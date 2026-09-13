# CE-QS — QPT-128 finalization (v1.43)

**Date:** 11 September 2026
**Committee:** N = 64 seats, F = 21 faults, Q = 43 quorum (2Q − N = 22 = F + 1)
**Evidence file:** `domains/06-qpt128-security-target/src/qpt128_finalization.py` (19 exact-arithmetic tests; `--report` reproduces every number below)
**Companion:** `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md` with `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`, which covers certificate formats and sizes

**Paths.** Paths are relative to the repository root and version suffixes have been dropped from file names. Where a pointer carries a line number, the number is the one recorded in the source tree; it is not re-verified against the repository copies. Where the source names a file that is not copied into this repository, the text says so.

---

## 0. Result

The QPT-128 question is now closed. It was not closed before for three reasons, and all three are fixed here.

1. **The project was aiming at two different targets.**
   - The operators ledger (`domains/04-operator-ledger/docs/operator-ledger.md:28-33`) defines QPT-128 as a *work factor*: an adversary with fewer than 2^128 quantum gates wins with probability below 1/3.
   - The v1.21 ledger (`domains/02-ceqs-construction-evolution/docs/size-path-resolution.md:53-56`), §2 of the research trail (`docs/01-research-journey/pqt.md:138-142`) and the closing theorem of the research trail (`docs/01-research-journey/pqt.md:2143-2145`) instead demand *Adv < 2^−128 against every QPT adversary*.
   - **Lemma L1 proves the second demand is unattainable** for anything with a 256-bit secret: 2^63 Grover iterations already exceed 2^−128.
   - The target is fixed here as the work-factor definition (D1), strengthened to a rigorous per-gate ratio (D2).

2. **The unit of cost was never pinned.** Counting one gate per oracle query, even a single AES-256 key falls with probability 1/3 after 3·2^125 < 2^128 queries (Lemma L2). QPT-128 is only meaningful when each query is charged its circuit cost. That is the reading of NIST category 5.

3. **Reduction running time was never charged.** Quantum online extraction runs in O(q²) time. A secret hidden inside a proof therefore needs roughly twice the generic security of a secret sent in the clear (Lemma L5). This single fact decides which instantiations pass.

**Verdicts.** Every row below is an exact rational comparison in the evidence file.

| Instantiation | Accounting | D2 (Pr ≤ G·2^−130) | Margin | D1 (QPT-128) |
|---|---|---|---:|---|
| **B0**: public signer set, 43 category-5 signatures in the clear | gates (2^18 per query) | **PASS** | **+23.0 bits** | **PASS** (Pr ≤ 2^−25 at 2^128 gates) |
| **B1 Mode S**: hidden signers, 512-bit credentials, 1024-bit registry keys | gates, **rigorous** (extraction overhead charged) | **PASS** | **+29.4 bits** | **PASS** (Pr ≤ 2^−41.3) |
| B1 Mode S | gates, attack-cost | PASS | +29.4 | PASS |
| B1 Mode S | queries, attack-cost | PASS | +3.3 | PASS |
| B1 Mode S | queries, rigorous | FAIL | −40.0 | FAIL |
| B1 Mode S with 512-bit registry keys | gates, rigorous | FAIL | −141.2 | FAIL |
| Compat mode: ML-DSA-87 / SLH-DSA-256s *inside* an extractable proof (R29, v1.37–v1.38) | gates, rigorous | FAIL | −185.0 | FAIL |
| B0 | queries | FAIL | −11.0 | FAIL |
| Legacy D3 ledger (closing theorem of the research trail) | any | **refuted by L1** | — | — |

