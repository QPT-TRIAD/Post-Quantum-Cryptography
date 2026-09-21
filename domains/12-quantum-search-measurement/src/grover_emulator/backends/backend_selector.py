"""Choosing an engine for a configuration, and refusing before the machine is asked to try.

A configuration names the engines it would accept, in order. This module turns that list into one
engine, and it does it by *refusing*: an engine whose framework is not installed is not a candidate,
and an engine that would not fit in the memory budget is not a candidate either. Only when no
candidate is left does it raise, and it raises with the numbers that produced the refusal rather than
with a message about preferences.

**Why there is a selector at all, rather than a line that takes the first name.** Three engines with
three different failure modes are in play. Aer and qsim are exact but their memory is ``2**n``
amplitudes regardless of the circuit, so a faithful QLWR arithmetic oracle — 50 qubits at the
smallest instance, measured — is refused by both by a factor of thousands, and a sweep that meets
that refusal at the bottom of a 40-row table needs to know *which* engine refused and at what
estimate. The tensor-network engine is refused on a different number entirely: the width of the
contraction it found. And an engine's framework may simply be absent from the checkout. A preference
list is a preference; a refusal is a measurement; conflating them is how a run ends up reporting "no
engine" when the truth is "the preferred engine would have needed 34 TiB".

**MemAvailable is logged before every run.** The budget is checked against an estimate, and an
estimate is not a measurement of the machine — the host this project runs on may already be swapping
because of something else entirely, and on such a host a run that passes its budget check is still a
run that thrashes. So each run logs the kernel's ``MemAvailable`` immediately before the engine is
called, and logs a warning when the estimate is larger than what the kernel says is available. The
warning does not replace the refusal and is not a second budget: it is the one number that turns
"this sweep was slow" into "this sweep ran the machine out of memory at row 12".
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from typing import Any

from .base_backend import (
    BackendResult,
    QuantumBackend,
    RamBudgetExceeded,
    available_bytes,
    format_bytes,
    memory_snapshot,
)

__all__ = [
    "ENGINES",
    "BackendSelectorError",
    "UnknownBackend",
    "BackendUnavailable",
    "NoBackendAvailable",
    "NoBackendFits",
    "engine_names",
    "load_engine",
    "available_engines",
    "select_backend",
    "run_selected_backend",
]

ENGINES: dict[str, tuple[str, str]] = {
    "qiskit_aer": ("grover_emulator.backends.qiskit_aer_backend", "QiskitAerBackend"),
    "cirq_qsim": ("grover_emulator.backends.cirq_qsim_backend", "CirqQsimBackend"),
    "tensor_network": ("grover_emulator.backends.tensor_network_backend", "TensorNetworkBackend"),
}
"""Engine name to module and class, for the names ``backend.preference`` can carry.

The mapping is by name and the import is deferred, so importing this module does not import three
simulation frameworks, and a checkout missing one of them can still run the other two. Aer is first
in the default preference because it is the fastest exact engine here; qsim is beside it because it
is the only genuinely independent second opinion this project has — a different compiler and a
different kernel — and agreement between the two is evidence about the circuit rather than about one
library. The tensor-network engine is not in the default list: it is slower than Aer at every width
where Aer fits, and it is selected when a caller asks for it or when the statevector engines are over
budget.
"""

_LOG_NAME = "grover_emulator"
"""The package's logger, as :func:`grover_emulator.utils.logging_config.configure_logging` names it."""


class BackendSelectorError(RuntimeError):
    """The selector could not produce an engine."""


class UnknownBackend(BackendSelectorError):
    """A preference named an engine this checkout does not know."""


class BackendUnavailable(BackendSelectorError):
    """A known engine could not be loaded — usually a framework that is not installed."""


class NoBackendAvailable(BackendSelectorError):
    """No engine in the preference list could be loaded."""

    def __init__(self, preference: list[str], reasons: list[str]):
        self.preference = list(preference)
        self.reasons = list(reasons)
        super().__init__(
            "none of the preferred engines could be loaded: "
            + "; ".join(reasons)
            + ". A preference list is a preference, not an availability claim; either install the "
            "framework an engine needs or name one that is present."
        )


