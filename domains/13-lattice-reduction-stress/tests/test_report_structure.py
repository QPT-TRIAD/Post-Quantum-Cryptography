"""The report's structure: six sections, in the design document's order, each holding only its own.

Section 3.13 of the design document fixes the order — (1) scope boundary, (2) tested parameters and
dimensions, (3) empirical results marked "measured", (4) the estimator at the same scale marked
"theoretical, same scale", (5) the production-scale extrapolation marked "extrapolated — not
measured", (6) anomalies. Until this file the suite asserted that the boundary was *present* and
that section 5 rendered; nothing asserted the list, its order, or what each section may contain.
``SECTION_ORDER`` was read by no code and no test, so it could say anything.

Everything is asserted on a report the real pipeline wrote. A three-dimension sweep is the smallest
run that fills all six sections at once: it has measured attack points, a same-scale estimate, a
cross-sweep fit with an extrapolated half, and — because enumeration recovers the secret far below
the model's prediction at these sizes — a genuine anomaly. A hand-built results mapping would test
the renderer against the test author's idea of the producer, which is the boundary that has already
broken once in this project.

Sections are located twice, independently: by ``SECTION_ORDER`` and by where the headings sit in the
text. Table cells are compared whole, never by substring, so ``2.92`` cannot be "found" inside
``0.02921``.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pytest

from qlwr_lattice_stress.analysis.cost_estimation import estimate, parameter_set_from_instance
from qlwr_lattice_stress.analysis.empirical_vs_theoretical import compare_block_sizes
from qlwr_lattice_stress.config.schema import ExperimentConfig
from qlwr_lattice_stress.pipeline import _jsonable, build_instance, run_sweep
from qlwr_lattice_stress.protocols import (
    EXTRAPOLATED,
    MEASURED,
    NOT_RUN,
    PROVENANCE_LABELS,
    SAME_SCALE,
)
from qlwr_lattice_stress.reporting import (
    SCOPE_BOUNDARY,
    assert_boundary_precedes_first_table,
    figure_paths,
    generate_report,
    generate_report_from_run_dir,
    load_results,
    plot_block_size_curve,
    plot_measured_vs_extrapolated,
)
from qlwr_lattice_stress.reporting.report_generator import SECTION_ORDER
from qlwr_lattice_stress.utils.seeding import RunSeeds

SEED = 20260913
DIMENSIONS = (40, 50, 60)

#: The design document's sections 2-6 as the headings that open them, keyed the way
#: ``SECTION_ORDER`` names them. Section 1 is the boundary paragraph, which has no heading.
HEADING_OF = {
    "parameters": "## 2. Tested parameters and dimensions",
    "measured": f"## 3. Empirical results — {PROVENANCE_LABELS[MEASURED]}",
    "theoretical_same_scale": f"## 4. Cost model at the same scale — {PROVENANCE_LABELS[SAME_SCALE]}",
    "extrapolated": f"## 5. Production-scale extrapolation — {PROVENANCE_LABELS[EXTRAPOLATED]}",
    "anomalies": "## 6. Anomalies",
    "carried_forward": "## 7. Scope exclusions and contradictions carried forward",
}


def _config(output_dir: Path) -> ExperimentConfig:
    return ExperimentConfig.model_validate({
        "instance": {"source": "synthetic_scaled", "target_dimension": 60, "seed": SEED},
        "engine": {"preference": ("fpylll_bkz",), "threads": 1},
        "attack": {"types": ("primal", "dual"), "block_size_range": (10, 20, 30)},
        "sweep": {"dimension_range": DIMENSIONS},
        "output": {"dir": output_dir},
    })


@pytest.fixture(scope="module")
def sweep(tmp_path_factory):
    """One real sweep, shared. Returns ``(config, outcomes)``; every outcome has a run directory."""
    pytest.importorskip("estimator", reason="lattice-estimator is not importable")
    config = _config(tmp_path_factory.mktemp("report-structure"))
    outcomes = run_sweep(config)
    assert [o.get("provenance") for o in outcomes] == [None] * len(DIMENSIONS), outcomes
    return config, outcomes


@pytest.fixture(scope="module")
def results(sweep) -> dict:
    """The dimension-60 run: the results mapping the pipeline produced, not one assembled here."""
    return sweep[1][-1]


@pytest.fixture(scope="module")
def text(results) -> str:
    return (Path(results["run_dir"]) / "report.md").read_text()


def _section(markdown: str, number: int) -> str:
    """The body of section ``number``, from its heading to the next ``## `` heading."""
    match = re.search(rf"^## {number}\. .*?(?=^## |\Z)", markdown, flags=re.M | re.S)
    assert match, f"section {number} is absent"
    return match.group(0)


