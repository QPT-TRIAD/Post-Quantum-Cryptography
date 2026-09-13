# Verification

Every suite in `domains/10-digital-infrastructure/` was re-run in the pinned environment and compared
against the programme's recorded result. This document gives the command, the environment, the
recorded value, the observed value, the verdict and the notes for each item. Where a re-run
disagreed with the record, **both values are kept** and the difference is stated.

Verdicts are one of `reproduced`, `reproduced-with-difference`, `not-reproducible`, `not-run`.

---

## Environment

| | |
|---|---|
| interpreter | Python **3.12.3** |
| environment | the pinned Python environment, activated by `tooling/activate.sh` before every command; that script selects the environment's interpreter and sets `PYTHONDONTWRITEBYTECODE=1` |
| packages needed by this domain | `numpy` **2.4.6**, `dnspython` **2.8.0**, `hsslms` **0.1.3** |
| packages needed by nothing in this domain | `cryptography` 46.0.0, `galois` 0.4.11, `sympy` 1.13.1, `kyber-py` 1.2.0, `dilithium-py` 1.4.0, `pqcrypto` 0.3.4, `liboqs-python` 0.16.0, `hypothesis` 6.151.9, `pytest` 9.0.2 — pinned for the programme, imported by no D10 file; see `docs/packages.md` |
| host | one x86-64 host; runtimes below are from it and are not portable |
| date | 2026-09-13 |

Two interfaces, and there are no others. Every model and audit script takes exactly one of
`--self-test` (run its unittest suite) or `--report` (print its JSON report). `src/audit_ledger.py`
takes `--refresh`.

```sh
. tooling/activate.sh
cd domains/10-digital-infrastructure

# the whole audit ledger: runs S1–S6 --self-test, then each --report, then writes
# results/AUDIT_CHECKLIST_v2.1.md and results/AUDIT_LEDGER_v2.1.json
time python3 src/audit_ledger.py --refresh

# any single suite
python3 src/s1_lms.py --self-test
python3 history/s1_lms-v2.1.py --self-test
python3 src/s2_dns_worstcase.py --self-test
python3 src/s3_tls_wire.py --self-test
python3 src/s4_tesla_adversarial.py --self-test
python3 src/s5_bds_faults.py --self-test
python3 src/s6_hybrid_games.py --self-test

# the six design models (not part of the ledger's 70)
python3 src/s1s2_hashsig_dnssec.py --self-test
python3 src/s1s2_hashsig_dnssec-v2.0.py --self-test
python3 src/s3_tls_pki.py --self-test
python3 src/s4_embedded_broadcast.py --self-test
python3 src/s5_smartcard_hsm.py --self-test
python3 src/s6_migration_agility.py --self-test
```

---

## 1. Result of the ledger, and the sentence that must travel with it

The ledger was run end to end **twice**, independently, and both runs completed with

```
70/70 tests pass; suites: S1:ALL, S2:ALL, S3:ALL, S4:ALL, S5:ALL, S6:ALL
```

| run | command | wall time | result |
|---|---|---|---|
| 1 | `python3 src/audit_ledger.py --refresh` | 7m29.8s (user 7m29.2s, sys 0.4s) | 70/70, exit 0 |
| 2 | `python3 src/audit_ledger.py --refresh` | 12m57.8s (user 11m18.1s, sys 0.9s) | 70/70, exit 0 |

The recorded result is the same line, 70/70. The two wall times differ by 5m28s and are not a
discrepancy: they are wall-clock times on a shared host, taken while other work was running on it, and
the per-suite timings inside them moved in both directions (§3).

**This total is not a stable reproduction, and it must not be reported as one.** It came out on runs
where the S1-011 slope statistic landed right. The statistic itself is flaky at a measured rate of
approximately one half: the programme measured 98 of 200 single draws satisfying it (49.0 %), and the
re-measurement for this repository got 108 of 200 (54.0 %). The test has since been rewritten to
assert the slope on the median of 41 draws rather than on one draw (§4), and **the rewritten test
passed in every run performed for this repository, including both full ledger runs** — but a median is
not a guarantee, the flakiness is reduced and measured rather than eliminated, and the Grover-law
statement in this domain remains a **simulation**, not a measurement and not a proof.

