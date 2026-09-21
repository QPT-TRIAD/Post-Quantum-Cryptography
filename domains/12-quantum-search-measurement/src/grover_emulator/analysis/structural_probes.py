"""Different algorithms against the same oracle: is there structure a search cannot see?

A success curve answers "how fast does generic search amplify the marked set", and it answers it from
``(M, N)`` alone. It cannot answer "is this relation's marked set the image of something algebraic",
because a diagonal phase oracle is blind to its own structure — it is a sign pattern, and every sign
pattern of the same size produces the same curve. So the question is asked a different way: run an
algorithm whose *success* depends on structure the search algorithm never looks at, against the same
circuit, and see whether it finds anything.

Two probes, and the difference between them is not cosmetic:

* :func:`simon_style_probe` measures the **predicate** the oracle is built from — the computable
  ``x -> [x marked]`` — in the Hadamard basis. It is exact when the predicate's codomain register is
  an ancilla-free flag, and the reason is a cancellation: for a marked set closed under ``x -> x ^ s``
  the two members of every coset contribute opposite signs to the amplitude of any ``y`` with
  ``y . s = 1``, so that amplitude is exactly zero. With dirty ancillas in the codomain the two
  members arrive with different ancilla states and the cancellation does not happen, so the probe
  **refuses** at a lowering that leaves ancillas behind rather than running and reporting a number
  whose support argument no longer holds.

* :func:`qft_period_probe` measures the **oracle** itself — the diagonal ``diag((-1)**f)`` — through
  the same ``H^n . D . H^n`` that phase estimation is built from. It needs no ancilla-free codomain
  because it never computes ``f`` into a register: the phase kicks back from the diagonal, and the
  Fourier support is the orthogonal complement of the marked set's period lattice. It runs at any
  lowering whose *total* width fits the backend.

**A probe that never fires is indistinguishable from a broken one.** That is why the suite is
specified against two controls and why the controls are tests rather than remarks: the probes must
fire on :class:`~grover_emulator.problem.oracle_spec.HiddenPeriodOracleSpec` — whose structure is
planted and therefore detectable — and must not fire on
:class:`~grover_emulator.problem.oracle_spec.RandomControlOracleSpec`, which has nothing to find.
Silence on the real relation means something only if the same code was loud on the positive control.

**What a silence costs at the worked instance.** At ``M = 1`` the measured distribution is uniform
over every ``y`` except zero — one marked state leaves the amplitudes of the two codomain classes
equal in magnitude for every other ``y`` — so a sample that constrains anything at all has
probability ``2/N``, and resolving a period would take a sample count of order ``N**2``. At
``n_search = 12`` that is not reachable, and the probes say so: they report the silence as a sample
count that was too small (their statistic is the dimension of the space the samples left open), not
as evidence of absent structure. That distinction is the whole reason the statistic is reported next
to the flag rather than folded into it.

**Every result carries its caveat, and the caveat is a required field.** A probe that did not fire at
``n_search = 8`` did not fire at ``n_search = 8``. The register is where the resolution lives: a
period is recovered from the span of sampled constraints, the number of samples needed to resolve one
grows with the width, and the widths that fit in a statevector are the widths that do not hold a
real secret. :class:`ProbeResult` makes that statement mandatory rather than optional, so a results
table cannot render a probe without it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from ..circuits.ir import GateList, GateName
from ..circuits.phase_oracle import build_phase_oracle
from ..problem.oracle_spec import Lowering, OracleSpec
from ..reporting.report_generator import MEASURED, REFUSED
from .success_probability import AnalysisError, sample_counts, search_register_probabilities, statevector_of

__all__ = [
    "ProbeResult",
    "ProbeError",
    "MEASURED",
    "NOT_RUN",
    "STRUCTURE_CAVEAT_TEMPLATE",
    "STRUCTURE_CAVEAT_REFUSED_TEMPLATE",
    "structure_caveat",
    "refusal_caveat",
    "simon_style_probe",
    "qft_period_probe",
    "run_probes",
    "verify_period",
]

NOTE_ON_STATUS_WORDS = """
:data:`MEASURED` and :data:`REFUSED` come from :mod:`grover_emulator.reporting.report_generator` and
are imported rather than retyped: the words a probe writes into its status have to be the words the
report matches on, or a refusal renders as a result. :data:`NOT_RUN` is the same string as
:data:`REFUSED` under the name a probe reads better with, and both are re-exported so a caller
naming a status does not have to import two modules to do it.
"""

NOT_RUN = REFUSED
"""The probe was not attempted, and :attr:`ProbeResult.reason` says why."""

STRUCTURE_CAVEAT_TEMPLATE = (
    "Absence of detected structure at n_search = {n} is evidence about this width and not proof that "
    "the structure is absent at n = 128. The probe resolves a period from {samples} sampled "
    "constraints on a {n}-qubit register; the number of samples needed to resolve one grows with the "
    "width while the widths a statevector can hold do not, so a probe that stays silent below the "
    "ceiling bounds nothing above it. Silence here is worth exactly as much as the positive control "
    "the same code fires on, and no more."
)
"""The mandatory caveat, in the words every :class:`ProbeResult` carries.

