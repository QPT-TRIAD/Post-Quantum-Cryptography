# Verification record

What was executed for this domain in this repository, on what, with what observed output, and what
was not executed and why. Every command below was run in the pinned environment described in
§"Environment". Verdicts use the programme's vocabulary: `reproduced`, `reproduced-with-difference`,
`not-reproducible`, `not-run`.

| # | Item | Command | Environment | Expected (recorded) | Observed | Verdict | Notes |
|---|---|---|---|---|---|---|---|
| 1 | v0.7 finite-state checker | `python3 pqaqc_finite_state_check.py` (cwd `src/`) | Python 3.12.3, Linux x86_64, 12 cores | `results/pqaqc_modelcheck.txt:15-28` | byte-identical output, exit 0, 0.70 s wall, 25,868 kB max RSS | `reproduced` | 5 safe models, 3 expected-fail mutants, 1 recovery path |
| 2 | v0.6 finite-state checker | `python3 pqaqc_finite_state_check-v0.6.py` (cwd `history/`) | same | `history/pqaqc_modelcheck-v0.6.txt:4-7` | byte-identical output, exit 0, 0.22 s wall, 17,372 kB max RSS | `reproduced` | 3 models plus one set-arithmetic check |
| 3 | Configuration/module invariant names | scan `formal/epoch-barrier.cfg` for `INVARIANT` lines, match each against `^NAME ==` in `formal/epoch-barrier.tla` | same | `results/pqaqc_modelcheck.txt:32` | 9 names, 9 defined, 0 missing | `reproduced` | the recorded line was produced against the v0.7 artifacts, which are not preserved; this check is run against the surviving pair |
| 4 | TLA+ model-check, v0.6 module | `java -jar tla2tools.jar -config formal/epoch-barrier.cfg formal/epoch-barrier.tla` (the intended form) | Java 21.0.12 present; no `tla2tools.jar` on the filesystem; no other TLA+ tooling | `history/pqaqc_modelcheck-v0.6.txt:9-11`: "TLC status: NOT RUN in this environment." | not executed | `not-run` | **no TLA+ tools are installed here**, so no run was possible and none was invented; the recorded lines are quoted as recorded in §"Recorded TLA+ items" |
| 5 | TLA+ model-check, v0.7 module | none possible | same | `results/pqaqc_modelcheck.txt:9-11` | not executed; the v0.7 `.tla` and `.cfg` are not preserved in this repository | `not-run` | the recorded `ARTIFACT CONSISTENCY` lines are quoted as recorded; see §"Recorded TLA+ items" for why one of them cannot be verified and one does not hold of the surviving module |
| 6 | Executable copies byte-identical | `sha256sum` against the file map | same | map hashes | `src/pqaqc_finite_state_check.py` `4ebce814…`, `history/pqaqc_finite_state_check-v0.6.py` `d1a3d162…` | `reproduced` | copies are unmodified |
| 7 | Recorded outputs byte-identical | `sha256sum` against the file map | same | map hashes | `results/pqaqc_modelcheck.txt` `24d2ab20…`, `history/pqaqc_modelcheck-v0.6.txt` `4af592d3…` | `reproduced` | copies are unmodified |
| 8 | Source tree untouched | `sha256sum` of all ten mapped source files against the file map | same | map hashes | all ten match | `reproduced` | nothing was created, modified or deleted under the source tree |
| 9 | Document fidelity of copied text | `diff -u <source> <copy>` for the four copied documents | same | listed deltas only | exactly the deltas listed in §"Document deltas" | `reproduced` | no other edit to any body line |
| 10 | Control-byte scrub | scan every file for bytes `< 0x20` other than tab, LF and CR | same | none | 0 files | `reproduced` | the two corrupted LaTeX control bytes in the v0.7 record were repaired (row 9) |
| 11 | Citation resolution | every `path:line` and bare `:line` pointer in the three authored documents resolved against the cited file | same | all resolve, none out of range | all resolve; all ranges within the cited files | `reproduced` | pointers were checked mechanically and by reading the resolved lines |
| 12 | Module name vs file name | read `formal/epoch-barrier.tla:1` | same | a TLA+ identifier cannot contain a hyphen | `MODULE epoch_barrier` in `formal/epoch-barrier.tla` | `reproduced` | a deliberate, documented deviation from the file map; see §"Deviations" |

## Environment

- Python 3.12.3 (GCC 13.3.0), from the programme's pinned virtual environment.
- Java: OpenJDK 21.0.12 (`21.0.12+8-1-24.04-Ubuntu`), present on `PATH`.
- TLA+ tooling: none. A filesystem-wide search for `tla2tools*.jar` returns nothing, and no other
  model-checking tool is installed.
- Host: Linux 7.0.0-31-generic, x86_64, 12 cores.
- Both checker runs were single-process, standard-library-only, with no file I/O and no network.

## Recorded TLA+ items, quoted as recorded

These are the whole of the recorded TLA+ output. They were produced by the earlier work recorded in
the shipped files, not by this repository, and they are quoted here exactly as shipped.

From `results/pqaqc_modelcheck.txt:9-11`:

```
The TLA+ artifact was also checked mechanically for CFG/TLA invariant-name
consistency. Native TLC was not run in this runtime because tla2tools.jar is
not installed locally.
```

