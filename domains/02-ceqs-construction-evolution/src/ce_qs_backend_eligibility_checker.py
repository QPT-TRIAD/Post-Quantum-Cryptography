#!/usr/bin/env python3
"""
CE-QS v1.6 backend eligibility checker.

No cryptography. Encodes the decision logic and exact byte-gate arithmetic.
A backend with any FAIL or OPEN property is not yet production-eligible.
"""
from dataclasses import dataclass

PASS = "PASS"
FAIL = "FAIL"
OPEN = "OPEN"
EXPERIMENTAL = "EXPERIMENTAL"

GATE = 32768
Q = 43

@dataclass
class Backend:
    name: str
    e1_pq: str
    e2_public: str
    e3_privacy: str
    e4_exact_relation: str
    e5_scch: str
    e6_constructible: str
    e7_liveness: str
    proof_bytes: int | None
    handle_bytes: int | None
    overhead: int = 0
    benchmark_status: str = OPEN

    def byte_status(self):
        if self.proof_bytes is None or self.handle_bytes is None:
            return OPEN, None
        total = self.proof_bytes + Q*self.handle_bytes + self.overhead
        return (PASS if total <= GATE else FAIL), total

    def eligible(self):
        props = [
            self.e1_pq, self.e2_public, self.e3_privacy,
            self.e4_exact_relation, self.e5_scch,
            self.e6_constructible, self.e7_liveness
        ]
        bstat, _ = self.byte_status()
        return all(x == PASS for x in props) and bstat == PASS

backends = [
    Backend(
        "LaZer-2024-succinct",
        PASS, PASS, FAIL, OPEN, OPEN, PASS, PASS,
        75300, 0
    ),
    Backend(
        "LaZer-Toolkit-2026",
        OPEN, PASS, PASS, OPEN, OPEN, PASS, PASS,
        None, None
    ),
    Backend(
        "CoSNIZK-published-DAA",
        PASS, PASS, PASS, OPEN, OPEN, PASS, OPEN,
        38*1024, 0
    ),
    Backend(
        "Fusion-direct",
        PASS, PASS, OPEN, OPEN, OPEN, PASS, PASS,
        int(46.08*1024), 0
    ),
    Backend(
        "Lazarus-repo",
        EXPERIMENTAL, PASS, EXPERIMENTAL, OPEN, OPEN,
        PASS, OPEN, 28*1024, 48, benchmark_status=EXPERIMENTAL
    ),
    Backend(
        "Mutable-BARG-theory",
        PASS, PASS, PASS, OPEN, OPEN, PASS, OPEN,
        None, None
    ),
]

for b in backends:
    bs, total = b.byte_status()
    print(
        f"{b.name:26s} eligible={b.eligible()} "
        f"byte_status={bs} total={total}"
    )
    assert not b.eligible()

# Exact gate examples.
def score(P, h, O=0):
    return GATE - (P + Q*h + O)

assert score(28*1024, 48) == 2032
assert score(28*1024, 96) == -32
print("PASS score_28KiB_48B=2032")
print("EXPECTED-FAIL score_28KiB_96B=-32")

# Backend only becomes eligible when every property is PASS and byte gate passes.
toy = Backend(
    "toy-all-pass",
    PASS,PASS,PASS,PASS,PASS,PASS,PASS,
    24*1024, 96
)
assert toy.eligible()
status,total = toy.byte_status()
assert status == PASS and total == toy.proof_bytes + Q*toy.handle_bytes
print(f"PASS eligibility_requires_all_properties toy_total={toy.proof_bytes + Q*toy.handle_bytes}")

print("NOTE: eligibility logic only; no backend cryptography benchmark executed.")
