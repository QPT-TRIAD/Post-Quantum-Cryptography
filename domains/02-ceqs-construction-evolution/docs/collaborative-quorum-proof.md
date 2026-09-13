# CE-QS v1.4 — Collaborative Quorum-Proof Compression
## One Final PQ Proof from Distributed Validator Secrets

**Status:** proof continuation from v1.3.  
**Date:** 2026-09-09.  
**Track:** hidden-signer Target \(B_1\).  
**Claim boundary:** v1.4 proves a generic collaborative-prover composition theorem and corrects the v1.3 anonymity hybrid. It does not claim a concrete <32-KiB proof or a production-round-optimal MPC protocol.

---

# 0. Proof correction to v1.3: public-key-conditioned LWR hybrid

v1.3's anonymity proof informally said that the fresh handle outputs:

\[
t_i,u_{i,1},\ldots,u_{i,d}
\]

could be replaced by uniform LWR-range values while leaving the registered trace public key:

\[
y_i=F_{s_i}(A)
\]

fixed.

That is stronger than ordinary multi-sample LWR pseudorandomness and was not separately assumed.

The proof can be repaired without adding a new assumption.

---

# 1. Correct multi-user LWR anonymity hybrid

For validator \(i\), define its complete wPRF sample bundle:

\[
\mathcal B_i
=
\left(
(A,y_i),
(B_j,t_i),
(\widehat B_{j,1},u_{i,1}),
\ldots,
(\widehat B_{j,d},u_{i,d})
\right).
\]

All input matrices are independent uniform CRS samples.

Under QLWR with polynomially many samples under one secret, the complete bundle:

\[
\mathcal B_i
\]

is indistinguishable from:

\[
\mathcal U_i
=
\left(
(A,U_{i,0}),
(B_j,U_{i,1}),
\ldots,
(\widehat B_{j,d},U_{i,d+1})
\right)
\]

with independent uniform output-range elements.

For signer anonymity, replace one **whole validator bundle at a time**, including the registry trace key.

Since validators use independent trace secrets, a hybrid over the \(N\) registry identities gives total loss at most:

\[
N\epsilon_{\rm QLWR}.
\]

In the all-uniform hybrid, every registered trace key and every challenge handle component is identity-independent.

The challenge bit therefore disappears.

Reverse the hybrids if needed.

Thus the conservative corrected bound is:

\[
\boxed{
Adv_{\rm Anon}^{QPT}
\le
\epsilon_{\rm ZK}
+
N\epsilon_{\rm QLWR}
+
\epsilon_{\rm HandleColl}.
}
\]

For the reference committee:

\[
N=64.
\]

This replaces the under-justified "fixed public key + fresh-output replacement" sentence in v1.3.

The main v1.3 theorem remains structurally unchanged.

---

# 2. Why nested local proofs are not necessary

v1.0-v1.3 used:

\[
C_i=
(i,\sigma_i,h_i,\pi_i^T)
\]

where each validator generated a local zero-knowledge proof:

\[
\pi_i^T
\]

certifying its private trace secret and handle.

The leader then generated a second proof that it possessed \(Q\) valid local proofs.

This is constructible, but it makes the outer relation verify \(Q\) proof objects.

A different school of thought solves the distributed-witness problem directly:

\[
\boxed{
\textbf{collaborative zero knowledge}.
}
\]

The validators can jointly execute the prover algorithm for **one** NIZK while keeping their private trace witnesses distributed.

---

# 3. Collaborative NIZK compiler theorem

Recent collaborative-NIZK work formalizes the following generic fact.

Let:

\[
\mathsf{NIZK}
=
(KeyGen,Prove,Verify)
\]

be an argument of knowledge for relation:

\[
\mathcal R.
\]

Let:

\[
\Pi_{\rm MPC}
\]

be an MPC protocol securely computing:

\[
Prove(crs,x,w)
\]

when the witness:

\[
w=(w_1,\ldots,w_s)
\]

is distributed among \(s\) parties.

If the MPC is maliciously secure-with-abort against \(t\) corrupted provers, then the distributed prover together with the ordinary NIZK verifier gives a collaborative NIZK argument of knowledge with:

- completeness;
- knowledge soundness;
- \(t\)-zero knowledge.

This statement is explicitly restated as Theorem 1 in the 2026 collaborative CP-NIZK work, following Ozdemir--Boneh.

The final proof seen by the verifier is an ordinary NIZK proof.

Therefore collaborative proving does **not** multiply public proof size by the number of provers.

---

# 4. QPT collaborative lifting theorem

### Theorem 4.1

