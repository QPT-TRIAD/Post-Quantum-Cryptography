# PQ CE-QS — Adversarial Multi-Track Compartmentalized Verification (companion to v1.19)

**Method note.** v1.19 correctly identified four independent errors in the previous adversarial-alternative report: (a) the 46–50-candidate pool claim was arithmetically wrong against a worst-case 21-Byzantine adversary; (b) the size-gate falsification rule conflated a loose upper bound with a proof of impossibility; (c) the illustrative security-loss composition added bit-exponents instead of probabilities; (d) quantum-UC lifting was cited as if it supplied adaptive corruption, which its own corruption-set model does not. All four are accepted without qualification, and this report is built on the **corrected** baseline v1.19 establishes, not the superseded one.

The pattern behind all four errors is the same: a claim was accepted because it *sounded* like it closed a gap, without a sub-claim-by-sub-claim check against the actual model. This report's method is designed against exactly that failure mode. For each of the four blockers, it opens **multiple independent tracks** (not one preferred alternative), and within each track it **compartmentalizes** the argument into numbered sub-claims, each carrying its own proof attempt, its own validation check, and its own verdict — `PROVEN (conditional)`, `OPEN`, or `REJECTED` — so that a failure in one sub-claim cannot silently be inherited by a conclusion that only cites the track's headline.

No sub-claim in this report is graded `PROVEN` unless a specific argument is given for it in this document or directly inherited, with its conditions restated, from v1.18/v1.19. Everything else is `OPEN`. Nothing here executes code, generates a QC, or measures a proof.

---

## Blocker 1 — Authorization-to-trace binding

### Track 1.A — Port the existing v1.10 shared-index relation as reference (no new architecture)

- **C1.A.1** — *Claim:* the private relation in `ce_qs_relation_v1_10.py` already specifies, not merely computes, the conjunction TraceKeyRel ∧ HandleRel ∧ VerifyVote over one shared index `i`, as v1.19 §1 quotes.
  *Argument:* this is a direct reading of the cited source file, already checked by v1.19 against the implementation; no independent claim is added here.
  *Validation:* consistent with v1.19 §1 and the quorum wrapper's distinctness/canonical-list checks.
  *Verdict:* **PROVEN (conditional on the cited source file being an accurate specification of intended behavior)** — this is a specification fact, not a security proof.

