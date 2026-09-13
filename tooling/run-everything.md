# Running the repository

The ordered recipe for re-running every check in this repository, with the directory to run it from,
the recorded runtime, and the pass criterion.

**Where the times come from.** Every figure in the runtime column is a recorded wall-clock
measurement from the verification pass that produced this repository's results — the
`wall_seconds=`, `elapsed_s` or `ELAPSED` field of the recorded run logs, whichever the layer wrote.
They are not estimates. The recording host had 12 cores (13th Gen Intel Core i7-1355U, `nproc=12`,
recorded in the Mode B prover run); a slower machine moves the formal provers and the property suite
most, and the sub-second checkers hardly at all. Where a layer was re-run during the build with a
notably different time, both figures are given.

**What "pass" means.** Three things, and a layer satisfies all of them:

1. The command exits 0.
2. Its output matches the criterion stated for it below — usually a comparison against the recorded
   result file shipped beside the script.
3. Any line that looks like a failure is read. Several scripts print deliberate `EXPECTED-FAIL` lines
   that are negative controls: they are the check working, not the check failing. Conversely, an
   `OK (skipped=N)` line is not a pass — something that should have run did not, and the recorded
   baseline contains at least one such case.

Nothing in this repository reports a pass for a tool it could not run. A missing formal tool prints
`NOT RUN` with the reason; a missing Python package makes the layer stop or skip, and the logs say
which.

---

## 0. Before the first run

```sh
export PQT_SRC=/path/to/research-tree
source tooling/activate.sh
python3 -V                 # expect 3.12.3 or the same minor version
```

Both lines are needed, in that order: an assignment written on the same line as `source` is undone
when that command returns, and the mistake is quiet rather than loud, because a step whose harness
finds `PQT_SRC` unset reports itself `NOT RUN` instead of failing. `echo "$PQT_SRC"` shows which
state you are in.

Then, once, if you intend to run the audit stack's primitives layer: that layer resolves liboqs two
directories above itself — `primitives/../..` — and in this repository that is the `domains/`
directory, not the repository root. Create the compatibility directory and link from the repository
root:

```sh
mkdir -p tooling/tools/liboqs-0.16.0/build
ln -s ../../../src/liboqs/build/lib tooling/tools/liboqs-0.16.0/build/lib
printf '%s\n' '5a1a854b0dc9f2141bdc771c555ee60c37950183 tag 0.16.0' \
      > tooling/tools/liboqs-0.16.0/COMMIT.txt
ln -s ../tooling/tools domains/tools
```

`environment.md` §6 explains what those files must contain. Everything else in the tree finds its
inputs through `PQT_SRC` or through paths relative to its own directory, and needs no further setup.

## 1. The quick layers

These are the checks to run first. With one exception their whole set is seconds of work, and a
failure in them means a later, slower layer's output cannot be trusted to mean anything. The
exception is the audit stack's mathematics layer, which takes about three and a half minutes on the
host profile and is listed here rather than below because it is the last step before the formal
provers and everything after it is minutes long.

### Domain 01 — accountable quorum foundations

- **Directory:** `domains/01-accountable-quorum-foundations`
- **Command:** `python3 src/pqaqc_finite_state_check.py`
- **Recorded runtime:** 0.7 s (the superseded revision in `history/`, v0.6, takes 0.29 s)
- **Pass criterion:** exit 0, and the `COMPARE vs pqaqc_modelcheck_v0_7_results.txt (lines 15,28):
  IDENTICAL` line reports `IDENTICAL`. The `EXPECTED-FAIL ..._MUTANT` lines are negative controls.
- **Not run:** `formal/epoch-barrier.tla`. The invariants it states were checked by an independent
  enumeration script, not by the TLA+ model checker, which is not installed here.

### Domain 02 — CE-QS construction evolution

- **Directory:** `domains/02-ceqs-construction-evolution`
- **Command:** for each checker, `python3 src/<checker>.py`, then compare with its recorded file —
  for example `diff <(python3 src/ce_qs_quorum_family_checker.py) results/ce_qs_quorum_family_checker.txt`.
  The shipped checkers no longer print a comparison line themselves; the diff is the check.
- **Recorded runtimes:** `ce_qs_quorum_family_checker` 0.11 s; `ce_qs_bitmap_policy_checker` 0.11 s;
  `ce_qs_private_wrapper_relation_checker` 0.11 s; `ce_qs_relation_mock` 0.12 s;
  `ce_qs_relation_mock_ext` 3.05 s; `ce_qs_trace_tag_simulator` 0.83 s (its v0.1 predecessor in
  `history/`, 0.44 s). The remaining checkers in `src/` follow the same shape — run with no
  arguments, one table of `PASS`/`EXPECTED-FAIL` lines per configuration.
