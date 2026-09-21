"""The report's figures, drawn from a stored results mapping and nothing else.

Three rules shape everything here.

**A figure is drawn from the same mapping the report is rendered from.** :func:`plot_all` takes the
results mapping — the JSON of ``metrics.json`` — and never a live object. That is what makes a
figure regenerable from a finished results directory, and it is why the plotting code has no
knowledge of how a run was executed.

**Provenance is drawn, not just written.** A point that was measured and a curve that came out of a
fit are distinguished on the canvas: measured points are markers with a solid line, a fitted region
is dashed and carries the word ``extrapolated`` next to it. A reader who looks at the picture and
not at the table must still be unable to mistake a prediction for a measurement. A point that was
refused is drawn as a refusal, with its reason in the axis note — it is never simply absent, because
a chart with the unsimulable widths missing reads as a chart that covered them.

**The figures are deterministic.** The same results produce byte-identical files, asserted by test.
That means no timestamps and no version stamps in the PNG metadata, a fixed figure size and dpi, and
no ordering that depends on a dict iteration the caller happened to build in a particular order.

What no figure here does is present the success curve as evidence for the curve. The measured curve
and the closed form are drawn together because their agreement is a check on the harness, and the
figure says so in its note: the closed form is the analytic result, the circuit's own contribution is
the certification of ``M`` and the gate counts, which are in other figures.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib

matplotlib.use("Agg", force=True)  # no display is ever required to produce a report figure

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator, StrMethodFormatter  # noqa: E402

__all__ = [
    "SURFACE",
    "INK",
    "INK_SECONDARY",
    "MUTED",
    "GRID",
    "AXIS",
    "SERIES",
    "CRITICAL",
    "WARNING",
    "plot_success_curve",
    "plot_gate_scaling",
    "plot_statevector_cost",
    "plot_probe_summary",
    "plot_all",
]

# -----------------------------------------------------------------------------------------------
# the chart surface: one light palette, painted explicitly
# -----------------------------------------------------------------------------------------------
# A PNG cannot follow a viewer's theme, so the choice is made here rather than left to a default:
# a light chart surface, ink from the same scale, and a categorical order that is assigned in
# sequence and never cycled. The first three slots are the ones a chart may use for series that are
# compared pairwise; nothing in this report has more than three.

SURFACE = "#fcfcfb"
"""The chart surface. Painted, not inherited, so a figure is the same file everywhere."""

INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

SERIES: tuple[str, ...] = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")
"""Categorical slots, in fixed order. Series keep their slot for the whole report."""

MEASURED_COLOR = SERIES[0]
"""The one colour every measured quantity is drawn in, across every figure."""

CLOSED_FORM_COLOR = SERIES[1]
ARITHMETIC_COLOR = SERIES[1]
"""The arithmetic lowering keeps slot 2 in the cost figures, and the closed form keeps it in the
curve figure. They never appear on the same axes, so the reuse carries no ambiguity."""

CRITICAL = "#d03b3b"
WARNING = "#fab219"
"""Status colours, reserved for state — a refusal, a budget line — and never for identity. Both
always ship with a label, so the meaning never rests on the colour alone."""

_FIGSIZE = (9.0, 5.0)
"""One figure size for the whole report, so a page of figures reads as one document."""

_DPI = 160


def _style_axes(ax: plt.Axes) -> plt.Axes:
    """Hairline chrome, muted ticks, a solid one-shade-off grid. No dashes anywhere in the chrome."""
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=9, width=0.8)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(INK_SECONDARY)
    ax.grid(True, axis="y", color=GRID, linewidth=0.6, linestyle="-")
    ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    return ax


def _figure(height: float | None = None) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(_FIGSIZE[0], height or _FIGSIZE[1]), dpi=_DPI)
    fig.patch.set_facecolor(SURFACE)
    _style_axes(ax)
    return fig, ax


def _note(fig: plt.Figure, text: str, *, y: float = 0.012) -> None:
    """A provenance note under the axes, in muted ink. Every figure carries one."""
    fig.text(0.055, y, text, ha="left", va="bottom", fontsize=7.5, color=MUTED, wrap=True)


def _title(ax: plt.Axes, title: str, subtitle: str = "") -> None:
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=26 if subtitle else 10)
    if subtitle:
        ax.text(
            0.0,
            1.02,
            subtitle,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9,
            color=INK_SECONDARY,
        )


def _save(fig: plt.Figure, path: Path) -> Path:
    """Write a figure with no metadata, so two saves of the same figure are byte-identical."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path,
        facecolor=SURFACE,
        metadata={"Software": None, "CreationDate": None, "Artist": None},
    )
    plt.close(fig)
    return path


