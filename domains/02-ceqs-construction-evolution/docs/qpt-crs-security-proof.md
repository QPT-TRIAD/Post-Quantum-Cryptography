# CE-QS v1.3 — QPT/CRS Security Theorem
## A Post-Quantum, Sidecar-Free Hidden-Signer Quorum Certificate in the CRS Model

**Status:** formal proof continuation from v1.2.  
**Date:** 2026-09-09.  
**Track:** hidden-signer Target \(B_1\).  
**Security model:** QPT adversaries, common-reference-string setup, no random oracle in the load-bearing theorem.  
**Claim boundary:** v1.3 proves theoretical post-quantum existence **conditionally on explicit QLWR/Q-LWE/QEUF/QCR assumptions**. It does **not** prove a <32-KiB certificate or a practical setup/proving cost.

---

# 0. What v1.3 changes

v1.2 closed the LWR-SCCH trace adapter only in the classical ROM and left four quantum issues:

1. quantum LWR/wPRF security;
2. statistical uniqueness under quantum attacks;
3. quantum-accessible topic-base derivation;
4. a QROM-secure simulation-extractable local proof.

v1.3 removes items 3 and 4 from the QROM entirely.

### Topic bases

Instead of deriving bases with a random oracle, sample all bases for a bounded epoch as part of a public trace CRS.

### Local and outer proofs

Instead of Fiat--Shamir/Stern, use a post-quantum simulation-extractable NIZK for NP in the CRS model.

Jawale--Khurana prove that, assuming polynomial quantum hardness of LWE, such a simulation-extractable, adaptive multi-theorem computationally zero-knowledge argument for NP exists in the CRS model.

The remaining trace assumption is therefore the quantum hardness of the selected LWR distribution plus statistical uniqueness of the wPRF.

---

# 1. Notation

To avoid collision between BFT and lattice notation:

### BFT

\[
N=3F+1,
\qquad
Q=2F+1.
\]

Reference deployment:

\[
N=64,\quad F=21,\quad Q=43.
\]

### Lattice wPRF

Use:

\[
\nu
\]

for lattice secret dimension,

\[
q_L
\]

for the large LWR modulus,

\[
p
\]

for the rounded output modulus,

\[
m
\]

for the number of LWR rows.

The wPRF is:

\[
F_s(X)
=
\lfloor Xs\rceil_p
\in
\mathbb Z_p^m,
\]

for:

\[
s\in\mathbb Z_{q_L}^{\nu},
\qquad
X\in\mathbb Z_{q_L}^{m\times \nu}.
\]

For public tracing we require \(p\) prime.

---

# 2. Bounded conflict-domain budget

Each epoch declares a maximum number:

\[
D_{\max}
=
poly(\lambda)
\]

of conflict-domain slots.

A canonical injective map:

\[
DomainIndex(\tau)
\rightarrow
j\in[D_{\max}]
\]

assigns each admissible:

\[
\tau=(chain,e,h,v,\phi)
\]

to one slot.

If the epoch would exceed:

\[
D_{\max},
\]

the protocol performs a safe epoch rollover or safe halt before signing in an unallocated slot.

This is analogous to the query-budget hard cap already used in the Target-A proof architecture.

---

# 3. Trace Base CRS

`TraceSetup` samples independently and uniformly:

### Registry base

\[
A
\leftarrow
\mathbb Z_{q_L}^{m\times\nu}.
\]

### Per-domain link bases

For every:

\[
j\in[D_{\max}],
\]

sample:

\[
B_j
\leftarrow
\mathbb Z_{q_L}^{m\times\nu}.
\]

### Per-domain trace bases

Let:

\[
\kappa_C=384
\]

be the challenge-digest length.

Choose:

\[
d
=
\left\lceil
\frac{\kappa_C}{\log_2 p}
\right\rceil
\]

so that:

\[
p^d\ge2^{384}.
\]

For every \(j\) and \(r\in[d]\), sample:

