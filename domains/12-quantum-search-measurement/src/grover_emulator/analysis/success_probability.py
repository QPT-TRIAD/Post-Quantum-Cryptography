"""The success curve, the closed form, and the exact rational bound that brackets both.

**Three numbers per iteration count, and they are not interchangeable.** For every ``k`` this module
can report:

1. ``p_measured`` — the probability of reading a marked value from the circuit that was built and
   run, obtained by summing the exact statevector's ``|amplitude|^2`` over the marked basis states;
2. ``p_closed_form`` — ``sin^2((2k+1) * theta)`` with ``theta = arcsin(sqrt(M/N))``, from
   :mod:`grover_emulator.problem.search_space`, which knows nothing about circuits;
3. the exact rational **interval** that provably contains (2), computed in ``fractions`` arithmetic
   with no float anywhere, which is the only exact statement available about ``sin^2`` of a
   transcendental argument.

(3) is why this module exists in the shape it does. A measured curve compared against a *float*
closed form is a float compared against a float, and the comparison then has the same status as the
arithmetic inside the thing it is checking. ``sin y`` for ``y in [0, pi/2]`` has a lower-bounding
partial sum ``y - y**3/6`` (an alternating series with strictly decreasing terms, so truncating after
the second term undershoots) and an upper bound ``y``; both are rational whenever ``y`` is, and
``y = (2k+1) * 2**(-n/2)`` is rational exactly when the density exponent is even. So the exact
statement this module can make about a measured point is

    ``lower <= p_measured <= upper``

with both endpoints ``Fraction`` objects and the comparison performed in ``Fraction`` arithmetic —
the float is never converted *to* the bound, and the bound is never rounded *into* a float. The
condition for evaluability is named and reported rather than assumed: an odd density exponent has no
rational ``sin(theta)`` and is a refusal, and ``y`` above ``pi/2`` leaves the range in which the
series argument holds, which is also a refusal. Outside it the bound is *undefined*, not
wide — :func:`compare_to_exact_bound` records those points as skipped with the reason, because a
bound silently omitted from a table reads as a bound that was met.

**The iteration range is taken from the builder, never chosen here.** ``derive_iteration_range``
returns ``[0, k_opt + extra]`` for the spec's own ``k_opt = floor(pi/4 * sqrt(N/M))``. At the
smallest structurally faithful QLWR instance that is ``k_opt = 50``, and a fixed ``[0, 40]`` returns
a smooth, monotone, entirely plausible rising curve that never reaches its peak and supports no
conclusion. :func:`success_curve` therefore records whether the window it was given actually
contains the closed form's peak, and says so out loud when it does not.

**Agreement between (1) and (2) checks the harness, not the physics.** A diagonal phase oracle
contributes nothing to the curve: the curve is a function of ``(M, N)`` alone, so an engine running
that oracle reproduces a number the closed form already has exactly. What the circuit contributes is
that it certifies ``M`` and that it costs something — the agreement asserted here is a check that the
circuit, the backend and the simulator are wired to the same problem.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol, Sequence, runtime_checkable

import numpy as np

from ..circuits.grover_circuit_builder import (
    build_grover_circuit,
    derive_iteration_range,
    optimal_iterations,
)
from ..circuits.ir import GateList
from ..problem.oracle_spec import Lowering, OracleSpec
from ..utils.seeding import derive_seed, rng_for

__all__ = [
    "AnalysisError",
    "StatevectorBackend",
    "statevector_of",
    "search_register_probabilities",
    "marked_probability",
    "measured_success_probability",
    "theoretical_success_probability",
    "sample_counts",
    "SuccessCurve",
    "success_curve",
    "fit_residuals",
    "PI_OVER_TWO_UPPER",
    "exact_success_lower_bound",
    "exact_success_upper_bound",
    "exact_success_interval",
    "exact_bound_applicability",
    "ExactBoundComparison",
    "ExactBoundSummary",
    "compare_to_exact_bound",
    "exact_bound_for_spec",
]


class AnalysisError(RuntimeError):
    """A measurement could not be taken as asked — a refusal, not a fallback."""


# -----------------------------------------------------------------------------------------------
# the backend contract
# -----------------------------------------------------------------------------------------------


@runtime_checkable
class StatevectorBackend(Protocol):
    """The one thing the analysis layer needs from an engine.

    ``statevector(circuit)`` returns the exact final amplitudes of the gate list, as a complex array
    of length ``2**circuit.num_qubits``, indexed little-endian: bit ``q`` of the index is qubit
    ``q``. That convention is the IR's (see :mod:`grover_emulator.circuits.ir`) and it is the same
    one the frameworks use, so no index reversal is needed anywhere.

    Requiring exactly one method is deliberate. A curve, a probe and a baseline all need the same
    thing — the amplitudes of a circuit that was built from this project's IR — and a wider
    interface would let this layer depend on how a particular engine happens to be driven rather
    than on what it computes. Measurement is not part of the contract: sampling a known distribution
    is classical post-processing, and :func:`sample_counts` does it here, seeded, so that the
    statistics of a run are reproducible from the run's own seed.
    """

    def statevector(self, circuit: GateList) -> np.ndarray:  # pragma: no cover - protocol
        ...


_STATEVECTOR_METHODS = (
    "statevector",
    "amplitudes",
    "state_vector",
    "get_statevector",
    "run_statevector",
)
"""Method names accepted, in order. The first is the contract; the rest keep a backend written
against a different spelling usable rather than forcing a wrapper, in the same spirit as the report
renderer's tolerant readers. ``run_statevector`` is the engines in
:mod:`grover_emulator.backends`, which return a result object rather than a bare array — see
:data:`_STATEVECTOR_ATTRIBUTES` for how that is unwrapped.

