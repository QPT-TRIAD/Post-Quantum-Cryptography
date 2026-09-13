# CE-QS v0.9 — Quantum-Lift Ledger and Private-Wrapper Theorem
## Continuing the Proof for Public and Hidden Signer Sets

**Status:** proof continuation from Target-B v0.8.  
**Date:** 2026-09-08.  
**Tracks:** \(B_0\) public signer set and \(B_1\) hidden signer set.  
**Claim boundary:** this document closes the missing theorem-number citation, reduces the \(B_0\) QPT question to a specific primitive chain, and proves a generic private-wrapper theorem for \(B_1\). It does not claim a practical <32-KiB implementation or a complete QPT instantiation of the monotone-policy aggregate stack.

---

# 0. Theorem-number verification from v0.8

The v0.8 validation left one source detail unverified.

The monotone-policy aggregate-signature paper states:

### Theorem 7.5

Assuming a polynomially secure **2-composable vPIR for policies**, there exists a BARG with \(O(t)\)-adaptive subset extraction for weighted-threshold policies with threshold \(t\), with prover/aggregation time polynomial in \(t\).

### Theorem 7.6

Assuming:

- a 2-composable vPIR for policies; and
- a hash family with local opening,

there exists an aggregate-signature scheme for weighted-threshold policies with aggregation time polynomial in \(t\).

Setting:

\[
\alpha_i=1
\]

gives the ordinary unweighted threshold case.

So the specific theorem numbers used in v0.8 are now verified.

---

# 1. QPT dependency graph for Target \(B_0\)

The v0.8 public-signer construction is:

\[
QC_0
=
(B,\widehat{\sigma})
\]

where:

- \(B\) is the exact signer bitmap;
- \(f_B\) is deterministically derived from \(B\);
- \(\widehat{\sigma}\) is a monotone-policy aggregate signature for \(f_B\).

The classical security proof is complete conditionally on monotone-policy aggregate unforgeability.

To make the same theorem QPT-secure, the dependency chain is:

\[
\boxed{
\begin{array}{c}
\text{QEUF base signatures}\\
+\text{QCR hash/local opening}\\
+\text{QPT seBARG}\\
\Downarrow\\
\text{QPT 2-composable vPIR}\\
\Downarrow\\
\text{QPT adaptive-subset BARG}\\
\Downarrow\\
\text{QPT monotone-policy aggregate}\\
\Downarrow\\
\text{QPT }B_0\text{ quorum certificate}.
\end{array}
}
\]

The important point is that not every arrow is currently supplied by a published theorem in exactly this form.

---

# 2. Quantum local-opening lemma

The hash-tree/local-opening component is not the hard part.

Let a Merkle-style local-opening hash family be built from collision-resistant hash:

\[
H.
\]

Suppose a QPT adversary outputs:

\[
(rt,j,0,\rho_0,1,\rho_1)
\]

such that both openings verify at the same root and position.

Follow the two authentication paths from the leaf upward.

At the first level where the reconstructed node values become equal despite distinct child inputs, obtain:

\[
x\neq x'
\]

with:

