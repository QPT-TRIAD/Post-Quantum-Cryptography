"""The measurement layer: what the circuit does, and what may be concluded from it.

Four questions, each in its own module, and they are separate modules because they have different
failure modes:

* :mod:`~grover_emulator.analysis.success_probability` — does the built circuit amplify the marked
  set the way the closed form says it does? Answers with a curve, a residual summary, and a
  comparison against the exact rational bound where the bound applies.
* :mod:`~grover_emulator.analysis.structural_probes` — does the oracle have structure that makes a
  search the wrong tool? Answers with a firing/no-firing verdict and a mandatory caveat, because a
  probe that stays silent at a simulable width has established much less than a probe that fires.
* :mod:`~grover_emulator.analysis.classical_baseline` — what does the same problem cost a classical
  machine? Counted, not asserted, and labelled as exhaustive search rather than as the best attack.
* :mod:`~grover_emulator.analysis.scaling_extrapolation` — what does the circuit cost beyond the
  widths that can be simulated? Answers with a fit whose outputs are never blended with its inputs.

Every number this layer produces is either measured on a run, exactly computed from a closed form, or
extrapolated from measured points, and it says which. The exact ``Fraction`` computations are exact
because they can be; the extrapolations are labelled because they must be.
"""

from __future__ import annotations

from .classical_baseline import (
    BASELINE_CAVEAT,
    ClassicalBaseline,
    ClassicalSearchMeasurement,
    classical_baseline,
    expected_queries,
    measure_classical_search,
    per_query_cost,
    worst_case_queries,
)
from .scaling_extrapolation import (
    EXTRAPOLATION_CAVEAT_TEMPLATE,
    MIN_FIT_POINTS,
    ExtrapolatedPoint,
    MeasuredPoint,
    ScalingError,
    ScalingFit,
    fit_depth_scaling,
    fit_gate_scaling,
    measured_points_from_sweep,
    predict_gate_count,
    sweep_provenance,
)
from .structural_probes import (
    MEASURED,
    NOT_RUN,
    STRUCTURE_CAVEAT_REFUSED_TEMPLATE,
    STRUCTURE_CAVEAT_TEMPLATE,
    ProbeError,
    ProbeResult,
    qft_period_probe,
    refusal_caveat,
    run_probes,
    simon_style_probe,
    structure_caveat,
    verify_period,
)
from .success_probability import (
    PI_OVER_TWO_UPPER,
    AnalysisError,
    CurvePoint,
    ExactBoundComparison,
    ExactBoundSummary,
    StatevectorBackend,
    SuccessCurve,
    compare_to_exact_bound,
    exact_bound_applicability,
    exact_bound_for_spec,
    exact_success_interval,
    exact_success_lower_bound,
    exact_success_upper_bound,
    fit_residuals,
    marked_probability,
    measured_success_probability,
    sample_counts,
    search_register_probabilities,
    statevector_of,
    success_curve,
    theoretical_success_probability,
)

__all__ = [
    # the error type every module below raises or subclasses
    "AnalysisError",
    # success curve
    "StatevectorBackend",
    "statevector_of",
    "search_register_probabilities",
    "marked_probability",
    "measured_success_probability",
    "theoretical_success_probability",
    "sample_counts",
    "CurvePoint",
    "SuccessCurve",
    "success_curve",
    "fit_residuals",
    # exact bound
    "PI_OVER_TWO_UPPER",
    "exact_success_lower_bound",
    "exact_success_upper_bound",
    "exact_success_interval",
    "exact_bound_applicability",
    "exact_bound_for_spec",
    "ExactBoundComparison",
    "ExactBoundSummary",
    "compare_to_exact_bound",
    # probes
    "ProbeResult",
    "ProbeError",
    "MEASURED",
    "NOT_RUN",
    "STRUCTURE_CAVEAT_TEMPLATE",
    "STRUCTURE_CAVEAT_REFUSED_TEMPLATE",
    "structure_caveat",
    "refusal_caveat",
    "simon_style_probe",
    "qft_period_probe",
    "run_probes",
    "verify_period",
    # classical baseline
    "ClassicalBaseline",
    "ClassicalSearchMeasurement",
    "classical_baseline",
    "expected_queries",
    "worst_case_queries",
    "measure_classical_search",
    "per_query_cost",
    "BASELINE_CAVEAT",
    # scaling
    "ScalingError",
    "ScalingFit",
    "MeasuredPoint",
    "ExtrapolatedPoint",
    "fit_gate_scaling",
    "fit_depth_scaling",
    "predict_gate_count",
    "measured_points_from_sweep",
    "sweep_provenance",
    "MIN_FIT_POINTS",
    "EXTRAPOLATION_CAVEAT_TEMPLATE",
]
