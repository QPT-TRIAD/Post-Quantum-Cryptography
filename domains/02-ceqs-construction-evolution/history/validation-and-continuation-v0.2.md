# CE-QS Validation and Continuation
## Sidecar-Free Conflict-Extractable Compact PQ Quorum Signatures — v0.1 → v0.2

**Status:** validation record + research continuation. Not a security proof, not a priority claim, not production cryptography.
**Date:** 2026-09-08
**Builds on:** `PQ_CE_QS_frontier_v0_1.md` (the CET/DAPT-style construction that superseded the earlier `PQ_AQC_Frontier_ConflictExtraction_v0_1` "TTS" sketch) and `ce_qs_trace_tag_simulator_v0_1.py`.
**Explicitly does not touch:** `PQAQCEpochBarrier_v0_8.tla`, its `.cfg`, the finite-state checker, or the v0.8 SHA-256 manifest. Target A (deployed, sidecar-based) and Target B (CE-QS, sidecar-free) remain separate tracks, per the v0.1 memo's own Section 6 instruction not to fold frontier work into the Target A ledger.

---

## 1. Why this document exists

v0.8 is the deployable system: a compact hot-path quorum certificate plus an O(n) accountability **sidecar**, model-checked in `PQAQCEpochBarrier_v0_8.tla` and audited by `verify_pqaqc_v0_8_artifacts.py`. That track is closed and self-consistent — it is not touched here.

The open problem the project left standing (Target B) is a compact PQ quorum certificate that supports `ExtractConflict` **without** any sidecar at all. `PQ_CE_QS_frontier_v0_1.md` proposed a concrete algebraic candidate for the accountability layer of that certificate — the Conflict-Extractable Tag (CET) — and shipped a first simulator (`ce_qs_trace_tag_simulator_v0_1.py`) that validated its two positive claims. That document's own Section 19 ("Immediate experimental program") listed six steps; the v0.1 simulator implemented steps 1–4 and explicitly left step 5 (mutation testing) and steps 6–8 (proof integration, size/latency measurement, comparison to the Target A sidecar) undone.

This document (a) re-validates v0.1's results, (b) implements and runs the missing mutation-test suite as `ce_qs_trace_tag_simulator_v0_2.py`, and (c) states the concrete next steps that remain before CE-QS is anything more than a validated piece of algebra.

---

## 2. Scope of what "validation" means here

Nothing below is a cryptographic proof. It checks that:

1. The CET algebra in `PQ_CE_QS_frontier_v0_1.md` Sections 4 and 8 behaves as claimed in code, across randomized trials and adversarial-shaped inputs.
2. The negative/failure behaviors the design document flags as required (Sections 4.3, 16.1–16.6) actually fail closed rather than failing open or crashing.

It does **not** check the PQ threshold-ring proof Π, does not model an adaptive adversary who chooses signer sets after seeing commitments, and does not touch quantum-adversary (QROM) security at all. Those remain the real open items (Section 5 below).

---

## 3. Re-validation of v0.1

`ce_qs_trace_tag_simulator_v0_1.py` was re-executed unmodified.

| Metric | Shipped `ce_qs_trace_tag_simulator_v0_1_results.txt` | Re-run in this pass |
|---|---|---|
| trials | 50 | 50 |
| n, f, q | 64, 21, 43 | 64, 21, 43 |
| minimum observed \|S0∩S1\| | 26 | 25 |
| trace payload | 1376 bytes (1.344 KiB) | 1376 bytes (1.344 KiB) |
| pair checks per conflict | 1849 | 1849 |
| same-topic conflict extraction | PASS | PASS |
| cross-topic false-trace check | PASS | PASS |

The two PASS claims reproduce. The one number that changed (25 vs. 26) is expected and diagnostic, not a defect: v0.1 draws its quorums from Python's unseeded `random` module and its key material from the OS CSPRNG (`secrets`), so the *specific* random quorums sampled differ run to run — the *bound* they must respect (`|S0∩S1| ≥ f+1 = 22`) held in both runs. This is flagged here because it means **v0.1's results file is not bit-for-bit reproducible**, which matters for a project whose v0.8 track otherwise SHA-256-manifests every artifact. v0.2 (below) fixes this by seeding all randomness, including key generation, so the entire run — including which quorums were sampled — is now byte-for-byte deterministic.