It names ``n = 128`` deliberately: the claim a reader is tempted to make from a silent probe is about
the widths that hold a real secret, and those are the widths this instrument never reached."""


def structure_caveat(n_qubits: int, samples: int, extra: str = "") -> str:
    """The standard caveat for a probe at this width, with an optional probe-specific sentence.

    A probe whose *preconditions* matter beyond the width — the Simon-style probe's requirement of an
    ancilla-free codomain, say — states them here rather than in a footnote, because a firing probe
    whose precondition silently failed is a false positive and a silent one whose precondition failed
    is uninterpretable.
    """
    caveat = STRUCTURE_CAVEAT_TEMPLATE.format(n=n_qubits, samples=samples)
    if extra:
        caveat = f"{caveat} {extra}"
    return caveat


STRUCTURE_CAVEAT_REFUSED_TEMPLATE = (
    "This probe did not run at n_search = {n}, so the row carries no measurement of this oracle: "
    "neither a detection nor a silence, in either direction. The {samples} sample(s) a run would have "
    "drawn were never drawn, which is why the sample count recorded with this result is zero. The "
    "statement a measured caveat would have made — that absence of detected structure at a small "
    "width is evidence about that width and not proof of its absence at n = 128 — is not available "
    "here either, and for a stronger reason: a refusal is not weak evidence about n = 128, it is no "
    "evidence at any width. What the result records instead is why the probe could not run."
)
"""The caveat a *refused* probe carries.

