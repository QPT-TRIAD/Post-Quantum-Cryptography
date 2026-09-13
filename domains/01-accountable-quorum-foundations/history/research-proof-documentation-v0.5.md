# Post-Quantum Accountable Quorum Certificates
## Research Objective, Formal Proof Program, Design Evolution, Known Gaps, and Current Status

**Document status:** Research specification / proof-development record  
**Version:** 0.5 research record  
**Date:** 2026-09-08  
**Scope:** Post-quantum BFT quorum certification, accountability, epoch reconfiguration, threshold-signature integration, crash safety, and formal verification  
**Audience:** Cryptographers, distributed-systems researchers, protocol engineers, auditors, and formal-methods engineers

---

# 1. Executive summary

The project is trying to solve a concrete problem in Byzantine fault tolerant (BFT) systems:

> **How can a BFT validator committee obtain compact, post-quantum-secure quorum certificates without losing the accountability, reconfiguration safety, and operational properties that classical BLS-based systems obtain from compact aggregate or threshold signatures?**

The project currently has two related research targets.

The **deployable target** is a two-layer post-quantum accountable quorum-certificate system. A compact threshold signature is used on the consensus hot path, while individually attributable post-quantum evidence is retained outside the compact certificate and later cryptographically anchored. This design is intended to give practical compactness while preserving public blame evidence when accountability is needed.

The **frontier cryptographic target** is stronger:

> **A compact post-quantum quorum signature from which a conflicting signer can be extracted directly from two conflicting compact certificates, without retrieving an O(n)-scale accountability sidecar.**

The current work does **not** solve the second problem. It deliberately separates the two.

The central achievement of the proof work so far is not a new lattice signature. It is a progressively tightened **composition theorem** showing that a post-quantum threshold primitive can safely replace an ideal BFT quorum-certificate primitive if the exact security, state-management, epoch-transition, and evidence assumptions are satisfied.

The proof has gone through several revisions because many assumptions that initially looked like generic negligible cryptographic terms turned out to be concrete engineering or literature gaps. The revisions have therefore repeatedly narrowed claims, separated theorem obligations, and removed self-inflicted protocol complexity.

The most important remaining cryptographic gaps are:

1. **QROM security for the selected fast threshold-signature primitive.**
2. **A fully discharged concrete DKG theorem matching the exact implementation.**
3. **Concrete parameter/security-budget validation for the actual deployment lifetime and query counts.**
4. **Machine-checked refinement from the validator implementation to the formal state machine.**

The strongest still-open research goal is the compact conflict-extractable post-quantum quorum signature itself.

---

# 2. The original systems problem

Classical BFT systems can use compact aggregate or threshold signatures to compress many validator votes into a small quorum certificate. The canonical experience is:

\[
\{\sigma_i\}_{i\in Q}
\longrightarrow
\sigma_Q
\]

where \(\sigma_Q\) proves that a quorum authorized one proposal without carrying every individual signature.

Post-quantum signatures change this tradeoff. Individual lattice signatures are much larger, and general-purpose post-quantum multisignatures and threshold signatures are still a rapidly developing research area.

If a protocol simply concatenates individual post-quantum signatures, then quorum certificates grow approximately linearly in the number of signers:

\[
|\mathrm{QC}_{\mathrm{concat}}|
\approx
q\cdot |\sigma_{\mathrm{individual}}|.
\]

For a committee of \(n=64\) with a conventional BFT quorum

\[
q=43,
\]

even a few-kilobyte signature creates a certificate in the hundreds-of-kilobytes range before protocol metadata. At larger committee sizes this becomes increasingly expensive.

The research problem is therefore not merely "use post-quantum signatures." The required conjunction is closer to:

\[
\boxed{
\begin{aligned}
&\text{post-quantum security}\\
+{}&\text{small quorum certificates}\\
+{}&\text{low online round complexity}\\
+{}&\text{large committees}\\
+{}&\text{public accountability}\\
+{}&\text{safe reconfiguration}\\
+{}&\text{robust abort handling}\\
+{}&\text{crash-safe state management}\\
+{}&\text{practical verification and networking}.
\end{aligned}}
\]

No currently selected construction is assumed to satisfy all of these automatically.

---

# 3. What we are trying to build

The current practical architecture has five layers.

## 3.1 Compact consensus authorization

The BFT hot path uses a threshold-signature certificate:

\[
F=(M,\sigma)
\]

where:

- \(M\) is one canonical consensus statement;
- \(\sigma\) is a post-quantum threshold signature.

The threshold signature is intended to replace the ideal "quorum certificate" object in the underlying consensus proof.

The compact certificate itself does not need to expose every signer identity.

---

## 3.2 Individually attributable evidence

Validators also produce individually verifiable accountability receipts:

\[
\eta_i
=
\mathsf{Sign}_{sk_i^I}
\left(
\operatorname{enc}
(\texttt{PQ-EVID-V1},i,M)
\right).
\]

A sidecar contains at least a quorum of these receipts:

\[
E=
\{(i,\eta_i)\}_{i\in S},
\qquad
|S|\ge 2f+1.
\]

The evidence sidecar is committed by a Merkle root:

\[
C=\operatorname{MerkleRoot}(E).
\]

The purpose of the sidecar is not to make every normal consensus message large. It is to retain enough public evidence to prove which identities signed if conflicting accountable certificates later appear.

---

## 3.3 Evidence anchoring

A root generated only by a leader is insufficient, because the leader could commit to unavailable or invalid evidence.

Therefore honest validators vote to anchor evidence only after they have retrieved and verified it:

\[
\mathsf{AnchorVote}_i(C)
\Longrightarrow
\mathsf{HaveEvidence}_i(C).
\]

This produces the key invariant:

\[
\boxed{
\text{EvidenceBeforeAnchor}.
}
\]

Once an anchor quorum is formed, at least \(f+1\) honest validators must have possessed the evidence.

---

## 3.4 Finalized epoch barrier

Cross-epoch pipelining created a large and unnecessary proof surface because live locks, prepared certificates, and views would have to be translated between validator configurations.

The current design removes that requirement.

An epoch change occurs only after a unique terminal block has reached ordinary consensus finality:

\[
B_e^\dagger.
\]

The boundary is a **drained barrier**:

\[
\boxed{
\text{finalize terminal block}
\rightarrow
\text{post-finality seal}
\rightarrow
\text{activate next epoch}.
}
\]

No live prepare or lock state crosses the epoch boundary.

The new epoch starts from the finalized state root and the complete next public configuration embedded in the boundary.

---

## 3.5 Crash-safe stateful signing

Threshold schemes with preprocessing introduce state that may be dangerous to reuse.

Each preprocessing record follows a monotonic state machine:

\[
Unused
\rightarrow
Reserved(sid)
\rightarrow
Emitted(sid)
\rightarrow
Burned
\]

or:

\[
Unused
\rightarrow
Reserved(sid)
\rightarrow
Burned.
\]

There is no transition back to `Unused`.

Vote state, preprocessing reservation, epoch sealing, evidence possession, and epoch activation must all be made durable before corresponding externally visible signatures or votes are sent.

---

# 4. Two different research targets must not be conflated

## 4.1 Target A: practical accountable PQ quorum certification

This is the system currently being proven.

Desired interface:

\[
\boxed{
\text{compact threshold QC}
+
\text{external accountability evidence}
+
\text{cryptographic evidence binding}.
}
\]

The accountability evidence may be larger than the hot-path QC.