The order is not alphabetical and must not become so: ``statevector`` is the contract, and a backend
that offered both a bare array and a result object would be asked for the bare array first."""

_STATEVECTOR_ATTRIBUTES = ("statevector",)
"""Attribute names a returned *result object* may carry the amplitudes under.

Unwrapping happens here, once, rather than in every caller: a run asks an engine for amplitudes and
should not have to know whether the answer arrived as an array or inside an envelope with the
circuit's accounting attached. The envelope's other fields are the caller's to ignore — this layer
counts gates from the IR itself when it needs a count, and never from an engine's own report."""


NORM_TOLERANCE = {"double": 1e-9, "single": 1e-6}
"""How far from 1 a returned statevector's norm may sit, by the precision the engine declares.

The check exists to catch a circuit that is not the unitary it was given — a dropped qubit, a
non-unitary ``PERM`` — and those miss by parts in a hundred, not parts in a million. What the
tolerance has to clear is rounding, and rounding depends on the engine: a double-precision engine's
norm is good to about ``1e-15`` and is held to ``1e-9``; qsim holds ``complex64`` amplitudes, whose
norm error was measured at ``1e-8`` to ``3e-8`` on this project's probe circuits and at ``1.0e-7``
on a 4588-gate, 13-qubit Grover circuit — it grows with the gate count — so a single bound at
``1e-9`` refused every circuit that engine ran, and ``1e-7`` would refuse the long ones. The
single-precision bound is applied **only** to an engine that says it is single precision — it is
not a loosening for Aer or the reference simulator, where a norm off by ``1e-7`` is still a defect
and is still refused."""


def _declared_precision(backend: object, result: object) -> str:
    """``"single"`` or ``"double"``, from what the engine says about itself — never from the norm.

    Three declarations are read, most specific first: the ``precision`` a result envelope records for
    the run that produced it (``BackendResult.framework``), the engine's own ``bytes_per_amplitude``
    (8 is ``complex64``), and the dtype of a bare array. Anything that declares nothing is double,
    which is the strict bound: an engine has to claim single precision to be given its tolerance.
    """
    framework = getattr(result, "framework", None)
    if isinstance(framework, dict) and framework.get("precision") in NORM_TOLERANCE:
        return framework["precision"]
    if getattr(backend, "bytes_per_amplitude", None) == 8:
        return "single"
    if getattr(result, "dtype", None) in (np.dtype(np.complex64), np.dtype(np.float32)):
        return "single"
    return "double"