The earlier of the two runs is kept as evidence in the build evidence directory (`ledger_run1/`,
`logs_d10_ledger_run.txt`). The later one is what `results/` holds, so the regenerated files on
disk and the diff in §5 below are both from a completed run.

---

## 2. The required table

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| Ledger, all six suites | `python3 src/audit_ledger.py --refresh` | pinned venv, Py 3.12.3 | `70/70 tests pass; suites: S1:ALL, S2:ALL, S3:ALL, S4:ALL, S5:ALL, S6:ALL` | the same line, exit 0, 7m29.8s | **reproduced** | see §1: not a stable reproduction — read with the S1-011 sentence |
| S1 as the ledger runs it (`history/s1_lms-v2.1.py`) | `python3 history/s1_lms-v2.1.py --self-test` | pinned venv + `numpy` 2.4.6 + `hsslms` 0.1.3 | 11 tests, ALL PASS | `Ran 11 tests in 16.615s` … `OK` | **reproduced** | includes the two `hsslms` interop tests, both PASS |
| S2 | `python3 src/s2_dns_worstcase.py --self-test` | pinned venv + `dnspython` 2.8.0 | 6 tests, ALL PASS | `Ran 6 tests in 54.848s` … `OK` | **reproduced** | |
| S3 | `python3 src/s3_tls_wire.py --self-test` | pinned venv | 20 tests, ALL PASS | `Ran 20 tests in 0.972s` … `OK` | **reproduced** | |
| S4 | `python3 src/s4_tesla_adversarial.py --self-test` | pinned venv | 14 tests, ALL PASS | `Ran 14 tests in 2.158s` … `OK` | **reproduced** | |
| S5 | `python3 src/s5_bds_faults.py --self-test` | pinned venv | 5 tests, ALL PASS | `Ran 5 tests in 48.669s` … `OK` | **reproduced** | |
| S6 | `python3 src/s6_hybrid_games.py --self-test` | pinned venv | 14 tests, ALL PASS | `Ran 14 tests in 11.535s` … `OK` | **reproduced** | |
| S1 model, current revision | `python3 src/s1_lms.py --self-test` | pinned venv + `numpy` + `hsslms` | not in the ledger; 12 tests (11 + the v2.2 F3 regression S1-012) | `Ran 12 tests in 23.405s` … `OK` | **reproduced** | v2.2 revision; not one of the 70 |
| S1/S2 design model, v2.2 | `python3 src/s1s2_hashsig_dnssec.py --self-test` | pinned venv | 15 tests | `Ran 15 tests in 0.261s` … `OK` | **reproduced** | not one of the 70 |
| S1/S2 design model, v2.0 | `python3 src/s1s2_hashsig_dnssec-v2.0.py --self-test` | pinned venv | 10 tests | `Ran 10 tests in 0.240s` … `OK` | **reproduced** | the revision `src/s3_tls_pki.py` and `src/s4_embedded_broadcast.py` still load |
| S3 design model | `python3 src/s3_tls_pki.py --self-test` | pinned venv | 5 tests | `Ran 5 tests in 0.065s` … `OK` | **reproduced** | |
| S4 design model | `python3 src/s4_embedded_broadcast.py --self-test` | pinned venv | 5 tests | `Ran 5 tests in 0.047s` … `OK` | **reproduced** | |
| S5 design model | `python3 src/s5_smartcard_hsm.py --self-test` | pinned venv | 4 tests | `Ran 4 tests in 6.204s` … `OK` | **reproduced** | |
| S6 design model | `python3 src/s6_migration_agility.py --self-test` | pinned venv | 4 tests | `Ran 4 tests in 0.015s` … `OK` | **reproduced** | |
| `hsslms` interop (S1-003, S1-004) | inside the S1 suites | `hsslms` 0.1.3 installed | PASS both directions | PASS both directions; `independent_implementation: "hsslms 0.1.3"` in `results/s1_audit_report.json` | **reproduced** | byte-format agreement between two implementations of RFC 8554; not a security evaluation |
| S1-011 as recorded (single-draw slope) | `python3 history/s1_lms-v2.1.py --self-test` | pinned venv | PASS | PASS on the rewritten test; the **original** assertion is a coin flip | **reproduced-with-difference** | see §4 — this is the one recorded result that does not reproduce as stated |
| S1-011 single-draw slope frequency | re-measurement script over 200 runs | pinned venv | 98/200 = **49.0 %** | **108/200 = 54.0 %**, range 0.3195–0.7255, median 0.5097 | **reproduced-with-difference** | the two rates are separate samples of a ≈ coin flip; pooled 205/400 ≈ 51 % |
| S1-011 median-of-41 estimator | same script, 20 trials × 41 draws | pinned venv | 20/20, range [0.4819, 0.5316] | **20/20**, range [0.4877, 0.5494] | **reproduced** | this is the estimator the rewritten test asserts |
| S1-011 median-of-5 (rejected) | same script | pinned venv | 17/20 | **15/20**, range [0.4265, 0.6244] | **reproduced-with-difference** | both confirm 5 draws is not enough; neither figure is used |
| Checklist regeneration vs the canonical record | `diff records/audit-checklist.md results/AUDIT_CHECKLIST_v2.1.md` | — | byte-identical | 7 hunks; 8 changed lines in run 1, 10 in run 2 | **reproduced-with-difference** | see §5.1 |
| Ledger regeneration vs the canonical record | `diff` of the two JSON files | — | byte-identical | 9 hunks / 39 changed lines in run 1; 11 hunks / 43 in run 2 | **reproduced-with-difference** | see §5.2; includes `model_discrepancies.S5` `null` → populated |
| CPU cycles, RAM and stack figures | none | no CPU figure is measured anywhere in this domain | literature values, several `None` | unchanged (nothing re-measured) | **not-run** | no hardware was touched; see `docs/studies.md` and `docs/packages.md` |
| Study layout | `ls src/` | — | flat `src/`, 13 files, every module a sibling; only the superseded S1/S2 model keeps a version in its filename | flat `src/`, 13 files, one version-suffixed filename | **reproduced** | see §6 |
| Forbidden-content gate (repository) | `python3 tooling/checks/scan-forbidden.py .` | — | 0 findings | **0 findings, exit 0** | **reproduced** | also run over the two byte-identical `records/` copies separately: 0 findings |

