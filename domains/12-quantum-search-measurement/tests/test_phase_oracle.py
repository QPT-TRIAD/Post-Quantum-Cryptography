"""The phase oracle, for the three specs the plan names — on an engine, not only on paper.

Before this file, ``assert_oracle_is_diagonal`` had only ever been pointed at the corpus oracles.
The QLWR oracle, the random control and the hidden-period control were validated through their
success curves, which depend on ``(M, N)`` and would forgive a marked set of the right size in the
wrong place. Three kinds of evidence here, in increasing independence from the project's own code:

1. **The bitmask simulator** (``assert_oracle_is_diagonal``): exact, and the only thing that can
   reach the arithmetic lowering, whose oracle is fifty qubits wide. Its dense operator would be
   ``2**100`` entries, so it is never built.
2. **A real engine.** The truth-table oracle is applied to the uniform superposition on Aer and the
   *sign of every amplitude* is read back: minus on the marked states, plus on the rest, zero outside
   the clean-ancilla subspace. This is the plan's "verified via statevector simulation, not asserted
   from theory", on a simulator the project did not write.
3. **Qiskit's dense operator**, in the property test, where the register is small enough for it. The
   expected diagonal is written out from first principles, including what the sandwich does when the
   flag starts at 1 — which no other test in the suite looks at.

The two lowerings are also compared with each other directly, flag for flag, on more than the one
worked instance the rest of the suite uses.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grover_emulator.circuits.compilers import to_qiskit
from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.circuits.phase_oracle import build_phase_oracle, oracle_width
from grover_emulator.problem.oracle_spec import (
    HiddenPeriodOracleSpec,
    Lowering,
    OracleSpec,
    QLWROracleSpec,
    RandomControlOracleSpec,
)
from grover_emulator.problem.qlwr_instance import generate_scaled_instance
from grover_emulator.utils.validation import assert_oracle_is_diagonal, simulate_predicate_flag

# (n_search, nu, seed). Twelve is the smallest width at which a faithful instance exists; the seeds
# other than the fixture's give different bases, secrets and marked values, and fourteen gives a
# different modulus (q_L = 113 rather than 61), so the arithmetic is not checked at one prime only.
QLWR_CASES = [(12, 2, 20260913), (12, 2, 7), (12, 2, 99), (14, 2, 5)]

CONTROL_CASES = [
    ("random", 4, 1, 3),
    ("random", 6, 5, 3),
    ("random", 8, 8, 11),
    ("random", 8, 255, 2),  # all but one state marked: the dense end of the range
    ("period", 4, 0b10, 1),
    ("period", 6, 0b110, 5),
    ("period", 8, 0b100, 11),
]


@pytest.fixture(scope="module", params=QLWR_CASES, ids=lambda c: f"n{c[0]}-nu{c[1]}-seed{c[2]}")
def qlwr_case(request):
    """A QLWR spec per case, built once: generation enumerates the marked set."""
    n_search, nu, seed = request.param
    return QLWROracleSpec(generate_scaled_instance(n_search=n_search, nu=nu, seed=seed))


def control_spec(kind: str, n: int, parameter: int, seed: int) -> OracleSpec:
    if kind == "random":
        return RandomControlOracleSpec(n_qubits=n, n_marked=parameter, seed=seed)
    return HiddenPeriodOracleSpec(n_qubits=n, period=parameter, seed=seed)


def signs_on_the_uniform_superposition(engine, spec: OracleSpec) -> np.ndarray:
    """Run ``H^n ; oracle`` on an engine and return the amplitudes scaled by ``sqrt(N)``.

    Scaled so that a correct oracle gives exactly ``+1`` or ``-1`` on every clean-ancilla index and
    ``0`` everywhere else. Nothing is normalised by a reference amplitude: a global phase on the
    engine's output would be a finding, so it is left in to be seen.
    """
    n = spec.search_width()
    oracle = build_phase_oracle(spec, Lowering.TRUTH_TABLE)
    gl = GateList(oracle.num_qubits, label="uniform-then-oracle")
    for q in range(n):
        gl.append(GateName.H, q)
    gl.extend(oracle)
    return engine.run_statevector(gl).statevector * np.sqrt(1 << n)


def assert_signs_match_the_marked_set(scaled: np.ndarray, spec: OracleSpec) -> None:
    n = spec.search_width()
    marked = spec.marked_set()
    want = np.array([-1.0 if x in marked else 1.0 for x in range(1 << n)])

    np.testing.assert_allclose(scaled[: 1 << n], want, atol=1e-9)
    # Everything above the search register is the flag (and any ancilla) being non-zero. The oracle
    # must leave no amplitude there at all, or the diffuser would be acting on an entangled register.
    assert np.max(np.abs(scaled[1 << n :])) < 1e-9
    assert int(np.sum(scaled[: 1 << n].real < 0)) == len(marked)


# ---------------------------------------------------------------------------------------------
# QLWR: both lowerings
# ---------------------------------------------------------------------------------------------


def test_the_qlwr_cases_are_genuinely_different_instances():
    """Several seeds are only several tests if they give several instances."""
    specs = [QLWROracleSpec(generate_scaled_instance(n_search=n, nu=nu, seed=s)) for n, nu, s in QLWR_CASES]
    assert len({spec.marked_set() for spec in specs}) == len(specs)
    assert len({spec.instance.base for spec in specs}) == len(specs)
    assert len({spec.instance.q_l for spec in specs}) >= 2
    assert all(spec.search_width() == n for spec, (n, _, _) in zip(specs, QLWR_CASES))


def test_the_truth_table_qlwr_oracle_is_diagonal_with_the_right_signs(qlwr_case):
    spec = qlwr_case
    oracle = build_phase_oracle(spec, Lowering.TRUTH_TABLE)
    assert oracle.num_qubits == spec.search_width() + 1
    assert_oracle_is_diagonal(oracle, spec.search_width(), spec.marked_set())


def test_the_truth_table_qlwr_oracle_flips_exactly_the_marked_amplitude_on_aer(qlwr_case, aer_backend):
    scaled = signs_on_the_uniform_superposition(aer_backend, qlwr_case)
    assert_signs_match_the_marked_set(scaled, qlwr_case)


def test_the_arithmetic_predicate_marks_exactly_the_truth_table_marked_set(qlwr_case):
    """Every ``x``, by bitmask simulation of the fifty-qubit predicate, against two references: the
    truth-table *circuit's* flag, and the instance's own ``is_solution`` evaluated here one value at
    a time. The second is what keeps this from being a comparison of two circuits that share a
    marked set they both got from the same place."""
    spec = qlwr_case
    n = spec.search_width()

    arithmetic = simulate_predicate_flag(spec.build_predicate(Lowering.ARITHMETIC), n)
    truth_table = simulate_predicate_flag(spec.build_predicate(Lowering.TRUTH_TABLE), n)
    relation = np.array([spec.instance.is_solution(x) for x in range(1 << n)])

    assert arithmetic.shape == (1 << n,)
    assert np.array_equal(arithmetic, truth_table)
    assert np.array_equal(arithmetic, relation)
    assert set(np.nonzero(arithmetic)[0].tolist()) == set(spec.marked_set())
    assert np.array_equal(arithmetic, spec.truth_table())


def test_the_arithmetic_qlwr_oracle_is_diagonal_with_the_right_signs(qlwr_case):
    """The whole sandwich at the arithmetic lowering: every search value comes back to itself with
    every ancilla clean, carrying ``-1`` exactly when marked. Bitmask only — this oracle is about
    fifty qubits wide and has no dense form anyone could hold."""
    spec = qlwr_case
    oracle = build_phase_oracle(spec, Lowering.ARITHMETIC)

    assert oracle.num_qubits == oracle_width(spec, Lowering.ARITHMETIC)
    assert 40 < oracle.num_qubits <= 63, "outside the range the bitmask simulator was sized for"
    assert oracle.is_classically_simulable()
    assert_oracle_is_diagonal(oracle, spec.search_width(), spec.marked_set())


def test_the_two_qlwr_oracles_differ_in_cost_and_not_in_function(qlwr_case):
    """Same diagonal (asserted above), very different circuits — which is the point of having both:
    one is simulable, the other is the one whose gate count means something."""
    spec = qlwr_case
    cheap = build_phase_oracle(spec, Lowering.TRUTH_TABLE)
    faithful = build_phase_oracle(spec, Lowering.ARITHMETIC)
    assert len(faithful) > 100 * len(cheap)
    assert faithful.num_qubits > cheap.num_qubits
    assert cheap.label == "qlwr:truth_table:oracle"
    assert faithful.label == "qlwr:arithmetic:oracle"


def test_an_arithmetic_oracle_checked_against_the_wrong_marked_set_fails(qlwr_case):
    """The positive assertions above are only worth something if the helper can say no."""
    spec = qlwr_case
    oracle = build_phase_oracle(spec, Lowering.ARITHMETIC)
    (marked,) = spec.marked_set()
    shifted = frozenset({(marked + 1) % (1 << spec.search_width())})
    with pytest.raises(AssertionError, match="oracle phase wrong on 2 states"):
        assert_oracle_is_diagonal(oracle, spec.search_width(), shifted)


# ---------------------------------------------------------------------------------------------
# the controls
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("kind", "n", "parameter", "seed"), CONTROL_CASES)
def test_a_control_oracle_is_diagonal_with_the_right_signs(kind, n, parameter, seed):
    """Both lowerings, because for a control both *are* the lookup table and must stay that way."""
    spec = control_spec(kind, n, parameter, seed)
    for lowering in Lowering:
        oracle = build_phase_oracle(spec, lowering)
        assert oracle.num_qubits == n + 1
        assert_oracle_is_diagonal(oracle, n, spec.marked_set())


@pytest.mark.parametrize(("kind", "n", "parameter", "seed"), CONTROL_CASES)
def test_a_control_oracle_flips_exactly_the_marked_amplitudes_on_aer(kind, n, parameter, seed, aer_backend):
    spec = control_spec(kind, n, parameter, seed)
    scaled = signs_on_the_uniform_superposition(aer_backend, spec)
    assert_signs_match_the_marked_set(scaled, spec)


def test_the_shared_control_fixtures_pass_the_same_engine_check(random_spec, hidden_period_spec, aer_backend):
    """The specs every other test file uses as its controls, so that what those files assume about
    them is something this suite has actually run."""
    for spec in (random_spec, hidden_period_spec):
        assert_oracle_is_diagonal(build_phase_oracle(spec), spec.search_width(), spec.marked_set())
        assert_signs_match_the_marked_set(signs_on_the_uniform_superposition(aer_backend, spec), spec)


def test_the_hidden_period_oracle_carries_its_period_in_its_signs(aer_backend):
    """The engine's sign pattern is invariant under ``x -> x XOR period`` — the planted structure,
    read off amplitudes rather than off the spec's own set."""
    spec = HiddenPeriodOracleSpec(n_qubits=6, period=0b1010, seed=4)
    signs = signs_on_the_uniform_superposition(aer_backend, spec)[: 1 << 6].real
    shifted = signs[np.arange(1 << 6) ^ spec.period]
    np.testing.assert_allclose(signs, shifted, atol=1e-9)
    assert np.any(signs < 0) and np.any(signs > 0)