A different sentence from :data:`STRUCTURE_CAVEAT_TEMPLATE` because it is a different situation. The
measured template says a silence at this width does not bound a wider one; a refusal has no silence to
weaken, and printing the measured wording over a row that was never run would invite exactly the
reading — "no structure detected" — that the status column exists to prevent."""


def refusal_caveat(n_qubits: int, samples: int) -> str:
    """The caveat for a probe that was not run: what it did not do, and why that is not a silence."""
    return STRUCTURE_CAVEAT_REFUSED_TEMPLATE.format(n=n_qubits, samples=samples)


class ProbeError(AnalysisError):
    """A probe could not be run as asked. Distinct from a probe that ran and found nothing."""


@dataclass(frozen=True, slots=True)
class ProbeResult:
    """One probe, at one width, with the number it measured and the limit of what it means.

    :attr:`caveat` has no default and cannot be blank, and that is the point of the class. The
    statement it carries — that not detecting structure at a small width is evidence rather than proof
    of its absence at ``n = 128`` — is the difference between a negative result and a claim nobody
    can make, and a field that could be left empty would eventually be left empty in exactly the
    table that was quoted.

    Attributes:
        probe: the probe's name.
        fired: whether the probe *detected and verified* structure. A candidate that the classical
            check then refutes is not a firing, it is a sample count that was too small; the two are
            distinguished in :attr:`detail` and are never conflated in this flag.
        statistic: how much structure the samples are consistent with — the dimension of the subspace
            of constraints every sample satisfies. Zero means the samples admit no non-trivial period
            at all; a positive value means candidates exist, and :attr:`fired` says whether one of
            them survived verification. It is the same quantity for both probes so that the two are
            comparable in one table.
        n_qubits: the *search-register* width, per the project's convention that every width is a
            search width; :attr:`total_qubits` carries the circuit's own width.
        detail: what was measured, in words a reader can check against the statistic.
        caveat: the mandatory limitation statement. See the class docstring.
        status: ``"measured"`` or ``"not run"``.
        reason: why the probe was not run, when it was not.
    """

    probe: str
    fired: bool
    statistic: float
    n_qubits: int
    detail: str
    caveat: str
    total_qubits: int = 0
    """The circuit's own width. Zero means it did not differ from the search width."""
    status: str = MEASURED
    reason: str = ""
    oracle: str = ""
    lowering: str = ""
    method: str = ""
    samples: int = 0
    rank: int = 0
    nullity: int = 0
    candidate_period: int | None = None
    period_verified: bool = False

    def __post_init__(self) -> None:
        if not self.caveat or not self.caveat.strip():
            raise ValueError(
                f"probe {self.probe!r} was constructed without a caveat; the limitation statement is "
                "a required part of a probe result, not an optional one"
            )
        if self.status not in (MEASURED, NOT_RUN):
            raise ValueError(f"unknown probe status {self.status!r}; expected {MEASURED!r} or {NOT_RUN!r}")
        if self.status == NOT_RUN and self.fired:
            raise ValueError(
                f"probe {self.probe!r} cannot both have fired and not have run; a refusal is never "
                "a detection"
            )
        if self.status == NOT_RUN and not self.reason:
            raise ValueError(f"probe {self.probe!r} was not run and gives no reason")
        if not math.isfinite(self.statistic):
            raise ValueError(
                f"probe {self.probe!r} reports statistic {self.statistic!r}; a probe with no "
                "measurable statistic is reporting on itself"
            )
        if self.fired and not self.period_verified:
            raise ValueError(
                f"probe {self.probe!r} fired without a verified period; a candidate read off the "
                "sampled constraints is a hypothesis until the marked set confirms it"
            )

    @property
    def circuit_width(self) -> int:
        """The width of the circuit that was probed: the search register plus everything the oracle
        touches. It is reported next to the search width because the resolution argument is about the
        register while the cost argument is about the circuit."""
        return self.total_qubits or self.n_qubits

    def to_dict(self) -> dict:
        """The record the report renders. The first six keys are the ones its table prints."""
        return {
            "probe": self.probe,
            "fired": self.fired,
            "statistic": self.statistic,
            "n_qubits": self.n_qubits,
            "total_qubits": self.circuit_width,
            "detail": self.detail,
            "caveat": self.caveat,
            "status": self.status,
            "reason": self.reason,
            "oracle": self.oracle,
            "lowering": self.lowering,
            "method": self.method,
            "samples": self.samples,
            "rank": self.rank,
            "nullity": self.nullity,
            "candidate_period": self.candidate_period,
            "period_verified": self.period_verified,
            "provenance": MEASURED if self.status == MEASURED else NOT_RUN,
        }


# -----------------------------------------------------------------------------------------------
# GF(2) linear algebra on sampled constraints
# -----------------------------------------------------------------------------------------------


