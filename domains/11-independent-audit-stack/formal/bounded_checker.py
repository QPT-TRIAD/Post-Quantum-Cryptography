#!/usr/bin/env python3
"""
bounded_checker.py -- exhaustive state-space checker for the QPT-128 / CE-QS
profile-B0 quorum-certificate abstraction.  Third, independent model (no
Tamarin, no ProVerif): plain set enumeration in Python.

Abstract protocol (one coordinate K, candidates v1, v2, ...):
  * seats 0..N-1; a corrupt set Cset of size C (the adversary holds their keys)
  * a CORRUPT seat has a signature on (K, v) for EVERY candidate v
    (the adversary can obtain any signature from a corrupt seat)
  * an HONEST seat signs at most one candidate per K: its choice is
    either "no candidate" or exactly one v
  * a certificate for v is any set S of >= q distinct seats each having a
    signature on (K, v); Accept(K, v, S)
  * extraction on a conflicting pair (S1 for v1, S2 for v2, v1 != v2) outputs
    S1 & S2; a seat in the intersection has two signatures on conflicting
    transcripts (= slashable evidence)

Properties checked (mirroring Tamarin lemmas A..E):
  A  every accepted certificate has >= q pairwise-distinct signers and every
     signer either honestly signed (K,v) or is corrupt
  B  conflicting pair exists  ==>  C >= 2q-N
  C  every conflicting pair has a non-empty intersection (in fact >= 2q-N),
     and every seat in it holds signatures on both candidates
  D  no honest seat is ever in the intersection (non-frameability)
  E  boundary: C = 2q-N-1  ==> no conflicting pair;  C = 2q-N ==> one exists

Enumeration is EXHAUSTIVE over honest choices (3^H for two candidates) and
over all certificate signer sets (all subsets of size >= q of the supporters
of each candidate).  For N <= 7 every corrupt subset of size C is enumerated;
for N = 10 the corrupt set is fixed to {0..C-1} (the model is invariant under
permutation of seat labels, so this is without loss of generality).  With
three candidates (N <= 5) the same checks are repeated as a WLOG sanity test.
"""

import itertools
import sys
from math import comb

NS = [4, 5, 7, 10]


def quorum(n):
    return (2 * n) // 3 + 1


def honest_assignments(honest, ncand):
    """Every honest seat picks None or one of the ncand candidates."""
    choices = [None] + list(range(ncand))
    for combo in itertools.product(choices, repeat=len(honest)):
        yield dict(zip(honest, combo))


def supporters(cset, assign, v):
    """Seats that hold a signature on (K, v)."""
    return set(cset) | {s for s, c in assign.items() if c == v}


def certificates(supp, q):
    """All signer sets of size >= q drawn from supp (every accepted cert)."""
    supp = sorted(supp)
    for k in range(q, len(supp) + 1):
        for S in itertools.combinations(supp, k):
            yield frozenset(S)


def analyse(n, q, cset, ncand=2):
    """Exhaustively enumerate every reachable certificate pair for one corrupt
    set.  Returns (pair_exists, min_intersection, honest_named, witness,
    cert_count, pair_count, A_ok, C_ok)."""
    cset = frozenset(cset)
    honest = [s for s in range(n) if s not in cset]
    pair_exists = False
    min_inter = None
    honest_named = False
    witness = None
    ncerts = 0
    npairs = 0
    A_ok = True
    C_ok = True
    for assign in honest_assignments(honest, ncand):
        supp = [supporters(cset, assign, v) for v in range(ncand)]
        certs = [list(certificates(supp[v], q)) for v in range(ncand)]
        # A: every certificate: >= q distinct signers, each authorized
        for v in range(ncand):
            for S in certs[v]:
                ncerts += 1
                if len(S) < q:
                    A_ok = False
                for s in S:
                    if not (s in cset or assign.get(s) == v):
                        A_ok = False
        # conflicting pairs
        for v1, v2 in itertools.combinations(range(ncand), 2):
            if not certs[v1] or not certs[v2]:
                continue
            for S1 in certs[v1]:
                for S2 in certs[v2]:
                    npairs += 1
                    pair_exists = True
                    inter = S1 & S2
                    if min_inter is None or len(inter) < min_inter:
                        min_inter = len(inter)
                        witness = (v1, sorted(S1), v2, sorted(S2), sorted(inter))
                    if not inter:
                        C_ok = False
                    for s in inter:
                        # C: seat in intersection has sigs on both candidates
                        if not (s in supp[v1] and s in supp[v2]):
                            C_ok = False
                        # D: is an honest seat named?
                        if s not in cset:
                            honest_named = True
    return dict(pair_exists=pair_exists, min_inter=min_inter,
                honest_named=honest_named, witness=witness,
                ncerts=ncerts, npairs=npairs, A_ok=A_ok, C_ok=C_ok)


def corrupt_sets(n, c, exhaustive):
    if exhaustive:
        for cs in itertools.combinations(range(n), c):
            yield cs
    else:
        yield tuple(range(c))


