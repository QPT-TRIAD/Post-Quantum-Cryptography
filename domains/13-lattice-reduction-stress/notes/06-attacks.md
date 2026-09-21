# Milestone 7 — the two attack families, and one of them does not reach

## The primal attack works, and its threshold behaves

At the calibrated instance (`nu = 32, m = 76`, embedded dimension 77), with the **calibrated**
embedding factor `M = 3`:

| block size | recovered | time |
|---:|---|---:|
| 2 (LLL) | no | 0.01 s |
| 10 | no | 0.03 s |
| 20 | no | 0.04 s |
| **30** | **yes** | **0.12 s** |

The minimum successful block size is 30, with three recorded failures below it. Those failures are
what make the number a *threshold*: a sweep that stopped at the first success could not distinguish
"found at 30" from "found at 30 after failing everywhere below", and only the second supports a
statement about difficulty.

**The calibrated factor beat the hand-picked one.** M5's test used `M = 5` and needed block size 40;
the calibration returns `M = 3` and the attack succeeds at 30. Neither is wrong — a larger
embedding factor lengthens the planted vector, so it costs block size — but it is a reminder that
the factor is a real input to the result and belongs in the record beside it, which is why
`calibrate_embedding_factor` returns its measurement rather than only the number.

The round trip holds: a recovered vector inverts back to the secret the QLWR relation is defined on,
so the attack is about the scheme rather than about a lattice.

## The dual attack does not apply at this scale — at any size tested

| nu | m | dual dimension | shortest `\|\|y\|\|₁` | budget `q/(2B)` |
|---:|---:|---:|---:|---:|
| 4 | 12 | 8 | — | 256 |
| 32 | 76 | 44 | **~3.4 × 10⁴** | **256** |

The distinguisher's band is `||y||_1 * B`. For the statistic to separate real samples from uniform
ones, that band has to stay well inside `Z_q` — roughly `||y||_1 < q/(2B) = 256`. The shortest dual
vectors the reduced basis produces have `||y||_1` about **130 times that budget**, so the band
covers the entire residue space, every vector "lands inside it" for real *and* uniform samples, and
the statistic is identically zero.

**This is arithmetic, not a defect.** The dual lattice has determinant `q^n` in dimension `m`, so
its shortest vector scales as `q^(n/m)`; at `q = 2^16` with `n/m ≈ 0.4` that is large. Making the
dual attack reach would need a smaller modulus, a larger sample-to-unknown ratio, or a smaller
noise bound — none of which this parameter set offers.

**The asymmetry is worth stating plainly because it is the reverse of what a reader might expect:
at these parameters the *primal* attack is the easy one and the dual attack does not reach at all.**
The estimator reports the minimum over both families as the claimed security level, so a project
that ran only the dual would conclude the instance was hard.

The result is recorded as `not_run` **with its reason**, not as an advantage of zero. "The attack
does not apply here" and "the attack was tried and found nothing" are different claims, and a bare
zero cannot tell them apart — which is the same distinction the project's `provenance` field exists
to carry.

## A refusal is a result, in both attacks

Both attack entry points catch the engine's refusal — most commonly a block size exceeding the basis
dimension, which `fplll` accepts silently while doing something else — and return a `not_run` result
rather than raising. A caller sweeping block sizes should not have to special-case the ends of its
own range, and a sweep that omits a point it could not run is indistinguishable from one where the
point succeeded.

That this was needed at all came from the engine layer refusing a block size of 20 on an
8-dimensional dual basis: `fplll` would have run something and reported it at the requested size.

## State

262 tests pass. Both attack families are wired to the engine layer, both record their refusals, and
the primal attack's threshold is measured rather than assumed.
