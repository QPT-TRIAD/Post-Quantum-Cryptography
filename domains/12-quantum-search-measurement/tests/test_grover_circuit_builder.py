"""The Grover circuit builder: what it emits, how many times, and what it refuses.

Every other test in the suite hands ``build_grover_circuit`` an explicit iteration count, so the
default — the one a caller gets by saying nothing — had never been run, and ``sweep_iterations`` was
referenced by no test and no other module at all. The checks here are structural wherever they can
be, because structure is what the gate counts in a report are a count of:

    H^n, then k rounds of (oracle, diffuser)      =>      len == n + k * (len(oracle) + len(diffuser))

and the oracle and the diffuser are recovered from the emitted gate list slice by slice, rather than
inferred from its length alone.

One physical check closes the file: at the derived optimum, on Aer, the probability of reading a
marked state is ``sin^2((2k+1) theta)`` to ``1e-9``. That is the claim the whole builder exists to
make true, and a builder that repeated the oracle but not the diffuser, or the other way round, would
satisfy every length formula above and fail it.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

from grover_emulator.circuits.diffuser import build_diffuser
from grover_emulator.circuits.grover_circuit_builder import (
    build_grover_circuit,
    derive_iteration_range,
    optimal_iterations,
    sweep_iterations,
)
from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.circuits.phase_oracle import build_phase_oracle
from grover_emulator.problem.oracle_spec import HiddenPeriodOracleSpec, Lowering, RandomControlOracleSpec
from grover_emulator.problem.search_space import theoretical_optimal_iterations


def quietly(build, *args, **kwargs) -> GateList:
    """Call a builder with its below-optimum warning suppressed.

    Most tests here build short circuits on purpose. The warning has tests of its own below; letting
    it fire everywhere else would bury them.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return build(*args, **kwargs)


def one_marked(n: int = 5) -> RandomControlOracleSpec:
    return RandomControlOracleSpec(n_qubits=n, n_marked=1, seed=7)


def round_length(spec) -> int:
    return len(build_phase_oracle(spec)) + len(build_diffuser(spec.search_width()))


# ---------------------------------------------------------------------------------------------
# the default iteration count
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("n", "n_marked", "k_opt"), [(4, 1, 3), (5, 1, 4), (6, 1, 6), (6, 4, 3), (8, 8, 4)])
def test_the_default_iteration_count_is_the_theoretical_optimum(n, n_marked, k_opt):
    """Asserted from the structure of what was built, not from the label: the number of oracle
    phase kicks and the number of diffuser reflections in the default circuit are both
    ``floor(pi/4 sqrt(N/M))``, and the literal values pin that formula against a change in either
    module."""
    spec = RandomControlOracleSpec(n_qubits=n, n_marked=n_marked, seed=3)
    assert theoretical_optimal_iterations(1 << n, n_marked) == k_opt
    assert math.floor(math.pi / 4 * math.sqrt((1 << n) / n_marked)) == k_opt
    assert optimal_iterations(spec) == k_opt

    gl = build_grover_circuit(spec)

    flag = n
    oracle_kicks = [g for g in gl.gates if g.name is GateName.MCZ and g.qubits == (flag,)]
    reflections = [g for g in gl.gates if g.name is GateName.MCZ and set(g.qubits) == set(range(n))]
    assert len(oracle_kicks) == k_opt
    assert len(reflections) == k_opt
    assert len(gl) == n + k_opt * round_length(spec)
    assert gl.label.endswith(f"k={k_opt}]")


def test_the_default_build_is_the_explicit_build_at_the_optimum():
    spec = one_marked(6)
    default = build_grover_circuit(spec)
    explicit = build_grover_circuit(spec, optimal_iterations(spec))
    assert default.gates == explicit.gates
    assert default.num_qubits == explicit.num_qubits
    assert default.label == explicit.label


# ---------------------------------------------------------------------------------------------
# structure
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("k", [0, 1, 2, 5, 9])
def test_an_explicit_iteration_count_is_honoured_gate_for_gate(k):
    """The emitted list *is* ``H^n`` followed by ``k`` copies of (oracle, diffuser), in that order.
    ``k = 9`` is above the optimum, which is legitimate: the curve turning over is evidence."""
    spec = one_marked(5)
    n = spec.search_width()
    oracle = build_phase_oracle(spec).gates
    diffuser = build_diffuser(n).gates

    gl = quietly(build_grover_circuit, spec, k)

    assert len(gl) == n + k * (len(oracle) + len(diffuser))
    assert [(g.name, g.qubits) for g in gl.gates[:n]] == [(GateName.H, (q,)) for q in range(n)]
    cursor = n
    for _ in range(k):
        assert gl.gates[cursor : cursor + len(oracle)] == oracle
        cursor += len(oracle)
        assert gl.gates[cursor : cursor + len(diffuser)] == diffuser
        cursor += len(diffuser)
    assert cursor == len(gl)