\[
\widehat B_{j,r}
\leftarrow
\mathbb Z_{q_L}^{m\times\nu}.
\]

Publish all matrices as:

\[
crs_{\rm base}.
\]

They are sampled **before** validator trace keys and before consensus messages.

No participant chooses a topic base.

No hash-to-matrix random oracle appears in the theorem.

---

# 4. Setup-size honesty

The Trace Base CRS is polynomial but may be large.

Its raw matrix cost is:

\[
\boxed{
|crs_{\rm base}|
=
\bigl(
1+D_{\max}(1+d)
\bigr)
m\nu
\lceil\log_2 q_L\rceil
\text{ bits}.
}
\]

This is global epoch setup state, not a per-certificate sidecar.

v1.3 makes **no claim** that this setup is practically small.

A QROM hash-to-matrix derivation may later compress it, but that is an optimization adapter, not part of the load-bearing theorem.

---

# 5. Trace-key registration

Validator \(i\) samples:

\[
s_i\leftarrow\mathbb Z_{q_L}^{\nu}
\]

and registers:

\[
\boxed{
y_i=F_{s_i}(A).
}
\]

The epoch registry rejects duplicate \(y_i\).

Authentication signing keys:

\[
(sk_i^A,pk_i^A)
\]

are generated independently.

---

# 6. QLWR assumption

Define `QLWR` as the ordinary LWR distinguishing experiment except that the distinguisher is a quantum polynomial-time machine receiving polynomially many **classical random samples**:

\[
(X_j,F_s(X_j))
\]

or:

\[
(X_j,U_j),
\]

where the \(X_j\)'s are independent uniform matrices and the \(U_j\)'s are independent uniform elements of the wPRF range.

Let:

\[
\epsilon_{\rm QLWR}
\]

be the maximum QPT distinguishing advantage for the deployed sample bound.

v1.3 does not silently identify this assumption with LWE for arbitrary parameters.

Known LWE-to-LWR reductions are parameter/sample dependent.

A production assumption ledger must either:

- justify the selected LWR parameters through an appropriate reduction; or
- state QLWR directly.

---

# 7. QPT weak-pseudorandomness theorem

### Theorem 7.1

Under QLWR, the Yang--Au--Lai--Xu--Yu function is a weak pseudorandom function against QPT distinguishers with classical random-sample access.

### Proof

A wPRF sample is exactly:

\[
(X,\lfloor Xs\rceil_p).
\]

A random-function sample is exactly:

\[
(X,U)
\]

with independent uniform \(U\) in the output range.

Therefore a QPT wPRF distinguisher is directly a QPT LWR distinguisher on the same sample sequence.

No rewinding, measurement, oracle programming, or classical extraction is used.

Thus:

\[
\boxed{
\epsilon_{\rm QwPRF}
\le
\epsilon_{\rm QLWR}.
}
\]

\[
\blacksquare
\]

The source paper's classical Theorem 4.1 describes this reduction as direct from LWR; v1.3 simply quantifies the identical distributional reduction over QPT distinguishers.

---

# 8. Statistical uniqueness theorem

Yang et al. prove that when:

\[
m
\ge
\frac{\nu(\log q_L+1)}
{\log p-1},
\]

the probability over uniform:

\[
X\leftarrow
\mathbb Z_{q_L}^{m\times\nu}
\]

that **there exist** two distinct secrets:

\[
s_0\neq s_1
\]

with:

\[
F_{s_0}(X)=F_{s_1}(X)
\]

is bounded by a negligible counting term.

Their proof gives the displayed bound:

\[
\boxed{
\delta_U
\le
\frac{\nu}{2^\nu}.
}
\]

This statement already quantifies existentially over all colliding keys.

It is information-theoretic.

Therefore it holds against computationally unbounded classical or quantum adversaries.

---

# 9. Epoch-wide uniqueness event

The SCCH proof requires same-input uniqueness on:

- the registry base \(A\);
- every link base \(B_j\).

There are:

\[
D_{\max}+1
\]

