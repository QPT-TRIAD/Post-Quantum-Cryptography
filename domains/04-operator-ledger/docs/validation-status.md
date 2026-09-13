# Validation status: what is proved, computed, assumed and merely asserted

The ledger is a review document, not a proof. Its own contract `A23` states the rule that a reader
has to apply to it (line 702): *"Keep arithmetic tests, finite-model proofs, literature
theorems and unproved protocol assumptions as separate statuses. A green eligibility flag is not
itself a cryptographic proof."* The ledger names four statuses there. This document sorts the
ledger's contents into them, adds the fifth status the ledger needs and does not name, and states
what each one is worth.

## Status 1 — proved in the text (Lemmas 1–8, lines 66–270)

Eight lemmas are written out with proofs. The ledger labels all of them at line 68: *"elementary
derivations for this amendment. They are not claims of new results in the mathematics literature.
Any protocol-level application must discharge the stated premises."* The label is honest — Lemma 1
is algebra, Lemmas 2–3 are operator-norm estimates, Lemma 4 is a digit count, Lemma 5 is the tower
property plus a Bayes-style ratio, Lemma 6 is a rank census and a data-processing inequality, Lemma
7 is elementary scheduling arithmetic, Lemma 8 is weak duality plus a one-query distinguishing test.

The proofs are not where the weakness is. The weakness is that **every lemma that touches the
protocol is conditional on a premise the ledger states and does not discharge**:

| Lemma | What the proof actually establishes | The premise that is left open |
|---|---|---|
| 1 | The algebraic inversion of `J ≤ τ` into a bound on `p_*`, given a `B₀` | That the expression `J` describes the current verifier at all (85) |
| 2 | `Pr[∩B_t] ≤ ∏β_t` from a uniform per-round bound, classical and for a certified failure instrument | That the real verifier's failure instrument carries the certificate (152 — called **open**) |
| 3 | `‖K‖ ≤ 2^{-1/2} + η` and the resulting round counts | That some concrete instrument satisfies the `9/16` certificate (150 — "no such allowance has yet been proved") |
| 4 | The exact maximal mass of a base-`b` product box | That every nonextractable challenge set lies in such a box (206) |
| 5 | `E[X \| G₁∩G₂] ≤ ε(1−d₁)/(1−d₁−d₂)` and the retry tail `p^R` | That `G₁`, `G₂` are the actual good-key events, and that `p ≤ 759/1024` uniformly (227) |
| 6 | The rank census over `F_q`; entropy cannot increase through a deterministic map | That the deployed matrix is uniform over the field (238) |
| 7 | Work/depth composition; affine loss composition | None for the arithmetic; MAXDEPTH is explicitly not a security argument (255) |
| 8 | Strict weak duality; a fixed hash is distinguishable from an independent oracle | None for the negative half; the ledger notes it does not refute simulator-based indifferentiability (267) |

So Status 1 is: **eight correct elementary arguments, none of which closes a protocol obligation by
itself.**

Two wording cautions found while reading, which a careful reader should carry:

- Line 150 reads "the sufficient absolute perturbation allowance is at most `3/4 − 1/√2`". The
  intended statement is that `η ≤ 3/4 − 1/√2` suffices; as written it reads as an upper bound on
  admissible allowances, which is a different (and false) claim at large `η`.
- Lemma 3's proof is correct for the *stacked* map, and the ledger says the perturbation must be
  proved for the whole stacked map (138–142). A per-entry numerical error does not substitute for
  `η`. The `9/16` figure the whole headline rests on is a **premise for the protocol, not a result**.

## Status 2 — computed exactly (the checker, `src/operator_ledger_checks.py`)

Reproduced in full; see `VERIFICATION.md`. The output is byte-identical to the recorded block. The
arithmetic in it is correct: exact `Fraction` throughout, no floating-point decisions, no
randomness. The two groups that compare a closed form against an independent enumeration (group 14,
490 prefix counts and 156 box instances against brute force; group 17, 673 matrices against the rank
census) carry the strongest form of evidence here, because their counterpart is not the same pass's
opinion.

What Status 2 supports, and what it does not:

| Computed | Worth |
|---|---|
| Minimum rounds 73/137/193/265 at `s = 32/64/92/128` and 88/165/233/320 at `β = 9/16` | Exact, and correctly minimal, **for the formula `J`**. The formula is Status 3. |
| `joint_raw(128,512,1/2^128) > 1`; `minimum_rounds(128,½,h=256)` is `None` | The 256-bit hash width cannot meet the 128-bit target under this budget; correct arithmetic on the same borrowed formula. |
| Retry boundary `2^64·(759/1024)^519 ≤ 2^-160 < 2^64·(759/1024)^518` | Exact and tight. The base `759/1024` is an assumption, not a derived value. |
| Quorum intersection `≥ 5+5−7` over 441 pairs | A true counting fact at `N=7`; the general statement is elementary and the ledger labels it "only a set-counting lemma" (717). It is not an authorization theorem. |
| 673 matrices, 490/156 brute-force cross-checks, 54 commutator cases, the `KᵀK` certificates, the nilpotent and measurement-order counterexamples, matching pennies | Correct finite facts about the objects named. Each refutes a specific over-claim. |
| Groups whose asserted value is a **literal written by the same pass** — `T7`, `T42`, `D9`, `I21`, `I33`, and the conditioning half of group 16 | These confirm that the corrected value differs from the source's value. They cannot detect an error *in the correction*, because the correction and the literal came from the same author at the same time. |

