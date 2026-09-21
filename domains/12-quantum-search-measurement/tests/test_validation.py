"""The validation helpers, tested as the instruments they are.

Everything the suite says about the fifty-qubit arithmetic oracle it says through
``utils/validation.py``: the bitmask simulator is the only thing that can reach that width, and the
``assert_*`` helpers are what turn its output into a verdict. An instrument that cannot fail is not
measuring anything, and until this file none of these helpers had been shown to fail — every call in
the suite was on the passing side. So each assertion here gets both halves: an input it must accept
and a deliberately broken one it must reject, with the message checked so that the rejection is for
the intended reason.

The simulator itself is cross-checked from outside. A forty-line trajectory simulator is written out
below in plain Python integers — no NumPy, no shared code — and three things are compared with it:
``simulate_states``, Qiskit's dense ``Operator`` of ``to_qiskit(gl)``, and cirq's unitary of
``to_cirq(gl)``. ``notes/02-integration.md`` records that the ``PERM`` lowering to cirq was once
wrong in exactly the way a convention error is wrong (bit-reversed, silently), so ``PERM`` gates are
drawn into those gate lists and both frameworks have to land where the reference does.
"""

from __future__ import annotations

import cmath
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grover_emulator.circuits.compilers import to_cirq, to_qiskit
from grover_emulator.circuits.ir import Gate, GateList, GateName
from grover_emulator.circuits.phase_oracle import build_phase_oracle
from grover_emulator.problem.oracle_spec import Lowering, OracleSpec, RandomControlOracleSpec
from grover_emulator.utils.validation import (
    SimulationError,
    assert_ancillas_return_clean,
    assert_backend_agreement,
    assert_operators_agree_up_to_phase,
    assert_oracle_is_diagonal,
    assert_predicate_matches_spec,
    assert_sandwich_is_identity,
    assert_unitary,
    phase_to_complex,
    simulate_predicate_flag,
    simulate_states,
)

HADAMARD = np.array([[1.0, 1.0], [1.0, -1.0]]) / math.sqrt(2.0)


