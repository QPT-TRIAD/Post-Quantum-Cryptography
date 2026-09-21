"""The engine layer's own contract: what a budget refuses, and what a result is allowed to say.

Three properties are asserted here, and each of them is a property the rest of the project would
silently inherit if it were false.

1. **An over-budget run raises.** Not "runs slowly", not "returns None" — raises, with the estimate,
   the ceiling and the kernel's own ``MemAvailable`` attached, and it raises *before* the engine is
   constructed. The faithful QLWR arithmetic predicate is 50 qubits at the smallest instance, which is
   ``2**50`` amplitudes, which is 16 PiB at double precision before the working copy, so it is
   the real case rather than a contrived one and it is built here rather than described.
2. **Every metric comes from the IR.** A result's ``toffoli_count``, ``ir_depth`` and ``t_count`` are
   compared against :func:`ir_metrics` of the gate list that ran, for every engine. A framework's own
   depth and gate counts are recorded separately and are never allowed into that dict.
3. **Every engine writes the project's qubit convention.** A single X on qubit 0 must put the
   amplitude at index 1 and not at ``2**(n-1)``, on each engine independently. The convention is a
   measured property of each framework, not a shared assumption, so it is measured per engine.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pytest

from grover_emulator.backends import (
    ENGINES,
    MEM_AVAILABLE,
    BackendResult,
    BackendUnavailable,
    NoBackendFits,
    RamBudgetExceeded,
    UnknownBackend,
    available_bytes,
    available_engines,
    ir_metrics,
    load_engine,
    memory_snapshot,
    run_selected_backend,
    sample_statevector,
    select_backend,
    statevector_bytes,
)
from grover_emulator.backends.base_backend import format_bytes, from_most_significant_first
from grover_emulator.circuits.ir import Gate, GateList, GateName
from grover_emulator.problem.oracle_spec import Lowering
from grover_emulator.utils.validation import assert_backend_agreement

ENGINE_NAMES = ("qiskit_aer", "cirq_qsim", "tensor_network")
"""Every engine, by the name a configuration's preference list would use."""

FAITHFUL_ARITHMETIC_WIDTH = 50
"""The width of the smallest structurally faithful QLWR arithmetic circuit — predicate, oracle and all.

Not a guess: the test below builds each gate list and asserts its width before asserting the refusal.
All three are 50 wide, because the flag is the predicate's own last qubit and the phase oracle's
sandwich reuses that qubit rather than adding another. ``oracle_width(spec, Lowering.ARITHMETIC)``
names the same 50, and the test asserts that as a *relation* — ``oracle_width`` against the width of
the circuit ``build_phase_oracle`` actually builds, at both lowerings — so that an off-by-one in the
accounting fails loudly instead of matching a stale constant."""

REFUSAL_ESTIMATE_AT_THE_FAITHFUL_WIDTH = {
    "qiskit_aer": "32.0 PiB",
    "cirq_qsim": "16.0 PiB",
    "tensor_network": "32.0 PiB",
}
"""What each engine's own estimate renders as at that width, read off a real refusal.

Per engine rather than one figure, and measured rather than derived, because the width is what moves
these numbers: aer and the tensor-network engine each hold a double-precision amplitude (16 bytes,
two working copies) and qsim holds a single-precision one (8 bytes), so qsim's estimate is exactly
half of theirs — which is also why the cross-validation module can compare its amplitudes at a
tolerance the other two do not need."""


def _all_engines():
    """Every engine this checkout can load, constructed. Skips an engine whose framework is absent."""
    for name in ENGINE_NAMES:
        try:
            yield load_engine(name)()
        except BackendUnavailable as error:  # pragma: no cover - depends on the checkout
            pytest.skip(str(error))


@pytest.fixture(params=ENGINE_NAMES)
def engine(request):
    """One engine, constructed fresh for the test that uses it."""
    return load_engine(request.param)()


# ---------------------------------------------------------------------------------------------
# the budget: arithmetic first, then refusal
# ---------------------------------------------------------------------------------------------


def test_statevector_bytes_is_integer_arithmetic():
    assert statevector_bytes(0) == 32
    assert statevector_bytes(10) == 1024 * 16 * 2
    # A float factor would round this into a number that no longer says what the circuit needs.
    assert statevector_bytes(50) == (1 << 50) * 16 * 2
    assert isinstance(statevector_bytes(50), int)
    for bad in (-1,):
        with pytest.raises(ValueError):
            statevector_bytes(bad)
    with pytest.raises(ValueError):
        statevector_bytes(4, bytes_per_amplitude=0)
    with pytest.raises(ValueError):
        statevector_bytes(4, working_copies=0.5)


def test_format_bytes_reads_as_a_size():
    assert format_bytes(0) == "0 B"
    assert format_bytes(1536) == "1.5 KiB"
    assert format_bytes(6 * (1 << 30)) == "6.0 GiB"
    assert format_bytes((1 << 50) * 16) == "16.0 PiB"


