# Dead ends

The lines the research abandoned, in enough detail that a reader does not repeat them. Each entry
gives what was tried, what it cost, and the observation that ended it. Where the ending observation is
a measurement, the number is given; where it is an argument, the argument is given in the form that
settled it.

This is the larger part of the record. Eighteen approaches were abandoned, and only the last of the
size-campaign attempts and the last of the mathematical ones changed the shape of the final result
rather than merely closing a route.

Pointers are `PS:<line>`, `PS2:<line>`, `PQT:<line>` and `TM:<line>`.

---

## A. Routes through the hot path (Phase I–III)

### A1. Quorum certificates as concatenated per-seat ML-DSA signatures

**Tried.** The design the research started from: a 64-bit signer bitmap plus 43 raw ML-DSA
signatures.

**Cost.** ≈ 1.54 MiB at 667-of-1000 — 667 × 2,420 = 1,614,140 bytes (PS:53–55). At the served
committee of 64 it is smaller but structurally the same.

**Killed by.** Two observations, not one. The size grows linearly with the committee, and the
counting bound shows the problem is not merely bad parameters: ⌈log₂ C(n,t)⌉ bits are needed to
disclose the exact signer set, so no amount of compression makes a *set-disclosing* certificate
constant-size as n grows (PS:83, PS:103). Both facts were needed; the first alone suggests better
parameters, the second rules out the whole family.

### A2. Off-the-shelf lattice multisignatures on the hot path

**Tried.** Squirrel, Chipmunk and Lemur as the aggregation layer.

**Cost.** ≈ 771 KB at 4,096 signatures (Squirrel); ≈ 136 KB at 8,192 for 112-bit security (Chipmunk);
≈ 380 KB at 10⁶ and ≈ 185 KB at ≈1,000 (Lemur). Lemur is also stateful, with millisecond-scale
signing (PS:59).

**Killed by.** The 16 KB hot-path filter (PS:365). Lemur additionally fails the statelessness
requirement for a per-block certificate.

### A3. A threshold signature as the whole answer

**Tried.** A Ringtail-class threshold core alone: 13.4 KB signature and 10.5 KB online at 1,024
signers, which fits the hot path comfortably.

**Cost.** This was the most promising single-primitive answer, and it consumed the first architecture
round.

**Killed by.** The base protocol's slashing requirement: Tendermint-class finality needs signer-level
evidence for accountability, and a plain threshold signature supplies none (PS:43). Review input
later quantified how little of the resulting proof the threshold primitive actually carried:
sections 14 and 16 of v0.1 are pure quorum-intersection arguments that apply verbatim to classical
BLS, so the post-quantum-specific content is narrow (PS:2412). The route became the *core* of the
two-layer design rather than a dead end — but "one threshold signature, done" is the dead end.

### A4. Weighted-stake quorums in the first version

**Tried.** A weighted quorum predicate, with the weighted intersection condition 2q − W > B derived
and proved (PS:1364–1392).

**Cost.** An additional proof layer and additional attack surface, in a design that already had four
open proof obligations.

**Killed by.** The design being served is seat-based, one vote per seat. External review recommended
dropping it for the first version outright, and the owner narrowed the system accordingly
(PS:2412, PS:2428). The result was kept as a proved extension, not deleted: the weighted condition is
in v0.1 §21 and later versions do not use it.

### A5. Proactive refresh in the first version

**Tried.** Refreshable keys, so that a long-lived deployment does not rest on one DKG forever.

**Cost.** Refresh requires a trusted update token, and the closest scheme's refreshability is only
semi-adaptive in its own model (PS:2430–2440).

**Killed by.** The epoch structure adopted in D-3. A fresh DKG per epoch makes refresh unnecessary,
and the refresh mechanism would have imported exactly the trust assumption the epoch structure was
chosen to avoid. This is the clearest case in the record of a feature being dropped because another
decision made it redundant rather than because it failed.

