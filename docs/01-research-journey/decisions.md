# Decisions

The decisions that shaped CE-QS and the QPT-128 target: what the question was, which options were
live, what was chosen, the reason the record gives, the theory or measurement the choice rested on,
and whether it still stands.

The last field is the important one. Three of these decisions were later reversed, and two more were
narrowed by later work. A decision that no longer stands is kept in this register with its reversal,
because the construction as it exists today is a product of both the choices that survived and the
ones that did not.

Pointers are `PS:<line>`, `PS2:<line>`, `PQT:<line>` and `TM:<line>`. Claim labels are `[T]` theorem,
`[R]` reduction sketch, `[L]` model-or-ledger estimate, `[M]` measurement, `[S]` simulation, `[A]`
assumption, `[C]` conjecture. Where a decision rested on part of a published result rather than the
whole of it, the entry says which part — the full accounting is in `theories-used.md`.

---

## 1. The register

### D-1. Reframe the problem from "aggregate ML-DSA" to conflict-extractable PQ quorum signatures

**Question.** The starting problem was that quorum certificates made of per-seat ML-DSA signatures
grow with the committee. Is the fix an aggregate signature — or something else?

**Options.** (a) An aggregatable lattice signature, following the BLS analogy. (b) A compact
threshold signature plus an accountability sidecar. (c) A compact certificate from which a
*conflicting* signer can be extracted, without carrying the full signer set.

**Chosen.** (c). Decided at PS:103–115 and PS:449–455.

**Reason as stated.** The counting bound: a self-contained lossless encoding of the exact signer set
needs at least ⌈log₂ C(n,t)⌉ bits (PS:83), so a constant-size certificate cannot also reveal an
arbitrary exact signer set as n grows (PS:103). The observation that made (c) sufficient is a
requirement of the base protocol rather than of the signature: BFT needs conflict evidence for
slashing, not universal attribution. The third escape from the bound — weakened attribution — is
exactly conflict extraction (PS:107–109).

**Theory used.** The information-theoretic lower bound ⌈log₂ C(n,t)⌉ from the signer-set encoding.
**Full** application: this is a counting argument with no assumptions, and the trail uses all of it,
including the two computed instances (912.74 bits at n = 1000, t = 667; ≈ 918,285 bits at
n = 10⁶, t = 666,667). Nothing is borrowed partially here. The BLS draft's size figures (48-byte
signatures, 96-byte keys, PS:51) are used only for contrast: they set the target of "BLS-like
compactness" without any pairing assumption being carried over into the post-quantum construction.

**Still stands.** Yes. It becomes Target B in the uploaded memo and is restated as the programme's
main goal on 11 September 2026.

---

### D-2. Adopt the two-layer AQUA-QC architecture as the deployable path

**Question.** Given a decision to pursue conflict extraction, what should be built first?

**Options.** (a) Attack the compact conflict-extractable primitive directly. (b) Build a compact
threshold QC plus deferred, independently verifiable accountability evidence.

**Chosen.** (b): per-epoch DKG, a FastQC in the hot path, a Merkle accountability sidecar, and
deferred binding through the successor QC.

**Reason as stated.** The "RIFT" elimination filter (PS:121–127; exclusion rules at PS:365) removes
anything above 16 KB on the hot path, anything needing more than one online round, anything with no
signer evidence, and anything without DKG or refresh. A Ringtail-class threshold core survives most
of the filter, so the fastest credible path is that core plus deferred evidence — named AQUA-QC
(PS:127–133).

**Theory used.** Prior-art sizing as reported in the trail, used as a **contrast and scope** set
rather than as a proof: Squirrel ≈ 771 KB at 4,096 signatures, Chipmunk ≈ 136 KB at 8,192 for
112-bit security, Lemur ≈ 380 KB at 10⁶ (PS:59). The sub-16-KB hot-path rule is a project engineering
filter, not a theorem. IA-CCF is used as prior art that constrains the novelty claim: a Merkle log
over signed messages with contradiction-exposing receipts already exists (PS:197), so the sidecar
design had to admit it rather than claim it.

**Still stands.** As "Target A", yes — it is the architecture that reached a proof. It is not the
target the programme finally adopted. Its ≈ 139 KiB sidecar is one of the two facts that produced the
32 KiB cutoff, so it survives as the reason for a constraint rather than as the shipping design.

