# VERIFICATION — D4 operator-ledger

Every row below was run on 2026-09-13 during this domain's build. Commands are given exactly as
issued, with repository-relative paths. `env` is the pinned environment activated by
`. <env>/activate.sh` (the path is recorded in the repository's environment notes and is not
repeated here).

**Summary: everything D4 claims to reproduce, reproduces.** The catalogue copy, both extractions and
the checker re-run are byte-identical to their recorded counterparts; a negative control confirms the
checker's PASS is a real gate. One figure in the prior reading record — the "113 of 116" amendment
count — is **not reproduced**; the measured figure is 101 (106 on the stricter reading), and the
same record's amendment decomposition (130 / 82 / 37 / 11) is also not reproducible. Those two rows
are marked prominently below.

## Environment

| | |
|---|---|
| Interpreter | Python 3.12.3 (main, Aug 31 2026) from `env`, as recorded for this domain |
| Second interpreter | Python 3.13.15 (`/usr/bin/python3.13`), used as an independence check |
| Platform | Linux, x86-64; wall times from `time` |
| Network | not used by any row below |
| Third-party packages | none; the checker imports only `fractions`, `itertools`, `math`, `json` |

## Main table

| # | Item | Command (exact) | Environment | Expected (recorded) | Observed | Verdict | Notes |
|---:|---|---|---|---|---|---|---|
| 1 | Catalogue document copied byte-identical | `sha256sum <source-doc> docs/operator-ledger.md` | shell | the copy is the record | both `225fd1acf3389d2cd7ffb064ba0e37afc67e290b3d163540360fb72d084dc98a`; `cmp` reports identical | **reproduced** | 846,185 bytes, 19,608 lines. The source document's mtime is unchanged (2026-09-10 20:28). |
| 2 | Checker extraction byte-identical | `sed -n '19259,19607p' docs/operator-ledger.md \| cmp - src/operator_ledger_checks.py` | shell | matches the document's closing block | identical; 349 lines, 15,785 bytes, sha256 `6b7d8b71da21e57bf70b219707f5393dc004e88f0276da7dcc876c58eac22ecc` | **reproduced** | Independent hashes, not a self-comparison; the drawn range is the fenced code block only. |
| 3 | Recorded-results extraction byte-identical | `sed -n '19093,19251p' docs/operator-ledger.md \| cmp - results/operator_ledger_checks.json` | shell | matches the document's JSON block | identical; 159 lines, 5,011 bytes, sha256 `ccf30e1760cf4b945f3e08ba1c1ccceec94b81767cd40b4fefd0a3ea5bc46610` | **reproduced** | The range excludes the ``` fences at 19092 and 19252. |
| 4 | Checker re-run matches the record | `python3 src/operator_ledger_checks.py > /tmp/observed.json; diff results/operator_ledger_checks.json /tmp/observed.json` | pinned interpreter (3.12.3) | 23 groups, `full_QPT128_established: false`, JSON identical to the recorded block | exit 0, empty stderr, `diff` no output, wall 0.07–0.10 s | **reproduced** | `test_groups_passed: 23`; stages `73/137/193/265` ideal and `88/165/233/320` robust; `robust_128_raw_bound_log2_display: -5.302071443572686`. |
| 5 | Checker re-run under a second interpreter | `/usr/bin/python3.13 src/operator_ledger_checks.py \| diff results/operator_ledger_checks.json -` | Python 3.13.15 | — (not in the record) | exit 0, `diff` no output | **reproduced** | Shows the result does not depend on the interpreter above the 3.8 floor. |
| 6 | Negative control: a false expectation must fail | `sed 's/==\[73,137,193,265\]/==[74,137,193,265]/' src/operator_ledger_checks.py > /tmp/broken.py; python3 /tmp/broken.py` | pinned interpreter | not recorded | exit 1, **0 bytes of stdout**, `AssertionError` on stderr | **reproduced** | One line changed (checker line 223). Run on a scratch copy outside the repository; the shipped file was not modified. Confirms PASS is a gate rather than a label. |
| 7 | `-O` disables the whole pass criterion | `/usr/bin/python3.12 -O /tmp/broken.py` | Python 3.12 with optimisation | not recorded | exit 0, full 5,011-byte JSON, 23 groups `PASS` | **reproduced** | **Hazard, recorded as a finding.** The same broken file that fails normally reports complete success under `-O`. Any harness adopting this checker must not pass `-O`/`-OO`. |
| 8 | Interpreter floor of `pow(x,-1,q)` | inspect only: `grep -n 'pow(' src/operator_ledger_checks.py` | — | Python ≥ 3.8 | one call site, line 94, three-argument `pow` with a negative integer exponent | **not-run** | No interpreter below 3.12 exists on this machine, so the floor could not be executed. The call path *is* exercised by the recorded run (group 17 pivots), so the run does establish that it works at 3.12 and 3.13. |
| 9 | Amendment count | `grep -c '^\*\*Amendment (' docs/operator-ledger.md` | shell | 116 (ledger header, line 7) | 116 | **reproduced** | First amendment at line 804; the last at 19054. |
| 10 | Per-family amendment counts | awk over the 20 family line ranges (command in `docs/validation-status.md`) | shell | the ledger's own provenance table (306–327) | `L`16 `T`8 `F`7 `Q`8 `D`7 `I`8 `P`8 `S`7 `M`7 `C`6 `H`3 `K`3 `N`2 `X`3 `G`0 `R`9 `O`5 `W`2 `Y`5 `Z`2; sum 116 | **reproduced** | Every family matches the table the ledger publishes. `G` has no amendments at all. |
| 11 | Amendments per half-file | `awk 'NR>=788&&NR<=9697' … \| grep -c '^\*\*Amendment ('` and the same for 9698–19059 | shell | record says 82 and 37 | **79** (L1–C35) and **37** (C36–Z50); 79 + 37 = 116 | **not-reproducible** | The record's 37 is right; its 82 counts families `L`–`C` as whole families, including `C44`, `C45`, `C47`, which the 37 already contains. See `docs/validation-status.md`. |
| 12 | Entries named by a checker group | `sed -n '19066,19088p' docs/operator-ledger.md \| cut -d'\|' -f2 \| grep -oE '\b[A-Z][0-9]{1,2}\b' \| sort -u` | shell | not recorded as a list | 15: `D9 H20 I21 I33 L1 L10 L35 L47 L9 Q40 R36 T42 T7 T8 Y1` | **reproduced** | Taken from the Check column of the ledger's own 23-row results table. |
| 13 | Amendments carrying a literature citation | `grep '^\*\*Amendment (' docs/operator-ledger.md \| grep -cE '\[S[1-8]\]\|[Ee]xternal references? S[1-8]\|https?://\|arXiv\|FIPS\|RFC [0-9]\|doi:\|NIST'` | shell | record implies some do | **0** | **reproduced** | All 116 amendment paragraphs are single lines, so this scan covers their full text. |
| 14 | Citation instances in the document | `grep -nE '\[S[0-9]+\]\|[Ee]xternal references? S[0-9]' docs/operator-ledger.md \| grep -v '#op-' \| awk -F: '$1<284 \|\| $1>298'` | shell | 14 instances (reading record) | 12 lines, 89–732; 14 instances; per source `S1` 3, `S2` 1, `S3` 3, `S4` 3, `S5` 1, `S6` 1, `S7` 1, `S8` 1 | **reproduced** | Excludes the 8 source-list definition lines. All citations precede the first amendment (line 804). |
| 15 | **The "113 of 116" amendment-witness claim** | rows 9, 12, 13 combined | shell | "113 of the 116 amendments, and 34 of the 37 in this range, have no executable witness and no literature citation" (reading record, quoted by the theory index) | 116 total; 15 named by a checker group (**10** with a computed witness, 5 resting on literals or on `assert (1-2)==-1`); 0 cited; therefore **101** have neither (**106** on the strict reading) | **not-reproducible** | **See the discrepancy section. 113 was not observed and cannot be obtained from the document.** |
| 16 | **The "130 amendments / 82 / 37 / 11" decomposition** | rows 9 and 11 | shell | 130 amendments; 82 D4a; 37 D4b; 11 elsewhere | 116 amendments; 79 + 37 | **not-reproducible** | The "130" total and the "11 elsewhere" have no reading found here. See below. |
| 17 | The record's CE-exec classification of first-half amendments | not a runnable check; compared against row 12 | — | "CE-exec 9 including 2 weak" | measured by the criterion used here: 12 first-half amendments named by a group, 5 of them weak | **not-reproducible** | The record's criterion is not stated precisely enough to re-run; its figure (9) and this one (12) come from different classifications, so this row records a difference, not an error. |
| 18 | The two named predecessor inputs | `sha256sum` of the named files | — | digests recorded at lines 300 and 302 | files absent from the tree; digests uncheckable | **not-run** | `operators_1000(1).md` and `continuation_v1.32/report.md`. Stated as absent in the README; nothing was fabricated in their place. |
| 19 | Source tree untouched by this domain | `find <source-tree> -newermt '2026-09-13 00:00'` | shell | no writes by D4 | no path under the tree has an mtime inside this domain's build window; the D4 source document's mtime (2026-09-10 20:28) and hash are unchanged | **reproduced** | 12 paths elsewhere in that tree carry earlier same-day timestamps from other work on that machine (latest 17:26, before this domain's build began); none was written by D4, which read from the tree only. |

## The extraction, recorded

`src/` and `results/` are drawn from the catalogue document itself, so the repository does not depend
on the source tree for them. The two commands are the ones in the README:

```
sed -n '19259,19607p' docs/operator-ledger.md > src/operator_ledger_checks.py
sed -n '19093,19251p' docs/operator-ledger.md > results/operator_ledger_checks.json
```

Row 2 and row 3 confirm that re-running these reproduces the committed files byte for byte. The
document names the script `check_operators.py`; it is committed here as `domains/04-operator-ledger/src/operator_ledger_checks.py`,
as the domain brief proposes. No line of it was edited.

## Discrepancies, recorded without adjusting the record

### 1. The "113 of 116" claim is not reproduced (rows 15)

The claim as the reading record states it: *"113 of the 116 amendments, and 34 of the 37 in this
range, have no executable witness and no literature citation."* The second half of that sentence —
34 of 37 for the second-half range — is correct and was confirmed. The first half was not.

Measured: 116 amendments exist; 15 are named by a checker group; 10 of those rest on a computed
assertion; 0 carry any citation. So the number with neither an executable witness nor a citation is
**101** (or **106** if a witness must compute the corrected value rather than restate it). **113
would require only three witnesses in the entire file**, and three is the witness count for the
second half alone (`H20`, `R36`, `Y1`), which is the range the same dossier's own sentence is about.
The figure appears to be that half-range result applied to the whole-file denominator, and it
contradicts the same record's classification of the first half as containing nine executed-evidence
amendments. The ledger's own sentences are more careful than either: *"They do not test all 116
editorial amendments"* (line 19062) and *"These counts describe review coverage, not 1,000 certified
mathematical theorems"* (line 7).

The record is not adjusted here. The claim is stated as the record states it, and the measured
figure is stated beside it, with the commands that produce it.

### 2. The amendment decomposition (row 16)

The record gives the ledger "130 amendments (82 in the D4a range, 37 in the D4b range, 11
elsewhere)". The document contains 116 `Amendment (LABEL)` paragraphs, and its own header and
provenance table both say 116. By the record's own half boundary (`C36–Z50` for the second half),
the split by line range is 79 + 37 = 116. The 82 is the sum of the ledger's per-family counts for
families `L`–`C` taken as whole families; that spans the boundary and includes `C44`, `C45` and
`C47`, which the 37 already counts. No reading of the document that yields 130 or 11 was found.

### 3. A hazard in the checker, not an error in it (row 7)

The checker's entire pass criterion is `assert`. Under `python3 -O` the assertions are stripped and
a file with a false expectation prints a complete, well-formed summary with 23 `PASS` rows and exit
0. This is not a defect in the document's claim — the document never says otherwise — but it is a
condition any consumer of the checker must respect, and it is recorded here because a harness that
adopts the checker without knowing it would produce vacuous green results.

## What was not verified, and why

- **The original 1,000-entry catalogue** and **the v1.32 workspace report** are absent from the tree
  (row 18). The retention claim and the constants that trace to the report cannot be checked by
  anyone, here or elsewhere, from this repository.
- **The eight external sources** were not fetched or read; their statements are reported as the
  ledger gives them, and the three incomplete references are recorded as incomplete in
  `docs/theory-borrowed.md`. No reference was completed from memory.
- **The deployed verifier, hash, sampler and extractor** are outside this domain: the checker
  executes no quantum cryptanalysis and instantiates none of the seven open premises.
- **A systematic audit of the 116 amendments** was not performed. Nine were read closely and are
  correct as stated; that is not evidence about the other 107.