def random_unitary(dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    q, _ = np.linalg.qr(rng.normal(size=(dim, dim)) + 1j * rng.normal(size=(dim, dim)))
    return q


def random_state(dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.normal(size=dim) + 1j * rng.normal(size=dim)
    return v / np.linalg.norm(v)


# ---------------------------------------------------------------------------------------------
# assert_unitary
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "matrix",
    [HADAMARD, np.eye(4)[[2, 0, 3, 1]], np.diag([1, 1j, -1, cmath.exp(0.3j)]), random_unitary(8, 1)],
    ids=["hadamard", "permutation", "diagonal-phases", "random"],
)
def test_assert_unitary_accepts_a_unitary(matrix):
    assert_unitary(matrix)
    assert_unitary(matrix, tol=1e-12)


@pytest.mark.parametrize(
    "matrix",
    [2.0 * np.eye(2), np.array([[1.0, 1.0], [0.0, 1.0]]), np.zeros((3, 3)), np.diag([1.0, 0.0])],
    ids=["scaled", "shear", "zero", "projector"],
)
def test_assert_unitary_rejects_a_matrix_that_is_not(matrix):
    with pytest.raises(AssertionError, match="not unitary; worst deviation"):
        assert_unitary(matrix)


@pytest.mark.parametrize("shape", [(2, 3), (4,), (2, 2, 2)])
def test_assert_unitary_rejects_anything_that_is_not_a_square_matrix(shape):
    with pytest.raises(AssertionError, match="not square"):
        assert_unitary(np.ones(shape))


def test_assert_unitary_tolerance_is_the_callers():
    """A deviation of ``1e-6`` is a failure at the default and a pass at ``1e-3`` — the tolerance is
    an argument and it is the one that is used."""
    nearly = HADAMARD + 1e-6 * np.array([[1.0, 0.0], [0.0, 0.0]])
    with pytest.raises(AssertionError):
        assert_unitary(nearly)
    assert_unitary(nearly, tol=1e-3)


# ---------------------------------------------------------------------------------------------
# assert_operators_agree_up_to_phase
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("phi", [0.0, math.pi, math.pi / 2, 0.7345, -2.1])
def test_operators_differing_by_a_global_phase_agree(phi):
    u = random_unitary(8, 2)
    assert_operators_agree_up_to_phase(u, cmath.exp(1j * phi) * u, tol=1e-12)


def test_operators_differing_by_a_relative_phase_do_not_agree():
    """``diag(1, i)`` against the identity: same magnitudes everywhere, and a different operator.
    A comparison of ``abs`` entries would pass this, which is why the helper is not one."""
    with pytest.raises(AssertionError, match="more than a global phase"):
        assert_operators_agree_up_to_phase(np.eye(2), np.diag([1.0, 1j]))
    assert np.allclose(np.abs(np.eye(2)), np.abs(np.diag([1.0, 1j])))


def test_operators_differing_in_one_sign_among_many_do_not_agree():
    """One flipped entry of sixty-four moves the normalised overlap by about three percent. The
    default tolerance has to see that, because it is the size of a one-marked-state mistake."""
    flipped = np.eye(64)
    flipped[5, 5] = -1.0
    with pytest.raises(AssertionError, match="more than a global phase"):
        assert_operators_agree_up_to_phase(np.eye(64), flipped)


def test_operator_comparison_rejects_mismatched_shapes_and_zero_operators():
    with pytest.raises(AssertionError, match="unit-a: shapes differ"):
        assert_operators_agree_up_to_phase(np.eye(2), np.eye(4), label="unit-a")
    with pytest.raises(AssertionError, match="unit-b: one operator is zero"):
        assert_operators_agree_up_to_phase(np.eye(2), np.zeros((2, 2)), label="unit-b")


# ---------------------------------------------------------------------------------------------
# assert_backend_agreement
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("phi", [0.0, math.pi, 1.234, -0.5])
def test_statevectors_differing_by_a_global_phase_agree(phi):
    """The documented contract: Aer and qsim may differ by a unit scalar and the physics is the
    same, so this must pass rather than fail for a reason that is not a bug."""
    psi = random_state(32, 3)
    assert_backend_agreement(psi, cmath.exp(1j * phi) * psi, tol=1e-12)


def test_statevectors_differing_by_a_relative_phase_do_not_agree():
    plus = np.array([1.0, 1.0]) / math.sqrt(2.0)
    minus = np.array([1.0, -1.0]) / math.sqrt(2.0)
    with pytest.raises(AssertionError, match="engines disagree"):
        assert_backend_agreement(plus, minus)
    with pytest.raises(AssertionError, match="engines disagree"):
        assert_backend_agreement(plus, np.array([1.0, 1j]) / math.sqrt(2.0))


def test_different_basis_states_do_not_agree():
    a, b = np.zeros(16), np.zeros(16)
    a[3], b[4] = 1.0, 1.0
    with pytest.raises(AssertionError, match=r"pair: engines disagree; state overlap 0\.0"):
        assert_backend_agreement(a, b, label="pair")


def test_a_small_infidelity_is_caught_at_the_default_tolerance_and_passed_at_a_loose_one():
    """The single-precision engine is why the tolerance is an argument; the default must still be
    tight enough to see a ``1e-6`` shortfall."""
    psi = random_state(16, 4)
    other = random_state(16, 5)
    other = other - np.vdot(psi, other) * psi
    other /= np.linalg.norm(other)
    epsilon = math.sqrt(2e-6)  # overlap = cos(epsilon) ~ 1 - 1e-6
    nearby = math.cos(epsilon) * psi + math.sin(epsilon) * other

    with pytest.raises(AssertionError, match="fidelity shortfall"):
        assert_backend_agreement(psi, nearby)
    assert_backend_agreement(psi, nearby, tol=1e-3)


def test_statevector_comparison_rejects_mismatched_shapes_and_zero_vectors():
    psi = random_state(8, 6)
    with pytest.raises(AssertionError, match="w: shapes differ"):
        assert_backend_agreement(psi, random_state(16, 6), label="w")
    with pytest.raises(AssertionError, match="z: one statevector is zero"):
        assert_backend_agreement(psi, np.zeros(8), label="z")
    with pytest.raises(AssertionError, match="one statevector is zero"):
        assert_backend_agreement(np.zeros(8), psi)


# ---------------------------------------------------------------------------------------------
# the oracle assertions, on oracles that are wrong on purpose
# ---------------------------------------------------------------------------------------------


class TamperedSpec(OracleSpec):
    """Declares one marked set and builds the circuit for another — the defect the equivalence
    test exists to catch, made to order."""

    name = "tampered"

    def __init__(self, n_qubits: int, declared: frozenset[int], built: frozenset[int]):
        self._n, self._declared, self._built = n_qubits, frozenset(declared), frozenset(built)

    def search_width(self) -> int:
        return self._n

    def marked_set(self) -> frozenset[int]:
        return self._declared

    def ancilla_width(self, lowering: Lowering) -> int:
        return 0

    def build_predicate(self, lowering: Lowering) -> GateList:
        honest = TamperedSpec(self._n, self._built, self._built)
        return OracleSpec._build_truth_table(honest)


def test_a_correct_oracle_passes_and_the_same_oracle_against_a_shifted_set_fails():
    spec = RandomControlOracleSpec(n_qubits=5, n_marked=4, seed=2)
    oracle = build_phase_oracle(spec)
    assert_oracle_is_diagonal(oracle, 5, spec.marked_set())

    marked = sorted(spec.marked_set())
    unmarked = next(x for x in range(32) if x not in spec.marked_set())
    one_off = frozenset(marked[1:] + [unmarked])
    with pytest.raises(AssertionError, match="oracle phase wrong on 2 states"):
        assert_oracle_is_diagonal(oracle, 5, one_off)
    with pytest.raises(AssertionError, match="oracle phase wrong on 1 states"):
        assert_oracle_is_diagonal(oracle, 5, frozenset(marked[1:]))
    with pytest.raises(AssertionError, match="oracle phase wrong on 1 states"):
        assert_oracle_is_diagonal(oracle, 5, frozenset(marked + [unmarked]))


def test_an_oracle_that_leaves_its_flag_dirty_is_not_diagonal():
    """Predicate and ``Z`` with no uncompute: the phases are right and the flag is left set on every
    marked input. As a Grover oracle that is an entangling operation, and it must be refused."""
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=3, seed=5)
    dirty = spec.build_predicate(Lowering.TRUTH_TABLE)
    dirty.append(GateName.MCZ, dirty.num_qubits - 1)
    with pytest.raises(AssertionError, match="moved a basis state"):
        assert_oracle_is_diagonal(dirty, 4, spec.marked_set())


