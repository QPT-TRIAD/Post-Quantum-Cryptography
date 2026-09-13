# Mode B — written reductions, QROM theorem and production prover (v1.49)

**Date:** 11 September 2026
**Evidence:** `modeB_prover_v1.49.c` (production-parameter prover/verifier/extractor), `modeB_rigorous_ledger_v1.47.py` (exact ledger, FAEST-form R3 row, 6 tests), `hidden_signer_modeB_v1.46.py` (design, 12 tests), `modeB_voleith_toy_v1.48.py`.
**Primary sources used verbatim for bounds:** FAEST v2 specification (NIST round 2), Lemma 9.34, Lemma 9.37, Lemma 9.38 (from [AHJ+23]), Lemma 9.39, Corollary 9.35; Hülsing–Rijneveld–Song 2016 (search); Grilo–Hövelmanns–Hülsing–Majenz 2021 (simulation); DFMS 2022 (extraction, for the binding row only).

---

## 0. What this document establishes

| Item | Status |
|---|---|
| Construction "Mode B-r" (production form of Mode B) | fixed, §1 |
| Assumptions | six, named, §2 |
| Theorem 1 — non-frameability, **tight** (no proof extraction) | proved, §3 |
| Theorem 2 — safety and forensic completeness | proved from soundness + binding, §4 |
| Theorem 3 — QROM soundness of the proof system with multi-round loss | stated with explicit constants, proof by transplant of FAEST v2 Lemma 9.39; deviations listed, §5 |
| Theorem 4 — privacy | proved from A-P + simulation, §6 |
| Rigorous D2 ledger at production parameters | **passes, 7.7-bit margin** at (2^20 leaves, τ = 11, w_g = 16), §7 |
| Production prover | **runs at full parameters: 30,684-byte certificate, verified, 22 seats extracted**, §8 |
| Independent cryptanalysis | §9 (pending the independent analysis report at the time of writing; see the addendum) |

Everything below is conditional on the named assumptions and on the QROM heuristic for domain-separated SHAKE256. No claim is made beyond what the ledger rows compute.

---

## 1. Construction Mode B-r

Public parameters: seats N = 64, quorum Q = 43, field 𝔽 = GF(2^256) with f(x) = x^256 + x^10 + x^5 + x^2 + 1; key map F: 𝔽₂^512 → 𝔽₂^1024 expanded from a 32-byte seed as a random quadratic map with ρ quadratic monomials per equation (ρ = 4,096 by default; dense ρ = 131,328 is supported), dense random linear part and constant; hash H = SHAKE256 with domain-separation labels; power map G(r) = r^7 (a permutation of 𝔽 since gcd(7, 2^256−1) = 1).

**Registration** (per epoch and conflict domain d): seat i samples (s_i, r_i) ← 𝔽², publishes Y[d][i] = F(s_i ‖ r_i) (128 B). cfg = H("cfg", seed_F, Y[·][·]).

**Handle** for message m in domain d (v1.50 form): (c_a, c_b, c_c) = H("c", cfg, d, m, ctr) ∈ 𝔽³ with ctr the smallest counter for which L_c(s) = c_a·s ⊕ c_b·s² ⊕ c_c·s⁴ is invertible (it is 𝔽₂-linear in s; ≈3 tries); Z_i = r_i^7 ⊕ L_c(s_i) (32 B). (v1.46–v1.49 used L_c(s) = c·s; §9 item 1 explains the change.)

**Certificate:** header (208 B: cfg, d, m, count, width, payload length) ‖ 43 handles sorted strictly ‖ π.

**Relation R_B** for statement X = (cfg, d, m, (Z_j)_{j≤43}) and witness w = ((i_j, r_j))_{j≤43}:
- i_j ∈ [0, 64) encoded one-hot (b_j ∈ 𝔽₂^64, Σ b_j = 1);
- s_j := L_c^{-1}(Z_j ⊕ r_j^7) (derived; L_c^{-1} is a public 𝔽₂-linear map, so s_j has degree 3 in the bits of r_j);
- F(s_j ‖ r_j) = Σ_i b_{j,i} Y[d][i] (1,024 constraints of degree 6).

Committed witness per seat: 256 + 64 = 320 bits; ℓ = 13,760; masks 1,536; ℓ̂ = 15,296.

