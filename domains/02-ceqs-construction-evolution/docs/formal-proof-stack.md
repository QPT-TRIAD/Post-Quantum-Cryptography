# CE-QS v0.5 — Formal Proof Stack
## Conflict-Extractable Compact Post-Quantum Quorum Signatures Without a Sidecar

**Status:** first complete paper-proof pass for the abstract CE-QS construction.  
**Date:** 2026-09-08  
**Security model:** classical PPT / ROM-style first milestone, with explicit QROM lift conditions.  
**Important:** this document proves the composition **conditionally on named primitive properties**. It does not prove the concrete VOLE-in-the-Head circuit, CTRS adapter, or QROM Fiat–Shamir instantiation.

---

# 0. Proof-driven correction to v0.4

The source audit correctly identified that the CCS 2025 paper uses **ELBA (Expanded ALBA)**, not plain ALBA, for partially unique tagged signatures.

A second correction follows directly from ELBA Definition 6.1.

ELBA has parameters:

\[
n_f<n_p.
\]

Completeness applies when the prover knows at least:

\[
n_p
\]

valid unique items, while knowledge soundness guarantees extraction of **strictly more than**:

\[
n_f.
\]

To prove an exact BFT lower bound of:

\[
q=43,
\]

one may set:

\[
n_f=42,\qquad n_p=43.
\]

Therefore:

\[
\boxed{\text{ELBA does not theoretically require more than 43 contributions to prove a 43-signer lower bound.}}
\]

The real problem is efficiency.

For Telescope-style ALBA/ELBA, equation (13) gives approximately:

\[
u\ge
\frac{\lambda_{sound}+\log_2\lambda_{comp}+1-\log_2\log_2 e}
     {\log_2(n_p/n_f)}.
\]

For:

\[
\lambda_{sound}=\lambda_{comp}=128,
\quad
n_p=43,
\quad
n_f=42,
\]

this gives:

\[
\boxed{u\ge 3991}.
\]

At ring size 64, the CCS 2025 paper reports approximately 9.91 KB for one linkable AES128 ring signature. A naive ELBA proof with the source paper's "multiply one signature by \(u\)" sizing rule is therefore on the order of:

\[
3991\times9.91\text{ KB}
\approx
38.6\text{ MiB}.
\]

Even if all 64 validators participate:

\[
n_p=64,\qquad n_f=42,
\]

the same formula gives:

\[
u\ge 223,
\]

or roughly:

\[
2.2\text{ MiB}
\]

before protocol overhead.

So the corrected conclusion is:

\[
\boxed{\text{zero-slack ELBA is theoretically compatible with 43-of-64 liveness but catastrophically non-compact at these parameters.}}
\]

Efficient ELBA requires a much larger \(n_p/n_f\) gap, which is where BFT liveness tension reappears.

This replaces the stronger v0.4 impossibility claim.

---

# 1. Construction fixed for the proof

Let:

\[
n=3f+1,
\qquad
q=2f+1.
\]

For the reference committee:

\[
n=64,\quad f=21,\quad q=43.
\]

The epoch registry is fixed **before** any messages in the epoch's conflict domains are chosen:

\[
R_e=
\{(i,pk_i,X_i,K_i)\}_{i=1}^n.
\]

Validator \(i\) has independent secrets:

\[
sk_i
\]

for anonymous authentication,

\[
x_i\in\mathbb F
\]

for conflict tracing, and

\[
k_i
\]

for the deterministic per-topic mask.

Public bindings are:

\[
X_i=G_{tr}(x_i),
\qquad
K_i=G_{mask}(k_i).
\]

The field is:

\[
\mathbb F=GF(2^{256}).
\]

For conflict domain \(\tau\),

\[
r_{i,\tau}
=
F_{k_i}(\tau).
\]

For canonical message \(M\),

\[
c=
H_F(\tau,H(M))
\in
\mathbb F^*.
\]

The CET tag is:

\[
\boxed{
e_i(\tau,M)
=
r_{i,\tau}
+
c x_i.
}
\]