def test_an_oracle_that_leaves_an_ancilla_dirty_is_not_diagonal():
    """A correct sandwich, plus one stray CX from the search register into a spare ancilla."""
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=3, seed=5)
    oracle = build_phase_oracle(spec)
    wider = GateList(oracle.num_qubits + 1, list(oracle.gates))
    assert_oracle_is_diagonal(wider, 4, spec.marked_set())

    wider.append(GateName.CX, 0, oracle.num_qubits)
    with pytest.raises(AssertionError, match="moved a basis state"):
        assert_oracle_is_diagonal(wider, 4, spec.marked_set())


def test_an_oracle_with_the_wrong_phase_gate_is_refused():
    """``S`` where the ``Z`` belongs kicks back ``i`` rather than ``-1``: right states, wrong phase.
    The imaginary part is what catches it."""
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=2, seed=8)
    predicate = spec.build_predicate(Lowering.TRUTH_TABLE)
    wrong = predicate.copy()
    wrong.append(GateName.S, predicate.num_qubits - 1)
    wrong.extend(predicate.inverse())
    with pytest.raises(AssertionError, match="oracle phase wrong on 2 states"):
        assert_oracle_is_diagonal(wrong, 4, spec.marked_set())


def test_a_predicate_that_matches_its_spec_passes(random_spec, hidden_period_spec):
    """The two control fixtures, which no test had put through the equivalence check."""
    for spec in (random_spec, hidden_period_spec):
        for lowering in Lowering:
            assert_predicate_matches_spec(spec, lowering)


@pytest.mark.parametrize(
    ("built", "n_wrong"),
    [({3, 9, 21}, 2), ({3, 9}, 1), ({3, 9, 20, 30}, 1), (set(range(32)) - {3, 9, 20}, 32)],
    ids=["one-item-off", "one-missing", "one-extra", "complemented"],
)
def test_a_predicate_that_disagrees_with_its_spec_is_refused(built, n_wrong):
    spec = TamperedSpec(5, frozenset({3, 9, 20}), frozenset(built))
    with pytest.raises(AssertionError, match=f"disagrees with the marked set on {n_wrong} of 32"):
        assert_predicate_matches_spec(spec, Lowering.TRUTH_TABLE)


