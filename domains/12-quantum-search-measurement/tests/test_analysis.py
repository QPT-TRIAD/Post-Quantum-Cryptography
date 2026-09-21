"""The analysis layer end to end: two engines compared, four questions answered, one report.

Three things are established here that the per-module tests cannot establish on their own.

1. **The test-double statevector engine is not trusted on its own word.**
   :mod:`tests.reference_statevector` runs every circuit the other tests measure, so if it were wrong
   every "measured" number in this suite would be wrong in the same direction. It is therefore
   compared against Qiskit's ``Operator`` on a circuit containing every gate in the IR, and the
   success curve it produces is compared against the curve produced through Qiskit's ``Statevector``
   on the same gate lists.
2. **Measured and extrapolated never blend.** The scaling module's output keeps them in separate
   lists with separate provenance, and the fitted numbers are checked to be recoverable exactly when
   the data is a power law, so the fit is known to be arithmetic rather than curve-shaped noise.
3. **The layer's outputs are the report's inputs.** The last test assembles a results mapping from
   the analysis objects — as a run would — and renders the report, asserting that each section
   appears with its provenance attached rather than as a bare number.
"""

from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit.library import (
    CCXGate,
    CXGate,
    HGate,
    MCXGate,
    SGate,
    SdgGate,
    TGate,
    TdgGate,
    UnitaryGate,
    XGate,
)
from qiskit.quantum_info import Statevector

from grover_emulator.analysis.classical_baseline import (
    BASELINE_CAVEAT,
    classical_baseline,
    expected_queries,
    measure_classical_search,
    per_query_cost,
    worst_case_queries,
)
from grover_emulator.analysis.scaling_extrapolation import (
    EXTRAPOLATION_CAVEAT_TEMPLATE,
    MEASURED,
    MIN_FIT_POINTS,
    MeasuredPoint,
    ScalingError,
    fit_depth_scaling,
    fit_gate_scaling,
    measured_points_from_sweep,
    predict_gate_count,
    sweep_provenance,
)
from grover_emulator.analysis.structural_probes import (
    qft_period_probe,
    run_probes,
    simon_style_probe,
    verify_period,
)
from grover_emulator.analysis.success_probability import (
    measured_success_probability,
    statevector_of,
    success_curve,
)
from grover_emulator.circuits.grover_circuit_builder import (
    build_grover_circuit,
    optimal_iterations,
)
from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.problem.oracle_spec import Lowering, RandomControlOracleSpec
from grover_emulator.reporting.report_generator import EXTRAPOLATED, render_report
from reference_statevector import ReferenceStatevector

SINGLE_QUBIT_GATES = {
    GateName.H: HGate,
    GateName.X: XGate,
    GateName.S: SGate,
    GateName.SDG: SdgGate,
    GateName.T: TGate,
    GateName.TDG: TdgGate,
}


def to_qiskit(circuit: GateList) -> QuantumCircuit:
    """The same gate list as a Qiskit circuit, gate for gate.

    Deliberately a transcription rather than a translation layer: one IR gate becomes one Qiskit
    instruction, so the comparison tests the two engines' *semantics* and not a compiler's. The one
    place a decomposition is needed is ``MCZ``, which this Qiskit has no gate for — ``H . MCX . H``
    on one of the qubits is exact for any choice of that qubit, and the phase is not a global one.
    """
    qc = QuantumCircuit(circuit.num_qubits)
    for gate in circuit.gates:
        qubits = list(gate.qubits)
        if gate.name in SINGLE_QUBIT_GATES:
            qc.append(SINGLE_QUBIT_GATES[gate.name](), qubits)
        elif gate.name is GateName.CX:
            qc.append(CXGate(), qubits)
        elif gate.name is GateName.CCX:
            qc.append(CCXGate(), qubits)
        elif gate.name is GateName.MCX:
            qc.append(MCXGate(len(qubits) - 1), qubits)
        elif gate.name is GateName.MCZ:
            target, controls = qubits[-1], qubits[:-1]
            qc.append(HGate(), [target])
            if controls:
                qc.append(MCXGate(len(controls)), controls + [target])
            else:
                qc.append(XGate(), [target])
            qc.append(HGate(), [target])
        elif gate.name is GateName.PERM:
            table = [int(value) for value in gate.params[0]]
            dimension = 1 << len(qubits)
            matrix = np.zeros((dimension, dimension), dtype=complex)
            for source, destination in enumerate(table):
                matrix[destination, source] = 1.0
            qc.append(UnitaryGate(matrix), qubits)
        else:  # pragma: no cover - the IR has no other gate
            raise AssertionError(f"the adapter has no transcription for {gate.name!r}")
    return qc