def _wrap(text: Any, *, width: int, lines: int) -> str:
    """Free text folded to a bounded block, so a long sentence cannot run off the panel.

    A figure is not a table: the report prints a probe's detail in full, and this is the same
    sentence in the space a panel has for it. Folding it here rather than leaving it to the renderer
    keeps the layout deterministic — byte-identical figures need the same text in the same place —
    and keeps a text wider than the axes from defeating the layout pass, which is how the tail of a
    sentence ends up outside the picture where nobody reads it.
    """
    import textwrap

    body = " ".join(str(text).split())
    if not body:
        return ""
    folded = textwrap.wrap(body, width=width) or [""]
    if len(folded) > lines:
        folded = folded[:lines]
        folded[-1] = folded[-1].rstrip(".,;:") + " ..."
    return "\n".join(folded)


def _bytes_formatter(value: float, _position: int) -> str:
    """Byte counts on a log axis, in units a reader can hold in their head."""
    if value <= 0:
        return "0"
    for limit, unit in ((1e18, "EB"), (1e15, "PB"), (1e12, "TB"), (1e9, "GB"), (1e6, "MB"), (1e3, "kB")):
        if value >= limit:
            scaled = value / limit
            return f"{scaled:.0f} {unit}" if scaled >= 10 or scaled == int(scaled) else f"{scaled:.1f} {unit}"
    return f"{value:.0f} B"


def _get(mapping: Mapping[str, Any] | None, key: str, default: Any = None) -> Any:
    if not mapping:
        return default
    value = mapping.get(key, default)
    return default if value is None else value


def _records(value: Any) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    return [dict(row) for row in value]


def _numbers(records: Iterable[Mapping[str, Any]], *keys: str) -> list[tuple[float, ...]]:
    """The rows that have every one of ``keys``, as floats, skipping anything that is not a number."""
    out: list[tuple[float, ...]] = []
    for record in records:
        values: list[float] = []
        for key in keys:
            value = record.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                values = []
                break
            values.append(float(value))
        if values:
            out.append(tuple(values))
    return out


# -----------------------------------------------------------------------------------------------
# figures
# -----------------------------------------------------------------------------------------------


