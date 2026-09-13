# Experiment 4 — v1.27b (candidate B): `CEQS12B_FIXED_CONTEXT`

## The problem

Candidate A showed that the circuit could shrink without the proof shrinking much. Candidate B asked
two further questions at once, both about the *private witness*: can the length-prefixed private hash
encoding be replaced by fixed-width inputs, and can the public configuration and domain be prehashed so
that the private circuit no longer carries them? If both work, the tracing hash that produces the
`(link, mask)` pair fits in a **single** SHAKE rate block, and the relation needs only three
permutations per seat instead of four.

The relation that comes out of this is the one every later carrier in this domain transports. It is
also the relation for which this repository retains the most evidence.

## The relation carried: `CEQS12B_FIXED_CONTEXT`

Frame magic `PF27`, version 27, suite `0x27b3`. All output lengths are bytes. Define the
length-prefixed hash

```
H_lp(P_1,…,P_k) = SHAKE256( ‖_{j=1..k} ( u64be(|P_j|) ‖ P_j ), 64).
```

**Registry.** For each seat `i` in `0..63`, independently generate 48-byte seeds `t_i` and `v_i` and
register

```
K_i^T = SHAKE256("CEQS12B/tracekey" ‖ t_i, 64)
K_i^V = SHAKE256("CEQS12B/vote-key" ‖ v_i, 64)
```

Both literal labels are 16 bytes, so registration inputs are exactly 64 bytes — that is the
fixed-width change, and it is what removes the two-block private hash inputs.

**Configuration.** `C = H_lp("CEQS12B/config", M, K_0^T…K_63^T, K_0^V…K_63^V)` with metadata

```
FIXED-CONTEXT-PAIR/DIRECT-CHALLENGE/GF512/64/43/2x48/v1.27b
```

The verifier recomputes `C`, checks the exact parameters and the two 64-entry registries, and rejects
duplicate keys within either registry. For a 64-byte conflict domain `d`, `D = H_lp("CEQS12B/context", C, d)`
is the **prehashed public context** — it needs no new frame field or sidecar, because it is recomputed.

**Handles.** For each selected seat,

```
L_i ‖ R_i = SHAKE256("CEQS12B/pair-tag" ‖ t_i ‖ D, 128)
```

with the fixed partition `16 ‖ 48 ‖ 64` in one 128-byte input, injectively encoded for this fixed tuple
(no length prefixes). Then, in `F = F₂[X]/(X^512 + X^8 + X^5 + X^2 + 1)` with big-endian
polynomial-basis byte encoding and XOR addition, with `e_i` the element whose integer representation is
`i+1` and `c(m)` the direct field decoding of a canonical 64-byte message `m`:

```
Z_i = Decode_F(R_i) + c(m)·e_i.
```

**Body and witness.** The body is `(C, d, m, [(L_j, Z_j)]_{j=0}^{42})` sorted strictly by `L`; the
private witness is exactly 43 rows `(i_j, t_j, v_j)`, each row satisfying both registration equations
**and** the pair/masked-identity equations at the **same** index, with all indices in range and
different. Zero messages are allowed; different canonical messages always yield different field
challenges. The relation is still a **credential-preimage relation**: witness existence alone does not
establish a fresh approval event or a signature-of-knowledge theorem.

## The backend, and which part of its theory applies

Same patched Binius64 backend. The theory used is the same set as before, with the wiring lemma
(`D3-11`) applied to the new shape:

- The **MSB-select lookup tree** (`D3-10`, Lemma 1) still supplies the same six selectors to both
  registered-key lookups, the identity-scaled-message lookup and the one-hot occupancy lookup, so all
  four selections refer to the same seat.
- The **occupancy map** (`D3-10`, Lemma 2) still enforces distinctness, and it stays private.
- The **Keccak wiring** (`D3-11`) gives the saving: two 64-byte registration inputs need one
  permutation each; the 128-byte paired input and its padding fit in **one** rate block and its 128-byte
  output fits in that block's output — so **three private Keccak permutations per seat**. Public
  computation of `D` is part of verification/circuit specialization, not a private-witness hash
  circuit.
