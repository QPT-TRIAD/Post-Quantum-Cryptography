"""The recorded production parameter set, as named constants with their citations.

**This module is the deliberate crossing of the build's stop point, and it is written so that the
crossing is visible rather than incidental.**

Everything before it was validated against synthetic instances and *published* parameter sets only,
because the project's constraint was that nothing run against the corpus's recorded numbers. That
constraint was structural rather than remembered: ``InstanceSource`` has no member that can express
the production instance, and ``test_corpus_source_is_unrepresentable`` fails if one is added. It is
still true — **no lattice is ever built from these values, and no reduction ever runs on them.** The
only consumer is the lattice-estimator, which is a cost model.

**The values are recorded here rather than read from the research tree**, and that is a design
decision with two consequences. First, no source file names the tree, so
``test_no_source_file_names_the_research_tree`` keeps its meaning: there is no runtime reach into the
corpus and a run is reproducible without it. Second, every number below carries its citation, so a
reader can check it rather than trust it.

## What is recorded, and what is not

The corpus records these in two places that do not agree about ``p``. That contradiction is carried
in the report rather than resolved here — see ``_CITATION_CONTRADICTION`` — because the estimator
takes whichever ``p`` it is given and a reader needs to know which reading produced the number.
"""

from __future__ import annotations

__all__ = [
    "PRODUCTION_NU",
    "PRODUCTION_Q_L",
    "PRODUCTION_P",
    "PRODUCTION_M",
    "PRODUCTION_EXPOSURE",
    "PRODUCTION_NOISE_BOUND",
    "SAMPLE_COUNT_SATURATION",
    "QLWR_STATUS",
    "QLWR_OBLIGATION_CITATIONS",
    "SAMPLE_COUNT_SATURATION_PROVENANCE",
    "CITATIONS",
    "PRODUCTION_PARAMETER_SUMMARY",
    "sample_count_readings",
    "samples_after_normal_form",
    "secrets_that_force_saturation",
]

#: The lattice secret dimension.
#: `files/PQ_CE_QS_research_qualification_v1.18.md:257-261`; restated in
#: `_adversarial_alt_strategy_v1.md:100` and `_blocker_resolution_v1.19.md:223-231`.
PRODUCTION_NU = 256

#: The large modulus, ``2^16``.
PRODUCTION_Q_L = 1 << 16

#: The rounding modulus, ``2^8``. **Contradicted by the corpus** — see the citation note below.
PRODUCTION_P = 1 << 8

#: The number of LWR rows.
PRODUCTION_M = 608

#: The recorded sample exposure, ``608 + 1024 * (608 + 48)``. It is not the same quantity as ``m``,
#: and the corpus does not say which one an attack should be costed against. Both readings are
#: available through :func:`sample_count_readings`.
PRODUCTION_EXPOSURE = 672_352

#: ``q_L // (2p)``, derived rather than recorded. The rounding error is exactly uniform on
#: ``[-B, B-1]``; there is no sigma to choose, and choosing one would estimate a different instance.
PRODUCTION_NOISE_BOUND = PRODUCTION_Q_L // (2 * PRODUCTION_P)

#: The sample count at which the primal attack stops getting cheaper, **measured** at these
#: parameters — not recorded in the corpus and not a property of QLWR.
#:
#: Why it is here at all: it is what decides between the two readings. The cost as a function of the
#: sample count is a non-increasing step function, and past this point it is flat, so every count
#: from here to :data:`PRODUCTION_EXPOSURE` gives one identical estimate. The choice between the two
#: recorded readings therefore does not need to be made — what needs checking is only whether some
#: single secret reaches this count, which :func:`secrets_that_force_saturation` turns into a number
#: the corpus can be compared against.
#:
#: **It is a measurement, so it can move.** It belongs to this parameter set, the ``ADPS16``
#: classical cost model and estimator revision ``53da5982``; an estimator upgrade may return a
#: different step function. ``scripts/sample_count_saturation.py`` re-measures it and keeps the walk
#: it was read from in ``results/production_estimate/sample_count_saturation.json``, including the
#: eighteen steps below it. That script is the authority; this constant is a convenience that cites
#: it, and a test pins the two together.
SAMPLE_COUNT_SATURATION = 791

