# CE-QS Validation and Continuation
## v0.3 Finalized Construction — Relation-Mock Validation + Extension Pass

**Status:** validation record + research continuation. Not a security proof, not a priority claim, not production cryptography.
**Date:** 2026-09-08
**Builds on:** `PQ_CE_QS_finalized_construction_v0_3.md` and `ce_qs_relation_mock_v0_3.py`.
**Follows:** `PQ_CE_QS_validation_and_continuation_v0_2.md` (v0.1 re-validation + mutation-test suite, previous session).
**Explicitly does not touch:** `PQAQCEpochBarrier_v0_8.tla`, its `.cfg`, the finite-state checker, or the v0.8 SHA-256 manifest. Target A (deployed, sidecar-based) remains untouched.

---

## 1. Where this sits in the record

- **v0.1** proposed the CET algebra and validated its two core claims (same-topic extraction, cross-topic non-linkage) with an unseeded simulator.
- **v0.2** (previous session) re-validated v0.1 deterministically and added the five mutation tests v0.1's own experimental program had left undone (wrong mask, duplicate signer, forged tag, absent signer, challenge collision) — all at the bare field-arithmetic level, with no relation/proof structure at all.
- **v0.3** is a substantial step up: it fixes the actual relation \(\mathcal R_{\rm CEQS}\) that a real VOLE-in-the-Head circuit would need to implement (Section 9), names the specific PQ threshold-ring base it builds on (Chiang–Damgård–Duro–Engan–Kolby–Scholl, CCS 2025), finalizes distinctness as *public duplicate-tag rejection plus base-proof key-binding* rather than a vague delegation, and ships `ce_qs_relation_mock_v0_3.py` — a mock that checks contributions against the actual `(idx, sk, x, k)` witness structure instead of bare field elements.
- **This document** re-validates v0.3's shipped script and closes the remaining relation-mock-level gaps identified against v0.3's own Section 22 security-game list, before the real implementation work (WP1, Section 25) starts.

---

## 2. Re-validation of the shipped v0.3 artifacts

`ce_qs_relation_mock_v0_3.py` was re-executed unmodified against the uploaded `ce_qs_relation_mock_v0_3_results.txt`.

**Result: byte-for-byte identical.** Unlike v0.1, this script seeds its registry generation (`seed=20260908`), so the comparison is exact rather than "same shape, different numbers":

```
PASS valid_quorum_relation
EXPECTED-FAIL duplicate_signer_public_rejection reason=duplicate-tag
EXPECTED-FAIL wrong_mask_relation_binding
EXPECTED-FAIL forged_tag_relation_binding
PASS conflict_extracts_trace_secret
PASS trace_secret_exposure_alone_not_accepted
NOTE: relation mock only; real VOLEitH ZK/aggregation proofs remain unimplemented.
```

This confirms, at the relation-mock level (i.e. checking against the real `(idx, sk_i, x_i, k_i)` witness tuple and the four-way membership/auth/trace/mask binding, not just the bare tag equation):

- a full-quorum certificate with all valid, distinct, key-bound tags verifies;
- v0.2's duplicate-signer gap is now closed **structurally**: a repeated signer produces a repeated deterministic tag, which the certificate verifier rejects outright (`duplicate-tag`) rather than relying on an external distinctness proof;
- a tag built from one signer's real `sk, x` but another signer's mask key `k` fails the relation (this is a stronger check than v0.2's mutation 1, which only checked the bare CET wasn't falsely traced — this checks the full relation itself rejects the malformed contribution);
- an arbitrary forged field element fails the relation outright, not merely "fails to trace" as in v0.2;
- conflict extraction still recovers the correct `x_i` and maps to the correct registry commitment;
- knowing an exposed `x_i` alone, with no real `sk_i` or `k_i`, does not satisfy the relation for a fabricated future contribution.

---

## 3. Extension pass: closing the remaining mock-checkable gaps

v0.3 Section 22 lists 11 required security games. The shipped script exercises pieces of games 2 (threshold unforgeability), 6 (extraction completeness), 9 (key-binding/no duplicate counting), and 10 (post-trace unforgeability, partially). Before WP1 (the real relation circuit) starts, it's worth confirming the *reference relation itself* — the thing WP1 will be implementing in VOLE-in-the-Head — doesn't have gaps in the parts that a Python mock genuinely *can* check. `ce_qs_relation_mock_v0_3_ext.py` adds five checks, run against the same seeded registry:

```
PASS regression_valid_quorum            v0.3 baseline still holds
EXPECTED-FAIL below_threshold_rejection  42 distinct valid contributions correctly rejected (need >= 43)
EXPECTED-FAIL cross_topic_unlinkability  signer=7 cross-topic tags did not cancel to x_i (as required by Section 15)
EXPECTED-FAIL same_message_linkability   repeat tag is linkable (equal) but extraction is correctly undefined (c0==c1), matching Section 4.4/14
EXPECTED-FAIL identity_impersonation     real secrets of signer=7 correctly rejected against claimed index=12
EXPECTED-FAIL post_exposure_probe        200000 random guesses for k_i found no G_mask preimage; x_i exposure alone did not yield a forgeable contribution (Section 16)

ALL EXTENSION-PASS CHECKS PASSED (5 new + 1 regression gate)
```

Deterministic and reproduced twice (`diff` clean) before being written to the results file.

### 3.1 What each new check verifies, and which v0.3 section it targets

