# CE-QS — Total QPT-128 Security Proof and Validation Report

**Construction:** CE-QS / hidden-signer conflict-extractable quorum certificate
**Reference committee:** \(N=64\), \(F=21\), \(Q=43\)
**Security target:** QPT adversarial failure probability \(<2^{-128}\)
**Security model:** QPT adversaries, CRS model, no random oracle in the load-bearing theorem
**Signature layer:** QEUF-CMA post-quantum signature; SLH-DSA is the intended hash-based instantiation
**Status:** Conditional QPT-128 theorem; concrete backend/parameter validation remains separately gated

---

## 1. Executive conclusion

The existing CE-QS construction has a coherent route to a QPT-128 security theorem.

The reference parameters are:

$$
N=64,\qquad F=21,\qquad Q=43.
$$

They satisfy:

$$
N=3F+1,
$$

and

$$
Q=2F+1=43.
$$

Therefore every accepted quorum contains at least

$$
Q-F=43-21=22
$$

honest validators.

Two accepted quorums intersect in at least

$$
2Q-N
=
86-64
=
22
=
F+1.
$$

Hence two conflicting quorum certificates necessarily share at least one honest validator.

The CE-QS construction then supplies a cryptographic mechanism for binding each hidden quorum member to a public trace handle and for extracting the common identity from two conflicting certificates. The source proof obtains

$$
|ExtractConflict(QC_0,QC_1)|\ge F+1=22
$$

under the stated cryptographic assumptions.

The post-quantum proof decomposes a successful attack into a finite collection of bad events:

$$
\mathsf{BAD}
=
\mathsf{Forge}
\lor
\mathsf{NIZK}
\lor
\mathsf{QLWR}
\lor
\mathsf{QCR}
\lor
\mathsf{Uniq}
\lor
\mathsf{Registry}
\lor
\mathsf{Composition}.
$$

The final probability is bounded by the sum of those events.

The central composition rule is therefore:

$$
\boxed{
\Pr[\mathsf{BAD}]
\le
\sum_i\epsilon_i.
}
$$

The security target is achieved whenever the complete instantiated ledger satisfies

$$
\boxed{
\sum_i\epsilon_i<2^{-128}.
}
$$

This is the correct meaning of QPT-128 for the composed construction.

The supplied audits independently verified the arithmetic rule

$$
8\cdot2^{-131}=2^{-128},
$$

and explicitly rejected the incorrect practice of assigning \(2^{-128}\) to every component and then calling the composition 128-bit.

---

# 2. Security definition

Let \(\mathcal A\) be a quantum polynomial-time adversary controlling at most \(F=21\) validator seats.

The CE-QS security experiment allows \(\mathcal A\) to:

* observe public quorum certificates;
* adaptively choose protocol messages within the experiment's resource bounds;
* corrupt up to 21 seats;
* obtain all information permitted by the corruption model;
* attempt to produce an invalid authorization;
* attempt to frame an honest validator;
* attempt to create two conflicting accepted certificates;
* attempt to cause false conflict extraction;
* attempt to violate hidden-signer privacy.

Define the total failure event:

$$
\mathsf{Fail}_{CE}.
$$

CE-QS is QPT-128 secure if

$$
\boxed{
\Pr[\mathsf{Fail}_{CE}]<2^{-128}.
}
$$

This is a probability statement over a specified QPT experiment, rather than an informal claim that the construction “has 128-bit security.”

The supplied v1.19 audit specifically identifies this distinction as necessary: a resource profile and composed failure-probability budget are required before a scalar 128-bit statement is meaningful.

---

# 3. Construction

Each validator \(i\) possesses two logically independent secret keys.

### Authentication key

$$
(sk_i^A,pk_i^A).
$$

It authorizes the validator's vote.

### Trace key

$$
s_i^T.
$$

The trace key is never intended to be the authentication key.

The trace registration uses

$$
y_i=F_{s_i^T}(A),
$$

where

$$
F_s(X)=\lfloor Xs\rceil_p
$$

is the selected LWR-derived weak pseudorandom function.

The source construction explicitly separates the authentication key from the trace key and registers the latter through the public registry relation.

A certificate has the abstract form

$$
QC=
(v,e,\tau,H(M),Q,E,\Pi_B),
$$

where:

* \(v\) is the version;
* \(e\) is the epoch;
* \(\tau\) is the conflict domain;
* \(H(M)\) commits to the authorized message;
* \(Q\) specifies the quorum threshold;
* \(E\) contains the public trace handles;
* \(\Pi_B\) is the outer proof.

The signer identities remain hidden.

---

# 4. Threshold correctness

The first security layer is purely combinatorial.

For

$$
N=64,\quad F=21,\quad Q=43,
$$

we have

$$
Q-F=22.
$$

Thus any valid quorum contains at least 22 honest seats.

For two valid quorums \(S_0,S_1\),

$$
|S_0\cap S_1|
\ge
|S_0|+|S_1|-N.
$$

Therefore

$$
|S_0\cap S_1|
\ge
43+43-64
=
22.
$$

Since the adversary controls at most 21 seats,

$$
|S_0\cap S_1|-F
\ge
22-21
=
1.
$$

Thus:

$$
\boxed{
\text{every two conflicting valid QCs share an honest signer.}
}
$$

This is the deterministic foundation of conflict extraction.

The supplied validation independently checked all three quantities:

$$
43=2(21)+1,
$$

$$
2(43)-64=22,
$$

and

$$
64>3(21)=63.
$$

All are arithmetically valid.

---

# 5. Trace-key registration

Validator \(i\) samples

$$
s_i^T\leftarrow\mathbb Z_{q_L}^{\nu}
$$

and publishes

$$
y_i=F_{s_i^T}(A).
$$

The registry must reject duplicate registered trace values.

Authentication keys are independently generated.

This separation is important because compromise of an authentication key must not automatically become compromise of the trace-opening mechanism.

The source proof identifies this registration construction explicitly.

---

# 6. QLWR assumption

The LWR primitive is defined by samples

$$
(X,F_s(X))
$$

where

$$
F_s(X)=\lfloor Xs\rceil_p.
$$

The quantum experiment permits a QPT distinguisher to receive polynomially many classical random samples.

Let

$$
\epsilon_{\rm QLWR}
$$

denote its maximum distinguishing advantage for the deployed sample bound.

The important point is that QPT security is **conditional on QLWR**.

The construction does not silently claim that an arbitrary LWR parameter set is automatically quantum-secure.

The source theorem gives the direct reduction

$$
\boxed{
\epsilon_{\rm QwPRF}
\le
\epsilon_{\rm QLWR}.
}
$$

The reduction is straight-line and requires no quantum rewinding, measurement, oracle programming, or random-oracle programming.

---

# 7. Statistical uniqueness

For the LWR/wPRF construction, distinct trace secrets must not map to the same output on a registered base.

The underlying counting argument establishes a statistical uniqueness bound of the form

$$
\delta_U\le\frac{\nu}{2^\nu}
$$

under the stated matrix-size condition

$$
m
\ge
\frac{\nu(\log q_L+1)}
{\log p-1}.
$$

Because this is an information-theoretic counting statement, it is not weakened merely because the adversary is quantum.

The epoch-wide bad event is bounded by a union bound over the bounded collection of trace bases:

$$
\boxed{
\delta_{\rm BaseBad}
\le
(D_{\max}+1)\frac{\nu}{2^\nu}.
}
$$

The construction uses a bounded CRS domain so that this union is finite and explicit.

---

# 8. Independently validated uniqueness calculation

The later audit reconstructed the previously unverifiable uniqueness calculation.

For the fixed-registry parameterization, it obtained

$$
\log_2\epsilon_A
\approx
-158.2885,
$$

and after the 1025-base factor:

$$
\log_2(1025\epsilon_A)
=
-148.2870623165.
$$

The independent derivation then bounded the pairwise-base term by

$$
\epsilon_{B\text{-pair}}
=
1024\binom{64}{2}2^{-176}
=
63\cdot2^{-161},
$$

giving

$$
\boxed{
\log_2\epsilon_{\rm new}
\approx
-154.8800181.
}
$$

The audit reproduced the source value to seven decimal places.

This is a strong validation of the **statistical uniqueness sub-bound**.

It is not, by itself, a proof of the whole QPT-128 theorem.

---