def _cells(section: str) -> list[list[str]]:
    """Every table row of a section as its cells, header and separator rows excluded."""
    rows = []
    for line in section.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def _numbers(section: str) -> set[str]:
    return {c for row in _cells(section) for c in row if re.fullmatch(r"-?\d+(\.\d+)?(e-?\d+)?", c)}


# ---------------------------------------------------------------------------------------------
# the six sections, in order
# ---------------------------------------------------------------------------------------------


def test_the_fixture_run_fills_every_section(results):
    """Anti-vacuity for everything below: a results mapping with an empty section would let the
    "nothing leaked into it" assertions pass on an empty string."""
    assert any(a["provenance"] == MEASURED for a in results["attacks"])
    assert any(a["provenance"] == NOT_RUN for a in results["attacks"])
    assert results["estimator_same_scale"]["beta_usvp"]
    assert results["scaling"]["kind"] == "block_size_growth"
    assert any(c["anomaly"] for c in results["comparisons"])


def test_the_sections_appear_in_the_design_documents_order_by_position(text):
    """Independent of ``SECTION_ORDER``: the six, literally, by where they sit in the text."""
    landmarks = [
        SCOPE_BOUNDARY,                                        # (1) scope boundary
        "## 2. Tested parameters and dimensions",              # (2)
        "## 3. Empirical results — measured",                  # (3)
        "## 4. Cost model at the same scale — theoretical, same scale",          # (4)
        "## 5. Production-scale extrapolation — extrapolated — not measured",    # (5)
        "## 6. Anomalies",                                     # (6)
    ]
    for landmark in landmarks:
        assert text.count(landmark) == 1, f"{landmark[:40]!r} appears {text.count(landmark)} times"
    positions = [text.index(landmark) for landmark in landmarks]
    assert positions == sorted(positions), positions

    # Nothing sits between them that the list does not account for: the numbered headings are
    # exactly 2..7, consecutive, with the project's seventh after the design document's six.
    numbered = re.findall(r"^## (\d+)\. ", text, flags=re.M)
    assert numbered == ["2", "3", "4", "5", "6", "7"]
    assert len(re.findall(r"^## ", text, flags=re.M)) == 6, "an unnumbered section was added"


def test_section_order_describes_the_report_that_is_written(text):
    """``SECTION_ORDER`` is only meaningful if it is true. Each key is tied to its heading, and the
    constant's order must be the order those headings occur in — so reordering ``generate_report``
    without the constant, or the constant without the report, fails here."""
    assert set(SECTION_ORDER) == set(HEADING_OF), set(SECTION_ORDER) ^ set(HEADING_OF)
    positions = [text.index(HEADING_OF[key]) for key in SECTION_ORDER]
    assert positions == sorted(positions), list(zip(SECTION_ORDER, positions))

    # The three provenance-bearing sections are named by the protocol's own constants, in
    # decreasing order of evidence, and sit together between the parameters and the anomalies.
    assert SECTION_ORDER[1:4] == (MEASURED, SAME_SCALE, EXTRAPOLATED)
    assert SECTION_ORDER[0] == "parameters" and SECTION_ORDER[4] == "anomalies"


def test_an_empty_results_mapping_still_yields_every_section_in_order(tmp_path):
    """The structure is not a property of a well-populated run. A run that recorded nothing must
    still say, section by section, that it recorded nothing."""
    empty = generate_report(tmp_path, {}, {}).read_text()
    positions = [empty.index(SCOPE_BOUNDARY)] + [empty.index(HEADING_OF[k]) for k in SECTION_ORDER]
    assert positions == sorted(positions)
    assert "_No attack points were recorded._" in _section(empty, 3)
    assert "_The estimator was not run for this instance._" in _section(empty, 4)
    assert "_No fit was produced for this run._" in _section(empty, 5)


