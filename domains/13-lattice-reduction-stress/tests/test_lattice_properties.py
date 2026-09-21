"""The lattice constructions as *properties*, checked against the definition and not only against ``src``.

The design document calls basis validity and planted-vector membership load-bearing, and until now
both were asserted at three fixed shapes and one modulus, through ``src``'s own ``assert_*`` helpers.
A helper that shares a misreading with the construction it checks — a transposed ``A``, a block in
the wrong place — passes it. So each property below is asserted twice: once through the helper,
which is what the pipeline relies on, and once from the definition, written out here in plain
Python integers against ``nf.a`` and nothing else.

Three parts, matching three modules:

* ``basis_construction`` / ``planted_vector`` — hypothesis properties over ``(nu, m, q, seed, M)``,
  including the non-production moduli ``q = 105`` and ``q = 61`` the helpers were never run at.
* ``primal_embedding`` — which had no direct test at all. ``notes/05-embeddings.md`` records the
  calibrated factors (``3, 3, 3, 2, 2`` at ``nu = 20``; ``3`` five times at ``nu = 32``); they are
  pinned here, seed for seed.
* ``dual_embedding`` — the "4 sizes x 5 seeds" the same note records, the exact primal-dual
  relation, and one corruption *per check*, because a test that trips only the annihilation check
  says nothing about whether the volume check can fail.
"""

from __future__ import annotations

import math
import random

import numpy as np
import pytest
import sympy
from fpylll import LLL, IntegerMatrix
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from qlwr_lattice_stress.lattice._exact import NotInLattice
from qlwr_lattice_stress.lattice.basis_construction import (
    assert_basis_valid,
    basis_determinant_abs,
    build_primal_embedding_basis,
    build_qary_basis,
)
from qlwr_lattice_stress.lattice.dual_embedding import (
    assert_dual_valid,
    dual_basis,
    dual_dimension,
)
from qlwr_lattice_stress.lattice.planted_vector import (
    assert_in_lattice,
    planted_norm_squared,
    planted_short_vector,
)
from qlwr_lattice_stress.lattice.primal_embedding import (
    artifact_norm,
    calibrate_embedding_factor,
    kannan_embedding,
    minimum_embedding_factor,
)
from qlwr_lattice_stress.problem.normal_form import PivotNotFound, to_normal_form
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8

#: The production pair, a smaller power-of-two pair, a composite modulus with an *odd* ratio
#: ``q / p = 15``, and a prime non-divisor pair. The last two are the ones no lattice helper had
#: been run at.
MODULI = [(PRODUCTION_Q, PRODUCTION_P), (1 << 12, 1 << 4), (105, 7), (61, 19)]

#: The four shapes and five seeds ``notes/05-embeddings.md`` records for the dual invariants.
DUAL_SIZES = [(4, 12), (8, 20), (16, 40), (32, 76)]
SEEDS = [1, 2, 3, 4, 5]


def make_nf(nu=8, m=20, seed=1, q=PRODUCTION_Q, p=PRODUCTION_P, *, tries=200):
    """A normal-form instance, by the same draw order as ``test_basis_construction.make_nf``.

    The draw order is kept identical on purpose: the calibrated factors pinned below are the ones
    ``notes/05`` measured, and they are reproducible only from the same stream. Returns ``None``
    when no full-rank base or no valid pivot turns up, which a property test discards.
    """
    rng = random.Random(seed)
    for _ in range(tries):
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    else:
        return None
    instance = LatticeQLWRInstance(
        nu=nu, q_l=q, p=p, m=m,
        secret_s=tuple(rng.randrange(q) for _ in range(nu)), base=base, seed=seed,
    )
    try:
        return to_normal_form(instance)
    except PivotNotFound:
        return None


@st.composite
def normal_forms(draw, *, moduli=MODULI, min_extra=2, max_extra=10):
    nu = draw(st.integers(min_value=2, max_value=5))
    m = draw(st.integers(min_value=nu + min_extra, max_value=nu + max_extra))
    q, p = draw(st.sampled_from(moduli))
    seed = draw(st.integers(min_value=0, max_value=2**32 - 1))
    nf = make_nf(nu, m, seed, q, p)
    assume(nf is not None)
    return nf


def rows_of(matrix) -> list[list[int]]:
    return [[int(matrix[i, j]) for j in range(matrix.ncols)] for i in range(matrix.nrows)]


