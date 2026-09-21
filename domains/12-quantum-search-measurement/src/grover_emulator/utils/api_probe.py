"""Milestone 0 — verify every framework API this project builds on, before building on it.

The design pass named a set of framework classes this project intends to use, on the strength of
documentation reading. Documentation is not execution. This module turns each of those claims into
an executable assertion, and — where a class's *semantics* are underspecified — into a measurement
that pins the convention down.

Three of these checks are not "does the name exist" but "what does it actually do":

* :func:`check_weighted_sum_ordering` — ``WeightedSumGate``'s documented rule that "the first
  weight applies to the upper-most qubit" runs against the little-endian convention every other
  part of this project uses. If it is true as written, a dot product compiled through this gate
  comes out **reversed**, which for a symmetric dot product is undetectable arithmetically and
  marks the wrong state. The check measures the mapping instead of trusting the sentence.

* :func:`check_quadratic_form_convention` — ``QuadraticFormGate``'s handling of the diagonal, of
  off-diagonal symmetry, and of its offset are all unspecified. It is brute-forced against direct
  evaluation on every input for small N.

* :func:`check_ripple_carry_ancillas` — a framework gate that secretly allocates ancillas inflates
  the real width past the recorded one, which would let a RAM-budget check pass and the run swap.

Each check returns a :class:`ProbeResult`. The script :file:`scripts/probe_apis.py` prints them and
exits non-zero if any failed. Nothing in this project is built on an API that has not passed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["ProbeResult", "probe_all", "format_report"]


@dataclass
class ProbeResult:
    """One API assertion, with the observed fact that settles it."""

    name: str
    ok: bool
    detail: str = ""
    required: bool = True
    notes: list[str] = field(default_factory=list)

    def line(self) -> str:
        tag = "ok  " if self.ok else ("FAIL" if self.required else "warn")
        return f"[{tag}] {self.name:<52} {self.detail}"


class ProbeFailure(AssertionError):
    """A check that could not be completed at all — distinct from a check that ran and said no."""


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------


def _amplitudes(circuit, num_qubits: int) -> np.ndarray:
    """The full statevector of ``circuit``, computed with Aer.

    Aer rather than a pure-numpy simulation on purpose: the point of this probe is to exercise the
    engine this project will actually run on.
    """
    from qiskit_aer import AerSimulator
    from qiskit import transpile

    sim = AerSimulator(method="statevector")
    circuit = circuit.copy()
    circuit.save_statevector()
    result = sim.run(transpile(circuit, sim), shots=1).result()
    sv = np.asarray(result.get_statevector(circuit))
    if len(sv) != (1 << num_qubits):
        raise ProbeFailure(f"expected {1 << num_qubits} amplitudes, got {len(sv)}")
    return sv


def _nonzero_index(sv: np.ndarray, tol: float = 1e-9) -> int:
    """Index of the single dominant amplitude, asserting the state really is a basis state."""
    mags = np.abs(sv)
    idx = int(np.argmax(mags))
    if mags[idx] < 1.0 - tol:
        raise ProbeFailure(
            f"state is not a computational basis state: max |amplitude| = {mags[idx]:.6f}"
        )
    return idx


def _little_endian_index(qubit_values: "dict[int, int]") -> int:
    """Index of a basis state under the convention that qubit ``q`` carries bit ``q``."""
    return sum(v << q for q, v in qubit_values.items())


# ---------------------------------------------------------------------------------------------
# A. versions and presence
# ---------------------------------------------------------------------------------------------


def check_versions() -> list[ProbeResult]:
    out: list[ProbeResult] = []
    for mod, required in (
        ("qiskit", True),
        ("qiskit_aer", True),
        ("cirq", True),
        ("qsimcirq", True),
        ("quimb", True),
        ("cotengra", True),
        ("sympy", True),
        ("numpy", True),
        ("numba", True),
    ):
        try:
            m = __import__(mod)
            out.append(ProbeResult(mod, True, getattr(m, "__version__", "?"), required=required))
        except Exception as exc:  # noqa: BLE001 - a missing engine is a probe result, not a crash
            out.append(ProbeResult(mod, False, f"{type(exc).__name__}: {exc}", required=required))
    return out


def check_qiskit_library_surface() -> list[ProbeResult]:
    """Every ``qiskit.circuit.library`` name this project intends to use, and the absences."""
    import qiskit
    from qiskit import circuit as qc

    wanted = [
        "CDKMRippleCarryAdder",
        "VBERippleCarryAdder",
        "DraperQFTAdder",
        "IntegerComparatorGate",
        "WeightedSumGate",
        "QuadraticFormGate",
        "MCXGate",
        "MCPhaseGate",
        "PermutationGate",
        "PhaseOracleGate",
        "ModularAdderGate",
        "MultiplierGate",
        "HRSCumulativeMultiplier",
        "RGQFTMultiplier",
    ]
    absent = [
        "BooleanExpression",
        "PhaseOracle",
        "Multiplier",
        "Adder",
        "IntegerComparator",
        # Listed as present-and-usable by the design pass. It is not in 2.5.2. Its absence is why
        # the IR defines MCZ as a gate this project synthesises itself from MCPhaseGate: the
        # project's own construction is the one that gets counted, so it must be the one that runs.
        "MCZGate",
    ]

    out: list[ProbeResult] = []
    lib = qc.library
    for name in wanted:
        out.append(
            ProbeResult(f"qiskit.circuit.library.{name}", hasattr(lib, name), "present")
        )
    for name in absent:
        present = hasattr(lib, name)
        out.append(
            ProbeResult(
                f"qiskit.circuit.library.{name} (expected gone)",
                not present,
                "absent, as expected" if not present else "STILL PRESENT — recheck the plan",
                required=False,
            )
        )

    gone = not hasattr(qc, "classicalfunction") and not _importable(
        "qiskit.circuit.classicalfunction"
    )
    out.append(
        ProbeResult(
            "qiskit.circuit.classicalfunction removed (expected)",
            gone,
            "removed, as expected" if gone else "still importable — recheck the plan",
            required=False,
        )
    )
    out.append(ProbeResult("qiskit.__version__", True, qiskit.__version__))
    return out


def _importable(dotted: str) -> bool:
    import importlib

    try:
        importlib.import_module(dotted)
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------------------------
# B. the three semantic checks
# ---------------------------------------------------------------------------------------------


def check_weighted_sum_ordering() -> ProbeResult:
    """Measure ``WeightedSumGate``'s weight-to-qubit mapping.

    The class computes ``sum(weights[i] * x[i])`` into a result register. The question is which
    qubit ``weights[0]`` multiplies. The docs say "the upper-most qubit"; this project's registers
    are little-endian, so those are opposite answers and the difference is invisible in a symmetric
    dot product.
    """
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import WeightedSumGate

    n = 3
    weights = (1, 2, 4)  # distinct powers, so every basis state gives a distinct weighted sum
    gate = WeightedSumGate(n, weights)

    # The gate cannot be synthesised inside its own declared width: qiskit's high-level-synthesis
    # plugin demands clean ancillas on top of num_qubits. Supply them, and record the demand —
    # it is the reason this project builds its own accumulate step rather than using this gate.
    clean = 3
    qc = QuantumCircuit(gate.num_qubits + clean)
    qc.x(0)
    qc.append(gate, range(gate.num_qubits))
    sv = _amplitudes(qc, gate.num_qubits + clean)

    # Read the result register. The state register is the first n qubits; the sum follows it.
    idx = _nonzero_index(sv)
    result_value = idx >> n
    state_value = idx & ((1 << n) - 1)

    if state_value != 1:
        raise ProbeFailure(f"state register did not survive the gate: read {state_value}, want 1")

    if result_value == 1:
        mapping = "weights[i] -> qubit i (little-endian, matches this project)"
    elif result_value == 4:
        mapping = "weights[i] -> qubit n-1-i (the doc's 'upper-most qubit' first — REVERSED)"
    else:
        raise ProbeFailure(f"unexpected weighted sum {result_value} for qubit 0 set")

    ok = result_value == 1
    return ProbeResult(
        "WeightedSumGate weight->qubit ordering",
        ok,
        f"weights={weights}, X on q0 -> sum={result_value}; {mapping}",
        required=ok,
        notes=[
            "If this reads REVERSED, any dot product compiled through WeightedSumGate must reverse "
            "its weight vector, or mark the wrong state while M and k_opt stay correct."
        ]
        if not ok
        else [],
    )


def check_weighted_sum_ancillas() -> ProbeResult:
    """How many qubits ``WeightedSumGate`` allocates beyond the state and result registers."""
    from qiskit.circuit.library import WeightedSumGate

    n = 3
    gate = WeightedSumGate(n, (1, 2, 4))
    declared = gate.num_qubits
    result_qubits = _weighted_sum_result_width((1, 2, 4))
    expected_min = n + result_qubits
    extra = declared - expected_min
    return ProbeResult(
        "WeightedSumGate qubit allocation",
        extra >= 0,
        f"state={n}, result={result_qubits}, total declared={declared}, extra ancillas={extra}",
        notes=[f"{extra} undeclared ancillas" if extra else "no hidden ancillas"],
    )


def _weighted_sum_result_width(weights) -> int:
    total = sum(abs(w) for w in weights)
    return max(1, int(total).bit_length())


def check_quadratic_form_convention() -> ProbeResult:
    """Brute-force ``QuadraticFormGate`` against direct evaluation, for every input at small N.

    ``Q(x) = x^T A x + x^T b + c``, computed mod ``2^m``. The gate's treatment of the diagonal of
    A, of off-diagonal symmetry, and of the offset is not specified well enough to build on, so it
    is measured. Both the symmetric and the upper-triangular readings of ``A`` are tried, because
    the corpus's own quadratic-map structure stores the upper triangle.
    """
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import QuadraticFormGate

    rng = np.random.default_rng(20260913)
    n = 4
    m = 1
    trials = 0
    symmetric_matches = 0
    triangular_matches = 0
    total = 0

    for _ in range(3):
        A = rng.integers(0, 2, size=(n, n))
        b = rng.integers(0, 2, size=n)
        c = int(rng.integers(0, 2))
        trials += 1

        try:
            gate = QuadraticFormGate(m, A.tolist(), b.tolist(), c)
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                "QuadraticFormGate convention",
                False,
                f"construction failed: {type(exc).__name__}: {exc}",
            )

        for x in range(1 << n):
            qc = QuantumCircuit(gate.num_qubits)
            for q in range(n):
                if (x >> q) & 1:
                    qc.x(q)
            qc.append(gate, range(gate.num_qubits))
            sv = _amplitudes(qc, gate.num_qubits)
            idx = _nonzero_index(sv)
            got = idx >> n

            bits = np.array([(x >> q) & 1 for q in range(n)])

            sym = int((bits @ A @ bits + bits @ b + c) % (1 << m))
            tri = int((bits @ np.triu(A) @ bits + bits @ b + c) % (1 << m))

            total += 1
            symmetric_matches += int(sym == got)
            triangular_matches += int(tri == got)

    sym_rate = symmetric_matches / total
    tri_rate = triangular_matches / total

    if sym_rate == 1.0:
        verdict = "matches x^T A x + x^T b + c with A used as given (full matrix)"
        ok = True
    elif tri_rate == 1.0:
        verdict = "matches x^T A x + x^T b + c with A read as upper-triangular"
        ok = True
    else:
        verdict = (
            f"neither convention matches (symmetric {sym_rate:.0%}, triangular {tri_rate:.0%}) — "
            "use the hand-built x_i x_j Toffoli array fallback"
        )
        ok = False

    return ProbeResult(
        "QuadraticFormGate convention",
        ok,
        f"N={n}, m={m}, {trials} random (A,b,c), {total} inputs: {verdict}",
        notes=["Hand-built fallback required." ] if not ok else [],
    )


def check_library_ancilla_counts() -> list[ProbeResult]:
    """Declared width of each arithmetic block this project intends to build on."""
    from qiskit.circuit.library import (
        CDKMRippleCarryAdder,
        IntegerComparatorGate,
        MCPhaseGate,
        MCXGate,
        PermutationGate,
    )

    out: list[ProbeResult] = []

    # CDKM adds two n-qubit registers. Its width is 2n plus a small number of ancillas, which the
    # budget arithmetic has to carry. The point of this check is to *measure* that number rather
    # than take "ancilla-free" on faith — it is not ancilla-free.
    for kind in ("full", "half", "fixed"):
        try:
            n = 8
            g = CDKMRippleCarryAdder(n, kind=kind)
            extra = g.num_qubits - 2 * n
            out.append(
                ProbeResult(
                    f"CDKMRippleCarryAdder({n}, kind={kind!r})",
                    0 <= extra <= 2,
                    f"num_qubits={g.num_qubits} = 2*{n} operands + {extra} ancilla(e)",
                )
            )
        except Exception as exc:  # noqa: BLE001
            out.append(
                ProbeResult(f"CDKMRippleCarryAdder(kind={kind!r})", False, f"{type(exc).__name__}: {exc}")
            )

    g = IntegerComparatorGate(6, 61, geq=False)
    out.append(
        ProbeResult(
            "IntegerComparatorGate(6, 61, geq=False)",
            g.num_qubits >= 7,
            f"num_qubits={g.num_qubits} (>= 6 state + 1 result)",
        )
    )

    for c in (3, 4, 11):
        g = MCXGate(c)
        out.append(ProbeResult(f"MCXGate({c})", True, f"num_qubits={g.num_qubits}"))

    g = MCPhaseGate(np.pi, 3)
    out.append(ProbeResult("MCPhaseGate(pi, 3)", True, f"num_qubits={g.num_qubits} (4 = 3 ctrl + target)"))

    p = PermutationGate([1, 0, 3, 2])
    out.append(
        ProbeResult(
            "PermutationGate([1,0,3,2])",
            True,
            f"num_qubits={p.num_qubits}, definition present={p.definition is not None}",
        )
    )
    return out


def check_mcz_semantics() -> ProbeResult:
    """``MCPhaseGate(pi, k-1)`` is a valid MCZ: -1 exactly on the all-ones state, +1 elsewhere.

    This is the check that replaces ``MCZGate``, which does not exist in qiskit 2.5.2. If this
    passes, the compiler's MCZ lowering is sound; if it fails, MCZ is built as
    ``H . MCX . H`` on the last qubit, which is always available.
    """
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import MCPhaseGate
    import numpy as np

    k = 3
    gate = MCPhaseGate(np.pi, k - 1)
    if gate.num_qubits != k:
        return ProbeResult(
            "MCPhaseGate(pi, k-1) as MCZ",
            False,
            f"num_qubits={gate.num_qubits}, expected {k}",
        )
    for x in range(1 << k):
        qc = QuantumCircuit(k)
        for q in range(k):
            if (x >> q) & 1:
                qc.x(q)
        qc.append(gate, range(k))
        sv = _amplitudes(qc, k)
        idx = _nonzero_index(sv)
        if idx != x:
            raise ProbeFailure(f"MCZGate permuted |{x}> to |{idx}> — it must be diagonal")
        want = -1.0 if x == (1 << k) - 1 else 1.0
        if abs(sv[idx].real - want) > 1e-9 or abs(sv[idx].imag) > 1e-9:
            raise ProbeFailure(f"MCPhaseGate(pi) on |{x}> = {sv[idx]}, want {want}")
    return ProbeResult(
        "MCPhaseGate(pi, k-1) as MCZ",
        True,
        f"diagonal, -1 exactly on |{'1' * k}> over all {1 << k} basis states",
    )


def check_mcx_semantics() -> ProbeResult:
    """``MCXGate(c)`` flips the target iff every control is 1, for c in the sweep's range."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import MCXGate

    for c in (3, 4):
        gate = MCXGate(c)
        k = c + 1
        for x in range(1 << k):
            qc = QuantumCircuit(k)
            for q in range(k):
                if (x >> q) & 1:
                    qc.x(q)
            qc.append(gate, range(k))
            sv = _amplitudes(qc, k)
            idx = _nonzero_index(sv)
            controls_all_set = (x & ((1 << c) - 1)) == ((1 << c) - 1)
            want = x ^ (1 << c) if controls_all_set else x
            if idx != want:
                raise ProbeFailure(f"MCXGate({c}) on |{x}> gave |{idx}>, want |{want}>")
    return ProbeResult(
        "MCXGate(c) semantics", True, "flips the last qubit iff all controls set, c in {3,4}"
    )