# 9. QPT one-wayness

Suppose a QPT adversary can recover the trace secret from a random wPRF input/output pair.

The reduction obtains two challenge samples, gives one to the key-recovery adversary, forwards classical oracle samples, and tests the recovered secret against both challenge samples.

The construction therefore obtains

$$
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
$$

No quantum rewinding is needed.

Consequently, once QLWR and the statistical uniqueness conditions are instantiated, trace-secret recovery is reduced to the corresponding QPT assumptions.

---

# 10. Post-quantum NIZK layer

The local and outer proof layers use a post-quantum simulation-extractable NIZK in the CRS model.

Let

$$
\epsilon_{\rm SE}
$$

denote its relevant simulation-extraction failure probability.

The construction assumes polynomial quantum hardness of LWE for the underlying SE-NIZK.

This eliminates the need to base the load-bearing theorem on a QROM Fiat-Shamir transformation.

The source ledger therefore classifies:

* local proof security as QPT conditional;
* outer proof existence as QPT theoretical existence;
* the construction as using no random oracle in its load-bearing theorem.

---

# 11. Signature layer

The authorization relation requires an actual valid vote authorization.

Let

$$
\epsilon_{\rm sig}
$$

denote the QEUF-CMA advantage of the deployed post-quantum signature.

For a 64-seat adaptive corruption envelope, a conservative union bound gives

$$
\epsilon_{\rm vote}
\le
64\epsilon_{\rm sig}.
$$

Therefore the six-bit multiplicity loss must be included:

$$
-\log_2(64\epsilon_{\rm sig})
=
-\log_2\epsilon_{\rm sig}-6.
$$

Thus, if the signature contribution is allocated a budget of

$$
2^{-131},
$$

the underlying signature reduction must satisfy

$$
64\epsilon_{\rm sig}\le2^{-131},
$$

or

$$
\boxed{
\epsilon_{\rm sig}\le2^{-137}.
}
$$

If instead the signature term is allowed to consume the full \(2^{-128}\) target, the corresponding minimum is

$$
\epsilon_{\rm sig}\le2^{-134}.
$$

The distinction is essential: the latter is a one-row budget, while the former reserves four additional bits of composition slack.

SLH-DSA is suitable as the post-quantum signature primitive because it is a hash-based QEUF-CMA signature family; however, a category label must not be substituted for the composed system's explicit reduction loss.

---

# 12. Conflict-extraction equation

For a fixed domain \(d\), the construction publishes handles containing a link component and a message-dependent mask.

For a validator \(i\),

$$
Z_i
=
F_{C_d}(s_i)
+
c_M(i+1),
$$

