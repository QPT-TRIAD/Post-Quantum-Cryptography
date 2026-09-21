"""The problem layer, tested directly: the relation, the search space, and the two controls.

Everything downstream treats this layer as ground truth. The circuits are compared *to*
``QLWRInstance.marked_set()``, the success curves are compared *to* ``SearchSpace.success_probability``
and the probes are judged against the two control specs — so until now the layer was exercised by
every test and checked by none. A wrong rounding boundary here would not fail anything: both lowerings
would faithfully reproduce it, and the closed form would faithfully describe the wrong ``M``.

The tests below therefore never ask the layer to agree with itself. The relation is transcribed again
in ``fractions`` arithmetic (:func:`reference_relation`), genericity is re-derived from trial division and
a set of excluded forms, and the closed form is re-derived from ``math`` alone. Where the property is
algebraic rather than numeric — the redundancy of the inner ``mod q_L``, the XOR-closure of the planted
period, the ``(1 - 2M/N)**2`` floor on the success probability at the textbook optimum — it is a
hypothesis property, because those are statements about every instance and a single worked instance
supports none of them.

One thing is patched, once, and it is not the unit under test: ``_choose_parameters`` is replaced to
hand the generator a single-row base. No reachable argument produces a non-unique marked set (the
chosen ``m`` is two above the uniqueness inequality and every seed tried is unique on its first draw),
so the rejection loop, ``require_unique`` and the exhaustion error are otherwise unreachable.
"""

from __future__ import annotations

import dataclasses
import math
from fractions import Fraction

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from grover_emulator.problem import qlwr_instance as qlwr_module
from grover_emulator.problem.oracle_spec import (
    HiddenPeriodOracleSpec,
    Lowering,
    QLWROracleSpec,
    RandomControlOracleSpec,
)
from grover_emulator.problem.qlwr_instance import (
    QLWRInstance,
    generate_scaled_instance,
    is_generic_prime,
    largest_generic_prime_below,
    round_half_up,
)
from grover_emulator.problem.search_space import SearchSpace, theoretical_optimal_iterations
from grover_emulator.utils.validation import assert_predicate_matches_spec

# The worked instance's numbers, as literals. notes/01-arithmetic.md states them; a test that read
# them back out of the generator would be asserting that the generator equals itself.
DEFAULT_SEED = 20260913
GOLDEN_SECRET = (43, 16)
GOLDEN_MARKED = 1067  # 43 + 16 * 2**6, the secret in the register's little-endian component order
GENERIC_PRIMES_BELOW_64 = [11, 13, 19, 23, 29, 37, 41, 43, 47, 53, 59, 61]


# -----------------------------------------------------------------------------------------------
# independent references
# -----------------------------------------------------------------------------------------------


def reference_relation(q_l, p, base, s, *, reduce=True):
    """``F_s(X)`` written out again from the relation's statement, in ``fractions`` arithmetic.

    ``round(u * p / q_L) mod p`` with round-to-nearest spelled as ``floor(x + 1/2)`` over an exact
    rational. It shares no code with ``round_half_up``, which is the point: the module's one rounding
    definition is what the circuit's interval test is built from, so it has to be checked against
    something that is not it.
    """
    out = []
    for row in base:
        u = sum(x * sj for x, sj in zip(row, s))
        if reduce:
            u %= q_l
        out.append(math.floor(Fraction(u * p, q_l) + Fraction(1, 2)) % p)
    return tuple(out)


def reference_marked_set(inst: QLWRInstance) -> frozenset[int]:
    """Every register value whose components are all below ``q_L`` and reproduce the target."""
    w = (inst.q_l - 1).bit_length()
    target = reference_relation(inst.q_l, inst.p, inst.base, inst.secret_s)
    marked = set()
    for x in range(1 << (inst.nu * w)):
        s = tuple((x >> (j * w)) & ((1 << w) - 1) for j in range(inst.nu))
        if any(v >= inst.q_l for v in s):
            continue
        if reference_relation(inst.q_l, inst.p, inst.base, s) == target:
            marked.add(x)
    return frozenset(marked)


def reference_is_generic_prime(x: int) -> bool:
    """Prime by trial division over every smaller integer, and not ``2**k`` or ``2**k +- 1``."""
    if x < 2 or any(x % d == 0 for d in range(2, x)):
        return False
    special = set()
    for k in range(x.bit_length() + 2):
        special.update({1 << k, (1 << k) - 1, (1 << k) + 1})
    return x not in special


def small_instance(**overrides) -> QLWRInstance:
    """A hand-written instance over an 8-qubit register, small enough to enumerate in every test.

    ``q_L = 13`` leaves three of every sixteen component values invalid, so the embedding gap is
    exercised, and the marked set is *not* a singleton — the class does not require uniqueness, only
    the generator does, and a test that only ever saw ``M = 1`` would not notice a predicate that
    marked the secret and nothing else by construction.
    """
    fields = dict(q_l=13, nu=2, m=2, p=11, secret_s=(5, 9), base=((1, 2), (3, 4)))
    fields.update(overrides)
    return QLWRInstance(**fields)


# -----------------------------------------------------------------------------------------------
# round_half_up
# -----------------------------------------------------------------------------------------------


@settings(deadline=None, max_examples=300)
@given(st.integers(-(10**9), 10**9), st.integers(1, 10**6))
def test_round_half_up_is_floor_of_the_exact_quotient_plus_a_half(numerator, denominator):
    """Exact for every integer numerator, negative ones included, and never more than 1/2 away."""
    got = round_half_up(numerator, denominator)
    exact = Fraction(numerator, denominator)
    assert got == math.floor(exact + Fraction(1, 2))
    assert abs(got - exact) <= Fraction(1, 2)


