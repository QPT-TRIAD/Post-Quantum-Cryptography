# CE-QS v1.25: actual cryptographic proofs of the v1.24 relation

Two new 43-seat cryptographic arguments have been generated and independently verified. They implement the v1.24 contents-first relation, including its direct, injective message challenge. Public extraction from the two verified frames recovered exactly seats 0 through 21. Verification used the public registry and complete inline frame bytes after the two private witness files were deleted.

This closes the missing **working prover/verifier for the v1.24 relation**. It does not close the original compact PQ quorum-signature goal: these experimental frames exceed the 32 KiB envelope, the pinned backend has a 96-bit security parameter rather than a qualified QPT-128 theorem, and a distributed authorization protocol has not been implemented. The number of complete QCs meeting all original requirements remains zero.

## 1. What has been built

| Component | Implementation and evidence |
|---|---|
| Exact v1.24 configuration and hash labels | `adapter/src/trace.rs`, cross-checked against `continuation_v1.24/contents_contract.py` |
| One shared hidden seat selector | Six selector wires reused for all three credential tables, the message-scaled identity table, and the occupancy indicator |
| 43 distinct seats | Private 64-bit occupancy map; no repeated seat can pass the disjointness assertion |
| Three registered credential preimages per seat | Concrete SHAKE256 circuits, with 48-byte private seeds and 64-byte outputs |
| All 43 public tracing handles | Link and masked-identity equations checked in the same circuit |
| Actual cryptographic proof generation | Binius64 `ZKProver`, using the pinned source already available in the project |
| Public-only verification | `verify_public.py`; fresh native verifier subprocesses receive no witness path that exists |
| Full inline proof representation | Existing QVT1 exact transcript codec; every reconstructed transcript undergoes the native verifier and transcript finalization |
| Public conflict extraction | Match links, subtract masks in the binary field, divide by the nonzero message difference |

The native circuit is an equivalent binary-word implementation of the v1.24 predicate. It is not an implementation of the earlier proposed odd-prime-field R1CS compiler. There are no individual leaf proofs and no application-level recursive aggregation of leaf verifiers. The selected Binius ZK backend itself uses a Spartan wrapper internally; its commitments, queries, blinding-related data, and verification costs remain included in the whole proof.

The experimental framing is `DC25`, version 25, suite `0x2503`; the **relation** remains `CEQS124_DIRECT_CHALLENGE`. It cannot be substituted for a v1.23 proof or silently installed as a qualified production suite.

## 2. Exact statement and witness

Let the registry contain 64 entries in each of three roles. Seat indices are integers `i` in `0..63`. Each seat has independent private credentials `a_i`, `b_i`, and `v_i`, each 48 bytes. Define

\[
H(P_1,\ldots,P_k)=\operatorname{SHAKE256}(\operatorname{lp}(P_1,\ldots,P_k),64\text{ bytes}),
\]

where `lp` prefixes **each** part with its unsigned 64-bit big-endian length. The role keys are

\[
K_i^A=H(\texttt{CEQS124/link-key},a_i),\quad
K_i^B=H(\texttt{CEQS124/mask-key},b_i),\quad
K_i^V=H(\texttt{CEQS124/vote-key},v_i).
\]

The configuration fingerprint is

\[
C=H(\texttt{CEQS124/config},\mathrm{metadata},K_0^A,\ldots,K_{63}^A,
K_0^B,\ldots,K_{63}^B,K_0^V,\ldots,K_{63}^V),
\]

with exact metadata bytes

```
CONTENTS-FIRST/DIRECT-CHALLENGE/GF512/64/43/3x48/v1.24
```

The verifier recomputes this fingerprint and requires 64 different 64-byte keys in each registry. Registry authenticity and the assignment of seats to distinct authorized members come from the application's authenticated fixed configuration; a hash consistency check alone does not authenticate a registry.

Let

\[
\mathbb F=\mathbb F_2[X]/(X^{512}+X^8+X^5+X^2+1).
\]

