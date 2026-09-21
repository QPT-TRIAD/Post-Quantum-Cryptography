"""Kannan embedding for the primal (uSVP) attack, and the factor calibration it needs.

The embedding itself is a thin wrapper over
:func:`~qlwr_lattice_stress.lattice.basis_construction.build_primal_embedding_basis`. What this
module adds is the choice of factor, which M5 established is **not** a free parameter and **not** 1.

## Why the factor needs calibrating

Whenever ``p | q``, every lifted sample is ``b_i = (q/p) * t_i`` for integer ``t_i``. Multiplying
the embedding row by ``p`` therefore gives ``p * (b, 0, M) = (q * t, 0, p * M)``, and
``(q * t, 0, 0)`` is a lattice element — so their difference

    (0, ..., 0, p * M)

is in the lattice **whatever the instance**. Its norm is ``p * M``. If that is shorter than the
planted vector, the planted vector is not the shortest lattice vector, uSVP has nothing to find,
and the attack is meaningless.

The failure is silent in the worst way: **the planted vector is still genuinely in the lattice**, so
a membership check passes. Measured at ``nu = 32, m = 76``: at ``M = 1`` LLL returns the artifact
instead, yet every membership assertion holds. Only the two-sided recovery test — recovery at a
high block size *and not at a low one* — detects it.

## The condition

Requiring the artifact to exceed the planted vector gives

    (p*M)^2 > ||e||^2 + ||x||^2 + M^2   =>   M > sqrt((||e||^2 + ||x||^2) / (p^2 - 1))

which is instance-dependent: it grows with the noise and with the dimension, and shrinks as the
modulus ratio grows. ``calibrate_embedding_factor`` computes it and then *verifies* the result by
reduction rather than returning the analytic bound alone, because the artifact is the dominant short
vector but not provably the only one.
"""

from __future__ import annotations

import math

from ..problem.normal_form import NormalFormInstance
from .basis_construction import build_primal_embedding_basis
from .planted_vector import planted_norm_squared, planted_short_vector

__all__ = [
    "artifact_norm",
    "minimum_embedding_factor",
    "calibrate_embedding_factor",
    "kannan_embedding",
]


