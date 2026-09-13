# PQ CE-QS v1.18: research qualification and remaining blocker decisions

Research cutoff: **9 September 2026**. Target: a portable, post-quantum, conflict-extractable 43-of-64 quorum certificate, at most 32,768 bytes, with no per-certificate sidecar.

## 1. Decision

**The literature search identifies useful construction paths, but no examined construction qualifies for the complete target. Valid full QCs generated remain zero.** This revision finalizes the research screening and several architecture decisions. It does not claim a new cryptographic construction, a complete security proof, or successful full-QC verification.

The most useful next experiment is a **single, jointly bound lattice proof of authorization, hidden quorum membership and trace handles**. LastRings supplies a closer arbitrary-threshold authorization architecture than a shared-key threshold signature. The June 2026 lattice ZK toolkit supplies an implemented privacy route worth evaluating. Neither source establishes that their composition with our trace relation fits 32 KiB.[^2][^5]

The existing Binius trace implementation remains a functional reference. Its memory blocker was closed in v1.17 for two measured executions. Its current proof format cannot reach the original cap through changes confined to query values or Merkle paths: the retained prefix alone is already too large. This is a restriction on that implementation path, not an impossibility result for CE-QS.

The immediate decisions are:

| Question | Finalized decision for this revision |
|---|---|
| Can another query-value encoding alone finish the current system? | No, while retaining its measured 46,192-byte native prefix and current framing. |
| Does an implemented lattice ZK route exist in the literature? | Yes, authors now report one; the exact CE-QS port and security qualification remain open. |
| Can a small threshold signature replace the missing authorization proof? | Only with a demonstrated binding between its actual contributors and the same trace handles. No such integration is established here. |
| Can a proof of the current tracing secret become the vote signature? | No. That would violate the original separation between tracing and authorization secrets. |
| Is 32 KiB universally impossible? | No such lower bound was found or proved. No complete qualifying construction was found either. |
| Is the system ready to claim 22 actual equivocators from two valid QCs? | No. The demonstrated recovery concerns a trace-only synthetic fixture. |

## 2. Scope, method and evidence levels

The review screens **32 research papers and one primary implementation source**, grouped by the problem they address. Searches covered arbitrary and structured threshold ring signatures, public conflict tracing, lattice aggregation, hash-based succinct arguments, folding, signatures of knowledge, distributed proving, and post-quantum security reductions. Older foundational papers were checked alongside revisions available at the cutoff.

Primary evidence consists of author papers, conference or publisher pages, institutional publication records, a NIST-hosted team preview, and a project repository. Secondary search results were discovery leads. They are not the evidentiary basis for the qualification decisions. This is a broad targeted review, not an exhaustive census or an independent audit of every proof.

Access matters. Several ePrint PDFs were unavailable through the research interface, while their author abstracts and version histories were accessible. For those entries, claims are limited to those materials; unexamined theorem hypotheses remain unknown. Selected full-text definitions and tables were examined where accessible. The ledger records the access level separately for every source. The inaccessible Tetris PDF was not used to assert detailed theorem properties.

Three kinds of statements are kept distinct throughout: **authors' results**, **previously executed local evidence**, and **new reasoning in this report**. A paper's performance number is never presented as a locally reproduced CE-QS benchmark. An asymptotic proof-size bound, a component proof, or an interactive transcript is never counted as a complete QC.

Version-sensitive findings include SmallWood's February 2026 extractable-binding revision, the September 2026 Neo/SuperNeo revision, the narrowly scoped September LatticeBlindFold preprint, and the August 2026 revision and changed title of Liu's tracing paper. Older names or abstracts do not override the newer source.[^7][^12][^13][^21]

## 3. The contract being qualified

The application has a fixed public configuration with 64 registered validators. An accepted QC must certify **43 distinct, independently authorized seats**, drawn from arbitrary 43-element subsets of this flat registry. Ordinary certificates hide the signer identities under the declared privacy model. The authorization and trace components must use the same hidden seats.

Given two accepted QCs for distinct conflicting messages in the same domain, a public algorithm must recover at least 22 identities that actually authorized both messages. Its only certificate-specific inputs are those two QCs. Fixed public configuration is allowed; a secret tracing key, private witness, local signing transcript, external certificate log, or supplementary opening file is not.

Every reported identity must satisfy non-frameability. In particular, the original frontier document §14.9 requires that exposing a tracing secret must not enable ordinary consensus-signature forgery. Future-domain safety after exposure requires a specified rekeying, removal or evolution mechanism. Independence of authorization keys addresses the first condition; it does not automatically solve the second.

The complete serialized QC limit is 32,768 bytes. The **current** 160-byte header and 43 handles of 96 bytes consume 4,288 bytes, leaving **28,480 proof bytes**. This payload budget is specific to that layout. A different construction may use a different layout, but must account for every certificate-specific byte and retain the same overall limit.

The security target is the declared 128-bit post-quantum/QPT model, including concrete losses. A classical random-oracle proof under a conjecturally quantum-hard assumption does not by itself meet it. CRS generation, oracle access, adaptive queries, registration, corruption, exposure and composition must match the actual construction.

The intended collaborative producer must avoid centralized collection of private signer material. With at most 21 Byzantine validators, 43 honest validators remain. Progress requires an appropriate robust protocol or an identifiable-abort and replacement mechanism under the specified network assumptions. Security with abort alone does not establish eventual completion.

