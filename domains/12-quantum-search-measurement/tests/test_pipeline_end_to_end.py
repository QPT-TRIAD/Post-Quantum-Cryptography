"""One flow, at ``n = 8``: the pipeline runs, two engines agree, and the report is of that run.

``tests/test_end_to_end.py`` checks that the layers compose on the worked QLWR instance, and its
report test renders an *empty* results mapping. This file closes the three gaps that leaves.

1. **The whole pipeline at the plan's width.** ``run_experiment`` at ``n_search = 8`` against each of
   the two controls, with the circuit the run reports rebuilt from the run's own stored configuration,
   executed on Aer *and* qsim, compared with :func:`assert_backend_agreement`, and tied back to the
   number the run stored. The report is then read from the run directory and checked against the real
   results mapping — the preamble verbatim and ahead of the first table, and the run's own ``M``,
   peak and probe verdicts in the text.
2. **The probes' verdicts reach the report.** A ``hidden_period`` run whose report says the
   Simon-style probe *fired*, beside a ``random_control`` run whose report says it did *not*. A suite
   that is only ever seen silent in a report is indistinguishable from one that cannot speak.
3. **The probes on a real engine.** Everywhere else they run on the ``ReferenceStatevector`` test
   double or behind the CLI's adapter; here :class:`QiskitAerBackend` and
   :class:`TensorNetworkBackend` are handed to them directly.

QLWR is absent on purpose: no admissible instance exists below ``n_search = 12`` (``notes/01``), so
"end to end at eight qubits" is a statement about the controls, and the worked instance has its own
file.
"""

from __future__ import annotations

import math
import warnings
from pathlib import Path

import numpy as np
import pytest
import yaml

from grover_emulator.analysis.structural_probes import (
    MEASURED,
    NOT_RUN,
    _default_samples,
    qft_period_probe,
    run_probes,
    simon_style_probe,
    verify_period,
)
from grover_emulator.analysis.success_probability import AnalysisError
from grover_emulator.backends.cirq_qsim_backend import CirqQsimBackend
from grover_emulator.backends.qiskit_aer_backend import QiskitAerBackend
from grover_emulator.backends.tensor_network_backend import TensorNetworkBackend
from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit
from grover_emulator.cli import _build_spec, run_experiment
from grover_emulator.config.schema import ExperimentConfig
from grover_emulator.problem.oracle_spec import (
    HiddenPeriodOracleSpec,
    Lowering,
    RandomControlOracleSpec,
)
from grover_emulator.reporting.report_generator import SCOPE_BOUNDARY, load_results, render_report
from grover_emulator.utils.seeding import RunSeeds
from grover_emulator.utils.validation import assert_backend_agreement

N = 8
"""The plan's end-to-end width. Nine qubits with the flag: 8 KiB of statevector."""

DECISIVE_SAMPLES = 4000
"""Enough that a random control's samples span the register — silence about the oracle, not the probe."""

pytestmark = pytest.mark.filterwarnings(
    "ignore:n_iterations=.*below this instance's optimum:UserWarning"
)


# -----------------------------------------------------------------------------------------------
# the runs
# -----------------------------------------------------------------------------------------------


