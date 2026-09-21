"""The report: boundary first, controls second, then what each theorem's reduction did when run."""

from __future__ import annotations

from .campaign import NOT_RUNNABLE
from .runner import FAILS, HOLDS, HOLDS_WITH_LOSS, VACUOUS, Result
from .scope import SCOPE_BOUNDARY

__all__ = ["render_report", "controls_hold", "headline"]


def controls_hold(results: list[Result]) -> tuple[bool, list[str]]:
    """The runner's own checks: it must catch the broken reduction, and a reduction must stay silent
    for an adversary that never wins."""
    problems = []
    controls = [r for r in results if r.experiment.role == "control"]
    if not any(r.experiment.key == "control_broken" for r in controls):
        problems.append("the broken-reduction control was not run")
    for r in controls:
        if r.verdict != r.experiment.expect:
            problems.append(f"{r.experiment.key}: expected {r.experiment.expect}, got {r.verdict}")
        if r.experiment.key != "control_broken" and (r.solved or r.invalid_outputs):
            problems.append(f"{r.experiment.key}: a reduction produced output for an adversary that never won")
    return not problems, problems


def headline(results: list[Result]) -> list[str]:
    held, problems = controls_hold(results)
    if not held:
        return ["**The runner's own controls did not behave, so nothing below may be relied on:** "
                + "; ".join(problems)]
    by_key = {r.experiment.key: r for r in results}
    lines = ["The runner's controls behaved: it caught a deliberately broken reduction, and no "
             "reduction produced an answer for an adversary that never won."]
    plain, pre = by_key.get("t1_plain"), by_key.get("t1_prequery")
    if plain and pre:
        if plain.verdict == HOLDS and pre.verdict == FAILS:
            lines.append(
                "- **Theorem 1's reduction, run as its proof is written, does not survive a legitimate "
                f"adversary.** Against a framer that requests the approval first it is perfect "
                f"({plain.solved}/{plain.real_wins} wins converted). Against one that looks the "
                "challenge up *before* requesting the approval — a public hash of the message, which "
                f"nothing in the game forbids querying — the adversary wins {pre.real_wins}/{pre.trials} "
                f"real games and the reduction cannot be carried out in {pre.simulation_failures}/"
                f"{pre.trials}: the oracle has already answered, so 'programs c(m) := c*' is "
                "impossible, and the reduction has no opening with which to answer honestly. The "
                "proof's sentence 'This simulation is perfect' does not hold for this adversary.")
        else:
            lines.append(f"- Theorem 1 as written: plain adversary {plain.verdict}, pre-querying "
                         f"adversary {pre.verdict}.")
    guess, salted = by_key.get("t1_guessing"), by_key.get("t1_salted")
    if guess and guess.conversion is not None:
        lines.append(
            f"- The textbook repair — guess which message will be approved — is sound and converts at "
            f"{guess.conversion:.2f} against a predicted {guess.claimed_conversion:.2f}: a loss factor "
            "equal to the number of messages the adversary looked up. In the theorem's bound that "
            "factor is the adversary's query count q, so the bound reads q times weaker and the word "
            "'tight' does not survive this repair.")
    if salted:
        lines.append(
            f"- A second standard repair, *not in the record*: a random salt in the challenge. Against "
            f"the same pre-querying adversary the as-written reduction then {salted.verdict.lower()} "
            f"({salted.solved}/{salted.real_wins} converted, {salted.simulation_failures} failures), "
            "because the approval's oracle point is fresh when the reduction programs it. This shows "
            "the repair restores *this* reduction in *this* model; what a salt does to extraction, "
            "certificate size and the other theorems is not examined here.")
    if plain and pre and pre.verdict == FAILS:
        lines.append(
            "- **This is a hole in a proof, not a break of the scheme.** No honest seat was framed by "
            "anything cleverer than exhaustive search over an 8-bit-scale key, which is how every "
            "adversary here wins and which costs 2^255 at production size. What failed is the "
            "*argument* that framing is as hard as A-F1: for one class of adversary the argument "
            "cannot be carried out, so for that class the theorem's bound is unproven — not shown "
            "false. Whether framing is actually hard is exactly as open as it was before.")
    evader = by_key.get("t2_evader")
    if evader:
        lines.append(
            f"- Theorem 2 step 2: {evader.verdict.lower()}. Every evasion ({evader.solved}/"
            f"{evader.real_wins}) yielded a genuine collision of F — *given* the two openings, which "
            "here come from the ideal prover and in the record from a quantum online extractor that "
            "is not run.")
    return lines