From `results/pqaqc_modelcheck.txt:30-33`:

```
ARTIFACT CONSISTENCY
--------------------
PASS every INVARIANT named in the CFG is defined in the TLA+ module
PASS Domains and Preps are referenced by the actual TLA+ state/actions
```

From `history/pqaqc_modelcheck-v0.6.txt:9-11`:

```
TLC status: NOT RUN in this environment.
Reason: Java is installed, but tla2tools.jar is not available locally and external binary acquisition is blocked.
These PASS results are from the independent exhaustive Python checker, not TLC/TLAPS.
```

Three points, all verifiable by reading the preserved artifacts:

1. No line in either file reports a TLC execution. There is none: the model has never been given to a
   model checker, and this repository did not run one either.
2. The first `ARTIFACT CONSISTENCY` line is true of the surviving pair in the weaker sense recorded in
   row 3. It cannot be re-verified against the artifacts it was produced from, because those are the
   v0.7 files and they are not preserved.
3. The second `ARTIFACT CONSISTENCY` line does **not** hold of the surviving v0.6 module: `Epochs`,
   `Domains` and `Preps` each occur exactly once in `formal/epoch-barrier.tla` — in the `CONSTANTS`
   line — and are referenced by no state, guard or action. The line is consistent with the v0.7 module
   as the research record describes it, where conflict domains and preprocessing objects became real
   model dimensions.

## Document deltas

Four copied documents carry a trailing repository note, and three of them carry additional listed
edits. Everything else in each file is byte-identical to its source, as the `diff` output shows.

| File | Deltas |
|---|---|
| `docs/research-proof-documentation.md` (v0.7) | 5 hunks, 20 changed lines: three placement rewrites that remove third-party environment references (at source lines 64, 2142 and 2651); two repairs of corrupted LaTeX control bytes (`\boxed`, `\text`); a "not present in this repository" mark on the two artifact-list entries for the v0.7 TLA+ files; the trailing repository note |
| `history/research-proof-documentation-v0.6.md` | 5 hunks, 13 changed lines: the same three environment-reference rewrites (at lines 64, 1965 and 2431); the two artifact-list marks; the trailing repository note |
| `history/research-proof-documentation-v0.5.md` | 2 hunks, 9 changed lines: the two artifact-list marks; the trailing repository note |
| `docs/frontier-conflict-extraction.md` (v0.1) | 1 hunk, 7 changed lines: the trailing repository note only |

The environment-reference rewrites remove wording that described the machine of an earlier run
("this runtime", "external binary acquisition is unavailable here") and state the same fact without
the third-party environment detail. They change no claim about the artifact, the model or the tooling.
The LaTeX repairs restore a backslash that a control byte had replaced, so that the two commands
typeset as intended.

## Deviations

- `formal/epoch-barrier.tla` is a copy of the v0.6 module with two changes: the `MODULE` line reads
  `epoch_barrier` instead of `PQAQCEpochBarrier_v0_6`, and a trailing comment block records
  provenance. The rename is forced by the file map's destination path: a TLA+ identifier cannot
  contain a hyphen, so no valid module name can equal the file name `epoch-barrier.tla`. TLA+ tooling
  expects the two to match, so a TLC run needs the file copied or renamed to `epoch_barrier.tla`, or
  the module line changed back. This is the only deviation from a byte-identical copy among the
  copied documents and artifacts, and the only one that alters a copied file's non-comment content.
- `formal/epoch-barrier.cfg` is byte-identical to its source apart from a trailing comment block
  recording the same facts.
- The two executable copies and the two recorded-output copies are byte-identical to their sources
  and carry no note.

## Not run, and why

- **TLC and TLAPS for any revision of the epoch-barrier model.** No TLA+ tooling is installed in this
  environment: Java is present, `tla2tools.jar` is not, and no model checker was installed for this
  work. Nothing in this repository claims a model-checking result. The recorded TLA+ lines are quoted
  as recorded, with the quotes marked.
- **The v0.7 TLA+ module.** Not preserved in this repository, so it could be neither inspected nor
  run.
- **Refinement, fairness and liveness.** The surviving specification has no fairness conjunct and no
  refinement mapping to a base consensus protocol. Neither is checked here, and the base protocol's
  state machine is not yet frozen.
- **Cryptographic security of any primitive.** Nothing in this domain's verification is a
  cryptographic proof. The threshold-support interface, the evidence-framing bound and the
  boundary-uniqueness bound are assumptions and reduction sketches in the source; the checker results
  are bounded state exploration over finite abstractions.

## What still has to be validated

1. Run the v0.7 model under TLC with safety only, once a toolchain is available, in an environment
   that has said toolchain (recorded requirements: `docs/research-proof-documentation.md:3078-3089`).
2. Reproduce the checker's invariants inside TLC, including the derived boundary-finality model that
   the surviving TLA+ module cannot represent.
3. Freeze the base consensus protocol's state machine, then write the refinement mapping that
   connects any of these models to an implementation.
4. Treat the operational terms — durable non-rollback storage, query budgets, setup — as production
   obligations, not cryptographic negligibles; a rollback event on a restore path is recorded against
   this domain's assumptions.
