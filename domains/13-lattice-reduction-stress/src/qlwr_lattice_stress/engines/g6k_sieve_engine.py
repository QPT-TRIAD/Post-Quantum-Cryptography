"""Sieving through G6K — the engine that is optional, and the one that decides the sweep's cost.

G6K is not pip-installable in the ordinary sense (it has never had a wheel), so on a machine where
it was not built from source against a linkable fplll this engine simply is not there. Everything
that touches it is therefore written so that its absence is a fact the program *reports* and never a
`ModuleNotFoundError` three layers down: ``available()`` answers by attempting the import, and the
selector turns a ``False`` into a logged warning rather than a silent substitution.

Three things the library requires that are not obvious, all measured:

**``import cysignals.signals`` must come before ``import g6k``.** G6K's extension modules resolve
cysignals' symbols through the loaded Python symbol table, so the order is load-bearing and not a
style choice. The import is centralised in :func:`_import_g6k` so that no future import site can
get it wrong — which includes the ones inside the tour entry points, which is why they are imported
through a helper rather than at the top of this module.

**``SieverParams`` takes no positional argument.** Constructing it as ``SieverParams(4)`` raises
``TypeError``; the thread count is a field, set after construction. G6K's own test suite does the
same thing, which is the reference this follows.

**Thread scaling reverses with block size.** Measured: at block sizes 40 and 60 one thread is
fastest and four is slowest — consistent with 2 P-cores and 8 E-cores — while at block size 80 four
threads is 1.6x faster than one and at block size 90 it is **2.1x** faster (193 s against 405 s).
The interesting runs are the large-block-size ones, and the default used to be 4 for that reason.

**The default is 1, because four threads costs reproducibility.** Measured here: with ``threads=1``
two runs at the same seed return bit-identical bases; with ``threads=4`` they do not. The first time
this was measured the two runs agreed on the shortest-vector norm, and the default stayed at 4. The
second measurement settled it: ``notes/09-scaling-and-the-sweep.md`` records four identical
four-thread processes returning three distinct root-Hermite factors, one recovering the planted
vector and three not. This project's results are supposed to be re-derivable from their recorded
seeds, so an engine built without a thread count must be a reproducible one. A run that wants the
speed asks for it — ``threads=4`` — pays with a single draw instead of a measurement, and records
the thread count in its result, which is why ``ReducedBasisResult`` carries one.
"""

from __future__ import annotations

import contextlib
from typing import Any

from qlwr_lattice_stress.engines.base_engine import (
    INTERPRETER_BASELINE_BYTES,
    UNAVAILABLE_VERSION,
    ReductionEngine,
    TourOutcome,
    _reject_unknown_kwargs,
)

__all__ = [
    "G6KSieveEngine",
    "SIEVE_DB_BYTES_PER_ENTRY",
    "SIEVE_DB_ENTRIES_BASE",
    "SIEVE_DB_GROWTH_PER_BLOCK_BIT",
]

#: The database-population model G6K's own source uses: ``3.2 * (4/3)**(beta/2)`` entries. Kept as
#: the count model — it is what the literature quotes and what the plan was built on — while the
#: per-entry cost below is corrected.
SIEVE_DB_ENTRIES_BASE = 3.2
SIEVE_DB_GROWTH_PER_BLOCK_BIT = 4.0 / 3.0

#: The corrected per-entry cost, in bytes. The plan used ~850 B per entry with a further 2.0 safety
#: factor, which over-predicted by ~15x: at block size 90 that model gives 2174 MiB against a
#: measured cumulative peak of 231 MiB, of which ~90 MiB is the interpreter, so the run's own
#: footprint is at most ~141 MiB. Dividing those measured bounds by the model's entry count gives
#: ~145 B/entry at block size 80 and ~105 B/entry at 90; 160 is taken as the larger of the two, so
#: the estimate stays above both while the redundant safety factor is dropped, its margin already
#: carried by the bounds themselves.
#:
#: This constant is **bound-derived, not measured per configuration**. The profile script ran every
#: configuration inside one process, so ``ru_maxrss`` accumulated across them and the
#: per-configuration deltas it reported are noise (one configuration reporting less memory than an
#: earlier one, which is impossible). Only the cumulative peak is usable, and only as an upper
#: bound. Re-deriving this constant needs a fork per configuration; until then it is an estimate and
#: is documented as one.
SIEVE_DB_BYTES_PER_ENTRY = 160

