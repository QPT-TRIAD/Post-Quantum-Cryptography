"""The negative control must be a control — and ``build_instance``, which had no test of its own.

``pipeline.py`` describes ``random_lattice_control`` as *"a q-ary lattice with **no planted
vector**. It is the negative control: a correct attack must fail to recover anything."* and gives
the reason it matters: *"Without it, 'the attack succeeded' carries no weight — a probe that always
fires and an attack that always succeeds are indistinguishable from correct ones."*

What ``build_instance`` returned for that source until 2026-09-20 was a ``LatticeQLWRInstance`` built
exactly as the ``synthetic_scaled`` one is — a uniform base, a uniform secret, and samples *derived from that
secret* — differing only in its label and in which seed it records. It was a genuine planted
instance, the primal attack recovered it at block size 2, and the project therefore had no negative
control: the one experiment that could show the attack firing on nothing could not fail to fire.
The control now draws its samples uniformly (``LatticeQLWRInstance.control_samples``).

Each control test here is two-sided, because a control is only evidence next to the thing it
controls for. The ``synthetic_scaled`` half of each pair always passed and is a test in its own
right; the ``random_lattice_control`` half was ``xfail(strict=True)`` until ``src`` drew a control
with nothing planted in it, and passes now with the markers removed. One of the pairs deliberately does not go through the project's attack
at all: it builds the embedding from the *public* data alone — base, samples, modulus — so that it
says something about the instance and not about whichever code path is asked to attack it.
"""

from __future__ import annotations

import math

import pytest
from fpylll import LLL, IntegerMatrix
from hypothesis import given, settings
from hypothesis import strategies as st

from qlwr_lattice_stress.attacks import (
    find_minimum_successful_block_size,
    prepare_primal,
    run_primal_attack,
)
from qlwr_lattice_stress.config.schema import ExperimentConfig
from qlwr_lattice_stress.engines import FpylllBKZEngine
from qlwr_lattice_stress.pipeline import build_instance
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)
from qlwr_lattice_stress.protocols import MEASURED
from qlwr_lattice_stress.utils.seeding import RunSeeds

#: Historical: the defect as it stood before it was fixed on 2026-09-20, kept as the record of what
#: the tests below were written against. It was the xfail reason; nothing reads it now.
CONTROL_IS_PLANTED = (
    "src/qlwr_lattice_stress/pipeline.py:90-103 — the RANDOM_LATTICE_CONTROL branch of "
    "build_instance returns LatticeQLWRInstance(secret_s=<uniform>, base=<uniform>), whose samples "
    "are derived from that secret exactly as in the synthetic branch (:105-112); only `seed` and "
    "`label` differ. Reproduce: build_instance(ExperimentConfig.model_validate({'instance': "
    "{'source': 'random_lattice_control', 'target_dimension': 40}}), RunSeeds(root=20260913)) -> "
    "find_minimum_successful_block_size(inst, FpylllBKZEngine(threads=1), [2, 10, 20]) == (2, ...)."
)

DIMENSION = 40
SMALL_BLOCK_SIZES = (2, 10, 20)
DEFAULT_SEED = 20260913

#: The embedding factor for the public-data embedding below. At ``M = 1`` the lifted samples put
#: ``(0, ..., 0, p)`` of norm 256 in the lattice (``notes/05``), which would be the shortest vector
#: of *either* instance and hide the difference between them. At 4 that artifact has norm 1024,
#: above the Gaussian heuristic of about 807, and is out of the way.
PUBLIC_EMBEDDING_FACTOR = 4

#: Where "consistent with the Gaussian heuristic" is separated from "planted". Measured at this
#: dimension: a planted instance gives 0.55 to 0.69 of the heuristic; a simulated genuine control
#: (uniform samples over the same base, six seeds, BKZ-20) gives 1.01 to 1.16. Nothing lands between.
HEURISTIC_FRACTION = 0.85


def config_for(source: str, dimension: int = DIMENSION, **instance_fields) -> ExperimentConfig:
    return ExperimentConfig.model_validate(
        {"instance": {"source": source, "target_dimension": dimension, **instance_fields}}
    )


def build(source: str, dimension: int = DIMENSION, seed: int = DEFAULT_SEED, **instance_fields):
    config = config_for(source, dimension, seed=seed, **instance_fields)
    return build_instance(config, RunSeeds(root=seed))


def engine() -> FpylllBKZEngine:
    """Single-threaded, always. fpylll ignores the argument, but the project's rule is that every
    engine in a test is constructed at one thread, because G6K is not reproducible above it."""
    return FpylllBKZEngine(threads=1)


