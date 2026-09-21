"""Milestone 0 as a test: every framework API this project is built on, verified by execution.

The probe found five things that were wrong in the design pass's assumptions, three of which would
have failed silently. Running it as part of the suite means a dependency bump cannot quietly
reintroduce any of them.
"""

from __future__ import annotations

import pytest

from grover_emulator.utils.api_probe import probe_all


@pytest.fixture(scope="module")
def results():
    return probe_all()


def test_no_required_check_failed(results):
    failed = [r for r in results if r.required and not r.ok]
    assert not failed, "\n".join(r.line() for r in failed)


def test_the_five_measured_findings_still_hold(results):
    """Each of these was a documented behaviour that measurement contradicted. They are asserted
    individually so that a future framework version flipping one of them is a named failure rather
    than a line in a report nobody reads."""
    by_name = {r.name: r for r in results}

    # MCZGate does not exist; MCPhaseGate is the substitution. For an "expected gone" check, ok
    # means the name really is absent — so a failure here reads as "MCZGate came back", which is
    # the thing worth knowing.
    assert by_name["qiskit.circuit.library.MCZGate (expected gone)"].ok
    assert by_name["MCPhaseGate(pi, k-1) as MCZ"].ok

    # PermutationGate permutes qubit positions, not basis states -- unusable for the IR's `perm`.
    perm = by_name["PermutationGate is a qubit relabelling, not a basis permutation"]
    assert perm.ok and "2 of 24" in perm.detail

    # UnitaryGate is the lowering that does work for an arbitrary nonlinear permutation.
    assert by_name["UnitaryGate executes an arbitrary nonlinear permutation"].ok

    # QuadraticFormGate matched the full-matrix reading on every input.
    quad = by_name["QuadraticFormGate convention"]
    assert quad.ok and "full matrix" in quad.detail

    # The adder is not ancilla-free.
    assert "ancilla" in by_name["CDKMRippleCarryAdder(8, kind='full')"].detail


def test_both_engines_execute_a_uniform_superposition(results):
    by_name = {r.name: r for r in results}
    assert by_name["Aer statevector execution"].ok
    assert by_name["qsim (via cirq) statevector execution"].ok