- **Predicate equivalence** (`D3-12`) is re-proved for this relation as the "Circuit lemma" of
  `history/v1.27b/assessment.md` §4: assuming the documented native word-gate semantics and
  correctness of the Keccak gadget, the final circuit has a satisfying witness exactly when the
  canonical body satisfies the relation above.
- **Conditional conflict extraction** (`D3-13`) is re-proved for this relation in the same section:
  given same authenticated `C,d`, different canonical messages and the consistent-opening condition,
  public extraction returns exactly the common witness seats, at least `43 + 43 − 64 = 22`, via
  `e_i = (Z_i + Z'_i)(c(m) + c(m'))⁻¹`.

## How the adapter bridged them

`history/v1.27b/adapter/` holds the adapter source (`Cargo.toml`, `Cargo.lock`, `src/main.rs`) for
this relation; the compiled `ceqs-fixed-pair-v127b` is excluded (sha256 and size in
`docs/provenance.md` §4). Its manifest carries the exclusion header comment, and its `main.rs`
retains a **stale "paired-trace" comment** from the previous candidate even though the relation had
changed. That is a comment-level defect, not a semantic difference; it is recorded here because the
repository keeps the sources as they were, and a reader who sees "paired-trace" in this file should
not conclude the wrong relation is implemented. The equations in the previous section are the
specification; `src/paired_reference.py` is their executable form.

The driver `history/v1.27b/run_native.py` plus `verify_public.py`, `check_public_mutations.py` and
`reproduce.sh` are the v1.27b-era scripts kept unmodified; they are what `src/regenerate.py` copies
into a fresh directory, and they expect to run from a directory holding `bin/`, `fixture/` and
`adapter/`.

## Tests

| Test | What it asserts | Recorded result |
|---|---|---|
| Native constraint controls, per case | 11 checks: `honest_witness_matches_independent_fixture`, `seat_out_of_range`, `trace_seed_mutation`, `vote_seed_mutation`, `seat_reassignment`, `public_mask_mutation`, `public_link_mutation`, `other_seat_trace_seed`, `other_seat_vote_seed`, `duplicate_complete_contribution`, `link_mask_from_different_seats` | `results/check-case0.json`, `domains/03-zk-carrier-experiments/results/check-case1.json` (adapter 1.27b), plus the execution records and logs beside them |
| Independent reference suite | 15 checks including both honest relations, other-seat role substitutions, mixed link/mask rejection, the 22 expected conflict identities, changed domain/message/configuration rejection, 64 rotating quorums at an all-one message, and 384 field vectors | the 15-check suite re-runs today from `src/make_fixture.py` and passes 15/15 (`VERIFICATION.md` §2) |
| Public verification, isolated | both frames verified in fresh directories containing only the frame and the public configuration, with a nonexistent private input path; the native `.proof` files absent | `history/v1.27b/public_verification.json`: both `native_verified: true`, `private_input_opened: false`, 22 recovered indices |
| Private input removal | both witness files deleted after proving and before encoding | two files × 4,472 bytes = 8,944 bytes; `secure_erasure_claim: false` |
| Public negative controls | 18 mutations | all 18 rejected (`history/v1.27b/public_negative_checks.json`) |
| Fresh regeneration | the whole pipeline re-run in a new directory from a fresh fixture | `results/regeneration-validation.json`: both fresh frames verified, 22 indices recovered, 18 controls rejected, **frames 285,136 / 283,184 bytes** — different bytes, as expected |

The 18 negative controls, named in the record: `configuration`, `domain`, `message`, `link`, `mask`,
`proof`, `suite`, `count`, `proof_length`, `previous_suite_header`, `other_message_proof`,
`truncated`, `trailing`, `proof_absent`, `duplicate_public_handle`,
`changed_registry_without_rebinding`, `domain_rebound_in_frame_and_config`,
`registry_rebound_in_frame_and_config`.

## Measured sizes and verification results

Recorded in `history/v1.27b/encode_case{0,1}.json` and `history/v1.27b/public_verification.json`; the
frame bytes themselves are retained at `fixtures/case0/trace43_rate3.pf27` and
`fixtures/case1/trace43_rate3.pf27` and were re-checked byte-for-byte against the records for this
repository.

