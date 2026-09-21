"""The engine that contracts instead of iterating: quimb for the tensors, cotengra for the plan.

Every other engine here multiplies a state vector by one gate at a time, so its cost is ``2**n`` per
gate and its memory is ``2**n`` amplitudes no matter what the circuit looks like. This one turns the
circuit into a tensor network and contracts it as one object. The memory it needs and the work it
does are then properties of the *contraction* — the widest tensor the plan has to hold and the flop
count that got there — and those are the two numbers this module reports: ``contraction_width`` and
``contraction_cost``. At width 24 the difference is not academic; at width 8 it is invisible, which is
why the cross-validation test runs the same circuits through this engine and Aer and compares.

**Four measured facts, each of which changes the code rather than a comment.**

1. **quimb writes the first qubit most significant, like cirq.** Measured by preparing a single X on
   qubit 0 of a three-qubit circuit and reading the index back. Every statevector leaving this module
   goes through :func:`~grover_emulator.backends.base_backend.from_most_significant_first`.

2. **A multi-controlled gate is not a dense matrix here, and that is the whole point.** quimb applies
   ``X``/``Z`` with ``controls=`` as a *hyper* tensor network — one tensor per wire plus a
   controlled-gate construction of ``O(k)`` tensors, rather than a ``2**(k+1)``-squared matrix.
   Measured on a 9-qubit Grover circuit: 100 tensors, built in 0.02 s. The alternative route —
   transpiling to ``u``/``cx``/``ccx`` and applying each operation's matrix — measured 25,000
   operations, 35,217 tensors, and 25 s for the *same circuit*, because a 12-control phase gate
   decomposes into thousands of two-qubit operations. The hyper network is what keeps a 12-control
   oracle at all affordable, and it is why the gate lowering below never decomposes anything.

3. **The contraction plan has to come from the contraction call.** cotengra's ``ContractionTree``
   carries the circuit's indices in its own single-character alphabet, and a tree built by a route
   other than the one the contract call uses is mapped back against a different index layout. This
   was not a guess: a tree built with ``TensorNetwork.contraction_tree`` and then handed to
   ``contract(..., output_inds=...)`` returned a statevector of norm 1 whose overlap with Aer was
   ``0.0496`` — a silently wrong answer with nothing in it to raise. Asking the contract call itself
   for the plan (``get="tree"``) and contracting with *that* gives an overlap of ``1.000000000000``
   on the same circuit. So the plan is obtained once, from :meth:`TensorNetworkBackend._plan`, and
   the tree that is reported is the tree that runs.

4. **quimb's raw-matrix gate path reads a matrix's first axis as the *last* site.** ``apply_gate(U,
   *sites)`` on a two-qubit matrix behaves as if the control were ``sites[1]``; applying with the
   site list reversed puts the first axis on ``sites[0]``, which is the IR's convention. Measured by
   comparing a controlled-X written this way against Aer. Only the ``perm`` gate takes this path —
   every other gate in the IR has a named quimb equivalent — and the test suite asserts the resulting
   convention rather than trusting this paragraph.

5. **The plan is a heuristic search that does not reproduce, and the engine records it instead of
   promising it.** cotengra 0.8.2's ``HyperOptimizer`` has no ``seed`` parameter at all — an unknown
   keyword is accepted and silently dropped into the optimizer library's options — and the randomness
   is deeper than a sampler anyway: its ``greedy`` trial jitters the size dictionary through
   ``jitter_dict(size_dict, random_strength)`` with no seed argument, and its ``labels`` trial
   shuffles its site list off a process-global generator, so the trials draw from an RNG that no
   argument reaches — a seed handed to this engine reaches the sampler (two searches with the same
   seed proposed the same settings in the same order; a different seed proposed different ones) and
   stops there. Measured on the 11-qubit circuit above, five default searches found widths
   ``14, 14, 13, 14, 14`` at contraction costs from ``4.96e+05`` to ``8.80e+05``. What that costs this
   project is nothing about the answer and something about the record: a contraction is exact
   whatever the order, and those five statevectors agree with Aer to ``2.1e-15``–``2.9e-15`` and with
   each other to ``3.8e-15``. So the plan this engine used — width, cost, sliced indices, methods,
   repeats — is a field of every result (see :meth:`run_statevector`), and a caller who needs the
   *plan* to stand still can supply one: ``optimizer`` takes anything cotengra's ``optimize=``
   accepts, and a ``HyperOptimizer`` built with ``methods=["greedy"]``, ``max_repeats=1`` and
   ``constants={"greedy": {"random_strength": 0.0, "temperature": 0.0, "costmod": 1.0}}`` was measured
   to give the same width (16) and the same cost (``1.36e+06``) in three separate processes — wider
   than the default search finds, which is the trade a pinned plan makes.

**What is refused.** The engine returns a statevector, so it must materialize ``2**n`` amplitudes,
and the width-only estimate is that array plus one working copy. A circuit whose *plan* would need a
wider intermediate than the budget allows is refused too, after the plan is computed and before any
contraction starts — the plan is cheap to compute and says exactly what the contraction would hold.

**What it does not save, measured.** A contraction is cheaper in *work* than a gate-by-gate
iteration, and it is not cheaper in memory at any width where a statevector fits — because the answer
*is* a statevector. Measured at width 20 (16 MiB of amplitudes) in a warmed-up process, peak resident
set over the run: Aer 41.7 MiB, this engine 54.9 MiB, qsim 40.2 MiB. Its own output array plus one
transposed copy plus the network of small tensors is more, not less, than the array Aer holds. Anyone
reading this engine's name and expecting the memory advantage of a tensor network should read this
paragraph first: the advantage is real only for a question narrower than the full state — one
amplitude, one expectation value, or a sampled distribution computed along the contraction — and this
engine offers none of those, because everything it returns has to be comparable, amplitude for
amplitude, with what the other two engines return.
"""

