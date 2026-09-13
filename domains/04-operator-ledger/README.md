# D4 — operator-ledger

The 1,000-operator ledger: who signs what, and what it costs.

## What this domain is

The project needs a concrete QPT-128 security argument for conflict-extractable post-quantum
quorum certificates. This domain holds a side investigation that was run against that goal. A
user-supplied catalogue of 1,000 named mathematical "operators" — threshold meets, min-plus
products, Caputo derivatives, Shannon entropy, Shapley values, Smith normal forms and 994 others —
was screened against one question: can any of them discharge a real proof obligation?

The ledger is the adversarial answer. It retains all 1,000 entries under stable identifiers, marks
every inherited "source property" as uncertified, corrects 116 of them, parks 818 as having no
established route, and merges the 182 entries with a conceivable use into 28 typed "mutation"
contracts `A01`–`A28` with 112 focused research questions. Eight elementary lemmas that those
contracts rely on are proved in full in the text. A 349-line Python checker executes 23 finite
groups over the arithmetic. The ledger then states that the complete deployed QPT-128 claim remains
**OPEN** (line 11) and that the counts "describe review coverage, not 1,000 certified mathematical
theorems" (line 7).

The ledger does not build the protocol. Its own closing JSON carries
`"full_QPT128_established": false` and seven named open premises.

## Files

| Path | What it is |
|---|---|
| `docs/operator-ledger.md` | The catalogue document itself, v1.33, copied byte-identical from the source tree. 846,185 bytes, 19,608 lines, SHA-256 `225fd1acf3389d2cd7ffb064ba0e37afc67e290b3d163540360fb72d084dc98a`. This is the record; it is not split or summarised anywhere in this repository. |
| `src/operator_ledger_checks.py` | The checker extracted from the document's closing block, lines 19259–19607. 349 lines, SHA-256 `6b7d8b71da21e57bf70b219707f5393dc004e88f0276da7dcc876c58eac22ecc`. |
| `results/operator_ledger_checks.json` | The recorded output block, lines 19093–19251 of the document, extracted byte-identical. SHA-256 `ccf30e1760cf4b945f3e08ba1c1ccceec94b81767cd40b4fefd0a3ea5bc46610`. |
| `docs/construction-and-schema.md` | How the ledger was constructed, the entry schema, the disposition and amendment vocabulary, and the counts. |
| `docs/catalog-families.md` | What each of the 20 families of 50 entries does, and how many of its entries are active, amended or parked. |
| `docs/theory-borrowed.md` | The eight formal sources `[S1]`–`[S8]`, the eight lemmas, the quorum-intersection count: which part of each is used and which part is not. |
| `docs/checker-and-what-it-verifies.md` | What the checker is, how to run it, what each of its 23 groups asserts, and where the code asserts less than its scope string claims. |
| `docs/validation-status.md` | What is proved, what is computed, what is assumed, and what an amendment without an executable witness means for the strength of the claim it supports. |
| `VERIFICATION.md` | The reproduction table: the checker re-run against the recorded block, with the exact commands and the observed output. |

There is no `history/` directory in this domain. v1.33 is the only revision of the ledger, and the
three predecessor documents it names are absent from the source tree (see below).

## How to read it in order

1. `docs/operator-ledger.md`, lines 5–22 — the header. What the amendment claims about itself.
2. `docs/operator-ledger.md`, lines 24–65 — the target and the variable map. Every symbol used
   later is defined here once.
3. `docs/operator-ledger.md`, lines 66–270 — Lemmas 1–8, with their proofs. This is the only part
   of the document that is a written mathematical argument.
4. `docs/theory-borrowed.md` — which external theorem each lemma borrows, and which part of it.
5. `docs/operator-ledger.md`, lines 329–783 — `A01`–`A28`. Skip on a first read; return when the
   question is what the ledger wanted to do with a family.
