# VERIFICATION — D3, zk-carrier-experiments

What was checked when this domain was assembled, what was actually re-run, and what could not be
re-run at all. Every `not-run` item names the capability that is missing; every item that *was* run
carries the observed output, not a summary of it.

**Environment for every command below.** Ubuntu 24.04.4 LTS (x86_64, kernel 7.0.0-31), Python 3.12.3
in the pinned virtual environment, with `cryptography` 46.0.0 and `pqcrypto` 0.3.4 importable. No Rust
build was attempted; the host's `rustc` is 1.96.0, not the pinned 1.97.1, and the vendored backend tree
is not in this repository. Runs were made in a **copy** of the domain directory, so the retained files
shipped here were never written over by a test.

**The one rule that decides most of this file.** No native proof was generated, no adapter binary was
rebuilt, and no native proof was verified for this repository. Every frame size, every `native_verified`
flag and every negative-control count is a **record made by the experiment that produced it**, audited
here against that experiment's own files. Nothing in the table below is presented as a measurement
taken during assembly except where the row says `observed`.

## 1. Verification table

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| Evidence audit | `python3 src/audit_results.py` | pinned Python, domain copy | rewrites `results/evidence-audit.json`; re-derives the accounting over v1.25/v1.27/v1.27b and the field certificate | exit 0, 0.10 s; output **byte-identical** to the retained file | reproduced | re-checks `fixed + boundary + scalars = encoded_bytes` and `encoded_bytes + 5712 = frame_bytes` for all six records, the v1.27/v1.27b frame digests, `recovered_indices == range(22)`, and the absence of `PRIVATE_TRACE_WITNESS.bin` beside the fixtures |
| Carrier audit | `python3 src/audit_carriers.py` | pinned Python, domain copy | rewrites `results/carrier-audit.json`; re-reads the QVT2/QVT3 frames and the seed carriers | exit 0, 0.16 s; output **byte-identical** to the retained file | reproduced | re-checks both frame digests, both expanded-native-proof digests, the QVT2/QVT3 `same_native_proof: true` claim, 20 and 22 controls, and all five `.scd` carriers (588 B → 1,023 leaves) |
| Compression and span measurement | `python3 src/analyze_existing_carriers.py` | pinned Python, domain copy | rewrites `results/existing-carrier-results.json`; DEFLATE/bzip2/XZ larger than the raw frames | exit 0, 0.96 s; output **byte-identical** to the retained file | reproduced | 283,746 / 279,671 (deflate9), 285,250 / 281,232 (bzip2), 283,752 / 279,672 (xz) against 283,680 / 279,600 raw; field span 128 bits, hash span 256 |
| Reference suite | `CEQS_FIXTURES=<new dir> CEQS_RESULTS=<new dir> python3 src/make_fixture.py` | pinned Python, domain copy | 15 checks pass; `results/reference-checks.json` reproducible | exit 0, 0.10 s; **15/15**, `scope: REFERENCE_EQUATIONS_NOT_SECURITY_THEOREM`; output **byte-identical** to the retained file; fresh fixture files of the same size as the retained ones (config 17,929 B, provenance 1,237 B, statement 5,568 B/11,853 B, witness 4,472 B) | reproduced | without the environment overrides the script exits 1 with `RuntimeError: refusing to overwrite retained fixture` — that guard is the reason the retained fixture is intact |
| Authorization suite | `python3 src/test_authorization.py` | pinned Python + `pqcrypto` 0.3.4 | 51 checks pass; 86 approvals; 86 envelopes; intersection `0..21`; 5,712 / 27,056 / 11,020 B | exit 0, 4.0 s; **51/51**; every one of the 51 named checks `true`; all fields identical to `results/authorization-evidence.json` **except** two timings and the interpreter string | reproduced-with-difference | `measured_crypto_seconds` 1.4520808 (recorded) vs 3.4115175 (here); `measured_total_seconds` 1.6389486 vs 3.8167747; `runtime.python` "3.12.14" (recorded host) vs "3.12.3" (here). Wall-clock on a different host with freshly generated synthetic keys is not a reproducible quantity; no other field moved |
| Transparency audit | `python3 src/verify_audit.py` | pinned Python | 86 public approval checks; intersection `0..21`; `complete_QCs_verified: 0` | exit 0, 0.22 s; printed `"public_approval_checks": 86`, intersection 0–21, `"complete_QCs_verified": 0` | reproduced | pure public replay: public keys, bodies and signatures only; prints, writes nothing |
| One-command replay | `sh src/reproduce.sh` | pinned Python | installs/checks the dependency, runs the transparency audit and the 51 checks, writes `results/replay-evidence/` | exit 0, 6.62 s; `pqcrypto already importable …; nothing installed`; 86 checks; 51/51 | reproduced | the authorization record it writes carries the fresh timings noted above |
| Dependency check | `python3 src/install_dependency.py` | pinned Python + `pqcrypto` 0.3.4 | reports the pinned wheel and installs nothing when the package is already present | exit 0, 0.13 s; `pqcrypto already importable from …/site-packages/pqcrypto; nothing installed` | reproduced | the pinned name, sha256 `b2f9bad4…a6ebb` and size 27,036,304 B are the same constants as in `results/dependency-provenance.json`; with `--wheel` supplied it verifies the digest before installing |
| Seeded-data demonstration | `python3 src/seed_carrier_demo.py` | pinned Python, domain copy | five carriers, 588 B, 1,023 reconstructed leaves, 1,047,552 B of tapes, 3 controls each | exit 0, 0.48 s; same five quantities for hidden indices 0, 1, 17, 511, 1023; `.scd` files 588 B each | reproduced-with-difference | it **generates** its data from fresh `os.urandom` seeds and **overwrites** `fixtures/seed-demo/*.scd` and `results/seed-carrier-results.json`, so the carrier digests differ from the retained ones by construction. Run it on a copy if the retained digests matter; the retained digests are recorded in `results/carrier-audit.json` |
| Codec re-derivation | `python3 src/modify_codec.py --output <file>` | pinned Python | re-derives the QVT2 codec from the QVT1 codec | exit 0, 0.10 s; output **byte-identical** to `history/v1.28/adapter/src/codec.rs`, sha256 `82efda3fa777f733d929e0180dbef194b74ebe0daefce21a55ff52c11a431578` | reproduced | the only reproduction of a codec transformation available without a Rust toolchain |
| **12. Retained frame and native-proof bytes** | inline parse of all eight frames against `{pt27,pf27,pf28,pf2p}` header constants; `audit_results.py` and `audit_carriers.py` re-hash every file against its record | pinned Python, domain copy | frames of 287,648 / 281,232 / 283,680 / 279,600 / 282,016 / 277,968 / 273,952 / 270,304 B; native proofs 335,360 B; every recorded sha256 | every frame parses with magic/version/suite/count/width as recorded, `size == 5712 + proof_length`, 43 strictly sorted 64-byte links; every sha256 equals the recorded value; both native proofs 335,360 B with digests `de9d0365…b013` / `f5215457…8656` | reproduced | the digest comparisons are assertions inside the two audits (exit 0 above is the evidence); the framing/parse check is the inline command summarised in §2 |
| Accounting arithmetic | inline arithmetic check | pinned Python | 208 + 43·128 = 5,712; 5,712 + 27,056 = 32,768 | exact; QVT3 encoded 268,240 / 264,592 B → frames 273,952 / 270,304 B; over budget 241,184 / 237,536 B | reproduced | matches `results/encode-case*.json` (`fits_budget: false`) |
| Patch identity | `sha256sum src/prover_memory.patch` | any | sha256 `b9166068…4b563` | 24,941 B, sha256 `b916606810a4b8416baddadfac531302eec91935a73b1528a201a4a189a4b563` | reproduced | equals `patch_sha256` in `results/source-comparison.json` and the value in the domain brief |
| Modified-file table | cross-check of `results/source-comparison.json` against `docs/provenance.md` | any | six `crates/prover/src/...` files with their digests | all six paths and all six sha256 values appear in `docs/provenance.md` §2 | reproduced | `recompute.rs` is a new file, not a modification |
| Packaging scripts | `python3 src/{build_review_bundle,package_carriers,package_update}.py --help` | pinned Python | scripts state that the previous archive is required and is not retained | all three exit 0 and print their usage; `package_update.py --output X` fails with `the following arguments are required: --previous` | reproduced | the archives themselves are build products and are absent, so no package was rebuilt |
| Source tree read-only | `python3 tools/check_pqt_baseline.py` (work directory) | pinned Python | 1,157 baseline files, nothing changed | `present now: 1157`, `size changed: 0`, `mtime changed: 0`, `added: 0`, `removed: 0`, `RESULT: PASS -- source tree unmodified` | reproduced | the domain's rule was that the research tree is read-only; this is the evidence |
| Map fidelity | row-by-row sha256 comparison of every `copy` / `copy-history` row against the placed file | any | 177 files at the map's `new_path`, each with the map's sha256 | **177/177 present; 135 byte-identical; 42 deliberately rewritten** (see §3) | reproduced-with-difference | the 42 rewrites are the repository's required rewrites; the source-side check confirms all 177 map digests still match the source tree, so no source file changed under this build |
| Identifier scan | targeted scan of the domain for assistant-product and vendor names, absolute local paths, e-mail addresses and tracking parameters | any | none | none found: 0 local paths, 0 addresses, 0 tracking parameters. Only name-shaped matches are the upstream crate `sponge-cursor` in the four `Cargo.lock` files, two English words used in this domain's prose, and the `# This file is automatically @generated by Cargo.` line in those lockfiles | reproduced | documented false positives, not modifications; see §2 item 18 |
| Native public verification | `python3 src/verify_public.py --config fixtures/config.json --frame fixtures/case0/trace43_rate3.pf2p` | — | both frames `native_verified: true`, 22 indices recovered (`results/public-verification.json`) | exit 1 — `native carrier binary not present: …/src/bin/ceqs-polycarrier-v128` and the rebuild note | **not-run** | missing capability: the compiled adapter `ceqs-polycarrier-v128`, which needs the vendored backend at pinned commit `37e9cd64…` and Rust 1.97.1; neither is in this repository |
| 22 public negative controls | `python3 src/check_public_mutations.py` | — | 22 mutations rejected (`results/public-negative-checks.json`) | exit 1 — same missing binary | **not-run** | the same call: every mutation is tested by running the native verifier |
| Native driver | `python3 src/run_native.py <label> <mode> <case>` | — | proves `results/prove-case*.json`, checks `results/check-case*.json`, encodes `results/encode-case*.json` | exit 1 — same missing binary | **not-run** | the driver needs three positional arguments; the guard fires before any file is read |
| Fresh end-to-end regeneration | `python3 src/regenerate.py --output <new dir>` | — | a fresh v1.27b pair of frames 285,136 / 283,184 B, 18 controls rejected (`results/regeneration-validation.json`) | exit 1 — `native paired-trace binary not present: …/src/bin/ceqs-fixed-pair-v127b` and the rebuild instruction | **not-run** | missing capability: the v1.27b adapter build |
| Historical-generation verification | `PYTHONPATH=src python3 history/v1.27b/verify_public.py --config fixtures/config.json --frame fixtures/case0/trace43_rate3.pf27 --output OUT.json` | pinned Python | v1.27b frames verified (`history/v1.27b/public_verification.json`) | exit 1 — `FileNotFoundError: …/history/v1.27b/bin/ceqs-fixed-pair-v127b` | **not-run** | the `history/` scripts are byte-preserved and have no guard, so they fail at the subprocess call; they also need `src/` on `PYTHONPATH` for `paired_reference` |
| Older-generation frame parsing | `python3 src/verify_public.py --config fixtures/config.json --frame fixtures/case0/trace43_rate3.pf27` | pinned Python | n/a | exit 1 — `ValueError: wrong format or incomplete quorum`, raised **before** the binary guard | not-run (informational) | `src/verify_public.py` accepts only `PF2P`; older generations use their own `history/` script. This row exists so that a reader does not mistake the parse error for a missing-binary error |
| Adapter or backend rebuild | `cargo build --locked --release` | — | four adapter binaries of 5,531,152–5,721,256 B with the recorded digests | not attempted | **not-run** | out of scope by instruction; the vendored tree is not in this repository and the pinned Rust 1.97.1 is not installed (host has 1.96.0) |
| Recorded runtimes (`1.4520808 s`, `1.6389486 s`) | — | — | the v1.29 recording host | this host produced 3.4115175 s / 3.8167747 s for the same suite | reproduced-with-difference | the recorded figures are host-specific and are **not** reproduced here; the record keeps them and this file states the difference |
| Recorded proof sizes and `native_verified` flags | — | — | see the per-version table in the README | audited against the retained bytes and records; never measured here | not-run (as a measurement) | deliberately not claimed as a re-measurement; the byte-level audit is the strongest check available |

