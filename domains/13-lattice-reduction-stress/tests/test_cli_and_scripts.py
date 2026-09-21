"""The commands and scripts nothing invoked, and the config failures nothing provoked.

``test_cli.py`` reaches ``run``, ``report`` and ``planted-check``. ``sweep``, ``probe`` and
``estimate`` were listed in the help test and never called; ``scripts/run_experiment.py`` and
``scripts/sweep_dimensions.py`` — deliverables of the design document's milestone 10 — had no test at
all. A wrapper that is two lines long is still two lines that can name the wrong function, and the
only way to find out is to run it.

Every run here writes under ``tmp_path``. The repository's own ``results/`` tree holds the sweeps
the notes cite, so a test that wrote into it would be editing the evidence; the guard fixture below
makes that a failure rather than a convention.

The second half is the config loader's refusals. They matter more than they look: a lattice attack
"succeeds" against the wrong lattice without complaint, so the config is where a wrong run has to be
stopped — and until 2026-09-20 the shape ratio ``nu_over_m`` was not stopped there at all: a zero
denominator divided by zero downstream, a ratio above one hung ``build_instance``.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from typer.testing import CliRunner

from qlwr_lattice_stress.cli import app
from qlwr_lattice_stress.config.schema import ExperimentConfig, InstanceSettings, load_config
from qlwr_lattice_stress.reporting import SCOPE_BOUNDARY

runner = CliRunner()
REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def tiny_config(tmp_path: Path, **overrides) -> Path:
    """The smallest config that still exercises a real reduction: enumeration only, one thread,
    estimator off (it costs seconds per point and none of these tests read it)."""
    document = {
        "instance": {"source": "synthetic_scaled", "target_dimension": 40, "seed": 20260913},
        "engine": {"preference": ["fpylll_bkz"], "threads": 1},
        "attack": {"types": ["primal"], "block_size_range": [10, 20]},
        "sweep": {"dimension_range": [40, 50]},
        "cost_model": {"use_lattice_estimator": False},
        "output": {"dir": str(tmp_path / "results")},
    }
    document.update(overrides)
    path = tmp_path / "tiny.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    return path


def _tree(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*")} if root.exists() else set()


@pytest.fixture(autouse=True)
def the_shipped_results_tree_is_not_written(request):
    """Fails any test in this file that adds or removes a file under the repository's ``results/``."""
    before = _tree(REPO / "results")
    yield
    assert _tree(REPO / "results") == before, f"{request.node.name} wrote into the shipped results"


def _assert_a_complete_run_directory(run_dir: Path) -> None:
    for name in ("metrics.json", "report.md", "config.yaml"):
        assert (run_dir / name).is_file(), f"{run_dir.name} has no {name}"
    assert SCOPE_BOUNDARY in (run_dir / "report.md").read_text()


# ---------------------------------------------------------------------------------------------
# sweep
# ---------------------------------------------------------------------------------------------


def test_sweep_runs_every_dimension_and_writes_a_run_for_each(tmp_path):
    result = runner.invoke(app, ["sweep", "--config", str(tiny_config(tmp_path))])
    assert result.exit_code == 0, (result.stdout, result.exception)

    run_dirs = sorted(p.name for p in (tmp_path / "results").iterdir())
    assert run_dirs == ["synthetic_scaled-d40-s20260913", "synthetic_scaled-d50-s20260913"]
    for name in run_dirs:
        _assert_a_complete_run_directory(tmp_path / "results" / name)

    # One summary line per dimension, naming the dimension and what was found there.
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 2
    for dimension, line in zip((40, 50), lines):
        assert line.startswith(f"dimension {dimension}:"), line
        minimum = json.loads(
            (tmp_path / "results" / f"synthetic_scaled-d{dimension}-s20260913" / "metrics.json")
            .read_text()
        )["minimum_block_sizes"]["primal_usvp"]
        assert f"primal_usvp={minimum}" in line


def test_sweep_refuses_a_config_the_schema_refuses(tmp_path):
    """Non-zero, and the message names the legal values rather than saying something went wrong."""
    bad = tiny_config(tmp_path, instance={"source": "corpus_recorded"})
    result = runner.invoke(app, ["sweep", "--config", str(bad)])
    assert result.exit_code != 0
    assert isinstance(result.exception, ValidationError)
    assert "instance.source" in str(result.exception)
    assert "synthetic_scaled" in str(result.exception)
    assert not (tmp_path / "results").exists(), "a refused config still produced output"


def test_sweep_refuses_a_config_that_does_not_exist(tmp_path):
    result = runner.invoke(app, ["sweep", "--config", str(tmp_path / "absent.yaml")])
    assert result.exit_code == 2
    assert "does not exist" in result.output


def test_run_honours_an_explicit_run_id(tmp_path):
    result = runner.invoke(
        app, ["run", "--config", str(tiny_config(tmp_path)), "--run-id", "named-by-hand"]
    )
    assert result.exit_code == 0, (result.stdout, result.exception)
    assert [p.name for p in (tmp_path / "results").iterdir()] == ["named-by-hand"]
    _assert_a_complete_run_directory(tmp_path / "results" / "named-by-hand")
    assert "run id     : named-by-hand" in result.stdout


