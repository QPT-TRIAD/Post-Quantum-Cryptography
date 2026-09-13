# Theories used

The deduction chain of the research journey, organised by theory instead of by time. For each
conclusion: the theories invoked, and for each theory whether the **whole** result was applied or only
a part — and where only a part was applied, exactly which part, and why the remainder did not
transfer.

That last distinction is the point of this document. Several of the trail's conclusions look stronger
than they are because a published result is named next to them, and in almost every case only a
fragment of the result was actually used. A partial application must not be read as a full one, and
the entries below are written so that it cannot be.

**Entry fields.** *Statement as used here* is the form the trail uses, which is frequently narrower
than the textbook form. *Label* is the source's own: `[T]` theorem-with-proof, `[R]` reduction-sketch,
`[L]` model-or-ledger estimate, `[M]` measurement, `[S]` simulation, `[A]` assumption, `[C]` conjecture.
*Borrow* is **Full**, **Partial**, **scope-only** (the theory's scope statement is used, no result
from it) or **contrast-only** (it is named to position the work, not used in any step). *Citation as
the source gives it* reproduces the trail's citation, including where it is incomplete; nothing here
fills in a reference the source does not give.

A consolidated catalogue with statement-as-used for every entry is in
`docs/02-theory-and-references`; this document is the D0-specific slice of it, with the borrow
analysis made explicit.

---

## 1. The deduction chain