def _rank_and_null_space(rows: Iterable[int], n_bits: int) -> tuple[int, list[int]]:
    """Rank and a basis of the null space of the constraint rows, over GF(2).

    Each sample ``y`` from a Hadamard-basis measurement is a constraint ``y . s = 0`` on the secret
    period ``s``. The set of periods consistent with every sample is exactly the null space of the
    matrix whose rows are those ``y``; the rank is how much was learned, and the nullity is how much
    freedom is left. Elimination is done on integers as bit vectors — one XOR per pivot step, no
    floating point anywhere.
    """
    basis: dict[int, int] = {}
    for row in rows:
        value = int(row) & ((1 << n_bits) - 1)
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    # Full reduction before the null space is read off. Row echelon form alone is not enough and the
    # mistake is a silent one: a pivot column can still carry a 1 in a row whose own pivot is lower,
    # so reading the free columns off the echelon basis produces a *subspace* of the true null space.
    # That is the worst possible shape for this bug — the probe reports a nullity smaller than the
    # truth, its candidate list misses the real period, and it reads as a clean negative result.
    for pivot in sorted(basis, reverse=True):
        for other in basis:
            if other != pivot and (basis[other] >> pivot) & 1:
                basis[other] ^= basis[pivot]
    rank = len(basis)
    pivots = set(basis)
    null_space: list[int] = []
    for column in range(n_bits):
        if column in pivots:
            continue
        vector = 1 << column
        for pivot, row in basis.items():
            if (row >> column) & 1:
                vector |= 1 << pivot
        null_space.append(vector)
    return rank, null_space


def _candidates(null_space: Sequence[int], limit: int) -> list[int]:
    """Every non-zero vector in the span of ``null_space``, up to ``limit`` of them.

    The null space is spanned by at most ``n`` basis vectors, so an under-sampled probe can leave
    thousands of candidates; the caller is told to take more samples rather than being handed a
    truncated candidate list it would read as complete.
    """
    if len(null_space) > limit.bit_length() - 1:
        return []
    vectors = [0]
    for vector in null_space:
        vectors += [value ^ vector for value in vectors]
    return [value for value in vectors if value]


def verify_period(marked: frozenset[int], n_bits: int, period: int) -> bool:
    """Whether ``f(x) = f(x ^ period)`` holds for every ``x`` — decided from the marked set alone.

    This is the classical half of the probe, and it is what makes a firing a detection rather than a
    guess: the quantum samples propose, and the marked set disposes. It is also what keeps a negative
    control negative — a random function's samples produce spurious candidates whenever the sample
    count is short, and every one of them fails here, so the probe does not fire on structure that is
    not there. It reports that it could not yet rule the period out, which is a different sentence.

    **The check is over the marked set, not over every basis state, and that is an equivalence rather
    than a shortcut.** ``f(x) = f(x ^ s)`` for all ``x`` says the marked set is closed under XOR with
    ``s`` in both directions. If every marked value maps to a marked value, then the reverse holds
    too: if ``x`` were unmarked with ``x ^ s`` marked, applying the property to ``x ^ s`` — which is
    marked — gives ``x`` marked, a contradiction. So ``O(M)`` membership tests decide a property about
    all ``2**n`` basis states exactly, which is what makes it affordable to test every candidate the
    samples leave open instead of testing only the first few.
    """
    if period == 0 or period >= (1 << n_bits):
        return False
    return all((value ^ period) in marked for value in marked)


# -----------------------------------------------------------------------------------------------
# the sampling both probes share
# -----------------------------------------------------------------------------------------------


_MAX_CANDIDATES_LOG2 = 12
"""At most ``2**12 - 1`` candidate periods are enumerated. Beyond that the samples have not resolved
enough to be evidence of anything, which is reported rather than worked around."""


@dataclass(frozen=True, slots=True)
class _SamplingOutcome:
    """What the samples said, before anything is claimed about the oracle."""

    rank: int
    nullity: int
    nonzero_samples: int
    verified_periods: tuple[int, ...]
    candidates_examined: int
    unresolved: bool
    """True when the sample count left too many candidates to enumerate. Then the null space was
    never searched, and a silence means "not enough samples" rather than "nothing there"."""


