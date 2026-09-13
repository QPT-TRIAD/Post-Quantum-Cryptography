# CE-QS v1.27: smaller binding relation, with actual proofs

**Four retained new experimental cryptographic arguments verify. The final candidate reduces the 43-seat circuit by about 55% while preserving separate tracing and authorization credentials. It does not satisfy the complete compact PQ quorum-signature target.**

The final pair identifies the expected 22 shared test seats using only the authenticated public configuration and complete inline frames. Eighteen public mutation controls reject. The frames are 283,680 and 279,600 bytes, QPT-128 has not been established, and the prover remains centralized. There are zero complete QCs satisfying all original requirements.

This is a focused experiment following v1.26, not a replacement for the full historical review package. Candidate A and candidate B are new relations with new suite identifiers. Neither is a security-equivalent substitution for v1.25 without further analysis.

## 1. What changed and what information remains

The retained target is 43 distinct hidden authorizers among 64 seats, publicly identifiable overlap of at least 22 after a conflict, ordinary signer privacy, no secret opener, no per-certificate sidecar, QPT-128 security, a 32,768-byte complete certificate, and robust distributed generation with up to 21 faults in the specified network/corruption model.

The experiment combines the link and mask derivation into one 128-byte SHAKE output from a tracing seed. An independently generated authorization seed remains necessary in every circuit witness. Candidate B also prehashes the public configuration/domain context and uses unambiguous fixed-width private hash inputs. It does not shorten either half of a tracing handle or remove a credential check.

| Required information | Final candidate B representation |
|---|---|
| Registered member universe and suite | Authenticated fixed public configuration with two ordered key tables; its recomputed fingerprint is in the frame |
| Exact conflict context and message | 64-byte configuration fingerprint, 64-byte domain, 64-byte canonical message |
| Public conflict extraction data | All 43 full `(link, masked identity)` pairs, each 128 bytes |
| Same-seat trace/authorization binding | One hidden index selects both registered keys and the scaled identity |
| Distinct authorization witnesses | Exactly 43 hidden indices, checked with a private occupancy map |
| Complete public verification evidence | One inline QVT1 representation of the entire native proof transcript |

The intended frame still has a 208-byte header, 5,504 bytes of handles, and at most 27,056 bytes for the whole proof. The public context digest introduced below is recomputed; it needs no new frame field or sidecar. The fixed registry is shared configuration, not a per-certificate evidence service. Its authenticity and legitimate seat assignment remain application prerequisites.

## 2. Exact final relation: CEQS12B_FIXED_CONTEXT

All output lengths below are **bytes**. Define

\[
H_{\rm lp}(P_1,\ldots,P_k)
=\operatorname{SHAKE256}\!\left(\big\Vert_{j=1}^{k}
\bigl(\operatorname{u64be}(|P_j|)\Vert P_j\bigr),64\right).
\]

For each seat `i` in `0..63`, independently generate 48-byte seeds `t_i` and `v_i`. Register

\[
K_i^T=\operatorname{SHAKE256}(\texttt{CEQS12B/tracekey}\Vert t_i,64),
\qquad
K_i^V=\operatorname{SHAKE256}(\texttt{CEQS12B/vote-key}\Vert v_i,64).
\]

Both literal labels are 16 bytes. Registration inputs are therefore exactly 64 bytes. Define

\[
C=H_{\rm lp}(\texttt{CEQS12B/config},M,
K_0^T,\ldots,K_{63}^T,K_0^V,\ldots,K_{63}^V)
\]

with exact metadata

```
FIXED-CONTEXT-PAIR/DIRECT-CHALLENGE/GF512/64/43/2x48/v1.27b
```

The verifier recomputes `C`, checks the exact parameters and the two 64-entry registries, and rejects duplicate keys within either registry. For a 64-byte conflict domain `d`, set

\[
D=H_{\rm lp}(\texttt{CEQS12B/context},C,d).
\]

For each selected seat, compute

\[
L_i\Vert R_i=\operatorname{SHAKE256}
(\texttt{CEQS12B/pair-tag}\Vert t_i\Vert D,128),
\]

where `L_i` and `R_i` are each 64 bytes. The input has the fixed partition `16 || 48 || 64`, totaling 128 bytes. It is injectively encoded; length prefixes are unnecessary for this fixed tuple.

Use

\[
\mathbb F=\mathbb F_2[X]/(X^{512}+X^8+X^5+X^2+1).
\]

Field bytes use big-endian polynomial-basis encoding. Addition is XOR. Let `e_i` be the field element with integer representation `i+1`. For a canonical 64-byte message `m`, let `c(m)` be its direct field decoding and set

