"""The instance type, and the rank criterion that had to differ from the sibling project's.

The load-bearing tests here are the ones about the *modulus*: the recorded production parameter set
uses ``q_L = 2^16`` and ``p = 2^8``, and the sibling Grover project's rank helper computes modular
inverses, which do not exist modulo an even number. An instance type that inherited that helper
would either raise at construction or — worse, if the inverses happened to succeed on an odd pivot —
report a full-rank base for one that is not, and the attack would run against a lattice that does
not contain the secret.
"""

from __future__ import annotations

import random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    factorise,
    full_column_rank_mod,
    is_prime,
    round_half_up,
)

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8


def make_instance(nu=4, m=12, q=PRODUCTION_Q, p=PRODUCTION_P, seed=5) -> LatticeQLWRInstance:
    """A small instance at the recorded modulus pair, with a full-rank base."""
    rng = random.Random(seed)
    while True:
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    secret = tuple(rng.randrange(q) for _ in range(nu))
    return LatticeQLWRInstance(nu=nu, q_l=q, p=p, m=m, secret_s=secret, base=base, seed=seed)


# ---------------------------------------------------------------------------------------------
# the modulus the sibling project cannot represent
# ---------------------------------------------------------------------------------------------


def test_the_recorded_modulus_pair_is_accepted():
    """The whole reason this type exists rather than reusing the Grover project's."""
    inst = make_instance()
    assert inst.q_l == PRODUCTION_Q and inst.p == PRODUCTION_P


def test_the_grover_instance_type_rejects_the_same_parameters():
    """Stated as a fact about the sibling, so that if its constraint is ever relaxed the reason
    this type exists is re-examined rather than silently duplicated."""
    import sys
    from pathlib import Path

    # The sibling package, under either of the two names it carries: a numbered domain inside the
    # research repository, or a standalone checkout.
    beside = Path(__file__).resolve().parents[2]
    for name in ("12-quantum-search-measurement", "grover-oracle-emulator"):
        candidate = beside / name / "src"
        if (candidate / "grover_emulator").is_dir():
            sys.path.insert(0, str(candidate))
            break
    try:
        from grover_emulator.problem.qlwr_instance import is_generic_prime
    except ImportError:  # pragma: no cover - the sibling venv is not on this path
        pytest.skip("the sibling project is not importable from this environment")
    assert not is_generic_prime(PRODUCTION_Q), "2**16 is not a generic prime"
    assert not is_generic_prime(PRODUCTION_P), "2**8 is not a generic prime"


def test_the_rank_criterion_handles_a_power_of_two_modulus():
    """Rank over Z/2^k equals rank of the reduction mod 2 over F_2."""
    base = [[1, 0], [0, 1], [3, 5]]
    assert full_column_rank_mod(base, 1 << 16, 2) == 2


def test_the_rank_criterion_detects_a_deficient_base_mod_2_to_the_k():
    """A base whose columns are independent over the rationals can still be dependent mod 2^k.

    [[2, 0], [0, 1]] has rational rank 2 but is rank 1 mod 4 — the first column is 2, which is
    not invertible. A criterion built on modular inverses cannot see this.
    """
    assert full_column_rank_mod([[2, 0], [0, 1]], 4, 2) == 1
    assert full_column_rank_mod([[2, 0], [0, 1]], 8, 2) == 1


def test_the_rank_criterion_agrees_with_the_prime_case_when_q_is_prime():
    base = [[3, 1], [4, 2], [1, 1]]
    # over F_7: rows (3,1),(4,2),(1,1); (4,2) = 2*(2,1)... the rank is 2
    assert full_column_rank_mod(base, 7, 2) == 2


