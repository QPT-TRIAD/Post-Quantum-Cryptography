"""The root-Hermite factor against values that are known exactly, rather than against itself.

``delta = (||b1|| / |det B|^(1/d))^(1/d)`` is the project's one quality metric for a reduction, and
until this module nothing had compared it with a number somebody had worked out by hand. The checks
that existed were agreements: the exact route against the GSO route, and the engine's figure
against a test helper that restated the engine's own formula. An agreement between two
implementations that share an error is not evidence, and both pairs shared one (both were fixed
on 2026-09-20; see ``notes/10-test-completion-audit.md``):

* both analysis routes took the leading norm through ``math.isqrt``, which **floors** it. The
  lattice ``[[1, 1], [-1, 1]]`` has ``||b1|| = sqrt(2)`` and ``det = 2``, so its factor is exactly
  1; flooring the norm to 1 gave ``1 / 2^(1/4) = 0.8409`` from *both* routes, in agreement.
* the engine layer's ``root_hermite_factor`` returned ``||b0|| / det^(1/d)`` — the Hermite factor,
  with no ``d``-th root — and the helper in ``test_fpylll_bkz_engine.py`` omitted the same root. At
  dimension 40 the engine reported 1.68 where the rooted value is 1.013.

So every expectation below is computed *in this file*, by a route that shares nothing with ``src``:
a determinant by rational Gaussian elimination (``src`` uses Bareiss), and the roots in 50-digit
``mpmath`` arithmetic. The tests that pinned the two defects were ``xfail(strict=True)`` until
``src`` was corrected; they pass now, unchanged, and the markers are gone.
"""

from __future__ import annotations

import random
from fractions import Fraction

import mpmath
import pytest
from fpylll import LLL
from hypothesis import given, settings
from hypothesis import strategies as st

from engine_helpers import matrix_rows, qary_basis, squared_norms, to_integer_matrix
from qlwr_lattice_stress.analysis.hermite_factor import (
    achieved_root_hermite_factor,
    hermite_factor_from_gso,
)
from qlwr_lattice_stress.attacks import prepare_primal, run_primal_attack
from qlwr_lattice_stress.engines import FpylllBKZEngine
from qlwr_lattice_stress.engines.base_engine import root_hermite_factor
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)

#: Historical: the defect as it stood before it was fixed on 2026-09-20, kept as the record of what
#: the tests below were written against. It was the xfail reason; nothing reads it now.
ISQRT_DEFECT = (
    "src/qlwr_lattice_stress/analysis/hermite_factor.py:54 (exact route) and :89 (GSO route) take "
    "the leading norm with math.isqrt, which floors it: sqrt(2) becomes 1, so [[1,1],[-1,1]] "
    "reports 0.8409 instead of 1.0. Both routes share the floor, so their agreement cannot see it."
)
UNROOTED_DEFECT = (
    "src/qlwr_lattice_stress/engines/base_engine.py:410 returns exp(log||b0|| - log_det/d), i.e. "
    "||b0|| / det^(1/d) with no d-th root — the Hermite factor under the name of its root. A "
    "BKZ-20 basis at dimension 40 reports 1.68 where the rooted value is 1.013."
)

#: Bases whose leading norm is an integer, so flooring it changes nothing. All have factor exactly 1.
INTEGER_NORM_CASES = [
    pytest.param([[1, 0], [0, 1]], id="identity-2"),
    pytest.param([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], id="identity-4"),
    pytest.param([[7, 0, 0], [0, 7, 0], [0, 0, 7]], id="7I-3"),
    pytest.param([[65536, 0], [0, 65536]], id="qI-2"),
    # Norm 5, determinant 25: a rotation of 5*I, so the factor is 1 without being diagonal.
    pytest.param([[3, 4], [-4, 3]], id="rotated-5I"),
]


# ---------------------------------------------------------------------------------------------
# the independent reference
# ---------------------------------------------------------------------------------------------


