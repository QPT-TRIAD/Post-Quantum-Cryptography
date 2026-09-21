"""Compilers between the gate-list IR and the two frameworks.

Two directions, and both are load-bearing:

**Outward** — ``to_qiskit`` / ``to_cirq`` turn a :class:`~grover_emulator.circuits.ir.GateList`
into a runnable circuit. These are pure compilers: they contain no arithmetic and no physics, which
is what makes a disagreement between the two engines evidence about the engines rather than about
the circuit.

**Inward** — ``from_qiskit`` / ``from_cirq`` read a circuit back into the IR. This is not a
convenience. Without it, the gate list that was *counted* is not provably the circuit that *ran*,
and every gate count in every report is fiction. The round-trip is asserted by the test suite, and
:func:`assert_round_trip` is what makes the assertion cheap to write.

There is a third direction, and it is the reason this module exists at all:
``import_definition`` expands a vetted framework gate — ``CDKMRippleCarryAdder``, say — into IR
gates by walking its own ``.definition``. That lets a block be built from a construction someone
else has tested while the *accounting* stays in the IR. A framework gate that is left unexpanded
declares its own width and hides its ancillas; the probe found ``WeightedSumGate`` doing exactly
that, which is why nothing here emits an unexpanded framework gate except ``UnitaryGate`` for
``perm``, whose width is exactly its matrix dimension.
"""

from __future__ import annotations

import numpy as np

from .ir import Gate, GateList, GateName

__all__ = [
    "ToQiskitError",
    "to_qiskit",
    "from_qiskit",
    "to_cirq",
    "from_cirq",
    "import_definition",
    "assert_round_trip",
]


class ToQiskitError(RuntimeError):
    """A gate list could not be compiled, or a framework object could not be read back."""


# -----------------------------------------------------------------------------------------------
# outward: IR -> framework
# -----------------------------------------------------------------------------------------------

_QISKIT_SIMPLE = {
    GateName.X: "x",
    GateName.H: "h",
    GateName.CX: "cx",
    GateName.CCX: "ccx",
    GateName.S: "s",
    GateName.SDG: "sdg",
    GateName.T: "t",
    GateName.TDG: "tdg",
}


def to_qiskit(gl: GateList):
    """Compile a gate list to a ``qiskit.QuantumCircuit``.

    Qubit indices in the IR become qubit indices in the circuit, and the circuit's width is the
    IR's declared width. Nothing is transpiled and nothing is decomposed: the circuit that comes out
    is the gate list, one instruction per gate, in order. That property is what
    :func:`from_qiskit` depends on and what the round-trip test asserts.
    """
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import MCPhaseGate, MCXGate, UnitaryGate

    qc = QuantumCircuit(gl.num_qubits, name=gl.label or "ir")
    for gate in gl.gates:
        if gate.name in _QISKIT_SIMPLE:
            getattr(qc, _QISKIT_SIMPLE[gate.name])(*gate.qubits)
        elif gate.name is GateName.MCX:
            qc.append(MCXGate(len(gate.qubits) - 1), list(gate.qubits))
        elif gate.name is GateName.MCZ:
            if len(gate.qubits) == 1:
                qc.z(gate.qubits[0])
            else:
                # MCZGate does not exist in qiskit 2.5.2; MCPhaseGate(pi, k-1) is exactly it, and the
                # API probe verifies that over every basis state at k=3.
                qc.append(MCPhaseGate(np.pi, len(gate.qubits) - 1), list(gate.qubits))
        elif gate.name is GateName.PERM:
            qc.append(UnitaryGate(_permutation_matrix(gate.params[0])), list(gate.qubits))
        else:  # pragma: no cover - the enum is closed
            raise ToQiskitError(f"no qiskit lowering for {gate.name!r}")
    return qc


def _permutation_matrix(table) -> np.ndarray:
    """The unitary matrix of a basis-state permutation: ``M[table[i], i] = 1``."""
    n = len(table)
    m = np.zeros((n, n), dtype=complex)
    for src, dst in enumerate(table):
        m[dst, src] = 1.0
    return m


def _bit_reversal(n: int) -> np.ndarray:
    """The permutation that reverses the bit order of a basis index."""
    k = n.bit_length() - 1
    r = np.zeros((n, n), dtype=complex)
    for i in range(n):
        r[int(format(i, f"0{k}b")[::-1], 2), i] = 1.0
    return r


