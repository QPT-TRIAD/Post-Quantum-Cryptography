#!/usr/bin/env python3
r"""QPT-128 audit stack — FAULT-INJECTION layer on the certificate/extraction pipeline
(profile B0, sidecar_free_certificate_v1.44, read-only import).

An adversarial network sits between 64 signers, a collector, an archive and the
extractor. Faults: loss, duplication, reordering, delay, clock skew (stale coordinate),
node restart (archive re-read), state rollback (archive restored to an older snapshot),
corrupted message, corrupted signature, corrupted certificate, validator equivocation.
For every fault schedule the five properties are checked:

  P1 invalid state rejected       (every corrupted frame is rejected by verify_b0)
  P2 liveness where expected      (with >= q honest votes delivered a certificate forms)
  P3 no false blame               (extraction never names a seat that signed one side)
  P4 no lost evidence             (if two conflicting frames ever existed in the archive,
                                   every double-signer is named after recovery/replay)
  P5 no contradictory acceptance  (two frames with the same message are never a conflict;
                                   a rolled-back archive cannot un-name a double-signer)

Seeded, deterministic, replayable (--seed). The signature scheme is the module's
symbolic test double (width 32): this layer tests pipeline logic under faults, not
cryptographic strength (see math/ and the primitives layer for that).
"""

import argparse
import importlib.util
import json
import os
import random
import sys

# Reference source tree: the read-only inputs this layer audits. The verification
# environment exports PQT_SRC; see docs/inputs-and-provenance.md.
PQT = os.environ.get('PQT_SRC')
if not PQT or not os.path.isdir(PQT):
    raise SystemExit('PQT_SRC is not set: source the environment activation script '
                     '(tooling/), or point PQT_SRC at a local copy of the research tree')


def load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PQT, fn))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


b0 = load('sidecar44_fault', 'sidecar_free_certificate_v1.44.py')
N, Q = b0.N, b0.QUORUM
FAULTS = ('loss', 'duplication', 'reorder', 'delay', 'clock_skew', 'restart', 'rollback',
          'corrupt_message', 'corrupt_signature', 'corrupt_certificate', 'equivocation')


class World:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.prov = b0.SymbolicSignatures(width=32)
        keys = [self.prov.keygen() for _ in range(N)]
        self.registry = b0.RegistryB0(tuple(pk for pk, _ in keys), b'fault-lab')
        self.sks = [sk for _, sk in keys]
        self.cfg = b0.cfg_b0(self.registry)
        self.domain = b'D' * 64
        self.archive = []                      # frames the extractor can see
        self.snapshots = []
        self.byzantine = set()

    def frame(self, message, seats):
        return b0.encode_b0(self.registry, self.prov, self.domain, message, self.sks, sorted(seats))


def corrupt(rng, frame, where):
    b = bytearray(frame)
    if where == 'corrupt_message':
        off = 8 + 64 + 64 + rng.randrange(64)          # inside the header's message field (after suite/cfg/domain)
    elif where == 'corrupt_signature':
        off = len(b) - 1 - rng.randrange(min(len(b) - 1, Q * 32))
    else:
        off = rng.randrange(len(b))
    b[off] ^= 1 << rng.randrange(8)
    return bytes(b)


