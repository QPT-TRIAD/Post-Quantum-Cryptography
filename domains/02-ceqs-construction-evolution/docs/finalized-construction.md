# CE-QS v0.3 — Finalized Research Construction
## Sidecar-Free Conflict-Extractable Post-Quantum Quorum Signatures

**Status:** research construction with explicit primitive adapters and proof obligations.  
**Date:** 2026-09-08  
**Scope:** Target B only. This does not modify the audited Target-A v0.8 sidecar design.  
**Claim discipline:** This document finalizes the *construction specification and research choices*. It does **not** claim a completed cryptographic proof or a production implementation.

---

# 1. What v0.3 finalizes

The v0.2 record left five load-bearing items open:

1. multi-prover proof integration;
2. formal PQ pseudorandomness/non-frameability of CET;
3. trace-secret exposure;
4. total proof size;
5. ROM/QROM security.

A broad prior-art review changes their status as follows:

| Item | v0.2 | v0.3 |
|---|---|---|
| Multi-prover integration | open | **architecture fixed**: use a PQ threshold-ring/VOLE-in-the-Head base, not a threshold lattice signature |
| Hidden signer distinctness | delegated vaguely to \(\Pi\) | **syntax fixed**: deterministic key-binding tags + public duplicate rejection + base proof key-binding |
| CET trace algebra | tested | **construction fixed**, formal reduction outline specified |
| Non-frameability | open | **reduced to named assumptions**: base proof soundness/knowledge, PRF security, registry binding, challenge collision resistance |
| Trace-secret exposure | open | **key-separation rule fixed**; exposure does not reveal auth or mask key; re-key/removal policy fixed |
| Proof size | unknown | **acceptance gate fixed**, exact bytes remain benchmark-dependent |
| ROM/QROM | open | **upgrade path identified**: VOLE-in-the-Head QROM Fiat–Shamir analysis from CRYPTO 2025; CE-QS-specific proof still required |
| Asymptotically constant certificate | open | **not claimed**; v0.3 is \(O(q)\) in 256-bit anonymous tags |

The project therefore now has a concrete first sidecar-free construction target rather than a general research direction.

---

# 2. Qualified schools of thought

Only literature that resolves a specific CE-QS obligation is load-bearing.

## 2.1 Tetris / DAPT — traceability definition

**Use:** security semantics for anonymous-until-conflict tags.

Tetris introduces **Doubly-Authentication-Preventing Tags (DAPT)** with deterministic `Tag(sk, topic, message)` and public `TagTrace` on two different messages under one topic. Its threshold-ring traceability definitions require identifying guilty signers rather than merely detecting that misbehavior occurred.

**Borrowed principle:**

\[
\boxed{
\text{one tag is anonymous/pseudorandom; two conflicting tags are publicly traceable}.
}
\]

**Not borrowed:** Groth–Sahai, pairings, extendable shuffles, or ring/threshold extension. Fixed-epoch BFT does not need post-signature extendability.

---

## 2.2 Chiang–Damgård–Duro–Engan–Kolby–Scholl — PQ threshold ring + deterministic tags

**Use:** post-quantum hidden \(t\)-of-\(n\) authentication and public aggregation scaffold.

The CCS 2025 construction gives:

- PQ threshold ring signatures from symmetric assumptions and VOLE-in-the-Head;
- deterministic **key-binding** tags;
- pseudorandomness/anonymity arguments for those tags;
- a direct observation that deterministic tags prevent one key from contributing multiple times to a threshold signing instance;
- succinct aggregation via approximate lower-bound arguments of knowledge.

**Borrowed principle:**

\[
\boxed{
\text{hidden signer witness}
+
\text{deterministic key-binding tag}
+
\text{VOLEitH proof}.
}
\]

This is the base primitive family for CE-QS v0.3.

---

## 2.3 DAPS/PAPS — deliberate conditional disclosure is PQ-compatible

