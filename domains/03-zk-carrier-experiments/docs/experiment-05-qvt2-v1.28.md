# Experiment 5 — v1.28, QVT2: reconstructing a queried value from the fold that determines it

## The problem

By the end of experiment 4 the diagnosis was precise: in the retained transcripts, the transmitted
queried field values alone (81,376 and 80,304 bytes) exceeded the whole 27,056-byte proof position, and
the Merkle boundary hashes added 179,168 and 176,160 more. Shrinking the *relation* had bought almost
nothing. So this experiment stopped touching the relation and asked the question the report states
first: **what is information, and what is redundancy that a decoder can regenerate?**

The formalism the report introduces — and which both this and the next experiment use — is a **lossless
carrier**: an efficient pair

```
c = E(x, π),        D(x, c) = π,        V_c(x, c) = V(x, D(x, c))
```

where `x` is the public configuration and complete public statement and `π` is the native proof. The
carrier transmits only independent information; the decoder regenerates everything determined by that
information and `x`; and the verifier runs the fixed decoder and then the original verification
algorithm. The rules attached to it matter as much as the definition: a fixed public algorithm is
shared across certificates, but **per-certificate programs, coefficients, seeds, dictionaries, model
weights, corrections and algorithm parameters are certificate data and must be counted** — and a
pointer to an unavailable program or proof is not reconstruction.

## The relation carried

`CEQS12B_FIXED_CONTEXT`, unchanged (see `docs/experiment-04-fixed-context-v1.27b.md`). No new signing
credentials and no new native proofs were generated in this experiment: both codecs transform the
**public proofs retained from v1.27b**. The frames are `PF28`, version 28, suite `0x28b3`.

## The backend, and which part of its theory applies

Backend unchanged. The part of its theory used here is the opening structure (`D3-14`) plus two
elementary facts about the fold and about interpolation (`D3-15`):

- In the final FRI layer the verifier checks a linear fold `y = Σ_{j=0}^{b-1} w_j v_j`, where `y` is
  determined by the terminal codeword — and terminal polynomial coefficients were **already** fully
  present in QVT1. So one coordinate is a linear function of the others and of data the carrier
  already sends.
- Linearised FRI fold and the uniqueness of the interpolating polynomial are elementary; the additive
  NTT over the Gao–Mateer basis is a *backend* part whose correctness is checked by full-transcript
  equality rather than re-proved (the domain marks this split as `D3-15`, "full (fold,
  interpolation); partial (NTT)").

Only the fold fact is used. Nothing about FRI soundness is re-derived: soundness is inherited from the
native verifier call, exactly as the domain's `D3-14` and `D3-21` entries require.

## How the adapter bridged them

`history/v1.28/adapter/` holds the QVT2 adapter (`Cargo.toml`, `Cargo.lock`, `src/main.rs`,
`src/codec.rs`). QVT2 works as follows:

1. Choose a deterministic coordinate `p` not already known, with nonzero weight.
2. Omit `v_p` from the carrier and reconstruct it in the decoder by

   ```
   v_p = w_p^{-1} ( y − Σ_{j≠p} w_j v_j ).
   ```

3. If no eligible pivot exists, the codec **retains** the necessary values and checks the fully
   determined equation. There is no sampling assumption and no silent dropping: the fallback is an
   exact representation.
4. The representation is moved before the query data in the carrier, but the decoder still feeds the
   reconstructed native transcript to the verifier **in its original order**, so the transcript the
   verifier sees is the original one.

The v1.28p generation of this code is `src/adapter/src/codec.rs`; the pre-QVT2 codec is kept as
`src/adapter/src/codec_v1.rs`, and `src/modify_codec.py` re-derives the QVT2 codec from it. That
script was executed for this repository and reproduces `history/v1.28/adapter/src/codec.rs`
**byte-identically** (sha256 `82efda3fa777f733d929e0180dbef194b74ebe0daefce21a55ff52c11a431578`) — see
`VERIFICATION.md` §2. It is the only reproduction of a codec transformation available without the
native binaries.

## Tests

| Test | What it asserts | Recorded result |
|---|---|---|
| Affine round trip | the decoded native proof equals the original, byte for byte | both cases: `roundtrip_byte_exact: true`; the report states both decoded native proofs are byte-for-byte identical to their originals |
| Recovered elements | the number of field elements the fold replaces | **104** in case 0, **102** in case 1 |
| Isolated public verification | both `PF28` frames verified in fresh subprocess directories receiving only the authenticated public configuration and the complete frame bytes | `history/v1.28/public_verification.json`; expanded native-proof sha256 equals the originals |
| Expanded digest equality | the reconstructed native proof hashes to the original | `results/carrier-audit.json` records `native_sha256` `de9d0365…b013` (case 0) and `f5215457…8656` (case 1), identical for the QVT2 and QVT3 rows — `same_native_proof: true` |
| Public conflict extraction | the two frames still yield the common seats | exactly seats `0..21` |
| Public negative controls | 20 mutations | all 20 rejected (`history/v1.28/public_negative_checks.json`) |
| Private-witness involvement | — | none: "no private witness file is supplied or created by this codec experiment" |

The 20 controls add two names to candidate B's 18: `preloaded_terminal_coefficient` and
`previous_codec_magic`.

## Measured sizes and verification results

Recorded in `history/v1.28/encode_case{0,1}.json`; not re-measured here.

| Representation | Case 0 complete frame | Case 1 complete frame |
|---|---:|---:|
| Previous QVT1 (v1.27b) | 283,680 | 279,600 |
| **QVT2: affine terminal reconstruction** | **282,016** | **277,968** |
| Target | 32,768 | 32,768 |

Supporting quantities for the same run: encoded proof bytes 276,304 (case 0) and 272,256 (case 1);
native proof bytes 335,360 in both, unchanged; saving 1,664 and 1,632 bytes; `fits_budget: false`;
`saved_bytes` against the native proof 59,056 and 63,104.

## What it did not do

QVT2 saves 1,664 bytes — about 0.6 % of the frame. The accounting in this domain's audit
(`results/evidence-audit.json`, `results/carrier-audit.json`) shows where the rest is: 79,712 and
78,672 bytes of field values, 179,168 and 176,160 bytes of boundary hashes, and 17,424 bytes of fixed
and terminal data. The report's conclusion is that "an effective next proof construction must reduce
the queried-value representation as well as authentication data, while retaining the same relation
checks and a proved quantum soundness/knowledge bound" — and it states that silently dropping those
values would fail the native verifier's checks.

## Conclusion

QVT2 established, on real proofs, that a linear dependency can be removed from the carrier without
changing what is verified: the same two native proofs are reconstructed byte-for-byte and re-verified,
and the two frames are 1,664 and 1,632 bytes smaller. It also established the limit of that particular
trick — one coordinate per eligible leaf. The next experiment went after the whole final layer instead.
