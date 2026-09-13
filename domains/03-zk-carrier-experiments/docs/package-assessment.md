# CE-QS v1.29: ML-KEM + ML-DSA authorization experiment

**ML-KEM-1024 and ML-DSA-87 now work together in a tested authorization component. They have not produced a complete 32 KiB, QPT-128, privately distributed CE-QS certificate.**

This update adds actual message approvals to an executable tracing relation, transports those approvals using real post-quantum primitives, and checks the separation between authentication and truthful tracing. All 51 component checks passed. Two conflicting synthetic statements each have 43 valid ML-DSA approvals; their trace equations recover the 22 common test signers. These are ordinary witness checks and a transparent signature audit, not zero-knowledge proofs or complete quorum certificates.

The Israeli and South Korean research reviewed below supplies useful components and design constraints. None of the reviewed results provides an already instantiated proof of this complete relation within the required certificate budget. The previous v1.28 proof-carrier experiment is preserved in this package; its proofs do not certify the new relation.

## 1. Give each primitive one precise job

| Object or function | Job in this design | Where its information belongs |
|---|---|---|
| `ML-KEM.Encaps/Decaps`, `(ek_j, dk_j)` | Establish a secret with a designated receiving participant | Authenticated configuration and production messages; `dk_j` stays private |
| HKDF-SHA-512 and AES-256-GCM | Derive a transport key and protect an approval | Production messages; not the public relation proof |
| `ML-DSA.Sign/Verify`, `(pk_i, sk_i)` | Authenticate an explicit approval by seat `i` | Public key in fixed configuration; approval signature can be a private proof witness |
| `t_i`, `K_T[i]` | Bind a member's stable tracing credential | Credential private; commitment in fixed configuration |
| `(L_i,Z_i)` | Carry the public information needed for conflict extraction | All 43 handles inside the QC |
| Hidden `i` | Tie authorization, registration, and tracing to the same seat | Inside the proof relation, with range and distinctness checks |
| `pi_R29` | Prove all these conditions together without revealing the authorizers | Inside the QC; this component is still missing |

FIPS 203 defines key establishment, and FIPS 204 defines signatures [S1, S2]. Sharing a lattice-based ancestry does not make the two algorithms interchangeable. Their polynomial moduli also differ: 3,329 for ML-KEM and 8,380,417 for ML-DSA. Adding their vectors or reusing their secret keys is not a valid composition. We use independently generated keys and compose the algorithms through their interfaces.

Both chosen parameter sets are NIST category 5. This is a conservative component choice for the requested quantum target, **not a theorem that the entire system has QPT-128 security**. NIST describes these categories through comparison with reference cryptographic problems, not one universal numerical security label [S1, S2].

## 2. Exact authorization relation

This is a new experimental suite, `CEQS29-M87-K1024`. It is not wire-compatible with CEQS12B. Let `H` be SHAKE256 producing 64 bytes with unsigned 64-bit, big-endian length prefixes on each argument. The authenticated, fixed registry has 64 ordered rows:

\[
\mathcal R[i]=(K_T[i],pk_i,ek_i),\qquad
K_T[i]=H(\texttt{CEQS29/trace-key},t_i).
\]

`C` hashes the suite and all registry fields in that fixed order. The reference rejects repeated keys within each registry column. Authentic enrollment, proof of possession where needed, and malicious registration handling are prerequisites; length and duplicate checks do not implement an enrollment protocol. The experiment generates every registry key honestly.

For a 64-byte context `d` and 64-byte direct message challenge `m`, define

\[
L_i\parallel R_i=\operatorname{SHAKE256}_{128\,\mathrm{bytes}}
(\texttt{CEQS29/pair}\parallel t_i\parallel H(\texttt{CEQS29/domain},C,d)),
\qquad Z_i=R_i+m(i+1).
\]

Arithmetic is in the retained binary field defined by `x^512+x^8+x^5+x^2+1`, using canonical big-endian field encodings. The direct message field is injective on 64-byte messages. If a larger application object is hashed into this field, that mapping adds a separate collision obligation. Context `d` must identify the intended protocol instance, such as epoch, height, and view.

