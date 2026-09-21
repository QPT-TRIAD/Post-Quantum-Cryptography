"""The frozen result types every layer exchanges. Written before anything branches.

The sibling Grover project was built by four concurrent agents and then an integration pass. That
pass found three real defects and two measurement traps, **all of them at boundaries**, in modules
that were each green in isolation: a compiler whose two halves disagreed about qubit ordering
without either being wrong alone, a width computed two ways by two layers that each believed the
other, and a test fixture whose docstring — not its code — was the bug.

The lesson is not "test more". It is that a boundary between two components that are validated
against *different references* is exactly where a self-consistent layer cannot see its own error.
So the boundaries are frozen here, as code, with a test that fails when they drift.

Two rules make that work:

**Every result states where its numbers came from.** A ``provenance`` field carries one of
``measured``, ``theoretical_same_scale``, ``extrapolated`` or ``not_run``. The project's central
claim is a comparison between the first and the second, and its central hazard is presenting the
third as though it were the first. Making provenance part of the type means a report cannot blend
them by accident — it has to discard a field to do it.

**A refusal is a result, not an absence.** ``not_run`` carries a reason and, where known, the size
that made it impossible. A run that was skipped and a run that was never attempted look identical
in a results file that only records successes, and the difference is the whole point of the
hardware section.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

__all__ = [
    "Provenance",
    "MEASURED",
    "SAME_SCALE",
    "EXTRAPOLATED",
    "NOT_RUN",
    "PROVENANCE_LABELS",
    "ReducedBasisResult",
    "PrimalAttackResult",
    "DualAttackResult",
    "EstimatorReport",
    "ComparisonResult",
    "ScalingModel",
    "RunResults",
]

#: Where a number came from. Ordered from strongest to weakest evidence; a report that presents a
#: weaker one under a stronger one's heading is the failure this type exists to prevent.
Provenance = Literal["measured", "theoretical_same_scale", "extrapolated", "not_run"]

MEASURED: Provenance = "measured"
SAME_SCALE: Provenance = "theoretical_same_scale"
EXTRAPOLATED: Provenance = "extrapolated"
NOT_RUN: Provenance = "not_run"

#: The heading each provenance is rendered under. Held here rather than in the reporting layer so
#: that a result and its label cannot drift apart: the label is a property of the datum.
PROVENANCE_LABELS: dict[str, str] = {
    MEASURED: "measured",
    SAME_SCALE: "theoretical, same scale",
    EXTRAPOLATED: "extrapolated — not measured",
    NOT_RUN: "not run",
}


@dataclass(frozen=True, slots=True)
class ReducedBasisResult:
    """One reduction run, by one engine, at one block size.

    ``n_tours`` and ``converged`` are recorded because an unreduced-but-converged basis and a run
    truncated at a tour limit look identical in the output otherwise, and they mean different
    things: the first is a result, the second is a bound on how hard the instance might be.

    ``peak_rss_bytes`` is process-wide and monotonic on Linux, so it is an upper bound on the run
    rather than the run's own footprint, and is named accordingly.
    """

    basis: Any  # fpylll.IntegerMatrix; left untyped so this module imports without fpylll
    block_size: int
    wall_clock_s: float
    root_hermite_factor: float | None
    engine: str
    engine_version: str
    threads: int
    n_tours: int | None = None
    converged: bool | None = None
    peak_rss_bytes_upper_bound: int | None = None
    dimension: int | None = None
    provenance: Provenance = MEASURED
    not_run_reason: str | None = None

    def __post_init__(self) -> None:
        if self.provenance == NOT_RUN and not self.not_run_reason:
            raise ValueError(
                "a not_run result must carry its reason; a skipped run and a run that was never "
                "attempted are indistinguishable in a results file that records only successes"
            )


@dataclass(frozen=True, slots=True)
class PrimalAttackResult:
    """Whether uSVP recovery succeeded at one block size, and what it cost.

    ``recovered`` is exact-vector equality against the planted vector, never a norm threshold or an
    ``allclose``: a "close" vector is a different vector, and the attack either found the secret or
    it did not.
    """

    dimension: int
    block_size: int
    recovered: bool
    wall_clock_s: float
    root_hermite_factor: float | None = None
    recovered_vector: tuple[int, ...] | None = None
    embedding_factor: int | None = None
    engine: str | None = None
    #: Threads the engine **actually ran with**, not the number requested — the same rule
    #: ``ReducedBasisResult.threads`` follows, and for a sharper reason here. G6K is bit-reproducible
    #: at one thread and is not above it (measured; see that engine's module docstring). A sweep's
    #: minimum block size is therefore a *measurement* at one thread and a single draw at four, and
    #: without this field the two are indistinguishable in a results file.
    threads: int | None = None
    provenance: Provenance = MEASURED
    not_run_reason: str | None = None


@dataclass(frozen=True, slots=True)
class DualAttackResult:
    """A distinguishing statistic against real samples, and against a known-uniform control.

    The control is not optional. A distinguisher that fires on everything, including genuinely
    uniform samples, is a broken distinguisher that would otherwise read as a successful attack —
    the same reasoning as the sibling project's negative control, which turned out to be marking a
    set where the probe *should* have fired.
    """

    dimension: int
    block_size: int
    advantage: float
    control_advantage: float
    wall_clock_s: float
    n_samples: int | None = None
    engine: str | None = None
    provenance: Provenance = MEASURED
    not_run_reason: str | None = None


@dataclass(frozen=True, slots=True)
class EstimatorReport:
    """The cost models' answer, for the parameters it was given.

    ``provenance`` is ``theoretical_same_scale`` when the parameters are the scaled instance that
    was also attacked, and ``extrapolated`` when they are production parameters that were not. The
    same class carries both, so the field is load-bearing rather than decorative.
    """

    beta_usvp: int | None
    beta_dual: int | None
    rop_usvp_log2: float | None
    rop_dual_log2: float | None
    rop_classical_log2_min: float | None
    rop_quantum_log2_min: float | None
    minimum_over_models: str | None
    model_parameters: dict[str, Any] = field(default_factory=dict)
    estimator_revision: str | None = None
    red_cost_model: str | None = None
    red_shape_model: str | None = None
    provenance: Provenance = SAME_SCALE
    not_run_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Measured minimum successful block size against the model's prediction for the same instance.

    ``anomaly`` may not be ``None`` by accident. Returning ``None`` asserts that the two agree
    inside ``tolerance``, and the constructor enforces that: a comparison that is silent while the
    numbers disagree is indistinguishable from one that found nothing to compare.
    """

    dimension: int
    measured_min_block_size: int
    predicted_min_block_size: int
    discrepancy: float
    tolerance: float
    anomaly: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        agrees = abs(self.discrepancy) <= self.tolerance
        if agrees and self.anomaly is not None:
            raise ValueError("an agreement within tolerance must not also report an anomaly")
        if not agrees and not self.anomaly:
            raise ValueError(
                f"a discrepancy of {self.discrepancy:+.3f} outside the {self.tolerance} tolerance "
                "must be named as an anomaly; silence here is the failure this check exists for"
            )


