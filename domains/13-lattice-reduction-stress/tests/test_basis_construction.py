"""The lattice construction, and the checks that decide whether it is the right lattice.

The design document names the hazard directly: a wrong lattice reduces perfectly. A transposed
base, a stale ``qI`` block or a sign error all yield a full-rank lattice of the right determinant
that BKZ reduces happily, producing a root-Hermite factor indistinguishable from a correct one.
There is no downstream signal — which is why the checks here run *before* any reduction exists.

Two of them fail for different bugs and are therefore both required. The structural check verifies
the definition row by row; the volumetric check catches a basis that satisfies the definition
row-wise while spanning a sublattice or superlattice.

Every check is also shown to be **non-vacuous**: a corrupted basis must be caught, and a corrupted
planted vector must be rejected. A correctness test that has never failed is indistinguishable from
one that cannot.
"""

from __future__ import annotations

import random

import numpy as np
import pytest

from qlwr_lattice_stress.lattice._exact import NotInLattice, det_abs, solve_integer
from qlwr_lattice_stress.lattice.basis_construction import (
    assert_basis_valid,
    basis_determinant_abs,
    build_primal_embedding_basis,
    build_qary_basis,
)
from qlwr_lattice_stress.lattice.planted_vector import (
    assert_in_lattice,
    is_recovered,
    planted_norm_squared,
    planted_short_vector,
    recovered_from_coordinates,
)
from qlwr_lattice_stress.problem.normal_form import to_normal_form
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8

#: A dimension calibrated to be non-vacuous. At ``nu = 4, m = 12`` the lattice is 12-dimensional
#: and trivially reducible; the sizes below keep the membership check cheap while still exercising
#: the block structure at a scale where an off-by-one would show.
SIZES = [(4, 12), (8, 20), (16, 40)]


def make_nf(nu=8, m=20, seed=1, q=PRODUCTION_Q, p=PRODUCTION_P):
    rng = random.Random(seed)
    while True:
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    inst = LatticeQLWRInstance(
        nu=nu, q_l=q, p=p, m=m,
        secret_s=tuple(rng.randrange(q) for _ in range(nu)), base=base, seed=seed,
    )
    return to_normal_form(inst)


# ---------------------------------------------------------------------------------------------
# M4 — the earliest falsifier in the project
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("nu,m", SIZES)
@pytest.mark.parametrize("embedding_factor", [1, 2, 100])
def test_the_planted_vector_is_in_the_embedded_lattice(nu, m, embedding_factor):
    """One exact rational solve, seconds, at any dimension, **with no reduction run at all**.

    If this fails the construction is wrong and the failure is localised to this module, because
    nothing else has run yet. That is what makes it worth doing first.
    """
    nf = make_nf(nu=nu, m=m)
    basis = build_primal_embedding_basis(nf, embedding_factor=embedding_factor)
    planted = planted_short_vector(nf, embedding_factor=embedding_factor)
    coordinates = assert_in_lattice(planted, basis)
    # And the coordinates really do reproduce it, so the solve is not merely reporting success.
    assert recovered_from_coordinates(coordinates, basis) == tuple(int(v) for v in planted)


@pytest.mark.parametrize("nu,m", [(4, 12), (8, 20)])
def test_the_planted_vector_is_in_the_lattice_across_seeds(nu, m):
    """A pass on one seed is an anecdote; the instance is randomised, so the construction must hold
    for every draw."""
    for seed in range(1, 8):
        nf = make_nf(nu=nu, m=m, seed=seed)
        basis = build_primal_embedding_basis(nf, embedding_factor=7)
        planted = planted_short_vector(nf, embedding_factor=7)
        assert_in_lattice(planted, basis)


def test_a_corrupted_planted_vector_is_rejected():
    """**Non-vacuity.** If the membership check accepted anything, the gate above would pass on a
    broken construction. Perturbing one coordinate must be caught."""
    nf = make_nf(nu=4, m=12)
    basis = build_primal_embedding_basis(nf, embedding_factor=5)
    planted = planted_short_vector(nf, embedding_factor=5)
    planted[0] = int(planted[0]) + 1
    with pytest.raises(NotInLattice):
        assert_in_lattice(planted, basis)


def test_a_vector_in_the_rational_span_but_not_the_lattice_is_rejected():
    """The distinction the exact solve exists for: a vector that is *close* to the lattice is not
    in it, and a tolerance-based check would accept it."""
    basis = np.array([[2, 0], [0, 2]], dtype=object)
    with pytest.raises(NotInLattice, match="not the integer lattice"):
        solve_integer(basis, [1, 0])


def test_solve_integer_round_trips_a_known_combination():
    basis = np.array([[1, 2, 3], [0, 1, 4], [5, 6, 0]], dtype=object)
    coords = (3, -2, 7)
    target = tuple(sum(coords[i] * int(basis[i][j]) for i in range(3)) for j in range(3))
    assert solve_integer(basis, target) == coords