---

## 3. Timing differences

The `Ran N tests in T s` strings are the only part of the checklist that moves on every run, and they
moved in **both directions**: S1 20.051 → 9.334 s, S2 88.058 → 38.848 s, S3 1.404 → 0.670 s, S4
2.761 → 1.383 s, S5 43.451 → 22.294 s (faster), S6 5.485 → 6.634 s (slower).

These are wall-clock wall times on one host under whatever load it carried, not a measured resource
of the study. They are recorded here so that the regeneration diff is fully explained, and they are
**not** treated as results anywhere in `docs/`. The one timing figure this domain does treat as a
result — the audit ledger's own end-to-end wall time — is 7m29.8s for the run reported in §1.

---

## 4. S1-011: the one recorded result that does not reproduce as stated

**Recorded.** `records/audit-checklist.md` lists `S1-011`, `test_S1_011_grover_simulation_matches_law`,
column `bound`, status **PASS**, within a suite total of 70/70.

**What that test asserted.** Three things over `n ∈ {8, 10, 12, 14}`, running the exact state-vector
Grover simulation on the real keyed LM-OTS chain oracle:

1. `|k_measured − k_predicted| ≤ 1` — the measured first peak against the closed-form iteration count;
2. the success probability at the closed-form count, equal to its closed form to 1e-9;
3. the four-point least-squares slope of `log2(k_measured)` against `n`, within 0.06 of 0.5.

