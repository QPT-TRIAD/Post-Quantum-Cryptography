#!/usr/bin/env python3
r"""Audit S2 — DNSSEC under the MTL-ladder / canonical-order multiproof / sharded
design of pq_infra_s1s2_hashsig_dnssec_v2.0.py.

Four audit columns:
  (1) Spec conformance: responses are encoded with a REAL DNS wire encoder
      (dnspython 2.8.0, RFC 1035 name compression, RFC 4034/4035 RRSIG/NSEC/
      DNSKEY rdata, RFC 5155 NSEC3, EDNS OPT), not the byte model's constants.
  (2) Reproduce the numbers: the model's "worst NXDOMAIN 1,129 B at shard 2^12"
      is re-measured exactly, and the difference is reported.
  (3) Adversary: an automated WORST-CASE SEARCH (random + hill climbing) over
      zone parameters — name/label lengths, depth, DNSKEY count, rollover
      double-signing, CNAME chains, wildcard denial, type-bitmap windows,
      denial variant — for every response type that carries signatures; plus
      proof-manipulation games on the multiproof (remove a leaf, reorder nodes,
      substitute a node from another branch, different leaf statement,
      different-set/same-proof binding at reduced hash size) with an
      INDEPENDENT validator written top-down instead of bottom-up.
  (4) Bound: the multiproof's security is exactly second-preimage resistance of
      the node hash (MM-SPR in the MTL paper, Thm 2); measured binding at n =
      8..14 bits follows 2^-n.

Protocol decision made explicit here (the model left it implicit): a response
that carries k RRSIGs from one shard carries ONE multiproof in the first RRSIG
(MTL-Type 2) and a 5-byte batch reference in the others (MTL-Type 3).
"""

import argparse
import base64
import importlib.util
import json
import math
import os
import random
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
import dns.message, dns.name, dns.rrset, dns.rdata, dns.rdatatype, dns.rdataclass, dns.rcode, dns.flags  # noqa: E402

_spec = importlib.util.spec_from_file_location('s1s2', os.path.join(_HERE, 's1s2_hashsig_dnssec-v2.0.py'))
s1s2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s1s2)
H, N32 = s1s2.H, s1s2.N_BYTES

UDP_SAFE, UDP_RFC9715 = s1s2.UDP_SAFE, s1s2.UDP_RFC9715
ALG = 18          # IANA: ML-DSA-44 code point, used here as the placeholder algorithm number


# ------------------------------------------------------------ zone model ----
class Zone:
    """Synthetic signed zone in canonical order with an MTL ladder per shard."""

    def __init__(self, p, rng):
        self.p = p
        apex = 'a' * p['apex_len'] + '.'
        self.apex = dns.name.from_text(apex)
        lab = lambda i, k: (chr(ord('a') + (i + k) % 26) * p['label_len'])
        names = []
        for i in range(p['n_names']):
            labels = [lab(i, k) for k in range(p['n_labels'])]
            labels[0] = f'n{i:05d}' + labels[0][:max(0, p['label_len'] - 6)]
            names.append(dns.name.from_text('.'.join(labels) + '.' + apex))
        self.names = sorted(names)                      # dnspython sorts canonically
        types_per_name = ['A', 'NSEC'] + (['TXT'] * p['extra_types'])
        self.rrsets = [(self.apex, t) for t in ('NS', 'SOA', 'NSEC', 'DNSKEY')]
        # the wildcard RRsets are always present in the ladder so that both the
        # wildcard-synthesized answer and the wildcard denial can be encoded
        self.rrsets.append((dns.name.from_text('*.' + apex), 'A'))
        self.rrsets.append((dns.name.from_text('*.' + apex), 'NSEC'))
        for nm in self.names:
            for t in types_per_name:
                self.rrsets.append((nm, t))
        self.index = {k: i for i, k in enumerate(self.rrsets)}
        self.leaves = [H(b'rr', str(n).encode(), t.encode()) for n, t in self.rrsets]
        self.shard_log2 = p['shard_log2']
        S = 1 << self.shard_log2
        self.shards = [s1s2.MTLLadder(self.leaves[i:i + S], 0) for i in range(0, len(self.leaves), S)]

    def shard_of(self, idx):
        return idx >> self.shard_log2, idx & ((1 << self.shard_log2) - 1)

    def proofs_for(self, keys):
        """Batched multiproofs, one per shard touched; returns bytes per shard."""
        by_shard = {}
        for k in keys:
            s, local = self.shard_of(self.index[k])
            by_shard.setdefault(s, []).append(local)
        out = {}
        for s, locals_ in by_shard.items():
            out[s] = s1s2.MTLMultiproof.nbytes(s1s2.MTLMultiproof.build(self.shards[s], locals_))
        return out


