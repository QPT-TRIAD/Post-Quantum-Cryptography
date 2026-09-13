# Experiment 6 — v1.28p, QVT3: the whole final layer as 512 polynomial coefficients

## The problem

QVT2 removed one coordinate per eligible leaf. The final queried oracle in this profile has **4,096
field elements** represented by a polynomial of degree below 512 over the backend's binary field, and
the two retained proofs reveal 832 and 816 distinct evaluation values in their final-layer leaves
*before* removing deterministic redundancies. Each view therefore already supplies more than the 512
evaluations needed to interpolate. The question was whether the carrier could send the **coefficients**
instead of the samples and their Merkle paths.

## The relation carried

`CEQS12B_FIXED_CONTEXT`, unchanged, and the same two native proofs as QVT2. Frame magic `PF2P`,
version 28, suite `0x28c3`. No private witness file is supplied or created by this experiment.

## The backend, and which part of its theory applies

The part of theory used here is interpolation and evaluation over the backend's binary field, plus the
fact that the Merkle tree of the oracle is a deterministic function of its leaves (`D3-15`, `D3-14`):

1. The encoder chooses the first 512 queried positions in canonical order. Let their public
   coordinates be `x_0,…,x_511` and values `y_0,…,y_511`, and construct the Newton representation

   ```
   p(X) = Σ_{k=0}^{511} a_k · Π_{j=0}^{k-1} (X − x_j).
   ```

2. The carrier transmits the **512 coefficients**, occupying 8,192 bytes.
3. The decoder regenerates the coordinates using the pinned additive NTT, evaluates `p` at all 4,096
   positions, and **rebuilds the entire Merkle tree** of this oracle. It can then reconstruct every
   queried leaf, every authentication path, and the native layer data.

Three implementation facts carry the correctness argument, and the report states them as the reason the
reconstruction can be trusted at all:

- the implementation uses **batch inversion in Newton divided differences**;
- it obtains the actual evaluation coordinates from an **NTT transform of a degree-one basis vector**,
  avoiding any assumption that array indices are field coordinates;
- the encoder compares all reconstructed query values and all previously supplied Merkle nodes with the
  original public proof, and additionally checks equality of the **entire expanded native transcript** —
  so a wrong degree assumption, coordinate order, field representation, or tree reconstruction would
  fail those comparisons.

Only the fold and interpolation facts are borrowed as mathematics (`D3-15`: "full (fold,
interpolation); partial (NTT)"); the NTT's correctness is checked by exact transcript equality rather
than re-proved, and no FRI or BaseFold soundness is re-derived (`D3-14`, `D3-21`).

## How the adapter bridged them

`src/adapter/` is the v1.28p adapter — `src/main.rs` and `src/codec.rs` — and `src/adapter/src/codec_v1.rs`
retains the pre-QVT2 codec from which `src/modify_codec.py` re-derives the QVT2 codec byte-identically.
The critical selection rule is stated in the report and is a safety condition, not an optimisation:

> When the public sample count is insufficient for this polynomial form, QVT3 retains the affine
> representation. For the tested profile, both final layers use the polynomial form. Other layers
> retain their prior representation. **Transmitting full coefficients of an insufficiently sampled
> private oracle is not an approved substitution: those coefficients might reveal information absent
> from the old public proof.**

The decoder always invokes the ordinary native verifier and requires transcript exhaustion on the
reconstructed proof, so acceptance of a carrier implies acceptance of its expanded proof for the same
statement — assuming correct implementation of that entry point. Interpolation is **not** substituted
for proof verification, and the codec adds no authorization predicate.

## Tests

| Test | What it asserts | Recorded result |
|---|---|---|
| Codec round trip | decoded native proof equals the original | `roundtrip_byte_exact: true` in both cases; `all_native_checks_retained: true`; `scope: EXACT_NATIVE_TRANSCRIPT_CODEC_UNQUALIFIED` |
| Final-layer accounting | the polynomial form is actually used where claimed | case-0 final layer: `polynomial_mode: true`, `polynomial_carrier_coefficients: 512`, `regenerated_codeword_scalars: 4096`, `boundary_hashes: 0`, `transmitted_scalars: 512`, `terminal_encoded_bytes: 1,024` |
| Isolated public verification | fresh subprocesses receive only the authenticated configuration and the frame bytes | `results/public-verification.json`: both frames `native_verified: true`, `private_input_opened: false`, `expanded_native_sha256` equal to the originals |
| Public conflict extraction | — | exactly seats `0..21` |
| Public negative controls | 22 mutations | all 22 rejected (`results/public-negative-checks.json`) |
| Compression controls | whether generic compression could have done the same | **no**: DEFLATE 283,746 / 279,671, bzip2 285,250 / 281,232, XZ 283,752 / 279,672, all larger than the 283,680 / 279,600 raw frames, with every queried-field section at full binary span (128 bits for field values, 256 for hash values) |
| Seeded-data demonstration | whether generation can replace transmission in general | 588-byte carriers reconstruct 1,023 leaf seeds and 1,047,552 bytes of tapes, exactly, in five cases — but the demo *generates* its data from seeds; it does not compress an existing proof |