**What this means.**
- **Final QPT-128 theorem, public signers:** B0 (Theorem A, §4). Its reduction is tight and linear, and it rests on one named assumption: EUF-CMA of the chosen category-5 signature.
- **Final QPT-128 theorem, hidden signers:** Mode S (Theorem B, §5). It holds rigorously in gate units with a 29.4-bit margin. It rests on named generic-strength assumptions for single-block SHAKE256, the QROM for the Fiat–Shamir hash, and an ideal collaborative prover.
- **The signature-inside-proof designs** do not meet QPT-128 once reduction time is charged. These are SLH-DSA in the closing "Theorem — QPT-128 CE-QS" (`docs/01-research-journey/pqt.md:2128-2158`) and ML-DSA-87 in R29 (`docs/01-research-journey/pqt.md:1808, 1866-1870`; v1.29). They are replaced, not patched.
- **Certificate size is a separate question.** B0 fits 32 KiB with category-5 signatures of at most 757 bytes, for example UOV-V at 260 bytes. A hidden-signer Mode-S certificate under 32 KiB is still not achievable with any known proof system. See the companion document.

---

## 1. What was read

All 1,094 files were covered.

This is a process claim about the reading pass, reproduced here as recorded. The group names are
the source tree's own directory and file names; the repository redistributes those files under the
domain directories.

| Group | Files | How read |
|---|---:|---|
| the research trail (2,189 lines), v1.29 README / assessment (identical) | 3 | directly, every line |
| Top-level audit scripts v1.34–v1.42 | 9 | directly, every line; all self-tests re-run: 20 + 16 + 27 + 23 + 36 + 13 + 12 + v1.41 + v1.42, all OK |
| `files/` v0.9–v1.24 proofs, ledgers, checkers | 31 | directly, every line; checkers v0.9, v1.0, v1.1, v1.3, v1.4, v1.6 re-run and byte-identical to stored results |
| `files/` Target-A PQ-AQC v0.5–v0.7, frontier memo, TLA+, finite-state checkers, SHA256SUMS | 16 | read in full; checkers re-run; 11/11 manifest hashes match |
| `files/` CE-QS v0.1–v0.8, alt-strategy note, early checkers | 29 | read in full; checkers re-run (5 byte-identical; v0.1 unseeded) |
| the operators ledger (19,608 lines) | 1 | read in full, in two halves; embedded checker re-run, output identical |
| Experiment v1.17, v1.25–v1.27b, regeneration check, v1.27 history | ~160 | read in full; binaries and proofs hashed; all manifests verified |
| Experiment v1.28, v1.28p, v1.29, v1.28 history, root manifests | ~110 | read in full; v1.29 51/51 checks replayed; 86 ML-DSA-87 approvals re-verified with an independent FIPS 204 verifier |
| Vendored Binius64 source | 767 | read in full, in five parts |
| External literature for constants | 30+ papers | read in full; formulas checked against the published figures (§2) |

Duplicates confirmed byte-identical (both members of each pair are the file named first; the
twin is excluded from the repository as a duplicate):
- the two `PQ_AQC_Frontier_ConflictExtraction_v0_1` files, the `.md` member of which is
  `domains/01-accountable-quorum-foundations/docs/frontier-conflict-extraction.md`;
- the v1.19 blocker-resolution document (in the repository at
  `domains/02-ceqs-construction-evolution/history/blocker-resolution-v1.19.md`) and its `.txt` twin;
- the root README and the v1.29 package assessment (in the repository at
  `domains/03-zk-carrier-experiments/docs/package-assessment.md`).

---

## 2. The target, fixed once

Adversaries are quantum circuits, and G(A) is their gate count. When an oracle stands for a concrete hash, each query costs g_H gates. g_H is at least the T-count of that hash's circuit: 499,200 for a SHA3-256/Keccak-f[1600] oracle (Amy et al., SAC 2016, Table 2). The checker uses g_H = 2^18.

- **(D1) Work factor (operators ledger):** G(A) < 2^128 ⟹ Pr[Win(A)] < 1/3.
- **(D2) Ratio:** Pr[Win(A)] ≤ G(A)·2^−130 for every A.
- **(D3) Legacy:** Pr[Win(A)] < 2^−128 for every QPT A.