class QiskitStatevector:
    """The independent engine, behind the one method the analysis layer needs."""

    name = "qiskit_statevector"

    def statevector(self, circuit: GateList) -> np.ndarray:
        return np.asarray(Statevector.from_instruction(to_qiskit(circuit)).data, dtype=complex)


@pytest.fixture(scope="module")
def backend() -> ReferenceStatevector:
    return ReferenceStatevector()


@pytest.fixture(scope="module")
def independent() -> QiskitStatevector:
    return QiskitStatevector()


# -----------------------------------------------------------------------------------------------
# the test double, checked against an independent construction
# -----------------------------------------------------------------------------------------------


def _every_gate_circuit() -> GateList:
    """One circuit containing every gate in the IR, including the least-used ones.

    ``PERM`` is here because no Grover path emits it and a gate the tests never exercise is a gate
    whose engine implementation is untested — which is exactly the state a test double must not be in
    when it is the thing producing every measured number.
    """
    circuit = GateList(4)
    circuit.append(GateName.H, 0).append(GateName.H, 1).append(GateName.H, 2)
    circuit.append(GateName.X, 3)
    circuit.append(GateName.CX, 0, 1)
    circuit.append(GateName.CCX, 0, 1, 2)
    circuit.append(GateName.MCX, 0, 1, 2, 3)
    circuit.append(GateName.MCZ, 0, 1, 2)
    circuit.append(GateName.S, 0).append(GateName.SDG, 1)
    circuit.append(GateName.T, 2).append(GateName.TDG, 3)
    circuit.append(GateName.PERM, 0, 1, params=([0, 2, 3, 1],))
    circuit.append(GateName.MCZ, 0, 1, 2, 3)
    circuit.append(GateName.MCX, 0, 1, 2, 3)
    circuit.append(GateName.H, 3).append(GateName.CX, 2, 3)
    return circuit


def test_reference_engine_agrees_with_qiskit_on_every_gate(backend, independent):
    """The double's amplitudes match Qiskit's on a circuit built from the whole gate set."""
    circuit = _every_gate_circuit()
    reference = backend.statevector(circuit)
    expected = independent.statevector(circuit)
    assert float(np.max(np.abs(reference - expected))) < 1e-12
    # Non-trivial: a circuit whose output is a basis state would make a broken engine look correct.
    assert int(np.count_nonzero(np.abs(reference) > 1e-12)) > 4
    assert any(abs(amplitude.imag) > 1e-6 for amplitude in reference)


def test_reference_engine_agrees_with_qiskit_on_a_grover_circuit(backend, independent):
    """And on the circuit the analysis layer actually measures."""
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=1, seed=11)
    circuit = build_grover_circuit(spec, 3, Lowering.TRUTH_TABLE)
    assert float(
        np.max(np.abs(backend.statevector(circuit) - independent.statevector(circuit)))
    ) < 1e-12


def test_both_engines_produce_the_same_success_curve(backend, independent):
    """The curve the analysis layer reports does not depend on which engine measured it."""
    spec = RandomControlOracleSpec(n_qubits=5, n_marked=2, seed=4)
    through_reference = success_curve(spec, backend, iteration_range=range(0, 5))
    through_qiskit = success_curve(spec, independent, iteration_range=range(0, 5))
    for a, b in zip(through_reference.points, through_qiskit.points):
        assert a.measured == pytest.approx(b.measured, abs=1e-12)
    assert through_reference.peak_measured.iteration == through_qiskit.peak_measured.iteration