---

### D-3. Static corruption within an epoch, a fresh DKG per epoch, N ≤ 64 equal seats

**Question.** Which corruption model, and which committee size, should the first complete proof
assume?

**Options.** (a) Adaptive corruption with proactive refresh. (b) Static corruption within an epoch
with a fresh DKG per epoch. (c) Weighted stake instead of equal seats.

**Chosen.** (b), with N ≤ 64 and equal weights, plus "static within epoch, mobile between epochs"
(PS:2428–2440, PS:2878–2904).

**Reason as stated.** A fresh DKG per epoch removes the need to trust an update token, which is the
assumption proactive refresh otherwise carries (PS:2430–2440). N ≤ 64 is the profile the closest
threshold scheme supports. Weighted stake was dropped because the design being served is seat-based,
and because a weighted predicate would add proof and attack surface for no requirement (PS:2412,
PS:2428).

**Theory used.** Two partial borrows, and both are recorded as partial on purpose. From **Hermine's
profile** (N ≤ 64, one online round after preprocessing, non-interactive identifiable abort, ≈ 11 KB,
PS:2420) the decision borrows the *parameter range and interface shape only*; the scheme's DKG claim
is explicitly not inherited, because the preview advertises DKG while the ePrint assumes a trusted
dealer (PS:3044). From **Hermine's refreshability** the decision borrows the *existence of the
feature* and then declines to use it: proactive refresh is dropped precisely because its update-token
assumption is the trust assumption the epoch structure was chosen to avoid. The Bellare et al.
TS-UF hierarchy is a later addition to this decision's support, used **partially**: only TS-UF-2's
rationale — that a malicious coordinator must not be able to combine incompatible honest views — is
carried over, as the reason a valid compact QC implies a threshold of honest supporters of one common
request (PS:4620).

**Still stands.** Yes, and it is the source of `(N, F, Q) = (64, 21, 43)` that every later document
uses. The "why 64" is thinner than the other decisions here: the trail's honest answer is the
scheme's supported range and the seat-based design, not an independent security argument.

---

### D-4. 384-bit commitments and a 384-bit challenge hash

**Question.** How wide must commitments and the challenge hash be for a post-quantum adversary?

**Options.** 256 bits, matching classical collision resistance; 384 bits; 512 bits.

**Chosen.** 384 bits (PS:2740–2768, PS:3655–3675, PQT:685–741).

**Reason as stated.** A generic quantum collision search costs about 2^(m/3) for an m-bit output
(Brassard–Høyer–Tapp), so a 256-bit hash gives only ≈ `2^85.3` security, while 2^(384/3) = 2^128.
The report later generalises this into a sizing template:
h ≥ 3·log₂ Q + log₂ M + log₂ C + 131 = 339 bits for Q = 2^64 and M = 2^16, which 384 satisfies
(PQT:745–786).

**Theory used.** Brassard–Høyer–Tapp's quantum collision algorithm, **full** application: the entire
result is the reason for the width, and the trail's own arithmetic (256 → `2^85.3`, 384 → `2^128`)
follows from it directly. The template's 131-bit constant is a project choice at the `2^-131` ledger
granularity, not part of the cited theorem. That the *string* 384 is chosen rather than, say, 448 is
not derived — it is the smallest multiple of 128 that clears the bound with margin.

**Still stands.** Yes. It is one of the decisions that survive every later revision, and the challenge
width appears in the migrated `pqt.md` unchanged.

---

### D-5. Evidence signatures ML-DSA-44 → ML-DSA-65

**Question.** Which ML-DSA parameter set carries the per-seat evidence signatures?

**Options.** ML-DSA-44 (2,420-byte signatures), ML-DSA-65 (3,309 bytes), ML-DSA-87 (4,627 bytes).

**Chosen.** ML-DSA-65 (PS:3197–3203), on the strength of a multi-user lifetime budget.

**Reason as stated.** With 64 seats and E epochs, the multi-user loss is log₂(64E). Daily epochs over
ten years give E = 3,650, a loss of 17.835 bits, and a single-user target of 157.835 bits at a
`2^-140` budget — so a 128-bit-category parameter set is not enough and the 192-bit-category one is
what the screening calls for (PS:3145–3221, PS:5607).

