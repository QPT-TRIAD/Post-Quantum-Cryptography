"""G6K, the optional engine: absent cleanly, and recorded honestly when it is present.

G6K has never had a published wheel, so this engine is missing on most machines and present on
exactly one. Both states are tested. The absence tests are the more important of the two, because
they are the ones that would otherwise only ever run on a machine that does not exist yet: they
replace the module G6K is imported from and require that the engine reports *why* it cannot run
rather than raising from three layers down. The engine selector's warning — the difference between a
fallback and a silent substitution — is built on that answer.

The presence tests are skipped when the engine is unavailable, through ``available()`` itself rather
than through an import at the top of this module, so the skip decision and the engine's own
availability answer cannot disagree.
"""

from __future__ import annotations

import builtins
import os
import pathlib
import subprocess
import sys

import pytest

from engine_helpers import (  # type: ignore[import-not-found]
    matrix_rows,
    min_squared_norm,
    qary_basis,
)
from qlwr_lattice_stress.engines.base_engine import (
    INTERPRETER_BASELINE_BYTES,
    UNAVAILABLE_VERSION,
    assert_same_lattice,
)
from qlwr_lattice_stress.engines.g6k_sieve_engine import (
    CALIBRATION_BLOCK_SIZE,
    SIEVE_DB_BYTES_PER_ENTRY,
    G6KSieveEngine,
    sieve_db_entries,
)

pytestmark = [pytest.mark.engine, pytest.mark.sieve]

DIMENSION = 40
BLOCK_SIZE = 40
SHORTEST_SQUARED_NORM = 170242

#: Measured peak resident set size of the whole process, cumulative, at ``scripts/profile_hardware``
#: block size 90: 231 MiB, of which ~90 MiB is the interpreter. It is an upper bound on that run's
#: own footprint, not that run's footprint — the profiler ran every configuration in one process, so
#: ``ru_maxrss`` accumulated across them and the per-configuration deltas it printed are noise. That
#: defect is why the memory model below is described as bound-derived rather than measured.
MEASURED_CUMULATIVE_PEAK_BYTES = 231 * (1 << 20)

#: What the plan's model predicted at the same block size: ``3.2 * (4/3)**45`` entries at ~850 B
#: each with a further factor of 2.0 — 2174 MiB against a measured peak of 231 MiB, an over-
#: prediction of about 15x.
UNCORRECTED_MODEL_BYTES = 2174 * (1 << 20)

AVAILABLE = G6KSieveEngine().available()

requires_g6k = pytest.mark.skipif(
    not AVAILABLE,
    reason="G6K is not importable in this interpreter; see G6KSieveEngine.unavailable_reason()",
)


@pytest.fixture
def without_g6k(monkeypatch):
    """Make ``import g6k`` raise, and nothing else.

    Replaces ``builtins.__import__`` rather than removing ``sys.modules`` entries: an ``import``
    statement calls ``__import__`` before the module cache is consulted, so this covers the cached
    and uncached cases with one mechanism, and the guard has to be in the import machinery to be
    testing what the engine actually does. Every other import — including ``cysignals.signals``,
    which must precede G6K and is the first thing ``_import_g6k`` does — is delegated unchanged, so
    a failure here cannot be a failure of something else.
    """
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "g6k" or name.startswith("g6k."):
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    return guarded_import


# -- absent --------------------------------------------------------------------------------------


def test_availability_is_false_and_the_reason_names_g6k(without_g6k):
    """``available()`` answers by attempting the import, so this is the real absence path."""
    engine = G6KSieveEngine()
    assert engine.available() is False
    reason = engine.unavailable_reason()
    assert reason is not None
    assert "g6k" in reason
    # The reason is read by whoever sees the selector's warning, so it names the failure and why it
    # is expected rather than being a bare "unavailable".
    assert "ModuleNotFoundError" in reason
    assert "wheel" in reason


def test_the_version_is_reported_as_unavailable_and_not_fabricated(without_g6k):
    """A result claiming a version it could not read is worse than one that says it does not know."""
    assert G6KSieveEngine().version() == UNAVAILABLE_VERSION
    assert UNAVAILABLE_VERSION == "unavailable"


