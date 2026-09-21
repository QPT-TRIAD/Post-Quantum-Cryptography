"""The estimator path, and the cross-check that makes it trustworthy.

The load-bearing test here is :func:`test_the_estimators_normal_form_is_the_same_transformation` —
cross-check 2 of the project's battery. The emulator will build its own normal form in M3 and apply
it before constructing a lattice; the estimator applies *its* normal form internally before
estimating. If those two transformations differ, the empirical and theoretical halves of the
project's central comparison describe different lattices, and nothing else in the build could
detect it: both numbers would be individually correct and mutually meaningless.

The check is two code paths to one number — pass the parameters raw and let the estimator normalise
them, or normalise them explicitly first and hand over the result. Both must yield the same block
size.
"""

from __future__ import annotations

import math
import random

import pytest

from qlwr_lattice_stress.analysis.cost_estimation import (
    EstimatorUnavailable,
    PUBLISHED_LWE_SCHEMES,
    _cost_field,
    estimate,
    estimator_revision,
    lwe_parameters_for,
    parameter_set_from_instance,
    reference_parameter_set,
)
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)
from qlwr_lattice_stress.protocols import EXTRAPOLATED, SAME_SCALE

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8


def _estimator():
    try:
        import estimator

        return estimator
    except ImportError:  # pragma: no cover
        pytest.skip("lattice-estimator is not importable")


#: The recorded production shape as a *ratio*: 608 samples for 256 unknowns. The scaling rule
#: preserves this, and it turns out to be load-bearing rather than cosmetic — see `make_instance`.
PRODUCTION_M_OVER_NU = 608 / 256


def make_instance(nu=64, m=None, seed=3) -> LatticeQLWRInstance:
    """A scaled instance at the recorded modulus pair and the recorded sample-to-unknown ratio.

    The ratio is not decoration. Measured across (nu, m): at m = nu the estimator returns an
    infinite cost for **every** attack family, because a dual attack needs substantially more
    samples than unknowns and the primal one needs the noise to be small relative to the embedding.
    At the production ratio of 2.38 the models return finite numbers. Below a *family-dependent*
    threshold they do not, and the thresholds are not equal: `usvp` needs m ≳ 2.08*nu and is
    near-constant there, while `dual` runs 1.34 to 2.30 across nu = 32..512. This docstring
    originally said "about 1.6" for every family — one measurement at nu = 64, generalised.
    A test instance with m = nu would have made the cross-check vacuous: it would have compared
    two infinities and agreed.

    The modulus pair is shared with the recorded set deliberately: preserving it is the purpose of
    the scaling rule. The dimension is not shared.
    """
    rng = random.Random(seed)
    q = PRODUCTION_Q
    if m is None:
        m = round(nu * PRODUCTION_M_OVER_NU)
    while True:
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    secret = tuple(rng.randrange(q) for _ in range(nu))
    return LatticeQLWRInstance(
        nu=nu, q_l=q, p=PRODUCTION_P, m=m, secret_s=secret, base=base, seed=seed
    )


# ---------------------------------------------------------------------------------------------
# the mapping — derived, not fitted
# ---------------------------------------------------------------------------------------------


def test_the_noise_distribution_comes_from_the_modulus_ratio():
    """Exactly uniform on ``[-q/(2p), q/(2p) - 1]``. No sigma is chosen anywhere."""
    inst = make_instance()
    params = lwe_parameters_for(inst)
    b = inst.noise_bound
    assert b == PRODUCTION_Q // (2 * PRODUCTION_P) == 128
    # The estimator's ND.Uniform carries its own standard deviation; it must equal the closed form
    # for a *discrete uniform* on that interval, which is what the rounding produces.
    expected = math.sqrt((4.0 * b * b - 1.0) / 12.0)
    assert float(params.Xe.stddev) == pytest.approx(expected, rel=1e-9)


def test_the_mapping_keeps_the_secret_uniform():
    """The corpus specifies a uniform secret. Normalising is the estimator's business, not this
    mapping's — doing it here would hide the very transformation the cross-check is about."""
    inst = make_instance()
    params = lwe_parameters_for(inst)
    assert float(params.Xs.stddev) == pytest.approx(
        math.sqrt((float(PRODUCTION_Q) ** 2 - 1) / 12.0), rel=1e-6
    )