# ---------------------------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------------------------


@pytest.mark.slow
def test_probe_runs_every_check_and_exits_zero():
    """The real probe: a real sieving tour and a real estimate, so this is the slow one."""
    result = runner.invoke(app, ["probe"])
    assert result.exit_code == 0, result.stdout
    assert "qlwr-lattice-stress: API probe" in result.stdout
    assert " 0 required failures" in result.stdout
    assert "[ok  ] " in result.stdout and "[FAIL]" not in result.stdout


def test_probe_exits_non_zero_when_a_required_check_fails(monkeypatch):
    """The exit code is what a build script reads. The probe itself is replaced here — it is the
    dependency — and the command's translation of its verdict is what is under test."""
    from qlwr_lattice_stress.utils import api_probe

    monkeypatch.setattr(
        api_probe, "probe_all",
        lambda: [api_probe.Check("fpylll imports", False, "ImportError: gone", True),
                 api_probe.Check("g6k imports", False, "not built", False)],
    )
    result = runner.invoke(app, ["probe"])
    assert result.exit_code == 1
    assert "REQUIRED FAILURES" in result.stdout
    assert "[FAIL] fpylll imports -- ImportError: gone" in result.stdout
    # An optional absence alone is not a failure, and the report says which is which.
    assert "[none] g6k imports" in result.stdout

    monkeypatch.setattr(
        api_probe, "probe_all", lambda: [api_probe.Check("g6k imports", False, "not built", False)]
    )
    assert runner.invoke(app, ["probe"]).exit_code == 0


# ---------------------------------------------------------------------------------------------
# estimate
# ---------------------------------------------------------------------------------------------


def test_estimate_reports_the_published_set_as_json():
    pytest.importorskip("estimator", reason="lattice-estimator is not importable")
    result = runner.invoke(app, ["estimate", "--scheme", "Kyber512"])
    assert result.exit_code == 0, (result.stdout, result.exception)

    payload = json.loads(result.stdout[result.stdout.index("{"):])
    assert payload["scheme"] == "Kyber512"
    assert payload["usvp_beta"] == 406, "the pinned Kyber512 baseline (notes/00)"
    assert isinstance(payload["dual_beta"], int) and payload["dual_beta"] > 0
    assert payload["log2_rop_quantum_min"] < payload["log2_rop_classical_min"]
    assert len(payload["estimator_revision"]) == 40


def test_estimate_refuses_an_unknown_scheme_and_names_the_known_ones():
    result = runner.invoke(app, ["estimate", "--scheme", "Kyber513"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)
    assert "Kyber513" in str(result.exception) and "Kyber512" in str(result.exception)


# ---------------------------------------------------------------------------------------------
# the two wrapper scripts, as processes
# ---------------------------------------------------------------------------------------------


def _script(name: str, *args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / name), *args],
        capture_output=True, text=True, cwd=cwd, timeout=300,
    )