@settings(deadline=None, max_examples=200)
@given(st.integers(-(10**6), 10**6), st.integers(1, 10**4))
def test_an_exact_half_rounds_up_on_both_sides_of_zero(k, half_denominator):
    """``(2k + 1) / 2`` rounds to ``k + 1`` whatever the sign: toward plus infinity, not away from 0.

    The tie is the case a float would get wrong and the one the circuit's interval boundaries sit
    on, so it is drawn deliberately rather than left for the general property to stumble into. The
    fraction is left unreduced on purpose — ``(2k+1)*d / 2d`` is the same tie.
    """
    assert round_half_up((2 * k + 1) * half_denominator, 2 * half_denominator) == k + 1


def test_round_half_up_at_the_values_the_relation_actually_meets():
    assert round_half_up(0, 61) == 0
    assert round_half_up(60 * 19, 61) == 19  # the wrap bucket: rounds to p, which is 0 mod p
    assert round_half_up(3, 2) == 2
    assert round_half_up(-3, 2) == -1
    assert round_half_up(-1, 2) == 0
    assert round_half_up(7, 7) == 1


@pytest.mark.parametrize("denominator", [0, -1, -61])
def test_round_half_up_refuses_a_non_positive_denominator(denominator):
    with pytest.raises(ValueError, match="denominator must be positive"):
        round_half_up(5, denominator)


# -----------------------------------------------------------------------------------------------
# generic primes
# -----------------------------------------------------------------------------------------------


def test_the_generic_primes_below_64_are_the_twelve_the_notes_list():
    """The literal list, and the same list re-derived from trial division minus the special forms.

    The excluded primes below 64 are 2, 3, 5, 7, 17 and 31: each is a power of two or one away from
    one. 61 surviving is what makes ``q_L = 61`` the worked instance's modulus.
    """
    assert [x for x in range(64) if is_generic_prime(x)] == GENERIC_PRIMES_BELOW_64
    assert [x for x in range(64) if reference_is_generic_prime(x)] == GENERIC_PRIMES_BELOW_64


@settings(deadline=None, max_examples=300)
@given(st.integers(-10, 5000))
def test_genericity_agrees_with_trial_division_minus_the_special_forms(x):
    assert is_generic_prime(x) is reference_is_generic_prime(x)


@pytest.mark.parametrize("x", [-7, 0, 1, 2, 3, 5, 7, 17, 31, 127, 257, 8191, 65537])
def test_special_form_and_degenerate_values_are_never_generic(x):
    """Fermat and Mersenne primes are prime and still refused; so is everything below 2."""
    assert is_generic_prime(x) is False


@pytest.mark.parametrize("x", [9, 15, 21, 25, 49, 121, 3599])
def test_a_composite_that_is_not_of_special_form_is_still_not_generic(x):
    """3599 = 59 * 61: the trial division has to run all the way to the square root."""
    assert is_generic_prime(x) is False


@pytest.mark.parametrize(
    "bound, expected",
    [(64, 61), (62, 61), (61, 59), (32, 29), (16, 13), (12, 11), (11, None), (8, None), (0, None), (-5, None)],
)
def test_largest_generic_prime_below_is_strict_and_none_when_there_is_none(bound, expected):
    """Strictly below: the bound itself is excluded even when it is generic (61 -> 59, 11 -> None)."""
    assert largest_generic_prime_below(bound) == expected


@settings(deadline=None, max_examples=100)
@given(st.integers(12, 5000))
def test_largest_generic_prime_below_skips_nothing(bound):
    found = largest_generic_prime_below(bound)
    assert found is not None and found < bound
    assert reference_is_generic_prime(found)
    assert not any(reference_is_generic_prime(x) for x in range(found + 1, bound))


# -----------------------------------------------------------------------------------------------
# QLWRInstance: the relation and the marking predicate
# -----------------------------------------------------------------------------------------------


def test_evaluate_is_the_relation_as_written_on_every_valid_secret():
    inst = small_instance()
    for s0 in range(inst.q_l):
        for s1 in range(inst.q_l):
            assert inst.evaluate((s0, s1)) == reference_relation(inst.q_l, inst.p, inst.base, (s0, s1))


def test_the_target_is_the_relation_applied_to_the_real_secret(qlwr_instance):
    inst = qlwr_instance
    want = reference_relation(inst.q_l, inst.p, inst.base, inst.secret_s)
    assert inst.target == want
    assert len(inst.target) == inst.m
    assert all(0 <= a < inst.p for a in inst.target)


def test_is_solution_agrees_with_the_transcribed_relation_on_every_register_value():
    """Exhaustive, on an instance with more than one marked value and a non-trivial invalid region."""
    inst = small_instance()
    want = reference_marked_set(inst)
    assert len(want) > 1, "the hand-written instance is meant to be non-unique"
    for x in range(1 << inst.n_search):
        assert inst.is_solution(x) is (x in want), f"is_solution disagrees at x={x}"
    assert inst.marked_set() == want


def test_the_worked_instance_marks_exactly_what_the_transcribed_relation_marks(qlwr_instance):
    """All 4096 register values of the instance every other test file uses as its reference."""
    assert qlwr_instance.marked_set() == reference_marked_set(qlwr_instance) == frozenset({GOLDEN_MARKED})


