#!/usr/bin/env python3
"""Where the sample count stops mattering, which turns "which reading" into a threshold.

The production estimate reports two readings, `rows` (608) and `exposure` (672,352), 17 bits apart
on the headline. Presented as two numbers, that invites the question *which one is the answer* —
and the corpus does not say, so the question has no answer in the corpus.

Measured here, it does not need one. The cost as a function of the sample count **saturates**: past
some point, more samples change nothing, because the primal attack has already been given every
advantage the extra data can buy. Everything above the saturation point gives one identical answer,
so the entire span from the saturation point to 672,352 is one reading with one cost, and only the
region below it is in question.

That converts a choice between two readings into a property the corpus can be checked against:

    does any single secret accumulate at least `saturation_point` rows?

If yes, the exposure reading's cost applies and the number is well defined. If no, the cost is
higher and depends on the count actually reached — which is a fact about the corpus's accounting,
not about QLWR.

Why this is worth a script rather than a sentence: the answer is a threshold in the sample count and
the project's own history is of sample-count facts being written up as scheme properties. The
saturation point is not a property of QLWR either. It is a property of this parameter set, this cost
model, and this estimator revision, and the JSON records all three.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _beta(m: int, nu: int, q: int, noise_bound: int, model) -> int:
    """The primal uSVP block size the estimator returns at ``m`` samples."""
    from estimator.lwe import primal_usvp
    from estimator.lwe_parameters import LWEParameters
    from estimator.nd import Uniform

    params = LWEParameters(
        n=nu,
        q=q,
        Xs=Uniform(0, q - 1),
        Xe=Uniform(-noise_bound, noise_bound - 1),
        m=m,
    )
    return int(primal_usvp(params, red_cost_model=model)["beta"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nu", type=int, default=None)
    ap.add_argument("--coarse-step", type=int, default=10,
                    help="stride of the initial walk, refined by bisection afterwards")
    ap.add_argument("--scan-to", type=int, default=None,
                    help="highest sample count to walk; defaults to a little past the exposure")
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()

    from estimator.reduction import ADPS16

    from qlwr_lattice_stress.problem.production_parameters import (
        PRODUCTION_EXPOSURE,
        PRODUCTION_M,
        PRODUCTION_NOISE_BOUND,
        PRODUCTION_NU,
        PRODUCTION_Q_L,
        sample_count_readings,
    )

    nu = args.nu if args.nu is not None else PRODUCTION_NU
    q, noise_bound = PRODUCTION_Q_L, PRODUCTION_NOISE_BOUND
    scan_to = args.scan_to if args.scan_to else int(PRODUCTION_EXPOSURE ** 0.5) + nu
    model = ADPS16(mode="classical")

    readings = sample_count_readings()
    start = min(readings.values())

    # Walk the whole scanned range. **Not** stopping at the first plateau: the block size as a
    # function of the sample count is a non-increasing step function, and it has more than one flat
    # region, so two equal consecutive readings mean a step and not the floor. Stopping there reports
    # the first step as the saturation point and understates the threshold by twelve samples at the
    # recorded parameters — which is how this loop was written the first time.
    walk: list[dict] = []
    for m in range(start, scan_to + 1, args.coarse_step):
        walk.append({
            "m": m,
            "m_over_nu": round(m / nu, 4),
            "beta_usvp": _beta(m, nu, q, noise_bound, model),
        })

    betas = [point["beta_usvp"] for point in walk]
    target = min(betas)
    first_at_target = betas.index(target)

    if first_at_target == len(walk) - 1:
        print(json.dumps({
            "error": "the block size was still falling at the end of the scanned range",
            "scanned_to": scan_to,
            "lowest_seen": target,
            "note": (
                "the floor is at or above the edge of the scan, so no saturation point is "
                "established; re-run with a larger --scan-to"
            ),
        }, sort_keys=True))
        return 1

    # Bisect the interval the floor was first attained in, so the reported threshold is the true
    # first attainment rather than a multiple of the stride.
    lo = walk[first_at_target - 1]["m"] if first_at_target > 0 else start - 1
    hi = walk[first_at_target]["m"]
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if _beta(mid, nu, q, noise_bound, model) == target:
            hi = mid
        else:
            lo = mid
    saturation = hi
    last_above = lo
    # Every block size the walk passed through, with the first count that reached it. Reported so a
    # reader can see the step structure the threshold sits in rather than only the threshold.
    steps = [
        {"beta_usvp": beta, "first_seen_at_m": walk[betas.index(beta)]["m"]}
        for beta in sorted(set(betas), reverse=True)
    ]

    report = {
        "nu": nu,
        "q_l": q,
        "noise_bound": noise_bound,
        "estimator_revision": None,
        "cost_model": "ADPS16(classical)",
        "scan_from": start,
        "scan_to": scan_to,
        "coarse_step": args.coarse_step,
        "saturation_point": saturation,
        "saturation_m_over_nu": round(saturation / nu, 4),
        "beta_at_and_above_saturation": target,
        "last_sample_count_below_saturation": last_above,
        "beta_there": _beta(last_above, nu, q, noise_bound, model),
        "steps_walked": steps,
        "coarse_walk": walk,
        "recorded_readings": {
            reading: {
                "m": m,
                "at_or_above_saturation": m >= saturation,
                "beta_usvp": _beta(m, nu, q, noise_bound, model),
            }
            for reading, m in sorted(readings.items())
        },
    }
    try:  # recorded when the estimator exposes its revision; the estimate notes cite it by hash
        import subprocess
        report["estimator_revision"] = subprocess.run(
            ["git", "-C", str(Path(__import__("estimator").__file__).resolve().parents[1]),
             "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or None
    except Exception:
        pass

    report["steps_note"] = (
        "`first_seen_at_m` is where the coarse walk first observed each block size, so it is a "
        "multiple of the stride. The floor's entry is the one exception: it is refined by bisection "
        "to `saturation_point`, which is the number to use."
    )
    report["note"] = (
        "Above `saturation_point` the primal cost is constant, so every sample count from there to "
        f"{PRODUCTION_EXPOSURE} yields one identical estimate. The question a reader needs answered "
        "is therefore not which reading was meant but whether any single secret reaches the "
        "saturation point: at or above it the exposure reading's cost applies unchanged, below it "
        "the cost depends on the count actually reached. Both the saturation point and the cost "
        "model's output are properties of this parameter set and estimator revision, not of QLWR."
    )

    print(json.dumps({
        "saturation_point": saturation,
        "saturation_m_over_nu": report["saturation_m_over_nu"],
        "beta_at_and_above_saturation": target,
        "last_sample_count_below_saturation": last_above,
        "beta_there": report["beta_there"],
        "steps_walked": steps,
        "recorded_readings": report["recorded_readings"],
    }, sort_keys=True))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps({"wrote": str(args.output)}), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
