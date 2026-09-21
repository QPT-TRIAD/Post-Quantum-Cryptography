"""The gate-list IR: what every circuit in this project *is*, before any framework sees it.

Why an IR rather than a framework circuit
----------------------------------------
Three things this project has to do cannot be done from inside a framework circuit object.

1. **Count gates honestly.** Qiskit's and Cirq's own depth definitions disagree, and a framework
   gate may expand into an undocumented number of physical operations (and undocumented ancillas).
   A gate count read off a framework circuit is a count of *that framework's* decomposition, not of
   the circuit. Here the gate list is the circuit, and every metric is computed from it.

2. **Invert exactly.** An oracle needs its compute block uncomputed. ``QuantumCircuit.inverse()``
   may resynthesise rather than reverse, so the inverse that runs is not the inverse that was
   counted. Every gate in this IR is either self-inverse or has an exact closed-form inverse, so
   :meth:`GateList.inverse` is total, exact, and provably the reverse of the gate list.

3. **Simulate classically at widths a statevector cannot reach.** The action of a reversible
   circuit on a computational basis state is a bit-string permutation plus a phase. Tracking those
   *is* exact simulation, and it costs one machine word per basis state rather than a matrix. The
   phase is tracked as an exact integer power of the eighth root of unity, never a float. See
   :func:`phase_exponent`.

The gate set is closed, and deliberately contains no rotations. That keeps the T-count and the
Toffoli-count well defined, and it is what makes the classical simulator of :mod:`grover_emulator.utils.validation`
a pure integer/bitmask computation with no numerical tolerance anywhere.

Qubit and bit conventions
-------------------------
Qubits are integers. A gate's ``qubits`` tuple is ordered, and the order is meaningful per gate
(see each gate's notes below). Where a gate acts on a *register* of ``b`` qubits — only
:attr:`GateName.PERM` does — the basis index is read little-endian: ``qubits[k]`` carries bit ``k``,
so ``qubits[0]`` is the least significant bit. This matches how every framework in the project
indexes a register, and it is asserted by test rather than assumed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "GateName",
    "Gate",
    "GateList",
    "phase_exponent",
    "SELF_INVERSE",
    "INVERSE_PAIR",
]


class GateName(str, Enum):
    """The closed gate set. No gate in this set is a rotation."""

    # --- single-qubit permutations -------------------------------------------------
    X = "x"
    """Pauli X. ``qubits = (target,)``. Self-inverse."""

    H = "h"
    """Hadamard. ``qubits = (target,)``. Self-inverse."""

    # --- controlled permutations ---------------------------------------------------
    CX = "cx"
    """Controlled X. ``qubits = (control, target)``. Self-inverse."""

    CCX = "ccx"
    """Toffoli. ``qubits = (control0, control1, target)``. Self-inverse."""

    MCX = "mcx"
    """Multi-controlled X. ``qubits = (control0, ..., control_{k-1}, target)`` — the target is
    **last**. Flips the target iff every control is 1. Self-inverse. ``k >= 3``; use CCX for two
    controls so that a two-control gate is never counted as a multi-controlled one."""

    MCZ = "mcz"
    """Multi-controlled Z, phase form. ``qubits = (q0, ..., qk)`` — all qubits are symmetric, there
    is no distinguished target. Applies -1 iff every listed qubit is 1. Self-inverse. With a single
    qubit this is the Pauli Z, which is what the oracle sandwich applies to its flag."""

    # --- single-qubit phases -------------------------------------------------------
    S = "s"
    """Phase gate. ``qubits = (target,)``. Inverse is :attr:`SDG`."""

    SDG = "sdg"
    """Inverse phase gate. ``qubits = (target,)``. Inverse is :attr:`S`."""

    T = "t"
    """T gate, the eighth root of unity. ``qubits = (target,)``. Inverse is :attr:`TDG`."""

    TDG = "tdg"
    """Inverse T gate. ``qubits = (target,)``. Inverse is :attr:`T`."""

    # --- arbitrary b-bit permutations ----------------------------------------------
    PERM = "perm"
    """A permutation of the ``b`` computational basis states of ``b`` target qubits.

    ``qubits = (q0, ..., q_{b-1})``, little-endian as described in the module docstring, and
    ``params = (table,)`` where ``table`` is a tuple of ``2**b`` integers and ``table[i]`` is the
    basis index that ``i`` is mapped to. ``b <= 8``.

    Not self-inverse in general; its inverse is the inverse permutation, computed exactly by
    :meth:`Gate.inverse`. This is the gate an S-box is built from, and it is the reason the gate
    set cannot be only X/CX/CCX: an S-box is cheaper as a table than as a Toffoli network, and the
    accounting must be able to say which was used."""

    # --- explicitly out of the unitary IR ------------------------------------------
    # There is deliberately no MEASURE gate. Every circuit in this IR is unitary; measurement is a
    # backend concern, appended after compilation. Keeping it out is what makes GateList.inverse()
    # total — a measured circuit has no inverse, and admitting the gate would mean every caller
    # having to prove it never appears in a block that gets uncomputed. The compilers in
    # :mod:`grover_emulator.circuits.compilers` add measurement at the point of execution and
    # record that separately, so the gate list that was counted is still the gate list that ran.


SELF_INVERSE: frozenset[GateName] = frozenset(
    {GateName.X, GateName.H, GateName.CX, GateName.CCX, GateName.MCX, GateName.MCZ}
)
"""Gates equal to their own inverse. Each is a permutation of order two, or a strictly diagonal
operator with entries in {+1, -1}."""

INVERSE_PAIR: dict[GateName, GateName] = {
    GateName.S: GateName.SDG,
    GateName.SDG: GateName.S,
    GateName.T: GateName.TDG,
    GateName.TDG: GateName.T,
}
"""Gates whose inverse is a different gate of the set."""


# Powers of the eighth root of unity w8 = exp(i*pi/4), indexed by gate. Every gate in the set
# contributes a phase that is *exactly* a power of w8, so the classical simulator accumulates an
# integer mod 8 and never touches a float. The value is added to the running exponent for each
# qubit that is 1 at the point the gate is applied.
#
#   X, CX, CCX, MCX  : permutation only, no phase on any basis state      -> 0
#   PERM             : an arbitrary basis-state permutation, same reason  -> 0
#   H                : creates superposition; a single trajectory cannot follow it, so it is marked
#                      -1 to make the classical simulator refuse it (see below)
#   MCZ              : -1 iff every listed qubit is 1, i.e. w8^4          -> 4
#   S                : i on |1>, i.e. w8^2                                 -> 2
#   SDG              : -i on |1>, i.e. w8^6                                -> 6
#   T                : w8 on |1>                                           -> 1
#   TDG              : w8^7 on |1>                                         -> 7
_PHASE_EXPONENT: dict[GateName, int] = {
    GateName.X: 0,
    GateName.CX: 0,
    GateName.CCX: 0,
    GateName.MCX: 0,
    GateName.MCZ: 4,
    GateName.S: 2,
    GateName.SDG: 6,
    GateName.T: 1,
    GateName.TDG: 7,
    GateName.H: -1,
    GateName.PERM: 0,
}
"""Per-gate contribution to the exact phase exponent, or -1 for a gate that creates superposition.