| # | Conclusion | Label | Theories invoked | Borrow |
|---|---|---|---|---|
| C1 | A constant-size, self-contained certificate cannot disclose an arbitrary exact signer set as n → ∞ | `[T]` | Signer-set counting bound ⌈log₂ C(n,t)⌉; BLS size figures as contrast | Full; contrast-only |
| C2 | Reframe the problem as **conflict-extractable** quorum signatures | `[C]` | C1, plus the three-escape analysis | Full |
| C3 | The two-layer architecture (compact threshold core + deferred Merkle evidence) is the deployable path | architecture, not a claim | RIFT filter (project); prior-art sizing; IA-CCF as a novelty constraint | Contrast-only; scope-only |
| C4 | Two conflicting accepted certificates share ≥ f+1 = 22 signers, each publicly nameable, **with no cryptographic assumption** | `[T]` | Quorum intersection 2q − N | Full |
| C5 | Non-frameability ≤ ε_IS (multi-user qEUF-CMA of ML-DSA) | `[R]` | FIPS 204 multi-user surface; envelope construction (project) | Full as a standard reference; partial elsewhere |
| C6 | Availability ≤ ε_TS + ε_H + ε_DA | `[R]` | Availability interface (project); threshold-scheme soundness | Partial |
| C7 | Safety preservation ≤ Adv_Π + ε_DKG + ε_TS + ε_H, by projection onto base-protocol executions | `[R]` | Base-protocol model; DKG split into agreement / simulatability / malicious soundness | Partial |
| C8 | After f+1 honest seals, at most 2f can vote — fewer than the 2f+1 a quorum needs | `[T]` | Counting (project's own) | Full |
| C9 | A valid compact QC implies ≥ T − c honest supporters of one common signing request | `[T]` | Bellare et al. TS-UF-2 rationale; threshold-support lemma (project) | **Partial** |
| C10 | Commitments and the challenge hash must be 384 bits | `[T]` + `[L]` | Brassard–Høyer–Tapp quantum collision | Full |
| C11 | Multi-user lifetime loss is log₂(N_u) ≈ 17.835 bits at the frozen profile; use ML-DSA-65 | `[L]` | Multi-user loss term | **Partial** |
| C12 | QPT-128 = Σεᵢ < `2^-128` for every QPT adversary | `[A]`/`[L]` | Union bound (elementary) | Full within its frame; **later refuted** |
| C13 | Conditional QPT-128 theorem: six rows at `2^-131`, so Pr[BAD] ≤ (3/4)·`2^-128` | `[T]` conditional | C12's frame; additive SLH decomposition; uniqueness computation (project) | Full within its frame; **premise refuted** |
| C14 | The `Adv < 2^-128` target is unattainable — redefined as a gate work factor | `[T]` | Grover; BBBV/Zalka optimality | Full |
| C15 | Conflict-extraction identity i+1 = (Z_i + Z′_i)/(c_M + c_M′) over a characteristic-two field; 96-byte handle = 48-byte link + 48-byte mask | `[T]` | Elementary field algebra (project) | Full |
| C16 | The registry must reject a registration whose trace value duplicates an existing one | `[T]` | Elementary algebra on the link relation (project) | Full |
| C17 | Under 3q > n + 2c, at most K ≤ ⌊(n−c)/(q−c)⌋ ≤ 2 authorized requests per conflict domain | `[T]` | Counting (project) | Full |
| C18 | Sample-disclosure probability ≤ (1 − (2q−n)/n)^L in the ideal private-generation model | `[T]` in an ideal model | Counting plus an idealised secret-sample model (project) | Full within the ideal model; the concrete reductions were **not instantiated** |
| C19 | Feasibility condition nᵢ ≥ 128 + aᵢα + bᵢlog₂Kᵢ + log₂cᵢ + log₂m | project rule | Per-term bookkeeping; cubic collision scaling | Full as a rule |
| C20 | ε_sig ≤ 64·Adv_SLH, hence Adv_SLH ≤ `2^-134` | `[R]` | Additive SPHINCS+ games (PRF, FORS, hypertree); verified tight proof | **Partial** |
| C21 | ε_J ≤ min(1, ((72+40ℓ)Q³ + 2v)/2^h + 20Q²·p_triv) | `[R]` | DFMS online extraction; the trail's own two-proof extension | **Partial, in two different ways** |
| C22 | ε_CMA ≤ ε_NMA + L_stat, with δ ≤ `2^-540` and ε ≤ `2^-1670` | `[T]` + `[M]` | Barbosa et al. Fiat–Shamir-with-aborts | **Partial** |
| C23 | A self-contained frame verifies publicly with no sidecar, at 269,648 B | `[M]` | None | — |
| C24 | The bounded model's properties hold with negative controls over the reachable states | `[M]` | None borrowed | — |

---

## 2. Theories applied in full

### T1. The signer-set counting bound

**Statement as used here.** A self-contained lossless encoding of the exact signer set needs at least
⌈log₂ C(n,t)⌉ bits. Labelled theorem-with-proof (a counting argument) at PS:83.

**Borrow: Full.** The trail uses the whole result and both of the instances it computes: 912.74 bits
(≈ 114.1 B) at n = 1000, t = 667 against a 125-byte bitmap, and ≈ 918,285 bits at n = 10⁶,
t = 666,667. Nothing about the argument is quotiented and no assumption is attached to it.

**Why nothing was left out.** There is nothing to leave out: it is an injectivity-plus-counting
argument, applicable to any lossless encoding whatever. Its consequence is the strongest structural
statement in the whole trail — "a constant-size, self-contained certificate cannot also reveal an
arbitrary exact signer set as n → ∞" (PS:103) — and it is the reason the programme's target is a
property of *conflicts* rather than of the signer set. One arithmetic slip in the trail's own
presentation is recorded separately: what PS:99 calls "114.8 KiB" is 114.8 kB, i.e. 112.1 KiB.

**Guise note.** This theory is an *information-theoretic* bound on an encoding, not a cryptographic
hardness statement. It is the one result on the trail that cannot be weakened by a better algorithm,
and the distinction matters when it is compared with the cryptographic bounds below.

---

### T2. Quorum intersection, 2q − N

**Statement as used here.** Two quorums of size q from a committee of N intersect in at least
2q − N seats; with q = Q = 43 and N = 64 that is 22 = f + 1. First used as the obligation
|S₀ ∩ S₁| ≥ f+1 (PS:257) and later as the sealing and extraction invariant.

**Borrow: Full, and this is the one fully proved, quantum-independent result of the programme.**

**Where used.** Lemma L6 of AQUA-QC v0.1 states it with no cryptographic assumption (PS:996–1010);
the seal-quorum theorem uses the same counting (PS:3912–3948); the extraction argument
22 − 21 = 1 honest survivor follows from it (PQT:2078–2104); and the conflict domains of Phase V
reuse it (PS:5919–5943).

**Why the full application is the notable thing.** An external review said the quiet part plainly:
sections 14 and 16 of v0.1 "are pure quorum-intersection arguments that apply verbatim to classical
BLS", so the post-quantum-specific content of the original proof is narrow (PS:2412). That is
correct, and it should be read as a statement of *strength* remaining rather than of weakness found:
this is the part of the accountability claim that holds unconditionally, and every quantum-specific
part of the proof is layered on top of it rather than replacing it.

**Guise note — three distinct appearances of the same counting.**
(a) *Intersection*: 2q − N = 22 shared seats between two quorums.
(b) *Exclusion*: at most 2f = 42 can vote after f+1 = 22 honest seats have sealed, which is fewer than
the 43 a quorum needs.
(c) *Request count*: K ≤ ⌊(n−c)/(q−c)⌋, which with 3q > n + 2c gives K ≤ 2 authorized requests per
conflict domain.
All three are the same pigeonhole argument applied to different objects, and a reader who sees a
different constant in each should not read that as three different theories.

---

### T3. Grover search, with BBBV and Zalka

**Statement as used here.** Search on a 256-bit secret succeeds after ≈ 2^63 iterations, which already
exceeds `2^-128`; and the √2/2 recurrence fits the zero-error quadratic search model.

**Borrow: Full, as cited.** Grover's result and the matching lower bound are used whole: there is no
fragment of a quadratic speedup that the trail declines to apply. This is the only theory on the
trail that changed the *definition* of the programme's security target rather than a bound inside it.

**Where used.** The refutation of the `Adv < 2^-128` demand (Lemma L1 of the later finalization): for
anything with a 256-bit secret, a quadratic-speedup search alone breaks it. Also the reason one gate
per oracle query is the wrong cost unit, and the reason each query is charged its circuit cost.

**Scope limit recorded by the trail itself.** Zalka's optimality result is used **partially** in one
place: the √2/2 recurrence "fits the zero-error quadratic search model. It does not establish physical
MAXDEPTH or SLH-DSA security" (PS2:1058). The optimality theorem constrains search, not the physical
depth of a machine, and the trail says so rather than letting the fit imply a hardware claim.

---

### T4. Quantum collision finders (Brassard–Høyer–Tapp)

**Statement as used here.** A generic collision search on an m-bit output costs about 2^(m/3), so a
256-bit hash gives ≈ `2^85.3` and 384 bits are needed for `2^128`. Also cited as the N^(1/3) behaviour
at PS:3669.

**Borrow: Full.** The exponent is used directly, and the sizing template
h ≥ 3·log₂Q + log₂M + log₂C + 131 follows from it.

**Why the full application still yields a project number.** The 131-bit constant in the template is a
project choice matching the `2^-131` ledger granularity; it is not part of the cited result. The
theory supplies the factor of 3; the trail supplies the constant.

---

### T5. The seal-quorum counting and the conflict-domain counting

**Statement as used here.** (a) If f+1 honest participants have sealed, at most 2f votes can exist, and
2f < 2f+1 = q. (b) 3q > n + 2c implies at most two authorized requests per conflict domain.

**Borrow: Full — and both are the project's own counting, not a borrowed theorem.** They are recorded
here rather than under "project rules" because they carry load-bearing claims and a reader should know
they are self-contained: neither has an external premise, and neither can be weakened by a later
cryptanalytic result.

---

### T6. The FIPS standards, as size and parameter sources

**Statement as used here.** ML-DSA-44/65/87 signatures are 2,420 / 3,309 / 4,627 bytes; ML-DSA is an
individual signature scheme, not aggregatable; ML-KEM establishes shared secrets and provides no
signature unforgeability; SLH-DSA is a stateless hash-based scheme derived from SPHINCS+ with
deterministic root reconstruction.

**Borrow: Full as standards, and used as *references* rather than as theorems.** No FIPS security claim
is carried into any proof step. The trail states the bound explicitly: "approx 128/192/256-bit
strength with caution that categories are not one exact attack cost", and that the concrete FIPS
procedures — seeded expansion, masks, challenge sampling, encoding, rejection — "are not
interchangeable with ideal distributions" (PS2:742). That caution is the reason the compatibility
question stays open after the v1.22 authorization-suite change.

---

## 3. Theories applied in part — and exactly which part

### P1. DFMS online extraction (arXiv 2202.13730)

**Statement as used here.** Online extraction for commit-and-open proofs in the quantum random-oracle
model; the extraction charge is O(Q²), so a secret hidden inside a proof needs roughly twice the
generic security of a secret sent in the clear.

**Borrow: Partial, and in three separable degrees — a reader should keep them apart.**

1. *The O(Q²) charge is borrowed whole.* This is the single fact that decides which instantiations
   pass (Lemma L5 of the later finalization), and it was applied to every candidate: the compat mode
   fails by 185.0 bits under it, the 512-bit-registry-key variant by 141.2.
2. *The two-output extension is the trail's own derivation, not the paper's.* The bound
   ε_J ≤ min(1, ((72+40ℓ)Q³ + 2v)/2^h + 20Q²·p_triv) is labelled "my derivation from the published
   lemmas" (PQT:1723) and is explicitly a terminal extraction claim only (PQT:1725). So a reader must
   not attribute the coefficient structure to DFMS: `72 + 40ℓ`, `2v`, `20Q²` are project quantities.
3. *The premise is not met by the deployed backend.* The paper's Merkle theorem needs an efficient
   special-soundness decoder, which is required and not instantiated
   (PS2:866); the BaseFold/FRI backend is not shown to satisfy the theorem's hypotheses
   (PQT:1745); and the compressed-oracle simulation cost O(Q²)·poly(h,B) is a separate unresolved
   charge.

**Why the rest did not transfer.** The paper's result is about a commit-and-open proof built from a
special-sound protocol. The project's relation is a 43-seat circuit whose decoder does not exist, so
the borrowed part stops at the *cost model* (O(Q²)) plus the paper's lemma shapes. The trail records
the honest consequence rather than the hoped-for one: at r = 512, h = 832, ℓ = 2²⁰, Q = 2^128 the
bound gives ε_J < `2^-39`, which is "not a claim of failure probability `2^-128`" (PQT:1735–1741).

---

### P2. Barbosa et al., Fiat–Shamir with aborts

**Statement as used here.** ε_CMA ≤ ε_NMA + L_stat, with a rejection premise p ≤ 759/1024 and a
statistical loss L_stat ≤ `2^-539` at q_S = 2^64, q_H = 2^128.

**Borrow: Partial — the additive loss relation only.**

*Borrowed:* the decomposition of CMA security into NMA security plus a statistical term, and the
general shape that the statistical term is what absorbs the rejection behaviour.

*Not transferred, and why:* (a) the trail's own numbers for the deployed parameter set are a
recomputation, not the paper's — q = 8,380,417, n = 256, ℓ = 7, corank cutoff 28 giving δ ≤ `2^-540`
and ε ≤ `2^-1670`, which strengthens the paper's `2^-1664`, and the trail labels it a measurement
under a stipulated uniform model; (b) the trail states what that exponent is: "commitment entropy, not
1,670-bit signature security"; (c) the rejection premise p ≤ 759/1024 is labelled an assumption and
explicitly unproved (PQT:1784); (d) the paper's mechanisation is classical-ROM, with the QROM left
separate, so no quantum claim is inherited. The NMA algebra itself
([I | A | −t]·y = w̃ with a norm bound) is a project theorem by linear algebra, and self-target
MSIS hardness is stated as a separate obligation rather than folded in.

---

### P3. The Bellare et al. TS-UF hierarchy (CRYPTO 2022)

**Statement as used here.** TS-UF-0 through TS-UF-4 plus the strong variants; TS-UF-2 is the level at
which a malicious coordinator cannot combine incompatible honest views.

**Borrow: Partial — the rationale of one level, used to justify one lemma.**

*Borrowed:* the *reason* TS-UF-2 exists, which the trail uses to justify the threshold-support
argument: a valid compact QC implies at least T − c honest supporters of one common signing request
(PS:4600–4634, PS:4666–4732).

*Not transferred:* the hierarchy's formal definitions and separation results are not used as
premises; nothing in the proof is stated as "the scheme is TS-UF-2, therefore…". This is deliberate
and traceable to a refutation: an external review could not confirm that the scheme's own paper claims
TS-UF-2, and the trail's resolution was to keep *both* readings of the paper — the introduction's
TS-UF-2 and the formal `ts-suf-2` of Definition 3.2 and Theorem 6.4 — rather than to lean on either
(PS:5605). A reader who finds the hierarchy named next to this lemma should read it as *motivation for
a counting lemma*, not as a borrowed theorem.

**Citation status.** Standard (added): Bellare, Crites, Komlo, Maller, Tessaro, Zhu. The scheme's own
paper is cited by the trail, but the terminology mismatch inside that paper is recorded as a source
defect.

---

### P4. SPHINCS+ security games, and the formally verified tight proof

**Statement as used here.** The security of a hash-based signature splits additively into PRF_SKG,
PRF_MKG, FORS and hypertree games, the last with WOTS forgery, key-compression collision and tree-hash
collision; the bounds add. Hence ε_sig ≤ 64·Adv_SLH and Adv_SLH ≤ `2^-134`.

**Borrow: Partial — the decomposition and the additivity, not the quantum component terms.**

*Borrowed:* the modular structure and the fact that the terms add, which is what makes the six-row
ledger composable at all (PS2:1330, ePrint 2024/910 for the verified structure).

*Not transferred:* the *quantum* values of the per-component terms. The trail's own last recorded
blocker on this route is the extraction of cᵢ, aᵢ and bᵢ from the quantum SLH-DSA reductions
(PQT:1954) — which is to say, the additive frame was borrowed while its contents were not, and the
`2^-134` figure is a project allocation inside that frame rather than a number the cited work
supplies.

*Also not transferred, and this mattered later:* tightness claims for the deployed parameter set. The
route was refuted at v1.43 on the separate ground of reduction running time (P1 above), not on the
ground of tightness, and a reader should not conflate the two.

---

### P5. Hermine (ePrint 2026/419)

**Statement as used here.** N ≤ 64; ≈ 11 KB; one online round after preprocessing; non-interactive
identifiable abort; proactive refresh; standard MLWE/MSIS with AOM-MISIS as an intermediate problem.

**Borrow: Partial, in four distinct parts — and this is the most finely divided borrow on the trail.**

| Part of Hermine | Borrowed? | Why, or why not |
|---|---|---|
| N ≤ 64 parameter range | Yes | It is the reason the committee is 64. The trail gives no stronger justification for the number |
| Interface shape (DKG, ShareSign, Combine, identifiable abort) | Yes | Used as the interface the system proof is written against |
| Epoch structure (fresh DKG per epoch) | Yes | Adopted so that refresh is unnecessary |
| Refreshability | Named, declined | Its update token is a trust assumption the epoch structure removes |
| DKG result | **No** | The preview advertises DKG while the ePrint assumes a trusted dealer and calls DKG results "orthogonal" (PS:3044, PS:3741) — an acknowledged gap, not a design choice |
| Identifiable-abort result as-is | **No** | Its IA experiment assumes an honest aggregator, so every share is wrapped in a signed envelope to recover identifiability under a malicious aggregator (PS:3225–3257) |
| `ts-suf-2` / TS-UF-2 terminology | **No** | Internally inconsistent in the source; both readings are kept (PS:5605) |
| "Signing the certificate does not itself prove that its tracing handles identify the same authorizers" | Yes, as a **boundary** | Used negatively: it is the reason Hermine cannot be the whole answer |

**Why the rest did not transfer.** The scheme answers the threshold-signing question; the programme's
question is a different one — binding authorizations to trace handles. So the borrowed parts are the
ones that describe *the committee and the interface*, and the parts that describe *the scheme's
security* were excluded. This is the split recorded as D-6, and it is why the DKG gap lands in an
adapter instead of inside the composition theorem.

---

### P6. Ringtail (IEEE S&P 2025; ePrint 2024/1113)

**Statement as used here.** Two rounds with a message-independent first message; 13.4 KB signature and
10.5 KB online at 1,024 signers; standard LWE in the random-oracle model with trusted key
generation; parameters under 2^60 signing queries.

**Borrow: Partial — sizing and interface only.**

*Borrowed:* the ≈ 13–14 KB hot-path estimate, which is the number the whole architecture is sized
against, and the "first message independent of the message" property, which is what makes a
one-online-round design possible.

*Not transferred:* the scheme's security, on three separate grounds the trail records — trusted key
generation, a `2^60` query bound that falls short of the target's `2^64`, and no binding of tracing
handles. One correction belongs here too: an external review asserted the scheme rests on a new
"AOM-MLWE" assumption, and the trail corrected it — the published result rests on standard LWE in the
ROM (PS:2420), with the AOM-MLWE technique belonging to a different CRYPTO'24 paper.

---

### P7. The compressed-oracle collision lemma (Isabelle AFP outline)

**Statement as used here.** min(1, 12(Q+154)³/2^h); at Q = 2^128 and h = 512, ≈ `2^-124.415`.

**Borrow: Partial, and the partiality is a citation defect rather than a scope choice.**

*Borrowed:* the cubic shape and the min(1, ·) cap, used as the quantum collision term in
p_bad^ideal ≤ ε_J + ε_bind + δ_run + 64(ε_MLWE + ε_SelfTargetMSIS + L_stat + Δ_spec).

*Not transferred:* the constant. The "+154" is transcribed exactly as found and is unsourced; the
trail's own arithmetic is insensitive to it (12·2^384/2^512 = `2^-124.415`), which is why the defect
does not change the number but does mean the citation cannot be checked. The source is an AFP outline,
not a paper, and the result is an *ideal-oracle component* statement, so it composes only inside the
ledger's frame.

---

### P8. ZKBoo (USENIX Security 2016)

**Statement as used here.** Three local checks suffice as the structure of the extraction argument.

**Borrow: Partial — a structural transplant.**

*Borrowed:* the three-check pattern, used at v1.36 to shape the concrete circuit extractor E* and
its 27 test groups.

*Not transferred:* the paper's own security analysis for its circuit language, and its concrete
commit-and-open instantiation. The trail needs a backend satisfying DFMS's premises (P1), and ZKBoo's
three checks are used as the *form* of the extractor rather than as its security proof. The fuller use
of the paper's Lemmas 1–3 and its `p_triv` term as a concrete backend belongs to
`domains/05-extraction-and-signature-reductions/`, not to this trail; here the borrow is the pattern only.

---

### P9. Collaborative MPC proving (Ozdemir, USENIX Security 2022)

**Statement as used here.** Map collaborative proving to a single proof, avoiding recursion.

**Borrow: Partial — a design pattern, taken as a direction.**

*Borrowed:* the idea that the 43-seat relation can be proved by a collaboratively computed single
proof rather than a recursive composition, which is what makes the 27,056 B slot conceivable at all
(PS2:375).

*Not transferred:* any theorem. The work is named as a way to avoid recursion, not as a construction
that meets the slot, and the v1.24 contents contract lists the collaborative prover as a
simplification rather than as an instantiated component.

---

### P10. DAPS / PAPS conditional disclosure

**Statement as used here.** Disclose predefined data when a predicate is violated — the pattern for an
audit secret released on conflict.

**Borrow: Partial.**

*Borrowed:* the conditional-disclosure pattern, which is the shape of the secret-quorum-sample
construction: a value recoverable only once two conflicting committed quorums exist.

*Not transferred:* the published constructions' assumptions. Lattice DAPS carries circular-security
and random-oracle assumptions that the trail does not import, and the trail's own construction is
stated in an ideal private-generation model rather than under those assumptions.

---

### P11. Refinement mappings (arXiv 1703.05121)

**Statement as used here.** Refinement mappings with history and stuttering variables are standard.

**Borrow: Partial — an idiom for formulating obligations.**

*Borrowed:* the stuttering/history-variable formulation used to state the crash obligations and the
five durable linearization points (PS:5363–5391).

*Not transferred:* the refinement-mapping metatheorem. No refinement proof was carried out, so the
idiom supplies the shape of the obligations and none of their discharge.

---

### P12. The machine-checked HotStuff-family result (arXiv 2203.14711)

**Statement as used here.** It proves a single configuration; configuration change is a separate proof
layer.

**Borrow: Scope-only.** No result from the paper is a premise of any step. What is borrowed is its
*scope statement*, which is used to justify a design decision (D-7: reconfiguration only at a
finalized barrier). A reader should not read "machine-checked" as transferring any machine-checked
property to this construction — it transfers an argument about where a proof boundary lies.

---

### P13. The multi-user loss term, log₂(N_u)

**Statement as used here.** With 64 seats and E epochs the multi-user loss is log₂(64E) ≈ 17.835 bits
at E = 3,650, giving a 157.835-bit single-user target at a `2^-140` budget.

**Borrow: Partial — the loss term, not the reduction.**

*Borrowed:* the standard multi-user bookkeeping term, and only that. The trail labels the whole row a
model-or-ledger estimate and says explicitly that it is "security-budget screening, not a substitute
for the concrete ML-DSA reduction" (PS:3221).

*Not transferred:* the concrete multi-user hybrid argument that would convert the screening number
into a bound. This is the row that has been independently recomputed (review #6 reproduced E = 3,653,
N_u = 233,792, 17.835, 145.835, 157.835, 174.165 and 142,287 B ≈ 139.0 KiB), so the *arithmetic* is
verified twice while the *reduction* remains absent. That combination — verified arithmetic, absent
reduction — is the most commonly misread state in this record.

---

### P14. Carolan–Poremba sponge one-wayness

**Statement as used here.** 80(T+1)²/2^min(r,c), for a single-round sponge under a uniform full-rate
input and an ideal invertible permutation.

**Borrow: Scope-only.** The result is recorded as an *alternative* accounting for the sampler change
and is not used in any final bound. It is kept because it bounds a case the trail cares about (a
single-round sponge) under hypotheses the deployed hash does not obviously meet.

---

### P15. Canetti–Goldreich–Halevi; Cojocaru et al.; Alagic et al.

**Statement as used here.** General limitations of random-oracle instantiation; quantum lifting with
explicit sponge collision bounds, some of which exceed 1; quantum sponge indifferentiability under an
ideal-permutation assumption.

**Borrow: Scope-only in all three cases.** They are cited to establish that no universal
SHAKE-versus-random-oracle distance is available (the refutation itself is arithmetic: the
distinguishing advantage is 1 − 2^-h) and to show what the alternatives would require. The
observation that some of Cojocaru et al.'s substituted bounds exceed 1 is recorded as a caution about
substituting bounds into a ledger, not used as a result.

---

### P16. Jackson–Miller–Wang (arXiv 2312.16619)

**Statement as used here.** The condition 2γη′n(m+k) < ⌊q/32⌋ fails for ML-DSA-87 even at η′ = 1.

**Borrow: Full as cited, used negatively.** The paper's own condition is applied exactly as stated and
found false: 6,304,047,104 < 261,888 fails by a factor of about 24,000. This is a *boundary* use — the
result is invoked to show that a published QROM bound cannot be quoted for the deployed parameter set,
not to bound anything.

---

### P17. Hoeffding's inequality

**Statement as used here.** Would bound a concentrated estimate over many trials.

**Borrow: None — the applicability was refuted, and this entry exists so that the name is not left
unresolved.** Three obstacles were recorded (PS2:1200–1243): the hybrid's AND-verification gives an
intersection bounded by min rather than by a product; the public state test accepts with Tr(ρ²) = 1 so
there is no gap Δ to concentrate; and Hoeffding requires independence that a single GHZ state does not
supply. The arithmetic that follows from granting it anyway (N = 128, Δ = 1/2 → `2^-92.33248`; Δ ≥
0.588705 needed for `2^-128`) is correct and was checked against the source's own formula form. The
failure is in the premise.

---

### P18. Watrous, and the resource-versus-security distinction

**Statement as used here.** BQP concerns decision problems; qubits are not security bits.

**Borrow: Contrast-only.** Cited to dispose of the GHZ construction's premise, not used in any bound.

---

## 4. Guise collisions

The same theory, or the same name, appearing in more than one form. A reader who meets these in
different documents should know they are one thing.

- **Grover, in three guises.** (a) As the *attack* that refutes the advantage target: 2^63 iterations
  against a 256-bit secret. (b) As the *cost model* of the replacement target: the gate work factor.
  (c) As the distinction between *query* and *gate* accounting: counting one gate per query lets
  AES-256 fall after 3·2^125 queries, so each query is charged its circuit cost. Same theorem, three
  different roles, and the third is what makes the target meaningful.
- **Collision bounds, in three exponents.** (a) The generic quantum collision exponent 2^(m/3) behind
  the 384-bit width. (b) The cubic term 12(Q+154)³/2^h in the extraction bound. (c) The multi-target
  cubic estimate (2⁶⁴)³/2^256 = `2^-64` in the pasted Category-5 material. These are three different
  computations that all contain a cube; only (a) is the BHT exponent.
- **Quorum counting, in three applications** — see T2's guise note.
- **"D1", "D2", "D3", in two senses.** In the decision register, D-1…D-17 are decisions. In the v1.43
  verdicts table, D1/D2 are the adopted target definitions and "Legacy D3" is the refuted advantage
  bound. Separately, this repository has a *domain* D3 which is a package of zero-knowledge carrier
  experiments. The three uses are unrelated and the collision is worth knowing before quoting a
  pointer.
- **"TS-UF-2" and "ts-suf-2".** One scheme's own paper uses both for what appears to be the same
  level. The trail keeps both readings rather than choosing, and this document follows it.
- **"AOM-MISIS" and "AOM-MSIS".** Technical term and presentation term for the same intermediate
  problem, with the technique itself belonging to a different paper from the scheme that uses it.

## 5. Named but not load-bearing

Recorded so that a reader does not treat citation volume as evidential weight.

- **Shor** (quant-ph/9508027): scope-only. It explains why the classical base must be replaced; no
  step of any proof depends on it.
- **NIST MAXDEPTH** (the three illustrative depth caps 2⁴⁰, 2⁶⁴, 2⁹⁶): scope-only. Used to frame the
  parallel-search work 2^216 / 2^192 / 2^160, which is a model comparison and not a security claim.
- **The project's method vocabulary** (Genesis table, GLYPH, MORPH/LEXON, NEXUS, SEMA,
  DISCOURSE/PRAGMA, CLOSURE/GENERATE, the three-projector "TRIAD" predicate, RIFT, GRAIL, QMC, and the
  quantum variants): no cryptographic weight. "None of them is a cryptographic assumption" (PS:323).
  RIFT survives as a filter and the three-projector predicate as a design sketch; neither is used in a
  proof.