def test_memory_snapshot_reads_the_kernel(tmp_path: Path):
    fake = tmp_path / "meminfo"
    fake.write_text(
        "MemTotal:       16000000 kB\n"
        "MemFree:         1000000 kB\n"
        "MemAvailable:    7000000 kB\n"
        "SwapTotal:       4000000 kB\n"
        "SwapFree:         900000 kB\n"
        "HugePages_Total:       0\n",
        encoding="utf-8",
    )
    snapshot = memory_snapshot(fake)
    assert snapshot["memtotal"] == 16000000 * 1024
    assert snapshot[MEM_AVAILABLE] == 7000000 * 1024
    assert snapshot["hugepages_total"] == 0  # a unitless line is bytes, not kilobytes
    assert available_bytes(snapshot) == 7000000 * 1024
    # The key is spelled the way the kernel spells it, without an underscore: a reader looking for
    # ``mem_available`` finds nothing and reports "unknown" for a number that is right there.
    assert "mem_available" not in snapshot


def test_memory_snapshot_of_a_missing_file_is_empty_not_an_error(tmp_path: Path):
    # A diagnostic that can fail a run is worse than one that is occasionally silent.
    assert memory_snapshot(tmp_path / "not-here") == {}
    assert memory_snapshot(Path("/proc/does-not-exist")) == {}
    assert available_bytes({}) is None


def test_a_run_over_budget_raises_with_its_numbers():
    engine = load_engine("qiskit_aer")(ram_budget_gb=1.0)
    assert engine.exceeds_ram_budget(40) is True
    assert engine.exceeds_ram_budget(8) is False

    with pytest.raises(RamBudgetExceeded) as caught:
        engine.require_within_budget(40)
    refusal = caught.value
    assert refusal.backend == "qiskit_aer"
    assert refusal.n_qubits == 40
    assert refusal.estimate_bytes == (1 << 40) * 16 * 2
    assert refusal.budget_bytes == 1 << 30
    # The message has to be readable on its own: a sweep's log line is often all a reader has.
    assert "40 qubits" in str(refusal)
    assert "1.0 GiB" in str(refusal)
    assert "32.0 TiB" in str(refusal)


def test_the_engine_with_the_smaller_amplitude_fits_a_width_the_other_refuses():
    """qsim is single precision, so it holds half of what Aer holds — measured, and load-bearing.

    At a half-gigabyte ceiling the two engines do not agree about a 25-qubit circuit, and that
    disagreement is not a bug in either estimate: qsim's CPU state vector really is ``complex64``
    (``dtype`` measured on the returned array, ``itemsize`` 8), which is also why its amplitudes
    differ from Aer's by about ``4e-8`` on the circuits the cross-validation test runs. The bytes per
    amplitude below are the engine's declared figure and the cross-validation module asserts what
    that figure costs in the numbers.
    """
    half_a_gigabyte = 0.5
    aer = load_engine("qiskit_aer")(ram_budget_gb=half_a_gigabyte)
    qsim = load_engine("cirq_qsim")(ram_budget_gb=half_a_gigabyte)
    assert aer.bytes_per_amplitude == 16
    assert qsim.bytes_per_amplitude == 8
    assert aer.estimate_bytes(24) == 2 * qsim.estimate_bytes(24)
    assert aer.exceeds_ram_budget(25) is True
    assert qsim.exceeds_ram_budget(25) is False


