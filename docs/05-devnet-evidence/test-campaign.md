# The devnet test campaign

This document is the campaign record: one entry per test, each with what it exercises, how the fault
was injected, what was observed, the pass/fail as recorded, and the specific claim the result
supports. Tests that failed and tests that did not run are included, with the reason.

Every entry cites its run identifier. Run identifiers are record names and are quoted verbatim; a run
identifier is the only handle needed to find the record. The campaign ran against a 64-seat fixture —
n = 64 seats, f = 21, quorum q = 43, overlap bound 2q − n = 22 — that the records themselves mark
`NON-NORMATIVE DEVNET TEST FIXTURE - NOT A RATIFIED MAINNET GENESIS VALUE`.

## How an entry is written

| Field | Meaning |
|---|---|
| **Exercises** | The premise or behaviour under test, in the terms the record uses. |
| **Injection** | The mechanism by which the fault or condition was introduced. |
| **Observed** | What the running system did. |
| **Recorded result** | `passed`, `failed` or `not_run` as the record states it, with the check count. |
| **Claim supported** | The one statement this result is allowed to support — never wider. |
| **Boundary** | What the result does not support. Carried on every entry, including the passing ones. |

Three statuses appear and they are not interchangeable: **`passed`** (the check ran and held),
**`failed`** (the check ran and did not hold), **`not_run`** (the check did not execute, with the
reason recorded). A `not_run` is never a pass, and a check that could not run is never reported as an
absence of findings. Within-model, outside-model and input-validation results are reported in their
own regimes and never merged into a single total.

A note on finding numbers, because two series collide. The findings cited by number in this document
(F8, F10, F11, F12, F13) are the **campaign's own** expectation-refutation identifiers, taken from the
testbed's expectation record. The independent audit stack keeps an unrelated series of the same shape
(F1–F5), and this document says whose a number is whenever it cites one. Same letter, different
record.

## Campaign summary

| Test | Recorded result | Run |
|---|---|---|
| `UNPAUSED_BASELINE` | **passed**, 5/5 checks, view 0 | `20260913T143920Z` |
| `F8` liveness classification (pre-fix arms A/B/B2/C) | debug arm A **did not finalize**; release arms B/B2 **finalized**, verdict `mixed_inconclusive`; arm C (n = 32) **finalized** | `20260913T125634Z` |
| `F8` post-fix arms D/E/E2 | **D did not finalize** (`design_limit_on_this_host`); **E finalized** (`mixed_inconclusive`); **E2 finalized** (`debug_build_artefact`) | `20260913T132924Z` |
| `KEY_ROLLBACK` variant G | **failed** — 8 checks, 7 passed, the fail-closed expectation failed → finding F10 | `20260913T072300Z` |
| `STALE_STATE` | **passed**, 17/17 checks | `20260913T072646Z` |
| `REPLAY` | 25 checks: 24 passed (checks 0–23); typed-duplicate re-extraction `not_run` → finding F11 | `20260913T063631Z` |
| `MULTI_TARGET` | **passed** (380 checks, then 899 checks on the re-run) | `20260911T154517Z`, `20260913T064402Z` |
| `MALFORMED_CERTIFICATE` | **passed**, 30 checks | `20260911T153826Z` |
| `REJECTION_STREAM` | **passed**, 9 checks | `20260913T070954Z` |
| `DIFFERENTIAL_EXTRACT` | **passed**, 17 checks | `20260913T071235Z` |
| `MESSAGE_FAULTS` | **not run** — committed unpaused 64-seat round, not executed on the fixed binary | — |
| `PARTIAL_NETWORK` | **not run live** — record split → finding F12 | — |
| `PARTIAL_NETWORK-liveness` | **not run** — `not_run`, blocked by F8 | — |
| `WITHHELD_CERTIFICATE` | **not run** — never unpauses in the current driver; binary open | — |
| `SOAK64` | **not run** — no 64-seat soak has been executed | — |

An entry is written for each of these below. The committed scenario specifications live with the
testbed and are not reproduced here; this package reports the runs it has records for.

