"""Path setup shared by every test module.

The package lives under ``src/`` and is installed into the sage environment by a path entry rather
than a build, so putting ``src`` on ``sys.path`` here means a test run behaves the same started from
any directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# The modulus pair the recorded production parameter set uses. Held fixed across the scaling rule
# deliberately: preserving the modulus ratio is the entire purpose of scaling, so a scaled instance
# that changed q or p would not be a scaled instance of anything.
PRODUCTION_MODULUS = 1 << 16
PRODUCTION_ROUNDING = 1 << 8

# The recorded production shape, as a ratio rather than as two numbers -- see ScalingRule. The
# dimensions themselves appear only in the guard test that asserts they are *not* used.
PRODUCTION_NU_OVER_M = (256, 608)


@pytest.fixture(scope="session")
def production_modulus() -> tuple[int, int]:
    return PRODUCTION_MODULUS, PRODUCTION_ROUNDING