Form a canonical public body `B` from the fixed suite, `C,d,m`, and exactly 43 handles sorted strictly by `L`. Member `i` signs

\[
A_i=\texttt{CEQS29/VOTE/v1}\parallel H(\texttt{CEQS29/body},B)
\parallel\operatorname{u8}(i)\parallel L_i\parallel Z_i,
\qquad \sigma_i=\operatorname{MLDSA87.Sign}(sk_i,A_i).
\]

This uses the pure ML-DSA external API with empty external context; the application domain is explicitly in the signed message. It is not an invocation of HashML-DSA. Members approve after the candidate handle list has been assembled, so changing the list requires new approvals. This extra approval phase avoids a circular dependency between signatures and the final proof.

The witness is `w=((i_j,t_j,sigma_j))` for 43 rows. The desired predicate `R29(B,w)` requires all of:

1. Authentic configuration binding and canonical public-body framing.
2. Exactly 43 distinct indices in `0..63`.
3. The trace credential opens `K_T[i_j]` at that index.
4. The public handle at that row equals the handle computed with that credential and index.
5. The same registry index selects the ML-DSA public key, and its signature verifies on `A_i`.

`authorization.py:check_witness` executes this predicate using ordinary cryptographic verification. It sees the witnesses. **There are still no ML-DSA verification constraints inside a generated succinct proof in this update.** A valid proof must encode the complete standardized verifier, including canonical signature parsing, response bounds, hints, and challenge recomputation. A linear equation about lattice vectors is insufficient.

## 3. Conditional accountability argument

Assume an authenticated fixed registry; consistent trace openings across the two proofs; distinct context links for different registered seats; an appropriate **joint QPT argument-of-knowledge extractor** for two accepted proofs of `R29`; and multi-user unforgeability of the member approval signatures in the required quantum model.

Extraction gives two sets `S_0,S_1`, each containing 43 distinct registry seats. Therefore

\[
|S_0\cap S_1|\ge 43+43-64=22.
\]

For a common seat, the context mask and link repeat while the message changes. Consequently

\[
\frac{Z_i^{(0)}+Z_i^{(1)}}{m_0+m_1}=i+1.
\]

The denominator is nonzero for distinct direct challenges. Correct relation proofs ensure that each recovered identity is the same index whose approval signature verified. If an uncorrupted member never approved one of the corresponding signed messages, extracting that signature yields a signature forgery, unless one of the binding or extraction assumptions failed. Signing the transport envelope is domain-separated from signing an approval, so it cannot itself supply that approval.

Schematically, with each term defined for the **whole experiment**, a failure bound would take the form

\[
\epsilon_{\mathrm{CE}}\le
\epsilon_{\mathrm{registry}}+
\epsilon_{\mathrm{body\mbox{-}binding}}+
\epsilon_{\mathrm{trace\mbox{-}binding}}+
\epsilon_{\mathrm{link}}+
\epsilon_{\mathrm{joint\mbox{-}extract}}+
\epsilon_{\mathrm{MU\mbox{-}approval}}.
\]

This is a reduction outline conditional on the missing proof system and precise security games. No numerical bound is claimed. Quantum query budgets, numbers of sessions and corruptions, reduction losses, adaptive corruption semantics, and setup assumptions must be supplied before evaluating these terms. Ordinary language soundness alone does not establish an approval event: valid signatures exist mathematically even when an adversary cannot compute them.

This accountability statement must also cover conflicting certificates produced when more than 21 members equivocate. The separate availability target with at most 21 faults does not restrict the forensic game to a regime where conflicting certificates should never arise.

## 4. ML-KEM transport that was actually executed

For every transmitted approval, the sender encapsulates a fresh secret to a registered recipient's ML-KEM-1024 key. HKDF-SHA-512 derives an AES-256-GCM key with the header and KEM ciphertext bound into the derivation. The associated data bind the suite-specific transport format, sender, recipient, session, complete body digest, recipient-key fingerprint, and KEM ciphertext. A fresh nonce is used with each independently established key.

