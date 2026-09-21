"""The run report, and the boundary it must state before anything else.

**The scope boundary is structural, not framing.** :data:`SCOPE_BOUNDARY` is emitted, verbatim, as
the first thing after the title of every report this module produces — before any results table, in
every code path, including the path where a results directory is empty and nothing could be
reported. It is not a disclaimer appended to a claim; it is the thing that decides which claims the
rest of the document is allowed to make. A test asserts it appears verbatim, and a test asserts it
appears before the first table.

Three further statements are required of every report and are emitted unconditionally, in the
report's own words rather than as a quoted constant:

* **No security conclusion.** Nothing here is a statement about a production parameter set, and a
  probe that did not fire at ``n_search = 20`` did not fire at ``n_search = 20``.
* **A diagonal phase oracle contributes nothing to the success curve.** The curve is a function of
  ``(M, N)`` alone. "The curve ran on Aer" is therefore *not* independent evidence for the curve —
  the closed form is the evidence. What the circuit contributes is that it *certifies M* (the
  marked set the circuit implements is the marked set the closed form is evaluated on, checked
  exhaustively at widths where that is possible) and that it *costs something* (the gate counts,
  which no ``(M, N)`` recursion can produce).
* **Measured versus extrapolated.** Every number carries its provenance. A fit is labelled a fit
  wherever it appears, and no fitted number is ever presented as a measurement.

The results mapping this module consumes is the same JSON the run writes to ``metrics.json``, so a
report can be regenerated from a finished results directory without re-running anything — which is
the point of writing it from a stored mapping rather than from live objects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TypedDict

__all__ = [
    "SCOPE_BOUNDARY",
    "RunResults",
    "generate_report",
    "render_report",
    "load_results",
    "generate_report_from_run_dir",
]

SCOPE_BOUNDARY = (
    "This system does not and cannot simulate a fault-tolerant quantum computer breaking 128-bit "
    "security — the state space is exponential and no classical machine can hold it at that scale. "
    "What it *does* provide is exact, verifiable quantum simulation at small n (real amplitudes, "
    "real interference, real measurement statistics), from which structural conclusions and "
    "resource extrapolations can be drawn."
)
"""The scope boundary, as one unwrapped string.

Kept as a single line on purpose: a report that reflows it into paragraphs would no longer contain
it, and "the report contains it verbatim" is a property a string comparison can check only if the
string survives being written.
"""

MEASURED = "measured"
"""The number was produced by building and running something at this width."""

EXTRAPOLATED = "extrapolated"
"""The number came out of a fitted model. It is not a measurement and is never labelled as one."""

REFUSED = "not run"
"""The point was not attempted, and the reason is recorded with it rather than omitted."""


class RunResults(TypedDict, total=False):
    """The results contract, as written to ``metrics.json`` and read back by the report.

    Every key is optional: a report is generated from whatever a run managed to produce, and a
    section whose data is absent is printed as "not run" with the reason from :attr:`not_run`
    rather than being dropped. A missing section that vanishes silently is a report that reads as
    complete while covering less, which is the failure mode this whole module exists to avoid.
    """

    run_id: str
    kind: str
    """``"experiment"`` or ``"sweep"``."""
    config: dict
    """The validated configuration as written into the run directory, echoed by the report."""
    created_utc: str
    """Stamped when the run starts, never by the renderer: regenerating a report must reproduce it
    byte for byte from the same directory."""
    config_path: str
    seed: int
    spec: dict
    """:meth:`OracleSpec.describe`."""
    instance: dict
    """``QLWRInstance.describe()`` where the spec has one."""
    marked_set_size: int
    """``M``, measured. Never the config's target fraction."""
    search_width: int
    n_items: int
    """``N``."""
    optimal_iterations: int
    iteration_range: list[int]
    lowering: str
    backend: dict
    circuits: dict
    """``{label: GateList.to_dict()}``, each counted from the IR."""
    curve: list
    """Records of ``iteration, empirical_p_success, theoretical_p_success``."""
    curve_fit: dict
    """Whatever :func:`fit_residuals` returned — a fit, labelled as one."""
    probes: list
    """Records of ``probe, fired, statistic, n_qubits, detail, caveat``."""
    scaling: dict
    sweep: list
    validation: list
    classical_baseline: dict
    notes: list
    not_run: dict
    """``{section: reason}`` for sections this run could not produce."""
    figures: list


