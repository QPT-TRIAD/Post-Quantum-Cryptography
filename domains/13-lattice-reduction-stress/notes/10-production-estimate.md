# The production estimate — the stop point, and what crossing it produced

Every milestone before this one validated the machinery against synthetic instances and *published*
parameter sets. This is the first execution against the corpus's recorded numbers, and it was made
deliberately rather than by drift: the build carried a structural guard
(`InstanceSource` has no corpus member, and a test fails if one is added) specifically so that
crossing would have to be an act. It was.

## What was run, and what was not

| | |
|---|---|
| parameters | ν = 256, q_L = 2¹⁶, p = 2⁸ |
| sample readings | **both** — `m = 608` rows and `exposure = 672,352` |
| where they live | `problem/production_parameters.py` — recorded constants **with citations**, not read from the research tree |
| what consumed them | `production_parameter_set()` → lattice-estimator |
| lattice built | **none** |
| reductions run | **none** |

At ν = 256 the uSVP dimension is 609. The largest lattice this project has actually reduced is 161,
at a cost of roughly ten minutes for one block size on this host. **Nothing at production scale is
measurable here and nothing was attempted.** What follows is a cost model's output.

Keeping the constants in the project rather than reading the tree has two consequences worth
stating: no source file names the research tree, so the guard that forbids that keeps its meaning;
and the run reproduces without the corpus present.

## The result — the missing lattice row

Both sample readings, because they are different amounts of data to an attack:

| quantity | `rows` (m = 608) | `exposure` (m = 672,352) |
|---|---|---|
| block size, `primal_usvp` | **426** | **368** |
| block size, `dual` | 351 — *not an optimum, see below* | 387 |
| log₂ operations, classical, minimum over models | **124.39** | **107.46** |
| log₂ operations, quantum sieving, minimum over models | **112.89** | **97.52** |
| model attaining the minimum | `primal_usvp` | `primal_usvp` |
| estimator revision | `53da5982597709ba0fdf94ea37a84d822310fd84` | same |

Both figures are pure core-SVP at the block size beside them — 426 × 0.292 = 124.39 and
368 × 0.292 = 107.46 — so the reduction cost *is* the whole cost, with no repetition factor on top.
That is a consistency check on the `primal_usvp` row and not on the dual, which carries repetitions.

The design document's premise was that `AUDIT_LEDGER_v2.1.json`'s `security_exponents` table has no
lattice row — its rows are S1–S6, all hash-based, with one entry noting lattice hardness is *"an
input from the QPT-128 ledger, not re-derived."* This is that row, re-derived.

**More samples make the attack cheaper, which is the opposite of the naive reading.** The primal
block size falls from 426 to 368 as the sample count rises by three orders of magnitude, and the
cost with it. The estimator's `primal_usvp` optimises the lattice dimension it uses, so an attacker
with more samples has strictly more room; 608 samples is a *constraint* on the attack, not a
protection from it. Under the rows reading the attack is sample-starved, and the number is
correspondingly higher.

## The sample count decides the dual column, and the reported rows figure is not an optimum

The two readings differ by 17 bits for the primal and — as the estimator returns them — **136 bits
for the dual**. A gap that size is a claim that needs checking rather than reporting, so it was
checked, by walking the dual attack's own cost surface at both readings
(`scripts/sample_count_sensitivity.py`, whose output is kept in
`results/production_estimate/sample_count_sensitivity.json`).

The mechanism is the project's own normal-form identity showing up inside the estimator. The normal
form replaces the uniform secret with a short one and **pays for it with ν samples**; the estimator
does the same thing, and its `normalize()` returns `m − n`. That leaves

| reading | samples recorded | after the normal form |
|---|---|---|
| `rows` | 608 | **352** |
| `exposure` | 672,352 | 672,096 |

608 samples look ample for 256 unknowns until 256 of them are spent. The estimator's dual search
range is then bounded by the count that survives — `max_beta = min(params.m − ζ, 1754)` on the
*normalised* parameters — so the rows reading searches block sizes only up to 352, while the exposure
reading searches to 672,096.

