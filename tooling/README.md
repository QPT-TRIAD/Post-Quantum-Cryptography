# `tooling/` — rebuild the environment, run the repository

This package is the operational half of the repository. Everything else records what was done and
what was found; this directory records **how to stand the same environment up and how to re-run the
same commands**, so that a reader who arrives with nothing but a clone can reach the recorded
results and check them against what they observe.

It answers four questions:

| Question | File |
|---|---|
| What do I have to install, and in what order? | `environment.md` |
| What is each third-party package, and how far can I trust it? | `packages.md` |
| What do I run, in which directory, and what counts as a pass? | `run-everything.md` |
| Which script needs which package, and what breaks without it? | `imports.md` |
| What was actually observed on the machine that recorded the results? | `VERIFICATION.md` |

## Two paths through this package

**Path 1 — rebuild the environment.** Follow `environment.md` end to end. It builds one pinned
Python environment, a second one that reproduces the container mathematics pins, a locally compiled
liboqs 0.16.0, and the three formal tools (Tamarin, Maude, ProVerif) plus GraphViz. It needs no
root, and it is a sequence of downloads, builds and package installs rather than a long compute job:
the only recorded build time is liboqs at 2 min 54 s on 12 cores, and no total wall time was
recorded for a rebuild from scratch. Then run `run-everything.md` from the top.

**Path 2 — reuse an environment you already have.** If an environment already exists with the
layout `environment.md` describes, set `PQT_ENV` to it, source `activate.sh`, and go straight to
`run-everything.md`. Nothing else in this package needs to be executed; `VERIFICATION.md` tells you
which versions the recorded results came from, so you can tell me whether your environment would be
expected to reproduce them.

## What you must supply yourself

Two things are deliberately **not** in this repository.

1. **The read-only research tree.** The harnesses in `domains/11-independent-audit-stack` read their
   input files from it at run time. Point at your local copy with the `PQT_SRC` environment variable.
   Several scripts in the tree read `PQT_SRC`, and `tooling/activate.sh` is the script that sets it:
   if it is unset, the activation script prints one sentence saying what the variable is for and how
   to point it at a local copy, and everything that needs the tree reports itself as not run rather
   than guessing a path.
2. **The NIST ACVP conformance-vector files.** The primitives cross-check needs five
   `internalProjection.json` files. They are not distributed here;
   `domains/11-independent-audit-stack/primitives/vectors/SOURCE.txt` records the upstream commit and
   the SHA-256 of each file so you can fetch and check them.

A third item is optional. `pqcrypto` 0.3.4 is installed from PyPI like every other distribution; the
wheel that the recorded runs used is not redistributed, but its digest is recorded so you can check
the copy you install. `environment.md` §4 has the command.

## Using the activation script

```sh
export PQT_SRC=/path/to/research-tree
source tooling/activate.sh
```

- Write those as two lines. `PQT_SRC=/path/to/research-tree source tooling/activate.sh` looks
  equivalent and is not: in bash the assignment on a `source` command's own line is undone the
  moment that command returns, so `PQT_SRC` is unset again in the shell that then runs the
  harnesses, and they report themselves not run. The activation script says this when it finds the
  variable unset, and `environment.md` §3 lists what reads it.
- No machine-specific path appears in `activate.sh`. The environment root is derived from the
  script's own location, so the repository can be cloned anywhere and still work. Set `PQT_ENV`
  before sourcing only if the environment lives outside this directory.
- It exports `PQT_ENV`, `PQT_SRC`, `PATH` (the formal tools), `MAUDE_LIB`, `OQS_INSTALL_PATH`,
  `LD_LIBRARY_PATH`, `PKG_CONFIG_PATH` and `PYTHONDONTWRITEBYTECODE=1`. `environment.md` §3 lists
  what reads each one.
- It does not fail when something is missing. If the Python environment is absent it says so and
  carries on, because the formal-tool half of the tree does not need it, and the reverse is also
  true. A missing tool surfaces at the step that needs it, as `NOT RUN` with the reason, never as a
  silent pass.

## Conventions this package follows

- Every version string in these documents was read from the live environment with the command shown
  next to it in `VERIFICATION.md`. Nothing is quoted from a ledger or a memory of one.
- Run times in `run-everything.md` are the times recorded by the verification pass that produced
  this repository's results. They are measurements, not estimates, and they are labelled with the
  host they came from where the host matters.
- Where a step could not be run in this environment, it is written down as not run, with the reason
  and what would be needed to run it. `VERIFICATION.md` is the complete list.
