"""Shared test fixtures and the path setup every test module relies on.

The package lives under ``src/`` and is not installed into the virtual environment, so the tests put
it on the path here rather than each module repeating the dance. Doing it in one place also means a
test run started from any directory behaves the same.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# The default sweep widths, as search-register widths. Kept here so that a test which needs "a small
# instance" and a test which needs "the sweep's smallest instance" cannot drift apart.
SMALL_N = 8
FAITHFUL_N = 12  # the smallest structurally faithful QLWR instance; see notes/01-arithmetic.md


@pytest.fixture(scope="session")
def qlwr_instance():
    """The worked QLWR instance, generated once for the whole session.

    Generation enumerates the marked set, so building it per-test would be quietly expensive.
    """
    from grover_emulator.problem.qlwr_instance import generate_scaled_instance

    return generate_scaled_instance(n_search=FAITHFUL_N, nu=2, seed=20260913)


@pytest.fixture(scope="session")
def qlwr_spec(qlwr_instance):
    from grover_emulator.problem.oracle_spec import QLWROracleSpec

    return QLWROracleSpec(qlwr_instance)


@pytest.fixture(scope="session")
def random_spec():
    """A negative control: no structure to find, so a probe that fires on it is broken.

    Eight marked values of the ``2**SMALL_N`` at this register, drawn at a size and a seed chosen so
    that the set carries no structure at all. The size is not a matter of taste. Two values is not a
    weak control but a broken one: every two-element set ``{a, b}`` is closed under
    ``x -> x ^ (a ^ b)``, so it has a genuine XOR-period, the structural probes detect it, and their
    firing is correct behaviour rather than a false positive. That no non-zero ``s`` closes this set,
    and that both probes stay silent on it, is asserted by
    ``tests/test_analysis.py::test_the_negative_control_is_genuinely_unstructured``.
    """
    from grover_emulator.problem.oracle_spec import RandomControlOracleSpec

    return RandomControlOracleSpec(n_qubits=SMALL_N, n_marked=8, seed=11)


@pytest.fixture(scope="session")
def hidden_period_spec():
    """A positive control: structure is planted, so a probe that misses it is broken."""
    from grover_emulator.problem.oracle_spec import HiddenPeriodOracleSpec

    return HiddenPeriodOracleSpec(n_qubits=SMALL_N, period=0b100, seed=11)


@pytest.fixture(scope="session")
def aer_backend():
    """The primary engine, constructed once."""
    from grover_emulator.backends.qiskit_aer_backend import QiskitAerBackend

    return QiskitAerBackend()
