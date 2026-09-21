# pq_infra_s1s2_hashsig_dnssec_v2.2.py — audit-fix release of v2.0 (2026-09-13): F2 (empty/extra-node multiproof
# accepted) and F4 (merkle_verify raised on malformed input). v2.0 is preserved immutably.
# S2-006 (2026-09-21): interior Merkle nodes are hashed with their position. v2.0 used H('node', l, r)
# for every node of every structure, so an adversary holding T signed structures tested one evaluation
# against all T targets: at n = 256 and T = 2^40 that is 2^108 quantum queries = 2^126 gates, inside the
# 2^128 budget. Binding each node to (structure id, level, parent index) puts each target in its own
# function, restoring 2^128 queries = 2^146 gates. Zero wire bytes: every prefix component is already
# known to the verifier (the public seed is half the public key; the rung, level and index come from the
# proof). Structure id is the ladder rung for MTL and the public seed for the XMSS-style tree.
#!/usr/bin/env python3
r"""PQ infrastructure program — steps S1 and S2, built from glued partial theories.

Blockers being attacked (from the global-deployment assessment), easiest first:

  S1  Firmware / secure boot.  The literature answer exists: stateful hash-based
      signatures (SP 800-208: LMS/HSS, XMSS/XMSS^MT). Verification is hashes
      only — no big-integer or polynomial arithmetic — so it fits a boot ROM.
      Here: a working WOTS+ / Merkle (XMSS-style) signer and verifier with exact
      byte and hash-count accounting, cross-checked against the RFC 8391 sizes.

  S2  DNSSEC.  The hard number is 1,232 bytes: the DNS Flag Day 2020 UDP buffer
      above which fragmentation starts dropping answers. A single ML-DSA-44
      RRSIG (2,420 B) already exceeds it. Two glued ideas:
        (a) Merkle Tree Ladder (MTL) mode [Fregly–Harvey–Kaliski–Sheth 2023]:
            sign a ladder of Merkle subtree roots once; each record carries a
            condensed signature = authentication path + rung reference; the
            verifier caches the signed ladder. Amortises the big signature over
            every record in the zone.
        (b) Compact category-5 signatures with SMALL public keys (SQIsign-V:
            292 B signature, ~129 B key), because DNSKEY responses carry keys.
      Here: a working MTL ladder (binary-counter subtree decomposition), the
      per-record condensed-signature size law, and a DNS wire-size model that
      classifies every candidate against 1,232 / 4,096 B for the three response
      types that matter: A, DNSKEY, and the NSEC3 NXDOMAIN (4 RRSIGs).

Theorems borrowed (stated, then tested):
  T1  Winternitz OTS + Merkle tree: EUF-CMA from second-preimage resistance of
      the hash, with signature size len*n + h*n and verify cost <= len*(w-1)+h
      hash calls (RFC 8391 §5; Buchmann–Dahmen–Hülsing 2011).
  T2  Ladder covering: the first N leaves of a Merkle sequence are covered by
      popcount(N) <= floor(log2 N)+1 perfect-subtree roots (the binary
      decomposition of N). Signing that ladder authenticates all N leaves; a
      leaf's condensed proof has at most floor(log2 N) nodes.  (MTL mode core.)
  T3  Amortisation: with one underlying signature of S bytes over a ladder for
      N records, the per-record signature cost is S/N + 32*floor(log2 N) + O(1),
      which is below any lattice signature for N >= ~16 and below 1,232 B for
      every N <= 2^38.

Everything below is tested (`--self-test`) and measured (`--report`). Toy
security: the underlying signature is a size parameter, not a real scheme; the
hash is SHAKE256. No claim is made beyond what the tests show.
"""

import argparse
import hashlib
import json
import math
import os
import sys
import unittest

# ============================================================ hash ======
N_BYTES = 32
_HASH_CALLS = 0


def H(*parts):
    """SHAKE256-256 over length-prefixed parts; counts calls for cost accounting."""
    global _HASH_CALLS
    _HASH_CALLS += 1
    h = hashlib.shake_256()
    for p in parts:
        h.update(len(p).to_bytes(4, 'big'))
        h.update(p)
    return h.digest(N_BYTES)


def hash_calls_reset():
    global _HASH_CALLS
    _HASH_CALLS = 0


def hash_calls():
    return _HASH_CALLS


# ================================================ S1: WOTS+ / Merkle =====
W = 16
LOG_W = 4
LEN1 = (8 * N_BYTES) // LOG_W                     # 64
LEN2 = math.floor(math.log2(LEN1 * (W - 1)) / LOG_W) + 1   # 3
LEN = LEN1 + LEN2                                   # 67


