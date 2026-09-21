# The six studies end to end

This document walks S1–S6 in the order the programme built them. Each study is presented the same
way: the problem, the binding constraint, the theory that was borrowed and **which part of it**, the
construction step by step, the tests, the measured result, and — explicitly — what the study does
not show.

Claim labels, as in the rest of this repository:

| label | meaning |
|---|---|
| **[T]** | theorem with proof, as cited by the source |
| **[R]** | reduction sketch |
| **[L]** | model-or-ledger estimate |
| **[M]** | measurement of a Python model or a byte encoder |
| **[S]** | simulation |
| **[A]** | assumption |
| **[C]** | conjecture |

Pointers name the file in this directory and the symbol or test that carries the number, so every
figure can be found again. Where a figure comes from a regenerated report, the pointer is
`results/sN_audit_report.json` with its key path.

---

## 0. The common frame

### 0.1 The target

QPT-128: an attacker with fewer than 2^128 *gates*, where each hash query costs at least 2^18 gates,
succeeds with probability below 1/3. Reference attack costs per NIST category: Cat 1 = 2^83,
Cat 2 = 2^100, Cat 3 = 2^116, Cat 5 = 2^148 gates (`docs/pq-infra-program.md` §1).
Those four figures are category **floors**, not attack costs on any particular scheme: 83, 116 and
148 are Grover key search on AES-128 / AES-192 / AES-256, half the key length in Grover iterations
charged at the gate cost of one AES evaluation (64+19, 96+20, 128+20), the AES-256 entry being the
G-cost 1.17·2^148 of Jaques–Naehrig–Roetteler–Virdia Tables 9 and 11; 100 is the Category-2
collision entry and nothing in these studies uses it. Reading a floor as a scheme's own attack cost
is the conservative direction only while the best known attack on that scheme costs at least the
floor. Analytic cross-check at full parameters, not measured: an independent estimator run
(lattice-estimator, ADPS16 core-SVP, quantum) puts ML-KEM-1024 near 2^231.6 quantum / 2^255.2
classical and ML-KEM-512 near 2^107.6 quantum, in core-SVP operations rather than these gate units,
so Category 5 is conservative at the deployed parameter sets and Category 1 sits below the budget.
Only Category 5 passes, so every layer in these studies is asked for a Category-5 target.
`src/s6_hybrid_games.py` prints the margins directly
(`results/s6_audit_report.json` → `games` S6-F, and `s1` gate margins below).

### 0.2 Gate accounting and the Grover law

For a preimage or second preimage on an n-bit hash, the query model gives 2^(n/2) queries
(Grover; optimal by the BBBV 1997 lower bound, **cited as** "a theorem in the query model"). At
2^18 gates per query that is 2^(n/2+18) gates:

| n | queries | gates | vs 2^128 |
|---|---|---|---|
| 128 | 2^64 | 2^82 | −46 bits |
| 192 | 2^96 | 2^114 | −14 bits |
| 256 | 2^128 | 2^146 | +18 bits |

Source: `results/s1_audit_report.json` → `qpt128` (S1-010) and `results/s6_audit_report.json` →
`games` S6-F. The 2^18 gates-per-query floor is an **engineering assumption**, not a theorem
(`src/s1_lms.py` → `UNTESTABLE`, first entry). The whole table is therefore [L]: a ledger
computation over a cited theorem plus an assumed constant.

### 0.3 Composition: when two bounds may be added

A union bound Pr[A ∨ B] ≤ Pr[A] + Pr[B] is a statement about two events in **one** probability
space — one experiment, one adversary, one winning condition. The programme therefore adds bounds
only for events inside one attacker goal and lists independent layers side by side
(`src/audit_ledger.py` → `composition()`).

The only same-goal union in the whole domain is one TLS session:

| part | gates (log2) |
|---|---|
| ephemeral KEM ML-KEM-1024 | 148 |
| server long-term KEM ML-KEM-1024 | 148 |
| MTC / transcript hash, prefixed nodes | 146 |

−log2(2^−148 + 2^−148 + 2^−146) = **145.42** ([L]; `results/AUDIT_LEDGER_v2.1.json` →
`composition.same_goal_union.union_gates_log2`). Refused: S1+S2, S2+S3, S4+S5, any cross-layer sum
(`composition.refused`).

### 0.4 The shared toolkit

One Merkle toolkit is reused across the six studies: WOTS+ chains, LM-OTS w = 8 (34 chains), Merkle
trees, MTL ladders, multiproofs and BDS traversal. Two hash conventions appear:

- the v2.0 models hash SHAKE256-256 over length-prefixed parts with a global call counter
  (`src/s1s2_hashsig_dnssec-v2.0.py`);
- the S1 audit implements RFC 8554 exactly, SHA-256 truncated to n bytes (`src/s1_lms.py`);
- the S3/S6 toys use SHA3-256 / HMAC-SHA3-256.

### 0.5 How to run a study

Every model and every audit takes exactly one of `--self-test` or `--report` (argparse mutually
exclusive and required). `src/audit_ledger.py` takes `--refresh`. See `VERIFICATION.md` for the
exact commands, runtimes and observed output in the pinned environment.

---

## 1. S1 — firmware and secure boot

**Files.** `src/s1s2_hashsig_dnssec.py` (design, revision v2.2), `src/s1s2_hashsig_dnssec-v2.0.py`
(design, revision v2.0 — still loaded by the S3/S4 models), `history/s1_lms-v2.1.py` and
`src/s1_lms.py` (the RFC-exact audit, revisions v2.1 and v2.2).

### 1.1 The problem

Firmware and boot ROMs must verify updates for decades. The verifier must run in a boot ROM, which
means "hashes only — no big-integer or polynomial arithmetic". The literature answer already
exists: stateful hash-based signatures (SP 800-208: LMS/HSS, XMSS/XMSS^MT). The question the study
actually had to answer is not "does a signature exist" but "at which hash output length, given
QPT-128".

### 1.2 The binding constraints

1. **Hash output length.** n = 192 gives 2^114 gates and fails QPT-128 by 14 bits; n = 256 gives
   2^146 and passes. NSA's preferred LMS SHA-256/192 therefore fails this target [L].
2. **Statefulness.** A one-time key must never be reused, so the key must live in a hardware module
   that commits the leaf index to non-volatile memory *before* releasing a signature (SP 800-208
   §8.1). This is an assumption here — A-NoExport — not something the code can establish.
3. **ROM immutability.** A ROM verifier cannot be rotated in the field, so the parameter set chosen
   at manufacture must already be Category 5.

### 1.3 Theory borrowed, and which part

| theory | as used here | which part | what is not used |
|---|---|---|---|
| Winternitz OTS + Merkle tree (RFC 8391 §5; Buchmann–Dahmen–Hülsing 2011) | "EUF-CMA from second-preimage resistance of the hash, with signature size len·n + h·n and verify cost ≤ len·(w−1) + h hash calls" [T as cited] | the size formula and the hash-call bound — the two things the study measures | the security proof itself: the code tests sizes and costs, it does not re-prove EUF-CMA |
| RFC 8554 (LMS/HSS, McGrew–Curcio–Fluhrer 2019) | typecodes; the domain separators D_PBLC, D_MESG, D_LEAF, D_INTR; `coef()`; the checksum; node numbering r = 1 … 2^(h+1)−1; the two type fields in a signature; §5.1 "these two hash functions SHOULD be the same" | the exact byte format, so that sizes and interop are checkable rather than asserted | the RFC's own security analysis |
| SP 800-208 §4 tables | the approved (n, m) pairings — LMS m must equal LM-OTS n | the pairing rule that the v2.2 fix enforces (`approved_pair()`) | the FIPS 140-3 validation claim (no hardware was touched) |
| BBBV 1997 | Grover optimality | query-model lower bound | it says nothing about gate counts — the 2^18 constant is separate and assumed |

### 1.4 The construction

- **Design (v2.0).** WOTS+ with w = 16 (len1 = 64, len2 = 3, len = 67) under an XMSS-style Merkle
  tree, with the signer advancing state *before* releasing the signature. A second, parametric
  model (`WOTS(256)`) halves the chain count and pays about 8× in verify hashes — LM-OTS w = 8,
  p = 34, the RFC choice.
- **Audit (v2.1/v2.2).** RFC 8554 rewritten from the RFC text: typecodes, the four domain
  separators, `coef()`, the checksum, node numbering. Cross-verified in both directions against
  **hsslms 0.1.3**, plus a persistent signer with NVM and a hardware monotonic counter.
- **v2.2 fix (F3).** `approved_pair()` refuses a mixed LMS m / LM-OTS n typecode pair at keygen
  (`ValueError`) and at verify (`False`), which is what SP 800-208 §4 requires. The regression is
  S1-012.

### 1.5 Sizes and costs

