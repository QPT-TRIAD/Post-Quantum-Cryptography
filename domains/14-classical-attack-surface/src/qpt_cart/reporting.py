"""The campaign report. Boundary first, controls second, subjects only if the controls held.

Three kinds of number appear and are never put in the same table: **measured** (a mean or median
over seeds of something the attack did), **fitted** (a growth rate or a model comparison computed from
measured points), and **extrapolated** (the fitted line read off at production size). The
extrapolated section exists so the measurement can be set beside the record's formula; it is not a
security estimate and says so on every row.
"""

from __future__ import annotations

from statistics import mean, median

from .analysis.workload_curve import Verdict
from .harness import SUBJECT, TrackOutcome, controls_hold
from .scope import EXTRAPOLATED, FITTED, MEASURED, SCOPE_BOUNDARY

__all__ = ["render_report", "findings"]


def _measured_table(outcome: TrackOutcome) -> list[str]:
    track = outcome.track
    unit = next((r.work_unit for r in outcome.results), "")
    timed = track.measure == "seconds"
    lines = ["| size | runs finished | median seconds | log2 | note |", "|---|---|---|---|---|"] if timed \
        else ["| size | runs finished | mean work | log2 | median seconds | note |", "|---|---|---|---|---|---|"]
    by_size: dict[int, list] = {}
    for result in outcome.results:
        by_size.setdefault(result.size, []).append(result)
    for size in sorted(by_size):
        runs = by_size[size]
        done = [r for r in runs if r.success]
        note = ""
        if len(done) < len(runs):
            reasons = sorted({r.not_run_reason for r in runs if not r.success and r.not_run_reason})
            note = "dropped from the fit: " + "; ".join(reasons)
        elif size in outcome.skipped_below_floor:
            note = "below the timing floor: overhead, not the attack"
        extra = [r.detail.get("minimum_block_size") for r in done if "minimum_block_size" in r.detail]
        if extra:
            note = (note + " " if note else "") + f"min block size {sorted(set(extra))}"
        if done:
            value = (mean if track.measure == "work" else median)(getattr(r, track.measure) for r in done)
            import math
            seconds = "" if timed else f"{median(r.seconds for r in done):.3g} | "
            lines.append(f"| {size} | {len(done)}/{len(runs)} | {value:,.4g} | {math.log2(value):.2f} | "
                         f"{seconds}{note} |")
        else:
            lines.append(f"| {size} | 0/{len(runs)} | — | — | {'' if timed else '— | '}{note} |")
    return [f"Unit of work: {unit}. Provenance: **{MEASURED}**.", "", *lines]


def _fit_lines(outcome: TrackOutcome) -> list[str]:
    fit, track = outcome.fit, outcome.track
    lines = [f"Provenance: **{FITTED}**.", "", f"- **Verdict: {fit.verdict}** — {fit.reason}"]
    if fit.exponent_bits_per_unit is not None:
        low, high = fit.exponent_ci95
        lines.append(f"- growth rate: {fit.exponent_bits_per_unit:.3f} bits of work per unit of size "
                     f"(95% interval {low:.3f}..{high:.3f}); as a power law, degree "
                     f"{fit.polynomial_degree:.2f}")
    if track.expected_exponent is not None and fit.exponent_matches_expectation is not None:
        agrees = "agrees with" if fit.exponent_matches_expectation else "**DISAGREES with**"
        lines.append(f"- {agrees} the expected {track.expected_exponent:.3f} — {track.expectation_source}")
    elif track.expectation_source:
        lines.append(f"- for comparison: {track.expectation_source}")
    if fit.dropped_sizes:
        lines.append(f"- sizes dropped because a seed did not finish: {fit.dropped_sizes}")
    if track.note:
        lines.append(f"- {track.note}")
    return lines