such independent matrices.

By union bound:

\[
\boxed{
\delta_{\rm BaseBad}
\le
(D_{\max}+1)
\frac{\nu}{2^\nu}.
}
\]

Condition on the complement event:

\[
GoodBase.
\]

Then, simultaneously for every epoch domain, each link output binds one wPRF secret key.

No quantum search argument is necessary because the bad-base event is decided entirely at CRS generation.

---

# 10. Strong uniqueness is optional in the main adapter

v1.2 carried a separate strong-uniqueness assumption for outputs under two independently sampled inputs.

The QPT/CRS SCCH trace gate only needs **same-input uniqueness** on:

\[
A
\]

and:

\[
B_j.
\]

All trace bases:

\[
\widehat B_{j,r}
\]

are used only for pseudorandom masking, not to decide whether two handles belong to one key.

Therefore the main v1.3 trace/non-frameability theorem drops strong uniqueness from its minimal assumption list.

It remains available as defense-in-depth and for alternative adapters.

---

# 11. QPT one-wayness theorem

Yang et al. Lemma F.1 proves that weak pseudorandomness plus uniqueness imply one-wayness of a random wPRF input/output pair when the domain and range are super-polynomial.

The reduction is straight-line:

1. obtain two challenge samples;
2. give the first to the key-recovery adversary;
3. forward each classical sample query to the challenge oracle;
4. test the recovered key on both challenge samples.

There is no rewind of the adversary.

Therefore the reduction continues to work when the adversary is internally quantum, provided its interface to the sample oracle is classical.

### Theorem 11.1

Under QLWR, statistical uniqueness, and super-polynomial domain/range:

\[
\boxed{
\epsilon_{\rm QOW}
\le
\epsilon_{\rm QLWR}
+
\delta_U
+
\delta_{\rm dom}
+
\delta_{\rm rng}.
}
\]

Here:

- \(\delta_{\rm dom}\) bounds equality of the two independently sampled inputs;
- \(\delta_{\rm rng}\) bounds a random second output matching the uniquely determined key's output.

Both are negligible for the deployed wPRF spaces.

\[
\blacksquare
\]

---

# 12. Post-quantum simulation-extractable NIZK

Jawale--Khurana prove:

> Assuming polynomial quantum hardness of LWE, there exists a simulation-extractable, adaptive multi-theorem computationally zero-knowledge argument for NP in the common reference string model.

Denote one independent instance by:

\[
\mathsf{SEZK}.
\]

Security terms:

\[
\epsilon_{\rm SE},
\qquad
\epsilon_{\rm ZK}.
\]

v1.3 uses independent domain-separated CRSs for:

- local handle certification;
- the outer hidden-quorum proof.

No Fiat--Shamir transform is required.

No QROM is required for proof extraction.

---

# 13. Quantum-collision-resistant message challenge

Use:

\[
H_C:
\{0,1\}^\star
\rightarrow
\{0,1\}^{384}
\]

as a **quantum collision-resistant hash function**.

For canonical conflict statement:

\[
x_C
=
enc(
\texttt{CEQS-CHALLENGE-v2},
epoch,\tau,H(M)
),
\]

compute:

\[
D=H_C(x_C).
\]

Encode \(D\) injectively in base \(p\):

\[
(c_1,\ldots,c_d)
=
Enc_p(D)
\in
\mathbb Z_p^d.
\]

Because \(p\) is prime, every nonzero coordinate difference is invertible.

If two distinct canonical statements have equal challenge vectors, they give a collision in \(H_C\).

Thus:

\[
\boxed{
\epsilon_{\rm ChallengeEvasion}
\le
\epsilon_{\rm QColl}(H_C).
}
\]

For a random-function screening heuristic, 384 output bits correspond to the generic quantum collision scale \(2^{384/3}=2^{128}\).

The theorem itself relies on QCR security, not on the heuristic.

---

# 14. QPT SCCH handle

For domain slot:

\[
j=DomainIndex(\tau),
\]

