# `records/` — corrections, canonical audit records, provenance

This directory holds the part of the repository that is about the programme's own mistakes: the
register of hypotheses that were tested and refuted, the release record of the fixes, the canonical
copies of the audit ledger and its checklist, the findings of the verification pass run while this
repository was assembled, and the provenance of every file that is and is not here.

Nothing in this directory is a proof of anything. It is the record of what was believed, what the
experiments returned, what was repaired, and what a re-run does or does not reproduce. Its purpose is
that a reader can audit the repository's honesty rather than take its word for it.

## Files

| file | bytes | sha256 (first 16) | what it is |
|---|---:|---|---|
| `failed-assumptions.md` | 16,775 | `68628f0fad6e73d2` | append-only register of refuted hypotheses and harness mistakes. Copied byte-identical from the source tree; not edited here. |
| `fixes.md` | 5,044 | `a22c10fdf0fd3900` | the audit-fix release for findings F1–F5, with its own appended correction section. Copied byte-identical; not edited here. |
| `audit-checklist.md` | 23,850 | `cbf871af8cf0c744` | canonical copy of the S1–S6 audit checklist v2.1. Written by the digital-infrastructure package; links here are the canonical ones. |
| `audit-ledger.json` | 50,497 | `b6cc01f09ed01b27` | canonical copy of the audit ledger v2.1: per-test results, attack records, security-exponent table. |
| `verification-findings.md` | 34,055 | `1b16f33d273756b0` | the findings of the verification pass that ran while this repository was assembled — findings 1–8, in three kinds — with an appended addendum of five further findings (9–13) from `domains/10-digital-infrastructure/`'s own re-run after the repair. Each carries its command, environment, observed numbers and disposition. Authored for this repository. |
| `provenance.md` | 295,551 | `d37975f9db74cc13` | how the repository was assembled: the file map (one row per source file with digest, size, action and destination), the naming rules and the one deviation from them, and the exclusion policy in full. Authored for this repository. |
| `file-map.tsv` | 580,318 | `64c9424720c0434b` | the file map as data: `original_path`, `sha256`, `size`, `domain_id`, `action`, `new_path`, `notes`. This is the table `provenance.md` embeds, and the table `tooling/checks/verify-repository.py` checks the tree against. |
| `rewrites.tsv` | 127,547 | `eccc137ba42017d2` | one row per rewrite the assembly made, 267 rows: the text replaced, the files it was replaced in, the text that replaced it, and the reason. This is what turns a digest difference from a fault into a recorded decision. Column 2 is keyed by the **destination path** — the path inside this repository — so a row can be followed to the file it describes. 506 of its name occurrences are repository destinations; five more — the devnet and transcript files that were deliberately not copied here — are names from the read-only source tree, and the reason column of those rows says so. The reason column opens with `[mechanical]` (163 rows), `[judgement]` (72) or `[no-rewrite]` (32), the last marking a span the assembly found and deliberately left alone. **Columns 1, 3 and 4 are redacted for publication** — see below. |
| `scrub-report.tsv` | — | — | written by the integration scrub, not by this package: one row per line replaced (`path`, `line`, `rule`, `before`, `after`). Present only in a work tree that has run `tooling/checks/` against unpublished material; it is not part of this repository, because the lines it records are the ones being removed.

### Why `rewrites.tsv` is redacted

The first column of a rewrite row is the text that was **removed**, and what was removed is exactly
the class of string this repository must not carry: absolute paths of the machine the work was done
on, the scratch directory prefix, a campaign parameter, an assistant tool name. Publishing the table
as generated would republish, in the provenance record, the strings the provenance record exists to
document the removal of.

So the published copy replaces those spans with a placeholder that names the category, and leaves
everything else intact. Three categories occur in this table: `<redacted: machine path>` (41
occurrences), and one each of `<redacted: coding-tool name>` and `<redacted: assistant wording>`. The
rules cover more classes than the table happens to trigger. What a reader keeps is the part that does
work: which files were rewritten, how many spans, which replacement class, and the reason. What they
lose is the literal text, which they can recover from the source byte-for-byte using the file's
digest in `file-map.tsv`.

