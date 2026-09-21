"""The command line end to end: one config in, one results directory out.

The properties asserted here are the ones that decide whether a report is worth reading, and each of
them is a decision rather than a default:

1. **The iteration range is derived from the instance, never from the configuration.** A fixed window
   is a way to produce a monotone rising curve that supports no conclusion, so the check is not that a
   range exists but that a configuration *asking* for a different one does not get it.
2. **``M`` is measured, not configured.** The run reports the size of the marked set it enumerated,
   and the configuration's target fraction enters no computation.
3. **An over-budget point is refused before allocation.** The refusal carries the byte count that made
   it one, and the engine is never asked to run.
4. **A refusal is an outcome, not a crash.** Every sweep width that could not be built is a row with
   its reason, and a run whose instance could not be generated still writes a results directory.
5. **The incremental curve is the same curve.** The CLI applies one round at a time rather than
   building a k-round circuit per point, so the suite asserts the two agree point by point against
   the analysis layer's from-scratch curve.

Everything here runs at the smallest widths that produce a real QLWR instance (``n_search = 12``; the
worked instance in ``notes/01-arithmetic.md``) or against the small controls, because the point is the
contract and not the arithmetic.
"""

from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from grover_emulator.cli import (
    DEFAULT_CONFIG,
    ExecutionRefused,
    _AmplitudeAdapter,
    _certification_refusal,
    _draws_affordable,
    _exact_statevector_curve,
    app,
    regenerate_report,
    run_experiment,
    run_sweep,
)
from grover_emulator.problem.oracle_spec import (
    Lowering,
    RandomControlOracleSpec,
)
from grover_emulator.reporting.report_generator import SCOPE_BOUNDARY, load_results
from grover_emulator.utils.seeding import RunSeeds

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_experiment.py"
SWEEP_SCRIPT = REPO / "scripts" / "sweep_scaling.py"

FAITHFUL_N = 12
"""The smallest structurally faithful QLWR instance; below it no admissible prime pair exists."""


# -----------------------------------------------------------------------------------------------
# configurations, and the runs that spend them
# -----------------------------------------------------------------------------------------------


def _write_config(directory: Path, name: str, **sections) -> Path:
    """A configuration file built from the schema's own defaults plus the given sections."""
    from grover_emulator.config.schema import ExperimentConfig

    base = ExperimentConfig()
    body = yaml.safe_load(
        yaml.safe_dump(
            {
                "run": {"seed": base.run.seed, "lowering": base.run.lowering},
                "oracle": {
                    "type": base.oracle.type.value,
                    "target_qubits": base.oracle.target_qubits,
                    "marked_fraction": base.oracle.marked_fraction,
                    "seed": base.oracle.seed,
                    "nu": base.oracle.nu,
                    "min_rounding_gap": base.oracle.min_rounding_gap,
                },
                "sweep": {"qubit_range": list(base.sweep.qubit_range)},
                "backend": {
                    "preference": list(base.backend.preference),
                    "ram_budget_gb": base.backend.ram_budget_gb,
                    "shots": base.backend.shots,
                },
                "probes": {
                    "run_simon_style": base.probes.run_simon_style,
                    "run_qft_period": base.probes.run_qft_period,
                },
                "output": {"dir": directory.as_posix(), "formats": ["markdown", "json", "png"]},
            }
        )
    )
    body["sweep"]["iteration_range"] = None
    for section, values in sections.items():
        body.setdefault(section, {}).update(values)
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(body, sort_keys=True), encoding="utf-8")
    return path


@pytest.fixture(scope="session")
def run_root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("cli-runs")


@pytest.fixture(scope="session")
def small_config(run_root: Path) -> Path:
    """One row of sweep, one instance: the cheapest configuration that still has a real curve."""
    return _write_config(
        run_root,
        "small.yaml",
        oracle={"target_qubits": FAITHFUL_N, "type": "qlwr"},
        sweep={"qubit_range": [FAITHFUL_N]},
        backend={"shots": 500},
        output={"dir": (run_root / "results").as_posix()},
    )


