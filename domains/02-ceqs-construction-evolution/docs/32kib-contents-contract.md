# PQ CE-QS v1.24: define the 32 KiB contents, then prove them

9 September 2026. This revision follows the request to start with the certificate's required information and then choose a proof that validates it. The v1.23 fusion implementation and measurements are retained as supporting evidence. **The new contents contract is specified and reference-tested; a qualifying compact proof has not been produced.**

The proposed certificate contains just three semantic objects:

\[
\boxed{\mathrm{QC}=(\mathrm{context},\{(L_j,Z_j)\}_{j=1}^{43},\pi_{\rm joint})}.
\]

The context identifies the committee, conflict domain, message, and proof rules. The handles preserve the information a future public conflict extractor will need. One zero-knowledge argument of knowledge validates all handles and authorizations together. This is the proof target; there is no requirement to reproduce the internal transcript layout of the earlier backend.

**Contents are assigned by purpose, before selecting a proof system.**

| Object in the certificate | Why it must be available | Allocation in this design |
|---|---|---:|
| Context and framing | Bind verification to the exact registry, domain, message, relation, and canonical encoding | 208 bytes |
| 43 inline pairs \((L_j,Z_j)\) | Match repeated signers anonymously and recover identities from conflicting statements | 5,504 bytes |
| One complete joint proof | Prove distinct membership, credential knowledge, correct handles, and context binding while hiding the witness | Up to 27,056 bytes |

These are design allocations, not a measurement of a finished certificate. The header fields are `magic[4], version[2], suite[2], cfg[64], d[64], m[64], count[2], width[2], proof_length[4]`. All proof commitments, responses, openings, salts, and other data required by the chosen public verifier must fit inside the proof allocation. There is no additional proof file, omitted opening, or external leaf list.

This inventory assumes the verifier already possesses the **fixed authenticated 64-seat registry and approved verification parameters**, as in the existing system model. The registry is not certificate-specific. Its identifier authenticates a known registry; it cannot reconstruct an unknown one. If the requirement is instead that the certificate also transport an otherwise unavailable registry, those public keys must be included too, and this allocation would have to change. An unauthenticated registry carried by its purported signers cannot establish who the authoritative committee is.

**The certificate does not have to disclose its witness.** Seat indices, the three secret credentials for each selected seat, proof randomness, and the internal computation trace stay private. In the new hash-credential suite, separate per-signer signatures and leaf proofs need not be serialized. The full proof verifies credential knowledge directly. This choice does not establish ML-DSA compatibility.

The certificate also need not contain the signing protocol's communication transcript, an opener's secret, or a separate accusation proof for every recovered seat. Subject to the eventual security theorem, the two verified conflicting certificates and the public extraction calculation constitute the evidence. A single certificate still carries every public trace handle needed for that calculation. Replacing those handles with a digest would require a different publicly executable extraction mechanism; a digest alone does not supply the missing values.

**One redundant challenge hash can be removed.** The context already carries a canonical 64-byte message digest \(m\). Interpret those existing bytes directly as a field element:

\[
c_m=\operatorname{decode}_{\mathbb F}(m),\qquad
\mathbb F=\mathrm{GF}(2)[x]/(x^{512}+x^8+x^5+x^2+1).
\]

This encoding is a bijection between 64-byte strings and field elements. Therefore \(m\ne m'\Rightarrow c_m\ne c_{m'}\), without a further challenge-hash collision assumption. Every nonzero difference is invertible. Zero itself is a valid message challenge; division occurs only on a difference between distinct messages.

This change removes the extra map from message digest to challenge. It does not remove collision assumptions for an upstream raw-message digest, the registry, or the link hash. Configuration and domain remain bound through the handle equations and the proof statement. It is a **new relation family**, not a parser-only reinterpretation of a v1.23 proof.

For a hidden seat \(i\), retain independent credentials \(a_i,b_i,v_i\) and public registration keys

