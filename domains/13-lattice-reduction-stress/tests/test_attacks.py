"""The two attack families, and the one of them that does not apply at this scale.

The primal attack works and its threshold behaves. The dual attack is **inapplicable** across every
size tested, for a reason that is arithmetic rather than a defect: the distinguisher's band is
``||y||_1 * B``, and the shortest dual vectors available at this modulus-to-noise ratio have
``||y||_1`` roughly 130 times the ``q/(2B)`` budget. The band then covers the whole residue space
and the statistic cannot separate anything.

That asymmetry is worth stating plainly because it is the reverse of what a reader might expect: at
these parameters the *primal* attack is the easy one and the dual attack does not reach. The
estimator reports the minimum over both, so a project that ran only the dual would conclude the
instance was hard.
"""

from __future__ import annotations

import random

import numpy as np
import pytest

from qlwr_lattice_stress.attacks import (
    find_minimum_successful_block_size,
    prepare_primal,
    recover_secret_from_vector,
    run_dual_attack,
    run_primal_attack,
    uniform_control,
)
from qlwr_lattice_stress.engines import FpylllBKZEngine
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)
from qlwr_lattice_stress.protocols import NOT_RUN

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8

#: The calibrated instance from M5: large enough that LLL fails, small enough to run in seconds.
NU, M = 32, 76


def make_instance(seed: int = 1) -> LatticeQLWRInstance:
    rng = random.Random(seed)
    while True:
        base = tuple(tuple(rng.randrange(PRODUCTION_Q) for _ in range(NU)) for _ in range(M))
        if full_column_rank_mod([list(r) for r in base], PRODUCTION_Q, NU) == NU:
            break
    return LatticeQLWRInstance(
        nu=NU, q_l=PRODUCTION_Q, p=PRODUCTION_P, m=M,
        secret_s=tuple(rng.randrange(PRODUCTION_Q) for _ in range(NU)), base=base, seed=seed,
    )


@pytest.fixture(scope="module")
def engine():
    return FpylllBKZEngine()


@pytest.fixture(scope="module")
def prepared():
    return make_instance(), prepare_primal(make_instance())


# ---------------------------------------------------------------------------------------------
# the primal attack
# ---------------------------------------------------------------------------------------------


@pytest.mark.slow
def test_the_primal_sweep_finds_a_threshold_and_records_the_failures(engine):
    """A minimum block size is only meaningful alongside the failures below it.

    A sweep that stopped at the first success could not distinguish "found at 30" from "found at 30
    after failing everywhere below", and only the second makes the number a threshold.
    """
    instance = make_instance()
    minimum, results = find_minimum_successful_block_size(instance, engine, [2, 10, 20, 30, 40])

    assert minimum is not None, "no block size in the range recovered the vector"
    failures = [r for r in results if not r.recovered]
    assert failures, "a minimum with no failures below it is not a threshold"
    assert all(r.block_size < minimum for r in failures), (
        "a failure above the reported minimum would contradict it"
    )
    assert min(r.block_size for r in results if r.recovered) == minimum


@pytest.mark.slow
def test_recovery_requires_a_real_block_size(engine):
    """The anti-vacuity assertion, at the level of the attack rather than the fixture.

    LLL must not recover it, or the threshold means nothing.
    """
    instance = make_instance()
    result = run_primal_attack(instance, engine, 2)
    assert not result.recovered, "LLL recovered the planted vector; the instance is too easy"


@pytest.mark.slow
def test_the_attack_is_deterministic_for_a_fixed_instance(engine):
    """Two runs of the same instance must agree, or a recorded threshold could not be reproduced."""
    instance = make_instance(seed=3)
    first = run_primal_attack(instance, engine, 30)
    second = run_primal_attack(instance, engine, 30)
    assert first.recovered == second.recovered


def test_the_recovered_secret_matches_the_instance(prepared):
    """The round trip that makes this about QLWR rather than about a lattice.

    A recovered vector yields ``x``, and ``x`` inverts to the secret. Without this assertion the
    attack could be recovering an object with no relation to the scheme.
    """
    instance, (nf, factor, basis, planted) = prepared
    assert recover_secret_from_vector(planted, nf, instance) == tuple(instance.secret_s)


def test_the_planted_vector_is_in_the_lattice(prepared):
    """The M4 gate, re-asserted here so a regression in the attack's own construction is caught
    where it happens rather than in a test file two milestones away."""
    from qlwr_lattice_stress.lattice.planted_vector import assert_in_lattice

    instance, (nf, factor, basis, planted) = prepared
    assert_in_lattice(list(planted), basis)


def test_a_block_size_the_engine_refuses_becomes_a_result_not_an_exception(engine):
    """A refusal has to be reportable. A sweep that omits a point it could not run is
    indistinguishable from one where the point succeeded."""
    instance = make_instance()
    nf, _, basis, _ = prepare_primal(instance)
    oversized = basis.nrows + 5
    result = run_primal_attack(instance, engine, oversized)
    # fpylll would accept this silently; the engine refuses it, and the attack surfaces that. The
    # assertion used to accept either provenance, which any outcome that did not raise satisfies.
    assert result.provenance == "not_run"
    assert f"block size {oversized} exceeds the basis dimension {basis.nrows}" in result.not_run_reason
    assert result.recovered is False and result.wall_clock_s == 0.0


