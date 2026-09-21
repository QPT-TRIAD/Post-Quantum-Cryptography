"""The corpus's two oracles: the relation is what the corpus's own code says it is, at k = 1.

Two of these tests are the acceptance conditions that matter, and both are comparisons against
something outside this project rather than against a re-implementation of it.

**The single-hash semantics is transcribed, not paraphrased.** ``grover_chain_inversion`` in
``pq_audit_s1_lms_v2.1.py`` is short enough to write out again exactly as it stands, and that is what
the first test does: the same digest input assembled field for field, the same prefix, the same mask.
If the spec's chain ever drifts from that function — a different encodings width, a symmetrised
field order, a mask that stops folding — the two disagree on some candidate and the test names it.
The mask is the part worth pinning: at a width that is not a multiple of eight the corpus keeps the
low ``n`` bits of a ``ceil(n / 8)``-byte prefix, which is not the same function as taking the high
``n`` bits, and only a width like 10 or 14 tells them apart.

**The quadratic form's convention is measured, not assumed.** ``QuadraticFormGate`` evaluates
``x^T A x + x^T b + c`` with ``A`` used as given; the corpus's key map stores ``A`` as the upper
triangle and evaluates ``sum_{i<j} A[i][j] x_i x_j``. Those are the same function only because the
monomials live strictly above the diagonal in both — so the test evaluates all three readings (the
spec's own map, the dense-matrix reading, and the framework gate's output over a statevector) on
every input at a width small enough to enumerate, and a disagreement is a disagreement on a specific
``x`` rather than a statistic.
"""

from __future__ import annotations

import hashlib
import math
import struct

import numpy as np
import pytest

from grover_emulator.circuits.ir import GateName
from grover_emulator.circuits.phase_oracle import build_phase_oracle, oracle_width
from grover_emulator.problem.corpus_oracles import (
    ChainConvention,
    KeyMapMode,
    LMOtsChainSpec,
    ModeBKeyMapSpec,
)
from grover_emulator.problem.oracle_spec import Lowering
from grover_emulator.utils.seeding import RunSeeds
from grover_emulator.utils.validation import (
    assert_ancillas_return_clean,
    assert_oracle_is_diagonal,
    assert_predicate_matches_spec,
)

# The widths the corpus's own reduced-size sweep uses. 10 and 14 are the interesting ones: the
# digest prefix is two bytes and the mask is a genuine fold, not a byte truncation.
CORPUS_WIDTHS = (8, 10, 12, 14)


def corpus_chain(n_bits: int, x: int, *, identifier=b"I" * 16, q=3, i=5, j=2) -> int:
    """``grover_chain_inversion``'s ``f``, transcribed as it stands.

    One SHA-256 over ``I || u32(q) || u16(i) || u8(j) || x``, the first ``ceil(n / 8)`` bytes read
    big-endian and masked to ``n`` bits. Nothing here is derived from the spec under test; it is the
    corpus's function, and the spec has to meet it.
    """
    n_bytes = (n_bits + 7) // 8
    payload = (
        identifier
        + struct.pack(">I", q)
        + struct.pack(">H", i)
        + struct.pack(">B", j)
        + x.to_bytes(n_bytes, "big")
    )
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:n_bytes], "big") & ((1 << n_bits) - 1)


# -----------------------------------------------------------------------------------------------
# LMOtsChainSpec
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n_bits", CORPUS_WIDTHS)
def test_single_hash_semantics_reproduces_the_corpus_function(n_bits):
    """At ``chain_length = 1`` the spec's chain is the corpus's function on every candidate."""
    spec = LMOtsChainSpec(n_bits)
    assert spec.chain_length == 1
    assert spec.convention is ChainConvention.SINGLE_HASH
    for x in range(1 << n_bits):
        assert spec._chain(x) == corpus_chain(n_bits, x), f"chain disagrees at x={x}, n={n_bits}"


@pytest.mark.parametrize("n_bits", CORPUS_WIDTHS)
def test_marked_set_is_the_preimage_of_the_target(n_bits):
    """The marked set is exactly the preimage of the recorded target, and ``M`` is its size.

    Computed here from the transcribed function rather than from the spec's, so a spec whose
    ``marked_set`` and whose ``_chain`` disagree cannot pass by agreeing with itself.
    """
    spec = LMOtsChainSpec(n_bits)
    want = frozenset(x for x in range(1 << n_bits) if corpus_chain(n_bits, x) == spec._target)
    assert spec.marked_set() == want
    assert spec.space().n_marked == len(want) >= 1
    assert spec.report()["target"] == spec._target


