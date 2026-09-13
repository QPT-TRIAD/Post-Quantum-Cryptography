# Post-Quantum Accountable Quorum Certificates
## Research Objective, Formal Proof Program, Design Evolution, Known Gaps, and Current Status

**Document status:** Research specification / proof-development record  
**Version:** 0.7 research record  
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

# 1A. v0.6 resolution record

v0.6 freezes three points that were previously moving.

First, the Hermine security-label dispute is resolved by distinguishing **motivating prose** from the **formal game and theorem**. The paper says it extends strong unforgeability to the proactive setting "with a focus on TS-UF-2" from the Bellare et al. hierarchy. However, Definition 3.2 formally defines the game `Game^ts-suf-2`, calls the property `ts-suf-2`, and Theorem 6.4 states that Hermine is `ts-suf-2`. Therefore this record cites the formal theorem as the load-bearing security statement while retaining TS-UF-2 as the hierarchy/provenance description. This avoids upgrading or downgrading the theorem based on introductory prose.

Second, this record standardizes the technical assumption name to **AOM-MISIS**, matching the notation used in the Hermine paper's hardness-assumption section and unforgeability theorem. NIST preview material abbreviates the same discussion as "AOM-MSIS"; v0.6 records that as presentation terminology and does not create a second assumption row from it.

Third, v0.6 stops deferring the individual-evidence lifetime budget. The reference deployment profile is now frozen for proof budgeting as:

\[
\boxed{
N_{\max}=64,\quad
\text{daily epochs},\quad
\text{10-year design life},\quad
\text{ML-DSA-65 evidence keys}.
}
\]

This is a **reference profile**, not a claim that the eventual product must rotate daily. Any deployment changing these values must rerun the same budget calculation before release.

The formal-methods track also advances in v0.6. TLC itself was not executed, because the TLA+ tools JAR was not available to the authors. Rather than call the model "checked," v0.6 does two things:

1. produces a fully finite four-node TLA+ model/configuration ready for TLC; and
2. executes an independent exhaustive Python state explorer over three decomposed finite models mirroring the critical invariants.

The executable finite-state checks completed with no invariant violation in:

- **15,633** vote/seal/epoch states and **44,388** transitions;
- **2,401** preprocessing states and **10,976** transitions;
- **90** evidence/anchor states and **233** transitions.

These results are useful bounded evidence, but they are **not a substitute for TLC/TLAPS** and are labeled accordingly throughout the document.

---

# 1B. v0.7 formal-methods correction record

v0.7 applies the same evidence discipline to the project's own formal-methods artifacts that earlier revisions applied to external cryptographic papers.

The v0.6 checker results were genuine executions, but several prose claims exceeded what those models represented. v0.7 records each correction explicitly.

### Correction 1 — documentation/artifact invariant mismatch

v0.6 prose named invariants that were not present in the TLA+ artifact. v0.7 eliminates that mismatch.

The v0.7 `.cfg` contains only invariant identifiers that are actually defined in the `.tla` module, and generation now includes an automated consistency check that fails if a CFG invariant is absent from the TLA+ source.

### Correction 2 — boundary uniqueness is now represented rather than assumed

v0.6 represented `finalizedBoundary` as one scalar that could be assigned only once. Two finalized boundaries therefore could not exist in the state representation.

v0.7 instead represents:

- honest boundary votes;
- Byzantine boundary votes;
- a set of independently formable boundary finality certificates.

A boundary certificate forms only after at least \(q=2f+1\) boundary votes.

Honest validators may vote for only one candidate boundary; the Byzantine validator may vote for both.

The actual invariant is:

\[
\boxed{
|\mathsf{FinalityCerts}|\le1.
}
\]

This means the finite model can represent the ingredients that would create a boundary fork and checks that the honest-vote/quorum rules prevent the second certificate.

A deliberately unsafe mutation that allows honest validators to vote for both boundaries **does produce a boundary fork counterexample**. That negative control is retained in the verification record.

This is still not a proof of a real base BFT protocol's finality theorem. It is a bounded executable check of the quorum-intersection/one-honest-vote abstraction used by the boundary proof.

### Correction 3 — crash is no longer a stutter-only action

v0.6 used:

`Crash == UNCHANGED vars`.

That did not model crash recovery.

v0.7 separates volatile and durable state.

For votes:

\[
\text{BeginVote}_{volatile}
\rightarrow
\text{PersistVote}_{durable}
\rightarrow
\text{SendVote}.
\]

For preprocessing:

\[
\text{BeginReserve}_{volatile}
\rightarrow
\text{PersistReserve}_{durable}
\rightarrow
\text{UsePrep}
\rightarrow
\text{SendShare}.
\]

A crash:

- clears volatile vote state;
- clears volatile preprocessing reservations;
- preserves durable vote reservations;
- preserves durable preprocessing state.

Restart conservatively burns durable preprocessing states that were reserved or emitted.

The safe checker exhaustively explores crashes at these boundaries.

A deliberately unsafe mutation that permits transmission from volatile, non-persisted state is also explored and **does produce a counterexample**. The negative-control trace demonstrates why persist-before-send is load-bearing.

### Correction 4 — conflict domains and preprocessing objects are now real model dimensions

v0.6 declared `Domains` and `Preps` but did not use them in the state machine.

v0.7 uses:

\[
VoteChoice[i][d]
\]

for domain-indexed votes and:

\[
PrepState[i][p]
\]

for preprocessing objects.

The bounded configuration uses two distinct conflict domains and two preprocessing objects.

`Epochs` was removed as a misleading unused parameter; the current bounded epoch model explicitly represents old epoch `0` and activated epoch `1`.

### Correction 5 — partition recovery now uses the transition system

v0.6's `partition_recovery()` was only direct set arithmetic.

v0.7 introduces explicit seal-network state:

- durable seal production;
- per-node connectivity;
- partition action;
- heal action;
- seal delivery;
- seal certificate formation from delivered acknowledgements.

The checker exhaustively explores the finite seal/network model for safety.

It also executes a recovery path through the **same transition relation**:

\[
\begin{aligned}
&produce_0,\ deliver_0,\\
&produce_1,\ deliver_1,\\
&partition_2,\ produce_2,\\
&heal_2,\ deliver_2,\ formQC.
\end{aligned}
\]

This proves only that the recovery path is reachable in the bounded model. It is **not** a temporal-logic proof that recovery is inevitable under fairness. Eventual recovery remains a liveness theorem conditioned on eventual synchrony/fair delivery.

### Negative controls are now mandatory

A checker that only reports PASS on a model whose state representation excludes bad states can create false confidence.

v0.7 therefore includes mutation tests that intentionally remove critical guards.

The checker must:

- PASS the safe model; and
- FAIL the mutated model with a concrete counterexample.

This establishes that the bounded checker is capable of observing the failure modes the documentation says it is testing.

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

# 35. Current Hermine adapter status — corrected formal wording

The Hermine adapter is relevant because it targets a medium-size committee and a low-online-round lattice threshold-signature path.

The proof ledger is now keyed to the **formal theorem**, not a paraphrase:

- the introductory/security discussion says Hermine extends strong unforgeability to the proactive setting **with a focus on TS-UF-2** from the Bellare et al. hierarchy;
- Definition 3.2 then defines the proactive strong-unforgeability game under the identifier `ts-suf-2`;
- Theorem 6.4 states formally that **Hermine is `ts-suf-2`** under MSIS and AOM-MISIS;
- the NIST MPTS slides summarize the same result as **TS-sUF-2 in the ROM**;
- therefore the load-bearing ledger entry is **"formal theorem: ts-suf-2; hierarchy/provenance: TS-UF-2"** rather than pretending those two phrases are interchangeable.

This distinction matters because TS-UF-i and strong-unforgeability variants are different security notions. The project does not infer a security level from naming alone; it uses the actual winning condition and theorem statement of the selected primitive.

For hardness notation, v0.6 uses **AOM-MISIS** everywhere in the technical proof, because that is the notation used by the detailed paper for the Algebraic One-More Module-ISIS problem. NIST preview/slides use the shorter presentation label **AOM-MSIS**. The two labels are recorded as source-level terminology rather than modeled as independent assumptions.

The remaining Hermine adapter status is:

- threshold signing theorem: available in the published **ROM** model;
- formal theorem: `ts-suf-2`, with explicit query parameters in Theorem 6.4;
- hardness route: MSIS plus AOM-MISIS, with the paper citing reductions of AOM-MISIS to standard MSIS/MLWE in the stated regimes;
- DKG: described in project/NIST material, but its careful formal analysis is not discharged by the detailed signing proof relied on here;
- full QROM threshold-signing theorem: not discharged;
- concrete production implementation assurance: not discharged.

