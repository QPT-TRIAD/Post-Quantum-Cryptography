# How the ledger was constructed, and how its entries are shaped

## The problem, stated before any solution

The project's goal is a QPT-128 security argument for conflict-extractable post-quantum quorum
certificates. Such an argument has to name, for every step, either a theorem with a proof or an
explicit assumption. The hard part is not the arithmetic of any one step. It is that the argument
has many steps — extraction, contraction, sampler mass, good-key events, signature hardness, hash
behaviour, resource accounting — and a step without a source is a hole that is easy to leave
unnoticed, because a plausible-looking formula can be written down at any point.

The ledger approaches that problem from the wrong end on purpose. Instead of building the argument,
it takes a large body of named mathematics and asks, for each item, whether the item can be tied to
a specific obligation. The difficulty is that most named mathematics cannot. A general theorem about
a transform, an entropy, a derivative or an equilibrium is not a statement about the verifier's
challenge distribution, the extractor's database, or the adversary's resource vector. Deciding
"no route" for an item is therefore the common outcome, and the ledger's value lies mostly in the
negative verdicts and in the exact typed adapter each verdict demands before the verdict could be
reversed.

## What the ledger was built from

The ledger is version 1.33, dated 9 September 2026 (line 3). It was produced from two inputs, both
of which it names with a SHA-256 digest, and **both of which are absent from the source tree**:

| Input | Where named | Digest as recorded |
|---|---|---|
| `operators_1000(1).md` — the original 1,000-entry catalogue | Line 300 | `95e846198d956426a348d9f1bc8aa8692e36971b11340a1b3d6c28d446da1e95` |
| `continuation_v1.32/report.md` — the workspace baseline that supplied the extraction budget, the ternary comparison and the retry truncation | Lines 297, 302 | `ebdcd6e82374c3f8d5af98d58f11af524027e0a5b85cdedfa388e398ddddb4b8` |

Neither digest can be checked. The consequence is stated plainly in the ledger itself: the
extension of the commit-and-open analysis "does not establish that the current verifier satisfies
those hypotheses" (89), and "No new claim is made that all earlier attachments were independently
re-audited in this pass" (297). A reader must therefore treat the retention claim ("all 1,000
entries have been read and retained", line 7) as unverifiable from this repository: there is no
original to diff against.

The ledger is a single markdown file of 846,185 bytes and 19,608 lines. It embeds its own result and
its own checker, which makes it self-contained: the closing block is a machine-readable summary
(JSON, lines 19093–19251) and a 349-line Python script (lines 19259–19607) that regenerates it.

## The construction, step by step

Each step below carries the assumption it needs.

1. **Import the catalogue unchanged, under stable identifiers.** All 1,000 entries are carried as
   `<letter><1..50>` with an HTML anchor `op-<lowercase id>`. *Assumption:* the source catalogue is
   what the digest at line 300 says it is. Not checkable here.

2. **Demote every inherited claim to uncertified text.** Every entry keeps its original signature,
   definition, property and use, under the field name "Source property — not certified" and "Source
   use — context only". The rule is stated at line 304: "The original source property is preserved
   as historical, unverified text in every entry. No amendment means **not certified**, not 'true'."
   *Assumption:* none; this step is a labelling decision and is applied uniformly.

3. **Amend the claims that are wrong, mis-typed or under-hypothesised.** 116 entries receive an
   `Amendment (LABEL)` paragraph. *Assumption:* the amendment is correct. The ledger supplies no
   proof and no citation for any of them — see `validation-status.md`.

4. **Impose a disposition.** Every entry is either `ACTIVE INVESTIGATION` (182) or
   `PARKED — NO DIRECT ROUTE ESTABLISHED` (818), optionally with `; SPECIFIC AMENDMENT`,
   `; SOURCE SIGNATURE NEEDS COMPLETION` or `; HYBRID NAME IS NOT A COMPOSITION PROOF` appended.
   The semantics are given at line 304: parked "does not assert that the mathematics is useless",
   it asserts that no direct QPT-128 contribution was established.

