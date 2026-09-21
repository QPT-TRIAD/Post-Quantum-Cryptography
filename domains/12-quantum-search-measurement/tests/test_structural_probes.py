"""The probes, tested for being *discriminative* rather than merely quiet.

A probe suite that never fires is indistinguishable from a broken one, so the centre of this file is
the positive control: a marked set with a planted XOR-period, which the probes must detect and must
recover *exactly*. Only against that does the negative control mean anything, and the negative control
in turn has to be built carefully: a control that quietly carries structure of its own is not a
control. See :func:`test_the_negative_control_fixture_carries_no_period`, which pins the session
fixture's eight marked values, the absence of any period closing them, and the decisive form of both
probes' silence on it.

Three further properties are asserted because a probe's silence is only interpretable if they hold:
the sample count behind it, the reason it did not fire (a refuted candidate is not the same finding
as a spanned register), and the caveat that says what silence at ``n = 8`` can and cannot support.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from grover_emulator.analysis.structural_probes import (
    MEASURED,
    NOT_RUN,
    STRUCTURE_CAVEAT_TEMPLATE,
    ProbeResult,
    qft_period_probe,
    run_probes,
    simon_style_probe,
    structure_caveat,
    verify_period,
)
from grover_emulator.analysis.success_probability import (
    search_register_probabilities,
    statevector_of,
)
from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.circuits.phase_oracle import build_phase_oracle, oracle_width
from grover_emulator.problem.oracle_spec import (
    HiddenPeriodOracleSpec,
    Lowering,
    RandomControlOracleSpec,
)
from reference_statevector import ReferenceStatevector

# Periods with the low bit clear, which is the construction's requirement, at a register where each
# is a genuine period rather than a degenerate one. 0b10101010 = 170 is included because it is the
# widest period this register admits, and a probe that resolves only small periods is a probe that
# would miss a long one.
PLANTED_PERIODS = (0b10, 0b100, 0b1000, 0b1100, 0b100000, 0b10101010)

# Enough samples that a random control is refuted at the level of "the sampled support is the whole
# space". See test_negative_control_is_decisive: at the default 64 the same probe is silent for a
# weaker reason, which is the distinction the whole file turns on.
DECISIVE_SAMPLES = 4000


@pytest.fixture(scope="module")
def backend() -> ReferenceStatevector:
    return ReferenceStatevector()


@pytest.fixture(scope="module")
def random_control() -> RandomControlOracleSpec:
    """A negative control at M = 8, n = 8, seed 1 — the shape the session ``random_spec`` uses too.

    The size is the point rather than a matter of taste. At two marked values the set is closed under
    ``x -> x ^ (a ^ b)`` whatever the values are, so it has a genuine XOR-period and a probe firing on
    it would be correct rather than broken; that arithmetic is recorded in
    ``tests/test_analysis.py``. Seed 1 is drawn here so that the tests below do not rest on the
    session fixture's seed.
    """
    return RandomControlOracleSpec(n_qubits=8, n_marked=8, seed=1)


def _hadamard_layer(width: int, total_qubits: int) -> GateList:
    """``H`` on the low ``width`` qubits. Built here from the IR so the test constructs the circuit
    the probe's docstring names, rather than reaching into the probe for it."""
    circuit = GateList(total_qubits)
    for qubit in range(width):
        circuit.append(GateName.H, qubit)
    return circuit


# -----------------------------------------------------------------------------------------------
# the positive control: the probes must detect planted structure
# -----------------------------------------------------------------------------------------------


def test_positive_control_fires_on_both_probes(hidden_period_spec, backend):
    """The session positive control — n = 8, planted period 0b100 — is detected and recovered.

    This is the test that makes every silence elsewhere in this file worth something.
    """
    results = run_probes(hidden_period_spec, backend)
    assert [result.probe for result in results] == ["simon_style", "qft_period"]
    for result in results:
        assert result.status == MEASURED
        assert result.fired is True, result.detail
        assert result.period_verified is True
        assert result.candidate_period == 0b100
        assert result.n_qubits == 8
        assert "fired" in result.detail


@pytest.mark.parametrize("period", PLANTED_PERIODS)
def test_planted_periods_are_recovered_exactly(period, backend):
    """Every planted period is read back as itself, by both probes, with no candidates to spare.

    Recovering *a* period would be too weak a claim: the probes are asked to name ``s`` exactly, and
    a candidate that merely happens to be verified would pass a weaker test.
    """
    spec = HiddenPeriodOracleSpec(n_qubits=8, period=period, seed=11)
    for result in run_probes(spec, backend):
        assert result.fired is True, f"{result.probe} missed the planted period {period:#b}"
        assert result.candidate_period == period


