#!/usr/bin/env python3
"""Property / malformed-input / differential layer for
  T3 = pq_infra_s1s2_hashsig_dnssec_v2.0.py  (WOTS+/Merkle: MerkleSigner, merkle_verify; MTLLadder; MTLMultiproof)
  T4 = pq_audit_s1_lms_v2.1.py               (RFC 8554 LmsPrivate / lms_verify)  vs  hsslms 0.1.3 (independent)

Run:  python3 -m pytest -q test_props_hashsig.py   or   python3 test_props_hashsig.py
"""
import importlib.util
import os
import random
import struct
import sys
import unittest

sys.dont_write_bytecode = True
from hypothesis import HealthCheck, given, settings, strategies as st, assume

# Reference source tree: the read-only inputs this layer audits. The verification
# environment exports PQT_SRC; see docs/inputs-and-provenance.md.
PQT = os.environ.get('PQT_SRC')
if not PQT or not os.path.isdir(PQT):
    raise SystemExit('PQT_SRC is not set: source the environment activation script '
                     '(tooling/), or point PQT_SRC at a local copy of the research tree')


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PQT, filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


T3 = _load('s1s2_audit', 'pq_infra_s1s2_hashsig_dnssec_v2.0.py')
T4 = _load('lms21_audit', 'pq_audit_s1_lms_v2.1.py')
import hsslms  # noqa: E402

settings.register_profile('audit', deadline=None, derandomize=True, print_blob=True,
                          suppress_health_check=list(HealthCheck))
settings.load_profile('audit')

H = T3.H

# ------------------------------------------------------------------ Merkle pool (h=4, 16 sigs)
SIGNER4 = T3.MerkleSigner(4, b'\x11' * 32)
POOL = []
for _i in range(16):
    _m = b'firmware-%02d' % _i
    POOL.append((_m, SIGNER4.sign(_m)))


def mverify(msg, sig, root=None, pubseed=None, height=4):
    return T3.merkle_verify(SIGNER4.root if root is None else root,
                            SIGNER4.pubseed if pubseed is None else pubseed, height, msg, sig)


def copy_sig(sig):
    return {'idx': sig['idx'], 'ots': list(sig['ots']), 'auth': list(sig['auth'])}


def flip(b, i, x=1):
    a = bytearray(b)
    a[i % len(a)] ^= x or 1
    return bytes(a)


# ------------------------------------------------------------------ LMS keys
PAIRS = [(5, 1), (5, 2), (5, 3), (5, 4), (10, 5), (10, 6), (10, 7), (10, 8), (5, 8), (10, 4)]
T4KEYS, HSKEYS = {}, {}


def t4_key(pair, fresh=False):
    k = T4KEYS.get(pair)
    if k is None or fresh or k.q >= (1 << k.h):
        n = T4KEYS.get(('gen', pair), 0) + 1
        T4KEYS[('gen', pair)] = n
        k = T4.LmsPrivate(pair[0], pair[1], I=bytes([n]) * 16, seed=(bytes([pair[0], pair[1], n]) * 11)[:32])
        T4KEYS[pair] = k
    return k


def hs_key(pair):
    k = HSKEYS.get(pair)
    if k is None or k.get_avail_signatures() == 0:
        k = hsslms.LMS_Priv(hsslms.LMS_ALGORITHM_TYPE(pair[0]), hsslms.LMOTS_ALGORITHM_TYPE(pair[1]), num_cores=1)
        HSKEYS[pair] = k
    return k


def hs_verify(pk, msg, sig):
    try:
        hsslms.LMS_Pub(pk).verify(msg, sig)
        return True
    except Exception:                                                   # noqa: BLE001  hsslms raises INVALID
        return False


T4SIGS = {}                                                               # pair -> (pk, key, [(msg, sig)] x4)
for _pair in PAIRS:
    _k = T4.LmsPrivate(_pair[0], _pair[1], I=b'\xA5' * 16, seed=(bytes(_pair) * 16)[:32])   # dedicated, never re-used
    T4SIGS[_pair] = (_k.public_key(), _k,
                     [(b'boot-%d-%d' % _pair + bytes([j]), _k.sign(b'boot-%d-%d' % _pair + bytes([j]))) for j in range(4)])

