"""The diffuser, against two constructions that share no code with it.

``circuits/diffuser.py`` says of itself that "a test compares it against Qiskit's own
``GroverOperator``", and until this file that test did not exist. The diffuser was exercised only
through success curves, which is a strong check of the whole circuit and a weak one of this part: a
curve cannot say *which* factor of a wrong product is the wrong one.

Two references, deliberately unrelated:

* the analytic operator ``2|s><s| - I``, built here from NumPy outer products and nothing else;
* Qiskit's ``grover_operator`` over an **identity oracle**, which leaves exactly the library's own
  diffuser — written by other people, from the same textbook.

Both comparisons are **up to a global phase**, and that is not slack. ``H^n X^n (MCZ) X^n H^n``
evaluates to ``I - 2|s><s|``, the negative of the textbook form; the sign is a global phase, it is
physically meaningless, and ``assert_operators_agree_up_to_phase`` exists precisely so that this
comparison can be made without calling a correct circuit wrong. The exact sign is pinned separately,
so that the convention is recorded rather than merely tolerated.
"""

from __future__ import annotations

import numpy as np
import pytest

from grover_emulator.circuits.compilers import to_qiskit
from grover_emulator.circuits.diffuser import build_diffuser
from grover_emulator.circuits.ir import GateName
from grover_emulator.utils.validation import assert_operators_agree_up_to_phase, assert_unitary

WIDTHS = [2, 3, 4, 5, 6]


def diffuser_matrix(n: int) -> np.ndarray:
    from qiskit.quantum_info import Operator

    return np.asarray(Operator(to_qiskit(build_diffuser(n))).data)


def inversion_about_the_mean(n: int) -> np.ndarray:
    """``2|s><s| - I`` with ``|s>`` the uniform superposition — no circuit, no framework."""
    dim = 1 << n
    s = np.full(dim, 1.0 / np.sqrt(dim))
    return 2.0 * np.outer(s, s) - np.eye(dim)


# ---------------------------------------------------------------------------------------------
# the operator
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", WIDTHS)
def test_the_diffuser_is_unitary(n):
    assert_unitary(diffuser_matrix(n), 1e-12)


@pytest.mark.parametrize("n", [1] + WIDTHS)
def test_the_diffuser_is_inversion_about_the_mean_up_to_a_global_phase(n):
    """``n = 1`` is included: the module special-cases it (a one-qubit mcz is the Pauli Z), and a
    special case is where a construction that is right in general goes wrong."""
    assert_operators_agree_up_to_phase(
        diffuser_matrix(n), inversion_about_the_mean(n), tol=1e-12, label=f"diffuser[{n}]"
    )


@pytest.mark.parametrize("n", WIDTHS)
def test_the_global_phase_is_minus_one_exactly(n):
    """The circuit is ``I - 2|s><s|``, entry for entry. Recorded so that a change of convention —
    which would be harmless to every success curve — still shows up as a change."""
    np.testing.assert_allclose(diffuser_matrix(n), -inversion_about_the_mean(n), atol=1e-12)


@pytest.mark.parametrize("n", WIDTHS)
def test_the_diffuser_agrees_with_qiskits_own_grover_operator(n):
    """``grover_operator(identity oracle)`` is Qiskit's diffuser and nothing else.

    The identity oracle is an empty circuit, so the product the library returns is its zero
    reflection conjugated by its state preparation — the same operator from an independent hand.
    """
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import grover_operator
    from qiskit.quantum_info import Operator

    reference = np.asarray(Operator(grover_operator(QuantumCircuit(n))).data)
    assert_operators_agree_up_to_phase(
        diffuser_matrix(n), reference, tol=1e-9, label=f"diffuser[{n}] vs qiskit"
    )


