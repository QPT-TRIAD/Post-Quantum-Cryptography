# Conflict-Extractable Compact Post-Quantum Quorum Signatures Without a Sidecar
## Frontier Construction v0.1 — Fixed-Committee Traceable Threshold-Ring Direction

**Status:** candidate construction and proof program; not a security proof, not a priority claim, not production cryptography.  
**Date:** 2026-09-08  
**Goal:** remove the external accountability sidecar while keeping a hidden BFT quorum and enabling public extraction of a common conflicting signer from two compact post-quantum certificates.

---

# 1. Target

For a registered committee \(R=\{pk_1,\dots,pk_n\}\), threshold \(q\), topic/conflict-domain \(\tau\), and message \(M\), define a certificate

\[
\Sigma \leftarrow \mathsf{SignQuorum}(R,q,\tau,M,S)
\]

for a hidden signer set \(S\subseteq[n]\), \(|S|\ge q\).

The target conflict interface is

\[
\boxed{
\mathsf{ExtractConflict}
(\tau,M_0,\Sigma_0,M_1,\Sigma_1)
\rightarrow
\{(i,\pi_i)\}
}
\]

when \(M_0\neq M_1\) are conflicting statements in the same domain.

For BFT:

\[
n=3f+1,\qquad q=2f+1.
\]

Then any two quorum signer sets satisfy

\[
|S_0\cap S_1|\ge f+1.
\]

The certificate must not contain individual ML-DSA signatures and requires no external evidence sidecar.

---

# 2. Literature bridge

The construction direction is obtained by combining ideas from four previously separate schools.

## 2.1 Traceable threshold ring signatures

Tetris (Avitabile–Botta–Fiore, ESORICS 2025) formalizes traceability in a threshold ring setting and introduces **Doubly-Authentication-Preventing Tags (DAPT)**.

A DAPT tag is tied to:

- one hidden signing key,
- one topic,
- one message.

One tag is pseudorandom/anonymity preserving. Two tags from the same key and topic but different messages permit public tracing.

Tetris is pairing/Groth–Sahai based and its final construction is linear size. Its hardest machinery is required because its signatures are **extendable after creation**.

A fixed BFT epoch does not require that functionality.

## 2.2 Post-quantum threshold ring signatures from VOLE-in-the-Head

Chiang–Damgård–Duro–Engan–Kolby–Scholl (CCS 2025) construct post-quantum threshold ring signatures from symmetric-key one-wayness and VOLE-in-the-Head ZK.

Their work already supplies:

- hidden \(t\)-of-\(n\) signers;
- public verification of a threshold;
- deterministic key-binding tags;
- pseudorandomness/anonymity arguments for tags;
- public aggregation;
- succinct approximate lower-bound arguments of knowledge.

Their tags are **linkability tags**, not conflict-extracting DAPT tags.

This is the closest post-quantum scaffold.

## 2.3 DAPS/PAPS

Boneh–Kim–Nikolaenko give lattice-based post-quantum DAPS/PAPS.

The important design principle is:

\[
\text{one authentication is safe}
\]

but

\[
\text{two predicate-conflicting authentications reveal private signer information}.
\]

This proves that deliberate post-quantum conditional leakage is cryptographically meaningful; it is not inherently incompatible with lattice/post-quantum assumptions.

## 2.4 Rate-limiting nullifiers / compact e-cash

Rate-limiting nullifiers and double-spend tracing use the same algebraic pattern:

\[
\text{one point hides a secret;}
\qquad
\text{two forbidden uses reconstruct it}.
\]

This suggests that the trace tag itself should be a small algebraic share rather than a conventional digital signature.

---

# 3. Main design change from the earlier TTS memo

The earlier memo tried to modify the masking randomness inside a lattice threshold signature.

That creates a direct collision with rejection sampling and leakage-prevention mechanisms.

This version instead separates the layers:

\[
\boxed{
\text{PQ hidden-threshold proof}
+
\text{anonymous conflict trace tags}.
}
\]

The base proof establishes that at least \(q\) distinct registered secret-key holders participated.

Trace tags carry the conditional accountability.