**Why (3) is a coin flip.** The simulator draws its secret with `secrets.randbelow(N)`, so the size M
of the marked set is random from run to run, and `k_measured` moves with it. Over one draw of four
sizes the regression slope therefore lands anywhere in a wide band.

**Measured, in the programme's own measurement:** the assertion holds in **98 of 200** runs
(**49.0 %**), slope range 0.268–0.726, median 0.511.

**Re-measured for this repository, 200 independent runs, importing the shipped
`src/s1_lms.py`:** the assertion holds in **108 of 200** runs (**54.0 %**), range 0.3195–0.7255,
median 0.5097, mean 0.5094.

**Both numbers are kept.** They are two independent samples of a statistic that is close to a coin
flip, and they disagree by 10 runs in 200, which is well inside sampling noise for a proportion near
a half. Pooled, 205 of 400 runs satisfy the original assertion (51.3 %). The recorded `PASS` was a
favourable draw, and the recorded `49.0 %` is itself a sample rather than a constant of the test.

**The rewrite, and what it takes to make it hold.** Test (3) is replaced by the median of the same
slope over **41 independent draws**, still asserted within 0.06 of 0.5. Assertions (1) and (2) are
kept exactly as they were — they are exact and reproduce on every run.

| estimator | recorded | observed here |
|---|---|---|
| median of 41 draws | 20/20 trials, range [0.4819, 0.5316] | **20/20**, range [0.4877, 0.5494] |
| median of 5 draws (rejected) | 17/20 | 15/20, range [0.4265, 0.6244] |

**Residual risk, stated plainly.** A median of 41 is a much better-behaved statistic than one draw,
but it is not a proof and the estimator still has a distribution. The rewritten test passed in every
run performed for this repository; that is evidence, not a guarantee. The claim label of the
Grover-law statement stays **simulation** — a state-vector simulation of a reduced instance, not a
measurement of a deployed system and not a proof.

**Evidence.** The measurement script and its full output are kept in the build evidence directory
(`S1-011-slope-measurement.txt`); the script imports the shipped module, so it measures the code that
is in this repository rather than a copy.

---

## 5. Regeneration against the programme's canonical records

`records/audit-checklist.md` and `records/audit-ledger.json` are the programme's own recorded copies,
byte-identical to the source tree. The files under `results/` were regenerated here by
`src/audit_ledger.py --refresh`. The two are compared below. Nothing in `records/` was modified.

### 5.1 Checklist: 7 hunks, 8 changed lines

| what changed | recorded | run 1 | run 2 (in `results/`) |
|---|---|---|---|
| S1 summary | `Ran 11 tests in 20.051s` | `9.334s` | `47.236s` |
| S2 summary | `Ran 6 tests in 88.058s` | `38.848s` | `92.267s` |
| S3 summary | `Ran 20 tests in 1.404s` | `0.670s` | `0.416s` |
| S4 summary | `Ran 14 tests in 2.761s` | `1.383s` | `0.912s` |
| S5 summary | `Ran 5 tests in 43.451s` | `22.294s` | `16.708s` |
| S6 summary | `Ran 14 tests in 5.485s` | `6.634s` | `9.979s` |
| S1-G2-sim-n8 draw | `k=7 (pred 7), p=0.996846` | `k=12 (pred 12), p=0.999947` | same as run 1 |
| S1-G2-sim-n10 draw | `k=17 (pred 17), p=0.999448` | `k=25 (pred 25), p=0.999461` | same as run 1 |
| S1-G2-sim-n12 draw | `k=35 (pred 35), p=0.999997` | unchanged (35) | `k=25 (pred 25), p=0.999461` |
| S1-G2-sim-n14 draw | `k=100 (pred 100), p=1.000000` | unchanged (100) | `k=50 (pred 50), p=0.999945` |

