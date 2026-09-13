# Inputs and provenance

The audit stack consumes code and documents it did not write. This file says where those inputs
come from, which copy of each is authoritative, what the repository ships and what it does not, and
which placeholder stands for which machine-specific string in the recorded text.

## 1. The read-only research tree (`PQT_SRC`)

Every layer that loads an audited input names the tree through one environment variable:

```python
PQT = os.environ.get('PQT_SRC')
if not PQT or not os.path.isdir(PQT):
    raise SystemExit('PQT_SRC is not set: source the environment activation script '
                     '(tooling/), or point PQT_SRC at a local copy of the research tree')
```

The verification environment exports `PQT_SRC` (see `tooling/`); there is no default path and no
fallback, so an unset variable stops the layer with that message rather than silently auditing
something else. Nothing in this domain writes into the tree: the harnesses set
`sys.dont_write_bytecode = True` (and the environment exports `PYTHONDONTWRITEBYTECODE=1`), so not
even a `__pycache__` directory is created there.

**One deliberate exception.** `fixes/make_fixes.py` *adds* the F1–F5 fixed files to the tree — that
is how they were produced in the programme. It is therefore **not run** when assembling or
verifying this repository, and the fixed files it would write (`modeB_prover_v1.51.c`,
`pq_infra_s1s2_hashsig_dnssec_v2.2.py`, `pq_audit_s1_lms_v2.2.py`, `hidden_signer_modeB_v1.51.py`)
are already in the tree, where the fixed-file regression tests load them from. The script keeps a
`SystemExit` guard of the same form as above and aborts unless every replacement pattern matches
exactly once.

## 2. Which copy of each input is authoritative

The repository carries each audited file once, at the `new_path` the file map gives it
(`records/file-map.tsv`, one row per source file with its digest and size). The two C targets are
the exception: the map records them as `exclude-duplicate`, because the hidden-signers domain
already carries them byte-identically.

| audited input (in `PQT_SRC`) | published copy in this repository | loaded or read by |
|---|---|---|
| `sidecar_free_certificate_v1.44.py` | `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` | `property/test_props_b0.py`, `property/differential_b0.py`, `fault/fault_injection.py`, `math/math_layer.py`, `independent-b0/gen_b0_vectors.py` |
| `B0_wire_spec_v1.44.md` | `domains/07-compact-certificate-b0/docs/b0-wire-spec.md` | read (not imported) by `independent-b0/b0_indep.py`; `SPEC_GAPS.md` cites its §1–§11 |
| `hidden_signer_modeB_v1.46.py` | `domains/08-hidden-signers/history/hidden-signer-mode-b-v1.46.py` | `math/math_layer.py` (comparison rows) |
| `hidden_signer_modeB_v1.50.py` | `domains/08-hidden-signers/history/hidden-signer-mode-b-v1.50.py` | `property/test_props_modeB.py`, `math/math_layer.py` |
| `hidden_signer_modeB_v1.51.py` | `domains/08-hidden-signers/src/hidden_signer_mode_b.py` | `fixes/property_fixed/test_props_modeB_fixed.py`; its own `--self-test` |
| `modeB_prover_v1.50.c` | `domains/08-hidden-signers/history/mode-b-prover-v1.50.c` | `implementation/build.sh` (and the sanitizer/fuzz scripts it builds for) |
| `modeB_prover_v1.51.c` | `domains/08-hidden-signers/src/mode_b_prover.c` | the F1 regression run `implementation/production/v151_lsan_reduced.txt` |
| `pq_infra_s1s2_hashsig_dnssec_v2.0.py` | `domains/10-digital-infrastructure/src/s1s2_hashsig_dnssec-v2.0.py` | `property/test_props_hashsig.py` (T3) |
| `pq_infra_s1s2_hashsig_dnssec_v2.2.py` | `domains/10-digital-infrastructure/src/s1s2_hashsig_dnssec.py` | `fixes/property_fixed/test_props_hashsig_fixed.py` (T3) |
| `pq_audit_s1_lms_v2.1.py` | `domains/10-digital-infrastructure/history/s1_lms-v2.1.py` | `property/test_props_hashsig.py` (T4) |
| `pq_audit_s1_lms_v2.2.py` | `domains/10-digital-infrastructure/src/s1_lms.py` | `fixes/property_fixed/test_props_hashsig_fixed.py` (T4) |
| `pq_infra_s4_embedded_broadcast_v2.0.py` | `domains/10-digital-infrastructure/src/s4_embedded_broadcast.py` | `property/test_props_tesla.py` (T5) |
| `qpt128_finalization_v1.43.py` | `domains/06-qpt128-security-target/src/qpt128_finalization.py` | `math/math_layer.py` (comparison rows, read-only) |
| `hsslms` 0.1.3 | third-party package, not part of the tree | `property/test_props_hashsig.py` (differential LMS) |
| NIST ACVP `internalProjection.json` files | **not shipped** — see `primitives/vectors/SOURCE.txt` | `primitives/cross_validate.py` |

