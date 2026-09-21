"""The IR and its compilers: the properties every other module's accounting rests on.

Three of these are acceptance conditions rather than conveniences:

* the round-trip through both frameworks is exact — without it, the gate list that was counted is
  not the circuit that ran, and every gate count in every report is fiction;
* ``inverse()`` is an involution and is *exact*, which is what makes the oracle sandwich a real
  uncompute rather than an approximate one;
* gate semantics match the analytic matrices, verified against an independent construction rather
  than against this module's own reading of itself.
"""

from __future__ import annotations

import numpy as np
import pytest

from grover_emulator.circuits.compilers import (
    ToQiskitError,
    assert_round_trip,
    from_cirq,
    from_qiskit,
    import_definition,
    relabel,
    to_cirq,
    to_qiskit,
)
from grover_emulator.circuits.ir import Gate, GateList, GateName, phase_exponent


def sample_gate_list(n: int = 10) -> GateList:
    """Every gate in the set, at every arity that fits in ``n`` — so ``n`` must be at least 10."""
    if n < 10:
        raise ValueError("sample_gate_list needs n >= 10 to reach every gate and arity")
    gl = GateList(n, label="sample")
    gl.append(GateName.X, 0)
    gl.append(GateName.H, 1)
    gl.append(GateName.CX, 0, 1)
    gl.append(GateName.CCX, 0, 1, 2)
    gl.append(GateName.MCZ, 0)  # one-qubit mcz is the Pauli Z
    gl.append(GateName.S, 5)
    gl.append(GateName.SDG, 5)
    gl.append(GateName.T, 6)
    gl.append(GateName.TDG, 6)
    gl.append(GateName.PERM, 7, 8, 9, params=([3, 1, 0, 2, 7, 4, 6, 5],))
    for k in range(1, n):
        gl.append(GateName.MCZ, *range(k))
    for k in range(4, n):
        gl.append(GateName.MCX, *range(k))
    return gl


# ---------------------------------------------------------------------------------------------
# round-trip — acceptance condition 8
# ---------------------------------------------------------------------------------------------


def test_round_trip_both_frameworks_is_exact():
    gl = sample_gate_list()
    assert gl.gates == from_qiskit(to_qiskit(gl)).gates
    assert gl.gates == from_cirq(to_cirq(gl)).gates


def test_assert_round_trip_helper_passes():
    assert_round_trip(sample_gate_list())


def test_round_trip_preserves_order_and_multiplicity():
    """A compiler that dropped or reordered a gate would still round-trip a *set*; this checks the
    sequence, which is what the gate count is a count of."""
    gl = GateList(4)
    for _ in range(3):
        gl.append(GateName.X, 0)
        gl.append(GateName.T, 1)
        gl.append(GateName.X, 0)
    back = from_qiskit(to_qiskit(gl))
    assert [g.name for g in back.gates] == [g.name for g in gl.gates]
    assert len(back.gates) == len(gl.gates)


def test_from_qiskit_refuses_a_gate_outside_the_ir_set():
    """Silently mapping an unknown instruction is how the accounting stops describing the circuit."""
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2)
    qc.rx(0.3, 0)  # a rotation: deliberately not in the IR
    with pytest.raises(ToQiskitError):
        from_qiskit(qc)


# ---------------------------------------------------------------------------------------------
# gate semantics, against analytic matrices
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("k", [1, 2, 3, 4, 5])
def test_mcz_is_negation_on_the_all_ones_state(k):
    from qiskit.quantum_info import Operator

    gl = GateList(k)
    gl.append(GateName.MCZ, *range(k))
    matrix = Operator(to_qiskit(gl)).data
    want = np.diag([-1.0 if bin(i).count("1") == k else 1.0 for i in range(1 << k)])
    assert np.allclose(matrix, want)


@pytest.mark.parametrize("k", [4, 5, 6])
def test_mcx_flips_only_the_target(k):
    """The IR's contract is controls first, target last. Checking the whole matrix rather than one
    example, because a permutation that is right on one basis state can be wrong on another."""
    from qiskit.quantum_info import Operator

    gl = GateList(k)
    gl.append(GateName.MCX, *range(k))
    matrix = Operator(to_qiskit(gl)).data
    controls_mask = (1 << (k - 1)) - 1
    want = np.zeros((1 << k, 1 << k))
    for i in range(1 << k):
        target = i ^ (1 << (k - 1)) if (i & controls_mask) == controls_mask else i
        want[target, i] = 1
    assert np.allclose(matrix, want)


def test_perm_is_a_basis_permutation_and_its_inverse_undoes_it():
    from qiskit.quantum_info import Operator

    table = [3, 1, 0, 2, 7, 4, 6, 5]
    gl = GateList(3)
    gl.append(GateName.PERM, 0, 1, 2, params=(table,))
    matrix = Operator(to_qiskit(gl)).data
    want = np.zeros((8, 8))
    for src, dst in enumerate(table):
        want[dst, src] = 1
    assert np.allclose(matrix, want)

    inverse = GateList(3)
    inverse.append(GateName.PERM, 0, 1, 2, params=(tuple(np.argsort(table).tolist()),))
    assert np.allclose(Operator(to_qiskit(inverse)).data @ matrix, np.eye(8))