**Lemma L1 (D3 is unattainable).** Let a uniformly random 256-bit secret determine a winning output. After j = 2^63 Grover iterations the success probability exceeds 2^−128.

*Proof.* Success is sin²((2j+1)θ) with sin θ = 2^−128. Since θ ≥ sin θ and sin y ≥ y − y³/6 on [0, 1], success ≥ (y − y³/6)² with y = (2^64 + 1)·2^−128. That exceeds 2^−128. (Exact rational check, test 01.) ∎

Consequently, "Adv < 2^−128 for every QPT adversary" is false for SLH-DSA-SHAKE-256s, ML-DSA-87, AES-256 and every 256-bit credential. This affects:
- the research trail (`docs/01-research-journey/pqt.md`) line 5, §1 (`:96-104`), §2 (`:138-142`), §17 (`:814`), the §18 theorem (`:920-948`) and §34 (`:1503-1520`);
- the closing theorem (`docs/01-research-journey/pqt.md:2143-2158`);
- the requirement "Adv_SLH ≤ 2^−134" (`docs/01-research-journey/pqt.md:2032`), read as a D3 statement.

**Lemma L2 (count gates, not queries).** 3·2^125 iterations (< 2^127) give success ≥ 1/3 against one 256-bit key; 3·2^122 suffice against 64 keys (test 03). So D1 in query units fails for every 256-bit-secret component. D1 is attainable only when each query is charged its circuit, which is exactly how NIST category 5 ("resources comparable to AES-256 key search") is defined.

**Lemma L3 (composition).**
- If Win ⊆ ∪ Bad_i and Pr[Bad_i] ≤ ρ_i(G), then Pr[Win] ≤ Σ ρ_i(G).
- If Σ_i max_{1≤G≤2^128} ρ_i(G)/G ≤ 2^−130, then D2 holds.
- D2 implies D1, because G < 2^128 gives Pr < 1/4.
- Probabilities add; exponents do not. The project's rule 8·2^−131 = 2^−128 remains valid as arithmetic on the per-gate coefficients.

**Lemma L4 (endpoint evaluation).**
- Let ρ(q) be a polynomial in q with non-negative coefficients, with q = G/g. Then ρ(G/g)/G is convex in G, so its maximum on [1, 2^128] is at an endpoint.
- The checker evaluates uncapped envelopes at both endpoints and applies min(1, ·) only to the D1 probability.
- A capped envelope is *not* convex. Its ratio can peak where the cap starts to bind (test 19 exhibits such a case), so capping before maximising would be unsound.

**Lemma L5 (extraction overhead).**
- DFMS's online extractor for Fiat–Shamir commit-and-open proofs in the QROM runs in O(q²)·poly time (DFMS, CRYPTO 2022, Theorem 4.2).
- Any reduction that *uses* an extracted witness to break a standard-model primitive F therefore runs in time t_B ≈ G + a·q²·g_sim.
- If F's generic attack bound is c·(t/g_F)^e/2^n, then D2 requires roughly

  n ≥ (2e − 1)·128 + 130 + log₂c + e·log₂(a·g_sim) − 2e·log₂g_H − e·log₂g_F.

- Consequences in gate units:
  - a preimage/search row (e = 2) passes with n = 512;
  - a collision row (e = 3) needs n = 1024;
  - a 256-bit signature inside the proof fails.
- A signature sent in the clear needs no extraction; its reduction is linear.

---

## 3. Constants used, all checked against full texts

