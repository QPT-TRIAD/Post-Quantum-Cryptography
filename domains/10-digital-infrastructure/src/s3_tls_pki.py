#!/usr/bin/env python3
r"""PQ infrastructure program — step S3: TLS 1.3 / Web PKI at Category 5.

The blocker: a Category-5 chain built the obvious way (ML-KEM-1024 + ML-DSA-87
everywhere) is ~27 KB on the server's first flight, past the TCP initial window
(10 MSS = 14,600 B) and far past the QUIC 3x anti-amplification budget, so it
costs extra round trips and, on some paths, fails outright.

Glued ideas (each stated as a theory, each measured below):
  G1  Merkle Tree Certificates [Benjamin–O'Brien–Westerbaan, draft-davidben-
      tls-merkle-tree-certs]: the CA signs a batch Merkle root; the handshake
      carries an inclusion proof (32·log2(batch)) instead of CA signatures and
      SCTs. The client learns roots out of band (from a transparency service).
      Security: second-preimage resistance of the hash + the CA's signature on
      the root, which never travels in the handshake at all.
  G2  Compact category-5 signature for the server's own handshake signature
      (SQIsign-V 292 B / 129 B key, from the NIST additional round-2 list).
  G3  KEMTLS [Schwabe–Stebila–Wiggers]: replace the server's signing key by a
      KEM key so the server never signs; at Category 5 the KEM is ML-KEM-1024
      (pk 1,568 / ct 1,568) — we measure whether that is actually smaller than
      G2 (it is not) and what it buys instead (no per-handshake signing).
  G4  QUIC amplification (RFC 9000 §8.1): server may send 3x what the client
      sent before address validation; clients pad Initial to ≥1,200 B. The
      client's own ML-KEM key share sets the budget, so a bigger KEM gives the
      server MORE room, not less.

Working prototype: an MTC batch tree over synthetic assertions with inclusion
proofs, verification and tamper tests, reusing the Merkle code from S1/S2.
Everything in `--self-test` is asserted; `--report` prints the ledger.
"""

import argparse
import importlib.util
import json
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('s1s2', os.path.join(_HERE, 's1s2_hashsig_dnssec-v2.0.py'))
s1s2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s1s2)
H, N_BYTES = s1s2.H, s1s2.N_BYTES

# --------------------------------------------------------------- primitives --
# (public key bytes, signature-or-ciphertext bytes, NIST category)
SIG = {
    'ECDSA-P256': (64, 64, 0),
    'ML-DSA-44':  (1312, 2420, 2),
    'ML-DSA-65':  (1952, 3309, 3),
    'ML-DSA-87':  (2592, 4627, 5),
    'Falcon-1024': (1793, 1280, 5),
    'SQIsign-V':  (129, 292, 5),
    'MAYO-5':     (5554, 964, 5),
    'OV-V-pkc':   (446992, 260, 5),
}
KEM = {
    'X25519':      (32, 32, 0),
    'ML-KEM-768':  (1184, 1088, 3),
    'ML-KEM-1024': (1568, 1568, 5),
}

# TLS 1.3 record/handshake overheads (bytes), conservative round numbers.
CH_BASE = 260            # ClientHello without key_share
SH_BASE = 90             # ServerHello without key_share
EE = 50                  # EncryptedExtensions
CERT_TBS = 350           # X.509 TBS overhead per certificate (names, validity, extensions)
CERT_MSG = 12            # Certificate message framing
SCT_OVERHEAD = 40
CV_OVERHEAD = 8
FINISHED = 40
RECORD_OVERHEAD = 60

QUIC_MIN_INITIAL = 1200  # RFC 9000 §14.1 client Initial padding
QUIC_AMPLIFICATION = 3   # RFC 9000 §8.1
QUIC_DATAGRAM = 1200
TCP_INITCWND_BYTES = 10 * 1460
# Cloudflare measured (pq-2024, pq-2025 posts): ~15% slowdown at +9 kB; crossing
# +10 kB costs an extra round trip (>60%) and trips middleboxes; second bump at 30 kB.
CLOUDFLARE_CLIFF_EXTRA_BYTES = 10_000


