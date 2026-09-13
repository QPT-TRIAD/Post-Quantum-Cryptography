# CE-QS v0.8 — Public-Signer Theoretical Completion
## A Succinct Sidecar-Free Accountable PQ Quorum Certificate from Monotone-Policy Aggregate Signatures

**Status:** formal composition theorem for Target \(B_0\) (public signer set).  
**Date:** 2026-09-08.  
**Track:** Target \(B_0\) only. Hidden-signer Target \(B_1\) remains the CET/DAPT research track.  
**Claim discipline:** this document establishes a theoretical construction under the published monotone-policy aggregate-signature interface. It does not claim a practical implementation, a <32-KiB measured artifact, or a formally quantum-adversary proof.

---

# 0. Correction carried forward from the v0.7 validation

The current Lemur paper reports:

\[
185.5\text{ KB}
\]

for its \(N=1024\), \(\tau=20\), 128-bit aggregate profile, not 201.2 KB.

This correction does not affect any theorem below.

The important v0.7 result remains:

> If signer identities may be public, an exact signer bitmap plus an exact signer-set-bound PQ aggregate is enough for conflict accountability; CET is required only for the stronger hidden-signer problem.

v0.8 now closes the missing *theoretical compact-aggregate* slot for that public-signer branch.

---

# 1. Published primitive used by v0.8

Let:

\[
\mathsf{MPAgg}
=
(
Setup,
KeyAgg,
SigAgg,
AggVerify
)
\]

be an aggregate-signature scheme for monotone policies as defined by Brodsky, Choudhuri, Jain, and Paneth (EUROCRYPT 2024).

For \(k\) registered verification keys:

\[
vk_1,\ldots,vk_k,
\]

a monotone policy is:

\[
f:\{0,1\}^k\rightarrow\{0,1\}.
\]

The aggregate signature attests that the aggregator possesses valid individual signatures whose validity vector satisfies \(f\).

The paper's Definition 4.1 gives adaptive unforgeability in a game where the adversary may:

- request honest verification keys;
- request signatures under those keys;
- request signing keys;
- introduce maliciously generated verification keys.

For the target message \(M\), define:

\[
b_i=1
\]

when the adversary is legitimately entitled to count key \(i\), namely because:

- it is a maliciously generated key;
- the adversary obtained a signature on \(M\);
- or it obtained the corresponding signing key.

The adversary wins if:

\[
f(b_1,\ldots,b_k)=0
\]

but:

\[
AggVerify(crs,f,\widehat{vk},M,\widehat{\sigma})=1.
\]

This is exactly the security shape needed for a public BFT signer bitmap.

---

# 2. Threshold policies are directly supported

The EUROCRYPT 2024 construction explicitly supports weighted threshold policies:

\[
f(b_1,\ldots,b_k)=1
\iff
\sum_{i=1}^{k}\alpha_i b_i\ge t.
\]

Setting:

\[
\alpha_i=1
\]

gives ordinary threshold signing.

The paper also proves a fast-aggregation variant in which aggregation time for threshold policies is polynomial in the number \(t\) of provided signatures rather than the total registry size.

For BFT:

\[
k=n=64,
\qquad
q=43.
\]

---

# 3. Bitmap-conjunction policy

Let:

\[
B\in\{0,1\}^n
\]

be the claimed signer bitmap.

Define:

\[
w(B)
=
\sum_i B_i.
\]

The certificate verifier requires:

\[
w(B)\ge q.
\]

Now define the monotone weighted-threshold policy:

\[
\boxed{
f_B(z_1,\ldots,z_n)
=
\mathbf 1
\left[
\sum_{i=1}^{n} B_i z_i
\ge
w(B)
\right].
}
\]

Because every:

\[
B_i,z_i\in\{0,1\},
\]

this condition is equivalent to:

\[
\boxed{
f_B(z)=1
\iff
\forall i\text{ with }B_i=1,\ z_i=1.
}
\]

So \(f_B\) is simply the conjunction of all identities claimed by the bitmap.

It is monotone.

It is also a weighted-threshold policy of the exact family covered by the published fast-aggregation theorem.

---

# 4. Construction \(PQ\text{-}AQC_{\rm Public}\)

## Setup