No Hermine/Raccoon rejection-sampling internals need to be modified.

---

# 4. Working primitive: Conflict-Extractable Tag (CET)

This section gives an algebraic research candidate, not a final standardized primitive.

Let \(\mathbb F_p\) be a large field.

Every validator has:

- normal hidden signing witness \(sk_i\);
- independent trace secret \(x_i\in\mathbb F_p\);
- independent mask-PRF key \(k_i\);
- public trace commitment

\[
X_i=H_T(x_i).
\]

For conflict domain \(\tau\),

\[
r_{i,\tau}=F_{k_i}(\tau)\in\mathbb F_p.
\]

For message \(M\), derive

\[
c=H_c(\tau\parallel M)\in\mathbb F_p.
\]

The trace tag is

\[
\boxed{
e_i(\tau,M)
=
r_{i,\tau}+c\,x_i
\pmod p.
}
\]

## 4.1 One-certificate hiding

Under PRF security, \(r_{i,\tau}\) is pseudorandom.

Therefore

\[
e_i=r_{i,\tau}+c x_i
\]

is computationally indistinguishable from a random field element to an observer who does not know \(k_i\).

The public commitment \(H_T(x_i)\) should not permit recovery of \(x_i\).

## 4.2 Same-topic conflict extraction

Suppose the same signer produces tags on two different messages in the same domain:

\[
e_0=r+c_0x_i,
\]

\[
e_1=r+c_1x_i.
\]

Then:

\[
e_0-e_1=(c_0-c_1)x_i.
\]

If \(c_0\neq c_1\),

\[
\boxed{
\widehat x_i=
(e_0-e_1)(c_0-c_1)^{-1}
\pmod p.
}
\]

The candidate is publicly checked using

\[
H_T(\widehat x_i)\stackrel?=X_i.
\]

Thus two conflicting tags reveal an identity-binding trace secret.

## 4.3 Different topics

For \(\tau_0\neq\tau_1\),

\[
r_{i,\tau_0}\neq r_{i,\tau_1}
\]

pseudorandomly, so subtraction does not cancel the mask.

## 4.4 Same message

For the same topic and same message the deterministic tag repeats.

This can expose **linkability of duplicate signing**, but does not reveal \(x_i\).

That matches standard traceable-ring semantics: same issue/message can be linkable while different messages in the issue trigger identity extraction.

---

# 5. Important key-separation rule

The extracted \(x_i\) MUST NOT be:

- the validator consensus signing key;
- the VOLE threshold-ring witness;
- the PRF mask key.

It is a dedicated tracing secret.

Therefore conflict extraction does not automatically forge future consensus signatures.

A validator whose trace secret is exposed is considered proven faulty and must be removed/re-keyed before it is permitted to participate in a subsequent accountability domain.

A production construction should preferably use forward-secure/per-domain trace secrets so exposure in one conflict domain cannot assist framing in future domains.

---

# 6. Quorum certificate

Let hidden signer set be

\[
S=\{i_1,\dots,i_t\},
\qquad
t\ge q.
\]

Every signer contributes a CET tag:

\[
e_j=e_{i_j}(\tau,M).
\]

The tags are shuffled so their correspondence with public keys is hidden.

Define

\[
E=(e_1,\dots,e_t).
\]

The public certificate is

\[
\boxed{
\Sigma=
(\tau,M,q,E,\Pi).
}
\]

Here \(\Pi\) is a post-quantum zero-knowledge/threshold-ring proof of the relation:

> There exist \(t\ge q\) **distinct** registered signer indices and valid secret signing witnesses such that every public tag in \(E\) is a correctly generated CET tag for one distinct hidden signer on \((\tau,M)\).

The indices must remain hidden.

The proof must bind the exact same hidden indices to:

1. threshold authentication;
2. CET tag generation.

This “same hidden active set across two relations” is exactly the kind of witness-binding problem that the threshold-ring/VOLE and Tetris proof lines teach us how to formulate.

---

# 7. Extraction algorithm

Given two accepted certificates

\[
\Sigma_0=(\tau,M_0,q,E_0,\Pi_0)
\]

and

\[
\Sigma_1=(\tau,M_1,q,E_1,\Pi_1)
\]

