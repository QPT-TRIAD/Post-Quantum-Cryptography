# CE-QS v0.6 — Exact-Aggregator Lifting Proof
## Backend-Neutral Proof for Sidecar-Free Conflict-Extractable PQ Quorum Signatures

**Status:** abstract composition proof continued from v0.5.  
**Date:** 2026-09-08.  
**Scope:** Target B only.  
**Claim boundary:** this document proves a generic lifting theorem from an exact anonymous threshold-ring proof to CE-QS, under explicit interfaces. It does not prove that CTRS or any other concrete backend satisfies the new CET-liftability interface with acceptable concrete size.

---

# 1. Why v0.6 exists

v0.5 proved the CET layer and its composition with an **abstract exact certificate verifier**.

The remaining open slot was:

\[
\boxed{
\text{an exact compact PQ anonymous threshold aggregate that can prove the CE-QS relation}.
}
\]

The 2025 GC-TRS/CTRS paper gives exactly the neighboring generic shape:

\[
\boxed{
\text{one aggregated signature}
+
\text{one exact }t\text{-out-of-}n\text{ proof}.
}
\]

The purpose of v0.6 is to answer a precise question:

> What exact property must a GC-TRS/CTRS-like backend satisfy so that all of the v0.5 CE-QS proofs lift unchanged?

The answer is a new adapter property called **CET-liftability**.

---

# 2. Remove backend-specific mask assumptions

v0.3/v0.4 used an AES-like mask because it fits VOLE-in-the-Head.

CTRS is lattice-native, so forcing AES into its proof system may be the wrong engineering choice.

The proof therefore depends only on an abstract mask primitive.

Define:

\[
\mathsf{Mask}
=
(
\mathsf{KGen},
\mathsf{Commit},
\mathsf{Eval},
\mathsf{Rel}
).
\]

For secret mask key \(k\):

\[
K=\mathsf{Commit}(k).
\]

For topic \(\tau\):

\[
r=\mathsf{Eval}(k,\tau)\in\mathcal V.
\]

Required properties:

### M1. Determinism

For fixed \(k,\tau\):

\[
\mathsf{Eval}(k,\tau)
\]

is unique.

### M2. Auxiliary-input pseudorandomness

Even given public:

\[
K=\mathsf{Commit}(k),
\]

the function:

\[
\tau\mapsto\mathsf{Eval}(k,\tau)
\]

is pseudorandom on admissible fresh topics.

Advantage:

\[
\epsilon_{\rm mask-prf}.
\]

### M3. Key binding

It is infeasible to find:

\[
k\neq k'
\]

with:

\[
\mathsf{Commit}(k)
=
\mathsf{Commit}(k').
\]

Advantage:

\[
\epsilon_{\rm mask-bind}.
\]

### M4. Proof compatibility

The backend proof system can prove:

\[
K=\mathsf{Commit}(k)
\]

and:

\[
r=\mathsf{Eval}(k,\tau)
\]

without revealing \(k\).

This is an implementation property, not a standalone hardness assumption.

---

# 3. Two qualified mask adapters

## 3.1 VOLEitH adapter

Use the symmetric-key tag/public-key machinery already supported by the selected VOLE-in-the-Head implementation.

Advantages:

- efficient Boolean/arithmetic circuit representation;
- matches the CCS 2025 code base;
- tag pseudorandomness/key-binding already central to that construction.

This remains the best prototype adapter.

## 3.2 Lattice-native adapter

The post-quantum traceable-ring literature gives a lattice PRF family of the form:

\[
F^H(u,\Gamma)
=
\lfloor H(\Gamma)u\rceil_p.
\]

Published traceable-ring work states QROM pseudorandomness of this family from LWE under its parameter conditions and additionally studies uniqueness/intersection-free properties.

This is a qualified candidate for CTRS because the computation is native to lattice arithmetic.

For CE-QS, its output may be a vector/module element rather than one 256-bit field element.

The extraction algebra then becomes module-valued:

\[
e_i=r_{i,\tau}+c x_i.
\]

For scalar:

\[
c\in\mathbb Z_p^*
\]

and vector:

\[
x_i,r_{i,\tau},e_i\in\mathbb Z_p^m,
\]

conflict extraction is componentwise:

\[
\boxed{
x_i=(c_0-c_1)^{-1}(e_{i,0}-e_{i,1}).
}
\]

Thus the CE-QS proof does not require AES specifically.

Concrete tag length for the lattice-native adapter is not frozen until its parameters are selected.

---

# 4. Abstract exact aggregate

Let:

\[
\mathsf{AggAuth}
=
(
\mathsf{AggSetup},
\mathsf{Contribute},
\mathsf{Aggregate},
\mathsf{AggRel},
\mathsf{AggVerify}
).
\]

An aggregate signature is:

\[
\sigma_{\rm agg}.
\]

A witness that signer \(i\) legitimately contributed is:

\[
a_i.
\]

The exact aggregate relation is:

\[
\mathsf{AggRel}
(
R,M,\sigma_{\rm agg};
(i_1,a_1),\ldots,(i_s,a_s)
)
=1.
\]

It means:

1. all \(i_j\) are valid registry identities;
2. the corresponding authentication witnesses legitimately authorize \(M\);
3. \(\sigma_{\rm agg}\) is exactly the aggregate of those contributions.

This relation need not reveal the identities publicly.

---

# 5. Exact hidden-threshold proof

Let:

\[
\mathsf{TOP}
=
(
\mathsf{Setup},
\mathsf{Prove},
\mathsf{Verify},
\mathsf{Extract},
\mathsf{Sim}
).
\]

`TOP` is an exact \(t\)-out-of-\(n\) proof, not ELBA.

Public statement:

\[
x.
\]

Witness set:

\[
W=(w_1,\ldots,w_s).
\]

For threshold \(q\), accepted proof semantics require:

\[
s\ge q.
\]

Required properties:

### T1. Completeness

Valid \(W\) produces an accepted proof.

### T2. Exact knowledge extraction

From any fresh accepted proof for threshold \(q\), the extractor outputs at least:

\[
q
\]

valid distinct witnesses satisfying the proved relation.

There is no \(n_f/n_p\) gap.

### T3. Zero knowledge / quorum witness indistinguishability

Proof distributions do not reveal which valid witness set was used beyond permitted public leakage.

### T4. Public-statement binding

All public CET tags and the aggregate signature are immutable components of the statement being proved.

---

# 6. CET-liftability — the missing adapter property

A threshold-ring backend is **CET-liftable** if its exact threshold proof can prove the following relation while retaining T1–T4.

Public statement:

\[
X=
(
R_e,
\tau,
H(M),
q,
\sigma_{\rm agg},
E
).
\]

Let:

\[
E=(e_1,\ldots,e_s),
\qquad
s\ge q.
\]

Hidden witness:

\[
W=
\left(
(i_j,sk_j,x_j,k_j,a_j)
\right)_{j=1}^s
\]

plus a hidden permutation:

\[
\pi\in S_s.
\]

The lifted relation:

\[
\boxed{
\mathcal R_{\rm Lift}(X;W,\pi)=1
}
\]

iff all of the following hold.

## L1. Registry membership

For each \(j\):

\[
(i_j,pk_{i_j},X_{i_j},K_{i_j})\in R_e.
\]

## L2. Authentication witness

\[
AuthRel(pk_{i_j},sk_j)=1.
\]

## L3. Trace-secret binding

\[
G_{\rm tr}(x_j)=X_{i_j}.
\]

## L4. Mask-key binding

\[
K_{i_j}=\mathsf{Mask.Commit}(k_j).
\]

## L5. Correct CET

Let:

\[
r_j=\mathsf{Mask.Eval}(k_j,\tau),
\]

and:

\[
c=H_F(\tau,H(M)).
\]

Then:

\[
e_{\pi(j)}
=
r_j+c x_j.
\]

## L6. Aggregate authentication

\[
\mathsf{AggRel}
(
R_e,M,\sigma_{\rm agg};
(i_1,a_1),\ldots,(i_s,a_s)
)
=1.
\]

## L7. Identity distinctness

\[
i_j\neq i_k
\qquad
\forall j\neq k.
\]

For deterministic key-bound CETs, L7 may be enforced either inside the proof or by the combination of:

- public duplicate-tag rejection;
- registry binding;
- deterministic CET;
- exact witness extraction.

The v0.5 distinctness lemma proves the equivalence under those binding assumptions.

---

# 7. CE-GC-TRS construction

Assume a CET-liftable backend.

## Contribution

Each signer creates its private authentication contribution and CET:

\[
e_i=
\mathsf{Mask.Eval}(k_i,\tau)+c x_i.
\]

## Aggregate

Authorized signers combine authentication contributions into:

\[
\sigma_{\rm agg}.
\]

Let:

\[
E
\]

be the canonical sorted CET list.

## Prove

Generate:

\[
\pi_{\rm lift}
\leftarrow
\mathsf{TOP.Prove}
(
X;
W,\pi
).
\]

## Certificate

\[
\boxed{
\Sigma
=
(
v,e,\tau,H(M),q,
\sigma_{\rm agg},
E,
\pi_{\rm lift}
).
}
\]

## Verification

Accept iff:

1. domain/version encoding is canonical;
2. \(s=|E|\ge q\);
3. public CETs are pairwise distinct;
4. \(\mathsf{TOP.Verify}(X,\pi_{\rm lift})=1\).

This is sidecar-free.

---

# 8. The CET-Lifting Theorem

### Theorem 8.1

Assume:

1. the backend is CET-liftable;
2. Mask satisfies M1–M3;
3. trace commitments are binding;
4. authentication witnesses are unforgeable/binding;
5. challenge hashing satisfies v0.5 A8–A9.

Then CE-GC-TRS inherits:

- exact threshold soundness;
- quorum anonymity;
- cross-topic unlinkability;
- conflict-extraction completeness;
- trace soundness;
- honest non-frameability;
- post-exposure authentication security,

with only additive losses from the lifted proof and mask adapter.

### Proof

Every v0.5 reduction invokes the certificate backend through exactly three facts:

#### F1. Exact witness existence

An accepted certificate yields at least \(q\) valid distinct registered witnesses.

This is T2 applied to:

\[
\mathcal R_{\rm Lift}.
\]

#### F2. Hidden-witness simulation

The proof transcript can be simulated or switched between admissible witness sets.

This is T3.

#### F3. Public CET binding

The public tag list used by the extractor is the exact list certified by the proof.

This is T4 plus L5.

No v0.5 reduction inspects the internal representation of:

\[
\sigma_{\rm agg}
\]

or the t-out-of-n proof.

Therefore substitute F1–F3 into the proofs of v0.5 Sections 5–16.

All steps remain unchanged.

The new loss is at most:

\[
\epsilon_{\rm Lift}
=
\epsilon_{\rm TOP-ext}
+
\epsilon_{\rm TOP-zk}
+
\epsilon_{\rm TOP-bind}
\]

in whichever security game uses the corresponding property.

Hence the claimed properties lift.

\[
\blacksquare
\]

---

# 9. Exact threshold soundness under the lifted backend

Suppose a certificate verifies but fewer than \(q\) legitimate registered identities authorized \(M\).

By T2, extract:

\[
q
\]

distinct witnesses satisfying:

\[
\mathcal R_{\rm Lift}.
\]

L2 gives \(q\) valid authentication witnesses.

Therefore at least one extracted authentication witness belongs to an identity not legitimately available to the adversary.

This breaks authentication-key security or TOP extraction/soundness.

Thus:

\[
\boxed{
Adv^{ThreshForge}_{CE-GCTRS}
\le
\epsilon_{\rm TOP-ext}
+
\epsilon_{\rm auth}
+
\epsilon_{\rm bind}.
}
\]

`AggRel` is important here because it prevents the proof from certifying \(q\) unrelated registered witnesses while attaching an aggregate signature generated by some different set.

---

# 10. The same-hidden-set binding theorem

A subtle requirement is that CET witnesses and aggregate-authentication witnesses must describe the **same hidden identities**.

If the proof instead established only:

\[
\exists S_{\rm auth}:|S_{\rm auth}|\ge q
\]

for the aggregate and independently:

\[
\exists S_{\rm tag}:|S_{\rm tag}|\ge q
\]

for the CET list, extraction would not follow: quorum intersection of the two *certificates* would say nothing about whether the tags belonged to the actual authentication signers.

Therefore L6 and L1–L5 use the **same index variables**:

\[
i_1,\ldots,i_s.
\]

This is load-bearing.

### Theorem 10.1

If:

\[
\mathcal R_{\rm Lift}(X;W,\pi)=1,
\]

then:

\[
S_{\rm agg}=S_{\rm CET}.
\]

Proof is immediate from the relation: one tuple:

\[
(i_j,sk_j,x_j,k_j,a_j)
\]

simultaneously satisfies the authentication and CET clauses.

This is the exact "missing link" between compact threshold aggregation and conflict extraction.

---

# 11. Anonymity lifting theorem

Let:

\[
S_0,S_1
\]

be equal-size admissible hidden signer sets.

Start from a real CE-GC-TRS certificate using \(S_b\).

## H0

Real aggregate, real CETs, real lifted proof.

## H1

Use T3 to simulate/switch the lifted proof.

Loss:

\[
\epsilon_{\rm TOP-zk}.
\]

## H2

Replace each honest mask output by uniform.

Loss for \(s\) tags:

\[
s\epsilon_{\rm mask-prf}.
\]

Then CETs are independent random elements translated by fixed trace terms and therefore reveal no signer identities.

## H3

Use the base exact threshold-ring aggregate anonymity property to switch the hidden aggregate signer set:

\[
S_0\leftrightarrow S_1.
\]

Loss:

\[
\epsilon_{\rm AggAnon}.
\]

Reverse H2/H1.

Therefore:

\[
\boxed{
Adv^{Anon}_{CE-GCTRS}
\le
2\epsilon_{\rm TOP-zk}
+
2s\epsilon_{\rm mask-prf}
+
\epsilon_{\rm AggAnon}
+
\epsilon_{\rm coll}.
}
\]

A tighter game can merge the forward/reverse hybrid terms; this conservative expression is sufficient for the composition theorem.

---

# 12. Conflict extraction under the lifted backend

Take two accepted conflicting certificates.

T2 extracts:

\[
S_0,S_1
\]

with:

\[
|S_0|,|S_1|\ge q.
\]

Because L1–L6 bind the public CET lists to those same identities, every:

\[
i\in S_0\cap S_1
\]

has one certified tag in each public list.

Then the v0.5 CET identity:

\[
x_i
=
(c_0-c_1)^{-1}
(e_{i,0}-e_{i,1})
\]

recovers the trace secret.

Thus:

\[
\boxed{
|ExtractConflict|
\ge
2q-n.
}
\]

For BFT:

\[
n=3f+1,
\qquad
q=2f+1,
\]

so:

\[
\boxed{
|ExtractConflict|
\ge
f+1.
}
\]

No assumption about the internal aggregate signature is needed after T2 and L6.

---

# 13. Trace soundness and framing lift

Suppose `ExtractConflict` outputs honest victim \(\ell\) even though \(\ell\) did not contribute to both certificates.

T2 gives valid witness sets for both certificates.

L5 certifies the public tags.

Therefore the false trace is reduced entirely to the v0.5 CET trace-soundness game.

Add only the probability that the lifted proof extractor or binding fails.

Hence:

\[
\boxed{
Adv^{Frame}_{CE-GCTRS}
\le
Adv^{FalseTrace}_{CET}
+
2\epsilon_{\rm TOP-ext}
+
2\epsilon_{\rm TOP-bind}.
}
\]

This theorem is useful because it cleanly separates:

- **threshold proof soundness**, and
- **trace algebra soundness**.

They can be audited independently.

---

# 14. Post-exposure theorem lift

Once a valid conflict exposes:

\[
x_i,
\]

any new accepted certificate contribution attributed to \(i\) yields, through T2/L2/L4, valid:

\[
sk_i
\]

and:

\[
k_i
\]

witnesses.

Thus disclosure of \(x_i\) alone cannot create a future accepted contribution unless:

- authentication security breaks;
- mask-key binding/preimage security breaks;
- lifted proof soundness breaks.

Therefore:

\[
\boxed{
Adv^{PostExposureForge}
\le
\epsilon_{\rm auth}
+
\epsilon_{\rm mask-bind}
+
\epsilon_{\rm TOP-ext}.
}
\]

---

# 15. A stronger backend-neutral main theorem

### Theorem 15.1 — CE-QS Generic Exact-Aggregate Theorem

Let:

\[
n=3f+1,
\qquad
q=2f+1.
\]

Assume a CET-liftable exact threshold-ring backend and the v0.5 CET primitive assumptions.

Then CE-QS has the following properties.

### Exact quorum authorization

Every accepted certificate contains at least:

\[
q
\]

distinct registered authorization witnesses.

### Quorum privacy

A single certificate hides the signer set subject to permitted same-message linkability.

### Public conflict accountability

Two conflicting certificates reveal at least:

\[
f+1
\]

common signer identities.

### Honest exculpability

An honest identity not present in both signer sets is not output except with the trace/lift proof failure advantage.

### Post-trace key separation

Exposure of \(x_i\) alone does not imply authentication-key compromise.

Consequently, the BFT safety theorem of v0.5 applies with the exact aggregate backend replacing the concatenated proof list.

\[
\blacksquare
\]

---

# 16. What GC-TRS already supplies conceptually

The 2025 GC-TRS paper describes a generic threshold-ring construction built from:

- an identification scheme;
- a commitment scheme;
- a special \(t\)-out-of-\(n\) zero-knowledge proof.

The final threshold-ring signature contains:

\[
\boxed{
\text{one aggregated signature}
+
\text{one }t\text{-out-of-}n\text{ proof}.
}
\]

This is exactly the public syntax required by:

\[
(\sigma_{\rm agg},\pi_{\rm lift})
\]

in the generic theorem.

CTRS further claims logarithmic final signature size in ring size.

What is **not yet proved** is that CTRS's concrete \(t\)-out-of-\(n\) proof is CET-liftable in the sense of Section 6.

That is now the sole concrete proof-adapter question.

---

# 17. Why CET-liftability is not automatic

A threshold proof that establishes only:

\[
\sigma_{\rm agg}
\text{ was generated by some }q\text{ ring members}
\]

does not authenticate a separately attached tag list.

A malicious combiner could attach tags belonging to a different set.

Therefore simply concatenating:

\[
E
\]

to an existing CTRS signature is insecure.

The proof must certify:

\[
\boxed{
\text{same hidden indices}
\Rightarrow
\begin{cases}
\text{aggregate authorization},\\
\text{CET generation}.
\end{cases}
}
\]

This is why CET-liftability is a real new proof obligation rather than formatting.

---

# 18. Lattice-native relation route

CTRS uses lattice commitments and lattice zero-knowledge techniques.

For a lattice-native mask adapter, the CET relation can be written using mostly module-linear operations:

\[
r
=
\lfloor H(\tau)k\rceil_p,
\]

\[
e
=
r+c x.
\]

The second equation is linear once:

\[
r,c
\]

are public/proved.

The first contains rounding and a matrix-vector relation already common in LWE/PRF constructions.

Post-quantum traceable-ring work gives published precedent for proving statements involving this PRF family and for QROM pseudorandomness under LWE.

Therefore CTRS+CET is not blocked by an obviously incompatible primitive.

But until the actual CTRS proof equations are extended, this remains a qualified construction path rather than a theorem about CTRS itself.

---

# 19. Concrete compactness status

The publicly accessible metadata for the 2025 GC-TRS paper confirms:

- the final signature contains one aggregate signature plus one proof;
- CTRS is logarithmic in ring size.

The accessible material in this pass did **not** expose a defensible concrete byte-size table for:

\[
n=64,\quad q=43.
\]

Therefore v0.6 does not claim a CTRS byte estimate.

The 32-KiB gate remains an implementation/parameter question.

This is preferable to inferring bytes from asymptotics.

---

# 20. Proof obligations to instantiate CTRS

A concrete CTRS adapter is complete only after proving:

## C1. Exact extraction

Accepted CTRS proof extracts at least \(q\) distinct hidden identities.

## C2. Aggregate relation binding

The extracted identities are exactly the identities represented by the aggregate signature.

## C3. CET relation extension

The proof can additionally certify:

\[
G_{\rm tr}(x_i)=X_i,
\]

\[
K_i=\mathsf{Mask.Commit}(k_i),
\]

and:

\[
e_i=\mathsf{Mask.Eval}(k_i,\tau)+c x_i.
\]

## C4. Hidden permutation

The proof reveals neither:

\[
i_j
\]

nor the mapping from each public CET:

\[
e_j
\]

to a registry position.

## C5. Zero knowledge / witness indistinguishability after extension

Adding CET clauses does not break signer anonymity.

## C6. Concrete size

At:

\[
n=64,q=43,
\]

the final:

\[
(\sigma_{\rm agg},E,\pi_{\rm lift})
\]

must fit the project gate.

## C7. Quantum-model statement

The final proof must state whether the concrete instantiation is:

- ROM/classical;
- QROM;
- or standard-model.

No model upgrade is implicit.

---

# 21. Proof status after v0.6

| Item | Status |
|---|---|
| CET primitive | conditionally proved in v0.5 |
| Exact certificate composition | conditionally proved in v0.5 |
| Backend-neutral mask interface | **proved/spec'd in v0.6** |
| CET-liftability definition | **closed** |
| Generic exact-aggregate lifting theorem | **proved conditionally** |
| Same-hidden-set necessity | **proved** |
| Anonymity lifting | **proved conditionally** |
| Conflict extraction lifting | **proved conditionally** |
| Framing lifting | **proved conditionally** |
| Post-exposure lifting | **proved conditionally** |
| CTRS generic structural match | **confirmed** |
| CTRS concrete CET-liftability | **open** |
| CTRS concrete 64/43 byte size | **not established from accessible source material** |
| VOLEitH exact compactness | fails project size gate by published v0.5 calculation |
| ELBA zero-slack compactness | fails project size gate by published v0.5 calculation |
| QROM CE-QS adapter | open |

---

# 22. The missing link is now one theorem

The project began Target B with a broad problem:

\[
\text{compact PQ accountability without sidecar}.
\]

After v0.1–v0.6, the remaining theoretical question has become:

\[
\boxed{
\textbf{Does there exist a practical CET-liftable exact PQ }t\textbf{-out-of-}n
\textbf{ proof/aggregate under the 32-KiB gate?}
}
\]

For CTRS specifically:

\[
\boxed{
\textbf{Prove C1--C7 for the CTRS instantiation.}
}
\]

If yes, the CE-QS security proof is already available through Theorem 15.1.

If no, the search must move to another exact compact threshold-ring backend.

---

# 23. Next concrete proof task

The next proof should operate directly on the CTRS \(t\)-out-of-\(n\) relation.

For every original CTRS witness equation, write the augmented witness tuple:

\[
w_i^{CE}
=
(w_i^{CTRS},x_i,k_i).
\]

Then append:

\[
G_{\rm tr}(x_i)=X_i,
\]

\[
\mathsf{Mask.Rel}(K_i,k_i,\tau,r_i)=1,
\]

\[
e_i=r_i+c x_i.
\]

The task is to show that the extended proof keeps:

- correctness;
- extractability;
- equivocation/ZK properties;
- asymptotic proof size.

This is no longer a CE-QS conceptual-design problem.

It is a concrete extension theorem for the CTRS proof system.

---

# 24. Sources underlying v0.6

1. Lin, Wang, Wen, Sun, Liang, *Generic construction of threshold ring signatures and lattice-based instantiations*, Designs, Codes and Cryptography 93(9), 2025.
   - generic GC-TRS structure;
   - aggregated signature + \(t\)-out-of-\(n\) proof;
   - CTRS logarithmic ring-size statement.

2. Feng, Liu, Li, Li, Wu, *Traceable ring signatures: general framework and post-quantum security*, Designs, Codes and Cryptography 89(6), 2021.
   - PQ TRS framework;
   - QROM lattice/symmetric instantiations;
   - PRF/hash/NIZK proof strategy.

3. Lattice-based certificateless TRS literature using:

\[
F^H(u,\Gamma)=\lfloor H(\Gamma)u\rceil_p
\]

with stated LWE/QROM pseudorandomness, uniqueness, and traceability properties.

4. v0.5 CE-QS proof stack:
   - R1--R4;
   - exact threshold theorem;
   - conflict extraction;
   - ELBA/VOLEitH size corrections.

---

# 25. Bottom line

The proof has advanced one layer.

We no longer need to prove CE-QS separately for every future compact threshold-ring scheme.

We now have a generic lifting theorem:

\[
\boxed{
\text{CET-liftable exact anonymous threshold-ring backend}
\Longrightarrow
\text{CE-QS security properties}.
}
\]

The single concrete open theorem is whether CTRS is CET-liftable with practical parameters.

That is the correct next object to attack.
