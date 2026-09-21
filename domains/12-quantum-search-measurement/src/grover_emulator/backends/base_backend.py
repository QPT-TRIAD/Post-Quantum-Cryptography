"""What every engine in this project has to be, and the two things none of them may do.

**A run that would not fit in memory is refused, never attempted.** The host this project is
developed on has 4 GiB of swap and, at the time of writing, 3.1 GiB of it already in use. On such a
machine a simulation that overshoots does not slow down — it swaps, and every other process on the
box slows down with it. There is no version of that failure that ends in a useful number, so the
budget is checked *before* the engine is constructed and the refusal is an exception carrying the
estimate, the ceiling, and the kernel's own ``MemAvailable``. :meth:`QuantumBackend.exceeds_ram_budget`
answers the question; :meth:`QuantumBackend.require_within_budget` refuses, and every engine in this
package calls the latter as its first statement.

**Every metric comes from the IR.** ``toffoli_count``, ``ir_depth`` and ``t_count`` are read from
the :class:`~grover_emulator.circuits.ir.GateList` through :func:`ir_metrics`, which is the only
place in this package that produces them. A framework's own ``depth()`` or ``count_ops()`` counts
*that framework's* decomposition of the circuit — the API probe measured the two disagreeing — so
framework-side numbers are recorded under :attr:`BackendResult.framework` and are never compared to
the IR's. :meth:`BackendResult.__post_init__` refuses a result whose metrics are missing any of the
three, which makes "the accounting came from the IR" a machine-checked precondition rather than a
convention.

**Every statevector this package returns is in the project's qubit convention**: qubit ``q``
carries bit ``q``, as in :mod:`grover_emulator.circuits.ir`. Measured, not assumed: Aer already
indexes that way, while cirq and quimb both put the *first* qubit in the most significant position.
The conversion happens once per engine, is named, and is asserted by test — the same treatment the
IR gives its own little-endian convention.
"""

from __future__ import annotations

import secrets
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ..circuits.ir import GateList
from ..utils.seeding import rng_for

__all__ = [
    "BackendError",
    "RamBudgetExceeded",
    "MEMINFO_PATH",
    "MEM_AVAILABLE",
    "available_bytes",
    "memory_snapshot",
    "statevector_bytes",
    "ir_metrics",
    "from_most_significant_first",
    "sample_statevector",
    "BackendResult",
    "QuantumBackend",
]

MEMINFO_PATH = Path("/proc/meminfo")
"""Where the kernel's own accounting lives. Overridable so a test can drive the reader with a fixed
file instead of the machine it happens to be running on."""

MEM_AVAILABLE = "memavailable"
"""The key :func:`memory_snapshot` produces for the kernel's ``MemAvailable`` line.

Named once, because the spelling is not the obvious one: the kernel writes ``MemAvailable`` and the
reader lowercases the label without inserting an underscore, so the key is ``memavailable`` and not
``mem_available``. A caller that guesses ``mem_available`` gets ``None`` from a snapshot that has the
number in it and falls into the "unknown" branch — from which the estimate-vs-machine warning in
:func:`~grover_emulator.backends.backend_selector.run_selected_backend` silently never fires, and
:class:`RamBudgetExceeded` silently drops the kernel's number from a message that promises it.
"""

_COMPLEX128_BYTES = 16
"""Bytes per amplitude of a double-precision complex statevector, which is what Aer and numpy hold."""


class BackendError(RuntimeError):
    """An engine could not run the circuit it was handed."""


class RamBudgetExceeded(BackendError):
    """A run was refused because its estimate exceeds the configured ceiling.

    Carries the numbers as attributes as well as in the message, so a sweep can record the refusal
    as a row — estimate, ceiling, and what the kernel said was available — rather than as a string
    nobody can aggregate.
    """

    def __init__(
        self,
        backend: str,
        n_qubits: int,
        estimate_bytes: int,
        budget_bytes: int,
        meminfo: dict[str, int] | None = None,
        detail: str = "",
    ):
        self.backend = backend
        self.n_qubits = n_qubits
        self.estimate_bytes = estimate_bytes
        self.budget_bytes = budget_bytes
        self.meminfo = dict(meminfo or {})
        available = available_bytes(self.meminfo)
        tail = (
            f"; the kernel reports {format_bytes(available)} available"
            if available is not None
            else ""
        )
        super().__init__(
            f"{backend} refuses {n_qubits} qubits: the run needs {format_bytes(estimate_bytes)}, "
            f"over the {format_bytes(budget_bytes)} ceiling{tail}.{detail} The budget is a refusal "
            "rather than a hint: on a machine with swap already in use, a simulation that "
            "overshoots thrashes instead of merely running slowly."
        )


