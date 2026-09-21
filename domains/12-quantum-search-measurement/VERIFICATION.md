# Verification — domain 12 (quantum search, measured)

Every command below was run on 2026-09-21 from `domains/12-quantum-search-measurement` in this
repository, against the files as published. The two campaigns were **re-run in full** into a scratch
directory outside the repository and compared field by field with the stored payloads, so the stored
evidence is untouched and the reproduction is a real observation rather than a reading of what was
already there.

**Environment.** The project's pinned virtual environment: CPython **3.12.3** with **numpy 2.5.3**,
**qiskit 2.5.2**, **qiskit-aer 0.17.2**, **cirq 1.7.0**, **qsimcirq 0.22.1**, **scipy 1.18.1**,
**pytest 9.1.1** and **hypothesis 6.168.0**. Aer is the primary statevector engine; Cirq/qsim is the
cross-validation engine and is not used by the campaigns below. `pyproject.toml` sets
`testpaths = ["tests"]`, `addopts = "-q --strict-markers"`, two markers (`slow`, `engine`) and one
warning filter; neither the markers nor the filter deselect anything, so the bare command below runs
the whole suite. Host: Ubuntu 24.04.4, x86_64, kernel 7.0.0-31, 12 cores, with another domain's
suite running concurrently for part of the time (see the timing note on the first row).

| item | command | environment | expected | observed | verdict | notes |
|---|---|---|---|---|---|---|
| the test suite | `python -m pytest -q` | pinned virtual environment | the suite passes | **`1059 passed, 38 warnings in 257.13s (0:04:17)`**, exit 0, 0 failures, 0 errors, 0 skips | reproduced | 30 test files holding 613 `def test_` bodies; the remainder are parametrised cases. The 38 warnings are the harness's own `UserWarning`s, raised on purpose where an iteration window is set below the instance's optimum — the tests that exercise the truncated-curve refusal path. The wall clock was measured while domain 13's suite was running on the same host; it carries no claim. Run with `-p no:cacheprovider` and `-o addopts=""`, which the next row shows changes nothing |
| the suite is not silently narrowed | `python -m pytest --collect-only -q`, and reading `pyproject.toml` | pinned virtual environment | the recorded options must not deselect tests | collection under the project's own options sums to **1059**, the same number the run above executed; `addopts` is `-q --strict-markers` and neither flag selects | reproduced | recorded because a marker filter in `addopts` is the ordinary way a suite count silently shrinks. There is none here. The executed run was made with `-o addopts=""` and `-p no:cacheprovider`, so no cache directory is written beside the sources; this row is what shows those flags changed nothing |
| the SHA-256 circuit is SHA-256 | the suite run above; the assertions read from `tests/test_sha256_circuit.py` | pinned virtual environment | the built circuit must reproduce a reference implementation | that file's **23 test bodies pass**, among them: the FIPS 180-4 vectors (`abc`, the empty message, and the 55-byte vector) against the reference digest; **every one-block length** — 56 messages of lengths 0 … 55 — matching the reference; a property-based check over arbitrary one-block messages at 60 examples; a two-block message **refused** rather than mis-hashed; the work registers returned clean; the circuit followed by its inverse the identity on arbitrary states including dirty scratch; and the gate set X, CNOT and Toffoli only | reproduced | the inverse test runs from arbitrary states, not only from states the forward circuit produces, so the inverse is a true inverse. `K` is re-derived at 60 digits from FIPS 180-4 §4.2.2, so a transcription slip in the constants would fail rather than propagate |
| hash-oracle cost campaign, re-run | `python scripts/hash_oracle_cost.py --out <scratch>` | pinned virtual environment | the stored payload of `results/hash-oracle-cost-2026-09-21/` | exit 0; **`verified_digests: 64/64`**, 801 qubits, 45,392 `ccx`, 150,128 `cx`, 2,394 `x`. Compared field by field with the stored JSON: **exactly one field differs, `generated_utc`.** The rendered `report.md` is byte-identical | reproduced | the circuit is verified in the same run that counts it, which is the property that makes the count mean anything. Written to a scratch directory outside the repository so the stored evidence is not overwritten |
| the floor, per query and per hash | the same payload | pinned virtual environment | the record's assumption is 2^18 gates per hash-oracle query | per query, cheapest figure **2^18.60** as built (`log2 18.595844`), margin **+0.60**; published optimised query T-count **2^18.83**. Per single hash, **2^17.59** as built (`log2 17.594514`) and published optimised **2^17.80** — **both below 2^18** | reproduced | the direction of the bound is the finding and is stated in the report's own preamble: a built circuit bounds hashing cost from **above**, the record needs a bound from **below**, so this cannot prove the floor. Error correction is not counted anywhere in this row |
| infrastructure campaign, re-run | `python scripts/infra_campaign.py --out <scratch>` | pinned virtual environment | the stored payload of `results/infra-2026-09-20/` | exit 0 in **69.0 s** wall (3 m 11 s user); compared field by field: **exactly one field differs, `generated_utc`** | reproduced | seed 20260920 is recorded in the payload and the campaign is deterministic from it. Same scratch-directory treatment as the row above |
| iteration law on the record's game | the same payload | pinned virtual environment | the measured success peak should sit at the textbook iteration count | measured peak `k` equals textbook `k` at **every width**: 3/3 at `n = 6`, 7/7 at 8, 17/17 at 10, 50/50 at 12, 71/71 at 14. `P` at peak 0.998139 / 0.996846 / 0.999448 / 0.999945 / 0.999916; max absolute residual against `sin²((2k+1)θ)` 1.44e-15, 2.44e-15, 7.99e-15, 2.41e-14, 5.55e-16 | reproduced | `M` is 3, 3, 2, 1, 2 at those widths and is the *measured* size of the marked set the circuit implements, not a configured target |
| the two fitted exponents | the same payload | pinned virtual environment | the record assumes 0.5 and −0.5 | iteration law **0.529431337710122** against an assumed 0.5; multi-target law **−0.5176478853608645** against an assumed −0.5 | reproduced | both are carried in the payload under `provenance_of_fit`: *fitted to measured points; not a measurement at n = 192 or 256*, and *not a measurement at T = 2^40*. They are fits to five and to seven points and are labelled as fits wherever they appear |
| the structure probes and the one refusal | the same payload | pinned virtual environment | the positive control must fire, the negative control must not | positive control (`hidden_period`) fired on **both** probes, rank 7, 64 samples. Negative control (`random_control`) fired on **neither**, ranks 4 and 7. The record's LM-OTS game: QFT probe measured, did **not** fire, rank 1; Simon-style probe **not run**, 0 samples | reproduced | the refusal carries its reason — that lowering leaves 1 ancilla in the predicate's codomain register, where the cancellation the probe depends on does not hold. It is recorded as *no evidence at any width*, which is a different statement from a silence, and the report writes out the difference rather than leaving it to the reader |
| §D of the campaign report says what it does not measure | reading `results/infra-2026-09-20/report.md` | — | the truth-table oracles of §A–C must not be read as hash-circuit costs | present: the section states that those oracles are lowered from a truth table, that nothing in §A–C bears on the gates-per-query term, and that the term is counted separately by `scripts/hash_oracle_cost.py` | reproduced | a report that omitted this would let a reader take a truth-table gate count for a hash cost, which is the single easiest misreading available here |
| repository content gate, this domain | `python tooling/checks/scan-forbidden.py domains/12-quantum-search-measurement` from the repository root | pinned virtual environment | nothing in this domain may carry a forbidden name, a machine path, a tracking parameter, a contact string or a secret | **files scanned: 89, findings: 0**, exit 0 — every category 0 | reproduced | run after the last edit of this build. The earlier package-style README carried a relative interpreter path in its usage block and was replaced by this build's `README.md` |