### A6. Quorus for the fast path

**Tried.** A DKG-based, UC-style threshold scheme that verifies under an unmodified FIPS 204
verifier.

**Cost.** Evaluated and measured against the filter, then dropped.

**Killed by.** Sixteen online rounds (PS:5247–5261). One online round was a hard filter, and no
amount of protocol engineering inside the scheme changes the round count. Kept as a proof-first
alternative during the DKG deliberation, not as a fast-path candidate.

### A7. The project-internal method vocabulary

**Tried.** An earlier set of named methods was carried into the research and cross-examined against
the cryptographic problem: a "Genesis" table, GLYPH, MORPH/LEXON, NEXUS, SEMA, DISCOURSE/PRAGMA,
CLOSURE/GENERATE, a "TRIAD" predicate, RIFT, GRAIL, QMC, a genetic algorithm, and a family of
quantum variants (RIFT-Q, TRIAD-Q, GRAIL-Q).

**Cost.** A substantial part of Phase I, including a full cross-examination pass (PS:321–411).

**Killed by.** The finding that none of them is a cryptographic assumption (PS:323). Two fragments
survive and should not be dismissed with the rest: RIFT survives as the concrete elimination filter
that chose the architecture, and "TRIAD" survives as a three-projector certificate predicate
P_I ∧ P_D ∧ P_R (PS:349–359). A reader should also note the name collision — that predicate is not
the blockchain of the same name, which is a separate matter entirely and is not material to this
repository.

### A8. Deterministic QMC points as a source of keys, masks, nonces or salts

**Tried.** An uploaded routine whose basis set was claimed to be algebraically independent, and which
was therefore a candidate source of pseudorandom material.

**Cost.** A review pass over the uploaded code and its claim.

**Killed by.** The dependence is real and elementary: φ and √5 satisfy 2φ − √5 − 1 = 0, so the bases
are not independent (PS:381–389). The rule that followed is absolute and worth repeating: deterministic
QMC points must never generate keys, masks, nonces or salts (PS:391).

---

## B. The formal-methods track (Phase IV)

### B1. A bounded model that did not check what the prose attributed to it

**Tried.** An exhaustive state-space checker over a TLA-like model, reported by pass counts, with the
prose naming the invariants it was said to verify.

**Cost.** Two model versions and five rounds of external review. v0.6's reported counts were
15,633/44,388, 2,401/10,976 and 90/233 states and transitions; review #6 re-ran the checker and
reproduced them.

**Killed by.** Five defects found by inspection and confirmed against the configuration file: two
named invariants (`FinalizedBoundaryUnique`, `EpochMonotonicByConstruction`) are absent from the
specification, which contains TypeOK plus eight and lists nine invariants in its configuration;
boundary uniqueness is assumed by representation, since the model has a single scalar
`finalizedBoundary`; `Crash == UNCHANGED vars` is a stutter step and not a crash; the constants
`Preps`, `Domains` and `Epochs` are dead, so `VoteOnce` means "one vote ever"; and
`partition_recovery()` is hard-coded set arithmetic (PS:5642–5662).

**What replaced it.** v0.7 with all five repaired, a volatile/durable crash model, and mandatory
negative controls: a run with the domain guard removed, an honest boundary double-vote producing
QC(B₀) ∧ QC(B₁), and a send-before-persist crash trace. Pass counts 729/2,916, 140/400,
23,474/127,006, 28/55 and 1,440/8,592, with thirteen configuration invariants matched. The lesson is
recorded as D-9.

### B2. Native TLC or TLAPS as the assurance route

**Tried.** Running the standard TLA+ tools over the actual specification.

**Cost.** Named as the mechanisation target at v0.4 (eight invariants and five crash points,
PS:4412–4448), carried through v0.5 and v0.7, and never executed. v0.5 records that TLC and TLAPS
were not installed in the research environment and that external binary acquisition was blocked
(PS:5417–5442); v0.6 reports the same for `tla2tools.jar` (PS:5609).