6. `docs/catalog-families.md` beside `docs/operator-ledger.md`, lines 784–19059 — the catalogue.
   The family table in the second document is the index to the first.
7. `docs/operator-ledger.md`, lines 19060–19608 — the executed checks, the recorded JSON, the
   checker. Then run the checker yourself: `docs/checker-and-what-it-verifies.md`.
8. `docs/validation-status.md`, then `VERIFICATION.md`.

## Navigation index

The document is 846 KB across 19,608 lines with 1,070 markdown headings: 9 level-2 sections, 60
level-3 subsections and 1,000 level-4 catalogue entries. The index below gives the level-2 and
level-3 headings with their line ranges, which is enough to reach any part of the file. Line ranges
run to the line before the next heading of the same or a higher level.

### Top-level sections

| Lines | Section |
|---|---|
| 1–4 | Title and version (v1.33, 9 September 2026) |
| 5–23 | What this amendment establishes — counts, the 9/16 result, the OPEN status, how to use the document |
| 24–65 | Target, variables and proof obligations — the target convention, the symbol map (35–52), the gap table (56–64) |
| 66–270 | Partial proofs and substitutions — Lemmas 1–8 |
| 271–283 | Priority investigation sequence — six priorities with stop/go criteria |
| 284–298 | Primary sources used for the cryptographic interfaces — `[S1]`–`[S8]` and the workspace baseline |
| 299–328 | Review provenance and coverage — input digests and the per-family count table |
| 329–783 | Mutated operators and focused research questions — the `A01`–`A28` summary table (333–362) and one section per investigation (364–783) |
| 784–19059 | Complete amended catalog — 20 families of 50 entries |
| 19060–19089 | Executed adversarial checks — the 23-row result table |
| 19090–19253 | Complete machine-readable results — the recorded JSON (fenced 19092–19252) |
| 19254–19608 | Standalone reproduction code — the checker (fenced 19258–19608; code 19259–19607) |

### Lemmas and investigations

| Lines | Section |
|---|---|
| 15–23 | How to use this document |
| 54–65 | Smallest concrete results that would close the main gaps |
| 70–90 | Lemma 1: budget inversion and event composition |
| 91–133 | Lemma 2: adaptive failure contraction |
| 134–178 | Lemma 3: robust contraction and a 128-bit component calculation |
| 179–207 | Lemma 4: exact maximal mass for base-b product boxes |
| 208–228 | Lemma 5: compatible good events and finite retry tails |
| 229–248 | Lemma 6: finite-field rank counting and entropy discipline |
| 249–256 | Lemma 7: resource composition and the limited MAXDEPTH interpretation |
| 257–270 | Lemma 8: reject quantifier and idealization substitutions |
| 366–380 | A01: Invert a valid error budget |
| 381–395 | A02: Compose failure events without independence |
| 396–410 | A03: Keep the worst-case quantifiers |
| 411–425 | A04: Count serial work and parallel depth separately |
| 426–440 | A05: Give the shrink recurrence a measurable meaning |
| 441–455 | A06: Certify quantum contraction by a matrix inequality |
| 456–470 | A07: Allow certified imperfections in the shrink factor |
| 471–485 | A08: Handle dependent repetitions |
| 486–500 | A09: Reject spectral shortcuts |
| 501–515 | A10: Treat measurement and copying as explicit operations |
| 516–530 | A11: Count the actual challenge distribution |
| 531–545 | A12: Make a sampler change a protocol change |
| 546–560 | A13: Bound rejection and finite runtime |
| 561–575 | A14: Use guessing entropy and forbid free entropy creation |
| 576–590 | A15: Use finite-field rank for the actual distribution |
| 591–605 | A16: Glue good-key events without inventing independence |
| 606–620 | A17: Turn a security label into a reduction contract |
| 621–635 | A18: Construct the actual joint decoder interface |
| 636–650 | A19: Separate a reduction extractor from public conflict extraction |
| 651–665 | A20: Make the fixed-hash bridge property-specific |
| 666–680 | A21: Track hash width separately from sponge capacity |
| 681–695 | A22: Account for proof-reduction resource inflation |
| 696–710 | A23: Make finite checks proof aids with explicit scope |
| 711–725 | A24: Keep distributed authorization in the witness relation |
| 726–740 | A25: Use randomness extraction only where its seed premise holds |
| 741–755 | A26: Replace random-looking tests with finite guarantees |
| 756–770 | A27: Do not turn smoothing into a security assumption |
| 771–783 | A28: Replace the master operator by a compatibility record |