def test_the_faithful_arithmetic_lowering_is_refused_by_every_engine(qlwr_spec):
    """The real over-budget case: the faithful arithmetic lowering, refused rather than attempted.

    Measured on the smallest structurally faithful QLWR instance (``n_search=12``, ``nu=2``):

        circuit    width  gates   Toffolis  IR depth
        predicate     50  11634      6738      7267
        oracle        50  23269     13476     14534
        grover k=1    50  23330     13476     14538

    All three are 50 wide. The predicate's last qubit is the flag, so the oracle sandwich reuses it
    rather than adding another, and the Grover circuit over the oracle is the same width again — which
    is what ``oracle_width`` reports as well, so the accounting and the circuit it names agree instead
    of differing by one. That agreement is asserted at both lowerings and as a relation rather than
    only as a literal, so a future off-by-one fails loudly rather than matching a stale number.

    Either way the run is ``2**50`` amplitudes: qiskit_aer and the tensor-network engine each estimate
    32.0 PiB for it, and qsim 16.0 PiB because its statevector is single precision. Both are a factor
    of thousands over the 6 GB ceiling, which is the case the refusal exists for.

    One more measurement, and it is the reason this circuit is not merely a size: the predicate and
    the oracle are permutation-plus-phase circuits, so they *are* classically simulable, and the
    verification path simulates them exactly — the Grover circuit over them is not, and needs an
    engine. So the refusal below is a refusal of the engine, not of the question.
    """
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit
    from grover_emulator.circuits.phase_oracle import build_phase_oracle, oracle_width

    predicate = qlwr_spec.build_predicate(Lowering.ARITHMETIC)
    oracle = build_phase_oracle(qlwr_spec, Lowering.ARITHMETIC)
    gl = build_grover_circuit(qlwr_spec, 1, Lowering.ARITHMETIC)

    assert predicate.num_qubits == FAITHFUL_ARITHMETIC_WIDTH
    assert ir_metrics(predicate)["gate_count"] == 11634
    assert ir_metrics(predicate)["toffoli_count"] == 6738
    assert ir_metrics(predicate)["ir_depth"] == 7267
    assert oracle.num_qubits == FAITHFUL_ARITHMETIC_WIDTH  # the sandwich reuses the flag qubit
    assert ir_metrics(oracle)["toffoli_count"] == 13476
    assert ir_metrics(oracle)["ir_depth"] == 14534
    assert oracle_width(qlwr_spec, Lowering.ARITHMETIC) == FAITHFUL_ARITHMETIC_WIDTH
    assert gl.num_qubits == FAITHFUL_ARITHMETIC_WIDTH
    assert predicate.is_classically_simulable() is True
    assert gl.is_classically_simulable() is False  # H and the diffuser: this one needs an engine

    # The width accounting has to name the circuit that exists, at both lowerings. Asserted as the
    # relation first and the literal second: a stale literal is exactly how an off-by-one in the
    # ancilla count would survive a test suite.
    for lowering in (Lowering.ARITHMETIC, Lowering.TRUTH_TABLE):
        assert oracle_width(qlwr_spec, lowering) == build_phase_oracle(qlwr_spec, lowering).num_qubits
    # And the 50 decomposes as: 12 search bits + 37 ancillas + the flag. The flag is not an ancilla,
    # which is the whole of the correction — ``ancilla_width`` counts the qubits between the search
    # register and the flag.
    assert qlwr_spec.search_width() == 12
    assert qlwr_spec.ancilla_width(Lowering.ARITHMETIC) == 37
    assert oracle_width(qlwr_spec, Lowering.ARITHMETIC) == 12 + 37 + 1

    for engine in _all_engines():
        for circuit in (predicate, oracle, gl):
            assert engine.exceeds_ram_budget(circuit.num_qubits) is True
            with pytest.raises(RamBudgetExceeded) as caught:
                engine.run_statevector(circuit)
            assert caught.value.n_qubits == circuit.num_qubits
            # Read back per engine rather than computed here: the estimate is what a corrected width
            # moves, so the numbers in the refusal are the thing being pinned.
            assert (
                format_bytes(caught.value.estimate_bytes)
                == REFUSAL_ESTIMATE_AT_THE_FAITHFUL_WIDTH[engine.name]
            )
        # Refusing is not the same as being unable to see the circuit: the accounting is still read
        # from the IR, so a refused row can be reported with its gate counts beside every other row.
        assert ir_metrics(gl)["toffoli_count"] == 13476
        assert ir_metrics(gl)["ir_depth"] == 14538


def test_the_selector_refuses_the_arithmetic_width_with_every_refusal_attached(qlwr_spec):
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit

    gl = build_grover_circuit(qlwr_spec, 1, Lowering.ARITHMETIC)
    config = _config(["qiskit_aer", "cirq_qsim", "tensor_network"], ram_budget_gb=6.0)
    with pytest.raises(NoBackendFits) as caught:
        select_backend(config, gate_list=gl)
    refusal = caught.value
    # It is a RamBudgetExceeded, so a caller that catches the engine's refusal catches this too...
    assert isinstance(refusal, RamBudgetExceeded)
    # ... and it carries every engine's own numbers rather than a summary of them.
    assert {r.backend for r in refusal.refusals} == set(ENGINE_NAMES)
    assert refusal.estimate_bytes == min(r.estimate_bytes for r in refusal.refusals)
    # The width the selector refused is the circuit's own, not a separate accounting of it.
    assert gl.num_qubits == FAITHFUL_ARITHMETIC_WIDTH
    assert refusal.n_qubits == gl.num_qubits
    for name in ENGINE_NAMES:
        assert name in str(refusal)
        assert REFUSAL_ESTIMATE_AT_THE_FAITHFUL_WIDTH[name] in str(refusal)


# ---------------------------------------------------------------------------------------------
# results: metrics from the IR, convention from the project
# ---------------------------------------------------------------------------------------------


def _tiny(label: str = "tiny") -> GateList:
    """A circuit small enough that every engine runs it in milliseconds, with every gate class."""
    gl = GateList(4, label=label)
    gl.append(GateName.H, 0)
    gl.append(GateName.H, 1)
    gl.append(GateName.CX, 0, 1)
    gl.append(GateName.T, 0)
    gl.append(GateName.TDG, 1)
    gl.append(GateName.S, 2)
    gl.append(GateName.SDG, 3)
    gl.append(GateName.CCX, 0, 1, 2)
    gl.append(GateName.MCZ, 0, 1, 2, 3)
    gl.append(GateName.MCX, 0, 1, 2, 3)
    return gl


def test_result_metrics_are_the_ir_metrics(engine):
    gl = _tiny()
    result = engine.run_statevector(gl)
    assert result.metrics == ir_metrics(gl)
    assert result.metrics["toffoli_count"] == gl.to_dict()["toffoli_count"]
    assert result.metrics["ir_depth"] == gl.to_dict()["ir_depth"]
    assert result.metrics["t_count"] == gl.to_dict()["t_count_explicit"]