- **Pass criterion:** exit 0, output identical to the file in `results/` of the same name, and every
  line either `PASS` or an intentional `EXPECTED-FAIL` negative control.
- **Note on randomness:** the current `domains/02-ceqs-construction-evolution/src/ce_qs_trace_tag_simulator.py` (v0.2) seeds all of its
  randomness, including key material, so it is byte-for-byte reproducible and the diff above is a
  real check. The superseded **v0.1** revision in `history/` is the one that is not: it draws
  quorums from an unseeded generator, and its recorded `minimum observed quorum intersection=26`
  yields 24, 25 or 26 across runs. The bound that same line quotes (`f + 1 = 22`) is unaffected, and
  no later version depends on the line — but do not read a v0.1 difference as a defect, and do not
  read a v0.1 match as evidence. `domains/02-…/README.md` states this at the top of the domain.

### Domain 03 — proof-carrier experiments

- **Directory:** `domains/03-zk-carrier-experiments`
- **Command:** `sh src/reproduce.sh`
- **Recorded runtime:** the component that dominates this script measured 1.64 s end to end, of which
  1.45 s is cryptography (`results/authorization-evidence.json`); no separate wall time is recorded
  for the `reproduce.sh` wrapper itself, and the other steps of the script are sub-second.
- **Pass criterion:** exit 0 and all 51 component checks passing. The script first checks that the
  pinned `pqcrypto` is importable (see `packages.md`), replays the retained transparent signature
  audit, and runs the checks with freshly generated synthetic keys.
- **Note:** the decisive result of this domain is a negative control, not a pass line: the
  signature-only audit **accepts** a body with an incorrect trace mask while the full witness
  predicate rejects it. Read it in the output rather than in the exit status.
- **Historical replays** live under `history/` and are separate; the current relation does not
  supersede their claims or inherit from them.

### Domain 04 — operator ledger

- **Directory:** `domains/04-operator-ledger`
- **Command:** `python3 src/operator_ledger_checks.py > /tmp/observed.json; diff results/operator_ledger_checks.json /tmp/observed.json`
- **Recorded runtime:** 0.07–0.10 s.
- **Pass criterion:** an empty `diff` against the recorded JSON, 23 test groups at `PASS`, and
  `"full_QPT128_established": false`. That last field is the result, not a defect: the ledger's own
  checker does not establish the target, and a run that reported it as established would not be
  reproducing this record.
- **Same script, second interpreter:** the domain also runs it under Python 3.13 and gets the same
  output, which is its independence check on the interpreter. The domain's `VERIFICATION.md` records
  one prior figure it does **not** reproduce — an amendment count of 113, measured here as 101 (106
  on the stricter reading) — so read that file before comparing counts against an earlier record.

### Domain 06 — QPT-128 security target

- **Directory:** `domains/06-qpt128-security-target`
- **Commands:** `python3 src/qpt128_finalization.py --self-test` then `--report`
- **Recorded runtimes:** self-test 0.20 s (19 tests), `--report` 0.21 s
- **Pass criterion:** `Ran 19 tests` with `OK`; then a report whose L1 block records the target as
  *refuted as stated* and restated as D1/D2 with gate accounting. That refutation is the recorded
  result — a run that reports the target as established would not be reproducing this repository.

### Domain 05 — extraction and signature reductions

- **Directory:** `domains/05-extraction-and-signature-reductions`
- **Commands:** each script takes `--self-test`, and one of `--report` / `--explain` / `--json`
  (bare invocations exit 2 with the required-argument message, as the baseline logs show).
- **Recorded runtimes:** `joint_extractor_lift` 0.095 s self-test; `ceqs29_extractor` 0.83 s
  self-test (20 tests) and 0.14 s for `--certificate`; `circuit_witness_extractor` 0.196 s
  self-test (27 tests); `signature_security_reduction` 0.28 s (23 tests);
  `slh_dsa_signature_reduction` 0.30 s (36 tests); `signature_margin_sweep` 0.21 s (13 tests);
  `phase_ghz_security_check` 0.33 s (12 tests); `hybrid_sampling_bound_audit` 0.16 s;
  `slh_tree_conditioning_audit` 0.16 s. The `signature_margin_sweep` JSON run is the largest
  output in the tree (about 20,000 lines) and is still only a scenario table.
