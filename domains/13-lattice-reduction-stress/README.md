# 13 — Lattice reduction under stress

A CPU-only system that takes a QLWR parameter set, builds the corresponding lattice, and runs
**real** classical lattice reduction against it — BKZ through fpylll, sieving through G6K — then
sets what it measured beside the analytic cost models the NIST PQC process uses, through the
lattice estimator.

**What it establishes.** Three things, and the first two are about this domain's own earlier
numbers.

1. *Reduction really runs, and where it stops is measurable.* Across a dimension sweep the primal
   uSVP attack recovered the planted vector at minimum block sizes **10, 10, 30, 40, 70** at
   dimensions 40, 60, 80, 100, 130, and at **dimension 160 it found no minimum anywhere in the
   configured block-size range** — a refusal the sweep records rather than smooths over.
2. *A green test suite can sit on top of wrong numbers, and here it did.* A completion audit added
   tests whose failing cases were pinned one defect at a time; five of the defects had changed
   recorded figures (§4). The most consequential: **the engine's "root Hermite factor" was never
   rooted**, and **every `results/` directory written before 2026-09-20 records the un-rooted value
   under the key `root_hermite_factor`** and under a report column headed `root-Hermite`.
3. *The record's category table is not a lattice cost, and saying so changes what a comparison
   means.* Its 83 / 100 / 116 / 148 log₂ gates decode as key bits ÷ 2 plus log₂ gates per AES
   evaluation — **NIST category floors from Grover key search on AES**, not attack costs against a
   lattice. Set beside the estimator, all six deployed ML-KEM and ML-DSA parameter sets clear their
   floor; **ML-KEM-512 sits at about 2^107.6 quantum core-SVP, below the 2^128 budget** (§5).

**What it does not establish.** It cannot attack the production parameter set and does not claim to.
At ν = 256 the uSVP dimension is 609 and the largest lattice ever reduced here is **161**. Every
production figure in this domain is a cost model's output with no lattice built and no reduction
run, labelled `extrapolated` in the type system rather than by convention. And **G6K is not
reproducible above one thread**, so `engine.threads` is 1 and any figure produced at four threads is
a single draw rather than a measurement (§3).

---

## 1. How to read this domain

| Order | File | What it is |
|---|---|---|
| 1 | this file | what was measured, the defects that moved recorded numbers, the stop point, the limits |
| 2 | `src/qlwr_lattice_stress/protocols.py` | the interface freeze: the four provenances and the guards that keep them apart |
| 3 | `src/qlwr_lattice_stress/problem/`, `lattice/` | the instance type, the normal form, the q-ary lattice, the primal embedding |
| 4 | `src/qlwr_lattice_stress/engines/` | the fpylll BKZ engine and the G6K sieve engine, and the selector between them |
| 5 | `src/qlwr_lattice_stress/analysis/`, `reporting/` | the Hermite routes, the estimator comparison, the growth fit, the report generator |
| 6 | `notes/10-test-completion-audit.md` | the defect-by-defect audit record — read this before any stored figure |
| 7 | `notes/09-scaling-and-the-sweep.md` | the sweep, the fit that had to be replaced, and the thread-count finding |
| 8 | `notes/10-production-estimate.md` | the stop point: what crossing it produced, and the two sample readings |
| 9 | `results/infra-2026-09-21/report.md` | the estimator beside the record's category table |
| 10 | `results/synthetic_scaled-d*/` | the six swept runs: `config.yaml`, `metrics.json`, `report.md`, `figures/` |
| 11 | `VERIFICATION.md` | the re-run record: commands, environment, observed counts |

Every run directory carries its own `config.yaml`, so a run is reproducible from the directory it
produced rather than from a reconstructed command line.

---

## 2. What is measured, and what is only modelled

The separation is enforced in the type system rather than by convention: every result carries a
`provenance`, the report renders each under its own heading, and `estimate()` refuses to relabel a
non-same-scale parameter set as same-scale.

| provenance | what it means | where it appears |
|---|---|---|
| measured | a lattice was built and reduced at that size | the sweep's block-size minima, the Hermite factors, the wall clocks |
| same-scale estimate | the estimator run at the dimension that was actually attacked | `estimator_same_scale` in every `metrics.json` |
| extrapolated | a fit evaluated outside the measured range, or the estimator at production size | the growth fit's second half, and every production figure |
| not run | a point that was refused, with the reason | the time-guard refusals, the inapplicable dual attack |