def test_the_secret_is_seeded_so_m_is_fixed_and_reported():
    """Two constructions of the same description are the same problem, and a different seed is not.

    This is the defect the upstream game has and this spec does not: there the secret came from
    ``secrets.randbelow(N)``, so ``M`` moved between runs with nothing in the result to say which
    draw had happened.
    """
    a, b = LMOtsChainSpec(12), LMOtsChainSpec(12)
    assert a._secret == b._secret
    assert a.marked_set() == b.marked_set()
    assert a.report()["n_marked"] == b.report()["n_marked"]

    other = LMOtsChainSpec(12, seed=20260914)
    assert other._secret != a._secret
    assert other._target != a._target


def test_the_seed_record_carries_the_marked_set_size():
    """A run's record holds the ``M`` its curve was computed against."""
    seeds = RunSeeds(root=20260913)
    spec = LMOtsChainSpec(10, seeds=seeds)
    record = seeds.to_dict()
    assert record["facts"]["lmots_chain.marked_set_size"] == spec.space().n_marked
    assert record["facts"]["lmots_chain.target"] == spec._target
    seeds.verify()


def test_chain_length_selects_the_iterated_convention_and_advances_j():
    """``k > 1`` is a chain over advancing indices, and it is reported as one.

    Built here by hand from the transcribed node function: the spec must apply the node ``k`` times
    with the chain index advancing from ``j``, which at ``k = 1`` collapses to the corpus's single
    call and above it does not.
    """
    k = 3
    spec = LMOtsChainSpec(10, k)
    assert spec.chain_length == k
    assert spec.convention is ChainConvention.ITERATED_CHAIN

    for x in (0, 1, 517, 1023):
        value = x
        for step in range(k):
            value = corpus_chain(
                10,
                value,
                identifier=spec.identifier,
                q=spec.q,
                i=spec.i,
                j=spec.j + step,
            )
        assert spec._chain(x) == value

    # The two conventions are different problems, not two names for one: the iterated chain's
    # targets and marked sets do not coincide with the single hash's.
    single = LMOtsChainSpec(10, 1)
    assert spec._target != single._target
    assert spec.marked_set() != single.marked_set()
    assert spec.report()["chain_convention"] == "iterated_chain"
    assert single.report()["chain_convention"] == "single_hash"


def test_an_unreachable_target_is_refused_rather_than_yielding_an_empty_search():
    """``M = 0`` is refused at construction, naming the reason instead of failing much later."""
    spec = LMOtsChainSpec(8)
    reachable = {corpus_chain(8, x) for x in range(256)}
    unreachable = next(v for v in range(256) if v not in reachable)
    with pytest.raises(ValueError, match="marked set would be empty"):
        LMOtsChainSpec(8, target=unreachable)


def test_a_missing_first_peak_is_none_rather_than_stopiteration():
    """The upstream ``next(...)`` had no default; a window without a turnover reports None.

    Two windows that raised upstream, and they are the two that happen in practice. An empty window
    is the degenerate one. The other is the one that matters: a window that stops before the peak,
    where the curve rises monotonically for every step it takes — the shape a fixed
    ``iteration_range`` produces, and the shape that looks like a result. At ``n = 10`` the optimum
    is ``k = 12``, so a window ending at 2 contains no turnover at all; the curve says so instead of
    the run dying, and the report still carries the optimum it did not reach.
    """
    spec = LMOtsChainSpec(10)
    curve = spec.grover_curve(max_iterations=0)
    assert curve["k_first_peak"] is None
    assert curve["k_first_peak_closed_form"] is None
    assert curve["p_at_k_first_peak"] is None

    truncated = spec.grover_curve(max_iterations=2)
    assert truncated["k_predicted"] == 12
    assert truncated["k_first_peak"] is None
    assert truncated["k_first_peak_closed_form"] is None

    # At a window the peak is inside, it is there and it is the closed form's.
    full = spec.grover_curve()
    assert full["k_first_peak"] is not None
    assert abs(full["k_first_peak"] - full["k_predicted"]) <= 1


