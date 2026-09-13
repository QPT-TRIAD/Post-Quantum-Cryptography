# Sizes, and where each number comes from

Every number in this package appears here with its provenance. The labels mean exactly this:

| label | meaning |
|---|---|
| **measured here** | produced by a command re-run **in this repository** on 2026-09-13, against the repository copy of the reference module, in the pinned environment named in §1. The raw output is in `domains/07-compact-certificate-b0/results/`. |
| **measured elsewhere** | a measurement recorded by **another domain of this repository**, from that domain's own run. Named per row. |
| **quoted — spec** | transcribed from a **published specification or paper**. Not executed. |
| **quoted — paper** | a measurement published by a third party. Not executed here. |
| **arithmetic** | computed from numbers in the same row by the stated formula. Not independently observed. |

No number in this package is a security bound. A size says what a build produced; it says nothing
about whether the producing scheme is secure.

---

## 1. The environment

**All rows labelled *measured here*.** Host: Ubuntu 24.04.4, x86_64, kernel 7.0.0-31, CPython 3.12.3.
Library builds: **liboqs 0.16.0**, locally built shared library at commit
`5a1a854b0dc9f2141bdc771c555ee60c37950183` (`-DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON
-DOQS_DIST_BUILD=ON`), exported through `OQS_INSTALL_PATH`; **liboqs-python 0.16.0**;
**pqcrypto 0.3.4**. The activation script and the exact commands are in
`docs/03-construction/VERIFICATION.md`.

The reference module is `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`.
Its own test suite is 39 tests; `--self-test` passes (`Ran 39 tests`, `OK`) in this environment.

---

## 2. The frame sizes that were measured

The formula, and its two constants:

```
frame  = 208 (header) + 8 (bitmap) + Σ over 43 slots of W
       = 216 + 43·W
gate   = W ≤ (32,768 − 216) // 43 = 32,552 // 43 = 757
         757 → 216 + 43·757 = 216 + 32,551 = 32,767  fits (1 byte to spare)
         758 → 216 + 43·758 = 216 + 32,594 = 32,810  does not fit
```

Source of the gate: `B0_MAX_SIGNATURE_BYTES = (MAX_FRAME_BYTES − B0_FIXED_BYTES) // QUORUM` in the
reference, and `b0_size_gate` in `--report` (`sig_bytes_757_fits: true`,
`sig_bytes_758_fits: false`, `frame_bytes_at_757: 32767`) — **measured here**.

Every row of the table below is **measured here** unless the last column says otherwise. The
`43·W` and frame columns are **arithmetic** on the `W` and public-key columns, which are the
measured values; the demo asserts `len(frame0) == 216 + 43·W` for each row, so the arithmetic is
also observed, not merely computed.

| # | Scheme (claimed category) | Library | `W` (B) | Public key (B) | `43·W` | Frame (B) | Verdict | Source |
|---|---|---|---:|---:|---:|---:|---|---|
| 1 | **OV-V-pkc** (5) | liboqs | 260 | 446,992 | 11,180 | **11,396** | verified, 22 extracted, blame ok, tamper rejected | measured here |
| 2 | SNOVA_29_6_5 (5) | liboqs | 454 | 2,716 | 19,522 | 19,738 | same | measured here |
| 3 | SNOVA_60_10_4 (5) | liboqs | 576 | 8,016 | 24,768 | 24,984 | same | measured here |
| 4 | **OV-V-pkc‖SNOVA_29_6_5** (5) | liboqs | 714 | 449,712 | 30,702 | **30,918** | same; both halves tamper-rejected | measured here |
| 5 | MAYO-5 (5) | liboqs | 964 | 5,554 | 41,452 | 41,668 | **oversize** | measured here |
| 6 | ML-DSA-87 (5) | liboqs | 4,627 | 2,592 | 198,961 | 199,177 | **oversize** | measured here |
| 7 | ML-DSA-87 (5) | pqcrypto | 4,627 | 2,592 | 198,961 | 199,177 | **oversize** | measured here |
| 8 | Falcon-padded-512 (1) | pqcrypto | 666 | 897 | 28,638 | 28,854 | verified, **category 1** | measured here |

