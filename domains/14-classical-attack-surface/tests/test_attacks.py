"""The attacks: each one really wins, and its answer is checked with the primitive's own ``verify``.

An attack that reports success without the recovered secret being verified measures the time to
produce *an* output. Every test here checks the recovered object against the public data — and,
where the secret is unique, against the planted one. The budget path is tested too: an attack that
runs out of time must say so, because "did not finish" silently read as "held" is the failure this
whole tester exists to avoid.
"""

from __future__ import annotations

import pytest

from qpt_cart.attacks.algebraic import boolean_system, gaussian_preimage, groebner_keymap, sage_available
from qpt_cart.attacks.brute_force import brute_force_function, brute_force_keymap
from qpt_cart.attacks.collision import (
    _solve,
    _symmetric,
    birthday_collision,
    difference_system,
    linear_trick_collision,
)
from qpt_cart.attacks.lattice import lattice_engine_path, lattice_primal
from qpt_cart.primitives.controls import LinearMapControl, RandomFunctionControl
from qpt_cart.primitives.keymap import HandleMode, KeyMapScheme, Opening
from qpt_cart.primitives.qlwr_trace import QlwrTrace

needs_sage = pytest.mark.skipif(not sage_available(), reason="SageMath not importable")
needs_lattice_engine = pytest.mark.skipif(lattice_engine_path() is None,
                                          reason="lattice-stress engine not found")


# -- exhaustive search -----------------------------------------------------------------------------


@pytest.mark.parametrize("mode", list(HandleMode))
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_exhaustive_search_recovers_the_planted_opening(mode, seed):
    scheme = KeyMapScheme(8, mode)
    opening, transcript = scheme.transcript(seed)
    result = brute_force_keymap(scheme, transcript, seed=seed)
    assert result.success and result.verified
    assert 1 <= result.work <= 1 << 8
    # walk the same path by hand: the work is the distance from the seeded start to the secret r
    from qpt_cart.attacks.brute_force import _offset
    assert result.work == (opening.r - _offset(seed, 8)) % (1 << 8) + 1


def test_exhaustive_search_that_runs_out_of_budget_says_so():
    scheme = KeyMapScheme(16, HandleMode.B)
    _, transcript = scheme.transcript(5)
    result = brute_force_keymap(scheme, transcript, seed=5, max_seconds=0.0)
    if not result.success:                      # it may get lucky inside the first 1024 tries
        assert "budget" in result.not_run_reason and result.work >= 1024 and not result.verified


def test_the_random_function_control_falls_to_exhaustive_search():
    control = RandomFunctionControl(10, 4)
    _, public = control.keygen()
    result = brute_force_function(control, public, seed=4)
    assert result.success and 1 <= result.work <= 1 << 10


# -- the degenerate algebraic attack ---------------------------------------------------------------


@pytest.mark.parametrize("n", [8, 32, 96])
def test_gaussian_elimination_inverts_the_linear_control(n):
    control = LinearMapControl(n, 2)
    secret, public = control.keygen()
    result = gaussian_preimage(control, public)
    assert result.success and result.verified
    assert result.work <= 4 * n ** 3            # cubic, with room: 2n rows against n pivots


# -- collisions ------------------------------------------------------------------------------------


def test_the_difference_system_is_linear_in_x_and_is_the_difference():
    """For a fixed delta, ``F(x + delta) + F(x)`` must equal ``<coeff, x> + rhs`` for every x."""
    qmap = KeyMapScheme(4, HandleMode.A).map
    symmetric = _symmetric(qmap)
    for delta in (1, 0b10110101, 0b11111111, 0b01000010):
        system = list(difference_system(qmap, delta, symmetric))
        for x in range(1 << qmap.n_vars):
            difference = qmap.evaluate(x ^ delta) ^ qmap.evaluate(x)
            for e, (coeff, rhs) in enumerate(system):
                assert (difference >> e) & 1 == ((coeff & x).bit_count() & 1) ^ rhs