**Theory used.** A model-or-ledger estimate, labelled as such by its author: "security-budget
screening, not a substitute for the concrete ML-DSA reduction" (PS:3221). The borrowed part is the
standard multi-user loss term log₂(N_u); the rest of a multi-user reduction — the concrete
hybrid argument that would turn the screening number into a bound — is **not** borrowed, and the
trail says so. The FIPS 204 specification is used as a size and parameter source only
(2,420 / 3,309 / 4,627 bytes), and the trail explicitly warns that the concrete FIPS procedures are
not interchangeable with ideal distributions.

**Still stands.** For Target A, yes. It does not carry to the final target: the signature-inside-proof
route was later replaced, so this decision governs the sidecar architecture's evidence layer rather
than the shipping certificate.

---

### D-6. Split every result into a system composition theorem plus a concrete instantiation corollary

**Question.** How should borrowed primitive results be attached to a system proof?

**Options.** (a) Prove the system and the instantiation in one theorem. (b) Prove the system
composition generically, then instantiate the primitives in a separate corollary that names its own
assumptions.

**Chosen.** (b), the "SystemProof + PrimitiveAdapter" split (PS:3050–3062, PS:5237–5243).

**Reason as stated.** It firewalls borrowed primitive results: when a scheme's own paper is found to
have a gap — as Hermine's DKG was — the gap lands in the adapter and the composition survives
(PS:3741, PS:5217).

**Theory used.** Methodological, not a citation. The nearest published support is the practice of
modular reduction composition it imitates. It is used **fully** in the sense that the split is applied
consistently: every later domain's obligation list separates system-level from primitive-level gaps.
Its one limit is recorded: the split organises obligations, it does not discharge them, and every
unmet primitive obligation in §2 below is a gap that lives in an adapter.

**Still stands.** Yes, and it is one of the two methodological decisions that outlive the architecture
it was made for.

---

### D-7. Reconfiguration only at a finalized barrier; finalize first, seal second; self-contained config

**Question.** When may the validator set and keys change, and how is a reconfiguration made safe?

**Options.** (a) Allow reconfiguration during the close of an epoch. (b) Require an already-finalized
checkpoint, seal afterwards, and place the next configuration inside the close block.

**Chosen.** (b), in three moves at v0.4 and v0.5 (PS:3806, PS:4781–4817, PS:4862–4904).

**Reason as stated.** Machine-checked HotStuff-family work proves a *single* configuration, so
configuration change must be a separate proof layer (arXiv 2203.14711, PS:3802). Sealing during the
close consensus creates a deadlock under partition; finalizing first and sealing second removes it
(PS:4864). Placing the next configuration and setup inside the close block removes a preimage gap
that would otherwise need a separate argument about where `localConfig_{e+1}` comes from (PS:4781,
review #2's third gap at PS:3010).

**Theory used.** Three borrows, all **partial** and all recorded as such. From arXiv 2203.14711 the
decision borrows a *scope statement* only — that the machine-checked result covers one configuration
— not the machine-checked proof itself; no result from that paper is used as a premise. From the
epoch/seal structure the trail borrows the *drained-barrier idea* (no cross-height pipelining in the
reconfiguration path, PS:4763) without importing any pipelined-HotStuff liveness theorem. From
refinement-map practice (arXiv 1703.05121) it borrows the *stuttering/history-variable idiom* for
formulating the crash obligations (PS:5363), not the refinement-mapping metatheorem.

**Still stands.** For Target A, yes: v0.5's seals, carry values, activation rule and induction over
epochs all rest on it. It is not carried into CE-QS, which has a fixed committee per epoch by D-3.

---

### D-8. Silence is never blame; a signed invalid share is

**Question.** Under partial synchrony, how should a participant that does not respond be treated?

**Options.** (a) Treat non-response as misbehaviour and blame it. (b) Treat only provable
misbehaviour as blame; treat absence as a timeout with no attribution.

**Chosen.** (b) (PS:2622–2664, PS:3247–3257).

**Reason as stated.** Under partial synchrony a missing message is indistinguishable from a slow
network, so absence cannot be proved. A share that *fails to verify* and is signed by its sender can
be. The false-blame bound is then Adv_false-blame ≤ Adv_ID-MU + ε_IA + ε_H (PS:3261–3297).

**Theory used.** This is a statement about what a partial-synchrony adversary can be held to, used
**fully** but narrowly: the trail does not invoke a liveness theorem, only the indistinguishability
of absence from delay. The identifiable-abort machinery of the underlying threshold scheme is
borrowed **partially** — the trail notes that Hermine's identifiable-abort experiment assumes an
honest aggregator, so every share is wrapped in a signed envelope to recover identifiability when the
aggregator is malicious (PS:3225–3257). The scheme's own IA result is therefore not used as-is; only
its *verdict* (that a bad share is attributable to a sender) is transplanted into the envelope.

**Still stands.** Yes. It is restated in the migrated `pqt.md` (PQT:1353) and it is one of the few
decisions taken in Phase III that applies unchanged to CE-QS.

---

### D-9. Model-checking claims must match artefacts; negative controls are mandatory

**Question.** What standard should a bounded-checking result meet before it is quoted as evidence?

**Options.** (a) Quote the pass counts. (b) Quote the pass counts together with a negative control
for each property, and require that every named invariant exists in the checked specification.

**Chosen.** (b), adopted after external review #6 refuted five formal-methods claims (PS:5642–5662,
repaired at PS:5694–5714).