def test_permutation_gate_table_is_canonicalised_to_a_tuple():
    """A list and a tuple with the same contents must compare equal, or a compiler-produced gate
    never equals the one it was built from and the round-trip fails for a reason that is not a bug.

    A ``b``-qubit table has ``2**b`` entries, so a two-qubit table is four long, not two — the
    obvious-looking ``[1, 0]`` is a *one*-qubit table and is rejected.
    """
    a = Gate(GateName.PERM, (0, 1), params=([1, 0, 3, 2],))
    b = Gate(GateName.PERM, (0, 1), params=((1, 0, 3, 2),))
    assert a == b
    assert isinstance(a.params[0], tuple)


def test_perm_rejects_a_non_permutation():
    with pytest.raises(ValueError):
        Gate(GateName.PERM, (0, 1), params=((0, 0, 1, 1),))


def test_perm_rejects_a_table_of_the_wrong_length():
    with pytest.raises(ValueError):
        Gate(GateName.PERM, (0, 1), params=((1, 0),))


# ---------------------------------------------------------------------------------------------
# inverse
# ---------------------------------------------------------------------------------------------


def test_inverse_is_exact_and_an_involution():
    gl = sample_gate_list()
    assert gl.inverse().inverse().gates == gl.gates


def test_inverse_matches_the_matrix_inverse():
    from qiskit.quantum_info import Operator

    gl = sample_gate_list(6 + 4)  # enough width for every gate and arity
    forward = Operator(to_qiskit(gl)).data
    back = Operator(to_qiskit(gl.inverse())).data
    assert np.allclose(back @ forward, np.eye(forward.shape[0]))


def test_inverse_of_a_read_only_gate_list_does_not_mutate_the_original():
    gl = GateList(3)
    gl.append(GateName.S, 0)
    before = list(gl.gates)
    gl.inverse()
    assert gl.gates == before


# ---------------------------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------------------------


def test_depth_is_the_critical_path_not_the_gate_count():
    """Two independent gates on separate qubits must not add depth, and two on the same qubit must."""
    wide = GateList(4)
    wide.append(GateName.X, 0)
    wide.append(GateName.X, 1)
    wide.append(GateName.X, 2)
    assert wide.depth() == 1

    chain = GateList(4)
    chain.append(GateName.X, 0)
    chain.append(GateName.X, 0)
    chain.append(GateName.X, 0)
    assert chain.depth() == 3


def test_toffoli_accounting_separates_logical_from_decomposed():
    """The two counts differ by an order of magnitude, so a report that quotes one without saying
    which is not reporting a measurement."""
    gl = GateList(12)
    gl.append(GateName.CCX, 0, 1, 2)
    gl.append(GateName.MCX, *range(11))
    assert gl.toffoli_count() == 2  # logical: one ccx, one mcx
    assert gl.toffoli_equivalent() == 1 + 9  # ancilla-assisted: c - 1
    assert gl.toffoli_equivalent(ancilla_free=True) == 1 + (4 * 100 - 80 + 4)


def test_t_count_counts_both_t_and_tdg():
    gl = GateList(2)
    gl.append(GateName.T, 0)
    gl.append(GateName.TDG, 1)
    assert gl.t_count() == 2


def test_classical_simulability_flag_is_honest():
    perm_only = GateList(2)
    perm_only.append(GateName.CX, 0, 1)
    perm_only.append(GateName.MCZ, 0, 1)
    perm_only.append(GateName.T, 0)
    assert perm_only.is_classically_simulable()

    with_h = GateList(2)
    with_h.append(GateName.H, 0)
    assert not with_h.is_classically_simulable()


def test_phase_exponent_refuses_a_non_diagonal_gate():
    """A single-trajectory simulation through H would be silently wrong, so it stops instead."""
    with pytest.raises(ValueError):
        phase_exponent(Gate(GateName.H, (0,)), (True,))


# ---------------------------------------------------------------------------------------------
# structural helpers
# ---------------------------------------------------------------------------------------------


def test_ancilla_peak_counts_carried_but_unused_qubits():
    gl = GateList(8)
    gl.append(GateName.X, 0)
    assert gl.ancilla_peak() == 7


def test_append_rejects_a_qubit_beyond_the_declared_width():
    gl = GateList(2)
    with pytest.raises(ValueError):
        gl.append(GateName.X, 5)


def test_relabel_moves_a_block_and_can_invert_it():
    block = GateList(2, label="block")
    block.append(GateName.CX, 0, 1)
    moved = relabel(block, {0: 3, 1: 7}, 8)
    assert [g.qubits for g in moved.gates] == [(3, 7)]
    inverted = relabel(block, {0: 3, 1: 7}, 8, invert=True)
    assert [g.qubits for g in inverted.gates] == [(3, 7)]  # CX is self-inverse


