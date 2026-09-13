# PQ CE-QS: Adversarial Alternative-Strategy Report (companion to v1.18)

**Scope note.** v1.18 closed several questions (threshold semantics, memory, the column-vs-arbitrary-subset issue, whether an implemented lattice ZK route exists) and left four items explicitly open in its §7–§8 tables:

1. **Complete authorization-to-trace binding** (the joint relation that makes "authorized" and "traced" refer to the *same* 43 seats, not two independently valid but unrelated sets).
2. **32 KiB serialized-certificate budget.**
3. **128-bit QPT (quantum-polynomial-time) security qualification** of the composed construction and its trace parameters.
4. **Distributed production** — a malicious-secure proving protocol that makes progress with ≤21 of 64 validators Byzantine.

This report does not revisit resolved items and asserts no new construction, proof, or measurement. It takes a different starting method than v1.18's recommended path — v1.18 proceeds constructively ("start from LastRings + the June 2026 lattice ZK toolkit, try to fit the joint relation"). This report proceeds **adversarially**: for each open item, it first asks what a capable attacker or a hostile reviewer would exploit in the *straightforward* version of that path, and only then proposes a structural change motivated by closing that specific hole. The result is a single alternative architecture sketch, offered as a second candidate for the "next bounded experiment," not a replacement for v1.18's own recommendation.

---

## 1. Authorization-to-trace binding

### 1.1 What breaks the naive version
v1.18 §5.3 already proves the core failure mode: if authorization-for-*S* and trace-validity-for-*T* are separate proofs, an accepting pair only guarantees |S| = |T| = 43 in a 64-seat registry, not S = T. The guaranteed overlap is only

|S ∩ T| ≥ 43 + 43 − 64 = 22,

which is exactly the quorum's advertised recovery count — a strong signal that S = T is being *assumed*, not proved, in any design that keeps the two relations separate. A hostile reviewer would target this directly with a **mix-and-match forgery**: hold one genuinely authorized seat's public material, one genuinely traceable seat's material from a *different* identity, and submit both proofs against the same statement. If the verifier only checks "some 43-set authorized" and "some 43-set traceable" without a per-index equality constraint, this forgery is accepted.

A second, subtler attack is **handle reuse across proofs**: even inside a single joint relation, if the per-seat index used in the authorization sub-statement and the index used in the trace sub-statement are not forced to be the *same witness variable* (e.g., because the circuit compiler introduced two copies during composition), the binding degrades back to the two-proof case even though it looks like "one proof."

### 1.2 A different binding strategy
v1.18's Mode A/B both propose closing this by writing one monolithic relation that re-derives signature verification *and* trace-handle generation *and* index equality inside a single circuit. That is sound but maximizes circuit size, which is adversarial to blocker #2 (serialization). An alternative, structurally different approach:

**Commit-once, prove-opening.** At registration (or once per epoch), each seat *i* publishes a single lattice commitment

C_i = Commit(pk_i, tk_i, r_i)

binding its authorization key material and its tracing key material under one opening randomness r_i. This commitment is public and long-lived, not per-QC. The per-certificate relation then only needs to prove, for 43 hidden indices:

- knowledge of an opening of C_{i_j} to (pk, tk, r),
- a valid authorization witness under pk,
- a valid trace witness under tk consistent with the current message/domain,
- distinctness of the 43 indices.

The binding of "same seat" is now enforced once, outside the hot path, by the commitment itself — the joint relation only has to prove "I opened the same commitment for both facts," which is a much smaller equality-of-opening constraint than re-verifying two independent cryptographic relations end-to-end and then separately asserting index equality.

**Adversarial stress-test of this alternative before adopting it:**

- *Commitment malleability.* If Commit is not strongly binding under the specific ring/modulus used, an attacker may produce a second opening (pk, tk′) for the same C_i, re-attaching a different tracing key to a legitimately authorized public key. Requires an explicitly checked binding reduction for the chosen commitment, not an assumed one.
- *Cross-epoch replay.* Because C_i is long-lived, it must be domain-separated per epoch/version inside the opened statement (as v1.18 §6 already requires for x); otherwise a stale commitment from an earlier epoch could be replayed into a later relation.
- *Rogue-commitment / proof-of-possession.* Registration must force each party to prove knowledge of its own r_i and secret material at commit time, or a coalition can construct C_i as a function of another honest party's public commitment (a rogue-key-style attack ported to the commitment setting) to later claim shared credit or frame that party.
- *Non-frameability regression.* Moving the binding earlier does not remove the obligation in v1.18 §7: the trace witness must still require the actual signing/tracing secret, not merely a valid-looking opening, or an attacker with only pk_i (no si) could still frame seat i.

