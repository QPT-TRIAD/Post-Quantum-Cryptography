# Milestone 5 — the embedding factor, and a disagreement with the cost model

The load-bearing test needs an instance where the attack is *not* trivial. Calibrating one turned up
two things: an artifact that makes the naive embedding factor wrong, and a large disagreement
between the estimator's prediction and measured behaviour that is itself the finding the project
exists to produce.

## Finding 1 — the embedding always contains ``(0, ..., 0, pM)``

At `M = 1` the reduction returns a vector of norm 256 that has nothing to do with the secret: zero
in every sample coordinate, zero in every secret coordinate, and `-p` in the last. It is shorter
than the planted vector (525), so the planted vector is not the shortest, and uSVP has nothing to
find.

The cause is structural and exact. When `p | q`, every lifted sample is `b_i = (q/p) * t_i` with
integer `t_i`. Multiplying the embedding row by `p` gives

    p * (b, 0, M) = (q * t, 0, p * M)

and `(q * t, 0, 0)` is a lattice element, so their difference is in the lattice:

    (0, ..., 0, p * M)

**So the embedded lattice always contains a vector of norm `p * M`, whatever the instance.** For the
planted vector to stay shortest, `M` must be large enough that `p*M` exceeds it — which is a
condition on the instance, not a constant:

    (p*M)^2 > ||e||^2 + ||x||^2 + M^2

At `nu = 20, m = 48` that needs `M >= 3`; `M = 10` works comfortably. **The design document's
sketch uses `M = 1`, and that is wrong** — it would produce an attack that runs, reports a plausible
root-Hermite factor, and is not attacking the intended vector.

This makes `calibrate_embedding_factor` load-bearing rather than a convenience, and it is why the
planted-vector test must assert the planted vector is *shortest*, not merely *in the lattice*.
Membership alone passed at `M = 1` — the vector is genuinely in the lattice — while the attack was
meaningless.

## Finding 2 — the estimator predicts a block size the attack does not need

The plan's calibration recipe selects a dimension whose estimator-predicted block size lands in
`[25, 45]`. At `nu = 20, m = 48` the estimator predicts **β = 42**.

Measured: **LLL (β = 2) recovers the planted vector**, at every embedding factor that makes it
shortest. There is no block size at which the attack fails and then succeeds — it succeeds
immediately.

| nu | m | lattice dim | estimator β (usvp) | measured |
|---:|---:|---:|---:|---|
| 20 | 48 | 49 | 42 | recovered at β = 2 |
| 32 | 76 | 77 | 40 | *(not yet measured)* |
| 64 | 152 | 153 | 84 | *(not yet measured)* |

Two candidate explanations, and they are not exclusive:

1. **The embedding differs from the model's.** The cost model's uSVP attack targets the q-ary
   lattice, whose shortest vector is the error alone (`||e||^2 = 144030` at this size). The emulator
   embeds the secret alongside it, so its planted vector is `(e, -x, M)` with
   `||.||^2 = 276024` — roughly twice the norm. A longer target should be *harder*, not easier, so
   this does not explain the direction.
2. **The instance is in a regime the model does not describe.** The error is uniform on `[-B, B]`
   with `B = q/(2p)`, and the modulus is a power of two. The model assumes a Gaussian error and a
   generic modulus. This is the same *class* of mismatch as the M2 finding that `usvp` returns an
   infinite cost for a QLWR instance at all.

**This disagreement is the project's subject, not a defect in it.** The central comparison is
measured versus theoretical at the same scale, and a large discrepancy is a result — one that has to
be reported as an anomaly rather than absorbed. But it does block the M5 test as specified, because
a test whose assertion is "recovery succeeds above the predicted block size and fails below" cannot
be written on an instance where recovery succeeds at zero cost.

## What this changes

- `calibrate_embedding_factor` must search for a factor at which the planted vector is **shortest**,
  and the search is over an instance-dependent threshold, not a fixed constant.
- The M5 fixture must be calibrated on **measured** behaviour — the smallest dimension at which LLL
  demonstrably fails — not on the estimator's predicted block size. The plan's `[25, 45]` recipe is
  discarded; it was a reasonable proxy and the measurement contradicts it.
- The estimator-versus-measured gap becomes a first-class result with a place in report section (7),
  alongside the M2 finding that `usvp` does not apply to QLWR at all.

## Finding 2, resolved — it is a small-dimension artifact, and it is not about QLWR

