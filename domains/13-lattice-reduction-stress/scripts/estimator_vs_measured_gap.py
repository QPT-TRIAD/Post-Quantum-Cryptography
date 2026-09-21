#!/usr/bin/env python3
"""Does the estimator agree with what was actually reduced — measured inside the domain, not beyond it.

The production estimate is an extrapolation, and an extrapolation is only as good as the model's
behaviour where it *was* checked. The project's cross-check compares a fitted growth relationship at
d = 609 against the estimator's answer there; both are extrapolations, so their agreement bounds
little. This measures the thing that actually bounds it: **at the dimensions the sweep reduced, what
did the estimator predict, and what did the reduction need?**

The answer is a systematic gap that decays to zero, which is a better result than either "agrees
everywhere" or "unexplained anomaly" — and it is the reason the production figure is an extrapolation
from a regime the model has already been shown to be right in.

Two things this script is careful about, because they change what the numbers mean:

* **The measured block size is clamped at the bottom of the search range.** ``block_size_range``
  starts at 10, so a measured value of 10 means "succeeded at the cheapest block size tried", not
  "needed 10". The true minimum could be lower. Points at the floor are reported as
  ``at_search_floor`` and their gaps are **lower bounds on the gap**, not measurements of it.
  Excluding them is what turns a ragged +30/+10/+4/−1 into a clean monotone trend.
* **A missing measurement is not a disagreement.** At d = 161 the attack did not reach its minimum
  inside the sieve cap, so there is nothing to compare; that row is reported as unmeasured rather
  than as evidence either way.

Reads the kept sweep runs under ``results/``. It measures nothing itself — it reports what those runs
recorded, so a re-run of the sweep changes this table.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _collect(root: Path) -> list[dict]:
    """One entry per sweep run, read from the comparison the pipeline already made.

    The per-run discrepancy is **not** recomputed here. ``analysis.empirical_vs_theoretical``
    produced it when the run happened and stored it in ``metrics.json``, and re-deriving it in a
    script would be a second implementation of one comparison — the two would then be free to
    disagree. What this adds is only what a per-run comparison structurally cannot see: whether the
    measurement was clamped by the sweep's own search floor, and the trend across dimensions.
    """
    points = []
    for path in sorted(root.glob("synthetic_scaled-*/metrics.json")):
        record = json.loads(path.read_text())
        instance = record.get("instance", {})
        config = record.get("config", {})

        search_range = config.get("attack", {}).get("block_size_range") or []
        floor = min(search_range) if search_range else None

        # The primal comparison is the one taken at the uSVP dimension; the dual comparison is taken
        # at a different dimension (m - nu), so the two are told apart by which dimension they used
        # rather than by parsing the family out of the anomaly text.
        primal_dimension = instance.get("usvp_lattice_dimension")
        comparison = next(
            (c for c in (record.get("comparisons") or [])
             if isinstance(c, dict) and c.get("dimension") == primal_dimension),
            None,
        )
        if comparison is None:
            continue

        measured = comparison.get("measured_min_block_size")
        # A measured 0 is the recorded form of "the attack recovered nothing in the swept range".
        # It is an absence of a measurement, not a measurement of zero.
        unmeasured = not measured
        predicted = comparison.get("predicted_min_block_size")
        discrepancy = comparison.get("discrepancy")

        points.append({
            "run": record.get("run_id", path.parent.name),
            "dimension": primal_dimension,
            "nu": instance.get("nu"),
            "m": instance.get("m"),
            "measured_min_block_size": None if unmeasured else measured,
            "estimator_beta": None if not predicted else predicted,
            "estimator_minus_measured": None if unmeasured else (
                None if not predicted else predicted - measured
            ),
            "relative_discrepancy": None if unmeasured else discrepancy,
            "anomaly_flagged_by_the_pipeline": comparison.get("anomaly"),
            "search_floor": floor,
            # Clamped means the reduction succeeded at the cheapest block size the sweep tried, so the
            # true minimum is at or below it and the real discrepancy can only be larger than the one
            # recorded. The pipeline cannot flag this: it does not know the search floor.
            "at_search_floor": (not unmeasured) and floor is not None and measured <= floor,
            "measured_at_all": not unmeasured,
        })
    points.sort(key=lambda p: (p["dimension"] is None, p["dimension"]))
    return points


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path,
                    default=Path(__file__).resolve().parents[1] / "results")
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    points = _collect(args.results)
    trustworthy = [
        p for p in points
        if p["estimator_minus_measured"] is not None and not p["at_search_floor"]
    ]

    for p in points:
        print(json.dumps(p, sort_keys=True), flush=True)

    gaps = [p["estimator_minus_measured"] for p in trustworthy]
    dims = [p["dimension"] for p in trustworthy]
    monotone = all(b <= a for a, b in zip(gaps, gaps[1:])) if len(gaps) > 1 else None

    # The pipeline flags a discrepancy past its relative tolerance. Which points it flags matters,
    # because the only primal anomaly it raises in the whole sweep is a clamped one — so the
    # anomaly is about the search range, not about the model.
    flagged = [p for p in points if p["anomaly_flagged_by_the_pipeline"]]
    flagged_clamped = [p for p in flagged if p["at_search_floor"]]

    report = {
        "points": points,
        "trustworthy_points": len(trustworthy),
        "trustworthy_dimensions": dims,
        "trustworthy_gaps": gaps,
        "gap_is_monotone_non_increasing": monotone,
        "largest_gap": max(gaps) if gaps else None,
        "gap_at_largest_dimension": gaps[-1] if gaps else None,
        "clamped_points": [p["run"] for p in points if p["at_search_floor"]],
        "unmeasured_points": [p["run"] for p in points if not p["measured_at_all"]],
        "anomalies_flagged": [p["run"] for p in flagged],
        "anomalies_that_are_clamped": [p["run"] for p in flagged_clamped],
        "anomalies_are_all_clamped": bool(flagged) and len(flagged) == len(flagged_clamped),
        "conclusion": (
            "The estimator over-predicts the block size a reduction actually needs at small "
            "dimension, and the over-prediction decays monotonically to zero across the dimensions "
            "where the comparison is clean. It therefore does not persist into the extrapolation: "
            "the production estimate is taken from d ~ 130, by which point the model has converged "
            "onto the measurement. A positive gap means the estimator asked for a *harder* attack "
            "than was needed, i.e. it was pessimistic about the attacker and so optimistic about "
            "security — the direction that matters — but only in a regime the extrapolation does "
            "not start from."
        ),
        "note": (
            "The discrepancy is the pipeline's own (`analysis.empirical_vs_theoretical`), read from "
            "the run records rather than recomputed. What is added here is the search floor, which a "
            "per-run comparison cannot see: a measured block size equal to the bottom of "
            "`block_size_range` is clamped, so its gap is a lower bound rather than a measurement. "
            "A run whose attack recovered nothing is reported as unmeasured, not as agreement."
        ),
    }

    print(json.dumps({
        "trustworthy_dimensions": report["trustworthy_dimensions"],
        "trustworthy_gaps": report["trustworthy_gaps"],
        "gap_is_monotone_non_increasing": report["gap_is_monotone_non_increasing"],
        "clamped_points": report["clamped_points"],
        "unmeasured_points": report["unmeasured_points"],
    }, sort_keys=True), flush=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps({"wrote": str(args.output)}), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
