#!/usr/bin/env python3
r"""Hidden-signer CE-QS "Mode A": design reference and 32-KiB gap calculator, v1.45.

Purpose
-------
Mode S (v1.43/v1.44) proves two credential-keyed hash evaluations per seat: a
registry key map and a domain PRF for the link L and mask R. Mode A removes the
PRF and the link tag. The per-seat relation keeps one key-map evaluation, a
linear handle and a selector. This file implements Mode A's frame, private
relation and public extractor (tested), and sizes Mode A with the FAEST v2
signature-size formula, which reproduces all four published FAEST L5 sizes
exactly (tested).

It does NOT produce a compact hidden-signer certificate. It has no
zero-knowledge proof backend, and no published primitive fits the budget.

Construction
------------
Parameters: N = 64 seats, quorum 43, overlap 22.
Field F = GF(2)[X]/(X^336 + X^7 + X^4 + X + 1); irreducibility is tested.

Registry epoch (fixed, authenticated, not certificate-specific):
- For every domain d of the epoch, seat i draws one-time secrets s (224 bits) and
  r (336 bits) and registers Y[d][i] = K(D_A, s, r).
- D_A = H("CQ45/A/K", epoch, d).
- K(D_A, s, r) = SHAKE256(D_A || s || r)[:64]; the 134-byte input fits one absorb block.
- cfg = H("CQ45/cfg/A", epoch, all domains, all Y).

Approving message m in domain d:
- c(m) = SHAKE256-derived 336-bit field element of (cfg, d, m).
- The seat's handle is Z = r XOR c(m)*s in F, 42 bytes.

Certificate:
  header (208 B, suite 0x45A0) || 43 handles, strictly increasing || proof
  |QC| = 208 + 43*42 + |proof| = 2,014 + |proof|,  so the proof slot is 30,754 B.

Private relation R_A (what the zero-knowledge proof must establish):
  there exist rows (i_j, s_j, r_j), j = 1..43, aligned with the sorted handles, with
  1. distinct i_j in [0, 64);
  2. s_j < 2^224;
  3. K(D_A, s_j, r_j) = Y[d][i_j];
  4. Z_j = r_j XOR c(m)*s_j.

Public extraction:
- Take two verified certificates with equal (cfg, d) and m0 != m1, and set
  delta = c0 XOR c1.
- For every handle pair (Z0_j, Z1_k), 43 x 43 in total, compute
  s' = (Z0_j XOR Z1_k)/delta and r' = Z0_j XOR c0*s'. Keep s' < 2^224, and look
  K(D_A, s', r') up in the domain's 64 registry keys.
- A hit is seat i. The public evidence is (s', r') together with both handles.
- A true double-authorizer always hits, because both of its handles use the same
  registered opening. A false hit requires a K collision or preimage.

Why no PRF and no link tag are needed:
- The opening (s, r) is one-time per domain, so handles in different domains are
  independent.
- The pair search replaces the link tag, and s < 2^224 plus the registry lookup
  filter out mismatched pairs.

What Mode A still needs, stated once
------------------------------------
(A1) A key map K that is one-way (the 43 x 64 targets need at least 224-bit
     openings), binding (collision resistance of at least 313 bits), and hiding
     under the linear leakage Z = r XOR c*s. Its in-proof witness must be at most
     max_keymap_witness_bits for the chosen prover parameters.
(A2) c(m) collision-resistant at 336 bits (a public computation outside the proof).
(A3) A zero-knowledge, online-extractable proof of R_A that fits the slot. The
     calculator assumes a FAEST v2-style VOLE-in-the-head proof.
(A4) A collaborative prover: whoever sees an opening (s, r) can compute a second
     handle and frame that seat, so no single aggregator may learn it.
(A5) A per-epoch registry of 64 x T x 64 bytes for T domains.

Non-claims
----------
- SHAKE256 is the executable reference key map. Its proof cost (38,400 AND gates)
  is far over budget.
- The Rain-based and hypothetical key-map rows are sizing inputs, not constructions.
- No security theorem for Mode A is claimed here.
"""

from dataclasses import dataclass
import argparse
import hashlib
import json
import random
import struct
import sys
import unittest

