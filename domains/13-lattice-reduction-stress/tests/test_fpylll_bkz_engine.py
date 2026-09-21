"""The enumeration engine: the one that is always there, and the one the others are compared to.

It is required — no fallback exists for it, and the package does not run without it — so these tests
run in every interpreter rather than being skipped. What they check is mostly that a run's result is
*complete*: the fields that distinguish a measurement from a bound, and the one number a sweep
reports. A result missing ``converged`` reads exactly like a converged one, and a result whose
Hermite factor was computed from a different quantity than the one it claims is worse than a
missing result, because nothing downstream can tell.

The agreement tests here are against fplll's own enumeration, which is not a fully independent
oracle — see ``test_engine_lattice_preservation.py`` for the pruned-free enumeration and the sieving
engine agreeing on the same instance. What this module adds is the definitional check: the reported
root-Hermite factor is compared against ``||b_0|| / det(L)^(1/d)`` computed from the *known exact*
determinant of the basis this project builds (``q**m``, by construction), not against anything the
library reported.
"""

from __future__ import annotations

import math

import pytest
from fpylll import SVP, IntegerMatrix

from engine_helpers import (  # type: ignore[import-not-found]
    DEFAULT_Q,
    matrix_rows,
    min_squared_norm,
    qary_basis,
    squared_norms,
    to_integer_matrix,
)
from qlwr_lattice_stress.engines.base_engine import INTERPRETER_BASELINE_BYTES
from qlwr_lattice_stress.engines.fpylll_bkz_engine import (
    ENUMERATION_WORKSPACE_BYTES_PER_BLOCK_ENTRY,
    FpylllBKZEngine,
)
from qlwr_lattice_stress.protocols import MEASURED, ReducedBasisResult

pytestmark = pytest.mark.engine

DIMENSION = 40
BLOCK_SIZE = 40


