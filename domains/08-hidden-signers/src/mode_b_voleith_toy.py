#!/usr/bin/env python3
r"""Mode B end to end with a REAL (toy-security) VOLE-in-the-head proof, v1.48.

What this tests. Every Mode B size so far came from the FAEST v2 formula. This
file implements the proof system structurally as FAEST does -- GGM seed trees,
all-but-one vector commitments, VOLE from vector commitments with correction
values, a VOLE consistency hash, a QuickSilver degree-3 check with zero-knowledge
masks, and a multi-round Fiat-Shamir transform -- for the exact Mode B relation
R_B, at toy parameters so that it runs in Python:

  field GF(2^16) for s, r and the handle (r^7 is a permutation: gcd(7, 2^16-1)=1),
  key map F: F2^32 -> F2^48, 64 seats, quorum 43,
  tau = 8 repetitions of 2^8 parties, MAC field GF(2^64) (= tau * 8 bits).

Toy security: soundness about 2^-64 and 128-bit-free everything; the point is
structural fidelity and a MEASURED proof size to compare with the formula, not
security. Then the full certificate pipeline runs: registry, two conflicting
frames with real proofs in the proof slot, verification, and public pair-search
extraction of the 22 double-signers.

Proof system (prover P, verifier V, statement X = frame header + handles + cfg):
 1. P builds tau GGM trees; leaf i of tree j commits com_ji = H(leaf); sends
    h_com = H(all com). Leaf values r_ji = PRG(leaf) of ell_hat bits give the VOLE
    u_j = XOR_i r_ji,  v_j[t] = XOR_{i: bit t of i = 1} r_ji  (t < 8).
    V holding all leaves but Delta_j gets q_j[t] = v_j[t] XOR bit_t(Delta_j) u_j.
    P sends corrections c_j = u_1 XOR u_j (j >= 2) and d = w XOR u_1 (witness bits
    plus mask bits). Per position p, V_p = concat_j,t v_j[t][p] in GF(2^64),
    Delta = concat bits, and Q_p = V_p + Delta * w_p.
 2. Challenge chi1. P sends u~ = sum_p chi1^p u_p (+ basis-coded mask bits) and
    h_V = sum_p chi1^p V_p. V checks sum_p chi1^p Q_p = h_V + Delta u~.
 3. Challenge chi2. For each constraint f_c (multilinear, degree <= 3, f_c(w) = 0),
    the homogenised f^_c(Q) = sum_S Delta^(3-|S|) prod_{p in S} Q_p is a polynomial
    in Delta whose degree-3 coefficient is f_c(w). P sends the three lower
    coefficients of sum_c chi2^c f^_c, each masked by an independent uniform VOLE
    value; V checks the identity at Delta.
 4. Challenge Delta_1..Delta_tau. P opens all-but-one leaves of every tree
    (8 sibling nodes + the unopened leaf commitment per tree).

Constraints of R_B per seat (witness s, r, one-hot b; 2*16 + 64 = 96 bits):
  48 key-map equations F_e(s||r) + sum_i b_i Y[i]_e = 0          (degree 2)
  16 handle bits     Z_k + (c s)_k + (r^7)_k = 0, r^7 = r r^2 r^4    (degree 3,
                     made multilinear: x^2 = x for bits)
   1 selector        sum_i b_i + 1 = 0                             (degree 1)

Measured proof bytes are printed next to the FAEST v2 formula at the same
(tau, ell, T_open, lambda) so the accounting used in v1.46/v1.47 is checked
against a running implementation. Reuses the Mode B frame, registry, handle and
extractor code of the v1.46 base module
(../history/hidden-signer-mode-b-v1.46.py in this repository) unchanged.

Non-claims: toy parameters, no QROM proof, a research prototype. Not constant
time. The 2^32-leaf production trees of the v1.47 ledger are 2^24 times larger
than these.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import random
import struct
import sys
import time
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The v1.46 base module keeps its version in its filename and sits in history/.
_spec = importlib.util.spec_from_file_location(
    'modeB', os.path.join(_HERE, os.pardir, 'history', 'hidden-signer-mode-b-v1.46.py'))
modeB = importlib.util.module_from_spec(_spec)
sys.modules['modeB'] = modeB
_spec.loader.exec_module(modeB)

N_SEATS, QUORUM, MIN_OVERLAP = modeB.N_SEATS, modeB.QUORUM, modeB.MIN_OVERLAP

# ---------------------------------------------------------------- params ----
TOY_N = 16                      # bits of s, r; field GF(2^16)
TOY_EXPANSION = 16              # key map F2^32 -> F2^48
TAU = 8                         # repetitions
B_BITS = 8                      # parties per repetition = 2^8
LAMBDA = TAU * B_BITS           # MAC field GF(2^64)
POLY64 = (1 << 64) | (1 << 4) | (1 << 3) | (1 << 1) | 1
DEGREE = 3
W_SEAT = 2 * TOY_N + N_SEATS    # 96 witness bits per seat
ELL = QUORUM * W_SEAT           # 4128 witness bits
MASK_BITS = LAMBDA + (DEGREE - 1) * LAMBDA      # VOLE-hash mask + QuickSilver masks
ELL_HAT = ELL + MASK_BITS       # 4320 committed bits


class ProofError(Exception):
    pass


# ------------------------------------------------------------- GF(2^64) ----
def gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        b >>= 1
        a <<= 1
        if a >> LAMBDA:
            a ^= POLY64
    return r


def gpow(a, k):
    r = 1
    while k:
        if k & 1:
            r = gmul(r, a)
        a = gmul(a, a)
        k >>= 1
    return r


# ----------------------------------------------------------------- hash ----
def H(label, *parts, length=32):
    h = hashlib.shake_256()
    h.update(label)
    for p in parts:
        h.update(struct.pack('>Q', len(p)))
        h.update(p)
    return h.digest(length)


def prg(seed, nbits):
    return int.from_bytes(hashlib.shake_256(b'CQ48/prg' + seed).digest((nbits + 7) // 8), 'big') & ((1 << nbits) - 1)


def bits_of(x, n):
    return [(x >> i) & 1 for i in range(n)]


# --------------------------------------------------------------- GGM tree ----
def ggm_leaves(root, depth):
    level = [root]
    for _ in range(depth):
        nxt = []
        for node in level:
            nxt.append(H(b'CQ48/L', node))
            nxt.append(H(b'CQ48/R', node))
        level = nxt
    return level


def ggm_open(root, depth, hidden):
    """Sibling nodes along the path to `hidden` (from the root down)."""
    node, path = root, []
    for lvl in range(depth):
        bit = (hidden >> (depth - 1 - lvl)) & 1
        left, right = H(b'CQ48/L', node), H(b'CQ48/R', node)
        path.append(right if bit == 0 else left)
        node = left if bit == 0 else right
    return path


def ggm_reconstruct(path, depth, hidden):
    """All leaves except `hidden` from the sibling path; None at the hidden index."""
    leaves = [None] * (1 << depth)

    def fill(node, lvl, index):
        if lvl == depth:
            leaves[index] = node
            return
        fill(H(b'CQ48/L', node), lvl + 1, index << 1)
        fill(H(b'CQ48/R', node), lvl + 1, (index << 1) | 1)
    for lvl in range(depth):
        bit = (hidden >> (depth - 1 - lvl)) & 1
        sib_index = ((hidden >> (depth - lvl)) << 1) | (1 - bit)
        fill(path[lvl], lvl + 1, sib_index)
    return leaves


# ------------------------------------------------------- constraint build ----
def r7_cubic_table(field, n):
    """(r^7)_k as multilinear monomials in r's bits, for each output bit k."""
    sq = [field.mul(1 << b, 1 << b) for b in range(n)]           # x^(2b)
    sq4 = [field.mul(sq[c], sq[c]) for c in range(n)]            # x^(4c)
    table = [dict() for _ in range(n)]
    for a in range(n):
        for b in range(n):
            ab = field.mul(1 << a, sq[b])
            for c in range(n):
                prod = field.mul(ab, sq4[c])
                mono = tuple(sorted({a, b, c}))
                for k in range(n):
                    if (prod >> k) & 1:
                        table[k][mono] = table[k].get(mono, 0) ^ 1
    return [[m for m, v in t.items() if v] for t in table]