Walking the surface at the rows reading, at the same normalised parameters the estimator used:

```
beta = 351   2^249.627     <- what the estimator returned, at the top of its range
beta = 456   2^133.152     <- the model's minimum, at a block size it never searched
                              gap: 116.5 bits
```

The cost is still falling when the search range ends, and the true minimum sits 105 block sizes
beyond it. **So the rows reading's dual figure is a bound imposed by the data available, not the
attack's cost** — 116 bits above what the same model says the same attack costs with more samples.
At the exposure reading the same walk finds its minimum exactly where the estimator put it
(β = 387, 2^113.004, gap 0.0), so that column is a genuine optimum and the estimator's answer there
is trustworthy.

The headline is unaffected, and it is worth saying *why* rather than leaving it to luck: under both
readings the minimum over models is attained by `primal_usvp`, and with the dual corrected the
margins are **8.8 bits** (124.39 against 133.15) and **5.5 bits** (107.46 against 113.00). The
reported 124.39 would have been the minimum even had the dual been optimised properly — but that was
not knowable from the estimator's output alone, and under a slightly different parameter set the
uncorrected dual would have been the number quoted as the security level while being 116 bits too
high.

## The reading question has an answer, and it is a threshold rather than a choice

The two readings are 17 bits apart on the headline and the corpus does not say which one a cost
should be quoted against. Left there, the honest report is two numbers and a shrug — and a reader who
needs one number picks whichever suits them.

It does not have to be left there. The cost as a function of the sample count is a non-increasing
**step function**, and measured at these parameters it reaches its floor at **791 samples** and is
flat from there upward. So the exposure reading is not a second opinion: it is the flat region, and
every count from 791 to 672,352 and beyond returns the same block size.

```
m = 608   beta 426   <- the rows reading, on the slope
   618        418
   ...        ...     19 steps, 426 down to 368
   778        369
   779        369     <- first plateau, and NOT the floor
   790        369
   791        368     <- the floor, first attained here
   ...        368       flat from here up
672,352      368     <- the exposure reading
```

Measured by `scripts/sample_count_saturation.py`, kept in
`results/production_estimate/sample_count_saturation.json`. It is a property of this parameter set,
the `ADPS16` classical cost model and estimator revision `53da5982` — so it is recorded with that
provenance and the constant in `production_parameters.py` is pinned to the results file by a test,
rather than left as a number a later edit could drift.

**What it changes.** The question is no longer *608 or 672,352* but **does any single secret
accumulate 791 rows?** That is a question about the corpus's accounting and it has a checkable
answer, which the reading choice did not. Three consequences follow:

1. **The exposure reading is robust.** It does not rest on the exposure arithmetic being exactly
   right. Any per-secret count at or above 791 — which is 0.12 % of the recorded exposure — yields
   the identical estimate, so an error in the corpus's row accounting would have to be enormous
   before it moved this number.
2. **What the corpus supports without an assumption is the higher figure.** The recorded row count
   is 608, and 608 is below the threshold. So **124.39 bits is the number that follows from the
   corpus as recorded**, and 107.46 is the number that follows once the rows are attributed to a
   single secret. Stated in that order, because the lower number is the one a reader will want and
   it is the one that carries the extra premise.
3. **The premise is checkable, and cheap to satisfy.** The secret is fixed per validator while the
   matrix is domain-indexed, so a validator's rows across the 1,024 domains share a secret and the
   exposure is a per-validator count. If that reading is wrong and the 672,352 is a total spread over
   many secrets, the exposure reading is still *forced* for any spread over at most **851** secrets
   (`secrets_that_force_saturation()`, by pigeonhole: with `N` secrets one carries at least
   `ceil(672352/N)`, which is ≥ 791 exactly when `N ≤ 851`). One secret per domain — 1,024 — is above
   that bound and would put the cost nearer the 656-row step, at 115.92 bits.

