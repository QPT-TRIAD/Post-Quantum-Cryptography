# The circuit witness extractor and the relation it targets

Source: `src/circuit_witness_extractor.py` (v1.36). Script: `python3
src/circuit_witness_extractor.py --self-test` or `--explain`; the bare invocation prints the module
header and exits 0. All paths are relative to the repository root.

## 1. The problem, and why it is hard

The joint-extractor lift of v1.35 is conditional on premises P1–P4, and P4 is not free: it demands a
decoder that, given a database in which the adversary's commitments can be inverted, reconstructs a
witness for an accepted proof **without being handed an accepting challenge set**. A decoder that is
handed the successful challenge and then reads off the witness proves nothing — a cheating prover
could have arranged which challenges succeed. This is the difference between special soundness and
S-soundness, and it is the actual cryptographic content of an extraction argument.

v1.36 supplies such a decoder for a concrete, fully specified backend, together with the matching
prover and verifier. It is a *new candidate backend*, not a repair of the R29 relation. The source is
emphatic on this point, and the emphasis is warranted: a working extractor for the wrong relation
looks exactly like progress and is not.

## 2. The relation targeted

A statement `x` encodes a fixed acyclic Boolean circuit `C`, public context bytes, and a repetition
count `r`. Gates are `CONST`, `NOT`, `XOR` and `AND`, referencing only earlier wires. The relation
implemented is

```
R_C(x, w)  =  [ w is an n-bit vector and C(w) = 1 ].
```

Canonical encodings bind each view to the complete `x`, repetition and party. The context label
**alone does not constrain `C`'s semantics**: an application must pin its approved circuit and the
correct public inputs. Test 27 exists for exactly this: a weak circuit carrying the same context
string does not verify for the intended statement. A proof for the constant-1 circuit does not prove
R29 because it is labelled with an R29 context string.

For R29 integration the source states the requirement without hedging: `C` must be the audited
circuit for the **entire** fixed authorization predicate on the body and authenticated registry —
43 distinct indices, every trace-credential opening, recomputation of each handle using the same
index, and full approval-signature verification for that same seat and canonical approval message —
and a proved witness-bit encoding must map the extracted vector back to all 43 `(index, seed,
signature)` rows. Neither a supplied Boolean `authorized` flag nor a circuit that checks only the
handle algebra can substitute for those conditions.

## 3. Theory used

| Theory | Statement **as used here** | What it justifies | Full / partial | Citation as the source gives it |
|---|---|---|---|---|
| ZKBoo (Giacomelli–Madsen–Orlandi, USENIX Security 2016) | §4.1 and Proposition 4.2 supply a three-share circuit decomposition and a **three**-special-soundness argument | the share recurrence and Lemma 1 | **partial** — share decomposition and three-special soundness only. The source explicitly rejects **two**-special soundness, because two openings may reveal all input shares while leaving a computation branch unchecked | as given: USENIX Security 2016, §4.1, Prop. 4.2, App. A |
| DFMS (arXiv 2202.13730) | Definition 3.5 (S-sound\*) and Lemma 4.1 / Theorem 4.2 (ordinary commit-and-open bound) | the notion the decoder must satisfy, and the `κ_J` instantiation | **partial** — the S-sound\* definition and the ordinary C&O bound; the Merkle variant is not used | as given in the source |
| SHAKE256 | a concrete 64-byte-output oracle for the tests | the committed messages in the executable backend | **used as a concrete function only** — the source states it is "never as an ideal-oracle proof" | standard |

The three-share arithmetic: for each input witness bit `w`, choose uniform shares `w0, w1` and set
`w2 = w XOR w0 XOR w1`. Each view carries its own wire shares and independent random mask bits for
all AND gates. No pseudorandom tape generator and no new hardness assumption is needed for the
relation. For an AND gate the share recurrence is

```
z_i = a_i b_i  XOR  a_{i+1} b_i  XOR  a_i b_{i+1}  XOR  ρ_i  XOR  ρ_{i+1},
```

with indices taken modulo 3. The four **distinct** challenge subsets are `{0,1}`, `{1,2}`, `{2,0}`
and `{0,1,3}`, the last of which adds the exact dummy opening; `{0,1,3}` carries no witness-recovery
role and exists to make the fourth subset distinct while preserving binary challenge sampling.

## 4. The argument, step by step

**Lemma 1 — three passing directions yield a witness.**
If, at one repetition, all three local directions pass on the *same* three fixed view messages, the
three-share reconstruction is forced to a vector `w` with `C(w) = 1`.
*Assumption.* The commitment scheme is binding, so a view's message is fixed once committed; the
canonical encodings tie each message to the repetition and party. With that, the reconstruction is
deterministic and the AND recurrence propagates it gate by gate through the acyclic circuit.

