"""Aer, the primary engine: exact statevector, and sampling that agrees with it.

Aer is primary because it is the fastest exact statevector engine here and because it runs the
circuit :func:`grover_emulator.circuits.compilers.to_qiskit` produced, instruction for instruction,
with nothing decomposed behind the accounting's back. The circuit is compiled from the IR, its width
is asserted equal to the IR's declared width before anything is run, and the IR's metrics are
attached to the result rather than the simulator's.

**Two measured facts this engine depends on.** Aer indexes a statevector with qubit 0 as the least
significant bit, which is the IR's convention, so nothing is permuted here — unlike cirq and quimb,
which both need the conversion. And Aer applies a multi-controlled Z natively through
``MCPhaseGate(pi, k - 1)``, which is the lowering the compilers use because ``MCZGate`` does not
exist in this version; a 24-control phase gate therefore costs one instruction rather than a
decomposition into thousands, which is what makes the truth-table oracle runnable at width 24.

**Seeding.** ``seed_simulator`` is a 31-bit field, so a drawn 64-bit seed is masked into range and
the *masked* value is what gets recorded. Recording the drawn value instead would be a record that
does not reproduce its own run, which is the failure mode :mod:`grover_emulator.utils.seeding` exists
to prevent.
"""

from __future__ import annotations

import secrets
import resource
from typing import Any

import numpy as np

from ..circuits.compilers import to_qiskit
from ..circuits.ir import GateList
from .base_backend import (
    MEMINFO_PATH,
    BackendError,
    BackendResult,
    QuantumBackend,
    ir_metrics,
    statevector_bytes,
)

__all__ = ["QiskitAerBackend"]

_SEED_MASK = 0x7FFFFFFF
"""``seed_simulator`` is a signed 32-bit field. Masking keeps a drawn seed inside it; the masked
value is recorded because that is the value that ran."""

SAVE_LABEL = "statevector"
"""The label the save instruction carries and the label the result is read back under.

The instruction is constructed and appended explicitly rather than through ``QuantumCircuit``'s
``save_statevector`` shortcut: that method only exists once ``qiskit_aer`` has been imported, because
it is registered onto the class as an import side effect. A module that calls it before importing
the provider works in a process where something else imported the provider first and fails with an
``AttributeError`` in one where nothing did — which is exactly the kind of state-dependent bug that
passes a test run and fails the run after it. ``from qiskit_aer.library import SaveStatevector`` has
no such condition.
"""


def _peak_rss_mb() -> float:
    """The process's peak resident set size, in MiB.

    ``ru_maxrss`` is Linux's high-water mark for the whole process, not for one call, so it is
    meaningful as "what this run's engine actually touched" only in a process that has not done
    anything larger. It is recorded as an observation alongside the estimate and is never used in
    the budget decision — an estimate that could only be checked after the allocation would not be
    a budget check.
    """
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