def test_both_engines_probe_the_same_oracle_the_same_way(backend, independent, hidden_period_spec):
    from_reference = simon_style_probe(hidden_period_spec, backend)
    from_qiskit = simon_style_probe(hidden_period_spec, independent)
    assert from_reference.fired == from_qiskit.fired is True
    assert from_reference.candidate_period == from_qiskit.candidate_period == 0b100


class _ResultEnvelope:
    """The shape the project's own engines return: the amplitudes inside a result object.

    Modelled on :class:`grover_emulator.backends.base_backend.BackendResult`, which carries the IR
    accounting beside the statevector. The analysis layer unwraps that envelope rather than requiring
    a wrapper, so a run can hand an engine straight to :func:`success_curve`. The fields the analysis
    layer ignores are present here so that the test would notice if it started depending on one.
    """

    def __init__(self, statevector, num_qubits):
        self.statevector = statevector
        self.num_qubits = num_qubits
        self.method = "statevector"
        self.metrics = {"toffoli_count": 0, "ir_depth": 0, "t_count": 0}


class _EnvelopingEngine:
    def __init__(self, inner):
        self.inner = inner

    def run_statevector(self, circuit):
        return _ResultEnvelope(self.inner.statevector(circuit), circuit.num_qubits)


def test_an_engine_returning_a_result_object_is_unwrapped():
    """``run_statevector`` is accepted, and its envelope is unwrapped before validation.

    The engines in this project return the amplitudes inside a result object that also carries the
    circuit's accounting. Requiring a wrapper around that would put an adapter between the analysis
    layer and every engine, so the unwrapping lives in :func:`statevector_of` and is asserted here
    against a test double of the envelope — the real engines are tested where they live.
    """
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=1, seed=11)
    engine = _EnvelopingEngine(ReferenceStatevector())
    circuit = build_grover_circuit(spec, 3, Lowering.TRUTH_TABLE)
    assert statevector_of(engine, circuit).shape == (1 << circuit.num_qubits,)
    curve = success_curve(spec, engine, iteration_range=range(0, 3))
    assert curve.residuals["max_abs_residual"] < 1e-12


def test_the_reference_engine_refuses_a_circuit_wider_than_its_cap(backend):
    spec = RandomControlOracleSpec(n_qubits=30, n_marked=1, seed=1)
    circuit = build_grover_circuit(spec, 0, Lowering.TRUTH_TABLE)
    with pytest.raises(ValueError, match="capped"):
        backend.statevector(circuit)


# -----------------------------------------------------------------------------------------------
# the classical baseline
# -----------------------------------------------------------------------------------------------


def test_expected_and_worst_case_query_counts_are_exact():
    assert expected_queries(16, 1) == Fraction(17, 2)
    assert isinstance(expected_queries(16, 1), Fraction)
    assert worst_case_queries(16, 1) == 16
    assert expected_queries(4096, 1) == Fraction(4097, 2)
    assert worst_case_queries(4096, 1) == 4096
    with pytest.raises(ValueError):
        expected_queries(16, 0)
    with pytest.raises(ValueError):
        worst_case_queries(16, 17)


def test_measured_search_is_a_real_scan_and_is_reproducible():
    """The measured count is one draw from the distribution, never the expectation relabelled."""
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=3, seed=9)
    first = measure_classical_search(spec, ("test",))
    second = measure_classical_search(spec, ("test",))
    assert first == second
    assert first.found in spec.marked_set()
    assert first.queries == first.offset + 1
    assert 1 <= first.queries <= worst_case_queries(spec.space().n_items, spec.space().n_marked)
    # A search that examined every value exactly once, which is what a scan without replacement is.
    assert first.n_items == 1 << 6
    assert first.to_dict()["provenance"].startswith("measured")


def test_baseline_keeps_the_measured_count_and_the_exact_expectation_apart():
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=1, seed=9)
    baseline = classical_baseline(spec, ("test",))
    assert baseline.queries_expected == Fraction(65, 2)
    assert baseline.grover_iterations == 6  # floor(pi/4 * sqrt(64)) = floor(6.283)
    assert baseline.speedup_expected == Fraction(65, 2) / 6
    assert isinstance(baseline.speedup_expected, Fraction)
    record = baseline.to_dict()
    assert next(iter(record)) == "queries"
    assert record["queries"] == baseline.queries
    assert record["queries_provenance"].startswith("measured")
    assert record["queries_expected"] == str(Fraction(65, 2))
    assert record["queries_expected_provenance"].startswith("exact")
    assert record["caveat"] == BASELINE_CAVEAT