with \(M_0\neq M_1\):

1. Verify both certificates.
2. Compute:

\[
c_b=H_c(\tau\parallel M_b).
\]

3. For every pair

\[
(e_0,e_1)\in E_0\times E_1,
\]

compute:

\[
\widehat x=
(e_0-e_1)(c_0-c_1)^{-1}.
\]

4. Compute \(H_T(\widehat x)\).
5. Look it up in the registered trace-commitment table.
6. Every match identifies a common signer.

For \(q=43\):

\[
|E_0\times E_1|=1849.
\]

That is a trivial amount of conflict-only work.

Happy-path verification does not perform this quadratic trace scan.

---

# 8. Deterministic conflict-extraction theorem

Assume the ZK relation is sound, so every tag in \(E_b\) comes from one distinct signer in \(S_b\).

For BFT:

\[
n=3f+1,\qquad |S_0|,|S_1|\ge2f+1.
\]

Then:

\[
|S_0\cap S_1|\ge f+1.
\]

For every

\[
i\in S_0\cap S_1,
\]

one tag in \(E_0\) and one tag in \(E_1\) were generated using the same \(x_i\) and the same topic mask \(r_{i,\tau}\).

Therefore the pairwise scan contains the pair:

\[
(e_i(\tau,M_0),e_i(\tau,M_1)).
\]

For that pair:

\[
\widehat x_i=x_i.
\]

Consequently:

\[
\boxed{
|\mathsf{ExtractConflict}(\Sigma_0,\Sigma_1)|
\ge
f+1
}
\]

except through:

- threshold/ZK soundness failure;
- PRF/tag failure;
- hash/challenge collision;
- trace-commitment failure.

This is deterministic with respect to quorum intersection; it does not require probabilistic MinHash sampling.

---

# 9. Certificate size at the current 64-seat target

For:

\[
n=64,
\quad
f=21,
\quad
q=43,
\]

and one 256-bit field element per CET tag:

\[
43\times32
=
1376\text{ bytes}.
\]

Thus the trace payload itself is only:

\[
\boxed{1.344\text{ KiB}.}
\]

The complete certificate size is:

\[
\boxed{
|\Sigma|
=
|\Pi_{\mathrm{PQ-TRS}}|
+
1376
+
O(\lambda).
}
\]

The proof \(\Pi\), not the trace tags, becomes the dominant size target.

This is radically different from a 43-signature ML-DSA evidence sidecar, whose raw signature payload alone is on the order of 139 KiB using ML-DSA-65.

---

# 10. What “compact” means here

This construction is:

- **sidecar-free**;
- hidden-signer;
- conflict-extractable;
- practically compact for \(n\le64\).

It is **not asymptotically constant-size**, because it carries one anonymous trace tag per hidden signer:

\[
O(q\lambda)
\]

tag bits.

This is already much smaller than carrying \(q\) individual PQ signatures, but it does not yet meet the strongest possible Target-B requirement:

\[
O(\lambda)
\]

certificate size independent of \(q,n\).

That stricter target remains a second-stage research question.

---

# 11. Why this is a better immediate direction than sampled tags

A tempting alternative is to carry only \(k\) randomly sampled tags.

For two BFT quorums in a 64-seat committee:

\[
|S_0\cap S_1|\ge22.
\]

Their worst-case Jaccard overlap is at least

\[
J\ge22/64=0.34375.
\]

With ideal independent MinHash positions:

\[
P[\text{miss all common signers}]
\le
(1-J)^k.
\]

To drive this below \(2^{-128}\) requires approximately

\[
k=211.
\]

That is more tags than the deterministic \(q=43\) scheme at the current committee cap.

More importantly, a malicious combiner can adapt the signer set to public sampling randomness.

The deterministic all-signer-tag certificate therefore wins for the first practical construction.

---

# 12. Why fixed-committee BFT makes this easier than Tetris

Tetris solves a harder problem:

- the threshold can grow after the signature exists;
- the ring can grow after the signature exists;
- observers see the entire update history;
- strong anonymity must survive all updates.

That requires extendable proofs, re-randomizable commitments and shuffle machinery.