def build_constraints(p, registry, domain, parsed, r7_table):
    """List of constraints; each is a list of monomials (tuples of witness
    positions, () = constant 1). Constraint satisfied iff XOR over monomials = 0."""
    n = p.n
    keys = [int.from_bytes(k, 'big') for k in registry.keys[domain]]
    c = modeB.challenge(p, parsed.cfg, domain, parsed.message)
    cs_cols = [p.field.mul(c, 1 << a) for a in range(n)]
    cons = []
    for j in range(QUORUM):
        base = j * W_SEAT
        z = int.from_bytes(parsed.handles[j], 'big')
        for e in range(p.keymap.m):
            monos = []
            if p.keymap.const[e]:
                monos.append(())
            lin = p.keymap.lin[e]
            for i in range(2 * n):
                if (lin >> i) & 1:
                    monos.append((base + i,))
                row = p.keymap.rows[e][i]
                jj = i + 1
                while row >> jj:
                    if (row >> jj) & 1:
                        monos.append((base + i, base + jj))
                    jj += 1
            for i in range(N_SEATS):
                if (keys[i] >> e) & 1:
                    monos.append((base + 2 * n + i,))
            cons.append(monos)
        for k in range(n):
            monos = [()] if (z >> k) & 1 else []
            for a in range(n):
                if (cs_cols[a] >> k) & 1:
                    monos.append((base + a,))
            for mono in r7_table[k]:
                monos.append(tuple(base + n + idx for idx in mono))
            cons.append(monos)
        cons.append([()] + [(base + 2 * n + i,) for i in range(N_SEATS)])
    return cons


