"""The success curve, checked against the closed form before it is pointed at anything.

The order of these tests is the order the validation was done in: a trivial instance where the answer
is known by hand, then the derived iteration range, then the exact rational bound, then the QLWR
instance the project actually cares about. A curve that disagrees with ``sin^2((2k+1)theta)`` at
``n = 4, M = 1`` would make every later number meaningless, and at that width the whole check costs
milliseconds — there is no reason to look at ``n = 12`` first.
"""

from __future__ import annotations

import math
import warnings
from fractions import Fraction

import numpy as np
import pytest

from grover_emulator.analysis.success_probability import (
    PI_OVER_TWO_UPPER,
    AnalysisError,
    compare_to_exact_bound,
    exact_bound_applicability,
    exact_bound_for_spec,
    exact_success_interval,
    exact_success_lower_bound,
    exact_success_upper_bound,
    fit_residuals,
    marked_probability,
    measured_success_probability,
    sample_counts,
    search_register_probabilities,
    statevector_of,
    success_curve,
    theoretical_success_probability,
)
from grover_emulator.circuits.grover_circuit_builder import (
    derive_iteration_range,
    optimal_iterations,
)
from grover_emulator.problem.oracle_spec import (
    HiddenPeriodOracleSpec,
    Lowering,
    RandomControlOracleSpec,
)
from reference_statevector import ReferenceStatevector

# The smallest instance on which "does the harness measure the thing it says it measures" can be
# answered by hand: four basis states, one of them marked, theta = arcsin(1/4).
TINY_N = 4
TINY_K_OPT = 3


@pytest.fixture(scope="module")
def backend() -> ReferenceStatevector:
    return ReferenceStatevector()


@pytest.fixture(scope="module")
def tiny_spec() -> RandomControlOracleSpec:
    return RandomControlOracleSpec(n_qubits=TINY_N, n_marked=1, seed=11)


# -----------------------------------------------------------------------------------------------
# the trivial instance, before anything else
# -----------------------------------------------------------------------------------------------


def test_tiny_instance_agrees_with_the_closed_form(tiny_spec, backend):
    """n=4, M=1: the measured curve is ``sin^2((2k+1)theta)`` to float precision, at every k."""
    curve = success_curve(tiny_spec, backend)
    assert curve.n_marked == 1
    assert curve.n_items == 1 << TINY_N
    assert curve.optimal_iterations == TINY_K_OPT
    summary = curve.residuals
    assert summary["max_abs_residual"] < 1e-12, summary
    assert summary["peak_iteration_agrees"], summary
    assert curve.peak_measured.measured == pytest.approx(curve.peak_closed_form.closed_form, abs=1e-12)


def test_closed_form_is_sin_squared_of_theta(tiny_spec):
    """The closed form this module compares against is literally ``sin^2((2k+1) * theta)``."""
    theta = math.asin(math.sqrt(1.0 / (1 << TINY_N)))
    for k in range(0, 6):
        assert theoretical_success_probability(tiny_spec, k) == pytest.approx(
            math.sin((2 * k + 1) * theta) ** 2, abs=1e-15
        )


def test_single_point_measurement_matches_the_curve_point(tiny_spec, backend):
    """``measured_success_probability`` at ``k`` is the same number the curve records at ``k``."""
    for k in (0, TINY_K_OPT, TINY_K_OPT + 2):
        measured = measured_success_probability(tiny_spec, backend, k)
        assert measured == pytest.approx(theoretical_success_probability(tiny_spec, k), abs=1e-12)


def test_probabilities_are_a_distribution(backend):
    """The marginal over the search register sums to 1 and the marked sum is the success event."""
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=4, seed=3)
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit

    statevector = statevector_of(backend, build_grover_circuit(spec, 3, Lowering.TRUTH_TABLE))
    probabilities = search_register_probabilities(statevector, spec.search_width())
    assert probabilities.shape == (1 << 6,)
    assert float(probabilities.sum()) == pytest.approx(1.0, abs=1e-12)
    assert marked_probability(probabilities, spec.marked_set()) == pytest.approx(
        theoretical_success_probability(spec, 3), abs=1e-12
    )


# -----------------------------------------------------------------------------------------------
# the iteration range is derived, never chosen
# -----------------------------------------------------------------------------------------------


def test_derived_range_contains_the_peak(tiny_spec):
    iteration_range = derive_iteration_range(tiny_spec)
    assert iteration_range.start == 0
    assert TINY_K_OPT in iteration_range
    # The default range must also show the curve turn over, or the peak is indistinguishable from
    # the end of the window.
    assert max(iteration_range) > TINY_K_OPT