The classical bitmask simulator tracks *one* basis state's trajectory, which is exact for a circuit
of basis permutations and diagonal phases. ``PERM`` is such a permutation — it sends each basis
state to exactly one basis state, like ``X`` and ``CX`` — so it carries exponent 0. ``H`` is the
one gate here that creates superposition: tracking a single trajectory through it would be silently
wrong. So it is marked -1 and the simulator refuses any gate list containing it. That refusal is
the point: the phase-oracle compute block is permutations-and-phases, and the simulator's
precondition is machine-checked rather than documented.
"""


@dataclass(frozen=True, slots=True)
class Gate:
    """One gate in the IR.

    ``qubits`` is ordered and its meaning is gate-specific — see :class:`GateName`. ``params``
    carries the gate's classical data, if any; only :attr:`GateName.PERM` uses it.
    """

    name: GateName
    qubits: tuple[int, ...]
    params: tuple = ()

    def __post_init__(self) -> None:
        if not self.qubits:
            raise ValueError(f"{self.name.value}: a gate must act on at least one qubit")
        if len(set(self.qubits)) != len(self.qubits):
            raise ValueError(f"{self.name.value}: repeated qubit in {self.qubits}")
        if min(self.qubits) < 0:
            raise ValueError(f"{self.name.value}: negative qubit index in {self.qubits}")
        self._check_arity()
        # Canonicalise the permutation table to a tuple. Without this, a gate built from a list and
        # the same gate recovered by a compiler (which yields a tuple) compare unequal, and the
        # round-trip assertion fails for a reason that has nothing to do with the circuit.
        if self.name is GateName.PERM and not isinstance(self.params[0], tuple):
            object.__setattr__(self, "params", (tuple(self.params[0]),))

    def _check_arity(self) -> None:
        n = len(self.qubits)
        if self.name in (GateName.X, GateName.H, GateName.S, GateName.SDG, GateName.T, GateName.TDG):
            if n != 1:
                raise ValueError(f"{self.name.value}: takes 1 qubit, got {n}")
            if self.params:
                raise ValueError(f"{self.name.value}: takes no params")
        elif self.name is GateName.CX:
            if n != 2:
                raise ValueError(f"cx: takes 2 qubits, got {n}")
        elif self.name is GateName.CCX:
            if n != 3:
                raise ValueError(f"ccx: takes 3 qubits, got {n}")
        elif self.name is GateName.MCX:
            if n < 4:
                raise ValueError(
                    f"mcx: takes at least 4 qubits (3 controls + target), got {n}; "
                    "use ccx for two controls"
                )
        elif self.name is GateName.MCZ:
            # One qubit is allowed and means the Pauli Z: the phase -1 exactly when that qubit is 1.
            # It is the gate the oracle sandwich puts on a single flag, so refusing it would mean
            # every caller reaching for a different name for the same operator.
            if n < 1:
                raise ValueError(f"mcz: takes at least 1 qubit, got {n}")
        elif self.name is GateName.PERM:
            if n < 1 or n > 8:
                raise ValueError(f"perm: takes 1..8 qubits, got {n}")
            if len(self.params) != 1:
                raise ValueError("perm: params must be exactly (table,)")
            table = self.params[0]
            if len(table) != (1 << n):
                raise ValueError(
                    f"perm: on {n} qubits the table must have {1 << n} entries, got {len(table)}"
                )
            if sorted(table) != list(range(1 << n)):
                raise ValueError("perm: the table is not a permutation of 0..2**b - 1")

    @property
    def width(self) -> int:
        """Number of qubits this gate acts on."""
        return len(self.qubits)

    def inverse(self) -> "Gate":
        """The exact inverse of this gate."""
        if self.name in SELF_INVERSE:
            return self
        if self.name in INVERSE_PAIR:
            return Gate(INVERSE_PAIR[self.name], self.qubits, self.params)
        if self.name is GateName.PERM:
            table = self.params[0]
            inv = [0] * len(table)
            for i, image in enumerate(table):
                inv[image] = i
            return Gate(GateName.PERM, self.qubits, (tuple(inv),))
        raise AssertionError(f"no inverse defined for {self.name!r}")  # pragma: no cover


def phase_exponent(gate: Gate, ones: "object") -> int:
    """Phase-exponent contribution of ``gate`` for a basis state, given which of its qubits are 1.

    ``ones`` is a sequence of booleans, one per entry of ``gate.qubits``, saying whether that qubit
    is 1 in the basis state being tracked. The return value is added to a running exponent mod 8.

    Raises:
        ValueError: if the gate creates superposition. That is a *refusal*, not a fallback: a
            caller that reaches this with ``H`` is trying to track a single trajectory through a
            circuit that has more than one, and the honest answer is to stop. ``PERM`` is not
            refused: it moves a basis state to exactly one basis state and contributes no phase.

    This function exists as the single definition of the gate set's phase behaviour, so that the
    classical simulator, any future symbolic checker, and the test suite all read it from one
    place rather than each encoding it.
    """
    exp = _PHASE_EXPONENT[gate.name]
    if exp < 0:
        raise ValueError(
            f"{gate.name.value} creates superposition; a single-trajectory classical simulation "
            "is not exact through it"
        )
    if gate.name is GateName.MCZ:
        return exp if all(ones) else 0
    if len(gate.qubits) == 1:
        return exp if ones[0] else 0
    # Controlled phase gates on >1 qubit are not in the set; every other gate here contributes
    # nothing (X, CX, CCX, MCX and PERM are pure permutations).
    return 0


@dataclass(slots=True)
class GateList:
    """An ordered list of :class:`Gate`, plus the declared total width.

    The list order is the causal order: gate *i* may depend on any gate before it. It is not
    required to be a schedule — :meth:`depth` derives a schedule from the dependencies, which is
    why two builds of the same circuit that emit gates in a different order can still be compared
    by depth.
    """

    num_qubits: int
    gates: list[Gate] = field(default_factory=list)
    label: str = ""

    # -- construction ---------------------------------------------------------------------

    def append(self, name: GateName, *qubits: int, params: tuple = ()) -> "GateList":
        """Append a gate and return self, so builds read as a script."""
        g = Gate(name, tuple(qubits), params)
        if max(g.qubits) >= self.num_qubits:
            raise ValueError(
                f"{name.value} on qubit {max(g.qubits)} exceeds declared width {self.num_qubits}"
            )
        self.gates.append(g)
        return self

    def extend(self, other: "GateList") -> "GateList":
        """Concatenate another gate list, provided it fits in this one's width."""
        if other.num_qubits > self.num_qubits:
            raise ValueError(
                f"cannot extend a {self.num_qubits}-qubit list with a {other.num_qubits}-qubit one"
            )
        self.gates.extend(other.gates)
        return self

    def copy(self) -> "GateList":
        return GateList(self.num_qubits, list(self.gates), self.label)

    # -- structure ------------------------------------------------------------------------

    def inverse(self) -> "GateList":
        """The exact inverse circuit: the gates reversed and each replaced by its inverse.

        Total, because every gate in the set has an exact inverse. This is what a compute/uncompute
        sandwich is built from, and it is deliberately *not* a call into a framework's
        ``.inverse()``, which may resynthesise and silently diverge from the gate list that was
        counted.
        """
        return GateList(
            self.num_qubits,
            [g.inverse() for g in reversed(self.gates)],
            f"{self.label}^-1" if self.label else "",
        )

    def active_qubits(self) -> set[int]:
        """Every qubit index touched by at least one gate."""
        out: set[int] = set()
        for g in self.gates:
            out.update(g.qubits)
        return out

    def ancilla_peak(self) -> int:
        """Width minus the number of qubits any gate touches — i.e. qubits carried but unused.

        This is the *declared* ancilla count. It is a lower bound on what a framework will actually
        allocate: a framework gate may bring its own undocumented ancillas. The compilers assert
        the framework's allocation against this number so that a discrepancy is a build failure
        rather than a run that swaps.
        """
        return self.num_qubits - len(self.active_qubits())

    # -- metrics --------------------------------------------------------------------------

    def counts(self) -> dict[str, int]:
        """Gate counts by name, plus ``total``."""
        out: dict[str, int] = {}
        for g in self.gates:
            out[g.name.value] = out.get(g.name.value, 0) + 1
        out["total"] = len(self.gates)
        return out

    def toffoli_count(self) -> int:
        """Number of three-or-more-input controlled gates, **as written in the IR**.

        ``ccx`` counts one; ``mcx`` counts one however many controls it carries. This is the
        logical count, with no decomposition assumed — a decomposition-specific count belongs in
        :meth:`toffoli_equivalent`, where the assumption can be named.
        """
        return sum(1 for g in self.gates if g.name in (GateName.CCX, GateName.MCX))

    def toffoli_equivalent(self, ancilla_free: bool = False) -> int:
        """Toffoli-equivalents, under a named decomposition assumption.

        Args:
            ancilla_free: if False (the default), an ``mcx`` with ``c`` controls is taken as
                ``c - 1`` Toffolis, the standard decomposition that borrows one clean ancilla.
                If True, it is taken as ``4c**2 - 8c + 4``, the standard ancilla-free bound.

        The assumption is a parameter rather than a constant because the number moves by an order
        of magnitude between the two, and a report that quotes one without saying which is not
        reporting a measurement.
        """
        total = 0
        for g in self.gates:
            if g.name is GateName.CCX:
                total += 1
            elif g.name is GateName.MCX:
                c = len(g.qubits) - 1
                total += (4 * c * c - 8 * c + 4) if ancilla_free else (c - 1)
        return total

    def t_count(self, *, toffoli_equivalent: bool = False, ancilla_free: bool = False) -> int:
        """T-count, under the standard 7-T ancilla-free Toffoli decomposition.

        ``t`` gates count one and ``tdg`` count one, since a T-count is a count of both. Controlled
        gates are expanded per :meth:`toffoli_equivalent`. The 7 is an assumption, not a
        measurement, and it is stated here so a reader can substitute their own.
        """
        explicit = sum(1 for g in self.gates if g.name in (GateName.T, GateName.TDG))
        if toffoli_equivalent:
            return explicit + 7 * self.toffoli_equivalent(ancilla_free=ancilla_free)
        return explicit

    def depth(self) -> int:
        """Critical-path depth by list scheduling over the gate list.

        Each gate occupies its qubits for one time step, and may start only once every qubit it
        acts on is free. This is the ASAP schedule of the IR. It is the project's one definition of
        depth; a framework's own ``depth()`` is recorded separately and never compared to this one,
        because the definitions differ.
        """
        free: dict[int, int] = {}
        end = 0
        for g in self.gates:
            start = max((free.get(q, 0) for q in g.qubits), default=0)
            stop = start + 1
            for q in g.qubits:
                free[q] = stop
            end = max(end, stop)
        return end

    def is_classically_simulable(self) -> bool:
        """Whether every gate is a permutation or a diagonal phase.

        True means a single trajectory through this gate list is an exact simulation of one basis
        state, which is the precondition of :mod:`grover_emulator.utils.validation`. False means
        the list contains ``H`` and creates superposition. ``PERM`` does not: it is a basis-state
        permutation like ``X`` and ``CX``, and a list containing it is still simulable.
        """
        return all(_PHASE_EXPONENT[g.name] >= 0 for g in self.gates)

    # -- serialisation --------------------------------------------------------------------

    def to_dict(self) -> dict:
        """A JSON-safe form, for recording a circuit in a run's metrics."""
        return {
            "label": self.label,
            "num_qubits": self.num_qubits,
            "gate_count": len(self.gates),
            "counts": self.counts(),
            "toffoli_count": self.toffoli_count(),
            "toffoli_equivalent_ancilla_free": self.toffoli_equivalent(ancilla_free=True),
            "t_count_explicit": self.t_count(),
            "t_count_with_toffolis": self.t_count(toffoli_equivalent=True),
            "ir_depth": self.depth(),
            "ancilla_peak": self.ancilla_peak(),
            "classically_simulable": self.is_classically_simulable(),
        }

    def __len__(self) -> int:
        return len(self.gates)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"GateList(width={self.num_qubits}, gates={len(self.gates)}, "
            f"depth={self.depth()}, label={self.label!r})"
        )