Two consequences of the `exclude-duplicate` rows, both handled in place:

- `implementation/build.sh` falls back to `domains/08-hidden-signers/history/mode-b-prover-v1.50.c`
  when `implementation/src/modeB_prover_v1.50.c` is absent, and exits 2 with that instruction if
  neither is found. The two files are byte-identical (`sha256 ff8e5cd9…6adb92`, the digest
  `IMPLEMENTATION_RESULTS.md` quotes for the pristine copy).
- `implementation/src/` does ship two files of its own: `modeB_prover_v1.50_nomain.c` (the preprocessed
  translation unit the fuzzer builds) and `nomain.diff`, the diff that produced it.

`property/test_props_b0.py` and `property/differential_b0.py` write their logs and re-generated
vectors *beside themselves*, never into the tree. `property/run_all.sh` and the stack's `run_all.sh`
write `run_all.log` next to themselves; the recorded run of the assembled stack is kept separately
in `results/` (see §4).

## 3. What the repository does not ship

- **The NIST ACVP vector files.** `primitives/vectors/SOURCE.txt` records the source URL, the
  download date, the upstream commit `975de31eb83d87039ec88934fdc47d8c312b892d` and the sha256 of
  each of the five files. They are large upstream artifacts and are not redistributed here. A
  re-run without them stops with `KeyError: 'ML-DSA-87'`: the layer reads the files, it does not
  synthesise them. Downloading the five files from that commit and checking the five digests is
  what the verification run for this repository did before the primitives layer would execute (all
  five matched).
- **Toolchains and binaries.** No compiled binary, container image or tool tarball is shipped:
  Tamarin 1.12.0 and Maude 3.5.1, liboqs 0.16.0, the clang-18 sanitizer runtimes and libFuzzer, the
  private compiler-rt (`rt/18`), ProVerif, EasyCrypt and SageMath are all described in the recorded
  logs and in the stack's own `Dockerfile` (carried as recorded), but nothing is bundled. A layer
  whose tool is missing reports `NOT RUN`; it never reports a pass.
- **The demos' build products and corpora.** The fuzzer corpus is regenerated by
  `implementation/gen_corpus.py`; only `corpus_genuine.bin` and `implementation/logs/ref_calib.json`
  travel with the stack.

## 4. Placeholders in recorded text

Recorded logs, JSON and tracebacks name machine-specific strings as placeholders. Only recorded
text uses them — never code.

| placeholder | stands for |
|---|---|
| `<workdir>/` | the working directory the recorded run used (a scratch tree outside the source tree) |
| `<source-tree>/` | the read-only research tree; two traceback logs use it, with frame numbers, file names and error text kept exactly as recorded |
| `<stack root>/../tools/` | the layout the stack's own scripts expect for tools that used to sit beside it (Tamarin, Maude, liboqs); the pinned environment now puts the tools on `PATH` instead |

`results/run_all.log` and `results/run_all.console.txt` are the recorded full-stack runs; `run_all.sh`
writes a fresh `run_all.log` in the stack root when re-run, so a re-run does not overwrite the
recorded evidence. `math/math_run.log` (identical in the v0.1 and v0.2 trees, ending in the
`"seconds": 217.2` run of 2026-09-11) and `math/math_results.json` (the v0.2 run, `_meta.seconds`
82.6) are two different recorded runs of the same layer, and every measured value in the two results
files is identical — only `_meta.seconds` differs, 217.2 in `history/math-results-v0.1.json` against
82.6 here. Both are kept, and the layer table in `README.md` gives both figures.

The shipped copy of `math/math_results.json` is byte-identical to its file-map source
(`audit_stack_v0.2/qpt_audit_stack/math/math_results.json`, sha256
`7536bdaa4b85df189f0ad914fa94d904bdd41d20b2fb4593f0fd1c0b26cfc2a3`, 7,779 B). `VERIFICATION.md`
records that a re-run of the math layer, whose output is written to the working directory, had
overwritten it with a fresh run (`_meta.seconds` 211.4) during assembly; the recorded file was
restored from the source and the digest re-checked.

## 5. Environment variables

| variable | status | meaning |
|---|---|---|
| `PQT_SRC` | required by every layer that loads an audited input | the read-only research tree; unset or non-directory raises `SystemExit` |
| `AUDIT_PYLIB` | optional, set by nothing | an extra site-packages directory, for a reader who installed the pinned packages somewhere else. The pinned verification environment already provides Hypothesis, hsslms, SymPy and galois, so the suites do not need it |

Nothing else in the stack reads the environment. The two constants replace what were, in the source
tree, a machine-specific absolute path to the research tree and a scratch `pylib` directory (a
temporary copy of `hsslms` made before it was installed) — both are gone, not merely defaulted.
