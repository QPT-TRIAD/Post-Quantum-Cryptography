"""The dual attack: reduce the dual lattice, then distinguish real samples from uniform ones.

The design document asks for both attack families because the estimator reports the **minimum over
both** as the claimed security level. Testing one gives a one-sided picture, and the one-sided
picture can only ever be optimistic — it is the *easier* attack that sets security.

## Why there is always a control

Every evaluation runs the same statistic against a set of genuinely uniform samples and reports
both. A distinguisher that fires on everything — including uniform noise — is a broken distinguisher
that would otherwise read as a successful attack. The sibling project learned this the hard way: its
negative-control fixture marked two values, and a correct probe *should* have fired on it, so the
fixture could never have detected a broken probe.

The control here is a real distribution rather than a fixed array, so it can be resampled and the
statistic's behaviour under the null observed rather than assumed.

## The statistic

For a short dual vector ``y`` and the real relation ``b = A x + e' (mod q)``,

    <y, b> == <y, e'>  (mod q)

because ``A^T y == 0 (mod q)`` by construction. Since ``y`` is short and ``e'`` is small,
``|<y, e'>| <= ||y||_1 * B`` is far below ``q/2`` — so the residue is *detectably* small. A uniform
``b`` gives a uniform residue. The statistic is the fraction of samples landing inside that band,
against the fraction a uniform distribution would produce.
"""

from __future__ import annotations

import math
import time

from ..lattice.dual_embedding import DistinguisherStatistic, dual_basis, dual_distinguisher
from ..problem.qlwr_instance import LatticeQLWRInstance
from ..protocols import MEASURED, NOT_RUN, DualAttackResult

__all__ = ["run_dual_attack", "uniform_control", "short_dual_vectors"]


def short_dual_vectors(reduced_rows, nf, *, count: int) -> list[list[int]]:
    """The ``count`` shortest rows of a reduced dual basis.

    Shortness is what makes the distinguisher work — the band width is ``||y||_1 * B`` — so the
    rows are ranked by Euclidean norm and the shortest taken. ``||y||_1`` rather than ``||y||_2``
    drives the band, and the two orderings can differ; Euclidean is used for the ranking because it
    is what reduction minimises, and the band is computed exactly from ``||y||_1`` afterwards.
    """
    rows = [[int(v) for v in row] for row in reduced_rows]
    rows.sort(key=lambda r: sum(v * v for v in r))
    return rows[:count]


def uniform_control(nf, *, seed: int, n: int = 1) -> list[list[int]]:
    """``n`` genuinely uniform sample vectors in ``Z_q^m`` — the known-should-not-distinguish case.

    Usually one is enough, because the statistic is evaluated over many *dual vectors* against a
    single sample; a control sample is one more such sample. Drawn uniformly on ``Z_q`` rather than
    by shifting or rescaling the real sample, which would carry structure the statistic could latch
    onto and make the control agree for the wrong reason.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    m = nf.m
    return [list(map(int, rng.integers(0, nf.q, size=m))) for _ in range(n)]


def run_dual_attack(
    instance: LatticeQLWRInstance,
    engine,
    block_size: int,
    *,
    transformed=None,
    control_seed: int = 0x5EED,
    shortest_vectors: int | None = None,
) -> DualAttackResult:
    """Reduce the dual lattice at one block size and evaluate the distinguisher.

    ``transformed`` accepts a prepared ``(nf, dual_basis)`` pair so a sweep does not rebuild the
    normal form and the dual basis at every block size.
    """
    from ..problem.normal_form import to_normal_form

    if transformed is None:
        nf = to_normal_form(instance)
        basis = dual_basis(nf)
    else:
        nf, basis = transformed

    started = time.perf_counter()
    try:
        outcome = engine.reduce(basis, block_size)
    except ValueError as exc:
        # A block size the engine refuses — most often one exceeding the basis dimension, which
        # fplll accepts silently. A refusal is recorded as a result rather than raised: a sweep that
        # omits a point it could not run is indistinguishable from one where the point succeeded,
        # and the caller sweeping block sizes should not have to special-case the small end.
        return DualAttackResult(
            dimension=basis.nrows,
            block_size=block_size,
            advantage=0.0,
            control_advantage=0.0,
            wall_clock_s=time.perf_counter() - started,
            engine=getattr(engine, "name", None),
            provenance=NOT_RUN,
            not_run_reason=str(exc),
        )
    elapsed = time.perf_counter() - started

    rows = [[int(outcome.basis[i, j]) for j in range(outcome.basis.ncols)]
            for i in range(outcome.basis.nrows)]
    # Default to *every* row of the reduced basis, not the shortest one. The statistic is a
    # fraction over dual vectors, so a single vector gives a fraction of 0 or 1 and no distribution
    # at all. `shortest_vectors` exists for a caller that wants a cheaper, coarser estimate.
    candidates = short_dual_vectors(rows, nf, count=shortest_vectors or len(rows))

    sample = list(map(int, nf.b))
    control = uniform_control(nf, seed=control_seed)[0]

    statistic = dual_distinguisher(candidates, sample, nf, control_sample=control)

    # The band is `||y||_1 * B`. When it reaches the whole residue space the statistic cannot
    # separate anything, and reporting an advantage of zero would read as "the attack was tried and
    # found nothing" rather than "the attack does not apply here".
    #
    # Measured at nu=32, m=76: the reduced dual vectors have ||y||_1 ~ 3.3e4 against a band budget of
    # q/(2B) = 256, so the band is roughly 10^4 times too wide. The dual attack needs dual vectors
    # short enough that the band stays well inside Z_q, and at this modulus-to-noise ratio none
    # exist at any dimension reachable here. That is a finding about the parameter regime, and the
    # opposite of the primal result at the same scale.
    if statistic.expected_fraction >= 1.0:
        return DualAttackResult(
            dimension=basis.nrows,
            block_size=block_size,
            advantage=0.0,
            control_advantage=0.0,
            wall_clock_s=elapsed,
            n_samples=statistic.n_samples,
            engine=outcome.engine,
            provenance=NOT_RUN,
            not_run_reason=(
                f"the band ||y||_1*B covers the whole residue space (expected fraction "
                f"{statistic.expected_fraction:.3g}); the shortest reduced dual vector has "
                f"||y||_1 far above the q/(2B) = {nf.q // (2 * nf.noise_bound)} budget, so no dual "
                "vector can distinguish at this scale. The attack does not apply here rather than "
                "having been tried and failed."
            ),
        )

    return DualAttackResult(
        dimension=basis.nrows,
        block_size=block_size,
        advantage=statistic.advantage,
        control_advantage=statistic.control_advantage,
        wall_clock_s=elapsed,
        n_samples=statistic.n_samples,
        engine=outcome.engine,
        provenance=MEASURED,
    )