**Killed by.** Environment, not by the idea. The consequence a reader must carry: the v0.7 `.tla`
and `.cfg` files are not in the source tree at all, and the entire v0.8 artefact-audit release — the
`.tla`, `.cfg`, standalone auditor, SHA-256 manifest and bundle — is absent from it. So every model
check on this trail is unreproducible here, and the recorded counts cannot be re-verified. Review #7
also found no consistency-check code in the checker script, which is why the v0.8 release added a
standalone auditor.

### B3. Translating liveness through a carry value, and sealing during close consensus

**Tried.** Two related formulations from v0.4: a `Carry_e` value that would translate liveness across
the epoch boundary, and sealing performed inside the close consensus.

**Cost.** v0.4's epoch-closure design was built on the first; the second was the natural way to make
the seal depend on the close.

**Killed by.** Deadlock under partition. Sealing inside the close means the close cannot complete
until the seal exists and the seal cannot exist until the close completes (PS:4864). The carry-based
translation was replaced by a finalized barrier: an epoch may change only at an already-finalized
checkpoint (PS:3806). What replaced both — finalize first, seal second, and place the next
configuration and setup inside the close block — also removed a preimage gap that the earlier
formulation left open (PS:4781–4817).

---

## C. The sidecar-free construction (Phase V)

### C1. Naive aggregated trace tags

**Tried.** Tags of the form z_i(h) = a_i + h·u_i, aggregated across the quorum, on the assumption that
the aggregation preserves enough structure to recover a conflicting signer from two certificates.

**Cost.** This was the first construction attempted for Target B, and it is the reason the phase
produced a refutation before it produced a design.

**Killed by.** A small-field counterexample. Aggregation over *different* quorums leaves the masks
unmatched: the divided difference computed from two certificates was 41, against true token values of
3 and 13 (PS:5863–5885). The trail records the scope of its own refutation precisely — it disproves
that particular rule, not every possible trace-tag construction — and the lesson generalises: any
extraction rule that reads a linear aggregate must be checked against two *different* quorums, not
against two challenges to the same one.

### C2. Publicly sampled trace tags

**Tried.** Sampling the trace tag set from public randomness.

**Cost.** Recorded in a separate CE-QS frontier note rather than in the trail.

**Killed by.** A malicious combiner can adapt the signer set to public sampling randomness. This is
the observation that forced the sampling to be private, and it is the reason the surviving
construction's central operational rule is that "the collector must not learn r_d before the two
committed quorums are fixed" (PS:6088). It is recorded here with a caveat: the relationships between
that note, the earlier trace-tag sketch and the CE-QS v0.1–v1.6 line are not resolvable from the
trail, and a reader who needs them should go to `domains/02-ceqs-construction-evolution/`.

### C3. A 33-byte certificate from the sample-disclosure bound

**Tried.** The hope that the disclosure bound would make the sample short enough to be the certificate:
L = ⌈(λ + log₂ Q_d)/(−log₂(1−γ))⌉ with γ = 22/64.

**Cost.** The computation itself, which was expected to be the good news of the phase.

**Killed by.** Its own arithmetic. L = 211 for `2^-128` in a single domain and L = 264 for 2³²
domains, i.e. 33 bytes of sample. The trail states the conclusion against its own hope: "That is not a
33-byte signature" (PS:6116–6140). The bound is real and correctly computed; what it cannot do is be
the whole certificate, because the verifier sees |σ| = O(λ + L) + |π(λ, n)| and compactness therefore
requires |π| = poly(λ, log n).

### C4. Early or public sample disclosure

**Tried.** Disclosing the sample before the two quorums are fixed, which would have simplified the
protocol.

**Cost.** One of four negative controls in the target's test set.

**Killed by.** Adaptive avoidance: an adversary who sees the sampling randomness before choosing its
signer set can pick a set that avoids the sample. This is the same observation as C2, re-derived
inside the construction, and it is why the negative control exists.