The checker never certifies a theorem: `cryptographic_theorem_verified` is the literal `False`, and
group 23 asserts it stays `False` even for a self-compatible record. The final JSON says
`"full_QPT128_established": false` and lists seven open premises.

## Status 3 — assumed, and not established anywhere in this repository

- **The `9/16` challenge-mass premise** for the real protocol's failure instrument (Lemma 3, 150).
- **The joint-extraction expression** `J = ((72+40ℓ)Q³ + 2v)/2^h + 20Q²p_*` (74–76). Its only stated
  provenance is "the supplied workspace report v1.32" (89) — a document that is **absent** — and its
  own description of itself as "my derivation from the published lemmas". No theorem, page or
  equation number is given. Later project documents derive `(20ℓ+60)Q³` and `(22ℓ+60)q³` instead;
  the ledger is not flagged as wrong and the round tables do not move, but the record's consistency
  does.
- **The retry bound `p = 759/1024`** (Lemma 5, 227).
- **The two named inputs**, `operators_1000(1).md` and `continuation_v1.32/report.md`, whose SHA-256
  digests are recorded at lines 300 and 302 and **cannot be checked**: both files are absent from the
  tree. The retention claim ("all 1,000 entries have been read and retained", line 7) cannot be
  verified against an original that does not exist here.
- **The seven open premises** in the recorded JSON: the actual joint relation decoder, a public
  conflict extractor without the reduction's sidecar data, the `p_*` bridge for the actual protocol
  and sampler, concrete signature hardness at the reduction's resources, a compatible signature
  good-key event with a standardised algorithm adapter, the deployed hash's game properties, and
  concrete gate/depth/memory accounting.
- **That the deployed verifier satisfies `[S1]`'s special-soundness and Merkle-commitment
  hypotheses.** The ledger says so itself at line 89: *"This document does not establish that the
  current verifier satisfies those hypotheses."* Every extraction claim in the ledger that descends
  from `[S1]` inherits that gap.

## Status 4 — proved elsewhere, used under hypotheses (`[S1]`–`[S8]`)

Eight sources, fourteen citation instances in five lemmas and seven contract-scope paragraphs, none
in a catalogue entry (`docs/theory-borrowed.md` carries the per-source analysis). Three of the eight
are cited without the locator a reader would need: `[S1]` has no theorem number, `[S2]` has no year
and a truncated author list, `[S5]` is a web page with no date whose normative counterpart (a NIST
standard) is not cited. None of these are fatal; all of them mean the borrowed part cannot be
checked from the ledger alone.

## Status 5 — asserted only: the 116 amendments

This is the status the ledger does not name, and the one that decides what the catalogue is worth.

An `Amendment (LABEL)` paragraph is a prose correction of an inherited "source property". Nothing in
the document proves it. There is no citation, and — except where the checker exercises it — no
executable check. The measurement follows.

### Counts, reproduced

```
grep -c '^\*\*Amendment (' docs/operator-ledger.md                      # 116 amendments
grep -n '^\*\*Amendment (' docs/operator-ledger.md | head -1            # first at line 804
awk 'NR>=788&&NR<=9697'   docs/operator-ledger.md | grep -c '^\*\*Amendment ('   # 79  (L1–C35)
awk 'NR>=9698&&NR<=19059' docs/operator-ledger.md | grep -c '^\*\*Amendment ('   # 37  (C36–Z50)
grep '^\*\*Amendment (' docs/operator-ledger.md | grep -cE '\[S[1-8]\]|[Ee]xternal references? S[1-8]|https?://|arXiv|FIPS|RFC [0-9]|doi:|NIST'
                                                                        # 0   amendments carrying a citation
```

Per-family amendment counts, from the same file by line range: `L` 16, `T` 8, `F` 7, `Q` 8, `D` 7,
`I` 8, `P` 8, `S` 7, `M` 7, `C` 6, `H` 3, `K` 3, `N` 2, `X` 3, `G` 0, `R` 9, `O` 5, `W` 2, `Y` 5,
`Z` 2 — sum 116, matching the ledger's own provenance table (306–327).

Entries named by a checker group, taken from the Check column of the ledger's own results table
(lines 19066–19088):

```
sed -n '19066,19088p' docs/operator-ledger.md | cut -d'|' -f2 | grep -oE '\b[A-Z][0-9]{1,2}\b' | sort -u
# D9 H20 I21 I33 L1 L10 L35 L47 L9 Q40 R36 T42 T7 T8 Y1   (15)
```

### The finding recorded in the reading record, checked

