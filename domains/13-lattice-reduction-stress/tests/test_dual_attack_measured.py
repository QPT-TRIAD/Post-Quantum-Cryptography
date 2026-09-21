"""The dual attack's MEASURED branch, against a uniform-random control — and the primal leftovers.

Every other dual-attack call in the suite lands in the "band covers the residue space" refusal,
because at the recorded modulus pair (``q = 2^16``, ``p = 2^8``, noise bound 128) the reduced dual
vectors are some hundred times too long for the band to stay inside ``Z_q``. That is a true finding
about the parameter regime, but it leaves the plan's requirement — *a distinguishing statistic
against a uniform-random control* — without a single executed assertion: the branch that computes
an advantage was never reached.

The fixture here reaches it by widening the rounding modulus to ``p = 2^15``. The noise bound is
then ``q/(2p) = 1`` and the band budget ``q/(2B)`` is 32768, so a BKZ-10 reduced dual vector
(``||y||_1`` around 10^3 at ``nu = 8, m = 24``) sits well inside it.

**The fixture is checked for degeneracy, because the obvious one is degenerate.** At
``(nu, m) = (4, 16)``, seed 3, every rounding error happens to be zero, so the normal-form target
``b'`` is the zero vector — and ``<y, 0> = 0`` lands inside *any* band for *any* ``y``, dual or not.
That instance reports an advantage of 0.9957 and proves nothing: a unit vector "distinguishes" on
it just as well. The instance used below, ``(8, 24)`` seed 3, has a non-zero target and non-zero
errors, which is asserted rather than assumed.
"""

from __future__ import annotations

import dataclasses
import random

import numpy as np
import pytest

from qlwr_lattice_stress.attacks import (
    find_minimum_successful_block_size,
    prepare_primal,
    recover_secret_from_vector,
    run_dual_attack,
    run_primal_attack,
    short_dual_vectors,
    uniform_control,
)
from qlwr_lattice_stress.engines import FpylllBKZEngine
from qlwr_lattice_stress.lattice.dual_embedding import (
    DistinguisherStatistic,
    dual_basis,
    dual_distinguisher,
)
from qlwr_lattice_stress.problem.normal_form import to_normal_form
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)
from qlwr_lattice_stress.protocols import MEASURED, NOT_RUN

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8

#: The rounding modulus at which the dual attack reaches: noise bound 1, band budget 32768.
WIDE_P = 1 << 15

#: The block size every dual run below uses. Small enough to take milliseconds at dimension 16.
BLOCK_SIZE = 10


def make_instance(nu: int, m: int, *, p: int = PRODUCTION_P, seed: int = 3) -> LatticeQLWRInstance:
    """A QLWR instance at the production modulus, with the rounding modulus left as a parameter."""
    rng = random.Random(seed)
    q = PRODUCTION_Q
    while True:
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    return LatticeQLWRInstance(
        nu=nu, q_l=q, p=p, m=m,
        secret_s=tuple(rng.randrange(q) for _ in range(nu)), base=base, seed=seed,
    )


@pytest.fixture(scope="module")
def engine():
    # fpylll ignores the thread count, and one is what the project records as reproducible.
    return FpylllBKZEngine(threads=1)


@pytest.fixture(scope="module")
def reachable():
    """The instance on which the dual attack measures, with its normal form and dual basis."""
    instance = make_instance(8, 24, p=WIDE_P, seed=3)
    nf = to_normal_form(instance)
    return instance, nf, dual_basis(nf)


@pytest.fixture(scope="module")
def reduced_dual_rows(engine, reachable):
    """The BKZ-reduced dual basis, as integer rows — genuinely short dual vectors."""
    _, _, basis = reachable
    outcome = engine.reduce(basis, BLOCK_SIZE)
    return [
        [int(outcome.basis[i, j]) for j in range(outcome.basis.ncols)]
        for i in range(outcome.basis.nrows)
    ]


# ---------------------------------------------------------------------------------------------
# the fixture is not the degenerate one
# ---------------------------------------------------------------------------------------------


