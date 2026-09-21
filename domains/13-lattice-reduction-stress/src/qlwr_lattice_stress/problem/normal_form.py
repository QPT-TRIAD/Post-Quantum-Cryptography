"""The normal-form transformation: turning a uniform-secret instance into one with a short vector.

**Why this is not optional.** The corpus specifies a secret uniform on ``Z_{q_L}``. A uniform secret
has no short representative, so a Kannan embedding built on it contains **no short vector at all** —
the planted-vector test would fail, correctly, and there would be nothing for reduction to find. The
attack is necessarily on the normal form.

The estimator does the same thing for the same reason: ``lwe_primal.py`` calls
``LWEParameters.normalize(params)`` and then, when the secret is no smaller than the error, adds
``n`` dimensions "to allow for a larger embedding lattice dimension: Bai and Galbraith"
(``[ACISP:BaiGal14]``). The M2 cross-check establishes that the emulator's transformation and the
estimator's give the same block size, which is what makes the project's measured-versus-theoretical
comparison a comparison of two accounts of one lattice.

**The algebra, written out, because the sign and index conventions are where this goes silently
wrong.** Given ``b = A x + e (mod q)`` with ``A`` of shape ``m x nu``, ``x`` uniform and ``e`` small:

1. Choose ``nu`` rows of ``A`` forming ``A1``, invertible modulo ``q``; ``A2`` is the rest.
2. ``e1`` and ``e2`` are the corresponding parts of ``e``.
3. From ``b1 = A1 s - e1``, we get ``s = A1^{-1} (b1 + e1)``.
4. Substituting into the remaining rows:
   ``b2 - A2 A1^{-1} b1 = -e2 - A2 A1^{-1} e1  (mod q)``.
5. Carrying the substitution through: ``b2 = A2 A1^{-1} b1 + A2 A1^{-1} e1 - e2``, so
   ``b2 - A2 A1^{-1} b1 = +A2 A1^{-1} e1 - e2``.
6. Set ``A' = +A2 A1^{-1}``, ``b' = b2 - A2 A1^{-1} b1``, ``x = e1``, ``e' = -e2``, giving
   ``b' = A' x + e' (mod q)``.

Every one of those four signs is load-bearing and none is self-evident. ``A'`` is **positive** —
substituting ``s = A1^{-1}(b1 + e1)`` into ``b2 = A2 s - e2`` yields ``+A2 A1^{-1} e1``, and a
dropped sign there gives a transformation that still passes a consistency check on a *different*
``b'``. The check below caught exactly that, twice, on the way to this version.

**The relation carries a minus sign, and getting it wrong is invisible.** The instance defines its
error as ``e = u - b`` with ``u = <X, s> mod q``, so ``b = A s - e`` rather than ``b = A s + e``.
Deriving the normal form for a plus sign produces a transformation that is self-consistent and
wrong: the consistency check below fails immediately, which is the only reason it was caught. It is
worth stating here because nothing downstream would have looked unusual — the lattice would have
reduced, and the Hermite factor would have been a plausible number.

The other place the sign bites is the wrap case. For ``u`` near ``q``, ``round_half_up`` returns
``p`` exactly and ``target`` reduces to ``0``, so ``b = 0`` while ``e = u - q`` — the relation holds
modulo ``q`` but not as integers. The transformation is derived modulo ``q`` throughout for that
reason.

So the **secret is ``e1``** and the **error is ``-e2``** — both small, which is the whole point. The
transformation costs ``nu`` samples: ``m' = m - nu``. That cost is real and measured: at a sample
ratio below about 1.6 the estimator's models stop applying altogether (see
``notes/02-estimator.md``), and a normal form that quietly ate too many samples would manufacture
an instance nobody can attack.

**The pivot must be invertible modulo ``q``, not merely over the rationals.** At ``q = 2^16`` that
means ``det(A1)`` must be *odd*. A submatrix with an even determinant is invertible over ``Q`` and
singular over ``Z/2^16``, and picking one would produce a transformation that cannot be inverted —
so the check is ``gcd(det, q) == 1``, never ``det != 0``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .qlwr_instance import LatticeQLWRInstance, factorise

__all__ = [
    "NormalFormInstance",
    "to_normal_form",
    "invert_normal_form",
    "choose_invertible_pivot",
    "inverse_mod",
    "assert_invertible_pivot",
]


class PivotNotFound(ValueError):
    """No invertible ``nu x nu`` submatrix exists modulo ``q``.

    A real outcome rather than a bug: if every ``nu``-subset of rows is singular modulo some prime
    dividing ``q``, the base does not span and no normal form exists. Raised rather than worked
    around, because a substitute pivot would silently produce a different instance.
    """


def _rank_mod_p(rows: np.ndarray, p: int) -> int:
    """Rank over ``F_p``, by Gaussian elimination on an int64 copy."""
    a = (rows % p).astype(np.int64).copy()
    n_rows, n_cols = a.shape
    rank = 0
    for col in range(n_cols):
        pivot = None
        for r in range(rank, n_rows):
            if a[r, col] % p:
                pivot = r
                break
        if pivot is None:
            continue
        if pivot != rank:
            a[[rank, pivot]] = a[[pivot, rank]]
        inv = pow(int(a[rank, col]), -1, p)
        a[rank] = (a[rank] * inv) % p
        for r in range(n_rows):
            if r != rank and a[r, col] % p:
                a[r] = (a[r] - int(a[r, col]) * a[rank]) % p
        rank += 1
        if rank == n_rows:
            break
    return rank


def choose_invertible_pivot(
    base: np.ndarray, q: int, *, require_complement_full_rank: bool = True
) -> tuple[int, ...]:
    """Pick ``nu`` row indices whose submatrix is invertible modulo ``q``.

    Greedy on the rank modulo each prime factor. Greedy is optimal for a single prime — linear
    independence over a field is a matroid, and for the modulus this project uses (``2^16``) there
    is exactly one prime, so no search is needed. For a modulus with several prime factors the
    simultaneous requirement is an intersection of matroids, where greedy is not guaranteed
    optimal; that case is detected and reported rather than silently accepted, because a pivot that
    is independent modulo one prime and dependent modulo another is not invertible.

    The final choice is verified by ``gcd(det, q) == 1`` regardless of how it was found. The greedy
    is a heuristic for *finding* the pivot; the determinant is what decides.
    """
    m, nu = base.shape
    if m < nu:
        raise PivotNotFound(f"base is {m}x{nu}; need at least nu={nu} rows")

    primes = sorted(factorise(q))

    def greedy(order: list[int]) -> list[int]:
        """One pass over the rows in the given order, accepting a row only if it adds rank for
        every prime that still needs it.

        A row that is independent modulo one prime and dependent modulo another would leave the
        final submatrix singular modulo ``q``, whatever the individual ranks say — so acceptance is
        all-primes, not any-prime.
        """
        # An echelon basis per prime, as (pivot index, row) pairs, so elimination is a direct
        # operation and rollback is trivial. Adding rows can never lower a rank, so the only reason
        # to reject is that the row buys nothing where something is still needed.
        echelon: dict[int, list[tuple[int, np.ndarray]]] = {p: [] for p in primes}
        picked: list[int] = []
        for row in order:
            staged: dict[int, tuple[int, np.ndarray] | None] = {}
            for p in primes:
                vec = (base[row] % p).astype(np.int64).copy()
                for pivot_idx, basis_row in echelon[p]:
                    if vec[pivot_idx] % p:
                        factor = int(vec[pivot_idx]) * pow(int(basis_row[pivot_idx]), -1, p) % p
                        vec = (vec - factor * basis_row) % p
                non_zero = np.flatnonzero(vec % p)
                staged[p] = (int(non_zero[0]), vec) if non_zero.size else None
            if all(staged[p] is not None for p in primes if len(echelon[p]) < nu):
                for p in primes:
                    if staged[p] is not None and len(echelon[p]) < nu:
                        echelon[p].append(staged[p])
                picked.append(row)
                if len(picked) == nu:
                    break
        return picked

    def complement_spans(picked: list[int]) -> bool:
        """Does the *remaining* rows' matrix still have full column rank?

        Not a nicety. The normal form's transformed base is ``A' = A2 A1^{-1}``, so ``A'`` has
        exactly the rank of ``A2`` — and choosing ``nu`` rows for ``A1`` can leave a complement that
        does not span. Measured: at ``nu = 4, m = 12``, one seed in eight produces ``A'`` of rank 3
        against a needed 4.

        A rank-deficient ``A'`` is the worst kind of defect here: the relation ``b' = A' x + e'``
        still holds, ``|det B| = q^m`` still holds, and every structural check passes — while the
        lattice's short-vector structure is different and the planted vector is no longer the object
        the attack recovers. The dual lattice, which needs ``A'`` of full rank to exist at all, is
        where it surfaces.
        """
        if not require_complement_full_rank:
            return True
        rest = [i for i in range(m) if i not in set(picked)]
        if len(rest) < nu:
            return True  # fewer remaining rows than columns; nothing to require
        matrix = np.array(base[rest], dtype=np.int64)
        return min(_rank_mod_p(matrix % p, p) for p in primes) == nu

    # A single prime is a matroid, where greedy is optimal and one pass suffices — and the modulus
    # this project uses, 2^16, is exactly that case. Several primes make the requirement an
    # intersection of matroids, where greedy is *not* guaranteed to find a solution that exists.
    # Restarts are the cheap remedy: the failure is order-dependent, so a different order often
    # succeeds. The determinant check below is what actually decides, whatever the search found.
    # Restarts are needed even for a single prime, because of the complement condition rather than
    # the rank one: greedy finds a full-rank subset on the first pass for a single prime, but that
    # subset's *complement* need not span, and a different order often fixes it.
    import random as _random

    rng = _random.Random(0x5EED ^ q)
    orderings = [list(range(m))]
    for _ in range(48):
        shuffled = list(range(m))
        rng.shuffle(shuffled)
        orderings.append(shuffled)

    best: list[int] = []
    best_reason = "no ordering was attempted"
    for order in orderings:
        picked = greedy(order)
        if len(picked) < nu:
            if len(picked) > len(best):
                best = picked
                best_reason = f"only {len(picked)} independent rows found"
            continue
        if not complement_spans(picked):
            best_reason = (
                f"a full-rank pivot of {nu} rows was found, but the remaining {m - nu} rows do not "
                "span modulo q, so the transformed base A' = A2 A1^-1 would be rank-deficient. "
                "That is silent everywhere else — the relation still holds and |det B| is still "
                "q^m — while the lattice's short-vector structure is wrong."
            )
            continue
        chosen = sorted(picked)
        break
    else:
        raise PivotNotFound(
            f"no pivot of {nu} rows from {m} was found, over {len(orderings)} orderings, such that "
            f"both it is invertible and its complement spans modulo q={q}: {best_reason}. "
            "Redraw the base rather than substituting a pivot; a deficient A' produces a lattice "
            "that reduces and reports a plausible Hermite factor."
        )

    submatrix = base[chosen]
    if math.gcd(abs(_exact_det(submatrix)), q) != 1:
        raise PivotNotFound(
            f"greedy selected {nu} rows but their determinant is not coprime to q={q}; "
            "the submatrix is invertible over the rationals and singular modulo q"
        )
    return tuple(chosen)


def _exact_det(matrix: np.ndarray) -> int:
    """Exact integer determinant by fraction-free Gaussian elimination (Bareiss).

    Integer-only: a float determinant at these magnitudes would round, and a rounded determinant
    used in a coprimality test is a coin flip rather than a check.
    """
    a = [[int(v) for v in row] for row in matrix]
    n = len(a)
    sign = 1
    prev = 1
    for k in range(n - 1):
        if a[k][k] == 0:
            swap = next((r for r in range(k + 1, n) if a[r][k] != 0), None)
            if swap is None:
                return 0
            a[k], a[swap] = a[swap], a[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * a[k][k] - a[i][k] * a[k][j]) // prev
        prev = a[k][k]
        for i in range(k + 1, n):
            a[i][k] = 0
    return sign * a[n - 1][n - 1]


def _inverse_mod_prime_power(matrix: np.ndarray, p: int, exponent: int) -> np.ndarray:
    """Inverse modulo ``p**exponent``, by Gauss-Jordan with pivoting on entries coprime to ``p``.

    Works because a matrix invertible modulo ``p^k`` reduces to one invertible modulo ``p``, so
    after each elimination the remaining submatrix still has a column entry not divisible by ``p``
    and a valid pivot always exists.
    """
    q = p**exponent
    n = matrix.shape[0]
    a = (matrix % q).astype(np.int64).copy()
    inv = np.eye(n, dtype=np.int64) % q

    for col in range(n):
        pivot = next((r for r in range(col, n) if int(a[r, col]) % p), None)
        if pivot is None:
            raise ValueError(
                f"column {col} has every entry divisible by {p}, so the matrix is singular "
                f"modulo {q}. Choose an invertible pivot first."
            )
        if pivot != col:
            a[[col, pivot]] = a[[pivot, col]]
            inv[[col, pivot]] = inv[[pivot, col]]

        factor = pow(int(a[col, col]), -1, q)
        a[col] = (a[col] * factor) % q
        inv[col] = (inv[col] * factor) % q

        for r in range(n):
            if r != col and a[r, col] % q:
                f = int(a[r, col])
                a[r] = (a[r] - f * a[col]) % q
                inv[r] = (inv[r] - f * inv[col]) % q

    return inv


def inverse_mod(matrix: np.ndarray, q: int) -> np.ndarray:
    """The inverse of a square matrix modulo ``q``, for **any** modulus.

    A single prime power is handled directly. A modulus with several prime factors goes through the
    Chinese remainder theorem, and that is not optional: Gauss-Jordan over ``Z/105`` can need to
    *combine* rows to reach an invertible pivot rather than merely swap one in — ``[[3,1],[5,2]]``
    has determinant 1 and is invertible, while neither entry of its first column is invertible
    alone. Pivoting on a single entry therefore fails on matrices that are perfectly invertible, so
    the prime-power case is solved separately for each factor and the results recombined.
    """
    n = matrix.shape[0]
    factors = factorise(q)

    if len(factors) == 1:
        (p, exponent), = factors.items()
        return _inverse_mod_prime_power(matrix, p, exponent)

    residues = []
    moduli = []
    for p, exponent in sorted(factors.items()):
        pk = p**exponent
        residues.append(_inverse_mod_prime_power(matrix, p, exponent))
        moduli.append(pk)

    # CRT coefficient-wise: for each entry, find the value that reduces to every residue.
    inv = np.zeros((n, n), dtype=np.int64)
    for i in range(n):
        for j in range(n):
            value, modulus = int(residues[0][i, j]) % moduli[0], moduli[0]
            for r, m in zip(residues[1:], moduli[1:]):
                # Solve value + modulus*t == r[i,j] (mod m) for t, then merge.
                rhs = (int(r[i, j]) - value) % m
                step = (rhs * pow(modulus % m, -1, m)) % m
                value = value + modulus * step
                modulus *= m
            inv[i, j] = value % q
    return inv


@dataclass(frozen=True, slots=True)
class NormalFormInstance:
    """``b = A x + e (mod q)`` with **both** ``x`` and ``e`` small.

    Produced from a :class:`~qlwr_lattice_stress.problem.qlwr_instance.LatticeQLWRInstance` by
    :func:`to_normal_form`. The relation to the original is exact and invertible, which is what lets
    a recovered vector be turned back into the secret the QLWR relation is actually about.

    Attributes:
        n: the secret dimension, ``nu`` in the original instance.
        q: the modulus, unchanged.
        m: the number of remaining samples, ``m - nu`` in the original instance.
        a: the transformed ``m x n`` base, modulo ``q``.
        b: the transformed target, modulo ``q``.
        x: the small secret — the original instance's pivoted errors ``e1``.
        e: the small error — the original instance's remaining errors ``e2``.
        noise_bound: the half-width of the interval both ``x`` and ``e`` lie in.
        pivot_rows: the original rows the pivot was taken from, so the transformation can be undone.
        source_seed: carried so a result can be traced to the instance that produced it.
    """

    n: int
    q: int
    m: int
    a: np.ndarray
    b: np.ndarray
    x: np.ndarray
    e: np.ndarray
    noise_bound: int
    pivot_rows: tuple[int, ...]
    source_seed: int = 0

    def __post_init__(self) -> None:
        if self.a.shape != (self.m, self.n):
            raise ValueError(f"a has shape {self.a.shape}, expected ({self.m}, {self.n})")
        if self.b.shape != (self.m,):
            raise ValueError(f"b has shape {self.b.shape}, expected ({self.m},)")
        if self.x.shape != (self.n,):
            raise ValueError(f"x has shape {self.x.shape}, expected ({self.n},)")
        if self.e.shape != (self.m,):
            raise ValueError(f"e has shape {self.e.shape}, expected ({self.m},)")
        if len(self.pivot_rows) != self.n:
            raise ValueError(f"pivot_rows has {len(self.pivot_rows)} entries, expected {self.n}")

    def check(self) -> None:
        """``A x + e == b (mod q)``, in exact integers. The instance's defining identity."""
        lhs = (self.a @ self.x + self.e) % self.q
        if not np.array_equal(lhs, self.b % self.q):
            worst = int(np.max(np.abs((lhs - self.b) % self.q)))
            raise AssertionError(
                f"normal form is inconsistent: (A x + e - b) mod q has maximum {worst}. "
                "Every downstream result would describe a different instance."
            )

    def check_small(self) -> None:
        """Both the secret and the error are small.

        This is the property that makes the instance attackable at all: if either were large, the
        embedding would contain no short vector and the planted-vector test would fail for a reason
        that looked like a bug in the lattice construction.

        The bound is the symmetric interval ``[-B, B]`` rather than the original error's exact
        ``[-B, B-1]``. The transformation negates one of the two vectors — the relation requires it
        — and negating ``[-B, B-1]`` gives ``[-(B-1), B]``. Both have width ``2B``; the symmetric
        closure contains both, and asserting the narrower interval would fail on a legitimate
        instance for a reason that has nothing to do with the lattice.
        """
        bound = self.noise_bound
        for name, vec in (("x", self.x), ("e", self.e)):
            if np.any(vec < -bound) or np.any(vec > bound):
                lo, hi = int(vec.min()), int(vec.max())
                raise AssertionError(
                    f"{name} spans [{lo}, {hi}], outside the small interval [{-bound}, {bound}]"
                )

    def describe(self) -> dict:
        return {
            "n": self.n,
            "q": self.q,
            "m": self.m,
            "noise_bound": self.noise_bound,
            "noise_interval": [-self.noise_bound, self.noise_bound - 1],
            "pivot_rows": list(self.pivot_rows),
            "source_seed": self.source_seed,
            "samples_consumed": self.n,
        }