def test_qlwr_optimum_is_derived_and_the_default_window_reaches_it(qlwr_spec):
    """The worked instance's k_opt is 50, and the default window is built from it rather than fixed.

    A window like ``[0, 40]`` returns a smooth, monotone, entirely plausible rising curve that never
    reaches its peak. This asserts the window is derived from this instance's own ``(M, N)`` so that
    the failure mode cannot reappear as a constant somebody liked the look of.
    """
    assert qlwr_spec.space().n_marked == 1
    assert optimal_iterations(qlwr_spec) == 50
    iteration_range = derive_iteration_range(qlwr_spec)
    assert 50 in iteration_range
    assert max(iteration_range) > 50


def test_short_fixed_window_warns_and_records_that_it_missed_the_peak(tiny_spec, backend):
    """A truncated window is reported, not silently measured.

    ``[0, 2]`` stops one iteration short of this instance's peak, and the curve across it rises
    smoothly — the exact shape that reads as a result. The warning and the flag are what make it
    readable as a truncation instead.
    """
    with pytest.warns(UserWarning, match="does not"):
        truncated = success_curve(tiny_spec, backend, iteration_range=range(0, TINY_K_OPT))
    assert truncated.window_contains_closed_form_peak is False
    # The numbers are still recorded — the point is to report the truncation, not to refuse.
    assert len(truncated.points) == TINY_K_OPT
    assert truncated.peak_measured.measured < 1.0


def test_derived_window_does_not_warn(tiny_spec, backend):
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        curve = success_curve(tiny_spec, backend)
    assert curve.window_contains_closed_form_peak is True


def test_empty_iteration_range_is_refused(tiny_spec, backend):
    with pytest.raises(AnalysisError, match="empty"):
        success_curve(tiny_spec, backend, iteration_range=range(0, 0))


# -----------------------------------------------------------------------------------------------
# the exact rational bound
# -----------------------------------------------------------------------------------------------


def test_exact_bounds_are_fractions_not_floats():
    """The bound never becomes a float, not even for a moment, and the closed form has an exact pair.

    ``n = 8``, ``M = 1``: ``y = 1/16``, so the lower bound is ``(1/16 - 1/(6*16^3))^2`` and the upper
    is ``(1/16)^2``. Both are written here as fractions, so the test fails if the implementation ever
    routes the arithmetic through ``float``.
    """
    lower, upper = exact_success_interval(8, 0, 0)
    assert isinstance(lower, Fraction) and isinstance(upper, Fraction)
    assert lower == Fraction(1535, 24576) ** 2 == Fraction(2356225, 603979776)
    assert upper == Fraction(1, 256)
    assert lower < upper


def test_exact_bound_brackets_the_measured_curve(tiny_spec, backend):
    """Every measured point sits inside the exactly-rational interval, compared in Fraction space."""
    curve = success_curve(tiny_spec, backend)
    summary = curve.exact_bound_comparison()
    # k = 0, 1, 2 at n = 4: (2k+1)/4 stays at or below pi/2, and k >= 3 leaves the valid range.
    assert summary.n_compared == 3
    assert summary.all_meet_lower
    assert summary.n_within_interval == summary.n_compared
    for comparison in summary.comparisons:
        assert isinstance(comparison.lower, Fraction)
        assert comparison.lower <= Fraction(comparison.measured) <= comparison.upper
        assert comparison.gap_over_lower >= 0


def test_bound_is_undefined_where_the_density_exponent_is_odd():
    """``M = 2`` at ``n = 8`` has an irrational ``sin(theta)`` and therefore no exact rational bound.

    The refusal is returned with its reason rather than raised, so a curve-wide comparison can record
    the points it skipped; a silently missing point reads like a point the bound was met at.
    """
    applicable, reason = exact_bound_applicability(8, 0, 1)
    assert applicable is False
    assert "odd" in reason
    with pytest.raises(ValueError, match="odd"):
        exact_success_lower_bound(8, 0, 1)


def test_bound_is_undefined_past_the_first_peak():
    """``(2k+1) * sin(theta) > pi/2`` leaves the range the series argument is valid on.

    That is a refusal of the domain, not a loose bound: reporting the largest undefined point as zero
    would read as a bound the curve failed at.
    """
    applicable, reason = exact_bound_applicability(8, 13, 0)
    assert applicable is False
    assert "pi/2" in reason
    assert Fraction(27, 16) > PI_OVER_TWO_UPPER
    assert exact_bound_applicability(8, 12, 0)[0] is True


def test_comparison_records_every_skipped_point_with_its_reason(tiny_spec, backend):
    curve = success_curve(tiny_spec, backend)
    summary = compare_to_exact_bound(curve.records, log2_targets=0, n_bits=TINY_N)
    assert summary.n_compared + len(summary.skipped) == len(curve.records)
    assert all(reason for _, reason in summary.skipped)
    record = summary.to_dict()
    assert record["n_compared"] == summary.n_compared
    assert record["n_skipped"] == len(summary.skipped)
    assert record["all_meet_lower"] is True


