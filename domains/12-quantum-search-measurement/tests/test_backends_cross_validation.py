"""Two engines that share nothing but the gate list, run on the same circuits, and compared.

A single engine's answer is an assertion about that engine. This module runs the project's own
circuits — the same ``GateList`` — through more than one engine and compares the *statevectors*, which
is the only check in the project that can catch a lowering that is internally consistent and wrong.
Aer and qsim share no compiler, no circuit representation and no kernel: Aer gets a qiskit circuit
and runs its own statevector method, qsim gets a cirq circuit and runs qsim's kernel. When the two
agree to floating-point tolerance, the thing that is being checked is the gate list.

**Everything here is CPU-feasible: the widest configuration is 17 qubits.** A faithful QLWR
arithmetic oracle is 50 qubits wide and no engine will run it — that refusal is asserted in
``tests/test_backends.py`` and is not repeated here, because a cross-validation needs two answers and
an engine that refuses has none.

**The tolerance is measured rather than chosen, and the measurement is surprising enough to write
down.** qsim's state vector is ``complex64``, so its amplitudes are single precision — measured
against Aer below, the worst per-amplitude difference on these configurations is ``4.5e-08``. A
per-amplitude comparison at ``1e-9`` would therefore fail on circuits that are provably equal. But
the comparison made here is an overlap up to a global phase, and ``1 - |<a|b>|`` is *second order* in
that error: the measured shortfall is at most ``9.3e-15`` over all six configurations, five orders of
magnitude inside the project's own ``1e-9`` tolerance. So the default tolerance is used unchanged
between Aer and qsim, and both halves of that argument are asserted — by
:func:`test_the_single_precision_engine_is_what_sets_the_tolerance` for the shortfall and by
:func:`test_the_amplitudes_are_not_comparable_entry_by_entry` for the per-amplitude figures.

**Where the engines are compared.** Every configuration below is built from the project's own problem
layer: Aer and qsim are compared on all six, and the tensor-network engine on the three whose
contraction plans are cheap. None of them contains a ``perm`` gate — the Grover circuits are built
from ``h``, ``x``, ``mcx`` and ``mcz`` — so a compiler's *matrix convention* for ``perm`` is not what
this module tests. That convention is checked directly on the compiled unitaries in
``tests/test_backends.py``, which is also where the cirq lowering's bit-reversal conjugation is
pinned against ``Operator(to_qiskit(...)).data``.

**Sampling is compared to the exact distribution, not to another sampler.** Aer and qsim each have a
native sampler, and agreement between two samplers is weak evidence: both can be wrong in the same
way, and a sampler is exactly the kind of component that is wrong quietly. The exact distribution is
the statevector's ``|amplitude|**2`` from an engine that was itself cross-validated, and each
sampler's draws are compared against *that*.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from grover_emulator.backends import ir_metrics, load_engine
from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit
from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.config.schema import BackendSettings
from grover_emulator.problem.oracle_spec import (
    HiddenPeriodOracleSpec,
    Lowering,
    RandomControlOracleSpec,
)
from grover_emulator.utils.validation import assert_backend_agreement

pytestmark = pytest.mark.filterwarnings(
    # The k-below-optimum advisory is about the success curve's shape at the iteration count used
    # here, not about the circuit: engine agreement is a question about the gate list, and the same
    # circuit at its optimum would cost minutes to build for no additional evidence.
    r"ignore:n_iterations=.*is below this instance's optimum:UserWarning"
)

AER = "qiskit_aer"
QSIM = "cirq_qsim"
TENSOR_NETWORK = "tensor_network"

TWO_ENGINE_TOLERANCE = 1e-9
"""The tolerance for every comparison here, including the ones involving qsim.

Not relaxed for the single-precision engine, because the measurement says it does not have to be: the
overlap shortfall between a ``complex64`` statevector and a double-precision one is second order in
the amplitude error, so the ``4.5e-08`` amplitudes produce a ``9.3e-15`` shortfall. This is the project's
default tolerance in :func:`~grover_emulator.utils.validation.assert_backend_agreement`, and it is
passed with about five orders of margin on every configuration below.