def _write_config(directory: Path, name: str, **oracle) -> Path:
    body = {
        "oracle": {"target_qubits": N, **oracle},
        "sweep": {"qubit_range": [N], "iteration_range": None},
        "backend": {"shots": 500},
        "output": {"dir": (directory / "results").as_posix(), "formats": ["markdown", "json"]},
    }
    path = directory / name
    path.write_text(yaml.safe_dump(body, sort_keys=True), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def run_root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("pipeline-end-to-end")


@pytest.fixture(scope="module")
def control_run(run_root: Path):
    """The negative control: eight marked values of 256, the size at which no accidental period exists."""
    config = _write_config(run_root, "control.yaml", type="random_control", marked_fraction=8 / 256)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_experiment(config)


@pytest.fixture(scope="module")
def period_run(run_root: Path):
    """The positive control, with the period drawn by the run itself from its own seed."""
    config = _write_config(run_root, "period.yaml", type="hidden_period")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_experiment(config)


@pytest.fixture(scope="module")
def aer() -> QiskitAerBackend:
    return QiskitAerBackend()


@pytest.fixture(scope="module")
def qsim() -> CirqQsimBackend:
    return CirqQsimBackend()


def _spec_from_results(results):
    """The spec a stored run describes, rebuilt from the configuration it validated."""
    config = ExperimentConfig.model_validate(results["config"])
    spec, _instance, refusal = _build_spec(config, RunSeeds.new(results["seed"]))
    assert refusal is None, refusal
    return spec


def _report(run_dir: Path) -> str:
    return (run_dir / "report.md").read_text(encoding="utf-8")


def _probe_rows(text: str) -> dict[str, list[str]]:
    """``{probe: cells}`` from the report's structural-probe table."""
    start = text.index("## Structural probes")
    block = text[start: text.index("\n## ", start + 1)]
    rows = {}
    for line in block.splitlines():
        if line.startswith("| ") and not line.startswith("| probe ") and "---" not in line:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows[cells[0]] = cells
    return rows


# -----------------------------------------------------------------------------------------------
# (a), (b): pipeline, cross-backend agreement and the report, in one flow per control
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("which", ["control_run", "period_run"])
def test_the_pipeline_runs_two_engines_agree_and_the_report_is_of_that_run(which, request, aer, qsim):
    """Pipeline, then the same GateList on Aer and qsim, then the report — nothing re-stated by hand.

    The circuit compared across engines is built from the spec the run's *stored* configuration
    rebuilds, and that spec's marked set is first required to be the one the run stored, so the
    agreement is about the run's circuit and not about a lookalike.
    """
    run_dir, results = request.getfixturevalue(which)

    # -- the pipeline produced every section, at the width asked for -----------------------------
    assert results["search_width"] == N and results["n_items"] == 1 << N
    for section in ("spec", "circuits", "curve", "curve_fit", "probes", "classical_baseline",
                    "validation", "sweep"):
        assert results.get(section), f"{section} is missing: {results['not_run']}"
    assert set(results["not_run"]) <= {"scaling"}, results["not_run"]
    assert all(row["ok"] is True for row in results["validation"])

    spec = _spec_from_results(results)
    assert sorted(spec.marked_set()) == results["marked_set"]
    assert len(results["marked_set"]) == results["marked_set_size"]
    k_opt = results["optimal_iterations"]
    assert k_opt == math.floor(math.pi / 4 * math.sqrt((1 << N) / results["marked_set_size"]))

    # -- two engines, one gate list ---------------------------------------------------------------
    circuit = build_grover_circuit(spec, k_opt, Lowering.TRUTH_TABLE)
    assert circuit.num_qubits == N + 1
    a = np.asarray(aer.run_statevector(circuit).statevector)
    b = np.asarray(qsim.run_statevector(circuit).statevector)
    assert_backend_agreement(a, b, tol=1e-6, label=f"{spec.name} k={k_opt}")
    assert float(np.max(np.abs(a))) < 0.9, "a basis-state output would make any two engines agree"

    # Each engine's success probability is the number the run stored at k_opt — so the engines
    # agree with each other *and* with the pipeline, not merely with each other.
    stored = next(r for r in results["curve"] if r["iteration"] == k_opt)["empirical_p_success"]
    marked = np.array(results["marked_set"])
    assert float(np.sum(np.abs(a[marked]) ** 2)) == pytest.approx(stored, abs=1e-12)
    assert float(np.sum(np.abs(b[marked]) ** 2)) == pytest.approx(stored, abs=1e-5)
    assert results["curve_fit"]["peak_iteration_measured"] == k_opt
    assert results["curve_fit"]["max_abs_residual"] < 1e-12

    # -- the report, read from the run directory --------------------------------------------------
    text = _report(run_dir)
    assert text.count(SCOPE_BOUNDARY) == 1
    assert text.index(SCOPE_BOUNDARY) < text.index("|---"), "a table arrived before the boundary"
    assert text.index(SCOPE_BOUNDARY) < text.index("\n## ")
    # The title, then the boundary, then everything else: nothing is read before it.
    written = [line for line in text.splitlines() if line.strip()]
    assert written[0] == f"# Report: {results['run_id']} (experiment)"
    assert written[1] == f"> {SCOPE_BOUNDARY}"
    # It is the report of *these* results: re-rendering the stored mapping reproduces it exactly.
    assert load_results(run_dir) == results
    assert render_report(results["config"], results, figures={}, run_dir=run_dir) == text
    assert f"| marked set size M | {results['marked_set_size']} |" in text
    assert f"| search width n_search | {N} |" in text
    assert f"The measured curve peaks at `k = {k_opt}`" in text
    assert f"`M = {results['marked_set_size']}` of `N = 256` basis states" in text


def test_an_orthogonal_state_is_a_disagreement_the_gate_can_see(control_run, aer):
    """The agreement check above is a real predicate: one more round of the same circuit fails it."""
    _run_dir, results = control_run
    spec = _spec_from_results(results)
    k_opt = results["optimal_iterations"]
    at_peak = aer.run_statevector(build_grover_circuit(spec, k_opt)).statevector
    one_more = aer.run_statevector(build_grover_circuit(spec, k_opt + 1)).statevector
    with pytest.raises(AssertionError, match="engines disagree"):
        assert_backend_agreement(at_peak, one_more, tol=1e-6)


# -----------------------------------------------------------------------------------------------
# (c): the probes' verdicts, in the results and in the report
# -----------------------------------------------------------------------------------------------


def test_the_hidden_period_run_reports_that_the_simon_style_probe_fired(period_run):
    run_dir, results = period_run
    spec = _spec_from_results(results)
    assert isinstance(spec, HiddenPeriodOracleSpec)
    assert spec.period % 2 == 0 and 0 < spec.period < 1 << N, "the run draws an even period"

    by_name = {record["probe"]: record for record in results["probes"]}
    assert set(by_name) == {"simon_style", "qft_period"}
    for record in by_name.values():
        assert record["status"] == MEASURED
        assert record["fired"] is True, record["detail"]
        assert record["period_verified"] is True
        assert record["candidate_period"] == spec.period
        assert verify_period(frozenset(results["marked_set"]), N, record["candidate_period"])

    text = _report(run_dir)
    rows = _probe_rows(text)
    assert rows["simon_style"][1] == "yes" and rows["qft_period"][1] == "yes"
    assert f"for the period(s) {spec.period} " in rows["simon_style"][4]
    assert "n = 128" in rows["simon_style"][5], "a firing row still carries the caveat"
    assert "2 of 2 probes fired `[measured]`" in text
    assert "No probe fired" not in text


def test_the_random_control_run_reports_that_the_simon_style_probe_did_not_fire(control_run):
    run_dir, results = control_run
    marked = frozenset(results["marked_set"])
    assert len(marked) == 8
    assert not any(verify_period(marked, N, s) for s in range(1, 1 << N)), (
        "the control carries a period of its own, so a firing probe would be right"
    )

    for record in results["probes"]:
        assert record["status"] == MEASURED
        assert record["fired"] is False
        assert record["candidate_period"] is None and record["period_verified"] is False
        assert record["samples"] == 64

    text = _report(run_dir)
    rows = _probe_rows(text)
    assert rows["simon_style"][1] == "no" and rows["qft_period"][1] == "no"
    assert rows["simon_style"][4].startswith("not fired:")
    assert "No probe fired, over 2 probes `[measured]`" in text
    assert "probes fired `[measured]`. A firing probe" not in text
    assert "positive control (`hidden_period`)" in text


def test_the_two_reports_differ_where_the_oracles_differ_and_nowhere_in_the_boundary(
    control_run, period_run
):
    """Same harness, same width, same seed: the verdict column is the oracle's, the preamble is not."""
    control_text, period_text = _report(control_run[0]), _report(period_run[0])
    split = "## Run identity"
    assert control_text.split(split)[0].splitlines()[1:] == period_text.split(split)[0].splitlines()[1:]
    assert _probe_rows(control_text)["simon_style"][1] != _probe_rows(period_text)["simon_style"][1]


# -----------------------------------------------------------------------------------------------
# (d): the probes on real engines, handed over directly
# -----------------------------------------------------------------------------------------------


def test_both_probes_detect_the_planted_period_on_aer(hidden_period_spec, aer):
    """No test double and no adapter: the engine's own ``run_statevector`` is what the probe drives."""
    simon = simon_style_probe(hidden_period_spec, aer)
    qft = qft_period_probe(hidden_period_spec, aer)
    for result in (simon, qft):
        assert result.status == MEASURED
        assert result.fired is True, result.detail
        assert result.candidate_period == 0b100 and result.period_verified is True
        assert result.n_qubits == N and result.total_qubits == N + 1
    assert simon.probe == "simon_style" and qft.probe == "qft_period"


def test_both_probes_stay_quiet_on_the_random_control_on_aer(random_spec, aer):
    """The strong silence — the samples span the register — on the engine production runs on."""
    for result in run_probes(random_spec, aer, samples=DECISIVE_SAMPLES):
        assert result.status == MEASURED
        assert result.fired is False, result.detail
        assert result.rank == N and result.nullity == 0
        assert result.candidate_period is None
        assert "spanned the full register" in result.detail


def test_the_real_engine_and_the_test_double_return_the_same_verdict(hidden_period_spec, aer):
    """Sampling is seeded from the description of the run, so the two results match field for field."""
    from reference_statevector import ReferenceStatevector

    through_aer = [result.to_dict() for result in run_probes(hidden_period_spec, aer)]
    through_double = [
        result.to_dict() for result in run_probes(hidden_period_spec, ReferenceStatevector())
    ]
    for real, double in zip(through_aer, through_double, strict=True):
        for key in ("probe", "fired", "candidate_period", "period_verified", "samples", "n_qubits"):
            assert real[key] == double[key], key


def test_both_probes_discriminate_on_the_tensor_network_engine():
    """The contraction engine satisfies the same one-method contract, at a width it contracts quickly.

    ``n = 6`` rather than 8: every marked value is one multi-controlled gate, and a contraction plan
    over the 32-gate oracle of the eight-qubit control costs half a minute where this costs seconds.
    The control is checked to carry no period first, since six qubits is small enough for accidents.
    """
    engine = TensorNetworkBackend()
    planted = HiddenPeriodOracleSpec(n_qubits=6, period=0b100, seed=11)
    control = RandomControlOracleSpec(n_qubits=6, n_marked=8, seed=11)
    assert not any(verify_period(control.marked_set(), 6, s) for s in range(1, 1 << 6))

    for result in run_probes(planted, engine):
        assert result.status == MEASURED
        assert result.fired is True, result.detail
        assert result.candidate_period == 0b100
    for result in run_probes(control, engine, samples=DECISIVE_SAMPLES):
        assert result.status == MEASURED
        assert result.fired is False, result.detail
        assert result.nullity == 0 and result.candidate_period is None


def test_the_probes_accept_the_single_precision_engine_too(hidden_period_spec, qsim):
    """``cirq_qsim`` is a configurable engine, so the analysis layer has to be drivable by it."""
    results = run_probes(hidden_period_spec, qsim)
    assert [result.fired for result in results] == [True, True]
    assert [result.candidate_period for result in results] == [0b100, 0b100]


# -----------------------------------------------------------------------------------------------
# (e): the sample-count rule, including the arm no simulated width reaches
# -----------------------------------------------------------------------------------------------


def test_the_default_sample_count_is_four_per_qubit_above_sixteen_qubits():
    """``max(4n, 64)``: the floor holds through ``n = 16`` and the ``4n`` arm takes over at 17."""
    assert [_default_samples(n) for n in (1, 8, 12, 16)] == [64, 64, 64, 64]
    assert _default_samples(17) == 68
    assert _default_samples(20) == 80
    assert _default_samples(128) == 512
    for n in range(1, 40):
        assert _default_samples(n) == max(4 * n, 64)
        assert _default_samples(n + 1) >= _default_samples(n)
    # The two arms meet exactly at sixteen, so neither is dead code on either side of it.
    assert 4 * 16 == 64 and _default_samples(17) - _default_samples(16) == 4


def test_a_probe_at_twenty_qubits_would_have_drawn_eighty_samples(aer):
    """The ``4n`` arm through the public probe, without simulating anything.

    A width ceiling below the circuit makes the probe refuse before it builds a statevector, and a
    refusal records the count it *would* have drawn in its caveat — so the rule is observed at
    ``n = 20`` for the price of drawing one marked value.
    """
    spec = RandomControlOracleSpec(n_qubits=20, n_marked=1, seed=3)
    result = qft_period_probe(spec, aer, max_total_qubits=8)
    assert result.status == NOT_RUN and result.fired is False
    assert result.samples == 0, "nothing was drawn, and the record says so"
    assert "The 80 sample(s) a run would have drawn" in result.caveat
    assert "n_search = 20" in result.caveat