## 2. What actually runs here, with observed output

Runs are listed in the order a reader would perform them. All were executed in a copy of the domain
directory in the pinned environment.

1. **Environment.** `python3 -V` gives `Python 3.12.3`; `cryptography` 46.0.0 and `pqcrypto` 0.3.4 are
   importable. See §2 item 18 for the identifier scan.
2. **Evidence audit.** `python3 src/audit_results.py` → exit 0, 0.10 s. Prints the audit JSON and
   writes `results/evidence-audit.json`; the file is byte-identical to the retained one. This is the
   check that the retained accounting is internally consistent and that the field
   `x^512 + x^8 + x^5 + x^2 + 1` carries a Rabin certificate (`frobenius_512_equals_x: true`,
   `gcd_x_2pow256_minus_x: 1`, `degree_prime_divisors: [2]`, `irreducible: true`).
3. **Carrier audit.** `python3 src/audit_carriers.py` → exit 0, 0.16 s, byte-identical output. This is
   the check that the four current-generation frames on disk are the frames the records describe
   (frame digest, expanded-native digest, control counts, `.scd` carriers).
4. **Compression and span.** `python3 src/analyze_existing_carriers.py` → exit 0, 0.96 s,
   byte-identical output. Confirms the recorded claim that generic lossless compression does not help
   on these frames and that the queried-field sections have full binary span.