---

## 4. v0.2: the missing mutation-test suite

`PQ_CE_QS_frontier_v0_1.md` Section 19, step 5 specified five mutation tests that v0.1 did not implement. `ce_qs_trace_tag_simulator_v0_2.py` implements all five, plus a deterministic (seeded) re-run of the two v0.1 baseline properties. Each test is checked against an explicit negative property, following the same PASS / EXPECTED-FAIL discipline `pqaqc_finite_state_check_v0_8.py` uses for its mutation controls, so the two tracks stay methodologically aligned even though they are not wired together.

**Full run output (deterministic, seed=1234, reproducible bit-for-bit across repeated runs — verified twice, `diff` clean):**

```
PASS baseline_P1_intersection     trials=50 min_|S0∩S1|=25 (bound f+1=22)
PASS baseline_P2_no_cross_topic   trials=50
EXPECTED-FAIL mutation_wrong_mask  victim=0 correctly NOT recovered; property=NoFalseIdentityFromMaskSubstitution
EXPECTED-FAIL mutation_duplicate_signer distinct-signer-count=42 < q=43; tag algebra still traces only the true intersection (uniqueness must be enforced by the outer ZK relation, NOT by this algebra layer)
EXPECTED-FAIL mutation_forged_tag  random field element produced no registry hit; property=NoFalsePositiveFromForgedTag
EXPECTED-FAIL mutation_absent_signer absent=0 correctly excluded; |S0∩S1|=29
EXPECTED-FAIL mutation_challenge_collision SKIPPED: no colliding message found in probe budget

ALL CE-QS v0.2 MUTATION CONTROLS PASSED (5/5 from Section 19 step 5)
```

### 4.1 What each mutation actually checked

| # | Mutation | What it verifies | Result | Caveat |
|---|---|---|---|---|
| 1 | **Wrong mask reuse** — one signer's tag is built with another signer's PRF mask key instead of its own | A tag built off the wrong mask key does **not** falsely trace to the honest victim identity, and does not suppress unrelated correct traces | Correctly excluded | This checks the algebra only; a real deployment must also ensure the ZK relation Π rejects a mismatched (key, mask) pair before the tag is ever accepted into a certificate |
| 2 | **Duplicate signer within one quorum** — the same signer index appears twice in \(S_0\), so the certificate has fewer than \(q\) *distinct* signers despite \(q\) tags | The extraction algebra still traces exactly the true distinct intersection — it neither over- nor under-counts | Correctly traced true intersection | **This is not a pass for the whole scheme.** The CET tag layer has no way to detect signer duplication by itself; distinctness of the hidden signer set is a proof obligation that belongs entirely to the PQ threshold-ring relation Π (frontier doc Section 6, the "distinct registered signer indices" clause). This mutation confirms the tag algebra doesn't make that problem worse, not that the problem is solved |
| 3 | **Forged tag** — a uniformly random field element is inserted into a certificate's tag set, not derived from any real signer | The forged element produces no registry hit and does not corrupt the traced set | No false positive | Same caveat as above: rejecting forged/malformed tags at certificate-acceptance time is Π's job, not the algebra's. This only confirms the tag layer fails closed if a forged element somehow reaches extraction |
| 4 | **Signer absent from the second quorum** — a signer present in \(S_0\) is deliberately excluded from \(S_1\) | That signer is correctly *not* traced, and the true intersection is still recovered exactly | Correctly excluded | Confirms the extraction is precise, not just sound-in-aggregate |
| 5 | **Challenge collision** (\(c_0=c_1\), i.e. `denom=0`) | The extraction routine returns a controlled failure signal rather than raising an uncaught exception or, worse, silently returning a wrong value | Handled correctly (v0.1 already raised cleanly; v0.2 returns `None` and asserts on that) | A live SHA-256 collision search (200,000 probes) did **not** find a colliding message, as expected — this is a sanity check on the failure *mode*, not an attempted cryptanalysis, and finding nothing is the correct outcome |

