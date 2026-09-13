#!/usr/bin/env python3
"""
Toy simulator for CE-QS frontier v0.1.

NOT CRYPTOGRAPHIC SOFTWARE.

Checks only:
  - BFT quorum intersection,
  - deterministic per-topic masks,
  - tag = mask + challenge*trace_secret,
  - recovery of common signer trace secrets from conflicting tag multisets.

It does NOT implement VOLE-in-the-Head, ZK, a threshold ring signature,
or a security proof.
"""
import hashlib
import random
import secrets

P = 2**255 - 19

def H_field(data: bytes) -> int:
    return int.from_bytes(hashlib.sha256(data).digest(), "big") % P

def trace_commit(x: int) -> bytes:
    return hashlib.sha256(
        b"TRACE-COMMIT-v1" + x.to_bytes(32, "big")
    ).digest()

def topic_mask(mask_key: bytes, topic: bytes) -> int:
    return H_field(b"MASK-v1" + mask_key + topic)

def challenge(topic: bytes, message: bytes) -> int:
    c = H_field(b"CHAL-v1" + topic + message)
    return c or 1

def tag(x: int, mask_key: bytes, topic: bytes, message: bytes) -> int:
    return (
        topic_mask(mask_key, topic)
        + challenge(topic, message) * x
    ) % P

def make_registry(n: int):
    xs = [secrets.randbelow(P - 1) + 1 for _ in range(n)]
    ks = [secrets.token_bytes(32) for _ in range(n)]
    commits = {trace_commit(x): i for i, x in enumerate(xs)}
    return xs, ks, commits

def make_certificate(S, xs, ks, topic, message):
    tags = [tag(xs[i], ks[i], topic, message) for i in S]
    random.shuffle(tags)
    return tags

def extract(tags0, tags1, topic0, m0, topic1, m1, registry):
    c0 = challenge(topic0, m0)
    c1 = challenge(topic1, m1)
    denom = (c0 - c1) % P
    if denom == 0:
        raise RuntimeError("challenge collision in toy simulation")
    denom_inv = pow(denom, P - 2, P)

    out = set()
    for e0 in tags0:
        for e1 in tags1:
            x = ((e0 - e1) * denom_inv) % P
            i = registry.get(trace_commit(x))
            if i is not None:
                out.add(i)
    return out

def run(trials=50, n=64):
    f = (n - 1) // 3
    q = 2*f + 1
    assert n == 3*f + 1

    xs, ks, registry = make_registry(n)

    topic = b"epoch=7|height=901|view=3|phase=vote"
    m0 = b"block-A"
    m1 = b"block-B"

    minimum_intersection = n

    for trial in range(trials):
        S0 = set(random.sample(range(n), q))
        S1 = set(random.sample(range(n), q))
        I = S0 & S1
        assert len(I) >= f + 1
        minimum_intersection = min(minimum_intersection, len(I))

        C0 = make_certificate(S0, xs, ks, topic, m0)
        C1 = make_certificate(S1, xs, ks, topic, m1)

        traced = extract(C0, C1, topic, m0, topic, m1, registry)
        if traced != I:
            raise AssertionError(
                f"trial {trial}: expected={sorted(I)}, "
                f"traced={sorted(traced)}"
            )

        # Different topics should not cancel the deterministic mask.
        other_topic = topic + b"|different-domain"
        C_other = make_certificate(S1, xs, ks, other_topic, m1)
        cross = extract(
            C0, C_other,
            topic, m0,
            other_topic, m1,
            registry,
        )
        if cross:
            raise AssertionError(
                f"cross-topic false trace on trial {trial}: {cross}"
            )

    print(f"PASS trials={trials}")
    print(f"n={n} f={f} q={q}")
    print(f"minimum observed quorum intersection={minimum_intersection}")
    print(f"trace tag payload at 32 bytes/tag={q*32} bytes "
          f"({q*32/1024:.3f} KiB)")
    print(f"pair checks per conflict={q*q}")
    print("PASS same-topic conflicting certificates recover exactly "
          "the hidden signer-set intersection")
    print("PASS different-topic certificates produced no trace match")
    print("NOTE: algebra/combinatorics only; no ZK/security proof implemented.")

if __name__ == "__main__":
    run()