| Quantity | Published statement | Source |
|---|---|---|
| Preimage / search, random function | 8·p·(q+1)²/2^n | Hülsing–Rijneveld–Song, ePrint 2015/1256, Thm 1 (λ = p/2^n) |
| Collision, random function | (2e(q+1)√(10(q+1)/M) + √(2/M))²; leading term 40e²(q+1)³/M ≈ 295.6(q+1)³/M | Chung–Fehr–Huang–Liao, EUROCRYPT 2021, Thm 5.29 |
| Commit-and-open Fiat–Shamir online extraction | ε_ex ≤ (22ℓ + 60)q³2^−n + 20q²·p_triv; extractor time O(q²)·poly | Don–Fehr–Majenz–Schaffner, CRYPTO 2022, Thm 4.2 |
| Joint two-proof extraction | adds a 2(v₀+v₁)·2^−n readout term over one measured database | project v1.35 (`domains/05-extraction-and-signature-reductions/src/joint_extractor_lift.py:95-138`) |
| Honest-proof simulation | (3q_s/2)·√((q_H + q_s + 1)·γ(Commit)) + q_s·Δ_HVZK | Grilo–Hövelmanns–Hülsing–Majenz, ASIACRYPT 2021, Thm 3 |
| SHA3-256 oracle | T-count 499,200; Grover preimage total cost 2^166.5 | Amy et al., SAC 2016, Tables 2–3 |
| AES-256 oracle | T-count 75,580; Grover G-cost 1.17·2^148 without a depth limit | Jaques–Naehrig–Roetteler–Virdia (revised), Tables 9 and 11 |
| **"12(q+154)³/2^n"** | **not found** in any source | stated without a reference in the research trail (`docs/01-research-journey/pqt.md:1667-1675`); the exact CFHL bound at q = 2^128, n = 512 is ≈ 2^−119.8, not 2^−124.415 |

---

## 4. Theorem A — public signer set (profile B0)

**Construction** (fixed in `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`).
- **Registry:** 64 distinct public keys pk_i of a signature scheme Σ, with cfg = H("CQ44/cfg/B0", scheme_id, pk_0..pk_63).
- **Approval:** seat i signs M_i = "CQ44/B0/VOTE" ‖ cfg ‖ d ‖ m ‖ u8(i) using the pure API with an empty context.
- **Certificate:** the 208-byte header ‖ an 8-byte bitmap with exactly 43 set bits ‖ 43 signatures in seat order.
- **ExtractConflict:** verify both certificates; require the same (cfg, d) and m₀ ≠ m₁; output S = bitmap₀ ∧ bitmap₁.

**Theorem A.** Let A be any adversary that corrupts a set C of seats and outputs two accepted conflicting certificates. Let Adv_Σ(t) be the EUF-CMA advantage of Σ at time t.

1. **Accountability, no probability.** |S| ≥ 43 + 43 − 64 = 22. For every s ∈ S, both certificates contain Σ-signatures under pk_s on M_s(m₀) and M_s(m₁). The evidence is the two certificates themselves.
2. **Non-frameability.** Fix an honest seat i* that approves at most one m per (cfg, d). Then Pr[i* ∈ S] ≤ Adv_Σ(G + O(1)).
3. **Safety.** If |C| ≤ 21, then Pr[two conflicting accepted certificates exist] ≤ 64·Adv_Σ(G + O(1)).

*Proof.*
- (1) Two 43-element subsets of a 64-element set meet in at least 22 elements, and verification checks every signature.
- (2) i* approved at most one of m₀, m₁. The signature on the other message is a fresh-message forgery. The reduction embeds the EUF-CMA challenge key at i*, generates the other 63 keys itself, and forwards i*'s signing queries. It runs A once, so its time is linear.
- (3) With |C| ≤ 21, S contains at least 22 − 21 = 1 honest seat. Guessing it uniformly among 64 seats costs a factor 64. B0 needs no extractor, because the signatures are public, and no rewinding. The guessing step is the v1.37 selector argument (`domains/05-extraction-and-signature-reductions/src/signature_security_reduction.py:143-183`); v1.37 additionally runs an extractor, which B0 does not. ∎