def test_the_real_secret_is_marked_and_invalid_encodings_never_are():
    """An out-of-range component encodes no secret, even when it is congruent to the real one.

    ``(5 + 13, 9)`` reduces to the secret mod ``q_L`` and fits in the 4-bit component, so a predicate
    that skipped the validity test would mark it — that is the relation the docstring says it would
    be wrong to describe.
    """
    inst = small_instance(secret_s=(2, 9))
    w = inst.w
    encoded_secret = 2 | (9 << w)
    assert inst.is_solution(encoded_secret) is True

    alias = (2 + inst.q_l) | (9 << w)
    assert alias < (1 << inst.n_search)
    assert inst.is_valid(alias) is False
    assert inst.evaluate(inst.decode(alias)) == inst.target  # it *would* match, were it a secret
    assert inst.is_solution(alias) is False

    invalid = [x for x in range(1 << inst.n_search) if not inst.is_valid(x)]
    assert len(invalid) == inst.embedding_gap
    assert not any(inst.is_solution(x) for x in invalid)


@pytest.mark.parametrize("candidate", [-1, 256, 10**6])
def test_is_solution_refuses_a_value_outside_the_register(candidate):
    with pytest.raises(ValueError, match="outside the search register"):
        small_instance().is_solution(candidate)


def test_decode_splits_the_register_little_endian_by_component(qlwr_instance):
    inst = qlwr_instance
    assert inst.decode(GOLDEN_MARKED) == GOLDEN_SECRET
    assert inst.decode(0) == (0, 0)
    assert inst.decode((1 << 12) - 1) == (63, 63)
    assert inst.decode(1 << 6) == (0, 1)
    for x in (0, 1, 63, 64, 1067, 4095):
        s = inst.decode(x)
        assert sum(v << (j * inst.w) for j, v in enumerate(s)) == x


def test_is_valid_is_componentwise_below_the_modulus(qlwr_instance):
    inst = qlwr_instance
    assert inst.is_valid(60 | (60 << 6)) is True
    assert inst.is_valid(61) is False
    assert inst.is_valid(61 << 6) is False
    assert sum(inst.is_valid(x) for x in range(1 << 12)) == 61**2


def test_the_embedding_gap_of_the_worked_instance_is_375(qlwr_instance):
    """``2**12 - 61**2``. The report quotes it as a faithfulness caveat, so it is pinned as a literal."""
    assert qlwr_instance.embedding_gap == 375 == 4096 - 3721
    assert small_instance().embedding_gap == 256 - 169


def test_sample_raw_rounded_and_inner_product_are_the_pieces_of_evaluate():
    inst = small_instance()
    assert inst.w == 4 and inst.n_search == 8
    assert inst.inner_product(1, (5, 9)) == (3 * 5 + 4 * 9) % 13
    assert dataclasses.replace(inst, reduce_mod_ql=False).inner_product(1, (5, 9)) == 51
    # 12 * 11 / 13 = 10.15..., which rounds to 10.
    assert inst.raw_rounded(12) == 10
    assert [inst.sample(v) for v in range(13)] == [
        math.floor(Fraction(v * 11, 13) + Fraction(1, 2)) % 11 for v in range(13)
    ]
    # The wrap bucket: 60 * 19 / 61 = 18.69 rounds to p itself, which is 0 in Z_p.
    wrap = QLWRInstance(q_l=61, nu=1, m=1, p=19, secret_s=(1,), base=((1,),))
    assert wrap.raw_rounded(60) == 19
    assert wrap.sample(60) == 0


def test_describe_reports_the_measured_marked_set_and_the_chosen_parameters(qlwr_instance):
    d = qlwr_instance.describe()
    assert (d["q_l"], d["p"], d["nu"], d["m"]) == (61, 19, 2, 7)
    assert d["n_search"] == 12 and d["n_items"] == 4096
    assert d["n_marked"] == 1
    assert d["embedding_gap"] == 375
    assert d["base_rank"] == 2
    assert d["seed"] == DEFAULT_SEED
    assert d["rounding_gap_bits"] == pytest.approx(math.log2(61 / 19))
    # The inequality the record states; the generator's m is two above its ceiling.
    assert math.ceil(d["uniqueness_inequality_min_m"]) + 2 == d["m"]


# -- __post_init__ ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides, message",
    [
        (dict(q_l=31, p=11, secret_s=(5, 9)), "q_l=31 must be a generic prime"),  # Mersenne
        (dict(q_l=17, p=11), "q_l=17 must be a generic prime"),  # Fermat
        (dict(q_l=15, p=11), "q_l=15 must be a generic prime"),  # composite
        (dict(q_l=2, p=2), "q_l=2 must be a generic prime"),
        (dict(p=7), "p=7 must be a generic prime"),
        (dict(p=9), "p=9 must be a generic prime"),
        (dict(p=19), "p=19 exceeds q_l=13"),
        (dict(secret_s=(5,)), "secret_s has 1 entries, expected nu=2"),
        (dict(secret_s=(5, 9, 1)), "secret_s has 3 entries, expected nu=2"),
        (dict(secret_s=(5, 13)), r"outside \[0, q_l\)"),
        (dict(secret_s=(-1, 9)), r"outside \[0, q_l\)"),
        (dict(m=3), "base has 2 rows, expected m=3"),
        (dict(base=((1, 2), (3,))), "every base row must have nu=2 entries"),
        (dict(base=((1, 2), (2, 4))), "column rank 1"),
        (dict(base=((1, 2), (14, 15))), "column rank 1"),  # equal rows once reduced mod 13
        (dict(base=((0, 0), (0, 0))), "column rank 0"),
    ],
)
def test_a_malformed_instance_is_refused_at_construction(overrides, message):
    with pytest.raises(ValueError, match=message):
        small_instance(**overrides)


def test_equal_moduli_and_a_tall_base_are_accepted():
    """The refusals above are not a blanket one: ``p == q_L`` is legal, and so is ``m > nu``."""
    inst = small_instance(p=13, m=3, base=((1, 2), (2, 4), (0, 1)))
    assert inst.target == tuple(v % 13 for v in (5 + 18, 10 + 36, 9))


