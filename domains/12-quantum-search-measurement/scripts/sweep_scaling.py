#!/usr/bin/env python3
"""Measure circuit cost across the configured widths, refusing what will not fit.

Usage:
    .venv/bin/python scripts/sweep_scaling.py --config config/default_experiment.yaml

Each width in ``sweep.qubit_range`` gets a row: the width of the circuit under each lowering, the
gate count and depth counted from the gate-list IR, and a provenance flag. A width is never dropped
because it could not be run — it is recorded as a refusal with the reason and the size that made it
one, and the report prints those in their own table.

Two things this script deliberately does not do. It does not attempt a point and hope the machine
survives it: the statevector a point would need is computed from its width and compared against the
budget *before* anything is allocated, which is the only time a budget can be useful. And it does
not simulate: a gate count is a property of the circuit as written, so the sweep reaches widths
whose execution nobody can afford, which is the whole reason the cost curve extends past the
simulated ceiling.

The same sweep is available from the module itself, as
``PYTHONPATH=src .venv/bin/python -m grover_emulator.cli sweep`` (or as ``grover-emulator sweep``
once the package is installed).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grover_emulator.cli import app  # noqa: E402


def main() -> int:
    argv = ["sweep", *sys.argv[1:]]
    if len(argv) == 1:
        argv.extend(["--config", "config/default_experiment.yaml"])
    try:
        app(argv)
    except SystemExit as exit_:  # typer signals through SystemExit; pass the code through
        return int(exit_.code or 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