The generic system theorem remains independent of Hermine. A different threshold primitive may replace this adapter if it satisfies the same system-facing security interface.

---

# 36. Ringtail correction log

One important literature error was found and corrected during the project.

An earlier critique incorrectly associated Ringtail with a new algebraic one-more Module-LWE assumption.

The published Ringtail result instead states its security from standard LWE in the random-oracle model and contrasts itself with contemporaneous work based on newer assumptions.

This mattered because the assumption ledger is load-bearing. A scheme's hardness foundation cannot be summarized from memory or adjacent related-work citations.

**Lesson:** every primitive row in the assumption ledger must be derived from the exact primary theorem used by the implementation.

---

# 37. Hermine assumption and naming correction log

The assumption ledger has been corrected several times because neighboring lattice-threshold papers use similar but non-identical terminology.

The v0.6 technical wording is:

> Hermine's formal unforgeability theorem is stated under MSIS and **AOM-MISIS**. The detailed paper defines AOM-MISIS as its Algebraic One-More Module-ISIS problem and cites a reduction to standard MSIS and MLWE in the parameter regimes used for the security argument.

The NIST MPTS preview/slides use the shorter spelling **AOM-MSIS**. This document does not silently alternate the two forms. It uses AOM-MISIS in formulas and theorem statements and notes the NIST spelling only when describing those specific presentation materials.

Likewise, the security notion is not summarized as merely "TS-UF-2" or merely "strong TS-UF-2." The correct record is:

\[
\boxed{
\text{formal game/theorem: ts-suf-2}
\quad;\quad
\text{hierarchy focus cited in prose: TS-UF-2}.
}
\]

This avoids conflating the origin of the security hierarchy with the exact game Hermine finally proves.

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

# 40. Individual-signature multi-user security — v0.6 reference budget frozen

The evidence layer uses many independent validator identity keys over the system lifetime. v0.6 therefore freezes a concrete **reference security profile** instead of leaving the multi-user term symbolic forever.

Reference profile:

\[
\boxed{
N_{\max}=64,\qquad
\text{epoch length}=24\text{ h},\qquad
L=10\text{ years}.
}
\]

Using 365.25 days/year and rounding up gives:

\[
E=3,653\text{ epochs}.
\]

If every validator receives a fresh evidence-signing key every epoch, the lifetime number of public evidence keys is at most:

\[
N_u=64E=233,792.
\]

Under the conservative generic single-user to multi-user union bound:

\[
\operatorname{Adv}^{MU}
\le
N_u\operatorname{Adv}^{SU},
\]

the loss is:

\[
\log_2 N_u
=
17.835\text{ bits}.
\]

Therefore, to hold the **entire identity-signature layer** below a lifetime forging budget of \(2^{-128}\), a crude single-user proxy would need:

\[
-\log_2\operatorname{Adv}^{SU}
\ge
128+17.835
=
145.835.
\]

v0.6 adopts a stricter internal allocation:

\[
\boxed{
\operatorname{Adv}^{MU}_{ID}
\le2^{-140}.
}
\]

The corresponding single-user screening target is:

\[
140+17.835
=
\boxed{157.835\text{ bits}}.
\]

The reference evidence signature is therefore frozen as:

\[
\boxed{\text{ML-DSA-65}}.
\]

NIST places ML-DSA-65 in security category 3 and requires a 192-bit-strength RBG for its key generation. Security categories are **not literal exact forging-probability exponents**, so the following subtraction is only a screening calculation, not a security reduction. If one uses 192 bits as a rough category-strength proxy, the conservative linear multi-user screening margin would be:

\[
192-17.835
=
174.165\text{ bits},
\]

which is above the v0.6 140-bit identity-layer budget.

At the 64-seat maximum quorum,

\[
q=43.
\]

An ML-DSA-65 signature is 3309 bytes, so the raw signature portion of a fully attributable evidence sidecar is:

\[
43\times3309
=
142,287\text{ bytes}
\approx
139.0\text{ KiB}.
\]

That cost is intentionally moved off the compact consensus QC hot path.

### What is solved here

The project no longer says "the multi-user budget will be chosen later." It has a concrete reference budget and parameter choice against which code, benchmarks, and audits can be run.

### What would force recalculation

The budget must be recomputed if any of these change:

- committee cap above 64;
- epoch rotation faster than daily;
- design lifetime above 10 years;
- more than one independent evidence key per validator per epoch;
- a different per-key signature parameter set;
- a tighter system-wide probability allocation.

This is deliberately a **reference deployment contract** rather than a universal cryptographic constant.

---

# 41. Concrete-security work still required after the v0.6 budget freeze

The identity-signature layer now has a concrete reference committee/epoch/lifetime budget. The remaining concrete-security work is primarily on the **threshold primitive**, because its theorem contains construction-specific parameters and query losses.

Still required before a production cryptographic profile can be called frozen:

- exact Hermine (or replacement primitive) parameter set used by the implementation;
- exact \(Q_{\rm Sign}\), \(Q_{H_c}\), \(Q_{H_\beta}\), and refresh-query policy admitted by the selected theorem;
- a deployment signing-session rate and hard per-epoch session cap;
- concrete MSIS/AOM-MISIS/MLWE estimates for those parameters using current attack estimators;
- rejection/failure probabilities, if any, at the chosen parameters;
- the exact setup/DKG trust or proof adapter;
- final QROM/ROM deployment statement;
- preprocessing inventory sized from the session cap plus recovery reserve.

Frozen in the v0.6 **reference** profile:

- validator cap: 64;
- identity-key rotation: daily;
- design lifetime: 10 years;
- evidence signature: ML-DSA-65;
- identity-layer lifetime budget: \(2^{-140}\);
- evidence commitment target: 384-bit output.

The threshold-signature parameter table cannot be honestly filled in until the exact implementation version and theorem parameter set are selected. That item is blocked on the primitive adapter, unlike the multi-user identity budget which is now resolved.

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

# 49. Formal implementation state — v0.7 exact artifact ledger

The formal-methods artifacts are now documented from the files that actually exist rather than from the intended model.

## TLA+ state represented in v0.7

`PQAQCEpochBarrier_v0_7.tla` explicitly represents:

- validator running/crashed state;
- durable vote state indexed by validator and conflict domain;
- volatile vote state indexed by validator and conflict domain;
- externally sent vote records;
- durable preprocessing phase indexed by validator and preprocessing object;
- durable preprocessing session binding;
- volatile preprocessing reservation;
- externally sent threshold-share records;
- evidence possession;
- evidence anchor votes;
- honest boundary votes;
- Byzantine boundary votes;
- independently formable boundary finality certificates;
- honest seal production;
- Byzantine seal production;
- per-node link connectivity;
- delivered seal acknowledgements;
- seal certificates;
- local epoch activation;
- activated boundary.

The model uses the configured `Domains` and `Preps` sets as real state dimensions.

## TLA+ invariants actually present

The `.cfg` requests exactly the invariant identifiers actually defined by the `.tla` file:

1. `TypeOK`
2. `HonestVoteOncePerDomain`
3. `SentVoteMatchesDurable`
4. `PrepNoReuse`
5. `SentShareMatchesDurableSession`
6. `CrashedHasNoVolatileState`
7. `EvidenceBeforeAnchor`
8. `BoundaryFinalityUnique`
9. `SealOnlyFinalized`
10. `DeliveredSealAuthentic`
11. `SealCertOnlyFinalized`
12. `SealCertHasDeliveredQuorum`
13. `ActivationRequiresSealCert`

Generation performs an automated CFG/TLA identifier-consistency check. v0.7 creation fails if a CFG invariant name is not defined in the TLA+ module.

## What `BoundaryFinalityUnique` means now

Unlike v0.6, this is not encoded as a single scalar that can only be assigned once.

The model permits each candidate boundary to form a separate finality certificate if it can gather a quorum. Honest validators are restricted to one boundary vote, while Byzantine validators may vote for both candidates.

The invariant:

\[
|\mathsf{FinalityCerts}|\le1
\]

is therefore a property of the quorum/vote transition system rather than a type restriction on one scalar.

The bounded checker additionally runs an unsafe mutation where honest boundary double-voting is permitted; that model produces a concrete two-certificate boundary-fork trace.

## Native TLC status

Native TLC/TLAPS is still **not claimed**.

Java is installed, but `tla2tools.jar` was not available to the authors. The TLA+ module has therefore not been executed by TLC.

The formal claim remains:

\[
\boxed{
\text{TLA+ specification produced and artifact-consistency checked; native TLC pending.}
}
\]

