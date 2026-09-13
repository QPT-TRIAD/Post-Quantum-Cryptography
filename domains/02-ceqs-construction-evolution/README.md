# D2 — ceqs-construction-evolution

The version ladder of the CE-QS construction: a conflict-extractable, sidecar-free, post-quantum
quorum certificate, pursued through the version numbers **v0.1 … v1.24** over two days
(8–9 September 2026). This domain holds every revision of the construction that survived in the
record, the small checker that accompanied each one, and what that checker recorded.

The value of this domain is not the current design alone. It is the sequence: which version changed
what, which claim was retracted by a later version, which branch was closed and why, and which
numbers a re-run does or does not reproduce.

*Read this file first.* It is the entry point. Everything else is reachable from the tables below.

> **Verification status, in brief.** All eleven current checkers reproduce their recorded results
> byte-for-byte in the pinned environment. **One recorded result does not fully reproduce:** the
> superseded v0.1 simulator reports `minimum observed quorum intersection=26` and yields 24, 25 or 26
> across runs, because it draws its quorums from an unseeded generator — the line is a sample
> minimum, not a computed bound. The bound that same line quotes (`f + 1 = 22`) is unaffected, every
> observed value is above it, and no later version depends on the line. Recorded in full in
> `VERIFICATION.md` §2, with every other discrepancy, absent artifact and un-run item.

---

## 1. The problem the sequence attacks

A Byzantine-fault-tolerant committee of `n = 64` validators with `f = 21` faulty votes with
quorums of `q = 2f + 1 = 43` seats. The certificate that proves "43 seats signed this block" must
satisfy three requirements at once:

1. **Conflict-extractable without a sidecar.** Two accepted certificates for conflicting messages in
   the same conflict domain (`τ`) must let *anyone* identify every seat that signed both — using only
   the two certificates and fixed public configuration. No extra per-certificate file, opener
   service, log or witness is allowed.
2. **Hidden signer set (Target B1).** One certificate must not reveal which seats signed. The
   public-signer variant (Target B0) is the same object with the bitmap disclosed.
3. **Compact.** At most 32,768 bytes total. This number is a **project engineering decision**, not a
   cryptographic limit, and it is far below the raw evidence it replaces: the ML-DSA signature witness
   alone measured 142,287 bytes (≈139 KiB) before proof encoding
   (`history/blocker-resolution-v1.19.md:77`). The byte gate appears throughout the sequence — as
   three gates at v0.3, as property E8 at v1.6, and as `43h + P + O ≤ 32768` from v1.5 on.

Quorum intersection gives the arithmetic that makes extraction possible at all:
`|S₀ ∩ S₁| ≥ 2q − n = 22 = f + 1` seats are common to any two quorums — see
`docs/formal-proof-stack.md` §15 and the checker `src/ce_qs_quorum_family_checker.py`.

The immediate predecessor is `../01-accountable-quorum-foundations` (D1): a "modify the masking
randomness inside a lattice threshold signature" idea that v0.1 abandoned in favour of separating
the hidden-threshold proof from the trace tags.

---

## 2. How to read this domain

| If you want… | Read |
|---|---|
| the sequence, what changed and why | this file, §3, and `docs/inflections/` |
| the construction as it currently stands | `docs/construction-end-to-end.md` |
| the exact bytes and the relation | `docs/32kib-contents-contract.md` (v1.24, the current revision) |
| the strongest proved theorem in the sequence | `docs/qpt-crs-security-proof.md` (v1.3) with the correction in `docs/collaborative-quorum-proof.md` (v1.4) §1 |
| what each checker asserts and returned | `VERIFICATION.md`, then `results/` |
| run the checkers | §6 below |

Authored documents (problem statement, ladder, inflections, end-to-end construction, verification)
are `README.md`, `VERIFICATION.md`, `docs/construction-end-to-end.md` and `docs/inflections/*.md`.
All other files under `docs/`, `results/`, `src/` and `history/` are **source documents**, copied
from the research tree. Line numbers cited in the authored documents refer to those copies.

**Copies are byte-identical except where a rewrite is mandated and recorded.** 56 of the 62 copied
files are byte-identical to their source. Six files carry fourteen single-line rewrites in total, each
replacing one phrase that named the working occasion as a session (the word *session* preceded by
*this*) with *this pass* — the term the same corpus already uses for the same idea — one phrase per
line, meaning preserved. The six files and their per-file counts are listed in `VERIFICATION.md` §3,
recorded in the project's `records/rewrites.tsv` (classes `scrub-ai:1…5`), and the integration gate therefore
reports no unexplained hash difference for this domain. Nothing else in any copied file was changed:
in particular, the internal references to research-tree filenames were **left as the sources wrote
them**, and §5.1 below maps every one of those names to its path here.

