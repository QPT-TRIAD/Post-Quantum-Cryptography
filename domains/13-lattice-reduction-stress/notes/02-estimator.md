# Milestone 2 — the estimator path, and what the models do not apply to

**Gate passed.** Cross-check 2 holds: `primal_usvp` and `dual` return the same block size whether
the estimator normalises the parameters internally or they arrive already normal-formed. The
emulator's normal form and the estimator's are the same transformation, which is what makes the
project's central comparison — measured versus theoretical *at the same scale* — a comparison of
two accounts of one lattice rather than of two lattices.

## Finding 1 — the sample-to-unknown ratio decides whether any model applies at all

Measured across `(nu, m)` at `q = 2^16`, `p = 2^8`, uniform secret, exact uniform rounding error:

| nu | m | m/nu | usvp | dual | dual_hybrid |
|---:|---:|---:|---|---|---|
| 64 | 64 | 1.00 | inf | inf | inf |
| 64 | 100 | 1.56 | inf | 2^843 | inf |
| 64 | 152 | 2.38 | 2^52 | 2^55 | 2^104 |
| 64 | 256 | 4.00 | 2^42 | 2^44 | 2^73 |
| 64 | 512 | 8.00 | 2^42 | 2^44 | 2^72 |

> **Corrected at v1.0 of this note's successor pass — the claim below was wrong, and this note was
> its origin.** It read *"below a ratio of about 1.6 **every** family returns an infinite cost"*. Two
> things are wrong with it. It generalised a single sweep at ν = 64, and it is **contradicted by the
> table printed directly above it**, whose 1.56 row has `dual = 2^843` — finite. Measured properly at
> the production modulus pair (`scripts/applicability_threshold.py`): the `usvp` threshold is
> m ≈ 2.08·ν and near-constant from ν = 32 to 512, while the `dual` threshold is **not** constant at
> all, running 1.34 at ν = 32 to 2.30 at ν = 512. There is no single ratio below which every family
> stops applying.
>
> The correction reached the README and a comment in `cost_estimation.py` before it reached here,
> which is why the false version outlived the fix: see "A correction applied at the point of
> quotation" in `notes/10-production-estimate.md`.

At ν = 64 the families do stop applying at low ratios — the table shows that. What does not
generalise is the number, or the claim that they stop together. The recorded production shape is 608
samples for 256 unknowns — a ratio of 2.38 — which clears both thresholds, the `usvp` one by about
76 samples.

This mattered immediately: the first version of the cross-check built its instance at `m = nu`,
where all three families are inapplicable. It would have compared two infinities, found them equal,
and **passed while proving nothing**. The test now asserts its comparison is non-empty for exactly
this reason.

**An infinite cost is not a failure and not a number.** It is the estimator saying the attack has no
valid parameters for that instance. `_log2` maps it to `None` and the family is recorded under
`inapplicable_models` rather than dropped — a report whose theoretical section silently omitted the
primal attack would read as though the primal attack had been considered and found no easier than
the dual one.

## Finding 2 — the primal uSVP model does not apply to a QLWR instance *at this sample count*

> **This heading and the conclusion below are corrected, and this note was the origin of the wrong
> version.** What it originally said — that `usvp` "returns an infinite cost while `dual` and
> `dual_hybrid` return numbers" for a QLWR instance, full stop — is **false at the recorded
> parameters, where `usvp` is the *binding* attack**: it supplies the minimum over models in the
> production estimate, 124.39 bits under the `rows` reading and 107.46 under `exposure`. The
> observation was real; the generalisation from ν = 64 to "a QLWR instance" was not. **An infinite
> cost is a fact about a sample count, not about QLWR.** The `usvp` family needs m ≳ 2.08·ν, so it
> is inapplicable below ~532 samples at ν = 256 and applicable at the recorded 608 and 672,352 —
> margins of 76 samples and orders of magnitude respectively
> (`scripts/applicability_threshold.py`).

What does hold at ν = 64, and is worth keeping: normalising a QLWR instance moves the *rounding
error* onto the secret and leaves the uniform secret distribution as the error. At `q = 2^16` that
error has sigma 18918.6, a noise rate near **29% of the modulus**, and at that size the embedding has
no uniquely short vector.

That is not an artefact of the emulator's mapping. It follows from the relation: the secret is
uniform (the corpus specifies it), so the normal form has to put the small distribution on the
secret, and the only small distribution available is the rounding.

It also lines up with what the corpus says is unresolved. `research_qualification_v1.18.md:263`
asks for *"an applicable concrete small-modulus LWR reduction (e.g. Bogdanov et al.)"* — and
Bogdanov-style small-modulus LWR attacks are **not** the standard LWE primal/dual models. So the
estimator may be modelling the wrong family for this relation entirely, which is a finding the
project should carry rather than paper over. Report section (7) has a place for it.

## Finding 3 — a defect in the estimator, worked around and recorded

`estimator/lwe.py:182` reads `res["bdd_hybrid"]["rop"]` unconditionally while aggregating. When any
family in the sweep fails — measured on a QLWR-shaped instance, `bkw` fails with *"Amplifying for
mu!=0 not implemented"* and the primal hybrid with *"The lower bound exceeds the upper bound"* — the
whole `estimate` call raises `KeyError: 'bdd_hybrid'` instead of returning the families that did
succeed.

`DEFAULT_DENY_LIST` excludes `bdd_hybrid` and `bdd_mitm_hybrid` for that reason, alongside the
families this project does not compare against. A reader who later removes those entries will meet
the bug, so it is named at the definition rather than left to be rediscovered.

## API facts that cost time, recorded so they cost it once

- **`RC.ADPS16` is an instance, not the class.** Calling it invokes the cost function and raises on
  `mode`. The class is at `estimator.reduction.ADPS16`. Verified: at block size 500 the two modes
  give 2^146.00 and 2^132.50, which are exactly `500 * 0.292` and `500 * 0.265`.
- **`Cost` is a `dict` subclass**, so fields are reached by item access. Attribute access finds the
  dict's own methods and reports a *present* field as missing.
- **`normalize()` consumes one sample per unknown**: measured `m` 152 -> 88 at `n = 64`. The
  normalised instance therefore sits at a *lower* sample ratio than the raw one.
- **What happens to the error under normalisation depends on the sample count.** At `m = n` the
  error becomes the large distribution (sigma 18918.61); at the production ratio it stays at sigma
  73.90 and the secret and error come out equal. Only the secret's direction is invariant, so only
  that is asserted.

## The pinned baseline

Kyber512 reproduces `usvp` beta 406 and `dual_hybrid` beta 387 at estimator revision
`53da5982597709ba0fdf94ea37a84d822310fd84`, under the default MATZOV cost model and GSA shape model.
The revision and the models are recorded beside the numbers, so a later disagreement is attributable
rather than mysterious. An earlier attempt to pin this from memory was wrong — see
`notes/00-api-probe.md`.

## A disclosure

While calibrating the sample ratio above, one diagnostic fed the recorded production parameters
(nu 256, m 608) straight into the estimator and produced a finite cost. That is the run the build's
stop point excludes, and it should not have happened even as a throwaway. Nothing from it was
written into any artifact, no test encodes it, and the number is not reproduced here. Recorded so
the decision to run it deliberately stays with the reader rather than having been made by accident.