**Corollary A (QPT-128).** Instantiate Adv_Σ with the category-5 envelope (AES-256 key search, 8(t/g + 1)²/2^256 with g = 2^17 T gates per Grover iteration). Then D2 holds with margin **+23.0 bits**, and D1 holds with Pr ≤ 2^−25 at G = 2^128 (checker scenario "B0 … gates"). In query units the same row fails by 11 bits, as L2 predicts.

**Named assumption A-sig.** Σ is EUF-CMA at category-5 generic strength. The candidates that also fit the size gate (≤ 757 bytes) are all in NIST's additional-signature process; none is FIPS-standardized. The OV-V and SNOVA sizes below were measured in v1.44 through liboqs 0.16.0.
- UOV-V, 260 bytes. Its QROM route is Kosuge–Xagawa, ePrint 2022/1359, Thm 1, which carries a (2q+1)² loss on the underlying inversion problem. That loss belongs to the scheme's own security proof, not to CE-QS composition.
- SQIsign-V, 292 bytes (classical-ROM proof).
- SNOVA_29_6_5, 454 bytes, and SNOVA_60_10_4, 576 bytes.

---

## 5. Theorem B — hidden signer set (profile B1, "Mode S")

**Construction** (fixed in `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`). Seat i holds a 64-byte credential x_i.
- **Registry key:** K[i] = SHAKE256("CEQS/K1" ‖ x_i, 128 bytes). The input is 71 bytes, a single absorb block, and the output is 1024 bits.
- **Configuration:** cfg = H("CQ44/cfg/B1", K_0..K_63). Duplicate keys are rejected.
- **Context:** D = H("CQ44/ctx", cfg, d).
- **Handle:** L‖R = SHAKE256("CEQS/P1" ‖ x_i ‖ D, 128 bytes), a 135-byte single-block input. Z = R ⊕ decode(m)·(i+1) in GF(2)[X]/(X^512 + X^8 + X^5 + X^2 + 1).
- **Certificate:** header ‖ 43 handles sorted strictly by L ‖ proof π.
- **Relation R_S** over statement X = (header fields, handles) and witness w = ((i_j, x_j))_{j=1..43}:
  1. the 43 seats are distinct values in 0..63;
  2. K1(x_j) = K[i_j];
  3. handle_j = handle(x_j, i_j, D, m).
- **Proof π:** a Fiat–Shamir signature of knowledge (the message m is in X) over an S-sound* commit-and-open protocol with r repetitions, for example the four-subset ZKBoo of v1.36 (ℓ = 4r, p_triv = (3/4)^r). Its challenge has at least 2r bits from a QRO.
- **Producer:** an ideal collaborative prover F_Prove. An honest seat contributes only to the one message it approves per (cfg, d).
- **ExtractConflict:** the v1.34 division-free decoder (code `domains/05-extraction-and-signature-reductions/src/ceqs29_extractor.py:271-335`; correctness Claims 2–3 at `:82-132`).

**Bad events.** Charged over the whole experiment. q_H ≤ G/g_H counts oracle queries; t_B = G + q_H²·2^12 is the running time of any reduction that uses extracted witnesses.

| Event | Meaning | Bound | Status |
|---|---|---|---|
| E1 | a joint extraction of both accepted proofs fails | DFMS Thm 4.2 + v1.35 readout | proven, QROM |
| E2 | simulated honest proofs are distinguishable | GHHM Thm 3, q_s = 2^64, γ ≤ 2^−512 | proven, QROM |
| E3 | an extracted witness contains a preimage of an honest key | 8·64·(t_B/g_F + 1)²/2^512 | named assumption A-F (one-wayness) |
| E4 | a corrupt seat holds two openings of its key | CFHL form at n = 1024, time t_B | named assumption A-F (collision resistance) |
| E5 | two registered credentials give equal links in one domain | 8·2016·(t_B/g_F + 1)²/2^512 | named assumption A-F (registration first) |
| E6–E8 | HVZK with uniform tapes; ideal F_Prove; authenticated registry, canonical encoding, durable approval state | 0 in the model | model premises |

