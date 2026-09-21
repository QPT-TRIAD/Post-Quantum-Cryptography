"""The report layer: what a generated report says, and what it refuses to say.

Four properties, and the first is the one the project exists under.

1. **Every report carries the scope boundary verbatim.** Not paraphrased, not summarised, not
   omitted for a short run: the same string the module defines, present in the text that is written,
   on every path through the writer, and before the first section heading and the first table. A
   report whose first table arrived before the boundary would be a table read without it.
2. **The curve is not evidence for itself.** A diagonal phase oracle makes the success probability a
   function of ``(M, N)``, so an engine agreeing with the closed form checks the harness and not the
   physics. The report says so in the preamble and again beside the curve, and the curve table's
   columns are labelled so that a reader cannot take the measured column for independent support.
3. **Regeneration is reproduction.** The report is a view of a stored mapping, so rendering it twice
   from the same directory — through either entry point, with or without a redraw — writes the same
   bytes. Figures are deterministic to the same standard, which is why their PNG metadata is empty.
4. **A refusal travels as a reason.** Every point that was not run appears in its own table with the
   reason and the size that made it one, including the widths whose cost is the finding.

The tests work mostly from a mapping assembled here rather than from a simulated run: the report
layer renders what it is handed, and asserting that on synthetic numbers is both faster and a
stronger statement about the renderer than asserting it on whatever a simulation happened to produce.
The end-to-end path — a real run directory, regenerated through the CLI — is checked against the
smallest real instance.
"""

from __future__ import annotations

import hashlib
import json
import math
import warnings
from pathlib import Path

import pytest
import yaml

from grover_emulator.reporting import plots
from grover_emulator.reporting.report_generator import (
    EXTRAPOLATED,
    MEASURED,
    REFUSED,
    SCOPE_BOUNDARY,
    generate_report,
    generate_report_from_run_dir,
    load_results,
    render_report,
)

RUN_ID = "qlwr-n12-truth_table-s20260913"
N_SEARCH = 12
N_ITEMS = 4096
K_OPT = 50
EXTRA = 2

ARITHMETIC_REFUSAL = (
    # The width and the size are the ones a real refusal produces at this instance. They were 51 and
    # 64.0 PiB while `ancilla_width` counted the flag twice; see notes/02-integration.md. This is a
    # hand-written fixture rather than a measured string, so nothing here fails if it drifts — which
    # is exactly why it is worth keeping true.
    "the arithmetic lowering at n_search=12: qiskit_aer refuses 50 qubits: the run needs 32.0 PiB, "
    "over the 6.0 GiB ceiling. The budget is a refusal rather than a hint: on a machine with swap "
    "already in use, a simulation that overshoots thrashes instead of merely running slowly."
)
INSTANCE_REFUSAL = (
    "no admissible QLWR instance at n_search=4 within the sweep's construction budget of 524288 "
    "candidate draw(s): no generic prime below 2**2"
)
SCALING_REFUSAL = (
    "ScalingError: a power law fitted to 2 point(s) has no residual to inspect and cannot be "
    "contradicted by its own data; at least 3 measured points are required, and this refusal is the "
    "point rather than an inconvenience"
)


# -----------------------------------------------------------------------------------------------
# the mapping a run writes, assembled here
# -----------------------------------------------------------------------------------------------


def _curve(up_to: int = K_OPT + EXTRA) -> list[dict]:
    theta = math.asin(math.sqrt(1 / N_ITEMS))
    records = []
    for k in range(0, up_to + 1):
        p = math.sin((2 * k + 1) * theta) ** 2
        records.append(
            {
                "iteration": k,
                "empirical_p_success": p,
                "theoretical_p_success": p,
                "residual": 0.0,
                "sampled_p_success": p if k == up_to else None,
                "shots": 20000 if k == up_to else 0,
                "provenance": {
                    "empirical_p_success": "measured (exact statevector)",
                    "theoretical_p_success": "closed form sin^2((2k+1)theta)",
                    "sampled_p_success": "measured (shots)" if k == up_to else "not taken",
                },
            }
        )
    return records


