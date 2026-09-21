"""The lattice-preservation invariant, and the proof that checking it is not vacuous.

A reduction that silently changed the lattice would leave every other signal intact. The returned
basis is square, integer, full rank and reduces perfectly well; the root-Hermite factor computed
from it is plausible to several decimal places; the run's timing, tour count and provenance are all
correct. Nothing per-engine can see it, because per-engine tests compare an engine against its own
conventions. This is the lattice form of the defect that survived a whole test suite in the sibling
project because every layer was individually correct and the error lived only in a boundary.

So this module does two jobs. It checks the invariant on real engine output, and — more
importantly — it aims at the check itself, from several directions, to show that it fails when it
should. A boundary check that has only ever been observed passing is a check nobody has any reason
to believe: the corruption tests below are the evidence, and the "nearby modulus" one is the exact
scenario the project's own prose describes, an instance that reduces just as well and reports just
as plausible a number while being a different lattice.
"""

from __future__ import annotations

import math
import re

import pytest
from fpylll import LLL, SVP, IntegerMatrix

from engine_helpers import (  # type: ignore[import-not-found]
    CorruptingEngine,
    DEFAULT_Q,
    NoOpEngine,
    min_squared_norm,
    qary_basis,
    squared_norms,
    to_integer_matrix,
)
from qlwr_lattice_stress.engines.base_engine import (
    LatticePreservationError,
    assert_same_lattice,
    matrix_rows,
    root_hermite_factor,
)
from qlwr_lattice_stress.engines.fpylll_bkz_engine import FpylllBKZEngine
from qlwr_lattice_stress.engines.g6k_sieve_engine import G6KSieveEngine

DIMENSION = 40
BLOCK_SIZE = 40

#: Calibrated against this instance as constructed by :func:`engine_helpers.qary_basis`, measured:
#: LLL alone reaches ``min ||b_i||^2 = 262767``, the true shortest vector has ``||.||^2 = 170242``.
#: Both numbers are properties of a seeded instance and are stable across runs; they are written out
#: rather than computed so that a change in one of them is a test failure rather than a silent
#: re-baselining of every assertion in this module.
LLL_SQUARED_NORM = 262767
SHORTEST_SQUARED_NORM = 170242

#: The reported root-Hermite factor of the block-size-40 run, and of the same basis with one entry
#: perturbed by one. Measured: they differ by 2.2e-6 relative — which is the entire point of the
#: corruption test below.
#:
#: Re-pinned 2026-09-20. These were ``1.6117340871180106`` and ``1.6118745183768928`` (8.7e-5
#: apart): the *un-rooted* Hermite factor, which ``root_hermite_factor`` returned under this name
#: until it was given its ``d``-th root. The new values are the 40th roots of the old ones — the
#: same two bases, the quantity the name promises — and the perturbation is forty times harder to
#: see, which strengthens the argument below rather than weakening it.
REDUCED_HERMITE_FACTOR = 1.0120042462977306
PERTURBED_HERMITE_FACTOR = 1.0120064506159738


# -- the invariant, on real engine output -------------------------------------------------------


def test_an_engine_result_spans_the_input_lattice():
    """The statement the engines make about themselves, restated from outside them."""
    engine = FpylllBKZEngine()
    basis = qary_basis(DIMENSION)
    before = matrix_rows(basis)
    result = engine.reduce(basis, 20)
    assert_same_lattice(before, result.basis)
    assert result.dimension == DIMENSION


def test_a_run_that_converged_without_reducing_still_spans_the_input_lattice():
    """The trivial case, which is the one an implementation is most likely to short-circuit away.

    At block size 2 a tour redoes what LLL already did: the basis comes back LLL-reduced and
    unchanged, and the run reports ``converged=True``. An engine that skipped the check when the
    basis was unchanged would be correct here and untested everywhere else — and this is the exact
    input where the base class's identity short-circuit fires, so the test would be vacuous if the
    check were only in the non-identity path.
    """
    engine = FpylllBKZEngine()
    basis = qary_basis(DIMENSION)
    before = matrix_rows(basis)
    result = engine.reduce(basis, 2)
    assert result.converged is True

    lll_only = IntegerMatrix(basis)
    LLL.reduction(lll_only)
    assert matrix_rows(result.basis) == matrix_rows(lll_only)
    assert_same_lattice(before, result.basis)


