# 01 — Accountable quorum foundations

The first domain of the programme, and the one that fixes the vocabulary the later domains use. It
defines what a quorum is, what it means to blame a seat, and what can and cannot be extracted from
two conflicting quorum certificates — and it states, once and exactly, the counting fact that makes
accountability possible at all.

## The founding problem

A quorum certificate proves that a quorum approved a statement. A *compact* quorum certificate —
the kind a post-quantum system wants, because concatenating individual signatures grows the
certificate in proportion to the number of signers — proves that a quorum approved a statement
**without naming anyone in it**. That is the whole difficulty, and it is a trade rather than an
oversight:

- keeping the individual signatures makes the certificate linear in the signer count, which is the
  cost the design exists to remove;
- replacing them with one aggregate or threshold signature removes the cost and the attribution
  together.

Two compact certificates on two conflicting statements therefore prove that *someone* misbehaved,
while leaving no way to punish anyone for it: the certificate that shows the crime also hides the
criminal. A system built this way can detect equivocation and do nothing about it. Restoring
accountability is the programme's problem, and this domain is where its terms of reference are set.

The source splits the response into two targets and refuses to conflate them:

- **Target A** — the deployable system: a compact threshold signature on the consensus hot path, an
  external accountability sidecar of individually attributable evidence, and cryptographic binding
  between the two. Everything in this domain except the frontier memo belongs to Target A.
- **Target B** — the frontier: a compact quorum signature from which a conflicting signer can be
  extracted directly from two conflicting certificates, with no O(n) sidecar to retrieve. Its status
  in the record is *open*.

## The definitions this programme fixes at the start

These are stated formally, with the assumption each needs, in
[`docs/definitions-and-conflict-extraction.md`](docs/definitions-and-conflict-extraction.md):

- **Committee and seat.** `n = 3f + 1` validators (`n ≤ 64` at the first implementation target),
  voting is equal-seat rather than stake-weighted, and corruption is static within an epoch with
  `c ≤ f`.
- **Quorum.** `q = 2f + 1` signers, written `T = 2f + 1` where it is the threshold of the signing
  scheme. At the reference committee of 64 seats the quorum is 43.
- **Quorum intersection.** Any two quorums intersect in at least `2q − N` seats — the single counting
  fact this repository states in one place, in the general form. At the reference committee
  `2·43 − 64 = 22`.
- **The 22 double-authorizers requirement.** A conflict between two quorum certificates at the
  reference committee therefore requires **at least 22 seats to have authorized both statements** —
  22 double-authorizers — while at most `f = 21` seats are Byzantine. At least one of the 22 is
  honest. That is the domain's core requirement: a conflict cannot occur without an honest seat
  having signed twice, unless the signature primitive itself failed. The source states the same step
  in its `f + 1` form, and the 22 is arithmetic on the source's two constants.
- **Conflict domain.** The unit over which a signer must not equivocate,
  `d = (epoch, height, view, phase)`, with a durable vote log and persist-before-send ordering.
- **Blame.** Silence is never blame evidence; a share is blamable only through its authenticated
  envelope. Individually attributable evidence is a signed accountability receipt, carried in a
  sidecar committed by a Merkle root, with anchoring conditioned on the voter holding the evidence.

## What the epoch-barrier model is for

An epoch change in this design is not an administrative event but a safety boundary: an epoch is
crossed only after a terminal block reaches ordinary finality, a seal certificate is formed over the
finalized boundary, and the complete next public configuration is embedded in that boundary rather
than referenced by hash. The barrier is what prevents two parts of the system from finalizing
different boundaries around the change.

[`formal/epoch-barrier.tla`](formal/epoch-barrier.tla) with [`formal/epoch-barrier.cfg`](formal/epoch-barrier.cfg)
is the **specification** of that mechanism — the v0.6 revision, the only revision preserved here. It
is a specification document, not a verification result: it has never been executed by TLC or TLAPS,
and no model checker was run for this repository. [`docs/epoch-barrier-specification.md`](docs/epoch-barrier-specification.md)
explains, invariant by invariant, what the model is intended to capture, what it does not represent
(no adversary, no network, crash as a stutter, boundary uniqueness assumed rather than derived), what
the recorded outputs say, and what would be needed before a model-check could mean anything.

## What these documents establish, and what they merely specify

Established by proof in the source, and restated here: the quorum-intersection counting fact, and the
honest-support intersection `|H_0 ∩ H_1| ≥ f + 1 − c ≥ 1` that follows from it once the threshold
support assumption is granted. Both are elementary counting; the second is only as strong as the
primitive assumption it consumes.