That statement is intentionally narrower than "TLA+ verified."

---

# 50. Executed bounded verification — v0.7 exact scope

The independent checker is:

`pqaqc_finite_state_check_v0_7.py`

It is **not** TLC and it is **not** a cryptographic proof.

It consists of five deliberately decomposed finite models so that each result has a narrow interpretation.

- `domain_votes_safe`: **729 states**, **2,916 transitions**, no invariant violation
- `boundary_safe`: **140 states**, **400 transitions**, no invariant violation
- `crash_safe`: **23,474 states**, **127,006 transitions**, no invariant violation
- `evidence_safe`: **28 states**, **55 transitions**, no invariant violation
- `seal_network_safe`: **1,440 states**, **8,592 transitions**, no invariant violation

## What each PASS means

### Domain-vote model

Checks one honest vote per **conflict domain**, with two distinct modeled domains.

This corrects the v0.6 flat "one vote ever" abstraction.

### Boundary model

Checks that two competing boundary finality certificates cannot both form for:

\[
n=4,\quad f=1,\quad q=3,
\]

when:

- each honest validator votes for at most one boundary;
- the Byzantine validator may vote for both.

This is a bounded executable check of the quorum-intersection abstraction. It does not replace a full base-consensus finality proof.

### Crash model

Uses real volatile/durable distinctions.

Crash clears volatile state but preserves durable state.

Restart burns preprocessing records left in reserved/emitted durable phases.

The checker verifies that externally sent votes correspond to durable vote reservations and that externally sent threshold shares correspond to durable preprocessing bindings.

### Evidence model

Checks:

\[
AnchorVote_i(C)\Rightarrow HaveEvidence_i(C).
\]

### Seal-network model

Checks that:

- delivered seals were actually produced;
- a seal certificate contains at least \(q\) delivered acknowledgements.

The model contains explicit partition and heal transitions.

## Negative-control / mutation results

v0.7 intentionally runs unsafe variants.

The safe checker is considered meaningful only if these mutated models fail.

The mutations are:

1. allow an honest validator to send conflicting messages in one domain;
2. allow honest validators to vote for both candidate epoch boundaries;
3. allow vote/share transmission from volatile state before durable persistence.

The executed checker found counterexamples for all three mutations.

This matters because it demonstrates that the checker is not merely reporting invariants that are impossible to violate because of the representation.

## Partition-recovery result

The post-seal recovery path is now executed through the actual seal transition function.

The tested path:

1. honest validator 0 produces and delivers a seal;
2. honest validator 1 produces and delivers a seal;
3. validator 2 is partitioned;
4. validator 2 produces its durable seal while partitioned;
5. no certificate yet exists;
6. validator 2 is healed;
7. its seal is delivered;
8. the 3-of-4 seal certificate forms.

This establishes **reachability of recovery** in the finite model.

It does not prove inevitable recovery under every scheduler.

The liveness theorem therefore remains conditional on eventual synchrony and fair/effective retransmission.

## Correct wording for external review

The strongest accurate statement from these runs is:

\[
\boxed{
\text{The v0.7 decomposed finite abstractions were exhaustively explored with no safety-invariant violation,}
}
\]

together with:

\[
\boxed{
\text{three deliberately unsafe mutations produced the expected counterexamples.}
}
\]

The project must not call this "machine-verified consensus safety" or "TLA+ verified."

---

# 51. Required model-checking scenarios after v0.7

The bounded checker now directly covers several formerly outstanding scenarios, but the integrated TLC/refinement program remains larger.

## Executed in the v0.7 independent checker

- two separate conflict domains;
- honest one-vote-per-domain;
- deliberately unsafe same-domain double vote;
- two competing epoch boundaries;
- Byzantine vote on both boundaries;
- actual boundary finality certificate formation from quorum votes;
- deliberately unsafe honest boundary double-vote producing a fork;
- volatile vote before persistence;
- durable vote persistence;
- send after persistence;
- volatile preprocessing reservation;
- durable preprocessing reservation;
- preprocessing use;
- share send after durable state;
- crash clearing volatile state;
- restart preserving votes and burning reserved/emitted preprocessing;
- deliberately unsafe send-before-persist mutation;
- evidence receipt before anchor vote;
- partitioned seal delivery;
- heal and seal retransmission;
- quorum seal formation.

## Still required in native TLC / integrated model