def test_zero_iterations_is_only_the_hadamard_layer():
    spec = one_marked(5)
    gl = quietly(build_grover_circuit, spec, 0)
    assert [g.name for g in gl.gates] == [GateName.H] * 5
    assert sorted(g.qubits[0] for g in gl.gates) == list(range(5))
    assert gl.num_qubits == 6, "the flag is declared even when no oracle has touched it"


def test_the_flag_is_never_put_into_superposition_and_nothing_is_measured():
    """The diffuser acts on the search register only. An H reaching the flag would make the oracle's
    kickback act on a superposed flag, and the circuit would still be unitary and still run."""
    spec = RandomControlOracleSpec(n_qubits=5, n_marked=2, seed=2)
    gl = quietly(build_grover_circuit, spec, 2)
    flag = spec.search_width()

    touching_flag = {g.name for g in gl.gates if flag in g.qubits}
    assert GateName.H not in touching_flag
    assert touching_flag <= {GateName.MCZ, GateName.CX, GateName.CCX, GateName.MCX, GateName.X}
    assert {g.name for g in gl.gates} <= set(GateName), "the IR has no measurement to append"
    assert gl.num_qubits == flag + 1


def test_the_lowering_is_passed_through_to_the_oracle(qlwr_spec):
    """Width is the visible difference: the arithmetic oracle drags its ancillas into the circuit.
    Built at ``k = 1`` only — the circuit is inspected, never run."""
    cheap = quietly(build_grover_circuit, qlwr_spec, 1, Lowering.TRUTH_TABLE)
    faithful = quietly(build_grover_circuit, qlwr_spec, 1, Lowering.ARITHMETIC)
    n = qlwr_spec.search_width()
    diffuser = len(build_diffuser(n))

    assert cheap.num_qubits == n + 1
    assert faithful.num_qubits == build_phase_oracle(qlwr_spec, Lowering.ARITHMETIC).num_qubits
    assert len(faithful) == n + len(build_phase_oracle(qlwr_spec, Lowering.ARITHMETIC)) + diffuser
    assert "arithmetic" in faithful.label and "truth_table" in cheap.label
    # The diffuser still reflects about the search register alone, however wide the oracle is.
    reflection = [g for g in faithful.gates if g.name is GateName.MCZ and len(g.qubits) > 1]
    assert [set(g.qubits) for g in reflection] == [set(range(n))]


# ---------------------------------------------------------------------------------------------
# refusals and warnings
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("k", [-1, -50])
def test_a_negative_iteration_count_is_refused(k):
    with pytest.raises(ValueError, match="n_iterations must be >= 0"):
        build_grover_circuit(one_marked(4), k)


@pytest.mark.parametrize("k", [0, 1, 3])
def test_building_below_the_optimum_warns_and_names_both_numbers(k):
    """A truncated curve rises monotonically and looks like a result. The builder cannot stop a
    caller asking for one, so it says so — as a ``UserWarning`` carrying the count asked for and the
    count the instance needs."""
    spec = one_marked(5)  # k_opt == 4
    with pytest.warns(UserWarning, match=rf"n_iterations={k} is below .* k_opt=4"):
        build_grover_circuit(spec, k)


@pytest.mark.parametrize("k", [None, 4, 5, 40])
def test_building_at_or_above_the_optimum_is_silent(k):
    spec = one_marked(5)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        build_grover_circuit(spec, k)


def test_a_spec_whose_optimum_is_zero_never_warns():
    """Three quarters of the space marked puts the optimum at zero rounds, and no legal count is
    below zero — so the default build is the bare Hadamard layer and says nothing."""
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=12, seed=5)
    assert optimal_iterations(spec) == 0
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        gl = build_grover_circuit(spec)
    assert [g.name for g in gl.gates] == [GateName.H] * 4


# ---------------------------------------------------------------------------------------------
# sweep_iterations
# ---------------------------------------------------------------------------------------------


