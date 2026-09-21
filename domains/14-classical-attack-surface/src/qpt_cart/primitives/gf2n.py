"""GF(2^n) as integers: bit ``i`` of an element is the coefficient of ``X^i``.

The handle of the QPT-128 hidden-signer modes lives here — ``Z = G(r) + c*s`` with ``G(r) = r^7``
(Mode B) or ``G(r) = r`` (Mode A) — so the field has to exist at every scaled size, not only at the
production ``n = 256``. The modulus is the lexicographically first irreducible trinomial or
pentanomial, found by search and *certified* by Rabin's test on every construction: a reducible
modulus gives a ring with zero divisors in which ``c`` may have no inverse and ``r -> r^7`` is not a
permutation, and every attack cost measured over it would describe a different object.
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations

__all__ = ["Field", "is_irreducible", "find_modulus"]


def _poly_mod(a: int, f: int) -> int:
    df = f.bit_length()
    while a.bit_length() >= df:
        a ^= f << (a.bit_length() - df)
    return a


def _poly_mulmod(a: int, b: int, f: int) -> int:
    out = 0
    n = f.bit_length() - 1
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if (a >> n) & 1:
            a ^= f
    return out


def _poly_gcd(a: int, b: int) -> int:
    while b:
        a, b = b, _poly_mod(a, b)
    return a


def _prime_factors(n: int) -> list[int]:
    out, d = [], 2
    while d * d <= n:
        if n % d == 0:
            out.append(d)
            while n % d == 0:
                n //= d
        d += 1
    return out + ([n] if n > 1 else [])


def is_irreducible(f: int) -> bool:
    """Rabin's test: ``X^(2^n) = X mod f`` and ``gcd(X^(2^(n/p)) - X, f) = 1`` for each prime ``p | n``."""
    n = f.bit_length() - 1
    if n < 1:
        return False
    checkpoints = {n // p for p in _prime_factors(n)}
    power = 2                                           # the polynomial X
    for k in range(1, n + 1):
        power = _poly_mulmod(power, power, f)
        if k in checkpoints and _poly_gcd(f, power ^ 2) != 1:
            return False
    return power == _poly_mod(2, f)


#: The record's own production modulus (``hidden_signer_modeB_v1.46.py:127``), used at n = 256 so
#: that the production-size object is the record's object and not merely an isomorphic copy of it.
RECORD_MODULI = {256: (1 << 256) | (1 << 10) | (1 << 5) | (1 << 2) | 1}


@lru_cache(maxsize=None)
def find_modulus(n: int) -> int:
    """The record's modulus where it names one; else the first irreducible ``X^n + ... + 1`` with
    three, then five, terms. Any irreducible modulus gives the same field up to a linear change of
    basis, under which a *random* quadratic map stays a random quadratic map — so the choice at
    scaled sizes does not move any attack cost."""
    if n < 2:
        raise ValueError(f"GF(2^{n}) is not a useful field here; need n >= 2")
    if n in RECORD_MODULI:
        return RECORD_MODULI[n]
    for weight in (1, 3):
        for middle in combinations(range(1, n), weight):
            f = (1 << n) | 1 | sum(1 << e for e in middle)
            if is_irreducible(f):
                return f
    raise ValueError(f"no irreducible trinomial or pentanomial of degree {n}")  # pragma: no cover


class Field:
    """``GF(2)[X] / (modulus)`` with the operations the handle needs."""

    def __init__(self, n: int, modulus: int | None = None):
        self.n = n
        self.modulus = modulus if modulus is not None else find_modulus(n)
        if self.modulus.bit_length() - 1 != n or not is_irreducible(self.modulus):
            raise ValueError(f"modulus {self.modulus:#x} is not an irreducible polynomial of degree {n}")
        self.order = (1 << n) - 1

    def mul(self, a: int, b: int) -> int:
        return _poly_mulmod(a, b, self.modulus)

    def pow(self, a: int, e: int) -> int:
        out, base = 1, a
        while e:
            if e & 1:
                out = self.mul(out, base)
            base = self.mul(base, base)
            e >>= 1
        return out

    def inv(self, a: int) -> int:
        if a == 0:
            raise ZeroDivisionError("0 has no inverse")
        return self.pow(a, self.order - 1)

    def power_is_permutation(self, e: int) -> bool:
        """``r -> r^e`` permutes the field exactly when ``gcd(e, 2^n - 1) = 1``."""
        from math import gcd
        return gcd(e, self.order) == 1

    def mul_matrix(self, c: int) -> list[int]:
        """Multiplication by ``c`` as a GF(2)-linear map: ``rows[i]`` is the mask of input bits that
        feed output bit ``i``. This is what makes ``c*s`` a *linear* term in every algebraic attack."""
        columns = [self.mul(c, 1 << j) for j in range(self.n)]
        return [sum(((columns[j] >> i) & 1) << j for j in range(self.n)) for i in range(self.n)]