## 4. Research schools and what qualifies from each

### 4.1 Aggregate native lattice relations and hide the quorum

**LoTRS** combines independent lattice signing keys with hidden selection among predefined columns. Its preview table reports 25.0 KiB for 16 signers and 32 columns, meaning a 512-key structured table. The larger 50-by-100 setting is 35.8 KiB. The preview's reductions are stated in the ROM. It offers useful aggregation and selection ideas, but its allowed-quorum policy differs from arbitrary 43-of-64, and its signature does not include our conflict-tracing relation. These figures cannot qualify this system.[^1]

**LastRings** supports arbitrary thresholds and logarithmic dependence on ring size. It combines Falcon-signature knowledge with LaBRADOR and a separate ZK layer. Its abstract reports signatures below 150 kB for rings up to 4,096 at illustrative thresholds. This makes it a relevant authorization architecture; it does not provide an exact 43-of-64 CE-QS measurement or establish a public conflict extractor for our handles.[^2]

**LaZer** supplies C implementations with a Python interface for lattice relations and norm bounds, including linear-size proofs and LaBRADOR-based succinct proofs. It is an engineering starting point for expressing a native relation. The library's ability to prove a lattice equation does not automatically cover the message hashes, signature verification, hidden seat selection and exact range constraints in our relation.[^3]

**LaBRADOR** reports a 58 KB proof of knowledge for an R1CS instance with approximately one million constraints. The original proof of knowledge must not be labeled a complete zero-knowledge solution. Its compactness is useful evidence for the lattice school; the cited benchmark already exceeds our entire QC allowance and is not our relation.[^4]

**A Toolkit for Succinct Lattice-Based Zero Knowledge Proofs**, received in June 2026, reports a concrete implementation integrating a linear ZK proof into LaBRADOR and extending LaZer. This updates the earlier assessment: lack of any implemented ZK integration is no longer the literature-level obstacle. The remaining work is to port and qualify the exact joint CE-QS relation, including its public inputs and nonlinear operations. No sub-28,480-byte complete proof is established by the abstract.[^5]

**Orthus** targets sublinear verification of lattice relations. Its authors report a ninefold verification improvement for aggregating 2^17 Falcon signatures. That is a verification result at a different workload, not evidence that 43 trace-bound authorizations fit our cap. It belongs after relation and privacy correctness in the evaluation sequence.[^6]

**Our assessment:** this family is the highest-priority architecture experiment because it can amortize many algebraic authorization relations. Preserve arbitrary membership and shared witnesses. Do not port the structured-column policy or presume that adding a separate tracing proof preserves the reported size.

### 4.2 Use hash-based proofs, with complete privacy and extraction arguments

**SmallWood** targets comparatively small instances and reports exact lattice-problem proofs below 25 KB for a range of parameters, including Kyber and Dilithium instances. Its February 2026 revision repairs binding definitions for an extractable setting. A proof about a lattice instance is not equivalent to proving 43 signature verifications plus registry membership, trace computations and hashes. Count the final encoded relation, including intermediate variables, before using its favorable size regime.[^7]

**zip** supplies nonrecursive compression for hash-based SNARGs. Its reported results reach approximately 60% of original proof size in examined benchmarks. That means retaining 60%, not removing 60%, and is not a universal factor. A CE-QS evaluation would require the exact applicable transformation and a new transcript/security map. It may alter more than the query encoding, so the restricted native-prefix floor cannot automatically be applied to every zip construction.[^8]

**WHIR** is a polynomial commitment/proximity-testing component with a reported 63 KiB commitment-opening example at 100-bit security and degree 2^22. Its performance is useful when selecting a proof protocol, but a PCS opening is not a private full quorum certificate. Neither its parameters nor its size can be transplanted into our complete-QC ledger without the surrounding argument.[^9]

**Zero-Knowledge IOPPs for Constrained Interleaved Codes** supplies honest-verifier ZK, round-by-round knowledge soundness and composable IOR techniques. It is a concrete theoretical path for protecting witnesses in modern code-based proof systems. It does not, without the remaining transformations and their hypotheses, certify the noninteractive QROM privacy of a chosen implementation.[^10]

**How to Prove Post-Quantum Security for Succinct Non-Interactive Reductions** extends BCS-style analysis to IORs in the QROM, including adaptive straightline quantum extraction and a modular vector-commitment analysis. This gives relevant tools for a composed hash-proof security argument. The relation, transcript schedule and commitment implementation still have to satisfy the theorem's hypotheses, with explicit concrete losses. It supplies neither a free 128-bit parameter upgrade nor automatic simulation-extractability.[^11]

The **spartan-whir repository** is a useful implementation cross-check. Its observed API supports security settings up to 123 bits, and its recorded full-ZK SHA-256 benchmark for a 2,048-byte input is 1,226,660 bytes for DirectSparse at 116 bits. These are the repository's measurements, not ours. This snapshot is not a 128-bit QPT-qualified CE-QS backend.[^33]

**Our assessment:** retain this school for an auditable general-purpose reference and evaluate whole-protocol improvements. Stop treating query-path compression as the only missing change. A component's privacy theorem and another paper's QROM theorem must be joined explicitly; their titles are not a composition proof.

### 4.3 Fold computations, then prove the final accumulated claim