All additions/subtractions below are field operations. In characteristic two, subtraction and addition coincide; the algebraic equalities remain valid.

---

# 2. Exact proof relation

A contribution has public statement:

\[
I=(R_e,\tau,H(M),e)
\]

and hidden witness:

\[
w=(i,sk_i,x_i,k_i).
\]

Define:

\[
\mathcal R_{CEQS}(I;w)=1
\]

iff:

\[
(i,pk_i,X_i,K_i)\in R_e,
\]

\[
AuthRel(pk_i,sk_i)=1,
\]

\[
G_{tr}(x_i)=X_i,
\]

\[
G_{mask}(k_i)=K_i,
\]

and:

\[
e
=
F_{k_i}(\tau)
+
H_F(\tau,H(M))x_i.
\]

The anonymous proof system is denoted:

\[
\Pi=(Setup,Prove,Verify,Extract,Sim).
\]

For the first proof milestone it is assumed to have:

1. completeness;
2. zero knowledge;
3. knowledge soundness / weak simulation extractability sufficient to extract a witness from every fresh accepted contribution;
4. statement binding to the public CET \(e\).

These are the same *types* of properties used by the CCS 2025 threshold-ring theorem, whose Theorem 5.9 assumes completeness, zero knowledge and weak simulation extractability of its NIZK together with pseudorandom, one-way and key-binding public-key/tag functions.

---

# 3. Exact certificate semantics

A consensus-critical certificate contains:

\[
\Sigma=
(v,e,\tau,H(M),q,E,\Pi_\Sigma)
\]

where:

\[
E=(e_1,\ldots,e_s),
\qquad
s\ge q.
\]

The exact-verification interface MUST imply:

> there exist \(s\) accepted witnesses for the \(s\) public CET tags, and those witnesses correspond to at least \(q\) distinct registry identities.

For the baseline construction, \(\Pi_\Sigma\) may simply contain the \(s\) anonymous proofs.

A future exact compact aggregator may replace the concatenation only if it provides the same extraction theorem.

ELBA is **not** used in this exact semantic definition.

---

# 4. Primitive assumptions

We name each assumption because the final reductions depend on different ones.

## A1. Anonymous proof completeness

For every valid witness:

\[
\Pr[Verify(I,Prove(I,w))=1]
\ge
1-\epsilon_{cor}.
\]

## A2. Knowledge soundness / weak simulation extractability

For an accepted fresh proof, failure to extract a valid witness occurs with probability at most:

\[
\epsilon_{ext}.
\]

## A3. Zero knowledge

Real and simulated proof transcripts differ with advantage at most:

\[
\epsilon_{zk}.
\]

## A4. Authentication-key hardness and binding

An adversary cannot obtain a valid honest \(sk_i\) for a registered \(pk_i\), nor find two valid authentication witnesses for the same registered key, except with advantages:

\[
\epsilon_{auth},
\qquad
\epsilon_{auth-bind}.
\]

## A5. Trace-binding security

For registered \(X_i\), it is infeasible to produce a different opening to the same trace commitment:

\[
\epsilon_{tr-bind}.
\]

The registry rejects duplicate \(X_i\) values.

## A6. Mask-key binding

For registered \(K_i\), it is infeasible to provide two valid mask keys:

\[
\epsilon_{mask-bind}.
\]

## A7. Auxiliary-input mask pseudorandomness

Given the public registry tuple, outputs:

\[
F_{k_i}(\tau)
\]

are computationally indistinguishable from a random function on fresh topics for an uncompromised key.

Denote the advantage:

\[
\epsilon_{PRF}.
\]

This is stronger than bare textbook PRF security because the adversary sees public values derived from the key. It is modeled after the CCS 2025 paper's tag-function pseudorandomness property, which explicitly gives the adversary the associated public key.

## A8. Challenge random oracle / hash-to-field

For distinct canonical messages in one topic:

\[
H_F(\tau,H(M_0))
=
H_F(\tau,H(M_1))
\]

occurs only with probability:

\[
\epsilon_H.
\]