def exact_abs_determinant(rows) -> int:
    """``|det|`` by Gaussian elimination over the rationals — deliberately *not* Bareiss.

    ``src`` computes its determinant by fraction-free elimination in ``lattice/_exact.py``. Using a
    different algorithm here means a defect in that one cannot reproduce itself in the reference.
    """
    a = [[Fraction(int(v)) for v in row] for row in rows]
    n = len(a)
    det = Fraction(1)
    for col in range(n):
        pivot = next((r for r in range(col, n) if a[r][col] != 0), None)
        if pivot is None:
            return 0
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
            det = -det
        det *= a[col][col]
        for r in range(col + 1, n):
            factor = a[r][col] / a[col][col]
            if factor:
                a[r] = [x - factor * y for x, y in zip(a[r], a[col])]
    assert det.denominator == 1, "an integer matrix has an integer determinant"
    return abs(int(det))


def reference_root_hermite_factor(basis, *, leading: str = "shortest") -> float:
    """``(||b|| / |det|^(1/d))^(1/d)`` in 50-digit arithmetic, from exact integers.

    ``leading`` selects which row supplies ``||b||``: the shortest one (the analysis layer's
    documented choice) or row zero (the engine layer's). On a reduced basis they coincide, and the
    tests that compare the layers assert that they do rather than assuming it.
    """
    rows = [[int(v) for v in row] for row in matrix_rows(basis)] if hasattr(basis, "nrows") else [
        [int(v) for v in row] for row in basis
    ]
    d = len(rows)
    norms_squared = [sum(v * v for v in row) for row in rows]
    norm_squared = min(norms_squared) if leading == "shortest" else norms_squared[0]
    with mpmath.workdps(50):
        log_norm = mpmath.log(mpmath.mpf(norm_squared)) / 2
        log_det = mpmath.log(mpmath.mpf(exact_abs_determinant(rows)))
        return float(mpmath.exp((log_norm - log_det / d) / d))


def test_the_reference_reproduces_a_value_derived_by_hand():
    """The reference is itself checked, against algebra rather than against code.

    ``[[1,1,0],[0,1,1],[1,0,1]]`` has every row of norm ``sqrt(2)`` and determinant 2, so
    ``delta = (2^(1/2) / 2^(1/3))^(1/3) = 2^(1/18)``. A reference that was wrong in the same
    direction as ``src`` would make every comparison below meaningless.
    """
    assert exact_abs_determinant([[1, 1, 0], [0, 1, 1], [1, 0, 1]]) == 2
    assert reference_root_hermite_factor([[1, 1, 0], [0, 1, 1], [1, 0, 1]]) == pytest.approx(
        1.0392592260318434, abs=1e-15
    )
    assert reference_root_hermite_factor([[3, 4], [-4, 3]]) == pytest.approx(1.0, abs=1e-15)


# ---------------------------------------------------------------------------------------------
# route 1 — achieved_root_hermite_factor
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("rows", INTEGER_NORM_CASES)
def test_the_exact_route_gives_one_on_a_scaled_orthonormal_basis(rows):
    """``k * (orthonormal)`` has ``||b1|| = k`` and ``det = k^d``, so the factor is exactly 1.

    These pass today because every leading norm here is an integer. They are the anchor that the
    irrational cases below are compared against: same function, same lattice shape, and the only
    thing that changes is whether the norm survives being floored.
    """
    assert achieved_root_hermite_factor(rows) == pytest.approx(1.0, abs=1e-12)
    assert achieved_root_hermite_factor(to_integer_matrix(rows)) == pytest.approx(1.0, abs=1e-12)


def test_the_exact_route_gives_one_when_the_norm_is_irrational():
    """``[[1,1],[-1,1]]`` is ``sqrt(2)`` times a rotation: norm ``sqrt(2)``, determinant 2, factor 1.

    It is the same lattice shape as ``[[3,4],[-4,3]]`` above — which passes — with a leading norm
    that is not an integer. A factor *below* 1 on an orthogonal basis is impossible, which is what
    makes 0.8409 recognisably wrong rather than merely different.
    """
    assert achieved_root_hermite_factor([[1, 1], [-1, 1]]) == pytest.approx(1.0, abs=1e-12)


