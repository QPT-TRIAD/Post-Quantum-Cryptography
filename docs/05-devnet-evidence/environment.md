# The devnet environment

This document records how the devnet was stood up and configured, so that a reader can judge what a
result from it does and does not cover. It describes the testbed's behaviour and configuration as
observation; the ledger implementation's own source, compose files, configuration and key material are
**not** part of this repository and are not reproduced here.

## 1. The host

| Item | Value |
|---|---|
| Host | One shared machine, 12 cores available to the testbed |
| Storage | One local consumer NVMe SSD (device internals not observed) |
| Concurrency | Exclusive host lock: one scenario at a time, no other testbed containers running |
| Operator | Single operator; every scenario driven from one side |
| Quiet-host precheck | Before every bring-up: a rolling 60 s window requiring iowait < 5 % and no other testbed containers, for up to 600 s; otherwise the scenario records `not_run` with the reason "host not quiet" and the samples |
| In-run sampling | A host I/O sampler at 5 s intervals during every scenario; the post-fix liveness arms added 1 s iowait, disk statistics, PSI and dirty-page readings, container block I/O, and per-sweep failed seats with per-seat view and height |

The precheck exists because the campaign's own results depend on host storage state (see
`measurements.md` §4). It did not prevent the dependency: the calibration round ran after a precheck
showing iowait ≤ 0.13 % over 60 s and still drove host iowait to 92 % inside the round. The precheck
bounds the starting state, not the state during the run.

## 2. The cluster

| Item | Value |
|---|---|
| Seats (nodes) in the main fixture | **64**, one container per seat |
| Fixture parameters | n = 64, f = 21, quorum q = 43, overlap bound 2q − n = 22 |
| Fixture status | marked in the records `NON-NORMATIVE DEVNET TEST FIXTURE - NOT A RATIFIED MAINNET GENESIS VALUE` |
| Bring-up | a fresh cluster rendered and started per scenario; no seat carried state between scenarios unless the scenario was about exactly that |
| Smaller clusters | a 4-node matrix was run earlier for the same campaign; a 32-seat scale probe (`20260913T125634Z`, arm C) and a 64-seat cluster are the sizes used in the results in this package |
| Collector | one collector component receives artifacts; its routes to the partitioned seats are what the network shaping targets |
| Probe matrix | a directed **64 × 63** in-container probe matrix (every seat to every other seat) when network state is under test |

The 4-node matrix's results belong to the independent-audit domain's account and are not restated
here; this package reports the 64-seat campaign and names the smaller runs only where they are part of
a comparison (the n = 32 scale probe in the liveness arms).

## 3. Fault injection

Three families of mechanism were used, and each scenario entry in `test-campaign.md` names which one
it used.

**In-process fault routes on the node.** The node exposes administrative fault endpoints used only by
the harness: `/devnet/equivocate` (a seat votes for two conflicting candidates), `/devnet/dual-proposal`
(two proposals at one height), `/devnet/artifact` and `/devnet/assemble-qc` (artifact retrieval and
certificate assembly, used to build the multi-target transplant candidates), `/devnet/withhold` (a seat
withholds a certificate it is expected to reveal), `/devnet/pause` (pauses the unpaused rounds, which
is how the paused scenarios are driven), and `/devnet/ceqs-extract`, `/devnet/safety`, `/devnet/key`
and `/devnet/history` for extraction, safety state, key state and history inspection. Normal client
traffic goes through the client intent route and the peer relay route; the peer and client paths differ
deliberately in their duplicate handling (see `measurements.md` §7).

**State manipulation on the seat's own volume.** For the restart and rollback scenarios the harness
copies files into and out of a running seat's container: the signing journal copied from *before* one
of the seat's own votes, reinstalled over the seat's current data volume, followed by a restart
(`KEY_ROLLBACK`); a seat held back and then caught up (`STALE_STATE`); a seat restarted to observe
readiness. Both restarts in these scenarios took 7.1 s.