def test_result_refuses_a_metrics_dict_that_lost_the_accounting():
    good = {"toffoli_count": 1, "ir_depth": 2, "t_count": 3}
    with pytest.raises(ValueError) as caught:
        BackendResult(
            backend="x",
            label="l",
            num_qubits=1,
            method="statevector",
            statevector=np.ones(2, dtype=complex),
            counts=None,
            shots=0,
            metrics={k: v for k, v in good.items() if k != "ir_depth"},
            framework={},
            estimate_bytes=1,
            memory_before={},
            elapsed_s=0.0,
        )
    assert "ir_depth" in str(caught.value)


def test_result_refuses_counts_that_do_not_add_up():
    with pytest.raises(ValueError):
        BackendResult(
            backend="x",
            label="l",
            num_qubits=1,
            method="sampled",
            statevector=None,
            counts={0: 5},
            shots=6,
            metrics={"toffoli_count": 0, "ir_depth": 1, "t_count": 0},
            framework={},
            estimate_bytes=1,
            memory_before={},
            elapsed_s=0.0,
        )


@pytest.mark.parametrize("qubit", [0, 3])
def test_every_engine_writes_the_project_convention(engine, qubit):
    """An X on qubit q must land on basis index ``1 << q`` — the IR's little-endian convention.

    Measured per engine rather than assumed: Aer already indexes this way, and cirq and quimb both
    put the first qubit in the most significant position, so two of the three engines permute and the
    one that does not must be known to not do it.
    """
    gl = GateList(4)
    gl.append(GateName.X, qubit)
    statevector = engine.run_statevector(gl).statevector
    expected = np.zeros(16, dtype=complex)
    expected[1 << qubit] = 1.0
    np.testing.assert_allclose(statevector, expected, atol=1e-6)


def test_the_conversion_helper_is_its_own_inverse():
    vector = np.arange(8, dtype=complex)
    once = from_most_significant_first(vector, 3)
    twice = from_most_significant_first(once, 3)
    np.testing.assert_allclose(twice, vector)
    # And it is a real permutation: an X on the first qubit of three moves index 4 to index 1.
    x0 = np.zeros(8, dtype=complex)
    x0[4] = 1.0
    assert from_most_significant_first(x0, 3)[1] == 1.0


def test_result_to_dict_is_json_safe(engine):
    gl = _tiny(label="json")
    payload = json.dumps(engine.run_statevector(gl).to_dict())
    assert json.loads(payload)["label"] == "json"
    sampled = engine.run(gl, shots=64, seed=5)
    counts = json.loads(json.dumps(sampled.to_dict()))["counts"]
    assert sum(counts.values()) == 64


def test_sampled_counts_add_up_and_are_seeded(engine):
    gl = _tiny(label="sampling")
    first = engine.run_sampled(gl, shots=512, seed=99)
    second = engine.run_sampled(gl, shots=512, seed=99)
    assert first.counts == second.counts
    assert sum(first.counts.values()) == 512
    assert all(0 <= index < 16 for index in first.counts)
    # A sampled run carries no statevector and no lie about how many shots it drew.
    assert first.statevector is None
    assert first.shots == 512
    third = engine.run_sampled(gl, shots=512, seed=100)
    assert third.counts != first.counts


def test_sampling_from_a_statevector_is_exact_and_seeded():
    statevector = np.zeros(4, dtype=complex)
    statevector[1] = np.sqrt(0.25)
    statevector[3] = np.sqrt(0.75)
    counts = sample_statevector(statevector, 4000, seed=7)
    assert sum(counts.values()) == 4000
    assert set(counts) <= {1, 3}
    # 0.75 of 4000 is 3000; the draw is exact, so the only error is binomial.
    assert abs(counts[3] - 3000) < 200
    assert sample_statevector(statevector, 100, seed=7) == sample_statevector(statevector, 100, seed=7)
    assert sample_statevector(statevector, 100, seed=1) != sample_statevector(statevector, 100, seed=2)


def test_a_seeded_statevector_run_repeats(engine):
    gl = _tiny(label="repeat")
    first = engine.run_statevector(gl, seed=3).statevector
    second = engine.run_statevector(gl, seed=3).statevector
    np.testing.assert_allclose(first, second, atol=1e-12)


def test_the_perm_gate_runs_on_every_engine(engine):
    """The IR's ``perm`` has no named equivalent in any framework; it is a unitary in all three.

    The table is indexed off the *values* of the gate's qubits, little-endian: entry ``g`` of the
    table names the new value of that register, with bit ``k`` of ``g`` the state of ``qubits[k]``.
    That is the rule :mod:`grover_emulator.utils.validation` simulates, and the reference this asserts
    against is written out in that form (:func:`_reference_perm_index`) rather than taken from a
    second backend.

    Note what this circuit is *not*: the table ``(1, 0, 2, 3)`` on qubits ``(0, 1)`` looks like a swap
    and is not one on a state with qubit 1 set — index 2 is a fixed point of it. Measured: all three
    engines leave the amplitude at index 2, and so does the reference.
    """
    gl = GateList(3, label="perm")
    gl.append(GateName.X, 1)
    gl.append(GateName.PERM, 0, 1, params=((1, 0, 2, 3),))
    statevector = engine.run_statevector(gl).statevector
    assert _reference_perm_index((1, 0, 2, 3), (0, 1), 0b010) == 0b010
    expected = np.zeros(8, dtype=complex)
    expected[0b010] = 1.0
    np.testing.assert_allclose(np.abs(statevector), np.abs(expected), atol=1e-6)