validator \(i\) computes:

\[
t_i
=
F_{s_i}(B_j).
\]

For each:

\[
r\in[d],
\]

compute:

\[
u_{i,r}
=
F_{s_i}(\widehat B_{j,r}),
\]

and:

\[
z_{i,r}
=
u_{i,r}+c_r y_i
\pmod p.
\]

Public handle:

\[
\boxed{
h_i
=
(t_i,z_{i,1},\ldots,z_{i,d}).
}
\]

---

# 15. Local QPT certification relation

The local statement is:

\[
(R_e,i,j,H(M),h_i).
\]

The NP witness is:

\[
s_i.
\]

The relation checks:

\[
y_i=F_{s_i}(A),
\]

\[
t_i=F_{s_i}(B_j),
\]

and for every \(r\):

\[
z_{i,r}
=
F_{s_i}(\widehat B_{j,r})
+
c_r y_i.
\]

Because wPRF evaluation and rounding are polynomial-time computations, this is an NP relation.

Use:

\[
\pi_i^T
\leftarrow
SEZK.Prove(
crs_T,
statement_i;
s_i
).
\]

This closes the v1.2 "QROM Stern compiler" obligation.

---

# 16. Outer QPT hidden-quorum relation

Each signer sends the collector:

\[
C_i=
(i,\sigma_i,h_i,\pi_i^T)
\]

where:

\[
\sigma_i
\]

is an ordinary QEUF-CMA PQ vote signature.

The outer statement is:

\[
(R_e,\tau,H(M),Q,E),
\]

where \(E\) is the canonical public handle list.

The outer NP witness contains:

\[
(i_j,\sigma_j,h_j,\pi_j^T)_{j=1}^{s}
\]

and a permutation.

The relation verifies:

1. \(s=|E|\ge Q\);
2. all \(i_j\) are distinct;
3. every vote signature verifies on \(M\);
4. every local SEZK proof verifies;
5. the witness handles are exactly the public list \(E\).

Use an independent post-quantum SE-NIZK:

\[
\Pi_B
\leftarrow
SEZK.Prove(
crs_B,
X_B;
W_B
).
\]

Final QC:

\[
\boxed{
QC=
(v,e,\tau,H(M),Q,E,\Pi_B).
}
\]

No individual signature or local proof is transmitted in the final QC.

---

# 17. QPT threshold-soundness theorem

### Theorem 17.1

Assume:

- outer SE-NIZK soundness;
- QEUF-CMA vote signatures.

Then any accepted QC represents at least:

\[
Q
\]

distinct registered vote authorizations except with:

\[
\boxed{
\epsilon_{\rm Thresh}
\le
\epsilon_{\rm SE}^{B}
+
Q\epsilon_{\rm QEUF}.
}
\]

### Proof

Outer soundness gives a satisfying witness.

The relation contains at least \(Q\) distinct indices and a valid signature under every corresponding registered authentication key.

A selected uncompromised honest key that did not sign yields a QEUF forgery.

\[
\blacksquare
\]

---

# 18. QPT certified-handle theorem

### Theorem 18.1

Conditioned on `GoodBase`, every public handle in an accepted QC has a valid wPRF secret opening to the same hidden identity that supplied its vote signature, except with:

\[
\boxed{
\epsilon_{\rm HandleCert}
\le
\epsilon_{\rm SE}^{B}
+
Q\epsilon_{\rm SE}^{T}.
}
\]

### Proof

Outer extraction gives the hidden contribution tuple.

The local proof verifies for the same index.

Local simulation extractability yields a valid secret witness for each fresh malicious proof.

\[
\blacksquare
\]

---

# 19. QPT cross-key trace soundness

Take two validity-gated handles in one domain.

If their link components satisfy:

\[
t_0=t_1,
\]

local extraction gives:

\[
t_b=F_{s_b}(B_j).
\]

Under `GoodBase`, \(B_j\) has no distinct-key collision.

Therefore:

\[
s_0=s_1.
\]