def statevector_of(backend: object, circuit: GateList) -> np.ndarray:
    """The exact final amplitudes of ``circuit``, validated before anything is computed from them.

    The validation is not defensive decoration. An engine that returned a vector for the *search
    register only* would produce a success probability that is right, a probe marginal that is right,
    and a silent disagreement with the circuit's declared width — and the disagreement would surface
    as a numerical puzzle somewhere downstream rather than as a refusal here.

    Raises:
        AnalysisError: if the backend exposes no statevector method, if the returned array is not
            one amplitude per basis state of the declared width, or if it is not normalised to
            within :data:`NORM_TOLERANCE` for the precision the engine declares.
    """
    for name in _STATEVECTOR_METHODS:
        method = getattr(backend, name, None)
        if callable(method):
            raw = method(circuit)
            break
    else:
        raise AnalysisError(
            f"{type(backend).__name__} exposes none of {_STATEVECTOR_METHODS}; the analysis layer "
            "needs exact amplitudes and cannot substitute counts or a classical trajectory for them"
        )

    # Read before the envelope is unwrapped: the run's declared precision travels on the result
    # object, and the bare array that replaces it below has already been widened to complex128.
    precision = _declared_precision(backend, raw)
    for attribute in _STATEVECTOR_ATTRIBUTES:
        if not isinstance(raw, np.ndarray) and hasattr(raw, attribute):
            raw = getattr(raw, attribute)
            break
    statevector = np.asarray(raw, dtype=complex)
    expected = 1 << circuit.num_qubits
    if statevector.shape != (expected,):
        raise AnalysisError(
            f"{type(backend).__name__} returned {statevector.shape} for a "
            f"{circuit.num_qubits}-qubit circuit ({circuit.label!r}); expected ({expected},). A "
            "statevector over a subset of the qubits is a different state, and every probability "
            "derived from it would be a probability of the wrong event."
        )
    norm = float(np.linalg.norm(statevector))
    if abs(norm - 1.0) > NORM_TOLERANCE[precision]:
        raise AnalysisError(
            f"{type(backend).__name__} returned a non-normalised statevector (norm {norm:.12f}, "
            f"tolerance {NORM_TOLERANCE[precision]:g} for a {precision}-precision engine); "
            "the circuit it ran is not the unitary gate list it was given"
        )
    if precision == "single":
        # Inside its tolerance, a single-precision engine's norm drift is a common factor that
        # rounding put on every amplitude. It is divided out here, once, so that every later check
        # on the *distribution* (`sample_counts` requires probabilities summing to 1 within 1e-9)
        # stays at double-precision strictness for every engine instead of being loosened for all
        # of them. No ratio of probabilities changes; a double-precision vector is never touched.
        statevector = statevector / norm
    return statevector


# -----------------------------------------------------------------------------------------------
# probabilities
# -----------------------------------------------------------------------------------------------


def search_register_probabilities(statevector: np.ndarray, n_search: int) -> np.ndarray:
    """``p(x)`` over the search register: ``|amplitude|^2`` marginalised over everything above it.

    The search register occupies the low ``n_search`` bits of the index, so the marginal is a sum
    over the leading axis of the ``(rest, search)`` reshape. The ancillas and the flag are traced
    out rather than assumed clean: for the oracle sandwich they *are* clean, and a measurement taken
    without relying on that is one that would still be right if the property ever stopped holding.
    """
    statevector = np.asarray(statevector, dtype=complex)
    length = int(statevector.shape[0]) if statevector.ndim else 0
    if length < 1 or length & (length - 1):
        raise AnalysisError(
            f"a statevector of length {length} is not a power of two of amplitudes"
        )
    total_qubits = length.bit_length() - 1
    if not 0 < n_search <= total_qubits:
        raise AnalysisError(f"search width {n_search} does not fit a {total_qubits}-qubit state")
    probabilities = np.sum(np.abs(statevector.reshape(-1, 1 << n_search)) ** 2, axis=0)
    return probabilities


def marked_probability(probabilities: np.ndarray, marked: frozenset[int] | set[int]) -> float:
    """Sum of ``p`` over the marked values — the probability of measuring a solution."""
    if not marked:
        raise AnalysisError("the marked set is empty; there is no success event to measure")
    highest = max(marked)
    if highest >= probabilities.shape[0]:
        raise AnalysisError(
            f"a marked value ({highest}) lies outside a {probabilities.shape[0]}-state register"
        )
    return float(sum(probabilities[x] for x in marked))


def measured_success_probability(
    spec: OracleSpec,
    backend: object,
    n_iterations: int | None = None,
    lowering: Lowering = Lowering.TRUTH_TABLE,
) -> float:
    """The measured probability of reading the marked set after ``n_iterations`` rounds.

    ``n_iterations=None`` means the spec's own optimum. No measurement is appended to the circuit:
    the IR is unitary and the backend returns amplitudes, so the probability is read off the exact
    final state rather than estimated from shots.
    """
    circuit = build_grover_circuit(spec, n_iterations, lowering)
    statevector = statevector_of(backend, circuit)
    probabilities = search_register_probabilities(statevector, spec.search_width())
    return marked_probability(probabilities, spec.marked_set())


def theoretical_success_probability(spec: OracleSpec, n_iterations: int) -> float:
    """``sin^2((2k+1) * theta)`` for this spec's own ``M`` and ``N``."""
    return spec.space().success_probability(n_iterations)


def sample_counts(
    probabilities: np.ndarray,
    shots: int,
    *parts: str | int | bytes | None,
) -> dict[int, int]:
    """Draw ``shots`` outcomes from ``probabilities`` under a seed derived from ``parts``.

    Sampling lives here rather than in a backend for the same reason the seed does: the statistics of
    a run are a property of the run, so they have to be reproducible from the run's own record. The
    seed is derived (never drawn) from the description passed in, so two runs that measured the same
    curve at the same width sample the same outcomes.
    """
    if shots < 1:
        raise AnalysisError(f"shots must be >= 1, got {shots}")
    probabilities = np.asarray(probabilities, dtype=float)
    total = float(probabilities.sum())
    if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-12):
        raise AnalysisError(
            f"outcome probabilities sum to {total:.12f}; a distribution that does not is a state "
            "that was never normalised"
        )
    rng = rng_for(derive_seed("analysis/sample_counts", *parts, shots))
    draws = rng.choice(probabilities.shape[0], size=shots, p=probabilities / total)
    values, counts = np.unique(draws, return_counts=True)
    return {int(v): int(c) for v, c in zip(values, counts)}