This is offered as a candidate that trades a larger one-time registration cost for a smaller per-certificate relation — directly relevant to blocker #2 — but it is not free: it adds a new commitment-binding assumption and a new registration-time proof obligation that v1.18's monolithic version does not need. Either binding strategy still requires the full obligation list in v1.18 §7 (chosen-message unforgeability, non-frameability reduction, etc.); commit-then-open changes *where* the binding is enforced, not *whether* every listed obligation must still be discharged.

---

## 2. 32 KiB serialization

### 2.1 What breaks the naive version
v1.18 §5.1 already shows the current hash-based (Binius-style) trace format has a **restricted native prefix of 46,192 bytes alone**, exceeding the entire 32,768-byte cap before any query values, Merkle paths, or terminal encoding are added. The arithmetic in that section is not adversarial per se, but the adversarial reading of it is important: *any* redesign that keeps a hash-based IOP/STARK-family backend inherits a proof-size floor that scales with the transcript's query complexity and Merkle-path depth, which is fundamentally the wrong asymptotic regime for a hard 32 KiB cap on a fixed, small (43-of-64) relation. Treating this as "an encoding problem to be optimized" is itself the failure mode v1.18 flags in its decision table: no query/path-only recoding closes a 17,728-byte gap that exists *before* queries are added.

### 2.2 A different strategy: change backend family, then budget top-down
Rather than trying to compress the existing format, adopt algebraic (lattice) succinct arguments — the family already flagged as the highest-priority path in v1.18 §4.1 — and treat the 28,480-byte remaining budget (32,768 − 4,288 header/handles) as a **hard top-down constraint on relation size**, checked before any prover run, per v1.18 §8's own recommended next step. Concretely:

| Budget item | Bytes | Note |
|---|---:|---|
| Header + 43 handles | 4,288 | Fixed, per v1.18 §3 |
| Proof-system commitments/openings | ? | Must be measured against the actual ported relation |
| Domain-separation / suite tag overhead | small, fixed | Part of the canonical frame in v1.18 §6 |
| **Total available for proof body** | **28,480** | Hard ceiling |

The adversarial question to ask of any lattice candidate before committing engineering time: LaBRADOR's cited 58 KB figure is for a ~1M-constraint R1CS instance unrelated to this relation (v1.18 §4.1). A CE-QS relation — 43 authorization checks (or 43 commitment-opening checks, per §1.2 above), registry membership, and 43 trace-handle derivations — has an unknown, unmeasured constraint count. The only defensible use of that 58 KB figure is as a *rough scaling reference*, not a size estimate: if proof size scales sub-linearly (roughly √ or log in constraint count for this proof family), a relation with a few thousand constraints per seat could plausibly land well below 58 KB, but "plausibly" is not "measured," and v1.18 is explicit that no sub-28,480-byte complete proof is established by any abstract reviewed.

**Two structural levers to pull, each with an adversarial caveat:**

- *Batch membership instead of 43 separate membership checks.* Prove one aggregate statement — "all 43 hidden indices are members of the registry and mutually distinct" — via a single batched opening against a vector commitment to the registry, instead of 43 independent membership sub-proofs. Adversarial check: naive batching (e.g., a single random linear combination of 43 openings) can leak soundness if the batching coefficients are not properly bound to the transcript (a batched proof can be soundness-degraded to something checkable by an attacker who controls which indices collide under the batching relation); this needs the same treatment as Orthus's batch-verification claims (v1.18 §4.1) — a stated, checked soundness-error analysis for *this* batch size and field, not an assumed one.
- *Amortize the trace relation across seats* rather than deriving it 43 independent times. Adversarial check: amortization schemes typically assume identical structure across instances; the trace relation must be checked to actually be structurally identical for every seat (same field, same hash calls) or the amortization argument does not apply and silently underclaims cost.

### 2.3 Explicit falsification gate
Before any large prover run: produce the relation inventory v1.18 §8 already calls for (private-variable count, constraint count, hash-call count, selection/distinctness constraints) and compute a conservative size estimate under the *chosen* backend's actual scaling law — not a borrowed figure from an unrelated benchmark. If the conservative estimate exceeds 28,480 bytes, stop before implementing, per v1.18's own stated policy that "a favorable estimate is only permission to measure, not an acceptance result" (and an unfavorable one is permission to stop early).

---

## 3. 128-bit QPT security

### 3.1 What breaks the naive version
The naive failure mode, already named in v1.18 §7, is **parameter transplantation**: taking a component's stated security level (e.g., a 116-bit or 123-bit figure from the spartan-whir benchmark, or a classical ROM bound from a ported signature scheme) and assuming it composes into a 128-bit QPT bound for the full system "because the pieces are individually strong enough." An adversary does not need to break any single component to break this: they only need the *seam* between components — the point where one paper's theorem hypotheses are not actually satisfied by how the artifact is used — to be unverified. v1.18 is explicit that this composition has not been checked for any candidate.