DIFF_LOG = []


# =============================================================================
class MerkleProperties(unittest.TestCase):

    @given(st.integers(2, 3), st.lists(st.binary(max_size=64), min_size=1, max_size=8), st.binary(max_size=64),
           st.binary(min_size=32, max_size=32))
    @settings(max_examples=40)
    def test_sign_verify_roundtrip_wrong_message_and_exhaustion(self, h, msgs, other, seed):
        s = T3.MerkleSigner(h, seed)
        msgs = msgs[:1 << h]
        sigs = []
        for k, m in enumerate(msgs):
            sig = s.sign(m)
            self.assertEqual(sig['idx'], k)                                 # state advances 0,1,2,...
            self.assertTrue(T3.merkle_verify(s.root, s.pubseed, h, m, sig))
            if other != m:
                self.assertFalse(T3.merkle_verify(s.root, s.pubseed, h, other, sig))
            sigs.append(sig)
        for _ in range((1 << h) - len(msgs)):
            s.sign(b'fill')
        with self.assertRaises(RuntimeError):                               # state exhaustion
            s.sign(b'one too many')
        self.assertEqual(len({x['idx'] for x in sigs}), len(sigs))

    @given(st.integers(0, 15), st.integers(0, 3), st.integers(0, 31), st.integers(1, 255))
    @settings(max_examples=200)
    def test_auth_path_tamper_rejected(self, which, level, byte, xor):
        m, sig = POOL[which]
        t = copy_sig(sig)
        t['auth'][level] = flip(t['auth'][level], byte, xor)
        self.assertFalse(mverify(m, t))

    def test_auth_path_tamper_every_level_exhaustive(self):
        for m, sig in POOL:
            self.assertTrue(mverify(m, sig))
            for level in range(4):
                t = copy_sig(sig)
                t['auth'][level] = flip(t['auth'][level], 0, 0x01)
                self.assertFalse(mverify(m, t), (sig['idx'], level))
                t = copy_sig(sig)
                t['auth'][level] = H(b'foreign', bytes([level]))
                self.assertFalse(mverify(m, t))
            t = copy_sig(sig)
            t['auth'] = t['auth'][:-1]
            self.assertFalse(mverify(m, t))                                 # short path
            t = copy_sig(sig)
            t['auth'] = t['auth'] + [H(b'x')]
            self.assertFalse(mverify(m, t))                                 # long path
            t = copy_sig(sig)
            t['auth'] = t['auth'][::-1]
            self.assertFalse(mverify(m, t))                                 # reversed path

    @given(st.integers(0, 15), st.integers(0, T3.LEN - 1), st.integers(0, 31), st.integers(1, 255))
    @settings(max_examples=120)
    def test_ots_element_tamper_rejected(self, which, i, byte, xor):
        m, sig = POOL[which]
        t = copy_sig(sig)
        t['ots'][i] = flip(t['ots'][i], byte, xor)
        self.assertFalse(mverify(m, t))

    @given(st.integers(0, 15), st.integers(-3, 20))
    @settings(max_examples=100)
    def test_index_tamper_rejected(self, which, idx):
        m, sig = POOL[which]
        assume(idx != sig['idx'])
        t = copy_sig(sig)
        t['idx'] = idx
        self.assertFalse(mverify(m, t))

    def test_wrong_root_pubseed_height_and_ots_truncation(self):
        m, sig = POOL[3]
        self.assertFalse(mverify(m, sig, root=H(b'other-root')))
        self.assertFalse(mverify(m, sig, pubseed=H(b'other-seed')))
        self.assertFalse(mverify(m, sig, height=3))
        self.assertFalse(mverify(m, sig, height=5))
        t = copy_sig(sig)
        t['ots'] = t['ots'][:-1]
        self.assertFalse(mverify(m, t))
        t = copy_sig(sig)
        t['ots'] = t['ots'] + [H(b'x')]
        self.assertFalse(mverify(m, t))
        other_m, other_sig = POOL[4]
        t = copy_sig(other_sig)
        t['idx'] = sig['idx']                                               # index of another leaf
        self.assertFalse(mverify(other_m, t))

    def test_merkle_verify_malformed_signature_objects_return_false(self):
        """Invalid-encoding catalogue for merkle_verify: it must return False, not raise."""
        m, sig = POOL[0]
        cases = {
            'idx_float': dict(copy_sig(sig), idx=float(sig['idx'])),
            'idx_str': dict(copy_sig(sig), idx=str(sig['idx'])),
            'idx_none': dict(copy_sig(sig), idx=None),
            'missing_auth': {'idx': sig['idx'], 'ots': list(sig['ots'])},
            'missing_ots': {'idx': sig['idx'], 'auth': list(sig['auth'])},
            'auth_not_list': dict(copy_sig(sig), auth=b''.join(sig['auth'])),
            'ots_element_int': dict(copy_sig(sig), ots=[0] * T3.LEN),
            'empty_dict': {},
        }
        crashes = {}
        for name, bad in cases.items():
            try:
                self.assertFalse(mverify(m, bad), name)
            except AssertionError:
                raise
            except Exception as e:                                          # noqa: BLE001
                crashes[name] = type(e).__name__
        self.assertEqual(crashes, {}, 'merkle_verify raises instead of returning False: %r' % crashes)