def test_reducing_without_g6k_raises_rather_than_returning_something(without_g6k):
    """A reduction that cannot happen must not come back as a basis somebody else reduced."""
    engine = G6KSieveEngine()
    with pytest.raises(RuntimeError) as raised:
        engine.reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    message = str(raised.value)
    assert "g6k_sieve" in message
    assert "g6k" in message
    assert "available()" in message


def test_the_package_imports_and_reports_absence_without_either_library():
    """A machine with neither library must still be able to say which engine it ran without.

    Run in a fresh interpreter, because the subject is the package's *import* and this process has
    already imported both libraries. Setting ``sys.modules[name] = None`` makes any ``import name``
    raise, which is the closest thing to a machine where they were never built; a top-level import
    of either one anywhere in the package turns this into a non-zero exit.
    """
    code = (
        "import sys;"
        "sys.modules['g6k'] = None;"
        "sys.modules['fpylll'] = None;"
        "from qlwr_lattice_stress.engines import FpylllBKZEngine, G6KSieveEngine;"
        "print(G6KSieveEngine().available(), FpylllBKZEngine().available());"
        "print(G6KSieveEngine().unavailable_reason() is not None,"
        " FpylllBKZEngine().unavailable_reason() is not None);"
        "print(G6KSieveEngine().version())"
    )
    import qlwr_lattice_stress

    source_root = str(pathlib.Path(qlwr_lattice_stress.__file__).resolve().parents[1])
    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": source_root},
    )
    assert completed.returncode == 0, completed.stderr
    availability, reasons, version = completed.stdout.splitlines()
    assert availability == "False False"
    assert reasons == "True True"
    assert version == UNAVAILABLE_VERSION


# -- present -------------------------------------------------------------------------------------


@requires_g6k
def test_the_version_is_the_librarys_own():
    import g6k

    assert G6KSieveEngine().version() == str(g6k.__version__)
    assert G6KSieveEngine().version() != UNAVAILABLE_VERSION


@requires_g6k
def test_the_default_thread_count_is_one():
    """Measured twice, and the second measurement wins. 4 threads is 2.1x faster than 1 at block size
    90 (193 s against 405 s) — and is not reproducible: notes/09 records four identical four-thread
    processes returning three distinct root-Hermite factors. This test pinned 4 until 2026-09-20,
    which was pinning the defect; a default is what runs when nobody chose."""
    assert G6KSieveEngine().default_threads == 1
    assert G6KSieveEngine().threads == 1


@requires_g6k
def test_a_run_records_the_thread_count_it_actually_used():
    result = G6KSieveEngine(threads=1).reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    assert result.threads == 1
    assert result.engine == "g6k_sieve"
    assert result.n_tours >= 1
    assert isinstance(result.converged, bool)
    assert result.root_hermite_factor is not None


@requires_g6k
def test_a_seeded_run_is_bit_reproducible_at_one_thread():
    """Measured, and the reason the thread count is in the result: two runs at the same seed with
    ``threads=1`` return bit-identical bases; with ``threads=4`` they do not. Nothing
    in G6K promises determinism, so a result whose seed is published with it is only re-derivable
    when the run chose one thread."""
    engine = G6KSieveEngine(seed=20260914, threads=1)
    first = engine.reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    second = engine.reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    assert matrix_rows(first.basis) == matrix_rows(second.basis)


@requires_g6k
def test_a_different_seed_is_a_different_run():
    """The converse, so the test above is known to be pinning the seed and not a fixed answer."""
    first = G6KSieveEngine(seed=1, threads=1).reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    second = G6KSieveEngine(seed=2, threads=1).reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    assert matrix_rows(first.basis) != matrix_rows(second.basis)


@requires_g6k
def test_a_run_reaches_the_shortest_vector():
    """Measured: the sieving engine at block size 40 reaches ``||.||^2 = 170242``, the same value
    exact enumeration returns on this instance.

    Asserted here against the recorded constant rather than against a recomputed oracle: the
    agreement between the three methods is the subject of ``test_engine_lattice_preservation.py``,
    and duplicating the oracle here would mean this test could pass while all three agreed wrongly.
    """
    result = G6KSieveEngine(threads=1).reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    assert min_squared_norm(result.basis) == SHORTEST_SQUARED_NORM