---

## 1. `UNPAUSED_BASELINE` — the calibration gate

- **Exercises.** Whether an *unpaused*, otherwise honest 64-seat cluster finalizes one round when the
  node binary is built with the repository's own `mainnet` Cargo profile. This is the gate that
  blocks the unpaused scenarios until it passes on the binary those scenarios will use.
- **Injection.** No fault. One round with no equivocation and no injected fault: all 64 seats start
  at one finalized height and one state root (checked first), the round is driven, and every seat's
  `/v1/status` is sampled through the pending window. The node binary is mounted read-only after a
  build manifest verifies (sha256 equal, profile in {debug, release, mainnet}, sources digest equal to
  a fresh digest of the current sources), one read-only mount per service, with `docker compose
  config` and in-container sha256 checks after bring-up. Exclusive host lock; quiet-host precheck
  before the bring-up (rolling 60 s window, iowait < 5 %, no other testbed containers, up to 600 s).
- **Observed.** Precheck `quiet`, iowait ≤ 0.13 % over 60 s. Manifest verified, in-container sha256
  equal on 64/64 seats. First finalization seen at 20.2 s (`first_finalization_s` 20.17); all 64 seats
  at one new finalized height with one state root at 37.5 s (`convergence_s` 37.46); the frame's
  relation QC at view 0 with 43 signers. `/v1/status` over the pending window: p50 3.381 s, p95
  5.011 s, 512 probes, ok fraction 0.6. Container CPU sum over the pending window: median 7.05 %,
  max 1,160.3 %. No seat named (`honest_seats_named == []`, no finalized offence, C = 0, extraction
  not invoked); no container exited; all 64 seats still running after the window.
- **Recorded result.** **passed**, 5/5 checks, on node `22026ca8…` (profile `mainnet`, sources digest
  `e0f5687c…`), one attempt, view 0.
- **Claim supported.** That a 64-seat unpaused round can finalize on this hardware with a
  release-quality build, and that the gate that unlocks the unpaused scenarios has been met for this
  binary.
- **Boundary.** A mainnet-profile pass **does not close F8 for the debug build**. This is a
  local-control observation, not a benchmark; the latency numbers are properties of this host in this
  window, not of the construction. Passing the gate closes no finding and is not a scenario result —
  the unpaused scenarios themselves have not run on it.

## 2. `F8` — unpaused 64-seat liveness, debug against release

- **Exercises.** The scenario the campaign calls F8: an honest, unpaused 64-seat cluster finalizing
  the single-equivocator TVSE submitted through the client intent route within 180 s. The question the
  follow-up runs answer is whether a non-finalizing round is caused by the debug build or by a real
  limit.
- **Injection.** Dual proposal, then seat 5 equivocates; all seats unpaused; the evidence submitted
  through `POST /v1/intents`; every seat's `/v1/status` sampled every 5 s with a 5 s timeout, plus
  container statistics, host load, memory, and (post-fix only) 1 s iowait, disk statistics, PSI and
  dirty-page readings. Arms differ only in the node binary; the compose overlay mounts it, and
  `docker compose config` shows exactly one mount per service with the in-container sha256 equal. The
  harness and thresholds (`THRESHOLDS.json` sha `538c34bb…`) were frozen before any round.
- **Observed — pre-fix arms (run `20260913T125634Z`).**
  - Arm A, debug, n = 64: **did not finalize**, 0 in 300 s; `/v1/status` ok 4.9 %, p95 5.0 s;
    container CPU sum median 1,163 %, max 1,234 %; RSS sum max 3.6 GiB; load max 73.7.
  - Arm B, release, n = 64: finalized, one root, first 145 s / all-64 152 s, in view 1; ok 92.4 %,
    p95 5.0 s; CPU median 347 %, max 1,161 %; RSS sum max 6.3 GiB.
  - Arm B2, release replicate: finalized, one root, 137 s / 167 s, view 1; ok 71.6 %, p95 5.0 s.
  - Arm C, release, n = 32 scale probe: finalized, one root, ≤ 5 s; ok 100 %, p95 0.05 s; CPU 379 %
    on one sample.
  - Verdict on the pre-committed rules: **`mixed_inconclusive`** — B finalized within 300 s on one
    root with CPU median below 900 %, but failed the `status p95 < 1 s` condition, and did not meet
    the design-limit condition either.
  - Micro-measurements (medians of 3, marked ≈ in the record): ML-DSA-87 sign + verify debug 10.6 ms
    against release 0.78 ms per signature, about **13.6×**; one validation-equivalent ≈ 0.26 s per
    transfer and ≈ 0.32 s per evidence intent in debug, against ≈ 6–9 ms in release, the release value
    at the exec-jitter floor; capacity about 40 validations/s in debug and about 1,300/s in release,
    against the estimated relay demand of about 2,000/s at n = 64.