def _recover_period(marked: frozenset[int], n_bits: int, samples: Sequence[int]) -> _SamplingOutcome:
    """Turn measured ``y`` values into a verdict about the marked set's period lattice."""
    nonzero = [y for y in samples if y]
    rank, null_space = _rank_and_null_space(nonzero, n_bits)
    nullity = n_bits - rank
    if nullity == 0:
        return _SamplingOutcome(rank, 0, len(nonzero), (), 0, False)
    if len(null_space) >= _MAX_CANDIDATES_LOG2 + 1:
        return _SamplingOutcome(rank, nullity, len(nonzero), (), 0, True)
    candidates = _candidates(null_space, 1 << _MAX_CANDIDATES_LOG2)
    verified = tuple(sorted(p for p in candidates if verify_period(marked, n_bits, p)))
    return _SamplingOutcome(rank, nullity, len(nonzero), verified, len(candidates), False)


def _sample_hadamard_outcomes(
    circuit: GateList,
    n_search: int,
    backend: object,
    samples: int,
    seed_parts: Sequence[str | int | bytes | None],
) -> list[int]:
    """Run ``circuit`` and return ``samples`` measured search-register values, seeded.

    The measurement is a draw from the exact marginal over the search register, taken here rather
    than by a backend: the same amplitudes that make the curve exact make the sampled outcomes
    reproducible, and a probe whose samples varied between runs could not be a control.
    """
    statevector = statevector_of(backend, circuit)
    probabilities = search_register_probabilities(statevector, n_search)
    counts = sample_counts(probabilities, samples, *seed_parts)
    outcomes: list[int] = []
    for value in sorted(counts):
        outcomes.extend([value] * counts[value])
    return outcomes


def _hadamard_layer(n_search: int, total_qubits: int) -> GateList:
    """``H`` on every search-register qubit, as its own gate list, for composition."""
    layer = GateList(total_qubits, label="H^n (search register)")
    for qubit in range(n_search):
        layer.append(GateName.H, qubit)
    return layer


def _refusal(
    probe: str,
    spec: OracleSpec,
    lowering: Lowering,
    n_search: int,
    samples: int,
    reason: str,
) -> ProbeResult:
    """A probe that was not run: the status, the reason, and a caveat that says what a refusal is.

    The caveat is the refusal wording rather than the measured one, and ``samples`` is recorded as
    zero because none were drawn — the count that *would* have been drawn survives inside the caveat
    text, named as such.
    """
    return ProbeResult(
        probe=probe,
        fired=False,
        statistic=0.0,
        n_qubits=n_search,
        detail=f"not run: {reason}",
        caveat=refusal_caveat(n_search, samples),
        status=NOT_RUN,
        reason=reason,
        oracle=spec.name,
        lowering=lowering.value,
        samples=0,
        method="",
    )


def _default_samples(n_search: int) -> int:
    """Enough samples to resolve a codimension-one structure at this width, with margin.

    The sample count needed grows with the register: each measured ``y`` is one GF(2) constraint, and
    a period survives only if the sampled rows span the whole orthogonal complement. Four samples per
    qubit clears that for the planted-period control at every width this layer runs at; a caller
    expecting to rule structure *out* at a large ``M = 1`` instance must ask for more and is told so
    by the statistic rather than by a guess.
    """
    return max(4 * n_search, 64)


# -----------------------------------------------------------------------------------------------
# the probes
# -----------------------------------------------------------------------------------------------