This is fundamentally a systems/cryptographic-composition result.

---

## 4.2 Target B: compact conflict-extractable PQ quorum signature

This is the stronger frontier primitive.

Given two compact certificates

\[
\sigma_0,\sigma_1
\]

on conflicting statements

\[
M_0,M_1,
\]

we want:

\[
\boxed{
\mathsf{ExtractConflict}
(M_0,\sigma_0,M_1,\sigma_1)
\rightarrow
(i,\pi_i)
}
\]

such that:

\[
\mathsf{VerifyBlame}
(M_0,\sigma_0,M_1,\sigma_1,i,\pi_i)=1.
\]

The normal certificate should remain compact and should not have to encode the complete arbitrary signer set.

This would be a genuinely new cryptographic result if achieved with strong practical properties.

**Current status:** open.

The current sidecar construction does not solve this.

---

# 5. Information-theoretic pressure on accountability

If a self-contained certificate must reveal the exact subset of \(t\) signers among \(n\) validators, it must distinguish among

\[
\binom nt
\]

possible signer subsets.

Therefore it needs at least:

\[
\boxed{
\log_2 \binom nt
}
\]

bits merely to encode the exact signer-set choice in the worst case.

This explains an important design decision:

> normal consensus does not necessarily need full signer-set disclosure; full attribution may be deferred until accountability is required.

This does not prove a compact conflict-extractable scheme exists. It explains why weakening the happy-path attribution requirement is a rational direction.

---

# 6. Current threat model

The current v1 theorem is deliberately narrower than the eventual desired system.

## 6.1 Committee

\[
n=3f+1.
\]

For the first implementation target:

\[
n\le64.
\]

The voting model is equal-seat, not stake-weighted.

---

## 6.2 Byzantine corruption

Within one epoch:

\[
c\le f.
\]

The principal theorem assumes static corruption during the epoch.

Different validator subsets may be corrupt in different epochs only if old threshold shares and one-time signing material are securely retired.

Fully adaptive/mobile corruption is not claimed.

---

## 6.3 Network

Safety does not require synchrony.

Liveness assumes eventual synchrony / partial synchrony.

Silence is never cryptographic blame evidence.

A missing validator message causes only:

\[
\text{timeout / view change}.
\]

A signed but cryptographically invalid share may create blame evidence.

---

## 6.4 Quantum adversary boundary

The system is intended for post-quantum security.

However, the precise random-oracle model matters.

A threshold proof in the classical random-oracle model does **not** automatically establish security in the quantum random-oracle model.

The system theorem therefore distinguishes:

- **ROM instantiation**, currently supported by the selected published threshold result;
- **QROM instantiation**, still an open primitive-level obligation for the fast threshold adapter.

---

# 7. Core quorum arithmetic

For:

\[
n=3f+1
\]

and:

\[
q=2f+1,
\]

any two quorums \(S_0,S_1\) satisfy:

\[
\begin{aligned}
|S_0\cap S_1|
&\ge
|S_0|+|S_1|-n\\
&\ge
(2f+1)+(2f+1)-(3f+1)\\
&=
f+1.
\end{aligned}
\]

Therefore:

\[
\boxed{
|S_0\cap S_1|\ge f+1.
}
\]

Since at most \(f\) validators are Byzantine, two literal \(2f+1\)-signer evidence quorums share at least one honest validator.

This is a deterministic combinatorial fact, not a post-quantum property.

---

# 8. Correct compact-QC abstraction

An earlier version treated a valid compact threshold signature as though it directly exposed a known set of \(2f+1\) signers.

That was too strong.

The current proof uses the actual threshold-security support notion.

Let:

\[
T=2f+1
\]

and let the adversary control:

\[
c\le f
\]

participants.

For a threshold signature satisfying the required strong unforgeability/support game, an accepted nontrivial threshold signature must have received valid partial-signature support from at least:

\[
T-c
\]

honest participants for one common signing request, except with the threshold forgery advantage.

Thus:

\[
\boxed{
|\mathsf{HonestSupport}(F)|
\ge
T-c
\ge
f+1.
}
\]

This is the correct load-bearing interface.

---

# 9. Honest-support intersection for conflicting compact QCs

Let:

\[
H_0=\mathsf{HonestSupport}(F_0)
\]

and:

\[
H_1=\mathsf{HonestSupport}(F_1).
\]

The total honest population is:

\[
n-c.
\]

Each honest support set has size at least:

\[
T-c.
\]

Therefore:

\[
\begin{aligned}
|H_0\cap H_1|
&\ge
2(T-c)-(n-c)\\
&=
2T-n-c\\
&=
2(2f+1)-(3f+1)-c\\
&=
f+1-c.
\end{aligned}
\]

Because:

\[
c\le f,
\]

we obtain:

\[
\boxed{
|H_0\cap H_1|\ge1.
}
\]

Therefore two conflicting compact QCs require at least one honest participant to support both conflicting signing requests, unless the threshold primitive's security property fails.

Combined with the honest vote-once invariant, this is the bridge from threshold-signature security to BFT safety.

---

# 10. Canonical consensus messages

Every signed message must contain an unambiguous domain.

A representative canonical message contains:

\[
\begin{aligned}
M=\operatorname{enc}(&
\texttt{PQ-CONSENSUS-V1},\\
&sid,\\
&chainID,\\
&epoch,\\
&height,\\
&view,\\
&phase,\\
&H(block),\\
&H(parent),\\
&H(activeSet),\\
&previousEvidenceRoot).
\end{aligned}
\]

The exact encoding must be injective.

For v1, fixed-width fields are preferred over permissive serialization formats.

Unknown fields, trailing bytes, noncanonical integers, and alternate encodings of the same semantic object must be rejected.

---

# 11. Session identifiers

Threshold-signature sessions need explicit domain separation.

A session identifier can be derived as:

\[
sid=
H_{\rm sid}
(
\texttt{TS-SESSION-V1}
\|
chainID
\|
epoch
\|
height
\|
view
\|
phase
\|
H(block)
\|
H(activeSet)
\|
batchID
).
\]

The active-set digest is included because the threshold security experiment and the consensus protocol must agree on which signer set / session context is being authenticated.

No signer-specific value that differs across validators may be inserted into the common message unless the threshold primitive is explicitly designed for that structure.

---

# 12. Accountability receipts

Each signer creates an independently verifiable receipt:

\[
\eta_i
=
\mathsf{Sign}_{sk_i^I}
(
\operatorname{enc}
(
\texttt{PQ-EVID-V1},
i,
M
)).
\]

If an accepted evidence set contains an honest validator that did not produce its receipt, then the adversary has forged that validator's individual signature.

Hence:

\[
\boxed{
\operatorname{Adv}^{EvidenceFrame}
\le
\operatorname{Adv}^{MU-QEUF}_{ID}.
}
\]

This is distinct from threshold-signature security.

---

# 13. Malformed share versus silence

A major proof correction was distinguishing non-response from provable malformed behavior.

The network is partially synchronous. Therefore:

\[
\boxed{
\text{absence of a message is not public cryptographic evidence}.
}
\]

The only safe interpretation is:

\[
\text{non-response}\rightarrow\text{timeout}.
\]

A share can be publicly blamed only if the signer authenticated the share envelope.

For example:

\[
X_i=
\operatorname{enc}
(
\texttt{PQ-TS-SHARE-V1},
i,
sid,
H(M),
H(preprocessingContext),
H(\rho_i)
)
\]

and:

\[
\zeta_i=
\mathsf{Sign}_{sk_i^I}(X_i).
\]