**Proof system Π_B:** the FAEST v2 interactive proof with the AES circuit replaced by R_B and the QuickSilver check at degree 6: τ repetitions of GGM trees with 2^b leaves, leaf commitments (64 B), VOLE from vector commitments with corrections c_2..c_τ and witness correction d, VOLE consistency hash (challenge χ₁), QuickSilver combination (challenge χ₂) with 5 mask elements, last challenge Δ of τ·b bits with w_g grinding bits, per-tree all-but-one openings. Fiat–Shamir over the statement hash.

**Extraction** (public): for two accepted certificates with equal (cfg, d), m₀ ≠ m₁: for each of the 43×43 handle pairs solve the 𝔽₂-linear system (L_{c₀} ⊕ L_{c₁})(s) = Z₀ ⊕ Z₁ (≤ 4 solutions), r = (Z₀ ⊕ L_{c₀}(s))^{1/7}; output every seat i with F(s‖r) = Y[d][i], with (s, r) as evidence. Every identified seat is reported; the count ≥ 22 is a completeness flag, not an abort.

**Production parameters** (§7): b = 20, τ = 11, w_g = 16 (τ·b + w_g = 236 ≥ 230), expansion 512, domains per epoch ≤ 2^20.

---

## 2. Assumptions

| Label | Statement | Where it enters |
|---|---|---|
| **A-F1** (one-wayness with handle) | For (s, r) ← 𝔽², c ← 𝔽\{0}, given (Y = F(s‖r), Z = r^7 ⊕ c s, c), no quantum algorithm with q evaluations of F finds (s', r') with F(s'‖r') = Y with probability better than the HRS16 search bound 8(q+1)²/2^256 per target. Multi-target: p targets multiply by p. | Theorem 1 (framing) |
| **A-F2** (binding) | Finding x ≠ x' with F(x) = F(x') costs at least the linear-trick search: with q evaluations, probability ≤ 8(q+1)²/2^512 (expansion E = 512). | Theorem 2 (completeness) |
| **A-QROM** | The domain-separated SHAKE256 instances of Π_B and of c, cfg are quantum-accessible random oracles. | Theorems 3, 4 |
| **A-P** (privacy) | For (s, r) ← 𝔽², c ← 𝔽\{0}: (Y, c, r^7 ⊕ c s) ≈ (Y, c, U) for uniform U ∈ 𝔽, with quantum distinguishing advantage bounded by the A-F1 search bound (decision-to-search: any distinguisher yields a preimage finder via the pair-search structure; see §6). | Theorem 4 |
| **A-Prove** | The proof is produced by a party that learns the 43 openings and behaves honestly (ideal F_Prove / trusted aggregator). Whoever holds an opening can frame that seat; this assumption is therefore essential, not technical (v1.46 §5). | Theorems 1, 4 |
| **A-Reg** | Registry authenticity; registration precedes use of a domain; honest openings uniform; each honest seat approves at most one message per (cfg, d); canonical encoding. | all |

Cost model: v1.43 gate accounting (each oracle/F evaluation ≥ 2^18 gates; adversary budget G ≤ 2^128 gates; D2 target Pr ≤ G·2^−130).

---

## 3. Theorem 1 — non-frameability (tight)

**Game Frame(i*).** Seat i* is honest. The adversary A controls any other seats, sees all public data, obtains honest approvals for messages of its choice (one per domain for i*), and outputs two certificates C₀, C₁ accepted by the verifier with equal (cfg, d) and m₀ ≠ m₁. A wins if the public extraction names i* although i* approved at most one of m₀, m₁ in d.

**Theorem 1.** For every quantum A with G gates, Pr[Frame(i*)] ≤ 8·p·(q+1)²/2^256 with q = G/2^18 and p the number of honest registry keys in the epoch (p ≤ 64·T for T domains). The reduction runs A once and performs one public extraction; no proof witness is extracted.

