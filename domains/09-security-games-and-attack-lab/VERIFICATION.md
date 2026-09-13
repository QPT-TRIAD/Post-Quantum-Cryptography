# Verification — domain 09 (security games and attack lab)

Every command below was re-run on 2026-09-13 against the **repository copy** of the two harnesses
(`src/ceqs_attack_lab.py`, `src/ceqs_games.py`), from `domains/09-security-games-and-attack-lab/src`,
and compared with the run recorded during the programme's reading pass. That recorded run is the
baseline this domain is checked against; its headline figures — the recorded wall clocks `54.5 s` and
`126.1 s` among them — are quoted in `tooling/run-everything.md` of this repository, and the log files
themselves are part of the programme's build record and are not shipped here. Where a recorded value
does not recur, both values are kept below and the reason is given.

**Environment.** The programme's pinned interpreter: CPython **3.12.3**, with **numpy 2.4.6** for the
attack lab's Grover simulation (the games harness does not import numpy). Both harnesses import only
the standard library, numpy, and the Mode B implementation they test — no solver, estimator or
external service is in the loop, which is why every measured value re-runs identically. All runs use
`PYTHONDONTWRITEBYTECODE=1`, so no `__pycache__` is written beside the sources (none is present).
Host: Ubuntu 24.04.4, x86_64, kernel 7.0.0-31, loaded at the time by other domain builds of this
repository (see the timing rows).

