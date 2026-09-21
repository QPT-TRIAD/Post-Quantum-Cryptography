"""Grover's circuit, and the iteration range it must be run over.

**The iteration range is derived, never configured.** The plan document that specified this project
carried ``iteration_range: [0, 40]`` as a fixed default. At the smallest structurally faithful QLWR
instance the optimum is ``k = 50``, and at ``n_search = 24`` it is ``3216``. Run over ``[0, 40]``,
every sweep point returns a smooth, monotone, entirely plausible rising success curve that never
reaches its peak and supports no conclusion at all — and nothing raises. A fixed range is not a
tunable; it is a way to produce confident nonsense, so this module refuses to accept one.

The optimum is a property of the spec, not of the width: it follows from ``M`` and ``N``, both of
which the spec reports exactly.
"""

from __future__ import annotations

from ..problem.oracle_spec import Lowering, OracleSpec
from .compilers import relabel
from .diffuser import build_diffuser
from .ir import GateList, GateName
from .phase_oracle import build_phase_oracle, oracle_width

__all__ = [
    "build_grover_circuit",
    "sweep_iterations",
    "derive_iteration_range",
    "optimal_iterations",
]


def optimal_iterations(spec: OracleSpec) -> int:
    """``floor(pi/4 * sqrt(N/M))`` for this spec's own search space."""
    return spec.space().optimal_iterations


def derive_iteration_range(spec: OracleSpec, extra: int = 2) -> range:
    """A range that certainly contains the peak: ``[0, k_opt + extra]``.

    Derived per instance rather than configured. ``extra`` gives room to see the curve turn over,
    which is the thing a reader needs in order to trust that the peak is real rather than the end of
    the window.
    """
    k_opt = optimal_iterations(spec)
    return range(0, k_opt + extra + 1)


def build_grover_circuit(
    spec: OracleSpec,
    n_iterations: int | None = None,
    lowering: Lowering = Lowering.TRUTH_TABLE,
) -> GateList:
    """``H^n`` then ``n_iterations`` rounds of (oracle, diffuser).

    Args:
        spec: the oracle.
        n_iterations: defaults to the spec's own optimum. Passing a value *above* the optimum is
            legitimate — the curve turns over and comes back down, and seeing that is evidence the
            peak is real; passing one far below it silently truncates the curve before its peak, so
            the caller is warned rather than trusted.
        lowering: which oracle lowering to use.

    No measurement is appended. The IR is unitary, and measurement is a backend concern; the
    backend adds it after compiling, so that the gate list that was counted is still the gate list
    that ran.
    """
    import warnings

    n_search = spec.search_width()
    total = oracle_width(spec, lowering)
    k_opt = optimal_iterations(spec)
    if n_iterations is None:
        n_iterations = k_opt
    if n_iterations < 0:
        raise ValueError(f"n_iterations must be >= 0, got {n_iterations}")
    if n_iterations < k_opt:
        warnings.warn(
            f"n_iterations={n_iterations} is below this instance's optimum k_opt={k_opt}; the "
            "success curve will be truncated before its peak and will rise monotonically for the "
            "whole window, which looks like a result and is not one",
            stacklevel=2,
        )

    oracle = build_phase_oracle(spec, lowering)
    diffuser = relabel(build_diffuser(n_search), {q: q for q in range(n_search)}, total)

    gl = GateList(total, label=f"grover[{spec.name}:{lowering.value}:k={n_iterations}]")
    for q in range(n_search):
        gl.append(GateName.H, q)
    for _ in range(n_iterations):
        gl.extend(oracle)
        gl.extend(diffuser)
    return gl


def sweep_iterations(
    spec: OracleSpec,
    iteration_range: range | None = None,
    lowering: Lowering = Lowering.TRUTH_TABLE,
) -> list[tuple[int, GateList]]:
    """One circuit per iteration count, for the success-probability curve.

    The default range is derived from the spec. A caller may pass a shorter one for speed, and is
    warned by :func:`build_grover_circuit` when that shorter one stops before the peak.
    """
    if iteration_range is None:
        iteration_range = derive_iteration_range(spec)
    return [(k, build_grover_circuit(spec, k, lowering)) for k in iteration_range]