Field elements use 64-byte big-endian polynomial-basis encoding. The retained v1.23 field checks establish irreducibility of this modulus; the new native field-vector tests exercise this exact representation. Field addition is XOR. The identity embedding is the field element whose integer encoding is `i+1`; field multiplication is not ordinary integer multiplication.

The domain `d` and message `m` are exactly 64 bytes. The challenge is **the message itself interpreted as a field element**:

\[
c(m)=\operatorname{Decode}_{\mathbb F}(m).
\]

Consequently distinct canonical messages always have a nonzero challenge difference, including when one message is zero. If an application first hashes larger messages to 64 bytes, collision resistance of that upstream mapping remains a separate requirement.

The public handle for seat `i` is

\[
L_i=H(\texttt{CEQS124/link-tag},a_i,C,d),
\]

\[
r_i=\operatorname{Decode}_{\mathbb F}H(\texttt{CEQS124/mask-pad},b_i,C,d),
\qquad Z_i=r_i+c(m)\,(i+1).
\]

The public statement contains `(C,d,m,[(L_j,Z_j)]_{j=0}^{42})`, with strictly increasing `L_j`. Its witness contains exactly 43 rows `(i_j,a_j,b_j,v_j)`. The relation requires:

1. `i_j` is in `0..63`, and every selected index is different.
2. All three seed hashes equal the three registry entries at the **same** `i_j`.
3. The link and mask equations above reproduce every public handle.
4. The exact public configuration, domain, message, and sorted 43-handle list are the values being verified.

This is a credential-preimage relation. It does not verify an ML-DSA signature and does not establish an approval event merely from the existence of a witness.

## 3. Proof of the new circuit construction

### Lemma 1: shared selection is exact

For a private 64-bit word `i`, the circuit asserts `i >> 6 = 0`. Let `s_k` be `i << (63-k)` for `k=0..5`. The native `select(s,t,f)` operator reads the most significant bit of `s`. Thus `s_k` selects using exactly bit `k` of `i`; unused low bits of the selector word have no meaning.

At the first level of the lookup tree, bit 0 chooses the correct member of each adjacent pair. At level 2, bit 1 chooses the correct pair. Inductively, level `k+1` chooses the member indexed by the low `k+1` bits inside each block of that length. After six levels, the result is precisely table entry `i`.

The same six wires are supplied to every role lookup and to the public scaled-identity lookup. Therefore different roles cannot select different seat indices. These are semantic bitwise operations, not unconstrained selector hints.

### Lemma 2: occupancy enforces distinctness

Let `E_j` be the lookup result from the public table `[1 << 0, ..., 1 << 63]`. By Lemma 1, `E_j` has exactly one set bit, at index `i_j`. Starting with `O_0=0`, the circuit enforces

\[
O_j\mathbin{\&}E_j=0,\qquad O_{j+1}=O_j\mathbin{\oplus}E_j.
\]

Induction shows that, after each accepted row, `O_j` is the union of all previously selected bits. A fresh bit passes the AND-zero test and is added. A repeated bit makes that test nonzero before XOR could remove it. Hence all 43 indices are distinct. Conversely every sequence of 43 distinct indices satisfies these equations.

This avoids the characteristic-two error of replacing integer occupancy counts with field sums: an even repetition cannot disappear unnoticed. The occupancy map stays private and adds no signer bitmap to the frame.

### Lemma 3: the hash wiring checks the stated functions

The 16-byte role and tracing labels align the private seed at word offset 4 in the length-prefixed input. Registration hashing has an 80-byte input and uses one SHAKE-rate block; tracing hashing has a 224-byte input and uses two. The circuit applies SHAKE's `0x1f` suffix and final padding bit at the 136-byte rate, then invokes the native Keccak-f1600 gadget. Its first eight little-endian output words reconstruct the 64 hash bytes.