def _cirq_matrix_convention(m: np.ndarray) -> np.ndarray:
    """Re-express a matrix between qiskit's and cirq's qubit-ordering conventions.

    qiskit reads qubit 0 as the least significant bit; cirq reads the *first* qubit of an operation
    as the **most** significant. The same matrix therefore describes two different operations, and
    passing it unchanged to :class:`cirq.MatrixGate` silently runs something else — the exact
    failure mode this project exists to catch, since the gate list that was counted would no longer
    be the circuit that ran.

    Conjugating by the bit-reversal permutation converts one reading into the other. That
    permutation is its own inverse, so this function is an involution and ``to_cirq`` and
    ``from_cirq`` can share it rather than each carrying half of the conversion.

    Only ``PERM`` needs this. Every other gate in the set is a named cirq gate whose meaning does
    not depend on how the matrix is indexed.
    """
    r = _bit_reversal(m.shape[0])
    return r @ m @ r


def from_qiskit(qc) -> GateList:
    """Read a ``QuantumCircuit`` back into the IR.

    Reads ``circuit.data`` in order, so a compiler that drops, duplicates or reorders a gate is
    caught rather than accommodated. Anything outside the IR's gate set raises rather than being
    silently mapped — an unlowered framework gate is exactly the case where the accounting would
    stop describing the circuit.
    """
    from qiskit.circuit.library import MCPhaseGate, MCXGate, UnitaryGate

    name_of = {
        "x": GateName.X,
        "h": GateName.H,
        "cx": GateName.CX,
        "ccx": GateName.CCX,
        "s": GateName.S,
        "sdg": GateName.SDG,
        "t": GateName.T,
        "tdg": GateName.TDG,
        # A bare Pauli Z is the one-qubit case of mcz, and the compiler emits it that way, so it has
        # to come back that way or the round-trip would depend on which lowering wrote the gate.
        "z": GateName.MCZ,
    }
    gl = GateList(qc.num_qubits)
    qubit_index = {q: i for i, q in enumerate(qc.qubits)}

    for instruction in qc.data:
        op = instruction.operation
        qubits = tuple(qubit_index[q] for q in instruction.qubits)
        key = op.name.lower()

        if key in name_of:
            gl.append(name_of[key], *qubits)
        elif isinstance(op, MCXGate):
            gl.append(GateName.MCX, *qubits)
        elif isinstance(op, MCPhaseGate):
            lam = float(np.real(np.asarray(op.params[0], dtype=complex)))
            if abs(abs(lam) - np.pi) > 1e-9:
                raise ToQiskitError(f"MCPhaseGate with angle {lam} cannot be read back as mcz")
            gl.append(GateName.MCZ, *qubits)
        elif isinstance(op, UnitaryGate):
            gl.append(GateName.PERM, *qubits, params=(_table_from_matrix(op.to_matrix()),))
        else:
            raise ToQiskitError(
                f"instruction {op.name!r} is not in the IR gate set; the gate list that would be "
                "counted is not the circuit that would run"
            )
    return gl


def _table_from_matrix(m: np.ndarray) -> tuple[int, ...]:
    """Recover a permutation table from its matrix, refusing anything that is not a permutation."""
    if m.shape[0] != m.shape[1]:
        raise ToQiskitError(f"matrix is {m.shape}, not square")
    table = []
    for col in range(m.shape[1]):
        column = m[:, col]
        nz = np.nonzero(np.abs(column) > 1e-9)[0]
        if len(nz) != 1 or abs(abs(column[nz[0]]) - 1.0) > 1e-9:
            raise ToQiskitError(f"column {col} is not a single unit entry; not a permutation")
        table.append(int(nz[0]))
    if sorted(table) != list(range(len(table))):
        raise ToQiskitError("the matrix maps two inputs to the same output; not a permutation")
    return tuple(table)


# -----------------------------------------------------------------------------------------------
# inward: framework -> IR
# -----------------------------------------------------------------------------------------------


def import_definition(gate) -> tuple[GateList, int]:
    """Expand a framework gate's own ``.definition`` into IR gates.

    Returns the gate list over the definition's qubit order, and the number of qubits it declared.
    Raises if the gate has no definition or if the definition uses an operation outside the IR gate
    set — an unlowerable block would have to be counted as an opaque blob, and an opaque blob is
    precisely what this project exists to avoid.

    Block order follows the definition's own qubit ordering, so the caller wires the returned list by
    mapping its qubit ``k`` to the index the block should occupy.
    """
    definition = getattr(gate, "definition", None)
    if definition is None:
        raise ToQiskitError(
            f"{type(gate).__name__} has no .definition; it cannot be expanded into IR gates and "
            "would have to be counted as opaque"
        )
    gl = from_qiskit(definition)
    if gl.num_qubits != gate.num_qubits:
        raise ToQiskitError(
            f"{type(gate).__name__} declares {gate.num_qubits} qubits but its definition uses "
            f"{gl.num_qubits}; a discrepancy here is a hidden-ancilla bug"
        )
    return gl, gate.num_qubits