def plot_success_curve(results: Mapping[str, Any], path: Path) -> Path | None:
    """``p_success`` against iteration: what the circuit did, beside what the closed form says.

    The two curves are drawn together and the note beneath them says what their agreement is worth.
    The peak of the measured curve and the optimum the range was derived from are both labelled,
    because the point of the figure is that the window contains a peak and the reader can see it
    turn over.
    """
    curve = _records(_get(results, "curve"))
    measured = _numbers(curve, "iteration", "empirical_p_success")
    theory = _numbers(curve, "iteration", "theoretical_p_success")
    if not measured and not theory:
        return None

    fig, ax = _figure()
    _title(
        ax,
        "Success probability against Grover iteration",
        "measured by executing the circuit, against the analytic curve it should follow",
    )
    ax.set_xlabel("iterations k", fontsize=10, color=INK_SECONDARY)
    ax.set_ylabel("p(success)", fontsize=10, color=INK_SECONDARY)
    ax.set_ylim(-0.02, 1.02)

    handles: list[Line2D] = []
    if theory:
        xs = [row[0] for row in theory]
        ys = [row[1] for row in theory]
        ax.plot(xs, ys, color=CLOSED_FORM_COLOR, linewidth=2.0, zorder=3)
        handles.append(
            Line2D([], [], color=CLOSED_FORM_COLOR, linewidth=2.0, label="closed form  sin^2((2k+1)theta)")
        )
    if measured:
        xs = [row[0] for row in measured]
        ys = [row[1] for row in measured]
        ax.plot(
            xs,
            ys,
            color=MEASURED_COLOR,
            linewidth=2.0,
            marker="o",
            markersize=4.5,
            markerfacecolor=MEASURED_COLOR,
            markeredgecolor=SURFACE,
            markeredgewidth=1.0,
            zorder=4,
        )
        handles.insert(
            0,
            Line2D(
                [], [], color=MEASURED_COLOR, linewidth=2.0, marker="o", markersize=6,
                markerfacecolor=MEASURED_COLOR, markeredgecolor=SURFACE, label="measured (statevector)",
            ),
        )
        peak_k, peak_p = max(measured, key=lambda row: row[1])
        # Left of the peak and above the rising limb: the window always ends two iterations past
        # the optimum, so the space above the approach to the peak is the empty one.
        ax.annotate(
            f"measured peak  k={peak_k:.0f},  p={peak_p:.3f}",
            xy=(peak_k, peak_p),
            xytext=(-8, 6),
            textcoords="offset points",
            ha="right",
            va="bottom",
            fontsize=9,
            color=INK,
            arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8},
        )
        # Headroom for that label. The curve reaches 1.0 at the right-hand end of its window, so
        # without a band above it the label lands on the subtitle and both become unreadable.
        ax.set_ylim(-0.02, 1.12)

    # Pinned after the data is on the axes: setting a bound before anything is plotted pins the
    # other bound to the default, which silently crops the whole window.
    ax.set_xlim(left=0.0)

    optimum = _get(results, "optimal_iterations")
    if isinstance(optimum, (int, float)) and not isinstance(optimum, bool):
        ax.axvline(float(optimum), color=AXIS, linewidth=0.8, zorder=1)
        ax.annotate(
            f"k_opt = {int(optimum)}\n(derived from M, N)",
            xy=(float(optimum), 0.06),
            xytext=(6, 0),
            textcoords="offset points",
            ha="left",
            va="bottom",
            fontsize=8.5,
            color=MUTED,
        )

    if handles:
        # Upper left: the curve starts near zero and peaks at the right-hand end of the window it
        # was derived over, so this is the one region of the plot the data does not reach.
        ax.legend(
            handles=handles,
            loc="upper left",
            frameon=False,
            fontsize=9,
            labelcolor=INK_SECONDARY,
        )

    _note(
        fig,
        "Agreement between the two curves checks the harness, not the physics: a diagonal phase\n"
        "oracle leaves the curve a function of (M, N) alone. The closed form is the reference here,\n"
        "not the finding — what the circuit adds is that it certifies M, and that it costs gates.",
    )
    fig.tight_layout(rect=(0.0, 0.13, 1.0, 1.0))
    return _save(fig, path)