### C5. Target B without an instantiated proof backend

**Tried.** The full sidecar-free construction with a succinct proof π left as a parameter.

**Cost.** The whole phase, including the toy test suite: 78,608 interpolation cases over F₁₇, 289
masking tables, 4,096 and 151,263 sampling combinations, four negative controls. The trail states
plainly what the suite contains: "no real PQ signatures, MPC, NIZK, AEAD, DKG, cryptographic
sampler" (PS:6162–6186).

**Killed by.** Its own boundary statement, which is also the correct verdict: the result is "not yet
the unrestricted, fully instantiated compact PQ quorum signature requested by Target B" (PS:6220).
The four recorded boundaries are restricted corruption, private generation essential, proof backend
uninstantiated, efficiency unmeasured. This dead end is the most instructive one in the record,
because nothing about it failed: the counting theorem is correct, the extraction identity is correct,
and the construction is unusable only because π does not exist.

---

## D. The size campaign (Phase VI)

Eight routes were closed by measurement. The pattern is worth stating before the entries: every one of
them was closed by a *floor* — an optimistic lower bound computed before any real work — rather than
by a failed attempt. That is why the campaign burned twenty-three versions without ever producing a
frame near the budget.

### D1. A direct bit-circuit adapter (SmallWood)

**Tried.** Encode the relation as a bit circuit and prove it directly, at v1.11.

**Cost.** The adapter path plus hidden SHAKE compilation, 19 checks.

**Killed by.** An optimistic proof floor of **79,632 B** against a 28,480 B allowance — 2.8× over,
before any real work (PS2:111–113).

### D2. Rate and fold tuning of the FRI query representation

**Tried.** Adjust the rate and folding parameters of the existing query representation, at v1.13.

**Cost.** 34 checks, after the v1.12 baseline had already measured 328,672 B.

**Killed by.** The favourable relaxation still lands at **31,744 B**, missing 28,480 B by 3,264 B
(PS2:141–143). A near miss is the most expensive outcome available: it invites further tuning, and
the next entry shows that tuning is not where the problem is.

### D3. Encoding and protocol changes on top of the reference proof

**Tried.** A new query-value encoding (QVC1) with public reconstruction, at v1.14.

**Cost.** 61 checks.

**Killed by.** It worked and was not enough: 328,672 → **267,472 B**, a genuine 18.6% reduction, still
far over budget (PS2:156–160). The lesson is the one the trail drew at v1.27: the *representation* is
the obstruction, not the encoding of it.

### D4. Query- or path-level recoding alone

**Tried.** A 32-paper screen for a recoding that would reach the budget without changing the
authorization suite, at v1.18.

**Cost.** The screen produced a recommended research direction (a joint lattice proof binding
authorization, membership and trace handles) and a restricted floor.

**Killed by.** The floor for the then-current encoding is **50,496 B** (PS2:233–243). Query or path
changes alone cannot reach 32 KiB.

### D5. Query-only compression with a retained prefix

**Tried.** At v1.22, keep a prefix of the proof and compress only the queried values.

**Cost.** Two 43-seat frames were built and verified: 727,792 and 735,152 B.

**Killed by.** The retained prefix blocks the compression that would have paid for it (PS2:337). The
frames are ≈ 8.5× over the budget.

### D6. LAPQ-LRS aggregation

**Tried.** Use the Chinese lattice accountable-linkable ring-signature aggregation to carry the 43
approvals, at v1.22.

**Cost.** +1.39% gates, two verification runs.

**Killed by.** Its aggregation operates under a single signer's private key, so it does not establish
43 independent approvals (PS2:331). Nothing was wrong with the reference; it answers a different
question.

### D7. Designated-verifier proofs (LUNA)

**Tried.** LUNA's sub-6 KB proofs as the reserved-slot proof, at v1.26.

**Cost.** A literature screen that also cleared Hermine and the v1.25 prover off the list.

