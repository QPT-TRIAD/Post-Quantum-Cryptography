# CE-QS v1.26: attempts to close the three remaining requirements

**Result: no construction meeting all three requirements has been established.** This update checks concrete alternatives to the v1.25 prover, including small lattice proofs, newer distributed lattice signatures, and a quantum-secure proof transformation. It identifies a missing binding property that prevents a simple threshold-signature replacement from solving the problem. The new executable work is an ideal-interface composition model, not another cryptographic proof or an MPC implementation.

The v1.25 artifacts remain two verified experimental proofs of the exact 43-seat relation, with public recovery of 22 shared test identities. Their verification does not establish QPT-128, a 32 KiB certificate, or actual distributed authorization. The full v1.25 proof report is preserved verbatim later in this document so that the established results and their limits remain reviewable.

## 1. Requirements retained

The accepted target is a publicly verifiable certificate with 43 distinct hidden authorizers out of 64, no per-certificate sidecar or secret opener, conflict extraction of at least 22 actual shared authorizers, ordinary signer privacy, QPT-128 security, and robust generation with a total of at most 21 faulty or withholding participants after the required network conditions hold.

The current contents contract contains a 208-byte header, 43 full 128-byte handles, and one complete proof of at most 27,056 bytes. A different construction may integrate this information differently, but must preserve its semantics. Neither an experimental verification flag nor a statistical model check changes any requirement.

## 2. The compact-threshold-signature replacement needs an additional theorem

A tempting construction is to replace the large relation proof with a compact distributed signature on the entire body:

\[
B=(C,d,m,\{(L_j,Z_j)\}_{j=1}^{43}),\qquad
\Sigma=(B,\operatorname{ThresholdSign}(B)).
\]

This does bind the signature to the chosen body. It does **not**, from threshold unforgeability alone, establish that the claimed handles describe the same 43 authorizers who produced that signature.

**Composition obstruction.** Suppose the only semantic check performed by the public certificate verifier is ordinary threshold-signature verification, alongside syntax checks on the body. Suppose also that a qualified coalition can sign arbitrary bodies. Then threshold unforgeability alone cannot imply the CE-QS tracing and nonframing property for bodies chosen by that coalition.

**Reason.** The coalition can choose a well-formed body that is not a valid encoding of its participation. Signing that body is an authorized use of the underlying signature interface; it is not a signature forgery. Therefore a reduction that treats the resulting attribution error as a violation of threshold unforgeability has no valid final step. Body authentication and truth of the body relation are separate properties.

The executable model grants *perfect* body authentication and threshold checking. It uses a 43-seat authorizing coalition `0..42` for two different messages. The first body claims seats `21..63`; the second claims seats `0..20` and `42..63`. Both claimed sets have size 43. Their claimed intersection has 22 seats, `42..63`, although 21 of these seats are outside the actual coalition. Both bodies can be authenticated in that ideal interface. This is a countermodel to the proposed implication, not an attack on Hermine, Quorus, ML-DSA, or v1.25.

The model uses **43 corrupt authorizers**, outside the 21-fault liveness regime. It is relevant to a forensic/nonframing guarantee that must remain meaningful when enough members misbehave to cause conflicting certificates. If the application's accountability game instead restricts the adversary to 21 total corruptions, this countermodel does not break that game. In that restricted game, however, a safety theorem ruling out conflicting certificates cannot by itself establish useful attribution after a larger compromise. The two scopes must be stated separately.

The precise extra property needed is:

\[
\mathrm{Accept}(B,\Sigma)\Longrightarrow
\text{a publicly enforceable, extractable binding between the handle witnesses
and the message authorizations of the same distinct seats.}
\]

It must hold in the stated accountability corruption model. Adding an honest-party check during normal signing is insufficient to obtain this stronger public property from a generic signing interface when the signing coalition is malicious. A relation-restricted or accountable signing primitive could supply the property, but it would need its own construction and proof. No such compiler has been instantiated here.

## 3. Primary-source candidates and what they actually provide

Sources were checked on 2026-09-09. “Not established” below is a statement about this CE-QS instantiation, not a claim that the paper is incorrect or that all future constructions are impossible.

