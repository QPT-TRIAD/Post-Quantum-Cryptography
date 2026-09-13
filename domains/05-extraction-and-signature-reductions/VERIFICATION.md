# VERIFICATION — 05-extraction-and-signature-reductions

What was re-run while building this domain, what it returned, and how it compares with the recorded
baseline. Every command is written relative to the repository root. All paths in this file are
repository-root relative.

**The recorded baseline.** Nine verification logs were produced when the v1.34–v1.42 sources were
read: `ceqs29_extractor_v1.34.py.run.txt`, `joint_extractor_lift_v1.35.py.run.txt`,
`circuit_witness_extractor_v1.36.py.run.txt`, `signature_security_reduction_v1.37.py.run.txt`,
`slh_dsa_signature_reduction_v1.38.py.run.txt`, `signature_margin_sweep_v1.39.py.run.txt`,
`phase_ghz_security_check_v1.40.py.run.txt`, `hybrid_sampling_bound_audit_v1.41.py.run.txt` and
`slh_tree_conditioning_audit_v1.42.py.run.txt`, held in the build work tree's log directory. Each
log section carries the command, the interpreter version, an elapsed time **including** a shared
host-lock wait, the program's stdout and stderr as one stream, and an exit code.

**Environment for every row below.** Linux x86-64; Python 3.12.3, the interpreter the baseline was
recorded with. All nine scripts use the Python standard library only, so no other dependency applies
and no environment activation is needed to reproduce them. The recorded runs were wrapped in a shared
host-lock helper (`hostlock.py shared -- timeout 900 python3 …`); the runs here were made directly
with the same interpreter and no lock, so elapsed times are not comparable and nothing else is
affected. The machine was heavily loaded during this build — 12 cores, load average around 20, with
other domain builds running in parallel — which is visible in the slowest test suite's timing line
and nowhere else.

**Method.** For every item the program's output was captured as a single stream, stdout and stderr
merged, matching how the log was written. The capture was then compared **as a whole** against the
corresponding section of the recorded log, line by line, with a unified diff. Section boundaries are
the log's own 64-character separator lines; the log's host-lock line, absolute-path command header
and `# exit_code` footer line are not program output and were excluded from both sides before
diffing. Trailing blank lines and the log format's trailing-newline handling were normalised on both
sides. Exit codes were compared separately.

