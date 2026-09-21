"""Basis construction and stubs shared by the engine tests.

The project's own q-ary basis construction belongs to a different workstream, so the engines are
tested against a basis built here. It is the q-ary shape the project attacks, in its simplest
honest form: for a dimension ``d = nu + m``, rows ``i < nu`` are ``(e_i | A_i)`` for a random
``A`` in ``Z_q^{nu x m}``, and rows ``nu <= i`` are ``q * e_i``. Two properties are used by the
tests rather than being incidental to them:

* the determinant is **exactly** ``q**m``. The basis is block triangular with an identity block and
  a ``q * I`` block, so no cancellation is possible, and the tests can compute an independent,
  analytic root-Hermite factor to compare against the engine's Gram-Schmidt one.
* the lattice is generic — no planted short vector. A planted one is found by LLL alone, which would
  make any agreement between engines vacuous: they would be agreeing on a vector that plain LLL had
  already put in row 0. The measured behaviour of the generic instance is the opposite, and is what
  the tests below rely on: LLL returns ``min ||b_i||^2 = 223822`` at dimension 40 while the true
  shortest vector has norm ``||.||^2 = 175670``, so an engine that merely ran LLL cannot pass.

Everything is seeded through :mod:`qlwr_lattice_stress.utils.seeding`, with the draw named rather
than counted, so adding another draw anywhere does not shift this one.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from fpylll import IntegerMatrix

from qlwr_lattice_stress.engines.base_engine import ReductionEngine, TourOutcome, matrix_rows
from qlwr_lattice_stress.utils.seeding import rng_for

__all__ = [
    "CorruptingEngine",
    "NoOpEngine",
    "DEFAULT_Q",
    "matrix_rows",
    "qary_basis",
    "squared_norms",
    "min_squared_norm",
    "to_integer_matrix",
]

#: The production modulus. Held at the recorded value rather than a small one deliberately: the
#: engines are being tested at the scale the project actually uses, where the arithmetic is
#: arbitrary precision and a floating-point precision assumption would show up.
DEFAULT_Q = 1 << 16


def qary_basis(
    dimension: int = 40,
    q: int = DEFAULT_Q,
    seed: int = 0,
    label: str = "engine-test",
) -> IntegerMatrix:
    """A q-ary basis of ``dimension`` rows, with ``det = q ** (dimension // 2)`` exactly."""
    if dimension < 4 or dimension % 2:
        raise ValueError(f"dimension must be even and at least 4, got {dimension}")
    nu = dimension // 2
    m = dimension - nu
    rng = rng_for(seed, label, "qary", dimension, q)
    base = rng.integers(0, q, size=(nu, m), dtype=np.int64)
    matrix = IntegerMatrix(dimension, dimension, int_type="mpz")
    for i in range(nu):
        for j in range(m):
            matrix[i, j + nu] = int(base[i, j])
        matrix[i, i] = 1
    for j in range(m):
        matrix[nu + j, nu + j] = q
    return matrix


def to_integer_matrix(rows: Sequence[Sequence[int]]) -> IntegerMatrix:
    """An fpylll matrix holding ``rows``, for building deliberately wrong bases in a test."""
    matrix = IntegerMatrix(len(rows), len(rows[0]), int_type="mpz")
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            matrix[i, j] = int(value)
    return matrix


def squared_norms(matrix: Any) -> list[int]:
    """``||b_i||^2`` for every row, in exact integers."""
    return [sum(value * value for value in row) for row in matrix_rows(matrix)]


def min_squared_norm(matrix: Any) -> int:
    """The shortest row's squared norm — the smallest vector *in the basis*, not in the lattice."""
    return min(squared_norms(matrix))


class NoOpEngine(ReductionEngine):
    """A third engine that satisfies the interface and reduces nothing.

    Exists to show that the base class's invariants are the base class's: an engine written outside
    this package supplies a tour loop and inherits the input copy, the block-size bounds and the
    lattice-preservation check without restating any of them.
    """

    name = "noop_stub"

    @property
    def default_threads(self) -> int:
        return 1

    def unavailable_reason(self) -> str | None:
        return None

    def version(self) -> str:
        return "stub-1"

    def estimate_memory_bytes(self, block_size: int) -> int:
        return 1 << 20

    def _run_tours(self, matrix: Any, block_size: int, **kwargs: Any) -> TourOutcome:
        return TourOutcome(n_tours=1, converged=True, threads=1)


class CorruptingEngine(NoOpEngine):
    """A third engine that returns a basis of a *different* lattice.

    This is the engine the preservation test needs: it is self-consistent (square, integer, full
    rank, and it reduces perfectly well), so no check internal to it can see the problem. Only the
    boundary check can, and only if ``reduce`` actually runs it.
    """

    name = "corrupting_stub"

    def _run_tours(self, matrix: Any, block_size: int, **kwargs: Any) -> TourOutcome:
        matrix[0, 0] = int(matrix[0, 0]) + 1
        return TourOutcome(n_tours=1, converged=True, threads=1)