`$L` abbreviates `src/ceqs_attack_lab.py` and `$G` abbreviates `src/ceqs_games.py` below. Every
`observed` figure is the exit code of the process, not only its stdout: a mode whose failure path had
not been shown would make "exit 0" meaningless, so the failure path is demonstrated separately — by
the `results/probe_exit_codes.py` rows, which inject a failing test into a copy, and by the machine
check of the shipped JSON report, which is run once as shipped and once on a mutated copy.

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| lab self-test | `python3 $L --self-test` | pinned env | `Ran 5 tests`, `OK`, exit 0, 1.565 s in-run | `Ran 5 tests in 1.866s … OK` and `in 2.741s … OK` (furthest observation 5.330 s), **exit 0** every run | reproduced | the five test names are identical to the recorded list; the fastest observation here is 19 % above the recorded 1.565 s, the spread is host load. Raw output in `results/probe_exit_codes.txt` |
| games self-test | `python3 $G --self-test` | pinned env | `Ran 4 tests`, `OK`, exit 0, 2.405 s in-run | `Ran 4 tests in 2.493s … OK` and `in 2.554s … OK` (furthest observation 9.230 s), **exit 0** every run | reproduced | the four test names are identical to the recorded list; two observations sit within 7 % of the recorded 2.405 s, the spread is host load. Same file |
| lab full run | `python3 $L --all` | pinned env | exit 0, wall 54.5 s, `Successful violations: 0 of 24 attempts` | **exit 0**, `Successful violations: 0 of 24 attempts`; wall **54.95 s** in the confirmation run on a quiet host, and **113.51 s** for the run whose transcript is shipped | reproduced | the count and every measured value are identical in every run, and the quiet-host run lands within 1 % of the recorded 54.5 s. Raw output `results/attack-lab-run.txt`; the wall-clock spread is set out in the timing note below |
| games full run | `python3 $G --all` | pinned env | exit 0, wall 126.1 s, slopes 1.0178 / 0.4498 / 1.0242, threshold 22 | **exit 0**, slopes 1.0178 / 0.4498 / 1.0242, threshold 22; walls **56.11 s** (confirmation run) and **148.19 s** (the run whose transcript is shipped) | reproduced-with-difference | every measured value identical, including all 24 SAFETY rows and the false-positive seat; only the wall clock moves, in both directions. Raw output `results/games-run.txt` |
| **the wall clocks, every observation** | `--all` and `--all --json` for both harnesses, 10 runs across this build, plus 3 runs another package made of the same files | pinned env | the recorded runs were wrapped in a shared host-lock helper — `hostlock.py shared -- timeout 900 python3 …`, the practice domain 05's verification notes record for the recorded runs of that session | lab `--all`: **54.95 s** (quiet host, this build) and 113.51 s (the shipped transcript's run); lab `--all --json`: 59.63 s and 69.06 s. games `--all`: **56.11 s** (quiet host) and 148.19 s (shipped transcript); games `--all --json`: 55.54 s and 88.78 s. The same files measured elsewhere in this repository: lab 87.6 s, games 122.7 s and 168.58 s | reproduced-with-difference | the spread is host load, not code. Runs of identical code differ by up to 3× in **both** directions, the recorded lab figure is reproduced within 1 % when the host is quiet, and no measured value moved in any run — instead the same load pushes times both ways, so a wall clock here is evidence of nothing except how busy the host was. Wall time carries no claim in any document of this domain |
| every number quoted in the prose, checked against the machine-readable payload | a script reading `results/attack-lab-report.json` and `results/games-report.json` and asserting each value appears in the corresponding printed run | pinned env | the two documents must not disagree with the two reports | **24 assertions, 0 mismatches**: FRAME means 144.7 / 664.8 / 1,153.3 / 4,942.5 / 10,414.0, fit 1.0178, extrapolation 259.6; SUPPRESS ten means 16.0 … 71,289.0, fit 0.4498 and errors −12.4 / −38.1; EVADE means 7.0 / 21.5 / 61.5 / 453.2 / 1,322.0 / 8,217.0, fit 1.0242, `extrapolation_E512_log2_classical` = 524.8; SAFETY 22/22; `A_negative` 24 attempts with an empty `violations` list; B-framing ten means 88/88/580/580/968/968/4,702/4,702/9,358/9,358 with `mean_marked` 1.0 at every size; Grover measured optimum equals predicted at 12/25/35/71 with deviations 4.44/5.33/3.22/2.55 ×10⁻¹⁵; collision means 11.875 / 24.25 / 140.375 / 449.625 / 1,988.25 / 15,560.0; ledger R1 −145.0, R2 −209.0, R3 −138.1, R4 −159.4, R5 −181.2, total −137.7, D2 margin 7.7 | reproduced | this is how the domain's prose is held to its own artifacts. It found no disagreement, and the EVADE extrapolation is the value that an earlier draft of `docs/game-evade.md` had mis-copied as `2^512.8` — the check is what caught it |
| Experiment A (24 attempts) | `python3 $L --negative` | pinned env | 24 attempts, 0 successful violations, positive control extracts 22 seats | 24 attempts, **0 violations**; the report carries 24 result entries flagged `rejected: true`, of which 23 are refusals each with the implementation's own reason string and the 24th is the positive control (`positive control: honest conflict extracts 22 seats` / `extracted 22`) — in the report's vocabulary `rejected` means *the attempt gained no violation*, which is why the control carries the flag too | reproduced | exit 0, 0.97 s in the sequential pass. The reason strings are byte-identical to the record's. The record's own §9 groups ten of these under "malformed encoding … all rejected", `duplicate registration` among them |
| Experiment A, attempt 17 | same | pinned env | the record lists "duplicate registration" under the malformed-encoding category | rejected with reason **`handle collision`** — a toy-width artefact, not a duplicate-seat check: at `n = 14` the second registration's handles collide with probability ≈ 0.054, and at `n = 32` the same encode is **accepted** | reproduced-with-caveat | the 0-of-24 count stands; this row must not be quoted as evidence that duplicate registration is refused. `docs/attack-lab.md` §1 |
| Experiment B (framing, `M`) | `python3 $L --framing` | pinned env | `M = 1` for every target, both handle kinds; means 88 / 580 / 968 / 4,702 / 9,358 | `M = [1,1,1,1,1,1]` in all 60 target-instances for both kinds; identical means 88 / 580 / 968 / 4,702 / 9,358 | reproduced | exit 0, 28.29 s in the sequential pass. The power and linear handle rows are identical at every point |
| Experiment B2 (no-handle control) | `python3 $L --baseline` | pinned env | joint space `2^16`, `M = 1`; with handle `2^8` | identical (`log2_joint_space: 16`, `log2_space_with_handle: 8`, `marked_sizes: [1,1,1]`) | reproduced | exit 0, 5.75 s |
| Experiment C (Grover) | `python3 $L --grover` | pinned env, numpy 2.4.6 | measured optimal iterations equal predicted at every size; `max|sim−theory|` 4.4×10⁻¹⁵ … 5.3×10⁻¹⁵ | identical: 12/12, 25/25, 35/35, 71/71; deviations 4.44×10⁻¹⁵, 5.33×10⁻¹⁵, 3.22×10⁻¹⁵, 2.55×10⁻¹⁵ | reproduced | exit 0, 1.10 s |
| Experiment D (collision) | `python3 $L --collision` | pinned env | means 12 / 24 / 140 / 450 / 1,988 / 15,560; fitted slope 1.037 | means 11.875 / 24.25 / 140.375 / 449.625 / 1,988.25 / 15,560.0; fitted slope 1.037 | reproduced | exit 0, 20.43 s in the sequential pass. The record's table rounds these to integers; the exact means are in the report |
| Experiment E (challenge fix) | `python3 $L --challenge` | pinned env | v1.46 broken after 234 messages ("inverse of zero"); v1.50 survives a first-coefficient collision found after 172 messages | `v1.46_broken: true` after 234; `v1.50_survives: true`, collision after 172, 22 seats named | reproduced | exit 0, 0.38 s |
| Experiment F (ledger) | `python3 $L --all` (F is printed by `--all`) | pinned env | R1 −145.0, R2 −209.0, R3 −138.1, R4 −159.4, R5 −181.2, total −137.7, D2 margin 7.7 | identical to the last digit | reproduced | these rows are domain 08's ledger, **printed** by the lab and not recomputed here. They are not reconciled with the target domain's ledger (+29.4 bits over E1–E8) — an open item owned jointly with domains 06 and 08, recorded in `docs/validation-status.md` §7 |
| games: FRAME | `python3 $G --frame` | pinned env | means 144.7 / 664.8 / 1,153.3 / 4,942.5 / 10,414.0; fit slope 1.0178; endgame names the victim | identical; endgame output `victim seat 0 named by extraction: True` | reproduced | exit 0, 9.74 s |
| games: SUPPRESS | `python3 $G --suppress` | pinned env | 10 birthday points; pooled fit 0.4498; extrapolation errors −12.4 and −38.1 bits | identical, including all ten means and the two error figures | reproduced | exit 0, 34.02 s |
| games: EVADE | `python3 $G --evade` | pinned env | means 7.0 / 21.5 / 61.5 / 453.2 / 1,322.0 / 8,217.0; fit slope 1.0242 | identical; end-to-end `names the other 21 and flags complete=False` | reproduced | exit 0, 13.14 s |
| games: SAFETY | `python3 $G --safety` | pinned env | impossible for `C ≤ 21`; `C = 22` names 23 of 22 genuine with 0 missed; `C = 23` names 23 of 23 | identical, including the false-positive seat 40 at `C = 22` | reproduced | exit 0, 0.72 s |
| JSON report — lab | `python3 $L --all --json` → `results/attack-lab-report.json` | pinned env | no recorded baseline (the mode was not exercised in the reading pass) | exit 0, 69.06 s, 13,268 B; `attempts: 24`, `successful_violations: 0`, `violations: []`; every measured field equals `results/attack-lab-run.txt` | reproduced | the file holds a real run; it was zero bytes before this capture and is not a placeholder. `results/README.md` §2 |
| JSON report — games | `python3 $G --all --json` → `results/games-report.json` | pinned env | no recorded baseline | exit 0, 88.78 s, 14,124 B; slopes 1.0178 / 0.4498 / 1.0242, threshold 22/22, all four game definitions and all measurements present; equals `results/games-run.txt` field for field | reproduced | as above |
| machine check of the recorded gate | `python3 -c "import json,sys; d=json.load(open('../results/attack-lab-report.json')); a=d['A_negative']; sys.exit(0 if a['attempts']==24 and a['successful_violations']==0 and not a['violations'] else 1)"` | pinned env | exit 0 | **exit 0** | reproduced | run from `src/`; re-run during this build and it exited 0 again. Its failure path was then exercised: the same one-liner against a copy of the report with `A_negative.successful_violations` set to 1 exits **1**, so the check can fail and its exit 0 carries information |
| **failure path of the check mode** | `python3 results/probe_exit_codes.py` | pinned env | the mode that carries assertions must exit non-zero when one fails | shipped harnesses: `exit=0` (`Ran 5 tests … OK`, `Ran 4 tests … OK`). The same mode on a copy with **one test appended that fails unconditionally**: `exit=1` for both harnesses | reproduced | no shipped file is modified: the probe prints both harnesses' sha256 before and after and they are unchanged. The failure path is the source line `return 0 if r.wasSuccessful() else 1` |
| **`--all` has no failure exit code** | reading the source | pinned env | — | `src/ceqs_attack_lab.py` line 728 and `src/ceqs_games.py` line 569 are both a bare `return 0`: `--all` is a **report mode** and returns 0 by construction, so its verdict is in the report body, never in the exit code | stated, not a defect | the machine check above is what gives the report an exit code; `docs/games-methodology.md` §7 |
| probe output is regenerated | `grep -nE "/home/\|/Users/\|/tmp" results/probe_exit_codes.txt` | pinned env | no absolute path in a stored artifact | no match | reproduced | the first version of the probe printed the absolute path of `src/`; the probe now prints it relative to the repository root and the stored file was **regenerated**. A reader re-running the probe gets the same output apart from in-run test timings. `results/README.md` §2 |
| CFHL constants used by the games | binary search over `domains/06-qpt128-security-target/src/qpt128_finalization.py:cfhl_collision` for the smallest `q` whose bound exceeds 1/3 | pinned env, exact rational arithmetic | the games print `81.7` / `99.7` / `252.4` / `270.4` as constants, citing "the project's own CFHL collision bound" | re-derived: `2^81.74` queries at `h = 256` and `2^252.40` at `h = 768`; gates at `2^18`/query: 99.7 and 270.4 — the printed constants reproduce exactly | reproduced | the derivation is not shipped here: the function belongs to domain 06, which ships it for this purpose. A revised collision bound would move these four printed values and one verdict sentence, and no measured quantity. `docs/games-methodology.md` §5.3 |
| version cross-check | the same two commands re-run in a scratch tree, outside this repository, that mirrors the repository layout with the **v1.51** module placed at the pinned v1.50 path | pinned env | the shipped harnesses pin Mode B **v1.50** — `domains/08-hidden-signers/history/hidden-signer-mode-b-v1.50.py`, sha256 `97a3821a…` — the revision the record was measured against; domain 08's live module is the newer `domains/08-hidden-signers/src/hidden_signer_mode_b.py`, sha256 `f0803a89…`, whose own header calls it **v1.51, the audit-fix release of v1.50** adding F5 canonical-input checks (`encode` requires a 64-byte `domain` and `bytes` `proof`; `parse` requires `bytes`) plus two regression tests | lab `--negative`: exit 0, 24 PASS, and the 24 lines are **byte-identical** to the record's — every rejection reason unchanged, including `handle collision` and `noncanonical header`. **both suites were then run end to end under v1.51** (`--all`, exit 0 for each, 64.59 s and 56.77 s). Compared line by line with the v1.50 transcripts, after stripping the provenance header and the per-phase seconds: **lab 87 of 87 content lines identical, games 62 of 62 — 0 differences in either suite**. | reproduced | run during this build because the F5 checks add rejection paths, which is exactly what could change a rejection reason. A change here would mean the 0-of-24 count is a statement about v1.50 only and would have to be re-stated against v1.51. Not shipped, since its object is a scratch copy; the digests above are what the check rested on |
| read-only source tree | `python3 tools/check_pqt_baseline.py` (from the build workspace, outside this repository) | — | the baseline captured before this build must be unchanged | `baseline files: 1157`, `present now: 1157`, `size changed: 0`, `mtime changed: 0`, `added: 0`, `removed: 0`, `RESULT: PASS -- source tree unmodified` | reproduced | nothing under the source tree was created, modified or deleted; every source file was opened read-only |
| repository content gate, this domain | `python3 tooling/checks/scan-forbidden.py domains/09-security-games-and-attack-lab` | pinned env | nothing in this domain may carry an AI-tool name, a machine path, a tracking parameter, a contact string or a secret | **files scanned: 19, findings: 0**, exit 0 — `abs-path` 0 and every other category 0 | reproduced | run as the last check of this build, on the finished domain: `README.md`, `VERIFICATION.md`, the seven documents, the two harnesses and the eight files in `results/`; run again after the repository-wide scrub described two rows below, with the same 19 files and the same 0. The scanner skips its own source by identity |
| repository content gate, whole tree — a finding that is **not** this domain's | `python3 tooling/checks/scan-forbidden.py .` from the repository root | pinned env | the whole repository should scan clean | 626-file run (before this domain's last edits): **626 files scanned, 1 finding** — `abs-path`, in `domains/11-independent-audit-stack/results/rerun/fixed-file-selftests.txt` line 32, a stored traceback line naming an absolute source-tree path. On the same run this domain's 19 files were at 0, and when the whole tree was scanned earlier (613 and 625 files) the total was 0. **Re-run after the repository-wide scrub, 19:26: `644 files scanned, findings: 0`, all six categories 0, exit 0**; this domain's 19 files again 0; the audit-stack file no longer carries the path, and the package that owns it reports the emitter fixed and its transcripts regenerated | the 1 finding was reported, not fixed here; the clean re-run **reproduced** | the file belonged to the independent-audit-stack package, which was writing it while this domain was checked; that package owned the remedy (relativise the path where the capture is emitted and regenerate the file, which is what `results/probe_exit_codes.py` does here) and has applied it. Recorded rather than smoothed over: a repository-wide gate that passes only when nobody looks is worth less than one that reports what it saw. **A window in between is recorded too** (times throughout this document are host-local, UTC+2; the tooling package's own record states this same window as 17:25Z–17:26Z, which is the same two minutes): at 19:24 the scanner could not run at all — an automated tree-wide scrub replaced the scratch-prefix literal inside the scanner's own `abs-path` rule — a path component that names an AI tool, so the rule's own text is a string the `ai-name` category forbids — with a placeholder, and in doing so swallowed the delimiter guard in front of the next alternative and left an unbalanced parenthesis, so the command exited 1 with `re.error: unbalanced parenthesis` instead of any count. A gate that cannot parse reports nothing, and no other check flags it: `verify-repository.py` stayed at PASS throughout that window. The tooling package repaired the rule by 19:25 (the rule now carries the delimiter guard again and the scanner parses), and the substitution was logged while it was in flight in a `records/scrub-report.tsv` working file that had been removed again by 19:26 — so the repair is read here from the tool itself, not from a record of it. Note that the file itself is one of the strings the rule forbids, which is why the identity skip exists. One trap this leaves open, and the reason no whole-tree transcript is stored in this domain: the scanner's skip note prints **its own absolute source path**, so a stored transcript of a whole-tree run would carry exactly the string the `abs-path` rule forbids |
| repository file-map gate | `python3 tooling/checks/verify-repository.py` | pinned env | the tree matches `records/file-map.tsv`, and no file is empty | `empty files: **0**`, `UNEXPLAINED files: 0`, `missing from repo: 0`, `malformed map rows: 0` — all as required; but the overall verdict is **`RESULT: FAIL`, exit 1**, on `sha256 differences: 131 (explained by rewrites: 1)` | the four counts reproduced on both runs; the earlier FAIL was a discrepancy **not of this domain's making**, reported here because this domain saw it. **Re-run at 19:26, after the integration pass rebuilt the two tables at 19:24:35: `missing from repo: 0`, `sha256 differences: 0` (explained by rewrites: 132), `UNEXPLAINED files: 0`, `empty files: 0`, `RESULT: PASS`, exit 0** | reproduced | the tool credits a digest difference only when the file's **destination** path appears in the second column of `records/rewrites.tsv` (its source comment says so at line 79); on the earlier run that column held source-tree file names, so rewritten copies were not credited and landed in the error list. `tooling/checks/verify-repository.py` is unchanged since 19:10:34, so the repair was to the tables, not the tool: the rebuilt `records/rewrites.tsv` now names destination paths and every one of the 132 differences is credited. This domain's three map rows survived the rebuild unchanged (`attack_lab_results_v1.51.md`, byte-identical, no difference; the two rewritten harnesses, whose digests are in the Digests section above and whose rewrite rows are rows 77 and 78 of the rebuilt table). The map and rewrite tables were being rebuilt by the repository's integration pass while the first run was made (the work tree's `build_rewrites.py` was modified during it), and that pass owns the verdict on both |

## Digests

The two copied files carry repointed internal references (a relative module path for the pinned Mode B
revision, an orientation paragraph, plain repository paths in place of versioned file names), so their
digests differ from the source-tree digests by design. The pairs below are what this domain
contributes to the build's rewrite record; the rewritten copies are the ones in this directory.

| repository file | repository sha256 | source-tree file | source sha256 |
|---|---|---|---|
| `src/ceqs_attack_lab.py` | `7df54f12adb92b9ad39ab5aea40999a5cfda1d1becbb3c76d3c453ad1f21ac2e` | `ceqs_attack_lab_v1.51.py` | `78c9b204c10fd1db6bf1958d600950cc673e254487d3cd5615e7bfd62df96b31` |
| `src/ceqs_games.py` | `6af0bd2ccfd80eb71be2cc4c35c263d0dfda5c2dd7a9d0ba6dcb35e5ad4c7e8f` | `ceqs_games_v1.52.py` | `885bbfe705dd62f3b21640450c3a72410b853872b9698da57cc10c1d0879f62e` |
| `results/attack-lab-results.md` | `7638c8ca156fd41c7a76631799e9b84834388b243aa5c88b8d46205e7213bed5` | `attack_lab_results_v1.51.md` | same digest — **byte-identical, not rewritten** |

Both rewrites are **prose and path only**, and the count is per file, not per pair: 7 rows of
`records/rewrites.tsv` name `ceqs_attack_lab_v1.51.py` and 4 name `ceqs_games_v1.52.py`. In each file
exactly one row is `[judgement]` — the cross-domain loader path, which had to be repointed at the
pinned revision in another domain — and the rest are `[mechanical]`: the versioned file names of that
revision and of four other domains' files, which no longer exist under those names here. A rewritten
copy's output is identical to the record's, line for line (the v1.51 comparison above is the same
check run from the other side), which is the strongest available evidence that the rewrites are inert:
a substitution that had touched an executable statement would move a number or a rejection reason.

Files written by this build, for the record:

| file | bytes |
|---|---:|
| `README.md` | 18,351 |
| `docs/games-methodology.md` | 21,597 |
| `docs/attack-lab.md` | 19,718 |
| `docs/game-frame.md` | 10,089 |
| `docs/game-suppress.md` | 12,500 |
| `docs/game-evade.md` | 8,134 |
| `docs/game-safety.md` | 8,957 |
| `docs/validation-status.md` | 16,102 |
| `results/README.md` | 5,455 |
| `results/probe_exit_codes.py` | 6,992 |
| `results/probe_exit_codes.txt` | 1,320 |

Sizes are those of the files as published, measured after the last edit of this build — and after one
edit that was **not** this build's. At 19:17:53–19:18:07 the repository's assembly pass rewrote a bare
code-span file name in five of the documents above to name the sibling domain that owns it:
`docs/mode-b-security.md` → `domains/08-hidden-signers/docs/mode-b-security.md`,
`docs/theory.md` → `domains/06-qpt128-security-target/docs/theory.md`, and
`mode_b_rigorous_ledger.py` → `domains/08-hidden-signers/src/mode_b_rigorous_ledger.py`
(`README.md` +57 bytes, `docs/games-methodology.md` +94, `docs/attack-lab.md` +30,
`docs/game-evade.md` +26, `docs/validation-status.md` +30). It is a path qualification only, of names
this domain had already cited: the affected lines were re-read after it, and no number, verdict,
evidence label or quotation moved. Those five files are the only ones whose sizes differ from the
table's first printing (`game-frame.md`, `game-suppress.md`, `game-safety.md`, `results/README.md`,
`results/probe_exit_codes.py` and `results/probe_exit_codes.txt` are unchanged), so a reader diffing
published bytes against this table should expect these five and nothing else.

The two files this domain's checks depend on, neither of which this domain owns:

| dependency | digest | why it is here |
|---|---|---|
| `domains/08-hidden-signers/history/hidden-signer-mode-b-v1.50.py` | `97a3821a4235bd2a8db1c4ce6717edf9b5541d1f6758b1995c8670745888f75d` | the pinned Mode B revision both harnesses load; the record was measured against it |
| `domains/08-hidden-signers/src/hidden_signer_mode_b.py` | `f0803a89bb3c6a7cb6c37e5c95d5b4f0655d957067fd22315d7c580f4062654a` | the v1.51 audit-fix release the cross-check above substitutes for it |

`VERIFICATION.md` cannot carry its own digest. Running or importing the harnesses can leave a
`__pycache__` directory beside them; `PYTHONDONTWRITEBYTECODE=1` was set for every run and none is
present.

## What was not run, and why

- **Nothing was written, moved or deleted in the read-only source tree.** The baseline check above
  passes; every source file was opened read-only and no output of these runs was written outside this
  repository.
- **The production-parameter runs of the record's §8** (the C prover at 2^20 and 2^22 trees; 30,684 B
  and 28,708 B certificates; prove 60 s / 219 s). Those are a size-and-time measurement of a C
  prover that this domain does not ship, and their numbers are quoted from the record as such.