def a_of(nf) -> list[list[int]]:
    """``nf.a`` as nested Python ints, so nothing below depends on numpy's integer width."""
    return [[int(nf.a[i, j]) % nf.q for j in range(nf.n)] for i in range(nf.m)]


def exact_abs_det(rows) -> int:
    """``|det|`` through sympy's rationals — a second implementation, not ``src``'s Bareiss."""
    return abs(int(sympy.Matrix(rows).det(method="bareiss")))


def gaussian_heuristic(dimension: int, log_volume: float) -> float:
    """``sqrt(d / (2 pi e)) * vol^(1/d)``, with the volume supplied as a logarithm."""
    return math.sqrt(dimension / (2.0 * math.pi * math.e)) * math.exp(log_volume / dimension)


# ---------------------------------------------------------------------------------------------
# the q-ary basis
# ---------------------------------------------------------------------------------------------


@settings(deadline=None, max_examples=40)
@given(nf=normal_forms())
def test_the_qary_basis_is_valid_for_every_instance(nf):
    """``assert_basis_valid`` over random shapes, seeds and all four moduli — the helper's view."""
    assert_basis_valid(build_qary_basis(nf), nf)


@settings(deadline=None, max_examples=40)
@given(nf=normal_forms())
def test_every_qary_row_satisfies_the_modular_relation_independently(nf):
    """Every row ``(u | w)`` has ``u == A w (mod q)`` — recomputed here, against ``nf.a`` alone.

    Also pins the layout the rest of the project reads rows by: ``m`` sample coordinates first,
    then ``n`` secret coordinates; ``n`` secret rows first, then ``m`` modular rows.
    """
    n, m, q = nf.n, nf.m, nf.q
    a = a_of(nf)
    rows = rows_of(build_qary_basis(nf))
    assert len(rows) == n + m and all(len(row) == n + m for row in rows)
    for row in rows:
        u, w = row[:m], row[m:]
        for i in range(m):
            assert (u[i] - sum(a[i][j] * w[j] for j in range(n))) % q == 0

    # The shape of the two blocks, which the relation alone does not force.
    for j in range(n):
        assert rows[j][m:] == [int(k == j) for k in range(n)]
        assert rows[j][:m] == [a[i][j] for i in range(m)]
    for i in range(m):
        assert rows[n + i] == [q * int(k == i) for k in range(n + m)]


@settings(deadline=None, max_examples=40)
@given(nf=normal_forms())
def test_the_qary_determinant_is_q_to_the_sample_count(nf):
    """``|det B| = q^m`` with ``m`` the normal form's *remaining* sample count — by ``src``'s exact
    determinant and by an independent one, which must also agree with each other."""
    basis = build_qary_basis(nf)
    assert basis_determinant_abs(basis) == nf.q**nf.m
    assert exact_abs_det(rows_of(basis)) == nf.q**nf.m


@settings(deadline=None, max_examples=40)
@given(nf=normal_forms(), data=st.data())
def test_any_vector_satisfying_the_relation_is_in_the_qary_lattice(nf, data):
    """The converse direction. Rows satisfying the relation show the basis spans a *sub*lattice of
    the intended one; this shows it spans all of it, without going through the determinant.

    ``(A c + q z, c)`` for arbitrary integer ``c`` and ``z`` is the definition's general element,
    and a vector that violates the relation by one must be refused by the same solve.
    """
    n, m, q = nf.n, nf.m, nf.q
    a = a_of(nf)
    c = data.draw(st.lists(st.integers(-q, q), min_size=n, max_size=n))
    z = data.draw(st.lists(st.integers(-3, 3), min_size=m, max_size=m))
    vector = [sum(a[i][j] * c[j] for j in range(n)) + q * z[i] for i in range(m)] + c
    basis = build_qary_basis(nf)
    assert_in_lattice(vector, basis)

    vector[0] += 1
    with pytest.raises(NotInLattice):
        assert_in_lattice(vector, basis)


# ---------------------------------------------------------------------------------------------
# the embedded basis and the planted vector
# ---------------------------------------------------------------------------------------------