@pytest.mark.parametrize("n_bits", (8, 10))
def test_width_and_the_predicate_contract(n_bits):
    """``n_search + 2`` wide, both lowerings agreeing with the marked set, sandwich exact."""
    spec = LMOtsChainSpec(n_bits)
    assert spec.search_width() == n_bits
    assert not spec.supports_arithmetic_lowering
    for lowering in (Lowering.TRUTH_TABLE, Lowering.ARITHMETIC):
        assert spec.ancilla_width(lowering) == 1
        assert oracle_width(spec, lowering) == n_bits + 2
        assert_predicate_matches_spec(spec, lowering)
        predicate = spec.build_predicate(lowering)
        assert predicate.is_classically_simulable()
        assert predicate.num_qubits - 1 == spec.search_width() + 1


def test_the_truth_table_lowering_is_the_base_build_plus_one_controlled_x():
    """The relation's answer is the base build's, moved into the flag by a single gate.

    Asserted structurally rather than by gate count so that a change to the base build moves both
    and the two cannot drift: the spec's gate list is the base list, then one ``cx``.
    """
    spec = LMOtsChainSpec(10)
    predicate = spec.build_predicate(Lowering.TRUTH_TABLE)
    base = spec._build_truth_table()
    assert predicate.gates[:-1] == base.gates
    tail = predicate.gates[-1]
    assert tail.name is GateName.CX
    assert tail.qubits == (spec.search_width(), spec.search_width() + 1)


def test_measured_curve_matches_the_closed_form_and_the_half_power_law():
    """The corpus's S1-011 assertions, at widths it did not measure.

    Three things at once, because they are three views of one claim: the measured first peak is the
    predicted optimum, the success probability at that optimum is the closed form's to nine places,
    and ``log2(k)`` grows like ``n / 2`` across the sweep.

    The slope is the assertion worth a word about the ladder. The corpus makes it over
    ``(8, 10, 12, 14)``, where this spec's seeded draws give ``M = 1, 4, 1, 3`` — the marked-set size
    is not held constant across the ladder and cannot be, so ``k`` moves with ``M`` as well as with
    ``n`` and the measured slope comes out at 0.4439 against a tolerance of ±0.06. Five widths give
    0.4701 and six give 0.4819: the deviation shrinks as the ladder lengthens, which is what a
    ``sqrt(N / M)`` law sampled at varying ``M`` does. Six is used here so the tolerance is not the
    only thing standing between the assertion and the fluctuation, and ``k`` itself matches the
    closed form exactly at every one of the six — the deviation is in the fitted slope, not in the
    curve.
    """
    ladder = (8, 10, 12, 14, 16, 18)
    curves = [LMOtsChainSpec(n).grover_curve() for n in ladder]
    for curve in curves:
        assert curve["k_first_peak"] is not None, curve
        assert abs(curve["k_first_peak"] - curve["k_predicted"]) <= 1, curve
        assert curve["p_at_k_predicted"] == pytest.approx(curve["p_predicted"], abs=1e-9)

    xs = [float(c["n_search"]) for c in curves]
    ys = [math.log2(c["k_first_peak"]) for c in curves]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    assert slope == pytest.approx(0.5, abs=0.06), f"measured slope {slope:.4f}"


def test_the_report_pins_the_convention_it_used():
    """No report is quotable without the semantics behind it."""
    for chain_length, expected in ((1, "single_hash"), (4, "iterated_chain")):
        report = LMOtsChainSpec(10, chain_length).report()
        assert report["chain_convention"] == expected
        assert report["chain_length"] == chain_length
        assert report["work_qubits"] == 1
        assert report["n_marked"] == len(LMOtsChainSpec(10, chain_length).marked_set())


# -----------------------------------------------------------------------------------------------
# ModeBKeyMapSpec
# -----------------------------------------------------------------------------------------------


def dense_matrix(spec: ModeBKeyMapSpec, e: int) -> np.ndarray:
    """Equation ``e`` as a full ``n_vars x n_vars`` matrix, built from the stored triangle.

    The upper triangle is where the corpus keeps it; nothing is symmetrised and nothing is halved,
    which is the whole content of the convention being tested.
    """
    a = np.zeros((spec.n_vars, spec.n_vars), dtype=np.int64)
    for i in range(spec.n_vars):
        row = spec._rows[e][i]
        for j in range(i + 1, spec.n_vars):
            if (row >> j) & 1:
                a[i][j] = 1
    return a