@requires_g6k
def test_a_dual_mode_run_spans_the_input_lattice_and_finds_the_shortest_vector():
    """The dual path, which is where a wrong lattice is hardest to see.

    A dual attack reduces the dual lattice and is handed a primal basis afterwards; a mishandled
    conversion produces a self-consistent basis of the wrong lattice. Measured on this instance, the
    dual-mode run at block size 40 returns a basis spanning the same lattice holding the shortest
    vector (``||.||^2 = 170242``), with a *worse* first vector than the primal run — a Hermite
    factor ``||b1|| / det^(1/d)`` of 1.7944 against 1.6117, before the ``d``-th root — because the two modes do not return the same basis even when they find the same
    vector. That difference is why the mode belongs in the call and not in a convention.
    """
    engine = G6KSieveEngine(threads=1)
    basis = qary_basis(DIMENSION)
    before = matrix_rows(basis)
    result = engine.reduce(basis, BLOCK_SIZE, dual_mode=True)

    assert_same_lattice(before, result.basis)
    assert matrix_rows(basis) == before
    assert min_squared_norm(result.basis) == SHORTEST_SQUARED_NORM
    assert result.root_hermite_factor is not None and result.root_hermite_factor > 1.0


@requires_g6k
def test_a_dual_mode_run_records_the_mode_only_for_that_call():
    """Dual mode is scoped to one tour, and the engine is not left in it.

    Measured through the result rather than through G6K's internals: the same engine run twice, once
    with the keyword and once without, returns the primal basis for the second — a Hermite factor
    of 1.6117 against the dual's 1.7944. The pin is that factor's ``DIMENSION``-th root, because the
    root is what ``root_hermite_factor`` has returned since 2026-09-20; before that it returned the
    un-rooted 1.6117 under the same name, and this test pinned that.
    """
    engine = G6KSieveEngine(threads=1)
    duel = engine.reduce(qary_basis(DIMENSION), BLOCK_SIZE, dual_mode=True)
    primal = engine.reduce(qary_basis(DIMENSION), BLOCK_SIZE)
    assert duel.root_hermite_factor != primal.root_hermite_factor
    assert primal.root_hermite_factor == pytest.approx(1.6117340871180106 ** (1 / DIMENSION), rel=1e-9)


@requires_g6k
def test_an_unknown_keyword_is_refused_rather_than_ignored():
    """The mode keywords are the ones that change what was attacked, so an unrecognised one has to
    fail rather than produce a primal reduction under a dual label."""
    with pytest.raises(TypeError, match="dual"):
        G6KSieveEngine(threads=1).reduce(qary_basis(DIMENSION), BLOCK_SIZE, dual=True)


# -- the memory model ------------------------------------------------------------------------------


def test_the_database_model_is_g6ks_own():
    """``3.2 * (4/3)**(beta/2)`` entries, which is what G6K's source uses and what the plan was
    built on. Kept as the count model; it is the per-entry cost that was wrong."""
    assert sieve_db_entries(90) == pytest.approx(3.2 * (4.0 / 3.0) ** 45)
    assert sieve_db_entries(90) == pytest.approx(1.3408899e6, rel=1e-6)
    assert sieve_db_entries(20) < sieve_db_entries(40) < sieve_db_entries(90)


def test_the_memory_estimate_is_the_documented_model():
    engine = G6KSieveEngine()
    for block_size in (2, 40, 90, 100):
        expected = INTERPRETER_BASELINE_BYTES + int(
            sieve_db_entries(block_size) * SIEVE_DB_BYTES_PER_ENTRY
        )
        assert engine.estimate_memory_bytes(block_size) == expected


def test_the_memory_estimate_is_an_upper_bound_over_the_measured_peak():
    """The estimate has to be above the measured peak, or it is not a guard against a runaway.

    Measured: 231 MiB cumulative process peak at block size 90, against an estimate of 304.6 MiB —
    a ratio of 1.32. Above the measurement, and nowhere near the factor of ~10 that a bound-derived
    estimate would be allowed and would still be useless at.
    """
    estimate = G6KSieveEngine().estimate_memory_bytes(CALIBRATION_BLOCK_SIZE)
    assert estimate >= MEASURED_CUMULATIVE_PEAK_BYTES
    assert estimate / MEASURED_CUMULATIVE_PEAK_BYTES < 2.0