def to_normal_form(instance: LatticeQLWRInstance) -> NormalFormInstance:
    """Transform a uniform-secret QLWR instance into a small-secret, small-error one.

    Exact integer arithmetic throughout. The transformation consumes ``nu`` samples, which is
    reported rather than hidden — an instance that arrives at the lattice construction with too few
    samples to attack is a fact about the instance, not a detail of the implementation.
    """
    q = instance.q_l
    nu = instance.nu
    base = np.array(instance.base, dtype=np.int64)
    # The lifted samples, in Z_q. These are the b of b = A s + e.
    b_full = np.array(instance.public_samples(), dtype=np.int64) % q
    e_full = np.array(instance.error_vector(), dtype=np.int64)

    pivot = choose_invertible_pivot(base, q)
    rest = tuple(i for i in range(instance.m) if i not in set(pivot))

    a1 = base[list(pivot)]
    a2 = base[list(rest)]
    b1 = b_full[list(pivot)]
    b2 = b_full[list(rest)]
    e1 = e_full[list(pivot)]
    e2 = e_full[list(rest)]

    a1_inv = inverse_mod(a1, q)
    # A' = +A2 A1^{-1} and b' = b2 - A2 A1^{-1} b1, both modulo q. Derived in the module docstring;
    # the four signs there are each load-bearing and were each worth a failed check to establish.
    t = (a2 @ a1_inv) % q
    a_prime = t % q
    b_prime = (b2 - t @ b1) % q

    nf = NormalFormInstance(
        n=nu,
        q=q,
        m=instance.m - nu,
        a=a_prime % q,
        b=b_prime % q,
        # The secret of the transformed instance is the original's pivoted error...
        x=e1,
        # ...and its error is the *negated* remaining error, because the relation carries a minus
        # sign. See the module docstring: deriving this for `b = A s + e` gives a transformation
        # that is self-consistent and describes the wrong instance.
        e=-e2,
        noise_bound=instance.noise_bound,
        pivot_rows=pivot,
        source_seed=instance.seed,
    )
    nf.check()
    # A negative control has uniform samples, so its residuals are spread over all of ``Z_q`` and
    # ``check_small`` would refuse it. The refusal would be *true* — nothing small is in there — but
    # it would also turn every control point into a not-run, and "the attack was refused" is not the
    # statement a control exists to make: "the attack ran, at the same block sizes, and recovered
    # nothing" is. So the control goes through with ``x`` and ``e`` as large as they are; ``check()``
    # above still holds, because the relation is an identity in the residual.
    if not instance.is_control:
        nf.check_small()
    return nf


