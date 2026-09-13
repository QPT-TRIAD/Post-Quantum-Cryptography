#!/usr/bin/env python3
"""Derive the audit-fix versions from the FROZEN reference files by exact string
replacement. Every replacement must match exactly once, otherwise the script
aborts: no silent drift from the reference. Outputs are NEW files in the
project directory; the reference files are never touched.

  F1  modeB_prover_v1.50.c            -> modeB_prover_v1.51.c
  F2, F4  pq_infra_s1s2_hashsig_dnssec_v2.0.py -> pq_infra_s1s2_hashsig_dnssec_v2.2.py
  F3  pq_audit_s1_lms_v2.1.py         -> pq_audit_s1_lms_v2.2.py
  F5  hidden_signer_modeB_v1.50.py    -> hidden_signer_modeB_v1.51.py
"""
import os
import pathlib
import sys

# Reference source tree the fix versions are derived from. The verification environment
# exports PQT_SRC; see docs/inputs-and-provenance.md. This script only ADDS files there.
PQT = pathlib.Path(os.environ.get('PQT_SRC', ''))
if not PQT.is_dir():
    raise SystemExit('PQT_SRC is not set: source the environment activation script '
                     '(tooling/), or point PQT_SRC at a local copy of the research tree')


def patch(src, dst, replacements, prepend=None, append=None):
    text = (PQT / src).read_text()
    for old, new in replacements:
        n = text.count(old)
        if n != 1:
            print(f'ABORT {src}: pattern found {n} times (need exactly 1):\n{old[:120]}')
            sys.exit(1)
        text = text.replace(old, new)
    if prepend:
        text = prepend + text
    if append:
        # regression classes go BEFORE the __main__ guard, so main() can reference them
        guard = "\nif __name__ == '__main__':"
        if text.count(guard) != 1:
            print(f'ABORT {src}: __main__ guard found {text.count(guard)} times')
            sys.exit(1)
        text = text.replace(guard, append + guard, 1)
    (PQT / dst).write_text(text)
    print(f'wrote {dst} ({len(text)} bytes, {len(replacements)} replacement(s))')


# ---------------------------------------------------------------- F1 (C leak)
patch('modeB_prover_v1.50.c', 'modeB_prover_v1.51.c', [
    ('for (int i = 0; i < p->wg; i++) if ((h3[32 + (i >> 3)] >> (i & 7)) & 1) { *why = "grinding condition"; return 0; }',
     'for (int i = 0; i < p->wg; i++) if ((h3[32 + (i >> 3)] >> (i & 7)) & 1) { *why = "grinding condition"; free(P); return 0; }  /* F1: v1.50 leaked P here */'),
], prepend='/* modeB_prover_v1.51.c — audit-fix release of v1.50 (2026-09-13).\n'
           ' * F1 (LSan, audit stack v0.1): verify() returned on the grinding-condition check without freeing\n'
           ' * the circ_pub_t *P (9,568 B) allocated at the top of verify(); a stream of rejected proofs leaked\n'
           ' * one P each (rank-3 resource finding). This file is v1.50 plus that one free(); nothing else changed.\n'
           ' * The v1.50 reference is preserved immutably (see FAILED_ASSUMPTIONS.md F1).\n */\n')

# ------------------------------------------------------ F2, F4 (multiproof, merkle)
S1S2_VERIFY_OLD = '''    @staticmethod
    def verify(ladder_rung_roots, rungs, leaf_digests_by_index, proof):
        for r, p in proof.items():
            start, size = rungs[r]
            depth = size.bit_length() - 1
            known = {i: leaf_digests_by_index[start + i] for i in p['leaves']}
            supplied = {(lvl, i): h for lvl, i, h in p['nodes']}
            cur = dict(known)
            for lvl in range(depth):
                nxt = {}
                for i, h in cur.items():
                    sib = cur.get(i ^ 1) or supplied.get((lvl, i ^ 1))
                    if sib is None:
                        return False
                    left, right = (h, sib) if i & 1 == 0 else (sib, h)
                    nxt[i >> 1] = H(b'node', left, right)
                cur = nxt
            if cur.get(0) != ladder_rung_roots[r]:
                return False
        return True'''
