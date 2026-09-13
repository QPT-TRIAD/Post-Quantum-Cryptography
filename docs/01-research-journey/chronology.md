# Chronology

The sequence of the research that produced the CE-QS construction and the QPT-128 security target, as
the two trail transcripts record it, followed by the downstream corrections that changed what the
target means.

This document is a record. Where a claim made at some point on the trail was later refuted, the claim
is stated as it was made, and the refutation is stated next to it with the date or version that
produced it. No entry has been edited to agree with a later finding, and the register of reversals in
§IX is part of the chronology rather than an appendix to it. The standing value of every number here
lives in `records/verification-findings.md` and in the domain that owns the claim.

Pointers are `PS:<line>`, `PS2:<line>`, `PQT:<line>` and `TM:<line>`; see `README.md` for what those
texts are and why `PS`, `PS2` and `TM` are not in this repository. Version numbers such as `v1.42`
are the project's own document versions; §XI records which of them survive as files here and which
exist only as transcript prose.

---

## I. The sequence at a glance

| Phase | Trail span | Question | Outcome |
|---|---|---|---|
| 0 | PS:3–15 | Is the BFT design's stated weakness — per-seat ML-DSA votes, quorum certificates that grow with the committee — a real gap? | Premise accepted; a prior-art search is opened |
| I | PS:9–455 | Is "aggregatable PQ signatures for BFT quorums" unsolved, and what is the most credible novel angle? | A lower bound reframes the problem; the target becomes *conflict-extractable PQ quorum signatures*. No proof exists yet |
| II | PS:457–2412 | Produce the formal security proof | AQUA-QC v0.1 and a reference-free rewrite; first external review returns six work streams |
| III | PS:2416–5544 | Concrete profile, literature corrections, epoch seams | v0.2–v0.5; profile PQ-AQC-64/128 frozen at 64 seats, ML-DSA-65, 384-bit commitments; four external reviews |
| IV | PS:5546–5802 | Research record and formal-methods track | v0.5–v0.8; an exhaustive checker; five formal-methods overclaims found by review and repaired |
| V | PS:5804–6224 | Sidecar-free construction ("Target B") | A secret-quorum-sample construction with a counting theorem; the naive trace-tag rule is refuted by counterexample |
| VI | PS2:1–474 | Fit a hidden-signer conflict-extractable certificate into 32 KiB | v1.7–v1.29; seven distinct approaches abandoned; no accepted full quorum certificate; the decisive obstruction named |
| VII | PS2:476–1489, PQT:1583–1956 | Put QPT-128 on a mathematical footing | v1.30–v1.42; five refutations of pasted claims; conditional bounds only |
| VIII | PS2:1491–3342, PQT:1–1560 | State the total QPT-128 theorem | A conditional six-row theorem at `2^-131` per row; the report's own status verdicts |
| IX | outside the trails | What happened to those conclusions | The `Adv < 2^-128` target refuted by Lemma L1; target redefined as a gate work factor; two reversals owned by other domains |

---

## II. Phase 0 — the starting problem (PS:3–15)

The trail opens with an owner request (PS:3) about a BFT design document that is not itself in the
tree. The research step reports that it could not locate the document (PS:15). The request quotes the
document's self-declared weakness: individual ML-DSA votes, no aggregation, and quorum certificates
that grow with committee size, contrasted with classical BLS aggregation. It asks for a prior-art
search against HotStuff, Jolteon, Fast-HotStuff, DiemBFT/LibraBFT, Narwhal-Bullshark, Tendermint and
recent post-quantum BFT work.

Later external review input identifies the design document as belonging to the TRIAD blockchain: it
refers to "TRIAD's own design (per your earlier document) … seat-based, one-vote-per-seat" (PS:2412).
The devnet test plan records the ratified set as 64 validators, 21 faults, 43 quorum, with a
`QuorumCertificateV1` carrying a 64-bit signer bitmap plus raw per-seat ML-DSA signatures (TM:45–46).
Those numbers are the origin of `(N, F, Q) = (64, 21, 43)` that the whole programme later uses. No
TRIAD material is copied into this repository; the facts above are recorded here only as the problem
statement the research started from.

Also in this phase, and declared non-cryptographic: an operator monograph, a thesis and a preon
document (PS:15, PS:347, PS:479), and a set of named research methods (Genesis table, GLYPH,
MORPH/LEXON, NEXUS, SEMA, DISCOURSE/PRAGMA, CLOSURE/GENERATE, RIFT, GRAIL, QMC, and a family of
quantum variants). The trail states plainly that "none of them is a cryptographic assumption"
(PS:323). One of them produced a correction that survives: an uploaded QMC routine's claim that its
bases are algebraically independent is false, because φ and √5 satisfy 2φ − √5 − 1 = 0 (PS:381–389),
and deterministic QMC points must never generate keys, masks, nonces or salts (PS:391).

---

## III. Phase I — prior art and the birth of the target (PS:9–455)

### III-a. Verdict on the premise

The premise was half right. As an external-literature report: PQ multisignatures and threshold
signatures already exist — Squirrel, Chipmunk and Lemur for synchronized lattice multisignatures;
Threshold Raccoon, Ringtail, Olingo, Tanuki, Hermine and Mithril for lattice threshold; and a NIST
multi-party threshold call opened in January 2026 (PS:21). What is *not* solved is the conjunction:
post-quantum security, BLS-like compactness, independent or distributed keys, one online round, large
dynamic committees, weighted predicates, public accountability, adaptive corruption and refresh, and
fast aggregation (PS:23–25). A July 2026 Distributed Quorum Signatures paper reaches the same
conclusion (PS:27).

### III-b. The lower bound that reframed the objective (PS:75–115)

**Statement as used.** A self-contained lossless encoding of the exact signer set needs at least
⌈log₂ C(n,t)⌉ bits (PS:83). Label: theorem-with-proof, by counting.

**Why it mattered.** At n = 1000, t = 667 the bound is ≈ 912.74 bits ≈ 114.1 B, against a 125-byte
bitmap — so a bitmap is nearly optimal for moderate committees (PS:93–95). At n = 10⁶,
t = 666,667 the same count gives ≈ 918,285 bits (PS:99, where the figure is written "114.8 KiB";
see §X for the unit slip). The conclusion drawn: "A constant-size, self-contained certificate cannot
also reveal an arbitrary exact signer set as n→∞" (PS:103).

**The three escapes** (PS:107–109): a threshold key that hides the set; attribution made outside the
certificate; or weakened attribution. The third escape is the one the programme took, and it is the
first appearance of the concept that defines everything after it: **conflict-extractable
post-quantum quorum signatures** (PS:115).

### III-c. The engineering answer, and the admission

A "RIFT" elimination filter (PS:121–127, exclusion rules at PS:365) excluded anything over 16 KB from
the hot path, anything needing more than one online round, anything with no signer evidence, and
anything without DKG or refresh. Ringtail survived most of it, and the chosen architecture —
**AQUA-QC = Accountable QUAntum-safe Quorum Certificate** (PS:127–133) — was a Ringtail/Tanuki/
Hermine-class compact threshold core plus deferred, independently verifiable accountability evidence:
per-epoch DKG, n = 3f+1, t = 2f+1, a canonical vote digest, ML-DSA identity receipts, a hot-path
FastQC of roughly 13–14 KB (PS:183), a Merkle accountability sidecar E_j with root C_j, and deferred
binding through the successor QC (SQC_j = (FQC_j, C_j, FQC_{j+1})). Prior art is admitted rather than
claimed: IA-CCF Merkle receipts (PS:197).

The trail stated the proof gap at the time: "A complete security proof does not yet exist" (PS:237),
and listed the obligations, the central one being the quorum-intersection identity |S₀ ∩ S₁| ≥ f+1
(PS:257).

### III-d. The stronger target and the honest boundary