An invalid-share proof contains the authenticated envelope and the invalid partial share.

A malicious leader cannot turn a dropped message into a slashable offense.

---

# 14. Evidence binding

A Merkle root:

\[
C=\operatorname{MerkleRoot}(E)
\]

commits to the sidecar.

For a conservative quantum collision margin, the design currently uses a 384-bit commitment output.

The motivation is the generic quantum collision-search scaling of approximately:

\[
2^{m/3}
\]

for an \(m\)-bit idealized collision target.

Thus:

\[
m=384
\]

gives a conservative generic target around:

\[
2^{128}.
\]

This does not replace scheme-specific cryptanalysis. It is a generic hash-output sizing policy.

---

# 15. Evidence-before-anchor theorem

An honest anchor voter must retrieve, verify, and persist the complete evidence sidecar before voting for its root.

The invariant is:

\[
\boxed{
AnchorVote_i(C)
\Longrightarrow
HaveEvidence_i(C).
}
\]

If an anchor certificate contains:

\[
2f+1
\]

votes, at least:

\[
f+1
\]

of those voters are honest.

Therefore at the moment the anchor certificate is formed:

\[
\boxed{
\text{at least }f+1\text{ honest validators possess the sidecar}.
}
\]

This is an availability fact at the time of anchoring.

Long-term retrievability additionally depends on storage and network assumptions.

---

# 16. Why cross-epoch pipelining was removed

The first version of the epoch proof tried to carry arbitrary live protocol state into the next committee:

- locks;
- prepared certificates;
- current view;
- partially formed QCs;
- uncommitted candidates.

That created a large proof obligation with protocol-specific semantics.

The current v1 design removes the problem by requiring:

\[
\boxed{
\text{reconfiguration only at a finalized barrier}.
}
\]

The tradeoff is intentional:

- **cost:** no pipelined reconfiguration across the epoch boundary;
- **benefit:** clean, finite safety proof.

---

# 17. Terminal epoch block

The current epoch finalizes a special terminal block:

\[
B_e^\dagger.
\]

It contains:

\[
\boxed{
\begin{aligned}
B_e^\dagger = (&
e,\\
&h_e,\\
&stateRoot_e,\\
&Config_{e+1},\\
&Setup_{e+1},\\
&accountabilityFrontier_e).
\end{aligned}}
\]

`Config_{e+1}` is embedded directly rather than merely referenced by an unavailable hash preimage.

The boundary is rare enough that a larger object is an acceptable tradeoff.

---

# 18. Self-contained next configuration

The next public configuration is canonical and contains all public activation material, for example:

\[
Config_{e+1}
=
[
Entry_1,\ldots,Entry_{n'}
]
\]

with entries containing fields such as:

\[
(
seat_i,
identityPK_i,
transportPK_i,
thresholdShareVK_i,
endpoint_i
).
\]

The threshold setup descriptor contains:

\[
(
PK^{TS}_{e+1},
setupMode,
setupTranscriptDigest
).
\]

Private threshold shares are not embedded.

A validator may activate only if its private share is locally ready and consistent with the public setup descriptor according to the selected threshold primitive.

---

# 19. Finalize first, seal second

An earlier seal design risked deadlock if honest validators sealed while consensus was still trying to decide which terminal block should win.

That was corrected.

The current sequence is:

\[
\boxed{
\text{ordinary BFT finality}
\rightarrow
\text{post-finality irreversible seal}
\rightarrow
\text{seal certificate}
\rightarrow
\text{next-epoch activation}.
}
\]

Validators do not seal merely because they voted for a terminal proposal.

They seal only after seeing proof that one terminal block is already finalized.

This is crucial.

---

# 20. Seal state

Once validator \(i\) sees a valid finality proof for \(B_e^\dagger\), it atomically persists:

\[
\mathsf{Sealed}_i(e,H(B_e^\dagger)).
\]

It then signs a seal acknowledgment:

\[
\eta_i^{seal}
=
\mathsf{Sign}_{sk_i^I}
(
\operatorname{enc}
(
\texttt{EPOCH-SEAL-V1},
e,
H(B_e^\dagger),
H(FinalityProof_e)
)).
\]

The state is irreversible.

A sealed validator may retransmit the same persisted acknowledgment.

It may never produce a different seal for the same epoch.

---

# 21. Post-seal partition recovery

A network partition may occur after some validators have sealed but before the seal certificate has been assembled.

This does not threaten safety because the terminal block was already finalized before sealing began.

After eventual synchrony:

1. all honest validators learn the same finalized boundary;
2. already-sealed validators retransmit their persisted acknowledgments;
3. unsealed honest validators seal the same boundary;
4. the collector eventually obtains at least \(2f+1\) honest-compatible seal acknowledgments.

Thus:

\[
\boxed{
\text{partial sealing can delay activation but does not permanently deadlock it under eventual synchrony}.
}
\]

This is a liveness theorem conditioned on eventual synchrony and durable seal storage.

---

# 22. Boundary certificate

The boundary object is self-contained:

\[
BC_e=
(
B_e^\dagger,
FinalityProof_e,
S_e
)
\]

where:

\[
S_e=
\{(i,\eta_i^{seal})\}
\]

and:

\[
|S_e|\ge2f+1.
\]

Boundary verification checks:

1. the old epoch's finality proof;
2. canonical boundary serialization;
3. full embedded next public configuration;
4. at least \(2f+1\) distinct seal identities;
5. every seal signature;
6. every seal refers to the exact same finalized boundary and finality proof.

---

# 23. Boundary uniqueness

Suppose two conflicting boundary certificates both verify.

Each contains at least:

\[
2f+1
\]

seal identities.

Their signer sets intersect in at least:

\[
f+1.
\]

At most \(f\) are Byzantine.

Therefore at least one honest validator would have had to seal two different finalized boundaries.

This contradicts the seal invariant unless:

- an identity signature was forged;
- persistent state rolled back;
- or the underlying consensus finality theorem already failed.

Thus:

\[
\boxed{
\operatorname{Adv}^{BoundaryFork}
\le
\operatorname{Adv}^{MU-QEUF}_{ID}
+
\epsilon_{\rm rollback}
+
\operatorname{Adv}^{BaseSafety}.
}
\]

---

# 24. New epoch activation

An honest validator activates epoch \(e+1\) only if:

\[
\mathsf{VerifyBoundary}(BC_e)=1.
\]

It validates the full public configuration embedded in the boundary.

It verifies that:

\[
PK^{TS}_{local}=PK^{TS}_{e+1}.
\]

It verifies:

\[
\mathsf{ShareReady}_i(e+1)=true.
\]

It then durably records:

\[
Genesis_{e+1}=H(B_e^\dagger)
\]

and:

\[
epoch_i=e+1.
\]

Only after those writes may it send its first new-epoch vote.

---

# 25. Old messages become inert

The protocol does not pretend that old signatures disappear.

Instead:

\[
\boxed{
epoch(M)\ne epoch_i
\Longrightarrow
M\text{ cannot alter safety state}.
}
\]

A stale old-epoch QC can remain historically valid.

It cannot:

- change a lock;
- reserve a vote;
- consume new preprocessing;
- alter finality;
- modify the new epoch's state.

This is a protocol admission rule rather than a cryptographic erasure claim.

---

# 26. Cross-epoch safety theorem

Every valid block in epoch \(e+1\) must descend from:

\[
B_e^\dagger.
\]

Thus:

\[
B_e^\dagger\preceq B.
\]

If epoch \(e\) is safe, the boundary is unique, and epoch \(e+1\) is internally safe, no committed block in \(e+1\) can conflict with a committed block in \(e\).

By induction across epochs:

\[
\boxed{
\text{all honest committed histories remain prefix-compatible}.
}
\]

This closes the generic cross-epoch safety proof for the drained-barrier v1 design.

---

# 27. Preprocessing state machine

For each preprocessing object \(p\):

\[
Prep[p]\in
\{
Unused,
Reserved(sid),
Emitted(sid),
Burned
\}.
\]

Permitted transitions are:

\[
Unused
\rightarrow
Reserved(sid)
\rightarrow
Emitted(sid)
\rightarrow
Burned
\]

and:

\[
Unused
\rightarrow
Reserved(sid)
\rightarrow
Burned.
\]

No transition goes backward.

Crash recovery conservatively maps:

\[
Reserved\rightarrow Burned
\]

and:

\[
Emitted\rightarrow Burned
\]

unless the implementation can prove safe idempotent recovery of the identical session.

---

# 28. Preprocessing non-reuse invariant

The invariant is:

\[
\boxed{
\forall p,\ sid_0\ne sid_1:
\neg(
Used(p,sid_0)\land Used(p,sid_1)
).
}
\]

Because only `Unused` records may become reserved and no later state returns to `Unused`, one preprocessing object cannot become associated with two session IDs in the abstract machine.

This is a state-machine theorem, not a lattice-hardness assumption.

---

# 29. Vote-once state

For domain:

\[
d=(e,h,v,\phi),
\]

the validator stores:

\[
VoteLog_i[d].
\]

Before sending a threshold share, it persists the message identity.

A later request in the same conflict domain succeeds only if it refers to the same canonical message.

Therefore:

\[
\boxed{
Vote_i(M_0,d)\land Vote_i(M_1,d)
\Rightarrow
M_0=M_1
}
\]

except under persistent rollback or a collision in whatever digest is used in the durable log.

---

# 30. Required durable ordering

The implementation proof depends on five critical ordering requirements.

## Vote

\[
\boxed{
Persist(VoteReservation)
<
Send(SignatureShare).
}
\]

## Preprocessing

\[
\boxed{
Persist(PrepReserved)
<
Use(Prep)
<
Send(Share).
}
\]

## Evidence

\[
\boxed{
Persist(Evidence)
<
Send(AnchorVote).
}
\]

## Seal

\[
\boxed{
Persist(Seal)
<
Send(SealAck).
}
\]

## Activation

\[
\boxed{
Persist(NewEpochGenesis)
<
Send(FirstNewEpochVote).
}
\]

If software violates these orderings, the paper proof may remain mathematically correct while no longer applying to the implementation.

---

# 31. Query-budget problem

A concrete threshold theorem may support a bounded number of signing and random-oracle queries.

Therefore the deployment must track a signing-session budget.

Let:

\[
Counter_e
\]

count started threshold sessions.

Require:

\[
Counter_e
\le
Q_{\rm Sign}^{deploy}
<
Q_{\rm Sign}^{proof}.
\]

If the deployment reaches its configured hard cap, the safe response is:

\[
\boxed{
\mathsf{SafeHalt}.
}
\]

Liveness may stop.

The implementation must not silently exceed the theorem's query regime.

This turns a hidden proof-assumption violation into an explicit operational state.

---

# 32. Preprocessing exhaustion

Finite preprocessing creates a resource-liveness condition.

Let:

\[
R_i(t)
\]

be the number of unused records at validator \(i\).

A signing round can proceed without Byzantine help when:

\[
\left|
\{i\in H:R_i(t)>0\}
\right|
\ge2f+1.
\]

Thus preprocessing exhaustion belongs in the liveness theorem:

\[
\boxed{
\Pr[\mathsf{LivenessFailure}]
\le
\Pr[\neg\mathsf{Synchrony}]
+
\Pr[\mathsf{PrepExhaust}]
+
\Pr[\mathsf{StorageFailure}]
+
\epsilon_{\rm TS-correctness}.
}
\]

The first three terms are operational probabilities, not cryptographic negligibles.

---

# 33. Static corruption boundary

The current proof does not claim full adaptive corruption security.

Within an epoch, the corrupted set is bounded by:

\[
c\le f.
\]

A future stronger profile would require:

- proactive share refresh;
- secure erasure;
- adaptive threshold security;
- forward-secure or key-evolving accountability signatures;
- stronger treatment of compromised preprocessing.

The current v1 profile chooses proof tractability over claiming those properties prematurely.

---

# 34. Setup / DKG problem

This has been one of the largest recurring struggles.

Early proof versions wrote:

\[
\epsilon_{\rm DKG}
\]

as though a complete, matching concrete DKG theorem were already available.

That was not justified.

The current proof separates setup from signing.

The system theorem assumes a setup functionality providing:

- one common threshold public key;
- internally consistent secret shares;
- the required secrecy threshold;
- public verification material required by the threshold scheme.

The failure probability / trust term is written separately:

\[
\delta_{\rm setup}.
\]

It is **not automatically called negligible**.

A concrete DKG adapter may replace:

\[
\delta_{\rm setup}
\]

with a cryptographic advantage only after its exact security theorem matches the deployment.

---

# 35. Current Hermine adapter status

The currently studied Hermine construction is relevant because it targets small/medium threshold groups and a low-online-round signing path.

The proof record currently treats its status as follows:

- the security notion `ts-suf-2` / TS-sUF-2 has been verified in the current Hermine materials;
- the threshold signing result is presented in the random-oracle model;
- its proof uses AOM-MISIS/AOM-MSIS as an intermediate problem while grounding the security claim in standard lattice assumptions through the stated reductions;
- DKG is described in the broader project material, but the detailed ePrint proof explicitly leaves the careful DKG formalization outside the main signing proof;
- therefore the current system theorem does not silently claim that the Hermine DKG obligation has already been discharged;
- full QROM threshold security remains a separate problem.

This adapter is replaceable. The system composition theorem should not depend permanently on Hermine.

---

# 36. Ringtail correction log

One important literature error was found and corrected during the project.

An earlier critique incorrectly associated Ringtail with a new algebraic one-more Module-LWE assumption.

The published Ringtail result instead states its security from standard LWE in the random-oracle model and contrasts itself with contemporaneous work based on newer assumptions.

This mattered because the assumption ledger is load-bearing. A scheme's hardness foundation cannot be summarized from memory or adjacent related-work citations.

**Lesson:** every primitive row in the assumption ledger must be derived from the exact primary theorem used by the implementation.

---

# 37. Hermine assumption correction log

Another correction occurred when the Hermine proof basis was initially described inconsistently.

The refined statement is:

> Hermine's stated security foundation is standard lattice hardness under the paper's reductions, with AOM-MISIS/AOM-MSIS appearing as an intermediate problem invoked by its unforgeability proof.

This is different from saying:

> Hermine assumes AOM-MISIS as an unrelated, independent new trust foundation.

That distinction was retained in the current documentation.

---

# 38. Hermine DKG correction log

The DKG description also required refinement.

Several formulations were considered and rejected:

1. "Hermine has fully proved DKG" — too strong for the detailed paper currently relied upon.
2. "Hermine is simply a trusted-dealer design" — also too simplistic because DKG is described as an intended/proposed component in the broader material.
3. **Current wording:** a DKG mechanism is described in project material, while the detailed signing paper leaves its careful DKG security formalization outside the main contribution; therefore the concrete DKG proof obligation is not marked discharged.

This is the wording that should remain until a matching formal DKG theorem is available and audited.

---

# 39. ROM/QROM struggle

This issue has survived several proof revisions because it cannot be eliminated through BFT bookkeeping.

A threshold signature may be post-quantum in its lattice hardness assumptions while still having only a classical random-oracle-model proof.

Those are different claims.

The system theorem therefore has two possible instantiation levels.

## ROM profile

The primitive security theorem is taken in its published ROM model.

## QROM profile

The primitive must provide the same threshold support/unforgeability guarantee when the adversary has quantum random-oracle access.

The BFT composition theorem itself does not materially change.

The primitive adapter theorem does.

This is one of the few remaining genuinely cryptographic rather than systems-level gaps.

---

# 40. Individual-signature multi-user security

Accountability uses many independent public keys across many epochs.

A conservative multi-user reduction may introduce a factor approximately proportional to the number of keys.

For:

\[
N_u=64E
\]

identity keys over \(E\) epochs:

\[
\operatorname{Adv}^{MU}
\le
N_u\operatorname{Adv}^{SU}.
\]

To keep a lifetime contribution below \(2^{-128}\):

\[
-\log_2 \operatorname{Adv}^{SU}
\gtrsim
128+\log_2(64E).
\]

This led to the recommendation that the evidence layer use a stronger parameter set than the absolute minimum security category if the deployment is long-lived.

The exact parameter set must be frozen only after the real epoch policy and lifetime key count are known.

---

# 41. Concrete-security work still required

The proof is currently dominated by asymptotic/game-based statements.

A deployable security profile must additionally fix:

- target security margin;
- actual committee cap;
- epoch lifetime;
- maximum lifetime epoch count;
- threshold signing-query budget;
- random-oracle query bounds used by the selected primitive proof;
- lattice dimensions and moduli;
- individual signature parameter set;
- hash/XOF output lengths;
- failure probabilities from rejection sampling if applicable;
- sidecar size;
- preprocessing inventory requirements.

The parameter set must then be evaluated against the best-known classical and quantum attacks using current lattice-estimation methodology.

No final parameter table has yet been frozen.

---

# 42. Formal security properties currently claimed conditionally

Under the stated primitive and system assumptions, the proof program now supports the following conditional claims.

## 42.1 Compact-QC support

Every accepted compact QC has the honest threshold support required by the selected threshold-security game.

## 42.2 Conflicting compact-QC safety

Two conflicting accepted compact QCs imply at least one honest validator supported both conflicting signing requests unless threshold security or the honest state machine failed.

## 42.3 Vote non-equivocation

An honest validator cannot intentionally emit conflicting votes from the abstract state machine.

## 42.4 Preprocessing non-reuse

An honest validator cannot bind one one-time preprocessing object to two sessions in the abstract state machine.

## 42.5 Evidence authenticity

An honest identity cannot appear in a valid evidence sidecar without producing its receipt, except through individual-signature forgery.

## 42.6 Evidence-before-anchor

Every honest anchor signer possessed the evidence before anchoring it.

## 42.7 Boundary uniqueness

Two conflicting valid epoch boundary certificates require an honest seal violation, identity forgery, persistent-state rollback, or failure of old-epoch finality.

## 42.8 Cross-epoch safety

Every valid new-epoch chain extends the unique finalized terminal block of the prior epoch.

## 42.9 Global safety

If every epoch is safe and every boundary is unique, all committed honest histories are prefix-compatible across the lifetime of the system.

## 42.10 Post-seal recovery

A network partition after partial sealing delays activation but does not permanently prevent seal completion under eventual synchrony and durable acknowledgment retransmission.

---

# 43. What is not currently proved

The following must not be presented as finished results.

## 43.1 Full QROM security for the selected fast threshold primitive

Still open.

## 43.2 A complete concrete DKG theorem matching the selected Hermine-style deployment

Still open / adapter-dependent.

## 43.3 Fully adaptive/mobile corruption

Not claimed.

## 43.4 Production implementation conformance

Not yet machine-proved.

## 43.5 Side-channel resistance

Not part of the abstract proof.

Examples include:

- timing;
- cache behavior;
- fault injection;
- secret-dependent memory access;
- RNG failure;
- rollback at storage/hypervisor level;
- filesystem corruption.

## 43.6 Final concrete lattice-security numbers

Not frozen.

## 43.7 Constant-size conflict extraction without sidecar

Still the major frontier cryptographic target.

---

# 44. Why weighted voting was removed from v1

A weighted quorum generalization was introduced during an earlier proof version.

It increased the proof surface without being required for the current seat-based design.

The v1 theorem therefore uses equal validator seats.

Weighted voting may be added later with a separate proof covering:

- weighted intersection;
- evidence weight;
- weighted accountability;
- reconfiguration;
- threshold access structure.

Removing it is intentional proof-surface reduction.

---

# 45. Why proactive refresh was removed from v1

Proactive refresh could improve long-term adaptive security.

It also introduces additional assumptions, protocols, corruption models, refresh-query bounds, state-erasure requirements, and DKG-like complexity.

The current proof therefore uses:

\[
\boxed{
\text{fresh setup / DKG at epoch changes}
}
\]

instead of proving intra-epoch proactive refresh.

This is another intentional scope reduction.

---

# 46. Why full evidence replication is used first

Erasure coding could reduce storage and bandwidth.

It also adds another correctness/availability theorem:

\[
\text{enough fragments}
\Rightarrow
\text{reconstruct exact sidecar}.
\]

For a \(64\)-validator first implementation, the proof currently prefers full evidence retention by honest anchor voters.

This makes the evidence availability theorem much simpler.

Erasure coding can be optimized later.

---

# 47. Why the epoch configuration is embedded

An earlier design committed only:

\[
H(Config_{e+1})
\]

and implicitly assumed new validators already possessed the correct preimage.

That hid a distribution dependency inside the activation theorem.

The current design embeds the complete public configuration in the finalized boundary.

Thus the activation proof depends only on obtaining the boundary certificate itself, plus the validator's own private setup material.

This closes the public-config-distribution seam.

---

# 48. Why finalize-first/seal-second matters

An earlier design risked having honest validators irreversibly seal while the network was still trying to resolve which boundary should finalize.

A partition at that point could destroy liveness.

The corrected design waits for ordinary finality first.

Only one already-finalized terminal block is then sealed.

This turns sealing from a consensus-decision mechanism into a post-finality acknowledgment mechanism.

The distinction significantly simplifies both safety and recovery proofs.

---

# 49. Formal implementation state

The abstract validator state includes at least:

\[
State_i=
(
epoch,
votes,
preprocessing,
evidence,
sealed,
boundary,
activation
).
\]

The current TLA+ starter model represents:

- current local epoch;
- vote set;
- preprocessing usage;
- preprocessing phase;
- evidence possession;
- evidence anchor votes;
- finalized boundaries;
- seal acknowledgments;
- seal certificates;
- activated boundary.

The model currently expresses these invariants:

1. `VoteOnce`
2. `PrepNoReuse`
3. `EvidenceBeforeAnchor`
4. `SealOnlyFinalized`
5. `SealUnique`
6. `ActivationRequiresSealCert`

The model is a **starter artifact**, not a completed machine-checked proof.

TLC/TLAPS verification has not yet been completed in the current research record.

---

# 50. Formal-methods next step

The proof now needs to move from paper reasoning to machine verification.

The target refinement map is:

\[
\alpha:
ConcreteValidatorState
\rightarrow
AbstractProtocolState.
\]

The implementation proof must establish:

## Initialization

\[
Init_C(c)
\Rightarrow
Init_A(\alpha(c)).
\]

## Forward simulation

Every concrete transition:

\[
c\rightarrow_C c'
\]

must map either to an allowed abstract transition:

\[
\alpha(c)\rightarrow_A\alpha(c')
\]

or to a stuttering step:

\[
\alpha(c)=\alpha(c').
\]

## Crash refinement

A crash/recovery transition must never result in:

\[
Burned\rightarrow Unused,
\]

\[
Sealed\rightarrow Active,
\]

\[
epoch(e+1)\rightarrow epoch(e),
\]

or deletion of a committed vote reservation.

This is now the highest-value systems proof obligation.

---

# 51. Required model-checking scenarios

The finite-state model should include at least:

- \(n=4\), \(f=1\), \(q=3\);
- two competing proposals;
- stale messages;
- network partition and heal;
- crashed leader;
- crashed signer after reservation;
- crash after share generation before send;
- crash after send before cleanup;
- partial evidence availability;
- evidence anchor before/after local persistence;
- boundary finality;
- partial post-finality seals;
- partition after partial sealing;
- seal retransmission;
- stale old-epoch QC after new epoch activation;
- validator missing private setup share;
- preprocessing pool exhaustion;
- query-budget exhaustion.

The properties to assert include:

\[
\boxed{
\text{no two honest finalized histories conflict}
}
\]

and all state invariants above.

---

# 52. Docker/implementation tests required in parallel

Formal verification does not replace fault injection.

A four-node local deployment is useful for exercising the \(f=1\) boundary.

Required tests include:

- stop one validator and verify remaining three finalize;
- 2/2 partition and verify neither side finalizes;
- Byzantine dual proposal;
- stale vote delivery after view advance;
- crash exactly after durable vote reservation;
- crash exactly after preprocessing reservation;
- malformed partial share;
- evidence deletion before anchor vote;
- partition immediately after boundary finality;
- partition immediately after first seal acknowledgments;
- stale old-epoch QC after activation;
- corrupted or noncanonical encoding;
- unavailable next private share;
- query-counter safe halt;
- preprocessing safe halt.

After every scenario, compare finalized height and state root across live honest nodes.

---

# 53. Main research struggles encountered

The proof did not fail because the quorum arithmetic was difficult. The hardest parts came from assumptions hidden around it.

## 53.1 Confusing adjacent cryptographic schemes

Several lattice threshold papers are close in date, terminology, and technique.

This caused assumption attribution mistakes.

The solution was to make the **assumption ledger** load-bearing and source every row from the exact theorem used.

---

## 53.2 Treating DKG as a generic negligible term

This was one of the most serious early proof weaknesses.

A DKG is a protocol with agreement, secrecy, robustness, malicious-participant handling, and sometimes asynchronous behavior.

It cannot be replaced by the symbol:

\[
\epsilon_{\rm DKG}
\]

without specifying which theorem supplies it.

Current solution:

\[
\delta_{\rm setup}
\]

remains visibly operational/conditional until a concrete DKG theorem is selected.

---

## 53.3 Treating "post-quantum" as one security model

Lattice hardness is not identical to QROM Fiat-Shamir security.

The solution was to separate the underlying hardness assumptions from the random-oracle security model.

---

## 53.4 Hidden statefulness

Fast threshold signatures may depend on one-use preprocessing.

A consensus proof that ignores that state can be correct on paper and insecure in code.

The solution was to elevate preprocessing into the protocol state machine.

---

## 53.5 Crash semantics

"Validator signs once" is not enough if a crash can erase the record saying it already signed.

The solution was persist-before-send and monotonic durable states.

---

## 53.6 Silence versus cryptographic guilt

Network delay can look identical to omission.

The solution was to forbid slashing on absence and require signed malformed-share evidence for cryptographic blame.

---

## 53.7 Evidence availability

A Merkle root does not prove the sidecar exists.

The solution was evidence-before-anchor: honest validators sign the root only after they possess and verify the sidecar.

---

## 53.8 Cross-epoch live state

Trying to translate arbitrary in-flight locks across committees created a large proof seam.

The solution was not a stronger carry object. The solution was to eliminate the requirement through a finalized drained boundary.

---

## 53.9 Configuration preimage availability

A configuration hash is useless to a validator that lacks the configuration itself.

The solution was to embed the entire public next configuration in the boundary.

---

## 53.10 Sealing too early

Irreversibly sealing while consensus was still deciding the terminal block risked liveness deadlock.

The solution was finalize first, seal second.

---

## 53.11 Lifetime multi-user loss

Per-key security strength cannot be interpreted in isolation when a long-lived system creates many public keys across many epochs.

The solution was to make lifetime key count part of the concrete security budget.

---

## 53.12 Combining all failure probabilities into one epsilon

Safety, framing, availability, and liveness do not have identical failure semantics.

The solution was separate top-level theorems and separate bounds.

---

# 54. Proof evolution log

## v0.1 — abstract composition

Main result:

- compact threshold QC;
- evidence sidecar;
- quorum intersection;
- evidence authenticity;
- non-frameability;
- rough cross-protocol composition.

Weaknesses:

- threshold scheme abstract;
- DKG abstract;
- no preprocessing model;
- no concurrent sessions;
- no concrete epoch seam;
- all failures collapsed into generic epsilon terms.

---

## v0.2 — concrete operational profile

Added:

- named threshold candidate investigation;
- separated DKG properties;
- concurrent-session model;
- preprocessing state machine;
- malformed-share versus silence distinction;
- 384-bit commitment policy;
- full evidence retention;
- multi-user evidence accounting;
- epoch transition object.

Weaknesses discovered:

- concrete DKG still unresolved;
- exact primitive assumption wording needed correction;
- epoch carry still contained vague safety state;
- ROM/QROM remained open.

---

## v0.3 — proof/adapter split

Major structural improvement:

\[
\boxed{
\text{generic system theorem}
+
\text{replaceable primitive adapter}.
}
\]

Added:

- explicit \(\delta_{\rm setup}\);
- lifetime evidence security budget;
- malicious aggregator envelope;
- self-contained epoch seal concept;
- stateful signing theorem target.

Weakness:

- `Carry_e` still risked hiding protocol-specific live state.

---

## v0.4 — finalized epoch barrier

Major simplification:

\[
\boxed{
\text{do not translate live locks across epochs}.
}
\]

Added:

- finalized terminal block;
- epoch sealing;
- old-message inertness;
- reduced carry object;
- global safety by induction;
- concrete TLA+ invariant list.

New liveness seam:

- sealing needed explicit partition recovery;
- public configuration distribution needed to be closed.

---

## v0.5 — exact support theorem and finalized seal protocol

Added/corrected:

- exact TS-sUF-2 support abstraction;
- honest-support intersection theorem for conflicting compact QCs;
- full next public config embedded in boundary;
- finalize first, seal second;
- seal retransmission after partition;
- query-budget hard cap;
- safe halt rather than theorem-regime overflow;
- implementation refinement theorem;
- TLA+ starter artifacts.

Current status:

- generic system proof is structurally stable;
- primitive-level QROM and concrete DKG remain the major cryptographic gaps;
- implementation refinement remains the major systems-verification gap.

---

# 55. Current system-level safety theorem

Let:

\[
n=3f+1,
\qquad
T=2f+1,
\qquad
c\le f.
\]

Assume:

1. the underlying BFT state machine is safe under an ideal QC abstraction;
2. the threshold signature supplies the required strong threshold-support/unforgeability property within the deployed query bounds;
3. canonical encoding is injective;
4. identity evidence signatures are multi-user post-quantum unforgeable;
5. security-critical digests are quantum collision resistant at the selected parameterization;
6. validator vote state is durable;
7. preprocessing is single-use and durable;
8. evidence is persisted before anchor votes;
9. epoch close happens only after old-epoch finality;
10. seals are post-finality, persistent, unique, and retransmittable;
11. the complete next public configuration is authenticated by the finalized boundary;
12. new-epoch activation persists the boundary genesis before voting;
13. stale-epoch messages are inert.

Then, except through the corresponding primitive failures or implementation-state rollback:

- every accepted compact QC has the threshold theorem's required honest support;
- two conflicting compact QCs require at least one common honest supporter;
- honest vote-once behavior prevents such conflicting support;
- two conflicting audited evidence quorums expose at least \(f+1\) common identities;
- a valid epoch boundary is unique;
- every valid new-epoch history extends the unique old-epoch terminal block;
- global committed histories remain prefix-compatible by induction.

---

# 56. Top-level bounds must remain separated

## Safety

Representative form:

\[
\boxed{
\begin{aligned}
\operatorname{Adv}^{GlobalSafety}
\le{}&
\operatorname{Adv}^{BaseSafety}\\
&+
\delta_{\rm setup}\\
&+
\operatorname{Adv}^{ThresholdForge}\\
&+
\operatorname{Adv}^{HashCollision}\\
&+
\epsilon_{\rm rollback}.
\end{aligned}}
\]

The exact reduction losses and query parameters belong in the concrete primitive adapter.

---

## Framing

\[
\boxed{
\operatorname{Adv}^{Frame}
\le
\operatorname{Adv}^{MU-QEUF}_{ID}
+
\epsilon_{\rm IA}
+
\operatorname{Adv}^{HashCollision}.
}
\]

---

## Evidence availability

\[
\boxed{
\Pr[\mathsf{EvidenceUnavailable}]
\le
\Pr[\mathsf{StorageFailure}]
+
\Pr[\mathsf{PersistentEclipse}]
+
\Pr[\mathsf{DataCorruption}].
}
\]

These are operational/network properties, not all cryptographic advantages.

---

## Liveness

\[
\boxed{
\Pr[\mathsf{LivenessFailure}]
\le
\Pr[\neg\mathsf{EventualSynchrony}]
+
\Pr[\mathsf{PrepExhaust}]
+
\Pr[\mathsf{SetupUnavailable}]
+
\Pr[\mathsf{StorageFailure}].
}
\]

Again, these are not all negligible cryptographic probabilities.

---

# 57. Current research status matrix

| Area | Status | Meaning |
|---|---|---|
| BFT quorum intersection | **Closed** | Elementary combinatorial theorem |
| Compact QC threshold-support abstraction | **Conditionally closed** | Depends on selected threshold security theorem |
| Hermine `ts-suf-2` notion | **Verified in current research record** | May be used in adapter with exact theorem citation |
| Hermine ROM model | **Verified** | Does not imply QROM |
| Hermine DKG proof for exact deployment | **Open/adapter-dependent** | Do not hide inside negligible epsilon |
| Evidence authenticity | **Closed conditionally** | Depends on individual PQ signature security |
| Non-frameability | **Closed conditionally** | Depends on ID signature + IA model |
| Evidence-before-anchor | **Closed at abstract state level** | Needs implementation refinement |
| Preprocessing non-reuse | **Closed at abstract state level** | Needs implementation refinement |
| Crash-safe vote-once | **Closed at abstract state level** | Needs durable-storage refinement |
| Public config distribution | **Closed by design** | Config embedded in boundary |
| Cross-epoch live locks | **Eliminated by design** | Drained finalized barrier |
| Partial-seal partition | **Closed conditionally** | Eventual synchrony + durable retransmission |
| Boundary uniqueness | **Closed conditionally** | Base finality + ID signatures + no rollback |
| Global cross-epoch safety | **Closed conditionally** | Induction over unique barriers |
| Concrete lifetime parameter set | **Open** | Needs estimator/security-budget work |
| TLA+ finite-state checking | **Not yet executed in this record** | Starter spec exists |
| TLAPS theorem proof | **Open** | Future formal-methods task |
| Implementation refinement proof | **Open** | Highest-value systems task |
| Side-channel assurance | **Open** | Separate implementation-security program |
| Compact no-sidecar conflict extraction | **Open frontier problem** | Potential new cryptographic contribution |
| Fast threshold primitive with full QROM proof | **Open/primitive-dependent** | Major cryptographic gap |

---

# 58. What would count as "done" for the practical system

The practical two-layer construction should not be called complete until all of the following are true.

## Cryptographic completion

- exact threshold primitive selected;
- exact theorem/security game cited;
- exact setup/DKG assumption stated;
- exact ROM/QROM posture stated;
- concrete lattice parameter analysis completed;
- query bounds fixed;
- individual evidence signature parameters fixed;
- multi-user/lifetime budget checked;
- hash/XOF sizes frozen.

## Protocol completion

- canonical signed-message schema frozen;
- canonical boundary schema frozen;
- full next public config schema frozen;
- epoch activation rules frozen;
- evidence sidecar schema frozen;
- malformed-share blame object frozen;
- preprocessing state machine frozen;
- query-budget safe-halt behavior frozen.

## Formal-methods completion

- TLA+ model runs under TLC for bounded four-node scenarios;
- safety invariants checked;
- liveness assumptions modeled separately;
- TLAPS or equivalent proof of key invariants where feasible;
- refinement map from implementation state to abstract state documented;
- crash transitions proved monotonic.

## Implementation completion

- persist-before-send implemented;
- preprocessing rollback prevented;
- epoch rollback prevented;
- canonical encoding differential-fuzzed;
- malformed share tests implemented;
- evidence persistence tests implemented;
- partition/seal recovery implemented;
- safe halt on proof/query/preprocessing limits implemented;
- state root convergence checker implemented.

## External assurance

- independent cryptographic review;
- independent distributed-systems audit;
- formal-methods review;
- side-channel/constant-time review;
- chaos testing;
- adversarial fuzzing;
- published reproducible benchmarks.

---

# 59. What would count as a genuinely new cryptographic result

The strongest research target remains:

\[
\boxed{
\text{compact PQ quorum certificate}
+
\text{conflict-only public extraction}
+
\text{no linear signer sidecar}
}
\]

with a construction and reduction proving:

### Threshold unforgeability

Fewer than the quorum threshold cannot produce a valid certificate.

### Conflict extraction

Two conflicting valid certificates permit extraction of at least one common signer.

### Non-frameability

No honest nonparticipating validator can be falsely extracted.

### Compact normal certificate

Happy-path certificate size is sublinear in the full signer-set evidence and ideally independent or nearly independent of committee size.

### Practical BFT signing

Low message-dependent online rounds.

### Post-quantum assumptions

Security reduces to accepted post-quantum hardness assumptions under an appropriate quantum adversarial model.

### Reconfiguration

The primitive can be safely re-keyed or replaced at epoch boundaries.

No such result is claimed in this project yet.

---

# 60. Research methodology lesson

The proof revisions exposed a repeatable principle:

> **Every abstract negligible term must eventually become one of three things: a named cryptographic theorem, an explicit operational assumption, or a protocol state-machine invariant.**

Examples:

\[
\epsilon_{\rm DKG}
\]

became:

\[
\delta_{\rm setup}
\]

until a real DKG theorem is available.

"validator signs once" became:

\[
VoteLog
+
PersistBeforeSend.
\]

"preprocessing is fresh" became:

\[
Unused\rightarrow Reserved\rightarrow Burned.
\]

"evidence exists" became:

\[
HaveEvidence
\Rightarrow
AnchorVote.
\]

"next configuration is known" became:

\[
Config_{e+1}\subset B_e^\dagger.
\]

"epoch handoff preserves locks" became:

\[
\text{no live locks cross the finalized barrier}.
\]

This is the main methodological improvement across the proof sequence.

---

# 61. Primary-source ledger

The research record should continue to treat primary sources as authoritative and should not rely on scheme descriptions copied from adjacent papers.

Current primary-source categories include:

## NIST threshold-cryptography process

- NIST IR 8214C, *NIST First Call for Multi-Party Threshold Schemes* (2026)
- NIST Multi-Party Threshold Cryptography project and preview materials

NIST currently describes a multi-stage process of previews, packages, and public analysis, with technical specifications, reference implementations, experimental reports, and patent notes required for package submissions.

## Hermine

- ePrint 2026/419, *Hermine: An Efficient Lattice-based FROST-like Threshold Signature*
- NIST MPTS 2026 Hermine preview/writeup/slides

Load-bearing items to quote directly from the exact version used:

- precise threshold-unforgeability notion;
- ROM/QROM model;
- exact hardness assumptions and intermediate proof problems;
- corruption model;
- signing query bounds;
- refresh bounds if used;
- DKG scope and theorem status;
- identifiable-abort conditions.

## Ringtail

- IEEE S&P 2025 Ringtail paper / corresponding ePrint

Load-bearing item already corrected:

- standard LWE/ROM result must not be conflated with an adjacent AOM-MLWE construction.

## Base BFT protocol

The exact base consensus protocol must be frozen before the final safety/refinement proof.

Its safety predicate determines:

- conflict domain;
- safe-vote rule;
- finality rule;
- terminal boundary semantics;
- exact meaning of "finalized."

The generic composition proof cannot substitute for this protocol-specific state-machine definition.

---

# 62. Current artifacts

Current formal-methods starter artifacts:

- `PQAQCEpochBarrier.tla` — referenced as an artifact of this record; the file is not present in this repository
- `PQAQCEpochBarrier.cfg` — referenced as an artifact of this record; the file is not present in this repository

The current model contains an abstract executable state machine for:

- one vote per domain;
- single-use preprocessing;
- evidence-before-anchor;
- finalized epoch boundary;
- post-finality sealing;
- seal-certificate activation;
- persistent state across crashes.

The artifact explicitly says it is a starter model and not a completed machine-checked proof.

---

# 63. Immediate next work, in order

## 1. Freeze the exact base consensus state machine

Do not continue proving "base BFT safety" as a black box forever.

Specify:

- proposal;
- safe-vote predicate;
- locking/preparation rule;
- finality;
- view change;
- epoch-close finality condition.

This is necessary for the final refinement theorem.

---

## 2. Run the TLA+ model

Use a finite four-node model:

\[
n=4,\quad f=1,\quad q=3.
\]

Search reachable states and counterexamples under crashes, stale messages, partial seals, and activation attempts.

---

## 3. Extend the TLA+ model to the corrected v0.5 seal sequence

The current starter model represents post-finality sealing but should be checked against the final "finalize first, seal second, retransmit persistent seal" semantics and the self-contained next config.

---

## 4. Produce the concrete primitive assumption ledger

For the exact threshold implementation version, quote:

- theorem number;
- security game name;
- hardness assumptions;
- random-oracle model;
- corruption model;
- query limits;
- DKG status;
- IA status;
- implementation limitations.

No paraphrased memory.

---

## 5. Run concrete lattice/security estimates

Freeze:

- committee cap;
- epoch duration;
- maximum lifetime epochs;
- signing session rate;
- threshold parameter set;
- evidence signature level;
- hash lengths.

Calculate lifetime security margins.

---

## 6. Build the implementation refinement map

Map actual database/WAL fields to:

\[
epoch,
VoteLog,
Prep,
Evidence,
Seal,
Boundary,
Activation.
\]

Identify the real durable linearization point for every externally visible vote.

---

## 7. Test each crash boundary on Docker

Crash immediately before and after each durability point and verify:

- no double vote;
- no preprocessing reuse;
- no epoch rollback;
- same seal retransmitted;
- stale messages inert;
- state roots reconverge.

---

## 8. Begin the separate frontier-crypto track

Do not confuse this with finishing the practical system.

Research conflict-extractable post-quantum quorum signatures as a distinct project with its own construction, security definition, lower bounds, and benchmarks.

---

# 64. Final project statement

The practical research goal can be stated as:

\[
\boxed{
\textbf{Build and formally justify a compact post-quantum BFT quorum-certificate system whose consensus safety does not depend on exposing every signer on the hot path, while preserving public accountability, crash safety, evidence availability, and safe epoch reconfiguration.}
}
\]

The proof strategy is:

\[
\boxed{
\text{base BFT safety}
+
\text{threshold-support security}
+
\text{durable vote state}
+
\text{single-use preprocessing}
+
\text{accountability evidence}
+
\text{finalized epoch barriers}
\Longrightarrow
\text{global accountable safety}.
}
\]

The remaining frontier goal is stronger:

\[
\boxed{
\textbf{Remove the sidecar itself by designing a compact post-quantum certificate that reveals a common conflicting signer only when two conflicting certificates exist.}
}
\]

That remains an open research target and should continue to be described as such until there is an exact construction, formal reduction, concrete security analysis, implementation, and independent review.

---

# 65. Current bottom line

The project began as a broad idea: replace large individual post-quantum BFT quorum certificates with something compact and accountable.

The main struggle was discovering that "compact threshold signature" is only one piece of the real problem. The hard boundaries were repeatedly elsewhere:

- exact primitive security notion;
- DKG;
- random-oracle model;
- stateful preprocessing;
- crashes;
- evidence availability;
- malicious aggregators;
- epoch seams;
- configuration distribution;
- lifetime query/security budgets;
- implementation refinement.

The current practical architecture is now much narrower and better specified because each of those problems was either:

1. turned into an explicit theorem,
2. turned into an explicit operational assumption,
3. turned into a persistent state invariant,
4. or removed through protocol simplification.

The paper proof is no longer changing shape dramatically from revision to revision. That is a signal that paper-only iteration has reached diminishing returns.

The next credibility gains will come from:

\[
\boxed{
\text{machine checking}
+
\text{concrete cryptographic parameters}
+
\text{implementation refinement}
+
\text{adversarial testing}.
}
\]

The truly novel cryptographic breakthrough—compact conflict extraction without a sidecar—remains separate and unsolved.

---

**Repository note.** This is the first surviving full revision of the Target-A record (v0.5); it is
superseded and kept for provenance. The current Target-A record is
`docs/research-proof-documentation.md` (v0.7). The TLA+ starter module named under "Current artifacts"
is not preserved in this repository; the only TLA+ specification that survives here is
`formal/epoch-barrier.tla` with `formal/epoch-barrier.cfg` (v0.6), which is a specification and has
never been executed by a model checker.