def test_every_engine_runs_the_check_before_returning():
    """A third engine cannot bypass the check by being written somewhere else.

    ``reduce`` is a template method, so the check belongs to the base class rather than to each
    engine. This stub returns a basis that differs from its input by one entry — a change no check
    internal to the engine could detect — and the base class must refuse to return it.
    """
    engine = CorruptingEngine()
    basis = qary_basis(DIMENSION)
    with pytest.raises(LatticePreservationError, match="not the lattice spanned by the input"):
        engine.reduce(basis, 20)


def test_a_well_behaved_third_engine_is_not_refused():
    """The converse, so the test above is known to be testing the corruption and not the stub.

    The stub reduces nothing, but ``reduce`` LLL-reduces before the tour loop, so the basis that
    comes back is not the basis that went in: it is a different basis of the same lattice, which is
    precisely the distinction the check exists to make. Comparing row norms here would fail for the
    right reason — the shortest *row* changes while the shortest *vector* does not.
    """
    engine = NoOpEngine()
    basis = qary_basis(DIMENSION)
    before = matrix_rows(basis)
    result = engine.reduce(basis, 20)
    assert result.engine == "noop_stub"
    assert result.n_tours == 1 and result.converged is True
    assert matrix_rows(result.basis) != before
    assert_same_lattice(before, result.basis)


# -- the check itself, aimed at from four directions ---------------------------------------------


def test_a_unimodular_transform_is_accepted():
    """A basis is not its rows. Elementary row operations move every entry and keep the lattice."""
    basis = qary_basis(DIMENSION)
    rows = matrix_rows(basis)
    moved = [list(row) for row in rows]
    moved[0] = [a + 3 * b for a, b in zip(moved[0], moved[7])]
    moved[5], moved[9] = moved[9], moved[5]
    moved[2] = [-a for a in moved[2]]
    assert moved != rows
    assert_same_lattice(basis, to_integer_matrix(moved))


def test_the_check_rejects_a_row_perturbed_by_one():
    """The required non-vacuity test: one entry, changed by one, in a 40-dimensional basis.

    The perturbation is invisible in the numbers a run reports. Measured on this instance, the
    root-Hermite factor of the corrupted basis is ``1.0120064506159738`` against the true
    ``1.0120042462977306`` — a relative difference of **2.2e-6**, in the sixth decimal of the one
    scalar a report quotes, and smaller than the difference between two block sizes one step apart.
    The basis is still square, still integral, still full rank, and still reduces without error.

    That is why the check is an exact solve and not a magnitude comparison, and why it has to be
    shown failing: a boundary check that has only ever been observed passing is a check nobody has
    any reason to believe.
    """
    reduced = FpylllBKZEngine().reduce(qary_basis(DIMENSION), BLOCK_SIZE).basis
    corrupt = [list(row) for row in matrix_rows(reduced)]
    corrupt[3][5] += 1
    corrupted = to_integer_matrix(corrupt)

    # The corruption is real, and the only thing that can see it is the transform.
    assert root_hermite_factor(reduced) == REDUCED_HERMITE_FACTOR
    assert root_hermite_factor(corrupted) == PERTURBED_HERMITE_FACTOR
    assert (
        abs(root_hermite_factor(corrupted) - root_hermite_factor(reduced)) / REDUCED_HERMITE_FACTOR
        < 1e-4
    )
    assert min_squared_norm(corrupted) == min_squared_norm(reduced)

    with pytest.raises(LatticePreservationError, match="not the lattice spanned by the input"):
        assert_same_lattice(reduced, corrupted)


def test_the_rejection_message_names_the_offending_entry():
    """A refusal a reader cannot act on is a refusal they will work around.

    The entry named is the transform's, not the basis's: the basis changed by one entry at (3, 5),
    and the non-integral coefficient that proves the lattice changed is at (3, 0) of the transform.
    Both facts are in the message, along with the denominator — ``65536``, the modulus — which is
    what tells a reader the corruption was a single unit against a ``q`` of ``2**16``.
    """
    reduced = FpylllBKZEngine().reduce(qary_basis(DIMENSION), BLOCK_SIZE).basis
    corrupt = [list(row) for row in matrix_rows(reduced)]
    corrupt[3][5] += 1
    with pytest.raises(LatticePreservationError) as raised:
        assert_same_lattice(
            reduced, to_integer_matrix(corrupt), context="fpylll_bkz at block size 40"
        )
    message = str(raised.value)
    assert "fpylll_bkz at block size 40" in message
    assert "not an integer" in message
    assert re.search(r"transform row \d+ entry \d+", message)
    assert "/65536" in message