- **Observed — post-fix arms (run `20260913T132924Z`), after the relay-path duplicate check landed.**
  - Arm D, debug post-fix: **did not finalize in 300 s**; CPU median 1,087 %, max 1,222 %; probe ok
    22.2 % (up from 4.9 %), p95 5.0 s; host iowait 0 / 70 %. Verdict `design_limit_on_this_host` —
    the relay dedup alone does not clear the debug stall; the remaining debug work still saturates the
    12 cores.
  - Arm E, release post-fix: finalized, one root, 67 s / 67 s, view 0; probe ok 65.8 %, p95 5.0 s;
    host iowait median 77.5 %, max 98 %. Verdict `mixed_inconclusive`, on the p95 rule.
  - Arm E2, release post-fix replicate, after a quiet-host wait: finalized, one root, 10 s / 10 s,
    view 0; probe ok 100 %, p95 0.75 s; host iowait median 0.3 %, max 77 %. Verdict
    `debug_build_artefact`.
  - E and E2 are the same binary and differ by **57 s**. The release verdict therefore depends on host
    state, not on the binary alone.
- **Recorded result.** Arm A: **failed to finalize** (no convergence in 300 s) — the debug-arm
  behaviour F8 recorded. Arm B and B2: **finalized**, with the `mixed_inconclusive` qualification the
  pre-committed rules attach. Arm C: **finalized** (n = 32). Post-fix: arm D **failed to finalize**
  with verdict `design_limit_on_this_host`; arms E and E2 **finalized** with verdicts
  `mixed_inconclusive` and `debug_build_artefact` respectively.
- **Recorded status of the F8 measurement as a whole.** **Mixed / inconclusive.** The release verdicts
  are `mixed_inconclusive` (pre-fix B/B2 and post-fix E) and `debug_build_artefact` (post-fix E2); the
  debug verdict is `design_limit_on_this_host` (post-fix D) and a plain failure to finalize (pre-fix
  A). The two release verdicts disagree with each other on identical binaries, which is why the
  record's own summary of the measurement is a mixed one rather than a single verdict.
- **Claim supported.** That the debug build cannot be used for unpaused 64-seat liveness on this host,
  and that a release-quality build can finalize the round — with the latency strongly dependent on
  host storage state. Also the measured debug/release ratio for the signing path.
- **Boundary.** Nothing in the cryptographic argument depends on 64 seats finalizing in a fixed time,
  and no result in this repository was retracted because of F8. What F8 bounds is the *evidence* for
  the liveness-facing scenarios: until they run on a binary that finalizes, their progress checks are
  recorded `not_run` with an explicit reason, never as a pass. The proposed mechanism — state-file
  fsyncs held under the node mutex while host storage is saturated — is an **inference, not isolated**.
  The measured ratios are local-control observations of one host, not benchmarks.

## 3. `KEY_ROLLBACK` (variant G) — restart from a stale signing journal

- **Exercises.** Whether the signing discipline survives a restore: a seat restarted with a signing
  journal copied *before* one of its own votes, together with its current data volume, either refuses
  to start or starts and refuses to sign.
- **Injection.** Seat 42 voted phase I for candidate A. Its signing journal was then copied from
  before that vote and reinstalled over a current data volume; the seat was restarted. Fixture
  corruption count C = 22 (seats 1–22 modelled as byzantine), 64 seats.