S1S2_VERIFY_NEW = '''    @staticmethod
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
                        nxt[i >> 1] = H(b'node', left, right)
                    cur = nxt
                if cur.get(0) != ladder_rung_roots[r]:
                    return False
                covered |= {start + i for i in leaves}
            if required is not None and not set(required) <= covered:
                return False
            return True
        except (TypeError, KeyError, IndexError, ValueError, AttributeError):
            return False'''

MERKLE_OLD = '''def merkle_verify(root, pubseed, height, msg, sig):
    idx = sig['idx']
    if not 0 <= idx < (1 << height) or len(sig['auth']) != height or len(sig['ots']) != LEN:
        return False'''
MERKLE_NEW = '''def merkle_verify(root, pubseed, height, msg, sig):
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
        return False'''

S1S2_TESTS = '''

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
        signer = MerkleSigner(3, b'\\x05' * 32)
        sig = signer.sign(b'm')
        self.assertTrue(merkle_verify(signer.root, signer.pubseed, 3, b'm', sig))
        for bad in ({}, None, {'idx': 1.0, 'ots': sig['ots'], 'auth': sig['auth']},
                    {'idx': '1', 'ots': sig['ots'], 'auth': sig['auth']}, {'idx': 1, 'ots': [1] * LEN, 'auth': sig['auth']},
                    {'idx': True, 'ots': sig['ots'], 'auth': sig['auth']}):
            self.assertFalse(merkle_verify(signer.root, signer.pubseed, 3, b'm', bad))
        self.assertFalse(merkle_verify(signer.root, signer.pubseed, 3, 'm', sig))
'''
patch('pq_infra_s1s2_hashsig_dnssec_v2.0.py', 'pq_infra_s1s2_hashsig_dnssec_v2.2.py',
      [(S1S2_VERIFY_OLD, S1S2_VERIFY_NEW), (MERKLE_OLD, MERKLE_NEW),
       ('    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))',
        '    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Tests),\n'
        '                                unittest.defaultTestLoader.loadTestsFromTestCase(AuditFixTests)])\n'
        '    r = unittest.TextTestRunner(verbosity=2).run(suite)')],
      prepend='# pq_infra_s1s2_hashsig_dnssec_v2.2.py — audit-fix release of v2.0 (2026-09-13): F2 (empty/extra-node multiproof\n'
              '# accepted) and F4 (merkle_verify raised on malformed input). v2.0 is preserved immutably.\n',
      append=S1S2_TESTS)

# ------------------------------------------------------------- F3 (mixed n/m)
LMS_INIT_OLD = '''    def __init__(self, lms_tc, ots_tc, I=None, seed=None):
        self.lms_tc, self.ots_tc = lms_tc, ots_tc
        self.m, self.h = LMS[lms_tc]'''
LMS_INIT_NEW = '''    def __init__(self, lms_tc, ots_tc, I=None, seed=None):
        if not approved_pair(lms_tc, ots_tc):
            raise ValueError('F3: LMS m and LM-OTS n must match (SP 800-208 approved sets pair n with m; '
                             'RFC 8554 5.1: the two hash functions SHOULD be the same)')
        self.lms_tc, self.ots_tc = lms_tc, ots_tc
        self.m, self.h = LMS[lms_tc]'''
LMS_VERIFY_OLD = '''    lms_tc, ots_tc = struct.unpack('>II', pubkey[:8])
    if lms_tc not in LMS or ots_tc not in LMOTS:
        return False'''
LMS_VERIFY_NEW = '''    lms_tc, ots_tc = struct.unpack('>II', pubkey[:8])
    if lms_tc not in LMS or ots_tc not in LMOTS or not approved_pair(lms_tc, ots_tc):
        return False                                   # F3: refuse non-approved n != m combinations'''