**Neo and SuperNeo** provide lattice-based folding over small fields with low-bit-cost commitments. The September 2026 version distinguishes Neo's SIMD restriction from SuperNeo's support for general constraint systems and extension fields. Folding can reduce repeated proving work, but an accumulated relation still needs a final verifier and all data required to check it. A fold transcript is not a complete portable QC.[^12]

**LatticeBlindFold** is particularly clear about its scope: one interactive step with blinding, committed evaluation claims, and additional lattice assumptions. It constructs no final decider and claims neither recursive composition nor a complete instance-in/instance-out folding interface. Its stated interactive parameters are not a finished Fiat–Shamir deployment. This is useful research on privacy, but it cannot close our proof-budget or full-protocol blocker today.[^13]

**Our assessment:** defer this branch until a final decider, noninteractive security argument and serialized closure are available for the selected relation. Charge the final commitments, openings and decider to the QC. Putting them in a retained accumulator service would violate the portable extraction contract.

### 4.4 Co-design authorization with the proof

**Signatures of knowledge** replace the usual verification-key relation with a public statement whose witness authorizes signing. Chase and Lysyanskaya provide the foundational security concept. It is relevant when choosing a new authorization suite, rather than carrying a conventional signature verification circuit into a proof.[^14]

**Snarky Signatures** connects simulation-extractable NIZKs and signatures of knowledge. Its concrete construction uses pairings and is not a PQ backend candidate. The useful lesson is the chosen-message security obligation: an ordinary accepting proof of some relation does not automatically provide the signature security needed after observing other proofs/signatures.[^15]

**Loquat** is a proof-friendly post-quantum signature using the Legendre PRF. Its authors report about 148,000 R1CS constraints for verification with an algebraic hash, and 32-signature aggregates of 197 KB using Aurora or 145 KB using recursive Fractal. This supports changing the authorization relation to reduce proof cost, but its published aggregates do not meet our cap and do not include CE-QS tracing.[^23]

**Plum** develops the power-residue-PRF route with STIR and reports about 116,000 verification constraints. Its 128-bit comparison improves on Loquat. That is a potentially useful new signature suite, not compatibility with existing ML-DSA registrations or a measured 43-member conflict-extractable certificate. The accessible publisher preview gives no basis to infer exact full-QC bytes.[^24]

**Our assessment:** a new suite may remove ML-DSA verification as an implementation requirement, but it must preserve independent authorization secrets, message authorization and the original exposure contract. This revision specifies that alternative conditionally below; it does not silently migrate the running design.

### 4.5 Start from public double-sign tracing

The **post-quantum linkable-ring framework** of Xue and coauthors uses signatures of knowledge and includes a hash-proof route. Linkability detects reuse, whereas CE-QS needs identities of actual equivocators. This framework is a useful anonymous authorization component, not the public identity extractor by itself.[^16]

**Feng and coauthors' traceable-ring framework** is closer functionally. The institutional abstract describes lattice and symmetric-key instantiations with QROM security. It is a priority source for the public tracing abstraction. Its available evidence does not establish a joint 43-of-64 proof, our exposure policy, or an exact complete certificate below the cap.[^17]

The **group-action TRS** paper defines public tracing and offers logarithmic signatures. Its table at ring size 64 reports 13.87 KB for an isogeny instantiation and 61.37 KB for a lattice instantiation. Its proof model is the classical ROM. Bundling 43 such signatures plainly exceeds 32 KiB, even interpreting KB as 1,000 bytes. These are useful tracing mechanisms, not a qualified compact QPT quorum construction.[^18]

The **code-based TRS** of Qi and Wang offers a different assumption family. The full text states a ROM security theorem, and its first concrete parameter row reports 7.9×10^7 signature bits. This is already far above our budget for one signature. We do not infer QROM security from syndrome-decoding assumptions or use the paper's asymptotic logarithmic claim as a concrete size guarantee.[^19]

**Tetris** directly combines threshold signing, public double-sign tracing and extendability. Its construction uses Groth–Sahai proof techniques, making it a conceptual classical reference rather than a qualified PQ implementation. A PQ replacement must re-establish its composition properties; replacing a proof-system name does not preserve them.[^20]

**Liu's revised tracing paper** explicitly identifies a security-definition gap: traditional anonymity, linkability and exculpability notions need not imply unforgeability. It introduces stronger notions; its concrete short construction is DDH/Bulletproofs based. We adopt the separate unforgeability check as a review obligation, without claiming that every earlier TRS is insecure or that this paper supplies a PQ construction.[^21]

**Post-Quantum Traceable Anonymous Credentials from Lattices** requires secret tracing and judging keys in its interface. That is a different accountability model. It does not qualify for extraction solely from two QCs and fixed public configuration, regardless of its post-quantum credential properties.[^22]

**Our assessment:** public TRS provides the right behavioral reference, but aggregation, actual quorum authorization and exposure safety remain separate obligations. Reject authority-based opening as a replacement for public conflict extraction. Do not equate a reduction's secret witness extractor with the public forensic algorithm.

### 4.6 Share one signing key among many participants

**Ringtail** reports a two-round threshold signature with a 13.4 KB signature at a 1,024-party, 128-bit setting and a ROM reduction to LWE. This is useful evidence that PQ threshold authenticity can be compact. The resulting shared-key signature alone does not expose which 43 validators participated or prove that those contributors own the accompanying trace handles.[^25]

