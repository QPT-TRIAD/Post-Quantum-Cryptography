#!/usr/bin/env python3
r"""PQ infrastructure program — step S5: smart cards, secure elements, HSMs, payment.

Blocker as usually stated: "PQ signatures don't fit a card" (2-8 KB RAM, ISO 7816
APDUs of 256 B, decades in the field, must SIGN not just verify).

Glued observation: SP 800-208 §8.1 requires that stateful hash-based keys live in a
hardware module that (a) never exports the private key, (b) increments and commits
the leaf index to non-volatile storage before releasing a signature, (c) is FIPS
140-3 Level 3+.  That is a description of a smart card / secure element.  The
"state problem" that makes LMS/XMSS unsuitable for general software is a
non-problem on a device that already has a tamper-resistant monotonic counter and
cannot be cloned or restored from backup.  So the card-side answer at Category 5
is: LMS (n=32, w=8, h=20) signed ON the card, with the authentication path
produced by the BDS traversal algorithm in bounded memory.

Theorems borrowed and tested:
  T1  BDS [Buchmann–Dahmen–Schneider 2008]: with parameter k, the auth path of
      every leaf 0..2^h-1 can be produced in order using at most (h-k)/2 leaf
      computations per signature and O(h^2)-bounded state. Verified here by an
      exhaustive comparison against naive auth paths for every leaf.
  T2  Per-signature work = WOTS sign (len chains, avg (w-1)/2 steps) + BDS
      leaf computations x (len·(w-1)) hashes. Measured, not estimated.
  T3  pqm4 (benchmarks.md, commit 90bfb63, 2025-05-22) shows lattice signing also
      fits small RAM: ML-DSA-44 m4fstack stack 5,080 B sign / 2,712 B verify,
      ML-DSA-65 6,616 / 2,712 B. Category 5 (ML-DSA-87) is not in that table;
      only the hash-based route below is measured here at Category 5.

Transport: ISO 7816-4 short APDU carries ≤256 B per response; extended APDUs up
to 65,535 B. Sizes vs the classical EMV RSA-1984 (248 B) are tabulated.

S2-006 (2026-09-21): interior Merkle nodes carry their position. v2.0 hashed every
interior node of every card as H('node', l, r), one function holding the nodes of
all T fielded devices, so an adversary tests one evaluation against all T targets at
once: at n = 256 and T = 2^40 that is 2^108 quantum queries = 2^126 gates, inside the
2^128 budget the card claims. Binding each node to (public seed, level, parent index)
— the XMSS-T address convention, and what RFC 8554's (I, r) does for LMS — puts each
target in its own function and restores 2^128 queries = 2^146 gates. The card's public
seed is half its public key and the leaf index already travels in the signature, so the
1,772-B signature and every APDU count below are unchanged.
"""

import argparse
import importlib.util
import json
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fn))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


s4 = _load('s4', 's4_embedded_broadcast.py')
s1s2 = s4.s1s2            # SAME module instance as the WOTS code, so hash_calls() sees every hash
H, N = s1s2.H, s1s2.N_BYTES


# ------------------------------------------------------------- BDS ---------
class _Treehash:
    __slots__ = ('i', 'next_idx', 'node', 'completed', 'stack')

    def __init__(self, i):
        self.i, self.next_idx, self.node, self.completed, self.stack = i, None, None, True, []

    def restart(self, start):
        self.next_idx, self.node, self.completed, self.stack = start, None, False, []

    def low(self):
        if self.completed:
            return 1 << 30
        return min((h for _, h in self.stack), default=self.i)


