"""Markdown reports, with the scope boundary as a structural guarantee rather than a convention.

The design document requires that *"any generated report must present measured and extrapolated
numbers in clearly separate sections — never blend them"*. That is enforced here in three ways, each
of which would have to be defeated deliberately rather than by accident:

1. **The preamble is emitted on every path**, and the absence of an argument that suppresses it is
   the point. A report without the boundary is not a report this project produces.
2. **It precedes the first table**, checked by index rather than membership. A boundary that
   appeared in a footnote after three results tables would satisfy a substring check while defeating
   its purpose.
3. **Each section is labelled with its provenance** — ``measured``, ``theoretical, same scale``, or
   ``extrapolated — not measured`` — taken from the protocol's own labels so a section and its
   heading cannot drift apart.

There are **seven** sections rather than the six the design document lists. The seventh carries the
things the project found but did not resolve: the corpus's internal contradiction about whether ``p``
must be prime, the ambiguous sample-exposure count, the small-dimension model artifact, and the
primal/dual asymmetry. A report that omitted those would read as a clean result, and it is not one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from ..protocols import PROVENANCE_LABELS, EXTRAPOLATED, MEASURED, NOT_RUN, SAME_SCALE

__all__ = [
    "SCOPE_BOUNDARY",
    "SECTION_ORDER",
    "generate_report",
    "generate_report_from_run_dir",
    "assert_boundary_precedes_first_table",
    "load_results",
]

#: The scope-boundary paragraph from the **top of the design document**, which its section 3.13
#: requires at the head of every report — verbatim up to the bold run-in label and the capital that
#: follows it, and not wrapped in anything that would let a reader take the results without it. The
#: closing sentence about security claims is this project's addition, *after* the paragraph and not
#: inside it.
#:
#: This comment used to say "verbatim from section 7" over a paraphrase, and the design document has
#: no section 7. The paragraph is pinned, as a literal, by
#: ``tests/test_report_structure.py::test_the_boundary_is_the_design_documents_paragraph_verbatim`` —
#: a constant that claims to be a quotation has to be checkable as one.
SCOPE_BOUNDARY = (
    "**Scope boundary.** This system cannot run BKZ or sieving at your full production "
    "dimension/modulus if those parameters are large — reduction cost grows exponentially in the "
    "block size needed, by design (that's what makes the scheme secure). What it *can* do: run the "
    "actual algorithms exactly, correctly, and completely at scaled-down dimensions, measure real "
    "empirical hardness there, and extrapolate to the full parameter set using the same cost models "
    "NIST uses for PQC categories 1–5. Any generated report must present measured and extrapolated "
    "numbers in clearly separate sections — never blend them. Nothing here is a security claim "
    "about the production parameters."
)

#: The order sections are emitted in. The boundary is first and the caveats last, and the three
#: provenance-bearing sections sit between them in decreasing order of evidence.
SECTION_ORDER = (
    "parameters",
    "measured",
    "theoretical_same_scale",
    "extrapolated",
    "anomalies",
    "carried_forward",
)

_TABLE_MARKER = "|---"


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def _fmt(value: Any, *, digits: int = 4) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def assert_boundary_precedes_first_table(markdown: str) -> None:
    """The boundary must appear *before* any table, not merely somewhere in the document.

    An index comparison rather than a substring check. A report whose boundary appeared after three
    tables of results would pass ``SCOPE_BOUNDARY in text`` while a reader had already read the
    numbers without it — which is the failure this asserts against.
    """
    if SCOPE_BOUNDARY not in markdown:
        raise AssertionError("the scope boundary is absent from the report")
    if _TABLE_MARKER not in markdown:
        return  # no tables, so nothing to precede
    if markdown.index(SCOPE_BOUNDARY) > markdown.index(_TABLE_MARKER):
        raise AssertionError(
            "the scope boundary appears after the first table. A reader reaches the numbers before "
            "the caveat, which defeats the purpose of having one."
        )


def _section_parameters(results: Mapping[str, Any]) -> str:
    instance = results.get("instance", {})
    config = results.get("config", {})
    rows = [
        ["instance source", instance.get("label", "—")],
        ["secret dimension (nu)", _fmt(instance.get("nu"))],
        ["modulus (q_l)", _fmt(instance.get("q_l"))],
        ["rounding modulus (p)", _fmt(instance.get("p"))],
        ["rows (m)", _fmt(instance.get("m"))],
        ["rounding ratio q_l/p", _fmt(instance.get("rounding_ratio"))],
        ["noise bound", _fmt(instance.get("noise_bound"))],
        ["noise interval", instance.get("noise_interval", "—")],
        ["equivalent sigma", _fmt(instance.get("equivalent_gaussian_sigma"))],
        ["bit-shift rounding", instance.get("is_bit_shift_rounding", False)],
        ["q-ary lattice dimension", _fmt(instance.get("qary_lattice_dimension"))],
        ["uSVP lattice dimension", _fmt(instance.get("usvp_lattice_dimension"))],
        ["seed", _fmt(instance.get("seed"))],
    ]
    return "## 2. Tested parameters and dimensions\n\n" + _table(["quantity", "value"], rows)


def _engine_cell(a: Mapping[str, Any]) -> str:
    """``engine ×threads``, or a dash where nothing ran.

    Threads are shown because they decide what the row *is*: G6K returns bit-identical bases at one
    thread and does not above it, so a minimum found at four threads cannot be re-derived from the
    seed the run recorded. A table that showed only the block size would present a single draw and a
    measurement identically.
    """
    name = a.get("engine")
    if not name:
        return "—"
    threads = a.get("threads")
    return f"{name} ×{threads}" if threads else name


def _section_measured(results: Mapping[str, Any]) -> str:
    attacks = results.get("attacks", [])
    rows = []
    for a in attacks:
        # The provenance column is not decoration. A point whose *reduction* ran but whose
        # distinguisher was inapplicable has a wall-clock time and no result, and without the column
        # it reads exactly like a point that was tried and found nothing — which is a different
        # claim, and the weaker one.
        provenance = a.get("provenance", MEASURED)
        label = PROVENANCE_LABELS.get(provenance, provenance)
        if provenance == NOT_RUN and a.get("not_run_reason"):
            label = f"{label} — see section 6"
        rows.append([
            a.get("family", "primal"),
            _fmt(a.get("block_size")),
            _fmt(a.get("dimension")),
            _engine_cell(a),
            label,
            "yes" if a.get("recovered") else "no",
            _fmt(a.get("wall_clock_s")),
            # Seven significant digits, where every other cell has four. The root-Hermite factor is
            # 1.0-something by construction and everything it says is in the third decimal and
            # beyond: at four digits a dimension-61 run renders as "1" in every row. That was
            # invisible while the engine reported the *un-rooted* factor under this name (1.012 and
            # up, until 2026-09-20); with the root taken, four digits is a column of ones.
            _fmt(a.get("root_hermite_factor"), digits=7),
        ])
    body = _table(
        ["family", "block size", "dimension", "engine", "provenance", "recovered",
         "wall clock (s)", "root-Hermite"],
        rows,
    ) if rows else "_No attack points were recorded._"

    # The dimension column carries two different lattices, because the two families reduce
    # different things. Saying so is not pedantry: this column previously mixed the embedded width
    # with the un-normalised one, so a reader saw 161 and 228 in adjacent rows of the same table and
    # had no way to tell which was the lattice under attack.
    dimension_note = (
        "\n\nThe **dimension** column is the width of the lattice *that family actually reduces*, "
        "which is not the same number for both: the primal attack embeds the normal-form q-ary "
        "lattice and adds one row and one column, while the dual attack reduces the dual of that "
        "lattice. Rows within a family share a dimension, because the lattice does not change when "
        "the block size does.\n"
    )

    # Only worth saying when it applies. Where every point ran at one thread the sentence would be
    # noise; where any point ran above it, the reader is looking at single draws.
    multi = sorted({a.get("threads") for a in attacks
                    if a.get("threads") and a.get("threads") > 1})
    threads_note = ""
    if multi:
        threads_note = (
            f"\n\n**The `engine` column matters here.** These points ran at "
            f"{', '.join(str(t) for t in multi)} threads. Measured: G6K returns bit-identical bases "
            "at one thread and does not above it, so a result at more than one thread is a *single "
            "draw*, not a measurement reproducible from the seed the run recorded. A minimum block "
            "size taken at those settings is one sample of a distribution; re-running may give a "
            "different one.\n"
        )

    minima = results.get("minimum_block_sizes", {})
    extra = ""
    if minima:
        extra = "\n\n**Minimum successful block size by family**\n\n" + _table(
            ["family", "minimum block size"],
            [[k, _fmt(v) if v is not None else "not reached"] for k, v in minima.items()],
        )
    return (
        f"## 3. Empirical results — {PROVENANCE_LABELS[MEASURED]}\n\n"
        "Everything in this section was executed on this machine.\n\n"
        + body + dimension_note + threads_note + extra
    )


def _section_theoretical(results: Mapping[str, Any]) -> str:
    report = results.get("estimator_same_scale", {})
    if not report:
        return (
            f"## 4. Cost model at the same scale — {PROVENANCE_LABELS[SAME_SCALE]}\n\n"
            "_The estimator was not run for this instance._\n"
        )
    rows = [
        ["usvp block size", _fmt(report.get("beta_usvp"))],
        ["dual block size", _fmt(report.get("beta_dual"))],
        ["log2 rop, usvp", _fmt(report.get("rop_usvp_log2"))],
        ["log2 rop, dual", _fmt(report.get("rop_dual_log2"))],
        ["log2 rop, minimum over models (classical)", _fmt(report.get("rop_classical_log2_min"))],
        ["log2 rop, minimum over models (quantum)", _fmt(report.get("rop_quantum_log2_min"))],
        ["model attaining the minimum", report.get("minimum_over_models", "—")],
        ["estimator revision", report.get("estimator_revision", "—")],
        ["cost model", report.get("red_cost_model", "—")],
        ["shape model", report.get("red_shape_model", "—")],
    ]
    inapplicable = report.get("model_parameters", {}).get("inapplicable_models", [])
    note = ""
    if inapplicable:
        note = (
            "\n\n**Model families that do not apply to this instance:** "
            + ", ".join(inapplicable)
            + ". An infinite cost means the attack has no valid parameters here, not that it is "
            "impossible at any cost — the distinction matters because it is the difference between "
            "a prediction and the absence of one.\n"
        )
    return (
        f"## 4. Cost model at the same scale — {PROVENANCE_LABELS[SAME_SCALE]}\n\n"
        "The estimator's prediction for **the same scaled instance that was attacked**. Comparing "
        "against a model evaluated at a different scale would measure the extrapolation rather than "
        "the physics.\n\n" + _table(["quantity", "value"], rows) + note
    )


def _section_extrapolated(results: Mapping[str, Any]) -> str:
    scaling = results.get("scaling", {})
    if not scaling:
        return (
            f"## 5. Production-scale extrapolation — {PROVENANCE_LABELS[EXTRAPOLATED]}\n\n"
            "_No fit was produced for this run._\n"
        )
    # The fit carries two shapes. A per-run fit is flat; the cross-sweep fit is nested
    # (`measured` / `extrapolated`), because its two steps must stay separately labelled. Reading
    # only one shape renders the other as a row of dashes — which a reader takes as "no fit was
    # produced" rather than "the report could not read the fit it was given". That is a boundary
    # defect of exactly the kind this project's cross-checks exist to catch, and it was caught here
    # by looking at the rendered output rather than at the numbers.
    if scaling.get("kind") == "block_size_growth":
        measured = scaling.get("measured", {})
        extrapolated = scaling.get("extrapolated", {})
        rows = [
            ["what was fitted", "required block size against lattice dimension"],
            ["slope (block sizes per unit dimension)", _fmt(measured.get("slope"))],
            ["intercept", _fmt(measured.get("intercept"))],
            ["R squared", _fmt(measured.get("r_squared"))],
            ["dimensions fitted", f"{measured.get('fitted_dimension_min')}–{measured.get('fitted_dimension_max')}"
                                  f"  ({_fmt(measured.get('n_points'))} points)"],
            ["target dimension", _fmt(extrapolated.get("target_dimension"))],
            ["predicted block size there", _fmt(extrapolated.get("predicted_block_size"))],
            ["core-SVP log2 cost there", _fmt(extrapolated.get("core_svp_log2_cost"))],
            ["core-SVP constant c", _fmt(extrapolated.get("core_svp_c"))],
        ]
        note = (
            "\n\nThe first five rows are **measured** — the relationship a sweep can actually "
            "observe. The last four are **extrapolated**: the fit evaluated at a dimension beyond "
            "those fitted, and the core-SVP model applied at the resulting block size. The two "
            "steps are separate and separately labelled, so the extrapolation can be rejected "
            "without rejecting the measurement.\n"
        )
        return (
            f"## 5. Production-scale extrapolation — {PROVENANCE_LABELS[EXTRAPOLATED]}\n\n"
            "**Not measured.** Model outputs fitted to the scaled measurements and evaluated beyond "
            "them; they carry the model's assumptions.\n\n"
            + _table(["quantity", "value"], rows)
            + note
        )

    rows = [
        ["slope c in 2^(c*beta)", _fmt(scaling.get("c"))],
        ["intercept", _fmt(scaling.get("intercept"))],
        ["R squared", _fmt(scaling.get("r_squared"))],
        ["points fitted", _fmt(scaling.get("n_points"))],
        ["fitted block size range", f"{scaling.get('fitted_beta_min')}–{scaling.get('fitted_beta_max')}"],
        ["beyond the fitted range", "yes" if scaling.get("extrapolates_outside_fitted_domain") else "no"],
    ]
    return (
        f"## 5. Production-scale extrapolation — {PROVENANCE_LABELS[EXTRAPOLATED]}\n\n"
        "**Not measured.** These are model outputs fitted to the scaled measurements above and "
        "evaluated beyond them; they carry the model's assumptions with them.\n\n"
        + _table(["quantity", "value"], rows)
    )


def _section_anomalies(results: Mapping[str, Any]) -> str:
    comparisons = results.get("comparisons", [])
    anomalies = [c for c in comparisons if c.get("anomaly")]
    notes = [c for c in comparisons if not c.get("anomaly") and c.get("note")]
    parts = []
    if anomalies:
        parts.append("**Anomalies — a disagreement at this size is a result, not noise.**\n")
        parts.extend(f"- dimension {c.get('dimension')}: {c['anomaly']}" for c in anomalies)
    else:
        parts.append("_No anomaly: every comparison that ran agreed within its stated tolerance._")
    if notes:
        parts.append("\n**Comparisons not made**, with the reason — these are *not* disagreements:")
        parts.extend(f"- dimension {c.get('dimension')}: {c['note']}" for c in notes)

    # Section 3 labels a refused row "not run — see section 6", so the reason has to *be* here. It
    # was not: this section rendered ``comparisons`` alone, and neither a row's ``not_run_reason``
    # nor ``results["not_run"]`` reached the report at all — a pointer to a section that did not
    # hold what it pointed at. Both sources are listed, because they overlap without either
    # containing the other: a refused primal point exists only as a row, a refused fit only as a
    # step. A reason that arrives by both routes (the dual attack's does) is written once.
    refusals: list[str] = []
    seen: set[str] = set()
    for a in results.get("attacks", []):
        reason = a.get("not_run_reason")
        if a.get("provenance") == NOT_RUN and reason and reason not in seen:
            seen.add(reason)
            refusals.append(
                f"- {a.get('family', 'primal')}, block size {_fmt(a.get('block_size'))}: {reason}"
            )
    for entry in results.get("not_run", []):
        reason = entry.get("reason")
        if reason and reason not in seen:
            seen.add(reason)
            refusals.append(f"- {entry.get('step', 'step')}: {reason}")
    if refusals:
        parts.append("\n**Not run**, with the reason — a refusal is *not* a failed attempt:")
        parts.extend(refusals)
    return "## 6. Anomalies\n\n" + "\n".join(parts)


def _section_carried_forward(results: Mapping[str, Any]) -> str:
    """The seventh section: what the project found and did not resolve.

    A report that omitted these would read as a clean result. It is not one — the corpus contradicts
    itself about the modulus, the sample-exposure count is ambiguous, and the cost model has a
    measured regime of inapplicability. Each is stated here rather than left for a reader to
    rediscover.
    """
    items = results.get("carried_forward") or _DEFAULT_CARRIED_FORWARD
    return (
        "## 7. Scope exclusions and contradictions carried forward\n\n"
        "Findings this project recorded and **did not resolve**. They are listed here because a "
        "report without them reads as a clean result.\n\n"
        + "\n".join(f"- {item}" for item in items)
    )


#: Always emitted, because none of them is a property of a particular run.
_DEFAULT_CARRIED_FORWARD = (
    "The corpus requires **p prime** for public tracing (`security_proof_v1.3.md:101`) while the "
    "only recorded numeric parameter set uses **p = 2^8** (`research_qualification_v1.18.md:257`). "
    "Both are recorded; neither is chosen.",
    "The **sample-exposure count is ambiguous and large**: m = 608 rows versus an exposure of "
    "672,352. Those are different sample counts to an attack, and a cost estimate is only meaningful "
    "alongside which reading it was made under.",
    "The cost model **does not apply below roughly 28 unknowns**, where the predicted block size "
    "approaches the lattice dimension and the model's cost figure is inapplicable rather than wrong. "
    "Measured boundary in notes/04.",
    "The estimator is **insensitive to both QLWR-specific deviations** — uniform versus Gaussian "
    "error, and power-of-two versus prime modulus — at every size tested. It cannot distinguish a "
    "QLWR instance from an LWE one at the same (n, q, m, sigma).",
    "The **primal and dual families diverge at this scale**: the primal attack reaches and the dual "
    "does not, for an arithmetic reason recorded in notes/06. Since the estimator reports the minimum "
    "over both, a run that exercised only the dual would conclude the instance was hard.",
    "`attack_lab_results_v1.51.md:7` states the QLWR-based construction *was refuted and replaced*, "
    "while `pqt.md:309-347` still defines QLWR as a live assumption. This tool does not resolve that "
    "and does not appear to.",
)


def generate_report(
    run_dir: str | Path, config: Any, results: Mapping[str, Any], figures: Any = None, *,
    filename: str = "report.md",
) -> Path:
    """Write ``report.md`` into ``run_dir`` and return its path.

    ``config`` may be a validated configuration, its mapping form, or a path to the YAML — and it is
    written into the results directory beside the report so a run can be reproduced from what it
    recorded rather than from what the operator remembers.
    """
    from ..config.schema import ExperimentConfig, dump_config, load_config

    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(config, (str, Path)):
        config_mapping = dump_config(load_config(config))
    elif isinstance(config, ExperimentConfig):
        config_mapping = dump_config(config)
    else:
        config_mapping = dict(config)

    results = dict(results)
    results.setdefault("config", config_mapping)

    title = results.get("run_id") or run_dir.name
    sections = [
        f"# {title}\n",
        SCOPE_BOUNDARY,
        _section_parameters(results),
        _section_measured(results),
        _section_theoretical(results),
        _section_extrapolated(results),
        _section_anomalies(results),
        _section_carried_forward(results),
    ]
    markdown = "\n\n".join(sections) + "\n"

    # Checked before writing, so an invalid report is never the artefact left on disk.
    assert_boundary_precedes_first_table(markdown)

    (run_dir / "config.yaml").write_text(_to_yaml(config_mapping))
    path = run_dir / filename
    path.write_text(markdown)
    return path


def _to_yaml(mapping: Mapping[str, Any]) -> str:
    import yaml

    return yaml.safe_dump(dict(mapping), sort_keys=False)


def load_results(run_dir: str | Path) -> dict:
    """Read a run's ``metrics.json``, or an empty mapping if the run recorded none."""
    path = Path(run_dir) / "metrics.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def generate_report_from_run_dir(
    run_dir: str | Path, *, figures: Any = None, filename: str = "report.md"
) -> Path:
    """Regenerate a report from a stored results directory.

    The round trip is the point: a report produced from what a run *recorded* must match the one it
    produced live, or the stored record does not describe the run. The sibling project asserts this
    by regenerating and comparing.
    """
    run_dir = Path(run_dir)
    results = load_results(run_dir)
    config_path = run_dir / "config.yaml"
    config: Any = config_path if config_path.exists() else {}
    return generate_report(run_dir, config, results, figures, filename=filename)