An outer ML-DSA-87 signature authenticates the entire transport envelope. The receiving participant checks its signature, decrypts, and separately verifies the inner approval against the claimed sender and exactly one handle in the body. A duplicate-origin cache is updated only after all checks pass. This follows the KEM-plus-authentication separation described in SP 800-227; it is a custom experimental composition, not a claim of implementing a named standard channel protocol [S3].

The plaintext is an approval signature. No trace seed or signing secret key is passed to the recipient. The recipient does learn the sender and corresponding handle; this channel is **not anonymous to the recipient**, and the public audit deliberately publishes the synthetic approving seats. A private distributed prover still needs a protocol that protects the hidden witness and activity pattern. Sending a full credential encrypted to a coordinator would only protect it from outsiders, not from that coordinator.

ML-KEM uses implicit rejection: a changed ciphertext can lead to a different returned key. Therefore the experiment tests a changed KEM ciphertext even after giving the test sender a valid outer signature on the changed envelope. The AEAD check rejects it. The implementation also rejects an authenticated, successfully decrypted envelope containing an invalid inner approval.

The experiment assumes correctly installed keys, static receiving keys, classical protocol interfaces, and local session-state continuity. It does not establish forward secrecy, secure erasure, Byzantine agreement, verifiable secret sharing, or a quantum UC channel theorem. All synthetic private inputs are in one test process; none is written into the retained evidence.

## 5. What information must be inside 32 KiB

| Required public content | Representation in this candidate | Status |
|---|---|---|
| Suite, registry reference, context and message | Fixed 208-byte body header | Implemented |
| Publicly computable conflict evidence | 43 complete 128-byte handles | Implemented at equation level |
| Truth of the 43-seat authorization and trace relation | One private-witness proof `pi_R29`, with all commitments, openings and corrections | **Not implemented** |

The contents contract leaves 27,056 bytes for that proof. The ML-DSA approvals can remain inside its private witness; they need not all appear literally in the certificate. That is the sound way to aim for compactness. ML-KEM ciphertexts are production messages and need not be final-QC data **only if verification of the eventual complete QC is independent of them**. The current prototype has no such QC verifier, so it cannot yet claim the no-sidecar property.

A KEM shared secret can generate a large private random tape, and the test confirms matching expansion to 1 MiB. A public verifier cannot decapsulate from `ek` and the ciphertext alone. Publishing the shared secret makes that tape public; publishing a decryption or signing key defeats the corresponding secrecy requirement. Thus KEM expansion can help transport or preprocessing, but does not compress arbitrary public proof information. Shared randomness also is not automatically a Beaver triple, authenticated correlation, or proof of relation satisfaction.

Nor can the short seed used to generate an ML-DSA private key be published as a compressed approval. It regenerates the signing authority itself. The candidate needs a proof of valid hidden signatures, not a public decoder for members' private keys.

The v1.28 public proof carriers remain 273,952 and 270,304 bytes and certify a different predicate. They cannot be relabeled as proofs of `R29`. Moving the missing ML-DSA checks outside their verifier does not make them support actual authorization.

## 6. Research mapped to the remaining variables

Regional attribution below follows verified author affiliations, not the country of a conference or a website mirror. Findings were checked on 2026-09-09. These are eligibility judgments for this project, not claims made by the papers about CE-QS.

