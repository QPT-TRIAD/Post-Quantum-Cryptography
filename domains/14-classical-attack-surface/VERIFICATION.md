# Verification — domain 14 (classical attack surface)

Every command below was run on 2026-09-21 from `domains/14-classical-attack-surface` in this
repository, against the files as published. The campaign in `results/campaign-2026-09-21-E300/` was
**not** regenerated: it is the evidence this domain's prose cites, it takes far longer than a test
run, and re-running it would overwrite that evidence. What was re-run is the test suite, the scope
mode, one real attack end to end, and a machine cross-check that every fitted exponent printed in
the report is the one stored in the payload beside it.

**Environment.** The sage environment interpreter — CPython **3.12.14** — which is the interpreter
that provides **fpylll 0.6.4**, **G6K 0.1.2**, **SageMath 10.9** (PolyBoRi for the Gröbner tracks)
and **numpy 2.4.6** in one process, with **pytest 9.0.2** and **hypothesis 6.151.9**. There is no
subprocess boundary between the harness and the mathematics libraries: the lattice track calls
fpylll through the sibling domain 13 engine in the same interpreter. `pyproject.toml` sets
`testpaths = ["tests"]` and `pythonpath = ["src"]` and no other pytest options. Host: Ubuntu
24.04.4, x86_64, kernel 7.0.0-31, 12 cores, with another domain's suite running at the same time.