@settings(deadline=None, max_examples=40)
@given(nf=normal_forms(), factor=st.integers(min_value=1, max_value=50))
def test_the_planted_vector_is_in_the_embedded_lattice_for_every_instance(nf, factor):
    """The project's earliest falsifier, as a property rather than at nine fixed points.

    The returned coordinates are checked too: the planted vector is ``(b, 0, M) - (b - e, x, 0)``,
    so its coordinate on the embedding row is exactly ``+1``. A solve that reported membership with
    any other coefficient there would be describing a different vector.
    """
    basis = build_primal_embedding_basis(nf, embedding_factor=factor)
    planted = planted_short_vector(nf, embedding_factor=factor)
    coordinates = assert_in_lattice(planted, basis)
    assert coordinates[-1] == 1

    rows = rows_of(basis)
    rebuilt = [sum(coordinates[i] * rows[i][j] for i in range(len(rows))) for j in range(len(rows))]
    assert rebuilt == [int(v) for v in planted]


@settings(deadline=None, max_examples=40)
@given(nf=normal_forms(), factor=st.integers(min_value=1, max_value=50))
def test_the_planted_vector_is_the_instances_own_error_and_secret(nf, factor):
    """``(e, -x, M)``, and it satisfies the relation it is supposed to encode — independently.

    ``e - A(-x) == e + A x == b (mod q)``: the planted vector minus the target row is a q-ary
    lattice vector. Asserted from ``nf.a`` and ``nf.b`` directly, so a planted vector built from the
    wrong block or the wrong sign fails here even if ``src``'s solver were to accept it.
    """
    n, m, q = nf.n, nf.m, nf.q
    a = a_of(nf)
    planted = [int(v) for v in planted_short_vector(nf, embedding_factor=factor)]
    assert len(planted) == m + n + 1
    assert planted[-1] == factor
    e, minus_x = planted[:m], planted[m : m + n]
    for i in range(m):
        assert (e[i] - sum(a[i][j] * minus_x[j] for j in range(n)) - int(nf.b[i])) % q == 0
    assert planted_norm_squared(nf, embedding_factor=factor) == sum(v * v for v in planted)


@settings(deadline=None, max_examples=40)
@given(nf=normal_forms(), factor=st.integers(min_value=1, max_value=50))
def test_the_planted_vector_is_short_relative_to_the_modulus(nf, factor):
    """Every coordinate of ``e`` and ``x`` is inside the noise bound, which is at most ``q / 2`` —
    and strictly inside it at every divisor modulus. A planted vector with a coordinate of order
    ``q`` is a uniform vector, and the embedding would contain nothing to find."""
    planted = [int(v) for v in planted_short_vector(nf, embedding_factor=factor)]
    bound = nf.noise_bound
    assert all(abs(v) <= bound for v in planted[:-1])
    assert 2 * bound <= nf.q
    assert sum(v * v for v in planted) <= (nf.m + nf.n) * bound * bound + factor * factor


@st.composite
def well_sampled_production_shapes(draw):
    """``(nu, m, seed)`` with ``m >= 3 nu + 2``, so ``2 nu + 2`` samples survive the normal form."""
    nu = draw(st.integers(min_value=2, max_value=5))
    m = draw(st.integers(min_value=3 * nu + 2, max_value=3 * nu + 8))
    return nu, m, draw(st.integers(min_value=0, max_value=2**32 - 1))


@settings(deadline=None, max_examples=40)
@given(shape=well_sampled_production_shapes(), factor=st.integers(min_value=1, max_value=50))
def test_the_planted_vector_is_shorter_than_the_gaussian_heuristic(shape, factor):
    """At the production modulus pair, with at least ``2 nu + 2`` samples left after the normal form.

    That sample count is where the statement is a theorem rather than an observation: the embedded
    lattice then has ``vol^(1/d) >= q^(2/3) = 1625``, so the Gaussian heuristic exceeds
    ``sqrt(d) * 393``, while the planted vector is at most ``sqrt(d) * 128``. A planted vector that
    is *not* below the heuristic is not a unique-SVP target, whatever else holds.
    """
    nu, m, seed = shape
    normal_form = make_nf(nu, m, seed)
    assume(normal_form is not None)
    dimension = normal_form.m + normal_form.n + 1
    log_volume = normal_form.m * math.log(normal_form.q) + math.log(factor)
    planted_norm = math.sqrt(planted_norm_squared(normal_form, embedding_factor=factor))
    assert planted_norm < gaussian_heuristic(dimension, log_volume)