N = 64
QUORUM = 43
MIN_OVERLAP = 22
MAX_FRAME_BYTES = 32768
HEADER_BYTES = 208
FIELD_BITS = 336
S_BITS = 224
HANDLE_BYTES = FIELD_BITS // 8                           # 42
INDEX_BITS = 6
POLY = (1 << 336) | (1 << 7) | (1 << 4) | (1 << 1) | 1
MAGIC = b'CQ45'
VERSION = 45
SUITE_A = 0x45A0
HEADER_FORMAT = '>4sHH64s64s64sHHI'
PREFIX_BYTES = HEADER_BYTES + QUORUM * HANDLE_BYTES     # 2,014
PROOF_SLOT_BYTES = MAX_FRAME_BYTES - PREFIX_BYTES       # 30,754


class ModeAError(Exception):
    pass


# ===========================================================================
# Field GF(2^336).
# ===========================================================================
def gf_mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a >> FIELD_BITS:
            a ^= POLY
    return result


def _poly_mod(a, m):
    mb = m.bit_length()
    while a.bit_length() >= mb:
        a ^= m << (a.bit_length() - mb)
    return a


def gf_inv(a):
    if not 0 < a < (1 << FIELD_BITS):
        raise ModeAError('inverse of zero or of a non-field element')
    u, v, g1, g2 = a, POLY, 1, 0
    while u != 1:
        j = u.bit_length() - v.bit_length()
        if j < 0:
            u, v, g1, g2, j = v, u, g2, g1, -j
        u ^= v << j
        g1 ^= g2 << j
    return _poly_mod(g1, POLY)


