#!/usr/bin/env python3
r"""PQ infrastructure program — step S6: Category 3 -> Category 5 migration and
crypto-agility, i.e. the hardest item: what is deployed today is ML-KEM-768
(Category 3), which sits 12 bits INSIDE the QPT-128 gate budget (the Category-3
floor is 2^116 gates, Grover key search on AES-192), so "deployed" is not
"done".

Glued ideas, each tested:
  G1  Hybrid KEM combiner in the X-Wing / draft-ietf-tls-ecdhe-mlkem style:
      K = H(label || ss_pq || ss_classical || ct_classical || pk_classical).
      Security (Giacon–Heuer–Poettering 2018; X-Wing 2024): IND-CCA if EITHER
      component is IND-CCA and H is a random oracle / PRF. Here the classical
      half is MODELLED AS BROKEN (adversary learns ss_classical) and the test
      checks the combined key is still unpredictable; and that mixing the
      classical ciphertext prevents cross-protocol/downgrade splicing.
  G2  Byte cost of moving the deployed hybrid from ML-KEM-768 to ML-KEM-1024:
      +384 B in the ClientHello, +480 B in the ServerHello — both already
      two-datagram messages, so no new packet boundary is crossed (S3 model).
  G3  Agility is a per-layer property. A verifier that lives in ROM cannot be
      rotated, so the choice made at manufacture must already be Category 5 —
      the argument for hash-based n=32 roots now (S1/S5), not "upgrade later".
  G4  Migration ledger: computed from the S2–S5 models, one row per layer:
      today's category, the Cat-5 artifact that fits, what it costs, and
      whether it can be rotated in the field.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import secrets
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fn))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# The S1/S2 model is loaded at revision v2.2, not the v2.0 file kept beside it: v2.2 carries the
# F2/F4 multiproof-verification fixes and the S2-006 position-prefixed node hashing. Only
# sharded_zone_answer is used here, and it is byte-identical between the two revisions, so the
# DNSSEC row's model figure is unchanged by the switch.
s1s2 = _load('s1s2', 's1s2_hashsig_dnssec.py')
s3 = _load('s3', 's3_tls_pki.py')
s4 = _load('s4', 's4_embedded_broadcast.py')

# NIST category FLOORS in log2 gates: the resource level a scheme in the category has to match,
# NOT the cost of the best known attack on the scheme deployed in that category. 83, 116 and 148
# are Grover key search on AES-128 / AES-192 / AES-256, i.e. half the key length in Grover
# iterations charged at the gate cost of one AES evaluation (64+19, 96+20, 128+20); the AES-256
# entry is the G-cost 1.17*2^148 of Jaques-Naehrig-Roetteler-Virdia Tables 9 and 11, which is the
# row the v1.43 constants table carries. 100 is the Category-2 entry (collision search on a
# 256-bit hash) and nothing below uses it. Reading a floor as a scheme's own attack cost is the
# conservative direction only while the best known attack on the scheme costs at least the floor.
# Analytic cross-check, not measured: an independent estimator run (lattice-estimator, ADPS16
# core-SVP, quantum) puts ML-KEM-1024 near 2^231.6 quantum and 2^255.2 classical, and ML-KEM-512
# near 2^107.6 quantum, so the Category-5 floor is the conservative side at the deployed
# Category-5 parameters while Category 1 sits below the 2^128 budget. Those counts are core-SVP
# operations rather than these gate units and bound the direction, not the number.
CATEGORY_ATTACK_GATES = {1: 83, 2: 100, 3: 116, 5: 148}
QPT128_BUDGET_LOG2 = 128


def category_passes_qpt128(cat):
    return CATEGORY_ATTACK_GATES[cat] >= QPT128_BUDGET_LOG2


# ------------------------------------------------------ G1: combiner -------
class ToyKEM:
    """Deterministic-for-test KEM stand-in: the shared secret is a PRF of the
    private key and the ciphertext. `broken=True` models a quantum adversary who
    recovers this component's shared secret from public data."""

    def __init__(self, tag, broken=False):
        self.tag, self.broken = tag, broken
        self.sk = secrets.token_bytes(32)
        self.pk = hashlib.sha3_256(b'pk' + tag + self.sk).digest()

    def encaps(self, pk):
        r = secrets.token_bytes(32)
        ct = hashlib.sha3_256(b'ct' + self.tag + pk + r).digest()
        ss = hashlib.sha3_256(b'ss' + self.tag + pk + ct + r).digest()
        return ct, ss, r

    def decaps(self, ct, r):
        return hashlib.sha3_256(b'ss' + self.tag + self.pk + ct + r).digest()


