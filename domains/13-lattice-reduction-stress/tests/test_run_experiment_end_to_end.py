"""``run_experiment`` and ``run_sweep``, called — the design document's milestone 11.

*"``tests/test_end_to_end.py`` on a small config (dimension 60, block sizes up to 30) — full
pipeline, asserting a report is produced with the mandatory scope-boundary preamble and all three
result sections clearly separated."* The existing end-to-end file assembles the pipeline by hand and
never calls ``run_experiment``; the CLI test that does call it turns the estimator and the dual
attack off and asserts that three files exist. So the function every command and script wraps had no
test of what it *writes*, and ``run_sweep`` had never been executed by the suite at all.

One real run at exactly the milestone's scale — dimension 60, block sizes 10/20/30, primal and dual,
estimator on, enumeration engine, one thread — is shared by the tests of its record. The smaller
runs further down each exist for one branch the shared run does not reach.

**Some tests here were expected to fail, and said so.** Each was ``xfail(strict=True)`` on a
behaviour the design document or the config's own comments promise and the pipeline did not
perform. They were strict so that the fix turned them into an error until the marker was removed —
which happened on 2026-09-20: the pipeline was corrected, the markers are gone, and the test bodies
are unchanged. ``notes/10-test-completion-audit.md`` lists each defect and its fix.

Nothing here writes outside ``tmp_path``: the repository's ``results/`` tree is evidence the notes
cite, not scratch space.
"""

from __future__ import annotations

import builtins
import json
import logging
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from qlwr_lattice_stress.analysis.hermite_factor import achieved_root_hermite_factor
from qlwr_lattice_stress.attacks import prepare_primal
from qlwr_lattice_stress.config.schema import (
    EngineSettings,
    ExperimentConfig,
    dump_config,
    load_config,
)
from qlwr_lattice_stress.engines import FpylllBKZEngine
from qlwr_lattice_stress.engines.base_engine import RamBudgetExceeded
from qlwr_lattice_stress.engines.engine_selector import DEFAULT_THREADS
from qlwr_lattice_stress.engines.g6k_sieve_engine import G6KSieveEngine
from qlwr_lattice_stress.pipeline import build_instance, run_experiment, run_sweep
from qlwr_lattice_stress.problem.normal_form import to_normal_form
from qlwr_lattice_stress.protocols import EXTRAPOLATED, MEASURED, NOT_RUN, SAME_SCALE
from qlwr_lattice_stress.reporting import SCOPE_BOUNDARY, assert_boundary_precedes_first_table
from qlwr_lattice_stress.utils.seeding import RunSeeds

REPO = Path(__file__).resolve().parents[1]
SHIPPED_CONFIG = REPO / "config" / "default_experiment.yaml"
SRC = REPO / "src" / "qlwr_lattice_stress"
SELECTOR_LOGGER = "qlwr_lattice_stress.engines.engine_selector"
SEED = 20260913


def make_config(output_dir: Path, **sections) -> ExperimentConfig:
    """The milestone-11 config, with any section's keys overridden.

    Enumeration only and one thread unless a test says otherwise: one thread because it is the only
    reproducible setting, enumeration because the tests that want G6K absent must not depend on it
    being present.
    """
    document: dict = {
        "instance": {"source": "synthetic_scaled", "target_dimension": 60, "seed": SEED},
        "engine": {"preference": ("fpylll_bkz",), "threads": 1},
        "attack": {"types": ("primal", "dual"), "block_size_range": (10, 20, 30)},
        "sweep": {"dimension_range": (40, 50)},
        "cost_model": {"use_lattice_estimator": True},
        "output": {"dir": output_dir},
    }
    for section, values in sections.items():
        document[section] = {**document[section], **values}
    return ExperimentConfig.model_validate(document)


def small_config(output_dir: Path, **sections) -> ExperimentConfig:
    """Dimension 40 with the estimator off — for the branches that need a run, not this run."""
    sections.setdefault("instance", {}).setdefault("target_dimension", 40)
    sections.setdefault("cost_model", {}).setdefault("use_lattice_estimator", False)
    return make_config(output_dir, **sections)