- multiple heights and views;
- stale old-view message arrival;
- explicit base-protocol lock/prepared state;
- leader/view-change transitions;
- actual finality rule of the selected BFT protocol rather than the boundary-quorum abstraction;
- query-budget safe halt;
- preprocessing inventory exhaustion;
- next-epoch private-share readiness;
- old-epoch messages after activation;
- multiple sequential epoch boundaries;
- state-root ancestry;
- fairness/eventual-synchrony temporal properties;
- Byzantine malformed-share delivery and blame envelopes;
- evidence loss after initial persistence;
- implementation-level WAL/fsync failures.

## Formal-methods sequencing

The next model-checking sequence is:

1. run the v0.7 TLA+ safety model under TLC when the toolchain is available;
2. reproduce the independent checker's invariants in TLC;
3. add symmetry reduction;
4. integrate the actual base BFT lock/view-change state machine;
5. add two sequential epoch transitions;
6. only then add temporal liveness/fairness properties.

The independent checker is a bounded cross-check and mutation harness. It is not a replacement for the TLA+ refinement program.

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

- exact formal `ts-suf-2` support abstraction (with TS-UF-2 retained only as hierarchy/provenance wording);
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

## v0.6 — source precision, lifetime budget, and executable state exploration

v0.6 resolves three long-running issues.

### Security-name precision

The ledger now distinguishes:

\[
\text{formal Hermine game/theorem: ts-suf-2}
\]

from the paper's prose description that it extends strong unforgeability with a focus on the TS-UF-2 hierarchy.

The technical assumption notation is standardized to AOM-MISIS, with the NIST-preview "AOM-MSIS" spelling recorded only as presentation terminology.

### Concrete evidence-layer lifetime budget

The reference deployment is frozen at:

\[
64\text{ validators},
\quad
1\text{-day epochs},
\quad
10\text{ years},
\quad
\text{ML-DSA-65},
\]

with a \(2^{-140}\) lifetime allocation for evidence-signature framing/forgery.

### Formal-methods execution

The model-checking track moved from an unexecuted outline to:

- revised finite TLA+ artifacts ready for TLC;
- three exhaustive independent finite-state explorations;
- explicit recorded state/transition counts;
- a reproduced post-seal partition-recovery scenario;
- a documented reason why TLC itself has not yet been run.

The remaining formal-methods claim is intentionally narrow: **bounded independent exploration passed; native TLC/TLAPS remains pending.**

---

## v0.7 — formal-artifact accountability and mutation testing

v0.7 applies the project's own "assumption ledger" discipline to formal methods.

The principal changes are:

- documentation lists only invariants actually present in the TLA+ artifact;
- conflict domains are first-class model indices;
- preprocessing objects are first-class model indices;
- boundary finality is derived from quorum votes rather than assumed through a single set-once scalar;
- crashes distinguish volatile from durable state;
- restart conservatively burns persisted one-time preprocessing;
- network partition/heal and seal delivery are explicit state transitions;
- the partition-recovery example runs through the actual transition relation;
- unsafe mutation controls are required and must produce counterexamples.

This revision does **not** upgrade the project to "machine-verified BFT." It makes the bounded evidence honest enough to be useful.

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
| Hermine formal security notion | **Verified: formal game/theorem `ts-suf-2`; prose cites TS-UF-2 focus** | Ledger keys to Definition 3.2 / Theorem 6.4, not shorthand prose |
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
| Boundary uniqueness | **Paper proof + bounded quorum abstraction checked** | v0.7 can represent competing finality certificates; full base-BFT finality still requires the selected protocol model |
| Global cross-epoch safety | **Closed conditionally** | Induction over unique barriers |
| Evidence-layer lifetime reference budget | **Frozen for v0.6 reference profile** | 64 validators, daily epochs, 10 years, ML-DSA-65, identity-layer budget \(2^{-140}\) |
| Formal-methods bounded checking | **v0.7 safe models passed; unsafe mutations failed as expected; TLC pending** | Domain-indexed votes, derived boundary finality, volatile/durable crash state, evidence, and explicit seal network checked in decomposed finite models |
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
- exact theorem/security game cited, including the distinction between TS-UF-2 provenance prose and the formal `ts-suf-2` game/theorem;
- exact setup/DKG assumption stated;
- exact ROM/QROM posture stated;
- concrete lattice parameter analysis completed;
- query bounds fixed;
- individual evidence signature parameters fixed;
- multi-user/lifetime budget checked against the frozen v0.6 reference profile;
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