For strong trace-soundness below we use the ROM ordering assumption that the epoch registry is committed before the adversary chooses the conflict messages.

## A9. Canonical encoding

Different protocol statements have different encoded byte strings before hashing.

---

# 5. Lemma — honest CETs are pseudorandom

For fixed public:

\[
(pk_i,X_i,K_i,\tau,M),
\]

consider:

\[
e_i=F_{k_i}(\tau)+c x_i.
\]

Replace:

\[
F_{k_i}(\tau)
\]

with uniform:

\[
R\leftarrow\mathbb F.
\]

By A7 the distinguishing loss is at most:

\[
\epsilon_{PRF}.
\]

Conditioned on the replacement:

\[
e_i=R+c x_i.
\]

For fixed \(c,x_i\), the map:

\[
R\mapsto R+c x_i
\]

is a bijection on \(\mathbb F\).

Therefore \(e_i\) is exactly uniform.

Hence:

\[
\boxed{
Adv^{1TagHide}
\le
\epsilon_{PRF}.
}
\]

This is reduction R1.

---

# 6. Lemma — deterministic duplicate detection implies identity distinctness

Suppose an accepted exact certificate contains \(s\) pairwise-distinct CETs:

\[
e_1,\ldots,e_s.
\]

By A2, except with probability at most:

\[
s\epsilon_{ext},
\]

extract witnesses:

\[
w_j=(i_j,sk_j,x_j,k_j)
\]

for every tag.

Assume two extracted witnesses have the same registry identity:

\[
i_a=i_b=i.
\]

There are two cases.

### Case 1 — the witnesses differ

Then at least one of:

\[
sk_a\ne sk_b,
\qquad
x_a\ne x_b,
\qquad
k_a\ne k_b
\]

opens the same registered tuple.

This violates A4, A5 or A6.

### Case 2 — the witnesses are identical

Because CET is deterministic for fixed:

\[
(i,\tau,M),
\]

we obtain:

\[
e_a=e_b.
\]

But accepted certificates require:

\[
e_a\ne e_b.
\]

Contradiction.

Therefore, except for extraction/binding failures:

\[
\boxed{
|\{i_1,\ldots,i_s\}|=s.
}
\]

In particular any accepted \(s\ge q\) certificate contains at least \(q\) distinct hidden identities.

---

# 7. Theorem — certificate threshold soundness

Define an unauthorized certificate as an accepted certificate for which fewer than \(q\) registered identities are legitimately available to the adversary for that statement.

Assume an adversary creates such a certificate.

By the distinctness lemma, extract at least \(q\) distinct valid witnesses.

Since fewer than \(q\) authorized identities are available, at least one extracted witness belongs to an honest identity whose authentication witness was unavailable to the adversary.

Thus either:

1. extraction failed;
2. public-key/witness binding failed;
3. the adversary obtained an honest authentication witness.

Therefore:

\[
\boxed{
Adv^{ThresholdForge}
\le
q\epsilon_{ext}
+
\epsilon_{auth-bind}
+
\epsilon_{tr-bind}
+
\epsilon_{mask-bind}
+
\epsilon_{auth}.
}
\]

This is the CE-QS exact-threshold analogue of the extraction/key-binding argument in the CCS 2025 threshold-ring unforgeability proof.

---

# 8. Theorem — certificate correctness

Let \(S\) be \(q\) distinct honest registered identities.

Every generated witness satisfies:

\[
\mathcal R_{CEQS}.
\]

Thus proof verification fails with probability at most:

\[
q\epsilon_{cor}.
\]

The remaining failure case is accidental equality of two honest CETs, causing duplicate-tag rejection.

By R1, replace all \(q\) tags with independent uniform field elements at cost at most:

\[
q\epsilon_{PRF}.
\]

Uniform collision probability is at most:

\[
\binom q2 2^{-256}.
\]

Therefore:

\[
\boxed{
\epsilon_{CEQS-cor}
\le
q\epsilon_{cor}
+
q\epsilon_{PRF}
+
\binom q2 2^{-256}.
}
\]

