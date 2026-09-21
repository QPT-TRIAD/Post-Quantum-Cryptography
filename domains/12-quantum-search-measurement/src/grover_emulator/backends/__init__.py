"""Simulation engines, the budget they run under, and the selector that picks between them.

The layer's contract is in :mod:`grover_emulator.backends.base_backend`: a run over the memory
ceiling is refused before anything is allocated, and every metric attached to a result comes from the
gate list's IR rather than from the framework that ran it.

The engines themselves are imported on demand rather than here. Each one drives a different
simulation framework, and importing all three to answer a question about one of them is how a package
acquires three heavy dependencies it may never use.
"""

from .backend_selector import (
    ENGINES,
    BackendSelectorError,
    BackendUnavailable,
    NoBackendAvailable,
    NoBackendFits,
    UnknownBackend,
    available_engines,
    engine_names,
    load_engine,
    run_selected_backend,
    select_backend,
)
from .base_backend import (
    MEM_AVAILABLE,
    BackendError,
    BackendResult,
    QuantumBackend,
    RamBudgetExceeded,
    available_bytes,
    from_most_significant_first,
    ir_metrics,
    memory_snapshot,
    sample_statevector,
    statevector_bytes,
)

__all__ = [
    "ENGINES",
    "MEM_AVAILABLE",
    "BackendError",
    "BackendResult",
    "BackendSelectorError",
    "BackendUnavailable",
    "NoBackendAvailable",
    "NoBackendFits",
    "QuantumBackend",
    "RamBudgetExceeded",
    "UnknownBackend",
    "available_bytes",
    "available_engines",
    "engine_names",
    "from_most_significant_first",
    "ir_metrics",
    "load_engine",
    "memory_snapshot",
    "run_selected_backend",
    "sample_statevector",
    "select_backend",
    "statevector_bytes",
]