# ---------------------------------------------------------------------------------------------
# the structure of the sandwich
# ---------------------------------------------------------------------------------------------


def test_the_oracle_is_predicate_then_z_then_the_exact_inverse():
    """Gate for gate. The inverse is the IR's own reversal, never a framework's resynthesis."""
    spec = RandomControlOracleSpec(n_qubits=5, n_marked=3, seed=9)
    predicate = spec.build_predicate(Lowering.TRUTH_TABLE)
    oracle = build_phase_oracle(spec)
    k = len(predicate)

    assert len(oracle) == 2 * k + 1
    assert oracle.gates[:k] == predicate.gates
    assert oracle.gates[k].name is GateName.MCZ
    assert oracle.gates[k].qubits == (predicate.num_qubits - 1,), "the phase belongs on the flag"
    assert oracle.gates[k + 1 :] == predicate.inverse().gates
    assert sum(1 for g in oracle.gates if g.name is GateName.MCZ) == 1


def test_building_an_oracle_does_not_disturb_the_predicate_it_was_built_from():
    """``build_phase_oracle`` copies before it appends; a spec that cached its predicate would
    otherwise grow by a sandwich every time an oracle was built from it."""
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=2, seed=1)
    before = len(spec.build_predicate(Lowering.TRUTH_TABLE))
    first, second = build_phase_oracle(spec), build_phase_oracle(spec)
    assert len(spec.build_predicate(Lowering.TRUTH_TABLE)) == before
    assert first.gates == second.gates