\[
K_L[i]=H(\texttt{link-key},a_i),\quad
K_R[i]=H(\texttt{mask-key},b_i),\quad
K_V[i]=H(\texttt{vote-key},v_i).
\]

Use the new domain-separated `CEQS124/` labels, an injective tuple encoding, SHAKE256 with 64-byte outputs, and a configuration identifier committing to this exact new relation and registry. Define

\[
L_i=H(\texttt{link-tag},a_i,\mathrm{cfg},d),\quad
r_i=\operatorname{decode}_{\mathbb F}H(\texttt{mask-pad},b_i,\mathrm{cfg},d),\quad
Z_i=r_i+c_m\operatorname{embed}(i+1).
\]

The repeatable link and mask depend on the domain, not the message. After verifying both conflicting proofs, match links and recover

\[
\widehat i=\operatorname{integer}\!\left((Z_i+Z_i')(c_m+c_{m'})^{-1}\right)-1.
\]

Accept only recovered field values representing identities 1 through 64, and only compare certificates with the same configuration and domain. The field was independently validated in v1.23; the new reference tests exercise zero, high-bit, and all-one message encodings. The recovery algebra needs no secrets, per-certificate sidecar, or intermediate proving transcript.

**The proof must establish this exact relation.** Let

\[
X=(\mathrm{cfg},d,m,(L_j,Z_j)_{j=1}^{43}),\qquad
W=((i_j,a_j,b_j,v_j))_{j=1}^{43}.
\]

The public parser establishes exactly 43 complete, canonically sorted handles and the expected context. The proof establishes that there exists a witness \(W\) satisfying all of the following:

1. Every \(i_j\) is an index in 0 through 63, and the 43 indices are distinct.
2. For each row, all three secret credentials open the three registered keys at that **same** index.
3. Each public link is computed from the registered link credential and this configuration/domain.
4. Each public masked identity is computed from the registered mask credential, the existing message bytes, and that same index.
5. Every public input is bound to the proof, including the complete handle list and the exact relation/suite.

The cryptographic requirement is a suitable **argument of knowledge**, not simply a short proof that an NP statement is satisfiable. The proof also needs the required zero-knowledge property. Actual authorization, non-framing, adaptive joint QPT extraction, and numerical QPT-128 losses must be established in the approval-oracle experiment. A parser, a witness checker, or a proof of possession without the appropriate message-binding security theorem does not discharge those obligations.

**A shared selector gives a concrete algebraic interface to a new proof.** This is a derivation for an odd-prime-field proof system, not a claim that the current binary-field backend already implements it. Give handle row \(j\) six private Boolean selector bits \(b_{j,k}\), and for public index \(i\) with bits \(i_k\), set

\[
e_{j,i}=\prod_{k=0}^{5}\big((1-i_k)(1-b_{j,k})+i_kb_{j,k}\big).
\]

For Boolean selector bits, this is exactly one at the selected index and zero elsewhere. The same \(e_{j,i}\) selects **all three** key tables, bit by bit:

\[
K^{(r)}_{j,\ell}=\sum_{i=0}^{63}e_{j,i}K^{(r)}_{i,\ell},\qquad r\in\{L,R,V\}.
\]

To enforce distinct seats, form column occupancies and constrain

\[
s_i=\sum_{j=1}^{43}e_{j,i},\qquad s_i(s_i-1)=0
\quad\text{in }\mathbb F_p,\quad p>43.
\]

Each integer occupancy is between 0 and 43. Because the field characteristic exceeds 43, its residue is zero or one only when the actual count is zero or one. Since there are 43 one-hot rows, exactly 43 different seats are selected. This proves the distinctness implication without exposing any bitmap. It replaces the logical pairwise inequality condition with column-occupancy conditions; selector construction has its own cost, so no whole-circuit performance improvement is asserted here. These equations must **not** be transplanted unchanged into characteristic two, where counts collapse to parity.