**Input mutation.** For the malformed, vacuous and rejection scenarios the harness mutates certificates
— truncation, re-encoding, emptying, an all-zero signer bitmap, a candidate flip — and offers them to
the node's verification path, in a single stream of 240 calls in the rejection scenario. One case in
the committed taxonomy, `index_out_of_range`, is not constructible in this fixture and is recorded
`not_applicable`.

Clock skew is injected at the seat level by interposing a time-shifting library on the process, so that
one seat's clock differs from the others. It belongs to the `MESSAGE_FAULTS` scenario, which has not
run live.

## 4. Container-level network shaping

Shaping is done **inside the containers**, not on the host, and this is a deliberate correction
recorded as the campaign's finding F12.

| Layer | Mechanism |
|---|---|
| Root queueing discipline | `prio` |
| Delay and loss | `netem delay 200ms loss 5%` on one band |
| Direction | `u32` destination filters on the collector's routes to the partitioned seats |
| Installation | all shaping installed in one `tc -batch` invocation per container, so the state is applied atomically |
| Packet filtering | in-container packet filter rules restored with `iptables-restore --noflush`, with a per-seat `iptables-save -c` census proving what each seat actually had installed |
| Verification | a directed 64 × 63 in-container probe matrix, seat to seat, to establish which pairs can reach each other before, during and after the partitioning |
| Partition shapes | a 32|32 halt window (32 seats each side), heal reachability, and the baseline height with one root across all 64 seats |

The original step used a host-level network-shaping tool that had no scope over the emulated seats.
That step could therefore only ever record `not_run`, and because one `not_run` makes a whole record
`not_run`, the scenario could never close. Moving the shaping into the containers is what made the
mechanism observable at all.

### What this emulation can emulate

- Delay, loss, duplication and reordering of messages between seats, at the configured rates.
- Reachability partitions between arbitrary sets of seats, in both directions, verified by the probe
  matrix rather than assumed from the rules being installed.
- A halt window with the cluster split in half, and heal afterwards.
- One seat's clock differing from the rest.
- Message-level adversarial behaviour: equivocation, dual proposals, withheld certificates, replayed
  certificates.
- Seat-local state faults: restart, journal rollback, falling behind and catching up.
- Malformed, vacuous and adversarial input at client and peer boundaries, sustained.
- Resource pressure as a consequence of input, observed from outside the container.

### What it cannot emulate

- **No host-level or multi-host network state.** Everything is inside one host's networking stack;
  there is no real wide-area latency, no independent path selection, no cross-host partition, and no
  failure mode that depends on the host's own network stack rather than the container's.
- **No independent operators.** One operator drives everything. Nothing here tests behaviour against
  an operator who is themselves faulty, unavailable or adversarial at the same time.
- **No validator churn.** Registry changes, validator set changes and key rotation are not
  constructible in this environment; the fixture's seat set is fixed for the life of a run.
- **No hardware root of trust.** A hardware anti-rollback counter is outside the software boundary the
  testbed controls: the signing-journal guard the rollback scenario exercises is software state, and a
  rollback that moves *every* local record backwards — including whatever a hardware counter would have
  protected — is explicitly outside the boundary the campaign decided on.
- **No storage-fault injection.** The host's storage behaviour is observed, not controlled: the run
  that stalled did so while the SSD was in a degraded write state left by a preceding heavy arm, and
  the isolating experiments (repeat under a controlled write load, after a long idle, with node data on
  a memory filesystem) were **not run**. The proposed mechanism — state-file fsyncs held under the node
  mutex — is an inference, not isolated.
- **No long soak.** The 24-hour soak form has not been run at 64 seats anywhere; the four-node soak is
  not a 64-seat result.
- **No real concurrency of uncertainty.** Because the host lock serialises scenarios, every result is a
  single clean run on an otherwise idle machine, except where the previous arm's writes are still being
  absorbed by the storage device — which is exactly the effect that made two identical runs differ by
  57 s.

## 5. The node binary, and the binary policy

Two profiles ran, and every result in this package is profile-qualified.