def _reference_perm_index(table, qubits, start):
    """The perm table applied to one basis state, by the rule the IR documents.

    Gather the gate's qubits into an index — bit ``k`` of it is the state of ``qubits[k]`` — look the
    table up on that index, and write the result back the same way. Spelled out here so the tests that
    compare engines against a reference do not take the reference from an engine.
    """
    gathered = 0
    for k, qubit in enumerate(qubits):
        gathered |= ((start >> qubit) & 1) << k
    written = table[gathered]
    out = start
    for k, qubit in enumerate(qubits):
        out = (out & ~(1 << qubit)) | (((written >> k) & 1) << qubit)
    return out


def _perm_expectation(table, qubits, start, num_qubits):
    expected = np.zeros(1 << num_qubits, dtype=complex)
    expected[_reference_perm_index(table, qubits, start)] = 1.0
    return expected


def _reversed_bits(index: int, width: int) -> int:
    """``index`` with its ``width``-bit binary representation reversed."""
    return int(format(index, f"0{width}b")[::-1], 2)


def _little_endian(unitary: np.ndarray, width: int) -> np.ndarray:
    """Re-index a matrix from cirq's reading of a qubit list into the IR's.

    cirq reads the *first* qubit of an operation as the most significant; the IR, like qiskit, reads
    qubit 0 as the least significant. The two readings are related by the bit-reversal permutation of
    the basis index, so re-indexing both axes by it converts one matrix into the other. Spelled out
    here rather than imported from the compiler, because a test that takes its convention from the
    code under test cannot catch that code getting the convention wrong.
    """
    order = [_reversed_bits(i, width) for i in range(1 << width)]
    return unitary[np.ix_(order, order)]


PERM_CONVENTION_CASES = (
    # (name, width, table, the gate's qubits, qubits carrying a preparation X)
    ("contiguous pair", 3, (1, 0, 2, 3), (0, 1), (1,)),
    ("non-contiguous pair", 4, (1, 0, 2, 3), (0, 2), (3,)),
    ("non-contiguous triple", 5, (3, 1, 0, 2, 5, 7, 6, 4), (0, 2, 3), (1, 4)),
)
"""A contiguous subset, and two that are not — the cases a lowering cannot get right by accident."""


@pytest.mark.parametrize(("name", "width", "table", "qubits", "prepared"), PERM_CONVENTION_CASES)
def test_the_cirq_perm_lowering_is_the_circuit_the_ir_describes(name, width, table, qubits, prepared):
    """cirq's ``MatrixGate`` and the IR describe the same unitary, checked from the outside.

    cirq reads the first qubit of an operation as the most significant and qiskit reads qubit 0 as the
    least significant, so one matrix handed unchanged to both describes two different operations: cirq
    would run the bit-reversal-conjugate of the gate the gate list counted, and every gate count in a
    report would describe a circuit nobody ran. The compiler conjugates the ``PERM`` matrix by that
    reversal, and this test checks the outcome without trusting that helper: it takes the cirq
    circuit's unitary at an explicit ``qubit_order`` over every IR qubit, re-indexes it into the IR's
    little-endian reading, and compares it entry by entry against ``Operator(to_qiskit(gl)).data`` for
    the same gate list. Two independently compiled circuits, so an agreement here is a statement about
    the gate list.

    The two matrices are also asserted to differ *without* the re-indexing, on every case. That is
    what keeps the comparison above from being vacuous: the re-indexing has to be doing real work
    here, and an assertion that the raw matrices differ is the evidence that it is. Cases where the
    two readings coincide would pass the alignment test whether or not the alignment was right.
    """
    import cirq
    from qiskit.quantum_info import Operator

    from grover_emulator.circuits.compilers import assert_round_trip, from_cirq, to_cirq, to_qiskit

    gl = GateList(width, label=f"perm-convention:{name}")
    for qubit in prepared:
        gl.append(GateName.X, qubit)
    gl.append(GateName.PERM, *qubits, params=(table,))

    # An explicit qubit order, and all of the IR's qubits: cirq's default order would silently narrow
    # the matrix to the qubits the gate touches, and the comparison would then be over a space the IR
    # never declared.
    cirq_unitary = to_cirq(gl).unitary(qubit_order=cirq.LineQubit.range(width))
    qiskit_unitary = Operator(to_qiskit(gl)).data

    np.testing.assert_allclose(_little_endian(cirq_unitary, width), qiskit_unitary, atol=1e-12)
    assert not np.allclose(cirq_unitary, qiskit_unitary, atol=1e-9)

    # The gate list that was counted is still the gate list that comes back, through both frameworks.
    assert_round_trip(gl)
    assert from_cirq(to_cirq(gl)).gates == gl.gates


