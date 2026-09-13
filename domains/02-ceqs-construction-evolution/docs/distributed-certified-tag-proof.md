# CE-QS v1.0 — Distributed Certified-Tag Proof
## Constructible Hidden-Signer, Sidecar-Free Conflict Accountability

**Status:** formal construction/proof continuation; fixes the v0.9 prover-knowledge gap.  
**Date:** 2026-09-09.  
**Track:** Target \(B_1\), hidden signer set.  
**Claim boundary:** this is an abstract cryptographic composition theorem. It does not claim a concrete <32-KiB implementation or a completed QROM reduction for the linear CET adapter.

---

# 0. Correction to v0.9: the outer prover cannot know validator trace secrets

The v0.9 Private Wrapper used a hidden witness containing:

\[
\{x_i,k_i\}_{i\in S}.
\]

That is not a constructible BFT protocol.

A leader/collector should receive votes, not every validator's private trace and mask secrets.

Therefore v1.0 replaces:

\[
\boxed{
\text{collector proves tag correctness from signer secrets}
}
\]

with:

\[
\boxed{
\text{each signer locally proves its own tag correctness;}
\quad
\text{collector proves possession of }q\text{ certified contributions}.
}
\]

This is a substantive construction correction, not merely a proof refactor.

---

# 1. Privacy model

v1.0 provides **public certificate signer-set privacy**.

The final transferable certificate hides the validator identities.

The collector/leader is allowed to learn the identities from the network messages it receives.

This is the natural BFT model: ordinary consensus leaders generally know which peers sent votes.

Hiding voters even from the collector requires anonymous transport/MPC and is a separate property not claimed here.

---

# 2. Registered keys

For epoch \(e\), validator \(i\) has two independent credentials.

## Authentication key

\[
(pk_i^A,sk_i^A)
\]

used to authorize the BFT vote.

## Trace key

\[
(pk_i^T,sk_i^T)
\]

used only for conflict accountability.

The two secret keys MUST be independently generated.

The registry is:

\[
R_e=
\{(i,pk_i^A,pk_i^T)\}_{i=1}^n.
\]

A trace-key disclosure must not imply authentication-key disclosure.

---

# 3. DAPT-shaped trace-tag abstraction

Use the Tetris DAPT interface as the security abstraction.

A trace-tag scheme:

\[
\mathsf{TT}
=
(
KeyGen_T,
Tag,
TagTrace
)
\]

has deterministic:

\[
e\leftarrow Tag(sk^T,\tau,M).
\]

For two different messages in one topic:

\[
TagTrace(e_0,e_1,M_0,M_1,pk^T)
\]

tests whether both tags were produced by the same trace key.

Required properties are the post-quantum analogues of Tetris Definitions 21–24:

### TT1. Key verifiability / unique registered trace key

The registered public trace key has a unique valid secret-key relation.

### TT2. Conflict trace completeness

For honest:

\[
e_b=Tag(sk_i^T,\tau,M_b),
\qquad
M_0\neq M_1,
\]

\[
Pr[
TagTrace(e_0,e_1,M_0,M_1,pk_i^T)=1
]
\ge
1-\epsilon_{\rm trace-cor}.
\]

### TT3. Cross-key trace soundness

Tags generated under different valid trace keys do not trace to either key except with:

\[
\epsilon_{\rm trace-sound}.
\]

### TT4. Tag pseudorandomness

A single admissible tag is indistinguishable from the scheme's random-tag distribution:

\[
\epsilon_{\rm tag-pr}.
\]

### TT5. Tag non-frameability

An adversary cannot create a pair that traces to an honest trace key that did not produce both conflicting tags except with:

\[
\epsilon_{\rm tag-frame}.
\]

These are security properties of the trace-tag primitive, not consequences of the outer batch proof.

---

# 4. Local certified-tag proof

A raw DAPT/CET tag is not sufficient.

The final proof must know that each public tag was honestly generated from a registered trace key.

Each validator therefore creates a **local certified-tag proof**.

Let:

\[
\mathsf{TagZK}
=
(
Setup_T,
Prove_T,
Verify_T
).
\]

The public local statement is:

\[
x_T=
(R_e,i,\tau,H(M),e_i).
\]

The witness is the signer's own trace-tag secret material:

\[
w_T=sk_i^T.
\]

The relation states:

1. \(pk_i^T\) is the registered trace key at index \(i\);
2. \(sk_i^T\) is a valid secret for \(pk_i^T\);
3.

\[
e_i=Tag(sk_i^T,\tau,M).
\]

Required:

- completeness;
- soundness;
- zero knowledge against a malicious collector.

The local proof need not hide \(i\) from the collector.

It MUST hide \(sk_i^T\).

---

# 5. Signer contribution protocol

For canonical consensus message \(M\) in conflict domain \(\tau\), validator \(i\):

1. checks its durable no-double-vote state;
2. computes ordinary PQ vote signature:

\[
\sigma_i
\leftarrow
Sign_A(sk_i^A,M);
\]

3. computes:

\[
e_i
\leftarrow
Tag(sk_i^T,\tau,M);
\]

4. computes:

\[
\pi_i^T
\leftarrow
Prove_T(
R_e,i,\tau,H(M),e_i;
sk_i^T
);
\]

5. sends:

\[
\boxed{
C_i=
(i,\sigma_i,e_i,\pi_i^T)
}
\]

to the collector.

No other validator and no collector receives \(sk_i^T\).

---

# 6. Collector verification

The collector accepts contribution \(C_i\) only if:

\[
Verify_A(pk_i^A,M,\sigma_i)=1
\]

and:

\[
Verify_T(R_e,i,\tau,H(M),e_i,\pi_i^T)=1.
\]

It collects:

\[
s\ge q
\]

contributions with distinct indices.

The collector forms canonical public tag list:

\[
E=
Sort(e_{i_1},\ldots,e_{i_s}).
\]

Duplicate public tags are rejected.

---

# 7. Outer batch-zero-knowledge relation

Let:

\[
\mathsf{BatchZK}
=
(
Setup_B,
Prove_B,
Verify_B
)
\]

be a zero-knowledge sound argument for the relation below.

Public statement:

\[
X_B=
(
R_e,
\tau,
H(M),
q,
E
).
\]

Witness:

\[
W_B=
(
(i_j,\sigma_j,e_j,\pi_j^T)_{j=1}^{s},
\pi
),
\]

where \(\pi\) is a permutation.

The relation:

\[
\mathcal R_{\rm DCET}(X_B;W_B)=1
\]

iff:

### B1. Threshold

\[
s=|E|\ge q.
\]

### B2. Distinct identities

\[
i_j\neq i_k
\quad
\forall j\neq k.
\]

### B3. Exact vote authorization

\[
Verify_A(pk_{i_j}^A,M,\sigma_j)=1
\quad
\forall j.
\]

### B4. Certified trace tags

\[
Verify_T(
R_e,
i_j,
\tau,
H(M),
e_j,
\pi_j^T
)=1
\quad
\forall j.
\]

### B5. Exact same-set public tag binding

\[
e_j=E_{\pi(j)}
\quad
\forall j,
\]

and \(\pi\) is a bijection onto all positions of \(E\).

Thus every hidden voter contributes exactly one public tag, and every public tag belongs to exactly one hidden voter in the witness.

---

# 8. Final certificate

The transferable certificate is:

\[
\boxed{
QC=
(
v,
e,
\tau,
H(M),
q,
E,
\Pi_B
)
}
\]

where:

\[
\Pi_B
\leftarrow
Prove_B(X_B;W_B).
\]

The individual PQ signatures and local tag proofs are **not** included in the final certificate.

They are witness material for the batch proof.

This is sidecar-free in the sense relevant to Target \(B_1\): no external evidence object must be fetched to verify or trace a conflict.

---

# 9. Constructibility theorem

### Theorem 9.1

The v1.0 prover is implementable without disclosing any validator trace secret to the collector.

### Proof

Validator \(i\) alone executes:

\[
Tag(sk_i^T,\tau,M)
\]

and:

\[
Prove_T(\ldots;sk_i^T).
\]

The collector receives only:

\[
(i,\sigma_i,e_i,\pi_i^T).
\]

The outer witness \(W_B\) consists only of these received values and a permutation.

It contains no:

\[
sk_i^A
\]

and no:

\[
sk_i^T.
\]

Therefore a collector can construct \(\Pi_B\) using exactly the data it receives in the protocol.

\[
\blacksquare
\]

This repairs the v0.9 constructibility gap.

---

# 10. Exact hidden-threshold soundness

### Theorem 10.1

Assume:

- BatchZK soundness;
- authentication-signature unforgeability.

If a v1.0 certificate verifies, then at least:

\[
q
\]

distinct registered identities authorized \(M\), except with the sum of those failure advantages.

### Proof

BatchZK soundness implies existence of a witness satisfying B1–B5.

B1 gives:

\[
s\ge q.
\]

B2 gives \(s\) distinct registered indices.

