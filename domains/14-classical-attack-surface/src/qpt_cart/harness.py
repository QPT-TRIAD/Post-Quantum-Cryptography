"""The campaign: which attack runs against which primitive at which sizes, and in what role.

A *track* is one attack against one primitive across a list of sizes and seeds, producing one
workload curve. Tracks have a role. **Controls run first and gate everything else**: if the
random-function control is not called exponential, or the linear-map control is not called
polynomial, the tester has not shown it can tell the two apart on this machine today, and the report
says the subject verdicts are void rather than printing them as if they meant something.

Count-based tracks (work measured in the attack's own operations) run their seeds in a process
pool, since contention cannot change a count. Time-based tracks (Groebner, BKZ) run one at a time,
because contention is exactly what would corrupt a wall-clock curve.
"""

from __future__ import annotations

import multiprocessing
import os
from dataclasses import dataclass, field

from .analysis.workload_curve import CurveFit, Verdict, central_points, fit_curve
from .attacks.algebraic import gaussian_preimage, groebner_keymap
from .attacks.base import AttackResult
from .attacks.brute_force import brute_force_function, brute_force_keymap
from .attacks.collision import birthday_collision, linear_trick_collision
from .attacks.lattice import lattice_primal
from .primitives.controls import LinearMapControl, RandomFunctionControl
from .primitives.keymap import PRODUCTION_N, HandleMode, KeyMapScheme, ScalingRule
from .primitives.qlwr_trace import QlwrTrace

__all__ = ["Track", "TrackOutcome", "PROFILES", "run_track", "run_campaign", "controls_hold"]

SUBJECT, CONTROL_EXPONENTIAL, CONTROL_POLYNOMIAL = "subject", "control: must be exponential", \
    "control: must be polynomial"


@dataclass(frozen=True)
class Track:
    key: str
    title: str
    role: str
    sizes: tuple[int, ...]
    seeds: int
    measure: str                       # "work" (counted) or "seconds" (timed)
    expected_exponent: float | None = None
    expectation_source: str = ""
    production_size: int | None = None
    max_seconds: float = 120.0
    seconds_floor: float = 0.0         # timed points below this are overhead, not the attack
    note: str = ""


@dataclass
class TrackOutcome:
    track: Track
    results: list[AttackResult]
    fit: CurveFit
    skipped_below_floor: list[int] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "TrackOutcome":
        """Rebuild an outcome from ``results.json`` so a report can be re-rendered without
        re-running a single attack."""
        track = dict(data["track"])
        track["sizes"] = tuple(track["sizes"])
        fit = dict(data["fit"])
        if fit.get("exponent_ci95") is not None:
            fit["exponent_ci95"] = tuple(fit["exponent_ci95"])
        return cls(Track(**track), [AttackResult(**r) for r in data["results"]], CurveFit(**fit),
                   list(data.get("skipped_below_floor", [])))

    def to_dict(self) -> dict:
        return {"track": self.track.__dict__, "fit": self.fit.to_dict(),
                "skipped_below_floor": self.skipped_below_floor,
                "results": [r.to_dict() for r in self.results]}


def _run_one(job) -> AttackResult:
    key, size, seed, max_seconds, expansion = job
    rule = ScalingRule(production_expansion=expansion)
    if key == "control_random_function":
        control = RandomFunctionControl(size, seed)
        return brute_force_function(control, control.keygen()[1], seed=seed, max_seconds=max_seconds,
                                    name="control/random_function")
    if key == "control_linear_map":
        control = LinearMapControl(size, seed)
        return gaussian_preimage(control, control.keygen()[1], seed=seed)
    if key in ("keymap_b_brute_force", "keymap_a_brute_force", "keymap_a_groebner", "keymap_b_groebner"):
        mode = HandleMode.A if "_a_" in key else HandleMode.B
        scheme = KeyMapScheme(size, mode, rule=rule)
        _, transcript = scheme.transcript(seed)
        attack = groebner_keymap if key.endswith("groebner") else brute_force_keymap
        return attack(scheme, transcript, seed=seed, max_seconds=max_seconds)
    if key in ("keymap_linear_trick", "keymap_birthday"):
        qmap = KeyMapScheme(size, HandleMode.A, rule=rule).map
        attack = linear_trick_collision if key == "keymap_linear_trick" else birthday_collision
        return attack(qmap, seed=seed, max_seconds=max_seconds)
    if key == "qlwr_lattice":
        return lattice_primal(QlwrTrace(size, seed=seed), seed=seed, max_seconds=max_seconds)
    raise ValueError(f"unknown track {key!r}")