| quantity | value | derivation | pointer |
|---|---|---|---|
| WOTS+ chains | len1 = 64, len2 = 3, len = 67 | len1 = 8·32/4; len2 = ⌊log2(64·15)/4⌋+1 = 3 | `src/s1s2_hashsig_dnssec-v2.0.py` → `WOTS` |
| XMSS-SHA2_20_256 signature | **2,820 B** | 4 (idx) + 32 (randomiser r) + 67·32 + 20·32 | same file, report `sizes` |
| LM-OTS parameters | w = 1/2/4/8 → p = 265/133/67/34 at n = 32; p = 200/101/51/26 at n = 24 | u = 8n/w; v = ⌈(⌊log2((2^w−1)·u)⌋+1)/w⌉; ls = 16 − v·w; p = u + v | `src/s1_lms.py` test S1-001 |
| LM-OTS W8 one-time signature | 1,124 B | 4 (type) + n + p·n = 4 + 32 + 34·32 | S1-001 |
| **LMS_SHA256_M32_H20 / LMOTS_SHA256_N32_W8** | **1,772 B** | 4 (q) + 1,124 (OTS, incl. its own type) + 4 (LMS type) + 20·32 | S1-001, `results/s1_audit_report.json` → `sizes["LMS_tc8/OTS_tc4"].sig` |
| LMS H20 / W4 | 2,828 B | 4 + (4+32+67·32 = 2,180) + 4 + 640 | S1-001, `sizes["LMS_tc8/OTS_tc3"]` |
| LMS M24_H20 / N24_W8 (NSA-preferred) | 1,140 B | 4 + (4+24+26·24 = 652) + 4 + 20·24 | S1-001, `sizes["LMS_tc13/OTS_tc8"]` |
| LMS public key (m = 32) | 56 B | 4 + 4 + 16 (I) + 32 | S1-001, `sizes[...]["pub"]` |
| Pre-fix LMS size (bug I6) | 1,768 B | 4+4+32+34·32+20·32 — one of RFC 8554's two type fields omitted | `docs/pq-infra-program.md` §9 |
| Verify hashes, WOTS+ w = 16, h = 4 | measured **471** vs bound **1,009**; **531** in the v2.2 report | bound = LEN·(W−1) + 4 = 67·15 + 4. The measured count is a draw, not a constant: the chain steps are `Σ(W−1−d_i)` over the base-w digits of `H("msg", root, addr, msg)`, so it moves when the root moves. The v2.2 root differs from v2.0's because the interior nodes carry their position (§2.6); the bound is unchanged and both counts sit well inside it | v2.0 report; `src/s1s2_hashsig_dnssec.py --report` |
| Verify hash bound, w = 256, h = 20 | **8,692** | 34·255 + 1 + 20 + 1 | v2.0 report |
| Verifier resources | LMS256H20W8: code 2.15 KB, stack 1.81 KB, 2.857 Mcycles | Kampanakis et al., ePrint 2021/041 Table 2 — **literature, not measured** | `docs/pq-infra-program.md` §7 |

The size model was wrong once (bug I6, 1,768 ≠ 1,772) precisely because RFC 8554 carries two type
fields; the fix was a format-specific size function and a regression test. That is the pattern of
this domain: the model proposes, the encoder or the RFC settles it.

### 1.6 Attack games and the reduced Grover simulation

Every hash call is domain-separated by (I, q, i, j) or (I, r, D_INTR), so "each target lives in a
different function, so a Grover search over one function hits at most one target" [R]
(`results/s1_audit_report.json` → `attack_games_n256`).

| game | goal | queries (log2) at n = 256 | gates (log2) | counts toward the bound? |
|---|---|---|---|---|
| G1 | second preimage of Q = H(I‖q‖D_MESG‖C‖m) | 128 | 146 | yes |
| G2 | invert one LM-OTS chain node | 128 | 146 | yes |
| G3 | collision on Q (BHT with QRAM) | 85.33 = 256/3 | 103.33 | **no** — the attacker does not choose C, so a collision gives no forgery in EUF-CMA |
| G4 | forge a Merkle path (interior-node second preimage) | 128 | 146 | yes |
| G5 | find a message whose digit vector dominates a signed one | ∞ | — | impossible: the checksum strictly decreases when any digit increases |

The cheapest *counting* game is G1 (`results/s1_audit_report.json` → `cheapest_game` = "G1"). At
n = 24 the same cheapest game costs 96 queries = 2^114 gates, so the NSA-preferred parameter set
fails the target.

**Reduced Grover simulation** [S]. The target is the real LM-OTS keyed chain oracle with SHA-256
truncated to n ∈ {8, 10, 12, 14} bits, simulated as an exact state vector in numpy. Measured
first-peak iteration k is compared with k_pred = ⌊π/(4θ)⌋, θ = asin(√(M/N)). The recorded ledger
rows were k = 7/17/35/100, each matching its own prediction; a re-run for this repository got
k = 12/25/35/100, again each matching its own prediction — the secret is drawn at random, so the
number of marked states M differs between runs and k moves with it. See §7 for what this does and
does not establish.

### 1.7 Tests

`src/s1_lms.py --self-test` and `history/s1_lms-v2.1.py --self-test`.

| test | what it asserts |
|---|---|
| S1-001 | sizes derived from typecode arithmetic match RFC 8554 / SP 800-208 |
| S1-002 | RFC-exact sign/verify round trip and tamper rejection for every typecode at h = 5 |
| S1-003 | signatures from this implementation verify under hsslms 0.1.3 (independent) |
| S1-004 | signatures from hsslms verify under this implementation; tampering fails |
| S1-005 | every leaf used once in order; the 2^h + 1-th signature is refused |
| S1-006 | power loss at every step boundary, restart, continue: no q appears twice |
| S1-007 | restoring an older NVM record cannot reuse leaves (fails closed by skipping) |
| S1-008 | 16 threads signing concurrently reserve distinct leaves |
| S1-009 | **negative demonstration**: two devices booted from one exported key state produce two signatures under one leaf — the reason export is forbidden |
| S1-010 | cheapest counting game is 2^(n/2) queries; n = 24 fails QPT-128, n = 32 passes |
| S1-011 | exact Grover on the keyed chain oracle: measured optimum equals the closed form |
| S1-012 (v2.2 only) | (F3) non-approved m ≠ n pairs are refused at keygen and at verify |

Measured for this repository: 11/11 in `history/s1_lms-v2.1.py`, 12/12 in `src/s1_lms.py`, both OK

Notes on test strength, from the sources and from the audit stack: S1-012's *verify* assertion also
returns False on the unfixed v2.1 (the signature length no longer matches the claimed OTS type), so
only the two keygen assertions discriminate. S1-011's slope assertion is the flaky one described in
§7.

### 1.8 What S1 does not show

- No hardware, no ROM, no cryptographic module. A-NoExport (the key never leaves the module, the
  index is committed before release) is an assumption.
- No cycle count is measured. The 2.857 Mcycles figure and the stack figures are literature.
- Nothing here is constant-time. The implementation is a Python model.
- The Grover simulation runs at n ≤ 14 bits; it is a *simulation* of the counting law, not a
  measurement of the deployed oracle. The Grover law statement stays labelled simulation.
- The security of the construction rests on cited theorems that are not re-proved here.

---

## 2. S2 — DNSSEC

**Files.** `src/s1s2_hashsig_dnssec.py` (design), `src/s2_dns_worstcase.py` (audit).

### 2.1 The problem

A DNSSEC answer must fit an unfragmented UDP datagram. A single ML-DSA-44 RRSIG is 2,420 B, which
already exceeds every datagram limit below. The v2.0 claim was "solved for any zone size by MTL
ladder + canonical-order sharding + Merkle multiproof + NSEC". The audit narrowed it: "UDP-safe for
any zone size" is **false as stated**.

### 2.2 The binding constraints

| constraint | value | source |
|---|---|---|
| DNS Flag Day 2020 UDP buffer | **1,232 B** = IPv6 minimum MTU 1,280 − 48 | cited by name |
| RFC 9715 §3.1 recommended maximum DNS/UDP payload | **1,400 B** | RFC number given |
| Common EDNS ceiling (above it, TCP) | 4,096 B | — |
| Measured failure rates, IPv4 stub → resolver | ≈0.9 % at ≤ 1,260 B; ≈1.65 % at 1,400–1,480 B; 18.9 % at 1,500 B | Koolhaas–Slokker 2020 (incomplete citation) |
| Validation throughput | signature ≤ 1,232 B **and** ≥ 1,000 validations/s | Müller et al., CCR 2020 Table 2 |
| RRSIG count of a denial | NSEC3 NXDOMAIN: **4** (3 NSEC3 + SOA); NSEC: **3** (SOA + apex NSEC + covering NSEC); compact denial (RFC 9824): **2**, signed online; CNAME chain of length k: k + 1 | RFC 5155 §7.2, RFC 2308 §3, RFC 4035, RFC 9824 |