- Nothing in these files is a statement about the cryptography. They say what ran, on what, with
  what result, and what did not run.

## The repository's own gates

`checks/` holds the four scripts that gate this repository rather than any result in it. Three of
them read the data under `records/`: `records/file-map.tsv`, one row per file (where it came from, its
digest, where it belongs), and `records/rewrites.tsv`, the files that differ from their source with
the class of change made — the map check reads both, the redaction reads the rewrites, and the link checker
reads the map to tell a name that *should* be absent from one that should not. Run them from the
repository root on a fresh clone; none of them needs the research tree, a virtual environment, or any
package outside the standard library. `VERIFICATION.md` §4.3 records what each one printed when it
was last run against this repository.

- **`checks/verify-repository.py` — is every file here accounted for?** Every copy row present at its
  destination and at the digest the map records, unless the row is listed as a rewrite; nothing
  present that neither the map nor the repository's own authored documents explain; no empty file;
  no malformed map row. Exit 0 means all of that holds. A non-zero exit means a file is missing, a
  digest differs without a recorded reason, or a file arrived that nobody decided to publish — the
  output names each one, and those are the three things to clear before publishing. Its `sha256
  differences` line prints two numbers and is worth reading in that order: first the count it could
  **not** match against a rewrites row, then the count it could, in brackets — so `0 (explained by
  rewrites: 132)` is a pass with 132 recorded differences and no unexplained ones, not a count of 132
  problems. Run the command and read the `HASH` lines rather than the bracketed number alone;
  `VERIFICATION.md` §4.3 records what this gate reported when it was first run here, the
  column-semantics disagreement behind that reading, and the run that now passes.
- **`checks/scan-forbidden.py` — does anything here carry a string that must not be published?** Assistant
  and vendor names, attribution phrases, machine-specific absolute paths, campaign parameters,
  e-mail addresses, and credential shapes. Exit 0 means none of the six categories matched. A
  non-zero exit means at least one file matched, and the file, the line and the category are
  printed. One file is exempt by construction: the scanner's own source has to contain the strings it
  searches for — the attribution phrases and path prefixes written out, and the name alternation
  assembled from fragments so that the published file does not itself carry the names — so it skips
  itself, by identity, not by name, and says so on every run. The exemption is positional: it fires
  on the copy that is executing, so an outside copy of the scanner reports the rule table against
  itself. `VERIFICATION.md` §4.3 records both runs, and the count each one reported.
- **`checks/redact-for-publication.py` — can the rewrites table be published as it stands?** No: its
  before-text is exactly what the scrubbing pass removed, so publishing it raw would republish the
  strings it exists to document the removal of. The script is meant to rewrite the table so that each
  removed span becomes a placeholder naming its category, keeping everything with evidentiary value —
  which files, how many lines, which class of change, and why — and dropping the string, sharing its
  rule set with the scanner instead of defining a second copy. Run with both paths given — its
  defaults point at `tooling/maps/`, which this repository does not have — it exits 0 and prints how
  many rows it read and how many spans it redacted per category. **When first run here it did not
  start at all**, because it imported its sibling by module name and the sibling's name has a hyphen
  in it; that was reported and has since been fixed, and `VERIFICATION.md` §4.3 records both the
  traceback it used to print and the output it prints now. The script's own reading of the published
  table is the useful part either way: `rows with redaction: 0` says no span of this table matches any
  forbidden-content rule, which is the property a published rewrites table is supposed to have.
- **`checks/check-links.py` — does every reference here point at something that exists?** A tree assembled
  from another tree by renaming and re-placing files is where a document keeps naming a file by its
  old name and reads fine while sending the reader nowhere. It checks markdown link targets, and
  backticked names that look like file paths, in two buckets: names the file map lists as *sources*
  (which are absent on purpose — that is what a copy is) and names nothing accounts for. Exit 0 means
  every markdown link resolves. A non-zero exit means at least one link does not, and those are
  printed; the code-span list is not a pass/fail condition, because a `not-run` record legitimately
  names an artifact that is not here, and it is printed for a human to read rather than acted on.

## Where the containers fit

`audit-stack/Dockerfile` and `audit-stack/Dockerfile.math` build the audit-stack layers in
containers, as a second, independent way of realising the environment. `Dockerfile.math` was built
and run, and its log records all eight mathematics groups reproduced. The full-stack image was never
built; treat everything that depends on it as untested. Both Dockerfiles were placed in this
directory by the package that owns them; `environment.md` §8 says what each needs, and where the
scanner's reach stops for a file whose suffix it does not list.