def combine(label, ss_pq, ss_cl, ct_cl, pk_cl):
    h = hashlib.sha3_256()
    for p in (label, ss_pq, ss_cl, ct_cl, pk_cl):
        h.update(len(p).to_bytes(2, 'big') + p)
    return h.digest()


# ------------------------------------------------------ G4: ledger ---------
def migration_ledger():
    rows = []
    # TLS key exchange
    ch768 = s3.client_hello_bytes(['X25519', 'ML-KEM-768'])
    ch1024 = s3.client_hello_bytes(['X25519', 'ML-KEM-1024'])
    rows.append({'layer': 'TLS key exchange', 'deployed': 'X25519MLKEM768 (Cat 3)',
                 'deployed_passes_qpt128': category_passes_qpt128(3),
                 'target': 'X25519 + ML-KEM-1024 (Cat 5)', 'target_passes_qpt128': category_passes_qpt128(5),
                 'cost': f'ClientHello +{ch1024 - ch768} B, ServerHello +480 B; datagrams {-(-ch768 // 1200)} -> {-(-ch1024 // 1200)}',
                 'rotatable_in_field': 'yes: per-handshake negotiation (named group)'})
    # TLS authentication
    L = {r['config']: r for r in s3.ledger()}
    rows.append({'layer': 'TLS / Web PKI authentication', 'deployed': 'ECDSA/RSA X.509 (Cat 0)',
                 'deployed_passes_qpt128': False,
                 'target': 'MTC + KEMTLS ML-KEM-1024 (Cat 5; no per-handshake signing)',
                 'target_passes_qpt128': True,
                 'cost': f"server flight {L['MTC + KEMTLS ML-KEM-1024, Cat 5']['server_flight']} B "
                         f"(+{L['MTC + KEMTLS ML-KEM-1024, Cat 5']['extra_vs_classical']} B) by the design model, superseded by the v2.1 exact "
                         "encoder at 4,148 B of handshake (4,203 B on TCP); fits QUIC 3x and TCP initcwnd under both figures",
                 'rotatable_in_field': 'yes: trust-anchor IDs / landmark roll (~weekly)'})
    # DNSSEC
    sh = s1s2.sharded_zone_answer(160_000_000, 12)
    rows.append({'layer': 'DNSSEC', 'deployed': 'ECDSA P-256 / RSA (Cat 0)', 'deployed_passes_qpt128': False,
                 'target': 'SLH-DSA-256s-MTL (n=32) ladder, canonical-order shards of 2^12, NSEC + multiproof',
                 'target_passes_qpt128': True,
                 'cost': f"worst NXDOMAIN {sh['answer_worst']} B for this zone shape by the design model, remeasured by the v2.1 wire encoder "
                         "at 954 B for the same shape; the v2.0 reading 'UDP-safe for any zone size' is withdrawn by v2.1, whose realistic "
                         "worst case is 1,530 B (NSEC) / 1,839 B (NSEC3), so typical shapes fit 1,232 B and worst cases need RFC 9715's "
                         "1,400 B with shards of 2^10; one 29,792-B ladder fetch per shard per TTL over TCP",
                 'rotatable_in_field': 'yes: RFC 6781 algorithm rollover (double-signing period)'})
    # Firmware / secure boot
    w = s4.WOTS(256)
    rows.append({'layer': 'Firmware / secure boot', 'deployed': 'RSA/ECDSA; some LMS/XMSS (Cisco, AMD, Microchip, Infineon)',
                 'deployed_passes_qpt128': None,
                 'target': 'LMS n=32 w=8 h=20 (Cat 5), NOT the NSA-preferred SHA-256/192',
                 'target_passes_qpt128': s4.qpt128_hash_preimage_ok(256),
                 'cost': f'signature {w.sig_bytes(20)} B; verify <= {w.verify_hashes_max(20)} hashes, 1.8 KB stack (2021/041)',
                 'rotatable_in_field': 'NO: ROM verifier fixed at manufacture -> choose Cat 5 now'})
    # Smart cards / HSM
    rows.append({'layer': 'Smart cards / SE / HSM signing', 'deployed': 'RSA-1984 EMV, ECDSA (Cat 0)',
                 'deployed_passes_qpt128': False,
                 'target': 'on-card LMS n=32 w=8 h=20 with BDS (Cat 5) or ML-DSA-87 in 8.1 KiB (2022/323)',
                 'target_passes_qpt128': True,
                 'cost': 'BDS peak state 2,148 B NVM at h=20, superseding the v2.0 bound of < 2 KB; at most 95,775 hashes/sign at h=20 '
                         '(mean 82,700), superseding the v2.0 bound of <= 86,720; 1,772 B sig = 7 short APDUs',
                 'rotatable_in_field': 'partial: applet update via GlobalPlatform; key state never exported'})
    # Broadcast / constrained links
    rows.append({'layer': 'Constrained broadcast (ICS, satellite, medical)', 'deployed': 'none / 128-bit TESLA (OSNMA)',
                 'deployed_passes_qpt128': s4.qpt128_hash_preimage_ok(128),
                 'target': 'TESLA with 256-bit chain keys anchored by LMS n=32 (Cat 5)',
                 'target_passes_qpt128': s4.qpt128_hash_preimage_ok(256),
                 'cost': f'{s4.TeslaSender.overhead_bytes()} B per message in steady state, which is the v2.1 restatement of the flat v2.0 '
                         'figure: the first d packets of a chain carry no disclosed key and are 20 B, and link framing adds 26-30 B; '
                         'one 1,772-B anchor per chain',
                 'rotatable_in_field': 'yes: new chain anchor per epoch'})
    return rows


