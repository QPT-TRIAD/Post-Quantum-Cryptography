"""Where the cost curve is measured, and where it stops being measured.

A statevector simulation ceiling is a fact about this machine's memory, not about the circuit. The
gate count of an instance at ``n_search = 12`` is measured; the gate count at ``n_search = 128``
cannot be, and the only honest way to put a number on it is to fit the measured ones and say so on
the same line as the number. That is the entire discipline of this module:

* A measured point and an extrapolated point are different types. They are not merged into one list
  of tuples, one column of a table, or one line of a chart. :class:`MeasuredPoint` refuses to be
  constructed from a record whose status is not ``"measured"``, so a refused sweep point cannot
  quietly become an input to a fit — the failure mode where a fit is drawn through a point that was
  never run and the resulting exponent looks *better* for it.
* Every record carries ``provenance``, and the two values are the report's own constants rather
  than strings retyped here. A report that renames them would otherwise leave this module emitting a
  label nothing renders.
* :meth:`ScalingFit.describe` labels each key with its own provenance, so a reader of the rendered
  table sees which numbers were built and which were modelled without having to read this docstring.

The fit is a power law, ``gates = a * n_search**b``, fitted by ordinary least squares on the
logarithms. Log-log because the quantity of interest in this project is the *exponent* — whether the
gate count grows with the search width the way the arithmetic construction says it should — and a
linear fit on the raw counts would answer a question about the intercept instead. ``np.linalg.lstsq``
rather than a closed form for the slope because the design matrix is built explicitly and handed to
the same routine whether there are three points or thirty, so the arithmetic cannot change shape with
the sample size.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from ..reporting.report_generator import EXTRAPOLATED, MEASURED, REFUSED
from .success_probability import AnalysisError

__all__ = [
    "ScalingError",
    "MeasuredPoint",
    "ExtrapolatedPoint",
    "ScalingFit",
    "fit_gate_scaling",
    "fit_depth_scaling",
    "predict_gate_count",
    "measured_points_from_sweep",
    "MIN_FIT_POINTS",
    "EXTRAPOLATION_CAVEAT_TEMPLATE",
]

MIN_FIT_POINTS = 3
"""Below this many measured points the module refuses to fit.