- **Observed.** In the **G** variant the seat came up **ready** (in 8.2 s; restart took 7.1 s) and
  released a conflicting phase-I vote for candidate B at the same coordinate (epoch 3, height 1,
  view 0), candidate `1659af8a…`, with `conflicts_with_pre_rollback_vote: true` — the expectation that
  it would fail closed is what failed. In the same record's **both-rolled-back** variant, which is
  *outside* the software boundary and is expected to behave as observed, the rolled-back seat starts
  and releases a conflicting vote for the other candidate, the side-B certificate including it
  assembles with the quorum's signers, and extraction names seats 1–22 **plus 42** with
  `attributed: true` and zero false positives: no honest seat was named, and every extraction-side
  check passes. The recovered seat's own vote is the conflicting one, and it is correctly attributed.
- **Recorded result.** **failed** — 8 checks, 7 passed and **1 failed**, the failed one being exactly
  the committed expectation "G: stale signing journal + current volume fails closed (startup or
  signing refused; no vote released)". This is the finding F10, carried as **A27** in
  `records/failed-assumptions.md`. The remaining 7 checks in the same record cover the
  both-rolled-back variant and the extraction side, and they pass: contract-valid extraction, the
  naming cross-check between decoded evidence votes and accused identity, and the rolled-back seat
  named as a genuine double-signer with correct attribution.
- **Claim supported.** That the operational honesty premise — "a seat contributes to at most one
  message per domain" — does **not** survive a restore as the models had implicitly assumed, and that
  a fleet-wide restore from one backup can push C from ≤ 21 (no conflict possible) to ≥ 22
  (conflicting certificates possible, all attributable). The cryptography behaved correctly: the seat
  really did sign twice and was correctly identified, and every attribution check on the extraction
  side passed.
- **Boundary.** This is not a cryptographic failure and not an attack on the construction. It is an
  operational premise that was implicit and is now explicit: the honesty condition must be stated over
  signer state that is **monotone**, and a rollback that moves all local records backwards is an
  operator-corruption event that counts in C. Resolution: the stale-journal-with-current-ledger case
  was ruled *inside* the software signer boundary — restore now installs the monotone join of the
  journal and the write-ahead log and refuses to start on conflicting records, with four tests that
  fail before and pass after the change — while only a simultaneous rollback of every local safety
  record stays outside. The live re-run on the fixed binary is **pending**; the record keeps its
  `failed` status until it runs.

## 4. `STALE_STATE` — catching up a seat that has fallen behind

- **Exercises.** Whether a seat that has fallen behind is caught up and its next round is driven, with
  no second vote released.
- **Injection.** Seat 5 — one of the round's voters — restarts on a **stale volume with its current
  signing journal**, the mirror image of the key-rollback fault: there the journal is stale and the
  volume current, here the volume is stale and the journal current. The seat is then caught up and
  driven into its next round, with another proposal re-delivered at the coordinate it has already
  signed. Fixture C = 0, byzantine set empty, 64 seats.
- **Observed.** 17 checks passed, in order: the seat restarts (7.1 s) and comes up **not ready** with
  interactive signing refused; while behind, the signing journal's position is at or ahead of the
  write-ahead log's; the re-delivered other proposal at the signed coordinate is **rejected with zero
  mutation**, and no second vote is released (`second_vote_released: false`); the seat catches up
  through verified history sync in 4.4 s (`catchup_seconds`) and becomes ready; the next round then
  runs with that seat voting normally in all three phases, each phase a certificate built from 43
  votes; the height-2 relation record is installed on all 64 seats, and after the round all 64 seats
  report height 2 and one state root.
- **Recorded result.** **passed**, 17/17 checks, driven by 3 administrative calls.
- **Claim supported.** That a lagging seat can be brought forward and driven to its next round without
  violating the one-vote discipline, on this fixture.
- **Boundary.** A single-run observation on one host at C = 0 with no byzantine seats. It says nothing
  about a lagging seat under an unpaused round at C ≥ 22.