def test_each_provenance_heading_carries_exactly_its_own_label(text):
    labels = {3: "measured", 4: "theoretical, same scale", 5: "extrapolated — not measured"}
    for number, label in labels.items():
        heading = _section(text, number).splitlines()[0]
        assert heading.endswith(f"— {label}"), heading
        for other_number, other in labels.items():
            if other_number != number and other != "measured":
                assert other not in heading, f"section {number} is also labelled {other!r}"
    assert "extrapolated" not in _section(text, 3).splitlines()[0]
    assert "theoretical" not in _section(text, 3).splitlines()[0]


# ---------------------------------------------------------------------------------------------
# the boundary
# ---------------------------------------------------------------------------------------------


def test_the_scope_boundary_precedes_the_first_table_and_the_first_heading(text):
    assert text.index(SCOPE_BOUNDARY) < text.index("|---")
    assert text.index(SCOPE_BOUNDARY) < text.index("\n## ")
    assert_boundary_precedes_first_table(text)

    # And the checker is not vacuous: the same report with the boundary moved to the end is caught,
    # although ``SCOPE_BOUNDARY in text`` still holds for it.
    moved = text.replace(SCOPE_BOUNDARY, "") + "\n" + SCOPE_BOUNDARY + "\n"
    assert SCOPE_BOUNDARY in moved
    with pytest.raises(AssertionError, match="after the first table"):
        assert_boundary_precedes_first_table(moved)
    with pytest.raises(AssertionError, match="absent"):
        assert_boundary_precedes_first_table(text.replace(SCOPE_BOUNDARY, ""))


#: The design document's scope-boundary paragraph, as it stands at the top of that document, after
#: the bold run-in label. Embedded rather than read: this project never opens the research tree, and
#: a preamble that is "verbatim" has to be checkable without it.
DESIGN_DOCUMENT_BOUNDARY = (
    "this system cannot run BKZ or sieving at your full production dimension/modulus if those "
    "parameters are large — reduction cost grows exponentially in the block size needed, by design "
    "(that's what makes the scheme secure). What it *can* do: run the actual algorithms exactly, "
    "correctly, and completely at scaled-down dimensions, measure real empirical hardness there, "
    "and extrapolate to the full parameter set using the same cost models NIST uses for PQC "
    "categories 1–5. Any generated report must present measured and extrapolated numbers in "
    "clearly separate sections — never blend them."
)


def _plain(markdown: str) -> str:
    """Whitespace collapsed, emphasis markers dropped, case folded: what "verbatim" survives."""
    return " ".join(markdown.replace("*", "").split()).casefold()


def test_the_boundary_says_the_four_things_it_exists_to_say():
    """The load-bearing phrases, which the constant and the design document's paragraph share. This
    pins the constant against an edit that softens it; it passes before and after the fix below."""
    plain = _plain(SCOPE_BOUNDARY)
    assert plain.startswith("scope boundary")
    for phrase in (
        "cannot run bkz or sieving",
        "reduction cost grows exponentially in the block size needed",
        "scaled-down dimensions",
        "measure real empirical hardness there",
        "extrapolate to the full parameter set",
        "never blend",
    ):
        assert phrase in plain, phrase


def test_the_boundary_is_the_design_documents_paragraph_verbatim():
    """Verbatim up to markdown emphasis, whitespace and the capital after the run-in label. The
    constant may *add* to the paragraph — it closes with a sentence about security claims — but the
    paragraph itself has to be in it, unedited."""
    assert _plain(DESIGN_DOCUMENT_BOUNDARY) in _plain(SCOPE_BOUNDARY)


# ---------------------------------------------------------------------------------------------
# section 3 holds the measurements, and only them
# ---------------------------------------------------------------------------------------------