#: The block size the two measured bounds above bracket.
CALIBRATION_BLOCK_SIZE = 90


def _import_g6k() -> Any:
    """Import G6K, with cysignals ahead of it, and return the module.

    Deliberately not cached. The availability tests replace the module an engine imports and then
    ask again; a cached success from a previous call in the same process would make the
    unavailability path unreachable from a test, which is how a fallback path rots. After the first
    successful call this is a ``sys.modules`` lookup.
    """
    import cysignals.signals  # noqa: F401  -- must precede g6k; see the module docstring
    import g6k

    return g6k


def _max_sieving_dim_warning_explained():
    """Silence G6K's ``full_n > MAX_SIEVING_DIM`` warning, having checked what it means.

    G6K warns from ``siever.pyx:107`` whenever the lattice is wider than ``MAX_SIEVING_DIM`` (128,
    ``kernel/siever.h:83``). Dimensions 130 and 160 give lattices 131 and 161 wide, so the sweep's
    two largest points warn on every tour while d100 and below never do.

    **It is over-conservative, and the reason is a naming collision rather than a limit.** ``full_n``
    is an ``unsigned int`` and ``full_muT``/``full_rr`` are ``std::vector``s sized to it; the fixed
    ``std::array<ZT, MAX_SIEVING_DIM>`` buffers in the same header hold *local* sieve coordinates,
    which are bounded by the block size. The macro bounds the sieving dimension, and the check
    compares it against the lattice dimension. This engine's block sizes never exceed
    the config schema's ``BLOCK_SIZE_HARD_MAX`` (90, with or without the long-run opt-in), so the
    quantity the macro actually bounds is always respected.

    That is a reading of the source, so it was checked by a route that would fail if the reading were
    wrong: at dimension 130 (lattice 131, above the limit) G6K **recovered the exact planted vector**
    at block size 70, and ``is_recovered`` is exact vector equality against the planted short vector
    rather than a norm threshold. A siever misbehaving above 128 would not find that vector at all.

    Suppressed **narrowly**, by message, so a G6K warning that is not this one still reaches the
    operator. A warning that fires on every run and means nothing is a warning that hides the ones
    that matter.
    """
    import warnings

    @contextlib.contextmanager
    def _silenced():
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"Dimension of lattice is larger than maximum supported.*",
                category=UserWarning,
            )
            yield

    return _silenced()


def _g6k_tour_entry_points() -> tuple[Any, Any, Any, Any]:
    """The tour entry points, imported only once G6K itself has imported cleanly."""
    _import_g6k()
    from g6k.algorithms.bkz import pump_n_jump_bkz_tour
    from g6k.siever import Siever
    from g6k.siever_params import SieverParams
    from g6k.utils.stats import dummy_tracer

    return Siever, SieverParams, pump_n_jump_bkz_tour, dummy_tracer


def sieve_db_entries(block_size: int) -> float:
    """G6K's own database-population model, ``3.2 * (4/3)**(beta/2)`` entries."""
    return SIEVE_DB_ENTRIES_BASE * SIEVE_DB_GROWTH_PER_BLOCK_BIT ** (block_size / 2.0)