def test_the_first_disagreeing_state_is_named():
    spec = TamperedSpec(5, frozenset({3, 9, 20}), frozenset({3, 9, 21}))
    with pytest.raises(AssertionError, match="first at 20"):
        assert_predicate_matches_spec(spec, Lowering.TRUTH_TABLE)


def test_a_predicate_too_wide_for_the_simulator_is_refused_not_truncated():
    class Wide(TamperedSpec):
        def build_predicate(self, lowering):
            gl = GateList(70)
            gl.append(GateName.CX, 0, 69)
            return gl

    with pytest.raises(SimulationError, match="too wide"):
        assert_predicate_matches_spec(Wide(2, frozenset({1}), frozenset({1})), Lowering.TRUTH_TABLE)


def test_ancilla_cleanliness_is_checked_in_both_directions():
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=3, seed=5)
    oracle = build_phase_oracle(spec)
    assert_ancillas_return_clean(oracle, 4)

    # The bare predicate leaves the flag set on marked inputs — by contract, and detectably.
    with pytest.raises(AssertionError, match="left ancillas dirty for search value"):
        assert_ancillas_return_clean(spec.build_predicate(Lowering.TRUTH_TABLE), 4)

    disturbed = GateList(5)
    disturbed.append(GateName.X, 2)
    with pytest.raises(AssertionError, match="disturbed the search register"):
        assert_ancillas_return_clean(disturbed, 4)


def test_the_sandwich_of_a_dirty_predicate_is_still_the_identity():
    """The contract in ``oracle_spec``: a predicate may leave ancillas set, because its exact inverse
    clears them. Shown on a predicate that is dirty and carries phases."""
    gl = GateList(5)
    gl.append(GateName.CX, 0, 3)
    gl.append(GateName.T, 3)
    gl.append(GateName.CCX, 1, 3, 4)
    gl.append(GateName.S, 4)
    with pytest.raises(AssertionError):
        assert_ancillas_return_clean(gl, 3)
    assert_sandwich_is_identity(gl, 3, label="dirty")


# ---------------------------------------------------------------------------------------------
# phase_to_complex
# ---------------------------------------------------------------------------------------------


def test_phase_to_complex_is_the_eighth_roots_of_unity():
    r = math.sqrt(0.5)
    want = [1, r + r * 1j, 1j, -r + r * 1j, -1, -r - r * 1j, -1j, r - r * 1j]
    np.testing.assert_allclose(phase_to_complex(np.arange(8)), want, atol=1e-15)


def test_phase_to_complex_reduces_modulo_eight_in_both_directions():
    exponents = np.array([8, 9, 16 + 4, -1, -4, -8, 8001])
    np.testing.assert_allclose(
        phase_to_complex(exponents), phase_to_complex(exponents % 8), atol=0.0
    )
    np.testing.assert_allclose(phase_to_complex(np.array([-1])), [cmath.exp(-1j * math.pi / 4)], atol=1e-15)


def test_phase_to_complex_keeps_the_shape_it_was_given():
    assert phase_to_complex(np.zeros((3, 5), dtype=np.int64)).shape == (3, 5)
    assert phase_to_complex([0, 4]).tolist() == [1.0, pytest.approx(-1.0)]


# ---------------------------------------------------------------------------------------------
# simulate_states, directly
# ---------------------------------------------------------------------------------------------


def test_each_permutation_gate_moves_the_states_it_should():
    gl = GateList(5)
    gl.append(GateName.X, 0)
    gl.append(GateName.CX, 0, 1)
    gl.append(GateName.CCX, 0, 1, 2)
    gl.append(GateName.MCX, 0, 1, 2, 3)
    final, phases = simulate_states(gl, np.array([0b00000, 0b00001, 0b10000]))
    # |0>: X sets bit 0, then each controlled gate fires in turn. |1>: X clears bit 0, nothing fires.
    assert final.tolist() == [0b01111, 0b00000, 0b11111]
    assert phases.tolist() == [0, 0, 0]