def relabel(gl: GateList, mapping: dict[int, int], num_qubits: int, *, invert: bool = False) -> GateList:
    """Copy a gate list onto new qubit indices.

    ``mapping`` sends the block's own qubit index to the target index. With ``invert`` the returned
    list is the block's exact inverse, which is how an uncompute is built from the block that
    computed it rather than from a framework's ``.inverse()``.
    """
    out = GateList(num_qubits, label=gl.label)
    for gate in gl.gates:
        out.gates.append(Gate(gate.name, tuple(mapping[q] for q in gate.qubits), gate.params))
    return out.inverse() if invert else out


# -----------------------------------------------------------------------------------------------
# outward: IR -> cirq
# -----------------------------------------------------------------------------------------------


def to_cirq(gl: GateList):
    """Compile a gate list to a ``cirq.Circuit``, tagging each op with its IR index.

    Cirq does not preserve insertion order across moments, so each op carries an ``ir:<index>`` tag
    and :func:`from_cirq` sorts on it. That makes the round-trip a real check — every IR gate must
    appear exactly once — rather than a check that depends on cirq's scheduling.
    """
    import cirq

    qubits = cirq.LineQubit.range(gl.num_qubits)
    ops = []
    for index, gate in enumerate(gl.gates):
        q = [qubits[i] for i in gate.qubits]
        k = len(gate.qubits)

        if gate.name is GateName.X:
            op = cirq.X(q[0])
        elif gate.name is GateName.H:
            op = cirq.H(q[0])
        elif gate.name is GateName.CX:
            op = cirq.CNOT(q[0], q[1])
        elif gate.name is GateName.CCX:
            op = cirq.TOFFOLI(q[0], q[1], q[2])
        elif gate.name is GateName.MCX:
            op = cirq.X(q[-1]).controlled_by(*q[:-1])
        elif gate.name is GateName.MCZ:
            op = cirq.Z(q[0]) if k == 1 else cirq.Z(q[-1]).controlled_by(*q[:-1])
        elif gate.name is GateName.S:
            op = cirq.S(q[0])
        elif gate.name is GateName.SDG:
            op = cirq.S(q[0]) ** -1
        elif gate.name is GateName.T:
            op = cirq.T(q[0])
        elif gate.name is GateName.TDG:
            op = cirq.T(q[0]) ** -1
        elif gate.name is GateName.PERM:
            op = cirq.MatrixGate(
                _cirq_matrix_convention(_permutation_matrix(gate.params[0]))
            ).on(*q)
        else:  # pragma: no cover
            raise ToQiskitError(f"no cirq lowering for {gate.name!r}")

        ops.append(op.with_tags(f"ir:{index}"))

    return cirq.Circuit(ops)


def from_cirq(circuit) -> GateList:
    """Read a ``cirq.Circuit`` back into the IR, using the ``ir:<index>`` tags for order."""
    import cirq

    tagged: list[tuple[int, Gate]] = []
    for op in circuit.all_operations():
        tags = [t for t in getattr(op, "tags", ()) if isinstance(t, str) and t.startswith("ir:")]
        if len(tags) != 1:
            raise ToQiskitError(
                f"operation {op} carries {len(tags)} ir: tags; it was not produced by to_cirq"
            )
        index = int(tags[0][3:])
        qubits = tuple(int(q.x) for q in op.qubits)
        tagged.append((index, _cirq_op_to_gate(op, qubits)))

    tagged.sort(key=lambda pair: pair[0])
    for expected, (index, _) in enumerate(tagged):
        if index != expected:
            raise ToQiskitError(f"ir: tag {index} out of sequence, expected {expected}")

    num_qubits = max((max(g.qubits) + 1 for _, g in tagged), default=0)
    gl = GateList(num_qubits)
    gl.gates = [g for _, g in tagged]
    return gl


# Measured, not assumed. cirq's phase gates are all ZPowGate, and their exponents are:
#     S -> 0.5    S**-1 -> -0.5    T -> 0.25    T**-1 -> -0.25
# Matching them by identity against `cirq.S` / `cirq.T` gets two of the four right and silently
# mismatches the other two, which is why this is a table keyed by the measured exponent.
#
# The X-like gates are matched by *measured* class name as well, for the same reason: `cirq.CNOT`
# is a `CXPowGate`, not a `CNotPowGate` as its name suggests, and the subclass relations between
# these are not what a reader would predict. Arity is checked alongside the name so that a
# misclassification cannot produce a gate of the wrong width.
_CIRQ_Z_EXPONENT = {
    0.5: GateName.S,
    -0.5: GateName.SDG,
    0.25: GateName.T,
    -0.25: GateName.TDG,
}