def plot_gate_scaling(results: Mapping[str, Any], path: Path) -> Path | None:
    """Circuit cost against width, from the gate-list IR, with any fitted region marked.

    Small multiples rather than two y-scales: gate count and depth are different quantities, and a
    second axis would invent a relationship between them by choosing where the two scales line up.

    The y-values are counts of the circuit *as written in the IR*. They are not simulation results
    and the subtitle says so, because the arithmetic lowering is not simulable at any of these
    widths and a reader could otherwise take the curve for one.
    """
    sweep = _records(_get(results, "sweep"))
    points = [row for row in sweep if _get(row, "n_search") is not None]
    if not points:
        return None

    fit = _get(results, "scaling", {}) or {}

    def series(key: str) -> list[tuple[float, float]]:
        return _numbers(points, "n_search", key)

    panels = [
        ("gate_count", "gates (arithmetic lowering)", "gate count"),
        ("ir_depth", "IR depth (arithmetic lowering)", "depth"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6), dpi=_DPI)
    fig.patch.set_facecolor(SURFACE)
    fitted = bool(_records(fit.get("curve")))

    for ax, (key, ylabel, short) in zip(axes, panels):
        _style_axes(ax)
        ax.set_xlabel("search-register width n_search", fontsize=10, color=INK_SECONDARY)
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        data = series(key)
        if not data:
            ax.text(
                0.5, 0.5, "not measured", transform=ax.transAxes, ha="center", va="center",
                fontsize=10, color=MUTED,
            )
            continue
        xs = [row[0] for row in data]
        ys = [row[1] for row in data]
        # A linear axis on purpose: across the sweep's widths a count spans less than a decade, and
        # a log axis over a narrow range is harder to read than the numbers themselves.
        ax.plot(
            xs, ys, color=ARITHMETIC_COLOR, linewidth=2.0, marker="o", markersize=5.5,
            markerfacecolor=ARITHMETIC_COLOR, markeredgecolor=SURFACE, markeredgewidth=1.0, zorder=3,
        )
        ax.set_ylabel(ylabel, fontsize=10, color=INK_SECONDARY)
        ax.set_title(short, loc="left", fontsize=10, color=INK_SECONDARY, pad=8)
        # Label the extreme selectively, rather than every point.
        top = max(range(len(ys)), key=lambda i: ys[i])
        ax.annotate(
            f"{ys[top]:,.0f}",
            xy=(xs[top], ys[top]),
            xytext=(-6, 8),
            textcoords="offset points",
            ha="right",
            fontsize=9,
            color=INK,
        )
        predicted = _numbers(_records(fit.get("curve")), "n_search", key)
        beyond = [row for row in predicted if row[0] > max(xs)]
        if beyond:
            # Drawn only where the fit leaves the measured range, so the dashed segment means
            # "prediction" rather than "a differently styled measurement".
            anchor_x = max(xs)
            anchor_y = ys[xs.index(anchor_x)]
            px = [anchor_x, *[row[0] for row in beyond]]
            py = [anchor_y, *[row[1] for row in beyond]]
            ax.plot(px, py, color=MUTED, linewidth=1.6, linestyle=(0, (5, 3)), zorder=2)
            ax.annotate(
                "extrapolated\n(fitted model)",
                xy=(px[-1], py[-1]),
                xytext=(-6, 6),
                textcoords="offset points",
                ha="right",
                va="bottom",
                fontsize=8.5,
                color=MUTED,
            )

    handles = [
        Line2D(
            [], [], color=ARITHMETIC_COLOR, linewidth=2.0, marker="o", markersize=6,
            markerfacecolor=ARITHMETIC_COLOR, markeredgecolor=SURFACE, label="measured from the IR",
        )
    ]
    if fitted:
        handles.append(Line2D([], [], color=MUTED, linewidth=1.6, linestyle=(0, (5, 3)), label="extrapolated (fit)"))
    axes[0].legend(handles=handles, loc="upper left", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)

    fig.suptitle(
        "What the relation costs, counted from the gate-list IR",
        x=0.02, y=0.985, ha="left", fontsize=12, color=INK,
    )
    _note(
        fig,
        "Counts are of the gate list that was built, never of a framework circuit object. These are\n"
        "circuit sizes, not simulation results: the arithmetic lowering is far too wide to simulate\n"
        "exactly at any width shown, which is the finding rather than an omission.",
        y=0.02,
    )
    fig.tight_layout(rect=(0.0, 0.17, 1.0, 0.93))
    return _save(fig, path)