Let the base NIZK be secure against QPT adversaries.

Let the MPC protocol securely compute the NIZK prover against QPT adversaries with abort.

Then the collaborative compiler preserves the same proof relation against QPT adversaries.

### Proof

The compiler theorem uses the MPC only to emulate the internal execution of:

\[
Prove.
\]

A malicious coalition's view is simulated by the MPC simulator.

The public proof distribution is exactly the output distribution of the underlying QPT-secure NIZK prover on the same statement/witness.

Knowledge soundness follows from the underlying NIZK extractor together with MPC correctness.

No rewinding specific to CE-QS is introduced.

Therefore any QPT-secure collaborative-MPC realization of the prover inherits the underlying proof's QPT statement.

\[
\blacksquare
\]

This theorem is conditional on the selected MPC's QPT malicious security.

---

# 5. BFT honest-majority lemma

For:

\[
N=3F+1,
\qquad
Q=2F+1,
\]

any \(Q\)-validator quorum contains at least:

\[
Q-F=F+1
\]

honest validators.

Therefore among the \(Q\) collaborative provers:

\[
\boxed{
F+1 > F.
}
\]

So the proof-generation group has a strict honest majority even when every Byzantine validator is included.

At the reference point:

\[
Q=43,
\quad
F=21,
\]

there are at least:

\[
22
\]

honest collaborative provers.

This creates a particularly natural setting for honest-majority malicious-secure MPC.

---

# 6. Collaborative CE-QS witness relation

The public statement is:

\[
X=
(
R_e,
\tau,
H(M),
Q,
E
).
\]

Let:

\[
E=(h_1,\ldots,h_s),
\qquad
s\ge Q.
\]

The distributed witness consists of one tuple per selected validator:

\[
w_j=
(i_j,\sigma_j,s_j^T)
\]

where:

- \(i_j\) is the validator index;
- \(\sigma_j\) is its ordinary PQ vote signature on \(M\);
- \(s_j^T\) is its private SCCH trace secret.

Validator \(j\) keeps:

\[
s_j^T
\]

local throughout the distributed proving protocol.

The collector may know:

\[
i_j,\sigma_j,
\]

but never learns:

\[
s_j^T.
\]

---

# 7. Collaborative CE-QS relation

Define:

\[
\mathcal R_{\rm Collab}(X;w_1,\ldots,w_s)=1
\]

iff:

### C1. Exact threshold

\[
s=|E|\ge Q.
\]

### C2. Distinct identities

\[
i_j\neq i_k
\quad
\forall j\neq k.
\]

### C3. Vote authorization

\[
Verify_A(
pk_{i_j}^A,
M,
\sigma_j
)=1
\quad
\forall j.
\]

### C4. Registered trace secret

\[
y_{i_j}
=
F_{s_j^T}(A).
\]

### C5. Correct public SCCH handle

For domain slot:

\[
r=DomainIndex(\tau),
\]

the public handle assigned to \(i_j\) satisfies the v1.3 SCCH equations under:

\[
s_j^T.
\]

### C6. Exact public-list binding

The multiset of witness-generated handles is exactly:

\[
E.
\]

The mapping from hidden identities to public handles is not revealed to the final verifier.

---

# 8. Collaborative proving protocol

Each validator first performs the ordinary crash-safe BFT vote action:

\[
Persist(VoteReservation)
<
ParticipateInCollabProof.
\]

It generates:

\[
\sigma_i=Sign_A(sk_i^A,M)
\]

and its public SCCH handle:

\[
h_i.
\]

Then the selected validators jointly execute:

\[
\Pi_{\rm MPC}
\]

to evaluate:

\[
\pi
=
NIZK.Prove(
crs,
X;
w_1,\ldots,w_s
).
\]

Final transferable certificate:

\[
\boxed{
QC_{\rm collab}
=
(
v,e,\tau,H(M),Q,E,\pi
).
}
\]

There are:

- no per-validator local NIZKs in the final object;
- no per-validator local NIZKs in the outer witness;
- no trace secrets at the collector.

---

# 9. Constructibility theorem

### Theorem 9.1

No party in the collaborative protocol needs to know the full CE-QS witness.

### Proof

Validator \(j\) supplies only its own:

\[
s_j^T.
\]

The collector supplies or broadcasts public/known contribution metadata.

The MPC computes the prover on the distributed witness.

MPC privacy guarantees that corrupted participants learn no honest:

\[
s_j^T
\]

beyond what follows from the final public proof and statement.

\[
\blacksquare
\]

This directly solves the v0.9 "central prover knows all trace secrets" failure without introducing a local-proof layer.