**A correction to this section, recorded because it is the same defect the section above is about.**
The first version of the script stopped the walk at the first two equal consecutive readings. The
cost function is a step function with more than one flat region, so that reported β = 369 at 779 as
the saturation point — twelve samples low, and wrong in the direction that matters, since a threshold
reported too low makes the exposure reading look safer than it is. The walk now scans for the global
minimum and bisects the interval it was first attained in, which is what returned 791. Both routes
were run independently and agree. The eighteen steps below the floor are kept in the results file so
the next reader can see the threshold's neighbourhood rather than only the threshold.

## The headline comes from a model that only applies by 76 samples

The result above is the estimator's, so it is worth asking when the estimator declines to answer at
all — because **an infinite cost is not a large number**, and a report that rendered the two alike
would be presenting a model that never ran as though it had run and found the scheme strong.

This project had that confusion in writing. The README and a comment in `cost_estimation.py` both
stated that `usvp` "returns an infinite cost for a QLWR instance" and that only the dual family
yields numbers — inherited from M2. It is false at the recorded parameters, where `usvp` supplies
this note's headline. What M2 had measured was the behaviour at a low sample count, generalised to
the scheme.

Measured instead (`scripts/applicability_threshold.py`, output kept in
`results/production_estimate/applicability_threshold.json`):

| family | smallest sample count that applies | m/ν there | margin at `rows` (608) |
|---|---|---|---|
| `usvp` | **532** | ≈ 2.08 | **76 samples** |
| `dual` | 536 | 1.34 → 2.30 over ν = 32…512 | 72 samples |

Below 532 samples at ν = 256 the estimator returns an infinite cost for **every** family: not a high
cost, no answer. The recorded rows reading clears that by 76 samples and the exposure reading by
orders of magnitude, so both estimates above stand. But the margin is the thing to carry: had the
corpus recorded `m ≈ 520` rather than 608, this project would have had nothing to report, and the
correct statement would have been "no applicable attack in this model" — which is not a security
claim and must never be printed as one.

The `usvp` threshold ratio is near-constant (2.13 at ν = 32 down to 2.07 at ν = 512), so it is
roughly a property of the shape. The `dual` ratio is not: it runs from 1.34 to 2.30 over the same
range, which is why the earlier "sample-to-unknown ratio of about 1.6" was a single measurement at
ν = 64 rather than a rule.

## The cross-check, which is the part that makes it more than a model's opinion

The production number is the estimator's, and the estimator is a model. What bounds how much it can
be trusted is the **same-scale comparison** the scaled sweep supplies — and that comparison extends
further than it was designed to.

The clean single-threaded sweep fitted a growth relationship over five dimensions:

```
beta = 0.6926 * d - 24.795      R^2 = 0.9440     d in [40, 130]
```

Extrapolated to the production uSVP dimension of 609, it predicts **β = 397**. The estimator,
evaluated directly at the production parameters, says **426** under the rows reading and **368**
under the exposure reading. The two are **6.8 % apart** and **7.3 % apart** respectively, and they
are not the same route: one is a relationship fitted to measured reduction costs, the other is a
cost model evaluated where there is no measurement at all.

**The two readings now bracket the fit rather than one matching it**, which is worth stating plainly
because it weakens what the agreement shows. The fitted instances carry the rows ratio
(m/ν = 608/256), so if either reading should have matched the extrapolation it is the rows one; it
does not do so better than the exposure reading does. The fit agrees with both to within ~7 %, and
so it is evidence that the *model family* extrapolates sanely. It is not evidence for one reading
over the other, and the two readings differ by 58 in block size — a gap the extrapolation is simply
too coarse to resolve.

For scale: the fitted domain ends at 130 and the extrapolation is to 609 — a 3.8× extrapolation,
far outside anything the fit was built on. The agreement is encouraging and it is **not** a
validation at production scale. It is two models agreeing about a region neither has measured.

## A number in the plan that was wrong, and how

The plan listed an open uncertainty as *"the required β at production scale (≈87 estimated)"*, calling
it the single most consequential number the project would produce. **The production value is 426**
under the rows reading and **368** under the exposure reading — and the plan's figure is not close
to either.