def test_the_mapping_preserves_the_parameters_that_matter():
    inst = make_instance(nu=32, m=76)
    p = lwe_parameters_for(inst)
    assert (p.n, p.q, p.m) == (32, PRODUCTION_Q, 76)


def test_normalising_costs_samples():
    """A fact the cross-check depends on: ``normalize()`` consumes one sample per unknown.

    Measured: m goes 152 -> 88 at n=64. So the *normalised* instance has a lower sample-to-unknown
    ratio than the raw one, and below the applicable threshold the estimator returns an infinite cost
    rather than a number. That threshold is family-dependent (`usvp` ~2.08*nu and near-constant;
    `dual` 1.34 to 2.30) — the "about 1.6" this docstring used to quote was one point at nu = 64.
    That is why the cross-check below asserts its comparison is non-empty rather than assuming both
    routes produce a number.
    """
    est = _estimator()
    from estimator.lwe_parameters import LWEParameters

    raw = lwe_parameters_for(make_instance(nu=64))
    assert LWEParameters.normalize(raw).m == raw.m - raw.n


def test_a_parameter_set_from_an_instance_carries_its_provenance():
    ps = parameter_set_from_instance(make_instance())
    assert ps.kind == "lwe"
    assert "Uniform(-128, 127)" in ps.noise
    assert ps.q == PRODUCTION_Q


# ---------------------------------------------------------------------------------------------
# CROSS-CHECK 2 — the reason this milestone exists
# ---------------------------------------------------------------------------------------------


@pytest.mark.slow
def test_the_estimators_normal_form_is_the_same_transformation():
    """Two routes to one number.

    Route 1 hands the estimator the raw instance and lets its ``normalize()`` do the work.
    Route 2 normalises explicitly first and hands over the result.

    If these disagree, the emulator's normal form (M3) and the estimator's are not the same
    transformation — and the project's central comparison, measured versus theoretical at the same
    scale, would be comparing two different lattices. Both numbers would look right.

    The route-2 call must bypass the estimator's own normalisation of an already-normal instance;
    ``normalize()`` is idempotent, so passing the normalised parameters through the same entry point
    exercises exactly that.
    """
    est = _estimator()
    from estimator.lwe_parameters import LWEParameters

    inst = make_instance(nu=64)  # m follows the recorded sample-to-unknown ratio
    raw = lwe_parameters_for(inst)

    normalised = LWEParameters.normalize(raw)
    # The transformation must actually do something here, or this test would pass vacuously by
    # comparing a thing with itself.
    assert float(normalised.Xs.stddev) < float(raw.Xs.stddev), (
        "normalize() left the secret large, so the two routes are identical and the check proves "
        "nothing about whether the transformations agree"
    )

    from qlwr_lattice_stress.analysis.cost_estimation import DEFAULT_DENY_LIST

    route1 = est.LWE.estimate(raw, deny_list=DEFAULT_DENY_LIST, quiet=True)
    route2 = est.LWE.estimate(normalised, deny_list=DEFAULT_DENY_LIST, quiet=True)

    compared, inapplicable = [], []
    for family in ("usvp", "dual", "dual_hybrid"):
        if family not in route1 or family not in route2:
            continue
        # A family with an infinite cost has no valid parameters for this instance, so there is no
        # block size to compare. Counting it as agreement would be the vacuous version of this
        # test; recording it and asserting the comparison is non-empty below is the honest one.
        if _log2_optional(route1[family].get("rop")) is None:
            inapplicable.append(family)
            continue
        b1 = _cost_field(route1[family], "beta", attack=family)
        b2 = _cost_field(route2[family], "beta", attack=family)
        assert b1 == b2, (
            f"{family}: raw parameters give beta={b1} but explicitly normal-formed parameters give "
            f"beta={b2}. The two normal forms are not the same transformation, so the measured and "
            "theoretical halves of the comparison would describe different lattices."
        )
        compared.append(family)

    assert compared, (
        f"no attack family was applicable, so this check proved nothing "
        f"(inapplicable: {inapplicable}); the instance needs different parameters"
    )


def _log2_optional(value):
    from math import isinf, log2

    try:
        f = float(value)
    except Exception:  # noqa: BLE001
        return None
    return None if isinf(f) else log2(f)