**Reason as stated.** Two named invariants were absent from the `.tla`; boundary uniqueness was
assumed by representation; the crash step was a stutter; three constants were dead, making `VoteOnce`
mean "one vote ever"; partition recovery was hard-coded arithmetic. A pass count over a model that
does not contain the property is not evidence for the property.

**Theory used.** None — this is a methodological decision forced by refutation, and it is recorded
that way. Its operational content is the negative control: for each checked property, a run with the
enforcing mechanism removed must fail. v0.7 supplies three (domain guard removed; an honest boundary
double-vote producing QC(B₀) ∧ QC(B₁); a send-before-persist crash trace).

**Still stands.** Yes, as a standard. The standard is what condemns the broader claim: even after the
repairs, native TLC and TLAPS were never run and the artefacts for v0.7 and v0.8 are missing from
the tree, so no model check on this trail is reproducible here.

---

### D-10. Pursue Target B — no sidecar

**Question.** After Target A worked, should the programme stop at the sidecar design or attempt the
sidecar-free primitive?

**Options.** (a) Ship Target A. (b) Attempt a compact certificate from which a conflicting signer is
extracted directly from two conflicting certificates.

**Chosen.** (b), the owner's request at PS:5808, restated as the programme's main goal on
11 September 2026.

**Reason as stated.** Target A's sidecar is ≈ 139 KiB of evidence that must be retained and made
available; the certificate itself is small, but the accountability system is not. Target B would make
the evidence intrinsic to the pair of certificates.

**Theory used.** The **counting bound from D-1** is reused in full, now as the reason the naive
approach must fail: if the certificate cannot carry the signer set, the extracted conflict must come
from a relation between two certificates rather than from stored evidence. The conditional-disclosure
pattern is borrowed **partially** from DAPS/PAPS (PS:5842), whose published constructions carry
circular-security and random-oracle assumptions that the trail does not import.

**Still stands.** Yes — but only in the public-signer case. B0 plus the UOV-V adapter measures
11,396 bytes and fits the frame; the hidden-signer case does not close, and the requirement of hidden
signers (D-16) is what remains open.

---

### D-11. A hard 32 KiB = 32,768 B frame

**Question.** Should the certificate have a size cap, and what cap?

**Options.** No cap; a 32 KiB cap; a larger experimental cap.

**Chosen.** 32,768 bytes, with the proof allowance derived as 32,768 − 43·96 − 160 = 28,480 B and
later restated by the v1.24 contents contract as 208 + 5,504 + 27,056 = 32,768 (PS2:83, PS2:98,
PS2:364).

**Reason as stated.** It is a project engineering decision, chosen to sit far below the ≈ 139 KiB raw
evidence payload of Target A while leaving room for a post-quantum proof. The trail's own scoping
sentence is part of the decision: the cap "is enforced by the current QC format, but it is not a
fundamental cryptographic limit" (PS2:172).

**Theory used.** None. The cap is arithmetic plus an engineering judgement, and the escape hatch
found at v1.15 — a 269,648-byte frame verified publicly with no sidecar — is what the scoping
sentence is for. Two later measurements quantify the gap rather than the cap: a restricted floor of
50,496 B for the then-current encoding (PS2:239) and ≈ 80 KiB of queried field values alone
(PS2:435).