**Theorem B.** For every adversary A with G gates:
- **Safety** (|C| ≤ 21): Pr ≤ E1 + E2 + E3.
- **Non-frameability** of an honest seat: Pr ≤ E1 + E2 + E3 + E4 + E5.
- **Forensic completeness** (any number of colluders; fewer than 22 identified double-authorizers, or a seat identified that is not in both witnesses): Pr ≤ E1 + E2 + E4 + E5.

*Proof.*
- **Setup.** Run A. Verify both proofs in one compressed-oracle simulation and measure the database once. Decode both witnesses (v1.35 lift, no rewinding). Outside E1 both witnesses satisfy R_S. Honest proofs are simulated without honest credentials (E2).
- **Counting.** Distinctness gives 43 distinct seats per witness, so at least 22 common seats.
- **Safety.** With |C| ≤ 21 some common seat i* is honest. It approved at most one of the two messages. So the witness for the other message contains x′ with K1(x′) = K[i*], a preimage of an honest key (E3).
- **Framing.** Suppose the decoder outputs seat i* at matched link L, and let (s₀, x₀) and (s₁, x₁) be the rows at the matched positions. Consider the cases:
  - **x₀ = x₁.** Then K[s₀] = K[s₁]. Registry distinctness forces s₀ = s₁, and the decoded identity is s₀ = i*. The honest key's preimage then appears in a witness for an unapproved message (E3).
  - **x₀ ≠ x₁ with equal L.** Either two registered credentials collide on L in this domain (E5), or a corrupt seat used a second opening of its key (E4).
- **Completeness.** A common seat s is missed only if its two rows use different openings (E4), or its link coincides with another seat's (E5). Otherwise equal links and Z₀ ⊕ Z₁ = (m₀ ⊕ m₁)(s + 1) recover s (v1.34, Claim 2). ∎

**Corollary B (QPT-128).** The minimum repetitions giving the extraction row a share ≤ 2^−133 are **r = 553** (gate units) and **r = 640** (query units).

At r = 640 (checker rows, log₂ of max Pr/G):

| Row | Gates, rigorous | Queries, attack-cost |
|---|---:|---:|
| E1 extraction | −169.302 | −133.302 |
| E2 simulation | −159.415 | −159.415 |
| E3 honest preimage | −203.0 | −375.0 |
| E4 key collision (1024-bit) | −500.793 | −758.793 |
| E5 link coincidence | −198.023 | −370.023 |
| **Total** | **−159.414 (D2 margin +29.414)** | **−133.302 (+3.302)** |

- With 512-bit registry keys, E4 becomes +11.2 and the rigorous ledger fails. This is why keys are 1024-bit: one absorb block and one squeeze, so no extra permutation.
- In query units with the rigorous reduction time, E3 and E5 fail at n = 512 (total −89.98). Rigorous query-unit accounting would need 1024-bit credentials.
- The target counts gates, so Corollary B is the operative statement.

**Named assumptions.** Theorem B rests on these and nothing else:

| Label | Assumption |
|---|---|
| A-QROM | The domain-separated Fiat–Shamir/commitment hash (SHAKE256 XOF, ≥ 2r = 1,280 challenge bits) is modelled as a quantum random oracle. This is a model. A fixed hash is never indistinguishable from a random oracle (`docs/01-research-journey/pqt.md:1843-1851`; operators ledger, Lemma 8). |
| A-F | The single-block functions K1 (512-bit input, 1024-bit output) and P1 meet generic preimage, collision and search bounds in the ideal-permutation reading, and are PRFs for the privacy game. |
| A-cost | Each oracle or credential-function evaluation costs at least 2^18 T gates. |
| A-γ | Honest commitments have min-entropy ≥ 512 bits; tapes are uniform. |
| A-MPC | F_Prove has a QPT secure-with-abort realization (v1.4 Thm 4.1). Liveness uses identifiable abort (v1.19, conditional 22-attempt theorem). |
| A-protocol | Authenticated registry; registration before domain contexts are used; uniform honest credentials; durable per-(cfg, d) approval state; canonical encoding. |