@pytest.mark.parametrize("name", ["run_experiment.py", "sweep_dimensions.py", "move_tools.py"])
def test_each_script_explains_itself_and_does_nothing_else(name, tmp_path):
    proc = _script(name, "--help", cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "usage:" in proc.stdout
    assert list(tmp_path.iterdir()) == [], "--help left something behind"


@pytest.mark.parametrize("name", ["run_experiment.py", "sweep_dimensions.py"])
def test_each_script_requires_a_config(name, tmp_path):
    proc = _script(name, cwd=tmp_path)
    assert proc.returncode == 2
    assert "--config" in proc.stderr


def test_run_experiment_script_runs_for_real(tmp_path):
    proc = _script(
        "run_experiment.py", "--config", str(tiny_config(tmp_path)), "--run-id", "scripted",
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]

    printed = json.loads(proc.stdout)
    run_dir = tmp_path / "results" / "scripted"
    assert printed["run_id"] == "scripted" and Path(printed["run_dir"]) == run_dir
    assert "attacks" not in printed, "the summary is documented as omitting the per-point rows"
    _assert_a_complete_run_directory(run_dir)

    # The wrapper and the library agree, because the wrapper *is* the library call.
    stored = json.loads((run_dir / "metrics.json").read_text())
    assert stored["minimum_block_sizes"] == printed["minimum_block_sizes"]
    assert stored["attacks"], "the run recorded no attack point"


def test_sweep_dimensions_script_runs_for_real(tmp_path):
    proc = _script("sweep_dimensions.py", "--config", str(tiny_config(tmp_path)), cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr[-2000:]

    outcomes = json.loads(proc.stdout)
    assert [o["instance"]["qary_lattice_dimension"] for o in outcomes] == [40, 50]
    for outcome in outcomes:
        assert Path(outcome["run_dir"]).parent == tmp_path / "results"
        _assert_a_complete_run_directory(Path(outcome["run_dir"]))


def test_a_script_given_a_bad_config_fails_and_says_why(tmp_path):
    bad = tiny_config(tmp_path, instance={"source": "corpus_recorded"})
    proc = _script("run_experiment.py", "--config", str(bad), cwd=tmp_path)
    assert proc.returncode != 0
    assert "instance.source" in proc.stderr and "synthetic_scaled" in proc.stderr
    assert not (tmp_path / "results").exists()


# ---------------------------------------------------------------------------------------------
# move_tools.py: the script with a deletion stage
# ---------------------------------------------------------------------------------------------


def _import_move_tools():
    spec = importlib.util.spec_from_file_location("move_tools_under_test", SCRIPTS / "move_tools.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_importing_move_tools_moves_nothing(monkeypatch):
    """Read first, then tested: the module body defines constants and functions, and every stage
    sits behind ``main``. This pins that — each filesystem and process primitive the stages use is
    made to raise for the duration of the import, so a stage promoted to import time fails here."""
    import shutil

    def must_not_run(*args, **kwargs):
        raise AssertionError(f"import performed a side effect: {args!r}")

    for owner, name in ((shutil, "copytree"), (shutil, "rmtree"), (subprocess, "run"),
                        (Path, "write_text"), (Path, "mkdir")):
        monkeypatch.setattr(owner, name, must_not_run)

    module = _import_move_tools()
    assert module.TOOLS == ("g6k", "lattice-estimator")
    assert module.DEST_ROOT == Path.home() / "Documents" / "lattice-tools"
    assert callable(module.main)


def test_the_path_entry_is_refused_outside_the_sage_environment(monkeypatch, tmp_path):
    """A ``.pth`` in the wrong site-packages puts G6K on the path of interpreters this project has
    nothing to do with. The refusal must come before the write."""
    import sysconfig

    module = _import_move_tools()
    elsewhere = tmp_path / "lib" / "python3.12" / "site-packages"
    elsewhere.mkdir(parents=True)
    monkeypatch.setattr(sysconfig, "get_paths", lambda *a, **k: {"purelib": str(elsewhere)})

    with pytest.raises(RuntimeError, match="sage env"):
        module.site_packages()
    with pytest.raises(RuntimeError, match="sage env"):
        module.install_stage()
    assert list(elsewhere.iterdir()) == []


# ---------------------------------------------------------------------------------------------
# load_config: the refusals
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("text", ["", "# only a comment\n", "---\n"])
def test_an_empty_config_file_is_refused_by_name(tmp_path, text):
    """Not defaulted. An empty file validating to the default config would run the shipped sweep
    because someone truncated a file."""
    path = tmp_path / "empty.yaml"
    path.write_text(text)
    with pytest.raises(ValueError, match="is empty") as exc:
        load_config(path)
    assert str(path) in str(exc.value)


@pytest.mark.parametrize(
    ("text", "kind"), [("- a\n- b\n", "list"), ("just a sentence\n", "str"), ("42\n", "int")]
)
def test_a_config_that_is_not_a_mapping_is_refused_with_its_type(tmp_path, text, kind):
    path = tmp_path / "shape.yaml"
    path.write_text(text)
    with pytest.raises(ValueError, match=f"mapping at the top level, got {kind}"):
        load_config(path)


def test_a_published_reference_without_a_scheme_is_refused_before_any_work(tmp_path):
    """Wherever the refusal lives — at load or at the top of the run — it must be a ``ValueError``
    that names the missing key, and it must leave nothing on disk."""
    from qlwr_lattice_stress.pipeline import run_experiment

    path = tiny_config(tmp_path, instance={"source": "published_reference"})
    with pytest.raises(ValueError, match="reference_scheme"):
        run_experiment(load_config(path))
    assert not (tmp_path / "results").exists()


def test_yaml_lists_load_as_tuples(tmp_path):
    """The loader's one transformation. A list field could be mutated after validation, which would
    defeat freezing the model."""
    cfg = load_config(tiny_config(tmp_path))
    assert cfg.attack.block_size_range == (10, 20)
    assert cfg.sweep.dimension_range == (40, 50)
    assert cfg.instance.nu_over_m == (256, 608)
    assert isinstance(cfg.engine.preference, tuple)


# ---------------------------------------------------------------------------------------------
# nu_over_m
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("ratio", [(256, 608), (1, 2), (25, 60)])
def test_a_sane_shape_ratio_is_accepted_unchanged(ratio):
    assert InstanceSettings(nu_over_m=ratio).nu_over_m == ratio


@pytest.mark.parametrize(
    "ratio", [(1, 0), (3, 2), (-1, 2)], ids=["zero-denominator", "nu-exceeds-m", "negative"]
)
def test_a_shape_ratio_that_describes_no_instance_is_refused_at_load(ratio):
    """Validated here and nowhere else, so this is the only place the three can be stopped. The
    second is the dangerous one: it does not raise, it hangs."""
    with pytest.raises(ValidationError):
        InstanceSettings(nu_over_m=ratio)
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate({"instance": {"nu_over_m": ratio}})