**Still stands.** Yes for the public-signer certificate (B0 at 11,396 B fits); open for a
hidden-signer certificate, where the v1.43 companion document states that no known proof system
achieves it.

---

### D-12. Analyse what must be inside the 32 KiB rather than the achieved size

**Question.** After twenty versions of reducing a measured frame, what is the productive next move?

**Options.** (a) Keep optimizing the prover. (b) Specify what the reserved slot must contain and
derive the allowance from that.

**Chosen.** (b), on the owner's redirect at PS2:354: "instead of calculating size … analyze what has
to be present in the 32Kib".

**Reason as stated.** The measured frames were 279,600–283,680 B against a 27,056 B slot, and the
obstruction had been identified as representative rather than parametric — the queried field values
alone were ≈ 80 KiB (PS2:435). Specifying the contents turns an optimization problem into a
statement of what the proof must show.

**Theory used.** The v1.24 contents contract is a **specification**, not a theorem: 208 B of context,
43 anonymous handles at 128 B each, one joint proof within 27,056 B, showing 43 distinct registered
authorizers, three credentials bound per hidden seat, and the tracing equations (PS2:360–366). Two
simplifications in it are borrowed from standard proof-engineering practice and used **fully** at the
level of the relation: message bytes treated as an injective field challenge, which removes a
challenge-hash collision assumption, and a single private selector across three credential tables.
The collaborative-MPC proving idea is borrowed **partially** from Ozdemir's USENIX Security 2022 work
(PS2:375): the trail takes "map collaborative proving to one proof, avoiding recursion" as a design
pattern, not as a theorem about any particular backend.

**Still stands.** As a specification, yes — it is the clearest statement of what the hidden-signer
case requires, and it is why the open item is a named missing object rather than a size number.

---

### D-13. Vote signatures ML-DSA-87 → SLH-DSA-SHAKE-256s, with an optional P-384 hybrid

**Question.** Which signature backs the votes once the proof carries it?

**Options.** ML-DSA-87; SLH-DSA-SHAKE-256s alone; SLH-DSA in a hybrid with P-384.

**Chosen.** SLH-DSA-SHAKE-256s, optionally hybridised with P-384 (PS2:1005–1032, PS2:1550–1586).

**Reason as stated.** A hash-based reduction is available and additive, and the hybrid's
both-must-verify structure means a hybrid forgery yields an SLH forgery "without additional
probability loss", given independent keys and complete logs (PS2:1018–1022). The device family named
in the request is what the choice was being made for.

**Theory used.** Two borrows. From the **SPHINCS+ security games** the trail borrows the *additive
decomposition* — PRF, FORS, hypertree with WOTS forgery, key-compression collision and tree-hash
collision — and the fact that the bounds add (PS2:1330). This is a partial borrow in an important
sense: the decomposition and additivity are used in full, but the *quantum* terms c_i, a_i and b_i of
each component are not extracted, and the trail's last recorded blocker is precisely their absence
(PQT:1954). From the **formally verified tight SPHINCS+ proof** (ePrint 2024/910) it borrows the
*structure* of the modular additive reduction, not its tightness claims for the deployed parameter
set.

**Still stands.** No. **Refuted for signature-inside-proof designs** at v1.43: once reduction time is
charged, a secret hidden inside a proof needs roughly twice the generic security of a secret sent in
the clear, and both SLH-DSA in the closing theorem and ML-DSA-87 in R29 fail the target. They were
"replaced, not patched".

---

### D-14. QPT-128 = composed failure probability Σεᵢ < `2^-128` against every QPT adversary

**Question.** What should "QPT-128" mean as a security definition?

**Options.** (a) A work factor: the gates a quantum adversary must expend. (b) A failure
probability: the advantage of every QPT adversary is below `2^-128`.

**Chosen.** (b) at the time (PQT:96–104, PQT:138–144, PQT:2137–2145), on the stated principle that
"probabilities add; security exponents do not" (PQT:852).

**Reason as stated.** A resource profile and a composed failure-probability budget are both needed
before a scalar "128-bit" statement is meaningful; the v1.19 audit had identified the distinction as
necessary (PQT:148).