- **Read together with the next entry.** The pair matters more than either record: a seat that restarts
  with a **stale volume and current journal** refuses to sign while behind and never double-votes
  (this entry, passed), while a seat that restarts with a **stale journal** released a conflicting vote
  (`KEY_ROLLBACK`, failed). The distinguishing quantity is whether the seat's *signer state* moved
  backwards — which is exactly the monotonicity premise A27 records, and the reason the failed case is
  a premise finding rather than a cryptography finding.

## 5. `REPLAY` — replay of a finalized certificate, and re-extraction of a finalized offence

- **Exercises.** Replay of a finalized certificate, and re-extraction of an already-finalized offence:
  whether the node rejects the replay with the typed reason, and whether re-extraction reports the same
  seat as a duplicate rather than re-attributing it.
- **Injection.** A finalized certificate is replayed and the replayed-evidence round is driven through
  a paused administrative round: three phases of 1,854.452 ms, 1,872.453 ms and 1,856.085 ms, each
  with 43 votes. The typed-duplicate re-extraction then had to be constructed on a paused C = 22
  cluster, and the construction approved before the scenario text was changed is: phase I built on
  **both** sides; phases II and III on side A only; record A installed on all 64 seats and record B
  **never delivered**; seat 22's verified evidence finalized at height 2 through the same paused
  administrative round used for the replayed-certificate route; then the same pair re-extracted, which
  must report seat 22 `rejected` with the typed duplicate name while the other 21 stay `verified`.
- **Observed.** Checks 0–23 passed — the replay was rejected and the duplicate rejection was
  evidenced. The typed `SlashEvidenceDuplicate` re-extraction was **`not_run`**, with the recorded
  reason "the within-model single-equivocator route builds no conflicting QC pair at the offence
  coordinate". On review that reason did not hold: the offence key is computed once and holds no
  candidate identifier, so any finalized key makes that seat's claim a duplicate whichever record
  carried the evidence, and a pair route needs no fork-choice decision because side B never gets a
  quorum decision at all.
- **Recorded result.** **partially run**: 25 checks recorded; checks 0–23 **passed** (24 of them) and
  the last, `re-extract to observe the typed SlashEvidenceDuplicate name`, recorded **`not_run`**.
  This is the finding F11; the construction was rebuilt and **the live run is pending**.
- **Claim supported.** That a replay of a finalized certificate is rejected on the typed path, and (by
  construction, not yet by a live run) that a typed duplicate offence can be built at n = 64 from a
  real C = 22 extraction whose evidence was finalized, with deduplication per offence key.
- **Boundary.** The F11 construction does not prove fork choice, both branches finalized, or anything
  about unpaused rounds. One precondition is unverified live: the offer step rejects with
  `SlashEvidenceInvalid` before the duplicate check when the snapshot epoch differs from the vote
  epoch, so the route needs the epoch unchanged from height 1 to height 2. Until the live run happens,
  the typed-duplicate re-extraction is a construction with a driver, not an observation.

## 6. `MULTI_TARGET` — forging a quorum by transplanting signer sets

- **Exercises.** Whether an adversary holding control of some seats can graft a quorum's signer set
  onto a target seat and obtain a certificate that verifies — the "multi-target" route to a forged
  quorum.
- **Injection.** Equivocation plus artifact assembly: the driver calls the artifact and
  QC-assembly routes to build candidate certificates whose signer sets are transplanted across
  targets, then submits them to the node's verification path.