def test_exact_bound_for_spec_refuses_a_marked_set_that_is_not_a_power_of_two():
    spec = RandomControlOracleSpec(n_qubits=8, n_marked=3, seed=5)
    with pytest.raises(ValueError, match="not a power of two"):
        exact_bound_for_spec(spec, 0)
    with pytest.raises(AnalysisError, match="not a power of two"):
        success_curve(spec, ReferenceStatevector(), iteration_range=range(0, 2)).exact_bound_comparison()


def test_exact_bound_for_spec_uses_the_specs_own_m(tiny_spec):
    lower, upper = exact_bound_for_spec(tiny_spec, 1)
    assert (lower, upper) == exact_success_interval(TINY_N, 1, log2_targets=0)


def test_bound_requires_a_width_when_the_records_do_not_carry_one():
    records = [{"iteration": 0, "empirical_p_success": 0.5, "theoretical_p_success": 0.5}]
    with pytest.raises(AnalysisError, match="search width"):
        compare_to_exact_bound(records, log2_targets=0)


# -----------------------------------------------------------------------------------------------
# sampling: seeded, reproducible, and never a substitute for the exact amplitudes
# -----------------------------------------------------------------------------------------------


def test_sampling_is_reproducible_from_the_runs_own_seed_parts():
    probabilities = np.full(16, 1.0 / 16.0)
    first = sample_counts(probabilities, 4096, "run-a", 7)
    second = sample_counts(probabilities, 4096, "run-a", 7)
    other = sample_counts(probabilities, 4096, "run-b", 7)
    assert first == second
    assert sum(first.values()) == 4096
    assert other != first


def test_sampling_refuses_a_distribution_that_does_not_sum_to_one():
    with pytest.raises(AnalysisError, match="sum"):
        sample_counts(np.full(4, 0.5), 10, "x")


def test_sampled_estimator_tracks_the_exact_probability(tiny_spec, backend):
    curve = success_curve(tiny_spec, backend, shots=20000, seed_parts=("test",))
    peak = curve.peak_measured
    assert peak.sampled is not None
    assert peak.shots == 20000
    # A binomial estimate at 20000 shots has a standard error below 0.004 here; 0.02 is generous and
    # still tight enough to fail if the sampling were drawing from the wrong distribution.
    assert peak.sampled == pytest.approx(peak.measured, abs=0.02)


def test_sampling_does_not_disturb_the_measured_curve(tiny_spec, backend):
    """Turning shots on must not change the exact numbers: the sampler is a separate read-out."""
    exact = success_curve(tiny_spec, backend)
    sampled = success_curve(tiny_spec, backend, shots=1000, seed_parts=("test",))
    for a, b in zip(exact.points, sampled.points):
        assert a.measured == b.measured
        assert a.closed_form == b.closed_form


# -----------------------------------------------------------------------------------------------
# the record shape the report renders, and the residual summary
# -----------------------------------------------------------------------------------------------


def test_curve_records_carry_the_keys_the_report_reads(tiny_spec, backend):
    curve = success_curve(tiny_spec, backend, iteration_range=range(0, 3))
    for record in curve.records:
        assert {"iteration", "empirical_p_success", "theoretical_p_success"} <= set(record)
        assert "residual" in record
        assert record["provenance"]["empirical_p_success"].startswith("measured")


def test_describe_carries_the_window_and_both_peaks(tiny_spec, backend):
    curve = success_curve(tiny_spec, backend)
    described = curve.describe()
    assert described["optimal_iterations"] == TINY_K_OPT
    # The derived window is [0, k_opt + extra], recorded by its endpoints.
    assert described["iteration_range"] == [0, TINY_K_OPT + 2]
    assert len(described["curve"]) == len(curve.points)
    assert described["peak_measured"]["iteration"] == TINY_K_OPT
    assert described["peak_closed_form"]["iteration"] == TINY_K_OPT


def test_fit_residuals_reports_a_summary_and_labels_it_a_fit(tiny_spec, backend):
    summary = fit_residuals(success_curve(tiny_spec, backend).records)
    assert summary["n_points"] == TINY_K_OPT + 3
    assert summary["rms_residual"] < 1e-12
    assert summary["peak_iteration_agrees"] is True
    assert "fit" in summary["provenance"]


def test_fit_residuals_needs_both_curves():
    with pytest.raises(AnalysisError, match="residual summary"):
        fit_residuals([{"iteration": 0, "empirical_p_success": 0.5}])