- **The unshipped SAT experiments.** Not in this repository, not invoked by either harness, and not
  re-runnable here; the programme's validation package records that their one published comparison
  was inconclusive and that CryptoMiniSat never ran on the verification host. See `README.md` §5 and
  `docs/validation-status.md` §6.
- **Any cryptanalysis of the key map `F`** (XL, hybrid, Gröbner, lattice, Weil descent). Nothing in
  this domain attempts it; it is domain 08's surface and the largest untested dependency of every
  conclusion here.
- **A continuous end-to-end attack.** FRAME's endgame starts from the recovered opening and EVADE's
  from a fabricated second opening rather than a genuine collision; in both cases the two halves are
  measured separately at the same parameters. `docs/game-frame.md` §4, `docs/game-evade.md` §5,
  `docs/validation-status.md` §5.
- **A formal proof tool.** No result in this domain is stated as machine-checked, so no prover or
  model checker was exercised. `tamarin-prover`, `maude` and `proverif` are not needed by anything
  here.
- **The two-ledger reconciliation.** This domain quotes domain 08's ledger rows as the record does; it
  does not reconcile them with domain 06's E1–E8 rows, whose D2 margin differs by 21.7 bits. The
  programme's validation package names this domain as a co-owner of that open item, and
  `docs/validation-status.md` §7 records it rather than resolving it.
