"""The phase oracle: ``diag((-1)**f)`` built as a sandwich, not asserted from theory.

The construction is the same for every spec and both lowerings:

    predicate  ->  Z on the flag  ->  predicate**-1

which is the standard oracle sandwich. Its correctness rests on nothing about the predicate except
the contract in :mod:`grover_emulator.problem.oracle_spec`: the predicate sets ``flag ^= [x marked]``
and its exact inverse undoes it completely. Since the inverse is taken at the IR level — gates
reversed, each replaced by its exact inverse — the sandwich is the identity up to the phase on the
flag, for any predicate that honours the contract, whether or not it cleaned up after itself.

**The inverse is never a framework's ``.inverse()``.** ``QuantumCircuit.inverse()`` may resynthesise
rather than reverse, so the circuit that runs would not be the circuit that was counted. Reversing
the gate list is exact and is the only inverse this project will accept.
"""

from __future__ import annotations

from ..problem.oracle_spec import Lowering, OracleSpec
from .ir import GateList, GateName

__all__ = ["build_phase_oracle", "oracle_width"]


def oracle_width(spec: OracleSpec, lowering: Lowering) -> int:
    """Total width of the oracle circuit: search register, ancillas, and the flag."""
    return spec.search_width() + spec.ancilla_width(lowering) + 1


def build_phase_oracle(spec: OracleSpec, lowering: Lowering = Lowering.TRUTH_TABLE) -> GateList:
    """The oracle as a gate list over ``search_width + ancilla_width + 1`` qubits.

    The flag is the last qubit. Applying this to ``|x>|0...0>|0>`` gives
    ``(-1)**[x marked] |x>|0...0>|0>`` — the ancillas come back clean because the second half is the
    first half's exact inverse, which is the whole reason the predicate is allowed to be untidy.
    """
    predicate = spec.build_predicate(lowering)
    flag = predicate.num_qubits - 1

    gl = predicate.copy()
    gl.append(GateName.MCZ, flag)  # a one-qubit mcz is the Pauli Z
    gl.extend(predicate.inverse())
    gl.label = f"{spec.name}:{lowering.value}:oracle"
    return gl