Eight runs over **seven distinct schemes** — ML-DSA-87 is run under both libraries and produces the
same width and the same frame under each. The reference's own size table lists it once.

**Recorded run and this run.** The recorded `--real-demo` output is
`domains/07-compact-certificate-b0/results/real-demo.json`. Re-running the same command in this
repository produced output **identical in every top-level field** — `real_demo`, `schemes`,
`liboqs_version`, `liboqs_python_version`, `category5_fitting_verified`, `summary` — including all
eight frame sizes above. Wall time differed (recorded 13.7 s; observed 57.1 s on the verification
host under load). The numbers did not. See `VERIFICATION.md`.

**Derived facts about this table, all arithmetic on measured values:**

- The four accepted rows span 11,396 – 30,918 bytes, i.e. 35 % – 94 % of the 32,768-byte budget.
- The two oversize rows exceed it by 41,668 / 32,768 = 1.27× and 199,177 / 32,768 = **6.08×**.
- ML-DSA-87's single signature (4,627 B) is 6.11× the per-seat slot (757 B). One signature does not
  fit where 43 are needed.
- Falcon-padded-512 fits with 32,768 − 28,854 = 3,914 bytes to spare and is still inadmissible, at
  category 1.
- Overhead: the fixed 216 bytes are 216 / 11,396 = 1.90 % of the smallest frame above and
  216 / 30,918 = 0.70 % of the largest.

---

## 3. The size table's other rows — quoted, not run

The reference carries eleven entries in `SIGNATURE_SIZE_TABLE`. Four of them no recorded run covers.
They are reproduced here **as the reference prints them**, with the provenance corrected per row:

| Entry | Category | `W` (B) | Frame `216 + 43·W` | Provenance of `W` | Was it executed? |
|---|---:|---:|---:|---|---|
| SLH-DSA-SHAKE-256s | 5 | 29,792 | 1,281,272 | **quoted — spec**: FIPS 205, Table 2 | **No.** See §4 |
| Falcon-padded-1024 | 5 | 1,280 | 55,256 | **quoted — spec**: Falcon round-3 padded signature size | **Not in the archived run.** See §4 |
| SQIsign-V | 5 | 292 | 12,772 | **quoted — spec**: SQIsign round-2 specification | **No** — the reference labels it `not executed here` |
| HAWK-1024 | 5 | 1,221 | 52,719 | **quoted — spec**: HAWK round-2 specification | **No** — same label |

Of these four, **SQIsign-V would fit** (`12,772 ≤ 32,768`, with 19,996 bytes to spare) if its
specification size were realised in an implementation. The other three cannot fit at any
implementation of the stated size. None of the four may be read as an admissible scheme here: no
run has confirmed any of their widths, their category claims, or their behaviour under the
procedure in `profiles.md` §2.2.

---

## 4. The provenance gap in `SIGNATURE_SIZE_TABLE`, stated plainly

Three entries in the reference's size table carry a `source` string that ends **"measured liboqs
0.16.0"**:

```
ML-DSA-87              'FIPS 204, Table 2; measured liboqs 0.16.0'
SLH-DSA-SHAKE-256s     'FIPS 205, Table 2; measured liboqs 0.16.0'
Falcon-padded-1024     'Falcon round-3 padded signature size; measured liboqs 0.16.0'
```

Reading `real_demo()` in the module shows what the recorded `--real-demo` run actually executes:
from pqcrypto it loads **`falcon_padded_512` and `ml_dsa_87` only**; from liboqs it loads the
enabled providers whose claimed level matches. Consequently:

| Entry | `source` says | `--real-demo` actually runs it? |
|---|---|---|
| ML-DSA-87 | measured liboqs | **yes** — and also under pqcrypto. Width 4,627 confirmed by both. |
| SLH-DSA-SHAKE-256s | measured liboqs | **no** — no row in `domains/07-compact-certificate-b0/results/real-demo.json` |
| Falcon-padded-1024 | measured liboqs | **no** — no row in `domains/07-compact-certificate-b0/results/real-demo.json` |

