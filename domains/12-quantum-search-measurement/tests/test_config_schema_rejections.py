"""What the configuration schema refuses, and the one number it computes.

``tests/test_config_schema.py`` holds the defaults and the two load failures that are about the file
(an unknown key, a missing path). This file is the other half of the same argument: a schema whose
bounds have never been seen to reject anything is a schema nobody knows is there. Each refusal below
names the field it expects the error to point at and the kind of error it expects, because "some
ValidationError was raised" is also what a typo in the *test's* own key would produce — every model
forbids extra keys — and a test that passes for that reason asserts nothing about the bound.

Each bound is tested from both sides: the last legal value is accepted in the same test that refuses
the first illegal one, so an off-by-one in either direction is a failure rather than a coincidence.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from grover_emulator.config.schema import (
    BackendSettings,
    ExperimentConfig,
    OracleSettings,
    OracleType,
    OutputSettings,
    SweepSettings,
    expected_optimal_iterations,
    load_config,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENT = ROOT / "config" / "default_experiment.yaml"


def validate(raw: dict) -> ExperimentConfig:
    """Validate a mapping with the width warning silenced; it has its own tests below."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return ExperimentConfig.model_validate(raw)


def single_error(raw: dict) -> dict:
    """The one error a bad mapping produces. More than one would mean the test broke two rules."""
    with pytest.raises(ValidationError) as caught:
        validate(raw)
    errors = caught.value.errors()
    assert len(errors) == 1, errors
    return errors[0]


def write_config(tmp_path: Path, **sections) -> Path:
    """The default experiment with some sections' keys replaced, written where a loader can read it."""
    raw = yaml.safe_load(DEFAULT_EXPERIMENT.read_text(encoding="utf-8"))
    for section, values in sections.items():
        raw[section].update(values)
    path = tmp_path / "experiment.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return path


# -----------------------------------------------------------------------------------------------
# oracle
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["shor", "QLWR", "random", "", 3, None])
def test_an_oracle_type_outside_the_enum_is_refused_and_the_legal_ones_are_listed(value):
    error = single_error({"oracle": {"type": value}})
    assert error["loc"] == ("oracle", "type")
    assert error["type"] == "enum"
    for legal in ("qlwr", "random_control", "hidden_period", "lmots_chain", "key_map"):
        assert legal in error["msg"]


def test_every_documented_oracle_type_is_accepted_by_its_value():
    assert {t.value for t in OracleType} == {"qlwr", "random_control", "hidden_period", "lmots_chain", "key_map"}
    for oracle_type in OracleType:
        assert validate({"oracle": {"type": oracle_type.value}}).oracle.type is oracle_type


@pytest.mark.parametrize(
    "field, legal, illegal, kind",
    [
        ("target_qubits", 2, 1, "greater_than_equal"),
        ("target_qubits", 30, 31, "less_than_equal"),
        ("target_qubits", 2, 0, "greater_than_equal"),
        ("target_qubits", 2, -4, "greater_than_equal"),
        ("marked_fraction", 1e-12, 0.0, "greater_than"),
        ("marked_fraction", 1e-12, -0.5, "greater_than"),
        ("marked_fraction", 0.999999, 1.0, "less_than"),
        ("nu", 1, 0, "greater_than_equal"),
        ("nu", 4, 5, "less_than_equal"),
        ("min_rounding_gap", 1.5, 1.49, "greater_than_equal"),
        ("chain_length", 1, 0, "greater_than_equal"),
        ("chain_length", 254, 255, "less_than_equal"),
        ("chain_image_bits", 2, 1, "greater_than_equal"),
        ("key_map_outputs", 1, 0, "greater_than_equal"),
        ("key_map_outputs", 64, 65, "less_than_equal"),
    ],
)
def test_an_oracle_bound_accepts_its_last_legal_value_and_refuses_the_next(field, legal, illegal, kind):
    assert getattr(validate({"oracle": {field: legal}}).oracle, field) == legal
    error = single_error({"oracle": {field: illegal}})
    assert error["loc"] == ("oracle", field)
    assert error["type"] == kind


