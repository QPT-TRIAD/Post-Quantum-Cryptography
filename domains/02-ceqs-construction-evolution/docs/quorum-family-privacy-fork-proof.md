# CE-QS v0.7 — Quorum-Family and Privacy-Fork Proof
## What Can Be Compact, What Can Be Anonymous, and What BFT Actually Requires

**Status:** proof continuation from v0.6.  
**Date:** 2026-09-08.  
**Track:** Target B only.  
**Claim discipline:** this document proves two new combinatorial/composition theorems and uses them to narrow the cryptographic target. It does not claim a practical <32-KiB PQ aggregate has been constructed.

---

# 1. Why this proof layer is necessary

v0.6 reduced hidden-signer CE-QS to a **CET-liftable exact anonymous threshold backend**.

The next literature candidate, LoTRS, has a different structure:

- public keys form a \(T\times N\) table;
- one valid hidden signer set is one column;
- a two-round lattice multisignature enforces threshold participation;
- a 1-out-of-\(N\) proof hides which column signed.

This is substantially more efficient than generic lattice \(T\)-out-of-\(N\) threshold-ring constructions.

However, ordinary BFT does not begin with a fixed small family of admissible quorum columns.

For:

\[
n=3f+1,\qquad q=2f+1=n-f,
\]

**any** \(q\)-subset of validators may be the only all-honest quorum after \(f\) arbitrary faults.

This creates a combinatorial compatibility question before cryptography even begins.

---

# 2. Definitions

Let:

\[
V=\{1,\ldots,n\}
\]

be the validator set.

Let:

\[
\mathcal B_f
=
\{B\subseteq V:|B|=f\}
\]

be the allowed Byzantine/crash fault sets of maximum size.

Let:

\[
\mathcal F
\subseteq
2^V
\]

be the family of signer sets admitted by a structured quorum-signature backend.

For a direct BFT finality backend, every:

\[
Q\in\mathcal F
\]

must satisfy:

\[
|Q|\ge q.
\]

### Byzantine-independent liveness coverage

We say \(\mathcal F\) has **full \(f\)-fault coverage** if:

\[
\forall B\in\mathcal B_f,\
\exists Q\in\mathcal F:
Q\subseteq V\setminus B.
\]

This means progress never needs a faulty validator's participation.

---

# 3. Structured Quorum Coverage Theorem

### Theorem 3.1

Let:

\[
q=n-f.
\]

If:

1. every admissible signer set has size at least \(q\); and
2. \(\mathcal F\) has full \(f\)-fault coverage;

then:

\[
\boxed{
\{V\setminus B:B\in\mathcal B_f\}
\subseteq
\mathcal F.
}
\]

Consequently:

\[
\boxed{
|\mathcal F|
\ge
\binom nf
=
\binom nq.
}
\]

### Proof

Fix arbitrary:

\[
B\in\mathcal B_f.
\]

By full fault coverage there exists:

\[
Q\in\mathcal F
\]

such that:

\[
Q\subseteq V\setminus B.
\]

But:

\[
|V\setminus B|
=
n-f
=
q.
\]

By assumption:

\[
|Q|\ge q.
\]

Since \(Q\) is a subset of a set containing exactly \(q\) elements:

\[
|Q|=q
\]

and necessarily:

\[
Q=V\setminus B.
\]

Because \(B\) was arbitrary, every complement of an \(f\)-subset must belong to \(\mathcal F\).

Complementation is injective, so there are:

\[
\binom nf
\]

such quorum sets.

\[
\blacksquare
\]

---

# 4. Reference 64-validator consequence

For:

\[
n=64,\qquad f=21,\qquad q=43,
\]

a structured backend preserving ordinary arbitrary-\(f\)-fault liveness requires at least:

\[
\boxed{
\binom{64}{21}
=
41,107,996,877,935,680
}
\]

admissible quorum sets.

In information terms:

\[
\log_2 \binom{64}{21}
\approx
\boxed{55.190\text{ bits}}.
\]

Thus a LoTRS-like direct structured-column representation would require at least approximately:

\[
2^{55.19}
\]

candidate columns if one column is to represent each possible all-honest 43-validator quorum.

This is a **combinatorial lower bound**, independent of lattice assumptions or proof-system efficiency.