Thus a pair produced under two different trace secrets never reaches the identity-extraction step.

Accounting for extraction failure:

\[
\boxed{
\epsilon_{\rm TraceSound}^{QPT}
\le
2\epsilon_{\rm SE}^{T}
+
\delta_{\rm BaseBad}.
}
\]

No affine-claw or QROM collision assumption appears.

---

# 20. QPT trace completeness

For the same secret and same domain:

\[
t_0=t_1.
\]

If:

\[
M_0\neq M_1
\]

and the challenge digest does not collide, choose:

\[
r
\]

with:

\[
c_{0,r}\neq c_{1,r}.
\]

Because the trace base is identical for the domain:

\[
u_{0,r}=u_{1,r}.
\]

Hence:

\[
z_{0,r}-z_{1,r}
=
(c_{0,r}-c_{1,r})y.
\]

Therefore:

\[
\boxed{
y=
(c_{0,r}-c_{1,r})^{-1}
(z_{0,r}-z_{1,r}).
}
\]

So:

\[
\boxed{
\epsilon_{\rm TraceCor}^{QPT}
\le
\epsilon_{\rm QColl}(H_C).
}
\]

---

# 21. QPT extended no-split theorem

Fix a registered trace key:

\[
y_i.
\]

Every fresh certified handle attributed to \(i\) yields, by local extraction, a secret opening:

\[
s
\]

with:

\[
F_s(A)=y_i.
\]

Conditioned on `GoodBase`, registry-base uniqueness implies one secret opening.

For one domain, deterministic evaluation on \(B_j\) therefore gives exactly one link value:

\[
t_i.
\]

Hence one registered identity cannot generate two unlinkable valid same-domain handle classes except with:

\[
\boxed{
\epsilon_{\rm NoSplit}^{QPT}
\le
Q_{\rm local}\epsilon_{\rm SE}^{T}
+
\delta_{\rm BaseBad}.
}
\]

---

# 22. QPT one-certificate anonymity

The public observer sees:

- the epoch registry;
- \(E=(h_1,\ldots,h_s)\);
- the outer proof.

It does not see the hidden indices.

Consider two admissible equal-size honest signer sets.

### Hybrid H0

Real QC.

### Hybrid H1

Use QPT zero knowledge to simulate:

\[
\Pi_B.
\]

Loss:

\[
\epsilon_{\rm ZK}^{B}.
\]

### Hybrid H2

For each challenge signer, view:

\[
(A,y_i)
\]

as one random LWR sample and:

\[
(B_j,t_i),
\quad
(\widehat B_{j,r},u_{i,r})
\]

as further independent random samples under the same secret.

By QLWR, replace the fresh outputs:

\[
t_i,u_{i,1},\ldots,u_{i,d}
\]

with independent uniform range elements while leaving the public anchor:

\[
y_i
\]

fixed.

Loss over \(s\) signers:

\[
s\epsilon_{\rm QLWR}.
\]

Then each:

\[
z_{i,r}=u_{i,r}+c_r y_i
\]

is uniform because \(u_{i,r}\) is uniform.

Thus the public handle distribution is independent of signer identity.

Therefore:

\[
\boxed{
Adv_{\rm Anon}^{QPT}
\le
\epsilon_{\rm ZK}^{B}
+
s\epsilon_{\rm QLWR}
+
\epsilon_{\rm HandleColl}.
}
\]

Same-message/same-domain linkability is explicit permitted leakage and is excluded from the anonymity challenge.

---

# 23. QPT one-wayness corollary

The straight-line lift of Yang et al. Lemma F.1 gives:

\[
\boxed{
\epsilon_{\rm QOW}
\le
\epsilon_{\rm QLWR}
+
\delta_U
+
\delta_{\rm dom}
+
\delta_{\rm rng}.
}
\]

This is the term used in extended exculpability.

No proof rewinding or random-oracle extraction is required.

---

# 24. QPT extended exculpability theorem

### Theorem 24.1