def _base_w(msg_digest):
    digits = []
    for b in msg_digest:
        digits.append(b >> 4)
        digits.append(b & 0xF)
    csum = sum(W - 1 - d for d in digits)
    csum <<= (8 - ((LEN2 * LOG_W) % 8)) % 8
    cbytes = csum.to_bytes((LEN2 * LOG_W + 7) // 8, 'big')
    cdig = []
    for b in cbytes:
        cdig.append(b >> 4)
        cdig.append(b & 0xF)
    return digits + cdig[:LEN2]


def _chain(x, start, steps, pubseed, addr, i):
    for s in range(start, start + steps):
        x = H(b'chain', pubseed, addr, i.to_bytes(2, 'big'), s.to_bytes(1, 'big'), x)
    return x


def wots_keygen(secret_seed, pubseed, addr):
    sk = [H(b'wots-sk', secret_seed, addr, i.to_bytes(2, 'big')) for i in range(LEN)]
    pk = [_chain(sk[i], 0, W - 1, pubseed, addr, i) for i in range(LEN)]
    return sk, pk


def wots_sign(msg_digest, sk, pubseed, addr):
    d = _base_w(msg_digest)
    return [_chain(sk[i], 0, d[i], pubseed, addr, i) for i in range(LEN)]


def wots_pk_from_sig(msg_digest, sig, pubseed, addr):
    d = _base_w(msg_digest)
    return [_chain(sig[i], d[i], W - 1 - d[i], pubseed, addr, i) for i in range(LEN)]


def wots_compress(pk, pubseed, addr):
    return H(b'wots-pk', pubseed, addr, *pk)


class MerkleSigner:
    """XMSS-style: 2^h one-time keys under one Merkle root. Stateful."""

    def __init__(self, height, secret_seed):
        self.h = height
        self.secret_seed = secret_seed
        self.pubseed = H(b'pubseed', secret_seed)
        self.n_leaves = 1 << height
        self.leaves = []
        for idx in range(self.n_leaves):
            addr = idx.to_bytes(4, 'big')
            _, pk = wots_keygen(secret_seed, self.pubseed, addr)
            self.leaves.append(wots_compress(pk, self.pubseed, addr))
        self.levels = [self.leaves]
        while len(self.levels[-1]) > 1:
            lvl, prev = len(self.levels) - 1, self.levels[-1]
            # S2-006: the node is bound to (public seed, level, parent index), the XMSS-T address
            # convention. Leaves already carry `addr`; without this the interior nodes did not.
            self.levels.append([H(b'node', self.pubseed, lvl.to_bytes(1, 'big'), (i // 2).to_bytes(4, 'big'),
                                  prev[i], prev[i + 1]) for i in range(0, len(prev), 2)])
        self.root = self.levels[-1][0]
        self.next_idx = 0

    def auth_path(self, idx):
        path = []
        for lvl in range(self.h):
            sib = idx ^ 1
            path.append(self.levels[lvl][sib])
            idx >>= 1
        return path

    def sign(self, msg):
        if self.next_idx >= self.n_leaves:
            raise RuntimeError('one-time keys exhausted: state must never be reused')
        idx = self.next_idx
        self.next_idx += 1                       # state advance BEFORE release
        addr = idx.to_bytes(4, 'big')
        sk, _ = wots_keygen(self.secret_seed, self.pubseed, addr)
        digest = H(b'msg', self.root, addr, msg)
        return {'idx': idx, 'ots': wots_sign(digest, sk, self.pubseed, addr),
                'auth': self.auth_path(idx)}

    @staticmethod
    def sig_bytes(height):
        return 4 + LEN * N_BYTES + height * N_BYTES

    @staticmethod
    def pk_bytes():
        return 2 * N_BYTES                          # root + pubseed


def merkle_verify(root, pubseed, height, msg, sig):
    try:                                   # F4: malformed objects return False, never raise
        return _merkle_verify_checked(root, pubseed, height, msg, sig)
    except (TypeError, KeyError, IndexError, ValueError, AttributeError):
        return False


def _merkle_verify_checked(root, pubseed, height, msg, sig):
    if type(sig) is not dict or type(msg) is not bytes:
        return False
    idx = sig['idx']
    if type(idx) is not int or type(idx) is bool:
        return False
    if not 0 <= idx < (1 << height) or len(sig['auth']) != height or len(sig['ots']) != LEN:
        return False
    if any(type(x) is not bytes or len(x) != N_BYTES for x in sig['ots']) or any(type(x) is not bytes or len(x) != N_BYTES for x in sig['auth']):
        return False
    addr = idx.to_bytes(4, 'big')
    digest = H(b'msg', root, addr, msg)
    node = wots_compress(wots_pk_from_sig(digest, sig['ots'], pubseed, addr), pubseed, addr)
    for lvl in range(height):
        sib = sig['auth'][lvl]
        left, right = (node, sib) if (idx >> lvl) & 1 == 0 else (sib, node)
        node = H(b'node', pubseed, lvl.to_bytes(1, 'big'), (idx >> (lvl + 1)).to_bytes(4, 'big'), left, right)
    return node == root


# ============================================== S2: MTL ladder mode =====
def ladder_rungs(n):
    """Binary-counter decomposition of the first n leaves into perfect subtrees.
    Returns [(start, size)], sizes descending, popcount(n) entries."""
    rungs, start, bit = [], 0, n.bit_length() - 1
    while bit >= 0:
        size = 1 << bit
        if n & size:
            rungs.append((start, size))
            start += size
        bit -= 1
    return rungs


class MTLLadder:
    """Sign the ladder once; issue condensed per-leaf proofs; verifier caches
    the signed ladder. The underlying signature is modelled by its byte size.
    S2-006: an interior node is hashed as H('node', rung, level, parent index,
    l, r). The three prefix fields cost nothing on the wire: the verifier reads
    the rung from the proof and derives level and index from the walk."""

    def __init__(self, leaf_digests, underlying_sig_bytes):
        self.n = len(leaf_digests)
        self.leaves = list(leaf_digests)
        self.underlying_sig_bytes = underlying_sig_bytes
        self.rungs = ladder_rungs(self.n)
        self.rung_roots, self.rung_levels = [], []
        for r, (start, size) in enumerate(self.rungs):
            levels = [self.leaves[start:start + size]]
            while len(levels[-1]) > 1:
                lvl, p = len(levels) - 1, levels[-1]
                levels.append([H(b'node', r.to_bytes(4, 'big'), lvl.to_bytes(1, 'big'), (i // 2).to_bytes(4, 'big'),
                                 p[i], p[i + 1]) for i in range(0, len(p), 2)])
            self.rung_levels.append(levels)
            self.rung_roots.append(levels[-1][0])
        # ONE underlying signature covers the whole ladder
        self.ladder_bytes = 4 + len(self.rungs) * (4 + N_BYTES) + underlying_sig_bytes

    def condensed(self, i):
        for r, (start, size) in enumerate(self.rungs):
            if start <= i < start + size:
                idx, path = i - start, []
                levels = self.rung_levels[r]
                for lvl in range(len(levels) - 1):
                    path.append(levels[lvl][idx ^ 1])
                    idx >>= 1
                return {'leaf': i, 'rung': r, 'path': path}
        raise IndexError(i)

    @staticmethod
    def condensed_bytes(proof):
        return 4 + 1 + len(proof['path']) * N_BYTES

    @staticmethod
    def verify(rung_roots, rungs, leaf_digest, proof):
        r = proof['rung']
        if not 0 <= r < len(rungs):
            return False
        start, size = rungs[r]
        idx = proof['leaf'] - start
        if not 0 <= idx < size or len(proof['path']) != size.bit_length() - 1:
            return False
        node = leaf_digest
        for lvl, sib in enumerate(proof['path']):
            left, right = (node, sib) if (idx >> lvl) & 1 == 0 else (sib, node)
            node = H(b'node', r.to_bytes(4, 'big'), lvl.to_bytes(1, 'big'), (idx >> (lvl + 1)).to_bytes(4, 'big'),
                     left, right)
        return node == rung_roots[r]


def mtl_amortised_bytes(n, underlying_sig_bytes):
    """Per-record cost: share of the one ladder signature + worst-case path."""
    ladder = 4 + bin(n).count('1') * (4 + N_BYTES) + underlying_sig_bytes
    worst_path = (n.bit_length() - 1) * N_BYTES + 5
    return ladder / n + worst_path


def multiproof_nodes(leaf_indices, depth):
    """Number of sibling nodes a Merkle multiproof needs for a set of leaves in
    one perfect subtree of the given depth (siblings that are themselves in the
    proven set, or derivable from it, are not transmitted)."""
    frontier = set(leaf_indices)
    total = 0
    for _ in range(depth):
        nxt = set()
        for i in frontier:
            if (i ^ 1) not in frontier:
                total += 1
            nxt.add(i >> 1)
        frontier = nxt
    return total


class MTLMultiproof:
    """Batched condensed signature for several leaves of the same ladder rung.
    S2-006: `build` copies nodes out of `ladder.rung_levels`, which are already
    position-prefixed, so only `verify` recomputes a hash and it uses the same
    (rung, level, parent index) prefix. The proof carries the rung and the leaf
    indices; level and parent index come from the walk, so nothing is added."""

    @staticmethod
    def build(ladder, leaf_indices):
        rung_of = {}
        for i in leaf_indices:
            for r, (start, size) in enumerate(ladder.rungs):
                if start <= i < start + size:
                    rung_of.setdefault(r, []).append(i - start)
        proof = {}
        for r, idxs in rung_of.items():
            levels = ladder.rung_levels[r]
            frontier, nodes = set(idxs), []
            for lvl in range(len(levels) - 1):
                nxt = set()
                for i in sorted(frontier):
                    if (i ^ 1) not in frontier:
                        nodes.append((lvl, i ^ 1, levels[lvl][i ^ 1]))
                    nxt.add(i >> 1)
                frontier = nxt
            proof[r] = {'leaves': sorted(idxs), 'nodes': nodes}
        return proof

    @staticmethod
    def nbytes(proof):
        return sum(4 + 1 + 4 * len(p['leaves']) + len(p['nodes']) * N_BYTES for p in proof.values())

    @staticmethod
    def verify(ladder_rung_roots, rungs, leaf_digests_by_index, proof, required=None):
        """F2 (audit stack v0.1): a proof must prove something — an empty proof, an
        unknown rung, a leaf out of range, a malformed node, a MISSING sibling or an
        EXTRA node not on any proven path all return False. `required`, when given,
        is the set of absolute leaf indices the caller needs covered; any uncovered
        index returns False. Never raises on malformed input (F4 class)."""
        try:
            if type(proof) is not dict or not proof:
                return False
            covered = set()
            for r, p in proof.items():
                if type(r) is not int or not 0 <= r < len(rungs) or type(p) is not dict:
                    return False
                start, size = rungs[r]
                depth = size.bit_length() - 1
                leaves = p.get('leaves')
                nodes = p.get('nodes')
                if type(leaves) not in (list, tuple) or not leaves or type(nodes) not in (list, tuple):
                    return False
                if any(type(i) is not int or not 0 <= i < size for i in leaves) or len(set(leaves)) != len(leaves):
                    return False
                supplied = {}
                for item in nodes:
                    if type(item) not in (tuple, list) or len(item) != 3:
                        return False
                    lvl, i, h = item
                    if type(lvl) is not int or type(i) is not int or type(h) is not bytes or len(h) != N_BYTES:
                        return False
                    if not 0 <= lvl < depth or not 0 <= i < (size >> lvl) or (lvl, i) in supplied:
                        return False
                    supplied[(lvl, i)] = h
                # the exact sibling set a proof of these leaves needs: no more, no less
                need, frontier = set(), set(leaves)
                for lvl in range(depth):
                    nxt = set()
                    for i in frontier:
                        if (i ^ 1) not in frontier:
                            need.add((lvl, i ^ 1))
                        nxt.add(i >> 1)
                    frontier = nxt
                if set(supplied) != need:
                    return False
                cur = {i: leaf_digests_by_index[start + i] for i in leaves}
                for lvl in range(depth):
                    nxt = {}
                    for i, h in cur.items():
                        sib = cur.get(i ^ 1)
                        if sib is None:
                            sib = supplied[(lvl, i ^ 1)]
                        left, right = (h, sib) if i & 1 == 0 else (sib, h)
                        nxt[i >> 1] = H(b'node', r.to_bytes(4, 'big'), lvl.to_bytes(1, 'big'),
                                        (i >> 1).to_bytes(4, 'big'), left, right)
                    cur = nxt
                if cur.get(0) != ladder_rung_roots[r]:
                    return False
                covered |= {start + i for i in leaves}
            if required is not None and not set(required) <= covered:
                return False
            return True
        except (TypeError, KeyError, IndexError, ValueError, AttributeError):
            return False


# ========================================== S2: DNSSEC wire model =======
# (signature bytes, public key bytes, NIST category, note)
SCHEMES = {
    'ECDSA-P256 (classical)': (64, 64, 0, 'baseline; broken by Shor'),
    'Ed25519 (classical)':    (64, 32, 0, 'baseline; broken by Shor'),
    'Falcon-512':             (666, 897, 1, 'FIPS 206 draft'),
    'Falcon-1024':            (1280, 1793, 5, 'FIPS 206 draft'),
    'ML-DSA-44':              (2420, 1312, 2, 'FIPS 204'),
    'ML-DSA-65':              (3309, 1952, 3, 'FIPS 204'),
    'ML-DSA-87':              (4627, 2592, 5, 'FIPS 204'),
    'SLH-DSA-128s':           (7856, 32, 1, 'FIPS 205'),
    'SLH-DSA-256s':           (29792, 64, 5, 'FIPS 205'),
    'SQIsign-I (rd2)':        (148, 65, 1, 'spec v2.0 2025-02-05 Table 1 (VERIFIED)'),
    'SQIsign-V (rd2)':        (292, 129, 5, 'spec v2.0 2025-02-05 Table 1 (VERIFIED); sign 507.5 / verify 35.7 Mcycles'),
    'SQIsign-V (v3.0 rd3)':   (406, 169, 5, 'sqisign.org v3.0 2026-09-01 (web page VERIFIED; spec not read)'),
    'MAYO-5':                 (964, 5554, 5, 'NIST additional rd2 (measured v1.44)'),
    'OV-V-pkc':               (260, 446992, 5, 'key cannot travel in DNS'),
    'XMSS-SHA256 h20 (S1)':   (2820, 64, 5, 'RFC 8391; stateful; n=32 -> 2^128 quantum preimage'),
}

UDP_SAFE = 1232          # DNS Flag Day 2020 (IPv6 min MTU 1280 - 48)
UDP_RFC9715 = 1400       # RFC 9715 §3.1 RECOMMENDED maximum DNS/UDP payload
EDNS_MAX = 4096          # common EDNS buffer ceiling; above -> TCP

# Müller et al., CCR 2020 Table 2: validation >= 1,000 signatures/s.
MULLER_MIN_VERIFY_PER_S = 1000
CPU_HZ = 3.4e9
VERIFY_MCYCLES = {'SQIsign-V (rd2)': 35.7, 'SQIsign-I (rd2)': 5.1}   # spec v2.0 Table 2, i7-13700K


def verify_rate_per_s(scheme):
    mc = VERIFY_MCYCLES.get(scheme)
    return None if mc is None else CPU_HZ / (mc * 1e6)

# Approximate wire overheads (bytes) excluding signatures and keys.
A_BASE = 12 + 24 + 16 + 45                # header, question, A RR, RRSIG shell
DNSKEY_BASE = 12 + 24 + 2 * 16 + 45       # two DNSKEY shells + one RRSIG shell
NXDOMAIN_BASE = 12 + 24 + 40 + 3 * 60 + 4 * 45   # SOA + 3 NSEC3 + 4 RRSIG shells
NXDOMAIN_SIGS = 4

# Denial-of-existence variants (how many RRSIGs an NXDOMAIN answer carries).
#   nsec3   : closest-encloser proof, SOA + 3 NSEC3            -> 4 RRSIGs (RFC 5155)
#   nsec    : SOA + apex NSEC (no-wildcard) + covering NSEC    -> 3 RRSIGs (RFC 4035)
#   compact : RFC 9824 compact denial, SOA + one synthesized
#             NSEC, signed ONLINE                              -> 2 RRSIGs
DOE_VARIANTS = {
    'nsec3':   {'sigs': 4, 'base': 12 + 24 + 40 + 3 * 60 + 4 * 45, 'online': False},
    'nsec':    {'sigs': 3, 'base': 12 + 24 + 40 + 2 * 60 + 3 * 45, 'online': False},
    'compact': {'sigs': 2, 'base': 12 + 24 + 40 + 1 * 60 + 2 * 45, 'online': True},
}


def dns_sizes(sig, pk, dnskey_sigs=1):
    return {
        'A':        A_BASE + sig,
        'DNSKEY':   DNSKEY_BASE + 2 * pk + dnskey_sigs * sig,
        'NXDOMAIN': NXDOMAIN_BASE + NXDOMAIN_SIGS * sig,
    }


def doe_sizes(sig):
    return {k: v['base'] + v['sigs'] * sig for k, v in DOE_VARIANTS.items()}


def max_sig_for_udp(variant):
    v = DOE_VARIANTS[variant]
    return (UDP_SAFE - v['base']) // v['sigs']


def synthetic_zone_leaves(n_names):
    """Canonical-order RRset leaves of a synthetic zone: apex RRsets first
    (NS=2, SOA=6, NSEC=47, DNSKEY=48 in type order), then one A + one NSEC
    per delegated name in canonical name order. Returns (leaf_digests, index)."""
    leaves, index = [], {}
    for t in ('NS', 'SOA', 'NSEC', 'DNSKEY'):
        index[('@', t)] = len(leaves)
        leaves.append(H(b'rr', b'@', t.encode()))
    for k in range(n_names):
        name = b'n%08d' % k
        for t in ('A', 'NSEC'):
            index[(name, t)] = len(leaves)
            leaves.append(H(b'rr', name, t.encode()))
    return leaves, index


def sharded_zone_answer(n_names_total, shard_log2, variant='nsec', sample=48):
    """Glue for large zones: split the canonical-order leaf sequence into shards
    of 2^shard_log2 leaves, each with its OWN signed ladder (the underlying
    signature is paid once per shard per re-sign, fetched once per shard per
    TTL by a resolver). Answer size then depends on the shard, not the zone.
    Returns worst-case answer bytes over sampled NXDOMAINs in one shard, plus
    the number of shards a zone of n_names_total names has.
    Note: apex RRsets (SOA, apex NSEC) live in shard 0; a denial for a name in
    shard j therefore needs proofs from shard 0 AND shard j (two ladders)."""
    n_names_shard = (1 << shard_log2) // 2
    leaves, index = synthetic_zone_leaves(n_names_shard - 2)
    lad = MTLLadder(leaves, underlying_sig_bytes=0)
    apex = [index[('@', 'SOA')], index[('@', 'NSEC')]]
    worst = 0
    for s in range(sample):
        q = int.from_bytes(H(b'shard', s.to_bytes(4, 'big'))[:4], 'big') % (n_names_shard - 2)
        cover = index[(b'n%08d' % q, 'NSEC')]
        p_apex = MTLMultiproof.build(lad, apex)              # from shard 0's ladder
        p_cover = MTLMultiproof.build(lad, [cover])          # from shard j's ladder
        worst = max(worst, MTLMultiproof.nbytes(p_apex) + MTLMultiproof.nbytes(p_cover) + 8)
    base = DOE_VARIANTS[variant]['base']
    n_shards = -(-(2 * n_names_total + 4) // (1 << shard_log2))
    return {'shard_leaves': 1 << shard_log2, 'shards': n_shards,
            'answer_worst': base + worst, 'answer_class': classify(base + worst)}


def nxdomain_multiproof_bytes(ladder, index, n_names, variant, sample=64, seed=b'nx'):
    """Measured batched-proof bytes for the RRSIG set of one NXDOMAIN answer
    when the ladder leaves are in canonical zone order."""
    sizes = []
    for s in range(sample):
        q = int.from_bytes(H(seed, s.to_bytes(4, 'big'))[:4], 'big') % n_names
        cover = index[(b'n%08d' % q, 'NSEC')]
        if variant == 'nsec3':
            # three NSEC3 owners are hash-random: model as random leaves
            others = [index[(b'n%08d' % (int.from_bytes(H(seed, b'h', s.to_bytes(4, 'big'), j.to_bytes(1, 'big'))[:4], 'big') % n_names), 'NSEC')]
                      for j in range(3)]
            leaves = [index[('@', 'SOA')]] + others
        elif variant == 'nsec':
            leaves = [index[('@', 'SOA')], index[('@', 'NSEC')], cover]
        else:
            raise ValueError('compact denial is online-signed; it has no precomputed leaves')
        proof = MTLMultiproof.build(ladder, leaves)
        sizes.append(MTLMultiproof.nbytes(proof))
    return {'min': min(sizes), 'max': max(sizes), 'mean': round(sum(sizes) / len(sizes), 1)}


def classify(nbytes):
    if nbytes <= UDP_SAFE:
        return 'UDP-safe'
    if nbytes <= UDP_RFC9715:
        return 'UDP-safe (RFC 9715 1400)'
    if nbytes <= EDNS_MAX:
        return 'EDNS-only (fragmentation risk)'
    return 'TCP fallback'


def dnssec_table(mtl_zone_records=(1 << 12, 1 << 16, 1 << 20)):
    rows = []
    for name, (sig, pk, cat, note) in SCHEMES.items():
        s = dns_sizes(sig, pk)
        row = {'scheme': name, 'category': cat, 'sig': sig, 'pk': pk,
               'A': s['A'], 'DNSKEY': s['DNSKEY'], 'NXDOMAIN': s['NXDOMAIN'],
               'A_class': classify(s['A']), 'DNSKEY_class': classify(s['DNSKEY']),
               'NXDOMAIN_class': classify(s['NXDOMAIN']),
               'all_udp_safe': all(v <= UDP_SAFE for v in s.values()), 'note': note}
        # MTL mode: RRSIG carries a condensed proof; the ladder+full signature
        # is fetched once per zone (modelled as its own response).
        row['mtl'] = {}
        for n in mtl_zone_records:
            cond = 5 + (n.bit_length() - 1) * N_BYTES
            ladder_resp = 12 + 24 + 45 + 4 + bin(n).count('1') * 36 + sig
            m = {'condensed_sig': cond, 'A': A_BASE + cond,
                 'NXDOMAIN': NXDOMAIN_BASE + NXDOMAIN_SIGS * cond,
                 'ladder_response': ladder_resp, 'DNSKEY': DNSKEY_BASE + 2 * pk + cond}
            m['records_udp_safe'] = m['A'] <= UDP_SAFE and m['NXDOMAIN'] <= UDP_SAFE
            m['ladder_class'] = classify(ladder_resp)
            row['mtl'][str(n)] = m
        rows.append(row)
    return rows


# ================================================================ tests ==
class Tests(unittest.TestCase):
    def test_s1_wots_roundtrip_and_tamper(self):
        seed, pubseed, addr = b'seed' * 8, H(b'ps'), b'\x00\x00\x00\x07'
        sk, pk = wots_keygen(seed, pubseed, addr)
        d = H(b'a message')
        sig = wots_sign(d, sk, pubseed, addr)
        self.assertEqual(wots_pk_from_sig(d, sig, pubseed, addr), pk)
        self.assertNotEqual(wots_pk_from_sig(H(b'other'), sig, pubseed, addr), pk)
        bad = list(sig)
        bad[3] = H(b'x')
        self.assertNotEqual(wots_pk_from_sig(d, bad, pubseed, addr), pk)

    def test_s1_merkle_sign_verify_sizes_and_cost(self):
        h = 4
        signer = MerkleSigner(h, b'\x01' * 32)
        msgs = [b'fw-%d' % i for i in range(1 << h)]
        for m in msgs:
            sig = signer.sign(m)
            hash_calls_reset()
            self.assertTrue(merkle_verify(signer.root, signer.pubseed, h, m, sig))
            self.assertLessEqual(hash_calls(), LEN * (W - 1) + h + 3)        # T1 bound
            self.assertFalse(merkle_verify(signer.root, signer.pubseed, h, m + b'!', sig))
        with self.assertRaises(RuntimeError):
            signer.sign(b'one too many')                                     # statefulness
        # RFC 8391 XMSS-SHA256 h=20: 2,820 B (= 4 + 32 + 67*32 + 20*32). Ours omits
        # the 32-byte randomiser r; everything else matches exactly.
        self.assertEqual(MerkleSigner.sig_bytes(20) + N_BYTES, 2820)
        self.assertEqual(LEN, 67)

    def test_s2_ladder_rungs_are_binary_decomposition(self):
        for n in (1, 2, 3, 7, 8, 100, 1000, 65536, 65537):
            rungs = ladder_rungs(n)
            self.assertEqual(sum(s for _, s in rungs), n)
            self.assertEqual(len(rungs), bin(n).count('1'))                  # T2
            self.assertLessEqual(len(rungs), n.bit_length())
            self.assertEqual([s for _, s in rungs], sorted((s for _, s in rungs), reverse=True))

    def test_s2_mtl_every_leaf_verifies_and_tamper_fails(self):
        n = 1000
        leaves = [H(b'rr-%d' % i) for i in range(n)]
        lad = MTLLadder(leaves, underlying_sig_bytes=4627)
        for i in range(n):
            p = lad.condensed(i)
            self.assertTrue(MTLLadder.verify(lad.rung_roots, lad.rungs, leaves[i], p))
            self.assertLessEqual(len(p['path']), n.bit_length() - 1)         # T2
        p = lad.condensed(17)
        self.assertFalse(MTLLadder.verify(lad.rung_roots, lad.rungs, H(b'forged'), p))
        p['path'][0] = H(b'bad')
        self.assertFalse(MTLLadder.verify(lad.rung_roots, lad.rungs, leaves[17], p))

    def test_s2_amortisation_law(self):
        # T3: per-record cost falls below every lattice signature quickly and
        # stays under the UDP ceiling for any realistic zone.
        for sig in (2420, 4627, 29792):
            self.assertLess(mtl_amortised_bytes(16, sig), sig)
            for n in (1 << 12, 1 << 20, 1 << 30, 1 << 38):
                self.assertLess(mtl_amortised_bytes(n, sig), UDP_SAFE)
        self.assertLess(mtl_amortised_bytes(1 << 20, 29792), 700)

    def test_s2_dnssec_classification(self):
        rows = {r['scheme']: r for r in dnssec_table()}
        self.assertFalse(rows['ML-DSA-44']['all_udp_safe'])       # the premise's problem
        self.assertEqual(rows['ML-DSA-44']['A_class'], 'EDNS-only (fragmentation risk)')
        self.assertFalse(rows['Falcon-512']['all_udp_safe'])      # DNSKEY/NXDOMAIN blow it
        self.assertTrue(rows['Ed25519 (classical)']['all_udp_safe'])
        # FALSIFIED HYPOTHESIS (first run): "a compact Cat-5 signature fits every
        # response".  SQIsign-V fits A and DNSKEY but the NSEC3 NXDOMAIN answer
        # carries 4 RRSIGs -> 1,604 B.  Recorded, not hidden:
        sq = rows['SQIsign-V (rd2)']
        self.assertEqual(sq['A_class'], 'UDP-safe')
        self.assertEqual(sq['DNSKEY_class'], 'UDP-safe')
        self.assertEqual(sq['NXDOMAIN_class'], 'EDNS-only (fragmentation risk)')
        self.assertFalse(sq['all_udp_safe'])
        # FALSIFIED HYPOTHESIS 2: "MTL alone rescues NXDOMAIN". Condensed proofs
        # at 2^20 leaves are 645 B each; four of them exceed the UDP ceiling.
        self.assertFalse(rows['SLH-DSA-256s']['mtl']['1048576']['records_udp_safe'])
        self.assertEqual(rows['SLH-DSA-256s']['mtl']['1048576']['ladder_class'], 'TCP fallback')

    def test_s2_denial_variant_signature_budget(self):
        # The binding constraint is the RRSIG count in the denial answer.
        self.assertEqual(max_sig_for_udp('nsec3'), 199)     # no Cat-5 scheme
        self.assertGreaterEqual(max_sig_for_udp('nsec'), 292)   # SQIsign-V fits
        self.assertGreaterEqual(max_sig_for_udp('compact'), 292)
        self.assertLess(max_sig_for_udp('nsec'), 666)       # Falcon-512 does not
        d = doe_sizes(292)
        self.assertLessEqual(d['nsec'], UDP_SAFE)
        self.assertLessEqual(d['compact'], UDP_SAFE)
        self.assertGreater(d['nsec3'], UDP_SAFE)

    def test_s2_sqisign_v3_and_verify_rate(self):
        # Updated sizes (v3.0): NSEC denial no longer fits even RFC 9715's 1400.
        d = doe_sizes(406)
        self.assertGreater(d['nsec'], UDP_RFC9715)
        self.assertLessEqual(d['compact'], UDP_SAFE)          # 1,038 B, online-signed
        # Müller requirement: >= 1,000 verifications/s. SQIsign-V: ~95/s/core.
        self.assertLess(verify_rate_per_s('SQIsign-V (rd2)'), MULLER_MIN_VERIFY_PER_S)
        self.assertLess(verify_rate_per_s('SQIsign-I (rd2)'), MULLER_MIN_VERIFY_PER_S)

    def test_s2_sharded_ladder_answer_independent_of_zone_size(self):
        small = sharded_zone_answer(1 << 12, shard_log2=12)
        big = sharded_zone_answer(160_000_000, shard_log2=12)       # .com-scale
        self.assertEqual(small['answer_worst'], big['answer_worst'])
        self.assertLessEqual(big['answer_worst'], UDP_SAFE)
        self.assertGreater(big['shards'], 70_000)
        self.assertLessEqual(sharded_zone_answer(160_000_000, shard_log2=14)['answer_worst'], UDP_RFC9715)

    def test_s2_multiproof_correct_and_smaller(self):
        n_names = 2000
        leaves, index = synthetic_zone_leaves(n_names)
        lad = MTLLadder(leaves, underlying_sig_bytes=4627)
        sel = [index[('@', 'SOA')], index[('@', 'NSEC')], index[(b'n%08d' % 1234, 'NSEC')]]
        proof = MTLMultiproof.build(lad, sel)
        self.assertTrue(MTLMultiproof.verify(lad.rung_roots, lad.rungs, leaves, proof))
        # tamper: wrong leaf content
        bad = list(leaves)
        bad[sel[2]] = H(b'forged')
        self.assertFalse(MTLMultiproof.verify(lad.rung_roots, lad.rungs, bad, proof))
        # strictly smaller than three separate condensed signatures
        separate = sum(MTLLadder.condensed_bytes(lad.condensed(i)) for i in sel)
        self.assertLess(MTLMultiproof.nbytes(proof), separate)
        # counting law matches the built proof
        r0 = proof[0]
        depth = lad.rungs[0][1].bit_length() - 1
        self.assertEqual(len(r0['nodes']), multiproof_nodes(r0['leaves'], depth))


# =============================================================== report ==
def _multiproof_measurements():
    out = {}
    for n_names in (1 << 10, 1 << 14):
        leaves, index = synthetic_zone_leaves(n_names)
        lad = MTLLadder(leaves, underlying_sig_bytes=4627)
        row = {'leaves': len(leaves)}
        for variant in ('nsec3', 'nsec'):
            m = nxdomain_multiproof_bytes(lad, index, n_names, variant, sample=48)
            base = DOE_VARIANTS[variant]['base']
            m['answer_max'] = base + m['max']
            m['answer_class_max'] = classify(base + m['max'])
            m['separate_condensed'] = DOE_VARIANTS[variant]['sigs'] * (5 + (len(leaves).bit_length() - 1) * N_BYTES)
            row[variant] = m
        out[str(n_names)] = row
    return out


def report():
    signer = MerkleSigner(4, b'\x02' * 32)
    sig = signer.sign(b'firmware-image-v1')
    hash_calls_reset()
    ok = merkle_verify(signer.root, signer.pubseed, 4, b'firmware-image-v1', sig)
    verify_hashes = hash_calls()
    out = {
        'S1_firmware_hash_based': {
            'construction': 'WOTS+ (w=16, len=67) under XMSS-style Merkle tree',
            'verified': ok,
            'verify_hash_calls_measured_h4': verify_hashes,
            'verify_hash_calls_bound_T1': LEN * (W - 1) + 4,
            'signature_bytes': {f'h={h}': MerkleSigner.sig_bytes(h) + N_BYTES for h in (10, 16, 20)},
            'rfc8391_xmss_sha256_h20_bytes': 2820,
            'public_key_bytes': MerkleSigner.pk_bytes(),
            'boot_rom_fit': 'verification uses only hash calls and ~2.9 KB of signature; '
                            'no big-int, no polynomial arithmetic, state on the SIGNER only',
            'category': 'SP 800-208 class; security from hash second-preimage resistance',
        },
        'S2_dnssec': {
            'udp_safe_bytes': UDP_SAFE, 'edns_max_bytes': EDNS_MAX,
            'nxdomain_rrsigs': NXDOMAIN_SIGS,
            'max_signature_bytes_for_udp_by_denial_variant': {k: max_sig_for_udp(k) for k in DOE_VARIANTS},
            'denial_sizes_sqisign_v_v2': doe_sizes(292),
            'denial_sizes_sqisign_v_v3': doe_sizes(406),
            'denial_sizes_falcon512': doe_sizes(666),
            'verify_per_s': {k: round(verify_rate_per_s(k)) for k in VERIFY_MCYCLES},
            'muller_min_verify_per_s': MULLER_MIN_VERIFY_PER_S,
            'sharded_ladder': {f'shard_2^{s}': sharded_zone_answer(160_000_000, s) for s in (10, 12, 14, 16)},
            'mtl_multiproof_nxdomain_bytes': _multiproof_measurements(),
            'table': dnssec_table(),
            'mtl_amortised_per_record_bytes': {
                sig_name: {str(n): round(mtl_amortised_bytes(n, SCHEMES[sig_name][0]), 1)
                           for n in (16, 1 << 10, 1 << 16, 1 << 20)}
                for sig_name in ('ML-DSA-44', 'ML-DSA-87', 'SLH-DSA-256s')},
        },
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--report', action='store_true')
    a = ap.parse_args(argv)
    if a.report:
        print(json.dumps(report(), indent=2))
        return 0
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Tests),
                                unittest.defaultTestLoader.loadTestsFromTestCase(AuditFixTests),
                                unittest.defaultTestLoader.loadTestsFromTestCase(PositionPrefixTests)])
    r = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if r.wasSuccessful() else 1



# ============================================================ v2.2 regressions
class AuditFixTests(unittest.TestCase):
    """F2 / F4 regressions (audit stack v0.1, property layer H2/H3)."""

    def setUp(self):
        self.leaves = [H(b'fx', i.to_bytes(2, 'big')) for i in range(300)]
        self.lad = MTLLadder(self.leaves, 0)

    def test_f2_empty_proof_rejected(self):
        self.assertFalse(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, {}))
        self.assertFalse(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, None))
        self.assertFalse(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, {0: {'leaves': [], 'nodes': []}}))

    def test_f2_extra_and_missing_nodes_rejected(self):
        p = MTLMultiproof.build(self.lad, [1, 2, 200])
        self.assertTrue(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, p))
        import copy
        extra = copy.deepcopy(p); extra[0]['nodes'].append((0, 7, self.leaves[7]))
        self.assertFalse(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, extra))
        missing = copy.deepcopy(p); missing[0]['nodes'].pop()
        self.assertFalse(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, missing))
        dup = copy.deepcopy(p); dup[0]['nodes'].append(dup[0]['nodes'][0])
        self.assertFalse(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, dup))

    def test_f2_required_coverage(self):
        p = MTLMultiproof.build(self.lad, [5])
        self.assertTrue(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, p, required={5}))
        self.assertFalse(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, p, required={5, 6}))

    def test_f2_malformed_returns_false_never_raises(self):
        for bad in ({99: {'leaves': [0], 'nodes': []}}, {0: {'leaves': [10 ** 9], 'nodes': []}},
                    {0: {'leaves': [1], 'nodes': [('x',)]}}, {0: {'leaves': [1], 'nodes': [(0, 0, b'short')]}},
                    {0: {'leaves': [1, 1], 'nodes': []}}, {'0': {'leaves': [1], 'nodes': []}}, 7, [], b''):
            self.assertFalse(MTLMultiproof.verify(self.lad.rung_roots, self.lad.rungs, self.leaves, bad))

    def test_f4_merkle_verify_malformed_returns_false(self):
        signer = MerkleSigner(3, b'\x05' * 32)
        sig = signer.sign(b'm')
        self.assertTrue(merkle_verify(signer.root, signer.pubseed, 3, b'm', sig))
        for bad in ({}, None, {'idx': 1.0, 'ots': sig['ots'], 'auth': sig['auth']},
                    {'idx': '1', 'ots': sig['ots'], 'auth': sig['auth']}, {'idx': 1, 'ots': [1] * LEN, 'auth': sig['auth']},
                    {'idx': True, 'ots': sig['ots'], 'auth': sig['auth']}):
            self.assertFalse(merkle_verify(signer.root, signer.pubseed, 3, b'm', bad))
        self.assertFalse(merkle_verify(signer.root, signer.pubseed, 3, 'm', sig))