@pytest.mark.parametrize("mode,n", [(KeyMapMode.A, 3), (KeyMapMode.B, 2)])
def test_quadratic_form_convention_measured_against_the_framework_gate(mode, n):
    """The spec's map, the dense-matrix reading, and ``QuadraticFormGate`` agree on every input.

    Re-measured here rather than taken from the API probe because this spec's lowering *is* the
    upper-triangle reading: if the framework gate were the triangular reading instead, the map the
    corpus stores and the circuit this project counts would be two different functions, and every
    gate count derived from it would describe a relation nobody asked about.

    Both equations are checked at six variables; at eight, one is, because the second equation of a
    map is an independent draw through the same construction and the wider register already costs
    four times the statevector work per equation for the same convention.
    """
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import QuadraticFormGate
    from qiskit.quantum_info import Statevector

    spec = ModeBKeyMapSpec(n, mode, n_outputs=2)
    for e in range(2 if spec.n_vars <= 6 else 1):
        a = dense_matrix(spec, e)
        b = np.array([(spec._lin[e] >> i) & 1 for i in range(spec.n_vars)], dtype=np.int64)
        c = int(spec._const[e])
        gate = QuadraticFormGate(1, a.tolist(), b.tolist(), c)
        assert gate.num_qubits == spec.n_vars + 1

        for x in range(1 << spec.n_vars):
            bits = np.array([(x >> i) & 1 for i in range(spec.n_vars)], dtype=np.int64)
            expected = int((bits @ a @ bits + bits @ b + c) % 2)

            circuit = QuantumCircuit(spec.n_vars + 1)
            for q in range(spec.n_vars):
                if (x >> q) & 1:
                    circuit.x(q)
            circuit.append(gate, range(spec.n_vars + 1))
            state = Statevector(circuit)
            framework = int(np.argmax(np.abs(state.data))) >> spec.n_vars

            assert framework == expected, f"framework gate disagrees at x={x}, equation {e}"
            assert (spec._evaluate(x) >> e) & 1 == expected, f"spec map disagrees at x={x}"


def test_the_api_probe_still_finds_the_gate_well_behaved():
    """The frozen probe's verdict on the gate, asserted here because this spec depends on it."""
    from grover_emulator.utils.api_probe import check_quadratic_form_convention

    result = check_quadratic_form_convention()
    assert result.ok, result.detail
    assert "full matrix" in result.detail


@pytest.mark.parametrize(
    "mode,n,expected_vars",
    [(KeyMapMode.A, 2, 4), (KeyMapMode.A, 3, 6), (KeyMapMode.B, 2, 8), (KeyMapMode.B, 3, 12)],
)
def test_width_rule(mode, n, expected_vars):
    """``2n + 2`` in mode A, ``4n + 2`` in mode B, for the single-equation map the rule describes."""
    spec = ModeBKeyMapSpec(n, mode)
    assert spec.search_width() == expected_vars
    assert spec.n_vars == (2 * n if mode is KeyMapMode.A else 4 * n)
    assert oracle_width(spec, Lowering.TRUTH_TABLE) == expected_vars + 2
    assert oracle_width(spec, Lowering.ARITHMETIC) == expected_vars + 2


@pytest.mark.parametrize("mode", [KeyMapMode.A, KeyMapMode.B])
def test_predicate_matches_the_marked_set_in_both_lowerings(mode):
    """The compiled map and the lookup table against the map's own marked set, exhaustively."""
    spec = ModeBKeyMapSpec(2, mode)
    assert_predicate_matches_spec(spec, Lowering.TRUTH_TABLE)
    assert_predicate_matches_spec(spec, Lowering.ARITHMETIC)

    # The tagged set is the preimage of the target, computed from the map's own evaluation.
    want = frozenset(x for x in range(1 << spec.n_vars) if spec._evaluate(x) == spec._target)
    assert spec.marked_set() == want


@pytest.mark.parametrize("n_outputs", (1, 2, 3))
def test_the_compiled_lowering_costs_what_the_equations_imply(n_outputs):
    """Every linear term one controlled X, every monomial one Toffoli, and nothing else.

    The report quotes an equation's cost as a gate count; this is the assertion that the cost model
    and the circuit are the same object, which is what makes the extrapolation attached to something
    that computes the right function.
    """
    spec = ModeBKeyMapSpec(3, KeyMapMode.A, n_outputs=n_outputs)
    predicate = spec.build_predicate(Lowering.ARITHMETIC)
    counts = predicate.counts()

    linear = sum(spec.variable_terms(e)["linear_terms"] for e in range(n_outputs))
    monomials = sum(spec.variable_terms(e)["monomials"] for e in range(n_outputs))
    conjugations = sum(spec.variable_terms(e)["constant"] for e in range(n_outputs))
    target_x = sum(
        1 for e in range(n_outputs) if not (spec._target >> e) & 1
    )

    assert counts.get("x", 0) == conjugations + target_x

    # One controlled X per linear term, one Toffoli per monomial, and one more gate folding the
    # work register into the flag — the smallest gate that fits the number of equations, so the
    # fold is counted under the same name as a monomial when there are two of them.
    fold = {1: "cx", 2: "ccx"}.get(n_outputs, "mcx")
    expected = {"cx": linear, "ccx": monomials, "mcx": 0}
    expected[fold] += 1
    for name, want in expected.items():
        assert counts.get(name, 0) == want, f"{name}: {counts.get(name, 0)} != {want}"
    assert predicate.num_qubits == spec.search_width() + n_outputs + 1