def test_an_instance_is_immutable():
    inst = small_instance()
    with pytest.raises(dataclasses.FrozenInstanceError):
        inst.p = 11


# -- the redundancy of the inner reduction ---------------------------------------------------------


@st.composite
def arbitrary_instances(draw):
    """Any legal instance over at most 12 search qubits — *not* only the unique ones.

    Drawn by hand rather than through the generator because the identity is about the relation, and
    the generator only ever returns the ``M = 1`` corner of it. Entries of the base are drawn up to
    ``4 * q_L`` so the unreduced inner product runs many multiples of ``q_L`` past the modulus.
    """
    q_l = draw(st.sampled_from(GENERIC_PRIMES_BELOW_64))
    p = draw(st.sampled_from([g for g in GENERIC_PRIMES_BELOW_64 if g <= q_l]))
    nu = draw(st.integers(1, 2))
    m = draw(st.integers(nu, 4))
    base = tuple(
        tuple(draw(st.integers(0, 4 * q_l)) for _ in range(nu)) for _ in range(m)
    )
    secret = tuple(draw(st.integers(0, q_l - 1)) for _ in range(nu))
    return dict(q_l=q_l, nu=nu, m=m, p=p, secret_s=secret, base=base)


@settings(deadline=None, max_examples=40)
@given(arbitrary_instances())
def test_reducing_mod_ql_before_rounding_never_changes_the_marked_set(fields):
    """``round((u + k q) p / q) == round(u p / q) + k p``, so the trailing ``mod p`` absorbs ``k``.

    The module docstring calls this the single most valuable property test in the oracle: two
    constructions that must agree for a reason independent of either implementation. Checked at the
    level of ``evaluate`` on every valid secret, which is stronger than equality of marked sets, and
    then on the marked sets themselves against the transcribed relation.
    """
    try:
        reduced = QLWRInstance(**fields, reduce_mod_ql=True)
    except ValueError:
        assume(False)  # a rank-deficient draw is refused, which is its own test above
    unreduced = dataclasses.replace(reduced, reduce_mod_ql=False)

    assert unreduced.target == reduced.target
    for x in range(1 << reduced.n_search):
        if reduced.is_valid(x):
            s = reduced.decode(x)
            assert unreduced.evaluate(s) == reduced.evaluate(s), f"the two readings differ at s={s}"
    assert unreduced.marked_set() == reduced.marked_set() == reference_marked_set(reduced)
    encoded_secret = sum(v << (j * reduced.w) for j, v in enumerate(reduced.secret_s))
    assert encoded_secret in unreduced.marked_set()


@settings(deadline=None, max_examples=12)
@given(st.integers(0, 2**32 - 1), st.sampled_from([(6, 1), (8, 1), (12, 2)]))
def test_the_generator_returns_the_same_instance_with_and_without_the_reduction(seed, shape):
    """Across seeds and sizes: same draw, same parameters, same single marked value.

    The flag does not enter the random stream, and — because the marked set is identical — it cannot
    change which draw is the first admissible one either.
    """
    n_search, nu = shape
    with_reduction = generate_scaled_instance(n_search=n_search, nu=nu, seed=seed, reduce_mod_ql=True)
    without = generate_scaled_instance(n_search=n_search, nu=nu, seed=seed, reduce_mod_ql=False)
    assert with_reduction.reduce_mod_ql is True and without.reduce_mod_ql is False
    assert dataclasses.replace(without, reduce_mod_ql=True) == with_reduction
    assert without.marked_set() == with_reduction.marked_set()
    assert len(without.marked_set()) == 1


# -----------------------------------------------------------------------------------------------
# generate_scaled_instance
# -----------------------------------------------------------------------------------------------


def test_the_default_instance_has_the_parameters_the_notes_record():
    inst = generate_scaled_instance()
    assert (inst.q_l, inst.p, inst.m, inst.nu, inst.w, inst.n_search) == (61, 19, 7, 2, 6, 12)
    assert inst.seed == DEFAULT_SEED
    assert inst.reduce_mod_ql is True
    assert inst.secret_s == GOLDEN_SECRET
    assert inst.marked_set() == frozenset({GOLDEN_MARKED})
    assert inst == generate_scaled_instance(n_search=12, nu=2, seed=DEFAULT_SEED)


def test_equal_seeds_give_equal_instances_and_different_seeds_do_not():
    a = generate_scaled_instance(seed=7)
    b = generate_scaled_instance(seed=7)
    c = generate_scaled_instance(seed=8)
    assert a == b
    assert a.base != c.base and a.secret_s != c.secret_s
    # The parameters are a function of the width, not of the seed; only the draw moves.
    assert (a.q_l, a.p, a.m) == (c.q_l, c.p, c.m)
    assert c.seed == 8


@pytest.mark.parametrize(
    "n_search, nu, expected",
    [(6, 1, (61, 19, 5)), (8, 1, (251, 83, 4)), (12, 2, (61, 19, 7)), (14, 2, (113, 37, 6))],
)
def test_the_parameters_follow_the_stated_rule_at_every_admissible_width(n_search, nu, expected):
    """``q_L`` the largest generic prime in ``w`` bits, ``p`` the largest one a gap below, ``M == 1``."""
    inst = generate_scaled_instance(n_search=n_search, nu=nu, seed=3)
    assert (inst.q_l, inst.p, inst.m) == expected
    assert inst.n_search == n_search
    assert inst.q_l == max(x for x in range(1 << inst.w) if reference_is_generic_prime(x))
    assert len(reference_marked_set(inst)) == 1
    assert inst.m >= inst.nu * (math.log2(inst.q_l) + 1) / (math.log2(inst.p) - 1)