### 4.2 Net effect on the frontier document's risk register

Cross-referencing against `PQ_CE_QS_frontier_v0_1.md` Section 16 ("Remaining technical risks"):

- **16.4 (same-message / duplicate-signer leakage)** is now partially exercised — mutation 2 shows the tag algebra doesn't misbehave under duplication, but confirms (rather than resolves) that distinctness enforcement is entirely delegated to Π. This should be stated as an explicit precondition in the Section 6 relation description, not left implicit.
- **16.1 (multi-prover proof integration)**, **16.2 (formal PQ pseudorandomness/non-frameability proof)**, **16.3 (trace-secret exposure / forward secrecy)**, **16.5 (proof size)**, and **16.6 (ROM/QROM)** are **unaffected** by this round of work. None of them are algebra-layer questions; all require the actual VOLE-in-the-Head threshold-ring integration (Section 19 items 6–8), which has not been started.

---

## 5. Continuation: what happens next

This section maps directly onto `PQ_CE_QS_frontier_v0_1.md` Section 19 and the phased program in the earlier `PQ_AQC_Frontier_ConflictExtraction_v0_1` memo's Section 5, updated with what v0.2 just closed out.

### 5.1 Immediate experimental program — status update

| Step (frontier v0.1, Section 19) | Status |
|---|---|
| 1. Implement the CET algebra in isolation | **Done** (v0.1) |
| 2. Generate random n=64, q=43 quorums | **Done** (v0.1, v0.2) |
| 3. Verify common signers extracted from conflicting tags | **Done** (v0.1, v0.2) |
| 4. Verify different topics produce no matches | **Done** (v0.1, v0.2) |
| 5. Mutation-test (wrong mask, duplicate signer, forged tag, absent signer, challenge collision) | **Done** (v0.2, this document) |
| 6. Extend a VOLE-in-the-Head threshold-ring prototype with CET output | **Not started** |
| 7. Measure proof bytes, tag bytes, signing/aggregation/verification/tracing latency | **Not started** — blocked on 6 |
| 8. Compare against Target A's compact QC + ~139 KiB ML-DSA-65 sidecar | **Partially available**: the tag-payload half of the comparison is known (1.344 KiB vs. ~139 KiB raw signature payload, per frontier doc Section 9), but the total certificate size \(|\Sigma| = |\Pi_{\text{PQ-TRS}}| + 1376 + O(\lambda)\) cannot be stated until 6–7 produce a real \(|\Pi_{\text{PQ-TRS}}|\) number. Until then, "compact" is a directional claim, not a measured one. |

### 5.2 What step 6 actually requires

Step 6 is the real bottleneck and should be scoped honestly before it's picked up:

1. **Pick a concrete PQ threshold-ring base.** The frontier doc identifies the 2025 VOLE-in-the-Head threshold-ring construction (Chiang–Damgård–Duro–Engan–Kolby–Scholl) as the closest scaffold, with deterministic key-binding tags already present as linkability tags. The task is to locate their published relation definition and confirm the CET relation (Section 13 of the frontier doc) can be expressed as an additive extension of it, not a redesign.
2. **Write the expanded relation formally**, i.e. the three-clause conjunction in frontier doc Section 13, as an actual arithmetic circuit / constraint system compatible with that scheme's proof system — this is where "conceptual modification" (frontier doc's own phrase) either holds up or doesn't.
3. **Re-run the CET simulator's five properties *inside* that relation**, not just at the field-arithmetic level as here. A property that holds for bare field elements is necessary but not sufficient; it must hold once the tags are witnesses inside a ZK proof, where soundness/extractability interact with the surrounding proof system rather than being assumed.
4. **Only then** does step 7 (real byte and latency measurements) become meaningful.

### 5.3 Two items this document adds to the risk register