def test_a_wider_register_still_resolves_the_period(backend):
    """n = 10 with a two-bit planted period, to show the recovery is not a width-eight accident."""
    spec = HiddenPeriodOracleSpec(n_qubits=10, period=0b11000, seed=5)
    results = run_probes(spec, backend)
    assert [result.candidate_period for result in results] == [0b11000, 0b11000]
    assert all(result.fired and result.n_qubits == 10 for result in results)


def test_the_sampled_support_argument_holds_exactly(backend):
    """Where the probes' silence comes from, stated as the algebraic fact it is.

    Both circuits return outcomes supported on the orthogonal complement of the period: for a marked
    set closed under ``x -> x ^ s``, each coset's two members contribute opposite signs and cancel at
    every ``y`` with ``y . s = 1``. The assertion is an exact zero, computed from the statevector,
    rather than a small number — a probe built on a cancellation that does not quite happen would
    otherwise pass every statistical test here while meaning nothing.
    """
    spec = HiddenPeriodOracleSpec(n_qubits=8, period=0b100, seed=11)
    width = spec.search_width()
    total = width + spec.ancilla_width(Lowering.TRUTH_TABLE) + 1

    predicate = _hadamard_layer(width, total)
    predicate.extend(spec.build_predicate(Lowering.TRUTH_TABLE))
    predicate.extend(_hadamard_layer(width, total))

    spectrum = _hadamard_layer(width, total)
    spectrum.extend(build_phase_oracle(spec, Lowering.TRUTH_TABLE))
    spectrum.extend(_hadamard_layer(width, total))

    wrong = np.array(
        [bin(y & spec.period).count("1") & 1 for y in range(1 << width)], dtype=bool
    )
    assert wrong.any() and not wrong.all()

    for circuit in (predicate, spectrum):
        probabilities = search_register_probabilities(statevector_of(backend, circuit), width)
        assert float(probabilities.sum()) == pytest.approx(1.0, abs=1e-12)
        # Exactly zero on y with y.s = 1, and the great majority of the mass inside the complement.
        assert float(probabilities[wrong].sum()) < 1e-15
        assert float(probabilities[~wrong].sum()) > 0.99


# -----------------------------------------------------------------------------------------------
# the negative control: the probes must not fire on an unstructured oracle
# -----------------------------------------------------------------------------------------------


def test_negative_control_is_decisive(random_control, backend):
    """M = 8 at n = 8 over several seeds: no firing, and the strong form of silence.

    The strong form is ``nullity == 0`` — the sampled constraints span the register, so no
    non-trivial period is consistent with the measurement at all. Anything weaker would leave open
    that the probe was silent because it did not look hard enough.
    """
    for seed in range(1, 9):
        spec = RandomControlOracleSpec(n_qubits=8, n_marked=8, seed=seed)
        for result in run_probes(spec, backend, samples=DECISIVE_SAMPLES):
            assert result.fired is False, f"{result.probe} fired on random control seed {seed}"
            assert result.rank == result.n_qubits
            assert result.nullity == 0
            assert result.candidate_period is None
            assert "spanned the full register" in result.detail


def test_negative_control_is_silent_at_the_default_sample_count(random_control, backend):
    """At the default budget the same oracle is silent for a weaker reason, and says which.

    This is not the same finding as the test above and the probe distinguishes them in words: a
    refuted candidate means the samples were too few, which is a statement about the probe, whereas a
    spanned register is a statement about the oracle.
    """
    results = run_probes(RandomControlOracleSpec(n_qubits=8, n_marked=8, seed=1), backend)
    for result in results:
        assert result.fired is False
        assert result.samples == max(4 * result.n_qubits, 64)
        assert result.nullity > 0
        assert "too few" in result.detail and "refuted" in result.detail


def test_default_sample_count_is_a_derived_rule_not_a_constant(backend):
    spec = RandomControlOracleSpec(n_qubits=8, n_marked=8, seed=1)
    result = simon_style_probe(spec, backend)
    assert result.samples == 64
    wider = simon_style_probe(HiddenPeriodOracleSpec(n_qubits=10, period=0b11000, seed=5), backend)
    assert wider.samples == 40 or wider.samples == 64  # max(4 * n, 64) at n = 10
    assert wider.samples == max(4 * 10, 64)