---

## 3. The version ladder

Legend: **current** = the map marks this file as the current revision of its lineage; **history**
= superseded, kept in `history/` with its version in the filename.

### 3.1 Track A — the abstract construction (v0.1 → v0.9)

| Version | Date | Document (repository path) | What changed | Why | Checker and what it recorded |
|---|---|---|---|---|---|
| v0.1 | 2026-09-08 | `docs/frontier.md` | First CE-QS direction: a PQ hidden-threshold proof plus per-signer conflict-extractable tags (CET); abandons the D1 idea of modifying masking randomness inside a lattice threshold signature. Tag `e_i = r_{i,τ} + c·x_i`. Certificates of size `|Π| + 1376 + O(λ)` bytes. | Layering: the hidden-threshold proof establishes "≥ q distinct registered signers"; the tags add accountability only on conflict. | `history/ce_qs_trace_tag_simulator-v0.1.py` | `PASS trials=50`; `n=64 f=21 q=43`; minimum observed intersection 26; tag payload 1376 B (1.344 KiB); 1849 pair checks per conflict. **The minimum-intersection line is nondeterministic (24/25/26 observed).** |
| v0.2 | 2026-09-08 | `history/validation-and-continuation-v0.2.md` | Validation record plus the five mutation controls that v0.1 §19 step 5 specified but did not implement. | Reproduce v0.1's algebra and mutate it. | `src/ce_qs_trace_tag_simulator.py` | `ALL CE-QS v0.2 MUTATION CONTROLS PASSED (5/5)`; but the **duplicate-signer mutant is not rejected** ("uniqueness must be enforced by the outer ZK relation") and the challenge-collision branch is skipped yet counted. |
| v0.3 | 2026-09-08 | `docs/finalized-construction.md` | Architecture frozen: post-quantum threshold-ring/VOLE-in-the-Head base instead of a lattice threshold signature; field changed to GF(2²⁵⁶); registry of three domain-separated secrets; relation `R_CEQS`; **public duplicate-tag rejection** `|set(E)|=|E|`; size gates 16 / 16–32 / >32 KiB. | The v0.2 duplicate-signer gap: algebra alone cannot reject a repeated seat. | `src/ce_qs_relation_mock.py` and `src/ce_qs_relation_mock_ext.py` | 3 PASS / 3 EXPECTED-FAIL, including `duplicate_signer_public_rejection reason=duplicate-tag`; extension: 5 new checks + 1 regression gate (below-threshold, cross-topic, same-message linkability, impersonation, exposure). |
| v0.4 | 2026-09-08 | `docs/research-synthesis-final.md` | Architecture, definitions, source tiers and fallback bases frozen; claim that the 2025 succinct-aggregation construction (ALBA) needs slack `Δ > 0`, so an **exact** 43-of-64 aggregate is impossible; Mode A (exact) split from Mode B (succinct). | A signature counted by an approximate aggregate cannot be a Byzantine-independent finality primitive. (This claim is retracted one version later.) | — (no checker) | — |
| v0.5 | 2026-09-08 | `docs/formal-proof-stack.md` | First complete paper-proof pass, conditional on assumptions A1–A9: one-tag hiding, distinctness, threshold soundness, correctness, quorum anonymity, cross-topic unlinkability, extraction completeness, ROM trace soundness, non-frameability, post-exposure, BFT conflict. **Retracts v0.4:** with ELBA's `n_f = 42, n_p = 43`, zero-slack exact 43-of-64 is theoretically compatible, but needs `u ≥ 3991` repetitions ≈ 38.6 MiB. Exact concatenation `43 × 9.91 KB = 426.13 KB` fails the 32-KiB gate by an order of magnitude. | v0.4's impossibility claim is false as a theoretical statement; the real obstacle is size. | — (no checker) | — (arithmetic re-computed in `docs/inflections/01-elba-impossibility-retracted.md` and `VERIFICATION.md` §5) |
| v0.6 | 2026-09-08 | `docs/exact-aggregator-lifting-proof.md` | Backend-neutral lifting: mask interface M1–M4, exact hidden-threshold proof TOP T1–T4, and the new adapter property **CET-liftability** L1–L7; Theorem 8.1 lifts every v0.5 reduction given three backend properties. A compact *exact* aggregator becomes mandatory. | v0.5 showed naive concatenation cannot meet the gate. | — (no checker) | — |
| v0.7 | 2026-09-08 | `docs/quorum-family-privacy-fork-proof.md` | Structured Quorum Coverage Theorem `|F| ≥ C(n,f)`; the LoTRS trichotomy (structured-quorum backends cannot serve arbitrary-fault BFT); **the privacy fork**: if signers may be public, accountability is an exact multisignature plus an `n`-bit bitmap, so the CET machinery is needed only for hidden signers. Targets **B0** and **B1** named. | Narrows the target: do not spend cryptographic complexity hiding 8 bytes. | `src/ce_qs_quorum_family_checker.py` | `PASS public_bitmap_bytes=8`; exhaustive coverage and one-omission mutant for n = 4, 7, 10; `C(64,21) = 41107996877935680`, `log2 = 55.190269`. |
| v0.8 | 2026-09-08 | `docs/public-signer-theoretical-completion.md` | Target B0 completed at the abstract level from monotone-policy aggregate signatures; bitmap-conjunction policy `f_B`; `Adv^SetFrame ≤ Adv^UF_MPAgg`; extraction `supp(B₀ ∧ B₁)`; "Target B0 is theoretically solved at the abstract cryptographic level". Corrects the Lemur figure 201.2 → 185.5 KB. | A compact, policy-selectable aggregate signature gives exact quorum semantics with public accountability. | `src/ce_qs_bitmap_policy_checker.py` | `PASS` for `f_B` equivalence at n = 3, 4, 5 (exhaustive) and BFT intersection at n = 4, 7; `EXPECTED-FAIL unbound_bitmap_attack blocked_by=f_B`; `PASS n=64 bitmap_size_bytes=8`. |
| v0.9 | 2026-09-08 | `docs/quantum-lift-private-wrapper-proof.md` | QPT ledger for B0 (dependency chain down to a vPIR/adaptive-subset-extraction bottleneck); **private wrapper** for B1 hiding the bitmap and the tags inside one NIZK, `|QC_priv| = |E| + |π_ZK| + O(λ)`, `|E| = 1376 B`; "a specialized anonymous threshold-ring signature is no longer necessary". | B0 needs unconditional extraction without a trapdoor; B1 needs the witness hidden. | `src/ce_qs_private_wrapper_relation_checker.py` | 2 PASS / 3 EXPECTED-FAIL over relation PW1–PW8, including `conflict_extracts_exact_intersection intersection=[0, 1, 2]` — the worst case `2q − n = f + 1 = 3` at n = 7. |