def format_bytes(value: int) -> str:
    """A byte count in the largest binary unit that keeps it readable, to one decimal place."""
    step = 1024.0
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"):
        if size < step or unit == "EiB":
            return f"{int(value)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= step
    raise AssertionError("unreachable")  # pragma: no cover


def memory_snapshot(path: str | Path = MEMINFO_PATH) -> dict[str, int]:
    """The kernel's memory numbers, in bytes, or an empty mapping where there is no ``/proc``.

    ``MemAvailable`` is the number this package cares about: it is the kernel's estimate of what a
    new allocation can use without pushing the machine into swap, which is precisely the question a
    budget check is asking. ``MemFree`` answers a different question — page cache is reclaimable and
    is counted as used — and reading it would overstate the pressure on any machine that has been up
    for a while.

    An unreadable file is an empty mapping rather than an exception: the snapshot is context for a
    log line and a field in a result, and a diagnostic that can fail a run is worse than one that is
    occasionally silent.
    """
    out: dict[str, int] = {}
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2 or not parts[1].isdigit():
            continue
        key = parts[0].rstrip(":").lower()
        unit = 1024 if len(parts) > 2 and parts[2].lower() == "kb" else 1
        out[key] = int(parts[1]) * unit
    return out


def available_bytes(snapshot: dict[str, int]) -> int | None:
    """The kernel's ``MemAvailable`` from a snapshot, or ``None`` where the snapshot has no answer.

    Every caller that wants this number wants it for the same reason — to compare it against an
    estimate — and each of them would otherwise spell the key out again and be wrong in the same way.
    """
    return snapshot.get(MEM_AVAILABLE)


def statevector_bytes(
    n_qubits: int,
    *,
    bytes_per_amplitude: int = _COMPLEX128_BYTES,
    working_copies: float = 2.0,
) -> int:
    """Bytes to hold ``2**n_qubits`` amplitudes, times the working copies the engine may hold.

    Integer arithmetic throughout. A float here would round a ``2**50`` amplitude count into a
    number that no longer says what the circuit needs, and the budget decision is a comparison
    against that number.
    """
    if n_qubits < 0:
        raise ValueError(f"n_qubits must be non-negative, got {n_qubits}")
    if bytes_per_amplitude < 1:
        raise ValueError(f"bytes_per_amplitude must be positive, got {bytes_per_amplitude}")
    if working_copies < 1.0:
        raise ValueError(f"working_copies must be at least 1, got {working_copies}")
    return int((1 << n_qubits) * bytes_per_amplitude * working_copies)


def ir_metrics(gl: GateList) -> dict[str, Any]:
    """The accounting for a gate list, read from the IR and nothing else.

    ``toffoli_count``, ``t_count`` and ``ir_depth`` are the three the project reports everywhere.
    ``t_count`` is the explicit T and T-dagger count, with ``t_count_with_toffolis`` alongside it
    rather than in place of it, because the 7-T Toffoli decomposition is an assumption and a report
    that quotes one number without saying which it is is not reporting a measurement.
    """
    d = gl.to_dict()
    return {
        "label": d["label"],
        "num_qubits": d["num_qubits"],
        "gate_count": d["gate_count"],
        "counts": d["counts"],
        "toffoli_count": d["toffoli_count"],
        "t_count": d["t_count_explicit"],
        "t_count_with_toffolis": d["t_count_with_toffolis"],
        "ir_depth": d["ir_depth"],
        "ancilla_peak": d["ancilla_peak"],
        "classically_simulable": d["classically_simulable"],
    }