class Tests(unittest.TestCase):
    def test_category_verdicts(self):
        self.assertFalse(category_passes_qpt128(3))     # deployed hybrid is not QPT-128
        self.assertTrue(category_passes_qpt128(5))

    def test_g1_combiner_survives_classical_break(self):
        pq, cl = ToyKEM(b'mlkem'), ToyKEM(b'x25519', broken=True)
        ct_pq, ss_pq, r_pq = pq.encaps(pq.pk)
        ct_cl, ss_cl, r_cl = cl.encaps(cl.pk)
        k_client = combine(b'X25519MLKEM1024', ss_pq, ss_cl, ct_cl, cl.pk)
        k_server = combine(b'X25519MLKEM1024', pq.decaps(ct_pq, r_pq), cl.decaps(ct_cl, r_cl), ct_cl, cl.pk)
        self.assertEqual(k_client, k_server)
        # adversary with the classical secret but a wrong PQ secret gets a different key
        guess = combine(b'X25519MLKEM1024', secrets.token_bytes(32), ss_cl, ct_cl, cl.pk)
        self.assertNotEqual(guess, k_client)
        # splicing a different classical ciphertext or label changes the key (downgrade/cross-protocol binding)
        self.assertNotEqual(combine(b'X25519MLKEM1024', ss_pq, ss_cl, b'\x00' * 32, cl.pk), k_client)
        self.assertNotEqual(combine(b'X25519MLKEM768', ss_pq, ss_cl, ct_cl, cl.pk), k_client)

    def test_g2_byte_cost_no_new_datagram(self):
        ch768 = s3.client_hello_bytes(['X25519', 'ML-KEM-768'])
        ch1024 = s3.client_hello_bytes(['X25519', 'ML-KEM-1024'])
        self.assertEqual(ch1024 - ch768, 384)
        self.assertEqual(-(-ch768 // 1200), -(-ch1024 // 1200))          # both 2 datagrams

    def test_g4_ledger_all_targets_cat5(self):
        rows = migration_ledger()
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(r['target_passes_qpt128'] for r in rows))
        self.assertEqual(sum(1 for r in rows if r['deployed_passes_qpt128'] is True), 0)
        self.assertTrue(any(r['rotatable_in_field'].startswith('NO') for r in rows))


def report():
    return {'category_attack_log2_gates': CATEGORY_ATTACK_GATES, 'budget_log2': QPT128_BUDGET_LOG2,
            'ledger': migration_ledger()}


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