5. **Reference suite.** `CEQS_FIXTURES=<new dir> CEQS_RESULTS=<new dir> python3 src/make_fixture.py` →
   exit 0, 0.10 s, `checks_passed: 15`, and `results/reference-checks.json` byte-identical to the
   retained file. Covered: both honest 43-seat relations, other-seat role substitution in both roles,
   mixed link/mask rejection, the 22 expected conflict identities, changed domain/message/configuration
   rejection, 64 rotating quorums at an all-one message, 384 field vectors, and the zero-message
   observation (22 recovered mask outputs). Run without the overrides it refuses to overwrite the
   retained fixture.
6. **Authorization suite.** `python3 src/test_authorization.py` → exit 0, 4.0 s (recorded 1.45 s of
   cryptographic work on the recording host; the same suite costs 3.41 s here). 51/51 named checks
   `true`. The archived `results/authorization-evidence.json` and the re-run agree in every field
   except the two timings and the interpreter version string — see the table above.
7. **Transparency audit.** `python3 src/verify_audit.py` → exit 0, 0.22 s, prints
   `"public_approval_checks": 86`, `"algebraic_intersection": [0 … 21]`, `"complete_QCs_verified": 0`.
8. **One command.** `sh src/reproduce.sh` → exit 0, 6.62 s. It runs steps 9, 7 and 6 in that order and
   writes `results/replay-evidence/{results.json,public_approval_audit.json}` — a **new** directory, so
   the retained records are not overwritten.