It is a measurement of this checkout, not a law: a different qsim build with a single-precision
*kernel* rather than single-precision storage would move these numbers, and the tests below exist to
say so out loud rather than to assume the margin.
"""

SHOTS = BackendSettings().shots
"""The project's own configured shot count, read from the schema rather than retyped.

The statistical bound below is expressed in terms of it, so a configuration change moves the bound
with the number instead of silently invalidating it.
"""


# ---------------------------------------------------------------------------------------------
# the configurations, all built from the project's own problem layer
# ---------------------------------------------------------------------------------------------

CONFIG_NAMES = (
    "random8-k1",
    "random8-k2",
    "hidden8-k2",
    "qlwr12-truth-table-k1",
    "qlwr12-truth-table-k2",
    "random16-k1",
)
"""Every configuration compared between the two statevector engines.

Six of them, at widths 9 to 17, from three spec families, all at the truth-table lowering: it is the
lowering the arithmetic one is infeasible beside — a 50-qubit oracle that every engine refuses, which
``tests/test_backends.py`` asserts and which cannot be cross-validated because no engine returns an
answer for it.
"""

TN_CONFIG_NAMES = ("random8-k1", "random8-k2", "qlwr12-truth-table-k1")
"""The subset run through the tensor-network engine as well.

Its cost is the contraction plan's, not the circuit's: the same 9-qubit circuit that Aer runs in
milliseconds takes a seeded plan search of seconds here, and a circuit of 195 hyper indices (the
hidden-period oracle at k=2) takes minutes. These three are the ones measured to plan inside a
couple of seconds each, and they are enough to put the third engine on a Grover circuit from two
different spec families.
"""


@pytest.fixture(scope="module")
def configs(qlwr_spec, random_spec, hidden_period_spec) -> dict[str, GateList]:
    """The configurations, built once for the module and reused by every test that names one.

    Building them once matters: the QLWR predicate enumerates its marked set, and a per-test rebuild
    would put that cost inside every comparison.
    """
    return {
        "random8-k1": build_grover_circuit(random_spec, 1),
        "random8-k2": build_grover_circuit(random_spec, 2),
        "hidden8-k2": build_grover_circuit(hidden_period_spec, 2),
        "qlwr12-truth-table-k1": build_grover_circuit(qlwr_spec, 1, Lowering.TRUTH_TABLE),
        "qlwr12-truth-table-k2": build_grover_circuit(qlwr_spec, 2, Lowering.TRUTH_TABLE),
        "random16-k1": build_grover_circuit(RandomControlOracleSpec(n_qubits=16, n_marked=1, seed=11), 1),
    }


def _statevector(engine_name: str, gl: GateList, *, seed: int = 20260913):
    """One engine's exact run, with the two invariants every comparison here rests on."""
    result = load_engine(engine_name)().run_statevector(gl, seed=seed)
    assert result.num_qubits == gl.num_qubits
    norm = float(np.linalg.norm(result.statevector))
    assert math.isclose(norm, 1.0, abs_tol=1e-5), f"{engine_name}: |psi| = {norm}"
    return result


def _overlap_shortfall(a: np.ndarray, b: np.ndarray) -> float:
    """``1 - |<a|b>|`` for normalised vectors — the quantity the tolerance is stated in terms of."""
    a = np.asarray(a, dtype=complex)
    b = np.asarray(b, dtype=complex)
    return float(1.0 - abs(np.vdot(a / np.linalg.norm(a), b / np.linalg.norm(b))))