### 3.2 Track B — the hidden-signer theorem (v1.0 → v1.4)

| Version | Date | Document (repository path) | What changed | Why | Checker and what it recorded |
|---|---|---|---|---|---|
| v1.0 | 2026-09-09 | `docs/distributed-certified-tag-proof.md` | Per-validator certified tags plus a collector proof over `q` contributions; `QC = (v, e, τ, H(M), q, E, Π_B)`. Tag width raised 256 → **384 bits** (256-bit tags give only ≈85.3 quantum collision bits), so the public tag payload becomes `43 × 48 = 2064 B`. | The v0.9 wrapper's single prover held every signer's trace and mask secret: "not a constructible BFT protocol". | `src/ce_qs_distributed_certified_tag_checker.py` | 3 PASS / 5 EXPECTED-FAIL; `PASS collector_witness_contains_no_signer_secrets`; `PASS conflict_extracts_exact_intersection intersection=[0, 1, 2]`. |
| v1.1 | 2026-09-09 | `docs/strong-certified-conflict-handle-proof.md` | Trace interface replaced by **strong certified conflict handles** (SCCH): Setup, KeyGen, Handle, VerifyHandle, SameSigner, TraceConflict, VerifyTrace; validity-gated tracing; security games S1–S6; public `VerifyBlame`. Direct strong traceable ring signatures are functionally sufficient; the obstacle is compactness (Feng lattice TRS ≈5.80 MiB for 43 signatures; a classical DDH construction ≈38.97 KiB). | The classic traceable-ring-signature notions miss trace-specific attacks and do not imply unforgeability. | `src/ce_qs_strong_conflict_handle_checker.py` | 4 PASS / 4 EXPECTED-FAIL; `PASS exact_conflict_trace identities=[0, 1, 2]`; `PASS public_verify_blame`. |
| v1.2 | — | **not in this tree** | Known only from v1.3's description: closed the LWR adapter in the classical ROM and left four quantum issues. No file, ledger or trail entry exists. | — | — | — |
| v1.3 | 2026-09-09 | `docs/qpt-crs-security-proof.md` | **Current for the non-interactive (Mode NI) lineage.** Removes the random oracle from the load-bearing theorem: pre-sampled bounded Trace Base CRS for all domain bases, post-quantum simulation-extractable NIZK in the CRS model for both proofs, QLWR stated as its own assumption, 384-bit quantum-collision-resistant challenge hash. Full conditional QPT theorem 26.1 with nine assumptions. `|QC| = Q(d+1)·m·⌈log₂ p⌉ + |Π_B| + O(λ)`. | Both remaining quantum-random-oracle dependencies are taken out of the theorem rather than assumed away. | `src/ce_qs_qpt_crs_structural_checker.py` | 4 PASS / 2 EXPECTED-FAIL; `PASS challenge_encoding_injective toy_bits=16` (all 65,536 digests); `EXPECTED-FAIL cross_key_false_trace blocked_by=unique_link_base`; `EXPECTED-FAIL domain_budget_exhaustion safe_halt`. |
| v1.4 | 2026-09-09 | `docs/collaborative-quorum-proof.md` | **Current for the collaborative (Mode CP) lineage.** Corrects the v1.3 anonymity hybrid: replacing fresh handle outputs while holding a registered key fixed "is stronger than ordinary multi-sample LWR pseudorandomness"; the repair replaces each validator's whole bundle and the bound becomes `ε_ZK + N·ε_QLWR + ε_HandleColl` with `N = 64`. Adds collaborative zero knowledge (one NIZK prover run jointly by the selected validators) with safety-under-abort and conditional liveness. | The v1.3 bound was not justified as written. | `src/ce_qs_collaborative_quorum_checker.py` | 8 PASS / 1 EXPECTED-FAIL; exhaustive honest-majority enumeration for n = 4, 7, 10 (16 / 441 / 14400 quorum pairs); `PASS reference_64_21_43 honest_in_any_quorum>=22`. |