def test_the_perm_gate_agrees_between_the_two_engines_that_read_it_the_same_way():
    """Aer against the tensor-network engine, on a table that moves every basis state.

    The case above is deliberately a table with a fixed point; this one is a four-cycle, so a lowering
    that reversed anything would have to disagree. Both engines are checked against the reference
    rather than only against each other, because two engines agreeing on a shared mistake is exactly
    what a mutual comparison cannot detect.
    """
    aer = load_engine("qiskit_aer")()
    tn = load_engine("tensor_network")()
    table, qubits, start = (1, 2, 3, 0), (0, 1), 0b0010

    gl = GateList(4, label="perm-agreement")
    gl.append(GateName.X, 1)
    gl.append(GateName.PERM, *qubits, params=(table,))
    assert _reference_perm_index(table, qubits, start) == 0b0011

    expected = _perm_expectation(table, qubits, start, 4)
    for engine in (aer, tn):
        assert_backend_agreement(
            engine.run_statevector(gl).statevector, expected, tol=1e-9, label=engine.name
        )


def test_every_engine_declares_the_framework_it_needs():
    for name in ENGINE_NAMES:
        engine_class = load_engine(name)
        assert engine_class.requires, f"{name} declares no framework requirement"
        assert engine_class.name == name
        assert engine_class.bytes_per_amplitude in (8, 16)


def test_an_unknown_name_is_refused_by_name():
    with pytest.raises(UnknownBackend) as caught:
        load_engine("qiskit_aer_v2")
    assert "qiskit_aer_v2" in str(caught.value)
    assert "tensor_network" in str(caught.value)


def test_available_engines_are_the_registry_entry_point():
    from grover_emulator.backends import engine_names

    assert engine_names() == list(ENGINES)
    assert set(available_engines()) <= set(ENGINES)


# ---------------------------------------------------------------------------------------------
# the tensor-network engine's own two numbers
# ---------------------------------------------------------------------------------------------


def test_the_tensor_network_reports_the_plan_it_executed():
    """The plan is a field of the result, because it is a heuristic and not a promise.

    cotengra's search does not reproduce — five default searches of an 11-qubit circuit found widths
    ``14, 14, 13, 14, 14`` at costs from ``4.96e+05`` to ``8.80e+05`` — so what a run can report is the
    plan *it* used: the width, the cost, the optimizer that produced it, and the seed it was handed.
    The last of those is a parameter of the search rather than a guarantee about it, which is why the
    plan is recorded beside it.

    Two of the fields are properties of the contraction rather than of the search, and they are the
    ones held to a bound here. The widest intermediate is at least as wide as the output tensor, which
    carries every index the circuit has, so a plan can never be narrower than its own circuit — a
    bound that holds for any plan, where the tempting one (no wider than the output plus one) is false
    and measurably so: this same family at two iterations measured widths 9 and 10 for a 7-qubit
    circuit. And ``sliced_inds`` is zero structurally, not by luck: the default search leaves
    cotengra's four refinement options at ``"auto"``, and cotengra resolves that combination to subtree
    reconfiguration with slicing off.
    """
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit
    from grover_emulator.problem.oracle_spec import RandomControlOracleSpec

    engine = load_engine("tensor_network")()
    gl = build_grover_circuit(RandomControlOracleSpec(n_qubits=6, n_marked=1, seed=11), 1)
    result = engine.run_statevector(gl, seed=4)
    framework = result.framework
    assert framework["tensor_count"] > 0
    assert framework["contraction_width"] >= gl.num_qubits
    assert framework["contraction_cost"] > 0
    assert framework["sliced_inds"] == 0
    assert framework["plan_optimizer"] == "hyper"
    assert framework["max_repeats"] == engine.max_repeats
    assert framework["methods"] == list(engine.methods)
    assert framework["seed"] == 4


def test_two_runs_of_the_tensor_network_agree_even_when_their_plans_need_not():
    """The answer reproduces, and that is the claim this engine can actually make.

    A contraction is exact whatever order it is carried out in, so the search being a heuristic costs
    the *answer* nothing: measured on an 11-qubit circuit, five default searches whose widths ranged
    over 13 to 14 produced statevectors agreeing with Aer to ``2.1e-15``–``2.9e-15`` and with each
    other to ``3.8e-15``. This test asserts that at the project's own tolerance, on a circuit small
    enough that three searches are cheap, and it deliberately does not assert anything about the
    widths: whether they differ is the search's business, and a test that required them to differ
    would be as fragile as one that required them to match.
    """
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit
    from grover_emulator.problem.oracle_spec import RandomControlOracleSpec

    engine = load_engine("tensor_network")()
    gl = build_grover_circuit(RandomControlOracleSpec(n_qubits=6, n_marked=1, seed=11), 2)
    runs = [engine.run_statevector(gl) for _ in range(3)]
    plans = [(int(r.framework["contraction_width"]), r.framework["contraction_cost"]) for r in runs]
    assert all(width >= gl.num_qubits and cost > 0 for width, cost in plans)

    for other in runs[1:]:
        assert_backend_agreement(
            runs[0].statevector, other.statevector, tol=1e-9, label="tensor_network repeat"
        )
    # And every run's accounting is the circuit's, not the plan's: the plan is reported beside the
    # metrics and never inside them.
    assert all(r.metrics == ir_metrics(gl) for r in runs)