- **Pass criterion:** `OK` from each self-test. For the report-only scripts the criterion is the
  recorded boundary statement, not a pass line: `hybrid_sampling_bound_audit` ends
  `No sampling endpoint is substituted for epsilon_SLH.` and `slh_tree_conditioning_audit` reports
  `SLH TREE CONDITIONAL LIMIT: UNESTABLISHED`. Those are the results.

### Domain 07 — compact certificate, profile B0

- **Directory:** `domains/07-compact-certificate-b0`
- **Commands:** `python3 src/sidecar_free_certificate.py --self-test`, then `--report`, then
  `--real-demo` (the last one needs the environment sourced).
- **Recorded runtimes:** self-test 0.19 s (39 tests; re-run 0.18–0.19 s); `--report` 0.10 s;
  `--real-demo` 13.7 s in the baseline, 19.8–24.0 s on re-run (host load; identical numbers).
- **Pass criterion:** `Ran 39 tests` with `OK`; for `--real-demo`, the measured table plus
  `"real_demo": "available"`. Run without the environment, the same command exits 1 with
  `{"real_demo": "unavailable", "reason": ...}` — a documented outcome, and the file
  `results/real-demo-unavailable.json` is the recorded instance of it.
- **Note:** two fields differ from the recorded baseline in the shipped `results/` files (a module
  name changed by the file rename, and nothing else). The domain's own `results/README.md` states
  them; read it before calling a difference a discrepancy.

### Domain 10 — digital infrastructure, the quick half

- **Directory:** `domains/10-digital-infrastructure`
- **Commands:** `python3 src/<script>.py --self-test` then `--report`, for each of
  `domains/10-digital-infrastructure/src/s1s2_hashsig_dnssec.py`, `domains/10-digital-infrastructure/src/s3_tls_pki.py`, `domains/10-digital-infrastructure/src/s4_embedded_broadcast.py`, `domains/10-digital-infrastructure/src/s5_smartcard_hsm.py`,
  `domains/10-digital-infrastructure/src/s6_migration_agility.py`, `domains/10-digital-infrastructure/src/s3_tls_wire.py`, `domains/10-digital-infrastructure/src/s4_tesla_adversarial.py`, `domains/10-digital-infrastructure/src/s6_hybrid_games.py`.
- **Recorded runtimes (self-test / report):** `s1s2_hashsig_dnssec` 0.57 / 0.88 s;
  `s3_tls_pki` 0.14 / 0.13 s; `s4_embedded_broadcast` 0.15 / 0.10 s; `s5_smartcard_hsm` 4.85 / 27.69 s;
  `s6_migration_agility` 0.17 / 0.16 s; `s3_tls_wire` 0.95 / 0.53 s;
  `s4_tesla_adversarial` 1.03 / 0.60 s; `s6_hybrid_games` 5.39 / 5.69 s.
- **Pass criterion:** `Ran N tests` with `OK`, then a report. Several of these reports exist to
  record that a claim was corrected rather than confirmed — `s5_bds_faults` re-measures four v2.0
  claims and corrects two of them, and `s6_hybrid_games` returns `null` for the composed bound by
  design, because a union bound across two attacker goals is not defined. Take those as the pass
  criterion for those rows.
- **Note:** a bare invocation of any of these exits 2 with an argparse message; that is the recorded
  behaviour of the baseline runs too.

### Domain 11 — audit stack, the quick layers

- **Directory:** `domains/11-independent-audit-stack`
- **Commands and recorded runtimes:** `python3 math/math_layer.py` — about three and a half minutes on
  the host profile (the tree holds two recorded host figures for the same layer, 217.2 s in
  `math/math_run.log` and 211.4 s in the `_meta` block of `math/math_results.json`; both are real
  runs, and a re-run overwrites the JSON) and 102.8 s under the container profile (both 8/8 groups
  reproduced); `python3 formal/bounded_checker.py`
  (ends `RESULT: all rows ok`); `python3 independent-b0/b0_indep.py` (`self-test ok` plus a
  configuration digest); `python3 independent-b0/check_vectors.py` 19.4 s (6701 comparisons, 0
  failures, output identical to the archived results).
- **`bash run_all.sh`** runs all the layers in order and writes `run_all.log` next to it. Read that
  file: the console summary gives one exit code per step, and the log holds the output. The recorded
  baseline of the full stack shows one step as `NOT RUN` (ProVerif was not on `PATH` at that moment)
  and everything else at exit 0.
