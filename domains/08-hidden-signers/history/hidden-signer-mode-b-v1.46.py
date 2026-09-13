#!/usr/bin/env python3
r"""Hidden-signer CE-QS "Mode B": tested design, attacks, security estimates and
32-KiB sizing, v1.46.

Frontier status. No published scheme gives a hidden 43-of-64 quorum, public
keyless double-signer tracing, category-5 post-quantum security and 32,768
bytes together (v1.45 literature pass). Mode B is built by combining partial
ideas from different sources and testing each decision at toy scale:

  source                              | idea borrowed                              | tested here
  ------------------------------------+--------------------------------------------+-------------------
  v1.24 contract / Fujisaki-Suzuki    | algebraic handle that exposes the signer   | pair-search
  traceable ring signatures           | only when it signs twice in one domain     | extraction
  MQOM2 / KuMQuat ("One Tree")        | a quadratic map needs NO intermediate      | witness count
                                      | witness in a VOLE-in-the-head proof        |
  Ding-Yang cubic hash break,         | quadratic maps are not collision resistant | linear-trick
  own linear-trick test               | ... unless EXPANDING (m - N large)         | attack, counts
  Gold / inverse power S-boxes,       | a low-degree power PERMUTATION of r        | SAT + hybrid:
  MiMC x^3, Rain                      | blocks linear elimination of r             | r^7 = no leak
  FAEST-d7 / QuickSilver              | degree-3..7 constraints on committed input | size formula
  v0.5 distinctness lemma             | distinct handles + binding => distinct     | relation test
                                      | seats, no selector count constraints       |

Design (n = 256, field GF(2^256), key map F: F2^512 -> F2^812)
---------------------------------------------------------------
Per epoch and domain d, seat i draws a one-time opening (s, r), two uniform
256-bit strings, and registers  Y[d][i] = F(s || r)  (812 bits = 102 bytes),
where F is a fixed public quadratic map expanded from a 32-byte seed. cfg commits
to the epoch, the domains and every Y. For message m, the public challenge is
c = SHAKE256("CQ46/c" || cfg || d || m) as a nonzero field element, and the seat's
handle is
    Z = G(r) XOR c * s,     G(r) = r^7   (a permutation of GF(2^256)),
32 bytes. A certificate is
    header (208 B) || 43 handles, strictly increasing (1,376 B) || proof
so the proof slot is 32,768 - 1,584 = 31,184 bytes.

Private relation R_B (what the proof must show): rows (i_j, s_j, r_j) aligned with
the sorted handles with F(s_j || r_j) = Y[d][i_j] and Z_j = r_j^7 XOR c*s_j. Per
seat the committed witness is s, r and a 64-bit one-hot selector: 576 bits, all
constraints of degree <= 3, no intermediate wires. Distinct seats follow from the
strict ordering of handles plus the binding of F (a duplicate seat would need two
openings of one Y).

Public extraction: for two accepted certificates with equal (cfg, d) and m0 != m1,
try all 43 x 43 handle pairs: s = (Z0 XOR Z1)/(c0 XOR c1), r = G^-1(Z0 XOR c0*s),
and look F(s||r) up among the domain's 64 keys. Any hit is a double-authorizer,
publicly re-checkable from (s, r) and the two handles. No link tag, no sidecar,
no opener.

Attacks tested (small n, this file) and estimated (n = 256, --report)
---------------------------------------------------------------------
A0 Generic. Guess r (Grover), derive s = (Z XOR r^7)/c linearly, check F: 2^(n/2)
   = 2^128 iterations, 2^122.3 with the 43 x 64 registry targets. This is the
   ACTUAL framing bound; nothing below beats it. In the v1.43 attack-cost D2
   ledger (HRS16 row, 2752 targets, 2^18 gates per evaluation) it gives
   log2 Pr/G = -149.6 at 2^128 gates, a 19.6-bit margin. It does NOT satisfy the
   rigorous L5 ledger (extraction time charged), which needs n = 512 and then
   38-50 KB certificates (see --report 'rigorous_ledger_variant').
A1 Linear elimination. With a LINEAR handle (Mode A, v1.45) r = Z XOR c*s, so the
   attacker eliminates r and attacks F with n unknowns instead of 2n. Hybrid
   Grover+XL estimate at n = 256: 123 bits quantum, i.e. the algebraic route
   drops BELOW the generic 128. With G = r^7 the algebraic estimate is 251 bits,
   identical to attacking F with no handle at all: the handle adds no algebraic
   leverage, and security is the generic A0 bound. This is why Mode B uses r^7.
A2 Linear-trick collisions. For a quadratic F and fixed delta, F(x+delta)+F(x) is
   LINEAR in x: a collision costs one Gaussian elimination per delta when m = N.
   Toy test: ~40% of deltas collide at m = N; none of 1000 at m = N + 16.
   Expected quantum cost 2^((m-N)/2) = 2^150 for m - N = 300. A corrupt seat can
   therefore not register a key with two openings it knows.
A3 Generic. 2752 registry targets give at most 11.4 bits of multi-target gain;
   BHT collision on 812 bits is 2^271; the challenge c is public.

Cost model for the estimates: XL at the semi-regular degree with omega = 2 and
quantum hybridization (Grover over k guessed variables), i.e. the standard
MQ-estimator recipe; costs are in field-operation units, which the v1.43 gate
accounting only increases. These are EDUCATED ESTIMATES for the best-known attack
families, not proofs; a dedicated cryptanalysis of "expanding random MQ + power
handle" is future work.

What Mode B does NOT have: a zero-knowledge backend, a security theorem, a
collaborative prover (whoever holds (s, r) can frame that seat), or a measured
proof. The size below comes from the FAEST v2 formula, which reproduces the four
published FAEST L5 sizes to the byte, with attack-derived minimum parameters.

CLI: --self-test, --report, --demo-256 (full-size registry, frames, extraction;
uses numpy if present), --explain.
"""