The stronger cryptographic target, CE-QC (PS:271–317), was given seven algorithms (DKG, Preprocess,
ShareSign, Combine, Verify, Blame, VerifyBlame) and six properties (completeness, soundness or
non-frameability, unforgeability, privacy, robustness, refreshability) — the list that CE-QS
eventually implements. The unsolved component was named then: committing the trace tags without an
O(n) certificate (PS:313).

**Phase I closes with a conjecture, not a result.** "It remains unproved that such a primitive can be
made simultaneously compact, practical, post-quantum secure, non-frameable, one-round online, and
robust" (PS:455). Label: conjecture / open problem. The rest of the trail is the attempt to reduce
that conjecture to something provable, and the record of where the reductions stopped.

---

## IV. Phase II — AQUA-QC v0.1, the reference-free rewrite, and the first external review (PS:457–2412)

**II-a. AQUA-QC v0.1** (PS:463–1468), labelled theorem-with-proof and explicitly "paper-level,
game-based reduction proof … not yet machine-checked in EasyCrypt, Coq, TLA+" (PS:469). It states at
the outset that it does **not** prove the compact-certificate primitive (PS:475).

Contents, in the order they appear: the model (n = 3f+1, t = 2f+1, QPT adversary, static corruption
within an epoch at PS:493, partial synchrony at PS:495); primitives TS, IS = ML-DSA with multi-user
qEUF-CMA, an injective encoding, domain-separated hashes with Merkle 0x00/0x01 prefixes and a length
commitment, and an availability interface Put/Get; the honest vote algorithm with atomic persist
(PS:632–669); FastQC F = (M, σ) (PS:687); the sidecar and VerifyEvidence (PS:701–727); the anchor
A(F,C) and Q = (F, C, F⁺) (PS:735–767); four bad events BadT, BadI, BadH, BadA (PS:775–806); six
lemmas L1–L6, of which **L6 is the quorum-intersection argument and needs no cryptographic
assumption** (PS:996–1010); six theorems T1–T6, T4 being safety preservation by projection onto
base-protocol executions (PS:1142–1211); and a composition step carrying the warning that a
classical-ROM threshold proof is not automatically a QROM proof (PS:1298–1329).

**A correction inside the phase.** The Phase I vote digest placed a signer-specific preprocessing
identifier inside the common message m_j (PS:155). v0.1 corrects this: a signer-specific
preprocessing identifier must not be in the common message (PS:614).

**What v0.1 lists as unproved** (PS:1408–1444): no compact CE-QC; no internal proof for the threshold
scheme; no adaptive-corruption proof; no side-channel proof; no implementation proof.

**II-b. The reference-free rewrite** (PS:1478–2396) strips external references and the earlier method
vocabulary. It keeps the same architecture under the labels PQ-QC-V1 / PQ-EVID-V1 /
PQ-EVID-ANCHOR-V1, adds the requirement that the storage write must precede either signature becoming
visible (PS:1652), and reaches the same conclusion — "the earlier conclusion does survive a
standalone cryptographic derivation" (PS:2396) — while stating its own boundary: "this construction
has **not** solved the stronger problem: two compact PQ threshold signatures → extract a conflicting
signer" (PS:2329–2347).

**II-c. External review input #1** (PS:2400–2412). Its calibration is worth recording because it
shaped all later work: the reduction structure is sound, but sections 14 and 16 are pure
quorum-intersection arguments that apply verbatim to classical BLS, so the post-quantum-specific
content is narrow. Six work streams follow — pin the threshold scheme and treat DKG as the biggest
gap; concrete parameters with the Lattice Estimator; invalid-share denial of service, preprocessing
exhaustion and evidence censorship; decide static versus adaptive corruption; mechanise the
reductions; and specify canonical encoding with differential fuzzing — sequenced
WS1 → WS2 → WS6 → WS3 → WS4 → WS5. It also asserted that Ringtail rests on "Algebraic One-More
Module-LWE". That assertion was corrected in the next phase.

---

## V. Phase III — concrete profile, literature corrections, epoch seams (PS:2416–5544)

### V-a. Corrections of the review, and of the corrections

- **Correction (v0.2, PS:2420).** Ringtail's published 2025 result rests on standard LWE in the
  random-oracle model, not on a new AOM-MLWE assumption, but it assumes trusted key generation.
- **Hermine** was identified as the closer fit for a committee capped at 64: N ≤ 64, DKG, a single
  online round, non-interactive identifiable abort, proactive refresh, ≈ 11 KB (PS:2420). Its venue
  was claimed as a forthcoming AsiaCrypt 2026 paper; disputed in review #2 (PS:3012), treated as
  forthcoming metadata after IBM's listing (PS:3046).
- **Correction of the review (v0.3, PS:3038–3042).** Hermine is standard MLWE/MSIS, with AOM-MISIS as
  an intermediate proof problem; the NIST slides use "AOM-MSIS". The naming wobble was raised again
  in review #5 (PS:5560) and settled in v0.6 (PS:5605): AOM-MISIS is the technical term, AOM-MSIS is
  presentation terminology.
- **Source mismatch (v0.3, PS:3044).** The NIST preview advertises DKG, but the ePrint assumes
  trusted key generation and leaves the Vandermonde DKG analysis to future work. Review #3 sharpened
  this: the ePrint calls DKG results "orthogonal" and cites ePrint 2025/871, so it is "an
  acknowledged proof gap" rather than a design choice (PS:3741).
- **The `ts-suf-2` question, reversed twice.** Review #4 could not confirm "TS-suf-2" and pointed at
  the Bellare et al. hierarchy TS-UF-0..4 (PS:4558). v0.5 then reported that the ePrint's
  Definition 3.2 defines `ts-suf-2` and its Theorem 6.4 states the scheme is `ts-suf-2` under MSIS +
  AOM-MISIS, while the introduction says TS-UF-2 (PS:4594). Review #5 said TS-suf-2 is wrong. v0.6
  found the correction "went the opposite way from the proposed change": the introduction says
  TS-UF-2, the formal Definition 3.2 defines `ts-suf-2`, Theorem 6.4 states `ts-suf-2`. **Both facts
  are recorded** (PS:5605). This is the trail's clearest example of a paper's own internal
  inconsistency, and the record keeps both readings rather than choosing one.

### V-b. The profile decisions

Narrowing the system (PS:2428–2440): N ≤ 64, equal weights, a fixed committee per epoch, a fresh DKG
per epoch, static corruption, no refresh. The trail does not give a deeper reason for 64 than
Hermine's N ≤ 64 profile (PS:2420). The assumption ledger is five entries: ML-DSA evidence, SHAKE256,
single-use crash-persistent preprocessing, full sidecar retention, equal seats (PS:2448–2464).

Silence is never blame: non-response is a timeout, and only a signed invalid share is blame
(PS:2622–2664). Commitments are 384 bits, because a generic quantum collision search costs about
2^(m/3) and 2^(384/3) = 2^128 (PS:2740–2768). Availability is provided without erasure coding
(PS:2772–2802). Multi-user loss is N_u ≤ 64E, and the evidence signature is changed from ML-DSA-44 to
ML-DSA-65 (PS:2832–2850, PS:3197–3203).

### V-c. The multi-user budget, and the one number that survives to the end

Labelled model-or-ledger estimate and explicitly "security-budget screening, not a substitute for the
concrete ML-DSA reduction" (PS:3221). For daily epochs over ten years (E = 3,650) the loss is
log₂(64E) ≈ 17.83 bits, giving κ_SU ≳ 145.8 bits at `2^-128`, 150.4 for hourly epochs, 153.9 for 10⁶
epochs; at a `2^-140` budget, 157.8 and 162.4. The reference profile frozen at v0.6 is 64 validators,
daily epochs, a ten-year life and ML-DSA-65, giving 3,653 epochs, 233,792 keys, 17.835 bits of loss, a
157.835-bit single-user target at `2^-140`, and a ≈ 139 KiB sidecar (PS:5607). Review #6 recomputed
each of these independently and got the same values (PS:5628), which is why this row is one of the
few in the whole campaign to have been checked twice by different parties.

