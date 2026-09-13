# The epoch-barrier model, explained as a specification

This document explains what the model in `formal/epoch-barrier.tla` is, what each invariant named in
`formal/epoch-barrier.cfg` is intended to capture, what the recorded model-check output says, and what
the executable checkers in `src/` actually cover.

One statement belongs at the top, because it is the statement most easily lost: **the model-check was
not re-run for this repository, and no TLC or TLAPS run has been performed at any point in the
record.** The TLA+ files are specification documents. The recorded output ships as recorded. The
environment in which this repository was assembled has Java (OpenJDK 21.0.12) but no `tla2tools.jar`
and no other TLA+ tooling, so every TLA+ item is marked `not-run` in `VERIFICATION.md`, with that
reason. The only items in this domain that were executed here are the two Python checkers, whose
results reproduced exactly (§7).

## 1. Which revision of the specification survives here

The surviving specification is the **v0.6 revision** of the epoch-barrier model. The version suffix
has been dropped because it is the only revision preserved in this repository; the file map's `copy`
row is that artifact.

The current research record names a v0.7 module instead, `PQAQCEpochBarrier_v0_7.tla` with its
configuration (`docs/research-proof-documentation.md:3050-3051`), and describes it as materially
different from v0.6: competing boundaries representable, conflict domains indexed, crash state split
into volatile and durable, partitions affecting seal delivery (`:3080-3085`). **Neither v0.7 file is
preserved here**, so the v0.7 model cannot be inspected and nothing in this document describes it
beyond quoting the record's own list. The surviving v0.6 artifact is precisely the revision the v0.7
correction record was written against (`:79-212`), which is why §4 below reads as a list of the things
that revision does not represent.

Two mechanical facts about the surviving artifact were established by reading it, and both matter to
anyone attempting a TLC run:

- the file name `formal/epoch-barrier.tla` does not match its `MODULE epoch_barrier` line, because a
  TLA+ identifier cannot contain a hyphen (`formal/epoch-barrier.tla:1`). TLA+ tooling expects the
  file name to equal the module name, so a run needs the file renamed or the module line changed back;
- the configuration therefore has to be passed explicitly, for example with
  `-config formal/epoch-barrier.cfg`.

Both are recorded in the repository notes carried by the two files, and both are re-checked in
`VERIFICATION.md`.

## 2. The model, read as a specification

The module is a four-node safety specification of the epoch barrier. Its declared constants
(`formal/epoch-barrier.tla:4-5`) are `Nodes`, `F`, `Q`, `Epochs`, `Domains`, `Messages`, `Sessions`,
`Preps`, `EvidenceRoots` and `Boundaries`, with two assumptions (`:7-8`):

```
ASSUME Q = 2 * F + 1
ASSUME Cardinality(Nodes) = 3 * F + 1
```

The shipped configuration (`formal/epoch-barrier.cfg:3-13`) sets `F = 1`, `Q = 3`,
`Nodes = {0,1,2,3}`, `Epochs = {0,1}`, `Domains = {0}`, `Messages = {0,1}`, `Sessions = {0,1}`,
`Preps = {0}`, `EvidenceRoots = {0}`, `Boundaries = {0,1}`. The reference committee of the domain is
`n = 3f + 1` with `q = 2f + 1` (`docs/definitions-and-conflict-extraction.md` §2-§3); the bounded
instance is the smallest non-trivial one, `f = 1`, four seats, quorum three.

Pointers are `path:line` into the files of this directory. A bare `:NNN` continues the file named
most recently in the surrounding text; where a table is introduced by a sentence naming a file, bare
pointers in that table refer to the same file.

The ten state variables (`formal/epoch-barrier.tla:10-20`) and their intended meaning:

| Variable | Intended meaning |
|---|---|
| `epoch` | one epoch index per node, 0 (old epoch) or 1 (activated epoch) |
| `voteChoice` | the ordinary vote a node has cast, or `None` |
| `prepPhase`, `prepSession` | preprocessing-object lifetime: `"U"` unused, `"R"` reserved, `"E"` emitted, `"B"` burned, with the session a reserved object belongs to |
| `haveEvidence` | set of `<<node, root>>` pairs: evidence the node has retrieved and verified |
| `anchorVotes` | set of `<<node, root>>` pairs: anchor votes the node has cast |
| `finalizedBoundary` | the single boundary the abstract base protocol has finalized, or `None` |
| `sealChoice`, `sealCert` | what each node sealed, and the formed seal certificate |
| `activatedBoundary` | the boundary each node activated against |

