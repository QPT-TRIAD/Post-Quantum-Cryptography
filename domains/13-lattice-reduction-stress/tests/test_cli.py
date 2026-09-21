"""The command-line surface: every command reachable, and the pipeline callable without one."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from qlwr_lattice_stress.cli import app
from qlwr_lattice_stress.config.schema import load_config

runner = CliRunner()
REPO = Path(__file__).resolve().parents[1]


def small_config(tmp_path: Path) -> Path:
    """A config small enough to run inside a test, at the calibrated dimension."""
    path = tmp_path / "small.yaml"
    path.write_text(yaml.safe_dump({
        "instance": {"source": "synthetic_scaled", "target_dimension": 76, "seed": 20260913},
        "engine": {"preference": ["fpylll_bkz"], "threads": 1},
        "attack": {"types": ["primal"], "block_size_range": [2, 20, 30]},
        "sweep": {"dimension_range": [40, 76]},
        "cost_model": {"use_lattice_estimator": False},
        "output": {"dir": str(tmp_path / "results")},
    }, sort_keys=False))
    return path


def test_the_cli_exposes_every_command():
    out = runner.invoke(app, ["--help"]).stdout
    for command in ("probe", "run", "sweep", "report", "planted-check", "estimate"):
        assert command in out, command


def test_planted_check_runs_and_reports_membership():
    result = runner.invoke(app, ["planted-check", "--dimension", "40"])
    assert result.exit_code == 0, result.stdout
    assert "membership" in result.stdout
    assert "embedding factor" in result.stdout


def test_the_shipped_config_loads_through_the_cli_path():
    cfg = load_config(REPO / "config" / "default_experiment.yaml")
    assert cfg.attack.block_size_range[0] == 10


@pytest.mark.slow
def test_run_produces_a_report_with_the_boundary(tmp_path):
    from qlwr_lattice_stress.reporting import SCOPE_BOUNDARY, assert_boundary_precedes_first_table

    config = small_config(tmp_path)
    result = runner.invoke(app, ["run", "--config", str(config)])
    assert result.exit_code == 0, result.stdout

    run_dirs = list((tmp_path / "results").iterdir())
    assert len(run_dirs) == 1
    report = (run_dirs[0] / "report.md").read_text()
    assert SCOPE_BOUNDARY in report
    assert_boundary_precedes_first_table(report)
    # The config is written beside the results, so a run is reproducible from its own directory.
    assert (run_dirs[0] / "config.yaml").exists()
    assert (run_dirs[0] / "metrics.json").exists()


@pytest.mark.slow
def test_report_regenerates_from_the_run_directory(tmp_path):
    """The round trip: a report produced from what a run recorded must carry the same boundary."""
    from qlwr_lattice_stress.reporting import SCOPE_BOUNDARY

    config = small_config(tmp_path)
    runner.invoke(app, ["run", "--config", str(config)])
    run_dir = next((tmp_path / "results").iterdir())

    result = runner.invoke(app, ["report", str(run_dir)])
    assert result.exit_code == 0, result.stdout
    assert SCOPE_BOUNDARY in (run_dir / "report.md").read_text()


def test_metrics_json_is_serialisable(tmp_path):
    """Sage Integers print and compare like ints and are not JSON-serialisable, so the failure
    would otherwise surface at the reporting boundary — after a run has completed and its results
    cannot be written."""
    from qlwr_lattice_stress.analysis.cost_estimation import estimate, reference_parameter_set

    report = estimate(reference_parameter_set("Kyber512"))
    json.dumps({"beta": report.beta_usvp})  # raises if it is still a Sage Integer
    assert isinstance(report.beta_usvp, int)