def test_expanding_the_map_thins_the_tagged_set():
    """One equation tags a large fraction of the register; more equations tag less of it.

    This is why the equation count is a parameter rather than a constant. A one-equation map over
    ``F2`` tags about half its register — the default eight-variable map tags 120 of 256, and the
    fraction over a sweep of seeds and widths runs 0.25 to 0.625, tightening towards 0.5 as the
    register widens — which is a relation Grover cannot amplify. The report says so through
    ``marked_fraction`` rather than leaving a caller to discover it from a flat curve. Eight
    equations on the same register leave two candidates.
    """
    thin = ModeBKeyMapSpec(4, KeyMapMode.A, n_outputs=1)
    fat = ModeBKeyMapSpec(4, KeyMapMode.A, n_outputs=8)
    assert thin.space().n_marked == 120
    assert thin.space().marked_fraction > 0.3
    assert fat.space().n_marked == 2
    assert fat.space().n_marked < thin.space().n_marked
    assert oracle_width(fat, Lowering.ARITHMETIC) == fat.search_width() + 8 + 1
    assert oracle_width(fat, Lowering.TRUTH_TABLE) == fat.search_width() + 2


def test_the_report_pins_the_mode_and_the_map_shape():
    report = ModeBKeyMapSpec(3, KeyMapMode.B).report()
    assert report["mode"] == "B"
    assert report["n_variables"] == 12
    assert report["n_outputs"] == 1
    assert report["n_marked"] == len(ModeBKeyMapSpec(3, KeyMapMode.B).marked_set())
    assert report["equation_cost_per_output"]["monomials"] <= report["n_variables"] ** 2


# -----------------------------------------------------------------------------------------------
# the contract both of them are held to
# -----------------------------------------------------------------------------------------------


def test_both_predicates_are_dirty_by_construction_so_the_sandwich_is_the_contract():
    """The work qubits are not uncomputed, and the negative keeps that from becoming a claim.

    ``assert_ancillas_return_clean`` is the assertion for a predicate that is clean on its own.
    Neither of these claims that: their work qubits hold the relation's answer, which is the point
    of having them, and the oracle sandwich's exact inverse is what clears them — which is why
    ``assert_predicate_matches_spec`` ends in a sandwich check rather than a cleanness one. Asserting
    the negative here means a later change that started uncomputing the work qubits would surface as
    a failing test, at which point the question is whether the spec should be claiming cleanness,
    not whether to relax the test.
    """
    cases = (
        (LMOtsChainSpec(8), Lowering.TRUTH_TABLE),
        (ModeBKeyMapSpec(2, KeyMapMode.A), Lowering.ARITHMETIC),
    )
    for spec, lowering in cases:
        predicate = spec.build_predicate(lowering)
        with pytest.raises(AssertionError, match="left ancillas dirty"):
            assert_ancillas_return_clean(predicate, spec.search_width())


def test_the_phase_oracle_over_each_predicate_marks_exactly_the_marked_set():
    """The end the predicates exist for: ``diag((-1)**f)`` on the search register, ancillas clean.

    A predicate that agreed with its marked set and whose sandwich was the identity would still be
    useless if the sandwich the *oracle* builds did not put the phase on the right states, and that
    is a different circuit: the predicate's two halves with a Z on the flag between them. This is
    therefore the integration assertion rather than a fourth restatement of the third — it is what
    the sweep's success curve actually runs.
    """
    for spec in (LMOtsChainSpec(8), ModeBKeyMapSpec(2, KeyMapMode.A), ModeBKeyMapSpec(2, KeyMapMode.B)):
        for lowering in (Lowering.TRUTH_TABLE, Lowering.ARITHMETIC):
            oracle = build_phase_oracle(spec, lowering)
            assert oracle.num_qubits == oracle_width(spec, lowering)
            assert_oracle_is_diagonal(oracle, spec.search_width(), spec.marked_set())