| # | Check | v0.3 reference | What it confirms |
|---|---|---|---|
| 1 | **Below-threshold rejection** | Section 7 (`s ≥ q`), Section 8 | A certificate with `q−1` fully valid, distinct, key-bound contributions is still correctly rejected. v0.3's own script never exercised the `below-threshold` branch of `verify_certificate_mock` — only `duplicate-tag` and `invalid-relation` were tested. This closes that gap. |
| 2 | **Cross-topic unlinkability** | Section 15 | Subtracting two tags from the *same signer* but *different topics* does not cancel to `x_i`, at the full-relation level (v0.2 checked this on bare field elements only). Confirms the mask term `F_{k_i}(τ)` is doing its job in the relation-mock, not just in isolated algebra. |
| 3 | **Same-message linkability without secret exposure** | Section 4.4, Section 14 | Re-signing the identical `(τ, M)` produces the identical deterministic tag (correctly linkable, by design) but does **not** hand the extractor a usable pair, since `c0 == c1` makes the denominator zero. This is the relation-mock counterpart of v0.2's challenge-collision control, but exercised as an intentional same-message case rather than a brute-force search. |
| 4 | **Identity impersonation with an otherwise-genuine witness** | Section 9 (membership clause) | An attacker holding their own fully valid `(sk, x, k)` cannot bind a contribution to a *different* registered index. This specifically tests the membership clause of `R_CEQS` in isolation from the other three clauses — every individual secret is real and self-consistent, only the claimed index is wrong, and the relation still rejects it. |
| 5 | **Bounded preimage-guess probe against `G_mask` post-exposure** | Section 16 | After a real conflict exposes `x_i`, 200,000 random guesses for `k_i` find no preimage of the public `K_i`. This is the relation-mock's version of the "post-exposure safety" property v0.3 states in prose (Section 16: "knowing `x_i` alone does not permit generation of a new accepted CET") — checked empirically against the actual `G_mask` binding rather than asserted only in the writeup. |

### 3.2 What is still not mock-checkable

This extension pass does **not** touch, and cannot touch with a Python mock:

- **Game 3, quorum anonymity** — a real distributional/indistinguishability claim about the VOLEitH transcript, meaningless against a mock that has no transcript.
- **Game 7, trace soundness (formal)** and **Game 8, non-frameability (formal)** — the mock checks specific attack shapes (wrong mask, forged tag, impersonation) fail, which is necessary evidence but not the actual reduction v0.3 Section 13 specifies. The formal statement is still unwritten.
- **Game 11, QROM security** — entirely dependent on the CRYPTO 2025 Fiat–Shamir transform being correctly instantiated (v0.3 Section 18, Milestone Q), which requires the real proof system.

These are exactly the items v0.3 itself lists as "genuinely open" in Section 27 (items 1, 2, 4, 5). Nothing in this document changes that status — it only exhausts the cheaper, relation-structure-level checks first so that when WP1 starts, the circuit spec is validated as thoroughly as a mock can validate it.

---

## 4. Net effect on the v0.3 record

- The shipped v0.3 relation mock **reproduces exactly**.
- Five additional relation-mock checks pass, each targeting a specific v0.3 section that had prose claims but no corresponding executable check: threshold enforcement at the boundary (`q−1` vs `q`), cross-topic independence at the full-relation level, same-message linkability without leakage, membership-clause isolation under impersonation, and an empirical (not just asserted) check of the post-exposure safety claim.
- **No item on v0.3's own "what remains genuinely open" list (Section 27) is closed by this work.** WP1 (the actual VOLE-in-the-Head relation implementation), the formal reductions, real proof-size measurement, the QROM transform, and independent review are unaffected — they are proof-system and implementation work, not relation-mock work, and no amount of Python mocking substitutes for them. This document should be read as "the reference relation has now been exercised about as thoroughly as a mock can exercise it," not as progress on any of the six open items in Section 27.

---

## 5. Bottom line

v0.3 correctly upgraded v0.2's algebra-only mutation tests into checks against the actual four-clause relation (membership, auth-key ownership, trace-secret binding, mask-key binding, correct CET). The shipped script's six checks reproduce exactly, and the five additional checks in this pass confirm the relation also behaves correctly on inputs the original script didn't exercise: threshold boundary, cross-topic separation, same-message linkability, membership-clause impersonation, and a bounded empirical probe of the post-exposure claim. That closes out the relation-mock work that made sense to do before WP1.

The next honest milestone remains exactly what v0.3 Section 30 says it is: **CE-QS v0.4 = actual VOLE-in-the-Head relation implementation + measured proof bytes + first formal reductions.** This document is preparatory validation for that milestone, not a step that substitutes for it.

---

## Appendix A — Artifact manifest (this continuation only)

```
SHA256                                                            FILE
bc61e06c8fad514257f73e8a022f49dd023259cf60b26050e8c84669aee8b8ef  ce_qs_relation_mock_v0_3_ext.py
0452f28716e770574c72b67f48a9e23cb7fe56fd920d8bc625327b6f1c13f6c6  ce_qs_relation_mock_v0_3_ext_results.txt
```

For reference, the v0.3 artifacts as re-hashed in this pass (unchanged from upload, confirming byte-for-byte reproduction — the CE-QS track still has no formal SHA-256 manifest of its own):

```
SHA256                                                            FILE
5825515e8c3dd529a1f95c39ae8497a3c05466a2afb2b6de035bdab6c6576f99  ce_qs_relation_mock_v0_3.py
900e768dd9d123a336becfb5d5f938c622d2cb1f22a7226d0311981a3e218c0c  ce_qs_relation_mock_v0_3_results.txt
```

**Scope note:** none of these files, nor this report, modify or are referenced by `PQAQCEpochBarrier_v0_8.tla`, `PQAQCEpochBarrier_v0_8.cfg`, `pqaqc_finite_state_check_v0_8.py`, `pqaqc_modelcheck_v0_8_results.txt`, `verify_pqaqc_v0_8_artifacts.py`, or `PQ_AQC_v0_8_SHA256SUMS.txt`. The v0.8 Target A release remains exactly as audited.