### V-d. Epoch closure and the density of the argument (v0.4, PS:3774–4550)

The decision that shapes the rest: an epoch may change only at an already-finalized checkpoint
(PS:3806), on the strength of machine-checked HotStuff-family work that proves a single configuration
only (arXiv 2203.14711, PS:3802). From it come the terminal height and the EpochClose block, the
accountability frontier a_e = H_end − 1, the Open→Sealed transition, and the **seal-quorum theorem**:
at most f+1 honest parties have sealed, so at most 2f can vote, which is fewer than the 2f+1 a quorum
needs (PS:3912–3948). Old votes are rendered inert rather than erased. `Carry_e` is defined, its
sufficiency, completeness, boundary uniqueness, activation and cross-epoch safety are argued, and the
whole is closed by induction over epochs (PS:4004–4248). Eight invariants I1–I8 and five crash points
are named as the mechanisation target (PS:4412–4448).

### V-e. The formal-methods episode: five overclaims, found and fixed

v0.5 reports TLC/TLAPS as unavailable in the research environment, so the model is not claimed as
checked (PS:5417–5442). Review #6 then re-ran the independent exhaustive checker, reproduced its
numbers, and refuted five formal-methods claims (PS:5642–5662):

1. the prose names invariants that are absent from the `.tla`, which has TypeOK plus eight;
2. boundary uniqueness is assumed by representation, a single scalar `finalizedBoundary`;
3. `Crash == UNCHANGED vars` is a stutter step, not a crash;
4. `Preps`/`Domains`/`Epochs` are dead constants, so `VoteOnce` means "one vote ever";
5. `partition_recovery()` is hard-coded set arithmetic.

v0.7 repairs all five, adds competing boundary certificates with the invariant |FinalityCerts| ≤ 1, a
volatile/durable crash model, domain-indexed votes, and **negative controls** — a run with the domain
guard removed, a run in which an honest boundary double-vote yields QC(B₀) ∧ QC(B₁), and a
send-before-persist crash trace (PS:5666–5733). The results are recorded as pass counts over
reachable states, 729/2,916; 140/400; 23,474/127,006; 28/55; 1,440/8,592, with thirteen configuration
invariants matched. Review #7 re-ran v0.7, confirmed the repairs, and noted two residual defects: the
`.tla`/`.cfg` files were not in the upload, and there was no consistency check in the checker script
(PS:5735–5763). v0.8 adds the `.tla`/`.cfg`, an auditor, thirteen invariants and a SHA-256 manifest,
and still claims only that "native TLC/TLAPS and implementation refinement are still pending"
(PS:5802). **None of the v0.8 artefacts are in the tree**, and the v0.7 `.tla`/`.cfg` are missing too.

---

## VI. Phase V — the pivot to "without a sidecar" (PS:5804–6224)

An uploaded memo defines the two targets (PS:5806). **Target A** is the compact hot-path QC plus an
external sidecar, which v0.8 had produced. **Target B** is "a compact post-quantum quorum signature
from which a conflicting signer can be extracted directly from two conflicting compact certificates,
without retrieving an O(n)-scale accountability sidecar". The owner asks for Target B, "learn from
v0.8 borrow school of thought from different research papers broad search that qualify and link the
missing link" (PS:5808), and links the Distributed Quorum Signatures paper, arXiv 2607.17700
(PS:5812).

The construction attempted is **conflict-triggered disclosure of a secret quorum sample**. DQS changes
communication rather than building a compact aggregate (PS:5834); DAPS/PAPS supply the
conditional-disclosure pattern (PS:5842); traceable ring signatures, accountable threshold ring
signatures, lattice TAPS and QROM proof systems each fill only part of the need (PS:5846–5855).

**The first dead end of this phase is a refutation, not a design.** Naive aggregated trace tags
z_i(h) = a_i + h·u_i fail after aggregation over different quorums, because the masks do not match:
a small-field example gives divided difference 41 against true tokens 3 and 13 (PS:5863–5885). The
trail states the scope of the refutation itself — "This disproves that particular naive extraction
rule—not every possible trace-tag construction."

**The "missing link" is a counting theorem.** With K the number of authorized requests per domain,
K ≤ ⌊(n−c)/(q−c)⌋, and 3q > n + 2c implies K ≤ 2 (PS:5919–5943). For n = 64, q = 43 it holds for
c ≤ 32, so the non-vacuous window is 22 ≤ c ≤ 32 (PS:5945–5967). The certificate is
σ = (C_S, Y_r, Y_K, ν, Z_S, π), with disclosure values Y = a_d + h·r_d recoverable from two challenges
and π a zero-knowledge argument of knowledge (PS:6006–6054). The core operational rule: "the
collector must not learn r_d before the two committed quorums are fixed" (PS:6088).

**Where the size argument fails.** The bound in the ideal private-generation model is
Pr ≤ (1 − (2q−n)/n)^L (PS:6092–6114), with L = ⌈(λ + log₂ Q_d)/(−log₂(1−γ))⌉. At γ = 22/64 that is
L = 211 for `2^-128` in a single domain, and L = 264 for 2³² domains, i.e. 33 bytes. The trail draws
the conclusion against its own hope: "That is not a 33-byte signature" (PS:6116–6140). The verifier
sees |σ| = O(λ+L) + |π(λ,n)|, so compactness needs |π| = poly(λ, log n) — which is the same missing
proof backend as before (PS:6144–6160).

The phase's tests are toy algebra and combinatorics — 78,608 interpolation cases over F₁₇, 289 masking
tables, 4,096 and 151,263 sampling combinations, four negative controls — and the trail says so: "no
real PQ signatures, MPC, NIZK, AEAD, DKG, cryptographic sampler" (PS:6162–6186). Four boundaries are
recorded (PS:6202–6210): restricted corruption; private generation essential; proof backend
uninstantiated; efficiency unmeasured. The phase ends with an explicit negative: "not yet the
unrestricted, fully instantiated compact PQ quorum signature requested by Target B" (PS:6220).

**A chronology gap, stated as a gap.** `PS` ends here; `PS2` begins at CE-QS v1.6 → v1.7. The CE-QS
versions v0.1–v1.6 exist only as files elsewhere in the tree. This is the one place where the
chronology cannot be reconstructed from the trail, and it is recorded rather than smoothed over. A
related tension is unresolved in the record: a separate CE-QS frontier note of 2026-09-08 argues
against public sampled tags on the ground that "a malicious combiner can adapt the signer set to
public sampling randomness", and a companion note says that note superseded the earlier trace-tag
sketch. The D0 trails never record how the secret-sample route relates to the CE-QS v0.1–v1.6 line.

---

## VII. Phase VI — the CE-QS backend and the size campaign, v1.7 → v1.29 (PS2:1–474)

The second trail export is stamped "September 13th 2026, 3:42:04 pm" (PS2:1). Its standing question is
the one the rest of the programme inherits: fit a hidden-signer, publicly verifiable, sidecar-free,
43-of-64 conflict-extractable certificate into a hard 32 KiB = 32,768 B frame.

Two derivation facts a reader needs for the table. The 32 KiB cutoff is a project engineering
decision, set far below the ≈ 139 KiB raw evidence payload of Target A while leaving room for the
proof. The proof allowance is arithmetic: the first budget statement in the trail is at v1.9
(PS2:83), and the recorded derivation is 32,768 − 43·96 − 160 = 28,480 B; the v1.24 contents contract
replaces the 96-byte handle assumption and gives 208 + 5,504 + 27,056 = 32,768, i.e. 27,056 B for the
proof and 128 B per handle.

