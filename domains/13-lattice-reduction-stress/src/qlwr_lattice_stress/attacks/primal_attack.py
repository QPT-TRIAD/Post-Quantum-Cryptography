"""The primal (uSVP) attack: embed, reduce, check whether the planted vector came out.

Two things about this module are load-bearing and easy to get subtly wrong.

**Success is exact integer equality with the planted vector.** Not a norm comparison, not an
``allclose``, not "a vector of about the right length". A different vector of the right length is a
different vector, and the attack either found the secret or it did not. The sibling project's
integration pass found a case where two layers each computed "the size" differently and neither was
wrong alone; the same class of bug here would be an attack that appears to succeed on a vector it
did not find.

**The sweep records its failures.** ``find_minimum_successful_block_size`` returns every point it
tried, including the ones that failed. A sweep that stopped at the first success could not
distinguish "found at 30" from "found at 30 after failing everywhere below", and those are different
statements — the second is what makes the block size a *threshold* rather than an observation.
"""

from __future__ import annotations

import time

from ..lattice.basis_construction import build_primal_embedding_basis
from ..lattice.planted_vector import is_recovered, planted_short_vector
from ..lattice.primal_embedding import calibrate_embedding_factor
from ..problem.normal_form import NormalFormInstance, invert_normal_form, to_normal_form
from ..problem.qlwr_instance import LatticeQLWRInstance
from ..protocols import MEASURED, NOT_RUN, PrimalAttackResult  # noqa: F401

__all__ = [
    "prepare_primal",
    "run_primal_attack",
    "find_minimum_successful_block_size",
    "recover_secret_from_vector",
]


def prepare_primal(
    instance: LatticeQLWRInstance, *, embedding_factor: int | None = None
) -> tuple[NormalFormInstance, int, object, tuple[int, ...]]:
    """Normal form, calibrated embedding factor, embedded basis, planted vector.

    Separated from the attack so the expensive part can be built once and reduced at many block
    sizes — and so a caller can inspect the construction before paying for a reduction.
    """
    nf = to_normal_form(instance)
    factor = embedding_factor
    if factor is None:
        factor, _ = calibrate_embedding_factor(nf)
    basis = build_primal_embedding_basis(nf, embedding_factor=factor)
    planted = tuple(int(v) for v in planted_short_vector(nf, embedding_factor=factor))
    return nf, factor, basis, planted


def run_primal_attack(
    instance: LatticeQLWRInstance,
    engine,
    block_size: int,
    *,
    embedding_factor: int | None = None,
    prepared=None,
) -> PrimalAttackResult:
    """Reduce the embedded lattice at one block size and report whether the secret came out."""
    if prepared is None:
        prepared = prepare_primal(instance, embedding_factor=embedding_factor)
    nf, factor, basis, planted = prepared

    try:
        outcome = engine.reduce(basis, block_size)
    except ValueError as exc:
        # A block size the engine refuses — most often one exceeding the basis dimension, which
        # fplll accepts silently while doing something else. Recorded as a result rather than
        # raised: a refusal and a failure must not look the same in a sweep's output, and a caller
        # iterating block sizes should not have to special-case the small or large end.
        return not_run(basis, str(exc), block_size=block_size, engine=getattr(engine, "name", None))
    rows = _rows_of(outcome.basis)
    recovered = is_recovered(rows, planted)

    return PrimalAttackResult(
        dimension=basis.nrows,
        block_size=block_size,
        recovered=recovered,
        wall_clock_s=outcome.wall_clock_s,
        root_hermite_factor=outcome.root_hermite_factor,
        recovered_vector=planted if recovered else None,
        embedding_factor=factor,
        engine=outcome.engine,
        # Taken from the reduction outcome rather than from the engine, so it is the count that
        # actually ran. ``run_primal_attack`` is handed an engine it did not construct, and an
        # engine configured for four threads may have run single-threaded — fpylll ignores the
        # argument entirely. Recording the request would defeat the purpose of the field.
        threads=outcome.threads,
        provenance=MEASURED,
    )


def _rows_of(basis) -> list[list[int]]:
    return [[int(basis[i, j]) for j in range(basis.ncols)] for i in range(basis.nrows)]