def witness_bits(rows):
    w = []
    for (i, s, r) in rows:
        w += bits_of(s, TOY_N) + bits_of(r, TOY_N)
        w += [1 if t == i else 0 for t in range(N_SEATS)]
    return w


def eval_constraints(cons, w):
    bad = 0
    for monos in cons:
        acc = 0
        for mono in monos:
            v = 1
            for pos in mono:
                v &= w[pos]
            acc ^= v
        bad += acc
    return bad


# ------------------------------------------------------ polynomial in X ----
def mono_poly(mono, V, w):
    """Coefficients [X^0..X^3] of X^(3-|S|) * prod_{p in S} (V_p + X w_p)."""
    coeffs = [1, 0, 0, 0]
    deg = 0
    for pos in mono:
        vp, wp = V[pos], w[pos]
        new = [0, 0, 0, 0]
        for k in range(deg + 1):
            if coeffs[k]:
                new[k] ^= gmul(coeffs[k], vp)
                if wp:
                    new[k + 1] ^= coeffs[k]
        coeffs, deg = new, deg + 1
    shift = DEGREE - len(mono)
    return [0] * shift + coeffs[:DEGREE + 1 - shift]


def mono_eval(mono, Q, delta_pows):
    v = delta_pows[DEGREE - len(mono)]
    for pos in mono:
        v = gmul(v, Q[pos])
    return v


# ------------------------------------------------------------- transcript ----
def fs_challenge(label, transcript, nbits):
    return prg(H(label, transcript), nbits)