### 3.3 Track C — backends, budgets and blockers (v1.5 → v1.24)

| Version | Date | Document (repository path) | What changed | Why | Checker and what it recorded |
|---|---|---|---|---|---|
| v1.5 | — | `docs/compactness-source-ledger-v1.5.md` | Compactness ledger only; no proof document exists. Fixes the hard byte gate `43h + P + O ≤ 32768` and records that the then-known succinct lattice aggregate is not zero-knowledge. | A hard, checkable gate replaces discussion. | — | — |
| v1.6 | 2026-09-09 | `docs/backend-eligibility-proof.md` | Eligibility properties **E1–E8** (post-quantum security, public verifiability, witness privacy, exact threshold/same-set binding, SCCH compatibility, constructible prover, liveness adapter, byte gate) and Theorem 3.1: a backend meeting E1–E8 instantiates v1.3/v1.4 unchanged. Reclassifies the "not zero-knowledge" limitation of the 2026 suite as historical. | Turn open-ended searching into a falsifiable test. | `src/ce_qs_backend_eligibility_checker.py` | All six candidate backends `eligible=False` (LaZer-2024 FAIL at 75,300 B, CoSNIZK FAIL 38,912 B, Fusion FAIL 47,185 B, Lazarus PASS at 30,736 B on bytes but not eligible on properties); `PASS score_28KiB_48B=2032`; `EXPECTED-FAIL score_28KiB_96B=-32`. |
| v1.7–v1.17 | — | **not in this tree** | Eleven numbers with no document. Reported (not verifiable here) as: 22 equivocators required; LaZer build stopped on missing GMP headers; 96-byte handles; a rounding-bias fix; a direct bit-circuit adapter ruled out at a 79,632-byte floor; real proofs of 43 link hashes at 328,672 B; 267,472 B after re-encoding; a 96-byte-handle frame at 269,648 B; 506,848 B for a single-contributor frame; 776,736 / 785,456 B frames with 22 trace identities recovered. | — | — | — |
| v1.18 | 2026-09-09 | `docs/research-qualification.md` | Literature screen of 32 papers plus one repository: **no examined construction qualifies; valid full QCs generated remain zero**. Contract made precise (43 seats from arbitrary subsets of a flat 64-seat registry, ≥22 extracted, 128-bit QPT including losses, collaborative production under 21 Byzantine). Retires the v1.6 checklist framing: the obstacle is "a joint construction and security qualification, not a missing positive flag in the eligibility checker". Derives the retained-format floor `|QC| ≥ 50,496 > 32,768` and `C(64,43) ≈ 2^55.19`. | Every screened backend failed at least one requirement, and the binary size floor is arithmetic, not an estimate. | — (no checker; the referenced 34-check artifact is absent) | — |
| v1.19 | 2026-09-09 | `history/blocker-resolution-v1.19.md` | Adjudicates the adversarial alternative-strategy review: registration commitments do not replace message-specific checks (rejected); the 46–50 candidate pool is arithmetically wrong (rejected: worst case needs 64); a loose upper estimate is not an impossibility proof; collision is not preimage. Adds the relation inventory (13,914,112 scalar products, 6,957,056 packed multiplications, 215 Keccak permutations, 22,176,863 wires, 142,287 B ML-DSA witness), exact pool probabilities, a conditional retry theorem (≤21 blame-producing failures, ≤22 attempts), and the correction `8·2⁻¹³¹ = 2⁻¹²⁸`. | Four independent errors in the review had to be corrected before its proposals could be used. | — (the referenced 116-check model is absent) | — |
| v1.20 | 2026-09-09 | `docs/blocker-resolution.md` | **Current for the blocker-resolution lineage.** Frozen-registry optimization: **176 link rows instead of 608**, giving `ε_B-pair ≤ 1024·C(64,2)·2⁻¹⁷⁶ = 63·2⁻¹⁶¹ ≈ 2⁻¹⁵⁵·⁰²`, total `≈ 2⁻¹⁵⁴·⁸⁸`. Corrected public conflict theorem with explicit premises. New executed trace circuit: 9,800,861 gates (from 14,988,983), 4,579,328 packed multiplications, 86 Keccak permutations, **0 ML-DSA constraints**, frames 722,528 / 729,728 B, ≈13.0 GiB peak RSS. | The 608-row argument required injectivity over every possible secret; a frozen registry needs only separation of the 64 registered ones. | — (reported: 154 bound checks, 27 consistency checks, 86 ML-DSA signatures accepted and 86 wrong-seat substitutions rejected; artifacts are absent) | — |
| v1.21 | 2026-09-09 | `docs/size-path-resolution.md` | Quantified kill/keep across the three blockers. Reproduced arithmetic: 0.0737 B/gate; 50,384-byte prefix obstruction; 662 B/seat; only "Mode S" (GKR linear layer + native hash + lattice signature-of-knowledge) survives. Several verdicts rest on estimates, which this document itself labels. | Bounds the search space after v1.20's measurements. | — | — |
| v1.22, v1.23 | — | **not in this tree** | v1.22 (reported): a user-only credential bound to the same hidden seat, +1.39 % gates, two 43-seat frames of 727,792 and 735,152 B. v1.23 (reported): a "fusion" implementation with seven native proofs of the earlier hashed-challenge relation. | — | — | — |
| v1.24 | 2026-09-09 | `docs/32kib-contents-contract.md` | **Current revision of the sequence.** Contents-first certificate `QC = (context, {(L_j, Z_j)}, π_joint)` with a purpose-based allocation 208 + 5,504 + 27,056 bytes; the challenge hash is **removed** by interpreting the existing 64-byte message digest directly as a field element of `GF(2)[x]/(x⁵¹²+x⁸+x⁵+x²+1)`; authorization becomes three independent hash credentials; a shared-selector relation over an odd prime field proves distinct seats by column occupancy; distributed generation by one MPC over 64 logical participants. | Choose what the certificate must contain before choosing a proof system. | — (reported: 44 reference and contract checks; artifact absent) | — |