---

## 6. Why compat mode (signature inside the proof) is withdrawn

Consider the v1.29 R29 relation (ML-DSA-87) and the v1.38 SLH-DSA-SHAKE-256s suite. Their accountability reductions (v1.37 eq. (5), `domains/05-extraction-and-signature-reductions/src/signature_security_reduction.py:265`; v1.38 eq. (C), `domains/05-extraction-and-signature-reductions/src/slh_dsa_signature_reduction.py:211`) give

p ≤ κ_E + L_E(δ_B + 64·ε_sig).

The conversion itself is correct. But ε_sig must be evaluated at the reduction's running time. That time includes the O(q²) extractor (L5). With a category-5 signature, whose secret is at the 256-bit level, the signature row at 2^128 gates is +55 (gates) and +161 (queries) in log₂ of Pr/G. The ledger fails by 185 bits (gates).

Under attack-cost accounting, which ignores reduction time, compat mode would pass like B0. But that is not a proof. The size question rules out compat mode independently. The project's own estimate for 43 in-proof ML-DSA-65 verifications is 53–96M gates (`domains/02-ceqs-construction-evolution/docs/size-path-resolution.md:28`). A separate count from FIPS 205 parameters is about 4.6k–8.6k Keccak permutations for each SLH-DSA-SHAKE-256s verification; the project states no such figure.

---

## 7. Corrections to the project record

Found during the full read. Each is cited to its location.

1. **D3 target** (`docs/01-research-journey/pqt.md:5, 138-142, 920-948, 1503-1520, 2143-2145`; v1.21 Lane 2, `domains/02-ceqs-construction-evolution/docs/size-path-resolution.md:53-56`). Refuted by L1; replaced by D1/D2 with gate accounting. v1.19 §6 itself warns against this reading (`domains/02-ceqs-construction-evolution/history/blocker-resolution-v1.19.md:191`).
2. **"12(Q+154)³/2^h"** (`docs/01-research-journey/pqt.md:1667-1675`). No source exists. The published CFHL bound is about 4.6 bits weaker at q = 2^128, h = 512.
3. **v1.36 parameter range h = 512, r ≤ 256** (`domains/05-extraction-and-signature-reductions/src/circuit_witness_extractor.py:122-127, 372`). Too short for QPT-128 extraction: r ≥ 553 (gates) or 640 (queries), which needs 1,106–1,280 challenge bits.
4. **Operators v1.33 "320 rounds at 9/16"** (`domains/04-operator-ledger/docs/operator-ledger.md:150-177`). This is a D1 constant-success allocation (τ = 1/24) under an unproven per-round premise. It does not carry over to a D2 ledger. With DFMS's proven (3/4)^r sampler the numbers are those in item 3.
5. **Compat-mode theorem** (`docs/01-research-journey/pqt.md:1808, 1866-1870, 2128-2158`; v1.37; v1.38). The conversion is valid, but category-5 signatures fail once reduction time is charged (§6). Replaced by B0 or Mode S.
6. **Anonymity admissibility gap** in v0.5 R2 (`domains/02-ceqs-construction-evolution/docs/formal-proof-stack.md:649-652`), inherited by v0.6 (`domains/02-ceqs-construction-evolution/docs/exact-aggregator-lifting-proof.md:701-771`). An identity with even one other contribution in the same topic can be linked. The privacy game must exclude identities in S₀ △ S₁ that have other contributions in that topic.
7. **Distinctness.** The v0.5 lemma (`domains/02-ceqs-construction-evolution/docs/formal-proof-stack.md:465-541`) shows that distinct deterministic tags imply distinct seats, *given extraction and the binding assumptions A4–A6*. Mode S keeps the explicit distinctness check instead: it is cheap and removes the dependence on binding from threshold counting.
8. **v1.29 `extract_algebra`** (`domains/03-zk-carrier-experiments/src/authorization.py:155-170`) checks neither distinct recovered seats nor ≥ 22. The v1.34 decoder and the v1.44 B1 extractor check both.
9. **v1.26 analysis note** (`domains/03-zk-carrier-experiments/docs/analysis-note.md:5, 99`) promises embedded v1.25 text and model code that are absent.
10. **Binius64 backend used in v1.17–v1.28p.** The crate paths below point into the vendored third-party tree (upstream `https://github.com/binius-zk/binius64`), which is excluded from this repository; the finding is reproduced with its paths as recorded.
    - `SECURITY_BITS = 96` (`crates/verifier/src/verify.rs:35`);
    - GF(2^128) challenges (`crates/verifier/src/config.rs:12`);
    - FRI soundness charges only the query phase (`crates/iop/src/fri/common.rs:497-510`);
    - no QROM or extraction analysis anywhere;
    - the constraint system is not absorbed into the Fiat–Shamir transcript (`crates/verifier/src/verify.rs:224-235`);
    - composite M4 chip calls are unconstrained (`crates/m4-verifier/src/composite.rs:39-45`);
    - deferred recursion is unsound unless `check_deferred` runs (`crates/recursion/src/circuit.rs:276-335`).

    No carrier built on it can be QPT-128, at any size.
