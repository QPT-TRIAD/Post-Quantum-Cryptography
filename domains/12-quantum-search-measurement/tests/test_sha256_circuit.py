"""The reversible SHA-256: that it *is* SHA-256, and only then what it costs.

A gate count is worth nothing until the circuit it counts has been shown to compute the function it
is named after, so the order here is the order of the argument. The adder is checked exhaustively
against Python's ``+``. The constants are recomputed from the primes rather than trusted. Reduced
rounds are checked against an independent reference written in this file, so a defect would be
localised to a round. The full circuit is checked against :mod:`hashlib` on the FIPS vectors, on
every one-block length, and under hypothesis. The work registers are shown clean, and the circuit
followed by its inverse is shown to be the identity on arbitrary states — which is what lets an
oracle un-hash. Only after all that are the counts pinned.

Nothing here builds a statevector: the circuit is 801 qubits. Everything runs on the bit-sliced
simulator, which is itself cross-checked below against the project's ``uint64`` simulator.
"""

from __future__ import annotations

import hashlib
import random
from decimal import Decimal, getcontext

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.circuits.sha256_circuit import (
    IV,
    K,
    PUBLISHED_AMY_2016,
    Sha256Layout,
    build_sha256_compression,
    build_sha256_preimage_predicate,
    pad_single_block,
    ripple_carry_add,
)
from grover_emulator.utils.validation import simulate_states
from grover_emulator.utils.wide_simulation import (
    WideSimulationError,
    pack_columns,
    simulate_bitsliced,
    unpack_register,
)

MASK = 0xFFFFFFFF


# -- the simulator the rest of the file stands on --------------------------------------------------


def test_the_bitsliced_simulator_agrees_with_the_uint64_simulator_on_random_circuits():
    rng = random.Random(7)
    for _ in range(20):
        n = rng.randrange(4, 12)
        gl = GateList(n)
        for _ in range(60):
            qubits = rng.sample(range(n), rng.choice((1, 2, 3, 4)))
            gl.append((GateName.X, GateName.CX, GateName.CCX, GateName.MCX)[len(qubits) - 1], *qubits)
        inputs = list(range(1 << n))
        columns = pack_columns(n, [(list(range(n)), inputs)])
        sliced = unpack_register(simulate_bitsliced(gl, columns, len(inputs)), list(range(n)), len(inputs))
        packed, _ = simulate_states(gl, np.arange(1 << n))
        assert sliced == packed.tolist()


def test_the_bitsliced_simulator_refuses_a_gate_that_is_not_a_permutation():
    gl = GateList(2)
    gl.append(GateName.H, 0)
    with pytest.raises(WideSimulationError, match="not a basis permutation"):
        simulate_bitsliced(gl, [0, 0], 1)


def test_an_x_gate_flips_only_the_inputs_that_exist():
    gl = GateList(1)
    gl.append(GateName.X, 0)
    assert simulate_bitsliced(gl, [0b101], 3) == [0b010]


# -- the adder ------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_the_adder_is_addition_mod_two_to_the_n_on_every_input(n):
    a, b, ancilla = list(range(n)), list(range(n, 2 * n)), 2 * n
    gl = GateList(2 * n + 1)
    ripple_carry_add(gl, a, b, ancilla)
    pairs = [(x, y) for x in range(1 << n) for y in range(1 << n)]
    columns = pack_columns(2 * n + 1, [(a, [p[0] for p in pairs]), (b, [p[1] for p in pairs])])
    out = simulate_bitsliced(gl, columns, len(pairs))
    assert unpack_register(out, b, len(pairs)) == [(x + y) % (1 << n) for x, y in pairs]
    assert unpack_register(out, a, len(pairs)) == [x for x, _ in pairs], "the addend is preserved"
    assert out[ancilla] == 0, "the carry ancilla is returned clean"


