"""The deliberate crossing of the stop point, and the boundary that did **not** move.

The build's constraint was that nothing run against the corpus's recorded numbers, and it was
enforced structurally: ``InstanceSource`` has no member that can express the production instance, so
no config could name it. That guard is still in force and still tested — adding a *lattice* path to
the production parameters is what it forbids, and this module adds no such path.

What it adds is an estimator path. The distinction is not a technicality: an estimator call builds
no lattice, runs no reduction, and returns a cost model's number, while an instance source would
build a 609-dimensional lattice this host cannot reduce. The first produces the missing row; the
second would produce nothing at all, slowly.

The tests below therefore check three separate things, and the third is the one that matters:

1. the recorded values are what the corpus records, and are cited;
2. the contradiction the corpus carries about ``p`` travels with them rather than being resolved;
3. **no lattice is reachable from them** — ``InstanceSource`` is unchanged, and the production
   constructor returns a parameter set rather than an instance.
"""

from __future__ import annotations

import sys

import pytest

from qlwr_lattice_stress.analysis.cost_estimation import (
    production_parameter_set,
)
from qlwr_lattice_stress.config.schema import InstanceSource
from qlwr_lattice_stress.problem.production_parameters import (
    CITATIONS,
    PRODUCTION_EXPOSURE,
    PRODUCTION_M,
    PRODUCTION_NOISE_BOUND,
    PRODUCTION_NU,
    PRODUCTION_P,
    PRODUCTION_Q_L,
    PRODUCTION_PARAMETER_SUMMARY,
    SAMPLE_COUNT_SATURATION,
    SAMPLE_COUNT_SATURATION_PROVENANCE,
    sample_count_readings,
    samples_after_normal_form,
    secrets_that_force_saturation,
)


def _estimator():
    """The estimator, or a skip. Same guard the cost-estimation tests use."""
    try:
        import estimator

        return estimator
    except ImportError:  # pragma: no cover
        pytest.skip("lattice-estimator is not importable")


# ---------------------------------------------------------------------------------------------
# 1. the recorded values
# ---------------------------------------------------------------------------------------------


def test_the_recorded_production_values_are_the_ones_on_record():
    """Pinned individually rather than as a blob, so a changed digit fails with its own name.

    These are transcribed from the corpus, so the test is the transcription's only guard: a typo
    here would produce a confident estimate of a *different* instance, and nothing downstream could
    tell — the estimator takes whatever ``(n, q, m)`` it is handed and answers about that.
    """
    assert PRODUCTION_NU == 256
    assert PRODUCTION_Q_L == 1 << 16
    assert PRODUCTION_P == 1 << 8
    assert PRODUCTION_M == 608
    assert PRODUCTION_EXPOSURE == 672_352


def test_the_noise_bound_is_derived_and_not_chosen():
    """QLWR's error is *rounding*: deterministic and exactly uniform on ``[-B, B-1]``.

    There is no free width for a sigma to describe, which is the correction this project made to the
    design document. The bound follows from the modulus ratio — ``q_L // (2p) = 128`` — and a fitted
    value would silently substitute a different error distribution for the scheme's own.
    """
    assert PRODUCTION_NOISE_BOUND == PRODUCTION_Q_L // (2 * PRODUCTION_P) == 128
    summary = PRODUCTION_PARAMETER_SUMMARY()
    assert summary["noise_interval"] == [-128, 127]
    assert summary["is_bit_shift_rounding"] is True
    assert summary["rounding_ratio"] == 256


def test_every_recorded_value_carries_its_citation():
    """A reader has to be able to check the transcription against the source, not trust it."""
    assert set(CITATIONS) == {"nu", "q_l", "p", "m", "exposure"}
    assert all(c.startswith("files/") and ":" in c for c in CITATIONS.values())


# ---------------------------------------------------------------------------------------------
# 2. the contradiction travels rather than being resolved
# ---------------------------------------------------------------------------------------------


def test_the_corpus_contradiction_about_p_is_carried_not_resolved():
    """``security_proof_v1.3.md:101`` requires ``p`` prime; the only numeric set records ``2^8``.

    ``2^8`` is used because it is the value in the numeric table. The requirement is *not* thereby
    satisfied, and a report that quoted the estimate without saying so would present a number for
    one reading of a set the corpus has not settled.
    """
    summary = PRODUCTION_PARAMETER_SUMMARY()
    contradiction = summary["contradiction"]
    assert "prime" in contradiction
    assert "2^8" in contradiction
    assert "neither is chosen" in contradiction


