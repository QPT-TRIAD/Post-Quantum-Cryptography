"""The scaled QLWR relation, in exact integer arithmetic.

The relation, as the research record states it:

    F_s(X)_i = round( (sum_j X_ij * s_j  mod  q_L) * p / q_L )  mod  p     in Z_p^m

with ``s in Z_{q_L}^nu`` the secret, ``X in Z_{q_L}^{m x nu}`` a public matrix, ``p`` a prime, and
rounding to nearest.

Three things about this file are deliberate and load-bearing.

**No numeric parameters are taken from anywhere.** The research record states the relation and a
uniqueness inequality (``m >= nu * (log q_L + 1) / (log p - 1)``) and contains **no numeric
instantiation of it at all**. Every number this module uses is chosen by
:func:`generate_scaled_instance` and is reported as chosen. Nothing here is a parameter anyone
published.

**No floats.** Every function is integer or ``fractions`` arithmetic. A Boolean oracle whose
predicate was computed in floating point would have a boundary the circuit cannot reproduce, and the
failure would show up as a handful of basis states the two lowerings disagree on — the most
expensive kind of bug to find. ``round_half_up`` is the one definition of "round to nearest" used by
the predicate, by the circuit's interval test, and by the tests.

**The reduction ``mod q_L`` is carried, and it is provably redundant.** Under the trailing ``mod p``,

    round((u + k*q_L) * p / q_L)  ==  round(u * p / q_L) + k*p     (mod p)

so reducing the inner product mod ``q_L`` before rounding cannot change the marked set. It is
computed anyway, behind :attr:`QLWRInstance.reduce_mod_ql`, because it *is* required under the
alternative reading of the relation (the one without a trailing ``mod p``), and because the
redundancy is the single most valuable property test in this oracle: two constructions that must
agree for a reason that has nothing to do with either one's implementation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

__all__ = [
    "round_half_up",
    "is_generic_prime",
    "largest_generic_prime_below",
    "QLWRInstance",
    "generate_scaled_instance",
]


def round_half_up(numerator: int, denominator: int) -> int:
    """``floor((2a + b) / 2b)`` — round ``a/b`` to nearest, halves away from zero for positives.

    Exact for all integers, negative numerators included. For ``b > 0`` and ``a >= 0`` this rounds
    ``a/b`` to the nearest integer, with exact halves rounding up.
    """
    if denominator <= 0:
        raise ValueError(f"denominator must be positive, got {denominator}")
    return (2 * numerator + denominator) // (2 * denominator)


def _ceildiv(a: int, b: int) -> int:
    """Exact ceiling of ``a/b`` for ``b > 0``, correct for negative ``a``."""
    return -((-a) // b)


def is_generic_prime(x: int) -> bool:
    """Prime, and not of the form ``2**k``, ``2**k - 1`` or ``2**k + 1``.

    Genericity is a requirement, not taste. A modulus of special form admits arithmetic shortcuts
    (Mersenne reduction is a fold; a power of two needs no reduction at all), so a gate-count fit
    measured on one would be a fit to the shortcut rather than to the relation.
    """
    if x < 2:
        return False
    if x in (2, 3):
        return False  # 2 = 2^1+1, 3 = 2^2-1: both special
    if x % 2 == 0:
        return False
    for k in range(2, x.bit_length() + 2):
        if x == (1 << k) - 1 or x == (1 << k) + 1:
            return False
    d = 3
    while d * d <= x:
        if x % d == 0:
            return False
        d += 2
    return True


def largest_generic_prime_below(bound: int) -> int | None:
    """The largest generic prime strictly below ``bound``, or None if there is none."""
    for x in range(bound - 1, 2, -1):
        if is_generic_prime(x):
            return x
    return None


def _rank_mod_prime(rows: list[list[int]], q: int) -> int:
    """Rank of a matrix over the field ``Z_q`` (``q`` prime), by Gaussian elimination."""
    if not rows:
        return 0
    a = [row[:] for row in rows]
    n_rows, n_cols = len(a), len(a[0])
    rank = 0
    for col in range(n_cols):
        pivot = None
        for r in range(rank, n_rows):
            if a[r][col] % q:
                pivot = r
                break
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        inv = pow(a[rank][col], -1, q)
        a[rank] = [(v * inv) % q for v in a[rank]]
        for r in range(n_rows):
            if r != rank and a[r][col] % q:
                factor = a[r][col] % q
                a[r] = [(a[r][c] - factor * a[rank][c]) % q for c in range(n_cols)]
        rank += 1
        if rank == n_rows:
            break
    return rank


@dataclass(frozen=True, slots=True)
class QLWRInstance:
    """One instantiation of the QLWR relation, with a chosen secret and a public base.

    The experiment is **secret recovery**, not a search for a preimage of ``F``: the base ``X`` is
    public and the target ``a = F_s(X)`` is a classical constant, so the search is over
    ``s' in Z_{q_L}^nu`` with marking condition ``F_{s'}(X) == a``.

    That is the variant the uniqueness inequality is about. ``m >= nu(log q_L + 1)/(log p - 1)`` is
    precisely the statement that the marking set has exactly one element, so the security statement
    and the experimental design are the same object, and Grover is run against its single cleanest
    instance.

    Attributes:
        q_l: the modulus of the ring the secret and base live in. Prime, generic.
        nu: the dimension of the secret.
        m: the number of rows of the public base, hence the number of samples.
        p: the rounding modulus. Prime, generic.
        secret_s: the secret, ``nu`` values in ``[0, q_l)``.
        base: the public ``m x nu`` matrix over ``Z_{q_l}``, row-major.
        reduce_mod_ql: whether the inner product is reduced mod ``q_L`` before rounding. Provably
            redundant; see the module docstring.
        seed: the seed that produced this instance, recorded so a run is reproducible from it.
    """

    q_l: int
    nu: int
    m: int
    p: int
    secret_s: tuple[int, ...]
    base: tuple[tuple[int, ...], ...]
    reduce_mod_ql: bool = True
    seed: int = 0

    def __post_init__(self) -> None:
        if self.q_l < 3 or not is_generic_prime(self.q_l):
            raise ValueError(f"q_l={self.q_l} must be a generic prime")
        if self.p < 3 or not is_generic_prime(self.p):
            raise ValueError(f"p={self.p} must be a generic prime")
        if self.p > self.q_l:
            raise ValueError(f"p={self.p} exceeds q_l={self.q_l}; the rounding would be lossless")
        if len(self.secret_s) != self.nu:
            raise ValueError(f"secret_s has {len(self.secret_s)} entries, expected nu={self.nu}")
        if any(not 0 <= v < self.q_l for v in self.secret_s):
            raise ValueError("secret_s has an entry outside [0, q_l)")
        if len(self.base) != self.m:
            raise ValueError(f"base has {len(self.base)} rows, expected m={self.m}")
        if any(len(row) != self.nu for row in self.base):
            raise ValueError(f"every base row must have nu={self.nu} entries")
        rank = _rank_mod_prime([list(r) for r in self.base], self.q_l)
        if rank != self.nu:
            raise ValueError(
                f"base has column rank {rank} over Z_{self.q_l}, need {self.nu}. A rank-deficient "
                "base makes s -> Xs non-injective and inflates the marked set without bound."
            )

    # -- the relation ------------------------------------------------------------------------

    def raw_rounded(self, v: int) -> int:
        """``round_half_up(v * p, q_l)`` — the pre-reduction sample, an integer in ``[0, p]``."""
        return round_half_up(v * self.p, self.q_l)

    def sample(self, v: int) -> int:
        """The relation's output for a pre-reduction inner product ``v``, in ``Z_p``."""
        return self.raw_rounded(v) % self.p

    def inner_product(self, row: int, s: tuple[int, ...]) -> int:
        """``sum_j X_ij * s_j``, reduced mod ``q_l`` if :attr:`reduce_mod_ql`."""
        total = sum(x * sj for x, sj in zip(self.base[row], s))
        return total % self.q_l if self.reduce_mod_ql else total

    def evaluate(self, s: tuple[int, ...]) -> tuple[int, ...]:
        """``F_s(X)`` for an arbitrary candidate secret."""
        return tuple(self.sample(self.inner_product(i, s)) for i in range(self.m))

    @property
    def target(self) -> tuple[int, ...]:
        """``F`` applied to the real secret — the constant the search compares against."""
        return self.evaluate(self.secret_s)

    # -- the marking predicate ---------------------------------------------------------------

    @property
    def w(self) -> int:
        """Bits per secret component: ``ceil(log2 q_l)``."""
        return (self.q_l - 1).bit_length()

    @property
    def n_search(self) -> int:
        """Search-register width in qubits, ``nu * w``."""
        return self.nu * self.w

    @property
    def embedding_gap(self) -> int:
        """``2**n_search - q_l**nu`` — basis states that encode no valid secret.

        Nonzero whenever ``q_l`` is not a power of two, which genericity forces. Those states are
        never marked, so the closed form's ``M`` and ``N`` remain exact; the gap is reported as a
        faithfulness caveat rather than hidden.
        """
        return (1 << self.n_search) - self.q_l**self.nu

    def decode(self, candidate: int) -> tuple[int, ...]:
        """Split a search-register integer into ``nu`` ``w``-bit components."""
        mask = (1 << self.w) - 1
        return tuple((candidate >> (j * self.w)) & mask for j in range(self.nu))

    def is_valid(self, candidate: int) -> bool:
        """Whether a register value encodes a secret at all, i.e. every component is below ``q_l``."""
        return all(v < self.q_l for v in self.decode(candidate))

    def is_solution(self, candidate: int) -> bool:
        """Whether a search-register value is marked.

        Invalid encodings are never marked. That is not a convenience: the register is wider than
        the space it encodes, and a predicate that marked out-of-range values would be describing a
        different relation from the one written down.
        """
        if not 0 <= candidate < (1 << self.n_search):
            raise ValueError(f"candidate {candidate} outside the search register")
        if not self.is_valid(candidate):
            return False
        return self.evaluate(self.decode(candidate)) == self.target

    def marked_set(self) -> frozenset[int]:
        """Every marked register value, by exhaustive enumeration. Feasible for ``n_search`` <= 24."""
        return frozenset(x for x in range(1 << self.n_search) if self.is_solution(x))

    # -- reporting ---------------------------------------------------------------------------

    def describe(self) -> dict:
        """The instance's parameters, with the provenance of each number stated.

        ``chosen`` is True for every field: no numeric instantiation of this relation exists in the
        research record, so nothing here can honestly be labelled as sourced.
        """
        marked = self.marked_set()
        return {
            "relation": "F_s(X)_i = round_half_up((sum_j X_ij s_j mod q_l) * p, q_l) mod p",
            "q_l": self.q_l,
            "nu": self.nu,
            "m": self.m,
            "p": self.p,
            "w_bits_per_component": self.w,
            "n_search": self.n_search,
            "n_items": 1 << self.n_search,
            "embedding_gap": self.embedding_gap,
            "reduce_mod_ql": self.reduce_mod_ql,
            "seed": self.seed,
            "n_marked": len(marked),
            "rounding_gap_bits": math.log2(self.q_l / self.p),
            "uniqueness_inequality_min_m": self.nu * (math.log2(self.q_l) + 1) / (math.log2(self.p) - 1),
            "parameters_are": "chosen for this emulator; the research record states constraints only",
            "base_rank": _rank_mod_prime([list(r) for r in self.base], self.q_l),
        }