### 3.4 Which version is current, and why

Two questions must be separated.

**The current revision of the sequence is v1.24** (`docs/32kib-contents-contract.md`). It is the last
version written (9 September 2026), it is the only revision that fixes the certificate's byte
allocation by purpose, and every subsequent step in the programme implements *its* relation
(`../03-zk-carrier-experiments` builds the v1.24 relation natively as `CEQS124_DIRECT_CHALLENGE`).
The map marks it "current revision (v1.24)".

**A reader looking for a security theorem must not use v1.24.** v1.24 is a specification with a
reference test; it contains no theorem. The strongest theorem in the sequence remains v1.3
(conditional, conditional on nine named assumptions) with the v1.4 §1 correction, and no version
after v1.4 re-proves it for the executed parameterization. Six further lineages each have their own
current revision, as the map records:

| Lineage | Current revision | File |
|---|---|---|
| hidden-signer theorem, non-interactive mode | v1.3 | `docs/qpt-crs-security-proof.md` |
| hidden-signer theorem, collaborative mode | v1.4 | `docs/collaborative-quorum-proof.md` |
| backend eligibility | v1.6 | `docs/backend-eligibility-proof.md` |
| research qualification | v1.18 | `docs/research-qualification.md` |
| blocker resolution | v1.20 | `docs/blocker-resolution.md` |
| size path | v1.21 | `docs/size-path-resolution.md` |
| certificate contents | v1.24 | `docs/32kib-contents-contract.md` |
| validation and continuation | v0.8 | `docs/validation-and-continuation.md` |
| each checker | its highest version | `src/` (the current script drops the version suffix) |