@settings(deadline=None, max_examples=40)
@given(nf=normal_forms(), factor=st.integers(min_value=1, max_value=50))
def test_the_embedded_determinant_is_q_to_the_sample_count_times_the_factor(nf, factor):
    basis = build_primal_embedding_basis(nf, embedding_factor=factor)
    assert basis.nrows == basis.ncols == nf.m + nf.n + 1
    assert basis_determinant_abs(basis) == nf.q**nf.m * factor
    assert exact_abs_det(rows_of(basis)) == nf.q**nf.m * factor


# ---------------------------------------------------------------------------------------------
# primal_embedding — the factor, the artifact, and the wrapper
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("factor", [1, 3, 17])
def test_the_artifact_norm_is_p_times_the_factor_at_a_divisor_modulus(factor):
    """``p * (b, 0, M) - (q t, 0, 0) = (0, ..., 0, p M)``, so the artifact has norm ``p * M`` — and
    it really is in the lattice, which is the claim the number stands for."""
    nf = make_nf(nu=4, m=12)
    assert artifact_norm(nf, factor) == PRODUCTION_P * factor

    basis = build_primal_embedding_basis(nf, embedding_factor=factor)
    artifact = [0] * (nf.m + nf.n) + [PRODUCTION_P * factor]
    assert_in_lattice(artifact, basis)
    # Non-vacuity, and minimality: no smaller multiple of M on the last coordinate is in the
    # lattice, so ``p * M`` is the artifact's norm and not merely *a* norm.
    for k in (1, 2, PRODUCTION_P - 1):
        with pytest.raises(NotInLattice):
            assert_in_lattice([0] * (nf.m + nf.n) + [k * factor], basis)


def test_there_is_no_artifact_at_a_non_divisor_modulus():
    """``q = 61, p = 19``: ``p * (q // p)`` is not a multiple of ``q``, the derivation has nothing
    to stand on, and the function reports 0 — confirmed against the lattice, not just the return."""
    nf = make_nf(nu=4, m=12, q=61, p=19)
    assert artifact_norm(nf, 5) == 0
    basis = build_primal_embedding_basis(nf, embedding_factor=5)
    with pytest.raises(NotInLattice):
        assert_in_lattice([0] * (nf.m + nf.n) + [19 * 5], basis)


def test_the_artifact_norm_is_p_times_the_factor_whenever_p_divides_q():
    """The docstring's condition is ``p | q``. ``q = 105, p = 7`` satisfies it with an odd ratio."""
    nf = make_nf(nu=4, m=12, q=105, p=7)
    basis = build_primal_embedding_basis(nf, embedding_factor=5)
    # The artifact is there — this half passes today, and is what makes the 0 below a wrong answer.
    assert_in_lattice([0] * (nf.m + nf.n) + [7 * 5], basis)
    assert artifact_norm(nf, 5) == 7 * 5