### The 20 catalogue families

Each family holds 50 entries, identified `<letter><1..50>` and anchored `op-<lowercase id>`.

| Lines | Family | Active | Amended | Parked |
|---|---|---:|---:|---:|
| 788–1721 | L — Lattice and order | 17 | 16 | 33 |
| 1722–2639 | T — Tropical and idempotent algebra | 8 | 8 | 42 |
| 2640–3555 | F — Fractional calculus | 5 | 7 | 45 |
| 3556–4473 | Q — q-deformed operators | 6 | 8 | 44 |
| 4474–5389 | D — Discrete difference calculus | 6 | 7 | 44 |
| 5390–6307 | I — Information theory | 18 | 8 | 32 |
| 6308–7225 | P — Paths and loops | 3 | 8 | 47 |
| 7226–8141 | S — Spectral operators | 18 | 7 | 32 |
| 8142–9057 | M — Probability and measure | 18 | 7 | 32 |
| 9058–9971 | C — Combinatorics and generating functions | 11 | 6 | 39 |
| 9972–10879 | H — Topology and homology | 1 | 3 | 49 |
| 10880–11787 | K — Category theory | 11 | 3 | 39 |
| 11788–12693 | N — Noncommutative algebra | 1 | 2 | 49 |
| 12694–13601 | X — Stochastic calculus | 2 | 3 | 48 |
| 13602–14503 | G — Geometry and Lie/Clifford operators | 1 | 0 | 49 |
| 14504–15423 | R — Quantum resource theory | 12 | 9 | 38 |
| 15424–16335 | O — Logic and verification | 21 | 5 | 29 |
| 16336–17241 | W — Multiscale transforms | 10 | 2 | 40 |
| 17242–18153 | Y — Games and decisions | 8 | 5 | 42 |
| 18154–19059 | Z — Hybrid constructions | 5 | 2 | 45 |

Active and amended columns are the ledger's own provenance table (lines 306–327); the active
column is reproduced exactly by the entries' own `QPT-128 substitution` links. "Amended" counts
entries carrying an `Amendment (LABEL)` paragraph. Active and parked partition each family's 50
entries, so the parked column is `50 − active`; amended overlaps both. Across the whole file: 182
active, 818 parked, 116 amended, of which 35 are both active and amended and 81 are both parked and
amended.

## What the ledger establishes, and what it only asserts

**Established, in the sense that a reader can check it by re-running or by reading a proof in the
text:**

- Eight elementary lemmas with written proofs (lines 66–270). They are labelled by the document
  itself as "elementary derivations for this amendment. They are not claims of new results in the
  mathematics literature" (line 68). Every protocol-level application of them is conditional on a
  premise the ledger states and does not discharge.
- The exact minimum-round table 73/137/193/265 at `s = 32/64/92/128` and the robust 9/16 variant
  88/165/233/320, computed in exact rational arithmetic. Re-running the checker reproduces these.
- The base-b product-box mass formula and its small-instance brute-force agreement (490 prefix
  counts and 156 box instances).
- The retry-truncation boundary `R = 519` at `q_S = 2^64`, `p = 759/1024`, target `2^-160`;
  `R = 518` does not suffice.
- The quorum-intersection set count `|S0 ∩ S1| ≥ |S0| + |S1| − N`, exhaustively checked on 441
  pairs at `N = 7`, `t = 5`.
