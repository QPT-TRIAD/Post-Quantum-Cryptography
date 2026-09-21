#!/usr/bin/env python3
"""Milestone 0 gate: verify every framework API this project builds on.

Exits 0 only if every required check passed. Run it before building anything, and re-run it after
any dependency change.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grover_emulator.utils.api_probe import format_report, probe_all  # noqa: E402


def main() -> int:
    results = probe_all()
    print(format_report(results))
    return 1 if any(not r.ok and r.required for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