# -----------------------------------------------------------------------------------------------
# generation
# -----------------------------------------------------------------------------------------------


def _choose_parameters(n_search: int, nu: int, min_rounding_gap: float) -> tuple[int, int, int, int, int]:
    """Pick ``(q_l, w, p, m_min, m)`` for a target search width, generically where possible.

    ``w`` is forced by the register split, ``q_l`` is the largest generic prime that fits in ``w``
    bits, ``p`` the largest generic prime at least ``min_rounding_gap`` times smaller, and ``m`` the
    uniqueness inequality's value. Whether these are *admissible* is decided by the caller, which
    measures the marked set rather than trusting the inequality.
    """
    w = n_search // nu
    if w < 2:
        raise ValueError(f"n_search={n_search}, nu={nu} leaves {w} bits per component; need >= 2")
    q_l = largest_generic_prime_below(1 << w)
    if q_l is None:
        raise ValueError(f"no generic prime below 2**{w}")
    p = largest_generic_prime_below(int(q_l / min_rounding_gap) + 1)
    if p is None or p < 3:
        raise ValueError(
            f"no generic prime at least {min_rounding_gap}x below q_l={q_l}; "
            "the smallest structurally faithful instance is wider than this"
        )
    m_min = math.ceil(nu * (math.log2(q_l) + 1) / (math.log2(p) - 1))
    return q_l, w, p, m_min, max(m_min + 2, m_min + 1)


