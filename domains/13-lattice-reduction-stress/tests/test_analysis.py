"""The analysis layer: the two routes to a quality metric, the comparison, and the fit.

Two things here are cross-checks from the project's battery rather than ordinary tests.

**Cross-check 5** computes the root-Hermite factor two ways — an exact integer determinant, and
``fpylll``'s Gram-Schmidt data — and requires them to agree. That is what caught a real defect:
``get_r(i, i)`` returns the *squared* norm of a Gram-Schmidt vector, so ``prod(r_ii)`` is the
determinant squared, and the resulting factor was still plausible-looking in isolation. Only the
disagreement between the routes revealed it. Measured agreement is now 1e-14 relative or better.

**Cross-check 2's sibling** here is the comparison: a discrepancy outside tolerance must be *named*.
The type refuses to hold a silent disagreement, so the test is that the refusal fires.
"""

from __future__ import annotations

import math
import random

import numpy as np
import pandas as pd
import pytest
from fpylll import LLL

from qlwr_lattice_stress.analysis.empirical_vs_theoretical import (
    FAMILY_PRIMAL,
    compare_block_sizes,
    summarise_anomalies,
)
from qlwr_lattice_stress.analysis.hermite_factor import (
    achieved_root_hermite_factor,
    delta_from_block_size,
    gsa_predicted_norm,
    hermite_factor_from_gso,
)
from qlwr_lattice_stress.analysis.scaling_extrapolation import (
    InsufficientPoints,
    fit_core_svp_model,
    predict_log2_cost,
)
from qlwr_lattice_stress.lattice.basis_construction import build_primal_embedding_basis
from qlwr_lattice_stress.problem.normal_form import to_normal_form
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)
from qlwr_lattice_stress.protocols import (
    EXTRAPOLATED,
    MEASURED,
    SAME_SCALE,
    EstimatorReport,
)

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8