\[
H(x)=H(x').
\]

This transformation is deterministic and straight-line.

Therefore:

\[
\boxed{
Adv^{QOpenBind}_{HT}
\le
Adv^{QColl}_{H}.
}
\]

Hence a quantum-collision-resistant Merkle hash gives the local-opening binding property against QPT adversaries.

This closes the hash/local-opening portion of the v0.8 quantum-lift ledger.

---

# 3. Quantum vPIR lifting proposition

The monotone-policy paper constructs 2-composable vPIR from:

1. a hash family with local opening;
2. a somewhere-extractable BARG.

Its proof uses:

- completeness;
- seBARG extraction/soundness;
- index hiding;
- collision resistance of local openings;
- straight-line hybrid/coupling arguments.

It does not rely on classical rewinding of the adversary.

Therefore define the following QPT assumptions on the seBARG:

### QB1. QPT index hiding

The hidden extraction index remains indistinguishable to QPT adversaries.

### QB2. QPT somewhere extraction/soundness

Accepted adversarial proofs satisfy the required extraction/soundness property against QPT provers.

### QB3. QPT composable security

The two parallel proof instances used by the vPIR construction remain secure jointly against QPT adversaries.

### Proposition 3.1

If:

- QB1–QB3 hold;
- the local-opening hash is QPT binding;

then the proof of 2-composable vPIR security lifts to QPT adversaries by the same straight-line hybrid structure.

Thus:

\[
\boxed{
Adv^{QPT}_{vPIR}
\le
Adv^{QPT}_{seBARG}
+
Adv^{QOpenBind}_{HT}
+
negl(\lambda).
}
\]

This is a **conditional lifting proposition**, not a claim that the exact seBARG used in the 2024 paper already has QB1–QB3 in the literature.

---

# 4. QPT threshold-aggregate lifting theorem

Theorem 7.5 builds the adaptive-subset BARG for threshold policies from 2-composable vPIR.

Theorem 7.6 then builds the aggregate-signature scheme from:

- that threshold BARG;
- a local-opening hash family;
- an arbitrary base digital signature scheme.

The CE-QS \(B_0\) reduction itself is black-box and straight-line.

Therefore:

### Theorem 4.1

If:

1. the base signature is QEUF-CMA secure;
2. the hash/local-opening family is QPT secure;
3. the 2-composable vPIR satisfies its definition against QPT adversaries;
4. Theorem-7.5 adaptive subset extraction holds against QPT adversaries;

then the public-signer CE-QS \(B_0\) theorem holds against QPT adversaries.

Formally:

\[
\boxed{
Adv^{QPT}_{B_0}
\le
Adv^{QPT}_{MPAgg}
+
\epsilon_{\rm rollback}
+
Adv^{BaseSafety}.
}
\]

No random-oracle programming and no forking lemma enters the CE-QS reduction.

---

# 5. The actual QPT bottleneck

A broad search finds post-quantum succinct-proof results from LWE and post-quantum NIZKs from LWE.

It also finds prior work showing **somewhere statistically sound** argument systems whose straight-line soundness proofs remain post-quantum when the underlying assumptions are post-quantum.

However, these are not the same theorem as:

\[
\boxed{
\text{QPT adaptive-subset-extractable BARG for the exact policy relation used by Theorem 7.5}.
}
\]

Likewise, the 2024 monotone-policy aggregate paper defines its adversaries classically.

Therefore the strongest accurate status is:

\[
\boxed{
\textbf{The }B_0\textbf{ QPT lift is reduced to QB1--QB3 / QPT adaptive-subset extraction, not yet discharged.}
}
\]

This is much narrower than the previous generic statement "QPT security is open."

---

# 6. No concrete monotone-policy implementation found

The current literature and author/project pages confirm the construction and its asymptotic theorems.

This proof pass did not locate a public implementation or concrete byte/latency table for the full chain:

\[
seBARG
+
hash/local-opening
+
2\text{-composable vPIR}
+
threshold aggregate.
\]

Therefore:

\[
\boxed{
B_0\text{ is theoretically succinct but still has no concrete CE-QS parameterization in this record.}
}
\]

No 32-KiB claim is made.

---

# 7. Hidden signer Target \(B_1\): a new wrapper construction

The hidden-signer problem does **not** require a threshold-ring backend if we already possess the exact public-signer \(B_0\) aggregate.

Instead, hide the entire public \(B_0\) certificate inside a zero-knowledge proof and bind the same hidden bitmap to CET tags.

This is the **Private Wrapper** construction.

---

# 8. Private Wrapper public statement

The public statement is:

\[
X=
(
R_e,
\widehat{vk},
\tau,
H(M),
q,
E
)
\]

where:

\[
E=(e_1,\ldots,e_s)
\]

is the public list of distinct CET tags.

No signer bitmap is public.

No monotone-policy aggregate signature is public.

---

# 9. Private Wrapper witness

The hidden witness is:

\[
W=
(
B,
\widehat{\sigma},
\{x_i,k_i\}_{i:B_i=1},
\pi
)
\]

where:

- \(B\in\{0,1\}^n\) is the hidden signer bitmap;
- \(\widehat{\sigma}\) is a valid \(B_0\) monotone-policy aggregate;
- \(x_i\) is signer \(i\)'s trace secret;
- \(k_i\) is signer \(i\)'s mask secret;
- \(\pi\) is a hidden bijection from selected signer positions to the public tag positions.

Require:

\[
w(B)=s
\]

and:

\[
s\ge q.
\]

---

# 10. Private Wrapper relation

Define:

\[
\mathcal R_{\rm Priv}(X;W)=1
\]

iff all conditions hold.

## PW1. Exact hidden threshold

\[
w(B)=|E|\ge q.
\]

## PW2. Bitmap-derived policy

Construct:

\[
f_B(z)
=
\mathbf 1
\left[
\sum_i B_i z_i
\ge
w(B)
\right].
\]

## PW3. Hidden aggregate verification

\[
AggVerify(
crs_{MPA},
f_B,
\widehat{vk},
M,
\widehat{\sigma}
)
=
1.
\]

## PW4. Trace binding

For every selected:

\[
i:B_i=1,
\]

\[
G_{\rm tr}(x_i)=X_i.
\]

## PW5. Mask binding

\[
G_{\rm mask}(k_i)=K_i.
\]

## PW6. CET generation

Let:

\[
c=H_F(\tau,H(M)).
\]

For every selected \(i\),

\[
e_{\pi(i)}
=
F_{k_i}(\tau)+c x_i.
\]

## PW7. Bijection

\[
\pi
\]

maps the selected \(w(B)\) identities bijectively to all positions in \(E\).

## PW8. Public uniqueness

All tags in:

\[
E
\]

are pairwise distinct.

---

# 11. Private Wrapper proof system

Let:

\[
\mathsf{ZK}
=
(
Setup,
Prove,
Verify
)
\]

be a non-interactive zero-knowledge argument for:

\[
\mathcal R_{\rm Priv}.
\]

For strong framing proofs we may additionally require:

- simulation extractability; or
- knowledge soundness.

The public \(B_1\) certificate is:

\[
\boxed{
QC_{\rm priv}
=
(
v,e,\tau,H(M),q,E,\pi_{\rm ZK}
).
}
\]

Neither:

\[
B
\]

nor:

\[
\widehat{\sigma}
\]

appears in the certificate.

---

# 12. Theorem — exact hidden quorum soundness

### Theorem 12.1

Assume:

1. the ZK argument is sound for \(\mathcal R_{\rm Priv}\);
2. the monotone-policy aggregate is unforgeable.

If:

\[
VerifyPriv(QC_{\rm priv})=1,
\]

then, except with the sum of those failure advantages, at least:

\[
q
\]

distinct registered identities signed \(M\).

### Proof

ZK soundness implies existence of a witness:

\[
(B,\widehat{\sigma},\ldots)
\]

satisfying PW1–PW8.

PW1 gives:

\[
w(B)\ge q.
\]

PW3 gives an accepted public-signer aggregate for the bitmap policy:

\[
f_B.
\]

By the v0.8 exact signer-set theorem, every selected honest uncompromised identity in:

\[
\operatorname{supp}(B)
\]

actually signed \(M\), except with aggregate-signature forgery advantage.

The bitmap has:

\[
w(B)\ge q
\]

distinct indices.

Therefore the hidden certificate has at least \(q\) distinct signer authorizations.

\[
\blacksquare
\]

---

# 13. Theorem — same-hidden-set binding

### Theorem 13.1

In every satisfying witness of:

\[
\mathcal R_{\rm Priv},
\]

the signer set authenticated by the hidden aggregate is exactly the signer set represented by the public CET list.

### Proof

The aggregate is verified against:

\[
f_B.
\]

The CET clauses PW4–PW7 quantify over the same bitmap:

\[
B.
\]

PW7 is a bijection between:

\[
\operatorname{supp}(B)
\]

and all positions in \(E\).

Therefore:

\[
S_{\rm Agg}
=
\operatorname{supp}(B)
=
S_{\rm CET}.
\]

\[
\blacksquare
\]

This is the private-wrapper analogue of v0.6's same-hidden-set theorem, but it no longer depends on a threshold-ring proof.

---

# 14. Theorem — hidden quorum anonymity

Consider two equal-size admissible signer sets:

\[
S_0,S_1
\]

whose members do not violate the conflict predicate in the challenge topic.

### H0

Real private-wrapper certificate for \(S_b\).

### H1

Replace the NIZK proof by its zero-knowledge simulation.

Loss:

\[
\epsilon_{\rm ZK}.
\]

The hidden bitmap:

\[
B
\]

and aggregate:

\[
\widehat{\sigma}
\]

are now absent from the adversary's view except through the simulated proof.

### H2

For every challenge signer replace:

\[
F_{k_i}(\tau)
\]

by uniform randomness.

Loss:

\[
s\epsilon_{\rm PRF}.
\]

Each CET becomes uniform in the tag space.

Therefore the public tag list distribution no longer depends on the signer identities, except for negligible accidental collision probability.

Thus:

\[
\boxed{
Adv^{Anon}_{Priv}
\le
\epsilon_{\rm ZK}
+
s\epsilon_{\rm PRF}
+
\epsilon_{\rm tag-coll}.
}
\]

Notice that **MPAgg itself needs no signer-anonymity theorem** because the MPA aggregate is hidden inside the zero-knowledge witness.

This is a major simplification.

---

# 15. Theorem — private conflict extraction

Take two accepted conflicting private certificates:

\[
QC_0,
QC_1.
\]

By Theorem 12.1, obtain hidden signer sets:

\[
S_0,S_1
\]

with:

\[
|S_0|,|S_1|\ge q.
\]

For ordinary BFT:

\[
|S_0\cap S_1|
\ge
2q-n
=
f+1.
\]

By Theorem 13.1, every member of each hidden signer set has exactly one certified public CET in the corresponding tag list.

For every:

\[
i\in S_0\cap S_1,
\]

the two public tags satisfy:

\[
e_{i,0}=r_i+c_0x_i,
\]

\[
e_{i,1}=r_i+c_1x_i.
\]

Hence:

\[
x_i
=
(c_0-c_1)^{-1}
(e_{i,0}-e_{i,1}).
\]

The pairwise scan finds that pair.

Therefore:

\[
\boxed{
|ExtractConflict(QC_0,QC_1)|
\ge
f+1.
}
\]

The extraction algorithm itself needs no NIZK trapdoor.

It is public.

---

# 16. Theorem — private non-frameability

A false accusation requires one of:

1. a false private-wrapper statement accepted;
2. a false signer bitmap aggregate accepted;
3. a CET false-trace event.

Therefore:

\[
\boxed{
Adv^{Frame}_{Priv}
\le
2\epsilon_{\rm ZK-sound}
+
2Adv^{UF}_{MPAgg}
+
Adv^{FalseTrace}_{CET}.
}
\]

If a simulation-extractable NIZK is used, the reduction can be strengthened to extract the offending witness from fresh adversarial proofs even after simulated-proof queries.

---

# 17. Post-quantum NIZK availability

Post-quantum non-interactive zero-knowledge arguments for NP from LWE are known.

More strongly, current literature cites an LWE-based **post-quantum simulation-extractable, adaptive multi-theorem computationally zero-knowledge NIZK for NP** in the CRS model.

Therefore the private wrapper's required *security interface* has a post-quantum existence result under LWE.

However, the available theorem does not by itself give the project a practical succinct proof.

Thus:

\[
\boxed{
\text{PQ zero knowledge is available;}
\qquad
\text{PQ succinct private-wrapper proof remains a compactness question}.
}
\]

---

# 18. Standard-assumption zero-knowledge route from BARGs

There is also a second route.

Recent work proves that:

- an adaptively sound BARG plus a one-way function implies a computational NIZK for NP;
- alternatively, a somewhere-sound BARG plus public-key encryption gives a computational NIZK.

Existing BARG constructions from standard assumptions can have proof size polylogarithmic in the number of batch instances.

The resulting NIZK compiler itself guarantees zero knowledge but its proof-size transformation is not automatically polylogarithmic in the private-wrapper witness; its parameterization can be sublinear rather than fully succinct.

Therefore this route is useful as a **standard-assumption privacy compiler**, but it does not yet close the 32-KiB gate.

---

# 19. Private Wrapper Theorem

### Theorem 19.1

Assume:

1. an exact public-signer \(B_0\) monotone-policy aggregate signature;
2. a binding CET construction;
3. a zero-knowledge sound argument for \(\mathcal R_{\rm Priv}\).

Then there exists a sidecar-free hidden-signer quorum certificate satisfying:

- exact hidden threshold authorization;
- signer-set privacy for one non-conflicting certificate;
- public conflict extraction;
- honest non-frameability;
- no permanent tracing authority.

The certificate size is:

\[
\boxed{
|QC_{\rm priv}|
=
|E|
+
|\pi_{\rm ZK}|
+
O(\lambda).
}
\]

For the current scalar CET profile:

\[
|E|
=
43\cdot32
=
1376\text{ bytes}.
\]

The hidden bitmap and hidden MPA aggregate do **not** contribute to public certificate size.

\[
\blacksquare
\]

---

# 20. What v0.9 changes about Target \(B_1\)

Before v0.9 the hidden-signer branch appeared to require a specialized compact threshold-ring backend.

v0.9 shows that this is not necessary.

The threshold-ring machinery can be replaced by:

\[
\boxed{
\text{public-signer exact aggregate as hidden witness}
+
\text{zero-knowledge wrapper}
+
\text{public CET list}.
}
\]

This means:

- CTRS is no longer the unique conceptual route;
- LoTRS structured anonymity is no longer required;
- the monotone-policy aggregate can provide exact authorization;
- the NIZK provides privacy;
- CET provides conflict-only public tracing.

The cryptographic roles are now orthogonal.

---

# 21. QPT composition ledger for \(B_1\)

A fully QPT-secure private wrapper requires:

### Q1. QPT public aggregate

The unresolved \(B_0\) QB1–QB3 chain from Sections 1–5.

### Q2. QPT zero knowledge

Available in principle from LWE-based PQ NIZK literature.

### Q3. QPT soundness/extractability

Simulation-extractable PQ NIZKs from LWE provide a qualified route.

### Q4. QPT CET mask pseudorandomness

Requires the chosen mask adapter to be QPRF-secure given public bindings.

### Q5. QPT trace-commitment binding

Requires quantum preimage/second-preimage/collision security as appropriate.

### Q6. QPT false-trace proof

The v0.5 registration-first classical-ROM linear-relation argument must be replaced by a quantum-query bound or a standard-model challenge derivation.

Thus the private-wrapper theorem is backend-neutral, but complete QPT security is still blocked by:

\[
\boxed{
\text{QPT MPA adaptive-subset extraction}
+
\text{QPT CET trace-soundness analysis}.
}
\]

The NIZK itself is no longer the conceptual blocker.

---

# 22. Compactness frontier after v0.9

## Public \(B_0\)

Theoretical aggregate:

\[
poly(\lambda,\log n)
\]

plus 8-byte bitmap.

Practical bytes unknown.

## Private \(B_1\)

Theoretical certificate:

\[
1376\text{ CET bytes}
+
|\pi_{\rm ZK}|
+
O(\lambda).
\]

The MPA aggregate is hidden witness data, so it does not appear on the wire.

Thus the private branch's compactness problem is now exactly:

\[
\boxed{
\textbf{Can the private-wrapper NIZK fit inside roughly 30 KiB at }n=64,q=43?
}
\]

This is a substantially narrower implementation target than finding a wholly new threshold-ring signature.

---

# 23. New theorem hierarchy

The proof stack is now:

### Layer 1 — BFT arithmetic

\[
2q-n=f+1.
\]

### Layer 2 — Public exact authorization

Bitmap-derived monotone-policy aggregate.

### Layer 3 — Private wrapping

Hide:

\[
(B,\widehat{\sigma})
\]

inside ZK and bind it to CETs.

### Layer 4 — Conflict extraction

CET pairwise algebra.

### Layer 5 — BFT accountability

At least \(f+1\) common identities are exposed on conflict.

This modular decomposition means each cryptographic component has one job.

---

# 24. Remaining proof obligations after v0.9

The following are now the true open theoretical items.

## O1. QPT adaptive-subset extraction

Provide or prove the quantum analogue of the MPA threshold-policy BARG/vPIR chain.

## O2. QPT false-trace proof

Upgrade v0.5 R3 from classical ROM to QROM or remove the ROM dependence.

## O3. Succinct/private-wrapper implementation

Instantiate \(\mathcal R_{\rm Priv}\) in a proof system and measure:

\[
|\pi_{\rm ZK}|.
\]

## O4. Concrete MPA implementation

Measure the hidden aggregate's proving cost even though its bytes are not public.

## O5. CRS/setup integration

Define how the MPA CRS and NIZK CRS are generated and rotated at epoch boundaries.

These are no longer ambiguous research directions.

---

# 25. Main conclusion

v0.9 advances both branches.

For \(B_0\):

\[
\boxed{
\text{the exact Theorem-7.5/7.6 source chain is confirmed and the QPT gap is localized}.
}
\]

For \(B_1\):

\[
\boxed{
\textbf{a specialized anonymous threshold-ring signature is no longer necessary in the abstract construction}.
}
\]

Instead:

\[
\boxed{
QC_{\rm priv}
=
(
E,
\pi_{\rm ZK}
)
}
\]

where the zero-knowledge witness contains:

\[
(B,\widehat{\sigma},\text{CET secrets}).
\]

This construction inherits exact authorization from the public MPA aggregate, privacy from ZK, and conflict extraction from CET.

The remaining practical compactness question is the size and proving cost of one concrete post-quantum proof of \(\mathcal R_{\rm Priv}\), not the existence of a new threshold-ring primitive.