Unless a row says otherwise, every count and byte figure below is a measurement reported in the
transcript. The artefacts are mostly not in the tree (§XI).

| Ver. | Question asked | What was tried | What the tests returned | What was concluded or refuted |
|---|---|---|---|---|
| v1.7 | finalize the incomplete v1.6 items (PS2:15) | audit and corrections over 60 structural checks | 60 checks pass; the pinned proof-system source was inspected and its size output is an estimate — the build stopped at missing GMP headers (PS2:21–27) | the conditional proof is corrected to extract **22 distinct equivocators**; replacing all tracing material with ordinary zero-knowledge proofs is a "restricted obstruction"; blockers listed: conflict-handle construction, 43-signer implementation, measured bytes (PS2:30) |
| v1.8 | finalize the blockers (PS2:38) | build the pinned proof-system core | 2 synthetic proofs verified, **5 runs failed**; estimated ≈ 108 KiB with no serialized measurement (PS2:44–48) | a quorum-family liveness theorem and a conditional key-separation proof are added; the v1.3/v1.4 sources are missing and requested (PS2:55) |
| v1.9 | "finalize the blockers to we can celebrate" (PS2:77) | conflict handles, 9 uploads | **96-byte conflict handles**; 39 component checks (PS2:81) | ≤ 32 KiB unfinished: parameter qualification, compact backend, distributed proving (PS2:83) |
| v1.10 | solve the blockers | fix rounding bias; a private quorum relation over real ML-DSA-65 | 51 checks; recovers exactly 22 shared signers (PS2:96) | open: parameter qualification, **a public proof within 28,480 B**, distributed proving (PS2:98) |
| v1.11 | next blocker | a direct bit-circuit SmallWood adapter | optimistic proof floor **79,632 B > 28,480 B** (model-or-ledger estimate); hidden SHAKE compiled; 19 checks (PS2:111–113) | **adapter ruled out** — the floor is 2.8× the allowance before any real work |
| v1.12 | next blocker | a real zero-knowledge proof of all 43 link hashes | verifies in a fresh process from public inputs; 15 checks at 4 settings; smallest **328,672 B = 11.54× budget** (PS2:126–128) | compactness open |
| v1.13 | continue | rate and fold tuning of the current FRI query representation | the favourable relaxation still lands at **31,744 B > 28,480 B**; 34 checks (PS2:141–143) | **tuning ruled out for that representation** — it misses by 3,264 B |
| v1.14 | "different query-value encoding or proof protocol" | QVC1 encoding with public reconstruction | 328,672 → **267,472 B (−18.6%)**; 61 checks (PS2:156–160) | still over budget |
| v1.15 | "is the proof budget a hard blocker?" (PS2:168) | a 512 KiB experimental profile | a **269,648-byte self-contained frame** verified publicly with no sidecar; 38 checks (PS2:174–180) | **clarification of the record:** "The 32 KiB budget is enforced by the current QC format, but it is not a fundamental cryptographic limit" (PS2:172). The frame covers only the 43 link hashes (PS2:183) |
| v1.16 | finalize the blockers | trace binding for 43 contributors | single-contributor frame **506,848 B**; 43 checks; full-quorum proving exceeded the memory cap with witness buffers of **26.5 GiB** (PS2:197–201) | "No valid full QC has been produced" (PS2:204) |
| v1.17 | continue | the memory blocker | 2 proofs verify with an unchanged verifier at ≈ **16.9 GiB** peak; frames **776,736 and 785,456 B**; 22 trace identities recovered; 27 checks (PS2:218–220) | "Valid quorum certificates: zero" (PS2:220) |
| v1.18 | broad search, "school of thought" (PS2:229) | screen **32 papers** | recommends one joint lattice proof binding authorization, quorum membership and trace handles (LastRings + LaZer toolkit) as "a proposed research direction, not an established construction"; **restricted floor 50,496 B** for the current encoding; 34 checks (PS2:233–243) | query or path changes alone cannot reach 32 KiB (PS2:239) |
| v1.19 | read the uploaded document (PS2:252–254) | pool sizing, retries, binding | 46–50 candidates cannot guarantee 43 against 21 withholders while keeping all 64; retries ≤ **22** if each failure soundly identifies a fresh Byzantine; the seat index is already shared, and the missing piece is authorization verification inside the backend; 116 checks (PS2:260–267) | registration commitments do not replace in-proof authorization (PS2:264) |
| v1.20 | reconcile three uploads (PS2:275–281) | freeze registrations before sampling domain matrices | **−34.2% trace scalar products**; both trace proofs verified; smallest frame **722,528 B** against a 32,768 B budget (PS2:285–287) | a "corrected extraction theorem" (PS2:289); the size gap is ≈ 22× |
| v1.21 | Chinese and Japanese papers (PS2:300) | the fixed-opening premise | "distinct public links imply distinct seats"; duplicates already rejected; 41 checks (PS2:306–314) | 43 authorizations inside 28,480 B still open; "Accepted complete QCs: zero" (PS2:317) |
| v1.22 | use the Chinese and Japanese papers | bind a voting key and a trace key to the same hidden seat | +1.39% gates; two 43-seat frames verify; 22 synthetic identities after private-file removal; frames **727,792 and 735,152 B** (PS2:331–337) | the Chinese LAPQ-LRS aggregation uses one signer's key, so it does not establish 43 approvals; retaining the prefix blocks query-only compression; the change alters the authorization suite and leaves ML-DSA compatibility open (PS2:331–341) |
| — | owner: reverse-engineer the blockers, map variables to papers, fuse formulas, test a scenario (PS2:348) | — | no response block is recorded | — |
| v1.24 | **owner redirect: "instead of calculating size … analyze what has to be present in the 32Kib"** (PS2:354) | a contents contract | context **208 B** + 43 anonymous handles **5,504 B** + one joint proof **≤ 27,056 B** (PS2:360–364); the proof must show 43 distinct registered authorizers, three credentials bound per hidden seat, and the tracing equations (PS2:366); simplifications: message bytes treated as an injective field challenge, removing a challenge-hash collision assumption, and one private selector across three credential tables (PS2:370–372); 44 reference checks over 22 seats (PS2:377) | "A qualifying cryptographic proof for the reserved slot remains unconstructed" (PS2:377) |
| v1.25 | "build the cryptographic proof" (PS2:385) | a complete 43-seat relation prover | two experimental proofs verified independently; 22 identities recovered without witnesses or a sidecar (PS2:389) | 32 KiB, QPT-128 and distributed authorization all unresolved (PS2:391) |
| v1.26 | "solve" those three (PS2:402) | literature screen | LUNA's sub-6 KB proofs need a designated verifier; Hermine supports ≤ 64 parties but its signing does not bind tracing handles; the v1.25 prover lacks QPT-128 and exceeds the slot (PS2:408–412) | **the composition obstruction is named:** the missing object is "a compact, publicly verifiable proof binding all 43 authorizations to their conflict handles" (PS2:414) |
| v1.27 | continue | relation reduction | circuit **−55%**; 2 proofs verify; 22 identities; all **18 tampering checks** rejected; frames **279,600–283,680 B**; backend parameter 96-bit; centralized prover (PS2:424–432) | **finding: the queried field values alone are ≈ 80 KiB**, so the representation or the protocol must change (PS2:435) |
| v1.28 | "algorithms to be the carrier of information … reach 32Kib" (PS2:441) | carriers | no response block in the trail | — |
| v1.29 | ML-KEM and ML-DSA; Israeli and South Korean papers (PS2:451) | ML-KEM-1024 + ML-DSA-87 approval delivery | 51 checks; encrypted and authenticated approvals; 43 distinct signatures checked against the statement and the handles; 22 recovered; replay, substituted keys, altered statements and duplicate seats all rejected (PS2:455–466) | **the decisive refutation of the phase: "valid signatures can approve an incorrect tracing equation"**, so a zero-knowledge proof linking signature, identity and handle is still required (PS2:468); Aurora, AIM/AIMer and HAETAE give ideas but no instantiation (PS2:470); 27,056 B remains the open slot (PS2:472) |