The public message also supplies a lookup table of the bits of \(c_m\operatorname{embed}(i+1)\), selected with the same coefficients. Thus identity scaling and registry membership cannot refer to different seats. Concrete SHAKE operations can be reduced to Boolean gates; over \(\mathbb F_p\), use

\[
z_{\rm AND}=xy,\qquad z_{\rm XOR}=x+y-2xy,\qquad b(b-1)=0.
\]

Products in the selector are decomposed into intermediate multiplication wires. These equations specify a route to a quadratic/R1CS relation. Full SHAKE arithmetization, wire binding, zero-knowledge masking, and the proof system's field/security parameters still need implementation and verification. The test field 101 checks the count equations only and is not a cryptographic parameter proposal.

**Distributed generation does not inherently require recursion.** A different architecture jointly computes the ordinary direct proof generator:

\[
(X,\pi)\leftarrow
\operatorname{MPC}\big[\operatorname{SelectAndProve}_{R_{43}}\big]
\big((\eta_i,a_i,b_i,v_i)_{i=0}^{63};\rho\big).
\]

Here \(\eta_i\) is seat \(i\)'s private approval of the exact public configuration/domain/message. Inside the secure computation, validate approving inputs against their authenticated seat slots, choose 43 valid approvals if available, create their sorted public handles, and run the ordinary randomized prover. Output only \(X,\pi\). Invalid or absent inputs do not count. Honest seats supply inputs only for statements they authorize.

In an ideal execution of this function, the output proof is an ordinary direct proof. It contains neither 43 proofs of individual contributions nor a proof verifying those proofs. A secure implementation must realize that function with suitable joint randomness, input privacy, correctness, and output delivery. This removes recursive verifier arithmetization from the **proposed architecture**, not from an already completed distributed implementation. It moves work to generation; it does not magically shorten an unsuitable underlying direct proof.

For robustness, keep **64 logical MPC participants** and count at most **21 corrupt or withholding participants in total**. The classical BGW threshold \(n>3f\) is numerically compatible: \(64>63\). A protocol involving only 43 parties cannot invoke that theorem to tolerate 21 Byzantine parties. Synchrony, authenticated private channels, active security, and the corruption model have to match the chosen MPC theorem. BGW's classical result is not by itself a completed quantum-composable instantiation. Unruh's quantum lifting theorem applies when the necessary statistical classical UC-security premise has first been established; it is not a rule upgrading every classical implementation automatically.

Protocol messages exchanged while generating the proof may be large. They are not part of later certificate verification or tracing. A scheme that needs those messages again to verify has failed this contract.

**Research selection now follows the relation, not advertised output sizes.**

| Research route | What it can contribute to the exact content contract | Missing qualification |
|---|---|---|
| Biasioli et al., *A Toolkit for Succinct Lattice-Based Zero Knowledge Proofs* (2026) | A concrete route combining succinct lattice proofs and witness privacy, exposed through LaZer | Compile and prove this complete hash/selector relation; establish the required QPT knowledge/security model and bounded transcript |
| Spartan-style constraints with WHIR openings | A general constraint proof plus a replaceable polynomial-opening layer | Correct field/Boolean compilation, complete zero knowledge, adaptive QPT extraction, and the exact proof-slot implementation |
| Ozdemir–Boneh collaborative proofs (2022) | Joint computation of one proof over distributed secrets | Their efficient implemented pairing-based choices are not PQ; their abort model does not establish our progress condition |
| Liu et al., scalable collaborative proofs (China-affiliated, 2025) | Shared and distributed multivariate prover operations | The paper explicitly leaves the malicious-privacy extension as future work; its prototype is not this robust PQ prover |
| Anada–Fukumitsu–Hasegawa (Japan, 2023) and Feng et al. (China-affiliated, 2021) | Separate authorization credentials and anonymous proof/PRF structure already used in the fusion | Their complete signature protocols and security results do not transfer to the modified relation |
| LoTRS structured threshold ring signatures | Reusable anonymous selection and multi-signature ideas | Its hidden-column policy proves a different quorum predicate; a fixed family of columns does not establish arbitrary 43-of-64 membership or this conflict relation |