**Lemma 2 — the decoder is S-sound\*.**
Define `S` to be the monotone family of sets of global challenges for which there exists a repetition
`j` whose selected local directions cover `{0,1,2}`. Suppose the fixed committed messages admit
accepting responses to every challenge in some member of `S`. At that `j` all three local directions
pass with the same three fixed view messages, and Lemma 1 gives a valid witness. The decoder tests
every `j` and every local direction — cost `O(r(n+g))` for `n` input bits and `g` gates, plus parsing
and canonical encoding work polynomial in their encoded lengths — so it finds a witness **without
receiving that member of `S`**. There is no `4^r` search. Missing dummy messages may invalidate
symbol 3, but they are unnecessary for reconstruction once the three directions pass.
*Assumption.* The committed messages are fixed before the challenge; the decoder reads them from the
database rather than from the adversary.

**Lemma 3 — the exact trivial-success parameter is `(3/4)^r`.**
If a challenge set lies outside `S`, every repetition's projection misses at least one local
direction. Missing direction 1 or 2 excludes at least one of the four symbols; missing direction 0
excludes two. Each coordinate therefore permits at most three symbols, so the whole challenge set
lies inside a product of such coordinate sets and has size at most `3^r`. The set `{0,2,3}^r`
attains that size and is outside `S`. Hence `p_triv = 3^r/4^r = (3/4)^r`.
*Assumption.* None about independence: the proof "does not assume that a malicious challenge set
factorizes or that different repetitions' cheating events are independent. It is a counting statement
about `S` and a uniformly sampled global challenge." The source also states what it is not: it "is
not the complete Fiat–Shamir extraction error against quantum oracle queries".

**Negative controls, which are as important as the lemmas.**

- Two accepting checks can hide a false computation: the test starts from the false witness `(0,0)`
  for `C(w) = w0 AND w1`, generates correct shares, flips only branch 1's final output share and
  updates the declared output so its XOR becomes 1. Directions 0 and 2 still pass, direction 1 fails,
  all input shares are present, the reconstruction is still `(0,0)`, and `E*` correctly returns
  failure. The rule "two openings expose all shares, therefore extract" is invalid.
- Three arbitrary **distinct** global challenges are not enough: `(0,0)`, `(0,3)`, `(3,0)` are
  distinct but select only local direction 0 in either repetition. The theorem requires local
  three-direction coverage at some repetition, not a count of transcripts.

**An amendment, recorded rather than concealed.** An earlier draft of the challenge mapping sent
symbols 0 and 3 to the same opening pair. That was insufficient to identify four distinct subsets in
the source theorem, so the implementation was amended before finalization. The v1.36 header records
the change.

**Instantiation.** For this backend's ordinary commit-and-open protocol the symbols are
`ℓ = 4r`, `p_triv = (3/4)^r`, `v0 + v1 ≤ 2 + 6r`, `h = 512` in the reference hash interface, with
`4^r` distinct global challenge subsets, `1 ≤ r ≤ 256`, and a public verifier making at most
`1 + 3r` hash calls (one challenge call, plus at most three commitment-opening checks per
repetition). Inserting these into the conservative v1.35 bound gives an admissible error term

```
κ_J = min(1, [4 + 12r + (80r + 60)Q³]/2^512  +  20 Q² (3/4)^r),
```

where `Q` includes all charged oracle calls through both verifications. The source labels this
symbolic bookkeeping under the exact QROM backend assumptions — "not a selected parameter set or a
numerical QPT-128 claim". Note that `(80r + 60) = (20ℓ + 60)` with `ℓ = 4r`: this instantiation
carries the `(20ℓ + 60)` coefficient of v1.35, and the unresolved constant discrepancy flagged in
[`joint-extractor-lift.md`](joint-extractor-lift.md) §5 applies to it as well.

## 5. Database post-processing

The circuit prover commits using the domain-separated input
`b'CEQS136/commit\x00' ‖ canonical_message`. The challenge uses a different prefix and includes the
full canonical first message and statement. Verification checks the challenge, every selected hash
opening, the dummy contents when selected, and the local direction constraints. After a reduction
measures its oracle database `D`, `extract_from_database` builds the canonical inverse map, looks up
each commitment's preimage, and runs the decoder. Two exact witnesses were recovered from one shared
classical test database after both circuit proofs had verified — and test 13, with `hashlib.shake_256`
patched to fail, confirms that **zero** post-extraction hash calls are made.

## 6. Tests