- The negative results: threshold meet is not idempotent; normalized majorization envelopes are not
  majorization join and meet; spectral radius is not a norm bound; a fixed hash is distinguishable
  from an independent random oracle with gap `1 − 2^-h`; a reduction's shared compressed-oracle
  database is not a public input; and name-based analogy (a rough-path signature is not an
  authentication signature) is rejected.

**Only asserted:**

- Every one of the 1,000 inherited "source property" fields. The document marks them
  "not certified" by design and states that "No amendment means not certified, not 'true'" (304).
  884 of the 1,000 entries carry no amendment at all, including 418 of the first half's 500.
- The 116 amendments themselves, except where the checker exercises them — see the measured count
  below. An amendment is an editorial correction written in prose. Nothing in the document proves
  it beyond the sentence that states it.
- The inherited extraction expression `J = ((72+40ℓ)Q³ + 2v)/2^h + 20Q²p_*` (lines 74–76). The
  document attributes it to a workspace report that is absent from the tree and gives no theorem
  number; it later diverged, without being flagged: a later project file derives `(20ℓ+60)Q³`, and
  a still later one records the published commit-and-open bound as `(22ℓ+60)q³`. The round tables
  are unchanged under all three.
- The seven open premises listed in the recorded JSON: the joint decoder, a public conflict
  extractor without the reduction's sidecar data, the `p_*` bridge, concrete signature hardness at
  the reduction's resources, the compatible good-key event and algorithm adapter, deployed-hash
  game properties, and concrete gate/depth/memory accounting.

## Amendment witnesses: the count actually measured

The ledger contains **116** `Amendment (LABEL)` paragraphs, one per amended entry; a parser over
all 1,000 entries reproduces the label histogram the document's own table gives. The prior reading
record claims that **113 of the 116 amendments have no executable witness and no citation**. That
figure is **not reproduced**.

Measured directly against the document:

- **Amendments with an executable witness: 15 of 116.** They are the entries `L1`, `L9`, `L10`,
  `L35`, `L47`, `T7`, `T8`, `T42`, `Q40`, `D9`, `I21`, `I33`, `H20`, `R36`, `Y1` — exactly the
  entries named by a group in the checker's own 23-row results table. Of these, five (`T7`, `T42`,
  `D9`, `I21`, `I33`) are witnessed only by a hard-coded or vacuous comparison; on the stricter
  reading that the assertion must compute rather than restate the corrected value, **10** amendments
  have an executable witness.
- **Amendments carrying a literature citation: 0 of 116.** No amendment text contains a source tag,
  a URL, an arXiv identifier, a FIPS or RFC number, or any other locator. The document's eight
  formal sources `[S1]`–`[S8]` are cited only in the lemma and investigation sections (lines 89,
  130, 247, 255, 267, 507, 567, 612, 627, 657, 672, 732), never in a catalogue amendment.
- **Therefore amendments with neither an executable witness nor a citation: 101 of 116** (106 if
  the five hard-coded or vacuous groups are discounted).

The claimed 113 would require only 3 amendments in the whole file to have an executable witness.
Three is the correct count for the *second half* of the document alone (`H20`, `R36`, `Y1`), which
is where the claim's own qualifying clause puts it. The figure appears to be that half-count
extrapolated to the whole file; it is stated in the prior reading record but not in the ledger, and
it is inconsistent with the same record's classification of the first half, which lists nine
amendments there as having executed checker evidence. The ledger's own header is more careful than
either: "They do not test all 116 editorial amendments" (line 19062). The full working is in
`docs/validation-status.md`; the reproduction is in `VERIFICATION.md`.

This matters for what the ledger is worth. An amendment with no executable witness and no citation
is an editorial opinion about a mathematical statement. It may be correct, and spot-checking
suggests most of the sampled ones are. But its only support is the sentence that asserts it, and
the ledger's own validation rule (A23, lines 696–710) is that arithmetic tests, finite-model
proofs, literature theorems and unproved protocol assumptions must be kept as separate statuses.
By that rule the 101 amendments are a fourth status the document does not name: unproved,
uncited, unchecked editorial corrections.