The epoch fixes the canonical validator registry:

\[
R_e=(vk_1,\ldots,vk_n).
\]

Run:

\[
crs\leftarrow Setup(1^\lambda).
\]

Compute the aggregate verification key:

\[
\widehat{vk}
\leftarrow
KeyAgg(crs,R_e).
\]

The registry ordering is immutable for the epoch.

---

## Vote

Validator \(i\) signs canonical consensus message:

\[
M
=
enc(
\texttt{PQ-AQC-PUBLIC-v1},
chain,
epoch,
height,
view,
phase,
blockHash,
parentHash
).
\]

It produces:

\[
\sigma_i
\leftarrow
Sign(sk_i,M).
\]

---

## Aggregate

Suppose the collector receives valid signatures from signer set:

\[
S.
\]

Choose any:

\[
B
\]

whose 1-bits are a subset of \(S\) and satisfy:

\[
w(B)\ge q.
\]

The simplest canonical choice is:

\[
B_i=1
\iff
i\in S_{\rm cert}
\]

for one deterministic \(q\)-signer subset \(S_{\rm cert}\subseteq S\).

Compute:

\[
f_B.
\]

Then:

\[
\widehat{\sigma}
\leftarrow
SigAgg(
crs,
f_B,
R_e,
(\sigma_i)_{i\in S_{\rm cert}},
M
).
\]

---

## Certificate

\[
\boxed{
QC=
(
v,
epoch,
H(M),
B,
\widehat{\sigma}
).
}
\]

For \(n=64\), \(B\) is exactly 8 bytes.

---

## Verify

Accept iff:

1. version/domain encoding is canonical;
2. registry/epoch is the expected one;
3. \(w(B)\ge q\);
4. \(f_B\) is deterministically reconstructed from \(B\);
5.

\[
AggVerify(
crs,
f_B,
\widehat{vk},
M,
\widehat{\sigma}
)=1.
\]

The verifier never accepts a policy supplied independently from the bitmap.

This prevents bitmap/policy mismatch.

---

# 5. Lemma — bitmap policy equivalence

### Lemma 5.1

For:

\[
B,z\in\{0,1\}^n,
\]

\[
f_B(z)=1
\]

iff:

\[
\operatorname{supp}(B)
\subseteq
\operatorname{supp}(z).
\]

### Proof

By definition:

\[
f_B(z)=1
\iff
\sum_i B_i z_i
\ge
\sum_i B_i.
\]

But every term satisfies:

\[
B_i z_i\le B_i.
\]

Therefore the sum can reach:

\[
\sum_i B_i
\]

only when:

\[
B_i z_i=B_i
\]

for every \(i\).

Whenever:

\[
B_i=1,
\]

this requires:

\[
z_i=1.
\]

Conversely, if all selected positions have \(z_i=1\), both sums are equal.

\[
\blacksquare
\]

---

# 6. Theorem — exact public signer-set soundness

### Theorem 6.1

Assume \(\mathsf{MPAgg}\) satisfies Definition-4.1 adaptive unforgeability.

Let an adversary output an accepted certificate:

\[
QC=(B,\widehat{\sigma})
\]

for message \(M\).

Then, except with aggregate-signature unforgeability advantage, every honest uncompromised identity:

\[
i\in\operatorname{supp}(B)
\]

actually signed \(M\).

### Proof

Suppose instead there exists:

\[
i^\star\in\operatorname{supp}(B)
\]

such that:

1. \(vk_{i^\star}\) is an honestly generated registered key;
2. the adversary did not obtain \(sk_{i^\star}\);
3. the adversary did not obtain a signature from \(i^\star\) on \(M\).

In the aggregate-unforgeability experiment:

\[
b_{i^\star}=0.
\]

Since:

\[
B_{i^\star}=1,
\]

Lemma 5.1 gives:

\[
f_B(b)=0.
\]

But the CE-QC verifier accepted, so:

\[
AggVerify(crs,f_B,\widehat{vk},M,\widehat{\sigma})=1.
\]

This is precisely a winning forgery in Definition 4.1.

Therefore:

\[
\boxed{
Adv^{SetFrame}_{AQC}
\le
Adv^{UF}_{MPAgg}.
}
\]