# ---------------------------------------------------------------------------------------------
# the basis, and its two independent checks
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("nu,m", SIZES)
def test_the_qary_basis_passes_both_checks(nu, m):
    nf = make_nf(nu=nu, m=m)
    basis = build_qary_basis(nf)
    assert_basis_valid(basis, nf)
    assert basis_determinant_abs(basis) == nf.q**nf.m


@pytest.mark.parametrize("nu,m", SIZES)
def test_the_embedded_basis_has_the_expected_volume(nu, m):
    """``|det| = q^m * M`` — the embedding adds one row and one column, scaling the volume by the
    embedding factor exactly."""
    nf = make_nf(nu=nu, m=m)
    for factor in (1, 3, 97):
        basis = build_primal_embedding_basis(nf, embedding_factor=factor)
        assert basis_determinant_abs(basis) == nf.q**nf.m * factor


def test_a_structurally_broken_basis_is_caught():
    """**Non-vacuity of the structural check.** Adding one to a single sample coordinate breaks the
    modular relation for that row."""
    from fpylll import IntegerMatrix

    nf = make_nf(nu=4, m=12)
    basis = build_qary_basis(nf)
    corrupted = IntegerMatrix(basis.nrows, basis.ncols, int_type="mpz")
    for i in range(basis.nrows):
        for j in range(basis.ncols):
            corrupted[i, j] = int(basis[i, j])
    corrupted[0, 0] = int(corrupted[0, 0]) + 1
    with pytest.raises(AssertionError, match="not in the lattice"):
        assert_basis_valid(corrupted, nf)


def test_a_wrong_volume_is_caught_by_the_volumetric_check_alone():
    """**Non-vacuity of the volumetric check, independently.**

    Scaling one ``q`` row keeps every row structurally valid — it is still a multiple of ``q`` —
    while changing the volume. The structural check passes and the volumetric one must fail, which
    is why both exist rather than one.
    """
    from fpylll import IntegerMatrix

    nf = make_nf(nu=4, m=12)
    basis = build_qary_basis(nf)
    corrupted = IntegerMatrix(basis.nrows, basis.ncols, int_type="mpz")
    for i in range(basis.nrows):
        for j in range(basis.ncols):
            corrupted[i, j] = int(basis[i, j])
    # Double a modular row: still congruent to zero, so still a valid lattice element, but it no
    # longer generates the same lattice.
    for j in range(basis.ncols):
        corrupted[nf.n, j] = 2 * int(corrupted[nf.n, j])

    with pytest.raises(AssertionError, match="volume|det"):
        assert_basis_valid(corrupted, nf)


def test_a_basis_of_the_wrong_shape_is_refused():
    nf = make_nf(nu=4, m=12)
    with pytest.raises(ValueError, match="expected"):
        assert_basis_valid(build_primal_embedding_basis(nf, embedding_factor=1), nf)


# ---------------------------------------------------------------------------------------------
# recovery
# ---------------------------------------------------------------------------------------------


def test_recovery_is_exact_integer_equality_not_a_norm():
    """A vector of the right length is a different vector. Accepting one would let a basis that
    found something else entirely pass as a success."""
    planted = np.array([1, 2, 3], dtype=object)
    assert is_recovered(np.array([[1, 2, 3]], dtype=object), planted)
    assert is_recovered(np.array([[-1, -2, -3]], dtype=object), planted)
    assert not is_recovered(np.array([[1, 2, 4]], dtype=object), planted)
    assert not is_recovered(np.array([[2, 4, 6]], dtype=object), planted)


def test_the_planted_norm_grows_with_the_embedding_factor():
    """``||(e, -x, M)||^2 = ||e||^2 + ||x||^2 + M^2`` — the embedding factor is added in quadrature,
    which is what makes the choice a real trade-off rather than a free parameter."""
    nf = make_nf(nu=4, m=12)
    base = planted_norm_squared(nf, embedding_factor=0)
    for m_factor in (1, 10, 100):
        assert planted_norm_squared(nf, embedding_factor=m_factor) == base + m_factor**2


# ---------------------------------------------------------------------------------------------
# the exact helpers
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "matrix,expected",
    [
        ([[1, 0], [0, 1]], 1),
        ([[2, 0], [0, 3]], 6),
        ([[0, 1], [1, 0]], 1),
        ([[2, 0], [0, 2]], 4),
        ([[1, 2], [3, 4]], 2),
        ([[1, 2], [2, 4]], 0),
    ],
)
def test_det_abs_is_exact(matrix, expected):
    assert det_abs(np.array(matrix, dtype=object)) == expected


def test_det_abs_is_not_a_float_determinant():
    """At these magnitudes a float determinant rounds. The check compares against ``q**m`` exactly,
    and a check that rounds is a check that can agree with a wrong basis."""
    n = 12
    matrix = np.eye(n, dtype=object) * 65536
    assert det_abs(matrix) == 65536**n


def test_solve_integer_refuses_an_inconsistent_system():
    basis = np.array([[1, 0], [0, 2]], dtype=object)
    with pytest.raises(NotInLattice):
        solve_integer(basis, [1, 1])