def simon_style_probe(
    spec: OracleSpec,
    backend: object,
    lowering: Lowering = Lowering.TRUTH_TABLE,
    samples: int | None = None,
    seed_parts: Sequence[str | int | bytes | None] = (),
) -> ProbeResult:
    """``H^n`` ; predicate ; ``H^n`` — measure, and ask whether the outcomes share a period.

    The predicate is the same object the phase oracle is built from: the oracle is this predicate
    inside a compute/uncompute sandwich, so probing the predicate is probing the oracle's own
    computable half rather than a description of it.

    Not run, with the reason recorded, when the predicate's codomain register is not an ancilla-free
    flag. The cancellation the probe rests on — coset members contributing opposite signs to every
    ``y`` with ``y . s = 1`` — needs the two members to arrive in the *same* codomain state; with
    dirty ancillas they do not, the support argument fails, and a number produced under a support
    argument that does not hold is worse than no number.
    """
    n_search = spec.search_width()
    ancillas = spec.ancilla_width(lowering)
    total = n_search + ancillas + 1
    samples = _default_samples(n_search) if samples is None else samples
    if ancillas:
        return _refusal(
            "simon_style",
            spec,
            lowering,
            n_search,
            samples,
            f"the {lowering.value} lowering leaves {ancillas} ancillas in the predicate's codomain "
            "register, where the cancellation that makes the measured distribution supported on the "
            "orthogonal complement does not hold; use the truth-table lowering, which is ancilla-free",
        )

    circuit = _hadamard_layer(n_search, total)
    circuit.extend(spec.build_predicate(lowering))
    circuit.extend(_hadamard_layer(n_search, total))
    circuit.label = f"{spec.name}:{lowering.value}:simon_style"

    outcomes = _sample_hadamard_outcomes(
        circuit, n_search, backend, samples, (spec.name, n_search, "simon_style", *seed_parts)
    )
    outcome = _recover_period(spec.marked_set(), n_search, outcomes)
    caveat = structure_caveat(
        n_search,
        samples,
        "The probe is exact only because this lowering's codomain register is an ancilla-free flag; "
        "it refuses to run where that fails, so a firing is a firing of the circuit the curve ran on.",
    )
    return _verdict(
        "simon_style",
        spec,
        lowering,
        n_search,
        total,
        samples,
        outcome,
        caveat,
        method="H^n . predicate . H^n, measured in the Hadamard basis",
    )


def qft_period_probe(
    spec: OracleSpec,
    backend: object,
    lowering: Lowering = Lowering.TRUTH_TABLE,
    samples: int | None = None,
    max_total_qubits: int = 20,
    seed_parts: Sequence[str | int | bytes | None] = (),
) -> ProbeResult:
    """``H^n`` ; oracle ; ``H^n`` — the phase kickback read as a spectrum.

    The oracle is the diagonal ``diag((-1)**f)``. Its Fourier transform over ``Z_2^n`` vanishes
    outside the orthogonal complement of the marked set's period lattice: for a marked set closed
    under ``x -> x ^ s``, the ``y``-component of the transform sums ``(-1)**f`` over each coset with
    opposite signs and cancels. Measuring the search register therefore returns values that are all
    orthogonal to any period the marked set has, which is the structure question asked with no
    ancilla in the codomain and no assumption beyond the oracle's contract.
    """
    n_search = spec.search_width()
    ancillas = spec.ancilla_width(lowering)
    total = n_search + ancillas + 1
    samples = _default_samples(n_search) if samples is None else samples
    if total > max_total_qubits:
        return _refusal(
            "qft_period",
            spec,
            lowering,
            n_search,
            samples,
            f"the {lowering.value} oracle is {total} qubits wide, above the {max_total_qubits}-qubit "
            "ceiling this probe holds its statevector under; the probe needs the whole circuit, not "
            "the search register alone, because the phase kicks back through every qubit the oracle "
            "touches",
        )

    circuit = _hadamard_layer(n_search, total)
    circuit.extend(build_phase_oracle(spec, lowering))
    circuit.extend(_hadamard_layer(n_search, total))
    circuit.label = f"{spec.name}:{lowering.value}:qft_period"

    outcomes = _sample_hadamard_outcomes(
        circuit, n_search, backend, samples, (spec.name, n_search, "qft_period", *seed_parts)
    )
    outcome = _recover_period(spec.marked_set(), n_search, outcomes)
    caveat = structure_caveat(
        n_search,
        samples,
        f"The probe ran on the {lowering.value} oracle at {total} qubits; the phase kicks back "
        "through every qubit the oracle touches, so the frequency resolution is that circuit's, not "
        "the search register's alone.",
    )
    return _verdict(
        "qft_period",
        spec,
        lowering,
        n_search,
        total,
        samples,
        outcome,
        caveat,
        method="H^n . oracle . H^n (phase kickback), measured in the Hadamard basis",
    )