9. **Dependency.** `python3 src/install_dependency.py` → exit 0, 0.13 s,
   `pqcrypto already importable from …; nothing installed`.
10. **Seeded-data demonstration.** `python3 src/seed_carrier_demo.py` → exit 0, 0.48 s, five carriers
    of 588 B, `reconstructed_leaf_seeds: 1023`, `equivalent_leaf_seed_bytes: 49104`,
    `expanded_tape_bytes: 1047552`, `exact_reconstruction: true`, `negative_controls: 3` per carrier.
    It writes `fixtures/seed-demo/*.scd` and `results/seed-carrier-results.json` and therefore replaces
    those files with freshly seeded ones of the same shape.
11. **Codec re-derivation.** `python3 src/modify_codec.py --output <file>` → exit 0, 0.10 s; the output
    hashes to `82efda3fa777f733d929e0180dbef194b74ebe0daefce21a55ff52c11a431578`, identical to
    `history/v1.28/adapter/src/codec.rs`.
12. **Fixture bytes.** The eight retained frames were parsed with their generations' header constants
    (`>4sHH64s64s64sHHI`, 208 bytes) and checked for canonical size, handle count, link ordering and
    agreement between the file size and the recorded proof length. All eight pass:
    `pt27` 287,648 = 5,712 + 281,936 and 281,232 = 5,712 + 275,520; `pf27` 283,680 = 5,712 + 277,968
    and 279,600 = 5,712 + 273,888; `pf28` 282,016 = 5,712 + 276,304 and 277,968 = 5,712 + 272,256;
    `pf2p` 273,952 = 5,712 + 268,240 and 270,304 = 5,712 + 264,592. The two native proofs are 335,360 B
    each. Digest equality against the records is asserted inside items 2 and 3 above.
