#!/usr/bin/env python3
"""
CE-QS v1.1 strong certified conflict-handle logic checker.

NOT cryptographic software.

Models:
- valid handles certified to hidden signer identities,
- deterministic same-topic handle key for duplicate counting,
- public conflict trace,
- explicit VerifyBlame,
- outer QC membership.

Mutation controls exercise false blame, invalid membership, same-message
duplicate evasion, and cross-key false trace.
"""
from dataclasses import dataclass
import hashlib

P = 2**127 - 1

def H(x: bytes) -> int:
    return int.from_bytes(hashlib.sha256(x).digest(), "big") % P or 1

@dataclass(frozen=True)
class Handle:
    link: int
    trace: int

class IdealSCCH:
    def __init__(self, keys):
        self.keys = dict(keys)  # identity -> secret scalar
        self.pub = {i: H(b"PK|" + str(s).encode()) for i, s in keys.items()}

    def challenge(self, topic, msg):
        return H(b"C|" + topic + msg)

    def base(self, secret, topic, which):
        return H(b"B|" + str(secret).encode() + b"|" + topic + bytes([which]))

    def handle(self, i, topic, msg):
        s = self.keys[i]
        y = self.pub[i]
        t = self.base(s, topic, 0)
        u = self.base(s, topic, 1)
        c = self.challenge(topic, msg)
        return Handle(t, (u + c * y) % P)

    def trace(self, topic, m0, h0, m1, h1):
        # Validity-gated caller only. Require same link and distinct challenge.
        if h0.link != h1.link:
            return None
        c0, c1 = self.challenge(topic, m0), self.challenge(topic, m1)
        if c0 == c1:
            return None
        y = ((h0.trace - h1.trace) * pow((c0-c1) % P, P-2, P)) % P
        for i, pk in self.pub.items():
            if pk == y:
                return i
        return None

def verify_qc(scch, topic, msg, hidden_ids, E, q):
    if len(hidden_ids) < q or len(set(hidden_ids)) != len(hidden_ids):
        return False
    expected = [scch.handle(i, topic, msg) for i in hidden_ids]
    # Outer proof's same-set relation, idealized.
    return sorted(expected, key=lambda h:(h.link,h.trace)) == sorted(E, key=lambda h:(h.link,h.trace))

def extract(scch, topic, m0, E0, m1, E1):
    out = {}
    for a, h0 in enumerate(E0):
        for b, h1 in enumerate(E1):
            i = scch.trace(topic, m0, h0, m1, h1)
            if i is not None:
                out[i] = (a,b)
    return out

def verify_blame(scch, topic, m0, E0, m1, E1, i, pair):
    a,b = pair
    if not (0 <= a < len(E0) and 0 <= b < len(E1)):
        return False
    return scch.trace(topic, m0, E0[a], m1, E1[b]) == i

def run():
    scch = IdealSCCH({0:11, 1:17, 2:23, 3:29, 4:31, 5:37, 6:41})
    topic = b"epoch=3|height=8"
    q = 5

    # Baseline.
    S0 = [0,1,2,3,4]
    S1 = [0,1,2,5,6]
    m0, m1 = b"A", b"B"
    E0 = [scch.handle(i,topic,m0) for i in S0]
    E1 = [scch.handle(i,topic,m1) for i in S1]
    assert verify_qc(scch,topic,m0,S0,E0,q)
    assert verify_qc(scch,topic,m1,S1,E1,q)
    print("PASS valid_qcs")

    blame = extract(scch,topic,m0,E0,m1,E1)
    assert set(blame) == set(S0) & set(S1)
    print(f"PASS exact_conflict_trace identities={sorted(blame)}")

    for i,pair in blame.items():
        assert verify_blame(scch,topic,m0,E0,m1,E1,i,pair)
    print("PASS public_verify_blame")

    # False blame mutation: use valid pair from signer 0 but claim signer 4.
    assert not verify_blame(scch,topic,m0,E0,m1,E1,4,blame[0])
    print("EXPECTED-FAIL false_identity_blame")

    # Public tag not belonging to QC witness.
    Ebad = list(E0)
    Ebad[0] = scch.handle(5,topic,m0)
    assert not verify_qc(scch,topic,m0,S0,Ebad,q)
    print("EXPECTED-FAIL handle_not_bound_to_qc_signer_set")

    # Duplicate hidden identity cannot count twice.
    Sdup = [0,1,2,3,3]
    Edup = [scch.handle(i,topic,m0) for i in Sdup]
    assert not verify_qc(scch,topic,m0,Sdup,Edup,q)
    print("EXPECTED-FAIL duplicate_identity_threshold_evasion")

    # Same signer, same message -> same handle (linkable) but no conflict trace.
    h = scch.handle(0,topic,m0)
    assert h == scch.handle(0,topic,m0)
    assert scch.trace(topic,m0,h,m0,h) is None
    print("PASS same_message_link_without_conflict_blame")

    # Different signer handles have different link values in this ideal adapter
    # and do not falsely trace.
    h0 = scch.handle(0,topic,m0)
    h1 = scch.handle(1,topic,m1)
    assert scch.trace(topic,m0,h0,m1,h1) is None
    print("EXPECTED-FAIL cross_key_false_trace")

    print("NOTE: ideal SCCH only; no lattice/ROM/QROM cryptography implemented.")

if __name__ == "__main__":
    run()