def test_the_exact_route_matches_a_hand_computed_three_dimensional_value():
    """Norm ``sqrt(2)``, determinant 2, dimension 3: ``delta = 2^((1/2 - 1/3)/3) = 2^(1/18)``."""
    expected = 2.0 ** (1.0 / 18.0)
    assert expected == pytest.approx(1.0392592260318434, abs=1e-15)
    assert achieved_root_hermite_factor([[1, 1, 0], [0, 1, 1], [1, 0, 1]]) == pytest.approx(
        expected, abs=1e-12
    )


def test_the_exact_route_uses_the_shortest_row_not_row_zero():
    """Documented behaviour, pinned with integer norms so it is independent of the rounding defect.

    Rows of norm 5 and 3 with determinant 15: the factor from the shortest row is
    ``(3 / sqrt(15))^(1/2)``; from row zero it would be ``(5 / sqrt(15))^(1/2)``.
    """
    basis = [[5, 0], [0, 3]]
    assert achieved_root_hermite_factor(basis) == pytest.approx((3 / 15**0.5) ** 0.5, abs=1e-12)
    assert achieved_root_hermite_factor(basis) == pytest.approx(
        reference_root_hermite_factor(basis), abs=1e-12
    )


def test_the_exact_route_refuses_bases_that_have_no_factor():
    with pytest.raises(ValueError, match="empty basis"):
        achieved_root_hermite_factor([])
    with pytest.raises(ValueError, match="zero vector"):
        achieved_root_hermite_factor([[0, 0], [1, 1]])
    with pytest.raises(ValueError, match="singular"):
        achieved_root_hermite_factor([[1, 2], [2, 4]])


# ---------------------------------------------------------------------------------------------
# route 2 — hermite_factor_from_gso, on the same inputs
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("rows", INTEGER_NORM_CASES)
def test_the_gso_route_gives_one_on_a_scaled_orthonormal_basis(rows):
    assert hermite_factor_from_gso(to_integer_matrix(rows)) == pytest.approx(1.0, abs=1e-12)


def test_the_gso_route_gives_one_when_the_norm_is_irrational():
    assert hermite_factor_from_gso(to_integer_matrix([[1, 1], [-1, 1]])) == pytest.approx(
        1.0, abs=1e-12
    )


def test_the_gso_route_matches_a_hand_computed_three_dimensional_value():
    basis = to_integer_matrix([[1, 1, 0], [0, 1, 1], [1, 0, 1]])
    assert hermite_factor_from_gso(basis) == pytest.approx(2.0 ** (1.0 / 18.0), abs=1e-12)


# ---------------------------------------------------------------------------------------------
# the cross-check, made three-cornered so a shared error is visible
# ---------------------------------------------------------------------------------------------


def _assert_both_routes_equal_the_reference(basis) -> None:
    exact = achieved_root_hermite_factor(basis)
    gso = hermite_factor_from_gso(basis)
    reference = reference_root_hermite_factor(basis)
    # The two-cornered check that already existed. It holds today, and that is the problem with it.
    assert exact == pytest.approx(gso, rel=1e-12)
    # The third corner. Two routes agreeing with each other *and* with a number computed without
    # either of them is the statement the project's cross-check 5 claims to make.
    assert exact == pytest.approx(reference, rel=1e-12)
    assert gso == pytest.approx(reference, rel=1e-12)


@pytest.mark.parametrize("rows", INTEGER_NORM_CASES)
def test_both_routes_equal_the_independent_value_when_the_norm_is_an_integer(rows):
    _assert_both_routes_equal_the_reference(to_integer_matrix(rows))


