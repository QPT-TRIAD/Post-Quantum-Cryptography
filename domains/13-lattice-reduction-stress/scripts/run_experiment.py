#!/usr/bin/env python3
"""Run one experiment from a config.

A thin wrapper over ``qlwr_lattice_stress.pipeline.run_experiment`` so the library path is the one
exercised — a result should be reproducible by calling the same function rather than by
reconstructing a command line.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qlwr_lattice_stress.config.schema import load_config  # noqa: E402
from qlwr_lattice_stress.pipeline import run_experiment  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", "-c", required=True)
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args()

    results = run_experiment(load_config(args.config), run_id=args.run_id)
    print(json.dumps({k: v for k, v in results.items() if k != "attacks"}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