def test_the_tensor_network_refuses_a_plan_wider_than_its_budget():
    """The plan is a memory claim, and it is checked before the contraction rather than after.

    Driven through a stub plan first, so the arithmetic of the refusal is asserted exactly, and then
    end to end: a real circuit whose *measured* plan is wider than its own output, run under a ceiling
    placed between the two estimates.

    The circuit is chosen from a measurement rather than assumed to be one. Contraction widths for the
    same family, under the engine's default search, one measurement each:

        circuit        width  contraction width
        random k=1         9                9
        qlwr truth k=1    13               13
        random k=3        11               12 to 16

    The first two contract at exactly the output width, so there is no ceiling that admits the output
    and refuses the contraction — a longer circuit is what makes the two numbers separate, and the one
    used below is the cheapest of those measured that does. Its width is a *range*, which is the point
    of the last paragraph here: the default search does not reproduce, so the ceiling is compared
    against a plan that is pinned rather than against whatever the search returns this time.
    """
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit
    from grover_emulator.problem.oracle_spec import RandomControlOracleSpec

    engine_class = load_engine("tensor_network")

    class _Plan:
        """A plan that claims a width, which is all the budget check reads from it."""

        def __init__(self, width):
            self._width = width

        def contraction_width(self):
            return self._width

    stub = engine_class(ram_budget_gb=(1 << 16) / (1 << 30))
    assert stub.require_plan_within_budget(_Plan(10), 5) == 2**10 * 16 * 2
    with pytest.raises(RamBudgetExceeded) as caught:
        stub.require_plan_within_budget(_Plan(20), 5)
    assert caught.value.n_qubits == 5
    assert "width 20" in str(caught.value)

    # End to end, on a circuit whose plan is genuinely wider than its own statevector: three Grover
    # iterations over a 10-qubit random-control oracle, whose widths measured 12 to 16 against a
    # circuit of 11.
    #
    # The plan is pinned rather than searched, and that is a requirement of the test and not a
    # convenience: a refusal is a comparison between a ceiling and the plan that would run, so the
    # plan has to be the one the engine will actually use. A default search can come back narrower
    # than a ceiling placed to refuse the last one, which is what made an earlier version of this test
    # pass or fail depending on the run. A single greedy trial with its hyper-parameters held constant
    # is deterministic across processes — measured: width 16, cost 1.36e+06, identical in three
    # separate interpreters (`jitter_dict` is the one greedy input that draws from a generator nothing
    # can seed, and a constant zero strength is what keeps it out of the picture).
    import cotengra as ctg

    pinned = ctg.HyperOptimizer(
        methods=["greedy"],
        max_repeats=1,
        constants={"greedy": {"random_strength": 0.0, "temperature": 0.0, "costmod": 1.0}},
        progbar=False,
        parallel=False,
    )
    gl = build_grover_circuit(RandomControlOracleSpec(n_qubits=10, n_marked=1, seed=11), 3)
    engine = engine_class(optimizer=pinned)
    plan = engine.run_statevector(gl).framework
    assert plan["plan_optimizer"] == "HyperOptimizer"
    assert plan["contraction_width"] > gl.num_qubits
    peak = statevector_bytes(int(plan["contraction_width"]), bytes_per_amplitude=16, working_copies=2)
    dense = engine_class().estimate_bytes(gl.num_qubits)
    between = (dense + peak) // 2
    assert dense < between < peak
    small = engine_class(optimizer=pinned, ram_budget_gb=between / (1 << 30))
    assert small.exceeds_ram_budget(gl.num_qubits) is False
    with pytest.raises(RamBudgetExceeded) as caught:
        small.run_statevector(gl)
    assert caught.value.estimate_bytes == peak
    assert "contraction plan" in str(caught.value)


def test_the_tensor_network_runs_a_sampled_pass_from_its_own_statevector():
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit
    from grover_emulator.problem.oracle_spec import RandomControlOracleSpec

    engine = load_engine("tensor_network")()
    gl = build_grover_circuit(RandomControlOracleSpec(n_qubits=6, n_marked=1, seed=11), 2)
    exact = engine.run_statevector(gl)
    sampled = engine.run_sampled(gl, shots=2000, seed=17)
    assert sampled.framework["sampled_from"] == "statevector"
    # The marker is the marked state, and it is where the exact distribution is heaviest.
    marker = int(np.argmax(exact.probabilities()))
    assert sampled.counts.get(marker, 0) / sampled.shots > 0.2


# ---------------------------------------------------------------------------------------------
# the selector
# ---------------------------------------------------------------------------------------------


class _Settings:
    """A configuration's backend section, without the rest of the configuration."""

    def __init__(self, preference, ram_budget_gb=6.0):
        self.preference = list(preference)
        self.ram_budget_gb = ram_budget_gb


def _config(preference, ram_budget_gb=6.0):
    class _Config:
        backend = _Settings(preference, ram_budget_gb)

    return _Config()


