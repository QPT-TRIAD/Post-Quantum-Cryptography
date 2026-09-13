#!/usr/bin/env python3
r"""PQ infrastructure program — step S4: ICS / embedded / satellite / medical.

The blocker is not CPU, it is the LINK: LoRa frames of 51 B, Iridium SBD of 340 B,
9.6 kbps serial, CAN-FD 64 B, BLE 244 B. A 4,627-byte ML-DSA-87 signature is 91
LoRa frames; even the 1,772-byte LMS signature is 35. And these devices are
receivers of authenticated BROADCAST (firmware, commands, telemetry, GNSS-style
navigation data) far more often than they are signers.

Glued ideas (stated, then measured):
  G1  LM-OTS with w=8 (SP 800-208 / RFC 8554, LMOTS_SHA256_N32_W8): 34 chains
      instead of 67, so the one-time part is 1,088 B; full LMS h=20 = 1,772 B.
      Same second-preimage security at n=32 (2^128 quantum preimage: QPT-128
      eligible). Trade: ~8.5k hashes per verify instead of ~1k.
  G2  TESLA delayed-key-disclosure broadcast authentication [Perrig–Canetti–
      Tygar–Song 2000/2002; RFC 4082] — the mechanism Galileo OSNMA deploys —
      widened from 128-bit to 256-bit chain keys so the chain's one-wayness is
      a 2^128 quantum preimage. Per message: 4 B index + 16 B MAC + 32 B
      disclosed key. One hash-based signature anchors a chain of 2^16 keys.
      Security (RFC 4082 §3.3; Perrig et al.): if the receiver knows the key
      K_i had not yet been disclosed when the packet arrived (loose time sync
      with bound d), forging requires either a MAC forgery (online, 2^-t per
      try, no offline Grover advantage) or a preimage of the chain hash.
  G3  Amortisation: TESLA is only worth it because the anchor signature is
      paid once per chain; the per-message overhead is then 52 B, i.e. one
      LoRa frame, so authenticated broadcast fits the link where NO PQ
      signature does.

Everything here is executed: a parametric Winternitz OTS (w=16 and w=256) with
exact hash counts, a TESLA sender/receiver with time-sync enforcement, replay
and late-key rejection, and a link-budget table. `--self-test`, `--report`.
"""

import argparse
import hashlib
import hmac
import importlib.util
import json
import math
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('s1s2', os.path.join(_HERE, 's1s2_hashsig_dnssec-v2.0.py'))
s1s2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s1s2)
H, N = s1s2.H, s1s2.N_BYTES


# --------------------------------------------- G1: parametric Winternitz ----
class WOTS:
    def __init__(self, w):
        assert w in (16, 256)
        self.w = w
        self.lg = int(math.log2(w))
        self.len1 = (8 * N) // self.lg
        self.len2 = math.floor(math.log2(self.len1 * (w - 1)) / self.lg) + 1
        self.len = self.len1 + self.len2

    def digits(self, d):
        out = []
        if self.w == 16:
            for b in d:
                out += [b >> 4, b & 0xF]
        else:
            out = list(d)
        csum = sum(self.w - 1 - x for x in out)
        cs = []
        for _ in range(self.len2):
            cs.append(csum % self.w)
            csum //= self.w
        return out + cs[::-1]

    def chain(self, x, start, steps, ps, addr, i):
        for s in range(start, start + steps):
            x = H(b'ch', ps, addr, i.to_bytes(2, 'big'), s.to_bytes(2, 'big'), x)
        return x

    def keygen(self, seed, ps, addr):
        sk = [H(b'sk', seed, addr, i.to_bytes(2, 'big')) for i in range(self.len)]
        pk = [self.chain(sk[i], 0, self.w - 1, ps, addr, i) for i in range(self.len)]
        return sk, H(b'pk', ps, addr, *pk)

    def sign(self, d, sk, ps, addr):
        dg = self.digits(d)
        return [self.chain(sk[i], 0, dg[i], ps, addr, i) for i in range(self.len)]

    def pk_from_sig(self, d, sig, ps, addr):
        dg = self.digits(d)
        return H(b'pk', ps, addr, *[self.chain(sig[i], dg[i], self.w - 1 - dg[i], ps, addr, i) for i in range(self.len)])

    def sig_bytes(self, h, fmt='lms'):
        if fmt == 'lms':    # RFC 8554: q + (ots type + C + p*n) + lms type + path
            return 4 + (4 + N + self.len * N) + 4 + h * N
        return 4 + N + self.len * N + h * N              # RFC 8391 XMSS: idx + r + chains + path

    def verify_hashes_max(self, h):
        return self.len * (self.w - 1) + 1 + h + 1


