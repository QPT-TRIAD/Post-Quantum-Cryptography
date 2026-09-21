#!/usr/bin/env python3
"""Where each attack family stops applying, and how much room the recorded parameters have.

An infinite cost from the estimator is not a large number; it is the model declining to answer. The
build's own documentation stated that outcome as a property of QLWR instances — *"`usvp` comes back
infinite ... only `dual` returns numbers"* — and that is wrong in a way that matters, because the
production estimate's headline **is** the `usvp` number. It applies at the recorded parameters. What
the earlier reading had actually measured was the behaviour at a low sample count.

Measured here instead, at the production modulus pair and a given secret dimension:

* the smallest sample count at which each family returns anything at all;
* where the recorded readings sit relative to those thresholds.

The margin is the point. At nu = 256 the recorded rows reading clears the `usvp` threshold by 76
samples. An instance a little below it does not produce a *high* cost; it produces **no applicable
attack**, and a report that rendered those two as the same thing would be describing a model that
declined to run as though it had run and found the scheme strong.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nu", type=int, default=256, help="secret dimension to sweep at")
    ap.add_argument("--families", default="usvp,dual",
                    help="comma-separated estimator families to bracket")
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    from sage.all import oo

    from estimator.lwe import dual, primal_usvp
    from estimator.lwe_parameters import LWEParameters
    from estimator.nd import Uniform
    from estimator.reduction import ADPS16

    from qlwr_lattice_stress.problem.production_parameters import (
        PRODUCTION_EXPOSURE,
        PRODUCTION_M,
        PRODUCTION_NOISE_BOUND,
        PRODUCTION_Q_L,
    )

    model = ADPS16(mode="classical")
    funcs = {"usvp": primal_usvp, "dual": dual}
    families = [f.strip() for f in args.families.split(",") if f.strip()]

    def applies(func, params) -> bool:
        try:
            return func(params, red_cost_model=model)["rop"] != oo
        except Exception:
            # A family that raises is not applying either. Recorded as False rather than swallowed,
            # since the question here is only whether a number came back.
            return False

    # Below 2*nu the estimator does not normalise at all, so the sweep starts at nu and the
    # thresholds are reported against both counts.
    threshold: dict[str, int | None] = {f: None for f in families}
    transitions: list[dict] = []
    previous: tuple | None = None

    for m in range(args.nu, max(PRODUCTION_M, args.nu) * 4 + 1):
        params = LWEParameters(
            n=args.nu,
            q=PRODUCTION_Q_L,
            Xs=Uniform(0, PRODUCTION_Q_L - 1),
            Xe=Uniform(-PRODUCTION_NOISE_BOUND, PRODUCTION_NOISE_BOUND - 1),
            m=m,
        ).normalize()
        current = tuple(applies(funcs[f], params) for f in families)
        if current != previous:
            for f, now in zip(families, current):
                if now and threshold[f] is None:
                    threshold[f] = m
            transitions.append({
                "m": m,
                "m_over_nu": round(m / args.nu, 4),
                "samples_after_normal_form": int(params.m),
                **{f: now for f, now in zip(families, current)},
            })
            previous = current
        if all(v is not None for v in threshold.values()):
            break

    report = {
        "nu": args.nu,
        "q_l": PRODUCTION_Q_L,
        "noise_bound": PRODUCTION_NOISE_BOUND,
        "families": families,
        "thresholds": threshold,
        "transitions": transitions,
        "recorded_readings": {
            "rows": {
                "m": PRODUCTION_M,
                "samples_after_normal_form": PRODUCTION_M - args.nu,
                **{f: (PRODUCTION_M >= threshold[f] if threshold[f] else None)
                   for f in families},
            },
            "exposure": {
                "m": PRODUCTION_EXPOSURE,
                "samples_after_normal_form": PRODUCTION_EXPOSURE - args.nu,
                **{f: (PRODUCTION_EXPOSURE >= threshold[f] if threshold[f] else None)
                   for f in families},
            },
        },
    }
    report["note"] = (
        "An infinite cost is the model declining to answer, not a large number. Compare the "
        "thresholds against the recorded readings before quoting any cost: below a threshold the "
        "correct statement is 'no applicable attack in this model', which is not a security claim."
    )

    for f in families:
        t = threshold[f]
        print(json.dumps({
            "family": f,
            "smallest_sample_count_that_applies": t,
            "m_over_nu": round(t / args.nu, 4) if t else None,
            "rows_margin_samples": (PRODUCTION_M - t) if t else None,
        }, sort_keys=True), flush=True)
    print(json.dumps({"transitions": transitions}))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps({"wrote": str(args.output)}), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
