"""Measured minimum block size against the cost model's prediction, at the same scale.

This is the project's central comparison, and the design document is explicit about what a
disagreement means: *"large disagreement here is itself the finding — it means either the
estimator's assumptions do not hold well for your instance's specific structure, or your
embedding/engine has a bug."*

The comparison is deliberately made **at the same scale**: the estimator is run on the scaled
instance that was actually attacked, not on production parameters. Comparing a measurement against a
model evaluated somewhere else would produce a difference that reflects the extrapolation rather
than the physics.

## Silence is a failure

:class:`~qlwr_lattice_stress.protocols.ComparisonResult` refuses to be constructed with a
discrepancy outside tolerance and no named anomaly. That is enforced in the type rather than trusted
to this module, because a comparison that returns quietly while the numbers disagree is
indistinguishable from one that found nothing to compare — and the second is the failure the whole
project exists to avoid.

## The asymmetry found at M7 belongs here

The primal attack reaches and the dual attack does not, at this parameter scale. A comparison that
reported a single "agreement" number would hide that. So the comparison names *which family* it is
about, and a family that does not apply is reported as such rather than as a large discrepancy.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..protocols import (
    NOT_RUN,
    ComparisonResult,
    EstimatorReport,
    Provenance,
    PrimalAttackResult,
)

__all__ = ["compare_block_sizes", "summarise_anomalies", "FAMILY_PRIMAL", "FAMILY_DUAL"]

FAMILY_PRIMAL = "primal_usvp"
FAMILY_DUAL = "dual"


def compare_block_sizes(
    *,
    dimension: int,
    measured_min_block_size: int | None,
    report: EstimatorReport,
    family: str = FAMILY_PRIMAL,
    tolerance_fraction: float = 0.25,
    extra_note: str | None = None,
) -> ComparisonResult:
    """Compare a measured threshold with the model's prediction for the same instance.

    ``tolerance_fraction`` is relative rather than absolute: a discrepancy of 5 block sizes means
    something different at a predicted 20 than at a predicted 200, and an absolute tolerance would
    be lax at one end and harsh at the other.

    A family the estimator reports as **inapplicable** is not a discrepancy. Where the model returns
    an infinite cost the prediction does not exist, and inventing a large discrepancy to represent
    "no prediction" would put a number into the report that no measurement supports.
    """
    if family == FAMILY_PRIMAL:
        predicted = report.beta_usvp
    elif family == FAMILY_DUAL:
        predicted = report.beta_dual
    else:
        raise ValueError(f"unknown attack family {family!r}")

    if predicted is None:
        return ComparisonResult(
            dimension=dimension,
            measured_min_block_size=measured_min_block_size or 0,
            predicted_min_block_size=0,
            discrepancy=0.0,
            tolerance=tolerance_fraction,
            anomaly=None,
            note=(
                f"the estimator reports no block size for the {family} family on this instance, so "
                "there is nothing to compare against. That is an absence of a prediction rather "
                "than agreement with one."
            ),
        )

    if measured_min_block_size is None:
        # The attack did not reach within its sweep. That is a real outcome and it is a *positive*
        # discrepancy — the instance is harder than the sweep covered — so it is named, not hidden.
        return ComparisonResult(
            dimension=dimension,
            measured_min_block_size=0,
            predicted_min_block_size=int(predicted),
            discrepancy=float(predicted),
            tolerance=tolerance_fraction,
            anomaly=(
                f"the {family} attack recovered nothing anywhere in the swept block-size range, "
                f"where the model predicts success at {predicted}. Either the sweep did not reach "
                "far enough or the instance is harder than the model says."
            ),
        )

    relative = (measured_min_block_size - predicted) / max(1, predicted)
    anomaly = None
    if abs(relative) > tolerance_fraction:
        direction = "above" if relative > 0 else "below"
        anomaly = (
            f"the {family} attack needed block size {measured_min_block_size} where the model "
            f"predicts {predicted} — {abs(relative):.0%} {direction} the prediction, outside the "
            f"{tolerance_fraction:.0%} tolerance. A disagreement of this size is a result, not "
            "noise: it means either the model's assumptions do not hold for this instance's "
            "structure, or the embedding or the engine has a defect. Check the planted-vector "
            "test first — it is the cheapest of those to rule out."
        )

    return ComparisonResult(
        dimension=dimension,
        measured_min_block_size=measured_min_block_size,
        predicted_min_block_size=int(predicted),
        discrepancy=relative,
        tolerance=tolerance_fraction,
        anomaly=anomaly,
        note=extra_note,
    )


@dataclass(frozen=True, slots=True)
class AnomalySummary:
    """Every anomaly a run produced, and every comparison that was silent for a stated reason."""

    anomalies: tuple[str, ...]
    not_compared: tuple[str, ...]

    @property
    def has_anomalies(self) -> bool:
        return bool(self.anomalies)

    def describe(self) -> str:
        lines = []
        if self.anomalies:
            lines.append(f"{len(self.anomalies)} anomaly(ies):")
            lines.extend(f"  - {a}" for a in self.anomalies)
        else:
            lines.append("no anomalies: every comparison that ran agreed within tolerance")
        if self.not_compared:
            lines.append(f"{len(self.not_compared)} comparison(s) not made:")
            lines.extend(f"  - {n}" for n in self.not_compared)
        return "\n".join(lines)


def summarise_anomalies(comparisons) -> AnomalySummary:
    """Collect a run's anomalies and its non-comparisons, keeping the two apart.

    Merging them would be the easy thing and the wrong one: "the model and the measurement disagree
    by 300%" and "the model produced no prediction to disagree with" call for different responses,
    and a report that listed them together would invite the second to be read as the first.
    """
    anomalies: list[str] = []
    not_compared: list[str] = []
    for comparison in comparisons:
        if comparison.anomaly:
            anomalies.append(f"dimension {comparison.dimension}: {comparison.anomaly}")
        elif comparison.note:
            not_compared.append(f"dimension {comparison.dimension}: {comparison.note}")
    return AnomalySummary(tuple(anomalies), tuple(not_compared))
