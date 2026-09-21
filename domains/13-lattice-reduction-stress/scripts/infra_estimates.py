#!/usr/bin/env python3
"""The PQ infrastructure program's lattice numbers, put beside the estimator's.

The infrastructure record (TLS/PKI S3, migration S6, and its audit ledger) carries one table of
"attack gates" per NIST category and treats the category-5 entry as the cost of attacking
ML-KEM-1024:

    CATEGORY_ATTACK_GATES = {1: 83, 2: 100, 3: 116, 5: 148}      (log2 gates)

It attributes the table to the v1.43 finalization, which does not contain it, and the record's own
audit says the numbers are "not re-derived". They decode as 64+19, 96+20 and 128+20: Grover key
search on AES-128/192/256 at 2^19-2^20 gates per AES evaluation. That is NIST's *definition* of
categories 1, 3 and 5 — a floor every scheme in the category must clear — and not the cost of any
lattice attack. Using the floor as a scheme's cost is conservative exactly as long as the best
known lattice attack on the scheme costs at least the floor, which the record never checks.

This script checks it, with the estimator NIST submitters use, for the lattice schemes the
infrastructure program deploys: ML-KEM (as Kyber512/768/1024) and ML-DSA (as Dilithium2/3/5).

What the comparison can and cannot say. The estimator's numbers are core-SVP operation counts
(ADPS16: 0.292*beta classical, 0.265*beta quantum), which deliberately *under*-count — one SVP call,
no polynomial factors, no memory. The record's floors are gate counts. So "core-SVP >= floor" is a
comparison that errs toward the attacker on the lattice side, and a scheme that passes it passes
with room; a scheme that fails it has not thereby been broken. Nothing here is measured: these are
analytic estimates at full scale, and the report labels every one of them theoretical.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qlwr_lattice_stress.analysis.cost_estimation import (  # noqa: E402
    estimate,
    reference_parameter_set,
)
from qlwr_lattice_stress.reporting.report_generator import SCOPE_BOUNDARY  # noqa: E402

#: The record's table, as named values with where it states them — nothing is read from the record
#: at run time. The decomposition is this script's reading of the numbers, not the record's.
RECORD_CATEGORY_FLOOR_LOG2_GATES = {1: 83, 2: 100, 3: 116, 5: 148}
RECORD_WHERE = ("pq_infra_s6_migration_agility_v2.0.py:50 (CATEGORY_ATTACK_GATES); "
                "pq_audit_ledger_v2.1.py:151,156,166 (148 as 'ML-KEM-1024'); attributed to the "
                "v1.43 finalization, which does not contain the table")
FLOOR_DECODES_AS = {1: "64 + 19  (Grover on AES-128)", 3: "96 + 20  (Grover on AES-192)",
                    5: "128 + 20 (Grover on AES-256)"}
QPT_BUDGET_LOG2_GATES = 128

#: (estimator name, standardised name, NIST category, where the infrastructure program uses it)
SCHEMES = (
    ("Kyber512", "ML-KEM-512", 1, "S3 TLS key exchange, S6 hybrids"),
    ("Kyber768", "ML-KEM-768", 3, "S3 TLS key exchange, S6 hybrids"),
    ("Kyber1024", "ML-KEM-1024", 5, "S3 TLS key exchange, S6 hybrids; the record's '148'"),
    ("Dilithium2_MSIS_WkUnf", "ML-DSA-44", 2, "S3 PKI certificates"),
    ("Dilithium3_MSIS_WkUnf", "ML-DSA-65", 3, "S3 PKI certificates"),
    ("Dilithium5_MSIS_WkUnf", "ML-DSA-87", 5, "S3 PKI certificates; B0 certificate baseline"),
)


def row_for(estimator_name: str, standard_name: str, category: int, used_in: str) -> dict:
    report = estimate(reference_parameter_set(estimator_name))
    floor = RECORD_CATEGORY_FLOOR_LOG2_GATES[category]
    # The quantum figure where the path gives one; the SIS path is classical-only, and a classical
    # number is not silently promoted into the quantum column.
    quantum, classical = report.rop_quantum_log2_min, report.rop_classical_log2_min
    judged, basis = (quantum, "quantum core-SVP") if quantum is not None else (
        classical, "classical only - this estimator path reports no quantum figure")
    return {
        "scheme": standard_name, "estimator_parameter_set": estimator_name,
        "nist_category": category, "used_in": used_in,
        "beta_usvp": report.beta_usvp, "beta_dual": report.beta_dual,
        "classical_log2": classical, "quantum_log2": quantum,
        "cost_model": report.red_cost_model, "cheapest_attack": report.minimum_over_models,
        "record_floor_log2_gates": floor,
        "judged_on": basis,
        "clears_record_floor": None if judged is None else judged >= floor,
        "margin_over_floor_bits": None if judged is None else round(judged - floor, 2),
        "clears_qpt128_budget": None if judged is None else judged >= QPT_BUDGET_LOG2_GATES,
        "provenance": "theoretical (analytic estimate at full scale; not measured)",
        "estimator_revision": report.estimator_revision,
    }


def render(results: dict) -> str:
    out = [
        "# PQ infrastructure program: the lattice numbers beside the estimator's",
        "", SCOPE_BOUNDARY, "",
        "**Everything in this report is theoretical.** No lattice was built or reduced: these are "
        "the estimator's analytic costs at full scale. Core-SVP under-counts an attack's cost, and "
        "the record's floors are gate counts, so each comparison below errs toward the attacker.",
        "",
        "## The record's table is a category floor, not a lattice cost",
        "",
        f"Stated at: {RECORD_WHERE}.",
        "",
        "| category | record, log2 gates | decodes as |", "|---|---|---|",
        *[f"| {c} | {RECORD_CATEGORY_FLOOR_LOG2_GATES[c]} | {FLOOR_DECODES_AS.get(c, '—')} |"
          for c in sorted(RECORD_CATEGORY_FLOOR_LOG2_GATES)],
        "",
        "## Estimator cost of the best known lattice attack — theoretical",
        "",
        "| scheme | cat | β usvp | β dual | classical log2 | quantum log2 | record floor | "
        "margin (bits) | ≥ floor | ≥ 2^128 budget | judged on |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results["rows"]:
        def cell(v):
            return "—" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v))
        out.append(
            f"| {r['scheme']} | {r['nist_category']} | {cell(r['beta_usvp'])} | "
            f"{cell(r['beta_dual'])} | {cell(r['classical_log2'])} | {cell(r['quantum_log2'])} | "
            f"{r['record_floor_log2_gates']} | {cell(r['margin_over_floor_bits'])} | "
            f"{cell(r['clears_record_floor'])} | {cell(r['clears_qpt128_budget'])} | "
            f"{r['judged_on']} |")
    out += ["", "Cost models: " + "; ".join(sorted({r["cost_model"] for r in results["rows"]}))
            + f". Estimator revision {results['rows'][0]['estimator_revision'][:12]}.", ""]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="directory for the json and report")
    args = parser.parse_args()
    results = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "record_floor_log2_gates": RECORD_CATEGORY_FLOOR_LOG2_GATES,
        "record_where": RECORD_WHERE,
        "rows": [row_for(*scheme) for scheme in SCHEMES],
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "infra_estimates.json").write_text(json.dumps(results, indent=2))
    (args.out / "report.md").write_text(render(results))
    print(render(results))


if __name__ == "__main__":
    main()