**No version of this construction has ever produced a valid full certificate.** That statement is
made by the sources themselves at v1.18, v1.19 and v1.20, and nothing later contradicts it.

### 3.5 Version numbers with no document in this repository

v1.2, v1.5 (main proof document), v1.7–v1.17, v1.22 and v1.23 have no file here. They are recorded
in the ladder above from what later versions and the research journal say about them, and they are
labelled as reported. No claim in this domain rests on a missing document.

---

## 4. What this domain proves, and what it does not

**Established by exhaustive computation or exact arithmetic** (re-runnable from `src/`):

- Quorum-family coverage and the `2q − n` intersection bound (`src/ce_qs_quorum_family_checker.py`);
- the bitmap policy equivalence `f_B(z) = 1 ⇔ supp(B) ⊆ supp(z)` (`src/ce_qs_bitmap_policy_checker.py`);
- honest-majority density in any 43-quorum (`src/ce_qs_collaborative_quorum_checker.py`);
- the byte-gate arithmetic and the eligibility decision logic (`src/ce_qs_backend_eligibility_checker.py`);
- the CET extraction algebra and its failure modes, at the level of a mock relation
  (`src/ce_qs_relation_mock.py`, `src/ce_qs_relation_mock_ext.py`, `src/ce_qs_trace_tag_simulator.py`,
  `src/ce_qs_distributed_certified_tag_checker.py`, `src/ce_qs_strong_conflict_handle_checker.py`,
  `src/ce_qs_private_wrapper_relation_checker.py`, `src/ce_qs_qpt_crs_structural_checker.py`).

**Established as conditional theorems over abstract primitives:** the v0.5–v1.4 reductions. Every
bound is in terms of unnamed advantages (`ε_PRF`, `ε_ZK`, `ε_QLWR`, …). No primitive is instantiated,
no proof system is built, and no machine-checked proof exists anywhere in this domain.