\[
\blacksquare
\]

---

# 7. Corollary — exact quorum soundness

The verifier requires:

\[
w(B)\ge q.
\]

All positions in \(B\) are distinct by bitmap syntax.

By Theorem 6.1, every uncompromised honest selected identity really signed \(M\), while corrupted identities are legitimately adversary-controlled signers.

Thus every accepted certificate cryptographically represents at least:

\[
\boxed{q}
\]

distinct registered authorizations.

No threshold-signature DKG is needed.

No signer sidecar is needed.

---

# 8. Theorem — public conflict extraction

Let:

\[
QC_0=(B_0,\widehat{\sigma}_0)
\]

and:

\[
QC_1=(B_1,\widehat{\sigma}_1)
\]

be accepted certificates for conflicting messages in the same BFT conflict domain.

Define:

\[
B_\cap=B_0\land B_1.
\]

Because:

\[
w(B_0),w(B_1)\ge q,
\]

set intersection gives:

\[
w(B_\cap)
\ge
2q-n.
\]

For:

\[
n=3f+1,
\qquad
q=2f+1,
\]

\[
2q-n=f+1.
\]

Therefore:

\[
\boxed{
w(B_0\land B_1)\ge f+1.
}
\]

Every selected bit is publicly identifiable.

Thus:

\[
\boxed{
ExtractConflict(QC_0,QC_1)
=
\operatorname{supp}(B_0\land B_1).
}
\]

This is exact and deterministic.

\[
\blacksquare
\]

---

# 9. Theorem — public VerifyBlame

Define:

\[
VerifyBlame(
QC_0,QC_1,i
)=1
\]

iff:

1. both QCs verify;
2. their statements conflict in the same domain;
3.

\[
B_0[i]=B_1[i]=1.
\]

### Theorem 9.1 — non-frameability

If honest uncompromised validator \(i\) did not sign both conflicting messages, then:

\[
VerifyBlame(QC_0,QC_1,i)=1
\]

only with probability bounded by aggregate-signature forgery.

### Proof

If \(i\) did not sign \(M_b\) for one of:

\[
b\in\{0,1\},
\]

yet:

\[
B_b[i]=1
\]

and \(QC_b\) verifies, Theorem 6.1 yields a forgery.

Hence:

\[
\boxed{
Adv^{Frame}_{AQC}
\le
2Adv^{UF}_{MPAgg}.
}
\]

The factor 2 is the conservative union bound over the two certificates.

\[
\blacksquare
\]

---

# 10. BFT conflict-impossibility theorem

Assume:

1. \(n=3f+1\);
2. at most \(f\) validators are Byzantine;
3. honest validators never sign two conflicting statements in one conflict domain;
4. vote state is crash-persistent;
5. the aggregate primitive is unforgeable.

Suppose two conflicting QCs verify.

Their bitmap intersection contains at least:

\[
f+1
\]

validators.

At most \(f\) are Byzantine.

Therefore at least one validator in the intersection is honest.

By Theorem 6.1 that honest validator signed both messages.

This contradicts honest no-double-vote unless persistent vote state failed.

Therefore:

\[
\boxed{
Adv^{BFTConflict}_{B_0}
\le
2Adv^{UF}_{MPAgg}
+
\epsilon_{\rm rollback}
+
Adv^{BaseSafety}.
}
\]

This is a complete reduction from public-signer sidecar-free quorum accountability to monotone-policy aggregate-signature security.

---

# 11. Succinctness theorem

The EUROCRYPT 2024 paper proves, for read-once bounded-space policies, aggregate signature size and verification time:

\[
poly(\log k,S,\lambda).
\]

Threshold policies use:

\[
S=\log k.
\]

It separately gives a threshold-policy fast aggregator with aggregation time:

\[
poly(t,\lambda)
\]

for threshold \(t\).

Our bitmap policy \(f_B\) is a weighted threshold policy with:

\[
\alpha_i=B_i,
\qquad
t=w(B).
\]

Therefore the cryptographic aggregate has size:

\[
\boxed{
poly(\lambda,\log n).
}
\]

The complete certificate additionally contains the public bitmap:

\[
n\text{ bits}.
\]

Thus:

\[
\boxed{
|QC|
=
poly(\lambda,\log n)
+
n
+
O(\lambda)
\text{ bits}.
}
\]

For the fixed reference committee:

\[
n=64,
\]

signer attribution costs only:

\[
\boxed{8\text{ bytes}}.
\]

This is **practically compact for fixed \(n=64\)**, although asymptotically the public bitmap remains linear in \(n\).

---

# 12. Theoretical completion theorem for Target \(B_0\)

### Theorem 12.1

Assume an adaptively secure monotone-policy aggregate-signature scheme for weighted threshold policies, together with canonical BFT state.

Then there exists a non-interactive, sidecar-free quorum certificate for:

\[
n=3f+1,\qquad q=2f+1
\]

with:

- independent validator keys;
- no threshold DKG;
- exact public signer attribution;
- deterministic public conflict extraction;
- non-frameability under aggregate unforgeability;
- cryptographic aggregate size polylogarithmic in the validator count;
- \(n\)-bit public signer metadata.

For \(n=64\), the signer metadata is 8 bytes.

Thus:

\[
\boxed{
\textbf{Target }B_0\textbf{ is theoretically solved at the abstract cryptographic level.}
}
\]

What is not solved is practical instantiation below the project's 32-KiB gate.

\[
\blacksquare
\]

---

# 13. Standard-assumption / post-quantum qualification

The EUROCRYPT 2024 aggregate construction is not merely a heuristic SNARK wrapper.

The paper builds adaptive subset-extractable monotone-policy BARGs from:

- somewhere-extractable BARGs;
- hash families with local opening;
- 2-composable verifiable PIR.

Its Theorem 3.6 cites somewhere-extractable BARGs under:

\[
\text{LWE}
\]

or:

\[
\text{DLIN}.
\]

For the PQ branch we select LWE.

The threshold policy itself is explicitly handled by the paper's weighted-threshold Theorems 7.5 and 7.6.

Therefore a **lattice-assumption route exists** to the theoretical construction.

However, the published security definitions are written for classical efficient adversaries.

Accordingly, the strongest accurate statement is:

\[
\boxed{
\text{classically proved adaptive construction from standard assumptions, with an LWE instantiation path}.
}
\]

It is **not yet** legitimate to relabel this theorem:

\[
\text{QPT-secure}.
\]

---

# 14. Quantum-Lift Criterion

Define \(MPAgg^{Q}\) as the same construction instantiated so that:

1. base digital signatures are QEUF-CMA secure;
2. LWE hardness holds against QPT adversaries;
3. the hash family is quantum collision resistant;
4. somewhere-extractable BARG/index-hiding properties hold against QPT adversaries;
5. 2-composable vPIR simulation/extraction holds against QPT adversaries;
6. the monotone-policy aggregation proof preserves these properties under quantum distinguishers.

### Theorem 14.1

If items 1–6 hold, then Theorems 6.1–12.1 hold against QPT adversaries with the same black-box reduction structure.

### Proof

The CE-QS \(B_0\) reductions never rewind the adversary and never use random-oracle programming.

They invoke the aggregate primitive only through its unforgeability experiment.

Therefore a QPT-secure realization of the same aggregate interface substitutes directly.

\[
\blacksquare
\]

This avoids the Hermine/Fiat–Shamir QROM problem structurally.

The unresolved issue is whether the full monotone-policy BARG/vPIR stack has a published QPT theorem matching items 2–6.

---

# 15. Why the bitmap must define the policy

It is unsafe to verify:

\[
\widehat{\sigma}
\]

only against the generic threshold policy:

\[
\sum_i z_i\ge q
\]

while separately carrying an unauthenticated bitmap.

Then an attacker could attach an arbitrary bitmap to a valid threshold aggregate.

Therefore:

\[
\boxed{
B\rightarrow f_B\rightarrow AggVerify
}
\]

is mandatory.

The bitmap is not metadata.

It is part of the authenticated policy statement.

This is the public-signer analogue of v0.6's same-hidden-set binding theorem.

---

# 16. Why plain threshold policy is insufficient for accountability

A policy:

\[
f_q(z)=
\mathbf 1
\left[
\sum_i z_i\ge q
\right]
\]

proves that **some** quorum signed.

