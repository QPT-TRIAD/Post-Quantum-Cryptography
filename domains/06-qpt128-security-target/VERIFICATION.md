# VERIFICATION — 06-qpt128-security-target

What was re-run while building this domain, what it returned, and how it compares with the recorded
baseline. Every command below is written relative to the repository root. The recorded baseline is
the verification log produced when the v1.43 source was read (build work tree:
`logs/qpt128_finalization_v1.43.py.run.txt`, run under a shared host lock, with the environment
activation script for the pinned interpreter). That log holds three runs: the bare invocation, the
self-test and the report. Nothing else was recorded for this source, so for the remaining items the
table records what was observed and says explicitly that there is no baseline to compare with.

**Environment for every row below.** Linux x86-64; Python 3.12.3 (the pinned interpreter). The
checker is standard-library only, so no other dependency applies. The recorded runs were made with
the environment activation script; the runs here were made the same way. The recorded runs were made
under a shared host lock, so the elapsed times in the log include the lock wait; the runs here were
not, which affects only elapsed-time lines, never outputs or exit codes.

## Required table

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| placed source bytes | `sha256sum domains/06-qpt128-security-target/src/qpt128_finalization.py` (before the rewrite) | — | map records `2762b2c2…` for `qpt128_finalization_v1.43.py` | `2762b2c2…` | reproduced | byte-identical to the source before the documented rewrite; after the rewrite the file is `b3f3325e…` (see "Differences that are expected, not discrepancies") |
| placed document bytes | `sha256sum domains/06-qpt128-security-target/docs/qpt128-finalization.md` (before the rewrite) | — | map records `ee356655…` for `QPT128_finalization_v1.43.md` | `ee356655…` | reproduced | byte-identical before the rewrite; after the rewrite `65cf4be2…` |
| bare invocation | `python3 domains/06-qpt128-security-target/src/qpt128_finalization.py` | Python 3.12.3 | exit 2, usage message, by design | exit 2; stdout 0 bytes; stderr: `usage: qpt128_finalization.py [-h] (--self-test \| --report \| --explain)` and `error: one of the arguments --self-test --report --explain is required` | reproduced | the behaviour is intended and documented in `README.md` §2 and `docs/qpt128-finalization.md` §0; the recorded usage line names the versioned filename, this one the unversioned one (see "Differences that are expected, not discrepancies") |
| `--self-test` | `python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --self-test` | Python 3.12.3 | 19 tests OK, exit 0 | `Ran 19 tests … OK`, exit 0, stdout empty (unittest writes to stderr) | reproduced | all 19 test names identical to the recorded run |
| `--self-test` timing line | same | Python 3.12.3 | `Ran 19 tests in 0.042s` | `0.016s`, `0.029s`, `0.037s`, `0.038s`, `0.040s`, `0.044s` over repeated runs | reproduced-with-difference | timing only; the count and the verdict are identical. The build note anticipates "~0.02 s", the recorded log says 0.042 s, and the observed runs straddle both. No test content differs |
| `--report` | `python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --report` | Python 3.12.3 | the JSON the document's tables quote, exit 0 | 12,495-byte JSON on stdout, empty stderr, exit 0 | reproduced-with-difference | 204 value leaves, identical key set; **2 leaves differ from the recorded JSON, both display strings rewritten by the required scrub, no numeric leaf differs** — see below |
| `--report` determinism | same command, twice | Python 3.12.3 | identical output | byte-identical to `results/qpt128_report.json` on re-run | reproduced | the report is a pure function of the constants |
| `--explain` | `python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --explain` | Python 3.12.3 | **no recorded baseline** — the baseline log covers the bare invocation, `--self-test` and `--report` only | command executed: 8,247 bytes on stdout, empty stderr, exit 0; prose consistent with the placed source and with the report | not-run | the command runs; what is not-run is the **comparison**, because there is no recorded output for it. The reproduction is therefore of the invocation only |
| independent recomputation | `python3 domains/06-qpt128-security-target/results/ledger-independent-check.py` | Python 3.12.3 | all recomputed values agree with the regenerated report (self-consistency target; this check is new here) | exit 0; all 23 printed comparisons agree, and the boolean `RESULT:` line reads "all recomputed values agree with the report" | reproduced | loads the checker by path without modifying it, recomputes every scenario total, both D2 margins, the minimum repetition counts at `r` and `r−1`, the legacy-constant comparison and the quorum identities by its own route; output kept as `results/ledger-independent-check.txt` |
| model-premise rows | `python3 … --report` (+ test 16) | Python 3.12.3 | rows E6, E7, E8 and B0's rollback row are zero and labelled `model-premise` | confirmed in the report's `statuses` and `rows` maps | reproduced | the label was not upgraded; the nulls in the JSON are exact zeros |
| refutation record | `python3 … --report`, key `L1` | Python 3.12.3 | verdict `REFUTED as stated; restate as D1/D2 with gate accounting` | same string; `exceeds_two_pow_minus_128: true` | reproduced | the refutation was not softened; it is also recorded in `records/failed-assumptions.md` entry Q1 |
| source tree untouched | `python3 tools/check_pqt_baseline.py` (build work tree) | Python 3.12.3 | 1,157 baseline files, 0 changed/add/removed | 1,157 present, size changed 0, mtime changed 0, added 0, removed 0, PASS | reproduced | nothing was created, modified or deleted in the read-only source tree |
| published-repo scrub | `grep -rnE` for absolute paths, e-mail addresses and tool-vendor names across the domain; plus the scrub list of the source dossier | — | none present; no second-person address, no "turn", no AI-agent wording | none present | reproduced | the only remaining match for the word "user" is the cryptographic term `multi-user signature forgery (x64)` in a row name, plus the two places in this file that quote the recorded value being scrubbed |
| cross-domain paths resolve | `grep -rhoE 'domains/[0-9][^ )`,;:]*' docs README.md VERIFICATION.md \| sort -u` then test each | — | every referenced path is the map's `new_path` for that file | 26 references, 25 present at check time; the one absent is the D9 domain directory, which is placed separately | reproduced-with-difference | the references are the build map's `new_path` values; the Binius64 crate paths are prefixed with a note that they point into the excluded vendored tree, and line-number references that could not be re-verified are marked as the source's own |