def test_baseline_caveat_says_it_is_exhaustive_search_and_not_the_best_attack():
    assert "exhaustive search" in BASELINE_CAVEAT
    assert "not the best known" in BASELINE_CAVEAT
    assert "structural probes" in BASELINE_CAVEAT


def test_worked_instance_speedup_is_the_exact_ratio(qlwr_spec):
    """The headline ratio for the worked instance, as an exact rational rather than a decimal.

    ``(N+1)/(M+1)`` is ``4097/2`` and the optimum is ``k_opt = 50``, so the speedup is exactly
    ``4097/100`` = 40.97. Reporting it as a float would put a rounding into the denominator of the
    project's cost claim for no reason.
    """
    baseline = classical_baseline(qlwr_spec, ("test",))
    assert baseline.n_items == 4096 and baseline.n_marked == 1
    assert baseline.queries_expected == Fraction(4097, 2)
    assert baseline.grover_iterations == 50
    assert baseline.speedup_expected == Fraction(4097, 100)
    assert float(baseline.speedup_expected) == pytest.approx(40.97)
    assert 1 <= baseline.queries <= 4096


def test_per_query_cost_is_counted_from_the_instances_own_parameters(qlwr_spec):
    instance = qlwr_spec.instance
    cost = per_query_cost(qlwr_spec)
    assert cost["applicable"] is True
    assert cost["elementary_operations"] == 3 * instance.m * instance.nu + 2 * instance.m
    assert set(cost) >= {"multiplications", "additions", "roundings", "provenance"}


def test_per_query_cost_is_refused_where_there_is_no_arithmetic_form():
    cost = per_query_cost(RandomControlOracleSpec(n_qubits=6, n_marked=1, seed=1))
    assert cost["applicable"] is False
    assert "lookup table" in cost["reason"]


def test_the_work_ratio_names_its_two_different_units(qlwr_spec):
    """The ratio is only computable where both halves exist: a per-query cost and a gate count."""
    with_count = classical_baseline(qlwr_spec, ("test",), oracle_gate_count=11634)
    assert with_count.total_grover_work == with_count.grover_iterations * 11634
    assert with_count.work_ratio is not None and with_count.work_ratio > 0
    assert "not a speedup" in with_count.to_dict()["work_ratio_note"]
    without = classical_baseline(qlwr_spec, ("test",))
    assert without.total_grover_work is None
    assert without.work_ratio is None
    assert "total_grover_work_ir_gates" not in without.to_dict()
    # And on a spec with no arithmetic form the classical half is missing, so neither ratio appears.
    lookup = classical_baseline(RandomControlOracleSpec(n_qubits=6, n_marked=1, seed=9), ("test",))
    assert lookup.total_classical_work is None
    assert lookup.work_ratio is None


def test_baseline_refuses_an_instance_grover_cannot_improve_on():
    """``k_opt = 0`` is not a smaller speedup, it is a search that is already over.

    Twelve of sixteen values marked gives ``floor(pi/4 * sqrt(16/12)) = 0``: a single classical query
    is already the better algorithm, and there is nothing for the comparison to be about.
    """
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=12, seed=1)
    assert optimal_iterations(spec) == 0
    with pytest.raises(ValueError, match="no iterations at all"):
        classical_baseline(spec, ("test",))


# -----------------------------------------------------------------------------------------------
# scaling: the fit, and the wall between measured and modelled
# -----------------------------------------------------------------------------------------------


def _synthetic_points(widths, gate_counts, depths=None):
    return [
        MeasuredPoint(
            n_search=width,
            gate_count=count,
            ir_depth=None if depths is None else depths[index],
        )
        for index, (width, count) in enumerate(zip(widths, gate_counts))
    ]


