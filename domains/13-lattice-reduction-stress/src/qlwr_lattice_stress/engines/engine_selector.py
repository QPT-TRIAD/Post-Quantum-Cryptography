"""Choosing an engine, and refusing to do it quietly.

The sweep wants G6K: it is the stronger engine, it is faster at the block sizes that matter, and if
it is not installed the interesting runs get measurably weaker. Falling back to enumeration is a
legitimate thing to do — the alternative is not running at all — but it changes what the numbers
mean. At a fixed block size a sieve reaches shorter vectors than enumeration, so a root-Hermite
factor measured at block size 60 on one engine is not the same quantity as one measured at block
size 60 on the other. A substitution that leaves no trace turns a run of enumeration points into a
run of "G6K points" in the results file, and the report that reads it will compare them against a
model calibrated for sieving.

So the fallback exists, is the *documented* behaviour, and is loud: one WARNING naming the engine
that was asked for, the reason it is unavailable, the engine that will run instead, and the fact
that the run's strength is reduced. Silence is the failure mode being designed against here, not
the fallback itself.

The RAM check is deliberately a separate function rather than a step inside ``select_engine``. The
budget is a property of a *block size*, and one engine object serves a whole sweep of them, so the
check belongs at the point where a block size is about to be attempted: ``assert_within_ram_budget``
raises rather than returning a flag, because a caller that ignored a ``False`` would spend the six
GiB and lose the run.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from qlwr_lattice_stress.engines.base_engine import RamBudgetExceeded, ReductionEngine
from qlwr_lattice_stress.engines.fpylll_bkz_engine import FpylllBKZEngine
from qlwr_lattice_stress.engines.g6k_sieve_engine import G6KSieveEngine
from qlwr_lattice_stress.utils.seeding import RunSeeds

__all__ = [
    "DEFAULT_ENGINE",
    "DEFAULT_RAM_BUDGET_GB",
    "DEFAULT_THREADS",
    "ENGINE_NAMES",
    "FPYLLL_BKZ",
    "G6K",
    "assert_within_ram_budget",
    "select_engine",
]

_LOG = logging.getLogger(__name__)

G6K = "g6k"
FPYLLL_BKZ = "fpylll_bkz"

#: The engines a config may name, strongest first. Ordering is the preference order, not an
#: alphabetical list: ``DEFAULT_ENGINE`` is the head of it.
ENGINE_NAMES: tuple[str, ...] = (G6K, FPYLLL_BKZ)

#: What runs when the requested engine cannot. One step, and the step is recorded when it is taken.
FALLBACK_CHAIN: dict[str, str] = {G6K: FPYLLL_BKZ}

DEFAULT_ENGINE = G6K

#: Threads for the engine's own parallelism. **1, and it is a correctness setting rather than a
#: speed one**: the hardware calibration found 4 to be 2.1x faster than 1 at block size 90, and this
#: was 4 until 2026-09-20 for that reason — but notes/09-scaling-and-the-sweep.md then measured four
#: identical four-thread G6K processes returning three distinct root-Hermite factors, one recovering
#: the planted vector and three not. A default that yields single draws makes every run that did
#: not think about threads irreproducible from its own seed. The enumeration engine accepts this
#: value and records 1, because it has no threads to give.
DEFAULT_THREADS = 1

#: The refusal threshold the calibration kept: it never fired there (the measured peak at block
#: size 90 is 231 MiB against 7.5 GiB), and it is retained as a guard against a genuine runaway
#: rather than as the thing that sets the sweep's ceiling.
DEFAULT_RAM_BUDGET_GB = 6.0

_ENGINE_CLASSES: dict[str, type[ReductionEngine]] = {
    G6K: G6KSieveEngine,
    FPYLLL_BKZ: FpylllBKZEngine,
}

#: The config key naming the requested engine.
ENGINE_KEY = "engine"

#: The config key naming an ordered list of engines, strongest wanted first. When present it
#: replaces both ``engine`` and :data:`FALLBACK_CHAIN`: the head is the engine asked for and the
#: tail is what may run instead, **and nothing outside the list may** — a preference of ``[g6k]``
#: alone is a request to fail rather than to substitute.
PREFERENCE_KEY = "preference"


def _config_value(config: Any, key: str, default: Any) -> Any:
    """Read ``key`` from a mapping or from an object with attributes.

    Both, because the selection is called from the sweep runner (which has a parsed mapping from the
    config file) and from tests and ad-hoc scripts (which have an object). A selector that only
    accepted one of those would push a dict-to-object adapter into every caller, and the adapter is
    the kind of glue that ends up quietly defaulting a key nobody noticed was misspelled.
    """
    if config is None:
        return default
    if isinstance(config, Mapping):
        return config.get(key, default)
    return getattr(config, key, default)


def build_engine(
    name: str,
    *,
    seed: int = 0,
    seeds: RunSeeds | None = None,
    threads: int | None = None,
    max_tours: int | None = None,
    gauss_crossover: int | None = None,
) -> ReductionEngine:
    """Construct one engine by name, with no substitution and no fallback.

    Kept separate from :func:`select_engine` so that a caller who *wants* the named engine and wants
    a hard failure when it is absent can have that, and the fallback policy stays in one place.

    ``gauss_crossover`` reaches the sieving engine only. It is a property of G6K's sieve; the
    enumeration engine has no sieve to cross over to, and is not handed a knob it would ignore.
    """
    if name not in _ENGINE_CLASSES:
        raise ValueError(
            f"unknown engine {name!r}; known engines are {', '.join(ENGINE_NAMES)}. An unknown name "
            "is refused rather than defaulted, because a typo in a config would otherwise silently "
            "select whichever engine happens to be the default."
        )
    engine_class = _ENGINE_CLASSES[name]
    kwargs: dict[str, Any] = {"seed": seed, "seeds": seeds, "threads": threads}
    if max_tours is not None:
        kwargs["max_tours"] = max_tours
    if gauss_crossover is not None and name == G6K:
        kwargs["gauss_crossover"] = gauss_crossover
    return engine_class(**kwargs)


def select_engine(config: Any = None) -> ReductionEngine:
    """The engine a run should use, given its config.

    Reads ``engine`` (one of :data:`ENGINE_NAMES`, default :data:`DEFAULT_ENGINE`), ``threads``
    (default :data:`DEFAULT_THREADS`), ``seed`` and ``gauss_crossover`` from ``config``, which may
    be a mapping, an object with those attributes, a bare engine name, or ``None`` for the defaults.

    A config may instead carry ``preference`` — an ordered sequence of engine names (or of enum
    members whose ``value`` is one), which is what the experiment schema's ``engine.preference`` is.
    Its head is the requested engine and its tail, in order, is the only set of engines that may be
    substituted; :data:`FALLBACK_CHAIN` is not consulted. The pipeline used to build
    ``preference[0]`` and never look at the rest, so the shipped ``[g6k, fpylll_bkz]`` raised on a
    machine without G6K where its own comment promised a fallback.

    When the requested engine is unavailable, the next available engine is returned **with a
    WARNING that names the requested engine, the reason it is unavailable, the engine that will
    run, and the fact that the run's strength is reduced**. The warning is the deliverable as much
    as the engine is: a fallback that a report cannot see is a mislabelled measurement.

    Raises:
        ValueError: for an unknown engine name, or a missing fallback.
        RuntimeError: if neither the requested engine nor its fallback can run, since no reduction
            is possible and returning ``None`` would push the failure into the first use of it.
    """
    preference = None if isinstance(config, str) else _config_value(config, PREFERENCE_KEY, None)
    if preference:
        names = [getattr(name, "value", name) for name in preference]
        requested, fallback_names = names[0], names[1:]
    else:
        requested = (
            config if isinstance(config, str) else _config_value(config, ENGINE_KEY, DEFAULT_ENGINE)
        )
        # ``isinstance`` first: an unhashable ``engine`` value has to reach the refusal below as a
        # ValueError, not die here as a TypeError from the dict lookup.
        chained = FALLBACK_CHAIN.get(requested) if isinstance(requested, str) else None
        fallback_names = [chained] if chained else []
    for name in (requested, *fallback_names):
        if not isinstance(name, str):
            raise ValueError(f"config key {ENGINE_KEY!r} must be a string, got {name!r}")
        if name not in _ENGINE_CLASSES:
            raise ValueError(
                f"unknown engine {name!r}; known engines are {', '.join(ENGINE_NAMES)}"
            )

    threads = _config_value(config, "threads", DEFAULT_THREADS)
    seed = _config_value(config, "seed", 0)
    seeds = _config_value(config, "seeds", None)
    gauss_crossover = _config_value(config, "gauss_crossover", None)

    def build(name: str) -> ReductionEngine:
        return build_engine(
            name, seed=seed, seeds=seeds, threads=threads, gauss_crossover=gauss_crossover
        )

    engine = build(requested)
    if engine.available():
        _LOG.info(
            "reduction engine %r selected (version %s, threads %s)",
            engine.name,
            engine.version(),
            engine.threads,
        )
        return engine

    if not fallback_names:
        raise RuntimeError(
            f"engine {requested!r} is unavailable ({engine.unavailable_reason()}) and has no "
            "fallback; this run cannot be performed and must be recorded as not_run rather than "
            "attempted with something else"
        )
    # First available wins. With two engines there is one fallback and this loop runs once; it is a
    # loop so that a third engine added to a preference list is tried rather than silently skipped.
    unavailable: list[str] = []
    fallback = None
    for fallback_name in fallback_names:
        candidate = build(fallback_name)
        if candidate.available():
            fallback = candidate
            break
        unavailable.append(f"{fallback_name!r} ({candidate.unavailable_reason()})")
    if fallback is None:
        raise RuntimeError(
            f"engine {requested!r} is unavailable ({engine.unavailable_reason()}) and so is its "
            f"fallback {', '.join(unavailable)}; no reduction is possible in this interpreter"
        )

    _LOG.warning(
        "engine fallback: %r was requested but is unavailable (%s). Falling back to %r. "
        "The run's strength is reduced: at the same block size a sieving engine returns shorter "
        "vectors than enumeration, so block sizes and root-Hermite factors measured on %r are not "
        "comparable with ones measured on %r, and this run's results must be labelled with the "
        "engine that actually ran.",
        requested,
        engine.unavailable_reason(),
        fallback.name,
        fallback.name,
        requested,
    )
    return fallback


def assert_within_ram_budget(
    engine: ReductionEngine,
    block_size: int,
    budget_gb: float = DEFAULT_RAM_BUDGET_GB,
) -> int:
    """Refuse a block size whose estimated footprint exceeds ``budget_gb``, before running it.

    Raises rather than returning a flag, and raises *before* any reduction is attempted: a run that
    is stopped at the budget leaves a partial basis and a wall-clock time that reads like a
    completed measurement of a hard instance. The estimate is a model and is documented as one — the
    measured peak at block size 90 is 231 MiB against 7.5 GiB available, so this guard is a check
    against a genuine runaway, not the thing that decides how far a sweep goes.

    Returns:
        The estimated footprint in bytes, for the run's log or its notes.

    Raises:
        ValueError: if the budget is not positive.
        RamBudgetExceeded: if the estimate exceeds the budget. The message carries the engine, the
            block size, the estimate and the budget, because a refusal that a reader cannot
            reproduce is a refusal they will work around.
    """
    if budget_gb <= 0:
        raise ValueError(f"budget_gb must be positive, got {budget_gb}")
    predicted = engine.estimate_memory_bytes(block_size)
    budget_bytes = int(budget_gb * (1 << 30))
    if predicted > budget_bytes:
        raise RamBudgetExceeded(
            f"{engine.name} at block size {block_size} is estimated at "
            f"{predicted / (1 << 20):.1f} MiB, over the budget of {budget_gb} GiB "
            f"({budget_bytes} bytes). Refusing rather than attempting: the estimate is an upper "
            "bound, and a run that exhausts memory part-way through leaves a partial reduction "
            "whose wall-clock time would be recorded as a measurement."
        )
    return predicted
