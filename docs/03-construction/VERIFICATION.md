# Verification — docs/03-construction

Every command this package depends on was re-run on **2026-09-13** against the **repository copy**
of the reference module, and compared with a recorded value. Where a recorded value did not recur,
both values are kept below and the reason is given.

**Environment.** The programme's pinned verification environment: an activation script for a shell
that puts CPython 3.12.3, liboqs 0.16.0 (locally built shared library, exported through
`OQS_INSTALL_PATH`; commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`,
`-DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON -DOQS_DIST_BUILD=ON`), liboqs-python 0.16.0 and
pqcrypto 0.3.4 on the path. Host: Ubuntu 24.04.4, x86_64, kernel 7.0.0-31. Commands are run from
the repository root unless a path says otherwise.

`$M` abbreviates `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`. The
**recorded baseline** for this package is the raw output archived by the domain-07 build in
`domains/07-compact-certificate-b0/results/`; where the archived file is itself the recorded value,
the row says so.

---

## 1. Reproduction table

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| self-test passes | `python3 $M --self-test` | pinned env | `Ran 39 tests`, `OK`, exit 0 (`domains/07-compact-certificate-b0/results/self-test.txt`) | `Ran 39 tests`, `OK`, exit 0; the 39 test names match the recorded list | reproduced | the suite covers the frame logic this package documents: size gate, width mismatch, wrong cfg/domain/message/suite, popcount 42 and 44, all overlaps 22–43, blame, B1 body and proof budget, Theorem C budgets |
| self-test timing | same | pinned env | `Ran 39 tests in 0.180s` (`domains/07-compact-certificate-b0/results/self-test.txt`); the source-tree reading pass recorded `0.094s` | `0.135s`, `0.180s`, `0.197s` on three runs | reproduced-with-difference | host load only; the recorded figure recurs and no test result changed |
| `--report` content | `python3 $M --report` | pinned env | `domains/07-compact-certificate-b0/results/report.json` — size tables, gate, lower bounds, Theorem C budgets | exit 0; parsed and compared key by key: **every top-level key identical**, including `module` | reproduced | compared against `domains/07-compact-certificate-b0/results/report.json`, which already carries the rewritten module name. Against the source-tree baseline the `"module"` field alone differs (`sidecar_free_certificate_v1.44` → `sidecar_free_certificate`), the single content effect of dropping the version suffix; that difference is the domain-07 build's, recorded in its own `VERIFICATION.md` |
| size gate 757 / 758 | `python3 $M --report` | pinned env | `sig_bytes_757_fits: true`, `sig_bytes_758_fits: false`, `frame_bytes_at_757: 32767` | identical | reproduced | `(32,768 − 216) // 43 = 757`, remainder 1 |
| frame arithmetic, every measured row | `python3 $M --real-demo` | pinned env, all three libraries | `domains/07-compact-certificate-b0/results/real-demo.json`: 11,396 / 19,738 / 24,984 / 30,918 / 28,854 / 41,668 / 199,177 ×2 | identical — all eight frames reproduced to the byte | reproduced | the demo asserts `len(frame0) == 216 + 43·W` per row, so the arithmetic of `sizes.md` §2 is observed, not merely computed |
| `--real-demo` content | same | pinned env | `domains/07-compact-certificate-b0/results/real-demo.json` — `schemes`, `liboqs_version`, `liboqs_python_version`, `category5_fitting_verified`, `summary` | exit 0; **every top-level field identical**, including `category5_fitting_verified = [OV-V-pkc, OV-V-pkc‖SNOVA_29_6_5, SNOVA_29_6_5, SNOVA_60_10_4]` | reproduced | this is the row that establishes the whole measured table of `sizes.md` §2 and the accept/reject evidence of `profiles.md` §2.3 |
| `--real-demo` timing | same | pinned env | `13.667722704 s` | `57.1 s` | reproduced-with-difference | host load; the domain-07 build observed 19.8 s and 24.0 s for the same command on the same host. No output value depends on it |
| oversize rejection, exactly one scheme at the boundary | `python3 $M --real-demo` | pinned env | MAYO-5 and ML-DSA-87 rejected with `frame exceeds the 32768-byte portability bound`; Falcon-padded-512 accepted at category 1 | identical, for MAYO-5 (41,668), ML-DSA-87 (199,177, both libraries) and Falcon-padded-512 (28,854, `category 1: does NOT meet QPT-128`) | reproduced | the rejections are the evidence the budget excludes FIPS-standardized signatures; see `profiles.md` §2.3 |
| worked example, `W = 32` | the heredoc in `docs/03-construction/wire-format.md` §7 | pinned env (stdlib only) | `1592`; header, bitmap `000007ffffffffff`, seat-0 slot, and `[(0, 0, 0), (1, 1, 1), (2, 2, 2)]` as printed in §3 | identical, character for character | reproduced | the command needs no third-party package, so any reader can run it |
| worked example digests | same, extended in `worked_example.py` (scratch, not shipped) | pinned env | header SHA-256 `6fb2fed1…dbd9`, frame0 `f82f800d…0a4e`, frame1 `fd7c2a77…38c0` as printed in §3.4 | identical | reproduced | recorded so a reader can check their own encoder byte for byte |
| extraction positions | same | pinned env | 22 seats, positions `(0,0,0) (1,1,1) (2,2,2) …` | 22 seats, `[0 … 21]` | reproduced | the extraction is the framing the construction is named for |
| bitmap popcounts and intersection | same | pinned env | bitmap0 `000007ffffffffff` popcount 43; bitmap1 `fffff800003fffff` popcount 43; intersection 22 | identical | reproduced | 43 = `QUORUM`; 22 = `MIN_OVERLAP` |
| blame, in and out | same, calling `verify_blame_b0(f0, f1, reg, p, cfg, seat)` | pinned env | seat 0 blames, seat 30 does not | seat 0 **True**, seat 21 **True**; seats 22, 30, 42, 43, 63 **False** | reproduced | the seats that are in both quorums blame; the seats in exactly one do not. `seat` is **the last argument** — an earlier call in this build passed it first and got `False` for every seat, which is a caller error, not a defect |
| vote-message length | direct measurement of `vote_message_b0(cfg, d, m, 0)` | pinned env | `docs/03-construction/wire-format.md` §1 as first drafted said 199 bytes | **205 bytes** = 12 (`CQ44/B0/VOTE`) + 64 + 64 + 64 + 1 | **not-reproducible** | the first draft was wrong: the prefix is 12 bytes, not 6, and `12 + 64 + 64 + 64 + 1 = 205`. Corrected in `wire-format.md` §1 and stated in `parameters.md` §3 |
| B1 worked example | `b1_example.py` (scratch, not shipped) against the repository module | pinned env | `docs/03-construction/wire-format.md` §5 | frame **5,752** bytes = `5,712 + 40`; suite `44b1`; width `0080` (128); `payload_len` `0x15a8` (5,544); proof marker 40 bytes; `verify_b1` → `STRUCTURE_ONLY_NO_QUALIFIED_PROOF`, `auth False`; `extract_b1` → `ALGEBRAIC_CANDIDATES_ONLY`, 22 candidates | reproduced | confirms B1's structural path and its **non**-result: `authorization_verified` is `False` by construction |
| finding F6 (encode-side cap) — first-hand | `python3 -c` replay, and `domains/07-compact-certificate-b0/results/probe_a10_f6.py` | pinned env | dossier F6: encode does not enforce the 32,768-byte cap although the wire specification makes it normative | `encode_b0` at width 758 emits **32,810 bytes** with no error; `b0_fits(758) = False`; `b0_frame_bytes(758) = 32810`; `verify_b0` of that frame → `FrameError: frame exceeds the 32768-byte portability bound` | reproduced | reproduced **twice**: once through the archived probe and once by direct call in this build. Stated as a documented gap in `wire-format.md` §6.1 and `parameters.md` §7; the reference is not patched |
| finding A.10 (misnamed test mutations) | `python3 domains/07-compact-certificate-b0/results/probe_a10_f6.py` | pinned env | dossier A.10: two B0 tests mutate at CEQS29 body offsets while their names claim CQ44 header checks | probe output **byte-identical** to `domains/07-compact-certificate-b0/results/probe_a10_f6.txt`: misaligned message → `count must be 43`; aligned → `signature for seat 0 does not verify`; misaligned width → `payload_len does not match the trailing bytes`; aligned → `header width does not match the provider width` | reproduced | the named checks are never exercised by those two tests. Recorded in `wire-format.md` §6.2 |
| header offsets and `calcsize` | `struct.calcsize('>4sHH64s64s64sHHI')` | pinned env | 208, offsets 0/4/6/8/72/136/200/202/204 as tabulated in `wire-format.md` §1 | identical | reproduced | `STATEMENT_FORMAT` = 204 |
| public-key sizes, 64-seat registry | `python3 $M --real-demo`, then `64 × public_key_bytes` | pinned env | per-scheme `public_key_bytes` in `domains/07-compact-certificate-b0/results/real-demo.json` | identical per scheme; the 64-seat totals in `sizes.md` §6 are arithmetic on them | reproduced | the registry is **not** carried in any frame; `sizes.md` §6 labels the totals as arithmetic for exactly that reason |

---

## 2. What was not run, and why

| item | why not | what this package does instead |
|---|---|---|
| Independent B0 conformance check (900 vectors, 6,701/6,701 checks, 18 spec gaps) | the map assigns `b0_indep.py`, `gen_b0_vectors.py`, `check_vectors.py`, `b0_vectors.json`, `SPEC_GAPS.md` and `INDEPENDENT_RESULTS.md` to `domains/11-independent-audit-stack/independent-b0/`, and that domain owns and re-runs them | cites the result in `README.md` §6 and `sizes.md`; reads `SPEC_GAPS.md` for notes 15 and 16, which are the independent statement of the vote-message concatenation and of the encode-side cap |
| The production Mode B run (30,684-byte certificate) | **no archived result carries it.** Every JSON in `domains/08-hidden-signers/results/` is the *reduced* setting: `b = 12, τ = 20, w_g = 8, ρ = 1,024`, `proof_bytes: 47,524`, `frame_bytes: 49,108`, `fits_32768: false`. A search of that directory for `30684`, `30,684`, `29100`, `29,100` returns nothing | `sizes.md` §7 records the archived 49,108-byte reduced run as **measured elsewhere** and labels the 30,684-byte production figure **claimed in prose only**, not a measurement |
| SLH-DSA-SHAKE-256s and Falcon-padded-1024 widths | the recorded `--real-demo` never loads them (`real_demo()` loads `falcon_padded_512` and `ml_dsa_87` from pqcrypto, plus the enabled liboqs providers) although both `SIGNATURE_SIZE_TABLE` entries carry the source string *"measured liboqs 0.16.0"* | `sizes.md` §4 records the provenance gap per row and treats both as **quoted from a specification**, never as measured |
| The 21.49 KB single-witness ring-signature figure | third-party published measurement (Chiang et al., CCS'25, ePrint 2025/113, Table 2) | quoted as such in `sizes.md` §7 and `profiles.md` §3.4, where it is explicitly **a lower bound on the single-witness case**, not an estimate of any B1 certificate |
| The original source-tree `--real-demo` JSON, byte for byte | never archived as a file; it survives only as log text from the reading pass | the domain-07 build compared its own run against that text field by field; this package compares against the archived `domains/07-compact-certificate-b0/results/real-demo.json`, which is identical to it |
| Any formal proof tool | nothing in this package is stated as a machine-checked result | Theorems A, B and C are cited from `domains/06-qpt128-security-target/` and `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md` with their hypotheses stated, including that Theorem C is a **necessary condition for witness-committing families**, not a universal lower bound |

---

## 3. Numbers this package states that no one has measured

Stated here so that no reader mistakes them for measurements. They appear in the package only with
this label attached.

| Number | Where | Status |
|---|---|---|
| 30,684 B (Mode B production certificate) | `sizes.md` §7 | claimed in prose; not in any archived result |
| 29,792 B, 1,280 B, 292 B, 1,221 B (SLH-DSA-SHAKE-256s, Falcon-padded-1024, SQIsign-V, HAWK-1024 widths) | `sizes.md` §3 | quoted from specifications |
| 21.49 KB (one hidden signer, ring signature) | `sizes.md` §7, `profiles.md` §3.4 | quoted from a paper; a lower bound |
| 412,800 B, 109,856 B (Mode S linear and Binius64 floors) | `sizes.md` §8 | estimates from re-implemented estimators; the reference's own word for the "no known primitive fits" verdict is an assessment, not an impossibility proof |
| +23.0 bits (B0's D2 margin), 7.7 bits (Mode B's) | `README.md` §6, `profiles.md` §4, `sizes.md` §8 | ledger computations under stated assumptions, not measurements |
| `2^24` gates per Grover iteration | `sizes.md` §8, `parameters.md` §6 | an **assumption** in Theorem C |

---

## 4. Files written by this package

| file | sha256 |
|---|---|
| `docs/03-construction/README.md` | `77cb7c336ce57aff4a2d5cb627841c868b53b2c9fd87fd931284a6fe5a47c8ba` |
| `docs/03-construction/construction.md` | `3b1f21a2236daec7e72e9ea790386878197bcaec60bad6d8bcd9197cef8fbbc1` |
| `docs/03-construction/wire-format.md` | `10db90f7e30d04b7952ab732f53b20c627544ae434c6251f8ff5a7516e27f664` |
| `docs/03-construction/profiles.md` | `769641e5e676198f4ce00eadd79f5da557d23c6d98c3edaab24f74b3c95d83da` |
| `docs/03-construction/sizes.md` | `47478a0806f45e19e005f4eaf3ad6914c6f2752dfb820a6281c08c56908b88e8` |
| `docs/03-construction/parameters.md` | `71cb8325194d2de6fff6958f06fcc1907a5a1097eac89e0b2569d3dbcb35115d` |
| `docs/03-construction/VERIFICATION.md` | this file cannot carry its own hash; it is the seventh and last file of the package |

Nothing was created, modified or deleted anywhere under the read-only source tree (the research
tree this repository was assembled from, which is outside this repository). The two examples of
`wire-format.md` were generated by scratch
scripts outside this repository, which are not shipped; the heredoc in `wire-format.md` §7
regenerates the B0 example from the repository alone and is the one a reader should use.

---

## 5. Inconsistencies found, and where each is recorded

| # | Inconsistency | Recorded in |
|---|---|---|
| 1 | `SIGNATURE_SIZE_TABLE` labels SLH-DSA-SHAKE-256s and Falcon-padded-1024 *"measured liboqs 0.16.0"*, but the recorded `--real-demo` executes neither. Their widths are specification values with a measurement claim attached | `sizes.md` §4 |
| 2 | Domain 08's documented production certificate (30,684 B) has no archived result; every archived run is the reduced setting at 49,108 B, which does not fit | `sizes.md` §7 |
| 3 | The reference does not enforce the 32,768-byte cap on the encode side, although the wire specification makes that refusal normative | `wire-format.md` §6.1, `parameters.md` §7 (`sizes.md` §2 has the gate) |
| 4 | Two B0 tests mutate at CEQS29-era body offsets while their names claim CQ44 header checks, so the named checks are never exercised | `wire-format.md` §6.2 |
| 5 | The vote message uses plain concatenation while `cfg` uses the length-prefixed `H`; an implementer who assumes one rule for both produces frames that do not verify | `wire-format.md` §1, `parameters.md` §3; design note 15 of the independent implementation |

Items 1, 3 and 4 are recorded as **open**, not silently fixed: the reference must remain the
revision the measurements were taken on. Item 5 is a documentation hazard, not a defect — the
reference is unambiguous — and both this package and the independent implementation now state it
explicitly.