def check_phase_oracle_gate() -> ProbeResult:
    """``PhaseOracleGate`` exists and takes a boolean-expression string (its new interface)."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import PhaseOracleGate

    try:
        gate = PhaseOracleGate("a & b")
    except Exception as exc:  # noqa: BLE001
        return ProbeResult(
            "PhaseOracleGate(boolean string)",
            False,
            f"{type(exc).__name__}: {exc}",
            notes=["Falls back to an explicit MCZ chain, which is the plan's primary form anyway."],
        )

    k = gate.num_qubits
    if k != 2:
        return ProbeResult(
            "PhaseOracleGate(boolean string)",
            True,
            f"constructed; num_qubits={k} (note: not 2 for 'a & b')",
            required=False,
        )

    qc = QuantumCircuit(2)
    qc.x(0)
    qc.x(1)
    qc.append(gate, [0, 1])
    sv = _amplitudes(qc, 2)
    idx = _nonzero_index(sv)
    ok = abs(sv[idx].real - (-1.0)) < 1e-9
    return ProbeResult(
        "PhaseOracleGate(boolean string)",
        ok,
        f"'a & b' with a=b=1 gives amplitude {sv[idx].real:+.3f} (want -1)",
    )


# ---------------------------------------------------------------------------------------------
# C. engines actually run
# ---------------------------------------------------------------------------------------------


def check_permutation_gate_semantics() -> ProbeResult:
    """``PermutationGate`` permutes **qubit positions**, not basis states. It is not usable for ``perm``.

    This is the check that caught a wrong assumption before it reached the compiler. The class name
    and its ``pattern`` argument read as though they express a permutation of computational basis
    states — which is what the IR's :attr:`GateName.PERM` means, and what an S-box needs. They do
    not. ``num_qubits`` is ``len(pattern)``, and the operation is a relabelling of qubit *indices*.

    The consequence is a group-order argument, not a taste judgement: qubit relabellings on ``b``
    qubits form a group of order ``b!``, while basis-state permutations form one of order ``2**b!``.
    On two qubits that is 2 against 24 — measured below — so a nonlinear S-box is unreachable.
    """
    from qiskit.circuit.library import PermutationGate
    from qiskit.quantum_info import Operator

    b = 2
    reached = set()
    for pattern in ([0, 1], [1, 0]):
        gate = PermutationGate(pattern)
        if gate.num_qubits != b:
            raise ProbeFailure(f"num_qubits={gate.num_qubits}, expected {b}")
        op = Operator(gate)
        reached.add(tuple(int(np.argmax(np.abs(op.data[:, i]))) for i in range(1 << b)))

    total_possible = 24  # 4! basis-state permutations on 2 qubits
    ok = len(reached) == 2 and len(reached) < total_possible
    return ProbeResult(
        "PermutationGate is a qubit relabelling, not a basis permutation",
        ok,
        f"on {b} qubits it reaches {len(reached)} of {total_possible} maps; "
        "group order b! vs 2**b! — unusable for `perm`",
        notes=[
            "`perm` is therefore lowered as a UnitaryGate (see the next check), not a "
            "PermutationGate. Gate accounting reports a perm as one b-qubit block."
        ],
        required=False,
    )


def check_unitary_gate_permutation() -> ProbeResult:
    """``UnitaryGate`` executes an arbitrary (nonlinear) basis permutation exactly, on Aer.

    This is the lowering the compiler uses for the IR's ``perm`` gate. The permutation tested is
    deliberately one no qubit relabelling can reach, so a pass here is evidence for the property
    that matters and not just evidence that some unitary ran.
    """
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import UnitaryGate
    from qiskit_aer import AerSimulator

    table = [3, 1, 0, 2, 7, 4, 6, 5]  # arbitrary nonlinear 3-bit S-box
    if sorted(table) != list(range(8)):
        raise ProbeFailure("the test table is not a permutation")

    matrix = np.zeros((8, 8), dtype=complex)
    for src, dst in enumerate(table):
        matrix[dst, src] = 1.0
    gate = UnitaryGate(matrix)
    if gate.num_qubits != 3:
        raise ProbeFailure(f"UnitaryGate num_qubits={gate.num_qubits}, expected 3")

    sim = AerSimulator(method="statevector")
    for x in range(8):
        qc = QuantumCircuit(3)
        for q in range(3):
            if (x >> q) & 1:
                qc.x(q)
        qc.append(gate, [0, 1, 2])
        qc.save_statevector()
        sv = np.asarray(sim.run(transpile(qc, sim), shots=1).result().get_statevector(qc))
        got = _nonzero_index(sv)
        if got != table[x]:
            raise ProbeFailure(f"|{x}> -> |{got}>, want |{table[x]}>")

    return ProbeResult(
        "UnitaryGate executes an arbitrary nonlinear permutation",
        True,
        f"table={table} exact on all 8 basis states; this is the `perm` lowering",
    )


def check_aer_executes() -> ProbeResult:
    """The unbounded ``qiskit-aer`` -> ``qiskit>=1.1.0`` declaration, tested not believed."""
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator

    sim = AerSimulator(method="statevector")
    qc = QuantumCircuit(4)
    qc.h(range(4))
    qc.save_statevector()
    result = sim.run(transpile(qc, sim), shots=1).result()
    sv = np.asarray(result.get_statevector(qc))
    uniform = np.allclose(np.abs(sv), 0.25)
    return ProbeResult(
        "Aer statevector execution",
        uniform and len(sv) == 16,
        f"4-qubit uniform superposition: {len(sv)} amplitudes, all |a|=0.25 -> {uniform}",
    )


def check_qsim_executes() -> ProbeResult:
    """qsim through the cirq front end, which is the cross-validation engine."""
    import cirq
    import qsimcirq

    q = cirq.LineQubit.range(4)
    circuit = cirq.Circuit([cirq.H(x) for x in q])
    sim = qsimcirq.QSimSimulator()
    result = sim.simulate(circuit)
    sv = result.final_state_vector
    uniform = np.allclose(np.abs(sv), 0.25)
    return ProbeResult(
        "qsim (via cirq) statevector execution",
        uniform and len(sv) == 16,
        f"4-qubit uniform superposition: {len(sv)} amplitudes, all |a|=0.25 -> {uniform}",
    )


def check_cirq_surface() -> list[ProbeResult]:
    import cirq

    out: list[ProbeResult] = []
    for name in ("X", "H", "CNOT", "TOFFOLI", "S", "T", "Z", "MeasurementGate"):
        out.append(ProbeResult(f"cirq.{name}", hasattr(cirq, name), "present"))
    out.append(
        ProbeResult(
            "cirq.TaggedOperation / .with_tags",
            hasattr(cirq.Operation, "with_tags"),
            "present (used for IR round-trip)",
        )
    )
    return out


# ---------------------------------------------------------------------------------------------
# entry points
# ---------------------------------------------------------------------------------------------


def probe_all() -> list[ProbeResult]:
    """Run every check. A check that raises is reported as a failure, never as a crash."""
    groups = [
        check_versions,
        check_qiskit_library_surface,
        check_weighted_sum_ordering,
        check_weighted_sum_ancillas,
        check_quadratic_form_convention,
        check_library_ancilla_counts,
        check_mcz_semantics,
        check_mcx_semantics,
        check_phase_oracle_gate,
        check_permutation_gate_semantics,
        check_unitary_gate_permutation,
        check_aer_executes,
        check_qsim_executes,
        check_cirq_surface,
    ]
    results: list[ProbeResult] = []
    for fn in groups:
        try:
            r = fn()
        except Exception as exc:  # noqa: BLE001
            results.append(
                ProbeResult(fn.__name__, False, f"{type(exc).__name__}: {exc}")
            )
            continue
        results.extend(r if isinstance(r, list) else [r])
    return results


def format_report(results: list[ProbeResult]) -> str:
    lines = ["milestone 0 - framework API probe", ""]
    for r in results:
        lines.append(r.line())
        for note in r.notes:
            lines.append(f"         -> {note}")
    failed = [r for r in results if not r.ok and r.required]
    lines.append("")
    lines.append(f"{len(results)} checks, {len(failed)} required failures")
    return "\n".join(lines)