The first two are candidate direct-proof routes, not selected qualified backends. The collaborative papers inform proof generation. In particular, using an MPC-friendly variant that outputs separate commitments/openings for every prover would change the intended one-proof interface and must be reassessed. No benchmark factor from these papers is treated as a substitute for a construction.

**The test scenario checks information sufficiency and the new formulas.** `continuation_v1.24/contents_contract.py` creates public deterministic test data for two 43-seat statements with exactly 22 common seats. It checks the entire witness relation in ordinary reference code, discards the witness from the public extraction inputs, and recovers exactly indices 0 through 21. It also tests 64 rotating arbitrary quorums, same-seat credential substitutions, incomplete trace handles, missing context, duplicate seats, changed messages, selector equations, and the MPC threshold conditions.

All **44 reference and contract checks passed**. They include the direct-challenge boundary cases and the guard preventing modular count wraparound. The ideal selection model produces 43 approvals with 21 missing inputs and refuses a 42-approval instance. This is an ideal-function test, not a networked MPC run. No dummy proof was written, and no placeholder-filled 32 KiB object was accepted.

`contents_contract.json` records every public, private, fixed-setup, and generation-only object; `public_statement_examples.json` contains the unproved public examples; `contents_check_results.json` records the checks. The v1.23 package preserves seven actual native proofs of the earlier hashed-challenge relation. They remain useful evidence for that relation and **are not proofs of the revised v1.24 relation**.

The contents-first result is therefore concrete: a complete statement inventory, a simpler injective challenge, an explicit shared-selector proof relation, and a direct collaborative-generation architecture. The remaining construction target is precise: **one self-contained, zero-knowledge, appropriately QPT knowledge-sound proof of this full relation inside the reserved proof slot, with a secure distributed prover**. The present work does not yet supply that cryptographic proof.

**Primary sources and scope of access.**

1. [Biasioli et al., *A Toolkit for Succinct Lattice-Based Zero Knowledge Proofs*](https://eprint.iacr.org/2026/1289). Primary abstract and authors' [LaZer repository](https://github.com/lazer-crypto/lazer) inspected; PDF fetch unavailable. No uninspected theorem is used.
2. [Client-Side Proving team's WHIR design document](https://hackmd.io/@clientsideproving/whir-based), a living first-party research document; [WHIR paper](https://eprint.iacr.org/2024/1586). Candidate interface only.
3. [Ozdemir and Boneh, USENIX Security 2022](https://www.usenix.org/system/files/sec22-ozdemir.pdf). Full paper, introduction and sections 3–5; distinguishes generic MPC proving, aborts, and concrete implementations.
4. [Liu et al., USENIX Security 2025](https://www.usenix.org/system/files/usenixsecurity25-liu-xuanming.pdf). Full paper, introduction and section 7, including its stated malicious-security limitation.
5. [Ben-Or, Goldwasser, Wigderson, STOC 1988, author-institution record](https://cris.huji.ac.il/en/publications/completeness-theorems-for-non-cryptographic-fault-tolerant-distri/). Primary abstract supplies the Byzantine threshold; no UC-security theorem is inferred from it.
6. [Unruh, *Universally Composable Quantum Multi-Party Computation*](https://kodu.ut.ee/~unruh/publications/quantum-uc.html). Author abstract and [publisher record](https://doi.org/10.1007/978-3-642-13190-5_25); lifting used only with its stated premise.
7. [LoTRS author preview hosted by NIST](https://csrc.nist.gov/csrc/media/Projects/threshold-cryptography/documents/TCall-1/LoTRS-PW02.pdf). Full preview; the hidden-column quorum definition is the relevant distinction, not its headline size.
8. The full Chinese/Japanese trace and credential sources, quantum-proof ledger, and 53-component mapping are retained in `continuation_v1.23/sources.json` and `component_map.md`, with direct primary-source URLs.