Actions and what each is intended to capture (`:42-129`):

| Action | Lines | Intended to capture |
|---|---|---|
| `ReservePrep(i,s)`, `EmitPrep(i)`, `BurnPrep(i)` | `:42-59` | the preprocessing state machine `Unused → Reserved(sid) → Emitted(sid) → Burned`, with `Reserved → Burned` also allowed |
| `OrdinaryVote(i,m)` | `:61-67` | one ordinary vote, in the old epoch, not by a sealed node, never twice |
| `ReceiveEvidence(i,c)` | `:69-72` | retrieving and verifying evidence, unguarded |
| `AnchorVote(i,c)` | `:74-79` | anchoring only for evidence the node holds — the model's rendering of the evidence-before-anchor invariant |
| `FinalizeBoundary(b)` | `:81-85` | abstract base-protocol finality: one boundary, chosen once, with no votes represented |
| `SealAfterFinality(i)` | `:87-93` | sealing only after finality, at most once per node, always the finalized boundary |
| `FormSealCert` | `:98-104` | a seal certificate formed from at least `Q` seal signers on the finalized boundary |
| `Activate(i)` | `:106-113` | activation, only once a seal certificate exists |
| `Crash` | `:115-116` | `UNCHANGED vars` — a stutter step, discussed in §4 |

`Next` is the disjunction of these (`:118-129`) and the specification is
`Spec == Init /\ [][Next]_vars` (`:131`). There is no fairness conjunct and no temporal property, so
no liveness statement — nothing about recovery, progress or eventual activation — is expressible, let
alone checked, in this module.

## 3. The nine configured invariants

`formal/epoch-barrier.cfg:15-23` names nine invariants; all nine are defined in the module
(`formal/epoch-barrier.tla:133-173`). This is a mechanical consistency check that can be re-run
without a model checker and is recorded in `VERIFICATION.md`. The table gives what each is intended to
capture and how it behaves in the surviving revision.

| Invariant | Defined in `formal/epoch-barrier.tla` | Intended to capture | In the surviving revision |
|---|---|---|---|
| `TypeOK` | `:165-173` | each variable stays in its declared domain | type predicate |
| `VoteOnce` | `:133-134` | one vote per node per conflict domain | a type predicate: `voteChoice[i] ∈ Messages ∪ {None}`. The substantive restriction is the guard `voteChoice[i] = None` in `OrdinaryVote` (`:64`), and there is no domain index — one vote for the whole run |
| `PrepNoReuse` | `:136-140` | a preprocessing object is never used for two sessions | a state predicate: phase in `{"U","R","E","B"}`, unused implies no session, used implies a session (`:139-140`). No session history is kept, so two uses of one object are excluded by the absence of any action that could produce them, not by a checked invariant |
| `EvidenceBeforeAnchor` | `:142-144` | the anchoring invariant of the domain's §7 | guard-enforced by `AnchorVote`'s precondition `<<i,c>> \in haveEvidence` (`:76`) |
| `SealOnlyFinalized` | `:146-148` | a node seals only the finalized boundary | guard-enforced: `SealAfterFinality` writes `finalizedBoundary`, which is assigned exactly once |
| `SealUnique` | `:150-151` | a seal choice is a boundary or `None` | type predicate |
| `SealCertOnlyFinalized` | `:153-154` | a seal certificate certifies the finalized boundary | guard-enforced: `FormSealCert` writes `finalizedBoundary`, guarded by `sealCert = None` |
| `SealCertHasQuorum` | `:156-157` | a certificate has at least `Q` seal signers | guard-enforced: `FormSealCert` requires `Cardinality(SealSigners(finalizedBoundary)) >= Q` (`:101`), and `sealChoice` is never decreased once set |
| `ActivationRequiresSealCert` | `:159-163` | activation requires a seal certificate | guard-enforced: `Activate` requires `sealCert # None` and writes `sealCert` (`:108-111`); `epoch` is only ever set from 0 to 1 |

