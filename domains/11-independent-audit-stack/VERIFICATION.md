# Verification — domain 11 (independent audit stack)

Two kinds of material live in this domain and they are kept apart here:

- **Re-run for this repository.** Every layer that can be executed without shipping tools or hosts
  this repository does not carry was re-run on 2026-09-13 in the programme's pinned verification
  environment, and its recorded result was compared with the fresh one. Those rows are in §1, each
  with the exact command and a transcript under `results/rerun/`.
- **Quoted as recorded.** Anything that needs a tool, a host or a repository this domain does not
  ship is **not** re-run; it is quoted with the file it was recorded in and with what would be
  needed to run it. Those rows are in §2 and they are marked `not-run` — never as a pass, and never
  as verification by adjacency to something that was run.

Where a re-run disagreed with the record, **both values are kept**. The disagreements are collected
in §3 so that none of them has to be found by reading a table.

Verdicts are one of `reproduced`, `reproduced-with-difference`, `not-reproducible`, `not-run`.

One standing correction governs this whole document: the property layer's "**16/16 and 16/16**" is
**withdrawn** (programme records `records/failed-assumptions.md`, entry A28). The hash-signature
half fails at collection and runs **0 tests**; Mode B passes 16. Re-run here, both halves, §1 rows
14–15, with the exact error in §3.1.

---

## 0. Environment

| | |
|---|---|
| interpreter | CPython **3.12.3** (`python3` from the pinned virtual environment) |
| activation | the programme's pinned verification environment. The repository carries the portable equivalent: `export PQT_SRC=/path/to/research-tree` on its own line, then `. tooling/activate.sh` (it exports `PQT_ENV`, `PQT_SRC`, `PYTHONDONTWRITEBYTECODE=1`, puts `venv/bin` and `tools/bin` on `PATH`, sets `MAUDE_LIB`, `OQS_INSTALL_PATH`, `LD_LIBRARY_PATH`) |
| Python packages used below | `hypothesis` **6.151.9**, `hsslms` **0.1.3**, `sympy` **1.13.1**, `galois` **0.4.11**, `numpy` **2.4.6**, `pytest` **9.0.2**, `dilithium-py` **1.4.0**, `kyber-py` **1.2.0**, `liboqs-python` **0.16.0**, `pqcrypto` **0.3.4** |
| provers | `tamarin-prover` **1.12.0** with `maude` **3.5.1**; `proverif` **2.05** |
| compilers | `clang`/`clang-18` **18.1.8** — **without** the sanitizer runtimes (see §2) |
| absent from this host, and not shipped | EasyCrypt, SageMath, Docker, the devnet nodes, the ACVP vector files |
| host | one x86-64 host, 12 cores, 15 GB RAM; every runtime below is from it and is not portable |
| date | 2026-09-13 |

Commands below are written from the domain root (`domains/11-independent-audit-stack/`) with the
environment activated. `$PQT_SRC` is the read-only research tree; no layer writes into it.

---