# -----------------------------------------------------------------------------------------------
# tolerant readers
# -----------------------------------------------------------------------------------------------


def _as_mapping(config: Any) -> dict:
    """Normalise the ``config`` argument: a model, a mapping, or a path to a YAML file."""
    if config is None:
        return {}
    if isinstance(config, Mapping):
        return dict(config)
    if isinstance(config, (str, Path)):
        from ..config.schema import dump_config, load_config

        return dump_config(load_config(config))
    dump = getattr(config, "model_dump", None)
    if callable(dump):
        return dump(mode="json")
    raise TypeError(f"cannot read a configuration from {type(config).__name__}")


def _records(value: Any) -> list[dict]:
    """Normalise a table argument: a list of mappings, or a pandas DataFrame."""
    if value is None:
        return []
    if hasattr(value, "to_dict") and hasattr(value, "columns"):
        return [dict(row) for row in value.to_dict(orient="records")]
    if isinstance(value, Mapping):
        return [dict(value)]
    out: list[dict] = []
    for row in value:
        out.append(dict(row) if isinstance(row, Mapping) else {"value": row})
    return out


def _get(mapping: Mapping[str, Any] | None, key: str, default: Any = None) -> Any:
    if not mapping:
        return default
    value = mapping.get(key, default)
    return default if value is None else value


def _num(value: Any, digits: int = 6) -> str:
    """Format a number for a table without inventing precision it does not have."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    # A structure is a fact too — one equation's linear terms, monomials and constant, say — and a
    # compact JSON rendering keeps it on the one line a table cell is, rather than a Python repr
    # with quotes that a reader has to parse back.
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, separators=(",", ":")) if value else "-"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:  # NaN, from a fit that did not converge
            return "nan"
        if value == 0.0:
            return "0"
        magnitude = abs(value)
        if magnitude < 1e-4 or magnitude >= 1e6:
            return f"{value:.{digits - 2}e}"
        return f"{value:.{digits}g}"
    return str(value)


def _table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    rows = [list(r) for r in rows]
    if not rows:
        return ""
    head = "| " + " | ".join(str(h) for h in headers) + " |"
    rule = "|" + "|".join("---" for _ in headers) + "|"
    body = ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join([head, rule, *body])


def _bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items if item)


# -----------------------------------------------------------------------------------------------
# sections
# -----------------------------------------------------------------------------------------------


def _preamble() -> str:
    """The boundary and the statements every report owes a reader. Emitted unconditionally."""
    return f"""> {SCOPE_BOUNDARY}

## What this report does not establish

**No security conclusion is drawn about any production parameter set.** Nothing below is a statement
about the security of QPT-128 or of any other deployed parameters. Every circuit here is built and
simulated at a width where the state space fits in memory on one machine, and a probe that did not
fire at that width did not fire at that width — it is not evidence that the same structure is absent
at a width that holds a real secret.

**A diagonal phase oracle contributes nothing to the success curve.** For any marked set the curve
depends on `M` and `N` and on nothing else: `sin^2((2k+1)theta)` with `theta = arcsin(sqrt(M/N))`.
That is why "the curve ran on Aer" is *not* independent evidence for the curve — an engine executing
a diagonal phase oracle reproduces a function of `(M, N)` that the closed form already gives exactly,
and agreement between the two is a check on the harness rather than on the physics. The circuit's
contribution to this project is two other things: it **certifies `M`** — the marked set the closed
form is evaluated on is the marked set the circuit implements, which is checked exhaustively at
widths where the whole reachable subspace can be enumerated rather than assumed — and it **costs
something**, the gate counts and depth that no amplitude recursion over `(M, N)` can produce. The
cost is the finding; the curve is the control.

**Measured and extrapolated numbers are distinguished throughout.** A number tagged `measured` was
produced by building and running something at that width. A number tagged `extrapolated` came out of
a fitted model and is a prediction, including every value at a width above the statevector ceiling.
Fitted statistics are labelled as fits wherever they appear, and no fitted value is quoted in place
of a measurement.