# cirq normalises controlled gates by folding as many controls as it has a dedicated class for.
# `cirq.X(q).controlled_by(a, b)` is a CCXPowGate and `cirq.Z(q).controlled_by(a, b)` is a
# CCZPowGate — neither is a ControlledGate — while a fourth control wraps one in a ControlledGate
# whose sub_gate is the three-control form. Measured at every arity rather than guessed:
#
#     mcz on 1, 2, 3 qubits -> _PauliZ, CZPowGate, CCZPowGate
#     mcz on 4+ qubits      -> ControlledGate wrapping CCZPowGate
#
# so a reader that only handled ControlledGate, or only the named classes, would cover half the
# range and fail on the other half.
_CIRQ_X_LIKE = {
    "_PauliX": 1,
    "XPowGate": 1,
    "CXPowGate": 2,
    "CNotPowGate": 2,
    "CCXPowGate": 3,
}
_CIRQ_Z_LIKE = {
    "_PauliZ": 1,
    "CZPowGate": 2,
    "CCZPowGate": 3,
}


def _cirq_op_to_gate(op, qubits: tuple[int, ...]) -> Gate:
    import cirq

    gate = op.gate
    if isinstance(gate, cirq.MatrixGate):
        # cirq.MatrixGate keeps its matrix private; the public route is cirq.unitary. The matrix is
        # converted back out of cirq's ordering convention before the table is read off it — the
        # inverse of what to_cirq applied, which is this same call because it is an involution.
        matrix = _cirq_matrix_convention(cirq.unitary(gate))
        return Gate(GateName.PERM, qubits, (_table_from_matrix(matrix),))
    if cirq.is_parameterized(gate):
        raise ToQiskitError(f"cirq operation {op} has a symbolic exponent")

    # Unwrap any ControlledGate wrapping, so the base class decides X-like versus Z-like. The
    # control values are checked: an open (negatively controlled) gate is not in the IR's set, and
    # reading it as a closed one would invert the meaning of a control without any symptom.
    # control_values is a ProductOfSums whose elements are tuples: (1,) for a closed control and
    # (0,) for an open one. Comparing an element against the integer 1 tests nothing useful — every
    # closed control would read as open — so the membership test is on the element's contents.
    base = gate
    while isinstance(base, cirq.ControlledGate):
        for value in base.control_values:
            if 1 not in tuple(value):
                raise ToQiskitError(f"cirq operation {op} has an open control; not in the IR set")
        base = base.sub_gate

    tname = type(base).__name__
    exponent = float(getattr(base, "exponent", 1.0))
    n = len(qubits)

    if tname in _CIRQ_X_LIKE and exponent == 1.0:
        arity = _CIRQ_X_LIKE[tname]
        if n == arity:
            # cirq's two- and three-qubit X forms map onto the smaller IR gates, so a two-control
            # gate is never counted as a multi-controlled one.
            return Gate({1: GateName.X, 2: GateName.CX, 3: GateName.CCX}[arity], qubits)
        if n > arity:
            # A ControlledGate wrapping the three-control form: controls first, target last, which
            # is the IR's mcx convention. Verified by the round-trip test, not assumed.
            return Gate(GateName.MCX, qubits)

    if tname in _CIRQ_Z_LIKE and exponent == 1.0 and n >= _CIRQ_Z_LIKE[tname]:
        return Gate(GateName.MCZ, qubits)

    if tname == "HPowGate" and exponent == 1.0 and n == 1:
        return Gate(GateName.H, qubits)
    if tname == "ZPowGate" and n == 1:
        name = _CIRQ_Z_EXPONENT.get(exponent)
        if name is not None:
            return Gate(name, qubits)
    raise ToQiskitError(f"cirq operation {op} is not in the IR gate set")


# -----------------------------------------------------------------------------------------------
# the assertion the accounting rests on
# -----------------------------------------------------------------------------------------------


def assert_round_trip(gl: GateList) -> None:
    """Assert that both frameworks give the gate list back unchanged.

    This is acceptance condition 8 of the build plan. If it does not hold, the gate list that was
    counted is not the circuit that ran, and the Toffoli count, the depth and the T-count describe
    something nobody executed.
    """
    if gl.gates != from_qiskit(to_qiskit(gl)).gates:
        raise AssertionError("qiskit round-trip changed the gate list")
    if gl.gates != from_cirq(to_cirq(gl)).gates:
        raise AssertionError("cirq round-trip changed the gate list")