def results_mapping(**overrides) -> dict:
    """A results mapping with every section a report can render, and no simulation behind it."""
    mapping: dict = {
        "run_id": RUN_ID,
        "kind": "experiment",
        "config": {
            "run": {"seed": 20260913, "lowering": "truth_table"},
            "oracle": {
                "type": "qlwr",
                "target_qubits": N_SEARCH,
                "marked_fraction": 1.0e-6,
                "nu": 2,
                "seed": 20260913,
                "min_rounding_gap": 3.0,
            },
            "sweep": {"qubit_range": [4, N_SEARCH], "iteration_range": None},
            "backend": {"preference": ["qiskit_aer"], "ram_budget_gb": 6.0, "shots": 20000},
            "probes": {"run_simon_style": True, "run_qft_period": True},
            "output": {"dir": "results/", "formats": ["markdown", "json", "png"]},
        },
        "config_path": "config/default_experiment.yaml",
        "created_utc": "2026-09-13T00:00:00Z",
        "seed": 20260913,
        "spec": {"name": "qlwr", "search_width": N_SEARCH, "n_items": N_ITEMS, "n_marked": 1},
        "instance": {"q_l": 61, "nu": 2, "m": 7, "p": 19, "seed": 20260913},
        "marked_set_size": 1,
        "search_width": N_SEARCH,
        "n_items": N_ITEMS,
        "optimal_iterations": K_OPT,
        "iteration_range": [0, K_OPT + EXTRA],
        "marked_set": [1067],
        "backend": {
            "name": "qiskit_aer",
            "method": "statevector",
            "shots": 20000,
            "sampled_at": K_OPT + EXTRA,
            "exact_statevector_bytes": 16 * (1 << (N_SEARCH + 1)),
            "budget_gb": 6.0,
        },
        "circuits": {
            f"grover k={K_OPT} (truth_table)": {
                "label": f"grover[k={K_OPT},truth_table]",
                "num_qubits": N_SEARCH + 1,
                "gate_count": 4012,
                "counts": {"h": 13, "mcx": 100},
                "toffoli_count": 100,
                "t_count_with_toffolis": 7700,
                "ir_depth": 551,
                "ancilla_peak": 0,
                "classically_simulable": True,
            },
            "oracle (arithmetic)": {
                "label": "oracle[arithmetic]",
                "num_qubits": 50,
                "gate_count": 23269,
                "counts": {"ccx": 13476},
                "toffoli_count": 13476,
                "t_count_with_toffolis": 194894,
                "ir_depth": 14534,
                "ancilla_peak": 0,
                "classically_simulable": False,
            },
        },
        "curve": _curve(),
        "curve_fit": {
            "max_abs_residual": 2.5868e-14,
            "rms_residual": 1.2918e-14,
            "n_points": K_OPT + EXTRA + 1,
            "peak_iteration_agrees": True,
            "peak_iteration_measured": K_OPT,
            "peak_iteration_closed_form": K_OPT,
            "provenance": "fit (a summary of the measured curve against the closed form)",
        },
        "probes": [
            {
                "probe": "simon_style",
                "fired": False,
                "statistic": 12.0,
                "n_qubits": N_SEARCH,
                "total_qubits": N_SEARCH + 1,
                "detail": "not fired: 0 non-zero sample(s) of 64 left 4095 candidate period(s)",
                "caveat": (
                    f"Absence of detected structure at n_search = {N_SEARCH} is evidence about this "
                    "width and not proof that the structure is absent at n = 128."
                ),
                "status": MEASURED,
                "reason": "",
                "provenance": MEASURED,
            },
            {
                "probe": "qft_period",
                "fired": False,
                "statistic": 12.0,
                "n_qubits": N_SEARCH,
                "total_qubits": N_SEARCH + 1,
                "detail": "not fired: 0 non-zero sample(s) of 64 left 4095 candidate period(s)",
                "caveat": (
                    f"Absence of detected structure at n_search = {N_SEARCH} is evidence about this "
                    "width and not proof that the structure is absent at n = 128."
                ),
                "status": MEASURED,
                "reason": "",
                "provenance": MEASURED,
            },
        ],
        "sweep": [
            {
                "n_search": 4,
                "status": REFUSED,
                "reason": INSTANCE_REFUSAL,
                "wall_seconds": 0.0,
            },
            {
                "n_search": N_SEARCH,
                "n_qubits_truth_table": N_SEARCH + 1,
                "n_qubits_arithmetic": 50,
                "statevector_bytes_truth_table": 16 * (1 << (N_SEARCH + 1)),
                "statevector_bytes_arithmetic": 16 * (1 << 50),
                "optimal_iterations": K_OPT,
                "oracle_gates_truth_table": 31,
                "oracle_depth_truth_table": 6,
                "grover_gates_truth_table": 4012,
                "grover_depth_truth_table": 551,
                "gate_count": 23269,
                "ir_depth": 14534,
                "toffoli_count": 13476,
                "t_count_with_toffolis": 194894,
                "ancilla_peak": 0,
                "n_qubits": 50,
                "lowering": "arithmetic",
                "status": MEASURED,
                "wall_seconds": 0.094,
                "statevector_fits_budget_truth_table": True,
                "statevector_fits_budget_arithmetic": False,
            },
        ],
        "scaling": {
            "exponent": 3.4,
            "scale": 0.42,
            "n_points": 3,
            "widths": [12, 16, 20],
            "residuals": [0.0, 0.1, -0.1],
            "provenance": EXTRAPOLATED,
            "sweep_provenance": {"measured": [12, 16, 20], "refused": [4, 8, 24]},
        },
        "validation": [
            {
                "name": "predicate == marked set (truth_table)",
                "ok": True,
                "n_search": N_SEARCH,
                "n_states": N_ITEMS,
                "memory_bytes": 8 * N_ITEMS,
                "detail": f"all {N_ITEMS:,} reachable basis states",
            },
            {
                "name": "predicate == marked set (arithmetic)",
                "ok": True,
                "n_search": N_SEARCH,
                "n_states": N_ITEMS,
                "memory_bytes": 8 * N_ITEMS,
                "detail": f"all {N_ITEMS:,} reachable basis states",
            },
        ],
        "classical_baseline": {
            "queries": 2136,
            "queries_expected": "4097/2",
            "queries_expected_float": 2048.5,
            "queries_worst_case": 4096,
            "grover_iterations": K_OPT,
            "n_items": N_ITEMS,
            "n_marked": 1,
            "caveat": (
                "The baseline here is exhaustive search, which is the algorithm Grover is compared "
                "against and the only one for which the quadratic speedup is a statement at all."
            ),
            "speedup": 40.97,
        },
        "notes": [
            "every stochastic choice is derived from the run seed 20260913",
            "M = 1 was measured by enumerating the search register",
        ],
        "not_run": {
            "statevector pass, arithmetic lowering at n_search=12": ARITHMETIC_REFUSAL,
            "scaling": SCALING_REFUSAL,
        },
        "wall_seconds": 10.2,
    }
    mapping.update(overrides)
    return mapping