@pytest.fixture(scope="module")
def synthetic() -> LatticeQLWRInstance:
    return build("synthetic_scaled")


@pytest.fixture(scope="module")
def control() -> LatticeQLWRInstance:
    return build("random_lattice_control")


# ---------------------------------------------------------------------------------------------
# the public-data embedding: what an attacker sees, with none of the project's attack code
# ---------------------------------------------------------------------------------------------


def public_embedding(instance, factor: int) -> IntegerMatrix:
    """Kannan embedding of the samples into ``Lambda = {A c + q z}``, from public data only.

    ``Lambda`` lives in the sample space ``Z^m`` and has volume ``q^(m - nu)``. A planted instance
    has ``dist(b, Lambda) = ||e||``, so ``(e, M)`` is in this lattice and is far shorter than
    anything else in it. With uniform samples ``b`` is a generic point, and the shortest vector is
    whatever the Gaussian heuristic says it is. No normal form, no pivot, no recorded secret or
    error: nothing the instance could use to tell the test what to find.
    """
    q, m, nu = instance.q_l, instance.m, instance.nu
    generators = IntegerMatrix(nu + m, m, int_type="mpz")
    for j in range(nu):
        for i in range(m):
            generators[j, i] = int(instance.base[i][j])
    for i in range(m):
        generators[nu + i, i] = q
    LLL.reduction(generators)  # moves the nu dependencies to zero rows, leaving a basis below them

    embedded = IntegerMatrix(m + 1, m + 1, int_type="mpz")
    for i in range(m):
        for j in range(m):
            embedded[i, j] = generators[nu + i, j]
    for j, value in enumerate(instance.public_samples()):
        embedded[m, j] = int(value)
    embedded[m, m] = factor
    return embedded


def shortest_norm_after_reduction(instance, block_size: int = 20) -> float:
    reduced = engine().reduce(public_embedding(instance, PUBLIC_EMBEDDING_FACTOR), block_size).basis
    return math.sqrt(
        min(
            sum(int(reduced[i, j]) ** 2 for j in range(reduced.ncols))
            for i in range(reduced.nrows)
        )
    )


def public_gaussian_heuristic(instance) -> float:
    d = instance.m + 1
    log_volume = (instance.m - instance.nu) * math.log(instance.q_l) + math.log(PUBLIC_EMBEDDING_FACTOR)
    return math.sqrt(d / (2.0 * math.pi * math.e)) * math.exp(log_volume / d)