def test_a_power_law_is_recovered_exactly():
    """``gates = 7 * n**2`` comes back as exponent 2 and scale 7, so the fit is arithmetic."""
    widths = (8, 10, 12, 16)
    points = _synthetic_points(widths, [7 * width**2 for width in widths])
    fit = fit_gate_scaling(points, target_widths=(20,))
    assert fit.exponent == pytest.approx(2.0, abs=1e-9)
    assert fit.scale == pytest.approx(7.0, rel=1e-9)
    assert fit.rms_residual_log2 < 1e-9
    assert fit.r_squared == pytest.approx(1.0, abs=1e-9)
    assert fit.predictions[0].gate_count == pytest.approx(7 * 20**2, rel=1e-9)


def test_fit_refuses_fewer_points_than_it_can_be_contradicted_by():
    points = _synthetic_points((8, 10), (100, 200))
    with pytest.raises(ScalingError, match="no residual to inspect"):
        fit_gate_scaling(points)
    assert MIN_FIT_POINTS == 3


def test_fit_refuses_two_measurements_at_one_width():
    points = _synthetic_points((8, 8, 12), (100, 101, 200))
    with pytest.raises(ScalingError, match="repeat"):
        fit_gate_scaling(points)


def test_fit_refuses_a_point_that_was_never_run():
    """A refused sweep record has no gate count, and placing it in a fit would move the intercept."""
    record = {"n_search": 14, "status": "not run", "reason": "statevector would not fit", "gate_count": 0}
    with pytest.raises(ScalingError, match="not an input to a fit"):
        MeasuredPoint.from_record(record)
    with pytest.raises(ScalingError, match="no gate_count"):
        MeasuredPoint.from_record({"n_search": 8, "status": MEASURED})


def test_sweep_records_split_into_measured_points_and_counted_refusals():
    records = [
        {"n_search": 8, "status": MEASURED, "gate_count": 584, "ir_depth": 133},
        {"n_search": 10, "status": MEASURED, "gate_count": 1608, "ir_depth": 290},
        {"n_search": 12, "status": MEASURED, "gate_count": 3650, "ir_depth": 902},
        {"n_search": 14, "status": "not run", "reason": "memory", "gate_count": 0},
    ]
    assert len(measured_points_from_sweep(records)) == 3
    assert sweep_provenance(records) == {
        MEASURED: 3,
        "not run": 1,
        "measured_widths": [8, 10, 12],
        "refused_widths": [14],
    }


def test_measured_and_extrapolated_are_never_in_the_same_list():
    """The separation is structural: two lists, two provenance values, no shared iteration."""
    points = _synthetic_points((8, 10, 12), (584, 1608, 3650))
    fit = fit_gate_scaling(points, target_widths=(128, 256))
    record = fit.to_dict()
    assert {entry["provenance"] for entry in record["measured"]} == {MEASURED}
    assert {entry["provenance"] for entry in record["extrapolated"]} == {EXTRAPOLATED}
    assert [entry["n_search"] for entry in record["measured"]] == [8, 10, 12]
    assert [entry["n_search"] for entry in record["extrapolated"]] == [128, 256]
    # Every recorded measurement is the one that was built; every prediction carries the range it
    # came from, so a prediction cannot be quoted without the evidence behind it.
    assert [entry["gate_count"] for entry in record["measured"]] == [584, 1608, 3650]
    for entry in record["extrapolated"]:
        assert entry["measured_range"] == [8, 12]
        assert entry["n_measured_points"] == 3
        assert entry["inside_measured_range"] is False
        assert "n_search = 8..12" in entry["caveat"]


def test_the_fit_table_labels_every_number_with_its_own_provenance():
    points = _synthetic_points((8, 10, 12), (584, 1608, 3650))
    fit = fit_gate_scaling(points, target_widths=(128,))
    table = fit.describe()
    numeric = {key for key, value in table.items() if isinstance(value, (int, float))}
    assert numeric == {
        "measured_points_used",
        "extrapolated_exponent",
        "extrapolated_scale_per_width_power",
        "extrapolated_rms_residual_log2",
        "extrapolated_max_residual_log2",
        "extrapolated_r_squared",
        "extrapolated_factor_per_doubling_of_width",
        "extrapolated_gate_count_n_search_128",
    }
    assert table["measured_range_n_search"] == "8..12"
    assert table["extrapolated_gate_count_n_search_128"] == pytest.approx(
        fit.predictions[0].gate_count
    )
    assert EXTRAPOLATION_CAVEAT_TEMPLATE.format(
        n_points=3, lo=8, hi=12
    ) in table["caveat"]