def test_the_default_sweep_runs_from_zero_to_two_past_the_optimum():
    """One ``(k, circuit)`` pair per count, in order, over a range derived from the instance — far
    enough past the peak to see the curve turn over."""
    spec = one_marked(5)
    k_opt = optimal_iterations(spec)
    assert derive_iteration_range(spec) == range(0, k_opt + 3)

    sweep = quietly(sweep_iterations, spec)

    assert [k for k, _ in sweep] == list(range(0, k_opt + 3))
    assert all(isinstance(gl, GateList) for _, gl in sweep)
    for k, gl in sweep:
        want = quietly(build_grover_circuit, spec, k)
        assert gl.gates == want.gates, f"k={k}"
        assert gl.num_qubits == want.num_qubits
        assert gl.label == want.label


def test_consecutive_sweep_circuits_differ_by_exactly_one_round():
    spec = HiddenPeriodOracleSpec(n_qubits=5, period=0b10, seed=3)
    sweep = quietly(sweep_iterations, spec)
    lengths = [len(gl) for _, gl in sweep]
    assert len(sweep) >= 3
    assert set(np.diff(lengths).tolist()) == {round_length(spec)}
    for (_, shorter), (_, longer) in zip(sweep, sweep[1:]):
        assert longer.gates[: len(shorter)] == shorter.gates


def test_an_explicit_sweep_range_is_honoured_including_its_step():
    spec = one_marked(5)
    sweep = quietly(sweep_iterations, spec, range(1, 8, 3))
    assert [k for k, _ in sweep] == [1, 4, 7]
    for k, gl in sweep:
        assert gl.gates == quietly(build_grover_circuit, spec, k).gates


def test_an_empty_sweep_range_gives_no_circuits():
    assert sweep_iterations(one_marked(4), range(0)) == []


def test_a_sweep_that_stops_short_of_the_peak_warns():
    """The builder's warning has to survive being called in a loop, or a shortened sweep — the
    exact case it was written for — would be the one place it never fires."""
    spec = one_marked(5)
    with pytest.warns(UserWarning, match="below this instance's optimum"):
        sweep_iterations(spec, range(0, 2))


def test_the_sweep_passes_its_lowering_through():
    spec = one_marked(4)
    for lowering in Lowering:
        sweep = quietly(sweep_iterations, spec, range(1, 2), lowering)
        assert sweep[0][1].label == f"grover[random_control:{lowering.value}:k=1]"


# ---------------------------------------------------------------------------------------------
# the physics the structure is for
# ---------------------------------------------------------------------------------------------


def marked_probability(engine, spec, gl: GateList) -> float:
    """Probability of reading a marked value *with the flag clean* — the only outcomes that count."""
    probabilities = np.abs(engine.run_statevector(gl).statevector) ** 2
    assert probabilities.sum() == pytest.approx(1.0, abs=1e-9)
    return float(sum(probabilities[x] for x in spec.marked_set()))


@pytest.mark.parametrize(("n", "n_marked", "seed"), [(4, 1, 1), (6, 1, 7), (6, 3, 2), (8, 1, 5)])
def test_success_at_the_optimum_matches_the_closed_form_on_aer(aer_backend, n, n_marked, seed):
    """``sin^2((2k+1) arcsin sqrt(M/N))``, computed here from ``M`` and ``N`` alone."""
    spec = RandomControlOracleSpec(n_qubits=n, n_marked=n_marked, seed=seed)
    k_opt = optimal_iterations(spec)
    theta = math.asin(math.sqrt(n_marked / (1 << n)))

    measured = marked_probability(aer_backend, spec, build_grover_circuit(spec))

    assert measured == pytest.approx(math.sin((2 * k_opt + 1) * theta) ** 2, abs=1e-9)
    assert measured > 0.9, "at the optimum the search should all but succeed"


def test_every_sweep_point_matches_the_closed_form_on_aer(aer_backend):
    """The whole default sweep, so the rise, the peak at ``k_opt`` and the turn-over are all seen."""
    spec = one_marked(5)
    theta = math.asin(math.sqrt(1 / 32))
    curve = []
    for k, gl in quietly(sweep_iterations, spec):
        measured = marked_probability(aer_backend, spec, gl)
        assert measured == pytest.approx(math.sin((2 * k + 1) * theta) ** 2, abs=1e-9), f"k={k}"
        curve.append(measured)

    assert curve[0] == pytest.approx(1 / 32, abs=1e-12)
    assert int(np.argmax(curve)) == optimal_iterations(spec)
    assert curve[-1] < max(curve), "the sweep must run far enough to see the curve come back down"