**This run's seed and marked-set size are stated explicitly**: the seed is in the run identity table
below, and `M` is the measured size of the marked set — enumerated, not taken from the configuration.
"""


def _identity_section(config: Mapping[str, Any], results: Mapping[str, Any]) -> str:
    oracle = _get(config, "oracle", {}) or {}
    run = _get(config, "run", {}) or {}
    backend = _get(results, "backend", {}) or {}

    rows = [
        ("run id", _get(results, "run_id", "-")),
        ("kind", _get(results, "kind", "experiment")),
        ("seed", _get(results, "seed", _get(run, "seed", "-"))),
        ("oracle type", _get(oracle, "type", _get(_get(results, "spec", {}) or {}, "name", "-"))),
        ("search width n_search", _get(results, "search_width", "-")),
        ("marked set size M", _get(results, "marked_set_size", "-")),
        ("search space size N", _get(results, "n_items", "-")),
        ("marked fraction M/N", _num(_fraction(results), 4)),
        ("optimal iterations k_opt", _get(results, "optimal_iterations", "-")),
        ("iteration range", _range_text(_get(results, "iteration_range"))),
        ("oracle lowering", _get(results, "lowering", _get(run, "lowering", "-"))),
        ("backend", _get(backend, "name", _get(backend, "engine", "-"))),
        ("shots", _get(backend, "shots", _get(_get(config, "backend", {}) or {}, "shots", "-"))),
        ("created", _get(results, "created_utc", "-")),
    ]
    body = "\n".join(f"| {name} | {value} |" for name, value in rows)
    return f"""## Run identity

| field | value |
|---|---|
{body}

`M` in the closed form and `M` here are the same object: it is the size of the marked set the
circuit implements, measured by enumerating the search register. A report whose `M` came from the
configuration rather than from the marked set would be describing a different problem from the one
its circuit computes.
"""


def _fraction(results: Mapping[str, Any]) -> float | None:
    n_marked = _get(results, "marked_set_size")
    n_items = _get(results, "n_items")
    if not n_marked or not n_items:
        return None
    return n_marked / n_items


def _range_text(value: Any) -> str:
    if not value:
        return "-"
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return f"[{value[0]}, {value[1]}] inclusive"
    return str(value)


_BASE_SPEC_FACTS = frozenset(
    {
        "name",
        "supports_arithmetic_lowering",
        "search_width",
        "n_items",
        "n_marked",
        "marked_fraction",
        "optimal_iterations",
        "ancilla_width_truth_table",
        "ancilla_width_arithmetic",
    }
)
"""The spec facts the property table below states, so that they are not stated twice.