@pytest.mark.parametrize("gap", [1.5, 2.0, 3.0, 5.0])
def test_the_minimum_rounding_gap_is_honoured_and_is_tight(gap):
    """``q_L / p >= gap``, and no larger generic prime would also have satisfied it."""
    inst = generate_scaled_instance(n_search=12, nu=2, seed=5, min_rounding_gap=gap)
    assert inst.q_l == 61
    assert inst.q_l / inst.p >= gap
    admissible = [g for g in GENERIC_PRIMES_BELOW_64 if g * gap <= inst.q_l]
    assert inst.p == max(admissible)
    assert len(inst.marked_set()) == 1


@pytest.mark.parametrize(
    "n_search, nu, message",
    [
        (4, 2, "no generic prime below"),
        (4, 1, "smallest structurally faithful instance is wider"),
        (10, 2, "smallest structurally faithful instance is wider"),
        (4, 3, "leaves 1 bits per component"),
    ],
)
def test_a_width_with_no_admissible_prime_pair_is_refused(n_search, nu, message):
    """``n_search = 4`` is in the default sweep; its refusal is a recorded row, so it must be a ValueError."""
    with pytest.raises(ValueError, match=message):
        generate_scaled_instance(n_search=n_search, nu=nu)


def test_a_gap_no_generic_prime_can_meet_is_refused():
    with pytest.raises(ValueError, match="no generic prime at least 6.0x below q_l=61"):
        generate_scaled_instance(n_search=12, nu=2, min_rounding_gap=6.0)


def test_zero_attempts_is_exhaustion_not_a_silent_none():
    with pytest.raises(RuntimeError, match=r"no instance with M=1 found in 0 draws at n_search=12, nu=2, q_l=61, p=19"):
        generate_scaled_instance(max_attempts=0)


@pytest.fixture
def single_row_parameters(monkeypatch):
    """Hand the generator ``m = 1`` at ``(q_L, p) = (61, 19)``, ``nu = 1``.

    One sample pins the secret only to a rounding bucket: ``x`` is invertible mod 61, so the marked
    set is the preimage of one bucket, which holds 3 or 4 residues and never 1. That makes every draw
    non-unique, deterministically, which no argument the generator accepts can arrange.
    """
    monkeypatch.setattr(qlwr_module, "_choose_parameters", lambda n_search, nu, gap: (61, 6, 19, 3, 1))


def test_exhaustion_raises_with_the_parameters_it_gave_up_at(single_row_parameters):
    with pytest.raises(RuntimeError, match=r"no instance with M=1 found in 5 draws at n_search=6, nu=1, q_l=61, p=19"):
        generate_scaled_instance(n_search=6, nu=1, seed=1, max_attempts=5)


def test_require_unique_false_returns_the_non_unique_instance_a_strict_run_rejects(single_row_parameters):
    """Same seed, same draw: refused when uniqueness is required, returned and measured when it is not."""
    with pytest.raises(RuntimeError):
        generate_scaled_instance(n_search=6, nu=1, seed=1, max_attempts=1)

    inst = generate_scaled_instance(n_search=6, nu=1, seed=1, require_unique=False, max_attempts=1)
    marked = inst.marked_set()
    assert inst.m == 1
    assert len(marked) in (3, 4)
    assert marked == reference_marked_set(inst)
    assert inst.secret_s[0] in marked


def test_require_unique_false_changes_nothing_when_the_first_draw_is_already_unique():
    assert generate_scaled_instance(seed=5, require_unique=False) == generate_scaled_instance(seed=5)


def test_m_is_raised_when_the_inequality_was_not_enough(single_row_parameters):
    """The docstring's promise: too few samples is answered by more samples, not by giving up.

    With ``m`` starting at 1 every draw is non-unique; two or three rows at ``(61, 19)`` are enough
    for a unique secret, so a generator that widened ``m`` on failure would succeed well inside 256
    draws and return an instance with ``m > 1``.
    """
    inst = generate_scaled_instance(n_search=6, nu=1, seed=1, max_attempts=256)
    assert inst.m > 1
    assert len(inst.marked_set()) == 1


# -----------------------------------------------------------------------------------------------
# SearchSpace and the closed form
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "n_items, n_marked, expected",
    [
        (16, 1, 3),
        (64, 1, 6),
        (1024, 1, 25),
        (4096, 1, 50),
        (1 << 24, 1, 3216),
        (16, 4, 1),
        (8, 2, 1),
        (16, 12, 0),
        (16, 16, 0),
    ],
)
def test_the_textbook_optimum_at_the_values_the_project_quotes(n_items, n_marked, expected):
    """50 and 3216 are the two numbers the config schema's docstring argues from."""
    assert theoretical_optimal_iterations(n_items, n_marked) == expected


@pytest.mark.parametrize("n_items, n_marked", [(16, 0), (16, 17), (16, -1), (0, 0)])
def test_the_optimum_refuses_a_marked_count_outside_one_to_n(n_items, n_marked):
    with pytest.raises(ValueError, match="need 1 <= M <= N"):
        theoretical_optimal_iterations(n_items, n_marked)