def test_the_corrected_constant_removes_the_over_prediction():
    """The plan's model over-predicted by ~15x and would have refused block sizes that run in 231
    MiB. Recorded as a test because the correction is the whole point of the constant, and because
    the number it replaced is the one a reader will find in the notes."""
    model = G6KSieveEngine().estimate_memory_bytes(CALIBRATION_BLOCK_SIZE)
    assert model < UNCORRECTED_MODEL_BYTES / 5
    assert SIEVE_DB_BYTES_PER_ENTRY == 160


def test_the_memory_estimate_is_monotone_in_the_block_size():
    engine = G6KSieveEngine()
    estimates = [engine.estimate_memory_bytes(beta) for beta in range(40, 100, 6)]
    assert estimates == sorted(estimates)
    assert len(set(estimates)) == len(estimates)


def test_the_memory_estimate_grows_as_the_sieve_database_does():
    """The model is a database-population model and not a fitted curve: at block size 90 the entry
    count is ``3.2 * (4/3)**45 ~ 1.34e6``, and the estimate must be dominated by it rather than by
    the interpreter baseline."""
    engine = G6KSieveEngine()
    assert engine.estimate_memory_bytes(90) - INTERPRETER_BASELINE_BYTES > 200 * (1 << 20)
    assert engine.estimate_memory_bytes(40) - INTERPRETER_BASELINE_BYTES < 1 * (1 << 20)


def test_a_non_positive_block_size_has_no_estimate():
    with pytest.raises(ValueError):
        G6KSieveEngine().estimate_memory_bytes(0)


# -- and the selector's view of it -----------------------------------------------------------------


def test_the_selector_falls_back_when_g6k_is_absent(without_g6k):
    """The end-to-end statement: absence produces a runnable engine and a recorded substitution."""
    from qlwr_lattice_stress.engines.engine_selector import FpylllBKZEngine, select_engine

    engine = select_engine({"engine": "g6k"})
    assert isinstance(engine, FpylllBKZEngine)
    assert engine.available() is True
    result = engine.reduce(qary_basis(DIMENSION), 20)
    assert result.engine == "fpylll_bkz"
    assert result.engine_version != UNAVAILABLE_VERSION
    assert result.provenance == "measured"


def test_the_fallback_leaves_the_dimension_alone(without_g6k):
    """What a fallback may not do: change the instance, so that the run stays comparable."""
    from qlwr_lattice_stress.engines.engine_selector import select_engine

    engine = select_engine({"engine": "g6k", "threads": 2})
    basis = qary_basis(DIMENSION)
    before = matrix_rows(basis)
    result = engine.reduce(basis, 20)
    assert result.dimension == DIMENSION
    assert_same_lattice(before, result.basis)
    assert result.block_size == 20


# -- the suppressed warning, and how far the suppression reaches ----------------------------------


def test_the_max_sieving_dim_warning_is_suppressed_narrowly():
    """G6K warns whenever the *lattice* is wider than ``MAX_SIEVING_DIM``, which does not bound it.

    The macro bounds the sieving block size; the check in ``siever.pyx:107`` compares it against
    ``full_n``, the lattice width. So every sweep point above dimension 100 warns on every tour
    while nothing is wrong — measured at dimension 130, where G6K recovered the exact planted vector
    at block size 70.

    Suppressed by **message**, so this test asserts both halves: G6K's warning does not reach the
    operator, and a different ``UserWarning`` still does. A suppression broad enough to hide the
    second is worse than the noise it removes.
    """
    import warnings

    from qlwr_lattice_stress.engines.g6k_sieve_engine import _max_sieving_dim_warning_explained

    g6k_message = ("Dimension of lattice is larger than maximum supported. To fix this warning, "
                   "change the value of MAX_SIEVING_DIM in siever.h and recompile.")
    other_message = "reserved_n is larger than maximum supported."

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with _max_sieving_dim_warning_explained():
            warnings.warn(g6k_message, UserWarning)
            warnings.warn(other_message, UserWarning)

    messages = [str(w.message) for w in caught]
    assert g6k_message not in messages, "the explained warning still reaches the operator"
    assert other_message in messages, (
        "the suppression is too broad: a different G6K warning was swallowed, and a warning that "
        "hides others is worse than the one it was added to remove"
    )