Let \(i^\star\) be an honest uncorrupted validator.

A QPT adversary that causes:

\[
VerifyBlame(QC_0,QC_1,i^\star)=1
\]

although \(i^\star\) did not produce both conflicting certified handles succeeds only if one of:

- outer SE-NIZK soundness;
- local simulation extraction;
- base uniqueness;
- trace-key one-wayness;
- registry uniqueness;
- challenge collision resistance;
- vote-signature security

fails.

A conservative bound is:

\[
\boxed{
\begin{aligned}
Adv_{\rm Frame}^{QPT}
\le{}&
2\epsilon_{\rm SE}^{B}
+
2Q\epsilon_{\rm SE}^{T}\\
&+
2Q\epsilon_{\rm QEUF}
+
\delta_{\rm BaseBad}\\
&+
\epsilon_{\rm QOW}
+
\epsilon_{\rm Registry}\\
&+
\epsilon_{\rm QColl}(H_C).
\end{aligned}
}
\]

### Proof sketch

Outer soundness binds the selected public handles to real distinct vote contributors.

Local extraction obtains a valid trace secret for every fresh malicious handle.

Equal link tags in one domain imply equal secrets under `GoodBase`.

The public trace equation then yields the registered public key opened by that secret.

If it equals the honest target key while the target did not create the adversarial handle, the reduction recovers a valid secret opening of the honest target's random registration pair:

\[
(A,y^\star),
\]

breaking QPT one-wayness.

Copies do not frame:

- same-message copies are only linked;
- changing the message invalidates the local certified statement.

\[
\blacksquare
\]

---

# 25. QPT conflict-extraction theorem

For:

\[
N=3F+1,
\qquad
Q=2F+1,
\]

two accepted conflicting QCs give hidden signer sets:

\[
S_0,S_1
\]

with:

\[
|S_0|,|S_1|\ge Q.
\]

Thus:

\[
|S_0\cap S_1|
\ge
2Q-N
=
F+1.
\]

Every common identity has one certified handle in each public list.

Trace completeness identifies it.

Therefore:

\[
\boxed{
|ExtractConflict(QC_0,QC_1)|
\ge
F+1
}
\]

except with the accumulated threshold/handle/challenge bad-event probability.

For the reference committee:

\[
\boxed{
|ExtractConflict|
\ge
22.
}
\]

---

# 26. Full QPT hidden-CE-QS theorem

### Theorem 26.1

Assume:

1. QLWR for the selected wPRF parameters/sample budget;
2. the statistical uniqueness condition of Theorem 4.1;
3. polynomial quantum hardness of LWE for the Jawale--Khurana SE-NIZKs;
4. QEUF-CMA security of the validator vote signature;
5. quantum collision resistance of the 384-bit challenge hash;
6. unique registry trace keys;
7. canonical encoding;
8. bounded Trace Base CRS domain slots;
9. durable no-double-vote state.

Then the distributed-certified-handle construction gives a **non-interactive transferable sidecar-free hidden-signer quorum certificate** secure against QPT adversaries with:

- exact threshold authorization;
- public signer-set anonymity subject to explicit same-topic link leakage;
- public conflict extraction;
- publicly verifiable blame;
- extended no-split counting;
- honest non-frameability;
- post-trace separation from the authentication key.

The theorem uses no random oracle.

The certificate is:

\[
\boxed{
QC=
(v,e,\tau,H(M),Q,E,\Pi_B).
}
\]

\[
\blacksquare
\]

---

# 27. What "post-quantum solved" means here

v1.3 closes **theoretical post-quantum security/existence**, conditionally on explicit QPT assumptions.

It does not close practical compactness.

The public handle size remains:

\[
\boxed{
|h|
=
(d+1)m\lceil\log_2 p\rceil
\text{ bits}.
}
\]

The final QC size is:

\[
\boxed{
|QC|
=
Q(d+1)m\lceil\log_2 p\rceil
+
|\Pi_B|
+
O(\lambda).
}
\]