@pytest.mark.parametrize("n", WIDTHS)
def test_inverting_about_the_all_ones_state_would_be_caught(n):
    """The module's own warning, made into a check: without the X-conjugation the reflection is
    about ``H^n|1...1>`` instead of the mean. That operator is unitary and looks like a diffuser, so
    the comparison above has to be able to tell the two apart — and this shows it can."""
    from qiskit.quantum_info import Operator

    without_x = build_diffuser(n)
    without_x.gates = [g for g in without_x.gates if g.name is not GateName.X]
    wrong = np.asarray(Operator(to_qiskit(without_x)).data)

    assert_unitary(wrong, 1e-12)
    with pytest.raises(AssertionError, match="global phase"):
        assert_operators_agree_up_to_phase(wrong, inversion_about_the_mean(n), tol=1e-9)


@pytest.mark.parametrize("n", WIDTHS)
def test_the_uniform_superposition_is_the_reflection_axis(n):
    """``|s>`` is an eigenvector and everything orthogonal to it is too, with the opposite sign."""
    dim = 1 << n
    matrix = diffuser_matrix(n)
    s = np.full(dim, 1.0 / np.sqrt(dim))
    orthogonal = np.zeros(dim)
    orthogonal[0], orthogonal[1] = 1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)

    np.testing.assert_allclose(matrix @ s, -s, atol=1e-12)
    np.testing.assert_allclose(matrix @ orthogonal, orthogonal, atol=1e-12)


# ---------------------------------------------------------------------------------------------
# the gate list
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1] + WIDTHS)
def test_the_diffuser_is_built_from_primitives_only(n):
    """H, X and one multi-controlled Z — nothing imported, nothing opaque, so the gate count is a
    count of what runs. The sequence is asserted, not just the set: ``H^n X^n MCZ X^n H^n``."""
    gl = build_diffuser(n)

    assert {g.name for g in gl.gates} == {GateName.H, GateName.X, GateName.MCZ}
    assert gl.counts() == {"h": 2 * n, "x": 2 * n, "mcz": 1, "total": 4 * n + 1}
    assert [g.name for g in gl.gates] == (
        [GateName.H] * n + [GateName.X] * n + [GateName.MCZ] + [GateName.X] * n + [GateName.H] * n
    )

    mcz = gl.gates[2 * n]
    assert sorted(mcz.qubits) == list(range(n)), "the phase must be conditioned on every qubit"


@pytest.mark.parametrize("n", [1] + WIDTHS)
def test_the_diffuser_declares_exactly_its_own_width(n):
    """No hidden ancilla: every declared qubit is touched, and there are no others."""
    gl = build_diffuser(n)
    assert gl.num_qubits == n
    assert gl.active_qubits() == set(range(n))
    assert gl.ancilla_peak() == 0
    assert gl.label == f"diffuser[{n}]"


def test_the_diffuser_is_not_classically_simulable():
    """It contains H, so the bitmask simulator must refuse it rather than track one trajectory."""
    assert build_diffuser(3).is_classically_simulable() is False


@pytest.mark.parametrize("n", WIDTHS)
def test_the_diffuser_is_its_own_inverse(n):
    """A reflection squares to the identity. The IR inverse reverses the order within each layer, so
    the gate lists differ as sequences; what must hold is that the gates are the same multiset and
    the operator is the same operator."""
    from qiskit.quantum_info import Operator

    gl = build_diffuser(n)
    inverse = gl.inverse()
    assert sorted((g.name.value, g.qubits) for g in inverse.gates) == sorted(
        (g.name.value, g.qubits) for g in gl.gates
    )

    matrix = diffuser_matrix(n)
    np.testing.assert_allclose(np.asarray(Operator(to_qiskit(inverse)).data), matrix, atol=1e-12)
    np.testing.assert_allclose(matrix @ matrix, np.eye(1 << n), atol=1e-12)


@pytest.mark.parametrize("n", [0, -1, -7])
def test_a_diffuser_over_no_qubits_is_refused(n):
    with pytest.raises(ValueError, match="at least 1 qubit"):
        build_diffuser(n)
