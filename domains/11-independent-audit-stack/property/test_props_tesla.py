#!/usr/bin/env python3
"""Property / malformed-input layer for T5 = pq_infra_s4_embedded_broadcast_v2.0.py
(TeslaSender / TeslaReceiver, RFC 4082-style delayed key disclosure).

Packet = u32 interval || payload || MAC_16(K_i, u32||payload) || K_{i-d} (32 B, present iff i-d >= 1).
Receiver: receive(packet, receiver_interval); accepted = [(i, payload)], rejected = [(i, reason)].

Known bugs from the earlier audit are REPRODUCED here as expectedFailure tests:
  S4-004  pending packets are stranded under loss (a lost disclosure packet i+d strands interval i
          forever, although K_i is derivable from any later disclosed key by hashing);
  S4-005  the replay filter is populated BEFORE authentication: an attacker who can predict a
          packet body suppresses the genuine packet ('replay') without knowing any key.

Run:  python3 -m pytest -q test_props_tesla.py   or   python3 test_props_tesla.py
"""
import importlib.util
import os
import sys
import unittest

sys.dont_write_bytecode = True
from hypothesis import HealthCheck, given, settings, strategies as st

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


T5 = _load('s4_audit', 'pq_infra_s4_embedded_broadcast_v2.0.py')
H, NB, MAC = T5.H, T5.N, T5._mac

settings.register_profile('audit', deadline=None, derandomize=True, print_blob=True,
                          suppress_health_check=list(HealthCheck))
settings.load_profile('audit')


def payload(i):
    return b'telemetry-%03d' % i


def setup(L, d, sync=0, seed=b'sat-1'):
    s = T5.TeslaSender(seed, L, d)
    r = T5.TeslaReceiver(s.anchor, L, d, sync)
    pk = {i: s.send(i, payload(i)) for i in range(1, L + 1)}
    return s, r, pk


def flip(b, i, x=1):
    a = bytearray(b)
    a[i % len(a)] ^= x or 1
    return bytes(a)


def forge(kind, s, i, L, d, data):
    """Attacker packets whose body never equals a genuine body (genuine bodies are covered by
    the S4-005 reproduction). The attacker knows all keys already disclosed (K_j, j <= i-d-1)."""
    if kind == 'random':
        return data.draw(st.binary(min_size=0, max_size=80))
    tgt = i if kind != 'future' else min(L, i + 1)
    body = tgt.to_bytes(4, 'big') + b'ATTACK-' + payload(tgt)
    if kind == 'flip_body':                                      # genuine packet, one payload byte flipped
        g = s.send(i, payload(i))
        return flip(g, 4 + data.draw(st.integers(0, len(payload(i)) - 1)), data.draw(st.integers(1, 255)))
    if kind == 'wrong_index':                                    # genuine packet with the index rewritten
        g = s.send(i, payload(i))
        j = data.draw(st.integers(1, L).filter(lambda x: x != i))
        return j.to_bytes(4, 'big') + g[4:]
    if kind in ('old_key_mac', 'future'):                        # MAC under the newest disclosed key
        j = i - d - 1                                            # K_j is public once packet i-1 is out
        key = s.keys[j] if j >= 1 else H(b'attacker-guess', bytes([i]))
        disclosed = s.keys[tgt - d] if tgt - d >= 1 else b''
        return body + MAC(key, body, 16) + disclosed
    if kind == 'junk_key':                                       # good-looking packet, junk MAC and key
        return body + bytes(16) + H(b'junk', bytes([i]))
    raise ValueError(kind)


