"""The scaling fit, produced by the real pipeline rather than handed to the renderer.

The scaling module is tested on synthetic points and the report is tested on a synthetic mapping, and
between the two sits the one path neither reaches: ``cli._attach_scaling`` turning a sweep's own rows
into ``results["scaling"]``. Every sweep elsewhere in the suite has a single measurable width, so that
path is only ever seen *refusing*. Here it is made to succeed, three ways:

* a **QLWR sweep** over ``[4, 12, 14, 16]`` — one width with no admissible instance and three that are
  built and counted, so the fit exists *and* has a refusal travelling beside it;
* a **full experiment** on the corpus's key map over ``[4, 6, 8]``, which reaches the same function
  through ``_attach_analysis`` instead of through ``run_sweep``;
* the **documented script**, ``scripts/sweep_scaling.py``, as a subprocess.

What is asserted is the project's own discipline, on real output: the rows that were built are
labelled ``measured``, every fitted number is labelled ``extrapolated``, the two sit in separate
tables in the rendered report, and no fitted number appears on a measured row. The fit is also
recomputed independently from the sweep rows, because a label on a wrong number is still wrong.

The negative control for all of that is an oracle with no arithmetic form: three widths of
``random_control`` are three measured rows and *no* fit, since the truth-table gate count is a count of
the marked set and fitting it would be fitting ``M``.
"""

from __future__ import annotations

import math
import re
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest
import yaml

from grover_emulator.analysis.scaling_extrapolation import MIN_FIT_POINTS
from grover_emulator.cli import run_experiment, run_sweep
from grover_emulator.reporting.report_generator import (
    EXTRAPOLATED,
    MEASURED,
    REFUSED,
    SCOPE_BOUNDARY,
    load_results,
)

REPO = Path(__file__).resolve().parents[1]
SWEEP_SCRIPT = REPO / "scripts" / "sweep_scaling.py"

QLWR_WIDTHS = [4, 12, 14, 16]
"""One inadmissible width and three faithful ones; 16 is where certification is still about a second."""

KEY_MAP_WIDTHS = [4, 6, 8]
"""Mode A searches two bits per map variable, so these are maps over two, three and four variables."""

EVERY_VALUE_IS_EXTRAPOLATED = "**Every value in this table is `[extrapolated]`.**"


# -----------------------------------------------------------------------------------------------
# configurations, and the runs that spend them
# -----------------------------------------------------------------------------------------------


def _write_config(directory: Path, name: str, *, oracle: dict, widths: list[int]) -> Path:
    """A minimal configuration: the schema's defaults plus an oracle, the widths, and a tmp output."""
    body = {
        "oracle": oracle,
        "sweep": {"qubit_range": widths, "iteration_range": None},
        "backend": {"shots": 200},
        "output": {"dir": (directory / "results").as_posix(), "formats": ["markdown", "json"]},
    }
    path = directory / name
    path.write_text(yaml.safe_dump(body, sort_keys=True), encoding="utf-8")
    return path


@pytest.fixture(scope="module")
def run_root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("scaling-end-to-end")


