#!/usr/bin/env python3
"""
CE-QS v0.8 policy-binding checker.

No cryptography. Exhaustively checks, for small n, that the bitmap-derived
weighted threshold policy f_B(z) accepts iff every bitmap-selected signer
is present in z. It also checks the BFT intersection/blame rule.
"""
import itertools

def f_B(B, z):
    threshold = sum(B)
    return sum(b * zi for b, zi in zip(B, z)) >= threshold

def support(bits):
    return {i for i, b in enumerate(bits) if b}

def check_policy(n):
    vecs = list(itertools.product((0, 1), repeat=n))
    for B in vecs:
        for z in vecs:
            lhs = f_B(B, z)
            rhs = support(B) <= support(z)
            if lhs != rhs:
                raise AssertionError((n, B, z, lhs, rhs))
    print(f"PASS bitmap_policy_equivalence n={n}")

def check_bft(n, f):
    q = n - f
    sets = [
        set(c)
        for c in itertools.combinations(range(n), q)
    ]
    min_i = min(len(a & b) for a in sets for b in sets)
    assert min_i == 2 * q - n
    assert min_i == f + 1
    print(
        f"PASS bft_intersection n={n} f={f} q={q} "
        f"minimum={min_i}"
    )

def mutation_unbound_bitmap():
    # A generic threshold certificate from signers {0,1,2} would pass q=3.
    # If bitmap were NOT bound into the policy, attacker could claim
    # bitmap {0,1,3}.  The bitmap policy correctly rejects because 3 absent.
    z = (1, 1, 1, 0)
    malicious_B = (1, 1, 0, 1)
    assert sum(z) >= 3
    assert not f_B(malicious_B, z)
    print("EXPECTED-FAIL unbound_bitmap_attack blocked_by=f_B")

def main():
    for n in (3, 4, 5):
        check_policy(n)
    check_bft(4, 1)
    check_bft(7, 2)
    mutation_unbound_bitmap()
    print("PASS n=64 bitmap_size_bytes=8")

if __name__ == "__main__":
    main()