## What was not run, and why

- **The `n = 20` experiment in `results/qlwr-n20-truth_table-s20260913/`** was read, not re-run. It
  is an exact statevector over 1,048,576 amplitudes swept across an iteration range of `[0, 806]`
  with 20,000 shots; re-running it is hours, and its stored `metrics.json`, `config.yaml` and four
  figures are the evidence quoted in `README.md` §2. Its run identity — seed 20260913, `M = 1`
  measured by enumerating the search register, `k_opt = 804` — is recorded in the report itself.
- **Nothing at a width above the statevector ceiling.** An exact statevector is `2^n` complex
  amplitudes, so roughly `n = 24` is the limit on this host. Every figure above that ceiling in this
  domain is a fit and is labelled as one.
- **No error correction, no magic-state distillation, no depth budget.** The counts in §4 of
  `README.md` are logical gate counts of one explicit circuit.
- **No real quantum hardware, and no claim to have simulated one.** The domain simulates the
  algorithm exactly and classically; the scope boundary at the head of every report says so before
  any table.
- **The published SAC 2016 figures were not re-derived.** They are read from the payload's
  `published` block, which names its source, and are printed beside the counted figures so a reader
  can compare rather than take either on trust.
- **Nothing was written to or read from the read-only research tree.** Both campaign re-runs wrote
  to a scratch directory outside this repository; no file under `results/` was modified by this
  build.
