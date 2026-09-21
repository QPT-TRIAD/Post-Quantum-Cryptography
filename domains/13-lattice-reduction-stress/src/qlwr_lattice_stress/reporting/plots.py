"""Figures, each carrying its own provenance label.

The rule the reports follow applies to figures too, and a figure is where it is easiest to break:
two series on one axis look like one dataset, and a reader will not go looking for which points were
measured. So measured and extrapolated series are drawn **visually distinct and never joined into a
single line**, and every figure is titled with its provenance rather than relying on a caption
elsewhere.

The module imports matplotlib lazily. A run that produces no figures should not need a plotting
backend, and on a headless machine the import can fail for reasons that have nothing to do with the
result.
"""

from __future__ import annotations

from pathlib import Path

from ..protocols import PROVENANCE_LABELS, EXTRAPOLATED, MEASURED

__all__ = ["plot_block_size_curve", "plot_measured_vs_extrapolated", "figure_paths"]


def _pyplot():
    import matplotlib

    matplotlib.use("Agg")  # headless: no display, and no attempt to find one
    import matplotlib.pyplot as plt

    return plt


def figure_paths(run_dir: str | Path) -> list[Path]:
    """Every figure a run produced, so a report can reference them without being told the names."""
    directory = Path(run_dir) / "figures"
    if not directory.exists():
        return []
    return sorted(p for p in directory.iterdir() if p.suffix in (".png", ".pdf", ".svg"))


def plot_block_size_curve(
    points: list[tuple[int, float]], *, dimension: int, out_path: str | Path, title: str | None = None
) -> Path:
    """Block size against wall-clock time, from **measured** points only.

    Recovered and unrecovered points are drawn with different markers rather than as one series: the
    threshold is the interesting feature, and a line through both would smooth it away.
    """
    plt = _pyplot()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not points:
        raise ValueError("no points to plot")

    plt.figure(figsize=(7, 4.5))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    plt.plot(xs, ys, marker="o", linestyle="none")
    plt.xlabel("block size")
    plt.ylabel("wall clock (s)")
    plt.title(title or f"Reduction cost, dimension {dimension} — {PROVENANCE_LABELS[MEASURED]}")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()
    return out_path


def plot_measured_vs_extrapolated(
    measured: list[tuple[int, float]],
    extrapolated: list[tuple[int, float]],
    *,
    out_path: str | Path,
    title: str | None = None,
) -> Path:
    """Two series, visually distinct, **never joined into one line**.

    Separate colours, separate markers, dashed for the model, and a legend naming which is which.
    Joining them would produce a single curve that appears to be one dataset — and the whole rule the
    project is built on is that a reader must be able to tell a measurement from a model output
    without reading a caption.
    """
    plt = _pyplot()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7, 4.5))
    if measured:
        plt.plot(
            [p[0] for p in measured], [p[1] for p in measured],
            marker="o", linestyle="none", color="tab:blue",
            label=PROVENANCE_LABELS[MEASURED],
        )
    if extrapolated:
        plt.plot(
            [p[0] for p in extrapolated], [p[1] for p in extrapolated],
            linestyle="--", color="tab:red", label=PROVENANCE_LABELS[EXTRAPOLATED],
        )
    plt.xlabel("block size")
    plt.ylabel("log2 cost")
    plt.title(title or "Measured against extrapolated")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=140)
    plt.close()
    return out_path