# =============================================================================
class TeslaProperties(unittest.TestCase):

    @given(st.integers(6, 40), st.integers(1, 4), st.integers(0, 4))
    @settings(max_examples=80)
    def test_genuine_accepted_after_disclosure(self, L, d, sync):
        """Perfectly timed receiver (receiver_interval == i): with sync < d every interval whose key
        is disclosed within the chain (i <= L-d) is accepted exactly once with its payload; the last
        d stay pending; with sync >= d the safety condition refuses everything."""
        s, r, pk = setup(L, d, sync)
        for i in range(1, L + 1):
            r.receive(pk[i], i)
        if sync < d:
            self.assertEqual(sorted(r.accepted), [(i, payload(i)) for i in range(1, L - d + 1)])
            self.assertEqual(sorted(r.pending), list(range(L - d + 1, L + 1)))
            self.assertEqual(r.rejected, [])
        else:
            self.assertEqual(r.accepted, [])
            self.assertTrue(all(why == 'key may already be disclosed' for _, why in r.rejected))

    @given(st.integers(6, 30), st.integers(1, 3), st.data())
    @settings(max_examples=150)
    def test_forgeries_never_accepted_and_do_not_block_genuine(self, L, d, data):
        """Interleave up to two attacker packets before each genuine one. Safety: accepted is a
        subset of the genuine (i, payload) set. Liveness (bodies differ from genuine): every
        i <= L-d is still accepted."""
        s, r, pk = setup(L, d)
        genuine = {(i, payload(i)) for i in range(1, L + 1)}
        for i in range(1, L + 1):
            for _ in range(data.draw(st.integers(0, 2))):
                kind = data.draw(st.sampled_from(['random', 'flip_body', 'wrong_index', 'old_key_mac', 'future', 'junk_key']))
                r.receive(forge(kind, s, i, L, d, data), i)
            r.receive(pk[i], i)
        self.assertTrue(set(r.accepted) <= genuine, set(r.accepted) - genuine)
        self.assertEqual(len(r.accepted), len(set(r.accepted)))
        self.assertEqual(sorted(r.accepted), [(i, payload(i)) for i in range(1, L - d + 1)])

    @given(st.integers(4, 30), st.integers(1, 3), st.integers(0, 3), st.integers(0, 255))
    @settings(max_examples=150)
    def test_bit_flips_in_body_or_tag_never_accepted(self, L, d, pos, xor):
        """Any single-byte change inside the authenticated part (index || payload || MAC) of a genuine
        packet is never accepted (a flip in the trailing disclosed key only spoils the key)."""
        s, r, pk = setup(L, d)
        i = 1 + (pos % L)
        auth_len = 4 + len(payload(i)) + 16
        j = xor % auth_len
        bad = flip(pk[i], j, (xor | 1))
        r.receive(bad, i)
        for k in range(1, L + 1):                                  # let every key be disclosed
            r.receive(pk[k], k)
        tail = 16 + (NB if i - d >= 1 else 0)
        bad_body = bad[:-tail]
        self.assertNotIn((int.from_bytes(bad_body[:4], 'big'), bad_body[4:]), set(r.accepted))
        self.assertTrue(set(r.accepted) <= {(k, payload(k)) for k in range(1, L + 1)})

    @given(st.integers(4, 30), st.integers(1, 3), st.integers(1, 30))
    @settings(max_examples=100)
    def test_replay_rejected(self, L, d, which):
        s, r, pk = setup(L, d)
        for i in range(1, L + 1):
            r.receive(pk[i], i)
        i = 1 + (which % L)
        before = list(r.accepted)
        r.receive(pk[i], L)                                        # exact replay, any time
        r.receive(pk[i], i)
        self.assertEqual(r.rejected.count((i, 'replay')), 2)
        self.assertEqual(r.accepted, before)

    @given(st.integers(4, 30), st.integers(1, 3), st.integers(0, 2), st.integers(1, 30), st.integers(0, 10))
    @settings(max_examples=100)
    def test_late_rejected(self, L, d, sync, which, lateness):
        """A packet for interval i arriving when receiver_interval + sync >= i + d is refused as
        'key may already be disclosed' and never accepted, even if its key is disclosed later."""
        s, r, pk = setup(L, d, sync)
        i = 1 + (which % L)
        t = i + d - sync + lateness
        r.receive(pk[i], t)
        self.assertIn((i, 'key may already be disclosed'), r.rejected)
        self.assertNotIn(i, r.pending)
        for k in range(i + 1, L + 1):
            r.receive(pk[k], max(k, t))
        self.assertNotIn((i, payload(i)), r.accepted)

    def test_out_of_range_and_short_packets(self):
        L, d = 10, 2
        s, r, pk = setup(L, d)
        for i in (0, L + 1, 1 << 31):
            r.receive(i.to_bytes(4, 'big') + b'x' * 60, 1)
            self.assertIn((i, 'range'), r.rejected)
        for junk in (b'', b'\x00', b'\x00\x00\x00\x03', b'\x00\x00\x00\x03' + b'a' * 10):
            r.receive(junk, 1)
        for i in range(1, L + 1):
            r.receive(pk[i], i)
        self.assertEqual(sorted(r.accepted), [(i, payload(i)) for i in range(1, L - d + 1)])

    @given(st.binary(max_size=120), st.integers(0, 40))
    @settings(max_examples=200)
    def test_random_packets_never_accepted_and_never_crash(self, pkt, t):
        s = T5.TeslaSender(b'seed', 32, 2)
        r = T5.TeslaReceiver(s.anchor, 32, 2, 0)
        r.receive(pkt, t)
        self.assertEqual(r.accepted, [])

    # ------------------------------------------------------ known-bug reproductions
    @unittest.expectedFailure
    def test_S4_004_stranded_pending_packets_under_loss(self):
        """S4-004: packet 5 (which discloses K_3) is lost. Packet 6 discloses K_4 and K_3 = H(K_4)
        is therefore known to the receiver, yet interval 3 is never released from pending.
        Expected (RFC 4082 semantics): (3, payload) accepted once any later key is disclosed."""
        L, d = 20, 2
        s, r, pk = setup(L, d)
        for i in range(1, L + 1):
            if i != 5:
                r.receive(pk[i], i)
        self.assertEqual(H(b'tesla-chain', r.known[4]), s.keys[3])         # receiver holds K_4 -> K_3
        self.assertIn((3, payload(3)), r.accepted,
                      'stranded: pending=%r accepted_intervals=%r' % (sorted(r.pending), sorted(i for i, _ in r.accepted)))

    @unittest.expectedFailure
    def test_S4_005_unauthenticated_replay_filter_dos(self):
        """S4-005: an attacker who predicts the body of packet 5 sends (5, body) with a junk MAC and
        junk key BEFORE the genuine packet; the genuine packet is then dropped as 'replay'. No key
        material is needed. Expected: the genuine (5, payload) is accepted after K_5 is disclosed."""
        L, d = 20, 2
        s, r, pk = setup(L, d)
        for i in range(1, 5):
            r.receive(pk[i], i)
        body = (5).to_bytes(4, 'big') + payload(5)
        r.receive(body + bytes(16) + H(b'junk'), 5)                       # attacker, no keys
        r.receive(pk[5], 5)                                               # genuine
        for i in range(6, L + 1):
            r.receive(pk[i], i)
        self.assertIn((5, payload(5)), r.accepted, 'rejected=%r' % [x for x in r.rejected if x[0] == 5])

    def test_S4_005_mechanism_is_unauthenticated_filter_observation(self):
        """Observation supporting S4-005: the 'seen' filter grows with unauthenticated garbage
        (one entry per distinct (interval, body) received, keys or not)."""
        s, r, pk = setup(10, 2)
        for k in range(200):
            r.receive((3).to_bytes(4, 'big') + b'g%03d' % k + bytes(16) + bytes(NB), 3)
        self.assertGreaterEqual(len(r.seen), 200)
        self.assertGreaterEqual(sum(len(v) for v in r.pending.values()), 200)   # and pending grows too
        self.assertEqual(r.accepted, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