- **Observed.** The control is part of the result: the **legitimate** side-A certificate verified in
  every pair (378 of 378 in the first pass), and the transplanted side B never verified in any pair.
  First pass (`20260911T154517Z`): 378 pair attempts, 380 checks passed, **0 successful forgeries**,
  0 false positives, 0 honest seats named. Wall-clock per pair 1,336.3–2,870.7 ms (median
  1,898.7 ms); decode 43.051 ms, extract 61 µs, offer 942.937 ms, verify 158.246 ms. 379
  administrative calls, 469,656,610 bytes, 728.93 s of local-control time.
  Second pass on the extended target set (`20260913T064402Z`): 447 pairs, 378 attempts, **899 checks
  passed**, 0 successes, 0 false positives, 0 honest seats named. That pass also carries the explicit
  fail-closed controls: every same-set transplant was claimed and rejected as invalid evidence and
  never named; a whole foreign certificate presented as either side, in each of the three phases, drew
  a contract-valid reply with a typed reason — an unknown validator set when presented as one side,
  a coordinate mismatch on the validator-set identifier when presented as the other; every cross-set
  foreign entry was claimed and rejected and never named; no transplanted entry was ever verified
  (`verified_transplants == 0` over same-set and cross-set); and the extraction node's memory and
  process counts stayed inside their committed bounds (≤ 256 MiB growth and ≤ +16 processes over the
  burst). 449 administrative calls, 552,717,548 bytes, 526.186 s. The certificate sizes released by
  the live node in that pass are recorded in `measurements.md`.
- **Recorded result.** **passed** in both passes, as an input-validation-regime scenario.
- **Claim supported.** That on this fixture, with this fault route, 378 transplant attempts over a
  447-pair target set produced no certificate that the node's verifier accepted, and named no honest
  seat — while the legitimate certificate in the same pairs did verify, so the route was exercised
  rather than inert. The fail-closed reading is the one the record commits to: an unverifiable
  transplant is rejected with a typed reason and never named, rather than accepted in silence.
- **Boundary.** **378 attempts is a count of what was tried, not a bound on what exists.** A bounded
  devnet run with no successful transplant is not evidence that no transplant exists, and it is not
  evidence about the construction: it is evidence that this implementation's verification path did not
  accept these particular attempts on this host. No attack on the cryptography is implied in either
  direction.

## 7. `MALFORMED_CERTIFICATE` — malformed and vacuous inputs

- **Exercises.** Whether malformed, truncated and vacuous certificates are rejected rather than
  accepted, and whether rejection is typed.
- **Injection.** Certificates are truncated, re-encoded, emptied and otherwise corrupted, then offered
  to the node's verification path. One case in the committed taxonomy — `index_out_of_range` — is not
  constructible in this fixture; the driver originally recorded it `not_run`, which is the campaign's
  finding F2.
- **Observed.** 30 checks passed on run `20260911T153826Z` (17 administrative calls, 11,840,217 bytes,
  2.589 s of local-control time) — **15 cases, each checked twice**: once that the reply was
  contract-valid with the safety bytes byte-identical, and once that the rejection was the *predicted
  typed* rejection. The decode cases are truncated, trailing byte, flipped magic, flipped version,
  invalid phase, non-zero flags, count not equal to the bitmap's population count, a moved bitmap bit,
  a duplicate index, an index ≥ 64, and a signature-length overrun; the extraction cases are the
  signature-length boundary values 3,309 / 4,626 / 4,628 and a below-quorum certificate. Every case
  was rejected with the predicted type; none was accepted. The `index_out_of_range` case is recorded
  `not_applicable` in the corrected taxonomy rather than `not_run`.
- **Recorded result.** **passed**, 30 checks. An earlier record of the same scenario was `not_run`
  and no longer counts; F2 is the correction of that driver behaviour, not a defect of the node.
- **Claim supported.** That this implementation rejects the malformed and vacuous certificate shapes
  in the committed taxonomy — including the empty and zero-signer frames — rather than accepting them.
- **Boundary.** Input validation, not soundness. Rejecting a malformed certificate says nothing about
  whether a well-formed but forged one would verify; that question belongs to the `MULTI_TARGET`
  entry, and its answer there is likewise bounded.

## 8. `REJECTION_STREAM` — sustained rejections and resource behaviour

- **Exercises.** Whether a sustained stream of rejected inputs leaks resources, changes durable
  state, or accumulates processes. Two classes of defect found by the independent audit stack in a
  different implementation motivated the scenario: the per-rejection resource leak (the audit stack's
  own F1 class) and vacuous acceptance (its F2 class). Those are the audit stack's numbers, not this
  campaign's.