def test_a_refused_point_reports_the_same_dimension_as_a_measured_one(engine):
    """Cross-check: one column, one meaning.

    The sweep's ``dimension`` column carried two different quantities — the points that ran reported
    the embedded basis width (``nf.m + nf.n + 1``), and the points the time guard refused reported
    ``instance.m + instance.nu + 1``. In the dimension-160 run that was **161 against 228 in adjacent
    rows of the same table**, and section 6's anomaly text inherited the 228.

    Both are plausible numbers and neither looks wrong alone. What makes it a defect is that only
    one of them is a lattice this attack ever built: the normal form consumes ``nu`` samples and
    adds ``nu`` unknowns, so the true width is ``instance.m + 1``, and ``instance.m + nu + 1``
    describes the embedding you get if the normal form is *skipped* — the one that contains no short
    vector, which is the premise the whole project rests on.

    The assertion is on equality across the sweep rather than on the value, because that is the
    property the report depends on and the one that was false.
    """
    instance = make_instance()
    nf, _, basis, _ = prepare_primal(instance)

    # The range starts below the threshold on purpose: block size 2 fails on this instance (the
    # slow test above relies on the same fact), so the sweep neither succeeds early and breaks nor
    # leaves the guard without a previous measurement to project from.
    minimum, results = find_minimum_successful_block_size(
        instance, engine, [2, 10, 20, 30], max_seconds_per_block_size=1e-9
    )
    assert len(results) >= 2, "the guard did not fire; the test would be vacuous"
    assert any(r.provenance == NOT_RUN for r in results), "no refused point to compare against"

    dimensions = {r.dimension for r in results}
    assert len(dimensions) == 1, (
        f"the sweep reported dimensions {sorted(dimensions)}. A single column of a single table "
        "cannot mean two things; the refused points are describing a lattice the attack never built."
    )
    assert dimensions == {basis.nrows}, (
        f"reported {sorted(dimensions)}, the embedded basis is {basis.nrows} wide"
    )

    # And the identity that makes it safe to take the width from the embedded basis: normalising
    # consumes nu samples and adds nu unknowns, leaving the total unchanged.
    assert basis.nrows == nf.m + nf.n + 1
    assert instance.m + instance.nu + 1 != basis.nrows, (
        "nu is zero or the wrong formula has become right; if these coincide the test is vacuous"
    )


def test_each_family_is_labelled_at_the_width_of_its_own_lattice(engine):
    """The two families reduce different lattices, so they do not share a dimension.

    Both are pinned against the basis the corresponding attack actually constructs, rather than
    against the formula — a formula checked against itself is what produced the defect this guards.
    The primal width comes from ``prepare_primal``'s embedded basis and the dual width from
    ``dual_basis``.
    """
    from qlwr_lattice_stress.lattice.dual_embedding import dual_basis
    from qlwr_lattice_stress.pipeline import lattice_widths_by_family

    instance = make_instance()
    nf, _, embedded, _ = prepare_primal(instance)
    widths = lattice_widths_by_family(nf)

    assert widths["primal_usvp"] == embedded.nrows, (
        f"the primal comparison would be labelled {widths['primal_usvp']} while the attack reduces "
        f"a lattice {embedded.nrows} wide"
    )
    assert widths["dual"] == dual_basis(nf).nrows, (
        f"the dual comparison would be labelled {widths['dual']} while the dual attack reduces a "
        f"lattice {dual_basis(nf).nrows} wide"
    )
    assert widths["primal_usvp"] != widths["dual"], "the two lattices are not the same width"

    # And the identity that ties the primal width back to the raw instance, which is why
    # ``instance.m`` alone is the right q-ary dimension to report: normalising consumes nu samples
    # and adds nu unknowns. ``instance.m + instance.nu + 1`` — the value this replaced — is larger
    # by exactly nu, and describes the embedding you get if the normal form is skipped.
    assert widths["primal_usvp"] == instance.m + 1
    assert instance.m + instance.nu + 1 == widths["primal_usvp"] + instance.nu


# ---------------------------------------------------------------------------------------------
# the dual attack
# ---------------------------------------------------------------------------------------------


@pytest.mark.slow
def test_the_dual_attack_reports_inapplicability_rather_than_absence(engine):
    """It does not apply here, and the difference between "does not apply" and "was tried and found
    nothing" is the whole reason the refusal carries a reason.

    Measured: the shortest reduced dual vector has ``||y||_1`` far above the ``q/(2B)`` budget, so
    the band covers the whole residue space and no vector can distinguish.
    """
    instance = make_instance()
    result = run_dual_attack(instance, engine, 20)
    assert result.provenance == NOT_RUN, (
        "expected the dual attack to be inapplicable at this scale; if this now measures, the "
        "finding has changed and the note should be revisited rather than the test relaxed"
    )
    assert result.not_run_reason and "band" in result.not_run_reason


def test_the_uniform_control_is_uniform_and_seeded():
    """The control must be genuinely uniform and reproducible. Drawing it by perturbing the real
    sample would carry structure the statistic could latch onto, and the control would then agree
    for the wrong reason."""
    from qlwr_lattice_stress.problem.normal_form import to_normal_form

    nf = to_normal_form(make_instance())
    a = uniform_control(nf, seed=1234)[0]
    b = uniform_control(nf, seed=1234)[0]
    c = uniform_control(nf, seed=1235)[0]
    assert a == b and a != c
    assert len(a) == nf.m
    assert all(0 <= v < nf.q for v in a)
    # A crude sanity check that it is not a constant or a rescaled copy of the real sample.
    assert len(set(a)) > nf.m // 2
    assert a != list(map(int, nf.b))


# The distinguisher's positive control lives in ``tests/test_dual_attack_measured.py``
# (``test_the_dual_attack_measures_and_separates_real_from_uniform`` and the tests around it): real
# reduced dual vectors, a real sample against a uniform one, both sides and the gap asserted. The
# test that stood here — "separates real from uniform when it can" — handed the statistic a unit
# vector, which its own comment said is not in the dual, and asserted only that two fractions lay in
# [0, 1]. Every outcome passes that, so it was deleted rather than kept as a second, weaker claim.