# =============================================================================
class MTLProperties(unittest.TestCase):

    def _ladder(self, n, tag=b'rr'):
        leaves = [H(tag, i.to_bytes(4, 'big')) for i in range(n)]
        return leaves, T3.MTLLadder(leaves, underlying_sig_bytes=4627)

    @given(st.integers(1, 48), st.integers(0, 47), st.integers(0, 31))
    @settings(max_examples=120)
    def test_condensed_proof_verifies_and_every_tamper_fails(self, n, i, byte):
        leaves, lad = self._ladder(n)
        i %= n
        p = lad.condensed(i)
        V = T3.MTLLadder.verify
        self.assertTrue(V(lad.rung_roots, lad.rungs, leaves[i], p))
        self.assertFalse(V(lad.rung_roots, lad.rungs, H(b'forged'), p))     # changed leaf
        for lvl in range(len(p['path'])):
            q = dict(p, path=list(p['path']))
            q['path'][lvl] = flip(q['path'][lvl], byte)
            self.assertFalse(V(lad.rung_roots, lad.rungs, leaves[i], q))    # auth-path tamper
        if len(p['path']) >= 2:
            q = dict(p, path=[p['path'][1], p['path'][0]] + p['path'][2:])
            self.assertFalse(V(lad.rung_roots, lad.rungs, leaves[i], q))    # swapped coordinates
        if p['path']:
            q = dict(p, path=p['path'][:-1])
            self.assertFalse(V(lad.rung_roots, lad.rungs, leaves[i], q))    # short path
        q = dict(p, path=p['path'] + [H(b'extra')])
        self.assertFalse(V(lad.rung_roots, lad.rungs, leaves[i], q))        # long path
        q = dict(p, rung=p['rung'] + 1)
        self.assertFalse(V(lad.rung_roots, lad.rungs, leaves[i], q))        # wrong rung
        q = dict(p, leaf=n)
        self.assertFalse(V(lad.rung_roots, lad.rungs, leaves[i], q))        # leaf index out of range
        if n > 1:
            j = (i + 1) % n
            self.assertFalse(V(lad.rung_roots, lad.rungs, leaves[j], p))    # another leaf under this proof

    @given(st.integers(1, 48), st.data())
    @settings(max_examples=120)
    def test_multiproof_verifies_and_mutations_fail(self, n, data):
        leaves, lad = self._ladder(n)
        sel = sorted(data.draw(st.sets(st.integers(0, n - 1), min_size=1, max_size=min(n, 6))))
        proof = T3.MTLMultiproof.build(lad, sel)
        V = T3.MTLMultiproof.verify
        self.assertTrue(V(lad.rung_roots, lad.rungs, leaves, proof))
        r = data.draw(st.sampled_from(sorted(proof)))
        p = proof[r]

        def clone():
            return {k: {'leaves': list(v['leaves']), 'nodes': list(v['nodes'])} for k, v in proof.items()}

        # removing a leaf
        q = clone()
        q[r]['leaves'].remove(data.draw(st.sampled_from(p['leaves'])))
        self.assertFalse(V(lad.rung_roots, lad.rungs, leaves, q))
        # changed leaf digest
        bad = list(leaves)
        bad[lad.rungs[r][0] + p['leaves'][0]] = H(b'forged')
        self.assertFalse(V(lad.rung_roots, lad.rungs, bad, proof))
        if p['nodes']:
            # foreign node
            q = clone()
            k = data.draw(st.integers(0, len(p['nodes']) - 1))
            lvl, i, _ = q[r]['nodes'][k]
            q[r]['nodes'][k] = (lvl, i, H(b'foreign'))
            self.assertFalse(V(lad.rung_roots, lad.rungs, leaves, q))
            # bit flip in a node
            q = clone()
            q[r]['nodes'][k] = (lvl, i, flip(p['nodes'][k][2], data.draw(st.integers(0, 31))))
            self.assertFalse(V(lad.rung_roots, lad.rungs, leaves, q))
        if len(p['nodes']) >= 2:
            # swapping hash values between two coordinates
            q = clone()
            a, b = data.draw(st.lists(st.integers(0, len(p['nodes']) - 1), min_size=2, max_size=2, unique=True))
            (la, ia, ha), (lb, ib, hb) = q[r]['nodes'][a], q[r]['nodes'][b]
            assume(ha != hb)
            q[r]['nodes'][a], q[r]['nodes'][b] = (la, ia, hb), (lb, ib, ha)
            self.assertFalse(V(lad.rung_roots, lad.rungs, leaves, q))
        # extra leaf claimed but not present in the tree position
        if lad.rungs[r][1] > len(p['leaves']):
            q = clone()
            extra = next(i for i in range(lad.rungs[r][1]) if i not in p['leaves'])
            q[r]['leaves'].append(extra)
            bad = list(leaves)
            bad[lad.rungs[r][0] + extra] = H(b'not-in-tree')
            self.assertFalse(V(lad.rung_roots, lad.rungs, bad, q))

    def test_multiproof_non_canonical_inputs(self):
        """Invalid-encoding catalogue for MTLMultiproof.verify (must return False, never raise
        and never accept a proof that proves nothing)."""
        leaves, lad = self._ladder(20)
        V = T3.MTLMultiproof.verify
        proof = T3.MTLMultiproof.build(lad, [3, 7])
        self.assertTrue(V(lad.rung_roots, lad.rungs, leaves, proof))
        observations = {}
        # extra unused node: accepted (non-minimal proof) -- observation only, semantically sound
        q = {0: {'leaves': list(proof[0]['leaves']), 'nodes': list(proof[0]['nodes']) + [(0, 15, H(b'junk'))]}}
        observations['extra_unused_node_accepted'] = V(lad.rung_roots, lad.rungs, leaves, q)
        print('\n[MTL] observations:', observations)
        crashes, accepts = {}, []
        cases = {
            'empty_proof_dict': {},
            'rung_with_no_leaves': {0: {'leaves': [], 'nodes': []}},
            'leaf_index_equal_to_rung_size': {0: {'leaves': [16], 'nodes': []}},
            'leaf_index_beyond_all_leaves': {0: {'leaves': [10 ** 6], 'nodes': []}},
            'negative_leaf_index': {0: {'leaves': [-1], 'nodes': []}},
            'unknown_rung_key': {5: {'leaves': [0], 'nodes': []}},
            'nodes_wrong_shape': {0: {'leaves': [3], 'nodes': [(0, 2)]}},
        }
        for name, bad in cases.items():
            try:
                if V(lad.rung_roots, lad.rungs, leaves, bad) is not False:
                    accepts.append(name)
            except Exception as e:                                          # noqa: BLE001
                crashes[name] = type(e).__name__
        print('[MTL multiproof catalogue] ACCEPTS=%r CRASHES=%r' % (accepts, crashes))
        self.assertTrue(accepts == [] and crashes == {},
                        'ACCEPT-ON-INVALID multiproof: %r ; raises instead of False: %r' % (accepts, crashes))


