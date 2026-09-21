#!/usr/bin/env python3
"""Is one BKZ reduction at one block size the same across processes?

Run as a **separate process** per repetition, because that is the axis the question is about. The
same instance, the same block size, the same engine: if ``recovered`` differs between processes, the
result is not reproducible from its own record, and cross-check 7 does not hold at the attack layer.

Two modes:

``--unseeded``
    as the engine ships today — nothing calls ``fpylll.util.set_random_seed``.
``--seeded N``
    ``set_random_seed(N)`` before the reduction, to test whether fplll's rerandomisation is the cause.

Prints one line per repetition: the recovered flag, the first-row norm, and the tour count.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", "-c", default=str(Path(__file__).resolve().parents[1]
                                                 / "config" / "default_experiment.yaml"))
    ap.add_argument("--dimension", "-d", type=int, default=80)
    ap.add_argument("--block-size", "-b", type=int, default=10)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--seeded", type=int, default=None,
                    help="seed for fplll's RNG; omit to leave it unseeded as the engine does")
    ap.add_argument("--engine", "-e", default=None,
                    help="engine name; defaults to the config's first preference")
    ap.add_argument("--threads", "-t", type=int, default=None,
                    help="threads; defaults to the config's value")
    args = ap.parse_args()

    from qlwr_lattice_stress.attacks.primal_attack import prepare_primal, run_primal_attack
    from qlwr_lattice_stress.config.schema import load_config
    from qlwr_lattice_stress.engines import build_engine

    config = load_config(args.config)
    point = config.model_copy(update={
        "instance": config.instance.model_copy(update={"target_dimension": args.dimension}),
        "run_id": None,
    })

    from qlwr_lattice_stress.pipeline import build_instance
    from qlwr_lattice_stress.utils.seeding import RunSeeds, root_from_environment

    seeds = RunSeeds(root=root_from_environment(point.instance.seed))
    instance = build_instance(point, seeds)

    if args.seeded is not None:
        from fpylll.util import set_random_seed

        set_random_seed(args.seeded)

    engine_name = args.engine or point.engine.preference[0].value
    threads = args.threads if args.threads is not None else point.engine.threads
    engine = build_engine(engine_name, threads=threads)
    prepared = prepare_primal(instance)
    nf, factor, basis, planted = prepared

    print(json.dumps({
        "dimension": args.dimension,
        "block_size": args.block_size,
        "lattice_dimension": basis.nrows,
        "embedding_factor": factor,
        "engine": getattr(engine, "name", engine_name),
        "threads": threads,
        "seeded": args.seeded,
        "seed_root": seeds.root,
        "pid": os.getpid(),
    }))

    for i in range(args.repeats):
        # A fresh copy each time: the engine mutates in place, so reusing the basis would measure
        # the reduction of an already-reduced lattice — a different question, and one that would
        # look like a reproducibility success.
        from fpylll import IntegerMatrix

        fresh = IntegerMatrix(basis.nrows, basis.ncols, int_type="mpz")
        for r in range(basis.nrows):
            for c in range(basis.ncols):
                fresh[r, c] = basis[r, c]

        result = run_primal_attack(instance, engine, args.block_size,
                                   prepared=(nf, factor, fresh, planted))
        print(json.dumps({
            "repeat": i,
            "recovered": bool(result.recovered),
            "wall_clock_s": round(result.wall_clock_s, 3),
            "root_hermite_factor": (round(float(result.root_hermite_factor), 8)
                                    if result.root_hermite_factor is not None else None),
        }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