B3 gives a valid authentication signature under every corresponding registered public key.

If any uncompromised honest selected identity did not sign \(M\), B3 supplies a valid forgery.

Thus the certificate contains at least \(q\) distinct authorizations.

\[
\blacksquare
\]

A conservative bound is:

\[
\boxed{
Adv^{ThreshForge}
\le
\epsilon_{\rm BatchSound}
+
q\epsilon_{\rm SigForge}.
}
\]

---

# 11. Certified-tag soundness theorem

### Theorem 11.1

Assume BatchZK soundness and local TagZK soundness.

Then every public:

\[
e\in E
\]

in an accepted certificate is a valid trace tag generated with some registered trace key belonging to the same hidden identity that supplied a valid vote signature.

### Proof

By outer soundness obtain \(W_B\).

B5 maps every public tag position to one hidden contribution.

B4 says that contribution has an accepted local tag proof for the same hidden index.

By local TagZK soundness, the tag statement is true.

B3 binds the same hidden index to the vote signature.

Therefore:

\[
S_{\rm Vote}
=
S_{\rm Tag}.
\]

\[
\blacksquare
\]

Failure probability is bounded by:

\[
\boxed{
\epsilon_{\rm BatchSound}
+
q\epsilon_{\rm TagSound}.
}
\]

---

# 12. Public signer-set anonymity theorem

The collector learns the signer identities.

The final-certificate observer does not.

### Theorem 12.1

Assume:

- BatchZK zero knowledge;
- TT4 tag pseudorandomness.

For two equal-size admissible hidden signer sets, a public observer cannot distinguish which set generated the final certificate except with:

\[
\boxed{
Adv^{Anon}_{DCET}
\le
\epsilon_{\rm BatchZK}
+
q\epsilon_{\rm tag-pr}
+
\epsilon_{\rm tag-coll}.
}
\]

### Proof

Hybrid H0 is the real certificate.

H1 replaces \(\Pi_B\) by its zero-knowledge simulation.

The hidden identities, signatures, and local proofs disappear from the adversary's meaningful view.

H2 replaces each public tag by the random-tag distribution using TT4, one tag at a time.

The remaining public list is independent of signer identities, aside from accidental collisions.

\[
\blacksquare
\]

No anonymity property of the ordinary PQ signature scheme is required.

---

# 13. Conflict extraction

Given two accepted certificates:

\[
QC_0=(E_0,\Pi_0),
\qquad
QC_1=(E_1,\Pi_1)
\]

for conflicting \(M_0\neq M_1\) in the same topic \(\tau\):

1. verify both certificates;
2. for every:

\[
e_0\in E_0,\quad e_1\in E_1;
\]

3. for every registered trace public key \(pk_i^T\), test:

\[
TagTrace(
e_0,e_1,M_0,M_1,pk_i^T
).
\]

Every successful key is output.

This generic DAPT interface costs at most:

\[
|E_0||E_1|n
\]

trace checks.

At \(q=43,n=64\):

\[
43^2\cdot64
=
118336
\]

conflict-only checks.

A concrete algebraic CET can do better by recovering the identity token directly.

---

# 14. Conflict-extraction completeness theorem

### Theorem 14.1

Let:

\[
n=3f+1,
\qquad
q=2f+1.
\]

For two accepted conflicting certificates, except with proof/tag correctness failures:

\[
\boxed{
|ExtractConflict(QC_0,QC_1)|
\ge
f+1.
}
\]

### Proof

By Theorem 10.1, each certificate has a hidden signer set:

\[
S_0,S_1
\]

with:

\[
|S_0|,|S_1|\ge q.
\]

Quorum intersection gives:

\[
|S_0\cap S_1|
\ge
2q-n
=
f+1.
\]

By Theorem 11.1, each common signer \(i\) has one correctly generated public tag in each public list.

TT2 implies that pair traces to:

\[
pk_i^T.
\]

The extraction algorithm checks every pair and every registered trace key.

Therefore every common signer is output except with trace-correctness failure.

\[
\blacksquare
\]

---

# 15. Non-frameability theorem

### Theorem 15.1

Suppose an honest identity \(i\) did not produce certified trace tags in both conflicting certificates.

Then \(i\) is output by conflict extraction only if at least one of:

1. BatchZK soundness fails;
2. local TagZK soundness fails;
3. TT3 cross-key trace soundness fails;
4. TT5 tag non-frameability fails;
5. an authentication signature is forged.

Thus:

\[
\boxed{
\begin{aligned}
Adv^{Frame}_{DCET}
\le{}&
2\epsilon_{\rm BatchSound}
+
2q\epsilon_{\rm TagSound}\\
&+
\epsilon_{\rm trace-sound}
+
\epsilon_{\rm tag-frame}
+
2q\epsilon_{\rm SigForge}.
\end{aligned}
}
\]

The exact coefficient can be tightened in the final game proof.

The important point is structural: framing decomposes into independently named primitives.

---

# 16. BFT conflict-impossibility theorem

Assume:

1. \(n=3f+1\);
2. at most \(f\) Byzantine validators;
3. honest validators persistently refuse conflicting votes in one domain;
4. v1.0 certificate soundness and trace correctness.

If two conflicting certificates verify, Theorem 14.1 reveals at least:

\[
f+1
\]

common identities.

At most \(f\) are Byzantine.

Therefore at least one common identity is honest.

By Theorem 11.1 and vote-signature soundness, that honest identity authorized both conflicts.

This contradicts the durable honest voting rule unless:

- the cryptography failed;
- persistent state rolled back;
- or the base BFT safety theorem failed.

Thus:

\[
\boxed{
Adv^{BFTConflict}
\le
\epsilon_{\rm DCET}
+
\epsilon_{\rm rollback}
+
Adv^{BaseSafety}.
}
\]

---

# 17. Post-exposure security

The authentication key and trace key are independent.

If the concrete trace mechanism exposes \(sk_i^T\), or a derived blame secret, after a conflict, this does not by itself reveal:

\[
sk_i^A.
\]

Therefore the traced validator cannot forge future vote signatures solely from the trace event.

Operationally, a traced validator is removed/re-keyed at the next safe epoch transition.

The exact post-exposure theorem is:

\[
\boxed{
Adv^{PostTraceVoteForge}
\le
Adv^{QEUF}_{AuthSig}
+
\epsilon_{\rm key-separation}.
}
\]

---

# 18. PQ instantiation routes for the trace-tag layer

The generic theorem intentionally separates the trace-tag definition from its implementation.

## Route A — linear CET

The existing CE-QS tag:

\[
e_i=
F_{k_i}(\tau)+c x_i
\]

is a simple DAPT-shaped candidate.

It needs a PQ local proof of correct tag generation and a QPT false-trace theorem.

## Route B — PQ traceable-ring tag machinery

Feng–Liu–Li–Li–Wu (DCC 2021) give a general traceable-ring-signature framework built from:

- NIZK proof of knowledge;
- hash family;
- pseudorandom function with additional properties;

with lattice and symmetric-key instantiations proved in the QROM.

This is strong evidence that a PQ traceable-tag layer is feasible.

A formal reduction from their exact signature/tag syntax to TT1–TT5 remains an adapter theorem, not something v1.0 assumes silently.

## Route C — lattice DAPS/PAPS

Boneh–Kim–Nikolaenko construct the first lattice-based post-quantum DAPS and PAPS.

This gives a second conditional-disclosure route.

It is less attractive for CE-QS when the extracted value is the authentication signing key; a deployment should instead use an independently registered blame credential.

---

# 19. Succinct outer-proof route

The outer relation is a batch relation over:

\[
q
\]

private vote/tag contributions.

A generic NIZK proves it, but succinctness is the practical goal.

STOC 2024's *Batch Proofs Are Statistically Hiding* proves, among other results, that sufficiently compressing somewhere-sound non-interactive BARGs plus one-way functions imply adaptively sound non-interactive computational zero-knowledge arguments for NP.

This supplies a theoretical route from:

\[
\boxed{
\text{compressing batch argument}
\rightarrow
\text{hiding batch argument}
}
\]

without designing an anonymous threshold-ring signature.

It does not provide a CE-QS concrete byte count.

---

# 20. QROM screening for the linear CET adapter

This section is a **parameter-screening argument**, not the final QROM proof.

Let the linear CET challenge be:

\[
c=H_F(\tau,M)\in GF(2^\kappa).
\]

For a false cross-key trace to registered victim \(\ell\), a pair of correctly generated tags from identities \(a,b\) must satisfy an affine relation:

\[
A\,H_F(\tau,M_0)
+
B\,H_F(\tau,M_1)
=
D
\]

for fixed coefficients determined by the registered trace keys and topic masks.

There are three generic cases.

## One coefficient zero

The adversary must hit one specified random-oracle output.

This is preimage-style quantum search with generic scale:

\[
2^{\kappa/2}.
\]

## Both coefficients nonzero

The adversary searches for two oracle outputs satisfying a fixed affine relation.

This is claw/collision-shaped.