---

# 10. Public proof-size theorem

### Theorem 10.1

The collaborative protocol's final NIZK has exactly the public proof format of the underlying NIZK.

Therefore:

\[
\boxed{
|QC_{\rm collab}|
=
|E|
+
|\pi_{\rm base-NIZK}|
+
O(\lambda).
}
\]

There is no:

\[
Q\cdot|\pi_i^T|
\]

term.

There is also no circuit subrelation for verifying \(Q\) local proof transcripts.

The relation instead directly proves the \(Q\) SCCH equations.

This is the main compactness advantage of collaborative proving.

---

# 11. Threshold soundness theorem

### Theorem 11.1

Assume:

- collaborative NIZK knowledge soundness;
- QEUF-CMA vote signatures.

An accepted final proof implies at least:

\[
Q
\]

distinct registered vote authorizations.

### Proof

Knowledge soundness gives a distributed witness satisfying C1--C6.

C1/C2 give \(Q\) distinct validator indices.

C3 gives one valid vote signature under every corresponding registered authentication key.

Any uncompromised honest selected key that did not sign yields a QEUF forgery.

Thus:

\[
\boxed{
\epsilon_{\rm Thresh}
\le
\epsilon_{\rm CollabSound}
+
Q\epsilon_{\rm QEUF}.
}
\]

\[
\blacksquare
\]

---

# 12. Same-hidden-set theorem

The same hidden validator tuple:

\[
(i_j,\sigma_j,s_j^T)
\]

simultaneously satisfies:

- C3 vote authorization;
- C4/C5 SCCH generation.

Therefore:

\[
\boxed{
S_{\rm Vote}
=
S_{\rm Handle}.
}
\]

This replaces the earlier same-hidden-set proof via local proof verification.

---

# 13. Public anonymity theorem

The final verifier sees:

\[
E,\pi
\]

but not the selected indices.

Use:

1. collaborative NIZK zero knowledge to simulate \(\pi\);
2. the corrected multi-user QLWR hybrid from Section 1 to replace whole trace-key/handle bundles.

Then:

\[
\boxed{
Adv_{\rm Anon}^{QPT}
\le
\epsilon_{\rm CollabZK}
+
N\epsilon_{\rm QLWR}
+
\epsilon_{\rm HandleColl}.
}
\]

The collector and the collaborative provers know who participated.

The theorem is **public-observer anonymity**, not anonymity from co-provers.

---

# 14. Conflict extraction theorem

By threshold soundness, two conflicting accepted QCs have hidden signer sets:

\[
S_0,S_1
\]

with:

\[
|S_0|,|S_1|\ge Q.
\]

Hence:

\[
|S_0\cap S_1|
\ge
2Q-N
=
F+1.
\]

The same-hidden-set theorem binds the public SCCH handles to these exact signer sets.

The v1.3 trace theorem therefore reveals every common signer except with the named SCCH bad-event probability.

Thus:

\[
\boxed{
|ExtractConflict|
\ge
F+1.
}
\]

For 64/43:

\[
\boxed{
|ExtractConflict|
\ge22.
}
\]

---

# 15. Non-frameability theorem

The final blame proof uses only:

- two accepted collaborative QCs;
- public handle positions;
- the SCCH public trace verifier.

False blame implies one of:

- collaborative proof soundness failure;
- vote-signature forgery;
- SCCH extended-exculpability failure.

Thus:

\[
\boxed{
Adv_{\rm Frame}
\le
2\epsilon_{\rm CollabSound}
+
2Q\epsilon_{\rm QEUF}
+
\epsilon_{\rm SCCH-frame}.
}
\]

This is strictly simpler than the nested-proof bound because there is no separate local-proof soundness term.

---

# 16. Safety under proof-generation abort

Secure-with-abort collaborative proving is sufficient for **safety**.

If a Byzantine participant aborts:

\[
\boxed{
\text{no proof}
\Rightarrow
\text{no new valid QC}.
}
\]

An abort cannot create a conflicting accepted certificate.

Thus the cryptographic safety theorem is independent of collaborative-proof liveness.

---

# 17. Liveness problem introduced by collaborative proving

Collaborative proof generation is not free.

A malicious selected signer may abort the MPC after contributing a vote.

Therefore ordinary secure-with-abort MPC does **not** by itself guarantee BFT progress.

v1.4 separates two liveness adapters.

---

# 18. Liveness Adapter A — guaranteed-output-delivery MPC

Assume an honest-majority QPT-secure MPC protocol that realizes the collaborative prover with guaranteed output delivery after network synchrony.