A BFT epoch already fixes:

\[
(R,q).
\]

So the first CE-QC construction can deliberately exclude:

- ring extension;
- threshold extension;
- post-signature join.

This removes the main reason Tetris needs its heaviest proof machinery.

The research target becomes:

\[
\boxed{
\text{fixed-ring PQ traceable threshold ring signature}
}
\]

rather than:

\[
\text{post-quantum Tetris with extendability}.
\]

---

# 13. Main post-quantum construction hypothesis

The most promising concrete route is:

\[
\boxed{
\text{VOLE-in-the-Head threshold ring signature}
+
\text{CET/DAPT-style tags}.
}
\]

The 2025 VOLE-in-the-Head threshold-ring work already has deterministic key-binding pseudorandom tags.

The proposed modification is conceptual:

\[
\text{linkable deterministic tag}
\longrightarrow
\text{conflict-extractable deterministic tag}.
\]

The relation proved by each anonymous signer is expanded from roughly:

\[
\mathsf{OwnKey}(pk_i,sk_i)
\]

to:

\[
\mathsf{OwnKey}(pk_i,sk_i)
\land
\mathsf{ValidTraceSecret}(X_i,x_i)
\land
e=F_{k_i}(\tau)+H_c(\tau,M)x_i.
\]

The threshold proof must still ensure distinct hidden keys.

---

# 14. Security games required

## 14.1 Correctness

An honestly formed \(q\)-signer certificate verifies.

## 14.2 Threshold unforgeability

No adversary controlling fewer than \(q\) valid witnesses can create an accepted certificate.

## 14.3 Quorum anonymity

Given one accepted certificate, the adversary cannot distinguish which eligible signer set generated it beyond unavoidable public information.

The CET multiset must be simulatable by pseudorandom field elements.

## 14.4 Cross-topic unlinkability

Tags generated by the same signer in different domains must be unlinkable.

## 14.5 Conflict extraction completeness

For two accepted certificates on conflicting messages in the same domain:

\[
\Pr[
\mathsf{ExtractConflict}
\text{ misses every member of }
S_0\cap S_1
]
\le
\operatorname{negl}(\lambda).
\]

For BFT the intersection is guaranteed nonempty and in fact has size at least \(f+1\).

## 14.6 Trace soundness

Every reported identity must correspond to a signer that actually contributed to both certificates.

## 14.7 Non-frameability / exculpability

An adversary must not be able to create two accepted certificates that cause tracing to an honest validator that did not contribute to both.

## 14.8 Joint security

Adding CET tags must not weaken the underlying threshold-ring proof.

## 14.9 Post-exposure safety

Exposure of a tracing secret must not enable ordinary consensus signature forgery.

Future-domain framing after trace-secret exposure must be prevented by validator removal/re-keying or forward-secure trace-secret evolution.

---

# 15. Reduction shape

The final theorem should have a form similar to:

\[
\boxed{
\begin{aligned}
\operatorname{Adv}^{CE\text{-}QS}
\le{}&
\operatorname{Adv}^{TRS}_{forge}\\
&+
\operatorname{Adv}^{ZK}_{sound}\\
&+
q\operatorname{Adv}^{PRF}\\
&+
\operatorname{Adv}^{Hash}_{preimage/collision}\\
&+
\operatorname{Adv}^{TraceFrame}.
\end{aligned}
}
\]

Extraction completeness itself is mostly combinatorial once proof soundness guarantees that the public tag multiset corresponds to the hidden quorum.

---

# 16. Remaining technical risks

## 16.1 Multi-prover proof integration

The combiner does not know every signer's private witness.

The PQ threshold-ring scheme must support distributed contributions while proving the CET relation.

This is the most immediate construction task.

## 16.2 CET post-quantum proof

The simple linear tag above needs a formal pseudorandomness and non-frameability theorem against quantum adversaries.

It should be compared directly with DAPT, DAPS/PAPS and RLN rather than treated as self-evidently secure.

## 16.3 Trace-secret exposure

The first conflict reveals a tracing secret.

The validator should be immediately removed from future signing domains, or a forward-secure trace-token design must replace the static \(x_i\).