**The sweep, measured.** Seed 20260913, one thread, G6K:

| dimension | ν | minimum block size that recovered the planted vector |
|---:|---:|---|
| 40 | 17 | 10 |
| 60 | 25 | 10 |
| 80 | 34 | 30 |
| 100 | 42 | 40 |
| 130 | 55 | 70 |
| **160** | **67** | **none found in the configured range** |

Fitted across the five dimensions that reached a minimum — required block size against lattice
dimension — slope **0.6926**, intercept −24.795, **R² 0.9440**. Evaluated at dimension 160 that fit
predicts block size **86.02**, and core-SVP at c = 0.292 puts that at log₂ 25.12 operations. The fit
is the *measured* step; applying core-SVP afterwards is the *extrapolated* step, and the two are
separately labelled so a reader can reject the second without rejecting the first.

Two things limit that fit, and both are recorded rather than argued away. The configured block-size
grid has step 10, so the measured threshold is quantised and part of the apparent growth is the
quantisation. And the dual attack does not apply at these scales at all: the band `‖y‖₁·B` covers
the whole residue space, so the shortest reduced dual vector is far above the budget. That is
recorded as *not run with a reason*, which is a different statement from a high cost.

---

## 3. One thread, because four is not a measurement

`scripts/determinism_probe.py` runs one reduction per process. Eight processes, dimension 80, block
size 10, identical instance and seed:

```
threads=1   3.11695792   3.11695792   3.11695792   3.11695792     <- four processes, one value
threads=4   3.78538167   3.55510025   1.22330782   3.55510025     <- four processes, three values
```

At one thread the reduction is bit-identical across processes. At four it is not — and **one of the
four draws recovered the planted vector while the other three did not**. Two sweeps of the same
instance at the same block size had disagreed completely (root-Hermite 3.5551 and no recovery
against 1.2233 and recovery); both of those values are in the set above. The embedding factor was 3
in all eight runs, which excludes the calibration as a cause, because it uses LLL and LLL is
deterministic.

So `engine.threads` is **1** everywhere, and three consequences are carried rather than buried:

- **The dimension-80 minimum is not a number at four threads.** It is 10 or 20 depending on the
  draw, and anything fitted across the sweep inherits that.
- **One thread is not free.** It is faster at small block sizes and loses badly at large ones: the
  clean one-thread sweep took dimension 130 from 120 s to **595 s**, a factor of 5.0. Reproducibility
  is the reason to choose it; speed is not.
- **The attack record now carries what produced it.** `PrimalAttackResult` carries `engine` and
  `threads`, populated from the reduction outcome rather than from the engine, and the report has an
  `engine` column. Before that change a draw and a measurement were the same row.

---

## 4. Defects that changed recorded numbers

A completion audit added test files whose failing tests were `xfail(strict=True)`, one marker per
defect, each naming a file and a line. **None of these defects raised; each produced a plausible
record.** All markers are now removed.

| defect | where | what it did | fix |
|---|---|---|---|
| **`root_hermite_factor` was never rooted** | `engines/base_engine.py` | it returned `‖b₁‖ / det^(1/d)` — the Hermite factor with **no `d`-th root** — and the primal attack and the pipeline copied it unchanged. At dimension 61 a stored run says ≈ **1.0117** where the metric the design document defines is ≈ **1.0002** | the `d`-th root is taken. The report column printed four significant digits, which renders every rooted value as `1`; it prints seven now |
| **both Hermite routes floored the leading norm** | `analysis/hermite_factor.py` | `math.isqrt` floored the norm, so `[[1,1],[-1,1]]` reported **0.8409** for a factor of exactly 1 — **from both routes, in agreement.** Two independent routes agreeing on the same wrong answer is the failure mode a cross-check is supposed to exclude | the norm is no longer floored |
| **the negative control was a planted instance** | `problem/qlwr_instance.py` | `random_lattice_control` built its samples *from a secret*, exactly as `synthetic_scaled` does, under a different label. The primal attack recovered it at block size 2. The one experiment that could show the attack firing on nothing **could not fail to fire** | the instance type gained `control_samples`: the public samples are drawn uniformly over the values a sample can take, a secret is still recorded and explains nothing, and `describe()` records `planted: false` |
| **the production estimate was labelled `theoretical_same_scale`** | the estimator path | **nothing was attacked at that scale.** A model output at ν = 256 carried the label a measurement at the attacked dimension carries | `ParameterSet` carries a `provenance`; `production_parameter_set` sets `extrapolated`, and `estimate()` refuses to relabel it |
| **the SIS estimator path returned all-`None`** | `_estimate_sis` | it read the cost with `getattr(lattice, "rop", None)`, but the estimator's `Cost` is a dict subclass, so **ML-DSA-2/3/5 all reported `None`** | read through `_cost_field`; they report 2^152.2, 2^211.5 and 2^288.2 |

