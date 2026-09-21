# Milestone 8–9 — the quality metric, the comparison, and the fit

## Cross-check 5 found a real bug, which is why it exists

The root-Hermite factor is computed two ways — an exact integer determinant by fraction-free
elimination, and `fpylll`'s Gram-Schmidt data. They disagreed by **8–26%**.

The cause: **`GSO.Mat.get_r(i, i)` returns the *squared* norm of the i-th Gram-Schmidt vector**, so
`prod(r_ii)` is the determinant *squared*. Measured on a 20-dimensional q-ary basis, the raw product
gave `log = 128.946` against an exact `log|det| = 64.473` — exactly double.

**The result was plausible in isolation.** It produced a root-Hermite factor of 0.937 where the
correct value is 1.018, and 0.937 is a perfectly believable number for a reduced basis. Nothing about
it looked wrong. Only the disagreement between two independent routes revealed it — which is the
entire argument for computing a quantity twice from different references, and the same class of bug
the sibling project hit when two layers each computed "the size" a different way and neither was
wrong alone.

After the fix the routes agree to **1e-14 relative or better**, against the 1e-9 the plan required.

## The GSA formula is refused outside its domain

`delta_0(beta) = (beta/(2*pi*e) * (pi*beta)^(1/beta))^(1/(2*(beta-1)))` returns **0.54 at beta = 2**
and values below 1 for every block size below about 40. That is not a prediction; it is the formula
leaving the regime it was derived for.

It is now **refused below block size 40** rather than clamped. Clamping to 1.0 would produce a number
that looks like a prediction, and `gsa_predicted_norm` would then return a norm no model supports.
Where it is valid it matches the literature: 1.0125 at `beta = 40` (against ~1.0128) and 1.00926 at
`beta = 100` (against ~1.0092).

## `delta < 1` is expected here, and my own assertion was wrong

I wrote a test asserting the achieved factor is at least 1, on the reasoning that a quality metric
cannot be better than perfect. It failed at `nu = 20` with **0.9980**.

The reasoning is right for a *generic* lattice and wrong for this one. The achieved factor is
`(||b1|| / det^(1/d))^(1/d)`, and the bound `delta >= 1` describes what reduction achieves on a
lattice whose shortest vector is typical. A lattice containing an **anomalously short vector** —
which is exactly what a uSVP instance is, by construction — gives a value below 1 whenever reduction
finds it.

So `delta < 1` is not a defect in the metric. It is a *signature* of the planted vector, and the
test now records that: measured 0.9980 at `nu = 20` against 1.0176 at `nu = 32`, both finite and
near 1, with the direction of the deviation carrying information the magnitude does not.

## The comparison names its anomalies, in the type

`compare_block_sizes` compares the measured threshold against the estimator's prediction **for the
same scaled instance**, which is what makes it a comparison of two accounts of one lattice rather
than of a measurement against an extrapolation.

Three outcomes, kept distinct because they call for different responses:

| case | outcome |
|---|---|
| within tolerance | no anomaly, `discrepancy` recorded |
| outside tolerance | **anomaly, named** — silence is enforced as a constructor failure |
| the model made no prediction | a `note`, **not** a discrepancy |

The third matters: where the estimator reports an infinite cost it has made no prediction to
disagree with, and inventing a large discrepancy to represent that would put a number into the
report that no measurement supports. `summarise_anomalies` keeps the two lists apart for the same
reason — "the model and the measurement disagree" and "the model produced nothing to compare" are
different claims.

## The fit refuses to look confident on thin evidence

Least-squares on `log2(cost) = c * beta + intercept`, exercised against a synthetic table with a
known slope — a fit validated only against real data cannot distinguish "the model holds" from "the
fit works".

**A fit needs at least three points.** Two points determine a line exactly, so the residual is zero
by construction and the fit cannot be contradicted by its own data; reporting `R^2 = 1.0` from two
points is the most confident possible statement from the least possible evidence.

The fitted domain travels with the model, and `predict_log2_cost` returns the value **tagged** as
`measured` or `extrapolated` so a consumer cannot label an extrapolation as a measurement without
discarding the tag deliberately — the same rule the reports are built on, moved into the analysis
layer where it cannot be lost on the way to a figure.

## State

285 tests pass. The analysis layer is complete: quality metric with two agreeing routes, comparison
with enforced anomaly reporting, and a fit that states its domain and its evidence.