Because the selected quorum has at least:

\[
F+1
\]

honest parties against at most:

\[
F
\]

corrupt parties, the honest-majority condition holds.

Then after GST, a selected quorum can complete the proof without Byzantine veto.

This is the cleanest hot-path collaborative mode.

The existence/performance of a concrete QPT MPC for the exact prover is an implementation obligation.

---

# 19. Liveness Adapter B — identifiable abort and replacement

Suppose the MPC provides **sound identifiable abort**.

On proof-generation failure, it outputs at least one cryptographically attributable participant that deviated.

Remove that participant from the candidate proving set for the current view and retry.

There are at most:

\[
F
\]

Byzantine validators.

Therefore after at most:

\[
F
\]

correctly attributable Byzantine aborts, all remaining active candidates are honest.

The committee contains exactly:

\[
N-F=Q
\]

honest validators.

Hence an all-honest quorum exists and eventually completes the collaborative proof after GST.

### Theorem 19.1

Under:

- eventual synchrony;
- sound identifiable abort;
- no false exclusion of honest validators;
- durable vote reservations;

the retry process terminates after at most:

\[
F
\]

Byzantine-attributable aborts plus ordinary timeout/view-change delays.

This is a conditional liveness theorem, not a property of bare CoNIZK.

---

# 20. Why non-identifiable abort is insufficient

If an abort reveals only:

\[
\text{"proof failed"}
\]

but not which participant caused it, an adversary can cause repeated retries involving at least one Byzantine party.

The protocol has no monotone progress measure toward the all-honest quorum.

Therefore:

\[
\boxed{
\text{secure-with-abort alone gives safety, not liveness}.
}
\]

This is the collaborative-proof analogue of CE-QS's earlier rule:

> silence is a timeout/liveness event, not public blame.

---

# 21. Two deployment modes

## Mode NI — non-interactive contributor mode

Use the v1.3 architecture:

\[
(i,\sigma_i,h_i,\pi_i^T)
\]

followed by a single-party outer proof.

Advantages:

- signer sends one self-contained contribution;
- no collaborative proof rounds;
- Byzantine signer cannot later veto proof generation after contribution.

Disadvantages:

- outer prover must verify \(Q\) local proofs;
- larger/more expensive relation.

---

## Mode CP — collaborative proof mode

Use v1.4:

\[
(i,\sigma_i,h_i)
\]

plus distributed proof generation.

Advantages:

- no local NIZK layer;
- one direct final proof;
- smaller logical relation;
- no collector access to trace secrets.

Disadvantages:

- additional interactive MPC;
- liveness needs robust or identifiable-abort machinery.

Both modes instantiate the same final CE-QS security interface.

---

# 22. Collaborative/segregated NIZK as concrete evidence

Chen--Hough--El Kassem introduce **Collaborative Segregated NIZK (CoSNIZK)** specifically so a sensitive prover can jointly generate a lattice proof with a potentially corrupt helper while keeping the sensitive secret hidden.

Their concrete post-quantum DAA construction:

- uses module-lattice assumptions plus the ISISf assumption;
- jointly creates attestations between TPM and host;
- reports a final DAA signature of about:

\[
38\text{ KB}.
\]

This is highly relevant implementation evidence for CE-QS's:

\[
\text{validators with sensitive secrets}
+
\text{collector doing heavy proving work}.
\]

It is **not** a CE-QS proof-size measurement.

At the project's 32-KiB gate, 38 KB is already above the target before adding CE-QS public conflict handles.

Therefore CoSNIZK is evidence of practical proximity, not proof that the gate is met.

---

# 23. 2026 collaborative CP-NIZK evidence

The 2026 collaborative CP-NIZK work generalizes distributed-witness proving and proves the generic compiler theorem used in Section 3.

Its implementation results use classical Groth16/Bulletproof systems, so those concrete proof sizes are not PQ evidence.

Its conceptual contribution is still useful:

- distributed provers can jointly generate one proof;
- the verifier sees the same kind of proof as a single prover would produce;
- t-zero-knowledge protects witnesses of honest provers;
- composability can dramatically reduce distributed prover overhead.

Thus it strengthens the architectural case for Mode CP while remaining non-load-bearing for PQ security.

---

# 24. Compactness evidence from adjacent PQ proof systems

## CoSNIZK / DAA

\[
\sim38\text{ KB}
\]

for one lattice DAA attestation.

Closest directly collaborative PQ benchmark found.

## Orthus

CRYPTO 2026 introduces a practical lattice proof system with sublinear verification and demonstrates a \(9\times\) verifier speedup for Falcon aggregation at \(2^{17}\) signatures.