87 is close to what the clean fit predicts at dimension 160 (86.0), and to the estimator's own
same-scale prediction there (88). So the plan's figure was almost certainly the *scaled-dimension*
value, recorded under a production label — the same confusion of two dimensions that produced the
`161`/`228` column defect in section 3 of the reports. Recorded because the plan is what a reader
would check the result against.

## The corpus's two QPT-128 margins, and what separates them

Crossing the stop point meant reading the corpus's security accounting closely enough to know what
this note's number does and does not bear on. Two of its figures do not obviously agree, and **neither
is a lattice number**. Both are recorded because a reader arriving here from the corpus will have met
them; they turn out to be a before-and-after with the transition unmarked, and recomputing them
turned up a third thing — a one-line defect in how Mode B's margin is summed.

### The hidden-signer construction carries +29.4 bits and +7.7 bits

| | source | ledger rows | total | D2 margin |
|---|---|---|---|---|
| Mode S | `QPT128_finalization_v1.43.md:210` | E1–E5 | −159.414 | **+29.414** |
| Mode B | `modeB_rigorous_ledger_v1.47.py`, quoted at `attack_lab_results_v1.51.md:176` | R1–R5 | −137.7 | **+7.7** |

These are not two estimates of one quantity. Both ledgers report `log2 Pr/G`, the ledger sets
`KAPPA = 130`, and both margins are exactly `−130 − total` — so the arithmetic is not in dispute, it
is the same arithmetic applied to different rows. Both totals are also their own dominant row plus a
small correction, which is what a union bound looks like when one term dominates.

**What separates them is a row.** Mode S's ledger has no proof-soundness entry. Mode B's has
R3 = −138.1, and R3 is what its total is now dominated by, where Mode S was dominated by its
simulation row E2 = −159.415 — a row that survives into Mode B as R4 = −159.4. The link-coincidence
path also carries across, E5 = −198.023 to R5, once the v1.52 correction moved R5 from −943 to
−181.2 by identifying that path as the dominant one. The remaining rows differ in both name and
value, so no row-by-row map is claimed here; the load-bearing point is that **R3 has no counterpart
in Mode S at all**, and R3 is the binding row.

The reason is stated in the corpus and is easy to miss. Mode S is a *profile*, not a construction:
`sidecar_free_finalization_v1.44.md:105` says B1 "fixes the relation, frame, extractor and QPT-128
ledger (v1.43 Theorem B); **only the proof is missing**." A ledger for a design with no proof system
cannot contain a proof-soundness row, so +29.4 is the correct margin for a certificate that does not
yet exist. Supplying the proof — Mode A, then Mode B — is what introduces R3, and **the gap between
the two margins is the price of the proof system**, not a revision of an estimate.

The two figures are therefore a before and an after with the transition unmarked, and the earlier one
is the one a reader is likelier to quote: it is larger, and it appears in the document whose opening
line says the question is closed.

### Mode B's quoted margin charges the proof row twice

Recomputing both ledgers from their recorded rows — `scripts/qpt128_margins.py`, output kept in
`results/production_estimate/qpt128_margins.json` — reproduces Mode S to **0.0005 bits**, which is
the rounding of its three-decimal inputs. Mode B reproduces too, but only under a combination the
corpus does not describe.

The v1.49 revision replaces the proof-soundness row's *model*, from DFMS-modelled to FAEST v2's
Lemma 9.39 form. In `modeB_rigorous_ledger_v1.47.py` the replacement is written as

```python
led = ledger(tau, b, grinding)                    # computes the DFMS-modelled R3
led['rows']['R3 proof soundness (FAEST v2 Lemma 9.39 form, degree 6)'] = row
total = math.log2(sum(2 ** v for v in led['rows'].values()))
```

The new row is stored under a **key distinct from the row it replaces**, so the DFMS row is still in
the mapping when the total is summed. **Proof soundness is charged twice**, and the resulting margin
is what the corpus quotes:

| combination | total | D2 margin |
|---|---:|---:|
| both R3 rows — *what the code sums, and what is quoted* | −137.669 | **7.669** |
| FAEST row only — the revision read as a replacement | −138.081 | **8.081** |
| DFMS row only — the pre-v1.49 model | −139.642 | 9.642 |

