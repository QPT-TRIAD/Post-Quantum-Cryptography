"""The boundary between a classical predicate and a quantum circuit.

Every oracle in this project is an :class:`OracleSpec`: a thing that can say which register values
are marked, and can build itself as reversible gates. Everything downstream — the phase oracle, the
diffuser, the backends, the probes — talks to this interface and never to a particular relation.

**The predicate contract.** ``build_predicate(lowering)`` returns a :class:`GateList` over
``search_width() + ancilla_width(lowering)`` qubits in which:

* qubits ``0 .. search_width()-1`` are the search register, little-endian;
* the **last** qubit is the flag;
* the net effect is ``flag ^= [the register value is marked]``.

**The ancillas may be left dirty, and that is the contract rather than an oversight.** A predicate
is always used inside a sandwich — ``predicate ; Z(flag) ; predicate.inverse()`` — and the inverse is
exact, so every ancilla returns to ``|0>`` whether or not the forward pass cleaned up after itself.
Requiring the predicate to be clean on its own would mean uncomputing the accumulator at the end of
every row, doubling the gate count of the thing this project exists to count. The property the tests
assert is therefore that the *sandwich* is the identity up to the flag's phase, which is exactly
what the oracle needs and strictly more than cleanness would give.

The truth-table lowering happens to be clean anyway — it is X-conjugated multi-controlled X gates
with no ancillas — so it can be, and is, used standalone.

Nothing else. That contract is what lets the oracle builder put one ``Z`` on the flag between a
predicate and its exact inverse and get a phase oracle, for any spec, without knowing what the spec
computes.

**Two lowerings, and the truth-table one is not a shortcut.** ``TRUTH_TABLE`` builds a
multi-controlled X per marked state; it is ancilla-free and it is the oracle of record at small
widths. ``ARITHMETIC`` compiles the actual relation. They must agree on every basis state at every
enumerable width, and that agreement is acceptance condition 6 of the build plan — the test that
keeps the gate-count extrapolation attached to a circuit that computes the right function.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Iterable

import numpy as np

from ..circuits.ir import GateList, GateName
from ..circuits.reversible_arithmetic import (
    add_constant,
    equal_to_constant,
    less_than_constant,
    multi_controlled_x,
    sample_intervals,
)
from .qlwr_instance import QLWRInstance
from .search_space import SearchSpace

__all__ = [
    "Lowering",
    "OracleSpec",
    "QLWROracleSpec",
    "RandomControlOracleSpec",
    "HiddenPeriodOracleSpec",
]


class Lowering(str, Enum):
    """How a predicate is turned into gates."""

    TRUTH_TABLE = "truth_table"
    """One multi-controlled X per marked state. Ancilla-free, exact, and only usable at widths
    small enough to enumerate. The oracle of record at those widths."""

    ARITHMETIC = "arithmetic"
    """The relation compiled to reversible arithmetic. This is the circuit whose gate count the
    extrapolation is about."""


class OracleSpec(ABC):
    """A marked-set predicate, with its circuit lowerings."""

    name: str = "spec"

    @property
    def supports_arithmetic_lowering(self) -> bool:
        """Whether :attr:`Lowering.ARITHMETIC` means anything for this spec.

        False for a uniformly random marked set: a random function has no arithmetic form, and its
        "arithmetic" lowering *is* its lookup table. That is not a gap in the interface — it is the
        negative control doing its job, and the control's ``Theta(M * n)`` cost is precisely the
        baseline against which a real relation's ``Theta(n**2)`` is the finding.
        """
        return True

    @abstractmethod
    def search_width(self) -> int:
        """Number of qubits in the search register."""

    @abstractmethod
    def marked_set(self) -> frozenset[int]:
        """Every marked register value, exactly."""

    @abstractmethod
    def ancilla_width(self, lowering: Lowering) -> int:
        """Ancillas the predicate needs, between the search register and the flag."""

    @abstractmethod
    def build_predicate(self, lowering: Lowering) -> GateList:
        """The predicate as gates, per the module-level contract."""

    # -- derived, never overridden -------------------------------------------------------------

    def space(self) -> SearchSpace:
        """The search space, built from the marked set rather than from a count.

        There is deliberately no way to declare ``M`` separately from the marked set. A spec that
        could report an ``M`` unrelated to the set it actually marks is a spec whose success curve
        and whose circuit describe different problems.
        """
        return SearchSpace(self.search_width(), self.marked_set())

    def truth_table(self) -> np.ndarray:
        """A boolean array of length ``2**search_width``, True at marked values."""
        table = np.zeros(1 << self.search_width(), dtype=bool)
        for x in self.marked_set():
            table[x] = True
        return table

    def is_marked(self, value: int) -> bool:
        return value in self.marked_set()

    def describe(self) -> dict:
        """Scalar facts for a report."""
        space = self.space()
        return {
            "name": self.name,
            "search_width": self.search_width(),
            "n_items": space.n_items,
            "n_marked": space.n_marked,
            "marked_fraction": space.marked_fraction,
            "optimal_iterations": space.optimal_iterations,
            "supports_arithmetic_lowering": self.supports_arithmetic_lowering,
            "ancilla_width_truth_table": self.ancilla_width(Lowering.TRUTH_TABLE),
            "ancilla_width_arithmetic": self.ancilla_width(Lowering.ARITHMETIC),
        }

    # -- shared lowering -----------------------------------------------------------------------

    def _build_truth_table(self) -> GateList:
        """One X-conjugated multi-controlled X per marked state, XORed into the flag.

        The conjugations turn "the register reads exactly this pattern" into a multi-controlled X.
        At ``M = 1`` — the QLWR instance's case by construction — this is a single gate, which is
        why the truth-table lowering is not merely a testing convenience but the thing that makes
        large-``n`` Grover simulable at all.
        """
        n = self.search_width()
        gl = GateList(n + 1, label=f"{self.name}:truth_table")
        flag = n
        for value in sorted(self.marked_set()):
            zero_bits = [q for q in range(n) if not (value >> q) & 1]
            for q in zero_bits:
                gl.append(GateName.X, q)
            multi_controlled_x(gl, tuple(range(n)), flag)
            for q in zero_bits:
                gl.append(GateName.X, q)
        return gl


# -----------------------------------------------------------------------------------------------
# QLWR
# -----------------------------------------------------------------------------------------------


class QLWROracleSpec(OracleSpec):
    """Secret recovery against a scaled QLWR instance.

    The search is over ``s' in Z_{q_L}^nu``; a value is marked when every one of the ``m`` registered
    samples reproduces the target, and the target is ``F`` applied to the real secret.

    **The circuit never reduces the accumulator by a division.** Each addend ``X_ij * 2**t`` is
    reduced mod ``q_L`` *as a classical constant* before it is added, and a conditional subtraction
    of ``q_L`` follows each controlled addition. That is sound because reduction distributes over
    addition — ``(a mod q + b mod q) mod q == (a + b) mod q`` — and it bounds the accumulator at
    ``q_L`` instead of at ``nu * (q_L - 1)**2``. The accumulator is therefore ``w + 1`` qubits rather
    than ``2w``, and the circuit contains no modular reduction block at all: the reduction is folded
    into the constants and into the one conditional subtraction. The building blocks this rests on
    are each verified exhaustively in :mod:`grover_emulator.circuits.reversible_arithmetic`.
    """

    name = "qlwr"

    def __init__(self, instance: QLWRInstance):
        self.instance = instance
        self._marked: frozenset[int] | None = None
        self._ancilla_counts: dict[Lowering, int] = {}

    # -- layout --------------------------------------------------------------------------------

    @property
    def _w(self) -> int:
        return self.instance.w

    @property
    def _n_search(self) -> int:
        return self.instance.n_search

    @property
    def _acc_width(self) -> int:
        """Accumulator bits: it holds a value below ``q_L`` and one addition above it."""
        return self._w + 1

    def _layout(self) -> dict[str, list[int]]:
        """Qubit roles for the arithmetic lowering.

        Fixed here, once, rather than recomputed by the builder — a layout computed in two places is
        a layout that will eventually disagree with itself.

        ``redflags`` is the pool of conditional-subtract controls, one per controlled addition. They
        are dirty while a row is being accumulated and are cleaned by that row's own inverse pass,
        which is what lets one pool of ``nu * w`` serve every row instead of one pool per row.
        """
        inst = self.instance
        n = self._n_search
        w1 = self._acc_width
        layout: dict[str, list[int]] = {"search": list(range(n))}
        cursor = n
        for name, size in (
            ("acc", w1),
            ("work", w1),
            ("rowflags", inst.m),
            ("valid_flags", inst.nu),
            ("valid", 1),
            ("all_match", 1),
            ("redflags", inst.nu * self._w),
            ("flag", 1),
        ):
            layout[name] = list(range(cursor, cursor + size))
            cursor += size
        layout["total"] = list(range(cursor))
        return layout

    def search_width(self) -> int:
        return self._n_search

    def ancilla_width(self, lowering: Lowering) -> int:
        if lowering is Lowering.TRUTH_TABLE:
            return 0
        if lowering is not Lowering.ARITHMETIC:
            raise ValueError(f"unknown lowering {lowering!r}")
        if lowering not in self._ancilla_counts:
            # ``layout["total"]`` spans the search register, the work ancillas *and* the flag,
            # because the arithmetic predicate is built as one gate list over all of them. The flag
            # is not an ancilla — it sits after them and is the qubit ``build_phase_oracle`` kicks
            # back from — so it is subtracted rather than counted, which is what the abstract
            # docstring above promises. Counting it made ``oracle_width`` report one qubit more than
            # the circuit it was naming: a width no circuit in this project has.
            self._ancilla_counts[lowering] = len(self._layout()["total"]) - self._n_search - 1
        return self._ancilla_counts[lowering]

    def marked_set(self) -> frozenset[int]:
        if self._marked is None:
            self._marked = self.instance.marked_set()
        return self._marked

    # -- the arithmetic lowering ---------------------------------------------------------------

    def build_predicate(self, lowering: Lowering) -> GateList:
        if lowering is Lowering.TRUTH_TABLE:
            return self._build_truth_table()
        if lowering is not Lowering.ARITHMETIC:
            raise ValueError(f"unknown lowering {lowering!r}")
        return self._build_arithmetic()

    def _component_bits(self, j: int) -> list[int]:
        """Search-register qubits holding component ``j`` of the candidate secret."""
        w = self._w
        return list(range(j * w, (j + 1) * w))

    def _accumulate_row(self, row: int, acc: list[int], work: list[int], redflags: list[int]) -> GateList:
        """The forward pass that leaves the reduced inner product for one row in ``acc``.

        Each addend is reduced mod ``q_L`` *as a classical constant* before it is added, so the
        accumulator holds a value below ``q_L`` before each addition and below ``2*q_L`` after it.
        One conditional subtraction then restores it to ``[0, q_L)``. The two facts that make this
        sound are that reduction distributes over addition, and that ``q_L < 2**w`` so a single
        subtraction always suffices.

        The conditional-subtract controls are deliberately left **dirty**. This function returns only
        the forward pass; the caller extends with its exact inverse straight afterwards, and that
        inverse is what clears them. Building the cleanup here instead would mean recomputing a
        comparison against a value the subtraction has already changed, which does not work — the
        comparison result is not recoverable from the reduced accumulator.
        """
        inst = self.instance
        gl = GateList(0, label=f"row{row}:forward")
        gl.num_qubits = max(acc + work + redflags) + 1
        k = 0
        for j in range(inst.nu):
            bits = self._component_bits(j)
            for t in range(self._w):
                addend = (inst.base[row][j] << t) % inst.q_l
                if addend:
                    add_constant(gl, acc, addend, control=bits[t])

                # Conditional subtraction of q_L, controlled on acc >= q_L.
                less_than_constant(gl, acc, inst.q_l, redflags[k], work)
                gl.append(GateName.X, redflags[k])  # now reads "acc >= q_L"
                add_constant(gl, acc, (1 << len(acc)) - inst.q_l, control=redflags[k])
                k += 1
        return gl

    def _build_arithmetic(self) -> GateList:
        inst = self.instance
        lay = self._layout()
        gl = GateList(len(lay["total"]), label=f"{self.name}:arithmetic")
        acc, work = lay["acc"], lay["work"]
        rowflags, valid = lay["rowflags"], lay["valid"][0]
        all_match, flag = lay["all_match"][0], lay["flag"][0]
        valid_flags, redflags = lay["valid_flags"], lay["redflags"]

        # --- validity: every component of the candidate must be below q_L ------------------------
        # The register is wider than the space it encodes whenever q_L is not a power of two, which
        # genericity forces. An out-of-range component encodes no secret and must never be marked.
        for j in range(inst.nu):
            less_than_constant(gl, self._component_bits(j), inst.q_l, valid_flags[j], work)
        multi_controlled_x(gl, tuple(valid_flags), valid)

        # --- one row at a time, each accumulated and then exactly un-accumulated -----------------
        # The forward pass leaves its conditional-subtract controls dirty, so its inverse follows
        # immediately after the row's comparison. That both restores the accumulator for the next
        # row and clears the flags, which is what lets one pool of controls serve every row.
        for i in range(inst.m):
            forward = self._accumulate_row(i, acc, work, redflags)
            gl.extend(forward)
            for lo, hi in sample_intervals(inst.q_l, inst.p, inst.target[i]):
                # [lo <= acc <= hi]  ==  [acc < lo] XOR [acc < hi + 1], and the two are disjoint.
                less_than_constant(gl, acc, lo, rowflags[i], work)
                less_than_constant(gl, acc, hi + 1, rowflags[i], work)
            gl.extend(forward.inverse())

        # --- conjunction over rows and over validity, then into the flag -------------------------
        multi_controlled_x(gl, tuple(rowflags), all_match)
        gl.append(GateName.CCX, all_match, valid, flag)

        # The validity flags and all_match are left set on purpose: the oracle sandwich takes this
        # whole gate list's inverse, and that is what returns every ancilla to |0>.
        return gl


# -----------------------------------------------------------------------------------------------
# controls
# -----------------------------------------------------------------------------------------------


class RandomControlOracleSpec(OracleSpec):
    """A uniformly random marked set of a requested size — the negative control.

    It exists so that "no structure detected" means something. A probe suite that has never once
    fired is indistinguishable from a broken one, and this is the spec that proves it does not fire
    when there is nothing to find.
    """

    name = "random_control"

    def __init__(self, n_qubits: int, n_marked: int, seed: int):
        self.n_qubits = n_qubits
        self.n_marked = n_marked
        self.seed = seed
        rng = np.random.default_rng(seed)
        if not 1 <= n_marked < (1 << n_qubits):
            raise ValueError(f"n_marked={n_marked} must be in [1, 2**{n_qubits})")
        chosen = rng.choice(1 << n_qubits, size=n_marked, replace=False)
        self._marked = frozenset(int(x) for x in chosen)

    @property
    def supports_arithmetic_lowering(self) -> bool:
        """False, and the interface says so rather than pretending otherwise.

        A uniformly random function has no arithmetic form. Its "arithmetic" lowering is its lookup
        table, which is exactly what :meth:`build_predicate` returns for both lowerings — and the
        ``Theta(M n)`` cost of that table is the baseline a real relation's ``Theta(n**2)`` is
        measured against, not a defect to be worked around.
        """
        return False

    def search_width(self) -> int:
        return self.n_qubits

    def marked_set(self) -> frozenset[int]:
        return self._marked

    def ancilla_width(self, lowering: Lowering) -> int:
        return 0

    def build_predicate(self, lowering: Lowering) -> GateList:
        return self._build_truth_table()


class HiddenPeriodOracleSpec(OracleSpec):
    """A marked set with a planted XOR-period — the positive control.

    Marks ``x`` when ``x`` and ``x XOR period`` both lie in a chosen half-space, so that
    ``f(x) = f(x XOR period)`` holds for every ``x``. The structural probes **must** detect this;
    if they do not, they are not detecting anything, and their silence on the real relation would
    mean nothing.

    This is a control, not a security target: the period is planted by construction and is known to
    the generator.
    """

    name = "hidden_period"

    def __init__(self, n_qubits: int, period: int, seed: int):
        if n_qubits < 2:
            raise ValueError("a hidden period needs at least 2 qubits")
        if not 0 < period < (1 << n_qubits):
            raise ValueError(f"period {period} outside the register")
        self.n_qubits = n_qubits
        self.period = period
        self.seed = seed
        rng = np.random.default_rng(seed)
        # Mark x when the low bit of x is 0 and x < N/2 in the folded space, which is closed under
        # x -> x XOR period exactly when period's low bit is zero.
        if period & 1:
            raise ValueError("the planted period must have its low bit clear for this construction")
        half = (1 << n_qubits) // 2
        base = {int(x) for x in rng.choice(half, size=max(1, half // 8), replace=False)}
        marked = set()
        for x in base:
            marked.add(x)
            marked.add(x ^ period)
        self._marked = frozenset(m for m in marked if 0 <= m < (1 << n_qubits))

    def search_width(self) -> int:
        return self.n_qubits

    def marked_set(self) -> frozenset[int]:
        return self._marked

    def ancilla_width(self, lowering: Lowering) -> int:
        return 0

    def build_predicate(self, lowering: Lowering) -> GateList:
        """Both lowerings are the lookup table: the structure is in *which* states are marked, and
        a planted period has no arithmetic form to compile."""
        return self._build_truth_table()