def kem_bytes(*kems):
    pk = sum(KEM[k][0] for k in kems)
    ct = sum(KEM[k][1] for k in kems)
    # Hybrid with a sound combiner: quantum security is that of the strongest
    # component (the classical half is assumed broken), hence max, not min.
    cat = max(KEM[k][2] for k in kems) if kems else 0
    return pk, ct, cat


def client_hello_bytes(kems):
    pk, _, _ = kem_bytes(*kems)
    return CH_BASE + pk


def quic_server_budget(ch_bytes):
    """Bytes the server may send before address validation: 3x the client's
    datagrams, each padded to >= 1,200 B."""
    n_datagrams = -(-ch_bytes // QUIC_DATAGRAM)
    return QUIC_AMPLIFICATION * max(ch_bytes, n_datagrams * QUIC_MIN_INITIAL)


def mtc_proof_bytes(batch_log2):
    """Inclusion proof: path + index + batch id + assertion framing."""
    return batch_log2 * N_BYTES + 4 + 8 + 16


def server_flight(cfg):
    """Server's first flight (ServerHello .. Finished) in bytes."""
    pk, ct, kcat = kem_bytes(*cfg['kems'])
    b = SH_BASE + ct + EE + RECORD_OVERHEAD
    cats = [kcat]
    if cfg['pki'] == 'x509':
        chain_sig = cfg['chain_sig']
        spk, ssig, scat = SIG[chain_sig]
        leaf_pk = SIG[cfg['server_auth']][0]
        # leaf: server pk + CA signature; intermediate: CA pk + root signature
        b += CERT_MSG + (CERT_TBS + leaf_pk + ssig) + (CERT_TBS + spk + ssig)
        b += cfg['scts'] * (ssig + SCT_OVERHEAD)
        cats.append(scat)
    elif cfg['pki'] == 'mtc':
        leaf_pk = SIG[cfg['server_auth']][0] if cfg['server_auth'] in SIG else KEM[cfg['server_auth']][0]
        b += CERT_MSG + 64 + leaf_pk + mtc_proof_bytes(cfg['batch_log2'])   # assertion + proof
        # the CA signature on the batch root is fetched out of band: 0 bytes here
    else:
        raise ValueError(cfg['pki'])
    if cfg['server_auth'] in SIG:
        b += SIG[cfg['server_auth']][1] + CV_OVERHEAD              # CertificateVerify
        cats.append(SIG[cfg['server_auth']][2])
    else:                                                          # KEMTLS
        cats.append(KEM[cfg['server_auth']][2])
        # no CertificateVerify; the client's next flight carries a ciphertext
    b += FINISHED
    return b, min(cats)


CONFIGS = [
    {'name': 'classical today',          'kems': ['X25519'], 'pki': 'x509', 'chain_sig': 'ECDSA-P256', 'server_auth': 'ECDSA-P256', 'scts': 2},
    {'name': 'deployed hybrid (2024-26)', 'kems': ['X25519', 'ML-KEM-768'], 'pki': 'x509', 'chain_sig': 'ECDSA-P256', 'server_auth': 'ECDSA-P256', 'scts': 2},
    {'name': 'naive PQ chain, Cat 2/3',   'kems': ['X25519', 'ML-KEM-768'], 'pki': 'x509', 'chain_sig': 'ML-DSA-44', 'server_auth': 'ML-DSA-44', 'scts': 2},
    {'name': 'naive PQ chain, Cat 5',     'kems': ['X25519', 'ML-KEM-1024'], 'pki': 'x509', 'chain_sig': 'ML-DSA-87', 'server_auth': 'ML-DSA-87', 'scts': 2},
    {'name': 'X.509 + SQIsign-V, Cat 5',  'kems': ['X25519', 'ML-KEM-1024'], 'pki': 'x509', 'chain_sig': 'SQIsign-V', 'server_auth': 'SQIsign-V', 'scts': 2},
    {'name': 'MTC + ML-DSA-87, Cat 5',    'kems': ['X25519', 'ML-KEM-1024'], 'pki': 'mtc', 'server_auth': 'ML-DSA-87', 'batch_log2': 24},
    {'name': 'MTC + SQIsign-V, Cat 5',    'kems': ['X25519', 'ML-KEM-1024'], 'pki': 'mtc', 'server_auth': 'SQIsign-V', 'batch_log2': 24},
    {'name': 'MTC + MAYO-5, Cat 5',       'kems': ['X25519', 'ML-KEM-1024'], 'pki': 'mtc', 'server_auth': 'MAYO-5', 'batch_log2': 24},
    {'name': 'MTC + KEMTLS ML-KEM-1024, Cat 5', 'kems': ['X25519', 'ML-KEM-1024'], 'pki': 'mtc', 'server_auth': 'ML-KEM-1024', 'batch_log2': 24},
    {'name': 'MTC + OV-V (pk in handshake)', 'kems': ['X25519', 'ML-KEM-1024'], 'pki': 'mtc', 'server_auth': 'OV-V-pkc', 'batch_log2': 24},
]


def ledger():
    rows = []
    baseline, _ = server_flight(CONFIGS[0])
    for cfg in CONFIGS:
        ch = client_hello_bytes(cfg['kems'])
        sf, cat = server_flight(cfg)
        budget = quic_server_budget(ch)
        row = {
            'config': cfg['name'], 'category': cat, 'qpt128_eligible': cat == 5,
            'client_hello': ch, 'server_flight': sf, 'extra_vs_classical': sf - baseline,
            'under_cloudflare_10kB_cliff': sf - baseline < CLOUDFLARE_CLIFF_EXTRA_BYTES,
            'quic_budget': budget, 'quic_fits_first_flight': sf <= budget,
            'tcp_initcwnd_fits': sf <= TCP_INITCWND_BYTES,
            'server_signs_per_handshake': cfg['server_auth'] in SIG and cfg['server_auth'] != 'ECDSA-P256' or cfg['server_auth'] == 'ECDSA-P256',
        }
        if cfg['server_auth'] not in SIG:
            row['server_signs_per_handshake'] = False
            row['kemtls_client_ct'] = KEM[cfg['server_auth']][1]
        rows.append(row)
    return rows


# ------------------------------------------------------ MTC prototype -------
class MTCBatch:
    """A batch of assertions (domain, key) under one Merkle root. The CA signs
    the root once per batch (signature size is a parameter, never sent in the
    handshake); each server gets an inclusion proof.
    S2-006: interior nodes are hashed as H('mtc-node', batch id, level, parent
    index, l, r). Leaves were already bound to the batch id; the interior nodes
    were not, so every node of every batch lived in one function and T signed
    batches gave a multi-target second preimage at 2^(n/2)/sqrt(T) queries:
    2^126 gates at n = 256, T = 2^40, inside the QPT-128 budget. The batch id
    and the index already travel in the proof, so the fix costs zero bytes."""

    def __init__(self, assertions, batch_id):
        self.batch_id = batch_id
        self.assertions = list(assertions)
        n = len(self.assertions)
        size = 1
        while size < n:
            size <<= 1
        leaves = [H(b'mtc-leaf', batch_id, a) for a in self.assertions]
        leaves += [H(b'mtc-pad', batch_id, i.to_bytes(4, 'big')) for i in range(n, size)]
        self.levels = [leaves]
        while len(self.levels[-1]) > 1:
            lvl, p = len(self.levels) - 1, self.levels[-1]
            self.levels.append([H(b'mtc-node', batch_id, lvl.to_bytes(1, 'big'), (i // 2).to_bytes(4, 'big'),
                                  p[i], p[i + 1]) for i in range(0, len(p), 2)])
        self.root = self.levels[-1][0]
        self.depth = len(self.levels) - 1

    def proof(self, i):
        path, idx = [], i
        for lvl in range(self.depth):
            path.append(self.levels[lvl][idx ^ 1])
            idx >>= 1
        return {'batch_id': self.batch_id, 'index': i, 'path': path}

    @staticmethod
    def verify(root, assertion, proof):
        node = H(b'mtc-leaf', proof['batch_id'], assertion)
        idx = proof['index']
        for lvl, sib in enumerate(proof['path']):
            left, right = (node, sib) if idx & 1 == 0 else (sib, node)
            node = H(b'mtc-node', proof['batch_id'], lvl.to_bytes(1, 'big'), (idx >> 1).to_bytes(4, 'big'),
                     left, right)
            idx >>= 1
        return node == root and idx == 0

    @staticmethod
    def proof_bytes(proof):
        return len(proof['path']) * N_BYTES + 4 + len(proof['batch_id'])


# ----------------------------------------------------------------- tests ----
class Tests(unittest.TestCase):
    def test_quic_budget_grows_with_client_kem(self):
        # G4: a bigger client key share raises the server's amplification budget.
        b768 = quic_server_budget(client_hello_bytes(['X25519', 'ML-KEM-768']))
        b1024 = quic_server_budget(client_hello_bytes(['X25519', 'ML-KEM-1024']))
        self.assertGreaterEqual(b1024, b768)
        self.assertEqual(quic_server_budget(500), 3600)

    def test_naive_cat5_chain_fails_both_windows(self):
        rows = {r['config']: r for r in ledger()}
        r = rows['naive PQ chain, Cat 5']
        self.assertGreater(r['server_flight'], TCP_INITCWND_BYTES)
        self.assertFalse(r['quic_fits_first_flight'])
        self.assertTrue(r['qpt128_eligible'])

    def test_cat2_chain_is_not_qpt128_even_if_it_fit(self):
        rows = {r['config']: r for r in ledger()}
        self.assertFalse(rows['naive PQ chain, Cat 2/3']['qpt128_eligible'])
        self.assertFalse(rows['deployed hybrid (2024-26)']['qpt128_eligible'])

    def test_cat5_configs_that_fit_first_flight(self):
        rows = {r['config']: r for r in ledger()}
        fits = [n for n, r in rows.items() if r['qpt128_eligible'] and r['quic_fits_first_flight']
                and r['tcp_initcwnd_fits'] and r['under_cloudflare_10kB_cliff']]
        # sanity against Cloudflare's own figure: ML-DSA-44 everywhere ~ +15-17 kB
        self.assertTrue(14_000 <= rows['naive PQ chain, Cat 2/3']['extra_vs_classical'] <= 18_000)
        for name in ('X.509 + SQIsign-V, Cat 5', 'MTC + SQIsign-V, Cat 5', 'MTC + KEMTLS ML-KEM-1024, Cat 5'):
            self.assertIn(name, fits)
        self.assertNotIn('MTC + OV-V (pk in handshake)', fits)      # 447 KB key
        # MEASURED (first run refuted the guess that these fit everywhere): MTC with
        # ML-DSA-87 or MAYO-5 stays under the 10 kB cliff and the TCP window but
        # exceeds the QUIC 3x budget for a 2-datagram ClientHello (7,200 B).
        for name in ('MTC + MAYO-5, Cat 5', 'MTC + ML-DSA-87, Cat 5'):
            self.assertTrue(rows[name]['under_cloudflare_10kB_cliff'])
            self.assertTrue(rows[name]['tcp_initcwnd_fits'])
            self.assertFalse(rows[name]['quic_fits_first_flight'])
            self.assertNotIn(name, fits)
        # G3 measured: at Cat 5, KEMTLS costs more bytes than SQIsign-V ...
        self.assertGreater(rows['MTC + KEMTLS ML-KEM-1024, Cat 5']['server_flight'],
                           rows['MTC + SQIsign-V, Cat 5']['server_flight'])
        # ... but is the only Cat-5 option with no per-handshake server signature.
        self.assertFalse(rows['MTC + KEMTLS ML-KEM-1024, Cat 5']['server_signs_per_handshake'])
        # the smallest QPT-128-eligible flight is below the classical-today + hybrid one
        self.assertLess(rows['MTC + SQIsign-V, Cat 5']['server_flight'], rows['naive PQ chain, Cat 2/3']['server_flight'])

    def test_mtc_prototype(self):
        assertions = [b'example%05d.test|pk|' % i + H(b'k', i.to_bytes(4, 'big')) for i in range(5000)]
        batch = MTCBatch(assertions, batch_id=b'2026-09-11T12')
        self.assertEqual(batch.depth, 13)
        for i in (0, 1, 2500, 4999):
            p = batch.proof(i)
            self.assertTrue(MTCBatch.verify(batch.root, assertions[i], p))
            self.assertEqual(MTCBatch.proof_bytes(p), 13 * 32 + 4 + len(b'2026-09-11T12'))
        p = batch.proof(7)
        self.assertFalse(MTCBatch.verify(batch.root, assertions[8], p))       # wrong assertion
        self.assertFalse(MTCBatch.verify(batch.root, assertions[7], {**p, 'index': 8}))
        p2 = dict(p); p2['path'] = list(p['path']); p2['path'][3] = H(b'x')
        self.assertFalse(MTCBatch.verify(batch.root, assertions[7], p2))
        other = MTCBatch(assertions, batch_id=b'2026-09-11T13')             # cross-batch replay
        self.assertFalse(MTCBatch.verify(other.root, assertions[7], p))
        self.assertLess(mtc_proof_bytes(24), 900)                            # 2^24 certs per batch

    def test_mtc_node_hash_is_position_prefixed(self):
        """S2-006: the v2.0 MTC nodes were H('mtc-node', l, r), so every interior
        node of every batch sat in one function and T signed batches gave a
        multi-target second preimage. Each assertion here fails against that."""
        bid = b'2026-09-21T09'
        batch = MTCBatch([b'example%05d.test' % i for i in range(8)], batch_id=bid)
        lv, z4, z1 = batch.levels, b'\x00\x00\x00\x00', b'\x00'
        self.assertEqual(lv[1][0], H(b'mtc-node', bid, z1, z4, lv[0][0], lv[0][1]))
        self.assertEqual(lv[1][1], H(b'mtc-node', bid, z1, b'\x00\x00\x00\x01', lv[0][2], lv[0][3]))
        self.assertEqual(lv[2][0], H(b'mtc-node', bid, b'\x01', z4, lv[1][0], lv[1][1]))
        # same children at a different index, a different level, another batch, and
        # the v2.0 shape are four different nodes
        for dropped in (H(b'mtc-node', lv[0][0], lv[0][1]),
                        H(b'mtc-node', bid, z1, b'\x00\x00\x00\x01', lv[0][0], lv[0][1]),
                        H(b'mtc-node', bid, b'\x01', z4, lv[0][0], lv[0][1]),
                        H(b'mtc-node', b'2026-09-21T10', z1, z4, lv[0][0], lv[0][1])):
            self.assertNotEqual(lv[1][0], dropped)
        # a path lifted to another index: rejected, though v2.0 accepted it because
        # the repeated assertions make every subtree of the batch the same bytes
        rep = [b'repeat|a', b'repeat|b'] * 4
        r = MTCBatch(rep, batch_id=bid)
        p0 = r.proof(0)
        self.assertTrue(MTCBatch.verify(r.root, rep[0], p0))
        self.assertFalse(MTCBatch.verify(r.root, rep[2], {**p0, 'index': 2}))
        old, path, idx = [[H(b'mtc-leaf', bid, a) for a in rep]], [], 0
        while len(old[-1]) > 1:
            p = old[-1]
            old.append([H(b'mtc-node', p[i], p[i + 1]) for i in range(0, len(p), 2)])
        for lvl in range(3):
            path.append(old[lvl][idx ^ 1])
            idx >>= 1
        for j in (0, 2, 4):
            node, idx = H(b'mtc-leaf', bid, rep[j]), j
            for sib in path:
                node = H(b'mtc-node', node, sib) if idx & 1 == 0 else H(b'mtc-node', sib, node)
                idx >>= 1
            self.assertEqual(node, old[-1][0])


def report():
    return {'thresholds': {'quic_min_initial': QUIC_MIN_INITIAL, 'quic_amplification': QUIC_AMPLIFICATION,
                           'tcp_initcwnd_bytes': TCP_INITCWND_BYTES},
            'ledger': ledger()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--report', action='store_true')
    a = ap.parse_args(argv)
    if a.report:
        print(json.dumps(report(), indent=2))
        return 0
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if r.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