\[
Z_i=\operatorname{Decode}_{\mathbb F}(R_i)+c(m)e_i.
\]

The body is `(C,d,m,[(L_j,Z_j)]_{j=0}^{42})`, sorted strictly by `L_j`. The private witness has exactly 43 rows `(i_j,t_j,v_j)`. Every row must satisfy both registration equations and the pair/masked-identity equations at the **same** index. All indices must be in range and different.

Zero messages are allowed. Different canonical 64-byte messages always yield different field challenges. If a larger application message is first hashed into these 64 bytes, that upstream message-binding property is a separate obligation.

**This is still a credential-preimage relation.** Its witness includes an authorization credential; witness existence alone does not establish a fresh approval event or a signature-of-knowledge theorem.

## 3. Why the circuit is smaller

The SHAKE256 specification uses the 1,600-bit Keccak permutation with capacity 512 bits, hence a 1,088-bit/136-byte rate. Its output can extend beyond a fixed digest length. These properties follow from [FIPS 202, sections 5.2 and 6.2](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.202.pdf). The following circuit optimization is our construction, not a CE-QS theorem from that standard.

The two 64-byte registration inputs each need one permutation. The 128-byte paired input and its padding fit in one rate block; its 128-byte output also fits in that block's output. Thus candidate B needs three private Keccak permutations per seat. The public computation of `D` is part of verification/circuit specialization and is not a private-witness hash circuit.

The v1.25 relation used seven permutations per seat: three registration hashes plus two two-block tracing hashes. Intermediate candidate A uses two registration hashes plus one two-block paired hash, for four permutations. Candidate A retains the length-prefixed private encoding and includes `C,d` directly in that paired hash. Its exact equations are in `continuation_v1.27/paired_reference.py`.

| Measured quantity | v1.25 baseline | Candidate A | Candidate B |
|---|---:|---:|---:|
| Private permutations per seat | 7 | 4 | 3 |
| Private 64-bit witness words | 817 | 559 | 559 |
| Case 0 gates | 899,429 | 521,717 | 402,306 |
| Case 1 gates | 904,933 | 527,221 | 407,810 |
| Allocated committed words, both cases | 262,144 | 262,144 | 131,072 |
| Native proof bytes, each case | 339,200 | 339,104 | 335,360 |
| Complete frame bytes, case 0 | 289,664 | 287,648 | 283,680 |
| Complete frame bytes, case 1 | 287,712 | 281,232 | 279,600 |

These are fixed-profile individual runs with fresh inputs/randomness, not average benchmarks or an optimality claim. Message-dependent constants account for the two circuit sizes. Native proof sizes barely change despite the large circuit reduction.

## 4. Predicate equivalence and conditional extraction proof

**Circuit lemma.** Assuming the documented native word-gate semantics and correctness of the Keccak gadget, the final circuit has a satisfying witness exactly when the canonical body satisfies the relation in section 2.

*Proof.* The constraint `i >> 6 = 0` restricts a witness word to `0..63`. Six selectors read its six index bits. Reusing those selectors in both registered-key lookups, the identity-scaled-message lookup, and the one-hot occupancy lookup makes all four selections refer to the same seat.

Let `E_j=1<<i_j` and initially `O_0=0`. The circuit checks `O_j & E_j = 0` before setting `O_{j+1}=O_j XOR E_j`. Induction shows that `O_j` records exactly the prior selected seats, so a repeated seat fails before its bit could cancel. This is bitwise occupancy, not a characteristic-two sum of counts.

The hash circuit puts the six private seed words at word offset 2, after the 16-byte label. It applies SHAKE's byte suffix/padding and the concrete Keccak gadget. Its first eight or sixteen output words supply exactly the required hash bytes. Both registered-key equalities and every public handle equality are constrained. Conversely, a relation witness supplies these private words and makes all equalities and occupancy checks pass. Canonical ordering and exact lengths are also checked by the host parser. ∎

The configuration, domain, and message specialize the public circuit; handles are its explicit public input words. Rebuilding the correct circuit is mandatory. A cached verifier for another context cannot be reused. This is an implementation-level argument plus independent execution checks, not a machine-checked compiler proof.

**Consistent-opening condition.** For the particular two satisfying witnesses, repeated seats use the same tracing seed, and different seats have different links in the fixed context. This condition is computationally motivated, not mathematically guaranteed by a finite hash. Alternative preimages for a registered tracing key or cross-seat link collisions need bounds in a complete security game.

**Conditional conflict theorem.** If two canonical bodies satisfy the final relation, use the same authenticated `C,d`, have different canonical messages, and satisfy the consistent-opening condition, public extraction returns exactly their common witness-seat identities, at least 22 of them.