@settings(deadline=None, max_examples=200)
@given(st.integers(0, MASK), st.integers(0, MASK))
def test_the_32_bit_adder_matches_python(x, y):
    a, b = list(range(32)), list(range(32, 64))
    gl = GateList(65)
    ripple_carry_add(gl, a, b, 64)
    out = simulate_bitsliced(gl, pack_columns(65, [(a, [x]), (b, [y])]), 1)
    assert unpack_register(out, b, 1) == [(x + y) & MASK]
    assert unpack_register(out, a, 1) == [x] and out[64] == 0


@pytest.mark.parametrize("n", [2, 8, 32])
def test_the_adder_costs_what_its_docstring_says(n):
    gl = GateList(2 * n + 1)
    ripple_carry_add(gl, list(range(n)), list(range(n, 2 * n)), 2 * n)
    assert gl.counts() == {"cx": 4 * (n - 1) + 2, "ccx": 2 * (n - 1), "total": 6 * (n - 1) + 2}


def test_the_adder_refuses_overlapping_or_mismatched_registers():
    with pytest.raises(ValueError, match="disjoint"):
        ripple_carry_add(GateList(8), [0, 1], [1, 2], 3)
    with pytest.raises(ValueError, match="cannot be added"):
        ripple_carry_add(GateList(8), [0, 1], [2, 3, 4], 5)


# -- the constants --------------------------------------------------------------------------------


def _primes(count: int) -> list[int]:
    found: list[int] = []
    candidate = 2
    while len(found) < count:
        if all(candidate % p for p in found):
            found.append(candidate)
        candidate += 1
    return found


def test_the_round_constants_are_the_cube_roots_of_the_first_sixty_four_primes():
    """FIPS 180-4 section 4.2.2, recomputed at 60 digits — a transcription slip in ``K`` would give a
    circuit that is self-consistent, passes every structural test, and is not SHA-256."""
    getcontext().prec = 60
    third = Decimal(1) / Decimal(3)
    for prime, constant in zip(_primes(64), K):
        root = Decimal(prime) ** third
        assert int((root - int(root)) * (1 << 32)) == constant


def test_the_initial_value_is_the_square_roots_of_the_first_eight_primes():
    getcontext().prec = 60
    for prime, value in zip(_primes(8), IV):
        root = Decimal(prime).sqrt()
        assert int((root - int(root)) * (1 << 32)) == value


# -- an independent reference, so a defect has a round number ---------------------------------------


def _rotr(x: int, r: int) -> int:
    return ((x >> r) | (x << (32 - r))) & MASK