**Efficient Threshold ML-DSA** gives compatibility with ML-DSA and reports its evaluated small-party regime, up to six parties with average communication bounded by 1 MB per party. It does not establish a 43-party independent-key proof or its trace binding. Standard verifier compatibility does not supply those additional semantics.[^26]

**Our assessment:** these signatures may be ingredients in a redesigned system, but are not sufficient replacements for the missing joint authorization relation. An aggregate verification result and an unrelated trace proof cannot be accepted as one quorum certificate.

### 4.7 Distribute private proof generation and handle aborts

**Unmasking TRaccoon** adds identifiable abort to its particular threshold signing protocol. It reports extra communication of 60 + 6.4|T| KB when signing fails and formally analyzes a ZK variant of LaBRADOR. This is a useful model for making malicious failure attributable. It is not an automatic wrapper for arbitrary Binius or LaZer collaborative proving.[^27]

**CoSNIZK** protects selected provers' secrets in a collaborative setting, demonstrated by TPM/host direct anonymous attestation. The authors report a 38 KB DAA signature and a UC-oriented construction. Its segregated privacy model and two-role application cannot be assumed to give the 43-party, 21-fault behavior required here.[^28]

**Experimenting with Collaborative zk-SNARKs** shows how multiple parties can prove statements about distributed secrets, with concrete pairing-based experiments. Its architecture is relevant, but its proof sizes, communication costs and implementation optimizations cannot be imported unchanged into a PQ backend.[^29]

**Distributed-prover ZK work by Dayama and coauthors** offers a general IOP-based path to joint NP proving. It is a candidate compiler architecture. Mapping corruption, communication, output delivery and cost to the exact selected CE-QS proof protocol remains an implementation and proof task.[^30]

**Our assessment:** ephemeral proving messages are allowed; they become a forbidden sidecar only if later QC verification or conflict extraction needs them. Handle aborts separately from successful-certificate bytes. For liveness, explain how honest validators can replace provably faulty participants without losing all feasible 43-member quorums.

### 4.8 Replace portable certificates with network certification

**Byzantine Fault-Tolerant Post-Quantum Distributed Quorum Signatures** takes a different systems approach, using ordinary signatures and reliable-broadcast-style processing to make certification a local event. The indexed author abstract is relevant to consensus performance, but this changes the object the verifier relies on. It does not provide the required offline two-certificate artifact. Full text was not available through the research interface, so no stronger protocol claim is made here.[^31]

**Our assessment:** retain this as an alternative product contract only. It cannot be used to declare the original no-sidecar, portable-QC goal finished.

## 5. Exact deductions that resolve misleading shortcuts

### 5.1 The current encoding has a restricted size floor

The v1.17 evidence records two full 43-contributor **trace-component** frames, accepted by the unchanged original verifier. Their sizes are 776,736 and 785,456 bytes. The first decomposes as follows:

| Part | Bytes |
|---|---:|
| Current header and 43 handles | 4,288 |
| QVT1 header | 16 |
| Retained native prefix | 46,192 |
| Query field elements | 223,872 |
| Merkle boundary hashes | 494,176 |
| Terminal encoding | 8,192 |
| Total | **776,736** |

Therefore, with that native prefix and layout retained,

\[
|QC|\ge 4,288+16+46,192=50,496>32,768.
\]

The excess is **17,728 bytes even after hypothetically deleting all query and terminal data**. The prefix itself exceeds the entire target, so making the current handles smaller cannot by itself fix this restricted format either. This is arithmetic about measured serialized sections, not an information-theoretic bound on all representations or proof systems.

A new protocol that changes the prefix, an eligible whole-proof transformation, or a different backend remains possible. There is no evidence that simply increasing memory or lifting a diagnostic transport cap changes the original compactness verdict. The current full authorization relation has not been measured, so these trace-only numbers are not a full-QC benchmark.

### 5.2 Predefined columns do not implement arbitrary subsets

For a flat registry of 64 seats, the number of possible 43-seat quorums is

\[
\binom{64}{43}=41,107,996,877,935,680\approx 2^{55.19}.
\]

Naively giving every allowed subset its own 43-entry column would require **1,767,643,865,751,234,240 key references**. This calculation rules out naive enumeration as a practical way to reuse a predefined-column interface for this policy. It does not rule out an efficiently represented arbitrary-subset selection relation. Such a relation is precisely what a replacement proof must implement and price.

Even a headline 25 KiB component leaves only 2,880 bytes after adding our current 4,288-byte envelope. That arithmetic says nothing about whether missing trace, membership, privacy and composition work fits in the remainder. The entire joint proof must be measured.

### 5.3 Two independently valid existential proofs do not establish the same quorum

Suppose one proof establishes authorization by some 43-seat set S, while another establishes valid trace handles for some 43-seat set T. Without a binding connection, the statements imply only the existence of two sets. In a 64-seat registry they may differ in 21 seats each. Their guaranteed intersection of 22 does not make all 43 trace handles authorized.

This is a logical counterexample to the proposed composition rule, not an exploit against an implemented scheme. A correct construction must either use the same hidden seat variables throughout one relation, or prove equality of suitable binding commitments to those variables and their authorization data. Hiding those commitments, proving consistent openings and serializing the required proofs all have a cost.