# =============================================================================
class LMSProperties(unittest.TestCase):

    @given(st.sampled_from(PAIRS), st.integers(0, 3), st.binary(max_size=64), st.integers(0, 10000), st.integers(1, 255))
    @settings(max_examples=200)
    def test_lms_roundtrip_wrong_message_and_byte_tamper(self, pair, j, other, pos, xor):
        pk, _, sigs = T4SIGS[pair]
        m, sig = sigs[j]
        self.assertEqual(len(sig), T4.lms_sizes(*pair)['sig'])
        self.assertTrue(T4.lms_verify(pk, m, sig))
        if other != m:
            self.assertFalse(T4.lms_verify(pk, other, sig))
        self.assertFalse(T4.lms_verify(pk, m, flip(sig, pos, xor)))          # any single-byte change
        self.assertFalse(T4.lms_verify(flip(pk, pos, xor), m, sig))          # public key change
        self.assertFalse(T4.lms_verify(pk, m, sig[:-1]))
        self.assertFalse(T4.lms_verify(pk, m, sig + b'\x00'))
        self.assertFalse(T4.lms_verify(pk[:-1], m, sig))

    def test_lms_path_q_and_typecode_tamper_every_field(self):
        for pair in PAIRS:
            pk, k, sigs = T4SIGS[pair]
            m, sig = sigs[0]
            ots_len = T4.lmots_sizes(pair[1])['sig']
            for lvl in range(k.h):                                           # every auth-path node
                pos = 8 + ots_len + lvl * k.m
                self.assertFalse(T4.lms_verify(pk, m, flip(sig, pos)), (pair, lvl))
            for q in (1, 31, 32, 1 << 20):                                   # index field
                self.assertFalse(T4.lms_verify(pk, m, struct.pack('>I', q) + sig[4:]))
            bad = bytearray(sig)
            struct.pack_into('>I', bad, 4, (pair[1] % 8) + 1)                # OTS typecode field
            self.assertFalse(T4.lms_verify(pk, m, bytes(bad)))
            bad = bytearray(sig)
            struct.pack_into('>I', bad, 4 + ots_len, (pair[0] % 14) + 1)     # LMS typecode field
            self.assertFalse(T4.lms_verify(pk, m, bytes(bad)))
            self.assertFalse(T4.lms_verify(sig[:4] + pk[4:], m, sig))       # wrong pk typecode
            self.assertFalse(T4.lms_verify(b'', m, sig))
            self.assertFalse(T4.lms_verify(pk, m, b''))

    def test_lms_state_exhaustion(self):
        k = T4.LmsPrivate(5, 4, I=b'\x77' * 16, seed=b'\x55' * 32)
        qs = [struct.unpack('>I', k.sign(b'x')[:4])[0] for _ in range(32)]
        self.assertEqual(qs, list(range(32)))
        with self.assertRaises(RuntimeError):
            k.sign(b'33rd')

    def test_differential_lms_100_cases(self):
        """100 seeded (typecode pair, message) cases: sign with T4 -> verify with hsslms, and sign
        with hsslms -> verify with T4; tampered signatures rejected by both. Any disagreement is a finding."""
        rng = random.Random(2024)
        disagreements = []
        for c in range(100):
            pair = PAIRS[c % len(PAIRS)]
            msg = rng.randbytes(rng.randint(0, 3000))
            t4k = t4_key(pair)
            hsk = hs_key(pair)
            t4pk, hspk = t4k.public_key(), hsk.gen_pub().get_pubkey()
            t4sig, hssig = t4k.sign(msg), hsk.sign(msg)
            row = {
                'T4->hsslms': hs_verify(t4pk, msg, t4sig),
                'hsslms->T4': T4.lms_verify(hspk, msg, hssig),
                'T4->T4': T4.lms_verify(t4pk, msg, t4sig),
                'hsslms->hsslms': hs_verify(hspk, msg, hssig),
                'sizes_equal': (len(t4sig), len(t4pk)) == (len(hssig), len(hspk)) == (T4.lms_sizes(*pair)['sig'], T4.lms_sizes(*pair)['pub']),
            }
            pos = rng.randrange(len(t4sig))
            x = rng.randrange(1, 256)
            row['tamper_T4sig_rejected_by_both'] = (not hs_verify(t4pk, msg, flip(t4sig, pos, x))) and (not T4.lms_verify(t4pk, msg, flip(t4sig, pos, x)))
            row['tamper_hssig_rejected_by_both'] = (not hs_verify(hspk, msg, flip(hssig, pos % len(hssig), x))) and (not T4.lms_verify(hspk, msg, flip(hssig, pos % len(hssig), x)))
            row['wrong_msg_rejected_by_both'] = (not hs_verify(t4pk, msg + b'!', t4sig)) and (not T4.lms_verify(hspk, msg + b'!', hssig))
            if not all(row.values()):
                disagreements.append((c, pair, len(msg), row))
        DIFF_LOG.append(('lms_100', disagreements))
        print('\n[LMS differential] 100 cases over pairs %s: %d disagreements' % (PAIRS, len(disagreements)))
        self.assertEqual(disagreements, [])

    @given(st.sampled_from(PAIRS), st.binary(max_size=2000), st.integers(0, 31))
    @settings(max_examples=40)
    def test_differential_lms_hypothesis(self, pair, msg, q):
        """Hypothesis-driven cross-check (T4 signs with an explicit leaf index so shrinking never
        exhausts its state; hsslms keys are regenerated when exhausted)."""
        pk, key, _ = T4SIGS[pair]
        hsk = hs_key(pair)
        t4sig, hssig = key.sign_with_index(q, msg), hsk.sign(msg)
        self.assertTrue(hs_verify(pk, msg, t4sig), pair)
        self.assertTrue(T4.lms_verify(hsk.gen_pub().get_pubkey(), msg, hssig), pair)

    def test_mixed_n_m_typecodes_FINDING(self):
        """LMS/LM-OTS pairs with different hash lengths (LMS m=32 with LM-OTS n=24 and vice versa)
        are accepted by both constructors (neither enforces m == n). Property asserted: for every
        accepted pair the two implementations interoperate in both directions and each verifies its
        own output. Any failure is a differential finding; the message lists the exact matrix."""
        matrix = {}
        for pair in ((5, 8), (10, 4)):
            pk, key, _ = T4SIGS[pair]
            hsk = hs_key(pair)
            hspk = hsk.gen_pub().get_pubkey()
            t4sig, hssig = key.sign_with_index(7, b'mixed'), hsk.sign(b'mixed')
            matrix[pair] = {
                'len_T4': len(t4sig), 'len_hsslms': len(hssig), 'len_formula_T4': T4.lms_sizes(*pair)['sig'],
                'T4->T4': T4.lms_verify(pk, b'mixed', t4sig),
                'T4->hsslms': hs_verify(pk, b'mixed', t4sig),
                'hsslms->hsslms': hs_verify(hspk, b'mixed', hssig),
                'hsslms->T4': T4.lms_verify(hspk, b'mixed', hssig),
            }
        print('\n[LMS mixed n/m matrix]', matrix)
        for pair, row in matrix.items():
            self.assertTrue(all(v is True for k, v in row.items() if '->' in k), (pair, row))


if __name__ == '__main__':
    unittest.main(verbosity=2)