@settings(deadline=None, max_examples=300)
@given(st.integers(4, 10**7), st.data())
def test_the_optimum_is_the_closed_form_and_is_monotone(n_items, data):
    """Equal to ``floor(pi/4 sqrt(N/M))``, non-increasing in ``M``, non-decreasing in ``N``."""
    n_marked = data.draw(st.integers(1, n_items - 1))
    k = theoretical_optimal_iterations(n_items, n_marked)
    assert isinstance(k, int)
    assert k == math.floor(math.pi / 4 * math.sqrt(n_items / n_marked))
    assert theoretical_optimal_iterations(n_items, n_marked + 1) <= k
    assert theoretical_optimal_iterations(n_items + 1, n_marked) >= k
    assert theoretical_optimal_iterations(4 * n_items, n_marked) in (2 * k, 2 * k + 1)


@settings(deadline=None, max_examples=300)
@given(st.integers(4, 10**7), st.data())
def test_success_at_the_optimum_is_at_least_one_minus_two_m_over_n_squared(n_items, data):
    """For ``M <= N/4``: ``sin^2((2 k_opt + 1) theta) >= (1 - 2M/N)**2``.

    Why it is true. With ``x = sqrt(M/N)`` and ``theta = asin x``, ``k_opt`` lies in
    ``(pi/4x - 1, pi/4x]``, so the rotated angle ``phi = (2 k_opt + 1) theta`` lies in
    ``[pi/2 - theta, pi/2 + theta + (pi/2)(theta/x - 1)]`` (the lower end uses ``theta >= x``). On
    ``x <= 1/2`` the last term is below ``0.3 x**2 <= theta``, so ``|phi - pi/2| <= 2 theta <= pi/3``
    and ``sin^2 phi >= cos^2(2 theta) = (1 - 2M/N)**2``.

    Why it is worth having. The bound is tight enough to notice an optimum that is off by two
    iterations at small ``M/N``, or one computed from ``N/M`` without the square root, and it holds
    for every ``N``, not only powers of two. The tempting stronger claim — that ``k_opt`` beats
    ``k_opt - 1`` — is false; see the next test.
    """
    n_marked = data.draw(st.integers(1, n_items // 4))
    k = theoretical_optimal_iterations(n_items, n_marked)
    theta = math.asin(math.sqrt(n_marked / n_items))
    p_success = math.sin((2 * k + 1) * theta) ** 2
    assert p_success >= (1 - 2 * n_marked / n_items) ** 2 - 1e-12


def test_the_textbook_count_is_not_always_the_count_closest_to_one():
    """``floor(pi/4 sqrt(N/M))`` overshoots the true maximiser when an integer falls between them.

    The docstring once promised "the iteration count at which the success probability is closest to
    1". That was the defect, not the formula, which is the plan's documented textbook one: at
    ``N = 128, M = 19`` it returns 2 (p = 0.8435) while k = 1 gives p = 0.8595, and 82 such
    ``(N, M)`` exist for ``N = 2**n <= 4096``, ``M <= N/4``. Pinned so that neither the formula nor
    the claim drifts back: the count is the closed form, and the true peak is a different function.
    """
    space = SearchSpace(7, frozenset(range(19)))
    k = theoretical_optimal_iterations(128, 19)
    best = max(range(k + 2), key=space.success_probability)

    assert k == math.floor(math.pi / 4 * math.sqrt(128 / 19)) == 2
    assert best == 1
    assert space.success_probability(best) > space.success_probability(k)
    assert space.first_peak_iteration(k + 2) == best


@pytest.mark.parametrize("n_qubits", range(2, 25))
def test_at_a_single_marked_item_the_optimum_is_the_true_peak(n_qubits):
    """The QLWR case, ``M = 1``: here the textbook count *is* the argmax, at every width to 24."""
    n_items = 1 << n_qubits
    theta = math.asin(math.sqrt(1 / n_items))
    k = theoretical_optimal_iterations(n_items, 1)

    def p(j):
        return math.sin((2 * j + 1) * theta) ** 2

    assert p(k) >= p(k - 1)
    assert p(k) >= p(k + 1)


def test_a_search_space_reports_n_m_and_the_rotation_angle():
    space = SearchSpace(4, frozenset({3}))
    assert (space.n_items, space.n_marked) == (16, 1)
    assert space.marked_fraction == 1 / 16
    assert space.theta == pytest.approx(math.asin(0.25), abs=1e-15)
    assert space.optimal_iterations == 3

    quarter = SearchSpace(4, frozenset({0, 5, 10, 15}))
    assert quarter.theta == pytest.approx(math.pi / 6, abs=1e-15)
    # M/N = 1/4 is the one case where a single iteration is exact.
    assert quarter.success_probability(1) == pytest.approx(1.0, abs=1e-15)


@settings(deadline=None, max_examples=200)
@given(st.integers(1, 10), st.data())
def test_success_probability_is_sin_squared_of_the_rotated_angle(n_qubits, data):
    n_items = 1 << n_qubits
    marked = data.draw(st.sets(st.integers(0, n_items - 1), min_size=1, max_size=min(n_items - 1, 40)))
    k = data.draw(st.integers(0, 200))
    space = SearchSpace(n_qubits, frozenset(marked))
    theta = math.asin(math.sqrt(len(marked) / n_items))
    assert space.theta == pytest.approx(theta, abs=1e-15)
    assert space.success_probability(k) == pytest.approx(math.sin((2 * k + 1) * theta) ** 2, abs=1e-12)
    assert space.success_probability(0) == pytest.approx(len(marked) / n_items, abs=1e-12)
    assert 0.0 <= space.success_probability(k) <= 1.0


def test_success_probability_matches_the_exact_recursion_at_n_16():
    """Against the amplitude recursion worked by hand in rationals, not against another ``sin``.

    One Grover iteration maps ``(a, b)`` — the amplitude on each marked and each unmarked state — to
    ``(2 mean - (-a), 2 mean - b)`` after the sign flip. At ``N = 16, M = 1`` that gives success
    probabilities 1/16, 121/256, 3721/4096, 63001/65536.
    """
    space = SearchSpace(4, frozenset({9}))
    a, b = Fraction(1, 4), Fraction(1, 4)
    expected = [a * a]
    for _ in range(3):
        a = -a
        mean = (a + 15 * b) / 16
        a, b = 2 * mean - a, 2 * mean - b
        expected.append(a * a)
    assert expected == [Fraction(1, 16), Fraction(121, 256), Fraction(3721, 4096), Fraction(63001, 65536)]
    for k, want in enumerate(expected):
        assert space.success_probability(k) == pytest.approx(float(want), abs=1e-12)


def test_a_negative_iteration_count_is_refused():
    with pytest.raises(ValueError, match="iterations must be >= 0"):
        SearchSpace(4, frozenset({3})).success_probability(-1)


def test_the_first_peak_is_found_or_reported_missing():
    """None is a fact about the window, not an error: the curve is still rising at k = 2."""
    space = SearchSpace(4, frozenset({3}))
    assert space.first_peak_iteration(10) == 3
    assert space.first_peak_iteration(4) == 3
    assert space.first_peak_iteration(3) is None
    assert space.first_peak_iteration(0) is None
    # Above M/N = 1/2 the curve falls from the start, so the "peak" is the uniform superposition.
    assert SearchSpace(2, frozenset({0, 1, 2})).first_peak_iteration(5) == 0


@settings(deadline=None, max_examples=150)
@given(st.integers(2, 12), st.data())
def test_the_first_peak_is_the_optimum_or_the_iteration_before_it(n_qubits, data):
    """For ``M <= N/4`` the textbook count overshoots the true peak by at most one iteration."""
    n_items = 1 << n_qubits
    n_marked = data.draw(st.integers(1, n_items // 4))
    space = SearchSpace(n_qubits, frozenset(range(n_marked)))
    k_opt = space.optimal_iterations
    peak = space.first_peak_iteration(k_opt + 2)
    assert peak in (k_opt - 1, k_opt)
    assert space.success_probability(peak) >= space.success_probability(k_opt)


@pytest.mark.parametrize(
    "n_qubits, marked, message",
    [
        (0, frozenset({0}), "n_qubits must be >= 1"),
        (-3, frozenset({0}), "n_qubits must be >= 1"),
        (4, frozenset(), "marked set is empty"),
        (2, frozenset({0, 1, 2, 3}), "covers all 4 basis states"),
        (3, frozenset({1, 8}), r"1 marked item\(s\) outside 0..7, e.g. 8"),
        (3, frozenset({-1, 2}), r"1 marked item\(s\) outside 0..7, e.g. -1"),
    ],
)
def test_a_search_space_with_nothing_to_search_for_is_refused(n_qubits, marked, message):
    with pytest.raises(ValueError, match=message):
        SearchSpace(n_qubits, marked)


def test_the_largest_and_smallest_legal_marked_sets_are_accepted():
    assert SearchSpace(1, frozenset({1})).n_marked == 1
    assert SearchSpace(3, frozenset(range(7))).n_marked == 7


# -----------------------------------------------------------------------------------------------
# the QLWR spec's view of the instance
# -----------------------------------------------------------------------------------------------


def test_the_qlwr_truth_table_is_the_instance_predicate_on_every_value(qlwr_instance, qlwr_spec):
    table = qlwr_spec.truth_table()
    assert table.dtype == np.bool_
    assert table.shape == (4096,)
    assert np.flatnonzero(table).tolist() == [GOLDEN_MARKED]
    for x in range(4096):
        assert bool(table[x]) is qlwr_instance.is_solution(x)
    assert qlwr_spec.is_marked(GOLDEN_MARKED) and not qlwr_spec.is_marked(GOLDEN_MARKED + 1)
    assert qlwr_spec.space() == SearchSpace(12, frozenset({GOLDEN_MARKED}))


def test_a_non_unique_instance_lowers_to_the_same_function_both_ways():
    """The arithmetic lowering on an instance with ``M > 1``, invalid encodings and ``p`` close to ``q_L``.

    The worked instance only ever shows the circuit a single marked value; this one has several and
    a different prime pair, so the interval test and the validity test are both exercised on a second
    relation.
    """
    spec = QLWROracleSpec(small_instance())
    assert spec.marked_set() == reference_marked_set(spec.instance)
    assert spec.space().n_marked > 1
    assert_predicate_matches_spec(spec, Lowering.TRUTH_TABLE)
    assert_predicate_matches_spec(spec, Lowering.ARITHMETIC)


def test_an_unknown_lowering_is_refused_by_the_qlwr_spec(qlwr_spec):
    with pytest.raises(ValueError, match="unknown lowering"):
        qlwr_spec.build_predicate("lookup")
    with pytest.raises(ValueError, match="unknown lowering"):
        qlwr_spec.ancilla_width("lookup")


# -----------------------------------------------------------------------------------------------
# RandomControlOracleSpec
# -----------------------------------------------------------------------------------------------


@settings(deadline=None, max_examples=100)
@given(st.integers(1, 10), st.integers(0, 2**32 - 1), st.data())
def test_the_control_marks_exactly_the_requested_number_of_distinct_values(n_qubits, seed, data):
    n_items = 1 << n_qubits
    n_marked = data.draw(st.integers(1, n_items - 1))
    spec = RandomControlOracleSpec(n_qubits, n_marked, seed)
    marked = spec.marked_set()
    assert len(marked) == n_marked
    assert all(isinstance(x, int) and 0 <= x < n_items for x in marked)
    assert spec.space().n_marked == n_marked

    table = spec.truth_table()
    assert table.dtype == np.bool_ and table.shape == (n_items,)
    assert int(table.sum()) == n_marked
    assert frozenset(np.flatnonzero(table).tolist()) == marked

    # Same description, same problem.
    assert RandomControlOracleSpec(n_qubits, n_marked, seed).marked_set() == marked


def test_the_control_is_a_function_of_its_seed():
    a = RandomControlOracleSpec(8, 8, seed=11)
    drawn = {RandomControlOracleSpec(8, 8, seed=s).marked_set() for s in range(20)}
    assert len(drawn) == 20, "twenty seeds should give twenty different 8-subsets of 256"
    assert a.marked_set() == RandomControlOracleSpec(8, 8, seed=11).marked_set()


@pytest.mark.parametrize("n_qubits, n_marked", [(4, 0), (4, -1), (4, 16), (4, 17), (1, 2)])
def test_the_control_refuses_a_marked_count_it_cannot_search(n_qubits, n_marked):
    """``M = N`` is refused as firmly as ``M = 0``: both leave Grover nothing to do."""
    with pytest.raises(ValueError, match=r"must be in \[1, 2\*\*"):
        RandomControlOracleSpec(n_qubits, n_marked, seed=1)


def test_the_control_has_no_arithmetic_form_and_says_so():
    spec = RandomControlOracleSpec(6, 5, seed=3)
    assert spec.supports_arithmetic_lowering is False
    assert spec.ancilla_width(Lowering.TRUTH_TABLE) == spec.ancilla_width(Lowering.ARITHMETIC) == 0
    assert spec.build_predicate(Lowering.ARITHMETIC).num_qubits == 7
    d = spec.describe()
    assert (d["name"], d["search_width"], d["n_items"], d["n_marked"]) == ("random_control", 6, 64, 5)
    assert d["supports_arithmetic_lowering"] is False
    assert d["optimal_iterations"] == theoretical_optimal_iterations(64, 5) == 2


@pytest.mark.parametrize("lowering", list(Lowering))
@pytest.mark.parametrize("n_qubits, n_marked, seed", [(1, 1, 0), (3, 7, 2), (6, 5, 3), (8, 8, 11)])
def test_the_control_predicate_computes_its_marked_set(n_qubits, n_marked, seed, lowering):
    assert_predicate_matches_spec(RandomControlOracleSpec(n_qubits, n_marked, seed), lowering)


# -----------------------------------------------------------------------------------------------
# HiddenPeriodOracleSpec
# -----------------------------------------------------------------------------------------------


@st.composite
def planted_periods(draw):
    n_qubits = draw(st.integers(2, 9))
    period = 2 * draw(st.integers(1, (1 << (n_qubits - 1)) - 1))
    return n_qubits, period, draw(st.integers(0, 2**32 - 1))


@settings(deadline=None, max_examples=150)
@given(planted_periods())
def test_the_planted_period_holds_at_every_register_value(args):
    """``f(x) == f(x XOR s)`` for all ``x`` — the promise the probes are validated against."""
    n_qubits, period, seed = args
    spec = HiddenPeriodOracleSpec(n_qubits, period, seed)
    n_items = 1 << n_qubits
    table = spec.truth_table()
    assert table.dtype == np.bool_ and table.shape == (n_items,)
    for x in range(n_items):
        assert table[x] == table[x ^ period], f"f({x}) != f({x} ^ {period})"

    marked = spec.marked_set()
    assert {x ^ period for x in marked} == set(marked)
    assert len(marked) % 2 == 0
    # The construction draws max(1, N/16) base points and adds each one's partner.
    drawn = max(1, n_items // 16)
    assert drawn <= len(marked) <= 2 * drawn
    assert spec.space().n_marked == len(marked)
    assert HiddenPeriodOracleSpec(n_qubits, period, seed).marked_set() == marked


def test_the_hidden_period_spec_is_a_function_of_its_seed_and_its_period():
    a = HiddenPeriodOracleSpec(8, 0b100, seed=11)
    assert a.marked_set() == HiddenPeriodOracleSpec(8, 0b100, seed=11).marked_set()
    assert a.marked_set() != HiddenPeriodOracleSpec(8, 0b100, seed=12).marked_set()
    assert a.marked_set() != HiddenPeriodOracleSpec(8, 0b1000, seed=11).marked_set()
    assert (a.n_qubits, a.period, a.seed) == (8, 4, 11)
    assert a.supports_arithmetic_lowering is True
    assert a.describe()["name"] == "hidden_period"


@pytest.mark.parametrize(
    "n_qubits, period, message",
    [
        (1, 0, "at least 2 qubits"),
        (0, 2, "at least 2 qubits"),
        (4, 0, "period 0 outside the register"),
        (4, 16, "period 16 outside the register"),
        (4, -2, "period -2 outside the register"),
        (4, 1, "low bit clear"),
        (4, 15, "low bit clear"),
        (8, 0b101, "low bit clear"),
    ],
)
def test_a_period_the_construction_cannot_plant_is_refused(n_qubits, period, message):
    with pytest.raises(ValueError, match=message):
        HiddenPeriodOracleSpec(n_qubits, period, seed=1)


@pytest.mark.parametrize("lowering", list(Lowering))
@pytest.mark.parametrize("n_qubits, period, seed", [(2, 2, 0), (5, 0b10110, 4), (8, 0b100, 11), (8, 0b11111110, 7)])
def test_the_hidden_period_predicate_computes_its_marked_set(n_qubits, period, seed, lowering):
    spec = HiddenPeriodOracleSpec(n_qubits, period, seed)
    assert spec.ancilla_width(lowering) == 0
    assert_predicate_matches_spec(spec, lowering)