def plot_statevector_cost(
    results: Mapping[str, Any], path: Path, *, budget_gb: float
) -> Path | None:
    """Where exact statevector simulation stops, against the memory budget of the run.

    The two lowerings are drawn as separate series because they are two different circuits over the
    same problem, and the difference between them is the point: the truth-table oracle is the one
    that can be simulated, and the arithmetic one — the circuit whose cost the report is about —
    cannot be, at any width. Refused points are drawn, not dropped.
    """
    sweep = _records(_get(results, "sweep"))
    if not sweep:
        return None

    fig, ax = _figure()
    _title(
        ax,
        "Exact statevector cost, against the run's memory budget",
        "complex128 amplitudes: 16 * 2**(width) bytes for one statevector",
    )
    ax.set_yscale("log")
    ax.set_xlabel("total circuit width (qubits)", fontsize=10, color=INK_SECONDARY)
    ax.set_ylabel("statevector bytes", fontsize=10, color=INK_SECONDARY)
    ax.yaxis.set_major_formatter(FuncFormatter(_bytes_formatter))

    budget_bytes = float(budget_gb) * 1024.0**3

    def points(field: str, width_field: str) -> list[tuple[float, float]]:
        return _numbers(sweep, width_field, field)

    truth = points("statevector_bytes_truth_table", "n_qubits_truth_table")
    arith = points("statevector_bytes_arithmetic", "n_qubits_arithmetic")
    if not truth and not arith:
        return None

    handles: list[Line2D] = []
    if truth:
        xs = [row[0] for row in truth]
        ys = [row[1] for row in truth]
        ax.plot(
            xs, ys, color=MEASURED_COLOR, linewidth=2.0, marker="o", markersize=6,
            markerfacecolor=MEASURED_COLOR, markeredgecolor=SURFACE, markeredgewidth=1.0, zorder=4,
        )
        handles.append(
            Line2D([], [], color=MEASURED_COLOR, linewidth=2.0, marker="o", markersize=6,
                   markerfacecolor=MEASURED_COLOR, markeredgecolor=SURFACE,
                   label="truth-table lowering (simulable)")
        )
    if arith:
        xs = [row[0] for row in arith]
        ys = [row[1] for row in arith]
        ax.plot(
            xs, ys, color=ARITHMETIC_COLOR, linewidth=2.0, marker="D", markersize=5.5,
            markerfacecolor=ARITHMETIC_COLOR, markeredgecolor=SURFACE, markeredgewidth=1.0, zorder=4,
        )
        handles.append(
            Line2D([], [], color=ARITHMETIC_COLOR, linewidth=2.0, marker="D", markersize=5.5,
                   markerfacecolor=ARITHMETIC_COLOR, markeredgecolor=SURFACE,
                   label="arithmetic lowering (refused)")
        )
        for x, y in arith:
            ax.annotate(
                "refused",
                xy=(x, y),
                xytext=(-6, 8),
                textcoords="offset points",
                ha="right",
                fontsize=8,
                color=CRITICAL,
            )

    ax.axhline(budget_bytes, color=WARNING, linewidth=1.6, zorder=3)
    ax.annotate(
        f"run budget  {budget_gb:g} GB",
        xy=(ax.get_xlim()[1], budget_bytes),
        xytext=(-4, 6),
        textcoords="offset points",
        ha="right",
        va="bottom",
        fontsize=9,
        color=INK,
    )

    if handles:
        ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)

    _note(
        fig,
        "A point above the budget is refused before anything is allocated, and is listed with its\n"
        "reason in the report's refusal table. The arithmetic lowering's minimum width is 50 qubits\n"
        "at the smallest structurally faithful instance: that is a measured limitation, not a bug.",
    )
    fig.tight_layout(rect=(0.0, 0.13, 1.0, 1.0))
    return _save(fig, path)


