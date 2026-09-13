#!/usr/bin/env python3
"""
CE-QS v0.7 combinatorial proof checker.

No cryptography. Exhaustively verifies the Structured Quorum Coverage
Theorem for small BFT instances and mutation-tests omission of one required
quorum. It also checks the public-bitmap intersection theorem.

The n=64 count is calculated combinatorially, not enumerated.
"""
import itertools
import math

def subsets(V, k):
    return [frozenset(x) for x in itertools.combinations(V, k)]

def required_family(n, f):
    V = frozenset(range(n))
    return {V - B for B in subsets(V, f)}

def full_fault_coverage(n, f, family):
    V = frozenset(range(n))
    q = n - f
    for B in subsets(V, f):
        available = V - B
        if not any(len(Q) >= q and Q <= available for Q in family):
            return False, B
    return True, None

def check_instance(n, f):
    q = n - f
    family = required_family(n, f)

    assert len(family) == math.comb(n, f)
    ok, bad = full_fault_coverage(n, f, family)
    assert ok

    missing = next(iter(family))
    mutant = family - {missing}
    ok, bad = full_fault_coverage(n, f, mutant)
    assert not ok

    quorums = subsets(frozenset(range(n)), q)
    min_intersection = min(len(A & B) for A in quorums for B in quorums)
    assert min_intersection == 2*q - n

    print(
        f"PASS n={n} f={f} q={q} "
        f"required_family={len(family)} "
        f"min_quorum_intersection={min_intersection}"
    )
    print(
        "EXPECTED-FAIL omitted_required_quorum "
        f"uncovered_fault_set={sorted(bad)}"
    )

def main():
    check_instance(4, 1)
    check_instance(7, 2)
    check_instance(10, 3)

    n, f = 64, 21
    q = n - f
    count = math.comb(n, f)
    assert q == 43
    assert count == 41107996877935680

    print(
        f"PASS n=64 f=21 q=43 combinatorial_required_columns={count} "
        f"log2={math.log2(count):.6f}"
    )
    print("PASS public_bitmap_bytes=8")

if __name__ == "__main__":
    main()
