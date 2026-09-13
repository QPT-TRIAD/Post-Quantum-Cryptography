#!/usr/bin/env python3
"""
CE-QS v1.0 distributed-certified-tag relation checker.

NOT cryptographic software. It uses idealized signature/proof verification
tokens to check the construction logic:

- each signer keeps trace secrets local;
- collector witness contains only public contribution data;
- distinct hidden identities are enforced;
- vote signatures and tag certificates are bound to the same identity;
- public tag list is exactly the witness tag multiset;
- conflict extraction recovers the hidden signer-set intersection for the
  linear-CET toy adapter.

The ideal proof/signature tokens model verification interfaces only.
"""
from dataclasses import dataclass
import hashlib
import random

P = 2**127 - 1

def H(data: bytes) -> int:
    return int.from_bytes(hashlib.sha256(data).digest(), "big") % P or 1

@dataclass(frozen=True)
class Contribution:
    idx: int
    vote_sig: bytes
    tag: int
    tag_proof: bytes

class IdealRegistry:
    def __init__(self, n=7, seed=101):
        rng = random.Random(seed)
        self.auth_sk = {}
        self.trace_x = {}
        self.mask_k = {}
        self.auth_pk = {}
        self.trace_commit = {}
        self.mask_commit = {}
        self.valid_tag_proofs = set()
        for i in range(n):
            ask = bytes(rng.randrange(256) for _ in range(16))
            x = rng.randrange(1, P)
            k = bytes(rng.randrange(256) for _ in range(16))
            self.auth_sk[i] = ask
            self.trace_x[i] = x
            self.mask_k[i] = k
            self.auth_pk[i] = hashlib.sha256(b"APK|" + ask).digest()
            self.trace_commit[i] = H(b"X|" + str(x).encode())
            self.mask_commit[i] = hashlib.sha256(b"K|" + k).digest()

    def vote_sign(self, i, msg):
        return hashlib.sha256(b"SIG|" + self.auth_sk[i] + msg).digest()

    def vote_verify(self, i, msg, sig):
        return sig == self.vote_sign(i, msg)

    def mask(self, i, topic):
        return H(b"MASK|" + self.mask_k[i] + topic)

    def challenge(self, topic, msg):
        return H(b"CHAL|" + topic + msg)

    def tag(self, i, topic, msg):
        return (self.mask(i, topic) + self.challenge(topic, msg) * self.trace_x[i]) % P

    def tag_prove(self, i, topic, msg, tag):
        # Idealized local ZK: verify witness internally, issue opaque token.
        assert tag == self.tag(i, topic, msg)
        stmt = self._tag_stmt(i, topic, msg, tag)
        proof = hashlib.sha256(b"IDEAL-TAG-PROOF|" + stmt).digest()
        self.valid_tag_proofs.add((stmt, proof))
        return proof

    def _tag_stmt(self, i, topic, msg, tag):
        return (
            str(i).encode() + b"|" + topic + b"|" + msg + b"|" +
            str(tag).encode()
        )

    def tag_verify(self, i, topic, msg, tag, proof):
        stmt = self._tag_stmt(i, topic, msg, tag)
        return (stmt, proof) in self.valid_tag_proofs

    def contribute(self, i, topic, msg):
        e = self.tag(i, topic, msg)
        return Contribution(
            i,
            self.vote_sign(i, msg),
            e,
            self.tag_prove(i, topic, msg, e),
        )

def outer_relation(reg, topic, msg, E, contribs, q):
    if len(contribs) < q or len(E) != len(contribs):
        return False
    ids = [c.idx for c in contribs]
    if len(set(ids)) != len(ids):
        return False
    if len(set(E)) != len(E):
        return False
    for c in contribs:
        if not reg.vote_verify(c.idx, msg, c.vote_sig):
            return False
        if not reg.tag_verify(c.idx, topic, msg, c.tag, c.tag_proof):
            return False
    return sorted(E) == sorted(c.tag for c in contribs)