def test_the_check_rejects_a_scaled_row():
    """A sublattice of index 2, with an *integral* transform whose determinant is 2.

    Separate from the perturbed-row case because it exercises the other branch: the transform is
    integral, so the failure has to be caught by the determinant rather than by the denominator.
    """
    basis = qary_basis(DIMENSION)
    rows = matrix_rows(basis)
    doubled = [list(row) for row in rows]
    doubled[0] = [2 * value for value in doubled[0]]
    with pytest.raises(LatticePreservationError, match=r"det U\| == 2"):
        assert_same_lattice(basis, to_integer_matrix(doubled))


def test_the_check_rejects_a_basis_over_a_nearby_modulus():
    """The project's own described failure: a lattice over a nearby modulus.

    Same base block, same dimension, same shape; only the ``q`` on the diagonal moves, from
    ``2**16`` to ``2**16 - 2``. The corrupted basis is not obviously wrong by any check that does
    not solve for the transform: it is 40x40, integral, full rank, and it LLL-reduces without
    complaint. Measured, its reported root-Hermite factor is ``2.041150498649`` against the true
    lattice's ``2.112049808724`` — a 3.4e-2 relative difference, in the direction that *flatters*
    the result, because the run over the wrong modulus reports a shorter ``b_0``. A stronger-looking
    reduction is the last thing a reader questions.
    """
    basis = qary_basis(DIMENSION)
    rows = matrix_rows(basis)
    nu = DIMENSION // 2
    nearby = [list(row) for row in rows]
    for j in range(nu, DIMENSION):
        nearby[j][j] = DEFAULT_Q - 2
    nearby_matrix = to_integer_matrix(nearby)

    with pytest.raises(LatticePreservationError):
        assert_same_lattice(basis, nearby_matrix)

    # What a run would have reported, and why nothing in it looks wrong. Both are LLL-reduced
    # first, because that is the state a run's basis is in by the time a Hermite factor is quoted.
    reduced_true = IntegerMatrix(basis)
    reduced_nearby = IntegerMatrix(nearby_matrix)
    LLL.reduction(reduced_true)
    LLL.reduction(reduced_nearby)
    true_factor = root_hermite_factor(reduced_true)
    nearby_factor = root_hermite_factor(reduced_nearby)
    assert true_factor is not None and nearby_factor is not None
    assert abs(nearby_factor - true_factor) / true_factor < 5e-2
    # And the wrong lattice looks *better* by the one number a report quotes.
    assert nearby_factor < true_factor


# -- the check's own preconditions ---------------------------------------------------------------


def test_the_check_accepts_either_representation():
    """The engines hand over fpylll matrices; a test hands over lists. One checker, both forms."""
    basis = qary_basis(12)
    rows = matrix_rows(basis)
    assert_same_lattice(rows, rows)
    assert_same_lattice(basis, rows)
    assert_same_lattice(rows, basis)


def test_a_non_square_pair_is_refused():
    with pytest.raises(ValueError, match="square"):
        assert_same_lattice([[1, 2], [3, 4]], [[1, 2, 3], [4, 5, 6]])


def test_a_singular_input_is_reported_as_such():
    """A degenerate basis does not span a lattice, and "singular" is a different failure.

    Reporting it as a lattice change would send a reader looking for a bug in the engine instead of
    at what the engine was handed.
    """
    singular = [[1, 2], [2, 4]]
    with pytest.raises(LatticePreservationError, match="singular"):
        assert_same_lattice(singular, [[1, 2], [2, 5]])


# -- three-way agreement on one instance ---------------------------------------------------------


def _exact_shortest_vector_squared_norm() -> int:
    """Exact enumeration, as the reference the engines are measured against.

    ``method="proved"`` and not the default: the default path (``pruning=True``) reaches fplll's
    external-enumeration code in this build and aborts the process on a pruning-vector mismatch,
    measured — a hard exit, not an exception, which would take the test session with it. ``proved``
    is also the honest call here: the docstring guarantees the result, and this is the oracle.
    """
    basis = qary_basis(DIMENSION)
    LLL.reduction(basis)
    vector = SVP.shortest_vector(basis, method="proved")
    return sum(int(value) ** 2 for value in vector)


@pytest.fixture(scope="module")
def exact_shortest_squared_norm() -> int:
    return _exact_shortest_vector_squared_norm()


