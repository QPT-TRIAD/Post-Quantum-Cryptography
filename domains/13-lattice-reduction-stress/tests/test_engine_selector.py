"""Choosing an engine: the fallback, the warning that makes it a fallback, and the refusal.

The substitution this file is about is the one the project is most exposed to. G6K is not always
present, the sweep wants it, and the alternative to falling back is not running. The fallback is
therefore *correct behaviour* and the tests below assert it happens — and assert, just as hard, that
it happens loudly. A run that asked for a sieve, got enumeration, and recorded neither is a run
whose root-Hermite factors will be read as sieving results and compared against a sieving model.

Two behaviours that are easy to get half-right and are tested separately: the warning is emitted by
the selector and not merely available from it, and it names the reason rather than saying that
something went wrong. The second is what makes the fallback diagnosable on a machine whose only
symptom is a weaker run.

The RAM check is a refusal and not a flag, and it is tested as one: the stub engine below raises if
it is ever reduced with, so a test that passes proves the check happened *before* the work and not
after it.
"""

from __future__ import annotations

import builtins
import logging
from dataclasses import dataclass

import pytest

from engine_helpers import NoOpEngine, qary_basis  # type: ignore[import-not-found]
from qlwr_lattice_stress.engines.base_engine import RamBudgetExceeded
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
from qlwr_lattice_stress.engines.g6k_sieve_engine import G6KSieveEngine
from qlwr_lattice_stress.utils.seeding import RunSeeds

SELECTOR_LOGGER = "qlwr_lattice_stress.engines.engine_selector"

AVAILABLE = G6KSieveEngine().available()
requires_g6k = pytest.mark.skipif(
    not AVAILABLE,
    reason="G6K is not importable in this interpreter; see G6KSieveEngine.unavailable_reason()",
)


@pytest.fixture
def without_g6k(monkeypatch):
    """Make ``import g6k`` raise, so the selector meets the case it exists for.

    ``builtins.__import__`` rather than ``sys.modules``: the import statement calls it first, so one
    guard covers a cached module and an uncached one, and it is the mechanism the engine's own
    availability check goes through. Everything else is delegated, so this cannot fail for a reason
    unrelated to G6K.
    """
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "g6k" or name.startswith("g6k."):
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


def selector_warnings(caplog) -> list[str]:
    """The WARNING records this module's logger actually emitted during the test."""
    return [
        record.getMessage()
        for record in caplog.records
        if record.name == SELECTOR_LOGGER and record.levelno >= logging.WARNING
    ]


class UntouchableEngine(NoOpEngine):
    """An engine that fails loudly if a budget refusal is ever late.

    The refusal has to happen before the run, and a test that only asserts the exception cannot tell
    "refused before starting" from "refused after finishing, with the answer thrown away". This
    engine makes the difference observable: if ``reduce`` is reached, the test errors with the
    message below instead of passing.
    """

    name = "untouchable_stub"

    def estimate_memory_bytes(self, block_size: int) -> int:
        return block_size**2 * (1 << 30)

    def reduce(self, *args, **kwargs):  # type: ignore[override]
        raise AssertionError("must not be called: the budget refusal has to precede the reduction")


# -- which engine -------------------------------------------------------------------------------


def test_the_default_engine_is_the_stronger_one():
    """The ordering is a preference, not an alphabetical list: G6K first, and the default is the
    head of it."""
    assert DEFAULT_ENGINE == G6K == "g6k"
    assert ENGINE_NAMES[0] == G6K
    assert FPYLLL_BKZ in ENGINE_NAMES
    # 1, the only reproducible G6K setting (notes/09). This line pinned 4 until 2026-09-20.
    assert DEFAULT_THREADS == 1


@requires_g6k
def test_the_default_selection_is_g6k_when_it_is_available(caplog):
    with caplog.at_level(logging.INFO, logger=SELECTOR_LOGGER):
        engine = select_engine()
    assert isinstance(engine, G6KSieveEngine)
    assert engine.threads == DEFAULT_THREADS
    # Nothing was substituted, so nothing may be reported as having been.
    assert selector_warnings(caplog) == []


@requires_g6k
def test_asking_for_g6k_explicitly_is_not_a_fallback(caplog):
    with caplog.at_level(logging.INFO, logger=SELECTOR_LOGGER):
        engine = select_engine({"engine": "g6k"})
    assert isinstance(engine, G6KSieveEngine)
    assert selector_warnings(caplog) == []


def test_asking_for_fpylll_logs_nothing(caplog):
    """An enumeration run that was asked for is not a reduced-strength run.

    It is weaker at a fixed block size than a sieving run would be — but that is the measurement
    the caller chose to take, and warning about it would train a reader to ignore the warning that
    matters.
    """
    with caplog.at_level(logging.INFO, logger=SELECTOR_LOGGER):
        engine = select_engine({"engine": "fpylll_bkz"})
    assert isinstance(engine, FpylllBKZEngine)
    assert engine.threads == DEFAULT_THREADS
    assert selector_warnings(caplog) == []


