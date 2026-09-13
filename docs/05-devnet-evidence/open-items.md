# Open items

Every test that did not finish, every question the campaign left open, and — for each one — what it
would take to close it. Two things are stated for each item: **what would close it**, and **whether
this environment could close it at all**. An item that no configuration of this testbed can close is
marked as such rather than left to look like a scheduling problem.

None of these is a cryptographic claim. Each is a platform claim that the research record now states
explicitly instead of assuming.

## 1. Summary

| # | Open item | What would close it | Closable here? |
|---|---|---|---|
| 1 | `KEY_ROLLBACK` re-run on the fixed binary (finding F10 / A27) | Re-run the variant-G scenario against the node whose startup installs the monotone join of journal and log and refuses conflicting records; a fail-closed result closes the record | Yes — after the fixed binary is mounted and the run is performed |
| 2 | `REPLAY` typed-duplicate re-extraction (finding F11) | Run the rebuilt construction live on a paused C = 22 cluster; the record must show seat 22 `rejected` with the typed duplicate name and the other 21 `verified` | Yes — driver is ready |
| 3 | `MESSAGE_FAULTS` | Run the committed unpaused 64-seat round with duplication, reordering, loss and one-seat clock skew, on a binary that finalizes | Only if liveness holds on the chosen binary |
| 4 | `PARTIAL_NETWORK` | Run the finality-free checks live: shaping mechanics, both partitions' mechanics, the 32\|32 halt window, heal reachability, all 64 seats at the baseline height with one root | Yes — these checks do not need liveness |
| 5 | `PARTIAL_NETWORK-liveness` | Run the progress checks across the partition on a binary that finalizes; until then the record stays `not_run` "blocked by F8" | Only with a binary that finalizes |
| 6 | `WITHHELD_CERTIFICATE` | Drive the committed "new view finalizes" step, not just the view advance, and run it live | Yes — after the driver is extended and the binary question is answered |
| 7 | `SOAK64` | Run a 64-seat soak for a committed duration; the 24-hour form has never been run at 64 seats | Partly — a bounded soak is runnable on a quiet host; the 24-hour form is host-limited (see §7) |
| 8 | Which binary the two never-unpausing scenarios use | A decision, recorded; the scenarios commit unpaused rounds but the driver never unpauses them | Yes — a decision, not a run |
| 9 | The F8 mechanism (fsync under the node mutex) | One of the three isolating experiments in §4, or a refutation | Yes, in principle — the experiments are identified and were not run |
| 10 | The variance between identical release runs | Repeat the release liveness arm enough times to separate binary effects from host state | Partly — more runs on one host reduce but do not remove the confound |
| 11 | The deferred follow-ups of the relay-duplicate change | Validation cache, validation outside the mutex, gossip list including the seat itself, the N² relay | Yes — engineering, outside this repository |
| 12 | The F11 epoch precondition | Verify live that the snapshot epoch is unchanged from height 1 to height 2 on the route | Yes — alongside item 2 |
| 13 | Real partition tolerance at 64 seats | A partition across independent hosts and operators | **No** — never possible in a single-host testbed |

## 2. Re-runs pending on the fixed binary

The code changes landed, and the records have **not** been re-run against them. Until they are, the
records keep their recorded status, and no reader should take a fix for a verified fix.

- **`KEY_ROLLBACK` (item 1).** The scenario's fail-closed expectation is unchanged, and the fix — a
  restore that installs the monotone join of the signing journal and the write-ahead log and refuses to
  start on conflicting records — is recorded with four tests that fail before and pass after it. The
  re-run has not happened, so the record stays `failed` and the finding F10 / A27 stays open on
  evidence. What closes it: re-run the variant-G scenario on the fixed binary and record the outcome.
  A fail-closed result closes the item; a second failure reopens the code change, not the premise —
  the premise is already refuted.
- **`REPLAY` typed-duplicate re-extraction (item 2, with item 12).** The construction was rebuilt and
  approved, the driver is ready, and the live run is pending. What closes it: a live run in which the
  re-extracted pair reports seat 22 `rejected` with the typed duplicate reason while the other 21 stay
  `verified`, on a paused C = 22 cluster whose evidence was finalized through the paused administrative
  round. The precondition in item 12 — the snapshot epoch must be unchanged from height 1 to height 2,
  or the offer step rejects with the invalid-evidence reason before the duplicate check — must hold in
  that run; if it does not, the route needs a different fixture rather than a different assertion.
- **The relay-duplicate change itself (item 11).** The change is deliberately narrow: on the peer relay
  route only, a receipt byte-identical to an entry already queued skips re-validation, while the client
  submission route still validates first — this preserves the recorded client-path expectations.
  Its follow-ups are open: a validation cache, validation moved outside the node mutex, a gossip list
  including the seat itself, and the N² relay itself. They are engineering work on a separate
  repository, and none of them is claimed here as done.

## 3. Scenarios that have not run

Each of these is recorded `not_run`, never as a pass, and none is re-expected before it runs.

- **`MESSAGE_FAULTS` (item 3).** Duplication, reordering, loss and one-seat clock skew during an
  unpaused 64-seat round. Its baseline round — the calibration gate — passed on the `mainnet`-profile
  binary (`UNPAUSED_BASELINE`, run `20260913T143920Z`), which removes the binary objection but does not
  run the scenario. What closes it: the scenario itself, on a binary that finalizes.
- **`PARTIAL_NETWORK` (item 4).** Its checks were split out precisely so that the finality-free half
  could run without liveness. It has not. What closes it: a live run of the finality-free checks —
  shaping installed and censused per seat, both partitions' mechanics, the 32|32 halt window, heal
  reachability, and all 64 seats at the baseline height with one root. This half is runnable now.