The redaction is a program, not an edit: `tooling/checks/redact-for-publication.py`, which applies
the same rules as `tooling/checks/scan-forbidden.py` and refuses to write its output if any rule
still matches anything the table would publish. Twenty-three of the 267 rows carry at least one
placeholder — 22 in the removed-text column, 8 in the replacement column, 2 in the reason column.

The `files` column is **not** redacted, and it names paths inside this repository, so every row can
be followed to the file it describes. The reason column is redacted in two rows only, where the
reason quotes the span it is describing.

The first four digests above are the **source digests**: `file-map.tsv` records the same values for
those four files, so each can be checked with `sha256sum` against the map, including the two this
package placed byte-identical and did not edit. The next two are the digests of the two documents
written for this package, as published. The last two are the digests of the two data tables the
assembly placed here: the map itself, and the rewrite table.

## How to read a correction entry

Every entry in `failed-assumptions.md` is one row of a seven-column table, in the order the
programme's own rule fixes:

| column | what it holds |
|---|---|
| `#` | the entry identifier — `Q1`–`Q6` (CE-QS / QPT-128), `I1`–`I8` (infrastructure program v2.0), `A1`–`A21` (audit v2.1), `A22`–`A26` (audit stack v0.1, the audit's own harness mistakes), `A27`–`A28` (devnet cross-references) |
| `Hypothesis` | the claim as it was actually held, not a summary written afterwards |
| `Experiment` | what was run to test it |
| `Result` | what came back, with the numbers the run produced |
| `Why it failed` | the diagnosis — the arithmetic, the mis-accounting or the missing premise |
| `Fix` | what replaced the claim; "abandoned" and "narrowed" are fixes too |
| `Regression test` | the test that holds the correction in place; where a test identifier is given, that test is the entry's authority |

Read the row as one argument: a claim is worth nothing once its test fails, and it is worth what its
regression test asserts, no more. The file states its own discipline on its first lines: entries are
never deleted, and the same discipline governs the release record `fixes.md`, whose original table
cell for the F2/F4 fixes still reads `16/16` and is superseded by the appended correction section
without that cell being edited.

Two labels are used inside the entries and are the source's, not this package's: a *finding* (F1–F6)
is a defect found in code, rated by security impact; an *entry* (Q, I, A) is a belief that a test
refuted or narrowed. Where an entry's own wording was later found to overstate what was measured,
that is recorded as a finding of the verification pass in `verification-findings.md`, not by editing
the entry.

## The standing rule

**A claim that a re-run does not reproduce is withdrawn in public, with the reason and the date, in
place.** The claim is not quietly edited, not removed, and not left standing while a footnote denies
it. The withdrawal is written where the claim was made, or in a document that the claim's own text
points to, and the number that failed to reproduce is named together with what was observed instead.

Two worked examples ship in this directory:

- `failed-assumptions.md` entry `A28` (2026-09-13) withdraws the hash-signature property-layer count
  "16/16" that `fixes.md` had recorded. The reason is exact: the property module builds a mixed
  LMS/LM-OTS parameter pair at import, a construction the F3 fix refuses, so the suite fails at
  collection and executes no tests. The rest of the same line — 16 passed for Mode B, 7/7 for the
  Mode B v1.51 self-test — reproduced and is kept.
- `verification-findings.md` records, in this package, **eight findings of this pass, in three
  kinds**. Those where **a re-run contradicted the record**: a recorded PASS that does not reproduce
  (the S1-011 Grover slope assertion), three suites that would not run as shipped, an unseeded
  simulator whose recorded minimum is one sample of a random value, and a recorded statement about a
  formal module that the surviving revision of the module contradicts. And those where **reading the
  record against its own output showed it counted something that did not happen**: a published figure
  the sources do not support (the operator-ledger amendment counts, and the decomposition beside
  them), and a suite whose "5/5" counts a control that was skipped and one that cannot fail at that
  layer. Two further entries record what the assembly changed (wordings and machine-specific paths
  removed) and a hazard found while checking (a checker whose entire pass criterion disappears under
  interpreter optimisation). An appended addendum records five further findings — 9 to 13 — from
  `domains/10-digital-infrastructure/`'s own re-run after the repair; they are kept apart because
  they are a second pass over the same ground, not corrections to the eight.

A reader who wants to check whether the rule is followed should re-run the regression test named in
the row. Where a test cannot be run here — because a dependency, a toolchain or a devnet is missing —
`verification-findings.md` and each domain's `VERIFICATION.md` say so, and say which one.

## Why these findings are published

A repository that reports its own verification can be read in two ways: as a set of claims, or as a
record that includes the corrections *to itself*. This directory is the second kind. Its findings
name a PASS that a re-run does not reproduce, a suite total that counted a control which never
executed, a figure that appears in the programme's own reading record and is not in the document it
describes, and a checker that can be made to report complete success while its expectations are
knowingly false. Every one of them is published with the command that shows it, the environment it
was run in, and the numbers that came back — rather than corrected quietly and reported only once it
passes.

Two kinds of finding are kept apart on purpose, because they are found in different ways and a
reader should be able to see which is which. A finding of the first kind needs a **re-run**: the
recorded result is reproduced as a command and the command returns something else, or returns
nothing at all. A finding of the second kind needs only **the record's own output**: it counts an
event that the same output says was skipped, or its figures do not add up. The second kind is the
more uncomfortable of the two, because nothing failed — the number was simply never true, and it sat
in a summary line that everyone downstream read as a pass.

The alternative to publishing them is a repository whose own verification is only ever reported when
it passes. That leaves a reader unable to tell a claim that survived checking from one that was never
checked, and with no way to calibrate the rest of the record. Publishing the failures is what makes
the passes mean anything.

## Notes on the byte-identical files

`failed-assumptions.md` and `fixes.md` are copied byte-identical, as the historical record. Two
consequences a reader should know about:

1. **They refer to each other by their original filenames.** Inside them, `FAILED_ASSUMPTIONS.md` is
   this directory's `failed-assumptions.md`, and `FIXES_v2.2.md` is this directory's `fixes.md`. The
   version suffix in the second name identifies the release, not a revision of the document.
2. **They refer to material that is not in this repository.** The devnet kit's
   `reference/HASHES.sha256` is the manifest of immutable reference files; the kit belongs to a
   separate ledger repository and nothing from it is copied here (see `provenance.md`). Entry `A27`
   concerns a devnet test result and names a devnet run; the node code is out of scope for this
   repository, and the result is summarised in the authored devnet-evidence chapter under `docs/`.

Nothing else in these two files was rewritten, reordered or trimmed.

## What these records do not establish

- They do not upgrade any claim. A row that records a measurement is still a measurement, and a row
  that records a simulation (the Grover law) is still labelled a simulation.
- They are not evidence for the claims of the domains they name. The authority of a row is its
  regression test, and the test lives in the domain that owns the code.
- The audit checklist total "70/70 tests pass" is the state of the suites when the checklist was
  generated. It includes S1-011, which is flaky; `verification-findings.md` records the measurement
  and the disposition.
- The operator ledger's 116 amendments are corrections made in a document, not verified theorems.
  The measurement of how many of them have an executable witness or a citation is recorded in
  `verification-findings.md` and worked through in `domains/04-operator-ledger/`.

## Where to go next

- The claims themselves, with their tests and re-runs: `domains/<NN>-<name>/`, each with its own
  `README.md` and `VERIFICATION.md`.
- The construction, the target and the games: `domains/06-qpt128-security-target/`,
  `docs/03-construction/`, `docs/04-security-and-validation/`.
- The audit suites the two canonical records describe: `domains/10-digital-infrastructure/`.
- How to rebuild the environment before re-running anything: `tooling/`.
