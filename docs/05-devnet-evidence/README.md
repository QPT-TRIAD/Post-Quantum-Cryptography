# 05 — Devnet evidence

This package is the record of what was actually run when the operational premises behind this
programme's claims were exercised on a live, multi-node ledger devnet. It answers four questions
about each test: what was exercised, how the fault was injected, what the node did, and what the
result does and does not support.

The ledger implementation under test is a **different repository**. None of its source, configuration
or key material is copied here, and nothing in this package is part of the cryptographic argument
chain. What ships is the *evidence*: run identifiers, injected faults, observed behaviour, recorded
pass/fail, and the specific claim each result is allowed to support. The devnet is an independent
implementation of the quorum ledger; a disagreement between it and the models in this repository is
evidence about the models, not a bug report about either side.

## Why a separate ledger was involved at all

The construction in `docs/03-construction` is a *quorum* construction: it assumes a set of seats, a
threshold, and a signing discipline. Most of its content can be checked in isolation — games,
extractors, wire sizes, model checkers — and is checked that way in the domain packages. Three things
cannot be:

1. that the **signing discipline** ("at most one message per seat per domain") actually holds when a
   real node restarts, restores a backup, or is rolled back;
2. that the **liveness** assumptions hold at realistic scale — 64 seats — on real hardware;
3. that the **fault taxonomy** used in the games corresponds to faults a real implementation can be
   driven into.

Every test in this package attacks one of those three. Nothing here attacks the cryptography.

## How to read this package

| Document | What it holds |
|---|---|
| `test-campaign.md` | One entry per test: what it exercises, how the fault was injected, what was observed, the pass/fail as recorded, and the claim the result supports. Includes the tests that failed and the tests recorded `not_run`, with reasons. |
| `measurements.md` | The numbers: certificate and frame sizes as released by a live node, timings, message counts, the release-measurement reconciliation, and the deduplication observations — each with the run that produced it and whether it is a single run or a repeated one. |
| `environment.md` | How the devnet was stood up: node count, topology, fault-injection mechanism, container-level network shaping, pinned binary profile, and what the in-container emulation can and cannot emulate. Lists the items this host could not complete. |
| `open-items.md` | The tests not finished and the questions left open, each with what it would take to close it — including re-runs on the fixed binary and the runs never possible in this environment. |
| `VERIFICATION.md` | The verification mode for this package: no row here was produced by a run in this repository. What was checked in this tree, row by row, with the command and the observed result — the arithmetic, the released sizes, the digests, the run identifiers — plus what cannot be checked here and why, and the places where the sources disagree with each other. |

## The standing caveat

Read this before any number in this package.

**A devnet is a controlled, small, single-operator network.** Every run recorded here took place on
one 12-core host, under one operator, with an exclusive host lock, against 64-seat fixtures that the
records themselves mark `NON-NORMATIVE DEVNET TEST FIXTURE - NOT A RATIFIED MAINNET GENESIS VALUE`.
The fixture's parameters are n = 64 seats, f = 21, quorum q = 43, overlap bound 2q − n = 22. The only
deviations from 64 seats in this package are a 32-seat scale probe used as a comparison inside the
liveness arms, and a four-node soak recorded in the same testbed, which is not a 64-seat result.

Four consequences follow, and they are the reason this package exists as a separate document rather
than as paragraphs inside the domain packages:

1. **What passes here bounds the *implementation's* behaviour under the injected faults.** A passing
   check says: when this fault was injected into this build on this host, the node did this. It does
   not say the construction is secure, that the fault cannot be exploited elsewhere, or that a
   different implementation would behave the same way.
2. **Passing these tests says nothing about the cryptographic claims.** The QPT-128 claim rests on
   the ledger row and its named assumptions, which no devnet run changes. A devnet result is never a
   security level, and it is never promoted into evidence for the construction.
3. **Absence of an attack in a bounded run is not absence of the attack.** Where a scenario was run
   and no conflict, no forgery and no false attribution was observed, the record states how many
   attempts were made, over what target set, with what result — and does not read the zero as
   impossibility. The relevant runs made 378 attempts against named targets and observed zero
   successful transplants; 378 is a count of what was tried, not a bound on what exists.
4. **A `not_run` is never a pass.** Records in this campaign distinguish `passed`, `failed` and
   `not_run`, and where a check could not run the reason is carried with it. Nothing in this package
   softens a `not_run` into an absence of findings.

## Measurements and observations of a running system

The assignment of terms is deliberate and is used consistently across the four documents:

| Kind | What it is | Examples in this package |
|---|---|---|
| **Measurement** | A number read off a running node or a record file: a byte count, a check count, a timestamp delta, a resource sample. Reproducible only in the sense that the record is on disk. | Released frame sizes; `/v1/status` latency percentiles; container CPU sum; host iowait samples; per-call RSS slope; extraction counts. |
| **Observation of a running system** | A statement about what a live system did when driven: did the round finalize, did the seat refuse to start, did the guard reject the record. Single-run by construction; the count of occurrences is part of the observation. | Whether an unpaused 64-seat round finalized at all; whether a restarted seat released a conflicting vote; whether typed rejections were returned for every malformed input. |
| **Derived count** | Arithmetic on recorded values, stated with the arithmetic. | The 199,099 B + 43 × 6 B = 199,357 B reconciliation in `measurements.md`. |