from dataclasses import dataclass
import argparse
import hashlib
import json
import math
import random
import struct
import sys
import time
import unittest

N_SEATS = 64
QUORUM = 43
MIN_OVERLAP = 22
MAX_FRAME_BYTES = 32768
HEADER_BYTES = 208
HEADER_FORMAT = '>4sHH64s64s64sHHI'
MAGIC = b'CQ46'
VERSION = 46
SUITE_B = 0x46B0

N_BITS = 256                                   # field size and secret size
KEYMAP_EXPANSION = 300
M_EQUATIONS = 2 * N_BITS + KEYMAP_EXPANSION    # 812
KEY_BYTES = (M_EQUATIONS + 7) // 8             # 102
HANDLE_BYTES = N_BITS // 8                     # 32
PREFIX_BYTES = HEADER_BYTES + QUORUM * HANDLE_BYTES   # 1,584
PROOF_SLOT_BYTES = MAX_FRAME_BYTES - PREFIX_BYTES     # 31,184
POWER = 7                                      # G(r) = r^7


class ModeBError(Exception):
    pass


# ===========================================================================
# Binary fields GF(2^n). Production n = 256 with x^256 + x^10 + x^5 + x^2 + 1.
# ===========================================================================
KNOWN_POLYS = {256: (1 << 256) | (1 << 10) | (1 << 5) | (1 << 2) | 1}


def _poly_mod(a, m):
    mb = m.bit_length()
    while a.bit_length() >= mb:
        a ^= m << (a.bit_length() - mb)
    return a