The domain's own record confirms this: `domains/07-compact-certificate-b0/VERIFICATION.md` states
that *"the Falcon-padded-1024 liboqs probe and the pqcrypto version of the original run were
likewise not archived"*. So the two library-measured-looking rows rest on a probe that exists as a
claim, not as an archived result.

**How this package uses them.** The two rows appear in `profiles.md` §2.4 and in this section, and
**never** in the measured table of §2. They are counted as *quoted from a specification*, with the
library-measurement part of their source string treated as unverified for the purposes of this
package. This is a provenance inconsistency in the reference's own metadata, recorded here rather
than corrected, because the reference must stay the revision the measurements were taken on.

**What would close it.** A `--real-demo`-shaped run that loads `sphincs_shake_256s_simple` and
`falcon_padded_1024` and records their measured widths in an archived JSON. Both are standard
liboqs/pqcrypto mechanisms; the recorded run simply does not request them.

---

## 5. The header, the bitmap, and the two profiles' fixed parts

All **measured here** unless noted. These are decoded from the frames the module produces and, in
the worked case, from the hexadecimal in `wire-format.md` §§3 and 5.

| Quantity | Value (B) | Where it comes from |
|---|---:|---|
| `HEADER_BYTES` | 208 | `struct.calcsize('>4sHH64s64s64sHHI')`, asserted by the module and by `--report` |
| header without `payload_len` | 204 | `struct.calcsize('>4sHH64s64s64sHH')` = `STATEMENT_FORMAT` |
| bitmap | 8 | one bit per seat, `N = 64` exactly |
| `B0_FIXED_BYTES` | 216 | 208 + 8 — header plus bitmap, before any signature |
| signature slots | 43 | `COUNT = QUORUM` |
| per-seat slot at the gate | 757 | `(32,768 − 216) // 43` |
| largest frame that fits | 32,767 | `216 + 43·757`; one byte of budget unspent because 43 ∤ 32,552 |
| smallest measured B0 frame | 11,396 | row 1 of §2 |
| largest measured B0 frame that fits | 30,918 | row 4 of §2 |
| worked-example frame (`W = 32`) | 1,592 | `216 + 43·32 = 216 + 1,376`; `payload_len = 8 + 1,376 = 1,384` = `0x00000568` |
| `HANDLE_BYTES` (B1) | 128 | `B1_REGISTRY_KEY_BYTES`; registry keys are 128 bytes for the ledger's collision-resistance requirement |
| B1 handles | 5,504 | `43 · 128` |
| `B1_PREFIX_BYTES` | 5,712 | `208 + 5,504` |
| `B1_PROOF_MAX` | 27,056 | `32,768 − 5,712` |
| B1 at the limit | 32,768 | `5,712 + 27,056`, exactly the budget |
| B1 structure-only example | 5,752 | `5,712 + 40`; the 40-byte ASCII marker `STRUCTURE-ONLY/NOT-A-PROOF/CQ44-B1/v1.44` that `StructureOnlyTestBackend` emits |

The B1 rows are **arithmetic** on constants read from the module plus one **measured here** frame
(the 5,752-byte example of `wire-format.md` §5). No B1 proof of any real size exists to measure:
`verify_b1` reports `STRUCTURE_ONLY_NO_QUALIFIED_PROOF` and `authorization_verified = False` for
every frame, by construction.

---

## 6. The registry — the size that is *not* in the frame

The frame carries no public keys. The verifier holds a 64-seat registry out of band, so this cost is
real but does not appear in any frame size above. Per-seat public-key sizes are **measured here**
(the demo records `public_key_bytes` for each row); the 64-seat totals are **arithmetic**:

| Scheme | Public key (B) | 64-seat registry (B) | Frame (B) | Registry ÷ frame |
|---|---:|---:|---:|---:|
| OV-V-pkc | 446,992 | 28,607,488 | 11,396 | 2,510× |
| SNOVA_29_6_5 | 2,716 | 173,824 | 19,738 | 8.8× |
| SNOVA_60_10_4 | 8,016 | 513,024 | 24,984 | 20.5× |
| OV-V-pkc‖SNOVA_29_6_5 | 449,712 | 28,781,568 | 30,918 | 931× |
| ML-DSA-87 (oversize anyway) | 2,592 | 165,888 | 199,177 | 0.83× |
| Falcon-padded-512 (category 1) | 897 | 57,408 | 28,854 | 2.0× |