class BDS:
    """Bounded-memory Merkle authentication-path traversal (BDS 2008), as in the
    RFC 8391 reference implementation's bds_round / bds_treehash_update.
    S2-006: every interior node is hashed H('node', pubseed, level of the two
    children, index of the parent, l, r). The traversal reaches the same node by
    three different routes — the key-generation stack, the round that rebuilds
    auth[tau] from auth[tau-1] and keep[tau-1], and a treehash update — and all
    three must derive the same (level, index) from the state they already track,
    or verification stops matching construction. Both are tracked: the keygen
    stack carries (node, height, index), the round knows tau and s, and a
    treehash node's index follows from the last leaf it consumed."""

    def __init__(self, leaf_fn, h, k, pubseed):
        assert (h - k) % 2 == 0 and k >= 2
        self.leaf_fn, self.h, self.k, self.pubseed = leaf_fn, h, k, pubseed
        self.leaf_calls = 0
        self.auth = [None] * h
        self.keep = [None] * (h // 2 + 1)
        self.treehash = [_Treehash(i) for i in range(h - k)]
        self.retain = {i: {} for i in range(h - k, h)}
        self.s = 0
        self.root = self._keygen()

    def _leaf(self, idx):
        self.leaf_calls += 1
        return self.leaf_fn(idx)

    def _keygen(self):
        stack = []                                  # (node, height, index)
        for idx in range(1 << self.h):
            node, hgt, j = self._leaf(idx), 0, idx
            self._capture(node, hgt, j)
            while stack and stack[-1][1] == hgt:
                left = stack.pop()
                # the two children sit at level hgt with indices j-1 and j, so the parent
                # is index j >> 1; the tuple's right side still holds the pre-merge values
                node, hgt, j = H(b'node', self.pubseed, hgt.to_bytes(1, 'big'), (j >> 1).to_bytes(4, 'big'),
                                 left[0], node), hgt + 1, j >> 1
                self._capture(node, hgt, j)
            stack.append((node, hgt, j))
        return stack[0][0]

    def _capture(self, node, i, j):
        if i >= self.h:
            return
        if j == 1:
            self.auth[i] = node
        elif j == 3 and i < self.h - self.k:
            self.treehash[i].node = node
        elif i >= self.h - self.k and j & 1 and j >= 3:
            self.retain[i][j] = node

    def auth_path(self):
        """Auth path for the current leaf index (list of h nodes)."""
        return list(self.auth)

    def advance(self):
        """Move from leaf s to s+1, updating the state (BDS round)."""
        s, h, k = self.s, self.h, self.k
        if s + 1 >= (1 << h):
            self.s += 1
            return
        tau = 0
        while (s >> tau) & 1:
            tau += 1
        if tau > 0:
            left, right = self.auth[tau - 1], self.keep[(tau - 1) >> 1]
        if not ((s >> (tau + 1)) & 1) and tau < h - 1:
            self.keep[tau >> 1] = self.auth[tau]
        if tau == 0:
            self.auth[0] = self._leaf(s)
        else:
            # auth[tau] for leaf s+1 is the node at level tau with index ((s+1) >> tau) ^ 1,
            # built from two level-(tau-1) children
            self.auth[tau] = H(b'node', self.pubseed, (tau - 1).to_bytes(1, 'big'),
                               (((s + 1) >> tau) ^ 1).to_bytes(4, 'big'), left, right)
            for i in range(tau):
                if i < h - k:
                    self.auth[i] = self.treehash[i].node
                else:
                    j = ((s + 1) >> i) + 1
                    self.auth[i] = self.retain[i].pop(j)
            for i in range(min(tau, h - k)):
                start = s + 1 + 3 * (1 << i)
                if start < (1 << h):
                    self.treehash[i].restart(start)
        for _ in range((h - k) // 2):
            cands = [t for t in self.treehash if not t.completed]
            if not cands:
                break
            t = min(cands, key=lambda t: (t.low(), t.i))
            self._treehash_update(t)
        self.s += 1

    def _treehash_update(self, t):
        leaf_idx = t.next_idx
        node, hgt = self._leaf(leaf_idx), 0
        while t.stack and t.stack[-1][1] == hgt:
            left, _ = t.stack.pop()
            # a completed subtree ends at the leaf just consumed, so the node stands at
            # index leaf_idx >> hgt and its parent at leaf_idx >> (hgt + 1)
            node, hgt = H(b'node', self.pubseed, hgt.to_bytes(1, 'big'),
                          (leaf_idx >> (hgt + 1)).to_bytes(4, 'big'), left, node), hgt + 1
        if hgt == t.i:
            t.node, t.completed = node, True
        else:
            t.stack.append((node, hgt))
        t.next_idx += 1

    def state_bytes(self):
        n = N
        auth = self.h * n
        keep = len(self.keep) * n
        th = len(self.treehash) * (n + 8)
        stacks = sum(len(t.stack) for t in self.treehash) * (n + 1)
        retain = sum(len(v) for v in self.retain.values()) * n
        return {'auth': auth, 'keep': keep, 'treehash_nodes': th, 'stacks_now': stacks,
                'retain': retain, 'index': 8, 'total': auth + keep + th + stacks + retain + 8}


def naive_auth_paths(leaves, pubseed):
    """Independent recomputation of every auth path; the S2-006 prefix here has to
    agree with all three BDS routes, which is what the h=2..12 comparison tests."""
    levels = [list(leaves)]
    while len(levels[-1]) > 1:
        lvl, p = len(levels) - 1, levels[-1]
        levels.append([H(b'node', pubseed, lvl.to_bytes(1, 'big'), (i // 2).to_bytes(4, 'big'),
                         p[i], p[i + 1]) for i in range(0, len(p), 2)])
    out = []
    for idx in range(len(leaves)):
        path, j = [], idx
        for lvl in range(len(levels) - 1):
            path.append(levels[lvl][j ^ 1])
            j >>= 1
        out.append(path)
    return out, levels[-1][0]


# --------------------------------------------------- card signer model -----
class CardSigner:
    """LMS-style signer with WOTS w=256 leaves and BDS traversal; the index is
    committed (here: attribute) BEFORE the signature is released."""

    def __init__(self, h, k, w=256, seed=b'card'):
        self.w = s4.WOTS(w)
        self.h = h
        self.ps = H(b'ps', seed)
        self.seed = seed
        self.bds = BDS(self._leaf, h, k, self.ps)
        self.root = self.bds.root
        self.committed_index = 0

    def _leaf(self, idx):
        _, pk = self.w.keygen(self.seed, self.ps, idx.to_bytes(4, 'big'))
        return pk

    def sign(self, msg):
        idx = self.committed_index
        if idx >= (1 << self.h):
            raise RuntimeError('exhausted')
        self.committed_index += 1                       # NVM commit before release
        addr = idx.to_bytes(4, 'big')
        # derive only the OTS secret (34 hashes); the public chains are not needed to sign
        sk = [H(b'sk', self.seed, addr, i.to_bytes(2, 'big')) for i in range(self.w.len)]
        d = H(b'msg', self.root, addr, msg)
        ots = self.w.sign(d, sk, self.ps, addr)
        path = self.bds.auth_path()
        self.bds.advance()
        return {'idx': idx, 'ots': ots, 'path': path}

    def verify(self, msg, sig):
        idx = sig['idx']
        addr = idx.to_bytes(4, 'big')
        d = H(b'msg', self.root, addr, msg)
        node = self.w.pk_from_sig(d, sig['ots'], self.ps, addr)
        for lvl, sib in enumerate(sig['path']):
            left, right = (node, sib) if (idx >> lvl) & 1 == 0 else (sib, node)
            node = H(b'node', self.ps, lvl.to_bytes(1, 'big'), (idx >> (lvl + 1)).to_bytes(4, 'big'),
                     left, right)
        return node == self.root


# ------------------------------------------------- verified literature -----
# Card RAM: NXP SmartMX3 P71D3xx fact sheet (2025): 12 KB; Infineon SLE 78CLX
# product brief: 8 KB.  Memory figures below are KiB of RAM/stack.
CARD_RAM_KB = {'Infineon SLE 78CLX': 8, 'NXP SmartMX3 P71': 12}
LITERATURE_RAM_KIB = {
    # Bos–Renes–Sprenkels, ePrint 2022/323 Table 2 (STM32F407 @24 MHz, C):
    'Dilithium5 keygen/sign/verify (2022/323)': (7.9, 8.1, 2.7),
    'Dilithium3 keygen/sign/verify (2022/323)': (6.4, 6.5, 2.7),
    # Kampanakis et al., ePrint 2021/041 Table 2 (verifier only, stack KB):
    'LMS256H20W8 verify stack (2021/041)': (None, None, 1.81),
    'SPX256H20w256 verify stack (2021/041)': (None, None, 4.25),
    # Botros–Kannwischer–Schwabe 2019/489 Table 3 (bytes -> KiB):
    'Kyber-1024 keygen/encaps/decaps (2019/489)': (4160 / 1024, 3752 / 1024, 3776 / 1024),
}
LITERATURE_CYCLES = {
    'Dilithium5 sign kcycles @24MHz (2022/323)': 44332,      # ~1.85 s at 24 MHz
    'LMS256H20W8 verify Mcycles x86 (2021/041)': 2.857,
}
DEPLOYED_HBS_SECURE_BOOT = {   # vendor, scheme, year, source type
    'Cisco trust anchors (LDWM/LMS, work since 2013; 8100/Cat9500/FW4215)': 2024,
    'Infineon OPTIGA TPM SLB 9672 XMSS-signed firmware update': 2022,
    'Microchip MEC175xB LMS verification, CNSA 2.0': 2025,
    'AMD Versal Gen 2 LMS secure boot (WP566)': 2025,
    'Lattice MachXO5-NX TDQ ML-DSA/LMS/XMSS bitstream auth': 2025,
    'OpenTitan Earl Grey ROM: ECDSA-P256 + SLH-DSA hybrid': 2024,
}


# ------------------------------------------------------------ APDU model ----
APDU_SHORT = 256
APDU_EXTENDED = 65535
SIGS = {'EMV RSA-1984 (classical)': 248, 'ECDSA P-256': 64,
        'LMS n32 w8 h20 (this step)': 1772, 'ML-DSA-44 (Cat 2)': 2420,
        'ML-DSA-87 (Cat 5)': 4627, 'SQIsign-V (Cat 5)': 292, 'XMSS-SHA2_20_256': 2820}


def apdu_table():
    return {k: {'bytes': v, 'short_apdu_chunks': -(-v // APDU_SHORT), 'fits_one_extended_apdu': v <= APDU_EXTENDED}
            for k, v in SIGS.items()}


# ----------------------------------------------------------------- tests ----
class Tests(unittest.TestCase):
    def test_t1_bds_matches_naive_for_every_leaf(self):
        ps = H(b'ps', b'card')
        for h, k in ((6, 2), (8, 2), (8, 4)):
            leaves = [H(b'leaf', h.to_bytes(1, 'big'), i.to_bytes(4, 'big')) for i in range(1 << h)]
            calls = [0]

            def leaf_fn(i, leaves=leaves, calls=calls):
                calls[0] += 1
                return leaves[i]
            bds = BDS(leaf_fn, h, k, ps)
            paths, root = naive_auth_paths(leaves, ps)
            self.assertEqual(bds.root, root)
            after_keygen = calls[0]
            self.assertEqual(after_keygen, 1 << h)
            max_state = 0
            for s in range(1 << h):
                self.assertEqual(bds.auth_path(), paths[s], f'h={h} k={k} leaf {s}')
                before = calls[0]
                bds.advance()
                self.assertLessEqual(calls[0] - before, (h - k) // 2 + 1)      # T1 bound (+1: tau==0 leaf)
                max_state = max(max_state, bds.state_bytes()['total'])
            self.assertLess(max_state, 2048)                                      # fits card NVM comfortably

    def test_t2_card_signer_roundtrip_and_cost(self):
        card = CardSigner(h=6, k=2)
        s1s2.hash_calls_reset()
        base_leaf_calls = card.bds.leaf_calls
        sigs = []
        for i in range(1 << 6):
            sigs.append(card.sign(b'txn-%02d' % i))
        hashes = s1s2.hash_calls()
        per_sig = hashes / 64
        leaf_per_sig = (card.bds.leaf_calls - base_leaf_calls) / 64
        self.assertLessEqual(leaf_per_sig, (6 - 2) / 2 + 1)
        # WOTS w=256 sign avg 34*127.5 ~ 4.3k + <= 3 leaf computations (8,670 hashes each)
        self.assertGreater(per_sig, 4_000)          # counter must see the WOTS chains (aliasing bug guard)
        self.assertLess(per_sig, 40_000)
        for i, s in enumerate(sigs):
            self.assertTrue(card.verify(b'txn-%02d' % i, s))
        self.assertFalse(card.verify(b'txn-00', sigs[1]))
        with self.assertRaises(RuntimeError):
            card.sign(b'one more')                              # 65th signature refused
        self.assertEqual(card.committed_index, 64)

    def test_t3_literature_fit(self):
        d5 = LITERATURE_RAM_KIB['Dilithium5 keygen/sign/verify (2022/323)']
        self.assertLessEqual(d5[1], CARD_RAM_KB['NXP SmartMX3 P71'])       # Cat-5 lattice signing fits 12 KB
        self.assertGreater(d5[1], CARD_RAM_KB['Infineon SLE 78CLX'])       # but not 8 KB (8.1 KiB)
        self.assertLess(LITERATURE_RAM_KIB['LMS256H20W8 verify stack (2021/041)'][2], 2)
        self.assertGreaterEqual(len(DEPLOYED_HBS_SECURE_BOOT), 5)

    def test_apdu(self):
        t = apdu_table()
        self.assertEqual(t['LMS n32 w8 h20 (this step)']['short_apdu_chunks'], 7)
        self.assertEqual(t['ML-DSA-87 (Cat 5)']['short_apdu_chunks'], 19)
        self.assertTrue(all(v['fits_one_extended_apdu'] for v in t.values()))


# ====================================================== S2-006 regressions
def _unprefixed_levels(leaves):
    """The v2.0 node hash, kept in the test section only so the regressions can show
    what the position prefix now rejects: every interior node of every card was
    H('node', l, r), one function holding all T targets."""
    levels = [list(leaves)]
    while len(levels[-1]) > 1:
        p = levels[-1]
        levels.append([H(b'node', p[i], p[i + 1]) for i in range(0, len(p), 2)])
    return levels


class PositionPrefixTests(unittest.TestCase):
    """S2-006 on the card tree: an interior node carries (public seed, level,
    parent index). Each of these fails against the v2.0 hashing."""

    def test_s5_006_node_hash_binds_seed_level_and_index(self):
        ps = H(b'ps', b'bind')
        a, b = H(b'la'), H(b'lb')
        leaves = [a, b] * 8                                   # h = 4; every subtree repeats
        bds = BDS(lambda i: leaves[i], 4, 2, ps)
        paths, root = naive_auth_paths(leaves, ps)
        self.assertEqual(bds.root, root)                      # keygen, treehash and round agree
        z4, z1 = b'\x00\x00\x00\x00', b'\x00'
        n0 = H(b'node', ps, z1, z4, a, b)                     # children at level 0 -> parent (1, 0)
        n1 = H(b'node', ps, z1, b'\x00\x00\x00\x01', a, b)    # same children, parent (1, 1)
        self.assertNotEqual(n0, n1)
        self.assertEqual(bds.auth_path()[1], n1)              # leaf 0's level-1 sibling is (1, 1)
        self.assertEqual(bds.auth_path()[2], H(b'node', ps, b'\x01', b'\x00\x00\x00\x01',
                                               H(b'node', ps, z1, b'\x00\x00\x00\x02', a, b),
                                               H(b'node', ps, z1, b'\x00\x00\x00\x03', a, b)))
        # dropping any one prefix field, or all three (the v2.0 shape), changes the node
        for dropped in (H(b'node', a, b), H(b'node', z1, z4, a, b),
                        H(b'node', ps, z4, a, b), H(b'node', ps, z1, a, b)):
            self.assertNotEqual(n0, dropped)
        # another device with the same leaf bytes no longer shares the interior nodes
        other = H(b'ps', b'other-card')
        self.assertNotEqual(bds.root, naive_auth_paths(leaves, other)[1])
        self.assertNotEqual(bds.root, _unprefixed_levels(leaves)[-1][0])

    def test_s5_006_auth_path_does_not_transplant_to_another_leaf(self):
        ps = H(b'ps', b'transplant')
        leaves = [H(b'la'), H(b'lb')] * 8
        paths, _ = naive_auth_paths(leaves, ps)
        for j in (2, 4, 6):                                   # identical child bytes, other positions
            self.assertNotEqual(paths[0], paths[j])
        # under v2.0 the move was free: the repeated subtrees are the same bytes, so
        # leaf 0's path reaches the same root from leaves 2, 4 and 6 as well.
        old, path, idx = _unprefixed_levels(leaves), [], 0
        for lvl in range(4):
            path.append(old[lvl][idx ^ 1])
            idx >>= 1
        for j in (0, 2, 4, 6):
            node, idx = leaves[j], j
            for lvl, sib in enumerate(path):
                node = H(b'node', node, sib) if (idx >> lvl) & 1 == 0 else H(b'node', sib, node)
            self.assertEqual(node, old[-1][0])

    def test_s5_006_card_signer_verifies_against_the_prefixed_tree(self):
        card = CardSigner(h=4, k=2, w=16, seed=b'card-prefix')
        leaves = [card._leaf(i) for i in range(16)]
        self.assertEqual(card.root, naive_auth_paths(leaves, card.ps)[1])
        self.assertNotEqual(card.root, _unprefixed_levels(leaves)[-1][0])
        for i in range(16):
            sig = card.sign(b'txn-%d' % i)
            self.assertTrue(card.verify(b'txn-%d' % i, sig))
            moved = dict(sig, idx=(i + 1) % 16)               # same path at another position
            self.assertFalse(card.verify(b'txn-%d' % i, moved))


def report():
    card = CardSigner(h=8, k=2)
    s1s2.hash_calls_reset()
    lc0 = card.bds.leaf_calls
    for i in range(256):
        card.sign(b'txn-%03d' % i)
    hashes = s1s2.hash_calls()
    lc = card.bds.leaf_calls - lc0
    per_leaf = card.w.len * (card.w.w - 1)
    return {
        'bds_h8_k2': {'hashes_per_signature_measured': round(hashes / 256, 1),
                      'leaf_computations_per_signature': round(lc / 256, 2),
                      'state_bytes_end': card.bds.state_bytes()},
        'projection_h20_k2': {'leaf_computations_per_signature_max': (20 - 2) // 2,
                              'hashes_per_signature_max': (20 - 2) // 2 * per_leaf + card.w.len * 255 + 20,
                              'note': '~1 us/hash on a secure element with HW SHA-256 -> ~85 ms; assumption, not measured'},
        'apdu': apdu_table(),
        'card_ram_kb': CARD_RAM_KB, 'literature_ram_kib': LITERATURE_RAM_KIB,
        'literature_cycles': LITERATURE_CYCLES, 'deployed_hbs_secure_boot': DEPLOYED_HBS_SECURE_BOOT,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--report', action='store_true')
    a = ap.parse_args(argv)
    if a.report:
        print(json.dumps(report(), indent=2)); return 0
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Tests),
                                unittest.defaultTestLoader.loadTestsFromTestCase(PositionPrefixTests)])
    r = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if r.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
