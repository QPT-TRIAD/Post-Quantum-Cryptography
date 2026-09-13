# CE-QS v1.28: algorithms as information carriers

**The carrier idea works for structured data, and a new carrier now works on the real retained proofs. It has not produced a complete 32 KiB CE-QS certificate.**

This update searches for generative and algebraic representations, implements two new public proof codecs, and tests a seeded-data demonstration. The stronger proof codec replaces the final queried polynomial layer and its authentication paths with 512 polynomial coefficients. The native verifier accepts the reconstructed proofs. The complete frames are 273,952 and 270,304 bytes, down from 283,680 and 279,600 bytes.

No new signing credentials or native proofs were generated in this update. Both codecs transform the public proofs retained from v1.27b. QPT-128, actual distributed authorization, and the full 32 KiB requirement remain unresolved.

## 1. What an information-carrying algorithm must provide

Let `x` denote the public configuration and complete public statement, and let `pi` be the native proof. A lossless carrier is an efficient pair of algorithms

\[
c=E(x,\pi),\qquad D(x,c)=\pi.
\]

The verifier runs the fixed decoder and then the original verification algorithm:

\[
V_c(x,c)=V(x,D(x,c)).
\]

The carrier need only transmit independent information; the decoder may regenerate everything determined by that information and `x`. A fixed, public algorithm is shared across certificates. Per-certificate programs, coefficients, seeds, dictionaries, model weights, corrections, and algorithm parameters are certificate data and must be counted. A pointer to an unavailable program or proof is not reconstruction.

For the retained contents contract, the 208-byte header and 43 full 128-byte tracing handles leave **27,056 bytes** for the complete proof carrier. Computation can replace transmitted redundancy. It cannot recover information absent from both the carrier and public input.

A different, generative proof protocol may create its proof data as

\[
\text{proof data}=G(x,s,\delta),
\]

where `s` is a short seed description and `delta` contains the corrections that make the generated data satisfy the required relation. It must also authenticate those data, prove the exact 43-seat relation, and preserve privacy. The size of the seed alone is not the size of such a proof.

## 2. Algorithms and research mapped to the required information

Sources were checked on 2026-09-09. The eligibility judgments below are our assessment of this CE-QS task; published component results are not claimed as a complete CE-QS instantiation.