# -----------------------------------------------------------------------------------------------
# the backend contract
# -----------------------------------------------------------------------------------------------


class _WrongShape:
    def statevector(self, circuit):
        return np.zeros(4, dtype=complex)


class _Unnormalised:
    def statevector(self, circuit):
        return np.zeros(1 << circuit.num_qubits, dtype=complex)


class _NoMethod:
    pass


class _TolerantlyNamed:
    def __init__(self, inner):
        self.inner = inner

    def get_statevector(self, circuit):
        return self.inner.statevector(circuit)


def test_statevector_over_the_wrong_width_is_refused(tiny_spec):
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit

    circuit = build_grover_circuit(tiny_spec, 1, Lowering.TRUTH_TABLE)
    with pytest.raises(AnalysisError, match="expected"):
        statevector_of(_WrongShape(), circuit)


def test_unnormalised_statevector_is_refused(tiny_spec):
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit

    circuit = build_grover_circuit(tiny_spec, 1, Lowering.TRUTH_TABLE)
    with pytest.raises(AnalysisError, match="non-normalised"):
        statevector_of(_Unnormalised(), circuit)


def test_backend_without_a_statevector_method_is_refused(tiny_spec):
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit

    circuit = build_grover_circuit(tiny_spec, 1, Lowering.TRUTH_TABLE)
    with pytest.raises(AnalysisError, match="statevector"):
        statevector_of(_NoMethod(), circuit)


def test_a_backend_spelling_the_method_differently_still_works(tiny_spec, backend):
    measured = measured_success_probability(tiny_spec, _TolerantlyNamed(backend), 2)
    assert measured == pytest.approx(theoretical_success_probability(tiny_spec, 2), abs=1e-12)


def test_search_register_probabilities_refuses_a_non_power_of_two_state():
    with pytest.raises(AnalysisError, match="power of two"):
        search_register_probabilities(np.zeros(3, dtype=complex), 1)


# -----------------------------------------------------------------------------------------------
# the worked instance
# -----------------------------------------------------------------------------------------------


def test_worked_instance_peaks_at_the_derived_optimum(qlwr_spec, backend):
    """The QLWR curve over a window around k=50, measured against the closed form.

    Seven points rather than all 53: the assertion is about the peak and the residual, and the whole
    range costs about ten seconds at ``n = 12`` for no extra information. The window still contains
    the turnover at k=51, so the peak is a maximum and not the end of the range.
    """
    curve = success_curve(qlwr_spec, backend, iteration_range=range(47, 53))
    assert curve.window_contains_closed_form_peak is True
    assert curve.peak_measured.iteration == 50
    assert curve.peak_closed_form.iteration == 50
    assert curve.peak_measured.measured > 0.9999
    assert curve.peak_measured.measured == pytest.approx(curve.peak_closed_form.closed_form, abs=1e-12)
    assert curve.residuals["max_abs_residual"] < 1e-12
    # The curve is seen to come down again, which is what distinguishes a peak from a plateau.
    assert curve.points[-1].measured < curve.points[-2].measured


def test_worked_instance_meets_the_exact_lower_bound_at_every_comparable_point(qlwr_spec, backend):
    """Below the peak the exact bound exists, and the measured curve clears it exactly.

    Above the peak ``(2k+1) * sin(theta)`` leaves ``[0, pi/2]`` and the bound is undefined, so the
    comparison splits into points compared and points skipped — never into points quietly dropped.
    """
    curve = success_curve(qlwr_spec, backend, iteration_range=range(45, 53))
    summary = curve.exact_bound_comparison()
    assert summary.n_compared >= 4
    assert summary.n_skipped >= 1
    assert summary.all_meet_lower
    assert summary.n_within_interval == summary.n_compared
    skipped_iterations = {k for k, _ in summary.skipped}
    assert skipped_iterations.issubset({50, 51, 52})
    assert all("pi/2" in reason for _, reason in summary.skipped)


def test_a_spec_with_no_arithmetic_lowering_is_measured_the_same_way(backend):
    """The curve does not depend on which spec it is given, only on ``(M, N)`` — which is the point.

    A diagonal phase oracle contributes nothing to the amplitude of the marked set; what the circuit
    certifies is ``M``, and what it costs is the subject of the scaling module. Two structurally
    different oracles with the same ``(M, N)`` must produce the same curve, and this asserts it on
    the positive-control spec rather than on a third ad-hoc instance.
    """
    period = HiddenPeriodOracleSpec(n_qubits=6, period=0b1000, seed=11)
    curve = success_curve(period, backend, iteration_range=range(0, 3))
    for point in curve.points:
        assert point.measured == pytest.approx(point.closed_form, abs=1e-12)