The generic LWE-based SE-NIZK theorem establishes polynomial-size proof existence, not a \(<32\)-KiB proof.

Thus:

\[
\boxed{
\textbf{sidecar-free + hidden-signer + QPT security: theoretically closed;}
}
\]

\[
\boxed{
\textbf{compact/practical <32 KiB: still open.}
}
\]

---

# 28. Compactness search: what newly qualifies

The broad 2026 literature search identifies several relevant but non-closing directions.

## 28.1 Compact lattice set-membership NIZK without RO

Tran--Nguyen--Liu--Pieprzyk--Susilo (ePrint 2026/1885) introduce a standard-model lattice NIZK for set membership with proof size logarithmic in the set cardinality and ring-signature applications.

This could reduce registry-membership cost in future specialized local/outer proofs.

It is **not** a general NP BatchZK for 43 signature/handle verifications, so it does not discharge \(|\Pi_B|\).

---

## 28.2 Orthus

Bolboceanu--Bootle--Lyubashevsky--Merino-Gallardo--Seiler, CRYPTO 2026 / ePrint 2026/398, implement a succinct lattice proof system with sublinear verification for lattice-native relations.

Their Falcon aggregation benchmark reduces verifier time by roughly \(9\times\) at \(2^{17}\) signatures.

Orthus is highly relevant if CE-QS chooses lattice-native vote signatures/handles.

The accessible abstract does not provide a CE-QS 43-contribution proof-size figure, so no byte claim is made.

---

## 28.3 LaZer / LaBRADOR ecosystem

NIST's 2026 threshold-call preview explicitly presents LaZer as a transparent non-interactive lattice ZK argument of knowledge for module-lattice relations.

This is a serious implementation candidate for a **specialized** outer relation, especially if both vote signatures and trace handles are lattice-native.

Again, no CE-QS <32-KiB result is inferred.

---

## 28.4 Designated-verifier 16-KB lattice zkSNARK

Ishai--Su--Wu demonstrate lattice-based designated-verifier zkSNARKs with proofs just over 16 KB for a large NP relation after preprocessing.

This shows PQ succinctness in the desired byte regime is possible under a weaker verification model.

It is not directly usable for a public transferable QC because the verifier is designated.

---

## 28.5 Succinct ZK from one-way functions, CRYPTO 2026

The newest black-box OWF construction significantly reduces communication, but its proof length still contains a leading witness-size term.

It does not solve the CE-QS public-certificate compression target.

---

# 29. Stronger source synthesis

The research schools now align cleanly:

### Accountable anonymity / LWR

Supplies:
- deterministic link gate;
- public two-challenge identity extraction;
- statistical uniqueness;
- one-wayness reduction.

### Post-quantum SE-NIZK

Supplies:
- local handle certification;
- malicious-proof extraction;
- outer hidden-quorum proof;
- QPT zero knowledge.

### Quantum collision theory

Supplies:
- conservative 384-bit message-challenge sizing.

### Modern strong-linkability work

Supplies:
- the requirement that bases be canonical and counting must resist "more unlinkable outputs than owned keys."

### Succinct lattice proof systems

Supply:
- the current implementation frontier for making \(\Pi_B\) and/or lattice handle checks small.

---

# 30. Revised open-problem statement

The original frontier was:

> Can conflict-extractable compact PQ quorum signatures exist without a sidecar?

After v1.3, the theoretical existence/security question is no longer the main unknown.

The remaining frontier is:

\[
\boxed{
\textbf{Can the QPT-secure construction be compressed below the practical certificate gate?}
}
\]

Concretely:

1. replace the large generic LWR handle with a smaller SCCH satisfying the same theorem;
2. instantiate the outer QPT ZK relation with a succinct practical lattice/hash proof;
3. achieve:

\[
\boxed{
|QC|\le32\text{ KiB}
}
\]

at:

\[
N=64,\quad Q=43.
\]

The proof architecture no longer has to change if those adapters preserve the v1.3 interfaces.
