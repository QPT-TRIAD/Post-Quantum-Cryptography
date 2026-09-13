# 03 — The construction: profile B0 end to end

This package specifies the CE-QS quorum certificate as an implementable object: the frame, every
field and every byte, the order a verifier executes it in, the two profiles that share the frame,
the sizes that were measured, and the parameters the construction fixes. A reader who implements
only what is written here produces frames that the reference implementation accepts.

**Notation.** `N` = 64 seats, indices `0..63`; `QUORUM` = 43; `F` = 21 (fault bound);
`MIN_OVERLAP` = `2·QUORUM − N` = 22; `W` = a signature scheme's fixed signature width in bytes.
Paths are relative to the repository root.

## 1. The object

A **certificate** is a portable byte string of at most 32,768 bytes. A verifier that holds only the
authenticated 64-seat registry can check it alone: no sidecar file, no external leaf list, no
proving transcript, and no secret opener. Two certificates that conflict — same configuration, same
conflict domain, different message — publicly expose at least 22 seats that authorized both.

The certificate is produced by a quorum of 43 of the 64 seats. `N = 3F + 1` and `QUORUM = 2F + 1`
hold at `(64, 21, 43)`.

## 2. The problem

Two requirements pull against each other.

1. **The conflict witness is a counting fact, not a cryptographic one.** Any two 43-subsets of a
   64-set intersect in at least `43 + 43 − 64 = 22` seats. The witness therefore exists whenever
   both certificates are authentic. The work is making it *publicly computable from the two
   certificates alone*, with no opener secret and no extra evidence file.
2. **The size budget is tight for post-quantum signatures.** 32,768 bytes for a 208-byte header, an
   8-byte bitmap and 43 signatures leaves 757 bytes per signature. No FIPS-standardized signature
   fits. The two FIPS schemes named in the reference's size table are ML-DSA-87 at 4,627 bytes
   (FIPS 204 Table 2 **and measured here** — it is one of the rows `--real-demo` rejects as
   oversize) and SLH-DSA-SHAKE-256s at 29,792 bytes (FIPS 205 Table 2, **quoted, not measured** —
   no recorded run executes it; see `sizes.md` §4). The schemes that fit are candidates in NIST's
   additional-signature process.

A third requirement, **hidden signers**, is stated by the programme as part of the target. It is
not met, and this package says so wherever it is relevant.

## 3. The two profiles

Both profiles share one 208-byte header and one suite identifier field. They differ in payload.

| | **B0** — public signer set | **B1** — hidden signers ("Mode S") |
|---|---|---|
| suite id (`u16`, big-endian) | `0x44B0` | `0x44B1` |
| payload | 8-byte bitmap ‖ 43 fixed-width signatures | 43 handles (128 B each) ‖ one proof |
| `payload_len` | `8 + 43·W` | `5,504 + proof_len` |
| frame length | `216 + 43·W` | `5,712 + proof_len`, `proof_len ≤ 27,056` |
| signers | public — the bitmap names them | hidden by construction |
| status | executable reference; measured with real signatures | frame, relation and algebraic extractor executable; **no qualified proof backend exists**, and `verify_b1` never reports authorization |

`0x44B0` is the B0 profile identifier, and `0x44B1` is the B1 profile identifier. They are written
as the `suite` field of the header (`docs/03-construction/wire-format.md` §2).

## 4. The measured sizes, with the arithmetic

Frame size is `208 (header) + 8 (bitmap) + 43·W = 216 + 43·W`. The size gate is

```
W ≤ (32,768 − 216) // 43 = 32,552 // 43 = 757       757 → 32,767 bytes fits
                                                    758 → 32,810 bytes does not
```

| Scheme (claimed category) | `W` | Signature block `43·W` | Frame `216 + 43·W` |
|---|---:|---:|---:|
| **OV-V-pkc** (5) | 260 | 43 · 260 = 11,180 | 216 + 11,180 = **11,396** |
| SNOVA_29_6_5 (5) | 454 | 43 · 454 = 19,522 | 216 + 19,522 = **19,738** |
| SNOVA_60_10_4 (5) | 576 | 43 · 576 = 24,768 | 216 + 24,768 = **24,984** |
| **OV-V-pkc‖SNOVA_29_6_5** (5) | 714 | 43 · 714 = 30,702 | 216 + 30,702 = **30,918** |
| MAYO-5 (5) | 964 | 43 · 964 = 41,452 | 216 + 41,452 = 41,668 — **oversize** |
| ML-DSA-87 (5) | 4,627 | 43 · 4,627 = 198,961 | 216 + 198,961 = 199,177 — **oversize** |
| Falcon-padded-512 (1) | 666 | 43 · 666 = 28,638 | 216 + 28,638 = 28,854 — fits, but **category 1** |