def test_a_prediction_inside_the_measured_range_says_so():
    points = _synthetic_points((8, 10, 12), (584, 1608, 3650))
    fit = fit_gate_scaling(points)
    inside = predict_gate_count(fit, 10)
    outside = predict_gate_count(fit, 128)
    assert inside.inside_measured_range is True
    assert outside.inside_measured_range is False
    assert "was not simulated" in outside.caveat


def test_depth_is_fitted_from_measured_depth_only():
    """Depth and gate count are separate curves, so depth is never inferred from the count.

    The points here carry a depth that follows a cubic against a gate count that does not, so a
    module that fitted one from the other would return the wrong exponent rather than the right one
    by accident.
    """
    widths = (8, 10, 12, 16)
    points = _synthetic_points(
        widths,
        [7 * width**2 for width in widths],
        [2 * width**3 for width in widths],
    )
    fit = fit_depth_scaling(points, target_widths=(128,))
    assert "ir_depth" in fit.form
    assert fit.exponent == pytest.approx(3.0, abs=1e-9)
    assert fit.measured_range == (8, 16)
    with pytest.raises(ScalingError, match="IR depth"):
        fit_depth_scaling(_synthetic_points((8, 10, 12), (584, 1608, 3650)))


def test_fits_are_deterministic():
    points = _synthetic_points((8, 10, 12, 14), (584, 1608, 3650, 16708))
    first = fit_gate_scaling(points, target_widths=(128,)).to_dict()
    second = fit_gate_scaling(points, target_widths=(128,)).to_dict()
    assert first == second


# -----------------------------------------------------------------------------------------------
# the whole layer, into the report
# -----------------------------------------------------------------------------------------------


def _measured_sweep() -> list[dict]:
    """A real sweep: four widths, each actually built and counted, at the truth-table lowering.

    The lowering is recorded on every record because a gate count without its construction is not a
    measurement of anything in particular — the arithmetic lowering costs a different number at the
    same width, and the report must not read one as the other.
    """
    records = []
    for n_search in (8, 10, 12, 14):
        spec = RandomControlOracleSpec(n_qubits=n_search, n_marked=1, seed=7)
        circuit = build_grover_circuit(spec, optimal_iterations(spec), Lowering.TRUTH_TABLE)
        stats = circuit.to_dict()
        records.append(
            {
                "n_search": n_search,
                "n_qubits_truth_table": stats["num_qubits"],
                "n_qubits_arithmetic": stats["num_qubits"],
                "gate_count": stats["gate_count"],
                "ir_depth": stats["ir_depth"],
                "lowering": "truth_table",
                "status": MEASURED,
                "reason": "",
            }
        )
    return records


