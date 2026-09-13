#!/usr/bin/env python3
"""
CE-QS v0.3 relation-level mock checker.

NOT CRYPTOGRAPHIC SOFTWARE and NOT ZERO KNOWLEDGE.

Purpose:
- exercise the exact v0.3 relation structure,
- verify public duplicate-tag rejection closes the v0.2 duplicate-signer gap,
- verify wrong-mask/forged-tag contributions are rejected when witness binding
  is checked,
- verify trace-secret exposure alone cannot create an accepted contribution.

This is a specification test before implementing the relation in VOLEitH.
"""
import hashlib
import random

P = 2**255 - 19

def H(data):
    return hashlib.sha256(data).digest()

def Hf(data):
    return int.from_bytes(H(data), "big") % P or 1

def G_trace(x):
    return H(b"TRACE-v3" + x.to_bytes(32, "big"))

def G_mask(k):
    return H(b"MASK-BIND-v3" + k)

def pub_from_sk(sk):
    return H(b"AUTH-v3" + sk)

def prf(k, topic):
    return Hf(b"PRF-v3" + k + topic)

def challenge(topic, msg):
    return Hf(b"CHAL-v3" + topic + H(msg))

def cet(x, k, topic, msg):
    return (prf(k, topic) + challenge(topic, msg) * x) % P

def make_registry(n=64, seed=20260908):
    rng = random.Random(seed)
    reg = []
    sec = []
    for i in range(n):
        sk = bytes(rng.randrange(256) for _ in range(32))
        x = rng.randrange(1, P)
        k = bytes(rng.randrange(256) for _ in range(32))
        reg.append((pub_from_sk(sk), G_trace(x), G_mask(k)))
        sec.append((sk, x, k))
    return reg, sec

def relation(reg, idx, sk, x, k, topic, msg, tag):
    if idx < 0 or idx >= len(reg):
        return False
    pk, X, K = reg[idx]
    return (
        pub_from_sk(sk) == pk
        and G_trace(x) == X
        and G_mask(k) == K
        and cet(x, k, topic, msg) == tag
    )

def contribution(reg, sec, idx, topic, msg):
    sk, x, k = sec[idx]
    e = cet(x, k, topic, msg)
    assert relation(reg, idx, sk, x, k, topic, msg, e)
    return e, (idx, sk, x, k)  # witness would be hidden in the real ZK proof

def verify_mock_contribution(reg, topic, msg, tag, witness):
    idx, sk, x, k = witness
    return relation(reg, idx, sk, x, k, topic, msg, tag)

def verify_certificate_mock(reg, topic, msg, contributions, q):
    # Real construction verifies ZK proofs instead of receiving witnesses.
    tags = []
    for tag, wit in contributions:
        if not verify_mock_contribution(reg, topic, msg, tag, wit):
            return False, "invalid-relation"
        tags.append(tag)
    if len(tags) < q:
        return False, "below-threshold"
    if len(set(tags)) != len(tags):
        return False, "duplicate-tag"
    return True, "ok"

def run():
    n = 64
    f = 21
    q = 43
    topic = b"epoch=8|height=1200|view=4|phase=vote"
    m0 = b"A"
    m1 = b"B"

    reg, sec = make_registry(n)

    # Safe quorum.
    S = list(range(q))
    C = [contribution(reg, sec, i, topic, m0) for i in S]
    ok, why = verify_certificate_mock(reg, topic, m0, C, q)
    assert ok
    print("PASS valid_quorum_relation")

    # Duplicate same signer: deterministic tag duplicates -> public rejection.
    dup = C[:-1] + [C[0]]
    ok, why = verify_certificate_mock(reg, topic, m0, dup, q)
    assert not ok and why == "duplicate-tag"
    print("EXPECTED-FAIL duplicate_signer_public_rejection reason=duplicate-tag")

    # Wrong mask key with victim's other witnesses -> relation fails.
    victim = 0
    sk, x, _ = sec[victim]
    wrong_k = sec[1][2]
    bad_tag = cet(x, wrong_k, topic, m0)
    bad_wit = (victim, sk, x, wrong_k)
    assert not verify_mock_contribution(reg, topic, m0, bad_tag, bad_wit)
    print("EXPECTED-FAIL wrong_mask_relation_binding")

    # Random forged tag + honest witness fails.
    sk, x, k = sec[2]
    forged = (cet(x, k, topic, m0) + 1) % P
    assert not verify_mock_contribution(reg, topic, m0, forged, (2, sk, x, k))
    print("EXPECTED-FAIL forged_tag_relation_binding")

    # Conflict extraction for same signer.
    e0, _ = contribution(reg, sec, 3, topic, m0)
    e1, _ = contribution(reg, sec, 3, topic, m1)
    c0, c1 = challenge(topic, m0), challenge(topic, m1)
    recovered = ((e0 - e1) * pow((c0 - c1) % P, P - 2, P)) % P
    assert G_trace(recovered) == reg[3][1]
    print("PASS conflict_extracts_trace_secret")

    # Exposure of x alone cannot make a relation-valid contribution: attacker
    # still lacks auth sk and mask key k.  Try arbitrary guessed values.
    exposed_x = recovered
    fake_sk = b"\x00" * 32
    fake_k = b"\x00" * 32
    fake_tag = cet(exposed_x, fake_k, topic, b"C")
    assert not relation(reg, 3, fake_sk, exposed_x, fake_k, topic, b"C", fake_tag)
    print("PASS trace_secret_exposure_alone_not_accepted")

    print("NOTE: relation mock only; real VOLEitH ZK/aggregation proofs remain unimplemented.")

if __name__ == "__main__":
    run()
