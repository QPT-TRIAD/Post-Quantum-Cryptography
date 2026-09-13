# Toward Conflict-Extractable Compact Post-Quantum Quorum Signatures
## A Research-Direction Memo on Target B (Frontier Track), Building on v0.8

**Document status:** Exploratory research direction — not a construction, not a proof, not a claim of priority.
**Builds on:** PQ_AQC research record v0.8 (deployable Target A system + formal-methods track).
**Scope of this memo:** Item 8 of v0.8's "immediate next work" list — *begin the separate frontier-crypto track* — taken up as a standalone design-space survey and a candidate research program, deliberately kept out of the v1 proof.

---

## 0. What this document is and isn't

v0.8 solved Target A (compact hot-path QC + external accountability sidecar) to a defensible research standard and left Target B explicitly open:

> **Target B.** A compact post-quantum quorum signature from which a conflicting signer can be extracted directly from two conflicting compact certificates, without retrieving an O(n)-scale accountability sidecar.

This memo does not solve Target B. It does three narrower things:

1. Surveys the closest existing cryptographic primitives and states plainly why none of them is a drop-in answer.
2. Proposes one candidate construction sketch, named here for reference as **trace-tagged threshold signing (TTS)**, and is explicit about which parts are plausible and which parts are currently unresolved tensions rather than solved sub-problems.
3. Lays out a phased research program with the checkpoints at which the project should be willing to conclude Target B is not achievable with acceptable size/security trade-offs, rather than assuming it must be.

Nothing here should be cited as a security result. If this direction is pursued, it needs its own security definitions, its own proof, its own primary-source ledger, and its own formal-methods track — exactly as demanded of Hermine and Ringtail in the v0.1–v0.8 record — before any claim stronger than "candidate direction" is attached to it.

---

## 1. Restating the target precisely

From the existing record (Section 4.2, v0.5–v0.8):

\[
\boxed{
\mathsf{ExtractConflict}(M_0,\sigma_0,M_1,\sigma_1)\rightarrow(i,\pi_i)
\quad\text{s.t.}\quad
\mathsf{VerifyBlame}(M_0,\sigma_0,M_1,\sigma_1,i,\pi_i)=1,
}
\]

given two accepted compact certificates \(\sigma_0,\sigma_1\) on conflicting statements \(M_0\neq M_1\) in the same session, **without** either certificate encoding the signer subset and **without** retrieving any O(n) object analogous to the current evidence sidecar.

Three properties need to hold simultaneously, and the difficulty of Target B is almost entirely in the fact that each one independently is well-understood, but no published construction gives all three together:

- **Compactness / anonymity on the happy path.** A single valid certificate on one message must look like an ordinary constant-size threshold signature — it must not leak who signed, or even how many signers contributed beyond "at least \(t\)."
- **Soundness of extraction.** Two *conflicting* certificates must yield a correct, verifiable identity except with negligible probability — this is a new security game, not a corollary of the base threshold scheme's unforgeability.
- **No sidecar.** The extraction must work from the two compact objects alone. This is what rules out simply attaching a small commitment per signer to the certificate and calling it "compact" — that is a smaller sidecar, not the removal of one.

---

## 2. Closest existing primitives, and why none of them closes the gap

### 2.1 Accountable subgroup multisignatures (classical, e.g. Boneh–Drijvers–Neven)

BDN-style constructions give O(1)-verification multisignatures where the *exact signer subset* is always recoverable from a bitmap alongside the signature. This solves compactness and gives unconditional accountability, but it is the wrong shape of accountability for Target B: it discloses the signer set on every signature, not only on conflict. Target A already made the deliberate choice not to do this (Section 5 of the v0.5–v0.8 record, the \(\log_2\binom{n}{t}\) information-theoretic argument) — full disclosure on the happy path is exactly what the sidecar architecture was built to avoid, so this line of work doesn't help close Target B; it's the thing Target A already rejected for the same reason Target B wants to avoid it too.

### 2.2 Traceable ring signatures (Fujisaki–Suzuki notion, PQ instantiations exist)