- precise threshold-unforgeability notion, quoting the formal Definition 3.2 / Theorem 6.4 rather than introductory shorthand;
- ROM/QROM model;
- exact hardness assumptions and intermediate proof problems; use AOM-MISIS for the paper's technical notation and record NIST's AOM-MSIS spelling only as presentation terminology;
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

v0.7 formal-methods artifacts:

- `PQAQCEpochBarrier_v0_7.tla` — referenced as an artifact of this record; the file is not present in this repository
- `PQAQCEpochBarrier_v0_7.cfg` — referenced as an artifact of this record; the file is not present in this repository
- `pqaqc_finite_state_check_v0_7.py`
- `pqaqc_modelcheck_v0_7_results.txt`

The TLA+ module now models:

- domain-indexed voting;
- durable/volatile vote state;
- multiple preprocessing objects;
- crash/restart;
- evidence possession/anchoring;
- competing boundary votes and independently formable finality certificates;
- explicit partition/heal state;
- seal production and delivery;
- seal certificate formation;
- epoch activation.

The Python checker independently and exhaustively explores decomposed finite abstractions of those properties and includes unsafe mutation controls.

Neither artifact is described as a completed proof of the production implementation.

The existing v0.6 artifacts are retained only as historical proof-development records and should not be cited as the current formal model.

---

# 63. Immediate next work, in order

## 1. Run the v0.7 TLA+ model under native TLC

The model is now materially different from v0.6:

- competing boundaries are representable;
- conflict domains are indexed;
- crash state is volatile/durable;
- partitions affect seal delivery.

The first TLC objective is safety only.

Do not add fairness until these invariants reproduce the independent checker results.

## 2. Freeze the actual base BFT state machine

Boundary finality is still abstracted as a quorum of one-vote-per-honest-validator boundary votes.

The production proof must define the actual:

- proposal rule;
- lock/prepared state;
- safe-vote predicate;
- view-change rule;
- commit/finality rule.

Only then can the boundary abstraction be refined to the deployed consensus protocol.

## 3. Build the implementation refinement map

Map real WAL/database fields to:

\[
running,\ durableVote,\ volatileVote,\ Prep,\ Evidence,\ Seal,\ Epoch.
\]

The critical test is whether the implementation's crash behavior matches the v0.7 durable/volatile abstract machine.

## 4. Execute Docker crash tests at the modeled boundaries

Crash after:

- BeginVote but before PersistVote;
- PersistVote but before SendVote;
- BeginReserve but before PersistReserve;
- PersistReserve but before UsePrep;
- UsePrep but before SendShare;
- SendShare before cleanup;
- seal persistence before delivery;
- new-epoch activation before first vote.

The executable implementation must match the abstract recovery rules.

## 5. Finish the threshold primitive adapter

Still required:

- exact concrete parameter set;
- exact query bounds;
- exact DKG/setup adapter;
- ROM/QROM statement;
- lattice-estimator run.

These remain primitive-level obligations rather than BFT bookkeeping issues.

## 6. Keep frontier conflict extraction separate

The no-sidecar conflict-extractable post-quantum quorum signature remains a separate cryptographic research project.

Do not allow completion of the practical two-layer system to be represented as completion of that stronger primitive.

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

The truly novel cryptographic breakthrough—compact conflict extraction without a sidecar—remains separate and unsolved. The formal-methods claim is likewise deliberately bounded: v0.7 has executable finite-state evidence and mutation counterexamples, but native TLC/TLAPS and implementation refinement remain unfinished.

---

**Repository note.** This is the current Target-A research record (v0.7); v0.5 and v0.6 are kept as
`history/research-proof-documentation-v0.5.md` and `history/research-proof-documentation-v0.6.md`.
The v0.8 record, and the v0.7/v0.8 TLA+ modules named in the text, are not preserved in this
repository; the only TLA+ specification that survives here is `formal/epoch-barrier.tla` with
`formal/epoch-barrier.cfg` (the v0.6 model), which is a specification and has never been executed by a
model checker. The current bounded checker is `src/pqaqc_finite_state_check.py` and its recorded output
is `results/pqaqc_modelcheck.txt`. See `docs/epoch-barrier-specification.md` for what the recorded
model-check output does and does not establish.