@pytest.mark.parametrize("nu,m", [(20, 48), (32, 76)])
@pytest.mark.parametrize("seed", SEEDS)
def test_the_minimum_embedding_factor_is_the_analytic_threshold(nu, m, seed):
    """``M > sqrt((||e||^2 + ||x||^2) / (p^2 - 1))``, the smallest such integer, and never below 2.

    Recomputed here from ``nf.e`` and ``nf.x``. The threshold is also checked from both sides,
    which the closed form alone would not show: at the returned ``M`` the artifact ``p * M`` is
    longer than the planted vector, and — wherever the floor of 2 is not what decided it — at
    ``M - 1`` it is not.
    """
    nf = make_nf(nu=nu, m=m, seed=seed)
    minimum = minimum_embedding_factor(nf)

    planted_without_m = sum(int(v) ** 2 for v in nf.e) + sum(int(v) ** 2 for v in nf.x)
    threshold = math.isqrt(planted_without_m // (PRODUCTION_P**2 - 1)) + 1
    assert minimum == max(2, threshold)
    assert minimum >= 2

    assert (PRODUCTION_P * minimum) ** 2 > planted_without_m + minimum**2
    if minimum > 2:
        below = minimum - 1
        assert (PRODUCTION_P * below) ** 2 <= planted_without_m + below**2


#: ``notes/05-embeddings.md``, "Measured calibration, stable across seeds", seeds 1 to 5 in order.
RECORDED_CALIBRATION = {(20, 48): [3, 3, 3, 2, 2], (32, 76): [3, 3, 3, 3, 3]}


@pytest.mark.parametrize("nu,m", sorted(RECORDED_CALIBRATION))
def test_the_calibrated_factor_is_stable_across_seeds_and_matches_the_record(nu, m):
    """Five seeds per shape, against the factors the note records.

    "Stable" is given a meaning that can fail: every factor is at least the analytic minimum, no
    seed walks more than one step above it, and the spread across seeds is at most one. The exact
    values are pinned as well — they are a measurement the report quotes.
    """
    factors = []
    for seed in SEEDS:
        nf = make_nf(nu=nu, m=m, seed=seed)
        factor, measurement = calibrate_embedding_factor(nf)
        minimum = minimum_embedding_factor(nf)
        assert minimum <= factor <= minimum + 1
        assert measurement["factor"] == factor
        assert measurement["analytic_lower_bound"] == minimum
        factors.append(factor)
    assert max(factors) - min(factors) <= 1
    assert factors == RECORDED_CALIBRATION[(nu, m)]


@pytest.mark.parametrize("seed", SEEDS)
def test_the_calibration_measurement_describes_the_factor_it_returns(seed):
    """The measurement goes into the run record, so each field is checked against a recomputation
    rather than for mere presence — and the property the calibration exists for is asserted: at the
    returned factor the artifact is longer than the planted vector, and at ``M = 1`` it is not."""
    nf = make_nf(nu=20, m=48, seed=seed)
    factor, measurement = calibrate_embedding_factor(nf)
    assert set(measurement) == {
        "factor",
        "analytic_lower_bound",
        "planted_norm_squared",
        "artifact_norm",
        "artifact_exceeds_planted",
        "verified_by_reduction_at_block_size",
    }
    planted = [int(v) for v in planted_short_vector(nf, embedding_factor=factor)]
    assert measurement["planted_norm_squared"] == sum(v * v for v in planted)
    assert measurement["artifact_norm"] == PRODUCTION_P * factor
    assert measurement["artifact_exceeds_planted"] is True
    assert measurement["artifact_norm"] ** 2 > measurement["planted_norm_squared"]

    # The M = 1 finding the calibration exists to prevent: artifact 256 against a planted ~500.
    assert artifact_norm(nf, 1) ** 2 < planted_norm_squared(nf, embedding_factor=1)


@pytest.mark.parametrize("factor", [1, 4, 9])
def test_kannan_embedding_places_the_target_row_and_the_factor(factor):
    """Shape ``(d+1) x (d+1)``; the q-ary basis in the top-left block; a zero last column above the
    target row; the target row ``(b mod q, 0, ..., 0, M)``."""
    nf = make_nf(nu=6, m=18, seed=3)
    n, m, q = nf.n, nf.m, nf.q
    d = n + m
    embedded = kannan_embedding(nf, embedding_factor=factor)
    assert (embedded.nrows, embedded.ncols) == (d + 1, d + 1)

    rows = rows_of(embedded)
    assert [row[:d] for row in rows[:d]] == rows_of(build_qary_basis(nf))
    assert [row[d] for row in rows[:d]] == [0] * d
    assert rows[d] == [int(v) % q for v in nf.b] + [0] * n + [factor]
    assert rows_of(build_primal_embedding_basis(nf, embedding_factor=factor)) == rows


def test_kannan_embedding_calibrates_when_no_factor_is_given():
    """The default is the calibrated factor — not 1, which is the silent failure the module
    docstring describes — and an explicit factor is honoured rather than re-calibrated."""
    nf = make_nf(nu=20, m=48, seed=1)
    calibrated, _ = calibrate_embedding_factor(nf)
    assert calibrated == 3
    d = nf.n + nf.m
    assert int(kannan_embedding(nf)[d, d]) == calibrated
    assert int(kannan_embedding(nf, embedding_factor=11)[d, d]) == 11


@pytest.mark.parametrize("factor", [0, -1])
def test_a_non_positive_embedding_factor_is_refused(factor):
    nf = make_nf(nu=4, m=12)
    with pytest.raises(ValueError, match="embedding_factor must be positive"):
        kannan_embedding(nf, embedding_factor=factor)
    with pytest.raises(ValueError, match="embedding_factor must be positive"):
        build_primal_embedding_basis(nf, embedding_factor=factor)


# ---------------------------------------------------------------------------------------------
# the dual lattice
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("nu,m", DUAL_SIZES)
@pytest.mark.parametrize("seed", SEEDS)
def test_both_dual_invariants_hold_across_four_sizes_and_five_seeds(nu, m, seed):
    """The sentence in ``notes/05``, as a test. At ``nu = 32`` the volume is a 155-digit integer."""
    nf = make_nf(nu=nu, m=m, seed=seed)
    dual = dual_basis(nf)
    assert_dual_valid(dual, build_qary_basis(nf), nf)
    assert dual_dimension(nf) == nf.m == dual.nrows == dual.ncols == m - nu


@pytest.mark.parametrize("nu,m", DUAL_SIZES)
@pytest.mark.parametrize("seed", SEEDS)
def test_every_dual_vector_annihilates_the_base_modulo_q(nu, m, seed):
    """``A^T y == 0 (mod q)`` for every row ``y`` — the definition in ``dual_basis``'s docstring,
    against ``nf.a`` in Python integers, with no primal basis and no ``src`` helper involved."""
    nf = make_nf(nu=nu, m=m, seed=seed)
    a = a_of(nf)
    for y in rows_of(dual_basis(nf)):
        assert len(y) == nf.m
        for j in range(nf.n):
            assert sum(a[i][j] * y[i] for i in range(nf.m)) % nf.q == 0


def _sample_block(nf) -> list[list[int]]:
    """The first ``m`` columns of the q-ary basis: ``n + m`` generators of ``{A c + q z}``."""
    return [row[: nf.m] for row in rows_of(build_qary_basis(nf))]


def _lattice_basis_from_generators(generators: list[list[int]], rank: int) -> list[list[int]]:
    """A basis of the lattice the generators span. LLL moves the dependencies to zero rows."""
    matrix = IntegerMatrix(len(generators), len(generators[0]), int_type="mpz")
    for i, row in enumerate(generators):
        for j, value in enumerate(row):
            matrix[i, j] = value
    LLL.reduction(matrix)
    rows = rows_of(matrix)
    n_zero = len(rows) - rank
    assert all(not any(row) for row in rows[:n_zero])
    return rows[n_zero:]


@pytest.mark.parametrize("nu,m,q,p", [(4, 12, PRODUCTION_Q, PRODUCTION_P), (8, 20, PRODUCTION_Q, PRODUCTION_P),
                                      (16, 40, PRODUCTION_Q, PRODUCTION_P), (4, 12, 105, 7), (4, 12, 61, 19)])
@pytest.mark.parametrize("seed", SEEDS)
def test_the_primal_and_dual_bases_satisfy_the_scaled_dual_relation(nu, m, q, p, seed):
    """``B_s D^T == 0 (mod q)`` entrywise, and for a *basis* ``P`` of the sample lattice
    ``P D^T = q U`` with ``U`` unimodular.

    The first statement is annihilation as a matrix identity over the whole generating set. The
    second is stronger and is the exact relation: ``src`` builds ``{y : A^T y == 0 (mod q)}``,
    which is ``q`` times the true dual of ``Lambda = {A c + q z}``, so ``P D^T / q`` must be an
    integer matrix of determinant ``+-1``. That pins the dual completely — a sublattice of it
    (volume too large) gives ``|det U| > 1`` — without consulting ``|det D|`` at all.
    """
    nf = make_nf(nu=nu, m=m, seed=seed, q=q, p=p)
    assert nf is not None
    dual = rows_of(dual_basis(nf))
    generators = _sample_block(nf)

    product = [[sum(g * y for g, y in zip(row, dual_row)) for dual_row in dual] for row in generators]
    assert all(value % q == 0 for row in product for value in row)

    primal = _lattice_basis_from_generators(generators, rank=nf.m)
    scaled = [[sum(g * y for g, y in zip(row, dual_row)) for dual_row in dual] for row in primal]
    assert all(value % q == 0 for row in scaled for value in row)
    assert exact_abs_det([[value // q for value in row] for row in scaled]) == 1

    # The two volumes, independently: det(P) * det(D) = q^m, with det(D) = q^n.
    assert exact_abs_det(primal) == q ** (nf.m - nf.n)
    assert exact_abs_det(dual) == q**nf.n


@settings(deadline=None, max_examples=30)
@given(nf=normal_forms(min_extra=4, max_extra=12))
def test_the_dual_is_valid_for_every_instance_and_modulus(nf):
    """The helper and the definition together, over random shapes and the non-power-of-two moduli
    ``assert_dual_valid`` had never been run at."""
    assume(nf.m >= nf.n)
    try:
        dual = dual_basis(nf)
    except PivotNotFound:
        assume(False)
    assert_dual_valid(dual, build_qary_basis(nf), nf)
    a = a_of(nf)
    for y in rows_of(dual):
        assert all(sum(a[i][j] * y[i] for i in range(nf.m)) % nf.q == 0 for j in range(nf.n))
    assert exact_abs_det(rows_of(dual)) == nf.q**nf.n


def _annihilates(dual, nf) -> bool:
    a = a_of(nf)
    return all(
        sum(a[i][j] * y[i] for i in range(nf.m)) % nf.q == 0
        for y in rows_of(dual)
        for j in range(nf.n)
    )


def _kernel_row_and_pivot_column(dual, nf) -> tuple[int, int]:
    """A kernel row (one holding the unit entry) and a pivot column (one holding ``q``)."""
    rows = rows_of(dual)
    pivot_column = next(j for j in range(nf.m) if rows[0][j] == nf.q)
    kernel_row = next(i for i, row in enumerate(rows) if 1 in row and nf.q not in row)
    return kernel_row, pivot_column


@pytest.mark.parametrize("seed", SEEDS)
def test_a_dual_row_outside_the_dual_is_caught_by_the_annihilation_check_alone(seed):
    """Corruption one: breaks annihilation, **preserves the volume**.

    Adding 1 to a kernel row's entry in a pivot column leaves the basis block-triangular with the
    same diagonal, so ``|det D|`` is still ``q^n`` — asserted, not assumed — and the volume check
    could not have been what fired. The row is no longer in the dual because ``A^T e_pivot`` is a
    row of an invertible matrix and so is not zero modulo ``q``.
    """
    nf = make_nf(nu=8, m=20, seed=seed)
    primal = build_qary_basis(nf)
    dual = dual_basis(nf)
    kernel_row, pivot_column = _kernel_row_and_pivot_column(dual, nf)
    dual[kernel_row, pivot_column] = int(dual[kernel_row, pivot_column]) + 1

    assert exact_abs_det(rows_of(dual)) == nf.q**nf.n
    assert not _annihilates(dual, nf)
    with pytest.raises(AssertionError, match="is not orthogonal to a primal sample row modulo q"):
        assert_dual_valid(dual, primal, nf)


@pytest.mark.parametrize("seed", SEEDS)
def test_a_dual_sublattice_is_caught_by_the_volume_check_alone(seed):
    """Corruption two: **preserves annihilation**, breaks the volume.

    Doubling a kernel row gives a vector that is still in the dual — the congruence is linear — so
    every row still annihilates, again asserted independently. What is left is an index-2
    sublattice, which only ``|det D| == q^n`` can see. This is the half the existing cross-check
    ``4b`` names and never exercises.
    """
    nf = make_nf(nu=8, m=20, seed=seed)
    primal = build_qary_basis(nf)
    dual = dual_basis(nf)
    kernel_row, _ = _kernel_row_and_pivot_column(dual, nf)
    for j in range(nf.m):
        dual[kernel_row, j] = 2 * int(dual[kernel_row, j])

    assert _annihilates(dual, nf)
    assert exact_abs_det(rows_of(dual)) == 2 * nf.q**nf.n
    with pytest.raises(AssertionError, match=r"\|det D\| = \d+, expected q\^n"):
        assert_dual_valid(dual, primal, nf)


def test_a_dual_basis_of_the_wrong_shape_is_refused():
    nf = make_nf(nu=4, m=12)
    too_small = IntegerMatrix(nf.m - 1, nf.m - 1, int_type="mpz")
    with pytest.raises(ValueError, match="dual basis is 7x7, expected 8x8"):
        assert_dual_valid(too_small, build_qary_basis(nf), nf)


def test_the_dual_dimension_is_the_sample_count_not_the_secret_dimension():
    nf = make_nf(nu=4, m=12)
    assert (nf.n, nf.m) == (4, 8)
    assert dual_dimension(nf) == 8
    assert np.array(rows_of(dual_basis(nf)), dtype=object).shape == (8, 8)