@pytest.mark.parametrize(
    "section, field, value",
    [("oracle", "key_map_mode", "C"), ("oracle", "key_map_mode", "a"), ("run", "lowering", "qft")],
)
def test_a_literal_field_refuses_a_spelling_it_does_not_list(section, field, value):
    error = single_error({section: {field: value}})
    assert error["loc"] == (section, field)
    assert error["type"] == "literal_error"


@pytest.mark.parametrize("value", ["twenty", 20.5, [20], None])
def test_a_width_that_is_not_an_integer_is_refused(value):
    assert single_error({"oracle": {"target_qubits": value}})["loc"] == ("oracle", "target_qubits")


# -----------------------------------------------------------------------------------------------
# backend
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field, legal, illegal, kind",
    [
        ("ram_budget_gb", 0.001, 0.0, "greater_than"),
        ("ram_budget_gb", 0.001, -6.0, "greater_than"),
        ("shots", 1, 0, "greater_than_equal"),
        ("shots", 1, -20000, "greater_than_equal"),
    ],
)
def test_a_backend_bound_accepts_its_last_legal_value_and_refuses_the_next(field, legal, illegal, kind):
    assert getattr(validate({"backend": {field: legal}}).backend, field) == legal
    error = single_error({"backend": {field: illegal}})
    assert error["loc"] == ("backend", field)
    assert error["type"] == kind


def test_a_backend_preference_that_repeats_an_engine_is_refused():
    error = single_error({"backend": {"preference": ["qiskit_aer", "cirq_qsim", "qiskit_aer"]}})
    assert error["loc"] == ("backend", "preference")
    assert "backend preference repeats an engine" in error["msg"]
    assert "qiskit_aer" in error["msg"]


def test_an_empty_backend_preference_is_refused():
    error = single_error({"backend": {"preference": []}})
    assert error["loc"] == ("backend", "preference")
    assert error["type"] == "too_short"


def test_the_order_of_a_legal_preference_survives_validation():
    """The order is the preference; a schema that sorted or deduplicated would be changing the request.

    The plan document lists ``tensor_network`` in its default preference; the shipped default does
    not, and that is pinned here so it cannot change in either direction without a test noticing.
    """
    assert BackendSettings().preference == ["qiskit_aer", "cirq_qsim"]
    chosen = validate({"backend": {"preference": ["tensor_network", "cirq_qsim", "qiskit_aer"]}})
    assert chosen.backend.preference == ["tensor_network", "cirq_qsim", "qiskit_aer"]


# -----------------------------------------------------------------------------------------------
# sweep
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "qubit_range, message",
    [
        ([8, 4], "sweep widths must be ascending"),
        ([4, 12, 8, 16], "sweep widths must be ascending"),
        ([4, 4], "sweep widths repeat"),
        ([4, 8, 8, 12], "sweep widths repeat"),
        ([1, 4], "every sweep width must be at least 2"),
        ([0], "every sweep width must be at least 2"),
        ([-8, 8], "every sweep width must be at least 2"),
    ],
)
def test_a_sweep_that_is_not_strictly_ascending_widths_of_at_least_two_is_refused(qubit_range, message):
    error = single_error({"sweep": {"qubit_range": qubit_range}})
    assert error["loc"] == ("sweep", "qubit_range")
    assert error["type"] == "value_error"
    assert message in error["msg"]
    assert str(qubit_range) in error["msg"], "the refusal quotes the list it refused"


def test_an_empty_sweep_is_refused():
    error = single_error({"sweep": {"qubit_range": []}})
    assert error["loc"] == ("sweep", "qubit_range")
    assert error["type"] == "too_short"


def test_a_single_width_and_the_smallest_width_are_a_legal_sweep():
    assert SweepSettings(qubit_range=[2]).qubit_range == [2]
    assert SweepSettings(qubit_range=[2, 3, 30]).qubit_range == [2, 3, 30]