def run_track(track: Track, *, expansion: int = 300, workers: int | None = None) -> TrackOutcome:
    jobs = [(track.key, size, seed, track.max_seconds, expansion)
            for size in track.sizes for seed in range(1, track.seeds + 1)]
    if track.measure == "work" and len(jobs) > 1:
        workers = workers or max(1, min(len(jobs), (os.cpu_count() or 2) - 1))
        with multiprocessing.get_context("fork").Pool(workers) as pool:
            results = pool.map(_run_one, jobs)
    else:
        # Timed tracks stop climbing once a size has exceeded its budget. Sizes run in increasing
        # order and cost grows with size, so a larger one would exceed it too — and spending another
        # full budget per seed to re-learn that is hours of wall-clock for no information. What was
        # skipped is recorded as not run, with this as the reason: it is a statement about the
        # budget, exactly like the run that tripped it, and never about the primitive.
        results, tripped_at = [], None
        for job in jobs:
            _, size, seed, _, _ = job
            if tripped_at is not None and size >= tripped_at:
                results.append(AttackResult(
                    attack=track.key, primitive="-", size=size, seed=seed, success=False, work=None,
                    work_unit="seconds", seconds=0.0, provenance="not run",
                    not_run_reason=f"skipped: size {tripped_at} already exceeded the "
                                   f"{track.max_seconds:g}s budget"))
                continue
            result = _run_one(job)
            results.append(result)
            if not result.success and "budget" in (result.not_run_reason or ""):
                tripped_at = size

    sizes, values, dropped = central_points(results, use=track.measure)
    below = []
    if track.measure == "seconds" and track.seconds_floor > 0:
        keep = [(s, v) for s, v in zip(sizes, values) if 2 ** v >= track.seconds_floor]
        below = [s for s, v in zip(sizes, values) if 2 ** v < track.seconds_floor]
        sizes, values = [s for s, _ in keep], [v for _, v in keep]
    fit = fit_curve(sizes, values, dropped=dropped, expected_exponent=track.expected_exponent,
                    production_size=track.production_size)
    return TrackOutcome(track, results, fit, below)


def controls_hold(outcomes: list[TrackOutcome]) -> tuple[bool, list[str]]:
    """Whether the tester told exponential from polynomial on the controls, and what went wrong."""
    problems = []
    for outcome in outcomes:
        role, verdict = outcome.track.role, outcome.fit.verdict
        if role == CONTROL_EXPONENTIAL and verdict != Verdict.EXPONENTIAL:
            problems.append(f"{outcome.track.title}: expected '{Verdict.EXPONENTIAL}', got '{verdict}'")
        if role == CONTROL_EXPONENTIAL and outcome.fit.exponent_matches_expectation is False:
            problems.append(f"{outcome.track.title}: growth rate "
                            f"{outcome.fit.exponent_bits_per_unit:.3f} is not the known 1.0")
        if role == CONTROL_POLYNOMIAL and verdict != Verdict.POLYNOMIAL:
            problems.append(f"{outcome.track.title}: expected '{Verdict.POLYNOMIAL}', got '{verdict}'")
    have = {o.track.role for o in outcomes}
    for needed in (CONTROL_EXPONENTIAL, CONTROL_POLYNOMIAL):
        if needed not in have:
            problems.append(f"no track with role '{needed}' was run")
    return not problems, problems