def test_each_phase_gate_contributes_its_exact_exponent():
    """``T T S Z`` on a set qubit is ``1 + 1 + 2 + 4``; on a clear qubit it is nothing at all."""
    gl = GateList(3)
    for name in (GateName.T, GateName.T, GateName.S, GateName.MCZ):
        gl.append(name, 0)
    gl.append(GateName.SDG, 1)
    gl.append(GateName.TDG, 1)
    gl.append(GateName.MCZ, 0, 1, 2)
    final, phases = simulate_states(gl, np.arange(8))
    assert final.tolist() == list(range(8))
    want = [(8 if x & 1 else 0) + (13 if x & 2 else 0) + (4 if x == 7 else 0) for x in range(8)]
    assert phases.tolist() == want
    np.testing.assert_allclose(
        phase_to_complex(phases), [cmath.exp(1j * math.pi / 4 * k) for k in want], atol=1e-12
    )


def test_the_result_does_not_depend_on_the_chunk_size():
    """Chunking bounds memory; it must not be visible in the answer, including at a chunk that does
    not divide the input and at a chunk of one."""
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=9, seed=4)
    oracle = build_phase_oracle(spec)
    initial = np.arange(64, dtype=np.uint64)
    whole = simulate_states(oracle, initial)
    for chunk in (1, 7, 64, 1000):
        final, phases = simulate_states(oracle, initial, chunk=chunk)
        assert np.array_equal(final, whole[0]) and np.array_equal(phases, whole[1])
    assert set(np.nonzero(whole[1] % 8 == 4)[0].tolist()) == set(spec.marked_set())


def test_the_input_array_is_not_modified():
    gl = GateList(2)
    gl.append(GateName.X, 0)
    initial = np.array([0, 1, 2, 3], dtype=np.uint64)
    final, _ = simulate_states(gl, initial)
    assert initial.tolist() == [0, 1, 2, 3]
    assert final.tolist() == [1, 0, 3, 2]


def test_a_gate_list_that_creates_superposition_is_refused():
    gl = GateList(2)
    gl.append(GateName.CX, 0, 1)
    gl.append(GateName.H, 0)
    with pytest.raises(SimulationError, match=r"\['h'\].*superposition"):
        simulate_states(gl, np.arange(4))


def test_a_gate_list_wider_than_a_machine_word_is_refused():
    gl = GateList(64)
    gl.append(GateName.X, 63)
    with pytest.raises(SimulationError, match="cannot exceed 63"):
        simulate_states(gl, np.array([0]))
    assert simulate_states(GateList(63, list(gl.gates[:0])), np.array([5]))[0].tolist() == [5]


def test_the_top_qubit_of_the_widest_legal_register_is_usable():
    """Bit 62 of a ``uint64``: the shifts must not overflow into the sign of a signed type."""
    gl = GateList(63)
    gl.append(GateName.X, 62)
    gl.append(GateName.CX, 62, 0)
    gl.append(GateName.MCZ, 62)
    final, phases = simulate_states(gl, np.array([0]))
    assert int(final[0]) == (1 << 62) | 1
    assert phases.tolist() == [4]


def test_simulate_predicate_flag_reads_the_last_qubit_over_the_search_register():
    spec = RandomControlOracleSpec(n_qubits=5, n_marked=6, seed=12)
    flags = simulate_predicate_flag(spec.build_predicate(Lowering.TRUTH_TABLE), 5)
    assert flags.dtype == bool and flags.shape == (32,)
    assert set(np.nonzero(flags)[0].tolist()) == set(spec.marked_set())


@pytest.mark.parametrize("n_search", [-1, 3, 4])
def test_simulate_predicate_flag_refuses_a_search_width_that_leaves_no_flag(n_search):
    gl = GateList(3)
    gl.append(GateName.CX, 0, 2)
    with pytest.raises(SimulationError, match="outside a 3-qubit circuit"):
        simulate_predicate_flag(gl, n_search)


# ---------------------------------------------------------------------------------------------
# the simulator against an independent reference and two frameworks
# ---------------------------------------------------------------------------------------------

WIDTH = 5

_REFERENCE_PHASE = {GateName.S: 2, GateName.SDG: 6, GateName.T: 1, GateName.TDG: 7}