def extract_linear(reg, topic, m0, E0, m1, E1):
    c0 = reg.challenge(topic, m0)
    c1 = reg.challenge(topic, m1)
    den = (c0 - c1) % P
    if den == 0:
        return None
    inv = pow(den, P - 2, P)
    commitments = {reg.trace_commit[i]: i for i in reg.trace_commit}
    out = set()
    for e0 in E0:
        for e1 in E1:
            x = ((e0 - e1) * inv) % P
            X = H(b"X|" + str(x).encode())
            if X in commitments:
                out.add(commitments[X])
    return out

def run():
    n, f, q = 7, 2, 5
    reg = IdealRegistry(n)
    topic = b"epoch=2|height=17|phase=vote"
    msg = b"block-A"

    S = [0,1,2,3,4]
    C = [reg.contribute(i, topic, msg) for i in S]
    E = [c.tag for c in C]
    assert outer_relation(reg, topic, msg, E, C, q)
    print("PASS valid_distributed_relation")

    # Constructibility: collector contribution objects contain no trace x/k.
    forbidden_fields = {"trace_x", "mask_k", "auth_sk"}
    fields = set(Contribution.__dataclass_fields__)
    assert not (fields & forbidden_fields)
    print("PASS collector_witness_contains_no_signer_secrets")

    # Duplicate identity.
    Cdup = C[:-1] + [C[0]]
    Edup = [c.tag for c in Cdup]
    assert not outer_relation(reg, topic, msg, Edup, Cdup, q)
    print("EXPECTED-FAIL duplicate_hidden_identity")

    # Swap in a tag from a different identity while retaining original
    # identity/signature/proof.
    foreign = reg.contribute(5, topic, msg)
    bad0 = C[0]
    swapped = Contribution(
        bad0.idx, bad0.vote_sig, foreign.tag, bad0.tag_proof
    )
    Cbad = [swapped] + C[1:]
    Ebad = [c.tag for c in Cbad]
    assert not outer_relation(reg, topic, msg, Ebad, Cbad, q)
    print("EXPECTED-FAIL vote_tag_identity_mismatch")

    # Forged tag proof token.
    forged = Contribution(
        C[0].idx, C[0].vote_sig, C[0].tag,
        b"\x00" * len(C[0].tag_proof)
    )
    Cforged = [forged] + C[1:]
    Eforged = [c.tag for c in Cforged]
    assert not outer_relation(reg, topic, msg, Eforged, Cforged, q)
    print("EXPECTED-FAIL forged_local_tag_proof")

    # Public E does not match witness tag multiset.
    Emismatch = list(E)
    Emismatch[0] = (Emismatch[0] + 1) % P
    assert not outer_relation(reg, topic, msg, Emismatch, C, q)
    print("EXPECTED-FAIL public_tag_list_mismatch")

    # Below threshold.
    assert not outer_relation(reg, topic, msg, E[:q-1], C[:q-1], q)
    print("EXPECTED-FAIL below_threshold")

    # Conflict extraction.
    S0 = {0,1,2,3,4}
    S1 = {0,1,2,5,6}
    m0, m1 = b"A", b"B"
    C0 = [reg.contribute(i, topic, m0) for i in sorted(S0)]
    C1 = [reg.contribute(i, topic, m1) for i in sorted(S1)]
    E0 = [c.tag for c in C0]
    E1 = [c.tag for c in C1]
    assert outer_relation(reg, topic, m0, E0, C0, q)
    assert outer_relation(reg, topic, m1, E1, C1, q)
    traced = extract_linear(reg, topic, m0, E0, m1, E1)
    assert traced == S0 & S1
    print(f"PASS conflict_extracts_exact_intersection intersection={sorted(traced)}")

    print("NOTE: ideal proof/signature interfaces only; no real ZK or PQ signatures.")

if __name__ == "__main__":
    run()