**Reader analysis, not a source claim.** Every configured invariant holds by construction: each is
either a type predicate or is enforced directly by an action guard on variables that never change
after they are set. A TLC run over this module would therefore confirm that the module's guards are
what they are; it would not independently discover a safety property. The record reaches the same
conclusion about one of these invariants from the other direction, in its correction list: of the
v0.6 treatment of boundary uniqueness it states that "two finalized boundaries therefore could not
exist in the state representation" (`docs/research-proof-documentation.md:93`). Section 4 lists the
rest.

## 4. What the surviving revision does not represent

Each item below is a limitation of the artifact, and each is one the v0.7 correction record itself
names (`docs/research-proof-documentation.md:79-212`).

- **No Byzantine behaviour, no adversary.** `Next` offers every node the same guarded actions; there
  is no action that lets a participant deviate. The invariants are therefore statements about a
  system in which every node runs the specification. The quorum-intersection reasoning that gives the
  barrier its safety content lives in the paper argument and in the checker's boundary model, not
  here.
- **No network.** There is no message domain, no delivery relation, no loss, duplication or
  partition. `Messages` (`formal/epoch-barrier.tla:4`) supplies vote payloads only.
- **`Crash` is a stutter.** `Crash == UNCHANGED vars` (`formal/epoch-barrier.tla:115-116`) changes
  nothing, so the module cannot express a state that is lost on restart. The record states plainly
  that this "did not model crash recovery" (`docs/research-proof-documentation.md:119-127`); the
  volatile/durable crash model exists only in the Python checker (v0.7 correction 3, `:119-162`).
- **A second finalized boundary is not representable.** `FinalizeBoundary` requires
  `finalizedBoundary = None` (`formal/epoch-barrier.tla:82`), so boundary uniqueness is assumed by
  the state representation
  rather than derived. The record identifies this as the v0.6 defect that v0.7 corrects by
  representing honest votes, Byzantine votes and independently formable certificates
  (`:91-117`). The correction is not present in the surviving artifact.
- **`Epochs`, `Domains` and `Preps` are declared and never used.** Each of the three identifiers
  occurs exactly once in the module — in the `CONSTANTS` line (`formal/epoch-barrier.tla:4`). The
  configuration instantiates
  them (`formal/epoch-barrier.cfg:7-11`), which makes them look load-bearing. The record confirms the
  defect: v0.6 "declared `Domains` and `Preps` but did not use them in the state machine", and
  `Epochs` was later removed as "a misleading unused parameter"
  (`docs/research-proof-documentation.md:164-184`).
- **Epochs do not iterate.** `epoch[i]` moves at most once, from 0 to 1
  (`formal/epoch-barrier.tla:109`), and nothing resets
  `voteChoice`, the preprocessing phases or the seal choices for a new epoch. The model checks one
  barrier crossing, not a sequence of them.
- **Activation is unconstrained beyond the certificate.**
  `Activate` (`formal/epoch-barrier.tla:106-113`) lets any
  epoch-0 node activate once a seal certificate exists; it does not require that node to have sealed,
  to have validated the embedded configuration, or to have persisted a genesis record. Those steps
  are paper requirements (`docs/research-proof-documentation.md:1227-1260`), not model guards.
- **No fairness, hence no liveness.** See §2.

## 5. The recorded model-check output

The shipped results files are the whole of the recorded output. The lines that speak about TLA+ are
quoted here exactly as recorded, and were not produced in this repository. From the current record
(`results/pqaqc_modelcheck.txt`):

```
IMPORTANT SCOPE
---------------
These are independent finite-state checks, NOT TLC/TLAPS results.
They check the finite abstractions in pqaqc_finite_state_check_v0_7.py.

The TLA+ artifact was also checked mechanically for CFG/TLA invariant-name
consistency. Native TLC was not run in this runtime because tla2tools.jar is
not installed locally.
```

and, at its end:

```
ARTIFACT CONSISTENCY
--------------------
PASS every INVARIANT named in the CFG is defined in the TLA+ module
PASS Domains and Preps are referenced by the actual TLA+ state/actions
```

From the v0.6 record (`history/pqaqc_modelcheck-v0.6.txt:9-11`):