5. **Route the active entries into 28 typed contracts.** The 182 active entries become members of
   `A01`–`A28`. Each investigation carries a mutated formula or interface, a contract-and-proof-scope
   paragraph, and four numbered questions. 112 questions in total. *Assumption:* membership is a
   proposed use, not an established one. The ledger says so: the mutated formula "is established
   only to the extent stated in the linked lemma; it is not evidence that a deployed protocol
   realizes the map" (331).

6. **Prove the small set of facts the contracts actually use.** Lemmas 1–8 (lines 66–270) are
   written out in full. Each is elementary and each is labelled as such: "elementary derivations for
   this amendment. They are not claims of new results in the mathematics literature. Any
   protocol-level application must discharge the stated premises" (68).

7. **Execute what can be executed.** 23 finite check groups over exact rational arithmetic and small
   exhaustive enumerations, run by the embedded checker. *Assumption:* none for the arithmetic; the
   groups are re-runnable, and this repository reproduces the recorded output byte for byte.

8. **State what is not done.** The closing JSON carries `"full_QPT128_established": false` and seven
   open premises. The header states the full claim remains OPEN (11).

## The entry schema

Every one of the 1,000 entries follows this order exactly. A parser over the file finds all ten
fields in every entry and no unparseable lines.

1. `<a id="op-xN"></a>` — the anchor.
2. `#### XN. \`symbol\` — name` — the identifier and the operator's symbol and name.
3. `**Disposition.**` — `ACTIVE INVESTIGATION` or `PARKED — NO DIRECT ROUTE ESTABLISHED`, with the
   optional qualifiers above. Occurs exactly 1,000 times.
4. `**Source signature.**` — the type signature as the catalogue gave it.
5. `**Source definition.**` — the definition as the catalogue gave it.
6. `**Source property — not certified.**` — the claim under review.
7. `**Source use — context only.**` — the application context the catalogue gave.
8. `**Amendment (LABEL).**` — optional; present in 116 entries. The correction text.
9. `**QPT-128 substitution.**` — for an active entry, "Use only through [Axx](#axx)[, …], with each
   contract and its four research questions."; for a parked entry, always the same sentence:
   "None established in this pass. Supply a finite typed adapter and an event/resource inequality
   before promoting this entry." (818 occurrences).
10. `**Eligibility question for XN.**` — for an active entry, verbatim one of the four questions of
    one of its own investigations plus the tail "Identify the exact role of this operator in that
    derivation."; for a parked entry, a family-generic question shared by the parked entries of that
    family.

A single active entry, abridged from L1 at lines 796–815:

```
**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.
**Source signature.** L × L × [0,1] → L
**Source property — not certified.** Idempotent and θ-monotone: increasing θ shrinks the result.
**Amendment (FALSE_AS_STATED).** Do not assert idempotence on all inputs. … For example,
  x=1/4, nu(z)=z and theta=1/2 give bottom, not x.
**QPT-128 substitution.** Use only through [A01](#a01), with each contract and its four research questions.
**Eligibility question for L1.** Which exact event is being bounded, and are Q, h, leaf count and
  verifier calls from that same experiment? Identify the exact role of this operator in that derivation.
```

## Disposition and amendment vocabulary

**Dispositions** partition the file: 182 active / 818 parked. Of the 182 active, 35 also carry an
amendment; of the 818 parked, 81 do. 50 entries in family Z carry the hybrid flag and 130 entries
across the file carry the incomplete-signature flag.

**Amendment labels**, with whole-file counts. The ledger does not publish a label histogram — its
provenance table gives per-family active and amended counts, not labels. The histogram below was
produced by a parser over the 116 `**Amendment (LABEL).**` fields, and agrees with the prior
reading record's independent parse:

| Label | Count | Label | Count |
|---|---:|---|---:|
| `DOMAIN_GAP` | 34 | `FORMULA_GAP` | 4 |
| `FALSE_AS_STATED` | 24 | `NORMALIZATION` | 3 |
| `TYPE_GAP` | 14 | `PRECISION` | 2 |
| `FORMULA_ERROR` | 9 | `REDUNDANT_OR_UNDEFINED` | 1 |
| `DIRECTION_ERROR` | 7 | `DIMENSION_ERROR` | 1 |
| `DEFINITION_MISMATCH` | 6 | `VARIANCE_ERROR` | 1 |
| `SIGN_ERROR` | 5 | `UNSUPPORTED_INFERENCE` | 1 |
| | | `COMPLEXITY_GAP` | 1 |
| | | `TOPOLOGY_GAP` | 1 |
| | | `UNSUPPORTED_SECURITY` | 1 |
| | | `UNDEFINED_COMPOSITION` | 1 |