13. **Patch and modified-file record.** `src/prover_memory.patch` is 24,941 B with sha256
    `b916606810a4b8416baddadfac531302eec91935a73b1528a201a4a189a4b563`, equal to the `patch_sha256`
    in `results/source-comparison.json`; the six modified upstream files and digests in that record
    appear exactly as listed in `docs/provenance.md` §2.
14. **Dependency pins.** `results/dependency-provenance.json` records the wheel name, the PyPI
    digests, `hash_matches_pypi: true`, and the local digest `b2f9bad4…a6ebb` at 27,036,304 B; the two
    constants in `src/install_dependency.py` are the same values.
15. **Packaging scripts.** All three print usage and require `--previous`; no package was rebuilt
    because the prior archives are not retained.
16. **Read-only source tree.** `python3 tools/check_pqt_baseline.py` → `RESULT: PASS -- source tree
    unmodified` (1,157 files, 0 size changes, 0 mtime changes, 0 added, 0 removed).
17. **Map fidelity.** 177 rows with `action` in `{copy, copy-history}`: 177 present, 135 byte-identical
    to the map's sha256, 42 rewritten (§3). The 177 map digests were also re-checked against the source
    tree the map was taken from: all 177 still match, so nothing in the source material moved under
    this build.
18. **Identifier scan.** A targeted scan over the whole domain — for assistant-product and vendor names,
    absolute local paths in both POSIX and Windows form, e-mail addresses, and campaign-tracking query
    parameters — finds no local path, no address and no tracking parameter. The only name-shaped
    matches are `sponge-cursor`, an upstream Rust crate in the four byte-identical `Cargo.lock` files
    and not a product, two ordinary English words this domain uses in prose (one in a sentence about
    enrollment, one in the phrase "size ledger"), and the `# This file is automatically @generated by
    Cargo.` line those lockfiles carry. None of them is a reference to a tool.

## 3. Deliberate deviations from byte-identity