| item | command | environment | expected | observed | verdict | notes |
|---|---|---|---|---|---|---|
| the test suite | `python -m pytest -q` | sage environment interpreter | the suite passes; the domain records 95 tests | **`95 passed in 6.34s`**, exit 0 | reproduced | four test files — `test_primitives.py`, `test_attacks.py`, `test_workload_curve.py`, `test_campaign_and_cli.py` — holding 60 `def test_` bodies; the remainder are parametrised cases. Run with `-p no:cacheprovider` and `-o addopts=""`; `python -m pytest --collect-only -q` under the project's own options reports **95 tests collected**, so neither flag selects |
| scope boundary is printed, not summarised | `scripts/qpt-cart scope` | sage environment interpreter | the paragraph of `src/qpt_cart/scope.py`, verbatim | exit 0; printed verbatim, including *"It cannot VALIDATE production security"* and the three mis-extrapolation figures **+4.6, −12.4, −38.1** | reproduced | the mode reads no result file and takes no arguments |
| boundary heads the stored report | a reader script asserting `SCOPE_BOUNDARY` occurs in `results/campaign-2026-09-21-E300/report.md` and equals `results.json:scope_boundary` | sage environment interpreter | the boundary is structural, not decoration | **present byte-identically in both** | reproduced | a report that lost it would be claiming more than the tester supports; the suite asserts the same thing independently |
| every printed fit is the stored fit | the same script comparing each track's `exponent_bits_per_unit`, to three decimals, against the report text | sage environment interpreter | 9 tracks, 9 fits, no disagreement | **9 tracks, 9 fits, 0 mismatches**: 0.992, 0.046, 0.983, 0.993, 0.983, 0.483, 0.722, 1.120, 0.337 | reproduced | this is how the prose is held to its own artifacts, and it is the check that would catch a narrative that had drifted from its payload |
| the control gate | the same script reading the two control tracks' verdicts | sage environment interpreter | the random function must come out exponential at ≈ 1.0; the linear map must be caught as polynomial | `control_random_function`: **exponential in range**, 0.992. `control_linear_map`: **polynomial in range**, 0.046, power-law degree 3.00 | reproduced | both roles present in the payload. Had either verdict been wrong the report would have declared its own subject verdicts void, and none of §4 of `README.md` could be read |
| one attack, run end to end now | `scripts/qpt-cart attack keymap_b_groebner --size 10` | sage environment interpreter, PolyBoRi | a real solve, verified against the primitive's own `verify` | exit 0; `success: true`, `verified: true`, `openings_found: 1`, 20 unknowns, 42 equations, `max_degree: 3`, **1.707 s** against the campaign's stored median of 0.9008 s at the same size | reproduced-with-difference | only the wall clock moves, and it moves because the host was running two other suites; the solve, its verification and the system's shape are identical. Seconds are the unit of work for this track, which is exactly why the track's fit is labelled as seconds on one machine and never as operations |
| the counted subjects' growth rates | stored: `results/campaign-2026-09-21-E300/` | campaign `full`, `E = 300`, generated 2026-09-20T23:23:58Z | each should land on the record's formula | Mode B exhaustive search **0.983** (95 % 0.951…1.016) against 1.000; Mode A **0.993** (0.954…1.031) against 1.000; structural collision **0.983** (0.900…1.065) against 1.000; birthday **0.483** (0.430…0.537) against 0.500 | recorded, not re-run | these four are *counted*, not timed, so they are machine-independent. Each verdict is "exponential in range" with the exponential model fitting 13.0×, 18.8×, 6.8× and 3.6× better than the polynomial one |
| the Mode A algebraic verdict | stored, as above | — | the harness expects a staircase and requires a factor of 3.0 before naming a model | **inconclusive**: exponential RSS 2.5568 against polynomial RSS 2.5745; growth 0.722 (0.548…0.895). Medians 0.042, 0.063, 0.136, **1.135**, 2.944, 5.348, 8.854 s at `n = 16…28` | recorded, not re-run | the expectation is written into `harness.py` beside the track, before the run, so "inconclusive" is a description rather than an excuse. The step between `n = 20` and `n = 22` is larger than the whole range on either side |
| the Mode B algebraic verdict | stored, as above | — | — | **exponential in range**, growth 1.120 (0.981…1.258), exponential model 3.5× better | recorded, not re-run | this is the figure §5 of `README.md` says survives the implementation correction: above one bit per bit of `n`, so this attack never overtakes search |
| the lattice track | stored, as above | fpylll BKZ, 1 thread | a "polynomial in range" verdict here would be the LLL regime, not a break | **exponential in range**, growth 0.337 (0.306…0.368), 7.0× better; **sizes 40 and 48 dropped from the fit** because a seed did not finish; minimum block sizes `[2]`, `[2]`, `[2]`, `[2]`, `[2, 20]`, `[10, 30]`, `[30]`, `[40]` | recorded, not re-run | the column that carries the meaning is the block size, not the seconds. One thread, because G6K is not reproducible above one — the finding is domain 13's and is inherited here |
| the implementation correction is printed where the table is | reading `results/campaign-2026-09-21-E300/report.md` §2b and `src/qpt_cart/reporting.py` | sage environment interpreter | the comparison must not be presentable as an algorithm comparison | the paragraph **"This compares two implementations, not two algorithms — read it that way"** is emitted from `reporting.py` immediately above the table, with the ≈ 2^12 enumerator factor and the statement that it reverses every "Gröbner wins" row | reproduced | it is generated with the table rather than added to the prose afterwards, so the table cannot be published without it |
| the cited MQ-estimator figure | reading `src/qpt_cart/reporting.py` | — | is it computed here or quoted? | **quoted.** The 2^31 bit operations at `n = 28` and the ≈ 2^35 measured cycles appear only as literal text in `reporting.py`; no CryptographicEstimators import exists anywhere in `src/` | stated, not re-derived | `README.md` §5 labels it as cited for this reason. A reader who wants it re-derived must run that library themselves |
| repository content gate, this domain | `python tooling/checks/scan-forbidden.py domains/14-classical-attack-surface` from the repository root | sage environment interpreter | nothing in this domain may carry a forbidden name, a machine path, a tracking parameter, a contact string or a secret | **files scanned: 31, findings: 0**, exit 0 — every category 0 | reproduced | run after the last edit of this build. The earlier package-style README carried an interpreter path under a home directory and was replaced by this build's `README.md` |

## What was not run, and why

- **The campaign itself.** `scripts/qpt-cart campaign --out <dir> --scale full` rebuilds a results
  directory in place. The stored run is what `README.md` quotes; it was read and cross-checked
  rather than overwritten. Its `meta` block records the scale, the expansion and a generation
  timestamp, which is what a re-runner needs. The longest tracks carry per-point budgets of 600 to
  1,200 seconds, so a full re-run is hours, not minutes.
- **Anything at production size.** `n = 256` is out of reach for every attack here, which is the
  design property under test rather than a shortcoming of the harness.
- **The attacks that were not attempted at all**: hybrid (guess-then-solve), an F4/F5 engine faster
  than PolyBoRi, the alternative Mode B formulation that eliminates `s` and solves degree-6
  equations in `n` unknowns, the dual lattice attack, and every implementation-level attack
  (timing, faults, side channels). A curve that was never measured is not a curve that came out
  flat.
- **The record's formulas.** 148.8 and 378.2 classical bits at `n = 256` are quoted as figures the
  record produced from a formula. Nothing here re-derives them; §4 of `README.md` sets them beside
  a measurement instead.
- **Nothing was written to or read from the read-only research tree.** The record's parameters live
  in this domain's own sources as named constants with their source lines, so a run reproduces
  without that tree present.