def test_import_definition_refuses_a_gate_with_no_definition():
    """An opaque block cannot be counted, and being unable to count what ran is the failure this
    project exists to avoid.

    The stub is used rather than a real framework gate because several library gates do carry a
    definition that decomposes into something useful, and the property under test is what happens
    when one does not — not which library gate happens to be definition-less in this version.
    """

    class Opaque:
        num_qubits = 4
        definition = None

    with pytest.raises(ToQiskitError):
        import_definition(Opaque())


def test_import_definition_refuses_a_width_mismatch():
    """A gate whose definition uses a different width from its declaration is a hidden-ancilla bug,
    and it must be a build failure rather than a run that quietly allocates more than was budgeted."""

    class Lying:
        num_qubits = 8
        definition = None

    lying = Lying()
    from qiskit import QuantumCircuit

    lying.definition = QuantumCircuit(2)  # declares 8, defines 2
    with pytest.raises(ToQiskitError):
        import_definition(lying)


# ---------------------------------------------------------------------------------------------
# cross-framework unitaries -- the check the round-trip cannot make
# ---------------------------------------------------------------------------------------------


def _align_cirq_to_qiskit(u, n: int):
    """Re-index a cirq unitary into qiskit's basis ordering.

    qiskit reads qubit 0 as the least significant bit; cirq reads the *first* qubit of an operation
    as the **most** significant. The two frameworks therefore write the same operator as different
    matrices, and comparing them raw fails on every multi-qubit gate for a reason that has nothing
    to do with either lowering. The bit-reversal permutation is the conversion, and it is its own
    inverse.
    """
    index = lambda i: int(format(i, f"0{n}b")[::-1], 2)  # noqa: E731 - local, one line
    out = np.zeros_like(u)
    for i in range(1 << n):
        for j in range(1 << n):
            out[index(i), index(j)] = u[i, j]
    return out


def _unitaries_agree(gl: GateList) -> bool:
    import cirq
    from qiskit.quantum_info import Operator

    n = gl.num_qubits
    want = Operator(to_qiskit(gl)).data
    circuit = to_cirq(gl)
    # ``qubit_order`` is explicit: a circuit only *contains* the qubits its operations touch, so an
    # untouched qubit would silently shrink the matrix instead of contributing an identity factor.
    got = circuit.unitary(qubit_order=cirq.LineQubit.range(n))
    return np.allclose(want, _align_cirq_to_qiskit(got, n))


@pytest.mark.parametrize(
    "table",
    [
        [1, 0, 3, 2],  # 2 qubits
        [3, 1, 0, 2, 7, 4, 6, 5],  # 3 qubits
        [2, 0, 1, 3, 4, 5, 7, 6],  # 3 qubits, a different shape
        [15, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],  # 4 qubits, a rotation
    ],
)
def test_perm_lowering_agrees_across_frameworks(table):
    """The round-trip is convention-independent: it compares gate *names and qubits*, both of which
    stay correct while the operation they denote differs. A ``to_cirq`` that handed cirq the
    permutation matrix in the wrong qubit order passed every round-trip test in this file and still
    executed a different permutation. This compares the unitaries, which is the only thing that
    catches it."""
    n = len(table).bit_length() - 1
    gl = GateList(n)
    gl.append(GateName.PERM, *range(n), params=(table,))
    assert _unitaries_agree(gl)


@pytest.mark.parametrize("qubits", [(0, 1, 3), (1, 3, 4), (0, 2)])
def test_perm_lowering_agrees_on_non_contiguous_qubits(qubits):
    """A permutation on a subset of the register, which is the case a full-width test cannot see:
    the untouched qubits must come out as identity factors in the right positions."""
    n = max(qubits) + 1
    k = len(qubits)
    table = list(range(1 << k))[::-1]  # a reversal, so a mis-ordering cannot coincide with identity
    gl = GateList(n)
    gl.append(GateName.PERM, *qubits, params=(table,))
    assert _unitaries_agree(gl)


def test_every_gate_class_agrees_across_frameworks():
    """The same comparison over the whole gate set, so a future lowering that mis-orders a
    control/target pair is caught by the same mechanism rather than only PERM being watched."""
    gl = GateList(6)
    gl.append(GateName.X, 0)
    gl.append(GateName.H, 1)
    gl.append(GateName.CX, 0, 2)
    gl.append(GateName.CCX, 0, 1, 2)
    gl.append(GateName.MCX, *range(4))
    gl.append(GateName.MCZ, 0, 1, 2)
    gl.append(GateName.S, 3)
    gl.append(GateName.SDG, 4)
    gl.append(GateName.T, 5)
    gl.append(GateName.TDG, 5)
    gl.append(GateName.PERM, 3, 4, 5, params=([7, 2, 5, 0, 6, 1, 4, 3],))
    assert _unitaries_agree(gl)