## 1. Re-run for this repository

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| Map fidelity: every published copy against `records/file-map.tsv` | per-row `sha256` of source and of the published copy (139 rows), then `python3 tooling/checks/verify-repository.py` at the repository root | pinned env | the map register itself: **139 D11 `copy`/`copy-history` rows**, each with a digest and a size (77 further D11 rows are `excluded`: recorded by the map, deliberately not copied) | **139 rows: 0 missing sources, 0 source-digest mismatches; 97 published files byte-identical to source; 42 differ** (671 changed lines in total), every one of them registered in `records/rewrites.tsv` (196 rows) | reproduced | of the 42, **21 differ only on lines that carry a machine path** in the source (the `<workdir>/`/`<source-tree>/` placeholders, or a scratch path deleted outright) and **21 have at least one changed line with no path in it**: the `PYLIB` deletion and the `PQT_SRC` environment guards (`math/math_layer.py`, `fault/fault_injection.py`, `fixes/make_fixes.py`, `independent-b0/gen_b0_vectors.py`, the four `property/test_*.py`, the two `fixes/property_fixed/*.py`), shell drivers referencing the environment (`run_all.sh`, `property/run_all.sh`, `formal/perlemma_n7_8g/run.sh`), `implementation/build.sh`'s fallback to the published copy of the frozen C target, prose rewordings (`formal/FINDINGS.md`, `formal/qpt128_quorum.spthy`, `implementation/TARGET_NOTES.md`, `property/test_props_b0.py`), the two recorded overview documents, and the `tooling/audit-stack/Dockerfile.math` example comment |
| `math/` M1–M8 | `python3 math/math_layer.py` | pinned env | `math/math_results.json`: 8/8 `REPRODUCED`, `_meta.seconds` **82.6**; the v0.1 log ends `"seconds": 217.2` (`math/math_run.log`) | 8/8 `REPRODUCED`, `_meta.seconds` **235.8**; **every measured value identical** to the recorded file — the diff is that one line | reproduced-with-difference | timing only, and it is a whole-machine figure. Transcript `results/rerun/math-layer.txt` |
| the recorded math results file itself | `sha256sum math/math_results.json` vs its map source | pinned env | source `audit_stack_v0.2/qpt_audit_stack/math/math_results.json`, sha256 `7536bdaa4b85df189f0ad914fa94d904bdd41d20b2fb4593f0fd1c0b26cfc2a3`, 7,779 B | identical to source, digest re-checked | reproduced | this layer writes its output into the working directory, and a re-run during assembly **overwrote** the published copy (`_meta.seconds` 211.4, a value that exists nowhere else). The recorded file was restored from the source byte-for-byte. See §3.7 |
| Tamarin N = 4, all 12 lemmas | `tamarin-prover --prove formal/qpt128_quorum.spthy +RTS -N2 -M2500m` | pinned env | `formal/tamarin_output.txt`: 12/12 verified, steps 9, 6, 162, 158, 6, 2374, 82, 34, 18, 15, 82, 22; exit 0; Tamarin's own processing time 111.31 s (v0.1; 126.74 s in the v0.2 full-stack run) | 12/12 verified, **the same 12 step counts in the same order**; the output is identical to the recorded file line for line — of 9,607 lines only 5 differ: the header timestamp, Tamarin's own `processing time: 111.31s` → `132.08s`, and the shell timing block; exit 0 | reproduced-with-difference | runtime only. Transcript `results/rerun/formal-tamarin-n4.txt` |
| Tamarin N = 4, one lemma alone | `tamarin-prover --prove=C1_intersection_nonempty formal/qpt128_quorum.spthy` | pinned env | `formal/perlemma_n4/summary.txt`: `C1_intersection_nonempty \| rc=0 \| 4s \| verified (34 steps)`; the per-lemma file's own `processing time: 4.27s` | verified (34 steps), exit 0; also identical apart from the same 5 lines (timestamp, `processing time: 4.27s` → `4.76s`, shell timing); shell wall clock 4.841 s | reproduced-with-difference | runtime only; the other lemmas are reported "analysis incomplete" in that file, which is what a single-lemma run means. Transcript `results/rerun/formal-tamarin-n4-C1.txt` |
| Bounded checker (third protocol model) | `python3 formal/bounded_checker.py` | pinned env | `formal/bounded_checker_output.txt`, 0.45 s | **byte-identical**: the transcript and the published file both hash to `1e7db0a1d20ab2efbfe2b9741f4a0c9dd70b3f3da88e13758d48e220d4f0a571`, 0.679 s | reproduced-with-difference | runtime only. Transcript `results/rerun/formal-bounded-checker-output.txt` |
| Primitives cross-validation | `python3 primitives/cross_validate.py` (needs the five ACVP files, row below) | pinned env | `primitives/results.json` + `primitives/RESULTS.md`, 24.7 s; `disagreements=0`, `critical=0` | **0 disagreements, 0 critical**; every ACVP pass/fail table identical; 20 JSON fields differ: `versions.liboqs.commit` is `unknown` (the fetched liboqs has no git metadata), the recorded `<workdir>` path field, the 12 timing medians, `runtime_s` 59.2, and `tamper.kem_public_key` 10/40 → **9/41** | reproduced-with-difference | the tamper split is not stable: a second consecutive run of the same command recorded **3/47** (`results/rerun/primitives-results-second-run.json`). See §3.5. Transcripts `results/rerun/primitives-cross-validate.txt`, `…-second-run.txt` |
| NIST ACVP vector files | fetch the five `internalProjection.json` from commit `975de31eb83d…` and digest them against `primitives/vectors/SOURCE.txt` | pinned env | SOURCE.txt records the commit, the download date and the sha256 of each file | **5 of 5 match** | reproduced | the files are not redistributed (`docs/inputs-and-provenance.md` §3). Transcript `results/rerun/acvp-vectors.txt` |
| Property suites, differential and malformed input | `bash property/run_all.sh` | pinned env | `property/logs/summary.txt`: tesla exit 0 `8 passed, 2 xfailed`; b0 exit 0 `12 passed`; hashsig exit 1 `5 failed, 11 passed`; modeB exit 1 `2 failed, 14 passed`; differential `100 agree` | identical counts and exit codes; differential `n=100 agree=100 accepted_by_both=0`; timings longer (3.46 / 12.55 / 26.25 / 146.36 s against recorded 2.61 / 6.56 / 22.47 / 110.09 s) | reproduced-with-difference | timings only; the failures are findings F2–F5, recorded as such. Transcript `results/rerun/property-suites.txt` |
| Fault injection | `python3 fault/fault_injection.py` | pinned env | `fault/fault_results.json`: 300 schedules, 1,717 checks, 3,700 corruptions rejected, 33 conflicts extracted, 0 failures | **byte-identical**: the re-run's own `fault_results.json` and the published file both hash to `fe3b28422b32ed59ae0e3dc3455c5b73916cd3ab2d5688db4314c697f03ceb2b`; 0.822 s | reproduced | the recorded README figure is "< 1 s". Transcript `results/rerun/fault-injection.txt` |
| Independent B0 implementation | `python3 independent-b0/check_vectors.py` | pinned env | `independent-b0/independent_results.json`, 9.6 s, 0 disagreements, 6,701 agreements | **byte-identical**: the published file and a fresh run made for this row both hash to `fdaba88228c211ee628453d2a5ad67f92f165b7ad7608e483071ae50d6831ce0`; 4.904 s (5.813 s on the earlier re-run) | reproduced-with-difference | runtime only. Transcript `results/rerun/independent-b0.txt` |
| ProVerif, C = 2 | `proverif formal/qpt128_quorum.pv` | pinned env, ProVerif 2.05 | recorded state: **unexecuted** on the host that produced the models; the file's header carries the expectations, not observations | exit 0, 0.35 s; 9 queries answered: A, A′, D, D′, the C = 2 trivial B/C form **true**; "two accepted frames ⇒ same candidate" **false** with the expected attack trace; `Accept` reachable; `Evidence` reachable | reproduced | every expectation written in that file holds. Transcript `results/proverif-run/qpt128_quorum.out` |
| ProVerif, C = 1 | `proverif formal/qpt128_quorum_C1.pv` | pinned env, ProVerif 2.05 | same recorded state; its header expects the query `not Evidence` to be **true** (no evidence reachable at C = 1) | exit 0, 0.25 s; A, A′, D, D′ **true**; E1 ("two accepted frames ⇒ same candidate") **true**; `Accept` reachable; **`not Evidence` is false — `Evidence` is reachable**, with an exact counter-example trace | reproduced-with-difference | a model-vs-its-own-expectation disagreement, falsified by the first execution of that model; the model is not refuted (D still holds). See §3.6. Transcript `results/proverif-run/qpt128_quorum_C1.out` |
| Mode B fixed property suite | `python3 -m pytest -q fixes/property_fixed/test_props_modeB_fixed.py` | pinned env | recorded as the first half of "16/16 and 16/16" (`docs/audit-stack-overview.md` §3b step 1, stack README) | **16 passed** in 202.13 s | reproduced | this half of the withdrawn claim survives. Transcript `results/rerun/fixed-file-suites.txt` |
| Hash-signature fixed property suite | `python3 -m pytest -q fixes/property_fixed/test_props_hashsig_fixed.py` | pinned env | recorded as the second half of "16/16 and 16/16" | **collection ERROR: 0 tests executed**, exit 1 | **not-reproducible** | the standing correction, A28. Exact error in §3.1. Transcript `results/rerun/fixed-file-suites.txt` |
| Fixed-file self-tests | `python3 $PQT_SRC/hidden_signer_modeB_v1.51.py --self-test`; `python3 $PQT_SRC/pq_infra_s1s2_hashsig_dnssec_v2.2.py --self-test`; `python3 $PQT_SRC/pq_audit_s1_lms_v2.2.py --self-test` | pinned env | `fixes/hidden_signer_modeB_v1.51.py.log`: `Ran 7 tests … FAILED (errors=1)`; `fixes/pq_infra_s1s2_hashsig_dnssec_v2.2.py.log`: `Ran 15 tests … OK`; `fixes/pq_audit_s1_lms_v2.2.py.log`: `Ran 12 tests … OK` | Mode B v1.51 **7/7 OK** (`Ran 7 tests in 23.041s`, and `in 8.111s` on the second run); hashsig v2.2 **15/15 OK** (`Ran 15 tests in 0.197s`); lms v2.2 **12/12 OK on one run and 11/12 on another**, the failure being `S1-011_grover_simulation_matches_law` (`0.5651768673355566 != 0.5 within 0.06`) | reproduced-with-difference | the archived Mode B log is an earlier failing iteration (§3.2, K11). `S1-011` is a coin flip: **7 of 10** consecutive re-runs passed (3 failed). Transcripts `results/rerun/fixed-file-selftests.txt`, `results/rerun/s1011-stability-probe.txt`; see §3.4 |