## Required table

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| placed source bytes | `sha256sum domains/05-extraction-and-signature-reductions/src/*.py` immediately after the copy, before any rewrite | — | the map records nine `sha256` values for the nine `original_path` rows of this domain | all nine matched the recorded hashes byte for byte | **reproduced** | verified at copy time. The files were then rewritten as the build contract requires (version suffix dropped from self-references, bare filenames replaced by repository paths, conversational provenance removed, a "Path note" appended). Current hashes are under "Hashes of the placed files" below. The map's recorded source sizes are correspondingly smaller than the placed sizes: `joint_extractor_lift` 24,572 → 25,554 bytes, `circuit_witness_extractor` 46,855 → 47,745, `ceqs29_extractor` 56,649 → 58,035 |
| machine-readable output, length sweep | `python3 src/signature_margin_sweep.py --json` | Python 3.12.3 | the 811,628-byte record captured in the v1.39 log; exit 0 | 811,628 bytes, exit 0 | **reproduced** | byte-identical. The re-run's stdout, the shipped `results/signature_margin_sweep.records.json` and the recorded section (after the log format's trailing-newline normalisation) are the same bytes: sha256 `30eda8d17c5f7d0070a14a9ea0dd0984d57ae1a2cce89b12564aa64dc3ffe270` |
| machine-readable output, certificate | `python3 src/ceqs29_extractor.py --certificate` | Python 3.12.3 | the 798-byte certificate captured in the v1.34 log; exit 0 | 798 bytes, exit 0 | **reproduced** | byte-identical, including `"irreducible": true` for the GF(2^512) modulus: sha256 `912178941200ef0fa708bde7357ae96b8a1d2f02934564d3c04bafdd33c8fc8f` |
| bare invocation, exit 2 by design | `python3 src/ceqs29_extractor.py` | Python 3.12.3 | exit 2; argparse names the required `--body0 --body1 --configuration` | exit 2; the same three arguments named | reproduced-with-difference | the program name in the usage and error lines is the unversioned one, and argparse re-wraps the usage line because the shorter name no longer needs the two-line break. Diff under "v1.34, bare invocation" |
| bare invocation | `python3 src/joint_extractor_lift.py` | Python 3.12.3 | exit 0; prints the module header, 12,063 bytes | exit 0; 13,045 bytes | reproduced-with-difference | three content differences, all required rewrites: two versioned self-reference usage lines, one provenance passage, one appended "Path note" |
| bare invocation | `python3 src/circuit_witness_extractor.py` | Python 3.12.3 | exit 0; prints the module header, 14,783 bytes | exit 0; 15,673 bytes | reproduced-with-difference | four hunks: the two usage lines, the provenance passage, the `[L1]` reference to the v1.35 record, and the appended "Path note" |
| bare invocation | `python3 src/signature_security_reduction.py` | Python 3.12.3 | exit 2; `one of the arguments --explain --self-test is required` | exit 2; identical text with the unversioned program name | reproduced-with-difference | program name only, two lines |
| bare invocation | `python3 src/slh_dsa_signature_reduction.py` | Python 3.12.3 | exit 2; the same argparse shape | exit 2; identical text with the unversioned program name | reproduced-with-difference | program name only, two lines |
| bare invocation | `python3 src/signature_margin_sweep.py` | Python 3.12.3 | exit 2; `one of the arguments --report --json --self-test is required` | exit 2; identical text with the unversioned program name | reproduced-with-difference | program name only, two lines |
| bare invocation | `python3 src/phase_ghz_security_check.py` | Python 3.12.3 | exit 2; the same argparse shape | exit 2; identical text with the unversioned program name | reproduced-with-difference | program name only, two lines |
| `--self-test` | `python3 src/ceqs29_extractor.py --self-test` | Python 3.12.3 | 20 tests, `OK`, exit 0 | `Ran 20 tests … OK`, exit 0, all 20 test names identical | **reproduced** | the timing line differs — see "Timing lines". The count, the names and the verdict are unchanged |
| `--self-test` | `python3 src/joint_extractor_lift.py --self-test` | Python 3.12.3 | 16 tests, `OK`, exit 0 | `Ran 16 tests … OK`, exit 0, all names identical | **reproduced** | timing line only: recorded `0.001s`, observed `0.001s` in one run and `0.002s` in another |
| `--self-test` | `python3 src/circuit_witness_extractor.py --self-test` | Python 3.12.3 | 27 tests, `OK`, exit 0 | `Ran 27 tests … OK`, exit 0, all names identical | **reproduced** | timing line only: `0.055s` recorded, `0.094s`–`0.132s` observed |
| `--self-test` | `python3 src/signature_security_reduction.py --self-test` | Python 3.12.3 | 23 tests, `OK`, exit 0 | `Ran 23 tests … OK`, exit 0, all names identical | **reproduced** | timing line only: `0.132s` recorded, `0.078s`–`0.189s` observed |
| `--self-test` | `python3 src/slh_dsa_signature_reduction.py --self-test` | Python 3.12.3 | 36 tests, `OK`, exit 0 | `Ran 36 tests … OK`, exit 0, all names identical | **reproduced** | timing line only: `0.136s` recorded, `0.078s`–`0.351s` observed |
| `--self-test` | `python3 src/signature_margin_sweep.py --self-test` | Python 3.12.3 | 13 tests, `OK`, exit 0 | `Ran 13 tests … OK`, exit 0, all names identical | **reproduced** | timing line only: `0.083s` recorded, `0.044s`–`0.159s` observed |
| `--self-test` | `python3 src/phase_ghz_security_check.py --self-test` | Python 3.12.3 | 12 tests, `OK`, exit 0 | `Ran 12 tests … OK`, exit 0, all names identical | **reproduced** | timing line only: `0.173s` recorded, `0.222s`–`0.440s` observed |
| tests and report | `python3 src/hybrid_sampling_bound_audit.py` | Python 3.12.3 | 10 tests, `OK`, then the report; exit 0 | identical in one re-run, including `Ran 10 tests in 0.028s`; in another re-run the only difference was the timing line, `0.038s` | **reproduced** | the report body matches line for line: 92.332482617, 120.988772745, `2^-128`, the state-test acceptance 1, the 45/89/128/177/178/179/186/189 table, and the closing `No sampling endpoint is substituted for epsilon_SLH.` |
| tests and report | `python3 src/slh_tree_conditioning_audit.py` | Python 3.12.3 | 10 tests, `OK`, then the report; exit 0 | identical except the timing line (`0.003s` recorded, `0.004s`–`0.008s` observed) | **reproduced** | both `UNESTABLISHED` status lines, the `2^-127` line, the `TCR_F` coefficient 3, the three parameter sets and the closing line match |
| `--report` | `python3 src/signature_margin_sweep.py --report` | Python 3.12.3 | 15,297 bytes on stdout, exit 0 | 16,189 bytes on stdout, exit 0 | reproduced-with-difference | **every table, threshold, status string and number is identical.** Three passages differ, all required rewrites: 18 lines added, 4 removed, +892 bytes. See "v1.39, `--report`". Both sides begin with the same single leading blank line |
| total test count | the nine test runs above | Python 3.12.3 | 167 tests across the band | 167 tests, all `OK`, every exit code 0 | **reproduced** | 20 + 16 + 27 + 23 + 36 + 13 + 12 + 10 + 10 |
| source tree untouched | `python3 tools/check_pqt_baseline.py` in the build work tree | Python 3.12.3 | 1,157 baseline files, 0 changed, added or removed | baseline 1,157 / present now 1,157 / size changed 0 / mtime changed 0 / added 0 / removed 0 / `RESULT: PASS -- source tree unmodified` | **reproduced** | nothing was created, modified or deleted under the read-only source tree |
| published-repo scrub | pattern scans over the whole domain directory for absolute local paths, e-mail addresses, a URL campaign parameter, AI-tool or vendor names, and conversational provenance | — | none present | none present; two word-level false positives | **reproduced** | the only hits are the ordinary word inside "proof-assistant formalization" (`src/signature_security_reduction.py` line 13, quoted in `docs/signature-reductions.md`) and the word "enrollment" in `src/slh_dsa_signature_reduction.py` line 81 |
| internal links resolve | extract every relative markdown link in the domain and test it on disk | — | every link resolves | 0 dangling links across all nine documents | **reproduced** | documents link to each other, to `results/` and to this file |
| cross-domain paths resolve | collect every `domains/…` reference in the domain and test each on disk | — | each is the map's `new_path` for that file | 4 distinct cross-domain paths, all present | **reproduced** | `domains/03-zk-carrier-experiments/src/authorization.py`, `domains/03-zk-carrier-experiments/docs/package-assessment.md`, `domains/03-zk-carrier-experiments/results/public-approval-audit.json`, `docs/01-research-journey/pqt.md`; the remaining `domains/…` references are this domain's own files |
| `history/` | `awk -F'\t' '$0 ~ /D5/'` over `records/file-map.tsv` in the build work tree | — | all nine D5 rows have `action=copy` | all nine rows are `copy`; no `copy-history` row exists for this domain | **reproduced** | there is therefore no `history/` directory. v1.37 and v1.38 are separate steps of the series with their own files, not superseded revisions of another file, and both are placed in `src/` in full |