*Proof.* The two witness sets each contain 43 distinct elements of a 64-element universe, so their intersection has size at least `43+43-64=22`. For any common seat `i`, identical `t_i,C,d` give identical `D,L_i,R_i`. Consequently

\[
Z_i+Z'_i=(c(m)+c(m'))e_i,
\qquad
\boxed{e_i=(Z_i+Z'_i)(c(m)+c(m'))^{-1}}.
\]

The denominator is nonzero by injective message decoding. The condition on distinct seats excludes false link matches. Every match therefore recovers its actual common witness index. ∎

`audit_results.py` independently checks the field modulus using the Rabin irreducibility criterion: `X^(2^512)=X mod f` and `gcd(X^(2^256)-X,f)=1`; 2 is the only prime divisor of 512. The reference fixture work checks 384 Python field vectors. The full native witness checks additionally match the independently computed handles in both 43-seat cases. The retained native selector/scaling unit-test source was not rerun in this update.

The public extractor verifies both entire experimental proofs before applying the equation, requires matching contexts and different messages, and rejects out-of-range or insufficiently distinct outputs. Turning this witness theorem into attribution of **actual equivocating authorizers** still requires the authorization/extractability reduction described below.

## 5. What is still too large inside the proof

The final proof position contains an exact QVT1 reconstruction of the complete native transcript. The decoder invokes the normal upstream verifier and transcript finalization after reconstruction. It does not accept a hash of an unavailable proof, omit queries, or treat the native `.proof` audit copy as a required external input.

| Encoded proof component | Candidate B case 0 | Candidate B case 1 |
|---|---:|---:|
| Native prefix | 16,384 | 16,384 |
| Transmitted queried field values | 81,376 | 80,304 |
| Merkle boundary hashes | 179,168 | 176,160 |
| Terminal coefficients | 1,024 | 1,024 |
| Codec header | 16 | 16 |
| Complete encoded proof | 277,968 | 273,888 |

This gives a specific diagnosis beyond the final size. **In these retained transcripts, the transmitted field values alone exceed the entire 27,056-byte proof position.** Hypothetically assigning every boundary hash zero cost, while retaining the current field-value/prefix/terminal representation, would still leave 98,800 and 97,728 bytes of proof.

The hypothetical zero-cost calculation is accounting, not a valid verifier modification or an information-theoretic lower bound. Query overlap is transcript-dependent. It does not exclude another encoding, commitment, proof protocol, or relation-restricted signature construction. It does show that eliminating private hash permutations and reducing Merkle-path duplication has not addressed enough of the remaining information cost in this implementation.

An effective next proof construction must reduce the queried-value representation as well as authentication data, while retaining the same relation checks and a proved quantum soundness/knowledge bound. Reusing the current verifier while silently dropping those values would fail its checks.

## 6. Security assumptions changed, and obligations still open

| Obligation | What this experiment establishes | What is still required |
|---|---|---|
| Same-seat binding predicate | Both independent credentials and each complete handle are constrained at one hidden index | An adaptive multi-session signature-of-knowledge/extractability result tying accepted proofs to fresh approvals |
| Tracing consistency | Conditional algebraic theorem; two verified test pairs recover the expected overlap | Concrete registered-preimage consistency and link-collision bounds in the accountability corruption model |
| Paired-output privacy | Exact 128-byte derivation implemented | Joint pseudorandomness of `(L,R)` given registered tracing keys and permitted exposures, plus composed proof privacy |
| Public context prehash | Recomputed by both implementations; changed contexts rejected | Context/configuration binding bounds, including collisions in the new public digest `D` |
| QPT-128 | No new qualification | A concrete resource model and complete bounds for the actual proof, hashes, credentials, approval protocol, channels, and composition |
| Distributed generation | Private input shape reduced; intended function unchanged | Actual maliciously secure distributed prover with credential privacy, authorization, and required output delivery |
| Complete 32 KiB certificate | All necessary semantics remain represented inline | A whole proof fitting 27,056 bytes with the required security properties |

A single-domain zero-message handle reveals `R_i`, and a conflict reveals `i` and the same mask output. These equations do not output `t_i` or `v_i`; this observation is not a proof of seed-recovery hardness. The authorization seed remains independently generated and has its own registration check. Deriving `L` and `R` as halves of one XOF output adds a joint-output assumption; it is not justified by treating the halves as independent standard hashes. Their correlation with public keys and other transcripts must be analyzed.