class QiskitAerBackend(QuantumBackend):
    """``qiskit-aer`` with ``method="statevector"``.

    The working-copy factor defaults to 2 and is documented rather than measured, because the
    number Aer holds is a property of its implementation: the simulator's own state vector, plus the
    copy ``save_statevector`` hands back into Python. Measured at width 24 in a fresh process: a
    uniform superposition of 24 qubits peaks the process at 367 MiB against 256 MiB of amplitudes,
    so the factor of 2 is not tight and is not meant to be — it is the reserve the budget is spent
    out of, and the peak observed on each run is recorded next to it.
    """

    name = "qiskit_aer"
    requires = ("qiskit", "qiskit_aer")
    bytes_per_amplitude = 16

    def __init__(
        self,
        ram_budget_gb: float = 6.0,
        *,
        working_copies: float = 2.0,
        max_parallel_threads: int = 1,
        meminfo_path: str | Any = MEMINFO_PATH,
    ):
        super().__init__(ram_budget_gb, working_copies=working_copies, meminfo_path=meminfo_path)
        if max_parallel_threads < 1:
            raise ValueError(f"max_parallel_threads must be at least 1, got {max_parallel_threads}")
        self.max_parallel_threads = int(max_parallel_threads)

    # -- budget ----------------------------------------------------------------------------------

    def estimate_bytes(self, n_qubits: int) -> int:
        return statevector_bytes(
            n_qubits,
            bytes_per_amplitude=self.bytes_per_amplitude,
            working_copies=self.working_copies,
        )

    def describe(self) -> dict[str, Any]:
        return dict(super().describe(), method="statevector", max_parallel_threads=self.max_parallel_threads)

    # -- engine ----------------------------------------------------------------------------------

    def _simulator(self, seed: int | None):
        """A fresh simulator per run: an AerSimulator carries state between runs and a reused one
        would make a run's result depend on what ran before it."""
        from qiskit_aer import AerSimulator

        options: dict[str, Any] = {
            "method": "statevector",
            "max_parallel_threads": self.max_parallel_threads,
        }
        if seed is not None:
            options["seed_simulator"] = int(seed) & _SEED_MASK
        return AerSimulator(**options)

    def _compile(self, gl: GateList):
        """The IR as a qiskit circuit, with the width assertion the accounting rests on."""
        from qiskit import transpile

        circuit = to_qiskit(gl)
        self._require_compiled_width(gl, circuit.num_qubits)
        return circuit, transpile

    @staticmethod
    def _save_statevector(circuit):
        """Append the statevector save instruction, by construction rather than by shortcut."""
        from qiskit_aer.library import SaveStatevector

        circuit.append(SaveStatevector(circuit.num_qubits, label=SAVE_LABEL), circuit.qubits)

    @staticmethod
    def _statevector_of(result):
        """The saved statevector, read back by label from the run's own data.

        ``Result.get_statevector`` looks the key up under a hard-coded ``"statevector"`` and takes the
        *experiment* as its argument, so a relabelled save would be invisible to it and a label passed
        where an experiment is expected would be a lookup that fails for a reason that reads like a
        missing result. Reading the data directly keeps the label in one place and makes a missing
        one an error that names the keys that were there.
        """
        data = result.data(0)
        if SAVE_LABEL not in data:
            raise BackendError(
                f"aer returned no {SAVE_LABEL!r}; the run's keys were {sorted(data)}"
            )
        return data[SAVE_LABEL]

    @staticmethod
    def _versions() -> dict[str, str]:
        import qiskit
        import qiskit_aer

        return {"qiskit": qiskit.__version__, "qiskit_aer": qiskit_aer.__version__}

    def run_statevector(self, gl: GateList, *, seed: int | None = None) -> BackendResult:
        estimate = self.require_within_budget(gl.num_qubits)
        memory = self.memory_before()
        circuit, transpile = self._compile(gl)
        # Read the framework-side depth before the save instruction is appended: a save is not part
        # of the circuit that was counted, and letting it into the framework's depth would make the
        # two numbers differ for a reason that has nothing to do with the circuit.
        framework_depth = circuit.depth()

        self._save_statevector(circuit)
        simulator = self._simulator(seed)
        start = self._timed()
        # optimization_level=0: from level 2 the transpiler elides a swap-like PERM into a *final
        # layout* instead of gates. The saved statevector is then in the permuted qubit order, and
        # nothing here undoes it — amplitudes land on the wrong indices with every other check
        # (gate names, qubits, norm) still correct. Aer fuses gates itself, so nothing is lost.
        result = simulator.run(
            transpile(circuit, simulator, optimization_level=0), shots=1
        ).result()
        elapsed = self._timed() - start
        if not result.success:
            raise BackendError(f"aer reported an unsuccessful run: {result.status}")

        statevector = np.asarray(self._statevector_of(result), dtype=complex)
        if statevector.shape[0] != (1 << gl.num_qubits):
            raise BackendError(
                f"aer returned {statevector.shape[0]} amplitudes for {gl.num_qubits} qubits"
            )

        return BackendResult(
            backend=self.name,
            label=gl.label,
            num_qubits=gl.num_qubits,
            method="statevector",
            # Aer's index convention is the IR's: qubit q carries bit q, measured by preparing a
            # single X and reading the index back. Nothing is permuted on this path.
            statevector=statevector,
            counts=None,
            shots=0,
            metrics=ir_metrics(gl),
            framework=dict(
                self._versions(),
                simulator="AerSimulator",
                engine_method="statevector",
                circuit_depth=framework_depth,
                circuit_ops=len(circuit.data),
                seed_simulator=None if seed is None else int(seed) & _SEED_MASK,
                peak_rss_mb=round(_peak_rss_mb(), 1),
            ),
            estimate_bytes=estimate,
            memory_before=memory,
            elapsed_s=elapsed,
        )

    def run_sampled(self, gl: GateList, *, shots: int, seed: int | None = None) -> BackendResult:
        """Aer's own sampler over the same circuit, seeded and recorded.

        The outcome keys are bit strings in which the leftmost character is the *highest*-numbered
        qubit, so reading a key as a base-2 integer gives the IR's little-endian basis index with no
        reversal. That is the opposite of the convention the same engine's statevector uses, which is
        why it is stated here rather than assumed from the statevector path.
        """
        if shots < 1:
            raise ValueError(f"shots must be at least 1, got {shots}")
        drawn = secrets.randbits(64) if seed is None else int(seed)
        estimate = self.require_within_budget(gl.num_qubits)
        memory = self.memory_before()
        circuit, transpile = self._compile(gl)
        framework_depth = circuit.depth()

        circuit.measure_all()
        simulator = self._simulator(drawn)
        start = self._timed()
        result = simulator.run(
            transpile(circuit, simulator, optimization_level=0), shots=shots
        ).result()
        elapsed = self._timed() - start
        if not result.success:
            raise BackendError(f"aer reported an unsuccessful run: {result.status}")

        counts = {int(key.replace(" ", ""), 2): int(value) for key, value in result.get_counts().items()}
        if sum(counts.values()) != shots:
            raise BackendError(
                f"aer returned {sum(counts.values())} outcomes for {shots} shots"
            )

        return BackendResult(
            backend=self.name,
            label=gl.label,
            num_qubits=gl.num_qubits,
            method="sampled",
            statevector=None,
            counts=counts,
            shots=shots,
            metrics=ir_metrics(gl),
            framework=dict(
                self._versions(),
                simulator="AerSimulator",
                engine_method="statevector",
                circuit_depth=framework_depth,
                circuit_ops=len(circuit.data),
                seed_simulator=drawn & _SEED_MASK,
                seed=drawn,
                sampler="native",
                peak_rss_mb=round(_peak_rss_mb(), 1),
            ),
            estimate_bytes=estimate,
            memory_before=memory,
            elapsed_s=elapsed,
        )