# ---------------------------------------------------------------------------------------------
# the comparisons
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", CONFIG_NAMES)
def test_two_independent_engines_agree_on_the_same_gate_list(name, configs):
    """Aer and qsim, on a Grover circuit from the project's own problem layer.

    Three things are asserted and they are separate claims. The statevectors agree up to a global
    phase, which is the physics. The metrics dicts are *identical*, which says the accounting came
    from the gate list and not from either framework — a framework-side depth would differ here,
    since the two compilers do not produce the same circuit objects. And each result's width equals
    the IR's, which is the precondition of the budget check that admitted the run.
    """
    gl = configs[name]
    aer = _statevector(AER, gl)
    qsim = _statevector(QSIM, gl)

    assert_backend_agreement(aer.statevector, qsim.statevector, tol=TWO_ENGINE_TOLERANCE, label=name)
    assert aer.metrics == qsim.metrics
    assert aer.metrics["num_qubits"] == gl.num_qubits
    assert aer.metrics["toffoli_count"] > 0

    # The frameworks are not compared to each other, only recorded: the two compilers count
    # different depths for the same gate list, which is exactly why the IR's depth is the headline.
    assert "circuit_depth" in aer.framework and "circuit_depth" in qsim.framework


@pytest.mark.parametrize("name", TN_CONFIG_NAMES)
def test_the_tensor_network_engine_agrees_with_aer(name, configs):
    """The third engine, on the configurations its plan search stays cheap for.

    This engine has no shared code with Aer either — it turns the IR into a tensor network and
    contracts it — so agreement here is a third independent reading of the same gate list. Both are
    double precision: the contraction is done in numpy's complex128 and returns the dtype Aer holds,
    and the measured shortfall is at most ``4.8e-14``.
    """
    gl = configs[name]
    aer = _statevector(AER, gl)
    tn = _statevector(TENSOR_NETWORK, gl)

    assert_backend_agreement(aer.statevector, tn.statevector, tol=TWO_ENGINE_TOLERANCE, label=name)
    assert tn.framework["converted_from_msb_first"] is True
    assert tn.framework["contraction_width"] > 0


def test_the_three_engines_agree_on_a_circuit_that_uses_every_gate_class():
    """One circuit carrying every named gate in the IR, through all three engines.

    The Grover configurations above exercise H, T, CX, CCX, MCX and MCZ. This one adds the single-qubit
    phase gates and the three-control phase gate, at a width where the tensor network's plan search is
    free — because a lowering that mishandles one gate class is exactly the failure a comparison on one
    family of circuits would miss.
    """
    gl = GateList(6, label="every-gate-class")
    gl.append(GateName.H, 0)
    gl.append(GateName.H, 1)
    gl.append(GateName.H, 2)
    gl.append(GateName.CX, 0, 1)
    gl.append(GateName.CX, 1, 2)
    gl.append(GateName.S, 3)
    gl.append(GateName.SDG, 4)
    gl.append(GateName.T, 5)
    gl.append(GateName.TDG, 0)
    gl.append(GateName.CCX, 0, 1, 2)
    gl.append(GateName.CCX, 3, 4, 5)
    gl.append(GateName.MCX, 0, 1, 2, 3)
    gl.append(GateName.MCZ, 2, 3, 4, 5)
    gl.append(GateName.MCZ, 5)
    gl.append(GateName.H, 5)

    aer = _statevector(AER, gl)
    qsim = _statevector(QSIM, gl)
    tn = _statevector(TENSOR_NETWORK, gl)

    assert_backend_agreement(aer.statevector, qsim.statevector, tol=TWO_ENGINE_TOLERANCE, label="aer-qsim")
    assert_backend_agreement(aer.statevector, tn.statevector, tol=TWO_ENGINE_TOLERANCE, label="aer-tn")
    assert_backend_agreement(qsim.statevector, tn.statevector, tol=TWO_ENGINE_TOLERANCE, label="qsim-tn")
    # And the circuit is not a uniform superposition, which would make the agreement above trivial:
    # this is a check on the configuration, not on the engines.
    assert not np.allclose(np.abs(aer.statevector), 1.0 / math.sqrt(2**6), atol=1e-3)