@pytest.mark.parametrize(
    "iteration_range, message",
    [
        ([5], "iteration_range must be null or [lo, hi], got [5]"),
        ([], "iteration_range must be null or [lo, hi], got []"),
        ([1, 2, 3], "iteration_range must be null or [lo, hi], got [1, 2, 3]"),
        ([-1, 5], "iteration_range starts below 0: [-1, 5]"),
        ([5, 4], "iteration_range is empty: [5, 4]"),
        ([-3, -5], "iteration_range starts below 0: [-3, -5]"),
    ],
)
def test_a_malformed_iteration_range_is_refused_with_the_reason(iteration_range, message):
    error = single_error({"sweep": {"iteration_range": iteration_range}})
    assert error["loc"] == ("sweep", "iteration_range")
    assert error["type"] == "value_error"
    assert message in error["msg"]


@pytest.mark.parametrize("value", [40, "0-40", {"lo": 0, "hi": 40}])
def test_an_iteration_range_that_is_not_a_list_is_refused(value):
    """A bare ``40`` is the ambiguity the two-element rule exists to prevent: a count, or a bound?"""
    error = single_error({"sweep": {"iteration_range": value}})
    assert error["loc"] == ("sweep", "iteration_range")
    assert error["type"] == "list_type"


def test_the_iteration_range_is_inclusive_at_both_ends():
    assert SweepSettings(iteration_range=[0, 0]).to_range() == range(0, 1)
    assert SweepSettings(iteration_range=[7, 7]).to_range() == range(7, 8)
    assert list(SweepSettings(iteration_range=[48, 52]).to_range()) == [48, 49, 50, 51, 52]


# -----------------------------------------------------------------------------------------------
# output
# -----------------------------------------------------------------------------------------------


def test_output_formats_that_repeat_are_refused():
    error = single_error({"output": {"formats": ["json", "markdown", "json"]}})
    assert error["loc"] == ("output", "formats")
    assert "output formats repeat" in error["msg"]


def test_an_unknown_output_format_is_refused_at_its_position():
    error = single_error({"output": {"formats": ["json", "pdf"]}})
    assert error["loc"] == ("output", "formats", 1)
    assert error["type"] == "literal_error"


def test_no_output_format_at_all_is_refused():
    assert single_error({"output": {"formats": []}})["type"] == "too_short"
    assert OutputSettings(formats=["json"]).formats == ["json"]


# -----------------------------------------------------------------------------------------------
# the shape of the whole mapping
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, loc",
    [
        ({"orcale": {}}, ("orcale",)),
        ({"sweep": {"qubit_rnage": [4]}}, ("sweep", "qubit_rnage")),
        ({"backend": {"gpu": True}}, ("backend", "gpu")),
        ({"probes": {"run_shor": True}}, ("probes", "run_shor")),
    ],
)
def test_an_unknown_key_is_refused_at_every_level(raw, loc):
    error = single_error(raw)
    assert error["loc"] == loc
    assert error["type"] == "extra_forbidden"


@pytest.mark.parametrize("text", ["- qlwr\n- 20\n", "qlwr\n", "42\n"])
def test_a_config_whose_top_level_is_not_a_mapping_is_refused(tmp_path, text):
    path = tmp_path / "not-a-mapping.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="top level of a config must be a mapping"):
        load_config(path)


