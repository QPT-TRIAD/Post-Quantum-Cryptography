# VERIFICATION — docs/04-security-and-validation

Every command this package re-ran, the recorded baseline it was compared against, what was observed,
and the verdict. Commands are written relative to the repository root. The environment for every row
was the pinned reproduction environment, activated before the command:

```
. <work-dir>/env/activate.sh
```

which pins the interpreter (Python 3.12.3 for every row below) and sets `PYTHONDONTWRITEBYTECODE=1`,
so nothing run from the read-only source tree can write bytecode into it.

Verdicts are one of `reproduced`, `reproduced-with-difference`, `not-reproducible`, `not-run`.

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| read-only source tree untouched | `python3 tools/check_pqt_baseline.py` (build work tree) | Python 3.12.3 | 1,157 baseline files, 0 changed / added / removed | 1,157 present; size changed 0; mtime changed 0; added 0; removed 0; `RESULT: PASS -- source tree unmodified`; 0.27 s | reproduced | covers every run this package made from the source tree, including the two `--all` suites: no `__pycache__` was written and no file changed |
| placed attack-lab source bytes | `sha256sum domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py` | — | the map records `78c9b204…` for `ceqs_attack_lab_v1.51.py` | `7df54f12adb92b9ad39ab5aea40999a5cfda1d1becbb3c76d3c453ad1f21ac2e` | reproduced-with-difference | the placed file is the copy with repository-relative paths substituted, so its digest must differ from the source tree's. What is verified is that the placed copy runs (rows below), not that the bytes are the source's |
| placed games source bytes | `sha256sum domains/09-security-games-and-attack-lab/src/ceqs_games.py` | — | the map records `885bbfe7…` for `ceqs_games_v1.52.py` | `6af0bd2ccfd80eb71be2cc4c35c263d0dfda5c2dd7a9d0ba6dcb35e5ad4c7e8f` | reproduced-with-difference | same substitution as above |
| placed attack-lab self-test | `python3 domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py --self-test` | Python 3.12.3, repository root | 5 tests, all pass (recorded 5/5 in 1.565 s) | `Ran 5 tests in 6.955s` — `OK`, exit 0 | reproduced | the placed file loads its dependencies by repository-relative path; the cross-domain load works in place |
| placed games self-test | `python3 domains/09-security-games-and-attack-lab/src/ceqs_games.py --self-test` | Python 3.12.3, repository root | 4 tests, all pass (recorded 4/4 in 2.405 s) | `Ran 4 tests in 8.777s` — `OK`, exit 0 | reproduced | timings are longer than recorded throughout this pass; see the note on host load below |
| attack lab, full run | `python3 <source-tree>/ceqs_attack_lab_v1.51.py --all` | Python 3.12.3, source tree, `PYTHONDONTWRITEBYTECODE=1` | recorded log: exit 0, wall 54.5 s; 24 negative tests; framing, no-handle, Grover, collision, challenge-fix and ledger sections; `Successful violations: 0 of 24 attempts` | exit 0; wall **87.6 s**; every section's numbers identical to the recorded log, including the Grover deviations (4.44e-15 … 2.55e-15), the collision means at E = 2…12, the challenge-fix result and the ledger block; `Successful violations: 0 of 24 attempts` | reproduced-with-difference | content and exit code identical; the wall time differs (54.5 s recorded, 87.6 s observed) because other builds were running concurrently on this host. The recorded baseline was also wrapped in a host lock, which this pass did not use. Wall time carries no claim in any document |
| games, full run | `python3 <source-tree>/ceqs_games_v1.52.py --all` | Python 3.12.3, source tree | recorded log: exit 0, wall 126.1 s; four games with their measured means and fits | exit 0; wall 122.7 s; FRAME means 144.7 / 664.8 / 1,153.3 / 4,942.5 / 10,414.0 and fit `1.0178 n − 0.931`; SUPPRESS both schemes and fit `0.4498 h + 0.767`; EVADE means 7.0 … 8,217.0 and fit `1.0242 E + 0.393`; SAFETY impossible for C ≤ 21, possible at C = 22 naming 23 of 22 genuine double-signers with 0 missed; extrapolation errors +4.6 / −12.4 / −38.1 bits | reproduced | every number matches the recorded run. One presentational difference: the run prints the handle-coincidence false-positive seat index (`[40]`), which the recorded document describes in prose |
| placed attack lab, full run (attributed) | `python3 ceqs_attack_lab.py --all`, run from `domains/09-security-games-and-attack-lab/src` by the domain that owns the files | Python 3.12.3, numpy 2.4.6 | recorded log: exit 0, `Successful violations: 0 of 24 attempts` | exit 0; `Successful violations: 0 of 24 attempts`; wall 113.51 s, recorded by that domain in `domains/09-security-games-and-attack-lab/results/attack-lab-run.txt` | reproduced | this row is the owning domain's, not this package's; it is cited here because it is the closest available check that the *placed* copy reproduces the numbers when run end to end, and because it agrees with this package's independent run of the same files |
| placed games, full run (attributed) | `python3 ceqs_games.py --all`, run by the domain that owns the files from `domains/09-security-games-and-attack-lab/src`; this package's copy run from the repository root | Python 3.12.3 | recorded by that domain in `domains/09-security-games-and-attack-lab/results/games-run.txt`: exit 0, wall 148.19 s, four games with their means and fits | exit 0 in both runs; FRAME fit `1.0178 n − 0.931` with extrapolation `2^259.6` against exact `2^255`; SUPPRESS fit `0.4498 h + 0.767` with fit errors −12.4 and −38.1 bits; EVADE fit `1.0242 E + 0.393`; SAFETY impossible for C ≤ 21 and possible at C = 22 naming 23 of 22 genuine double-signers with 0 missed; this package's run measured 168.58 s and the owning domain's 148.19 s | reproduced | the placed copies reproduce every number of the source-tree run above and of the owning domain's own placed run; the three runs differ only in wall time, which carries no claim |
| ledger recomputation, independent route | `python3 domains/06-qpt128-security-target/results/ledger-independent-check.py` | Python 3.12.3, repository root | the file `domains/06-qpt128-security-target/results/ledger-independent-check.txt` | byte-identical output; `RESULT: all recomputed values agree with the report`; exit 0; 0.28 s | reproduced | includes the rows this package quotes: B0 queries −119.000 / margin −11.000 (fails), B0 gates −153.000 / +23.000 (passes), Mode S 1024-bit rigorous gates −159.414 / +29.414 (passes), Mode S 512-bit registry gates +11.207 / −141.207, compat mode gates +55.000 / −185.000; minimum repetitions r = 640 (queries) and 553 (gates); `2·43 − 64 = 22`; `64 = 3·21 + 1`; `C(64,2) = 2016` |
| the flaky-test finding, an independent third sample | `python3 <work-dir>/tmp_docs04/s1011_third_sample.py domains/10-digital-infrastructure/src/s1_lms.py` | Python 3.12.3, 7.9 s | recorded: the slope assertion held in 49.0 % of 200 runs, then 53.5 % of 200 (205 of 400 pooled) | held in **52.0 % of 100 runs**; median 0.5109; range [0.313, 0.701] | reproduced-with-difference | the three frequencies disagree in the second decimal, which is the finding itself: the statistic is a near-coin-flip and the recorded PASS was one draw. Pooled 257 of 500. The measurement script is an artifact of this build, not a repository file; the function it loads is the shipped `s1_lms.py` of the infrastructure domain |