- **`PARTIAL_NETWORK-liveness` (item 5).** The progress checks. Recorded `not_run` with the reason
  "blocked by F8" until they can run on a binary that finalizes. What closes it: a finalizing binary —
  nothing else changes the record.
- **`WITHHELD_CERTIFICATE` (item 6).** The committed scenario expects a new view to finalize after a
  certificate is withheld; the driver advances the view but does not drive the finalization, so the
  scenario as committed cannot pass. What closes it: extend the driver to drive the committed step, then
  run it live on a binary that finalizes.
- **`SOAK64` (item 7).** A bounded soak at 64 seats has never run. The 24-hour form has not been run at
  64 seats anywhere in this programme. What would close it: a 64-seat soak of a committed duration on
  hardware that can hold it — see §7.

## 4. The liveness mechanism

The F8 records found that with the debug build an unpaused 64-seat round does not finalize, and that
the release build finalizes with storage-sensitive latency. The proposed mechanism — nodes rewriting
auxiliary state with `sync_all`, rename and directory fsync, and the write-ahead log and key guard
also flushing, none of it off the node mutex, while `/v1/status` takes the same mutex — is an
**inference**. It is
consistent with the observation that the stalls track host I/O pressure and clear when the pressure
clears. It is not shown.

Three isolating experiments are identified and were **not run**:

1. repeat the slow arm immediately after a controlled write load;
2. repeat it after a long idle;
3. run it with node data on a memory-backed filesystem.

What closes the item: any one of the three, or a refutation. The observation that makes this a live
question rather than a curiosity: in the calibration run, on a host whose own precheck had shown iowait
≤ 0.13 % over 60 s, host iowait still reached 92.12 % inside the round, and `/v1/status` answered on
only 4–36 of 64 seats in the sweeps from 20 s to 35 s while container CPU was 1–8 % — and the round
still finalized in view 0 at 37.5 s. Storage pressure therefore arises within a round, on a quiet host,
not only after a preceding heavy arm.

A second open question belongs to this item: the two post-fix release runs of the **same binary**
differed by **57 s** and carry opposite verdicts on pre-committed rules (`mixed_inconclusive` for the
slow one, `debug_build_artefact` for the fast one). What closes it: more release runs, which reduce the
confound without removing it on a single host.

## 5. The binary question

Two scenarios that commit unpaused 64-seat rounds never unpause in the current driver —
`WITHHELD_CERTIFICATE` and `SOAK64` — so the binary policy's rule ("unpaused scenarios run on the
`mainnet` profile, paused scenarios stay on debug") does not decide which binary they use. This is an
open question for the decision owner, not a measurement. What closes it: a recorded decision, after
which the scenarios can be driven or explicitly retired.

Related: a `mainnet`-profile pass **never** closes a finding for the debug build. The debug arms failed
to finalize both before and after the relay change (`design_limit_on_this_host`), and that record stays
as it is.

## 6. Questions the campaign answered only partially

- **Sustained-load behaviour.** The rejection stream is a 240-call window with a fitted 7-point memory
  slope of 18,827.56 B/call and no state change. That is not a soak. What would close it: a long
  rejection stream with the same instrumentation, and a leak threshold committed in advance.
- **Independent verification coverage.** The differential run verified 258 of 258 signatures with zero
  disagreements on one certificate set. What would close it: the same differential run over the other
  scenarios' certificates, and an audit of the independent implementation itself, which was not
  audited here.
- **The non-constructible taxonomy case.** `index_out_of_range` cannot be built in this fixture and is
  recorded `not_applicable`. It cannot be closed in this environment; it can only be recorded as
  not applicable, which it is.
- **Attribution coverage.** Every run reported zero false positives and named no honest seat. What
  would close the question of whether attribution is correct in general: a run at a corruption count
  where the honest/Byzantine split is not known in advance, and an externally held key, neither of
  which this fixture provides.

## 7. Runs never possible in this environment

These are not pending. No amount of time on this testbed produces them, and the record should be read
with that in mind.

- **Real partition tolerance.** A single-host testbed cannot partition independent hosts. It can
  emulate unreachability between containers, which is what `PARTIAL_NETWORK` does; it cannot test a
  partition that follows from network topology, independent operators or a real wide-area path.
- **Validator churn.** Registry changes, validator set changes and key rotation are not constructible:
  the seat set is fixed for the life of a run.
- **A hardware root of trust.** A hardware anti-rollback counter sits outside the software boundary the
  testbed controls. The rollback scenario exercises software signer state, and a rollback that moves
  every local record backwards — including whatever such a counter would have protected — is explicitly
  outside the boundary the campaign decided on. No run here can speak to it.
- **A 24-hour soak at 64 seats.** Not run anywhere in this programme; at 64 seats on a shared 12-core
  host, the storage behaviour observed in the liveness arms makes a long soak an unreliable instrument
  even if it were attempted — the host would be measuring itself.
- **Independent operators, independent clocks, independent storage.** One operator, one host clock, one
  storage device. Every timing in this package is therefore a timing of this host, and the honest
  description of the 57-second spread between two identical runs is that the host is a variable the
  testbed cannot control, only sample.
- **A second implementation of the node to disagree with.** There is none at 64 seats, so there is no
  differential check of node behaviour of the kind that exists for the B0 extraction rule in the audit
  domain.

## 8. Why these stay open in public

The campaign's rule — a recorded number that a re-run does not reproduce is withdrawn in public, in
place, with the reason — is what produced the two corrections this evidence forced (`A27` in
`records/failed-assumptions.md`, and the withdrawal of the "16/16" property figure as `A28`). The same
rule keeps the items above open rather than closed by argument: an item is closed by a run, a decision,
or an explicit statement that the environment cannot produce it — never by the absence of a bad result.