---

# 5. LoTRS Trichotomy

Consider direct use of a structured threshold-ring backend whose admissible signer set has exactly \(T\) signers.

## Case A — \(T>q\)

After \(f\) faults there may be only:

\[
n-f=q
\]

honest/available validators.

Then:

\[
T>q
\]

requires a faulty validator to participate.

Therefore Byzantine-independent liveness fails.

---

## Case B — \(T=q\)

Theorem 3.1 applies.

To tolerate every \(f\)-subset of faulty validators, the structured family needs at least:

\[
\binom nf
\]

columns.

For 64/21/43 this is:

\[
41,107,996,877,935,680.
\]

The structured efficiency advantage disappears catastrophically at the policy-description level.

---

## Case C — \(T<q\)

One structured threshold-ring signature authenticates fewer than the BFT quorum threshold:

\[
T<q.
\]

It therefore does not by itself establish the BFT finality predicate.

A second exact threshold layer must certify that enough structured groups or individual validators participated.

That returns the system to an exact aggregation problem.

---

# 6. Corollary — direct LoTRS is not a drop-in backend for ordinary BFT

### Corollary 6.1

A one-column structured threshold-ring scheme cannot simultaneously preserve:

1. arbitrary \(f\)-fault Byzantine-independent liveness;
2. ordinary quorum threshold:

\[
q=n-f;
\]

3. a polynomial-size fixed family of admissible columns,

unless the fault/quorum model is restricted.

### Proof

Cases A–C exhaust \(T>q,T=q,T<q\).

\[
\blacksquare
\]

This is not a defect in LoTRS.

LoTRS is intentionally designed for applications where the **approval pattern itself is structured**.

It means ordinary BFT is not such an application unless the consensus policy is changed.

---

# 7. When structured LoTRS *can* fit CE-QS

Let:

\[
\mathcal D\subseteq 2^V
\]

be a restricted fault domain.

Let:

\[
\mathcal F
\]

be a structured quorum family.

A structured CE-QS backend is sufficient when:

### Coverage

\[
\forall B\in\mathcal D,\
\exists Q\in\mathcal F:
Q\subseteq V\setminus B.
\]

### Safety intersection

\[
\forall Q_0,Q_1\in\mathcal F:
|Q_0\cap Q_1|>f.
\]

Then any two structured finality certificates have an honest intersection and CET conflict extraction still works.

Thus LoTRS remains qualified for:

- role-based committees;
- one delegate per organization/region;
- structured fault models;
- consensus protocols whose admissible quorums are explicitly restricted.

It is **not** a generic replacement for ordinary unstructured 43-of-64 quorum voting.

---

# 8. The Privacy Fork

The structured-quorum result motivates a more basic question:

> Does Target B actually require the signer set to remain hidden in a non-conflicting certificate?

If the answer is **no**, the conflict-extraction problem becomes dramatically simpler.

Define a second construction target:

\[
\mathsf{CEQS\text{-}Public}.
\]

Certificate:

\[
\boxed{
\Sigma_{\rm pub}
=
(v,e,\tau,H(M),B,\sigma_{\rm MS})
}
\]

where:

- \(B\in\{0,1\}^n\) is the signer bitmap;
- \(\operatorname{wt}(B)\ge q\);
- \(\sigma_{\rm MS}\) is an exact post-quantum multisignature bound to:
  - the exact message;
  - the exact selected public keys / bitmap.

For:

\[
n=64,
\]

the bitmap is only:

\[
\boxed{8\text{ bytes}}.
\]

No CET tags are required.

No accountability sidecar is required.

---

# 9. Public-Signer Exact Multisignature Interface

Let:

\[
\mathsf{MS}
=
(
KeyGen,
Sign,
Aggregate,
Verify
).
\]

Required security properties:

## P1. Independent registered keys

Validators generate independent signing keys.

## P2. Rogue-key security / proof of possession or equivalent

An adversary cannot choose malicious public keys that make another validator appear in an aggregate.

## P3. Exact signer-set binding

If:

\[
Verify(R,M,B,\sigma)=1,
\]

then every identity whose bit is 1 in \(B\) is cryptographically represented in the aggregate, except with forgery advantage.

The aggregate cannot be replayed under another bitmap.

## P4. Threshold check