- **Injection.** 240 rejection calls in a stream, plus three vacuous inputs (an empty frame, a
  zero-signer frame, and a candidate-flip case), all offered to the node's verification path on the
  C = 22 fixture with the client and evidence checks held constant.
- **Observed.** 9 checks passed, against pre-committed resource thresholds. 243 attempts, 0 successes.
  Every stream call returned a typed client error — **240/240, no 5xx and no 2xx**; the three vacuous
  inputs never named anyone, with typed reasons `vacuous:empty-hex` → `decode.a:TooShort`,
  `vacuous:zero-signer` → `NotAQuorum{got:0,need:43}` and `vacuous:candidate-flip` →
  `SlashEvidenceInvalid`. Canonical re-encoding of every corpus certificate was byte-identical to the
  node's bytes, so no encoding ambiguity was available to exploit. The safety bytes were identical
  around the whole stream; durable state did not change on rejection. Resident memory grew 6,039,798
  bytes over the run, and the per-call fit over 7 points gives a slope of 18,827.56 B/call (intercept
  21,507,416.8; peak RSS 27,577,548) — inside the committed bound that the slope times the stream
  length stay under 64 MiB and the total delta under 128 MiB. Process count delta 0, inside the
  committed bound of +8. The statistics counter's delta equalled the calls issued, every error key was
  a known contract key, and the node's log tail contains no panic. Four administrative calls,
  1,212,103 bytes, 2.028 s of local-control time.
- **Recorded result.** **passed**, 9 checks.
- **Claim supported.** That on this fixture the node answered every rejection with a typed client
  error, changed no durable state, and spawned no process; and that its resident-memory growth under
  a 240-call rejection stream is 18,827.56 bytes per call over a 7-point fit.
- **Boundary.** A 240-call stream is a short window, not a soak; the RSS slope is a fitted line over 7
  points on one host, not a leak rate law, and it is reported with its arithmetic so a reader can see
  how little it rests on. This scenario does not test the cryptographic reject path — only that
  rejection happens and is typed.

## 9. `DIFFERENTIAL_EXTRACT` — two independent verifiers on the same certificates

- **Exercises.** Whether an independent extraction and verification implementation agrees with the
  node on the same certificates: the differential-testing item of the audit stack, run against the
  node's own output.
- **Injection.** No fault is injected into the node. The independent extractor, with its own vendored
  ML-DSA-87 implementation, is run over the same certificates the node produced, and the two sets of
  names are compared.
- **Observed.** 17 checks passed. **258 of 258 (6 × 43)** signatures verified by the independent
  implementation; the independent decoder equalled the harness decoder on all 6 certificates, and the
  independent canonical re-encoding was byte-identical to the node's bytes on all 6. The validator-set
  identifier the independent code computed from the canonical snapshot equalled the certificates'
  field. For each of the three case families — identity, distinction and relation — four checks
  passed: the naming cross-check between decoded evidence votes and the accused identity, a
  contract-valid reply with identical safety bytes, agreement between the node and the independent
  implementation on claims, vote digests, verdicts and names, and an independently named set equal to
  the 22 double-signers with no honest seat named. The error-taxonomy differential agrees across the
  node, the independent implementation and the committed expectation on 24 of 24 constructible cases,
  with `index_out_of_range` recorded `not_applicable`.
- **Recorded result.** **passed**, 17 checks.
- **Claim supported.** That for the certificates in this run, an implementation written separately
  from the node verified every one of the 258 signatures and extracted the same signer names, with
  zero disagreements — and therefore that no spec gap or one-sided bug surfaced in this sample.
- **Boundary.** Agreement on one certificate set is not a proof of equivalence between the two
  implementations, and the independent implementation is itself unaudited here. A disagreement would
  have been a finding; the absence of one in this sample is reported as agreement, not as correctness.

## 10. `PARTIAL_NETWORK` and `PARTIAL_NETWORK-liveness` — partition, delay and heal

