# pq_audit_s1_lms_v2.2.py — audit-fix release of v2.1 (2026-09-13): F3, refuse non-approved mixed m/n typecodes.
#!/usr/bin/env python3
r"""Audit S1 — firmware / LMS (RFC 8554, SP 800-208). Four audit columns:

  (1) Does the implementation do what the specification says?
      RFC 8554-EXACT LM-OTS + LMS written here from the RFC text (typecodes,
      D_PBLC/D_MESG/D_LEAF/D_INTR, coef(), checksum, node numbering), sizes
      DERIVED from typecodes, and cross-verified in BOTH directions against an
      independent implementation (hsslms 0.1.3, PyPI) that knows nothing about
      this code.
  (2) Can we reproduce the claimed resource numbers?  Sizes 1,772 / 2,180 B
      etc. come out of the typecode arithmetic, not constants.
  (3) Can an adversary violate the property?  A persistent signer with an NVM
      model + hardware monotonic counter, crash injection at every step of
      reserve -> sign -> persist, rollback, concurrency, exhaustion, and the
      clone experiment that shows WHY key export must be forbidden.
  (4) Does the bound support the claim?  Explicit attack GAMES G1..G5 with
      their query costs, the cheapest one identified, and a reduced-size Grover
      simulation on the actual LM-OTS keyed chain structure that confirms the
      2^(n/2) law the ledger uses.

Untestable assumption stated at the end.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import secrets
import struct
import sys
import threading
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
try:
    import hsslms                                      # independent implementation
    HAVE_HSSLMS = True
except Exception:                                      # pragma: no cover
    HAVE_HSSLMS = False


def u32(x): return struct.pack('>I', x)
def u16(x): return struct.pack('>H', x)
def u8(x): return struct.pack('>B', x)


D_PBLC, D_MESG, D_LEAF, D_INTR = u16(0x8080), u16(0x8181), u16(0x8282), u16(0x8383)

# ---------------------------------------------------------------- RFC 8554 --
# typecode -> (n, w)          (SP 800-208 §4.1 Table 1 / §4.2 Table 3)
LMOTS = {1: (32, 1), 2: (32, 2), 3: (32, 4), 4: (32, 8), 5: (24, 1), 6: (24, 2), 7: (24, 4), 8: (24, 8)}
# typecode -> (m, h)          (§4.1 Table 2 / §4.2 Table 4)
LMS = {5: (32, 5), 6: (32, 10), 7: (32, 15), 8: (32, 20), 9: (32, 25),
       10: (24, 5), 11: (24, 10), 12: (24, 15), 13: (24, 20), 14: (24, 25)}


def lmots_params(tc):
    n, w = LMOTS[tc]
    u = 8 * n // w
    v = math.ceil((math.floor(math.log2((2 ** w - 1) * u)) + 1) / w)
    ls = 16 - v * w
    return n, w, u + v, ls


def H(data, n=32):
    return hashlib.sha256(data).digest()[:n]


def coef(S, i, w):
    return (2 ** w - 1) & (S[(i * w) // 8] >> (8 - (w * (i % (8 // w)) + w)))


def checksum(Q, n, w, ls):
    u = 8 * n // w
    s = sum((2 ** w - 1) - coef(Q, i, w) for i in range(u))
    return (s << ls) & 0xFFFF


def lmots_sizes(tc):
    n, w, p, ls = lmots_params(tc)
    return {'sig': 4 + n + p * n, 'p': p, 'ls': ls}


def approved_pair(lms_tc, ots_tc):
    """SP 800-208 §4 lists LMS sets with m = 32 only alongside LM-OTS sets with n = 32, and m = 24 with
    n = 24 (same hash function). RFC 8554 §5.1 is silent on n vs m but says the hash functions SHOULD be
    the same. Mixed pairs are therefore not approved; both this implementation and hsslms 0.1.3 accepted
    them and hsslms is self-inconsistent on them (audit stack v0.1, F3)."""
    return lms_tc in LMS and ots_tc in LMOTS and LMS[lms_tc][0] == LMOTS[ots_tc][0]


def lms_sizes(lms_tc, ots_tc):
    m, h = LMS[lms_tc]
    return {'pub': 4 + 4 + 16 + m, 'sig': 4 + lmots_sizes(ots_tc)['sig'] + 4 + h * m}


class LmotsKey:
    def __init__(self, tc, I, q, seed):
        self.tc, self.I, self.q = tc, I, q
        self.n, self.w, self.p, self.ls = lmots_params(tc)
        # RFC 8554 Appendix A pseudorandom key generation
        self.x = [H(I + u32(q) + u16(i) + u8(0xff) + seed, self.n) for i in range(self.p)]

    def _chain(self, i, start, end, tmp):
        for j in range(start, end):
            tmp = H(self.I + u32(self.q) + u16(i) + u8(j) + tmp, self.n)
        return tmp

    def public_K(self):
        y = [self._chain(i, 0, 2 ** self.w - 1, self.x[i]) for i in range(self.p)]
        return H(self.I + u32(self.q) + D_PBLC + b''.join(y), self.n)

    def sign(self, message, C=None):
        C = secrets.token_bytes(self.n) if C is None else C
        Q = H(self.I + u32(self.q) + D_MESG + C + message, self.n)
        Qc = Q + u16(checksum(Q, self.n, self.w, self.ls))
        y = [self._chain(i, 0, coef(Qc, i, self.w), self.x[i]) for i in range(self.p)]
        return u32(self.tc) + C + b''.join(y)


def lmots_candidate_K(tc, I, q, message, sig):
    n, w, p, ls = lmots_params(tc)
    if len(sig) != 4 + n + p * n or struct.unpack('>I', sig[:4])[0] != tc:
        return None
    C = sig[4:4 + n]
    y = [sig[4 + n + i * n: 4 + n + (i + 1) * n] for i in range(p)]
    Q = H(I + u32(q) + D_MESG + C + message, n)
    Qc = Q + u16(checksum(Q, n, w, ls))
    z = []
    for i in range(p):
        tmp = y[i]
        for j in range(coef(Qc, i, w), 2 ** w - 1):
            tmp = H(I + u32(q) + u16(i) + u8(j) + tmp, n)
        z.append(tmp)
    return H(I + u32(q) + D_PBLC + b''.join(z), n)


class LmsPrivate:
    """RFC 8554 §5 LMS; node numbering r=1 root .. leaves 2^h+q."""

    def __init__(self, lms_tc, ots_tc, I=None, seed=None):
        if not approved_pair(lms_tc, ots_tc):
            raise ValueError('F3: LMS m and LM-OTS n must match (SP 800-208 approved sets pair n with m; '
                             'RFC 8554 5.1: the two hash functions SHOULD be the same)')
        self.lms_tc, self.ots_tc = lms_tc, ots_tc
        self.m, self.h = LMS[lms_tc]
        self.I = secrets.token_bytes(16) if I is None else I
        self.seed = secrets.token_bytes(32) if seed is None else seed
        self.q = 0
        N = 1 << self.h
        self.T = [None] * (2 * N)
        for i in range(N):
            K = LmotsKey(ots_tc, self.I, i, self.seed).public_K()
            self.T[N + i] = H(self.I + u32(N + i) + D_LEAF + K, self.m)
        for r in range(N - 1, 0, -1):
            self.T[r] = H(self.I + u32(r) + D_INTR + self.T[2 * r] + self.T[2 * r + 1], self.m)

    def public_key(self):
        return u32(self.lms_tc) + u32(self.ots_tc) + self.I + self.T[1]

    def path(self, q):
        r, out = (1 << self.h) + q, []
        for _ in range(self.h):
            out.append(self.T[r ^ 1])
            r >>= 1
        return b''.join(out)

    def sign_with_index(self, q, message):
        ots = LmotsKey(self.ots_tc, self.I, q, self.seed).sign(message)
        return u32(q) + ots + u32(self.lms_tc) + self.path(q)

    def sign(self, message):
        if self.q >= (1 << self.h):
            raise RuntimeError('LMS private key exhausted')
        q = self.q
        self.q += 1
        return self.sign_with_index(q, message)


def lms_verify(pubkey, message, sig):
    if len(pubkey) < 24:
        return False
    lms_tc, ots_tc = struct.unpack('>II', pubkey[:8])
    if lms_tc not in LMS or ots_tc not in LMOTS or not approved_pair(lms_tc, ots_tc):
        return False                                   # F3: refuse non-approved n != m combinations
    m, h = LMS[lms_tc]
    if len(pubkey) != 24 + m:
        return False
    I, T1 = pubkey[8:24], pubkey[24:]
    ots_len = lmots_sizes(ots_tc)['sig']
    if len(sig) != 4 + ots_len + 4 + h * m:
        return False
    q = struct.unpack('>I', sig[:4])[0]
    if q >= (1 << h):
        return False
    ots = sig[4:4 + ots_len]
    if struct.unpack('>I', sig[4 + ots_len:8 + ots_len])[0] != lms_tc:
        return False
    path = sig[8 + ots_len:]
    Kc = lmots_candidate_K(ots_tc, I, q, message, ots)
    if Kc is None:
        return False
    r = (1 << h) + q
    tmp = H(I + u32(r) + D_LEAF + Kc, m)
    for i in range(h):
        sib = path[i * m:(i + 1) * m]
        if r & 1:
            tmp = H(I + u32(r >> 1) + D_INTR + sib + tmp, m)
        else:
            tmp = H(I + u32(r >> 1) + D_INTR + tmp + sib, m)
        r >>= 1
    return tmp == T1


# ------------------------------------------------- persistent signer / NVM --
class Crash(Exception):
    pass


class NVM:
    """Non-volatile store with atomic record write; the hardware monotonic
    counter can only increase and cannot be restored from a snapshot."""

    def __init__(self):
        self.record = None          # {'q': next index, 'ctr': counter at write}
        self.hw_counter = 0         # tamper-resistant monotonic counter

    def snapshot(self):
        return dict(self.record) if self.record else None

    def restore(self, snap):        # an attacker's rollback: hw_counter untouched
        self.record = dict(snap) if snap else None


class PersistentSigner:
    """reserve (NVM commit of q+1 and hw_counter+1)  ->  sign  ->  release.
    `crash_at` ∈ {None, 'before_reserve', 'after_counter', 'after_record',
    'after_sign'} raises Crash at that point (power loss)."""

    STEPS = ('before_reserve', 'after_counter', 'after_record', 'after_sign')

    def __init__(self, key: LmsPrivate, nvm: NVM):
        self.key, self.nvm = key, nvm
        self.lock = threading.Lock()
        if nvm.record is None:
            nvm.record = {'q': 0, 'ctr': nvm.hw_counter}
        self.boot_check()

    def boot_check(self):
        rec = self.nvm.record
        if rec['ctr'] != self.nvm.hw_counter:
            # NVM record is older than the hardware counter: rollback or torn write.
            # Fail closed: skip ahead by the counter gap so no leaf can be reused.
            gap = self.nvm.hw_counter - rec['ctr']
            if gap < 0:
                raise RuntimeError('hardware counter behind record: impossible state')
            self.nvm.record = {'q': rec['q'] + gap, 'ctr': self.nvm.hw_counter}

    def sign(self, message, crash_at=None):
        with self.lock:
            if crash_at == 'before_reserve':
                raise Crash
            rec = self.nvm.record
            q = rec['q']
            if q >= (1 << self.key.h):
                raise RuntimeError('exhausted')
            self.nvm.hw_counter += 1                       # step 1: counter
            if crash_at == 'after_counter':
                raise Crash
            self.nvm.record = {'q': q + 1, 'ctr': self.nvm.hw_counter}   # step 2: record (atomic)
            if crash_at == 'after_record':
                raise Crash
            sig = self.key.sign_with_index(q, message)      # step 3: sign
            if crash_at == 'after_sign':
                raise Crash                                 # signature may have leaked: count it
            return sig


# ---------------------------------------------------- quantum attack games --
GATES_PER_QUERY_LOG2 = 18
BUDGET_LOG2 = 128


def attack_games(n_bits, h, p, w):
    """Each game: what the adversary must find, the generic quantum query cost
    (log2), and why. Multi-target speedups are blocked by the (I, q, i, j)
    domain separation in every hash call: each target lives in a different
    function, so a Grover search over one function hits at most one target."""
    return [
        {'id': 'G1', 'game': 'second preimage of the message hash Q = H(I||q||D_MESG||C||m) for a signed (C,m)',
         'quantum_queries_log2': n_bits / 2, 'why': 'Grover on a fixed function, single target (C fixed by signer)'},
        {'id': 'G2', 'game': 'invert one LM-OTS chain node H(I||q||i||j||.) to lower a digit',
         'quantum_queries_log2': n_bits / 2, 'why': 'single-target Grover; (I,q,i,j) prefix makes each node its own function'},
        {'id': 'G3', 'game': 'hash collision on Q to sign two messages with one OTS leaf',
         'quantum_queries_log2': n_bits / 3, 'why': 'BHT with QRAM; but the attacker does not choose C, so a collision '
                                                    'gives no forgery in EUF-CMA (recorded, not counted)', 'counts': False},
        {'id': 'G4', 'game': 'forge a Merkle path to a fresh leaf (second preimage on an interior node)',
         'quantum_queries_log2': n_bits / 2, 'why': 'node prefix (I, r, D_INTR) fixes the function'},
        {'id': 'G5', 'game': 'find a message whose digit vector dominates a signed one (no inversion)',
         'quantum_queries_log2': float('inf'), 'why': 'impossible: checksum strictly decreases when any digit increases'},
    ]


def cheapest_counting_game(games):
    return min((g for g in games if g.get('counts', True)), key=lambda g: g['quantum_queries_log2'])


def qpt128_verdict(n_bits):
    q = n_bits / 2
    gates = q + GATES_PER_QUERY_LOG2
    return {'n_bits': n_bits, 'queries_log2': q, 'gates_log2': gates, 'margin_bits': gates - BUDGET_LOG2,
            'passes': gates >= BUDGET_LOG2}


def grover_chain_inversion(n, I=b'I' * 16, q=3, i=5, j=2):
    """Reduced-size game G2 on the ACTUAL keyed chain structure: inputs are n-bit,
    the hash is SHA-256 truncated to n bits, the target is the chain value of a
    random secret. Exact state-vector Grover; returns measured optimal iteration
    count and success probability vs the closed form."""
    import numpy as np
    N = 1 << n
    nb = (n + 7) // 8
    secret = secrets.randbelow(N)

    def f(x):
        d = hashlib.sha256(I + u32(q) + u16(i) + u8(j) + x.to_bytes(nb, 'big')).digest()
        return int.from_bytes(d[:nb], 'big') & (N - 1)
    target = f(secret)
    marked = np.array([f(x) == target for x in range(N)])
    M = int(marked.sum())
    theta = math.asin(math.sqrt(M / N))
    k_pred = int(math.floor(math.pi / (4 * theta)))
    amp = np.full(N, 1 / math.sqrt(N))
    probs = [float((amp[marked] ** 2).sum())]
    for k in range(1, 2 * k_pred + 3):
        amp[marked] *= -1
        amp = 2 * amp.mean() - amp
        probs.append(float((amp[marked] ** 2).sum()))
    # first peak of the oscillation = the iteration count an attacker would use
    k_first_peak = next(k for k in range(1, len(probs) - 1) if probs[k + 1] < probs[k])
    pred_p = math.sin((2 * k_pred + 1) * theta) ** 2
    return {'n': n, 'marked': M, 'k_measured': k_first_peak, 'k_predicted': k_pred,
            'p_measured': probs[k_first_peak], 'p_predicted_at_k_pred': pred_p,
            'p_at_k_pred': probs[k_pred]}


# ----------------------------------------------------------------- tests ----
class Tests(unittest.TestCase):
    def test_S1_001_sizes_from_typecodes(self):
        """S1-001 sizes derived from typecode arithmetic match RFC 8554 / SP 800-208."""
        self.assertEqual([lmots_params(t)[2] for t in (1, 2, 3, 4)], [265, 133, 67, 34])
        self.assertEqual([lmots_params(t)[3] for t in (1, 2, 3, 4)], [7, 6, 4, 0])
        self.assertEqual([lmots_params(t)[2] for t in (5, 6, 7, 8)], [200, 101, 51, 26])   # n=24
        self.assertEqual(lms_sizes(8, 4)['sig'], 1772)        # H20 / W8
        self.assertEqual(lms_sizes(8, 3)['sig'], 2828)        # H20 / W4
        self.assertEqual(lms_sizes(13, 8)['sig'], 4 + (4 + 24 + 26 * 24) + 4 + 20 * 24)   # n=24 set: 1,140
        self.assertEqual(lms_sizes(8, 4)['pub'], 56)
        # cross-check with the v2.0 WOTS formula used in S4/S5
        spec = importlib.util.spec_from_file_location('s4', os.path.join(_HERE, 's4_embedded_broadcast.py'))
        s4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s4)
        self.assertEqual(s4.WOTS(256).sig_bytes(20), lms_sizes(8, 4)['sig'])

    def test_S1_002_self_roundtrip_all_ots_types(self):
        """S1-002 RFC-exact sign/verify round trip, tamper rejection, every typecode at H5."""
        for ots in (1, 2, 3, 4, 5, 6, 7, 8):
            lms_tc = 5 if LMOTS[ots][0] == 32 else 10
            k = LmsPrivate(lms_tc, ots, I=bytes(range(16)), seed=b'\x07' * 32)
            pk = k.public_key()
            sig = k.sign(b'firmware v1')
            self.assertEqual(len(sig), lms_sizes(lms_tc, ots)['sig'])
            self.assertTrue(lms_verify(pk, b'firmware v1', sig))
            self.assertFalse(lms_verify(pk, b'firmware v2', sig))
            bad = bytearray(sig); bad[40] ^= 1
            self.assertFalse(lms_verify(pk, b'firmware v1', bytes(bad)))
            bad = bytearray(sig); bad[-1] ^= 1
            self.assertFalse(lms_verify(pk, b'firmware v1', bytes(bad)))

    @unittest.skipUnless(HAVE_HSSLMS, 'hsslms not installed')
    def test_S1_003_interop_mine_to_hsslms(self):
        """S1-003 signatures from this implementation verify under hsslms (independent)."""
        for lms_tc, ots in ((5, 4), (5, 3), (5, 1), (10, 8), (6, 4)):
            k = LmsPrivate(lms_tc, ots)
            pub = hsslms.LMS_Pub(k.public_key())
            for msg in (b'', b'x', b'firmware image ' * 100):
                sig = k.sign(msg)
                pub.verify(msg, sig)                       # hsslms raises INVALID on failure
                with self.assertRaises(Exception):
                    pub.verify(msg + b'!', sig)
                bad = bytearray(sig); bad[-5] ^= 1
                with self.assertRaises(Exception):
                    pub.verify(msg, bytes(bad))

    @unittest.skipUnless(HAVE_HSSLMS, 'hsslms not installed')
    def test_S1_004_interop_hsslms_to_mine(self):
        """S1-004 signatures from hsslms verify under this implementation; tampering fails."""
        for lms_tc, ots in ((5, 4), (5, 3), (10, 8)):
            priv = hsslms.LMS_Priv(hsslms.LMS_ALGORITHM_TYPE(lms_tc), hsslms.LMOTS_ALGORITHM_TYPE(ots), num_cores=1)
            pk = priv.gen_pub().get_pubkey()
            self.assertEqual(len(pk), lms_sizes(lms_tc, ots)['pub'])
            for msg in (b'', b'boot block', b'A' * 4096):
                sig = priv.sign(msg)
                self.assertEqual(len(sig), lms_sizes(lms_tc, ots)['sig'])
                self.assertTrue(lms_verify(pk, msg, sig), (lms_tc, ots))
                self.assertFalse(lms_verify(pk, msg + b'\x00', sig))
                bad = bytearray(sig); bad[8] ^= 0x80
                self.assertFalse(lms_verify(pk, msg, bytes(bad)))

    def test_S1_005_state_machine_normal_and_exhaustion(self):
        """S1-005 every leaf used once in order; the 2^h+1-th signature is refused."""
        key = LmsPrivate(5, 4, I=b'\x01' * 16, seed=b'\x02' * 32)
        s = PersistentSigner(key, NVM())
        used = []
        for i in range(32):
            sig = s.sign(b'm%d' % i)
            used.append(struct.unpack('>I', sig[:4])[0])
            self.assertTrue(lms_verify(key.public_key(), b'm%d' % i, sig))
        self.assertEqual(used, list(range(32)))
        with self.assertRaises(RuntimeError):
            s.sign(b'one more')

    def test_S1_006_crash_injection_never_reuses_a_leaf(self):
        """S1-006 power loss at every step boundary, restart, continue: no q appears twice
        (a signature computed before a crash is counted as possibly leaked)."""
        key = LmsPrivate(5, 4, I=b'\x03' * 16, seed=b'\x04' * 32)
        nvm = NVM()
        signer = PersistentSigner(key, nvm)
        seen = []
        step = 0
        for crash_at in (None, 'before_reserve', 'after_counter', 'after_record', 'after_sign') * 5:
            try:
                sig = signer.sign(b'msg', crash_at=crash_at)
                seen.append(struct.unpack('>I', sig[:4])[0])
            except Crash:
                if crash_at in ('after_record', 'after_sign'):
                    seen.append(nvm.record['q'] - 1)          # that leaf is burned
                signer = PersistentSigner(key, nvm)            # reboot from NVM
            step += 1
        self.assertEqual(len(seen), len(set(seen)), f'leaf reuse: {seen}')
        self.assertEqual(seen, sorted(seen))

    def test_S1_007_rollback_detected_by_hardware_counter(self):
        """S1-007 restoring an older NVM record cannot reuse leaves (fails closed by skipping)."""
        key = LmsPrivate(5, 4, I=b'\x05' * 16, seed=b'\x06' * 32)
        nvm = NVM()
        s = PersistentSigner(key, nvm)
        s.sign(b'a'); s.sign(b'b')
        snap = nvm.snapshot()                         # attacker copies NVM after 2 signatures
        s.sign(b'c'); s.sign(b'd')
        nvm.restore(snap)                             # rollback (hw counter stays at 4)
        s2 = PersistentSigner(key, nvm)               # reboot: record.ctr=2 < hw=4 -> skip to q=4
        q = struct.unpack('>I', s2.sign(b'e')[:4])[0]
        self.assertEqual(q, 4)

    def test_S1_008_concurrent_signing_unique_leaves(self):
        """S1-008 16 threads signing concurrently reserve distinct leaves."""
        key = LmsPrivate(5, 4, I=b'\x08' * 16, seed=b'\x09' * 32)
        s = PersistentSigner(key, NVM())
        out, lock = [], threading.Lock()

        def worker():
            sig = s.sign(b'concurrent')
            with lock:
                out.append(struct.unpack('>I', sig[:4])[0])
        th = [threading.Thread(target=worker) for _ in range(16)]
        [t.start() for t in th]; [t.join() for t in th]
        self.assertEqual(len(set(out)), 16)

    def test_S1_009_clone_shows_why_export_is_forbidden(self):
        """S1-009 NEGATIVE DEMONSTRATION: two devices booted from one exported key state
        produce two signatures with the same q (OTS reuse) — the failure SP 800-208 §8.1
        prevents only by forbidding export. Untestable assumption A-NoExport."""
        key = LmsPrivate(5, 4, I=b'\x0a' * 16, seed=b'\x0b' * 32)
        a, b = PersistentSigner(key, NVM()), PersistentSigner(key, NVM())   # cloned
        qa = struct.unpack('>I', a.sign(b'x')[:4])[0]
        qb = struct.unpack('>I', b.sign(b'y')[:4])[0]
        self.assertEqual(qa, qb)          # the disaster, made visible

    def test_S1_010_attack_game_ledger(self):
        """S1-010 cheapest counting game is 2^(n/2) queries; n=24 fails QPT-128, n=32 passes."""
        g = cheapest_counting_game(attack_games(192, 20, 26, 8))
        self.assertEqual(g['quantum_queries_log2'], 96)
        self.assertFalse(qpt128_verdict(192)['passes'])
        self.assertEqual(qpt128_verdict(192)['margin_bits'], -14)
        self.assertTrue(qpt128_verdict(256)['passes'])
        self.assertEqual(qpt128_verdict(256)['margin_bits'], 18)

    def test_S1_011_grover_simulation_matches_law(self):
        """S1-011 exact Grover on the keyed chain oracle: measured optimum == closed form.

        The two per-seed assertions are exact and reproduce on every run.  The
        regression slope of log2(k) against n over one draw is not: the simulator draws
        its secret with secrets.randbelow(N), so the marked-set size M is random.  The
        slope is therefore asserted on the median over 41 independent draws.
        """
        rows = [grover_chain_inversion(n) for n in (8, 10, 12, 14)]
        for r in rows:
            self.assertLessEqual(abs(r['k_measured'] - r['k_predicted']), 1, r)   # floor() vs first peak
            self.assertAlmostEqual(r['p_at_k_pred'], r['p_predicted_at_k_pred'], places=9)

        def slope_of(rs):
            xs = [r['n'] for r in rs]; ys = [math.log2(r['k_measured']) for r in rs]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)

        slopes = sorted(slope_of([grover_chain_inversion(n) for n in (8, 10, 12, 14)]) for _ in range(41))
        self.assertAlmostEqual(slopes[len(slopes) // 2], 0.5, delta=0.06)


UNTESTABLE = [
    'A-NoExport: the private key state never leaves the hardware module (SP 800-208 §8.1); '
    'S1-009 shows the consequence if it does.',
    'A-Grover: 2^(n/2) queries is optimal for unstructured search (BBBV 1997 lower bound — a theorem '
    'in the query model); the >= 2^18 gates/query floor is an engineering assumption.',
    'A-SHA256: SHA-256 truncated to n bytes behaves as a random function for (second-)preimage; '
    'no structural attack better than generic is known.',
]


def report():
    out = {'independent_implementation': 'hsslms 0.1.3' if HAVE_HSSLMS else None,
           'sizes': {f'LMS_tc{l}/OTS_tc{o}': lms_sizes(l, o) for l, o in ((8, 4), (8, 3), (13, 8), (5, 4))},
           'attack_games_n256': attack_games(256, 20, 34, 8),
           'cheapest_game': cheapest_counting_game(attack_games(256, 20, 34, 8))['id'],
           'qpt128': [qpt128_verdict(n) for n in (128, 192, 256)],
           'grover_reduced': [grover_chain_inversion(n) for n in (8, 10, 12, 14)],
           'untestable_assumptions': UNTESTABLE}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--report', action='store_true')
    a = ap.parse_args(argv)
    if a.report:
        print(json.dumps(report(), indent=2)); return 0
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Tests),
                                unittest.defaultTestLoader.loadTestsFromTestCase(AuditFixTests)])
    r = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if r.wasSuccessful() else 1



class AuditFixTests(unittest.TestCase):
    def test_S1_012_mixed_typecodes_refused(self):
        """S1-012 (F3) non-approved m != n pairs are refused at keygen and at verify."""
        with self.assertRaises(ValueError):
            LmsPrivate(5, 8)                                 # M32_H5 with N24_W8
        with self.assertRaises(ValueError):
            LmsPrivate(10, 4)                                # M24_H5 with N32_W8
        k = LmsPrivate(5, 4)
        sig = k.sign(b'x')
        pk = bytearray(k.public_key()); pk[4:8] = (8).to_bytes(4, 'big')   # claim OTS type N24_W8
        self.assertFalse(lms_verify(bytes(pk), b'x', sig))
        self.assertTrue(approved_pair(8, 4) and approved_pair(13, 8) and not approved_pair(8, 8))

if __name__ == '__main__':
    sys.exit(main())