class G6KSieveEngine(ReductionEngine):
    """BKZ whose SVP oracle is G6K's sieve, primal by default and dual on request.

    The dual mode is the reason ``dual_mode`` is a keyword argument here and nowhere else: a dual
    attack reduces the *dual* lattice, and handing a primal reduction to a dual attack produces a
    self-consistent basis for the wrong problem. It is passed through to
    ``siever.temp_params(dual_mode=True)`` for the duration of one tour and no longer.
    """

    name = "g6k_sieve"

    def __init__(self, *, gauss_crossover: int | None = None, **kwargs: Any) -> None:
        """
        Args:
            gauss_crossover: The sieving dimension below which G6K runs its Gauss sieve instead of
                its default sieve — ``SieverParams.gauss_crossover``, read at ``siever.pyx:1314``.
                ``None`` leaves G6K's own default (50) in place. It is the config's
                ``engine.gauss_crossover``, which was validated, shipped in the YAML and handed to
                nothing until 2026-09-20.
            **kwargs: Everything :class:`ReductionEngine` takes.
        """
        super().__init__(**kwargs)
        if gauss_crossover is not None and gauss_crossover < 1:
            raise ValueError(f"gauss_crossover must be at least 1, got {gauss_crossover}")
        self.gauss_crossover = gauss_crossover

    @property
    def default_threads(self) -> int:
        # 1, not 4. Four threads is 2.1x faster at block size 90 and is *not reproducible*:
        # notes/09-scaling-and-the-sweep.md measured four identical four-thread processes returning
        # three distinct root-Hermite factors, one of which recovered the planted vector. A default
        # is what runs when nobody chose, and nobody should get single draws by not choosing. This
        # returned 4 until 2026-09-20; see the module docstring.
        return 1

    def unavailable_reason(self) -> str | None:
        try:
            _import_g6k()
        except Exception as exc:
            return (
                f"g6k is not importable in this interpreter: {type(exc).__name__}: {exc}. It has "
                "never had a published wheel and is built from source against a linkable fplll, so "
                "absence here means it was not built for this environment."
            )
        return None

    def version(self) -> str:
        try:
            g6k = _import_g6k()
        except Exception:
            return UNAVAILABLE_VERSION
        return str(getattr(g6k, "__version__", UNAVAILABLE_VERSION))

    def estimate_memory_bytes(self, block_size: int) -> int:
        """Interpreter baseline plus the sieve database, with the plan's constant corrected.

        The correction and its provenance — including why it is bound-derived rather than measured
        — are recorded on :data:`SIEVE_DB_BYTES_PER_ENTRY`. What matters operationally is the
        conclusion the measurement supports: at block size 90 this is ~305 MiB against 7.5 GiB
        available, so memory is not the binding constraint on this project and this estimate is a
        guard against a genuine runaway rather than the thing that sets the sweep's ceiling.
        """
        if block_size < 1:
            raise ValueError(f"block size must be positive, got {block_size}")
        return INTERPRETER_BASELINE_BYTES + int(sieve_db_entries(block_size) * SIEVE_DB_BYTES_PER_ENTRY)

    def _run_tours(
        self, matrix: Any, block_size: int, *, dual_mode: bool = False, **kwargs: Any
    ) -> TourOutcome:
        """Run sieving tours one at a time, counting them, in primal or dual mode.

        The seed is derived per call from the block size and the dimension, so a rerun of the same
        instance at the same block size replays, and a different instance does not reuse the same
        stream. ``Siever`` mutates ``matrix`` in place — measured — including during construction,
        which is why the base class hands over a copy and not the caller's basis.
        """
        _reject_unknown_kwargs(kwargs, allowed=("dual_mode",), engine=self.name)

        Siever, SieverParams, pump_n_jump_bkz_tour, dummy_tracer = _g6k_tour_entry_points()

        params = SieverParams()
        params.threads = self.threads
        if self.gauss_crossover is not None:
            params.gauss_crossover = self.gauss_crossover
        with _max_sieving_dim_warning_explained():
            siever = Siever(matrix, params, seed=self._seed_for("tour", block_size, matrix.nrows))

        def one_tour(beta: int) -> None:
            if dual_mode:
                with siever.temp_params(dual_mode=True):
                    pump_n_jump_bkz_tour(siever, dummy_tracer, beta)
            else:
                pump_n_jump_bkz_tour(siever, dummy_tracer, beta)

        n_tours, converged = self._tour_loop(matrix, block_size, one_tour, self.max_tours)
        return TourOutcome(n_tours=n_tours, converged=converged, threads=self.threads)