Verifier explicitly checks:

\[
\operatorname{wt}(B)\ge q.
\]

---

# 10. Public-Signer Certificate Soundness Theorem

### Theorem 10.1

If P1–P4 hold, every accepted:

\[
\Sigma_{\rm pub}
\]

contains at least:

\[
q
\]

distinct registered signer authorizations, except with multisignature forgery/key-binding advantage.

### Proof

Verifier requires:

\[
\operatorname{wt}(B)\ge q.
\]

A bitmap has no duplicate positions.

By P3, every set bit corresponds to a real aggregate signer.

Therefore at least \(q\) distinct registered identities authorized \(M\).

\[
\blacksquare
\]

---

# 11. Public Conflict Extraction Theorem

For two accepted conflicting certificates:

\[
(B_0,\sigma_0),
\qquad
(B_1,\sigma_1),
\]

define:

\[
\boxed{
B_\cap=B_0\land B_1.
}
\]

By Theorem 10.1:

\[
|S_0|,|S_1|\ge q.
\]

Hence:

\[
|S_0\cap S_1|
\ge
2q-n.
\]

Therefore:

\[
\boxed{
\operatorname{wt}(B_\cap)
\ge
2q-n.
}
\]

For:

\[
n=3f+1,\qquad q=2f+1,
\]

we get:

\[
\boxed{
\operatorname{wt}(B_\cap)
\ge
f+1.
}
\]

So conflict extraction is literally:

```text
blame_bitmap = certificate_0.bitmap AND certificate_1.bitmap
```

No tracing algebra is necessary.

---

# 12. Public Non-Frameability Theorem

Suppose honest validator \(i\) did not authorize \(M\), but an accepted certificate has:

\[
B[i]=1.
\]

By exact signer-set binding P3, this constitutes:

- multisignature forgery;
- rogue-key/key-binding failure;
- or violation of the underlying registered-key assumption.

Thus:

\[
\boxed{
Adv^{Frame}_{Public}
\le
Adv^{MS-Forge}
+
Adv^{RogueKey}
+
Adv^{SetBind}.
}
\]

For conflicting certificates, an honest validator in:

\[
B_0\land B_1
\]

is therefore publicly proven to have authorized both exact statements, modulo the same cryptographic failure events.

---

# 13. BFT Safety Corollary for the public-signer variant

Assume at most \(f\) Byzantine validators and honest no-double-vote state.

If two conflicting public-signer certificates verify, their intersection contains at least:

\[
f+1
\]

identities.

At least one is honest.

But an honest validator does not authorize both conflicts.

Contradiction unless:

- multisignature security failed;
- signer persistent state rolled back;
- or base BFT safety failed.

Hence:

\[
\boxed{
Adv^{Conflict}_{Public}
\le
2Adv^{MS-Forge}
+
Adv^{SetBind}
+
\epsilon_{\rm rollback}
+
Adv^{BaseSafety}.
}
\]

This is a complete composition theorem conditional on the exact multisignature primitive.

---

# 14. Theorem — where CE-specific difficulty actually comes from

### Theorem 14.1 — Privacy Separation

For a fixed \(n\le64\) BFT committee:

- **without signer-set privacy**, conflict accountability reduces to exact multisignature signer-set binding plus an \(n\)-bit bitmap;
- **with signer-set privacy**, a valid certificate must hide the quorum while retaining a latent relation enabling conflict-only extraction.

Therefore CET/DAPT-style cryptography is needed for **privacy-preserving accountability**, not for conflict accountability by itself.

### Consequence

The Target-B problem should be split into:

\[
\boxed{
\mathsf{Target\ B_0}
=
\text{compact exact PQ multisignature + public signer bitmap}
}
\]

and:

\[
\boxed{
\mathsf{Target\ B_1}
=
\text{compact exact PQ quorum + hidden signers + conflict-only extraction}.
}
\]

The current CET research solves the trace layer needed by \(B_1\).

It is unnecessary for \(B_0\).

---

# 15. Current PQ multisignature evidence for Target \(B_0\)

Synchronized PQ multisignatures are explicitly designed for blockchain consensus and independent keys.

## Chipmunk

Published lattice synchronized multisignature.

Reported:

\[
8192
\]

signatures aggregated to approximately:

\[
136\text{ KB}
\]

at its stated 112-bit security configuration.

This proves the primitive class is real, but does not establish the CE-QS 32-KiB project gate at \(n=64\).

## Lemur

2026 synchronized PQ multisignature.

Its public artifact reports approximately:

\[
201.2\text{ KB}
\]

for an aggregate at:

\[
N=1024.
\]

Again, this confirms exact independent-key PQ aggregation is available, but not the desired size at the reported configuration.

Neither reported number is extrapolated to \(N=64\) here.

The exact 64-validator benchmark must be run from the implementations.

---

# 16. Falcon + succinct-proof aggregation branch

Another exact public-signer direction aggregates ordinary Falcon signatures using lattice succinct proofs.

Published LaBRADOR aggregation reports approximately:

- 93 KB for 500 Falcon-512 signatures with salts;
- 73 KB without salts;
- 120/80 KB at 1000 signatures;
- 165/85 KB at 2000 signatures.

This is proof that a generic PQ signature-plus-proof aggregation architecture is viable.

It does not provide a published 43-signature number sufficient to claim the 32-KiB gate is met.

This branch remains a benchmark candidate for \(B_0\), not a completed solution.

---

# 17. Monotone-Policy Aggregate Signatures — the asymptotic ideal

EUROCRYPT 2024 defines aggregate signatures for monotone policies.

A threshold predicate:

\[
\sum_i B_i\ge q
\]

is a monotone policy.

The paper gives succinct aggregates whose size is independent of the number of signers and succinct verification when all signers authenticate the same message.

This is asymptotically almost exactly what a BFT QC wants.

However:

- the constructions are theoretical BARG-based primitives;
- no practical CE-QS-sized post-quantum implementation is established here;
- hidden policy satisfaction alone does not give conflict accountability.

For \(B_0\), expose the signer bitmap.

For \(B_1\), a future policy aggregate must be augmented with the same-hidden-set CET relation.

Thus monotone-policy aggregation provides a useful **upper-level target architecture**, but not today's practical backend.

---

# 18. Structured anonymity versus arbitrary quorum anonymity

LoTRS's efficiency comes from hiding one member of a small admissible signer-set family.

CE-QS \(B_1\) currently asks for anonymity over arbitrary \(q\)-subsets:

\[
S\in\binom Vq.
\]

Theorem 3.1 demonstrates that these are fundamentally different policy spaces under arbitrary BFT faults.

This explains why structured threshold-ring systems cannot be treated as direct drop-in evidence for arbitrary-quorum hidden-signature feasibility.

---

# 19. Backend decision after v0.7

## For \(B_0\) — public signer set

Stop using threshold-ring constructions.

Benchmark in this order:

1. Lemur at actual \(n=64\);
2. Chipmunk at actual lifetime/message-budget parameters;
3. Falcon + LaBRADOR/LaZer aggregation;
4. hash-based succinct-argument aggregation.

Certificate remains:

\[
(bitmap,\sigma_{\rm aggregate}).
\]

The accountability proof is already complete.

---

## For \(B_1\) — hidden signer set

Continue CET.

Backend candidates:

1. exact CET-liftable PQ threshold-ring aggregate;
2. a future practical monotone-policy aggregate plus CET same-set proof;
3. structured LoTRS only if the BFT fault/quorum policy itself becomes structured.

Do not treat LoTRS as a direct arbitrary-quorum backend.

---

# 20. New lower-bound interpretation

The earlier information-theoretic observation said an exact public arbitrary signer set needs roughly:

\[
\log_2\binom nq
\]

bits in general.

For the fixed 64-validator implementation, however, a bitmap uses exactly:

\[
64\text{ bits}=8\text{ bytes}.
\]

Therefore **signer-set metadata is not the practical compactness problem at \(n=64\)**.

The hard part is the PQ proof/signature object.

This matters:

\[
\boxed{
\text{do not spend cryptographic complexity hiding 8 bytes unless signer privacy is an explicit product/security requirement.}
}
\]

For asymptotically large \(n\), the information-theoretic issue returns.

---

# 21. Proof status after v0.7