**Use:** proof strategy for the fact that "two forbidden authentications reveal signer information" is a valid cryptographic primitive, not an implementation flaw.

Lattice DAPS/PAPS establishes post-quantum constructions where signatures are normal until a predicate over signed messages is violated, at which point signer secret information becomes extractable.

**Borrowed principle:**

\[
\boxed{
\phi(M_0,M_1)=1
\Longrightarrow
\text{extract signer-linked secret}.
}
\]

For CE-QS:

\[
\phi_\tau(M_0,M_1)
=
[\tau_0=\tau_1]
\land
[M_0\neq M_1]
\land
[\mathsf{Conflict}(M_0,M_1)].
\]

---

## 2.4 Rate-limiting nullifiers / compact e-cash — two-point secret recovery

**Use:** algebraic shape of CET.

RLN uses a per-epoch line/polynomial: one signal reveals one point and preserves anonymity; multiple forbidden signals provide enough points to recover an identity secret. Classical compact e-cash uses the same broad "double spend causes identity recovery" school.

**Borrowed principle:**

\[
\boxed{
\text{single evaluation hides intercept;}
\quad
\text{two evaluations recover it}.
}
\]

CE-QS uses this only as an algebraic design pattern, not as a security assumption.

---

## 2.5 TAPS / accountable threshold signatures — privacy/accountability separation

**Use:** security-definition separation.

TAPS shows that threshold-signature privacy and accountability should be modeled as separate interfaces rather than conflated with unforgeability.

CE-QS adopts that separation but removes the secret tracing authority: tracing is triggered publicly by a conflicting certificate pair.

---

## 2.6 Set-membership / commit-and-prove literature

**Use:** registry binding.

Commit-and-prove set-membership work shows a modular way to prove:

\[
i\in R
\land
P(i,w)
\]

while hiding the member/index.

CE-QS does not require a general SNARK for this if the selected threshold-ring construction already proves hidden membership, but this literature is the fallback adapter if registry tuples become richer.

---

## 2.7 FAEST / VOLE-in-the-Head QROM analysis

**Use:** QROM upgrade path.

CRYPTO 2025 gives an improved QROM analysis and a Fiat–Shamir transform applicable to VOLE-in-the-Head-based signatures.

This does **not** automatically prove CE-QS in QROM, but it removes the earlier concern that VOLE-in-the-Head itself has no credible QROM route.

---

# 3. Registry

A fixed epoch publishes a canonical registry:

\[
R_e=
\{
(pk_i,X_i,K_i)
\}_{i=1}^{n}.
\]

For validator \(i\):

- \(sk_i\): authentication witness for \(pk_i\);
- \(x_i\in\mathbb F\): independent 256-bit tracing secret;
- \(k_i\): independent mask-PRF key;
- \(X_i=G_{\rm tr}(x_i)\): deterministic one-way trace commitment;
- \(K_i=G_{\rm mask}(k_i)\): deterministic public binding for the PRF key.

`G_tr` and `G_mask` must be efficiently provable in the selected VOLE-in-the-Head circuit. Prefer the same AES/block-cipher family already analyzed by the base PQ threshold-ring construction rather than introducing an unrelated hash gadget.

The three secrets MUST be domain separated:

\[
sk_i\neq x_i\neq k_i
\]

in the sense that no one is deterministically recoverable from another.

---

# 4. Field and tag encoding

Use a fixed binary field:

\[
\mathbb F=\operatorname{GF}(2^{256}).
\]

The irreducible polynomial defining the field is a protocol constant and part of the versioned encoding.

For conflict domain \(\tau\), define a 256-bit deterministic mask:

\[
r_{i,\tau}
=
F_{k_i}(\texttt{"CEQS-MASK-v1"}\parallel\tau)
\in\mathbb F.
\]

For message \(M\), define nonzero challenge:

\[
c=
H_F(
\texttt{"CEQS-CHAL-v1"}
\parallel
\tau
\parallel
H(M)
)
\in\mathbb F^\*.
\]