@pytest.fixture(scope="session")
def small_run(small_config: Path):
    """The run every end-to-end assertion below reads. Executed once for the whole session."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_experiment(small_config)


@pytest.fixture(scope="session")
def control_config(run_root: Path) -> Path:
    """A negative control at a width whose whole curve costs less than a second."""
    return _write_config(
        run_root,
        "control.yaml",
        oracle={"type": "random_control", "target_qubits": 6, "marked_fraction": 0.05},
        sweep={"qubit_range": [6]},
        backend={"shots": 200},
        output={"dir": (run_root / "control-results").as_posix()},
    )


@pytest.fixture(scope="session")
def control_run(control_config: Path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_experiment(control_config)


# -----------------------------------------------------------------------------------------------
# the results directory
# -----------------------------------------------------------------------------------------------


def test_a_run_writes_the_directory_the_report_reads(small_run):
    run_dir, results = small_run
    assert run_dir.is_dir()
    for name in ("config.yaml", "metrics.json", "report.md"):
        assert (run_dir / name).is_file(), f"{name} is missing from {run_dir}"
    assert (run_dir / "figures").is_dir()
    assert list((run_dir / "figures").glob("*.png"))
    # The mapping on disk is the mapping the report was rendered from, byte for byte.
    assert load_results(run_dir) == json.loads(json.dumps(results, default=str))


def test_the_directory_name_identifies_the_run(small_run, small_config):
    run_dir, results = small_run
    from grover_emulator.config.schema import load_config

    config = load_config(small_config)
    assert results["run_id"] == run_dir.name
    assert results["run_id"] == (
        f"{config.oracle.type.value}-n{config.oracle.target_qubits}-"
        f"{config.run.lowering}-s{config.run.seed}"
    )


def test_the_configuration_written_is_the_one_validated(small_run, small_config):
    """The echo is what the run loaded, not the file that happens to be on disk now."""
    run_dir, results = small_run
    stored = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
    assert stored["oracle"]["target_qubits"] == results["config"]["oracle"]["target_qubits"]
    assert stored["backend"]["ram_budget_gb"] == results["config"]["backend"]["ram_budget_gb"]
    assert results["config_path"] == str(small_config)


def test_a_run_carries_the_scope_boundary(small_run):
    run_dir, _results = small_run
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert SCOPE_BOUNDARY in text


# -----------------------------------------------------------------------------------------------
# the iteration range is derived, not configured
# -----------------------------------------------------------------------------------------------


def test_the_iteration_range_is_derived_from_the_instance(small_run):
    _run_dir, results = small_run
    from grover_emulator.circuits.grover_circuit_builder import derive_iteration_range

    k_opt = results["optimal_iterations"]
    assert results["iteration_range"] == [0, k_opt + 2]
    assert results["config"]["sweep"]["iteration_range"] is None
    # The same function the builder exposes, over the same instance, is where the range came from.
    spec = _spec_from_results(results)
    assert derive_iteration_range(spec) == range(0, k_opt + 3)


def test_a_configured_iteration_range_is_refused_and_warned_about(run_root, control_config):
    """A fixed window is not obeyed: the run warns, then derives the range from the instance anyway."""
    fixed = _write_config(
        run_root,
        "fixed-window.yaml",
        oracle={"type": "random_control", "target_qubits": 6, "marked_fraction": 0.05},
        sweep={"qubit_range": [6], "iteration_range": [0, 3]},
        backend={"shots": 100},
    )
    with pytest.warns(UserWarning, match="iteration_range is fixed"):
        _run_dir, results = run_experiment(fixed, run_id="fixed-window")
    derived = results["iteration_range"]
    assert derived[0] == 0
    assert derived[1] == results["optimal_iterations"] + 2
    assert derived != [0, 3]
    assert len(results["curve"]) == derived[1] + 1
    assert results["curve"][-1]["iteration"] == derived[1]


def test_the_range_warns_when_it_could_not_contain_the_peak(control_run):
    """The window is checked against the closed form's peak, so a truncated one cannot pass silently."""
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=1, seed=11)
    from grover_emulator.analysis import success_curve

    from grover_emulator.backends.qiskit_aer_backend import QiskitAerBackend

    engine = _AmplitudeAdapter(QiskitAerBackend())
    with pytest.warns(UserWarning, match="does not contain the closed form's peak"):
        success_curve(spec, engine, iteration_range=range(0, 2))