def test_the_layer_renders_into_a_report_with_its_provenance_intact(tmp_path, qlwr_spec, backend):
    """Every section of the report that this layer feeds, rendered from the layer's own output.

    The assertion that matters is the last group: the report has to show the measured curve, the
    probe caveat, the measured sweep rows and the extrapolated fit *as different things*. A report
    where a fitted gate count and a counted one appear in the same table would be the failure this
    whole layer is arranged to prevent.
    """
    curve = success_curve(qlwr_spec, backend, iteration_range=range(47, 53))
    probes = run_probes(qlwr_spec, backend)
    sweep = _measured_sweep()
    points = measured_points_from_sweep(sweep)
    fit = fit_gate_scaling(points, target_widths=(128,))
    per_iteration = sweep[2]["gate_count"] // optimal_iterations(
        RandomControlOracleSpec(n_qubits=12, n_marked=1, seed=7)
    )
    baseline = classical_baseline(qlwr_spec, ("report",), oracle_gate_count=per_iteration)

    results = {
        "run_id": "test-run",
        "kind": "experiment",
        "created_utc": "2026-01-01T00:00:00Z",
        "config_path": "config/default_experiment.yaml",
        "seed": 20260913,
        "spec": qlwr_spec.describe(),
        "instance": qlwr_spec.instance.describe(),
        "marked_set_size": curve.n_marked,
        "search_width": curve.search_width,
        "n_items": curve.n_items,
        "optimal_iterations": curve.optimal_iterations,
        "iteration_range": list(curve.iteration_range),
        "lowering": curve.lowering,
        "backend": {"name": backend.name, "n_qubits_max": backend.n_qubits_max},
        "curve": curve.records,
        "curve_fit": curve.residuals,
        "probes": [result.to_dict() for result in probes],
        "sweep": sweep,
        "scaling": fit.describe(),
        "classical_baseline": baseline.to_dict(),
        "notes": ["The sweep records above were counted at the truth-table lowering."],
    }

    text = render_report(qlwr_spec.describe(), results, run_dir=tmp_path)

    assert "## Success probability versus iteration" in text
    assert "## Structural probes" in text
    assert "## Classical baseline" in text
    assert "## Scaling, and where it stops being measurement" in text
    assert "`[measured]`" in text

    # The curve: the measured peak at the derived optimum, and the closed form beside it.
    assert "The measured curve peaks at `k = 50`" in text
    assert "k_opt = 50" in text

    # The probes: the caveat is rendered in the same row as the verdict.
    assert "n = 128" in text
    assert "simon_style" in text and "qft_period" in text

    # The scaling: the measured rows with their provenance, and the fit labelled as a model.
    assert "truth table" in text or "n_search" in text
    assert "extrapolated_gate_count_n_search_128" in text
    assert "Every value in this table is `[extrapolated]`" in text
    assert "It was not simulated" in text

    # The baseline: the measured query count first, and the exact expectation and worst case named.
    assert f"`{baseline.queries}` queries" in text
    assert "4097/2" in text
    assert "exhaustive search" in text

    # And nothing that was fitted is presented as counted.
    extrapolated_count = f"{fit.predictions[0].gate_count:.6g}"
    assert extrapolated_count not in str(sweep)


def test_a_report_built_without_this_layer_says_so_rather_than_omitting_it(tmp_path, qlwr_spec):
    """A missing section is printed as missing. The alternative reads as a section that found nothing."""
    text = render_report(
        qlwr_spec.describe(),
        {
            "run_id": "empty",
            "kind": "experiment",
            "not_run": {
                "curve": "the backend was not available",
                "probes": "the backend was not available",
                "scaling": "no sweep was run",
                "classical_baseline": "not requested",
            },
        },
        run_dir=tmp_path,
    )
    assert "Not measured: the backend was not available" in text
    assert "Not run: the backend was not available" in text
    assert "Not run: no sweep was run" in text
    assert "Not computed: not requested" in text


def test_probe_refusals_reach_the_report_as_refusals(tmp_path, qlwr_spec, backend):
    """A probe that could not run is reported with its reason, in the probe table itself."""
    refused = qft_period_probe(qlwr_spec, backend, lowering=Lowering.ARITHMETIC)
    text = render_report(
        qlwr_spec.describe(),
        {"run_id": "refusal", "kind": "experiment", "probes": [refused.to_dict()]},
        run_dir=tmp_path,
    )
    assert "not run" in text
    assert "ceiling" in text
    assert "did not run" in text


def test_the_layer_never_writes_a_report_of_its_own(tmp_path, qlwr_spec, backend):
    """The analysis layer returns objects; only the reporting layer writes files.

    Cheap to assert and worth asserting: an analysis function that wrote a file would put a side
    effect inside a measurement, and the reproducibility of a run would then depend on the order in
    which its parts were called.
    """
    before = sorted(path.name for path in Path(tmp_path).iterdir())
    success_curve(qlwr_spec, backend, iteration_range=range(50, 52))
    run_probes(qlwr_spec, backend, samples=64)
    classical_baseline(qlwr_spec, ("no-write",))
    fit_gate_scaling(_synthetic_points((8, 10, 12), (584, 1608, 3650)), target_widths=(128,))
    assert sorted(path.name for path in Path(tmp_path).iterdir()) == before