| Source and affiliation | Component or variable it helps | What can be carried forward | Limit here |
|---|---|---|---|
| **Aurora**, Ben-Sasson, Chiesa, Riabzev, Spooner, Virza, Ward; Technion/StarkWare coauthors in Israel [S4] | `pi_R29`, polynomial encoding and consistency | Encode the full predicate as one proof statement; use polynomial structure rather than literal witness transmission | The paper's example proofs and plausibly-PQ claim do not instantiate this 27,056-byte proof position or its QPT-128 reduction |
| **AIM / AIMer**, KAIST, Samsung SDS, Sungshin Women's University [S5] | A proof-friendly one-way relation and MPC-in-the-head views | Co-design the proved primitive and proof protocol to reduce nonlinear work | Replacing SHAKE tracing with AIM changes the scheme; a one-way function is not automatically the required context-dependent PRF. AIMer is not an ML-DSA aggregation proof |
| **HAETAE**, SNU/CryptoLab/ETRI and European coauthors [S6] | Short lattice signature responses and their distributions | Sampling and rejection analysis are legitimate ways to change a signature's representation | A different signature scheme, not a drop-in ML-DSA encoding or an anonymous 43-seat proof |
| **Secure Multi-party Matrix Invertibility Testing over Small Finite Fields**, Han–Lee–Park–Son, KAIST [S7] | Private arithmetic in a distributed computation | Make leakage and the ideal functionality explicit; the paper uses an arithmetic black-box with Shamir sharing | An invertibility subprotocol for MQ-related work, not a compiler for ML-DSA or this prover |
| **Quorus** [S8] | Distributed generation of standard-compatible ML-DSA signatures | Shows that standards-compatible threshold signing can use MPC | A signature under a group key still does not prove that the individual authorizers match these tracing handles |
| **Sometimes You Can't Distribute Random-Oracle-Based Proofs** [S9] | Distributed prover, extraction model, corruption threshold | Analyze the chosen random-oracle model before claiming a generic MPC compiler | Its stated barrier concerns all-but-one corruption with black-box restrictions; it is not an impossibility theorem for the 21-of-64 setting. The checked paper lists Brown/Silence affiliations, so it is not counted as Israeli research |

The useful fusion is therefore at the **predicate and protocol interfaces**: standard signatures provide extractable approval evidence; a suitable proof system hides and binds that evidence; a suitable MPC protocol constructs that proof privately; ML-KEM protects the production channels. Neither a paper's compression factor nor its security theorem transfers merely because another component also uses lattices or MPC.

For example, the classical honest-majority arithmetic `64 > 3*21` identifies a possible operating regime. It does not implement active-secure multiplication, private selection of 43 inputs, biased-abort handling, or a quantum-secure realization of the final prover. A committee of only 43 workers would not satisfy that same inequality for 21 faults.

## 7. Observed results and gates

The retained run generated 64 independent ML-DSA-87 key pairs, 64 independent ML-KEM-1024 key pairs, and 64 private trace seeds. Two cases used `0..42` and `0..21,43..63` as their approving sets. It created and checked 86 inner approvals and successfully transported all 86. The main cryptographic case work took approximately 1.45 seconds on this host; the entire component run took approximately 1.64 seconds. This is a local simulation, not a distributed performance measurement.

All 51 checks passed. They cover exact approval binding, missing and repeated authorizers, cross-context reuse, registered trace openings, transport authentication, decryption integrity, replay state, and the algebraic intersection. The public audit can be replayed independently using only public keys, bodies and signatures.

The decisive negative control constructs an incorrect trace mask and has the synthetic authorizers genuinely sign that incorrect body. **Signature-only auditing accepts; the full witness predicate rejects.** This does not attack ML-DSA. It demonstrates why replacing the predicate proof with ordinary or threshold signatures does not establish truthful tracing.

| Gate | Result |
|---|---|
| Actual ML-DSA approval predicate in executable reference | Implemented and tested |
| Authenticated ML-KEM transport of approvals | Implemented and tested as a local component |
| Same-seat authorization / trace binding in executable reference | Implemented and tested |
| Same checks certified inside a succinct ZK proof | **Open** |
| Complete QC at most 32 KiB | **Open** |
| Whole-system QPT-128 qualification | **Open** |
| Private distributed production robust to 21 faults | **Open** |
| Accepted complete original-goal QCs | **0** |

The next decisive implementation task is a circuit or native proof relation for the **full ML-DSA verifier plus same-seat tracing**, followed by an actual private proof with all bytes included. The present work resolves the executable specification of approval binding and validates the chosen transport primitives; it does not resolve that proof-engineering and cryptographic research task.