- **Pass criterion:** per layer, as above; for the stack as a whole, every step exit 0 except steps
  recorded as `NOT RUN` for a stated reason.

---

## 2. The slow layers (minutes to tens of minutes)

Run these last, and run them one at a time: they are the ones where a wrong result would be expensive
to discover at the end.

### Domain 11 — the formal provers

- **Tamarin:** `tamarin-prover --prove formal/qpt128_quorum.spthy`, from
  `domains/11-independent-audit-stack`.
  **Recorded runtime: 111 s**, exit 0, all twelve lemmas verified.
- **Tamarin, larger instantiation:** `formal/qpt128_quorum_n7.spthy`.
  **This does not finish.** The recorded batch run was stopped at **1,200 s**; a per-lemma run gets
  five lemmas verified in 116–156 s each and leaves four with no result, most after timeouts of
  266–420 s. Record it as a gap, which is what the repository records.
- **Per-lemma script:** `formal/perlemma_n7_8g/run.sh` reproduces the per-lemma attempt;
  `formal/gen_n7_votes.py` generates its input. Read `formal/FINDINGS.md` alongside the results.
- **ProVerif:** `proverif formal/qpt128_quorum.pv`. No runtime is recorded for this repository's
  models: the baseline full-stack run shows `ProVerif NOT RUN (proverif not on PATH)`. With ProVerif
  installed, run it and record what you observe; the installation check is the distribution example
  named in `environment.md` §9, not the project model.
- **If a prover is absent**, `run_all.sh` prints `NOT RUN` with the tool name. Never treat that as a
  pass.

### Domain 11 — the property suite

- **Command:** `bash property/run_all.sh` (it invokes `python3 -m pytest` per file and writes one log
  per file into `property/logs/`).
- **Recorded runtimes and outcomes:** `tesla` 2.61 s, 8 passed, 2 xfailed; `b0` 6.56 s, 12 passed;
  `differential_b0` 2,200 pairs with 0 disagreements; `hashsig` 22.47 s, 5 failed and 11 passed;
  `modeB` 110.09 s (1 min 50 s), 2 failed and 14 passed.
- **Pass criterion:** read it file by file. Two of the five files record genuine failures — the
  hash-signature suite finds malformed proofs being accepted, and the Mode B suite finds a malformed
  catalogue accepted. Those findings are part of the repository's result and are reproduced by
  reading the logs, not by a green exit code. `property/FINDINGS.md` states them.
- **Re-run note:** the two `fixes/property_fixed/` files are the patched variants of the failing
  suites, with their own logs. They run the same way.

### Domain 11 — implementation layers

- **Commands:** `implementation/run_sanitizers.sh`, `implementation/run_fuzz.sh`,
  `implementation/run_asan_production.sh`, `implementation/production/run_production.sh`,
  `implementation/build.sh`.
- **Status: not re-run during the verification pass.** The recorded results are in
  `implementation/IMPLEMENTATION_RESULTS.md` and `implementation/production/PRODUCTION_RESULTS.md`.
  They need clang with the sanitizer and libFuzzer runtimes; at production parameters one recorded
  run timed out. Treat these as recorded results you can re-attempt, not as a step this recipe
  promises to complete in a stated time.

### Domain 11 — the primitives cross-check

- **Command:** `python3 primitives/cross_validate.py`
- **Recorded runtime:** 24.7 s.
- **Status: it needs five NIST ACVP vector files that are not shipped here.**
  `primitives/vectors/SOURCE.txt` records the upstream commit and the SHA-256 of each of the five
  files. Fetch them, verify the digests, put them beside that file, and the layer reproduces the
  recorded cross-validation of liboqs against dilithium-py, kyber-py and the vectors. Without them
  the layer cannot complete, and the honest entry is `not-run`.

### Domain 09 — security games and attack lab

- **Directory:** `domains/09-security-games-and-attack-lab`
- **Commands:** `python3 src/ceqs_games.py --all` and `python3 src/ceqs_attack_lab.py --all`
  (`--self-test` for each is the quick variant).
- **Recorded runtimes:** games `--self-test` 2.5 s (4 tests) and `--all` **126.1 s**;
  attack lab `--self-test` 1.7 s (5 tests) and `--all` **54.5 s**.
