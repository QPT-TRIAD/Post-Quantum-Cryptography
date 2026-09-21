"""The normal-form transformation, and the two sign errors and one structural fact it took to get right.

Three things in here are worth the reader's attention, because each was a wrong answer that looked
right:

* the relation is ``b = A s - e``, **not** ``+e``. Derived for a plus sign it produces a
  transformation that is internally consistent and describes a different instance.
* ``A' = +A2 A1^{-1}``, not negative — substituting ``s = A1^{-1}(b1 + e1)`` into ``b2 = A2 s - e2``
  yields a *positive* term, and dropping that sign passes a consistency check on the wrong ``b'``.
* the sample reduction mod ``p`` is a single wrap at the top **only when ``p`` divides ``q``**.
  Otherwise ``(q//p) * r`` exceeds ``p`` for many ``r`` and the residual stops being small. The
  recorded production pair ``2^8 | 2^16`` is exactly the clean case, which is why this is easy to
  miss.
"""

from __future__ import annotations

import random

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from qlwr_lattice_stress.problem.normal_form import (
    PivotNotFound,
    assert_invertible_pivot,
    choose_invertible_pivot,
    inverse_mod,
    invert_normal_form,
    to_normal_form,
)
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8


def make_instance(nu=8, m=20, q=PRODUCTION_Q, p=PRODUCTION_P, seed=1) -> LatticeQLWRInstance:
    rng = random.Random(seed)
    while True:
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    return LatticeQLWRInstance(
        nu=nu, q_l=q, p=p, m=m,
        secret_s=tuple(rng.randrange(q) for _ in range(nu)), base=base, seed=seed,
    )


# ---------------------------------------------------------------------------------------------
# the relation, which everything else rests on
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "q,p",
    [(PRODUCTION_Q, PRODUCTION_P), (1 << 8, 1 << 4), (61, 19), (61, 13), (43, 11), (105, 3)],
)
def test_the_relation_holds_modulo_q_for_every_modulus(q, p):
    """``A s - e == b (mod q)`` — the identity the lattice construction assumes.

    Asserted across divisor and non-divisor moduli because the two behave differently, and a
    version that held only for the production pair would look correct on every default run.
    """
    inst = make_instance(nu=3, m=10, q=q, p=p)
    a = np.array(inst.base, dtype=np.int64)
    s = np.array(inst.secret_s, dtype=np.int64)
    b = np.array(inst.public_samples(), dtype=np.int64)
    e = np.array(inst.error_vector(), dtype=np.int64)
    assert np.array_equal((a @ s - e) % q, b % q), "A s - e must equal b modulo q"


@pytest.mark.parametrize("q,p", [(PRODUCTION_Q, PRODUCTION_P), (61, 19), (105, 3)])
def test_the_error_stays_inside_the_computed_bound(q, p):
    inst = make_instance(nu=3, m=10, q=q, p=p)
    bound = inst.noise_bound
    assert all(abs(v) <= bound for v in inst.error_vector())


def test_a_non_divisor_modulus_has_a_much_larger_noise_rate():
    """The structural fact: the sample reduction is one wrap at the top only when ``p`` divides
    ``q``.

    Measured at ``q = 61, p = 19``: ``q//p = 3``, so ``(q//p)*r`` exceeds ``p`` from ``r = 7``
    onward and the sample wraps repeatedly rather than once. The residual reaches 23 out of a
    modulus of 61 — a 38% noise rate — where the divisor case sits at 128 of 65536, roughly 0.2%.

    This is why the recorded production parameters are the clean regime, and why an instance built
    at a non-divisor modulus is a *different and much noisier* object rather than a scaled version
    of it.
    """
    clean = make_instance(q=PRODUCTION_Q, p=PRODUCTION_P)
    noisy = make_instance(q=61, p=19)
    clean_rate = clean.noise_bound / clean.q_l
    noisy_rate = noisy.noise_bound / noisy.q_l
    assert clean_rate < 0.01, clean_rate
    assert noisy_rate > 0.3, noisy_rate


def test_the_error_definition_matches_the_lifted_sample_not_the_raw_rounding():
    """In the wrap bucket these differ by ``(q//p)*p``, which is ``q`` only when ``p`` divides it."""
    inst = make_instance(q=61, p=19, nu=3, m=10)
    a = np.array(inst.base, dtype=np.int64)
    s = np.array(inst.secret_s, dtype=np.int64)
    assert np.array_equal(
        (a @ s - np.array(inst.error_vector())) % inst.q_l,
        np.array(inst.public_samples()) % inst.q_l,
    )


# ---------------------------------------------------------------------------------------------
# the transformation
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "q,p", [(PRODUCTION_Q, PRODUCTION_P), (256, 16), (61, 19), (105, 3)]
)
def test_the_secret_is_recovered_exactly(q, p):
    """The round trip that makes the attack's output *about QLWR* rather than about a generic LWE
    instance: a recovered short vector yields ``e1``, and ``e1`` yields the secret."""
    for seed in range(1, 6):
        inst = make_instance(nu=4, m=14, q=q, p=p, seed=seed)
        nf = to_normal_form(inst)
        assert invert_normal_form(nf, inst) == tuple(inst.secret_s), f"seed {seed}"