| Result | Status |
|---|---|
| Structured Quorum Coverage Theorem | **proved** |
| LoTRS direct arbitrary-BFT trichotomy | **proved** |
| Restricted structured-quorum CE-QS condition | **proved** |
| Public bitmap exact-multisig certificate soundness | **proved conditionally** |
| Public bitmap conflict extraction | **proved** |
| Public bitmap non-frameability | **proved conditionally** |
| Public bitmap BFT safety composition | **proved conditionally** |
| Privacy Separation Theorem | **proved** |
| Practical <32 KiB \(B_0\) backend | **open** |
| Practical <32 KiB hidden-signer \(B_1\) backend | **open** |
| CET v0.5/v0.6 proof stack | unchanged |
| LoTRS under restricted structured fault model | eligible future branch |
| QROM proof for hidden CE-QS | open |

---

# 22. The narrowed research question

There are now two honest questions.

### Public accountability

\[
\boxed{
\textbf{Can an exact independent-key PQ multisignature for 43-of-64 fit below 32 KiB?}
}
\]

If yes, sidecar-free public conflict extraction is solved at the system-composition level:

\[
8\text{-byte bitmap}
+
\text{compact PQ multisig}.
\]

### Private accountability

\[
\boxed{
\textbf{Can an exact compact PQ aggregate bind the same hidden arbitrary 43-of-64 signer set to CET tags?}
\]

That remains the deeper CE-QS problem.

---

# 23. Next empirical milestone

Before extending the hidden-signer proof further, benchmark the public variant at the actual operating point:

\[
n=64,\qquad q=43.
\]

Run:

- Lemur;
- Chipmunk;
- one proof-based Falcon aggregation implementation if available.

Measure actual:

- public-key bytes;
- aggregate signature bytes;
- signing latency;
- aggregation latency;
- verification latency;
- state/preprocessing limits.

If one meets:

\[
|\sigma|+8\text{ bytes}\le32\text{ KiB},
\]

then Target \(B_0\) has a concrete candidate and the CET track can be reserved strictly for the stronger privacy requirement.

---

# 24. Primary literature anchors

- Jagganath et al., *LoTRS: Practical Post-Quantum Structured Threshold Ring Signatures from Lattices*, 2026.
  - structured \(T\times N\) public-key table;
  - one hidden admissible column;
  - threshold multisignature + 1-out-of-many anonymity proof;
  - ~35 KB at the paper's \(T=50,N=100\) headline point.

- Fleischhacker et al., *Chipmunk: Better Synchronized Multi-Signatures from Lattices*, CCS 2023.
  - independent-key synchronized blockchain multisignatures;
  - non-interactive aggregation;
  - rogue-key security;
  - ~136 KB aggregate for 8192 signatures at stated parameters.

- Lin et al., *Lemur: Scalable Post-Quantum Synchronized Multi-Signatures*, CCS 2026.
  - synchronized PQ multisignature;
  - public artifact reports ~201.2 KB aggregate at \(N=1024\).

- Aardal et al., *Aggregating Falcon Signatures with LaBRADOR*, CRYPTO 2024.
  - proof-based exact aggregation of Falcon signatures.

- Brodsky, Choudhuri, Jain, Paneth, *Monotone-Policy Aggregate Signatures*, EUROCRYPT 2024.
  - succinct aggregation for threshold/weighted monotone policies;
  - aggregate size independent of number of signers in the theoretical construction.

---

# 25. Bottom line

v0.7 proves that the problem has two qualitatively different versions.

If **public signer identity is acceptable**, CE-specific tracing machinery disappears:

\[
\boxed{
\text{exact PQ multisignature}
+
\text{8-byte signer bitmap}
}
\]

already gives sidecar-free conflict extraction for 64 validators.

The unsolved issue is only practical aggregate size.

If **signer privacy is mandatory**, then CET/DAPT remains necessary, and the v0.5/v0.6 same-hidden-set proof is still the right architecture.

LoTRS does not bypass that problem for ordinary arbitrary-fault BFT because its structured quorum family would need at least:

\[
\boxed{
41,107,996,877,935,680
}
\]

columns to cover all possible all-honest 43-of-64 quorums.

The next design decision is therefore explicit rather than hidden:

\[
\boxed{
\textbf{Does the production quorum certificate require signer-set privacy?}
}
\]

That requirement determines which cryptographic research track is necessary.