def reference_trajectory(gl: GateList, state: int) -> tuple[int, int]:
    """One basis state through a permutation-and-phase gate list, in plain Python integers.

    Written from the gate definitions in the IR's docstrings and sharing nothing with the module
    under test — not NumPy, not ``phase_exponent``, not the bit-packing. ``PERM`` is little-endian:
    ``qubits[k]`` carries bit ``k`` of the table index and of the table entry.
    """
    exponent = 0
    for gate in gl.gates:
        bit = [(state >> q) & 1 for q in gate.qubits]
        if gate.name is GateName.X:
            state ^= 1 << gate.qubits[0]
        elif gate.name in (GateName.CX, GateName.CCX, GateName.MCX):
            if all(bit[:-1]):
                state ^= 1 << gate.qubits[-1]
        elif gate.name is GateName.MCZ:
            exponent += 4 if all(bit) else 0
        elif gate.name in _REFERENCE_PHASE:
            exponent += _REFERENCE_PHASE[gate.name] * bit[0]
        elif gate.name is GateName.PERM:
            image = gate.params[0][sum(b << k for k, b in enumerate(bit))]
            for k, q in enumerate(gate.qubits):
                state = (state & ~(1 << q)) | (((image >> k) & 1) << q)
        else:
            raise AssertionError(f"{gate.name} has no single trajectory")
    return state, exponent % 8


def reference_unitary(gl: GateList) -> np.ndarray:
    dim = 1 << gl.num_qubits
    matrix = np.zeros((dim, dim), dtype=complex)
    for x in range(dim):
        final, exponent = reference_trajectory(gl, x)
        matrix[final, x] = cmath.exp(1j * math.pi / 4 * exponent)
    return matrix


def qiskit_unitary(gl: GateList) -> np.ndarray:
    from qiskit.quantum_info import Operator

    return np.asarray(Operator(to_qiskit(gl)).data)


def cirq_unitary_little_endian(gl: GateList) -> np.ndarray:
    """cirq's unitary over every declared qubit, re-indexed into the IR's reading.

    cirq takes the first qubit of the order as the most significant bit of the index; the IR and
    Qiskit take qubit 0 as the least. Reversing the bits of both indices converts one to the other.
    Spelled out here, not imported from the compiler whose convention is being checked.
    """
    import cirq

    n = gl.num_qubits
    unitary = to_cirq(gl).unitary(qubit_order=cirq.LineQubit.range(n))
    order = [int(format(i, f"0{n}b")[::-1], 2) for i in range(1 << n)]
    return unitary[np.ix_(order, order)]


@st.composite
def gates(draw, width: int, with_perm: bool):
    names = [GateName.X, GateName.CX, GateName.CCX, GateName.MCX, GateName.MCZ]
    names += [GateName.S, GateName.SDG, GateName.T, GateName.TDG]
    if with_perm:
        names += [GateName.PERM, GateName.PERM]  # weighted up: it is the gate with a history
    name = draw(st.sampled_from(names))
    arity = {
        GateName.CX: st.just(2),
        GateName.CCX: st.just(3),
        GateName.MCX: st.integers(4, width),
        GateName.MCZ: st.integers(1, width),
        GateName.PERM: st.integers(1, 3),
    }.get(name, st.just(1))
    k = draw(arity)
    qubits = tuple(draw(st.permutations(range(width)))[:k])
    params = (tuple(draw(st.permutations(range(1 << k)))),) if name is GateName.PERM else ()
    return Gate(name, qubits, params)


def gate_lists(with_perm: bool):
    return st.lists(gates(WIDTH, with_perm), min_size=1, max_size=12).map(
        lambda gs: GateList(WIDTH, list(gs), "drawn")
    )


@settings(deadline=None, max_examples=60)
@given(gl=gate_lists(with_perm=False))
def test_the_bitmask_simulator_agrees_with_the_reference_and_both_frameworks(gl):
    """Every basis state of a drawn permutation-and-phase circuit, four ways.

    ``simulate_states`` is compared with the plain-Python reference exactly (integers), and the
    unitary it implies is compared with Qiskit's and cirq's. Non-contiguous, out-of-order qubit
    tuples are drawn on purpose: a simulator that read ``qubits`` as sorted would pass on
    ``(0, 1, 2)`` and fail here.
    """
    dim = 1 << WIDTH
    final, phases = simulate_states(gl, np.arange(dim))
    reference = [reference_trajectory(gl, x) for x in range(dim)]

    assert final.tolist() == [state for state, _ in reference]
    assert (phases % 8).tolist() == [exponent for _, exponent in reference]

    implied = np.zeros((dim, dim), dtype=complex)
    implied[final.astype(np.int64), np.arange(dim)] = phase_to_complex(phases)
    assert_unitary(implied, 1e-12)
    np.testing.assert_allclose(qiskit_unitary(gl), implied, atol=1e-9)
    np.testing.assert_allclose(cirq_unitary_little_endian(gl), implied, atol=1e-7)


