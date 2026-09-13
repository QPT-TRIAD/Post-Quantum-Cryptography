# CE-QS Validation and Continuation
## v0.8 Public-Signer Theoretical Completion — Independent Validation

**Status:** validation record + limited continuation. Not a security proof, not a priority claim, not production cryptography.
**Date:** 2026-09-08
**Scope:** `PQ_CE_QS_public_signer_theoretical_completion_v0.8.md`, `ce_qs_bitmap_policy_checker_v0.8.py`, and `ce_qs_bitmap_policy_checker_v0.8_results.txt`, checked against the shipped `PQ_CE_QS_v0.8_SHA256SUMS.txt` and against the real cited literature (web-fetched: Brodsky–Choudhuri–Jain–Paneth *Monotone-Policy Aggregate Signatures* eprint 2024/899, fetched in full through Section 6.1; Kniep–Sliwinski–Wattenhofer *Byzantine Fault-Tolerant Post-Quantum Distributed Quorum Signatures*, arXiv 2607.17700).
**Follows:** `PQ_CE_QS_v0_7_validation_and_continuation.md` (quorum-family/privacy-fork validation + Lemur 185.5 KB correction, previous session).
**Explicitly does not touch:** `PQAQCEpochBarrier_v0_8.tla`, its `.cfg`, the finite-state checker, or the v0.8 (Target A) SHA-256 manifest. That is a *different* v0.8 — the deployed Target A epoch-barrier release — and remains untouched. This document validates the *Target B₀* "public-signer theoretical completion" artifact set, which is versioned v0.8 independently within the Target B track.

---

## 1. Artifact integrity

```
FILE                                                       MANIFEST (v0.8 SHA256SUMS)                                         COMPUTED                                                          MATCH
PQ_CE_QS_public_signer_theoretical_completion_v0.8.md      31bd52f1e8237c08c086cc2bcf2cec8d2ef826fea1dd9cf48dd09aa7bf3696cf  31bd52f1e8237c08c086cc2bcf2cec8d2ef826fea1dd9cf48dd09aa7bf3696cf  YES
ce_qs_bitmap_policy_checker_v0.8.py                        f32b9952ede037320a26a157c0e5468a4f3a68880de3dde9fa2f79c93aa80c56  f32b9952ede037320a26a157c0e5468a4f3a68880de3dde9fa2f79c93aa80c56  YES
ce_qs_bitmap_policy_checker_v0.8_results.txt               5ec3d1ffe1b834723c14921dfa17ef7ae2e58c815c37f697327829492af2b9f7  5ec3d1ffe1b834723c14921dfa17ef7ae2e58c815c37f697327829492af2b9f7  YES
```

**Result: PASS.** All three files are exactly what the manifest claims.

**Executable check:** the checker script was re-run from a clean container. Its output was byte-for-byte identical to the shipped `results.txt`.

---

## 2. What v0.8 is actually claiming

v0.8 closes the concrete gap v0.7 left open for the public-signer branch (B₀): v0.7 proved that *if* signer identities may be public, an 8-byte bitmap plus an exact signer-set-bound aggregate is sufficient for conflict accountability — but it did not exhibit a concrete cryptographic primitive with the right binding shape. v0.8 supplies one: it instantiates the abstract "exact signer-set-bound aggregate" with the real, published Monotone-Policy Aggregate Signature (MPAgg) primitive of Brodsky, Choudhuri, Jain, and Paneth (EUROCRYPT 2024), using a specific bitmap-conjunction policy `f_B` that the document proves is exactly the "every bit named by B must be present" predicate.

This is a different kind of proof from v0.7 again: rather than a combinatorial/architectural theorem, it is a concrete reduction from CE-QS's B₀ soundness/extraction/non-frameability properties to the published primitive's own unforgeability game, plus an honest scoping discussion of what standard-assumption/post-quantum guarantees the underlying primitive actually offers today.

### 2.1 Spot-check of the proof logic

Read in full, not sampled.