def from_most_significant_first(statevector: np.ndarray, num_qubits: int) -> np.ndarray:
    """Re-order a statevector whose *first* qubit is its most significant bit.

    Cirq and quimb both write a statevector that way: an X on the first qubit of a three-qubit
    circuit leaves the amplitude at index 4, not at index 1. Aer writes it the other way round, and
    the IR's convention is Aer's — qubit ``q`` carries bit ``q``. Without this conversion the two
    engines agree on every circuit's *content* and disagree on every circuit's *indices*, and the
    symptom is a cross-validation that reports a 0.48 overlap on circuits that are in fact equal.

    The transposition is its own inverse, so a caller that has already converted and calls again
    gets the original back. That is a property of the operation and not a licence to be unsure of
    which convention an array is in: each engine's conversion is applied exactly once, at the point
    the engine's output is read.
    """
    vec = np.asarray(statevector)
    if vec.ndim != 1 or vec.shape[0] != (1 << num_qubits):
        raise BackendError(
            f"expected {1 << num_qubits} amplitudes for {num_qubits} qubits, got shape {vec.shape}"
        )
    if num_qubits <= 1:
        return vec
    axes = tuple(reversed(range(num_qubits)))
    return vec.reshape((2,) * num_qubits).transpose(axes).reshape(-1)


def sample_statevector(statevector: np.ndarray, shots: int, seed: int) -> dict[int, int]:
    """Sample basis-state indices from a statevector, seeded through :mod:`grover_emulator.utils.seeding`.

    Exact in the sense that matters here: the sampling distribution is ``|amplitude|**2`` to the
    precision of the vector, and the draw is a single seeded inverse-CDF over it. This is what an
    engine without a native sampler uses, and it is also the check a native sampler is compared
    against — a sampler and a distribution that disagree are a bug in one of the two, and there is
    no third thing that could be wrong.
    """
    if shots < 1:
        raise ValueError(f"shots must be at least 1, got {shots}")
    vec = np.asarray(statevector, dtype=complex)
    probabilities = np.abs(vec) ** 2
    total = float(probabilities.sum())
    if total <= 0.0:
        raise BackendError("the statevector is all zeros; there is nothing to sample")
    cumulative = np.cumsum(probabilities / total)
    # The last entry of a floating-point cumulative sum can land just below 1.0, which would make a
    # draw of exactly 1.0 fall off the end. Pinning it costs nothing and removes the case.
    cumulative[-1] = 1.0
    draws = rng_for(seed).random(shots)
    indices = np.searchsorted(cumulative, draws, side="right")
    values, counts = np.unique(indices, return_counts=True)
    return {int(v): int(c) for v, c in zip(values, counts)}