*Proof.* B receives an A-F1 instance (Y*, Z*, c*) for a random target and embeds it as seat i*'s key and handle: it sets Y[d][i*] := Y* and, when A requests i*'s approval of some m in d, programs c(m) := c* (a random-oracle output, uniform) and answers with Z*; all other seats' openings B samples itself (A-Reg). This simulation is perfect. When A wins, the extraction names i*, which means some pair (Z₀_j, Z₁_k) decoded to (s', r') with F(s'‖r') = Y*. B outputs (s', r'). With p honest keys, B embeds the multi-target instance across them (each with its own programmed c). B's running time is G + O(1) evaluations. ∎

**Why it is tight.** In Mode S (v1.43) the credential lives only inside the proof, so the reduction must run a QROM extractor, whose O(q²) time forced 512-bit credentials (Lemma L5). Here the evidence is recovered by the *public* pair search from the certificate bytes, exactly as in B0 where the evidence is the public signature. That is the glue between B0's tight reduction and a hidden-signer design.

---

## 4. Theorem 2 — safety and forensic completeness

**Game Safety.** At most 21 corrupt seats. A outputs two accepted certificates with equal (cfg, d) and m₀ ≠ m₁. A wins if fewer than 22 distinct seats are extracted, or an extracted seat is honest and did not double-approve.

**Theorem 2.** Pr[A wins Safety] ≤ ε_snd(Π_B) + ε_bind + ε_fp + Pr[Frame], where ε_snd is the QROM soundness error of Π_B for a false statement (Theorem 3), ε_bind = 8(t_B/2^18 + 1)²/2^512 for the extraction-charged time t_B = G + q²·2^12 (A-F2 with the v1.43 L5 accounting), ε_fp = 2^64·42·43/2^256 (corrected in v1.52: a seat present in exactly one certificate is named when its would-be handle under the other message coincides with one of the 43 handles published there — this is driven by the handle width, not the key width; the rarer key-coincidence path 2^64·64·43²·4/2^1024 is also counted), and Pr[Frame] from Theorem 1.

*Proof.* Consider the accepted C₀, C₁.
1. *Soundness.* If either statement is false — fewer than 43 distinct registered seats behind the handles with correct openings — the verifier accepted a proof of a false statement: probability ≤ ε_snd per certificate (Theorem 3). Otherwise both statements are true.
2. *Common seats.* Two 43-subsets of 64 share ≥ 22 seats. For each common seat i with openings (s, r) in C₀ and (s', r') in C₁: if (s, r) = (s', r'), the pair search recovers i from Z₀_i, Z₁_i (deterministic identity). If (s, r) ≠ (s', r') then x = s‖r ≠ x' = s'‖r' with F(x) = F(x'), a collision. To output it, the reduction needs both openings: it runs the QROM online extractor of Π_B on both proofs (DFMS22, time O(q²)), which is why t_B is charged. Hence Pr[some common seat unrecovered] ≤ ε_bind.
3. *Honest seats.* A common honest seat that approved only one of the messages has a second handle in the other certificate with the same opening (by step 2); that is Frame, bounded by Theorem 1. A spurious hit on a non-common seat occurs when a wrong pair decodes to a registered opening — dominantly when an absent seat's would-be handle under the other message coincides with a published handle: ε_fp.
Union bound. ∎

**Corollary (accountability).** With ≤ 21 corrupt seats, the extracted set has ≥ 22 seats, each a genuine double-approver, except with the probability above.

---

## 5. Theorem 3 — QROM soundness of Π_B with the multi-round loss

**Setting.** Π_B is the FAEST v2 proof system with (i) the relation R_B in place of AES, (ii) a QuickSilver check of degree d_QS = 6 instead of 3, (iii) hash outputs of 512 bits for commitments and commitment hashes, (iv) per-tree openings instead of the batched BAVC opening, (v) ℓ̂ = 15,296 > 2^13. Its interactive form has the same seven challenges as FAEST-IP⁺ (FAEST v2 §9.7.1): iv, leaf-commitment universal hashes, per-tree commitment hashes, com, χ₁, χ₂, Δ‖grinding.

