#!/usr/bin/env python3
"""Run the configured dimension sweep, one experiment per point.

Every point is a full run, and a point that cannot be run is recorded as its own result rather than
aborting the sweep — a sweep that stopped at the first refusal would report a shorter range as
though it were the configured one.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qlwr_lattice_stress.config.schema import load_config  # noqa: E402
from qlwr_lattice_stress.pipeline import run_sweep  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", "-c", required=True)
    args = ap.parse_args()

    outcomes = run_sweep(load_config(args.config))
    print(json.dumps(outcomes, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