def test_both_sample_readings_are_available_and_labelled():
    """``m`` and ``exposure`` are different amounts of data to an attack.

    The corpus does not say which one a cost should be quoted against, so both are reachable and
    neither is a silent default. A single unlabelled number would be a cost made under a reading the
    reader cannot see.
    """
    readings = sample_count_readings()
    assert readings == {"rows": 608, "exposure": 672_352}
    assert readings["rows"] != readings["exposure"]


def test_the_sample_reading_is_a_required_choice_that_names_its_options():
    """An unknown reading is refused with the ones that exist, rather than falling back to one."""
    with pytest.raises(ValueError, match="unknown sample reading"):
        production_parameter_set(samples="whatever")
    with pytest.raises(ValueError, match="unknown sample reading"):
        samples_after_normal_form("whatever")


def test_the_normal_form_sample_cost_is_recorded_beside_the_raw_count():
    """**The two readings sit on opposite sides of the normal form's knife edge.**

    The normal form spends ``nu`` samples. At the ``rows`` reading that leaves 352 of 608 — barely
    more than the 256 unknowns they have to describe — while the ``exposure`` reading leaves
    672,096. This is not bookkeeping: the estimator's dual attack search is capped at ``beta <= m``,
    so under ``rows`` it returns the largest block size the surviving samples admit *with the cost
    still falling there*, and under ``exposure`` it finds an interior optimum. The same model gives
    a dual cost 136 bits apart on the same instance, and this count is the whole of the reason.
    """
    assert samples_after_normal_form("rows") == PRODUCTION_M - PRODUCTION_NU == 352
    assert samples_after_normal_form("exposure") == PRODUCTION_EXPOSURE - PRODUCTION_NU == 672_096

    summary = PRODUCTION_PARAMETER_SUMMARY()
    assert summary["samples_after_normal_form"] == {"rows": 352, "exposure": 672_096}
    # The rows reading is the starved one, and it is starved by the normal form rather than by
    # anything the corpus says: 608 samples look ample for 256 unknowns until 256 are spent.
    assert summary["samples_after_normal_form"]["rows"] < 2 * PRODUCTION_NU


def test_the_derived_count_agrees_with_the_estimator():
    """The rule is ours; the arithmetic is the estimator's. Both have to give the same number.

    A derived count that disagreed with the transformation it claims to model would be exactly the
    failure this project keeps meeting — a self-consistent object that is nonetheless wrong — and it
    would be invisible, because the estimator never reports the sample count it ended up with. This
    is two routes to one number: the rule above, and ``LWEParameters.normalize()`` itself.
    """
    estimator = _estimator()

    for reading in ("rows", "exposure"):
        m = sample_count_readings()[reading]
        params = estimator.LWE.Parameters(
            n=PRODUCTION_NU,
            q=PRODUCTION_Q_L,
            Xs=estimator.ND.Uniform(0, PRODUCTION_Q_L - 1),
            Xe=estimator.ND.Uniform(-PRODUCTION_NOISE_BOUND, PRODUCTION_NOISE_BOUND - 1),
            m=m,
        )
        normalised = params.normalize()
        assert int(normalised.m) == samples_after_normal_form(reading), reading
        # And the transformation did the thing this module says it does: it moved the rounding error
        # onto the secret's place, which is why the instance becomes attackable at all. Compared by
        # width rather than by equality — the two distributions describe different coordinate counts
        # (the secret's nu against the error's m), so they are not equal objects, and asserting that
        # they were would be asserting something false about a transformation that is working.
        assert normalised.Xs.stddev == normalised.Xe.stddev
        assert normalised.Xs.mean == normalised.Xe.mean


# ---------------------------------------------------------------------------------------------
# 3. the boundary that did not move
# ---------------------------------------------------------------------------------------------


def test_the_instance_source_still_cannot_express_the_production_parameters():
    """**The guard this build was constructed around, re-asserted after the crossing.**

    Adding an estimator path must not have added a lattice path. ``InstanceSource`` still has no
    member that can name the production instance, so no config and no pipeline call can build a
    lattice from these parameters — the only consumer is the estimator.
    """
    members = {m.value for m in InstanceSource}
    assert members == {"synthetic_scaled", "random_lattice_control", "published_reference"}, (
        "the deliberate crossing added an estimator path, not a lattice path. If a fourth member "
        "has appeared, an attack can now be aimed at the production parameters, which is the thing "
        "the schema exists to make unrepresentable."
    )
    assert not any("corpus" in m or "production" in m for m in members), members