The backend is based on Binius64 commit `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4`, with the retained v1.17 prover memory/recomputation patch. The complete experimental source, patch, and prior patch-validation note are included. This is not a pristine upstream checkout. Its `crates/verifier/src/verify.rs` has `SECURITY_BITS = 96`; the standard suite uses SHA-256 and internal `Ghash128b` arithmetic. Its ZK backend contains a Spartan wrapper and BaseFold machinery. Those components and their complete verification data remain in the proof. Larger application hash outputs do not qualify this backend for QPT-128, and there is no instantiated quantum argument-of-knowledge composition theorem here.

Actual authorization remains stronger than a relation witness. The required game must account for prior approvals/proofs, exact message/domain binding, corrupted seats, and framing attempts. A general proof of knowledge for an isolated statement is not automatically the needed multi-session authorization theorem.

For distributed generation, the target function still receives seat-authenticated approvals of the exact `(suite,C,d,m)` and private credentials; it privately selects 43 valid distinct seats, computes the handles, and generates the complete proof with private unbiased randomness. A 64-party MPC realization with 21 faults is the relevant honest-majority architecture; substituting only 43 total MPC parties while claiming the same `n>3t` guarantee is invalid. No such MPC realization was executed in this experiment. Merely collecting all credentials at a coordinator would defeat the retained distributed-privacy requirement.

Thus the three named original blockers remain open. The closed implementation item is narrower: a substantially smaller, explicit credential/handle binding relation with actual publicly verifiable experimental proofs.

## 7. Execution and reproducibility

Two fresh configurations were generated, one for each candidate. Each used 128 independent `os.urandom(48)` draws. Native proof randomness came from the backend. Each test configuration produced:

- Case 0: seats `0..42`, with the zero message.
- Case 1: seats `0..21` and `43..63`, with message field value `2^511+17`.

Both candidate implementations passed 11 native constraint controls per case. These cover valid witnesses, range, changes to either seed, seat reassignment, altered handles, other-seat credentials, repeated complete contributions, and mixed link/mask contributions. Each independent reference suite passed 15 recorded checks, including 64 rotating quorums at an all-one message and the 384 field vectors.

For each candidate, both private witness files were deleted after proving and before encoding/public verification: 8,944 bytes total per candidate. This is file-removal evidence, not a secure-storage erasure claim. The prover held all selected credentials in one process; expected signer identities are public test provenance, so this is neither a distributed run nor an empirical anonymity experiment.

Both candidate pairs verified from fresh directories containing only their respective frame, with a nonexistent private input path and the public configuration. The native `.proof` files were absent from those verification directories. Candidate B additionally rejected 18 public mutations, including a changed domain in both frame and configuration, a changed registry with a recomputed configuration fingerprint, and a proof transplanted from the other message. These go beyond rejecting inconsistent headers.

Final candidate binary SHA-256:

```
dfa90585c22c692a66b6bc9ab689ec1c44e68cb7b128e9bd883ce265930975c5
```

Final frame SHA-256 values:

```
dd77def56fe25a11e265a759053070f93a3e6bc8d25028e25ecaf23267706a40
fb1ac2ef59e6147e50d87410aed96c74c52d766c163c3d7baf4e57832c602a2c
```

From the package root, run `sh reproduce.sh` to verify both retained pairs, rerun candidate B's public negative controls, and audit the field/accounting records. The included binaries were built for this Linux x86-64 host with `target-cpu=native`; another host may require rebuilding. Backend source and both adapter lockfiles are included. Third-party Cargo dependencies and the Rust toolchain are not bundled.

To build the final adapter with an installed compatible Rust toolchain:

```bash
cargo build --locked --release --manifest-path continuation_v1.27b/adapter/Cargo.toml
cp continuation_v1.27b/adapter/target/release/ceqs-fixed-pair-v127b continuation_v1.27b/bin/
```

Use `python3 continuation_v1.27b/regenerate.py --output NEW_DIRECTORY` to generate and verify a fresh test pair in a new directory without overwriting retained fixtures. Rebuilding changes the binary digest, and fresh proof randomness changes frame hashes; retained hash-evidence audits refer specifically to the shipped experiment. The fresh-pair regeneration command was also executed successfully in a separate directory: both fresh frames verified, the expected overlap was recovered, all 18 public controls rejected. A post-process workspace audit found its private files present despite the in-process deletion record; a separate cleanup removed them. Their reappearance is unexplained. The helper now asserts absence immediately after deletion and at completion. This cleanup discrepancy affects the extra regeneration test, not the four retained proofs: their private-file absence was checked separately before public verification. This additional reproduction run does not qualify the protocol. The full historical review archive is not included in this focused package; v1.25 comparison records and its report are retained for context.