The conflict-extractable tag is:

\[
\boxed{
e_i(\tau,M)
=
r_{i,\tau}
+
c\,x_i.
}
\]

All field operations use the canonical 256-bit representation.

---

# 5. Why the tag is hidden once

Replace \(F_{k_i}(\tau)\) by a uniform field element \(R\).

Then:

\[
e_i=R+c x_i
\]

is uniform over \(\mathbb F\) for every fixed \(x_i,c\).

Therefore a one-tag distinguishing adversary gives a PRF distinguisher, up to the base proof's leakage.

Hybrid form:

\[
\boxed{
\operatorname{Adv}^{1\text{-}tag\text{-}hide}
\le
\operatorname{Adv}^{PRF}_F
+
\operatorname{Adv}^{ZK}_{\Pi}.
}
\]

This is the exact proof shape to mechanize.

---

# 6. Conflict extraction

For the same \(\tau\), two different messages give:

\[
e_0=r+c_0x_i,
\]

\[
e_1=r+c_1x_i.
\]

Hence:

\[
e_0-e_1=(c_0-c_1)x_i.
\]

If:

\[
c_0\neq c_1,
\]

then:

\[
\boxed{
x_i=
(e_0-e_1)(c_0-c_1)^{-1}.
}
\]

Public identity recovery is:

\[
G_{\rm tr}(x_i)=X_i.
\]

The registry maps \(X_i\) to validator \(i\).

---

# 7. Certificate syntax

For one accepted BFT vote statement:

\[
(\tau,M)
\]

with threshold \(q\), the final certificate is:

\[
\boxed{
\Sigma=
(
v,
e,
\tau,
H(M),
q,
E,
\Pi
).
}
\]

Where:

- `v` is construction/version;
- `e` is epoch;
- \(E=(e_1,\dots,e_s)\) is a canonical sorted list of anonymous CET tags;
- \(s\ge q\);
- every tag is distinct;
- \(\Pi\) is the selected PQ threshold-ring/VOLE-in-the-Head proof/aggregate.

No individual PQ signatures and no external accountability sidecar are required.

---

# 8. Distinctness — finalized

This point is no longer delegated to an expensive hidden pairwise-index proof.

For a fixed \((\tau,M)\), CET is deterministic:

\[
e_i(\tau,M)
=
r_{i,\tau}+c x_i.
\]

If the same signer contributes twice, it produces the same tag twice.

Therefore certificate verification requires:

\[
\boxed{
|\operatorname{set}(E)|=|E|.
}
\]

Duplicate public tags cause immediate rejection.

The base PQ threshold-ring relation additionally proves **key binding**: each accepted tag is associated with a valid hidden registered signing key.

Different honest validators collide on the same 256-bit tag only with negligible probability under pseudorandomness; malicious rogue-key/tag collision attempts are covered by registry key validation plus tag key-binding.

Thus threshold counting uses:

\[
\boxed{
\text{number of distinct valid key-bound CET tags}.
}
\]

This directly mirrors the deterministic-tag threshold-counting principle in the CCS 2025 VOLE-in-the-Head threshold-ring construction.

---

# 9. Exact relation proved by each anonymous contribution

For public instance:

\[
I=
(
R_e,\tau,H(M),e_{\rm tag}
)
\]

the hidden witness is:

\[
w=(i,sk_i,x_i,k_i).
\]

The relation is:

\[
\boxed{
\mathcal R_{\rm CEQS}(I;w)=1
}
\]

iff all conditions hold:

### Membership

\[
(pk_i,X_i,K_i)\in R_e.
\]

### Authentication-key ownership

\[
\mathsf{KeyRel}_{auth}(pk_i,sk_i)=1.
\]

### Trace-secret binding

\[
G_{\rm tr}(x_i)=X_i.
\]

### Mask-key binding

\[
G_{\rm mask}(k_i)=K_i.
\]

### Correct deterministic CET