Binding law of the model: 436 B of overhead + 4 RRSIGs ≤ 1,232 B ⇒ **signature ≤ 199 B** for the
NSEC3 NXDOMAIN case (`results/AUDIT_LEDGER_v2.1.json` → `model_discrepancies.S2` and the v2.0
report). The 436 B is 12 (header) + 24 (question) + 40 (SOA) + 3·60 (NSEC3) + 4·45 (RRSIG shells).

### 2.3 Theory borrowed, and which part

| theory | as used here | which part | not used |
|---|---|---|---|
| MTL mode (Fregly–Harvey–Kaliski–Sheth, CT-RSA 2023; ePrint 2022/1730) | a binary-counter decomposition of N leaves into popcount(N) perfect subtrees; one underlying signature covers the ladder; each record carries a condensed proof | the ladder decomposition and the condensed-signature size formula 5 + (⌊log2 N⌋)·32 | the theorem's security proof — only its **Thm 2 (MM-SPR of the node hash)** is invoked, and that is exactly the assumption the audit then attacks |
| draft-ietf-plants / draft-harvey MTL mode-09 | condensed-signature formula 28 + 3n + n⌊log2 N⌋; `mtl-mode-full` EDNS option | size sanity check (540 B at N = 10^4 with n = 32) | the deployment protocol |
| RFC 9824 compact denial | 2 RRSIGs, signed online | the alternative denial shape and its cost model | — |
| RFC 5155 / 4035 / 2308 | RRSIG counts per denial variant | the RRSIG-count law above | — |
| dnspython 2.8.0 | RFC 1035 name compression, RFC 4034/4035/5155 rdata, EDNS OPT | a real wire encoder and parser | it makes no security claim; it is a byte-format library |

### 2.4 The refutation sequence (what died, in order)

1. **Hypothesis 1 — a compact Category-5 signature fits every response. REFUTED.** SQIsign-V rd2
   (292 B signature) fits the A record (389 B) and DNSKEY (663 B), but the NSEC3 NXDOMAIN denial is
   436 + 4·292 = **1,604 B**.
2. **Hypothesis 2 — the MTL condensed signature alone rescues NXDOMAIN. REFUTED.** The condensed
   signature is 5 + (⌊log2 N⌋)·32 = **645 B** at N = 2^20 (389 B at 2^12, 517 B at 2^16); four of
   them are 436 + 4·645 = 3,016 B.
3. **Hypothesis 3 — SQIsign is the DNSSEC answer. REFUTED by verification.** The v3.0 parameters are
   406 B signature / 169 B public key, so the NSEC denial is 331 + 3·406 = **1,549 B** > 1,400 B;
   and verification at level V costs 35.7 Mcycles, i.e. 3.4e9 / 35.7e6 ≈ **95 verifications/s per
   core**, below Müller's 1,000/s. Compact denial (2 RRSIGs, 226 + 2·406 = 1,038 B) fits but needs
   online signing at 507.5 Mcycles ≈ 7 signatures/s per core, which a random-subdomain flood ends.
4. **What survived — three glued pieces.** (a) the MTL ladder; (b) a **canonical-order Merkle
   multiproof**: RRsets sit in the ladder in canonical zone order (apex NS = 0, SOA = 1, NSEC = 2,
   DNSKEY = 3, then A + NSEC per name), so the SOA and apex NSEC carried by every denial share most
   of their path and one multiproof proves all three denial RRSIGs; (c) **sharded ladders**: one
   ladder per 2^k canonical-order leaves, each signed separately, so a denial needs shard 0 (apex)
   plus shard j and the answer size becomes independent of zone size. The underlying signature can
   then be SLH-DSA-256s (29,792 B, stateless, n = 32), fetched once per shard per TTL over TCP.
   NSEC3 must be abandoned for NSEC: RFC 9276 already zeroes its iterations, and the
   closest-encloser proof is what costs the fourth RRSIG.

### 2.5 The audit: a real wire encoder and a worst-case search

`src/s2_dns_worstcase.py` builds genuine DNS messages with dnspython (name compression, RRSIG /
NSEC / DNSKEY rdata, NSEC3, EDNS OPT) and parses them back. Two protocol decisions are the audit's
own and are labelled as such: the first RRSIG of a shard carries MTL-Type 2 plus the multiproof,
the others MTL-Type 3 plus a 4-byte leaf index; ALG = 18 (the ML-DSA-44 code point) is used as a
placeholder. The worst case is searched by random sampling plus hill climbing over names, labels,
apex length, DNSKEY count, rollover double-signing, CNAME chains, wildcard, bitmap windows, denial
variant, protocol and shard size.

| quantity | value | pointer |
|---|---|---|
| Exact wire, the model's own baseline zone shape | **954 B** (the model said 1,129 B) | `results/s2_audit_report.json` → `baseline_exact.NXDOMAIN`, `model_claim_nxdomain_shard12` = 1129 |
| Realistic worst NXDOMAIN, NSEC, batched | **1,530 B** — 3 labels of 20 chars, 30-char apex, two keys double-signing during rollover, 2^14 shards | `docs/pq-infra-audit.md` |
| The same with no double-signing | **1,361 B** | `docs/pq-infra-audit.md` |
| … and shards of 2^10 | **1,287 B** (≤ 1,400, still > 1,232) | `docs/pq-infra-audit.md` |
| Worst case over *all* variants | **1,839 B**: NSEC3, 3 labels, 30-char apex, 1 key, 2 RRSIGs, 2 bitmap windows, shard 2^10 | `results/s2_audit_report.json` → `worst_case["NXDOMAIN/realistic"]` |
| Realistic worst, other types | CNAME 1,513; WILDCARD 1,260; DNSKEY 822; A 661 | `worst_case` (`/realistic` rows) |
| Pathological (uncapped search) | NXDOMAIN 2,120; CNAME 3,830; WILDCARD 1,597; DNSKEY 912; A 790 | `worst_case` (`/pathological` rows) |
| Multiproof NSEC denial, 2^10 names (2,052 leaves) | **988 B** answer vs 1,071 B for three separate condensed signatures | v2.0 report |
| Multiproof NSEC denial, 2^14 names (32,772 leaves) | **1,244 B** vs 1,455 B separate | v2.0 report |
| Multiproof over NSEC3-style random owners | 1,609 B (2^10) / 2,121 B (2^14) — EDNS-only | v2.0 report |
| Sharded worst NXDOMAIN at .com scale (160 M names) | 2^10: 312,501 shards, 1,001 B; **2^12: 78,126 shards, 1,129 B**; 2^14: 19,532 shards, 1,257 B; 2^16: 4,883 shards, 1,385 B | v2.0 report |
| Ladder response with SLH-DSA-256s | 29,913 B (TCP fallback) | v2.0 report |
| Validation rate | SQIsign-V 95/s, SQIsign-I 667/s, against a 1,000/s requirement | v2.0 report |

The corrected domain statement is therefore: **typical zone shapes are UDP-safe at 1,232 B;
realistic worst cases need RFC 9715's 1,400 B and small shards; rollover windows should be
TCP-tolerant** (`docs/pq-infra-audit.md`, findings §2).

### 2.6 The finding that matters most: unprefixed Merkle nodes

The v2.0 ladders and multiproofs hash interior nodes as `H("node", l, r)` with **no position
prefix**. Single-structure second preimage resistance is 2^−n per query either way — a first-run
reading of a log2(depth) loss was a per-trial/per-query mis-accounting, corrected and kept on the
record as A3 (`results/s2_audit_report.json` → `binding_game_per_query`: at n = 8, 109/24,576
unprefixed and 145/24,576 prefixed against an expected 2^−8 = 0.00390625).

The problem is the **multi-target** game. An adversary holding T signed structures tests one node
evaluation against all T targets at once; the prefixed variant commits to one position per query:

| measurement | unprefixed | prefixed | expectation |
|---|---|---|---|
| n = 16, T = 64, per 100k queries | 90 | 1 | 97.66 / 1.53 |
| n = 16, T = 256, per 100k queries | 401 | 2 | 390.63 / 1.53 |

(`results/s2_audit_report.json` → `multi_target_game`.) At production parameters with T ≈ 2^40,
the ledger gives an unprefixed cost of 2^(n/2)/√T queries → 128 − 20 + 18 = **2^126 gates**, which
is *inside* the 2^128 budget, i.e. it **fails QPT-128**; the prefixed variant is 2^146 and passes
(`results/s2_audit_report.json` → `multi_target_ledger_n256`).

The fix costs zero bytes: hash `H(node, ladder_id, rung, level, index, l, r)` — exactly
what RFC 8554's (I, r) and XMSS-T's addresses already do. It was first implemented inside the audit
file (`prefixed_multiproof_build` / `prefixed_multiproof_verify`) and **is now applied to the design
files as well**:

| file | structure | prefix on an interior node |
|---|---|---|
| `src/s1s2_hashsig_dnssec.py` | XMSS-style Merkle tree (S1) | `H('node', public seed, level, parent index, l, r)` |
| `src/s1s2_hashsig_dnssec.py` | MTL ladder, condensed proof, multiproof (S2) | `H('node', rung, level, parent index, l, r)` |
| `src/s3_tls_pki.py` | MTC batch tree (S3) | `H('mtc-node', batch id, level, parent index, l, r)` |
| `src/s5_smartcard_hsm.py`, `src/s5_bds_faults.py` | on-card LMS tree under BDS traversal (S5) | `H('node', public seed, level, parent index, l, r)` |

Every prefix field is already held by the verifier (the public seed is half the S1 and S5 public key,
and the rung, batch id and leaf index travel in the proof), so nothing was added to the wire and no
`--report` byte count moves. The S1 tree needed it too: the WOTS+ address `addr` binds the *leaves*
of a tree and never reaches the interior nodes, so before this every key pair's interior nodes sat in
one function. The S5 card tree is the same tree under a different traversal, and needed it for the
same reason with T counted over fielded devices rather than zones. `src/s1s2_hashsig_dnssec-v2.0.py`
keeps the unprefixed hashing as the record of what v2.0 was. Each file carries regressions
(`test_s2_006_*`, `test_s1_006_*`, `test_s5_006_*`,
`test_mtc_node_hash_is_position_prefixed`) that fail against the previous hashing: a node at one
position no longer equals the same child pair at another, a condensed proof built for one leaf no
longer verifies at another leaf whose subtree repeats, an authentication path lifted to another leaf
of a tree whose subtrees repeat is refused where the card's own self-check used to accept it, and the
multiproof verifier rejects a proof whose nodes were computed without prefixes. The caveat is stated
in the source: the
prefixed variant of the measured game assigns each query to one target position by construction, so
it demonstrates the counting argument rather than independently discovering it, and MM-SPR is
"measured only at n ≤ 14 bits" while the same file runs the game at n = 16 — a wording
inconsistency that is recorded rather than smoothed over.

### 2.7 Tests

`src/s2_dns_worstcase.py --self-test`.

| test | what it asserts |
|---|---|
| S2-001 | responses parse back with dnspython and carry the expected RRSIG count |
| S2-002 | exact wire size of the model's baseline case vs the model's 1,129 B |
| S2-003 | realistic-legal worst case per response type under the batched protocol |
| S2-004 | multiproof manipulation games: remove a leaf / reorder nodes / foreign node / changed statement all rejected; an extra unused node is rejected by the independent verifier only — the v2.0 reference verifier accepted it, which became finding F2 |
| S2-005 | single-structure second preimage: per query ≈ 2^−n for both variants |
| S2-006 | the multi-target finding above: with T signed structures, unprefixed node hashing fails QPT-128 |

Two falsified test hypotheses are kept on the record: A2 — "reordering the node list breaks
verification" was *accepted*, because nodes carry explicit (level, index) coordinates and their
order is irrelevant; the test now swaps hash values instead. A3 — the per-trial / per-query
mis-accounting above.

### 2.8 What S2 does not show

- Resolver and middlebox behaviour above 1,232 / 1,400 B is taken from the literature, not measured
  here.
- MM-SPR of the node hash is assumed, and measured only at n ≤ 16 bits.
- The shard model uses one synthetic ladder for both shard 0 and shard j.
- The MTL-Type 2/3 protocol, the ALG = 18 placeholder and several encoding choices are the audit's
  own decisions, not an IETF draft.
- The multi-target fix is **not** in the design files.
- The 1,129 B v2.0 figure for the modelled zone shape does not reproduce: the exact encoder gives
  954 B for that shape and 1,839 B for the worst legal shape. Both numbers are kept.

---

## 3. S3 — TLS 1.3, QUIC and the Web PKI

**Files.** `src/s3_tls_pki.py` (design), `src/s3_tls_wire.py` (audit).

### 3.1 The problem

The obvious Category-5 chain — ML-KEM-1024 plus ML-DSA-87 everywhere — makes the server's first
flight 30,959 B in the model (31,021 B exact), far past the TCP initial window and past the
measured "10 kB cliff". Chrome's 2026 position is that PQ X.509 will not enter the Chrome Root
Store and an MTC-based quantum-resistant root store is targeted for Q3 2027; CQRP cosigners are
ML-DSA-44, which is Category 2 and outside QPT-128.

### 3.2 The binding constraints

| constraint | value | source |
|---|---|---|
| RFC 9000 §14.1 | client Initial padded to ≥ 1,200 B | RFC number given |
| RFC 9000 §8.1 anti-amplification | server may send ≤ 3× the bytes received before address validation | RFC number given |
| QUIC server budget | 3 · max(ClientHello, datagrams · 1,200) — a Category-5 ClientHello (1,811 B exact) is 2 datagrams, so **7,200 B** | `results/s3_audit_report.json` → `part_a.ledger` |
| TCP initial congestion window | 10 MSS = 10 · 1,460 = **14,600 B** | — |
| The 10 kB cliff (Cloudflare pq-2024, pq-2025) | +9 kB ≈ 15 % slower; crossing +10 kB extra costs a round trip (> 60 %) and trips middleboxes; a second bump at 30 kB; ML-DSA-44 everywhere ≈ +15–17 kB; median compressed chain today 3.2 kB | blog titles only (incomplete citation) |
| Smallest Category-5 KEM public key | ML-KEM-1024 at 1,568 B > 1,455 B (Classic McEliece has 194–208 B ciphertexts but ~1 MB keys), so a Category-5 ClientHello is always two datagrams | — |

### 3.3 Theory borrowed, and which part

| theory | as used here | which part | not used |
|---|---|---|---|
| Merkle Tree Certificates (draft-davidben-tls-merkle-tree-certs; draft-ietf-plants-merkle-tree-certs) | the CA signs a batch root; the handshake carries an inclusion proof of 32·log2(batch) bytes instead of CA signatures and SCTs | the proof shape and the security statement "second-preimage resistance of the hash plus the CA's signature on the root, which never travels in the handshake" [R as stated] | the drafts are not implemented as written; the assertion/proof encoding follows the draft's field shapes but the audit's own assembly |
| KEMTLS (Schwabe–Stebila–Wiggers CCS 2020; ePrint 2020/534; KEMTLS-PDK ePrint 2021/779) | the server authenticates by KEM decapsulation, so it never signs | the handshake *shape* — which messages carry what — not the proof | the multi-hop and PDK variants |
| RFC 8446 §4 | handshake message and extension encoding | exact byte layout | — |
| RFC 6962 §3.2 | the SignedCertificateTimestamp structure for SCT bytes; RFC 6962-style trees as a multi-target class | byte structure and the class of trees exposed to the S2-006 attack | transparency-log semantics |
| FIPS 203 Table 3 | ML-KEM sizes (768: 1,184/1,088; 1024: 1,568/1,568) | the byte counts | — |

### 3.4 The construction

Four candidate designs were carried through the audit: **G1** Merkle Tree Certificates; **G2** a
compact Category-5 server signature (SQIsign-V, 292 B signature / 129 B key); **G3** KEMTLS; **G4**
the observation that a bigger KEM gives the server *more* room under the 3× amplification rule, not
less. The recommended combination is **MTC + KEMTLS with ML-KEM-1024**, with
SQIsign/OV-V reserved for the offline cosigner role.

The audit builds a real RFC 8446 handshake encoder, a DER X.509 template, the MTC assertion and
proof encoding, TLS record framing, QUIC datagram packing and TCP segmentation; Part B runs KEMTLS
on an ideal-KEM toy with eight network-adversary games plus a positive control; Part C reports CPU
numbers from verified literature only.

Model versus exact bytes, exact values from `results/s3_audit_report.json` → `part_a.ledger`:

| config | Cat | server flight (model) | exact handshake | Δ | TCP bytes | QUIC UDP bytes | datagrams | QUIC 3× / TCP |
|---|---|---|---|---|---|---|---|---|
| classical today | 0 | 1,520 | 1,554 | +34 | 1,653 | 1,708 | 2 | fits / fits |
| deployed hybrid X25519MLKEM768 + ECDSA | 0 | 2,608 | 2,642 | +34 | 2,741 | 2,847 | 3 | fits / fits |
| naive ML-DSA-44 chain | 2 | 16,884 | 16,930 | +46 | 17,029 | 17,735 | 15 | no / no |
| naive ML-DSA-87 chain | 5 | 30,959 | 31,021 | +62 | 31,142 | 32,396 | 26 | no / no |
| X.509 + SQIsign-V | 5 | 4,358 | 4,416 | +58 | 4,515 | 4,671 | 4 | fits / fits |
| MTC + ML-DSA-87 | 5 | 9,939 | 9,859 | −80 | 9,958 | 10,364 | 9 | **no** / fits |
| MTC + SQIsign-V | 5 | 3,141 | **3,061** | −80 | 3,160 | 3,266 | 3 | fits / fits |
| MTC + MAYO-5 | 5 | 9,238 | 9,158 | −80 | 9,257 | 9,613 | 8 | **no** / fits |
| **MTC + KEMTLS ML-KEM-1024** | 5 | 4,280 | **4,148** | −132 | 4,203 | 4,403 | 4 | fits / fits |
| MTC + OV-V (pk in handshake) | 5 | 449,972 | **not encodable** | — | — | — | — | no / no |