**The consequence that reaches outside the source tree.** The stored result directories are **not
rewritten** — they are the evidence the earlier notes cite. So: *every `results/` directory written
before 2026-09-20 carries the un-rooted factor under the name `root_hermite_factor`.* The six swept
runs here are dated 2026-09-14 and are in that set. To compare a stored figure with a new one, take
the stored figure to the power `1/d`, where `d` is that row's `dimension` column. Taking a root is
monotone, so arguments that turned on stored values being *distinct* — the thread-count table in §3
among them — are untouched.

Three further defects from the same audit did not move a published number but are worth naming,
because each was a self-consistent object that was nonetheless wrong: the pipeline read only the
head of its engine preference list while the shipped configuration promised a logged fallback;
`engine.ram_budget_gb`, `output.formats`, `engine.gauss_crossover`, `attack.search_beyond_prediction`
and `instance.nu_over_m` were validated or read nowhere; and the report generator kept reading a
flat `scaling` shape after the pipeline had started writing a nested one, so every swept run's
extrapolation section rendered as a **table of dashes while 310 tests passed**. A table of dashes is
not ambiguous, it is misleading: it reads as "no fit was produced", which is a claim about the run.

---

## 5. The record's category table, and the estimator beside it

`results/infra-2026-09-21/`, generated 2026-09-20T22:17:14Z. **Everything in this section is
theoretical: no lattice was built and none was reduced.** Core-SVP under-counts an attack's cost and
the record's floors are gate counts, so every comparison below errs toward the attacker.

The record states attack costs per NIST category as log₂ gates. Decoded:

| category | record, log₂ gates | decodes as |
|---|---|---|
| 1 | 83 | 64 + 19 (Grover on AES-128) |
| 2 | 100 | — |
| 3 | 116 | 96 + 20 (Grover on AES-192) |
| 5 | 148 | 128 + 20 (Grover on AES-256) |

That is **key bits ÷ 2 plus log₂ gates per AES evaluation** — a category floor from Grover key
search on a block cipher. It is not a lattice attack cost, and a lattice figure and this table are
therefore not the same quantity.

Estimator cost of the best known lattice attack at full scale, cost models ADPS16
classical/quantum with the estimator's default shape, SIS default, estimator revision `53da5982`:

| scheme | cat | β uSVP | β dual | classical log₂ | quantum log₂ | record floor | margin | ≥ floor | ≥ 2^128 budget | judged on |
|---|---:|---:|---:|---|---|---:|---|---|---|---|
| ML-KEM-512 | 1 | 406 | 424 | 118.55 | **107.59** | 83 | 24.59 | yes | **no** | quantum core-SVP |
| ML-KEM-768 | 3 | 624 | 648 | 182.21 | 165.36 | 116 | 49.36 | yes | yes | quantum core-SVP |
| ML-KEM-1024 | 5 | 874 | 904 | 255.21 | 231.61 | 148 | 83.61 | yes | yes | quantum core-SVP |
| ML-DSA-44 | 2 | — | — | 152.16 | — | 100 | 52.16 | yes | yes | classical only — this estimator path reports no quantum figure |
| ML-DSA-65 | 3 | — | — | 211.49 | — | 116 | 95.49 | yes | yes | classical only — as above |
| ML-DSA-87 | 5 | — | — | 288.21 | — | 148 | 140.21 | yes | yes | classical only — as above |

**All six clear their category floor.** The one row that does not clear the 2^128 budget is
ML-KEM-512, at about 2^107.6 quantum core-SVP. The three ML-DSA rows are judged on a classical
figure only, because this estimator path returns no quantum cost for them — which is a gap in the
comparison, not a claim that none exists.

---

## 6. The stop point, crossed deliberately and only for the estimator