**Lemma 3.1 (round-by-round soundness).** For a false statement, Π_B's interactive form is RBR-sound with errors ε_{−3} = ε_{−1} = ε₀ = 0, ε_{−2} = τ·2^−λ, ε₁ ≤ ε_v·(τ choose 2), ε₂ ≤ ε_zk, ε₃ = d_QS·2^−λ′ where λ = 256 is the MAC field size, λ′ = τ·b + w_g the entropy of the last challenge, and ε_v, ε_zk are the universal-hash errors of the VOLE consistency and ZK hashes.
*Proof.* Identical to FAEST v2 Lemma 9.34 and Lemma 9.37 — the state function reconstructs u, V from the leaf commitments, checks the VOLE consistency (Claim 1 of Lemma 9.34, imported from BBD+23 Theorem 2), runs the QuickSilver arithmetisation of R_B on the committed witness (Claim 2), and for the last round applies the degree bound: a nonzero polynomial of degree d_QS in Δ has at most d_QS roots among the 2^{τb} committed values, and the w_g grinding bits multiply the hit probability by 2^−w_g (Lemma 6.3 form). The relation R_B affects only the circuit run inside the state function, not the errors. The ℓ̂ > 2^13 condition of Lemma 9.34 enters only the constant (1 + 2^{B−50}) of ε_v, which stays orders of magnitude below ε₃. ∎

**Theorem 3.** Let A be a QROM adversary making Q̃ quantum queries in total to the domain-separated oracles of Π_B, and let Q = Q̃ + 2τ + 12. For a false statement,

  Pr[verifier accepts] ≤ 10·(τ+1)·Q³·2^−512 + 10·Q²·max(τ·2^−256, d_QS·2^−λ′).

*Proof.* Transplant of FAEST v2 Lemma 9.39. Define the "bad transcript" predicate on the compressed-oracle database exactly as there (RBRState flips from 0 to 1 at some challenge derived by the oracle); it has (τ+4)-local witnesses. Lemma 9.38 ([AHJ+23] Lemma 1) bounds the probability that a Q-query algorithm outputs a witness by (Σ_{k≤Q} √(10·δ(k)))² where δ(k) is the maximum, over databases of size ≤ k and oracle inputs x, of the probability over a fresh output u that the predicate becomes true. The case analysis of Lemma 9.39 (items 1–6) carries over unchanged: for the collision-type events δ ≤ (τ+1)·k·2^−512 with our 512-bit outputs; for the RBR events δ ≤ ε_max := max(τ·2^−256, d_QS·2^−λ′) by Lemma 3.1. Cauchy–Schwarz gives 10·Q·Σ_k δ(k) ≤ 10(τ+1)Q³2^−512 + 10Q²ε_max. ∎