def test_a_random_control_curve_still_matches_the_closed_form(backend):
    """The closed form depends on ``(M, N)`` alone; the control spec has no structure to depart from.

    Included as the negative half of the curve's meaning: agreement between the measured curve and
    the closed form is evidence the harness is wired to the same problem, and would look the same if
    the oracle had structure — which is why the probes exist as a separate question.
    """
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=4, seed=2)
    curve = success_curve(spec, backend, iteration_range=range(0, 4))
    assert measured_success_probability(spec, backend, 2) == pytest.approx(
        curve.points[2].closed_form, abs=1e-12
    )
    assert math.isclose(curve.peak_measured.measured, curve.peak_closed_form.closed_form, abs_tol=1e-12)


def test_statevector_of_is_the_only_thing_the_layer_needs_from_an_engine():
    """The layer's whole engine contract, in one assertion: one method, one array.

    ``QiskitStatevector`` above exposes ``statevector`` and nothing else an engine would have —
    no sampling, no transpilation, no device — and every measurement in this file ran through it.
    """
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=1, seed=11)
    engine = QiskitStatevector()
    circuit = build_grover_circuit(spec, 1, Lowering.TRUTH_TABLE)
    statevector = statevector_of(engine, circuit)
    assert statevector.shape == (1 << circuit.num_qubits,)
    assert not hasattr(engine, "sample")


# -----------------------------------------------------------------------------------------------
# the negative control, and what a silence on it is worth
# -----------------------------------------------------------------------------------------------

DECISIVE_SAMPLES = 4000
"""Sample count for the control checks, against the probes' own default of ``max(4 * n, 64)``.

At the default the random control is silent for the weak reason — candidates appeared in the null
space and the marked set refuted each one — which is a statement about the sample count rather than
about the oracle. Four thousand samples span the register, so the silence that remains is a
statement about the oracle. The count is deliberately the one the probe module's own controls use,
so that both readings are of the same measurement.
"""


def test_the_negative_control_is_genuinely_unstructured(random_spec, backend):
    """The session negative control has nothing in it, by exhaustive check and by both probes.

    A negative control supports exactly one claim — "a probe that fires on this is broken" — and it
    supports it only if no working probe has anything to find there. Two different checks are made:
    the marked set is tested against *every* non-zero candidate period, which decides the closure
    property outright at this width, and the probes are run against the circuit built from it, so
    the sampled half is checked against the arithmetic half.
    """
    marked = random_spec.marked_set()
    n = random_spec.search_width()
    # A floor on the size rather than a size assertion: a marked set this small could be closed by
    # accident — two elements always are — so the size is recorded here and the claim is the
    # exhaustive check below, which is a statement about this set and not about how big it is.
    assert len(marked) >= 8

    periods = [period for period in range(1, 1 << n) if verify_period(marked, n, period)]
    assert periods == [], (
        f"the control has the period(s) {periods}, so a probe firing on it would be right and the "
        "fixture could not tell a working probe from a broken one"
    )

    for result in run_probes(random_spec, backend, samples=DECISIVE_SAMPLES):
        assert result.status == MEASURED
        assert result.fired is False, result.detail
        assert result.period_verified is False
        assert result.candidate_period is None
        # The strong silence: the samples spanned the register, so no non-trivial period is
        # consistent with what was measured at all. The weak form would leave the nullity positive.
        assert result.nullity == 0


def test_a_two_element_control_is_degenerate_which_is_why_it_is_not_the_fixture(random_spec, backend):
    """The arithmetic the fixture's size follows from, recorded as a fact rather than as a detection.

    For marked values ``{a, b}`` the map ``x -> x ^ (a ^ b)`` exchanges the two and so closes the
    set. A two-element marked set therefore has a period whatever its elements happen to be, both
    probes find it, and their firing on it says nothing about whether the probes work — which is why
    the session fixture is not two elements. The degeneracy is kept here, at the width the fixture
    actually uses, so that the size is not read later as an arbitrary choice.
    """
    two = RandomControlOracleSpec(n_qubits=random_spec.search_width(), n_marked=2, seed=11)
    marked = sorted(two.marked_set())
    difference = marked[0] ^ marked[1]
    assert verify_period(two.marked_set(), two.search_width(), difference)

    result = simon_style_probe(two, backend, samples=DECISIVE_SAMPLES)
    assert result.fired is True
    assert result.candidate_period == difference