- **Lemma 5.1 (bitmap-policy equivalence) is correctly proved.** `f_B(z)=1 ⟺ Σ B_i z_i ≥ Σ B_i`. Since each term `B_i z_i ≤ B_i`, the sum can only reach `Σ B_i` if `B_i z_i = B_i` for every `i`, which forces `z_i=1` wherever `B_i=1` — i.e., `supp(B) ⊆ supp(z)`. The converse direction is immediate. This is a clean, gap-free argument, and it correctly identifies `f_B` as a weighted-threshold policy (`α_i = B_i`, `t = w(B)`) of the exact family the published fast-aggregation theorem covers — so nothing hand-wavy is smuggled in between "the paper supports weighted thresholds" and "our specific `f_B` is a weighted threshold."
- **Theorem 6.1 (exact public signer-set soundness) reduces correctly to the paper's actual unforgeability game.** The reduction is a direct forgery construction: an honest, uncompromised `i*` in `supp(B)` who did not sign, wasn't corrupted, and wasn't queried has `b_{i*}=0` in the real MPAgg game exactly as defined; Lemma 5.1 forces `f_B(b)=0`; an accepting `AggVerify` is then precisely a winning forgery. This is checked against the real Definition 4.1 in §4 below and matches essentially verbatim.
- **§7–§10 (exact quorum soundness, public conflict extraction, VerifyBlame/non-frameability, BFT conflict-impossibility) are the same `2q−n=f+1` intersection argument used in every prior CE-QS version (v0.1 through v0.7), now instantiated concretely rather than abstractly.** The recomputation in §3 below confirms `2q−n=f+1=22` at `n=64,f=21` exactly, consistent with every earlier pass.
- **§13's standard-assumption qualification is appropriately hedged, and this hedge is correct on inspection of the source** (§4 below): the cited paper's core security definitions (Definition 3.1 for signatures, Definition 4.1 for the aggregation scheme) are written for PPT adversaries with no quantum framing, so v0.8's refusal to relabel the construction "QPT-secure" without further work is the right call, not excess caution.
- **§14 (Quantum-Lift Criterion) is stated and proved as a conditional, structural observation** — "if items 1–6 hold, then the same black-box reductions carry over because CE-QS's B₀ reductions never rewind and never program a random oracle" — and is explicit that it does **not** itself establish items 2–6 hold for any concrete instantiation. This is the correct way to flag a plausible but unproven path, matching the discipline v0.5/v0.6 used for the QROM question and v0.6 used for the lattice-native mask adapter.
- **§17's DQS comparison is scoped correctly**: it neither claims DQS invalidates Theorem 12.1 nor claims Theorem 12.1 makes DQS unnecessary — it correctly identifies these as answering different questions (transferable certificate vs. deployable communication pattern), which matches the real DQS paper's own framing once checked (§5 below).
- **The proof-status table (§20) is honest**: "Formal QPT security" and "Concrete <32-KiB implementation" are both marked **open**, and "B₀ is theoretically closed but practically open" (§18, §21) is stated plainly rather than blurred into a stronger claim.

**No logical gaps found in this pass.** This is, notably, the first validation pass in this series (v0.4–v0.8) that found no substantive correction needed — see §6.

---

## 3. Independent recomputation of the combinatorial claims

| Quantity | v0.8 states | Recomputed | Match |
|---|---|---|---|
| `q = n−f` at n=64, f=21 | 43 | 43 | YES |
| `2q−n` at n=64, f=21 | f+1 = 22 | 22 | YES |
| Bitmap size at n=64 | 8 bytes | 64 bits = 8 bytes | YES |
| Checker script re-execution | matches shipped `results.txt` | byte-for-byte identical | YES |

The checker script's own exhaustive checks were also re-verified conceptually: `check_policy(n)` brute-forces *every* `(B,z)` pair for `n∈{3,4,5}` and asserts `f_B(B,z) == (supp(B)⊆supp(z))` — this is Lemma 5.1 checked by exhaustion rather than proof, and it is the correct exhaustive test for that lemma (2^(2n) pairs checked per n, all pass). `check_bft` independently recomputes the `2q−n=f+1` identity for two small instances. The `mutation_unbound_bitmap` test is a well-chosen negative case: it demonstrates concretely that a valid `q=3` threshold-satisfying witness `z=(1,1,1,0)` does **not** validate under a *mismatched* bitmap `(1,1,0,1)` — i.e., that the bitmap must be bound into the verified policy (§15's point), not carried as unauthenticated metadata alongside a generic threshold proof.

---

## 4. External fact-check: does the real EUROCRYPT 2024 paper support what v0.8 says about it?

The actual paper — Brodsky, Choudhuri, Jain, Paneth, *Monotone-Policy Aggregate Signatures*, EUROCRYPT 2024 / ePrint 2024/899 — was fetched in full through Section 6.1 (Introduction, Technical Overview, Preliminaries, and the two main constructions with their theorems and proofs).