def analytic_root_hermite_factor(matrix) -> float:
    """``(||b_0|| / det(L)^(1/d))^(1/d)``, with ``det(L)`` known exactly and not read from the library.

    ``qary_basis`` is block triangular with an identity block and a ``q * I`` block, so its
    determinant is exactly ``q**(d//2)`` with no cancellation possible. That makes this an
    independent value rather than a rearrangement of the engine's own arithmetic: the engine reads
    its Gram-Schmidt norms from fpylll, and this reads the integer rows. ``math.sqrt`` and not
    ``isqrt``: the reported factor is a float, and flooring the norm at the last integer would show
    up as a 3e-4 disagreement that says nothing about the engine.
    """
    rows = matrix_rows(matrix)
    dimension = len(rows)
    first_row_norm = math.sqrt(sum(value * value for value in rows[0]))
    determinant_root = DEFAULT_Q ** ((dimension // 2) / dimension)
    # The d-th root is what makes this the *root* Hermite factor. This helper once omitted it, as
    # the engine did, so the test agreed with the engine on the wrong quantity.
    return (first_row_norm / determinant_root) ** (1.0 / dimension)


# -- the interface -------------------------------------------------------------------------------


def test_the_engine_is_available_here():
    engine = FpylllBKZEngine()
    assert engine.available() is True
    assert engine.unavailable_reason() is None
    assert engine.name == "fpylll_bkz"


def test_the_version_is_the_librarys_own():
    import fpylll

    assert FpylllBKZEngine().version() == fpylll.__version__


def test_the_default_thread_count_is_one():
    """Measured, not chosen: this build's enumeration is single-threaded."""
    assert FpylllBKZEngine().default_threads == 1
    assert FpylllBKZEngine().threads == 1


def test_threads_are_accepted_for_interface_parity_and_ignored():
    """A sweep hands one configuration to either engine; a result must not claim what did not run."""
    engine = FpylllBKZEngine(threads=4)
    assert engine.threads == 4
    result = engine.reduce(qary_basis(DIMENSION), 2)
    assert result.threads == 1


# -- what a run records --------------------------------------------------------------------------


def test_a_run_records_every_field_that_makes_it_a_measurement():
    """Each field is asserted for what it would cost a reader to have it missing or wrong."""
    engine = FpylllBKZEngine(seed=11)
    basis = qary_basis(DIMENSION)
    result = engine.reduce(basis, 20)

    assert isinstance(result, ReducedBasisResult)
    assert result.engine == "fpylll_bkz"
    assert result.engine_version == engine.version()
    assert result.block_size == 20
    assert result.dimension == DIMENSION
    assert result.threads == 1
    assert result.wall_clock_s > 0.0
    assert result.provenance == MEASURED
    assert result.not_run_reason is None
    # A tour count and a convergence flag are the difference between a result and a bound on how
    # hard the instance might be. Two identical-looking bases in a results file mean different
    # things depending on this pair, so neither may be silently absent.
    assert result.n_tours >= 1
    assert isinstance(result.converged, bool)
    assert isinstance(result.peak_rss_bytes_upper_bound, int)
    assert result.peak_rss_bytes_upper_bound > 0
    assert result.root_hermite_factor is not None
    assert result.root_hermite_factor > 1.0


def test_a_run_does_not_modify_the_basis_it_was_handed():
    """Both fplll and G6K reduce in place, so the caller's basis is the evidence the preservation
    check compares against — and it stops being evidence the moment an engine writes to it."""
    engine = FpylllBKZEngine()
    basis = qary_basis(DIMENSION)
    before = matrix_rows(basis)
    result = engine.reduce(basis, 20)
    assert matrix_rows(basis) == before
    # And the run did something: the returned rows are not the rows that went in.
    assert matrix_rows(result.basis) != before


def test_the_returned_basis_is_a_fresh_matrix_holding_the_reduced_rows():
    result = FpylllBKZEngine().reduce(qary_basis(DIMENSION), 20)
    assert isinstance(result.basis, IntegerMatrix)
    assert result.basis.nrows == DIMENSION and result.basis.ncols == DIMENSION


# -- the reported number, against an independently known value ------------------------------------


def test_the_root_hermite_factor_matches_the_analytic_value():
    """``||b_0|| / q**(m/d)``, with ``det(L) = q**m`` known exactly from the construction.

    Agreement is to 4e-16 relative, measured — i.e. to the last bit or two of a double — which is
    the strongest statement available for two different routes to one quantity. A tolerance rather
    than equality because the engine's route goes through a floating-point Gram-Schmidt.
    """
    result = FpylllBKZEngine().reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    expected = analytic_root_hermite_factor(result.basis)
    assert result.root_hermite_factor is not None
    assert math.isclose(result.root_hermite_factor, expected, rel_tol=1e-9)


def test_the_root_hermite_factor_is_none_rather_than_fabricated_when_it_cannot_be_computed():
    """``None`` is a value this project can act on; a substituted one is not.

    A fabricated factor is indistinguishable downstream from a measured one — the failure the whole
    provenance field exists to prevent — so the helper returns ``None`` for a basis whose
    Gram-Schmidt norms are unusable. Measured: a zero matrix and a singular one both give ``None``,
    while a trivially reduced basis gives exactly ``1.0``. Nothing here is an engine: the point is
    the helper's behaviour, which every engine's result depends on.
    """
    from qlwr_lattice_stress.engines.base_engine import root_hermite_factor

    assert root_hermite_factor(IntegerMatrix(4, 4)) is None
    assert root_hermite_factor(to_integer_matrix([[1, 2], [2, 4]])) is None
    assert root_hermite_factor(to_integer_matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])) == 1.0


def test_block_size_equal_to_the_dimension_reaches_the_shortest_vector():
    """At ``beta = d`` the block *is* the lattice, so the result is the exact SVP answer.

    The oracle is fplll's own enumeration with ``method="proved"``, which is what makes this test
    about the engine's plumbing (did the block size reach the reduction, did the result record the
    basis that came out) rather than about fplll's ability to enumerate. Its default path
    (``pruning=True``) aborts the process in this build, measured; nothing here calls it.
    """
    result = FpylllBKZEngine().reduce(qary_basis(DIMENSION), BLOCK_SIZE)

    reference = IntegerMatrix(qary_basis(DIMENSION))
    vector = SVP.shortest_vector(reference, method="proved")
    exact = sum(int(value) ** 2 for value in vector)

    assert min_squared_norm(result.basis) == exact
    # b_0, specifically: the Hermite factor is computed from the first row, so "reduced at block
    # size d" has to mean the shortest vector was moved to the front, not merely produced somewhere.
    assert squared_norms(result.basis)[0] == exact


def test_a_small_block_size_does_not_reach_the_shortest_vector():
    """Non-vacuity for the test above: the agreement is not something any run gets for free.

    Measured on this instance: LLL leaves ``min ||b_i||^2 = 262767`` where the shortest vector is
    ``170242``, and a run at block size 20 closes the gap only part way, to ``184943``. Without this,
    "the engine reached the shortest vector at block size d" would be satisfied by an engine that
    returned its input at any block size.
    """
    result = FpylllBKZEngine().reduce(qary_basis(DIMENSION), 20)
    assert min_squared_norm(result.basis) == 184943
    assert 170242 < min_squared_norm(result.basis) < 262767