@pytest.fixture(scope="module")
def qlwr_sweep(run_root: Path):
    """The sweep command's own function over three faithful QLWR widths and one refused one."""
    config = _write_config(
        run_root, "qlwr-sweep.yaml", oracle={"type": "qlwr", "target_qubits": 12}, widths=QLWR_WIDTHS
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_sweep(config, run_id="qlwr-sweep")


@pytest.fixture(scope="module")
def key_map_run(run_root: Path):
    """A whole experiment — curve, probes, baseline — whose sweep has three measurable widths."""
    config = _write_config(
        run_root,
        "key-map.yaml",
        oracle={"type": "key_map", "target_qubits": 8, "key_map_mode": "A"},
        widths=KEY_MAP_WIDTHS,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_experiment(config, run_id="key-map-experiment")


@pytest.fixture(scope="module")
def control_sweep(run_root: Path):
    """Three widths of the negative control: measured rows with no arithmetic circuit to count."""
    config = _write_config(
        run_root,
        "control-sweep.yaml",
        oracle={"type": "random_control", "target_qubits": 6, "marked_fraction": 0.05},
        widths=KEY_MAP_WIDTHS,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return run_sweep(config, run_id="control-sweep")


def _measured_rows(results: dict) -> list[dict]:
    return [row for row in results["sweep"] if row["status"] == "measured"]


def _independent_fit(rows: list[dict]) -> tuple[float, float, float]:
    """``(exponent, scale, r_squared)`` by ``np.polyfit`` on the logs — not the module's own routine."""
    x = np.log([row["n_search"] for row in rows])
    y = np.log([row["gate_count"] for row in rows])
    slope, intercept = np.polyfit(x, y, 1)
    residuals = y - (slope * x + intercept)
    r_squared = 1.0 - float(np.sum(residuals**2)) / float(np.sum((y - y.mean()) ** 2))
    return float(slope), float(math.exp(intercept)), r_squared


def _section(text: str, heading: str) -> str:
    """The report from ``heading`` up to the next heading of the same or a higher level."""
    start = text.index(heading)
    level = len(heading) - len(heading.lstrip("#"))
    following = re.search(rf"^#{{1,{level}}} ", text[start + len(heading):], flags=re.MULTILINE)
    end = start + len(heading) + following.start() if following else len(text)
    return text[start:end]


def _table_rows(block: str) -> list[list[str]]:
    """The body rows of every markdown table in ``block``, as stripped cells."""
    rows = []
    for line in block.splitlines():
        if not line.startswith("| ") or set(line) <= set("|- "):
            continue
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def _is_number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


# -----------------------------------------------------------------------------------------------
# the fit exists, and it is the fit of the rows that were measured
# -----------------------------------------------------------------------------------------------


def test_a_sweep_with_three_measured_widths_produces_a_fit(qlwr_sweep):
    _run_dir, results = qlwr_sweep
    assert results["kind"] == "sweep"
    assert "scaling" in results, results["not_run"].get("scaling")
    assert "scaling" not in results["not_run"]
    assert len(_measured_rows(results)) == 3 >= MIN_FIT_POINTS
    scaling = results["scaling"]
    assert scaling["measured_points_used"] == 3
    assert scaling["measured_range_n_search"] == "12..16"
    assert scaling["form"] == "gate_count = scale * n_search ** exponent"


def test_the_refused_width_travels_beside_the_fit_and_never_enters_it(qlwr_sweep):
    """``n_search = 4`` has no admissible instance: it is a row, a provenance count, and not a point."""
    _run_dir, results = qlwr_sweep
    rows = {row["n_search"]: row for row in results["sweep"]}
    assert rows[4]["status"] == REFUSED and rows[4]["reason"]
    assert "gate_count" not in rows[4]
    provenance = results["scaling"]["sweep_provenance"]
    assert provenance[MEASURED] == 3 and provenance[REFUSED] == 1
    assert provenance["measured_widths"] == [12, 14, 16]
    assert provenance["refused_widths"] == [4]
    assert results["scaling"]["measured_points_used"] == provenance[MEASURED]


def test_the_fit_is_the_least_squares_line_through_the_measured_rows(qlwr_sweep):
    """Recomputed with a different routine from the sweep's own rows, to nine significant figures."""
    _run_dir, results = qlwr_sweep
    rows = _measured_rows(results)
    assert [row["lowering"] for row in rows] == ["arithmetic"] * 3
    assert all(row["gate_count"] > 1000 for row in rows), "the arithmetic oracle is thousands of gates"
    assert [row["gate_count"] for row in rows] == sorted(row["gate_count"] for row in rows)

    exponent, scale, r_squared = _independent_fit(rows)
    scaling = results["scaling"]
    assert scaling["extrapolated_exponent"] == pytest.approx(exponent, rel=1e-9)
    assert scaling["extrapolated_scale_per_width_power"] == pytest.approx(scale, rel=1e-9)
    assert scaling["extrapolated_r_squared"] == pytest.approx(r_squared, rel=1e-9)
    assert scaling["extrapolated_factor_per_doubling_of_width"] == pytest.approx(2.0**exponent, rel=1e-9)
    # Three points and two parameters leave a residual, which is the whole reason three is the floor.
    assert 0.0 < scaling["extrapolated_rms_residual_log2"] <= scaling["extrapolated_max_residual_log2"]
    assert 0.5 < scaling["extrapolated_exponent"] < 3.0


def test_every_fitted_number_carries_extrapolated_in_its_own_key(qlwr_sweep, key_map_run):
    """A float in the fit is a model output, and its key says so; the rest describe the evidence."""
    for _run_dir, results in (qlwr_sweep, key_map_run):
        scaling = results["scaling"]
        floats = {key: value for key, value in scaling.items() if isinstance(value, float)}
        assert len(floats) >= 6
        for key in floats:
            assert key.startswith(f"{EXTRAPOLATED}_"), f"{key} is fitted but not labelled"
            assert MEASURED not in key
        described = {key for key in scaling if not key.startswith(f"{EXTRAPOLATED}_")}
        assert described == {
            "form", "fit_method", "measured_points_used", "measured_range_n_search", "caveat",
            "sweep_provenance",
        }
        assert isinstance(scaling["measured_points_used"], int)


def test_the_caveat_names_the_measured_range_the_numbers_came_from(qlwr_sweep):
    _run_dir, results = qlwr_sweep
    caveat = results["scaling"]["caveat"]
    assert "extrapolated from 3 measured point(s) over n_search = 12..16" in caveat
    assert "was not simulated" in caveat
    assert "a projection is not a measurement" in caveat


def test_the_sweep_rows_are_measured_and_none_of_them_carries_a_fitted_value(qlwr_sweep):
    """The stored rows hold counts from the IR; nothing the model produced is written back into them."""
    _run_dir, results = qlwr_sweep
    fitted = {value for value in results["scaling"].values() if isinstance(value, float)}
    for row in _measured_rows(results):
        assert row["status"] == MEASURED
        assert isinstance(row["gate_count"], int) and isinstance(row["ir_depth"], int)
        assert not any(key.startswith(EXTRAPOLATED) for key in row)
        assert fitted.isdisjoint(value for value in row.values() if isinstance(value, float))


# -----------------------------------------------------------------------------------------------
# the rendered report keeps the two apart
# -----------------------------------------------------------------------------------------------


def test_the_report_tags_built_rows_measured_and_the_refused_row_not_run(qlwr_sweep):
    run_dir, results = qlwr_sweep
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    scaling_section = _section(text, "## Scaling, and where it stops being measurement")
    sweep_table = scaling_section[: scaling_section.index("### The fit")]
    rows = {cells[0]: cells for cells in _table_rows(sweep_table) if cells[0].isdigit()}
    assert sorted(rows, key=int) == ["4", "12", "14", "16"]
    for row in _measured_rows(results):
        cells = rows[str(row["n_search"])]
        assert cells[3] == str(row["gate_count"]) and cells[4] == str(row["ir_depth"])
        assert cells[6] == MEASURED and cells[7] == ""
    assert rows["4"][6] == REFUSED
    assert rows["4"][3] == "-" and rows["4"][7], "a refused row has no gate count and does have a reason"


def test_the_report_puts_the_fit_in_its_own_table_under_the_extrapolated_statement(qlwr_sweep):
    run_dir, _results = qlwr_sweep
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    scaling_section = _section(text, "## Scaling, and where it stops being measurement")
    assert scaling_section.count("### The fit") == 1
    assert scaling_section.index("| provenance |") < scaling_section.index("### The fit")
    fit_block = _section(scaling_section, "### The fit")
    assert EVERY_VALUE_IS_EXTRAPOLATED in fit_block
    assert "a prediction, not a measurement" in fit_block
    # The statement comes after the table it governs and before anything else is tabulated.
    assert fit_block.index("| fit parameter | value |") < fit_block.index(EVERY_VALUE_IS_EXTRAPOLATED)


def test_no_fitted_number_is_printed_on_a_measured_row(qlwr_sweep, key_map_run):
    """The check the project's discipline comes down to, made on the text a reader is given.

    Every numeric cell of the fit table is collected; every row of the report tagged ``measured`` is
    collected; and no fitted cell appears on any such row. The fit table's own rows are then checked
    the other way round: a numeric value there sits under an ``extrapolated_`` key, except the count
    of points the fit used, which is a description of the evidence and equals the measured-row count.
    """
    for run_dir, results in (qlwr_sweep, key_map_run):
        text = (run_dir / "report.md").read_text(encoding="utf-8")
        fit_block = _section(text, "### The fit")
        fit_rows = [cells for cells in _table_rows(fit_block) if cells[0] != "fit parameter"]
        fitted_cells = []
        for key, value, *_rest in fit_rows:
            if not _is_number(value):
                continue
            if key == "measured_points_used":
                assert int(value) == len(_measured_rows(results))
                continue
            assert key.startswith(f"{EXTRAPOLATED}_"), f"{key} = {value} is a number without a label"
            fitted_cells.append(value)
        assert len(fitted_cells) >= 6

        outside_the_fit = text.replace(fit_block, "")
        measured_lines = [
            line for line in outside_the_fit.splitlines() if f"| {MEASURED} |" in line
        ]
        assert len(measured_lines) >= len(_measured_rows(results))
        for line in measured_lines:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            assert not set(cells) & set(fitted_cells), line
            assert EXTRAPOLATED not in line


def test_the_sweep_report_carries_the_scope_boundary_before_its_first_table(qlwr_sweep):
    run_dir, _results = qlwr_sweep
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert SCOPE_BOUNDARY in text
    assert text.index(SCOPE_BOUNDARY) < text.index("|---")


def test_the_stored_mapping_is_what_the_report_was_rendered_from(qlwr_sweep):
    run_dir, results = qlwr_sweep
    stored = load_results(run_dir)
    assert stored["scaling"] == results["scaling"]
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert f"| extrapolated_exponent | {stored['scaling']['extrapolated_exponent']:.6g} |" in text


# -----------------------------------------------------------------------------------------------
# the same path, reached through a whole experiment
# -----------------------------------------------------------------------------------------------


def test_a_full_experiment_attaches_the_fit_beside_its_curve_and_probes(key_map_run):
    run_dir, results = key_map_run
    assert results["kind"] == "experiment"
    assert results["curve"] and results["probes"], "the fit must not displace the other sections"
    assert "scaling" in results and "scaling" not in results["not_run"]
    rows = _measured_rows(results)
    assert [row["n_search"] for row in rows] == KEY_MAP_WIDTHS
    assert results["scaling"]["measured_range_n_search"] == "4..8"

    exponent, scale, _r_squared = _independent_fit(rows)
    assert results["scaling"]["extrapolated_exponent"] == pytest.approx(exponent, rel=1e-9)
    assert results["scaling"]["extrapolated_scale_per_width_power"] == pytest.approx(scale, rel=1e-9)

    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert EVERY_VALUE_IS_EXTRAPOLATED in text
    assert text.index("## Success probability versus iteration") < text.index("### The fit")


def test_the_experiments_own_width_is_one_of_the_fitted_points(key_map_run):
    """The sweep reuses the run's spec at the shared width, so the fitted row is the circuit that ran."""
    _run_dir, results = key_map_run
    row = next(row for row in _measured_rows(results) if row["n_search"] == results["search_width"])
    assert row["gate_count"] == results["circuits"]["oracle (arithmetic)"]["gate_count"]
    assert row["n_marked"] == results["marked_set_size"]


# -----------------------------------------------------------------------------------------------
# the control: measured rows that must not become a fit
# -----------------------------------------------------------------------------------------------


def test_an_oracle_with_no_arithmetic_form_is_swept_and_never_fitted(control_sweep):
    """Three measured widths and no fit: a truth-table gate count is a count of ``M``, not a cost."""
    run_dir, results = control_sweep
    rows = _measured_rows(results)
    assert [row["n_search"] for row in rows] == KEY_MAP_WIDTHS
    assert all("gate_count" not in row for row in rows)
    assert all(row["oracle_gates_truth_table"] > 0 for row in rows)
    assert "scaling" not in results
    assert "carries no gate_count" in results["not_run"]["scaling"]

    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "### The fit" not in text
    assert EVERY_VALUE_IS_EXTRAPOLATED not in text
    assert "carries no gate_count" in _section(text, "## Points that were not run, and why")


# -----------------------------------------------------------------------------------------------
# the documented script
# -----------------------------------------------------------------------------------------------


def test_the_sweep_script_produces_a_labelled_fit(run_root, tmp_path):
    """``scripts/sweep_scaling.py --config ...``, executed: the definition-of-done item, as written."""
    config = run_root / "key-map.yaml"
    if not config.is_file():
        config = _write_config(
            run_root,
            "key-map.yaml",
            oracle={"type": "key_map", "target_qubits": 8, "key_map_mode": "A"},
            widths=KEY_MAP_WIDTHS,
        )
    completed = subprocess.run(
        [
            sys.executable, str(SWEEP_SCRIPT), "--config", str(config),
            "--output-dir", str(tmp_path), "--run-id", "scripted",
        ],
        capture_output=True, text=True, cwd=REPO,
    )
    assert completed.returncode == 0, completed.stderr
    run_dir = tmp_path / "scripted"
    assert str(run_dir / "report.md") in completed.stdout
    stored = load_results(run_dir)
    assert stored["kind"] == "sweep"
    assert stored["scaling"]["measured_points_used"] == 3
    text = (run_dir / "report.md").read_text(encoding="utf-8")
    assert EVERY_VALUE_IS_EXTRAPOLATED in text and f"| {MEASURED} |" in text


# -----------------------------------------------------------------------------------------------
# plan-mandated, and absent
# -----------------------------------------------------------------------------------------------


def test_the_pipeline_projects_the_cost_to_the_128_bit_width(qlwr_sweep):
    """The plan's scaling law is fitted *in order to* project it to ``n = 128``, labelled as such."""
    _run_dir, results = qlwr_sweep
    scaling = results["scaling"]
    projected = [key for key in scaling if key.startswith("extrapolated_gate_count_n_search_")]
    assert "extrapolated_gate_count_n_search_128" in projected, sorted(scaling)
    assert scaling["extrapolated_gate_count_n_search_128"] > _measured_rows(results)[-1]["gate_count"]
    assert any("query" in key or "iterations" in key for key in scaling), sorted(scaling)