| v0.8 claim | Checked against paper | Result |
|---|---|---|
| Definition 4.1's unforgeability game: adversary may query verification keys, signatures, and signing keys, adaptively; `b_i=1` iff key is maliciously generated, or adversary got a signature on `M` under it, or adversary got its signing key; adversary wins iff `f(b)=0` and `AggVerify` accepts | Paper's actual Definition 4.1: (cite index="66-1">for i∈[k], let b_i=1 if one of the following conditions holds — A did not make a verification key query answered with vk_i (a maliciously generated key); A made a signing query for vk_i,m; A made a signing key query for vk_i; otherwise b_i=0 — and A wins the game if f(b1,...,bk)=0 and AggVerify(crs,f,v̂k,m,σ)=1</cite> | **Confirmed essentially verbatim.** v0.8's own-words paraphrase in §1 reproduces the structure of the real definition exactly, condition-for-condition. |
| Weighted-threshold policies are explicitly supported, with the threshold function using state `S=log k` | Paper's own framing: (cite index="66-1">this class of monotone policies includes, for example, the t-out-of-k threshold function with state of size S=log k, or the weighted threshold function for weights in [B] with state of size S=log kB</cite> | **Confirmed exactly.** |
| A fast-aggregation variant exists whose aggregation time is polynomial in `t` (signatures provided) rather than `k` (total registry size), for threshold policies | Paper's Theorem 1.2 (Informal): (cite index="66-1">assuming the existence of somewhere extractable BARGs, there exist aggregate signature schemes for threshold policies such that the size of the CRS, the aggregated signature, and the verification time are poly(log k, λ), and the aggregation time is poly(t, λ) for threshold t</cite> | **Confirmed exactly**, including the specific poly(log k, λ) vs poly(t, λ) split v0.8 §11 relies on. |
| Theorem 3.6 gives a Λ-secure somewhere-extractable BARG assuming LWE or DLIN hardness | Paper's actual Theorem 3.6: (cite index="66-1">there exists a Λ-secure seBARG for BatchIndexTMSAT assuming Λ-hardness of LWE or DLIN</cite> | **Confirmed exactly**, same theorem number, same statement. |
| The construction is built from somewhere-extractable BARGs, hash families with local opening, and (2-composable) verifiable PIR | Paper's own structure: Section 3.2 is "Hash Family with Local Opening," Section 3.3 is "Somewhere Extractable Batch Arguments (seBARGs)," and Section 6 is "Composable Verifiable Private Information Retrieval for Policies," used exactly as the building blocks for the main constructions in Sections 5.3–5.4 | **Confirmed** — this is the paper's actual architecture, not a loose gloss. |
| The security definitions (Definition 3.1 for base signatures, Definition 4.1 for aggregation) are written for classical (PPT) adversaries with no explicit quantum treatment | Paper's Definition 3.1: (cite index="66-1">for any admissible poly-size adversary A, there exists a negligible function negl such that... Pr[Verify(...)=1] ≤ negl(λ)</cite> — no QROM/QPT framing anywhere in the fetched sections | **Confirmed** — v0.8's caution about not relabeling this "QPT-secure" is correct and not overcautious. |
| A July 2026 systems paper ("DQS") sidesteps the compact-PQ-quorum-signature problem via distributed local certificate events from ordinary signatures and Bracha-style approval broadcast | arXiv:2607.17700, Kniep, Sliwinski, Wattenhofer, *Byzantine Fault-Tolerant Post-Quantum Distributed Quorum Signatures*, submitted 20 Jul 2026: (cite index="67-1">we introduce a primitive we call Distributed Quorum Signature (DQS), built solely from ordinary digital signatures and a Bracha-style approval broadcast... weak certificates capture safety, strong certificates capture liveness</cite>, explicitly motivated because (cite index="68-1">no post-quantum alternative with constant size aggregates exists... quorum signatures are a true show-stopper</cite> | **Confirmed** — real paper, correct authors, correct date, correct characterization of its approach and motivation. |

**No fabricated or misattributed claim was found.** Every specific, checkable technical claim v0.8 makes about the EUROCRYPT 2024 paper and the DQS paper is accurate.

### 4.1 One item not independently confirmed

v0.8 §13 cites "the paper's weighted-threshold Theorems 7.5 and 7.6" for the standard-assumption lattice route. The fetch performed this pass covered the paper through Section 6.1 (stopping partway into the vPIR construction); Section 7 ("BARGs with Adaptive Subset Extraction for Bounded-Space Policies," which per the paper's own table of contents includes "7.2 Adaptive Subset Extraction with Sublinear Prover for Threshold Policies") was not reached in the fetched text, so the specific theorem numbers 7.5/7.6 could not be checked directly. The general claim — that Section 7.2 addresses exactly the threshold-policy sublinear-prover result — is consistent with the table of contents and with Theorem 1.2's informal statement (already confirmed above), so this is flagged as **plausible but not independently verified**, in the same spirit as the LaBRADOR/Falcon per-N figures flagged unverified in the v0.7 pass, rather than as an error.

---

## 5. What this pass does and does not change

- **Confirms all proof logic exactly** (§2–§3): Lemma 5.1, the Theorem 6.1 forgery reduction, the exact-soundness/conflict-extraction/non-frameability/BFT-composition chain, and the checker script's reproducibility all check out with no gaps.
- **Confirms every specific, checkable external claim about the EUROCRYPT 2024 paper** (§4): the unforgeability game structure, weighted-threshold support, the fast-aggregation theorem, Theorem 3.6's exact statement, the seBARG/hash-family/vPIR architecture, and the classical-only framing of the security definitions.
- **Confirms the DQS paper citation** (§4) as real, correctly dated, and accurately characterized.
- **Correctly carries forward the v0.7 correction** (§0 of v0.8 itself, verified in §4 of the prior validation pass): v0.8 cites Lemur at 185.5 KB, not the earlier erroneous 201.2 KB — this is good practice, propagating a prior correction rather than letting it silently drift back.
- **Issues no new correction.** This is the first document in the v0.4–v0.8 series where the validation pass found no factual or logical error to flag — the ALBA→ELBA fix (v0.4), the "not impossible, just non-compact" refinement (v0.5), and the Lemur figure fix (v0.7) all had a substantive correction; this pass does not.
- **Leaves one detail flagged as unverified rather than confirmed** (§4.1): the specific "Theorems 7.5/7.6" numbering, due to fetch coverage stopping before Section 7.
- **Leaves every one of v0.8's own listed open items open** (§20 of v0.8): formal QPT security and a concrete <32-KiB implementation are both still open, and B₁ (hidden signer set) is explicitly and correctly stated as unaffected — v0.8 does not claim to solve, and does not solve, the CET/privacy track.

---

## 6. Recommended next concrete task

Three bounded, well-scoped tasks follow directly from this pass, in the same "fetch and check" spirit as v0.5–v0.7:

1. **Close the one unverified citation** (§4.1): fetch the remainder of ePrint 2024/899 (Sections 7–8, currently unread) to confirm the exact numbering and statement of the weighted-threshold theorems v0.8 §13 relies on for its LWE-based standard-assumption claim.
2. **Begin the practical-instantiation question v0.8 correctly leaves open** (§18, §21): the paper's BARG/hash-tree/vPIR machinery has, to this validator's knowledge, no published concrete implementation or byte-level benchmark comparable to the CTRS/LoTRS/Lemur/Chipmunk numbers already gathered in the v0.6/v0.7 passes. The next honest step is the same kind of literature search performed for CTRS in v0.6: check whether any concrete parameter estimates or implementation exist for seBARG + hash-tree + 2-composable-vPIR-based aggregate signatures at anything resembling `n=64` before assuming the construction is asymptotically compact but concretely unknown (as v0.8 itself already correctly assumes, §18 — this task would only sharpen "unknown" into either "measured and large" or "no implementation exists yet," the same kind of sharpening v0.6→v0.7 did for CTRS→LoTRS).
3. **Scope the Quantum-Lift Criterion's items 2–6 concretely** (§14 of v0.8): identify whether QPT/QROM-secure analogues of somewhere-extractable BARGs, hash families with local opening, and 2-composable vPIR are independently known in the literature (each is itself an active research object), to convert Theorem 14.1's conditional statement into either a citation chain or an explicit list of open sub-problems, mirroring how v0.6's CET-liftability definition converted an abstract question into a concrete checklist (C1–C7).

None of these are required to validate v0.8's own claims, which check out as stated; they are the natural continuation the document's own "practical status" (§18) and "open" markers (§20) point to.

---

## Appendix A — Sources fetched and used in this pass

- `eprint.iacr.org/2024/899.pdf` — Brodsky, Choudhuri, Jain, Paneth, *Monotone-Policy Aggregate Signatures*, EUROCRYPT 2024 (fetched through Section 6.1; used for §2, §4 — Definition 4.1, Theorem 1.1, Theorem 1.2, Theorem 3.6, Section 3.2/3.3/6 architecture, Definition 3.1).
- `arxiv.org/abs/2607.17700` and `arxiv.org/html/2607.17700` — Kniep, Sliwinski, Wattenhofer, *Byzantine Fault-Tolerant Post-Quantum Distributed Quorum Signatures* (fetched; used for §4, §5 — abstract and introduction).

**Scope note:** none of these sources, this document, or the v0.8 (Target B₀) files it validates modify or are referenced by `PQAQCEpochBarrier_v0_8.tla`, `PQAQCEpochBarrier_v0_8.cfg`, `pqaqc_finite_state_check_v0_8.py`, `pqaqc_modelcheck_v0_8_results.txt`, `verify_pqaqc_v0_8_artifacts.py`, or `PQ_AQC_v0_8_SHA256SUMS.txt`. The deployed Target A epoch-barrier release remains exactly as previously audited.
