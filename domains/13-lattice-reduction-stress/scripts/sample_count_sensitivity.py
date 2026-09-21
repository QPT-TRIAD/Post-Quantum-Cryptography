#!/usr/bin/env python3
"""Why the two sample readings give dual costs 136 bits apart.

The production estimate reports a `rows` reading and an `exposure` reading, and the dual column
between them moves from 2^249.63 to 2^113.00 while the primal column moves 17 bits. A reader who
takes both as optima would conclude the model is unstable. It is not: the two readings sit on
opposite sides of the normal form's knife edge, and this walks the cost surface to show it.

Three facts, each measured here rather than read off the estimator's source:

1. **The normal form spends ``nu`` samples.** ``LWEParameters.normalize()`` fires when the error is
   narrower than the secret and ``m >= 2 * nu``, and it returns ``m - n``. At the recorded
   parameters that turns 608 samples into 352 and 672,352 into 672,096.
2. **The estimator's dual search is bounded by the sample count.** Its ``max_beta`` is
   ``max(min(params.m - zeta, max_beta_global), 40 + opt_step)`` evaluated on the *normalised*
   parameters, so the rows reading searches a much shorter range of block sizes than the exposure
   reading does — even though the instance, the modulus and the error are identical.
3. **At the rows reading the cost is still falling when the range ends.** That is what makes the
   returned number a bound set by the data rather than the attack's cost, and it is the only one of
   the three that a reader could not get from the source.

Two things about calling the estimator directly, both found the hard way and both recorded because a
reader will meet them:

* **Normalise first.** ``LWE.estimate`` calls ``params.normalize()`` before dispatching, so calling a
  cost function on raw parameters asks about a different instance and returns an infinite cost.
* **Register the impermanent keys.** ``dual()`` calls ``Cost.register_impermanent(...)`` before
  running; without it the cost machinery raises ``NotImplementedError: ... does not know about a key
  but should: 'mem'``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _dual_surface(params, model, lo: int, hi: int, step: int):
    """Walk the dual attack's cost over block size on already-normalised parameters."""
    from estimator.lwe_dual import DualHybrid
    from estimator.lwe_guess import distinguish
    from sage.all import oo

    points = []
    for beta in range(lo, hi + 1, step):
        cost = DualHybrid.cost(
            solver=distinguish, params=params, beta=beta, zeta=0, h1=0,
            success_probability=0.99, red_cost_model=model, log_level=0,
        )
        rop = cost["rop"]
        points.append({
            "beta": beta,
            "log2_rop": None if rop == oo else round(float(rop.log2()), 3),
            "m_used": None if cost["m"] == oo else int(cost["m"]),
            "d": None if cost["d"] == oo else int(cost["d"]),
        })
    return points


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--reading", choices=("rows", "exposure", "both"), default="both")
    ap.add_argument("--step", type=int, default=5, help="block-size stride for the surface walk")
    ap.add_argument("--span", type=int, default=140,
                    help="how far above the returned block size to keep walking")
    ap.add_argument("--output", type=Path, default=None,
                    help="write the full JSON here as well as the summary to stdout")
    args = ap.parse_args()

    from estimator.cost import Cost
    from estimator.lwe import dual
    from estimator.lwe_parameters import LWEParameters
    from estimator.nd import Uniform
    from estimator.reduction import ADPS16

    from qlwr_lattice_stress.problem.production_parameters import (
        PRODUCTION_NOISE_BOUND,
        PRODUCTION_NU,
        PRODUCTION_Q_L,
        sample_count_readings,
        samples_after_normal_form,
    )

    # ``dual()`` does this before it runs; without it the Cost machinery refuses the call.
    Cost.register_impermanent(
        rop=True, mem=False, red=True, beta=False, delta=False, m=True, d=False,
    )
    model = ADPS16(mode="classical")

    readings = ("rows", "exposure") if args.reading == "both" else (args.reading,)
    report: dict = {"readings": {}}

    for reading in readings:
        m = sample_count_readings()[reading]
        params = LWEParameters(
            n=PRODUCTION_NU,
            q=PRODUCTION_Q_L,
            Xs=Uniform(0, PRODUCTION_Q_L - 1),
            Xe=Uniform(-PRODUCTION_NOISE_BOUND, PRODUCTION_NOISE_BOUND - 1),
            m=m,
        ).normalize()

        returned = dual(params, red_cost_model=model)
        beta_returned = int(returned["beta"])

        surface = _dual_surface(
            params, model, max(2, beta_returned - 60), beta_returned + args.span, args.step
        )
        finite = [p for p in surface if p["log2_rop"] is not None]

        entry = {
            "samples_available": m,
            "samples_after_normal_form": samples_after_normal_form(reading),
            "estimator_saw_m": int(params.m),
            "returned_beta": beta_returned,
            "returned_log2_rop": round(float(returned["rop"].log2()), 3),
            "surface_range": [surface[0]["beta"], surface[-1]["beta"]],
            "surface": surface,
        }
        if finite:
            best = min(finite, key=lambda p: p["log2_rop"])
            entry["lowest_on_the_walked_range"] = best
            entry["gap_to_the_model_minimum_bits"] = round(
                entry["returned_log2_rop"] - best["log2_rop"], 3
            )
            # The load-bearing question, and the reason this script exists: did the estimator return
            # the model's minimum, or the best value inside a range something else bounded?
            entry["returned_attains_the_model_minimum"] = (
                entry["gap_to_the_model_minimum_bits"] < 0.01
            )
            # A minimum sitting on the edge of the walk means the walk was too narrow, and the
            # "optimum" beside it is an artefact of where the walk stopped. Said out loud rather
            # than left for a reader to notice.
            entry["minimum_sits_at_the_edge_of_the_walk"] = best["beta"] in (
                surface[0]["beta"], surface[-1]["beta"],
            )
        report["readings"][reading] = entry

        print(json.dumps({
            "reading": reading,
            "samples_available": m,
            "samples_after_normal_form": entry["samples_after_normal_form"],
            "estimator_saw_m": entry["estimator_saw_m"],
            "estimator_returned_beta": beta_returned,
            "estimator_returned_log2_rop": entry["returned_log2_rop"],
            "walked_beta_over": entry["surface_range"],
            "lowest_found_at_beta": entry.get("lowest_on_the_walked_range", {}).get("beta"),
            "lowest_found_log2_rop": entry.get("lowest_on_the_walked_range", {}).get("log2_rop"),
            "gap_to_the_model_minimum_bits": entry.get("gap_to_the_model_minimum_bits"),
            "returned_attains_the_model_minimum": entry.get(
                "returned_attains_the_model_minimum"
            ),
            "minimum_sits_at_the_edge_of_the_walk": entry.get(
                "minimum_sits_at_the_edge_of_the_walk"
            ),
        }, sort_keys=True), flush=True)

    report["note"] = (
        "Model output, not a measurement. `returned_attains_the_model_minimum` being false means "
        "the block size the estimator returned was bounded by something other than the attack — "
        "at the rows reading, by the sample count left after the normal form — and the cost beside "
        "it is therefore an upper bound imposed by the data available rather than the model's "
        "minimum."
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True))
        print(json.dumps({"wrote": str(args.output)}), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