@settings(deadline=None, max_examples=60)
@given(gl=gate_lists(with_perm=True))
def test_perm_gates_mean_the_same_thing_through_qiskit_and_through_cirq(gl):
    """The lowering that was once wrong. Both frameworks against the reference — not against each
    other, since two compilers sharing ``_permutation_matrix`` could share a mistake in it."""
    want = reference_unitary(gl)
    assert_unitary(want, 1e-12)
    np.testing.assert_allclose(qiskit_unitary(gl), want, atol=1e-9)
    np.testing.assert_allclose(cirq_unitary_little_endian(gl), want, atol=1e-7)


def test_the_perm_cross_check_would_notice_a_bit_reversed_table():
    """Keeps the test above honest: a three-qubit table that is not symmetric under bit reversal,
    on non-contiguous qubits, gives a different unitary when its qubit order is reversed."""
    table = (3, 1, 0, 2, 5, 7, 6, 4)
    gl = GateList(WIDTH, [Gate(GateName.PERM, (0, 2, 3), (table,))])
    backwards = GateList(WIDTH, [Gate(GateName.PERM, (3, 2, 0), (table,))])
    assert not np.allclose(reference_unitary(gl), reference_unitary(backwards))
    np.testing.assert_allclose(qiskit_unitary(backwards), reference_unitary(backwards), atol=1e-9)
    np.testing.assert_allclose(cirq_unitary_little_endian(backwards), reference_unitary(backwards), atol=1e-7)


def drawn_circuit(seed: int, with_perm: bool) -> GateList:
    """A basis-state preparation followed by fourteen seeded gates, over out-of-order qubit tuples."""
    rng = np.random.default_rng(seed)
    start = int(rng.integers(1, 1 << WIDTH))
    choices = [GateName.X, GateName.CX, GateName.CCX, GateName.MCX, GateName.MCZ]
    choices += [GateName.S, GateName.SDG, GateName.T, GateName.TDG]
    choices += [GateName.PERM] * 3 if with_perm else []
    arity = {GateName.CX: 2, GateName.CCX: 3, GateName.MCX: 4, GateName.MCZ: 2, GateName.PERM: 2}

    gl = GateList(WIDTH, label=f"engine-check:{seed}")
    for q in range(WIDTH):
        if (start >> q) & 1:
            gl.append(GateName.X, q)
    for _ in range(14):
        name = choices[int(rng.integers(len(choices)))]
        k = arity.get(name, 1)
        qubits = tuple(int(q) for q in rng.permutation(WIDTH)[:k])
        params = (tuple(int(v) for v in rng.permutation(1 << k)),) if name is GateName.PERM else ()
        gl.gates.append(Gate(name, qubits, params))
    return gl


def one_hot(gl: GateList) -> np.ndarray:
    """The statevector the reference predicts for ``gl`` applied to ``|0...0>``."""
    final, exponent = reference_trajectory(gl, 0)
    want = np.zeros(1 << gl.num_qubits, dtype=complex)
    want[final] = cmath.exp(1j * math.pi / 4 * exponent)
    return want


@pytest.mark.parametrize("seed", range(8))
def test_the_bitmask_simulator_agrees_with_a_statevector_engine(aer_backend, seed):
    """On Aer, through the project's own backend class: all the amplitude lands on the state the
    bitmask simulator says, carrying the phase it says — compared entry by entry with no global
    phase divided out, because for a basis state there is none to hide behind."""
    gl = drawn_circuit(seed, with_perm=False)
    states, phases = simulate_states(gl, np.array([0]))

    want = np.zeros(1 << WIDTH, dtype=complex)
    want[int(states[0])] = phase_to_complex(phases)[0]
    np.testing.assert_allclose(aer_backend.run_statevector(gl).statevector, want, atol=1e-9)
    np.testing.assert_allclose(want, one_hot(gl), atol=1e-12)