**Where Phase VI ends.** After twenty-three versions the campaign has seven abandoned approaches
(§VIII), four frames that verify but overshoot the cap by 8.5×–24×, zero accepted full quorum
certificates, one named missing object, and one measured obstruction — an ≈ 80 KiB representation of
queried values that no amount of tuning had moved. The 32 KiB gate is never opened.

---

## VIII. Phase VII — the QPT-128 mathematical track, v1.30 → v1.42 (PS2:476–1489, PQT:1583–1956)

The owner narrows the objective: "only work on 128pqt … divide and conquer … glue different school of
thought math … learn from trying 256 and 512". A pasted text defines QPT-128 as forcing a quantum
adversary to expend at least 2^128 quantum gates or logical operations, lists Shor and Grover,
AES-256, "SHA-384 or SHA3-512" as a 512-bit state hash, ML-KEM-1024 parameters, and MAXDEPTH examples
of 2⁴⁰ and 2⁶⁴. Its references are site roots only, so the citation status is recorded as
*incomplete in source*.

The track proceeds by taking one component at a time and trying to bound it. Six of the twelve steps
end in a refutation of the material that was pasted in, and five of those refutations are of claims
that would have made the target look already met.

**v1.30 — a partial model** (PS2:576–599, PQT:1665–1687). A quantum collision bound for a random
h-bit function, written 12(Q+154)³/2^h and attributed to an Isabelle AFP outline on compressed
oracles; at Q = 2^128 and h = 512 it gives ≈ `2^-124.415`. The "+154" constant is transcribed as
found, and the value is insensitive to it. A conditional quorum-safety bound follows. The general
lesson recorded from the 256- and 512-bit stress cases: "expanding a hash output cannot increase
secret entropy, and extraction losses can exhaust an otherwise sufficient component budget"
(PS2:590).

**v1.31 — compartmentalised partial proofs** (PS2:607–818, PQT:1691–1884). Three components are
bounded separately. *The joint extractor* is built on the Don–Fehr–Majenz–Schaffner online
extraction result (arXiv 2202.13730) and extended by the trail's own derivation to a two-proof,
one-database case, ε_J ≤ min(1, ((72+40ℓ)Q³ + 2v)/2^h + 20Q²·p_triv), labelled a reduction sketch and
explicitly a terminal extraction claim only; at r = 512, h = 832, ℓ = 2²⁰, Q = 2^128 it gives
ε_J < `2^-39`, which the trail states is "not a claim of failure probability `2^-128`". *The
signature* component corrects Barbosa et al.'s FSwA bound to ε_CMA ≤ ε_NMA + L_stat, computes a
corank condition giving δ ≤ `2^-540` and ε ≤ `2^-1670` — strengthening the paper's `2^-1664` — and
states what that number is: "commitment entropy, not 1,670-bit signature security". The rejection
premise is labelled an assumption and unproved. *The hash* component refutes a universal
SHAKE-versus-random-oracle distance, because the distinguishing advantage is 1 − 2^-h, and records
that "requesting 832 output bits from SHAKE256 does not increase its 512-bit capacity" (PS2:1862).

**v1.32 — staged comparison and MAXDEPTH** (PS2:822–897). With a 512-bit oracle and a 1/24 threshold
the recurrence p_n = p₀·2^-n needs n = 73, 137, 193, 265 repetitions at 32, 64, 92 and 128 bits; at
128 bits, 320 repetitions give ε_J < `2^-59`. Parallel search W_n = √N·2^(n/2) under depth caps 2⁴⁰,
2⁶⁴ and 2⁹⁶ gives work 2^216, 2^192 and 2^160. **Refutation:** the original 512-bit ternary sampler
passes the bound at 32 and 64 bits but fails at 92 and 128 (PS2:888).

**v1.33 — 1,000 operators amended** (PS2:901–922). 116 corrections, 28 mutations over 182 operators,
112 research questions, 23 adversarial test groups. The strongest partial result is conditional: 320
rounds meet the extraction allocation at Q = 2^128 *if* the protocol proves a 9/16 per-round bound on
non-extractable challenge mass. This file's own definition of QPT-128 as a work factor
(`operators_1000_QPT128_amended_v1.33.md:28–33`) is the definition the project finally adopts.

**v1.34–v1.37 — extractor and signature reductions** (PS2:926–1001). A public decoder with no
sidecar and conditional correctness; a conditional joint extraction that "needs no multiplicative
extraction loss"; a concrete circuit extractor with three local checks after Giacomelli et al.; and
the reduction p_conflict ≤ κ_E + L_E(δ_binding + 64·ε_ML-DSA-87), with adaptive loss 64 or 43 if the
21 corrupt seats are fixed before setup. Throughout, the joint witness extractor is unresolved
because the system lacks a proof protocol for the complete relation.

**v1.38 — SLH-DSA replaces ML-DSA** (PS2:1005–1032). The hybrid's both-must-verify structure means a
hybrid forgery yields an SLH forgery without additional probability loss, given independent keys and
complete logs. ε_SLH is not concretely bounded. This is the change that v1.43 later reverses.

**v1.39 — margin sweep 120–136** (PS2:1036–1063). 2,088 scenarios. A `2^-128` system bound needs a
primitive at `2^-134`, or `2^-136` if the signature gets a quarter of the budget. The √2/2 recurrence
"fits the zero-error quadratic search model. It does not establish physical MAXDEPTH or SLH-DSA
security" (PS2:1058). "No concrete QPT level was established" (PS2:1061).

**v1.40 — the GHZ/√i phase idea** (PS2:1122–1145). The circuit is correct: 129 gates, 12 exact
symbolic tests. **Refuted as a security argument**, because QPT and BQP describe resources, "128
qubits" is not 128-bit security, |√i| = 1, and GHZ has only two populated basis states. What survives
is a simulation argument: Adv_withGHZ(t, q_H, q_S) ≤ Adv_ordinary(t+129, q_H, q_S), since the
adversary can prepare the public state itself. It "supplies no smaller forgery advantage".

**v1.41 — the post-quantum/classical hybrid sampling bound** (PS2:1200–1243). Three refutations of
the pasted claim: AND-verification gives an intersection ≤ min, not a product, so
Adv_Hybrid ≤ Adv_SLH; the public state test accepts with Tr(ρ²) = 1, so there is no gap Δ at all; and
Hoeffding's inequality needs independence, which a single GHZ state does not supply. Even granting
applicability, N = 128 with Δ = 1/2 gives `2^-92.33248`, and reaching `2^-128` needs Δ ≥ 0.588705.
What is kept is constructive and much weaker: a conditional pass probability ≤ 1/2 at every step
gives Pr[all 128 pass] ≤ `2^-128` with dependence allowed — but the premise is missing.

**v1.42 — SLH-DSA tree conditioning** (PS2:1311–1336). The pasted text expanded SLH-DSA wrongly, and
claimed p_max = 1/2 from 128 structured checks. Three refutations: tree layers do not create fresh
challenges, because the verification is a deterministic root reconstruction; Pr[F|G] ≤ min(1, ε/Pr[G])
can equal 1; and q_s·L/2^λ = `2^-127` exceeds `2^-128` already at q_s = 1 with two leaves, so a
Category 1 parameter set is not a universal `2^-128` claim. The constructive replacement is the
additive SPHINCS+ decomposition into PRF, FORS and hypertree (WOTS, key compression, tree hash).