def test_section_three_carries_the_measured_block_size_hermite_factor_and_wall_clock(results, text):
    rows = _cells(_section(text, 3))
    measured = [a for a in results["attacks"] if a["provenance"] == MEASURED]
    for attack in measured:
        row = next(
            (r for r in rows if r[0] == attack["family"] and r[1] == str(attack["block_size"])), None
        )
        assert row is not None, f"no row for block size {attack['block_size']}"
        family, block, dimension, engine, provenance, recovered, wall_clock, hermite = row
        assert int(dimension) == attack["dimension"]
        assert engine == f"{attack['engine']} ×{attack['threads']}"
        assert provenance == "measured"
        assert recovered == ("yes" if attack["recovered"] else "no")
        assert float(wall_clock) == pytest.approx(attack["wall_clock_s"], rel=1e-3)
        assert float(hermite) == pytest.approx(attack["root_hermite_factor"], rel=1e-3)

    minimum = results["minimum_block_sizes"]["primal_usvp"]
    assert ["primal_usvp", str(minimum)] in rows, "the minimum block size is not in section 3"
    assert ["dual", "not reached"] in rows


def test_a_point_that_did_not_run_is_not_rendered_as_a_measurement(results, text):
    """The section is headed "measured", so a row in it that was not measured has to say so itself."""
    not_run = [a for a in results["attacks"] if a["provenance"] == NOT_RUN]
    assert not_run, "the fixture has no not-run point, so this would prove nothing"
    rows = _cells(_section(text, 3))
    for attack in not_run:
        row = next(r for r in rows if r[0] == attack["family"] and len(r) == 8)
        assert row[4].startswith(PROVENANCE_LABELS[NOT_RUN]), row
        assert row[4] != PROVENANCE_LABELS[MEASURED]
        assert row[3] == "—" and row[7] == "—", "a point that did not run shows an engine or a factor"


def test_a_not_run_row_points_at_a_section_that_holds_its_reason(results, text):
    attack = next(a for a in results["attacks"] if a["provenance"] == NOT_RUN)
    assert "see section 6" in _section(text, 3)
    # The reason's opening clause is enough; the whole string is long and may be re-wrapped.
    assert attack["not_run_reason"][:60] in _section(text, 6)


def test_no_extrapolated_number_appears_in_section_three(results, text):
    """The rule the project is built on, as a set intersection. The fit's target block size equals
    a measured block size in this run (the fit is flat), so the numbers checked are the two that
    exist *only* as model outputs: the core-SVP cost and its constant."""
    extrapolated = results["scaling"]["extrapolated"]
    model_only = {f"{extrapolated['core_svp_log2_cost']:.4g}", f"{extrapolated['core_svp_c']:.4g}"}
    assert model_only <= _numbers(_section(text, 5)), "the fixture's extrapolation was not rendered"

    for number in (2, 3):
        leaked = model_only & _numbers(_section(text, number))
        assert not leaked, f"extrapolated value(s) {leaked} appear in section {number}"
    assert "extrapolated" not in _section(text, 3).casefold()


def test_no_measured_number_is_labelled_extrapolated(results, text):
    """Section 5 has a measured half (the fit) and an extrapolated half, and says which rows are
    which. Each half must hold its own values; the attack measurements belong to neither."""
    section = _section(text, 5)
    rows = [r for r in _cells(section) if r != ["quantity", "value"]]
    labels = [r[0] for r in rows]
    assert "The first five rows are **measured**" in section
    assert "The last four are **extrapolated**" in section
    assert len(rows) == 9

    fit, beyond = results["scaling"]["measured"], results["scaling"]["extrapolated"]
    measured_half, extrapolated_half = dict(rows[:5]), dict(rows[5:])
    assert float(measured_half["slope (block sizes per unit dimension)"]) == pytest.approx(fit["slope"])
    assert float(measured_half["intercept"]) == pytest.approx(fit["intercept"], rel=1e-3)
    assert measured_half["dimensions fitted"].startswith(
        f"{fit['fitted_dimension_min']}–{fit['fitted_dimension_max']}"
    )
    assert float(extrapolated_half["core-SVP log2 cost there"]) == pytest.approx(
        beyond["core_svp_log2_cost"], rel=1e-3
    )
    assert float(extrapolated_half["predicted block size there"]) == pytest.approx(
        beyond["predicted_block_size"], rel=1e-3
    )
    assert not {"slope (block sizes per unit dimension)", "intercept", "R squared"} & set(labels[5:])

    # The per-point measurements (wall clock, root-Hermite factor) are section 3's alone.
    # The root-Hermite factor is rendered at seven significant digits and compared at seven: a
    # *rooted* factor is 1.0-and-a-bit, so at four digits every one of them reads "1.0xx" or plain
    # "1" and collides with an R squared of 1 in section 5. (At four digits this test once passed
    # only because the factor it saw was the un-rooted one, which is distinctive by accident.)
    precision = {"wall_clock_s": ".4g", "root_hermite_factor": ".7g"}
    point_values = {
        format(a[key], spec) for a in results["attacks"] if a["provenance"] == MEASURED
        for key, spec in precision.items()
    }
    assert point_values <= _numbers(_section(text, 3))
    assert not point_values & _numbers(section)
    assert not point_values & _numbers(_section(text, 4))