The 22 controls add `polynomial_coefficient` and `previous_affine_codec_magic` to the QVT2 set of 20.

## Measured sizes and verification results

Recorded in `results/encode_case{0,1}.json` (the v1.28p encode records) and
`results/public-verification.json`; the frame bytes are retained at
`fixtures/case0/trace43_rate3.pf2p` and `fixtures/case1/trace43_rate3.pf2p` and were re-checked
byte-for-byte against the records for this repository.

| Representation | Case 0 complete frame | Case 1 complete frame |
|---|---:|---:|
| QVT1 (v1.27b) | 283,680 | 279,600 |
| QVT2 (affine) | 282,016 | 277,968 |
| **QVT3 (polynomial)** | **273,952** | **270,304** |
| Target | 32,768 | 32,768 |

| Quantity | Case 0 | Case 1 |
|---|---:|---:|
| Final layer, QVT1 | 17,920 B | 17,488 B |
| Final layer, QVT3 | 8,192 B | 8,192 B |
| Saved against QVT1 | 9,728 B | 9,296 B |
| Native proof (unchanged) | 335,360 B | 335,360 B |
| Encoded proof | 268,240 B | 264,592 B |
| Gates | 402,306 | 407,810 |
| Frame sha256 | `079788fe…29f5` | `4a55fdc2…617a` |
| Expanded native sha256 | `de9d0365…b013` | `f5215457…8656` |

The budget check in the record is unambiguous: `proof_payload_budget: 27,056`,
`encoded_bytes: 268,240`, `fits_budget: false` — **241,184 bytes over budget in case 0**, and
237,536 in case 1. The domain's own wording for the remaining information is: "QVT3 still carries
78,080 / 77,248 bytes of field coefficients and queried values, 172,736 / 169,920 bytes of Merkle
boundary hashes, and 17,424 bytes of prefix, terminal, and codec data. Even hypothetically assigning
all remaining boundary hashes zero cost would leave 95,504 / 94,672 proof bytes."

## Arguments the report makes, and the label on each

| Claim | Label as stated |
|---|---|
| Correctness: for distinct evaluation coordinates, the degree-below-512 interpolating polynomial is unique; when the public reconstruction checks succeed, every supplied final-layer value and authentication node equals the original, so the decoder recovers the original native proof | **construction argument** (correctness argument), supported by exact replay and finite negative tests |
| Acceptance: the public entry point always invokes the ordinary native verifier and requires transcript exhaustion, so acceptance of a carrier implies acceptance of its expanded proof | **construction argument**, conditional on correct implementation of the entry point |
| Privacy: the encoder uses only the old public proof and public statement, so it is efficient public postprocessing and cannot disclose information unavailable to an observer performing the same computation; if the original proof distribution has a suitable ZK simulator, the encoded distribution preserves indistinguishability | **conditional** privacy argument — explicitly does not establish a ZK or QPT theorem for the unqualified backend |
| The "zero-cost boundary hashes" figures | **accounting**, not a lower bound against another protocol |
| The counting argument for fixed-length decoders | elementary, and explicitly **does not** rule out a 32 KiB CE-QS proof |

## Conclusion

QVT3 is the best representation in this domain: it removes 9,728 and 9,296 bytes from the frames of a
relation it does not change, on proofs it does not regenerate, and it does so by exploiting sampling
that the transcripts genuinely already contained. It also closes the avenue it appears to open: the
same trick cannot be applied to an insufficiently sampled oracle without a disclosure risk, the
boundary hashes remain the dominant term, and the report's own route for the remaining gap is a
*generative* proof with selective seed disclosure and authenticated corrections —

```
|opened seed description| + |corrections| + |binding/consistency evidence| + |other proof data| ≤ 27,056
```

— which is stated as a research direction, not as an instantiated protocol. The report's closing
position, which this repository repeats: the immediate result is an implemented polynomial carrier,
not completion of the 32 KiB goal.