The registry also holds 64 secret keys, whose lengths the demo does not record. **This is a real
cost of the construction and it is asymmetric**: the frame is small, the verifier's state is not.
The reference's own size table records OV-V's standard public key as 2,869,440 bytes and the
compressed `-pkc` form as 446,992; the frame measurements above use the `-pkc` form.

---

## 7. Sizes from the other domains of this repository

**Measured elsewhere** — recorded by the named domain, not re-run for this package.

| Quantity | Value | Source | What it is |
|---|---:|---|---|
| Mode B production certificate | **30,684 B** | `domains/08-hidden-signers/docs/mode-b-security.md` §8 **prose table only** — see the caveat below | claimed: a **verified** hidden-signer certificate at 2^20 trees, τ = 11, w_g = 16, ρ = 4,096, 22 seats extracted, tampering rejected. 2,084 B under the bound. Not a B1 frame — Mode B is a different construction (n = 256, GF(2^256), F: F₂^512 → F₂^1024) |
| Mode B production proof, from the formula | 29,100 B | same | `h_com 64 + (τ−1)·1,912 + 1,912 + 64 + 192 + 4 + τ·(32b + 64)` |
| Mode B at 2^22 leaves | 28,708 B | same | one fewer repetition: −1,976 B, prover cost ×3.6 |
| Mode B **reduced** setting | **49,108 B** | `domains/08-hidden-signers/results/prover-v1.49-run.json`, `prover-v1.50-run.json`, `prover-v1.51-run.json`, `prover-v1.51-asan-run.json` | **archived raw result**: b = 12, τ = 20, w_g = 8, ρ = 1,024, proof 47,524 B, frame 49,108 B, `fits_32768: false`, `verified: [true, true]`, `tampered_rejected: true`, `extracted_count: 22` |

**Caveat on the 30,684-byte production figure — it is not in an archived result.** A search of every
file in `domains/08-hidden-signers/results/` for `30684`, `30,684`, `29100` and `29,100` returns
**nothing**. All four archived run records (`prover-v1.49-run.json`, `prover-v1.50-run.json`,
`prover-v1.51-run.json`, `prover-v1.51-asan-run.json`) carry the *reduced* parameter set —
`b = 12, τ = 20, w_g = 8, ρ = 1,024` — at `proof_bytes: 47,524`, `frame_bytes: 49,108`,
`fits_32768: false`. The production figures exist only in the **prose** of
`domains/08-hidden-signers/docs/mode-b-security.md` §8 and `domains/08-hidden-signers/docs/hidden-signer-32kib.md`, not in a machine-readable record.

So, for this package:

- The **reduced** Mode B run is **measured elsewhere** — it has an archived JSON, and it is worth
  recording that **it does not fit the 32 KiB bound** (49,108 > 32,768).
- The **production** 30,684-byte certificate is **claimed in prose**, and this package does not
  treat it as a measurement. The largest *archived* hidden-signer frame in this repository is
  49,108 bytes.
- Neither figure is a B1 frame, and neither makes B1's 27,056-byte proof slot any less empty. Mode B
  is a different construction with its own frame format, its own `prefix_bytes: 1,584`, and its own
  parameters.

The record should not be read as saying the production run did not happen — it says the run is not
archived here, so a reader of this repository cannot check it. Re-running the production setting is
possible in principle (2^20 leaves, ≈97 s of prover time at 12 cores per the same table) and would
close the gap.

**Quoted — paper.**

| Quantity | Value | Source |
|---|---:|---|
| VOLE-in-the-head ring signature, AES-256-EM, **one** hidden signer among 2^6 | 21.49 KB | Chiang et al., CCS'25, ePrint 2025/113, Table 2, λ = 256, not linkable — as transcribed in the reference's closure document §3.4 |