def test_section_four_holds_the_same_scale_estimate(results, text):
    report = results["estimator_same_scale"]
    assert report["provenance"] == SAME_SCALE
    rows = dict(r for r in _cells(_section(text, 4)) if len(r) == 2)
    assert rows["usvp block size"] == str(report["beta_usvp"])
    assert float(rows["log2 rop, usvp"]) == pytest.approx(report["rop_usvp_log2"], rel=1e-3)
    assert rows["estimator revision"] == report["estimator_revision"]
    assert "the same scaled instance that was attacked" in _section(text, 4)


# ---------------------------------------------------------------------------------------------
# section 6
# ---------------------------------------------------------------------------------------------


def test_the_pipelines_own_anomaly_reaches_section_six(results, text):
    section = _section(text, 6)
    anomalies = [c for c in results["comparisons"] if c["anomaly"]]
    assert anomalies
    for comparison in anomalies:
        assert f"- dimension {comparison['dimension']}: {comparison['anomaly']}" in section
    assert "No anomaly" not in section
    # And nowhere else: an anomaly rendered under "measured" would read as a measurement.
    for number in (2, 3, 4, 5):
        assert anomalies[0]["anomaly"][:50] not in _section(text, number)


def test_an_anomaly_from_the_real_comparison_reaches_section_six_and_agreement_does_not(
    sweep, results, tmp_path
):
    """Built through ``compare_block_sizes`` on the real estimate for the real instance, so the
    text asserted is whatever that function writes rather than a string this test made up."""
    config, _ = sweep
    instance = build_instance(config, RunSeeds(root=SEED))
    report = estimate(parameter_set_from_instance(instance))
    assert report.beta_usvp is not None

    far = compare_block_sizes(
        dimension=instance.m + 1, measured_min_block_size=3 * report.beta_usvp, report=report
    )
    agrees = compare_block_sizes(
        dimension=instance.m + 1, measured_min_block_size=report.beta_usvp, report=report
    )
    assert far.anomaly and "above the prediction" in far.anomaly
    assert agrees.anomaly is None

    def section_six(comparisons, name):
        doctored = {**results, "comparisons": [_jsonable(c) for c in comparisons]}
        return _section(generate_report(tmp_path / name, config, doctored).read_text(), 6)

    flagged = section_six([far, agrees], "flagged")
    assert f"- dimension {instance.m + 1}: {far.anomaly}" in flagged
    assert flagged.count("- dimension") == 1, "the agreeing comparison was listed as an anomaly"

    quiet = section_six([agrees], "quiet")
    assert "_No anomaly: every comparison that ran agreed within its stated tolerance._" in quiet
    assert "- dimension" not in quiet


# ---------------------------------------------------------------------------------------------
# the round trip
# ---------------------------------------------------------------------------------------------


def test_the_report_regenerated_from_the_run_directory_is_byte_identical(sweep):
    """For every run of the sweep: a report produced from what a run *recorded* must equal the one
    it produced live, or the stored record does not describe the run."""
    for outcome in sweep[1]:
        run_dir = Path(outcome["run_dir"])
        live = (run_dir / "report.md").read_bytes()
        config_before = (run_dir / "config.yaml").read_bytes()

        again = generate_report_from_run_dir(run_dir, filename="regenerated.md")
        assert again == run_dir / "regenerated.md"
        assert again.read_bytes() == live
        assert (run_dir / "report.md").read_bytes() == live, "regenerating under a new name rewrote the original"
        assert (run_dir / "config.yaml").read_bytes() == config_before, "config.yaml is not a fixed point"


