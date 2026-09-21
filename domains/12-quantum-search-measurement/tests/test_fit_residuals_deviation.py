"""The residual summary, fed a curve that actually departs from the closed form.

Every other test in this suite hands :func:`fit_residuals` a curve whose residual is float noise, so a
summary that returned zeros — or that read the closed-form column twice — would pass all of them. This
file is the other half: curves that *deviate*, with the size of the deviation worked out by hand or
from the construction, so the three magnitudes and the peak flag are each seen to move when they
should and by the amount they should.

Four deviations, because they fail differently:

* a **hand-sized table** whose residuals are ``0.1, -0.2, -0.4, 0.2``, where every summary statistic
  is a number a reader can check on paper;
* a **damped** curve — the shape decoherence or a leaking ancilla would produce — whose peak may stay
  put while the magnitudes grow;
* a **shifted** curve — the shape an off-by-one in the round count produces — where the peak flag is
  the thing that must fall;
* a **constant** curve, the shape of an oracle that marks nothing the diffuser can amplify.

Then the converse, which is what makes a large residual mean something: a genuine curve estimated from
a finite number of shots stays inside binomial sampling noise, point by point. The plan this project
was built from says a statistically significant deviation "must be flagged, not silently averaged
away"; the last test records, as a strict expected failure, that the summary carries magnitudes only
and no such flag.
"""

from __future__ import annotations

import math

import pytest

from grover_emulator.analysis.success_probability import fit_residuals, success_curve
from grover_emulator.problem.oracle_spec import RandomControlOracleSpec
from reference_statevector import ReferenceStatevector

SHOTS = 20000
"""The configuration's own default shot count, so the noise floor asserted here is the one a run has."""

SIGMAS = 5.0
"""How many binomial standard deviations a genuine sampled point may sit from the closed form."""


@pytest.fixture(scope="module")
def backend() -> ReferenceStatevector:
    return ReferenceStatevector()


@pytest.fixture(scope="module")
def spec() -> RandomControlOracleSpec:
    """``N = 64, M = 1``: ``k_opt = 6``, so the derived window ``[0, 8]`` has a peak with room to move."""
    return RandomControlOracleSpec(n_qubits=6, n_marked=1, seed=11)


@pytest.fixture(scope="module")
def genuine(spec, backend) -> list[dict]:
    """The records of a real measured curve, which the tests below then bend on purpose."""
    return success_curve(spec, backend).records


def _closed_form(k: int, n_items: int = 64, n_marked: int = 1) -> float:
    """``sin^2((2k+1) theta)``, written out here rather than imported so the check is independent."""
    theta = math.asin(math.sqrt(n_marked / n_items))
    return math.sin((2 * k + 1) * theta) ** 2


def _with_measured(records: list[dict], values: list[float]) -> list[dict]:
    """The same records with the measured column replaced, and nothing else touched."""
    assert len(records) == len(values)
    return [{**record, "empirical_p_success": value} for record, value in zip(records, values)]


def _binomial_sigma(p: float, shots: int) -> float:
    return math.sqrt(max(p * (1.0 - p), 0.0) / shots)


# -----------------------------------------------------------------------------------------------
# the fixture is the curve the deviations are measured from
# -----------------------------------------------------------------------------------------------


def test_the_genuine_curve_is_the_closed_form_and_peaks_at_the_optimum(genuine):
    """The baseline the deviations depart from: residual at float noise, and the peak where it belongs."""
    assert [record["iteration"] for record in genuine] == list(range(0, 9))
    for record in genuine:
        assert record["theoretical_p_success"] == pytest.approx(
            _closed_form(record["iteration"]), abs=1e-12
        )
    summary = fit_residuals(genuine)
    assert summary["max_abs_residual"] < 1e-12
    assert summary["peak_iteration_measured"] == summary["peak_iteration_closed_form"] == 6
    assert summary["peak_iteration_agrees"] is True