A second failure mode is **quantum-vs-classical conflation**: a classical random-oracle proof under a "conjecturally quantum-hard" assumption, or a Grover-vulnerable generic-search bound quietly treated as already discounted, both silently understate the true quantum security level. v1.18 §7 flags the same issue for the local trace parameters: "a native configuration labeled 96 cannot be relabeled 128."

### 3.2 A different strategy: build the loss ledger before, not after, implementation
v1.18's implicit ordering is construct-then-qualify: build the joint relation, then check whether its security composes. The adversarial alternative is to invert that order — build the **concrete security-loss ledger first**, as a standalone artifact, and only commit engineering effort to a backend whose ledger can plausibly close at 128 bits. This avoids the specific risk visible across almost every source in v1.18 §4: paper after paper reports "the exact CE-QS port and security qualification remain open," which is exactly the failure mode of discovering the composition gap only after the implementation is built.

A minimal loss ledger for this system needs, at minimum, one row per reduction step actually used:

| Step | Hardness/assumption | Model | Concrete loss source |
|---|---|---|---|
| Commitment binding (§1.2) or signature EUF-CMA | MSIS / MLWE or scheme-specific | (Q)ROM or standard model | Reduction tightness, number of queries |
| Trace-handle collision resistance | Hash/commitment collision resistance | QROM | Grover-adjusted search bound |
| Joint-relation soundness | Proof-system knowledge soundness | (Q)ROM, straightline extraction | Extraction slack, transcript size |
| Non-frameability | Application-specific reduction | — | Whether it covers adaptive corruption/exposure |
| Distributed-proving privacy (§4) | MPC/collaborative-ZK security | Malicious/UC | Corruption threshold, simulator loss |
| Composition of the above | — | — | Sum of all above losses vs. 128-bit target with slack |

This is the same obligation table as v1.18 §7, restated as a build order rather than a checklist: **no parameter set is pinned until every row has an actual number**, not a name. This directly targets the local audit already flagged as unresolved in v1.18 §7 — dimension 256, q = 65,536, p = 256, and the derived row-exposure count 672,352 — which needs to be matched against an applicable small-modulus LWR reduction (e.g., Bogdanov et al.) with concrete sample/noise conditions, not treated as self-evidently 128-bit because it "looks large."

### 3.3 Adversarial red-team check for the ledger itself
The ledger is only useful if it is stress-tested against the strongest attacker the model allows: adaptive corruption (attacker chooses which validators to corrupt *after* seeing partial transcripts), tracing-secret exposure (must not degrade authorization security, per v1.18 §3's non-frameability requirement — a proof of tracing-secret possession must not become a forgeable vote, exactly the shortcut v1.18 §1's decision table already rejects), and quantum access to any oracle the proof system exposes (QROM, not ROM, throughout). A ledger built only against a classical or static-corruption adversary should be treated as disqualifying, not merely incomplete.

---

## 4. Distributed production under ≤21 Byzantine faults

### 4.1 What breaks the naive version
v1.18 §4.7 already surveys collaborative-ZK and identifiable-abort literature and concludes none of it is an "automatic wrapper" for the specific relation here. The adversarial reading: a naive port directly runs the full joint relation (§1–§3 above) as one large multi-party computation among all 43+ contributing validators. This conflates two different liveness problems:

1. **Agreeing on which 43-plus seats will participate** — a threshold-signature-style problem, relatively mature (Ringtail, Efficient Threshold ML-DSA, Unmasking TRaccoon's identifiable-abort machinery, all surveyed in v1.18 §4.6–4.7).
2. **Jointly proving the expensive relation without centralizing any party's secret** — a collaborative-ZK problem, less mature at this scale and relation size per v1.18's own assessment.

Running both inside one protocol maximizes the attack surface: a malicious validator who wants to grief the system gets to choose *when* to abort — before the cheap agreement step (cheap to recover from) or during the expensive joint-proving step (expensive to recover from, since restarting means redoing proof work already sunk). A naive single-phase design lets the attacker always pick the expensive failure point.

### 4.2 A different strategy: phase-separate agreement from proving, over-provision the second phase
1. **Phase 1 — participant agreement.** Run a cheap identifiable-abort threshold protocol (in the style of Unmasking TRaccoon's abort accounting, v1.18 §4.7) to fix a candidate set of *k* > 43 seats (e.g., 46–50) willing and able to contribute, with malicious aborters identifiable and excludable at low cost. Progress here only requires enough honest, responsive validators to reach 43 eligible candidates out of the pool, which is easier than requiring exactly 43 specific ones to survive the expensive phase.
2. **Phase 2 — collaborative proving.** Run the joint relation (§1's binding, sized per §2's budget, qualified per §3's ledger) only among the already-agreed candidate set, with a bounded timeout. If fewer than 43 of the candidates remain responsive by the timeout, fall back to a replacement round drawn from the phase-1 surplus rather than re-running phase 1 from scratch.

**Adversarial checks specific to this split, before it can be called an improvement rather than just a different design:**

- *Does splitting weaken any proof?* The joint relation's security (§1, §3) must not implicitly assume the participant set was chosen through the same protocol that proves the relation; if phase 1's agreement transcript is later usable as an oracle by an attacker in phase 2 (e.g., leaking which specific seats are "live"), that must be accounted for in the phase-2 privacy argument, not assumed away.
- *Grief cost asymmetry.* The whole point of the split is to make the attacker's cheapest griefing point (aborting in phase 1) also the cheapest point for defenders to recover from. This must actually hold under the specific fault threshold (21 of 64): worked out fault-tolerance arithmetic — not intuition — is needed to confirm that a pool of 46–50 candidates has a high enough probability of yielding 43 honest, responsive participants given ≤21 total Byzantine validators in the full 64-seat registry.
- *Progress vs. security-with-abort.* v1.18 §3 explicitly separates "security with abort" from "eventual completion": phase separation improves the *expected* cost of completion but does not by itself supply a liveness proof. A replacement-round bound and a worst-case retry count under adversarial scheduling still need to be stated and justified against the network-timing assumptions actually used.
- *Centralization re-introduced by the back door.* Any coordinator used to run phase 1 or manage the phase-1→phase-2 handoff must not become a de facto centralized collector of private signer material, which v1.18 §3 rules out explicitly.

---

## 5. Combined alternative architecture (summary)

None of §1–§4's proposals stand alone; they are coupled: the commit-then-open binding (§1) is what makes the batched-membership budget (§2) plausible; the two-phase distributed protocol (§4) only inherits a sound privacy argument if that argument is written against the actual phase-2 participant-selection process, which the loss ledger (§3) must include as one of its rows, not treat as external to the cryptography. As a single sketch:

1. Long-lived per-seat commitments binding authorization and tracing material (§1.2), domain-separated per epoch.
2. A lattice succinct-argument relation over 43 hidden opened commitments plus a batched registry-membership check (§2.2), sized against the 28,480-byte remainder before any prover is built.
3. A concrete security-loss ledger (§3.2) covering every reduction step above, including the distributed-proving step, checked against an adaptive-corruption, QROM-access, tracing-exposure adversary before parameters are pinned.
4. A two-phase distributed-production protocol (§4.2): cheap identifiable-abort agreement on an over-provisioned candidate set, followed by bounded collaborative proving among the agreed set, with a replacement round rather than a full restart on timeout.

### 5.1 What this alternative does *not* claim
Consistent with v1.18's own reproducibility discipline: this is a research sketch, not an implementation, proof, or measurement. It has not been checked for the specific concrete constraint count, has no measured proof size, no completed loss ledger with actual numbers, and no distributed-proving prototype. Every "adversarial check" listed above is a requirement the alternative must still discharge, not evidence that it already has.

### 5.2 Falsification checklist (what would kill this alternative specifically)
- A relation inventory (§2.3) showing the commit-then-open relation's constraint count still yields a conservative size estimate above 28,480 bytes.
- A demonstrated soundness gap in the batched-membership or amortized-trace constructions under the actual field/parameters chosen (§2.2).
- A loss-ledger row (§3.2) that cannot be closed under QROM/adaptive-corruption assumptions at the chosen parameters without exceeding the 128-bit budget.
- A fault-tolerance calculation (§4.2) showing the 46–50-candidate over-provisioning does not, in fact, meaningfully improve expected completion probability at the 21-of-64 threshold.

Any single one of these is sufficient to reject this alternative in favor of v1.18's own recommended path, or a third option not considered here — which is the point of stating them explicitly rather than only afterward.

---

## Sources referenced

This report draws its factual claims (measured byte figures, footnote-cited results, decision-table entries) entirely from *PQ CE-QS v1.18: research qualification and remaining blocker decisions* (research cutoff 2026-09-09); no new literature search was performed. Source attributions (LastRings, LaBRADOR, Orthus, Unmasking TRaccoon, Ringtail, Efficient Threshold ML-DSA, Bogdanov et al., spartan-whir) follow the numbering and bibliography already established in that document's §4 and Sources section.
