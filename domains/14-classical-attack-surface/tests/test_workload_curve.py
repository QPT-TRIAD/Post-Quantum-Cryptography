"""The verdict machinery, on curves whose shape is known because they were made that way.

The whole tester reduces to one judgement — exponential or polynomial — so that judgement is tested
directly on synthetic data: clean curves of each shape, noisy ones, ranges too short to decide, and
the cases where the honest answer is "cannot tell". The thresholds are pinned so a change to them
is a visible decision and not a side effect.
"""

from __future__ import annotations

import math
import random

import pytest

from qpt_cart.analysis import workload_curve as wc
from qpt_cart.analysis.workload_curve import Verdict, central_points, fit_curve
from qpt_cart.attacks.base import AttackResult

SIZES = [8, 10, 12, 14, 16, 18, 20]


def test_a_clean_exponential_is_called_exponential_at_its_rate():
    fit = fit_curve(SIZES, [0.8 * n - 3 for n in SIZES], expected_exponent=0.8, production_size=256)
    assert fit.verdict == Verdict.EXPONENTIAL
    assert fit.exponent_bits_per_unit == pytest.approx(0.8)
    assert fit.exponent_matches_expectation is True
    assert fit.extrapolation["log2_work"] == pytest.approx(0.8 * 256 - 3)
    assert "not measured" in fit.extrapolation["provenance"]
    assert "-38.1" in fit.extrapolation["warning"]


@pytest.mark.parametrize("degree", [2.0, 3.0, 5.0])
def test_a_clean_power_law_is_called_polynomial_with_its_degree(degree):
    fit = fit_curve(SIZES, [degree * math.log2(n) + 1 for n in SIZES], production_size=256)
    assert fit.verdict == Verdict.POLYNOMIAL
    assert fit.polynomial_degree == pytest.approx(degree)
    assert fit.extrapolation is None, "a polynomial curve is a finding, not something to extrapolate"


@pytest.mark.parametrize("seed", range(8))
def test_the_verdicts_survive_the_sampling_noise_the_campaign_actually_has(seed):
    """0.15 bits is the noise of a 64-seed mean of a uniform count; both shapes must survive it."""
    rng = random.Random(seed)
    noisy = lambda values: [v + rng.gauss(0, 0.15) for v in values]            # noqa: E731
    assert fit_curve(SIZES, noisy([n - 1.0 for n in SIZES])).verdict == Verdict.EXPONENTIAL
    assert fit_curve([16, 24, 32, 48, 64, 96, 128],
                     noisy([3 * math.log2(n) for n in (16, 24, 32, 48, 64, 96, 128)])
                     ).verdict == Verdict.POLYNOMIAL


def test_too_few_points_or_too_short_a_range_is_insufficient_not_a_guess():
    assert fit_curve([8, 10, 12], [7, 9, 11]).verdict == Verdict.INSUFFICIENT
    short = fit_curve([20, 21, 22, 23, 24], [19, 20, 21, 22, 23])
    assert short.verdict == Verdict.INSUFFICIENT and "cannot be told apart" in short.reason
    assert wc.MIN_POINTS == 4 and wc.MIN_SIZE_RATIO == 1.5 and wc.DECISIVE_RSS_RATIO == 3.0


def test_a_flat_curve_and_an_ambiguous_curve_are_inconclusive():
    rng = random.Random(1)
    flat = fit_curve(SIZES, [10 + rng.gauss(0, 0.3) for _ in SIZES])
    assert flat.verdict == Verdict.INCONCLUSIVE and "not distinguishable from zero" in flat.reason
    # halfway between the two shapes: neither model wins by the decisive factor
    blend = [0.5 * (n - 1) + 0.5 * (6.2 * math.log2(n) - 12) for n in SIZES]
    assert fit_curve(SIZES, blend).verdict == Verdict.INCONCLUSIVE


def test_a_rate_that_disagrees_with_the_expected_one_is_flagged():
    fit = fit_curve(SIZES, [0.5 * n for n in SIZES], expected_exponent=1.0)
    assert fit.verdict == Verdict.EXPONENTIAL and fit.exponent_matches_expectation is False


def _run(size, work, seconds=1.0, success=True):
    return AttackResult("a", "p", size, 0, success, work, "u", seconds)


def test_counted_work_uses_the_mean_and_wall_clock_uses_the_median():
    runs = [_run(8, 10.0, 1.0), _run(8, 20.0, 2.0), _run(8, 90.0, 100.0)]
    sizes, values, _ = central_points(runs, use="work")
    assert values == [pytest.approx(math.log2(40.0))]
    sizes, values, _ = central_points(runs, use="seconds")
    assert values == [pytest.approx(math.log2(2.0))], "one slow run does not move a median"


def test_a_size_where_any_seed_failed_is_dropped_not_averaged_over_the_survivors():
    runs = [_run(8, 100.0), _run(8, 120.0), _run(10, 400.0), _run(10, None, success=False)]
    sizes, _, dropped = central_points(runs, use="work")
    assert sizes == [8] and dropped == [10]
