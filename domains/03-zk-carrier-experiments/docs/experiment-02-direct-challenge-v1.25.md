# Experiment 2 — v1.25: real proofs of the v1.24 contents-first relation

## The problem

Before v1.25 the programme had a relation and a codec but no *working prover/verifier pair* for it.
The question this experiment asked was narrow and decisive: can the v1.24 "contents-first, direct
challenge" relation be proved by the pinned backend, and can the resulting frames be verified by a
process that holds **only** the public configuration and the complete frames — after the private
witness files have been deleted? Everything downstream in this domain depends on the answer being yes.

## The relation carried: `CEQS124_DIRECT_CHALLENGE`

Experimental framing `DC25`, version 25, suite `0x2503`. The relation itself is v1.24's and cannot be
substituted for a v1.23 proof or installed as a production suite. With `H` = SHAKE256 to 64 bytes over
length-prefixed arguments (`lp` prefixes **each** part with its unsigned 64-bit big-endian length):

- **Registry.** 64 entries in each of **three** roles. Each seat `i` has independent private
  credentials `a_i`, `b_i`, `v_i`, each 48 bytes, and
  `K_i^A = H(CEQS124/link-key, a_i)`, `K_i^B = H(CEQS124/mask-key, b_i)`,
  `K_i^V = H(CEQS124/vote-key, v_i)`.
- **Configuration fingerprint.** `C = H(CEQS124/config, metadata, K_0^A…K_63^A, K_0^B…K_63^B, K_0^V…K_63^V)`
  with metadata bytes `CONTENTS-FIRST/DIRECT-CHALLENGE/GF512/64/43/3x48/v1.24`. The verifier recomputes
  `C` and requires 64 different 64-byte keys in each registry.
- **Field.** `F = F₂[X]/(X^512 + X^8 + X^5 + X^2 + 1)`, elements as 64-byte big-endian polynomial-basis
  encodings, addition XOR. The identity embedding of seat `i` is the element whose integer encoding is
  `i + 1` — **field multiplication is not ordinary integer multiplication**.
- **Challenge.** The message itself, decoded as a field element: `c(m) = Decode_F(m)`, where `d` and
  `m` are exactly 64 bytes each. Distinct canonical messages therefore always have a nonzero challenge
  difference, including when one message is zero.
- **Handles.** `L_i = H(CEQS124/link-tag, a_i, C, d)` and
  `r_i = Decode_F H(CEQS124/mask-pad, b_i, C, d)`, `Z_i = r_i + c(m)·(i+1)`.
- **Statement and witness.** The public statement is `(C, d, m, [(L_j, Z_j)]_{j=0}^{42})` sorted
  strictly by `L`; the witness is exactly 43 rows `(i_j, a_j, b_j, v_j)` with `i_j` in `0..63`, all
  indices different, the three seed hashes equal to the three registry entries **at the same** `i_j`,
  and every public handle reproduced.

This is a **credential-preimage relation**. It does not verify an ML-DSA signature, and a witness does
not by itself establish an approval event.

## The backend, and which part of its theory applies

Backend: the patched Binius64 ZK prover (experiment 1). The native circuit is an equivalent
binary-word implementation of the predicate — **not** an implementation of the earlier proposed
odd-prime-field R1CS compiler. There are no individual leaf proofs and no application-level recursive
aggregation; the backend's Spartan wrapper, its commitments, queries, blinding data and verification
costs all remain inside the proof.

Three pieces of theory are used, and each is used in a limited way (domain IDs `D3-10`, `D3-11`,
`D3-12`):

- **Shared selection (`D3-10`, Lemma 1).** For a private 64-bit word `i`, assert `i >> 6 = 0`; let
  `s_k = i << (63−k)`. The native `select(s,t,f)` reads the most significant bit of `s`, so `s_k`
  selects on exactly bit `k`. Six levels of the lookup tree therefore return table entry `i`, and the
  same six wires are reused for all three registries and the public scaled-identity lookup, so
  **different roles cannot select different seats**.
- **Occupancy (`D3-10`, Lemma 2).** With `E_j` the lookup result from the public table
  `[1<<0, …, 1<<63]`, the circuit enforces `O_j & E_j = 0` and `O_{j+1} = O_j ⊕ E_j` starting from
  `O_0 = 0`. A repeated seat fails the AND-zero test *before* XOR could cancel it. The source notes
  explicitly that this avoids the characteristic-two error of replacing integer occupancy counts with
  field sums, and that the occupancy map stays private, adding no signer bitmap to the frame.
- **Hash wiring (`D3-11`).** An 80-byte registration input uses one SHAKE rate block; a 224-byte
  tracing input uses two. The circuit applies SHAKE's `0x1f` suffix and final padding bit at the
  136-byte rate, then invokes the native Keccak-f1600 gadget, and its first eight little-endian output
  words reconstruct the 64 hash bytes. Hence **three one-permutation registration checks and two
  two-permutation tracing hashes per contribution: seven Keccak permutations per seat.** The source
  labels this `[A]`+`[M]`: it assumes correct implementation of the pinned Keccak and word-gate
  library, and is implementation evidence rather than a machine-checked proof.

The proposition (`D3-12`) is that, assuming the stated native gate semantics and a correct Keccak
gadget, a canonical body has a satisfying native circuit witness **iff** it has a v1.24 relation
witness. The proof is in `history/v1.25/assessment.md` §3, with both directions given.