def test_the_stored_results_are_the_results_that_were_returned(results):
    stored = load_results(results["run_dir"])
    assert stored["attacks"] == json.loads(json.dumps(results["attacks"]))
    assert stored["scaling"] == json.loads(json.dumps(_jsonable(results["scaling"])))
    assert load_results(Path(results["run_dir"]) / "no-such-run") == {}


# ---------------------------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------------------------

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def kept_figure(monkeypatch):
    """Let a test look at a figure after the plotting function has saved it.

    The functions close their figure, correctly. ``pyplot.close`` is held back for the duration of
    one test so the title and legend can be read from the figure that was actually saved, rather
    than re-deriving them; everything is closed afterwards.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    real_close = plt.close
    plt.close("all")
    monkeypatch.setattr(plt, "close", lambda *args, **kwargs: None)
    yield plt
    real_close("all")


def _measured_points(outcomes) -> list[tuple[int, float]]:
    return [
        (a["block_size"], a["wall_clock_s"])
        for o in outcomes for a in o["attacks"] if a["provenance"] == MEASURED
    ]


def test_the_block_size_curve_is_a_png_titled_measured(sweep, tmp_path, kept_figure):
    points = _measured_points(sweep[1])
    assert len(points) >= 3
    out = plot_block_size_curve(points, dimension=60, out_path=tmp_path / "figures" / "curve.png")

    assert out == tmp_path / "figures" / "curve.png"
    assert out.read_bytes()[:8] == PNG_SIGNATURE and out.stat().st_size > 2000

    import matplotlib

    assert matplotlib.get_backend().casefold() == "agg"
    axes = kept_figure.gcf().axes[0]
    assert axes.get_title() == f"Reduction cost, dimension 60 — {PROVENANCE_LABELS[MEASURED]}"
    assert "extrapolated" not in axes.get_title()
    (line,) = axes.get_lines()
    assert list(line.get_xdata()) == [p[0] for p in points]
    assert line.get_linestyle() == "None", "measured points were joined into a curve"


def test_the_block_size_curve_refuses_to_draw_nothing(tmp_path):
    with pytest.raises(ValueError, match="no points"):
        plot_block_size_curve([], dimension=60, out_path=tmp_path / "empty.png")
    assert not (tmp_path / "empty.png").exists()


def test_measured_and_extrapolated_are_two_labelled_series_never_one_line(
    sweep, results, tmp_path, kept_figure
):
    """Two series on one axis look like one dataset unless the figure itself says otherwise — so
    the legend, the line styles and the separation of the data are all asserted on the figure."""
    measured = [(beta, math.log2(seconds)) for beta, seconds in _measured_points(sweep[1])]
    c = results["scaling"]["extrapolated"]["core_svp_c"]
    extrapolated = [(beta, c * beta) for beta in (30, 60, 90)]

    out = plot_measured_vs_extrapolated(
        measured, extrapolated, out_path=tmp_path / "figures" / "both.png"
    )
    assert out.read_bytes()[:8] == PNG_SIGNATURE and out.stat().st_size > 2000

    axes = kept_figure.gcf().axes[0]
    legend = [t.get_text() for t in axes.get_legend().get_texts()]
    assert legend == [PROVENANCE_LABELS[MEASURED], PROVENANCE_LABELS[EXTRAPOLATED]]

    measured_line, model_line = axes.get_lines()
    assert measured_line.get_label() == "measured"
    assert model_line.get_label() == "extrapolated — not measured"
    assert measured_line.get_linestyle() == "None" and measured_line.get_marker() == "o"
    assert model_line.get_linestyle() == "--"
    assert measured_line.get_color() != model_line.get_color()
    assert list(measured_line.get_xdata()) == [p[0] for p in measured]
    assert list(model_line.get_xdata()) == [30, 60, 90], "the model's line runs through measured points"


def test_figure_paths_lists_what_a_run_drew(sweep, tmp_path):
    assert figure_paths(tmp_path) == [], "a run with no figures directory has no figures"
    points = _measured_points(sweep[1])
    plot_block_size_curve(points, dimension=60, out_path=tmp_path / "figures" / "b.png")
    plot_block_size_curve(points, dimension=60, out_path=tmp_path / "figures" / "a.png")
    (tmp_path / "figures" / "notes.txt").write_text("not a figure")
    assert figure_paths(tmp_path) == [tmp_path / "figures" / "a.png", tmp_path / "figures" / "b.png"]