@dataclass(frozen=True, slots=True, eq=False)
class BackendResult:
    """One engine's answer, with the accounting that says what circuit produced it.

    ``eq`` is off deliberately. A dataclass comparison would compare the statevector arrays
    element-wise and hand the caller a numpy array where a boolean was expected; agreement between
    two engines is a question about physics and is answered by
    :func:`grover_emulator.utils.validation.assert_backend_agreement`, which is written to answer it
    up to a global phase rather than entry by entry.

    Attributes:
        backend: the engine's name, the same string a configuration's ``backend.preference`` uses.
        label: the gate list's own label, so a result can be traced back to the circuit counted.
        num_qubits: the IR width. Never the framework's — the two are asserted equal at compile.
        method: ``"statevector"`` or ``"sampled"``.
        statevector: amplitudes in the project's convention, or None for a sampled-only run.
        counts: basis index -> number of shots, or None. Index ``i`` is the register value, per the
            IR's little-endian convention.
        shots: shots drawn; 0 for a statevector run.
        metrics: :func:`ir_metrics` of the circuit that ran.
        framework: engine-side facts — versions, timings, the framework's own circuit depth. Kept
            apart from ``metrics`` because these describe the engine, not the circuit.
        estimate_bytes: what the run was budgeted at, recorded whether or not it was close.
        memory_before: the kernel's snapshot taken immediately before execution.
        elapsed_s: wall time inside the engine, excluding compilation.
    """

    backend: str
    label: str
    num_qubits: int
    method: str
    statevector: np.ndarray | None
    counts: dict[int, int] | None
    shots: int
    metrics: dict[str, Any]
    framework: dict[str, Any]
    estimate_bytes: int
    memory_before: dict[str, int]
    elapsed_s: float

    def __post_init__(self) -> None:
        if self.num_qubits < 1:
            raise ValueError(f"num_qubits must be at least 1, got {self.num_qubits}")
        if self.method not in ("statevector", "sampled"):
            raise ValueError(f"unknown method {self.method!r}")
        missing = {"toffoli_count", "ir_depth", "t_count"} - set(self.metrics)
        if missing:
            raise ValueError(
                f"metrics are missing {sorted(missing)}; the accounting for a run comes from the "
                "gate list's IR and nowhere else"
            )
        if self.statevector is None and self.counts is None:
            raise ValueError("a result carries a statevector, counts, or both — not neither")
        if self.statevector is not None:
            vec = np.asarray(self.statevector)
            if vec.ndim != 1 or vec.shape[0] != (1 << self.num_qubits):
                raise ValueError(
                    f"statevector has shape {vec.shape}, expected {1 << self.num_qubits} amplitudes"
                )
            if not np.iscomplexobj(vec):
                raise ValueError("a statevector is complex; an array of reals is a bug upstream")
        if self.counts is not None:
            if self.shots < 1:
                raise ValueError("a sampled result must record at least one shot")
            if sum(self.counts.values()) != self.shots:
                raise ValueError(
                    f"counts sum to {sum(self.counts.values())}, not the {self.shots} shots claimed"
                )
            out_of_range = [i for i in self.counts if not 0 <= i < (1 << self.num_qubits)]
            if out_of_range:
                raise ValueError(
                    f"counts contain basis index {out_of_range[0]}, outside a "
                    f"{self.num_qubits}-qubit register"
                )

    # -- derived views ---------------------------------------------------------------------------

    def probabilities(self) -> np.ndarray:
        """``|amplitude|**2`` for every basis state. Requires a statevector."""
        if self.statevector is None:
            raise BackendError(f"{self.backend} produced counts only; there is no statevector")
        return np.abs(np.asarray(self.statevector, dtype=complex)) ** 2

    def measured_probabilities(self) -> dict[int, float]:
        """The sampled frequency of every observed basis state. Requires counts."""
        if self.counts is None:
            raise BackendError(f"{self.backend} produced no counts to measure frequencies from")
        return {index: count / self.shots for index, count in self.counts.items()}

    def to_dict(self) -> dict[str, Any]:
        """A JSON-safe form, for a run's record.

        The statevector is summarised rather than dumped: a record carrying 2**24 amplitudes is a
        record nobody diffs. What is kept is its length, its norm — which is 1.0 for a unitary
        circuit and is therefore a check — and the eight heaviest outcomes, which is what a reader
        compares against a theoretical distribution by eye.
        """
        summary = None
        if self.statevector is not None:
            probabilities = self.probabilities()
            heaviest = np.argsort(probabilities)[::-1][:8]
            summary = {
                "length": int(probabilities.size),
                "norm": float(np.linalg.norm(np.asarray(self.statevector))),
                "top_outcomes": [
                    {"index": int(i), "probability": float(probabilities[i])} for i in heaviest
                ],
            }
        return {
            "backend": self.backend,
            "label": self.label,
            "num_qubits": self.num_qubits,
            "method": self.method,
            "shots": self.shots,
            "estimate_bytes": int(self.estimate_bytes),
            "elapsed_s": float(self.elapsed_s),
            "metrics": self.metrics,
            "framework": self.framework,
            "memory_before": {k: int(v) for k, v in self.memory_before.items()},
            "statevector": summary,
            "counts": None if self.counts is None else {str(k): int(v) for k, v in sorted(self.counts.items())},
        }