def test_the_selector_takes_the_first_engine_in_the_preference():
    engine = select_backend(_config(["qiskit_aer", "cirq_qsim"]), num_qubits=10)
    assert engine.name == "qiskit_aer"
    engine = select_backend(_config(["cirq_qsim", "qiskit_aer"]), num_qubits=10)
    assert engine.name == "cirq_qsim"


def test_the_selector_reads_a_bare_backend_section_too():
    engine = select_backend(_Settings(["tensor_network"]), num_qubits=6)
    assert engine.name == "tensor_network"


def test_the_selector_skips_an_engine_whose_framework_is_absent(monkeypatch):
    """A preference is a preference: an engine that cannot load is passed over, not raised on."""
    import grover_emulator.backends.backend_selector as selector

    registry = dict(selector.ENGINES)
    registry["ghost"] = ("grover_emulator.backends.no_such_module", "GhostBackend")
    monkeypatch.setattr(selector, "ENGINES", registry)
    engine = select_backend(_config(["ghost", "qiskit_aer"]), num_qubits=8)
    assert engine.name == "qiskit_aer"


def test_the_selector_raises_when_no_engine_can_be_loaded(monkeypatch):
    from grover_emulator.backends import NoBackendAvailable

    import grover_emulator.backends.backend_selector as selector

    monkeypatch.setattr(
        selector, "ENGINES", {"ghost": ("grover_emulator.backends.no_such_module", "GhostBackend")}
    )
    with pytest.raises(NoBackendAvailable) as caught:
        select_backend(_config(["ghost"]), num_qubits=8)
    assert "no_such_module" in str(caught.value)
    assert caught.value.preference == ["ghost"]


def test_the_selector_refuses_a_width_that_only_some_engines_can_take():
    """The refusal is per engine, and the first engine that fits is the one returned."""
    # 4 MiB: Aer needs 2**18 * 16 * 2 = 8 MiB at 18 qubits and qsim needs 4 MiB.
    config = _config(["qiskit_aer", "cirq_qsim", "tensor_network"], ram_budget_gb=4 * 1024 / (1 << 20))
    assert select_backend(config, num_qubits=17).name == "qiskit_aer"
    assert select_backend(config, num_qubits=18).name == "cirq_qsim"


def test_the_selectors_carries_a_budget_refusal_as_a_budget_refusal():
    config = _config(["qiskit_aer", "cirq_qsim"], ram_budget_gb=1e-6)
    with pytest.raises(RamBudgetExceeded):
        select_backend(config, num_qubits=30)


def test_a_run_logs_mem_available_before_it_starts(caplog):
    gl = GateList(3, label="logged")
    gl.append(GateName.H, 0)
    config = _config(["qiskit_aer"])
    with caplog.at_level(logging.INFO, logger="grover_emulator"):
        result = run_selected_backend(config, gl, seed=1)
    lines = [record.getMessage() for record in caplog.records]
    assert any("MemAvailable" in line for line in lines)
    assert any("running qiskit_aer" in line for line in lines)
    assert any("finished" in line for line in lines)
    # The snapshot the log line was written from is the one the result carries — and the number is
    # in it, rather than the line saying "unknown" while the snapshot holds the answer.
    assert result.memory_before.get(MEM_AVAILABLE) is not None
    mem_lines = [line for line in lines if "MemAvailable" in line]
    assert mem_lines and all("unknown" not in line for line in mem_lines)


def test_a_run_warns_when_the_machine_has_less_than_the_estimate(monkeypatch, caplog):
    """The budget is checked against a ceiling, not against the machine — so the machine is logged."""
    import grover_emulator.backends.backend_selector as selector

    starved = {MEM_AVAILABLE: 1024, "memtotal": 1024 * 1024}
    monkeypatch.setattr(selector, "memory_snapshot", lambda *a, **k: starved)
    gl = GateList(10, label="starved")
    gl.append(GateName.H, 0)
    with caplog.at_level(logging.INFO, logger="grover_emulator"):
        run_selected_backend(_config(["qiskit_aer"]), gl, seed=1)
    warnings = [record.getMessage() for record in caplog.records if record.levelno >= logging.WARNING]
    assert any("swap" in line for line in warnings)
    # And the refusal message carries the same number when the run is over budget instead.
    refusal = RamBudgetExceeded("x", 40, 1 << 40, 1 << 30, starved)
    assert "1.0 KiB available" in str(refusal)


def test_the_selector_passes_the_configurations_shots_and_seed_through():
    from grover_emulator.circuits.grover_circuit_builder import build_grover_circuit
    from grover_emulator.problem.oracle_spec import RandomControlOracleSpec

    gl = build_grover_circuit(RandomControlOracleSpec(n_qubits=5, n_marked=1, seed=11), 2)
    config = _config(["qiskit_aer"])
    sampled = run_selected_backend(config, gl, shots=256, seed=8)
    assert sampled.method == "sampled"
    assert sum(sampled.counts.values()) == 256
    exact = run_selected_backend(config, gl, seed=8)
    assert exact.method == "statevector"
    assert exact.statevector.shape[0] == (1 << gl.num_qubits)