def test_the_fallback_from_g6k_logs_a_warning_that_names_everything(without_g6k, caplog):
    """The warning is the deliverable as much as the fallback is.

    It has to name the engine that was asked for, the reason it is unavailable, the engine that will
    run instead, and the fact that the run's strength is reduced. A warning missing any of those
    leaves the reader to work out which run in a sweep is not what it says it is.
    """
    with caplog.at_level(logging.WARNING, logger=SELECTOR_LOGGER):
        engine = select_engine({"engine": "g6k"})

    assert isinstance(engine, FpylllBKZEngine)
    assert engine.available() is True

    warnings = selector_warnings(caplog)
    assert len(warnings) == 1
    message = warnings[0]
    assert "g6k" in message
    assert "fpylll_bkz" in message
    assert "strength is reduced" in message
    # The reason, not a generic failure: the whole point of carrying it is that a reader on a
    # machine without G6K can see *why* it is missing rather than only that it is.
    assert "ModuleNotFoundError" in message
    assert "wheel" in message


def test_the_fallback_engine_is_recorded_as_the_one_that_ran(without_g6k):
    """The check that the warning is not the only place the substitution is visible.

    A results file is read long after the log is gone, and the engine label in it is what a later
    reader compares against a model. It has to say ``fpylll_bkz``.
    """
    engine = select_engine({"engine": "g6k"})
    result = engine.reduce(qary_basis(12), 12)
    assert result.engine == FPYLLL_BKZ
    assert result.engine != G6K


def test_the_fallback_keeps_the_configuration_the_run_asked_for(without_g6k):
    """A fallback substitutes the engine, not the sweep. Same threads, same seed, same dimensions."""
    engine = select_engine({"engine": "g6k", "threads": 3, "seed": 99})
    assert isinstance(engine, FpylllBKZEngine)
    assert engine.threads == 3
    assert engine.seed == 99


# -- refusals ------------------------------------------------------------------------------------


def test_an_unknown_engine_name_lists_the_known_ones():
    """A typo must not select the default engine and produce a plausible run for the wrong tool."""
    with pytest.raises(ValueError) as raised:
        select_engine({"engine": "g6k_sieve"})
    message = str(raised.value)
    assert "g6k_sieve" in message
    assert "g6k" in message and "fpylll_bkz" in message


def test_a_non_string_engine_value_is_refused():
    with pytest.raises(ValueError, match="must be a string"):
        select_engine({"engine": ["g6k"]})


def test_both_engines_unavailable_raises_rather_than_returning_none(monkeypatch):
    """No reduction is possible, and ``None`` would push that failure into the first use of it.

    The engines are made unavailable through their own answer rather than through an import, because
    what is being tested is the selector's response to two ``False``\\ es — the import machinery is
    covered in ``test_g6k_sieve_engine.py``.
    """
    monkeypatch.setattr(G6KSieveEngine, "unavailable_reason", lambda self: "no sieve here")
    monkeypatch.setattr(FpylllBKZEngine, "unavailable_reason", lambda self: "no enumeration here")

    with pytest.raises(RuntimeError) as raised:
        select_engine({"engine": "g6k"})
    message = str(raised.value)
    assert "no sieve here" in message
    assert "no enumeration here" in message
    assert "no reduction is possible" in message


def test_build_engine_does_not_substitute(without_g6k):
    """``build_engine`` is the honest-hard-failure counterpart to the selector, and it must not
    quietly do the selector's job: it returns the engine that was named, unavailable and all."""
    engine = build_engine("g6k")
    assert isinstance(engine, G6KSieveEngine)
    assert engine.available() is False
    with pytest.raises(RuntimeError):
        engine.reduce(qary_basis(12), 12)


def test_build_engine_refuses_an_unknown_name():
    with pytest.raises(ValueError, match="unknown engine"):
        build_engine("nope")


# -- the config's shape ---------------------------------------------------------------------------


@dataclass
class Config:
    """The same three keys, the way a parsed config file would carry them."""

    engine: str = "fpylll_bkz"
    threads: int = 2
    seed: int = 5


def test_a_mapping_and_an_attribute_object_select_the_same_engine():
    from_mapping = select_engine({"engine": "fpylll_bkz", "threads": 2, "seed": 5})
    from_object = select_engine(Config())
    assert type(from_mapping) is type(from_object) is FpylllBKZEngine
    assert (from_mapping.threads, from_mapping.seed) == (2, 5)
    assert (from_object.threads, from_object.seed) == (2, 5)


def test_a_bare_engine_name_is_a_config():
    engine = select_engine("fpylll_bkz")
    assert isinstance(engine, FpylllBKZEngine)
    assert engine.threads == DEFAULT_THREADS


@requires_g6k
def test_no_config_selects_the_default_engine():
    assert isinstance(select_engine(None), G6KSieveEngine)


def test_a_config_missing_a_key_falls_back_to_the_documented_default():
    """Defaults are read from one place, so a config that omits ``threads`` gets the calibrated
    value rather than an engine's own convenience default."""
    engine = select_engine({"engine": "fpylll_bkz"})
    assert engine.threads == DEFAULT_THREADS
    assert engine.seed == 0
    assert engine.seeds is None