Specified or sketched rather than proved: the evidence-framing bound, the boundary-uniqueness bound
and the end-to-end extraction argument. These are reduction sketches — the source states the
inequality and the shape of the reduction, and does not write the reduction out. They are labelled as
such at each claim.

Executed, but only as bounded state exploration: the two finite-state checkers in
[`src/`](src/) and [`history/`](history/). Both were re-run for this repository and reproduced the
shipped results exactly. They are not TLC, not a cryptographic proof, and each model's claim is as
narrow as the abstraction it explores.

Open, and stated as open: Target B (compact conflict extraction without a sidecar); the practical
frontier memo's candidate direction, which was later dropped; TLC and TLAPS for any revision of the
epoch-barrier model; and refinement of the model to the base consensus protocol, which cannot be
written until that protocol's state machine is frozen.

## How to read this domain, in order

1. [`docs/definitions-and-conflict-extraction.md`](docs/definitions-and-conflict-extraction.md) —
   start here. Definitions, the counting fact, the extraction argument end to end, the assumption
   inventory, and the open items.
2. [`docs/epoch-barrier-specification.md`](docs/epoch-barrier-specification.md) — the barrier model
   as a specification, its nine configured invariants, what the recorded model-check output does and
   does not say.
3. [`docs/research-proof-documentation.md`](docs/research-proof-documentation.md) — the current
   Target-A research record (v0.7), in full. Long; the two documents above are its map. Its earlier
   revisions are kept in [`history/`](history/) as `domains/01-accountable-quorum-foundations/history/research-proof-documentation-v0.5.md` and
   `-v0.6.md`.
4. [`docs/frontier-conflict-extraction.md`](docs/frontier-conflict-extraction.md) — the v0.1 Target-B
   design memo. It is a design-space survey, explicitly "not a construction, not a proof, not a claim
   of priority", and it is superseded by the later frontier work in the construction-evolution
   domain.
5. [`formal/`](formal/) — the epoch-barrier specification and its TLC configuration.
6. [`src/`](src/) and [`results/`](results/) — the current finite-state checker and its recorded
   output.
7. [`VERIFICATION.md`](VERIFICATION.md) — what was re-run in this repository, on what, with what
   observed output, and what was not run and why.

## Provenance and conventions

- **Current revisions carry no version suffix**; superseded revisions keep it and live in
  [`history/`](history/): the v0.5 and v0.6 research records, the v0.6 checker
  (`history/pqaqc_finite_state_check-v0.6.py`) and the v0.6 recorded output
  (`history/pqaqc_modelcheck-v0.6.txt`).
- **Executable files and recorded outputs are byte-identical** to their sources:
  `src/pqaqc_finite_state_check.py`, `history/pqaqc_finite_state_check-v0.6.py`,
  `results/pqaqc_modelcheck.txt` and `history/pqaqc_modelcheck-v0.6.txt`.
- **Copied text documents carry a trailing "Repository note"** recording provenance, what is
  superseded, and — where a revision not preserved here is referenced — that the referenced file is
  absent. No other editorial change has been made to their body text, except for three placement
  rewrites in the current record and three in its v0.6 predecessor, which remove third-party
  environment references; two repairs of corrupted LaTeX control bytes; and two marks on artifact-list
  entries naming files not preserved here. Every one of those edits is listed, with its line, in
  [`VERIFICATION.md`](VERIFICATION.md).
- **One deliberate deviation from the file map**: `formal/epoch-barrier.tla` was renamed internally
  to `MODULE epoch_barrier`, because a TLA+ identifier cannot contain a hyphen and the map's
  hyphenated file name therefore cannot equal any valid module name. The mismatch, and what a TLC run
  must do about it, is recorded both in the file's repository note and in
  [`docs/epoch-barrier-specification.md`](docs/epoch-barrier-specification.md) §1.
- **Not preserved here.** The v0.7 TLA+ module and configuration, and the v0.8 research record named
  in the frontier memo, are referenced by the shipped text but are not part of this repository.

## Discrepancies

None outstanding. The re-run comparisons agree with every shipped result file; the only items not
reproducible here are the TLA+ model-check items, which were never run and are marked `not-run` with
the reason in [`VERIFICATION.md`](VERIFICATION.md). Two recorded claims that no longer have an
artifact behind them — the v0.7 "artifact consistency" lines and the v0.7 TLA+ module itself — are
flagged as such in [`docs/epoch-barrier-specification.md`](docs/epoch-barrier-specification.md) §5
rather than repeated as verified.