#: **What a hardness number computed for these parameters is for.** This travels with the number,
#: the way :data:`~qlwr_lattice_stress.problem.qpt128_accounting.MODE_B_STATUS` travels with the
#: margins, because the number is easy to lift out of context and re-quote as something it is not.
#:
#: QLWR is **not in any live profile**. Occurrences of ``LWR``/``QLWR`` are zero in the B0 wire spec,
#: in the finalization document, in the Mode S documents and in the Mode B security document: B0
#: rests on EUF-CMA of a category-5 signature, Mode S instantiates the link-and-mask roles with a
#: hash-based domain PRF, and Mode B's handle is a power map. QLWR survives only in the superseded
#: original construction, which ``attack_lab_results_v1.51.md:7`` records as refuted and replaced.
#:
#: So the estimate in ``notes/10-production-estimate.md`` is **not** a statement about deployed
#: security, and the corpus never claimed one for these parameters — it claims the opposite. The
#: nearest thing to a figure anywhere is a *budget allocation*, ``ε_QLWR ≤ 2⁻¹³¹`` at
#: ``pqt.md:2137`` under an explicit "suppose". What the estimate fills is a named obligation the
#: corpus marks open, under its own heading at ``pqt.md:1542-1548``: *"Concrete QPT-128
#: instantiation — NOT YET NUMERICALLY CERTIFIED."*
QLWR_STATUS = (
    "withdrawn from every live profile — QLWR survives only in the superseded original "
    "construction. A hardness figure for these parameters fills the corpus's open obligation "
    "(C3.5, research_qualification_v1.18.md:279, pqt.md §25); it is not a deployed security "
    "level and must not be quoted as a QPT-128 claim."
)

#: The corpus locations that record the obligation this estimate fills, so the claim travels with
#: its citation rather than being asserted.
QLWR_OBLIGATION_CITATIONS = (
    "files/PQ_CE_QS_multitrack_verification_v1_20.md:130-132",   # C3.5, verdict OPEN
    "files/PQ_CE_QS_research_qualification_v1.18.md:279",        # 128-bit QPT qualification: Open
    "pqt.md:1192-1226",                                          # §25, the parameter-validation obligation
    "pqt.md:1542-1548",                                          # "NOT YET NUMERICALLY CERTIFIED"
)

#: What produced :data:`SAMPLE_COUNT_SATURATION`, recorded so a stale value is detectable rather
#: than silently wrong.
SAMPLE_COUNT_SATURATION_PROVENANCE = {
    "script": "scripts/sample_count_saturation.py",
    "results": "results/production_estimate/sample_count_saturation.json",
    "cost_model": "ADPS16(classical)",
    "estimator_revision": "53da5982597709ba0fdf94ea37a84d822310fd84",
    "beta_at_and_above": 368,
    "last_count_below": 790,
    "beta_there": 369,
    "steps_below": 18,
}


def sample_count_readings() -> dict[str, int]:
    """The two sample counts the corpus supports, each labelled.

    A cost estimate is only meaningful alongside which reading it was made under, so both are
    returned rather than one being silently preferred. ``m`` is the number of recorded rows;
    ``exposure`` is what the corpus records as the sample exposure. To a lattice attack those are
    different amounts of data, and the estimator takes the one it is handed.
    """
    return {"rows": PRODUCTION_M, "exposure": PRODUCTION_EXPOSURE}


def samples_after_normal_form(reading: str) -> int:
    """How many samples survive the normal form — the count an attack actually gets.

    The normal form replaces the uniform secret with a short one, and it pays for that by
    **consuming ``nu`` samples** to produce the new secret's coordinates. That identity is what makes
    a QLWR instance attackable at all (a uniform secret has no short representative, so an embedding
    built on it contains no short vector), and this function is its cost side.

    It is derived here rather than left to the estimator because it decides the answer, and the two
    readings sit on opposite sides of the knife edge. At the ``rows`` reading 608 - 256 = 352
    samples remain, and the estimator's dual attack search is capped at ``beta <= m`` — so it returns
    the largest block size 352 samples admit, with the cost *still falling there*. At the ``exposure``
    reading 672,096 remain and the same search finds an interior optimum. The same model, the same
    instance, and the dual column means something different in each row; a report that printed the
    two costs without this count would show a 136-bit gap with nothing to explain it.

    The rule mirrors ``LWEParameters.normalize()`` in the estimator: the transformation fires only
    when the error is narrower than the secret *and* ``m >= 2 * nu``, so a sample count below that
    threshold passes through untouched rather than being reduced to something negative.
    """
    readings = sample_count_readings()
    if reading not in readings:
        raise ValueError(
            f"unknown sample reading {reading!r}; the corpus supports {sorted(readings)}. The two "
            "are different amounts of data to an attack, and a cost is only meaningful alongside "
            "which one it was made under."
        )
    m = readings[reading]
    if m < 2 * PRODUCTION_NU:
        return m
    return m - PRODUCTION_NU