**Theory used.** This is a project definition, not a citation, and its support is the arithmetic of
union bounds. Used **fully** within its own frame: the six-row ledger at `2^-131` gives
Pr[BAD] ≤ (3/4)·2^-128, which is a valid union bound. What the union bound does *not* supply is any
statement about the adversary's cost — and that omission is what refuted the definition.

**Still stands.** No. **Refuted as unattainable** by Lemma L1: for anything with a 256-bit secret,
2^63 Grover iterations already exceed `2^-128`, so the demand cannot be met by a construction of this
shape. QPT-128 is now the work-factor definition D1, strengthened to the per-gate ratio
Pr ≤ G·2^-130 (D2), with the unit of cost pinned to a query's circuit cost and the reduction's running
time charged. The verdicts table marks the refuted row "Legacy D3 ledger (`pqt.md` closing theorem)" —
a target-definition label, not the repository's domain D3.

---

### D-15. The registry rejects duplicate trace values

**Question.** What happens if two registrations present the same trace value?

**Options.** Overwrite; accept and disambiguate later; reject the registration.

**Chosen.** Reject (PQT:1052–1082).

**Reason as stated.** The v1.20 audit found that equal secrets make the link values coincide, so two
seats could share a trace identity and the extraction identity would not identify a unique seat.

**Theory used.** Elementary algebra on the link relation, used **fully**: the correction is a
one-line consequence of the trace equation, and the trail gives no other support because none is
needed. It is recorded as a mandatory correction from the audit rather than as a design preference.

**Still stands.** Yes, unchanged into the migrated report and into the later construction.

---

### D-16. Hidden-signer privacy is part of the CE-QS experiment

**Question.** Is hiding the signer set a property of the target, or an optional extra?

**Options.** (a) Public signer set. (b) Hidden signer set as part of the security definition.

**Chosen.** (b) (PQT:130).

**Reason as stated.** It is stated as part of the experiment rather than argued for: the target is a
construction whose security definition includes hidden signer-set security, listed among the
properties the closing theorem delivers (PQT:2147–2158).

**Theory used.** None beyond the definition itself. This is the decision with the largest downstream
consequence and the thinnest stated support, and the record should be read that way: the requirement
is announced in the definition and then carries the programme's one permanently open item. Phase VI
exists because of it — the hidden-signer case is what forced the relation proof, the ≈ 80 KiB
obstruction, and the missing binding proof.

**Still stands.** Yes as a requirement; **unmet as a result.** It is open with R1, and it is the
reason B0's 11,396-byte closure is a partial closure.

---

### D-17. The two later programmes

**Question.** Should the digital-infrastructure programme and the independent audit stack be built on
the trail's QPT-128 definition?

**Options.** (a) Inherit the definition from `pqt.md`. (b) Inherit it from the later finalization.

**Chosen.** (b), implicitly: neither programme appears anywhere in the trail, and both name the
v1.43 finalization as their target source.

**Reason as stated.** The audit stack's method statement is that "every layer attempts to disprove a
claim with a counterfactual" (audit-stack note, 11 September 2026); the infrastructure programme
targets "QPT-128 as fixed in `QPT128_finalization_v1.43` … only NIST Category 5 passes".

**Theory used.** Not from this trail. Both inherit whatever the v1.43 lemmas establish.

**Still stands.** Yes, and it is the cleanest illustration of D-14's reversal: two programmes built
after the trail deliberately took their definition from the document that refuted the trail's target,
not from the trail.

---

## 2. Decisions that were reversed or narrowed

| Decision | What happened | Owner |
|---|---|---|
| D-13 (SLH-DSA in the proof) | Refuted for signature-inside-proof designs at v1.43; replaced, not patched | `domains/06-qpt128-security-target/` |
| D-14 (Adv < `2^-128`) | Refuted as unattainable by Lemma L1; replaced by the gate work factor D1/D2 | `domains/06-qpt128-security-target/`, `records/` entry Q1 |
| D-16 (hidden signers) | Requirement kept; result open. The property-layer count offered as evidence for the hidden-signer work is withdrawn — the hash-signature suite collects zero tests | `domains/08-hidden-signers/`, `records/` |
| D-5 (ML-DSA-65 evidence) | Narrowed: governs the sidecar architecture's evidence layer, not the shipping certificate | `domains/01-accountable-quorum-foundations/` |
| D-11 (32 KiB) | Narrowed: met for public signers, open for hidden signers | `domains/07-compact-certificate-b0/` |