For two **correctly bound** accepted QCs with signer sets S0 and S1, ordinary set arithmetic gives

\[
|S_0\cap S_1|\ge |S_0|+|S_1|-64=22.
\]

Turning that into 22 public accusations additionally requires the trace correctness and non-frameability theorems. The arithmetic alone does not identify anyone. The blame theorem must remain meaningful when a conflicting pair exists; it cannot assume away the very misbehavior it is meant to expose.

## 6. A concrete conditional architecture specification

The proposal below is a reviewable research specification. It is not a claimed implementation or a proof that a suitable backend meets the budget.

Let the public statement x bind the protocol version, authorization-suite identifier, fixed configuration digest, epoch, conflict domain, message and all 43 handles. Domain separation and canonical encodings must be part of the actual verifier and Fiat–Shamir transcript. A hidden witness contains 43 distinct indices and the trace material for those same indices.

### Mode A: preserve existing ML-DSA authorization

For each hidden seat i, the witness contains a valid ML-DSA-65 vote signature σi and trace material si. The relation enforces registry membership, exact signature verification on the protocol-defined vote bytes, exact trace-handle generation, and equality of the index used by all components. It must also enforce distinctness and canonical representation.

If the vote format binds an individual trace handle, verify that exact binding. If it signs only the message and domain, do not claim that it endorses an arbitrary complete handle list. Any change to the signed vote format requires an explicit versioned relation. External checks during fixture generation cannot replace these constraints.

This mode retains the current authorization interface. Its unresolved tasks are the full in-proof verification relation, a suitable proof backend and a complete measurement. A native Falcon or proof-friendly-signature result is not evidence of ML-DSA compatibility.

### Mode B: adopt a new independent authorization relation

Each registered seat has an authorization secret ai independent of its tracing secret si, with a public relation AuthRel(pki, ai). A properly defined signature-of-knowledge protocol jointly proves, on the complete message-bound statement,

\[
\exists\,(i_j,a_{i_j},s_{i_j})_{j=1}^{43}:\quad
\operatorname{Distinct}(i_1,\ldots,i_{43})\ \land
\bigwedge_{j=1}^{43}
\left[
\operatorname{Registered}(i_j,pk_{i_j},tk_{i_j})
\land\operatorname{AuthRel}(pk_{i_j},a_{i_j})
\land\operatorname{TraceRel}(tk_{i_j},s_{i_j},d,m,h_j)
\right].
\]

The fact that a message appears as an NP public input does not itself make this a secure signature. The complete SoK construction must bind that message and withstand the specified chosen-message interactions. A suitable multi-theorem QPT simulation-extractable construction is one sufficient route; a different direct security proof is acceptable if it actually proves the required game. Do not require a stronger primitive merely by name when a valid application-specific proof would suffice.

Authorization one-wayness must hold in the relevant multi-user, auxiliary-information and exposure setting. Each honest party's proving contribution must be tied to its explicit approval of x. A combiner that gathers all authorization secrets would destroy the intended operational separation even if the resulting proof verified.

This design removes conventional signature-verifier circuits only by adopting a new authorization suite and registration policy. It keeps ai separate from si, so learning si is not by definition learning the signing witness. That separation is necessary, not a proof of post-exposure security. The new suite still needs a complete reduction and a future-domain recovery policy.

### Acceptance predicate and public extraction

A verifier accepts only a canonical complete frame, within its configured total cap, whose proof establishes the selected complete relation at the pinned parameter set. It must reject unsupported suites, parameter downgrade, mismatched domains, duplicate seats, partial proofs and trailing unbound data.

The public extractor first verifies both complete QCs under the same relevant configuration and checks the conflict predicate. It then runs the public handle extractor and returns only identities for which the required trace evidence is satisfied. If a backend is unqualified or absent, the full-QC API must continue to reject or report unavailability. The trace-only diagnostic must not be promoted by renaming it.

## 7. Security obligations still requiring substantive work

The main remaining obstacle is a **joint construction and security qualification**, not a missing positive flag in the eligibility checker. Each item below needs evidence specific to the selected backend and authorization mode.

| Obligation | Required evidence |
|---|---|
| Authorization | A chosen-message QPT unforgeability/SoK argument and exact relation; approved votes and traced seats coincide. |
| Quorum integrity | Hidden registry membership and 43 distinct indices under the actual registration model, including malformed or adversarial registrations. |
| Public tracing | Correct recovery of every required intersection member from the two serialized QCs alone. |
| Non-frameability | A reduction covering honest parties who did not authorize both conflicting messages, not merely linkability. |
| Privacy | A compatible QPT privacy argument for public statements, repeated sessions, permitted leakage and collaborative transcripts. |
| Post-exposure behavior | Separate authorization/tracing keys and a proved or precisely scoped removal, rekeying or evolution policy. |
| Proof security | Exact CRS/QROM hypotheses, transcript binding, extraction, soundness and composition losses for pinned parameters. |
| Distributed production | A malicious-secure protocol with the stated fault threshold and a justified progress/abort recovery rule. |
| Compactness | A complete serialized certificate within 32,768 bytes; no omitted finalizer, opening or per-QC state. |

For the existing trace parameters, the local audit records dimension 256, q = 65,536, p = 256, 608 registration rows and 1,024 domains. The corresponding row exposure count used in the audit is

\[
608+1,024(608+48)=672,352.
\]

