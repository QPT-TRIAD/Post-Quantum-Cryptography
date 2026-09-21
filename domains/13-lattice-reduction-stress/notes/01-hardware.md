# Milestone 1 — hardware calibration

The plan carried a feasibility table derived from G6K's source constants. This milestone tested it,
and the table was wrong in one direction and the thread advice wrong in the other.

## What was measured

`scripts/profile_hardware.py`, 12 sieving points and 6 enumeration points, one process.

**G6K sieving** (`pump_n_jump_bkz_tour` on a q-ary basis of dimension `max(β+10, 60)`):

| β | t=1 | t=2 | t=4 | cumulative peak RSS |
|---:|---:|---:|---:|---:|
| 40 | 0.61 s | 0.72 s | 0.78 s | ≤97 MiB |
| 60 | 4.04 s | 4.07 s | 4.34 s | ≤106 MiB |
| 80 | 57.85 s | 39.18 s | **35.62 s** | ≤133 MiB |
| 90 | 404.59 s | 244.75 s | **193.18 s** | ≤231 MiB |

**fpylll BKZ** (enumeration, 2 tours, `AUTO_ABORT`):

| dimension | β=20 | β=30 | β=40 |
|---:|---:|---:|---:|
| 100 | 0.061 s | 0.227 s | 26.110 s |
| 160 | 0.275 s | 0.582 s | 58.638 s |

No point was refused: memory never approached the 6 GiB budget.

## Finding 1 — the memory model over-predicts by about an order of magnitude

> **WITHDRAWN — see "Post-fix re-run" at the end of this note.** The table below compares a predicted
> *database* size against a measured footprint that, on later measurement, **contains no sieve
> database**: `Siever.db_size()` reports 500 at every block size and every tour count, and peak RSS is
> flat across five consecutive β = 80 tours where the model predicts a 258 MiB database. The bound
> this note reports is real — the fork-fix re-run measures 112 MiB at β = 90 against ≤ 141 MiB here —
> but the *ratio* is not a statement about the model in either direction. **The model is now
> re-measured at one dimension with a real database in the footprint, and the sign is the opposite
> of this finding's: it under-predicts by ~1.3×, not over-predicts by ~15×** — see "Resolved:"
> below. Kept as written because the reasoning that produced it is the record of how the bound was
> obtained.

The plan's model was `db_size(β) = 3.2 · (4/3)^(β/2)` entries × ~850 B/entry × 2.0 safety,
giving 516 MiB at β=80 and 2174 MiB at β=90. Against the cumulative peak:

| β | predicted | cumulative peak | true footprint (peak − ~90 MiB import baseline) | over-prediction |
|---:|---:|---:|---:|---:|
| 80 | 516 MiB | ≤133 MiB | ≤43 MiB | **~12×** |
| 90 | 2174 MiB | ≤231 MiB | ≤141 MiB | **~15×** |

Two conclusions, and the second matters more than the first.

The per-entry cost is far below 850 B, so **the safety factor must come down**. But the deeper point
is that **memory is not the binding constraint at all**: β=90 peaks at 231 MiB against 7.5 GiB
available. The plan's `sieve_block_size_max: 80` was set by a memory fear that the measurement does
not support. What actually limits the sweep is **time** — β=90 costs 193 s at the best thread count,
and β=100 is five to ten times that.

So the cap should be a *time* budget, not a memory one, and the memory check should stay as a
correctness guard against a genuine runaway rather than as the thing that sets the ceiling.

## Finding 2 — the thread recommendation was backwards where it matters

At β=40 and 60, one thread is fastest and four is slowest — consistent with 2 P-cores and 8 E-cores.
At β=80, four threads is 1.6× faster than one. At β=90 it is **2.1× faster**.

The crossover is real and has a plausible shape: at small β each tour is short enough that
synchronisation dominates, while at large β the sieving database is big enough that the E-cores
contribute more than they cost. The plan's D5 ("2 threads, because 2 P-cores") holds only in the
regime nobody cares about — the interesting runs are the large-β ones.

**Default `threads: 4`**, with the measurement recorded. One thread remains available and is faster
if a great many small-β runs are ever wanted.

## Finding 3 — a defect in this profiler, recorded rather than hidden