Not statistics — arithmetic. A power law has two free parameters, so two points determine it exactly
and leave no residual to inspect: a fit through two points is a statement that the data cannot
contradict, which is a different thing from a fit the data supports. Three points is the smallest
sample that can disagree with the model, and a disagreement that is visible is the only reason to
believe the agreement at widths nobody can check.
"""

EXTRAPOLATION_CAVEAT_TEMPLATE = (
    "This number is extrapolated from {n_points} measured point(s) over n_search = {lo}..{hi}. It "
    "was not simulated, and the model it comes from has only ever been checked inside that range: a "
    "power law fitted to three widths is an assumption about the fourth, and the assumption is "
    "cheapest exactly where it is least testable. The cost claim of this project is the *exponent* "
    "and the exponent is what the measured range supports; the absolute count at any width outside "
    "it is a projection, reported because a curve is more useful than a table and labelled because a "
    "projection is not a measurement."
)
"""Names the measured range, so an extrapolated number cannot be quoted without it."""


class ScalingError(AnalysisError):
    """The fit could not be made as asked — too few points, or a point that is not a measurement."""


# -----------------------------------------------------------------------------------------------
# the two kinds of point
# -----------------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MeasuredPoint:
    """One width, built and counted. Nothing here is inferred.

    Attributes:
        n_search: the search-register width.
        gate_count: gates in one Grover iteration, counted from the IR.
        ir_depth: depth of the same circuit, when it was counted.
        n_qubits: the circuit's full width, when it is known.
        wall_seconds: how long the build took, when it was timed. A property of this machine and
            never of the circuit, which is why it never enters the fit.
        lowering: which lowering produced the count.
        source: the record this was built from, kept for provenance.
    """

    n_search: int
    gate_count: int
    ir_depth: int | None = None
    n_qubits: int | None = None
    wall_seconds: float | None = None
    lowering: str = "arithmetic"
    source: Mapping[str, Any] = field(default_factory=dict)
    provenance: str = MEASURED

    def __post_init__(self) -> None:
        if self.gate_count <= 0:
            raise ScalingError(
                f"a gate count of {self.gate_count} at n_search={self.n_search} cannot be fitted on "
                "a log scale, and a count that is not positive is not a measurement"
            )
        if self.n_search < 1:
            raise ScalingError(f"n_search must be >= 1, got {self.n_search}")

    @classmethod
    def from_record(cls, record: Mapping[str, Any]) -> "MeasuredPoint":
        """Build from one ``sweep`` record, refusing anything that was not actually run.

        A sweep point is refused for a reason — a width whose statevector would not fit, a lowering
        the spec does not support — and such a point has a ``gate_count`` of ``0`` or none at all.
        Accepting it would place the fit's intercept wherever the zero landed. The refusal here is
        the boundary at which measured and modelled are kept apart, and it is enforced once, here,
        rather than trusted to every caller.
        """
        status = str(record.get("status", ""))
        n_search = record.get("n_search")
        if status != "measured":
            raise ScalingError(
                f"n_search={n_search} has status {status or '(missing)'!r}, not {MEASURED!r}: "
                f"{record.get('reason') or 'no reason was recorded'}. A point that was not run is "
                "not an input to a fit, and the fit is not weakened by leaving it out — it is made "
                "honest."
            )
        gate_count = record.get("gate_count")
        if not gate_count:
            raise ScalingError(
                f"n_search={n_search} is marked {MEASURED!r} but carries no gate_count; a measured "
                "point without its measurement is a claim, not a point"
            )
        return cls(
            n_search=int(n_search),
            gate_count=int(gate_count),
            ir_depth=record.get("ir_depth"),
            # The width is informational here and taken from whichever of the sweep's own spellings
            # is present; the fit itself runs on ``n_search`` alone.
            n_qubits=(
                record.get("n_qubits_concrete")
                or record.get("n_qubits")
                or record.get("n_qubits_truth_table")
                or record.get("n_qubits_arithmetic")
            ),
            wall_seconds=record.get("wall_seconds"),
            lowering=str(record.get("lowering", "arithmetic")),
            source=dict(record),
        )

    def to_dict(self) -> dict:
        record: dict[str, Any] = {
            "n_search": self.n_search,
            "gate_count": self.gate_count,
            "lowering": self.lowering,
            "provenance": self.provenance,
        }
        if self.ir_depth is not None:
            record["ir_depth"] = self.ir_depth
        if self.n_qubits is not None:
            record["n_qubits"] = self.n_qubits
        if self.wall_seconds is not None:
            record["wall_seconds"] = self.wall_seconds
            record["wall_seconds_provenance"] = "measured (this machine, this run)"
        return record


@dataclass(frozen=True, slots=True)
class ExtrapolatedPoint:
    """One width, predicted. It has no measurement behind it and says so in every rendering.

    Attributes:
        n_search: the width being predicted.
        gate_count: the fitted prediction.
        measured_range: ``(lo, hi)`` of the widths the fit was made from. Carried on the point rather
            than only on the fit, because a point travels further than the object that made it.
        inside_measured_range: whether this width is one the fit has evidence about. A prediction
            *inside* the fitted range is an interpolation and is checkable; one outside it is not,
            and the two are distinguished rather than both being called extrapolation.
    """

    n_search: int
    gate_count: float
    measured_range: tuple[int, int]
    n_measured_points: int
    basis: str = "power law fitted to measured gate counts (log-log least squares)"
    provenance: str = EXTRAPOLATED

    @property
    def inside_measured_range(self) -> bool:
        low, high = self.measured_range
        return low <= self.n_search <= high

    @property
    def caveat(self) -> str:
        low, high = self.measured_range
        return EXTRAPOLATION_CAVEAT_TEMPLATE.format(
            n_points=self.n_measured_points, lo=low, hi=high
        )

    def to_dict(self) -> dict:
        return {
            "n_search": self.n_search,
            "gate_count": self.gate_count,
            "provenance": self.provenance,
            "basis": self.basis,
            "measured_range": list(self.measured_range),
            "n_measured_points": self.n_measured_points,
            "inside_measured_range": self.inside_measured_range,
            "caveat": self.caveat,
        }


# -----------------------------------------------------------------------------------------------
# the fit
# -----------------------------------------------------------------------------------------------


def _log_log_least_squares(
    widths: Sequence[int], counts: Sequence[float], minimum: int
) -> tuple[float, float, np.ndarray]:
    """``(exponent, scale, residuals)`` for ``counts = scale * widths**exponent``.

    The design matrix is ``[1, log(width)]`` and the response is ``log(count)``, so the fitted
    intercept is ``log(scale)``. ``lstsq`` is used rather than the two-point closed form so the same
    code path handles 3 points and 30; it is a deterministic routine, and with the same inputs it
    returns the same bits on every run, which is what makes a report reproducible.
    """
    if len(widths) < minimum:
        raise ScalingError(
            f"a power law fitted to {len(widths)} point(s) has no residual to inspect and cannot be "
            f"contradicted by its own data; at least {minimum} measured points are required, and this "
            "refusal is the point rather than an inconvenience"
        )
    if len(set(widths)) != len(widths):
        raise ScalingError(
            f"the measured widths repeat ({sorted(widths)}); two measurements at one width are not "
            "two points on a curve"
        )
    x = np.log(np.asarray(widths, dtype=float))
    y = np.log(np.asarray(counts, dtype=float))
    design = np.column_stack([np.ones_like(x), x])
    solution, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    residuals = y - design @ solution
    return float(solution[1]), float(math.exp(solution[0])), residuals


@dataclass(frozen=True)
class ScalingFit:
    """A power law, the measured points it was fitted to, and the predictions made from it.

    The three are separate attributes and stay separate in every rendering. There is no iteration
    that yields both kinds of point, because code that walks a mixed list is code that will
    eventually average it.
    """

    points: tuple[MeasuredPoint, ...]
    exponent: float
    scale: float
    residuals: tuple[float, ...]
    target_widths: tuple[int, ...] = ()
    predictions: tuple[ExtrapolatedPoint, ...] = ()
    form: str = "gate_count = scale * n_search ** exponent"
    fit_method: str = "ordinary least squares on log(gate_count) against log(n_search)"

    # -- what the measured points support, on their own -----------------------------------------

    @property
    def measured_range(self) -> tuple[int, int]:
        widths = [p.n_search for p in self.points]
        return min(widths), max(widths)

    @property
    def n_points(self) -> int:
        return len(self.points)

    @property
    def rms_residual_log2(self) -> float:
        """RMS of the fit's residuals, in log2 of the gate count.

        A residual of ``0.1`` means the model is off by about 7% at that width — so this number says
        how much trust the extrapolation deserves *inside* the range, which is the only place the
        trust was ever checked.
        """
        return float(np.sqrt(np.mean(np.square(self.residuals))) / math.log(2.0))

    @property
    def max_residual_log2(self) -> float:
        return float(np.max(np.abs(self.residuals)) / math.log(2.0))

    @property
    def r_squared(self) -> float:
        y = np.log(np.asarray([p.gate_count for p in self.points], dtype=float))
        total = float(np.sum(np.square(y - y.mean())))
        if total == 0.0:
            return 1.0
        return 1.0 - float(np.sum(np.square(self.residuals))) / total

    @property
    def doubling_width_exponent(self) -> float:
        """What the exponent means in the currency a reader can picture.

        Ignoring the additive term, doubling the search width multiplies the gate count by
        ``2**exponent``. The arithmetic construction is expected to be close to linear in the width,
        so an exponent near 1 is the checkable part of this fit and it is checkable entirely inside
        the measured range.
        """
        return 2.0**self.exponent

    def recorded(self) -> list[dict]:
        """The measured points, each carrying ``MEASURED``. No predictions in this list, ever."""
        return [point.to_dict() for point in self.points]

    def extrapolated(self) -> list[dict]:
        """The predictions, each carrying ``EXTRAPOLATED`` and the range it came from."""
        return [point.to_dict() for point in self.predictions]

    def to_dict(self) -> dict:
        """The two lists under separate keys, plus the fit's own parameters.

        ``measured`` and ``extrapolated`` are never concatenated. A consumer that wants both has to
        write the concatenation itself, at which point it is a decision rather than an accident.
        """
        record: dict[str, Any] = {
            "form": self.form,
            "fit_method": self.fit_method,
            "measured": self.recorded(),
            "measured_range": list(self.measured_range),
            "n_points": self.n_points,
            "exponent": self.exponent,
            "scale": self.scale,
            "exponent_provenance": (
                f"{MEASURED} inputs, fitted parameter — a property of the measured range, not of any "
                "width outside it"
            ),
            "rms_residual_log2": self.rms_residual_log2,
            "max_residual_log2": self.max_residual_log2,
            "r_squared": self.r_squared,
            "doubling_width_factor": self.doubling_width_exponent,
            "residuals_provenance": f"{MEASURED}",
            "extrapolated": self.extrapolated(),
        }
        if self.residuals and len(set(p.n_search for p in self.points)) == self.n_points:
            record["per_width_residual_log2"] = {
                str(p.n_search): float(r) / math.log(2.0)
                for p, r in zip(sorted(self.points, key=lambda q: q.n_search), self.residuals)
            }
        return record

    def describe(self) -> dict:
        """The flat mapping the report renders as the fit's table.

        Every numeric value here is a fitted parameter or a prediction drawn from one, and its key
        says so. The measured inputs appear as a count and a range — descriptions of the evidence,
        not numbers blended in beside the model's outputs — so the report's blanket "every value in
        this table is extrapolated" stays true of every number in it.
        """
        table: dict[str, Any] = {
            "form": self.form,
            "fit_method": self.fit_method,
            "measured_points_used": self.n_points,
            "measured_range_n_search": f"{self.measured_range[0]}..{self.measured_range[1]}",
            "extrapolated_exponent": self.exponent,
            "extrapolated_scale_per_width_power": self.scale,
            "extrapolated_rms_residual_log2": self.rms_residual_log2,
            "extrapolated_max_residual_log2": self.max_residual_log2,
            "extrapolated_r_squared": self.r_squared,
            "extrapolated_factor_per_doubling_of_width": self.doubling_width_exponent,
        }
        low, high = self.measured_range
        table["caveat"] = EXTRAPOLATION_CAVEAT_TEMPLATE.format(
            n_points=self.n_points, lo=low, hi=high
        )
        for prediction in self.predictions:
            table[f"extrapolated_gate_count_n_search_{prediction.n_search}"] = prediction.gate_count
        return table


def fit_gate_scaling(
    points: Iterable[MeasuredPoint],
    target_widths: Sequence[int] = (),
    minimum_points: int = MIN_FIT_POINTS,
) -> ScalingFit:
    """Fit the gate-count power law and predict at ``target_widths``.

    Args:
        points: the measured points. Only :class:`MeasuredPoint` instances are accepted, and that is
            the type refusing a refused sweep record for you.
        target_widths: widths to predict. Each prediction carries the measured range it came from,
            including the ones that fall inside it, where the word for what happened is interpolation.
        minimum_points: overridable so a test can exercise the refusal at a smaller size; production
            callers leave it at :data:`MIN_FIT_POINTS`.

    Raises:
        ScalingError: fewer than ``minimum_points`` points, a repeated width, or a non-positive gate
            count — each of which is a fit that would be arithmetically possible and evidentially
            empty.
    """
    ordered = tuple(sorted(points, key=lambda p: p.n_search))
    if not ordered:
        raise ScalingError("there is nothing to fit; a sweep produced no measured points at all")
    exponent, scale, residuals = _log_log_least_squares(
        [p.n_search for p in ordered], [p.gate_count for p in ordered], minimum_points
    )
    fit = ScalingFit(
        points=ordered,
        exponent=exponent,
        scale=scale,
        residuals=tuple(float(r) for r in residuals),
    )
    if not target_widths:
        return fit
    low, high = fit.measured_range
    predictions = tuple(
        ExtrapolatedPoint(
            n_search=int(width),
            gate_count=scale * float(width) ** exponent,
            measured_range=(low, high),
            n_measured_points=fit.n_points,
        )
        for width in target_widths
    )
    return ScalingFit(
        points=fit.points,
        exponent=fit.exponent,
        scale=fit.scale,
        residuals=fit.residuals,
        target_widths=tuple(int(w) for w in target_widths),
        predictions=predictions,
        form=fit.form,
        fit_method=fit.fit_method,
    )


def fit_depth_scaling(
    points: Iterable[MeasuredPoint], target_widths: Sequence[int] = ()
) -> ScalingFit:
    """The same fit on IR depth, for points that carry one.

    Depth and gate count are different curves: a compiler that schedules well can hold depth down
    while the count rises, so predicting one from the other would be an assumption smuggled in as a
    convenience. This fits the depth that was measured, and refuses when too few points measured it.
    """
    with_depth = [p for p in points if p.ir_depth is not None]
    if len(with_depth) < MIN_FIT_POINTS:
        raise ScalingError(
            f"only {len(with_depth)} measured point(s) carry an IR depth; a depth curve cannot be "
            f"fitted from fewer than {MIN_FIT_POINTS}, and inferring depth from gate count would be "
            "a claim about the compiler rather than about the circuit"
        )
    depth_points = [
        MeasuredPoint(
            n_search=p.n_search,
            gate_count=int(p.ir_depth),
            ir_depth=None,
            n_qubits=p.n_qubits,
            wall_seconds=p.wall_seconds,
            lowering=p.lowering,
            source=p.source,
        )
        for p in with_depth
    ]
    fit = fit_gate_scaling(depth_points, target_widths)
    return ScalingFit(
        points=fit.points,
        exponent=fit.exponent,
        scale=fit.scale,
        residuals=fit.residuals,
        target_widths=fit.target_widths,
        predictions=fit.predictions,
        form="ir_depth = scale * n_search ** exponent",
        fit_method=fit.fit_method,
    )


def predict_gate_count(fit: ScalingFit, n_search: int) -> ExtrapolatedPoint:
    """One prediction, with the same labelling the batch path gives it."""
    low, high = fit.measured_range
    return ExtrapolatedPoint(
        n_search=int(n_search),
        gate_count=fit.scale * float(n_search) ** fit.exponent,
        measured_range=(low, high),
        n_measured_points=fit.n_points,
    )


def measured_points_from_sweep(records: Iterable[Mapping[str, Any]]) -> tuple[MeasuredPoint, ...]:
    """Turn ``sweep`` records into measured points, dropping the refused ones.

    Dropping is deliberate and is not silent: each refusal raises where it is encountered only if the
    caller wants it to, and the count of what was dropped is returned alongside via
    :func:`sweep_provenance`. What this function will not do is invent a gate count for a width that
    was refused, which is what would let a curve appear to span widths it never reached.
    """
    points: list[MeasuredPoint] = []
    for record in records:
        if str(record.get("status", "")) != "measured":
            continue
        points.append(MeasuredPoint.from_record(record))
    return tuple(points)


def sweep_provenance(records: Sequence[Mapping[str, Any]]) -> dict:
    """``{MEASURED: n, REFUSED: n}`` for a sweep, so a fit over part of a sweep says which part.

    A fit made from three of five widths is a weaker statement than one made from five, and the only
    thing that distinguishes them in a report is this count travelling with the curve.
    """
    measured = [r for r in records if str(r.get("status", "")) == "measured"]
    refused = [r for r in records if str(r.get("status", "")) != "measured"]
    return {
        MEASURED: len(measured),
        REFUSED: len(refused),
        "measured_widths": sorted(int(r["n_search"]) for r in measured if r.get("n_search") is not None),
        "refused_widths": sorted(int(r["n_search"]) for r in refused if r.get("n_search") is not None),
    }