def invert_normal_form(nf: NormalFormInstance, instance: LatticeQLWRInstance) -> tuple[int, ...]:
    """Recover the original secret from the transformed instance's small secret.

    ``s = A1^{-1} (b1 + x)`` with ``x = e1`` — a **plus**, because the relation is ``b = A s - e``.
    This is what makes the attack's output *about QLWR* rather than about a generic LWE instance: a
    recovered short vector yields ``e1``, and ``e1`` yields the secret the relation is defined on.
    Without this step a test could pass while recovering an object that has nothing to do with the
    scheme.
    """
    q = instance.q_l
    base = np.array(instance.base, dtype=np.int64)
    b_full = np.array(instance.public_samples(), dtype=np.int64) % q

    a1 = base[list(nf.pivot_rows)]
    b1 = b_full[list(nf.pivot_rows)]
    a1_inv = inverse_mod(a1, q)

    s = (a1_inv @ ((b1 + nf.x) % q)) % q
    return tuple(int(v) for v in s)


def assert_invertible_pivot(base: np.ndarray, rows: tuple[int, ...], q: int) -> None:
    """Check a caller-supplied pivot is actually invertible modulo ``q``.

    Separated from the search so a pivot can be pinned in a test or a config and still be checked.
    ``gcd(det, q) == 1``, never ``det != 0``: over ``Z/2^16`` an even determinant means singular,
    and a pivot that is invertible over the rationals but not modulo ``q`` produces a transformation
    that cannot be undone.
    """
    submatrix = np.array(base, dtype=np.int64)[list(rows)]
    if submatrix.shape[0] != submatrix.shape[1]:
        raise ValueError(f"pivot must be square, got shape {submatrix.shape}")
    det = _exact_det(submatrix)
    if math.gcd(abs(det), q) != 1:
        raise ValueError(
            f"det={det} is not coprime to q={q}; this pivot is invertible over the rationals and "
            "singular modulo q, so the normal form could not be inverted"
        )