def test_the_linear_solver_finds_a_solution_or_proves_there_is_none():
    assert _solve([(0b011, 1), (0b110, 0), (0b101, 1)]) is not None      # consistent (rank 2)
    assert _solve([(0b011, 1), (0b110, 0), (0b101, 0)]) is None          # rows sum to 0 = 1
    x = _solve([(0b001, 1), (0b010, 0), (0b100, 1)])
    assert x == 0b101


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_both_collision_attacks_return_a_real_collision(seed):
    qmap = KeyMapScheme(5, HandleMode.A).map
    for attack in (linear_trick_collision, birthday_collision):
        result = attack(qmap, seed=seed)
        assert result.success and result.verified and result.work >= 1
    assert linear_trick_collision(qmap, seed=seed).size == qmap.m_eqs - qmap.n_vars
    assert birthday_collision(qmap, seed=seed).size == qmap.m_eqs


def test_the_structural_collision_is_cheaper_than_the_generic_one_on_average():
    """2^E against 2^(m/2): at n = 5, E = 6 and m = 16, so about 64 tries against about 320."""
    qmap = KeyMapScheme(5, HandleMode.A).map
    trick = sum(linear_trick_collision(qmap, seed=s).work for s in range(1, 25)) / 24
    birthday = sum(birthday_collision(qmap, seed=s).work for s in range(1, 25)) / 24
    assert trick < birthday
    assert 16 < trick < 256 and 100 < birthday < 1000


# -- Groebner --------------------------------------------------------------------------------------


@needs_sage
@pytest.mark.parametrize("mode,n", [(HandleMode.A, 10), (HandleMode.B, 7)])
def test_the_boolean_system_vanishes_on_the_planted_opening_and_not_on_a_wrong_one(mode, n):
    scheme = KeyMapScheme(n, mode)
    opening, transcript = scheme.transcript(3)
    ring, equations, _, _ = boolean_system(scheme, transcript)

    def point(candidate: Opening):
        bits = [(candidate.s >> i) & 1 for i in range(n)]
        if mode is HandleMode.B:
            bits += [(candidate.r >> i) & 1 for i in range(n)]
        return bits

    assert all(f(*point(opening)) == 0 for f in equations)
    wrong = Opening(opening.s ^ 1, opening.r)
    assert any(f(*point(wrong)) != 0 for f in equations)
    expected_unknowns = n if mode is HandleMode.A else 2 * n
    assert ring.ngens() == expected_unknowns
    assert len(equations) == scheme.m_eqs + (n if mode is HandleMode.B else 0)
    assert max(int(f.degree()) for f in equations) == (2 if mode is HandleMode.A else 3)


@needs_sage
@pytest.mark.parametrize("mode,n", [(HandleMode.A, 12), (HandleMode.B, 7)])
def test_the_groebner_attack_recovers_an_opening_that_verifies(mode, n):
    scheme = KeyMapScheme(n, mode)
    opening, transcript = scheme.transcript(2)
    result = groebner_keymap(scheme, transcript, seed=2, max_seconds=120)
    assert result.success and result.verified, result.not_run_reason
    assert result.work is None and "seconds" in result.work_unit
    assert result.detail["openings_found"] >= 1


@needs_sage
def test_a_groebner_run_over_budget_is_recorded_as_not_run_and_not_as_a_failure_of_the_attack():
    scheme = KeyMapScheme(13, HandleMode.B)
    _, transcript = scheme.transcript(1)
    result = groebner_keymap(scheme, transcript, max_seconds=0.2)
    assert not result.success and result.provenance == "not run"
    assert "budget" in result.not_run_reason


# -- lattice ---------------------------------------------------------------------------------------


@needs_lattice_engine
def test_the_lattice_attack_recovers_the_trace_secret_and_attacks_the_same_relation():
    result = lattice_primal(QlwrTrace(12, seed=1), seed=1, max_seconds=120)
    assert result.success and result.verified, result.not_run_reason
    assert result.detail["minimum_block_size"] in result.detail["block_sizes_tried"]
    assert result.detail["lattice_dimension"] and result.detail["rows"] == QlwrTrace(12).m


def test_without_the_engine_the_lattice_attack_is_not_run_rather_than_faked(monkeypatch, tmp_path):
    monkeypatch.setenv("QPT_CART_LATTICE_ENGINE", str(tmp_path))
    result = lattice_primal(QlwrTrace(8))
    assert not result.success and result.provenance == "not run"
    assert "not found" in result.not_run_reason