def ser_bits(bits):
    x = 0
    for i, b in enumerate(bits):
        x |= b << i
    return x.to_bytes((len(bits) + 7) // 8, 'big')


def deser_bits(data, n):
    x = int.from_bytes(data, 'big')
    return [(x >> i) & 1 for i in range(n)]


# ------------------------------------------------------------------ prove ----
def prove(p, registry, domain, parsed_stmt, rows, statement, rng, r7_table):
    cons = build_constraints(p, registry, domain, parsed_stmt, r7_table)
    w = witness_bits(rows)
    if eval_constraints(cons, w):
        raise ProofError('witness does not satisfy R_B')
    w += [rng.getrandbits(1) for _ in range(MASK_BITS)]          # mask positions
    # 1. trees, leaves, VOLE
    roots = [H(b'CQ48/root', rng.getrandbits(256).to_bytes(32, 'big'), statement) for _ in range(TAU)]
    leaves = [ggm_leaves(root, B_BITS) for root in roots]
    coms = [[H(b'CQ48/com', leaf) for leaf in tree] for tree in leaves]
    h_com = H(b'CQ48/hcom', *[c for tree in coms for c in tree])
    u = [0] * TAU
    v = [[0] * B_BITS for _ in range(TAU)]
    for j in range(TAU):
        for i, leaf in enumerate(leaves[j]):
            r_i = prg(leaf, ELL_HAT)
            u[j] ^= r_i
            for t in range(B_BITS):
                if (i >> t) & 1:
                    v[j][t] ^= r_i
    corrections = [u[0] ^ u[j] for j in range(1, TAU)]
    wint = int(''.join('1' if b else '0' for b in reversed(w)), 2)
    d = wint ^ u[0]
    V = []
    for pos in range(ELL_HAT):
        val = 0
        for j in range(TAU):
            for t in range(B_BITS):
                if (v[j][t] >> pos) & 1:
                    val |= 1 << (j * B_BITS + t)
        V.append(val)
    round1 = h_com + b''.join(c.to_bytes((ELL_HAT + 7) // 8, 'big') for c in corrections) + d.to_bytes((ELL_HAT + 7) // 8, 'big')
    transcript = statement + round1
    # 2. VOLE consistency hash
    chi1 = fs_challenge(b'CQ48/chi1', transcript, LAMBDA)
    u_tilde, h_v, cp = 0, 0, 1
    for pos in range(ELL):
        u_bit = (u[0] >> pos) & 1
        if u_bit:
            u_tilde ^= cp
        h_v ^= gmul(cp, V[pos])
        cp = gmul(cp, chi1)
    for t in range(LAMBDA):                                       # basis-coded mask
        pos = ELL + t
        if (u[0] >> pos) & 1:
            u_tilde ^= 1 << t
        h_v ^= gmul(1 << t, V[pos])
    round2 = u_tilde.to_bytes(8, 'big') + h_v.to_bytes(8, 'big')
    transcript += round2
    # 3. QuickSilver
    chi2 = fs_challenge(b'CQ48/chi2', transcript, LAMBDA)
    A = [0, 0, 0, 0]
    cc = 1
    for monos in cons:
        pc = [0, 0, 0, 0]
        for mono in monos:
            mp = mono_poly(mono, V, w)
            for k in range(4):
                pc[k] ^= mp[k]
        for k in range(4):
            A[k] ^= gmul(cc, pc[k])
        cc = gmul(cc, chi2)
    if A[3]:
        raise ProofError('internal: top coefficient nonzero')
    masks = []
    for k in range(DEGREE - 1):
        base = ELL + LAMBDA + k * LAMBDA
        a_star = sum(w[base + t] << t for t in range(LAMBDA))
        b_star = 0
        for t in range(LAMBDA):
            b_star ^= gmul(1 << t, V[base + t])
        masks.append((a_star, b_star))
    A_sent = [A[0] ^ masks[0][1],
              A[1] ^ masks[0][0] ^ masks[1][1],
              A[2] ^ masks[1][0]]
    round3 = b''.join(x.to_bytes(8, 'big') for x in A_sent)
    transcript += round3
    # 4. openings
    deltas = [fs_challenge(b'CQ48/delta%d' % j, transcript, B_BITS) for j in range(TAU)]
    openings = b''
    for j in range(TAU):
        for node in ggm_open(roots[j], B_BITS, deltas[j]):
            openings += node
        openings += coms[j][deltas[j]]
    return round1 + round2 + round3 + openings


# ----------------------------------------------------------------- verify ----
def verify(p, registry, domain, parsed_stmt, statement, proof, r7_table):
    nb = (ELL_HAT + 7) // 8
    off = 0
    h_com = proof[off:off + 32]; off += 32
    corrections = []
    for _ in range(TAU - 1):
        corrections.append(int.from_bytes(proof[off:off + nb], 'big')); off += nb
    d = int.from_bytes(proof[off:off + nb], 'big'); off += nb
    round1 = proof[:off]
    u_tilde = int.from_bytes(proof[off:off + 8], 'big'); h_v = int.from_bytes(proof[off + 8:off + 16], 'big')
    round2 = proof[off:off + 16]; off += 16
    A_sent = [int.from_bytes(proof[off + 8 * k:off + 8 * k + 8], 'big') for k in range(3)]
    round3 = proof[off:off + 24]; off += 24
    transcript = statement + round1
    chi1 = fs_challenge(b'CQ48/chi1', transcript, LAMBDA)
    transcript += round2
    chi2 = fs_challenge(b'CQ48/chi2', transcript, LAMBDA)
    transcript += round3
    deltas = [fs_challenge(b'CQ48/delta%d' % j, transcript, B_BITS) for j in range(TAU)]
    # reconstruct leaves, commitments, q
    coms_all = []
    q = [[0] * B_BITS for _ in range(TAU)]
    for j in range(TAU):
        path = [proof[off + 32 * t:off + 32 * t + 32] for t in range(B_BITS)]; off += 32 * B_BITS
        com_hidden = proof[off:off + 32]; off += 32
        leaves = ggm_reconstruct(path, B_BITS, deltas[j])
        for i, leaf in enumerate(leaves):
            if leaf is None:
                coms_all.append(com_hidden)
                continue
            coms_all.append(H(b'CQ48/com', leaf))
            r_i = prg(leaf, ELL_HAT)
            for t in range(B_BITS):
                if ((i >> t) & 1) ^ ((deltas[j] >> t) & 1):
                    q[j][t] ^= r_i
        if j >= 1:                                                # correction to u_1
            for t in range(B_BITS):
                if (deltas[j] >> t) & 1:
                    q[j][t] ^= corrections[j - 1]
    if off != len(proof):
        raise ProofError('trailing bytes')
    if H(b'CQ48/hcom', *coms_all) != h_com:
        raise ProofError('commitment hash mismatch')
    Delta = 0
    for j in range(TAU):
        Delta |= deltas[j] << (j * B_BITS)
    Qraw, Q = [], []
    for pos in range(ELL_HAT):
        val = 0
        for j in range(TAU):
            for t in range(B_BITS):
                if (q[j][t] >> pos) & 1:
                    val |= 1 << (j * B_BITS + t)
        Qraw.append(val)                                  # = V_p + Delta u_p
        Q.append(val ^ Delta if (d >> pos) & 1 else val)  # = V_p + Delta w_p
    # VOLE consistency on the raw correlation (before the witness correction)
    lhs, cp = 0, 1
    for pos in range(ELL):
        lhs ^= gmul(cp, Qraw[pos]); cp = gmul(cp, chi1)
    for t in range(LAMBDA):
        lhs ^= gmul(1 << t, Qraw[ELL + t])
    if lhs != h_v ^ gmul(Delta, u_tilde):
        raise ProofError('VOLE consistency check failed')
    # QuickSilver
    cons = build_constraints(p, registry, domain, parsed_stmt, r7_table)
    delta_pows = [gpow(Delta, k) for k in range(DEGREE + 1)]
    C, cc = 0, 1
    for monos in cons:
        fc = 0
        for mono in monos:
            fc ^= mono_eval(mono, Q, delta_pows)
        C ^= gmul(cc, fc); cc = gmul(cc, chi2)
    for k in range(DEGREE - 1):
        base = ELL + LAMBDA + k * LAMBDA
        q_star = 0
        for t in range(LAMBDA):
            q_star ^= gmul(1 << t, Q[base + t])
        C ^= gmul(delta_pows[k], q_star)
    rhs = 0
    for k in range(DEGREE):
        rhs ^= gmul(A_sent[k], delta_pows[k])
    if C != rhs:
        raise ProofError('QuickSilver check failed')
    return True


# ------------------------------------------------------------- pipeline ----
class ToyBackend:
    qualified = False           # toy security; structurally faithful

    def __init__(self, p, registry, domain, rng):
        self.p, self.registry, self.domain, self.rng = p, registry, domain, rng
        self.r7 = r7_cubic_table(p.field, p.n)

    def statement(self, parsed):
        """Binds cfg, domain, message and the handles (not payload_len, which
        depends on the proof length itself)."""
        return H(b'CQ48/stmt', parsed.cfg, parsed.domain, parsed.message, *parsed.handles)

    def prove_frame(self, message, seats):
        secrets = self.secrets
        frame0 = modeB.encode(self.p, self.registry, secrets, self.domain, message, seats, proof=b'')
        parsed = modeB.parse(self.p, frame0)
        c = modeB.challenge(self.p, parsed.cfg, self.domain, message)
        by = {modeB.handle(self.p, secrets[self.domain][i], c): i for i in seats}
        rows = [(by[z],) + secrets[self.domain][by[z]] for z in parsed.handles]
        stmt = self.statement(parsed)
        proof = prove(self.p, self.registry, self.domain, parsed, rows, stmt, self.rng, self.r7)
        return modeB.encode(self.p, self.registry, secrets, self.domain, message, seats, proof=proof)

    def verify_frame(self, frame):
        parsed = modeB.parse(self.p, frame)
        if parsed.cfg != modeB.cfg_of(self.registry, self.p):
            raise ProofError('configuration mismatch')
        return verify(self.p, self.registry, self.domain, parsed, self.statement(parsed), parsed.proof, self.r7)


def formula_bytes(tau, ell, t_open, blocks, lam, degree, node_bits=None):
    """FAEST v2 size formula. node_bits sizes the opened tree nodes and leaf
    commitments (lambda in FAEST; this toy uses 256-bit SHAKE outputs)."""
    node_bits = node_bits or lam
    return (tau * (ell + 3 * lam + 16) + t_open * node_bits + blocks * node_bits * tau
            + lam + 128 + 32 + (degree - 2) * lam * tau + 7) // 8


def run_pipeline(seed=48, verbose=True):
    t0 = time.time()
    p = modeB.make_params(n=TOY_N, expansion=TOY_EXPANSION, seed=b'CQ48/toy')
    rng = random.Random(seed)
    d0 = bytes(range(64))
    registry, secrets = modeB.build_registry(p, b'CQ48-epoch', (d0,), rng)
    backend = ToyBackend(p, registry, d0, rng)
    backend.secrets = secrets
    m0, m1 = bytes(64), bytes(63) + b'\x11'
    left = list(range(QUORUM))
    right = list(range(MIN_OVERLAP)) + list(range(QUORUM, N_SEATS))
    t1 = time.time()
    f0 = backend.prove_frame(m0, left)
    t2 = time.time()
    f1 = backend.prove_frame(m1, right)
    ok0 = backend.verify_frame(f0)
    t3 = time.time()
    ok1 = backend.verify_frame(f1)
    blames = modeB.extract(p, registry, f0, f1)
    proof_len = len(modeB.parse(p, f0).proof)
    out = {
        'toy_params': {'n': TOY_N, 'keymap_m': p.keymap.m, 'tau': TAU, 'parties_log2': B_BITS,
                       'lambda': LAMBDA, 'ell': ELL, 'ell_hat': ELL_HAT},
        'frame_bytes': len(f0), 'proof_bytes_measured': proof_len,
        'proof_bytes_formula_lambda_bit_nodes': formula_bytes(TAU, ELL_HAT, TAU * B_BITS, 2, LAMBDA, DEGREE),
        'proof_bytes_formula_256_bit_nodes_1_block': formula_bytes(TAU, ELL_HAT, TAU * B_BITS, 1, LAMBDA, DEGREE, 256),
        'proof_breakdown_bytes': {
            'corrections_(tau-1)*ell_hat': (TAU - 1) * ((ELL_HAT + 7) // 8),
            'witness_correction_d': (ELL_HAT + 7) // 8,
            'vole_hash_u_tilde_h_v': 16, 'quicksilver_coefficients': 24, 'h_com': 32,
            'openings_tau*(b_nodes+com)*32': TAU * (B_BITS + 1) * 32},
        'verified': [ok0, ok1],
        'extracted_seats': [b.seat for b in blames], 'extracted_count': len(blames),
        'all_blames_verified': all(modeB.verify_blame(p, registry, f0, f1, b) for b in blames),
        'seconds': {'setup': round(t1 - t0, 1), 'prove_one': round(t2 - t1, 1),
                    'prove_second_plus_verify_first': round(t3 - t2, 1),
                    'total': round(time.time() - t0, 1)},
    }
    if verbose:
        print(json.dumps(out, indent=2))
    return out, backend, f0, f1


# ------------------------------------------------------------------ tests ----
class ToyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out, cls.backend, cls.f0, cls.f1 = run_pipeline(verbose=False)

    def test_pipeline_end_to_end(self):
        self.assertEqual(self.out['verified'], [True, True])
        self.assertEqual(self.out['extracted_seats'], list(range(MIN_OVERLAP)))
        self.assertTrue(self.out['all_blames_verified'])
        self.assertLessEqual(self.out['frame_bytes'], 32768)

    def test_measured_size_matches_formula(self):
        m = self.out['proof_bytes_measured']
        f256 = self.out['proof_bytes_formula_256_bit_nodes_1_block']
        self.assertLess(abs(m - f256) / f256, 0.05)      # same node size: within 5%
        self.assertEqual(m, sum(self.out['proof_breakdown_bytes'].values()))
        # The lambda-bit-node formula (as used for the production sizes) is below
        # the toy's bytes only because the toy opens 256-bit nodes for a 64-bit MAC field.
        self.assertLess(self.out['proof_bytes_formula_lambda_bit_nodes'], m)

    def test_tampered_proof_rejected(self):
        p = modeB.parse(self.backend.p, self.f0)
        for byte_off in (0, 40, len(p.proof) // 2, len(p.proof) - 1):
            bad = bytearray(self.f0)
            bad[len(self.f0) - len(p.proof) + byte_off] ^= 0x01
            with self.assertRaises(ProofError):
                self.backend.verify_frame(bytes(bad))

    def test_wrong_statement_rejected(self):
        # Same proof bytes under a different message: the FS challenges change.
        p = modeB.parse(self.backend.p, self.f0)
        hdr = bytearray(self.f0[:modeB.HEADER_BYTES])
        hdr[144:208] = bytes(63) + b'\x22'
        with self.assertRaises((ProofError, modeB.ModeBError)):
            self.backend.verify_frame(bytes(hdr) + self.f0[modeB.HEADER_BYTES:])

    def test_false_witness_refused_by_prover(self):
        b = self.backend
        secrets = dict(b.secrets)
        bad = list(secrets[b.domain])
        s, r = bad[0]
        bad[0] = (s ^ 1, r)                     # opening no longer matches Y[0]
        secrets2 = {b.domain: tuple(bad)}
        backend2 = ToyBackend(b.p, b.registry, b.domain, random.Random(1))
        backend2.secrets = secrets2
        with self.assertRaises((ProofError, modeB.ModeBError)):
            backend2.prove_frame(bytes(63) + b'\x33', list(range(QUORUM)))

    def test_ggm_open_reconstruct(self):
        root = H(b'x', b'root')
        leaves = ggm_leaves(root, B_BITS)
        for hidden in (0, 1, 77, 255):
            rec = ggm_reconstruct(ggm_open(root, B_BITS, hidden), B_BITS, hidden)
            self.assertIsNone(rec[hidden])
            self.assertTrue(all(rec[i] == leaves[i] for i in range(256) if i != hidden))

    def test_r7_table_matches_field(self):
        p = self.backend.p
        rng = random.Random(5)
        for _ in range(20):
            r = rng.getrandbits(TOY_N)
            rb = bits_of(r, TOY_N)
            want = p.field.G(r)
            for k in range(TOY_N):
                acc = 0
                for mono in self.backend.r7[k]:
                    v = 1
                    for idx in mono:
                        v &= rb[idx]
                    acc ^= v
                self.assertEqual(acc, (want >> k) & 1)


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--run', action='store_true')
    a = ap.parse_args(argv)
    if a.run:
        run_pipeline()
        return 0
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ToyTests))
    return 0 if r.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