Known generic quantum collision finding for a random function has tight query scale:

\[
2^{\kappa/3},
\]

and optimal quantum claw-finding has the same cubic-root flavor in balanced domains.

Therefore the conservative generic quantum security screen is governed by:

\[
\kappa/3.
\]

---

# 21. 384-bit linear-CET profile

A 256-bit challenge/tag field gives only roughly:

\[
256/3
\approx
85.3
\]

generic quantum collision/claw bits.

That is not a conservative 128-bit target.

Set instead:

\[
\boxed{
\kappa=384.
}
\]

Then:

\[
384/3=128.
\]

The preimage-shaped cases screen at:

\[
384/2=192
\]

generic quantum bits.

Therefore the collision/claw branch remains dominant.

For \(q=43\), 384-bit public tags cost:

\[
43\cdot48
=
\boxed{2064\text{ bytes}}
\]

which is approximately:

\[
\boxed{2.016\text{ KiB}}.
\]

This replaces the earlier 256-bit / 1376-byte profile for any deployment targeting conservative 128-bit generic QROM resistance.

---

# 22. QROM caveat: affine-claw resistance is not ordinary collision resistance

The argument in Sections 20–21 does **not** prove the exact linear CET secure in QROM.

The false-trace condition is an affine relation between two challenge outputs, not merely:

\[
H(x)=H(y).
\]

Therefore the final proof must establish an explicit **Affine-Claw Resistance** lemma for the chosen hash-to-field construction in the QROM, or adopt a trace-tag primitive with a published QROM non-frameability theorem.

The 384-bit value is justified as a conservative generic-query parameter screen from known collision/claw complexity.

It is not a substitute for that reduction.

---

# 23. Formal status after v1.0

| Property | Status |
|---|---|
| v0.9 collector-secret constructibility | **corrected** |
| Distributed signer contribution protocol | **specified** |
| Collector learns no trace secret | **proved by construction** |
| Exact hidden threshold | **proved conditionally** |
| Vote/tag same-hidden-set binding | **proved conditionally** |
| Public signer anonymity | **proved conditionally** |
| Conflict extraction \(\ge f+1\) | **proved conditionally** |
| Non-frameability composition | **proved conditionally** |
| BFT accountability composition | **proved conditionally** |
| Generic DAPT security interface | **aligned to published Tetris definitions** |
| PQ trace-tag existence | **qualified by PQ TRS / DAPS literature** |
| Succinct hiding outer proof existence route | **qualified by BARG→NIZK literature** |
| Concrete <32-KiB outer proof | **open** |
| Linear CET exact QROM affine-claw proof | **open** |
| Conservative linear-CET tag width | **384 bits** |
| Public tag payload at q=43 | **2064 bytes** |

---

# 24. Remaining theoretical obligations

## O1. Concrete PQ trace-tag adapter

Either:

- prove the 384-bit linear CET satisfies TT1–TT5 against QPT adversaries; or
- instantiate TT1–TT5 from a published PQ traceable-ring/tag construction.

## O2. Outer BatchZK instantiation

Choose a concrete post-quantum proof system for:

\[
\mathcal R_{\rm DCET}
\]

and establish:

- soundness;
- zero knowledge;
- proof size;
- prover/verification cost.

## O3. Affine-claw QROM theorem

If the linear CET remains the preferred tag:

derive a query bound for the exact false-trace affine relation rather than importing ordinary collision resistance.

## O4. Collector Byzantine behavior

The collector may censor honest contributions.

This affects liveness, not certificate safety.

Base BFT leader/view-change machinery must provide recovery.

---

# 25. Main conclusion

The hidden-signer construction is now **constructible**.

No central prover needs validator trace secrets.

Each validator locally creates:

\[
\boxed{
\text{PQ vote signature}
+
\text{public trace tag}
+
\text{private-to-collector tag-certification proof}.
}
\]

The collector proves in zero knowledge that it possesses:

\[
q
\]

distinct valid vote/certified-tag pairs whose tags are exactly the public list \(E\).

The final certificate contains only:

\[
\boxed{
E+\Pi_B+O(\lambda).
}
\]

Conflict extraction remains public and sidecar-free.

At the conservative 384-bit trace-tag profile, the entire public tag list for 43 signers is only:

\[
\boxed{
2064\text{ bytes}.
}
\]

The remaining frontier is no longer protocol constructibility.

It is:

\[
\boxed{
\textbf{a concrete succinct PQ BatchZK instantiation}
+
\textbf{a QPT-secure trace-tag adapter}.
}
\]