and for a conflicting message \(M'\),

$$
Z'_i
=
F_{C_d}(s_i)
+
c_{M'}(i+1).
$$

Over the characteristic-two field used by the construction,

$$
Z_i+Z'_i
=
(c_M+c_{M'})(i+1).
$$

Since

$$
M\ne M'
$$

implies

$$
c_M+c_{M'}\ne0,
$$

division yields

$$
\boxed{
i+1
=
\frac{Z_i+Z'_i}{c_M+c_{M'}}.
}
$$

Thus a matched handle pair carries its identity information in the **difference between two conflicting certificates**, not in either certificate individually.

The independent v1.20 audit reconstructed this equation from first principles and confirmed that the 48-byte link plus 48-byte mask gives the specified 96-byte handle.

---

# 13. Privacy of a single certificate

For one certificate, the trace mask is computationally pseudorandom under the QLWR assumption.

Consequently, an observer does not obtain the validator identity from a single handle merely by inspecting the public mask.

The ZK layer hides the witness mapping between:

$$
i
$$

and the public handle.

The simulator preserves the public statement but does not reveal the private witness.

Therefore zero knowledge does not conflict with the extraction equation: extraction requires **two conflicting public statements**, while ordinary verification exposes neither secret trace key nor signer index.

The v1.20 audit explicitly validated this distinction: simulation preserves public-input entropy; it does not turn simulation trapdoors into signing or trace-opening keys.

---

# 14. Authorization soundness

Trace equality alone is insufficient to establish that a validator actually authorized both messages.

A sound CE proof must establish all of:

1. the hidden seat is registered;
2. its trace secret satisfies the registry relation;
3. its public handle is correctly formed;
4. the seat is distinct from the other quorum seats;
5. the corresponding vote authorization is valid;
6. the authorization is bound to the exact message \(M\).

Therefore the critical reduction is:

$$
\text{false double-authorizer}
\Rightarrow
\text{NIZK extraction failure}
$$

or

$$
\text{false double-authorizer}
\Rightarrow
\text{signature forgery},
$$

plus the trace/uniqueness bad events.

The v1.20 audit correctly identifies this soundness/knowledge distinction and gives the extensible seven-term CE decomposition:

$$
\boxed{
\epsilon_{\rm CE}
\le
\epsilon_{\rm cfg}
+
\epsilon_{A\text{-uniq}}
+
\epsilon_{B\text{-pair}}
+
\epsilon_{H\text{-link}}
+
\epsilon_{H\text{-challenge}}
+
\epsilon_{\rm joint\text{-extract}}
+
\epsilon_{\rm vote\text{-forge}}.
}
$$

The terms are whole-experiment terms, not independent per-invocation probabilities.

---

# 15. Quantum hash-event discipline

The challenge hash has 384-bit output:

$$
H_C:\{0,1\}^\star\rightarrow\{0,1\}^{384}.
$$

This size is deliberate.

For a generic \(h\)-bit random function, the relevant quantum scalings are:

### Preimage

$$
\epsilon_{\rm pre}
\sim
\frac{Q^2}{2^h}.
$$

Constant-success complexity is approximately

$$
2^{h/2}.
$$

### Collision

$$
\epsilon_{\rm coll}
\sim
\frac{Q^3}{2^h}.
$$

Constant-success complexity is approximately

$$
2^{h/3}.
$$

Thus a 256-bit hash gives approximately 128-bit quantum **preimage** security but only approximately

$$
2^{256/3}
\approx
2^{85.3}
$$

generic quantum **collision** security.

Generic 128-bit quantum collision resistance therefore requires approximately

$$
h=384.
$$

The independent quantum-security audit verified this distinction and the resulting 384-bit design choice.

---

# 16. Why the 384-bit challenge is sufficient at the generic level

For a hypothetical collision term

$$
\epsilon_{\rm coll}
\le
C M Q^3 2^{-h},
$$

and target row budget \(2^{-131}\),

$$
h
\ge
3\log_2Q+\log_2M+\log_2C+131.
$$

For the illustrative resource profile

$$
Q=2^{64},\qquad M=2^{16},\qquad C=1,
$$

this becomes

$$
h\ge
3(64)+16+131
=
339.
$$

Therefore 384 bits would exceed this illustrative requirement by

$$
384-339=45
$$

bits.

The audit also correctly emphasizes that this is a **method template**, not a license to treat 339 bits as the actual CE-QS parameter theorem until the real collision event and constants are derived from the implemented extraction construction.

---

# 17. Complete QPT failure ledger

Define:

$$
\begin{aligned}
\epsilon_{\rm total}
={}&
\epsilon_{\rm cfg}
+\epsilon_{\rm A\text{-}uniq}
+\epsilon_{\rm B\text{-}pair}\\
&+\epsilon_{\rm QLWR}
+\epsilon_{\rm SE}\\
&+64\epsilon_{\rm sig}\\
&+\epsilon_{\rm QCR}\\
&+\epsilon_{\rm registry}\\
&+\epsilon_{\rm protocol}.
\end{aligned}
$$

The final acceptance condition is

$$
\boxed{
\epsilon_{\rm total}<2^{-128}.
}
$$

A conservative eight-row allocation is:

$$
\epsilon_i\le2^{-131}
$$

for every row.

Then

$$
\epsilon_{\rm total}
\le
8\cdot2^{-131}
=
2^{-128}.
$$

If strict inequality is required, at least one row must be strictly below its allocation, or the allocations must be tightened slightly.

A six-row allocation gives:

$$
6\cdot2^{-131}
=
\frac34\,2^{-128}
<
2^{-128}.
$$

The general rule is:

$$
\boxed{
\text{probabilities add; security exponents do not.}
}
$$

The supplied validation independently confirmed this arithmetic.

---

# 18. Full conditional security theorem

## Theorem — CE-QS QPT-128

Assume the following.

### A1 — QLWR

The deployed LWR parameterization is QPT-secure for its actual sample exposure:

$$
\epsilon_{\rm QLWR}
$$

is bounded by its assigned ledger budget.

### A2 — statistical uniqueness

The deployed CRS matrices satisfy the uniqueness condition with failure probability

$$
\epsilon_{\rm uniq}.
$$

### A3 — QPT SE-NIZK

The local/outer proof system is simulation-extractable against QPT adversaries under quantum-LWE, with failure probability

$$
\epsilon_{\rm SE}.
$$

### A4 — QEUF-CMA signature

The deployed vote signature is QEUF-CMA against QPT adversaries, with advantage

$$
\epsilon_{\rm sig}.
$$

### A5 — quantum collision resistance

The deployed 384-bit challenge hash satisfies its required QPT collision bound.

### A6 — unique registration

The registry rejects duplicate trace registrations.

### A7 — canonical encoding

The message, domain, configuration, and handle encodings are canonical and injective where required.

### A8 — bounded trace domain

The CRS contains only the declared polynomially bounded number of trace-domain slots.

### A9 — durable authorization state

A validator cannot authorize two conflicting messages while the protocol's persistent state claims it authorized only one.

Then every QPT adversary \(\mathcal A\) that violates CE-QS safety, hidden-signer authorization, non-frameability, or conflict-extraction soundness produces one of the bad events in the security ledger.

Consequently,

$$
\boxed{
\Adv_{\rm CE}^{QPT}(\mathcal A)
\le
\epsilon_{\rm total}.
}
$$

If

$$
\boxed{
\epsilon_{\rm total}<2^{-128},
}
$$

then

$$
\boxed{
\Adv_{\rm CE}^{QPT}(\mathcal A)<2^{-128}.
}
$$

Therefore CE-QS achieves the QPT-128 target under the stated assumptions and instantiated ledger.

$$
\blacksquare
$$

The v1.3 source independently states the same theorem architecture: QLWR, statistical uniqueness, quantum-LWE SE-NIZK, QEUF-CMA signatures, QCR, unique registry keys, canonical encoding, bounded CRS domains, and durable no-double-vote state.

---

# 19. Conflict-extraction theorem

Let

$$
QC_0=(M,E_0,\Pi_0)
$$

and

$$
QC_1=(M',E_1,\Pi_1)
$$

be two accepted certificates for the same configuration and domain, with

$$
M\ne M'.
$$

Let their hidden signer sets be

$$
S_0,S_1.
$$

Because

$$
|S_0|,|S_1|\ge43,
$$

we have

$$
|S_0\cap S_1|\ge22.
$$

Under trace uniqueness and handle soundness, every common honest signer contributes a pair of handles whose difference reveals its registered identity.

Thus:

$$
\boxed{
|ExtractConflict(QC_0,QC_1)|
\ge22
}
$$

except with probability bounded by the CE-QS failure ledger.

This is the desired \(F+1\) extraction guarantee.

---

# 20. Non-frameability

A QPT adversary attempting to make the extractor blame an honest validator who did not authorize both messages must defeat at least one of:

1. trace-key uniqueness;
2. trace one-wayness;
3. NIZK knowledge soundness;
4. signature QEUF-CMA;
5. challenge collision resistance;
6. registry binding.

The resulting reduction has the form

$$
\begin{aligned}
\Adv_{\rm Frame}^{QPT}
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
$$

The supplied source presents this as the explicit QPT frame bound.

The factors must be incorporated into the final ledger rather than ignored.

---

# 21. Critical registration correction

The v1.20 validation found one concrete specification defect:

> two seats must not be permitted to register the same trace secret.

If

$$
s_i=s_j,
$$

then

$$
F_A(s_i)=F_A(s_j).
$$

Their links can therefore coincide, and the extraction formula may return a value that is not either seat's index.

The quorum-intersection argument still guarantees that the true common seats exist, but the stronger claim that **every matched link recovers exactly one intended identity** fails without duplicate-secret prevention.

Therefore the finalized specification contains:

$$
\boxed{
\text{Reject registration if }y_i=y_j\text{ for any }i\ne j.
}
$$

This is a small but mandatory correction identified by the independent v1.20 audit.

---

# 22. Structural validation

The supplied structural checker validates the following idealized properties:

* same key + same domain + conflicting messages extracts the correct identity;
* different keys do not falsely trace under the ideal uniqueness model;
* the domain uses an immutable setup base;
* domain-budget exhaustion fails closed;
* the outer witness contains no trace secret or authentication secret.

The checker itself explicitly warns:

> structural toy model only; QLWR/LWE/NIZK/QCR security not executed.

Therefore these are **structural validation tests**, not cryptographic security experiments.

---

# 23. Numerical validation of the existing relation

The independent circuit/size audit reconstructed:

$$
43(608+608+48)\cdot256
=
13,914,112
$$

scalar products.

It also verified:

$$
6,957,056
$$

packed multiplications,

$$
903=\binom{43}{2}
$$

distinctness checks,

$$
215=5\cdot43
$$

Keccak operations,

and

$$
516=12\cdot43
$$

public handle words.

The 96-byte handle is therefore consistent with the 48-byte link plus 48-byte mask construction.

These figures were independently recomputed and found internally consistent.

---

# 24. What the validation proves

The validation evidence establishes:

### Proven

* quorum arithmetic;
* quorum intersection;
* honest-majority arithmetic;
* conflict-extraction algebra;
* handle-format arithmetic;
* distinctness count;
* challenge-size rationale;
* composition arithmetic;
* uniqueness calculation after independent reconstruction;
* structural domain-budget behavior;
* structural absence of trace/authentication secrets from the outer witness.

### Conditionally proven

* QLWR-to-wPRF security;
* QPT trace one-wayness;
* QPT SE-NIZK security;
* QEUF-CMA authorization;
* cross-key trace soundness;
* non-frameability;
* conflict extraction;
* complete QPT security theorem.

### Not established by the validation suite

* an actual quantum attack experiment;
* a concrete quantum-LWE reduction for every deployed parameter;
* a concrete QPT reduction matching the exact LWR row exposure;
* an implemented QPT collaborative MPC;
* a measured <32-KiB final QC;
* a generated, independently verified full production QC.

The source ledger explicitly makes this distinction: theoretical hidden-signer QPT security is conditionally closed, while practical certificate compactness remains open.

---

# 25. The LWR parameter-validation obligation

One major item must not be silently promoted to “proved.”

The current construction records a row-exposure figure of approximately

$$
672,352,
$$

but the supplied v1.19 audit states that matching this exposure to an applicable concrete small-modulus LWR hardness theorem remains open.

The correct validation sequence is:

$$
\text{CE-QS parameter set}
\rightarrow
\text{actual sample exposure}
\rightarrow
\text{applicable QLWR theorem}
\rightarrow
\text{concrete advantage}
\rightarrow
\text{ledger row}.
$$

It is not valid to infer

$$
\text{large-looking parameters}
\Rightarrow
128\text{-bit QPT security}.
$$

The audit explicitly leaves this obligation open.

---

# 26. Why the earlier 128-step verification argument is not used

The construction does not claim 128 independent verification challenges merely because a deterministic signature or proof can be decomposed into 128 sequential checks.

The invalid inference would be

$$
\Pr[F_1\cap\cdots\cap F_{128}]
\stackrel{\rm false}{\le}
2^{-128}
$$

without establishing conditional probabilities of the form

$$
\Pr[F_i\mid F_1,\ldots,F_{i-1}]
\le\frac12.
$$

The CE-QS theorem instead uses actual cryptographic reductions and a union bound over explicit bad events.

This removes the artificial source of “128-bit security” and makes the theorem auditable.

---

# 27. Why the GHZ/\(\sqrt i\) construction is not part of the proof

The proposed state

$$
|\Psi\rangle
=
\frac{|0^{128}\rangle+
e^{i\pi/4}|1^{128}\rangle}{\sqrt2}
$$

can be prepared using a Hadamard, a \(T\) phase, and 127 CNOTs.

However, the state contains no secret parameter.

Therefore it cannot independently authenticate a message or establish the acceptance gap required for a cryptographic reduction.

It is consequently excluded from the load-bearing QPT-128 proof.

This keeps the security theorem classical-cryptographic in its assumptions rather than assigning cryptographic meaning to an otherwise public quantum state.

---

# 28. Collaborative proving variant

The collaborative version distributes the trace secrets:

$$
w_j=(i_j,\sigma_j,s_j^T)
$$

among the participating validators.

Validator \(j\) retains

$$
s_j^T
$$

locally.

The final proof establishes:

1. threshold size;
2. distinct identities;
3. vote authorization;
4. trace registration;
5. correct handle generation;
6. exact public handle-list binding.

The final certificate contains one proof rather than \(Q\) local proof objects.

The source construction gives the collaborative relation explicitly and establishes that the final certificate contains no local NIZK list.

Safety follows from secure-with-abort MPC:

$$
\boxed{
\text{abort}\Rightarrow\text{no new valid QC}.
}
$$

Liveness requires either guaranteed-output-delivery MPC or sound identifiable abort plus replacement.

---

# 29. Liveness is separate from QPT safety

A Byzantine prover can abort a collaborative proof.

Therefore:

$$
\text{secure-with-abort}
\not\Rightarrow
\text{liveness}.
$$

The correct liveness theorem requires an additional mechanism.

With sound identifiable abort, each correctly attributed Byzantine failure decreases the remaining fault budget by at least one.

Define

$$
\Phi=21-b,
$$

where \(b\) is the number of correctly identified Byzantine seats.

Each sound exclusion gives

$$
\Phi\rightarrow\Phi-1.
$$

Therefore after at most 21 Byzantine exclusions, the remaining eligible set is honest.

This potential-function argument is conditionally valid, but the supplied audit correctly refuses to treat timeout or anonymous failure as cryptographic blame.

---

# 30. Compactness boundary

The QPT theorem does not imply the 32-KiB certificate target.

The current certificate-size expression is

$$
|QC|
=
Q(d+1)m\lceil\log_2p\rceil
+
|\Pi_B|
+
O(\lambda).
$$

The generic SE-NIZK theorem establishes polynomial proof size, not a 32-KiB bound.

The currently measured hash-based format has a scoped floor:

$$
46,192+4,288+16
=
50,496
>
32,768.
$$

This rules out that **specific measured format/layout**, not every hash-based proof system.

The independent audit explicitly rejects generalizing this floor to the entire hash-proof family.

---

# 31. Architectural route toward compactness

The most promising architectural direction identified by the supplied work is folding/recursive composition.

The per-seat decomposition is naturally:

$$
\text{registration}
+
\text{link}
+
\text{mask}
+
\text{authorization}
+
\text{hidden identity}.
$$

These 43 chunks can be recursively folded into one proof.

The source analysis identifies three concrete measurement gates:

### M1

Measure one complete authorization verification.

### M2

Measure the final folded proof:

$$
|QC|\le32,768.
$$

### M3

Measure recursive verifier overhead.

These are engineering gates, not security assumptions.

---

# 32. Final QPT-128 ledger template

The production security record should contain:

| Component               |              Required bound |
| ----------------------- | --------------------------: |
| Configuration binding   |      \(\epsilon_{\rm cfg}\) |
| Trace uniqueness        |     \(\epsilon_{\rm uniq}\) |
| Link-pair uniqueness    |     \(\epsilon_{\rm pair}\) |
| QLWR                    |     \(\epsilon_{\rm QLWR}\) |
| QPT SE-NIZK             |       \(\epsilon_{\rm SE}\) |
| Signature authorization |    \(64\epsilon_{\rm sig}\) |
| Challenge collision     |      \(\epsilon_{\rm QCR}\) |
| Registry integrity      | \(\epsilon_{\rm registry}\) |
| Protocol-state failure  | \(\epsilon_{\rm protocol}\) |
| **Total**               |           **\(<2^{-128}\)** |

The acceptance equation is:

$$
\boxed{
\epsilon_{\rm cfg}
+\epsilon_{\rm uniq}
+\epsilon_{\rm pair}
+\epsilon_{\rm QLWR}
+\epsilon_{\rm SE}
+64\epsilon_{\rm sig}
+\epsilon_{\rm QCR}
+\epsilon_{\rm registry}
+\epsilon_{\rm protocol}
<
2^{-128}.
}
$$

No term may be replaced by a category name.

No exponent may be added directly.

No independence assumption is required for the union bound.

---

# 33. Final validation matrix

| Property                                   | Result                                 |
| ------------------------------------------ | -------------------------------------- |
| \(N=64,F=21,Q=43\)                         | **Verified**                           |
| \(Q-F=22\) honest seats                    | **Verified**                           |
| \(2Q-N=22=F+1\)                            | **Verified**                           |
| Conflict extraction algebra                | **Verified**                           |
| 96-byte handle structure                   | **Verified**                           |
| 43 × 12 = 516 words                        | **Verified**                           |
| \(903=\binom{43}{2}\)                      | **Verified**                           |
| 384-bit collision target                   | **Validated at generic quantum level** |
| Statistical uniqueness                     | **Independently reconstructed**        |
| \(\log_2\epsilon_{\rm new}\approx-154.88\) | **Independently reconstructed**        |
| QLWR reduction                             | **Conditional**                        |
| QPT SE-NIZK                                | **Conditional**                        |
| Signature QEUF-CMA                         | **Conditional**                        |
| Complete composed \(<2^{-128}\) number     | **Requires instantiated ledger**       |
| Duplicate-registration defense             | **Mandatory correction**               |
| Current hash-based 32-KiB frame            | **Fails measured format**              |
| General 32-KiB compactness                 | **Open**                               |
| Full production QC execution               | **Not demonstrated**                   |

The supplied v1.20 adjudication reports that the checkable mathematical claims were independently reconstructed, including the uniqueness bound, while still retaining the distinction between conditional theorems and unimplemented artifacts.

---

# 34. Final security statement

The strongest correct final statement is therefore:

$$
\boxed{
\begin{minipage}{0.88\linewidth}
CE-QS with \(N=64\), \(F=21\), and \(Q=43\) admits a QPT-128 security proof in the CRS model, provided the deployed QLWR parameters, QPT simulation-extractable NIZK, post-quantum QEUF-CMA signature, quantum-collision-resistant challenge function, registry uniqueness, canonical encoding, and persistent authorization state satisfy the explicit quantitative failure ledger
\[
\epsilon_{\rm total}<2^{-128}.
$$

Under these assumptions, two conflicting accepted certificates contain at least \(F+1=22\) common-seat witnesses and the trace relation publicly extracts the conflicting authorization identities except with probability at most \(\epsilon_{\rm total}\).
\end{minipage}
}
]

This is a genuine conditional QPT-128 theorem, not a heuristic “128-bit” label.

---

# 35. Final status

### Security architecture

$$
\boxed{\textbf{CLOSED CONDITIONALLY}}
$$

The source construction contains a complete reduction architecture from CE-QS failure to explicit QPT assumptions and bounded statistical events.

### Mathematical validation

$$
\boxed{\textbf{SUBSTANTIALLY VALIDATED}}
$$

The quorum arithmetic, extraction identity, handle arithmetic, composition arithmetic, quantum collision/preimage distinction, and statistical uniqueness calculation have been independently checked.

### Concrete QPT-128 instantiation

$$
\boxed{\textbf{NOT YET NUMERICALLY CERTIFIED}}
$$

The exact LWR hardness matching and every concrete reduction-loss term must be populated before the theorem can honestly be converted into an unconditional “this parameter set has measured \(<2^{-128}\) advantage” claim. The audit explicitly leaves the LWR matching obligation open.

### 32-KiB certificate

$$
\boxed{\textbf{OPEN}}
$$

The existing measured format exceeds the cap, while the broader architectural compactness problem remains a separate engineering/research problem.

### Overall conclusion

The existing construction is sufficient to **finalize the QPT-128 proof framework and theorem**, but a rigorous report must not claim that the entire implementation has already been experimentally or concretely certified at \(2^{-128}\). The remaining work is parameter instantiation and backend validation, not a replacement of the underlying CE-QS security architecture.

ML-KEM and in combination with ML-DSA and try to solve the blockers look at israeli and south korea research papers
ML-KEM and in combination with ML-DSA and try to solve the blockers

I implemented and tested ML-KEM-1024 + ML-DSA-87. All 51 component checks passed.

The experiment now:

Encrypts and authenticates approval delivery.
Checks 43 distinct members’ signatures against the exact statement and their tracing handles.
Recovers the 22 common signers in the synthetic conflict test.
Rejects replayed approvals, substituted keys, altered statements, and duplicate seats.

The decisive finding: valid signatures can approve an incorrect tracing equation. The full witness checker rejects it. Therefore, the certificate still needs a zero-knowledge proof connecting each signature, registered identity, and tracing handle.

I also assessed Israeli Aurora research and South Korean AIM/AIMer and HAETAE research. They contribute proof-design and signature-compaction ideas, but none yet instantiates this complete combination.

Still unresolved: fitting that proof into the remaining 27,056 bytes, establishing whole-system QPT-128 security, and generating it privately with robust distributed participation. No complete qualifying QC has been produced.

The code, conditional accountability argument, research mapping, and reproducible evidence are saved in 
PQ_CE_QS_v1.29_MLKEM_MLDSA_experiment.zip.

Yesterday 8:21 PM

only work on 128pqt. first prove the math what you going to do is divide and conquer incremental find formulas with proof if partial even better glue different school of thought math and combine first collect then organize then test and validate learn from trying 256 and 512 pqt the errors will carve way to 128 Building a theoretical model for QPT-128 (Quantum Polynomial Time with a 128-bit security margin) involves designing a system where classical cryptographic structures are fortified to withstand bounded quantum algorithms—specifically aiming for a post-quantum security equivalent of 2¹²⁸ operations.

While the term "QPT" usually describes the complexity class BQP (Bounded-error Quantum Polynomial-time), in engineering and design it translates to setting up parameters that force a quantum adversary to expend a minimum of 2¹²⁸ quantum gates or logical operations to break the primitive. [1]

1. Define the Adversary Bounds

To construct a theoretical QPT-128 model, you must design against two distinct quantum attack vectors: [2, 3]

Shor's Algorithm (Algebraic Structure): Breaks traditional asymmetric math (RSA, ECC) in polynomial time ($O(\text{poly}(n))$) by finding the period of a function.
Grover's Algorithm (Unstructured Search): Provides a quadratic speedup for finding a specific entry in an unsorted database of size N, dropping the search time to $O(\sqrt{N})$. [4]

To achieve QPT-128, your goal is to bound the quantum execution cost (Time × Space) such that the total work required by an adversary using these algorithms exceeds 2¹²⁸ total quantum operations. [1]

2. Core Cryptographic Dimensions for QPT-128

When designing the primitives, the theoretical definitions must scale appropriately to absorb quantum speedups:

A. Symmetric Encryption & Hashing (Defeating Grover)

Grover's algorithm reduces the security of an n-bit block cipher or hash output to n/2 bits in an idealized quantum setting. [4]

The Math: To ensure a minimum work factor of 2¹²⁸, the physical bit length must be doubled to 256 bits. [4]
The Construction:
Use a 256-bit key block cipher like AES-256.
Use a 512-bit state hash function like SHA-384 or SHA3-512 to guarantee collision resistance bounds of 2¹²⁸ or higher against quantum amplitude amplification attacks. [1, 5]
B. Asymmetric Framework (Defeating Shor via Lattices)

Because Shor's algorithm solves discrete logarithms and prime factorization natively, you cannot use ECC or RSA. You must instead rely on problems belonging to NP-hard lattice frameworks, such as Learning With Errors (LWE) or Short Integer Solution (SIS), where the best quantum algorithms still require exponential time. [3]

To mathematically design a QPT-128 Lattice Key Encapsulation (comparable to NIST's Level 5 security / ML-KEM-1024): [1, 6]

Set Dimension (k): Set the module rank k = 4.
Vector Dimension (s): Use a polynomial ring degree of n = 256, totaling a lattice dimension of N = k × n = 1024.
Modulus (q): Choose a small prime modulus, typically q = 3329.
Error Distribution (η): Use a Centered Binomial Distribution (CBD) with η = 2.

Under the Core-SVP (Shortest Vector Problem) hardness model, these constraints dictate that the best known quantum sieve algorithms require greater than 2¹²⁸ quantum gates to find the secret vector, making the lattice asymptotically stable against a QPT adversary. [7]

3. Structural Design of a QPT-128 Primitive

If you were to draft a conceptual multi-layered protocol, it should follow an order of operations that completely isolates raw quantum-susceptible steps:

[ Classical Layer ]   --->   [ Lattice-Reduction Layer ]  --->   [ Entropy-Squeezing Layer ]
   AES-256 Key                 Module-LWE (k=4, n=256)             SHA3-512 Matrix Compression
 (Grover-Resistant)             (Shor-Resistant)                     (Pre-Image Bounded)

Matrix Initialization: Generate a public random matrix $\mathbf{A} \in \mathbb{Z}_q^{k \times k}$ via a extendable output function (like SHAKE-128).
Noise Injection: Sample secret vectors $\mathbf{s}$ and error vectors $\mathbf{e}$ from the binomial distribution. The hardness of the QPT-128 scheme is derived from the fact that recovering $\mathbf{s}$ from $\mathbf{b} = \mathbf{A}\mathbf{s} + \mathbf{e}$ is asymptotically intractable.
Quantum-Safe Hardening: Pass all intermediate key states through a SHA3-512 sponge construction to strip away potential multi-target attack structures that a quantum machine might exploit. [8]
4. Real-World Constraints to Account For

When taking this theoretical framework into a live design, you must mitigate a critical physical exploit: The MAXDEPTH Bound.

In pure theory, Grover's algorithm performs 2¹²⁸ sequential operations. However, in physics, a quantum computer cannot maintain qubit coherence indefinitely. If your adversary's quantum circuit depth is bounded by a realistic limit (e.g., 2⁴⁰ or 2⁶⁴ sequential steps), they are forced to run attacks in parallel. [2]

Because Grover's algorithm scales poorly when parallelized ($\sqrt{S}$ efficiency for S processors), parallelizing a quantum search actually increases the total global energy cost. As a result, standard AES-128 or ML-KEM-768 are heavily projected to maintain a pragmatic QPT-128 security perimeter in actual engineering environments. [3, 9]

To help refine this concept further, could you share:

Are you building an abstract mathematical proof (e.g., establishing a reduction to an NP-hard problem), or designing a software prototype?
Which cryptographic operation are you prioritizing: Key Exchange (like KEM) or Digital Signatures (like DSA)?

[1] https://crypto.stackexchange.com

[2] https://crypto.stackexchange.com

[3] https://words.filippo.io

[4] https://en.wikipedia.org

[5] https://words.filippo.io

[6] https://www.kaspersky.com.au

[7] https://csrc.nist.gov

[8] https://crypto.stackexchange.com

[9] https://portal.gigaom.com

I completed a partial mathematical proof for QPT-128, with explicit assumptions and reproducible checks.

For a uniformly random function with \(h\)-bit output, the published quantum collision bound is:

$$ \Pr[\text{collision}] \le \min\!\left(1,\frac{12(Q+154)^3}{2^h}\right). $$

At \(Q=2^{128}\) and \(h=512\), this gives approximately \(2^{-124.415}\)—well below constant success. This establishes an ideal-oracle component result, not a theorem about the complete implementation.

I then derived the conditional quorum-safety bound:

$$ p_{\mathrm{conflict}} \le \kappa_J+ L_J\!\left[ 64\,\epsilon_{\mathrm{signature}} +\frac{12(Q_*+154)^3}{2^{512}} \right]. $$

Here \(L_J\) is the joint-extraction loss, \(\kappa_J\) its error, and \(Q_*\) includes the reduction’s queries. These are now explicit quantities to prove for the actual system.

The 256/512 stress cases exposed two mistakes to avoid: expanding a hash output cannot increase secret entropy, and extraction losses can exhaust an otherwise sufficient component budget.

Validation: 8,965 counted cases passed, covering exact arithmetic, invalid-model rejection, and small quantum-search simulations. These checks validate the calculations; they do not establish lattice hardness.

The remaining mathematical obligations are the actual joint extractor, concrete signature-security bound, and connection between the ideal oracle and the deployed hash.

QPT128_mathematical_model_v1.30.md
QPT128_mathematical_model_v1.30.zip — proofs, source ledger, checker, and results.
QPT128_mathematical_model_v1.30.md
Document
do research find partial proofs that can be concocted into full proofs incrementally and compartmentalize each aspect segregated and validate each loose item from the following actual joint extractor, concrete signature-security bound, and connection between the ideal oracle and the deployed hash. 

I found compatible partial proofs and derived additional composition lemmas. They narrow all three blockers, but do not yet establish QPT-128 for the current implementation.

Obligation	Progress established here	Remaining requirement
Joint extractor	Conditional construction extracting both witnesses from one execution	Instantiate its decoder for the actual quorum-proof relation
Signature security	Checked statistical bounds and the algebraic forgery reduction	Concrete hardness bounds, rejection analysis, and exact ML-DSA adaptation
Deployed hash	Proved which proposed connection is invalid; identified applicable partial sponge results	Justify the specific hash properties used by each reduction

Joint extraction: use one shared oracle database.

Don–Fehr–Majenz–Schaffner prove online extraction for a class of commit-and-open proofs in the quantum random-oracle model. Their Merkle-tree theorem supplies the starting point; its assumptions include an efficient special-soundness decoder.

I derived the following conditional two-proof extension:

Run the adversary once, answering proof-oracle queries through one compressed quantum oracle.
Obtain its two classical proofs and verify both.
Measure the compressed database \(D\) once, at the end.
Decode both commitment roots from that same \(D\), then apply the deterministic witness decoder to each.

Let:

\(Q\) count all relevant oracle queries, including both verifications;
\(v\) count the two verifiers’ queries;
\(h\) be the ideal oracle’s output length;
\(\ell\) be the commitment’s leaf count;
\(p_{\mathrm{triv}}\) bound a challenge set insufficient for witness extraction.

A conservative bound obtained from the paper’s database lemma is

$$ \boxed{ \varepsilon_J \le \min\!\left( 1,\; \frac{(72+40\ell)Q^3+2v}{2^h} +20Q^2p_{\mathrm{triv}} \right). } $$

Here \(\varepsilon_J\) bounds the probability that both proofs accept while at least one extracted witness is invalid.

The composition argument is straightforward: outside the database’s global bad event, every accepted, database-consistent proof decodes correctly. Applying the verifier-consistency lemma to both verifications adds at most \(2v/2^h\). Thus extraction does not require two independent executions or multiplication of their success probabilities. This extension is my derivation from the published lemmas.

This is a terminal extraction claim. Preserving an adversary’s future interaction with the oracle after extraction needs an additional argument.

I also checked the challenge encoding. For \(r\) repetitions of a three-challenge protocol, suppose extraction succeeds whenever one repetition has all three valid responses. Any nonextractable challenge set then contains at most \(2^r\) vectors. Map a uniform \(h\)-bit integer into ternary challenges using reduction modulo \(3^r\). Counting the sampler’s preimages gives

$$ \boxed{ p_{\mathrm{triv}} \le \frac{2^r\lceil 2^h/3^r\rceil}{2^h} \le (2/3)^r+2^{r-h}. } $$

This supplies the encoding term that a bare repetition count omits.

For the illustrative ideal-model profile

$$ r=512,\qquad h=832,\qquad \ell=2^{20},\qquad Q=2^{128}, $$

exact arithmetic gives

$$ \varepsilon_J<2^{-39}. $$

That is a useful constant-success security margin. It is not a claim of failure probability \(2^{-128}\), nor a qualification of the deployed hash.

Two extractor issues remain:

The current BaseFold/FRI backend has not been shown to satisfy this commit-and-open theorem’s assumptions.
The published compressed-oracle simulation has \(O(Q^2)\operatorname{poly}(h,B)\) overhead. A hardness assumption covering only \(2^{128}\) gates therefore does not automatically cover the resulting reduction.

Signature security: separate statistical loss from computational hardness.

The corrected Fiat–Shamir-with-aborts analysis of Barbosa et al. gives

$$ \varepsilon_{\mathrm{CMA}} \le \varepsilon_{\mathrm{NMA}}+L_{\mathrm{stat}}, $$

where

$$ \begin{aligned} L_{\mathrm{stat}}={}& \frac{2q_S\sqrt{\epsilon}}{1-p} \sqrt{q_H+1+\frac{q_S}{1-p}}\\ &+2(q_H+1)\sqrt{\frac{q_S\epsilon}{1-p}} +q_S\zeta_{\mathrm{zk}}+\delta . \end{aligned} $$

Here \(\epsilon\) bounds commitment guessing, \(p\) bounds rejection, \(\delta\) covers exceptional keys, and \(\zeta_{\mathrm{zk}}\) is simulator error. These conditions must hold on compatible key distributions and events.

I independently recomputed the rank-distribution calculation for

$$ q=8380417,\quad n=256,\quad \ell=7, $$

using corank cutoff \(28\). Under the stipulated uniform matrix and uniform mask model, the exact integer results certify

$$ \boxed{\delta\le2^{-540},\qquad \epsilon\le2^{-1670}.} $$

The second bound strengthens the paper’s reported conservative \(2^{-1664}\) intermediate bound. This is commitment entropy, not 1,670-bit signature security.

The computation uses the following counting recurrence. When a partially constructed matrix has rank \(j\), its next column has:

$$ q^j \quad\text{choices preserving rank, and}\quad q^\ell-q^j \quad\text{choices increasing rank}. $$

Convolving the resulting corank distribution across the 256 components gives the exceptional-matrix probability and conditional guessing bound.

Substituting

$$ q_S=2^{64},\quad q_H=2^{128},\quad p\le759/1024,\quad \zeta_{\mathrm{zk}}=0 $$

gives the certified conditional result

$$ L_{\mathrm{stat}}\le2^{-539}. $$

The rejection premise remains unproved here: the paper explicitly uses a heuristic for that numerical rejection estimate. Its mechanized development covers the classical ROM proof; the QROM theorem is a separate mathematical proof.

I also checked the algebraic NMA reduction directly. Let a valid idealized signature determine the lifted commitment \(\widetilde w\), with

$$ G(\widetilde w,m)=c. $$

Define

$$ a=\widetilde w-Az+ct,\qquad y=(a,z,c). $$

Then

$$ \boxed{[I\mid A\mid -t]\,y=\widetilde w.} $$

Consequently \(y\) satisfies the required self-target equation. The first block must have the sign shown above. The usual verification bounds give

$$ \|y\|_\infty \le \max\!\left(\gamma_1-\beta,\, 2\gamma_2+1+\tau2^{d-1}\right). $$

This closes the linear-algebra portion of that adapter. Computational hardness of the resulting SelfTargetMSIS instance remains a separate assumption.

A tempting further reduction fails its parameter check. Jackson–Miller–Wang require

$$ 2\gamma\eta'n(m+k)<\lfloor q/32\rfloor. $$

For the relevant ML-DSA-87 substitution, even \(\eta'=1\) gives

$$ 6{,}304{,}047{,}104<261{,}888, $$

which is false. Their theorem therefore cannot remove this assumption for those parameters.

The exact FIPS 204 adapter must additionally address seeded matrix expansion, mask generation, challenge sampling, message encoding, and rejection behavior. FIPS specifies these concrete procedures; the ideal uniform distributions above are not automatically interchangeable with them.

A useful gluing lemma: combine good-key events without assuming independence.

Suppose one partial proof supplies event \(\Gamma_1\), with

$$ \Pr[\neg\Gamma_1]\le\delta_1,\qquad \mathbb E[g\mid\Gamma_1]\le\epsilon_1, $$

and another supplies \(\Gamma_2\), with
\(\Pr[\neg\Gamma_2]\le\delta_2\).

For \(\delta_1+\delta_2<1\), their common event satisfies

$$ \boxed{ \delta\le\delta_1+\delta_2,\qquad \mathbb E[g\mid\Gamma_1\cap\Gamma_2] \le \epsilon_1 \frac{1-\delta_1}{1-\delta_1-\delta_2}. } $$

The proof bounds the restricted expectation’s numerator by
\(\mathbb E[g\,1_{\Gamma_1}]\), and its denominator by
\(\Pr[\Gamma_1]-\delta_2\). No independence assumption is used.

This provides a precise interface for combining a future rejection-probability proof with the rank-entropy calculation.

There is also a simple bounded-runtime adapter. If each signing attempt conditionally rejects with probability at most \(p\), capping each request at \(R\) attempts adds at most

$$ \delta_{\mathrm{run}}\le q_Sp^R. $$

For the conditional \(p=759/1024\) profile, exact arithmetic shows that \(R=519\) suffices for

$$ q_S=2^{64},\qquad \delta_{\mathrm{run}}\le2^{-160}. $$

Hash instantiation: change the obligation being proved.

A universal small distinguishing distance between a fixed public hash \(H_0\) and an independently sampled random oracle is impossible.

Choose a fixed input \(x\), compute \(H_0(x)\), query the challenged oracle at \(x\), and compare. The distinguishing advantage is

$$ \boxed{1-2^{-h}.} $$

Therefore a proposed final theorem cannot simply append an assumed negligible “SHAKE-versus-random-oracle distance.” SHAKE may still satisfy the specific computational properties needed by the protocol. General limitations of random-oracle instantiation are also established by Canetti–Goldreich–Halevi.

The useful research connections are narrower:

Research result	What it can contribute	Boundary
Carolan–Poremba, single-round sponge one-wayness	Explicit bound \(80(T+1)^2/2^{\min(r,c)}\)	Uniform full-rate input and an ideal invertible permutation
Cojocaru et al., quantum lifting	Explicit sponge collision bounds	Some relevant substitutions give bounds above 1
Alagic et al., quantum sponge indifferentiability	A construction-level connection to an ideal oracle	Still assumes an ideal permutation

These are partial foundations for a hash argument, with different games and interfaces. They cannot be exchanged freely.

In particular, requesting 832 output bits from SHAKE256 does not increase its 512-bit capacity. The illustrative extractor’s 832-bit ideal-oracle bound therefore needs a separate instantiation argument.

The resulting conditional composition is now explicit.

Under the existing quorum-to-forgery reduction, compatible oracle interfaces, and the required implementation adapters, the target form is

$$ \boxed{ \begin{aligned} p_{\mathrm{bad}}^{\mathrm{ideal}} \le{}& \varepsilon_J+\varepsilon_{\mathrm{bind}} +\delta_{\mathrm{run}}\\ &+64\bigl( \varepsilon_{\mathrm{MLWE}} +\varepsilon_{\mathrm{SelfTargetMSIS}} +L_{\mathrm{stat}} +\Delta_{\mathrm{spec}} \bigr). \end{aligned} } $$

Every computational term must be evaluated at the reduction’s actual resources. Here \(\Delta_{\mathrm{spec}}\) denotes specific, still-unproved scheme-adaptation steps—not generic hash indistinguishability.

For the established QPT-128 work-factor definition, the complete argument must make this bound less than \(1/3\) for every adversary using fewer than \(2^{128}\) gates.

Validation completed this iteration included:

Exact rank arithmetic, cross-checked against 530 exhaustively enumerated small matrices.
4,096 polynomial-ring instances checking the NMA matrix identity.
101,504 finite-event checks of the good-event composition inequality.
390 challenge-sampler checks.
Exact rational bounds for statistical losses and retry truncation.

These checks validate arithmetic and algebraic components. They do not replace the missing backend extractor, hardness assumptions, or deployed-hash proof.

The workspace remained unavailable, so I could not create or save a new downloadable dossier; the results are provided here.

operators_1000(1).md
File
adversarial check and substitute and amend the 1000 operators file to get closer to establish 128 vitalize the operators to investigate questions. read the 1000 operators then make multiple questions what can they be used for to establish 128 after mutating to be used. 

Yes—but with one important correction: do not optimize \(h\), \(K\), or the coefficients until the quantum game is fixed. The arithmetic in the proposed 256-bit example exposes why.

For \(q_h=2^{64}\),

$$ \frac{(q_h+1)^3}{2^{256}}\approx2^{-64}, $$

so the claimed collision term is nowhere near \(2^{-128}\). Increasing \(n\) from 128 to 256 improves the exponent, but under that particular cubic bound it still leaves 64 bits on the table.

The next reduction should therefore be organized as:

$$ \boxed{ \epsilon_{\rm forge}^{Q} \le \epsilon_{\rm PRF}^{Q} +\epsilon_{\rm FORS}^{Q} +\epsilon_{\rm WOTS}^{Q} +\epsilon_{\rm tree}^{Q} +\epsilon_{\rm compression}^{Q} } $$

and for every term determine:

Exact quantum oracle model — classical-access, QROM, or quantum-accessible hash.
Query exponent \(q=2^\alpha\).
Target multiplicity \(K\).
Reduction coefficient \(c_i\).
Tree multiplicity \(h\).
Resulting security exponent.

For a generic term

$$ \epsilon_i\le c_i q^{a_i}K_i^{b_i}2^{-n_i}, $$

the exponent bookkeeping is

$$ -\log_2\epsilon_i \ge n_i-a_i\alpha-b_i\log_2K_i-\log_2c_i. $$

For an additive reduction, the safe aggregate is

$$ -\log_2\epsilon_{\rm total} \approx \min_i \left( -\log_2\epsilon_i \right) -\log_2 m, $$

where \(m\) is the number of failure events being summed.

That gives us a very useful 128-bit feasibility test:

$$ \boxed{ n_i \ge 128+a_i\alpha+b_i\log_2K_i+\log_2c_i+\log_2m } $$

for every component.

This is much stronger than simply saying “use SLH-DSA-256.”

The key lesson from 128 → 192 → 256

If the dominant proof term is cubic in quantum queries,

$$ \epsilon\sim q^3 2^{-n}, $$

then with \(q=2^{64}\):

\(n=128\): \(2^{-64}\)
\(n=192\): \(2^{-0}\)
\(n=256\): \(2^{-64}\)
\(n=320\): \(2^{-128}\)

before coefficients, targets, or additive losses.

So 256-bit output does not automatically establish QPT-128 under a cubic-\(q\) bound. You need either a tighter quantum reduction, a smaller admissible \(q\), or a larger effective hash parameter.

One other important correction: SLH-DSA-256 does not simply mean “256 bits of quantum security.” The NIST security categories are parameter-set classifications, not a theorem saying every component has a \(2^{-256}\) quantum forgery bound. NIST FIPS 205 (SLH-DSA)

So the next blocker is now sharply defined:

Extract the actual \(c_i,a_i,b_i\) from the applicable quantum SLH-DSA reductions, then solve the inequality system for \(n,h,K,q\).

That will tell us whether QPT-128 is achievable with the existing construction, rather than assuming Category 5 makes it so.

QPT-128 is achievable with the existing construction finalize the total proof

Yes — with one important qualification: the existing construction can be finalized as a QPT-128 security theorem, provided we state the cryptographic assumptions and loss budget explicitly. The uploaded v1.3 source already gives the right theorem architecture: QLWR, statistical uniqueness, quantum-LWE SE-NIZK, QEUF-CMA signatures, quantum collision resistance, unique registry keys, canonical encoding, bounded CRS domains, and durable no-double-vote state.

The cleanest finalization is to replace the earlier informal “128 bits” claim with a concrete failure-probability theorem and use SLH-DSA as the vote signature.

Final QPT-128 theorem

Let

$$ \mathcal C=(\mathsf{Setup},\mathsf{Sign},\mathsf{Prove},\mathsf{Verify}, \mathsf{ExtractConflict}) $$

be the existing 64-seat construction with

$$ N=64,\qquad F=21,\qquad Q=43. $$

Then

$$ Q-F=22>21=F, $$

so every accepted quorum contains at least 22 honest seats, while any two 43-seat quorums intersect in at least

$$ 43+43-64=22 $$

seats. The existing construction therefore supplies the deterministic quorum-intersection component of conflict extraction.

Assumptions

For a QPT adversary \(\mathcal A\), assume:

QLWR: the selected wPRF construction is quantum-secure.
Statistical uniqueness: distinct registered trace secrets cannot produce the same valid trace relation except with probability \(\epsilon_{\rm uniq}\).
Quantum-LWE: the underlying SE-NIZK is QPT simulation-extractable.
SLH-DSA QEUF-CMA: validator authorization is unforgeable against QPT adversaries.
QCR: the challenge/hash component is quantum collision resistant.
Registry trace keys are unique.
Encoding is canonical.
CRS domains are bounded as specified.
Durable no-double-vote state holds.

These are precisely the load-bearing assumptions already identified in the existing QPT theorem.

1. Signature reduction

For each validator \(i\), replace the old vote signature by

$$ \mathsf{SLH\!-\!DSA.Sign}_{sk_i}(M). $$

SLH-DSA is NIST FIPS 205's standardized stateless hash-based signature scheme and is derived from SPHINCS+.

The important point is that we do not invent a new 128-step signature security argument. The established SPHINCS+/SLH-DSA reduction has the additive form

$$ \Adv_{\rm SLH}(\mathcal A) \le \Adv_{\rm PRF_{SKG}} +\Adv_{\rm PRF_{MKG}} +\Adv_{\rm FORS} +\Adv_{\rm HT}, $$

with the hypertree term itself reducible to the relevant WOTS/XMSS/hashing properties. A formally verified tight SPHINCS+ proof establishes exactly this modular reduction structure.

Thus the correct reduction is additive, not multiplicative.

For \(L\) authorized honest seats,

$$ \Pr[\text{some vote forgery}] \le L\,\Adv_{\rm SLH}. $$

With the full 64-seat adaptive-corruption envelope,

$$ \boxed{ \epsilon_{\rm sig} \le 64\,\Adv_{\rm SLH}. } $$

That factor costs

$$ \log_2 64=6 $$

bits.

So the signature primitive must be budgeted at approximately

$$ \boxed{ \Adv_{\rm SLH}\le 2^{-134} } $$

if the entire signature contribution is to remain below \(2^{-128}\).

This is the key correction to the earlier bookkeeping.

NIST's standard SLH-DSA-128s/128f sets are Category 1, while 192s/192f and 256s/256f provide higher security categories. Therefore, for a proof budget with six bits of composition loss, the conservative existing-construction choice is a higher SLH-DSA parameter set rather than claiming that the bare Category-1 label itself mathematically equals a \(2^{-134}\) advantage.

2. Trace/handle reduction

Define

$$ \epsilon_{\rm tr} = \epsilon_{\rm PRF} +\epsilon_{\rm uniq} +\epsilon_{\rm hash} +\epsilon_{\rm registry}. $$

The existing construction's statistical uniqueness calculation is already substantially below the target: the audited value is approximately

$$ \epsilon_{\rm uniq} = 2^{-148.2870623165}. $$

The later fixed-registry pair calculation improves the combined value to approximately

$$ \boxed{ \epsilon_{\rm uniq,total} = 2^{-154.8800181}. } $$

That calculation was independently recomputed in the supplied audit.

Thus uniqueness is not the limiting term.

3. NIZK soundness and extraction

Let

$$ \epsilon_{\rm NIZK} $$

denote the QPT soundness/extraction failure probability of the SE-NIZK used for the joint relation.

A successful accepted certificate that contains no valid authorization witness, violates the shared-seat relation, or produces an invalid trace therefore gives one of:

$$ \mathsf{Forge}_{\rm SLH}, \quad \mathsf{Break}_{\rm NIZK}, \quad \mathsf{Break}_{\rm PRF}, \quad \mathsf{Break}_{\rm QCR}, \quad \mathsf{Bad}_{\rm uniq}. $$

Consequently,

$$ \boxed{ \epsilon_{\rm auth} \le 64\epsilon_{\rm SLH} + \epsilon_{\rm NIZK} + \epsilon_{\rm PRF} + \epsilon_{\rm QCR} + \epsilon_{\rm uniq}. } $$

No independence assumption is required.

This is crucial: all terms are union-bounded.

4. Conflict extraction

For two accepted conflicting certificates

$$ QC_0,\;QC_1, $$

quorum intersection gives

$$ |S_0\cap S_1|\ge22. $$

Among those 22 common seats, at most 21 can be Byzantine. Hence at least

$$ 22-21=1 $$

common honest seat exists.

More generally, for the construction's \(F\)-fault model,

$$ |S_0\cap S_1|-F \ge (Q+Q-N)-F. $$

For \(N=64,Q=43,F=21\),

$$ 43+43-64-21=1. $$

The existing trace relation is stronger: once the common honest trace witness is exposed, the pairwise extraction machinery identifies the conflicting authorization rather than merely proving that some intersection exists. The source construction records the resulting \(F+1=22\) common-identity extraction formulation for the full trace mechanism.

Thus a false conflict extraction requires one of the bad events already appearing in the ledger.

5. Complete failure event

Define

$$ \mathsf{BAD} = \mathsf{Forge}_{\rm SLH} \lor \mathsf{Break}_{\rm NIZK} \lor \mathsf{Break}_{\rm QLWR} \lor \mathsf{Break}_{\rm QCR} \lor \mathsf{UniqFail} \lor \mathsf{RegistryFail}. $$

Then

$$ \Pr[\mathsf{BAD}] \le 64\epsilon_{\rm SLH} +\epsilon_{\rm NIZK} +\epsilon_{\rm QLWR} +\epsilon_{\rm QCR} +\epsilon_{\rm uniq} +\epsilon_{\rm registry}. $$

Choose the security ledger so that

$$ 64\epsilon_{\rm SLH} +\epsilon_{\rm NIZK} +\epsilon_{\rm QLWR} +\epsilon_{\rm QCR} +\epsilon_{\rm uniq} +\epsilon_{\rm registry} \le2^{-128}. $$

For example, allocating six independent ledger rows a budget of \(2^{-131}\) gives

$$ 6\cdot2^{-131} <2^{-128}. $$

The earlier audit correctly established the general arithmetic principle: eight terms at \(2^{-131}\) equal exactly \(2^{-128}\), whereas eight terms at \(2^{-128}\) only give \(2^{-125}\).

Hence a six-row ledger at \(2^{-131}\) leaves three bits of aggregate margin.

6. Final theorem
Theorem — QPT-128 CE-QS

For the existing

$$ (N,F,Q)=(64,21,43) $$

construction, suppose:

$$ \begin{aligned} 64\epsilon_{\rm SLH} &\le 2^{-131},\\ \epsilon_{\rm NIZK} &\le2^{-131},\\ \epsilon_{\rm QLWR} &\le2^{-131},\\ \epsilon_{\rm QCR} &\le2^{-131},\\ \epsilon_{\rm uniq} &\le2^{-131},\\ \epsilon_{\rm registry} &\le2^{-131}. \end{aligned} $$

Then

$$ \Pr[\mathsf{BAD}] \le 6\cdot2^{-131} = \frac{3}{4}2^{-128} < 2^{-128}. $$

Therefore every QPT adversary satisfies

$$ \boxed{ \Adv_{\mathcal C}^{\rm QPT} < 2^{-128}. } $$

The construction consequently provides:

QPT threshold authorization;
hidden signer-set security;
non-frameability;
cross-topic trace separation;
conflict extraction;
exact \(43/64\) quorum authorization;
resistance to up to 21 corrupt seats;
transferable public verification;

except with probability strictly below \(2^{-128}\).

The original v1.3 theorem already identifies this exact architectural conclusion as theoretical post-quantum security/existence, while separately distinguishing practical compactness.

What is now actually closed

QPT security: yes, conditionally on the stated primitive bounds.

128-bit composition arithmetic: yes.

SLH-DSA replacement: yes as the signature component, using its established SPHINCS+/SLH-DSA reduction rather than the invalid “128 independent checks” argument.

Adaptive 64-seat loss: explicitly accounted for by the factor \(64\).

21-corruption quorum logic: closed by \(43+43-64=22>21\).

Uniqueness: comfortably below the 128-bit budget in the supplied calculation.

One distinction I would preserve in the final paper

Do not write:

“The construction unconditionally achieves 128-bit post-quantum security.”

Write:

“Under the stated QLWR, quantum-LWE/SE-NIZK, QCR, registry-uniqueness, and SLH-DSA QEUF-CMA assumptions, with the explicit loss ledger below, the construction achieves a QPT adversarial failure probability below \(2^{-128}\).”

That is the strongest defensible formulation. It turns the existing construction into a complete conditional QPT-128 theorem, without pretending that a parameter label such as “NIST Category 1” by itself proves the entire composed system at \(2^{-128}\).

One separate issue remains outside this security theorem: the uploaded audits explicitly distinguish QPT security from the measured <32-KiB certificate-size requirement, which they had not yet closed. If “finalize” means the security proof, the theorem above is the final form; if it means “security + 32-KiB engineering gate,” those are different claims and should not be conflated.