@pytest.mark.parametrize(
    "rows",
    [
        pytest.param([[1, 1], [-1, 1]], id="sqrt2-rotation"),
        pytest.param([[1, 1, 0], [0, 1, 1], [1, 0, 1]], id="three-dim-sqrt2"),
        pytest.param([[2, 1], [1, 3]], id="norm-sqrt5-det-5"),
    ],
)
def test_both_routes_equal_the_independent_value_when_the_norm_is_irrational(rows):
    _assert_both_routes_equal_the_reference(to_integer_matrix(rows))


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_both_routes_equal_the_independent_value_on_a_reduced_qary_basis(seed):
    """The case the metric is actually used on, at the production modulus.

    Here the floor is small — a norm near ``10^4`` loses under one part in ``10^4``, and the
    ``d``-th root shrinks that to about ``10^-6`` on the factor — which is exactly why it went
    unnoticed. It is still eight orders of magnitude above the ``4e-16`` agreement the module
    docstring quotes between its two routes, so a tolerance that tight can only be honest if the
    norm is not floored.
    """
    basis = qary_basis(20, seed=seed)
    LLL.reduction(basis)
    _assert_both_routes_equal_the_reference(basis)


@settings(deadline=None, max_examples=60)
@given(
    k=st.integers(min_value=1, max_value=10**6),
    d=st.integers(min_value=1, max_value=6),
    seed=st.integers(min_value=0, max_value=2**16),
)
def test_a_scaled_signed_permutation_always_has_factor_one(k, d, seed):
    """Property form of the anchor: ``k * P`` for a signed permutation ``P`` has factor exactly 1.

    Integer norms throughout, so this holds whatever happens to the rounding defect, and it pins
    that the determinant route is insensitive to row order and sign.
    """
    rng = random.Random(seed)
    columns = list(range(d))
    rng.shuffle(columns)
    rows = [[0] * d for _ in range(d)]
    for i, j in enumerate(columns):
        rows[i][j] = k * rng.choice((-1, 1))
    assert achieved_root_hermite_factor(rows) == pytest.approx(1.0, abs=1e-12)
    assert hermite_factor_from_gso(to_integer_matrix(rows)) == pytest.approx(1.0, abs=1e-12)


# ---------------------------------------------------------------------------------------------
# the engine layer must report the same quantity under the same name
# ---------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def reduced_forty():
    """One real BKZ-20 reduction of a generic 40-dimensional q-ary basis, single-threaded."""
    return FpylllBKZEngine(threads=1).reduce(qary_basis(40), 20)


def _make_instance(nu: int, m: int, seed: int) -> LatticeQLWRInstance:
    q, p = 1 << 16, 1 << 8
    rng = random.Random(seed)
    while True:
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    return LatticeQLWRInstance(
        nu=nu, q_l=q, p=p, m=m,
        secret_s=tuple(rng.randrange(q) for _ in range(nu)), base=base, seed=seed,
    )


def test_the_engine_helper_gives_one_on_a_scaled_orthonormal_basis():
    """Where rooted and un-rooted coincide — ``1^(1/d) = 1`` — the helper is right, and passes.

    Recorded so the failures below are read correctly: the helper's Gram-Schmidt volume and its
    leading norm are fine. What is missing is only the final root.
    """
    for rows in ([[1, 0], [0, 1]], [[3, 4], [-4, 3]], [[1, 1], [-1, 1]], [[7, 0, 0], [0, 7, 0], [0, 0, 7]]):
        assert root_hermite_factor(to_integer_matrix(rows)) == pytest.approx(1.0, abs=1e-12)


def test_the_engine_helper_matches_a_hand_computed_three_dimensional_value():
    """``2^(1/18) = 1.03926``. The un-rooted quantity is ``2^(1/6) = 1.12246``, which is what comes
    back today."""
    basis = to_integer_matrix([[1, 1, 0], [0, 1, 1], [1, 0, 1]])
    assert root_hermite_factor(basis) == pytest.approx(2.0 ** (1.0 / 18.0), abs=1e-12)