The category column is the minimum over the KEM category (maximum over hybrid components), the
chain signature and server authentication; that is why the deployed hybrid row reports 0 — the
ECDSA authentication drags it down. That min-over-auth rule is itself a refuted hypothesis, I5,
which was fixed in the *KEM* part only.

The KEMTLS flight, exactly (`a3` → `part_a.ledger` row 9):

- ServerHello = 90 + ct 1,600 = **1,690 B**; EncryptedExtensions = **19 B**; Certificate = **2,439 B**
  (assertion 1,612 + proof 797 + 2 + extension 17); total **4,148 B**.
- On TCP: (5 + 1,690) + CCS 6 + (5 + 1 + 16 + 19) + (22 + 2,439) = **4,203 B**.
- There is **no** CertificateVerify and **no** Finished in this flight: the server's Finished follows
  the client's KEM ciphertext, so the client's second flight is **1,626 B**.
- The ServerHello alone exceeds one 1,200-B Initial datagram: with any ML-KEM hybrid the server
  spends 2 padded Initial datagrams (2,400 B of the 7,200-B budget) on it.

Worst-case legal certificate (S3-009, random + hill-climb over 2,000 samples, converging on the
analytic maximum): **X.509 29,636 B**, **MTC 26,628 B**, at 100 SANs of 253 characters. Under that
certificate every recommended configuration breaks — MTC + SQIsign-V 28,689 B / 25 datagrams,
MTC + KEMTLS 29,776 B / 25, X.509 + SQIsign-V 31,134 B / 27 — while a typical 25 × 30-char SAN
certificate still fits (3,808 / 4,895 / 5,194 B). A name-count cap therefore belongs in the
deployment specification.

CPU axis (Part C, literature only): SQIsign-V signing costs 507.5 Mcycles, i.e. **6.7 handshakes
per second per core** at 3.4 GHz; an X.509 + SQIsign-V client verifies 5 × 35.7 = 178.5 Mcycles.
ML-KEM-1024 encaps/decaps, ML-DSA-87 and MAYO-5 are `None` — "not verified here", no number
invented. Bytes (B) and CPU (T) are reported as two separate axes, and the programme's own
"ML-KEM-1024 decapsulation is ~10⁴× cheaper" sentence is **unverified** and must not be quoted as a
result.

### 3.5 The KEMTLS attack games

Nine games on the ideal-KEM toy (`results/s3_audit_report.json` → `part_b.games`). The toy stores
encapsulation randomness in a registry the adversary never reads — that *is* the IND-CCA assumption.

| game | what the adversary does | outcome |
|---|---|---|
| POSITIVE-CONTROL | honest network | handshake completes, keys equal |
| MITM | substitutes its own ephemeral key share and knows both ephemeral secrets | BLOCKED — server `decrypt_error` on the client Finished |
| SERVER-KEY-SUBSTITUTION | owns a legitimately certified key in another batch | BLOCKED — `bad_certificate`, inclusion proof fails |
| TRANSCRIPT-ALTERATION | flips one byte of any field | BLOCKED — 13 single-field mutations across 7 messages, all rejected |
| REPLAY | recorded a full previous session including the client's ephemeral secret | BLOCKED — `decrypt_error` both sides (fresh ct_e under the new ephemeral key) |
| DOWNGRADE | removes the Category-5 group, supplies a Category-3 share | BLOCKED — client `illegal_parameter`; masked ServerHello → server `decrypt_error` |
| CROSS-SERVER-KEY-CONFUSION | *is* server b.example with a valid certificate | BLOCKED — "hostname not in assertion claims"; **with that check off the attack succeeds**, so the hostname claim is the only barrier |
| CERT-SUBSTITUTION | runs its own CA / batch | BLOCKED ×3 — `unknown_ca`, proof fails |
| KEM-CIPHERTEXT-SUBSTITUTION | replaces ct_S with its own encapsulation | BLOCKED — server `decrypt_error` |

Five hypotheses were refuted and are recorded: **H1** exact framing flips a fit/no-fit verdict (0
changes; |Δ| ≤ 132 B); **H2** the KEMTLS first flight carries a Finished; **H3** the ServerHello
fits one Initial packet; **H4** OV-V can be an MTC subject (a 446,992-B key overflows
`opaque<0..2^16-1>`); **H5** hostname binding is redundant given the Finished MACs.

### 3.6 Tests

`src/s3_tls_wire.py --self-test` (20 tests).