The reading record states: *"113 of the 116 amendments, and 34 of the 37 in this range, have no
executable witness and no literature citation"*, and the theory index carries it forward as
**"113 of the 116 ledger amendments have no executable witness and no citation"**.

**That figure is not reproduced.** Measured against the document:

- **116** amendments exist (above), not 130 as the same record's decomposition paragraph states.
- **15** of them are named by a group in the checker's own 23-row results table (command above).
  Discounting the five whose group rests on a literal or on `assert (1-2)==-1` — `T7`, `T42`, `D9`,
  `I21`, `I33` — gives **10** amendments with a *computed* witness.
- **0** of the 116 carry a literature citation. All 14 citation instances in the document fall on
  lines 89–732, before the first amendment at line 804; the per-source split is `S1` 3, `S2` 1,
  `S3` 3, `S4` 3, `S5` 1, `S6` 1, `S7` 1, `S8` 1.
- Therefore **101 of the 116 amendments have neither an executable witness nor a citation**, or
  **106** on the stricter reading that a witness must compute the corrected value. It is **not 113**.

The claimed 113 is exactly `116 − 3`, and 3 is the correct witness count for the *second half of the
document alone*: the same sentence's other half, "34 of the 37 in this range", is right, and the
three second-half witnesses are `H20`, `R36` and `Y1`, which are the three the dossier names. The
whole-file figure is that half-range result carried across to a denominator that does not belong to
it, and it contradicts the same reading record's own classification of the first half, which lists
nine first-half amendments as carrying executed checker evidence (that record's criterion is not the
one used above, under which 12 first-half amendments are named by a checker group). Two of the
ledger's own sentences are more careful than either figure: the results table says "They do not test
all 116 editorial amendments" (19062), and the header says the counts "describe review coverage, not
1,000 certified mathematical theorems" (7).

One further decomposition error in the same record: it gives the halves as "82 in the D4a range, 37
in the D4b range, 11 elsewhere". The ledger's half boundary is `C35`/`C36` (the reading record says
the second half is `C36–Z50`), and by line range the true split is **79 + 37 = 116**. The 82 is the
sum of the per-family counts for families `L`–`C` *as whole families*, which spans the boundary and
includes `C44`, `C45`, `C47` — the three amendments that the 37 already counts. The "11 elsewhere"
and the total "130" are not reproducible from the document in any reading found here.

### What an amendment without an executable witness means

For the ledger's headline, less than it looks: the 320-round result rests on Lemma 3's arithmetic,
the `9/16` premise, and the borrowed constant `J` — none of which is an amendment. The 116
corrections are not load-bearing for the number the domain exists to report.

For the catalogue, this is the whole story. The catalogue's value is its 818 parked verdicts and its
182 routings, and *every one of those verdicts is a judgement about an uncertified claim*. The
ledger handles this correctly at the top level — "No amendment means **not certified**, not 'true'"
(304) — but an amended entry inherits exactly the same epistemic status as an unamended one: the
correction is text. Two consequences follow, and they pull in opposite directions.

1. **A correction with no witness cannot be relied on, including when it is a rejection.** When an
   amendment says a named theorem is "false as stated" or that a route does not exist, and nothing
   checks it, the routing decision that follows is only as good as the prose. If such an amendment
   is wrong, a route the ledger closed may in fact be open. This is the direction that costs the
   ledger something: 818 parked entries are parked on the strength of judgements of exactly this
   kind.
2. **A correction with no witness is still a strictly better record than no correction at all.** The
   source property is retained beside it as historical text, so a reader sees the claim and the
   objection together and can adjudicate. The amendments sampled closely for this document —
   `R36` (Schmidt rank falls under a local reset, which group 21 builds), `R18` (`ΔF = F(initial) −
   F(final)` makes nonincreasing free energy give `ΔF ≥ 0`), `P17` (an infinite path signature is
   not an authentication signature), `H7` (interval decomposition needs pointwise
   finite-dimensional modules over a field), `C45`, `C47`, `F8`, `M25`, `S16` — are correct as
   stated. Nine hand-checked items out of 116 is not a sample a reader should generalise from, and
   no systematic audit of the other 107 was performed here.

The structural limit is worth stating plainly, because it cannot be fixed by adding checks of the
same kind: **the checker's witnesses were written by the pass that wrote the corrections.** Where a
group asserts a literal, the literal is that pass's own corrected value, so a PASS confirms
self-consistency, not truth. Only a witness derived from something the correcting pass did not
author — an independent enumeration (as in groups 14 and 17), a published theorem with a located
statement, or a counterexample a reader can verify by hand — raises an amendment above Status 5.
Measured that way, 10 of 116 amendments clear the bar, 15 are named by a group, and the remaining
101 are editorial judgements whose only support is the sentence that asserts them. A reader who
needs one of the 116 claims for a real obligation must therefore discharge it independently; the
ledger's own `A23` questions (696–710) are the right template for doing so, and its question
`A23-Q2` — "Can independent brute force check a closed-form counter without reusing its recurrence?"
— is precisely the question most of the 23 groups do not answer about themselves.
