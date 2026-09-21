#!/usr/bin/env python3
"""Run the milestone-0 API probe and exit non-zero if any required check failed.

Thin wrapper so the probe is reachable the same way as every other script here, and so that
``PYTHONPATH`` handling lives in one place rather than in the caller's shell.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qlwr_lattice_stress.utils.api_probe import format_report, probe_all, required_failures

if __name__ == "__main__":
    checks = probe_all()
    print(format_report(checks))
    raise SystemExit(1 if required_failures(checks) else 0)