def _verdict(
    probe: str,
    spec: OracleSpec,
    lowering: Lowering,
    n_search: int,
    total_qubits: int,
    samples: int,
    outcome: _SamplingOutcome,
    caveat: str,
    method: str,
) -> ProbeResult:
    """Turn sampled outcomes into a result, saying which of the three silences this one is.

    The three are different findings and are worded differently: no non-trivial period exists in the
    sampled span (the probe's negative result), candidates existed and every one was refuted by the
    marked set (a sample count too short to be evidence), or the null space was too large to search
    at all (the samples resolved nothing). Collapsing them into one "did not fire" is how a probe
    suite stops being interpretable.
    """
    fired = bool(outcome.verified_periods)
    if fired:
        periods = ", ".join(str(period) for period in outcome.verified_periods)
        detail = (
            f"fired: the marked set is closed under x -> x ^ s for the period(s) {periods} "
            f"({len(outcome.verified_periods)} of {outcome.candidates_examined} candidate(s) "
            f"survived the closure check, which decides the property for every one of the "
            f"{1 << n_search} basis states); {outcome.nonzero_samples} non-zero sample(s) of "
            f"{samples} constrained the period to a {outcome.nullity}-dimensional space"
        )
    elif outcome.unresolved:
        detail = (
            f"not fired: {outcome.nonzero_samples} non-zero sample(s) of {samples} left a "
            f"{outcome.nullity}-dimensional space of candidate periods, which is more than the "
            f"{1 << _MAX_CANDIDATES_LOG2} the probe will enumerate; the samples do not resolve this "
            "oracle at this width and the silence is not evidence of absent structure"
        )
    elif outcome.nullity == 0:
        detail = (
            f"not fired: {outcome.nonzero_samples} non-zero sample(s) of {samples} spanned the full "
            "register, so no non-trivial period is consistent with the measurement at all; the "
            "sampled support is the whole space"
        )
    else:
        detail = (
            f"not fired: {outcome.nonzero_samples} non-zero sample(s) of {samples} left "
            f"{outcome.candidates_examined} candidate period(s) in a {outcome.nullity}-dimensional "
            "space, and every one was refuted by checking f(x) = f(x ^ s) on the marked set; the "
            "samples were too few to rule the period out, which is not the same as finding one"
        )

    result = ProbeResult(
        probe=probe,
        fired=fired,
        statistic=float(outcome.nullity),
        n_qubits=n_search,
        detail=detail,
        caveat=caveat,
        total_qubits=total_qubits,
        status=MEASURED,
        oracle=spec.name,
        lowering=lowering.value,
        method=method,
        samples=samples,
        rank=outcome.rank,
        nullity=outcome.nullity,
        candidate_period=outcome.verified_periods[0] if outcome.verified_periods else None,
        period_verified=fired,
    )
    return result


def run_probes(
    spec: OracleSpec,
    backend: object,
    lowering: Lowering = Lowering.TRUTH_TABLE,
    samples: int | None = None,
    run_simon_style: bool = True,
    run_qft_period: bool = True,
    seed_parts: Sequence[str | int | bytes | None] = (),
) -> list[ProbeResult]:
    """Both probes against this spec, in a fixed order, refusals included.

    A refusal is returned as a result rather than raised, so a run records what it did not do and why
    in the same table as what it did. The alternative — an exception, or a probe quietly dropped — is
    a probe section that reads as complete while covering less.
    """
    results: list[ProbeResult] = []
    if run_simon_style:
        results.append(
            simon_style_probe(spec, backend, lowering=lowering, samples=samples, seed_parts=seed_parts)
        )
    if run_qft_period:
        results.append(
            qft_period_probe(spec, backend, lowering=lowering, samples=samples, seed_parts=seed_parts)
        )
    return results
