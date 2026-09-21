"""Exact classical simulation of a reversible circuit, and the assertions built on it.

**How a circuit is checked without materialising its matrix.** The action of a permutation-plus-phase
circuit on a computational basis state is a bit-string permutation plus a phase, and that is all a
phase oracle is. So the test tracks the permutation: one machine word per basis state, one bitwise
expression per gate. Memory is ``8 * 2**n`` bytes — **linear, not quadratic** — and it is exact:
there is no tolerance anywhere in this module, because the perturbation of a basis state is an
integer and the phase is accumulated as an exact power of the eighth root of unity.

**Why the ancillas do not have to be enumerated.** A predicate over ``n_search`` qubits with ``a``
ancillas lives in a ``2**(n_search + a)``-dimensional space, which for the QLWR arithmetic lowering
is ``2**50``. But the only inputs the circuit ever sees are *search register set, ancillas clean* —
``2**n_search`` of them. Enumerating that reachable subspace is a complete test of the predicate,
and it is the reason this module's cost is set by the search width rather than by the total width.

The phase is an integer exponent mod 8 throughout. Every gate in the IR contributes a phase that is
exactly ``exp(i*pi/4)**k`` for some integer ``k``, so the simulation is exact integer arithmetic and
the assertions comparing it to a closed form need no epsilon.
"""

from __future__ import annotations

import numpy as np

from ..circuits.ir import Gate, GateList, GateName, phase_exponent

__all__ = [
    "SimulationError",
    "simulate_states",
    "simulate_predicate_flag",
    "assert_predicate_matches_spec",
    "assert_ancillas_return_clean",
    "assert_sandwich_is_identity",
    "assert_unitary",
    "assert_operators_agree_up_to_phase",
    "assert_oracle_is_diagonal",
    "assert_backend_agreement",
    "phase_to_complex",
]


class SimulationError(RuntimeError):
    """The gate list cannot be classically simulated as a basis-state trajectory."""


def phase_to_complex(exponents: np.ndarray) -> np.ndarray:
    """``exp(i*pi/4)**k`` for an integer exponent array — exact, by table lookup."""
    table = np.exp(1j * np.pi / 4.0 * np.arange(8))
    return table[np.asarray(exponents, dtype=np.int64) % 8]


def _require_simulable(gl: GateList) -> None:
    if not gl.is_classically_simulable():
        offenders = sorted({g.name.value for g in gl.gates if not _is_diagonal(g)})
        raise SimulationError(
            f"gate list contains {offenders}, which create superposition; a single-trajectory "
            "simulation is exact only for permutations and diagonal phases. Simulate this circuit "
            "on a statevector engine instead."
        )


def _is_diagonal(gate: Gate) -> bool:
    from ..circuits.ir import _PHASE_EXPONENT

    return _PHASE_EXPONENT[gate.name] >= 0


def simulate_states(gl: GateList, initial: np.ndarray, chunk: int = 1 << 20) -> tuple[np.ndarray, np.ndarray]:
    """Apply ``gl`` to every basis state in ``initial``.

    Args:
        gl: the gate list. Must be permutation-plus-diagonal; anything else raises rather than
            silently producing a wrong answer.
        initial: an array of basis-state integers. The caller decides how many qubits matter; bits
            above the circuit's width are simply carried along and must start at zero.
        chunk: how many states to process at once. Chunking keeps peak memory bounded on a machine
            that is already under pressure, and it is why this works at ``n = 24`` without a
            multiple of the state array in scratch.

    Returns:
        ``(final_states, phase_exponents)`` — the permuted states and an integer exponent mod 8 for
        each, so the exact amplitude is ``exp(i*pi/4)**exponent``.
    """
    _require_simulable(gl)
    if gl.num_qubits > 63:
        raise SimulationError(
            f"gate list is {gl.num_qubits} qubits wide; the bitmask simulator packs one state into "
            "a uint64 and cannot exceed 63"
        )
    initial = np.asarray(initial, dtype=np.uint64)
    out = np.empty_like(initial)
    phases = np.zeros(initial.shape, dtype=np.int64)

    for start in range(0, initial.shape[0], chunk):
        s = initial[start : start + chunk].copy()
        ph = phases[start : start + chunk]
        for gate in gl.gates:
            _apply(s, ph, gate)
        out[start : start + chunk] = s

    return out, phases