\[
e_{\rm tag}
=
F_{k_i}(\tau)
+
H_F(\tau,H(M))x_i.
\]

The proof hides \(i,sk_i,x_i,k_i\).

The public tag is part of the Fiat–Shamir transcript so it cannot be replaced after proving.

---

# 10. Multi-prover integration — finalized architecture

Do **not** design one monolithic prover that knows all quorum secret keys.

Each signer independently creates an anonymous contribution:

\[
\pi_i=
(e_i,\pi_i^{\rm ZK})
\]

for the same public instance \((R_e,\tau,M)\).

The combiner:

1. verifies each contribution;
2. rejects duplicate CET tags;
3. retains \(s\ge q\) distinct accepted contributions;
4. applies the threshold-ring scheme's public aggregation procedure.

This follows the architecture of the post-quantum threshold-ring construction, where signing parties anonymously broadcast contributions for public aggregation.

The combiner never learns signer indices or witnesses.

The exact aggregation format depends on the selected implementation; CE-QS does not redefine its internal transcript unless the CET relation requires it.

---

# 11. Conflict extractor

Input:

\[
(\tau,M_0,\Sigma_0,M_1,\Sigma_1).
\]

Procedure:

1. verify both certificates;
2. require same epoch and same conflict domain;
3. require `Conflict(M0,M1)=1`;
4. compute \(c_0,c_1\);
5. reject the negligible `c0 == c1` case;
6. for every:

\[
e_a\in E_0,\qquad e_b\in E_1,
\]

compute:

\[
x^\*=
(e_a-e_b)(c_0-c_1)^{-1};
\]

7. evaluate \(G_{\rm tr}(x^\*)\);
8. output every registry match.

At \(q=43\), pair checks are:

\[
43^2=1849.
\]

Tracing is conflict-only and need not be optimized for the happy path.

---

# 12. Extraction completeness theorem

For:

\[
n=3f+1,\qquad q=2f+1,
\]

two valid quorum certificates have signer sets \(S_0,S_1\) satisfying:

\[
|S_0\cap S_1|\ge f+1.
\]

Soundness/key-binding of \(\Pi\) ensures every accepted CET corresponds to an actual hidden registered signer.

For every:

\[
i\in S_0\cap S_1,
\]

both certificates contain a valid CET generated from the same:

\[
(x_i,k_i,\tau)
\]

and different challenges \(c_0,c_1\).

Therefore the pairwise scan contains an extracting pair and returns \(x_i\).

Hence:

\[
\boxed{
|\mathsf{ExtractConflict}(\Sigma_0,\Sigma_1)|
\ge f+1
}
\]

except under the union of primitive failure events.

---

# 13. Trace soundness and non-frameability — finalized reduction target

Suppose extraction reports honest validator \(i\) even though \(i\) did not contribute to both accepted certificates.

At least one of the following must have occurred:

1. \(\Pi\) accepted a tag without a witness satisfying \(\mathcal R_{\rm CEQS}\);
2. the proof extractor/key-binding associated a tag with the wrong registry tuple;
3. \(G_{\rm tr}\) admitted an identity-breaking collision/second preimage;
4. the PRF/tag relation was violated;
5. the message challenges collided in a way that invalidates unique extraction.

Therefore the target bound is:

\[
\boxed{
\begin{aligned}
\operatorname{Adv}^{Frame}_{CEQS}
\le{}&
\operatorname{Adv}^{PoK/Sound}_{\Pi}\\
&+
\operatorname{Adv}^{KeyBind}_{\Pi}\\
&+
\operatorname{Adv}^{PRF}_{F}\\
&+
\operatorname{Adv}^{Bind}_{G_{\rm tr}}\\
&+
\operatorname{Adv}^{Coll}_{H_F}.
\end{aligned}
}
\]

This is the reduction that remains to be written formally.

The v0.2 algebra mutation tests already establish that wrong masks, absent signers, random forged field tags, duplicates and denominator failure do not create silent false identities at the algebra layer.

