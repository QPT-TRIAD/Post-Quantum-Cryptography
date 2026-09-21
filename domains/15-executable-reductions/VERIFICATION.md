# Verification — domain 15 (executable reductions)

Every command below was run on 2026-09-21 from `domains/15-executable-reductions` in this
repository, against the files as published. The stored campaigns in `results/` were not regenerated:
they are the evidence this domain's prose cites, and each carries its own seed, size and timestamp.
What was re-run is the test suite, the two read-only CLI modes, and a machine cross-check that every
verdict and every conversion ratio in the two reports follows from the two JSON payloads beside
them.

**Environment.** The sage environment interpreter — CPython **3.12.14**, the same interpreter that
provides fpylll 0.6.4, G6K 0.1.2 and SageMath 10.9 for the sibling domains — with **pytest 9.0.2**
and **hypothesis 6.151.9**. This domain itself needs none of the mathematics libraries: it imports
the standard library, the field and key map of domain 14 (through `QPT_RR_PRIMITIVES`), and nothing
else, which is why every figure re-runs identically. `pyproject.toml` sets `testpaths = ["tests"]`
and `pythonpath = ["src"]` and no other pytest options, so the bare command below is the whole
configuration. Host: Ubuntu 24.04.4, x86_64, kernel 7.0.0-31, 12 cores, under load from two other
domains' suites at the time.