**`peak_rss_delta_from_before` is not a measurement.** `ru_maxrss` is monotonic per process, and all
twelve configurations ran in one process, so the peak reached by β=90 t=1 set a floor every later
configuration inherited. The deltas returned as 5.2, 2.8, 0.0, 24.3, 0.0, 82.9, 6.4, 8.9 MiB —
noise, and β=90 t=2 reporting *less* than t=1 is physically impossible.

Only the **cumulative** peak is meaningful, and only as an upper bound: it says the footprint at
β=90 is at most 231 MiB, not that it is 231 MiB. That is enough to falsify the model — an
over-prediction of ~15× is falsified by any bound four times smaller — but a per-configuration
figure needs a fork per configuration.

**Fix before the model's constant is finalised:** run each configuration in a child process and
read the child's `ru_maxrss`, which then measures that configuration's own peak. Until then the
constant below is a bound-derived estimate and is marked as such.

## What this changes

| setting | plan | now | why |
|---|---|---|---|
| `threads` | 2 | **4** | measured 2.1× faster at β=90; the small-β regime where 1 wins is not the interesting one. **Unaffected by the withdrawal below** — it rests on wall-clock, which was measured correctly. |
| memory safety factor | ×2.0 on ~850 B/entry | **unchanged at ×2.0 — and see below** | the "~1/12 of that" this row used to recommend is **withdrawn**. It came from the same invalid comparison as Finding 1. With a database actually in the footprint, ~850 B/entry *under*-states the cost and ×2.0 does not cover it. |
| `sieve_block_size_max` | 80 (memory-driven) | **80 — retained, now provisional-by-default** | see the scope note below. The memory reasoning that set it is withdrawn; the cap stays because nothing has replaced it. |
| `ram_budget_gb` | 6.0 | 6.0, unchanged | still the correct refusal threshold for a genuine runaway, and it never fired |

### What the refusal gate is actually protecting against now

This needs saying explicitly, because a reader skimming M1's history would reasonably conclude the
cap is still empirically grounded. It is not, and the change is in kind rather than in degree:

* **Before the fork fix:** *"we predict β ≥ 90 needs more memory than we budgeted"* — a claim resting
  on the plan's model. **That reasoning is withdrawn.**
* **After the fork fix:** *"we no longer know what β ≥ 90 costs in memory."* The cap stays because
  **nothing has replaced the withdrawn estimate**, not because a measurement says it is still needed.

The later re-measurement (below) restores a *direction* — the model under-predicts rather than
over-predicts, so the cap is if anything conservative — but it is a single dimension, and it is not
yet a basis for moving a safety limit. **The honest current state is provisional-by-default: the gate
is standing in the absence of evidence rather than on the strength of it.**

## What is still uncertain

- **The true per-configuration footprint.** Bounded, not measured — see finding 3.
- **Where time stops being acceptable.** β=90 costs ~3 min at best; the extrapolation to β=100 is
  five-to-ten times that on the strength of two points, which is not a fit.
- **Whether 4 threads stays optimal at β=100+.** The trend is favourable but the measurement stops
  at 90.
- **The enumeration guard's accuracy.** It projected `d=160 β=40` at ~3 s from the β=30 point and
  the run took 58.6 s — so the guard underestimates by ~19× and is a backstop, not a budget. It
  still served its purpose (the earlier unbounded sweep would have run for hours) but should not be
  trusted to be tight.

---

## Post-fix re-run: the RSS defect is fixed, and the model's memory question got smaller

> Superseded in part by "Resolved: `db_size()` is a real accessor" below, which came after this
> section was written. Its conclusion that the per-entry constant "remains unmeasured" was right
> when written and is no longer true: the entry-count formula is now confirmed exactly at one
> dimension, and the per-entry cost is measured there too. Read the two together.

The fork-per-configuration fix described in Finding 3 was made and the profile re-run. It worked —
and it showed that **the quantity being measured is not the sieve database the model describes**,
which invalidates the comparison Finding 1 draws.

**The fix.** `profile_sieve` now forks a fresh process per `(block size, threads)` and reads that
child's `ru_maxrss`, so the high-water mark is the configuration's own. A second defect surfaced
immediately: each child pays a fixed **65 MiB** import cost (fpylll + G6K), which at β = 60 exceeds
the 29 MiB database the model predicts. Measured separately by a child that only imports, and
subtracted; the reported figure is `peak_rss_bytes_sieve_only`. The old contaminated deltas are kept
in `results/hardware_profile_single_process.json` as evidence — 5.4 MB, 2.8 MB, **8 KB**, 151 KB,
3.5 MB, 25 MB, **0**.

