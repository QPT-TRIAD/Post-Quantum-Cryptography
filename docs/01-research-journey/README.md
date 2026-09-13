# 01 — Research journey

This package is the chronological record of the research that produced the CE-QS construction and the
QPT-128 security target: what was attempted, in what order, what each attempt returned, what was
concluded, what was refuted, and what was abandoned. It exists because the result is not intelligible
without the route — several of the programme's definitions were rewritten in response to refutations,
and two of the constructions it is measured against were withdrawn rather than repaired.

It is a **record, not an argument**. Nothing here is a proof of anything, and nothing here restates a
result that another package owns. The construction is in `docs/03-construction`, the target and the
games are in `docs/04-security-and-validation` and `domains/06-qpt128-security-target`, and the theory
behind each step is catalogued in `docs/02-theory-and-references`.

## The rule that governs this package

**These documents are the record of what was said at the time, and a later correction never goes back
into them.** If a number here is refuted, the refutation is written in place — as a dated note saying
what failed to reproduce and what was observed instead — and the correction itself is recorded in
`records/verification-findings.md` and in the domain that owns the claim. The trail is not edited to
agree with a later finding, and a later finding is not presented as though the original document had
always said it.

A reader who wants the standing value of any number on this trail should read it here for what was
claimed and in `records/` for what still holds.

## What is in this directory

| Path | What it is |
|---|---|
| `chronology.md` | The sequence of the work phase by phase, with the per-version table of the CE-QS size campaign, the version-to-artefact inventory, and the register of every reversal the trail records. |
| `decisions.md` | The decisions that shaped the result: the question, the options, what was chosen, the stated reason, the theory or measurement the choice rested on, and whether it still stands. |
| `dead-ends.md` | The lines that were abandoned and why, in the detail needed to avoid repeating them: what was tried, what it cost, and the observation that killed it. |
| `theories-used.md` | The deduction chain: for each conclusion on the trail, the theories invoked, and — the point of the document — whether the whole theory applied or only a part, which part was borrowed, and why the remainder did not transfer. |
| `pqt.md` | The master security report for the hidden-signer construction, placed here unedited as the record of the target as it stood before it was refuted. See "How to read `pqt.md`" below. |
| `VERIFICATION.md` | The required table: what was checked while assembling this package, with commands, digests and observed results. |

## How to read `pqt.md`

`pqt.md` is the "CE-QS — Total QPT-128 Security Proof and Validation Report": the consolidated
statement of the construction, its assumption set, its eleven-term error ledger, its conditional
theorem and its own status verdict, written at the moment before the security target was redefined.

- Lines 1–1560 are the report proper. Read it as the target *as it then stood*: its closing theorem
  asserts that every QPT adversary satisfies an advantage below `2^-128`, and that target was
  **refuted downstream**. The refutation, the definitions that replaced it, and the verdict on the
  ledger's rows are in `domains/06-qpt128-security-target/` and `records/failed-assumptions.md`
  entry `Q1`. The document is not annotated in place; it is the historical artefact.
- Lines 1562–2188 are an out-of-order partial paste of the second trail export, not part of the
  report. They repeat material already carried at that export and skip the intermediate versions.
  A reader who wants the version-by-version record should use `chronology.md` instead.
- The final-statement box at lines 1508–1518 is malformed in the source: the display math opened at
  line 1511 with `\[` is closed at line 1513 by `$$`, and line 1518 carries a stray `]` where the
  `\boxed{` group ends. It is left exactly as found, so that the artefact is the artefact; the
  statement it intends to make is quoted in full in `chronology.md` §VIII.

## The two texts this package is written from, and why they are not here

The trail exists as two exported working transcripts, referred to throughout this package by the
shorthand **PS** and **PS2** (see the pointer table below). They are 6,224 and 3,342 lines of
request-and-response text containing role labels, tracking parameters, interface residue and pasted
third-party material. **They are not migrated into this repository.** The dossier that reads them
instructs that the narrative be rebuilt from them rather than copied, and the file map marks both
`source-only`.

Two consequences a reader should know:

1. **A pointer such as `PS:115` cannot be opened here.** It identifies a line in a text that was read
   in full during the build of this repository and deliberately not copied. The pointer is kept
   because it is the only traceable location for the claim, and dropping it would leave the claim
   unsourced.
2. **The scrubbed narrative is this package.** `chronology.md`, `decisions.md`, `dead-ends.md` and
   `theories-used.md` are newly written from those transcripts, not extracted from them. Nothing in
   them is a paste.

A third text, `test.md` (**TM**), is a devnet test plan belonging to a separate ledger repository. It
is out of scope and is not copied; the only facts taken from it here are the summary of this
programme's own test results, and those are routed to `docs/05-devnet-evidence`.

## Pointers, labels and citation status

**Pointers.** `PS:<line>` and `PS2:<line>` are lines of the first and second trail exports as named
above; `PQT:<line>` is a line of `pqt.md`, which *is* in this directory; `TM:<line>` is a line of the
devnet test plan. Version numbers in the form `v1.42` are the project's own document versions; the
version-to-artefact inventory in `chronology.md` says which of them survive as files in the
repository and which exist only as transcript prose.

**Claim labels.** Defined once for the repository in `docs/00-start-here/claim-labels.md`. The shorthand
used here is `[T]` theorem-with-proof, `[R]` reduction-sketch, `[L]` model-or-ledger estimate,
`[M]` measurement, `[S]` simulation, `[A]` assumption, `[C]` conjecture. A label is never upgraded:
a measurement on this trail never becomes a proof, and a conditional theorem is always reported with
its premise.

**Citation status.** Where a statement is about someone else's paper or standard, it is marked as an
external-literature report and is given as the trail gives it. The trail's citations are frequently
incomplete — several rest on a site root rather than a paper — and this package says so rather than
filling the reference in.

## How to read this package in order

1. `chronology.md` — read the phases in order. Phase I produces the target, Phase II–IV build and
   repair the accountable-quorum proof, Phase V pivots to the sidecar-free target, Phase VI is the
   collision with the size budget, Phase VII–VIII build and then overstate the security target, and
   Phase IX records what happened to those conclusions afterwards.
2. `dead-ends.md` — after the chronology, so that each abandoned line is recognised as something the
   record actually tried.
3. `decisions.md` — the choices that survived, with the reason each was made and its standing today.
4. `theories-used.md` — the same material organised by theory instead of by time, for a reader who
   wants to know which published result carries which step and how much of it was used.
5. `records/failed-assumptions.md` and `records/verification-findings.md` — before relying on any
   number on this trail.

## What this package proves and what it does not

**It does not prove anything.** It records what was attempted and what was concluded, and it labels
each conclusion with the claim label the source gave it. The accountability claim, the gate
work-factor target, the size limits and every measured figure have their own packages.

**It records the refutations as first-class results.** The trail contains more refuted hypotheses
than surviving ones, and the refutations are the reason the target is stated the way it is. A
chronology that stopped where the evidence was strongest would be a different and false document.

**It does not resolve the trail's open questions.** Where the record ends with an obligation
unmet — no accepted full quorum certificate, no compact publicly verifiable proof binding the
authorizations to their handles inside the reserved slot, no concrete DKG theorem, no quantum
random-oracle theorem for the fast adapter, no machine-checked proof of any statement — this package
says so and routes to the domain that owns it.

**It carries two reversals that belong to other packages**, because they are the fate of claims made
on this trail: the withdrawal of the hash-signature property-layer count, and the measurement showing
the operator-ledger amendment figures were not supported. Both are recorded in `chronology.md` §IX
with their owning domain, and neither is presented as a finding of this package.

## Where to go next

| If you want … | Go to |
|---|---|
| the construction and the wire format | `docs/03-construction/` |
| the security target, the games and the attack lab | `docs/04-security-and-validation/`, `domains/06-qpt128-security-target/`, `domains/09-security-games-and-attack-lab/` |
| the theory behind any step here | `docs/02-theory-and-references/` |
| the certificate sizes and the 32 KiB gate | `domains/07-compact-certificate-b0/` |
| the hidden-signer work that the trail's open item `R6` became | `domains/08-hidden-signers/` |
| what still holds and what was withdrawn | `records/` |