- **Pass criterion:** for the attack lab, `Successful violations: 0 of 24 attempts` — recorded
  together with its own caveat that the parameters are toys and the measurement tests the *scaling*
  of the attacks, not the production security level. For the games, the summary of measured against
  theoretical slopes, with the fitted-extrapolation note that the fitted figure departs from the
  exact one by a stated number of bits.
- **Note:** both scripts load the D8 v1.50 revision by filename from their own directory; if a run
  stops at import with a missing-file error naming `hidden_signer_modeB_v1.50.py`, that path is the
  thing to check (`imports.md` has the detail).

### Domain 10 — the long half

- **`domains/10-digital-infrastructure/src/s5_bds_faults.py --report`: recorded 92.1 s** (self-test 20.5 s). It re-measures four v2.0
  claims and records one confirmed, one higher than claimed during the run (664 B end state, 828 B
  peak), one too low (86,720 → 95,775 leaf computations in the worst round), and one size claim that
  becomes 2.1 KB at h=20 rather than the claimed "< 2 KB".
- **`domains/10-digital-infrastructure/src/s1_lms.py --self-test`: recorded 3.4 s**, `OK (skipped=2)`. **Read the skips.** The two skipped
  tests are the independent-implementation differential, skipped when `hsslms` is absent. In the
  environment of this repository it is present, so a re-run should show them *running* rather than
  skipped — a difference from the recorded baseline that is about availability only.
- **`domains/10-digital-infrastructure/src/audit_ledger.py`: recorded 222.0 s** — the single longest Python run in the repository. It
  runs every S1–S6 suite's self-test and reads their report JSON, then writes the checklist and the
  ledger into `domains/10-digital-infrastructure/results/`. Its recorded outcome was
  `61/64 tests pass; suites: S1:FAIL, S2:FAIL, S3:ALL, S4:ALL, S5:ALL, S6:ALL` — the two failing
  suites are the hsslms skip and the dnspython import failure. Expect the same figure to change once
  both packages are present, and report what you observe rather than the recorded number.
- **`domains/10-digital-infrastructure/src/s2_dns_worstcase.py`** died at its import line in the baseline (`No module named 'dns'`), so it
  has **no recorded runtime and no recorded result**. With `dnspython` installed it runs; whatever it
  reports will be the first result of that layer here.

### Domain 08 — hidden signers

- **Directory:** `domains/08-hidden-signers`
- **Commands and recorded runtimes:**
  - `python3 src/hidden_signer_mode_a.py --self-test` 2.1 s (8 tests); `--report` 0.1 s
  - `python3 src/hidden_signer_mode_b.py --self-test` 6.6 s (7 tests in v1.51; the v1.46 revision in
    `history/` takes 5.4 s for 12 tests)
  - `python3 src/mode_b_rigorous_ledger.py --self-test` 0.1 s (7 tests); `--report` 0.1 s
  - `python3 src/mode_b_voleith_toy.py --self-test` **58.8 s** (7 tests); `--run` **56.8 s**
  - the v1.46 revision's heavier modes, if you want them: `--demo-256` **72.1 s**,
    `--recompute-security` 9.3 s
  - the C prover: `gcc -O3 -march=native -fopenmp -Wall -o mode_b_prover src/mode_b_prover.c`, then
    `./mode_b_prover --vectors` (no recorded wall time) and
    `./mode_b_prover --run --b 12 --tau 20 --wg 8 --rho 1024` — recorded **6.4 s** for v1.51
    (11.9 s for v1.49, 7.4 s for v1.50).
- **Pass criterion:** `OK` from each self-test, and for the C prover a JSON record with
  `"verified":[true,true]`, `"tampered_rejected":true` and `extracted_count` as recorded. The
  `--run` invocations are documented smoke parameters and report `"fits_32768": false` — that is the
  expected shape of those runs, not a failure.
- **Note:** the C prover is compiled with `-march=native`. The recorded sizes come from the binary
  built that way; a different CPU gives a different binary and can give slightly different timings
  while the JSON fields stay the same.

---

## 3. Order, and what to expect