- **Exercises.** Partition of the 64-seat cluster, delay and loss on the collector's routes, the halt
  window with 32 seats on each side, and heal reachability — then, separately, whether the cluster
  still makes progress across the partition.
- **Injection.** Network emulation moved into the containers: a `prio` root queueing discipline with
  `netem delay 200ms loss 5%` on one band and `u32` destination filters on the collector's routes to
  the partitioned seats, installed in one batch; plus in-container packet filtering with a per-seat
  `iptables-save -c` census and a directed 64 × 63 in-container probe matrix. The original step
  depended on a tool with no scope over the emulated seats, which made the whole record a certain
  `not_run` — the finding F12.
- **Observed.** The record was split, and neither part has run live. `PARTIAL_NETWORK` now holds only
  finality-free checks: emulation mechanics, both partitions' mechanics, the 32|32 halt window, heal
  reachability, and all 64 seats at the baseline height with one root. `PARTIAL_NETWORK-liveness`
  holds the progress checks and records `not_run` with the reason "blocked by F8" while liveness is
  absent. The committed chain outcome was not changed by the split.
- **Recorded result.** **not run live** (both parts). No check is reported as passed.
- **Claim supported.** Nothing yet. The split itself supports one statement: that a record mixing
  finality-dependent and finality-free checks hides the finality-free ones, and that an emulation step
  with no scope over the target seats is a structured `not_run` rather than a failure of the system
  under test.
- **Boundary.** Partition tolerance and liveness at 64 seats under an unpaused round remain `not_run`,
  not passed. No result here may be read as evidence that the cluster survives a partition.

## 11. `MESSAGE_FAULTS` — reorder and delay during an unpaused round

- **Exercises.** Whether an unpaused 64-seat round tolerates message duplication, reordering, loss and
  one-seat clock skew.
- **Injection.** Duplication, reordering, loss and a one-seat clock skew injected during an unpaused
  round at 64 seats.
- **Observed.** Nothing — the scenario commits an unpaused 64-seat round and **has not run** on the
  fixed binary. The calibration gate `UNPAUSED_BASELINE` (entry 1) is its baseline round and passed;
  the scenario itself has not been executed.
- **Recorded result.** **not run.** Not re-expected before it runs.
- **Claim supported.** Nothing.
- **Boundary.** The fault taxonomy claim in `README.md` — that the faults used in the games
  correspond to faults a real implementation can be driven into — rests, for the delay/drop/reorder
  family, on the emulation mechanics of entry 10 and on this scenario's specification. Until this
  scenario runs, that part of the claim is constructed but not observed.

## 12. `WITHHELD_CERTIFICATE` and `SOAK64` — never unpause

- **Exercises.** Withholding a certificate that a seat is expected to reveal, and a long adversarial
  soak at 64 seats.
- **Injection.** Not run. Both scenarios are committed for unpaused 64-seat rounds, but in the current
  driver **neither unpauses**: `WITHHELD_CERTIFICATE`'s committed "new view finalizes" step is not
  driven — only the view advance is — and `SOAK64` is bounded by its soak-seconds option.
- **Observed.** Nothing. Which binary these two should run on is an **open question** recorded in
  `open-items.md`.
- **Recorded result.** **not run**, both.
- **Claim supported.** Nothing.
- **Boundary.** No 64-seat soak has been run anywhere in this campaign. The only long-running soak in
  the record is at four nodes, and it is not a 64-seat result. Withholding behaviour is therefore
  `not_run`, not passed.

---

## Reporting rules used above

- **Regimes are never merged.** Within-model, outside-model and input-validation results are reported
  in their own regimes, and no total is given that adds them.
- **A devnet result is never a security level.** No entry above is a statement about the
  construction's security; each is a statement about what this implementation did under this fault on
  this host.
- **A profile-qualified result stays qualified.** A `mainnet`-profile pass never closes a finding for
  the debug build, and no scenario result transfers between profiles.
- **Two attacker-cost columns are never added.** Where a record carries a theoretical (ledger) column
  and a measured (run) column, they are reported separately and never summed.
- **A `not_run` is never a pass**, and an expectation is not re-stated before it runs.