def _apply(s: np.ndarray, ph: np.ndarray, gate: Gate) -> None:
    """Apply one gate in place to the state array and the phase-exponent array."""
    q = gate.qubits
    name = gate.name

    if name is GateName.PERM:
        table = np.asarray(gate.params[0], dtype=np.uint64)
        bits = np.zeros(s.shape, dtype=np.uint64)
        for k, qubit in enumerate(q):
            bits |= ((s >> np.uint64(qubit)) & np.uint64(1)) << np.uint64(k)
        collected = np.zeros(s.shape, dtype=np.uint64)
        for k, qubit in enumerate(q):
            collected |= ((table[bits] >> np.uint64(k)) & np.uint64(1)) << np.uint64(qubit)
        # Clear the old bits and write the permuted ones.
        mask = np.uint64(0)
        for qubit in q:
            mask |= np.uint64(1) << np.uint64(qubit)
        s[...] = (s & ~mask) | collected
        return

    if name is GateName.X:
        s ^= np.uint64(1) << np.uint64(q[0])
        return
    if name is GateName.CX:
        s ^= (((s >> np.uint64(q[0])) & np.uint64(1)) << np.uint64(q[1]))
        return
    if name is GateName.CCX:
        cond = ((s >> np.uint64(q[0])) & np.uint64(1)) & ((s >> np.uint64(q[1])) & np.uint64(1))
        s ^= cond << np.uint64(q[2])
        return
    if name is GateName.MCX:
        cond = np.uint64(1) * np.ones(s.shape, dtype=np.uint64)
        for c in q[:-1]:
            cond &= (s >> np.uint64(c)) & np.uint64(1)
        s ^= cond << np.uint64(q[-1])
        return

    # Diagonal single- or multi-qubit phases.
    exp = phase_exponent(gate, tuple(True for _ in q))
    if name is GateName.MCZ:
        allset = np.uint64(1) * np.ones(s.shape, dtype=np.uint64)
        for c in q:
            allset &= (s >> np.uint64(c)) & np.uint64(1)
        ph += exp * allset.astype(np.int64)
        return
    bit = (s >> np.uint64(q[0])) & np.uint64(1)
    ph += exp * bit.astype(np.int64)


def simulate_predicate_flag(gl: GateList, n_search: int) -> np.ndarray:
    """The predicate's flag bit for every search value, with ancillas starting clean.

    This is the exhaustive equivalence test's engine. It enumerates the *reachable* subspace —
    ``2**n_search`` inputs — rather than the ``2**total_width`` space, which is what makes the test
    possible at all for a circuit with fifty qubits.
    """
    if not 0 <= n_search < gl.num_qubits:
        raise SimulationError(f"search width {n_search} outside a {gl.num_qubits}-qubit circuit")
    initial = np.arange(1 << n_search, dtype=np.uint64)
    final, _ = simulate_states(gl, initial)
    return ((final >> np.uint64(gl.num_qubits - 1)) & np.uint64(1)).astype(bool)


def assert_sandwich_is_identity(gl: GateList, n_search: int, label: str = "") -> None:
    """``predicate ; predicate.inverse()`` must be the identity on the reachable subspace.

    This is the property the oracle actually needs, and it is strictly stronger than the predicate
    being clean on its own: it says the sandwich restores the *whole* register, ancillas included,
    for every input. A predicate that leaked state its inverse could not undo would fail here even
    if it happened to leave its own ancillas at zero.
    """
    sandwich = gl.copy()
    sandwich.extend(gl.inverse())
    initial = np.arange(1 << n_search, dtype=np.uint64)
    final, phases = simulate_states(sandwich, initial)
    if np.any(final != initial):
        bad = int(np.nonzero(final != initial)[0][0])
        raise AssertionError(
            f"{label}: predicate followed by its inverse did not restore state {bad} "
            f"(got {int(final[bad])})"
        )
    if np.any(phases % 8 != 0):
        bad = int(np.nonzero(phases % 8 != 0)[0][0])
        raise AssertionError(
            f"{label}: sandwich carries a phase on state {bad} (exponent {int(phases[bad])}); "
            "the forward and inverse passes must cancel exactly"
        )


def assert_ancillas_return_clean(gl: GateList, n_search: int) -> None:
    """A *standalone* predicate that claims to be clean: no ancilla left set, register undisturbed.

    Used by the truth-table lowering and by any block that is meant to be composable on its own.
    Predicates that legitimately leave intermediate state behind are checked with
    :func:`assert_sandwich_is_identity` instead, which is the property the oracle uses.
    """
    initial = np.arange(1 << n_search, dtype=np.uint64)
    final, _ = simulate_states(gl, initial)
    ancilla_mask = np.uint64(((1 << gl.num_qubits) - 1) ^ ((1 << n_search) - 1))
    dirty = final & ancilla_mask
    if np.any(dirty):
        first = int(np.nonzero(dirty)[0][0])
        raise AssertionError(
            f"predicate left ancillas dirty for search value {first}: "
            f"residual bits {int(dirty[first]):#x}"
        )
    if np.any(final != initial):
        raise AssertionError("predicate disturbed the search register it was given")