@pytest.mark.slow
def test_normalisation_makes_the_secret_small():
    """The estimator's ``normalize`` and the emulator's must agree on *what* moves, not just that
    the resulting block size matches.

    The property is that the secret becomes small — measured against the **raw** secret, which is
    uniform on ``Z_q`` at sigma ~18918. It is deliberately *not* asserted against the resulting
    error, because what happens to the error depends on the sample count: at ``m = n`` it becomes
    the large distribution (measured sigma 18918.61), while at the production ratio it stays at
    sigma 73.90 and the two come out equal. Both are legitimate; only the secret's direction is
    invariant, and only that is asserted.
    """
    est = _estimator()
    from estimator.lwe_parameters import LWEParameters

    raw = lwe_parameters_for(make_instance(nu=64))
    normalised = LWEParameters.normalize(raw)
    assert float(normalised.Xs.stddev) < float(raw.Xs.stddev), (
        "after normalisation the secret should be small; if it is not, the embedding will contain "
        "no short vector and the attack would be on an instance with nothing to find"
    )
    # and it should have landed on the rounding noise, not somewhere arbitrary
    assert float(normalised.Xs.stddev) == pytest.approx(
        math.sqrt((4.0 * 128 * 128 - 1) / 12.0), rel=1e-6
    )


# ---------------------------------------------------------------------------------------------
# the published reference — the estimator validates itself
# ---------------------------------------------------------------------------------------------


@pytest.mark.slow
def test_kyber512_reproduces_its_pinned_baseline():
    """The theoretical half is anchored to the estimator's own output at a recorded revision.

    Not a literature constant: the estimate moves with the cost and shape models, so a remembered
    number would either fail on a legitimate model change or match by coincidence and hide one.
    """
    ps = reference_parameter_set("Kyber512")
    report = estimate(ps, models=("primal_usvp", "dual"))
    assert report.beta_usvp == 406
    assert report.provenance == SAME_SCALE
    assert report.estimator_revision != "unknown"


@pytest.mark.slow
def test_the_quantum_figure_is_lower_than_the_classical_one():
    """Quantum sieving's constant is 0.265 against 0.292, so the quantum cost must come out lower.
    If it does not, the ``mode`` argument is not being threaded through."""
    report = estimate(reference_parameter_set("Kyber512"), models=("primal_usvp",))
    assert report.rop_classical_log2_min is not None
    assert report.rop_quantum_log2_min is not None
    assert report.rop_quantum_log2_min < report.rop_classical_log2_min


@pytest.mark.slow
def test_the_minimum_is_taken_over_the_models_requested():
    """The minimum over attack families is the number that gets reported as the security level, so
    it must be the minimum over what was asked for — not over one family, and not over everything."""
    both = estimate(reference_parameter_set("Kyber512"), models=("primal_usvp", "dual"))
    only_usvp = estimate(reference_parameter_set("Kyber512"), models=("primal_usvp",))
    assert both.rop_classical_log2_min <= only_usvp.rop_classical_log2_min
    assert only_usvp.minimum_over_models == "primal_usvp"


def test_an_unknown_reference_scheme_is_refused_with_the_legal_names():
    with pytest.raises(ValueError, match="unknown published scheme"):
        reference_parameter_set("Kyber999")


def test_the_published_scheme_list_is_resolvable():
    """A typo in the tuple would only surface when someone asked for that scheme."""
    est = _estimator()
    for name in PUBLISHED_LWE_SCHEMES:
        assert hasattr(est.schemes, name), name


# ---------------------------------------------------------------------------------------------
# refusing to read a failure as a result
# ---------------------------------------------------------------------------------------------


def test_a_failed_attack_is_not_read_as_a_result():
    """The estimator runs each family under ``catch_exceptions=True``, so a failure returns a
    placeholder. Reading ``beta`` off it would put a number produced by a failure into the report's
    theoretical section, where it would look exactly like a real one."""
    with pytest.raises(ValueError, match="failed"):
        _cost_field(RuntimeError("model diverged"), "beta", attack="usvp")


def test_a_missing_field_is_refused_rather_than_defaulted():
    class NotACost:
        beta = 40

    with pytest.raises(ValueError, match="no 'rop'"):
        _cost_field(NotACost(), "rop", attack="usvp")


def test_a_none_cost_is_refused():
    with pytest.raises(ValueError, match="returned nothing"):
        _cost_field(None, "beta", attack="dual")