A second count in the same reading record is also wrong: it gives the two halves as "82 in the D4a
range, 37 in the D4b range, 11 elsewhere" out of "130 amendments". The ledger has 116 amendments,
and by its own half boundary at `C35`/`C36` the split is 79 + 37. The 82 is the whole-family sum for
families `L`–`C`, which includes the three amendments `C44`, `C45`, `C47` that the 37 already
counts. `docs/validation-status.md` has the line-range commands.

## The three absent predecessor documents

The ledger names three documents it depends on or supersedes. **All three are absent from the
source tree**, and none of them is in this repository. They are named here only so that a reader
does not go looking for them and so that no claim is fabricated in their place.

| Document | Where the ledger names it | Status |
|---|---|---|
| `operators_1000(1).md` | Line 300, with SHA-256 `95e846198d956426a348d9f1bc8aa8692e36971b11340a1b3d6c28d446da1e95`. The original 1,000-operator catalogue the ledger amends. | Absent from the tree. The digest therefore cannot be checked, and neither the claim that all 1,000 entries were retained nor the withdrawn "100–150 novel operators" assertion can be verified against its source. |
| `continuation_v1.32/report.md` | Lines 297 and 302, with SHA-256 `ebdcd6e82374c3f8d5af98d58f11af524027e0a5b85cdedfa388e398ddddb4b8`. The workspace baseline that supplied the extraction budget, the ternary comparison and the retry truncation. | Absent from the tree. The constants of Lemma 1 and the premise `p = 759/1024` of Lemma 5 trace to it and cannot be checked. |
| `qpt128-staged-comparison-and-maxdepth-v1.32.md` | The v1.32 staged comparison the ledger supersedes. | Absent from the tree. Referenced as prior work throughout the header; not present to compare against. |

The ledger is explicit about the resulting gap: "This document does not establish that the current
verifier satisfies those hypotheses. The extension and its budget inputs come from the supplied
workspace report v1.32" (line 89), and "No new claim is made that all earlier attachments were
independently re-audited in this pass" (line 297).

## Related domains in this repository

- **D5 extraction-and-signature-reductions** — executes the ledger's own priority 1 (`A18`/`A19`):
  the decoder and the joint-extraction lift. It re-derives the `Q³` coefficient and does not use
  the ledger's inherited `(72+40ℓ)`.
- **D6 qpt128-security-target** — adopts this ledger's work-factor target (lines 26–33) as its D1
  definition, restricts the 320-round result to D1, and replaces the extraction constant with the
  published commit-and-open bound.
- **D1 accountable-quorum-foundations** — carries the same `2t − N` quorum-intersection count that
  `A24` states here. One elementary counting fact is stated in several domains; the repository
  presents it once and cites it.
- **D11 independent-audit-stack** — the audit stack's "math" layer. The checker in this domain is a
  candidate for it, and the weak assertions catalogued in `docs/checker-and-what-it-verifies.md`
  are the ones to strengthen there.

## Reproducing this domain

```
. <env>/activate.sh                       # pinned interpreter; see the repository's environment notes
python3 src/operator_ledger_checks.py > /tmp/observed.json
diff results/operator_ledger_checks.json /tmp/observed.json     # expect no output
```

The extraction of both `src/` and `results/` from the catalogue document is reproducible inside
this repository, because `docs/operator-ledger.md` is byte-identical to the source file:

```
sed -n '19259,19607p' docs/operator-ledger.md > src/operator_ledger_checks.py
sed -n '19093,19251p' docs/operator-ledger.md > results/operator_ledger_checks.json
```

Both extracted files hash to the digests recorded above. `VERIFICATION.md` records the run with
its observed output.