The vocabulary is not defined anywhere in the ledger. What each label denotes has to be inferred
from the amendment it is attached to. Reading the 116 texts, the labels divide into four kinds:
a **domain gap** (the statement is true only under a hypothesis the source did not state, e.g. H7's
barcode decomposition needs pointwise finite-dimensional one-parameter modules over a field); a
**type gap** (the signature mixes two different kinds of object, e.g. C45's `C^{m×n}` over a PID);
a **false as stated** (the statement is simply wrong, e.g. R36's claim that Schmidt rank cannot
increase under LOCC — it can decrease, by local reset); and a **formula or sign error** (e.g. R18's
`ΔF ≤ 0` for nonincreasing free energy, where `ΔF = F(initial) − F(final)` gives `ΔF ≥ 0`).

**Per-family amended counts**: L 16, T 8, F 7, Q 8, D 7, I 8, P 8, S 7, M 7, C 6 (first half, 82
in total); H 3, K 3, N 2, X 3, G 0, R 9, O 5, W 2, Y 5, Z 2 (second half, 34 in total). `82 + 34 =
116`, which is the ledger's own header count. The prior reading record gives the second half as 37
by counting the 3 amendments in C36–C50 a second time; that decomposition double-counts and should
not be used.

## Counts, and how each one was checked

Every count below was reproduced by a parser over the 1,000 `####` entries and their fields, and by
`grep` for the specific tokens. The third column says what the check consisted of.

| Count | Value | How it was checked |
|---|---:|---|
| Catalogue entries | 1,000 | `grep -c '^#### '`; 50 per family heading |
| Markdown headings | 1,070 | 1 level-1, 9 level-2, 60 level-3, 1,000 level-4. `grep -c '^#'` returns 1,071 because it also counts the checker's `#!/usr/bin/env python3` shebang line. |
| Dispositions | 182 active / 818 parked | parser over the `**Disposition.**` field; sums to 1,000 |
| Amendments | 116 | parser over `**Amendment (`; every one sits in an entry whose disposition carries `SPECIFIC AMENDMENT` (116 of 116) |
| Investigations | 28 | headings `A01`–`A28` |
| Questions | 112 | four per investigation |
| Operators inside investigations | 182 | the union of the 28 "Original operators" lists equals the 182 active entries exactly, with 206 memberships in total |
| Route links | 206 | every active entry's "Use only through" list equals the set of investigations that list it; no mismatch in either direction |
| Incomplete signatures | 130 | parser over `SOURCE SIGNATURE NEEDS COMPLETION` |
| Hybrid flags | 50 | parser over `HYBRID`; all 50 in family Z |
| Internal anchors | 1,028 | 1,000 `op-…` plus 28 `aNN` |
| Executed check groups | 23 | the checker's own summary line, reproduced by re-running it |

The ledger's own header counts (line 7) — 1,000 retained, 116 corrections, 28 mutations, 112
questions, 182 operators, 818 parked — are all reproduced exactly. That is a check on internal
consistency, not on truth: the numbers describe review coverage, as the ledger says.

## Three construction choices worth naming

**The catalogue is not split.** One could imagine rewriting the file into a family per document.
That would be a rewrite of the record, and this repository does not do it. The catalogue document
is copied whole and byte-identical, and the per-family index in the README and in
`catalog-families.md` exists so that a reader can navigate it without the file having to be cut up.

**The checker is extracted, not rewritten.** It is reproduced from the document's closing block by
a recorded `sed` command, so that the extraction itself can be confirmed. The extraction is
byte-identical to the block and hashes to the digest recorded in `VERIFICATION.md`.

**Nothing is filled in.** The absent predecessor documents are named and marked absent. The
uncited constants are quoted as the ledger gives them, with their later divergent values noted as
divergences rather than silently replaced.