| Quantity | v1.25 | Candidate A | **Candidate B** |
|---|---:|---:|---:|
| Private permutations per seat | 7 | 4 | **3** |
| Private 64-bit witness words | 817 | 559 | **559** |
| Case-0 gates | 899,429 | 521,717 | **402,306** |
| Case-1 gates | 904,933 | 527,221 | **407,810** |
| Allocated committed words, both cases | 262,144 | 262,144 | **131,072** |
| Native proof bytes, each case | 339,200 | 339,104 | **335,360** |
| Complete frame bytes, case 0 | 289,664 | 287,648 | **283,680** |
| Complete frame bytes, case 1 | 287,712 | 281,232 | **279,600** |
| Frame sha256 | — | — | `dd77def5…06a40` / `fb1ac2ef…02a2c` |
| Binary sha256 | — | — | `dfa90585…75c5` |

The v1.27b report attaches three qualifications to that table, which this repository keeps: the runs
are fixed-profile individual runs with fresh inputs and randomness, not average benchmarks or an
optimality claim; message-dependent constants account for the two circuit sizes; and native proof
sizes barely change despite the large circuit reduction.

## What is still too large inside the proof

The v1.27b report gives the component breakdown of the encoded proof itself, which is the diagnosis
that motivates the next two experiments:

| Encoded proof component | Case 0 | Case 1 |
|---|---:|---:|
| Native prefix | 16,384 | 16,384 |
| Transmitted queried field values | 81,376 | 80,304 |
| Merkle boundary hashes | 179,168 | 176,160 |
| Terminal coefficients | 1,024 | 1,024 |
| Codec header | 16 | 16 |
| Complete encoded proof | 277,968 | 273,888 |

**In these retained transcripts, the transmitted field values alone exceed the entire 27,056-byte
proof position.** The report's hypothetical "all boundary hashes cost zero" calculation leaves 98,800
and 97,728 bytes of proof, and it states plainly that this is accounting, not a valid verifier
modification or an information-theoretic lower bound, and that query overlap is transcript-dependent.

## Conclusions, and open items

Candidate B is the relation this domain carries forward, and it is the best of the three pre-carrier
relations: the case-0 circuit is 55 % smaller than v1.25's, yet the native proof is 3,840 bytes
smaller. That single comparison is the experiment's main result.

Still open, in the report's own terms:

| Obligation | What this experiment establishes | What is still required |
|---|---|---|
| Same-seat binding predicate | both credentials and every complete handle are constrained at one hidden index | an adaptive multi-session signature-of-knowledge/extractability result tying accepted proofs to fresh approvals |
| Tracing consistency | conditional algebraic theorem; two verified test pairs recover the expected overlap | concrete registered-preimage consistency and link-collision bounds |
| Paired-output privacy | the exact 128-byte derivation is implemented | joint pseudorandomness of `(L,R)` given registered tracing keys and permitted exposures, plus composed proof privacy — treating the halves as independent standard hashes is not justified |
| Public context prehash | recomputed by both implementations; changed contexts rejected | context/configuration binding bounds, including collisions in the new public digest `D` |
| QPT-128 | no new qualification | a concrete resource model and complete bounds for the actual proof, hashes, credentials, approval protocol, channels and composition |
| Distributed generation | private input shape reduced; intended function unchanged | an actual maliciously secure distributed prover with credential privacy and required output delivery |
| Complete 32 KiB certificate | all necessary semantics remain represented inline | a whole proof fitting 27,056 bytes with the required security properties |
| Regeneration hygiene | the fresh-pair run verified and rejected all 18 controls | **a post-process audit found the regeneration run's private files present despite the in-process deletion record.** A separate cleanup removed them; their reappearance is unexplained. The helper now asserts absence immediately after deletion and at completion. This concerns the extra regeneration test, not the four retained proofs, whose private-file absence was checked separately before public verification |

One more observation the report records and this repository repeats rather than hides: a single-domain
zero-message handle reveals `R_i`, and a conflict reveals `i` and the same mask output. Those equations
do not output `t_i` or `v_i` — and the report notes that this observation "is not a proof of
seed-recovery hardness".