# ====================================================== S2-006 regressions
def _unprefixed_levels(leaves):
    """The v2.0 node hash, kept in the test section only so the regressions can
    show what the position prefix now rejects: every interior node of every
    structure was H('node', l, r), one function holding all T targets."""
    levels = [list(leaves)]
    while len(levels[-1]) > 1:
        p = levels[-1]
        levels.append([H(b'node', p[i], p[i + 1]) for i in range(0, len(p), 2)])
    return levels


def _unprefixed_root(leaf_digest, idx, path):
    node = leaf_digest
    for lvl, sib in enumerate(path):
        node = H(b'node', node, sib) if (idx >> lvl) & 1 == 0 else H(b'node', sib, node)
    return node


class PositionPrefixTests(unittest.TestCase):
    """S2-006 / failed-assumption A4: interior nodes carry (structure id, level,
    parent index). Each of these fails against the v2.0 hashing."""

    def test_s2_006_node_hash_binds_rung_level_and_index(self):
        a, b = H(b'pa'), H(b'pb')
        lad = MTLLadder([a, b] * 3, 0)                        # n = 6 -> rungs (0,4),(4,2)
        self.assertEqual(lad.rungs, [(0, 4), (4, 2)])
        z4, z1 = b'\x00\x00\x00\x00', b'\x00'
        want = H(b'node', z4, z1, z4, a, b)
        self.assertEqual(lad.rung_levels[0][1][0], want)
        # same children, different index -> different node
        self.assertEqual(lad.rung_levels[0][1][1], H(b'node', z4, z1, b'\x00\x00\x00\x01', a, b))
        self.assertNotEqual(lad.rung_levels[0][1][0], lad.rung_levels[0][1][1])
        # same children, same level and index, different rung -> different node
        self.assertEqual(lad.rung_levels[1][1][0], H(b'node', b'\x00\x00\x00\x01', z1, z4, a, b))
        self.assertNotEqual(lad.rung_levels[0][1][0], lad.rung_levels[1][1][0])
        # dropping any one prefix field, or all three (the v2.0 shape), changes the node
        for dropped in (H(b'node', a, b), H(b'node', z1, z4, a, b),
                        H(b'node', z4, z4, a, b), H(b'node', z4, z1, a, b)):
            self.assertNotEqual(want, dropped)

    def test_s2_006_condensed_proof_does_not_transplant_to_another_position(self):
        leaves = [H(b'pa'), H(b'pb')] * 8            # repeated blocks: every subtree repeats
        lad = MTLLadder(leaves, 0)
        self.assertEqual(lad.rungs, [(0, 16)])
        p0 = lad.condensed(0)
        self.assertTrue(MTLLadder.verify(lad.rung_roots, lad.rungs, leaves[0], p0))
        self.assertFalse(MTLLadder.verify(lad.rung_roots, lad.rungs, leaves[2], dict(p0, leaf=2)))
        self.assertFalse(MTLLadder.verify(lad.rung_roots, lad.rungs, leaves[4], dict(p0, leaf=4)))
        # under v2.0 the move was free: the repeated subtrees are the same bytes, so
        # leaf 0's path reaches the same root from leaf 2 and from leaf 4.
        old, path, idx = _unprefixed_levels(leaves), [], 0
        for lvl in range(4):
            path.append(old[lvl][idx ^ 1])
            idx >>= 1
        for j in (0, 2, 4):
            self.assertEqual(_unprefixed_root(leaves[j], j, path), old[-1][0])

    def test_s2_006_multiproof_rejects_unprefixed_nodes(self):
        leaves = [H(b'pz', i.to_bytes(2, 'big')) for i in range(64)]
        lad = MTLLadder(leaves, 0)
        good = MTLMultiproof.build(lad, [5, 17])
        self.assertTrue(MTLMultiproof.verify(lad.rung_roots, lad.rungs, leaves, good))
        old = _unprefixed_levels(leaves)
        stale = {0: {'leaves': good[0]['leaves'],
                     'nodes': [(lvl, i, old[lvl][i]) for lvl, i, _ in good[0]['nodes']]}}
        self.assertNotEqual(stale[0]['nodes'], good[0]['nodes'])      # levels >= 1 differ
        self.assertFalse(MTLMultiproof.verify(lad.rung_roots, lad.rungs, leaves, stale))
        # nor against the root of the wholly unprefixed structure the nodes came from
        self.assertFalse(MTLMultiproof.verify([old[-1][0]], lad.rungs, leaves, stale))

    def test_s1_006_merkle_nodes_bind_public_seed_level_and_index(self):
        signer = MerkleSigner(3, b'\x07' * 32)
        lv, z4, z1 = signer.levels, b'\x00\x00\x00\x00', b'\x00'
        self.assertEqual(lv[1][0], H(b'node', signer.pubseed, z1, z4, lv[0][0], lv[0][1]))
        self.assertEqual(lv[1][1], H(b'node', signer.pubseed, z1, b'\x00\x00\x00\x01', lv[0][2], lv[0][3]))
        self.assertEqual(lv[2][0], H(b'node', signer.pubseed, b'\x01', z4, lv[1][0], lv[1][1]))
        # the WOTS+ address binds the leaves only; before this the interior nodes of
        # every key pair shared one function. The public seed now separates them.
        other = MerkleSigner(2, b'\x08' * 32)
        self.assertNotEqual(lv[1][0], H(b'node', other.pubseed, z1, z4, lv[0][0], lv[0][1]))
        self.assertNotEqual(signer.root, _unprefixed_levels(lv[0])[-1][0])
        sig = signer.sign(b'fw')
        self.assertTrue(merkle_verify(signer.root, signer.pubseed, 3, b'fw', sig))
        self.assertFalse(merkle_verify(signer.root, other.pubseed, 3, b'fw', sig))

if __name__ == '__main__':
    sys.exit(main())