There are three one-permutation registration checks and two two-permutation tracing hashes per contribution: seven Keccak permutations per seat. Private seed words use little-endian machine encoding; this does not change the big-endian field encoding of the public masked identity. The selected scaled identity is computed from the public message with reduction tail `0x125` and inserted as constants into the circuit.

This argument assumes correct implementation of the pinned Keccak and word-gate library. The independent Python fixtures use Python's SHAKE implementation and separately implemented field multiplication; both full native witnesses matched these fixtures. This is implementation evidence, not a machine-checked proof of the compiler or Keccak gadget.

### Proposition: predicate equivalence

Assuming the stated native gate semantics and correct Keccak gadget, an accepted canonical body has a satisfying native circuit witness if and only if it has a witness for the v1.24 43-seat relation.

*Forward direction.* Range and occupancy give 43 different valid indices. Shared lookups give the same index for every role. Hash equality constraints give the registered preimages, and the public-output equality constraints give exactly the link and mask equations.

*Reverse direction.* Supply the valid relation's seat words and seed words, and compute the intermediate gates. Shared lookups select the stated keys, distinctness passes, and all public equations agree. The host's canonical parsing requirements are the same strict handle-order and width requirements in the reference relation.

The public keys, configuration, domain, and message specialize the verifier's circuit; the handle words are its explicit public input vector. Rebuilding that circuit from the authenticated configuration and frame is part of verification. A cached verifier for another message or domain must not be reused.

## 4. Conditional proof of conflict extraction

Define the *consistent-opening event* for a pair of statements as follows: each repeated registered seat uses the same link credential and mask credential in its satisfying witnesses, and distinct seats do not share a link tag in that context. Violating the first condition supplies alternative credential preimages for a registered key; violating the second supplies a cross-seat link collision. A cryptographic reduction must bound these events in the actual adaptive adversarial experiment. They are not assumed mathematically impossible.

**Theorem.** Suppose two canonical statements satisfy the relation, have the same authenticated `C,d`, have different canonical messages, and satisfy the consistent-opening event. Then public extraction returns exactly their intersection of witness-seat identities, containing at least 22 seats.

**Proof.** Let the two 43-element seat sets be `S` and `S'`. Both are subsets of a 64-seat universe, so

\[
|S\cap S'|=|S|+|S'|-|S\cup S'|\ge43+43-64=22.
\]

For each common seat `i`, its link is unchanged because `a_i,C,d` are unchanged. Its mask is unchanged for the same reason with `b_i`. Thus

\[
Z_i+Z_i'=(r_i+c(m)(i+1))+(r_i+c(m')(i+1))
=(c(m)+c(m'))(i+1).
\]

The message encoding is injective, so `c(m)+c(m')` is nonzero and invertible. Therefore

\[
\boxed{\ i+1=(Z_i+Z_i')\,(c(m)+c(m'))^{-1}\ }.
\]

The consistent-opening event also ensures that a matched link cannot belong to two different seats. Every match therefore gives exactly one genuine intersection identity and no extra identity. Subtracting one from the integer representation gives the seat index. This uses only the two public statements. ∎

The extractor verifies **both complete proofs first**, checks the same conflict context and different messages, matches links, performs the division, and rejects a result outside `1..64` or with fewer than 22 distinct indices. Matching raw, unverified handle lists is not accepted as evidence.

This theorem concerns witness identities. Turning it into a theorem about **actual equivocating authorizers**, including resistance to framing a member who did not approve both messages, additionally requires a suitable adaptive joint argument-of-knowledge theorem and an authorization protocol/reduction. Ordinary soundness alone does not establish knowledge or consent: valid witnesses may exist for a statement even when an adversary does not know them.

## 5. What fills the proof position

The contents-first layout remains three parts:

| Part | Required information |
|---|---|
| Header | Exact format/suite, authenticated configuration reference, conflict domain, canonical message, count, handle width, complete proof length |
| 43 inline handles | Every full link and masked identity needed for public intersection extraction |
| One complete proof | All transcript data required by the chosen verifier to establish the entire relation |

