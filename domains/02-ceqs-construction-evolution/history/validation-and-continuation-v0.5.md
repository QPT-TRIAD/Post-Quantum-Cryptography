# CE-QS Validation and Continuation
## v0.5 Formal Proof Stack — Independent Validation + Scoping for the Next Milestone

**Status:** validation record + limited continuation. Not a security proof, not a priority claim, not production cryptography.
**Date:** 2026-09-08
**Scope:** `PQ_CE_QS_v0.5_proof_corrections.md` and `PQ_CE_QS_formal_proof_stack_v0.5.md`, checked against the shipped `PQ_CE_QS_v0.5_SHA256SUMS.txt` and against the real CCS 2025 base paper (web-fetched in full: `eprint.iacr.org/2025/113.pdf`).
**Follows:** `PQ_CE_QS_v0_4_validation_and_corrections.md` (research-synthesis finalization + ALBA→ELBA correction, previous session).
**Explicitly does not touch:** `PQAQCEpochBarrier_v0_8.tla`, its `.cfg`, the finite-state checker, or the v0.8 SHA-256 manifest. Target A (deployed, sidecar-based) remains untouched.

---

## 1. Artifact integrity

```
FILE                                     MANIFEST (v0.5 SHA256SUMS)                                        COMPUTED                                                          MATCH
PQ_CE_QS_formal_proof_stack_v0.5.md      90437547bc349b35a674b33b370e8a45472c327656420f0e93912931b9e971c0  90437547bc349b35a674b33b370e8a45472c327656420f0e93912931b9e971c0  YES
PQ_CE_QS_v0.5_proof_corrections.md       3af42ec973a20fde4ffb57766fe188765884d176e2427a05fedfce134dff9c47  3af42ec973a20fde4ffb57766fe188765884d176e2427a05fedfce134dff9c47  YES
```

**Result: PASS.** Both files are exactly what the manifest claims (filename `.` vs `_` is a naming convention difference only; the bytes match).

---

## 2. What v0.5 is actually claiming, and whether the proof-correction chain holds up

v0.5's own framing (Section 0) is a two-part correction to v0.4:

1. **Naming correction (inherited from the v0.4 audit):** the CCS 2025 base paper uses **ELBA**, not plain ALBA, because plain ALBA needs fully unique signatures and CE-QS/the base paper's tags are only partially unique.
2. **A second, new correction that v0.5 derives itself:** v0.4's Section 12 claim — *"any positive ELBA slack (`n_p > n_f`) makes exact 43-of-64 liveness impossible"* — is **too strong**. v0.5 shows that setting `n_f = 42, n_p = 43` gives *zero* slack above the honest floor and is therefore theoretically compatible with exact liveness; the real obstruction is that the resulting proof is enormous (tens of MiB), not that it's impossible.

This is a substantive, falsifiable technical claim, so it was checked against the actual source rather than taken on the document's own authority.

### 2.1 External check against the real CCS 2025 paper

The full paper (Chiang, Damgård, Duro, Engan, Kolby, Scholl, *Post-Quantum Threshold Ring Signature Applications from VOLE-in-the-Head*, ACM CCS 2025 / ePrint 2025/113) was fetched directly. Findings:

| v0.5 claim | Checked against paper | Result |
|---|---|---|
| ELBA (Expanded ALBA) is a distinct primitive from ALBA, defined because plain ALBA needs full uniqueness and the base scheme only has partial (tag) uniqueness | Paper's own contributions paragraph: *"ALBA originally requires fully unique signatures... With tag functions, we instead get the guarantee that one component of the signature is unique. We therefore define Expanded ALBA (ELBA)..."*, formalized in **Definition 6.1** and **Theorem 6.2**, Section 6.1–6.2 | **Confirmed exactly.** |
| ELBA has parameters `n_f < n_p`; completeness holds for provers who know ≥ `n_p` valid items; knowledge soundness extracts a set of size `> n_f` | Definition 6.1: completeness for `W(S_p) ≥ n_p`; knowledge-soundness extractor guarantees `W(S) > n_f` | **Confirmed exactly**, same variable names, same direction of inequalities. |
| Equation (13): `u ≥ (λ_sound + log₂λ_comp + 1 − log₂log₂e) / log₂(n_p/n_f)` | Paper's own eq. (13), Section 6: identical formula (paper writes `log` for `log₂`, consistent with the paper's own worked example, see below) | **Confirmed exactly**, formula and variable names match. |
| At ring size `2⁶ = 64`, one linkable AES128 threshold-ring signature is **9.91 KB** | Paper's Table 1 (also reproduced as the expanded Table 2): row "This work ✓ AES128", column `2⁶`, value **9.91** | **Confirmed exactly**, to the reported decimal. |
| Paper's Example 6.3 says proof size is evaluated by multiplying one signature's size by `u` | Paper Example 6.3: *"the size of the proof can be directly evaluated by multiplying the size of one signature by u"* | **Confirmed exactly**, near-verbatim in the actual text (paraphrased here per citation rules). |