11. **Target-B frontier memo** (`domains/01-accountable-quorum-foundations/docs/frontier-conflict-extraction.md:38, 82`). It keys conflicts on a session id. If that id is the v0.5 session identifier, which hashes the block (`domains/01-accountable-quorum-foundations/history/research-proof-documentation-v0.5.md:586-610`), then equivocations never share a session. The memo does not cite that definition, so this link is an inference drawn here, not a claim the memo makes. Extraction must key on the domain, as CE-QS does.
12. **PQ-AQC v0.7** cites `PQAQCEpochBarrier_v0_7.tla/.cfg` (`domains/01-accountable-quorum-foundations/docs/research-proof-documentation.md:2077, 3050-3051`), which do not exist. Its "artifact consistency" results cannot be verified, and lines 2147–2148 contain corrupted LaTeX control characters.
13. **v0.3 VOLE-in-the-head size figure** "5,034-bit proof" (`domains/02-ceqs-construction-evolution/docs/finalized-construction.md:756`). Never reconciled with v0.5's 9.91 KB per linkable ring signature (`domains/02-ceqs-construction-evolution/docs/formal-proof-stack.md:79`). The two figures come from different papers and relations.
14. **Published sizes that replace estimates:**
    - LaBRADOR's 58 KB at 2^20 constraints is **not** zero-knowledge.
    - The 2026 lattice ZK toolkit reports about 110 KB with ZK.
    - FAEST-256s is 20,696 bytes for a *single* key.

    These settle the compact hidden-signer question in the companion document.

---

## 8. Reproduce

```
python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --self-test   # 19 tests, OK
python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --report      # all numbers in §0, §4, §5
python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --explain
```

The file uses only the standard library. Every verdict is an exact `Fraction` comparison; logarithms
are computed in 60-digit decimal arithmetic, rounded to 3 or 9 decimal places, and printed for
display only. Exactly one of the three options is required: a bare invocation prints its usage
message and exits with status 2, by design.

**Non-claims.**
- No new cryptanalysis is done; generic attack bounds are used as named assumptions.
- No proof backend, proof-size measurement or distributed prover is implemented here.
- The QROM remains a heuristic model for SHAKE256.
- Liveness under 21 faults is a separate conditional theorem (v1.19 §4,
  `domains/02-ceqs-construction-evolution/history/blocker-resolution-v1.19.md`).