def reference_state(block: bytes, rounds: int) -> list[int]:
    """The working variables ``a..h`` after ``rounds`` rounds, *before* the feed-forward."""
    w = [int.from_bytes(block[4 * j: 4 * j + 4], "big") for j in range(16)]
    for t in range(16, 64):
        s0 = _rotr(w[t - 15], 7) ^ _rotr(w[t - 15], 18) ^ (w[t - 15] >> 3)
        s1 = _rotr(w[t - 2], 17) ^ _rotr(w[t - 2], 19) ^ (w[t - 2] >> 10)
        w.append((w[t - 16] + s0 + w[t - 7] + s1) & MASK)
    a, b, c, d, e, f, g, h = IV
    for t in range(rounds):
        t1 = (h + (_rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)) + ((e & f) ^ (~e & g & MASK))
              + K[t] + w[t]) & MASK
        t2 = ((_rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) & MASK
        a, b, c, d, e, f, g, h = (t1 + t2) & MASK, a, b, c, (d + t1) & MASK, e, f, g
    return [a, b, c, d, e, f, g, h]


def run(gl: GateList, layout: Sha256Layout, blocks: list[bytes]) -> list[int]:
    registers = [
        (layout.message[j], [int.from_bytes(block[4 * j: 4 * j + 4], "big") for block in blocks])
        for j in range(16)
    ]
    return simulate_bitsliced(gl, pack_columns(gl.num_qubits, registers), len(blocks))


def digests(out: list[int], layout: Sha256Layout, count: int) -> list[bytes]:
    words = [unpack_register(out, layout.digest[w], count) for w in range(8)]
    return [b"".join(words[w][j].to_bytes(4, "big") for w in range(8)) for j in range(count)]


@pytest.mark.parametrize("rounds", [1, 2, 8, 15, 16, 17, 31, 32, 63, 64])
def test_every_reduced_round_count_matches_the_reference(rounds):
    """15/16/17 straddle the point where the message schedule starts writing over the window."""
    rng = random.Random(rounds)
    blocks = [rng.randbytes(64) for _ in range(16)]
    gl, layout = build_sha256_compression(rounds=rounds)
    out = run(gl, layout, blocks)
    for j, block in enumerate(blocks):
        expected = [(s + v) & MASK for s, v in zip(reference_state(block, rounds), IV)]
        assert [unpack_register(out, layout.digest[w], len(blocks))[j] for w in range(8)] == expected


# -- it is SHA-256 ---------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sha256():
    return build_sha256_compression()


def test_the_fips_vectors(sha256):
    gl, layout = sha256
    messages = [b"abc", b"", b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"[:55]]
    out = run(gl, layout, [pad_single_block(m) for m in messages])
    assert digests(out, layout, len(messages))[0].hex() == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
    assert digests(out, layout, len(messages)) == [hashlib.sha256(m).digest() for m in messages]


def test_every_one_block_length_matches_hashlib(sha256):
    gl, layout = sha256
    rng = random.Random(256)
    messages = [rng.randbytes(length) for length in range(56)]
    out = run(gl, layout, [pad_single_block(m) for m in messages])
    assert digests(out, layout, len(messages)) == [hashlib.sha256(m).digest() for m in messages]


@settings(deadline=None, max_examples=60)
@given(st.binary(max_size=55))
def test_any_one_block_message_matches_hashlib(sha256, message):
    gl, layout = sha256
    out = run(gl, layout, [pad_single_block(message)])
    assert digests(out, layout, 1) == [hashlib.sha256(message).digest()]


def test_a_two_block_message_is_refused_rather_than_mis_hashed():
    with pytest.raises(ValueError, match="two blocks"):
        pad_single_block(b"x" * 56)


def test_the_work_registers_are_returned_clean(sha256):
    gl, layout = sha256
    rng = random.Random(3)
    out = run(gl, layout, [rng.randbytes(64) for _ in range(32)])
    assert all(out[q] == 0 for q in layout.scratch)
    assert out[layout.ancilla] == 0


def test_the_circuit_followed_by_its_inverse_is_the_identity_on_arbitrary_states(sha256):
    """On *every* qubit, from states with dirty scratch too — so the inverse is a true inverse and
    not merely one that happens to work from the states the forward circuit produces."""
    gl, _ = sha256
    sandwich = GateList(gl.num_qubits)
    sandwich.extend(gl)
    sandwich.extend(gl.inverse())
    rng = random.Random(11)
    columns = [rng.getrandbits(48) for _ in range(gl.num_qubits)]
    assert simulate_bitsliced(sandwich, columns, 48) == columns


def test_the_gate_set_is_x_cnot_and_toffoli_only(sha256):
    gl, _ = sha256
    assert set(gl.counts()) == {"x", "cx", "ccx", "total"}


# -- and this is what it costs ---------------------------------------------------------------------


def test_the_toffoli_count_is_the_sum_of_its_parts(sha256):
    """Pinned as arithmetic, not as a magic number: 62 per adder, 64 per Ch or Maj (compute and
    uncompute), seven adders a round, three a schedule step, eight for the feed-forward."""
    gl, layout = sha256
    adder = 2 * (32 - 1)
    per_round = 7 * adder + 64 + 64
    per_schedule_step = 3 * adder
    assert gl.toffoli_count() == 64 * per_round + 48 * per_schedule_step + 8 * adder == 45_392
    assert gl.t_count(toffoli_equivalent=True) == 7 * 45_392 == 317_744
    assert gl.num_qubits == 801 == layout.num_qubits


def test_the_count_sits_between_the_published_optimised_and_unoptimised_figures(sha256):
    """A sanity bracket, not a derivation: a straightforward in-place build should land below Amy et
    al.'s unoptimised circuit (which is wider and uses a costlier adder) and above their T-par
    result. Landing outside would mean this circuit or this reading of their table is wrong."""
    gl, _ = sha256
    t_count = gl.t_count(toffoli_equivalent=True)
    assert PUBLISHED_AMY_2016["sha256_t_count_optimised"] < t_count
    assert t_count < PUBLISHED_AMY_2016["sha256_t_count_unoptimised"]
    assert gl.num_qubits < PUBLISHED_AMY_2016["sha256_qubits"]
    assert PUBLISHED_AMY_2016["sha256_oracle_t_count"] == 2 * 228_992 + 8_108


# -- the preimage predicate: the thing a Grover iteration actually calls ----------------------------

LMOTS_PREFIX = b"I" * 16 + (3).to_bytes(4, "big") + (5).to_bytes(2, "big") + (0).to_bytes(1, "big")


@pytest.fixture(scope="module")
def lmots_predicate():
    secret = bytes(range(1, 33))
    target = hashlib.sha256(LMOTS_PREFIX + secret).digest()
    return secret, target, build_sha256_preimage_predicate(LMOTS_PREFIX, 32, target)


def test_the_lm_ots_chain_step_is_exactly_one_block():
    """``I || q || i || j || x`` with ``n = 32`` is 55 bytes: the largest message one block holds."""
    assert len(LMOTS_PREFIX) + 32 == 55
    assert len(pad_single_block(LMOTS_PREFIX + b"\x00" * 32)) == 64


def test_the_predicate_marks_the_preimage_and_nothing_else_and_restores_every_qubit(lmots_predicate):
    secret, _, (gl, layout, search, flag) = lmots_predicate
    rng = random.Random(5)
    candidates = [secret] + [rng.randbytes(32) for _ in range(31)]
    near_miss = bytearray(secret)
    near_miss[-1] ^= 1
    candidates.append(bytes(near_miss))

    # search qubits are byte 0 first, least significant bit first within a byte
    values = [sum(((c[k // 8] >> (k % 8)) & 1) << k for k in range(256)) for c in candidates]
    columns = pack_columns(gl.num_qubits, [(search, values)])
    out = simulate_bitsliced(gl, columns, len(candidates))

    assert out[flag] == 0b1, "only the first candidate, the true preimage, is marked"
    restored = list(out)
    restored[flag] = 0
    assert restored == columns, "un-hashing returned the input, the scratch and the digest"


def test_a_truncated_image_marks_every_input_that_agrees_on_the_kept_bits():
    """``image_bits = 8``: one random input in 256 agrees, so a few hundred tries find collisions —
    which is what shows the comparison reads the *first* bits of the digest, in digest order."""
    prefix, secret = b"p" * 23, b"\x07"
    target = hashlib.sha256(prefix + secret).digest()
    gl, _, search, flag = build_sha256_preimage_predicate(prefix, 1, target, image_bits=8)
    out = simulate_bitsliced(gl, pack_columns(gl.num_qubits, [(search, list(range(256)))]), 256)
    expected = sum(
        1 << x for x in range(256)
        if hashlib.sha256(prefix + bytes([x])).digest()[0] == target[0]
    )
    assert out[flag] == expected
    assert (expected >> 7) & 1, "the secret itself is among them"


def test_the_predicate_costs_two_hashes_and_one_comparison(sha256, lmots_predicate):
    hash_gl, _ = sha256
    _, _, (gl, _, _, _) = lmots_predicate
    assert gl.counts()["ccx"] == 2 * hash_gl.toffoli_count()
    assert gl.counts()["mcx"] == 1
    # one 256-controlled X is 255 Toffolis under the IR's clean-ancilla assumption
    assert gl.toffoli_equivalent() == 2 * 45_392 + 255
