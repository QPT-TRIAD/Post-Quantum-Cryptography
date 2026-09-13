# results/ — what is in this directory, and where each file came from

Two kinds of file are here: **the recorded result**, shipped from the source tree and byte-identical
to it, and **this build's re-run artifacts**, produced inside this repository in the pinned
environment. They are kept apart below, because only the first is the record and only the second is
reproducible from this repository.

---

## 1. The recorded result

| file | sha256 | source | what it is |
|---|---|---|---|
| `attack-lab-results.md` | `7638c8ca156fd41c7a76631799e9b84834388b243aa5c88b8d46205e7213bed5` | `attack_lab_results_v1.51.md` | the write-up of both harnesses, v1.51/v1.52, dated 11 September 2026 |

This file is a `copy` row of the programme's file map and is shipped **byte-identical**: its sha256
equals the source's, so it is not listed as a rewrite. It names files by their historical, versioned
names; the map from those names to the repository's paths is in `../README.md` §6.

It is the record of a run made **before** this repository existed, on the source tree, under a shared
host lock (`hostlock.py shared`, which serialized the heavy runs against the other builds of that
session), from the source tree's root directory with `PYTHONDONTWRITEBYTECODE=1`. The recorded
figures this domain is checked against are in it: 24 violation attempts with 0 successes; the fitted
exponents; the extrapolation errors; the ledger rows.

## 2. This build's re-run artifacts

Every file below was produced inside this repository during this build. Each carries the command that
made it, the working directory, the environment, the exit code and the wall clock, either in its own
header (`*.txt`) or in `../VERIFICATION.md`.

| file | bytes | how it was produced | exit | wall |
|---|---:|---|---:|---:|
| `attack-lab-run.txt` | 5,709 | `python3 ceqs_attack_lab.py --all` from `../src` | 0 | 113.51 s |
| `games-run.txt` | 3,943 | `python3 ceqs_games.py --all` from `../src` | 0 | 148.19 s |
| `attack-lab-report.json` | 13,268 | `python3 ceqs_attack_lab.py --all --json` from `../src` | 0 | 69.06 s |
| `games-report.json` | 14,124 | `python3 ceqs_games.py --all --json` from `../src` | 0 | 88.78 s |
| `probe_exit_codes.py` | 6,992 | written by this build; reads both harnesses, writes nothing in the repository | 0 | — |
| `probe_exit_codes.txt` | 1,320 | `python3 probe_exit_codes.py` from this directory | 0 | — |

**Environment for all of them:** the programme's pinned interpreter, Python 3.12.3; numpy 2.4.6 for
the attack lab's Grover simulation (the games harness does not use numpy); `PYTHONDONTWRITEBYTECODE=1`
so no `__pycache__` is written beside the sources. No other package, solver or service is involved.

**Why the wall clocks differ from the record, and why they differ from each other.** The recorded runs
(54.5 s and 126.1 s) were wrapped in a shared host lock, serialized against the other builds of that
session. The runs captured here were made while other domain builds of this repository were running,
and repeated runs of the same commands move by up to 3× in **both** directions: the lab's `--all` was
measured at 54.95 s when the host was quiet and at 113.51 s under load, the games' `--all` at 56.11 s
and 148.19 s. Another package measured the same files here at 87.6 s, 122.7 s and 168.58 s. The measured
*values* are identical in every one of those runs; only the wall clock moves, which is why no claim in
this domain rests on one. `../VERIFICATION.md` carries each observation and marks those rows
`reproduced-with-difference`.

**Why the JSON files exist.** `--json` is a mode of both harnesses that prints the report and nothing
else. Keeping the report means a reader can check the domain's numbers mechanically instead of
re-reading prose: `../VERIFICATION.md` records a one-line check that reads
`A_negative.successful_violations` and `A_negative.attempts` from `attack-lab-report.json` and exits
non-zero unless they are `0` and `24`. The two report files are the output of the *last* capture run,
made after the earlier captures had been made under contention; each was diffed field by field
against `attack-lab-run.txt` / `games-run.txt` and agrees with them in every measured value.

**`probe_exit_codes.txt` is a regenerated file, and this matters for byte comparison.** The first
version of that output embedded the absolute path of the domain's `src/` directory, which names the
machine the file was made on. The probe was changed to print the directory relative to the repository
root, and the file was regenerated. **A reader who re-runs the probe will see output identical to the
stored file except for the in-run test timings** — the absolute path that appeared in the original
run is deliberately absent from the stored copy, and no other byte was altered. The regenerated file
contains no absolute path: checked by scanning it for `/home/`, `/Users/` and `/tmp`, with no match.

## 3. What is *not* here

- **No output of the unshipped SAT experiments.** They are not in this repository and neither are
  their logs; see `../README.md` §5 and `../docs/validation-status.md` §6.
- **No production-parameter runs.** The record's §8 (prover and verifier at 2^20 and 2^22 trees,
  30,684 B and 28,708 B certificates) is a C-prover measurement that this domain does not re-run; its
  numbers are quoted from the record and labelled as such.
- **No third-party solver output.** Neither harness invokes one.