@pytest.fixture
def rendered(tmp_path) -> str:
    """The report text for the mapping above, as written to disk."""
    results = results_mapping()
    path = generate_report(tmp_path, results["config"], results, figures=None)
    return path.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------------------------
# the scope boundary
# -----------------------------------------------------------------------------------------------


def test_the_scope_boundary_is_present_verbatim(rendered):
    assert SCOPE_BOUNDARY in rendered
    assert rendered.count(SCOPE_BOUNDARY) == 1
    # Verbatim means one unwrapped line: a reflowed paragraph would no longer contain it.
    line = next(line for line in rendered.splitlines() if SCOPE_BOUNDARY in line)
    assert line.startswith("> ")


def test_the_scope_boundary_comes_before_the_first_heading_and_the_first_table(rendered):
    boundary = rendered.index(SCOPE_BOUNDARY)
    assert boundary < rendered.index("## "), "the boundary must be read before any section"
    assert boundary < rendered.index("|---"), "the boundary must be read before any table"
    assert boundary < rendered.index("|"), "the boundary must be read before any table"
    assert "## What this report does not establish" in rendered


@pytest.mark.parametrize(
    "results",
    [
        {"run_id": "bare"},
        {"run_id": "sweep-only", "kind": "sweep"},
        {"run_id": "refused-everything", "not_run": {"curve": "refused"}},
    ],
    ids=["nothing-but-an-id", "sweep-kind", "everything-refused"],
)
def test_the_boundary_is_emitted_on_every_path_through_the_writer(tmp_path, results):
    """No argument suppresses it, and a report with almost no content still carries it."""
    text = render_report({}, results, run_dir=tmp_path)
    assert SCOPE_BOUNDARY in text
    assert text.splitlines()[0].startswith("# Report: ")
    assert text.index(SCOPE_BOUNDARY) < text.index("## ")