| # | Where | Command | Recorded | Verdict shape |
|---|---|---|---|---|
| 1 | `domains/01-accountable-quorum-foundations` | `python3 src/pqaqc_finite_state_check.py` | 0.7 s | comparison `IDENTICAL` |
| 2 | `domains/02-ceqs-construction-evolution` | `python3 src/<checker>.py`, diff against `results/` | 0.1–3.1 s each | every line `PASS` / `EXPECTED-FAIL` |
| 3 | `domains/03-zk-carrier-experiments` | `sh src/reproduce.sh` | 1.6 s | 51 checks pass |
| 4 | `domains/05-extraction-and-signature-reductions` | `python3 src/<script>.py --self-test` | 0.1–0.8 s each | `OK` |
| 5 | `domains/06-qpt128-security-target` | `python3 src/qpt128_finalization.py --self-test` | 0.2 s | `OK`, 19 tests |
| 6 | `domains/07-compact-certificate-b0` | `--self-test`, `--report` | 0.2 s, 0.1 s | `OK`, 39 tests |
| 7 | `domains/07-compact-certificate-b0` | `--real-demo` (environment sourced) | 13.7 s | `"real_demo": "available"` |
| 8 | `domains/10-digital-infrastructure` | `python3 src/<script>.py --self-test` | 0.1–5.4 s each | `OK` |
| 9 | `domains/10-digital-infrastructure` | `python3 src/<script>.py --report` | 0.1–27.7 s each | recorded report |
| 10 | `domains/11-independent-audit-stack` | `python3 math/math_layer.py` | 211–217 s host / 103 s container | 8/8 `REPRODUCED` |
| 11 | `domains/11-independent-audit-stack` | `python3 formal/bounded_checker.py` | fast | `RESULT: all rows ok` |
| 12 | `domains/11-independent-audit-stack` | `python3 independent-b0/check_vectors.py` | 19.4 s | 6701 comparisons, 0 failures |
| 13 | `domains/11-independent-audit-stack` | `python3 fault/fault_injection.py` | fast | 300 schedules, 0 failures |
| 14 | `domains/11-independent-audit-stack` | `bash property/run_all.sh` | 2.6–110 s per file | read per file; two files record failures |
| 15 | `domains/11-independent-audit-stack` | `tamarin-prover --prove formal/qpt128_quorum.spthy` | **111 s** | 12 lemmas verified |
| 16 | `domains/11-independent-audit-stack` | `proverif formal/qpt128_quorum.pv` | not recorded (was `NOT RUN`) | model-dependent |
| 17 | `domains/09-security-games-and-attack-lab` | `python3 src/ceqs_attack_lab.py --all` | **54.5 s** | 0 successful violations of 24 |
| 18 | `domains/09-security-games-and-attack-lab` | `python3 src/ceqs_games.py --all` | **126.1 s** | measured vs theoretical slopes |
| 19 | `domains/08-hidden-signers` | `python3 src/mode_b_*` as above | 0.1–72 s | `OK` per self-test |
| 20 | `domains/10-digital-infrastructure` | `python3 src/s5_bds_faults.py --report` | **92.1 s** | corrected claims |
| 21 | `domains/10-digital-infrastructure` | `python3 src/audit_ledger.py` | **222.0 s** | checklist + ledger written |
| 22 | `domains/11-independent-audit-stack` | `bash run_all.sh` | ~3.5 min + prover time | one step was `NOT RUN` |

**Expected to be slow:** the formal provers (111 s for the main Tamarin model; the larger one does
not finish inside 1,200 s), the property suite's Mode B file (110 s), the mathematics layer (~3.5 min
on the host profile), the audit ledger (222 s), and the two domain 09 `--all` runs (55 s and 126 s).
Everything else is under half a minute except the hidden-signer toy and the v1.46 prover demos, which
reach 72 s at their heaviest parameters, and most of the rest is under a second.

**Expected to be unavailable, and why**, in one place:

| Layer | Why |
|---|---|
| TLA+/TLC invariants | no `tla2tools.jar` and no pinned Java here; checked instead by an independent enumeration script |
| EasyCrypt (`formal/frame_b0.ec`) | EasyCrypt not installed; the file is an `admit`ted skeleton and was never checked |
| ACVP primitives cross-check | the five vector files are not shipped; fetch them by the digests in `vectors/SOURCE.txt` |
| Tamarin on the N=7 instantiation | does not terminate within the recorded 1,200 s batch budget; per-lemma run leaves four lemmas with no result |
| Sanitizer and fuzz layers | not re-run during verification; recorded results only (clang is present, the runs are long, and one timed out at production parameters) |
| CryptoMiniSat experiments | never run here; no recorded version |
| Binius64 adapter sizes | the recorded binaries contain AVX-512 instructions and were not executed on this host; rebuilding changes their digests |
| Docker-based realisation | `Dockerfile.math` was built and run (8/8 reproduced); the full-stack `Dockerfile` was never built |
| SageMath paths | not installed, and the mathematics layer has no Sage code path — installing it would change nothing |