**Not established, in any version:** a compact (<32 KiB) certificate; authorization inside the
proof (0 ML-DSA constraints in every executed circuit, by the sources' own measurement); a
distributed prover; a QPT-128 loss budget with concrete constants; the anonymity admissibility
condition (v1.3 → v1.4 correction; the same wording recurs at v0.6 and v0.9); and any measured
CE-QS proof size.

---

## 5. Files in this domain

Seventy-three files in total: 62 copied source files and 11 written for this repository.

| Directory | Files | What they are |
|---|---:|---|
| `docs/` | 29 | **copied** — current revisions of the construction, proof, qualification and review documents, plus the per-version ledgers and validation records |
| `docs/` | 9 | **authored** — `docs/construction-end-to-end.md` and `inflections/01…08` |
| `results/` | 14 | copied — the recorded `*_results.txt` of each checker and the three release checksum records |
| `src/` | 11 | copied — the current checker scripts (highest version of each, version suffix dropped) |
| `history/` | 8 | copied — superseded construction documents and the superseded v0.1 checker with its result |
| root | 2 | authored — `README.md`, `VERIFICATION.md` |

### 5.1 Source filename → repository path

Copied documents refer to each other by their original research-tree filenames. Those names are
**not** rewritten in the copies (six of them carry a mandated one-phrase rewrite and nothing else;
see §2 above); resolve them with this table.

| Original name | Repository path |
|---|---|
| `PQ_CE_QS_frontier_v0.1.md` | `docs/frontier.md` |
| `PQ_CE_QS_finalized_construction_v0.3.md` | `docs/finalized-construction.md` |
| `PQ_CE_QS_research_synthesis_final_v0.4.md` | `docs/research-synthesis-final.md` |
| `PQ_CE_QS_v0.4_source_qualification_ledger.md` | `docs/source-qualification-ledger-v0.4.md` |
| `PQ_CE_QS_v0_4_validation_and_corrections.md` | `history/validation-and-continuation-v0.4.md` |
| `PQ_CE_QS_validation_and_continuation_v0_2.md` | `history/validation-and-continuation-v0.2.md` |
| `PQ_CE_QS_validation_and_continuation_v0_3.md` | `history/validation-and-continuation-v0.3.md` |
| `PQ_CE_QS_v0_5_validation_and_continuation.md` | `history/validation-and-continuation-v0.5.md` |
| `PQ_CE_QS_v0_6_validation_and_continuation.md` | `history/validation-and-continuation-v0.6.md` |
| `PQ_CE_QS_v0_8_validation_and_continuation.md` | `docs/validation-and-continuation.md` |
| `PQ_CE_QS_formal_proof_stack_v0.5.md` | `docs/formal-proof-stack.md` |
| `PQ_CE_QS_v0.5_proof_corrections.md` | `docs/proof-corrections-v0.5.md` |
| `PQ_CE_QS_exact_aggregator_lifting_proof_v0.6.md` | `docs/exact-aggregator-lifting-proof.md` |
| `PQ_CE_QS_v0.6_CTRS_adapter_obligations.md` | `docs/ctrs-adapter-obligations-v0.6.md` |
| `PQ_CE_QS_quorum_family_privacy_fork_proof_v0.7.md` | `docs/quorum-family-privacy-fork-proof.md` |
| `PQ_CE_QS_public_signer_theoretical_completion_v0.8.md` | `docs/public-signer-theoretical-completion.md` |
| `PQ_CE_QS_v0.8_SHA256SUMS.txt` | `results/sha256sums-v0.8.txt` |
| `PQ_CE_QS_quantum_lift_private_wrapper_proof_v0.9.md` | `docs/quantum-lift-private-wrapper-proof.md` |
| `PQ_CE_QS_v0.9_QPT_assumption_ledger.md` | `docs/qpt-assumption-ledger-v0.9.md` |
| `PQ_CE_QS_distributed_certified_tag_proof_v1.0.md` | `docs/distributed-certified-tag-proof.md` |
| `PQ_CE_QS_v1.0_assumption_ledger.md` | `docs/assumption-ledger-v1.0.md` |
| `PQ_CE_QS_v1.0_SHA256SUMS.txt` | `results/sha256sums-v1.0.txt` |
| `PQ_CE_QS_strong_certified_conflict_handle_proof_v1.1.md` | `docs/strong-certified-conflict-handle-proof.md` |
| `PQ_CE_QS_v1.1_source_assumption_ledger.md` | `docs/source-assumption-ledger-v1.1.md` |
| `PQ_CE_QS_v1.1_SHA256SUMS.txt` | `results/sha256sums-v1.1.txt` |
| `PQ_CE_QS_QPT_CRS_security_proof_v1.3.md` | `docs/qpt-crs-security-proof.md` |
| `PQ_CE_QS_v1.3_QPT_source_ledger.md` | `docs/qpt-source-ledger-v1.3.md` |
| `PQ_CE_QS_collaborative_quorum_proof_v1.4.md` | `docs/collaborative-quorum-proof.md` |
| `PQ_CE_QS_v1.4_source_architecture_ledger.md` | `docs/source-architecture-ledger-v1.4.md` |
| `PQ_CE_QS_v1.5_compactness_source_ledger.md` | `docs/compactness-source-ledger-v1.5.md` |
| `PQ_CE_QS_backend_eligibility_proof_v1.6.md` | `docs/backend-eligibility-proof.md` |
| `PQ_CE_QS_research_qualification_v1.18.md` | `docs/research-qualification.md` |
| `PQ_CE_QS_adversarial_alt_strategy_v1.md` | `docs/adversarial-alt-strategy.md` |
| `PQ_CE_QS_blocker_resolution_v1.19.md` | `history/blocker-resolution-v1.19.md` |
| `PQ_CE_QS_blocker_resolution_v1.19.txt` | not copied (byte-identical duplicate of the above) |
| `PQ_CE_QS_multitrack_verification_v1_20.md` | `docs/multitrack-verification.md` |
| `PQ_CE_QS_blocker_resolution_v1.20.md` | `docs/blocker-resolution.md` |
| `PQ_CE_QS_size_path_resolution_v1.21.md` | `docs/size-path-resolution.md` |
| `PQ_CE_QS_32KiB_contents_contract_v1.24.md` | `docs/32kib-contents-contract.md` |
| `ce_qs_trace_tag_simulator_v0.1.py` / `_results.txt` | `history/ce_qs_trace_tag_simulator-v0.1.py` / `.txt` |
| `ce_qs_trace_tag_simulator_v0_2.py` / `_results.txt` | `src/ce_qs_trace_tag_simulator.py` / `results/ce_qs_trace_tag_simulator.txt` |
| `ce_qs_relation_mock_v0.3.py` / `_results.txt` | `src/ce_qs_relation_mock.py` / `results/ce_qs_relation_mock.txt` |
| `ce_qs_relation_mock_v0_3_ext.py` / `_results.txt` | `src/ce_qs_relation_mock_ext.py` / `results/ce_qs_relation_mock_ext.txt` |
| `ce_qs_quorum_family_checker_v0.7.py` / `_results.txt` | `src/ce_qs_quorum_family_checker.py` / `results/ce_qs_quorum_family_checker.txt` |
| `ce_qs_bitmap_policy_checker_v0.8.py` / `_results.txt` | `src/ce_qs_bitmap_policy_checker.py` / `results/ce_qs_bitmap_policy_checker.txt` |
| `ce_qs_private_wrapper_relation_checker_v0.9.py` / `_results.txt` | `src/ce_qs_private_wrapper_relation_checker.py` / `results/ce_qs_private_wrapper_relation_checker.txt` |
| `ce_qs_distributed_certified_tag_checker_v1.0.py` / `_results.txt` | `src/ce_qs_distributed_certified_tag_checker.py` / `results/ce_qs_distributed_certified_tag_checker.txt` |
| `ce_qs_strong_conflict_handle_checker_v1.1.py` / `_results.txt` | `src/ce_qs_strong_conflict_handle_checker.py` / `results/ce_qs_strong_conflict_handle_checker.txt` |
| `ce_qs_qpt_crs_structural_checker_v1.3.py` / `_results.txt` | `src/ce_qs_qpt_crs_structural_checker.py` / `results/ce_qs_qpt_crs_structural_checker.txt` |
| `ce_qs_collaborative_quorum_checker_v1.4.py` / `_results.txt` | `src/ce_qs_collaborative_quorum_checker.py` / `results/ce_qs_collaborative_quorum_checker.txt` |
| `ce_qs_backend_eligibility_checker_v1.6.py` / `_results.txt` | `src/ce_qs_backend_eligibility_checker.py` / `results/ce_qs_backend_eligibility_checker.txt` |

Because the copies are byte-identical, a document that says `PQ_CE_QS_frontier_v0_1.md` means
`docs/frontier.md`, and a checker docstring that names `PQ_CE_QS_formal_proof_stack_v0.5.md` means
`docs/formal-proof-stack.md`.

---

## 6. Running the checkers

Every checker in `src/` is a single self-contained Python file that imports only the standard
library, reads no input and writes no output. Run from this directory:

```
for f in src/*.py; do python3 "$f"; done
```

Each script's stdout is compared byte-for-byte with the matching file in `results/`. The record of
that comparison, with commands, timings and the one discrepancy, is in `VERIFICATION.md`.

The superseded v0.1 simulator is kept in `history/` with its version in the filename and its own
recorded result next to it. It is **not deterministic**: one line reports the minimum quorum
intersection observed over 50 random trials and varies between 24, 25 and 26. See
`VERIFICATION.md` §2.

---

## 7. Where to go next

- The construction explained end to end at its current revision: `docs/construction-end-to-end.md`.
- The turning points, one document each:
  1. `docs/inflections/01-elba-impossibility-retracted.md` — v0.4 → v0.5: an impossibility claim
     withdrawn, and the obstacle relocated from theory to size.
  2. `docs/inflections/02-exact-aggregator-and-privacy-fork.md` — v0.5 → v0.7: exactness becomes a
     named adapter property, and the target splits into public and hidden signers.
  3. `docs/inflections/03-public-signer-completion-and-private-wrapper.md` — v0.8 → v0.9: both halves
     of the fork reduced to a named primitive.
  4. `docs/inflections/04-central-prover-rejected-and-conflict-handles.md` — v0.9 → v1.1: the
     single-prover wrapper rejected as unbuildable, and the trace abstraction given games.
  5. `docs/inflections/05-random-oracles-removed-and-anonymity-hybrid.md` — v1.2 → v1.4: the random
     oracle leaves the load-bearing theorem, and an over-strong anonymity hybrid is repaired.
  6. `docs/inflections/06-from-property-checklist-to-joint-construction.md` — v1.5/v1.6 → v1.18:
     every candidate backend fails an eight-property test, and a size floor ends the search.
  7. `docs/inflections/07-review-adjudication-and-frozen-registry.md` — v1.18 → v1.20: four review
     inferences corrected, and 608 link rows become 176 under a setup condition.
  8. `docs/inflections/08-contents-first-and-injective-challenge.md` — v1.21 → v1.24: the certificate
     contents are fixed before the proof system, and the challenge hash is removed.
- What reproduces and what does not: `VERIFICATION.md`.
- The sibling domains: `../01-accountable-quorum-foundations` (the target and the quorum
  arithmetic), `../03-zk-carrier-experiments` (the proof-system experiments that implement the
  current relation), `../06-qpt128-security-target` (the gate-work-factor definition of the 128-bit
  requirement), `../07-compact-certificate-b0` (the later public-signer certificate), and
  `../08-hidden-signers` (the continuation of the hidden-signer track).
- The research journal records the design history that the missing v1.7–v1.17 documents carried;
  this domain cites it only as reported material.