# -----------------------------------------------------------------------------------------------
# a table small enough to check on paper
# -----------------------------------------------------------------------------------------------


def test_a_hand_sized_deviation_gives_the_hand_computed_summary():
    """Residuals ``0.1, -0.2, -0.4, 0.2``: max 0.4, mean -0.075, rms sqrt(0.25 / 4) = 0.25."""
    closed_form = [0.0, 0.5, 1.0, 0.5]
    measured = [0.1, 0.3, 0.6, 0.7]
    records = [
        {"iteration": k, "empirical_p_success": m, "theoretical_p_success": t}
        for k, (m, t) in enumerate(zip(measured, closed_form))
    ]
    summary = fit_residuals(records)
    assert summary["n_points"] == 4
    assert summary["max_abs_residual"] == pytest.approx(0.4, abs=1e-15)
    assert summary["mean_residual"] == pytest.approx(-0.075, abs=1e-15)
    assert summary["rms_residual"] == pytest.approx(0.25, abs=1e-15)
    # The measured curve keeps rising after the closed form has turned over.
    assert summary["peak_iteration_measured"] == 3
    assert summary["peak_iteration_closed_form"] == 2
    assert summary["peak_p_measured"] == pytest.approx(0.7)
    assert summary["peak_p_closed_form"] == pytest.approx(1.0)
    assert summary["peak_iteration_agrees"] is False


def test_the_sign_of_the_mean_residual_is_measured_minus_closed_form():
    """A curve that undershoots everywhere has a negative mean, not merely a large one."""
    records = [
        {"iteration": k, "empirical_p_success": 0.25, "theoretical_p_success": 0.75}
        for k in range(3)
    ]
    summary = fit_residuals(records)
    assert summary["mean_residual"] == pytest.approx(-0.5)
    assert summary["max_abs_residual"] == pytest.approx(0.5)
    assert summary["rms_residual"] == pytest.approx(0.5)


# -----------------------------------------------------------------------------------------------
# deviations of a real curve
# -----------------------------------------------------------------------------------------------


def test_a_damped_curve_is_reported_at_the_size_of_its_damping(genuine):
    """``p_k * exp(-k/10)``: the loss grows with ``k``, and the summary reports exactly that loss."""
    rate = 0.1
    damped = [_closed_form(k) * math.exp(-rate * k) for k in range(len(genuine))]
    summary = fit_residuals(_with_measured(genuine, damped))

    losses = [_closed_form(k) * (1.0 - math.exp(-rate * k)) for k in range(len(genuine))]
    assert summary["max_abs_residual"] == pytest.approx(max(losses), abs=1e-12)
    assert summary["mean_residual"] == pytest.approx(-sum(losses) / len(losses), abs=1e-12)
    assert summary["rms_residual"] == pytest.approx(
        math.sqrt(sum(loss * loss for loss in losses) / len(losses)), abs=1e-12
    )
    # The largest loss is one round *past* the peak, where the damping has had longer to act than
    # the closed form has had to fall: sin^2(15 theta) * (1 - e^-0.7) = 0.9074 * 0.5034.
    assert summary["max_abs_residual"] == pytest.approx(
        _closed_form(7) * (1.0 - math.exp(-0.7)), abs=1e-12
    )
    assert summary["max_abs_residual"] == pytest.approx(0.4568, abs=5e-5)
    assert 0.4 < summary["max_abs_residual"] < 0.5
    assert summary["mean_residual"] < -0.1, "a damped curve undershoots; the mean must say which way"
    assert summary["peak_p_measured"] < summary["peak_p_closed_form"] - 0.4