def centred_residuals(instance) -> list[int]:
    """``A s - b (mod q)``, centred, for the secret the instance records — in Python integers."""
    q = instance.q_l
    residuals = []
    for row, sample in zip(instance.base, instance.public_samples()):
        r = (sum(int(x) * int(s) for x, s in zip(row, instance.secret_s)) - int(sample)) % q
        residuals.append(r - q if r > q // 2 else r)
    return residuals


# ---------------------------------------------------------------------------------------------
# (a) the attack: recovered on the planted instance, not on the control
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("block_size", SMALL_BLOCK_SIZES)
def test_the_synthetic_instance_is_recovered_at_small_block_sizes(synthetic, block_size):
    """The positive half, on its own so that it is visible as a passing test.

    Without it the control test below would be satisfied by an attack that recovers nothing from
    anything — the mirror image of the defect it is written for.
    """
    result = run_primal_attack(synthetic, engine(), block_size)
    assert result.provenance == MEASURED
    assert result.recovered is True
    assert result.recovered_vector is not None


@pytest.mark.parametrize("block_size", SMALL_BLOCK_SIZES)
def test_the_control_is_not_recovered_where_the_synthetic_instance_is(synthetic, control, block_size):
    """Same dimension, same block size, same engine: recovered on one and not on the other."""
    assert control.m == synthetic.m and control.nu == synthetic.nu

    on_synthetic = run_primal_attack(synthetic, engine(), block_size)
    on_control = run_primal_attack(control, engine(), block_size)

    assert on_synthetic.recovered is True
    assert on_control.provenance == MEASURED, "a refusal is not a failed recovery"
    assert on_control.recovered is False
    assert on_control.recovered_vector is None


# ---------------------------------------------------------------------------------------------
# (b) the instance itself: nothing short is planted in it
# ---------------------------------------------------------------------------------------------


def test_the_synthetic_instance_has_a_planted_vector_far_below_the_heuristic(synthetic):
    """The positive half of (b), from public data. The shortest vector BKZ-20 finds is *exactly*
    ``(e, M)`` in norm — ``||e||^2 + M^2``, integer for integer — and is well under the Gaussian
    heuristic, which is what "planted" means."""
    found = shortest_norm_after_reduction(synthetic)
    planted_norm_squared = sum(e * e for e in synthetic.error_vector()) + PUBLIC_EMBEDDING_FACTOR**2
    assert round(found**2) == planted_norm_squared
    assert found < HEURISTIC_FRACTION * public_gaussian_heuristic(synthetic)


def test_the_controls_shortest_vector_is_consistent_with_the_gaussian_heuristic(control):
    """The control half of (b). After the same reduction of the same public-data embedding, the
    shortest vector of a lattice with nothing planted in it sits at the Gaussian heuristic — not at
    ``sqrt(m) * 74``, which is where a rounding-error vector sits and where today's is found."""
    found = shortest_norm_after_reduction(control)
    heuristic = public_gaussian_heuristic(control)
    assert found > HEURISTIC_FRACTION * heuristic, (found, heuristic)
    # And not absurdly above it either: a reduction that returned nothing short at all would be a
    # broken reduction, not a control.
    assert found < 1.5 * heuristic


def test_the_synthetic_samples_are_within_the_noise_bound_of_the_secret(synthetic):
    """The positive half of the relation check: ``A s - b`` is small for the recorded secret."""
    assert max(abs(r) for r in centred_residuals(synthetic)) <= synthetic.noise_bound


def test_the_controls_samples_are_not_explained_by_any_secret_it_records(control):
    """``check_relation()`` cannot make this distinction — ``exact_error`` *defines* ``e`` as the
    residual, so the identity holds for any samples whatever. What distinguishes a planted instance
    is that the residual is **small**. For a control it must not be: uniform samples leave a
    residual spread over all of ``Z_q``, and a maximum inside the noise bound over 40 rows has
    probability ``(257 / 65536)^40``."""
    residuals = centred_residuals(control)
    assert max(abs(r) for r in residuals) > control.noise_bound
    # Stronger, and still overwhelmingly certain for uniform samples: most rows are outside.
    outside = sum(abs(r) > control.noise_bound for r in residuals)
    assert outside > len(residuals) // 2


def test_the_control_offers_the_attack_no_short_planted_vector(control):
    """Through the project's own preparation. Either ``prepare_primal`` refuses the control — it has
    no small-secret normal form, so ``check_small`` raising is a legitimate outcome — or the vector
    it reports as "planted" is not short: at or above the embedded lattice's Gaussian heuristic.
    Today it returns a planted vector of norm about 450 against a heuristic of about 780."""
    try:
        nf, factor, basis, planted = prepare_primal(control)
    except (AssertionError, ValueError):
        return
    d = basis.nrows
    heuristic = math.sqrt(d / (2.0 * math.pi * math.e)) * math.exp(
        (nf.m * math.log(nf.q) + math.log(factor)) / d
    )
    assert math.sqrt(sum(v * v for v in planted)) > HEURISTIC_FRACTION * heuristic


# ---------------------------------------------------------------------------------------------
# (c) the sweep
# ---------------------------------------------------------------------------------------------


def test_the_sweep_finds_a_minimum_on_the_synthetic_instance(synthetic):
    minimum, results = find_minimum_successful_block_size(synthetic, engine(), SMALL_BLOCK_SIZES)
    assert minimum == 2
    assert [r.recovered for r in results] == [True]


def test_the_sweep_finds_no_minimum_on_the_control(control):
    """``None`` over the whole small range, with every point attempted, measured, and failed —
    rather than ``None`` because nothing ran."""
    minimum, results = find_minimum_successful_block_size(control, engine(), SMALL_BLOCK_SIZES)
    assert minimum is None
    assert [r.block_size for r in results] == list(SMALL_BLOCK_SIZES)
    assert all(r.provenance == MEASURED for r in results)
    assert not any(r.recovered for r in results)


# ---------------------------------------------------------------------------------------------
# build_instance — shape, ratio, moduli, seeds
# ---------------------------------------------------------------------------------------------

SWEEP_DIMENSIONS = (40, 60, 80, 100, 130, 160)
SOURCES = ("synthetic_scaled", "random_lattice_control")


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("dimension", SWEEP_DIMENSIONS)
def test_the_sample_count_is_the_target_dimension_and_nu_follows_the_ratio(source, dimension):
    """``m == target_dimension`` and ``nu == max(2, round(m * 256 / 608))`` at every dimension the
    shipped sweep uses — so the ratio the scaling rule exists to preserve is preserved to within
    the half-unit that rounding allows, and never drifts with the dimension."""
    instance = build(source, dimension)
    assert instance.m == dimension
    assert instance.nu == max(2, round(dimension * 256 / 608))
    assert abs(instance.nu - dimension * 256 / 608) <= 0.5
    assert len(instance.base) == dimension
    assert all(len(row) == instance.nu for row in instance.base)
    assert len(instance.secret_s) == instance.nu


@pytest.mark.parametrize(
    "ratio,dimension,expected_nu",
    [((1, 4), 40, 10), ((1, 2), 40, 20), ((3, 10), 50, 15), ((1, 100), 8, 2), ((1, 100), 40, 2)],
)
def test_a_configured_ratio_is_honoured_and_nu_never_falls_below_two(ratio, dimension, expected_nu):
    instance = build("synthetic_scaled", dimension, nu_over_m=ratio)
    assert (instance.nu, instance.m) == (expected_nu, dimension)


@pytest.mark.parametrize("source", SOURCES)
@pytest.mark.parametrize("dimension", (8, 40, 100))
def test_the_moduli_are_the_recorded_production_pair_at_every_dimension(source, dimension, production_modulus):
    """``q = 2^16, p = 2^8``, held fixed: a scaled instance that changed either would not be a
    scaled instance of anything."""
    instance = build(source, dimension)
    assert (instance.q_l, instance.p) == production_modulus == (1 << 16, 1 << 8)
    assert instance.noise_bound == 128
    assert instance.is_bit_shift_rounding


@pytest.mark.parametrize("source", SOURCES)
def test_the_instance_is_labelled_with_its_source_and_is_well_formed(source):
    instance = build(source)
    assert isinstance(instance, LatticeQLWRInstance)
    assert instance.label == source
    assert all(type(v) is int and 0 <= v < instance.q_l for v in instance.secret_s)
    assert all(type(v) is int and 0 <= v < instance.q_l for row in instance.base for v in row)
    assert full_column_rank_mod([list(r) for r in instance.base], instance.q_l, instance.nu) == instance.nu


def test_the_synthetic_instance_satisfies_its_relation():
    instance = build("synthetic_scaled")
    instance.check_relation()
    assert all(-128 <= e <= 127 for e in instance.error_vector())


@pytest.mark.parametrize("source", SOURCES)
def test_the_same_root_seed_builds_the_identical_instance(source):
    """Equality of the whole dataclass — base, secret, recorded seed and label — from two separate
    ``RunSeeds`` objects, so nothing is shared between the two builds but the integer."""
    first, second = build(source, seed=7), build(source, seed=7)
    assert first is not second
    assert first == second
    assert first.public_samples() == second.public_samples()


@pytest.mark.parametrize("source", SOURCES)
def test_different_root_seeds_build_different_instances(source):
    built = [build(source, seed=seed) for seed in (1, 2, 3, DEFAULT_SEED)]
    assert len({instance.base for instance in built}) == len(built)
    assert len({instance.secret_s for instance in built}) == len(built)
    assert len({instance.seed for instance in built}) == len(built)


def test_the_two_sources_do_not_share_a_draw():
    """Same root, different source: the streams are named by source, so the control is not the
    synthetic instance under another label."""
    synthetic, control = build("synthetic_scaled", seed=7), build("random_lattice_control", seed=7)
    assert synthetic.base != control.base
    assert synthetic.secret_s != control.secret_s or synthetic.public_samples() != control.public_samples()
    assert synthetic.seed == 7


def test_a_published_reference_builds_no_lattice_instance():
    config = config_for("published_reference", reference_scheme="Kyber512")
    with pytest.raises(ValueError, match="published_reference produces no lattice instance"):
        build_instance(config, RunSeeds(root=1))


@settings(deadline=None, max_examples=25)
@given(
    dimension=st.integers(min_value=8, max_value=64),
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    ratio=st.sampled_from([(256, 608), (1, 4), (1, 2), (2, 5)]),
)
def test_every_built_synthetic_instance_has_the_configured_shape_and_a_true_relation(dimension, seed, ratio):
    instance = build("synthetic_scaled", dimension, seed=seed, nu_over_m=ratio)
    assert instance.m == dimension
    assert instance.nu == max(2, round(dimension * ratio[0] / ratio[1]))
    assert (instance.q_l, instance.p, instance.seed) == (1 << 16, 1 << 8, seed)
    instance.check_relation()
    assert build("synthetic_scaled", dimension, seed=seed, nu_over_m=ratio) == instance