Every milestone before this one validated the machinery against synthetic instances and *published*
parameter sets. The recorded QLWR parameters — ν = 256, q = 2¹⁶, p = 2⁸ — are now in this domain as
cited constants and are fed to the cost model. **That is the whole of the crossing: no lattice is
built from them and no reduction is run on them.** At ν = 256 the uSVP dimension is 609; the largest
lattice reduced here is 161. Where the boundary still holds it is machine-checked: the configuration
schema cannot express the production instance, no source file names the read-only research tree, and
a test asserts both.

The record gives two sample readings and does not say which governs, so both are reported:

| quantity | `rows` (m = 608) | `exposure` (m = 672,352) |
|---|---|---|
| block size, `primal_usvp` | 426 | 368 |
| log₂ operations, classical, minimum over models | **124.39** | **107.46** |
| log₂ operations, quantum sieving, minimum over models | 112.89 | 97.52 |
| model attaining the minimum | `primal_usvp` | `primal_usvp` |

Both are pure core-SVP at the block size beside them — 426 × 0.292 = 124.39 and 368 × 0.292 =
107.46 — so the reduction cost is the whole cost, with no repetition factor on top. **More samples
make the attack cheaper**, which is the opposite of the naive reading: the estimator optimises the
lattice dimension it uses, so 608 samples is a constraint on the attacker rather than a protection
from one.

Three measured facts that bound how any of this may be quoted:

- **The choice between readings has a threshold, not two options.** The primal cost is a step
  function of the sample count that **reaches its floor at 791** and is flat above it, so every count
  from 791 to 672,352 returns the identical estimate. 124.39 follows from the record as written; the
  107.46 figure carries the premise that some single secret accumulates 791 rows.
- **The dual column of the `rows` reading is not an optimum and must not be quoted as a cost.** The
  estimator caps its dual block-size search at the samples left after the normal form, so at 352
  samples it returns β = 351 with the cost still falling; the model's own minimum is at β = 456 and
  **116 bits lower**. The headline is unaffected — `primal_usvp` is the minimum over models under
  both readings.
- **An infinite cost is the model declining to answer, not a large number.** Measured applicability
  thresholds at ν = 256: `usvp` applies from **532** samples, `dual` from **536**. The `rows`
  reading clears both, by 76 and 72 samples. An instance just below a threshold does not produce a
  high cost, it produces *no applicable attack*, and rendering those alike would be a false
  reassurance.

---

## 7. What this domain does not establish

- **No attack on the production parameter set.** Nothing at ν = 256 was built or reduced. §6 is a
  cost model's output.
- **No security claim from the estimator rows.** §5 is theoretical throughout, at core-SVP, which
  under-counts. It is a comparison of two analytic numbers, one of which (the category floor) is
  about AES rather than about lattices.
- **Stored figures from before 2026-09-20 are un-rooted.** §4. A reader who compares a stored
  `root_hermite_factor` with a freshly computed one without taking the `d`-th root will find a
  disagreement that is an artefact of the fix.
- **The growth fit is a shape, not a number.** Five points, a block-size grid of step 10, and a
  dimension that never reached a minimum. Its `R²` measures the scatter of quantised draws as much
  as it measures a relationship.
- **The memory model is not validated in either direction.** The hardware profiler's earlier claim
  that the model over-predicts by ≈ 15× was **withdrawn**: the footprint it compared against the
  model contains no sieve database — `Siever.db_size()` reports 500 at every block size and every
  tour count, and peak RSS is flat across five consecutive tours at β = 80 (123 → 124 MiB) where the
  model predicts a 258 MiB database. What survives is the confirmed bound: **112 MiB measured at
  β = 90 against M1's ≤ 141 MiB**, after subtracting the fixed **65 MiB** import cost every forked
  child pays. The per-entry constant is unmeasured, and `sieve_block_size_max: 80` rests on it.
- **The enumeration guard is a backstop, not a budget.** It under-predicts by about 19× — it
  projected 3 s for a run that took 58.6 s.
- **A lattice figure and the record's QPT-128 gate margins are not the same quantity**, and nothing
  here converts between them. Recomputing those margins from their own rows did find that Mode B's
  quoted +7.7 bits charges its proof-soundness row twice; charged once it is **8.081**, a difference
  of 0.412 bits in the conservative direction. The scope of that is **enumerated, not asserted**:
  the figure has three consumers, no threshold test reads it, and it never reaches the audit ledger,
  so no claim that consumes it is inflated by it. Mode B is research-only in any case; the deployed
  profile is B0.
- **No reduction was run by anything but this domain's own engines**, at one thread, on one host,
  under one seed schedule.