def recover_secret_from_vector(
    vector, nf: NormalFormInstance, instance: LatticeQLWRInstance
) -> tuple[int, ...]:
    """Turn a recovered lattice vector back into the QLWR secret.

    The vector is ``(e', -x, M)``; the middle block is ``-x``, and ``x`` is the pivoted error that
    inverts to the secret. This is what makes the attack's output *about QLWR*: without it a test
    could pass while recovering an object with no relation to the scheme.
    """
    import dataclasses

    import numpy as np

    values = [int(v) for v in vector]
    m, n = nf.m, nf.n
    if len(values) != m + n + 1:
        raise ValueError(f"vector has length {len(values)}, expected {m + n + 1}")
    x = np.array([-int(v) for v in values[m : m + n]], dtype=np.int64)
    return invert_normal_form(dataclasses.replace(nf, x=x), instance)


def find_minimum_successful_block_size(
    instance: LatticeQLWRInstance,
    engine,
    block_size_range,
    *,
    embedding_factor: int | None = None,
    stop_after_successes: int = 1,
    max_seconds_per_block_size: float | None = None,
) -> tuple[int | None, list[PrimalAttackResult]]:
    """Sweep block sizes upward and return the smallest that recovers the secret.

    Every point is recorded and returned, including failures. The failures are the reason the
    number means anything: a minimum block size reported without them is indistinguishable from a
    sweep that started at the answer.

    ``stop_after_successes`` allows a couple of confirmations past the first success rather than
    stopping dead, since a single recovery can be luck. The default of one keeps the cost down on
    instances where the threshold is already well established.
    """
    prepared = prepare_primal(instance, embedding_factor=embedding_factor)
    embedded_basis = prepared[2]
    results: list[PrimalAttackResult] = []
    successes = 0
    minimum: int | None = None

    previous_beta: int | None = None
    previous_elapsed: float | None = None

    for block_size in sorted(block_size_range):
        # A wall-clock guard, and the reason it is here rather than in the config: enumeration cost
        # grows steeply enough that an unbounded sweep is not slow, it is *unfinishable*. Measured
        # in M1, fpylll takes 58.6 s at dimension 160 and block size 40, and the growth is roughly
        # 5.5x per ten block sizes — so block size 80 at that dimension is hours, and a sweep that
        # tries every size to the top of its range would run for days on one point.
        #
        # The projection uses the *measured* previous point rather than a model, and is deliberately
        # generous: it is a backstop against an unbounded run, not a budget to be trusted. That
        # distinction matters — the same guard in `profile_hardware.py` under-predicted by 19x and
        # still served its purpose.
        if max_seconds_per_block_size and previous_elapsed and previous_beta is not None:
            projected = previous_elapsed * (30.0 ** ((block_size - previous_beta) / 20.0))
            if projected > max_seconds_per_block_size:
                results.append(
                    not_run(
                        embedded_basis,
                        f"projected {projected:.0f}s from the measured {previous_elapsed:.1f}s at "
                        f"block size {previous_beta}, over the {max_seconds_per_block_size:.0f}s "
                        "limit. Not a failure — the point was not attempted.",
                        block_size=block_size,
                        engine=getattr(engine, "name", None),
                    )
                )
                continue

        result = run_primal_attack(instance, engine, block_size, prepared=prepared)
        results.append(result)
        if result.provenance == MEASURED:
            previous_beta, previous_elapsed = block_size, result.wall_clock_s
        if result.recovered:
            successes += 1
            if minimum is None:
                minimum = block_size
            if successes >= stop_after_successes:
                break

    return minimum, results


def not_run(
    basis, reason: str, *, block_size: int = 0, engine: str | None = None
) -> PrimalAttackResult:
    """A refusal, as a result rather than an absence.

    A sweep that silently omits a point it could not run is indistinguishable from one where the
    point succeeded — which is why the refusal carries its reason into the record.

    **It takes the embedded basis, not the instance**, and that is a correction rather than a
    signature preference. It previously took the instance and reported ``m + nu + 1`` — the width of
    the lattice you would build *without* the normal form, which is the one this project
    established contains no short vector. Refused points therefore carried a dimension 67 larger
    than the points that did run, in the same column of the same table, and section 6's anomaly text
    inherited it. The correct width was already in the caller's hand; taking it from the object the
    successful path uses makes a second formula impossible to write.

    ``threads`` is deliberately left ``None``: nothing ran, and the field means what ran rather than
    what was configured. The engine name *is* recorded, because it identifies which engine's cost
    projection produced the refusal — a reason a reader may want to check.
    """
    return PrimalAttackResult(
        dimension=basis.nrows,
        block_size=block_size,
        recovered=False,
        wall_clock_s=0.0,
        engine=engine,
        provenance=NOT_RUN,
        not_run_reason=reason,
    )
