"""The small public functions nothing else calls from a test.

Each of these is on a path the pipeline runs on every experiment — the dual half of the comparison,
the anomaly text that reaches section 6, the frame the scaling fit consumes, the seed override, the
GSA reference norm, the probe's printed report — and each had no test. None is complicated. That is
the reason to pin them: a function this small is changed without a second look, and the first thing
to notice would otherwise be a report that reads differently.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from qlwr_lattice_stress.analysis.empirical_vs_theoretical import (
    FAMILY_DUAL,
    FAMILY_PRIMAL,
    AnomalySummary,
    compare_block_sizes,
    summarise_anomalies,
)
from qlwr_lattice_stress.analysis.hermite_factor import delta_from_block_size, gsa_predicted_norm
from qlwr_lattice_stress.analysis.scaling_extrapolation import (
    fit_core_svp_model,
    measurements_to_frame,
)
from qlwr_lattice_stress.protocols import (
    EXTRAPOLATED,
    MEASURED,
    NOT_RUN,
    SAME_SCALE,
    DualAttackResult,
    EstimatorReport,
    PrimalAttackResult,
)
from qlwr_lattice_stress.utils.api_probe import (
    Check,
    format_report,
    optional_absences,
    required_failures,
)
from qlwr_lattice_stress.utils.seeding import root_from_environment


def report(beta_usvp=None, beta_dual=None) -> EstimatorReport:
    return EstimatorReport(
        beta_usvp=beta_usvp, beta_dual=beta_dual,
        rop_usvp_log2=None, rop_dual_log2=None,
        rop_classical_log2_min=None, rop_quantum_log2_min=None,
        minimum_over_models="primal_usvp", provenance=SAME_SCALE,
    )


# ---------------------------------------------------------------------------------------------
# the dual half of the comparison
# ---------------------------------------------------------------------------------------------


def test_the_dual_family_is_compared_against_the_dual_prediction():
    """The two predictions are set far apart so that reading the wrong field cannot pass: against
    the primal 30 a measured 100 is a 233% anomaly, against the dual 100 it is exact agreement."""
    both = report(beta_usvp=30, beta_dual=100)

    dual = compare_block_sizes(
        dimension=44, measured_min_block_size=100, report=both, family=FAMILY_DUAL
    )
    assert dual.predicted_min_block_size == 100
    assert dual.discrepancy == 0.0
    assert dual.anomaly is None

    primal = compare_block_sizes(
        dimension=77, measured_min_block_size=100, report=both, family=FAMILY_PRIMAL
    )
    assert primal.predicted_min_block_size == 30
    assert primal.anomaly is not None


def test_a_dual_disagreement_names_the_dual_family_and_its_direction():
    result = compare_block_sizes(
        dimension=44, measured_min_block_size=20, report=report(beta_usvp=20, beta_dual=40),
        family=FAMILY_DUAL,
    )
    assert result.discrepancy == pytest.approx(-0.5)
    assert "the dual attack needed block size 20" in result.anomaly
    assert "predicts 40" in result.anomaly
    assert "50% below the prediction" in result.anomaly
    assert "25% tolerance" in result.anomaly
    assert "primal_usvp" not in result.anomaly


def test_a_missing_dual_prediction_is_an_absence_even_when_the_primal_one_exists():
    """The M7 asymmetry: the primal model applies and the dual one does not. The dual comparison
    must say "nothing to compare", not borrow the primal number and not invent a discrepancy."""
    result = compare_block_sizes(
        dimension=44, measured_min_block_size=None, report=report(beta_usvp=30, beta_dual=None),
        family=FAMILY_DUAL,
    )
    assert result.anomaly is None
    assert result.discrepancy == 0.0
    assert result.predicted_min_block_size == 0
    assert result.measured_min_block_size == 0
    assert "no block size for the dual family" in result.note
    assert "absence of a prediction rather than agreement" in result.note


def test_a_dual_sweep_that_recovered_nothing_is_named_as_dual():
    result = compare_block_sizes(
        dimension=44, measured_min_block_size=None, report=report(beta_dual=35), family=FAMILY_DUAL
    )
    assert result.discrepancy == 35.0
    assert "the dual attack recovered nothing" in result.anomaly
    assert "predicts success at 35" in result.anomaly


def test_an_unknown_family_is_refused():
    with pytest.raises(ValueError, match="unknown attack family 'hybrid'"):
        compare_block_sizes(
            dimension=44, measured_min_block_size=30, report=report(beta_usvp=30), family="hybrid"
        )


def test_the_tolerance_is_a_parameter_and_the_note_is_carried():
    """30 against 40 is 25% below — inside the default tolerance, outside a 10% one. The extra note
    travels with an agreement and turns it into a stated non-comparison in the summary."""
    common = dict(dimension=44, measured_min_block_size=30, report=report(beta_dual=40),
                  family=FAMILY_DUAL)
    assert compare_block_sizes(**common).anomaly is None
    strict = compare_block_sizes(**common, tolerance_fraction=0.10)
    assert strict.tolerance == 0.10
    assert "outside the 10% tolerance" in strict.anomaly

    noted = compare_block_sizes(**common, extra_note="single draw at four threads")
    assert noted.note == "single draw at four threads"
    assert summarise_anomalies([noted]).not_compared == (
        "dimension 44: single draw at four threads",
    )


# ---------------------------------------------------------------------------------------------
# the anomaly summary's text — what section 6 prints
# ---------------------------------------------------------------------------------------------


def test_an_agreement_is_described_as_agreement_and_nothing_else():
    summary = summarise_anomalies([
        compare_block_sizes(dimension=77, measured_min_block_size=30, report=report(beta_usvp=30)),
        compare_block_sizes(dimension=98, measured_min_block_size=41, report=report(beta_usvp=40)),
    ])
    assert not summary.has_anomalies
    assert summary.describe() == "no anomalies: every comparison that ran agreed within tolerance"


def test_an_anomaly_is_described_with_its_count_its_dimension_and_its_text():
    anomalous = compare_block_sizes(
        dimension=48, measured_min_block_size=90, report=report(beta_usvp=30)
    )
    absent = compare_block_sizes(
        dimension=44, measured_min_block_size=30, report=report(beta_dual=None), family=FAMILY_DUAL
    )
    agreeing = compare_block_sizes(
        dimension=77, measured_min_block_size=30, report=report(beta_usvp=30)
    )
    summary = summarise_anomalies([anomalous, absent, agreeing])
    lines = summary.describe().split("\n")

    assert summary.has_anomalies
    assert lines[0] == "1 anomaly(ies):"
    assert lines[1] == f"  - dimension 48: {anomalous.anomaly}"
    assert "200% above the prediction" in lines[1]
    assert lines[2] == "1 comparison(s) not made:"
    assert lines[3] == f"  - dimension 44: {absent.note}"
    assert len(lines) == 4, "the agreeing comparison contributes no line"
    assert "no anomalies" not in summary.describe()


def test_a_summary_with_only_non_comparisons_still_says_there_were_no_anomalies():
    summary = AnomalySummary(anomalies=(), not_compared=("dimension 44: no dual prediction",))
    assert summary.describe().split("\n") == [
        "no anomalies: every comparison that ran agreed within tolerance",
        "1 comparison(s) not made:",
        "  - dimension 44: no dual prediction",
    ]


def test_several_anomalies_are_counted_and_kept_in_order():
    summary = AnomalySummary(anomalies=("first", "second", "third"), not_compared=())
    assert summary.describe().split("\n") == ["3 anomaly(ies):", "  - first", "  - second", "  - third"]


# ---------------------------------------------------------------------------------------------
# the frame the scaling fit consumes
# ---------------------------------------------------------------------------------------------


def _point(block_size, wall, *, provenance=MEASURED, dimension=77, recovered=False):
    return PrimalAttackResult(
        dimension=dimension, block_size=block_size, recovered=recovered, wall_clock_s=wall,
        provenance=provenance,
        not_run_reason="projected over the limit" if provenance == NOT_RUN else None,
    )


def test_the_frame_has_the_columns_and_types_the_fit_reads():
    frame = measurements_to_frame([_point(20, 0.5), _point(30, 4.0), _point(40, 32.0)])

    assert list(frame.columns) == ["block_size", "wall_clock_s", "log2_cost", "dimension"]
    assert frame["block_size"].dtype == np.int64
    assert frame["dimension"].dtype == np.int64
    assert frame["wall_clock_s"].dtype == np.float64
    assert frame["log2_cost"].dtype == np.float64
    assert frame["block_size"].tolist() == [20, 30, 40]
    assert frame["wall_clock_s"].tolist() == [0.5, 4.0, 32.0]
    assert frame["log2_cost"].tolist() == [-1.0, 2.0, 5.0]
    assert frame["dimension"].tolist() == [77, 77, 77]


def test_only_measured_points_reach_the_frame():
    """Provenance is a *filter* here, not a column: the frame carries no provenance field because
    every row in it is measured by construction. A refusal has no cost to fit — its wall-clock is a
    zero that would drag the slope — and neither has anything labelled theoretical or extrapolated.
    """
    measurements = [
        _point(10, 0.25),
        _point(20, 0.0, provenance=NOT_RUN),
        _point(30, 2.0, provenance=NOT_RUN),      # a refusal that somehow carries a time
        _point(40, 8.0, provenance=EXTRAPOLATED),
        _point(50, 16.0, provenance=SAME_SCALE),
        _point(60, 0.0),                            # measured, but no clock: log2 is undefined
        _point(70, -1.0),
        DualAttackResult(dimension=44, block_size=80, advantage=0.9, control_advantage=0.0,
                         wall_clock_s=64.0),
    ]
    frame = measurements_to_frame(measurements)

    assert "provenance" not in frame.columns
    assert frame["block_size"].tolist() == [10, 80]
    assert frame["log2_cost"].tolist() == [-2.0, 6.0]
    assert frame["dimension"].tolist() == [77, 44]
    assert np.isfinite(frame["log2_cost"]).all()


def test_nothing_measured_gives_an_empty_frame_with_the_same_columns():
    frame = measurements_to_frame([_point(20, 0.0, provenance=NOT_RUN)])
    assert len(frame) == 0
    assert list(frame.columns) == ["block_size", "wall_clock_s", "log2_cost", "dimension"]
    assert list(measurements_to_frame([]).columns) == list(frame.columns)


def test_the_frame_feeds_the_fit_and_the_fit_is_labelled_measured():
    """End to end through the two functions: wall-clocks of exactly ``2^(0.3 * beta - 4)`` must come
    back as a slope of 0.3, over the measured block sizes only."""
    measurements = [_point(beta, 2.0 ** (0.3 * beta - 4.0)) for beta in (20, 30, 40, 50)]
    measurements.insert(2, _point(35, 0.0, provenance=NOT_RUN))

    fitted = fit_core_svp_model(measurements_to_frame(measurements))
    model = fitted.model

    assert [beta for beta, _ in fitted.points] == [20, 30, 40, 50], "the refusal was fitted"
    assert fitted.predict_log2_cost(40)[1] == MEASURED
    assert fitted.predict_log2_cost(400)[1] == EXTRAPOLATED
    assert model.c == pytest.approx(0.3, abs=1e-9)
    assert model.intercept == pytest.approx(-4.0, abs=1e-7)
    assert (model.fitted_beta_min, model.fitted_beta_max, model.n_points) == (20, 50, 4)
    assert model.provenance == MEASURED


# ---------------------------------------------------------------------------------------------
# the GSA reference norm
# ---------------------------------------------------------------------------------------------


def _delta_by_hand(beta: int) -> float:
    """``(beta/(2 pi e) * (pi beta)^(1/beta)) ^ (1/(2(beta-1)))``, written out independently."""
    inner = beta / (2.0 * math.pi * math.e) * (math.pi * beta) ** (1.0 / beta)
    return inner ** (1.0 / (2.0 * (beta - 1)))


def test_the_gsa_norm_matches_a_hand_computed_value():
    """``16 * I_4`` has determinant ``16^4``, so ``det^(1/d) = 16`` exactly and the prediction is
    ``delta^4 * 16``. At block size 40, ``delta = 1.0125375`` (worked by hand: ``40/(2 pi e) =
    2.34199``, ``(40 pi)^(1/40) = 1.128445``, product ``2.642810``, 78th root ``1.0125375``), and
    ``1.0125375^4 * 16 = 16.81761``."""
    basis = [[16, 0, 0, 0], [0, 16, 0, 0], [0, 0, 16, 0], [0, 0, 0, 16]]
    predicted = gsa_predicted_norm(basis, 40)

    assert predicted == pytest.approx(16.81761, abs=1e-4)
    assert predicted == pytest.approx(_delta_by_hand(40) ** 4 * 16.0, rel=1e-9)
    assert float(delta_from_block_size(40)) == pytest.approx(1.0125375, abs=1e-6)


def test_the_gsa_norm_uses_the_determinant_and_not_the_rows():
    """A non-diagonal basis with determinant 5: the prediction is ``delta^2 * sqrt(5)`` whatever the
    rows look like, and a unimodular change of basis must not move it."""
    basis = [[2, 1], [1, 3]]
    same_lattice = [[2, 1], [3, 4]]  # second row plus the first; determinant still 5

    expected = _delta_by_hand(60) ** 2 * math.sqrt(5.0)
    assert gsa_predicted_norm(basis, 60) == pytest.approx(expected, rel=1e-9)
    assert gsa_predicted_norm(basis, 60) == pytest.approx(2.2875811, abs=1e-6)
    assert gsa_predicted_norm(same_lattice, 60) == pytest.approx(expected, rel=1e-9)


def test_the_gsa_norm_falls_as_the_block_size_rises_and_accepts_an_fpylll_matrix():
    from fpylll import IntegerMatrix

    matrix = IntegerMatrix.from_matrix([[7, 0, 0], [0, 7, 0], [3, 5, 7]])
    norms = [gsa_predicted_norm(matrix, beta) for beta in (40, 60, 100, 200)]
    assert norms == sorted(norms, reverse=True)
    assert all(n > 7.0 for n in norms), "delta > 1, so the prediction sits above det^(1/d) = 7"
    assert norms[0] == pytest.approx(_delta_by_hand(40) ** 3 * 7.0, rel=1e-9)


# ---------------------------------------------------------------------------------------------
# the seed override
# ---------------------------------------------------------------------------------------------


def test_without_the_variable_the_configured_seed_is_used(monkeypatch):
    monkeypatch.delenv("QLS_SEED", raising=False)
    assert root_from_environment(20260913) == 20260913
    assert root_from_environment(0) == 0


def test_the_variable_overrides_the_configured_seed(monkeypatch):
    monkeypatch.setenv("QLS_SEED", "4242")
    assert root_from_environment(1) == 4242
    assert isinstance(root_from_environment(1), int)

    monkeypatch.setenv("QLS_SEED", "0")
    assert root_from_environment(7) == 0, "zero is a seed, not an unset variable"

    monkeypatch.setenv("QLS_SEED", " -12 ")
    assert root_from_environment(7) == -12


@pytest.mark.parametrize("raw", ["seven", "1.5", "0x10", ""])
def test_a_variable_that_is_not_an_integer_is_refused_by_name(monkeypatch, raw):
    """Falling back to the default here would replay a *different* run while reporting success —
    the opposite of what the variable is for."""
    monkeypatch.setenv("QLS_SEED", raw)
    with pytest.raises(ValueError, match="QLS_SEED=.* is not an integer") as excinfo:
        root_from_environment(1)
    assert repr(raw) in str(excinfo.value)


# ---------------------------------------------------------------------------------------------
# the probe's printed report
# ---------------------------------------------------------------------------------------------


def _checks() -> list[Check]:
    return [
        Check("fpylll imports", True, "fpylll 0.6.1"),
        Check("LLL runs", True),
        Check("estimator imports", False, "ImportError: no estimator", required=True),
        Check("g6k imports", False, "ModuleNotFoundError: no g6k", required=False),
    ]


def test_each_check_line_carries_its_mark_and_its_detail():
    ok, bare, failed, absent = _checks()
    assert ok.line() == "[ok  ] fpylll imports -- fpylll 0.6.1"
    assert bare.line() == "[ok  ] LLL runs"
    assert failed.line() == "[FAIL] estimator imports -- ImportError: no estimator"
    assert absent.line() == "[none] g6k imports -- ModuleNotFoundError: no g6k"


def test_the_report_separates_required_failures_from_optional_absences():
    checks = _checks()
    text = format_report(checks)
    lines = text.split("\n")

    assert " qlwr-lattice-stress: API probe" in lines
    for check in checks:
        assert check.line() in lines
    assert "  4 checks, 1 required failures, 1 optional absences" in lines

    optional_at = lines.index(
        "  Optional components absent (the pipeline must still run without them):"
    )
    required_at = lines.index("  REQUIRED FAILURES -- nothing may be built on these:")
    assert lines[optional_at + 1] == "    - g6k imports: ModuleNotFoundError: no g6k"
    assert lines[required_at + 1] == "    - estimator imports: ImportError: no estimator"
    assert optional_at < required_at

    # An optional absence is not a failure, and a required failure is not an absence.
    assert [c.name for c in required_failures(checks)] == ["estimator imports"]
    assert [c.name for c in optional_absences(checks)] == ["g6k imports"]
    assert "    - g6k imports: ModuleNotFoundError: no g6k" not in lines[required_at:]


def test_a_clean_probe_prints_neither_section():
    text = format_report([Check("fpylll imports", True, "ok"), Check("g6k imports", True, required=False)])
    assert "  2 checks, 0 required failures, 0 optional absences" in text.split("\n")
    assert "REQUIRED FAILURES" not in text
    assert "Optional components absent" not in text
    assert "[FAIL]" not in text and "[none]" not in text
