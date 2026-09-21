"""Whether the estimator agreed with the reductions that were actually run.

The production estimate is an extrapolation from d ~ 130, so what bounds it is whether the model
tracks measurement *inside* the fitted domain. These tests pin the two things that decide how the
recorded discrepancies should be read, and one of them is a correction rather than a confirmation:

* the over-prediction decays monotonically and reaches zero, so it does not carry into the
  extrapolation;
* the single anomaly the pipeline flags is a **search-floor artefact**, not a model disagreement,
  and a per-run comparison cannot see that because it does not know the sweep's floor.

They read the kept sweep records rather than re-running anything, so re-running the sweep with
different dimensions will legitimately change what they assert.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]


def _gap_module():
    """The script, imported by path — it is a script, not a library module."""
    path = _ROOT / "scripts" / "estimator_vs_measured_gap.py"
    spec = importlib.util.spec_from_file_location("_gap", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["_gap"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def points():
    module = _gap_module()
    collected = module._collect(_ROOT / "results")
    if not collected:
        pytest.skip("no sweep runs under results/")
    return collected


def test_the_over_prediction_decays_to_zero_across_the_clean_points(points):
    """The claim the production number rests on, asserted as a trend rather than a point.

    A single agreeing point would say nothing — one dimension matching could be luck. What makes the
    extrapolation defensible is that the *gap itself* shrinks to nothing as the model's regime is
    entered, which is a statement about the sequence.
    """
    clean = [p for p in points if p["estimator_minus_measured"] is not None and not p["at_search_floor"]]
    assert len(clean) >= 3, "too few unclamped points to establish a trend"

    gaps = [p["estimator_minus_measured"] for p in clean]
    dims = [p["dimension"] for p in clean]

    # Monotone non-increasing: each point is no further above the measurement than the last.
    assert all(b <= a for a, b in zip(gaps, gaps[1:])), (dims, gaps)
    # ...and it reaches zero, rather than merely shrinking. That is what makes it a regime effect
    # that ends, rather than a bias that persists and merely gets smaller.
    assert gaps[-1] <= 0, (dims, gaps)
    assert gaps[0] > 0, (dims, gaps)


def test_the_only_flagged_anomaly_is_a_search_floor_artefact(points):
    """**The correction.** The pipeline flags one primal anomaly, and it is clamped.

    ``compare_block_sizes`` uses a 25 % relative tolerance and knows nothing about
    ``block_size_range``. A run that succeeded at the cheapest block size tried has not been shown
    to need that block size — only that the sweep stopped there — so its recorded discrepancy is a
    lower bound, and the flag on it is a statement about the search range.
    """
    flagged = [p for p in points if p["anomaly_flagged_by_the_pipeline"]]
    assert flagged, "the sweep recorded no anomalies at all, so this test would be vacuous"

    clamped = [p for p in flagged if p["at_search_floor"]]
    assert clamped, "expected the flagged set to include a clamped point"
    # Every flagged point that was actually measured must be clamped. A flagged point that is *not*
    # clamped would be a real disagreement with the model and would need explaining.
    measured_and_flagged = [p for p in flagged if p["measured_at_all"]]
    assert all(p["at_search_floor"] for p in measured_and_flagged), (
        "an unclamped point was flagged, which is a genuine model disagreement rather than an "
        "artefact of the search range"
    )


def test_an_unmeasured_point_is_not_reported_as_agreement(points):
    """A run that recovered nothing is an absence of a measurement, not a zero.

    The distinction is load-bearing: recorded as 0 it would read as "needed no reduction at all",
    the strongest possible agreement. It is carried as ``None`` with ``measured_at_all`` false.
    """
    unmeasured = [p for p in points if not p["measured_at_all"]]
    for p in unmeasured:
        assert p["measured_min_block_size"] is None
        assert p["estimator_minus_measured"] is None
        assert p["relative_discrepancy"] is None
        # It is still allowed to carry an anomaly — "the sweep did not reach far enough" is a real
        # outcome and is named rather than hidden.
    assert all(
        p["search_floor"] is not None for p in points
    ), "the search floor must be recorded, or clamping cannot be detected"


def test_a_clamped_point_is_never_counted_as_a_measurement_of_the_gap(points):
    """The clamped points must be excluded from the trend, not averaged into it.

    Including d = 61 would put a lower bound into a sequence of measurements and flatten the trend
    that is the whole finding. Asserted by checking the two sets are disjoint and that the clamped
    set is non-empty — otherwise this exclusion would be doing nothing.
    """
    clamped = {p["run"] for p in points if p["at_search_floor"]}
    clean = {
        p["run"] for p in points
        if p["estimator_minus_measured"] is not None and not p["at_search_floor"]
    }
    assert clamped, "no clamped points found, so excluding them changes nothing and proves nothing"
    assert not (clamped & clean)