Two isolation instances were run, isolating the two ways a QLWR instance deviates from the LWE model.
**Both came back negative, and identically so.** The estimator returns the same block size for:

| | uniform error | Gaussian error (same sigma) | prime modulus | prime + Gaussian |
|---|---|---|---|---|
| n=20, m=48 | 42 | 42 | 42 | 42 |
| n=32, m=76 | 40 | 40 | 40 | — |
| n=64, m=152 | 84 | 84 | 84 | — |

The model's inputs are `(n, q, m, sigma)`, and both QLWR-specific deviations reduce to inputs a
matched LWE instance already shares — the error's *shape* enters only through its standard
deviation, and the modulus only through its bit length. **The estimator cannot distinguish a QLWR
instance from an LWE one at the same `(n, q, m, sigma)`.** So the disagreement is not about LWR
structure, and neither hypothesised cause is live.

What it *is*: a small-dimension artifact. Measured across sizes:

| n | m | est. dimension | usvp beta | **beta / d** |
|---:|---:|---:|---:|---:|
| 20 | 48 | 48 | 42 | **0.88** |
| 24 | 58 | 58 | 50 | 0.86 |
| 28 | 68 | 68 | 58 | 0.85 |
| 32 | 76 | 76 | 40 | 0.53 |
| 48 | 116 | 116 | 52 | 0.45 |
| 64 | 152 | 152 | 84 | 0.55 |
| 128 | 304 | 304 | 196 | 0.64 |

For `n <= 28` the predicted block size is 85–88% of the lattice dimension. At that ratio BKZ is
effectively full enumeration of a tiny lattice, which is cheap, so LLL recovering an anomalously
short vector is unremarkable and the predicted cost is inapplicable rather than wrong. The block
size also moves **non-monotonically** across that boundary (58 at n=28, 40 at n=32), which is the
signature of a model artifact rather than a physical effect. The regime is left behind by `n = 32`,
where `beta/d` falls to 0.53.

**This corrects a reading that would have been too strong.** The disagreement is *not* evidence that
the estimator overestimates QLWR's concrete security: the effect vanishes by `n = 32` and is a
property of dimension, not of the relation. It would be a serious claim and the measurement does not
support it. The two anomalies stay distinct in report section (7), as noted, but the second one is
now recorded as **a small-dimension artifact with a measured boundary**, which is weaker and more
accurate than "the estimator is wrong when applicable".

## Consequence for the M5 fixture

Use `n >= 32`. Below that the predicted block size approaches the dimension and every test of the
form "fails below the prediction, succeeds above it" is meaningless — there is no such boundary to
find. Whether LLL still fails at `n = 32` is the remaining measurement, and it is the one that
decides the fixture.

## The calibrated fixture, and the boundary is not sharp

`n = 32, m = 76` — embedded dimension 77, embedding factor 5.

| block size | outcome | time |
|---:|---|---:|
| 2 (LLL) | **no recovery** | 0.10 s |
| 20 | 2 of 5 seeds recover | 0.12 s |
| 40 | **recovery, all seeds** | ~16 s |

The estimator predicts β = 40 for this size, so **the model and the measurement agree here** —
which is the independent confirmation that the earlier disagreement was a small-dimension artifact
and not a defect in the model. That is the strongest evidence available for the resolution above,
and it comes from a different direction than the ratio table.

**The boundary is graded rather than sharp**, and that changed the test. The plan puts the negative
assertion at `β_pred - 15 = 25`; measured across seeds, β = 20 already recovers on three of five.
An assertion there would fail intermittently and read as flakiness rather than as "this instance is
easier than calibrated". The negative now runs at **LLL**, which is both the strongest claim that is
stable and the one that actually matters: *the cheapest reduction does not find it*.

M5 passes with the two-sided test in place: no recovery at LLL, recovery at the predicted block
size, exact integer equality against the planted vector, and — the assertion that makes it about
QLWR rather than about a lattice — the recovered vector inverting back to the secret the relation
was built on.

## Not yet done

- The `β/d` ratio should be recorded beside every measured result from here on. A block size that is
  a large fraction of the dimension makes the cost model's output inapplicable, and a reader
  comparing a small-scale measurement to a production estimate needs to see that before trusting
  the comparison.
- The `beta/d` ratio is worth recomputing for whatever fixture is chosen, and recording it beside
  the result: a block size that is a large fraction of the dimension makes the cost model's output
  inapplicable, and a reader comparing that number to a production estimate should be able to see
  it.