```
TLC status: NOT RUN in this environment.
Reason: Java is installed, but tla2tools.jar is not available locally and external binary acquisition is blocked.
These PASS results are from the independent exhaustive Python checker, not TLC/TLAPS.
```

Three observations on these lines, all of them from reading the surviving artifacts:

1. The first `ARTIFACT CONSISTENCY` line is reproducible against the surviving pair in the weaker
   sense that matters: every one of the nine invariant identifiers in the shipped configuration is
   defined in the shipped module (§3). It cannot be re-verified against the artifacts it was actually
   produced from, which are the v0.7 files, and which are not preserved.
2. The second `ARTIFACT CONSISTENCY` line is **not** true of the surviving v0.6 module: `Domains` and
   `Preps` occur only in its `CONSTANTS` line and are referenced by no state, guard or action. The
   line is consistent with the v0.7 module as the record describes it
   (`docs/research-proof-documentation.md:164-184`), where conflict
   domains and preprocessing objects became real model dimensions. Because that module is absent, the
   line is recorded here as an artifact-scope claim that this repository cannot re-run.
3. No line in either results file reports a TLC execution. There is none to report: the artifact was
   never given to a model checker.

## 6. What the executable checks do cover

The bounded properties that *were* executed are in the Python checkers, not in the TLA+ module. The
current checker (`src/pqaqc_finite_state_check.py`) explores five decomposed finite abstractions
exhaustively, over four nodes with three honest and one Byzantine, two conflict domains, two messages,
two sessions, two preprocessing objects and two boundaries (`:19-30`):

| Model | Lines in `src/pqaqc_finite_state_check.py` | What it explores |
|---|---|---|
| `domain_votes_safe` | `:84-117` | one honest vote per conflict domain — the per-domain vote-once property the TLA+ module does not index |
| `boundary_safe` | `:119-191` | boundary certificates *derived* from honest and Byzantine boundary votes with a quorum threshold, so a fork is representable and is excluded by the honest-vote rule rather than by construction |
| `crash_safe` | `:193-482` | volatile/durable vote and preprocessing state, crash (volatile state lost), restart (reserved or emitted preprocessing burned), and persist-before-send orderings |
| `evidence_safe` | `:484-536` | evidence possession before anchor votes, and quorum formation of an anchor certificate |
| `seal_network_safe` | `:538-666` | seal production, per-node connectivity, explicit partition and heal actions, delivery, and certificate formation from delivered acknowledgements |

Three of the models are re-run with guards deliberately removed as negative controls
(`src/pqaqc_finite_state_check.py:754-770`); each must produce a counterexample or the checker fails
its own assertion (`:797-799`). The partition recovery path (`:679-714`) is executed through the same
transition relation as the safety exploration, and is a reachability witness only — "not a
fairness/liveness proof" (`:681-683`).

The recorded output for the current checker (`results/pqaqc_modelcheck.txt:15-28`) reports state and
transition counts for the five safe models, the three expected failures with their counterexample
paths, and the recovery path. The v0.6 checker
(`history/pqaqc_finite_state_check-v0.6.py`) covers three smaller models — vote/seal/epoch (`:17-67`),
preprocessing (`:84-108`) and evidence/anchor (`:110-133`) — and its "partition recovery" is set
arithmetic on two literals (`:135-141`), which the record itself criticises
(`docs/research-proof-documentation.md:186-190`, correction 5).

**Both checkers were re-run for this repository** in the pinned environment, and both reproduced the
shipped results exactly; the commands, observed output and verdicts are in `VERIFICATION.md`. None of
this is a TLA+ result, and none of it is a proof.

## 7. The decomposition arithmetic

The v0.6 checker decomposes one monolithic state machine into three models because the combined state
space was too large to explore at once. The record states the decomposition and gives the counts
(`history/pqaqc_modelcheck-v0.6.txt:4-7`; `docs/research-proof-documentation.md:69-73`). The reduction
in size can be reconstructed by a reader from the model definitions, and the following is **reader
derivation, not a source claim and not a TLC measurement**:

- the preprocessing model has `7^4 = 2,401` reachable states — per node, unused, or one of three
  phases times two sessions;
- the evidence/anchor model has `3^4 + 9 = 90` reachable states — `3^4 = 81` possession/anchor
  combinations over four nodes, plus the nine combinations in which a certificate can also have
  formed;