def test_the_enumeration_oracle_is_shorter_than_what_lll_reaches(exact_shortest_squared_norm):
    """Non-vacuity for the agreement tests below.

    If LLL already returned the shortest vector, everything after this would be an engine agreeing
    with a basis it was handed. It does not: measured, LLL reaches ``223822`` where the shortest
    vector is ``175670``.
    """
    lll_only = qary_basis(DIMENSION)
    LLL.reduction(lll_only)
    assert min_squared_norm(lll_only) == LLL_SQUARED_NORM
    assert exact_shortest_squared_norm == SHORTEST_SQUARED_NORM
    assert exact_shortest_squared_norm < LLL_SQUARED_NORM


def test_bkz_and_exact_enumeration_agree_on_the_shortest_vector_norm(exact_shortest_squared_norm):
    """Two engines, two oracles: enum-BKZ at full block size against pruned-free enumeration."""
    result = FpylllBKZEngine().reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    assert min_squared_norm(result.basis) == exact_shortest_squared_norm
    # And BKZ places it first, which is the claim a block size is supposed to make.
    assert squared_norms(result.basis)[0] == exact_shortest_squared_norm


@pytest.mark.sieve
@pytest.mark.skipif(
    not G6KSieveEngine().available(),
    reason="G6K is not importable in this interpreter; see G6KSieveEngine.unavailable_reason()",
)
def test_sieving_agrees_with_bkz_and_exact_enumeration(exact_shortest_squared_norm):
    """The three-way agreement: sieving, enumeration-BKZ and exact enumeration, one instance.

    The three agree on the norm of the shortest vector of a 40-dimensional q-ary lattice. Each pair
    of them could agree while both were wrong — a shared convention about the lattice, a misread
    block size — which is why the third is here: exact enumeration has no block size and no sieve,
    so it shares no convention with either.

    The quantity compared is the *squared* norm, in exact integers. A norm comparison through
    floating point would make the test pass or fail on rounding, and this test exists to notice a
    disagreement, not to generate one.
    """
    sieved = G6KSieveEngine().reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    enumerated = FpylllBKZEngine().reduce(qary_basis(DIMENSION), BLOCK_SIZE)

    sieved_norm = min_squared_norm(sieved.basis)
    enumerated_norm = min_squared_norm(enumerated.basis)

    assert sieved_norm == exact_shortest_squared_norm, (
        f"sieving reached ||b_i||^2 = {sieved_norm} but the shortest vector has "
        f"{exact_shortest_squared_norm}; a longer vector here means the sieve missed, which is a "
        "fact about the run and not about the lattice"
    )
    assert enumerated_norm == exact_shortest_squared_norm
    assert sieved_norm == enumerated_norm


@pytest.mark.sieve
@pytest.mark.skipif(
    not G6KSieveEngine().available(),
    reason="G6K is not importable in this interpreter; see G6KSieveEngine.unavailable_reason()",
)
def test_a_seeded_sieving_run_is_reproducible_at_one_thread():
    """Measured: with ``threads=1`` two runs at the same seed return bit-identical bases; with
    ``threads=4`` they do not.

    Recorded as a test rather than as prose because it is a property of the results this project
    publishes: a run whose basis is not re-derivable from its seed is a run whose numbers exist but
    cannot be checked. ``threads=1`` is the price of that, and it is a factor of 2.1 at block size
    90 — a price the default now pays too: it was 4 until notes/09 measured what that cost.
    """
    engine = G6KSieveEngine(seed=20260914, threads=1)
    first = engine.reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    second = engine.reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    assert matrix_rows(first.basis) == matrix_rows(second.basis)


@pytest.mark.sieve
@pytest.mark.skipif(
    not G6KSieveEngine().available(),
    reason="G6K is not importable in this interpreter; see G6KSieveEngine.unavailable_reason()",
)
def test_a_dual_mode_run_still_spans_the_input_lattice():
    """Dual mode is where a wrong lattice is most likely, and least likely to be noticed.

    The dual attack reduces the dual lattice, and G6K hands back a primal basis afterwards. A
    mishandled conversion produces a self-consistent basis of the wrong lattice, which is exactly
    the failure the invariant exists for — and this is the only test in the suite that runs the
    dual path at all.
    """
    engine = G6KSieveEngine(threads=1)
    basis = qary_basis(DIMENSION)
    before = matrix_rows(basis)
    result = engine.reduce(basis, BLOCK_SIZE, dual_mode=True)
    assert_same_lattice(before, result.basis)
    assert result.root_hermite_factor is not None and result.root_hermite_factor >= 1.0
    assert math.isfinite(result.root_hermite_factor)
