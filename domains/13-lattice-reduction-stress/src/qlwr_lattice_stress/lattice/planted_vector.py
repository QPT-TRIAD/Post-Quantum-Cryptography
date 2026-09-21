"""The short vector an attacker is looking for, and the check that it is really there.

This module is the project's cheapest and earliest falsifier, and the design document is explicit
that nothing may be built on top of it until it passes: *"do not proceed past this step until this
test passes reliably."*

The reason is that every other check in the project is downstream of the lattice being right. A
wrong lattice reduces perfectly, produces a plausible root-Hermite factor, and yields a curve that
looks like a result. The only thing that distinguishes it is whether the vector the attack is
*supposed* to find is actually in the lattice — and that question is answered by one exact rational
solve, in seconds, at any dimension, with no reduction run at all.

**The planted vector.** For a normal-form instance ``b = A x + e (mod q)``, the embedded lattice
contains ``(b, 0, M)`` (a basis row) and ``(b - e, x, 0)`` (shown in
:mod:`~qlwr_lattice_stress.lattice.basis_construction`). Their difference

    ``(e, -x, M)``

is in the lattice, and it is short precisely because the normal form made both ``e`` and ``x``
small. That vector — not a norm threshold, not a nearby vector — is what the attack must return.

**Why membership is checked exactly.** ``z B = v`` is solved over the rationals and checked for
integrality. A least-squares or tolerance-based answer would report a vector as "in the lattice"
whenever it is close to one, which is exactly the vacuous pass this test exists to prevent.
"""

from __future__ import annotations

import numpy as np

from ..problem.normal_form import NormalFormInstance
from ._exact import NotInLattice, solve_integer

__all__ = [
    "planted_short_vector",
    "assert_in_lattice",
    "is_recovered",
    "recovered_from_coordinates",
    "planted_norm_squared",
]


def planted_short_vector(nf: NormalFormInstance, *, embedding_factor: int) -> np.ndarray:
    """``(e, -x, M)``, as an integer vector over the embedded basis's coordinates.

    Computed from the instance's own recorded ``x`` and ``e`` — the ground truth — and never
    inferred from a reduction. If this vector is not in the lattice, the construction is wrong and
    the failure is localised to one module because nothing else has run yet.

    The signs follow from the difference ``(b, 0, M) - (b - e, x, 0)``. The design document's
    sketch writes it as ``(-e, x, -M)``; that is the same vector multiplied by ``-1``, and since a
    lattice is closed under negation, either is a valid planted vector. The test compares up to
    sign for exactly that reason, rather than pinning a convention that carries no information.
    """
    n, m = nf.n, nf.m
    vector = np.zeros(m + n + 1, dtype=object)
    vector[:m] = [int(v) for v in nf.e]
    vector[m : m + n] = [-int(v) for v in nf.x]
    vector[m + n] = int(embedding_factor)
    return vector


def planted_norm_squared(nf: NormalFormInstance, *, embedding_factor: int) -> int:
    """``||(e, -x, M)||^2`` as an exact integer, for comparing against an enumerated shortest."""
    v = planted_short_vector(nf, embedding_factor=embedding_factor)
    return int(sum(int(x) * int(x) for x in v))


def assert_in_lattice(vector, basis) -> tuple[int, ...]:
    """Assert ``vector`` is an **integer** combination of ``basis`` rows; return the coordinates.

    The exact solve is the whole point. Nothing here uses a norm, a tolerance, or a nearest-plane
    approximation: a vector that is nearly in the lattice is not in it, and the difference is the
    difference between a test that means something and one that always passes.
    """
    return solve_integer(_as_rows(basis), vector)


def recovered_from_coordinates(coordinates, basis) -> tuple[int, ...]:
    """The lattice vector a set of coordinates denotes, recomputed from the basis.

    Used to confirm that a vector found inside a *reduced* basis really is the planted one rather
    than merely having the right norm — a reduced basis has different rows, so a row index means
    nothing across bases and only the vector itself does.
    """
    rows = _as_rows(basis)
    coords = [int(c) for c in coordinates]
    if len(coords) != len(rows):
        raise ValueError(f"{len(coords)} coordinates for {len(rows)} basis rows")
    return tuple(
        int(sum(coords[i] * rows[i][j] for i in range(len(rows))))
        for j in range(len(rows[0]))
    )


def _as_rows(basis) -> list[list[int]]:
    """A basis as a list of integer rows, from either a sequence or an ``fpylll`` matrix.

    Both forms appear — the construction returns an ``IntegerMatrix`` because that is what the
    engines consume, while tests and small hand-built cases use nested lists — and a helper that
    accepted only one would make the other look like a bug in the vector rather than the input.
    """
    if hasattr(basis, "nrows"):
        return [
            [int(basis[i, j]) for j in range(basis.ncols)] for i in range(basis.nrows)
        ]
    return [[int(v) for v in row] for row in basis]


def is_recovered(reduced_basis, planted, *, require_exact: bool = True) -> bool:
    """Does a row of ``reduced_basis`` equal ``+planted`` or ``-planted``?

    **Exact integer equality, never a norm comparison.** A vector of the right length is a different
    vector, and a test that accepted one would pass on a basis that had found something else
    entirely — which is the failure mode the negative assertion at low block size exists to catch.
    """
    planted = [int(v) for v in planted]
    negated = [-v for v in planted]
    rows = reduced_basis
    if hasattr(reduced_basis, "nrows"):
        rows = [
            [int(reduced_basis[i, j]) for j in range(reduced_basis.ncols)]
            for i in range(reduced_basis.nrows)
        ]
    for row in rows:
        values = [int(v) for v in row]
        if values == planted or values == negated:
            return True
        if not require_exact and len(values) == len(planted):
            # Explicitly opt-in only. Present so that a caller can record how close a run came
            # without being able to mistake that for recovery.
            if sum(abs(a - b) for a, b in zip(values, planted)) <= 1:
                return True
    return False