def test_the_single_precision_engine_is_what_sets_the_tolerance(configs):
    """The shortfall between a ``complex64`` engine and a double-precision one, measured on all six.

    The measured values of ``1 - |<aer|qsim>|``, against a per-amplitude difference of ``3.7e-09`` to
    ``4.5e-08`` (the test below):

        random8-k1      8.9e-16       random8-k2    3.3e-15
        hidden8-k2    6.8e-15       qlwr12-k1       8.4e-15
        qlwr12-k2     9.3e-15       random16-k1     9.2e-15

    Two things follow, and both are asserted rather than asserted-about. Every shortfall is inside the
    ``1e-9`` tolerance used throughout this module — so the single-precision engine does not need a
    relaxed tolerance, and the default one is not hiding a disagreement. And the shortfall is second
    order in the amplitude error, which is why a ``9.3e-15`` overlap shortfall and a ``4.5e-08``
    amplitude difference are both true at once. The two tables also show the second-order relation
    between them, which is what makes the argument more than a slogan: ``random8-k1`` has both the
    smallest per-amplitude difference of the six (``1.1e-08``) and the smallest shortfall
    (``8.9e-16``), and its neighbour ``random8-k2`` — the same oracle at twice the iterations — has
    a per-amplitude difference of ``2.2e-08`` and a shortfall of ``3.3e-15``. Twice the amplitude
    error, four times the shortfall.
    """
    worst = 0.0
    for name in CONFIG_NAMES:
        aer = _statevector(AER, configs[name])
        qsim = _statevector(QSIM, configs[name])
        shortfall = _overlap_shortfall(aer.statevector, qsim.statevector)
        assert shortfall < TWO_ENGINE_TOLERANCE, f"{name}: shortfall {shortfall:.3e} over the tolerance"
        worst = max(worst, shortfall)
    assert worst > 1e-16, "no configuration showed single-precision rounding at all"


def test_the_amplitudes_are_not_comparable_entry_by_entry(configs):
    """Why the agreement check is an overlap and not a subtraction, with the numbers.

    Measured per-amplitude differences between Aer and qsim, on the same configurations:

        random8-k1    1.1e-08       random8-k2    2.2e-08
        hidden8-k2    4.5e-08       qlwr12-k1     3.7e-09
        qlwr12-k2     7.5e-09       random16-k1   1.3e-08

    Every one of them is larger than the ``1e-9`` the statevectors agree to as vectors — by a factor
    of 3.7 at the smallest and 45 at the largest — so an entry-by-entry comparison at that tolerance
    would fail on six circuits that are equal. This test asserts the difference on the configuration
    with the largest of them, so that a future qsim that computes in double precision fails a test
    saying exactly what changed instead of silently making the paragraph above stale.
    """
    gl = configs["hidden8-k2"]
    aer = _statevector(AER, gl).statevector
    qsim = _statevector(QSIM, gl).statevector

    worst = float(np.abs(np.asarray(aer, dtype=complex) - np.asarray(qsim, dtype=complex)).max())
    assert worst > 1e-9, f"the engines now agree entry by entry to {worst:.3e}; the premise changed"
    # ...while the comparison that is actually made passes at that same tolerance.
    assert _overlap_shortfall(aer, qsim) < 1e-9


def _expected_total_variation(probabilities, shots: int) -> float:
    """The closed-form expectation of the total-variation distance of a sampled distribution.

    For ``N`` multinomial draws the mean absolute deviation of each observed frequency is
    ``sqrt(2 p (1-p) / (pi N))``, so ``E[TV] = (1/2) sum_i sqrt(2 p_i (1-p_i) / (pi N))``. This is the
    number the two sampler tests below are written against, rather than a bound like ``k/sqrt(N)``:
    the sum over outcomes is what makes the bound tight enough to be a check. On this module's
    sampling configuration the formula predicts ``0.0443``, and the two engines' samplers measured
    ``0.0426`` and ``0.0423`` — a few per cent either side, which is what makes it usable as a scale
    for a tolerance.
    """
    p = np.asarray(probabilities, dtype=float)
    return 0.5 * math.sqrt(2.0 / (math.pi * shots)) * float(np.sqrt(p * (1.0 - p)).sum())