def _tracks(scale: str, rule: ScalingRule) -> list[Track]:
    """``sizes`` is always the list of ``n`` (or ``nu``) the instances are built at. Two collision
    tracks are *drawn* against the parameter that drives them — ``E`` and ``m`` — which the attack
    reports as its size; their production sizes are that parameter at ``n = 256``."""
    quick = scale == "quick"
    e_prod = rule.production_expansion
    return [
        Track("control_random_function", "Control: preimage of a random function, exhaustive search",
              CONTROL_EXPONENTIAL, (6, 8, 10, 12, 14) if quick else (8, 10, 12, 14, 16, 18, 20),
              64, "work", 1.0, "one bit of work per bit of n; mean 2^n / e (extra preimages)"),
        Track("control_linear_map", "Control: preimage of a linear map, Gaussian elimination",
              CONTROL_POLYNOMIAL, (16, 24, 32, 48, 64) if quick else (16, 24, 32, 48, 64, 96, 128, 192, 256),
              3, "work", None, "O(n^3) bit operations"),
        Track("keymap_b_brute_force", "Key map, Mode B (r^7 handle): exhaustive search over r", SUBJECT,
              (5, 7, 8, 10, 11, 13) if quick else (8, 10, 11, 13, 14, 16, 17, 19), 64, "work", 1.0,
              "record: generic framing costs 2^(n-1) mean (attack lab FRAME experiment)", PRODUCTION_N,
              max_seconds=600.0),
        Track("keymap_a_brute_force", "Key map, Mode A (linear handle): exhaustive search over r",
              SUBJECT, (5, 7, 8, 10, 11, 13) if quick else (8, 10, 12, 14, 16, 18), 64, "work", 1.0,
              "same search; the handle's form does not help a black-box attacker", PRODUCTION_N,
              max_seconds=600.0),
        Track("keymap_linear_trick", "Key map collision: the structural 'linear trick' (drawn against E)",
              SUBJECT, (4, 5, 7, 8, 10) if quick else (5, 7, 8, 10, 11, 13, 14), 64, "work", 1.0,
              "record: 2^E differences (hidden_signer_modeB_v1.46.py:582)", e_prod, max_seconds=900.0),
        Track("keymap_birthday", "Key map collision: generic birthday search (drawn against m)", SUBJECT,
              (3, 4, 5, 6, 7) if quick else (4, 5, 6, 7, 8, 10, 11), 32, "work", 0.5,
              "sqrt(pi/2 * 2^m) evaluations for an m-bit output", 2 * PRODUCTION_N + e_prod,
              max_seconds=900.0),
        Track("keymap_a_groebner", "Key map, Mode A: Groebner basis (PolyBoRi), r eliminated", SUBJECT,
              (14, 16, 18, 20, 22) if quick else (16, 18, 20, 22, 24, 26, 28), 2 if quick else 3,
              "seconds", None, "record scores Mode A at 148.8 classical bits at n = 256, from a formula",
              PRODUCTION_N, max_seconds=60.0 if quick else 1200.0, seconds_floor=0.02,
              note="Expect a staircase, not a line: within one solving degree the cost is "
                   "polynomial in n, and it jumps when the degree steps up. A staircase fits "
                   "neither model, so 'inconclusive' here is a description, not a failure."),
        Track("keymap_b_groebner", "Key map, Mode B: Groebner basis (PolyBoRi), quadrics + cubics",
              SUBJECT, (7, 8, 10, 11) if quick else (7, 8, 10, 11, 13, 14), 2 if quick else 3, "seconds",
              None, "record scores Mode B at 378.2 classical bits at n = 256, from a formula",
              PRODUCTION_N, max_seconds=60.0 if quick else 1200.0, seconds_floor=0.02),
        Track("qlwr_lattice", "QLWR trace: primal lattice attack (fpylll BKZ, 1 thread)", SUBJECT,
              (12, 16, 20, 24, 28) if quick else (12, 16, 20, 24, 28, 32, 40, 48), 2, "seconds", None,
              "LLL suffices at the smallest sizes; hardness shows as the minimum block size climbing",
              None, max_seconds=120.0 if quick else 900.0, seconds_floor=0.02,
              note="Read the minimum block size column, not only the seconds: polynomial while "
                   "LLL (block size 2) suffices, exponential once the needed block size climbs. If "
                   "this track reads 'polynomial in range', that is the LLL regime and not a break."),
    ]


PROFILES = ("quick", "full")


def run_campaign(scale: str = "full", *, expansion: int = 300, only: tuple[str, ...] = (),
                 progress=None) -> list[TrackOutcome]:
    if scale not in PROFILES:
        raise ValueError(f"scale must be one of {PROFILES}")
    rule = ScalingRule(production_expansion=expansion)
    outcomes = []
    for track in _tracks(scale, rule):
        if only and track.key not in only and not track.role.startswith("control"):
            continue
        if progress:
            progress(f"running {track.key} at sizes {track.sizes} x {track.seeds} seed(s)")
        outcomes.append(run_track(track, expansion=expansion))
    return outcomes