# -- tours, and the two ways a run can stop --------------------------------------------------------


def test_a_tour_limit_is_recorded_as_not_converged():
    """``converged=False`` is a bound on the instance, not a failure, and it must be visible."""
    engine = FpylllBKZEngine(max_tours=1)
    result = engine.reduce(qary_basis(DIMENSION), 20)
    assert result.n_tours == 1
    assert result.converged is False


def test_the_same_run_converges_when_the_limit_is_lifted():
    """The contrast that makes ``converged`` mean something: same instance, same block size.

    Measured, it takes more than one tour to stall here — which is the point. The two results carry
    bases that a results file would show as identical runs, and they mean different things.
    """
    result = FpylllBKZEngine().reduce(qary_basis(DIMENSION), 20)
    assert result.converged is True
    assert result.n_tours > 1


def test_an_unreduced_but_converged_run_is_distinguishable():
    """A run that stops immediately because it has nothing left to do reports ``True``.

    At block size 2 a tour reproduces LLL, so ``||b_0||`` does not improve and the loop stops after
    one tour with ``converged=True``. This is the case that ``converged`` alone would misreport: the
    basis is barely reduced and the run is nonetheless finished, and the pair
    ``n_tours=1, converged=True`` is the only thing in the result that says so.
    """
    result = FpylllBKZEngine().reduce(qary_basis(DIMENSION), 2)
    assert result.n_tours == 1
    assert result.converged is True
    # And the basis it returns is the LLL basis, so "unreduced" is the right description of it.
    from fpylll import LLL

    lll_only = IntegerMatrix(qary_basis(DIMENSION))
    LLL.reduction(lll_only)
    assert matrix_rows(result.basis) == matrix_rows(lll_only)
    assert matrix_rows(result.basis) != matrix_rows(qary_basis(DIMENSION))


# -- refusals ------------------------------------------------------------------------------------


@pytest.mark.parametrize("block_size", [0, 1, -5])
def test_a_block_size_below_the_minimum_is_refused(block_size):
    with pytest.raises(ValueError, match="below"):
        FpylllBKZEngine().reduce(qary_basis(DIMENSION), block_size)


def test_a_block_size_past_the_dimension_is_refused():
    """fplll accepts this silently — measured, 41 on a 40-row basis raises nothing — so the bound is
    enforced here, where the run can be reported as refused rather than as done."""
    with pytest.raises(ValueError, match="exceeds the basis dimension"):
        FpylllBKZEngine().reduce(qary_basis(DIMENSION), DIMENSION + 1)


def test_a_non_integer_block_size_is_refused():
    for block_size in (20.0, "20", None, True):
        with pytest.raises(TypeError):
            FpylllBKZEngine().reduce(qary_basis(DIMENSION), block_size)


def test_an_unknown_keyword_is_refused_rather_than_ignored():
    """A caller who asks for ``auto_abort`` and is not given it has no way to see the difference in
    the result, and this engine deliberately does not implement it. See the module docstring."""
    with pytest.raises(TypeError, match="auto_abort"):
        FpylllBKZEngine().reduce(qary_basis(DIMENSION), 20, auto_abort=True)


def test_an_unknown_keyword_is_refused_before_the_reduction_runs():
    """The refusal costs nothing, which is what makes it usable as a guard in a sweep."""
    import time

    started = time.perf_counter()
    with pytest.raises(TypeError):
        FpylllBKZEngine().reduce(qary_basis(DIMENSION), 20, gh_bound=1.1)
    assert time.perf_counter() - started < 1.0


# -- the memory model ------------------------------------------------------------------------------


def test_the_memory_estimate_is_above_the_interpreter_baseline():
    assert FpylllBKZEngine().estimate_memory_bytes(40) > INTERPRETER_BASELINE_BYTES


def test_the_memory_estimate_is_the_documented_model():
    """Stated exactly, so that a change to the model is a test failure and not a drift."""
    engine = FpylllBKZEngine()
    for block_size in (2, 20, 40, 160):
        expected = (
            INTERPRETER_BASELINE_BYTES
            + ENUMERATION_WORKSPACE_BYTES_PER_BLOCK_ENTRY * block_size**2
        )
        assert engine.estimate_memory_bytes(block_size) == expected