# -----------------------------------------------------------------------------------------------
# M is measured
# -----------------------------------------------------------------------------------------------


def test_the_marked_set_size_is_measured_by_enumeration(small_run):
    _run_dir, results = small_run
    spec = _spec_from_results(results)
    enumerated = len(spec.marked_set())
    assert results["marked_set_size"] == enumerated == 1
    assert results["n_items"] == spec.space().n_items
    assert results["search_width"] == FAITHFUL_N
    # The configuration aimed at a density; the run reports the size it enumerated, and they differ.
    target = results["config"]["oracle"]["marked_fraction"]
    assert target != pytest.approx(enumerated / results["n_items"], rel=0.5)
    assert "measured" in " ".join(results["notes"])


def test_the_marked_set_is_stored_where_it_fits(small_run):
    _run_dir, results = small_run
    assert results["marked_set"] == sorted(_spec_from_results(results).marked_set())


# -----------------------------------------------------------------------------------------------
# the curve
# -----------------------------------------------------------------------------------------------


def test_the_curve_is_measured_and_matches_the_closed_form(small_run):
    _run_dir, results = small_run
    curve = results["curve"]
    assert len(curve) == results["iteration_range"][1] + 1
    for record in curve:
        assert record["provenance"]["empirical_p_success"].startswith("measured")
        assert record["provenance"]["theoretical_p_success"].startswith("closed form")
        assert record["empirical_p_success"] == pytest.approx(record["theoretical_p_success"], abs=1e-12)
    peak = max(curve, key=lambda r: r["empirical_p_success"])
    assert peak["iteration"] == results["optimal_iterations"]

    fit = results["curve_fit"]
    assert fit["peak_iteration_agrees"] in (True, "True", "yes")
    assert fit["max_abs_residual"] < 1e-9
    assert results["backend"]["method"] == "statevector"
    assert results["backend"]["exact_statevector_bytes"] == 16 * (1 << (FAITHFUL_N + 1))