**No fabricated or misattributed technical claim was found.** The ELBA formalism, the equation, and the 9.91 KB figure are all real and correctly transcribed.

### 2.2 One nuance worth recording explicitly (not a defect, but worth flagging for the record)

The paper's own worked example (Example 6.3) uses a much *looser* ratio, `n_p = 2·n_f`, and gets `u ≥ 136` — a small, practical proof. v0.5 instead evaluates the same general equation (13) at the much *tighter* ratio implied by CE-QS's own exact-BFT requirement, `n_p/n_f = 43/42 ≈ 1.024`, and gets `u ≥ 3991`. These are two different, valid evaluations of the same formula at two different parameterizations — not a contradiction between v0.5 and its source. It is worth stating explicitly in the record (as this document now does) so a future reader doesn't mistake the large gap between "136" (paper's example) and "3991" (v0.5's derivation) for an error; it is exactly what you'd expect from `u`'s inverse-log dependence on `n_p/n_f` as that ratio approaches 1.

### 2.3 Independent recomputation of every downstream number

All of v0.5's derived figures were recomputed from scratch in Python rather than trusted from the document text:

| Quantity | v0.5 states | Recomputed | Match |
|---|---|---|---|
| `u` at `n_p=43, n_f=42, λ=128` | `≥ 3991` | `3990.63 → ⌈⌉ = 3991` | YES |
| Proof size at that `u`, `43×64` config | `≈ 38.6 MiB` | `3991 × 9.91 KB = 39550.81 KB = 38.624 MiB` | YES |
| `u` at `n_p=64, n_f=42, λ=128` | `≥ 223` | `222.93 → ⌈⌉ = 223` | YES |
| Proof size at that `u` | `≈ 2.2 MiB` | `223 × 9.91 KB = 2209.93 KB = 2.158 MiB` | YES |
| Exact VOLEitH concatenation, `q=43` | `426.13 KB ≈ 0.416 MiB` | `43 × 9.91 = 426.13 KB = 0.4161 MiB` | YES |
| CET tag list, `q=43 × 32 B` | `1376 bytes` | `1376` | YES |
| `C(43,2)` (tag-collision union-bound term) | `903` | `903` | YES |

**Every downstream numeric claim in Sections 0, 17, 18, and 8 of the proof stack is exact**, not rounded loosely or hand-waved.

### 2.4 Net verdict on the proof-driven correction

- The ELBA-not-ALBA naming fix: **correct**, matches the source exactly (this simply carries forward the v0.4 audit's finding).
- The "zero-slack ELBA is not impossible, but is catastrophically non-compact" correction: **correct and better than v0.4's original claim** — v0.4 asserted impossibility where the actual obstruction is a (very large, but not infinite) proof-size cost. v0.5's version is the more precise and more defensible statement, and it is now grounded in a real, re-derived, and independently-recomputed number rather than a qualitative argument.
- The exact-concatenation baseline (`426.13 KB`, sidecar-free but ~13× over the 32 KiB compactness gate) is arithmetically exact and correctly flags GC-TRS/CTRS as the open slot rather than treating the VOLEitH concatenation as a finished answer.

---

## 3. Spot-check of the proof logic itself (not just the arithmetic)

The formal proof stack (Sections 4–22) was read in full, not sampled. Observations:

- **Structural consistency with the cited source's own methodology.** R1 (one-tag hiding, Section 5), R2 (quorum anonymity, Section 9), and the unforgeability/threshold-soundness argument (Section 7) all use the same hybrid-argument pattern (replace PRF outputs with uniform values, bound the distinguishing advantage, argue the resulting distribution is independent of the secret bit) that the CCS 2025 paper itself uses in its Lemma B.1–B.3 proofs of Theorem 5.9 (correctness, anonymity, unforgeability of the base threshold-ring scheme). This is the right template to borrow and it is applied consistently.
- **The distinctness argument (Section 6)** — that duplicate-signer contributions collapse to `e_a = e_b`, which an accepted certificate already excludes — is a clean, checkable, self-contained argument (no external primitive needed beyond determinism of the tag function) and it is correct as stated.
- **The registration-first ordering assumption (Section 13, R3)** is explicitly load-bearing and explicitly flagged as such ("This ordering is load-bearing"); the document does not bury this assumption, which is good practice — a reader who disputes the assumption knows exactly which theorem it's protecting.
- **Section 21's status table is honest about scope.** It marks "ELBA 43-of-64 impossibility" as **retracted: false as a theoretical statement**, rather than quietly dropping the old claim — this is the correct way to handle a self-correction in a running proof record, and it matches this document's own finding in §2.
- **No overclaiming detected downstream of the correction.** Section 22's main abstract theorem is conditioned on A1–A9 exactly as stated, and the closing sections (23, 24) explicitly state that the Target-B compactness goal is *still unmet*, not solved by the proof pass. This is consistent with the actual state of the evidence gathered above.

**No logical gaps or unjustified steps were found in this pass.** This is a proof-sketch-level review (checking that each step's justification is the kind of step the named assumption actually licenses), not a symbol-by-symbol formal verification — that caveat is already correctly stated in the source document itself ("first complete paper-proof pass," "does not prove the concrete... circuit").

---

## 4. Scoping the next milestone (Section 24B): what's actually available for the missing-primitive slot

v0.5 Section 19 names the concrete gap precisely: an exact, compact, anonymous PQ threshold-aggregation primitive that can absorb the CET relation, with GC-TRS/CTRS (Lin, Wang, Wen, Sun, Liang, *Generic Construction of Threshold Ring Signatures and Lattice-based Instantiations*, DCC 2025 / ePrint 2025/1205) as the leading candidate.

This pass re-confirmed the paper exists and re-confirmed its own headline claim in its own words: **the CTRS instantiation is the first threshold ring signature construction with signature size logarithmic in the ring size** (`n`), built from a generic `GC-TRS` construction (identification scheme + commitment scheme + a new "t-out-of-n proof protocol" primitive) with two lattice instantiations, `LTRS` (linear) and `CTRS` (logarithmic).

**What this pass could *not* yet confirm:** concrete byte-level signature sizes for CTRS at anything close to CE-QS's target parameters (`n=64`, `q=43`). The abstract and search-indexed portions of the DCC 2025 paper describe the asymptotic `O(log n)` result and the generic framework, but a size-at-`n=64` figure comparable to the CCS 2025 paper's Table 1 was not located in this pass — that requires pulling the full PDF (DCC 2025 / Springer, paywalled; ePrint 2025/1205 open-access copy not yet fetched) and reading its own parameter tables, the way the CCS 2025 paper was read in full above for the ELBA check.

**This is flagged as the concrete next action, not silently left open:** the honest next step for Section 24B is to web-fetch `eprint.iacr.org/2025/1205` in full (parallel to how `2025/113` was fetched for this pass), extract CTRS's actual proof-size formula and any reported concrete numbers, and re-run the same kind of arithmetic check performed in §2.3 above against CE-QS's `n=64, q=43` target. That is real, boundable work for the next session — it is not blocked on anything besides doing the fetch and the arithmetic, the same way this pass did for ELBA.

---

## 5. Net effect on the v0.5 record

- **Artifact integrity: PASS.** Both v0.5 files match the shipped manifest exactly.
- **Proof-driven correction (ELBA naming + "not impossible, but non-compact"): independently confirmed against the real CCS 2025 paper**, fetched and read in full rather than trusted from citation. Every quoted parameter, definition, equation, and table value matches the source exactly.
- **Every downstream number in the corrected argument (u≥3991, ≈38.6 MiB, u≥223, ≈2.2 MiB, 426.13 KB, 1376 bytes, C(43,2)=903) was independently recomputed and matches exactly.** Nothing in this chain was taken on faith.
- **Proof logic (Sections 4–22): spot-checked, structurally sound, consistent with the base paper's own proof methodology, and honest about what remains conditional/open.** No gaps found at the proof-sketch level.
- **One nuance recorded for the permanent record (§2.2):** v0.5's `u≥3991` and the base paper's own example `u≥136` are not in tension — they're the same formula evaluated at deliberately different `n_p/n_f` ratios (CE-QS's tight exact-liveness ratio vs. the paper's own looser illustrative ratio).
- **The next concrete, boundable task is identified and scoped (§4):** fetch ePrint 2025/1205 in full and extract CTRS's real size formula/parameters, to give Section 24B's feasibility study actual numbers to check against the 32 KiB gate, exactly as this pass did for the ELBA/equation-13 chain.

Nothing in this document closes any of v0.5's own listed open items (Section 21: exact compact aggregate backend, concrete VOLEitH circuit, concrete CTRS/GC-TRS adapter, QROM CE-QS proof, independent review — all still open). This document only checks that the v0.5 proof-driven correction is real, exact, and honestly scoped, and stakes out the next fetch-and-check task.

---

## Appendix A — Sources fetched and used in this pass

- `eprint.iacr.org/2025/113.pdf` — Chiang, Damgård, Duro, Engan, Kolby, Scholl, *Post-Quantum Threshold Ring Signature Applications from VOLE-in-the-Head*, CCS 2025 (fetched in full; used for §2.1, Table 1, Definition 6.1, Theorem 6.2, equation 13, Example 6.3).
- `eprint.iacr.org/2025/1205` and `link.springer.com/article/10.1007/s10623-025-01660-6` — Lin, Wang, Wen, Sun, Liang, *Generic Construction of Threshold Ring Signatures and Lattice-based Instantiations*, DCC 2025 (abstract/search-indexed content only this pass; full-text fetch is the flagged next step, §4).

**Scope note:** none of these sources, this document, or the v0.5 files it validates modify or are referenced by `PQAQCEpochBarrier_v0_8.tla`, `PQAQCEpochBarrier_v0_8.cfg`, `pqaqc_finite_state_check_v0_8.py`, `pqaqc_modelcheck_v0_8_results.txt`, `verify_pqaqc_v0_8_artifacts.py`, or `PQ_AQC_v0_8_SHA256SUMS.txt`. The v0.8 Target A release remains exactly as previously audited.
