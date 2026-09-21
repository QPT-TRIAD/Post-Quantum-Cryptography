"""From measured points to a verdict: does the attacker's work grow exponentially, or not?

Two two-parameter models are fitted to ``(size, log2 work)``:

    exponential   log2 W = a * n + b          work doubles every 1/a units of size
    polynomial    log2 W = k * log2(n) + b    work grows like n^k

They have the same number of parameters, so their residual sums of squares compare directly. The
verdict is the better fit, *when it is clearly better*; otherwise it is "inconclusive", which is a
real outcome and is reported as one. Over a short range the two shapes can be hard to tell apart —
a straight line and a gentle curve — so the verdict also needs enough points and enough range, and
says so when it lacks them rather than guessing.

**What the verdict means.** "Exponential" is a statement about *this attack over this range*. It is
not a proof about larger sizes (see :mod:`qpt_cart.scope`), and an extrapolation to production size
is computed only so it can be set beside the record's formula — it is labelled extrapolated
wherever it appears. "Polynomial" on a subject is the finding this tester exists to make.

Each point is a central value over seeds, of successful runs only: the **mean** for counted work
and the **median** for wall-clock. The mean is what the theory predicts for a counted attack —
exhaustive search for a fixed secret from a random starting point costs a *uniform* number of tries
with mean ``2^(n-1)``, the linear trick a *geometric* number with mean ``2^E`` — and its error
falls as ``1/sqrt(seeds)``, where a median of a uniform draw stays a coin toss: with five seeds it
blurred a known exponential into "inconclusive". Wall-clock gets the median because its errors are
outliers (a page fault, another process), which a mean would absorb and a median ignores. A size
where any seed failed to finish is dropped from the fit and listed, because a central value of the
runs that happened to finish is biased toward the easy ones.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from statistics import mean, median

import numpy as np

__all__ = ["Verdict", "CurveFit", "central_points", "fit_curve"]

MIN_POINTS = 4
MIN_SIZE_RATIO = 1.5            # largest size / smallest size
DECISIVE_RSS_RATIO = 3.0        # how much better the winning model must fit
NOISE_FLOOR_RSS = 1e-9          # below this both models fit perfectly; ratio is meaningless


class Verdict:
    EXPONENTIAL = "exponential in range"
    POLYNOMIAL = "polynomial in range"
    INCONCLUSIVE = "inconclusive"
    INSUFFICIENT = "insufficient data"


@dataclass
class CurveFit:
    verdict: str
    reason: str
    sizes: list[int]
    log2_work: list[float]
    dropped_sizes: list[int] = field(default_factory=list)
    exponent_bits_per_unit: float | None = None         # a
    exponent_ci95: tuple[float, float] | None = None
    intercept: float | None = None
    polynomial_degree: float | None = None              # k
    rss_exponential: float | None = None
    rss_polynomial: float | None = None
    expected_exponent: float | None = None
    exponent_matches_expectation: bool | None = None
    extrapolation: dict | None = None
    provenance: str = "fitted (to measured points; not a measurement)"

    def to_dict(self) -> dict:
        return asdict(self)


def central_points(results, *, use: str = "work") -> tuple[list[int], list[float], list[int]]:
    """``(sizes, log2 central value, dropped sizes)``: mean of counted work, median of seconds."""
    centre = mean if use == "work" else median
    by_size: dict[int, list] = {}
    for result in results:
        by_size.setdefault(result.size, []).append(result)
    sizes, values, dropped = [], [], []
    for size in sorted(by_size):
        runs = by_size[size]
        measures = [getattr(r, use) for r in runs]
        if not all(r.success for r in runs) or any(m is None or m <= 0 for m in measures):
            dropped.append(size)
            continue
        sizes.append(size)
        values.append(math.log2(centre(measures)))
    return sizes, values, dropped


def _linear_fit(x: np.ndarray, y: np.ndarray):
    design = np.vstack([x, np.ones_like(x)]).T
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    residuals = y - design @ coeffs
    rss = float(residuals @ residuals)
    dof = len(x) - 2
    if dof > 0:
        sigma2 = rss / dof
        slope_se = math.sqrt(sigma2 / float(((x - x.mean()) ** 2).sum()))
    else:
        slope_se = float("inf")
    return float(coeffs[0]), float(coeffs[1]), rss, slope_se


# two-sided 97.5% Student-t quantiles by degrees of freedom; beyond the table, the normal value
_T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
         9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 30: 2.042}


def _t975(dof: int) -> float:
    eligible = [d for d in _T975 if d <= dof]
    return _T975[max(eligible)] if eligible else float("inf")


def fit_curve(sizes, log2_work, *, dropped=(), expected_exponent: float | None = None,
              production_size: int | None = None, exponent_tolerance: float = 0.15) -> CurveFit:
    sizes, log2_work = list(sizes), list(log2_work)
    base = CurveFit(Verdict.INSUFFICIENT, "", sizes, log2_work, list(dropped),
                    expected_exponent=expected_exponent)
    if len(sizes) < MIN_POINTS:
        base.reason = f"{len(sizes)} usable size(s); a verdict needs at least {MIN_POINTS}"
        return base
    if max(sizes) / min(sizes) < MIN_SIZE_RATIO:
        base.reason = (f"sizes span {min(sizes)}..{max(sizes)}, a ratio under {MIN_SIZE_RATIO}; over "
                       "so short a range a line and a power law cannot be told apart")
        return base

    x, y = np.asarray(sizes, dtype=float), np.asarray(log2_work, dtype=float)
    a, b, rss_exp, a_se = _linear_fit(x, y)
    k, _, rss_poly, _ = _linear_fit(np.log2(x), y)
    half = _t975(len(sizes) - 2) * a_se
    base.exponent_bits_per_unit, base.intercept = a, b
    base.exponent_ci95 = (a - half, a + half)
    base.polynomial_degree, base.rss_exponential, base.rss_polynomial = k, rss_exp, rss_poly

    if a - half <= 0:
        base.verdict, base.reason = Verdict.INCONCLUSIVE, (
            f"the fitted growth rate {a:.3f} bits per unit is not distinguishable from zero "
            f"(95% interval {a - half:.3f}..{a + half:.3f})")
    elif max(rss_exp, rss_poly) < NOISE_FLOOR_RSS:
        base.verdict, base.reason = Verdict.INCONCLUSIVE, "both models fit exactly; no residual to compare"
    elif rss_poly >= DECISIVE_RSS_RATIO * max(rss_exp, NOISE_FLOOR_RSS):
        base.verdict, base.reason = Verdict.EXPONENTIAL, (
            f"the exponential model fits {rss_poly / max(rss_exp, NOISE_FLOOR_RSS):.1f}x better "
            f"(RSS {rss_exp:.4f} against {rss_poly:.4f})")
    elif rss_exp >= DECISIVE_RSS_RATIO * max(rss_poly, NOISE_FLOOR_RSS):
        base.verdict, base.reason = Verdict.POLYNOMIAL, (
            f"the polynomial model (degree {k:.2f}) fits "
            f"{rss_exp / max(rss_poly, NOISE_FLOOR_RSS):.1f}x better "
            f"(RSS {rss_poly:.4f} against {rss_exp:.4f})")
    else:
        base.verdict, base.reason = Verdict.INCONCLUSIVE, (
            f"neither model is clearly better (RSS exponential {rss_exp:.4f}, polynomial "
            f"{rss_poly:.4f}; a verdict needs a factor of {DECISIVE_RSS_RATIO})")

    if expected_exponent is not None:
        base.exponent_matches_expectation = bool(
            abs(a - expected_exponent) <= max(exponent_tolerance, half))
    if production_size is not None and base.verdict == Verdict.EXPONENTIAL:
        base.extrapolation = {
            "production_size": production_size,
            "log2_work": a * production_size + b,
            "log2_work_ci95": ((a - half) * production_size + b, (a + half) * production_size + b),
            "provenance": "extrapolated (model-based; not measured)",
            "warning": "a straight-line extrapolation across a factor of "
                       f"{production_size / max(sizes):.0f} in size; the record's own attack lab "
                       "found fits like this off by +4.6, -12.4 and -38.1 bits",
        }
    return base