## Differences recorded, not smoothed

Each difference below is a consequence of a rewrite the build contract requires, or of the machine's
load. The program name changes because the version suffix was dropped from the filename as the map
instructs; the content changes remove conversational provenance and replace bare filenames with
repository-relative paths.

### v1.34, bare invocation

```
-usage: ceqs29_extractor_v1.34.py [-h] --body0 BODY0 --body1 BODY1
-                                 --configuration CONFIGURATION
-ceqs29_extractor_v1.34.py: error: the following arguments are required: --body0, --body1, --configuration
+usage: ceqs29_extractor.py [-h] --body0 BODY0 --body1 BODY1 --configuration
+                           CONFIGURATION
+ceqs29_extractor.py: error: the following arguments are required: --body0, --body1, --configuration
```

The same three lines, re-wrapped because the program name is shorter. No argument is added, removed
or renamed.

### v1.35, bare invocation (module header)

Three hunks, 20 lines added and 5 removed, +982 bytes.

1. Two usage lines name the unversioned file:

```
-  python3 joint_extractor_lift_v1.35.py --self-test
+  python3 joint_extractor_lift.py --self-test
```

2. One paragraph of provenance was rewritten:

```
-This artifact makes no new claim about the source bytes: workspace maintenance
-removed the local files before this turn, so integration could not be checked.
-The v1.29 source package is needed again for work against its exact relation.
+This artifact makes no new claim about the source bytes: the v1.29 package
+was not available for inspection while it was written, so integration could
+not be checked. Its authorization code is in this repository at
+domains/03-zk-carrier-experiments/src/authorization.py, and work against that
+exact relation needs the package in full, prover and verifier included.
```

   The claim is unchanged — integration was not checked — and the rewritten text now says where the
   authorization code actually lives in this repository.