def test_a_run_seeds_object_is_passed_through_rather_than_replaced():
    """A run handed a :class:`RunSeeds` has to derive *through* it, or the derived-seed record in
    the results file describes a different run than the one that produced the basis."""
    seeds = RunSeeds(root=20260914)
    engine = select_engine({"engine": "fpylll_bkz", "seeds": seeds})
    assert engine.seeds is seeds
    # This engine derives nothing — it is deterministic and has no random draw to seed — so the
    # record stays empty. That is the correct answer, and it is checked rather than assumed: a
    # non-empty record here would mean the engine consumed randomness without it mattering.
    engine.reduce(qary_basis(12), 12)
    assert seeds.to_dict() == {"root": 20260914, "derived": []}
    seeds.verify()


@pytest.mark.sieve
@requires_g6k
def test_a_sieving_run_records_the_seeds_it_derived():
    """The engine that *does* randomise has to hand its draws back through the record.

    G6K takes a seed per tour; a run whose seed exists only in the process cannot be re-derived from
    its results file, which is the whole reason the record exists. ``verify`` re-derives every
    recorded seed from the root, so a passing check means the record is the run.
    """
    seeds = RunSeeds(root=20260914)
    engine = select_engine({"engine": "g6k", "seeds": seeds, "threads": 1})
    engine.reduce(qary_basis(12), 12)

    payload = seeds.to_dict()
    assert payload["root"] == 20260914
    assert len(payload["derived"]) == 1
    assert payload["derived"][0]["parts"][0] == G6KSieveEngine.name
    seeds.verify()


# -- the RAM budget --------------------------------------------------------------------------------


def test_the_budget_refuses_before_the_reduction_is_attempted():
    """The stub raises if it is ever reduced with, so this passing is the proof of ordering."""
    engine = UntouchableEngine()
    with pytest.raises(RamBudgetExceeded):
        assert_within_ram_budget(engine, 60, 6.0)
    with pytest.raises(RamBudgetExceeded):
        assert_within_ram_budget(engine, 3, 0.001)


def test_the_refusal_names_the_engine_the_block_size_the_estimate_and_the_budget():
    """A refusal a reader cannot reproduce is a refusal they will work around."""
    engine = UntouchableEngine()
    with pytest.raises(RamBudgetExceeded) as raised:
        assert_within_ram_budget(engine, 60, 6.0)
    message = str(raised.value)
    assert engine.name in message
    assert "block size 60" in message
    # The stub's model is 60**2 GiB, i.e. 3686400.0 MiB — the estimate appears in the message's own
    # units, so a reader can compare it with the log line the sweep prints.
    assert "3686400.0 MiB" in message
    assert "6.0 GiB" in message
    assert "Refusing rather than attempting" in message


def test_a_block_size_within_budget_returns_the_estimate():
    """The returned number is the model's, and callers log it beside the run."""
    engine = FpylllBKZEngine()
    estimate = assert_within_ram_budget(engine, 40, DEFAULT_RAM_BUDGET_GB)
    assert estimate == engine.estimate_memory_bytes(40)


def test_a_stricter_budget_refuses_what_a_looser_one_admits():
    """The check is a comparison against the model and not a constant: the same block size is
    admitted and refused depending on the budget, which is what a caller tuning a sweep needs."""
    engine = FpylllBKZEngine()
    admitted = assert_within_ram_budget(engine, 40, DEFAULT_RAM_BUDGET_GB)
    assert admitted > 0
    with pytest.raises(RamBudgetExceeded):
        assert_within_ram_budget(engine, 40, 0.05)  # 51.2 MiB of budget against a 106 MiB model


def test_a_non_positive_budget_is_refused():
    for budget in (0, -1.0):
        with pytest.raises(ValueError, match="must be positive"):
            assert_within_ram_budget(FpylllBKZEngine(), 40, budget)


def test_the_default_budget_admits_every_block_size_the_sweep_uses():
    """The refusal is a guard against a runaway, not the thing that sets the ceiling — measured, the
    peak at block size 90 is 231 MiB against 7.5 GiB, so what limits this project is time. This
    test is what would fail first if the model were ever tightened into a budget."""
    for engine in (FpylllBKZEngine(), G6KSieveEngine()):
        for block_size in (20, 40, 60, 90):
            assert_within_ram_budget(engine, block_size, DEFAULT_RAM_BUDGET_GB)


def test_the_budget_does_not_touch_the_engine_it_checks():
    """Checking a block size must not construct a reduction, or the sweep would pay for the runs it
    refuses. Measured through the engine's own state rather than by assuming."""
    engine = FpylllBKZEngine()
    before = (engine.seed, engine.threads, engine.max_tours)
    assert_within_ram_budget(engine, 90, DEFAULT_RAM_BUDGET_GB)
    assert (engine.seed, engine.threads, engine.max_tours) == before