def test_the_negative_control_fixture_carries_no_period(random_spec, backend):
    """The session ``random_spec`` is a control because it has no period — measured, not assumed.

    The size is not a matter of taste. Two marked values is not a weak control but a broken one: for
    any ``{a, b}`` the set is closed under ``x -> x ^ (a ^ b)``, which maps each of the two onto the
    other, so a two-element control has a genuine XOR-period and a probe that fires on it is right —
    which is why the fixture marks eight values rather than two. This test pins both halves of what
    makes that work: the *algebra*, by checking every one of the 255 non-zero periods against
    :func:`~grover_emulator.analysis.structural_probes.verify_period`, and the *measurement*, by
    requiring ``nullity == 0``. That second half is the one worth stating twice: the sampled
    constraints span the whole register, so the silence is a fact about the oracle, where a bare
    ``fired is False`` would also be satisfied by drawing too few samples.
    """
    marked = random_spec.marked_set()
    n = random_spec.search_width()
    assert len(marked) >= 8, "a control this small is degenerate; see the arithmetic above"
    assert sorted(marked) == [7, 32, 33, 125, 149, 152, 181, 200]
    assert not any(verify_period(marked, n, s) for s in range(1, 1 << n))

    results = run_probes(random_spec, backend, samples=DECISIVE_SAMPLES)
    assert [result.probe for result in results] == ["simon_style", "qft_period"]
    for result in results:
        assert result.fired is False, result.detail
        assert result.nullity == 0
        assert result.rank == n
        assert result.candidate_period is None
        assert "spanned the full register" in result.detail


def test_a_three_element_control_still_has_no_reason_to_fire(backend):
    """Three values is enough to break the accidental closure, which is why M >= 4 is the floor."""
    spec = RandomControlOracleSpec(n_qubits=8, n_marked=3, seed=1)
    marked = sorted(spec.marked_set())
    assert len(marked) == 3
    for other in marked[1:]:
        assert not verify_period(spec.marked_set(), 8, marked[0] ^ other)
    assert not any(
        result.fired for result in run_probes(spec, backend, samples=DECISIVE_SAMPLES)
    )


# -----------------------------------------------------------------------------------------------
# the worked instance: a sample-limited silence, and the count that makes it a finding
# -----------------------------------------------------------------------------------------------


def test_qlwr_silence_is_sample_limited_at_the_default_budget(qlwr_spec, backend):
    """The real instance, at the default sample count, produces the *weak* silence.

    That is the honest result at 64 samples and it is worded as such. The point of asserting it here
    is that the stronger claim in the next test needs a sample count 3000 times larger, and the
    difference between the two would be invisible if both rendered as "not fired".
    """
    for result in run_probes(qlwr_spec, backend):
        assert result.fired is False
        assert result.nullity == qlwr_spec.search_width()
        assert result.rank == 0
        assert "too few" in result.detail


def test_qlwr_silence_is_decisive_at_a_large_sample_count(qlwr_spec, backend):
    """With enough samples the search register is spanned and no period survives at all.

    Still a statement about ``n = 12``, which is what the caveat travelling with the result says.
    """
    for result in run_probes(qlwr_spec, backend, samples=200000):
        assert result.fired is False
        assert result.rank == qlwr_spec.search_width()
        assert result.nullity == 0
        assert "spanned the full register" in result.detail


# -----------------------------------------------------------------------------------------------
# refusals: named, recorded, and never rendered as a result
# -----------------------------------------------------------------------------------------------


def test_arithmetic_lowering_refusals_name_their_reason(qlwr_spec, backend):
    """Both probes refuse the arithmetic lowering, and each says what stopped it.

    A refusal that returned "not fired" without a reason would be indistinguishable from the negative
    result, which is exactly the confusion this distinction exists to prevent.
    """
    results = run_probes(qlwr_spec, backend, lowering=Lowering.ARITHMETIC)
    assert len(results) == 2
    simon = next(result for result in results if result.probe == "simon_style")
    qft = next(result for result in results if result.probe == "qft_period")
    assert simon.status == NOT_RUN and qft.status == NOT_RUN
    assert simon.fired is False and qft.fired is False
    assert "ancilla" in simon.reason
    # The ceiling message is built from the width accounting, so the number in it is the oracle's own
    # width and not a constant of the message. Asserted as the relation first and the literal second:
    # a stale literal would otherwise keep matching a width no circuit in this project has.
    assert "ceiling" in qft.reason
    assert str(oracle_width(qlwr_spec, Lowering.ARITHMETIC)) in qft.reason
    assert "50" in qft.reason
    for result in results:
        assert result.reason and result.caveat
        assert math.isfinite(result.statistic)
        assert result.to_dict()["provenance"] == NOT_RUN


def test_qft_probe_refuses_a_circuit_above_its_width_ceiling(backend):
    """The ceiling is a parameter, so the refusal can be exercised without the arithmetic lowering."""
    spec = HiddenPeriodOracleSpec(n_qubits=8, period=0b100, seed=11)
    result = qft_period_probe(spec, backend, max_total_qubits=8)
    assert result.status == NOT_RUN
    assert "ceiling" in result.reason
    assert result.fired is False