Rule: files are copied at the map's path. Two rules force exceptions — no absolute local paths (#4),
and no dangling references to files that are not in the repository (#1). **42 of the 177 placed files
are therefore not byte-identical to their source.** They were identified by comparing every placed
file's sha256 against the map's; the complete 772-line diff was reviewed line by line. The changes fall
into seven categories and nothing else:

| Category | Files | What changed |
|---|---|---|
| Adapter manifest header | 4 × `*/adapter/Cargo.toml` (8 lines each) | a comment stating that the relative `binius-*` path dependencies point into the excluded vendored tree, with the upstream URL, pinned commit, patch path and digest, and the rebuild command. **The dependencies themselves were kept** |
| Build-path removal | 3 × `build.stderr.log`, 1 × `regeneration-check.stdout.log`, 14 × `*_execution.json` | the recorded build/work prefix (an absolute scratch path in the source records) replaced by the corresponding relative path. `"binary": "<prefix>/continuation_v1.27b/bin/…"` → `"continuation_v1.27b/bin/…"`; every other field, size and digest untouched |
| Path relocation | `audit_results.py`, `audit_carriers.py`, `analyze_existing_carriers.py`, `make_fixture.py`, `verify_public.py`, `check_public_mutations.py`, `run_native.py`, `seed_carrier_demo.py`, `regenerate.py`, `modify_codec.py` | the source's `continuation_vX`-relative paths and underscore filenames replaced by this repository's paths, with environment overrides (`CEQS_FIXTURES`, `CEQS_RESULTS`, `CEQS_BINARY`) where the script has inputs. Output names follow the map's hyphen convention |
| Missing-input guards | `verify_public.py`, `run_native.py`, `regenerate.py` | an explicit check that names the absent binary, says why, and points at `docs/provenance.md`; the recorded results were produced before this addition |
| Package scripts | `build_review_bundle.py`, `package_carriers.py`, `package_update.py` | rewritten to take `--previous` and `--output`, to read members from their retained locations, and to say in the manifest and docstring that the vendored tree and compiled binaries of the recorded packages are excluded here |
| Dependency script | `install_dependency.py` | changed from "install the bundled wheel" to "check, or install from a wheel the caller supplies (`--wheel`), verifying the pinned digest first". Recorded because it changes behaviour, not only paths: the recorded package installed from its own bundled wheel |
| Entry-point defaults | `test_authorization.py` (`--out` default → `results/replay-evidence`), `verify_audit.py` (default path → `results/public-approval-audit.json`), `reproduce.sh` (three command lines), `docs/method.md`-adjacent edits | defaults now name retained files |

Two further behaviour changes, both deliberate and both about *this* repository's copy rather than
about any recorded result:

- `tempfile.TemporaryDirectory(dir=RUN)` became `tempfile.TemporaryDirectory()` in
  `src/verify_public.py` and `src/check_public_mutations.py`. The recorded version wrote temporary
  directories next to the run directory, which is where the three excluded `tmp*/config.json` files
  came from; they are no longer created. See §4.
- `src/make_fixture.py` refuses to overwrite an existing `fixtures/config.json`, so the retained
  fixture cannot be clobbered by a re-run. The recorded version wrote into its own run directory.

No asserted fact, byte size, gate count, digest, control count or comparison was changed by any of
these edits. The diff contains no numeric edit: the only numbers touched are inside path strings and
inside the two new guards' text.

## 4. Discrepancies, defects and things the sources get wrong

1. **Recorded runtimes are not reproduced.** The v1.29 component record carries
   `measured_crypto_seconds: 1.452080812996428` and `measured_total_seconds: 1.638948622996395` from
   its recording host (Python 3.12.14). The same suite here costs 3.4115175 s and 3.8167747 s. Both
   numbers are kept; the retained record is unchanged, and the README does not present the recorded
   runtimes as if they had been re-measured. Nothing else in that record differed.
2. **The `pqcrypto` install path differs.** The recorded package installed the pinned wheel into its
   own `vendor/` directory; here the pinned version is already importable in the environment, so
   `install_dependency.py` reports and installs nothing. Both outcomes are "the pinned 0.3.4 package is
   present"; the mechanism differs and is recorded rather than smoothed over.
3. **Temporary directories (source-level defect, fixed in this copy).** The recorded
   `verify_public.py` and `check_public_mutations.py` passed `dir=RUN` to
   `tempfile.TemporaryDirectory`, which created `tmp*/config.json` directories (17,384 B each) beside
   the run. Three such files are excluded from this repository as non-evidence, and the current scripts
   no longer create them. This changes no recorded number.
4. **A record referenced by a retained document is not retained.** `docs/method.md` refers to
   `runner_correction.json` for the list of v1.17 runner labels affected by the original-executable
   mistake. That record is not present in the source tree and is not in this repository;
   `docs/experiment-01-prover-memory-v1.17.md` says so where it cites it. Likewise the v1.25 relation
   references a v1.24 `contents_contract.py` that is not in this repository.
5. **Candidate A has no retained negative-control record and no report.** `history/v1.27/` holds
   adapter sources, records and logs, but no `assessment.md` and no mutation record. The 18-control
   record under `history/v1.27b/` belongs to candidate B and is not extended to candidate A here —
   stated in `docs/experiment-03-paired-trace-v1.27.md`.
6. **The v1.25 adapter and binary are absent from the source tree altogether**, not merely excluded
   from this repository: `history/v1.25/` holds only `assessment.md` and three result records, and no
   file-map row mentions `continuation_v1.25/bin/`. A v1.25 proof cannot be rebuilt from anything that
   survives. `docs/provenance.md` §4 records the digest the report quotes, and no frame bytes for that
   generation are retained anywhere, so only its accounting could be audited — which item 2 of §2 does.
7. **Unexplained reappearance of private files in the regeneration run.** Recorded by the experiment
   itself: the regeneration run's in-process deletion record says the private files were removed, yet a
   post-process audit found them present; a separate cleanup removed them and their reappearance is
   unexplained. This is kept in `docs/experiment-04-fixed-context-v1.27b.md` and in the README's list of
   what the domain does not establish. It concerns that extra test only, not the four retained proofs,
   whose private-file absence is asserted by the audits in §2 items 2 and 3.
8. **The v1.25 negative-control count (14) and its 13,072-byte deletion figure are report records
   only**, with no surviving record files; they are labelled as such in the v1.25 document.
9. **No upstream `cargo test` pass is claimed anywhere in this domain.** The v1.17 differential tests
   (4 layer shapes, 6 transcript shapes) are recorded, and `results/recompute-final-checks.json` is the
   retained record of them; the ordinary upstream test suite is not part of the record.
10. **All negative-control counts are finite.** 18 (v1.27b), 20 (QVT2), 22 (QVT3) are controls on
    those mutations, and each record carries its own `scope` field saying so.