def render_report(results: list[Result], *, meta: dict) -> str:
    lines = ["# QPT-128 Mode B-r: the security reductions, run", "", SCOPE_BOUNDARY, "",
             f"Toy size n = {meta.get('n')} bits, {meta.get('trials')} trials per experiment, seed "
             f"{meta.get('seed')}, generated {meta.get('generated_utc')}. Source of the reductions: "
             "`modeB_security_v1.49.md` sections 1-4.", "",
             "## What was found", "", *headline(results), "",
             "## 1. Controls — does the runner itself work?", ""]
    lines += _table([r for r in results if r.experiment.role == "control"])
    lines += ["", "## 2. The reductions, run", ""]
    lines += _table([r for r in results if r.experiment.role != "control"])
    lines += ["", "*Conversion* is how often the reduction solved its instance, relative to how often "
              "the adversary won the real game. The two worlds are played on independent instances, so "
              "for an adversary that wins only sometimes the ratio scatters around its true value and "
              "can land above 1; the z-score in section 3 is the test of whether the two win rates "
              "differ.", "", "## 3. Why each verdict", ""]
    for r in results:
        e = r.experiment
        lines += [f"### `{e.key}` — {e.theorem}", "",
                  f"Reduction: {e.reduction_name}. Adversary: {e.adversary_name}."
                  + (f" {e.note}" if e.note else ""), "",
                  f"**{r.verdict}** (expected before the run: {e.expect}"
                  + ("" if r.verdict == e.expect else " — **the run disagrees with the expectation**")
                  + ").", "", *[f"- {reason}" for reason in r.reasons]]
        for message, count in sorted(r.failure_messages.items(), key=lambda kv: -kv[1])[:3]:
            lines.append(f"- {count} x simulation stopped: {message}")
        redrawn = r.params.get("trials_redrawn_for_handle_coincidence")
        if redrawn:
            lines.append(f"- {redrawn} trial(s) redrawn because two 8-bit-scale handles coincided — a "
                         "toy-width artefact the real verifier's 'sorted strictly' rule also rejects.")
        lines.append("")
    lines += ["## 4. Not run, and why", "",
              "A step that is not executed here is not thereby confirmed. These are the parts of the "
              "record's argument this runner has nothing to execute for:", ""]
    lines += [f"- **{title}.** {why}" for title, why in NOT_RUNNABLE]
    lines += ["", "## 5. What this does not say", "",
              "Nothing above bears on whether A-F1 or A-F2 is *hard*. A reduction that holds shows "
              "'if the problem is hard, this part of the scheme is secure'; a reduction that fails "
              "shows the proof does not establish even that, which is a statement about the proof and "
              "not an attack on the scheme. The failing case here was found by a model with an ideal "
              "prover and a classical random oracle; in the quantum random-oracle model, where an "
              "adversary can query the challenge of every message in superposition, programming a "
              "point the adversary chose is harder, not easier.", ""]
    return "\n".join(lines)


def _table(results: list[Result]) -> list[str]:
    rows = ["| experiment | adversary wins real game | wins in simulation | simulation failed | "
            "solved the hard problem | wrong outputs | conversion (claimed) | verdict |",
            "|---|---|---|---|---|---|---|---|"]
    for r in results:
        conversion = "—" if r.conversion is None else f"{r.conversion:.2f}"
        rows.append(f"| `{r.experiment.key}` | {r.real_wins}/{r.trials} | {r.simulated_wins}/{r.trials} | "
                    f"{r.simulation_failures} | {r.solved} | {r.invalid_outputs} | "
                    f"{conversion} ({r.claimed_conversion:.2f}) | **{r.verdict}** |")
    return rows
