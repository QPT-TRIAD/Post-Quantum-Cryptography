# Recorded runs

Every file here is the raw output of a command that this build re-ran, on 2026-09-13, against the
repository copies in `../src/` and `../history/`. None of them is a hand-written summary. Commands
were run from the directory holding the file they execute (so relative paths in the output resolve),
with stdout and stderr captured together. The command, expected result and verdict for each is in
`../VERIFICATION.md`.

**Environment.** Ubuntu 24.04.4, x86_64, kernel 7.0.0-31, 12 threads; CPython 3.12.3 from the pinned
verification environment (numpy 2.4.6 present, optional); gcc (Ubuntu 14.2.0-4ubuntu2~24.04.1)
14.2.0. Run times recorded below are host-load dependent; the recorded baselines in the source
documents were taken on a faster host and differ in the direction the notes give.

| File | Command | Result |
|---|---|---|
| `mode-a-self-test.txt` | `python3 src/hidden_signer_mode_a.py --self-test` | `Ran 8 tests … OK` |
| `mode-a-report.json` | `python3 src/hidden_signer_mode_a.py --report` | the §3 sizing table and the FAEST reproduction |
| `mode-b-v1.46-self-test.txt` | `python3 history/hidden-signer-mode-b-v1.46.py --self-test` | `Ran 12 tests … OK` |
| `mode-b-v1.46-demo-256.txt` | `python3 history/hidden-signer-mode-b-v1.46.py --demo-256` | 64-key registry, two 1,584-byte frames, all 1,849 candidate openings searched, the 22 common seats recovered |
| `mode-b-v1.50-self-test.txt` | `python3 history/hidden-signer-mode-b-v1.50.py --self-test` | `Ran 5 tests … OK` |
| `mode-b-v1.51-self-test.txt` | `python3 src/hidden_signer_mode_b.py --self-test` | `Ran 7 tests … OK` |
| `ledger-self-test.txt` | `python3 src/mode_b_rigorous_ledger.py --self-test` | `Ran 7 tests … OK` |
| `ledger-report.json` | `python3 src/mode_b_rigorous_ledger.py --report` | every ledger row, sweep and comparison |
| `toy-self-test.txt` | `python3 src/mode_b_voleith_toy.py --self-test` | `Ran 7 tests … OK` |
| `toy-run.json` | `python3 src/mode_b_voleith_toy.py --run` | measured proof 6,696 B vs formula 6,924 B; 22 seats |
| `prover-v1.49-build.txt`, `-v1.50-`, `-v1.51-` | `gcc -O3 -march=native -fopenmp -Wall -o <bin> <file>.c` | exit 0, no warnings; the compiler banner is in the v1.51 file |
| `prover-v1.49-vectors.json`, `-v1.50-`, `-v1.51-` | `<bin> --vectors` | identical on all three |
| `prover-v1.49-run.json`, `-v1.50-`, `-v1.51-` | `<bin> --run --b 12 --tau 20 --wg 8 --rho 1024` | proof 47,524 B, `verified: [true,true]`, tamper rejected, 22 seats |
| `prover-v1.51-production-run.json` | `./modeB_prover --run --b 20 --tau 11 --wg 16 --rho 4096` | proof **29,100 B**, frame **30,684 B**, `fits_32768: true`, `verified: [true,true]`, tamper rejected, 22 seats; 236.84 s wall. The source of the 30,684-byte frame figure |
| `prover-v1.51-asan-run.json` | reduced ASan+UBSan build, `detect_leaks=0`, same `--run` setting | the same JSON as the plain build |
| `prover-v1.51-asan-lsan-reduced.txt` | the same build with `detect_leaks=1` | `AddressSanitizer: 33,732,200 byte(s) leaked in 9 allocation(s)`; no `verify()` frame; no UBSan diagnostic |
| `property-layer-modeb.txt` | `python3 -m pytest -q test_props_modeB_fixed.py` (audit-stack module) | `16 passed in 268.22s` |
| `property-layer-hashsig.txt` | `python3 -m pytest -q test_props_hashsig_fixed.py` (audit-stack module) | collection error: `F3: LMS m and LM-OTS n must match` — 0 tests executed, as record A28 states |

**The two property-layer files are not files of this domain.** They are the programme's property
suites, which live in the verification environment's audit stack; they are re-run here because
`../docs/validation-status.md` reports their figures, and a reader should be able to see the output
those figures come from. Their counts must be read exactly as record A28 states them: Mode B **16
passed**, hash-signature **fails at collection by design of the F3 fix**, and the earlier "16/16"
reading is **withdrawn**.

## Normalisation applied to two files

`prover-v1.51-asan-lsan-reduced.txt` is the sanitizer report verbatim except for three substitutions:
the build directory in the frame paths became `<build-dir>`, the home-directory prefix became
`<home>`, and the binary build id became `<id>`. No frame, address, allocation size or count was
altered. Nothing else in `results/` is edited: there are no absolute paths, host names, addresses or
timings that depend on the source tree in any other file.

## Not recorded here, and why

- The **clang-built** sanitizer runs, and the recorded **production-parameter ASan+UBSan** run: not
  run here. clang's sanitizer runtime is not installed in this environment, so no clang sanitizer
  binary can be built; the recorded baselines exist in the verification environment's audit stack.
  Both appear as `not-run` rows in `../VERIFICATION.md` with those reasons. The one
  production-parameter run that *was* performed here is a plain build and is archived above.