def test_the_boundary_cannot_be_suppressed_by_the_writer(tmp_path):
    """The writer's signature has no switch for it, which is the point rather than an omission."""
    import inspect

    for function in (render_report, generate_report, generate_report_from_run_dir):
        parameters = set(inspect.signature(function).parameters)
        assert not {p for p in parameters if "scope" in p or "boundary" in p}


def test_the_entry_point_refuses_to_run_if_the_boundary_is_altered(monkeypatch):
    from grover_emulator import cli

    cli._require_scope_boundary()  # the real module: no raise
    monkeypatch.setattr(cli, "SCOPE_BOUNDARY", "")
    with pytest.raises(RuntimeError, match="scope boundary is missing or altered"):
        cli._require_scope_boundary()
    monkeypatch.setattr(cli, "SCOPE_BOUNDARY", "something else entirely")
    with pytest.raises(RuntimeError, match="scope boundary is missing or altered"):
        cli._require_scope_boundary()


# -----------------------------------------------------------------------------------------------
# the curve is not evidence for itself
# -----------------------------------------------------------------------------------------------


def test_the_report_never_presents_the_curve_as_independent_evidence(rendered):
    """The one sentence the project cannot do without, in the preamble and again beside the curve."""
    assert "*not* independent evidence for the curve" in rendered
    assert "**not** independent evidence for the closed form" in rendered
    assert "the curve is the control" in rendered
    assert "a check on the harness rather than on the physics" in rendered
    # Stated before the curve is tabulated at all, and again inside its own section.
    assert rendered.index("independent evidence") < rendered.index(
        "## Success probability versus iteration"
    )
    assert rendered.count("a check on the harness") == 2


def test_the_curve_table_separates_the_measured_column_from_the_closed_form(rendered):
    header = next(line for line in rendered.splitlines() if "p_success (measured)" in line)
    assert "p_success (measured)" in header and "p_success (closed form)" in header


def test_a_fit_over_part_of_a_sweep_says_which_part(rendered):
    """A fitted number is never blended with its inputs: the table says extrapolated, and why."""
    assert "**Every value in this table is `[extrapolated]`.**" in rendered
    assert "These are fits to the measured curve `[extrapolated]`" in rendered
    assert "is a prediction, not a measurement" in rendered


def test_a_run_that_refused_to_fit_says_so_rather_than_drawing_a_line(tmp_path):
    results = results_mapping()
    results.pop("scaling")
    results["not_run"]["scaling"] = SCALING_REFUSAL
    text = render_report(results["config"], results, run_dir=tmp_path)
    assert SCALING_REFUSAL in text
    assert "at least 3 measured points are required" in text


def test_a_fitted_number_is_labelled_extrapolated(rendered):
    assert "**Every value in this table is `[extrapolated]`.**" in rendered
    assert "These are fits to the measured curve `[extrapolated]`" in rendered


# -----------------------------------------------------------------------------------------------
# measured, refused, and what a reader can tell apart
# -----------------------------------------------------------------------------------------------


def test_measured_and_refused_points_are_distinguishable_in_the_scaling_table(rendered):
    scaling = rendered.split("## Scaling, and where it stops being measurement")[1]
    assert "| measured |" in scaling or "| measured " in scaling
    scaling_table = scaling.split("## Points that were not run")[0]
    assert f"| {MEASURED} |" in scaling_table
    assert f"| {REFUSED} |" in scaling_table
    assert INSTANCE_REFUSAL in scaling_table


def test_every_refusal_is_recorded_with_its_reason(rendered):
    refusals = rendered.split("## Points that were not run, and why")[1]
    for reason in (ARITHMETIC_REFUSAL, SCALING_REFUSAL):
        assert reason in refusals
    assert INSTANCE_REFUSAL in refusals
    assert "statevector pass, arithmetic lowering at n_search=12" in refusals


def test_the_refusal_table_states_that_it_is_not_dropping_points(rendered):
    assert "deliberately not silently dropped" in rendered


def test_the_run_identity_carries_the_measured_marked_set_and_the_seed(rendered):
    identity = rendered.split("## Run identity")[1].split("\n## ")[0]
    assert "| marked set size M | 1 |" in identity
    assert "| seed | 20260913 |" in identity
    assert "| optimal iterations k_opt | 50 |" in identity
    assert "| backend | qiskit_aer |" in identity