**The unnamed additive-bookkeeping step** (PS2:1413–1489, PQT:1890–1956). The pasted text proposed
Category 5 with n = 256, a multi-target `2^-108`, and a collision estimate (2⁶⁴)³/2^256 = `2^-64`. The
**correction** is that `2^-64` is "nowhere near `2^-128`". The per-term bookkeeping rule becomes
−log₂ ε_i ≥ n_i − a_i·α − b_i·log₂ K_i − log₂ c_i with an aggregate ≈ min − log₂ m, giving the
feasibility condition n_i ≥ 128 + a_i·α + b_i·log₂ K_i + log₂ c_i + log₂ m. The cubic lesson is
tabulated at q = 2⁶⁴ — and the source's own table is wrong at one entry (§X). The section closes on
the remaining blocker: extracting c_i, a_i and b_i from quantum SLH-DSA reductions (PQT:1954).

---

## IX. Phase VIII — the conditional theorem and the Total report (PS2:1491–3342, PQT:1–1560)

The owner asserts that QPT-128 is achievable with the existing construction and asks for the total
proof (PS2:1493, PS2:1761). The result is the report that is placed in this directory as `pqt.md`.

**The "Final QPT-128 theorem"** (PS2:1497–1757 = PQT:1960–2188). The construction is
C = (Setup, Sign, Prove, Verify, ExtractConflict) with (N, F, Q) = (64, 21, 43), so Q − F = 22 > 21
and two quorums intersect in 43 + 43 − 64 = 22 seats. Nine assumptions are inherited from the
uploaded v1.3 source: QLWR wPRF, statistical uniqueness, a quantum-LWE simulation-extractable NIZK,
SLH-DSA QEUF-CMA, quantum collision resistance, unique registry trace keys, canonical encoding,
bounded CRS domains, and durable no-double-vote. SLH-DSA is decomposed additively (PRF_SKG + PRF_MKG
+ FORS + hypertree), giving ε_sig ≤ 64·Adv_SLH and hence Adv_SLH ≤ `2^-134`. Two uniqueness figures
are given to ten decimal places, `2^-148.2870623165` and `2^-154.8800181`, described as independently
recomputed in a supplied audit.

**The theorem's shape.** Six ledger rows at `2^-131` each, so Pr[BAD] ≤ 6·2^-131 = (3/4)·2^-128 <
2^-128. Label: theorem-with-proof, conditional on six uninstantiated primitive bounds. The trail's
own wording discipline is recorded with it: do not write that it "unconditionally achieves 128-bit PQ
security" (PQT:2176–2186). And the size question is explicitly separated: the measured sub-32-KiB
requirement "had not yet closed … different claims and should not be conflated" (PQT:2188).

**The report's own statement of the target** (PQT:138–144):

> CE-QS is QPT-128 secure if Pr[Fail_CE] < 2^-128.

**And its closing theorem** (the box at PQT:2138–2158, quoted as the source renders it, including one
source defect: the macro `\Adv` is used eight times in the report and defined nowhere, so it is
undefined in any standard renderer):

> **Theorem — QPT-128 CE-QS.** For the existing (N,F,Q) = (64,21,43) construction, suppose
> 64ε_SLH ≤ 2^-131, ε_NIZK ≤ 2^-131, ε_QLWR ≤ 2^-131, ε_QCR ≤ 2^-131, ε_uniq ≤ 2^-131 and
> ε_registry ≤ 2^-131. Then Pr[BAD] ≤ 6·2^-131 = (3/4)·2^-128 < 2^-128. Therefore every QPT adversary
> satisfies Adv_C^QPT < 2^-128.

**This is the claim that was refuted downstream.** See §IX-a. The report's own §34 states the
stronger conditional form, and its §35 records four status verdicts: architecture `CLOSED
CONDITIONALLY`; mathematics `SUBSTANTIALLY VALIDATED`; concrete instantiation `NOT YET NUMERICALLY
CERTIFIED`; 32-KiB certificate `OPEN`. The final paragraph is the report's own boundary on itself:
the construction is sufficient to finalize the proof framework, but "a rigorous report must not
claim that the entire implementation has already been experimentally or concretely certified at
2^-128."

**Numbered artefacts that survive to the standing record.** The conflict-extraction identity
i+1 = (Z_i + Z′_i)/(c_M + c_M′) over a characteristic-two field (PQT:546–602); the 96-byte handle as a
48-byte link plus a 48-byte mask (PQT:546–602); the 384-bit challenge hash, with the reasoning that a
256-bit hash gives only a `2^85.3` generic quantum collision (PQT:685–741); and the template
h ≥ 3·log₂ Q + log₂ M + log₂ C + 131 = 339 for Q = 2^64 and M = 2^16 (PQT:745–786). The mandated
registration correction — reject a registration whose y_i equals an existing y_j — is carried at
PQT:1052–1082 and is one of the few D0 conclusions that survives untouched.

**Two defects in the report itself**, recorded rather than repaired: nine ledger terms are listed
against an "eight-row allocation" (PQT:790–834), and the final-statement box in §34 is malformed
(PQT:1508–1518, the display math opened at 1511 with `\[` is closed at 1513 by `$$`, and line 1518
carries a stray `]`). The floor computation 46,192 + 4,288 + 16 = 50,496 > 32,768 is scoped to the
format (PQT:1357–1387), and the LWR row exposure of ≈ 672,352 is not matched to a concrete theorem
(PQT:1192–1226).

---

## X. Phase IX — downstream corrections that define QPT-128 as finally used

These events lie outside the trails. They are part of this chronology because they are the reason the
target is stated the way it is now, and because they are the fate of the trail's strongest claims.
Their full analysis belongs to the domains named against each entry, and none of them is a finding of
this package.

### X-a. The `Adv < 2^-128` target is refuted (v1.43, 11 September 2026)

The v1.43 finalization records that the project "was aiming at two different targets": the work-factor
definition in the operators file, and "Adv < 2^-128 against every QPT adversary" in the v1.21 ledger,
in `pqt.md` §2 and in `pqt.md`'s closing theorem. **Lemma L1 proves the second demand unattainable
for anything with a 256-bit secret: 2^63 Grover iterations already exceed `2^-128`.**

The target is fixed as the work-factor definition, strengthened to a per-gate ratio
Pr ≤ G·2^-130. Three further corrections come with it: the unit of cost is pinned, because counting
one gate per oracle query lets even a single AES-256 key fall with probability 1/3 after 3·2^125
queries (Lemma L2), so each query is charged its circuit cost; reduction running time is charged,
since online extraction runs in O(q²), so a secret hidden inside a proof needs roughly twice the
generic security of a secret sent in the clear (Lemma L5); and the signature-inside-proof designs
are replaced rather than patched, since neither SLH-DSA in the closing theorem nor ML-DSA-87 in R29
meets the target once reduction time is charged. The verdicts table marks the row
"Legacy D3 ledger (`pqt.md` closing theorem)" as **refuted by L1**.

Two notes for a reader of this repository. First, the label "D3" in that verdicts table is the third
of three *target definitions* in the table (D1 the gate work factor, D2 the per-gate ratio, D3 the
refuted advantage bound); it is **not** domain D3, which is a separate package in this repository
with its own contents. Second, `domains/04-operator-ledger/` later measures the v1.33 amendments and
finds the "113 of 116 have no witness" figure unsupported (§X-c below).

### X-b. Main goal and the 32 KiB closure (v1.44)

On 11 September 2026 the owner stated the main goal as conflict-extractable, compact post-quantum
quorum signatures without a sidecar. That is the trail's Target B, realised for the public-signer
case: B0 plus the UOV-V adapter measures 11,396 bytes with liboqs 0.16.0, which does fit the 32 KiB
frame. **Hidden signers remain open**, traced back to the hidden-signer privacy requirement of
`pqt.md` §2 and to the missing binding proof identified in Phase VI.