@given(
    q=st.sampled_from([4, 8, 16, 32, 9, 27, 12, 65536]),
    seed=st.integers(0, 10_000),
)
@settings(max_examples=40, deadline=None)
def test_the_rank_criterion_is_never_above_the_column_count(q, seed):
    """A rank above the number of columns would mean the elimination is wrong, and a base would be
    rejected as deficient when it is not."""
    rng = random.Random(seed)
    nu, m = 3, 6
    base = [[rng.randrange(q) for _ in range(nu)] for _ in range(m)]
    r = full_column_rank_mod(base, q, nu)
    assert 0 <= r <= nu


def test_a_rank_deficient_base_is_refused_with_a_reason():
    """A rank-deficient base makes s -> Xs non-injective, which is a different and much easier
    problem — so it must be a construction failure rather than a quietly easier attack."""
    with pytest.raises(ValueError, match="rank-deficient|column rank"):
        LatticeQLWRInstance(
            nu=2, q_l=PRODUCTION_Q, p=PRODUCTION_P, m=2,
            secret_s=(1, 2), base=((2, 0), (4, 0)),  # both rows are multiples of 2
        )


# ---------------------------------------------------------------------------------------------
# the relation
# ---------------------------------------------------------------------------------------------


def test_the_noise_interval_is_exactly_the_derived_one():
    """`[-q/(2p), q/(2p) - 1]`, derived rather than fitted — there is no sigma to choose."""
    inst = make_instance()
    assert inst.noise_bound == PRODUCTION_Q // (2 * PRODUCTION_P) == 128
    e = inst.error_vector()
    assert all(-128 <= v <= 127 for v in e), e


def test_the_relation_holds_for_every_row():
    """``A s - b - e == 0 (mod q_l)`` — the identity the whole construction rests on."""
    make_instance().check_relation()


def test_the_error_vector_is_not_all_zero():
    """A vacuous instance where the rounding happened to be lossless would make the planted vector
    trivially short and the attack meaningless."""
    e = make_instance(seed=11).error_vector()
    assert any(v != 0 for v in e)


def test_the_equivalent_sigma_matches_its_closed_form():
    """`sqrt((4B^2 - 1)/12)` for a uniform distribution on an interval of 2B integers."""
    inst = make_instance()
    b = inst.noise_bound
    assert inst.equivalent_gaussian_sigma == pytest.approx(((4 * b * b - 1) / 12) ** 0.5)


def test_the_recorded_parameters_are_bit_shift_rounding():
    """`q_L = 2^16, p = 2^8` makes the relation a shift and a mask. Reported, not hidden."""
    assert make_instance().is_bit_shift_rounding


def test_a_generic_prime_pair_is_not_bit_shift_rounding():
    inst = make_instance(q=61, p=19)
    assert not inst.is_bit_shift_rounding


def test_public_samples_are_the_lifted_rounded_values():
    inst = make_instance()
    assert inst.public_samples() == tuple(
        inst.rounding_ratio * v for v in inst.target
    )


def test_the_two_lattice_dimensions_are_distinct_and_reported():
    """The q-ary lattice is m wide; the primal embedding adds a row and a column. Quoting "the
    dimension" without saying which lattice is quoting a number a reader cannot check."""
    d = make_instance(m=12).describe()
    assert d["qary_lattice_dimension"] == 12
    assert d["usvp_lattice_dimension"] == 13


# ---------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------


def test_round_half_up_is_exact_and_rounds_halves_away_from_zero():
    assert round_half_up(5, 2) == 3
    assert round_half_up(7, 2) == 4
    assert round_half_up(0, 3) == 0


def test_round_half_up_refuses_a_non_positive_denominator():
    with pytest.raises(ValueError):
        round_half_up(1, 0)


def test_factorise_round_trips():
    for n in (2, 4, 12, 65536, 3 * 5 * 7, 1021 * 1019):
        f = factorise(n)
        prod = 1
        for prime, exp in f.items():
            assert is_prime(prime)
            prod *= prime**exp
        assert prod == n, (n, f)


def test_primality_on_known_values():
    assert is_prime(2) and is_prime(65537) and is_prime(1000003)
    assert not is_prime(1) and not is_prime(65536) and not is_prime(1000001)
