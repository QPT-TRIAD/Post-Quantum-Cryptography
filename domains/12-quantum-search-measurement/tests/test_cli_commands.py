"""The ``sweep`` and ``probe`` commands, invoked as commands.

``tests/test_cli.py`` drives ``run`` and ``report`` through :class:`typer.testing.CliRunner`, and
calls :func:`run_sweep` as a function; the two remaining commands are only ever asked for ``--help``.
A command's own layer is thin but it is not nothing — option names, the default results directory,
the exit status, what is printed for a caller to pick up, and what happens when the configuration
cannot be loaded — and none of it is reached by calling the function behind it.

So everything here goes through ``app``: a tiny configuration is written to ``tmp_path``, the command
is invoked with real arguments, and the assertions are about the process-level contract —

* exit status zero, with the report's path as the last line of output;
* the results directory holds the configuration echo, ``metrics.json``, and a ``report.md`` whose
  scope boundary comes before its first table;
* refusals are a *result* (status zero), while a configuration that cannot be loaded is a *failure*
  (status one) that names what was wrong, leaves no traceback, and writes nothing.

The sweep runs the corpus's key map at three widths because it is the cheapest oracle with an
arithmetic lowering: three measured gate counts, so the command is also seen producing a fit.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from grover_emulator.cli import app
from grover_emulator.config.schema import load_config
from grover_emulator.reporting.report_generator import SCOPE_BOUNDARY, load_results
from grover_emulator.utils import api_probe

WIDTHS = [4, 6, 8]
"""Key-map mode A searches two bits per variable: maps over two, three and four variables."""


def _write_config(directory: Path, name: str = "tiny.yaml", **sections) -> Path:
    """A small key-map configuration whose own ``output.dir`` is inside ``directory``."""
    body = {
        "run": {"seed": 77},
        "oracle": {"type": "key_map", "target_qubits": 8, "key_map_mode": "A"},
        "sweep": {"qubit_range": list(WIDTHS), "iteration_range": None},
        "backend": {"shots": 100},
        "output": {"dir": (directory / "configured-results").as_posix()},
    }
    for section, values in sections.items():
        body.setdefault(section, {}).update(values)
    path = directory / name
    path.write_text(yaml.safe_dump(body, sort_keys=True), encoding="utf-8")
    return path


def _reported_run_dir(output: str) -> Path:
    """The results directory a command announced: the parent of the last ``report.md`` line."""
    written = [line for line in output.splitlines() if line.endswith("report.md")]
    assert written, output
    return Path(written[-1]).parent


# -----------------------------------------------------------------------------------------------
# sweep
# -----------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sweep_invocation(tmp_path_factory):
    """``cli sweep --config ... --output-dir ... --run-id ...``, executed once for the module."""
    root = tmp_path_factory.mktemp("cli-sweep")
    config = _write_config(root)
    result = CliRunner().invoke(
        app,
        ["sweep", "--config", str(config), "--output-dir", str(root / "out"), "--run-id", "tiny-sweep"],
    )
    return root, config, result


def test_the_sweep_command_exits_zero_and_prints_where_the_report_went(sweep_invocation):
    root, _config, result = sweep_invocation
    assert result.exit_code == 0, result.output
    assert result.exception is None
    assert _reported_run_dir(result.output) == root / "out" / "tiny-sweep"
    assert result.output.rstrip().splitlines()[-1] == str(root / "out" / "tiny-sweep" / "report.md")


def test_the_sweep_command_writes_the_artefacts_a_run_is_read_from(sweep_invocation):
    root, _config, result = sweep_invocation
    run_dir = _reported_run_dir(result.output)
    for name in ("config.yaml", "metrics.json", "report.md"):
        assert (run_dir / name).is_file(), f"{name} is missing from {run_dir}"
    figures = sorted(path.name for path in (run_dir / "figures").glob("*.png"))
    assert "gate_scaling.png" in figures
    # The explicit --output-dir won: the configuration's own output.dir was never created.
    assert not (root / "configured-results").exists()


def test_the_configuration_copy_is_the_configuration_the_command_was_given(sweep_invocation):
    """The echo re-loads through the schema to the same validated configuration as the input file."""
    _root, config, result = sweep_invocation
    run_dir = _reported_run_dir(result.output)
    echo = run_dir / "config.yaml"
    assert load_config(echo) == load_config(config)
    assert str(config) in echo.read_text(encoding="utf-8").splitlines()[0]
    stored = yaml.safe_load(echo.read_text(encoding="utf-8"))
    assert stored["run"]["seed"] == 77
    assert stored["sweep"]["qubit_range"] == WIDTHS


def test_the_metrics_file_is_a_sweep_with_a_row_per_width_and_a_fit(sweep_invocation):
    _root, config, result = sweep_invocation
    stored = load_results(_reported_run_dir(result.output))
    assert stored["kind"] == "sweep" and stored["run_id"] == "tiny-sweep"
    assert stored["seed"] == 77 and stored["config_path"] == str(config)
    assert [row["n_search"] for row in stored["sweep"]] == WIDTHS
    assert [row["status"] for row in stored["sweep"]] == ["measured"] * 3
    assert all(row["gate_count"] > 0 and row["n_marked"] >= 1 for row in stored["sweep"])
    assert "curve" not in stored, "a sweep counts circuits; it does not execute them"
    assert stored["scaling"]["measured_points_used"] == 3
    assert stored["seed_record"]["root"] == 77


def test_the_sweep_report_states_the_boundary_before_its_first_table(sweep_invocation):
    _root, _config, result = sweep_invocation
    text = (_reported_run_dir(result.output) / "report.md").read_text(encoding="utf-8")
    assert text.startswith("# Report: tiny-sweep (sweep)\n")
    assert text.count(SCOPE_BOUNDARY) == 1
    assert text.index(SCOPE_BOUNDARY) < text.index("|---")
    assert text.index(SCOPE_BOUNDARY) < text.index("\n## ")
    # The table is of this sweep: its widest row, as stored, is a line of the report.
    widest = load_results(_reported_run_dir(result.output))["sweep"][-1]
    assert (
        f"| 8 | {widest['n_qubits_truth_table']} | {widest['n_qubits_arithmetic']} | "
        f"{widest['gate_count']} | {widest['ir_depth']} |"
    ) in text


def test_the_sweep_command_defaults_to_the_configured_directory_and_a_derived_name(tmp_path):
    """No ``--output-dir`` and no ``--run-id``: the configuration's directory, and a name that
    identifies the sweep — oracle, variant and seed — so two sweeps cannot overwrite each other."""
    config = _write_config(tmp_path)
    result = CliRunner().invoke(app, ["sweep", "-c", str(config)])
    assert result.exit_code == 0, result.output
    run_dir = _reported_run_dir(result.output)
    assert run_dir == tmp_path / "configured-results" / "sweep-key_map-nu2-modeA-eq1-s77"
    assert (run_dir / "metrics.json").is_file() and (run_dir / "report.md").is_file()


def test_a_sweep_whose_every_statevector_is_refused_still_exits_zero(tmp_path):
    """``--ram-budget-gb`` reaches the run, and a refusal is an outcome of the command, not an error."""
    config = _write_config(tmp_path)
    result = CliRunner().invoke(
        app,
        [
            "sweep", "--config", str(config), "--output-dir", str(tmp_path / "out"),
            "--run-id", "starved", "--ram-budget-gb", "1e-9",
        ],
    )
    assert result.exit_code == 0, result.output
    stored = load_results(tmp_path / "out" / "starved")
    assert all(row["status"] == "measured" for row in stored["sweep"]), "counting needs no memory"
    assert all(row["statevector_fits_budget_truth_table"] is False for row in stored["sweep"])
    refusals = [key for key in stored["not_run"] if key.startswith("statevector pass")]
    assert len(refusals) == 2 * len(WIDTHS)
    text = (tmp_path / "out" / "starved" / "report.md").read_text(encoding="utf-8")
    assert "## Points that were not run, and why" in text
    # The override is this invocation's; the configuration the run echoes still says what it said.
    assert stored["config"]["backend"]["ram_budget_gb"] == 6.0


# -----------------------------------------------------------------------------------------------
# a configuration that cannot be loaded
# -----------------------------------------------------------------------------------------------


def _assert_a_clean_failure(result, output_dir: Path) -> None:
    assert result.exit_code == 1, result.output
    assert "Traceback" not in result.output
    assert "ERROR" in result.output
    assert not output_dir.exists(), "a run that could not load its configuration wrote something"
    assert not any(line.endswith("report.md") for line in result.output.splitlines())


def test_a_missing_configuration_file_is_a_failure_that_names_the_file(tmp_path):
    missing = tmp_path / "absent.yaml"
    result = CliRunner().invoke(
        app, ["sweep", "--config", str(missing), "--output-dir", str(tmp_path / "out")]
    )
    _assert_a_clean_failure(result, tmp_path / "out")
    assert "FileNotFoundError" in result.output
    assert str(missing) in result.output


def test_an_unknown_key_is_a_failure_that_names_the_key(tmp_path):
    """A typo is not a default nobody chose: ``oracle.typ`` stops the command and is quoted back."""
    config = tmp_path / "typo.yaml"
    config.write_text(yaml.safe_dump({"oracle": {"typ": "qlwr"}}), encoding="utf-8")
    result = CliRunner().invoke(
        app, ["sweep", "--config", str(config), "--output-dir", str(tmp_path / "out")]
    )
    _assert_a_clean_failure(result, tmp_path / "out")
    assert "ValidationError" in result.output
    assert "oracle.typ" in result.output
    assert "Extra inputs are not permitted" in result.output


@pytest.mark.parametrize(
    ("section", "values", "named"),
    [
        ("oracle", {"type": "shor"}, "oracle.type"),
        ("oracle", {"target_qubits": 64}, "oracle.target_qubits"),
        ("sweep", {"qubit_range": [8, 6, 4]}, "ascending"),
        ("backend", {"ram_budget_gb": 0}, "backend.ram_budget_gb"),
    ],
)
def test_an_invalid_value_is_a_failure_that_names_the_field(tmp_path, section, values, named):
    config = _write_config(tmp_path, "invalid.yaml", **{section: values})
    for command in ("sweep", "run"):
        result = CliRunner().invoke(
            app, [command, "--config", str(config), "--output-dir", str(tmp_path / "out")]
        )
        _assert_a_clean_failure(result, tmp_path / "out")
        assert "ValidationError" in result.output
        assert named in result.output
    assert not (tmp_path / "configured-results").exists()


def test_a_configuration_that_is_not_a_mapping_is_a_failure_that_says_so(tmp_path):
    config = tmp_path / "list.yaml"
    config.write_text("- qlwr\n- 8\n", encoding="utf-8")
    result = CliRunner().invoke(
        app, ["sweep", "--config", str(config), "--output-dir", str(tmp_path / "out")]
    )
    _assert_a_clean_failure(result, tmp_path / "out")
    assert "the top level of a config must be a mapping, got list" in result.output


def test_an_unknown_option_is_a_usage_error_not_a_run(tmp_path):
    config = _write_config(tmp_path)
    result = CliRunner().invoke(app, ["sweep", "--config", str(config), "--iterations", "40"])
    assert result.exit_code == 2
    assert "No such option" in result.output
    assert not (tmp_path / "configured-results").exists()


# -----------------------------------------------------------------------------------------------
# probe
# -----------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def probe_invocation():
    """``cli probe``, for real: every framework API check this project is built on, executed."""
    return CliRunner().invoke(app, ["probe"])


def test_the_probe_command_passes_on_this_checkout_and_prints_every_check(probe_invocation):
    result = probe_invocation
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0] == "milestone 0 - framework API probe"
    checks = [line for line in lines if line.startswith("[")]
    assert len(checks) >= 20
    assert not [line for line in checks if line.startswith("[FAIL]")]
    for framework in ("qiskit", "qiskit_aer", "cirq", "qsimcirq", "quimb", "cotengra"):
        assert any(line.startswith("[ok  ]") and line.split()[2] == framework for line in checks), (
            f"{framework} was not checked"
        )
    # The summary line counts what was printed above it, and reports no required failure.
    assert lines[-1] == f"{len(checks)} checks, 0 required failures"


def test_the_probe_command_needs_no_configuration_and_writes_nothing(tmp_path, monkeypatch):
    """It is milestone zero: it must be runnable before a configuration or a results tree exists."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["probe", "--help"])
    assert result.exit_code == 0
    assert "--config" not in result.output
    assert "Milestone 0" in result.output
    assert list(tmp_path.iterdir()) == []


def test_the_probe_command_exits_non_zero_when_a_required_check_fails(monkeypatch):
    """The exit status is the command's own logic, so it is exercised with a failing check list.

    Only the list of checks is substituted — the command, its report formatting and its exit path
    are the real ones. A warning-level failure must not fail the command; a required one must.
    """
    advisory = [
        api_probe.ProbeResult("present.api", True, "1.0"),
        api_probe.ProbeResult("optional.api", False, "absent", required=False),
    ]
    monkeypatch.setattr(api_probe, "probe_all", lambda: advisory)
    result = CliRunner().invoke(app, ["probe"])
    assert result.exit_code == 0, result.output
    assert "[warn] optional.api" in result.output
    assert result.output.rstrip().endswith("2 checks, 0 required failures")

    broken = advisory + [api_probe.ProbeResult("required.api", False, "signature changed")]
    monkeypatch.setattr(api_probe, "probe_all", lambda: broken)
    result = CliRunner().invoke(app, ["probe"])
    assert result.exit_code == 1
    assert "[FAIL] required.api" in result.output and "signature changed" in result.output
    assert result.output.rstrip().endswith("3 checks, 1 required failures")