def test_the_positive_fixture_has_something_to_distinguish(reachable):
    """A zero target lands inside every band for every vector, so it would make everything below
    pass for the wrong reason. The errors and the target must both be non-zero."""
    instance, nf, _ = reachable
    assert nf.noise_bound == 1
    assert nf.q // (2 * nf.noise_bound) == 32768
    assert any(int(v) != 0 for v in nf.b), "the normal-form target is zero; any vector lands in band"
    assert any(int(v) != 0 for v in nf.e), "every error is zero; the instance is noiseless"
    assert any(int(v) != 0 for v in instance.error_vector())


def test_the_obvious_smaller_fixture_is_degenerate_and_is_not_used():
    """Recorded so the next reader does not swap it in for speed: at (4, 16), seed 3, the target is
    the zero vector, and a non-dual unit vector then "distinguishes" perfectly."""
    nf = to_normal_form(make_instance(4, 16, p=WIDE_P, seed=3))
    assert not any(int(v) for v in nf.b)
    unit = [1] + [0] * (nf.m - 1)
    statistic = dual_distinguisher([unit], list(map(int, nf.b)), nf)
    assert statistic.observed_fraction == 1.0, "a zero target is inside every band"


# ---------------------------------------------------------------------------------------------
# the MEASURED branch — real samples against the uniform control
# ---------------------------------------------------------------------------------------------


def test_the_dual_attack_measures_and_separates_real_from_uniform(engine, reachable):
    """The two-sided comparison the plan asks for.

    Real samples: every reduced dual vector lands inside its band, so the advantage is one minus the
    analytic uniform expectation. Uniform control, through the same statistic: nothing beyond what
    chance gives. The assertion is on both sides *and* on the gap, because a statistic that fired on
    everything would pass the first and only fail the second.
    """
    instance, nf, basis = reachable
    result = run_dual_attack(instance, engine, BLOCK_SIZE)

    assert result.provenance == MEASURED
    assert result.not_run_reason is None
    assert result.dimension == basis.nrows == nf.m == 16
    assert result.n_samples == nf.m, "every reduced row is evaluated by default"
    assert result.block_size == BLOCK_SIZE
    assert result.engine == "fpylll_bkz"
    assert result.wall_clock_s > 0

    assert result.advantage > 0.5
    assert abs(result.control_advantage) < 0.15
    assert result.advantage - result.control_advantage > 0.8
    # The measured values, so a drift in the reduction or the statistic is seen rather than absorbed
    # by the loose bounds above: 0.9659 against -0.0341 at the pinned fpylll.
    assert result.advantage == pytest.approx(0.966, abs=0.01)
    assert result.control_advantage == pytest.approx(-0.034, abs=0.01)


def test_the_dual_attack_is_deterministic_under_a_fixed_control_seed(engine, reachable):
    instance, _, _ = reachable
    first = run_dual_attack(instance, engine, BLOCK_SIZE, control_seed=1234)
    second = run_dual_attack(instance, engine, BLOCK_SIZE, control_seed=1234)
    assert first.advantage == second.advantage
    assert first.control_advantage == second.control_advantage
    assert first.n_samples == second.n_samples


def test_a_different_control_seed_changes_the_control_and_not_the_verdict(engine, reachable):
    """The control is a distribution that can be resampled, not a fixed array.

    Across seeds the control advantage takes more than one value — it is genuinely being redrawn —
    while the real-sample advantage does not move at all and stays above every control draw.
    """
    instance, nf, _ = reachable
    seeds = list(range(40))
    results = [run_dual_attack(instance, engine, BLOCK_SIZE, control_seed=s) for s in seeds]

    assert len({tuple(uniform_control(nf, seed=s)[0]) for s in seeds}) == len(seeds)
    controls = [r.control_advantage for r in results]
    assert len(set(controls)) > 1, "the control never changed, so the seed is not reaching it"

    assert len({r.advantage for r in results}) == 1, "the control seed leaked into the real statistic"
    for r in results:
        assert r.provenance == MEASURED
        assert r.advantage > abs(r.control_advantage) + 0.8
    # Under the null the statistic is centred on zero. Measured: mean +0.0065 over these 40 seeds.
    assert abs(sum(controls) / len(controls)) < 0.05