This is the closest published primitive to what Target B wants at the level of a single signer. A traceable ring signature (TRS) scheme is built so that: signing the same message twice under the same ring/issue is *detectable but stays anonymous*; signing two *different* messages under the same ring/issue *reveals the signer's identity*, publicly and verifiably, from the two signatures alone. That is precisely the anonymity-until-misbehavior/extraction-on-conflict shape Target B needs. Post-quantum instantiations already exist and cover multiple hardness families — lattice-based constructions, a coding-theory-based construction, and an isogeny-plus-lattice construction — so the underlying idea is not speculative; it has multiple independent realizations.

The gap: TRS is a **ring signature** primitive. It answers "did *someone* in this anonymity set sign," not "did *at least t of n* sign the same statement, compactly." There is no notion of threshold aggregation in TRS — every ring member's contribution is verified individually, and the "compactness" TRS constructions target is sublinear-in-ring-size verification, not a single constant-size object representing quorum consensus. Porting the traceability *mechanism* (a per-signer tag, typically built from a weak pseudorandom function keyed on the signer's secret and bound to the message/issue, such that two different messages under the same key yield an algebraically combinable pair of outputs) into a threshold-aggregated setting, without reintroducing per-signer linear size, is the actual open research problem.

### 2.3 Hidden-until-disclosed accountability via signature-in-signature embedding

A different but structurally relevant recent technique embeds an inner "accountable" signature inside the randomness of an outer signature, such that the outer signature remains computationally indistinguishable from an ordinary one until the signer voluntarily discloses the inner verification key, at which point the inner signature becomes extractable and checkable. This targets voluntary post-compromise disclosure, not adversarial conflict-triggered extraction, and it is not proactively triggered by a second, conflicting signature the way TRS or Target B needs — but the underlying idea (hide a structured, extractable object inside the randomness of an otherwise-standard signature so the happy path is indistinguishable from a normal signature) is a useful design pattern to borrow: it suggests one candidate way to keep the compact certificate constant-size and unremarkable while still carrying a latent extraction structure.

### 2.4 The obstacle that already exists in the deployable track: threshold lattice signatures are explicitly engineered to prevent this kind of leakage

This is the central tension, and it should be stated plainly rather than discovered halfway through a construction attempt. Naively thresholded Fiat-Shamir-with-aborts lattice signatures (the family Hermine, Threshold Raccoon, and the other NIST-preview candidates all belong to) leak exploitable information about signers' shares if a signer's partial response is not masked — this is a known, real failure mode, not a theoretical curiosity, and it is exactly why Threshold Raccoon introduces pairwise one-time additive masks between signers specifically to *prevent* algebraic leakage from repeated or related signing sessions. Rejection sampling adds a second, independent obstacle: intermediate values must stay hidden until sampling completes, which is why threshold PQ signing protocols reach for garbled-circuit or homomorphic-commitment machinery just to keep the *happy-path* signature secure.

Target B wants the opposite of what these masking techniques are built to guarantee: it wants signing two different messages under the same session to leak an identity-binding value, on purpose, while signing one message never leaks anything. That is not a small tweak to Hermine-style masking — it is asking for a scheme where the masking is unconditionally hiding for one message and conditionally, verifiably openable for two. This is a real, nontrivial cryptographic design constraint, not just an unimplemented feature.

---

## 3. A candidate direction: trace-tagged threshold signing (TTS)

This is a sketch, offered as a starting hypothesis for the research program in Section 4 — not a scheme.

**Idea.** Give each signer \(i\) a per-session tag derived from a value that is:

- **Additively/algebraically homomorphic** in a way that combining the tag from two different messages under the same session id yields a value that opens to \(i\)'s identity or long-term key;
- **Statistically hidden** when only one message has been signed, so a single valid compact certificate carries no extractable structure;
- **Bound into the aggregated signature** in a way that survives threshold aggregation without growing the certificate — i.e., the tag machinery must live inside the *same* algebraic structure the partial signatures already use, not alongside it as an extra per-signer field, or it silently reintroduces the O(n) sidecar under a different name.