---

# 14. Quorum anonymity — finalized target game

The anonymity game must explicitly allow the public to see the CET multiset.

For two eligible signer sets \(S_0,S_1\) of the same cardinality, with no signer violating the conflict predicate in the challenge domain, the adversary receives a certificate from one set and guesses which.

Required:

\[
\boxed{
\operatorname{Adv}^{Anon}_{CEQS}
\le
\operatorname{Adv}^{Anon}_{TRS}
+
q\operatorname{Adv}^{PRF}_F
+
\operatorname{Adv}^{ZK}_{\Pi}.
}
\]

Reason:

- replace each CET mask with uniform randomness;
- then every CET is uniform in \(\mathbb F\);
- only the underlying threshold-ring transcript remains.

Same-message duplicate signing is publicly linkable because deterministic tags repeat. This leakage is intentional and is included in the anonymity definition.

---

# 15. Cross-topic unlinkability

For:

\[
\tau_0\neq\tau_1,
\]

the masks are:

\[
F_{k_i}(\tau_0),\quad F_{k_i}(\tau_1).
\]

Under PRF security they are independent pseudorandom values.

Consequently, subtraction does not cancel a common mask and the trace relation does not hold.

Target bound:

\[
\boxed{
\operatorname{Adv}^{CrossTopicLink}
\le
2\operatorname{Adv}^{PRF}_F
+
\operatorname{Adv}^{ZK}_{\Pi}.
}
\]

---

# 16. Trace-secret exposure — finalized policy and cryptographic boundary

A conflict deliberately exposes:

\[
x_i.
\]

It must **not** expose:

\[
sk_i
\]

or:

\[
k_i.
\]

Knowing \(x_i\) alone does not permit generation of a new accepted CET because:

\[
r_{i,\tau}=F_{k_i}(\tau)
\]

still requires \(k_i\), and an accepted certificate contribution additionally requires proof of \(sk_i\) and \(k_i\).

Therefore trace extraction is not ordinary signature-key extraction.

### Mandatory protocol reaction

Once validator \(i\) is publicly traced:

1. mark the validator Byzantine/slashed in the application state;
2. exclude it at the next safe membership transition;
3. rotate all CE-QS trace/mask material before any future admission.

### Optional stronger profile

Use epoch-evolving trace/mask keys:

\[
(x_i^{(e)},k_i^{(e)})
\]

and securely erase old secrets.

Forward-secure ring-signature literature provides the correct one-way key-evolution school of thought, but it is not required for v0.3 correctness because epoch configuration is already fixed and re-keyed.

---

# 17. Proof size — finalized engineering gate, not fabricated measurement

The tag cost is known exactly for the reference committee:

\[
q=43,\qquad |e_i|=32\text{ bytes}.
\]

Therefore:

\[
|E|=1376\text{ bytes}=1.344\text{ KiB}.
\]

The exact \(|\Pi|\) for the expanded CE-QS relation is **not known until implementation**.

The VOLE-in-the-Head paper demonstrates that practical proofs for AES/ring-related relations live in the kilobyte range, including a 5034-bit proof for one ring-signature relation and a 35,306-bit proof for a substantially richer anonymous-transaction example. Those values are evidence of feasibility, not CE-QS measurements.

v0.3 therefore freezes acceptance gates instead of inventing bytes:

### Green

\[
\boxed{
|\Sigma|\le16\text{ KiB}
}
\]

### Acceptable research prototype

\[
\boxed{
16<|\Sigma|\le32\text{ KiB}
}
\]

### Fail Target-B practical-compactness gate

\[
\boxed{
|\Sigma|>32\text{ KiB}.
}
\]

The 32-KiB cutoff is a project engineering decision: it remains far below the ~139-KiB raw ML-DSA-65 evidence signature payload of Target A while leaving room for the PQ proof.

No publication/novelty claim depends on this cutoff.

---