For \(q=43\),

\[
\binom{43}{2}=903.
\]

The generic tag-collision term is therefore:

\[
903\cdot2^{-256}.
\]

---

# 9. Theorem R2 — quorum anonymity

Consider challenge signer sets:

\[
S_0,S_1
\]

of equal cardinality \(s\), satisfying the admissibility conditions:

- challenge identities are uncorrupted;
- no challenge identity has already authenticated two conflicting messages in the challenge topic.

Let \(b\leftarrow\{0,1\}\) and produce a certificate with signer set \(S_b\).

Perform the following hybrids.

## H0 — real certificate

Real CETs and real anonymous proofs.

## H1 — simulate anonymous proofs

Replace each proof with a zero-knowledge simulation.

Loss:

\[
s\epsilon_{zk}.
\]

## H2 — replace CET masks

For each challenge signer replace:

\[
F_{k_i}(\tau)
\]

with an independent uniform field element.

By a sequence of \(s\) hybrids:

\[
s\epsilon_{PRF}.
\]

After this step every public CET is uniform over \(\mathbb F\), independent of signer identity.

Sorting or canonicalizing the tag list is a deterministic function of an identity-independent random multiset.

Except for the negligible tag-collision event, the resulting public certificate distribution is independent of \(b\).

Thus:

\[
\boxed{
Adv^{Anon}_{CEQS}
\le
s\epsilon_{zk}
+
s\epsilon_{PRF}
+
\binom s2 2^{-256}.
}
\]

If the concrete backend exposes additional base-threshold-ring transcript information, add its published anonymity advantage as an extra term.

This completes R2 at the abstract proof level.

---

# 10. Theorem — cross-topic unlinkability

Consider the same honest signer on:

\[
\tau_0\ne\tau_1.
\]

Tags are:

\[
e_0=F_k(\tau_0)+c_0x,
\]

\[
e_1=F_k(\tau_1)+c_1x.
\]

Replace the two PRF outputs by independent uniform field elements:

\[
R_0,R_1.
\]

Hybrid cost:

\[
2\epsilon_{PRF}.
\]

Then:

\[
e_0=R_0+c_0x,
\qquad
e_1=R_1+c_1x
\]

are independent uniform field elements.

Therefore no efficient test can link them better than chance, except through the proof transcript.

With ZK proofs included:

\[
\boxed{
Adv^{CrossTopicLink}
\le
2\epsilon_{PRF}
+
2\epsilon_{zk}.
}
\]

---

# 11. Lemma — same-message linkability is intentional

For the same:

\[
(i,\tau,M),
\]

all inputs to CET are deterministic.

Therefore:

\[
e_i^{(1)}=e_i^{(2)}.
\]

Thus duplicate signing/retransmission of the identical statement is publicly linkable.

However:

\[
c_0=c_1
\]

so the conflict extraction denominator is zero.

No \(x_i\) is obtained from the pair.

This is explicit permitted leakage in the anonymity definition.

---

# 12. Theorem — conflict extraction completeness

Let two accepted certificates be:

\[
\Sigma_0
\]

and:

\[
\Sigma_1
\]

for conflicting canonical messages:

\[
M_0\ne M_1
\]

in the same topic \(\tau\).

By threshold soundness, except with cryptographic failure, their hidden signer sets satisfy:

\[
|S_0|,|S_1|\ge q.
\]

For:

\[
n=3f+1,
\qquad
q=2f+1,
\]

quorum intersection gives:

\[
|S_0\cap S_1|
\ge
2q-n
=
f+1.
\]

Take:

\[
i\in S_0\cap S_1.
\]

Its two tags are:

\[
e_{i,0}
=
r_{i,\tau}+c_0x_i,
\]

\[
e_{i,1}
=
r_{i,\tau}+c_1x_i.
\]

Subtract:

\[
e_{i,0}-e_{i,1}
=
(c_0-c_1)x_i.
\]

If:

\[
c_0\ne c_1,
\]

then:

\[
x_i
=
(e_{i,0}-e_{i,1})
(c_0-c_1)^{-1}.
\]