def poly_is_irreducible(f, degree):
    """Rabin's test for degree 336 = 2^4 * 3 * 7."""
    def sq_mod(x):
        y = int('0'.join(bin(x)[2:]), 2)
        return _poly_mod(y, f)

    def gcd(a, b):
        while b:
            a, b = b, _poly_mod(a, b)
        return a
    x = 2
    powers, y = {}, x
    for i in range(1, degree + 1):
        y = sq_mod(y)
        powers[i] = y
    if powers[degree] != x:
        return False
    return all(gcd(f, powers[degree // p] ^ x) == 1 for p in (2, 3, 7))


# ===========================================================================
# Hashing, registry and handles.
# ===========================================================================
def H(label, *parts):
    h = hashlib.shake_256()
    for p in (label,) + parts:
        h.update(struct.pack('>Q', len(p)))
        h.update(p)
    return h.digest(64)


def keymap_context(epoch, domain):
    return H(b'CQ45/A/K', epoch, domain)


def keymap(context, s, r):
    """Reference key map K(D_A, s, r): SHAKE256 over 64 + 28 + 42 = 134 bytes."""
    if not (0 <= s < (1 << S_BITS)) or not (0 <= r < (1 << FIELD_BITS)):
        raise ModeAError('opening out of range')
    data = context + s.to_bytes(28, 'big') + r.to_bytes(HANDLE_BYTES, 'big')
    if len(data) != 134:
        raise ModeAError('key-map input must be one 134-byte absorb block')
    return hashlib.shake_256(data).digest(64)


@dataclass(frozen=True)
class EpochRegistry:
    epoch: bytes
    domains: tuple                       # 64-byte domain identifiers
    keys: dict                           # domain -> tuple of 64 registry keys


def build_registry(epoch, domains, rng):
    """Honest registration: returns the public registry and the private openings."""
    keys, secrets = {}, {}
    for d in domains:
        context = keymap_context(epoch, d)
        row, openings = [], []
        for _ in range(N):
            s, r = rng.getrandbits(S_BITS), rng.getrandbits(FIELD_BITS)
            row.append(keymap(context, s, r))
            openings.append((s, r))
        if len(set(row)) != N:
            raise ModeAError('registry keys must be distinct')
        keys[d], secrets[d] = tuple(row), tuple(openings)
    return EpochRegistry(epoch, tuple(domains), keys), secrets


def cfg_of(registry):
    parts = [registry.epoch]
    for d in registry.domains:
        parts.append(d)
        parts.extend(registry.keys[d])
    return H(b'CQ45/cfg/A', *parts)


def challenge(cfg, domain, message):
    return int.from_bytes(hashlib.shake_256(
        b'CQ45/A/c' + cfg + domain + message).digest(HANDLE_BYTES), 'big')


def handle(opening, c):
    s, r = opening
    return (r ^ gf_mul(c, s)).to_bytes(HANDLE_BYTES, 'big')


# ===========================================================================
# Frame.
# ===========================================================================
@dataclass(frozen=True)
class Parsed:
    cfg: bytes
    domain: bytes
    message: bytes
    handles: tuple
    proof: bytes


def encode(registry, secrets, domain, message, seats, proof=b'STRUCTURE-ONLY'):
    if len(seats) != QUORUM or len(set(seats)) != QUORUM:
        raise ModeAError('exactly 43 distinct seats')
    cfg = cfg_of(registry)
    c = challenge(cfg, domain, message)
    handles = sorted(handle(secrets[domain][i], c) for i in seats)
    if len(proof) > PROOF_SLOT_BYTES:
        raise ModeAError('proof exceeds the slot')
    payload = b''.join(handles) + proof
    header = struct.pack(HEADER_FORMAT, MAGIC, VERSION, SUITE_A, cfg, domain, message,
                         QUORUM, HANDLE_BYTES, len(payload))
    return header + payload


def parse(frame):
    if len(frame) > MAX_FRAME_BYTES or len(frame) < PREFIX_BYTES:
        raise ModeAError('frame size out of bounds')
    magic, version, suite, cfg, domain, message, count, width, plen = struct.unpack(
        HEADER_FORMAT, frame[:HEADER_BYTES])
    if (magic, version, suite, count, width) != (MAGIC, VERSION, SUITE_A, QUORUM,
                                                 HANDLE_BYTES):
        raise ModeAError('noncanonical header')
    if plen != len(frame) - HEADER_BYTES:
        raise ModeAError('payload length mismatch')
    body = frame[HEADER_BYTES:]
    handles = tuple(body[j * HANDLE_BYTES:(j + 1) * HANDLE_BYTES] for j in range(QUORUM))
    if any(handles[j] >= handles[j + 1] for j in range(QUORUM - 1)):
        raise ModeAError('handles must be strictly increasing')
    return Parsed(cfg, domain, message, handles, body[QUORUM * HANDLE_BYTES:])


def check_relation(registry, parsed, rows):
    """The private relation R_A on rows (seat, s, r) aligned with parsed.handles."""
    if parsed.cfg != cfg_of(registry) or parsed.domain not in registry.keys:
        raise ModeAError('wrong configuration or unregistered domain')
    if len(rows) != QUORUM or len({i for i, _, _ in rows}) != QUORUM:
        raise ModeAError('43 rows with distinct seats required')
    context = keymap_context(registry.epoch, parsed.domain)
    c = challenge(parsed.cfg, parsed.domain, parsed.message)
    for (i, s, r), z in zip(rows, parsed.handles):
        if not 0 <= i < N or not 0 <= s < (1 << S_BITS):
            raise ModeAError('seat or s out of range')
        if keymap(context, s, r) != registry.keys[parsed.domain][i]:
            raise ModeAError('opening does not match the registry key')
        if handle((s, r), c) != z:
            raise ModeAError('handle is not r XOR c*s')
    return True


@dataclass(frozen=True)
class Blame:
    seat: int
    position0: int
    position1: int
    s: int
    r: int


def extract(registry, frame0, frame1):
    """Public conflict extraction by pair search. Proof checking is out of scope:
    both frames must already be accepted by a qualified verifier."""
    p0, p1 = parse(frame0), parse(frame1)
    if p0.cfg != p1.cfg or p0.cfg != cfg_of(registry):
        raise ModeAError('configuration mismatch')
    if p0.domain != p1.domain or p0.domain not in registry.keys:
        raise ModeAError('domain mismatch')
    if p0.message == p1.message:
        raise ModeAError('equal messages are not a conflict')
    c0 = challenge(p0.cfg, p0.domain, p0.message)
    c1 = challenge(p1.cfg, p1.domain, p1.message)
    inv = gf_inv(c0 ^ c1)
    table = {key: i for i, key in enumerate(registry.keys[p0.domain])}
    context = keymap_context(registry.epoch, p0.domain)
    found = {}
    for j, z0 in enumerate(p0.handles):
        a = int.from_bytes(z0, 'big')
        for k, z1 in enumerate(p1.handles):
            s = gf_mul(a ^ int.from_bytes(z1, 'big'), inv)
            if s >> S_BITS:
                continue
            r = a ^ gf_mul(c0, s)
            seat = table.get(keymap(context, s, r))
            if seat is None:
                continue
            if seat in found:
                raise ModeAError('one registry key opened twice: binding violated')
            found[seat] = Blame(seat, j, k, s, r)
    if len(found) < MIN_OVERLAP:
        raise ModeAError('fewer than 22 double-authorizers identified')
    return tuple(found[i] for i in sorted(found))


def verify_blame(registry, frame0, frame1, blame):
    p0, p1 = parse(frame0), parse(frame1)
    if p0.domain != p1.domain or p0.message == p1.message:
        return False
    context = keymap_context(registry.epoch, p0.domain)
    if keymap(context, blame.s, blame.r) != registry.keys[p0.domain][blame.seat]:
        return False
    c0 = challenge(p0.cfg, p0.domain, p0.message)
    c1 = challenge(p1.cfg, p1.domain, p1.message)
    return (handle((blame.s, blame.r), c0) == p0.handles[blame.position0]
            and handle((blame.s, blame.r), c1) == p1.handles[blame.position1])


# ===========================================================================
# Sizing: FAEST v2 signature-size formula and the Mode A certificate.
# ===========================================================================
def faest_v2_bits(tau, ell_bits, t_open, leaf_commit_blocks, lam=256, b_bits=16):
    """FAEST v2 spec section 3.1: tau*(ell + 3*lam + B) + T_open*lam
    + blocks*lam*tau + lam + 128 + 32."""
    return (tau * (ell_bits + 3 * lam + b_bits) + t_open * lam
            + leaf_commit_blocks * lam * tau + lam + 128 + 32)


def grover_reaches_one_third(log2_space, log2_marked, iterations_log2):
    """Same sufficient condition as sidecar_free_certificate_v1.44."""
    gap = log2_space - log2_marked
    if gap <= 1:
        return True
    if gap <= 4:
        return iterations_log2 >= 1
    two_k_plus_1 = 2 * ((1 << iterations_log2) - 1) + 1
    return (two_k_plus_1 ** 2 * 2500) << log2_marked >= 961 << log2_space


def min_secure_bits(log2_marked, iterations_log2):
    bits = log2_marked
    while grover_reaches_one_third(bits, log2_marked, iterations_log2):
        bits += 1
    return bits


KEYMAP_WITNESS_BITS = {
    # SHAKE256 one absorb block: 24 rounds x 1600 AND gates.
    'shake256_one_block (executable reference)': 38400,
    # Two Rain3-256 evaluations for a 512-bit output: 2 S-box outputs each (the
    # third follows from the public output), key shared with the opening.
    # Rain is analyzed as a one-way function, not in this mode.
    'rain3_256_two_blocks (published primitive, unanalyzed mode)': 1024,
    # Two AES-256-EM encryption witnesses (FAEST-EM-256: 2,688 = 256 + 2,432).
    'aes256_em_two_blocks (FAEST witness)': 2 * 2432,
    # A key map needing no intermediate witness: no such primitive is known.
    'hypothetical_witness_free': 0,
}


def mode_a_certificate(keymap_bits, log2_parties, grinding_bits=0, chain_log2=0,
                       attack_gates_log2=24, leaf_commit_blocks=2, t_open=None):
    """Estimated certificate bytes for Mode A with a FAEST v2-style proof."""
    iterations = 128 - attack_gates_log2
    s_required = min_secure_bits(0, iterations - chain_log2)
    tau = max(1, -(-(s_required - grinding_bits) // log2_parties))
    credential = min_secure_bits(12, iterations)          # 43 handles x 64 keys
    per_seat = credential + FIELD_BITS + INDEX_BITS + keymap_bits
    if t_open is None:
        t_open = max(0, s_required - grinding_bits)
    bits = faest_v2_bits(tau, QUORUM * per_seat, t_open, leaf_commit_blocks)
    total = PREFIX_BYTES + (bits + 7) // 8
    return {'tau': tau, 'challenge_bits': s_required, 'credential_bits': credential,
            'per_seat_witness_bits': per_seat, 'proof_bytes': (bits + 7) // 8,
            'certificate_bytes': total, 'fits': total <= MAX_FRAME_BYTES,
            'prover_leaf_expansions_log2': round(
                (tau * (1 << log2_parties)).bit_length() - 1, 1)}


def max_keymap_witness_bits(log2_parties, **kwargs):
    lo, hi = -1, 1 << 20
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if mode_a_certificate(mid, log2_parties, **kwargs)['fits']:
            lo = mid
        else:
            hi = mid
    return lo


SETTINGS = (
    {'log2_parties': 16, 'grinding_bits': 0, 'chain_log2': 0},
    {'log2_parties': 24, 'grinding_bits': 16, 'chain_log2': 16},
    {'log2_parties': 32, 'grinding_bits': 16, 'chain_log2': 16},
    {'log2_parties': 32, 'grinding_bits': 32, 'chain_log2': 16},
    {'log2_parties': 40, 'grinding_bits': 32, 'chain_log2': 16},
    {'log2_parties': 44, 'grinding_bits': 32, 'chain_log2': 24},
)


def build_report():
    rows = []
    for setting in SETTINGS:
        row = dict(setting)
        row['max_keymap_witness_bits'] = max_keymap_witness_bits(**setting)
        row['certificates'] = {
            name: mode_a_certificate(bits, **setting)['certificate_bytes']
            for name, bits in KEYMAP_WITNESS_BITS.items()}
        rows.append(row)
    return {
        'module': 'hidden_signer_modeA_v1.45',
        'frame': {'prefix_bytes': PREFIX_BYTES, 'proof_slot_bytes': PROOF_SLOT_BYTES,
                  'handle_bytes': HANDLE_BYTES, 'field_bits': FIELD_BITS,
                  's_bits': S_BITS},
        'faest_v2_reproduction_bytes': {
            'FAEST-256s': faest_v2_bits(22, 3104, 245, 3) // 8,
            'FAEST-256f': faest_v2_bits(32, 3104, 246, 3) // 8,
            'FAEST-EM-256s': faest_v2_bits(22, 2688, 218, 2) // 8,
            'FAEST-EM-256f': faest_v2_bits(32, 2688, 234, 2) // 8},
        'sizing_attack_gates_log2': 24,
        'settings': rows,
        'registry_bytes_per_epoch_of_2^16_domains': N * (1 << 16) * 64,
        'flags': {'compact_hidden_signer_certificate_produced': False,
                  'zero_knowledge_backend': False,
                  'collaborative_prover': False},
    }


# ===========================================================================
# Tests.
# ===========================================================================
_EPOCH = b'CQ45-test-epoch'
_D0 = bytes(range(64))
_D1 = bytes(range(1, 65))


def _msg(k):
    return k.to_bytes(64, 'big')


class ModeATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rng = random.Random(4545)
        cls.registry, cls.secrets = build_registry(_EPOCH, (_D0, _D1), cls.rng)

    def _rows(self, frame, domain, seats, message):
        c = challenge(cfg_of(self.registry), domain, message)
        by_handle = {handle(self.secrets[domain][i], c): i for i in seats}
        parsed = parse(frame)
        return [(by_handle[z],) + self.secrets[domain][by_handle[z]] for z in parsed.handles]

    def test_field_irreducible_and_inverse(self):
        self.assertTrue(poly_is_irreducible(POLY, FIELD_BITS))
        rng = random.Random(1)
        for _ in range(20):
            a = rng.getrandbits(FIELD_BITS) or 1
            self.assertEqual(gf_mul(a, gf_inv(a)), 1)

    def test_faest_formula_reproduces_published_sizes(self):
        self.assertEqual(faest_v2_bits(22, 3104, 245, 3), 20696 * 8)
        self.assertEqual(faest_v2_bits(32, 3104, 246, 3), 26548 * 8)
        self.assertEqual(faest_v2_bits(22, 2688, 218, 2), 17984 * 8)
        self.assertEqual(faest_v2_bits(32, 2688, 234, 2), 23476 * 8)

    def test_relation_and_frame(self):
        seats = list(range(QUORUM))
        frame = encode(self.registry, self.secrets, _D0, _msg(1), seats)
        self.assertEqual(len(frame), PREFIX_BYTES + len(b'STRUCTURE-ONLY'))
        rows = self._rows(frame, _D0, seats, _msg(1))
        self.assertTrue(check_relation(self.registry, parse(frame), rows))
        bad = list(rows)
        i, s, r = bad[0]
        bad[0] = (i, s ^ 1, r)
        with self.assertRaises(ModeAError):
            check_relation(self.registry, parse(frame), bad)
        dup = list(rows)
        dup[1] = (rows[0][0],) + rows[1][1:]
        with self.assertRaises(ModeAError):
            check_relation(self.registry, parse(frame), dup)
        other = parse(encode(self.registry, self.secrets, _D0, _msg(2), seats))
        with self.assertRaises(ModeAError):
            check_relation(self.registry, other, rows)

    def test_extraction_all_overlaps_with_public_evidence(self):
        rng = random.Random(7)
        for overlap in range(MIN_OVERLAP, QUORUM + 1):
            perm = list(range(N))
            rng.shuffle(perm)
            left = perm[:QUORUM]
            right = perm[:overlap] + perm[QUORUM:2 * QUORUM - overlap]
            f0 = encode(self.registry, self.secrets, _D0, _msg(10 + overlap), left)
            f1 = encode(self.registry, self.secrets, _D0, _msg(99 + overlap), right)
            blames = extract(self.registry, f0, f1)
            self.assertEqual([b.seat for b in blames], sorted(set(left) & set(right)))
            self.assertTrue(all(verify_blame(self.registry, f0, f1, b) for b in blames))

    def test_no_conflict_cases_rejected(self):
        seats = list(range(QUORUM))
        f0 = encode(self.registry, self.secrets, _D0, _msg(1), seats)
        with self.assertRaises(ModeAError):
            extract(self.registry, f0, encode(self.registry, self.secrets, _D0, _msg(1), seats))
        with self.assertRaises(ModeAError):
            extract(self.registry, f0, encode(self.registry, self.secrets, _D1, _msg(2), seats))

    def test_framing_without_opening_fails(self):
        # An adversary without seat 0's opening substitutes a random handle in a
        # conflicting frame: the pair search does not identify seat 0.
        seats = list(range(QUORUM))
        f0 = encode(self.registry, self.secrets, _D0, _msg(1), seats)
        f1 = bytearray(encode(self.registry, self.secrets, _D0, _msg(2),
                              list(range(1, QUORUM)) + [QUORUM]))
        c1 = challenge(cfg_of(self.registry), _D0, _msg(2))
        honest0 = handle(self.secrets[_D0][0], c1)
        self.assertNotIn(honest0, parse(bytes(f1)).handles)
        blames = extract(self.registry, f0, bytes(f1))
        self.assertNotIn(0, [b.seat for b in blames])
        self.assertEqual(len(blames), QUORUM - 1)

    def test_noncanonical_frames_rejected(self):
        seats = list(range(QUORUM))
        frame = bytearray(encode(self.registry, self.secrets, _D0, _msg(3), seats))
        a = HEADER_BYTES
        frame[a:a + HANDLE_BYTES], frame[a + HANDLE_BYTES:a + 2 * HANDLE_BYTES] = (
            frame[a + HANDLE_BYTES:a + 2 * HANDLE_BYTES], frame[a:a + HANDLE_BYTES])
        with self.assertRaises(ModeAError):
            parse(bytes(frame))
        with self.assertRaises(ModeAError):
            parse(bytes(encode(self.registry, self.secrets, _D0, _msg(3), seats)) + b'\x00' * 40000)

    def test_sizing_gap(self):
        for setting in SETTINGS:
            fits = {name: mode_a_certificate(bits, **setting)['fits']
                    for name, bits in KEYMAP_WITNESS_BITS.items()}
            self.assertFalse(fits['shake256_one_block (executable reference)'])
            self.assertFalse(fits['aes256_em_two_blocks (FAEST witness)'])
        # With a witness-free key map Mode A fits from 2^24-leaf trees onward.
        self.assertTrue(mode_a_certificate(0, 24, grinding_bits=16, chain_log2=16)['fits'])
        # Rain3 in two blocks fits only with 2^44-leaf trees and a 2^24-step chain.
        rain = KEYMAP_WITNESS_BITS['rain3_256_two_blocks (published primitive, unanalyzed mode)']
        self.assertFalse(mode_a_certificate(rain, 40, grinding_bits=32, chain_log2=16)['fits'])
        self.assertTrue(mode_a_certificate(rain, 44, grinding_bits=32, chain_log2=24)['fits'])
        self.assertEqual(mode_a_certificate(0, 16)['credential_bits'], 224)


def main(argv=None):
    parser = argparse.ArgumentParser(description='CE-QS Mode A reference and 32-KiB gap (v1.45).')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true')
    group.add_argument('--report', action='store_true')
    group.add_argument('--explain', action='store_true')
    args = parser.parse_args(argv)
    if args.explain:
        print(__doc__)
        return 0
    if args.report:
        print(json.dumps(build_report(), indent=2))
        return 0
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ModeATests))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