def test_sampling_agrees_with_the_exact_distribution_on_both_engines(configs):
    """Each engine's native sampler against the statevector's ``|amplitude|**2``.

    The tolerance is four times the closed-form expectation above, so the test asks whether the draw
    is a draw from *this* distribution rather than whether it happened to land near the mean. The
    measured distance is about one times the expectation for both engines; ``4x`` is the margin a
    seeded run needs to be reproducible across machines and library versions without being vacuous.

    The exact distribution is the cross-validated statevector's, not the other engine's sampler — two
    samplers agreeing is the weaker statement, and it is made separately below.
    """
    gl = configs["random8-k1"]
    exact = _statevector(AER, gl).probabilities()
    bound = 4.0 * _expected_total_variation(exact, SHOTS)

    for engine_name in (AER, QSIM):
        engine = load_engine(engine_name)()
        result = engine.run_sampled(gl, shots=SHOTS, seed=424242)
        assert result.shots == SHOTS
        assert sum(result.counts.values()) == SHOTS

        measured = np.zeros_like(exact)
        for index, count in result.counts.items():
            measured[index] = count / SHOTS
        total_variation = 0.5 * float(np.abs(measured - exact).sum())
        assert total_variation < bound, f"{engine_name}: TV distance {total_variation:.4f} > {bound:.4f}"
        # And the marked states are where the mass is: the sampler draws from the distribution it was
        # given, and this says the distribution is the Grover one rather than an even spread.
        assert measured.max() > 10.0 / (1 << gl.num_qubits)

        # The same engine repeats itself on the same seed, which is the reproducibility claim the
        # seeded runs make everywhere else in the project.
        again = engine.run_sampled(gl, shots=SHOTS, seed=424242)
        assert again.counts == result.counts


def test_the_two_engines_native_samplers_agree_with_each_other(configs):
    """The two samplers against each other — the weaker comparison, written second on purpose.

    Two independent draws differ by ``sqrt(2)`` times as much as one draw differs from the
    distribution, so the tolerance here is that factor times the one above. Measured: ``0.0587``
    against a scale of ``0.0443``, or about ``1.3`` times the expectation where the exact comparison
    came in at ``0.96``. What this adds over the test above is the case where both samplers are
    wrong in the same direction: the exact comparison catches that, and this one catches a single
    sampler that is shifted without being consistently shifted.
    """
    gl = configs["random8-k1"]
    exact = _statevector(AER, gl).probabilities()
    bound = 4.0 * math.sqrt(2.0) * _expected_total_variation(exact, SHOTS)

    aer_counts = load_engine(AER)().run_sampled(gl, shots=SHOTS, seed=7).counts
    qsim_counts = load_engine(QSIM)().run_sampled(gl, shots=SHOTS, seed=8).counts

    left = np.zeros(1 << gl.num_qubits)
    right = np.zeros(1 << gl.num_qubits)
    for index, count in aer_counts.items():
        left[index] = count / SHOTS
    for index, count in qsim_counts.items():
        right[index] = count / SHOTS
    total_variation = 0.5 * float(np.abs(left - right).sum())
    assert total_variation < bound, f"samplers differ by {total_variation:.4f} > {bound:.4f}"


def test_the_metrics_are_the_circuits_and_not_the_engines(configs):
    """The accounting is identical across engines per circuit, and it is not a constant.

    Both halves matter. Identical per circuit is what says the numbers came from the IR rather than
    from the framework that ran it — the two frameworks count different depths for the same gate list,
    which the summary above records separately. Not a constant is what says the metrics dict is a
    reading of the circuit: a function that returned a fixed shape would satisfy the first claim
    alone, so the Toffoli counts are asserted to differ across the configurations that differ.
    """
    toffolis = set()
    for name in CONFIG_NAMES:
        gl = configs[name]
        metrics = [_statevector(engine, gl).metrics for engine in (AER, QSIM)]
        assert metrics[0] == metrics[1] == ir_metrics(gl)
        toffolis.add(metrics[0]["toffoli_count"])
    assert len(toffolis) > 1, "every configuration reported the same Toffoli count"
