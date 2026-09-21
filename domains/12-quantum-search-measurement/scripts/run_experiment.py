#!/usr/bin/env python3
"""Run the configured experiment end to end and write its results directory.

Usage:
    .venv/bin/python scripts/run_experiment.py --config config/default_experiment.yaml

The same run is available from the module itself::

    PYTHONPATH=src .venv/bin/python -m grover_emulator.cli run --config config/default_experiment.yaml

or as the ``grover-emulator`` console script once ``pip install -e .`` has put the package on the
path. This wrapper exists so the documented command works either way — it adds ``src`` and hands its
arguments to the CLI unchanged, so the option parsing is the CLI's and there is one definition of
what a run is.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grover_emulator.cli import app  # noqa: E402


def main() -> int:
    argv = ["run", *sys.argv[1:]]
    if len(argv) == 1:
        argv.append("--config")
        argv.append("config/default_experiment.yaml")
    try:
        app(argv)
    except SystemExit as exit_:  # typer signals through SystemExit; pass the code through
        return int(exit_.code or 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
