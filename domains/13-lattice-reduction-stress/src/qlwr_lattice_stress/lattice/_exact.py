"""Exact integer linear algebra, for the checks that must not round.

Two operations, both used by the lattice checks:

* an exact determinant, which decides whether the basis spans the right volume;
* an exact solver, which decides whether the planted vector is actually an integer combination of
  the basis rows — the question the whole of M4 exists to answer.

Both are integer/rational throughout. A float determinant at these magnitudes rounds, and a
rounding determinant compared against ``q**m`` is a coin flip rather than a check. A floating
solution to ``z B = v`` would report a vector as "in the lattice" whenever it is close to one, which
is precisely the vacuous pass the planted-vector test is built to avoid.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np

__all__ = ["det_abs", "solve_integer", "NotInLattice"]


class NotInLattice(ValueError):
    """The vector is not an integer combination of the basis rows.

    Raised rather than returned as ``False`` because every caller that asks is asserting the vector
    *is* in the lattice, and a silent ``False`` would let a caller that forgot to check the result
    proceed with a vector the reduction can never find.
    """


def det_abs(matrix) -> int:
    """``|det M|`` exactly, by fraction-free (Bareiss) elimination.

    Bareiss keeps every intermediate value an integer — each division is exact — so nothing rounds
    and nothing grows faster than the determinant itself.
    """
    a = [[int(v) for v in row] for row in matrix]
    n = len(a)
    if n == 0:
        return 1
    if any(len(row) != n for row in a):
        raise ValueError("determinant requires a square matrix")

    sign = 1
    previous = 1
    for k in range(n - 1):
        if a[k][k] == 0:
            swap = next((r for r in range(k + 1, n) if a[r][k] != 0), None)
            if swap is None:
                return 0
            a[k], a[swap] = a[swap], a[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * a[k][k] - a[i][k] * a[k][j]) // previous
        previous = a[k][k]
        for i in range(k + 1, n):
            a[i][k] = 0
    return abs(sign * a[n - 1][n - 1])


def solve_integer(basis, target) -> tuple[int, ...]:
    """Solve ``z @ basis == target`` for an **integer** ``z``, or raise :class:`NotInLattice`.

    ``basis`` is given as rows, so the system is ``basis^T z = target``. Solved over the rationals
    by Gaussian elimination and then checked for integrality — never by least squares or by a
    tolerance, because a vector that is *close* to the lattice is not in it, and treating it as
    though it were is how a planted-vector test passes without proving anything.
    """
    rows = [[int(v) for v in row] for row in basis]
    n_equations = len(rows)
    if n_equations == 0:
        raise NotInLattice("empty basis")
    n_unknowns = len(rows[0])
    if any(len(r) != n_unknowns for r in rows):
        raise ValueError("basis rows must all have the same length")
    if len(target) != n_unknowns:
        raise ValueError(f"target has length {len(target)}, expected {n_unknowns}")

    # Augmented system: rows are equations over the unknowns z_i.
    # z @ basis = target  =>  sum_i z_i * basis[i][j] = target[j] for each column j.
    m = [[Fraction(rows[i][j]) for i in range(n_equations)] + [Fraction(int(target[j]))]
         for j in range(n_unknowns)]

    pivot_row = 0
    pivots: list[int] = []
    for col in range(n_equations):
        pivot = next((r for r in range(pivot_row, len(m)) if m[r][col] != 0), None)
        if pivot is None:
            continue
        m[pivot_row], m[pivot] = m[pivot], m[pivot_row]
        scale = m[pivot_row][col]
        m[pivot_row] = [v / scale for v in m[pivot_row]]
        for r in range(len(m)):
            if r != pivot_row and m[r][col] != 0:
                factor = m[r][col]
                m[r] = [a - factor * b for a, b in zip(m[r], m[pivot_row])]
        pivots.append(col)
        pivot_row += 1
        if pivot_row == len(m):
            break

    # An inconsistent row is 0 = nonzero, meaning the target is not in the span at all.
    for r in range(pivot_row, len(m)):
        if all(v == 0 for v in m[r][:n_equations]) and m[r][n_equations] != 0:
            raise NotInLattice(
                "the target is not in the span of the basis rows at all, so no integer "
                "combination can produce it"
            )

    if len(pivots) < n_equations:
        raise NotInLattice(
            f"the basis rows are linearly dependent ({len(pivots)} pivots for {n_equations} "
            "unknowns), so a unique integer solution does not exist"
        )

    solution = [Fraction(0)] * n_equations
    for i, col in enumerate(pivots):
        solution[col] = m[i][n_equations]

    non_integral = [(i, v) for i, v in enumerate(solution) if v.denominator != 1]
    if non_integral:
        i, v = non_integral[0]
        raise NotInLattice(
            f"the vector is in the rational span but not the integer lattice: coordinate {i} "
            f"solves to {v}. A vector that is close to the lattice is not in it."
        )
    return tuple(int(v) for v in solution)