| Profile | Use | How it is produced |
|---|---|---|
| Debug (default) | **Paused** scenarios | The testbed's default rendering mounts the debug node binary; the harness builds it in place |
| `mainnet` | **Unpaused** 64-seat scenarios | The ledger repository's own `mainnet` build profile: release, fat link-time optimization, overflow checks on, debug symbols at level 1. The build command is the repository's; it is not reproduced here |

The policy exists because the default debug rendering is not usable for the unpaused 64-seat liveness
scenarios on this host — the campaign's finding F13. Three safeguards accompany it:

1. **Verified binary mounting.** An explicit option mounts a given binary read-only, and only after a
   build manifest verifies: sha256 equal, profile in {debug, release, mainnet}, and a sources digest
   equal to a fresh digest of the current sources. After every bring-up, `docker compose config` is
   checked and the in-container sha256 is compared on every seat. If any check fails the driver refuses
   to run and writes no record.
2. **The calibration gate.** `UNPAUSED_BASELINE` — the baseline round of the message-fault scenario, on
   a fresh 64-seat cluster — passes only if the round finalizes **in view 0 within 180 s** with all 64
   seats on one root. It blocks the unpaused scenarios until it passes **on that binary**.
3. **Sequencing.** The quiet-host precheck and the 5 s host I/O sampler described in §1 apply to every
   bring-up.

Recorded binary identities, as sha256 prefixes (the records carry the full digest):

| Binary | sha256 prefix | Profile |
|---|---|---|
| Calibration node (`20260913T143920Z`) | `22026ca8…` | `mainnet` |
| Debug, pre-fix (arms A, B/B2 reference) | `c1479f2e…` | debug |
| Release, pre-fix (arm B/B2) | `96e30f0b…` | release |
| Debug, post-fix (arm D) | `42f6fe2a…` | debug |
| Release, post-fix (arms E/E2) | `dc4deff6…` | release |

The calibration node's sources digest is `e0f5687c…`. The pre-fix and post-fix source snapshots differ
in four files. The debug post-fix build was produced by an incremental build with no version-control
identity available at the time, so the record notes that the debug builds also differ in date and build
state — a non-isolation the record states rather than hides.

**A `mainnet`-profile pass never closes a finding for the debug build.** Paused scenarios stayed on the
debug binary throughout, and which binary the two scenarios that never unpause should use is an open
question (`open-items.md`).

## 6. What this environment could not complete

Carried here from the campaign's own status, and expanded in `open-items.md`:

- **The unpaused 64-seat liveness scenarios.** `MESSAGE_FAULTS` and `PARTIAL_NETWORK-liveness` are
  `not_run`; `PARTIAL_NETWORK` and `WITHHELD_CERTIFICATE` have not run live either.
- **No 64-seat soak**, at any duration.
- **The isolating experiments for the storage stall** (controlled write load, long idle, node data on a
  memory filesystem) were not run, so the fsync-under-mutex mechanism remains an inference.
- **The live re-runs on the fixed binary** — `KEY_ROLLBACK`, the `REPLAY` typed-duplicate construction —
  are pending, so both records keep their recorded status.
- **The corruption-count sweep was incomplete when the testbed status was written.** That status lists
  only C-21 and C-22 as having passing records in a completed summary. The archive nevertheless
  contains a **complete 28-point sweep** at run `20260911T134816Z` (`complete: true`, 22 within-model
  points C-0 … C-21 and 6 outside-model points C-22 … C-26 including the one-sided form, 0 failed,
  0 `not_run`), and the testbed's own naming correction against it is its finding F1. This package
  reports the campaign runs it has records for; the sweep's claim belongs to another domain and is not
  restated here.
- **No independent implementation** of the network, clock or storage layers; there is no second
  implementation of the node to disagree with this one.

## 7. What is not in this repository

The ledger implementation, its devnet harness, its chaos tooling, its compose rendering, its fixture
definitions and its keys are excluded. This package records what the testbed *did* and *returned*, in
the testbed's own vocabulary and with its own run identifiers. Nothing here is a substitute for that
implementation, and no result here can be reproduced without it.