# 18. QROM — finalized upgrade plan

The CCS 2025 PQ threshold-ring construction is based on VOLE-in-the-Head and Fiat–Shamir.

CRYPTO 2025 subsequently provides:

- improved QROM analysis for VOLE-in-the-Head signatures;
- a QROM analogue of its concrete proof;
- a new Fiat–Shamir transform stated to be applicable to VOLE-in-the-Head-based signature schemes.

Therefore the research path is:

### Milestone R

Prove CE-QS using the base threshold-ring paper's original model.

### Milestone Q

Replace the Fiat–Shamir adapter with the CRYPTO 2025 QROM-compatible transform and redo:

- threshold unforgeability;
- anonymity;
- tag pseudorandomness;
- extraction soundness/non-frameability

under quantum oracle access.

This is a **credible proof route**, not an automatic inheritance theorem. CE-QS must still prove that its expanded relation and deterministic CET outputs satisfy the hypotheses of the chosen QROM transform.

---

# 19. Why no general vector commitment is in v0.3

Vector commitments and hidden-position set-membership proofs are qualified fallback technology, but they are not load-bearing in v0.3.

The fixed epoch already publishes \(R_e\), and the PQ threshold-ring base already proves hidden ring membership.

Adding a second commitment layer would:

- increase proof size;
- duplicate hidden-membership logic;
- create another assumption ledger.

Use a separate set commitment only if production requirements make the validator registry too large to include directly in the threshold-ring public instance.

For \(n\le64\), this is unnecessary.

---

# 20. Why TAPS/DeTAPS is not the construction

TAPS and DeTAPS are useful security-definition references because they separate privacy from accountability.

They are not the CE-QS solution because they require a tracing capability/authority or tracing workflow.

CE-QS requires:

\[
\boxed{
\text{public trace only after a conflicting certificate pair}
}
\]

with no permanent tracing secret.

---

# 21. Why traitor tracing is not the construction

Traitor tracing solves a different quantifier:

\[
\text{pirate decoder}
\rightarrow
\text{one traitor}.
\]

CE-QS needs:

\[
\text{two accepted conflicting quorum certificates}
\rightarrow
\text{common signer}.
\]

Fingerprinting/traitor-tracing codes may become relevant if the \(O(q)\) tag list is later compressed, but they are unnecessary for the first construction and introduce avoidable complexity.

---

# 22. Exact v0.3 security games

The primitive is:

\[
\mathsf{CEQS}
=
(
\mathsf{Setup},
\mathsf{Register},
\mathsf{Contribute},
\mathsf{Aggregate},
\mathsf{Verify},
\mathsf{ExtractConflict},
\mathsf{VerifyBlame}
).
\]

Required games:

1. **Correctness**
2. **Threshold unforgeability**
3. **Quorum anonymity**
4. **One-tag pseudorandomness**
5. **Cross-topic unlinkability**
6. **Conflict extraction completeness**
7. **Trace soundness**
8. **Non-frameability/exculpability**
9. **Key-binding / no duplicate threshold counting**
10. **Post-trace authentication unforgeability**
11. **QROM security** for the final profile

These games are independent; one combined "CE-QS secure" epsilon must not hide which property failed.

---

# 23. Main theorem target

Let:

\[
n=3f+1,\qquad q=2f+1.
\]

Assume:

- the PQ threshold-ring base is threshold-unforgeable and anonymous;
- its proof system is knowledge-sound/key-binding for \(\mathcal R_{\rm CEQS}\);
- \(F\) is a quantum-secure PRF in the final profile;
- \(G_{\rm tr},G_{\rm mask}\) are appropriately one-way/binding;
- \(H_F\) has the required collision properties;
- registry generation prevents rogue-key substitution;
- canonical encoding/domain separation is injective.

Then the target theorem is:

\[
\boxed{
\begin{aligned}
\operatorname{Adv}^{CEQS}_{forge}
&\le
\epsilon_{TRS}+\epsilon_{PoK}+\epsilon_{tag},\\
\operatorname{Adv}^{CEQS}_{frame}
&\le
\epsilon_{PoK}+\epsilon_{bind}+\epsilon_{PRF}+\epsilon_H,\\
\operatorname{Adv}^{CEQS}_{anon}
&\le
\epsilon_{TRS-anon}+q\epsilon_{PRF}+\epsilon_{ZK}.
\end{aligned}
}
\]

And for every two accepted conflicting certificates:

\[
\boxed{
|\mathsf{ExtractConflict}(\Sigma_0,\Sigma_1)|
\ge
|S_0\cap S_1|
\ge
f+1
}
\]

except under the corresponding primitive bad events.

This is the theorem to prove, not yet a proven theorem.

---

# 24. Experimental status after v0.2

The uploaded v0.2 artifacts already establish at the algebra layer:

- randomized same-topic extraction: PASS;
- cross-topic no-false-trace: PASS;
- wrong mask: fails closed;
- duplicate signer: algebra remains precise but confirms threshold distinctness needs certificate validation;
- forged random tag: no false registry identity;
- absent signer: not traced;
- challenge collision path: controlled/negligible event.

The important change in v0.3 is that duplicate signer enforcement is now part of **public certificate verification** through deterministic tag uniqueness plus base proof key-binding.

The remaining implementation task is not another algebra simulator. It is the actual \(\mathcal R_{\rm CEQS}\) VOLE-in-the-Head circuit.

---

# 25. Implementation work package

## WP1 — relation circuit

Implement:

\[
\mathcal R_{\rm CEQS}
\]

using the selected VOLE-in-the-Head library/reference code.

Measure gate/constraint counts for:

- hidden ring membership;
- auth-key relation;
- trace commitment;
- mask-key commitment;
- two PRF/AES blocks if needed for 256 mask bits;
- field multiply/add for CET.

## WP2 — anonymous contribution

Modify the threshold-ring partial-signature path so `e_tag` is a public output bound to the proof transcript.

## WP3 — verifier

Reject:

- invalid proof;
- wrong domain/version;
- duplicate CET tag;
- fewer than \(q\) accepted/key-bound distinct tags.

## WP4 — aggregation

Use the base scheme's public aggregation.

If its approximate-lower-bound aggregation requires \(q+\Delta\) inputs to prove \(q\), then:

\[
q_{\rm collect}=q+\Delta
\]

must become the BFT operational collection threshold.

This must never be hidden in benchmark code.

## WP5 — extractor

Implement the \(O(q^2)\) pair scan and registry lookup.

## WP6 — benchmark

At:

\[
n=64,\quad q=43
\]

record:

- contribution bytes;
- aggregate proof bytes;
- CET bytes;
- total certificate bytes;
- contribution generation latency;
- aggregation latency;
- verification latency;
- conflict extraction latency.

---

# 26. Go/no-go criteria

Continue toward publication only if all are met:

### Security

- no false trace in formal non-frameability proof;
- base anonymity survives public CET list;
- threshold distinctness is cryptographically bound, not merely parser-enforced;
- trace-secret exposure does not enable authentication forgery;
- no hidden tracer/master opening key.

### Size

\[
|\Sigma|\le32\text{ KiB}
\]

at \(n=64,q=43\).

### Latency

Public verification and aggregation must be compatible with the intended BFT block interval.

No precise latency target is frozen until the Target-A implementation supplies its block-time budget.

### Quantum model

A ROM proof is acceptable as an intermediate research milestone.

A production "post-quantum" claim requires the exact QROM/standard-model statement supported by the selected primitive stack.

---

# 27. What remains genuinely open

After v0.3, the following are still research rather than documentation gaps:

1. **Implement the expanded VOLE-in-the-Head relation.**
2. **Complete the game-based proofs.**
3. **Measure the real aggregate proof size.**
4. **Prove/adapt the final QROM transform.**
5. **Independent cryptographic review.**
6. **Asymptotic compression below \(O(q)\) anonymous tags**, if constant-size-in-\(n\) remains a requirement.

