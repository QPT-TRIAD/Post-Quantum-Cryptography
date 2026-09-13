# Experiment 3 — v1.27 (candidate A): fusing the link and mask derivations

## The problem

v1.25 spent **seven Keccak permutations per seat** in the private witness: three registration hashes
(`a_i`, `b_i`, `v_i`) and two two-block tracing hashes. The tracing hashes had a fixed shape — a label
and a 48-byte seed, then a context — so the question was whether the *link* and the *mask* could be
derived from one hash invocation instead of two, and whether the length-prefixed private encoding
could be dropped for fixed-shape inputs. Each of those removes private witness words, and private
witness words are circuit shares of the proof size.

This document covers candidate A. Its successor, candidate B, is
`docs/experiment-04-fixed-context-v1.27b.md`; the two share a lineage and are compared directly by the
retained v1.27 report (`history/v1.27b/assessment.md` §3). **Candidate A's own report is not retained
in this repository** — no `assessment.md` exists for it — so everything here is taken either from the
v1.27b report's comparison table or from candidate A's own retained records under `history/v1.27/`.

## The relation carried: `CEQS127_PAIRED_TRACE`

Frame magic `PT27`, version 27, suite `0x2703`. Relative to v1.25:

- The link and mask derivations are combined into **one 128-byte SHAKE output** from a tracing seed.
- An independently generated authorization seed remains necessary in every circuit witness — the
  experiment did not remove a credential check.
- Candidate A **retains** the length-prefixed private encoding and includes `C, d` directly in the
  paired hash. Its exact equations are implemented in `history/v1.27/paired_reference.py`, which is
  the executable specification of this relation in this repository.

The information the frame must still carry is unchanged from v1.25 (v1.27b report §1): the
authenticated fixed public configuration with its recomputed fingerprint, the exact conflict context
and message, all 43 full `(link, masked identity)` pairs at 128 bytes each, the same-seat binding of
tracing and authorization through one hidden index, exactly 43 distinct hidden indices checked with a
private occupancy map, and one inline QVT1 representation of the entire native proof transcript.

The report warns explicitly that this is a **new relation with a new suite identifier** and "not a
security-equivalent substitution for v1.25 without further analysis".

## The backend, and which part of its theory applies

Same patched Binius64 backend. Same three pieces of construction theory as v1.25 — the MSB-select
lookup tree, the bitwise occupancy map, the hash-wiring count (`D3-10`, `D3-11`, `D3-12`) — with the
wiring lemma applied to the new hash shape:

- Two registration hashes per seat, each one SHAKE rate block.
- One paired hash whose input is a two-block input in this candidate (it still carries the
  length-prefixed encoding and `C, d`), i.e. **four permutations per seat**, down from seven.

The occupancy lemma is what keeps the distinctness property from v1.25 intact, and the predicate
equivalence argument transfers unchanged because the handle equations are the only thing that changed.

## How the adapter bridged them

`history/v1.27/adapter/` retains the candidate-A adapter: `Cargo.toml`, `Cargo.lock`,
`src/main.rs`, `src/trace.rs`. The adapter emits a `PT27` frame — a 208-byte header, 5,504 bytes of
handles and the QVT1 codec output — and the accompanying Python driver
(`history/v1.27/run_native.py`) records the check, prove, encode and verify stages separately, each
writing an `*_execution.json` record alongside its JSON result and log. The pairing change lives in
the circuit; the transcript handling, the verifier and the QVT1 codec are the v1.25 ones.

The adapter's manifest keeps its relative path dependencies into the vendored backend tree, which is
not in this repository; the file now carries a header comment recording that, the upstream URL and
pinned commit, the patch digest and the rebuild command. See `docs/provenance.md` §3.

## Tests