So the quoted 7.7 understates the margin by **0.412 bits**, and the proof system's true price is
21.333 bits rather than 21.714.

It is not one number. The block loops over five settings, calling `ledger()` and then adding the
FAEST row under a second key each time, so **every setting in the v1.49 table is double-charged** —
including the three alternatives the security document quotes beside the headline
(`modeB_security_v1.49.md:137`: 11.5, 3.7, 15.0). The defect is one line applied to a loop, so
correcting it moves the whole table.

**The rule is not in dispute, and that decides who owns the fix.** The corpus's own auditor contract
states it — *"Probabilities add; exponents do not"* — and `log2(sum(2**v))` is that rule, correctly
applied. What went wrong is that a superseded row was **left in the mapping**, not that the mapping
was summed wrongly. This is a stale-row defect, not a modelling disagreement.

### What "conservative" is scoped to, and what it is not

The direction is provable rather than observed: the two-charge sum is `Σothers + 2^dfms + 2^faest`,
the single-charge sum is `Σothers + 2^faest`, and since `2^dfms > 0` the two-charge total is *always*
larger and its margin *always* smaller, for any row values. Monotonicity of a union bound does the
rest.

That proves the sign. **It does not prove that no corpus claim is affected**, and the earlier version
of this section said so anyway — writing "no security claim in the corpus is inflated by it" on the
evidence of a single comparison's direction. That is this project's recurring defect, and it appeared
here in the same pass that was documenting it elsewhere. What is actually established, by enumerating
rather than reasoning:

| checked | result |
|---|---|
| consumers of the figure | **three** — `modeB_security_v1.49.md:135` and `attack_lab_results_v1.51.md:176` as prose quotes, `ceqs_attack_lab_v1.51.py:613` as a **hardcoded literal** in a report dict |
| any threshold reading it | **none.** `D2_pass` at `modeB_rigorous_ledger_v1.47.py:173` is attached to the *plain* ledger's total (line 171); the FAEST block at 222-227 emits a total and a margin with **no test at all** |
| does it reach the summary ledger | **no.** `AUDIT_LEDGER_v2.1.json` has ten rows, S1–S6, and **no hidden-signer row**; `7.7` does not appear in it |
| the same pattern elsewhere | **nowhere** — the mutation-then-sum shape occurs at `modeB_rigorous_ledger_v1.47.py:222-223` and at no other site, in the on-disk corpus or inside the shipped tarballs |
| Mode S's ledger | clean, but it sums **exact rationals** (`sum(ratios.values(), F(0))`) where Mode B uses float `log2` — the same rule at different precision, which is why Mode S reproduces to 0.0005 bits and Mode B only to 0.031 |

So the honest sentence is: **no claim that consumes this figure is inflated by it**, over an
enumerated consumer list — not "no security claim in the corpus". The stronger version was not
checked and is not supported.

And the quoted `7.7` is rounded from `7.669`, i.e. *upward*, by 0.031 bits. Both are below the
corrected 8.081, so the net direction is still conservative — but the rounding runs the other way,
which is worth knowing when the corpus's own contract says *"if the margin is thin, say the number —
do not round it into comfort."*

### The question is "closed" and the deployed claim is "OPEN"

`operators_1000_QPT128_amended_v1.33.md:11` — *"The complete deployed QPT-128 claim remains
**OPEN**"* — naming what is missing: a reduction's compressed-oracle database is not automatically a
public input available to a conflict extractor, and the joint decoder, the concrete
signature-hardness bound at the reduction's resources, and the deployed-hash connection still need
evidence. `QPT128_finalization_v1.43.md:12` — *"The QPT-128 question is now closed."*