The intended 32 KiB contract reserves 208 bytes for the header, 5,504 for the handles, and up to 27,056 for that whole proof. Nothing in this experiment moves transcript data, openings, commitments, or handles outside the frame. The registry is fixed public configuration shared across certificates, not a per-certificate retrieval service.

The instantiated proof position contains a QVT1 encoding of the complete Binius ZK transcript: the native prefix, queried field values, authenticated Merkle boundary data, and terminal data needed to reconstruct the native transcript. Deterministically redundant native data are reconstructed by the existing codec. The decoder then executes all native verification checks and requires transcript exhaustion. The native `.proof` files are optional audit copies and were absent from the isolated verification directories.

The two actual frames are **289,664** and **287,712 bytes**. This single fixed-profile run proves that the content relation is executable; it does not fit the 32 KiB contract. The experiment neither proves a lower bound against other protocols nor relaxes that contract. There was no parameter sweep, truncation, skipped query, or omitted sidecar counted as a solution.

## 6. Actual execution evidence

Fresh secret credentials were generated with `os.urandom`, not the public deterministic seeds used in the v1.24 equation tests. Native proof randomness came from the backend's `rand::rng()` path. The local prover held all selected credentials; this is a centralized experiment, not a 64-party approval run. The expected signer sets are intentionally public in the test provenance, so this run is not an empirical anonymity experiment.

| Experiment | Result |
|---|---|
| Quorum A | Seats `0..42`, zero message |
| Quorum B | Seats `0..21` and `43..63`, message value `2^511+17` |
| Native proof generation | Two new proofs, each of all 43 contributions |
| Native constraint controls | 12 checks per quorum, including duplicate complete contribution, other-seat role substitutions, malformed seat, seed changes, and changed public handles |
| Exhaustive selector test | All 4,096 ordered in-range seat pairs: different seats accepted, equal seats rejected; five out-of-range values rejected |
| Independent field vectors | 384 cases, covering all 64 identity embeddings and zero, low, high, and all-one-bit messages |
| Private input removal | Two files, 13,072 bytes total, removed before encoding and public verification; no secure-storage erasure claim |
| Isolated public verification | Both inline frames verified in fresh processes with nonexistent private paths |
| Public conflict extraction | Exactly 22 distinct indices: `0..21` |
| Public negative controls | 14 mutations rejected, covering context, message, handles, proof, format, count, lengths, truncation, trailing data, missing proof, duplicate handle, and registry inconsistency |
| Complete original-goal QCs | Zero |

Native statement constraint verification and proof verification are separate stages. The initial prover logs deliberately say `native_proof_verified=false` until a subsequent verifier runs. The later public-verification record is the acceptance evidence. In inherited native logs, `full_quorum_verified=false` refers to the unqualified complete-QC status; `full_quorum_relation_verified=true` records acceptance of the actual 43-seat experimental relation.

Proof A frame SHA-256:

```
17c29be18fd3e97e967f47cc1f0e2e79739168b43afdfa2f57f6eb7ef6983908
```

Proof B frame SHA-256:

```
87b63f90eccdcf3e8b5aee93d8ea8b6bc87e76be08163e40464c18e3fe157f4b
```

The retained native producer/verifier binary SHA-256 is

```
5a212125c67105e66bde6b59232fceba6402f9535bf8df3f3e490d7cdf38367b
```

## 7. Remaining security obligations

