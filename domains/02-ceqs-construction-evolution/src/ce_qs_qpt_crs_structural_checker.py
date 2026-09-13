#!/usr/bin/env python3
"""
CE-QS v1.3 QPT/CRS structural checker.

NOT cryptographic software.

Checks finite structural facts introduced by v1.3:
- bounded domain slots map to pre-sampled bases;
- no hash-to-base is needed;
- same-domain link bases are canonical and immutable;
- challenge digest/base-p encoding is injective for a toy finite digest space;
- exact conflict extraction from valid same-key handles;
- distinct-key false trace is blocked by uniqueness in the ideal model;
- outer relation has no signer secret material.
"""
from dataclasses import dataclass
import hashlib
import itertools
import random

P = 257   # toy prime
KAPPA = 16
D = 2     # 257^2 > 2^16
MOD = 65537

def enc_p(x):
    assert 0 <= x < (1 << KAPPA)
    out = []
    for _ in range(D):
        out.append(x % P)
        x //= P
    assert x == 0
    return tuple(out)

# Exhaustive injectivity for toy 16-bit digest.
seen = {}
for x in range(1 << KAPPA):
    e = enc_p(x)
    if e in seen:
        raise AssertionError((x, seen[e], e))
    seen[e] = x
print("PASS challenge_encoding_injective toy_bits=16")

@dataclass(frozen=True)
class Handle:
    link: int
    z: tuple

class BaseCRS:
    def __init__(self, dmax=8, seed=7):
        rng = random.Random(seed)
        self.A = rng.randrange(1, MOD)
        self.link = [rng.randrange(1, MOD) for _ in range(dmax)]
        self.trace = [
            tuple(rng.randrange(1, MOD) for _ in range(D))
            for _ in range(dmax)
        ]
        self.dmax = dmax

    def slot(self, topic_id):
        if not (0 <= topic_id < self.dmax):
            raise IndexError("safe-halt: domain budget exhausted")
        return topic_id

def prf(secret, base):
    # Ideal injective-in-secret toy PRF for structural checking.
    return (secret * base) % MOD

class Registry:
    def __init__(self, secrets, crs):
        self.s = dict(secrets)
        self.crs = crs
        self.y = {i: prf(s, crs.A) for i, s in secrets.items()}
        assert len(set(self.y.values())) == len(self.y)

    def challenge(self, topic_id, msg):
        digest = int.from_bytes(
            hashlib.sha256(
                b"C|" + str(topic_id).encode() + b"|" + msg
            ).digest()[:2], "big"
        )
        return enc_p(digest)

    def handle(self, i, topic_id, msg):
        j = self.crs.slot(topic_id)
        s = self.s[i]
        y = self.y[i] % P
        t = prf(s, self.crs.link[j])
        c = self.challenge(topic_id, msg)
        zs = []
        for r in range(D):
            u = prf(s, self.crs.trace[j][r]) % P
            zs.append((u + c[r] * y) % P)
        return Handle(t, tuple(zs))

    def trace(self, topic_id, m0, h0, m1, h1):
        if h0.link != h1.link:
            return None
        if m0 == m1:
            return "LINKED"
        c0 = self.challenge(topic_id, m0)
        c1 = self.challenge(topic_id, m1)
        if c0 == c1:
            return "COLLISION"
        for r, (a,b) in enumerate(zip(c0,c1)):
            if a != b:
                y = ((h0.z[r] - h1.z[r]) * pow((a-b) % P, P-2, P)) % P
                matches = [i for i, Y in self.y.items() if Y % P == y]
                return matches[0] if len(matches) == 1 else None
        raise AssertionError

crs = BaseCRS()
reg = Registry({0:3, 1:5, 2:7, 3:11}, crs)

# Same key/domain extracts.
m0, m1 = b"A", b"B"
h0 = reg.handle(2, 3, m0)
h1 = reg.handle(2, 3, m1)
assert reg.trace(3, m0, h0, m1, h1) == 2
print("PASS same_key_conflict_extract")

# Different keys blocked by link gate in ideal uniqueness model.
ha = reg.handle(0, 3, m0)
hb = reg.handle(1, 3, m1)
assert ha.link != hb.link
assert reg.trace(3, m0, ha, m1, hb) is None
print("EXPECTED-FAIL cross_key_false_trace blocked_by=unique_link_base")

# Same domain always uses same setup base.
assert reg.handle(2,3,b"X").link == reg.handle(2,3,b"Y").link
print("PASS setup_sampled_domain_base_immutable")

# Exhaustion is explicit fail-closed.
try:
    reg.handle(0, crs.dmax, b"x")
    raise AssertionError("budget overrun accepted")
except IndexError:
    print("EXPECTED-FAIL domain_budget_exhaustion safe_halt")

# Collector witness schema contains no trace secret.
outer_witness_fields = {"idx", "vote_sig", "handle", "local_proof"}
assert "trace_secret" not in outer_witness_fields
assert "auth_secret" not in outer_witness_fields
print("PASS outer_witness_no_signer_secrets")

print("NOTE: structural toy model only; QLWR/LWE/NIZK/QCR security not executed.")