def test_a_uniform_target_through_the_same_path_gives_no_advantage(engine, reachable):
    """The negative control through ``run_dual_attack`` itself rather than beside it.

    Same dual basis, same engine, same block size; only ``b`` is replaced by a uniform vector. The
    advantage that was 0.966 on the real target collapses to chance. Without this, a statistic that
    ignored ``b`` altogether would pass every test above.
    """
    instance, nf, basis = reachable
    real = run_dual_attack(instance, engine, BLOCK_SIZE, transformed=(nf, basis))
    assert real.advantage > 0.9

    advantages = []
    for seed in range(40):
        uniform_b = np.array(uniform_control(nf, seed=1000 + seed)[0], dtype=np.int64)
        forged = dataclasses.replace(nf, b=uniform_b)
        result = run_dual_attack(instance, engine, BLOCK_SIZE, transformed=(forged, basis))
        assert result.provenance == MEASURED
        assert result.advantage < 0.15, f"a uniform target distinguished at seed {seed}"
        advantages.append(result.advantage)
    assert abs(sum(advantages) / len(advantages)) < 0.05


def test_fewer_dual_vectors_is_a_coarser_statistic_of_the_same_sign(engine, reachable):
    instance, _, _ = reachable
    coarse = run_dual_attack(instance, engine, BLOCK_SIZE, shortest_vectors=4)
    assert coarse.provenance == MEASURED
    assert coarse.n_samples == 4
    assert coarse.advantage > 0.5 > abs(coarse.control_advantage)


# ---------------------------------------------------------------------------------------------
# the two refusals
# ---------------------------------------------------------------------------------------------


def test_a_band_covering_the_residue_space_is_not_run_and_says_why(engine):
    """At the production rounding modulus the attack does not apply, and the record says so.

    The reduction *did* run here, so the engine and the vector count are recorded; what is refused
    is reading an advantage off a statistic that cannot separate anything.
    """
    instance = make_instance(12, 30, p=PRODUCTION_P, seed=1)
    result = run_dual_attack(instance, engine, BLOCK_SIZE)

    assert result.provenance == NOT_RUN
    assert "covers the whole residue space" in result.not_run_reason
    assert "q/(2B) = 256" in result.not_run_reason
    assert "does not apply here rather than having been tried and failed" in result.not_run_reason
    assert result.advantage == 0.0 and result.control_advantage == 0.0
    assert result.dimension == instance.m - instance.nu == 18
    assert result.n_samples == 18
    assert result.engine == "fpylll_bkz"


def test_a_block_size_the_engine_refuses_is_not_run_with_the_engines_reason(engine, reachable):
    """The ``ValueError`` branch: nothing was reduced, and the engine's own words are the reason."""
    instance, _, basis = reachable
    result = run_dual_attack(instance, engine, basis.nrows + 5)

    assert result.provenance == NOT_RUN
    assert f"block size {basis.nrows + 5} exceeds the basis dimension {basis.nrows}" in (
        result.not_run_reason
    )
    assert result.dimension == basis.nrows
    assert result.block_size == basis.nrows + 5
    assert result.n_samples is None, "no statistic was evaluated, so no count may be reported"
    assert result.advantage == 0.0 and result.control_advantage == 0.0
    assert result.engine == "fpylll_bkz"


def test_a_block_size_below_two_is_refused_the_same_way(engine, reachable):
    instance, _, _ = reachable
    result = run_dual_attack(instance, engine, 1)
    assert result.provenance == NOT_RUN
    assert "below 2" in result.not_run_reason


# ---------------------------------------------------------------------------------------------
# the distinguisher itself, on genuinely short dual vectors
# ---------------------------------------------------------------------------------------------


def test_the_reduced_rows_are_dual_vectors_and_short(reachable, reduced_dual_rows):
    """``A^T y == 0 (mod q)`` for every row, checked directly against the normal form's base — and
    every row's band is far inside the residue space, which is what "short" has to mean here."""
    _, nf, _ = reachable
    a = [[int(v) for v in row] for row in nf.a]
    for y in reduced_dual_rows:
        for column in range(nf.n):
            assert sum(y[i] * a[i][column] for i in range(nf.m)) % nf.q == 0
        assert nf.noise_bound * sum(abs(v) for v in y) < nf.q // 8