| Obligation | Current status and exact missing step |
|---|---|
| Native circuit for the v1.24 predicate | Implemented; new cryptographic arguments verify |
| Public extraction equations | Proved under the explicit consistent-opening condition and tested after actual proof verification |
| 32 KiB complete frame | Unmet by this backend; another complete proof instantiation or protocol improvement must fit the existing proof position |
| QPT-128 knowledge security | Open. Pinned native `SECURITY_BITS` is 96; standard transcript/Merkle hashing uses SHA-256 and sumcheck arithmetic uses `Ghash128b`. Larger application hash outputs do not upgrade the backend theorem |
| Fresh authorization and nonframing | Open. Need the exact adaptive approval game, joint extraction/simulation guarantees, credential-preimage and tag-consistency reductions with concrete losses, and protection of credentials during proof generation |
| Ordinary signer privacy | Open for the composed protocol. Native ZK mode is used, but the full public view and credential-derived link/mask outputs need an appropriate indistinguishability analysis; repeated links intentionally remain linkable within a conflict domain |
| Distributed generation with 21 faults | Open. No robust MPC prover or quantum-composable distributed protocol was executed |
| Registry legitimacy | External authenticated configuration and member registration are required; duplicate-key rejection is not proof of separate membership |

Increasing a constant named `SECURITY_BITS`, compressing a larger proof with an external pointer, or calling a relation witness an approval would not discharge these obligations. No such substitution is made here.

## 8. Reproduction

From the root of the extracted review package, verify the retained pair:

```bash
python3 continuation_v1.25/verify_public.py \
  --config continuation_v1.25/fixture/config.json \
  --frame continuation_v1.25/fixture/case0/trace43_rate3.dc25 \
  --frame continuation_v1.25/fixture/case1/trace43_rate3.dc25
```

The shipped native binary was built for this host's x86-64 CPU features. Rebuild on a different compatible environment rather than assuming binary portability. The Rust source, lockfile, pinned backend source, Python reference code, complete frames, original native proofs, and verification records are in the review package. The package does not promise to bundle the Rust toolchain or Cargo cache.

```bash
RUSTFLAGS='-C target-cpu=native' cargo build --release \
  --manifest-path continuation_v1.25/adapter/Cargo.toml
```

Copy the newly built executable into `continuation_v1.25/bin/ceqs-direct-proof-v125` before running the Python verifier. The workspace build used Rust 1.97.1 and its existing offline dependency cache. The included `reproduce.sh` describes public verification and rebuilding without the workspace-specific toolchain wrapper.

New proof generation requires fresh private fixtures; the included fixture generator deliberately refuses to overwrite the retained evidence. The original credentials cannot be recovered from the package. Proof byte-for-byte reproduction is not expected from randomized proving; public verification of the retained bytes is reproducible.

## 9. Primary-source and implementation provenance

1. Binius Developers, [Binius64 source repository](https://github.com/binius-zk/binius64), accessed 2026-09-09. The repository identifies the implementation as a ZK succinct argument system over 64-bit words. This experiment uses the already pinned commit `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4`, not an unrecorded upgrade to the current repository.
2. Binius Developers, [constraint-system overview](https://www.binius.xyz/blueprint/overview/) and [CircuitBuilder documentation](https://docs.binius.xyz/binius_frontend/struct.CircuitBuilder.html), accessed 2026-09-09. These explain word-level constraints and the MSB selector convention. The exact implementation semantics were checked in the local pinned source.
3. Exact local backend sources: `continuation_v1.17/binius64-source/crates/verifier/src/zk_config.rs`, `verify.rs`, `config.rs`, and the hash-suite source. `ZKVerifier` uses the Spartan ZK wrapper and the configured FRI query count; `verify.rs` defines the 96-bit parameter. A stale public roadmap still says ZK is planned; the pinned executable source and selected `ZKProver`/`ZKVerifier` path are the evidence for which mode was actually run.
4. User-provided research and prior analysis remain preserved in the inherited review package. The exact relation source is `continuation_v1.24/contents_contract.py`; v1.23's proofs do not prove that relation. The extraction and selector lemmas in this report are arguments for the explicitly stated construction, not quotations or claimed new theorems from an unrelated paper.

No cited source is treated as a proof that this composition meets QPT-128, nonframing, robust collaborative generation, or 32 KiB compactness.