def test_a_shifted_peak_is_reported_as_a_disagreement(genuine):
    """The curve one round early — what an off-by-one in the round count measures."""
    shifted = [_closed_form(k + 1) for k in range(len(genuine))]
    summary = fit_residuals(_with_measured(genuine, shifted))

    assert summary["peak_iteration_closed_form"] == 6
    assert summary["peak_iteration_measured"] == 5
    assert summary["peak_iteration_agrees"] is False
    gaps = [_closed_form(k + 1) - _closed_form(k) for k in range(len(genuine))]
    assert summary["max_abs_residual"] == pytest.approx(max(abs(gap) for gap in gaps), abs=1e-12)
    assert summary["max_abs_residual"] > 0.2, "one round of a 64-state search moves p by a fifth"
    # The mean telescopes: (p_9 - p_0) / 9, which is small while the rms is not — the reason a
    # summary that reported only the mean would have averaged this deviation away.
    assert summary["mean_residual"] == pytest.approx(
        (_closed_form(9) - _closed_form(0)) / 9, abs=1e-12
    )
    assert abs(summary["mean_residual"]) < 0.1 < summary["rms_residual"]


def test_a_constant_curve_is_nowhere_near_the_closed_form(genuine):
    """An oracle that amplifies nothing: ``p = M/N`` at every ``k``."""
    flat = [1.0 / 64.0] * len(genuine)
    summary = fit_residuals(_with_measured(genuine, flat))

    theory = [_closed_form(k) for k in range(len(genuine))]
    assert summary["max_abs_residual"] == pytest.approx(max(theory) - 1.0 / 64.0, abs=1e-12)
    assert summary["max_abs_residual"] > 0.98
    assert summary["mean_residual"] == pytest.approx(1.0 / 64.0 - sum(theory) / len(theory), abs=1e-12)
    assert summary["rms_residual"] > 0.5
    # A flat curve has no peak; the first maximum is k = 0, and that is not the optimum.
    assert summary["peak_iteration_measured"] == 0
    assert summary["peak_p_measured"] == pytest.approx(1.0 / 64.0)
    assert summary["peak_iteration_agrees"] is False


def test_a_uniform_offset_keeps_the_peak_and_is_visible_only_in_the_magnitudes(genuine):
    """``1e-3`` added everywhere — the docstring's own example of "a bug or a finding".

    The peak flag cannot see this deviation, which is why the magnitudes are reported beside it: all
    three are exactly the offset, six orders of magnitude above the float noise of the genuine curve.
    """
    offset = 1e-3
    lifted = [record["empirical_p_success"] + offset for record in genuine]
    summary = fit_residuals(_with_measured(genuine, lifted))
    assert summary["peak_iteration_agrees"] is True
    assert summary["max_abs_residual"] == pytest.approx(offset, rel=1e-9)
    assert summary["mean_residual"] == pytest.approx(offset, rel=1e-9)
    assert summary["rms_residual"] == pytest.approx(offset, rel=1e-9)
    assert summary["max_abs_residual"] > 1e9 * fit_residuals(genuine)["max_abs_residual"]


def test_a_deviating_curve_does_not_change_the_closed_form_column(genuine):
    """The summary reads each column once: bending the measured one leaves the closed form's peak."""
    flat = [0.5] * len(genuine)
    summary = fit_residuals(_with_measured(genuine, flat))
    assert summary["peak_p_closed_form"] == pytest.approx(_closed_form(6), abs=1e-12)
    assert summary["peak_iteration_closed_form"] == 6
    assert summary["provenance"].startswith("fit")


# -----------------------------------------------------------------------------------------------
# the converse: a genuine sampled curve is inside its own sampling noise
# -----------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sampled_records(spec, backend) -> list[dict]:
    """The genuine curve as a finite-shots experiment would see it: the sampled estimator as ``p``."""
    curve = success_curve(spec, backend, shots=SHOTS, seed_parts=("fit-residuals-deviation",))
    records = curve.records
    assert all(record["shots"] == SHOTS for record in records)
    return _with_measured(records, [record["sampled_p_success"] for record in records])