# -----------------------------------------------------------------------------------------------
# the curve
# -----------------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CurvePoint:
    """One point of a success curve, with the provenance of each number written next to it."""

    iteration: int
    measured: float
    closed_form: float
    sampled: float | None = None
    shots: int = 0
    """Shots behind :attr:`sampled`. Zero means the sampled estimator was not asked for."""

    @property
    def residual(self) -> float:
        """``measured - closed_form``. A difference of two floats, and labelled as one."""
        return self.measured - self.closed_form

    def to_dict(self) -> dict:
        """The record the report renders: ``iteration``, ``empirical_*``, ``theoretical_*``."""
        record = {
            "iteration": self.iteration,
            "empirical_p_success": self.measured,
            "theoretical_p_success": self.closed_form,
            "residual": self.residual,
            "sampled_p_success": self.sampled,
            "shots": self.shots,
            "provenance": {
                "empirical_p_success": "measured (exact statevector)",
                "theoretical_p_success": "closed form sin^2((2k+1)theta)",
                "sampled_p_success": "measured (shots)" if self.sampled is not None else "not taken",
            },
        }
        return record


@dataclass(frozen=True)
class SuccessCurve:
    """A measured curve, the closed form it is compared against, and where the window stopped.

    ``window_contains_closed_form_peak`` is not decoration. The whole failure mode this project
    guards against is a curve that rises smoothly across a window that never reached the peak: it
    looks exactly like a result, and the only thing that distinguishes it from one is knowing where
    the peak is. That number is derived per instance from ``M`` and ``N``, and this record carries
    it so a reader never has to reconstruct whether the window was long enough.
    """

    spec_name: str
    search_width: int
    n_items: int
    n_marked: int
    optimal_iterations: int
    iteration_range: tuple[int, int]
    lowering: str
    points: tuple[CurvePoint, ...]
    window_contains_closed_form_peak: bool

    @property
    def records(self) -> list[dict]:
        """The list of records, as the report's ``curve`` section expects it."""
        return [point.to_dict() for point in self.points]

    @property
    def peak_measured(self) -> CurvePoint:
        return max(self.points, key=lambda point: point.measured)

    @property
    def peak_closed_form(self) -> CurvePoint:
        return max(self.points, key=lambda point: point.closed_form)

    @property
    def residuals(self) -> dict:
        """The residual summary, labelled as a fit wherever the report prints it."""
        return fit_residuals(self.records)

    def exact_bound_comparison(self) -> ExactBoundSummary:
        """Place this curve against the exact rational interval, point by point.

        The density exponent comes from the curve's own ``M``, so the bound is evaluated for the
        marked set the circuit implements rather than for one a caller re-states. A marked-set size
        that is not a power of two is a refusal from :func:`exact_bound_for_spec`, not a wider bound.
        """
        if self.n_marked & (self.n_marked - 1):
            raise AnalysisError(
                f"M={self.n_marked} is not a power of two; the density exponent is undefined and no "
                "exact rational bound exists for this curve"
            )
        return compare_to_exact_bound(
            self.records,
            log2_targets=self.n_marked.bit_length() - 1,
            n_bits=self.search_width,
        )

    def describe(self) -> dict:
        """Scalar facts plus the records, for a results file."""
        return {
            "spec": self.spec_name,
            "search_width": self.search_width,
            "n_items": self.n_items,
            "n_marked": self.n_marked,
            "optimal_iterations": self.optimal_iterations,
            "iteration_range": list(self.iteration_range),
            "lowering": self.lowering,
            "window_contains_closed_form_peak": self.window_contains_closed_form_peak,
            "peak_measured": {
                "iteration": self.peak_measured.iteration,
                "p_success": self.peak_measured.measured,
            },
            "peak_closed_form": {
                "iteration": self.peak_closed_form.iteration,
                "p_success": self.peak_closed_form.closed_form,
            },
            "curve": self.records,
        }