def plot_probe_summary(results: Mapping[str, Any], path: Path) -> Path | None:
    """Which structural probes fired, at which width — a state, not a magnitude.

    Drawn as one row per probe with the firing ones marked, because the number of probes is small
    and the question a reader has is "did anything fire", not "how much".
    """
    probes = _records(_get(results, "probes"))
    if not probes:
        return None

    labels = [str(_get(row, "probe", "-")) for row in probes]
    fired = [bool(_get(row, "fired", False)) for row in probes]

    details = [
        _wrap(_get(row, "detail", "") or _get(row, "caveat", ""), width=88, lines=3) for row in probes
    ]
    fig, ax = _figure(height=max(2.9, 0.42 * len(labels) + 0.62 * max(len(d.split("\n")) for d in details)))
    _title(ax, "Structural probes", "a probe that never fires is indistinguishable from a broken one")
    positions = list(range(len(labels)))
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=9, color=INK_SECONDARY)
    ax.set_ylim(len(labels) - 0.5, -0.5)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.grid(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(False)
    for position, is_fired, detail in zip(positions, fired, details):
        color = CRITICAL if is_fired else MEASURED_COLOR
        outcome = "fired" if is_fired else "did not fire"
        ax.plot(
            [0.06], [position], marker="o", markersize=9, color=color,
            markeredgecolor=SURFACE, markeredgewidth=1.5,
        )
        # The word travels with the colour: a firing probe is never signalled by colour alone.
        ax.text(0.12, position, outcome, va="center", fontsize=9.5, color=INK)
        if detail and detail != "-":
            ax.text(
                0.34, position, detail, va="center", fontsize=8, color=INK_SECONDARY,
                linespacing=1.4,
            )

    _note(
        fig,
        "A firing probe is a statement about this circuit at this width and nothing else: the\n"
        "controls (a planted period, and a uniformly random marked set) are what make silence mean\n"
        "something. Neither result is a statement about any production parameter set.",
        y=0.02,
    )
    fig.tight_layout(rect=(0.0, 0.17, 1.0, 1.0))
    return _save(fig, path)


# -----------------------------------------------------------------------------------------------
# entry point
# -----------------------------------------------------------------------------------------------


def plot_all(
    results: Mapping[str, Any],
    figures_dir: Path | str,
    *,
    budget_gb: float = 6.0,
) -> dict[str, Path]:
    """Draw every figure this run's results support, and return ``{caption: path}``.

    A figure whose data is absent is skipped rather than drawn empty: an empty axes in a report
    reads as a measurement of zero, which is a different claim from "this was not run". The skipped
    sections are named in the report's own "not run" table, where their reason is written out.

    Args:
        results: the results mapping — the same object the report is rendered from.
        figures_dir: where to write. Created if it does not exist.
        budget_gb: the run's memory budget, for the cost figure's threshold line.

    Returns:
        Captions mapped to paths, in the order the figures should appear in the report.
    """
    directory = Path(figures_dir)
    out: dict[str, Path] = {}
    plan: list[tuple[str, str, Any]] = [
        ("success_curve.png", "success probability against iteration", lambda p: plot_success_curve(results, p)),
        ("gate_scaling.png", "circuit cost against width", lambda p: plot_gate_scaling(results, p)),
        (
            "statevector_cost.png",
            "statevector cost against the memory budget",
            lambda p: plot_statevector_cost(results, p, budget_gb=budget_gb),
        ),
        ("probe_summary.png", "structural probes", lambda p: plot_probe_summary(results, p)),
    ]
    for filename, caption, draw in plan:
        path = draw(directory / filename)
        if path is not None and path.exists():
            out[caption] = path
    return out


def figure_table(results: Mapping[str, Any], figures: Mapping[str, Path]) -> list[dict[str, str]]:
    """The figures as records, for the results mapping's ``figures`` field."""
    return [{"caption": caption, "path": str(path.name)} for caption, path in figures.items()]


def describe_scale(n_qubits: int) -> str:
    """A width and its statevector size, for a caption or a note."""
    bytes_needed = 16 * (1 << n_qubits)
    return f"{n_qubits} qubits = {bytes_needed} bytes ({math.log2(bytes_needed):.0f} bits of address space)"
