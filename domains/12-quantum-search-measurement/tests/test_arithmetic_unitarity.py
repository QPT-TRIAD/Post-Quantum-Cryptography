"""Matrix-level verification of the arithmetic blocks, independent of the project's own simulator.

``tests/test_reversible_arithmetic.py`` checks every block exhaustively, but it does so through the
``verify_*`` helpers that live beside the blocks and through a bitmask simulator the project wrote
itself. That is exact, and it is not independent: a misreading of a gate shared by the builder and
the simulator would pass. This file goes the other way round. Each block is compiled with
``to_qiskit``, Qiskit's own ``Operator`` turns it into a dense matrix, and the matrix is required to

* be unitary (:func:`grover_emulator.utils.validation.assert_unitary`),
* be a **permutation** matrix — entries exactly 0 or 1, one per column — and
* send every basis state where Python's own integer arithmetic, written out here, says it goes.

The index convention is Qiskit's and the IR's, which coincide: bit ``q`` of a basis index is qubit
``q``, and ``Operator.data[row, col]`` is the amplitude of ``|row>`` after the circuit acts on
``|col>``. So ``image[col]`` below is read straight off the matrix, with no re-indexing to get wrong.

Widths stay small because the matrix is ``4**n`` entries: the comparator at ``n = 4`` is nine qubits.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grover_emulator.circuits.compilers import to_qiskit
from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.circuits.reversible_arithmetic import (
    add_constant,
    equal_to_constant,
    less_than_constant,
)
from grover_emulator.utils.validation import assert_unitary

TOL = 1e-12


def operator_of(gl: GateList) -> np.ndarray:
    """The dense matrix of a gate list, by Qiskit's construction rather than the project's."""
    from qiskit.quantum_info import Operator

    return np.asarray(Operator(to_qiskit(gl)).data)


def permutation_image(matrix: np.ndarray) -> list[int]:
    """Assert ``matrix`` is a 0/1 permutation matrix and return ``image[col] = row``.

    Unitarity alone would admit phases and superpositions; a reversible arithmetic block has
    neither, so the entries are required to be exactly 0 or 1 to tolerance, one per column and one
    per row.
    """
    assert_unitary(matrix, TOL)
    assert np.allclose(matrix.imag, 0.0, atol=TOL), "an arithmetic block carries no phase"
    rounded = np.rint(matrix.real)
    assert np.allclose(matrix.real, rounded, atol=TOL), "entries must be exactly 0 or 1"
    assert set(np.unique(rounded).tolist()) <= {0.0, 1.0}
    assert np.all(rounded.sum(axis=0) == 1), "a column with other than one entry"
    assert np.all(rounded.sum(axis=1) == 1), "a row with other than one entry"
    return [int(row) for row in np.argmax(rounded, axis=0)]


def bits_of(state: int, qubits: list[int]) -> int:
    """The integer a little-endian register holds in a basis state: ``qubits[k]`` carries bit ``k``."""
    return sum(((state >> q) & 1) << k for k, q in enumerate(qubits))


# ---------------------------------------------------------------------------------------------
# add_constant
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_add_constant_is_the_permutation_x_to_x_plus_c(n):
    """Every constant at every width: the matrix is the cyclic shift by ``c`` modulo ``2**n``."""
    for constant in range(1 << n):
        gl = GateList(n)
        add_constant(gl, list(range(n)), constant)
        image = permutation_image(operator_of(gl))
        assert image == [(x + constant) % (1 << n) for x in range(1 << n)], f"n={n} c={constant}"


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_controlled_add_constant_adds_only_when_the_control_is_set(n):
    """The control sits above the register. With it clear the block is the identity; with it set the
    register advances by ``c`` — and in both halves the control itself comes back unchanged."""
    control = n
    for constant in range(1 << n):
        gl = GateList(n + 1)
        add_constant(gl, list(range(n)), constant, control=control)
        image = permutation_image(operator_of(gl))
        for state in range(1 << (n + 1)):
            x, c_bit = state & ((1 << n) - 1), state >> n
            want = ((x + constant) % (1 << n) if c_bit else x) | (c_bit << n)
            assert image[state] == want, f"n={n} c={constant} state={state:#b}"


def test_controlled_add_on_a_scattered_register_leaves_bystanders_alone():
    """The register need not be contiguous or start at qubit 0, and the QLWR lowering relies on
    that: its accumulator sits above the search register and its controls are search bits. Qubit 2
    here is a bystander that no gate may touch."""
    reg, control, bystander = [4, 1, 3], 0, 2
    for constant in range(8):
        gl = GateList(5)
        add_constant(gl, reg, constant, control=control)
        image = permutation_image(operator_of(gl))
        for state in range(1 << 5):
            out = image[state]
            enabled = (state >> control) & 1
            value = bits_of(state, reg)
            assert bits_of(out, reg) == ((value + constant) % 8 if enabled else value)
            assert (out >> control) & 1 == enabled
            assert (out >> bystander) & 1 == (state >> bystander) & 1


@settings(deadline=None, max_examples=60)
@given(data=st.data())
def test_add_constant_matches_python_addition_for_any_drawn_case(data):
    """The property form of the above: any width, any constant, any value, either control state."""
    n = data.draw(st.integers(min_value=1, max_value=5), label="n")
    constant = data.draw(st.integers(min_value=0, max_value=(1 << n) - 1), label="constant")
    value = data.draw(st.integers(min_value=0, max_value=(1 << n) - 1), label="value")
    control_bit = data.draw(st.integers(min_value=0, max_value=1), label="control")

    gl = GateList(n + 1)
    add_constant(gl, list(range(n)), constant, control=n)
    column = operator_of(gl)[:, value | (control_bit << n)]

    want = ((value + constant) % (1 << n) if control_bit else value) | (control_bit << n)
    expected = np.zeros(1 << (n + 1))
    expected[want] = 1.0
    assert np.allclose(column, expected, atol=TOL)


# ---------------------------------------------------------------------------------------------
# less_than_constant
# ---------------------------------------------------------------------------------------------


def comparator(n: int, constant: int) -> tuple[GateList, int]:
    """Register on ``0..n-1``, work on ``n..2n-1``, flag on ``2n``."""
    gl = GateList(2 * n + 1)
    less_than_constant(gl, list(range(n)), constant, 2 * n, list(range(n, 2 * n)))
    return gl, 2 * n


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_less_than_constant_xors_the_comparison_into_the_flag(n):
    """Work clean on the way in: the register survives, the work qubits come back to ``|0>``, and
    the flag is **XORed** — checked with the flag starting at 1 as well as 0, because a block that
    *set* the flag rather than XORing it would pass every flag-starts-clear test and then break the
    interval test ``[acc < lo] XOR [acc < hi + 1]`` that the QLWR lowering is built from.

    The constants run past ``2**n`` to reach the short-circuit branch, where the comparison is
    decided by the register's width alone.
    """
    for constant in range((1 << n) + 2):
        gl, flag = comparator(n, constant)
        image = permutation_image(operator_of(gl))
        for x in range(1 << n):
            for flag_in in (0, 1):
                out = image[x | (flag_in << flag)]
                want_flag = flag_in ^ int(x < constant)
                assert out == x | (want_flag << flag), (
                    f"n={n} c={constant} x={x} flag_in={flag_in}: got {out:#b}"
                )


@pytest.mark.parametrize("n", [2, 3])
def test_less_than_constant_never_moves_the_register(n):
    """Over the *whole* space, dirty work qubits included: the register is only ever read. The
    X-conjugations around each Toffoli must cancel on every input, not just the clean ones."""
    for constant in range(1 << n):
        gl, _ = comparator(n, constant)
        image = permutation_image(operator_of(gl))
        mask = (1 << n) - 1
        assert all(image[state] & mask == state & mask for state in range(1 << (2 * n + 1)))


# ---------------------------------------------------------------------------------------------
# equal_to_constant
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_equal_to_constant_xors_the_equality_into_the_flag(n):
    """No ancillas, so this is the whole space: every register value with the flag at 0 and at 1."""
    flag = n
    for value in range(1 << n):
        gl = GateList(n + 1)
        equal_to_constant(gl, list(range(n)), value, flag)
        image = permutation_image(operator_of(gl))
        for state in range(1 << (n + 1)):
            x, flag_in = state & ((1 << n) - 1), state >> n
            assert image[state] == x | ((flag_in ^ int(x == value)) << flag), (
                f"n={n} v={value} state={state:#b}"
            )


def test_equal_to_constant_is_its_own_inverse():
    """An XOR into a flag applied twice is the identity; the matrix squared must be too."""
    gl = GateList(4)
    equal_to_constant(gl, [0, 1, 2], 0b101, 3)
    matrix = operator_of(gl)
    assert np.allclose(matrix @ matrix, np.eye(16), atol=TOL)


# ---------------------------------------------------------------------------------------------
# the composition the QLWR lowering is made of
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("modulus,addend", [(5, 3), (7, 6), (6, 1), (7, 0)])
def test_add_then_conditional_subtract_is_addition_modulo_q(modulus, addend):
    """The project has no ``mod_reduce`` block: the reduction is an add, a comparison against ``q``,
    and a controlled add of ``2**w - q``. This is that sequence in isolation, at a width where the
    matrix fits, checked against ``(v + a) % q`` for every accumulator value below ``q``.

    The comparison flag is left dirty, exactly as the lowering leaves it — it reads ``[v + a >= q]``
    — and the work qubits must be clean.
    """
    w1 = 4  # accumulator bits: holds a value below q and one addition above it
    acc, work, red = list(range(w1)), list(range(w1, 2 * w1)), 2 * w1
    gl = GateList(2 * w1 + 1)
    add_constant(gl, acc, addend)
    less_than_constant(gl, acc, modulus, red, work)
    gl.append(GateName.X, red)
    add_constant(gl, acc, (1 << w1) - modulus, control=red)

    image = permutation_image(operator_of(gl))
    for v in range(modulus):
        out = image[v]
        assert bits_of(out, acc) == (v + addend) % modulus, f"q={modulus} a={addend} v={v}"
        assert bits_of(out, work) == 0
        assert (out >> red) & 1 == int(v + addend >= modulus)