| test | what it asserts |
|---|---|
| S3-001 | TLS vectors, DER length encodings, record fragmentation and QUIC varints are exact |
| S3-002 | exact ClientHello vs the model's CH_BASE; client Initial datagram counts |
| S3-003 | ServerHello = 90 B + ct exactly (the model's SH_BASE is exact); with ML-KEM it needs two Initial packets |
| S3-004 | the DER X.509 template is well-formed; TBS overhead vs the model's CERT_TBS = 350 |
| S3-005 | the MTC Certificate message's exact bytes; the proof verifies with the model's MTCBatch |
| S3-006 | exact per-config numbers vs the model; the fits/does-not-fit verdict set is the audit result |
| S3-007 | datagram split, the 3× budget with exact client Initials, IPv4/IPv6 wire totals, TCP segments vs initcwnd |
| S3-008 | KEMTLS server first flight has no CertificateVerify/Finished; the client's second flight carries ct_S + Finished |
| S3-009 | the largest legal Certificate for the MTC and X.509 forms (random + hill climb) |
| S3-010 … S3-018 | the nine KEMTLS games above |
| S3-019 | CPU numbers only from verified literature; ML-KEM decapsulation is `None`; B and T reported separately |
| S3-020 | `--report` is valid JSON with the required sections and per-game records |

### 3.7 What S3 does not show

- The KEM is a toy; IND-CCA of ML-KEM is an input, not re-derived.
- No CPU number is measured. Six of the eight primitives in the CPU table are `None`.
- The MTC prototype hashed `H('mtc-node', l, r)` with no index — the same multi-target exposure as
  S2-006. **Flagged, still not measured at n = 256, and now fixed**: the prototype binds each node
  to (batch id, level, parent index), §2.6. The separation it rests on is still the ledger
  computation over a game run at n ≤ 16 bits.
- The largest legal certificate breaks every recommended configuration; a name-count cap is
  proposed, not standardised.
- The `10 kB cliff` and the failure-rate curve are Cloudflare/Chrome web posts cited by title only.
- Some FAILED_ASSUMPTIONS pointers do not align with the test that asserts the fact (A9 cites
  S3-006 while the flight shape is asserted in S3-008; A10 cites S3-007 while the ServerHello spill
  is S3-003; A11 cites S3-008 while non-encodability is asserted in S3-006).

---

## 4. S4 — constrained broadcast

**Files.** `src/s4_embedded_broadcast.py` (design), `src/s4_tesla_adversarial.py` (audit).

### 4.1 The problem

For ICS, satellite, medical, automotive and other embedded receivers of authenticated broadcast,
"the blocker is not CPU, it is the LINK". These devices are usually receivers, not signers. A
Category-5 signature does not fit a link frame — ML-DSA-87 needs 91 LoRa SF12 frames, i.e. 182
seconds at 0.5 frames/s. The design that survives is TESLA delayed key disclosure, widened to
256-bit chain keys so that chain one-wayness is a 2^128 quantum preimage, anchored by one hash-based
signature per chain.

### 4.2 The binding constraint: link frames

| link | payload per frame | frames/s |
|---|---|---|
| LoRa SF12 (EU868) | 51 B | 0.5 |
| Iridium SBD | 340 B | 0.05 |
| BLE 5 (DLE) | 244 B | 100 |
| CAN-FD | 64 B | 5,000 |
| 9.6 kbps serial | 1,200 B | 1 |
| NB-IoT (typical) | 1,200 B | 10 |

Frames = ⌈bytes / payload⌉. ML-DSA-87 (4,627 B) needs 91 LoRa frames, 14 Iridium frames, 19 BLE,
73 CAN-FD. XMSS-SHA2_20_256 (2,820 B) needs 56. LMS w8 h20 (1,772 B) needs 35 (70 s). 256-bit TESLA
needs 2 LoRa frames — and the audit notes the 4-byte index is what pushes it to two.

### 4.3 Theory borrowed, and which part

| theory | as used here | which part | not used |
|---|---|---|---|
| TESLA (Perrig–Canetti–Tygar–Song 2000/2002; RFC 4082) | a MAC chain where each key is disclosed one interval later, so a receiver that is provably late accepts, and a receiver that is early cannot forge | §3.3 (the security statement, as a reduction sketch), §3.4 (the disclosure delay d = ⌈(Δt+2ε)/T⌉ + 1) and §3.5 (the safe-packet test) — the three parts the code implements | the broadcast-authentication proof; nothing here is re-proved |
| LM-OTS w = 8 / SP 800-208 Table 1 | the anchor: one 1,772-B signature per 2^16-key chain, so the anchor is paid once per chain | the size and the second-preimage security at n = 32 | — |
| Galileo OSNMA | the deployed baseline — TESLA with 128-bit keys, which **fails** QPT-128: 2^64 · 2^18 = 2^82 gates | the counter-example that fixes the key length at 256 bits | OSNMA's own protocol |

The security statement as used: with a loose time-sync bound, forging requires "either a MAC forgery
(online, 2^−t per try, no offline Grover advantage) or a preimage of the chain hash" [R as cited].

### 4.4 The construction

- Chain keys: keys[0] is the public anchor; K_i = H('tesla-chain', K_{i+1}).
- Per message: 4 B index + 16 B MAC + 32 B disclosed key = **52 B**; the first d packets of a chain
  carry no key and cost **20 B**.
- MAC = HMAC-SHA3-256 truncated to 16 B.
- Receiver safety test (RFC 4082 §3.5): reject if receiver_interval + sync ≥ i + d.
- Replay filter on the (index, body) seen set — the source of BUG-2 below.
- One hash-based signature anchors a chain of 2^16 keys; amortised cost 52 + 1,772/65,536 =
  **52.03 B** per message.

The audit does not re-implement the design. It wraps it in a discrete-event adversarial network
(skew, delay, loss, duplication, reordering), sweeps a 270-point boundary grid, runs six attack
games each with a positive control, and does the byte accounting. Bugs are fixed **only in the
subclass `FixedTeslaReceiver`**; the design file is unchanged.

### 4.5 Boundary conditions

For the granular receiver, every genuine packet is accepted iff ⌈(Δt + ε)/T⌉ + ⌈ε/T⌉ ≤ d − 1 with
sync = ⌈ε/T⌉; for RFC 4082's continuous rule, ⌈(Δt + 2ε)/T⌉ ≤ d − 1, i.e. d = ⌈(Δt + 2ε)/T⌉ + 1.
The grid is d ∈ {1,2,3,4,6,8} × Δt ∈ {0,250,500,1000,1500,2000,3000,4000,6000} ms ×
ε ∈ {0,250,500,1000,2000} ms = **270 points** at T = 1,000 ms. Measured: zero mismatches between
the derived inequality and every grid point for both rules (`results/s4_audit_report.json` →
`boundary.mismatches_granular`, `mismatches_continuous` are both empty), **13/270** points where
the granular receiver is stricter than the continuous rule (ε not a multiple of T), **112/270**
points where all packets are accepted, and **0** forged packets accepted anywhere.

### 4.6 The attack games

| game | adversary capability | attempts | wins | the control that proves the test can win |
|---|---|---|---|---|
| FORGE | all disclosed keys K_1…K_{c−d}, transcript, injection, bit flips of in-flight packets | 463 | 0 | 1/1 with the true undisclosed K_{c+1} |
| REPLAY | record and re-deliver authenticated packets | 3 | 0 | 1/1 with receiver state lost |
| LATE | delay a genuine packet until its key is public | 8 | 0 | 1/1 with the safety test disabled |
| REORDER | reorder, swap, drop disclosures, substitute keys | 4 | 0 | 1/1 (the original receiver accepts the reordered stream) |
| KEY | relabel K_j as K_j′ and MAC with K_j | 78 | 0 | 1/1 |
| ANCHOR | forged, re-signed, key-substituted, validly signed rollback, replayed anchors | 5 | 0 | 2/2 — "the old chain-1 anchor still VERIFIES (the signature alone does not stop rollback)"; only the monotone (chain_id, start) pair does |

Total **561 attempts, 0 wins** (`docs/pq-infra-audit.md` findings §4;
`results/s4_audit_report.json` → `games`).

### 4.7 The two receiver bugs

- **BUG-1 (liveness).** Only `pending[i−d]` of the packet that carried a key is drained. If the
  packet disclosing K_i is lost or late, packets buffered for interval i are stranded even though
  K_i = H(K_{i+1}) is derivable from the next disclosure. Reproduction is S4-005; the loss sweep is
  S4-004. Fix: `FixedTeslaReceiver` records every intermediate chain key and drains every pending
  bucket whose key is known.
- **BUG-2 (denial of service).** The replay filter keys on the **unauthenticated** (index, body),
  so a pre-injected junk-MAC copy of a packet makes the genuine packet look like a replay.
  Reproduction is S4-006. Fix: duplicate suppression *after* MAC verification, on (index, payload).
  The FAILED_ASSUMPTIONS entry for this (A15) cites S4-005 — a pointer mismatch in the source.

Five model discrepancies are recorded (`results/s4_audit_report.json` → `model_discrepancies`):
1. "52 B per message" holds only for i > d.
2. The `TeslaReceiver` docstring says the receiver may *lead* by sync, but the code and RFC 4082
   bound the *sender* leading; "the dangerous direction is receiver lag".
3. The granular receiver is stricter than RFC 4082's continuous rule whenever ε is not a multiple
   of T.
4. The 1,772-B anchor figure is the LMS w8 size *formula*; the only executable Merkle signer in the
   repository is WOTS w16 (2,820 B at h = 20 including the randomiser).
5. Pending buckets are never pruned: any injected index inside the safe window allocates receiver
   memory — a DoS surface, not a forgery.

### 4.8 Tests

`src/s4_tesla_adversarial.py --self-test` (14 tests): S4-001 benign-link wiring; S4-002/S4-003 the
boundary inequality at every grid point for the granular and the continuous rule; S4-004 the loss
sweep; S4-005/S4-006 reproduction of BUG-1 and BUG-2; S4-007…S4-012 the six games; S4-013 byte
accounting; S4-014 the report is JSON.

### 4.9 What S4 does not show

- The time-sync bound ε is an assumption. So are PRF security of truncated HMAC-SHA3-256, the
  one-wayness of the SHAKE256 chain, and the state management of the anchor signature.
- No radio, no satellite link, no real-time clock was tested. Link figures are order-of-magnitude
  and the link framing constants (LoRa 13 B, Iridium SBD ≈ 30 B) are assumed.
- The executable anchor signer is WOTS w16, not the LMS w8 whose size the accounting uses.
- The fixes for BUG-1 and BUG-2 exist only in the audit subclass.
- The design file `src/s4_embedded_broadcast.py` is unchanged by the audit.

---

## 5. S5 — smart cards, secure elements, HSMs

**Files.** `src/s5_smartcard_hsm.py` (design), `src/s5_bds_faults.py` (audit).

### 5.1 The problem

PQ signatures do not fit a card: 2–8 KB of RAM, ISO 7816 APDUs of 256 B, decades in the field, and
unlike firmware these devices must **sign**. The reframing that makes the study tractable is that
SP 800-208 §8.1's requirements — no key export, the index committed to NVM before release, FIPS
140-3 Level 3 or better — *describe a smart card already*. "The 'state problem' … is a non-problem
on a device with a tamper-resistant monotonic counter and no backups" [A].

### 5.2 The binding constraints

| constraint | value |
|---|---|
| Card RAM | Infineon SLE 78CLX **8 KB**; NXP SmartMX3 P71 **12 KB** |
| ISO 7816-4 APDU | short response ≤ 256 B; extended ≤ 65,535 B |
| Classical baseline | EMV RSA-1984 = 248 B |
| Persistent state | BDS state in NVM; claimed bound < 2,048 B — **refuted below** |

### 5.3 Theory borrowed, and which part

**BDS traversal** (Buchmann–Dahmen–Schneider 2008), "as in the RFC 8391 reference implementation's
`bds_round` / `bds_treehash_update`". The part used is the **cost claim**: at most (h−k)/2 leaf
computations per signature and O(h²)-bounded state. The audit's job is exactly to test that part —
and it does not survive unchanged (the worst round is (h−k)/2 **+ 1**). The comparative literature
is used only as numbers: Bos–Renes–Sprenkels ePrint 2022/323 Table 2 (ML-DSA-87 signing in 8.1 KiB
— fits the P71, not the SLE 78); Kampanakis et al. ePrint 2021/041 Table 2 (LMS verify stack
1.81 KB, 2.857 Mcycles); Botros–Kannwischer–Schwabe ePrint 2019/489 Table 3; ePrint 2019/893
(Falcon-1024 signing needs 51–80 KB, so it is excluded from cards); pqm4 `benchmarks.md` commit
90bfb63 (ML-DSA-44/65 `m4fstack` figures — note Category 5 is *not* in that table).

### 5.4 The construction

On-card LMS with n = 32, w = 8, h = 20, with BDS traversal maintaining the authentication path
between signatures. `CardSigner` commits the index before release and derives only the one-time
secret — 34 hashes. The alternative in the literature is ML-DSA-87 in 8.1 KiB, which fits the P71
but not the SLE 78.

Interior nodes carry their position, the S2-006 fix of §2.6: `H('node', public seed, level of the
two children, index of the parent, l, r)`. The card tree is the S1 tree under a different traversal
and had the same exposure, with T counted over fielded devices rather than zones — at n = 256 and
T = 2^40 the unprefixed multi-target second preimage is 2^126 gates, inside the budget the card
claims through S1. What makes the fix practicable here is that BDS already tracks both coordinates:
the key-generation stack carries (node, height, index); the round that rebuilds `auth[tau]` knows
tau and the leaf index s, and the node it builds is the one at level tau with index ((s+1) >> tau) ^ 1;
and a treehash node's index is `last leaf consumed >> height`, because a completed subtree ends at
the leaf that completed it. Five places in `src/s5_smartcard_hsm.py` form or refold a node — those
three, the independent naive recomputation the tests compare against, and the card's verifier — and
one more in `src/s5_bds_faults.py`, the self-check that folds a leaf up its stored path. All six
must produce identical bytes at the same position, since BDS reaches one node by several routes;
that is what the h = 2…12 exhaustive comparison (S5-001) checks. Serialised BDS state carries the
public seed, so a card restored from NVM rebuilds the same nodes.

### 5.5 Every size and cost, with the corrected values

| quantity | value | derivation | pointer |
|---|---|---|---|
| BDS state byte model | h·32 (auth) + (h/2+1)·32 (keep) + (h−k)·40 (treehash) + stacks·33 + retain·32 + 8 | a byte model, not a serialisation | `src/s5_smartcard_hsm.py` |
| v2.0 state at h = 8, k = 2 | **664 B** (the **end** state after 256 signatures) | 256 + 160 + 240 + 8 | v2.0 report; the audit corrects this |
| Measured peak state (audit) | h = 8: **828**; 10: 1,037; 12: 1,312; 14: 1,554; 16: 1,763; 18: 1,939; **20: 2,148 B** | peak during the run, not the end state | `results/s5_audit_report.json` → `sweeps[h].peak_state_bytes` |
| v2.0 cost, h = 8, k = 2, w = 256 | **30,466.4** hashes/signature, 3.01 leaf computations/signature | instrumented counter | v2.0 report |
| Re-measurement | **30,445.5** (real signer, 256 signatures); composed model 30,555.1 (0.36 % high); h = 10: 39,109.9 vs 39,210.0 | `composition_check` | `results/s5_audit_report.json` → `composition_check` |
| Per-leaf keygen hashes, w = 256 | **8,705** = 34·255 + 34 + 1 | — | audit |
| OTS sign average, w = 256 | 4,370 = 34 + 34·127.5 + 1 | — | audit |
| **v2.0 projection, h = 20** | ≤ **86,720** — **refuted** | (h−k)/2 = 9 leaves × 34·255 | v2.0 report |
| **Maximum, h = 20 (audit)** | **95,775** | leaf max = (h−k)/2 **+ 1** = 10, measured on the 2^15-signature prefix window and equal to the bound | `results/s5_audit_report.json` → `h20_steady_state_w256.hashes_max` |
| Mean, h = 20 (audit) | **82,727** = 9·8,705 + 12 + 4,370 | the mean law (h−k)/2 is validated at h = 8…16: 3.0078, 4.0020, 5.0005, 6.0001, 7.00003 | `mean_formula_check` |
| Leaf computations max per signature | 4/5/6/7/8/9/10 at h = 8/10/12/14/16/18/20 = (h−2)/2 + 1 | — | `sweeps[h].leaf_per_sig.max` |
| APDU chunks | LMS 1,772 B → **7** short APDUs; ML-DSA-87 4,627 → 19; ML-DSA-44 → 10; XMSS 2,820 → 12; SQIsign-V → 2; RSA-1984 → 1; all fit one extended APDU | ⌈bytes/256⌉ | v2.0 report |
| Working memory | OTS buffer 34·32 = 1,088 B; chain temp 64 B | plus the persistent state | `working_memory_bytes_estimate` |

Three claims are corrected, not overwritten: state is 828 B at h = 8 (not 664 B — the 664 B was the
*end* state); the maximum at h = 20 is 95,775 hashes (not 86,720 — BDS needs (h−k)/2 + 1 leaf
computations in the worst round); and the persistent state at h = 20 is 2,148 B, i.e. 2.1 KB, which
is **above** the claimed "< 2 KB". The 30,466 figure is confirmed (30,445 measured).

The table is the v2.1 record and stays as recorded. Two of its *measured* means move when the
suites are re-run against the current source, and only those two: 30,445.5 → **30,477.4** at h = 8
and 39,109.9 → **39,097.0** at h = 10. The position prefix changed the tree root, the message
digest is `H('msg', root, addr, msg)`, and the number of WOTS chain steps is a function of that
digest — so a per-signature hash count is a draw around 34·127.5, not a fixed number (S1 records
the same effect, `docs/pq-infra-program.md`). Everything counted rather than drawn is unchanged to
the bit: leaf computations per signature, node hashes per signature (mean 2.066, max 6 at h = 8),
every peak-state figure, every h = 20 row and every byte count in the domain.

### 5.6 Tests

`src/s5_bds_faults.py --self-test` (7 tests: the five below and two S2-006 regressions);
`src/s5_smartcard_hsm.py --self-test` (7: T1–T3, the APDU table and three S2-006 regressions).

| test | what it asserts |
|---|---|
| S5-001 | BDS produces the same authentication path as the naive computation for every leaf, h = 2…12, every valid k — more than 43,000 path checks |
| S5-002 | skip / jump / rollback / corruption / serialise-restore behave as required |
| S5-003 | measured leaf computations per signature for h = 8…12 against the composed model and the (h−k)/2 + 1 bound |
| S5-004 | power loss after **every** hash call of a signing operation (h = 4, w = 16), roughly 120 injection points: no leaf is ever reused and every later signature still verifies |
| S5-005 | the 2^h + 1-th signature is refused and the index is monotone |
| `test_s5_006_*` | the S2-006 regressions: a node binds the public seed, the level and the parent index, so the same child pair one position over is a different node; the traversal state survives serialise/restore with the prefix intact; and an authentication path lifted to another leaf of a tree whose subtrees repeat is refused, where the self-check accepted it before. Each fails against the previous hashing. They are named outside the `S5-0NN` range deliberately: `src/audit_ledger.py` collects a suite's findings by that ID form, and these are regressions on a design-file fix rather than new audit findings, so the ledger's per-finding rows and its 70-test total do not move |

Test-quality notes kept from the source: `src/s5_bds_faults.py` contains one **vacuous** assertion
(an `… or True` clause); the effective check is the following one. The card inherits S1's security;
this study "adds no cryptographic claim" of its own.

### 5.7 What S5 does not show

- Atomic persistence of the {q, bds} record is assumed: a real card must use a journaling NVM write.
  Fault injection is a Python-level simulation of a power loss, not a voltage-glitch test.
- The conversion from hash counts to time assumes ~1 µs per hardware SHA-256 — an assumption, not a
  measurement.
- No card, no secure element and no HSM was touched. All RAM and stack figures are literature.
- The 2,148-B peak is measured on a 2^15-signature prefix window for h = 18 and h = 20, not over the
  full 2^20.

---

## 6. S6 — migration and crypto-agility

**Files.** `src/s6_migration_agility.py` (design), `src/s6_hybrid_games.py` (audit).

### 6.1 The problem

What is deployed — X25519MLKEM768, Category 3 — sits 12 bits inside the QPT-128 gate budget, so
"deployed" is not "done". Agility differs per layer, and ROM verifiers cannot rotate at all.

### 6.2 Theory borrowed, and which part

| theory | as used here | which part | not used |
|---|---|---|---|
| Giacon–Heuer–Poettering 2018 Thm 3.1; X-Wing (2024) | "IND-CCA if EITHER component is IND-CCA and H is a random oracle / PRF" [T as cited, in the ROM] | the combiner theorem, applied in the random-oracle model | the proof; and the sentence in the theorem that the components must be *independent* is the one the audit attacks |
| draft-ietf-tls-ecdhe-mlkem-05 | the deployed group and the label/secret ordering style | the combiner's input order | the draft's wire encoding |
| RFC 6781 | DNSSEC algorithm rollover window | the double-signing period used as a field-rotation lever | — |
| QPT-128 gate accounting (the programme's own) | category reference attacks 83/100/116/148 gates; 2^18 gates per query | the margins | the four figures as costs of attacking ML-KEM: they are NIST category floors (Grover on AES), and §0.1 gives the estimator cross-check |

### 6.3 The construction

- **Hybrid combiner**: K = H(label ‖ ss_pq ‖ ss_cl ‖ ct_cl ‖ pk_cl) over 2-byte length-prefixed
  parts, SHA3-256 — X-Wing / draft-ietf-tls-ecdhe-mlkem style.
- **Byte cost of 768 → 1024**: ClientHello +384 B (1,568 − 1,184), ServerHello +480 B
  (1,568 − 1,088); both messages are already two datagrams, so no new packet boundary appears.
- **Per-layer agility**, with ROM layers Category 5 at manufacture.
- **Migration ledger**, per layer: what is deployed, whether it passes, the Category-5 target, the
  cost, and whether the layer can rotate.

| layer | deployed | passes? | Category-5 target | cost | rotatable |
|---|---|---|---|---|---|
| TLS key exchange | X25519MLKEM768 (Cat 3) | no | X25519 + ML-KEM-1024 | CH +384 B, SH +480 B; datagrams 2 → 2 | yes (named group) |
| TLS / Web PKI authentication | ECDSA/RSA X.509 (Cat 0) | no | MTC + KEMTLS ML-KEM-1024 | server flight 4,280 B model / **4,148 B exact** | yes (trust-anchor IDs) |
| DNSSEC | ECDSA P-256 / RSA (Cat 0) | no | SLH-DSA-256s-MTL, shards 2^12, NSEC + multiproof | "worst NXDOMAIN 1,129 B" model / **narrowed by the audit to 954 B for that shape and 1,839 B realistic** | yes (RFC 6781 rollover) |
| Firmware / boot | RSA/ECDSA, some LMS/XMSS | no | LMS n = 32, w = 8, h = 20 — not SHA-256/192 | 1,772 B; verify ≤ 8,692 hashes; 1.8 KB stack | **NO** (ROM fixed at manufacture) |
| Cards / SE / HSM | RSA-1984, ECDSA (Cat 0) | no | on-card LMS + BDS, or ML-DSA-87 at 8.1 KiB | state 2,148 B (not < 2 KB); 95,775 hashes max (not 86,720); 7 short APDUs | partial (GlobalPlatform applet) |
| Constrained broadcast | none, or 128-bit TESLA (OSNMA) | no | 256-bit TESLA + LMS anchor | 52 B/message steady state; one 1,772-B anchor per chain | yes (new anchor per epoch) |

The ledger strings in the design file now carry the v2.1 figures for the four rows v2.1 superseded
(TLS authentication, DNSSEC, cards, broadcast), each naming the v2.0 figure it replaces, so the
design file, the audit and this table agree. The design file also loads the S1/S2 model at revision
v2.2 rather than the v2.0 file kept beside it; `sharded_zone_answer`, the only function it uses, is
byte-identical between the two, so the DNSSEC row's model figure is unchanged by that.

### 6.4 The audit games

| game | setup | trials | wins | the measured fact |
|---|---|---|---|---|
| **A** classical component fully compromised | PQ secret truncated to n ∈ {8,10,12,14,16}; 64 combiner queries per trial; 2,048 trials per point | 10,240 | 5,250 | hit rates 0.234 / 0.0604 / 0.0147 / 0.0030 / 0 against Q/2^n = 0.25 / 0.0625 / 0.0156 / 0.0039 / 0.00098; fitted slope −0.999 |
| **B** PQ component compromised | mirror of A | 10,240 | 5,372 | fitted slope −0.931 |
| **C (negative)** correlated randomness | both components draw from one n_seed-bit seed; the adversary uses public data only | 6,144 | **6,144** | win rate 1.0 at 8/12/16 seed bits; adversary work 2^(n_seed+1) hashes where the independence bound would give 2^(n_seed−256) — **independence is necessary, not merely sufficient** |
| **D** TLS group downgrade | offer [Cat 5, Cat 3, classical] | 7,424 | 850 | bound transcript + delete Cat 5 → 0/256 accepted; **unbound → 256/256 downgrade**; bound + a quantum adversary that deletes both PQ groups and re-MACs after breaking X25519 → **256/256**; adding client_min_cat = 3 → 0/256; t-bit tag guessing: 259 (t = 3), 59 (t = 5), 20 (t = 7) of 2,048, slope −0.924 |
| **E** ROM root substitution / rollback | pinned typecode 0x08 (LMS M32 H20 W8); adversary keys under n = 24 (0x0D), toy n = 16 (0xF0), toy n = 1 (0xF1) | 3,365 keygen trials | 8 | strict verifier: `typecode mismatch`; full compare without a typecode check: `root mismatch`; **a lax prefix verifier accepts the toy n = 1 forgery 8/8** (mean 420.6 trials against an expected 256); rollback: monotone counter → `rollback`, no counter → `accepted` |
| **F** agility ledger and gate margins | accounting | 0 | 0 | margins n = 128 → −46, 192 → −14, 256 → +18 bits; every target is Category 5; no deployed entry passes |
| composition | — | — | — | the same-goal union of two −128 bounds is **−127.0**; DNSSEC + firmware is **refused** |

Three hypotheses were falsified: **A18** "the hybrid combiner protects against any component
failure" (correlated seeds win 6,144/6,144); **A19** "transcript binding alone defeats downgrade"
(the quantum re-MAC wins 256/256; the fix is a client policy that refuses Category 0); **A20** "a
verifier that reads n from the record is harmless" (the lax prefix compare accepts forgeries; the
typecode must be pinned in ROM).

Two dossier observations, not in the source, are worth carrying: the tested policy is
`client_min_cat = 3`, and under QPT-128 Category 3 also fails, so refusing Category 0 is not
sufficient; and the measured acceptance for A20 is the toy n = 1 case, while the n = 24/16 figures
are gate-cost estimates [L].

### 6.5 Tests

`src/s6_hybrid_games.py --self-test` (14 tests): S6-001/S6-002 games A and B scale as 2^−n; S6-003
game C (the negative result); S6-004 transcript binding detects deletion; S6-005 the unbound
downgrade succeeds and the quantum caveat; S6-006 typecode pinning rejects substitution; S6-007 the
lax prefix compare is the failure mode; S6-008 root-version rollback; S6-009 the ledger targets
Category 5 and no deployed entry passes; S6-010 the exact gate margins; S6-011 the same-game union
bound; S6-012 composition refuses independent layers; S6-013 the report is JSON with the required
game fields; S6-014 `TruncWOTS` at n = 32 reproduces `s4.WOTS` exactly and the lengths at n = 24/16/1
are 26/18/4.

### 6.6 What S6 does not show

- The combiner theorem is used in the random-oracle model, and the independence of the two KEM
  components is an implementation property that cannot be tested here — game C shows only that it
  is necessary.
- The KEMs are toys; IND-CCA of ML-KEM and X25519 is an input, not re-derived.
- ROM immutability is an assumption.
- The agility ledger is a static table; no migration was executed.
- The ledger rows quote the v2.1 measurements where v2.1 superseded a v2.0 figure, but S6 does not
  re-derive them: they come from the S2, S3, S4 and S5 audits.

---

## 7. What the domain as a whole does and does not establish

**Evidence classes.**

- Byte sizes: arithmetic models with round-number overheads in v2.0 [L]; `len()` of constructed
  bytes from real encoders in v2.1 (TLS/QUIC/DER/MTC in S3, DNS in S2) [M]. Several encoding choices
  are the audit's own and are labelled so.
- Hash and leaf counts: instrumented counters over Python code [M].
- CPU cycles, RAM and stack: literature only, several `None`.
- Security: generic-attack query counting and Grover gate accounting [L]; reduced-size experiments
  at n ≤ 16 bits [M]/[S]; toy KEMs in the random-oracle style [M on a toy]; cited theorems (T1,
  BDS, GHP18, MTL Thm 2, KEMTLS, RFC 4082) are not re-proved [T as cited].
- Implementations: Python models and prototypes over SHAKE256/SHA-256/SHA3; none is constant-time
  or audited.

**The four audit columns.** Every test is tagged spec (the implementation does what the
specification says), numbers (a resource claim reproduced), attack (an adversary tries to violate
the property) or bound (the formal bound supports the claim). The count over the ledger is attack
36, spec 20, numbers 7, bound 7. The tags come from a **keyword classifier over test names**, not
from human review, and the ledger never captures test docstrings — the columns are a reading aid,
not a reviewed classification. See `docs/audit-method.md`.

**The S1-011 flakiness, stated once more, because it is the one recorded result that does not
reproduce.** The v2.1 test asserted a four-point regression slope of 0.5 ± 0.06 on a *single*
random draw. The simulator's secret is random, so the marked-set size M varies, and the assertion is
a coin flip: 98/200 (49.0 %) in the programme's measurement, 108/200 (54.0 %) in the re-measurement
made for this repository. Both numbers are kept. The test now asserts the median over 41 draws
(20/20 in 20 independent trials) while keeping the two exact per-seed assertions (200/200 each).
The rewritten test passed in every run performed for this repository, but a median is not a
guarantee; the honest statement is that the flakiness is reduced and measured, not eliminated, and
that the Grover law here remains a **simulation**.
