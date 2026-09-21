"""An exact statevector engine for the analysis tests — a test double, not a backend.

The analysis layer is written against one method (:class:`grover_emulator.analysis.success_probability.
StatevectorBackend`): hand it a gate list, get the amplitudes back. That is the whole contract, and it
is deliberately narrow, so a test can satisfy it with something small and self-contained rather than
depending on the engine that production runs on. This file is that something.

It is exact, not approximate: it applies the IR gates as the linear maps they are, on a dense
``2**n`` complex array, with no truncation and no tolerance. Its cost is the honest statevector cost,
which is why the tests that use it stay at search widths a statevector can hold — and why the
arithmetic lowering, at 50 qubits, is exercised through the classical bitmask simulator in
:mod:`grover_emulator.utils.validation` instead.

The thing that makes a test double acceptable here is that it is not trusted on its own word: the
gate semantics it implements are the same analytic matrices :mod:`tests.test_ir` checks the compilers
against, and ``test_analysis.py`` compares its output to a Qiskit ``Operator`` on a circuit that
contains every gate in the set. A double that was wrong would make every "measured" number in these
tests wrong, so it is checked against an independent construction rather than against itself.
"""

from __future__ import annotations

import numpy as np

from grover_emulator.circuits.ir import Gate, GateList, GateName

__all__ = ["ReferenceStatevector"]

_HADAMARD = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=complex) / np.sqrt(2.0)

_SINGLE_QUBIT_PHASES: dict[GateName, complex] = {
    GateName.S: 1j,
    GateName.SDG: -1j,
    GateName.T: np.exp(1j * np.pi / 4.0),
    GateName.TDG: np.exp(-1j * np.pi / 4.0),
}


class ReferenceStatevector:
    """A dense exact statevector engine over the IR gate set.

    Constructed once and reused: the object holds no state between calls, so a circuit run twice
    gives bit-identical amplitudes.
    """

    name = "reference_statevector"

    def __init__(self, n_qubits_max: int = 24):
        self.n_qubits_max = n_qubits_max
        self.runs = 0

    # -- the contract the analysis layer needs -------------------------------------------------

    def statevector(self, circuit: GateList) -> np.ndarray:
        """The exact final amplitudes, little-endian: bit ``q`` of the index is qubit ``q``."""
        if circuit.num_qubits > self.n_qubits_max:
            raise ValueError(
                f"{circuit.label or 'circuit'} is {circuit.num_qubits} qubits wide; this reference "
                f"engine is capped at {self.n_qubits_max} (a dense complex128 array of 2**n), which "
                "is a statement about memory rather than about the circuit"
            )
        self.runs += 1
        state = np.zeros(1 << circuit.num_qubits, dtype=complex)
        state[0] = 1.0
        for gate in circuit.gates:
            self._apply(state, gate, circuit.num_qubits)
        return state

    # -- gate application ---------------------------------------------------------------------

    def _apply(self, state: np.ndarray, gate: Gate, num_qubits: int) -> None:
        name = gate.name
        if name is GateName.H:
            self._apply_single(state, gate.qubits[0], _HADAMARD)
            return
        if name is GateName.X:
            self._apply_single(state, gate.qubits[0], np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex))
            return
        if name is GateName.CX:
            self._apply_controlled(state, gate.qubits[:1], gate.qubits[1], num_qubits)
            return
        if name in (GateName.CCX, GateName.MCX):
            self._apply_controlled(state, gate.qubits[:-1], gate.qubits[-1], num_qubits)
            return
        if name is GateName.MCZ:
            self._apply_mcz(state, gate.qubits, num_qubits)
            return
        if name in _SINGLE_QUBIT_PHASES:
            view = state.reshape(-1, 2, 1 << gate.qubits[0])
            view[:, 1, :] *= _SINGLE_QUBIT_PHASES[name]
            return
        if name is GateName.PERM:
            self._apply_perm(state, gate, num_qubits)
            return
        raise ValueError(f"the reference engine has no implementation for {name!r}")

    def _apply_single(self, state: np.ndarray, qubit: int, matrix: np.ndarray) -> None:
        """A 2x2 matrix on one qubit, by reshaping so that the qubit's bit is the middle axis.

        The reshape is exact: the flat index is ``high * 2**(q+1) + bit * 2**q + low``, so
        ``(high, bit, low)`` is precisely a C-order view of the amplitude array.
        """
        view = state.reshape(-1, 2, 1 << qubit)
        zero = view[:, 0, :].copy()
        one = view[:, 1, :].copy()
        view[:, 0, :] = matrix[0, 0] * zero + matrix[0, 1] * one
        view[:, 1, :] = matrix[1, 0] * zero + matrix[1, 1] * one

    def _apply_controlled(
        self, state: np.ndarray, controls: tuple[int, ...], target: int, num_qubits: int
    ) -> None:
        """X on ``target`` where every control is 1 — a conditional swap of two amplitude slices.

        The swap is done on a copy of the source slice because the two index sets interleave: writing
        in place would read values the same gate had already overwritten.
        """
        index = np.arange(1 << num_qubits, dtype=np.int64)
        condition = np.ones(1 << num_qubits, dtype=bool)
        for control in controls:
            condition &= ((index >> control) & 1).astype(bool)
        source = index[condition]
        image = source ^ (1 << target)
        held = state[source].copy()
        state[source] = state[image]
        state[image] = held

    def _apply_mcz(self, state: np.ndarray, qubits: tuple[int, ...], num_qubits: int) -> None:
        """``-1`` on every basis state whose listed qubits are all 1."""
        index = np.arange(1 << num_qubits, dtype=np.int64)
        condition = np.ones(1 << num_qubits, dtype=bool)
        for qubit in qubits:
            condition &= ((index >> qubit) & 1).astype(bool)
        state[condition] *= -1.0

    def _apply_perm(self, state: np.ndarray, gate: Gate, num_qubits: int) -> None:
        """An arbitrary b-qubit basis permutation, by explicit index arithmetic.

        Little-endian, per the IR: bit ``k`` of the basis index is ``gate.qubits[k]``, and the gate
        writes bit ``k`` of ``table[src]`` back into ``gate.qubits[k]``. Written out rather than
        reshaped because the qubits of a permutation need not be contiguous.
        """
        table = np.asarray(gate.params[0], dtype=np.int64)
        index = np.arange(1 << num_qubits, dtype=np.int64)
        sub = np.zeros_like(index)
        clear = np.int64(0)
        for k, qubit in enumerate(gate.qubits):
            sub |= ((index >> qubit) & 1) << k
            clear |= np.int64(1) << np.int64(qubit)
        image = np.asarray(table)[sub]
        destination = index & ~clear
        for k, qubit in enumerate(gate.qubits):
            destination |= ((image >> k) & 1) << qubit
        moved = np.empty_like(state)
        moved[destination] = state[index]
        state[...] = moved
