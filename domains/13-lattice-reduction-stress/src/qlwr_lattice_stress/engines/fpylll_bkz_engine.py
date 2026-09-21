"""BKZ by enumeration, through fpylll — the engine that is always present.

The other engine in this package sieves. Sieving and enumeration are not two ways of doing one
thing: at a fixed block size, sieving reaches shorter vectors, and enumeration is only competitive
because it is cheaper per block. That is why the engine selector refuses to substitute one for the
other silently, and why this engine exists even where G6K is installed — an enumeration point is
the control that says how much of a sieving run's advantage came from the sieve.

Measured on this machine (``notes/01-hardware.md``, ``scripts/profile_hardware.py``), two tours with
``AUTO_ABORT``:

===========  =======  =======  ========
dimension    beta=20  beta=30  beta=40
===========  =======  =======  ========
100          0.061 s  0.227 s  26.110 s
160          0.275 s  0.582 s  58.638 s
===========  =======  =======  ========

The cost is dominated by the block size, and the enumeration guard that projected ``d=160`` at
``beta=40`` from the ``beta=30`` point was off by a factor of ~19. That guard is a backstop against
an unbounded sweep; it is not a budget, and it is not used here.

Three details of the library that this wrapper has to get right, all measured rather than read:

* ``BKZ.reduction(B, param)`` **modifies ``B`` in place** and returns the same object. The base
  class's copy is what keeps the preservation check meaningful.
* fplll **accepts a block size larger than the dimension** without raising. Enforcing the bound is
  the caller's job, and the base class does it.
* fplll's default flags are right for this project and are left alone. No ``AUTO_ABORT``: it
  truncates a tour on a slope heuristic, which would make ``n_tours`` a number that does not mean
  what it says. No ``GH_BND``: it caps the enumeration radius at a multiple of the Gaussian
  heuristic, and a lattice whose shortest vector sits just above its own heuristic would then be
  reported as reduced when it is not. The flags actually passed are recorded in ``REDUCTION_FLAGS``
  for exactly that reason — "we reduced it" is not a specification.
"""

from __future__ import annotations

from typing import Any

from qlwr_lattice_stress.engines.base_engine import (
    INTERPRETER_BASELINE_BYTES,
    UNAVAILABLE_VERSION,
    ReductionEngine,
    TourOutcome,
    _reject_unknown_kwargs,
)

__all__ = ["FpylllBKZEngine", "ENUMERATION_WORKSPACE_BYTES_PER_BLOCK_ENTRY"]

#: The BKZ flags this engine passes: none. Named so that a reader does not have to infer from an
#: omitted argument whether the omission was a decision — see the module docstring for why
#: ``AUTO_ABORT`` and ``GH_BND`` are both deliberately absent.
REDUCTION_FLAGS = 0

#: Bytes of enumeration workspace per ``block_size**2``, the term of the memory model that is not
#: the interpreter. Bound-derived, not measured per configuration: the calibration ran all eighteen
#: of its points inside one process, so ``ru_maxrss`` accumulated across them and only the
#: *cumulative* peak is usable. That cumulative peak was <=97 MiB, of which ~90 MiB is the
#: interpreter, so the enumeration's own footprint at ``d=160, beta=40`` is at most ~7 MiB. 4 KiB
#: per ``beta**2`` puts ``beta=40`` at 6.4 MiB — just under that bound — and ``beta=160`` at 100 MiB.
#: The true per-configuration footprint remains unmeasured until the profiler forks per
#: configuration; until then this is an estimate that errs upward.
ENUMERATION_WORKSPACE_BYTES_PER_BLOCK_ENTRY = 4 * 1024


class FpylllBKZEngine(ReductionEngine):
    """BKZ with fplll's enumeration as the SVP oracle.

    Required, not optional: the package cannot run without it, and ``available()`` reflects what the
    import actually does rather than a constant.

    ``threads`` is accepted so that one sweep configuration can be handed to either engine
    unchanged, and it is *ignored*: the enumeration this build performs is single-threaded, and a
    result recording 4 would be claiming parallelism that did not happen. The recorded thread count
    is therefore always 1.
    """

    name = "fpylll_bkz"

    @property
    def default_threads(self) -> int:
        return 1

    def unavailable_reason(self) -> str | None:
        try:
            import fpylll  # noqa: F401
        except Exception as exc:
            return (
                f"fpylll is not importable in this interpreter: {type(exc).__name__}: {exc}. It is "
                "provided by the sage environment and is not pip-installable in the ordinary sense "
                "(its wheel vendors its own libfplll), so it is not declared as a dependency that a "
                "resolver could silently replace."
            )
        return None

    def version(self) -> str:
        try:
            import fpylll
        except Exception:
            return UNAVAILABLE_VERSION
        return str(getattr(fpylll, "__version__", UNAVAILABLE_VERSION))

    def estimate_memory_bytes(self, block_size: int) -> int:
        """Interpreter baseline plus an enumeration-workspace term that grows as ``beta**2``.

        See :data:`ENUMERATION_WORKSPACE_BYTES_PER_BLOCK_ENTRY` for why the second term is a
        bound-derived estimate rather than a measurement. Enumeration's footprint is quadratic in
        the block size and small at every size this project runs — which is the point: memory is not
        what limits the sweep, wall-clock time is, and this number exists only so that a genuine
        runaway can be refused before it starts.
        """
        if block_size < 1:
            raise ValueError(f"block size must be positive, got {block_size}")
        return INTERPRETER_BASELINE_BYTES + ENUMERATION_WORKSPACE_BYTES_PER_BLOCK_ENTRY * block_size**2

    def _run_tours(self, matrix: Any, block_size: int, **kwargs: Any) -> TourOutcome:
        """Run BKZ tours one at a time, counting them.

        One tour per call, with the loop above it, rather than letting fplll run ``max_loops``
        itself: the loop has to observe the basis between tours to decide convergence, and
        ``n_tours`` is only meaningful if this code counted the tours rather than inferring them.
        """
        _reject_unknown_kwargs(kwargs, allowed=(), engine=self.name)

        from fpylll import BKZ

        def one_tour(beta: int) -> None:
            BKZ.reduction(matrix, BKZ.Param(block_size=beta, max_loops=1, flags=REDUCTION_FLAGS))

        n_tours, converged = self._tour_loop(matrix, block_size, one_tour, self.max_tours)
        return TourOutcome(n_tours=n_tours, converged=converged, threads=self.default_threads)