class NoBackendFits(RamBudgetExceeded):
    """Every available engine refused the width, with each engine's own refusal attached.

    A :class:`~grover_emulator.backends.base_backend.RamBudgetExceeded` because that is what it is —
    a run that will not fit — and the caller that catches the engine's refusal should catch this one
    too. The estimate it carries is the *smallest* among the engines that refused, which is the
    friendliest number available and the one that says how far over the line the circuit is.
    """

    def __init__(
        self,
        refusals: list[RamBudgetExceeded],
        n_qubits: int,
        budget_bytes: int,
        meminfo: dict[str, int] | None = None,
    ):
        if not refusals:
            raise ValueError("NoBackendFits needs at least one engine's refusal")
        self.refusals = tuple(refusals)
        detail = " Every preferred engine refused: " + "; ".join(
            f"{refusal.backend} needs {format_bytes(refusal.estimate_bytes)}" for refusal in refusals
        ) + "."
        super().__init__(
            "selector",
            n_qubits,
            min(refusal.estimate_bytes for refusal in refusals),
            budget_bytes,
            meminfo,
            detail=detail,
        )


# -----------------------------------------------------------------------------------------------
# the registry
# -----------------------------------------------------------------------------------------------


def engine_names() -> list[str]:
    """Every engine name this checkout knows, whether or not its framework is installed."""
    return list(ENGINES)


def load_engine(name: str) -> type[QuantumBackend]:
    """The engine class registered under ``name``, if this checkout can actually run it.

    Availability is checked in two steps and both are needed. The module has to import, and the
    modules the engine *declares* it needs have to be importable as well — the class asks for
    ``requires`` precisely because every framework import in this package happens inside the method
    that needs it, so a successful module import is evidence of nothing. A check that stopped at the
    first step would let a preference list resolve to an engine that raises on its first run.
    """
    if name not in ENGINES:
        raise UnknownBackend(
            f"{name!r} is not an engine this checkout knows; known engines are "
            f"{sorted(ENGINES)}"
        )
    module_name, class_name = ENGINES[name]
    try:
        module = importlib.import_module(module_name)
    except ImportError as error:
        raise BackendUnavailable(f"{name}: {module_name} could not be imported: {error}") from error
    engine = getattr(module, class_name, None)
    if engine is None:
        raise BackendUnavailable(f"{name}: {module_name} does not provide {class_name}")
    missing = [module for module in engine.requires if importlib.util.find_spec(module) is None]
    if missing:
        raise BackendUnavailable(
            f"{name}: the engine needs {', '.join(missing)}, which is not installed in this checkout"
        )
    return engine


def available_engines() -> dict[str, type[QuantumBackend]]:
    """The engines this checkout can load, in registry order."""
    found: dict[str, type[QuantumBackend]] = {}
    for name in ENGINES:
        try:
            found[name] = load_engine(name)
        except BackendSelectorError:
            continue
    return found


# -----------------------------------------------------------------------------------------------
# selection
# -----------------------------------------------------------------------------------------------


def _preference_and_budget(config: Any) -> tuple[list[str], float]:
    """The preference list and the ceiling, from a full config or a backend section.

    Both are accepted because both are in scope at the call sites: the CLI holds an
    ``ExperimentConfig`` and a sweep row holds the section it was built from. Reading the fields here,
    once, keeps the selector from growing two entry points that can disagree.
    """
    settings = getattr(config, "backend", config)
    preference = list(getattr(settings, "preference", []))
    budget = float(getattr(settings, "ram_budget_gb", 6.0))
    if not preference:
        raise BackendSelectorError(
            "the configuration names no preferred engine; a preference list with nothing in it "
            "cannot be resolved into an engine"
        )
    return preference, budget