## 16.4 Same-message leakage

Deterministic tags may reveal linkability between duplicate signatures.

The anonymity definition must explicitly permit or prohibit this.

## 16.5 Proof size

The certificate is only truly useful if the PQ threshold-ring/ZK component remains substantially smaller than the former accountability sidecar.

## 16.6 ROM/QROM

The first milestone may be ROM-style, but the intended final claim is quantum-adversary security including the actual Fiat-Shamir/QROM model of the chosen VOLE-in-the-Head proof.

---

# 17. Second-stage route toward asymptotically smaller certificates

Once the \(O(q)\)-tag construction is secure, investigate compressing the anonymous tag multiset.

Relevant schools:

- TAPS quorum confirmation;
- LWE traitor tracing / fingerprinting codes;
- set-intersection sketches;
- polynomial/BCH set reconciliation;
- functional commitments;
- succinct ZK aggregation.

The right abstract subproblem is:

## Conflict Intersection Sketch (CIS)

Find algorithms

\[
\mathsf{Sketch}(S,\tau,M)
\]

and

\[
\mathsf{PairDecode}(C_0,C_1)
\]

such that:

1. one sketch hides \(S\);
2. two conflicting sketches reveal one member of \(S_0\cap S_1\);
3. sketch size is \(o(q)\), ideally \(O(\lambda+\log n)\);
4. no permanent tracing authority exists;
5. maliciously chosen quorum sets cannot evade extraction.

A secure CIS would replace the \(q\) CET tags and would be the missing component for a genuinely succinct CE-QC.

---

# 18. Prior-art boundary

The broad search found:

- classical traceable threshold ring signatures;
- post-quantum threshold ring signatures;
- post-quantum traceable single-signer ring signatures;
- post-quantum DAPS/PAPS;
- private accountable threshold signatures;
- lattice traitor tracing;
- rate-limit/double-spend tracing.

It did **not** locate a published scheme that combines:

\[
\boxed{
\text{PQ hidden }t\text{-of-}n
+
\text{public conflict-only identity extraction}
+
\text{no external tracer}
+
\text{no sidecar}
}
\]

in the fixed-committee BFT shape proposed here.

This is a research-literature conclusion, not a patent novelty opinion.

---

# 19. Immediate experimental program

1. Implement the CET algebra in isolation.
2. Generate random \(n=64,q=43\) quorums.
3. Verify all common signers are extracted from conflicting tag multisets.
4. Verify different topics produce no matches.
5. Mutation-test:
   - reuse wrong mask;
   - duplicate signer within a quorum;
   - forged tag;
   - one signer absent from second quorum;
   - challenge collision.
6. Extend a VOLE-in-the-Head threshold-ring prototype relation with CET output.
7. Measure:
   - final proof bytes;
   - tag bytes;
   - signing contribution bytes;
   - aggregation latency;
   - verification latency;
   - conflict tracing latency.
8. Compare against Target A's compact QC + ~139 KiB ML-DSA-65 sidecar.

---

# 20. Current conclusion

The broad prior-art search changes the status of Target B.

The problem is no longer best described as:

> "We need to invent threshold traceability from scratch."

Classical threshold traceability already exists, and post-quantum hidden-threshold signing already exists separately.

The narrower missing link is:

\[
\boxed{
\textbf{a post-quantum anonymous DAPT/CET tag integrated into a fixed-ring threshold proof.}
}
\]

For the current \(n\le64\) BFT target, the most credible first construction is therefore an \(O(q)\)-tag, sidecar-free certificate:

\[
\boxed{
\Sigma=(\text{PQ threshold-ring proof},\ 43\text{ anonymous CET tags})
}
\]

with approximately **1.344 KiB of trace-tag payload** plus the PQ threshold-ring proof.

Two conflicting valid certificates deterministically contain tags from at least \(f+1\) common signers, and the tag algebra extracts those signer identities.

This is not yet a proved post-quantum cryptographic primitive, but it is now a substantially more concrete construction target than the original TTS sketch and it links directly to specific, existing cryptographic mechanisms rather than speculative threshold-signature leakage.