# ---------------------------------------------------------------------------------------------
# property: any register, any marked set
# ---------------------------------------------------------------------------------------------


class ExplicitSetSpec(OracleSpec):
    """A spec over a marked set given outright, so the property can range over *sets* rather than
    over the seeds of a generator. It supplies only the set; the lowering under test is the shared
    one every spec in the project inherits."""

    name = "explicit_set"

    def __init__(self, n_qubits: int, marked: frozenset[int]):
        self._n = n_qubits
        self._marked = frozenset(marked)

    def search_width(self) -> int:
        return self._n

    def marked_set(self) -> frozenset[int]:
        return self._marked

    def ancilla_width(self, lowering: Lowering) -> int:
        return 0

    def build_predicate(self, lowering: Lowering) -> GateList:
        return self._build_truth_table()


@st.composite
def register_and_marked_set(draw):
    """``(n, marked)`` with ``marked`` non-empty and proper — the only sets Grover is defined on."""
    n = draw(st.integers(min_value=1, max_value=5))
    size = 1 << n
    marked = draw(st.sets(st.integers(min_value=0, max_value=size - 1), min_size=1, max_size=size - 1))
    return n, frozenset(marked)


@settings(deadline=None, max_examples=60)
@given(case=register_and_marked_set())
def test_the_oracle_flips_exactly_the_marked_basis_states_and_no_others(case):
    """For any small ``n`` and any non-empty proper marked set, by Qiskit's dense operator.

    The full diagonal is predicted, not only the half the algorithm uses. With the flag clear the
    entry is ``(-1)**f(x)``. With the flag *set* the predicate clears it exactly when ``x`` is
    marked, so the ``Z`` fires on the unmarked states instead and the entry is ``-(-1)**f(x)``.
    A sandwich that was not an exact inverse, or a ``Z`` on the wrong qubit, breaks one half or the
    other.
    """
    from qiskit.quantum_info import Operator

    n, marked = case
    spec = ExplicitSetSpec(n, marked)
    oracle = build_phase_oracle(spec)
    matrix = np.asarray(Operator(to_qiskit(oracle)).data)

    f = np.array([1 if x in marked else 0 for x in range(1 << n)])
    want = np.concatenate([(-1.0) ** f, -((-1.0) ** f)])
    np.testing.assert_allclose(matrix, np.diag(want), atol=1e-10)

    # The same fact through the project's own checker, so the two are known to agree with each other.
    assert_oracle_is_diagonal(oracle, n, marked)
    assert int(np.sum(np.diag(matrix)[: 1 << n].real < 0)) == len(marked)


@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=7),
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    data=st.data(),
)
def test_a_random_control_oracle_marks_its_own_set_for_any_size_and_seed(n, seed, data):
    """The generator-backed form of the property, over every legal ``n_marked`` — including the
    extremes ``1`` and ``2**n - 1`` that the fixed cases only sample."""
    n_marked = data.draw(st.integers(min_value=1, max_value=(1 << n) - 1), label="n_marked")
    spec = RandomControlOracleSpec(n_qubits=n, n_marked=n_marked, seed=seed)
    assert len(spec.marked_set()) == n_marked

    flags = simulate_predicate_flag(spec.build_predicate(Lowering.TRUTH_TABLE), n)
    assert set(np.nonzero(flags)[0].tolist()) == set(spec.marked_set())
    assert_oracle_is_diagonal(build_phase_oracle(spec), n, spec.marked_set())