3. A 13-line "Path note" paragraph was appended, naming the file's own repository path, saying that
   all paths in the file are repository-root relative, giving the version-to-path mapping for the
   whole band, and stating that line numbers carried in the file are the source's own and were not
   re-verified.

### v1.36, bare invocation (module header)

Four hunks, 20 lines added and 6 removed, +890 bytes. The two usage lines, the appended "Path note",
and:

```
-The visible project record supplies R29's intended conditions, but workspace
-maintenance removed its implementation package. This update therefore does
-not claim source integration or an accepted original-goal quorum certificate.
+The visible project record supplies R29's intended conditions, but its
+implementation package was not available for inspection while this revision
+was written. It therefore does not claim source integration or an accepted
+original-goal quorum certificate.
```

and in the reference list

```
-[L1] joint_extractor_lift_v1.35.py, the preceding conditional joint-lift
+[L1] src/joint_extractor_lift.py (v1.35), the preceding conditional joint-lift
```

### v1.39, `--report`

Three hunks, 18 lines added and 4 removed, +892 bytes. Every number, threshold, table row and status
string in the report is identical, including the near-128 transition table (`b = 134` adaptive
`(5/4)·2^-128` fails, `b = 135` adaptive `(3/4)·2^-128` passes, `b = 134` known-static
`(59/64)·2^-128` passes), the `b_min = s + ℓ + 6` identity, the four-way budget `b ≥ 136 + ℓ` and the
search widths 266 and 393.

| Passage | Recorded | Observed here | Why |
|---|---|---|---|
| §"exact inversion" | "This turn does not claim to have supplied that function." | "This revision does not claim to have supplied that function." | conversational wording |
| §"validation" | "The quorum reduction coefficients come from the conversation's v1.38 artifact." | "The quorum reduction coefficients come from the v1.38 record, src/slh_dsa_signature_reduction.py." | conversational wording; the file is now named by its repository path |
| end of file | (nothing) | the appended 13-line "Path note" paragraph | repository self-containment |

### v1.42, rewrites with no output difference

Four conversational passages in `slh_tree_conditioning_audit_v1.42.py` were rewritten — three that
referred to the person who proposed the audited expression, and one session-wording phrase about an
unavailable document. The four now read "the comparison proposed in the research trail", "the
research trail proposed, without a matching theorem", "arithmetic of the unsourced expression from
the research trail", and "the full text was not available". These passages lie in the module header
and in a function docstring, that is, in text the recorded invocation does not print: the recorded
v1.42 log contains only the test run and the report, and its report body is what the re-run
reproduces. This is why no diff appears for this file. The term "the research trail" is defined in
each file's appended "Path note" as the record kept at `docs/01-research-journey/pqt.md`.

## Timing lines

The one line that varies between runs is the test runner's elapsed-time line. Recorded values are
from the baseline logs, which were taken through the shared host lock; observed values are from this
build, on a machine carrying a load average around 20 on 12 cores. The extractor suite is the band's
slowest — it does 32,768 table comparisons and several thousand exact polynomial operations.