It does not identify which quorum.

For consensus safety alone that can be sufficient.

For public conflict accountability it is insufficient.

The bitmap-conjunction policy:

\[
f_B
\]

changes the statement from:

> some \(q\) validators signed

to:

> every validator named by \(B\) signed.

That is the exact logical step that makes:

\[
B_0\land B_1
\]

valid blame evidence.

---

# 17. Relationship to Distributed Quorum Signatures

A July 2026 systems paper, *Byzantine Fault-Tolerant Post-Quantum Distributed Quorum Signatures*, takes a different route.

It observes that no constant-size practical PQ quorum signature is currently known and replaces transferable quorum certificates with distributed local certificate events built from ordinary signatures and approval broadcast.

This is useful independent evidence about the current practical landscape.

It does **not** invalidate Theorem 12.1:

- monotone-policy aggregate signatures are theoretical and not demonstrated as practical;
- DQS targets deployable communication behavior without solving the advanced cryptographic aggregation problem;
- CE-QS \(B_0\) retains a transferable self-contained certificate.

Thus:

\[
\boxed{
\text{DQS is an engineering escape hatch;}
\qquad
B_0\text{ is a theoretical transferable construction.}
}
\]

---

# 18. Practical status

The theorem does not answer:

\[
|QC|\le32\text{ KiB}?
\]

The monotone-policy schemes rely on advanced BARG/vPIR machinery and the cited work is asymptotic/theoretical rather than a production benchmark.

Current practical synchronized PQ multisignatures remain much larger in published large-\(N\) profiles:

- Chipmunk: around 136 KB at \(N=8192\), 112-bit profile;
- Lemur: 185.5 KB at \(N=1024\), 128-bit profile.

These numbers do not determine the \(N=64\) point.

Therefore:

\[
\boxed{
\textbf{B}_0\textbf{ is theoretically closed but practically open.}
}
\]

---

# 19. Effect on hidden-signer Target \(B_1\)

The result does **not** solve \(B_1\).

The aggregate-signature paper does not give CE-QS's required signer-set privacy theorem.

Even if an aggregate does not explicitly include the signer set, absence of explicit identities is not a proof of anonymity.

For hidden signer accountability we still require either:

1. a CET-liftable anonymous exact aggregate; or
2. a zero-knowledge monotone-policy aggregate proving:
   - threshold authorization;
   - the same hidden set generated the public CET tags.

Therefore the v0.5/v0.6 CET proof remains active for \(B_1\).

---

# 20. New proof-status table

| Property | Target \(B_0\) status after v0.8 |
|---|---|
| Exact public signer-set binding | **proved conditionally on MPA unforgeability** |
| Threshold soundness | **proved** |
| Conflict extraction | **proved exactly** |
| Non-frameability | **proved conditionally** |
| BFT composition | **proved conditionally** |
| No DKG | **yes by construction** |
| No sidecar | **yes by construction** |
| Signer bitmap cost at n=64 | **8 bytes** |
| Cryptographic aggregate asymptotic size | **polylogarithmic by published theorem** |
| Adaptive classical security | **supported by published threshold-policy construction** |
| Standard-assumption lattice path | **exists via LWE-based BARG route** |
| Formal QPT security | **open** |
| Concrete <32-KiB implementation | **open** |
| Hidden signer privacy | **not provided / B1 only** |

---

# 21. Main conclusion

The proof line now has a clean hierarchy.

## \(B_0\): public signer set

\[
\boxed{
\text{monotone-policy aggregate signature}
+
\text{8-byte authenticated bitmap}
}
\]

gives a theoretically succinct, exact, transferable, sidecar-free accountable BFT quorum certificate.

No CET is needed.

## \(B_1\): hidden signer set

\[
\boxed{
\text{CET}
+
\text{same-hidden-set anonymous exact aggregate}
}
\]

remains the stronger open construction.

The remaining work is no longer one undifferentiated "post-quantum quorum signature" problem.

It is:

\[
\boxed{
\begin{array}{ll}
B_0:&\text{make the theoretically solved construction practical/QPT-secure};\\
B_1:&\text{add signer privacy + conflict-only extraction practically/QPT-secure}.
\end{array}
}
\]