def secrets_that_force_saturation(exposure: int = PRODUCTION_EXPOSURE) -> int:
    """How many distinct secrets the exposure can be spread over before the cost stops being forced.

    The recorded exposure is a total over many rows. If it is read under one secret, that secret
    carries all of it and comfortably clears the saturation point. If it is spread, no individual
    secret necessarily does — and then the cost depends on the largest per-secret count, which the
    corpus does not record.

    This is the largest number of secrets for which the spread cannot avoid the threshold, by
    pigeonhole: with ``N`` secrets and ``T`` rows some secret carries at least ``ceil(T/N)``, and
    ``ceil(T/N) >= S`` exactly when ``N <= (T-1)/(S-1)``.

    **It is a bound on a doubt, not a claim about the corpus.** The exposure is read here as one
    validator's count — the secret is fixed per validator while the matrix is domain-indexed, so a
    validator's rows across all 1,024 domains share a secret — and under that reading the question
    does not arise. The helper answers what happens if that reading is wrong and the 672,352 is a
    total spread over many secrets: below the returned count the exposure reading is *forced* and its
    cost stands, and above it the cost falls back toward the per-secret count actually reached. At
    the recorded values that is 851 — a spread averaging 790 rows per secret. One secret per domain,
    1,024, is above the bound and would put the cost nearer the 656-row step than the 791-row one.
    """
    # Integer-only, and deliberately not `ceil(exposure / saturation)`: that is the count of secrets
    # *at* which the bound lands, which is off by one from the count *below* which it holds.
    return (exposure - 1) // (SAMPLE_COUNT_SATURATION - 1)


#: Where each recorded value comes from. Kept as data so a report can print them without this module
#: having to be read.
CITATIONS = {
    "nu": "files/PQ_CE_QS_research_qualification_v1.18.md:257-261",
    "q_l": "files/PQ_CE_QS_research_qualification_v1.18.md:257-261",
    "p": "files/PQ_CE_QS_research_qualification_v1.18.md:257-261",
    "m": "files/PQ_CE_QS_research_qualification_v1.18.md:257-261",
    "exposure": "files/PQ_CE_QS_research_qualification_v1.18.md:257-261",
}

#: The corpus's internal contradiction about ``p``, recorded verbatim in substance and **not
#: resolved by this project**. ``security_proof_v1.3.md:101`` requires ``p`` prime for public
#: tracing while the only recorded numeric set uses ``2^8``, which is not prime. `2^8` is used here
#: because it is the value in the numeric table; the requirement is not thereby satisfied.
_CITATION_CONTRADICTION = (
    "`security_proof_v1.3.md:101` requires p prime; `research_qualification_v1.18.md:257` records "
    "p = 2^8. Both are recorded in the corpus and neither is chosen by this project."
)


def PRODUCTION_PARAMETER_SUMMARY() -> dict:
    """The recorded set, with its citations and the contradiction, as one printable mapping.

    A function rather than a constant so that the noise bound and the sample readings are computed
    where they are declared rather than duplicated.
    """
    return {
        "nu": PRODUCTION_NU,
        "q_l": PRODUCTION_Q_L,
        "p": PRODUCTION_P,
        "m": PRODUCTION_M,
        "exposure": PRODUCTION_EXPOSURE,
        "noise_bound": PRODUCTION_NOISE_BOUND,
        "noise_interval": [-PRODUCTION_NOISE_BOUND, PRODUCTION_NOISE_BOUND - 1],
        "rounding_ratio": PRODUCTION_Q_L // PRODUCTION_P,
        "is_bit_shift_rounding": True,
        "sample_count_readings": sample_count_readings(),
        "samples_after_normal_form": {
            reading: samples_after_normal_form(reading) for reading in sample_count_readings()
        },
        "sample_count_saturation": SAMPLE_COUNT_SATURATION,
        "sample_count_saturation_provenance": dict(SAMPLE_COUNT_SATURATION_PROVENANCE),
        "secrets_that_force_saturation": secrets_that_force_saturation(),
        "readings_at_or_above_saturation": {
            reading: m >= SAMPLE_COUNT_SATURATION
            for reading, m in sample_count_readings().items()
        },
        "citations": dict(CITATIONS),
        "contradiction": _CITATION_CONTRADICTION,
        "qlwr_status": QLWR_STATUS,
        "qlwr_obligation_citations": list(QLWR_OBLIGATION_CITATIONS),
        "lattice_built": False,
        "note": (
            "These values are consumed only by the lattice-estimator, which is a cost model. No "
            "lattice is constructed from them and no reduction runs on them: at nu = 256 the uSVP "
            "dimension is 609, which is far beyond anything this host can reduce. The number this "
            "produces is the model's, and its credibility rests on the same-scale comparison the "
            "scaled sweep supplies."
        ),
    }