def test_a_sampled_genuine_curve_stays_within_binomial_noise(sampled_records):
    """Point by point within ``5 sigma`` of ``sqrt(p(1-p)/shots)``, and not identically zero.

    One count of slack is allowed on top, because where ``p`` is within ``1/shots`` of 0 or 1 the
    binomial standard deviation understates the granularity of a count.
    """
    residuals = []
    for record in sampled_records:
        p = record["theoretical_p_success"]
        residual = record["empirical_p_success"] - p
        assert abs(residual) <= SIGMAS * _binomial_sigma(p, SHOTS) + 1.0 / SHOTS, record
        residuals.append(residual)
    assert any(residual != 0.0 for residual in residuals), "the sampled column was never sampled"

    summary = fit_residuals(sampled_records)
    worst_sigma = 0.5 / math.sqrt(SHOTS)
    assert 0.0 < summary["max_abs_residual"] <= SIGMAS * worst_sigma
    assert summary["max_abs_residual"] == pytest.approx(max(abs(r) for r in residuals), abs=1e-15)
    assert summary["rms_residual"] <= 2.0 * worst_sigma
    # The mean of independent binomial errors is tighter than any one of them.
    pooled = math.sqrt(
        sum(_binomial_sigma(r["theoretical_p_success"], SHOTS) ** 2 for r in sampled_records)
    ) / len(sampled_records)
    assert abs(summary["mean_residual"]) <= SIGMAS * pooled


def test_sampling_noise_does_not_move_the_peak_at_this_shot_count(sampled_records):
    """``p_6 - p_5`` is 0.033, over twenty standard deviations of the difference at 20000 shots."""
    spread = math.hypot(
        _binomial_sigma(_closed_form(5), SHOTS), _binomial_sigma(_closed_form(6), SHOTS)
    )
    assert _closed_form(6) - _closed_form(5) > 20 * spread
    assert fit_residuals(sampled_records)["peak_iteration_agrees"] is True


def test_the_deviations_above_are_far_outside_the_sampling_noise_of_a_genuine_curve(
    genuine, sampled_records
):
    """What separates a finding from noise is a ratio, and here it is two orders of magnitude.

    This is the comparison a significance flag would make. The summary supplies the numerator and
    the shot count supplies the denominator; the test makes it by hand because the summary does not.
    """
    noise = fit_residuals(sampled_records)["rms_residual"]
    damped = [_closed_form(k) * math.exp(-0.1 * k) for k in range(len(genuine))]
    shifted = [_closed_form(k + 1) for k in range(len(genuine))]
    for deviating in (damped, shifted, [1.0 / 64.0] * len(genuine)):
        summary = fit_residuals(_with_measured(genuine, deviating))
        assert summary["rms_residual"] > 50 * noise
        # And against the a-priori bound rather than the observed noise: no binomial point at this
        # shot count can sit further than 5 * 0.5 / sqrt(shots) out, and these sit ten times that.
        assert summary["max_abs_residual"] > 10 * SIGMAS * 0.5 / math.sqrt(SHOTS)


def test_a_statistically_significant_deviation_is_flagged_by_the_summary(sampled_records):
    """A damped sampled curve, 100 sigma off at the peak, must come back marked as significant.

    The records carry everything a flag needs — the measured value, the closed form and the shot
    count — so the summary has no missing input to blame. The assertion is deliberately loose about
    the key's spelling and strict about its existence and its value.
    """
    damped = [
        record["empirical_p_success"] * math.exp(-0.1 * record["iteration"])
        for record in sampled_records
    ]
    summary = fit_residuals(_with_measured(sampled_records, damped))
    flags = {
        key: value
        for key, value in summary.items()
        if "signific" in key.lower() or "flag" in key.lower()
    }
    assert flags, f"no significance flag among {sorted(summary)}"
    assert any(value is True for value in flags.values())
    quiet = fit_residuals(sampled_records)
    assert not any(quiet[key] is True for key in flags), "the flag fired on sampling noise"
