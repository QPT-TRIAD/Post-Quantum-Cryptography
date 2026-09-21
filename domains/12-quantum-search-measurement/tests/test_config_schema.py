"""One configuration schema, and the defaults the experiment is launched with.

The repository carried two copies of the schema for a while: ``src/grover_emulator/config/schema.py``
and a ``config/schema.py`` at the root that re-exported it. Two copies of a validation surface is the
failure the schema exists to prevent — a typo that neither copy rejects, a default that drifts in the
copy nothing reads — so the root copy is gone and the directory holds the YAML alone. The first three
tests here hold that state, because it is the kind of duplication that grows back: the cheap way to
"fix" an import from a script run out of the repository root is to re-add the alias.

The rest are the defaults the plan fixes, asserted rather than assumed, and the one setting that must
never acquire a default of its own. ``sweep.iteration_range`` is null, which means *derived per
instance* from the spec's own optimum; the plan document this project was built from carried a fixed
``[0, 40]``, which truncates every curve before its peak and returns a smooth, monotone, entirely
plausible rise that supports no conclusion. A fixed range is still allowed — a deliberately narrow
exploratory window is a legitimate thing to ask for — but it is never silent, so the warning is
asserted to fire and to quote the optimum the rest of the configuration implies.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from grover_emulator.config import schema
from grover_emulator.config.schema import (
    ExperimentConfig,
    OracleType,
    SweepSettings,
    dump_config,
    load_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DEFAULT_EXPERIMENT = CONFIG_DIR / "default_experiment.yaml"

# The sweep widths and the memory ceiling the plan fixes. Repeated here as literals on purpose: a
# test that reads the expected value out of the thing it is testing asserts nothing.
EXPECTED_QUBIT_RANGE = [4, 8, 12, 16, 20, 24]
EXPECTED_RAM_BUDGET_GB = 6.0


def test_the_root_config_directory_holds_data_and_no_code():
    """The directory is where the YAML lives; a Python module in it is the duplication growing back.

    Phrased as "no code" rather than "exactly one file" because a second plan document is a
    legitimate thing to add and a second schema is not: any ``.py`` here is a module that shadows,
    or duplicates, the one the installed package validates against.
    """
    assert DEFAULT_EXPERIMENT.is_file()
    entries = sorted(p.name for p in CONFIG_DIR.iterdir())
    assert [name for name in entries if name.endswith((".py", ".pyc", ".pyi"))] == []
    assert "__pycache__" not in entries
    assert "default_experiment.yaml" in entries


def test_the_root_schema_is_not_importable():
    """``import config.schema`` from the repository root fails, in a fresh interpreter.

    A subprocess because the question is about a new interpreter's import path from the repository
    root, not about this one's: pytest's own path setup puts ``tests/`` and ``src/`` on the path, so
    asking in-process would answer a question nobody asked. ``PYTHONPATH`` is cleared for the same
    reason — a leaked ``src`` entry would not make the module importable, but it would make the test
    depend on the shell it was launched from.
    """
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, "-c", "import config.schema"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode != 0, "the repository-root config package is importable again"
    assert "ModuleNotFoundError" in result.stderr, result.stderr


def test_the_single_schema_is_the_installed_one():
    """The schema the loader validates against lives under ``src``, which is what gets packaged."""
    assert Path(schema.__file__).resolve().is_relative_to(ROOT / "src")


def test_the_default_experiment_loads_with_the_documented_defaults():
    config = load_config(DEFAULT_EXPERIMENT)
    assert config.sweep.qubit_range == EXPECTED_QUBIT_RANGE
    assert config.backend.ram_budget_gb == EXPECTED_RAM_BUDGET_GB
    assert config.oracle.type is OracleType.QLWR
    assert config.oracle.target_qubits in EXPECTED_QUBIT_RANGE
    assert config.run.seed == 20260913


def test_the_iteration_range_is_derived_per_instance_and_has_no_default_of_its_own():
    """Null in the file, null on a bare section, and null in the config a run echoes.

    The three are separate claims and each has been broken differently in projects like this one: a
    field default that quietly became ``[0, 40]``, a loaded file that filled the null in from the
    section's default, and a config echo that reported the derived range as though it had been
    configured. ``to_range()`` returning None is what "derive it, do not read it" means in code.
    """
    assert SweepSettings().iteration_range is None
    assert SweepSettings().to_range() is None
    assert ExperimentConfig().sweep.to_range() is None

    config = load_config(DEFAULT_EXPERIMENT)
    assert config.sweep.iteration_range is None
    assert config.sweep.to_range() is None
    assert dump_config(config)["sweep"]["iteration_range"] is None


def test_a_fixed_iteration_range_is_allowed_but_never_silent(tmp_path):
    """A deliberately narrow window loads, with a warning naming what it would truncate."""
    text = DEFAULT_EXPERIMENT.read_text(encoding="utf-8").replace(
        "iteration_range: null", "iteration_range: [0, 40]"
    )
    path = tmp_path / "fixed-window.yaml"
    path.write_text(text, encoding="utf-8")

    with pytest.warns(UserWarning, match=r"iteration_range is fixed at \[0, 40\]"):
        config = load_config(path)

    assert config.sweep.to_range() == range(0, 41)
    # The window survives validation as written: a configuration that asked for a narrow window is
    # not silently normalised back to the derived one at load time.
    assert config.sweep.iteration_range == [0, 40]


def test_an_unknown_key_is_a_load_failure_that_names_it(tmp_path):
    """``extra="forbid"`` is the schema's reason to exist; a mistyped key is not a silent default."""
    text = DEFAULT_EXPERIMENT.read_text(encoding="utf-8").replace("target_qubits: 20", "target_qubts: 20")
    path = tmp_path / "typo.yaml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValidationError) as caught:
        load_config(path)
    assert "target_qubts" in str(caught.value)


def test_a_missing_config_file_is_refused_rather_than_defaulted(tmp_path):
    """A run that used built-in defaults because the path was mistyped reproduces nothing."""
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "not-here.yaml")