class QuantumBackend(ABC):
    """One engine, with the budget it is allowed and the refusal it owes when the run exceeds it.

    Subclasses implement :meth:`estimate_bytes` and :meth:`run_statevector`, and may override
    :meth:`run_sampled` when their engine has a native sampler worth using. They do not implement
    their own budget checks: :meth:`require_within_budget` is called by every run entry point here,
    so an engine cannot add a code path that skips it.
    """

    name: str = "backend"
    """Engine name. Matches the string in ``backend.preference`` and in the selector's registry."""

    requires: tuple[str, ...] = ()
    """The modules this engine's framework needs, for the selector's availability check.

    Declared here rather than discovered by the selector, because only the engine knows which
    packages it actually drives: importing an engine module is not evidence that the simulator behind
    it can be imported, since every framework import in this package happens inside the method that
    needs it. Without this, "the engine is available" would mean "a file exists", and a preference
    list would resolve to an engine that raises on its first run.
    """

    bytes_per_amplitude: int = _COMPLEX128_BYTES
    """What this engine holds per amplitude. Measured per engine, not assumed: qsim's CPU state
    vector is single precision, so it holds half of what Aer holds and is half as accurate."""

    def __init__(
        self,
        ram_budget_gb: float = 6.0,
        *,
        working_copies: float = 2.0,
        meminfo_path: str | Path = MEMINFO_PATH,
    ):
        if ram_budget_gb <= 0:
            raise ValueError(f"ram_budget_gb must be positive, got {ram_budget_gb}")
        self.ram_budget_gb = float(ram_budget_gb)
        self.budget_bytes = int(self.ram_budget_gb * (1 << 30))
        self.working_copies = float(working_copies)
        self.meminfo_path = Path(meminfo_path)

    # -- budget ----------------------------------------------------------------------------------

    @abstractmethod
    def estimate_bytes(self, n_qubits: int) -> int:
        """Bytes this engine would allocate to run an ``n_qubits`` circuit."""

    def estimate_bytes_for(self, gl: GateList) -> int:
        """The circuit-aware estimate, which is the width-only one unless an engine knows better.

        A tensor-network engine does know better: its cost is set by the contraction it finds, not
        by the width, so it overrides this. Everything else inherits a bound that depends only on
        the width, which is the honest thing to report when the width is all that is known.
        """
        return self.estimate_bytes(gl.num_qubits)

    def exceeds_ram_budget(self, n_qubits: int) -> bool:
        """Whether an ``n_qubits`` run would exceed this engine's ceiling. No allocation happens."""
        return self.estimate_bytes(n_qubits) > self.budget_bytes

    def require_within_budget(self, n_qubits: int) -> int:
        """Refuse an over-budget width, with the numbers, before anything is constructed.

        Returns the estimate when the run is allowed, so a caller can record what the run was
        budgeted at on the way through.
        """
        estimate = self.estimate_bytes(n_qubits)
        if estimate > self.budget_bytes:
            raise RamBudgetExceeded(
                self.name, n_qubits, estimate, self.budget_bytes, self.memory_before()
            )
        return estimate

    def memory_before(self) -> dict[str, int]:
        """The kernel's memory snapshot, as of this call."""
        return memory_snapshot(self.meminfo_path)

    def describe(self) -> dict[str, Any]:
        """Scalar facts about the engine, for a run's record."""
        return {
            "name": self.name,
            "ram_budget_gb": self.ram_budget_gb,
            "budget_bytes": self.budget_bytes,
            "working_copies": self.working_copies,
            "bytes_per_amplitude": self.bytes_per_amplitude,
        }

    # -- running ---------------------------------------------------------------------------------

    @abstractmethod
    def run_statevector(self, gl: GateList, *, seed: int | None = None) -> BackendResult:
        """Execute the circuit and return its exact statevector."""

    def run_sampled(self, gl: GateList, *, shots: int, seed: int | None = None) -> BackendResult:
        """Execute the circuit and return ``shots`` measurement outcomes.

        The default route is exact: the statevector, then a seeded inverse-CDF draw from its
        probabilities. An engine with a native sampler overrides this — Aer and qsim both do — and
        the check that the two routes agree is in the cross-validation test rather than in a
        comment, because a sampler is exactly the sort of component that is wrong quietly.

        ``seed=None`` draws from the operating system, which is allowed and is recorded: the failure
        mode being avoided is not a random draw, it is a random draw nobody wrote down.
        """
        if shots < 1:
            raise ValueError(f"shots must be at least 1, got {shots}")
        drawn = secrets.randbits(64) if seed is None else int(seed)
        statevector_result = self.run_statevector(gl, seed=drawn)
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

    def run(self, gl: GateList, *, shots: int | None = None, seed: int | None = None) -> BackendResult:
        """Statevector when ``shots`` is None, sampled otherwise. One call, one budget check."""
        if shots is None:
            return self.run_statevector(gl, seed=seed)
        return self.run_sampled(gl, shots=shots, seed=seed)

    # -- helpers for subclasses ------------------------------------------------------------------

    def _require_compiled_width(self, gl: GateList, compiled_num_qubits: int) -> None:
        """The framework's circuit must be exactly as wide as the IR declared.

        A framework gate that brings its own ancillas makes a framework circuit wider than the gate
        list, which would let a budget check pass while the engine allocated something else
        entirely. The probe found ``WeightedSumGate`` doing exactly that, so the check is asserted
        rather than trusted.
        """
        if compiled_num_qubits != gl.num_qubits:
            raise BackendError(
                f"{self.name}: the compiled circuit is {compiled_num_qubits} qubits wide but the IR "
                f"declares {gl.num_qubits}; a framework object has allocated qubits of its own and "
                "the accounting no longer describes what would run"
            )

    def _timed(self) -> float:
        """A monotonic clock reading, so elapsed time is measured and never computed from a date."""
        return time.perf_counter()
