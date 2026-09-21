"""Exact classical simulation of a permutation circuit of any width, many inputs at a time.

:mod:`grover_emulator.utils.validation` packs one basis state into a ``uint64`` and so stops at 63
qubits. A reversible hash is some eight hundred qubits wide, and the whole reason to build one is to
check it against the hash it claims to be — so it needs a simulator with no width limit.

This one is **bit-sliced**. Instead of one integer per basis state, there is one Python integer per
*qubit*, and bit ``j`` of that integer is the qubit's value in the ``j``-th test input. A gate then
acts on every test input at once with a single big-integer operation::

    X    q          column[q] ^= all_ones
    CX   c, t       column[t] ^= column[c]
    CCX  a, b, t    column[t] ^= column[a] & column[b]
    MCX  c..., t    column[t] ^= AND of the control columns

Python integers are arbitrary precision, so neither the number of qubits nor the number of
simultaneous inputs is bounded by a machine word. It is exact for the same reason the ``uint64``
simulator is: a circuit of X/CX/CCX/MCX sends each basis state to exactly one basis state, so
following trajectories *is* the circuit. Gates that create superposition (``H``) or carry phase
(``S``, ``T``, ``MCZ``) are refused rather than skipped — a hash circuit has no business containing
one, and silently ignoring a phase gate would verify a circuit that is not the one that was built.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from ..circuits.ir import GateList, GateName

__all__ = ["WideSimulationError", "simulate_bitsliced", "pack_columns", "unpack_register"]

_PERMUTATION_GATES = (GateName.X, GateName.CX, GateName.CCX, GateName.MCX)


class WideSimulationError(RuntimeError):
    """The gate list is not a circuit of basis permutations, so a trajectory is not the circuit."""


def simulate_bitsliced(gl: GateList, columns: Sequence[int], n_inputs: int) -> list[int]:
    """Run ``gl`` on ``n_inputs`` basis states at once; return the final per-qubit columns.

    Args:
        gl: a gate list of ``X``/``CX``/``CCX``/``MCX`` only.
        columns: one integer per qubit, ``len(columns) == gl.num_qubits``; bit ``j`` of
            ``columns[q]`` is qubit ``q`` in test input ``j``.
        n_inputs: how many test inputs the columns carry. Needed because ``X`` must flip exactly
            those bits: an ``X`` that flipped bits above ``n_inputs`` would leave garbage that a
            later comparison against a packed expectation would read as a failure of the circuit.
    """
    if len(columns) != gl.num_qubits:
        raise ValueError(f"{len(columns)} columns for a {gl.num_qubits}-qubit gate list")
    if n_inputs < 1:
        raise ValueError("n_inputs must be at least 1")
    ones = (1 << n_inputs) - 1
    state = [int(c) & ones for c in columns]
    for gate in gl.gates:
        name, q = gate.name, gate.qubits
        if name is GateName.CCX:
            state[q[2]] ^= state[q[0]] & state[q[1]]
        elif name is GateName.CX:
            state[q[1]] ^= state[q[0]]
        elif name is GateName.X:
            state[q[0]] ^= ones
        elif name is GateName.MCX:
            product = ones
            for control in q[:-1]:
                product &= state[control]
            state[q[-1]] ^= product
        else:
            raise WideSimulationError(
                f"{name.value} is not a basis permutation; the bit-sliced simulator follows "
                "trajectories and is exact only for X/CX/CCX/MCX"
            )
    return state


def pack_columns(num_qubits: int, registers: Iterable[tuple[Sequence[int], Sequence[int]]]) -> list[int]:
    """Columns for a circuit whose named registers hold the given values and all else is zero.

    ``registers`` yields ``(qubits, values)``: ``qubits[i]`` carries bit ``i`` of each value
    (little-endian, the IR's convention), and ``values[j]`` is that register's content in test
    input ``j``.
    """
    columns = [0] * num_qubits
    for qubits, values in registers:
        for j, value in enumerate(values):
            if value < 0 or value >> len(qubits):
                raise ValueError(f"value {value} does not fit a {len(qubits)}-qubit register")
            for i, qubit in enumerate(qubits):
                if (value >> i) & 1:
                    columns[qubit] |= 1 << j
    return columns


def unpack_register(columns: Sequence[int], qubits: Sequence[int], n_inputs: int) -> list[int]:
    """The register's value in each test input — the inverse of :func:`pack_columns`."""
    return [
        sum(((columns[qubit] >> j) & 1) << i for i, qubit in enumerate(qubits))
        for j in range(n_inputs)
    ]