The extractor scans every pair in:

\[
E_0\times E_1,
\]

so this pair is tested.

Registry uniqueness gives one identity for:

\[
G_{tr}(x_i)=X_i.
\]

Thus every common signer is output.

Therefore:

\[
\boxed{
|ExtractConflict(\Sigma_0,\Sigma_1)|
\ge
|S_0\cap S_1|
\ge
f+1
}
\]

except for:

- certificate extraction/soundness failure;
- \(H_F\) challenge collision;
- trace-commitment ambiguity.

This is the strongest part of CE-QS: once the exact certificate semantics are granted, the conflict-extraction proof is deterministic.

---

# 13. R3 — strong registered-key trace soundness in the ROM

The simple CET construction is **not** claimed secure in the strongest Tetris adversarial-key game where keys and messages may be chosen together with no registration ordering.

CE-QS instead uses its actual BFT lifecycle:

\[
\boxed{
\text{registry fixed first}
\rightarrow
\text{topic/messages chosen later}.
}
\]

This ordering is load-bearing.

Define a false trace as outputting registered identity \(\ell\) even though:

\[
\ell\notin S_0\cap S_1.
\]

Condition on successful proof extraction for both certificates.

Take any tag pair generated by identities:

\[
a\in S_0,
\qquad
b\in S_1.
\]

The extractor candidate is:

\[
x^*
=
\frac{r_a-r_b+c_0x_a-c_1x_b}
{c_0-c_1}.
\]

A false trace to registry identity \(\ell\) requires either:

### Event B1 — trace commitment failure

\[
x^*\ne x_\ell
\]

but:

\[
G_{tr}(x^*)=X_\ell.
\]

This is bounded by:

\[
\epsilon_{tr-bind}.
\]

### Event B2 — algebraic false equality

\[
x^*=x_\ell.
\]

For fixed registered secrets/masks this gives:

\[
r_a-r_b
+
c_0(x_a-x_\ell)
-
c_1(x_b-x_\ell)
=
0.
\]

If \(a=b=\ell\), this is a true common signer and not a false trace.

Otherwise the equation constrains at least one fresh challenge value.

Because the registry is fixed before message queries, and \(H_F\) is modeled as a random oracle to \(\mathbb F^*\), each pair of challenge-oracle queries satisfies the required nontrivial linear relation with probability at most approximately:

\[
2^{-256}.
\]

Let the adversary make at most:

\[
Q_H
\]

challenge-hash queries.

Union bound over query pairs, tag pairs and registry targets gives the conservative ROM term:

\[
\frac{n|E_0||E_1|Q_H^2}{2^{256}}.
\]

For \( |E_0|,|E_1|\le q\):

\[
\frac{nq^2Q_H^2}{2^{256}}.
\]

Hence:

\[
\boxed{
\begin{aligned}
Adv^{FalseTrace}_{CEQS}
\le{}&
2q\epsilon_{ext}
+
\epsilon_{auth-bind}
+
\epsilon_{tr-bind}
+
\epsilon_{mask-bind}\\
&+
\epsilon_H
+
\frac{nq^2Q_H^2}{2^{256}}.
\end{aligned}
}
\]

This proves R3 in the **registration-first classical ROM model**, subject to the extraction/binding assumptions.

It also explains precisely why registration order is part of the theorem.

---

# 14. Corollary — honest non-frameability / exculpability

If an honest identity \(\ell\) did not participate in both conflicting certificates, then a successful accusation of \(\ell\) is a false trace.

Therefore:

\[
\boxed{
Adv^{FrameHonest}
\le
Adv^{FalseTrace}.
}
\]

This matches the purpose of Tetris's exculpability property: an honest user that did not double-authenticate cannot be falsely accused.

---

# 15. R4 — post-exposure authentication security

Assume a genuine conflict exposes:

\[
x_i.
\]

The adversary does **not** receive:

\[
sk_i
\]

or:

\[
k_i.
\]

Suppose it later creates a fresh accepted contribution attributed to \(i\).

By A2, extract:

\[
(i,sk_i',x_i',k_i')
\]

satisfying the relation.

Because the registry tuple is fixed:

\[
AuthRel(pk_i,sk_i')=1,
\]

\[
G_{tr}(x_i')=X_i,
\]

\[
G_{mask}(k_i')=K_i.
\]

Knowing \(x_i\) only helps satisfy the middle equation.

The adversary must still obtain valid openings for the authentication and mask bindings.

Thus, except for extraction/binding failure, a successful post-exposure forge breaks either authentication-key hardness or mask-key preimage/binding security.

Therefore:

\[
\boxed{
Adv^{PostExposureForge}
\le
\epsilon_{ext}
+
\epsilon_{auth}
+
\epsilon_{auth-bind}
+
\epsilon_{mask-bind}.
}
\]

Operationally, a traced validator is removed/re-keyed at the next safe epoch transition; the theorem above shows that disclosure of \(x_i\) alone is not equivalent to disclosure of the authentication key.

---

# 16. BFT conflict-accountability theorem

Assume:

1. \(n=3f+1\);
2. at most \(f\) Byzantine validators;
3. honest validators never authenticate two conflicting messages in the same conflict domain;
4. CE-QS exact certificate soundness;
5. CE-QS conflict extraction completeness.

Suppose two conflicting certificates verify.

Each contains at least:

\[
q=2f+1
\]

distinct signer identities.

Their intersection contains at least:

\[
f+1.
\]

Since at most \(f\) identities are Byzantine, at least one common signer is honest.

But an honest signer never authenticates both conflicts.

Contradiction.

Therefore two conflicting valid CE-QS quorum certificates can coexist only if:

- the base BFT vote rule failed;
- persistent signer state rolled back;
- or one of the cryptographic bad events occurred.

A union-bound form is:

\[
\boxed{
Adv^{BFTConflict}
\le
2\epsilon_{CertSound}
+
\epsilon_{Extract}
+
\epsilon_{VoteRollback}
+
Adv^{BaseSafety}.
}
\]

This theorem connects Target B back to the v0.8 BFT proof architecture.

---

# 17. ELBA theorem — corrected proof and practical consequence

ELBA's published definition gives:

\[
n_f<n_p.
\]

The verifier's accepted proof has a knowledge extractor producing:

\[
W(S)>n_f.
\]

To guarantee at least:

\[
q=43,
\]

set:

\[
n_f=42.
\]

The smallest completeness threshold is:

\[
n_p=43.
\]

Therefore Byzantine-independent liveness is **not logically impossible**.

However, the published Telescope parameter formula gives:

\[
u\ge 3991
\]

at 128-bit soundness/completeness.

The source paper's Example 6.3 says the proof size can be evaluated by multiplying the size of one signature by \(u\).

At ring size 64, its linkable AES128 ring signature is about:

\[
9.91\text{ KB}.
\]

Thus the zero-slack ELBA proof is approximately:

\[
3991\times9.91\text{ KB}
\approx
38.6\text{ MiB}.
\]

This is far beyond the CE-QS 32-KiB practical target.

Therefore the actual theorem is:

\[
\boxed{
\text{ELBA preserves exact 43-of-64 semantics in principle, but the zero-slack parameterization destroys compactness.}
}
\]

This is stronger and more precise than saying ELBA is simply incompatible with BFT liveness.

---

# 18. Concrete size theorem for the current VOLEitH exact baseline

The CCS 2025 paper reports approximately:

\[
9.91\text{ KB}
\]

for one **linkable** AES128 ring signature at ring size:

\[
2^6=64.
\]

The exact Figure-8 threshold construction concatenates \(t\) partial signatures and verifies all of them.

For:

\[
q=43,
\]

the proof payload is therefore roughly:

\[
43\times9.91\text{ KB}
=
426.13\text{ KB}
\approx
0.416\text{ MiB},
\]

before adding CE-QS tracing material.

The CET list itself is only:

\[
43\times32
=
1376\text{ bytes}.
\]

Therefore:

\[
\boxed{
\text{the current exact VOLEitH concatenation is sidecar-free but fails the 32-KiB compactness gate by more than an order of magnitude.}
\]

This is a proof-by-source-parameter calculation, not a benchmark of a CE-QS implementation.

It changes the backend priority:

1. VOLEitH remains the best **relation/proof prototype**;
2. it is not currently a viable exact compact final certificate by concatenation;
3. a compact **exact** aggregator is now mandatory for Target B.

---

# 19. Exact compactness now reduces to one missing primitive interface

Define an exact anonymous aggregation primitive:

\[
ExactAgg
\]

with algorithms:

\[
Aggregate,
Verify,
ExtractWitnesses.
\]

Required property:

> Every accepted aggregate for threshold \(q\) admits extraction of at least \(q\) distinct valid CE-QS witnesses, with no \(n_p/n_f\) approximation gap.

If such a primitive has:

\[
|Aggregate|=O(poly(\lambda,\log n))
\]

and can incorporate the CET relation, then all proofs in Sections 5–16 lift unchanged.

The strongest published candidate family identified so far is GC-TRS/CTRS, whose final signature contains one aggregated signature and one \(t\)-out-of-\(n\) proof, with CTRS logarithmic in ring size.

The missing theorem is no longer "invent tracing."

It is:

\[
\boxed{
\textbf{bind CET to an exact compact PQ threshold-ring aggregate while preserving extraction and anonymity.}
}
\]

---

# 20. QROM lift — theorem schema, not completed proof

The classical/ROM reductions above use:

- zero-knowledge/simulation;
- extractability;
- pseudorandom tag hybrids;
- random-oracle challenge relations.

CRYPTO 2025 provides an improved QROM analysis and a Fiat–Shamir transform applicable to VOLE-in-the-Head-based signatures.

A CE-QS QROM theorem would follow if the chosen concrete backend proves:

1. QROM zero knowledge for the expanded relation;
2. QROM weak simulation extractability/knowledge soundness;
3. quantum pseudorandomness of the mask tag function given public bindings;
4. QROM collision/preimage bounds for \(H_F,G_{tr}\);
5. a quantum analogue of the registration-first false-trace random-oracle argument.

The first four have known methodological precedents.

The fifth must still be written carefully using a QROM query-bound technique; the classical \(Q_H^2/2^{256}\) union bound cannot simply be relabeled quantum-secure.

Thus:

\[
\boxed{
\text{the classical/ROM proof stack is complete at the abstract level; the CE-QS-specific QROM reduction remains open.}
\]

---

# 21. Proof status table

| Property | Paper proof status after v0.5 |
|---|---|
| CET algebraic correctness | **proved** |
| One-tag hiding | **proved conditionally on auxiliary-input PRF security** |
| Duplicate-signer/identity distinctness | **proved conditionally on extraction + binding** |
| Exact threshold soundness | **proved conditionally on extraction + auth hardness** |
| Certificate correctness | **proved conditionally** |
| Quorum anonymity | **proved conditionally in classical/ROM-style model** |
| Cross-topic unlinkability | **proved conditionally** |
| Same-message linkability | **proved exactly** |
| Conflict extraction completeness | **proved conditionally; combinatorial/algebraic core exact** |
| Registered-key trace soundness | **proved conditionally in registration-first classical ROM** |
| Honest non-frameability | **proved as corollary** |
| Post-exposure authentication security | **proved conditionally** |
| BFT conflict impossibility | **proved conditionally** |
| ELBA 43-of-64 impossibility | **retracted: false as a theoretical statement** |
| ELBA practical compactness at 43/42 | **shown infeasible by published parameter formula** |
| Exact VOLEitH concatenation under 32 KiB | **shown false from published size numbers** |
| Exact compact aggregate backend | **open** |
| Concrete CE-QS VOLEitH circuit | **open** |
| Concrete CTRS/GC-TRS CET adapter | **open** |
| QROM CE-QS proof | **open** |
| Independent cryptographic review | **open** |

---

# 22. Main abstract theorem

Let \(R_e\) be a fixed registry committed before conflict messages are chosen.

Let exact CE-QS verification guarantee extractable witnesses for at least:

\[
q=2f+1
\]

distinct registry identities.

Assume A1–A9.

Then except with probability bounded by the sum of the corresponding primitive advantages:

1. every accepted exact certificate has at least \(q\) distinct registered signer witnesses;
2. a single certificate hides its signer set subject to the stated permitted leakage;
3. tags are unlinkable across distinct topics;
4. two conflicting same-topic certificates reveal every common signer;
5. any two BFT quorums reveal at least \(f+1\) common signers;
6. an honest identity that did not double-authenticate is not falsely accused;
7. exposing a trace secret does not by itself enable future authentication.

Formally:

\[
\boxed{
\begin{aligned}
Adv^{CEQS}_{bad}
\le{}&
O(q)(\epsilon_{cor}+\epsilon_{ext}+\epsilon_{zk}+\epsilon_{PRF})\\
&+
\epsilon_{auth}
+
\epsilon_{auth-bind}
+
\epsilon_{tr-bind}
+
\epsilon_{mask-bind}
+
\epsilon_H\\
&+
\frac{nq^2Q_H^2}{2^{256}}
+
\epsilon_{rollback}.
\end{aligned}
}
\]

The exact coefficient depends on which game is being bounded; this displayed inequality is a conservative summary, not a replacement for the separate game bounds above.

---

# 23. What the proof has actually accomplished

The CE-QS construction is no longer merely "specified but unproved."

The **abstract cryptographic composition** now has paper reductions for the classical/ROM milestone.

However, the full Target-B claim:

> compact, exact, sidecar-free, PQ, conflict-extractable quorum certificate

is still not solved because the currently implemented exact VOLEitH threshold-ring backend is too large by concatenation, while its ELBA compression is approximate and becomes enormous at the zero-slack 43/42 parameterization.

Thus the remaining missing link is sharper than before:

\[
\boxed{
\textbf{an exact compact PQ anonymous threshold aggregate that can prove the CE-QS relation.}
}
\]

GC-TRS/CTRS is currently the strongest published family to investigate for that slot.

---

# 24. Next proof/implementation milestone

The next milestone should not be another algebra mock.

It should be two parallel artifacts:

### A. CE-QS relation implementation

Implement:

\[
\mathcal R_{CEQS}
\]

inside the official VOLEitH codebase to validate the proof relation and obtain real cost numbers.

### B. Exact compact aggregator feasibility study

Implement or formally map CET into GC-TRS/CTRS and determine whether:

\[
|\Sigma|\le32\text{ KiB}
\]

at:

\[
n=64,\quad q=43.
\]

If the exact compact adapter cannot meet this gate, Target B remains theoretically accountable and sidecar-free but does not meet the project's compactness goal.

---

# 25. Source anchors used in this proof pass

- Chiang et al., *Post-Quantum Threshold Ring Signature Applications from VOLE-in-the-Head*, CCS 2025:
  - Section 5.1 key binding and tag pseudorandomness;
  - Figure 8 exact threshold-ring construction;
  - Theorem 5.9;
  - Lemmas B.1–B.3;
  - Definition 6.1 / Theorem 6.2 for ELBA;
  - Table 1 size data.
- Avitabile, Botta, Fiore, *Tetris!*, ESORICS 2025:
  - DAPT Definitions 21–23;
  - traceability, anonymity and exculpability definitions.
- Boneh, Kim, Nikolaenko, *Lattice-Based DAPS and Generalizations*, ACNS 2017:
  - post-quantum conditional secret disclosure.
- Baum et al., *Shorter, Tighter, FAESTer*, CRYPTO 2025:
  - QROM analysis and VOLE-in-the-Head Fiat–Shamir methodology.
- Lin et al., *Generic Construction of Threshold Ring Signatures and Lattice-based Instantiations*, DCC 2025:
  - exact aggregated-signature + \(t\)-out-of-\(n\) proof architecture;
  - CTRS logarithmic ring-size claim.
