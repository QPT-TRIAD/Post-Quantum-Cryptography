#!/usr/bin/env python3
"""
CE-QS v0.9 private-wrapper relation checker.

NOT cryptographic software and NOT zero knowledge.

It checks the logical structure of the private-wrapper relation:
- hidden bitmap threshold,
- bitmap-policy binding,
- same hidden bitmap used by aggregate and CET list,
- bijection to public tags,
- mutation controls for mismatched bitmap/tag sets.
"""
import hashlib
import itertools
import random

P = 2**127 - 1

def H(data):
    return int.from_bytes(hashlib.sha256(data).digest(), "big") % P or 1

def mask(k, topic):
    return H(b"M|" + k + topic)

def chal(topic, msg):
    return H(b"C|" + topic + msg)

def tag(x, k, topic, msg):
    return (mask(k, topic) + chal(topic, msg) * x) % P

def f_B(B, signed):
    # signed is a set of actual signer indices.
    return all((not b) or (i in signed) for i, b in enumerate(B))

def relation(reg, B, signed, topic, msg, E, witness_map, q):
    if sum(B) != len(E) or sum(B) < q:
        return False
    if len(set(E)) != len(E):
        return False
    if not f_B(B, signed):
        return False

    selected = [i for i, b in enumerate(B) if b]
    if set(witness_map) != set(selected):
        return False

    generated = []
    for i in selected:
        x, k = witness_map[i]
        X, K = reg[i]
        if H(b"X|" + str(x).encode()) != X:
            return False
        if hashlib.sha256(b"K|" + k).digest() != K:
            return False
        generated.append(tag(x, k, topic, msg))

    return sorted(generated) == sorted(E)

def make(n=7, seed=99):
    rng = random.Random(seed)
    reg = []
    wit = {}
    for i in range(n):
        x = rng.randrange(1, P)
        k = bytes(rng.randrange(256) for _ in range(16))
        reg.append((H(b"X|" + str(x).encode()), hashlib.sha256(b"K|" + k).digest()))
        wit[i] = (x, k)
    return reg, wit

def run():
    n, f, q = 7, 2, 5
    reg, all_wit = make(n)
    topic = b"epoch=1|h=9|v=2"
    msg = b"block-A"

    S = {0,1,2,3,4}
    B = tuple(1 if i in S else 0 for i in range(n))
    E = [tag(*all_wit[i], topic, msg) for i in S]
    assert relation(reg, B, S, topic, msg, E, {i: all_wit[i] for i in S}, q)
    print("PASS valid_private_wrapper_relation")

    # Mutation 1: aggregate signer set differs from bitmap.
    signed_bad = {0,1,2,3,5}
    assert not relation(reg, B, signed_bad, topic, msg, E, {i: all_wit[i] for i in S}, q)
    print("EXPECTED-FAIL aggregate_bitmap_mismatch")

    # Mutation 2: tag list belongs to a different signer set.
    T = {0,1,2,3,5}
    E_bad = [tag(*all_wit[i], topic, msg) for i in T]
    assert not relation(reg, B, S, topic, msg, E_bad, {i: all_wit[i] for i in S}, q)
    print("EXPECTED-FAIL bitmap_cet_set_mismatch")

    # Mutation 3: below threshold hidden bitmap.
    S4 = {0,1,2,3}
    B4 = tuple(1 if i in S4 else 0 for i in range(n))
    E4 = [tag(*all_wit[i], topic, msg) for i in S4]
    assert not relation(reg, B4, S4, topic, msg, E4, {i: all_wit[i] for i in S4}, q)
    print("EXPECTED-FAIL hidden_below_threshold")

    # Conflict extraction on two private wrapper public tag lists.
    S1 = {0,1,2,3,4}
    S2 = {0,1,2,5,6}
    m0, m1 = b"A", b"B"
    E0 = [tag(*all_wit[i], topic, m0) for i in S1]
    E1 = [tag(*all_wit[i], topic, m1) for i in S2]
    c0, c1 = chal(topic, m0), chal(topic, m1)
    inv = pow((c0-c1) % P, P-2, P)
    commits = {reg[i][0]: i for i in range(n)}
    out = set()
    for a in E0:
        for b in E1:
            x = ((a-b) * inv) % P
            X = H(b"X|" + str(x).encode())
            if X in commits:
                out.add(commits[X])
    assert out == (S1 & S2)
    print(f"PASS conflict_extracts_exact_intersection intersection={sorted(out)}")

    print("NOTE: logical relation mock only; no MPA or NIZK implemented.")

if __name__ == "__main__":
    run()