**What it confirmed.** M1's bound was a bound and the measurement now sits under it: β = 90 t = 1 is
**112 MiB** sieve-only against M1's *≤ 141 MiB*. Per-configuration footprint across the range:
β = 40 → 8 MiB, 60 → 13, 80 → 36, 90 → 112.

**What it invalidated.** `Siever.db_size()` reports **500 at every block size, at every tour count,
and never grows** — from 0 at construction to 500 after the first tour, then constant. Two checks:

| driven | result |
|---|---|
| β = 60, 80, 90, one tour each | `db_size` = 500 in all three |
| β = 80, **five** consecutive tours | `db_size` = 500 each time; peak RSS 123 → 124 MiB |

The model's `db_size(β)` spans 17,919 → 1,340,890 entries over β = 60 → 90, which at ~850 B/entry is
15 MiB → 1.1 GiB. If the database were filling, five tours at β = 80 would drive RSS toward the
predicted **258 MiB**; it does not move at all. **The database the model describes is not present in
the footprint.**

**So Finding 1's "~15× over-prediction" is not established.** It compares a predicted database size
against a measured footprint that contains no database. This note's own table is careful — it says
*bound*, and it flags the fork defect — but the ratio it reports is the same comparison, and the
measured side is the tour's working set, not the sieving database. The corrected statement is that
**the memory model's per-entry constant is unmeasured**, in either direction, and the plan's
`sieve_block_size_max: 80` refusal — which exists to keep a β ≥ 100 run off a nearly-full swap file —
rests on that unmeasured constant.

**What would settle it, and what this note does not claim.** Either (a) drive G6K to a saturated
database by an explicit grow-and-sieve and watch where RSS plateaus, or (b) read `db_size()`'s
definition in the G6K source to establish what it reports. Until one of those is done, the safe
reading of the per-configuration numbers is: *they are the real footprint of a BKZ tour at that block
size, and they are a floor on any run that fills the database.* The refusal threshold should not be
loosened on the strength of them.

### Resolved: `db_size()` is a real accessor, and the tour was the wrong instrumentation point

The flat 500 is not a G6K cap and not a broken accessor. `kernel/siever.h:550` —
`size_t db_size() const { return db.size(); }` — is genuine database occupancy, and the docstring at
`g6k/siever.pyx:425` shows it returning 4252 in its own worked example. The problem was **where the
reading was taken.**

`pump_n_jump_bkz_tour` (`g6k/algorithms/bkz.py:97`) opens with **`g6k.shrink_db(0)`** (line 120), and
its index list is built so the *last* group runs at the **smallest** block size (line 133). So the
database is emptied at the start of a tour and left small at the end of it. The 500 recorded after
every tour is the aftermath, not the peak — and it was never going to scale with β, which is why it
did not.

Driving the Siever the way its own docstring does — `initialize_local(...)`, then `g(alg="gauss")`,
then `g()` — the database fills:

| sieving dimension | model `3.2·(4/3)^(d/2)` | measured `db_size()` | ratio |
|---:|---:|---:|---:|
| 70 | **75,510.1** | **75,510** | **1.00000** |

The model's database-size formula is **exactly right** — reproduced to five significant figures by the
real database. That formula was never in question; the earlier section's claim that it was "unmeasured
in either direction" was itself too strong, and is corrected here rather than left standing (this
note has now been wrong in both directions about the same constant, which is worth saying plainly).

What the measurement does show is a **different** constant being off, in the **opposite** direction to
Finding 1:

| quantity | model assumes | measured |
|---|---|---|
| entries at d = 70 | 75,510 | 75,510 ✓ |
| bytes per entry | 850 × 2.0 safety = **1,700** | **≈ 2,208** |

Peak RSS minus the process baseline was 159 MiB for 75,510 entries. So the model's ~850 B/entry
understates the real cost, and its ×2.0 safety factor does not cover the gap: the effective figure is
about **×2.6**, not ×2.0, and the model therefore **under-predicts by roughly 1.3×** at this scale.

**Finding 1 had the sign backwards.** It claimed a ~15× *over*-prediction; the truth at the one point
now measured cleanly is a ~1.3× *under*-prediction. The original comparison was invalid because the
footprint contained no database, and with a database in it the direction reverses.
