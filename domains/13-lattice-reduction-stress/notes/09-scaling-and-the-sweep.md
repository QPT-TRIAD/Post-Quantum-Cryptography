# The dimension sweep, and a fit that had to be replaced

Running a real sweep across the configured dimension range is the one thing M11 recorded as
unexercised: the fit had been tested against a synthetic frame with a *known slope*, which cannot
distinguish "the model holds" from "the fit works". Exercising it found that the fit, as specified,
measures the machine rather than the model.

## What the sweep produced

| dimension | nu | minimum block size | measured points | slowest point | refused |
|---:|---:|---:|---:|---:|---:|
| 40 | 17 | 10 | 1 | 3.7 s | 0 |
| 60 | 25 | 10 | 1 | 6.1 s | 0 |
| 80 | 34 | 20 | 2 | 32.1 s | 0 |
| 100 | 42 | 40 | 4 | 46.2 s | 0 |
| 130 | 55 | 60 | 6 | 119.9 s | 0 |
| **160** | **67** | **none found** | **5** | **132.8 s** | **3** |

**The sweep cannot reach its own largest configured dimension, and it says so.** Dimension 160
measured a minimum at nothing in the range: block size 50 took 132.8 s and did not recover, and the
guard refused everything above it —

```
beta=60: projected   728 s from the measured 132.8 s at block size 50
beta=70: projected  3985 s
beta=80: projected 21828 s   <- six hours
```

That is the guard doing exactly the job it was added for. Without it, dimension 160 alone would
still be running, and the sweep would have produced one number six hours later instead of five
dimensions and a recorded refusal.

**The refusal and the fit agree**, which is the strongest form this result could take. The growth fit
over the five dimensions that did reach a minimum — slope 0.598, intercept −21.1, **R² 0.929** —
predicts block size **74.7** at dimension 160. The sweep refused from 60 upward because it could not
be reached in budget. Two independent routes, one number: the threshold at 160 is around 75, and it
was not measured because reaching it needed more time than the run allowed.

## The fit as specified produces a negative exponent

The design document says to fit the core-SVP model — ``2^(c*beta)`` — to
``(dimension, minimum successful block size, wall-clock time)`` triples. Fitting
``log2(wall_clock)`` against block size gave:

```
slope c = -0.1545      (core-SVP constants are +0.292 classical, +0.265 quantum)
R^2     =  0.8563
```

**A negative exponent says cost decreases with block size, which no reduction does.** The cause is
that the two axes are *separately determined*:

- the minimum block size is a property of the **instance**;
- the wall clock is a property of **this machine and this engine** at that block size.

Measured: dimension 40 reached its minimum at block size 10 in **3.69 s**, while dimension 80 reached
its minimum at block size 20 in **1.63 s** — faster at a *larger* block size. Fitting one against the
other assumes they are the same quantity, and across a handful of points they are not.

The result is now **refused** by a distinct ``NonPositiveSlope`` exception rather than returned. A
negative ``c`` would flow into every extrapolation downstream and look exactly like a number, which
is the failure mode this project has now hit three times: a plausible figure produced by a
computation that was answering a different question.

## What replaced it

``fit_block_size_growth`` fits the **required block size against lattice dimension** — the
relationship a sweep can actually measure — and core-SVP is applied afterwards, as a separate step:

1. **measured**: ``beta_min`` against dimension, over the dimensions that reached one;
2. **extrapolated**: evaluate that fit at the target dimension, then apply core-SVP at the resulting
   block size.

The two steps are labelled separately so a reader can reject the second without rejecting the first,
which is the whole reason to keep them apart. And the growth relationship is monotone in the
direction the model needs, so it cannot produce a sign error — where it is wrong, it is wrong in
``r_squared`` rather than in a sign.

**Dimensions that never reached a minimum are absent rather than zero.** A dimension the attack could
not solve within the configured range says nothing about how the block size grows; entering a zero
would drag the slope down with a measurement that was never made.

## A resolution limit that inflates the apparent growth

The configured ``block_size_range`` is ``[10, 20, 30, …, 80]`` — **step 10**. The measured threshold
is therefore quantised, and dimensions 40 and 60 both report 10 because their true values fall in the
same bin. Part of the apparent doubling (10 → 20 → 40) is that quantisation rather than growth.

This inflates the apparent super-linearity and would let a poor ``r_squared`` be blamed on the model
rather than on the measurement. The fix is a finer grid at the small end — step 2 or 5 below
dimension 100 — not a different growth model. Recorded rather than corrected here, because changing
the grid changes every recorded number and should be a deliberate re-run.

## The report read a shape the pipeline had stopped writing

The refit changed what the pipeline writes: `scaling` became nested — `kind`, `measured`,
`extrapolated` — because the measured step and the extrapolated step must be separately rejectable.
`reporting/report_generator.py::_section_extrapolated` was not changed with it, and still read the
old flat keys. Every swept run's section 5 rendered as:

```
## 5. Production-scale extrapolation — extrapolated — not measured
| slope c in 2^(c*beta) | — |
| intercept | — |
| R squared | — |
```

**310 tests passed while this was true.** The fit was correct; the renderer was internally
consistent; only their *agreement* was broken, and no test computed the quantity both ways.

This is the fourth defect of the project's recurring class — a self-consistent object that is
nonetheless wrong — and the first caught by a **new detection route: reading the rendered output**
rather than a cross-check, an exact solve, or an independent algorithm. It is the cheapest of the
four routes, and it found something none of the others would have: the numbers were all correct and
the reader still could not see them.

The failure is specifically a *boundary* defect, in the sense the integration pass established. It
also has a property worth naming: a table of dashes is not ambiguous, it is **misleading**. It reads
as "no fit was produced", which is a claim about the run rather than about the report — the same
shape as the inapplicable-versus-absent distinction that section 4's note exists to preserve.

Guarded now by four tests: the cross-sweep shape renders its numbers, the older flat shape still
renders, an absent fit says so rather than showing an empty table, and every stored swept run's
report renders the fit it carries. The first is checked non-vacuously — the old renderer reinstated
against the new test reproduces the dashed table and is caught.

## The dimension column carried two different numbers

Inspecting the dimension-160 report rather than its numbers showed adjacent rows of one table
disagreeing about the size of the lattice:

```
| primal_usvp | 50 | 161 | measured               |
| primal_usvp | 60 | 228 | not run — see section 6 |
| dual        | 80 |  93 | not run — see section 6 |
```

The lattice does not grow when the block size changes. The points that ran reported ``basis.nrows``;
the points the **time guard** refused recomputed the dimension as ``instance.m + instance.nu + 1``.
Section 6's anomaly text inherited it — *"dimension 228: the model predicts success at 88"* —
comparing a correct model prediction against a lattice the attack never built.

**228 is not a typo; it is the dimension of the lattice you get if the normal form is skipped.** The
project's premise is that this lattice contains no short vector and is therefore the wrong thing to
attack. The refusals were describing it, in the same column as the points that had correctly built
the normal form. And it is off by exactly ``nu``, so it grows with the instance — at dimension 160 it
was a 42 % error.

The correct width was already in the caller's hand: the refusal sits inside the block-size loop,
which holds the prepared basis. ``not_run`` now takes **that basis** rather than the instance, so a
second formula cannot be written at the call site. The comparison's dimension came from the same
wrong expression and is now ``lattice_widths_by_family``:

| family | lattice it reduces | width |
|---|---|---|
| ``primal_usvp`` | normal-form q-ary lattice, embedded | ``nf.m + nf.n + 1`` |
| ``dual`` | the dual of that lattice | ``nf.m`` |

**Two families, two lattices, two dimensions** — the same "one column, one meaning" rule, and the
reason a single number for both was wrong for at least one of them whatever value was chosen.

The identity that makes any of this checkable: normalising consumes ``nu`` samples and *adds* ``nu``
unknowns, so ``nf.m + nf.n == instance.m`` exactly. ``instance.m + 1`` and ``nf.m + nf.n + 1`` are
therefore the same number — but only one of the two expressions says which lattice it means, and
only one covers the dual.

Guarded by two tests that pin each width against the basis the corresponding attack actually
constructs, rather than against the formula — a formula checked against itself is what produced this.

## The re-run disagreed with the first sweep, and the disagreement is the finding

Re-running the sweep to correct the dimension labels — same config, same seed, same instance —
produced a **different result at dimension 80**. The instance is byte-identical (`instance` blocks
compare equal, seed 20260913), the block size is identical, and the two runs disagree completely:

| | block size 10 | minimum |
|---|---|---|
| first sweep | root-Hermite **3.5551**, did not recover | 20 (found at 1.63 s) |
| re-run | root-Hermite **1.2233**, recovered | 10 |

Two reductions of the same basis at the same block size returned different lattices. That is not
noise around a measurement; it is the absence of a measurement.

### The cause, measured

`scripts/determinism_probe.py` runs one reduction per process, so the axis under test is the one the
question is about. Eight processes, dimension 80, block size 10, identical instance and seed:

```
threads=1   3.11695792   3.11695792   3.11695792   3.11695792     <- four processes, one value
threads=4   3.78538167   3.55510025   1.22330782   3.55510025     <- four processes, three values
```

At one thread the reduction is bit-identical across processes. At four it is not, and **one of the
four draws recovered the planted vector while the other three did not.** The two sweeps' recorded
values are both in that set: `1.22330782` is the re-run's, `3.55510025` is the first sweep's. The
embedding factor was 3 in all eight runs, which excludes the calibration as a cause — it uses LLL,
and LLL is deterministic.

Two consequences beyond the reproducibility itself:

**The dimension-80 minimum is not a number.** It is 10 or 20 depending on the draw. Anything fitted
across the sweep inherits that.

