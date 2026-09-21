"""Reduction engines, behind one interface and one invariant.

Importing this package pulls in neither fpylll nor G6K: both are imported lazily, inside the
functions that need them, so that the unavailability of an engine is something ``available()``
reports rather than something an ``import qlwr_lattice_stress.engines`` raises. The one exception
is deliberate — a module that could not be imported at all is a program that cannot explain which
engine it used, and the results file that records ``engine="g6k_sieve"`` has to be able to say so
on a machine where G6K was never built.
"""

from __future__ import annotations

from qlwr_lattice_stress.engines.base_engine import (
    CONVERGENCE_EPSILON_BITS,
    DEFAULT_MAX_TOURS,
    INTERPRETER_BASELINE_BYTES,
    MIN_BLOCK_SIZE,
    LatticePreservationError,
    RamBudgetExceeded,
    ReductionEngine,
    TourOutcome,
    UNAVAILABLE_VERSION,
    assert_same_lattice,
    matrix_rows,
    peak_rss_bytes_upper_bound,
    root_hermite_factor,
)
from qlwr_lattice_stress.engines.engine_selector import (
    DEFAULT_ENGINE,
    DEFAULT_RAM_BUDGET_GB,
    DEFAULT_THREADS,
    ENGINE_NAMES,
    FPYLLL_BKZ,
    G6K,
    assert_within_ram_budget,
    build_engine,
    select_engine,
)
from qlwr_lattice_stress.engines.fpylll_bkz_engine import FpylllBKZEngine
from qlwr_lattice_stress.engines.g6k_sieve_engine import G6KSieveEngine, sieve_db_entries

__all__ = [
    "assert_same_lattice",
    "assert_within_ram_budget",
    "build_engine",
    "CONVERGENCE_EPSILON_BITS",
    "DEFAULT_ENGINE",
    "DEFAULT_MAX_TOURS",
    "DEFAULT_RAM_BUDGET_GB",
    "DEFAULT_THREADS",
    "ENGINE_NAMES",
    "FPYLLL_BKZ",
    "FpylllBKZEngine",
    "G6K",
    "G6KSieveEngine",
    "INTERPRETER_BASELINE_BYTES",
    "LatticePreservationError",
    "MIN_BLOCK_SIZE",
    "RamBudgetExceeded",
    "ReductionEngine",
    "TourOutcome",
    "UNAVAILABLE_VERSION",
    "matrix_rows",
    "peak_rss_bytes_upper_bound",
    "root_hermite_factor",
    "select_engine",
    "sieve_db_entries",
]