GATES_PER_HASH_QUERY = 2 ** 18      # QPT-128 gate accounting floor (v1.43)
QPT128_GATE_BUDGET = 2 ** 128


def qpt128_hash_preimage_ok(n_bits):
    """A hash-based signature's security rests on (second-)preimage resistance of
    an n-bit hash: Grover needs 2^(n/2) queries. QPT-128 (D1): an attacker with
    fewer than 2^128 gates must have success probability < 1/3."""
    grover_gates = 2 ** (n_bits // 2) * GATES_PER_HASH_QUERY
    return grover_gates >= QPT128_GATE_BUDGET


# --------------------------------------------------- G2: TESLA broadcast ----
def _mac(key, msg, tag_len):
    return hmac.new(key, msg, hashlib.sha3_256).digest()[:tag_len]


class TeslaSender:
    def __init__(self, seed, chain_len, disclosure_delay, tag_len=16):
        self.L, self.d, self.tag_len = chain_len, disclosure_delay, tag_len
        keys = [H(b'tesla-seed', seed)]
        for _ in range(chain_len):
            keys.append(H(b'tesla-chain', keys[-1]))
        self.keys = keys[::-1]                 # keys[0] = anchor (public), keys[i+1] -> keys[i]
        self.anchor = self.keys[0]

    def send(self, interval, payload):
        assert 1 <= interval <= self.L
        k = self.keys[interval]
        disclosed = self.keys[interval - self.d] if interval - self.d >= 1 else b''
        body = interval.to_bytes(4, 'big') + payload
        return body + _mac(k, body, self.tag_len) + disclosed

    @staticmethod
    def overhead_bytes(tag_len=16):
        return 4 + tag_len + N


class TeslaReceiver:
    """Loose time sync: receiver clock may lead the sender's by at most `sync`
    intervals. A packet for interval i is accepted for later verification only
    if, at receipt, the sender cannot yet have disclosed K_i (RFC 4082 §3.5)."""

    def __init__(self, anchor, chain_len, disclosure_delay, sync, tag_len=16):
        self.anchor, self.L, self.d, self.sync, self.tag_len = anchor, chain_len, disclosure_delay, sync, tag_len
        self.known = {0: anchor}
        self.pending = {}
        self.accepted, self.rejected = [], []
        self.seen = set()

    def _authenticate_key(self, i, k):
        # walk from k back to the latest known key
        j = max(x for x in self.known if x <= i)
        x = k
        for _ in range(i - j):
            x = H(b'tesla-chain', x)
        if x != self.known[j]:
            return False
        self.known[i] = k
        return True

    def receive(self, packet, receiver_interval):
        i = int.from_bytes(packet[:4], 'big')
        body, tag = packet[:-(self.tag_len + N)] if len(packet) >= 4 + self.tag_len + N else (None, None), None
        if i < 1 or i > self.L:
            self.rejected.append((i, 'range')); return
        has_disc = i - self.d >= 1
        tail = self.tag_len + (N if has_disc else 0)
        body, tag = packet[:-tail], packet[-tail:-tail + self.tag_len] if has_disc else packet[-tail:]
        disclosed = packet[-N:] if has_disc else b''
        if (i, body) in self.seen:
            self.rejected.append((i, 'replay')); return
        self.seen.add((i, body))
        # safety condition: sender may have disclosed K_i only at interval i + d
        if receiver_interval + self.sync >= i + self.d:
            self.rejected.append((i, 'key may already be disclosed')); return
        self.pending.setdefault(i, []).append((body, tag))
        if has_disc:
            j = i - self.d
            if self._authenticate_key(j, disclosed):
                for b, t in self.pending.pop(j, []):
                    if hmac.compare_digest(_mac(disclosed, b, self.tag_len), t):
                        self.accepted.append((j, b[4:]))
                    else:
                        self.rejected.append((j, 'bad mac'))
            else:
                self.rejected.append((j, 'bad disclosed key'))


# ------------------------------------------------------ link budget --------
LINKS = {  # payload bytes per frame, frames per second (order of magnitude)
    'LoRa SF12 (EU868)':   (51, 0.5),
    'Iridium SBD':         (340, 0.05),
    'BLE 5 (DLE)':         (244, 100.0),
    'CAN-FD':              (64, 5000.0),
    '9.6 kbps serial':     (1200, 1.0),
    'NB-IoT (typ.)':       (1200, 10.0),
}
ARTIFACTS = {
    'ML-DSA-87 signature':        4627,
    'XMSS-SHA256 w16 h20 (S1)':   None,     # filled from WOTS(16)
    'LMS w8 h20 (G1)':            None,     # filled from WOTS(256)
    'SQIsign-V signature':        292,
    'TESLA per-message (G2)':     TeslaSender.overhead_bytes(),
    'TESLA anchor (LMS w8, once per 2^16 msgs)': None,
}


def link_table():
    w16, w256 = WOTS(16), WOTS(256)
    art = dict(ARTIFACTS)
    art['XMSS-SHA256 w16 h20 (S1)'] = w16.sig_bytes(20, 'xmss')
    art['LMS w8 h20 (G1)'] = w256.sig_bytes(20)
    art['TESLA anchor (LMS w8, once per 2^16 msgs)'] = w256.sig_bytes(20)
    rows = {}
    for a, nb in art.items():
        rows[a] = {'bytes': nb}
        for link, (mtu, fps) in LINKS.items():
            frames = -(-nb // mtu)
            rows[a][link] = {'frames': frames, 'seconds': round(frames / fps, 2)}
    return rows


# ----------------------------------------------------------------- tests ----
class Tests(unittest.TestCase):
    def test_g1_wots_params_match_rfc8554_lmots_w8(self):
        w = WOTS(256)
        self.assertEqual((w.len1, w.len2, w.len), (32, 2, 34))    # LMOTS_SHA256_N32_W8: p = 34
        self.assertEqual(w.sig_bytes(20), 1772)                    # RFC 8554 LMS h=20 w=8: 1,772 B
        self.assertEqual(WOTS(16).len, 67)
        self.assertEqual(WOTS(16).sig_bytes(20, 'xmss'), 2820)     # RFC 8391 XMSS-SHA2_20_256

    def test_g1_qpt128_needs_n32_not_nsa_preferred_n24(self):
        # CNSA 2.0 FAQ v2.1 p.7: "NSA's preferred parameter set is ... LMS with
        # SHA-256/192".  Under QPT-128 gate accounting that set fails; n=32 passes.
        self.assertFalse(qpt128_hash_preimage_ok(192))
        self.assertTrue(qpt128_hash_preimage_ok(256))
        self.assertEqual(2 ** 96 * GATES_PER_HASH_QUERY, 2 ** 114)   # 14 bits inside the budget

    def test_g1_w256_roundtrip_hashcount(self):
        for w in (WOTS(16), WOTS(256)):
            sk, pk = w.keygen(b's' * 32, b'p' * 32, b'\x00\x00\x00\x01')
            d = H(b'firmware blob')
            sig = w.sign(d, sk, b'p' * 32, b'\x00\x00\x00\x01')
            s1s2.hash_calls_reset()
            self.assertEqual(w.pk_from_sig(d, sig, b'p' * 32, b'\x00\x00\x00\x01'), pk)
            self.assertLessEqual(s1s2.hash_calls(), w.verify_hashes_max(0))
            self.assertNotEqual(w.pk_from_sig(H(b'other'), sig, b'p' * 32, b'\x00\x00\x00\x01'), pk)
        # w=256 shrinks the signature ~37% and costs ~8x the verify hashes
        self.assertLess(WOTS(256).sig_bytes(20), 0.65 * WOTS(16).sig_bytes(20, 'xmss'))
        self.assertGreater(WOTS(256).verify_hashes_max(20), 8 * WOTS(16).verify_hashes_max(20))

    def test_g2_tesla_accepts_genuine_rejects_forgery_replay_late(self):
        L, d, sync = 64, 2, 0
        s = TeslaSender(b'sat-1', L, d)
        r = TeslaReceiver(s.anchor, L, d, sync)
        pkts = {i: s.send(i, b'telemetry-%02d' % i) for i in range(1, 12)}
        for i in range(1, 12):
            r.receive(pkts[i], receiver_interval=i)
        got = dict(r.accepted)
        self.assertEqual(sorted(got), list(range(1, 10)))        # 10, 11 still pending (keys not disclosed)
        self.assertEqual(got[5], b'telemetry-05')
        # replay
        r.receive(pkts[3], receiver_interval=3)
        self.assertIn((3, 'replay'), r.rejected)
        # forgery: attacker knows disclosed keys only; tries to spoof interval 12 with key of 9
        forged = (12).to_bytes(4, 'big') + b'ATTACK'
        pkt = forged + _mac(s.keys[9], forged, 16) + s.keys[10]
        r.receive(pkt, receiver_interval=12)
        s2 = s.send(13, b'ok'); r.receive(s2, 13); s3 = s.send(14, b'ok'); r.receive(s3, 14)
        self.assertNotIn(12, dict(r.accepted))
        self.assertTrue(any(i == 12 and why == 'bad mac' for i, why in r.rejected))
        # late packet: arrives when its key could already be public -> refused
        late = s.send(20, b'late')
        r.receive(late, receiver_interval=22)
        self.assertIn((20, 'key may already be disclosed'), r.rejected)
        # bad disclosed key
        bad = pkts[11][:-N] + H(b'junk')
        r2 = TeslaReceiver(s.anchor, L, d, sync)
        r2.receive(bad, 11)
        self.assertIn((9, 'bad disclosed key'), r2.rejected)

    def test_g3_link_budget(self):
        t = link_table()
        self.assertEqual(t['LMS w8 h20 (G1)']['bytes'], 1772)
        self.assertEqual(t['TESLA per-message (G2)']['bytes'], 52)
        self.assertEqual(t['TESLA per-message (G2)']['LoRa SF12 (EU868)']['frames'], 2)   # 4 B header pushes it
        self.assertEqual(t['ML-DSA-87 signature']['LoRa SF12 (EU868)']['frames'], 91)
        self.assertEqual(t['LMS w8 h20 (G1)']['LoRa SF12 (EU868)']['frames'], 35)
        self.assertEqual(t['SQIsign-V signature']['LoRa SF12 (EU868)']['frames'], 6)


def report():
    return {'wots': {f'w={w}': {'len': WOTS(w).len, 'sig_h20_lms': WOTS(w).sig_bytes(20),
                                'sig_h20_xmss': WOTS(w).sig_bytes(20, 'xmss'),
                                'verify_hashes_max_h20': WOTS(w).verify_hashes_max(20)} for w in (16, 256)},
            'qpt128_hash_length': {'n=192 (NSA-preferred LMS SHA-256/192)': qpt128_hash_preimage_ok(192),
                                   'n=256': qpt128_hash_preimage_ok(256)},
            'tesla_overhead_per_message': TeslaSender.overhead_bytes(),
            'tesla_amortised_per_message_2^16': round(TeslaSender.overhead_bytes() + WOTS(256).sig_bytes(20) / 65536, 2),
            'links': link_table()}


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