**The time guard's refusals are an artefact of the same setting.** Four threads is not faster
everywhere: at dimension 80, block size 10 it cost **32.1 s against 10.4 s** at one thread — three
times slower, not faster. The guard at dimension 160 projected from a 132.8 s measurement at block
size 50 and refused everything above it, on a machine setting that made that point more expensive
than it needed to be. The "two independent routes agreeing at β ≈ 75" is therefore weaker than it
read: both routes ran through the same setting.

**But the trade reverses, and the first version of this note got that wrong.** It said one thread
was also the faster setting "across the whole configured range", generalising from a block-size-10
measurement. The clean one-thread sweep falsified it: d130 went from 120 s to **595 s**. Per
dimension against the four-thread sweep — d40 1.1×, d60 0.7×, d80 1.0×, d100 1.9×, d130 5.0×. One
thread wins at small block sizes and loses badly at large ones, which is where the sweep spends its
cost. The reproducibility requirement is still the reason to choose it; it is not a free win, and
the higher run time is the price.

### The cause was already written down in this repository

`engines/g6k_sieve_engine.py` says, of the engine the config puts first in its preference list:

> **And four threads costs reproducibility.** Measured here: with ``threads=1`` two runs at the same
> seed return bit-identical bases; with ``threads=4`` they do not.

`config/default_experiment.yaml` sets `threads: 4`. The project measured the trade, chose speed, and
**did not carry the consequence to where the numbers are reported.** The sweep's table of minima
reads as five measurements; each is one draw. The growth fit — slope 0.598, R² 0.929 — is a fit to
draws, and the R² is measuring their scatter as much as the relationship.

Three things let that happen, and each is a small gap rather than a wrong idea:

1. **The engine records the thread count; the attack record dropped it.** `ReducedBasisResult`
   carries `engine` and `threads` and reports them honestly — `FpylllBKZEngine` reports 1 because it
   genuinely is single-threaded, and it ignores the argument on purpose. But `PrimalAttackResult`
   carried neither, so the pipeline's attack dicts held only the block size and the wall clock. A
   draw and a measurement became the same row.
2. **Cross-check 7 could not see it.** It is named *"a run is reproducible from its own record"* and
   its body re-derives seeds from a root — arithmetic on a hash. It never runs a reduction. It
   certified a property it was structurally unable to observe, and passed throughout.
3. **The report had nowhere to say it.** Section 3 had no engine column, so the reader had no way to
   tell which engine produced a row, let alone at what thread count.

### What changed

`PrimalAttackResult` now carries `threads`, populated from the *reduction outcome* rather than from
the engine — the count that ran, not the count requested, which is the same rule
`ReducedBasisResult` already followed. `engine` is carried through the pipeline instead of dropped.
Section 3 gained an `engine` column and states, where it applies, that points above one thread are
single draws. Cross-check 7 was split: the seed bookkeeping keeps a name that describes what it
tests, and a new `7b` asserts the reduction half — one thread is bit-reproducible, and every
recorded point says what produced it.

**A note on what this does not fix.** The dimension-80 disagreement is a *result about the sweep*,
not a bug to be patched away: at four threads the number genuinely is a draw. One thread is chosen
because it is reproducible, and that is a choice about what a sweep is for — a fit for a security
estimate needs reproducible points, and it pays for them in wall clock at the high end. The trade is
recorded in the config beside the setting rather than buried here.

## State

The sweep is the first exercise of the fit against real multi-dimension data, and it did not survive
contact unchanged. That is the outcome the milestone was for: the fit was green in every test and
wrong in its first real use, which is exactly the class of defect the project's cross-checks exist to
catch and which a synthetic frame with a known slope structurally cannot.

**The results tree on disk is not fit to draw a conclusion from, and this is the state it is in.**

| runs | written by | dimensions | engine recorded |
|---|---|---|---|
| d40, d60, d80 | the first re-run | correct | no |
| d100, d130 | the second re-run | correct | no |
| **d160** | **the original sweep** | **still 228** | no |

Six runs, three code versions, and a dimension-160 record that still carries the defect the
re-run existed to fix — the second sweep was stopped at the thread-count finding before it reached
that point. None of the six records which engine or thread count produced it.

Re-running is the only way to a coherent record, and it should be done at **`threads: 1`**. That is
not only the reproducible setting: on the measured evidence it is also the faster one across the
whole configured range, because four threads costs 3.4–4.8× at block size 10 where the low-dimension
minima live, and its 1.6–2.1× advantage only appears at block sizes 80–90, which this sweep never
reached. The config's stated rationale — *"the interesting runs are the large-block-size ones, so the
default is 4"* — is inverted for the dimension range actually being swept.

The fit this note has quoted throughout (slope 0.598, R² 0.929, β ≈ 74.7 at dimension 160) is a fit
across the six mixed-version runs above, three of whose points are single draws. It should be read as
a shape rather than as a number, and re-derived after the re-run.
