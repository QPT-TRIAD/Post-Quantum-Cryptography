#!/usr/bin/env python3
"""Does G6K sieve correctly on a lattice wider than ``MAX_SIEVING_DIM``?

The clean sweep emitted, twice, on its d130 and d160 points:

    UserWarning: Dimension of lattice is larger than maximum supported. To fix this warning, change
    the value of MAX_SIEVING_DIM in siever.h and recompile.

``MAX_SIEVING_DIM`` is 128 (``kernel/siever.h:83``) and the warning fires from ``siever.pyx:107``
when ``full_n > 128``. Dimensions 130 and 160 give lattices 131 and 161 wide, so the warning starts
exactly between the d100 points (101 wide, no warning) and the d130 points (131 wide).

Reading the source says it is over-conservative: ``full_n`` is an ``unsigned int`` and
``full_muT``/``full_rr`` are ``std::vector``s sized to it, while the fixed ``std::array<ZT,
MAX_SIEVING_DIM>`` buffers hold *local* sieve coordinates. On that reading the macro bounds the
sieving block size, not the lattice.

**This project does not accept readings.** The probe checks the claim by a route that would fail if
the reading were wrong: the same lattice, above the limit, reduced by **two independent engines** at
the same block size. If G6K is silently doing something else above 128, it and fpylll will not agree
about whether the planted vector was found — and unlike a norm or a timing, the agreement is not a
quantity either engine reports about itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dimension", "-d", type=int, default=130,
                    help="raw instance dimension; the lattice is this plus one")
    ap.add_argument("--block-size", "-b", type=int, default=20)
    ap.add_argument("--repeat", type=int, default=3,
                    help="block sizes to test, stepping by 10 from --block-size")
    args = ap.parse_args()

    from qlwr_lattice_stress.attacks.primal_attack import prepare_primal, run_primal_attack
    from qlwr_lattice_stress.config.schema import load_config
    from qlwr_lattice_stress.engines import FpylllBKZEngine, build_engine
    from qlwr_lattice_stress.pipeline import build_instance
    from qlwr_lattice_stress.utils.seeding import RunSeeds, root_from_environment

    config = load_config(str(Path(__file__).resolve().parents[1]
                              / "config" / "default_experiment.yaml"))
    point = config.model_copy(update={
        "instance": config.instance.model_copy(update={"target_dimension": args.dimension}),
        "run_id": None,
    })
    seeds = RunSeeds(root=root_from_environment(point.instance.seed))
    instance = build_instance(point, seeds)

    nf, factor, basis, planted = prepare_primal(instance)

    print(json.dumps({
        "raw_dimension": args.dimension,
        "lattice_dimension": basis.nrows,
        "above_max_sieving_dim": basis.nrows > 128,
        "max_sieving_dim": 128,
        "embedding_factor": factor,
    }), flush=True)

    engines = {
        "g6k_sieve": build_engine("g6k", threads=1),
        "fpylll_bkz": FpylllBKZEngine(threads=1),
    }

    for step in range(args.repeat):
        beta = args.block_size + 10 * step
        row: dict = {"block_size": beta}
        for name, engine in engines.items():
            from fpylll import IntegerMatrix

            fresh = IntegerMatrix(basis.nrows, basis.ncols, int_type="mpz")
            for r in range(basis.nrows):
                for c in range(basis.ncols):
                    fresh[r, c] = basis[r, c]
            result = run_primal_attack(instance, engine, beta,
                                       prepared=(nf, factor, fresh, planted))
            row[name] = {
                "recovered": bool(result.recovered),
                "root_hermite_factor": (round(float(result.root_hermite_factor), 8)
                                        if result.root_hermite_factor is not None else None),
                "wall_clock_s": round(result.wall_clock_s, 2),
            }
        row["agree"] = row["g6k_sieve"]["recovered"] == row["fpylll_bkz"]["recovered"]
        print(json.dumps(row), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
