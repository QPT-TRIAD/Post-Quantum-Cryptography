#!/usr/bin/env python3
"""Recompute the corpus's two QPT-128 margins from its own recorded rows.

The corpus quotes two margins for the hidden-signer construction that do not obviously agree —
**+29.4 bits** (`QPT128_finalization_v1.43.md:210`, Mode S) and **+7.7 bits**
(`modeB_security_v1.49.md:135`, Mode B) — and neither is a lattice number. This script recomputes
both from their recorded rows under the corpus's own combination rule, so that neither has to be
taken on trust, and reports what actually separates them.

It finds two things, and only the second is a defect:

1. **The margins are not in conflict.** Both ledgers report `log2 Pr/G`, both are combined as
   `log2(sum(2**row))` against `KAPPA = 130`, and both reproduce. What separates them is a row:
   Mode S has no proof-soundness entry because Mode S is a profile with, in the corpus's own words,
   *"only the proof is missing"* (`sidecar_free_finalization_v1.44.md:105`). Supplying the proof
   introduces R3, R3 dominates, and the margin falls. **The gap is the price of the proof system.**

2. **Mode B's quoted margin charges proof soundness twice.** The v1.49 revision replaces the
   DFMS-modelled R3 with one in FAEST v2 Lemma 9.39 form, but stores it under a *different key*, and
   the total is summed over the rows mapping — so both are counted. That is what produces 7.669,
   printed as 7.7. Charged once, under the FAEST form the revision argues from, the margin is 8.081.

The second finding is **conservative**: it understates the margin, so it errs against the scheme and
inflates no security claim. It is reported because a figure quoted to 0.1 bits should be reproducible
from its own rows, and this one is not until the double charge is named.

Nothing here executes corpus code or reads the research tree. The row values are recorded constants
in `problem/qpt128_accounting.py`, with their citations; this script is arithmetic over them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    from qlwr_lattice_stress.problem.qpt128_accounting import margin_reconciliation

    report = margin_reconciliation()
    mode_s, mode_b = report["mode_s"], report["mode_b"]

    print(json.dumps({
        "ledger_rule": report["rule"],
        "kappa": report["kappa"],
        "mode_s": {
            "rows": {k: round(v, 3) for k, v in mode_s["rows"].items()},
            "recomputed_total_log2": mode_s["recomputed_total_log2"],
            "recorded_total_log2": mode_s["recorded_total_log2"],
            "residual_bits": mode_s["residual_bits"],
            "residual_is_rounding": mode_s["residual_is_rounding"],
            "d2_margin_bits": mode_s["recomputed_d2_margin_bits"],
        },
    }, sort_keys=True), flush=True)

    for key, variant in mode_b["variants"].items():
        print(json.dumps({
            "mode_b_variant": key,
            "rows_counted": variant["rows_counted"],
            "total_log2": variant["total_log2"],
            "d2_margin_bits": variant["d2_margin_bits"],
        }, sort_keys=True), flush=True)

    print(json.dumps({
        "mode_b_recorded_total_log2": mode_b["recorded_total_log2"],
        "mode_b_recorded_d2_margin_bits": mode_b["recorded_d2_margin_bits"],
        "reproducing_variant": mode_b["reproducing_variant"],
        "residual_bits": mode_b["residual_bits"],
        "double_charge_costs_bits": mode_b["double_charge_costs_bits"],
        "error_is_conservative": mode_b["error_is_conservative"],
    }, sort_keys=True), flush=True)

    # The one comparison a reader is most likely to attempt, refused explicitly rather than left to
    # be discovered: these margins and the lattice estimate are not the same quantity.
    print(json.dumps({
        "cross_currency_note": report["note"],
    }, sort_keys=True), flush=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps({"wrote": str(args.output)}), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
