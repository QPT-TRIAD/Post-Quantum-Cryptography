"""The QLWR relation in exact integer arithmetic — the lattice project's instance type.

This is deliberately **not** the sibling Grover project's ``QLWRInstance``, and the reason is
concrete rather than stylistic. That type requires ``q_l`` and ``p`` to be *generic primes* and
rejects powers of two, Mersenne and Fermat forms — a constraint that exists so a quantum gate-count
fit is not an artefact of a lucky modulus. The recorded production parameter set uses
``q_L = 2^16`` and ``p = 2^8``. Reusing that type would mean attacking a different instance than the
one on record, and the difference would be invisible: a lattice over a nearby prime modulus reduces
just as well and reports a plausible Hermite factor.

Two constraints from the sibling do carry over unchanged, because they are about the *relation*
rather than the quantum accounting:

* the base must have full column rank over ``Z_{q_l}``. A rank-deficient base makes ``s -> Xs``
  non-injective, which is a different (and much easier) problem.
* all arithmetic is exact. A float anywhere in basis construction produces a basis for a different
  lattice without raising.

One thing this module deliberately does **not** do is compute a marked set. The Grover project
counts it by brute force over ``2^(nu*w)`` states, which is fine at nu=2 and four thousand
iterations and impossible at nu=50. Lattice reduction does not care about the marked set at all:
the attack is on the lattice, and the secret is a short vector rather than a unique preimage. So
the expensive quantum-search accounting is absent here by design, not by omission.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = [
    "LatticeQLWRInstance",
    "round_half_up",
    "full_column_rank_mod",
    "is_prime",
    "factorise",
]


def round_half_up(numerator: int, denominator: int) -> int:
    """``round(numerator / denominator)`` exactly, halves away from zero, in integers.

    Written as ``(2a + b) // (2b)`` rather than ``round(a / b)`` because the latter goes through a
    float, and at ``q_l = 2^16`` with ``nu = 256`` the products exceed what a double represents
    exactly. The rounding *is* the relation; computing it in floating point would change which
    lattice is being attacked.
    """
    if denominator <= 0:
        raise ValueError(f"denominator must be positive, got {denominator}")
    return (2 * numerator + denominator) // (2 * denominator)


def is_prime(n: int) -> bool:
    """Deterministic Miller-Rabin for the magnitudes this project uses."""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def factorise(n: int) -> dict[int, int]:
    """Prime factorisation by trial division, with Pollard rho for the remaining cofactor.

    Only ever called on a modulus, and only to decide the rank criterion below, so it does not need
    to be fast — it needs to be *correct*, because a wrong factorisation would silently accept a
    rank-deficient base.
    """
    if n < 2:
        raise ValueError(f"cannot factorise {n}")
    factors: dict[int, int] = {}
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47):
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    while n > 1 and not is_prime(n):
        d = _pollard_rho(n)
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def _pollard_rho(n: int) -> int:
    import random as _random

    if n % 2 == 0:
        return 2
    rng = _random.Random(0xC0FFEE ^ n)
    while True:
        c = rng.randrange(1, n)
        x = y = rng.randrange(2, n)
        d = 1
        while d == 1:
            x = (x * x + c) % n
            y = (y * y + c) % n
            y = (y * y + c) % n
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d


def _rank_mod_p(rows: list[list[int]], p: int) -> int:
    """Rank of a matrix over the field ``F_p``.

    A *prime* modulus only, so that every non-zero pivot is invertible — which is what makes
    Gaussian elimination valid. The sibling project's helper of this name is called with
    ``q_l = 2^16`` in mind by mistake; here it is only ever reached through
    :func:`full_column_rank_mod`, which hands it a prime.
    """
    if not rows:
        return 0
    a = [[v % p for v in row] for row in rows]
    n_rows, n_cols = len(a), len(a[0])
    rank = 0
    for col in range(n_cols):
        pivot = next((r for r in range(rank, n_rows) if a[r][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        inv = pow(a[rank][col], -1, p)
        a[rank] = [(v * inv) % p for v in a[rank]]
        for r in range(n_rows):
            if r != rank and a[r][col]:
                factor = a[r][col]
                a[r] = [(a[r][c] - factor * a[rank][c]) % p for c in range(n_cols)]
        rank += 1
        if rank == n_rows:
            break
    return rank


def full_column_rank_mod(rows: list[list[int]], q: int, n_cols: int | None = None) -> int:
    """Rank of a matrix over ``Z/q``, for **any** modulus ``q``, prime or not.

    This is the function that must not be replaced by the sibling project's prime-only helper. That
    one computes ``pow(a, -1, q)`` for a pivot, which does not exist when ``q`` is even — and at
    ``q_l = 2^16`` that is every pivot that is not odd.

    The criterion is by the Chinese remainder theorem: a matrix over ``Z/q`` is surjective if and
    only if its reduction is surjective modulo every prime power dividing ``q``, and over
    ``Z/p^k`` if and only if it is surjective modulo ``p``. So the rank is taken modulo each prime
    factor of ``q`` — where every pivot is invertible — and the minimum is the answer. For
    ``q = 2^16`` this reduces to the rank of ``A mod 2`` over ``F_2``, which is exact and costs
    almost nothing.
    """
    if q < 2:
        raise ValueError(f"modulus must be at least 2, got {q}")
    if not rows:
        return 0
    cols = n_cols if n_cols is not None else len(rows[0])
    ranks = []
    for prime in factorise(q):
        ranks.append(_rank_mod_p([row[:cols] for row in rows], prime))
    return min(ranks)



def _require_integer(name: str, value: object) -> None:
    """Refuse anything that is not a plain integer — ``numpy`` integers count, ``bool`` does not."""
    import numbers

    if isinstance(value, bool) or not isinstance(value, numbers.Integral):
        raise TypeError(
            f"{name}={value!r} is a {type(value).__name__}; the instance is exact-integer only"
        )


@dataclass(frozen=True, slots=True)
class LatticeQLWRInstance:
    """One instantiation of the QLWR relation, with the secret the lattice attack will hunt for.

    The relation is ``F_s(X)_i = round_half_up((sum_j X_ij s_j mod q_l) * p, q_l) mod p``, exactly as
    the corpus defines it. The public sample an attacker sees is ``b_i = (q_l // p) * F_s(X)_i``,
    which is the rounded value lifted back into ``Z_{q_l}`` — the form in which the rounding error
    is a small signed offset rather than a residue.

    Attributes:
        nu: dimension of the secret.
        q_l: the large modulus. Prime *or* a power of two — see the module docstring.
        p: the rounding modulus. Must divide ``q_l`` or be prime; see ``__post_init__``.
        m: number of rows of the public base, hence the number of samples.
        secret_s: the secret, ``nu`` values in ``[0, q_l)``.
        base: the public ``m x nu`` matrix over ``Z_{q_l}``, row-major.
        seed: the seed that produced this instance, so a run is reproducible from its record.
        label: which instance source produced it, for the report's provenance block.
        control_samples: ``None`` for every planted instance. When set, these ``m`` values **are**
            the public samples, and nothing derives them from ``secret_s`` — the negative control.
            See :attr:`is_control`.
    """

    nu: int
    q_l: int
    p: int
    m: int
    secret_s: tuple[int, ...]
    base: tuple[tuple[int, ...], ...]
    seed: int = 0
    label: str = "synthetic_scaled"
    #: Last and defaulted, so every existing construction site builds exactly what it built before.
    control_samples: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        # Integers only, and checked before anything is compared: a float secret satisfies every
        # range test below, and then ``target`` and ``error_vector()`` come back as floats — a
        # basis built from them is a basis for some other lattice, and nothing downstream objects.
        # ``bool`` is refused by name because it *is* an ``int`` to ``isinstance``.
        for name in ("nu", "q_l", "p", "m", "seed"):
            _require_integer(name, getattr(self, name))
        for index, value in enumerate(self.secret_s):
            _require_integer(f"secret_s[{index}]", value)
        for r, row in enumerate(self.base):
            for c, value in enumerate(row):
                _require_integer(f"base[{r}][{c}]", value)

        if self.q_l < 2:
            raise ValueError(f"q_l={self.q_l} must be at least 2")
        if self.p < 2:
            raise ValueError(f"p={self.p} must be at least 2")
        if self.p > self.q_l:
            raise ValueError(f"p={self.p} exceeds q_l={self.q_l}; the rounding would be lossless")
        if not (self.q_l % self.p == 0 or is_prime(self.p)):
            raise ValueError(
                f"p={self.p} neither divides q_l={self.q_l} nor is prime; the sample lift "
                "q_l // p would not be exact"
            )
        if self.nu < 1 or self.m < 1:
            raise ValueError(f"nu={self.nu} and m={self.m} must both be positive")
        if len(self.secret_s) != self.nu:
            raise ValueError(f"secret_s has {len(self.secret_s)} entries, expected nu={self.nu}")
        if any(not 0 <= v < self.q_l for v in self.secret_s):
            raise ValueError("secret_s has an entry outside [0, q_l)")
        if len(self.base) != self.m:
            raise ValueError(f"base has {len(self.base)} rows, expected m={self.m}")
        if any(len(row) != self.nu for row in self.base):
            raise ValueError(f"every base row must have nu={self.nu} entries")

        rank = full_column_rank_mod([list(r) for r in self.base], self.q_l, self.nu)
        if rank != self.nu:
            raise ValueError(
                f"base has column rank {rank} over Z/{self.q_l}, need {self.nu}. A rank-deficient "
                "base makes s -> Xs non-injective, which is a different and much easier problem."
            )

        if self.control_samples is not None:
            # A control's samples have to be *possible* samples — lifted values ``(q_l // p) * v``
            # with ``v`` in ``Z_p`` — or the control differs from a planted instance in its support
            # as well as in its structure, and an attack could tell them apart for the wrong reason.
            if len(self.control_samples) != self.m:
                raise ValueError(
                    f"control_samples has {len(self.control_samples)} entries, expected m={self.m}"
                )
            for index, value in enumerate(self.control_samples):
                _require_integer(f"control_samples[{index}]", value)
                if value % self.rounding_ratio or not 0 <= value // self.rounding_ratio < self.p:
                    raise ValueError(
                        f"control_samples[{index}]={value} is not (q_l // p) * v for a v in Z_p"
                    )

    # -- the relation -------------------------------------------------------------------------

    def inner_product(self, row: int, s: tuple[int, ...]) -> int:
        """``sum_j X_ij s_j mod q_l``, in exact integers."""
        return sum(x * sj for x, sj in zip(self.base[row], s)) % self.q_l

    def raw_rounded(self, v: int) -> int:
        """``round_half_up(v * p, q_l)`` — the pre-reduction sample, an integer in ``[0, p]``."""
        return round_half_up(v * self.p, self.q_l)

    def sample(self, v: int) -> int:
        """The relation's output for a pre-reduction inner product ``v``, in ``Z_p``."""
        return self.raw_rounded(v) % self.p

    def evaluate(self, s: tuple[int, ...]) -> tuple[int, ...]:
        """``F_s(X)`` for an arbitrary candidate secret."""
        return tuple(self.sample(self.inner_product(i, s)) for i in range(self.m))

    @property
    def is_control(self) -> bool:
        """True when the public samples were drawn rather than derived — nothing is planted.

        The negative control (``random_lattice_control``) is this: a uniform base and **uniform
        samples**, so no secret explains them and the embedded lattice holds no unusually short
        vector. ``secret_s`` is still recorded, because the type requires one and because it lets a
        test show that the recorded secret does *not* explain the samples; ``exact_error`` is then
        the residual against that secret, spread over all of ``Z_q`` rather than inside the noise
        bound. The identity ``A s - e == b`` still holds — it holds for any samples, since ``e`` is
        defined as the residual — which is exactly why it cannot distinguish a control from a
        planted instance, and why the smallness of ``e`` is the property that does.
        """
        return self.control_samples is not None

    @property
    def target(self) -> tuple[int, ...]:
        """The public ``b`` an attacker is given, in ``Z_p``.

        ``F`` applied to the real secret for a planted instance; for a control, the drawn samples
        brought back down to ``Z_p``, so ``public_samples()`` is ``rounding_ratio * target`` for both.
        """
        if self.control_samples is not None:
            return tuple(v // self.rounding_ratio for v in self.control_samples)
        return self.evaluate(self.secret_s)

    # -- the rounding error, which is the whole object of the attack --------------------------

    @property
    def rounding_ratio(self) -> int:
        """``q_l // p`` — how many ``q_l``-values collapse to one sample. The relation's lossiness."""
        return self.q_l // self.p

    @property
    def noise_bound(self) -> int:
        """The half-width ``B`` of the rounding error's interval ``[-B, B]``.

        When ``p`` divides ``q_l`` this is exactly ``q_l // (2p)``, which is the recorded parameter
        case: ``2^8`` divides ``2^16``, giving ``[-128, 127]``. That is a *derived, deterministic*
        interval, not a Gaussian tail — there is no sigma to choose.

        **The simple formula is wrong when ``p`` does not divide ``q_l``**, and wrong in a way that
        matters. The sample is ``(q_l // p) * round_half_up(u * p, q_l)``, so when ``q_l // p`` is
        strictly less than ``q_l / p`` the residual ``u - (q_l//p) * r`` carries an extra
        ``r * (q_l/p - q_l//p)`` term that grows with ``r``. Measured at ``q_l = 61, p = 19`` the
        formula gives 1 while the error actually reaches 3, and a bound that is too small makes
        ``check_small`` reject honest instances while looking like a lattice bug.

        So the bound is *computed*: the rounding partitions ``[0, q_l)`` into ``p + 1`` buckets, the
        residual is monotone within each, so the extremes are attained at bucket edges and scanning
        them is exact. Cost is ``O(p)``, trivial at the production ``p = 256`` and bounded by
        ``q_l / 3`` because the rounding gap is at least three.
        """
        if self.q_l % self.p == 0:
            # Exact divisor case: the residual is bounded by half a bucket, symmetric.
            return self.q_l // (2 * self.p)

        if self.p > 1_000_000:
            # The scan is linear in p; past this the analytic floor is what is available, and it is
            # reported as such rather than presented as exact.
            return max(1, self.q_l // (2 * self.p))

        step = self.q_l // self.p
        worst = 0
        for r in range(self.p + 1):
            # Bucket r covers u where round_half_up(u*p, q_l) == r, i.e. u in
            # [ceil((2r-1)q/(2p)), floor((2r+1)q/(2p))), clipped to [0, q_l).
            lo_num, hi_num = (2 * r - 1) * self.q_l, (2 * r + 1) * self.q_l
            lo = max(0, -((-lo_num) // (2 * self.p)))  # ceil division
            hi = min(self.q_l - 1, hi_num // (2 * self.p))
            if lo > hi:
                continue
            # The sample this bucket produces: it is `step * r`, except that the r == p bucket
            # reduces mod p to zero — the wrap case, which is where the whole subtlety lives.
            sample_value = (step * r) % self.p
            for u in (lo, hi):
                residual = u - sample_value
                # Signed representative of the residual modulo q, which is what the relation
                # `b = A s - e (mod q)` actually requires. At the wrap bucket for a non-divisor
                # modulus this is the *only* choice that keeps the relation true.
                residual %= self.q_l
                if residual > self.q_l // 2:
                    residual -= self.q_l
                worst = max(worst, abs(residual))
        return max(1, worst)

    @property
    def is_bit_shift_rounding(self) -> bool:
        """True when both moduli are powers of two, so the relation is a shift and a mask.

        Worth surfacing rather than hiding: whether a power-of-two modulus admits a shortcut is a
        question the emulator can *measure*, and a report should say when its instance is in that
        regime rather than leaving a reader to notice.
        """
        return (self.q_l & (self.q_l - 1) == 0) and (self.p & (self.p - 1) == 0)

    def exact_error(self, row: int) -> int:
        """The signed rounding error of ``row`` for the **real** secret.

        (For a control — :attr:`is_control` — there is no real secret: this is the residual against
        the recorded one, it is not small, and that is the point of the control.)

        ``e_i`` is the signed representative of ``u_i - b_i`` modulo ``q_l``, where ``u_i`` is the
        reduced inner product and ``b_i`` the lifted sample. Defined this way, the identity
        ``A s - e == b (mod q_l)`` holds **by construction** — which is the property the entire
        lattice construction rests on.

        **Why not ``u_i - (q_l // p) * round_half_up(u_i * p, q_l)``**, which is the same thing in
        the ordinary case and which this method used to compute: in the wrap bucket
        (``round_half_up`` returning exactly ``p``) the sample reduces mod ``p`` to zero, and the
        two expressions differ by ``(q_l // p) * p``. That is exactly ``q_l`` when ``p`` divides
        ``q_l`` — the recorded parameter case, ``2^8 | 2^16`` — and is **not** ``q_l`` otherwise.
        So the older form silently broke the relation for a non-divisor modulus, which is why
        ``q_l = 61, p = 19`` produced an inconsistent normal form while the production pair did not.

        This is the ground truth the planted-vector test is built on: computed here from the
        relation, never inferred from a reduction.
        """
        u = self.inner_product(row, self.secret_s)
        residual = (u - self.public_samples()[row]) % self.q_l
        return residual - self.q_l if residual > self.q_l // 2 else residual

    def error_vector(self) -> tuple[int, ...]:
        return tuple(self.exact_error(i) for i in range(self.m))

    def public_samples(self) -> tuple[int, ...]:
        """``b_i = (q_l // p) * F_s(X)_i`` — the samples handed to an attacker, lifted to ``Z_{q_l}``.

        For a control the lifted samples are the drawn ones; see :attr:`is_control`.
        """
        return tuple(self.rounding_ratio * v for v in self.target)

    def check_relation(self) -> None:
        """``A s - b - e == 0 (mod q_l)``, for every row. The instance's defining identity."""
        b = self.public_samples()
        e = self.error_vector()
        for i in range(self.m):
            lhs = (self.inner_product(i, self.secret_s) - b[i] - e[i]) % self.q_l
            if lhs != 0:
                raise AssertionError(f"row {i}: A s - b - e = {lhs} mod q_l, expected 0")

    # -- reporting ----------------------------------------------------------------------------

    @property
    def equivalent_gaussian_sigma(self) -> float:
        """The standard deviation of the error, as a *reporting* convenience only.

        The error is exactly uniform on ``[-B, B-1]``, so its variance is ``((2B)^2 - 1)/12``
        exactly. Quoted because the literature speaks in sigmas when comparing to LWE instances;
        never used in a computation, because the interval is already exact and a sigma would only
        lose information.
        """
        b = self.noise_bound
        return math.sqrt((4.0 * b * b - 1.0) / 12.0)

    def describe(self) -> dict:
        return {
            "label": self.label,
            # Said in the record, not left to the label: a results file whose attack recovered
            # nothing reads very differently depending on whether there was anything to recover.
            "planted": not self.is_control,
            "nu": self.nu,
            "q_l": self.q_l,
            "p": self.p,
            "m": self.m,
            "seed": self.seed,
            "rounding_ratio": self.rounding_ratio,
            "noise_bound": self.noise_bound,
            "noise_interval": [-self.noise_bound, self.noise_bound - 1],
            "equivalent_gaussian_sigma": round(self.equivalent_gaussian_sigma, 4),
            "is_bit_shift_rounding": self.is_bit_shift_rounding,
            # The q-ary lattice has dimension m, and the primal attack embeds it — one row and one
            # column — so the uSVP instance BKZ actually sees is m + 1. Both are reported because
            # the literature quotes either, and a report that says "dimension m" without saying
            # which lattice is quoting a number a reader cannot check.
            #
            # That "m" is the *original* row count, and it is subtler than it looks: the attack never
            # builds a lattice from this instance directly, because a uniform secret has no short
            # representative. It builds one from the normal form, whose width is ``nf.m + nf.n`` —
            # and normalising consumes ``nu`` samples while adding ``nu`` unknowns, so that is
            # ``m - nu + nu = m`` exactly. The identity is what makes this number right;
            # ``m + nu + 1`` is the expression that looks equally natural and is larger by nu,
            # describing the embedding you get if the normal form is skipped. It was used in two
            # places before it was caught.
            "qary_lattice_dimension": self.m,
            "usvp_lattice_dimension": self.m + 1,
        }