def generate_scaled_instance(
    n_search: int = 12,
    nu: int = 2,
    seed: int = 20260913,
    min_rounding_gap: float = 3.0,
    require_unique: bool = True,
    reduce_mod_ql: bool = True,
    max_attempts: int = 4096,
) -> QLWRInstance:
    """Generate a scaled instance whose marked set is measured, not assumed.

    The research record supplies the uniqueness inequality without a derivation, so this function
    does not trust it: it builds a candidate, **counts the marked set exhaustively**, and rejects
    unless the count is exactly 1. ``m`` is raised when draws keep failing — by one sample at every
    eighth draw that comes back non-unique — which is the honest direction: the inequality is a
    lower bound with no upper bound attached. The returned instance's ``m`` is therefore the value
    that worked, which may exceed the inequality's.

    Args:
        n_search: the target search-register width in qubits.
        nu: the dimension of the secret. 2 is the smallest value with genuine matrix structure.
        seed: seeds both the parameter search and the generated base.
        min_rounding_gap: ``q_l / p`` at least this large, so rounding discards real information.
        require_unique: reject unless ``M == 1``. Turn off only to *measure* how a non-unique
            instance behaves, never to produce an instance for a success-curve run.
        reduce_mod_ql: see :attr:`QLWRInstance.reduce_mod_ql`.
        max_attempts: how many ``(base, secret)`` draws to try before giving up.

    Raises:
        RuntimeError: if no draw produced the required marked-set size. That is a real outcome and
            it is raised rather than papered over; see ``notes/`` for which parameter families can
            and cannot hit ``M = 1``.
    """
    import numpy as np

    q_l, w, p, m_min, m = _choose_parameters(n_search, nu, min_rounding_gap)
    rng = np.random.default_rng(seed)

    for attempt in range(max_attempts):
        base = tuple(
            tuple(int(v) for v in rng.integers(0, q_l, size=nu)) for _ in range(m)
        )
        secret = tuple(int(v) for v in rng.integers(0, q_l, size=nu))

        rows = [list(r) for r in base]
        if _rank_mod_prime(rows, q_l) != nu:
            continue

        try:
            inst = QLWRInstance(
                q_l=q_l,
                nu=nu,
                m=m,
                p=p,
                secret_s=secret,
                base=base,
                reduce_mod_ql=reduce_mod_ql,
                seed=seed,
            )
        except ValueError:
            continue

        n_marked = sum(1 for x in range(1 << inst.n_search) if inst.is_solution(x))
        if (n_marked == 1) or (not require_unique and n_marked >= 1):
            return inst
        if n_marked > 1 and attempt % 8 == 7:
            # The inequality was not enough: draws at this m keep coming back non-unique. Widen the
            # sample rather than the modulus, so the relation's parameters stay as chosen and only m
            # moves. The condition is `n_marked > 1`, not `== 0`: the real secret always satisfies
            # its own target, so a count of 0 cannot occur and a branch keyed on it never runs.
            # (Reaching here at all means require_unique — a non-unique draw was otherwise returned
            # above.) Every eighth draw rather than every draw, so one unlucky base does not move m
            # and an instance that is unique at the chosen m is still found at the chosen m.
            m += 1

    raise RuntimeError(
        f"no instance with M={1 if require_unique else '>=1'} found in {max_attempts} draws at "
        f"n_search={n_search}, nu={nu}, q_l={q_l}, p={p}, m={m}"
    )