# --------------------------------------------------------- wire encoder -----
def _rdata(rtype, text):
    return dns.rdata.from_text(dns.rdataclass.IN, getattr(dns.rdatatype, rtype), text)


def rrsig(owner, ttl, covered, labels, signer, sigbytes):
    b = base64.b64encode(sigbytes).decode()
    rd = _rdata('RRSIG', f'{covered} {ALG} {labels} {ttl} 20260101000000 20250101000000 12345 {signer} {b}')
    return dns.rrset.from_rdata(owner, ttl, rd)


def nsec(owner, ttl, nxt, windows):
    types = 'A RRSIG NSEC'
    if windows >= 2:
        types += ' TYPE65280'
    if windows >= 3:
        types += ' TYPE32768'
    return dns.rrset.from_rdata(owner, ttl, _rdata('NSEC', f'{nxt} {types}'))


def soa(owner, ttl, mname, rname):
    return dns.rrset.from_rdata(owner, ttl, _rdata('SOA', f'{mname} {rname} 2026091101 7200 3600 1209600 {ttl}'))


def dnskey(owner, ttl, keybytes, flags=257):
    return dns.rrset.from_rdata(owner, ttl, _rdata('DNSKEY', f'{flags} 3 {ALG} {base64.b64encode(keybytes).decode()}'))


def nsec3(zone, ttl, i, windows):
    owner = dns.name.from_text(base64.b32encode(H(b'h', i.to_bytes(2, 'big'))[:20]).decode().lower().rstrip('=') + '.' + str(zone))
    nxt = base64.b32encode(H(b'h', (i + 1).to_bytes(2, 'big'))[:20]).decode().rstrip('=')
    types = 'A RRSIG' + (' TYPE65280' if windows >= 2 else '') + (' TYPE32768' if windows >= 3 else '')
    return dns.rrset.from_rdata(owner, ttl, _rdata('NSEC3', f'1 0 0 - {nxt} {types}'))