def test_the_transformation_consumes_exactly_nu_samples():
    """The cost is real and measured: below a sample-to-unknown ratio of about 1.6 the estimator's
    models stop applying altogether, so a normal form that quietly ate too many samples would
    manufacture an unattackable instance."""
    inst = make_instance(nu=8, m=20)
    nf = to_normal_form(inst)
    assert nf.m == inst.m - inst.nu


def test_both_the_secret_and_the_error_are_small():
    """If either were large the embedding would contain no short vector, and the planted-vector
    test would fail for a reason that looked like a lattice bug."""
    nf = to_normal_form(make_instance(nu=8, m=20))
    nf.check_small()


def test_the_transformation_actually_reduces_the_secret():
    """A vacuous transformation that returned the instance unchanged would pass the round trip
    while defeating the point."""
    inst = make_instance(nu=8, m=20)
    nf = to_normal_form(inst)
    assert int(nf.x.max()) < inst.q_l // 2


def test_a_corrupted_normal_form_is_caught():
    """``check`` must not be decorative — a transformation that is off by one is exactly the
    failure mode this whole milestone exists to catch."""
    import dataclasses

    nf = to_normal_form(make_instance(nu=4, m=12))
    broken = dataclasses.replace(nf, b=(nf.b + 1) % nf.q)
    with pytest.raises(AssertionError, match="inconsistent"):
        broken.check()


# ---------------------------------------------------------------------------------------------
# the pivot
# ---------------------------------------------------------------------------------------------


@given(q=st.sampled_from([1 << 16, 1 << 8, 3 * 5 * 7, 105, 61]), seed=st.integers(0, 5000))
@settings(max_examples=15, deadline=None)
def test_a_chosen_pivot_is_always_invertible_modulo_q(q, seed):
    """When a pivot is returned, it is invertible modulo ``q``.

    The check is ``gcd(det, q) == 1``, never ``det != 0``: over ``Z/2^k`` an even determinant means
    singular, so a pivot invertible over the rationals can still be unusable.

    ``PivotNotFound`` is a **legitimate outcome**, not a failure. The search also requires the
    complement of the pivot to span, because the normal form's transformed base ``A' = A2 A1^-1``
    inherits the complement's rank — and for some draws no split satisfies both. That is the
    instance being unusable rather than the search being wrong, and the caller is expected to redraw
    rather than substitute a pivot. Asserting that a pivot is *always* found would be asserting
    something false.
    """
    inst = make_instance(nu=3, m=8, q=q, p=3, seed=seed)
    base = np.array(inst.base, dtype=np.int64)
    try:
        pivot = choose_invertible_pivot(base, q)
    except PivotNotFound:
        return  # a deficient draw: redraw, do not weaken the requirement
    assert_invertible_pivot(base, pivot, q)


def test_an_even_determinant_pivot_is_refused():
    """``[[2, 0], [0, 1]]`` has determinant 2 — invertible over the rationals, singular mod 4."""
    base = np.array([[2, 0], [0, 1], [5, 7]], dtype=np.int64)
    with pytest.raises(ValueError, match="not coprime"):
        assert_invertible_pivot(base, (0, 1), 4)


def test_a_base_that_cannot_span_is_refused():
    with pytest.raises(PivotNotFound):
        choose_invertible_pivot(np.zeros((6, 3), dtype=np.int64), 1 << 16)


def test_inverse_mod_handles_a_matrix_needing_row_combination():
    """``[[3,1],[5,2]]`` has determinant 1 and is invertible mod 105, but neither entry of its first
    column is invertible alone — so pivoting on a single entry fails on a matrix that is perfectly
    invertible, which is why a composite modulus goes through the CRT."""
    a = np.array([[3, 1], [5, 2]], dtype=np.int64)
    inverse = inverse_mod(a, 105)
    assert np.array_equal((a @ inverse) % 105, np.eye(2, dtype=np.int64))


def test_inverse_mod_round_trips_at_the_production_modulus():
    """On a *chosen* pivot, not the first ``nu`` rows.

    The first four rows of a random base are not in general invertible modulo ``2^16`` — that is
    precisely why the pivot is searched for rather than taken from the top — and handing
    ``inverse_mod`` a singular submatrix is meant to raise.
    """
    inst = make_instance(nu=4, m=12)
    base = np.array(inst.base, dtype=np.int64)
    pivot = choose_invertible_pivot(base, PRODUCTION_Q)
    a = base[list(pivot)]
    inverse = inverse_mod(a, PRODUCTION_Q)
    assert np.array_equal((a @ inverse) % PRODUCTION_Q, np.eye(4, dtype=np.int64))


def test_inverse_mod_refuses_a_singular_submatrix():
    """The refusal is the check working, not a limitation: an even determinant means singular over
    ``Z/2^k``, and inverting it would produce a transformation that cannot be undone."""
    with pytest.raises(ValueError, match="singular"):
        inverse_mod(np.array([[2, 0], [0, 2]], dtype=np.int64), 1 << 16)
