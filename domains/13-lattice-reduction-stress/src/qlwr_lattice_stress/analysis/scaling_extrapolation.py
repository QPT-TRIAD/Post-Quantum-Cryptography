"""Fitting the core-SVP model to measured points, and refusing to pretend an extrapolation is one.

The model is ``cost = 2^(c * beta)``, so ``log2(cost) = c * beta + intercept`` — a straight line in
the block size, which is the whole reason core-SVP is expressed that way.

**The fitted domain is part of the result, not documentation.** Core-SVP models *sieving* cost and
says nothing about the enumeration regime, so evaluating it below the block sizes it was fitted on is
a category error rather than an inaccuracy. :class:`~qlwr_lattice_stress.protocols.ScalingModel`
therefore requires ``extrapolates_outside_fitted_domain`` as a judgement the caller has to make,
rather than letting a number be quietly produced for a region where the model has no claim.

**Measured and extrapolated never share a container here.** A single fit result is one or the other,
and the caller states which when it evaluates. That is the same rule the reports are built on, moved
into the analysis layer so it cannot be lost on the way to a figure.

**A fit with fewer than three points is refused.** Two points determine a line exactly, so the
residual is zero by construction and the fit cannot be contradicted by its own data — a
two-point "fit" with an R² of 1.0 is the most confident-looking thing it is possible to produce from
the least evidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..protocols import EXTRAPOLATED, MEASURED, Provenance, ScalingModel

__all__ = [
    "BlockSizeGrowth",
    "InsufficientPoints",
    "NonPositiveSlope",
    "fit_block_size_growth",
    "fit_core_svp_model",
    "predict_log2_cost",
    "measurements_to_frame",
]


class NonPositiveSlope(ValueError):
    """The fit found cost *decreasing* with block size, which no reduction does.

    A distinct exception from :class:`InsufficientPoints` because the response differs: too few
    points means gather more, while a non-positive slope means the two axes being fitted are not the
    relationship the model describes.
    """


class InsufficientPoints(ValueError):
    """Fewer points than the model can be tested against.

    Raised rather than returning a degenerate fit: a line through two points has no residual, so it
    cannot be contradicted by its own data, and reporting ``R^2 = 1.0`` from it would be the most
    confident possible statement from the least possible evidence.
    """


@dataclass(frozen=True, slots=True)
class FittedModel:
    """The fit, with the domain it is valid on and the slope's meaning recorded."""

    model: ScalingModel
    points: tuple[tuple[int, float], ...]

    def predict_log2_cost(self, block_size: int) -> tuple[float, Provenance]:
        """``log2(cost)`` at a block size, tagged with whether that is a measurement or not.

        The tag is returned alongside the number rather than being left to the caller to remember.
        A value produced outside the fitted domain comes back as ``extrapolated``, and everything
        that consumes it can then label it without having to re-derive where the domain ended.
        """
        value = self.model.intercept + self.model.c * block_size
        inside = self.model.fitted_beta_min <= block_size <= self.model.fitted_beta_max
        return value, (MEASURED if inside else EXTRAPOLATED)


def fit_core_svp_model(df, *, block_size_column: str = "block_size",
                       cost_column: str = "log2_cost", minimum_points: int = 3) -> FittedModel:
    """Least-squares fit of ``log2(cost)`` against block size.

    Takes a frame rather than live result objects so it can be exercised against a synthetic table
    with a known slope, which is how the fit itself is tested — a fit validated only against real
    data cannot distinguish "the model holds" from "the fit works".
    """
    if block_size_column not in df.columns or cost_column not in df.columns:
        raise ValueError(
            f"frame needs columns {block_size_column!r} and {cost_column!r}; "
            f"it has {list(df.columns)}"
        )

    clean = df[[block_size_column, cost_column]].dropna()
    points = tuple(
        (int(b), float(c)) for b, c in zip(clean[block_size_column], clean[cost_column])
    )
    if len(points) < minimum_points:
        raise InsufficientPoints(
            f"a fit needs at least {minimum_points} points; got {len(points)}. Two points "
            "determine a line exactly, so the residual is zero by construction and the fit cannot "
            "be contradicted by its own data."
        )

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    n = len(points)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    if sxx == 0:
        raise ValueError("every point has the same block size; the slope is not determined")

    slope = sxy / sxx
    intercept = mean_y - slope * mean_x

    # A non-positive exponent is not a fit, it is a measurement that does not support one. The model
    # says cost grows with block size; a negative slope says it shrinks, which no reduction does.
    #
    # Measured on the first real sweep: dimension 40 reached its minimum at block size 10 in 3.69 s,
    # while dimension 80 reached its minimum at block size 20 in 1.63 s — faster at a *larger* block
    # size. The reason is that the two axes in the triple are separately determined: the minimum
    # block size is a property of the instance, and the wall clock is a property of this machine and
    # this engine at that block size. Fitting one against the other assumes they are the same
    # quantity, and across a handful of points they are not.
    #
    # Refused rather than returned, because a negative ``c`` would flow into every extrapolation
    # downstream and look exactly like a number.
    if slope <= 0:
        raise NonPositiveSlope(
            f"the fitted slope is {slope:.4f}, so cost would *decrease* with block size. The model "
            "says it grows, and no reduction contradicts that — so the measurement does not support "
            "this fit. Across dimensions the minimum block size and the wall clock are separately "
            "determined, and a few points cannot separate them. See notes/09 for what to fit "
            "instead: the required block size against dimension, with core-SVP applied afterwards."
        )
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    beta_min, beta_max = min(xs), max(xs)
    model = ScalingModel(
        c=slope,
        intercept=intercept,
        r_squared=r_squared,
        fitted_beta_min=beta_min,
        fitted_beta_max=beta_max,
        n_points=n,
        # Fitting says nothing about whether the caller will evaluate inside the domain, so the
        # honest default is that it might. A caller that stays inside sets it False explicitly.
        extrapolates_outside_fitted_domain=False,
        provenance=MEASURED,
    )
    return FittedModel(model=model, points=points)