v1.43 scopes its own claim in the next sentence: *"It was not closed before for three reasons, and all
three are fixed here"* — the three being that the project aimed at two different targets (D1 work
factor against D3's unattainable advantage bound), never pinned the unit of cost, and never charged
reduction running time. Each is a defect in **method**, and fixing them is a real result. It is not a
claim that the deployed construction is qualified, and the corpus keeps saying so afterwards:
`research_qualification_v1.18.md:279` (*"128-bit QPT qualification of the composition and trace
parameters | **Open**"*), `pqt.md:1196-1226` (§25, the LWR parameter-validation obligation), and C3.5
at `multitrack_verification_v1_20.md:132`.

### Neither margin is a deployment figure, and Mode B is not the deployed profile

The two items are the same item: v1.43's headline PASS is a ledger with **no proof row**, and the
proof was still missing when that document was written. So +29.4 is not a margin any deployable
certificate can have.

But **+7.7 is not one either**, and the first version of this section said it was. Mode B is
research-only and always has been. `test.md:241`, in the corpus's own words — *"Hidden-signer Mode B
is research-only: no production proof backend, no security theorem. Never compile it into a node."*
The **deployed** profile is **B0**, the public-signer certificate, at **+23.0 bits**
(`QPT128_finalization_v1.43.md:28`; `ledger.rs:41-42` carries `D2_MARGIN_BITS = 23`), and its ledger
is a separate one that this note never touches.

So the shape is: **+29.4 for a hidden-signer profile with no proof, +8.081 (quoted +7.7) for a
research design that will not be deployed, +23.0 for the thing that is.** Writing +7.7 into the
sentence "the margin a deployable certificate has" was a scope error of exactly the kind the two
paragraphs above are about — the number is right, the noun it was attached to was not.

Mode B's status is recorded in `problem/qpt128_accounting.py` as a constant with its citation, beside
the margins, so the figure and its scope travel together.

**None of these figures is a lattice number.** Both margins are `log2 Pr/G` in gate units against a
2^130 target with 2^18 gates charged per hash query. The production estimate in this note is in
sieving operations. There is no conversion between the two currencies in the corpus or in the work it
cites, so nothing here can be set against +29.4 or +7.7 — and neither can be set against 107.46.

## The corpus states no lattice claim for these parameters, and no profile carries one

This is the strongest result in this note, and it is an absence. Asked to produce "the corpus's QLWR
lattice-hardness claim" so the estimate can be checked against it, the corpus has none — and the
absence is threefold:

| looked for | found |
|---|---|
| a bit-security figure for ν=256, q_L=2¹⁶, p=2⁸, m=608 / 672,352 | **none** anywhere |
| a named attack family the number is a minimum over | **none** — the claim attaches to no family |
| a profile the claim attaches to | **none of the live ones** |

The nearest thing to a number is a **budget allocation**, not a derived hardness:
`pqt.md:2128-2143` says *"suppose … ε_QLWR ≤ 2⁻¹³¹ … Hence a six-row ledger at 2⁻¹³¹ leaves three
bits of aggregate margin."* That `2⁻¹³¹` is what the ledger assigns to the row, which is the input
the missing analysis was supposed to produce. `pqt.md:1548` says so directly: the exact LWR hardness
matching *"must be populated"*.

**No live profile uses QLWR at all.** Occurrence counts of `LWR`/`QLWR`/`trace`: **zero** in
`B0_wire_spec_v1.44.md`, zero in `QPT128_finalization_v1.43.md`, zero in
`sidecar_free_finalization_v1.44.md` and the Mode S documents, zero in `modeB_security_v1.49.md` and
`hidden_signer_32KiB_v1.46.md`. B0 rests on *"EUF-CMA of the chosen category-5 signature"*
(`QPT128_finalization_v1.43.md:39`); Mode S instantiates the same link-and-mask roles with a
hash-based domain PRF and Keccak (`sidecar_free_finalization_v1.44.md:164-167,192`); Mode B's handle
is the power map `Z = r⁷ ⊕ c_a s ⊕ c_b s² ⊕ c_c s⁴`. QLWR appears **only in the withdrawn original**,
the one `attack_lab_results_v1.51.md:7` describes as refuted and replaced.

The corpus's only Core-SVP numeric claim, `pqt.md:1621` ("greater than 2¹²⁸ quantum gates"), is
attached to a **different parameter set** — `pqt.md:1614-1619` specifies k = 4, n = 256, q = 3329,
η = 2, i.e. an ML-KEM-1024-like Module-LWE instance — and is sourced only to a bare NIST URL. It is
not this instance and must not be read as its hardness.

So the estimate in this note is not a check on a claim. It **fills an obligation the corpus records
as open** — C3.5 at `multitrack_verification_v1_20.md:132`, §25 at `pqt.md:1192-1226`, and
`research_qualification_v1.18.md:279` — under a heading the corpus itself supplies at
`pqt.md:1542-1548`: *"Concrete QPT-128 instantiation — **NOT YET NUMERICALLY CERTIFIED**."*

That is a cleaner position than it first appears. A number produced against an open obligation,
labelled with its reading and its model, is a contribution; a number produced against a claim that
names no attack family would have been an answer to a question the corpus never asked.

## The estimator converges onto the measurement inside the domain

The estimate is an extrapolation, so what bounds it is the model's behaviour where it *was* checked.
Measured (`scripts/estimator_vs_measured_gap.py`, output in
`results/production_estimate/estimator_vs_measured_gap.json`), from the discrepancies the pipeline
already recorded per run:

| dimension | measured β | estimator β | difference |
|---:|---:|---:|---:|
| 61 | 10 — *at the search floor* | 40 | +30 *(clamped)* |
| 81 | 30 | 40 | **+10** |
| 101 | 40 | 44 | **+4** |
| 131 | 70 | 69 | **−1** |
| 161 | *not reached* | 88 | — |

**The over-prediction decays monotonically to zero and is gone by d = 131.** A positive difference
means the estimator asked for a *harder* attack than the reduction needed — pessimistic about the
attacker, hence optimistic about security, which is the direction that would matter. But it does not
persist: the production estimate is taken from d ≈ 130, by which point the model has converged onto
the measurement.

Two things decide whether those numbers mean what they appear to. **The measured block size is
clamped at the bottom of `block_size_range`, which starts at 10**, so a measured 10 means "succeeded
at the cheapest block size tried", and the real difference is a *lower bound*. d = 61 is such a
point, and it is also the only primal anomaly the pipeline's own 25 % tolerance flags anywhere in the
sweep — so **the project's one flagged anomaly is an artefact of the search range, not a
disagreement with the model.** The machinery cannot see this, because it does not know the floor.
Separately, d = 161's anomaly is genuine and of a different kind: the attack recovered nothing inside
the sieve cap, which is an absent measurement rather than a disagreement, and it is reported that way
rather than as agreement.

## A correction applied at the point of quotation, but not at the point of origin

Three premises in one review pass turned out to be already-corrected errors. Two of the three were
things this project had fixed **earlier in the same session**. That density is worth diagnosing
rather than noting, because the mechanism is not what it looks like.

**It is not drift in whoever restates the project's state, and it is not a check-sequence design
flaw. It is that the corrections were applied where the claim was *quoted* and not where it was
*made*.**

| stale premise | corrected in | left standing in |
|---|---|---|
| `usvp` returns an infinite cost for a QLWR instance | README, `cost_estimation.py` comment | **`notes/02-estimator.md:36` — as a bold section heading, "Finding 2"** |
| "below a ratio of about 1.6 every family returns an infinite cost" | README | **`notes/02-estimator.md:21`**, and two docstrings in `tests/test_cost_estimation.py` |

`notes/02-estimator.md` was the **origin of both**. It is the M2 note; the claim was made there,
quoted from there into the README, and when the claim was found false the README was fixed and the
note was not. So the false version survived in the one place the project treats as its record — and
anyone, or anything, that consults the project's own account of itself finds it there. The premise
did not go stale in transit; **it was never corrected at the source, and the source is what gets
read.**

One of the three is a different failure and should not be filed with the others. The Kyber figure was
correctly recorded as a *closed* finding at `notes/00-api-probe.md:19` — *"A misattributed figure —
mine, not the tool's"* — and the premise reused it as evidence of an **open** risk. Nothing in the
repository was stale; a correctly-labelled past finding was read as a present one.

The distinction matters because the fixes differ. The second is a reading error and needs no change
to the project. The first is structural, and it is the **third appearance of one defect class** in
this project: a fix applied to one instance of a claim and not to the instances that mirror it. The
double charge was a row replaced under a key that did not overwrite it; the Mode B sentence attached
a right number to a wrong noun; this left a corrected claim in place at the place it was authored.
All three are *incomplete propagation*, and none of them is detectable by testing the thing that was
changed — only by looking for the other copies.

The discipline that follows, and it is cheap: **when a claim is corrected, correct it where it was
made, and grep for its other appearances rather than fixing the one in front of you.** Both of these
were found by a single `grep -rn` for the claim's distinguishing phrase, which took seconds and had
not been run.

## What this is not

**It is not a security claim about the scheme.** Three things stand between the number and such a
claim, and each is recorded rather than resolved:

1. **Core-SVP is a lower bound on cost that ignores the practical overhead of an attack.** The
   estimator's `rop` counts operations in a sieving model; a real attack pays for memory, for the
   number of tours, and for the gap between the model's assumption and the implementation. The
   design document's own scope boundary says this project's numbers are not security claims, and
   that applies to this row.

2. **The corpus contradicts itself about `p`.** `security_proof_v1.3.md:101` requires `p` prime for
   public tracing, while the only recorded numeric set uses `2⁸`. The estimate above is for `p = 2⁸`
   because that is the value in the table. It does not satisfy the prime requirement, and this
   project does not resolve which reading governs.

3. **The sample count is still not derived, but the choice between the two readings no longer has to
   be made blind.** The corpus records `m = 608` rows and an exposure of 672,352 and does not say
   which one a cost should be quoted against; they differ by 17 bits on the headline. What the
   saturation section establishes is that the difference is a **threshold rather than a range** —
   every per-secret count at or above 791 gives the exposure reading's answer identically — so the
   number is well defined once the rows' attribution is known. In that order: **124.39 bits follows
   from the corpus as recorded**, and 107.46 carries the additional premise that some single secret
   accumulates 791 rows. Quoting either without saying which reading it was made under is the failure
   this project's provenance discipline exists to prevent; the near-miss here is that the number a
   careless reader would have quoted was the 116-bits-too-high one.

## State

The build is complete through M11, the sweep is clean and reproducible, and the production estimate
exists. Every number above carries its provenance, and none of the measured and extrapolated figures
are blended.

Three things were wrong before this pass and are corrected rather than quietly dropped, because each
had been stated confidently by this project's own writing:

1. **The dual figure for the rows reading** was reported as an optimum. It is a cap, 116 bits high.
2. **"`usvp` returns an infinite cost for a QLWR instance"** — in the README and in a code comment.
   It is a statement about a sample count, and at the production parameters `usvp` is the binding
   attack.
3. **"a sample-to-unknown ratio of about 1.6"** — one measurement at ν = 64, generalised. The `usvp`
   ratio is near-constant at ≈ 2.08; the `dual` ratio is not constant at all.

All three are the same defect: a claim that was true where it was measured, written as though it were
true everywhere — the project's recurring failure mode, here appearing in prose rather than in code,
where no test was watching. The two numeric ones now have a script apiece, so the next reader
measures rather than trusts.

A fourth appeared during this pass and is corrected in place rather than dropped, because it is the
same defect committed again: the saturation walk originally stopped at the first flat region and
would have published a threshold twelve samples low. It was caught by re-deriving the number a second
way, which is the only reason the section above exists in the form it does. That makes three measured
quantities this pass added — the dual surface, the applicability thresholds, and the saturation
point — each with a script, a kept result, and a test that fails if the recorded constant drifts from
the measurement behind it.

**The estimate is a model's output and remains one.** Nothing here is measured against a reduction at
production scale, because nothing at production scale can be reduced on this host. What the saturation
section adds is not evidence about the scheme; it is the reason the *reading* is no longer an
unresolved ambiguity in this project's own reporting.