def test_an_empty_file_is_the_defaults_and_not_an_error(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("# nothing configured\n", encoding="utf-8")
    assert load_config(path) == ExperimentConfig()


def test_a_bad_value_in_a_file_is_refused_by_the_loader_too(tmp_path):
    """The rules above are on the models; this is the same rule reached through the path a run uses."""
    with pytest.raises(ValidationError) as caught:
        load_config(write_config(tmp_path, oracle={"type": "shor"}))
    assert caught.value.errors()[0]["loc"] == ("oracle", "type")

    with pytest.raises(ValidationError, match="sweep widths must be ascending"):
        load_config(write_config(tmp_path, sweep={"qubit_range": [24, 20]}))


def test_a_validated_config_cannot_be_edited():
    config = ExperimentConfig()
    with pytest.raises(ValidationError, match="frozen"):
        config.oracle.target_qubits = 12
    with pytest.raises(ValidationError, match="frozen"):
        config.sweep = SweepSettings(qubit_range=[4])


# -----------------------------------------------------------------------------------------------
# the width warning
# -----------------------------------------------------------------------------------------------


def test_a_run_width_outside_the_sweep_warns_and_still_loads():
    with pytest.warns(UserWarning, match=r"oracle\.target_qubits=10 is not in sweep\.qubit_range=\[4, 8, 12, 16, 20, 24\]"):
        config = ExperimentConfig.model_validate({"oracle": {"target_qubits": 10}})
    assert config.oracle.target_qubits == 10


def test_the_width_warning_reads_the_sweep_as_configured_not_the_default_one():
    with pytest.warns(UserWarning, match=r"target_qubits=20 is not in sweep\.qubit_range=\[6, 8, 10\]"):
        ExperimentConfig.model_validate({"sweep": {"qubit_range": [6, 8, 10]}})


def test_a_run_width_inside_the_sweep_is_silent():
    """Silence is asserted with warnings promoted to errors: absence of a warning is otherwise untestable."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ExperimentConfig()
        ExperimentConfig.model_validate({"oracle": {"target_qubits": 10}, "sweep": {"qubit_range": [6, 10]}})
        assert load_config(DEFAULT_EXPERIMENT).oracle.target_qubits == 20


def test_the_width_warning_reaches_a_config_loaded_from_a_file(tmp_path):
    with pytest.warns(UserWarning, match="no sweep point is a check on the run"):
        config = load_config(write_config(tmp_path, oracle={"target_qubits": 14}))
    assert config.oracle.target_qubits == 14


# -----------------------------------------------------------------------------------------------
# expected_optimal_iterations
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "oracle, expected",
    [
        ({}, 804),  # the default: QLWR at 20 qubits, M = 1, floor(pi/4 * 1024)
        ({"target_qubits": 12}, 50),
        ({"target_qubits": 24}, 3216),
        # QLWR's M is 1 by construction; the configured fraction is a design target and is not read.
        ({"target_qubits": 12, "marked_fraction": 0.25}, 50),
        ({"type": "random_control", "target_qubits": 4, "marked_fraction": 0.25}, 1),  # M = 4
        ({"type": "random_control", "target_qubits": 8, "marked_fraction": 0.03125}, 4),  # M = 8
        ({"type": "hidden_period", "target_qubits": 10, "marked_fraction": 0.001}, 25),  # M = round(1.024)
        # Clamped from below: a fraction that rounds to no marked item at all still means M = 1 ...
        ({"type": "hidden_period", "target_qubits": 4, "marked_fraction": 1e-6}, 3),
        # ... and from above: M = N is not a search, so the largest M is N - 1.
        ({"type": "random_control", "target_qubits": 2, "marked_fraction": 0.999999}, 0),
    ],
)
def test_the_optimum_a_configuration_implies(oracle, expected):
    assert expected_optimal_iterations(validate({"oracle": oracle})) == expected


@pytest.mark.parametrize("oracle_type", ["lmots_chain", "key_map"])
def test_no_optimum_is_quoted_for_an_oracle_whose_m_is_not_in_the_configuration(oracle_type):
    """None, not a number computed from a fraction those oracles never read."""
    config = validate({"oracle": {"type": oracle_type, "target_qubits": 8, "marked_fraction": 0.25}})
    assert expected_optimal_iterations(config) is None


def test_the_fixed_window_warning_quotes_the_optimum_the_configuration_implies(tmp_path):
    """At 12 qubits the optimum is 50, which ``[0, 40]`` truncates — the case the warning is for."""
    path = write_config(tmp_path, oracle={"target_qubits": 12}, sweep={"iteration_range": [0, 40]})
    with pytest.warns(UserWarning, match=r"imply an optimum near k=50\. If 40 < 50"):
        load_config(path)


def test_the_fixed_window_warning_says_when_there_is_no_optimum_to_quote(tmp_path):
    path = write_config(tmp_path, oracle={"type": "key_map"}, sweep={"iteration_range": [0, 5]})
    with pytest.warns(UserWarning, match="key_map takes its marked-set size from the relation") as caught:
        config = load_config(path)
    assert config.sweep.to_range() == range(0, 6)
    assert not any("imply an optimum" in str(w.message) for w in caught)