The records themselves label their timings `LOCAL-CONTROL OBSERVATION; NOT A NETWORK BENCHMARK OR
CONSENSUS TIMING`, and this package keeps that label attached. No number here is a benchmark, a
throughput figure, or a distribution over repeated trials; where a figure is a median it is a median
of three attempts, and the document says so.

## What the runs support, and what they do not

**What the runs support**, and nothing wider:

- that the signing discipline needs an explicit monotonicity premise, and that a restore is inside the
  signer boundary (A27);
- that a typed duplicate offence can be built at n = 64 from a real extraction whose evidence was
  finalized — construction and driver; the live run is pending, so it is not yet an observation;
- that the fault taxonomy used in the games corresponds to faults a real implementation can be driven
  into: partition, delay, drop, halt, heal, reorder and reveal-withholding;
- that a 64-seat round can finalize on this hardware with a release-quality build, and that the debug
  build cannot be used for unpaused 64-seat liveness on this host.

**What the runs do not support**, and this list is as load-bearing as the one above:

- any claim about throughput or latency as a property of the construction — single host, local
  control, storage-sensitive;
- the F8 mechanism: state-file fsyncs held under the node mutex is an inference, not isolated;
- partition tolerance or liveness at 64 seats under an unpaused round — which is exactly what is still
  `not_run`.

## What this evidence changed in the research record

Two corrections were forced by these runs and are recorded in `records/failed-assumptions.md`:

- **A27** — an implicit assumption that an honest seat stays honest across a restore was refuted. The
  honesty condition must be stated over signer state that is **monotone**; a fleet-wide restore from
  one backup can push the corruption count C from ≤ 21 (no conflict possible) to ≥ 22 (conflicting
  certificates possible, all attributable). The SAFETY and threshold statements in the domain
  documents therefore carry the additional premise "seats whose signer state is monotone", and the
  live re-run of the test on the fixed binary is pending (`open-items.md`).
- **A28** — a fix-stage claim of "16/16 and 16/16" for a property layer was **withdrawn**: re-running
  in a rebuilt environment gives 16 passes for the Mode B property module and a **collection error,
  0 tests executed**, for the hash-signature property module, which constructs a mixed key at import
  that the corresponding fix now correctly refuses. The archived fix log shows the same crash, so only
  the Mode B figure stands; the fixes themselves remain regression-tested by the v2.2 self-test
  (15/15), and the correction note is carried in `records/fixes.md`. This is a re-run result, not a
  devnet result, and it is recorded in `records/` because `records/` owns it.

Neither correction originates in this package. The findings themselves — the run identifiers, the
observed values and the disposition of each — are indexed here because the runs that produced them
are devnet runs, and referenced rather than duplicated where `records/` is the canonical owner.

## What this package deliberately does not do

- It does not copy, quote or paraphrase the ledger implementation's source, configuration, compose
  files, keys or logs. Those are excluded by construction; the exclusion is recorded once here.
- It does not restate a finding that `records/` owns. A27 and A28 are referenced by their identifiers
  with a one-line consequence, never rewritten.
- It does not promote a result. A passing check is reported as a passing check on a named build in a
  named environment; the words used to describe it are the words the record uses.
- It does not merge regimes. The campaign reports within-model, outside-model and input-validation
  results separately, and never as a single total.
- It does not treat the calibration gate as a scenario result. `UNPAUSED_BASELINE` is a gate that a
  binary must pass before other scenarios may run on it; passing it does not close any finding.
- It does not recompute a size, a probability or a byte count that the record already states. Where
  arithmetic on recorded values is shown, the inputs and the arithmetic are both given.

## Gaps in one paragraph

Stated in full in `open-items.md`. In short: the unpaused 64-seat scenarios that depend on liveness
have not run — `MESSAGE_FAULTS`, `WITHHELD_CERTIFICATE` and the progress half of `PARTIAL_NETWORK`
(`PARTIAL_NETWORK-liveness`) are recorded `not_run` with reasons, and a mainnet-profile calibration
pass does not close the debug build's stall. The `KEY_ROLLBACK` finding (A27) and the `REPLAY`
typed-duplicate construction are fixed in code but the live re-runs are pending, so both records keep
their recorded status. No 64-seat soak has been run at all; the only long soak in the campaign is at
four nodes. The mechanism proposed for the liveness stall — state-file fsyncs held under the node
mutex while host storage is saturated — is an **inference, not isolated**, and the observation that
storage pressure arose within a single round on a verified-quiet host makes it a live question rather
than a closed one. Partition tolerance and liveness at 64 seats under an unpaused round remain
`not_run`, not passed.