`python3 src/circuit_witness_extractor.py --self-test` runs 27 test groups and exits 0.

| Group | What it asserts |
|---|---|
| 01 | all `2^9` AND share cases reconstruct correctly |
| 02 | three checks reconstruct the input |
| 03 | a later repetition suffices |
| 04 | missing one view everywhere yields `None` |
| 05 | a malformed unused repetition is tolerated |
| 06 | wrong statement, party or repetition is rejected |
| 07 | tampered wires and tapes are rejected |
| 08 | two accepting checks hide a false computation (negative control) |
| 09 | challenge distribution and `(3/4)^r` for `r = 1…4` |
| 10 | 40 random acyclic circuits (seed 13610) |
| 11 | non-canonical circuits |
| 12 | non-canonical views |
| 13 | full proof plus database extraction with SHAKE patched to fail: zero post-extraction hash calls |
| 14 | two witnesses from one frozen database |
| 15 | wrong instance |
| 16 | the public verifier's database is insufficient, the prover's is sufficient |
| 17 | six proof mutations rejected |
| 18 | the prover refuses a false witness |
| 19 | output and partial-view shapes |
| 20 | `ℓ = 12`, `p_triv = 27/64` at `r = 3`, applied hash calls ≤ `1 + 3r` |
| 21 | a 257-bit witness is recovered |
| 22 | canonical inverse and commit domain |
| 23 | four distinct subsets; `4^r` global sets for `r ≤ 4` |
| 24 | the dummy slot is not needed for reconstruction |
| 25 | all four opening formats, with the challenge forced |
| 26 | distinct global challenges need local coverage |
| 27 | a weak circuit with the same context label does not verify for the intended statement |

Groups 08, 23 and 26 are the ones a reader should check first: they are the tests that would fail if
the soundness argument had been made too strong.

## 7. Sizes and cost

| Quantity | Value |
|---|---|
| Source file | 46,855 bytes, 943 lines |
| Commitments per repetition | `ℓ = 4r` (three views plus one dummy message) |
| Global challenge subsets | exactly `4^r` |
| Repetition range in the prototype | `1 ≤ r ≤ 256` with `h = 512`, so no rejection sampling and no modulo bias |
| Verifier hash calls | at most `1 + 3r` |
| Extractor cost | `O(r(n+g))` local operations, no `4^r` search |
| Recorded suite runtime | 0.055 s (27 tests) |

## 8. Packages and tools used

Python standard library only: `sys`, `dataclasses`, `fractions`, `hashlib`, `json`, `random`,
`unittest`, `itertools`, and `unittest.mock.patch`. `hashlib.shake_256` with a 64-byte output is the
test oracle; `unittest.mock.patch` is used in test 13 to prove that extraction performs no further
hash calls. `fractions` is used for the exact probability comparisons. No prover, no solver, and no
third-party package is involved.

## 9. Validation status

- **Proven, for this backend.** Lemma 1 (three directions force a witness), Lemma 2 (the decoder is
  S-sound\*), Lemma 3 (`p_triv = (3/4)^r`), and the cost claim `O(r(n+g))`.
- **Measured.** The 27 finite test groups, including 40 randomly generated acyclic circuits and the
  zk-commitment mutation set.
- **Not established.** Zero knowledge of this four-subset variant; a deployed-hash QPT bound; the
  compilation of R29 into `C`; and any performance figure for a large R29 circuit — "large
  R29-circuit performance has not been measured".
- **Corrected later.** The v1.43 record (domain 06) states that the prototype range `h = 512`,
  `r ≤ 256` is too short for QPT-128 extraction: `r ≥ 553` in gate units or `r ≥ 640` in query
  units, needing 1,106–1,280 challenge bits. The prototype's own header does not claim otherwise; it
  calls the instantiation symbolic. The correction is recorded here because a reader who takes
  `r ≤ 256` as a design choice rather than a prototype bound would draw the wrong conclusion.
- **Missing.** A pinned, audited compilation of the entire R29 authorization relation with a proved
  witness encoding and the equivalence `C_R29(public_input, Encode(w)) = 1 ⟺ R29(public_input, w)`.
  The v1.36 header records that the implementation package was not available for inspection while it
  was written, so it does not claim source integration or an accepted original-goal quorum
  certificate.

## 10. Open items

1. No R29 circuit, no witness encoding, and no equivalence proof.
2. Zero knowledge is not argued for this variant.
3. The prototype's `r` range is below what QPT-128 extraction needs.
4. The classical test database is not a quantum compressed-oracle implementation; no such
   implementation exists in this repository.
5. The extractor's cost claim is asymptotic and was not measured at R29 scale.