def test_the_configurations_target_fraction_is_not_used_as_the_marked_set(rendered):
    """The target density is a design intention; the report must not present it as M."""
    section = rendered.split("## The marked set, and how M is known")[1].split("\n## ")[0]
    assert "`[measured]`" in section
    assert "it was not read from the configuration's target density" in section
    assert "The configuration aimed at a marked fraction of" in section
    assert "The target is a design intention and enters no computation" in section


def test_the_arithmetic_circuits_cost_is_reported_as_measured_not_as_a_bug(rendered):
    circuits = rendered.split("## The circuit")[1].split("\n## ")[0]
    assert "oracle (arithmetic)" in circuits
    assert "23269" in circuits
    assert "measured" in circuits
    assert "classically_simulable" not in circuits, "internal flags are not prose"


# -----------------------------------------------------------------------------------------------
# regeneration
# -----------------------------------------------------------------------------------------------


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_regeneration_is_byte_identical(tmp_path, rendered):
    results = results_mapping()
    run_dir = tmp_path / "run"
    written = generate_report(run_dir, results["config"], results)
    (run_dir / "metrics.json").write_text(json.dumps(results, default=str), encoding="utf-8")
    assert written.read_text(encoding="utf-8") == rendered

    first = _digest(written)
    generate_report_from_run_dir(run_dir)
    assert _digest(written) == first
    generate_report_from_run_dir(run_dir, filename="again.md")
    assert _digest(run_dir / "again.md") == first


def test_regeneration_does_not_need_the_config_argument(tmp_path):
    """Everything the report needs is in the results directory, including the configuration."""
    results = results_mapping()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "metrics.json").write_text(json.dumps(results, default=str), encoding="utf-8")
    text = generate_report_from_run_dir(run_dir).read_text(encoding="utf-8")
    assert SCOPE_BOUNDARY in text
    assert str(results["config"]["backend"]["ram_budget_gb"]) in text


def test_regeneration_refuses_a_directory_that_is_not_a_finished_run(tmp_path):
    with pytest.raises(FileNotFoundError, match="metrics.json"):
        generate_report_from_run_dir(tmp_path)


def test_rendering_does_not_mutate_the_mapping_it_is_given(tmp_path):
    results = results_mapping()
    before = json.dumps(results, sort_keys=True, default=str)
    render_report(results["config"], results, run_dir=tmp_path)
    assert json.dumps(results, sort_keys=True, default=str) == before
    assert "figures" not in results


# -----------------------------------------------------------------------------------------------
# figures
# -----------------------------------------------------------------------------------------------


def test_figures_are_byte_identical_across_two_renders(tmp_path):
    """Determinism is a property of the drawing, not of the run: same input, same bytes."""
    results = results_mapping()
    first = plots.plot_all(results, tmp_path / "a", budget_gb=6.0)
    second = plots.plot_all(results, tmp_path / "b", budget_gb=6.0)
    assert set(first) == set(second)
    assert len(first) >= 4
    for caption, path in first.items():
        twin = second[caption]
        assert path.read_bytes() == twin.read_bytes(), f"{caption} is not deterministic"


def _png_chunk_types(blob: bytes) -> list[bytes]:
    """Every chunk type in a PNG, read from its structure rather than searched for in the bytes."""
    types: list[bytes] = []
    position = 8  # past the signature
    while position + 12 <= len(blob):
        length = int.from_bytes(blob[position : position + 4], "big")
        types.append(blob[position + 4 : position + 8])
        position += 12 + length
    return types


def test_figures_carry_no_timestamp_or_producer_metadata(tmp_path):
    """Byte-identical output needs the metadata gone, and gone means absent, not empty."""
    results = results_mapping()
    figures = plots.plot_all(results, tmp_path / "figures", budget_gb=6.0)
    for path in figures.values():
        types = _png_chunk_types(path.read_bytes())
        assert types[0] == b"IHDR" and b"IEND" in types
        for unwanted in (b"tEXt", b"iTXt", b"zTXt", b"tIME", b"eXIf"):
            assert unwanted not in types, f"{path.name} carries a {unwanted.decode()} chunk"


def test_a_figure_whose_data_is_absent_is_skipped_not_drawn_empty(tmp_path):
    """An empty axes reads as a measurement of zero, which is a different claim."""
    figures = plots.plot_all({}, tmp_path / "figures", budget_gb=6.0)
    assert figures == {}
    assert not list((tmp_path / "figures").glob("*.png"))

    partial = plots.plot_all({"sweep": results_mapping()["sweep"]}, tmp_path / "partial", budget_gb=6.0)
    assert "success probability against iteration" not in partial
    assert "circuit cost against width" in partial