## 3. The external-work comparison

Every outside construction the trail considered, and why it was not adopted. This is the record of the
options that were rejected on their published properties rather than by measurement. The figures are
as the trail reports them and were not re-verified against the primary sources; the reference
catalogue in `docs/02-theory-and-references` carries the citation status of each.

| Work | As the trail reports it | Why not adopted |
|---|---|---|
| **HotStuff** (arXiv 1803.05069) | Assumes a (2f+1, n)-threshold signing interface; the QC is one authenticator, giving linear communication | Not rejected — it is the interface being served. It defines the requirement a quorum signature must meet (PS:35) |
| **Jolteon, Fast-HotStuff** (arXiv 2106.10362) | Extra online signing rounds erase the latency gain | Excluded by the one-online-round filter (PS:37, PS:365) |
| **DiemBFT / LibraBFT** | Epochs align with DKG and refresh; the final QC of an epoch authenticates the next set | A design influence rather than a candidate; its epoch-key structure is the pattern D-3 follows (PS:39) |
| **Narwhal / Bullshark** (arXiv 2105.11827) | Dissemination separated from ordering; evidence can live in the dissemination layer | Not adopted as the evidence carrier: the certificate must be self-contained for transferable verification (PS:41) |
| **Tendermint** | Needs signer-level evidence for slashing | Defines the accountability requirement, and is the reason a plain threshold signature is insufficient (PS:43) |
| **DQS** (arXiv 2607.17700, July 2026) | No PQ quorum signature matches classical constant size; weak/strong local certificates, constant-size messages, quadratic total; ~70 KB Falcon+LaZer at ≈1,000 signers | The closest published work and the same conclusion. Not adopted because it "does not supply an independently transferable compact certificate pair" — its certificates are local (PS:27, PS:311) |
| **IA-CCF** (arXiv 2105.13116) | Already signs and logs BFT messages with Merkle receipts exposing contradictions | Not adopted as a system, and admitted as prior art: a Merkle log over signed messages is not novel, so the novelty claim had to be narrowed to the extractable certificate (PS:197) |
| **Squirrel** | 4,096 signatures → ≈ 771 KB | Hundreds of KB on the hot path (PS:59, PS:123) |
| **Chipmunk** | ≈ 136 KB for 8,192 signatures at 112-bit | Same, and 112-bit is below the target (PS:59) |
| **Lemur** | ≈ 380 KB at 10⁶; ≈ 185 KB at ≈1,000; stateful signing | Same; also stateful (PS:59) |
| **Threshold Raccoon** | ≈ 13 KiB signature, 40 KiB per-participant communication up to 1,024 | Communication, not size, is the obstacle at committee scale (PS:61) |
| **Ringtail** (IEEE S&P 2025; ePrint 2024/1113) | Two rounds with a message-independent first message; 13.4 KB signature and 10.5 KB online at 1,024; academic prototype; standard LWE in the ROM with trusted key generation; bound depends on Q_S = 2^60 | The closest fit and the origin of the ≈ 13–14 KB hot-path estimate. Not adopted directly: trusted key generation, a `2^60` query bound, and no binding of tracing handles (PS:61, PS:2420, PS:2542) |
| **Olingo** (ACM CCS 2026) | 9.7 KB signature with DKG and identifiable abort; ≈ 953 KB per participant, 596 KB with another proof system, 83 KB optimistic | The dealerless, proof-first alternative. Not adopted for the fast path because of per-participant communication; kept as the proof-first profile candidate (PS:61, PS:5235) |
| **Tanuki** | Combines Ringtail and Raccoon ideas; up to 1,024; AOM-MLWE technique | Same reasoning as its components (PS:63, PS:3000) |
| **Hermine** (ePrint 2026/419) | N ≤ 64; ≈ 11 KB; one online round after preprocessing; non-interactive identifiable abort; proactive refresh; standard MLWE/MSIS with AOM-MISIS intermediate; DKG advertised in the preview but assumed trusted-dealer in the ePrint; "signing the certificate does not itself prove that its tracing handles identify the same authorizers" | The source of the committee size, the interface shape and the epoch structure. Not adopted as the scheme: the DKG gap, the trusted-dealer assumption, and the fact that its signing does not bind tracing handles (PS:2420, PS:3044, PS2:411) |
| **Mithril** | ML-DSA verification compatible; evaluated up to six participants | Not evaluated at committee scale (PS:63) |
| **Quorus** (USENIX Security '26) | DKG, UC-style security, verifies under an unmodified FIPS 204 verifier; 16 online rounds | **Rejected for the fast path** on the online-round count alone (PS:5247–5261) |
| **AOM-MLWE** (Espitau/Katsumata/Takemure, CRYPTO'24) | A different paper from Ringtail, resting on a non-standard assumption | Not adopted; the trail's route needed standard assumptions, and its own downstream route (QLWR plus a NIZK) is stated separately (PS:2994) |
| **Bellare et al. TS-UF hierarchy** (CRYPTO 2022) | TS-UF-0..4 plus strong TS-SUF-i | Not a construction. Adopted **partially** as the rationale for the threshold-support lemma (D-3) |
| **TAPS / DeTAPS / lattice accountable tracing signatures** | Related tracing, privacy and accountability notions | Not a public two-certificate extractor with no opener (PS:303, PS:5855) |
| **DAPS / PAPS** | Disclose predefined data on predicate violation | Adopted **partially** as the conditional-disclosure pattern, without its circular-security and random-oracle assumptions (PS:5842) |
| **PQ traceable ring signatures (2021)** | Lattice and symmetric constructions in the QROM, logarithmic size | One hidden signer, not a quorum (PS:5848) |
| **Accountable threshold ring signatures (2024)** | Includes a designated opener | An opener is exactly what a transferable certificate cannot have (PS:5849) |
| **LastRings; LaZer ZK toolkit** (ePrint 2025/1633) | Components for a joint lattice proof binding authorization, membership and handles | Combining them is "a proposed research direction, not an established construction" (PS2:235). The LaZer build also stopped at missing GMP headers and produced size estimates only (PS2:21–27) |
| **LAPQ-LRS** | Aggregates under one signer's private key | Does not establish 43 independent approvals (PS2:331) |
| **LUNA** (ePrint 2022/1690) | Sub-6 KB proofs | Designated verifier (PS2:410) |
| **SmallWood** | Direct bit-circuit adapter | Optimistic floor 79,632 B, 2.8× the allowance (PS2:111) |
| **FRI / BaseFold** | Query representation | Rate and fold tuning lands at 31,744 B, 3,264 B over; the backend is also not shown to satisfy the extraction theorem's assumptions (PS2:141, PQT:1745) |
| **Collaborative MPC proving** (Ozdemir, USENIX Security 2022) | Map collaborative proving to one proof, avoiding recursion | Adopted as a design pattern for the reserved slot, not as a theorem (PS2:375) |
| **ZKBoo** (USENIX Security 2016) | Three local checks | Adopted **partially**: the three local checks are used as the structure of the extraction argument (PS2:969) |
| **Aurora; AIM/AIMer; HAETAE** | Proof-design and signature-compaction ideas | Give ideas; none instantiates the combination (PS2:470) |
| **FIPS 203/204/205** | ML-KEM, ML-DSA, SLH-DSA | Adopted as the primitive layer, with the recorded warning that concrete FIPS procedures are not interchangeable with ideal distributions (PS2:742) |

## 4. What still has to be decided, and by whom

These are decisions the trail leaves open. They are listed so that a reader does not mistake an
unmade decision for a made one.

- **One canonical target definition.** The trail's definition is refuted and the replacement lives in
  a later document. Until one definition is adopted repository-wide, no theorem on this trail may be
  cited as "the QPT-128 result".
- **The hidden-signer proof backend.** No compact publicly verifiable proof binding 43 authorizations
  to their handles inside 27,056 B exists. This is D-12's specification with nothing behind it.
- **The DKG.** No concrete theorem matches the implemented DKG; the scheme's own paper leaves it
  open, and the trail's alternative was a deployment trust assumption.
- **The QROM theorem for the fast threshold adapter.** Named as the only open cryptographic hole at
  v0.5 and never closed.
- **Whether a machine-checked proof is in scope.** The recommendations were made (EasyCrypt or
  CryptoVerif for reductions, TLA+ or Ivy for composition) and never carried out.