- the vote/seal/epoch model has `15,633` states.

The product of the two model counts with the `81` possession/anchor combinations rather than the
evidence model's `90` states, `15,633 × 2,401 × 81 = 3,040,321,473`, is the size of the combined state
space of a module that fuses the three, because the sub-machines share no guard except the anchoring
action's epoch condition, which removes no combination. That arithmetic explains why
decomposition was necessary. It is an argument on paper: no model checker counted those states, and
the number should not be quoted as a measured result. The record's stronger phrase — that the earlier
monolithic model "caught state-space explosion" — has no surviving artifact behind it.

## 8. Proof status of the barrier itself

The epoch barrier's safety claim is the boundary-uniqueness argument sketched in §8 of
`docs/definitions-and-conflict-extraction.md`: two verifying boundary certificates share at least
`f + 1` seats, at most `f` are Byzantine, so an honest validator sealed two boundaries. The record
states the bound as a **reduction sketch**,
`Adv^BoundaryFork ≤ Adv^{MU-QEUF}_ID + ε_rollback + Adv^BaseSafety`
(`docs/research-proof-documentation.md:1181-1221`), and its status matrix records "Boundary
uniqueness — **Paper proof + bounded quorum abstraction checked**" (`:2815`), with TLAPS left "Open"
(`:2819`). The bounded quorum abstraction referred to there is the kind of model the Python
`boundary_safe` check explores; it is not the TLA+ module, which cannot represent a second boundary at
all.

What would be required to raise this from a sketch is set out by the record itself: run the v0.7
model under TLC with safety only and no fairness, reproduce the checker's invariants there, and only
then attempt refinement (`:3078-3089`). Refinement is blocked on a further input: the boundary proof
abstracts finality as a quorum of one-vote-per-honest-validator boundary votes, and the production
proof needs the actual base protocol's proposal rule, lock state, safe-vote predicate and view-change
rule defined first (`:3091-3101`). Until that state machine is frozen, a refinement mapping — the
thing that would connect any model to the implementation — cannot be written.

## 9. Assumption ledger for the model claims

| Assumption | As used | What it limits |
|---|---|---|
| Every modelled participant follows the specification | the TLA+ module's actions are the only actions | the module says nothing about an adversary; Byzantine behaviour appears only in the Python boundary model, as a voter restricted by the quorum rule |
| Four seats, `f = 1`, quorum 3 | `formal/epoch-barrier.cfg:4-6` | the bounded instance is a consistency demonstration, not evidence about `n = 64` |
| Volatile state is exactly what a crash discards | Python `crash_succ` (`src/pqaqc_finite_state_check.py:403-436`) | a single-validator crash model: one node crashes at a time, and the storage layer is assumed to lose volatile state and keep durable state |
| Evidence is retrieved by honest nodes and never by the Byzantine node | Python `evidence_succ` (`:500-526`) | an honest-only evidence model; it checks the anchoring rule within that restriction |
| The Python models correspond informally to the TLA+ module | stated by the record (`docs/research-proof-documentation.md:3068`) | no refinement mapping exists in either direction; the correspondence is asserted, not proved |
| Durable storage does not roll back | consumed by vote-once and seal uniqueness | `ε_rollback` is operational, not negligible; see `docs/definitions-and-conflict-extraction.md` §11 |

## 10. Open items

1. No TLC or TLAPS run exists for any revision of this model. A run needs `tla2tools.jar` in the
   environment and the file-name/module-name mismatch resolved (§1).
2. The v0.7 TLA+ module and configuration are not preserved in this repository; the record's
   `ARTIFACT CONSISTENCY` lines refer to them and cannot be re-run here (§5).
3. The four v0.7 corrections that changed the model — boundary forks representable, crash modelled as
   volatile/durable, conflict domains and preprocessing objects indexed, partition recovery through
   the transition relation — are present only in the Python checker and the v0.7 prose, not in the
   surviving TLA+ artifact (§4).
4. The epoch barrier has no refinement relation to the base consensus protocol, and the base
   protocol's state machine is not yet frozen (§8).
5. The `3,040,321,473` state-product figure is a paper argument, not a measurement, and is labelled
   as such wherever it is quoted (§7).