Balanced rounding and the uniqueness calculation are useful arithmetic checks. They do not establish 128-bit computational hardness. The small-modulus LWR literature gives reductions with conditions involving sample count, modulus and noise, including sample-preserving results. The actual distributions and exposure pattern must be matched to an applicable reduction and concrete attack-cost analysis; no such qualification is completed here.[^32]

The error budget must include proof soundness, authorization forgery, tracing failure, framing, hash/commitment failures and composition losses in the actual experiment. An asymptotically negligible bound is not a concrete 128-bit certificate. A native configuration labeled 96 cannot be relabeled 128, and a classical collision budget cannot silently become a quantum one.

The v1.4 conditional reduction structure remains useful, but its error symbols must be instantiated. In particular, a proof extractor used by that reduction may have powers the public forensic extractor does not. Those are different algorithms with different inputs and obligations.

## 8. Blocker disposition and next experiment

| Blocker or uncertainty | Status after this research revision | Next evidence required |
|---|---|---|
| Local memory for the existing 43-contributor trace prover | **Closed in v1.17 for two measured runs** | No re-opening without a new workload or concrete regression. |
| Whether query/path-only recoding can fit the retained format | **Resolved negatively** | Change the retained protocol/representation or backend. |
| Whether a concrete LaBRADOR ZK implementation exists | **Literature gap resolved** | Port the joint relation; reproduce and audit the selected implementation. |
| Which threshold semantics are admissible | **Resolved** | Arbitrary 43-of-64; do not substitute predefined columns. |
| Whether current trace knowledge supplies independent authorization | **Resolved negatively** | Mode A complete verification, or a new Mode B suite with independent secrets. |
| Complete 32 KiB QC | **Open** | Exact frame from a qualifying complete relation. |
| 128-bit QPT qualification of the composition and trace parameters | **Open** | Matching theorems, concrete losses and parameter analysis. |
| Collaborative proving and progress under 21 faults | **Open** | Implemented protocol with privacy, consistency and abort/robustness evidence. |
| Public recovery of 22 actual equivocators from two full QCs | **Open** | Two accepted complete QCs plus public extraction and non-frameability evidence. |

The next bounded experiment should produce a **costed, single joint relation in the current lattice ZK toolkit**, using arbitrary hidden indices. Start with the intended authorization mode explicitly declared. Include all trace computations and message hashing; do not substitute an authorization boolean, a public signer list, or a precomputed claim supplied by a trusted party.

Before a large prover run, produce a relation inventory and backend parameter sheet: private-variable count, equation and norm bounds, hash constraints, selection/distinctness constraints, public-input encoding, proof-system parameters and a conservative serialized-size accounting. A fixed mandatory section larger than the remaining budget is sufficient to stop that specific parameterization early. A favorable estimate is only permission to measure, not an acceptance result.

If that relation fits and its security mapping is defensible, generate two full conflicting fixtures with at least 22 common signers. Fresh verifier processes must consume only the public configuration and complete QCs. The public extractor must recover the actual shared authorized seats. Negative cases must cover duplicate seats, mixed authorization/trace witnesses, wrong vote bytes, changed handles, malformed signatures and cross-domain reuse.

Distributed proving should then run that same relation with protected private inputs and the specified abort behavior. A successful centralized benchmark remains useful for cost discovery, but cannot close that distributed-security gate. Conversely, a distributed protocol's successful execution does not replace the proof of non-frameability or QPT security.

This sequence prioritizes the unresolved construction question. It avoids repeating already sufficient memory tests or spending another iteration on an encoding whose retained prefix cannot meet the cap.

## 9. Reproducibility and claim boundaries

This revision adds a source ledger, the qualification report, a concrete acceptance-obligation file, an arithmetic and artifact-integrity checker, and its output. It preserves the prior review package byte-for-byte as historical members. No proof backend, vote verifier or full-QC acceptance path was modified.

The checker recomputes quorum combinatorics, current budget arithmetic, the retained-prefix floor, existing frame hashes and serialized section totals. It also checks the source inventory and report references. These are reproducible consistency checks, **not cryptographic proofs or new native verification runs**. The v1.17 native-verifier results remain separately identified historical evidence.

The local evidence still consists of two verified trace-component proofs, 27 successful public-pair diagnostic checks and recovery of 22 synthetic trace identities. Both complete trace frames exceed the original budget. The fixture's published signer sets make it a diagnostic fixture, not a privacy experiment. Valid full-QC count remains zero.

The review package contains the evidence at these relative paths:

| Evidence | Package path |
|---|---|
| Prior measurements, verification records and backend pin | `PQ_CE_QS_source_ledger_v1_17.json` |
| Executed public pair diagnostics | `continuation_v1.17/trace_pair_check_results.json` |
| Measured public frames | `continuation_v1.17/fixture/case0/trace43_rate1.tr16` and `case1/trace43_rate1.tr16` |
| Rounding and uniqueness audit, explicitly excluding hardness qualification | `parameter_audit.json` |
| Original exposure and tracing contract | `continuation_v1.18/contract_sources/frontier_v0_1.md`, §§14.6–14.9 |
| Earlier conditional collaborative security argument | `continuation_v1.18/contract_sources/collaborative_quorum_v1_4.md` |

The historical Binius64 source pin is `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4`. Native verification in v1.17 used the original verifier, not a modified acceptance rule. The new package manifest records hashes for the research additions; every historical archive member is compared byte-for-byte with the v1.17 package during assembly.