def findings(outcomes: list[TrackOutcome]) -> list[str]:
    held, problems = controls_hold(outcomes)
    if not held:
        return ["**The controls did not hold, so no subject verdict below may be relied on:** "
                + "; ".join(problems)]
    out = ["The controls held: the tester called the random function exponential at the known rate "
           "and caught the linear map as polynomial. The subject verdicts are therefore meaningful "
           "*for the attacks and sizes run*."]
    for outcome in outcomes:
        if outcome.track.role != SUBJECT:
            continue
        fit, title = outcome.fit, outcome.track.title
        if fit.verdict == Verdict.POLYNOMIAL:
            tail = f" {outcome.track.note}" if outcome.track.note else \
                " **This is a shortcut at the sizes measured and needs explaining.**"
            out.append(f"- **{title}: polynomial in range.**{tail}")
        elif fit.verdict == Verdict.EXPONENTIAL:
            match = ""
            if fit.exponent_matches_expectation is True:
                match = f", at the rate the record's formula gives ({outcome.track.expected_exponent:.3f})"
            elif fit.exponent_matches_expectation is False:
                match = (f", but at {fit.exponent_bits_per_unit:.3f} bits per unit where the record's "
                         f"formula gives {outcome.track.expected_exponent:.3f} — **a disagreement**")
            out.append(f"- {title}: exponential in range{match}.")
        else:
            out.append(f"- {title}: {fit.verdict} — {fit.reason}.")
    return out


def _against_exhaustive_search(outcomes: list[TrackOutcome]) -> list[str]:
    """Does the algebraic attack beat exhaustive search, on the same machine, at the same size?

    A growth rate alone cannot answer that: an attack can grow more slowly and still lose
    everywhere in reach, or the reverse. So the two are put side by side in seconds. Exhaustive
    search is only *run* at small sizes; beyond them its time is **derived** — the measured seconds
    per opening, times the ``2^(n-1)`` mean the counted track confirmed — and is labelled so.
    """
    by_key = {o.track.key: o for o in outcomes}
    lines: list[str] = []
    for mode in ("a", "b"):
        brute, algebra = by_key.get(f"keymap_{mode}_brute_force"), by_key.get(f"keymap_{mode}_groebner")
        if not brute or not algebra:
            continue
        finished = [r for r in brute.results if r.success and r.work]
        if not finished:
            continue
        per_opening = sum(r.seconds for r in finished) / sum(r.work for r in finished)
        measured = {}
        for r in finished:
            measured.setdefault(r.size, []).append(r.seconds)
        rows = []
        for size in sorted({r.size for r in algebra.results}):
            runs = [r for r in algebra.results if r.size == size]
            if not runs or not all(r.success for r in runs):
                continue
            groebner = median(r.seconds for r in runs)
            if size in measured:
                search, how = mean(measured[size]), MEASURED
            else:
                search, how = per_opening * 2 ** (size - 1), "derived (measured rate x 2^(n-1))"
            winner = "Groebner" if groebner < search else "the Python search loop"
            rows.append(f"| {size} | {groebner:.3g} | {search:.3g} | {how} | "
                        f"{winner}, by {max(groebner, search) / min(groebner, search):,.1f}x |")
        if rows:
            lines += [f"### Mode {mode.upper()}", "",
                      f"Exhaustive search measured at {per_opening * 1e6:.1f} microseconds per opening.", "",
                      "| n | Groebner (C++), median s | exhaustive search (Python), mean s | search time is | finished first |",
                      "|---|---|---|---|---|", *rows, ""]
    if lines:
        lines = ["## 2b. Algebraic attack beside exhaustive search, as implemented here — measured and derived", "",
                 "Same machine, same sizes, in seconds. The record scores the linear handle (Mode A) "
                 "far below the power handle (Mode B) — 148.8 against 378.2 classical bits at "
                 "n = 256 — from a formula it never ran. This is that comparison, run.", "",
                 "**This compares two implementations, not two algorithms — read it that way.** "
                 "The Groebner engine is optimised C++. The exhaustive search is this package's "
                 "plain Python loop, tens of thousands of CPU cycles per opening, where an "
                 "optimised enumerator (libFES-style, bit-sliced Gray code) spends a few: a factor "
                 "of roughly 2^12. Applied to the table below, that factor **reverses every "
                 "'Groebner wins' row** — and the MQ estimator of the CryptographicEstimators "
                 "library agrees, naming exhaustive search the cheapest attack at all of these "
                 "sizes (2^31 bit operations at n = 28, against about 2^35 cycles measured for "
                 "Groebner). So the 'faster' column says which *program* finished first on this "
                 "machine and nothing about which attack is cheaper. What does carry over is the "
                 "**growth rate** in section 3: an algebraic attack that grows by less than one bit "
                 "per bit of n must overtake any exhaustive search eventually, however well "
                 "optimised, and one that grows by more than one bit never will.", "",
                 "**What a loss for Groebner here does and does not mean.** It means *this* "
                 "formulation, in *this* engine, lost. Mode B is modelled as the record models it — "
                 "2n unknowns, quadrics plus cubics — and an attacker is free to do otherwise: "
                 "eliminate s and solve degree-6 equations in n unknowns, guess some bits first "
                 "(hybrid), or use an F4/F5 engine faster than PolyBoRi. None of those was run, so "
                 "'exhaustive search wins' is a statement about the attack tried, not a proof that "
                 "no algebraic attack on Mode B beats it.", "", *lines]
    return lines


