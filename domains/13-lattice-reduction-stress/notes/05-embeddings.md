# Milestone 6 — the dual lattice, and a rank condition the normal form was missing

## The dual lattice

`Lambda* = { y in Z^m : A^T y == 0 (mod q) }`, dimension `m`, determinant `q^n`. A basis is built
from the same pivot the normal form already selects: `n` modular rows `q * e_i`, plus `m - n` kernel
rows carrying `-(A2 A1^{-1})^T` on the pivots.

Verified: **both invariants hold across 4 sizes x 5 seeds**, with `|det| = q^n` exact (at `nu = 32`
that is a 129-digit integer — the check is exact integer arithmetic, not a tolerance).

The two checks are independent by construction, and each catches what the other cannot:

| check | what it verifies | what it misses alone |
|---|---|---|
| annihilation | each dual row is orthogonal to each primal sample row mod `q` — the definition | a basis that annihilates correctly but spans a sublattice |
| volume | `\|det D\| == q^n` exactly | rows that happen to give the right volume but are not in the dual |

## Finding — the normal form's pivot could leave a rank-deficient base

This is the substantive one, and it was found by the dual construction refusing to run.

`choose_invertible_pivot` selected `n` rows forming an invertible `A1` and treated the rest as `A2`.
Nothing required **`A2` to span**. But the transformed base is `A' = A2 A1^{-1}`, so `A'` has
exactly `A2`'s rank — and a pivot search that only constrains `A1` can leave a complement that does
not.

Measured at `nu = 4, m = 12`: **one seed in eight** produced `A'` of rank 3 where 4 was needed.

**Why this is the worst kind of defect here.** The relation `b' = A' x + e'` still holds. The
structural basis check still passes. `|det B| = q^m` still holds. Every check the project had
passes, while the lattice's short-vector structure is different and the planted vector is no longer
the object the attack recovers. It surfaced only because the dual lattice cannot be constructed at
all from a rank-deficient `A'` — one milestone later than it should have.

Fixed by requiring the complement to span, with restarts over row orderings. Verified: **48 of 48
draws across four sizes now give a full-rank `A'`**, against 47 of 48 before.

**The condition is a parameter, not a constant.** `dual_basis` deliberately passes
`require_complement_full_rank=False`, because it takes its pivot inside an *already-transformed*
base where the construction is valid whatever the remaining rows' rank — its determinant is `q^n`
either way. Requiring it there refused pivots that work, which is how the distinction was found.

## Finding — the calibration was verifying the wrong thing

`calibrate_embedding_factor` originally confirmed a candidate factor by asking whether a reduction
recovered the planted vector. That is asking for **the thing the calibration exists to make
possible**: at the sizes where the factor matters, LLL does not recover the planted vector, so the
verification failed for every candidate and reported "the instance may be too noisy at any factor".

The concern the factor actually addresses is narrower: at too small a factor the shortest vector is
`(0, ..., 0, p*M)` rather than the planted one. LLL is more than sufficient to surface a vector that
short, so it detects exactly that case and nothing else. The verification now asks that question.

Measured calibration, stable across seeds:

| nu | m | analytic bound | calibrated M | planted ‖v‖² | artifact at M | at M=1 |
|---:|---:|---:|---|---:|---:|---:|
| 20 | 48 | 2 | 3, 3, 3, 2, 2 | 276 008 | 768 | **256** |
| 32 | 76 | 3 | 3, 3, 3, 3, 3 | 442 345 | 768 | **256** |

At `M = 1` the artifact has norm 256 against a planted vector of norm ~665 — so the artifact is
shorter, the planted vector is not the shortest lattice vector, and the attack is meaningless. That
is the `M = 1` finding from M5, now reproduced by the calibration that exists to prevent it.

## A test that was asserting something false

`test_a_chosen_pivot_is_always_invertible_modulo_q` asserted that a pivot is always found. With the
complement condition required, some draws genuinely admit no valid split, and the correct behaviour
is to refuse and let the caller redraw. The test now asserts the property of a *returned* pivot and
treats `PivotNotFound` as a legitimate outcome — because "a pivot is always found" is not true, and
a test asserting it would have to be weakened later in a way that looks like a regression.

## State

253 tests pass. `calibrate_embedding_factor` returns `(factor, measurement)` with the measurement
carried into the run record, since a block size compared against a model prediction is only
meaningful alongside the embedding that produced it.