Run 1 changed 8 lines (7 hunks); run 2 changed 10 (7 hunks). This is the complete difference in both
cases. Every test ID, column, description and status is identical, in the same order, including the
`**Totals: 70/70 tests pass.**` line at line 118 in all three files. The simulator rows differ because
the marked-set size is drawn at random (the same coin as §4); it happened to coincide with the
recorded draws twice in run 1 and not at all in run 2, which is what four independent random draws
look like. In every run the measured peak equals its own prediction, which is what those rows assert.

### 5.2 Ledger: the two runs

| run | hunks | lines removed | lines added |
|---|---|---|---|
| 1 | 9 | 9 | 30 |
| 2 (in `results/`) | 11 | 11 | 32 |

The whole difference is three things, in both runs:

1. **the simulator draws** — two lines changed in run 1, four in run 2, from the same random coin as
   §5.1;
2. **the six suite `summary` timing strings**, as in §5.1;
3. **`model_discrepancies.S5`: `null` → populated**, identical in both runs. This is a difference in
   the *record*, not in the code, and it is the one worth reading.

**Why `S5` is `null` in the recorded ledger.** The recorded ledger was generated while the cached
`results/s5_audit_report.json` on that machine predated the `v2_0_claims_remeasured` block, and
`load_report()` reads the cached report rather than re-running the suite unless `--refresh` is given.
With the cache refreshed, the block is present. **Nothing was overwritten and nothing was "fixed"**:
both ledgers are kept as they are, and the difference is stated here.

The block that is present in the regenerated ledger, and absent from the record:

| v2.0 claim | v2.1 measurement | verdict as recorded |
|---|---|---|
| BDS state at h = 8, k = 2 is **664 B** | peak **828 B** | "claim was the END state; peak during the run is higher" |
| **30,466** hashes/signature at h = 8 | **30,445.5** | **confirmed** |
| maximum at h = 20 is **≤ 86,720** hashes | maximum **95,775** | "claim too low: BDS needs (h−k)/2 + 1 leaf computations in the worst round, not (h−k)/2" |
| persistent state **< 2 KB** | **2,148 B at h = 20** | "2.1 KB at h = 20" — the claim does not hold |

`model_discrepancies.S2`, `.S3` and `.S4` are **identical** between the record and the regeneration,
so the only S-level difference in the entire ledger is `S5`.

### 5.3 The repository's two gates, and this domain's place in them

Both gates were run from the repository root, after every file in this domain was final.

```
python3 tooling/checks/scan-forbidden.py .
→ files scanned: 644, findings: 0   (every category 0), exit 0

python3 tooling/checks/verify-repository.py
→ map rows: 1369 … sha256 differences: 0 (explained by rewrites: 132)
  UNEXPLAINED files: 0 … RESULT: PASS, exit 0
```

**The forbidden-content gate is clean for this domain**: 0 findings in all six categories over the
29 files of `domains/10-digital-infrastructure/`, at every run. It is clean repository-wide in the
current run as well — 0 findings over 644 files. Both counts move while files are still being written
elsewhere: one intermediate repository-wide run reported 1, a recorded traceback path in another
domain, cleared before the next run.

**The map gate fails no longer, and the failure recorded here earlier is withdrawn where it stands.**
The superseded output is kept, because this domain's share of it was measured then and is what the
following paragraph explains:

```
superseded — the same command, before records/rewrites.tsv was regenerated destination-keyed:
→ map rows: 1369 … sha256 differences: 131 (explained by rewrites: 1)
  UNEXPLAINED files: 0 … RESULT: FAIL, exit 1
```

At that run the verifier reported 131 files whose sha256 differed from the hash `records/file-map.tsv`
records for their source, **1** of them explained by `records/rewrites.tsv`, and **14** of the 131
this domain's — 14 of its 18 map rows. The table has since been regenerated with its `files` column
keyed to destination paths, which is the matching the verifier performs; the same 14 files, still the
only 14 of this domain's 18 rows that differ, are now all explained, no difference stands, and the
gate exits 0. The tool prints only the first 80 items, so the D10 rows appear in neither run's output;
the count below was measured directly, by hashing each placed file and comparing it with its map row.
No copied file in this domain changed between the two runs — the count moved because the table gained
the destination paths it needed.