## 8. Reproduction and provenance

Run `sh reproduce.sh` from the extracted package root. It installs the bundled pinned `pqcrypto` wheel into a local `vendor` directory, replays the retained transparent signature audit, and runs the 51 checks with freshly generated synthetic keys. Python 3.12 on compatible x86-64 Linux, `cffi`, and `cryptography` are required. The recorded runtime used `cryptography` 46.0.0. Other platforms need their appropriate implementation build.

`pqcrypto` 0.3.4 supplies PQClean-derived native ML-KEM/ML-DSA implementations [S10]. The included wheel's SHA-256 was checked against the publisher's PyPI release metadata: `b2f9bad43a1e3970f55e6f68fc1864595c9b0c6e53638aa8393b1d01216a6ebb`. This identifies the executed implementation; it is not a conformance certification, side-channel audit, or new proof of the primitives' security. `dependency_provenance.json` records the exact release file.

New evidence retains only public synthetic registry keys, trace commitments, bodies, signatures, and results. The test process's private inputs are not retained. The previous package contents are preserved, with its root documentation under `history/`. Historical proof replays are separate from this new relation; see `reproduce_previous.sh`.

## Primary sources

- **[S1]** NIST, [FIPS 203: ML-KEM](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.203.pdf), final 2024, sections 3, 6–8. Algorithm roles, parameters, implicit rejection, and category interpretation.
- **[S2]** NIST, [FIPS 204: ML-DSA](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.204.pdf), final 2024, sections 4–6. The [current publication page](https://csrc.nist.gov/pubs/fips/204/final) also records pending errata. Standard algorithms and sizes were checked; this experiment is not a full errata/conformance audit.
- **[S3]** NIST, [SP 800-227: Recommendations for KEMs](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-227.pdf), final September 2025, sections 4 and 5.2. Secure use, authentication, KDFs and KEM-DEM.
- **[S4]** Ben-Sasson et al., [Aurora: Transparent Succinct Arguments for R1CS](https://eprint.iacr.org/2018/828.pdf), EUROCRYPT 2019. Abstract, theorem 1.2 and implementation section; [coauthor institutional page](https://www.dci.mit.edu/posts/aurora-transparent-succinct-arguments-for-r1cs-by-dcis-madars-virza-et-al) confirms Israeli affiliations.
- **[S5]** Kim et al., [AIM: Symmetric Primitive for Shorter Signatures with Stronger Security](https://eprint.iacr.org/2022/1387), CCS 2023. Author affiliations and abstract checked; PDF retrieval was unavailable, so no uninspected theorem or parameter table is credited.
- **[S6]** Cheon et al., [HAETAE: Shorter Lattice-Based Fiat-Shamir Signatures](https://eprint.iacr.org/2023/624), CHES 2024; [KpqC design document](https://kpqc.or.kr/images/pdf/HAETAE_Document.pdf). The two documents are not asserted to be byte-identical revisions.
- **[S7]** Han et al., [Secure Multi-party Matrix Invertibility Testing over Small Finite Fields](https://cic.iacr.org/p/3/2/33/pdf), IACR Communications in Cryptology 3(2), 2026. Abstract and functionality/leakage discussion.
- **[S8]** Bienstock et al., [Quorus: Efficient, Scalable Threshold ML-DSA Signatures from MPC](https://www.usenix.org/conference/usenixsecurity26/presentation/bienstock), USENIX Security 2026. Standard-compatible threshold output is the component claim used here.
- **[S9]** Doerner, Kondi, Rosenbloom, [Sometimes You Can't Distribute Random-Oracle-Based Proofs](https://eprint.iacr.org/2023/1381), CRYPTO 2024. Abstract and [author description](https://jackdoerner.net/research/) checked; PDF retrieval unavailable.
- **[S10]** [`pqcrypto` 0.3.4 publisher release](https://pypi.org/project/pqcrypto/0.3.4/). Pinned implementation provenance, not a research theorem.