def assert_predicate_matches_spec(spec, lowering) -> None:
    """The exhaustive equivalence test: both lowerings against the spec's marked set.

    Acceptance condition 6. Run for every spec at every enumerable width. A failure here means the
    gate counts describe a circuit that computes something other than the predicate it is named
    after, and every number derived from it is meaningless.
    """
    gl = spec.build_predicate(lowering)
    n = spec.search_width()
    if gl.num_qubits - n > 60:
        raise SimulationError(f"{spec.name}/{lowering} is too wide for the bitmask simulator")

    got = simulate_predicate_flag(gl, n)
    want = spec.truth_table()
    mismatch = np.nonzero(got != want)[0]
    if mismatch.size:
        raise AssertionError(
            f"{spec.name}/{lowering.value}: predicate disagrees with the marked set on "
            f"{mismatch.size} of {want.size} basis states, first at {int(mismatch[0])}"
        )
    # The flag is right. Now the property the oracle sandwich depends on: the predicate's own inverse
    # must undo it completely, ancillas included.
    assert_sandwich_is_identity(gl, n, label=f"{spec.name}/{lowering.value}")


def assert_unitary(matrix: np.ndarray, tol: float = 1e-9) -> None:
    """Assert ``M M^dagger == I`` to tolerance. Only usable at widths where a matrix fits."""
    m = np.asarray(matrix, dtype=complex)
    if m.ndim != 2 or m.shape[0] != m.shape[1]:
        raise AssertionError(f"matrix is {m.shape}, not square")
    product = m @ m.conj().T
    if not np.allclose(product, np.eye(m.shape[0]), atol=tol):
        worst = float(np.max(np.abs(product - np.eye(m.shape[0]))))
        raise AssertionError(f"matrix is not unitary; worst deviation {worst:.3e}")


def assert_oracle_is_diagonal(gl: GateList, n_search: int, marked: frozenset[int]) -> None:
    """The oracle acts as ``diag((-1)**f)``: ``-1`` exactly on marked states, ``+1`` elsewhere.

    Verified by simulation, never asserted from theory — the plan's §3.5 requirement.
    """
    initial = np.arange(1 << n_search, dtype=np.uint64)
    final, phases = simulate_states(gl, initial)
    if np.any(final != initial):
        raise AssertionError("the oracle is not diagonal: it moved a basis state")
    amplitude = phase_to_complex(phases)
    want = np.where(np.isin(np.arange(1 << n_search), sorted(marked)), -1.0, 1.0)
    bad = np.nonzero(~np.isclose(amplitude.real, want) | (np.abs(amplitude.imag) > 1e-12))[0]
    if bad.size:
        raise AssertionError(
            f"oracle phase wrong on {bad.size} states, first at {int(bad[0])}: "
            f"got {amplitude[bad[0]]}, want {want[bad[0]]}"
        )


def assert_operators_agree_up_to_phase(a: np.ndarray, b: np.ndarray, tol: float = 1e-9, label: str = "") -> None:
    """Two unitary matrices must agree up to a global phase.

    The diffuser is the reason this exists. ``H^n X^n (MCZ) X^n H^n`` evaluates to ``I - 2|s><s|``,
    while the textbook form of inversion about the mean is ``2|s><s| - I``. They differ by exactly
    ``-1`` on every entry — a global phase, physically meaningless, and enough to make a strict
    matrix comparison report a failure on a circuit that is provably right. The Grover success curve
    computed through this diffuser matches the closed form to ``1e-15``, which is what says the
    circuit is correct and the comparison was wrong.
    """
    a = np.asarray(a, dtype=complex)
    b = np.asarray(b, dtype=complex)
    if a.shape != b.shape:
        raise AssertionError(f"{label}: shapes differ, {a.shape} vs {b.shape}")
    # The Hilbert-Schmidt inner product |<A, B>| / (||A||_F ||B||_F) is 1.0 exactly when B = e^{i phi} A,
    # and strictly less otherwise — so it measures "equal up to a global phase" directly, without the
    # caller having to find the phase first.
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < tol or nb < tol:
        raise AssertionError(f"{label}: one operator is zero")
    overlap = abs(np.trace(a.conj().T @ b)) / (na * nb)
    if abs(overlap - 1.0) > tol:
        raise AssertionError(
            f"{label}: operators differ by more than a global phase (normalised overlap "
            f"{overlap:.12f})"
        )


def assert_backend_agreement(a: np.ndarray, b: np.ndarray, tol: float = 1e-9, label: str = "") -> None:
    """Two engines must agree on the final statevector, up to a global phase.

    Up to a global phase *on purpose*: Aer and qsim are free to differ by a unit-modulus scalar, and
    the physical content is the same. Comparing raw amplitudes would fail for a reason that is not a
    bug, which is worse than not comparing at all.
    """
    a = np.asarray(a, dtype=complex)
    b = np.asarray(b, dtype=complex)
    if a.shape != b.shape:
        raise AssertionError(f"{label}: shapes differ, {a.shape} vs {b.shape}")
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < tol or nb < tol:
        raise AssertionError(f"{label}: one statevector is zero")
    overlap = abs(np.vdot(a / na, b / nb))
    if 1.0 - overlap > tol:
        raise AssertionError(
            f"{label}: engines disagree; state overlap {overlap:.12f} (fidelity shortfall "
            f"{1.0 - overlap:.3e})"
        )