Everything else a spec reports about itself is the relation's own — which convention a chain was
evaluated under, over how many applications, which register a key map was searched over — and is
printed beside those properties rather than left behind in the mapping. A spec that reports no more
than the eight above renders exactly the table it did before.
"""


def _marked_set_section(results: Mapping[str, Any]) -> str:
    spec = _get(results, "spec", {}) or {}
    instance = _get(results, "instance", {}) or {}
    parts = ["## The marked set, and how M is known", ""]
    n_marked = _get(results, "marked_set_size")
    n_items = _get(results, "n_items")
    if n_marked is None:
        reason = _reason(results, "marked_set")
        parts.append(f"Not measured: {reason}")
        return "\n".join(parts)

    parts.append(
        f"`M = {n_marked}` of `N = {n_items}` basis states ({_num(_fraction(results), 4)} of the "
        "space). This was measured by enumerating the search register and evaluating the relation on "
        "every value `[measured]`; it was not read from the configuration's target density."
    )
    target = _target_fraction(results)
    if target is not None:
        parts.append(
            f"\nThe configuration aimed at a marked fraction of `{_num(target, 4)}`; the measured "
            f"fraction is `{_num(_fraction(results), 4)}`. The target is a design intention and "
            "enters no computation — M does."
        )
    if spec:
        parts.append("")
        parts.append(
            _table(
                ["property", "value"],
                [
                    ("spec", _get(spec, "name", "-")),
                    ("supports arithmetic lowering", _get(spec, "supports_arithmetic_lowering", "-")),
                    ("search width", _get(spec, "search_width", "-")),
                    ("n_items (N)", _get(spec, "n_items", "-")),
                    ("n_marked (M)", _get(spec, "n_marked", "-")),
                    ("optimal iterations", _get(spec, "optimal_iterations", "-")),
                    ("ancilla width, truth table", _get(spec, "ancilla_width_truth_table", "-")),
                    ("ancilla width, arithmetic", _get(spec, "ancilla_width_arithmetic", "-")),
                ],
            )
        )
        own_facts = sorted(
            (key, value) for key, value in spec.items() if key not in _BASE_SPEC_FACTS
        )
        if own_facts:
            parts.append("")
            parts.append(
                "The relation's own facts. They are the spec's rather than the harness's, and they "
                "say which problem the numbers above describe: one relation read two ways is two "
                "different search problems, with different marked sets and different gate counts, "
                "so the fact that pins the reading is part of the measurement rather than a note "
                "about it."
            )
            parts.append("")
            parts.append(_table(["fact", "value"], [(key, _num(value, 6)) for key, value in own_facts]))
    if instance:
        gap = _get(instance, "embedding_gap")
        parts.append("")
        parts.append("### The instance's own parameters")
        parts.append("")
        parts.append(
            _table(
                ["parameter", "value"],
                [(k, _num(v, 6) if isinstance(v, (int, float)) else v) for k, v in instance.items()],
            )
        )
        if gap:
            parts.append("")
            parts.append(
                f"The register is wider than the space it encodes: `2**n_search - q_l**nu = {gap}` "
                "basis states encode no valid secret and are never marked. That is a consequence of "
                "requiring a generic modulus (a power of two would admit arithmetic shortcuts and "
                "turn the gate-count fit into a fit of the shortcut), and it is reported rather than "
                "hidden: `M` and `N` in the closed form remain exact."
            )
    return "\n".join(parts)


def _target_fraction(results: Mapping[str, Any]) -> float | None:
    config = _get(results, "config", {}) or {}
    oracle = _get(config, "oracle", {}) or {}
    return oracle.get("marked_fraction")


def _circuit_section(results: Mapping[str, Any]) -> str:
    circuits = _get(results, "circuits", {}) or {}
    parts = ["## The circuit", ""]
    if not circuits:
        parts.append(f"Not built: {_reason(results, 'circuits')}")
        return "\n".join(parts)

    rows = []
    for label, metrics in circuits.items():
        metrics = metrics or {}
        counts = _get(metrics, "counts", {}) or {}
        rows.append(
            [
                label,
                _get(metrics, "num_qubits", "-"),
                _get(metrics, "gate_count", "-"),
                counts.get("mcx", 0) + counts.get("ccx", 0),
                _get(metrics, "toffoli_count", "-"),
                _get(metrics, "t_count_with_toffolis", "-"),
                _get(metrics, "ir_depth", "-"),
                _get(metrics, "ancilla_peak", "-"),
                MEASURED,
            ]
        )
    parts.append(
        _table(
            [
                "circuit",
                "width",
                "gates",
                "controlled-X (>=3 in)",
                "toffoli count",
                "t-count (7-T assumption)",
                "IR depth",
                "ancilla peak",
                "provenance",
            ],
            rows,
        )
    )
    parts.append("")
    parts.append(
        "Every count above is computed from the gate-list IR `[measured]`, never read off a "
        "framework's circuit object: framework gates may carry undocumented ancillas, and qiskit's "
        "and cirq's depth definitions disagree with each other. Where a decomposition assumption is "
        "unavoidable the assumption is named next to the number — the T-count assumes the standard "
        "7-T ancilla-free Toffoli."
    )
    return "\n".join(parts)


def _curve_section(results: Mapping[str, Any]) -> str:
    curve = _records(_get(results, "curve"))
    parts = ["## Success probability versus iteration", ""]
    if not curve:
        parts.append(f"Not measured: {_reason(results, 'curve')}")
        return "\n".join(parts)

    rows = []
    for record in curve:
        rows.append(
            [
                _get(record, "iteration", "-"),
                _num(_get(record, "empirical_p_success")),
                _num(_get(record, "theoretical_p_success")),
            ]
        )
    parts.append(_table(["iteration", "p_success (measured)", "p_success (closed form)"], rows))

    measured = [
        (int(_get(r, "iteration", 0)), float(_get(r, "empirical_p_success", 0.0)))
        for r in curve
        if _get(r, "empirical_p_success") is not None
    ]
    theoretical = [
        (int(_get(r, "iteration", 0)), float(_get(r, "theoretical_p_success", 0.0)))
        for r in curve
        if _get(r, "theoretical_p_success") is not None
    ]
    parts.append("")
    if measured:
        k_measured, p_measured = max(measured, key=lambda pair: pair[1])
        parts.append(
            f"The measured curve peaks at `k = {k_measured}` with `p = {_num(p_measured)}` "
            "`[measured]`."
        )
    if theoretical:
        k_theory, p_theory = max(theoretical, key=lambda pair: pair[1])
        parts.append(
            f"\nThe closed form `sin^2((2k+1)theta)` peaks at `k = {k_theory}` with "
            f"`p = {_num(p_theory)}` `[closed form]`."
        )
    optimum = _get(results, "optimal_iterations")
    if optimum is not None:
        parts.append(
            f"\nThe range was derived per instance from this spec's own optimum "
            f"(`k_opt = {optimum}`, plus a margin so the curve is seen to turn over). A fixed range "
            "is a bug for exactly this reason: the curve is only evidence of a peak if the window "
            "is known to contain one."
        )

    parts.append("")
    parts.append(
        "`p_success (measured)` comes from executing the circuit; `p_success (closed form)` is the "
        "analytic `sin^2((2k+1)theta)` for this `(M, N)`. Their agreement is a check on the harness "
        "and **not** independent evidence for the closed form — a diagonal phase oracle contributes "
        "nothing to the curve, so the curve carries no information the closed form did not already "
        "have. What the circuit adds is elsewhere in this report: the certification of `M` and the "
        "gate counts."
    )

    fit = _get(results, "curve_fit", {}) or {}
    parts.append("")
    if fit:
        parts.append("### Fit of the measured curve against the closed form")
        parts.append("")
        parts.append(
            _table(
                ["statistic", "value"],
                [
                    (k, _num(v, 6) if v is None or isinstance(v, (int, float, list)) else v)
                    for k, v in fit.items()
                ],
            )
        )
        parts.append("")
        # The flag gets a sentence of its own, above the table's fold: a significant deviation is
        # the one row here that must not be read past, and a `yes` in a table of magnitudes is
        # exactly where it would be.
        significant = _get(fit, "deviation_significant")
        if significant is True:
            parts.append(
                "**Flagged: the measured curve deviates significantly from the closed form** at "
                f"iteration(s) `{_num(_get(fit, 'significant_iterations'))}` — further than "
                f"`{_num(_get(fit, 'significance_threshold_sigmas'))}` binomial standard deviations "
                "at the recorded shot count, by a factor of "
                f"`{_num(_get(fit, 'max_residual_over_noise_bound'))}` over that bound at worst. "
                "That is not sampling noise: it is a bug in the harness or a finding about the "
                "problem, and the averaged statistics above must not be read without it."
            )
            parts.append("")
        elif significant is None and "deviation_significant" in fit:
            parts.append(
                "The deviation was not judged for significance: the curve records carry no shot "
                "count, so there is no sampling noise to judge it against."
            )
            parts.append("")
        parts.append(
            "These are fits to the measured curve `[extrapolated]`: they summarise the departure of "
            "the measurement from the closed form, and are not themselves measurements of anything."
        )
    else:
        parts.append(f"No residual fit: {_reason(results, 'curve_fit')}")
    return "\n".join(parts)


def _probe_section(results: Mapping[str, Any]) -> str:
    probes = _records(_get(results, "probes"))
    parts = ["## Structural probes", ""]
    if not probes:
        parts.append(f"Not run: {_reason(results, 'probes')}")
        return "\n".join(parts)

    rows = []
    for record in probes:
        rows.append(
            [
                _get(record, "probe", "-"),
                _num(_get(record, "fired")),
                _num(_get(record, "statistic")),
                _get(record, "n_qubits", "-"),
                _get(record, "detail", ""),
                _get(record, "caveat", "") or "-",
            ]
        )
    parts.append(
        _table(["probe", "fired", "statistic", "n_qubits", "detail", "caveat"], rows)
    )
    fired = [r for r in probes if _get(r, "fired")]
    parts.append("")
    if fired:
        parts.append(
            f"{len(fired)} of {len(probes)} probes fired `[measured]`. A firing probe is a statement "
            "about this circuit at this width and about nothing else; it is reported with its caveat "
            "column because a probe whose precondition does not hold at this width can fire for a "
            "reason that has nothing to do with algebraic structure."
        )
    else:
        parts.append(
            f"No probe fired, over {len(probes)} probes `[measured]`. That is a negative result at "
            "this width. It is only interpretable because the same suite is run against the positive "
            "control (`hidden_period`), whose structure is planted and therefore detectable: a suite "
            "that never fires on either is reporting on itself rather than on the oracle."
        )
    return "\n".join(parts)


def _scaling_section(results: Mapping[str, Any]) -> str:
    scaling = _get(results, "scaling", {}) or {}
    sweep = _records(_get(results, "sweep"))
    if not scaling and not sweep:
        return "## Scaling\n\nNot run: " + _reason(results, "scaling")

    parts = ["## Scaling, and where it stops being measurement", ""]
    if sweep:
        rows = []
        for record in sweep:
            status = _get(record, "status", "-")
            rows.append(
                [
                    _get(record, "n_search", "-"),
                    _get(record, "n_qubits_truth_table", "-"),
                    _get(record, "n_qubits_arithmetic", "-"),
                    _get(record, "gate_count", "-"),
                    _get(record, "ir_depth", "-"),
                    _get(record, "wall_seconds", "-"),
                    MEASURED if status == "measured" else REFUSED,
                    _get(record, "reason", "") if status != "measured" else "",
                ]
            )
        parts.append(
            _table(
                [
                    "n_search",
                    "width (truth table)",
                    "width (arithmetic)",
                    "gates",
                    "IR depth",
                    "wall seconds",
                    "provenance",
                    "reason",
                ],
                rows,
            )
        )
        parts.append("")
    if scaling:
        parts.append("### The fit")
        parts.append("")
        values = scaling if isinstance(scaling, Mapping) else {}
        describe = getattr(scaling, "describe", None)
        if not values and callable(describe):
            values = describe()
        parts.append(
            _table(
                ["fit parameter", "value"],
                [(k, _num(v, 6) if isinstance(v, (int, float)) else v) for k, v in values.items()],
            )
        )
        parts.append("")
        parts.append(
            "**Every value in this table is `[extrapolated]`.** It is a model fitted to the "
            "measured points above, and a gate count predicted from it at a width nobody simulated "
            "is a prediction, not a measurement. The fit is reported because the cost of the "
            "relation is the finding this project has that an `(M, N)` amplitude recursion does "
            "not, and the fit is the only form in which it extends past the simulated ceiling — "
            "which is exactly why its provenance has to travel with it."
        )
    return "\n".join(parts)


def _refusal_section(results: Mapping[str, Any]) -> str:
    sweep = _records(_get(results, "sweep"))
    refused = [r for r in sweep if _get(r, "status", "") != "measured"]
    not_run = _get(results, "not_run", {}) or {}
    if not refused and not not_run:
        return ""

    rows = []
    for record in refused:
        rows.append(
            [
                _get(record, "n_search", "-"),
                _get(record, "n_qubits_arithmetic", "-"),
                _get(record, "statevector_bytes_arithmetic", "-"),
                _get(record, "reason", "-"),
            ]
        )
    for section, reason in not_run.items():
        rows.append([section, "-", "-", reason])

    return "\n".join(
        [
            "## Points that were not run, and why",
            "",
            _table(["point", "width", "statevector bytes", "reason"], rows),
            "",
            "A point that could not be run is recorded as a refusal with its reason. It is "
            "deliberately not silently dropped: a sweep table with the unsimulable widths missing "
            "reads as a sweep that covered them.",
        ]
    )


def _validation_section(results: Mapping[str, Any]) -> str:
    validation = _records(_get(results, "validation"))
    parts = ["## The arithmetic lowering, validated classically", ""]
    if not validation:
        parts.append(f"Not run: {_reason(results, 'validation')}")
        return "\n".join(parts)

    parts.append(
        _table(
            ["check", "ok", "n_search", "states", "bytes", "detail"],
            [
                [
                    _get(r, "name", "-"),
                    _num(_get(r, "ok")),
                    _get(r, "n_search", "-"),
                    _get(r, "n_states", "-"),
                    _get(r, "memory_bytes", "-"),
                    _get(r, "detail", ""),
                ]
                for r in validation
            ],
        )
    )
    parts.append("")
    parts.append(
        "This is exact simulation with no tolerance anywhere: the IR is permutation-plus-diagonal, "
        "so a basis state's trajectory is a bit-string permutation and an integer phase exponent "
        "mod 8, and the check costs one machine word per basis state — linear in `2**n_search`, not "
        "the quadratic `2**n * 16` bytes of a complex statevector. It is therefore available at "
        "widths a statevector engine cannot reach, which is what lets the arithmetic lowering — the "
        "widest circuit this project builds — be checked at all."
    )
    return "\n".join(parts)


def _baseline_section(results: Mapping[str, Any]) -> str:
    baseline = _get(results, "classical_baseline", {}) or {}
    parts = ["## Classical baseline", ""]
    if not baseline:
        parts.append(f"Not computed: {_reason(results, 'classical_baseline')}")
        return "\n".join(parts)

    queries = baseline.get("queries")
    rows = [(k, _num(v, 6) if isinstance(v, (int, float)) else v) for k, v in baseline.items()]
    parts.append(_table(["quantity", "value"], rows))
    optimum = _get(results, "optimal_iterations")
    if queries and optimum:
        parts.append("")
        parts.append(
            f"Brute force needs `{queries}` queries `[measured by the classical evaluator]`; Grover "
            f"needs about `{optimum}` iterations. The ratio is the quadratic speedup, and it is a "
            "statement about this instance only: it says nothing about whether the relation has "
            "structure a better algorithm could use, which is what the probes are for."
        )
    return "\n".join(parts)


def _figure_section(run_dir: Path, figures: Mapping[str, Path] | None) -> str:
    if not figures:
        return ""
    rows = []
    blocks = []
    for name, path in figures.items():
        try:
            relative = path.relative_to(run_dir)
        except ValueError:
            relative = path
        rows.append([name, str(relative)])
        blocks.append(f"![{name}]({relative})")
    return "\n".join(
        [
            "## Figures",
            "",
            _table(["figure", "path"], rows),
            "",
            "\n\n".join(blocks),
            "",
            "Figures are static and deterministic: the same results produce byte-identical files.",
        ]
    )


def _notes_section(results: Mapping[str, Any]) -> str:
    notes = _get(results, "notes", []) or []
    if not notes:
        return ""
    return "\n".join(["## Notes on this run", "", _bullets(str(n) for n in notes)])


def _reproduction_section(config: Mapping[str, Any], results: Mapping[str, Any]) -> str:
    import yaml

    # default_flow_style=None keeps leaf lists (a qubit range, a format list) on one line while
    # still laying the sections out as a block: the echo is meant to be read, not parsed.
    echo = yaml.safe_dump(config, sort_keys=True, default_flow_style=None).strip()
    config_path = _get(results, "config_path", "config/default_experiment.yaml")
    run_dir = _get(results, "run_id", "{run_id}")
    return "\n".join(
        [
            "## Configuration, and how to reproduce this",
            "",
            f"Loaded from `{config_path}`. The echo below is what the run actually validated, not "
            "the file on disk, so a configuration edited after the fact cannot make this report "
            "describe a run that never happened.",
            "",
            "```yaml",
            echo,
            "```",
            "",
            "```sh",
            f".venv/bin/python scripts/run_experiment.py --config {config_path}",
            f".venv/bin/python scripts/sweep_scaling.py --config {config_path}",
            f".venv/bin/python -m grover_emulator.cli report --run-dir results/{run_dir}",
            "```",
            "",
            "A run is reproduced from its configuration and its seed: the seed is in the run "
            "identity table, the instance's parameters are in the instance table, and the measured "
            "marked set is derived from them rather than stored.",
        ]
    )


def _reason(results: Mapping[str, Any], section: str) -> str:
    not_run = _get(results, "not_run", {}) or {}
    return str(
        not_run.get(
            section,
            "this run did not produce this section; see the notes, or the run log for where it "
            "stopped",
        )
    )


# -----------------------------------------------------------------------------------------------
# rendering and writing
# -----------------------------------------------------------------------------------------------


def _figure_map(run_dir: Path, figures: Any) -> dict[str, Path]:
    """Resolve the figures argument to an ordered ``{caption: path}`` map of files that exist."""
    if figures is None:
        directory = run_dir / "figures"
        if not directory.is_dir():
            return {}
        return {p.stem.replace("_", " "): p for p in sorted(directory.glob("*.png"))}
    mapping: dict[str, Path] = {}
    if isinstance(figures, Mapping):
        items = figures.items()
    else:
        items = ((Path(p).stem.replace("_", " "), p) for p in figures)
    for name, path in items:
        path = Path(path)
        if path.exists():
            mapping[str(name)] = path
    return mapping


def render_report(config: Any, results: Mapping[str, Any], figures: Any = None, *, run_dir: Path | str = ".") -> str:
    """The report as text.

    Kept separate from :func:`generate_report` so the report can be printed, tested, or diffed
    without touching the filesystem — and so the verbatim-preamble property can be asserted on the
    text that is actually written.
    """
    run_dir = Path(run_dir)
    results = dict(results or {})
    config_map = _as_mapping(config)
    if config_map:
        results.setdefault("config", config_map)

    run_id = _get(results, "run_id", "unnamed-run")
    kind = _get(results, "kind", "experiment")
    figure_map = _figure_map(run_dir, figures)

    sections = [
        f"# Report: {run_id} ({kind})",
        _preamble(),
        _identity_section(config_map, results),
        _marked_set_section(results),
        _circuit_section(results),
        _curve_section(results),
        _probe_section(results),
        _scaling_section(results),
        _refusal_section(results),
        _validation_section(results),
        _baseline_section(results),
        _notes_section(results),
        _figure_section(run_dir, figure_map),
        _reproduction_section(config_map, results),
    ]
    text = "\n".join(part.strip("\n") + "\n" for part in sections if part and part.strip())
    return text


def generate_report(
    run_dir: Path | str,
    config: Any,
    results: Mapping[str, Any],
    figures: Any = None,
    *,
    filename: str = "report.md",
) -> Path:
    """Write ``report.md`` into ``run_dir`` and return its path.

    Args:
        run_dir: the results directory. Created if it does not exist, so that writing a report is
            never the step that fails for a reason unrelated to the report.
        config: the validated configuration, its mapping form, or a path to the YAML.
        results: the results mapping — the same JSON a run writes to ``metrics.json``.
        figures: figure paths, as a sequence or a ``{caption: path}`` mapping. ``None`` means "the
            figures in ``run_dir/figures``", which is what makes regeneration from a results
            directory work as a plain call.
        filename: the report's filename.

    Returns:
        The path written.

    The preamble is emitted on every path through this function. There is deliberately no argument
    that suppresses it: a report without the boundary is a report that is not in the results
    directory, and a caller wanting a document without it is asking for a different document.
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    text = render_report(config, results, figures=figures, run_dir=run_dir)
    path = run_dir / filename
    path.write_text(text, encoding="utf-8")
    return path


def load_results(run_dir: Path | str, filename: str = "metrics.json") -> dict:
    """Read a stored results mapping back, for regenerating a report without re-running."""
    path = Path(run_dir) / filename
    return json.loads(path.read_text(encoding="utf-8"))


def generate_report_from_run_dir(
    run_dir: Path | str, *, figures: Any = None, filename: str = "report.md"
) -> Path:
    """Regenerate ``report.md`` from a finished results directory.

    This is the whole reason the report is rendered from a stored mapping: a report is a view of
    results, not a side effect of computing them, and a view must be re-renderable when its
    formatting changes without the run being repeated.
    """
    run_dir = Path(run_dir)
    results = load_results(run_dir)
    config: Any = results.get("config")
    if not config:
        config_path = results.get("config_path")
        if config_path:
            config = config_path
    return generate_report(run_dir, config, results, figures=figures, filename=filename)