| Test | What it asserts | Recorded result |
|---|---|---|
| Native constraint controls (per case) | 11 checks: `honest_witness_matches_independent_fixture`, `seat_out_of_range`, `trace_seed_mutation`, `vote_seed_mutation`, `seat_reassignment`, `public_mask_mutation`, `public_link_mutation`, `other_seat_trace_seed`, `other_seat_vote_seed`, `duplicate_complete_contribution`, `link_mask_from_different_seats` | all eleven recorded in `history/v1.27/check_case0.json` and `check_case1.json` |
| Independent reference suite | the 15-check reference suite shared with candidate B: both honest 43-seat relations, other-seat role substitutions, mixed link/mask rejection, the 22 expected conflict identities, changed domain/message/configuration rejection, 64 rotating quorums at an all-one message, 384 field vectors | `history/v1.27/paired_reference.py` is the retained implementation; the suite re-runs today from `src/make_fixture.py` against the *current* relation (see `VERIFICATION.md`) |
| Public verification | both frames verified from a fresh directory with only the configuration and the inline frames | `history/v1.27/public_verification.json` |
| Private input removal | both private witness files deleted after proving and before encoding/public verification | `history/v1.27/private_input_deletion.json`: two files, 4,472 bytes each, 8,944 bytes total, `private_files_remaining: 0`, `secure_erasure_claim: false` |
| Public negative controls | mutations of the frame | **no record for candidate A is retained.** The 18-control record in this repository (`history/v1.27b/public_negative_checks.json`) belongs to candidate B |

## Measured sizes and verification results

Recorded measurements, quoted from `history/v1.27/encode_case{0,1}.json` and
`history/v1.27/public_verification.json`; not re-measured here.

| Quantity | v1.25 baseline | Candidate A | Case 0 | Case 1 |
|---|---:|---:|---:|---:|
| Private permutations per seat | 7 | 4 | 4 | 4 |
| Private 64-bit witness words | 817 | **559** | 559 | 559 |
| Gates | 899,429 / 904,933 | — | 521,717 | 527,221 |
| Allocated committed words | 262,144 | 262,144 | 262,144 | 262,144 |
| Native proof bytes | 339,200 | — | 339,104 | 339,104 |
| Encoded proof bytes | 283,952 / 282,000 | — | 281,936 | 275,520 |
| **Complete frame bytes** | 289,664 / 287,712 | — | **287,648** | **281,232** |
| Frame sha256 | — | — | `dcdf327d…a9cd` | `f892f913…d6077f` |
| Binary sha256 | `5a212125…8367` | — | `3a74de19…300a` | — |

The retained frame bytes for this candidate are `fixtures/case0/trace43_rate3.pt27` (287,648 bytes) and
`fixtures/case1/trace43_rate3.pt27` (281,232 bytes) — both re-checked against the records for this
repository (`VERIFICATION.md` §2, item 12).

The report's verdict on the saving: candidate A reduces the circuit substantially but the native proof
size barely changes (339,200 → 339,104 bytes), and the frames improve by 2,016 bytes in case 0 and
6,480 in case 1. That gap between circuit reduction and proof reduction is the finding that motivated
the next candidate and, later, the codecs.

## Negative controls and other published corrections

No negative-control record for candidate A survives. What survives is a
`history/v1.27/build.stderr.log` and the `history/v1.27/package-validation.json` /
`domains/03-zk-carrier-experiments/history/v1.27/source-manifest.json` pair for the review bundle that carried this candidate. The absent control
record is stated here rather than filled in from the sibling candidate's records: the 18 mutations
recorded under `history/v1.27b/` were rejected by candidate B's binary, and this repository does not
extend that result to candidate A.

## Conclusion

Candidate A answered its question: fusing the two derivations and dropping three of seven private
permutations cut the case-0 circuit from 899,429 to 521,717 gates (42 % of the baseline removed) and
the witness words from 817 to 559, but bought only 2,016 bytes in case 0. The frame was still 254,880
bytes over the target. The
relation was carried forward as a comparison baseline, and the *next* question — whether the private
hash encoding could be simplified further and the public context prehashed — was asked as candidate B.

Open items recorded for this candidate are the same as for v1.27b, and are listed in
`docs/experiment-04-fixed-context-v1.27b.md` §"Conclusions".