It is a promising direct-proof backend, but the accessible abstract does not give a CE-QS proof-size number.

## Practical sublinear lattice R1CS

Nguyen--Seiler CRYPTO 2022 gives proof size scaling with square root of witness size and concrete improvement over Ligero for large circuits.

Useful backend family; not a CE-QS measurement.

## Loquat + generic SNARK

Loquat verification is SNARK-friendly at about 148K R1CS constraints per signature, but published 32-signature aggregation is:

- about 197 KB with Aurora;
- about 145 KB using recursive Fractal.

This is well above the CE-QS gate and therefore not the preferred current route.

---

# 25. TripleRing / TripleRing+ status

TripleRing is a practical Module-SIS/Module-LWE TRS family for small/medium rings and reports at least 93% shorter signatures than the then-best PQ TRS at ring size \(2^6=64\).

Its published security uses the older Fujisaki--Suzuki anonymity/tag-linkability/exculpability model.

Therefore it remains a candidate **small handle donor**, not a load-bearing SCCH implementation until the v1.1 strengthened-security adapter is proved.

TripleRing+ is accepted at ESORICS 2026 under the title:

> *Compact Post-Quantum Traceable Ring Signatures from ML-DSA*.

No technical paper sufficient to verify its proof or exact bytes was found in this pass.

It remains watchlist-only.

---

# 26. Direct relation-size reduction

Mode NI proves:

\[
Q
\]

vote verifications plus:

\[
Q
\]

local proof verifications.

Mode CP proves directly:

\[
Q
\]

vote verifications plus:

\[
Q
\]

SCCH relations.

Let:

\[
C_{\rm TagZKVerify}
\]

be the circuit cost of verifying one local proof.

Then the collaborative relation removes roughly:

\[
\boxed{
Q\cdot C_{\rm TagZKVerify}
}
\]

constraints/operations from the outer relation.

This does not automatically imply a proportional proof-size reduction for a succinct proof system.

It is nevertheless a strict relation simplification.

---

# 27. Final v1.4 theorem

### Theorem 27.1 — Collaborative CE-QS

Assume:

1. the v1.3 QPT SCCH assumptions;
2. QEUF-CMA vote signatures;
3. a QPT-secure NIZK argument of knowledge for \(\mathcal R_{\rm Collab}\);
4. a QPT malicious-secure MPC implementation of its prover protecting honest trace witnesses against at most \(F\) corrupt validators;
5. durable no-double-vote state.

Then the collaborative construction yields a:

\[
\boxed{
\text{QPT-secure, hidden-signer, sidecar-free, publicly accountable QC}
}
\]

with:

- exact threshold authorization;
- public signer anonymity;
- public conflict extraction of at least:

\[
F+1
\]

common identities;
- publicly verifiable blame;
- non-frameability.

For safety, secure-with-abort MPC is sufficient.

For liveness, additionally require either:

- guaranteed output delivery; or
- sound identifiable abort plus replacement.

The final certificate has:

\[
\boxed{
|QC|
=
|E|
+
|\pi_{\rm base-NIZK}|
+
O(\lambda)
}
\]

and contains no local NIZK proofs.

\[
\blacksquare
\]

---

# 28. What v1.4 actually closes

### Closed

- v1.3 anonymity-hybrid gap: corrected.
- central-prover knowledge of trace secrets: avoided.
- need for public/per-witness local proofs in collaborative mode: removed.
- generic collaborative soundness/privacy theorem: established conditionally.
- exact BFT honest-majority condition for collaborative proving: proved.
- abort safety/liveness distinction: explicit.
- identifiable-abort termination bound: proved conditionally.

### Still open

- concrete QPT collaborative MPC implementation and rounds;
- concrete proof bytes for \(\mathcal R_{\rm Collab}\);
- compact SCCH handle;
- <32-KiB end-to-end QC;
- strengthened TripleRing/TripleRing+ adapter;
- whether Orthus/LaZer can instantiate the direct collaborative relation efficiently.

---

# 29. Next milestone

The proof architecture is now sufficiently modular that the next work should be empirical/concrete.

Build two prototype relations with identical public statement:

### Prototype NI

v1.3 nested non-interactive relation.

### Prototype CP

v1.4 direct collaborative relation.

Measure:

- relation size;
- prover time;
- verifier time;
- final proof bytes;
- inter-validator proof-generation rounds/bytes.

The comparison will decide whether collaborative proving is worth its liveness/round complexity.

The cryptographic accountability theorem no longer depends on that choice.