def success_curve(
    spec: OracleSpec,
    backend: object,
    iteration_range: range | None = None,
    lowering: Lowering = Lowering.TRUTH_TABLE,
    shots: int = 0,
    seed_parts: Sequence[str | int | bytes | None] = (),
) -> SuccessCurve:
    """The measured curve and the closed form, point by point.

    Args:
        spec: the oracle.
        backend: anything satisfying :class:`StatevectorBackend`.
        iteration_range: defaults to the range derived from this spec's own optimum. A shorter range
            is accepted and *reported*: the returned curve carries whether it contained the peak,
            and a warning names the optimum, because a truncated window is the single failure this
            project is built to avoid and it is invisible in the numbers themselves.
        lowering: which oracle lowering to run.
        shots: shots for the sampled estimator; zero skips it.
        seed_parts: identifies this run's sampling, so the same run replays its own statistics.

    The builder warns once per circuit when ``k`` is below the optimum, which over a sweep of 53
    points is 50 copies of the same warning followed by two silent ones — a stream that trains a
    reader to ignore it. The build is therefore made quiet here and the *window-level* fact is
    warned about once, which is the fact that matters.
    """
    space = spec.space()
    if iteration_range is None:
        iteration_range = derive_iteration_range(spec)
    if len(iteration_range) == 0:
        raise AnalysisError("the iteration range is empty; there is no curve to measure")
    k_opt = optimal_iterations(spec)

    peak_index = space.first_peak_iteration(max(iteration_range))
    window_contains_peak = peak_index is not None and peak_index in iteration_range
    if not window_contains_peak:
        warnings.warn(
            f"the iteration window [{iteration_range.start}, {iteration_range[-1]}] does not "
            f"contain the closed form's peak (this instance's optimum is k_opt={k_opt}); across "
            "this window the curve rises monotonically, which looks like a result and is not one",
            stacklevel=2,
        )

    points: list[CurvePoint] = []
    for k in iteration_range:
        with warnings.catch_warnings():
            # See the docstring: the per-circuit warning is the same sentence 50 times over a sweep,
            # and the window-level check above is the one with content.
            warnings.simplefilter("ignore", UserWarning)
            circuit = build_grover_circuit(spec, k, lowering)
        statevector = statevector_of(backend, circuit)
        probabilities = search_register_probabilities(statevector, spec.search_width())
        measured = marked_probability(probabilities, spec.marked_set())

        sampled: float | None = None
        if shots > 0:
            counts = sample_counts(probabilities, shots, spec.name, spec.search_width(), k, *seed_parts)
            sampled = sum(count for value, count in counts.items() if spec.is_marked(value)) / shots

        points.append(
            CurvePoint(
                iteration=k,
                measured=measured,
                closed_form=space.success_probability(k),
                sampled=sampled,
                shots=shots,
            )
        )

    return SuccessCurve(
        spec_name=spec.name,
        search_width=spec.search_width(),
        n_items=space.n_items,
        n_marked=space.n_marked,
        optimal_iterations=k_opt,
        iteration_range=(iteration_range.start, iteration_range[-1]),
        lowering=lowering.value if isinstance(lowering, Lowering) else str(lowering),
        points=tuple(points),
        window_contains_closed_form_peak=window_contains_peak,
    )


def fit_residuals(records: Sequence[dict]) -> dict:
    """How far the measured curve departs from the closed form, as a summary — not a fit parameter.

    Everything here is ``[extrapolated]`` in the report's sense: these numbers summarise a
    comparison, and none of them is a measurement of anything. They are reported because the size of
    the departure is the thing a reader wants before trusting that the harness measured the same
    problem the closed form describes — a departure of ``1e-15`` is float noise, and one of ``1e-3``
    is a bug or a finding.

    Magnitudes alone leave that last judgement to the reader, and a mean or an rms is exactly where
    one bad point gets averaged away. So when the records carry a shot count the summary also makes
    the comparison itself, point by point, and says so in ``deviation_significant``: a point is
    flagged when it sits further from the closed form than :data:`SIGNIFICANCE_SIGMAS` binomial
    standard deviations ``sqrt(p(1-p)/shots)`` at that point's own ``p`` and ``shots``, plus one
    count (``1/shots``) of slack — where ``p`` is within a count of 0 or 1 the standard deviation
    understates the granularity of a count. Both measured columns are judged: the curve being
    summarised (``empirical_p_success``) and, where it was taken, ``sampled_p_success``. The
    sampled column is the one the binomial model describes; the summarised column is held to the
    same bound because a departure that sampling noise could not explain is significant whichever
    column it shows up in. It is a one-sided test: ``False`` means "nothing here exceeds what
    ``shots`` samples would scatter by", not "the curves agree" — an exact-statevector column that
    is ``1e-3`` off stays below a 20000-shot bound, and the magnitudes above are still what reports
    it. With no shot count in the records there is no sampling noise to judge against, and the flag
    is ``None`` rather than a reassuring ``False``.
    """
    measured = [
        (int(record["iteration"]), float(record["empirical_p_success"]))
        for record in records
        if record.get("empirical_p_success") is not None
    ]
    closed_form = [
        (int(record["iteration"]), float(record["theoretical_p_success"]))
        for record in records
        if record.get("theoretical_p_success") is not None
    ]
    if not measured or not closed_form:
        raise AnalysisError("a residual summary needs both a measured and a closed-form curve")

    residuals = np.asarray([m - t for (_, m), (_, t) in zip(measured, closed_form)], dtype=float)
    k_measured, p_measured = max(measured, key=lambda pair: pair[1])
    k_theory, p_theory = max(closed_form, key=lambda pair: pair[1])
    significant, worst_ratio, flagged = _deviation_significance(records)
    return {
        "n_points": len(residuals),
        "max_abs_residual": float(np.max(np.abs(residuals))),
        "rms_residual": float(np.sqrt(np.mean(residuals**2))),
        "mean_residual": float(np.mean(residuals)),
        "peak_iteration_measured": k_measured,
        "peak_iteration_closed_form": k_theory,
        "peak_p_measured": float(p_measured),
        "peak_p_closed_form": float(p_theory),
        "peak_iteration_agrees": bool(k_measured == k_theory),
        "deviation_significant": significant,
        "significance_threshold_sigmas": SIGNIFICANCE_SIGMAS,
        "max_residual_over_noise_bound": worst_ratio,
        "significant_iterations": flagged,
        "provenance": "fit (a summary of the measured curve against the closed form)",
    }