def test_simon_style_probe_refuses_a_codomain_that_is_not_ancilla_free(qlwr_spec, backend):
    result = simon_style_probe(qlwr_spec, backend, lowering=Lowering.ARITHMETIC)
    assert result.status == NOT_RUN
    assert "ancilla" in result.reason
    assert "truth-table" in result.reason


# -----------------------------------------------------------------------------------------------
# the mandatory caveat
# -----------------------------------------------------------------------------------------------


def test_every_result_carries_the_caveat(qlwr_spec, backend, hidden_period_spec):
    """A result without the limitation statement is a result nobody should quote.

    Checked on a firing result, a silent result and a refused result, because it is the firing one
    that is quoted and the silent one whose reading is the whole trap.
    """
    results = run_probes(qlwr_spec, backend)
    results += run_probes(hidden_period_spec, backend)
    results += run_probes(qlwr_spec, backend, lowering=Lowering.ARITHMETIC)
    assert len(results) == 6
    for result in results:
        assert result.caveat.strip()
        assert "n = 128" in result.caveat
        assert result.to_dict()["caveat"] == result.caveat
        if result.status == MEASURED:
            assert str(result.samples) in result.caveat
        else:
            # A refusal does not get the measured wording: there was no silence to qualify.
            assert "did not run" in result.caveat
            assert result.samples == 0


def test_the_caveat_is_mandatory_by_construction():
    """The field has no default and cannot be blank, so the statement cannot be left out."""
    with pytest.raises(TypeError):
        ProbeResult(probe="x", fired=False, statistic=0.0, n_qubits=4, detail="")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="caveat"):
        ProbeResult(probe="x", fired=False, statistic=0.0, n_qubits=4, detail="", caveat="   ")


def test_a_caveat_cannot_be_written_without_naming_the_width_it_was_measured_at():
    """The template names ``n = 128`` and the sample count, and both survive formatting."""
    text = structure_caveat(8, 64)
    assert "n = 128" in text and "n_search = 8" in text and "64" in text
    assert text.startswith(STRUCTURE_CAVEAT_TEMPLATE.split("{")[0])
    with_extra = structure_caveat(8, 64, "And a probe-specific limitation.")
    assert with_extra.endswith("And a probe-specific limitation.")


def test_inconsistent_results_are_refused_by_the_result_type():
    """The type refuses the combinations that would make a verdict unreadable.

    Each of these is a result that *could* be constructed and then rendered, which is why the
    refusals live in the dataclass rather than in the code that happens to build one.
    """
    base = dict(probe="x", statistic=0.0, n_qubits=4, detail="d", caveat="a caveat")
    with pytest.raises(ValueError, match="status"):
        ProbeResult(fired=False, status="maybe", **base)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="not have run"):
        ProbeResult(fired=True, status=NOT_RUN, reason="r", period_verified=True, **base)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no reason"):
        ProbeResult(fired=False, status=NOT_RUN, **base)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="statistic"):
        ProbeResult(probe="x", fired=False, statistic=float("nan"), n_qubits=4, detail="d", caveat="c")
    with pytest.raises(ValueError, match="verified period"):
        ProbeResult(fired=True, **base)  # type: ignore[arg-type]


# -----------------------------------------------------------------------------------------------
# determinism and the record shape the report reads
# -----------------------------------------------------------------------------------------------


def test_probes_are_deterministic_under_the_same_seed_parts(hidden_period_spec, backend):
    first = [result.to_dict() for result in run_probes(hidden_period_spec, backend)]
    second = [result.to_dict() for result in run_probes(hidden_period_spec, backend)]
    assert first == second
    reseeded = [result.to_dict() for result in run_probes(hidden_period_spec, backend, seed_parts=("b",))]
    assert [record["fired"] for record in reseeded] == [record["fired"] for record in first]


def test_probe_records_carry_the_keys_the_report_reads(hidden_period_spec, backend):
    for result in run_probes(hidden_period_spec, backend):
        record = result.to_dict()
        for key in ("probe", "fired", "statistic", "n_qubits", "detail", "caveat"):
            assert key in record
        assert record["provenance"] == MEASURED
        assert record["total_qubits"] == result.circuit_width >= record["n_qubits"]


def test_rank_and_nullity_account_for_the_whole_register(random_control, backend):
    """``rank + nullity == n`` on every measured result: the sampled constraints are accounted for."""
    for result in run_probes(random_control, backend, samples=DECISIVE_SAMPLES):
        assert result.rank + result.nullity == result.n_qubits


def test_a_firing_result_never_reports_zero_candidates(backend):
    """A firing has to come from a candidate the marked set verified, so the statistic is positive."""
    spec = HiddenPeriodOracleSpec(n_qubits=8, period=0b1000, seed=11)
    for result in run_probes(spec, backend):
        assert result.fired and result.statistic > 0 and result.candidate_period == 0b1000
        assert "survived the closure check" in result.detail