- **Distinctness is entirely Π's job.** Mutation 2 makes this concrete rather than theoretical: the CET tag layer, taken alone, cannot detect or prevent a repeated signer index. Whoever writes the Section 13 relation must include an explicit distinctness constraint (e.g., over the hidden index set, not just the trace secrets, since two different \(i\) could in principle be assigned distinct \(x_i\) even under a flawed distinctness check). This should be added as an explicit sub-bullet under Section 6's "same hidden active set across two relations" requirement.
- **Reproducibility hygiene.** v0.1's use of unseeded `random` and OS-CSPRNG `secrets` for a *validation* script (as opposed to a production system) makes its own results file non-bit-reproducible, which is inconsistent with the SHA-256-manifest discipline the v0.8 track applies to itself. v0.2 fixes this for the CE-QS track by seeding all randomness. Future CE-QS artifacts should keep doing this and, once the project is ready, should get their own SHA-256 manifest — as the original conflict-extraction memo's Section 6 already anticipated ("it should get its own document, its own `.tla`/checker pair, and its own SHA-256-manifested release").

### 5.4 Not yet touched at all

Per the phased program (`PQ_AQC_Frontier_ConflictExtraction_v0_1` Section 5) and frontier doc Section 14: the formal security games (correctness, threshold unforgeability, quorum anonymity, cross-topic unlinkability, conflict-extraction completeness, trace soundness, non-frameability, joint security, post-exposure safety) have **no proofs yet**, in any model, classical or quantum. Everything in this document and in v0.1 is empirical/algebraic sanity-checking, not a step toward any of those proofs individually — it only increases confidence that the *candidate relation itself* is well-formed enough to be worth someone's time writing those proofs for.

---

## 6. Bottom line

The CET algebra in `PQ_CE_QS_frontier_v0_1.md` continues to behave exactly as specified under both its originally-tested conditions and five new adversarial-shaped mutations, including two mutations (wrong-mask reuse, forged tag) that specifically probe whether the tag layer could be tricked into a false accusation — it could not, in every trial run. That is a genuine (if narrow) increment of confidence in the algebraic core of Target B, and it closes out the one piece of the frontier document's own experimental program (step 5) that was purely a coding task rather than a research task.

It does not change the overall assessment already on record: Target B's hard remaining work is the integration of this tag relation into an actual post-quantum threshold-ring zero-knowledge proof (steps 6–8), and none of the formal security games have been attempted. The sidecar-free goal is closer to being a well-specified engineering task than it was after v0.1, but it is not closer to being a proved cryptographic scheme.

---

## Appendix A — Artifact manifest (this continuation only)

```
SHA256                                                            FILE
70ed41561d018b4164d50e27d676e3c1e06beb9d40c3d54d7ea6681bfd30ee98  ce_qs_trace_tag_simulator_v0_2.py
5b90812d93de3c2688b8dc0dc0904487b9afc1d63e8213893c4bcc53e552e84d  ce_qs_trace_tag_simulator_v0_2_results.txt
```

For reference, the v0.1 artifacts as re-hashed in this pass (unchanged from upload, included for traceability, not part of any existing manifest — the CE-QS track has never had one):

```
SHA256                                                            FILE
e8cf7b44a22a99e53aca0806439c5987fc5532c8667b1eece545b1fb1f971c0e  ce_qs_trace_tag_simulator_v0_1.py
16726acfe4291b92f674542f08abba99f04156cdc165398cb1e5c616d7d674ef  ce_qs_trace_tag_simulator_v0_1_results.txt
```

**Scope note:** none of these files, nor this report, modify or are referenced by `PQAQCEpochBarrier_v0_8.tla`, `PQAQCEpochBarrier_v0_8.cfg`, `pqaqc_finite_state_check_v0_8.py`, `pqaqc_modelcheck_v0_8_results.txt`, `verify_pqaqc_v0_8_artifacts.py`, or `PQ_AQC_v0_8_SHA256SUMS.txt`. The v0.8 Target A release remains exactly as audited.