## The two differences in `--report`

Diffed leaf by leaf against the JSON recorded for the same source:

| JSON pointer | recorded | observed here | why |
|---|---|---|---|
| `/definitions/D1` | `G<2^128 => Pr<1/3 (user target)` | `G<2^128 => Pr<1/3 (work-factor target)` | the published-repo scrub removes the conversational word "user"; "work-factor" is the term the same document uses for D1 everywhere else |
| `/L1/claim` | `pqt.md final theorem: Adv < 2^-128 for every QPT adversary (D3)` | `closing theorem of the research trail (docs/01-research-journey/pqt.md): Adv < 2^-128 for every QPT adversary (D3)` | bare filenames are replaced by repository-relative paths; the claim itself is word-for-word the recorded one |

Both are display strings in the JSON. Both edits are visible in the placed source file; neither
touches a number, a comparison or a verdict. The claim in `/L1/claim` is unaltered where it matters:
`Adv < 2^-128 for every QPT adversary (D3)`, and its verdict string is unchanged.

## Differences that are expected, not discrepancies

1. **The filename.** The sources are `qpt128_finalization_v1.43.py` and `QPT128_finalization_v1.43.md`
   in the source tree; the map's `copy` rows drop the version suffix, so the files placed here are
   `src/qpt128_finalization.py` and `docs/qpt128-finalization.md`. The usage message therefore names
   the unversioned file. The version is not lost: it is in the module's own header
   ("QPT-128 finalization — v1.43"), in `docs/qpt128-finalization.md`, and in the report's `version`
   key (still `1.43`).
2. **Paths inside the placed files.** Bare filenames of other project files were rewritten to
   repository-relative paths so the documents stand on their own, and line-number references that
   could not be re-verified are marked as the source's own line numbers rather than re-attributed.
3. **The results directory.** The build map places no files under `results/` for D6. `results/` here
   holds the `--report` output regenerated in this repository and the independent recomputation
   written for this domain; neither is a copied row.

## Not run, and why

| item | verdict | why |
|---|---|---|
| verifying every borrowed constant against the full texts of the cited papers | not-run | no network access and the papers are not in the tree; the sources' claim that the constants were checked against full texts is recorded as a **process claim**, not as a verification (`docs/theory.md` §14, §15 item 1) |
| re-deriving the DFMS, CFHL, HRS16 or GHHM bounds | not-run | out of scope for this domain; the ledger uses them as stated, and `docs/theory.md` §4 records the coefficient discrepancy (`22ℓ+60` here, `20ℓ+60` in D5, `72+40ℓ` in D4) rather than resolving it |
| the D5 and D7 domains' own self-tests and reports | not-run | other domains' builders verify those; this domain only resolves their file paths |
| the hidden-signer (B1) proof system under the 32 KiB certificate budget | not-run | no such proof system exists in the programme; that negative result belongs to `domains/07-compact-certificate-b0` |
| any solver, attack-lab or formal-prover run | not-run | none is used by this domain's evidence; the checker is self-contained |
| the `1.17·2^148` AES-256 Grover cost and the unsourced `12(q+154)³/2^n` as ledger terms | not-run | the first is quoted in the sources but charged nowhere; the second has no source and is kept only to measure the discrepancy, which the checker does (test 14) |

## Statement of what the numbers are

Every PASS/FAIL in this domain is an exact `Fraction` comparison. The logarithms in the report and in
the documents are computed in 60-digit decimal arithmetic, rounded to 3 or 9 decimals, and are
display only — the clearest case being Lemma L1's row, which prints `−128.0` for a bound that is
strictly greater than `2^−128`, with the strict comparison carried by the boolean beside it.