## How the adapter bridged them

`history/v1.25/adapter/` — the Rust adapter building the circuit — is **not retained in this
repository** (see the exclusions in `docs/provenance.md` §4: neither the v1.25 adapter source nor its
binary exists in the research tree, only the report and its three result records). What is retained is
the record of what that adapter did:

| Component | Implementation, as the report states it |
|---|---|
| Configuration and hash labels | `adapter/src/trace.rs`, cross-checked against the v1.24 `contents_contract.py` |
| One shared hidden seat selector | six selector wires reused for all three credential tables, the scaled-identity table and the occupancy indicator |
| 43 distinct seats | private 64-bit occupancy map, disjointness assertion |
| Three credential preimages per seat | concrete SHAKE256 circuits, 48-byte private seeds, 64-byte outputs |
| All 43 public handles | link and masked-identity equations checked in the same circuit |
| Full inline proof representation | the QVT1 exact transcript codec; every reconstructed transcript undergoes the native verifier and transcript finalization |

## Tests

| Test | What it asserts | Recorded result |
|---|---|---|
| Native constraint controls | 12 checks per quorum: valid witnesses, range, seed changes, seat reassignment, altered handles, other-seat credentials, repeated complete contributions, mixed link/mask contributions | passed for both quorums (`history/v1.25/encode_case0.json`, `encode_case1.json`) |
| Exhaustive selector test | all 4,096 ordered in-range seat pairs: different seats accepted, equal seats rejected; five out-of-range values rejected | passed |
| Independent field vectors | 384 cases covering all 64 identity embeddings and zero, low, high and all-one-bit messages | passed; re-run here as part of `src/make_fixture.py`'s 15-check suite |
| Private input removal | two files removed **before** encoding and public verification | 13,072 bytes total; no secure-storage erasure claim |
| Isolated public verification | both inline frames verified in fresh processes with **nonexistent** private paths | `native_verified: true` for both |
| Public conflict extraction | the two public statements alone recover the common seats | exactly 22 distinct indices, `0..21` |
| Public negative controls | 14 mutations: context, message, handles, proof, format, count, lengths, truncation, trailing data, missing proof, duplicate handle, registry inconsistency | 14 rejected |
| Complete original-goal QCs | — | **0** |

## Measured sizes and verification results

All of the following are **recorded measurements**, quoted from the retained files; they were not
re-measured for this repository, and the case-0 and case-1 frame files themselves are not in this
repository.

| Quantity | Case 0 | Case 1 |
|---|---:|---:|
| Gates | 899,429 | 904,933 |
| Committed allocated words | 262,144 | 262,144 |
| Private 64-bit witness words | 817 | 817 |
| Native proof bytes | 339,200 | 339,200 |
| Encoded proof bytes (QVT1) | 283,952 | 282,000 |
| **Complete frame bytes** | **289,664** | **287,712** |
| Frame sha256 | `17c29be1…3908` | `87b63f90…7f4b` |

Verification record `history/v1.25/public_verification.json`: scope
`ACTUAL_CEQS124_RELATION_PROOFS_EXPERIMENTAL`, binary sha256 `5a212125…8367`, input set "authenticated
public configuration and complete inline frame bytes", both frames `native_verified: true`,
`private_input_opened: false`, `all_proof_bytes_inline: true`, `complete_QC_accepted: false`,
22 recovered indices, and `complete_32KiB_QCs_accepted: 0`.

Two accounting notes the report makes itself. First, native statement-constraint verification and
proof verification are separate stages: the initial prover logs deliberately say
`native_proof_verified=false` until a subsequent verifier runs, and the public-verification record is
the acceptance evidence. Second, in inherited native logs `full_quorum_verified=false` refers to the
unqualified *complete-QC* status, while `full_quorum_relation_verified=true` records acceptance of the
actual 43-seat experimental relation.

## Conclusions, and what stayed open

The relation was executable and publicly verifiable, and the extraction identity
`i + 1 = (Z_i + Z'_i)(c(m) + c(m'))⁻¹` was *tested after actual proof verification*, not merely
derived (`D3-13`). The conditional conflict theorem holds under the consistent-opening event, and the
report states plainly that violating either half of that event — an alternative credential preimage
for a registered key, or a cross-seat link collision — must still be bounded by a reduction in the
adaptive adversarial experiment. They are "not assumed mathematically impossible."

Left open, in the report's own words: the 32 KiB gate (unmet by this backend); QPT-128 knowledge
security (pinned `SECURITY_BITS` is 96, transcript hashing is SHA-256, sumcheck arithmetic is
`Ghash128b`, and larger application hash outputs do not upgrade the backend theorem); fresh
authorization and nonframing (the adaptive approval game, joint extraction/simulation guarantees,
credential-preimage and tag-consistency reductions with concrete losses); ordinary signer privacy for
the composed protocol; distributed generation with 21 faults; and registry legitimacy, which remains
an external authenticated-configuration prerequisite.

The report adds one sentence that this repository keeps verbatim in spirit: increasing a constant named
`SECURITY_BITS`, compressing a larger proof with an external pointer, or calling a relation witness an
approval would not discharge these obligations, and no such substitution was made.