### X-c. Hidden signers

Modes A and B, v1.45–v1.51. Mode A's linear handle was shown to leak. Mode B acquired a rigorous
ledger and a running toy proof and is research-only: no production proof backend and no security
theorem. The property-layer count recorded for the fix stage — "16/16 and 16/16" — is **withdrawn**:
a re-run of the property suites found the Mode B suite passing 16 and the v1.51 self-test passing 7/7,
but the hash-signature property suite failed to collect at all, executing zero tests, because the
module builds a mixed m ≠ n typecode pair that the fix now refuses. The recorded count is supported
neither by the archived log nor by the re-run. This reversal is owned by `records/` and the hidden
signer domain; it is recorded here only because the claim was a claim about the trail's construction.

### X-d. Cryptanalysis and games (v1.49–v1.52)

A challenge-collision denial of extraction at 2^99.7 gates, repaired by a linearised handle to
2^270.4; an abort flaw at fewer than 22; a safety game that named 23 guilty seats where 22 were
guilty, with a false-positive row claimed at −943 against −181.2 measured; a safety sweep whose
threshold measures 22, matching the theory's 22; and scaling slopes 1.0178 (frame), 0.4498
(suppress) and 1.0242 (evade), with Grover matching exactly and extrapolation errors of
+4.6/−12.4/−38.1 bits. The suite total recorded is 253 tests across 16 suites. These are results of
that programme, not of the trail.

### X-e. Two later programmes absent from the trails

A digital-infrastructure programme of six tested steps at Category 5, and an independent audit stack
whose stated method is that "every layer attempts to disprove a claim with a counterfactual". Neither
is mentioned anywhere in PS, PS2, PQT or TM. Their defining documents are dated 11 September 2026.
They inherit the QPT-128 target from v1.43, not from the trail's own definition — which is the
clearest single consequence of §X-a.

---

## XI. Reversal register

Every reversal the trail records, in one place, with the claim as made, the observation that ended
it, and who owns the correction. The first four are the ones a reader is most likely to have met in a
summary of the results. The remainder are in chronological order of the phase that produced them.

### The four principal reversals

**1. The target definition refuted by Lemma L1.**
*Claimed:* "Adv < 2^-128 against every QPT adversary" — the closing theorem of `pqt.md`
(PQT:2137–2158) and its §2 target (PQT:138–144), asserted by the owner at PS2:1493 and restated as a
six-row `2^-131` ledger in Phase VIII. *Refuted by:* Lemma L1, which shows the demand is unattainable
for anything with a 256-bit secret, since 2^63 Grover iterations already exceed `2^-128`. *Standing
replacement:* QPT-128 as a gate work factor, strengthened to Pr ≤ G·2^-130 per gate, with the unit of
cost and the reduction's running time both charged. *Owner:* `domains/06-qpt128-security-target/` and `records/`
(entry Q1). *Note:* the verdicts table labels the refuted row "Legacy D3 ledger" — a target-definition
label, not the repository's domain D3.

**2. The withdrawn property-layer count.**
*Claimed:* the fix stage recorded the property layer as re-run "16/16 and 16/16". *Refuted by:* a
re-run in a rebuilt environment: the Mode B property suite passes 16, the v1.51 self-test passes 7/7,
and the hash-signature property suite collects zero tests and errors at import on a mixed m ≠ n
typecode pair that the fix itself refuses; the archived log shows the same crash. *Standing:* the
hash-signature "16/16" is withdrawn; the fixes themselves remain regression-tested by the v2.2
self-test. *Owner:* `records/` and `domains/08-hidden-signers/`. *Why it is here:* the count was a
statement about the trail's own construction, so the trail records its withdrawal even though the
correction is not this package's.

**3. The amendment figures later found unsupported.**
*Claimed:* that 113 of the 116 ledger amendments have no executable witness and no citation, and
separately that the two halves run "82 in the D4a range, 37 in the D4b range, 11 elsewhere" out of
"130 amendments". *Refuted by:* parsing the ledger directly. It contains 116 amendments. Amendments
with an executable witness: **15 of 116**, or **10** on the stricter reading that the assertion must
compute the corrected value rather than restate it. Amendments carrying a literature citation:
**0 of 116**. Therefore **101 of 116** (106 strict) have neither. The claimed 113 is not reproduced;
three is the correct count for the second half alone, and the figure appears to be that half-count
extrapolated to the whole file. The second count is also wrong: the ledger has 116 amendments, not
130, and by its own `C35`/`C36` boundary the split is 79 + 37 — the 82 is the whole-family sum for
families L–C and double-counts three amendments the 37 already includes. *Owner:* operator-ledger
domain. *Why it is here:* the v1.33 operators file is one of the trail's artefacts, and its headline
claim — 116 corrections — is what the measurement tests.

**4. The refuted sampling bound.**
*Claimed:* a post-quantum/classical hybrid bound obtained by multiplying per-step success
probabilities, with a Hoeffding-style estimate over the assembled state. *Refuted by:* three separate
observations — AND-verification yields an intersection ≤ min, not a product, so the hybrid advantage
is bounded by the weaker component; the public state test accepts with Tr(ρ²) = 1, so there is no gap
Δ to bound; and Hoeffding requires independence that a single GHZ state does not supply. Even
granting applicability, N = 128 with Δ = 1/2 gives `2^-92.33248`, and `2^-128` would need
Δ ≥ 0.588705. *Standing replacement:* only the constructive fragment, a conditional per-step pass
probability ≤ 1/2 giving Pr[all 128 pass] ≤ `2^-128` with dependence allowed — and its premise is
missing. *Owner:* `domains/05-extraction-and-signature-reductions/`.

### The remaining reversals, in phase order