| item | command | environment | expected | observed | verdict | notes |
|---|---|---|---|---|---|---|
| the test suite | `python -m pytest -q` | sage environment interpreter | the suite passes; the domain records 41 tests | **`41 passed in 20.40s`**, exit 0 | reproduced | three test files — `test_scheme.py`, `test_reductions.py`, `test_runner_and_report.py` — holding 36 `def test_` bodies; the extra cases are parametrised. Run with `-p no:cacheprovider` and `-o addopts=""` so no cache directory is written beside the sources; `python -m pytest --collect-only -q` under the project's own options reports **41 tests collected**, so neither flag selects |
| scope boundary is printed, not summarised | `scripts/qpt-rr scope` | sage environment interpreter | the paragraph of `src/qpt_rr/scope.py`, verbatim | exit 0; the paragraph printed verbatim, including the sentence *"A reduction that survives every adversary tried here has survived those adversaries, not every adversary."* | reproduced | the mode takes no arguments and reads no result file |
| the un-runnable steps are listed | `scripts/qpt-rr gaps` | sage environment interpreter | four entries: Theorem 3, the two openings of Theorem 2 step 2, assumption A-P, Theorem 4 | exit 0; **4 entries**, each with its reason, identical to `not_runnable` in both stored payloads | reproduced | this is the list reproduced as §6 of `README.md`. A step absent from a report is not thereby confirmed, which is why the mode exists |
| boundary appears in every artifact | a reader script asserting `SCOPE_BOUNDARY` occurs in `results/<run>/report.md` and equals `results/<run>/results.json:scope_boundary`, for both runs | sage environment interpreter | the boundary must head every report and be stored with every payload | **both reports and both payloads carry it byte-identically** | reproduced | the boundary is structural, not decoration: a report that lost it would be claiming more than the runner can support |
| every conversion ratio is recomputable | the same script recomputing `solved / real_wins` for all 18 experiment records and comparing with the stored `conversion` | sage environment interpreter | the two must agree, and a null ratio must correspond to zero real wins | **18 records, 0 mismatches**; `t1_lazy` and `t2_plain` carry a null ratio against 0 real wins in both runs | reproduced | this is how the prose is held to its own artifacts. It is also the check that would catch a report whose narrative had drifted from its payload |
| the headline failure, `n = 8` | stored: `results/run-2026-09-21-n8/` | recorded 2026-09-21T00:11:56Z, seed 20260921, 200 trials | `t1_prequery`: adversary wins 200/200 real games, simulation fails 200/200, 0 solved, verdict FAILS | as recorded: `real_wins` 200, `simulated_wins` 0, `simulation_failures` 200, `solved` 0, `invalid_outputs` 0, `conversion` 0.0, `z_score` 20.0; one failure message, at count 200 | recorded, not re-run | the campaign was not regenerated. Re-running it would overwrite the evidence this domain cites; the payload carries its own seed and is reproducible from it with `scripts/qpt-rr run --out <dir> --n 8 --trials 200` |
| the headline failure, `n = 10` | stored: `results/run-2026-09-21-n10/` | recorded 2026-09-21T00:10:41Z, seed 20260921, 100 trials | the same verdict at a second width | `real_wins` 100, `simulated_wins` 0, `simulation_failures` 100, `solved` 0, `conversion` 0.0, `z_score` 14.14 | recorded, not re-run | two widths, one seed. The finding is structural — the oracle has answered — so it is not expected to be width-sensitive, and it is not |
| the guessing repair's loss | stored: both payloads | — | sound, and converting below its claimed 0.20 | `n = 8`: 37 of 200 simulations survived, 163 aborted on a wrong bet, `conversion` **0.185**, `invalid_outputs` 0. `n = 10`: 17 of 100, 83 aborted, `conversion` **0.17** | recorded, not re-run | the reduction bets on one of 5 possibilities (`max_messages = 4`, so `claimed_success_given_win = 1/5`), against an adversary looking up its target plus 3 decoys. The observed loss factor is about 5.4 at `n = 8`. Soundness is what "HOLDS, WITH LOSS" asserts; tightness is what it withdraws |
| the salted candidate | stored: both payloads | — | the as-written reduction restored against the pre-querying adversary | `t1_salted`: 200/200 and 100/100 converted, 0 simulation failures, `z_score` 0.0, `salt_bits` 64 | recorded, not re-run | **not part of the record.** Its effect on extraction, certificate size and the other theorems was not examined here, and no row of this document should be read as evidence that it is safe |
| control: a broken reduction is caught | stored: both payloads | — | the runner must flag every output as not solving the problem | `control_broken`: `solved` 0 with `invalid_outputs` **200** (`n = 8`) and **100** (`n = 10`), verdict FAILS, although the adversary wins and the simulation runs | recorded, not re-run | this is the control that gives a HOLDS verdict its meaning: a runner that counted wins rather than checking outputs would have called this a success |
| control: no output without a win | stored: both payloads | — | a reduction handed an adversary that never wins must emit nothing | `t1_lazy` and `t2_plain`: 0 real wins, 0 simulated wins, 0 solved, **0 invalid outputs**, verdict NOT EXERCISED | recorded, not re-run | "NOT EXERCISED" is a distinct verdict from "HOLDS" on purpose: what it shows is only that nothing wrong came out |
| Theorem 2 step 2 | stored: both payloads | — | every evasion yields a genuine collision of the key map | 30 of 30 wins at `n = 7` in the first campaign (33 trials), 15 of 15 in the second (16 trials); `solved` equals `real_wins` in both, 0 invalid outputs | recorded, not re-run | **given** the two openings, which come from the ideal prover. The extractor that supplies them in the record is not run — see `scripts/qpt-rr gaps` |
| repository content gate, this domain | `python tooling/checks/scan-forbidden.py domains/15-executable-reductions` from the repository root | sage environment interpreter | nothing in this domain may carry a forbidden name, a machine path, a tracking parameter, a contact string or a secret | **files scanned: 23, findings: 0**, exit 0 — every category 0 | reproduced | run after the last edit of this build, on the finished domain. The earlier package-style README carried an interpreter path under a home directory and was replaced by this build's `README.md` |

## What was not run, and why

- **The campaigns themselves.** `scripts/qpt-rr run` regenerates a results directory in place. Both
  stored runs are the evidence `README.md` quotes, so they were read and cross-checked rather than
  overwritten. Each carries `n`, `trials`, `seed` and a generation timestamp, which is what a
  re-runner needs.
- **Anything at production width.** `n = 8` and `n = 10` are the widths at which an adversary can
  win by exhaustive search within a test run. No figure in this domain is a production number.
- **The four steps of §6 of `README.md`.** Theorem 3, the quantum online extractor, assumption A-P
  and Theorem 4 have nothing executable here, by their own nature rather than by omission.
- **Any statement about hardness.** No attack on A-F1 or A-F2 was attempted, here or anywhere in
  this domain. The runner tests conversions.
- **Nothing was written to or read from the read-only research tree.** The construction's parameters
  are recorded in this domain's own sources as cited constants; the field and key map are imported
  from the sibling domain in this repository.