No universal impossibility claim, theorem-level audit of inaccessible papers, measured performance for an unported backend, or completed new CE-QS construction is asserted. The useful result is a narrower and better-supported next construction attempt, with explicit rejection of the shortcuts that would change the goal.

## Sources

The references below are primary sources. Access descriptions indicate the material examined, not a claim that every line or proof was audited.

[^1]: Jagganath et al.. *LoTRS: Practical Post-Quantum Structured Threshold Ring Signatures from Lattices*. NIST preview 0.1, 2026-05-18. [Primary source](https://csrc.nist.gov/csrc/media/Projects/threshold-cryptography/documents/TCall-1/LoTRS-PW02.pdf). Access: full text selected sections and table; checked 2026-09-09.

[^2]: Jeon, Abou Haidar, Tibouchi. *LastRings: Lattice-based Scalable Threshold Ring Signatures*. ISC 2025; received 2025-09-10. [Primary source](https://eprint.iacr.org/2025/1633). Access: primary abstract and metadata; checked 2026-09-09.

[^3]: Lyubashevsky, Seiler, Steuer. *The LaZer Library: Lattice-Based Zero Knowledge and Succinct Proofs for Quantum-Safe Privacy*. CCS 2024; received 2024-11-10. [Primary source](https://eprint.iacr.org/2024/1846). Access: primary abstract and metadata; checked 2026-09-09.

[^4]: Beullens, Seiler. *LaBRADOR: Compact Proofs for R1CS from Module-SIS*. received 2022-10-07; CRYPTO 2023 work. [Primary source](https://eprint.iacr.org/2022/1341). Access: primary abstract and metadata; checked 2026-09-09.

[^5]: Biasioli et al.. *A Toolkit for Succinct Lattice-Based Zero Knowledge Proofs*. received 2026-06-19; approved 2026-06-22. [Primary source](https://eprint.iacr.org/2026/1289). Access: primary abstract and metadata; checked 2026-09-09.

[^6]: Bolboceanu et al.. *Orthus: Practical Sublinear Batch-Verification of Lattice Relations from Standard Assumptions*. CRYPTO 2026; revised 2026-06-30. [Primary source](https://eprint.iacr.org/2026/398). Access: primary abstract and metadata; checked 2026-09-09.

[^7]: Feneuil, Rivain. *SmallWood: Hash-Based Polynomial Commitments and Zero-Knowledge Arguments for Relatively Small Instances*. revised 2026-02-13. [Primary source](https://eprint.iacr.org/2025/1085). Access: primary abstract metadata and author slides; checked 2026-09-09.

[^8]: Fenzi, Zhang. *zip: Reducing Proof Sizes for Hash-Based SNARGs*. 2025/1446, version observed 2026-09-09. [Primary source](https://eprint.iacr.org/2025/1446). Access: primary abstract and metadata; checked 2026-09-09.

[^9]: Arnon, Chiesa, Fenzi, Yogev. *WHIR: Reed-Solomon Proximity Testing with Super-Fast Verification*. 2024/1586, version observed 2026-09-09. [Primary source](https://eprint.iacr.org/2024/1586). Access: primary abstract and metadata; checked 2026-09-09.

[^10]: Chiesa, Fenzi, Weissenberg. *Zero-Knowledge IOPPs for Constrained Interleaved Codes*. received 2026-02-25. [Primary source](https://eprint.iacr.org/2026/391). Access: primary abstract and metadata; checked 2026-09-09.

[^11]: Chiesa, Di, Hu, Zheng. *How to Prove Post-Quantum Security for Succinct Non-Interactive Reductions*. EUROCRYPT 2026; revised 2026-03-02. [Primary source](https://eprint.iacr.org/2025/2166). Access: primary abstract and metadata; checked 2026-09-09.

[^12]: Nguyen, Setty. *Neo and SuperNeo: Post-quantum folding with pay-per-bit costs over small fields*. CRYPTO 2026; revised 2026-09-04. [Primary source](https://eprint.iacr.org/2026/242). Access: primary abstract and metadata; checked 2026-09-09.

[^13]: Dall'Ava. *LatticeBlindFold: A Lattice-Based Analogue of NovaBlindFold*. received 2026-09-01; approved 2026-09-03. [Primary source](https://eprint.iacr.org/2026/1857). Access: primary abstract and explicit scope statement; checked 2026-09-09.

[^14]: Chase, Lysyanskaya. *On Signatures of Knowledge*. CRYPTO 2006. [Primary source](https://www.microsoft.com/en-us/research/publication/on-signatures-of-knowledge/). Access: primary indexed abstract; checked 2026-09-09.

[^15]: Groth, Maller. *Snarky Signatures: Minimal Signatures of Knowledge from Simulation-Extractable SNARKs*. CRYPTO 2017. [Primary source](https://discovery.ucl.ac.uk/10039783/1/SESNARKCryptoFinal.pdf). Access: full text selected definitions; checked 2026-09-09.

[^16]: Xue, Lu, Au, Zhang. *Efficient Linkable Ring Signatures: New Framework and Post-Quantum Instantiations*. 2024/553, version observed 2026-09-09. [Primary source](https://eprint.iacr.org/2024/553). Access: primary abstract and metadata; checked 2026-09-09.

[^17]: Feng, Liu, Li, Li, Wu. *Traceable ring signatures: general framework and post-quantum security*. Designs, Codes and Cryptography 89, 2021. [Primary source](https://digitalcommons.njit.edu/fac_pubs/4090/). Access: primary institutional abstract; checked 2026-09-09.

[^18]: Wei, Luo, Bao, Peng, He. *Traceable Ring Signatures from Group Actions: Logarithmic, Flexible, and Quantum Resistant*. SAC 2023 preproceedings. [Primary source](https://sac-workshop.github.io/sac-2023/preproceedings/19WeiWei.pdf). Access: full text selected definitions and table; checked 2026-09-09.

[^19]: Qi, Wang. *A New Code-Based Traceable Ring Signature Scheme*. published 2022-04-29. [Primary source](https://onlinelibrary.wiley.com/doi/10.1155/2022/3938321). Access: full text selected definitions and table; checked 2026-09-09.

[^20]: Avitabile, Botta, Fiore. *Tetris! Traceable Extendable Threshold Ring Signatures and More*. ESORICS 2025; revised 2025-10-29. [Primary source](https://eprint.iacr.org/2025/730). Access: primary abstract and metadata; checked 2026-09-09.

[^21]: Liu. *Traceability for Free: Traceable Ring Signatures Revisited*. revised 2026-08-22; formerly Traceable Ring Signatures Revisited. [Primary source](https://eprint.iacr.org/2025/1807). Access: primary abstract and metadata; checked 2026-09-09.

[^22]: Chathurangi, Li, Foo, Zhang. *Post-Quantum Traceable Anonymous Credentials from Lattices*. CiC 2(4); accepted 2025-12-02. [Primary source](https://cic.iacr.org/p/2/4/12/pdf). Access: full text selected definitions; checked 2026-09-09.

[^23]: Zhang et al.. *Loquat: A SNARK-Friendly Post-quantum Signature Based on the Legendre PRF with Applications in Ring and Aggregate Signatures*. CRYPTO 2024. [Primary source](https://research.monash.edu/en/publications/loquat-a-snark-friendly-post-quantum-signature-based-on-the-legen/). Access: primary institutional abstract; checked 2026-09-09.

[^24]: Zhang et al.. *Plum: SNARK-Friendly Post-Quantum Signature Based on Power Residue PRFs*. ProvSec 2025; published 2025-10-10. [Primary source](https://link.springer.com/chapter/10.1007/978-981-95-2961-2_6). Access: primary publisher abstract preview; checked 2026-09-09.

[^25]: Boschini et al.. *Ringtail: Practical Two-Round Threshold Signatures from Learning with Errors*. 2024/1113; IEEE S&P 2025. [Primary source](https://eprint.iacr.org/2024/1113). Access: primary abstract and metadata; checked 2026-09-09.

[^26]: Celi, del Pino, Espitau, Niot, Prest. *Efficient Threshold ML-DSA*. 2026/013; USENIX Security 2026; replaces 2025/1166. [Primary source](https://eprint.iacr.org/2026/013). Access: primary abstract and metadata; checked 2026-09-09.

[^27]: del Pino, Katsumata, Niot, Reichle, Takemure. *Unmasking TRaccoon: A Lattice-Based Threshold Signature with An Efficient Identifiable Abort Protocol*. CRYPTO 2025; revised 2025-07-02. [Primary source](https://eprint.iacr.org/2025/849). Access: primary abstract and metadata; checked 2026-09-09.

[^28]: Chen, Hough, El Kassem. *Collaborative, Segregated NIZK (CoSNIZK) and More Efficient Lattice-Based Direct Anonymous Attestation*. received 2024-05-31. [Primary source](https://eprint.iacr.org/2024/864). Access: primary abstract and metadata; checked 2026-09-09.

[^29]: Ozdemir, Boneh. *Experimenting with Collaborative zk-SNARKs: Zero-Knowledge Proofs for Distributed Secrets*. USENIX Security 2022. [Primary source](https://www.usenix.org/conference/usenixsecurity22/presentation/ozdemir). Access: primary conference abstract; checked 2026-09-09.

[^30]: Dayama, Patra, Paul, Singh, Vinayagamurthy. *How to prove any NP statement jointly? Efficient Distributed-prover Zero-Knowledge Protocols*. 2021/1599; PETS 2022. [Primary source](https://eprint.iacr.org/2021/1599). Access: primary abstract and metadata; checked 2026-09-09.

[^31]: Kniep, Sliwinski, Wattenhofer. *Byzantine Fault-Tolerant Post-Quantum Distributed Quorum Signatures*. arXiv v1, 2026-07-20. [Primary source](https://arxiv.org/abs/2607.17700). Access: primary indexed abstract only; checked 2026-09-09.

[^32]: Bogdanov, Guo, Masny, Richelson, Rosen. *On the Hardness of Learning with Rounding over Small Modulus*. TCC 2016a; revised 2016-02-05. [Primary source](https://eprint.iacr.org/2015/769). Access: primary abstract and metadata; checked 2026-09-09.

[^33]: Ethereum repository maintainers. *spartan-whir reference implementation*. README observed 2026-09-09; benchmark record 2026-08-27. [Primary source](https://github.com/ethereum/spartan-whir). Access: primary repository readme and benchmark table; checked 2026-09-09.