SIGNIFICANCE_SIGMAS = 5.0
"""How many binomial standard deviations a point may sit from the closed form before it is flagged.

Five, not two or three: a curve is a dozen points judged together, and the flag is meant to be read
as "this is not sampling noise" without a multiple-comparisons footnote. At five sigma a genuine
sampled curve of any length this project produces essentially never fires it."""


def _deviation_significance(records: Sequence[dict]) -> tuple[bool | None, float | None, list[int]]:
    """``(flag, worst |residual| / bound, flagged iterations)`` against binomial sampling noise.

    See :func:`fit_residuals` for what the bound is and why both measured columns are held to it.
    Records without a positive ``shots`` are skipped — they have no sampling noise to compare with —
    and when that is all of them the answer is ``(None, None, [])``: not judged, which is a
    different fact from judged-and-quiet.
    """
    worst: float | None = None
    flagged: list[int] = []
    for record in records:
        shots = record.get("shots")
        p = record.get("theoretical_p_success")
        if not shots or shots <= 0 or p is None:
            continue
        p = float(p)
        bound = SIGNIFICANCE_SIGMAS * math.sqrt(max(p * (1.0 - p), 0.0) / shots) + 1.0 / shots
        for column in ("empirical_p_success", "sampled_p_success"):
            value = record.get(column)
            if value is None:
                continue
            ratio = abs(float(value) - p) / bound
            worst = ratio if worst is None else max(worst, ratio)
            if ratio > 1.0 and int(record["iteration"]) not in flagged:
                flagged.append(int(record["iteration"]))
    if worst is None:
        return None, None, []
    return bool(flagged), float(worst), flagged


# -----------------------------------------------------------------------------------------------
# the exact rational bound
# -----------------------------------------------------------------------------------------------

PI_OVER_TWO_UPPER = Fraction(15708, 10000)
"""An exact rational **upper** bound on ``pi/2`` (1.5707963267948966...).

Kept as a ``Fraction`` so that the domain check on the bound below is an exact comparison. Testing
``y <= float(pi/2)`` would make the domain of an exact statement depend on a float, which is the one
thing this section exists to avoid."""