**Killed by.** LUNA's proofs require a designated verifier (PS2:410). A transferable certificate
cannot have one; the property that makes a certificate useful is the property LUNA gives up.

### D8. Signatures that carry the approvals without a binding proof

**Tried.** At v1.29, ML-KEM-1024 plus ML-DSA-87 as an approval delivery mechanism: encrypt and
authenticate the approvals, then check 43 distinct signatures against the statement and the handles.
The test set was substantial — 51 checks, with replay, substituted keys, altered statements and
duplicate seats all rejected.

**Cost.** The v1.29 experiment folder, and the strongest-looking result of the campaign until the
conclusion.

**Killed by.** One observation, and it is the decisive one for the whole phase: "valid signatures can
approve an incorrect tracing equation" (PS2:468). Every tampering check passed, because tampering was
not the threat. A signature binds its signer to a message; it does not bind the message to the trace
handle that identifies the signer's seat. So a zero-knowledge proof linking signature, identity and
handle remained necessary, and the missing object named at v1.26 — a compact publicly verifiable proof
binding all 43 authorizations to their conflict handles — was confirmed as the obstruction. Aurora,
AIM/AIMer and HAETAE supplied ideas and no instantiation.

### D9. Raising the budget instead of reducing the proof

**Tried.** A 512 KiB experimental profile, at v1.15, to test whether the cap was the real obstacle.

**Cost.** One frame built and verified: 269,648 B, self-contained, publicly verifiable, no sidecar,
38 checks.

**Killed by.** Two things at once, and they must be kept apart. It *succeeded* as a clarification —
the cap "is enforced by the current QC format, but it is not a fundamental cryptographic limit"
(PS2:172) — and it *failed* as a solution, because the frame covers only the 43 link hashes and not
the full quorum relation (PS2:183). The full case stayed out of reach: v1.16 produced no valid full QC
and needed 26.5 GiB of witness buffers; v1.17 reduced that to ≈ 16.9 GiB and still recorded "Valid
quorum certificates: zero" (PS2:220).

### D10. Making the candidate pool large enough to guarantee a quorum

**Tried.** At v1.19, size the pool so that 43 signers can be guaranteed against 21 withholders while
keeping all 64 seats.

**Cost.** 116 checks, the largest test set of the phase.

**Killed by.** It cannot be done by pool sizing alone: 46–50 candidates do not guarantee 43 against
21 withholders while retaining all 64, and the retry count is bounded at ≤ 22 and only if each
failure soundly identifies a *fresh* Byzantine (PS2:260–267).

### D11. Registration commitments as a substitute for in-proof authorization

**Tried.** At v1.19, let registration-time commitments to the authorization data stand in for
verifying the authorization inside the proof.

**Cost.** Part of the same 116-check pass.

**Killed by.** The seat index is already shared between participants, and the missing piece is
authorization *verification inside the backend*, which a commitment made at registration does not
provide (PS2:264). A commitment fixes what was registered; it does not show that the thing registered
authorizes the quorum being claimed.

---

## E. The QPT-128 mathematical track (Phase VII)

Five of these entries are refutations of claims brought in from outside rather than of the project's
own ideas. They are included because each one would, if it had held, have shortened the work
substantially — and because a reader who encounters the same claims should know what they cost.

### E1. A GHZ and √i phase construction as a security mechanism

**Tried.** An uploaded design: a 128-qubit GHZ state with a √i phase, presented as supplying security.

**Cost.** The circuit was built and checked: 129 gates, 12 exact symbolic tests, all correct.

**Killed by.** Three observations. QPT and BQP describe *resource* bounds, not security levels, so
"128 qubits" is not 128-bit security. |√i| = 1, so the phase carries no amplitude distinction. And
GHZ has only two populated basis states. What survives is a simulation argument and it is an equality
rather than an improvement: Adv_withGHZ(t, q_H, q_S) ≤ Adv_ordinary(t+129, q_H, q_S), because the
adversary can prepare the public state itself. It "supplies no smaller forgery advantage"
(PS2:1122–1145).