| Run | Recorded | Observed |
|---|---|---|
| `ceqs29_extractor --self-test` | `Ran 20 tests in 0.718s` | `1.141s`, `2.611s`, `3.637s` over separate runs; 2.5–6.1 s wall including interpreter start |
| `joint_extractor_lift --self-test` | `Ran 16 tests in 0.001s` | `0.001s` in one run, `0.002s` in another |
| `circuit_witness_extractor --self-test` | `Ran 27 tests in 0.055s` | `0.094s`, `0.116s`, `0.132s` |
| `signature_security_reduction --self-test` | `Ran 23 tests in 0.132s` | `0.078s`, `0.139s`, `0.189s` |
| `slh_dsa_signature_reduction --self-test` | `Ran 36 tests in 0.136s` | `0.078s`, `0.266s`, `0.351s` |
| `signature_margin_sweep --self-test` | `Ran 13 tests in 0.083s` | `0.044s`, `0.150s`, `0.159s` |
| `phase_ghz_security_check --self-test` | `Ran 12 tests in 0.173s` | `0.222s`, `0.398s`, `0.440s` |
| `hybrid_sampling_bound_audit` | `Ran 10 tests in 0.028s` | `0.028s` in one run, `0.038s` in another |
| `slh_tree_conditioning_audit` | `Ran 10 tests in 0.003s` | `0.003s`, `0.004s`, `0.008s` |

Timing only. The test counts, test names and verdicts are identical in every case, no assertion
depends on elapsed time, and a different timing can be produced in either direction by waiting for
the machine to be idle or busy. Nothing here indicates a behavioural change.

## Differences that are expected, not discrepancies

1. **The filenames.** The sources are `ceqs29_extractor_v1.34.py`, `joint_extractor_lift_v1.35.py`,
   …, `slh_tree_conditioning_audit_v1.42.py`; the map's `copy` rows drop the version suffix, so the
   placed files are `src/ceqs29_extractor.py`, `src/joint_extractor_lift.py`, … The version is not
   lost: it is in each file's own first heading and in the prose of every document in this domain.
   Any line a program prints that contains its own filename therefore shows the unversioned name,
   including argparse's usage and error lines, which re-wrap to the shorter name.
2. **Paths inside the placed files.** Bare filenames of other project files were replaced by
   repository-relative paths, self-references now name the file by its repository path, and every
   file carries an appended "Path note". Line-number references that could not be re-verified are
   marked in that note as the source's own numbers.
3. **The log format is not copied.** The recorded logs wrap each run in an absolute-path command
   header, a host-lock line and an `# exit_code` footer. The build map places no files under
   `results/`, so that directory holds outputs regenerated in this repository instead: one
   `<script>.out.txt` per script, in the form `====…` / `$ python3 <name> [args]` / `----…` / the
   program's merged output / `----…` / `# exit_code: N`, plus the two machine-readable artifacts.
   Nothing in `results/` is a copied map row, and the two large artifacts are byte-identical both to
   a fresh run and to the recorded sections.

## Hashes of the placed files

Current state of `src/` and `results/`, after the documented rewrites. These are the values a reader
should compare against a checkout.

| file | sha256 |
|---|---|
| `src/ceqs29_extractor.py` | `d3404be2b52821ef0d23f8d67be123045d506a78de64f75b8d7c9b38781861e6` |
| `src/joint_extractor_lift.py` | `cdd86dc6da7c4dd1e698d60c0360e099b9ae069e863b34dbcedffd2a43cf79b0` |
| `src/circuit_witness_extractor.py` | `99fe936c9fd9bb03d56e0298bb5d4bcd18104d5af90e1e54f9ec2900e6bbf4b7` |
| `src/signature_security_reduction.py` | `3c5e89ae745cdc868a10e506a0aab5afaa0c01eb08902998b99f64eb21008e68` |
| `src/slh_dsa_signature_reduction.py` | `9d36e36ed8cb4018f2c225b52daa6a5a0a1d41c2d54486da62626ddf16a12ae0` |
| `src/signature_margin_sweep.py` | `c632c549a44f27d159bce464ac7d925b211ef8b0718852b2e9a127490cf8e952` |
| `src/phase_ghz_security_check.py` | `711f8e0f2ad44edc472065b95938f1cc237d3932bb0d4750c196847c22a9ccde` |
| `src/hybrid_sampling_bound_audit.py` | `ae656c8a900469fa5892fb6a18c8b5112efd4513027802de92f985765baaeef9` |
| `src/slh_tree_conditioning_audit.py` | `bdfa8cda40bd85424567d5d0582e1b550df988efb4af4eaa3e841d6658d59edb` |
| `results/ceqs29_extractor.certificate.json` | `912178941200ef0fa708bde7357ae96b8a1d2f02934564d3c04bafdd33c8fc8f` |
| `results/signature_margin_sweep.records.json` | `30eda8d17c5f7d0070a14a9ea0dd0984d57ae1a2cce89b12564aa64dc3ffe270` |