Mechanically, this resembles the weak-PRF-based linking tag used in lattice traceable ring signatures, combined with the "hide a structured object in signature randomness" pattern from signature-in-signature accountability constructions, but applied to the *aggregated partial-signature* level of a FROST-like threshold scheme rather than to individual ring members. Concretely, one plausible starting point: derive each signer's per-session masking randomness as a value that is a function of (long-term key share, session id) via a lattice-based weak PRF, structured so that the *difference* of the masks used across two different messages under the same session is a short, extractable linear combination that reveals the signer's identity token — the lattice analogue of how ECDSA/Schnorr nonce reuse across two messages leaks the signing key, except engineered as an intentional, provable extraction property rather than tolerated as an implementation bug.

**What would need to be proven, at minimum**, before this is anything more than a sketch:

- **Anonymity/hiding game.** No PPT adversary can distinguish a certificate produced under this scheme from an ordinary Hermine-style certificate, given a single message per session.
- **Extraction soundness game.** For any adversarially produced pair of accepted, conflicting certificates in one session, `ExtractConflict` outputs a correct, verifiable identity except with negligible probability — this is a new game, structurally closer to the TRS traceability game than to any existing `TS-UF-*` notion, and it needs its own name and its own reduction.
- **Non-frameability.** No adversary, without corrupting signer \(i\), can cause `ExtractConflict` to output \(i\).
- **Joint unforgeability.** Adding the trace-tag machinery must not weaken the base scheme's own unforgeability game — the new algebraic structure is new attack surface, and "the base scheme is TS-UF-2 secure" says nothing about the composed object until this is proven separately.
- **QROM instantiation** of all of the above, eventually — though given that even the *deployable* target's ROM/QROM gap (v0.8, Section 39) remains open, it would be reasonable for this track to accept a ROM-only result as a legitimate first milestone rather than blocking on QROM from day one.

---

## 4. Why this is genuinely hard, stated as concrete obstacles rather than a difficulty rating

1. **The hiding requirement and the extraction requirement pull on the same algebraic structure in opposite directions.** Every leakage-prevention technique in the current threshold-PQ-signature literature (pairwise masks, homomorphic commitments, noise flooding) exists specifically to make the thing TTS wants to happen — conditional algebraic leakage — not happen. A construction here is not "add a feature" to Hermine; it is a different scheme that happens to share Hermine's happy-path shape.
2. **Ring signatures identify individuals; quorum certificates must not, even under scrutiny of the aggregate.** TRS's extraction works because each ring member's signature is checked individually. A compact quorum certificate is a *single aggregated object* by design — Target B is asking for a property TRS gets almost for free (per-member verification) without the thing that makes it free.
3. **Rejection sampling is size-dependent and adversarial-timing-sensitive.** Any masking scheme rich enough to support conditional double-open extraction needs to be re-analyzed against the same rejection-sampling leakage class that already complicates plain thresholding, and there is no guarantee the extraction structure survives rejection/retry without leaking early.
4. **Certificate size could regress toward the sidecar it's meant to replace.** If the trace-tag structure needs even a small additional lattice element per potential signer to make extraction work, and that element must be included in the aggregate rather than the individual partial signature, the "compact" certificate may grow with \(n\) again — just algebraically smeared instead of explicitly listed. Any candidate construction needs an explicit size analysis against the current \(n\le 64\) target before it is taken seriously as solving the O(n) problem rather than relabeling it.
5. **This needs its own formal-methods and assumption-ledger discipline from day one.** Given how much of the v0.1–v0.8 effort went into catching assumption-ledger errors and artifact/claim mismatches in a comparatively well-trodden deployable design, a genuinely novel primitive should be assumed to need at least as much scrutiny, not less, before any "solved" language is used.

---

## 5. Proposed phased research program

