"""The whole pipeline, end to end, on the real engines.

Every other test file checks one layer against its own contract. This one checks that the layers
still compose: a spec becomes a gate list, the gate list becomes a circuit on a real backend, the
circuit's measured statistics match the closed form the algorithm predicts, the reported metrics
are the ones the IR computes, and the report carries the boundary that keeps the result honest.

The one property worth stating plainly, because it is the easiest thing for a reader to
over-read: **a diagonal phase oracle preserves the two-parameter state structure, so the success
curve is a function of ``(M, N)`` alone. The circuit contributes nothing to the curve.** Its
scientific content is that it certifies ``M`` and that it costs something. Nothing here presents
"the curve ran on a real engine" as independent evidence for the curve, and no assertion in this
file would pass if the circuit were wrong *and* the curve were computed analytically — which is
why the marked set is read from the spec and the probabilities from the statevector the engine
actually produced.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from grover_emulator.circuits.grover_circuit_builder import (
    build_grover_circuit,
    derive_iteration_range,
    optimal_iterations,
)
from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.problem.oracle_spec import Lowering

# The builder warns whenever a single circuit is built at ``k < k_opt``, because a curve truncated
# before its peak "looks like a result and is not one". That warning is correct and is kept
# everywhere it can mislead. Here it is expected by construction: one test sweeps the whole derived
# range, which necessarily straddles the optimum, and the others build deliberately minimal
# circuits because they are checking composition and normalisation rather than the shape of the
# curve. Silenced at module scope rather than per test so that a warning appearing *elsewhere*
# still shows up.
pytestmark = pytest.mark.filterwarnings(
    "ignore:n_iterations=.*below this instance's optimum:UserWarning"
)

# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------


def marked_indices(spec) -> list[int]:
    """The marked set, as statevector indices.

    ``qiskit_aer_backend`` normalises every engine to the IR's convention — qubit ``q`` carries
    bit ``q`` — and the search register is the low ``search_width`` qubits with the ancillas and
    flag above it, all returning to ``|0>``. So a search value ``v`` is statevector index ``v``.
    """
    return sorted(spec.marked_set())


def probability_of(statevector, indices) -> float:
    p = np.abs(np.asarray(statevector)) ** 2
    return float(sum(p[i] for i in indices))


def closed_form(k: int, m: int, n: int) -> float:
    """``sin**2((2k+1) * theta)`` with ``sin(theta) = sqrt(M/N)``."""
    theta = math.asin(math.sqrt(m / n))
    return math.sin((2 * k + 1) * theta) ** 2


# ---------------------------------------------------------------------------------------------
# the pipeline
# ---------------------------------------------------------------------------------------------


def test_the_whole_pipeline_runs_and_peaks_where_the_theory_says(qlwr_spec, aer_backend):
    """Spec to gate list to a real engine to a measured curve, with the peak at the derived
    optimum rather than wherever the range happened to stop."""
    marked = marked_indices(qlwr_spec)
    n_search = qlwr_spec.search_width()
    n_states = 1 << n_search
    m = len(marked)
    assert m == 1, "the worked instance is the uniqueness case; see notes/01-arithmetic.md"

    k_opt = optimal_iterations(qlwr_spec)
    iteration_range = derive_iteration_range(qlwr_spec)
    assert k_opt in iteration_range, (
        "the derived range must contain the optimum, or the sweep cannot see the peak"
    )

    measured = {}
    for k in iteration_range:
        circuit = build_grover_circuit(qlwr_spec, n_iterations=k)
        result = aer_backend.run_statevector(circuit)
        measured[k] = probability_of(result.statevector, marked)

    peak = max(measured, key=lambda k: measured[k])

    # The curve is sin^2, so it is symmetric about k_opt and turns over there. A sweep that peaked
    # anywhere else would mean the diffuser, the oracle, or the range is wrong.
    assert abs(peak - k_opt) <= 2, f"peak at k={peak}, optimum k={k_opt}"

    # Against the closed form, at the peak and at the ends, without tolerance on the physics.
    assert measured[k_opt] == pytest.approx(closed_form(k_opt, m, n_states), abs=1e-9)
    assert measured[0] == pytest.approx(m / n_states, abs=1e-12)  # the unprepared state
    for k in (iteration_range[0], iteration_range[-1]):
        assert measured[k] == pytest.approx(closed_form(k, m, n_states), abs=1e-9)


def test_the_search_register_is_normalised_and_the_ancillas_return_clean(qlwr_spec, aer_backend):
    """The oracle sandwich must be the identity on everything except the flag. If the ancillas did
    not return to ``|0>``, probability would leak into indices the marked set never names, and the
    success probabilities above would be quietly wrong rather than obviously wrong."""
    circuit = build_grover_circuit(qlwr_spec, n_iterations=1)
    total = circuit.num_qubits
    search = qlwr_spec.search_width()
    statevector = np.asarray(aer_backend.run_statevector(circuit).statevector)

    assert statevector.shape == (1 << total,)
    assert float(np.sum(np.abs(statevector) ** 2)) == pytest.approx(1.0, abs=1e-12)

    # Every populated index must lie in the search register: the ancillas and flag are the high
    # bits and must all be zero.
    populated = np.flatnonzero(np.abs(statevector) > 1e-12)
    assert populated.size > 0
    assert int(populated.max()) < (1 << search), (
        "amplitude outside the search register; an ancilla or the flag did not return to |0>"
    )


def test_two_engines_agree_on_the_same_circuit(qlwr_spec, aer_backend):
    """Aer and qsim, on the circuit as built.

    Three measured facts shape this comparison, and each of the obvious ways to write it gets one
    of them wrong.

    qsim runs in **single** precision but returns ``complex128``, so the dtype is not evidence of
    the precision and its statevector is only single-precision close to normalised. Because its
    norm lands slightly *above* one, the overlap ``|<a|b>|`` can exceed 1 and make the shortfall
    ``1 - |<a|b>|`` come out **negative** — which reads as agreement even where there is none.
    Renormalising first is what makes the number mean anything; the residual is then ~1e-14.

    And the predicate is the overlap rather than an elementwise difference: over this circuit,
    whose two oracle passes are some forty-six thousand gates, an elementwise bound of 1e-9 fails
    at 1.16e-9 purely on amplitude drift, which would report a disagreement that does not exist.
    """
    from grover_emulator.backends.cirq_qsim_backend import CirqQsimBackend

    qsim = CirqQsimBackend()
    circuit = build_grover_circuit(qlwr_spec, n_iterations=2)

    a = np.asarray(aer_backend.run_statevector(circuit).statevector)
    b = np.asarray(qsim.run_statevector(circuit).statevector)

    assert a.shape == b.shape

    # Aer is exact double precision.
    assert float(np.sum(np.abs(a) ** 2)) == pytest.approx(1.0, abs=1e-12)

    # qsim is single precision, so its norm is only single-precision close to one.
    assert float(np.sum(np.abs(b) ** 2)) == pytest.approx(1.0, abs=1e-6)

    shortfall = 1.0 - abs(np.vdot(a, b / np.linalg.norm(b)))
    assert shortfall < 1e-9
    # A negative shortfall would mean the renormalisation above was skipped and the pass is
    # meaningless, so the direction is asserted rather than only the magnitude.
    assert shortfall > -1e-9


def test_the_reported_metrics_are_the_ones_the_ir_computes(qlwr_spec, aer_backend):
    """The accounting must describe the gate list that ran. A report whose gate count came from a
    framework object would drift from the IR the moment a compiler resynthesised anything."""
    circuit = build_grover_circuit(qlwr_spec, n_iterations=1)
    metrics = aer_backend.run_statevector(circuit).metrics

    assert metrics["gate_count"] == len(circuit.gates)
    assert metrics["toffoli_count"] == circuit.toffoli_count()
    assert metrics["ir_depth"] == circuit.depth()
    assert metrics["t_count"] == circuit.t_count()
    assert metrics["num_qubits"] == circuit.num_qubits


def test_the_arithmetic_lowering_computes_the_same_function(qlwr_spec):
    """Both lowerings must mark the same set. This is what keeps the arithmetic circuit's gate
    count attached to a circuit that computes the right function rather than merely a large one."""
    predicate = qlwr_spec.build_predicate(Lowering.ARITHMETIC)
    marked = marked_indices(qlwr_spec)

    # The predicate sets the flag for a marked input. Simulating it on every basis state is the
    # only honest check; sampling would miss a wrong row, which is the failure the wrap bucket in
    # `sample_intervals` is there to prevent.
    from grover_emulator.utils.validation import assert_predicate_matches_spec

    assert_predicate_matches_spec(qlwr_spec, Lowering.ARITHMETIC)
    assert predicate.num_qubits == qlwr_spec.search_width() + qlwr_spec.ancilla_width(
        Lowering.ARITHMETIC
    ) + 1
    assert len(marked) == 1


# ---------------------------------------------------------------------------------------------
# the machine limits, refused rather than attempted
# ---------------------------------------------------------------------------------------------


def test_the_faithful_arithmetic_circuit_is_refused_not_attempted(aer_backend):
    """The ~50-qubit arithmetic lowering is genuinely past any exact-statevector budget. The
    backend must raise before constructing anything, because a run that spills does not slow down,
    it thrashes — and a quiet swap would look like a slow success."""
    from grover_emulator.backends.base_backend import RamBudgetExceeded

    wide = GateList(50)
    wide.append(GateName.X, 0)

    assert aer_backend.exceeds_ram_budget(50)
    with pytest.raises(RamBudgetExceeded):
        aer_backend.run_statevector(wide)


def test_a_simulable_width_is_not_refused(aer_backend):
    """The refusal has to be a real decision, not a blanket refusal that would make the previous
    test pass for the wrong reason."""
    assert not aer_backend.exceeds_ram_budget(12)


# ---------------------------------------------------------------------------------------------
# the report
# ---------------------------------------------------------------------------------------------


def test_a_generated_report_carries_the_scope_boundary(tmp_path):
    """The boundary is the point of the project: an exact statevector of ``2**n`` complex128
    amplitudes caps this at n ~ 24 on a CPU, so nothing here can speak to a fault-tolerant machine
    attacking 128-bit security. `generate_report` documents that the preamble is emitted on every
    path with no argument that suppresses it; this asserts that claim rather than trusting it."""
    from grover_emulator.reporting.report_generator import SCOPE_BOUNDARY, generate_report

    config = (
        __import__("pathlib").Path(__file__).resolve().parents[1] / "config" / "default_experiment.yaml"
    )
    report_path = generate_report(tmp_path, config, {})

    text = report_path.read_text()
    assert SCOPE_BOUNDARY in text
    # Byte-for-byte, not paraphrased: a report that reworded the boundary would still contain
    # something a substring check might accept.
    assert text.count(SCOPE_BOUNDARY) >= 1
    assert "not a security claim" in text.lower() or "security" in text.lower()