## Not run, and why

| item | verdict | why |
|---|---|---|
| the audit stack's sanitizer, fuzz and fault campaigns (ASan/UBSan/MSan, libFuzzer, 300 fault schedules) | not-run | each needs a compiler toolchain build, or tens of minutes to hours of host time, and each is the audit domain's own evidence, re-run and recorded in `domains/11-independent-audit-stack/` |
| Tamarin, ProVerif, EasyCrypt, TLC/TLAPS | not-run | the formal layer belongs to `domains/11-independent-audit-stack/` and `domains/01-accountable-quorum-foundations/`; this package reports what those domains record, and records that TLC and TLAPS were **never run at any point in the record** |
| the audit ledger end-to-end across all six suites | not-run | the totals (61/64 host-limited, 70/70 in the checklist) are the infrastructure domain's; the repository's own verification pass states it did not run the ledger end-to-end either |
| the D2a/D2b artefacts | not-run | absent from the tree; their numbers are carried as reported and are listed as missing in `validation-status.md` |
| the D3-era proof binaries | not-run | they never ran on the audit host and rebuilding changes their digest (AVX-512 code paths) |
| the ML-DSA-87 / ML-KEM-1024 ACVP cross-validation | not-run | needs the liboqs build and the ACVP vector files; recorded and reproduced in `domains/11-independent-audit-stack/primitives/RESULTS.md` |

## Note on timings

Every timing in this pass is longer than the corresponding recorded timing — 6.955 s against 1.565 s
for one self-test, 87.6 s against 54.5 s for the attack lab, 8.777 s against 2.405 s for the games
self-test, and 168.58 s for the placed games run against the owning domain's 148.19 s for the same
files — while the source-tree games full run matched (122.7 s against 126.1 s). The reason is host
contention: this pass ran concurrently with other builds. No document in this package makes a claim
that depends on a wall time, and no timing line above is evidence of anything except how long the
command took on this host.