| Candidate | Verified contribution | Remaining incompatibility or obligation |
|---|---|---|
| **LUNA**, Steinfeld et al., CCS 2024, [ePrint 2022/1690](https://eprint.iacr.org/2022/1690) | Its primary abstract reports designated-verifier lattice arguments below 6 KB at its stated 128-bit security/privacy setting; an argument-of-knowledge variant requires stronger assumptions. | Verification requires a designated verifier. Publishing its secret verification material or adding a committee endorsement is not an established public-verification compiler. Its numbers do not instantiate the CE-QS relation or certify our QPT-128 profile. |
| **Hermine**, Borin et al., [ePrint 2026/419](https://eprint.iacr.org/2026/419), revised 2026-08-20 | The abstract reports support for up to 64 parties, roughly 11 KB signatures, identifiable abort, and proactive security. | A promising distributed-signing component. Its ordinary output does not by itself prove the CE-QS handle/authorizer relation. Its signature size is not the size of a qualified CE-QS certificate. |
| **Quorus**, Bienstock et al., [ePrint 2025/1163](https://eprint.iacr.org/2025/1163) | Provides an MPC-friendly ML-DSA variant with signatures accepted by the standard verification algorithm. | A signing functionality, not the CE-QS private relation prover. Its [NIST preview](https://csrc.nist.gov/csrc/media/Projects/threshold-cryptography/documents/TCall-1/Quorus-PW01.pdf), section 2.3, explicitly promises security with abort and leaves adaptive corruption and identifiable-abort discussion to later specification work. That preview cannot establish guaranteed delivery for our protocol. |
| **Efficient Threshold ML-DSA**, [ePrint 2026/013](https://eprint.iacr.org/2026/013) | Primary abstract describes a practical ML-DSA-compatible construction for small groups, benchmarked up to six parties. | This is not evidence for our 43-of-64 run. It supersedes the ML-DSA portion of withdrawn ePrint 2025/1166. |
| **A Toolkit for Succinct Lattice-Based Zero Knowledge Proofs**, Biasioli et al., [ePrint 2026/1289](https://eprint.iacr.org/2026/1289) | Provides a concrete implementation adding zero knowledge to LaBRADOR; the [authors' repository](https://github.com/lazer-crypto/lazer) gives benchmark commit `59a52f74ca39584edf77b4b8b7437dbd48f9ad94`. | Potential proof-backend work, but no actual proof of this exact relation within 27,056 bytes has been produced. The full PDF was unavailable through the retrieval path used in this update; no parameter-table claim is inferred from its abstract. |
| **RoKoko**, [ePrint 2026/575](https://eprint.iacr.org/2026/575) | A lattice argument with structured recursion, linear-time prover, and published abstract reporting proofs around 200 KB. | These reported experiments do not close the current complete-proof slot. They are not a lower bound for every relation or parameter regime. |
| **Privacy-Preserving Aggregate-Signatures**, Wei, Han and Liu, Shanghai Jiao Tong University, [ePrint 2026/836](https://eprint.iacr.org/2026/836) | Generic transformation with concrete SpeedyMuSig- and BLS-derived instantiations. | The named concrete instantiations do not supply a post-quantum CE-QS backend. “Pairing-free” alone is not a PQ qualification. |
| **Katsumata, A New Simple Technique to Bootstrap Various Lattice Zero-Knowledge Proofs to QROM Secure NIZKs**, AIST Japan, [CRYPTO 2021 paper](https://iacr.org/archive/crypto2021/12826193/12826193.pdf) | A semi-generic transformation for applicable lattice HVZK protocols to QROM NIZKs. | It is not a blanket theorem for the selected Binius/Spartan/BaseFold composition. Applying it would require a matching base protocol, all hypotheses, concrete losses, and resulting proof data. |

The withdrawn [ePrint 2025/1166](https://eprint.iacr.org/2025/1166) explicitly points to Hermine and Efficient Threshold ML-DSA as successors. It should no longer be treated as the authoritative current specification.

## 4. Distributed authorization: precise function, still no implementation claim

The retained architecture can avoid giving an aggregator members' credentials by computing the **ordinary direct prover inside secure MPC**. Its target function should be pinned as follows:

\[
\mathcal F_{\mathrm{CE\text{-}Prove}}(C,d,m;\{\mathrm{input}_i\}_{i=0}^{63}).
\]

Each authenticated private input port belongs to exactly one registered seat and supplies an approval of the exact `(suite,C,d,m)` context plus that seat's private credentials. The function checks credential registration, retains only valid approvals, privately selects exactly 43 distinct eligible seats, constructs the sorted handles, obtains unbiased private prover randomness, and evaluates the full proof generator. It releases only the final public frame and specified failure information. It does not release the witness to a coordinator.

This **function definition** resolves what distributed authorization must compute. It does not provide a maliciously secure protocol for computing it. The reference model accepts 43 approvals with 21 absent ports, refuses 42 approvals, rejects approval reuse across a different message/domain, and does not count 43 copies of one origin as a quorum. These are interface checks, not tests of network authentication or MPC privacy.

For a classical BGW-style honest-majority route, the 64-party condition is `64 > 3·21`; the same claim is false for a 43-party computation with 21 corruptions. Even with 64 parties, sharing alone is not enough. A degree-21 sharing can have a reconstruction code capable of correcting 21 erroneous shares, whereas multiplying two sharings naively creates degree 42 and loses that error-correction margin. Verifiable degree reduction or an equivalent malicious-secure multiplication protocol remains essential.

A complete instantiation also needs the actual quantum/adaptive corruption model, authenticated private channels, stated network synchrony, input commitment, robust multiplication, output delivery, and suitable composition theorem. Security with abort preserves some safety/privacy properties but does not establish progress against a participant who can repeatedly halt the run. Identifiable abort from a different signing protocol cannot be imported as a blame mechanism for this proof computation without a reduction.

## 5. QPT-128: the theorem cannot be supplied by relabeling parameters

The pinned v1.25 backend still uses the 96-bit parameter recorded in its source. Its quantum argument-of-knowledge security for this composition has not been instantiated. Increasing the application hash output, setting a label to 128, or reporting successful verification on test inputs would leave the missing theorem untouched.

A meaningful concrete claim requires a pinned resource profile and a proved inequality covering joint knowledge extraction, credential security, handle consistency, zero knowledge for the public view, and the distributed protocol. A possible *organizational form* is

\[
\operatorname{Adv}_{\mathrm{CE}}(\mathcal A)
\le \epsilon_{\mathrm{proof}}+\epsilon_{\mathrm{credential}}+
\epsilon_{\mathrm{tag}}+\epsilon_{\mathrm{MPC}}+
\epsilon_{\mathrm{channel}}.
\]

This displayed form is **not a completed security reduction**. The terms, simulators, extraction dependencies, adversarial resource bounds, and constants still need to be derived for the actual protocols. Quantum security is not established merely because each component's abstract uses the phrase “post-quantum.” Nor is a 128-bit work-factor target equivalent to failure probability at most `2^-128` at every possible adversarial query budget.

## 6. What the new tests establish

Fourteen ideal-model assertions passed. They establish:

- Perfect threshold authentication does not imply correctness of the asserted participant relation.
- The illustrative over-threshold countermodel must not be reported as a 21-corruption break.
- Exact approval context and distinct authenticated origins are necessary in the distributed target function.
- The 64-party arithmetic threshold is suitable for the cited class of MPC designs, while the 43-party substitution and naive multiplication shortcut are not.

They establish no new cryptographic proof, QPT bound, networked MPC execution, or complete QC. The model and exact result are embedded below for reproduction with ordinary Python.

## 7. Outcome

I have not solved the three requirements together. The current proof implementation remains a useful relation prototype, not a deployable compact PQ quorum signature. No impossibility theorem for the full target has been established either.

The concrete missing object is a publicly verifiable, QPT-qualified, compact proof or relation-restricted signing construction that binds the same 43 distinct private authorizations to every public conflict handle, together with a robust distributed generator. The compact signing papers and small designated-verifier proofs examined here do not supply that object by simple composition. Treating them as if they did would silently weaken the stated security requirements.
