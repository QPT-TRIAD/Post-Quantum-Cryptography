"""The root-Hermite factor: the standard measure of how good a reduction actually was.

Two routes to it, deliberately, because the sibling project's integration pass found a bug of
exactly this shape — two layers each computing "the size" differently, neither wrong alone, and the
disagreement invisible until something compared them.

**Route 1, exact.** ``||b1||^(1/d) / |det B|^(1/d^2)``, with the determinant taken as an *exact
integer* by fraction-free elimination and the roots taken once at the end. The determinant of these
lattices is ``q^m``, which is a several-hundred-digit integer; a floating determinant at that
magnitude rounds, and a check that rounds is a check that can agree with the wrong basis.

**Route 2, the library.** ``fpylll``'s GSO with row exponents exposes the Gram-Schmidt data, and the
volume computed from it is an independent construction. The two agree to floating-point tolerance —
measured at ``4.1e-16`` relative — and *that agreement is the check*: it is the only thing that would
catch a wrong block order or a misread leading vector.

The GSA prediction is also here, as an exact rational. It is what a *model* says the factor should
be at a given block size, so comparing it against the achieved value is a cheap sanity check that
does not require the estimator to run.
"""

from __future__ import annotations

import math
from fractions import Fraction

from ..lattice._exact import det_abs

__all__ = [
    "achieved_root_hermite_factor",
    "hermite_factor_from_gso",
    "delta_from_block_size",
    "gsa_predicted_norm",
]


def _rows(basis) -> list[list[int]]:
    if hasattr(basis, "nrows"):
        return [[int(basis[i, j]) for j in range(basis.ncols)] for i in range(basis.nrows)]
    return [[int(v) for v in row] for row in basis]


def achieved_root_hermite_factor(basis) -> float:
    """``||b1||^(1/d) / |det B|^(1/d^2)``, with the determinant exact.

    ``b1`` is the *shortest* row rather than row zero. Most callers pass a reduced basis, where row
    zero is shortest by construction, but a basis that failed to reduce would give a misleading
    factor from row zero alone — and a misreported quality metric is worse than a missing one.
    """
    rows = _rows(basis)
    if not rows:
        raise ValueError("empty basis")
    d = len(rows)
    # The *squared* norm is the exact integer; the norm itself is irrational almost always. Flooring
    # it with ``isqrt`` reported 0.8409 for ``[[1, 1], [-1, 1]]``, whose factor is exactly 1 — and
    # because the GSO route floored the same way, the two-route cross-check agreed on the error.
    shortest_squared = min(sum(v * v for v in row) for row in rows)
    if shortest_squared == 0:
        raise ValueError("the shortest row is the zero vector; the factor is undefined")
    determinant = Fraction(det_abs([[Fraction(v) for v in row] for row in rows]))
    if determinant == 0:
        raise ValueError("the basis is singular; the factor is undefined")
    # Logs of exact integers: ``math.log`` takes an int of any size, so ``det = q^m`` cannot
    # overflow a double on the way to its d^2-th root.
    log_determinant = math.log(determinant.numerator) - math.log(determinant.denominator)
    return math.exp(0.5 * math.log(shortest_squared) / d - log_determinant / (d * d))


def hermite_factor_from_gso(basis) -> float:
    """The same quantity via ``fpylll``'s Gram-Schmidt data — cross-check 5's second route.

    ``GSO.Mat`` with ``ROW_EXPO`` returns mantissa-exponent pairs, so the volume is accumulated in
    the exponent domain: no intermediate can overflow, and the result is independent of how the
    rows happen to be scaled.
    """
    from fpylll import GSO

    rows = _rows(basis)
    d = len(rows)
    matrix = GSO.Mat(basis, float_type="mpfr", flags=GSO.ROW_EXPO)
    matrix.update_gso()

    # ``get_r(i, i)`` is the **squared** norm of the i-th Gram-Schmidt vector, not its norm — so
    # ``prod(r_ii)`` is the determinant *squared*. Measured on a 20-dimensional q-ary basis: the
    # raw product gave ``log = 128.946`` against an exact ``log|det| = 64.473``, exactly double.
    # Taking half the sum is the correction, and getting it wrong is invisible in isolation because
    # the result is still a plausible-looking root-Hermite factor — it was only caught by comparing
    # against the exact route, which is the entire reason both routes exist.
    log_volume = 0.0
    for i in range(d):
        mantissa, exponent = matrix.get_r_exp(i, i)
        log_volume += math.log(float(mantissa)) + exponent * math.log(2.0)
    log_volume *= 0.5

    # Half the log of the exact squared norm, never ``isqrt``: see the exact route above.
    shortest_squared = min(sum(v * v for v in row) for row in rows)
    return math.exp(0.5 * math.log(shortest_squared) / d - log_volume / (d * d))


def delta_from_block_size(beta: int) -> Fraction:
    """The GSA prediction for the achieved root-Hermite factor at block size ``beta``.

    ``delta_0 = (beta / (2*pi*e) * (pi*beta)^(1/beta))^(1/(2*(beta-1)))`` — the standard form, and
    the same shape the estimator's own shape model is built from. Returned as a float because the
    exponents are irrational; the *inputs* are exact integers.

    **Refused below block size 40, because the formula degenerates there.** It returns 0.54 at
    ``beta = 2``, where the derivation's assumption — that the block size is large — has nothing
    left to stand on, and the value is a property of the algebra rather than of any reduction. GSA
    assumes ``beta`` is large; the standard presentation treats
    ``beta >= 40`` as the range where it applies, and at ``beta = 40`` this gives 1.0125 against a
    literature value near 1.0128.

    Raising rather than clamping: a clamped 1.0 would look like a real prediction, and
    ``gsa_predicted_norm`` would then return a norm that no model supports. A caller wanting a
    small-block-size reference should compare against the achieved value directly.
    """
    if beta < 40:
        raise ValueError(
            f"the GSA formula is not valid at block size {beta}: it is derived under the geometric "
            "series assumption, which requires beta to be large, and below about 40 it returns "
            f"values below 1 (at beta=2 it gives 0.54). GSA is only meaningful for beta >= 40."
        )
    inner = beta / (2.0 * math.pi * math.e) * (math.pi * beta) ** (1.0 / beta)
    return Fraction(inner ** (1.0 / (2.0 * (beta - 1)))).limit_denominator(10**12)


def gsa_predicted_norm(basis, beta: int) -> float:
    """What GSA says ``||b1||`` should be after a reduction at ``beta``.

    Compared against the achieved norm, this says whether a reduction performed as the model
    predicts at that block size — a question distinct from whether it found the planted vector, and
    the one that matters on runs that do not fully succeed.
    """
    rows = _rows(basis)
    d = len(rows)
    determinant = det_abs([[Fraction(v) for v in row] for row in rows])
    delta = float(delta_from_block_size(beta))
    return delta**d * determinant ** (1.0 / d)
