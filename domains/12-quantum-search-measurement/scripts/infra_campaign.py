#!/usr/bin/env python3
"""The PQ infrastructure program's quantum-search assumptions, measured at the widths that fit.

The infrastructure record (firmware signing S1, DNSSEC S2, TLS/PKI S3, broadcast S4, smart cards
S5, migration S6) judges every hash-based component against the 2^128 gate budget with one formula,

    log2(gates) = n/2  -  log2(T)/2  +  18

— Grover's square root on an n-bit image, the full square-root gain over T targets where domain
separation does not block it, and an assumed 2^18 gates per hash-oracle query. None of the three
terms is measured anywhere in that record: each test there checks the arithmetic of the formula.

This campaign measures the two terms an exact *simulator* can reach, on the record's own reduced-size
LM-OTS game and on the negative control, and says in the same report what it cannot reach:

  A. iteration law     — first measured peak of the success curve against floor(pi/4 sqrt(N/M)),
                         across widths; the fitted slope of log2(k) in n is the "n/2".
  B. multi-target law  — the same at one width across M = 1..2^j marked items; the fitted slope of
                         log2(k) in log2(M) is the "-log2(T)/2".
  C. structure         — the Simon-style and QFT probes on the LM-OTS relation, with the positive
                         control (must fire) and the negative control (must not) run beside it.
  D. NOT MEASURED HERE — the 2^18 gates-per-query floor. The oracles in A-C are lowered from a truth
                         table: the hash is evaluated classically and its answers are wired in, so
                         their gate counts say nothing about a hash circuit and are not reported as
                         one. That term is counted separately, on a verified reversible SHA-256, by
                         ``scripts/hash_oracle_cost.py`` — and section D says so rather than leave
                         a reader to think it was skipped or, worse, that A-C covered it.

Every width here is at most 14 search qubits. Agreement at these widths is evidence that the law
the record extrapolates is the law Grover's algorithm obeys on these relations; it is not a
measurement at n = 192 or n = 256, and the report says so before any table.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grover_emulator.analysis.structural_probes import run_probes  # noqa: E402
from grover_emulator.analysis.success_probability import success_curve  # noqa: E402
from grover_emulator.backends.qiskit_aer_backend import QiskitAerBackend  # noqa: E402
from grover_emulator.problem.corpus_oracles import LMOtsChainSpec  # noqa: E402
from grover_emulator.problem.oracle_spec import (  # noqa: E402
    HiddenPeriodOracleSpec,
    RandomControlOracleSpec,
)
from grover_emulator.reporting.report_generator import SCOPE_BOUNDARY  # noqa: E402

SEED = 20260920

#: What the infrastructure record assumes, with where it says so. Recorded here as named values —
#: the campaign reads nothing from that record at run time, so a run reproduces without it.
RECORD_ASSUMPTIONS = {
    "iteration_exponent": {
        "value": 0.5,
        "where": "pq_infra_s4_embedded_broadcast_v2.0.py:102-111 (2 ** (n_bits // 2)); "
                 "pq_audit_s6_hybrid_games_v2.1.py:369,378",
    },
    "multi_target_exponent": {
        "value": -0.5,
        "where": "pq_audit_s2_dns_worstcase_v2.1.py:455-458 (n/2 - T_log2/2 + 18, T = 2^40)",
    },
    "log2_gates_per_hash_query": {
        "value": 18,
        "where": "pq_infra_s4_embedded_broadcast_v2.0.py:102; pq_audit_s1_lms_v2.2.py:286; "
                 "pq_audit_s2_dns_worstcase_v2.1.py:455; QPT128_finalization_v1.43.md:72",
    },
}

WIDTHS = (6, 8, 10, 12, 14)
MULTI_TARGET_WIDTH = 12
MULTI_TARGET_COUNTS = (1, 2, 4, 8, 16, 32, 64)


def _slope(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least-squares slope and intercept. Two lines of algebra, so the fit is auditable here."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return slope, my - slope * mx


def _curve_row(spec, backend, label: str) -> dict:
    curve = success_curve(spec, backend, seed_parts=("infra", label))
    peak = curve.peak_measured
    residuals = curve.residuals
    return {
        "label": label,
        "spec": curve.spec_name,
        "search_width": curve.search_width,
        "n_marked": curve.n_marked,
        "textbook_iterations": curve.optimal_iterations,
        "measured_peak_iteration": peak.iteration,
        "measured_peak_probability": peak.measured,
        "closed_form_at_measured_peak": peak.closed_form,
        "max_abs_residual": residuals["max_abs_residual"],
        "window_contains_closed_form_peak": curve.window_contains_closed_form_peak,
        "provenance": "measured",
    }


def iteration_law(backend) -> dict:
    rows = [_curve_row(LMOtsChainSpec(n, seed=SEED), backend, f"lmots_chain/n={n}") for n in WIDTHS]
    # Normalise out M: a truncated hash has a handful of preimages at these widths, and the law
    # under test is k ~ sqrt(N/M), so the regression is of log2(k * sqrt(M)) on n.
    usable = [r for r in rows if r["measured_peak_iteration"] >= 1]
    xs = [float(r["search_width"]) for r in usable]
    ys = [math.log2(r["measured_peak_iteration"] * math.sqrt(r["n_marked"])) for r in usable]
    slope, intercept = _slope(xs, ys)
    return {"rows": rows, "fitted_exponent": slope, "fitted_intercept": intercept,
            "assumed_exponent": RECORD_ASSUMPTIONS["iteration_exponent"]["value"],
            "provenance_of_fit": "fitted to measured points; not a measurement at n = 192 or 256"}


def multi_target_law(backend) -> dict:
    rows = [
        _curve_row(RandomControlOracleSpec(MULTI_TARGET_WIDTH, m, SEED), backend,
                   f"random_control/n={MULTI_TARGET_WIDTH}/M={m}")
        for m in MULTI_TARGET_COUNTS
    ]
    xs = [math.log2(r["n_marked"]) for r in rows]
    ys = [math.log2(r["measured_peak_iteration"]) for r in rows]
    slope, intercept = _slope(xs, ys)
    return {"rows": rows, "fitted_exponent": slope, "fitted_intercept": intercept,
            "assumed_exponent": RECORD_ASSUMPTIONS["multi_target_exponent"]["value"],
            "provenance_of_fit": "fitted to measured points; not a measurement at T = 2^40"}


def structure(backend, width: int = 8) -> dict:
    subjects = {
        "lmots_chain (the record's LM-OTS game)": LMOtsChainSpec(width, seed=SEED),
        "hidden_period (positive control: must fire)": HiddenPeriodOracleSpec(width, 0b1010, SEED),
        "random_control (negative control: must not fire)":
            RandomControlOracleSpec(width, 4, SEED),
    }
    return {
        name: [result.to_dict() for result in run_probes(spec, backend, seed_parts=("infra", name))]
        for name, spec in subjects.items()
    }


def render(results: dict) -> str:
    a, b = results["iteration_law"], results["multi_target_law"]
    out = [
        "# PQ infrastructure program: quantum-search assumptions, measured at small width",
        "", SCOPE_BOUNDARY, "",
        "**What this adds to that boundary.** Widths here are at most 14 search qubits. The record "
        "judges components at n = 192 and n = 256 and T = 2^40. Nothing below is a measurement at "
        "those sizes; fitted exponents are labelled as fits.",
        "",
        "## A. Iteration law on the LM-OTS game — measured",
        "",
        "| width n | M | textbook k | measured peak k | P at peak | max abs residual vs sin² |",
        "|---|---|---|---|---|---|",
        *[f"| {r['search_width']} | {r['n_marked']} | {r['textbook_iterations']} | "
          f"{r['measured_peak_iteration']} | {r['measured_peak_probability']:.6f} | "
          f"{r['max_abs_residual']:.2e} |" for r in a["rows"]],
        "",
        f"Fitted exponent of k·√M in n — **fit, not measurement**: **{a['fitted_exponent']:.4f}** "
        f"(the record assumes {a['assumed_exponent']}).",
        "",
        f"## B. Multi-target law at n = {MULTI_TARGET_WIDTH} — measured",
        "",
        "| M | textbook k | measured peak k | P at peak |", "|---|---|---|---|",
        *[f"| {r['n_marked']} | {r['textbook_iterations']} | {r['measured_peak_iteration']} | "
          f"{r['measured_peak_probability']:.6f} |" for r in b["rows"]],
        "",
        f"Fitted exponent of k in M — **fit, not measurement**: **{b['fitted_exponent']:.4f}** "
        f"(the record assumes {b['assumed_exponent']}).",
        "",
        "The law holds for M marked inputs of *one* oracle. Whether T signed objects are T marks of "
        "one oracle is a property of the hashing, not of Grover: the record's own S1 ledger blocks "
        "the gain with per-node domain separation and its S2 ledger grants it to unprefixed Merkle "
        "nodes. This campaign confirms the law, not which case a deployment is in.",
        "",
        "## C. Structure probes at n = 8 — measured",
        "",
        "| subject | probe | status | fired | samples | rank |", "|---|---|---|---|---|---|",
    ]
    refused = []
    for name, probes in results["structure"].items():
        for p in probes:
            # A probe that refused to run has ``fired: False`` in its record, and so does a probe
            # that ran and stayed silent. They are different facts and only one is evidence, so
            # the refusal is rendered as no answer at all rather than as a quiet one.
            ran = p.get("status") == "measured"
            out.append(f"| {name} | {p.get('probe')} | {p.get('status')} | "
                       f"{p.get('fired') if ran else '— (no measurement)'} | "
                       f"{p.get('samples')} | {p.get('rank') if ran else '—'} |")
            if not ran:
                refused.append(f"- **{name} / {p.get('probe')} did not run:** {p.get('reason')}")
    if refused:
        out += ["", "Refusals — these rows are not silence, they are no evidence at any width:", "",
                *refused]
    caveats = {p.get("caveat") for probes in results["structure"].values() for p in probes}
    out += ["", *sorted(c for c in caveats if c), "",
            "## D. Not measured in this campaign: the 2^18 gates-per-query floor",
            "",
            "The record charges 2^18 gates per hash-oracle query "
            f"({RECORD_ASSUMPTIONS['log2_gates_per_hash_query']['where']}). The oracles in A–C are "
            "lowered from a truth table — the hash is evaluated classically and its answers wired "
            "in — so their gate counts are truth-table costs and are deliberately not reported "
            "here as a hash-circuit cost. Nothing in A–C bears on that term. It is counted "
            "separately, on a reversible SHA-256 verified against `hashlib`, by "
            "`scripts/hash_oracle_cost.py`; see that script's report for the figure, and for why a "
            "built circuit bounds the cost from above while the record needs a bound from below.",
            ""]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="directory for the json and report")
    args = parser.parse_args()
    backend = QiskitAerBackend()
    results = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": SEED,
        "record_assumptions": RECORD_ASSUMPTIONS,
        "iteration_law": iteration_law(backend),
        "multi_target_law": multi_target_law(backend),
        "structure": structure(backend),
        "not_measured_here": ["log2_gates_per_hash_query"],
        "counted_by": {"log2_gates_per_hash_query": "scripts/hash_oracle_cost.py"},
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "infra_campaign.json").write_text(json.dumps(results, indent=2, default=str))
    (args.out / "report.md").write_text(render(results))
    print(render(results))


if __name__ == "__main__":
    main()
