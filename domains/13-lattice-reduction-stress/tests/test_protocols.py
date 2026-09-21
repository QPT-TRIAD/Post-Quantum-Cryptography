"""The frozen result types: the invariants that make the boundaries safe.

These are not decoration. Each guard below encodes a failure that the sibling Grover project's
integration pass actually hit, or that its design anticipated:

* a skipped run and a run that was never attempted are indistinguishable in a results file that
  records only successes, so ``not_run`` must carry its reason;
* a comparison that reports agreement while the numbers disagree is worse than one that reports
  nothing, so ``ComparisonResult`` may not fall silent off-tolerance;
* the project's central claim is a comparison between measured and theoretical numbers, and its
  central hazard is presenting extrapolated ones as measured -- so provenance is part of the type
  rather than a convention in the reporting layer.
"""

from __future__ import annotations

import pytest

from qlwr_lattice_stress.protocols import (
    EXTRAPOLATED,
    MEASURED,
    NOT_RUN,
    PROVENANCE_LABELS,
    SAME_SCALE,
    ComparisonResult,
    ReducedBasisResult,
    ScalingModel,
)


def test_the_four_provenances_are_the_only_ones():
    """A fifth provenance would silently escape the report's labelling, so the set is fixed."""
    assert set(PROVENANCE_LABELS) == {MEASURED, SAME_SCALE, EXTRAPOLATED, NOT_RUN}


def test_every_provenance_has_a_distinct_label():
    """Two provenances rendering under the same heading is exactly how measured and extrapolated
    numbers get blended in a report without anyone editing a line of code."""
    labels = list(PROVENANCE_LABELS.values())
    assert len(labels) == len(set(labels))


def test_the_extrapolated_label_says_it_is_not_measured():
    assert "not measured" in PROVENANCE_LABELS[EXTRAPOLATED]


def test_a_not_run_result_must_carry_its_reason():
    with pytest.raises(ValueError, match="not_run result must carry its reason"):
        ReducedBasisResult(
            basis=None, block_size=40, wall_clock_s=0.0, root_hermite_factor=None,
            engine="g6k", engine_version="x", threads=2, provenance=NOT_RUN,
        )


def test_a_not_run_result_with_a_reason_is_accepted():
    """The refusal path has to be usable, or callers will report refusals as successes."""
    r = ReducedBasisResult(
        basis=None, block_size=100, wall_clock_s=0.0, root_hermite_factor=None,
        engine="g6k", engine_version="x", threads=2, provenance=NOT_RUN,
        not_run_reason="predicted 9.8 GiB exceeds the 6.0 GiB budget",
    )
    assert r.provenance == NOT_RUN and "GiB" in r.not_run_reason


def test_a_comparison_off_tolerance_must_name_an_anomaly():
    """The sibling project's rule, restated as a constructor guard: silence is the failure."""
    with pytest.raises(ValueError, match="must be named as an anomaly"):
        ComparisonResult(
            dimension=60, measured_min_block_size=30, predicted_min_block_size=20,
            discrepancy=10.0, tolerance=2.0,
        )


def test_a_comparison_within_tolerance_may_not_also_claim_an_anomaly():
    """The converse, so that 'agreement' and 'anomaly' cannot both be true and leave a reader to
    guess which one the report meant."""
    with pytest.raises(ValueError, match="must not also report an anomaly"):
        ComparisonResult(
            dimension=60, measured_min_block_size=30, predicted_min_block_size=30,
            discrepancy=0.0, tolerance=2.0, anomaly="something looks off",
        )


def test_a_clean_agreement_is_representable():
    c = ComparisonResult(
        dimension=60, measured_min_block_size=30, predicted_min_block_size=29,
        discrepancy=1.0, tolerance=2.0,
    )
    assert c.anomaly is None


def test_a_named_anomaly_is_representable():
    c = ComparisonResult(
        dimension=60, measured_min_block_size=45, predicted_min_block_size=25,
        discrepancy=20.0, tolerance=2.0,
        anomaly="measured block size far above prediction; check the embedding factor first",
    )
    assert "embedding factor" in c.anomaly


def test_scaling_model_requires_the_fitted_domain_to_be_stated():
    """Core-SVP models sieving cost and says nothing about the enumeration regime, so the domain
    is a claim about validity rather than documentation."""
    m = ScalingModel(
        c=0.292, intercept=1.0, r_squared=0.999, fitted_beta_min=40, fitted_beta_max=80,
        n_points=5, extrapolates_outside_fitted_domain=False,
    )
    assert m.fitted_beta_min == 40 and not m.extrapolates_outside_fitted_domain


def test_results_are_frozen():
    """Frozen so a downstream layer cannot adjust a number on its way into a report."""
    r = ReducedBasisResult(
        basis=None, block_size=40, wall_clock_s=1.0, root_hermite_factor=1.005,
        engine="fpylll_bkz", engine_version="0.6.4", threads=2,
    )
    with pytest.raises(Exception):
        r.block_size = 50  # type: ignore[misc]