from __future__ import annotations

import secrets
from typing import Any

import numpy as np

from ..circuits.ir import Gate, GateList, GateName
from .base_backend import (
    MEMINFO_PATH,
    BackendError,
    BackendResult,
    QuantumBackend,
    RamBudgetExceeded,
    format_bytes,
    from_most_significant_first,
    ir_metrics,
    statevector_bytes,
)

__all__ = ["TensorNetworkBackend"]

_NAMED_GATES = {
    GateName.X: "X",
    GateName.H: "H",
    GateName.CX: "CX",
    GateName.CCX: "CCX",
    GateName.S: "S",
    GateName.SDG: "SDG",
    GateName.T: "T",
    GateName.TDG: "TDG",
}
"""The IR gates quimb names identically. The table is exhaustive over the IR's named gates: a gate
that is not here and is not handled explicitly below raises rather than being skipped."""

_DEFAULT_METHODS = ("greedy", "labels")
"""The path finders the plan is searched over.

Named rather than left to cotengra's defaults for two reasons. The default set asks for a
partition-based finder whose dependency is absent from this checkout, and cotengra warns about the
substitution once per process — a warning nobody reads. And the pair is part of the record: it is
reported with every result, so a plan written down can say what was searched. What it cannot say is
what the search will return next time; see fact 5 at the top of this module.
"""

_DEFAULT_MAX_REPEATS = 4
"""How many times each finder is allowed to run before the best plan so far is taken.

Measured on the 13-qubit scaled QLWR circuit (255 tensors), one run at each setting:

    repeats   search time   contraction width   contraction cost
    1         0.66 s        19                  2.0e+07
    2         2.89 s        13                  5.5e+05
    4         6.28 s        13                  5.8e+05

One run of a search that does not reproduce (fact 5 above) is a sample and not a law, so these
numbers are indicative rather than exact — but the shape is not: a single pass is 40 times *cheaper*
in search and 64 times more expensive in memory, because the width it finds is six qubits wider, and
width is ``2**w`` bytes of intermediate tensor. The repeated search pays for itself the first time it
is used. Cotengra's own default is 128 repeats; four is the point on this curve where the width stops
improving.
"""


