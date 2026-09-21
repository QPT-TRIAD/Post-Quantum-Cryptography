# synthetic_scaled-d100-s20260913


**Scope boundary.** This system cannot run BKZ or sieving at the full production dimension and modulus — reduction cost grows exponentially in the block size needed, which is by design what makes the scheme secure. What it *can* do is run the actual algorithms exactly, correctly and completely at scaled-down dimensions, measure real empirical hardness there, and extrapolate to the full parameter set using the same cost models the NIST PQC process uses. **Measured and extrapolated numbers are never blended.** Nothing here is a security claim about the production parameters.

## 2. Tested parameters and dimensions

| quantity | value |
|---|---|
| instance source | synthetic_scaled |
| secret dimension (nu) | 42 |
| modulus (q_l) | 65536 |
| rounding modulus (p) | 256 |
| rows (m) | 100 |
| rounding ratio q_l/p | 256 |
| noise bound | 128 |
| noise interval | [-128, 127] |
| equivalent sigma | 73.9 |
| bit-shift rounding | True |
| q-ary lattice dimension | 100 |
| uSVP lattice dimension | 101 |
| seed | 20260913 |

## 3. Empirical results — measured

Everything in this section was executed on this machine.

| family | block size | dimension | engine | provenance | recovered | wall clock (s) | root-Hermite |
|---|---|---|---|---|---|---|---|
| primal_usvp | 10 | 101 | g6k_sieve ×1 | measured | no | 10.84 | 5.923 |
| primal_usvp | 20 | 101 | g6k_sieve ×1 | measured | no | 4.412 | 4.392 |
| primal_usvp | 30 | 101 | g6k_sieve ×1 | measured | no | 7.426 | 3.784 |
| primal_usvp | 40 | 101 | g6k_sieve ×1 | measured | yes | 9.969 | 1.315 |
| dual | 58 | 58 | — | not run — see section 6 | no | 5.377 | — |

The **dimension** column is the width of the lattice *that family actually reduces*, which is not the same number for both: the primal attack embeds the normal-form q-ary lattice and adds one row and one column, while the dual attack reduces the dual of that lattice. Rows within a family share a dimension, because the lattice does not change when the block size does.


**Minimum successful block size by family**

| family | minimum block size |
|---|---|
| primal_usvp | 40 |
| dual | not reached |

## 4. Cost model at the same scale — theoretical, same scale

The estimator's prediction for **the same scaled instance that was attacked**. Comparing against a model evaluated at a different scale would measure the extrapolation rather than the physics.

| quantity | value |
|---|---|
| usvp block size | 44 |
| dual block size | 55 |
| log2 rop, usvp | 12.85 |
| log2 rop, dual | 18.92 |
| log2 rop, minimum over models (classical) | 12.85 |
| log2 rop, minimum over models (quantum) | 11.66 |
| model attaining the minimum | primal_usvp |
| estimator revision | 53da5982597709ba0fdf94ea37a84d822310fd84 |
| cost model | ADPS16(classical/quantum), estimator default shape |
| shape model | GSA |

## 5. Production-scale extrapolation — extrapolated — not measured

**Not measured.** Model outputs fitted to the scaled measurements and evaluated beyond them; they carry the model's assumptions.

| quantity | value |
|---|---|
| what was fitted | required block size against lattice dimension |
| slope (block sizes per unit dimension) | 0.6926 |
| intercept | -24.8 |
| R squared | 0.944 |
| dimensions fitted | 40–130  (5 points) |
| target dimension | 160 |
| predicted block size there | 86.02 |
| core-SVP log2 cost there | 25.12 |
| core-SVP constant c | 0.292 |

The first five rows are **measured** — the relationship a sweep can actually observe. The last four are **extrapolated**: the fit evaluated at a dimension beyond those fitted, and the core-SVP model applied at the resulting block size. The two steps are separate and separately labelled, so the extrapolation can be rejected without rejecting the measurement.


## 6. Anomalies

**Anomalies — a disagreement at this size is a result, not noise.**

- dimension 58: the dual attack recovered nothing anywhere in the swept block-size range, where the model predicts success at 55. Either the sweep did not reach far enough or the instance is harder than the model says.

## 7. Scope exclusions and contradictions carried forward

Findings this project recorded and **did not resolve**. They are listed here because a report without them reads as a clean result.

- The corpus requires **p prime** for public tracing (`security_proof_v1.3.md:101`) while the only recorded numeric parameter set uses **p = 2^8** (`research_qualification_v1.18.md:257`). Both are recorded; neither is chosen.
- The **sample-exposure count is ambiguous and large**: m = 608 rows versus an exposure of 672,352. Those are different sample counts to an attack, and a cost estimate is only meaningful alongside which reading it was made under.
- The cost model **does not apply below roughly 28 unknowns**, where the predicted block size approaches the lattice dimension and the model's cost figure is inapplicable rather than wrong. Measured boundary in notes/04.
- The estimator is **insensitive to both QLWR-specific deviations** — uniform versus Gaussian error, and power-of-two versus prime modulus — at every size tested. It cannot distinguish a QLWR instance from an LWE one at the same (n, q, m, sigma).
- The **primal and dual families diverge at this scale**: the primal attack reaches and the dual does not, for an arithmetic reason recorded in notes/06. Since the estimator reports the minimum over both, a run that exercised only the dual would conclude the instance was hard.
- `attack_lab_results_v1.51.md:7` states the QLWR-based construction *was refuted and replaced*, while `pqt.md:309-347` still defines QLWR as a live assumption. This tool does not resolve that and does not appear to.