This is a **lower bound on the single-witness case**, published by a third party, and it is already
two thirds of the budget for *one* hidden signer. B1 needs **43** distinct hidden signers with
linkable handles. It is not an estimate of any B1 certificate, and no such certificate exists.

---

## 8. Estimates and lower bounds — labelled as such

All from `--report` (**measured here**: the module computes them and the tests assert them), all
**estimates or lower bounds, not measurements of a built object**, and none of them a certificate
size:

| Quantity | Value | Status |
|---|---:|---|
| Mode S linear-family lower bound | 412,800 B | **estimate**; exceeds the 27,056-byte proof budget by 15.3× |
| Binius64 PCS floor (96-bit) | 109,856 B | **estimate** from re-implemented estimators; exceeds the budget by 4.1× |
| Mode S committed words, minimum | 51,600 | estimate |
| Mode S `log₂` committed ceiling | 16 | estimate |
| `Keccak-f[1600]` AND gates | 38,400 | estimator constant |
| Binius64 ANDs per Keccak permutation | 600 | estimator constant |
| Mode S Keccak permutations | 86 | estimator constant |
| Theorem C: challenge bits required | 212 | **necessary condition** for witness-committing families at `h = 0`; 180 at `h = 16` |
| Theorem C: credential bits required, 64 targets | 218 | same |
| Theorem C: attack gates per hash, `log₂` upper bound | 24 | the assumption the bound rests on |

`domains/07-compact-certificate-b0/results/report.json`'s `lower_bounds` block carries the derived booleans
`linear_floor_exceeds_budget: true` and `binius64_floor_exceeds_budget: true`.

**The status of Theorem C.** It bounds witness-committing proof families (KKW-, BN++-,
FAEST-style). It is a **necessary condition for those families**, not a universal lower bound, and
it is not a proof that no hidden-signer certificate exists. `profiles.md` §3.4 states this where it
matters, and no reader should take this package as proving B1 impossible.

---

## 9. Every number in this package, in one place

| Number | Where it appears | Provenance |
|---|---|---|
| 32,768 B | `MAX_FRAME_BYTES`, budget | reference constant; the programme's requirement R1 |
| 216 B | header + bitmap | measured here (208 + 8) |
| 8 B | bitmap | reference constant, `N = 64` |
| 208 B | header | `struct.calcsize`; measured here |
| 43 | signatures / handles per frame | reference constant `COUNT = QUORUM` |
| 757 / 758 | size gate | measured here (`b0_size_gate` in `--report`) |
| 11,396 B | OV-V-pkc frame | measured here, `--real-demo` |
| 19,738 B | SNOVA_29_6_5 frame | measured here, `--real-demo` |
| 24,984 B | SNOVA_60_10_4 frame | measured here, `--real-demo` |
| 30,918 B | OV-V-pkc‖SNOVA_29_6_5 frame | measured here, `--real-demo` |
| 41,668 B | MAYO-5 frame, rejected | measured here, `--real-demo` |
| 199,177 B | ML-DSA-87 frame, rejected | measured here, `--real-demo` (both libraries) |
| 28,854 B | Falcon-padded-512 frame, admissible but category 1 | measured here, `--real-demo` |
| 1,592 B | toy worked example, `W = 32` | measured here, `wire-format.md` §3 / §7 |
| 5,712 / 27,056 / 5,752 B | B1 prefix / proof budget / structure-only example | arithmetic on module constants + one frame measured here |
| 30,684 B | Mode B production certificate | **claimed in prose only** — no archived result carries it (§7) |
| 49,108 B | Mode B reduced-setting frame | measured elsewhere, archived in `domains/08-hidden-signers/results/prover-v1.5*-run.json`; does **not** fit |
| 29,792 / 1,280 / 292 / 1,221 B | SLH-DSA-SHAKE-256s / Falcon-padded-1024 / SQIsign-V / HAWK-1024 widths | quoted — spec (§3, §4) |
| 21.49 KB | single hidden signer, ring signature | quoted — paper (§7) |
| 412,800 / 109,856 B | Mode S linear and Binius64 floors | estimates (§8) |
| 212 / 218 / 24 | Theorem C budgets and assumption | necessary condition for witness-committing families (§8) |