The `fixes/` layer's derivation script is deliberately **not** re-run — see §2.

---

## 2. Quoted as recorded — not re-run here

Each row names the file the recorded value lives in and what would be needed to run it. None of
these is a pass, and none of them inherits credit from the rows in §1.

| item | command (as recorded) | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| **C19** — 43-of-64 accountability under real consensus, threshold 22 | 64-seat sweep `C = 0…26` plus one-sided points, then a 4-node matrix | the **devnet** (64 seats, 4 nodes); not this repository and not this host | **28/28 points passed**; C-21 no conflicting pair (503 + 44 > 43); C-22 a pair, 22 named, 0 honest — `docs/audit-stack-overview.md` row C19 | not run | **not-run** | reason: the experiment is a devnet result and the devnet is excluded from this repository (`docs/inputs-and-provenance.md` §3 ships no binaries, containers or hosts). The sweep's own record is transcribed at `docs/05-devnet-evidence/` (run `20260911T134816Z`, `complete: true`, 28 points, 0 failed) and the claim is deliberately **not** restated from there. To run it: the devnet kit plus the 64-seat and 4-node hosts. Both programme documents already say the same: `docs/02-theory-and-references/gaps-and-unknowns.md` item 11 and `docs/04-security-and-validation/validation-status.md` |
| **EasyCrypt** `formal/frame_b0.ec` | `easycrypt compile frame_b0.ec` | needs an EasyCrypt toolchain (≥ 2024.x) with Why3 and an SMT solver — absent here and not shipped | a **reduction-sketch**: FRAME(B0) → EUF-CMA with loss N, game-hop plan in comments; the proof is `admit`ted, and three defects are visible to a reader (`Frame_Adv` declared over an oracle while instantiated with a `Scheme`; `corrupted <- fset0` never updated; `EUF_CMA.sk` referenced after the submodule that declares it) | not run | **not-run** | to run it: install EasyCrypt + Why3, then **replace the `admit`s** — compiling it as shipped would produce a "proof" of nothing. It is not evidence for QPT-128 in either case. See `docs/theory-and-borrowed-parts.md` §2, `docs/formal-models.md` §5 |
| ProVerif **as the ledger records it** | — | — | "model written, **unexecuted**" (`docs/audit-stack-overview.md`, tool-status row and claim C20) | run here, §1 rows 12–13 | not-run *as recorded* | the recorded "unexecuted" is left exactly as recorded; the two runs here are a *later* observation, not a correction of the ledger's statement about the audit host |
| Implementation layer: reduced sanitizers and libFuzzer | `bash implementation/build.sh && bash implementation/run_sanitizers.sh && bash implementation/run_fuzz.sh` | clang-18 **with** `-fsanitize=address,undefined,memory` runtimes; the layer expects a private resource dir `implementation/rt/18/` (an extracted `libclang-rt-18-dev`) | `implementation/asan_ubsan_output.txt` (F1 reproduced), `implementation/ubsan_output.txt`, `implementation/msan_output.txt`; `implementation/fuzz_log.txt`: 81,041 executions, 0 crashes, 0 accept-on-invalid | not run | **not-run** | reason: the sanitizer runtimes are **neither installed here nor shipped** — `clang-18 -fsanitize=address` fails with `/usr/bin/ld: cannot find …/libclang_rt.asan-x86_64.a: No such file or directory`, exactly the blocker `implementation/IMPLEMENTATION_RESULTS.md` line 5 records. To run it: `apt-get download libclang-rt-18-dev` (the same exact version) and extract it into `rt/18/`, as the source did |
| Implementation layer: production-parameter campaigns | `bash implementation/run_asan_production.sh` | clang-18 + runtimes, 8 threads, 2,194 s; MSan single-threaded, 3,600 s | `implementation/production/PRODUCTION_RESULTS.md`: ASan + UBSan at production parameters 0 ASan errors, 0 UB errors, **F1 reproduced (2 × 9,568 B)**; **MSan inconclusive** (timed out, no diagnostics) | not run | **not-run** | reasons: the runtimes above, plus ~37 minutes for ASan and a multi-hour budget for MSan (the MSan run did not finish in 60 min at 8 threads' worth of work). The recorded MSan outcome is **inconclusive, not a pass**, and stays that way |
| Tamarin N = 7 sweep at `-M8000m` | `formal/perlemma_n7_8g/run.sh` | ≥ 8 GB per lemma; the recording host had 15.6 GB with ~5 GB available | `formal/perlemma_n7_8g/RESULT.txt`: exit 137 after 194 / 204 / 265 s for A / B / C1; C2 also 209 s; E2 has no exit line; D1 and E1 never started | not run | **not-run** | reason: memory-bound on the recording host, and the queue was stopped to protect a production run; a re-run here would repeat a known resource failure. To run it: a host with ≥ 32 GB and hours per lemma. The v0.1 wording "all seven OOM-killed" is corrected in `docs/formal-models.md` §2 (K13) and §3.3 |
| SageMath engine for `math/` | `docker build -f tooling/audit-stack/Dockerfile.math …` | Docker + the `passagemath` wheel | `math/docker_build.log`, `math/docker_run.log`: the container built and reproduced 8/8 | not run | **not-run** | reason: no Docker on this host and no container is shipped. The math layer was re-run natively instead (SymPy 1.13.1 + galois 0.4.11), which is what `math_results.json` records as its engines: `"sage": "not installed"` |
| Full-stack `run_all.sh`, end to end | `bash run_all.sh` | pinned env + the implementation layer's toolchain | `results/run_all.log`, `results/run_all.console.txt` (the recorded full-stack run) | not run as one command | **not-run** | reason: it re-runs the fuzz/sanitizer layers that cannot run here (§2 rows 4–5) and it would write a fresh `run_all.log` over the stack root; every *other* layer it calls was re-run individually, §1 |
| `fixes/make_fixes.py` | `python3 fixes/make_fixes.py` | pinned env | derives `modeB_prover_v1.51.c`, `hidden_signer_modeB_v1.51.py`, `pq_infra_s1s2_hashsig_dnssec_v2.2.py`, `pq_audit_s1_lms_v2.2.py` by exact single-match replacement (aborts on drift) | not run | **not-run** | reason: the script **writes into the read-only research tree**, which the standing rule forbids (`docs/inputs-and-provenance.md` §1). The four fixed files are already published in the domains that own them, and the regression tests that load them from there **were** re-run (§1 rows 14–16) |
| The devnet's own environment and measurements | — | the devnet repository | `docs/05-devnet-evidence/*` | not run | **not-run** | belongs to the devnet domain; named here only because C19 above refers to it |

---

## 3. Discrepancies

Kept in both forms: the record as recorded, and the observation. None of them is smoothed over in
the domain's README or in its documents.

### 3.1 The "16/16 and 16/16" is withdrawn (A28) — hash-signature half runs **0 tests**

`fixes/property_fixed/test_props_hashsig_fixed.py` fails at **collection**, so the recorded count
for that half is not reproducible:

```
ERROR collecting test_props_hashsig_fixed.py
<stack root>/fixes/property_fixed/test_props_hashsig_fixed.py:100: in <module>
    _k = T4.LmsPrivate(_pair[0], _pair[1], I=b'\xA5' * 16, seed=(bytes(_pair) * 16)[:32])
<source-tree>/pq_audit_s1_lms_v2.2.py:149: in __init__
    raise ValueError('F3: LMS m and LM-OTS n must match (SP 800-208 approved sets pair n with m; '
E   ValueError: F3: LMS m and LM-OTS n must match (SP 800-208 approved sets pair n with m; RFC 8554 5.1: the two hash functions SHOULD be the same)
1 error in 3.85s
```

The module builds an `LmsPrivate` on a mixed m ≠ n typecode pair at import; the F3 fix now refuses
exactly that. Mode B's half is sound (16 passed). The correct statement is **Mode B 16/16,
hash-signature 0 collected**, and this domain reports that form. Records entry A28; archived
`fixes/property_fixed/hashsig_fixed.log` shows the same crash.

### 3.2 The v1.51 "7/7" against its archived log (K11)

`fixes/hidden_signer_modeB_v1.51.py.log` records 7 tests with **1 ERROR**
(`TypeError: object of type 'int' has no len()`, reached through `cfg_of`). A fresh run gives
`Ran 7 tests in 23.041s / OK`. Both are kept. The reason to prefer the fresh run is checkable: the
failure is inside the fix's *own new test*, and the source archive's metadata puts the log at
`03:55:53` and the fixed file's last write at `03:56:30` — the log is 37 s older than the file it
records, i.e. an earlier, still-failing iteration. The published copy of the log carries the
assembly's copy time, so those mtimes are quoted from the source archive, not from the file in
`fixes/`.

### 3.3 The N = 7 sweep is "resource-limited", not "all seven OOM-killed" (K13)

The v0.2 ledger's "Not done" line says the seven remaining N = 7 lemmas "are OOM-killed even at
`-M8000m`". The recorded files do not support the sweep: `formal/perlemma_n7_8g/RESULT.txt` names
three lemmas (A/B/C1 at 194/204/265 s), the per-lemma files record exit 137 for **four**
(A 194 s, B 204 s, C1 265 s, C2 209 s), `E2` has no exit line, and `D1`/`E1` were never started.
And the failures are not stable across runs (`formal/perlemma_n7/summary*.txt`: `A2` rc = 251 in
one pass and verified in 4,685 steps in another) — which is what makes them resource effects rather
than falsifications. **Nothing was falsified at N = 7.**

### 3.4 `S1-011` in the fixed LMS module is a coin flip (found here)

`python3 $PQT_SRC/pq_audit_s1_lms_v2.2.py --self-test` recorded `Ran 12 tests … OK`. On re-run it
gave 12/12 **once** and 11/12 on another run:

```
AssertionError: 0.5651768673355566 != 0.5 within 0.06 delta (0.06517686733555661 difference)
  File "<source-tree>/pq_audit_s1_lms_v2.2.py", line 503, in test_S1_011_grover_simulation_matches_law
```

A stability probe of 10 consecutive runs passed **7** and failed **3**. So the 12/12 in
`fixes/pq_audit_s1_lms_v2.2.py.log` is a single favourable draw of a probabilistic test, not a
stable result. This is the same test the programme's own validation status already flags as a coin
flip from the other direction (`docs/04-security-and-validation/validation-status.md`: the recorded
assertion held in 49.0 % / 53.5 % / 52.0 % of three large batches of runs). Both records stand;
the fixed *code* is unaffected — F3's refusal and the F2/F4 fixes are deterministic tests.

### 3.5 `primitives/`: the tamper split is not reproducible, and neither is the liboqs commit

The `tamper.kem_public_key` row takes **four different values for the same command**, and all four
are recorded:

| run | `rejected_ek` | `different_key` | where |
|---|---:|---:|---|
| v0.1 | 6 | 44 | `history/primitives-results-v0.1.json` |
| v0.2 (the published result) | 10 | 40 | `primitives/results.json` |
| first re-run | 9 | 41 | `docs/primitive-cross-validation.md` §3 (its own JSON was overwritten in the scratch copy by the next run) |
| second re-run | 3 | 47 | `results/rerun/primitives-results-second-run.json` |

What is stable across all four is the part that matters: the two counts always sum to 50, both
implementations always report the *same* split (`impls_differ: []`), `impls_agree_on_ek_validity`
is 50/50, `same_key` is 0, and `critical` is empty. The count that moves is how many of the 50
single-byte flips land in a region where liboqs refuses the key at all. `primitives/cross_validate.py`
line 41 seeds the module RNG (`random.Random(0x5150_2026)`, comment "reproducible messages / tamper
positions") and the positions come from it (`RNG.sample(range(len(ek)), N_TAMPER)`), but the key
being tampered with is generated by **unseeded** keygen — the harness only injects a seed for the
ACVP replay (`OQS_randombytes_custom_algorithm`, switched back to the system RNG afterwards). So
the row is a random variable even when the positions are not, and the doc's own reading of it is
the same. Reported as a stochastic row whose recorded value is one draw, not as a disagreement
between implementations.

Separately, `versions.liboqs.commit` is `unknown` in a re-run because the fetched liboqs build tree
carries no git metadata; the recorded value `5a1a854b0dc9f2141bdc771c555ee60c37950183` is the tag's
commit as `primitives/RESULTS.md` states it.

### 3.6 ProVerif C = 1: a documented expectation is falsified by measurement

The C = 1 model's own header expects `not Evidence` to be **true**. The run answers **false** —
`Evidence` is reachable: the adversary reads the published `sk0` and submits
`sign((a, a_1, s0), sk0)` and `sign((a, a_2, s0), sk0)` as two signatures of seat `s0` on
conflicting transcripts, so the extractor fires. No `Signed` event accompanies those terms (the
adversary built them with the `sign` constructor), so the one-candidate `restriction` does not
block the trace, and no two *accepted* frames are derivable — which is why E1 still holds. The
security-relevant queries are unaffected (`Evidence ⇒ Corrupt` is still true; the model is not
refuted). Reported as a **model-or-ledger expectation falsified by measurement**; the model file is
not edited.

### 3.7 The recorded math results file was overwritten during assembly, and restored

`math/math_layer.py` writes its output into the working directory. A re-run during assembly
therefore overwrote the published `math/math_results.json` with a fresh run (`_meta.seconds` 211.4,
a value that exists in no other file). The published copy was restored **byte-for-byte from its map
source** (`audit_stack_v0.2/qpt_audit_stack/math/math_results.json`, sha256
`7536bdaa4b85df189f0ad914fa94d904bdd41d20b2fb4593f0fd1c0b26cfc2a3`, 7,779 B) and the digest
re-verified against the map row. Recorded in
`docs/inputs-and-provenance.md` §4 and here. The same class of accident is why the re-runs for this
domain were made in a scratch copy of the stack outside the repository, and why `results/rerun/`
(the transcripts) is kept separate from `results/run_all.log` (the recorded run).

### 3.8 Timing figures do not travel

Recorded runtimes were produced on the recording host under different load; the re-runs above are
all on one 12-core host. The figures move and the *results* do not: math 82.6 → 235.8 s, Tamarin
N = 4 111.31 → 132.08 s (Tamarin's own processing time), C1 alone 4.27 → 4.76 s, bounded checker
0.45 → 0.679 s, primitives 24.7 s → 59.2 s and 30.2 s (`runtime_s`, recorded in
`docs/primitive-cross-validation.md` §3 and `results/rerun/primitives-results-second-run.json`;
wall clock 59.374 s and 30.189 s), independent B0 9.6 s → 5.813 s and 4.904 s (a fresh run made for
this document), property suites 2.61/6.56/22.47/110.09 → 3.46/12.55/26.25/146.36 s, Mode B v1.51
self-test 11.180 → 23.041 s (`results/rerun/fixed-file-suites.txt`) and 8.111 s
(`results/rerun/fixed-file-selftests.txt`), hashsig v2.2 self-test 0.471 → 0.197 s, lms v2.2
self-test 20.096 → 8.403 s. No verdict above rests on a timing figure.

### 3.9 Two figures the source records that this domain does not restate as its own

- The mutation count is **17,160**, not the 17,660 the v0.1 and v0.2 ledgers both print: 3 XOR masks
  over a 5,720-byte frame is 17,160, and the ledger's figure is not divisible by 3, so the loop
  cannot produce it (`docs/property-suites.md` §3, correction K14). The ledger is left as recorded.
- The SUPPRESS triple-collision slope is **−3.07** as machine-written in `math/math_results.json`
  (key `fitted_slope_triple_vs_m`, line 179, identical in the v0.1 and v0.2 runs) and **−3.03** as
  the prose of the ledger's C5 row states. This domain quotes the JSON, because that is the value
  the prose is describing.

---

## 4. Limits of this verification

- A **reproduced** verdict means: the recorded computation repeats here, on this host, with the
  commands above. It never means the construction is proven. Nothing in this domain proves QPT-128
  secure; nothing here proves the C prover memory-safe.
- The re-run transcripts in `results/rerun/` are the fresh outputs, with the two machine paths
  written as `<workdir>/` and `<source-tree>/` exactly as the recorded files write them; frame
  numbers, file names and error text are otherwise untouched. `results/run_all.log` and
  `results/run_all.console.txt` remain the **recorded** run, not a re-run.
- Rows in §2 are quoted, not verified. In particular the **C19** devnet result, the **EasyCrypt**
  skeleton and the **production sanitizer** campaigns are not evidence produced by this domain, and
  they are not listed as evidence for anything it claims.
- The environment is one host's; §3.8 lists every figure that moved with it.

---

## 5. The repository's own gates, over this domain

Run from the repository root (`/path/to/Post-Quantum-Cryptography`) on 2026-09-13 at 19:29, after the
whole domain — this file included — was in its final state:

| command | observed | verdict |
|---|---|---|
| `python3 tooling/checks/scan-forbidden.py .` | `files scanned: 644, findings: 0`, every one of the scanner's six categories zero and no file named; exit 0 | reproduced |
| `python3 tooling/checks/verify-repository.py` | `missing from repo: 0`; `sha256 differences: 0 (explained by rewrites: 132)`; `authored documents: 184`; `UNEXPLAINED files: 0`; `empty files: 0`; `malformed map rows: 0`; `RESULT: PASS`; exit 0 | reproduced |

Both gates were also run earlier during this assembly and again by the tooling package between 19:26
and 19:28, with the same counts; the domains' independent-reproduction rule applies to gates as to
everything else here, and the second measurement was made independently, against the same tree.

**An earlier scan of this domain did report a finding, and it stays on the record.** A whole-tree
scan made before the fixups were finished (626 files) reported exactly one finding, and it was
here: the research tree's own path, left inside a captured traceback in
`results/rerun/fixed-file-selftests.txt` by the emitter that wrote the transcript. The emitter was
corrected to write `<source-tree>/`, the file was regenerated from the same run with frame numbers,
file names and error text unchanged, and every scan recorded above was made after that. The counts
of the two clean runs are the ones quoted; the finding is not deleted, and the two tracebacks that
carry `<source-tree>/` are published as recorded, exactly as the source tree's own traceback logs
do.

Two cautions about quoting these:

- **No transcript of a whole-tree scan is stored in this domain.** The scanner prints its own
  absolute source path in the identity-skip note on stdout, so a faithfully stored whole-tree
  transcript would itself contain the string the `abs-path` rule forbids — the file would be a
  finding the moment it was committed. The transcripts under `results/rerun/` are per-layer runs
  and contain no such line; only the counts above are quoted.
- **A gate that does not parse reports nothing.** The tooling package's own verification records a
  window (19:24:33–19:25:47) in which `tooling/checks/scan-forbidden.py` raised
  `re.error: unbalanced parenthesis` and exited 1, while `verify-repository.py` stayed at PASS. No
  scan result recorded in this document was produced in that window — every one of them returned a
  count — and the counts above were re-measured after the repair rather than carried over from
  before it.