class Encoder:
    """Builds real responses; the RRSIG signature field carries the proof."""

    def __init__(self, zone: Zone, p):
        self.z, self.p = zone, p
        self.ttl = p['ttl']
        self.signer = str(zone.apex)
        self.keys = [H(b'key', k.to_bytes(1, 'big')) * (p['key_bytes'] // 32) for k in range(p['n_keys'])]

    def _sig_fields(self, rrset_keys):
        """Signature bytes for each RRSIG in canonical order of the RRsets in the
        response: first RRSIG per shard carries MTL-Type 2 + multiproof, the rest
        carry MTL-Type 3 + 4-byte leaf index. With `rollover` each RRset carries
        n_sigs RRSIGs (one per active key)."""
        if self.p['protocol'] == 'per_rrsig':
            out = []
            for k in rrset_keys:
                s, local = self.z.shard_of(self.z.index[k])
                cond = self.z.shards[s].condensed(local)
                out.append(b'\x01' + b'\x00' * s1s2.MTLLadder.condensed_bytes(cond))
            return out
        proofs = self.z.proofs_for(rrset_keys)
        seen, out = set(), []
        for k in rrset_keys:
            s, local = self.z.shard_of(self.z.index[k])
            if s not in seen:
                seen.add(s)
                out.append(b'\x02' + b'\x00' * proofs[s])
            else:
                out.append(b'\x03' + local.to_bytes(4, 'big'))
        return out

    def _finish(self, resp, sections):
        """sections: list of (section, rrset, rrset_key_for_proof or None)."""
        keys = [k for _, _, k in sections if k is not None]
        sigs = self._sig_fields(keys)
        it = iter(sigs)
        for sec, rr, k in sections:
            getattr(resp, sec).append(rr)
            if k is not None:
                for j in range(self.p['n_sigs']):
                    sb = next(it) if j == 0 else (b'\x03' + b'\x00' * 4)
                    labels = len(rr.name) - 1
                    getattr(resp, sec).append(rrsig(rr.name, self.ttl, dns.rdatatype.to_text(rr.rdtype), labels, self.signer, sb))
        resp.use_edns(0, payload=1232)
        wire = resp.to_wire(max_size=65535)
        return wire

    def _base(self, qname, qtype, rcode=dns.rcode.NOERROR):
        q = dns.message.make_query(qname, qtype, use_edns=0, want_dnssec=True)
        r = dns.message.make_response(q)
        r.flags |= dns.flags.AA
        r.set_rcode(rcode)
        return r

    def nxdomain(self, i):
        z, p = self.z, self.p
        target = z.names[i]
        qname = dns.name.from_text('zz.' + str(target))       # a nonexistent child of an existing name
        r = self._base(qname, 'A', dns.rcode.NXDOMAIN)
        mname = dns.name.from_text('m' * p['label_len'] + '.' + str(z.apex))
        secs = [('authority', soa(z.apex, self.ttl, mname, mname), (z.apex, 'SOA'))]
        if p['denial'] == 'nsec':
            nxt = z.names[i + 1] if i + 1 < len(z.names) else z.apex
            secs.append(('authority', nsec(target, self.ttl, nxt, p['bitmap_windows']), (target, 'NSEC')))
            # wildcard denial: apex NSEC covers *.apex
            secs.append(('authority', nsec(z.apex, self.ttl, z.names[0], p['bitmap_windows']), (z.apex, 'NSEC')))
        elif p['denial'] == 'compact':
            secs.append(('authority', nsec(qname, self.ttl, dns.name.from_text('\\000.' + str(qname)), 1), (target, 'NSEC')))
        else:  # nsec3: closest encloser, next closer, wildcard
            for j in range(3):
                secs.append(('authority', nsec3(z.apex, self.ttl, 3 * i + j, p['bitmap_windows']), (z.names[(i + j) % len(z.names)], 'NSEC')))
        return self._finish(r, secs)

    def dnskey(self):
        z = self.z
        r = self._base(z.apex, 'DNSKEY')
        rr = dns.rrset.from_rdata_list(z.apex, self.ttl, [_rdata('DNSKEY', f'257 3 {ALG} {base64.b64encode(k).decode()}') for k in self.keys])
        return self._finish(r, [('answer', rr, (z.apex, 'DNSKEY'))])

    def cname_chain(self, k):
        z = self.z
        r = self._base(z.names[0], 'A')
        secs = []
        for j in range(k):
            rr = dns.rrset.from_rdata(z.names[j], self.ttl, _rdata('CNAME', str(z.names[j + 1])))
            secs.append(('answer', rr, (z.names[j], 'A')))
        rr = dns.rrset.from_rdata(z.names[k], self.ttl, _rdata('A', '192.0.2.1'))
        secs.append(('answer', rr, (z.names[k], 'A')))
        return self._finish(r, secs)

    def wildcard_answer(self, i):
        z, p = self.z, self.p
        qname = dns.name.from_text('w' * p['label_len'] + '.' + str(z.apex))
        r = self._base(qname, 'A')
        wc = dns.name.from_text('*.' + str(z.apex))
        secs = [('answer', dns.rrset.from_rdata(qname, self.ttl, _rdata('A', '192.0.2.2')), (wc, 'A')),
                ('authority', nsec(z.names[i], self.ttl, z.names[i + 1] if i + 1 < len(z.names) else z.apex, p['bitmap_windows']), (z.names[i], 'NSEC'))]
        return self._finish(r, secs)

    def a_answer(self, i):
        z = self.z
        r = self._base(z.names[i], 'A')
        return self._finish(r, [('answer', dns.rrset.from_rdata(z.names[i], self.ttl, _rdata('A', '192.0.2.3')), (z.names[i], 'A'))])


# ------------------------------------------------------- parameter search ---
SPACE = {
    'n_names': [16, 64, 256, 1024, 2000], 'label_len': [1, 8, 20, 40, 63], 'n_labels': [1, 2, 3, 4],
    'apex_len': [3, 10, 30, 60], 'ttl': [60, 3600, 86400], 'n_keys': [1, 2, 3], 'key_bytes': [32, 64],
    'n_sigs': [1, 2], 'extra_types': [0, 1, 2], 'wildcard': [False, True], 'bitmap_windows': [1, 2, 3],
    'denial': ['nsec', 'compact', 'nsec3'], 'protocol': ['batched', 'per_rrsig'], 'shard_log2': [10, 12, 14],
    'cname_len': [0, 1, 4, 8], 'realistic': [True],
}
REALISTIC_CAP = {'label_len': 20, 'n_labels': 3, 'apex_len': 30, 'bitmap_windows': 2, 'cname_len': 4, 'extra_types': 1}


def legal(p):
    total = p['n_labels'] * (p['label_len'] + 1) + p['apex_len'] + 2      # wire name length
    if total + 3 > 255 or p['n_names'] < 10:                              # +3: the 'zz' query label
        return False
    if p['cname_len'] >= p['n_names']:
        return False
    return True


def response_sizes(p, rng):
    z = Zone(p, rng)
    e = Encoder(z, p)
    i = rng.randrange(0, min(p['n_names'], 1 << p['shard_log2']) - 1)
    return {'NXDOMAIN': len(e.nxdomain(i)), 'DNSKEY': len(e.dnskey()), 'A': len(e.a_answer(i)),
            'WILDCARD': len(e.wildcard_answer(i)), 'CNAME': len(e.cname_chain(p['cname_len']))}


def search(objective, samples=400, climb=150, seed=1, realistic=False, fixed=None):
    rng = random.Random(seed)

    def draw():
        while True:
            p = {k: rng.choice(v) for k, v in SPACE.items()}
            if realistic:
                for k, cap in REALISTIC_CAP.items():
                    p[k] = min(p[k], cap)
            if fixed:
                p.update(fixed)
            if legal(p):
                return p
    best, best_v = None, -1
    for _ in range(samples):
        p = draw()
        v = response_sizes(p, rng)[objective]
        if v > best_v:
            best, best_v = p, v
    for _ in range(climb):
        q = dict(best)
        k = rng.choice(list(SPACE))
        q[k] = rng.choice(SPACE[k])
        if realistic and k in REALISTIC_CAP:
            q[k] = min(q[k], REALISTIC_CAP[k])
        if fixed:
            q.update(fixed)
        if not legal(q):
            continue
        v = response_sizes(q, rng)[objective]
        if v > best_v:
            best, best_v = q, v
    return best_v, best


# ------------------------------------------- multiproof games / validator ---
def independent_multiproof_verify(rung_roots, rungs, leaf_digests_by_index, proof):
    """Top-down recomputation: for each rung, build the set of node positions
    that must be derivable, then evaluate recursively from the root down."""
    for r, p in proof.items():
        start, size = rungs[r]
        depth = size.bit_length() - 1
        leaves = {i: leaf_digests_by_index[start + i] for i in p['leaves']}
        supplied = {(lvl, i): h for lvl, i, h in p['nodes']}

        def node(lvl, i):
            if lvl == 0:
                return leaves.get(i) or supplied.get((0, i))
            if (lvl, i) in supplied:
                return supplied[(lvl, i)]
            l, rr = node(lvl - 1, 2 * i), node(lvl - 1, 2 * i + 1)
            if l is None or rr is None:
                return None
            return H(b'node', l, rr)
        # every supplied node must be a sibling of something on a proven path
        need = set()
        for i in p['leaves']:
            x = i
            for lvl in range(depth):
                need.add((lvl, x ^ 1)); x >>= 1
        if any(k not in need for k in supplied):
            return False
        if node(depth, 0) != rung_roots[r]:
            return False
    return True


def _Hn(n_bits):
    orig = s1s2.H

    def Hn(*parts):
        return orig(*parts)[:n_bits // 8] + b'\x00' * (32 - n_bits // 8)
    return Hn


def prefixed_multiproof_build(ladder, leaf_indices, Hf):
    """Variant with POSITION-PREFIXED node hashing H('node', rung, level, index, l, r)
    (as RFC 8554 / XMSS-T do): the audit's proposed fix for the multi-target loss."""
    rung_of = {}
    for i in leaf_indices:
        for r, (start, size) in enumerate(ladder.rungs):
            if start <= i < start + size:
                rung_of.setdefault(r, []).append(i - start)
    proof, roots = {}, {}
    for r, idxs in rung_of.items():
        start, size = ladder.rungs[r]
        depth = size.bit_length() - 1
        levels = [ladder.leaves[start:start + size]]
        for lvl in range(depth):
            p = levels[-1]
            levels.append([Hf(b'node', r.to_bytes(4, 'big'), lvl.to_bytes(1, 'big'), (i // 2).to_bytes(4, 'big'), p[i], p[i + 1])
                           for i in range(0, len(p), 2)])
        roots[r] = levels[-1][0]
        frontier, nodes = set(idxs), []
        for lvl in range(depth):
            nxt = set()
            for i in sorted(frontier):
                if (i ^ 1) not in frontier:
                    nodes.append((lvl, i ^ 1, levels[lvl][i ^ 1]))
                nxt.add(i >> 1)
            frontier = nxt
        proof[r] = {'leaves': sorted(idxs), 'nodes': nodes}
    return proof, roots


def prefixed_multiproof_verify(roots, rungs, leaf_digests_by_index, proof, Hf):
    for r, p in proof.items():
        start, size = rungs[r]
        depth = size.bit_length() - 1
        cur = {i: leaf_digests_by_index[start + i] for i in p['leaves']}
        supplied = {(lvl, i): h for lvl, i, h in p['nodes']}
        for lvl in range(depth):
            nxt = {}
            for i, h in cur.items():
                sib = cur.get(i ^ 1) or supplied.get((lvl, i ^ 1))
                if sib is None:
                    return False
                l, rr = (h, sib) if i & 1 == 0 else (sib, h)
                nxt[i >> 1] = Hf(b'node', r.to_bytes(4, 'big'), lvl.to_bytes(1, 'big'), (i >> 1).to_bytes(4, 'big'), l, rr)
            cur = nxt
        if cur.get(0) != roots[r]:
            return False
    return True


def binding_game(n_bits, trials, rng, prefixed=False, n_leaves=64):
    """Reduced-size single-structure second-preimage game: with the node hash
    truncated to n bits, how often does a DIFFERENT leaf value verify under an
    honest proof?  Each trial recomputes `depth` nodes, i.e. costs `depth`
    queries, and wins if ANY level collides — so wins ≈ depth·trials·2^-n for
    BOTH variants: per QUERY the rate is 2^-n either way.  (First-run
    mis-accounting, kept on record: 109/4096 was read as a 2^-5.2 loss; per
    query it is 109/24576 = 2^-7.8.)  Returns (wins, queries)."""
    orig = s1s2.H
    wins, queries = 0, 0
    Hn = _Hn(n_bits)
    depth = n_leaves.bit_length() - 1
    try:
        s1s2.H = Hn
        leaves = [Hn(b'leaf', i.to_bytes(2, 'big')) for i in range(n_leaves)]
        lad = s1s2.MTLLadder(leaves, 0)
        if prefixed:
            proof, roots = prefixed_multiproof_build(lad, [5, 17], Hn)
        else:
            proof, roots = s1s2.MTLMultiproof.build(lad, [5, 17]), lad.rung_roots
        for t in range(trials):
            fake = list(leaves)
            fake[17] = Hn(b'fake', t.to_bytes(4, 'big'))
            ok = (prefixed_multiproof_verify(roots, lad.rungs, fake, proof, Hn) if prefixed
                  else s1s2.MTLMultiproof.verify(roots, lad.rungs, fake, proof))
            queries += depth
            if ok:
                wins += 1
    finally:
        s1s2.H = orig
    return wins, queries


def multi_target_game(n_bits, T, queries, rng, prefixed=False):
    """The game where prefixes matter (MM-SPR, MTL Thm 2 / XMSS-T): the adversary
    holds T signed structures (T target interior nodes from T different ladders
    at various positions) and wins if ANY query H(l, r) equals ANY target.
      unprefixed: one evaluation is tested against all T targets -> T·2^-n / query
      prefixed by (ladder id, rung, level, index): an evaluation commits to one
      position, so it is tested against ONE target -> 2^-n / query
    Measured at reduced n; the ledger scales it to n = 256 and T = 2^40."""
    Hn = _Hn(n_bits)
    targets = {}
    for t in range(T):
        lid, lvl, idx = t.to_bytes(4, 'big'), rng.randrange(1, 10), rng.randrange(0, 2 ** 10)
        l, r = Hn(b'l', lid), Hn(b'r', lid)
        if prefixed:
            targets[(lid, lvl, idx)] = Hn(b'node', lid, lvl.to_bytes(1, 'big'), idx.to_bytes(4, 'big'), l, r)
        else:
            targets[t] = Hn(b'node', l, r)
    tset = set(targets.values())
    keys = list(targets)
    wins = 0
    for q in range(queries):
        l, r = Hn(b'try-l', q.to_bytes(4, 'big')), Hn(b'try-r', q.to_bytes(4, 'big'))
        if prefixed:
            lid, lvl, idx = keys[q % T]                      # the query commits to one position
            wins += Hn(b'node', lid, lvl.to_bytes(1, 'big'), idx.to_bytes(4, 'big'), l, r) == targets[(lid, lvl, idx)]
        else:
            wins += Hn(b'node', l, r) in tset
    return wins


def multi_target_ledger(n_bits=256, T_log2=40, gates_per_query_log2=18, budget_log2=128):
    """Quantum multi-target second preimage: 2^(n/2) / sqrt(T) queries when all
    targets live in one function (unprefixed); 2^(n/2) when each is its own."""
    un = n_bits / 2 - T_log2 / 2 + gates_per_query_log2
    pre = n_bits / 2 + gates_per_query_log2
    return {'unprefixed_gates_log2': un, 'unprefixed_passes_qpt128': un >= budget_log2,
            'prefixed_gates_log2': pre, 'prefixed_passes_qpt128': pre >= budget_log2, 'T_log2': T_log2}


# ----------------------------------------------------------------- tests ----
BASE = {'n_names': 256, 'label_len': 8, 'n_labels': 1, 'apex_len': 7, 'ttl': 3600, 'n_keys': 1, 'key_bytes': 32,
        'n_sigs': 1, 'extra_types': 0, 'wildcard': False, 'bitmap_windows': 1, 'denial': 'nsec',
        'protocol': 'batched', 'shard_log2': 12, 'cname_len': 0, 'realistic': True}


class Tests(unittest.TestCase):
    def test_S2_001_wire_encoder_is_real(self):
        """S2-001 responses parse back with dnspython and carry the expected RRSIG count."""
        p = dict(BASE)
        z = Zone(p, random.Random(0)); e = Encoder(z, p)
        wire = e.nxdomain(10)
        m = dns.message.from_wire(wire)
        self.assertEqual(m.rcode(), dns.rcode.NXDOMAIN)
        n_rrsig = sum(1 for rr in m.authority if rr.rdtype == dns.rdatatype.RRSIG)
        self.assertEqual(n_rrsig, 3)                          # SOA + NSEC + apex NSEC
        p3 = dict(BASE, denial='nsec3'); e3 = Encoder(Zone(p3, random.Random(0)), p3)
        m3 = dns.message.from_wire(e3.nxdomain(10))
        self.assertEqual(sum(1 for rr in m3.authority if rr.rdtype == dns.rdatatype.RRSIG), 4)
        pc = dict(BASE, denial='compact'); ec = Encoder(Zone(pc, random.Random(0)), pc)
        mc = dns.message.from_wire(ec.nxdomain(10))
        self.assertEqual(sum(1 for rr in mc.authority if rr.rdtype == dns.rdatatype.RRSIG), 2)

    def test_S2_002_model_numbers_remeasured(self):
        """S2-002 exact wire size of the model's baseline case vs the model's 1,129 B."""
        p = dict(BASE, n_names=2000)
        sizes = response_sizes(p, random.Random(1))
        self.assertLessEqual(sizes['NXDOMAIN'], UDP_SAFE)
        self.assertLessEqual(sizes['A'], UDP_SAFE)
        self.assertLessEqual(sizes['DNSKEY'], UDP_SAFE)
        # per-RRSIG condensed (no batching) must be larger than batched
        q = dict(p, protocol='per_rrsig')
        self.assertGreater(response_sizes(q, random.Random(1))['NXDOMAIN'], sizes['NXDOMAIN'])

    def test_S2_003_worst_case_search_realistic(self):
        """S2-003 realistic-legal worst case per response type under the batched protocol
        (measured; the assertion encodes what the search found, see report)."""
        # AUDIT FINDING (first run refuted the model's "1,129 B for any zone size"): the
        # realistic-legal worst case is ~1,530 B — 3×20-char labels, 30-char apex, two keys
        # with rollover double-signing, shard 2^14. Levers measured by the search:
        # no double-signing -> 1,361; plus shard 2^10 -> 1,287 (under RFC 9715, over 1,232).
        base = {'protocol': 'batched', 'denial': 'nsec'}
        worst, p = search('NXDOMAIN', samples=120, climb=60, seed=3, realistic=True, fixed=base)
        self.assertGreater(worst, UDP_RFC9715)
        self.assertLessEqual(worst, 1700)
        self.assertEqual(p['n_sigs'], 2)                              # rollover is the top lever
        no_roll, _ = search('NXDOMAIN', samples=120, climb=60, seed=3, realistic=True, fixed=dict(base, n_sigs=1))
        self.assertLess(no_roll, worst)
        small_shard, _ = search('NXDOMAIN', samples=120, climb=60, seed=3, realistic=True, fixed=dict(base, n_sigs=1, shard_log2=10))
        self.assertLessEqual(small_shard, UDP_RFC9715)
        self.assertGreater(small_shard, UDP_SAFE)
        cname, _ = search('CNAME', samples=80, climb=40, seed=3, realistic=True, fixed=base)
        self.assertGreater(cname, UDP_SAFE)                           # CNAME chains (5 RRSIGs) exceed 1,232

    def test_S2_004_multiproof_manipulation_games(self):
        """S2-004 remove leaf / reorder nodes / foreign node / changed statement all rejected;
        independent top-down validator agrees with the reference verifier on every case."""
        leaves = [H(b'leaf', i.to_bytes(2, 'big')) for i in range(300)]
        lad = s1s2.MTLLadder(leaves, 0)
        sel = [1, 2, 200]
        proof = s1s2.MTLMultiproof.build(lad, sel)
        V = lambda pr, lv=leaves: (s1s2.MTLMultiproof.verify(lad.rung_roots, lad.rungs, lv, pr),
                                   independent_multiproof_verify(lad.rung_roots, lad.rungs, lv, pr))
        self.assertEqual(V(proof), (True, True))                                      # positive control
        import copy
        p1 = copy.deepcopy(proof); p1[0]['leaves'].remove(200)                       # remove a leaf
        self.assertEqual(V(p1), (False, False))
        # FALSIFIED TEST HYPOTHESIS: "reordering the node list breaks verification".
        # Nodes carry explicit (level, index) coordinates, so list order is irrelevant —
        # a non-attack. The real manipulation is swapping hash VALUES between coordinates:
        p2 = copy.deepcopy(proof); p2[0]['nodes'][0], p2[0]['nodes'][1] = p2[0]['nodes'][1], p2[0]['nodes'][0]
        self.assertEqual(V(p2), (True, True))                                         # order-independent
        p2b = copy.deepcopy(proof)
        (l0, i0, h0), (l1, i1, h1) = p2b[0]['nodes'][0], p2b[0]['nodes'][1]
        p2b[0]['nodes'][0], p2b[0]['nodes'][1] = (l0, i0, h1), (l1, i1, h0)
        self.assertEqual(V(p2b), (False, False))                                      # values swapped
        p3 = copy.deepcopy(proof); lvl, i, _ = p3[0]['nodes'][2]
        p3[0]['nodes'][2] = (lvl, i, lad.rung_levels[0][lvl][(i + 2) % len(lad.rung_levels[0][lvl])])
        self.assertEqual(V(p3), (False, False))                                       # foreign node
        alt = list(leaves); alt[200] = H(b'other statement')
        self.assertEqual(V(proof, alt), (False, False))                               # different denial statement
        p4 = copy.deepcopy(proof); p4[0]['nodes'].append((0, 7, leaves[7]))            # extra node not on any path
        self.assertFalse(independent_multiproof_verify(lad.rung_roots, lad.rungs, leaves, p4))

    def test_S2_005_binding_per_query_is_2_pow_minus_n(self):
        """S2-005 single-structure second preimage: per QUERY ≈ 2^-n for both variants."""
        rng = random.Random(5)
        for prefixed in (False, True):
            w, q = binding_game(8, 4096, rng, prefixed=prefixed)
            rate = w / q
            self.assertTrue(0.5 / 256 <= rate <= 1.7 / 256, (prefixed, w, q))
            self.assertEqual(binding_game(32, 200, rng, prefixed=prefixed)[0], 0)

    def test_S2_006_multi_target_game_prefix_matters(self):
        """S2-006 AUDIT FINDING: with T signed structures, unprefixed node hashing gives
        T·2^-n per query (measured), prefixed gives 2^-n; at n=256, T=2^40 the unprefixed
        quantum cost is 2^126 gates — INSIDE the QPT-128 budget. Fix: prefix nodes with
        (ladder id, rung, level, index). Zero bytes added."""
        rng = random.Random(6)
        n, T, Q = 16, 64, 100_000
        wu = multi_target_game(n, T, Q, rng, prefixed=False)     # expect Q·T/2^n = 97.7
        wp = multi_target_game(n, T, Q, rng, prefixed=True)      # expect Q/2^n = 1.5
        self.assertTrue(60 <= wu <= 140, wu)
        self.assertLessEqual(wp, 8, wp)
        L = multi_target_ledger()
        self.assertFalse(L['unprefixed_passes_qpt128'])
        self.assertEqual(L['unprefixed_gates_log2'], 126)
        self.assertTrue(L['prefixed_passes_qpt128'])


def report():
    rng = random.Random(7)
    out = {'baseline_exact': response_sizes(dict(BASE, n_names=2000), rng),
           'model_claim_nxdomain_shard12': 1129, 'worst_case': {}}
    for realistic in (True, False):
        for obj in ('NXDOMAIN', 'CNAME', 'DNSKEY', 'WILDCARD', 'A'):
            v, p = search(obj, samples=200, climb=100, seed=11, realistic=realistic, fixed={'protocol': 'batched'})
            out['worst_case'][f"{obj}/{'realistic' if realistic else 'pathological'}"] = {
                'bytes': v, 'class': s1s2.classify(v), 'params': {k: p[k] for k in ('n_names', 'label_len', 'n_labels', 'apex_len', 'n_keys', 'n_sigs', 'denial', 'bitmap_windows', 'cname_len', 'shard_log2')}}
    out['binding_game_per_query'] = {}
    for n, t in ((8, 4096), (10, 8192), (12, 16384)):
        wu, qu = binding_game(n, t, rng); wp, qp = binding_game(n, t, rng, prefixed=True)
        out['binding_game_per_query'][f'n={n}'] = {'unprefixed': f'{wu}/{qu}', 'prefixed': f'{wp}/{qp}', 'expected_rate': 2 ** -n}
    out['multi_target_game'] = {f'n={n},T={T}': {'unprefixed_wins': multi_target_game(n, T, 100_000, rng),
                                                 'prefixed_wins': multi_target_game(n, T, 100_000, rng, prefixed=True),
                                                 'expected_unprefixed': 100_000 * T / 2 ** n, 'expected_prefixed': 100_000 / 2 ** n}
                                for n, T in ((16, 64), (16, 256))}
    out['multi_target_ledger_n256'] = multi_target_ledger()
    out['audit_finding_multi_target'] = ('v2.0 MTLLadder/MTLMultiproof hash interior nodes as H(node, l, r) with no ladder/position '
                                         'prefix. Single-structure second preimage is 2^-n per query either way (first-run reading of '
                                         'a log2(depth) loss was a per-trial/per-query mis-accounting, corrected). But in the '
                                         'multi-target game over T ≈ 2^40 signed nodes across all zones, one evaluation is tested '
                                         'against every target: quantum cost 2^(128-20) queries = 2^126 gates < 2^128 — fails QPT-128. '
                                         'Fix: H(node, ladder_id, rung, level, index, l, r) as RFC 8554 (I, r) / XMSS-T do; zero bytes.')
    out['untestable_assumptions'] = [
        'MM-SPR of the node hash (MTL Thm 2) — measured only at n ≤ 14 bits',
        'resolver behaviour above 1,232/1,400 B (fragmentation/TCP fallback) is from literature, not measured here',
        'the batch-reference RRSIG encoding (MTL-Type 2/3) is this audit\'s protocol decision, not an IETF draft']
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--report', action='store_true')
    a = ap.parse_args(argv)
    if a.report:
        print(json.dumps(report(), indent=2)); return 0
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if r.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