- **C1.A.2** — *Claim:* porting C1.A.1's condition into a public ZK/SNARK backend, unchanged, is sufficient to close the authorization-to-trace binding blocker.
  *Argument:* if the ported circuit enforces the identical conjunction with the same shared witness variable for `i` across all three sub-relations, the mix-and-match forgery (independently valid S ≠ T) is structurally excluded, because there is only one witness index per seat, not two.
  *Validation gap:* "unchanged" is doing the work here. A circuit compiler can silently duplicate a witness variable across sub-circuits (the exact regression named in the prior report's §1.1, "handle reuse across proofs"). This sub-claim is **not** validated until the specific backend's witness-wiring is inspected for that duplication risk.
  *Verdict:* **OPEN** — plausible but requires a backend-specific wiring check, not assumable from the source relation alone.

- **C1.A.3** — *Claim:* this track requires zero new cryptographic assumptions beyond those already implicit in the existing authorization suite (ML-DSA) and trace-hash construction.
  *Argument:* no new commitment scheme, no new registration primitive is introduced; the only new component is the proof system wrapping the existing relation.
  *Validation:* consistent with v1.19's decision to "retain the shared-index relation as the reference."
  *Verdict:* **PROVEN (conditional on the proof-system choice itself being separately qualified under Blocker 3)** — this sub-claim only isolates *which* assumptions are new, not that the old ones are sufficient.

**Track 1.A disposition:** the binding *specification* is settled and reference-grade (C1.A.1). The binding *implementation-in-a-backend* is not yet checked (C1.A.2) and cannot be marked proven from the specification alone.

### Track 1.B — Registration commitment as a static-cost optimization only

- **C1.B.1** — *Claim:* a registration commitment `C_i = Commit(pk_i, tk_i; r_i)` can bind a later-opened tuple to registration.
  *Verdict:* **PROVEN (conditional on the commitment scheme's binding property holding under the chosen ring/modulus)** — this is v1.19 §1's own concession, not disputed.

- **C1.B.2** — *Claim:* opening `C_i` at proof time removes the need for the per-QC `VerifyVote` and `HandleRel` checks.
  *Argument attempted:* none survives. v1.19 §1 shows the per-QC relation must still include both checks operating on the *opened* values; the commitment only relocates where the pairing of `(pk_i, tk_i)` is fixed, not whether a fresh vote and a fresh handle are valid for this message.
  *Verdict:* **REJECTED** — explicitly, by v1.19 §1's restated three-conjunct relation. This closes the previous report's implicit suggestion that commit-then-open shrinks the *message-specific* proof obligations; it only potentially changes *membership/registration-validation* cost, per C1.B.3.
  *Compartmentalization consequence:* because C1.B.2 is rejected, no downstream claim in this report (e.g., in Blocker 2) may assume the per-seat message-specific relation shrinks due to commitments. Any prior arithmetic that did so is retracted.

- **C1.B.3** — *Claim:* a commitment/authenticated-data-structure layer can reduce *static membership/registration-validation* cost versus the existing fixed 64-row ordered lookup.
  *Validation:* v1.19 §1 states this "would require a comparison with the actual existing lookup, using the exact backend," and that "no saving is credited until such a comparison is available."
  *Verdict:* **OPEN, and not creditable by default** — the correct prior for this sub-claim is "no saving," not "presumed saving," until measured.

- **C1.B.4** — *Claim:* proof-of-possession / rogue-registration defenses are needed for any commitment-based registration variant.
  *Argument:* inherited from the prior report's §1.2 adversarial check; v1.19 §1 does not contradict this but notes their necessity depends on "the chosen registration and aggregation model," i.e., it is conditional, not universal.
  *Verdict:* **PROVEN (conditional: applies specifically if aggregation/registration allows a party to derive its commitment as a function of another's public commitment; must be re-checked per concrete scheme)** — carried forward as a standing requirement on Track 1.B only, not Track 1.A.

**Track 1.B disposition:** reduced to a strictly optional, unproven-benefit registration-layer experiment (C1.B.3), with one confirmed rejected shortcut (C1.B.2) and one standing conditional obligation if pursued (C1.B.4). It is not a competing binding mechanism; it is, at best, a possible registration-side cost optimization layered *on top of* Track 1.A's relation, never a substitute for it — consistent with v1.19's explicit rejection of the cost-saving inference.

### Blocker 1 — consolidated verdict
The binding *problem* (two independently valid existential proofs) is closed at the specification level by the existing shared-index relation (C1.A.1). The binding *artifact* (a backend circuit that actually preserves single-witness wiring) is not yet checked (C1.A.2: OPEN). No commitment-based shortcut reduces the message-specific proof obligations (C1.B.2: REJECTED). **Net status: OPEN**, narrowed to a specific, checkable engineering task (witness-wiring audit of the chosen backend), not a design question.

---

## Blocker 2 — 32 KiB serialization

### Track 2.A — Retained hash-based (Binius-family) format

- **C2.A.1** — *Claim:* the measured 46,192-byte retained native prefix, under the current format/layout, makes the current serialized frame exceed 32,768 bytes regardless of query/path/terminal encoding changes.
  *Argument:* direct arithmetic from v1.18 §5.1, restated and not contradicted by v1.19 §5: `4,288 + 16 + 46,192 = 50,496 > 32,768`.
  *Validation:* v1.19 §5 explicitly preserves this specific floor while correcting the *scope* of the conclusion (see C2.A.2).
  *Verdict:* **PROVEN — for this measured format and layout only.**

- **C2.A.2** — *Claim:* this floor generalizes to every hash-based IOP/STARK-family backend, ruling the whole family out.
  *Argument:* none survives; v1.19 §5 explicitly rejects this generalization, citing SmallWood's differently-scaled small-instance regime as a counterexample to "every hash-based construction has this floor."
  *Verdict:* **REJECTED** — the previous report's Track 2 framing ("change backend family" as if hash-based were categorically excluded) overstated what C2.A.1 supports. A differently-designed hash-based small-instance construction is not ruled out by this arithmetic; it is simply unmeasured.

**Track 2.A disposition:** the *specific, currently implemented* hash-based format is excluded (C2.A.1: PROVEN). The hash-based *family* is not excluded (C2.A.2: REJECTED as stated). A small-instance hash-based candidate (e.g., in the SmallWood line) is a live, unmeasured track, not a closed one.

### Track 2.B — Lattice succinct-argument relation

- **C2.B.1** — *Claim:* the exact relation-size inventory needed to evaluate this track is now available: 43 hidden seats, 13,914,112 scalar products (43(608+608+48)·256), 6,957,056 packed multiplications, 11,051 private 64-bit input words, 516 public 64-bit handle words, 903 distinctness checks, 215 secret-dependent Keccak permutations, 22,176,863 native internal wires (v1.19 §2).
  *Validation:* v1.19 §2 is explicit that this inventory describes the **existing native trace circuit**, not a lattice R1CS/relation size, and explicitly warns against substituting these figures into "an unrelated proof-size graph."
  *Verdict:* **PROVEN as a fact about the existing implementation; NOT usable, by itself, as a lattice-relation size estimate.**

- **C2.B.2** — *Claim:* a lattice-backend proof size can be estimated by scaling an unrelated benchmark (e.g., LaBRADOR's 58 KB / ~1M-constraint figure) via an assumed √ or log scaling law.
  *Argument attempted:* none survives; v1.19 §5 states directly: "No scaling curve was supplied for the proposed lattice relation. Extrapolating from a 58 KB unrelated R1CS benchmark using an assumed square-root or logarithmic law cannot fill that gap."
  *Verdict:* **REJECTED.** The prior report's §2.2 "rough scaling reference" framing is retracted as a size-estimation method. It may still motivate *which family to prototype first*, but confers no numeric estimate.

- **C2.B.3** — *Claim:* batched membership and amortized trace-relation checks (proposed in the prior report §2.2) reduce serialized size versus 43 independent checks.
  *Validation:* v1.19 §2 states the existing circuit "already proves all 43 contributions in one native proof," so any batching claim "must identify which equations, openings or commitments it actually removes or amortizes," and "cannot start by assuming that the current system sends 43 separate full proofs."
  *Verdict:* **OPEN, with the burden of proof reassigned** — this is not a default saving on top of a naive 43-separate-proof baseline (which does not exist); it must be argued against the actual single joint-proof baseline, per seat/relation.

- **C2.B.4** — *Claim:* an ML-DSA-based authorization mode requires porting 43 full ML-DSA verifications into the relation, at 142,287 witness bytes pre-encoding (v1.19 §2).
  *Validation:* stated directly in v1.19's inventory; distinguished explicitly from proof-encoded bytes (no size-lower-bound inference is licensed from this figure alone).
  *Verdict:* **PROVEN (as a witness-size fact); implication for proof size remains OPEN** pending backend-specific compilation of ML-DSA verification into the chosen relation.

**Track 2.B disposition:** the inputs needed to *start* a real estimate now exist (C2.B.1, C2.B.4) but the estimation method attempted previously is rejected (C2.B.2), and the batching saving is unproven against the correct baseline (C2.B.3).

### Track 2.C — Corrected falsification gate (applies to both tracks)

- **C2.C.1** — *Claim:* "a conservative upper-bound estimate exceeds 28,480 bytes" is sufficient grounds to declare that parameterization impossible.
  *Verdict:* **REJECTED**, per v1.19 §5's table: only a certified lower bound exceeding the cap, or an actual measured frame exceeding it, licenses an impossibility/failure conclusion. A loose upper estimate only licenses *deferring* the branch for cost reasons, explicitly labeled as such.
  *Consequence:* the prior report's §2.3 "falsification gate" is corrected to distinguish stop-for-cost from proved-impossible, and this report adopts v1.19's six-row table (§5) as the authoritative version, not a re-derivation.

**Blocker 2 — consolidated verdict:** the current implemented format is excluded for its measured reasons only (not generalized). A lattice-relation size remains genuinely unknown; no estimation shortcut attempted so far survives scrutiny. **Net status: OPEN**, with the concrete next artifact identified and undisputed across both reports and v1.19: a real lattice-relation inventory (field, norm, hash, membership, authorization costs) for the *ported* joint relation, then measurement — not extrapolation.

---

## Blocker 3 — 128-bit QPT security

Compartmentalized directly against v1.19 §6's eight-obligation-group ledger structure, since that structure is itself validated (below) before being reused.

- **C3.0** — *Claim:* "128-bit security" as a single scalar is a well-formed target for this system's ledger.
  *Argument:* v1.19 §6 rejects this framing directly: a resource profile (queries, users, sessions, epochs, corruption, exposure) is required before any single number is meaningful, since a ~2^128 work factor is not equivalent to a per-adversary success probability below 2^-128.
  *Verdict:* **REJECTED as originally framed; corrected framing adopted:** the target is a *composed failure-probability budget* against a *stated resource profile*, not a bit-count.

- **C3.1 — Collision vs. preimage event identification.**
  *Claim:* the trace/handle hash construction's needed security property can be assumed to be generic preimage resistance.
  *Argument:* v1.19 §6 shows quantum preimage and collision events have different query exponents (Q²/2^h vs. Q³/2^h, with collision's constant-success exponent at h/3, not h/2), and that which event is actually required is determined by "the actual vector-commitment/extraction analysis," not assumed.
  *Verdict:* **OPEN**, downgraded from any default assumption — must be settled per the specific extraction argument used by the chosen backend before a hash-output width can be chosen.

- **C3.2 — Composition arithmetic.**
  *Claim:* eight obligation terms each individually bounded near a target level compose additively into a comparable total bound.
  *Argument:* v1.19 §6 corrects this exactly: probabilities add, bit-exponents do not; 8 × 2^-131 ≈ 2^-128, not "8 obligations therefore automatically fine because each is 2^-128."
  *Verdict:* **PROVEN (as a corrected arithmetic rule)** — adopted going forward: any future ledger must sum probabilities under a shared final target, with per-term budgets chosen so the sum clears that target (illustratively, eight terms at 2^-131 each clear a 2^-128 total, as v1.19 computes).

- **C3.3 — Concrete-parameter illustrative bound.**
  *Claim:* the illustrative bound h ≥ 3log₂Q + log₂M + log₂C + 131 (for a hypothetical εcoll ≤ CMQ³/2^h theorem) gives usable target parameters for this system.
  *Argument:* v1.19 §6 is explicit this is for illustration only — C, M, Q are not proved or selected for this construction; the 339-bit (or 275-bit, preimage-event) figures "demonstrate the effect of choosing the wrong event," not a recommendation.
  *Verdict:* **REJECTED as a parameter source; PROVEN as a worked method template** — the template (state the theorem, its constants, and solve for h against the target) is reusable once a real theorem for the actual construction is identified; the numbers are not.

- **C3.4 — Local statistical uniqueness bound.**
  *Claim:* the recomputed log₂ε_uniqueness ≈ −148.29 bound (dimension 256, 608 rows, 1,024 domains, exponent 16) qualifies the system's 128-bit target.
  *Argument:* v1.19 §6 is explicit this is "one conditional statistical collision bound under the existing matrix-sampling assumptions," not computational LWR hardness, not a framing theorem, and not the total system error.
  *Verdict:* **PROVEN (as one closed statistical sub-bound, scoped exactly as stated); explicitly not sufficient alone** — one of eight-plus ledger rows, and the only one with an actual computed number so far.

- **C3.5 — Row-exposure/LWR matching.**
  *Claim:* the row-exposure count 672,352 (v1.18 §7, restated v1.19 §6) has been matched to an applicable small-modulus LWR hardness reduction.
  *Verdict:* **OPEN** — v1.19 §6 states this matching "is still required," citing Bogdanov et al. as providing conditional reductions only, "not automatic validation of these parameters."

- **C3.6 — Quantum-UC lifting and adaptive corruption.**
  *Claim:* Unruh's quantum-UC lifting theorem supplies adaptive mid-execution corruption security for the proposed collaborative producer.
  *Argument:* v1.19 §6 checked the primary source directly (Definition 3, Theorem 15) and found the corruption set is fixed at the definition level, and lifting a classical stand-alone MPC proof to quantum-UC is not automatic either.
  *Verdict:* **REJECTED.** Adaptive-corruption security remains an explicit standing obligation, not dischargeable by this citation. This is the single most consequential correction for Blocker 4 as well, since it removes an implicit assumption the phase-separated distributed-production proposal (Track 4.B below) would otherwise have leaned on.

**Blocker 3 — consolidated verdict:** one arithmetic rule is now corrected and reusable (C3.2), one statistical sub-bound is genuinely closed and scoped (C3.4), and every computational/reduction-level obligation remains open (C3.1, C3.5) or is explicitly rejected as a shortcut (C3.3 as parameters, C3.6). **Net status: OPEN**, with a materially better-specified ledger than either prior report, and zero obligation groups fully qualified — matching v1.19's own "no required group is fully qualified" finding exactly.

---

## Blocker 4 — Distributed production under ≤21 Byzantine faults

### Track 4.A — Filtered candidate pool (superseded)

- **C4.A.1** — *Claim (prior report):* a 46–50-person over-provisioned candidate pool tolerates 21 arbitrary withholding validators while guaranteeing 43 usable contributions.
  *Argument:* none survives. v1.19 §3 gives the exact worst-case bound H_min(k) = k − 21, and the exact hypergeometric probabilities under a fixed-21, uniform-pool model (e.g., 50-candidate success probability = 5/2,057,778,636 ≈ 2.43×10⁻⁹), both showing this claim false for any k < 64 without further justified exclusion.
  *Verdict:* **REJECTED**, definitively, by exact combinatorics rather than approximation. This track is closed, not merely deprioritized.

- **C4.A.2 (replacement claim)** — *Claim:* a smaller pool becomes justified once **b** distinct Byzantine identities are *soundly identified and excluded* (not merely suspected), giving k ≥ 64 − b.
  *Validation:* v1.19 §3 derives this directly; a 50-person pool requires b ≥ 14 sound exclusions, a 46-person pool requires b ≥ 18.
  *Verdict:* **PROVEN (conditional: exclusions must be soundly certified, not silence-based, and the corruption budget must be total, not mobile/refreshing).**

**Track 4.A disposition:** collapses into the full-registry baseline (Track 4.C) unless a genuine sound-exclusion mechanism (Blocker-4-internal, separately proved) is running and has already excluded the stated number of identities.

### Track 4.B — Phase-separated agreement + collaborative proving (revised)

- **C4.B.1** — *Claim:* separating cheap participant-agreement from expensive collaborative proving reduces the attacker's ability to force the costliest failure point, and this separation is itself a sufficient liveness improvement.
  *Argument:* v1.19 §4 does not reject the phase-separation *idea* but explicitly states "the document's phase split alone proves neither cheap recovery nor" the retry theorem's second assumption (sound fault identification on failure).
  *Verdict:* **OPEN, downgraded from "improvement" to "unproven architectural choice"** — requires its own protocol and proof, not inferred from the split's existence.

- **C4.B.2** — *Claim:* Unmasking TRaccoon's identifiable-abort machinery transfers to an arbitrary collaborative proving protocol for this relation.
  *Argument:* v1.19 §4 rejects this transfer explicitly: "Transferring that guarantee to a different collaborative proof protocol requires a new protocol and proof; it cannot be inferred from its interface name."
  *Verdict:* **REJECTED** as a free inheritance; **OPEN** as a design target requiring its own construction.

- **C4.B.3** — *Claim:* a bounded timeout without a message-delay assumption can identify culpability for a griefing/aborting participant.
  *Argument:* v1.19 §4: "A timeout does not establish culpability before message-delay bounds apply. A lack of output also does not by itself identify which participant is at fault."
  *Verdict:* **REJECTED as stated.** Fault identification requires an explicit network-timing model plus a sound blame subprotocol, not a bare timeout.

- **C4.B.4** — *Claim (revised, conditional retry theorem, inherited from v1.19 §4):* under a stable delivery/timeout regime, with ≥43 never-corrupted validators, sound per-failure blame identification, no permanent honest exclusion, safe non-reuse across retries, and ≤21 total corruptions, there are at most 21 blame-producing failures and 22 total attempts before success.
  *Argument:* v1.19 §4's potential-function proof (Φ = 21 − b, strictly decreasing per sound failure) is checked here for internal consistency: the argument uses no independence assumption between attempts and only requires each failure to strictly reduce the fault budget by at least one distinct identity — this holds as stated.
  *Validation:* the model-check claim ("checked for every fault count 0–21") is an ideal-model verification of the potential argument's arithmetic, not evidence the five listed preconditions hold in any real protocol.
  *Verdict:* **PROVEN (conditional on all five stated preconditions holding simultaneously, none of which is currently discharged by an implemented protocol)** — this is the strongest closed result in this entire report, and its strength is precisely bounded: it is a theorem about a protocol *interface*, not a theorem that any such protocol exists.

### Track 4.C — Full 64-validator computing committee (BGW-style reference)

- **C4.C.1** — *Claim:* using all 64 validators as computing parties (not just as a candidate pool for the final 43 signers) satisfies the classical Byzantine-resilient general-MPC honest-majority threshold.
  *Argument:* v1.19 §4 cites 64 > 3·21 as matching the BGW threshold structure directly, and separately notes a 43-party *computing* committee containing 21 faulty members would *not* satisfy it — a distinct and stronger requirement than merely having 43 honest signers among 64 candidates.
  *Verdict:* **PROVEN (as an existence-oriented classical threshold match); NOT proven as an implemented PQ protocol** — v1.19 is explicit that "secure channels, broadcast or agreement layer, input-selection functionality, output delivery, corruption model and actual proof-generation computation still need qualification."

- **C4.C.2** — *Claim:* separating computing-committee membership from the hidden 43-signer selection avoids leaking the signer set.
  *Argument:* v1.19 §4 flags the opposite risk directly: if an external observer learns the exact active 43-member set, that leaks the signer set regardless of the QC's own zero-knowledge property, and "the exact leakage policy must still cover traffic, candidate lists, blame and retries."
  *Verdict:* **OPEN** — this is a genuine, currently unresolved privacy obligation, not a solved side-benefit of full-committee computation.

### Blocker 4 — consolidated verdict
The over-provisioned-pool shortcut is closed negatively with exact math (C4.A.1: REJECTED). The corrected exclusion-based pool-sizing rule is sound but conditional on a sound-exclusion mechanism that does not yet exist (C4.A.2). Phase separation survives only as an unproven design choice, not a liveness proof (C4.B.1–C4.B.3: OPEN/REJECTED as previously framed). One genuinely strong conditional theorem is established and independently checked here (C4.B.4: PROVEN, conditional). The full-committee alternative matches a classical threshold structure but remains unimplemented and introduces its own open leakage obligation (C4.C.1, C4.C.2). **Net status: OPEN**, now anchored by one concretely proven conditional theorem instead of an unverified architectural intuition — a genuine improvement in rigor, not a genuine closing of the blocker.

---

## Finalization

### What "finalize the research to be valid" would actually require
Achieving conflict-extractable, compact, post-quantum quorum signatures without a per-certificate sidecar — as a *finalized, valid* result — requires all four of the following simultaneously, not independently:

1. A concrete proof backend implementing the Track 1.A relation with an audited single-witness wiring (closing C1.A.2), producing an actual serialized certificate.
2. That certificate measured at ≤32,768 bytes for the complete frame — a measurement, not an upper-bound estimate (closing C2.B.1–C2.B.4 and satisfying the "actual complete frame" row of v1.19 §5's table, not the "favorable estimate" row).
3. A complete security-loss ledger with every obligation group in v1.19 §6 discharged by an applicable theorem with concrete constants, summed as probabilities against a stated resource profile (closing C3.1, C3.5, and every remaining `OPEN` row in Blocker 3).
4. An implemented distributed-production protocol satisfying C4.B.4's five preconditions (sound per-failure blame, no permanent honest exclusion, safe non-reuse across retries) under a stated network-timing model, plus a resolved leakage policy (C4.C.2) if a full-committee design is used.

### Consolidated scorecard

| Blocker | Closed / proven sub-claims | Rejected shortcuts (this round) | Still open |
|---|---|---|---|
| 1. Binding | Specification-level binding (C1.A.1); new-assumption isolation (C1.A.3) | Commitment-replaces-message-checks (C1.B.2) | Backend witness-wiring audit (C1.A.2); registration cost benefit (C1.B.3) |
| 2. Serialization | Current-format floor, scoped (C2.A.1); existing-circuit inventory (C2.B.1, C2.B.4) | Family-wide floor generalization (C2.A.2); scaling-law estimation (C2.B.2); loose-upper-bound-as-impossibility (C2.C.1) | Lattice relation size and measurement (C2.B.1's implication); batching saving vs. correct baseline (C2.B.3) |
| 3. QPT security | Composition arithmetic rule (C3.2); statistical uniqueness sub-bound (C3.4) | Scalar "128-bit" framing (C3.0); illustrative parameters as real ones (C3.3); quantum-lifting-implies-adaptive-corruption (C3.6) | Collision-vs-preimage event choice (C3.1); LWR matching (C3.5); every remaining ledger obligation |
| 4. Distributed production | Exclusion-conditioned pool-sizing rule (C4.A.2); conditional retry theorem (C4.B.4); classical full-committee threshold match (C4.C.1) | Fixed over-provisioned pool sufficiency (C4.A.1); free transfer of identifiable-abort machinery (C4.B.2); timeout-as-culpability (C4.B.3) | Actual sound blame subprotocol; adaptive-corruption privacy (per C3.6); signer-set leakage policy (C4.C.2) |

### Explicit non-finalization
No cell in the "still open" column above is closed by anything in this document, and no combination of the "closed" cells amounts to a working construction: they are scoped facts and conditional theorems about *pieces* of the system, several of them explicitly downgraded from claims made in the immediately preceding report. Declaring the overall research "finalized" or "valid" at this point would repeat, at the level of the whole report, the exact error v1.19 corrected at the level of individual claims — asserting a conclusion because a chain of plausible-sounding steps was assembled, rather than because every step was independently checked and found to hold. Consistent with both v1.18 and v1.19: **no new full QC was generated, no proof backend was implemented, no distributed prover was executed, and the valid full-QC count remains zero.** The genuine progress in this round is a smaller, more precisely bounded set of open sub-claims, each with a stated condition for closing it — not a closed system.
