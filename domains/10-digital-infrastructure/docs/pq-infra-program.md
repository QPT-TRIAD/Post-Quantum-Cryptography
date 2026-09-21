# Post-quantum global infrastructure program v2.0 — six tested steps at Category 5

Date: 2026-09-11. Method: for each deployment gap, borrow partial theorems from
different papers, glue them into one construction, write it as executable code
with assertions, let the tests refute the guesses, verify the numbers against
primary sources, report what survived. Nothing here is a deployment; everything
here is measured.

Target throughout: **QPT-128** as fixed in `QPT128_finalization_v1.43` — an
attacker with fewer than 2^128 gates (≥2^18 gates per hash query) succeeds with
probability < 1/3. By the v1.43 ledger only NIST Category 5 passes (reference
attacks: Cat 1 = 2^83, Cat 2 = 2^100, Cat 3 = 2^116, Cat 5 = 2^148 gates). So
"deployed hybrid ML-KEM-768" is Category 3 and is **not** the finish line.

## 0. Order of attack (easiest first) and result in one line each

| Step | Gap | Status after this work | Evidence |
|---|---|---|---|
| S1 | Firmware / secure boot | **Solved in the standard and shipping**; QPT-128 pins n = 32 (NSA's preferred SHA-256/192 fails by 14 bits) | `pq_infra_s1s2…`, `…s4…` |
| S2 | DNSSEC under 1,232 B | **Solved for any zone size** by MTL ladder + canonical-order sharding + Merkle multiproof + NSEC; SQIsign route refuted | `pq_infra_s1s2…` |
| S3 | TLS 1.3 / Web PKI | **Solved in bytes** by MTC + KEMTLS(ML-KEM-1024): 4,280-B server flight, no per-handshake signing; naive Cat-5 chain +29 kB refuted | `pq_infra_s3…` |
| S4 | ICS / satellite / medical links | **Solved** by 256-bit TESLA anchored by LMS: 52 B per message where no PQ signature fits | `pq_infra_s4…` |
| S5 | Smart cards / SE / HSM signing | **Solved**: on-card LMS with BDS traversal (state 664 B measured, <2 KB bound), or ML-DSA-87 in 8.1 KiB (literature) | `pq_infra_s5…` |
| S6 | Cat 3 → Cat 5 migration, agility | **Ledger**: every layer has a Cat-5 target that fits; ROM verifiers cannot be rotated, so choose n = 32 now | `pq_infra_s6…` |

28 tests, all passing:

```
pq_infra_s1s2_hashsig_dnssec_v2.0.py   10 tests   sha256 b2f079dde5c0efe4935f78ff8ca52f82c90caf80d278c978073d64a6be6351a7
pq_infra_s3_tls_pki_v2.0.py             5 tests   sha256 440dfcb17a01daaee2839c3d4eb13b106bfebfec81ed049c68c3e213bbccd9df
pq_infra_s4_embedded_broadcast_v2.0.py  5 tests   sha256 57e39f46af43cb8252b9ec2e9ffd6e522a3e11b6ae969c7a7170322570e0d059
pq_infra_s5_smartcard_hsm_v2.0.py       4 tests   sha256 9e8df16259e9a87bb6c61a9b9a71c52b5f473c0cdb1a426d4cbdf5633e0bd232
pq_infra_s6_migration_agility_v2.0.py   4 tests   sha256 2f806deacf5cf8fbede551d95319dfe09e6d92c2819277b6e97bf6a789b777fb
```

Run any file with `--self-test` or `--report`.

## 1. The unifying observation

Every "size" blocker in the list is the same blocker: a Category-5 signature is
too big for one packet / one APDU / one link frame, and there is no compact
Category-5 signature that is also fast. The literature already contains the
answer three separate times under three names — SP 800-208 (Merkle trees for
firmware), Merkle Tree Ladder mode (Merkle trees for DNSSEC), Merkle Tree
Certificates (Merkle trees for the Web PKI). The program therefore builds one
tested Merkle toolkit (WOTS+, LM-OTS w=8, tree, ladder, multiproof, BDS
traversal) and applies it layer by layer, adding one new glue per layer where
the literature stops short. Where a layer must *sign online*, it moves the
per-transaction work to a KEM (KEMTLS) or a MAC chain (TESLA) instead.

## 2. S1 — firmware and secure boot

**Borrowed.** T1: Winternitz OTS under a Merkle tree is EUF-CMA from
second-preimage resistance (RFC 8391 §5; Buchmann–Dahmen–Hülsing 2011).
SP 800-208 §8.1 (read in full): keys and signing must live in a hardware module
that never exports the key and commits the leaf index to NVM before releasing a
signature. CNSA 2.0 (advisory Sep 2022; FAQ v2.1 Dec 2024): LMS/XMSS approved
for firmware/software signing, "begin transitioning immediately", exclusively by
2030; NSA prefers **LMS SHA-256/192**; HSS/XMSS^MT not allowed in NSS.

**Built and measured.** WOTS+ w=16 (len 67) and LM-OTS w=8 (len 34) with exact
byte accounting reproduce the standards: XMSS-SHA2_20_256 = **2,820 B** (RFC
8391), LMS_SHA256_M32_H20 / W8 = **1,772 B** (RFC 8554). Verify at h=4 costs 471
hashes measured against the 1,009 bound (531 in the v2.2 revision, whose root
moved when the interior nodes took their position prefix: the chain steps are a
function of the message digest, so the count is a draw and the bound is not);
w=8 verify ≤ 8,692 hashes at h=20.
Statefulness enforced (65th signature on a 2^6 tree raises).

**QPT-128 finding (tested).** Grover preimage on an n-bit hash costs
2^(n/2)·2^18 gates. n = 192 → 2^114 < 2^128: the NSA-preferred set is **14
bits inside the budget**. n = 256 → 2^146: passes. QPT-128 firmware roots must
use the n = 32 parameter sets (LMS_SHA256_M32_*, XMSS-SHA2_*_256).

**Deployment reality.** Cisco trust anchors (LMS,
work since 2013, products 2024), Infineon OPTIGA TPM SLB 9672 XMSS-signed
firmware (2022), Microchip MEC175xB LMS (2025), AMD Versal Gen 2 LMS secure boot
(WP566, 2025), Lattice MachXO5-NX TDQ (2025), OpenTitan ROM ECDSA + SLH-DSA
hybrid (ROM frozen 2023). Verifier cost from Kampanakis et al. ePrint 2021/041
Table 2: LMS256H20W8 code 2.15 KB, stack 1.81 KB, 2.857 Mcycles.

## 3. S2 — DNSSEC

**Ceilings (verified).** DNS Flag Day 2020: 1,232 B (IPv6 min MTU 1280 − 48).
RFC 9715 §3.1 recommends ≤ 1,400. Measured failure (Koolhaas–Slokker 2020):
≈0.9 % at ≤1,260 B, ≈1.65 % at 1,400–1,480, 18.9 % at 1,500 (IPv4 stub→resolver).
Müller et al. CCR 2020 Table 2: sig ≤ 1,232 B **and** validation ≥ 1,000 sig/s.

**Hypothesis 1, refuted by the first test run.** "A compact Category-5
signature (SQIsign-V, 292 B) fits every response." A and DNSKEY fit; the NSEC3
NXDOMAIN answer carries **4 RRSIGs** (3 NSEC3 + SOA; RFC 5155 §7.2, RFC 2308
§3) → 1,604 B. Binding law: `436 + 4·sig ≤ 1232 ⇒ sig ≤ 199 B` — no Cat-5
scheme.

**Hypothesis 2, refuted.** "MTL mode alone rescues NXDOMAIN." Condensed
signatures at 2^20 leaves are 645 B each; four exceed the ceiling (the MTL
draft's own formula, 28 + 3n + n⌊log₂N⌋ with n = 32, gives 540 B at N = 10⁴).

**Hypothesis 3, refuted by verification.** SQIsign moved: v2.0 (Feb 2025)
level V = 292 B/129 B; **v3.0 (2026-09-01, round 3) = 406 B sig / 169 B pk**.
With 406 B even NSEC denial (3 RRSIGs) is 1,549 B. And verification is 35.7
Mcycles (v2.0 spec Table 2, i7-13700K) ≈ **95 verifications/s/core**, ten
times below Müller's floor. Compact denial (RFC 9824, Sep 2025; 2 RRSIGs →
1,038 B) needs *online* signing at 507.5 Mcycles ≈ 7 signatures/s/core: a
random-subdomain attack ends it. SQIsign is not the DNSSEC answer.

**What survived — three glued pieces, all measured.**

1. *MTL ladder* (Fregly–Harvey–Kaliski–Sheth, CT-RSA 2023; draft-harvey-cfrg-
   mtl-mode-09; draft-fregly-dnsop-slh-dsa-mtl-dnssec-06): one underlying
   signature per ladder; per-record condensed proof. Implemented; every leaf of
   a 1,000-leaf ladder verifies, tampering fails, rung count = popcount(N).
2. *Canonical-order multiproof* (new glue): put RRsets in the ladder in
   canonical zone order, so the SOA and apex NSEC that every denial carries are
   leaves 0–3 and share almost their whole path; prove the 3 RRSIGs of an NSEC
   denial with one Merkle multiproof. Measured worst case: **988 B** at 2^10
   names (vs 1,071 B for three separate condensed signatures), 1,244 B at 2^14.
3. *Sharded ladders* (new glue): ladder per 2^k canonical-order leaves, each
   signed separately; a denial needs shard 0 (apex) + shard j. Answer size is
   then independent of zone size. Measured at .com scale (160 M names):

   | shard | shards | worst NXDOMAIN | class |
   |---|---|---|---|
   | 2^10 | 312,501 | 1,001 B | UDP-safe |
   | 2^12 | 78,126 | **1,129 B** | UDP-safe |
   | 2^14 | 19,532 | 1,257 B | UDP-safe under RFC 9715 |
   | 2^16 | 4,883 | 1,385 B | UDP-safe under RFC 9715 |

   The underlying signature can then be anything — SLH-DSA-256s (29,792 B, the
   IETF draft's choice, stateless, n = 32) fetched once per shard per TTL over
   TCP (`mtl-mode-full` EDNS option). Validation is hashes only, far above
   1,000/s. NSEC3 must be abandoned for NSEC (RFC 9276 already zeroes its
   iterations; the closest-encloser proof is what costs the fourth RRSIG).

Open: the operational load of ~78k shard-ladder fetches per resolver per TTL at
TLD scale is a modelling result, not a measurement.

## 4. S3 — TLS 1.3 and the Web PKI

**Thresholds (verified).** RFC 9000 §8.1: server ≤ 3× bytes received before
address validation; §14.1: client Initial padded to ≥ 1,200 B. TCP initcwnd 10
MSS = 14,600 B. Cloudflare (pq-2024, pq-2025): +9 kB ≈ 15 % slower; crossing
**+10 kB** costs a round trip (>60 %) and trips middleboxes; second bump at
30 kB; ML-DSA-44 everywhere ≈ +15–17 kB; median compressed chain today 3.2 kB.
Chrome (2026-02-27; CQRP v0.3.0): PQ X.509 will **not** enter the Chrome Root
Store; MTC quantum-resistant root store targeted Q3 2027. Note: CQRP cosigners
are ML-DSA-44 — Category 2, outside QPT-128.

**Model (server first flight, bytes; Cat = min over components with hybrid KEM = max).**

| configuration | Cat | flight | vs classical | <10 kB | QUIC 3× | TCP | server signs |
|---|---|---|---|---|---|---|---|
| classical today | 0 | 1,520 | 0 | ✓ | ✓ | ✓ | yes |
| deployed hybrid X25519MLKEM768 + ECDSA | 3 | 2,608 | +1,088 | ✓ | ✓ | ✓ | yes |
| naive ML-DSA-44 chain | 2 | 16,884 | +15,364 | ✗ | ✗ | ✗ | yes |
| naive ML-DSA-87 chain | 5 | 30,959 | +29,439 | ✗ | ✗ | ✗ | yes |
| X.509 + SQIsign-V | 5 | 4,358 | +2,838 | ✓ | ✓ | ✓ | yes (~7/s/core) |
| MTC + ML-DSA-87 | 5 | 9,939 | +8,419 | ✓ | ✗ | ✓ | yes |
| MTC + SQIsign-V | 5 | 3,141 | +1,621 | ✓ | ✓ | ✓ | yes (~7/s/core) |
| MTC + MAYO-5 | 5 | 9,238 | +7,718 | ✓ | ✗ | ✓ | yes |
| **MTC + KEMTLS ML-KEM-1024** | 5 | **4,280** | +2,760 | ✓ | ✓ | ✓ | **no** |
| MTC + OV-V (pk in handshake) | 5 | 449,972 | — | ✗ | ✗ | ✗ | yes |

Sanity: the model's ML-DSA-44 chain (+15,364 B) sits inside Cloudflare's
measured +15–17 kB. The MTC proof (24 hashes + framing = 796 B) matches
draft-davidben-10 §6.4 (23 hashes = 736 B, "no signatures").

**Findings.** (i) Every Cat-5 KEM public key exceeds 1,455 B (smallest:
ML-KEM-1024, 1,568 B; Classic McEliece has 194–208 B ciphertexts but ~1 MB
keys), so a Cat-5 ClientHello is always two QUIC datagrams and the server budget
is 7,200 B — that budget, not the 10 kB cliff, is what MTC + ML-DSA-87 and MTC +
MAYO-5 fail (hypothesis refuted by test). (ii) The byte-optimal Cat-5 handshake
(MTC + SQIsign-V) is CPU-infeasible online (507.5 Mcycles per signature).
(iii) KEMTLS (Schwabe–Stebila–Wiggers 2020) at Category 5 costs *more* bytes
than SQIsign-V (verified as a measured reversal of the level-1 literature
comparison) but is the only Cat-5 option with no per-handshake signature;
ML-KEM-1024 decapsulation is ~10⁴× cheaper. **Recommendation: MTC + KEMTLS with
ML-KEM-1024**, SQIsign/OV-V reserved for the offline cosigner role. Working
MTC prototype: batch of 5,000 assertions, depth 13, inclusion proofs verified,
wrong assertion / index / path / cross-batch replay all rejected.

## 5. S4 — ICS, embedded, satellite, medical

**Borrowed.** LM-OTS w=8 (SP 800-208 Table 1: p = 34). TESLA (Perrig–Canetti–
Tygar–Song; RFC 4082), the mechanism Galileo OSNMA deploys with 128-bit keys —
widened to 256-bit chain keys so the chain's one-wayness is a 2^128 quantum
preimage (128-bit fails QPT-128 by the S1 test).

**Built and measured.** TESLA sender/receiver with the RFC 4082 §3.5 safety
condition (accept only if the key cannot yet be disclosed): genuine packets
accepted after disclosure, forgery with disclosed keys → `bad mac`, replay →
`replay`, late packet → refused, wrong disclosed key → `bad disclosed key`.
Per-message overhead **52 B** (4 index + 16 MAC + 32 key); one 1,772-B LMS
anchor per 2^16-message chain (52.03 B amortised).

| artifact | bytes | LoRa SF12 frames (51 B) | Iridium SBD (340 B) |
|---|---|---|---|
| ML-DSA-87 signature | 4,627 | 91 | 14 |
| XMSS-SHA2_20_256 | 2,820 | 56 | 9 |
| LMS w=8 h=20 | 1,772 | 35 | 6 |
| SQIsign-V (v2.0) | 292 | 6 | 1 |
| TESLA per message | 52 | 2 | 1 |

## 6. S5 — smart cards, secure elements, HSMs, payment

**Reframing.** SP 800-208 §8.1's requirements (no key export, index committed to
NVM before release, FIPS 140-3 Level 3+) describe a smart card. The "state
problem" that disqualifies LMS/XMSS for general software is a non-problem on a
device with a tamper-resistant monotonic counter and no backups.

**Built and measured.** BDS traversal (Buchmann–Dahmen–Schneider 2008; RFC 8391
reference structure) verified **exhaustively** against naive authentication
paths for every leaf at (h,k) = (6,2), (8,2), (8,4); root matches; ≤ (h−k)/2 + 1
leaf computations per advance; state 664 B at h=8 (bound < 2,048 B asserted).
Card signer: index committed before signature release, 65th signature refused.
Cost at h=8, k=2: **30,466 hashes per signature** measured (3.01 leaf
computations). Projection h=20: ≤ 9 leaf computations → ≤ 86,720 hashes, ≈ 85 ms
at 1 µs/hash on a hardware SHA-256 engine (assumption, not measured).
Transport: 1,772 B = 7 short APDUs (ML-DSA-87: 19), or one extended APDU.

**Literature (verified).** Card RAM: Infineon SLE 78 8 KB; NXP SmartMX3 P71
12 KB. Bos–Renes–Sprenkels ePrint 2022/323 Table 2: Dilithium5 keygen/sign/
verify 7.9 / **8.1** / 2.7 KiB (fits P71, not SLE 78), sign 44,332 kcycles.
Kyber-1024 decaps 3,776 B stack (2019/489). Falcon-1024 signing needs 51–80 KB
(2019/893) — excluded from cards. Infineon shipped CC EAL6 ML-KEM on TEGRION
(Jan 2025) for eSIM/SIM/smart card.

## 7. S6 — migration and agility

**Combiner.** X-Wing / draft-ietf-tls-ecdhe-mlkem style
K = H(label ‖ ss_pq ‖ ss_cl ‖ ct_cl ‖ pk_cl). Tested: agreement; with the
classical secret handed to the adversary the key stays unpredictable; splicing a
different classical ciphertext or label changes the key.

**Byte cost 768 → 1024.** ClientHello +384 B, ServerHello +480 B; both messages
already two datagrams — no new packet boundary (tested).

**Ledger.**

| layer | deployed (QPT-128?) | Category-5 target | cost | rotatable in field |
|---|---|---|---|---|
| TLS key exchange | X25519MLKEM768, Cat 3 (no) | X25519 + ML-KEM-1024 | +384 / +480 B | yes (named group) |
| TLS / Web PKI auth | ECDSA/RSA X.509 (no) | MTC + KEMTLS ML-KEM-1024 | 4,280-B flight | yes (trust-anchor IDs, weekly landmarks) |
| DNSSEC | ECDSA/RSA (no) | SLH-DSA-256s-MTL, 2^12 shards, NSEC + multiproof | 1,129 B worst NXDOMAIN | yes (RFC 6781 rollover) |
| Firmware / boot | mixed; some LMS/XMSS | LMS n=32 w=8 h=20 (not SHA-256/192) | 1,772 B; 1.8 KB stack | **no** — ROM fixed at manufacture |
| Cards / SE / HSM | RSA-1984 / ECDSA (no) | on-card LMS + BDS, or ML-DSA-87 @ 8.1 KiB | <2 KB NVM, ~85 ms | partial (GlobalPlatform applet) |
| Constrained broadcast | none / 128-bit TESLA (no) | 256-bit TESLA + LMS anchor | 52 B/msg | yes (new anchor per chain) |

## 8. Falsified hypotheses and bugs — kept on record

- "Compact Cat-5 signature fits every DNS response" — false (NXDOMAIN 4 RRSIGs).
- "MTL alone rescues NXDOMAIN" — false (4 × 645 B).
- "SQIsign-V is the DNSSEC/TLS answer" — false on verification (406 B in v3.0;
  95 verifies/s and 7 signs/s per core).
- "MTC + MAYO-5 / ML-DSA-87 fit the QUIC first flight" — false (7,200-B budget).
- Hybrid KEM category taken as min over components (zeroed every row) — fixed to max.
- LMS signature 4 B short (RFC 8554 carries two type fields; RFC 8391 none) — fixed.
- S5 hash counter blind to WOTS hashes through a duplicated module instance
  (reported 3.1 hashes/signature) — fixed, guard test added (must exceed 4,000).
- Card signer recomputed the public chains at signing time (39,137 → 30,466).

## 9. What is still open

- Real-device measurements: every cycle count is from literature (pqm4 commit
  90bfb63; ePrint 2022/323, 2021/041, 2019/489, 2019/893; SQIsign v2.0 Table 2).
- SQIsign v3.0 timings (spec not read; only sizes from sqisign.org).
- MAYO-5 and ML-DSA-87 server-side signing cost were not verified.
- TLD-scale DNSSEC: shard-ladder fetch load and resolver caching behaviour.
- All of S1–S6 are Python models and prototypes with SHAKE256; none is a
  constant-time or audited implementation.
- The Chrome quantum-resistant root program's ML-DSA-44 cosigners are Category
  2; a QPT-128 Web PKI needs Category-5 cosigners (ML-DSA-87 or SLH-DSA-256s
  off-line — size is irrelevant there because cosignatures never travel in the
  handshake).

## 10. Primary sources (documents read)

NIST SP 800-208 (all 59 pp.); FIPS 203 Table 3; CNSA 2.0 advisory (Sep 2022)
and FAQ v2.1 (Dec 2024); RFC 8391, 8554, 9000 §8.1/§14.1, 9715, 9824, 5155,
2308, 4035, 6891, 7766, 8879; draft-ietf-tls-ecdhe-mlkem-05; draft-harvey-cfrg-
mtl-mode-09; draft-fregly-dnsop-slh-dsa-mtl-dnssec-06; draft-ietf-plants-merkle-
tree-certs-05 and draft-davidben-tls-merkle-tree-certs-10 §6.4; ePrint 2022/1730
(MTL), 2020/534 (KEMTLS), 2021/779 (KEMTLS-PDK), 2022/1712, 2024/176, 2020/071
(NDSS'20), 2022/323, 2020/1278, 2019/489, 2019/893, 2021/041; SQIsign spec v2.0
Tables 1/2 and sqisign.org v3.0 page; pqm4 benchmarks.md (commit 90bfb63);
Müller et al. CCR 2020; Koolhaas–Slokker 2020; Goertzen–Stebila (arXiv
2211.14196); Schutijser et al. TMA 2025; Cloudflare posts sizing-up (2021),
pq-2024, pq-2025, bootstrap-mtc, radar 2024/2025; Google/Chromium posts May 2024
and Feb 2026; CQRP policy v0.3.0; CA/B servercert PR #679; vendor releases
(Cisco, Infineon, Microchip, AMD WP566, Lattice, OpenTitan, NXP, ST, TI, Intel).