| D10 files whose repo hash equals the map's source hash | 4 — `records/audit-checklist.md`, `records/audit-ledger.json`, `src/s1s2_hashsig_dnssec.py`, `src/s1s2_hashsig_dnssec-v2.0.py` |
| D10 files whose hash differs | **14**, and for each the rewrite is recorded in `records/rewrites.tsv` under the destination path the verifier matches |

The 14 are the files carrying the mandated edits: the `_PYLIB` line removals, the load strings
repointed at the flattened names, the wording scrub in the S3 CPU table and the audit document (the
phrase now reads `not verified here`), the S1-011 assertion change, and the two attribution wordings.
Every one of the 14 was diffed against its source file and every changed line falls into one of those
categories — there is no other deviation anywhere in the domain. So the differences are expected, and
at the superseded run they were nevertheless counted among the unexplained ones, for a mechanical
reason: the verifier tests each differing destination path against the `files` column of
`records/rewrites.tsv`, and that column then held **source** names (`pq_audit_ledger_v2.1.py`,
`pq_audit_s1_lms_v2.1.py`, and so on), the destinations appearing only in the reason column. The
count was reported here as observed and left to the table's owner rather than repaired here; the
table was then regenerated destination-keyed, and the current run explains all 14.

The `UNEXPLAINED files` count is 0 in both runs: the two that stood under
`domains/11-independent-audit-stack/formal/` (`proverif_output.txt`, `proverif_output_C1.txt`) were
resolved by a parallel pass before the superseded run, and none replaced them.

---

## 6. The layout, and the names the files came from

### What the layout is

Every Python file of this domain is flat in **`src/`** — thirteen files, no subdirectories, no
reference directory. They are the six suites the ledger runs (`src/s2_dns_worstcase.py`, `src/s3_tls_wire.py`,
`src/s4_tesla_adversarial.py`, `src/s5_bds_faults.py`, `src/s6_hybrid_games.py`, and `history/s1_lms-v2.1.py`),
the five design models plus the current S1 audit revision (`src/s1s2_hashsig_dnssec.py`, `src/s3_tls_pki.py`,
`src/s4_embedded_broadcast.py`, `src/s5_smartcard_hsm.py`, `src/s6_migration_agility.py`, `src/s1_lms.py`), and
`src/audit_ledger.py`.

**One file carries a version in its name:** `src/s1s2_hashsig_dnssec-v2.0.py`, the earlier revision of
`src/s1s2_hashsig_dnssec.py`, which sits beside its successor because it is still read —
`src/s3_tls_pki.py` and `src/s4_embedded_broadcast.py` each load it by filename as a cross-check oracle. The
suffix marks a file whose superseded revision is also present and still referenced; no other file in
this domain is in that position, so no other file carries one. `history/s1_lms-v2.1.py` is the one
file under `history/`: the S1 audit revision the ledger's S1 row runs, because that is the revision
the released `records/audit-ledger.json` was produced with (see `README.md`).

### The source names, where they differ

These files were migrated from a source tree whose filenames differ. The mapping is recorded in this
repository twice — `records/file-map.tsv` gives, per file, the source path and the path here, and
`records/rewrites.tsv` gives the reason for each rename. The renames are mechanical: a version suffix
that duplicated the revision marker inside the file was dropped, except where the superseded revision
is still present.