def test_the_memory_estimate_is_monotone_in_the_block_size():
    engine = FpylllBKZEngine()
    estimates = [engine.estimate_memory_bytes(beta) for beta in range(2, 100, 7)]
    assert estimates == sorted(estimates)
    assert len(set(estimates)) == len(estimates)


def test_the_memory_estimate_stays_small_where_the_sweep_runs():
    """Memory is not what limits this project. Recorded as a test because the model's *purpose* is
    to be an upper bound on a runaway, and a model that quietly became the binding constraint would
    be doing a different job."""
    engine = FpylllBKZEngine()
    assert engine.estimate_memory_bytes(40) < 200 * (1 << 20)
    assert engine.estimate_memory_bytes(160) < 512 * (1 << 20)


def test_a_non_positive_block_size_has_no_estimate():
    with pytest.raises(ValueError):
        FpylllBKZEngine().estimate_memory_bytes(0)


# -- determinism ----------------------------------------------------------------------------------
#
# The property this section asserts is the one the sweep rests on and the one nothing else checks:
# that reducing the same basis at the same block size twice gives the same answer. Cross-check 7 is
# named "a run is reproducible from its own record", but its body only re-derives seeds — it never
# runs a reduction, so it cannot observe this. The G6K engine has a bit-reproducibility test; this
# engine, which is the default and the one the dimension sweep runs on, had none.


def test_the_same_reduction_twice_gives_the_same_basis():
    """Twice in one process, from the same deterministic input.

    The property the sweep rests on and the one nothing checked. Cross-check 7 is named "a run is
    reproducible from its own record", but its body only re-derives seeds — it never runs a
    reduction, so it cannot observe this. The G6K engine has a bit-reproducibility test; this
    engine, which the dimension sweep can fall back to, had none.

    **This test passes, and the passing is a measurement rather than a design.** The neighbouring
    ``test_determinism_here_comes_from_single_threading_not_from_a_seed`` pins *why*: it is the
    thread count, not a seed, and the G6K engine — which the config prefers — is bit-reproducible at
    one thread and is not above it. Measured at dimension 80, block size 10: four processes at one
    thread all returned ``3.11695792``; four at four threads returned three distinct values, one of
    which recovered the planted vector and the others did not.
    """
    engine = FpylllBKZEngine()
    first = engine.reduce(qary_basis(dimension=DIMENSION), 20)
    second = engine.reduce(qary_basis(dimension=DIMENSION), 20)

    assert matrix_rows(first.basis) == matrix_rows(second.basis), (
        "the two reductions disagree. A measured number that changes between runs is not a "
        "measurement, and a results file recording one draw cannot be checked against anything."
    )
    assert first.root_hermite_factor == second.root_hermite_factor
    assert first.n_tours == second.n_tours
    assert first.converged == second.converged


def test_determinism_here_comes_from_single_threading_not_from_a_seed():
    """The mechanism, pinned — because the obvious wrong guess is that a seed does it.

    fplll's BKZ 2.0 does rerandomise part of the basis (``DEFAULT_RERANDOMIZATION_DENSITY`` is 3),
    which makes "seed the RNG" the natural first diagnosis for any non-reproducibility. It is wrong
    here. A ``rng_seed`` field was briefly added on that reasoning and then removed, before it
    reached a results file:

    * fpylll's BKZ is deterministic **because this engine runs it on one thread**. Four processes
      reducing the same basis at the same block size returned one identical value.
    * A seed recorded for a reduction that does not consume one would imply reproducibility is
      governed by that seed. An operator re-running with it would expect the same basis and would
      get one only because the thread count was also one — a correct outcome resting on a false
      reason.

    The thread count is the field that governs this, and ``ReducedBasisResult`` already carries it.
    """
    engine = FpylllBKZEngine(threads=4)
    assert engine.threads == 4, "the request is held, so the difference is visible where it matters"
    result = engine.reduce(qary_basis(dimension=DIMENSION), 2)
    assert result.threads == 1, (
        "the result must report what ran, not what was asked for. It is the only field a reader has "
        "for judging whether a recorded point is reproducible."
    )

    # And the determinism claim that field supports: same input, same answer, repeatedly.
    bases = [
        matrix_rows(FpylllBKZEngine().reduce(qary_basis(dimension=DIMENSION), 20).basis)
        for _ in range(3)
    ]
    assert bases[0] == bases[1] == bases[2], (
        "at one thread the reduction is bit-reproducible; the sweep's measured minima rest on this"
    )