@dataclass(frozen=True, slots=True)
class ScalingModel:
    """A core-SVP fit, with the domain it was fitted on.

    The domain is not documentation. Core-SVP is a model of sieving cost and says nothing about the
    enumeration regime, so extrapolating below the fitted block sizes is a category error rather
    than an inaccuracy — hence ``extrapolates_outside_fitted_domain`` as a required judgement the
    report has to face.
    """

    c: float
    intercept: float
    r_squared: float
    fitted_beta_min: int
    fitted_beta_max: int
    n_points: int
    extrapolates_outside_fitted_domain: bool
    provenance: Provenance = MEASURED
    note: str | None = None


class RunResults(TypedDict, total=False):
    """What a run writes to ``metrics.json`` and what the report generator reads back.

    A ``TypedDict`` rather than a dataclass because this is the *serialisation* boundary: it must
    survive a round-trip through JSON, which a frozen dataclass holding an ``IntegerMatrix`` cannot.
    The sibling project's report generator rounds-trips this way deliberately, so that a report can
    be regenerated from a stored results directory and checked against the live one.
    """

    run_id: str
    kind: str
    created_utc: str
    seed: int
    seeds: dict[str, Any]
    config: dict[str, Any]
    environment: dict[str, Any]
    instance: dict[str, Any]
    scaling_rule: dict[str, Any]
    attacks: list[dict[str, Any]]
    estimator_same_scale: dict[str, Any]
    estimator_production: dict[str, Any]
    comparisons: list[dict[str, Any]]
    scaling: dict[str, Any]
    sweep: list[dict[str, Any]]
    not_run: list[dict[str, Any]]
    notes: list[str]
