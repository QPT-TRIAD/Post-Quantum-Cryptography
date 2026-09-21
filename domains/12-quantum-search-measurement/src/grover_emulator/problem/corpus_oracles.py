"""The corpus's own two relations, brought behind the same interface as the controls.

Everything else in :mod:`grover_emulator.problem` is generated here: the QLWR instance, the random
control, the planted period. These two are not. They are the relations the audit corpus this
project's questions come from actually attacks, and the reason to carry them as
:class:`~grover_emulator.problem.oracle_spec.OracleSpec` is that a spec is the only place in the
project where "what is being searched" is written down. Once either of them is a spec, the phase
oracle, the exhaustive equivalence test, the structural probes and the gate accounting apply to it
unchanged, and its gate count is comparable with every other number the project reports.

**The chain that is not a chain.** The corpus's reduced-size LM-OTS game — ``grover_chain_inversion``
in ``pq_audit_s1_lms_v2.1.py`` — is documented as inverting "the chain value of a random secret".
The body iterates nothing: ``f`` is a *single* truncated SHA-256 over ``I || q || i || j || x``, with
those four fields doing domain separation, so the preimage of one chain node is one hash. That is a
sound reading of the structure — the node ``(i, j)`` is its own function, which is exactly why the
same file's attack ledger counts one target per function and blocks a multi-target speedup — but it
is not the reading the docstring gives, and the difference is load-bearing for anything that reports
a chain *length*. :class:`LMOtsChainSpec` implements both behind ``chain_length``, has ``k = 1``
reproduce the corpus's behaviour gate for gate, and writes the convention it used into every report
rather than leaving a reader to infer it from a default.

**Two defects in the upstream game, fixed rather than inherited.** Its secret is drawn with an
unseeded ``secrets.randbelow(N)``, so the marked-set size ``M`` changes from run to run and nothing
in the recorded result says which draw produced it; here the draw is derived from the description of
the thing being built (:mod:`grover_emulator.utils.seeding`) and ``M`` is a reported fact. And its
first peak is taken with ``next(...)`` and no default, which raises ``StopIteration`` whenever the
marked set is empty or the sampled window does not contain a peak; here a missing peak is ``None``,
because a missing peak is a fact about the window rather than a failure of the search.
"""

from __future__ import annotations

import hashlib
import math
import struct
from enum import Enum

import numpy as np

from ..circuits.ir import GateList, GateName
from ..circuits.reversible_arithmetic import multi_controlled_x
from ..utils.seeding import RunSeeds, derive_seed, rng_for
from .oracle_spec import Lowering, OracleSpec

__all__ = [
    "ChainConvention",
    "LMOtsChainSpec",
    "KeyMapMode",
    "ModeBKeyMapSpec",
]


def _u32(value: int) -> bytes:
    return struct.pack(">I", value)


def _u16(value: int) -> bytes:
    return struct.pack(">H", value)


def _u8(value: int) -> bytes:
    return struct.pack(">B", value)


# -----------------------------------------------------------------------------------------------
# the keyed LM-OTS chain node
# -----------------------------------------------------------------------------------------------


class ChainConvention(str, Enum):
    """Which reading of "chain" a spec is built on. Reported, never assumed."""

    SINGLE_HASH = "single_hash"
    """One truncated SHA-256 per candidate: the corpus's own behaviour, and the behaviour
    ``chain_length = 1`` reproduces exactly. The target is the ``(I, q, i, j)`` node's value, and the
    search is the preimage of that one node."""

    ITERATED_CHAIN = "iterated_chain"
    """``chain_length = k > 1`` applications of the node function, the chain index advancing by one
    per application — the RFC 8554 chain function, whose ``j`` is the step it is on. It starts at
    the spec's ``j``, so at ``k = 1`` it collapses to the same call the corpus makes, and above it
    the two readings are the same node function applied a different number of times. They are
    nevertheless different search problems, which is why the count is pinned in every report."""