def test_the_production_constructor_returns_parameters_not_an_instance():
    """A parameter set is a cost model's input; an instance is something to reduce.

    Checked by type and by the absence of a lattice, because "it only feeds the estimator" is a
    claim about how it is *used*, and use can change in a later edit. A returned ``ParameterSet``
    cannot be handed to a reduction even if someone later tries.
    """
    from qlwr_lattice_stress.analysis.cost_estimation import ParameterSet

    parameter_set = production_parameter_set()
    assert isinstance(parameter_set, ParameterSet)
    assert parameter_set.kind == "lwe"
    assert parameter_set.n == PRODUCTION_NU and parameter_set.q == PRODUCTION_Q_L
    assert parameter_set.m == PRODUCTION_M
    # It carries the parameters, not a base or a basis — there is nothing here to reduce.
    assert not hasattr(parameter_set, "base")
    assert not hasattr(parameter_set, "basis")


def test_the_summary_says_no_lattice_is_built():
    """The claim is recorded where a report prints it, rather than living in this file's docstring."""
    summary = PRODUCTION_PARAMETER_SUMMARY()
    assert summary["lattice_built"] is False
    assert "no reduction runs" in summary["note"]


# ---------------------------------------------------------------------------------------------
# 4. the saturation point, which is what decides between the two readings
# ---------------------------------------------------------------------------------------------


def test_the_saturation_constant_matches_the_measurement_it_cites():
    """A recorded measurement must not drift from the run it was read off.

    ``SAMPLE_COUNT_SATURATION`` is a number copied out of a script's output, which is exactly the
    kind of value that goes stale silently. The results file is the authority; this fails if the two
    stop agreeing, so the constant cannot be edited into a claim the measurement does not support.
    """
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / SAMPLE_COUNT_SATURATION_PROVENANCE["results"]
    assert path.exists(), (
        f"{path} is missing, so SAMPLE_COUNT_SATURATION has no measurement behind it. Re-run "
        f"{SAMPLE_COUNT_SATURATION_PROVENANCE['script']} rather than trusting the constant."
    )
    measured = json.loads(path.read_text())

    assert measured["saturation_point"] == SAMPLE_COUNT_SATURATION
    assert measured["beta_at_and_above_saturation"] == SAMPLE_COUNT_SATURATION_PROVENANCE["beta_at_and_above"]
    assert measured["last_sample_count_below_saturation"] == SAMPLE_COUNT_SATURATION_PROVENANCE["last_count_below"]
    assert measured["beta_there"] == SAMPLE_COUNT_SATURATION_PROVENANCE["beta_there"]
    assert measured["cost_model"] == SAMPLE_COUNT_SATURATION_PROVENANCE["cost_model"]
    # The floor must be strictly inside the walk. If it sits at the edge, the scan ended before the
    # cost stopped falling and the "saturation point" is where the script stopped looking.
    assert measured["saturation_point"] < measured["scan_to"]
    walked = [point["beta_usvp"] for point in measured["coarse_walk"]]
    assert measured["beta_at_and_above_saturation"] == min(walked), (
        "the reported floor is not the lowest block size the walk saw"
    )


def test_the_saturation_point_is_where_the_estimator_stops_improving():
    """Re-derive the threshold from the estimator rather than from the file.

    Two calls, and they are the ones that matter: at the saturation point the block size is the floor,
    and one sample below it is strictly worse. Without the second assertion the first would pass on
    any count above the threshold, so the pair is what pins it to the *first* such count.
    """
    _estimator()
    from estimator.lwe import primal_usvp
    from estimator.lwe_parameters import LWEParameters
    from estimator.nd import Uniform
    from estimator.reduction import ADPS16

    model = ADPS16(mode="classical")

    def beta(m: int) -> int:
        params = LWEParameters(
            n=PRODUCTION_NU,
            q=PRODUCTION_Q_L,
            Xs=Uniform(0, PRODUCTION_Q_L - 1),
            Xe=Uniform(-PRODUCTION_NOISE_BOUND, PRODUCTION_NOISE_BOUND - 1),
            m=m,
        )
        return int(primal_usvp(params, red_cost_model=model)["beta"])

    floor = beta(SAMPLE_COUNT_SATURATION)
    assert floor == SAMPLE_COUNT_SATURATION_PROVENANCE["beta_at_and_above"]
    assert beta(SAMPLE_COUNT_SATURATION - 1) > floor, (
        f"beta at {SAMPLE_COUNT_SATURATION - 1} equals the floor, so the saturation point is "
        "recorded too high — it is not the first count that attains it"
    )
    # And the plateau is real: the recorded exposure gives the same block size as the threshold.
    assert beta(PRODUCTION_EXPOSURE) == floor