All seven rows are **measurements**: they were produced by `--real-demo` against real signature
libraries, and reproduced in this repository. Provenance for each row, and the split between
measured and specification-quoted numbers, is in `docs/03-construction/sizes.md`.

## 5. Read this package in this order

| # | File | What it gives |
|---|---|---|
| 1 | `README.md` (this file) | the object, the problem, the profiles, the sizes, the map |
| 2 | `construction.md` | the construction step by step in the order a **verifier** executes it, with each step's purpose, inputs, outputs, failure mode and assumption |
| 3 | `wire-format.md` | the B0 frame as bytes: field, offset, width, encoding, valid range, and worked examples with their hexadecimal encodings |
| 4 | `profiles.md` | B0 and B1 side by side: what each admits, measures and proves, and the exact acceptance rule for a new signature scheme |
| 5 | `sizes.md` | every size with its source, marked *measured here*, *measured elsewhere* or *quoted from a specification* |
| 6 | `parameters.md` | every parameter the construction fixes, its value, where it comes from, and what breaks if it changes |
| 7 | `VERIFICATION.md` | each command re-run, the recorded baseline, the observed result and the verdict |

## 6. What rests on what

The construction's correctness has four separate supports, and they must not be conflated.

- **The frame logic** (encode, verify, extract, blame) is checked by 39 unit tests in the reference
  module and, independently, by a second implementation written from the wire specification alone
  that agreed with the reference on 6,701 of 6,701 checks over 900 generated vectors. It is not
  formally verified.
- **The size arithmetic** — the formula and the 757/758 gate — is asserted exactly by the tests and
  confirmed by the measurements in §4.
- **The security statement** is Theorem A of the QPT-128 finalization: accountability is
  deterministic; non-frameability and safety reduce tightly to the EUF-CMA security of the chosen
  signature scheme, a named assumption (`A-sig`) about non-FIPS candidates. Under the programme's
  gate accounting the target holds with a **+23.0-bit margin**.
- **Hidden signers together with 32 KiB** are **not** achieved. The gap is quantified by Theorem C
  for witness-committing proof families, which is a necessary condition for those families and not a
  universal lower bound. B1's own single-witness figure is a **lower bound** and its Theorem C is
  not a proof of a working scheme: no proof backend exists.

## 7. What this package does not claim

- No signature scheme is claimed to be category 5 beyond its submitters' own claim. The category
  value in every table is the library's `claimed_nist_level`, a submitter claim.
- No measured frame size is a security bound or a proof of anything. The measurements say what
  these library builds produced on the host named in `sizes.md`.
- B0 does not hide its signers. The 8-byte bitmap is in the clear.
- The reference implementation is not constant-time, and no side-channel testing was performed.
- The demo covers frames only: no network protocol, no key management, no liveness.

## 8. Where the raw material lives

| What | Where |
|---|---|
| Normative wire specification for B0 | `domains/07-compact-certificate-b0/docs/b0-wire-spec.md` |
| Reference module (B0 and B1, 39 tests) | `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` |
| Closure document: the seven requirements, the measured table, rejected designs, the falsification criterion | `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md` |
| Recorded run outputs (self-test, report, real demo, probes) | `domains/07-compact-certificate-b0/results/` |
| Independent implementation, 900 vectors, 6,701/6,701 checks, 18 specification gaps | `domains/11-independent-audit-stack/independent-b0/` |
| QPT-128 target and Theorems A and B | `domains/06-qpt128-security-target/` |
| How the construction got here, revision by revision | `domains/02-ceqs-construction-evolution/` |
| Why the extractor is the load-bearing part, and what the signature reduction costs | `domains/05-extraction-and-signature-reductions/` — `README.md`, then `docs/extraction-argument.md`, `docs/signature-reductions.md`, `docs/joint-extractor-lift.md`; nine runnable revisions in `src/` |
| Hidden signers past 32 KiB, and the measured Mode B certificate | `domains/08-hidden-signers/docs/hidden-signer-32kib.md` and `domains/08-hidden-signers/docs/mode-b-security.md`; raw runs in `results/` (this domain has no `README.md`) |
