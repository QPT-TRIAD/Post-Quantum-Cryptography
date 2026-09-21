"""The cross-validation engine: cirq's front end over qsim's simulator.

This engine exists to disagree with Aer when one of them is wrong. It is a genuinely independent
implementation — a different compiler, a different circuit representation, and a different
simulation kernel written by different people — so agreement between the two on the same gate list
is evidence about the gate list, and it is the only such evidence this project has.

**Two measured facts, both of which change the code rather than a comment.**

1. **qsim's state vector is single precision.** ``final_state_vector`` comes back with ``dtype``
   ``complex64`` and a measured ``itemsize`` of 8, so this engine holds half of what Aer holds per
   amplitude and the memory estimate here uses the smaller number. What that costs in the numbers
   was measured rather than inferred from the dtype: against Aer on Grover circuits of 9 to 17 qubits,
   the largest per-amplitude difference is ``4.2e-08`` on a 188-operation circuit and the smallest is
   ``1.1e-09`` on a 136-operation one. So the *amplitudes* carry single-precision rounding and a
   per-amplitude comparison at ``1e-9`` would fail on circuits that are provably equal.

   The comparison that is made, though, is an overlap up to a global phase, and that is second order
   in this error: the measured shortfall ``1 - |<aer|qsim>|`` is at most ``9.3e-15`` across those six
   configurations, which is five orders of magnitude inside the project's ``1e-9`` tolerance. Both
   numbers are asserted in ``tests/test_backends_cross_validation.py`` rather than described here.
   The consequence for a caller is narrow and worth stating: this engine's amplitudes are good to
   seven digits and any quantity formed from them is accurate to about fourteen, and a check on them
   has to be written as an overlap or as a tolerance in the ``1e-7`` range, not as an entry-by-entry
   comparison at double precision.

2. **cirq writes a statevector with the first qubit most significant.** An X on qubit 0 of a
   three-qubit circuit moves the amplitude to index 4, not to index 1 — measured, and the opposite
   of the IR's convention. Every statevector leaving this module therefore goes through
   :func:`~grover_emulator.backends.base_backend.from_most_significant_first`, and the test suite
   asserts the resulting convention by preparing a single X and reading the index back.
"""

from __future__ import annotations

import secrets
from typing import Any

import numpy as np

from ..circuits.compilers import to_cirq
from ..circuits.ir import GateList
from .base_backend import (
    MEMINFO_PATH,
    BackendError,
    BackendResult,
    QuantumBackend,
    from_most_significant_first,
    ir_metrics,
    statevector_bytes,
)

__all__ = ["CirqQsimBackend", "MEASUREMENT_KEY"]

MEASUREMENT_KEY = "m"
"""The key every measurement gate here uses. One key for the whole register: cirq's sampling returns
one array per key, and a per-qubit key would mean n arrays to reassemble in a fixed order."""

_SEED_MASK = 0x7FFFFFFF
"""qsim's seed is an integer it hashes into its own RNG; the mask keeps a drawn 64-bit seed inside a
range every consumer agrees on, and the masked value is what gets recorded."""