def test_short_dual_vectors_returns_the_shortest_in_order(reachable, reduced_dual_rows):
    _, nf, _ = reachable
    shuffled = list(reversed(reduced_dual_rows))
    picked = short_dual_vectors(shuffled, nf, count=5)

    norms = [sum(v * v for v in y) for y in picked]
    assert len(picked) == 5
    assert norms == sorted(norms)
    assert norms == sorted(sum(v * v for v in y) for y in reduced_dual_rows)[:5]
    assert all(isinstance(v, int) for y in picked for v in y)
    # Asking for more than there are returns them all rather than padding or raising.
    assert len(short_dual_vectors(reduced_dual_rows, nf, count=100)) == len(reduced_dual_rows)


def test_every_short_dual_vector_lands_in_band_on_the_real_sample(reachable, reduced_dual_rows):
    """The bound ``|<y, e'>| <= ||y||_1 * B`` is deterministic, so *all* of them land inside — not
    most. The control lands inside only as often as chance gives."""
    _, nf, _ = reachable
    vectors = short_dual_vectors(reduced_dual_rows, nf, count=8)
    sample = list(map(int, nf.b))
    control = uniform_control(nf, seed=11)[0]

    statistic = dual_distinguisher(vectors, sample, nf, control_sample=control)

    assert statistic.n_samples == 8
    assert statistic.in_band == 8
    assert statistic.observed_fraction == 1.0
    assert 0.0 < statistic.expected_fraction < 0.1
    assert statistic.advantage == pytest.approx(1.0 - statistic.expected_fraction)
    assert abs(statistic.control_advantage) < 0.15
    assert statistic.dual_norm_squared == min(sum(v * v for v in y) for y in vectors)
    assert statistic.is_meaningful

    # The expectation is the analytic one, recomputed here by hand from the band widths.
    by_hand = sum(
        min(1.0, (2 * nf.noise_bound * sum(abs(v) for v in y) + 1) / nf.q) for y in vectors
    ) / len(vectors)
    assert statistic.expected_fraction == pytest.approx(by_hand)


def test_without_a_control_sample_the_control_advantage_is_zero(reachable, reduced_dual_rows):
    _, nf, _ = reachable
    statistic = dual_distinguisher(reduced_dual_rows[:3], list(map(int, nf.b)), nf)
    assert statistic.control_advantage == 0.0
    assert statistic.advantage > 0.9


def test_a_vector_outside_the_dual_lattice_yields_no_advantage(reachable):
    """A unit vector is as short as a vector gets and is not in the dual: ``A^T e_0`` is a row of
    ``A``, not zero. Its inner product with the target is just a coordinate of ``b`` — uniform — so
    it must not land in its band, and shortness alone must not read as an attack."""
    _, nf, _ = reachable
    sample = list(map(int, nf.b))
    units = []
    for i in range(nf.m):
        unit = [0] * nf.m
        unit[i] = 1
        assert any(int(nf.a[i, j]) % nf.q for j in range(nf.n)), "e_i is in the dual; pick another"
        units.append(unit)

    statistic = dual_distinguisher(units, sample, nf, control_sample=uniform_control(nf, seed=5)[0])

    assert statistic.in_band == 0
    assert statistic.observed_fraction == 0.0
    assert statistic.advantage <= 0.0
    assert not statistic.is_meaningful


def test_a_dual_vector_of_the_wrong_length_is_refused(reachable):
    _, nf, _ = reachable
    with pytest.raises(ValueError, match=f"expected m={nf.m}"):
        dual_distinguisher([[1] * (nf.m - 1)], list(map(int, nf.b)), nf)


def test_a_statistic_is_meaningful_only_when_it_beats_its_control():
    def statistic(advantage: float, control: float) -> DistinguisherStatistic:
        return DistinguisherStatistic(
            n_samples=10, in_band=5, expected_fraction=0.1, observed_fraction=0.5,
            advantage=advantage, control_advantage=control, dual_norm_squared=9,
        )

    assert statistic(0.9, 0.05).is_meaningful
    assert statistic(0.9, -0.05).is_meaningful
    # Fires on uniform noise as hard as on the real thing: broken, not successful.
    assert not statistic(0.9, 0.9).is_meaningful
    assert not statistic(0.2, -0.4).is_meaningful, "the control's magnitude counts, not its sign"
    assert not statistic(0.0, 0.0).is_meaningful
    assert not statistic(-0.1, 0.0).is_meaningful


# ---------------------------------------------------------------------------------------------
# the primal leftovers
# ---------------------------------------------------------------------------------------------