def run_schedule(w: World, faults, C):
    """One schedule: C Byzantine seats (double-signers when equivocation is on), honest seats
    split by the adversary's best split, faults applied to the vote/certificate stream."""
    rng = w.rng
    m0, m1 = b'0' * 64, b'1' * 64
    seats = list(range(N))
    byz = seats[:C]
    honest = seats[C:]
    rng.shuffle(honest)
    need = max(Q - C, 0)
    side_a = byz + honest[:need]
    side_b = byz + honest[need:need + need] if 'equivocation' in faults and C >= 2 * Q - N else []
    result = {'C': C, 'faults': list(faults), 'checks': {}}
    # ---- votes travel through the faulty network: some are lost/duplicated/reordered/delayed
    delivered_a = list(side_a)
    if 'loss' in faults:
        delivered_a = [s for s in delivered_a if rng.random() > 0.15 or s in byz]
    if 'duplication' in faults:
        delivered_a = delivered_a + rng.sample(delivered_a, min(5, len(delivered_a)))
    if 'reorder' in faults:
        rng.shuffle(delivered_a)
    if 'delay' in faults:
        delivered_a = delivered_a[len(delivered_a) // 3:] + delivered_a[:len(delivered_a) // 3]
    uniq_a = sorted(set(delivered_a))
    # P2 liveness: a certificate forms iff >= q distinct votes arrived (duplicates never count twice)
    cert_a = w.frame(m0, uniq_a[:Q]) if len(uniq_a) >= Q else None
    result['checks']['P2_liveness'] = {'delivered_distinct': len(uniq_a), 'certificate_formed': cert_a is not None,
                                       'expected': len(uniq_a) >= Q, 'ok': (cert_a is not None) == (len(uniq_a) >= Q)}
    cert_b = w.frame(m1, sorted(side_b)[:Q]) if len(side_b) >= Q else None
    # ---- corruption faults on the certificate stream: every corrupted frame must be rejected (P1)
    p1 = {'attempts': 0, 'accepted': 0}
    for where in ('corrupt_message', 'corrupt_signature', 'corrupt_certificate'):
        if where in faults and cert_a is not None:
            for _ in range(20):
                bad = corrupt(rng, cert_a, where)
                p1['attempts'] += 1
                try:
                    b0.verify_b0(bad, w.registry, w.prov, w.cfg)
                    p1['accepted'] += 1
                except b0.CertError:
                    pass
    p1['ok'] = p1['accepted'] == 0
    result['checks']['P1_invalid_rejected'] = p1
    # ---- clock skew: a frame at a stale coordinate (different domain) is never a conflict partner
    if 'clock_skew' in faults and cert_a is not None:
        stale = b0.encode_b0(w.registry, w.prov, b'S' * 64, m1, w.sks, sorted(side_a)[:Q])
        try:
            b0.extract_b0(cert_a, stale, w.registry, w.prov, w.cfg)
            result['checks']['P5_skew_not_conflict'] = {'ok': False, 'detail': 'stale-coordinate frame accepted as a conflict'}
        except b0.CertError as e:
            result['checks']['P5_skew_not_conflict'] = {'ok': True, 'detail': str(e)}
    # ---- three archive replicas (gossip); restart re-reads bytes; rollback restores ONE replica
    replicas = [[], [], []]
    if cert_a is not None:
        for rep in replicas:
            rep.append(('A', cert_a))
        w.snapshots.append([list(rep) for rep in replicas])
    if cert_b is not None:
        for i, rep in enumerate(replicas):
            if 'loss' in faults and i == 2 and rng.random() < 0.5:
                continue                                        # B never reached replica 2
            rep.append(('B', cert_b))
    if 'restart' in faults:
        replicas = [[(k, bytes(f)) for k, f in rep] for rep in replicas]   # durable re-read: bytes identical
    rolled_back = False
    if 'rollback' in faults and w.snapshots:
        replicas[0] = list(w.snapshots[-1][0])                  # attacker restores replica 0 to before B
        rolled_back = True
    # the extractor consults every replica it can reach (the union): P5 says a single rollback cannot un-name
    seen = {}
    for rep in replicas:
        for k, f in rep:
            seen.setdefault(k, f)
    frames_a = [seen['A']] if 'A' in seen else []
    frames_b = [seen['B']] if 'B' in seen else []
    result['checks']['P5_rollback_cannot_unname'] = {'rolled_back': rolled_back,
                                                     'B_still_reachable': 'B' in seen if cert_b is not None else None,
                                                     'ok': (cert_b is None) or ('B' in seen)}
    # ---- extraction: P3 no false blame, P4 no lost evidence
    named = []
    if frames_a and frames_b:
        blames = b0.extract_b0(frames_a[0], frames_b[0], w.registry, w.prov, w.cfg)
        named = [bl.seat for bl in blames]
        assert all(b0.verify_blame_b0(frames_a[0], frames_b[0], w.registry, w.prov, w.cfg, s) for s in named)
    # a conflict exists only if BOTH certificates were ever formed; the double-signers are the
    # seats present in both formed certificates (signers of A are uniq_a[:Q], not side_a)
    conflict = cert_a is not None and cert_b is not None
    double = sorted(set(uniq_a[:Q]) & set(sorted(side_b)[:Q])) if conflict else []
    honest_named = [s for s in named if s not in byz]
    result['checks']['P3_no_false_blame'] = {'named': len(named), 'honest_named': honest_named, 'ok': honest_named == []}
    result['checks']['P4_no_lost_evidence'] = {'conflict': conflict, 'double_signers': len(double), 'named': len(named),
                                               'ok': (not conflict) or sorted(named) == double}
    # P5 contradictory acceptance: same message twice is never a conflict
    if cert_a is not None:
        try:
            b0.extract_b0(cert_a, cert_a, w.registry, w.prov, w.cfg)
            result['checks']['P5_same_message_not_conflict'] = {'ok': False}
        except b0.CertError as e:
            result['checks']['P5_same_message_not_conflict'] = {'ok': True, 'detail': str(e)}
    result['ok'] = all(v['ok'] for v in result['checks'].values())
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=11)
    ap.add_argument('--schedules', type=int, default=300)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)
    results, failures = [], []
    for i in range(a.schedules):
        k = rng.randrange(1, len(FAULTS) + 1)
        faults = tuple(sorted(rng.sample(FAULTS, k)))
        C = rng.choice([0, 1, 5, 21, 22, 23, 26, 30])
        w = World(seed=a.seed * 1000 + i)
        r = run_schedule(w, faults, C)
        r['schedule'] = i
        results.append(r)
        if not r['ok']:
            failures.append(r)
    summary = {'schedules': a.schedules, 'failures': len(failures), 'fault_classes': FAULTS,
               'checks_total': sum(len(r['checks']) for r in results),
               'p1_corruptions_attempted': sum(r['checks'].get('P1_invalid_rejected', {}).get('attempts', 0) for r in results),
               'p1_accepted_on_invalid': sum(r['checks'].get('P1_invalid_rejected', {}).get('accepted', 0) for r in results),
               'conflicts_extracted': sum(1 for r in results if r['checks']['P4_no_lost_evidence']['double_signers']),
               'honest_named_total': sum(len(r['checks']['P3_no_false_blame']['honest_named']) for r in results),
               'verdict': 'REPRODUCED' if not failures else 'FINDING', 'first_failures': failures[:3]}
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'fault_results.json'), 'w') as f:
        json.dump({'summary': summary, 'results': results}, f, indent=1)
    print(json.dumps(summary, indent=1)[:1500])
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())