def test_the_figure_table_names_files_rather_than_paths(tmp_path):
    results = results_mapping()
    figures = plots.plot_all(results, tmp_path / "figures", budget_gb=6.0)
    table = plots.figure_table(results, figures)
    assert table
    for record in table:
        assert "/" not in record["path"]
        assert record["path"].endswith(".png")
        assert record["caption"]


def test_the_report_links_every_figure_it_drew(tmp_path):
    results = results_mapping()
    run_dir = tmp_path / "run"
    figures = plots.plot_all(results, run_dir / "figures", budget_gb=6.0)
    results["figures"] = plots.figure_table(results, figures)
    text = generate_report(run_dir, results["config"], results, figures=figures).read_text("utf-8")
    assert "## Figures" in text
    assert "byte-identical files" in text
    for caption, path in figures.items():
        assert f"](figures/{path.name})" in text
        assert caption in text


def test_a_report_with_no_figures_omits_the_section_rather_than_showing_a_broken_one(tmp_path):
    """No figures means no figure section, and the boundary is still the first thing in the file."""
    results = results_mapping()
    text = generate_report(tmp_path, results["config"], results, figures={}).read_text("utf-8")
    assert SCOPE_BOUNDARY in text
    assert "## Figures" not in text
    assert "![" not in text


def test_describe_scale_states_the_width_and_what_it_costs():
    described = plots.describe_scale(20)
    assert "20 qubits" in described
    assert f"{16 * (1 << 20)} bytes" in described
    assert "24 bits" in described


# -----------------------------------------------------------------------------------------------
# end to end, from a real run directory
# -----------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_run(tmp_path_factory):
    """One real run at the smallest faithful instance, for the paths that need real artefacts."""
    from grover_emulator.config.schema import ExperimentConfig
    from grover_emulator.cli import run_experiment

    root = tmp_path_factory.mktemp("report-runs")
    base = ExperimentConfig()
    body = {
        "run": {"seed": base.run.seed, "lowering": "truth_table"},
        "oracle": {
            "type": "qlwr",
            "target_qubits": 12,
            "marked_fraction": 1.0e-6,
            "nu": 2,
            "seed": base.oracle.seed,
            "min_rounding_gap": 3.0,
        },
        "sweep": {"qubit_range": [12], "iteration_range": None},
        "backend": {"preference": ["qiskit_aer"], "ram_budget_gb": 6.0, "shots": 200},
        "probes": {"run_simon_style": True, "run_qft_period": True},
        "output": {"dir": root.as_posix(), "formats": ["markdown", "json", "png"]},
    }
    path = root / "report-e2e.yaml"
    path.write_text(yaml.safe_dump(body, sort_keys=True), encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        run_dir, _results = run_experiment(path, run_id="report-e2e")
    return run_dir


def test_a_real_run_directory_regenerates_its_report_byte_for_byte(real_run):
    """The report the CLI re-renders is the report the run wrote, figures table included."""
    from grover_emulator.cli import regenerate_report

    first = _digest(real_run / "report.md")
    original = (real_run / "report.md").read_text(encoding="utf-8")
    regenerate_report(real_run)
    assert _digest(real_run / "report.md") == first
    # The captions come from the run's own record, not from the filenames on disk.
    assert "success probability against iteration" in original
    assert "| success probability against iteration | figures/success_curve.png |" in original


def test_a_real_report_carries_the_boundary_and_the_labels(real_run):
    text = (real_run / "report.md").read_text(encoding="utf-8")
    assert SCOPE_BOUNDARY in text
    assert text.index(SCOPE_BOUNDARY) < text.index("|---")
    assert "*not* independent evidence for the curve" in text
    assert "The range was derived per instance" in text
    assert load_results(real_run)["marked_set_size"] == 1


def test_a_real_run_redraws_its_figures_byte_for_byte(real_run):
    """The redraw path replays the stored mapping: disk in, disk out, same bytes."""
    from grover_emulator.cli import regenerate_report

    before = {path.name: _digest(path) for path in sorted((real_run / "figures").glob("*.png"))}
    assert before
    regenerate_report(real_run, filename="report.md", redraw=True)
    after = {path.name: _digest(path) for path in sorted((real_run / "figures").glob("*.png"))}
    assert after == before
