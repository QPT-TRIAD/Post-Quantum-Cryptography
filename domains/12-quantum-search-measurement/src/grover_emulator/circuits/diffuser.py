"""The Grover diffuser: inversion about the mean.

``H^n . X^n . (multi-controlled Z) . X^n . H^n``

Built from primitives rather than imported as ``qiskit.circuit.library.GroverOperator``, so that the
circuit is auditable line by line and its gate count is the count of what actually runs. A test
compares it against Qiskit's own ``GroverOperator`` as an independent check — the point of that test
is to catch a mistake in this file, which is why this file does not call it.

The X-conjugation turns "all ones" into "all zeros", which is what the uniform superposition
``H^n|0>`` is centred on. Applying the multi-controlled Z without it would invert about the
all-ones state instead, which is a different operator and would show up as a success curve that
never rises.
"""

from __future__ import annotations

from .ir import GateList, GateName

__all__ = ["build_diffuser"]


def build_diffuser(n_qubits: int) -> GateList:
    """The diffuser over ``n_qubits``, in the IR.

    Acts on the search register only. The oracle's ancillas are returned to ``|0>`` by its own
    sandwich, so the diffuser never has to know about them.
    """
    if n_qubits < 1:
        raise ValueError(f"a diffuser needs at least 1 qubit, got {n_qubits}")

    gl = GateList(n_qubits, label=f"diffuser[{n_qubits}]")
    qubits = list(range(n_qubits))

    for q in qubits:
        gl.append(GateName.H, q)
    for q in qubits:
        gl.append(GateName.X, q)

    if n_qubits == 1:
        # mcz on one qubit is the Pauli Z; there are no controls to add.
        gl.append(GateName.MCZ, qubits[0])
    else:
        gl.append(GateName.MCZ, *qubits)

    for q in qubits:
        gl.append(GateName.X, q)
    for q in qubits:
        gl.append(GateName.H, q)
    return gl