| Algorithm or research direction | Information it can carry | Assessment for this task |
|---|---|---|
| **Seed trees / puncturable pseudorandom generation**, as used in [FAEST v2, sections 2 and 5](https://faest.info/faest-spec-v2.0.pdf) | Many generated random tapes from a small set of seeds, while selected tapes remain unopened | Strong match for designing a generative proof protocol. Cannot be pasted over arbitrary existing Binius query values. The full commitments, corrections, and relation proof still matter. |
| **MPC-in-the-head with preprocessing**, [Katz–Kolesnikov–Wang, 2018/475](https://eprint.iacr.org/2018/475) | Preprocessed protocol views and consistency evidence for Boolean-circuit knowledge proofs | A protocol family to investigate, not a byte codec or a distributed authorization implementation. Its signature measurements do not instantiate this relation. |
| **Polynomial interpolation and erasure recovery**, [Lin–Chung–Han, 1404.3458](https://arxiv.org/abs/1404.3458) | A codeword through a lower-dimensional polynomial representation | Directly applicable to the sufficiently sampled final layer. The implementation here uses Newton interpolation; it does not implement the paper's optimized erasure decoder. |
| **Additive NTT / binary-field polynomial commitments**, [Diamond–Posen, 2024/504](https://eprint.iacr.org/2024/504) | Polynomial coefficients and evaluations connected by deterministic transforms | Supplies the existing backend's algebraic setting. We reuse the pinned implementation to obtain the correct evaluation coordinates. |
| **Affine dependency elimination** | Values determined by public linear equations | Implemented as QVT2: reconstruct a missing coordinate from a known outgoing fold. |
| **WHIR**, [2024/1586](https://eprint.iacr.org/2024/1586) | Checks polynomial relations through a different, smaller-query protocol | Potential replacement for the opening protocol. Requires a full adaptation, ZK treatment, and qualified parameters; not an existing-proof decompressor. |
| **Khatam**, [2024/1843](https://eprint.iacr.org/2024/1843), and [BaseFold in the List-Decoding Regime](https://eprint.iacr.org/2024/1571.pdf) | Stronger proximity analysis that can reduce required proof communication | Relevant to a justified query schedule. No query was removed on the strength of an uninstantiated theorem in this experiment. |
| **HyperFond**, [2025/1349](https://eprint.iacr.org/2025/1349) | Distributed construction of a BaseFold-based proof | The authors report experiments on up to 16 machines. This does not by itself establish private 43-of-64 authorization or robust delivery with 21 malicious participants. |

FAEST specifies a generative commitment structure and a QROM analysis for its own scheme. That is a useful architectural precedent, not a QPT theorem for a SHAKE/CE-QS substitution. Its specification also discusses the exact scope of its QROM model. Likewise, polynomial commitment zero knowledge needs explicit treatment; [Diamond's binary-field ZK note, 2025/1015](https://eprint.iacr.org/2025/1015) gives a component construction, not a blanket guarantee for every disclosure of polynomial coefficients.

There is a specific reason to avoid blindly adopting aggressive WHIR parameters: [Crites–Stewart, 2025/2046](https://eprint.iacr.org/2025/2046) disproves the **up-to-capacity** mutual correlated agreement conjecture, among other conjectures. This is not a claim that every WHIR parameterization is insecure. A replacement must identify and use the actual proved regime and its error terms. Khatam's current abstract reports a factor-two proof-size improvement in its setting; that factor cannot simply be applied to our complete frames or multiplied with another paper's improvement.

## 3. Tested generative carrier: 588 bytes reconstruct about 1 MiB

`seed_carrier_demo.py` implements a demonstration with 1,024 generated leaves, excluding one leaf. A canonical tree frontier contains ten 48-byte seeds. With its 108-byte header/checksum, the carrier is **588 bytes**. Its decoder reconstructs 1,023 leaf seeds and expands them into **1,047,552 bytes** of tapes.

Five cases with different excluded positions reconstruct exactly and reject truncation, trailing bytes, and an altered seed against the recorded checksum. No member credentials are used. The excluded leaf is absent from the decoder's output; this finite check is not a proof of computational hiding.

**This is a seeded-data demonstration, not a quorum certificate, FAEST implementation, authenticated commitment, or generic compressor.** The checksum is consistency data, not proof of authorship. Its strong expansion ratio comes from generating the data from seeds in the first place. It does not identify a short seed whose expansion equals an arbitrary old proof.

## 4. First real-proof carrier: QVT2 affine reconstruction

In the final FRI layer, the original verifier checks a linear fold

\[
y=\sum_{j=0}^{b-1}w_jv_j,
\]

where `y` is determined by the terminal codeword. Terminal polynomial coefficients were already fully present in QVT1. QVT2 moves their representation before the query data in the carrier; it still feeds the reconstructed native transcript to the verifier in its original order.

Select a deterministic coordinate `p` not already known, with nonzero weight. Reconstruct it by

\[
v_p=w_p^{-1}\left(y-\sum_{j\ne p}w_jv_j\right).
\]

This sends one fewer field element per eligible final-layer leaf. If no eligible pivot exists, the codec retains the necessary values and checks the fully determined equation. In the two retained proofs it recovers 104 and 102 additional field elements, saving 1,664 and 1,632 bytes. Both decoded native proofs are byte-for-byte identical to their originals.

QVT2 is retained under `continuation_v1.28`. Its frame magic is `PF28`, version 28, suite `0x28b3`. Its full native verifier, relation, Fiat–Shamir transcript, and security parameter are unchanged.

## 5. Stronger real-proof carrier: QVT3 polynomial reconstruction

The final queried oracle in this profile has 4,096 field elements, represented by a polynomial of degree below 512 over the backend's binary field. The two retained proofs reveal 832 and 816 distinct evaluation values in their final-layer leaves, before removing deterministic redundancies. Thus each view already supplies more than the 512 evaluations needed for interpolation.

The encoder chooses the first 512 queried positions in canonical order. Let their public coordinates be `x_0,...,x_511` and values be `y_0,...,y_511`. It constructs the Newton representation

\[
p(X)=\sum_{k=0}^{511}a_k\prod_{j=0}^{k-1}(X-x_j).
\]

The carrier transmits the **512 coefficients**, occupying 8,192 bytes. The decoder regenerates the coordinates using the pinned additive NTT, evaluates `p` at all 4,096 positions, and rebuilds the entire Merkle tree of this oracle. It can then reconstruct every queried leaf, every authentication path, and the native layer data.

The implementation uses batch inversion in Newton divided differences. It uses an NTT transform of a degree-one basis vector to obtain the actual evaluation coordinates, avoiding an assumption that array indices themselves are field coordinates. The encoder compares all reconstructed query values and all previously supplied Merkle nodes with the original public proof. It also checks equality of the **entire expanded native transcript**. A wrong degree assumption, coordinate order, field representation, or tree reconstruction would fail these comparisons.

When the public sample count is insufficient for this polynomial form, QVT3 retains the affine representation. For the tested profile, both final layers use the polynomial form. Other layers retain their prior representation. Transmitting full coefficients of an insufficiently sampled private oracle is not an approved substitution: those coefficients might reveal information absent from the old public proof.

QVT3 is under `continuation_v1.28p`. Its frame magic is `PF2P`, version 28, suite `0x28c3`. It uses the same `CEQS12B_FIXED_CONTEXT` relation as v1.27b. The retained binary's SHA-256 is

```
77f4c11c4521729557f09fd3e8a5a09a3d73a54d82ef762fe7ded392416b181e
```

## 6. Why this preserves the checked statement

**Correctness argument.** For distinct evaluation coordinates, the degree-below-512 polynomial interpolating the selected values is unique. When the codec's public reconstruction checks succeed, every supplied final-layer value and authentication node equals the original. Other transcript components are retained or reconstructed by the previous exact codec. Thus the decoder recovers the original native proof.

**Acceptance argument.** The public entry point always invokes the ordinary native verifier and requires transcript exhaustion on the reconstructed proof. Therefore acceptance of a carrier implies acceptance of its expanded proof for the same statement, assuming correct implementation of that entry point. Interpolation is not substituted for proof verification. The codec only restricts the accepted representation; it does not add a new authorization predicate.

**Privacy argument, conditional on the original system.** The carrier encoder uses only the old public proof and public statement. Its output is efficient public postprocessing, so it cannot disclose information unavailable to an observer able to perform that same computation. If the original proof distribution has a suitable ZK simulator, applying this public encoder to that simulator preserves its indistinguishability, with the encoder's failure behavior included. This does not establish a ZK or QPT theorem for the unqualified backend itself.

These are construction arguments supported by exact replay and finite negative tests, not a machine-checked implementation proof or a completed authorization/security reduction.

## 7. Actual results and remaining information

| Representation | Case 0 complete frame | Case 1 complete frame |
|---|---:|---:|
| Previous QVT1 | 283,680 bytes | 279,600 bytes |
| QVT2: affine terminal reconstruction | 282,016 bytes | 277,968 bytes |
| QVT3: final-layer polynomial carrier | **273,952 bytes** | **270,304 bytes** |
| Target | 32,768 bytes | 32,768 bytes |

The QVT3 final layer occupies 8,192 bytes instead of 17,920 and 17,488 bytes in QVT1. It therefore saves 9,728 and 9,296 bytes overall. This is an actual representation change on real proofs, not a projected benchmark from a paper.

Both QVT2 and QVT3 versions verify in fresh subprocess directories receiving only the authenticated public configuration and complete frame bytes. Their expanded native-proof SHA-256 values equal the originals. Public conflict extraction recovers exactly seats `0..21`. QVT2 rejects 20 public negative controls; QVT3 rejects 22, adding polynomial-coefficient corruption and the earlier affine codec magic. No private witness file is supplied or created by this codec experiment.

Generic compression also round-tripped the old complete frames, but increased their size: DEFLATE produced 283,746 / 279,671 bytes, bzip2 285,250 / 281,232, and XZ 283,752 / 279,672. Every queried-field section had full 128-bit binary span in the raw representation. Those observations reject these particular compression approaches as useful here; they are not an entropy proof or an impossibility theorem about other algorithms.

QVT3 still carries 78,080 / 77,248 bytes of field coefficients and queried values, 172,736 / 169,920 bytes of Merkle boundary hashes, and 17,424 bytes of prefix, terminal, and codec data. Even hypothetically assigning all remaining boundary hashes zero cost would leave 95,504 / 94,672 proof bytes. This is accounting for these retained representations, not a lower bound against another protocol.

## 8. The route toward 32 KiB

The strongest architectural match to the requested idea is a **generative proof with selective seed disclosure and authenticated corrections**, combined with algebraic representations wherever the public data are redundant. This is a research direction, not an instantiated CE-QS protocol.

A candidate must provide all of the following inside its complete proof position:

\[
|\text{opened seed description}|+|\text{corrections}|+
|\text{binding/consistency evidence}|+|\text{other proof data}|\le27{,}056.
\]

Its verification must still enforce the same 43 distinct hidden seats, both registered credential preimages at each seat, all link/mask equations, and exact context/message binding. The seed openings must conceal the appropriate private views. The proof's consistency mechanism must bind the generated data to those credentials. Any new query schedule needs a matching soundness analysis, including the quantum transformation and concrete losses.

An algorithm containing the witness as constants would be small here—the old private witness file was only 4,472 bytes—but would disclose member credentials and identities. Publishing the prover's blinding seeds without an applicable hiding proof can have a similar problem. Neither is a valid compact CE-QS construction. Encrypting them for a secret decoder would change public verification.

A fixed decoder has only as many fixed-length `b`-bit descriptions as there are such bit strings, so it cannot losslessly represent every longer arbitrary string. This elementary counting argument does **not** rule out a 32 KiB CE-QS proof: valid proof distributions and redesigned protocols can be highly structured. It explains why the successful seed demonstration and the limited compression of old proofs are compatible.

The immediate result is an implemented polynomial carrier, not completion of the 32 KiB goal. The current backend still uses its 96-bit parameter and has no instantiated QPT-128 qualification for this composition. The codecs do not implement distributed authorization.

## 9. Reproduction and retained evidence

The updated archive preserves the previous v1.27 material and adds both new codecs, public frames, source, measurements, and the seeded-data demonstration. Previous root documentation/validation are preserved under `history/`.

Run `sh reproduce.sh` from the extracted archive root. It verifies both new representation pairs, tests the final carrier's public negative controls, checks expanded-proof hashes against the originals, and decodes the retained seed demonstrations. It does not require member credentials. The native binaries were built for this Linux host with `target-cpu=native`; other hardware may require rebuilding from the included adapters and pinned patched backend. Cargo dependencies and the Rust toolchain are not bundled.

The source/replay checks establish correctness for the retained cases. They do not claim that every imaginable proof is compressible, that published improvement factors compose, or that any complete original-goal certificate has been generated. That count remains zero.