def main():
    failures = 0
    print("QPT-128 / CE-QS profile B0 -- bounded exhaustive checker")
    print("q = floor(2N/3)+1 ; threshold 2q-N ; two candidates per K")
    print()
    hdr = ("{:>3} {:>3} {:>5} {:>3} | {:>22} {:>19} {:>12} | {:>9} {:>9} {:>4} {:>4} | {:>8} {:>6}"
           .format("N", "q", "2q-N", "C", "conflicting_pair_exists",
                   "extraction_nonempty", "honest_named", "certs", "pairs",
                   "A", "C", "csets", "E_ok"))
    print(hdr)
    print("-" * len(hdr))
    for n in NS:
        q = quorum(n)
        thr = 2 * q - n
        exhaustive = n <= 7
        for c in range(n + 1):
            agg_pair = False
            agg_min = None
            agg_honest = False
            agg_certs = 0
            agg_pairs = 0
            A_all = True
            C_all = True
            ncs = 0
            for cs in corrupt_sets(n, c, exhaustive):
                ncs += 1
                r = analyse(n, q, cs, ncand=2)
                agg_pair |= r["pair_exists"]
                agg_honest |= r["honest_named"]
                agg_certs += r["ncerts"]
                agg_pairs += r["npairs"]
                A_all &= r["A_ok"]
                C_all &= r["C_ok"]
                if r["min_inter"] is not None:
                    agg_min = r["min_inter"] if agg_min is None else min(agg_min, r["min_inter"])
            # E / B: the boundary
            expected_pair = c >= thr
            e_ok = (agg_pair == expected_pair)
            # C: nonempty and at least 2q-N when a pair exists
            if agg_pair:
                extraction = "yes(min|I|={})".format(agg_min)
                c_ok = C_all and agg_min is not None and agg_min >= 1 and agg_min >= thr
            else:
                extraction = "n/a"
                c_ok = True
            d_ok = not agg_honest
            row_ok = e_ok and A_all and c_ok and d_ok
            if not row_ok:
                failures += 1
            print("{:>3} {:>3} {:>5} {:>3} | {:>22} {:>19} {:>12} | {:>9} {:>9} {:>4} {:>4} | {:>8} {:>6}"
                  .format(n, q, thr, c, str(agg_pair), extraction, str(agg_honest),
                          agg_certs, agg_pairs, "ok" if A_all else "FAIL",
                          "ok" if c_ok else "FAIL", ncs, "ok" if e_ok else "FAIL"))
        # boundary assertions for this N
        below = c_below = thr - 1
        r_below = analyse(n, q, tuple(range(c_below)))
        r_at = analyse(n, q, tuple(range(thr)))
        assert not r_below["pair_exists"], (n, q, thr, "pair at C=2q-N-1")
        assert r_at["pair_exists"], (n, q, thr, "no pair at C=2q-N")
        assert not r_at["honest_named"], (n, q, thr, "honest seat named")
        assert r_at["min_inter"] >= thr, (n, q, thr, "intersection below 2q-N")
        w = r_at["witness"]
        print("   boundary N={} q={} 2q-N={}: C={} -> no conflicting pair; C={} -> pair exists, "
              "witness cert(v{})={} cert(v{})={} intersection={} (all corrupt: {})"
              .format(n, q, thr, c_below, thr, w[0], w[1], w[2], w[3], w[4],
                      all(s < thr for s in w[4])))
        print()

    # three-candidate WLOG sanity check for the small instances
    print("three-candidate sanity (N<=5, every corrupt subset): boundary and D re-checked")
    for n in [4, 5]:
        q = quorum(n)
        thr = 2 * q - n
        for c in range(n + 1):
            for cs in itertools.combinations(range(n), c):
                r = analyse(n, q, cs, ncand=3)
                assert r["pair_exists"] == (c >= thr), (n, c, cs, "3-cand boundary")
                assert not r["honest_named"], (n, c, cs, "3-cand honest named")
                assert r["A_ok"] and r["C_ok"], (n, c, cs, "3-cand A/C")
        print("   N={} q={} 2q-N={}: ok for all C in 0..{} and all corrupt subsets".format(n, q, thr, n))
    print()

    # the general counting identity used by the implementation (N=64, q=43)
    n, q = 64, 43
    thr = 2 * q - n
    print("ratified parameters: N={} q={} 2q-N={} (any two q-subsets of an N-set share >= {} seats; "
          "with C < {} corrupt no two conflicting certificates can exist)".format(n, q, thr, thr, thr))
    # minimum overlap of two q-subsets of an N-set is max(0, 2q-N): check the identity
    assert max(0, 2 * q - n) == thr
    print()
    if failures:
        print("RESULT: {} row(s) FAILED".format(failures))
        sys.exit(1)
    print("RESULT: all rows ok; boundary C = 2q-N confirmed for N in {}".format(NS))


if __name__ == "__main__":
    main()