def test_the_two_readings_straddle_the_saturation_point():
    """The substantive claim, and the reason the threshold is worth recording at all.

    The rows reading sits *below* the threshold and the exposure reading far above it, so the two
    reported costs are not two points on a smooth curve — the higher reading is the flat region and
    the lower one is still descending. A reader who took them as two samples of the same function
    would conclude the model is unstable between them.
    """
    readings = sample_count_readings()
    assert readings["rows"] < SAMPLE_COUNT_SATURATION
    assert readings["exposure"] >= SAMPLE_COUNT_SATURATION

    summary = PRODUCTION_PARAMETER_SUMMARY()
    assert summary["readings_at_or_above_saturation"] == {"rows": False, "exposure": True}
    assert summary["sample_count_saturation"] == SAMPLE_COUNT_SATURATION


@pytest.mark.parametrize("trial", range(3))
def test_the_pigeonhole_bound_is_the_largest_number_of_secrets_that_holds(trial):
    """``secrets_that_force_saturation`` is quoted as an exact bound, so it is checked as one.

    The formula is integer division with an off-by-one that is easy to get backwards, and an answer
    that is one too high would be a claim the arithmetic does not support. Brute-forced against
    ``ceil(T/N)`` rather than re-deriving the same expression twice.
    """
    exposure = PRODUCTION_EXPOSURE
    saturation = SAMPLE_COUNT_SATURATION
    bound = secrets_that_force_saturation()

    def forced(n: int) -> bool:
        return -(-exposure // n) >= saturation  # ceil(exposure / n)

    assert forced(bound), f"the bound itself ({bound}) does not force the threshold"
    assert not forced(bound + 1), f"{bound + 1} secrets still force it, so the bound is one short"
    # And it is the largest such N across the whole range, not just locally at the edge.
    assert all(forced(n) for n in range(1, bound + 1))
    assert not any(forced(n) for n in range(bound + 1, bound + 400))
    assert trial in range(3)  # parametrized to keep the brute force from being a single draw


def test_the_qlwr_status_travels_with_the_numbers():
    """**The anti-lift guard.** The estimate is quotable in isolation; this makes it not misquotable.

    A hardness figure for these parameters fills an obligation about a construction the corpus
    replaced. Nothing in the corpus claims a lattice security level for the deployed scheme — the
    opposite: QLWR occurs zero times in every live profile's documents, and the nearest figure
    anywhere is a budget allocation under the word "suppose". So the number must not be liftable
    into a QPT-128 claim, and the defence is a status string that sits in the same mapping as the
    parameters and in the same JSON as the estimate.
    """
    from qlwr_lattice_stress.problem.production_parameters import (
        QLWR_OBLIGATION_CITATIONS,
        QLWR_STATUS,
    )

    summary = PRODUCTION_PARAMETER_SUMMARY()
    assert summary["qlwr_status"] == QLWR_STATUS
    assert summary["qlwr_obligation_citations"] == list(QLWR_OBLIGATION_CITATIONS)

    # It must say the three things that stop a misquote: not live, what it fills, and what it is not.
    assert "withdrawn" in QLWR_STATUS
    assert "obligation" in QLWR_STATUS
    assert "not a deployed security level" in QLWR_STATUS

    # And it must carry citations, because an uncited status is an assertion.
    assert len(QLWR_OBLIGATION_CITATIONS) >= 4
    assert any("C3.5" in c or "multitrack" in c for c in QLWR_OBLIGATION_CITATIONS)
    assert any("1542-1548" in c for c in QLWR_OBLIGATION_CITATIONS)


def test_the_cli_reports_what_the_number_is_for():
    """The status must reach the machine-readable output, not only the prose around it.

    A consumer that reads ``estimates`` out of the CLI's JSON and ignores the human-facing scope
    string is exactly the consumer that will re-quote the number. Kept as a binding check rather
    than a prose check: it asserts the keys exist in the emitted JSON.
    """
    import json as _json
    import subprocess

    from pathlib import Path as _Path

    # The one legitimate skip, decided *before* the command runs: no estimator, no estimate. What
    # this used to do was skip on any non-zero exit — so a broken command, which is the thing a
    # binding check exists to catch, was reported as a test that had nothing to say.
    _estimator()

    root = _Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "qlwr_lattice_stress.cli", "production-estimate", "--samples", "rows"],
        capture_output=True, text=True, cwd=root, timeout=900,
    )
    assert result.returncode == 0, (
        f"production-estimate exited {result.returncode}: {result.stderr[-400:]}"
    )
    payload = _json.loads(result.stdout)

    assert "what_this_number_is_for" in payload
    assert "obligation_filled" in payload
    assert payload["what_this_number_is_for"] == PRODUCTION_PARAMETER_SUMMARY()["qlwr_status"]
    assert payload["obligation_filled"]
