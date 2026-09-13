# Verification — domain 07 (compact certificate, profile B0)

Every command below was re-run in the pinned environment on 2026-09-13 against the **repository
copy** of the reference module (`src/sidecar_free_certificate.py`), and compared with the run
recorded during the reading pass from the source-tree revision (that record is part of the
programme's build logs and is not shipped with this repository). Where a recorded value does not
recur, both values are kept below and the reason is given.

**Environment.** The programme's pinned verification environment: an activation script for a shell
that puts CPython 3.12.3, liboqs 0.16.0 (locally built shared library, exported through
`OQS_INSTALL_PATH`; commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`,
`-DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON -DOQS_DIST_BUILD=ON`), liboqs-python 0.16.0 and
pqcrypto 0.3.4 on the path, together with pinned builds of `tamarin-prover` 1.12.0, `maude` 3.5.1
and `proverif` 2.05. Source that activation script and the commands below are exact. Host: Ubuntu
24.04.4, x86_64, kernel 7.0.0-31. Rows marked *without the environment* use the system interpreter
with `OQS_INSTALL_PATH` and `PYTHONPATH` unset.

`$M` abbreviates `src/sidecar_free_certificate.py` below.

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| self-test result | `python3 $M --self-test` | pinned env | `Ran 39 tests`, `OK`, exit 0 | `Ran 39 tests`, `OK`, exit 0; all 39 test names identical to the recorded list | reproduced | raw output `results/self-test.txt` |
| self-test timing | same | pinned env | `Ran 39 tests in 0.094s` | `0.093s`, `0.158s`, `0.180s`, `0.190s` on four runs (wall 0.28–0.31 s) | reproduced-with-difference | host load only; the recorded figure recurs (0.093 s) and no test changed |
| `--report` | `python3 $M --report` | pinned env | exit 0, 0.103985984 s, full size tables, gate and Theorem C budgets | exit 0, 0.10–0.13 s, identical in every field **except** `"module"` | reproduced-with-difference | the one difference is the file-rename rewrite: `"sidecar_free_certificate_v1.44"` → `"sidecar_free_certificate"`. Raw output `results/report.json` |
| size gate (757/758) | `python3 $M --report` and `test_size_gate` inside `--self-test` | pinned env | `sig_bytes_757_fits: true`, `sig_bytes_758_fits: false`, `frame_bytes_at_757: 32767`; `b0_fits(757) is True`, `b0_fits(758) is False` | identical | reproduced | gate arithmetic `(32768−216)//43 = 757` |
| frame arithmetic 11,396 / 30,918 | `test_size_gate` inside `--self-test` | pinned env | `216 + 43·260 = 11,396`; `216 + 43·714 = 30,918` | identical | reproduced | also measured in `--real-demo` below |
| `--real-demo` (measured table) | `python3 $M --real-demo` | pinned env, liboqs 0.16.0 + liboqs-python 0.16.0 + pqcrypto 0.3.4 | exit 0, 8 runs / 7 schemes, 13.667722704 s; frames 11,396 / 19,738 / 24,984 / 30,918 / 28,854 / 41,668 / 199,177 ×2; `category5_fitting_verified = [OV-V-pkc, OV-V-pkc‖SNOVA_29_6_5, SNOVA_29_6_5, SNOVA_60_10_4]` | exit 0, 19.8 s and 24.0 s on two runs; **every field identical** to the recorded run (`real_demo`, `schemes`, versions, `category5_fitting_verified`, `summary`) | reproduced | raw output `results/real-demo.json`; the timing spread is host load, the numbers are not |
| `--real-demo` without the environment | `python3 $M --real-demo` | system interpreter, `OQS_INSTALL_PATH`/`PYTHONPATH` unset | exit 1, `{"real_demo": "unavailable", "reason": "neither pqcrypto nor an installed liboqs-python imports"}` | identical, exit 1, 0.10 s | reproduced | documented behaviour of the demo, not a defect; raw output `results/real-demo-unavailable.json` |
| bare invocation | `python3 $M` | pinned env | exit 2, argparse usage error naming the four modes | exit 2, same usage error | reproduced | recorded wall 0.159722126 s; observed 0.10 s |
| `--explain` | `python3 $M --explain` | pinned env | no recorded baseline (the mode was not exercised in the reading pass) | exit 0, 8,517 B of plain text, no absolute paths | reproduced | run for completeness; raw output `results/explain.txt` |
| finding A.10 — misaligned test mutations | `python3 results/probe_a10_f6.py` | pinned env | dossier A.10: two B0 tests mutate at CEQS29 body offsets while their names claim CQ44 header checks | misaligned message mutation → `count must be 43`; aligned → `signature for seat 0 does not verify`; misaligned width mutation → `payload_len does not match the trailing bytes`; aligned → `header width does not match the provider width` | reproduced | the named checks (`wrong message`, `width mismatch`) are never exercised by those two tests. Raw output `results/probe_a10_f6.txt` |
| finding F6 — encode-side size cap | `python3 results/probe_a10_f6.py` | pinned env | dossier F6: the encode side does not enforce the 32,768-byte cap although the wire specification makes it normative | `encode_b0` at width 758 emits **32,810 bytes** with no error; `verify_b0` rejects that frame: `frame exceeds the 32768-byte portability bound`; `b0_fits(758) = False` | reproduced | stated as an open item; the reference is not patched. See `docs/construction.md` §9, `docs/b0-wire-spec.md` §11 |
| independent B0 check (900 vectors, 6,701/6,701) | — | — | 6,701 of 6,701 checks agree, 18 specification gaps | not run here | not-run | the map places `b0_indep.py`, `b0_vectors.json`, `check_vectors.py`, `SPEC_GAPS.md` and `INDEPENDENT_RESULTS.md` in `domains/11-independent-audit-stack/independent-b0/`; that domain owns and re-runs them. Re-running here would duplicate another builder's artifact and its 5.2 MB vector file. This domain links to the result and records the gaps it found (encode-side cap; header-offset and width-field vectors) |
| original `--real-demo` raw JSON | — | — | the reading pass recorded the output inside the log, not as a JSON file | not available | not-run | the raw JSON of the original run was never archived; the log text is complete and was compared field by field against `results/real-demo.json`. The Falcon-padded-1024 liboqs probe and the pqcrypto version of the original run were likewise not archived |
| rewritten copies behave as the source | `python3 $M --self-test` on the rewritten copies; `diff` against the source revisions | pinned env | the copies must differ only in paths and naming | 39/39 tests pass on the repository copy; the report differs from the recorded report in the `module` field only; the `--real-demo` JSON is identical | reproduced | digests below. 20 rewrite points were applied under an exactly-once assertion, so a silent miss would have failed the build |

## Digests

The three copied files carry relative paths in place of source-tree references, so their digests
differ from the source-tree digests by design. The pairs below are what this domain contributes to
the build's rewrite record; the rewritten copies are the ones in this directory. A repository-wide
hash check will therefore report these three rows as differences until that record lists them,
which is the intended mechanism, not a defect.

| repository file | repository sha256 | source-tree file | source sha256 |
|---|---|---|---|
| `src/sidecar_free_certificate.py` | `3afdc786c33c7207bc6c2723e9e4208379c3cdf6cd1d23f462c58e033e279489` | `sidecar_free_certificate_v1.44.py` | `a30f1078ffee7f395bbd82a1b7b9a37f9c5518a71e63a4d5a85b0446146e68a8` |
| `docs/b0-wire-spec.md` | `5d8e60a1089a8b15b1b4f7df33f375c112ccf72841d182a183a7b17baa19cb32` | `B0_wire_spec_v1.44.md` | `5c639a06a6511cfcaf75209e04daef3d04c0763eafd1a6d8cea35713dab6b311` |
| `docs/sidecar-free-finalization.md` | `c2e119a2ad5f20e3d363a38b7fdc465027da03b60e3fdcb5ce05b5bf353b785f` | `sidecar_free_finalization_v1.44.md` | `65ec0c74c9bcd6c849e7c023d1c96b9ef8fd8dad5bfc46a9ff7b85328719b295` |

Files written by this build, for the record:

| file | sha256 |
|---|---|
| `README.md` | `87b27a05a44074c39b473fd5e3004d3d882707a4580861330f8c87b048f697d1` |
| `VERIFICATION.md` | see the repository's own digest record; this file cannot carry its own hash |
| `docs/construction.md` | `d7e12068cd077ae063c96417388e12bee998a3bbb52408090618610ea333e938` |
| `results/self-test.txt` | `8cbbd15b50b9d899ef2176e0e687f16b4e41e8df94c0c1d07ccadf9b6a80fbc3` |
| `results/report.json` | `831640177e0c317bf898ded0d4e5d3ab6a7fe4dd9d25c46b83ac43c98e9b9bf9` |
| `results/real-demo.json` | `e7f866bc7c7767d276f496d6916e97444a5a9fd7e512d59aea772f76146b9f6f` |
| `results/real-demo-unavailable.json` | `4b8f4211aa16333af2a0ddbc199221ba46d7153e6ab8d2e22a70af031867585a` |
| `results/explain.txt` | `54e3e0c88aec7797ecdc57b7faef78498951182b790ce756c21cb8c3f3ff49e7` |
| `results/probe_a10_f6.py` | `7bdee6ab5dcb3a23cde8eb73d5af161430493b57a499a404b142d60c5b1aa36c` |
| `results/probe_a10_f6.txt` | `f769cfb2eb6a28a76c9b386fcba2cc6998b1290fe11cec6ba2dc4e3a005e81fd` |
| `results/README.md` | `067585433ac8e96792485c3b4484b0c4078d7c65c8e23e88dde5a7c00979f46b` |

Running or importing the module can leave a `__pycache__` directory beside it. It is not part of
the repository and none is present; the probe in `results/` disables bytecode writing for this
reason. The digests above are the state of this domain as delivered.

## What was not run, and why

- **The independent B0 conformance check.** Its files are placed in the independent-audit-stack
  domain by the map, and that domain re-runs them. The result this domain relies on is the one
  recorded there: 6,701 of 6,701 checks over 900 vectors, with 18 specification gaps.
- **The original `--real-demo` run byte for byte.** Its output survives only inside the reading
  pass log; the raw JSON was never archived. The comparison above is against that log text, which is
  complete.
- **No formal proof tool was exercised.** Nothing in this domain is stated as a machine-checked
  result, so `tamarin-prover`, `maude` and `proverif` were not needed.
- **Nothing was written, moved or deleted in the read-only source tree.** Every source file was
  opened read-only, and no output of these runs was written outside this repository.