| Phase | Goal | Exit criterion |
|---|---|---|
| **0. Definitions** | Write the formal `ExtractConflict`/`VerifyBlame`/anonymity/non-frameability games precisely, independent of any candidate construction. | Games are self-contained, reviewed against the TRS traceability literature for consistency of notion naming (avoid a repeat of the TS-UF-2/TS-sUF-2 naming error from the Target A ledger). |
| **1. Classical proof-of-concept** | Instantiate the TTS idea over a *pairing-based* or discrete-log threshold scheme first, where masking/leakage tools are far better understood, purely to validate that the definitional apparatus from Phase 0 is satisfiable at all. | A classically-secure toy construction with a real reduction, even though it is not post-quantum — this is a sanity check on the definitions, not a deliverable. |
| **2. Lift to lattice setting** | Adapt the Phase 1 construction's trace-tag mechanism onto a FSwA-style threshold scheme (Hermine/Raccoon family). | A candidate construction with an explicit account of where rejection sampling interacts with the trace-tag masking. |
| **3. Resolve the masking/rejection-sampling tension** | Address Section 4, obstacle 3 directly — likely the hardest single step. | Either a proof that extraction survives rejection-and-retry without early leakage, or a documented impossibility/cost result explaining why not. |
| **4. Formal proof + concrete parameters** | Full reduction for all games in Phase 0, concrete lattice parameter estimates, and a real certificate-size number. | Certificate size compared explicitly against the current Target A baseline (compact QC + full sidecar) at \(n=64\); if TTS's certificate plus extraction data isn't meaningfully smaller than the current two-object total, the project should say so rather than presenting a technically-novel-but-practically-worse result as progress. |
| **5. Independent review** | External cryptographic review, ideally from authors already working in PQ traceable/linkable ring signatures, before any implementation work. | Same standard the project has applied to Hermine/Ringtail throughout: primary-source-derived, not self-assessed. |

A negative result at any phase — "this specific approach doesn't work, and here's the obstruction" — is a legitimate and useful outcome of this program and should be recorded with the same rigor as a positive one. The existing record's own bottom line (v0.5–v0.8) already treats Target B as the one genuinely unsolved research question in the whole project; a documented impossibility argument would still be real progress on that question.

---

## 6. Relationship to the existing v0.8 artifacts

This memo is deliberately **not** wired into `PQAQCEpochBarrier_v0_8.tla`, the Python checker, or the assumption ledger. If Phase 0–1 above produce anything concrete, it should get its own document, its own `.tla`/checker pair, and its own SHA-256-manifested release — following the exact discipline v0.8 now applies to itself — rather than being folded into the Target A proof record. Mixing an unproven frontier primitive into the deployable system's ledger is precisely the kind of scope-creep the v0.1→v0.8 revisions have been steadily engineering *out* of this project; this direction should not be the one that reintroduces it.

---

## 7. Bottom line

Target B is not obviously impossible — the ingredients (traceable ring signatures, hidden-until-disclosed accountability embeddings, lattice weak-PRFs) all exist independently and post-quantum instantiations of the closest primitive (TRS) are already published. But nothing published today combines those ingredients with threshold aggregation, and the specific reason it's hard is concrete and statable: the leakage-prevention techniques that make current PQ threshold signatures secure are engineered to prevent exactly the conditional algebraic disclosure this target wants to add back in, deliberately and provably, only on conflict. That is a real research question with a plausible but unproven path, not a known-hard or known-easy one — which is exactly why it belongs in its own tracked workstream rather than as an assumed future upgrade to Target A.

---

**Repository note.** This is the v0.1 Target-B (frontier) design memo. It refers to a v0.8 PQ-AQC
research record and to `PQAQCEpochBarrier_v0_8.tla`; neither is preserved in this repository, and the
latest surviving Target-A record here is `docs/research-proof-documentation.md` (v0.7). The memo is
superseded by the later frontier work in `../02-ceqs-construction-evolution/docs/frontier.md`, which
drops the proposal to modify masking randomness inside a lattice threshold signature. Nothing in this
memo is a construction, a proof, or a claim of priority.