**Deviations from FAEST and their effect.** (iv) Per-tree openings only change sizes, not soundness (each tree is opened all-but-one exactly as in FAEST's single-tree analysis). (iii) Larger outputs only lower the collision terms. (ii) Enters through d_QS. Nothing else in Lemma 9.39 depends on the circuit.

**Numerical consequence** (`modeB_rigorous_ledger_v1.47.py`, `r3_faest_qrom`): with Q = G/2^18 + 2τ + 12 and the D2 target, the row requires τ·b + w_g ≥ 230. Minimum τ: 14 at b = 16, **11 at b = 20**, 9 at b = 24 (all with w_g = 16), 7 at b = 32 with w_g = 32.

---

## 6. Theorem 4 — privacy

**Game Priv.** A chooses two 43-subsets S₀, S₁ of honest seats with |S₀| = |S₁|, a domain d and a message m; receives a certificate for m produced by F_Prove for S_β; must output β. A may see arbitrarily many other certificates in other domains and public registry data. (Admissibility: no seat of S₀ △ S₁ has another approval in d, closing the v0.5 gap noted in v1.43 §7.6.)

**Theorem 4.** |Pr[β' = β] − 1/2| ≤ ε_sim + 43·ε_P, where ε_sim = (3q_s/2)·√((q_H + q_s + 1)·2^−512) (GHHM21 Theorem 3: replacing the honest proof by the HVZK simulator with programmed challenges, commitment min-entropy 512 bits) and ε_P is the A-P advantage.

*Proof.* Hybrid 0: real certificate for S₀. Hybrid 1: proof replaced by the simulator (Π_B is HVZK: the VOLE masks u are uniform, the QuickSilver coefficients are masked by independent uniform values, and FAEST's simulator argument applies to any relation); distance ε_sim. In Hybrid 1 the certificate consists of the 43 handles only. Hybrids 2..44: replace, one seat at a time, the handle of a seat in S₀ \ S₁ by a uniform element, then move to S₁ \ S₀ handles: each step is distinguishable only with advantage ε_P (A-P), since the seat's opening is used in no other handle of domain d (A-Reg: one approval per domain; fresh openings per domain). After all replacements the distribution is independent of β. ∎

**On A-P.** A-P is a decisional assumption. It is implied by A-F1 in the following sense: a distinguisher D with advantage ε against (Y, c, Z) vs (Y, c, U) yields, by the pair-search structure, a test for whether a candidate opening is consistent; the v1.49 cryptanalysis pass tests the decisional/search gap empirically (§9). We do not claim a tight decision-to-search reduction.

---

## 7. Ledger (gate units, exact rationals, uncapped endpoints)

| Row | log₂ Pr/G at 2^128 gates | Source |
|---|---:|---|
| R1 framing (Theorem 1, tight, 64×2^10 targets) | −145.0 | A-F1, HRS16 |
| R2 evasion/binding (Theorem 2, extraction charged, E = 512) | −209.0 | A-F2 |
| R3 proof soundness (Theorem 3, τ = 11, b = 20, w_g = 16) | −138.1 | FAEST v2 Lemma 9.39 form |
| R4 simulation (GHHM21 Thm 3, 2^64 certificates) | −159.4 | proven |
| R5 pair-search false positive (handle coincidence; corrected in v1.52) | −181.2 | information-theoretic, measured law |
| **Total** | **−137.7 → D2 margin 7.7 bits** | **PASS** |

Alternative settings: (16, 14, 16): margin 11.5; (24, 9, 16): 3.7; (32, 7, 32): 15.0 (the last is not computable, §8).

---

## 8. Production prover (`modeB_prover_v1.49.c`)

Full parameters: GF(2^256) with carry-less multiplication (PCLMUL), SHAKE256 for every hash/PRG (verified against Python on test vectors), seeded key map at ρ = 4,096 monomials per equation (dense supported), OpenMP over repetitions (trees) and seats (QuickSilver).

Bugs found and fixed while bringing it up — the kind only an implementation exposes:
1. the 7th-root exponent 7⁻¹ mod (2^256−1) has period-3 hex digits, so its four 64-bit limbs differ; a copy-paste of one limb four times computed wrong roots (extraction found nothing);
2. Δ must be masked to the τ·b committed bits: the trees commit only those, and the uncommitted high bits broke the VOLE consistency identity.

| Run | Trees | τ | w_g | ρ | Proof bytes | Frame bytes | Fits | Verified | Extracted | Prove (s) | Verify (s) |
|---|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|
| reduced | 2^12 | 20 | 8 | 1,024 | 47,524 | 49,108 | no | yes, yes; tampering rejected | 22 | 3.0 | 1.3 |
| **production** | **2^20** | **11** | **16** | 4,096 (4,025 effective) | **29,100** | **30,684** | **yes** | yes, yes; tampering rejected | 22 | 97.4 (trees 88.4, QuickSilver 8.9, grinding 0.2) | 85.7 |
| dense key map (each monomial present w.p. ½: 65,416 per equation) | 2^12 | 20 | 8 | 65,416 | 47,524 | 49,108 | no | yes, yes; tampering rejected | 22 | 226 (QuickSilver 222.6, 6 threads) | 18.0 |
| **production, v1.50 linearized handle** (current design) | **2^20** | **11** | **16** | 4,096 | **29,100** | **30,684** | **yes** | yes, yes; tampering rejected | 22 (linear-solve extraction 1.9 s) | 60.3 (trees 53.2, QuickSilver 6.8) | 56.5 |
| production, v1.50, deeper trees | **2^22** | **10** | **16** | 4,096 | **27,124** | **28,708** | **yes** | yes, yes; tampering rejected | 22 (extraction 1.9 s) | 218.9 (trees 212.7, QuickSilver 6.2) | 194.6 |

Timings are on 12 cores; the v1.49 production run shared them with a concurrent job (4–5 cores on average), the v1.50 run had about 7. The linearized handle changes neither the proof size nor the prover cost: the certificate is byte-identical in size (30,684 B), and extraction with the 𝔽₂-linear solve takes 1.9 s. The proof-size formula used in v1.46–v1.47 is reproduced exactly by the implementation's byte layout: h_com 64 + (τ−1)·1,912 corrections + 1,912 witness correction + 64 VOLE hash + 192 QuickSilver + 4 grinding counter + τ·(32b + 64) openings = 29,100 B at the production setting. The measured frame is 2,084 B under the bound.

**The size/work trade-off, measured.** Both rows satisfy τ·b + w_g = 236 ≥ 230. Going from 2^20 to 2^22 leaves removes one repetition: the certificate drops 1,976 B (30,684 → 28,708) while the prover cost rises 3.6× (60 → 219 s), since tree expansion scales as τ·2^b. Verification tracks the prover (56 → 195 s); extraction is unchanged at 1.9 s.

**What dominates the prover.** Tree expansion: τ·2^b = 1.15×10^7 leaves, each expanded to ℓ̂ = 15,296 bits by SHAKE256 (≈17 Keccak permutations per leaf, 2×10^8 permutations). With a vectorised Keccak (4-way AVX2 ≈ 0.1 µs per permutation) this is ≈ 2 s per core-second budget of 20 s; the QuickSilver part (1.8×10^8 degree-6 monomial products at ρ = 4,096) is 9 s here and scales linearly with ρ: the dense run (65,416 monomials per equation, 16× more) took 223 s on 6 threads. Density is a security–performance knob: the algebraic estimates of v1.46 §3 are for dense maps; ρ = 4,096 (3% density) is the setting the cryptanalysis pass should judge (§9).

---

## 9. Independent cryptanalysis pass (results)

An independent adversarial pass (read-only, 30+ experiments) attacked the v1.46/v1.47 design. Findings, with what was done about each:

| # | Finding | Evidence | Cost | Action |
|---|---|---|---|---|
| **1** | **Challenge-collision denial of extraction.** With m₀ ≠ m₁ but c(m₀) = c(m₁), the extractor divides by c₀⊕c₁ = 0 and names nobody; a double-signing quorum chooses both messages, so an offline birthday search on the 256-bit c suffices. | Toy n = 14: collision by birthday over 2^7 messages; both frames accepted; extraction fails; the 22 double-signers' handles are byte-identical. | 2^128 classical (vOW); ≈2^85 quantum with QRAM (BHT), 2^102 without. Under the v1.43 CFHL collision row: −101 at 2^101 gates, 29 bits short of the D2 target. | **Fixed in v1.50:** Z = r⁷ ⊕ c_a·s ⊕ c_b·s² ⊕ c_c·s⁴ with a 768-bit-derived challenge and a public counter making L_c invertible; extraction is an F₂-linear solve with ≤ 4 candidates; suppression now needs a 768-bit collision. Circuit unchanged in degree (s = L_c⁻¹(t) is linear in t). |
| **2** | **The "< 22" abort turns one evader into a full denial.** A seat with two openings of its key (one F-collision) uses different openings in the two certificates; its pair decodes to garbage; at overlap 22 the extractor raised and the other 21 honest double-signers went unnamed. | Toy n = 14, E = 8: reproduced exactly. | one F-collision (2^E / 2^(E/2)) | **Fixed in v1.50:** extraction reports every identified seat; the count is a flag, never an abort. |
| 3 | Framing, generic bound: not beaten. The Grover predicate is target-specific, so multi-target does not help; the claimed 122.3 is conservative — the real generic cost is **2^128 quantum / 2^256 classical**. | derivation + batching analysis | 2^128 | none needed (ledger row R1 stays conservative) |
| 4 | Algebraic framing routes: Frobenius trick r⁸ = r·t makes the handle equations bilinear (estimator 251 → 245 quantum, still ≫ 128, and it would allow degree-2 constraints in the proof); auxiliary w = r³: 364–369; eliminate s → 1,024 degree-6 equations in 256 unknowns: hybrid 133.6 (guess 248 bits + linearize) ≈ generic within model error; Weil descent, chosen c, joint use of many Y: nothing. | `dreg_est.py` | ≥ 2^128 | none |
| 5 | **SAT slopes correct an earlier claim.** No handle: 2.42 bits/n (n = 7–11); linear handle: 1.29 (E = 0) / 1.58 (E = n) bits/n over n = 12–20; r⁷ handle: 0.90–0.93 bits/n (n = 12–16 only). Any handle collapses the SAT search from 2n to n bits (guess r, s follows), and SAT gives no r⁷-over-linear advantage. The v1.46 sentence "r⁷ instances behave like bare key maps" was wrong at toy scale; the r⁷ ranking rests on the XL model, and the security bound is the generic 2^128 regardless. | `sat_scale.py`, n = 7–20 | — | v1.46 §3.1 corrected |
| 6 | Evasion: nothing beats the linear trick. Bilinear (x, δ) system: hybrid minimised at the trick itself; FSS D_reg bounds ≥ 359 bits after guessing 480 δ-bits; SAT on the bilinear system scales ≈ 2^(2.6E) vs 2^E for the trick; subspace-restricted δ leaves 2^(k−E) expected solutions; a self-chosen registration x gains nothing. | `collision_sat.py` | 2^E / 2^(E/2) | none |
| 7 | Privacy: refutation of a wrong (Y, Z) pairing is 1.3–6.7× *slower* than solving the right one (no decisional shortcut); Z is exactly uniform at n = 8; 76,755 linear approximations have rms bias 2^−9.00 = the random-function expectation; cross-domain handles independent. | `privacy_sat.py`, `chi2.py` | — | none |
| 8 | Extraction soundness with ≤ 21 corrupt seats: naming an honest seat needs a 2^256 grind or a preimage; "opened twice" is unreachable with distinct keys; only items 1–2 survive. | `task4_toy.py` | — | none |
| 9 | Sparsity ρ = 4,096 (3%): no exponent changes — the linear-trick matrices have rank 511 exactly as dense for all δ weights tried; each variable meets ≈16 monomials per equation, far from the very-sparse regime; XL D_reg is density-independent. Only effect: an F evaluation costs ≈2^22 gates instead of 2^28, closer to the ledger's 2^18. | `ccoll_ledger.py` | — | none |
| 10 | Code review (v1.46 Python): `evaluate`, `diff_rows`, `collision_for_delta` exact vs brute force; numpy = pure Python at n = 256. Bugs: message canonicality (raw message hashed, header field is `64s`) — **fixed in v1.50 (64-byte digests only)**; the `inverse of zero` path (item 1); field polynomial and power not pinned by the suite id. | `code_review.py` | — | v1.50 |

Missing from the report at delivery time: e7 SAT rows at n = 17–20 and collision-SAT rows at N ≥ 14 (the independent analysis jobs had not finished); the reviewer states that neither gap affects any numbered finding. Our own sparse-vs-dense SAT comparison is in §9.1.

**v1.50 verification of the fixes.** `hidden_signer_modeB_v1.50.py` (5 tests): L_c is 𝔽₂-linear and invertible (counter < 32 in all trials), extraction recovers every overlap 22–43 through the linear solve, a frame with one common seat's handle replaced by an unregistered one yields the other 21 seats with `complete = False` instead of an abort, and non-64-byte messages are refused. `modeB_prover_v1.50.c`: the reduced-size run verifies, rejects tampering and extracts all 22 seats (extraction 3.3 s with the linear solves).

**Net effect on the claims.** Framing: 2^128 quantum queries (the ledger's 122.3 is conservative). Evasion: 2^(E/2) via key collision stands; the challenge-collision route (2^85–2^128) and the count abort are closed by v1.50. Privacy: no distinguisher below search. Two design changes, zero bytes added to the certificate.

### 9.0 Lemma (v1.51): partial challenge collisions cannot suppress extraction

Let the two certificates' challenge triples differ by (α, β, γ) and set D(s) = αs ⊕ βs² ⊕ γs⁴, the map the extractor inverts. D is a linearized (2-)polynomial of 2-degree ≤ 2 over GF(2^256), so it has at most 4 roots and its kernel is an 𝔽₂-subspace of dimension ≤ 2.

**Consequence.** For every (α, β, γ) ≠ 0 the extractor's linear solve returns at most 4 candidate openings, which the registry lookup filters; extraction fails **only** when D ≡ 0, i.e. the two triples are equal. This justifies the `max_free = 2` cap in the extractor and shows the attack needs a full 768-bit collision, not a partial one. Measured: over 3,000 random nonzero triples at n = 16 and at n = 17 the kernel dimension never exceeded 2; a collision in c_a alone leaves dimension 1, in c_a and c_b leaves dimension 0.

**Corrected cost of the suppression game** (an earlier draft said "2^768", which wrongly treated a collision as three preimage searches). Using this project's CFHL collision bound at advantage 1/3:

| | v1.46: 256-bit challenge | v1.50: 768-bit triple |
|---|---:|---:|
| classical birthday | 2^128 | 2^384 |
| quantum queries | 2^81.7 | 2^252.4 |
| gate units (2^18/query) | 2^99.7 — **inside the 2^128 budget** | 2^270.4 — safe by 142 bits |

### 9.1 Sparse vs dense key map (own experiment — inconclusive by design)

A toy SAT comparison (dense vs 3 % random quadratic maps, N = 24–40 unknowns, expansion 16) was attempted and hit the 25-minute cap without finishing its dense N = 24 instances (consistent with the reviewer's observation that a bare dense key map at N = 24 already takes > 17 minutes for CryptoMiniSat). More importantly the comparison cannot be made meaningful at toy scale: what matters for the known attacks is the number of monomials each variable meets per equation (≈16 at the production ρ = 4,096, N = 512), and at N ≤ 40 a "3 %" map has fewer than one monomial per variable per equation — a different, genuinely sparse regime. The evidence for ρ = 4,096 therefore rests on the reviewer's structural checks (§9 item 9): the linear-trick matrices A_δ have rank 511 for every δ weight tried, exactly as for dense maps; the per-variable monomial count is far above the very-sparse regime where guess-and-propagate methods apply; and XL's degree of regularity does not depend on density. A dedicated analysis of moderately sparse random MQ remains listed under open cryptanalysis.

---

## 10. Reproduce

```
gcc -O3 -march=native -fopenmp -o modeB_prover modeB_prover_v1.49.c
./modeB_prover --vectors                                   # SHAKE / GF(2^256) test vectors (match Python)
./modeB_prover --run --b 20 --tau 11 --wg 16 --rho 4096    # production run, ~3 min on 12 cores
./modeB_prover --run --b 12 --tau 20 --wg 8 --rho 1024     # 12-second smoke run
python3 modeB_rigorous_ledger_v1.47.py --report            # ledger incl. the FAEST-form R3 row
```

| File | sha256 |
|---|---|
| `modeB_prover_v1.50.c` (linearized handle; **current**) | `ff8e5cd9f5c84cde3d0ac6e654b7bfc5a26e21b7331b8098649b36f0fe6adb92` |
| `hidden_signer_modeB_v1.50.py` (5 tests; design reference with the fixes) | `e094a605f4e5ffa8b70f71f178c415ad64b23b315c0a44c26f477ec1dcc82bf1` |
| `modeB_prover_v1.49.c` (superseded by v1.50) | `8e7c0befe009774a994a238afb843f64a8879cc0409cef133f8ed05675b72baf` |
| `modeB_rigorous_ledger_v1.47.py` (7 tests; R5 corrected in v1.52) | `074f06454a4aaf11d4a801683194485211cc0bc4c31bf2433195ab3de96541ac` |
| `hidden_signer_modeB_v1.46.py` (12 tests) | `04df0b357f4671ab7d168e5c6daedf647f0f88bfc77f1ecb853491e8d96bd633` |
| `modeB_voleith_toy_v1.48.py` (7 tests) | `9fef036b837ab41fc9b110c08b51ffed9d5474287a63d555386f8d3f54b19e20` |

## 11. Non-claims

- Theorems 1, 2, 4 are conditional on A-F1, A-F2, A-P, A-Prove, A-Reg; Theorem 3 on A-QROM. None of A-F1/A-F2/A-P is a standard assumption; §9 and v1.46 §3 give the attack-based evidence.
- The multi-round QROM bound is transplanted from FAEST v2 Lemma 9.39 with the stated deviations; it has not been re-derived line by line for Π_B.
- A-Prove is essential: the aggregator can frame. No collaborative prover exists (v1.46 §5).
- Sizes and timings are for the research implementation; no side-channel or constant-time claims.