def _bound_argument(n_bits: int, iterations: int, log2_targets: int) -> Fraction:
    """``y = (2k+1) * 2**(-exp2/2)``, exactly — the argument the whole bound turns on.

    ``exp2 = n_bits - log2_targets`` is the density exponent: ``sin(theta) = 2**(-exp2/2)`` is
    rational exactly when ``exp2`` is even, which is the precondition of every function below.
    """
    if n_bits < 1:
        raise ValueError(f"n_bits must be >= 1, got {n_bits}")
    if type(iterations) is not int or iterations < 0:
        raise ValueError(f"iterations must be a non-negative integer, got {iterations!r}")
    if type(log2_targets) is not int or log2_targets < 0:
        raise ValueError(f"log2_targets must be a non-negative integer, got {log2_targets!r}")
    exp2 = n_bits - log2_targets
    if exp2 <= 0:
        raise ValueError(
            f"the marked set fills the search space (n_bits={n_bits}, log2_targets={log2_targets}); "
            "sin(theta) = 1 and there is nothing to amplify"
        )
    if exp2 % 2:
        raise ValueError(
            f"the density exponent {exp2} is odd, so sin(theta) = 2**(-{exp2}/2) is irrational and "
            "no exact rational bound exists at this width; a float here would be the bound's "
            "accuracy masquerading as the bound"
        )
    y = Fraction(2 * iterations + 1, 1 << (exp2 // 2))
    if y > PI_OVER_TWO_UPPER:
        raise ValueError(
            f"(2k+1) * sin(theta) = {float(y):.9f} exceeds pi/2, where the series that lower-bounds "
            "sin falls outside the range it is valid on; the bound is undefined past the first peak "
            "rather than merely loose, and reporting the largest undefined point as zero would read "
            "as a bound the curve failed"
        )
    return y


def exact_success_lower_bound(n_bits: int, iterations: int, log2_targets: int = 0) -> Fraction:
    """Exactly-rational lower bound on ``sin^2((2k+1) * theta)``, with ``sin(theta) = 2**-(exp2/2)``.

    ``sin y >= y - y**3/6`` for ``y in [0, pi/2]``: the alternating series for ``sin`` has terms
    strictly decreasing in magnitude over that range (the ratio of successive terms is at most
    ``y**2/6 <= 0.41``), so truncating after the second term undershoots, and squaring preserves the
    inequality because both sides are in ``[0, 1]``.

    Args:
        n_bits: the width of the search register, ``n``.
        iterations: the iteration count, ``k``.
        log2_targets: ``log2(M)``. The bound requires ``M`` to be a power of four so that the
            density exponent is even; for ``M = 1`` pass zero, which is the QLWR instance's case.

    Returns:
        A :class:`~fractions.Fraction` at most ``sin^2((2k+1)*theta)``, and never a float.

    Raises:
        ValueError: if the density exponent is positive but odd, or if ``(2k+1) * sin(theta)``
            exceeds ``pi/2``. Both are refusals of the *domain*, and both are reported by
            :func:`exact_bound_applicability` rather than being left for a caller to discover.
    """
    y = _bound_argument(n_bits, iterations, log2_targets)
    shortfall = y - y**3 / 6
    return shortfall * shortfall


def exact_success_upper_bound(n_bits: int, iterations: int, log2_targets: int = 0) -> Fraction:
    """Exactly-rational upper bound on the same quantity: ``y**2 >= sin^2(y)`` for ``y >= 0``.

    ``sin y <= y`` pointwise, and squaring both sides of an inequality between non-negative numbers
    preserves it. The pair gives an enclosure rather than a one-sided check, which is what lets a
    measured value be *placed* rather than merely cleared.
    """
    y = _bound_argument(n_bits, iterations, log2_targets)
    return y * y


def exact_success_interval(
    n_bits: int, iterations: int, log2_targets: int = 0
) -> tuple[Fraction, Fraction]:
    """``(lower, upper)`` — an exactly-rational interval containing ``sin^2((2k+1)*theta)``."""
    return (
        exact_success_lower_bound(n_bits, iterations, log2_targets),
        exact_success_upper_bound(n_bits, iterations, log2_targets),
    )


def exact_bound_applicability(
    n_bits: int, iterations: int, log2_targets: int = 0
) -> tuple[bool, str]:
    """Whether the exact bound exists at this point, and if not, why not.

    Returned rather than raised so that a curve-wide comparison can record the points it skipped
    with their reason. A point silently missing from a comparison table reads exactly like a point
    the bound was met at.
    """
    try:
        _bound_argument(n_bits, iterations, log2_targets)
    except ValueError as exc:
        return False, str(exc)
    return True, ""


@dataclass(frozen=True, slots=True)
class ExactBoundComparison:
    """One point, compared against the exact interval in exact arithmetic.

    :attr:`meets_lower` and :attr:`within_interval` are computed on ``Fraction`` objects: the
    measured probability is a float, which *is* an exact dyadic rational, and it is compared against
    a bound that never became a float. What that buys is that the comparison carries no rounding
    error of its own — the only inexactness left is inside the measured number itself, which is a
    fact about the amplitude and not about this comparison. ``gap_over_lower`` is present for a
    reader and is explicitly the display form.
    """

    iteration: int
    measured: float
    closed_form: float
    lower: Fraction
    upper: Fraction

    @property
    def meets_lower(self) -> bool:
        return Fraction(self.measured) >= self.lower

    @property
    def within_interval(self) -> bool:
        return self.lower <= Fraction(self.measured) <= self.upper

    @property
    def gap_over_lower(self) -> Fraction:
        """``measured - lower``, exactly. Non-negative whenever the bound holds."""
        return Fraction(self.measured) - self.lower

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "measured": self.measured,
            "closed_form": self.closed_form,
            "exact_lower_bound": _fraction_text(self.lower),
            "exact_upper_bound": _fraction_text(self.upper),
            "meets_exact_lower_bound": self.meets_lower,
            "within_exact_interval": self.within_interval,
            "gap_over_lower": _fraction_text(self.gap_over_lower),
            "gap_over_lower_float": float(self.gap_over_lower),
            "provenance": {
                "measured": "measured (exact statevector)",
                "closed_form": "float, not exact",
                "exact_lower_bound": "exact rational (Fraction arithmetic)",
                "gap_over_lower_float": "display form of an exact Fraction",
            },
        }


def _fraction_text(value: Fraction) -> str:
    """An exact spelling of a rational: the fraction itself, plus its decimal for a reader."""
    return f"{value.numerator}/{value.denominator} = {float(value):.17g}"


@dataclass(frozen=True)
class ExactBoundSummary:
    """Every comparison the bound could make, and every point it could not, with the reason."""

    comparisons: tuple[ExactBoundComparison, ...]
    skipped: tuple[tuple[int, str], ...]

    @property
    def n_compared(self) -> int:
        return len(self.comparisons)

    @property
    def n_meeting_lower(self) -> int:
        return sum(1 for comparison in self.comparisons if comparison.meets_lower)

    @property
    def n_within_interval(self) -> int:
        return sum(1 for comparison in self.comparisons if comparison.within_interval)

    @property
    def n_skipped(self) -> int:
        """Points the bound does not exist at. Reported beside :attr:`n_compared` because a table
        that shows only the points it compared is a table that hides its own coverage."""
        return len(self.skipped)

    @property
    def all_meet_lower(self) -> bool:
        """True when every point the bound is defined at lies at or above it.

        Vacuously true for an empty comparison set, so callers that need a non-vacuous statement check
        :attr:`n_compared` as well; :meth:`to_dict` reports both so a reader cannot mistake one for
        the other.
        """
        return self.n_meeting_lower == self.n_compared

    def to_dict(self) -> dict:
        return {
            "n_compared": self.n_compared,
            "n_meeting_lower": self.n_meeting_lower,
            "n_within_interval": self.n_within_interval,
            "all_meet_lower": self.all_meet_lower,
            "n_skipped": len(self.skipped),
            "skipped": [{"iteration": k, "reason": reason} for k, reason in self.skipped],
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
        }


def compare_to_exact_bound(
    records: Sequence[dict], log2_targets: int = 0, n_bits: int | None = None
) -> ExactBoundSummary:
    """Place every measured point against the exact rational interval, where the interval exists.

    Args:
        records: curve records as produced by :meth:`CurvePoint.to_dict`.
        log2_targets: ``log2(M)`` for the bound's density exponent.
        n_bits: overrides the width taken from the records; needed only when the records came from a
            run whose spec is not to hand.

    Returns:
        An :class:`ExactBoundSummary`. Points above the first peak are listed in ``skipped`` with the
        reason the bound does not exist there — never silently dropped.
    """
    comparisons: list[ExactBoundComparison] = []
    skipped: list[tuple[int, str]] = []
    for record in records:
        k = int(record["iteration"])
        measured = record.get("empirical_p_success")
        if measured is None:
            skipped.append((k, "no measured value at this iteration count"))
            continue
        width = n_bits if n_bits is not None else int(record.get("n_bits", 0))
        if not width:
            raise AnalysisError(
                "the exact bound needs the search width; pass n_bits= or give each record its own "
                "'n_bits'"
            )
        applicable, reason = exact_bound_applicability(width, k, log2_targets)
        if not applicable:
            skipped.append((k, reason))
            continue
        lower, upper = exact_success_interval(width, k, log2_targets)
        comparisons.append(
            ExactBoundComparison(
                iteration=k,
                measured=float(measured),
                closed_form=float(record.get("theoretical_p_success", float("nan"))),
                lower=lower,
                upper=upper,
            )
        )
    return ExactBoundSummary(tuple(comparisons), tuple(skipped))


def exact_bound_for_spec(spec: OracleSpec, iterations: int) -> tuple[Fraction, Fraction]:
    """The exact interval for this spec's own ``(N, M)``, with its density exponent checked.

    ``log2(M)`` is derived by exact bit inspection rather than by ``float``: ``int(math.log2(M))``
    returns 3 for ``M = 8`` and also for any ``M`` that rounds up to 8, which would make the bound's
    density exponent a property of the float library rather than of the marked set.

    Raises:
        ValueError: if ``M`` is not a power of two, or if the density exponent is odd. The bound
            exists for ``M`` a power of four (and for ``M = 1``); everywhere else the honest answer
            is that there is no exact rational statement to make at this width.
    """
    space = spec.space()
    n_marked = space.n_marked
    if n_marked & (n_marked - 1):
        raise ValueError(
            f"M={n_marked} is not a power of two, so log2(M) is not an integer and the density "
            "exponent is not defined; the exact bound is not available for this marked set"
        )
    return exact_success_interval(space.n_qubits, iterations, log2_targets=n_marked.bit_length() - 1)