### E2. A product rule for hybrid AND-verification, with a Hoeffding estimate

**Tried.** Bound a classical/post-quantum hybrid by multiplying per-component success probabilities,
then apply Hoeffding's inequality to the assembled state.

**Cost.** The pasted claim plus a dedicated audit script.

**Killed by.** Three independent refutations (PS2:1200–1243). First, AND-verification gives an
intersection bounded by min, not by a product, so Adv_Hybrid ≤ Adv_SLH — the weaker component governs.
Second, the public state test accepts with Tr(ρ²) = 1, so the gap Δ the estimate needs is zero.
Third, Hoeffding requires independence, which a single GHZ state does not supply. Even granting
applicability, N = 128 with Δ = 1/2 gives `2^-92.33248`, and `2^-128` would need Δ ≥ 0.588705.
Note on the arithmetic: the Δ ≥ 0.588705 figure was checked against the source's own formula and is
self-consistent; the failure is in the premise, not the evaluation.

**What survives.** A constructive fragment and nothing more: if the conditional pass probability is at
most 1/2 at every step, then Pr[all 128 pass] ≤ `2^-128`, and dependence is allowed. The premise is
missing.

### E3. Structured tree-head checks with an assumed per-check bound

**Tried.** An uploaded argument that 128 structured checks on the SLH-DSA tree give p_max = 1/2, and
that this is therefore a quantum security bound.

**Cost.** The pasted text plus an audit script.

**Killed by.** Three observations (PS2:1311–1336). The tree layers do not create fresh challenges,
because FIPS 205 verification is deterministic root reconstruction — the same challenge is reused, so
128 checks are not 128 independent trials. Pr[F | G] ≤ min(1, ε/Pr[G]) can equal 1, so a conditional
bound of this shape proves nothing without a lower bound on Pr[G]. And q_s·L/2^λ = `2^-127` already
exceeds `2^-128` at q_s = 1 with two leaves, so the smallest instance fails before the argument is
applied to anything real — a Category 1 parameter set is not a universal `2^-128` claim.

**What replaced it.** The additive SPHINCS+ decomposition: PRF, FORS and hypertree, with the
hypertree's WOTS forgery, key-compression collision and tree-hash collision as separate additive
terms.

### E4. "Category 5 implies QPT-128"

**Tried.** An uploaded argument that NIST Category 5 parameters give a `2^-128` quantum security
level, with the pasted support that SHA-384 and SHA3-512 provide a 512-bit state.

**Cost.** The pasted text plus a bookkeeping pass that produced a reusable rule.

**Killed by.** The cubic collision term. With q = 2⁶⁴ and n = 256 the collision bound leaves `2^-64`,
which the trail describes as "nowhere near `2^-128`" (PS2:1413–1489). A 512-bit state does not make
the cubic term vanish; it moves it.

**What replaced it.** A per-term bookkeeping rule that makes the requirement explicit:
−log₂ ε_i ≥ n_i − a_i·α − b_i·log₂ K_i − log₂ c_i, with an aggregate of roughly min − log₂ m, giving
the feasibility condition n_i ≥ 128 + a_i·α + b_i·log₂ K_i + log₂ c_i + log₂ m.

### E5. The Jackson–Miller–Wang reduction for ML-DSA-87

**Tried.** Use the JMW QROM bound for the deployed ML-DSA-87 parameter set.

**Cost.** A parameter check.

**Killed by.** The paper's own condition, 2γη′n(m+k) < ⌊q/32⌋, is false for ML-DSA-87 even at
η′ = 1: 6,304,047,104 < 261,888 is false, by a factor of about 24,000 (PQT:1804–1812). A published
QROM bound that needs matching parameter conditions cannot be quoted for a parameter set that does
not meet them.