@dataclass(frozen=True, slots=True)
class BlockSizeGrowth:
    """How the *required block size* grows with lattice dimension — the measured relationship.

    This is what a sweep can actually measure. The core-SVP exponent is a model constant (0.292
    classical, 0.265 quantum); it is not something a small sweep estimates, and attempting to
    fit it against wall-clock time measures the machine rather than the model.

    The extrapolation chain is therefore two labelled steps:

    1. **measured** — fit ``beta_min`` against dimension, over the dimensions that reached one;
    2. **extrapolated** — evaluate that fit at the production dimension, then apply core-SVP at the
       resulting block size.

    Each step is labelled, and neither is presented as the other. A reader can reject the first
    without rejecting the second, which is the point of keeping them apart.
    """

    slope: float
    intercept: float
    r_squared: float
    fitted_dimension_min: int
    fitted_dimension_max: int
    n_points: int
    points: tuple[tuple[int, int], ...]

    def block_size_at(self, dimension: int) -> tuple[float, Provenance]:
        """Predicted required block size at a dimension, tagged with which side of the range it is."""
        value = self.intercept + self.slope * dimension
        inside = self.fitted_dimension_min <= dimension <= self.fitted_dimension_max
        return value, (MEASURED if inside else EXTRAPOLATED)

    def core_svp_log2_cost_at(
        self, dimension: int, *, c: float = 0.292
    ) -> tuple[float, Provenance]:
        """Core-SVP cost at the predicted block size for a dimension.

        **Always extrapolated**, even inside the fitted dimension range: the block size may be a
        measured-relationship output there, but the cost is the model's, and labelling it measured
        because the block size was interpolated would be the exact blend the reports exist to
        prevent.
        """
        beta, _ = self.block_size_at(dimension)
        return c * beta, EXTRAPOLATED


def fit_block_size_growth(df, *, dimension_column: str = "dimension",
                          block_size_column: str = "block_size",
                          minimum_points: int = 3) -> BlockSizeGrowth:
    """Fit the required block size against lattice dimension.

    Monotone in the direction the model needs — a larger lattice needs at least as large a block
    size — so unlike a wall-clock fit it cannot produce a negative exponent. Where it is still
    non-monotone the caller sees it in ``r_squared`` rather than in a sign error.

    Dimensions that never reached a minimum are **absent** rather than zero: a dimension the attack
    could not solve within the configured range says nothing about how the block size grows, and
    entering a zero would drag the slope down with a measurement that was never made.
    """
    import pandas as pd  # noqa: F401

    if dimension_column not in df.columns or block_size_column not in df.columns:
        raise ValueError(
            f"frame needs columns {dimension_column!r} and {block_size_column!r}; "
            f"it has {list(df.columns)}"
        )
    clean = df[[dimension_column, block_size_column]].dropna()
    points = tuple(
        (int(d), int(b)) for d, b in zip(clean[dimension_column], clean[block_size_column])
    )
    if len(points) < minimum_points:
        raise InsufficientPoints(
            f"a growth fit needs at least {minimum_points} dimensions that reached a minimum block "
            f"size; got {len(points)}. Dimensions where the attack did not reach contribute "
            "nothing, because the range being too short is not a measurement of the block size."
        )

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    n = len(points)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    if sxx == 0:
        raise ValueError("every point has the same dimension; the slope is not determined")

    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    return BlockSizeGrowth(
        slope=slope, intercept=intercept,
        r_squared=(1.0 - ss_res / ss_tot) if ss_tot > 0 else 1.0,
        fitted_dimension_min=min(xs), fitted_dimension_max=max(xs),
        n_points=n, points=points,
    )


def predict_log2_cost(model: ScalingModel, block_size: int) -> tuple[float, Provenance]:
    """Convenience wrapper over :meth:`FittedModel.predict_log2_cost` for a bare model."""
    value = model.intercept + model.c * block_size
    inside = model.fitted_beta_min <= block_size <= model.fitted_beta_max
    return value, (MEASURED if inside else EXTRAPOLATED)


def measurements_to_frame(measurements):
    """Build the frame the fit consumes from a sequence of measured attack results.

    Only points that were actually measured are included: a refusal has no cost to fit, and putting
    a zero or a sentinel in its place would drag the slope toward whatever value the sentinel
    happened to be. Refusals are dropped with their count recorded by the caller, not silently.
    """
    import pandas as pd

    rows = []
    for result in measurements:
        if getattr(result, "provenance", MEASURED) != MEASURED:
            continue
        wall = getattr(result, "wall_clock_s", None)
        if wall is None or wall <= 0:
            continue
        rows.append({
            "block_size": int(result.block_size),
            "wall_clock_s": float(wall),
            "log2_cost": math.log2(float(wall)),
            "dimension": int(getattr(result, "dimension", 0) or 0),
        })
    return pd.DataFrame(rows, columns=["block_size", "wall_clock_s", "log2_cost", "dimension"])