class LMOtsChainSpec(OracleSpec):
    """Preimage of a keyed LM-OTS chain value — the corpus's reduced-size game G2.

    A candidate ``x`` is marked when the chain evaluated at ``x`` equals the target, and the target
    is the chain evaluated at a secret the spec draws and records. Everything about the drawing is
    seeded: the same construction gives the same secret, the same marked set, and the same ``M`` in
    every process, which is the property the upstream game does not have.

    Args:
        n_bits: width of the chain value in bits, i.e. the corpus's ``n``. The digest is taken over
            ``(n_bits + 7) // 8`` bytes and masked to ``n_bits`` bits, exactly as upstream — the mask
            is a fold, not a truncation of the digest to whole bytes, and at widths that are not a
            multiple of eight the two differ.
        chain_length: ``k``. 1 is the corpus's single hash; above 1 is a real chain, see
            :class:`ChainConvention`.
        fold_bits: width of the input the search register carries. It defaults to ``n_bits``, which
            is the corpus's reduced-size arrangement — there the searched value and the compared
            image are the same width. The two come apart on the real object, where a chain node
            takes an ``n``-byte input while the comparison is over the truncated image, so this is
            the knob that keeps the spec from silently encoding one width's assumption in the other.
        identifier: the 16-byte LM-OTS ``I`` field.
        q, i, j: the remaining domain-separation fields, as in the corpus: the leaf index, the chain
            index, and the position within the chain.
        seed: seeds the secret draw. Derived into a seed rather than used raw, so the record of the
            draw is the description of the spec.
        target: an explicit chain value to invert. ``None`` (the default) takes the chain value of
            the drawn secret, which guarantees ``M >= 1``; an explicit target that no candidate
            reaches is refused at construction rather than producing a spec with nothing to search.
        seeds: an optional :class:`~grover_emulator.utils.seeding.RunSeeds` record. When given, the
            secret's seed and the marked-set size are written into it, so the run's record carries
            the ``M`` its success curve was computed against.

    **Width.** The search register is ``fold_bits`` wide, the relation's answer lands in one work
    qubit and the flag is the last qubit, so the oracle is ``fold_bits + 2`` wide. The work qubit is
    not bookkeeping: it is where the relation's own answer lives, it is left set on marked inputs by
    construction, and the oracle sandwich's exact inverse is what clears it — the same contract the
    arithmetic lowering relies on, and the reason :func:`assert_sandwich_is_identity` rather than
    :func:`assert_ancillas_return_clean` is the assertion this spec is held to.
    """

    name = "lmots_chain"

    def __init__(
        self,
        n_bits: int,
        chain_length: int = 1,
        fold_bits: int | None = None,
        *,
        identifier: bytes = b"I" * 16,
        q: int = 3,
        i: int = 5,
        j: int = 2,
        seed: int = 20260913,
        target: int | None = None,
        seeds: RunSeeds | None = None,
    ):
        if n_bits < 2:
            raise ValueError(f"n_bits must be at least 2, got {n_bits}")
        if chain_length < 1:
            raise ValueError(f"chain_length must be at least 1, got {chain_length}")
        if len(identifier) != 16:
            raise ValueError(f"the LM-OTS I field is 16 bytes, got {len(identifier)}")
        if not 0 <= q < (1 << 32):
            raise ValueError(f"q is a u32, got {q}")
        if not 0 <= i < (1 << 16):
            raise ValueError(f"i is a u16, got {i}")
        if not 0 <= j + chain_length - 1 < (1 << 8):
            raise ValueError(
                f"the chain runs to index {j + chain_length - 1}, which does not fit the u8 chain "
                "index; lower j or the chain length"
            )

        self.n_bits = n_bits
        self.chain_length = chain_length
        self.fold_bits = n_bits if fold_bits is None else fold_bits
        if not 2 <= self.fold_bits <= (self._input_bytes * 8):
            raise ValueError(
                f"fold_bits={self.fold_bits} is outside 2..{self._input_bytes * 8} for n_bits="
                f"{n_bits}; the searched input must fit the {self._input_bytes} bytes the digest "
                "takes"
            )
        self.identifier = identifier
        self.q, self.i, self.j = q, i, j
        self.seed = seed
        self.seeds = seeds

        self.convention = (
            ChainConvention.SINGLE_HASH if chain_length == 1 else ChainConvention.ITERATED_CHAIN
        )

        self._secret = self._draw_secret()
        self._target = self._chain(self._secret) if target is None else int(target)
        if not 0 <= self._target < (1 << n_bits):
            raise ValueError(f"target {self._target} does not fit in {n_bits} bits")

        self._marked = frozenset(x for x in range(1 << self.fold_bits) if self._chain(x) == self._target)
        if not self._marked:
            raise ValueError(
                f"no candidate in the {1 << self.fold_bits}-value search space reaches the target "
                f"{self._target}; the marked set would be empty and Grover would have nothing to "
                "amplify"
            )
        if seeds is not None:
            seeds.record(f"{self.name}.marked_set_size", len(self._marked))
            seeds.record(f"{self.name}.target", self._target)

    # -- the relation ---------------------------------------------------------------------------

    @property
    def _input_bytes(self) -> int:
        """Bytes the digest takes, as upstream: ``ceil(n_bits / 8)``."""
        return (self.n_bits + 7) // 8

    def _draw_secret(self) -> int:
        """The secret whose chain value is the target, drawn from a derived seed.

        The derivation is the one :mod:`grover_emulator.utils.seeding` gives as its example, so the
        draw is a function of the problem's description alone: the same ``(n_bits, chain_length,
        fold_bits)`` gives the same secret in another process, under another hash seed, on another
        machine.
        """
        parts = ("lmots_chain", self.n_bits, self.chain_length, self.fold_bits, int(self.seed))
        if self.seeds is not None:
            return int(self.seeds.rng(*parts).integers(0, 1 << self.fold_bits))
        return int(rng_for(derive_seed(*parts)).integers(0, 1 << self.fold_bits))

    def _node(self, value: int, j: int) -> int:
        """One application of the corpus's keyed hash at chain index ``j``.

        Reproduced field for field — the same domain-separation order, the same big-endian
        encodings, the same ``ceil(n_bits / 8)`` prefix of the digest, the same mask. The mask is
        what makes widths that are not multiples of eight behave as the corpus does, and it is easy
        to "simplify" into a different function: at ``n_bits = 10`` the corpus keeps the low ten bits
        of a two-byte prefix, not the high ten.
        """
        payload = (
            self.identifier
            + _u32(self.q)
            + _u16(self.i)
            + _u8(j)
            + value.to_bytes(self._input_bytes, "big")
        )
        digest = hashlib.sha256(payload).digest()
        return int.from_bytes(digest[: self._input_bytes], "big") & ((1 << self.n_bits) - 1)

    def _chain(self, value: int) -> int:
        """The chain value of ``value`` under this spec's convention.

        At ``chain_length = 1`` this is one call to :meth:`_node` at index ``j``, which is exactly
        the corpus's ``f``. Above it, the index advances by one per application, so the chain is the
        RFC 8554 one rather than the same single-node function applied to itself — the two are
        different problems above ``k = 1`` and the report says which was run.
        """
        for step in range(self.chain_length):
            value = self._node(value, self.j + step)
        return value

    # -- the interface --------------------------------------------------------------------------

    def search_width(self) -> int:
        return self.fold_bits

    def marked_set(self) -> frozenset[int]:
        return self._marked

    def ancilla_width(self, lowering: Lowering) -> int:
        """One work qubit for either lowering.

        A truncated SHA-256 has no arithmetic form to compile — the conclusion
        :class:`~grover_emulator.problem.oracle_spec.RandomControlOracleSpec` reaches for a random
        function, reached here for a different reason: the relation is a hash, and the IR has no
        block that computes one. Both lowerings are therefore the marked set written as gates, and
        the width is the same for both.
        """
        if lowering not in (Lowering.TRUTH_TABLE, Lowering.ARITHMETIC):
            raise ValueError(f"unknown lowering {lowering!r}")
        return 1

    @property
    def supports_arithmetic_lowering(self) -> bool:
        """False. See :meth:`ancilla_width`: there is no arithmetic form, so claiming one would be
        a claim about a circuit that does not exist."""
        return False

    def build_predicate(self, lowering: Lowering) -> GateList:
        """The relation's answer in the work qubit, copied into the flag.

        The base class's truth-table build already emits one X-conjugated multi-controlled X per
        marked state, which is the whole of this relation as gates; what it does not do is keep the
        answer in a qubit of its own. It is copied up rather than rebuilt so that the two spec
        families cannot drift: the gate list here is the base one plus a single controlled X, and if
        that build ever changes, this changes with it.
        """
        if lowering not in (Lowering.TRUTH_TABLE, Lowering.ARITHMETIC):
            raise ValueError(f"unknown lowering {lowering!r}")
        n = self.search_width()
        answered = self._build_truth_table()  # n + 1 qubits, the answer in qubit n
        gl = GateList(n + 2, list(answered.gates), label=f"{self.name}:{self.convention.value}")
        gl.append(GateName.CX, n, n + 1)
        return gl

    # -- the corpus's game, and its reports ------------------------------------------------------

    def grover_curve(self, max_iterations: int | None = None) -> dict:
        """The exact success curve for this spec, and the quantities the corpus's game returns.

        The amplitudes are stepped as the corpus steps them — phase flip on the marked set, then
        inversion about the mean — so this is the same measurement rather than a closed form wearing
        the same column names. The closed form is reported beside it, and the two agreeing is what
        says the curve is the standard one.

        Args:
            max_iterations: how far to step the oscillation. The default is derived from the
                optimum, as the sweep's iteration range is, rather than fixed here.

        Returns:
            A JSON-safe report. ``k_first_peak`` is the first iteration count at which the curve
            turns over, or ``None`` when the window contains no turnover — the case the upstream
            code raised ``StopIteration`` on. ``chain_convention`` and ``chain_length`` are in the
            report so that a number cannot be quoted without the semantics it was measured under.
        """
        space = self.space()
        n_items, n_marked = space.n_items, space.n_marked
        theta = math.asin(math.sqrt(n_marked / n_items))
        k_predicted = int(math.floor(math.pi / (4 * theta))) if theta > 0 else 0
        if max_iterations is None:
            max_iterations = 2 * k_predicted + 2

        amp = np.full(n_items, 1.0 / math.sqrt(n_items))
        marked = np.zeros(n_items, dtype=bool)
        for x in self._marked:
            marked[x] = True
        probs = [float((amp[marked] ** 2).sum())]
        for _ in range(max_iterations):
            amp[marked] *= -1.0
            amp = 2.0 * amp.mean() - amp
            probs.append(float((amp[marked] ** 2).sum()))

        k_first_peak = next((k for k in range(1, len(probs) - 1) if probs[k + 1] < probs[k]), None)
        return {
            "name": self.name,
            "n_search": self.search_width(),
            "n_items": n_items,
            "n_marked": n_marked,
            "chain_length": self.chain_length,
            "chain_convention": self.convention.value,
            "k_predicted": k_predicted,
            "k_first_peak": k_first_peak,
            "p_at_k_first_peak": None if k_first_peak is None else probs[k_first_peak],
            "k_first_peak_closed_form": space.first_peak_iteration(max_iterations),
            "p_at_k_predicted": probs[k_predicted] if k_predicted < len(probs) else None,
            "p_predicted": space.success_probability(k_predicted),
            "max_iterations": max_iterations,
        }

    def report(self) -> dict:
        """The spec's facts, with the convention pinned and nothing left to infer.

        The base :meth:`describe` is the shape every spec reports; this adds the fields that only
        mean anything here, and the first of them is which chain semantics the numbers below
        describe. A marked-set size without that is a number that could belong to two different
        problems.
        """
        out = self.describe()
        out.update(
            {
                "chain_length": self.chain_length,
                "chain_convention": self.convention.value,
                "chain_applications": self.chain_length,
                "n_bits": self.n_bits,
                "fold_bits": self.fold_bits,
                "input_bytes": self._input_bytes,
                "identifier": self.identifier.hex(),
                "q": self.q,
                "i": self.i,
                "j": self.j,
                "target": self._target,
                "secret": self._secret,
                "seed": int(self.seed),
                "work_qubits": 1,
            }
        )
        return out