### E6. A universal SHAKE-versus-random-oracle distance

**Tried.** Assume a small, universal distance between SHAKE and a random oracle, and charge it to the
proof.

**Cost.** A hash-component audit.

**Killed by.** No such distance exists: the distinguishing advantage is 1 − 2^-h (PQT:1843–1851). What
remains is a list of conditional or partial results — Canetti–Goldreich–Halevi, Carolan–Poremba's
single-round sponge one-wayness 80(T+1)²/2^min(r,c), Cojocaru et al. (some of whose substituted bounds
exceed 1), and Alagic et al.'s indifferentiability under an ideal-permutation assumption. The related
positive statement is narrow: requesting 832 output bits from SHAKE256 does not increase its 512-bit
capacity (PQT:1862).

### E7. The original 512-bit ternary challenge sampler

**Tried.** Use the sampler as it stood through the staged comparison.

**Cost.** Twelve versions of the mathematical track had been built on it.

**Killed by.** "The original 512-bit ternary sampler passes our bound at 32 and 64, but fails at 92
and 128" (PS2:888). A component can be adequate at one security level and inadequate at another, and
the failure appears only when the levels are compared side by side — which is the reason the 32/64/92/
128 comparison exists.

### E8. The √2/2 recurrence as a measure of MAXDEPTH

**Tried.** Use the owner-supplied recurrence a_{n+1} = (√2/2)·a_n to measure MAXDEPTH, with p_n = p₀·2^-n.

**Cost.** The staged comparison at v1.32 and the margin sweep at v1.39 (2,088 scenarios).

**Killed by.** Its scope. The recurrence "fits the zero-error quadratic search model. It does not
establish physical MAXDEPTH or SLH-DSA security" (PS2:1058), and the sweep's own verdict is that "no
concrete QPT level was established" (PS2:1061). The induced relation p_n = p₀·2^-n "must be proved for
the actual protocol" (PS2:839–841) and never was.

### E9. The compat-mode route: a signature inside an extractable proof

**Tried.** Carry the approvals as real SLH-DSA or ML-DSA-87 signatures inside the proof, so that
signature security alone would deliver the quorum property. This is the v1.37–v1.38 route and it
survived into the migrated report.

**Cost.** The largest single investment of the mathematical track: the joint-extractor derivation,
the FSwA correction, the additive SLH decomposition, and the signing designs of v1.29 and v1.37–v1.38.

**Killed by.** Charging the reduction's running time. Quantum online extraction runs in O(q²), so a
secret hidden inside a proof needs roughly twice the generic security of a secret sent in the clear.
Under that accounting the compat mode fails by 185.0 bits, and the 512-bit-registry-key variant fails
by 141.2 (v1.43). The verdict recorded downstream is that these designs "do not meet QPT-128 once
reduction time is charged … replaced, not patched".

---

## F. What the dead ends have in common

Three patterns recur, and a reader planning similar work should take them from this record.

1. **The near miss is the expensive one.** Two of the size-campaign routes failed by 3,264 and
   2,816 bytes. Each invited further tuning, and the tuning was not where the problem was: the
   representation of queried values was still ≈ 80 KiB after every encoding change.
2. **The refutation in this programme almost always came from the premise, not the arithmetic.** The
   sampling bound, the tree-head checks, the GHZ argument and the Category 5 argument were each
   internally consistent and each rested on an assumption that did not hold — independence, freshness
   of challenges, secrecy of a state, or a cubic term that survives. In each case the arithmetic was
   worth checking and the arithmetic was not the problem.
3. **A correct theorem can still be unusable.** The Target-B counting theorem, the seal-quorum
   theorem and the conflict-extraction identity are all correct, and each depends on an object that
   does not exist: a succinct proof backend, an O(n)-free configuration proof, or a binding proof
   between a signature and a trace handle. In this record that pattern — a right result resting on a
   missing object — is the characteristic form of an unfinished proof rather than a failed one.