| source name | path here |
|---|---|
| `pq_audit_s1_lms_v2.1.py` | `history/s1_lms-v2.1.py` |
| `pq_audit_s1_lms_v2.2.py` | `src/s1_lms.py` |
| `pq_audit_s2_dns_worstcase_v2.1.py` | `src/s2_dns_worstcase.py` |
| `pq_audit_s3_tls_wire_v2.1.py` | `src/s3_tls_wire.py` |
| `pq_audit_s4_tesla_adversarial_v2.1.py` | `src/s4_tesla_adversarial.py` |
| `pq_audit_s5_bds_faults_v2.1.py` | `src/s5_bds_faults.py` |
| `pq_audit_s6_hybrid_games_v2.1.py` | `src/s6_hybrid_games.py` |
| `pq_audit_ledger_v2.1.py` | `src/audit_ledger.py` |
| `pq_infra_s1s2_hashsig_dnssec_v2.0.py` | `src/s1s2_hashsig_dnssec-v2.0.py` |
| `pq_infra_s1s2_hashsig_dnssec_v2.2.py` | `src/s1s2_hashsig_dnssec.py` |
| `pq_infra_s3_tls_pki_v2.0.py` | `src/s3_tls_pki.py` |
| `pq_infra_s4_embedded_broadcast_v2.0.py` | `src/s4_embedded_broadcast.py` |
| `pq_infra_s5_smartcard_hsm_v2.0.py` | `src/s5_smartcard_hsm.py` |
| `pq_infra_s6_migration_agility_v2.0.py` | `src/s6_migration_agility.py` |
| `pq_infra_program_v2.0.md` | `docs/pq-infra-program.md` |
| `pq_infra_audit_v2.1.md` | `docs/pq-infra-audit.md` |
| `AUDIT_CHECKLIST_v2.1.md` | `records/audit-checklist.md` |
| `AUDIT_LEDGER_v2.1.json` | `records/audit-ledger.json` |

### Why it is safe

Every cross-module load in this domain is built from the importing file's own directory:

```python
importlib.util.spec_from_file_location(name, os.path.join(_HERE, '<filename>'))
```

`_HERE` is the directory of the file doing the loading, so the modules only have to be **siblings** of
each other, and this is the only constraint the loaders impose. The flat `src/` satisfies it for every
loader — including the two loaders that pull `src/s1s2_hashsig_dnssec-v2.0.py` in, and the ledger's own
load of `history/s1_lms-v2.1.py` through a `..` path. Each load string was rewritten and then
confirmed by re-running the whole ledger (70/70, two independent runs) and every individual suite.

### What changed because of it

The load strings, and nothing else. No measurement, no report field and no test result depends on a
path; the two independent ledger runs and the thirteen individual suites all pass at the changed
strings, and `results/AUDIT_CHECKLIST_v2.1.md` is identical to the recorded checklist apart from
timings and the two random draws (§5.1).

---

## 7. What was not run, and why

- **No CPU, RAM or stack figure was re-measured.** Every cycle count, RAM budget and stack figure in
  this domain is cited from the literature, and several are `None` because no number was verified for
  that primitive. No hardware — no card, no secure element, no HSM, no radio, no server — was
  touched.
- **No network was involved.** The TLS, QUIC, DNS and broadcast results are byte encodings and models;
  nothing was sent.
- **The full 2^20 signature window for S5 was not walked.** The h = 18 and h = 20 peak-state figures
  are measured on a 2^15-signature prefix window, as the source states.
- **The reduced-size experiments were not extended.** They run at n ≤ 16 bits by construction; raising
  n would not make them a measurement of the deployed parameters, it would just make them slower.
- **The multi-target fix was not applied to the design files.** `prefixed_multiproof_build` /
  `prefixed_multiproof_verify` exist inside the S2 audit file only. Editing the design files was out of
  scope for this domain, and the exposure is flagged in `README.md` and `docs/studies.md` §2.6 rather
  than quietly repaired.
- **The S4 receiver fixes were not applied to the design file.** They exist only in the audit's
  `FixedTeslaReceiver` subclass, as the source intends.
- **Nothing under the read-only source tree was created, modified or deleted.** The build writes only
  inside `domains/10-digital-infrastructure/` and `records/`; the canonical `records/` copies were
  written once as byte-identical copies and have not been edited since.