# -----------------------------------------------------------------------------------------------
# the expanding quadratic key map
# -----------------------------------------------------------------------------------------------


class KeyMapMode(str, Enum):
    """Which of the corpus's two key-map registers a spec searches."""

    A = "A"
    """The map's own variables: the opening ``s || r``, two ``n``-bit halves, so ``2n`` qubits."""

    B = "B"
    """Twice that register, ``4n`` qubits. Named for the mode the corpus's production key map is
    instantiated in, where the map is the expanding object rather than a balanced one."""


class ModeBKeyMapSpec(OracleSpec):
    """A seeded expanding quadratic map over ``F2`` — the corpus's Mode-B key map.

    Equation ``e`` of the map is ``y_e = c_e XOR <b_e, x> XOR sum_{i<j} A_e[i][j] x_i x_j``, one
    equation per output bit, with ``A_e`` stored as the upper triangle the corpus stores it as. The
    spec's search register is the map's variable vector; a candidate is marked when the map's output
    equals the target, which is the map's output at a drawn secret unless the caller supplies one.

    **One work qubit per equation, and the width that follows.** The relation is evaluated in the
    circuit, one quadratic form per output bit, each into its own work qubit — the corpus's map has
    ``2n + E`` equations and this is where that count becomes circuit width. The flag then takes the
    conjunction over the equations. With the default single equation the oracle is ``n_vars + 2``
    wide: ``2n + 2`` in mode ``A``, ``4n + 2`` in mode ``B``. A caller who wants a preimage-sized
    marked set rather than the half-tagged register a single equation gives expands the map, and pays
    one work qubit per equation for it.

    **The gate convention, measured rather than assumed.** The corpus stores ``A`` as an upper
    triangle and evaluates ``sum_{i<j} A[i][j] x_i x_j`` directly, and this spec's arithmetic
    lowering is the network that computes exactly that: one controlled X per linear term and one
    Toffoli per monomial, folded into the work qubit. The framework's ``QuadraticFormGate`` computes
    the same function — ``x^T A x + x^T b + c`` with ``A`` used as given, which the API probe
    measures and the tests re-measure at small width — but it is a framework gate and the IR is a
    closed set of permutations and phases with no quadratic-form member, so the lowering is the
    hand-built network on purpose. The two agree by construction: over ``F2`` the monomials ``i < j``
    of an upper triangle are the whole of ``x^T A x``, with no symmetrisation and no doubled
    off-diagonal terms.

    **The work qubits are left dirty, and that is the contract.** The forward pass leaves them
    holding the map's output; the oracle sandwich's exact inverse is what returns them to ``|0>``.
    """

    name = "key_map"

    def __init__(
        self,
        n: int,
        mode: KeyMapMode = KeyMapMode.B,
        *,
        seed: bytes = b"grover-oracle-emulator/key-map",
        n_outputs: int = 1,
        target: int | None = None,
        seeds: RunSeeds | None = None,
    ):
        if n < 2:
            raise ValueError(f"n must be at least 2, got {n}")
        if not isinstance(seed, (bytes, bytearray)):
            raise TypeError(f"seed must be bytes, got {type(seed).__name__}")
        if not 1 <= n_outputs <= 64:
            raise ValueError(f"n_outputs must be in 1..64, got {n_outputs}")

        self.n = n
        self.mode = mode
        self.seed = bytes(seed)
        self.n_outputs = n_outputs
        self.n_vars = 2 * n if mode is KeyMapMode.A else 4 * n
        self.seeds = seeds

        # The map's equations, materialised from the corpus's own seeded stream.
        self._const: list[int] = []
        self._lin: list[int] = []
        self._rows: list[list[int]] = []  # _rows[e][i] keeps bits j > i only
        for e in range(n_outputs):
            const, lin, rows = self._equation(e)
            self._const.append(const)
            self._lin.append(lin)
            self._rows.append(rows)

        self._secret = self._draw_secret()
        self._target = self._evaluate(self._secret) if target is None else int(target)
        if not 0 <= self._target < (1 << n_outputs):
            raise ValueError(
                f"target {self._target} does not fit in the {n_outputs} output bit(s) of this map"
            )

        self._marked = frozenset(x for x in range(1 << self.n_vars) if self._evaluate(x) == self._target)
        if not self._marked:
            raise ValueError(
                f"no candidate reaches the target {self._target}; the marked set would be empty and "
                "Grover would have nothing to amplify"
            )
        if seeds is not None:
            seeds.record(f"{self.name}.marked_set_size", len(self._marked))
            seeds.record(f"{self.name}.target", self._target)

    # -- the map --------------------------------------------------------------------------------

    @property
    def _var_bytes(self) -> int:
        return (self.n_vars + 7) // 8

    def _equation(self, e: int) -> tuple[int, int, list[int]]:
        """Equation ``e`` of the seeded map, as ``(const, linear, rows)``.

        The stream is the corpus's: a ``shake_256`` XOF over ``b'CQ46/F'`` and the seed, walked as
        ``const`` byte, ``linear`` mask, then one mask per row with everything at or below the
        diagonal cleared. It is taken as a prefix, so materialising equation ``e`` alone gives the
        same bytes the corpus's whole-stream version gives at that offset — which is what lets this
        spec build the first few equations of the corpus's production map without materialising
        thirty megabytes of the rest.
        """
        stride = 1 + self._var_bytes * (self.n_vars + 1)
        stream = hashlib.shake_256(b"CQ46/F" + self.seed).digest(stride * (e + 1))
        pos = stride * e
        const = stream[pos] & 1
        pos += 1
        mask = (1 << self.n_vars) - 1
        lin = int.from_bytes(stream[pos : pos + self._var_bytes], "big") & mask
        pos += self._var_bytes
        rows = []
        for i in range(self.n_vars):
            row = int.from_bytes(stream[pos : pos + self._var_bytes], "big") & mask
            pos += self._var_bytes
            rows.append(row & ~((1 << (i + 1)) - 1))  # keep j > i only
        return const, lin, rows

    def _evaluate(self, x: int) -> int:
        """The map's output on ``x``, as an ``n_outputs``-bit integer.

        The corpus's evaluation, term for term: the constant, the parity of the linear mask, then
        the parity of each row against the set bits of ``x``. Written with integer parities rather
        than over a ``GF(2)`` matrix so that the object being evaluated is the one the stream
        produced, and the arithmetic lowering below can be read against it line by line.
        """
        if not 0 <= x < (1 << self.n_vars):
            raise ValueError(f"input {x} outside the map's {self.n_vars}-variable register")
        out = 0
        set_bits = [i for i in range(self.n_vars) if (x >> i) & 1]
        for e in range(self.n_outputs):
            acc = self._const[e] ^ (bin(self._lin[e] & x).count("1") & 1)
            for i in set_bits:
                acc ^= bin(self._rows[e][i] & x).count("1") & 1
            if acc:
                out |= 1 << e
        return out

    def _draw_secret(self) -> int:
        """The secret whose image is the target, drawn from a derived seed.

        The seed is derived from the description of the map — its mode, its variable count, its
        equation count, the caller's seed — so a spec rebuilt from the same description is the same
        problem, and the report's ``target`` is a fact about that problem rather than about the
        process that built it.
        """
        parts = ("key_map", self.mode.value, self.n_vars, self.n_outputs, self.seed)
        if self.seeds is not None:
            return int(self.seeds.rng(*parts).integers(0, 1 << self.n_vars))
        return int(rng_for(derive_seed(*parts)).integers(0, 1 << self.n_vars))

    def variable_terms(self, e: int) -> dict[str, int]:
        """The size of equation ``e`` as a gate network: linear terms, monomials, constant.

        Every monomial is one Toffoli and every linear term is one controlled X, so this is the
        lowering's cost read off the equation rather than counted from a built circuit — and the two
        are asserted equal by the tests, which is what keeps a cost model attached to a circuit.
        """
        return {
            "linear_terms": bin(self._lin[e]).count("1"),
            "monomials": sum(bin(row).count("1") for row in self._rows[e]),
            "constant": self._const[e],
        }

    # -- the interface --------------------------------------------------------------------------

    def search_width(self) -> int:
        return self.n_vars

    def marked_set(self) -> frozenset[int]:
        return self._marked

    def ancilla_width(self, lowering: Lowering) -> int:
        """One work qubit for the lookup table, one per equation for the compiled lowering.

        The truth-table lowering never evaluates the map: it writes the marked set out as
        multi-controlled X gates, and one qubit carries the answer. The arithmetic lowering needs a
        work qubit per output bit, because each equation's value has to be held somewhere before the
        flag can take the conjunction over them. That difference is why the two widths are stated
        separately rather than derived from a single formula.
        """
        if lowering is Lowering.TRUTH_TABLE:
            return 1
        if lowering is Lowering.ARITHMETIC:
            return self.n_outputs
        raise ValueError(f"unknown lowering {lowering!r}")

    def build_predicate(self, lowering: Lowering) -> GateList:
        if lowering is Lowering.TRUTH_TABLE:
            return self._build_lookup()
        if lowering is Lowering.ARITHMETIC:
            return self._build_compiled()
        raise ValueError(f"unknown lowering {lowering!r}")

    # -- the two lowerings ----------------------------------------------------------------------

    def _build_lookup(self) -> GateList:
        """The marked set as gates, its answer in one work qubit, then the flag.

        The base class's build already emits the conjugations and the multi-controlled X per marked
        state; the extra qubit is where the relation's answer is kept before the flag is given it.
        At a single equation this is about half the register's states — half of them exactly, less
        the ``2^(n/2 - 1)``-ish excess a quadratic form's zero set carries, so the fraction is 0.625
        down to 0.375 at six variables and inside a few thousandths of 0.5 by sixteen. That is a
        real property of a one-equation map rather than a defect of the writing: Grover over a
        half-marked register has nothing to amplify, and the report says so through
        ``marked_fraction`` instead of leaving a caller to find it from a flat curve.
        """
        n = self.search_width()
        answered = self._build_truth_table()  # n + 1 qubits, the answer in qubit n
        gl = GateList(n + 2, list(answered.gates), label=f"{self.name}:truth_table")
        gl.append(GateName.CX, n, n + 1)
        return gl

    def _build_compiled(self) -> GateList:
        """The map compiled: one quadratic form per output bit, then the conjunction into the flag.

        Each equation becomes its constant into the work qubit, one controlled X per set linear
        coefficient, and one Toffoli per monomial ``x_i x_j`` with ``i < j`` — the upper triangle the
        corpus stores, so no term is counted twice and none is missed. The work qubit is then
        conjugated where the target bit is clear, so that it reads 1 exactly when that equation
        agrees with the target, and one multi-controlled X over the work register puts the
        conjunction into the flag.

        Nothing is uncomputed. The work register is left holding the map's output, which is what the
        sandwich contract allows and what the inverse pass restores.
        """
        n = self.search_width()
        work = list(range(n, n + self.n_outputs))
        flag = n + self.n_outputs
        gl = GateList(n + self.n_outputs + 1, label=f"{self.name}:arithmetic")

        for e in range(self.n_outputs):
            work_bit = work[e]
            if self._const[e]:
                gl.append(GateName.X, work_bit)
            for i in range(n):
                if (self._lin[e] >> i) & 1:
                    gl.append(GateName.CX, i, work_bit)
                row = self._rows[e][i]
                for j in range(i + 1, n):
                    if (row >> j) & 1:
                        gl.append(GateName.CCX, i, j, work_bit)
            if not (self._target >> e) & 1:
                gl.append(GateName.X, work_bit)  # now reads "this equation agrees with the target"

        multi_controlled_x(gl, tuple(work), flag)
        return gl

    # -- reports --------------------------------------------------------------------------------

    def report(self) -> dict:
        """The spec's facts, with the map's shape and the lowering's cost attached.

        The base :meth:`describe` is the shape every spec reports. What is added here is what a
        reader needs to place the numbers: which register the search was over, how far the map
        expands, and what one equation costs as gates — because the extrapolation is about that
        cost, and a cost quoted without the equation it came from cannot be extrapolated.
        """
        out = self.describe()
        out.update(
            {
                "mode": self.mode.value,
                "n": self.n,
                "n_variables": self.n_vars,
                "n_outputs": self.n_outputs,
                "target": self._target,
                "secret": self._secret,
                "seed": self.seed.hex(),
                "work_qubits_truth_table": 1,
                "work_qubits_arithmetic": self.n_outputs,
                "equation_cost_per_output": self.variable_terms(0),
            }
        )
        return out