def poly_is_irreducible(f, n):
    """Rabin's test."""
    def sq(x):
        return _poly_mod(int('0'.join(bin(x)[2:]), 2), f)

    def gcd(a, b):
        while b:
            a, b = b, _poly_mod(a, b)
        return a
    x, y, powers = 2, 2, {}
    for i in range(1, n + 1):
        y = sq(y)
        powers[i] = y
    if powers[n] != x:
        return False
    primes = [p for p in range(2, n + 1) if n % p == 0 and all(p % q for q in range(2, p))]
    return all(gcd(f, powers[n // p] ^ x) == 1 for p in primes)


def find_poly(n):
    if n in KNOWN_POLYS:
        return KNOWN_POLYS[n]
    for low in range(1, 1 << min(n, 12), 2):
        f = (1 << n) | low
        if poly_is_irreducible(f, n):
            KNOWN_POLYS[n] = f
            return f
    raise ModeBError('no irreducible polynomial found')


class Field:
    def __init__(self, n):
        self.n = n
        self.poly = find_poly(n)
        self.order = (1 << n) - 1
        if math.gcd(POWER, self.order) != 1:
            raise ModeBError('r^7 is not a permutation of this field')
        self.inv_power = pow(POWER, -1, self.order)

    def mul(self, a, b):
        res = 0
        while b:
            if b & 1:
                res ^= a
            b >>= 1
            a <<= 1
            if a >> self.n:
                a ^= self.poly
        return res

    def pow(self, a, k):
        res = 1
        while k:
            if k & 1:
                res = self.mul(res, a)
            a = self.mul(a, a)
            k >>= 1
        return res

    def inv(self, a):
        if not 0 < a <= self.order:
            raise ModeBError('inverse of zero')
        return self.pow(a, self.order - 1)

    def G(self, r):
        return self.pow(r, POWER)

    def G_inv(self, z):
        return self.pow(z, self.inv_power)


# ===========================================================================
# Seeded expanding quadratic map F: F2^N -> F2^m.
# Equation e: y_e = const_e XOR <lin_e, x> XOR sum_{i<j} Q_e[i][j] x_i x_j.
# Q_e is stored as N row integers; row i holds bits j > i.
# ===========================================================================
class QuadMap:
    def __init__(self, n_vars, m_eqs, seed):
        self.N = n_vars
        self.m = m_eqs
        self.seed = seed
        nbytes = (n_vars + 7) // 8
        stream = hashlib.shake_256(b'CQ46/F' + seed).digest(m_eqs * (1 + nbytes * (n_vars + 1)))
        pos = 0
        self.const, self.lin, self.rows = [], [], []
        mask = (1 << n_vars) - 1
        for _ in range(m_eqs):
            self.const.append(stream[pos] & 1)
            pos += 1
            self.lin.append(int.from_bytes(stream[pos:pos + nbytes], 'big') & mask)
            pos += nbytes
            rows = []
            for i in range(n_vars):
                row = int.from_bytes(stream[pos:pos + nbytes], 'big') & mask
                pos += nbytes
                rows.append(row & ~((1 << (i + 1)) - 1))       # keep j > i only
            self.rows.append(rows)

    def evaluate(self, x):
        """Returns the m-bit output as an int (bit e = equation e)."""
        if not 0 <= x < (1 << self.N):
            raise ModeBError('input out of range')
        out = 0
        set_bits = [i for i in range(self.N) if (x >> i) & 1]
        for e in range(self.m):
            acc = self.const[e] ^ (bin(self.lin[e] & x).count('1') & 1)
            rows = self.rows[e]
            for i in set_bits:
                acc ^= bin(rows[i] & x).count('1') & 1
            if acc:
                out |= 1 << e
        return out

    def to_bytes(self, y):
        return y.to_bytes((self.m + 7) // 8, 'big')

    # -- attack A2: linear trick -------------------------------------------
    def diff_rows(self, delta):
        """F(x ^ delta) ^ F(x) = 0 as linear rows (coeff mask over x, rhs)."""
        rows = []
        for e in range(self.m):
            coeff, rhs = 0, self.const[e] ^ self.const[e]          # constants cancel
            rhs ^= bin(self.lin[e] & delta).count('1') & 1
            for i in range(self.N):
                if (delta >> i) & 1:
                    coeff ^= self.rows[e][i]                       # d_i x_j terms
                    rhs ^= bin(self.rows[e][i] & delta).count('1') & 1   # d_i d_j
            for i in range(self.N):
                # d_j x_i terms: bit i gets XOR of Q[i][j] for j with d_j = 1
                if bin(self.rows[e][i] & delta).count('1') & 1:
                    coeff ^= 1 << i
            rows.append((coeff, rhs))
        return rows

    def collision_for_delta(self, delta):
        """Solve the linear system; returns x with F(x)=F(x^delta) or None."""
        pivots = {}
        for coeff, rhs in self.diff_rows(delta):
            for p in sorted(pivots, reverse=True):
                if (coeff >> p) & 1:
                    pc, pr = pivots[p]
                    coeff ^= pc
                    rhs ^= pr
            if coeff == 0:
                if rhs:
                    return None
                continue
            pivots[coeff.bit_length() - 1] = (coeff, rhs)
        x = 0
        for p in sorted(pivots):                                   # back-substitute
            coeff, rhs = pivots[p]
            val = rhs ^ (bin(coeff & x & ~(1 << p)).count('1') & 1)
            if val:
                x |= 1 << p
        return x


# ===========================================================================
# Registry, handles, frames, relation, extraction.
# ===========================================================================
def H(label, *parts):
    h = hashlib.shake_256()
    for p in (label,) + parts:
        h.update(struct.pack('>Q', len(p)))
        h.update(p)
    return h.digest(64)


@dataclass(frozen=True)
class Params:
    n: int
    m: int
    field: Field
    keymap: QuadMap

    @property
    def handle_bytes(self):
        return (self.n + 7) // 8


def make_params(n=N_BITS, expansion=KEYMAP_EXPANSION, seed=b'CQ46/keymap-seed-v1'):
    return Params(n, 2 * n + expansion, Field(n), QuadMap(2 * n, 2 * n + expansion, seed))


@dataclass(frozen=True)
class Registry:
    epoch: bytes
    domains: tuple
    keys: dict                       # domain -> tuple of 64 key bytes


def opening_to_input(p, s, r):
    return s | (r << p.n)


def build_registry(p, epoch, domains, rng):
    keys, secrets = {}, {}
    for d in domains:
        row, openings = [], []
        for _ in range(N_SEATS):
            s, r = rng.getrandbits(p.n), rng.getrandbits(p.n)
            row.append(p.keymap.to_bytes(p.keymap.evaluate(opening_to_input(p, s, r))))
            openings.append((s, r))
        if len(set(row)) != N_SEATS:
            raise ModeBError('registry keys must be distinct')
        keys[d], secrets[d] = tuple(row), tuple(openings)
    return Registry(epoch, tuple(domains), keys), secrets


def cfg_of(registry, p):
    parts = [registry.epoch, p.keymap.seed, struct.pack('>HH', p.n, p.m)]
    for d in registry.domains:
        parts.append(d)
        parts.extend(registry.keys[d])
    return H(b'CQ46/cfg/B', *parts)


def challenge(p, cfg, domain, message):
    c = int.from_bytes(hashlib.shake_256(b'CQ46/c' + cfg + domain + message).digest(
        p.handle_bytes), 'big') & p.field.order
    return c or 1


def handle(p, opening, c):
    s, r = opening
    return (p.field.G(r) ^ p.field.mul(c, s)).to_bytes(p.handle_bytes, 'big')


def encode(p, registry, secrets, domain, message, seats, proof=b'STRUCTURE-ONLY'):
    if len(seats) != QUORUM or len(set(seats)) != QUORUM:
        raise ModeBError('exactly 43 distinct seats')
    cfg = cfg_of(registry, p)
    c = challenge(p, cfg, domain, message)
    handles = sorted(handle(p, secrets[domain][i], c) for i in seats)
    if len(set(handles)) != QUORUM:
        raise ModeBError('handle collision')
    payload = b''.join(handles) + proof
    header = struct.pack(HEADER_FORMAT, MAGIC, VERSION, SUITE_B, cfg, domain, message,
                         QUORUM, p.handle_bytes, len(payload))
    frame = header + payload
    if len(frame) > MAX_FRAME_BYTES:
        raise ModeBError('frame exceeds 32,768 bytes')
    return frame


@dataclass(frozen=True)
class Parsed:
    cfg: bytes
    domain: bytes
    message: bytes
    handles: tuple
    proof: bytes


def parse(p, frame):
    if len(frame) > MAX_FRAME_BYTES or len(frame) < HEADER_BYTES + QUORUM * p.handle_bytes:
        raise ModeBError('frame size out of bounds')
    magic, version, suite, cfg, domain, message, count, width, plen = struct.unpack(
        HEADER_FORMAT, frame[:HEADER_BYTES])
    if (magic, version, suite, count, width) != (MAGIC, VERSION, SUITE_B, QUORUM,
                                                 p.handle_bytes):
        raise ModeBError('noncanonical header')
    if plen != len(frame) - HEADER_BYTES:
        raise ModeBError('payload length mismatch')
    body = frame[HEADER_BYTES:]
    w = p.handle_bytes
    handles = tuple(body[j * w:(j + 1) * w] for j in range(QUORUM))
    if any(handles[j] >= handles[j + 1] for j in range(QUORUM - 1)):
        raise ModeBError('handles must be strictly increasing')
    return Parsed(cfg, domain, message, handles, body[QUORUM * w:])


def check_relation(p, registry, parsed, rows):
    """R_B on rows (seat, s, r) aligned with parsed.handles."""
    if parsed.cfg != cfg_of(registry, p) or parsed.domain not in registry.keys:
        raise ModeBError('wrong configuration or unregistered domain')
    if len(rows) != QUORUM:
        raise ModeBError('43 rows required')
    if len({i for i, _, _ in rows}) != QUORUM:
        raise ModeBError('duplicate seat')
    c = challenge(p, parsed.cfg, parsed.domain, parsed.message)
    for (i, s, r), z in zip(rows, parsed.handles):
        if not 0 <= i < N_SEATS or not 0 <= s <= p.field.order or not 0 <= r <= p.field.order:
            raise ModeBError('row out of range')
        if p.keymap.to_bytes(p.keymap.evaluate(opening_to_input(p, s, r))) != registry.keys[parsed.domain][i]:
            raise ModeBError('opening does not match the registry key')
        if handle(p, (s, r), c) != z:
            raise ModeBError('handle is not r^7 XOR c*s')
    return True


@dataclass(frozen=True)
class Blame:
    seat: int
    position0: int
    position1: int
    s: int
    r: int


def extract(p, registry, frame0, frame1, evaluator=None):
    """Public pair-search extraction. Both frames must already be accepted by a
    qualified verifier; proof checking is not part of this function."""
    p0, p1 = parse(p, frame0), parse(p, frame1)
    if p0.cfg != p1.cfg or p0.cfg != cfg_of(registry, p):
        raise ModeBError('configuration mismatch')
    if p0.domain != p1.domain or p0.domain not in registry.keys:
        raise ModeBError('domain mismatch')
    if p0.message == p1.message:
        raise ModeBError('equal messages are not a conflict')
    c0 = challenge(p, p0.cfg, p0.domain, p0.message)
    c1 = challenge(p, p1.cfg, p1.domain, p1.message)
    inv = p.field.inv(c0 ^ c1)
    table = {key: i for i, key in enumerate(registry.keys[p0.domain])}
    candidates = []
    for j, z0 in enumerate(p0.handles):
        a = int.from_bytes(z0, 'big')
        for k, z1 in enumerate(p1.handles):
            s = p.field.mul(a ^ int.from_bytes(z1, 'big'), inv)
            r = p.field.G_inv(a ^ p.field.mul(c0, s))
            candidates.append((j, k, s, r))
    evaluate = evaluator or (lambda xs: [p.keymap.evaluate(x) for x in xs])
    outputs = evaluate([opening_to_input(p, s, r) for _, _, s, r in candidates])
    found = {}
    for (j, k, s, r), y in zip(candidates, outputs):
        seat = table.get(p.keymap.to_bytes(y))
        if seat is None:
            continue
        if seat in found and (found[seat].s, found[seat].r) != (s, r):
            raise ModeBError('one registry key opened twice: binding violated')
        found.setdefault(seat, Blame(seat, j, k, s, r))
    if len(found) < MIN_OVERLAP:
        raise ModeBError('fewer than 22 double-authorizers identified')
    return tuple(found[i] for i in sorted(found))


def verify_blame(p, registry, frame0, frame1, blame):
    p0, p1 = parse(p, frame0), parse(p, frame1)
    if p0.domain != p1.domain or p0.message == p1.message or p0.cfg != p1.cfg:
        return False
    y = p.keymap.to_bytes(p.keymap.evaluate(opening_to_input(p, blame.s, blame.r)))
    if y != registry.keys[p0.domain][blame.seat]:
        return False
    c0 = challenge(p, p0.cfg, p0.domain, p0.message)
    c1 = challenge(p, p1.cfg, p1.domain, p1.message)
    return (handle(p, (blame.s, blame.r), c0) == p0.handles[blame.position0]
            and handle(p, (blame.s, blame.r), c1) == p1.handles[blame.position1])


# ===========================================================================
# Optional numpy evaluator for the full-size demo (1,849 candidate openings).
# ===========================================================================
def numpy_evaluator(qmap):
    try:
        import numpy as np
    except ImportError:
        return None
    N, m = qmap.N, qmap.m
    words = (N + 63) // 64

    def to_words(v):
        return [(v >> (64 * w)) & ((1 << 64) - 1) for w in range(words)]
    rows = np.array([[to_words(row) for row in qmap.rows[e]] for e in range(m)],
                    dtype=np.uint64)                                 # (m, N, words)
    lin = np.array([to_words(v) for v in qmap.lin], dtype=np.uint64)  # (m, words)
    const = np.array(qmap.const, dtype=np.uint8)
    if not hasattr(np, 'bitwise_count'):
        return None

    def evaluate(xs):
        outs = []
        for x in xs:
            xw = np.array(to_words(x), dtype=np.uint64)
            xbits = np.array([(x >> i) & 1 for i in range(N)], dtype=np.uint8)
            rx = np.bitwise_count(rows & xw).sum(axis=2, dtype=np.uint64) & 1   # (m, N)
            quad = (rx.astype(np.uint8) & xbits).sum(axis=1) & 1
            l = (np.bitwise_count(lin & xw).sum(axis=1, dtype=np.uint64) & 1).astype(np.uint8)
            bits = (const ^ l ^ quad.astype(np.uint8)) & 1
            y = 0
            for e in np.nonzero(bits)[0]:
                y |= 1 << int(e)
            outs.append(y)
        return outs
    return evaluate


# ===========================================================================
# Security estimates: semi-regular degree, XL, quantum hybrid.
# ===========================================================================
def dreg(N, degrees, dmax=None):
    dmax = dmax or N
    coeffs = [math.comb(N, k) for k in range(dmax + 1)]
    for d, count in degrees:
        if count <= 0:
            continue
        inv = [0] * (dmax + 1)
        k = 0
        while d * k <= dmax:
            inv[d * k] = (-1) ** k * math.comb(count + k - 1, k)
            k += 1
        new = [0] * (dmax + 1)
        for i, a in enumerate(coeffs):
            if a:
                for j in range(0, dmax + 1 - i, d):
                    if inv[j]:
                        new[i + j] += a * inv[j]
        coeffs = new
    for D, a in enumerate(coeffs):
        if a <= 0:
            return D
    return None


def hybrid_cost(N, degrees, quantum, omega=2.0, cap=420, step=None):
    step = step or max(1, N // 64)
    best = (float('inf'), None, None)
    for k in range(0, N, step):
        D = dreg(N - k, degrees, dmax=min(N - k, cap))
        if D is None:
            continue
        cost = (k / 2 if quantum else k) + omega * math.log2(math.comb(N - k, D))
        if cost < best[0]:
            best = (round(cost, 1), k, D)
    return best


def attack_shapes(n, expansion=KEYMAP_EXPANSION):
    m = 2 * n + expansion
    return {
        'F alone (no handle)': (2 * n, [(2, m)]),
        'F + linear handle (Mode A): r eliminated': (n, [(2, m)]),
        'F + r^3 handle (degree 2)': (2 * n, [(2, m + n)]),
        'F + r^7 handle (degree 3, Mode B)': (2 * n, [(2, m), (3, n)]),
    }


# Computed by hybrid_cost at n = 256 (this file, --recompute-security); minutes.
SECURITY_ESTIMATES_N256 = {
    'F alone (no handle)': {'classical': 385.8, 'quantum': 251.3},
    'F + linear handle (Mode A): r eliminated': {'classical': 148.8, 'quantum': 123.3},
    'F + r^3 handle (degree 2)': {'classical': 337.8, 'quantum': 244.8},
    'F + r^7 handle (degree 3, Mode B)': {'classical': 378.2, 'quantum': 251.3},
}


def linear_trick_quantum_log2(n, expansion=KEYMAP_EXPANSION):
    """Grover over delta until F(x^delta)^F(x)=0 is consistent: 2^((m-N)/2)."""
    return expansion / 2


def generic_framing_quantum_log2(n=N_BITS, targets=QUORUM * N_SEATS):
    """Grover over r with s derived linearly from the handle: 2^(n/2)/sqrt(targets)."""
    return round(n / 2 - math.log2(targets) / 2, 1)


def d2_attack_cost_row_log2(n=N_BITS, targets=QUORUM * N_SEATS, gates_per_query_log2=18,
                            budget_log2=128):
    """v1.43 HRS16 search row 8*p*(q+1)^2/2^n at G = 2^budget gates: log2(Pr/G)."""
    q = 2 ** (budget_log2 - gates_per_query_log2)
    return round(math.log2(8 * targets * (q + 1) ** 2) - n - budget_log2, 1)


def security_ledger(n=N_BITS, expansion=KEYMAP_EXPANSION, estimates=None):
    est = estimates or SECURITY_ESTIMATES_N256
    multi_target_bits = math.log2(QUORUM * N_SEATS)
    generic = generic_framing_quantum_log2(n)
    return {
        'units': 'log2 field operations (query units); v1.43 gate accounting adds >= 18',
        'framing_generic_grover_quantum': n / 2,
        'framing_generic_multi_target_quantum': generic,
        'framing_algebraic_xl_hybrid_quantum': est['F + r^7 handle (degree 3, Mode B)']['quantum'],
        'framing_algebraic_multi_target_quantum': round(
            est['F + r^7 handle (degree 3, Mode B)']['quantum'] - multi_target_bits, 1),
        'framing_effective_quantum': min(generic, round(
            est['F + r^7 handle (degree 3, Mode B)']['quantum'] - multi_target_bits, 1)),
        'evasion_collision_linear_trick_quantum': linear_trick_quantum_log2(n, expansion),
        'evasion_collision_bht_quantum': round((2 * n + expansion) / 3, 1),
        'mode_a_linear_handle_algebraic_quantum_for_comparison':
            est['F + linear handle (Mode A): r eliminated']['quantum'],
        'd2_attack_cost_framing_row_log2_at_2^128_gates': d2_attack_cost_row_log2(n),
        'd2_attack_cost_margin_bits': round(-130 - d2_attack_cost_row_log2(n), 1),
        'rigorous_L5_ledger': 'NOT met at n = 256: extraction-time accounting needs n = 512',
        'all_estimates_n256': est,
        'minimum_over_rows_quantum': min(generic, linear_trick_quantum_log2(n, expansion)),
    }


# ===========================================================================
# Sizing: FAEST v2 formula (reproduces FAEST L5 sizes exactly), attack-derived
# minimum parameters as in hidden_signer_modeA_v1.45.
# ===========================================================================
def faest_v2_bits(tau, ell_bits, t_open, leaf_commit_blocks, lam=256, b_bits=16,
                  degree=2):
    extra = (degree - 2) * lam * tau                     # higher-degree QuickSilver check
    return (tau * (ell_bits + 3 * lam + b_bits) + t_open * lam
            + leaf_commit_blocks * lam * tau + lam + 128 + 32 + extra)


def grover_reaches_one_third(log2_space, log2_marked, iterations_log2):
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


WITNESS_BITS_PER_SEAT = 2 * N_BITS + N_SEATS                     # s, r, one-hot: 576
CONSTRAINT_DEGREE = 3


def certificate_bytes(log2_parties, grinding_bits=0, chain_log2=0, attack_gates_log2=24,
                      witness_per_seat=WITNESS_BITS_PER_SEAT, degree=CONSTRAINT_DEGREE,
                      leaf_commit_blocks=2):
    iterations = 128 - attack_gates_log2
    s_required = min_secure_bits(0, iterations - chain_log2)
    tau = max(1, -(-(s_required - grinding_bits) // log2_parties))
    t_open = max(0, s_required - grinding_bits)
    bits = faest_v2_bits(tau, QUORUM * witness_per_seat, t_open, leaf_commit_blocks,
                         degree=degree)
    total = PREFIX_BYTES + (bits + 7) // 8
    return {'log2_parties': log2_parties, 'grinding_bits': grinding_bits,
            'chain_log2': chain_log2, 'tau': tau, 'challenge_bits': s_required,
            'proof_bytes': (bits + 7) // 8, 'certificate_bytes': total,
            'fits': total <= MAX_FRAME_BYTES,
            'prover_leaf_expansions_log2': (tau * (1 << log2_parties)).bit_length() - 1}


SETTINGS = (
    dict(log2_parties=16, grinding_bits=0, chain_log2=0),
    dict(log2_parties=20, grinding_bits=8, chain_log2=8),
    dict(log2_parties=24, grinding_bits=16, chain_log2=16),
    dict(log2_parties=32, grinding_bits=16, chain_log2=16),
    dict(log2_parties=32, grinding_bits=32, chain_log2=16),
)


def build_report(recompute_security=False):
    est = None
    if recompute_security:
        est = {}
        for name, (N, degs) in attack_shapes(N_BITS).items():
            c = hybrid_cost(N, degs, False)
            q = hybrid_cost(N, degs, True)
            est[name] = {'classical': c[0], 'quantum': q[0], 'classical_k_D': c[1:],
                         'quantum_k_D': q[1:]}
    return {
        'module': 'hidden_signer_modeB_v1.46',
        'parameters': {'n_bits': N_BITS, 'keymap_equations': M_EQUATIONS,
                       'keymap_expansion': KEYMAP_EXPANSION, 'key_bytes': KEY_BYTES,
                       'handle_bytes': HANDLE_BYTES, 'power': POWER,
                       'prefix_bytes': PREFIX_BYTES, 'proof_slot_bytes': PROOF_SLOT_BYTES,
                       'witness_bits_per_seat': WITNESS_BITS_PER_SEAT,
                       'constraint_degree': CONSTRAINT_DEGREE,
                       'keymap_public_description_MB': round(
                           M_EQUATIONS * (2 * N_BITS) * (2 * N_BITS) / 2 / 8 / 2 ** 20, 1),
                       'registry_bytes_per_seat_domain': KEY_BYTES},
        'faest_v2_reproduction_bytes': {
            'FAEST-256s': faest_v2_bits(22, 3104, 245, 3) // 8,
            'FAEST-256f': faest_v2_bits(32, 3104, 246, 3) // 8,
            'FAEST-EM-256s': faest_v2_bits(22, 2688, 218, 2) // 8,
            'FAEST-EM-256f': faest_v2_bits(32, 2688, 234, 2) // 8},
        'security_ledger': security_ledger(estimates=est),
        'sizes': [certificate_bytes(**s) for s in SETTINGS],
        'sizes_if_2^18_gates_per_hash': [certificate_bytes(attack_gates_log2=18, **s)
                                         for s in SETTINGS],
        'rigorous_ledger_variant': {
            'note': 'n = 512 field, 64-byte handles, witness 1088 bits/seat, as the '
                    'v1.43 L5 accounting would require for the framing row',
            'sizes': [{**certificate_bytes(witness_per_seat=2 * 512 + N_SEATS, **s),
                       'certificate_bytes': certificate_bytes(
                           witness_per_seat=2 * 512 + N_SEATS, **s)['certificate_bytes']
                       + QUORUM * 32,
                       'fits': certificate_bytes(
                           witness_per_seat=2 * 512 + N_SEATS, **s)['certificate_bytes']
                       + QUORUM * 32 <= MAX_FRAME_BYTES}
                      for s in SETTINGS]},
        'flags': {'compact_hidden_signer_certificate_produced': False,
                  'zero_knowledge_backend': False, 'collaborative_prover': False,
                  'security_theorem': False,
                  'security_numbers_are': 'best-known-attack estimates (XL/hybrid model)'},
    }


# ===========================================================================
# Full-size demo.
# ===========================================================================
def demo_256():
    t0 = time.time()
    p = make_params()
    rng = random.Random(46)
    d0 = bytes(range(64))
    registry, secrets = build_registry(p, b'CQ46-demo-epoch', (d0,), rng)
    t1 = time.time()
    m0, m1 = bytes(64), bytes(63) + b'\x11'
    left = list(range(QUORUM))
    right = list(range(MIN_OVERLAP)) + list(range(QUORUM, N_SEATS))
    f0 = encode(p, registry, secrets, d0, m0, left)
    f1 = encode(p, registry, secrets, d0, m1, right)
    t2 = time.time()
    ev = numpy_evaluator(p.keymap)
    blames = extract(p, registry, f0, f1, evaluator=ev)
    t3 = time.time()
    ok = all(verify_blame(p, registry, f0, f1, b) for b in blames)
    out = {'n': p.n, 'm': p.m, 'registry_seats': N_SEATS, 'key_bytes': KEY_BYTES,
           'frame_bytes_without_proof': len(f0) - len(b'STRUCTURE-ONLY'),
           'prefix_bytes': PREFIX_BYTES, 'proof_slot_bytes': PROOF_SLOT_BYTES,
           'extracted_seats': [b.seat for b in blames], 'extracted_count': len(blames),
           'all_blames_verified': ok, 'evaluator': 'numpy' if ev else 'pure-python',
           'seconds': {'keymap_and_registry_64_keys': round(t1 - t0, 1),
                       'two_frames': round(t2 - t1, 1),
                       'extraction_1849_candidates': round(t3 - t2, 1)}}
    print(json.dumps(out, indent=2))
    return 0 if ok and len(blames) == MIN_OVERLAP else 1


# ===========================================================================
# Tests (toy n for speed; production n only for field/permutation facts).
# ===========================================================================
class ModeBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # n must avoid multiples of 3 so that 7 does not divide 2^n - 1 (r^7 permutes).
        cls.p = make_params(n=32, expansion=16, seed=b'test')
        cls.rng = random.Random(4646)
        cls.d0, cls.d1 = bytes(range(64)), bytes(range(1, 65))
        cls.registry, cls.secrets = build_registry(cls.p, b'epoch', (cls.d0, cls.d1), cls.rng)

    def _rows(self, frame, domain, seats, message):
        c = challenge(self.p, cfg_of(self.registry, self.p), domain, message)
        by = {handle(self.p, self.secrets[domain][i], c): i for i in seats}
        return [(by[z],) + self.secrets[domain][by[z]] for z in parse(self.p, frame).handles]

    def test_production_field_and_permutation(self):
        f = Field(256)
        self.assertTrue(poly_is_irreducible(f.poly, 256))
        self.assertEqual(math.gcd(7, f.order), 1)
        rng = random.Random(1)
        for _ in range(3):
            r = rng.getrandbits(256)
            self.assertEqual(f.G_inv(f.G(r)), r)
            a = rng.getrandbits(256) or 1
            self.assertEqual(f.mul(a, f.inv(a)), 1)
        # x^3 would NOT be a permutation of GF(2^256): 3 | 2^256 - 1.
        self.assertEqual(math.gcd(3, f.order), 3)

    def test_toy_field(self):
        f = self.p.field
        for r in (1, 5, 12345, f.order):
            self.assertEqual(f.G_inv(f.G(r)), r)

    def test_faest_formula(self):
        self.assertEqual(faest_v2_bits(22, 3104, 245, 3), 20696 * 8)
        self.assertEqual(faest_v2_bits(32, 3104, 246, 3), 26548 * 8)
        self.assertEqual(faest_v2_bits(22, 2688, 218, 2), 17984 * 8)
        self.assertEqual(faest_v2_bits(32, 2688, 234, 2), 23476 * 8)

    def test_relation_and_extraction_all_overlaps(self):
        rng = random.Random(9)
        for overlap in (MIN_OVERLAP, 30, QUORUM):
            perm = list(range(N_SEATS))
            rng.shuffle(perm)
            left = perm[:QUORUM]
            right = perm[:overlap] + perm[QUORUM:2 * QUORUM - overlap]
            m0, m1 = (10 + overlap).to_bytes(64, 'big'), (99 + overlap).to_bytes(64, 'big')
            f0 = encode(self.p, self.registry, self.secrets, self.d0, m0, left)
            f1 = encode(self.p, self.registry, self.secrets, self.d0, m1, right)
            self.assertTrue(check_relation(self.p, self.registry, parse(self.p, f0),
                                           self._rows(f0, self.d0, left, m0)))
            blames = extract(self.p, self.registry, f0, f1)
            self.assertEqual([b.seat for b in blames], sorted(set(left) & set(right)))
            self.assertTrue(all(verify_blame(self.p, self.registry, f0, f1, b) for b in blames))

    def test_relation_rejects(self):
        seats = list(range(QUORUM))
        m = (1).to_bytes(64, 'big')
        f0 = encode(self.p, self.registry, self.secrets, self.d0, m, seats)
        rows = self._rows(f0, self.d0, seats, m)
        bad = list(rows)
        i, s, r = bad[0]
        bad[0] = (i, s ^ 1, r)
        with self.assertRaises(ModeBError):
            check_relation(self.p, self.registry, parse(self.p, f0), bad)
        dup = list(rows)
        dup[1] = (rows[0][0],) + rows[1][1:]
        with self.assertRaises(ModeBError):
            check_relation(self.p, self.registry, parse(self.p, f0), dup)
        with self.assertRaises(ModeBError):
            check_relation(self.p, self.registry,
                           parse(self.p, encode(self.p, self.registry, self.secrets, self.d0,
                                                (2).to_bytes(64, 'big'), seats)), rows)

    def test_conflict_preconditions_and_framing(self):
        seats = list(range(QUORUM))
        m1, m2 = (1).to_bytes(64, 'big'), (2).to_bytes(64, 'big')
        f0 = encode(self.p, self.registry, self.secrets, self.d0, m1, seats)
        with self.assertRaises(ModeBError):
            extract(self.p, self.registry, f0,
                    encode(self.p, self.registry, self.secrets, self.d0, m1, seats))
        with self.assertRaises(ModeBError):
            extract(self.p, self.registry, f0,
                    encode(self.p, self.registry, self.secrets, self.d1, m2, seats))
        # Frame without seat 0's opening never names seat 0.
        f1 = encode(self.p, self.registry, self.secrets, self.d0, m2,
                    list(range(1, QUORUM)) + [QUORUM])
        self.assertNotIn(0, [b.seat for b in extract(self.p, self.registry, f0, f1)])

    def test_cross_domain_handles_do_not_leak(self):
        # Same seat, two domains: different openings, so Z_d0 XOR Z_d1 is not (c0^c1)*s.
        seat = 5
        cfg = cfg_of(self.registry, self.p)
        m = (3).to_bytes(64, 'big')
        z0 = int.from_bytes(handle(self.p, self.secrets[self.d0][seat],
                                   challenge(self.p, cfg, self.d0, m)), 'big')
        z1 = int.from_bytes(handle(self.p, self.secrets[self.d1][seat],
                                   challenge(self.p, cfg, self.d1, m)), 'big')
        c0, c1 = challenge(self.p, cfg, self.d0, m), challenge(self.p, cfg, self.d1, m)
        s_guess = self.p.field.mul(z0 ^ z1, self.p.field.inv(c0 ^ c1))
        self.assertNotIn(s_guess, (self.secrets[self.d0][seat][0], self.secrets[self.d1][seat][0]))

    def test_attack_A1_linear_handle_eliminates_r(self):
        """Toy brute force: with a linear handle, r = Z ^ c*s, so 2^n candidates
        suffice; with r^7 the attacker must search (s, r) jointly (2^2n)."""
        n = 10
        p = make_params(n=n, expansion=8, seed=b'a1')
        f = p.field
        rng = random.Random(3)
        s, r = rng.getrandbits(n), rng.getrandbits(n)
        y = p.keymap.evaluate(opening_to_input(p, s, r))
        c = rng.getrandbits(n) or 1
        z_lin = r ^ f.mul(c, s)
        z_pow = f.G(r) ^ f.mul(c, s)
        # Linear handle: try every s, derive r, check F.
        hits_lin = [s2 for s2 in range(1 << n)
                    if p.keymap.evaluate(opening_to_input(p, s2, z_lin ^ f.mul(c, s2))) == y]
        self.assertEqual(hits_lin, [s])                    # 2^n work recovers the opening
        # Power handle: deriving r from a guessed s also works (G is invertible)...
        hits_pow = [s2 for s2 in range(1 << n)
                    if p.keymap.evaluate(opening_to_input(p, s2, f.G_inv(z_pow ^ f.mul(c, s2)))) == y]
        self.assertEqual(hits_pow, [s])
        # ... so brute force is 2^n in BOTH cases; the difference is ALGEBRAIC: the
        # linear handle keeps the substituted system quadratic in s (XL-friendly),
        # the power handle makes it degree 7*2 = high (G^-1 has huge degree). The
        # hybrid estimates in SECURITY_ESTIMATES_N256 quantify this.
        self.assertGreater(SECURITY_ESTIMATES_N256['F + r^7 handle (degree 3, Mode B)']['quantum'],
                           SECURITY_ESTIMATES_N256['F + linear handle (Mode A): r eliminated']['quantum'] + 100)

    def test_attack_A2_linear_trick_collisions(self):
        rng = random.Random(11)
        N = 32
        square = QuadMap(N, N, b'sq')
        expanding = QuadMap(N, N + 16, b'ex')
        hits_sq = hits_ex = 0
        for _ in range(60):
            delta = rng.getrandbits(N) or 1
            x = square.collision_for_delta(delta)
            if x is not None:
                self.assertEqual(square.evaluate(x), square.evaluate(x ^ delta))
                hits_sq += 1
            if expanding.collision_for_delta(delta) is not None:
                hits_ex += 1
        self.assertGreater(hits_sq, 10)      # ~40% expected
        self.assertEqual(hits_ex, 0)         # 60 * 2^-16 expected
        self.assertEqual(linear_trick_quantum_log2(N_BITS), 150)
        # Exactness against brute force at N = 10: consistent <=> a collision exists.
        q = QuadMap(10, 10, b'bf')
        table = {}
        for x in range(1 << 10):
            table.setdefault(q.evaluate(x), []).append(x)
        pairs = {x ^ y for xs in table.values() for x in xs for y in xs if x != y}
        for delta in range(1, 1 << 10):
            sol = q.collision_for_delta(delta)
            self.assertEqual(sol is not None, delta in pairs)
            if sol is not None:
                self.assertEqual(q.evaluate(sol), q.evaluate(sol ^ delta))

    def test_attack_A0_generic_bound_and_ledgers(self):
        self.assertEqual(generic_framing_quantum_log2(256), 122.3)
        led = security_ledger()
        self.assertEqual(led['framing_effective_quantum'], 122.3)
        self.assertEqual(led['minimum_over_rows_quantum'], 122.3)
        self.assertEqual(d2_attack_cost_row_log2(256), -149.6)
        self.assertGreater(led['d2_attack_cost_margin_bits'], 19)
        # The algebraic route never beats generic for the r^7 handle, but does
        # for the linear handle (Mode A): 123.3 < 128.
        self.assertGreater(SECURITY_ESTIMATES_N256['F + r^7 handle (degree 3, Mode B)']['quantum'], 128)
        self.assertLess(SECURITY_ESTIMATES_N256['F + linear handle (Mode A): r eliminated']['quantum'], 128)
        # The rigorous-ledger variant (n = 512) does not fit 32 KiB in any setting.
        self.assertTrue(all(not s['fits'] for s in build_report()['rigorous_ledger_variant']['sizes']))

    def test_security_estimator_small_case(self):
        # Quick consistency check of the estimator at n = 32 (seconds).
        shapes = attack_shapes(32, expansion=16)
        q = {name: hybrid_cost(N, d, True, step=4)[0] for name, (N, d) in shapes.items()}
        self.assertLess(q['F + linear handle (Mode A): r eliminated'], q['F alone (no handle)'])
        self.assertAlmostEqual(q['F + r^7 handle (degree 3, Mode B)'], q['F alone (no handle)'], delta=3)
        self.assertEqual(dreg(10, [(2, 10)]), 4)

    def test_sizes(self):
        fits = {s['log2_parties']: s['fits'] for s in (certificate_bytes(**x) for x in SETTINGS)}
        self.assertFalse(fits[16])
        self.assertTrue(fits[24])
        self.assertTrue(fits[32])
        self.assertTrue(certificate_bytes(24, 16, 16)['certificate_bytes'] <= 32768)
        self.assertEqual(WITNESS_BITS_PER_SEAT, 576)
        self.assertEqual(PROOF_SLOT_BYTES, 31184)


def main(argv=None):
    parser = argparse.ArgumentParser(description='CE-QS Mode B hidden-signer design (v1.46).')
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--report', action='store_true')
    g.add_argument('--recompute-security', action='store_true')
    g.add_argument('--demo-256', action='store_true')
    g.add_argument('--explain', action='store_true')
    args = parser.parse_args(argv)
    if args.explain:
        print(__doc__)
        return 0
    if args.report or args.recompute_security:
        print(json.dumps(build_report(recompute_security=args.recompute_security), indent=2))
        return 0
    if args.demo_256:
        return demo_256()
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ModeBTests))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