- **Lattice Estimator, EasyCrypt, CryptoVerif, Coq, TLA+, Ivy, TLC/TLAPS**: recommended and never
  executed. No result on this trail rests on a tool.
- **The ≈ 515-entry amendment catalogue** in the operator-ledger material: its entries are parked,
  its source-property fields are uncertified, and the ledger itself states that the material is
  uncertified source text. It contributes no claim and is not used in any proof here.

## 6. Citations the source gives incompletely

Restated from the reference catalogue, because a partial borrow on top of an incomplete citation is
the weakest state a claim can be in:

- The **compressed-oracle lemma** (P7): an AFP outline with an unsourced "+154".
- **Carolan–Poremba** (P14): a group link rather than a paper identifier.
- **Cojocaru et al.** (P15): no identifier.
- **Barbosa et al.** (P2): the trail gives a repository location; the theorem number is supplied by a
  later project document, not by the trail.
- **DFMS** (P1): complete in the source as an arXiv identifier; the venue is supplied only through a
  later project document.
- **The pasted QPT-128 material**: site roots only — a search engine, a blog, an encyclopedia, a
  vendor page, and standards portals — so every claim in it is recorded as *incomplete in source*.
- **The Target-B and v1.7–v1.32 artefacts** (see `chronology.md` §XII–XIII): absent from the tree, so
  their numbers can be cited but not checked.