def test_the_engine_helper_equals_the_analysis_layer_on_the_same_reduced_basis(reduced_forty):
    """Two layers, one name, one basis — so one number.

    The engine reads row zero and the analysis layer the shortest row; on a BKZ-reduced basis those
    are the same row, which is asserted rather than assumed. The comparison with the analysis layer
    is held to ``1e-4`` so that it isolates *this* defect from the norm-flooring one (worth about
    ``1e-6`` here); the comparison with the independent value is held tight.
    """
    norms = squared_norms(reduced_forty.basis)
    assert norms[0] == min(norms)

    from_engine = root_hermite_factor(reduced_forty.basis)
    assert from_engine == pytest.approx(
        reference_root_hermite_factor(reduced_forty.basis, leading="row_zero"), rel=1e-9
    )
    assert from_engine == pytest.approx(achieved_root_hermite_factor(reduced_forty.basis), rel=1e-4)


def test_a_reduction_result_carries_a_rooted_factor_in_the_physical_window(reduced_forty):
    """LLL achieves about 1.022 and BKZ-20 about 1.013; nothing achieves below 1 on a generic
    lattice, and nothing a reduction returns is as bad as 1.03. The un-rooted 1.68 is outside any
    window a reader of the report would recognise as a root-Hermite factor."""
    reported = reduced_forty.root_hermite_factor
    assert reported is not None
    assert reported == pytest.approx(
        reference_root_hermite_factor(reduced_forty.basis, leading="row_zero"), rel=1e-9
    )
    assert 1.0 < reported < 1.03


def test_the_independent_value_for_that_reduction_is_itself_in_the_window(reduced_forty):
    """Non-vacuity for the window: the reference lands inside it on the very basis the engine
    returned, so the xfail above is a statement about the engine's number and not about the window
    being mis-set. Also pins that un-rooting the engine's figure recovers the reference — i.e. the
    defect is the missing root and nothing else."""
    reference = reference_root_hermite_factor(reduced_forty.basis, leading="row_zero")
    assert 1.0 < reference < 1.03
    d = reduced_forty.basis.nrows
    reported = reduced_forty.root_hermite_factor
    # Holds whether the engine reports the rooted value (after the fix) or the un-rooted one
    # (today): one of the two readings of its number must be the reference.
    assert reference == pytest.approx(reported, rel=1e-9) or reference == pytest.approx(
        reported ** (1.0 / d), rel=1e-9
    )


def test_a_primal_attack_result_carries_the_same_rooted_factor():
    """The figure that reaches ``metrics.json`` and section 3 of the report.

    ``PrimalAttackResult`` does not carry the reduced basis, so the reference is computed from a
    second, identical reduction of the same prepared basis — fpylll is deterministic, and that the
    two reductions agree is asserted through the engine's own figure first. The embedded lattice
    is 41-dimensional (``m = 40`` plus the embedding row).

    The shape is ``nu = 20, m = 40`` on purpose. The window ``(1.0, 1.03)`` is a fact about
    reductions of lattices whose row zero is a *reduction's* output; a recovered planted vector is
    shorter than that by construction, and at ``nu = 17`` it is shorter than ``det^(1/d)`` itself,
    giving a correct rooted factor of 0.9977. With 20 samples left after the normal form the
    planted vector (norm about 470) is longer than the Gaussian heuristic (about 350), is not
    recovered, and row zero is an ordinary BKZ-10 vector: 1.0175.
    """
    instance = _make_instance(nu=20, m=40, seed=1)
    prepared = prepare_primal(instance)
    engine = FpylllBKZEngine(threads=1)

    result = run_primal_attack(instance, engine, 10, prepared=prepared)
    again = engine.reduce(prepared[2], 10)
    assert result.root_hermite_factor == again.root_hermite_factor
    assert result.dimension == 41

    reference = reference_root_hermite_factor(again.basis, leading="row_zero")
    assert result.root_hermite_factor == pytest.approx(reference, rel=1e-9)
    assert not result.recovered
    assert 1.0 < reference < 1.03
    assert 1.0 < result.root_hermite_factor < 1.03