def test_the_incremental_curve_equals_a_from_scratch_run(random_spec, aer_backend):
    """The execution shortcut, checked against the thing it stands in for.

    The CLI applies one round of (oracle, diffuser) to the evolving state; the analysis layer builds
    the k-round circuit from scratch for each point. The two must be the same simulation, so this
    compares them point by point — and the tolerance is a few units in the last place, which is what
    composing the same unitary twice can differ by in binary floating point, not a rounding of the
    answer.
    """
    from grover_emulator.analysis import success_curve

    engine = _AmplitudeAdapter(aer_backend)
    iterations = range(0, 4)
    assert iterations.stop <= random_spec.space().optimal_iterations, "keep the window inside the peak"
    records, _backend_record = _exact_statevector_curve(
        random_spec, Lowering.TRUTH_TABLE, iterations, budget_gb=6.0, shots=0,
        seeds=RunSeeds.new(4242), backend=engine,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        reference = success_curve(random_spec, engine, iteration_range=iterations)

    assert len(records) == len(reference.points)
    for record, point in zip(records, reference.points):
        assert record["iteration"] == point.iteration
        assert record["empirical_p_success"] == pytest.approx(point.measured, rel=0, abs=1e-15)
        assert record["theoretical_p_success"] == pytest.approx(point.closed_form, rel=0, abs=1e-15)


def test_the_curve_does_not_claim_independence_from_the_closed_form(small_run):
    """A diagonal phase oracle contributes nothing to the curve, and the report says so."""
    run_dir, _results = small_run
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "*not* independent evidence for the curve" in text
    assert "the curve is the control" in text


def test_the_shot_based_estimator_is_recorded_beside_the_exact_one(small_run):
    _run_dir, results = small_run
    last = results["curve"][-1]
    assert last["shots"] == results["config"]["backend"]["shots"]
    assert last["sampled_p_success"] is not None
    assert last["sampled_p_success"] == pytest.approx(last["empirical_p_success"], abs=0.1)
    assert results["backend"]["shots"] == results["config"]["backend"]["shots"]


# -----------------------------------------------------------------------------------------------
# the budget: refused, never attempted
# -----------------------------------------------------------------------------------------------


def test_an_over_budget_point_is_refused_with_its_size_before_allocation(qlwr_spec):
    """The refusal names the width and the size, and no state is ever allocated.

    The budget asked of the engine is the engine's own — the caller does not get a second opinion —
    so an engine holding a budget too small to hold the statevector is what refuses here, and the
    reason carries the estimate it refused on.
    """
    from grover_emulator.backends.qiskit_aer_backend import QiskitAerBackend

    engine = _AmplitudeAdapter(QiskitAerBackend(ram_budget_gb=1e-9))
    with pytest.raises(ExecutionRefused) as caught:
        _exact_statevector_curve(
            qlwr_spec, Lowering.TRUTH_TABLE, range(0, 2), budget_gb=6.0, shots=0,
            seeds=RunSeeds.new(1), backend=engine,
        )
    message = str(caught.value)
    assert "refuses 13 qubits" in message
    assert "ceiling" in message and "KiB" in message
    assert engine.runs == [], "the engine ran something the budget had already refused"


def test_the_local_check_is_used_when_there_is_no_engine(qlwr_spec):
    """Same refusal without the backends layer: the caller's own arithmetic, before allocation."""
    with pytest.raises(ExecutionRefused) as caught:
        _exact_statevector_curve(
            qlwr_spec, Lowering.TRUTH_TABLE, range(0, 2), budget_gb=1e-9, shots=0,
            seeds=RunSeeds.new(1), backend=None,
        )
    assert "Refused before allocating" in str(caught.value)
    assert f"{16 * (1 << 13):,}" in str(caught.value)


def test_a_refused_curve_is_recorded_in_the_run_and_in_the_report(run_root, control_config):
    """A run whose curve is refused still produces a report that says which point and why."""
    starved = _write_config(
        run_root,
        "starved.yaml",
        oracle={"type": "random_control", "target_qubits": 6, "marked_fraction": 0.05},
        sweep={"qubit_range": [6]},
        backend={"ram_budget_gb": 1e-9, "shots": 100},
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_dir, results = run_experiment(starved, run_id="starved")
    assert "curve" not in results
    reason = results["not_run"]["curve"]
    assert "over the" in reason and "budget" in reason
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "Not measured:" in text
    assert reason.split(":")[0][:20] in text or "budget" in text


def test_certification_cost_is_decided_from_the_width():
    """A width whose certification could not finish is refused from the width, not from a hang."""
    assert _draws_affordable(4) == 1 << 19
    assert _draws_affordable(20) == 8
    assert _draws_affordable(23) == 1
    assert _draws_affordable(24) is None
    reason = _certification_refusal(24)
    assert "2**24" in reason and "Refused rather than attempted" in reason


# -----------------------------------------------------------------------------------------------
# the sweep
# -----------------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sweep_run(run_root: Path):
    config = _write_config(
        run_root,
        "sweep.yaml",
        oracle={"target_qubits": FAITHFUL_N, "type": "qlwr"},
        sweep={"qubit_range": [4, FAITHFUL_N]},
        backend={"shots": 100},
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_sweep(config, run_id="sweep-under-test")


def test_every_sweep_width_gets_a_row_and_a_refusal_is_never_silent(sweep_run):
    _run_dir, results = sweep_run
    rows = results["sweep"]
    assert [row["n_search"] for row in rows] == [4, FAITHFUL_N]

    refused = [row for row in rows if row["status"] != "measured"]
    assert [row["n_search"] for row in refused] == [4]
    assert "no generic prime" in refused[0]["reason"]

    measured = [row for row in rows if row["status"] == "measured"]
    assert [row["n_search"] for row in measured] == [FAITHFUL_N]
    row = measured[0]
    assert row["n_qubits_truth_table"] == FAITHFUL_N + 1
    assert row["grover_gates_truth_table"] > row["oracle_gates_truth_table"] > 0
    assert row["gate_count"] > 1000, "the arithmetic oracle is thousands of gates, not a handful"
    assert row["toffoli_count"] > 0 and row["t_count_with_toffolis"] >= row["toffoli_count"]
    assert row["optimal_iterations"] == results["sweep"][1]["optimal_iterations"] > 0


def test_the_sweep_refuses_the_arithmetic_statevector_pass_with_its_size(sweep_run, qlwr_spec):
    """The arithmetic circuit is unsimulable, and that is recorded as a measured limit.

    The width, the byte cost and the refusal in one row describe one circuit: the arithmetic oracle
    is 50 qubits at this instance — the smallest one the relation is structurally faithful at — and
    one statevector of it is 16 PiB, which no machine in this class holds.
    """
    from grover_emulator.circuits.phase_oracle import build_phase_oracle

    _run_dir, results = sweep_run
    row = [r for r in results["sweep"] if r["status"] == "measured"][0]
    assert row["n_qubits_arithmetic"] == 50
    assert row["statevector_bytes_arithmetic"] == 16 * (1 << 50)
    assert row["statevector_fits_budget_arithmetic"] is False
    assert row["statevector_fits_budget_truth_table"] is True
    # The width reported is the circuit's own — the arithmetic oracle's gate list, which is the same
    # object the gate counts beside it in the row are counted from.
    assert row["n_qubits_arithmetic"] == build_phase_oracle(qlwr_spec, Lowering.ARITHMETIC).num_qubits
    assert row["n_qubits_truth_table"] == build_phase_oracle(qlwr_spec, Lowering.TRUTH_TABLE).num_qubits

    key = f"statevector pass, arithmetic lowering at n_search={FAITHFUL_N}"
    reason = results["not_run"][key]
    assert "50 qubits" in reason
    assert "PiB" in reason and "budget" in reason


def test_a_sweep_records_what_it_did_not_do(sweep_run):
    run_dir, results = sweep_run
    assert results["kind"] == "sweep"
    assert "curve" not in results, "a sweep measures circuit cost, not a success curve"
    notes = " ".join(results["notes"])
    assert "no statevector was allocated" in notes
    assert "gate-list IR" in notes
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert SCOPE_BOUNDARY in text


# -----------------------------------------------------------------------------------------------
# the corpus's own two oracles, selectable from the configuration
# -----------------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def lmots_default_run(run_root: Path):
    """The corpus's chain at its default chain length: one truncated hash per candidate."""
    config = _write_config(
        run_root,
        "lmots-default.yaml",
        oracle={"type": "lmots_chain", "target_qubits": 6},
        sweep={"qubit_range": [6]},
        backend={"shots": 200},
        output={"dir": (run_root / "lmots-default-results").as_posix()},
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_experiment(config, with_sweep=False)


@pytest.fixture(scope="session")
def lmots_run(run_root: Path):
    """The same relation iterated — the other reading of "chain" — at a 6-bit register."""
    config = _write_config(
        run_root,
        "lmots-chain.yaml",
        oracle={"type": "lmots_chain", "target_qubits": 6, "chain_length": 2},
        sweep={"qubit_range": [6]},
        backend={"shots": 200},
        output={"dir": (run_root / "lmots-results").as_posix()},
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_experiment(config)


@pytest.fixture(scope="session")
def key_map_run(run_root: Path):
    """The corpus's key map in mode B, at the smallest width that holds its 4n register."""
    config = _write_config(
        run_root,
        "key-map.yaml",
        oracle={"type": "key_map", "target_qubits": 8, "key_map_mode": "B"},
        sweep={"qubit_range": [8]},
        backend={"shots": 200},
        output={"dir": (run_root / "key-map-results").as_posix()},
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_experiment(config)


def test_the_lmots_chain_is_selected_by_type_from_the_configuration(lmots_run):
    """Reachable by writing a type into the configuration, with the reading pinned in the report."""
    run_dir, results = lmots_run
    assert results["spec"]["name"] == "lmots_chain"
    assert results["spec"]["chain_length"] == 2
    assert results["spec"]["chain_convention"] == "iterated_chain"
    # The reading is part of the run's identity, not only of its numbers: two chain lengths are two
    # search problems, and sharing a directory would let the second run overwrite the first's report.
    assert run_dir.name == results["run_id"] == (
        f"lmots_chain-k2-n{results['search_width']}-truth_table-s{results['seed']}"
    )
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "iterated_chain" in text and "chain_applications" in text
    assert SCOPE_BOUNDARY in text


def test_the_chain_run_reports_the_marked_set_size_the_spec_fixed(lmots_run):
    """``M`` is the relation's own and is measured, and the seed record carries the draw it came from."""
    _run_dir, results = lmots_run
    spec = _spec_from_results(results)
    assert results["marked_set_size"] == spec.space().n_marked == len(spec.marked_set())
    assert results["marked_set_size"] >= 1, "the chain's target is a value of the drawn secret"
    record = results["seed_record"]
    assert record["facts"]["lmots_chain.marked_set_size"] == results["marked_set_size"]
    # The secret is drawn from the description of the problem, so the recorded label names that
    # description — the width, the chain length, the fold width and the spec's own seed.
    assert any(label.startswith("lmots_chain.6.2.6.") for label in record["derived"])


def test_the_lmots_chain_claims_no_arithmetic_form(lmots_run):
    """A truncated hash is not arithmetic; the run says so instead of offering a compiled circuit."""
    _run_dir, results = lmots_run
    assert results["spec"]["supports_arithmetic_lowering"] is False
    assert "oracle (arithmetic)" not in results["circuits"]
    assert [row["name"] for row in results["validation"]] == ["predicate == marked set (truth_table)"]
    assert all(row["ok"] for row in results["validation"])


def test_the_default_chain_length_is_the_corpus_behaviour_and_says_so(lmots_default_run):
    """The default reproduces the corpus's single hash call for call, and the report names it."""
    run_dir, results = lmots_default_run
    assert results["spec"]["chain_length"] == 1
    assert results["spec"]["chain_convention"] == "single_hash"
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "single_hash" in text
    assert "one truncated hash per candidate" in text
    assert SCOPE_BOUNDARY in text


def test_the_key_map_is_selected_by_type_from_the_configuration(key_map_run):
    """The register the map was searched over is a reported fact, as open as the chain's reading."""
    run_dir, results = key_map_run
    assert results["spec"]["name"] == "key_map"
    assert results["spec"]["mode"] == "B"
    assert results["spec"]["n_variables"] == 8 and results["spec"]["n_outputs"] == 1
    assert run_dir.name == results["run_id"] == (
        f"key_map-modeB-eq1-n{results['search_width']}-truth_table-s{results['seed']}"
    )
    spec = _spec_from_results(results)
    assert results["marked_set_size"] == spec.space().n_marked == len(spec.marked_set())
    assert results["marked_set_size"] > 1
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "| n_variables | 8 |" in text and "| mode | B |" in text
    assert SCOPE_BOUNDARY in text


def test_the_key_map_compiles_in_both_lowerings(key_map_run):
    """The map is arithmetic, so both lowerings exist and are checked against the same marked set."""
    _run_dir, results = key_map_run
    assert results["spec"]["supports_arithmetic_lowering"] is True
    assert "oracle (arithmetic)" in results["circuits"]
    assert {row["name"] for row in results["validation"]} == {
        "predicate == marked set (truth_table)",
        "predicate == marked set (arithmetic)",
    }
    assert all(row["ok"] for row in results["validation"])
    assert results["spec"]["work_qubits_arithmetic"] == results["spec"]["n_outputs"]


def test_a_corpus_oracle_width_over_the_enumeration_budget_is_a_refusal_not_a_hang(run_root):
    """A width whose marked set cannot be measured inside the budget is a row with its reason.

    Both corpus oracles fix ``M`` by evaluating the relation on the whole search register, so the
    width is what decides whether a point is affordable — and 24 qubits of hashing is over the
    budget this project spends before refusing one. The refusal is decided from the width, before
    the enumeration starts, exactly as the arithmetic statevector pass is refused from its width.
    """
    config = _write_config(
        run_root,
        "lmots-wide.yaml",
        oracle={"type": "lmots_chain", "target_qubits": 24},
        sweep={"qubit_range": [6, 24]},
        backend={"shots": 100},
        output={"dir": (run_root / "lmots-wide-results").as_posix()},
    )
    _run_dir, results = run_sweep(config, run_id="lmots-wide")
    rows = {row["n_search"]: row for row in results["sweep"]}
    assert rows[6]["status"] == "measured" and rows[6]["n_marked"] >= 1
    assert rows[24]["status"] == "not run"
    assert "16,777,216" in rows[24]["reason"] and "budget" in rows[24]["reason"]


def test_the_corpus_reports_regenerate_byte_for_byte(lmots_run, key_map_run):
    """The report is a view of the stored mapping, for the corpus oracles as for the others.

    The facts that pin a reading are stored in the mapping and replayed from it, so re-rendering
    after the fact cannot re-derive them from a spec that no longer exists beside the numbers.
    """
    for run_dir, _results in (lmots_run, key_map_run):
        before = (run_dir / "report.md").read_text(encoding="utf-8")
        regenerate_report(run_dir)
        assert (run_dir / "report.md").read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    ("config_name", "spec_name"),
    [("lmots-chain.yaml", "lmots_chain"), ("key-map.yaml", "key_map")],
)
def test_the_run_command_reaches_the_corpus_oracles(run_root, tmp_path, config_name, spec_name):
    """The command line itself — ``cli run --config ...`` — not only the function behind it."""
    result = CliRunner().invoke(
        app,
        [
            "run",
            "--config",
            str(run_root / config_name),
            "--no-sweep",
            "--output-dir",
            str(tmp_path / config_name.replace(".yaml", "")),
        ],
    )
    assert result.exit_code == 0, result.output
    written = [line for line in result.output.splitlines() if line.endswith("report.md")]
    assert written, result.output
    run_dir = Path(written[-1]).parent
    stored = load_results(run_dir)
    assert stored["spec"]["name"] == spec_name
    assert SCOPE_BOUNDARY in (run_dir / "report.md").read_text(encoding="utf-8")


# -----------------------------------------------------------------------------------------------
# seeds
# -----------------------------------------------------------------------------------------------


def test_every_stochastic_choice_is_derivable_from_the_recorded_seed(small_run):
    _run_dir, results = small_run
    record = results["seed_record"]
    assert record["root"] == results["seed"]
    again = RunSeeds.from_dict(record)
    again.verify()
    original = RunSeeds.new(results["seed"])
    for parts in (("aer", 13), ("classical_baseline", 4096, 1)):
        assert again.derive(*parts) == original.derive(*parts)
    # The facts the run fixed — M above all — travel with the seeds that determined them.
    assert record["facts"]["marked_set_size"] == results["marked_set_size"]
    assert record["facts"]["iteration_range"] == results["iteration_range"]
    assert record["derived"], "a run that records no derived seed cannot be replayed"


def test_the_same_seed_and_instances_produce_the_same_seeds():
    first, second = RunSeeds.new(20260913), RunSeeds.new(20260913)
    assert first.derive("aer", 13) == second.derive("aer", 13)
    assert RunSeeds.new(20260914).derive("aer", 13) != first.derive("aer", 13)


# -----------------------------------------------------------------------------------------------
# the classical baseline, and the checks that keep the counts honest
# -----------------------------------------------------------------------------------------------


def test_the_baseline_is_a_measurement_with_its_caveat_attached(small_run):
    _run_dir, results = small_run
    baseline = results["classical_baseline"]
    assert baseline["queries"] >= 1
    assert baseline["n_marked"] == results["marked_set_size"]
    # The expectation is an exact rational over (M, N), not this one draw: (N+1)/(M+1) for a
    # random-order scan without replacement.
    n_items, n_marked = results["n_items"], results["marked_set_size"]
    assert float(baseline["queries_expected_float"]) == pytest.approx(
        (n_items + 1) / (n_marked + 1), rel=1e-9
    )
    assert baseline["queries_worst_case"] == n_items - n_marked + 1
    assert "caveat" in baseline and "exhaustive search" in baseline["caveat"]


def test_the_predicates_are_checked_against_the_marked_set(small_run):
    _run_dir, results = small_run
    rows = results["validation"]
    assert rows, "a run must say what it verified"
    assert all(row["ok"] is True for row in rows), rows
    assert {row["name"] for row in rows} == {
        "predicate == marked set (truth_table)",
        "predicate == marked set (arithmetic)",
    }
    assert all(row["n_states"] == 1 << FAITHFUL_N for row in rows)


def test_every_circuit_is_counted_from_the_ir(small_run):
    _run_dir, results = small_run
    circuits = results["circuits"]
    assert "oracle (truth_table)" in circuits
    assert "oracle (arithmetic)" in circuits
    grover = next(key for key in circuits if key.startswith("grover k="))
    assert circuits[grover]["num_qubits"] == FAITHFUL_N + 1
    assert circuits["oracle (arithmetic)"]["num_qubits"] == 50
    for record in circuits.values():
        assert set(record) >= {
            "label", "num_qubits", "gate_count", "counts", "toffoli_count",
            "t_count_with_toffolis", "ir_depth", "ancilla_peak", "classically_simulable",
        }


# -----------------------------------------------------------------------------------------------
# the analysis layer's sections, as the CLI reports them
# -----------------------------------------------------------------------------------------------


def test_the_probes_run_and_carry_their_caveat(control_run):
    _run_dir, results = control_run
    probes = results["probes"]
    assert probes, "the probe suite is present in this checkout and must have run"
    assert all("caveat" in record for record in probes)
    assert any(record["probe"] for record in probes)


def test_a_run_with_a_single_measured_width_refuses_to_fit(small_run):
    """One point is not a trend, and the fit says so instead of drawing a line through it."""
    _run_dir, results = small_run
    assert len([row for row in results["sweep"] if row["status"] == "measured"]) == 1
    assert "scaling" not in results
    assert "at least 3 measured points" in results["not_run"]["scaling"]


# -----------------------------------------------------------------------------------------------
# the commands
# -----------------------------------------------------------------------------------------------


def test_the_cli_advertises_its_commands():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("run", "sweep", "report", "probe"):
        assert command in result.output
        assert runner.invoke(app, [command, "--help"]).exit_code == 0


def test_the_report_command_regenerates_a_stored_run(small_run, tmp_path):
    run_dir, _results = small_run
    before = (run_dir / "report.md").read_text(encoding="utf-8")
    result = CliRunner().invoke(app, ["report", "--run-dir", str(run_dir)])
    assert result.exit_code == 0
    assert str(run_dir / "report.md") in result.output
    assert (run_dir / "report.md").read_text(encoding="utf-8") == before
    assert SCOPE_BOUNDARY in before

    elsewhere = regenerate_report(run_dir, filename="again.md")
    assert elsewhere.name == "again.md"
    assert elsewhere.read_text(encoding="utf-8") == before


def test_the_report_command_fails_loudly_on_a_directory_with_no_results(tmp_path):
    result = CliRunner().invoke(app, ["report", "--run-dir", str(tmp_path)])
    assert result.exit_code == 1


def test_the_documented_script_is_wired_to_the_run_command():
    """The command in the README, executed: ``scripts/run_experiment.py --help``."""
    for script in (SCRIPT, SWEEP_SCRIPT):
        assert script.is_file()
        completed = subprocess.run(
            [sys.executable, str(script), "--help"], capture_output=True, text=True, cwd=REPO
        )
        assert completed.returncode == 0, completed.stderr
        assert "--config" in completed.stdout
    # The scripts default to the same configuration the CLI does, and that file is in the tree.
    assert (REPO / DEFAULT_CONFIG).is_file()


def test_the_script_refuses_an_impossible_configuration_without_a_traceback(tmp_path):
    """A run that cannot be attempted exits non-zero and says so, rather than dumping a stack."""
    missing = tmp_path / "absent.yaml"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(missing)],
        capture_output=True, text=True, cwd=REPO,
    )
    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr


# -----------------------------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------------------------


def _spec_from_results(results):
    """The spec a stored run's results describe, rebuilt from the configuration it validated."""
    from grover_emulator.cli import _build_spec
    from grover_emulator.config.schema import ExperimentConfig

    config = ExperimentConfig.model_validate(results["config"])
    spec, _instance, refusal = _build_spec(config, RunSeeds.new(results["seed"]))
    assert refusal is None, refusal
    return spec