@pytest.mark.parametrize("engine_name", ["cirq_qsim", "tensor_network"])
@pytest.mark.parametrize("seed", range(6))
def test_drawn_perm_circuits_run_correctly_on_the_other_engines(engine_name, seed):
    """The same kind of circuit with ``PERM`` gates drawn in, on the two engines that do not go
    through Qiskit's transpiler. qsim is single precision, hence the tolerance."""
    from grover_emulator.backends import load_engine

    gl = drawn_circuit(seed, with_perm=True)
    assert any(g.name is GateName.PERM for g in gl.gates)
    statevector = load_engine(engine_name)().run_statevector(gl).statevector
    np.testing.assert_allclose(statevector, one_hot(gl), atol=1e-6)


SWAP_TABLE = (0, 2, 1, 3)
"""The two-qubit permutation that exchanges its qubits: index ``b0 + 2*b1`` goes to ``b1 + 2*b0``."""


def swap_shaped_perm() -> GateList:
    gl = GateList(2, label="swap-shaped-perm")
    gl.append(GateName.X, 0)
    gl.append(GateName.PERM, 0, 1, params=(SWAP_TABLE,))
    return gl


def test_a_swap_shaped_perm_is_compiled_correctly_by_both_frameworks():
    """``X(0)`` then the exchange leaves the excitation on qubit 1: basis index 2. Both compiled
    circuits say so, and so does the Aer *sampling* path — which localises the expected failure
    below to the statevector path of the Aer backend, not to ``to_qiskit``."""
    gl = swap_shaped_perm()
    assert reference_trajectory(gl, 0) == (2, 0)
    np.testing.assert_allclose(qiskit_unitary(gl), reference_unitary(gl), atol=1e-12)
    np.testing.assert_allclose(cirq_unitary_little_endian(gl), reference_unitary(gl), atol=1e-7)


def test_a_swap_shaped_perm_is_sampled_correctly_on_aer(aer_backend):
    assert aer_backend.run_sampled(swap_shaped_perm(), shots=32, seed=1).counts == {2: 32}


def test_a_swap_shaped_perm_gives_the_right_statevector_on_aer(aer_backend):
    gl = swap_shaped_perm()
    statevector = aer_backend.run_statevector(gl).statevector
    np.testing.assert_allclose(statevector, one_hot(gl), atol=1e-9)


def test_the_simulators_perm_branch_computes_the_right_permutation():
    """``validation._apply`` carries a ``PERM`` branch. It is driven directly here, because
    ``simulate_states`` refuses any gate list containing ``PERM`` before reaching it (see the
    expected failure below) — so without this the branch would be both untested and unreachable.
    Non-contiguous, out-of-order qubits, against the reference, for every basis state."""
    from grover_emulator.utils.validation import _apply

    rng = np.random.default_rng(20260920)
    for qubits in [(0,), (1, 0), (0, 2), (4, 1, 3), (2, 0, 4), (3, 2, 1)]:
        table = tuple(int(v) for v in rng.permutation(1 << len(qubits)))
        gate = Gate(GateName.PERM, qubits, (table,))
        states = np.arange(1 << WIDTH, dtype=np.uint64)
        phases = np.zeros(1 << WIDTH, dtype=np.int64)
        _apply(states, phases, gate)

        gl = GateList(WIDTH, [gate])
        assert states.tolist() == [reference_trajectory(gl, x)[0] for x in range(1 << WIDTH)]
        assert not phases.any()
        assert sorted(states.tolist()) == list(range(1 << WIDTH))


def test_simulate_states_follows_a_basis_state_through_a_perm_gate():
    gl = GateList(3)
    gl.append(GateName.X, 0)
    gl.append(GateName.PERM, 0, 2, params=((1, 2, 3, 0),))
    gl.append(GateName.T, 2)

    final, phases = simulate_states(gl, np.arange(8))

    reference = [reference_trajectory(gl, x) for x in range(8)]
    assert final.tolist() == [state for state, _ in reference]
    assert (phases % 8).tolist() == [exponent for _, exponent in reference]