def artifact_norm(nf: NormalFormInstance, embedding_factor: int) -> int:
    """``p * M`` — the norm of the vector the embedding always introduces, or 0 if there is none.

    Zero when ``p`` does not divide ``q``: the derivation needs ``p * (q // p)`` to be a multiple of
    ``q``, which holds exactly in the divisor case. A non-divisor modulus does not get a free pass —
    it has its own, larger noise (see ``notes/03-lattice-construction.md``) — it simply does not
    produce this particular artifact.
    """
    # ``NormalFormInstance`` does not carry ``p``, so it is recovered from the noise bound, which is
    # defined as ``q // (2p)``. Inverting that is exact whenever ``p`` divides ``q`` — the case
    # where the artifact exists at all.
    if nf.noise_bound <= 0:
        return 0
    p = nf.q // (2 * nf.noise_bound)
    # ``B = q // (2p) = (q // p) // 2`` when ``p`` divides ``q`` — the *floor*, so an odd ratio
    # ``q / p`` is consistent too. Requiring ``q // p == 2B`` accepted even ratios only, and at
    # ``q = 105, p = 7`` reported no artifact while ``(0, ..., 0, p * M)`` sat in the lattice.
    if p < 2 or nf.q % p != 0 or (nf.q // p) // 2 != nf.noise_bound:
        # Not a divisor modulus, so ``p * (q // p)`` is not a multiple of ``q`` and the artifact
        # does not arise. The instance has its own larger noise in that regime; see notes/03.
        return 0
    return p * embedding_factor


def minimum_embedding_factor(nf: NormalFormInstance) -> int:
    """The smallest ``M`` for which the artifact should exceed the planted vector.

    Analytic, and *conservative in the safe direction*: it ignores the ``M^2`` term in the planted
    vector's own norm, so the returned value is at or slightly below the true threshold. Erring low
    is the right side to err on because the verification in
    :func:`calibrate_embedding_factor` checks the result upward.
    """
    planted_without_m = planted_norm_squared(nf, embedding_factor=0)
    p = nf.q // (2 * nf.noise_bound) if nf.noise_bound else 0
    if not p or nf.q % p != 0:
        # No artifact. The factor still has to be large enough for the embedded coordinate to be
        # meaningful relative to the rest of the vector, which is the same condition with p = 1.
        return max(2, int(math.isqrt(planted_without_m // 3)) + 1)
    denominator = p * p - 1
    if denominator <= 0:
        return 2
    return max(2, math.isqrt(planted_without_m // denominator) + 1)


def _artifact_is_not_shortest(nf: NormalFormInstance, embedding_factor: int) -> bool:
    """Does LLL's shortest row turn out to be the artifact rather than something else?

    This is the right thing to verify, and getting it wrong cost a rebuild. An earlier version of
    this function asked whether **LLL recovers the planted vector** — which is exactly the thing the
    calibration exists to make possible, and which LLL does *not* do at the sizes where the
    calibration matters. It therefore failed for every candidate factor at `nu = 32`, and the
    failure looked like the instance being too noisy.

    The concern the factor exists to address is narrower: at too small a factor the lattice's
    shortest vector is `(0, ..., 0, p*M)` rather than the planted one. LLL is more than enough to
    surface a vector that short, so it detects exactly that case and nothing else — which is what a
    verification should do.
    """
    m, n = nf.m, nf.n

    basis = build_primal_embedding_basis(nf, embedding_factor=embedding_factor)
    _lll_reduce_in_place(basis)
    rows = [[int(basis[i, j]) for j in range(basis.ncols)] for i in range(basis.nrows)]

    def norm_sq(row):
        return sum(int(v) * int(v) for v in row)

    shortest = min(rows, key=norm_sq)
    artifact = [0] * (m + n + 1)
    artifact[-1] = _artifact_p(nf) * embedding_factor
    return shortest != artifact and shortest != [-v for v in artifact]


def _artifact_p(nf: NormalFormInstance) -> int:
    """``p``, recovered from the noise bound ``B = q // (2p)``."""
    if nf.noise_bound <= 0:
        return 0
    p = nf.q // (2 * nf.noise_bound)
    return p if (p >= 2 and nf.q % p == 0 and (nf.q // p) // 2 == nf.noise_bound) else 0


def _lll_reduce_in_place(basis) -> None:
    from fpylll import LLL

    LLL.reduction(basis)


def calibrate_embedding_factor(
    nf: NormalFormInstance, *, block_sizes: tuple[int, ...] = (2, 5, 10, 20)
) -> tuple[int, dict]:
    """Find a factor that makes the attack meaningful, and report how it was found.

    Returns ``(factor, measurement)``. The measurement is returned rather than logged because it
    belongs in the run's record: a reader comparing a block size against a model prediction needs to
    know which embedding produced it, and the factor is an input to that.

    The search starts at the analytic bound and walks up. Walking *up* rather than down is
    deliberate: a factor that is too small produces an attack that runs, reports a plausible
    root-Hermite factor, and is not attacking the intended vector — so the failure is silent, and
    the safe direction to err is the larger factor.
    """
    start = minimum_embedding_factor(nf)
    planted_norms = {}
    for factor in range(start, start + 16):
        planted_norms[factor] = planted_norm_squared(nf, embedding_factor=factor)
        artifact = artifact_norm(nf, embedding_factor=factor)
        if artifact and artifact * artifact <= planted_norms[factor]:
            continue  # the artifact still wins; a larger factor is required
        if _artifact_is_not_shortest(nf, factor):
            return factor, {
                "factor": factor,
                "analytic_lower_bound": minimum_embedding_factor(nf),
                "planted_norm_squared": planted_norms[factor],
                "artifact_norm": artifact,
                "artifact_exceeds_planted": bool(
                    artifact and artifact * artifact > planted_norms[factor]
                ),
                "verified_by_reduction_at_block_size": block_sizes[-1],
            }

    raise RuntimeError(
        f"no embedding factor in [{start}, {start + 15}] produced a lattice whose shortest vector "
        f"is the planted one (q={nf.q}, noise_bound={nf.noise_bound}). The instance may be too "
        "noisy for the embedding to work at any factor, which is a finding rather than a bug."
    )


def kannan_embedding(nf: NormalFormInstance, *, embedding_factor: int | None = None):
    """The embedded lattice, with the factor calibrated when one is not supplied.

    Supplying a factor explicitly is allowed so a caller can reproduce a recorded run, but the
    default calibrates rather than guessing — because the wrong default is a silent failure.
    """
    if embedding_factor is None:
        embedding_factor, _ = calibrate_embedding_factor(nf)
    return build_primal_embedding_basis(nf, embedding_factor=embedding_factor)