#: Easy enough that LLL alone recovers the planted vector (measured: success at every block size).
EASY = (17, 40)
#: The calibrated instance from the repo's own attack tests: LLL fails, and so does BKZ-5.
HARD = (32, 76)


@pytest.fixture(scope="module")
def easy_instance():
    return make_instance(*EASY, seed=1)


def test_the_sweep_confirms_past_the_first_success_when_asked(engine, easy_instance):
    """``stop_after_successes = 2`` runs exactly one confirmation and then stops; the minimum stays
    the *first* success rather than moving to the last one run."""
    block_sizes = [2, 10, 20, 30]

    minimum_one, one = find_minimum_successful_block_size(easy_instance, engine, block_sizes)
    minimum_two, two = find_minimum_successful_block_size(
        easy_instance, engine, block_sizes, stop_after_successes=2
    )
    assert [r.block_size for r in one] == [2]
    assert [r.block_size for r in two] == [2, 10]
    assert all(r.recovered and r.provenance == MEASURED for r in two)
    assert minimum_one == minimum_two == 2


def test_a_success_count_that_is_never_reached_runs_the_whole_range(engine, easy_instance):
    minimum, results = find_minimum_successful_block_size(
        easy_instance, engine, [10, 2, 20], stop_after_successes=10
    )
    assert [r.block_size for r in results] == [2, 10, 20], "swept in ascending order, all recorded"
    assert minimum == 2


@pytest.mark.slow
def test_an_exhausted_range_returns_none_with_every_failure_recorded(engine):
    """No block size in the range recovers, and the sweep says so with the evidence attached:
    ``None`` for the minimum, and one measured, unrecovered result per block size tried."""
    instance = make_instance(*HARD, seed=1)
    minimum, results = find_minimum_successful_block_size(instance, engine, [2, 5])

    assert minimum is None
    assert [r.block_size for r in results] == [2, 5]
    for r in results:
        assert r.provenance == MEASURED, "a failure is a measurement, not a refusal"
        assert r.recovered is False
        assert r.recovered_vector is None
        assert r.dimension == instance.m + 1
        assert r.wall_clock_s > 0


def test_an_oversized_block_size_is_not_run_with_the_engines_reason(engine, easy_instance):
    """The existing test accepts either provenance, which any non-raising outcome satisfies. The
    engine refuses this block size, so the only correct record is a refusal that says why."""
    prepared = prepare_primal(easy_instance)
    basis = prepared[2]
    oversized = basis.nrows + 5

    result = run_primal_attack(easy_instance, engine, oversized, prepared=prepared)

    assert result.provenance == NOT_RUN
    assert f"block size {oversized} exceeds the basis dimension {basis.nrows}" in (
        result.not_run_reason
    )
    assert result.recovered is False
    assert result.recovered_vector is None
    assert result.dimension == basis.nrows
    assert result.block_size == oversized
    assert result.engine == "fpylll_bkz"
    assert result.threads is None, "nothing ran, so no thread count ran either"
    assert result.wall_clock_s == 0.0


def test_a_refused_point_inside_a_sweep_is_recorded_and_does_not_end_it(engine, easy_instance):
    """Block size 1 is refused by the engine; the sweep records it and carries on to 2."""
    minimum, results = find_minimum_successful_block_size(easy_instance, engine, [1, 2])
    assert [(r.block_size, r.provenance) for r in results] == [(1, NOT_RUN), (2, MEASURED)]
    assert "below 2" in results[0].not_run_reason
    assert minimum == 2


def test_a_vector_of_the_wrong_length_cannot_be_read_as_a_secret(easy_instance):
    nf, _, basis, planted = prepare_primal(easy_instance)
    assert len(planted) == nf.m + nf.n + 1 == basis.ncols
    with pytest.raises(ValueError, match=f"length {len(planted) - 1}, expected {len(planted)}"):
        recover_secret_from_vector(planted[:-1], nf, easy_instance)
    with pytest.raises(ValueError, match=f"expected {len(planted)}"):
        recover_secret_from_vector(tuple(planted) + (0,), nf, easy_instance)
    # And the right length still round-trips, so the refusal is about length and nothing else.
    assert recover_secret_from_vector(planted, nf, easy_instance) == tuple(easy_instance.secret_s)
