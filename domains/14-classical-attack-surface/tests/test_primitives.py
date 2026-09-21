"""The primitives: that they are the objects the record defines, and that they scale honestly.

An attack curve is only as meaningful as the thing attacked. These tests pin the field (its modulus
is irreducible, and is the record's own at production size), the key map (a wrong opening never
verifies; the handle really is linear in ``s``), the scaling rule (the over-determination ratio is
held, not the absolute expansion), and the QLWR trace (exact integer rounding).
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from qpt_cart.primitives.controls import LinearMapControl, RandomFunctionControl
from qpt_cart.primitives.gf2n import RECORD_MODULI, Field, find_modulus, is_irreducible
from qpt_cart.primitives.keymap import HandleMode, KeyMapScheme, Opening, QuadMap, ScalingRule
from qpt_cart.primitives.qlwr_trace import QlwrScalingRule, QlwrTrace, round_half_up

SIZES = [4, 5, 7, 8, 10, 11, 13, 16]


# -- the field -------------------------------------------------------------------------------------


def test_irreducibility_is_decided_correctly_on_known_polynomials():
    assert is_irreducible(0b111)                 # X^2 + X + 1
    assert is_irreducible(0b1011)                # X^3 + X + 1
    assert is_irreducible(0b100011011)           # the AES polynomial
    assert not is_irreducible(0b101)             # X^2 + 1 = (X + 1)^2
    assert not is_irreducible(0b1111)            # X^3 + X^2 + X + 1 = (X + 1)^3
    assert not is_irreducible(0b100011010)       # even constant term: divisible by X


def test_the_production_modulus_is_the_records_own_and_is_irreducible():
    assert find_modulus(256) == RECORD_MODULI[256] == (1 << 256) | (1 << 10) | (1 << 5) | (1 << 2) | 1
    assert is_irreducible(find_modulus(256))


@pytest.mark.parametrize("n", SIZES + [24, 32])
def test_every_scaled_field_has_an_irreducible_modulus_of_the_right_degree(n):
    modulus = find_modulus(n)
    assert modulus.bit_length() - 1 == n and is_irreducible(modulus)


def test_a_reducible_modulus_is_refused():
    with pytest.raises(ValueError, match="not an irreducible"):
        Field(4, 0b10101)                        # X^4 + X^2 + 1 = (X^2 + X + 1)^2


@settings(deadline=None, max_examples=150)
@given(st.sampled_from(SIZES), st.data())
def test_field_axioms_hold(n, data):
    field = Field(n)
    element = st.integers(0, field.order)
    a, b, c = data.draw(element), data.draw(element), data.draw(element)
    assert field.mul(a, b) == field.mul(b, a)
    assert field.mul(a, field.mul(b, c)) == field.mul(field.mul(a, b), c)
    assert field.mul(a, b ^ c) == field.mul(a, b) ^ field.mul(a, c)
    assert field.mul(a, 1) == a
    if a:
        assert field.mul(a, field.inv(a)) == 1


@settings(deadline=None, max_examples=60)
@given(st.sampled_from(SIZES), st.data())
def test_multiplication_by_a_constant_is_the_linear_map_the_attacks_assume(n, data):
    field = Field(n)
    c, s = data.draw(st.integers(1, field.order)), data.draw(st.integers(0, field.order))
    rows = field.mul_matrix(c)
    assert sum(((row & s).bit_count() & 1) << i for i, row in enumerate(rows)) == field.mul(c, s)


@pytest.mark.parametrize("n", [4, 5, 7, 8, 10])
def test_the_seventh_power_permutes_the_field_exactly_when_three_does_not_divide_n(n):
    field = Field(n)
    image = {field.pow(r, 7) for r in range(1 << n)}
    assert (len(image) == 1 << n) == field.power_is_permutation(7) == (n % 3 != 0)


@pytest.mark.parametrize("n", [6, 9, 12])
def test_mode_b_refuses_a_size_where_the_handle_is_not_a_permutation(n):
    with pytest.raises(ValueError, match="not a permutation"):
        KeyMapScheme(n, HandleMode.B)
    KeyMapScheme(n, HandleMode.A)                # the linear handle has no such constraint


# -- the key map -----------------------------------------------------------------------------------


def test_the_scaling_rule_holds_the_ratio_and_recovers_production():
    rule = ScalingRule()
    assert rule.expansion_at(256) == 300 and rule.equations_at(256) == 812
    assert ScalingRule(production_expansion=512).equations_at(256) == 1024
    for n in SIZES:
        assert abs(rule.expansion_at(n) / n - 300 / 256) <= 0.5 / n + 1e-9
        assert rule.equations_at(n) == 2 * n + rule.expansion_at(n)


def test_the_map_is_the_quadratic_form_it_says_it_is():
    """Evaluate one equation by the definition — const + <lin, x> + sum_{i<j} Q_ij x_i x_j."""
    qmap = QuadMap(9, 14, b"definition")
    for x in (0, 1, 0b101010101, 0b111111111, 0b100110011):
        bits = [(x >> i) & 1 for i in range(9)]
        for e in range(qmap.m_eqs):
            value = qmap.const[e]
            for i in range(9):
                value ^= ((qmap.lin[e] >> i) & 1) & bits[i]
                for j in range(i + 1, 9):
                    value ^= ((qmap.rows[e][i] >> j) & 1) & bits[i] & bits[j]
            assert qmap.equation(e, x) == value
        assert qmap.matches(x, qmap.evaluate(x)) and not qmap.matches(x, qmap.evaluate(x) ^ 1)


@settings(deadline=None, max_examples=80)
@given(st.sampled_from([5, 7, 8, 10]), st.sampled_from(list(HandleMode)), st.integers(1, 10**6),
       st.data())
def test_the_honest_opening_verifies_and_no_perturbed_opening_does(n, mode, seed, data):
    scheme = KeyMapScheme(n, mode)
    opening, transcript = scheme.transcript(seed)
    assert scheme.verify(transcript, opening)
    flip = 1 << data.draw(st.integers(0, n - 1))
    assert not scheme.verify(transcript, Opening(opening.s ^ flip, opening.r))
    assert not scheme.verify(transcript, Opening(opening.s, opening.r ^ flip))


@settings(deadline=None, max_examples=80)
@given(st.sampled_from([5, 7, 8, 10]), st.sampled_from(list(HandleMode)), st.integers(1, 10**6))
def test_each_guess_of_r_determines_s_which_is_why_the_search_is_two_to_the_n(n, mode, seed):
    scheme = KeyMapScheme(n, mode)
    opening, transcript = scheme.transcript(seed)
    assert scheme.s_from_r(transcript, opening.r) == opening.s


def test_keygen_is_deterministic_and_seeds_differ():
    scheme = KeyMapScheme(10, HandleMode.B)
    assert scheme.keygen(7) == scheme.keygen(7)
    assert scheme.keygen(7) != scheme.keygen(8)


def test_a_zero_challenge_is_refused():
    scheme = KeyMapScheme(8, HandleMode.B)
    with pytest.raises(ValueError, match="non-zero"):
        scheme.respond(Opening(1, 2), 0)


# -- the QLWR trace --------------------------------------------------------------------------------


@settings(deadline=None, max_examples=300)
@given(st.integers(0, 10**12), st.integers(1, 10**6))
def test_rounding_is_exact_half_up(numerator, denominator):
    from fractions import Fraction
    import math
    assert round_half_up(numerator, denominator) == math.floor(Fraction(numerator, denominator) + Fraction(1, 2))


def test_the_trace_is_the_relation_in_exact_integers_and_scales_by_the_row_ratio():
    rule = QlwrScalingRule()
    assert (rule.q, rule.p, rule.rows_at(256)) == (1 << 16, 1 << 8, 608)
    trace = QlwrTrace(6, seed=3)
    secret = trace.keygen()
    public = trace.trace(secret)
    assert all(isinstance(v, int) and 0 <= v < trace.p for v in public) and len(public) == trace.m
    for row, b in zip(trace.matrix, public):
        inner = sum(x * s for x, s in zip(row, secret)) % trace.q
        assert b == ((2 * inner * trace.p + trace.q) // (2 * trace.q)) % trace.p
    assert trace.verify(public, secret)
    wrong = (secret[0] ^ 1,) + secret[1:]
    assert not trace.verify(public, wrong)


def test_the_trace_refuses_a_malformed_secret():
    trace = QlwrTrace(4)
    with pytest.raises(ValueError):
        trace.trace((1, 2, 3))
    with pytest.raises(ValueError):
        trace.trace((1, 2, 3, 1 << 16))


# -- the controls ----------------------------------------------------------------------------------


def test_the_linear_control_really_is_linear_and_the_random_one_really_is_not():
    linear, random_function = LinearMapControl(10, 1), RandomFunctionControl(10, 1)
    pairs = [(3, 5), (100, 27), (1023, 512), (77, 78)]
    assert all(linear.evaluate(a ^ b) == linear.evaluate(a) ^ linear.evaluate(b) for a, b in pairs)
    assert not all(random_function.evaluate(a ^ b) ==
                   random_function.evaluate(a) ^ random_function.evaluate(b) ^ random_function.evaluate(0)
                   for a, b in pairs)
    for control in (linear, random_function):
        secret, public = control.keygen()
        assert control.evaluate(secret) == public