| # | Claimed | Refuted by | Phase |
|---|---|---|---|
| R5 | A signer-specific preprocessing identifier belongs in the common message | A signer-specific identifier in the common message breaks the binding it was meant to support (PS:614) | II |
| R6 | Ringtail rests on a new "Algebraic One-More Module-LWE" assumption | Ringtail's published result rests on standard LWE in the random-oracle model, with trusted key generation (PS:2420) | III |
| R7 | Hermine's proof problem is "AOM-MLWE" and it is TS-suf-2 | Hermine is standard MLWE/MSIS with AOM-MISIS as an intermediate problem; the ePrint's introduction says TS-UF-2 while its Definition 3.2 and Theorem 6.4 say `ts-suf-2` — both readings are kept (PS:3038, PS:5605) | III |
| R8 | The v0.5/v0.6 model checks its named invariants | Two named invariants are absent from the `.tla`; boundary uniqueness is assumed by representation; the crash step is a stutter; three constants are dead, making `VoteOnce` mean "one vote ever"; partition recovery is hard-coded arithmetic (PS:5642–5662) | IV |
| R9 | Naive aggregated trace tags z_i(h) = a_i + h·u_i extract a conflicting signer | A small-field counterexample: divided difference 41 against true tokens 3 and 13. Scope limited by the trail itself to that particular rule (PS:5863–5885) | V |
| R10 | The Chinese LAPQ-LRS aggregation establishes 43 approvals | It uses one signer's key, so it does not aggregate independent authorizations (PS2:331) | VI |
| R11 | A direct SmallWood bit-circuit adapter can meet the 28,480 B allowance | Its optimistic floor is 79,632 B before any real work (PS2:111) | VI |
| R12 | Tuning the current FRI query representation can meet the allowance | The favourable relaxation still lands at 31,744 B, 3,264 B over (PS2:141) | VI |
| R13 | Query- or path-level recoding can reach 32 KiB | The restricted floor for the current encoding is 50,496 B (PS2:239) | VI |
| R14 | Retaining the prefix and compressing queries is compatible | The retained prefix blocks query-only compression (PS2:337) | VI |
| R15 | A designated-verifier sub-6 KB proof (LUNA) solves the slot | It requires a designated verifier, which a transferable certificate cannot use (PS2:410) | VI |
| R16 | Real ML-DSA-87 signatures can carry the approvals directly | "Valid signatures can approve an incorrect tracing equation", so a binding zero-knowledge proof is still required (PS2:468) | VI |
| R17 | The 512-bit ternary sampler passes the extraction bound | It passes at 32 and 64 bits and fails at 92 and 128 (PS2:888) | VII |
| R18 | The Jackson–Miller–Wang condition holds for ML-DSA-87 | 2γη′n(m+k) < ⌊q/32⌋ is false: 6,304,047,104 < 261,888 is false (PQT:1804–1812) | VII |
| R19 | A universal SHAKE-versus-random-oracle distance exists and is small | The distinguishing advantage is 1 − 2^-h, so no such universal distance exists (PQT:1843–1851) | VII |
| R20 | A GHZ/√i phase construction supplies security | The state is public and can be prepared by the adversary; |√i| = 1; GHZ has two populated basis states; the surviving statement is an equality of advantages, not an improvement (PS2:1122–1145) | VII |
| R21 | Expanded SLH-DSA tree layers create fresh challenges, giving p_max = 1/2 | Verification is deterministic root reconstruction; Pr[F\|G] ≤ min(1, ε/Pr[G]) can equal 1; q_s·L/2^λ = `2^-127` already exceeds `2^-128` at q_s = 1 with two leaves (PS2:1311–1336) | VII |
| R22 | Category 5 implies QPT-128 | The cubic collision bound leaves `2^-64` at n = 256, "nowhere near `2^-128`" (PS2:1413–1489) | VII |
| R23 | The signature-inside-proof designs meet QPT-128 | Once reduction time is charged they fail; SLH-DSA in the closing theorem and ML-DSA-87 in R29 are replaced, not patched (v1.43) | IX |
| R24 | The fix-stage property layer re-ran 16/16 and 16/16 | The hash-signature suite collects zero tests; the count is withdrawn (see reversal 2) | IX |
| R25 | 113 of 116 amendments lack a witness and a citation; the halves split 82 + 37 + 11 out of 130 | 15 of 116 have a witness (10 strict), 0 of 116 carry a citation, so 101 (106) have neither; the ledger has 116 amendments split 79 + 37 (see reversal 3) | IX |

---

## XII. Version → artefact inventory

Which version exists as a file in this repository, and which exists only as prose in a transcript. A
reader who wants to check a v1.11 number will find no artefact to open; a reader who wants to check
`pqt.md` will.

| Version / stage | Named artefact | In this repository? |
|---|---|---|
| prior-art review, AQUA-QC v0.1, reference-free rewrite, proofs v0.2–v0.5 | none named | no — prose only (PS:1–5544) |
| v0.5 research record | `PQ_AQC_research_proof_documentation_v0.5.md` | not in this package (`domains/01-accountable-quorum-foundations/`) |
| v0.6 | documentation, `PQAQCEpochBarrier_v0_6.tla`, `.cfg`, finite-state checker, results | not in this package; the results file's counts match the transcript (PS:5609) |
| v0.7 | documentation, checker, results | not in this package; **no v0.7 `.tla`/`.cfg` exists in the source tree** |
| v0.8 | doc, `.tla`, `.cfg`, checker, auditor, record, SHA-256 manifest, bundle | **absent from the source tree entirely** |
| Target-B memo | `PQ_AQC_Frontier_ConflictExtraction_v0_1.md` and a byte-identical copy | not in this package |
| Target-B construction, "Frontier v0.2" | report, executable checks, results, integrity manifest | **absent from the source tree** — a search for its own headline number 78,608 matches only the transcript |
| CE-QS v0.1–v1.6 | construction and proof documents | in the tree but outside the D0 trail span; their contents are another package's subject |
| v1.7–v1.17 | proof reports and review packages at each version | **absent** — prose only |
| v1.17 | a `continuation_v1.17/` experiment folder | in the tree, partially |
| v1.18, v1.19, v1.20 | qualification and blocker-resolution documents | in the tree (v1.19 also as a byte-identical `.txt`) |
| v1.21 | `PQ_CE_QS_size_path_resolution_v1.21.md` (the transcript calls it a blocker-resolution file) | in the tree, **under a different name** |
| v1.22 | blocker-resolution document | **absent** |
| v1.23 | never named in the trail | — |
| v1.24 | `PQ_CE_QS_32KiB_contents_contract_v1.24.md` | in the tree |
| v1.25, v1.26, v1.27, v1.28 | experiment folders, including a v1.27b and history copies; v1.26's file is `analysis_note.md` | in the tree, under differing names |
| v1.29 | `PQ_CE_QS_v1.29_MLKEM_MLDSA_experiment.zip` | in the tree as an experiment folder |
| v1.30, v1.32 | mathematical model and staged-comparison documents, zips | **absent** |
| v1.31 | none — the trail records that it "could not create or save" (PS2:818) | — |
| v1.33 | `operators_1000_QPT128_amended_v1.33.md` | in the tree; its input file is not |
| v1.34–v1.42 | eight Python scripts (extractor, lift, circuit witness, signature reduction, SLH reduction, margin sweep, GHZ check, sampling audit, tree conditioning) | in the tree |
| v1.43 onward | finalization, sidecar-free finalization, hidden-signer work, games | in the tree, outside the D0 trail span |

---

## XIII. Dependency register

Inputs the trail refers to as existing, which are not in the source tree and not in this repository.
They are listed so that no reader looks for them, and so that no gap is filled with a plausible
substitute.

| Referenced input | Where referenced | Status |
|---|---|---|
| The BFT/ML-DSA design document that opened the research | PS:3, PS:2412, PS:3759 | not in the tree; the research step reports it could not be located (PS:15) |
| An operator monograph, a thesis and a preon document | PS:15, PS:347, PS:479 | not in the tree; declared non-cryptographic analogies |
| The v1.3 and v1.4 CE-QS sources | PS2:55 | requested at v1.8; the v1.3 source is separately cited as the origin of the nine assumptions |
| The v0.8 artefact-audit bundle and the v0.7 `.tla`/`.cfg` | PS:5767–5802, review #7 | absent |
| The Target-B report and test bundle | PS:5818–6224 | absent; the headline number 78,608 exists only in prose |
| The v1.7–v1.16, v1.22, v1.30 and v1.32 review packages | PS2 passim | absent |
| `operators_1000(1).md`, the input to the v1.33 amendment pass | PQT:1886 | not in the tree |
| The supplied audit that recomputed the two uniqueness figures | PS2:1604 | a pasted block, not a file |
| `pqaqc_finite_state_check_v0_6.py` consistency checking | review #7 | the script exists; review #7 notes it contains no consistency check |

The consequences are stated in the records package: a claim that rests on a transcript-only artefact
must be re-run from the experiment folders where they exist, or labelled as reported but unreproduced.
Most of the v1.7–v1.32 counts and sizes are in that position.

---

## XIV. What this chronology does not record

- **No test was re-run for this package.** There is no executable in the research-journey domain;
  the recorded results here are the trail's, and `VERIFICATION.md` says so verdict by verdict.
- **The CE-QS v0.1–v1.6 span is missing.** `PS` ends at the Target-B construction and `PS2` begins at
  v1.7. Versions v0.1 to v1.6 exist as files but not as narrative.
- **Phase IX is summarised, not narrated.** The events in it were produced by later work whose own
  domains carry the detail; only their effect on the trail's claims is recorded here.
- **Independent cryptographic review is outstanding.** No statement anywhere on this trail is
  machine-checked or externally refereed. The trail's own reviews are recorded as external review
  input, and several of them corrected each other as well as the work.
