"""The toy Mode B-r: that it is the record's construction, and that its idealisations cannot cheat.

A reduction can only be judged inside a model whose rules are enforced. So beyond the arithmetic —
the linearized handle, its inverse, the seventh root, the first-invertible-counter rule — these
tests pin the two referees: an oracle that refuses to change an answer it has given, and an ideal
prover that certifies nothing it was not shown a witness for.
"""

from __future__ import annotations

import random

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from qpt_rr.scheme import (AlreadyQueried, HandleCoincidence, IdealProver, Opening, Params,
                           RandomOracle, Registry, Scheme)


@pytest.fixture(scope="module")
def scheme():
    return Scheme(Params(n=8))


def test_the_parameters_keep_the_records_shape():
    assert Params(n=8, seats=6, quorum=4).overlap == 2
    assert Params(n=8, seats=64, quorum=43).overlap == 22             # the record's own numbers
    with pytest.raises(ValueError, match="not divisible by 3"):
        Params(n=9)
    with pytest.raises(ValueError, match="overlap"):
        Params(n=8, seats=8, quorum=4)


def test_the_key_map_has_the_mode_b_r_expansion(scheme):
    assert scheme.map.n_vars == 16 and scheme.map.m_eqs == 32          # E = 2n, i.e. 512 at n = 256


@settings(deadline=None, max_examples=100)
@given(st.data())
def test_the_handle_map_is_linear_over_f2(scheme, data):
    element = st.integers(0, 255)
    triple = (data.draw(element), data.draw(element), data.draw(element))
    a, b = data.draw(element), data.draw(element)
    assert scheme.L(triple, a ^ b) == scheme.L(triple, a) ^ scheme.L(triple, b)


def test_solving_the_linearized_map_returns_exactly_the_preimages():
    scheme = Scheme(Params(n=5))
    rng = random.Random(1)
    for _ in range(60):
        triple = tuple(rng.getrandbits(5) for _ in range(3))
        target = rng.getrandbits(5)
        expected = sorted(s for s in range(32) if scheme.L(triple, s) == target)
        if triple == (0, 0, 0):
            assert scheme.solve_linearized(triple, target) == []       # D = 0 is reported as no answer
        else:
            assert sorted(scheme.solve_linearized(triple, target)) == expected
            assert len(expected) <= 4, "a nonzero map of 2-degree <= 2 has at most 4 preimages"


@settings(deadline=None, max_examples=100)
@given(st.integers(0, 255))
def test_the_seventh_root_inverts_the_seventh_power(scheme, x):
    assert scheme.seventh_root(scheme.field.pow(x, 7)) == x


def test_the_challenge_is_the_first_invertible_triple_along_the_counter(scheme):
    oracle, mask = RandomOracle(3), 255
    triple = scheme.challenge(oracle, b"cfg", 1, b"m")
    assert scheme.is_invertible(triple)
    asked = [p for _, p in oracle.log]
    assert [p[-1] for p in asked] == list(range(len(asked))), "counters are tried in order"
    for point in asked[:-1]:
        raw = oracle.query(point, 24)
        assert not scheme.is_invertible((raw & mask, (raw >> 8) & mask, raw >> 16))
    assert scheme.challenge(oracle, b"cfg", 1, b"m") == triple, "and the answer is stable"


def test_the_oracle_never_changes_an_answer_it_has_given():
    oracle = RandomOracle(1)
    oracle.program(("fresh",), 5)
    assert oracle.query(("fresh",), 8) == 5
    seen = oracle.query(("asked",), 8)
    with pytest.raises(AlreadyQueried):
        oracle.program(("asked",), seen ^ 1)
    with pytest.raises(AlreadyQueried):
        oracle.program(("fresh",), 6)
    assert oracle.query(("asked",), 8) == seen
    assert oracle.queries_by("adversary") == [("fresh",), ("asked",), ("asked",)]


def _world(n=11, seed=4):
    params, rng = Params(n=n), random.Random(seed)
    scheme = Scheme(params)
    openings = [scheme.sample_opening(rng) for _ in range(params.seats)]
    registry = Registry([scheme.public_key(o) for o in openings])
    oracle = RandomOracle(seed)
    return scheme, openings, registry, oracle, IdealProver(scheme, registry, oracle)


def test_the_ideal_prover_certifies_only_what_it_is_shown_a_witness_for():
    scheme, openings, registry, _, prover = _world()
    good = [(i, openings[i], 0) for i in range(4)]
    certificate = prover.certify(1, b"m", good)
    assert prover.verify(certificate)
    assert list(certificate.handles) == sorted(certificate.handles)

    with pytest.raises(ValueError, match="does not match"):
        prover.certify(1, b"m", good[:3] + [(3, Opening(openings[3].s ^ 1, openings[3].r), 0)])
    with pytest.raises(ValueError, match="distinct"):
        prover.certify(1, b"m", good[:3] + [good[0]])
    with pytest.raises(ValueError, match="distinct"):
        prover.certify(1, b"m", good[:3])


def test_a_certificate_that_was_not_issued_or_was_altered_is_rejected():
    from dataclasses import replace
    scheme, openings, registry, _, prover = _world()
    certificate = prover.certify(1, b"m", [(i, openings[i], 0) for i in range(4)])
    assert not prover.verify(replace(certificate, message=b"other"))
    assert not prover.verify(replace(certificate, handles=certificate.handles[::-1]))
    assert not prover.verify(replace(certificate, token=b"\\x00" * 32))


def test_two_equal_handles_are_refused_as_the_real_verifier_would():
    scheme, openings, registry, oracle, _ = _world(n=5)
    same = openings[0]
    registry = Registry([scheme.public_key(same)] * 6)
    prover = IdealProver(scheme, registry, oracle)
    with pytest.raises(HandleCoincidence):
        prover.certify(1, b"m", [(i, same, 0) for i in range(4)])


@pytest.mark.parametrize("seed", range(6))
def test_extraction_names_exactly_the_seats_that_signed_both_messages(seed):
    """Forensic completeness and no false accusation, at a width (11 bits) where a chance hit on a
    bystander is rare enough not to blur the test."""
    scheme, openings, registry, oracle, prover = _world(seed=seed)
    try:
        c0 = prover.certify(1, b"block A", [(i, openings[i], 0) for i in (0, 1, 2, 3)])
        c1 = prover.certify(1, b"block B", [(i, openings[i], 0) for i in (0, 1, 4, 5)])
    except HandleCoincidence:
        pytest.skip("two 11-bit handles coincided")
    named = scheme.extract(oracle, registry, c0, c1)
    assert [entry.seat for entry in named] == [0, 1]
    assert all(entry.opening == openings[entry.seat] for entry in named), "the evidence is the opening"


def test_extraction_refuses_two_certificates_that_are_not_a_conflict():
    scheme, openings, registry, oracle, prover = _world()
    c0 = prover.certify(1, b"same", [(i, openings[i], 0) for i in range(4)])
    with pytest.raises(ValueError, match="different messages"):
        scheme.extract(oracle, registry, c0, c0)