APPROVED = '''

def approved_pair(lms_tc, ots_tc):
    """SP 800-208 §4 lists LMS sets with m = 32 only alongside LM-OTS sets with n = 32, and m = 24 with
    n = 24 (same hash function). RFC 8554 §5.1 is silent on n vs m but says the hash functions SHOULD be
    the same. Mixed pairs are therefore not approved; both this implementation and hsslms 0.1.3 accepted
    them and hsslms is self-inconsistent on them (audit stack v0.1, F3)."""
    return lms_tc in LMS and ots_tc in LMOTS and LMS[lms_tc][0] == LMOTS[ots_tc][0]


def lms_sizes(lms_tc, ots_tc):'''
LMS_TESTS = '''

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
'''
patch('pq_audit_s1_lms_v2.1.py', 'pq_audit_s1_lms_v2.2.py',
      [(LMS_INIT_OLD, LMS_INIT_NEW), (LMS_VERIFY_OLD, LMS_VERIFY_NEW), ('\n\ndef lms_sizes(lms_tc, ots_tc):', APPROVED),
       ('    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))',
        '    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Tests),\n'
        '                                unittest.defaultTestLoader.loadTestsFromTestCase(AuditFixTests)])\n'
        '    r = unittest.TextTestRunner(verbosity=2).run(suite)')],
      prepend='# pq_audit_s1_lms_v2.2.py — audit-fix release of v2.1 (2026-09-13): F3, refuse non-approved mixed m/n typecodes.\n',
      append=LMS_TESTS)

# --------------------------------------------------------------- F5 (Mode B)
MB_ENCODE_OLD = '''def encode(p, registry, secrets, domain, message, seats, proof=b'STRUCTURE-ONLY'):
    if type(message) is not bytes or len(message) != 64:
        raise ModeBError('message must be a 64-byte digest')'''
MB_ENCODE_NEW = '''def encode(p, registry, secrets, domain, message, seats, proof=b'STRUCTURE-ONLY'):
    if type(message) is not bytes or len(message) != 64:
        raise ModeBError('message must be a 64-byte digest')
    if type(domain) is not bytes or len(domain) != 64:                 # F5: '64s' silently truncated/padded
        raise ModeBError('domain must be a 64-byte canonical string')
    if type(proof) is not bytes:
        raise ModeBError('proof must be bytes')'''
MB_PARSE_OLD = '''def parse(p, frame):
    if len(frame) > m46.MAX_FRAME_BYTES or len(frame) < m46.HEADER_BYTES + QUORUM * p.handle_bytes:'''
MB_PARSE_NEW = '''def parse(p, frame):
    if type(frame) is not bytes:                                       # F5: bytearray/str/None were not typed errors
        raise ModeBError('frame must be canonical bytes')
    if len(frame) > m46.MAX_FRAME_BYTES or len(frame) < m46.HEADER_BYTES + QUORUM * p.handle_bytes:'''
MB_TESTS = '''

class AuditFixTests(unittest.TestCase):
    """F5 regressions (audit stack v0.1, property layer M1/M2)."""

    @classmethod
    def setUpClass(cls):
        cls.p = m46.make_params(n=32, expansion=16, seed=b'v151-fix')
        import random
        rng = random.Random(151)
        cls.registry, cls.secrets = m46.build_registry(cls.p, b'epoch', (b'D' * 64,), rng)

    def test_f5_domain_canonicality(self):
        seats = list(range(QUORUM))
        for bad in (b'D' * 63, b'D' * 65, 'D' * 64, None):
            with self.assertRaises(ModeBError):
                encode(self.p, self.registry, self.secrets, bad, b'M' * 64, seats)
        with self.assertRaises(ModeBError):
            encode(self.p, self.registry, self.secrets, b'D' * 64, b'M' * 64, seats, proof='not-bytes')

    def test_f5_parse_requires_bytes(self):
        frame = encode(self.p, self.registry, self.secrets, b'D' * 64, b'M' * 64, list(range(QUORUM)))
        parse(self.p, frame)
        for bad in (bytearray(frame), memoryview(frame), frame.decode('latin1'), None, 7):
            with self.assertRaises(ModeBError):
                parse(self.p, bad)
'''
patch('hidden_signer_modeB_v1.50.py', 'hidden_signer_modeB_v1.51.py',
      [(MB_ENCODE_OLD, MB_ENCODE_NEW), (MB_PARSE_OLD, MB_PARSE_NEW),
       ('    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(V150Tests))',
        '    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(V150Tests),\n'
        '                                unittest.defaultTestLoader.loadTestsFromTestCase(AuditFixTests)])\n'
        '    r = unittest.TextTestRunner(verbosity=2).run(suite)')],
      prepend='# hidden_signer_modeB_v1.51.py — audit-fix release of v1.50 (2026-09-13): F5 canonical input checks.\n'
              '# Research code (Mode B); never compiled into a node. v1.50 is preserved immutably.\n',
      append=MB_TESTS)
print('all fixes written')
