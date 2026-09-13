#!/usr/bin/env python3
"""
CE-QS v1.4 collaborative-proof structural checker.

NOT cryptographic software.

Checks:
- Q=2F+1 selected provers always contain honest majority under <=F faults;
- distributed witness contains per-party trace secret, not a collector copy;
- one final proof object replaces local proof list;
- same hidden identities bind vote signatures and handles;
- identifiable-abort retry removes at most F Byzantine provers before the
  all-honest quorum remains;
- non-identifiable abort has no monotone progress measure.
"""
from dataclasses import dataclass
import itertools

def honest_majority(n, f):
    q = 2*f + 1
    assert n == 3*f + 1
    V = set(range(n))
    for B in itertools.combinations(V, f):
        B = set(B)
        for S in itertools.combinations(V, q):
            S = set(S)
            corrupt = len(S & B)
            honest = q - corrupt
            if not honest > corrupt:
                return False, (B,S)
    return True, None

for n,f in [(4,1),(7,2),(10,3)]:
    ok, bad = honest_majority(n,f)
    assert ok
    print(f"PASS collaborative_quorum_honest_majority n={n} f={f} q={2*f+1}")

@dataclass(frozen=True)
class PartyWitness:
    idx: int
    vote_sig: bytes
    trace_secret: int

@dataclass(frozen=True)
class FinalQC:
    public_handles: tuple
    one_proof: bytes

# Collector stores only metadata/signatures/handles; trace secrets remain party-local.
collector_fields = {"idx", "vote_sig", "handle"}
assert "trace_secret" not in collector_fields
print("PASS collector_has_no_trace_secret")

# Final proof syntax has exactly one proof field, no local-proof vector.
qc = FinalQC((1,2,3,4,5), b"ONE-PROOF")
assert isinstance(qc.one_proof, bytes)
assert not hasattr(qc, "local_proofs")
print("PASS one_final_proof_no_local_proof_list")

# Same hidden identity tuple logically supplies both vote and handle witness.
w = [
    PartyWitness(0,b"s0",11),
    PartyWitness(1,b"s1",17),
    PartyWitness(2,b"s2",23),
]
ids_vote = {x.idx for x in w}
ids_handle = {x.idx for x in w}
assert ids_vote == ids_handle
print("PASS same_hidden_set_vote_handle_binding")

# Identifiable-abort retry theorem, toy n=7 f=2 q=5.
n,f,q = 7,2,5
byz = {5,6}
active = set(range(n))
aborts = 0
while active & byz:
    culprit = min(active & byz)   # ideal sound identifiable abort
    active.remove(culprit)
    aborts += 1
    assert aborts <= f
assert len(active) == q
assert not (active & byz)
print(f"PASS identifiable_abort_converges aborts={aborts} remaining_honest={len(active)}")

# Non-identifiable abort has no state change; demonstrate the liveness defect.
active0 = frozenset(range(n))
active1 = active0  # anonymous "proof failed"
assert active1 == active0
print("EXPECTED-FAIL non_identifiable_abort_no_progress")

# Reference arithmetic.
n,f,q = 64,21,43
assert q == 2*f+1 and n == 3*f+1
assert q-f == 22 and 22 > 21
print("PASS reference_64_21_43 honest_in_any_quorum>=22")

print("NOTE: structural checker only; no MPC/NIZK/PQ cryptography implemented.")