Everything else in the first \(n\le64\) construction is now specified well enough to implement and attack.

---

# 28. Final construction statement

The v0.3 candidate is:

\[
\boxed{
\textbf{Fixed-Epoch Conflict-Extractable PQ Threshold Ring Quorum Signature}
}
\]

with certificate:

\[
\boxed{
\Sigma=
(
\text{PQ threshold-ring aggregate proof},
\text{distinct anonymous CET tag list}
).
}
\]

Each CET is:

\[
\boxed{
e_i=
F_{k_i}(\tau)
+
H_F(\tau,H(M))x_i
\in GF(2^{256}).
}
\]

A single certificate hides signer identities.

Two conflicting certificates in the same BFT conflict domain provide two CET multisets.

Quorum intersection guarantees at least:

\[
f+1
\]

common signers.

For each common signer, the deterministic topic mask cancels and yields the dedicated trace secret, which maps to one registered validator.

No external sidecar and no permanent tracing authority are required.

The construction remains \(O(q)\) rather than asymptotically constant-size. At the current \(q=43\) target, however, the deterministic trace payload is only 1,376 bytes; the practical viability decision now depends almost entirely on the final VOLE-in-the-Head proof size and latency.

---

# 29. Primary-source ledger used to finalize v0.3

1. **Avitabile, Botta, Fiore — Tetris! Traceable Extendable Threshold Ring Signatures and More**  
   ESORICS 2025 / ePrint 2025/730.  
   Used for DAPT and threshold traceability semantics.

2. **Chiang, Damgård, Duro, Engan, Kolby, Scholl — Post-Quantum Threshold Ring Signature Applications from VOLE-in-the-Head**  
   ACM CCS 2025 / ePrint 2025/113.  
   Used for PQ hidden-threshold ring architecture, deterministic key-binding tags, threshold distinctness, public aggregation, and symmetric-key assumptions.

3. **Boneh, Kim, Nikolaenko — Lattice-Based DAPS and Generalizations: Self-Enforcement in Signature Schemes**  
   ACNS 2017.  
   Used for post-quantum conditional disclosure / predicate-authentication security pattern.

4. **Camenisch, Hohenberger, Lysyanskaya — Compact E-Cash**  
   EUROCRYPT 2005.  
   Used only for anonymous-use/double-spend-trace design pattern.

5. **Rate-Limiting Nullifier literature/implementation specification**  
   Used only for the two-point polynomial identity-recovery pattern.

6. **Boneh, Komlo — Threshold Signatures with Private Accountability (TAPS)**  
   CRYPTO 2022 / ePrint 2022/1636.  
   Used for privacy/accountability definition separation.

7. **Baum et al. — Shorter, Tighter, FAESTer: Optimizations and Improved (QROM) Analysis for VOLE-in-the-Head Signatures**  
   CRYPTO 2025.  
   Used for the QROM Fiat–Shamir upgrade path.

8. **Zero-Knowledge Proofs for Set Membership: Efficient, Succinct, Modular**  
   Used as fallback commit-and-prove membership technology; not load-bearing for the fixed \(n\le64\) v0.3 profile.

---

# 30. Bottom line

The broad search does **not** justify saying the sidecar-free primitive is proven.

It does justify a much stronger statement than v0.2:

> The remaining problem has been reduced to implementing and proving one explicit post-quantum relation inside a published PQ threshold-ring/VOLE-in-the-Head architecture. The trace algebra, threshold-intersection argument, duplicate-signer strategy, exposure policy, size gate, and QROM upgrade path are now fixed.

The next honest milestone is therefore **not another conceptual memo**.

It is:

\[
\boxed{
\textbf{CE-QS v0.4 = actual VOLE-in-the-Head relation implementation + measured proof bytes + first formal reductions.}
}
\]
