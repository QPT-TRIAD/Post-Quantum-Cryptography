# VERIFICATION — docs/05-devnet-evidence

**Verification mode: transcription, not reproduction.** No row in this package was produced by a run
in this repository. The devnet runs happened elsewhere — on the ledger repository's own kit, on a
separate host — and what exists here is the *record* of them. Nothing in this tree can re-run a
devnet: the ledger implementation, its harness, its fixtures and its binaries are excluded from this
repository by the file map (`exclude-triad`; the devnet kit itself is excluded because it belongs to
a separate repository). What was checked here is therefore different in kind from the other packages'
verification pages: not "the command reproduced the number", but **"the number in the page is the
number in the record it names, the arithmetic in the page is the record's own arithmetic, and the
identifiers resolve"**. Every row below states which of those it is.

Verdicts used here: `transcribed-verified` (the value written in this package agrees with the field of
the named record), `reconciled` (arithmetic re-checked from the record's own inputs),
`reproduced` (a command run in this tree, producing its own result), `not-reproducible` (would need
the ledger repository), `not-run`.

Interpreter for every command below: CPython 3.12.3, repository root, stdlib only.

## 1. What was checked in this tree

| # | item | command / method | observed | record named | verdict | notes |
|---|---|---|---|---|---|---|
| 1 | the size reconciliation arithmetic | `python3 -c "print(199099 + 43*6)"` | **199357** | every multi-target record carries `certificate.expected_bytes_at_q43 = 199357` | reconciled | the only arithmetic the package shows. Inputs and result are both printed in `measurements.md` §1, so a reader can check it without the archive |
| 2 | released relation-QC size | read `certificate.size_bytes.*.qc_a` out of both multi-target records | `199357` in every entry, both passes (378 entries in the first, 447 in the second) | `20260911T154517Z`, `20260913T064402Z` | transcribed-verified | `measurements.md` §1 row 1 |
| 3 | released side-B size and its control | read `.qc_b` and the `xset-qc_b` entry | `203990` in every `mt:` entry of both passes; the second pass's control entry `199357` | same two runs | transcribed-verified | `measurements.md` §1 rows 2–3. The control is what makes the `203990` readable as a side-B form rather than a different object |
| 4 | the five binary sha256 prefixes | grep each prefix over the run archive | all five resolve to a full 64-hex digest; the calibration record additionally carries `in_container_sha256.all_match: true` over 64 seats for `22026ca8…` | `UNPAUSED_BASELINE.json`; the arm `round.json` files | transcribed-verified | `environment.md` §5. The package prints prefixes only; the records carry the full digests |
| 5 | the sources digest | read `node_binary.sources_digest` | `e0f5687c…` (64 hex) | `20260913T143920Z` | transcribed-verified | names the source snapshot the calibration binary was built from |
| 6 | every run identifier the package cites | extract every `20……T……Z` token from the package's documents, test each against the archive | **12 distinct identifiers, 12 present, 0 absent** | all runs named in the package | transcribed-verified | a citation that did not resolve would be a dead reference, not a wrong number; none did |
| 7 | multi-target attempt and check counts | `len(extractions)`, `len(checks)` per record | first pass **378** pairs / **380** checks, all `passed`; second pass **447** pairs / **899** checks | `20260911T154517Z`, `20260913T064402Z` | transcribed-verified | `measurements.md` §3. The second pass's own `attacker_cost.measured.attempts` is 378 in both passes; the 447 is the pair count, and the page labels it as such |
| 8 | typed-rejection count | read the rejection record's own check line | `every stream call is a typed 4xx rejection (no 5xx, no 2xx): 240/240`, detail `{'typed': 240}`; `attempts` 243 = 240 stream calls + 3 vacuous | `20260913T070954Z` | transcribed-verified | `measurements.md` §3 |
| 9 | differential verification count | read `independent_verifications` | `{total: 258, verified: 258, failed: {}}`, `disagreements: []` | `20260913T071235Z` | transcribed-verified | `measurements.md` §3 |
| 10 | calibration timings, view and counts | read the five check lines of the calibration record | `first_finalization_s 20.17`, `convergence_s 37.46`, `relation_qc_signers 43`, `view 0`, 64 seats at one root, `p50 3.381`, `p95 5.011`, 512 probes | `20260913T143920Z` | transcribed-verified | `measurements.md` §2. The record carries the `LOCAL-CONTROL OBSERVATION; NOT A NETWORK BENCHMARK` label; the page keeps it |
| 11 | the memory slope | read the rejection record's `fit` | `slope_bytes_per_call 18827.56`, `n 7`, `intercept 21507416.8`, `delta_bytes 6039798` | `20260913T070954Z` | transcribed-verified | `measurements.md` §4 |
| 12 | the F8 verdict strings | grep `verdict` in the F8 classification and post-fix records | exactly three strings: `mixed_inconclusive`, `design_limit_on_this_host`, `debug_build_artefact` | the two F8 records | transcribed-verified | the package uses those strings and no others; see discrepancy 2 below |
| 13 | corruption-sweep completeness | read the sweep summary | `complete: true`, `requested_points: 28`, within-model 22 passed / 0 failed / 0 not_run (C-0 … C-21), outside-model 6 passed / 0 failed / 0 not_run (C-22 … C-26 including `C-26-one-sided`) | `20260911T134816Z` | transcribed-verified | this is the row behind discrepancy 1 below |
| 14 | forbidden-content scan, this package | `python3 tooling/checks/scan-forbidden.py docs/05-devnet-evidence` | `files scanned: 6, findings: 0` — `ai-name 0, ai-meta 0, abs-path 0, tracking 0, contact 0, secret 0` | — | reproduced | run after the last edit to the package, including this page |
| 15 | forbidden-content scan, whole repository | `python3 tooling/checks/scan-forbidden.py .` | **610 files scanned, 0 findings** in all six categories | — | reproduced | the tree is assembled concurrently with this page, so the repository total is a property of the tree at the instant of the run: earlier in the same pass this invocation reported hits in another package's verification page, which that package's own pass then removed. **No run of it ever named a file of this package** |
| 16 | repository map gate, this package's files | `python3 tooling/checks/verify-repository.py` | the gate lists `environment.md`, `measurements.md`, `open-items.md` and `test-campaign.md` under its authored set, and `README.md` and `VERIFICATION.md` in its recognised authored names; **no `MISSING`, `HASH`, `UNEXPLAINED` or `EMPTY` line names this package** | — | reproduced | the gate's overall `RESULT: FAIL` at the time of this run comes from other domains — 131 recorded differences against `records/file-map.tsv`, and one empty file, all outside this package. Reported as observed, not as a pass |

The three gate rows above were run at repository root on the tree as it stood when this page was
finalised. Row 14 gave 0 findings over this package's six files, and did so on every re-run after
each edit; row 15 gave 0 findings over the whole tree. Row 16's non-zero lines were all outside this
package, in domains still being built concurrently with this one: the gate's recorded differences and
its one empty file are theirs, and this package contributes zero to both counts. That distinction is
stated because the two readings are not the same claim — a clean package inside a tree that is still
being assembled is exactly what this page can assert. The scan's own source is skipped by identity,
which is why the one path it prints is a note rather than a finding.

## 2. What cannot be checked here, and why

| item | verdict | why, and what a reader would need |
|---|---|---|
| any number in this package, by re-measurement | not-reproducible | the devnet kit is not in this repository. The map excludes it (`exclude-triad`) because it belongs to a separate ledger repository, and no file of that repository is copied here. Re-measuring needs that repository, its kit, and the host profile in `environment.md` §1 |
| the node binary digests | not-reproducible | the binaries are not shipped. `environment.md` §5 records sha256 prefixes; a reader can confirm them only by rebuilding the ledger's `mainnet` profile from the recorded source digest, which requires the ledger repository and its toolchain. Nothing in this tree can recompute them |
| the raw run records | not-run | the records the numbers were transcribed from are not part of this repository either; they live with the campaign's handoff material. What is checkable here is internal consistency between the page and the field it names — rows 1–13 — not the records' own existence on a third party's disk |
| a live re-run of any scenario | not-reproducible | needs the ledger repository, a quiet 12-core host with an exclusive lock, container runtime, and the fixture rendered fresh per scenario. `environment.md` §6 and `open-items.md` list which scenarios are pending and what each would take |
| the ledger's own source, configuration and keys | not-run | excluded by construction. This package records what the testbed *did* and *returned*; the exclusion is recorded once in `README.md` |

A reader who wants a re-measurement should read `environment.md` first: it names the host profile, the
container-level shaping, the fault-injection families and the binary policy, which together are the
minimum needed to reproduce a run rather than merely re-read one.

## 3. Discrepancies found in the sources, and how this package resolves them

These are recorded because a reader who consults both sources will meet them. In each row the package
carries both phrasings or states plainly which it followed; none is silently smoothed.

| # | source X says | source Y says | resolution in this package |
|---|---|---|---|
| 1 | `maps/work-packages.md` (WP-DOC-05) states that the seven chaos scenarios are `not_run` and that the corruption-count sweep is **not verifiable from the archives**, listing only C-21 and C-22 as having passing records | the archive holds the sweep **complete** at `20260911T134816Z`: `complete: true`, 28 requested points, 22 within-model and 6 outside-model, 0 failed, 0 `not_run` (row 13 above); the testbed's own finding F1 is a naming correction against it | both carried. `environment.md` §6 states the status text and the complete sweep side by side, and says the sweep's claim belongs to another domain and is not restated here. `open-items.md` carries the scenario statuses as the testbed records them |
| 2 | the drafted source material's F8 cell reads "mixed / inconclusive for the debug build" | the records give two different verdicts on pre-committed rules: `mixed_inconclusive` (pre-fix release arms and the post-fix replicate) and `design_limit_on_this_host` (the post-fix debug arm) | both phrasings carried. `test-campaign.md` entry 2 quotes the recorded verdict per arm, and `measurements.md` §6 says a `mainnet`-profile pass never closes the debug finding. The draft's sentence is not upgraded into a single verdict |
| 3 | the drafted material's support list says a typed-duplicate offence "can be constructed and observed" | the same parenthetical says the live run is pending | the pages say **constructed and driven, live run pending**. `README.md` lists it as construction-plus-driver and explicitly "not yet an observation"; `open-items.md` item 2 carries it as open. No observation is claimed |
| 4 | `maps/work-packages.md` (WP-DOC-05) names the package's files `results.md` and `limitations.md` | the assignment names five files: `README.md`, `test-campaign.md`, `measurements.md`, `environment.md`, `open-items.md` | the assignment's five filenames were used. The map's names are not carried into the pages; the content the map describes is distributed across the five |
| 5 | the drafted material attributes the extraction naming seats 1–22 plus 42 to the key-rollback scenario F10 generally | `records/failed-assumptions.md` A27 attributes that naming to the **GV (both-rolled-back)** variant specifically | the entry was restructured. `test-campaign.md` entry 3 separates variant G — which came up **ready** and released a conflicting vote, the failed expectation — from variant GV, which produced the naming with `attributed: true` and 0 false positives, and records the arm as 8 checks, 7 passed, 1 failed |

## 4. How to re-check this page

The rows of §1 that can be re-run from this repository, with no devnet access, are these:

```sh
python3 -c "print(199099 + 43*6)"                                    # row 1: 199357
python3 tooling/checks/scan-forbidden.py docs/05-devnet-evidence     # row 14: 0 findings
python3 tooling/checks/scan-forbidden.py .                           # row 15: 0 naming this package
python3 tooling/checks/verify-repository.py | grep 05-devnet         # row 16: authored only
```

The remaining rows need the run archive that the numbers were transcribed from, which is held with
the campaign's handoff material and is not in this repository; §2 says what a reader would need to
rebuild one. Nothing on this page re-runs a devnet, and no verdict here should be read as one.