The source files total 323,886 bytes over 6,521 lines; `results/` totals 885,814 bytes over eleven
files.

## Scrub findings, each reviewed

| Pattern | Hits | Verdict |
|---|---|---|
| absolute local paths (a home directory, a temporary directory, a tilde path) | 0 | — |
| e-mail addresses | 0 | — |
| URL campaign-tracking parameters | 0 | — |
| AI-tool or vendor names | 0 | — |
| the ordinary English word inside "proof-assistant formalization" | 1 | false positive: `src/signature_security_reduction.py` line 13, quoted in `docs/signature-reductions.md` |
| the word "enrollment" | 1 | false positive: `src/slh_dsa_signature_reduction.py` line 81 |
| conversational provenance (`this turn`, `the user`, `conversation`, `workspace maintenance`) | 0 | — |
| the word "session" | 1 | `"KEM session succeeded"` in a test description in `src/slh_dsa_signature_reduction.py` line 223 — the cryptographic term, not a chat term |
| versioned filenames inside the placed files | 0 | every version label left in a placed file is a prose version label ("v1.35"), never a filename; the filename mapping lives in the appended "Path note" |

The source dossier's scrub list named the conversational passages and the log headers. All of those
passages are rewritten or removed in the placed files, and the log headers are not carried into
`results/`.

## What was not run, and why

1. **The R29 relation against its own prover and verifier.** No prover or verifier for the full R29
   relation exists in the source tree. That absence is the domain's central open item, and v1.35 and
   v1.36 both record it. There is nothing to run.
2. **A quantum compressed-oracle simulation.** No implementation exists in the source tree. The
   classical test doubles in v1.35 and v1.36 are what the authors wrote, and both files say the
   doubles are not the backend.
3. **Real ML-DSA-87 and SLH-DSA signatures.** The reductions model both endpoints symbolically with
   length-enforcing adapters. No implementation of either standard is called and no signature is
   produced or verified, so FIPS 204 and FIPS 205 conformance is not tested here.
4. **Physical quantum hardware, and any physical error rate.** v1.40 works in exact algebra over
   `Q[ζ]/(ζ⁴ + 1)`; the trace-distance parameter `η` is set to zero by assumption.
5. **`--explain` / `--proof` as separate runs.** They print the module header, which is already
   exercised by the bare invocations of v1.35 and v1.36. The bare invocations of the other seven
   scripts exit 2 by design, and the recorded logs contain that behaviour rather than an `--explain`
   run, so no run was invented to fill the gap.
6. **The v1.43 finalization material** — the gate-unit ledger, the signature-row charge and the
   compat-mode withdrawal. Those are held in domain 06 and were not re-derived here; this domain
   records the reductions they apply to. `docs/signature-reductions.md` §6 states the custody
   boundary explicitly.

## One discrepancy inside the record itself

The coefficient of the ordinary commit-and-open term differs between two placed files. v1.35 derives
`(20ℓ + 60)Q³/2^h + 20Q²·p_triv` from DFMS Lemma 4.1; the later v1.43 material cites DFMS Theorem
4.2 as `(22ℓ + 60)q³2^-n + 20q²·p_triv`. The direction is conservative in the later form
(`22 > 20`), but the exact theorem statement was not re-verified against the paper during this build
and the difference is not resolved here. Both forms are reproduced where they occur, neither is
edited into the other, and the discrepancy is flagged in `README.md`, in
`docs/joint-extractor-lift.md` §5 and in `docs/circuit-witness-extractor.md` §4.