def _tree(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*")} if root.exists() else set()


@pytest.fixture(autouse=True)
def the_shipped_results_tree_is_not_written(request):
    before = _tree(REPO / "results")
    yield
    assert _tree(REPO / "results") == before, f"{request.node.name} wrote into the shipped results"


@pytest.fixture(scope="module")
def full_config(tmp_path_factory) -> ExperimentConfig:
    return make_config(tmp_path_factory.mktemp("milestone-11"))


@pytest.fixture(scope="module")
def full_run(full_config) -> dict:
    """The one real run at the milestone's scale. Skips where the estimator is absent, as the cost
    estimation tests do — the comparison is half of what this run is for."""
    pytest.importorskip("estimator", reason="lattice-estimator is not importable")
    return run_experiment(full_config)


@pytest.fixture(scope="module")
def metrics(full_run) -> dict:
    """What is on disk, which is what a later reader has — not the mapping that was returned."""
    return json.loads((Path(full_run["run_dir"]) / "metrics.json").read_text())


def _primal(record: dict) -> list[dict]:
    return [a for a in record["attacks"] if a["family"] == "primal_usvp"]


def _dual(record: dict) -> dict:
    (row,) = [a for a in record["attacks"] if a["family"] == "dual"]
    return row


# ---------------------------------------------------------------------------------------------
# the record a full run leaves
# ---------------------------------------------------------------------------------------------


def test_the_run_directory_holds_the_metrics_the_report_and_the_config(full_run, full_config):
    run_dir = Path(full_run["run_dir"])
    assert run_dir == Path(full_config.output.dir) / f"synthetic_scaled-d60-s{SEED}"
    assert sorted(p.name for p in run_dir.iterdir()) == ["config.yaml", "metrics.json", "report.md"]


def test_metrics_json_has_the_documented_top_level_keys(metrics, full_run):
    expected = {
        "run_id", "created_utc", "seed", "config", "not_run", "notes",
        "instance", "attacks", "minimum_block_sizes",
        "estimator_same_scale", "comparisons", "seeds", "environment",
    }
    assert expected <= set(metrics), expected - set(metrics)
    assert set(metrics) - expected <= {"scaling"}, set(metrics) - expected
    # ``run_dir`` is added to the returned mapping after the file is written; everything else the
    # caller was handed is what the file holds.
    assert set(full_run) - set(metrics) == {"run_dir"}
    assert metrics["run_id"] == f"synthetic_scaled-d60-s{SEED}"
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", metrics["created_utc"])


def test_the_instance_is_the_scaled_one_the_config_names(metrics):
    instance = metrics["instance"]
    assert instance["label"] == "synthetic_scaled"
    assert instance["m"] == instance["qary_lattice_dimension"] == 60
    assert instance["nu"] == round(60 * 256 / 608) == 25
    assert (instance["q_l"], instance["p"]) == (1 << 16, 1 << 8)
    assert instance["usvp_lattice_dimension"] == 61


def test_every_primal_point_is_a_measurement_with_its_engine_time_and_quality(metrics):
    """Measured block size, Hermite factor and wall clock — the three things the design document's
    section 3 is made of — plus what decides whether the row is reproducible."""
    rows = _primal(metrics)
    assert rows, "the run recorded no primal point"
    for row in rows:
        assert row["provenance"] == MEASURED and row["not_run_reason"] is None
        assert row["block_size"] in (10, 20, 30)
        assert row["dimension"] == 61
        assert (row["engine"], row["threads"]) == ("fpylll_bkz", 1)
        assert row["wall_clock_s"] > 0
        assert isinstance(row["root_hermite_factor"], float) and row["root_hermite_factor"] > 0
        assert isinstance(row["recovered"], bool)
    sizes = [row["block_size"] for row in rows]
    assert sizes == sorted(sizes), "the sweep is documented as ascending"


def test_the_minimum_block_size_is_the_first_point_that_recovered(metrics):
    rows = _primal(metrics)
    minimum = metrics["minimum_block_sizes"]["primal_usvp"]
    assert minimum is not None, "nothing recovered at dimension 60 within block size 30"
    recovered = [row["block_size"] for row in rows if row["recovered"]]
    assert minimum == min(recovered)
    assert all(not row["recovered"] for row in rows if row["block_size"] < minimum)
    assert metrics["minimum_block_sizes"]["dual"] is None


def test_the_recorded_hermite_factor_is_the_root_hermite_factor(metrics, full_config):
    """Re-derived independently: the same instance, the same engine at one thread (bit-reproducible),
    and the *analysis* layer's exact-integer metric on the basis that comes back."""
    row = next(r for r in _primal(metrics) if r["recovered"])
    instance = build_instance(full_config, RunSeeds(root=SEED))
    _, _, basis, _ = prepare_primal(instance)
    reduced = FpylllBKZEngine(threads=1).reduce(basis, row["block_size"])
    assert row["root_hermite_factor"] == pytest.approx(
        achieved_root_hermite_factor(reduced.basis), rel=1e-4
    )


def test_the_estimate_is_for_the_instance_that_was_attacked(metrics):
    """"Same scale" is the claim; the parameters the estimator was handed are the evidence."""
    report = metrics["estimator_same_scale"]
    assert report["provenance"] == SAME_SCALE
    parameters = report["model_parameters"]
    assert (parameters["n"], parameters["q"], parameters["m"]) == (
        metrics["instance"]["nu"], metrics["instance"]["q_l"], metrics["instance"]["m"]
    )
    assert isinstance(report["beta_usvp"], int) and 2 <= report["beta_usvp"] <= 61
    assert report["rop_quantum_log2_min"] < report["rop_classical_log2_min"]
    assert metrics["environment"]["estimator_revision"] == report["estimator_revision"]


def test_the_comparison_sets_the_measurement_beside_the_prediction(metrics):
    by_dimension = {c["dimension"]: c for c in metrics["comparisons"]}
    assert set(by_dimension) == {61, 35}, "one comparison per family, at that family's own width"

    primal = by_dimension[61]
    assert primal["measured_min_block_size"] == metrics["minimum_block_sizes"]["primal_usvp"]
    assert primal["predicted_min_block_size"] == metrics["estimator_same_scale"]["beta_usvp"]
    assert primal["discrepancy"] == pytest.approx(
        (primal["measured_min_block_size"] - primal["predicted_min_block_size"])
        / primal["predicted_min_block_size"]
    )
    # Silence is the failure: outside tolerance there must be words, inside it there must not.
    for comparison in metrics["comparisons"]:
        outside = abs(comparison["discrepancy"]) > comparison["tolerance"]
        assert bool(comparison["anomaly"]) == outside, comparison


def test_the_dual_attack_is_recorded_at_the_dual_lattices_own_dimension(metrics, full_config):
    """35 wide, not 61: the dual lattice lives in Z^(m - nu). Here the configured maximum (30) fits,
    so the block size is the configured one — the clamp itself is tested below, where it bites."""
    nf = to_normal_form(build_instance(full_config, RunSeeds(root=SEED)))
    row = _dual(metrics)
    assert row["dimension"] == nf.m == 35
    assert row["block_size"] == 30
    assert row["provenance"] in (MEASURED, NOT_RUN)
    if row["provenance"] == NOT_RUN:
        assert row["not_run_reason"]
        assert {"step": "dual attack", "reason": row["not_run_reason"]} in metrics["not_run"]
        assert "exceeds" not in row["not_run_reason"], "refused on a block-size limit, not on merit"


def test_a_block_size_range_wider_than_the_dual_lattice_is_clamped_to_it(tmp_path):
    """At dimension 40 the dual lattice is 23 wide and the range reaches 30. Unclamped, the engine
    refuses the request on a limit that has nothing to do with the attack."""
    config = small_config(tmp_path)
    nf = to_normal_form(build_instance(config, RunSeeds(root=SEED)))
    assert nf.m < max(config.attack.block_size_range), "the fixture no longer exercises the clamp"

    row = _dual(run_experiment(config))
    assert row["block_size"] == row["dimension"] == nf.m == 23
    assert "exceeds the basis dimension" not in (row["not_run_reason"] or "")
    assert row["wall_clock_s"] > 0, "the dual reduction never ran"


def test_the_config_is_written_beside_the_results_and_reloads_to_the_same_object(
    full_run, full_config, metrics
):
    reloaded = load_config(Path(full_run["run_dir"]) / "config.yaml")
    assert reloaded == full_config
    assert metrics["config"] == dump_config(full_config)
    assert metrics["config"]["engine"]["threads"] == 1


def test_the_seeds_and_the_toolchain_are_recorded(metrics):
    assert metrics["seed"] == metrics["seeds"]["root"] == SEED
    derived = [tuple(d["parts"]) for d in metrics["seeds"]["derived"]]
    assert ("instance", "synthetic_scaled", 60) in derived
    assert {"python", "fpylll", "g6k", "estimator_revision"} <= set(metrics["environment"])


def test_what_did_not_run_is_recorded_with_a_reason(metrics):
    """One measured primal point cannot support a fit, and the run says so rather than omitting it."""
    steps = {entry["step"]: entry["reason"] for entry in metrics["not_run"]}
    assert "scaling" not in metrics
    assert "needs at least 3" in steps["scaling fit"]
    assert all(reason for reason in steps.values())


def test_the_report_has_the_boundary_and_the_three_result_sections_apart(full_run, metrics):
    text = (Path(full_run["run_dir"]) / "report.md").read_text()
    assert_boundary_precedes_first_table(text)

    headings = [
        "## 3. Empirical results — measured",
        "## 4. Cost model at the same scale — theoretical, same scale",
        "## 5. Production-scale extrapolation — extrapolated — not measured",
    ]
    positions = [text.index(SCOPE_BOUNDARY)] + [text.index(h) for h in headings]
    assert positions == sorted(positions)
    assert all(text.count(h) == 1 for h in headings)

    measured, theoretical, extrapolated = (
        text.split(h, 1)[1].split("\n## ", 1)[0] for h in headings
    )
    minimum = metrics["minimum_block_sizes"]["primal_usvp"]
    assert f"| primal_usvp | {minimum} | 61 | fpylll_bkz ×1 | measured | yes |" in measured
    assert f"| usvp block size | {metrics['estimator_same_scale']['beta_usvp']} |" in theoretical
    assert "usvp block size" not in measured and "fpylll_bkz" not in theoretical
    assert "_No fit was produced for this run._" in extrapolated


def test_the_same_config_reproduces_the_same_record(tmp_path):
    """Everything but the clock. One thread and a recorded seed are supposed to be sufficient."""
    def record(where: Path) -> list[dict]:
        attacks = run_experiment(small_config(where))["attacks"]
        return [{k: v for k, v in a.items() if k != "wall_clock_s"} for a in attacks]

    assert record(tmp_path / "a") == record(tmp_path / "b")


# ---------------------------------------------------------------------------------------------
# the engine fallback, through the pipeline
# ---------------------------------------------------------------------------------------------


@pytest.fixture
def g6k_unavailable(monkeypatch):
    """The environment, not the unit: G6K reports itself absent, as it does where it was never
    built. ``available()`` is derived from ``unavailable_reason()``, so this is the single switch."""
    monkeypatch.setattr(G6KSieveEngine, "unavailable_reason", lambda self: "not built (test)")
    assert G6KSieveEngine().available() is False


def test_the_pipeline_falls_back_to_enumeration_and_says_so(tmp_path, caplog, g6k_unavailable):
    config = small_config(tmp_path, engine={"preference": ("g6k", "fpylll_bkz")})
    with caplog.at_level(logging.INFO):
        results = run_experiment(config)

    rows = _primal(results)
    assert rows and all(row["provenance"] == MEASURED for row in rows)
    assert {row["engine"] for row in rows} == {"fpylll_bkz"}, "a row is labelled with an engine that did not run"

    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("g6k" in w and "fpylll_bkz" in w for w in warnings), (
        f"the substitution was silent; warnings were {warnings}"
    )


def test_a_config_that_names_only_g6k_is_not_quietly_run_on_something_else(tmp_path, g6k_unavailable):
    """The other half of "never silently": with no fallback named, the run must not produce
    enumeration rows. Refusing loudly is correct; so would be a not-run record."""
    config = small_config(tmp_path, engine={"preference": ("g6k",)})
    try:
        results = run_experiment(config)
    except RuntimeError as exc:
        assert "g6k" in str(exc)
        return
    assert not [row for row in _primal(results) if row["provenance"] == MEASURED]


def test_enumeration_only_mode_never_touches_g6k(tmp_path, monkeypatch):
    """The design document's reduced-scope mode, spelled ``preference: [fpylll_bkz]`` here. G6K is
    made unimportable *and* its engine unconstructible, so the run completing is the proof."""
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "g6k" or name.startswith("g6k."):
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return real_import(name, *args, **kwargs)

    def must_not_be_built(self, *args, **kwargs):
        raise AssertionError("an enumeration-only run constructed the sieving engine")

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(G6KSieveEngine, "__init__", must_not_be_built)

    results = run_experiment(small_config(tmp_path))
    rows = _primal(results)
    assert rows and {row["engine"] for row in rows} == {"fpylll_bkz"}
    assert results["minimum_block_sizes"]["primal_usvp"] is not None
    assert results["environment"]["g6k"] == "absent"
    assert (Path(results["run_dir"]) / "report.md").is_file()


# ---------------------------------------------------------------------------------------------
# config fields the pipeline is supposed to obey
# ---------------------------------------------------------------------------------------------


def test_a_run_over_its_ram_budget_is_refused_before_any_reduction(tmp_path):
    """The enumeration engine's estimate starts at the interpreter baseline (~90 MiB), so a budget
    of one MiB is exceeded at every block size. Raising and recording are both acceptable refusals;
    a measured point is not."""
    config = small_config(tmp_path, engine={"ram_budget_gb": 1 / 1024})
    assert FpylllBKZEngine().estimate_memory_bytes(10) > (1 << 20)

    try:
        results = run_experiment(config)
    except RamBudgetExceeded:
        return
    measured = [row for row in results["attacks"] if row["provenance"] == MEASURED]
    assert not measured, f"{len(measured)} point(s) ran over a 1 MiB budget"
    assert any("budget" in entry["reason"] for entry in results["not_run"])


def test_a_json_only_run_writes_no_markdown_report(tmp_path):
    results = run_experiment(small_config(tmp_path, output={"formats": ("json",)}))
    run_dir = Path(results["run_dir"])
    assert (run_dir / "metrics.json").is_file()
    assert not (run_dir / "report.md").exists()


def test_a_run_that_asks_for_png_gets_a_figure(tmp_path):
    from qlwr_lattice_stress.reporting import figure_paths

    results = run_experiment(small_config(tmp_path, output={"formats": ("markdown", "json", "png")}))
    figures = figure_paths(results["run_dir"])
    assert figures and all(path.suffix == ".png" for path in figures)


@pytest.mark.parametrize(
    ("section", "field"),
    [
        pytest.param("engine", "threads", id="engine.threads"),
        pytest.param("attack", "max_seconds_per_block_size", id="attack.max_seconds_per_block_size"),
        pytest.param("engine", "ram_budget_gb", id="engine.ram_budget_gb"),
        pytest.param("engine", "gauss_crossover", id="engine.gauss_crossover"),
        pytest.param("attack", "search_beyond_prediction", id="attack.search_beyond_prediction"),
        pytest.param("output", "formats", id="output.formats"),
    ],
)
def test_a_config_field_is_either_consumed_or_not_offered(section, field):
    """A static check, deliberately: behaviour tests above cover the two fields whose effect is
    specified, and this covers the rest without inventing a specification for them. Removing a field
    from the schema satisfies it as well as wiring it in does. The two unmarked cases are the
    control — fields that *are* read — so the search is shown to find what exists."""
    if field not in getattr(ExperimentConfig(), section).__class__.model_fields:
        return
    readers = [
        str(path.relative_to(SRC)) for path in SRC.rglob("*.py")
        if path.name != "schema.py" and re.search(rf"\.{section}\.{field}\b", path.read_text())
    ]
    assert readers, f"config.{section}.{field} is read nowhere outside the schema"


# ---------------------------------------------------------------------------------------------
# run_sweep
# ---------------------------------------------------------------------------------------------


def _check_one_entry_per_dimension(outcomes: list[dict], dimensions: tuple[int, ...], root: Path):
    assert [o["instance"]["qary_lattice_dimension"] for o in outcomes] == list(dimensions)
    run_dirs = [Path(o["run_dir"]) for o in outcomes]
    assert len(set(run_dirs)) == len(dimensions) and all(d.parent == root for d in run_dirs)
    for outcome in outcomes:
        assert outcome.get("provenance") != NOT_RUN
        assert outcome["minimum_block_sizes"]["primal_usvp"] is not None


def test_a_two_dimension_sweep_runs_both_and_refuses_the_fit(tmp_path):
    config = small_config(tmp_path, sweep={"dimension_range": (40, 50)})
    outcomes = run_sweep(config)
    _check_one_entry_per_dimension(outcomes, (40, 50), tmp_path)

    for outcome in outcomes:
        assert "scaling" not in outcome, "two points determine a line; a fit through them is not a result"
        refusals = [e["reason"] for e in outcome["not_run"] if e["step"] == "scaling fit"]
        assert any("2 dimension(s)" in r and "needs at least 3" in r for r in refusals), refusals
        report = (Path(outcome["run_dir"]) / "report.md").read_text()
        assert "_No fit was produced for this run._" in report


def test_the_sweeps_refusal_to_fit_is_in_the_stored_record_too(tmp_path):
    outcomes = run_sweep(small_config(tmp_path, sweep={"dimension_range": (40, 50)}))
    for outcome in outcomes:
        stored = json.loads((Path(outcome["run_dir"]) / "metrics.json").read_text())
        assert any("dimension(s) reached a minimum" in e["reason"] for e in stored["not_run"])


def test_a_three_dimension_sweep_fits_and_labels_the_two_halves(tmp_path):
    """The fit is produced, its measured half is made of the sweep's own minima, and the half that
    goes beyond them says ``extrapolated`` — in the mapping, on disk and in the report."""
    dimensions = (40, 50, 60)
    config = small_config(tmp_path, sweep={"dimension_range": dimensions})
    outcomes = run_sweep(config)
    _check_one_entry_per_dimension(outcomes, dimensions, tmp_path)

    minima = [[d, o["minimum_block_sizes"]["primal_usvp"]] for d, o in zip(dimensions, outcomes)]
    for outcome in outcomes:
        scaling = outcome["scaling"]
        assert scaling["kind"] == "block_size_growth"
        assert [list(p) for p in scaling["measured"]["points"]] == minima
        assert scaling["measured"]["n_points"] == 3
        assert "provenance" not in scaling["measured"] or scaling["measured"]["provenance"] == MEASURED

        beyond = scaling["extrapolated"]
        assert beyond["provenance"] == EXTRAPOLATED
        assert beyond["target_dimension"] == max(dimensions)
        assert beyond["core_svp_log2_cost"] == pytest.approx(
            beyond["core_svp_c"] * beyond["predicted_block_size"], abs=5e-3
        )

        run_dir = Path(outcome["run_dir"])
        stored = json.loads((run_dir / "metrics.json").read_text())
        assert stored["scaling"]["extrapolated"]["provenance"] == EXTRAPOLATED
        section = (run_dir / "report.md").read_text().split("## 5.", 1)[1].split("\n## ", 1)[0]
        assert section.startswith(" Production-scale extrapolation — extrapolated — not measured")
        assert "first five rows are **measured**" in section
        assert f"| core-SVP log2 cost there | {beyond['core_svp_log2_cost']:.4g} |" in section


# ---------------------------------------------------------------------------------------------
# published_reference
# ---------------------------------------------------------------------------------------------


def test_a_published_reference_is_estimated_and_never_attacked(tmp_path, monkeypatch):
    pytest.importorskip("estimator", reason="lattice-estimator is not importable")
    from qlwr_lattice_stress import pipeline

    def no_attack(*args, **kwargs):
        raise AssertionError("a published reference set reached the lattice-attack path")

    for name in ("build_engine", "build_instance", "find_minimum_successful_block_size",
                 "run_dual_attack"):
        monkeypatch.setattr(pipeline, name, no_attack)

    config = make_config(
        tmp_path, instance={"source": "published_reference", "reference_scheme": "Kyber512"}
    )
    results = run_experiment(config)

    assert results["instance"] == {"label": "published_reference", "scheme": "Kyber512"}
    assert results["estimator_same_scale"]["beta_usvp"] == 406, "the pinned Kyber512 baseline"
    assert results["estimator_same_scale"]["rop_classical_log2_min"] > 100
    for absent in ("attacks", "minimum_block_sizes", "comparisons", "scaling"):
        assert absent not in results
    assert any("No lattice attack runs" in note for note in results["notes"])

    run_dir = Path(results["run_dir"])
    assert run_dir.name == f"published_reference-d60-s{SEED}"
    stored = json.loads((run_dir / "metrics.json").read_text())
    assert "attacks" not in stored and stored["estimator_same_scale"]["beta_usvp"] == 406
    report = (run_dir / "report.md").read_text()
    assert "_No attack points were recorded._" in report and "| usvp block size | 406 |" in report


def test_an_unknown_published_scheme_is_refused_with_the_known_ones(tmp_path):
    config = make_config(
        tmp_path, instance={"source": "published_reference", "reference_scheme": "Kyber513"}
    )
    with pytest.raises(ValueError, match="Kyber513") as exc:
        run_experiment(config)
    assert "Kyber512" in str(exc.value) and "Dilithium2_MSIS_WkUnf" in str(exc.value)
    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------------------------
# long_run_opt_in: the boundaries
# ---------------------------------------------------------------------------------------------


def _validates(document: dict) -> bool:
    try:
        ExperimentConfig.model_validate(document)
    except ValidationError as exc:
        assert "long_run_opt_in" in str(exc), exc
        return False
    return True


def test_dimension_200_is_allowed_and_201_needs_the_opt_in():
    assert _validates({"sweep": {"dimension_range": (40, 200)}})
    assert not _validates({"sweep": {"dimension_range": (40, 201)}})
    assert _validates({"sweep": {"dimension_range": (40, 201), "long_run_opt_in": True}})


def test_a_block_size_at_the_configured_ceiling_is_allowed_and_one_above_is_not():
    """The mechanism, at a ceiling the test sets — so it holds whatever the default is."""
    engine = {"sieve_block_size_max": 30}
    assert _validates({"engine": engine, "attack": {"block_size_range": (10, 30)}})
    assert not _validates({"engine": engine, "attack": {"block_size_range": (10, 31)}})
    assert _validates({"engine": engine, "attack": {"block_size_range": (10, 31)},
                       "sweep": {"long_run_opt_in": True}})


def test_block_size_60_needs_no_opt_in():
    assert _validates({"attack": {"block_size_range": (10, 60)}})


def test_block_size_61_needs_the_opt_in_by_default():
    assert EngineSettings().sieve_block_size_max == 60
    assert not _validates({"attack": {"block_size_range": (10, 61)}})
    assert _validates({"attack": {"block_size_range": (10, 61)}, "sweep": {"long_run_opt_in": True}})


# ---------------------------------------------------------------------------------------------
# the thread default
# ---------------------------------------------------------------------------------------------


def test_the_schema_thread_default_is_the_reproducible_one_the_yaml_ships():
    shipped = load_config(SHIPPED_CONFIG).engine.threads
    assert shipped == 1
    assert EngineSettings().threads == shipped
    assert ExperimentConfig().engine.threads == shipped


def test_the_selector_thread_default_is_the_reproducible_one_too():
    shipped = load_config(SHIPPED_CONFIG).engine.threads
    assert DEFAULT_THREADS == shipped == 1
    assert G6KSieveEngine().default_threads == shipped