def select_backend(
    config: Any,
    *,
    num_qubits: int | None = None,
    gate_list: Any = None,
    log: logging.Logger | None = None,
) -> QuantumBackend:
    """The first engine in the configuration's preference that can run this circuit.

    ``gate_list`` wins over ``num_qubits`` when both are given, because a gate list carries its own
    width and a caller that passes both has usually passed the width for a different reason. With
    neither, the first loadable engine is returned and the budget is not consulted — the engine will
    refuse at its own start, where the width is known and the estimate is the engine's own.

    Raises:
        UnknownBackend: a name in the preference is not in the registry.
        NoBackendAvailable: no preferred engine could be loaded, with each reason attached.
        NoBackendFits: every loadable engine refused the width, carrying each engine's refusal.
    """
    log = log or logging.getLogger(_LOG_NAME)
    preference, budget = _preference_and_budget(config)
    width = gate_list.num_qubits if gate_list is not None else num_qubits

    unavailable: list[str] = []
    refusals: list[RamBudgetExceeded] = []
    for name in preference:
        try:
            engine_class = load_engine(name)
        except UnknownBackend:
            raise
        except BackendUnavailable as error:
            unavailable.append(str(error))
            log.debug("backend_selector: skipping %s: %s", name, error)
            continue

        engine = engine_class(ram_budget_gb=budget)
        if width is None:
            log.info(
                "backend_selector: %s selected with no width to budget against; the engine checks "
                "the budget itself when it runs",
                name,
            )
            return engine
        try:
            estimate = engine.require_within_budget(width)
        except RamBudgetExceeded as refusal:
            refusals.append(refusal)
            log.info(
                "backend_selector: %s refuses %d qubits (%s estimated against a %s ceiling)",
                name,
                width,
                format_bytes(refusal.estimate_bytes),
                format_bytes(budget * (1 << 30)),
            )
            continue
        log.info(
            "backend_selector: %s selected for %d qubits, estimated %s",
            name,
            width,
            format_bytes(estimate),
        )
        return engine

    if refusals:
        raise NoBackendFits(refusals, width, int(budget * (1 << 30)), memory_snapshot())
    raise NoBackendAvailable(preference, unavailable)


def run_selected_backend(
    config: Any,
    gl: Any,
    *,
    shots: int | None = None,
    seed: int | None = None,
    log: logging.Logger | None = None,
) -> BackendResult:
    """Select an engine for this gate list, log what the machine looked like, and run it.

    The kernel's ``MemAvailable`` is read immediately before the engine is called and written to the
    log with the estimate beside it. That ordering is the point: a snapshot taken at the start of a
    sweep describes the sweep's first row, not its twelfth, and the row where a memory-starved run
    went wrong is exactly the row whose snapshot matters. The same snapshot is in the result's
    ``memory_before``, so a record carries it whether or not anyone kept the log.

    ``shots=None`` means the exact statevector; anything else is a sampled run. The seed is passed
    through untouched — an engine with no seed draws one and records the value it drew, so a run that
    was not given a seed is still a run whose seed is written down.
    """
    log = log or logging.getLogger(_LOG_NAME)
    snapshot = memory_snapshot()
    available = available_bytes(snapshot)
    engine = select_backend(config, gate_list=gl, log=log)
    estimate = engine.estimate_bytes_for(gl)

    log.info(
        "backend_selector: running %s on %r: %d qubits, estimated %s, MemAvailable %s, %s",
        engine.name,
        gl.label,
        gl.num_qubits,
        format_bytes(estimate),
        format_bytes(available) if available is not None else "unknown",
        "statevector" if shots is None else f"{shots} shots",
    )
    if available is not None and available < estimate:
        log.warning(
            "backend_selector: the kernel reports only %s available and this run is estimated at "
            "%s; the budget check passed against the configured ceiling, not against the machine, "
            "and this run may push the host into swap",
            format_bytes(available),
            format_bytes(estimate),
        )

    result = engine.run(gl, shots=shots, seed=seed)
    log.info(
        "backend_selector: %s finished %r in %.3fs: %s",
        result.backend,
        result.label,
        result.elapsed_s,
        "statevector of length %d" % result.statevector.shape[0]
        if result.statevector is not None
        else "counts over %d shots" % result.shots,
    )
    return result