def reduced_basis(nu=20, m=48, seed=1):
    rng = random.Random(seed)
    while True:
        base = tuple(tuple(rng.randrange(PRODUCTION_Q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], PRODUCTION_Q, nu) == nu:
            break
    instance = LatticeQLWRInstance(
        nu=nu, q_l=PRODUCTION_Q, p=PRODUCTION_P, m=m,
        secret_s=tuple(rng.randrange(PRODUCTION_Q) for _ in range(nu)), base=base, seed=seed,
    )
    basis = build_primal_embedding_basis(to_normal_form(instance), embedding_factor=3)
    LLL.reduction(basis)
    return basis


def report(beta_usvp=None, beta_dual=None) -> EstimatorReport:
    return EstimatorReport(
        beta_usvp=beta_usvp, beta_dual=beta_dual,
        rop_usvp_log2=None, rop_dual_log2=None,
        rop_classical_log2_min=None, rop_quantum_log2_min=None,
        minimum_over_models="primal_usvp", provenance=SAME_SCALE,
    )


# ---------------------------------------------------------------------------------------------
# cross-check 5
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("nu,m", [(8, 20), (20, 48), (32, 76)])
def test_the_two_hermite_routes_agree(nu, m):
    """Cross-check 5. Exact integer determinant against ``fpylll``'s Gram-Schmidt data.

    The routes fail for different reasons and neither is wrong alone, which is why both are
    computed. The tolerance is the plan's 1e-9 and the measured agreement is far tighter; the point
    of the check is the *class* of bug it catches, not the digits.
    """
    basis = reduced_basis(nu=nu, m=m)
    exact = achieved_root_hermite_factor(basis)
    via_gso = hermite_factor_from_gso(basis)
    assert exact == pytest.approx(via_gso, rel=1e-9), (
        f"the exact route gives {exact!r} and the GSO route {via_gso!r}. A disagreement means one "
        "of them is computing a different volume — the GSO diagonal holds squared norms."
    )


def test_the_hermite_factor_can_fall_below_one_which_is_the_point():
    """``delta < 1`` is **expected here**, and is a signature of the planted vector.

    The achieved factor is ``(||b1|| / det^(1/d))^(1/d)``. The bound ``delta >= 1`` applies to a
    *generic* lattice; a lattice containing an anomalously short vector — which is exactly what a
    uSVP instance is, by construction — gives a value below 1 whenever reduction finds it.

    Measured at `nu = 20, m = 48`: ``0.9980``, against ``1.0176`` at `nu = 32`. My first version of
    this test asserted ``>= 1.0`` on the reasoning that a quality metric cannot be better than
    perfect. That reasoning is right for a random lattice and wrong for this one, and the failure was
    informative rather than a defect.
    """
    factor = achieved_root_hermite_factor(reduced_basis())
    assert 0.0 < factor < 2.0, factor  # finite and of a plausible magnitude
    # It is computable for the calibrated instance and sits near 1, which is what a basis with a
    # planted vector and a nearby generic shortest vector both look like.
    assert factor == pytest.approx(1.0, abs=0.05)


def test_a_singular_basis_is_refused():
    from fpylll import IntegerMatrix

    singular = IntegerMatrix(2, 2, int_type="mpz")
    singular[0, 0] = 1
    singular[1, 0] = 2
    with pytest.raises(ValueError):
        achieved_root_hermite_factor(singular)


# ---------------------------------------------------------------------------------------------
# the GSA prediction, and its domain
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("beta,expected", [(40, 1.0125), (100, 1.00926)])
def test_gsa_matches_the_literature_where_it_is_valid(beta, expected):
    assert float(delta_from_block_size(beta)) == pytest.approx(expected, abs=5e-5)


@pytest.mark.parametrize("beta", [2, 10, 20, 39])
def test_gsa_is_refused_below_its_domain(beta):
    """The formula returns a value below 1 for small block sizes — 0.54 at beta=2 — which is not a
    prediction but the formula leaving the regime it was derived for. Clamping would disguise that;
    raising says so."""
    with pytest.raises(ValueError, match="not valid at block size"):
        delta_from_block_size(beta)


def test_gsa_predicted_norm_refuses_small_block_sizes_too():
    with pytest.raises(ValueError):
        gsa_predicted_norm(reduced_basis(), 2)


# ---------------------------------------------------------------------------------------------
# the comparison
# ---------------------------------------------------------------------------------------------


def test_agreement_within_tolerance_is_silent():
    result = compare_block_sizes(dimension=76, measured_min_block_size=30, report=report(beta_usvp=32))
    assert result.anomaly is None
    assert abs(result.discrepancy) <= result.tolerance


def test_a_large_discrepancy_is_named():
    """The project's rule: a disagreement is a finding, and silence is the failure mode."""
    result = compare_block_sizes(dimension=76, measured_min_block_size=90, report=report(beta_usvp=30))
    assert result.anomaly is not None
    assert "outside the" in result.anomaly


def test_the_type_refuses_a_silent_disagreement():
    """Enforced in the type, not trusted to this module — so a future caller cannot introduce one
    by constructing the result directly."""
    from qlwr_lattice_stress.protocols import ComparisonResult

    with pytest.raises(ValueError, match="must be named as an anomaly"):
        ComparisonResult(
            dimension=76, measured_min_block_size=90, predicted_min_block_size=30,
            discrepancy=2.0, tolerance=0.25,
        )


def test_an_inapplicable_model_is_not_a_discrepancy():
    """A model that reports no block size has made no prediction to disagree with. Reporting that
    as a large discrepancy would put a number into the report that no measurement supports."""
    result = compare_block_sizes(dimension=76, measured_min_block_size=30, report=report(beta_usvp=None))
    assert result.anomaly is None
    assert result.note and "no block size" in result.note


def test_a_sweep_that_recovered_nothing_is_an_anomaly():
    """The instance being harder than the sweep covered is a positive discrepancy, not an absence."""
    result = compare_block_sizes(dimension=76, measured_min_block_size=None, report=report(beta_usvp=30))
    assert result.anomaly is not None
    assert "recovered nothing" in result.anomaly


def test_anomalies_and_non_comparisons_are_kept_apart():
    """They call for different responses. Merging them would invite "the model produced no
    prediction" to be read as "the model and the measurement disagree"."""
    comparisons = [
        compare_block_sizes(dimension=48, measured_min_block_size=90, report=report(beta_usvp=30)),
        compare_block_sizes(dimension=76, measured_min_block_size=30, report=report(beta_usvp=30)),
        compare_block_sizes(dimension=98, measured_min_block_size=30, report=report(beta_usvp=None)),
    ]
    summary = summarise_anomalies(comparisons)
    assert summary.has_anomalies
    assert len(summary.anomalies) == 1
    assert len(summary.not_compared) == 1


# ---------------------------------------------------------------------------------------------
# the fit
# ---------------------------------------------------------------------------------------------


def test_the_fit_recovers_a_known_slope():
    """Exercised against a synthetic table with a slope built in.

    A fit validated only against real data cannot distinguish "the model holds" from "the fit
    works", which is why the frame is an input rather than the result objects.
    """
    beta = [20, 30, 40, 50, 60]
    frame = pd.DataFrame({"block_size": beta, "log2_cost": [0.292 * b + 7.0 for b in beta]})
    fitted = fit_core_svp_model(frame)
    assert fitted.model.c == pytest.approx(0.292, rel=1e-9)
    assert fitted.model.intercept == pytest.approx(7.0, rel=1e-9)
    assert fitted.model.r_squared == pytest.approx(1.0, abs=1e-12)
    assert (fitted.model.fitted_beta_min, fitted.model.fitted_beta_max) == (20, 60)


def test_a_two_point_fit_is_refused():
    """Two points determine a line exactly, so the residual is zero by construction and the fit
    cannot be contradicted by its own data."""
    frame = pd.DataFrame({"block_size": [20, 40], "log2_cost": [1.0, 2.0]})
    with pytest.raises(InsufficientPoints):
        fit_core_svp_model(frame)


def test_a_missing_column_is_named():
    with pytest.raises(ValueError, match="frame needs columns"):
        fit_core_svp_model(pd.DataFrame({"beta": [1, 2, 3]}))


def test_prediction_inside_the_domain_is_tagged_measured():
    """The tag travels with the number so a consumer cannot label an extrapolation as measured."""
    beta = [20, 30, 40, 50, 60]
    fitted = fit_core_svp_model(
        pd.DataFrame({"block_size": beta, "log2_cost": [0.292 * b for b in beta]})
    )
    _, inside = fitted.predict_log2_cost(40)
    _, outside = fitted.predict_log2_cost(200)
    assert inside == MEASURED
    assert outside == EXTRAPOLATED


def test_predict_log2_cost_agrees_with_the_model():
    beta = [20, 30, 40, 50, 60]
    fitted = fit_core_svp_model(
        pd.DataFrame({"block_size": beta, "log2_cost": [2.0 * b + 1.0 for b in beta]})
    )
    value, _ = predict_log2_cost(fitted.model, 35)
    assert value == pytest.approx(2.0 * 35 + 1.0)


# ---------------------------------------------------------------------------------------------
# the wall-clock fit's refusal, and the growth fit that replaced it
# ---------------------------------------------------------------------------------------------


def test_a_non_positive_slope_is_refused_not_returned():
    """Measured on the first real sweep: dimension 40 reached its minimum at block size 10 in
    3.69 s while dimension 80 reached its at block size 20 in 1.63 s — faster at a *larger* block
    size, giving a slope of -0.154.

    A negative core-SVP exponent says cost decreases with block size, which no reduction does. It is
    refused rather than returned, because a negative ``c`` would flow into every extrapolation
    downstream looking exactly like a number.
    """
    from qlwr_lattice_stress.analysis.scaling_extrapolation import NonPositiveSlope

    frame = pd.DataFrame({
        "block_size": [10, 20, 30],
        "log2_cost": [3.7, 1.6, 1.0],  # decreasing, as the real sweep produced
    })
    with pytest.raises(NonPositiveSlope, match="cost would \\*decrease\\*"):
        fit_core_svp_model(frame)


def test_the_growth_fit_recovers_a_known_relationship():
    """``beta_min`` against dimension — the relationship a sweep can actually measure."""
    from qlwr_lattice_stress.analysis.scaling_extrapolation import fit_block_size_growth

    frame = pd.DataFrame({
        "dimension": [40, 60, 80, 100],
        "block_size": [10, 20, 30, 40],  # exactly beta = d/2 - 10
    })
    growth = fit_block_size_growth(frame)
    assert growth.slope == pytest.approx(0.5)
    assert growth.intercept == pytest.approx(-10.0)
    assert growth.r_squared == pytest.approx(1.0, abs=1e-12)
    assert (growth.fitted_dimension_min, growth.fitted_dimension_max) == (40, 100)


def test_the_growth_fit_refuses_too_few_dimensions():
    """A dimension the attack could not solve contributes nothing, so the fit can legitimately have
    too few points even after a full sweep — and saying so is better than a line through two."""
    from qlwr_lattice_stress.analysis.scaling_extrapolation import (
        InsufficientPoints,
        fit_block_size_growth,
    )

    with pytest.raises(InsufficientPoints, match="at least 3"):
        fit_block_size_growth(pd.DataFrame({"dimension": [40, 80], "block_size": [10, 20]}))


def test_core_svp_cost_is_always_labelled_extrapolated():
    """Even where the block size was interpolated from measurements.

    The block size may be a measured-relationship output inside the fitted range, but the *cost* is
    the model's — labelling it measured because the block size was interpolated would be exactly the
    blend the reports exist to prevent.
    """
    from qlwr_lattice_stress.analysis.scaling_extrapolation import fit_block_size_growth

    growth = fit_block_size_growth(pd.DataFrame({
        "dimension": [40, 60, 80, 100],
        "block_size": [10, 20, 30, 40],
    }))
    # inside the fitted range
    _, beta_provenance = growth.block_size_at(60)
    _, cost_provenance = growth.core_svp_log2_cost_at(60)
    assert beta_provenance == MEASURED, "the block size at a fitted dimension is interpolated"
    assert cost_provenance == EXTRAPOLATED, "the cost is the model's, wherever it is evaluated"

    # and outside
    _, outside = growth.block_size_at(600)
    assert outside == EXTRAPOLATED


def test_the_growth_fit_cannot_produce_a_sign_error():
    """Unlike the wall-clock fit, the growth relationship is monotone in the direction the model
    needs — a larger lattice needs at least as large a block size — so where it is wrong it is wrong
    in ``r_squared`` rather than in a sign."""
    from qlwr_lattice_stress.analysis.scaling_extrapolation import fit_block_size_growth

    growth = fit_block_size_growth(pd.DataFrame({
        "dimension": [40, 60, 80, 100],
        "block_size": [10, 30, 40, 80],
    }))
    assert growth.slope > 0