def _permutation_matrix(table) -> np.ndarray:
    """The unitary of a basis-state permutation: ``M[table[i], i] = 1``.

    The same convention the qiskit and cirq compilers use for the IR's ``perm`` gate — a table that
    sends basis state ``i`` to state ``table[i]``, indexed little-endian so that bit ``q`` of the
    index is qubit ``q``. It is stated once per lowering rather than shared because each lowering
    needs it in its own form, and the thing that keeps them from drifting is not a shared helper but
    the cross-validation test: a circuit containing a ``perm`` gate is run through three engines and
    the statevectors are compared.
    """
    size = len(table)
    matrix = np.zeros((size, size), dtype=complex)
    for src, dst in enumerate(table):
        matrix[dst, src] = 1.0
    return matrix


class TensorNetworkBackend(QuantumBackend):
    """The circuit as a tensor network, contracted along a cotengra plan."""

    name = "tensor_network"
    requires = ("quimb", "cotengra")
    bytes_per_amplitude = 16
    """Complex128: quimb's tensors are numpy arrays and a circuit with a phase gate in it is complex.
    Measured on a statevector out of this engine rather than assumed from the dtype of the input."""

    def __init__(
        self,
        ram_budget_gb: float = 6.0,
        *,
        working_copies: float = 2.0,
        max_repeats: int = _DEFAULT_MAX_REPEATS,
        methods: tuple[str, ...] = _DEFAULT_METHODS,
        optimizer: Any = None,
        meminfo_path: Any = MEMINFO_PATH,
    ):
        super().__init__(ram_budget_gb, working_copies=working_copies, meminfo_path=meminfo_path)
        if max_repeats < 1:
            raise ValueError(f"max_repeats must be at least 1, got {max_repeats}")
        if not methods:
            raise ValueError("at least one path-finding method is required to plan a contraction")
        self.max_repeats = int(max_repeats)
        self.methods = tuple(methods)
        self.optimizer = optimizer
        """Anything cotengra's ``optimize=`` accepts, or ``None`` for this engine's own search.

        The default search is a hyper-optimized one because it finds the narrower plans, and it does
        not reproduce (fact 5 in the module docstring). A caller who needs the *plan* to be a
        property of the circuit rather than of the run supplies one here — a pinned
        ``HyperOptimizer``, a plain ``"greedy"``, or a plan replayed from an earlier run — and gets
        the same width and cost every time at whatever quality that choice costs. It is also how the
        refusal path is exercised against a plan that does not move: see
        ``tests/test_backends.py::test_the_tensor_network_refuses_a_plan_wider_than_its_budget``.
        """

    # -- budget ----------------------------------------------------------------------------------

    def estimate_bytes(self, n_qubits: int) -> int:
        """The width-only estimate: the statevector this engine returns, plus one working copy.

        It returns a full statevector, so ``2**n`` amplitudes are materialized whatever the
        contraction costs — the plan can make the *work* smaller, not the answer. What the plan
        changes is the ceiling, and that is checked separately once the plan exists.
        """
        return statevector_bytes(
            n_qubits,
            bytes_per_amplitude=self.bytes_per_amplitude,
            working_copies=self.working_copies,
        )

    def describe(self) -> dict[str, Any]:
        return dict(
            super().describe(),
            method="contraction",
            max_repeats=self.max_repeats,
            methods=list(self.methods),
            plan_optimizer=self._optimizer_name(),
        )

    def _optimizer_name(self) -> str:
        """What the plan search is, as a string a record can carry.

        The default search names itself ``"hyper"`` rather than the class name, because "HyperOptimizer"
        in a row says nothing about what was searched while the methods and repeat count beside it do.
        """
        if self.optimizer is None:
            return "hyper"
        if isinstance(self.optimizer, str):
            return self.optimizer
        return type(self.optimizer).__name__

    # -- lowering --------------------------------------------------------------------------------

    def _build(self, gl: GateList):
        """The IR as a quimb circuit, one ``apply_gate`` per IR gate, in IR order.

        Nothing is transpiled and nothing is decomposed. Each gate goes in as the gate it is —
        including the multi-controlled ones, which quimb represents as a small tensor network rather
        than as a dense operator, and including ``perm``, which has no named equivalent and goes in as
        its matrix with the site order reversed (measured; see the module docstring).
        """
        import quimb.tensor as qtn

        circuit = qtn.Circuit(gl.num_qubits)
        for gate in gl.gates:
            circuit = self._apply(circuit, gate)
        return circuit

    @staticmethod
    def _apply(circuit, gate: Gate):
        qubits = gate.qubits
        if gate.name in _NAMED_GATES:
            circuit.apply_gate(_NAMED_GATES[gate.name], *qubits)
        elif gate.name is GateName.MCX:
            # Controls first, target last — the IR's convention, the same one the qiskit and cirq
            # lowerings use, and the reason this is not simply a matrix.
            circuit.apply_gate("X", qubits[-1], controls=qubits[:-1])
        elif gate.name is GateName.MCZ:
            if len(qubits) == 1:
                circuit.apply_gate("Z", qubits[0])
            else:
                circuit.apply_gate("Z", qubits[-1], controls=qubits[:-1])
        elif gate.name is GateName.PERM:
            matrix = _permutation_matrix(gate.params[0])
            if matrix.shape[0] != (1 << len(qubits)):
                raise BackendError(
                    f"a perm gate on {len(qubits)} qubits carries a {matrix.shape[0]}x"
                    f"{matrix.shape[1]} matrix; the two disagree about the gate's width"
                )
            circuit.apply_gate(matrix, *reversed(qubits))
        else:  # pragma: no cover - the enum is closed
            raise BackendError(f"{TensorNetworkBackend.name} has no lowering for {gate.name!r}")
        return circuit

    # -- planning --------------------------------------------------------------------------------

    def _plan(self, network, output_inds: tuple[str, ...], seed: int | None):
        """The contraction tree this engine will execute, from the call that will execute it.

        ``get="tree"`` returns the tree the contraction call built for *this* output and index
        layout. A tree obtained any other way carries cotengra's own single-character index alphabet
        and is mapped back against a different layout — measured on a nine-qubit circuit as an
        overlap of 0.0496 against Aer, with no exception raised, which is why the plan is not
        constructed by hand anywhere in this module.

        ``seed`` is handed to the search but is not a reproducibility guarantee, and this docstring
        says so rather than implying one. ``HyperOptimizer`` has no ``seed`` parameter at all, so the
        value travels into the optimizer library's own options — where, measured on a 7-qubit
        circuit, it does reach the sampler that proposes hyper-parameters: two searches with the same
        seed proposed the same four ``(method, params)`` settings in the same order, and a search with
        a different seed proposed different ones. What no argument reaches is the trials themselves;
        see fact 5 in the module docstring. So the plan a run used is recorded in its result, and that
        record is the claim this module makes.
        """
        import cotengra as ctg

        optimize = self.optimizer
        if optimize is None:
            optimize = ctg.HyperOptimizer(
                seed=None if seed is None else int(seed),
                max_repeats=self.max_repeats,
                progbar=False,
                methods=list(self.methods),
                # The search is single-process on purpose. cotengra's default is to parallelise trials
                # across processes, and each copy of the search carries its own copy of the graph — on
                # a host that is already into its swap file, a plan search that forks eight workers is
                # a plan search that can be killed by the kernel.
                parallel=False,
            )
        return network.contract(all, output_inds=output_inds, optimize=optimize, get="tree")

    def require_plan_within_budget(self, tree, n_qubits: int) -> int:
        """Refuse a contraction whose widest intermediate would not fit, with the numbers.

        A plan is a memory claim before it is a time claim: contracting a tree means holding the
        widest tensor on the way up, which is ``2**width`` amplitudes and is the one number that
        decides whether the run is a simulation or a swap storm. The width-only estimate passed
        before the plan was built does not know this, so it is checked here, before the first
        contraction, with the same refusal every other engine raises.
        """
        peak = statevector_bytes(
            int(tree.contraction_width()),
            bytes_per_amplitude=self.bytes_per_amplitude,
            working_copies=self.working_copies,
        )
        if peak > self.budget_bytes:
            raise RamBudgetExceeded(
                self.name,
                n_qubits,
                peak,
                self.budget_bytes,
                self.memory_before(),
                detail=(
                    f" The contraction plan for this circuit has width "
                    f"{tree.contraction_width():.0f}, so its widest intermediate alone is "
                    f"{format_bytes(peak)}. The plan is reported either way, so a sweep can record "
                    "the width of a circuit it refused."
                ),
            )
        return peak

    # -- engine ----------------------------------------------------------------------------------

    @staticmethod
    def _versions() -> dict[str, str]:
        import cotengra
        import quimb

        return {"quimb": quimb.__version__, "cotengra": cotengra.__version__}

    def run_statevector(self, gl: GateList, *, seed: int | None = None) -> BackendResult:
        estimate = self.require_within_budget(gl.num_qubits)
        memory = self.memory_before()
        drawn = None if seed is None else int(seed)

        start = self._timed()
        circuit = self._build(gl)
        build_elapsed = self._timed() - start

        network = circuit.psi
        output_inds = tuple(network.site_ind(i) for i in range(gl.num_qubits))
        start = self._timed()
        tree = self._plan(network, output_inds, drawn)
        plan_elapsed = self._timed() - start
        self.require_plan_within_budget(tree, gl.num_qubits)

        start = self._timed()
        contracted = network.contract(all, output_inds=output_inds, optimize=tree)
        contract_elapsed = self._timed() - start

        if contracted.inds != output_inds:
            raise BackendError(
                f"the contraction returned indices {contracted.inds}, not the {output_inds} it was "
                "asked for; the amplitudes would be laid out in an order nobody asked for"
            )
        raw = np.asarray(contracted.data).reshape(-1)
        if raw.shape[0] != (1 << gl.num_qubits):
            raise BackendError(
                f"{self.name} returned {raw.shape[0]} amplitudes for {gl.num_qubits} qubits"
            )
        statevector = from_most_significant_first(raw, gl.num_qubits)

        return BackendResult(
            backend=self.name,
            label=gl.label,
            num_qubits=gl.num_qubits,
            method="statevector",
            statevector=np.asarray(statevector, dtype=complex),
            counts=None,
            shots=0,
            metrics=ir_metrics(gl),
            framework=dict(
                self._versions(),
                simulator="TensorNetwork.contract",
                engine_method="contraction",
                precision="double",
                tensor_count=len(network.tensors),
                hyper_indices=len(network.get_hyperinds(output_inds=output_inds)),
                # The plan is what this engine records instead of promising to reproduce it: two runs
                # of this circuit may report different widths (fact 5 above), and a row that says
                # which plan it ran on is a row whose memory claim can be checked afterwards.
                contraction_width=float(tree.contraction_width()),
                contraction_cost=float(tree.contraction_cost()),
                sliced_inds=len(tree.sliced_inds),
                plan_optimizer=self._optimizer_name(),
                max_repeats=self.max_repeats,
                methods=list(self.methods),
                seed=drawn,
                build_elapsed_s=build_elapsed,
                plan_elapsed_s=plan_elapsed,
                contract_elapsed_s=contract_elapsed,
                converted_from_msb_first=True,
            ),
            estimate_bytes=estimate,
            memory_before=memory,
            elapsed_s=build_elapsed + plan_elapsed + contract_elapsed,
        )

    def run_sampled(self, gl: GateList, *, shots: int, seed: int | None = None) -> BackendResult:
        """Sampling from the contracted statevector, seeded through the project's seeding module.

        There is no native sampler to prefer here. quimb can sample a circuit without ever forming
        the state, but only approximately and only along a chosen structure, and an engine's sampled
        run is compared against its own exact distribution by the cross-validation test — so the
        route that is exact is the route that is used. The draw is a single seeded inverse-CDF over
        ``|amplitude|**2`` from :func:`~grover_emulator.backends.base_backend.sample_statevector`.
        """
        if shots < 1:
            raise ValueError(f"shots must be at least 1, got {shots}")
        drawn = secrets.randbits(64) if seed is None else int(seed)
        statevector_result = self.run_statevector(gl, seed=drawn)
        from .base_backend import sample_statevector

        counts = sample_statevector(statevector_result.statevector, shots, drawn)
        return BackendResult(
            backend=self.name,
            label=gl.label,
            num_qubits=gl.num_qubits,
            method="sampled",
            statevector=None,
            counts=counts,
            shots=shots,
            metrics=statevector_result.metrics,
            framework=dict(statevector_result.framework, seed=drawn, sampled_from="statevector"),
            estimate_bytes=statevector_result.estimate_bytes,
            memory_before=statevector_result.memory_before,
            elapsed_s=statevector_result.elapsed_s,
        )