def render_report(outcomes: list[TrackOutcome], *, meta: dict) -> str:
    held, _ = controls_hold(outcomes)
    lines = ["# QPT-128 primitives: classical attack workload curves", "", SCOPE_BOUNDARY, "",
             f"Campaign `{meta.get('scale')}`, key-map expansion E = {meta.get('expansion')} at "
             f"n = 256 (ratio {meta.get('expansion', 0) / 256:.3f}), generated {meta.get('generated_utc')}.",
             "", "## Findings", "", *findings(outcomes), ""]

    lines += ["## 1. Controls — can this tester tell exponential from polynomial?", ""]
    for outcome in outcomes:
        if outcome.track.role != SUBJECT:
            lines += [f"### {outcome.track.title}", "", f"Role: {outcome.track.role}.", "",
                      *_measured_table(outcome), "", *_fit_lines(outcome), ""]

    lines += ["## 2. Subjects — measured", ""]
    if not held:
        lines += ["**Controls failed: the tables below are raw measurements only, and the verdicts "
                  "in section 3 are void.**", ""]
    for outcome in outcomes:
        if outcome.track.role == SUBJECT:
            lines += [f"### {outcome.track.title}", "", *_measured_table(outcome), ""]

    lines += _against_exhaustive_search(outcomes)

    lines += ["## 3. Subjects — fitted", ""]
    for outcome in outcomes:
        if outcome.track.role == SUBJECT:
            lines += [f"### {outcome.track.title}", "", *_fit_lines(outcome), ""]

    lines += ["## 4. Extrapolated to production size — not measured", "",
              f"Provenance of every row: **{EXTRAPOLATED}**. These are straight lines continued far "
              "outside the measured range. They are shown so the measured growth rate can be set "
              "beside the record's formula, and for no other purpose. **They are not security "
              "estimates.**", "",
              "| track | production size | extrapolated log2 work | 95% band | warning |",
              "|---|---|---|---|---|"]
    any_row = False
    for outcome in outcomes:
        ext = outcome.fit.extrapolation
        if outcome.track.role == SUBJECT and ext and held:
            any_row = True
            low, high = ext["log2_work_ci95"]
            lines.append(f"| {outcome.track.title} | {ext['production_size']} | "
                         f"{ext['log2_work']:.1f} | {low:.1f}..{high:.1f} | {ext['warning']} |")
    if not any_row:
        lines.append("| — | — | — | — | no track qualified (needs an exponential verdict and "
                     "controls that held) |")
    lines += ["", "Only tracks with an *exponential* verdict are extrapolated. A timed track's "
              "line is in log2 seconds on this machine, not in operations.", ""]
    return "\n".join(lines)