class CirqQsimBackend(QuantumBackend):
    """``qsimcirq`` over circuits compiled by :func:`grover_emulator.circuits.compilers.to_cirq`."""

    name = "cirq_qsim"
    requires = ("cirq", "qsimcirq")
    bytes_per_amplitude = 8
    """Measured: ``complex64``. See the module docstring."""

    def __init__(
        self,
        ram_budget_gb: float = 6.0,
        *,
        working_copies: float = 2.0,
        max_fused_gate_size: int = 2,
        meminfo_path: Any = MEMINFO_PATH,
    ):
        super().__init__(ram_budget_gb, working_copies=working_copies, meminfo_path=meminfo_path)
        if max_fused_gate_size < 1:
            raise ValueError(f"max_fused_gate_size must be at least 1, got {max_fused_gate_size}")
        self.max_fused_gate_size = int(max_fused_gate_size)

    # -- budget ----------------------------------------------------------------------------------

    def estimate_bytes(self, n_qubits: int) -> int:
        return statevector_bytes(
            n_qubits,
            bytes_per_amplitude=self.bytes_per_amplitude,
            working_copies=self.working_copies,
        )

    def describe(self) -> dict[str, Any]:
        return dict(
            super().describe(),
            method="statevector",
            precision="single",
            max_fused_gate_size=self.max_fused_gate_size,
        )

    # -- engine ----------------------------------------------------------------------------------

    def _simulator(self, seed: int | None):
        """A fresh simulator, seeded when a seed was given.

        qsim fuses up to ``max_fused_gate_size`` qubits into one kernel call, which is a performance
        knob and not a semantic one: the fused kernel is the same unitary. It is set here rather than
        left at its default so that a version bump cannot change what "the same circuit" means.
        """
        import qsimcirq

        options = qsimcirq.QSimOptions(max_fused_gate_size=self.max_fused_gate_size)
        if seed is None:
            return qsimcirq.QSimSimulator(options)
        return qsimcirq.QSimSimulator(options, seed=int(seed) & _SEED_MASK)

    def _qubits_and_circuit(self, gl: GateList):
        import cirq

        circuit = to_cirq(gl)
        qubits = cirq.LineQubit.range(gl.num_qubits)
        # An explicit order covering the whole declared width, not just the qubits some gate touched:
        # the amplitude array's length is part of the result, and a circuit that carries an unused
        # qubit must still produce 2**width amplitudes.
        return cirq, circuit, qubits

    @staticmethod
    def _versions() -> dict[str, str]:
        import cirq
        import qsimcirq

        return {"cirq": cirq.__version__, "qsimcirq": qsimcirq.__version__}

    def run_statevector(self, gl: GateList, *, seed: int | None = None) -> BackendResult:
        estimate = self.require_within_budget(gl.num_qubits)
        memory = self.memory_before()
        _cirq, circuit, qubits = self._qubits_and_circuit(gl)

        simulator = self._simulator(seed)
        start = self._timed()
        result = simulator.simulate(circuit, qubit_order=qubits)
        elapsed = self._timed() - start

        raw = np.asarray(result.final_state_vector)
        if raw.shape[0] != (1 << gl.num_qubits):
            raise BackendError(
                f"qsim returned {raw.shape[0]} amplitudes for {gl.num_qubits} qubits"
            )
        statevector = from_most_significant_first(raw, gl.num_qubits)

        return BackendResult(
            backend=self.name,
            label=gl.label,
            num_qubits=gl.num_qubits,
            method="statevector",
            statevector=np.asarray(statevector, dtype=complex),
            counts=None,
            shots=0,
            metrics=ir_metrics(gl),
            framework=dict(
                self._versions(),
                simulator="QSimSimulator",
                engine_method="statevector",
                precision="single",
                circuit_depth=len(circuit),
                circuit_ops=len(list(circuit.all_operations())),
                max_fused_gate_size=self.max_fused_gate_size,
                seed=None if seed is None else int(seed) & _SEED_MASK,
                qubit_order="LineQubit.range(width), most significant first",
                converted_from_msb_first=True,
            ),
            estimate_bytes=estimate,
            memory_before=memory,
            elapsed_s=elapsed,
        )

    def run_sampled(self, gl: GateList, *, shots: int, seed: int | None = None) -> BackendResult:
        """qsim's own sampler: the circuit plus one measurement gate over the whole register.

        The rows come back one column per qubit in the order the measurement names them, which is
        ascending, so column ``q`` is qubit ``q`` and packing a row as ``sum(bit_q << q)`` gives the
        IR's basis index directly. The statevector path needs a permutation and this one does not —
        an asymmetry that is a property of cirq's two interfaces and is asserted by test rather than
        trusted.
        """
        if shots < 1:
            raise ValueError(f"shots must be at least 1, got {shots}")
        drawn = secrets.randbits(64) if seed is None else int(seed)
        estimate = self.require_within_budget(gl.num_qubits)
        memory = self.memory_before()
        cirq, circuit, qubits = self._qubits_and_circuit(gl)

        measured = circuit + cirq.Circuit([cirq.measure(*qubits, key=MEASUREMENT_KEY)])
        simulator = self._simulator(drawn)
        start = self._timed()
        result = simulator.run(measured, repetitions=shots)
        elapsed = self._timed() - start

        rows = np.asarray(result.measurements[MEASUREMENT_KEY], dtype=np.int64)
        if rows.shape != (shots, gl.num_qubits):
            raise BackendError(
                f"qsim returned measurements of shape {rows.shape}, expected "
                f"{(shots, gl.num_qubits)}"
            )
        weights = np.int64(1) << np.arange(gl.num_qubits, dtype=np.int64)
        indices, counts = np.unique(rows @ weights, return_counts=True)

        return BackendResult(
            backend=self.name,
            label=gl.label,
            num_qubits=gl.num_qubits,
            method="sampled",
            statevector=None,
            counts={int(i): int(c) for i, c in zip(indices, counts)},
            shots=shots,
            metrics=ir_metrics(gl),
            framework=dict(
                self._versions(),
                simulator="QSimSimulator",
                engine_method="statevector",
                precision="single",
                circuit_depth=len(measured),
                circuit_ops=len(list(measured.all_operations())),
                max_fused_gate_size=self.max_fused_gate_size,
                seed=drawn & _SEED_MASK,
                sampler="native",
                measurement_key=MEASUREMENT_KEY,
            ),
            estimate_bytes=estimate,
            memory_before=memory,
            elapsed_s=elapsed,
        )
