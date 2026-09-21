"""The QLWR trace function ``F_s(X) = round_p(X s)``, with nothing around it.

The generation-1 QPT-128 record traces validators with a rounding-based weak PRF (``pqt.md``
287-321): a secret ``s`` in ``Z_q^nu``, a public matrix ``X`` in ``Z_q^{m x nu}``, and the public
trace ``b = round(p/q * (X s mod q)) mod p``. Recorded production values: ``nu = 256``,
``q = 2^16``, ``p = 2^8``, ``m = 608`` rows. Three operations: ``keygen``, ``trace``, ``verify``.
The attack goal is secret recovery from ``(X, b)`` — a Learning-With-Rounding instance, which is a
lattice problem, so the attack that matters is lattice reduction.

All arithmetic is exact integers. The rounding *is* the relation: computed through a float it
would define a different lattice at production size, where the products exceed a double.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

__all__ = ["QlwrScalingRule", "QlwrTrace", "round_half_up"]


def round_half_up(numerator: int, denominator: int) -> int:
    """``round(numerator / denominator)`` for non-negative integers, halves up, with no float."""
    if denominator <= 0 or numerator < 0:
        raise ValueError("round_half_up is defined here for numerator >= 0, denominator > 0")
    return (2 * numerator + denominator) // (2 * denominator)


@dataclass(frozen=True)
class QlwrScalingRule:
    """Production shape, shrunk by keeping the moduli and the rows-per-secret-coordinate ratio."""

    q: int = 1 << 16
    p: int = 1 << 8
    production_nu: int = 256
    production_m: int = 608
    source: str = "pqt.md:287-321 (relation); research_qualification_v1.18.md:257 (nu, q, p, rows)"

    def rows_at(self, nu: int) -> int:
        return max(nu + 1, round(self.production_m / self.production_nu * nu))


class QlwrTrace:
    def __init__(self, nu: int, *, rule: QlwrScalingRule | None = None, seed: int = 0):
        if nu < 1:
            raise ValueError("nu must be at least 1")
        self.rule = rule or QlwrScalingRule()
        self.nu, self.q, self.p, self.m = nu, self.rule.q, self.rule.p, self.rule.rows_at(nu)
        self.seed = seed
        self.matrix = self._draw(b"X", self.m * nu, nu)

    def _draw(self, label: bytes, count: int, width: int):
        nbytes = (self.q.bit_length() + 7) // 8 + 8             # 64 spare bits: no modulo bias worth the name
        stream = hashlib.shake_256(b"qpt-cart/qlwr/v1/" + label + self.seed.to_bytes(8, "big")
                                   + self.nu.to_bytes(2, "big")).digest(count * nbytes)
        values = [int.from_bytes(stream[i * nbytes:(i + 1) * nbytes], "big") % self.q
                  for i in range(count)]
        return tuple(tuple(values[i:i + width]) for i in range(0, count, width))

    def keygen(self) -> tuple[int, ...]:
        return self._draw(b"s", self.nu, self.nu)[0]

    def trace(self, secret: tuple[int, ...]) -> tuple[int, ...]:
        if len(secret) != self.nu or any(not 0 <= v < self.q for v in secret):
            raise ValueError("secret must be nu integers in [0, q)")
        return tuple(
            round_half_up((sum(x * s for x, s in zip(row, secret)) % self.q) * self.p, self.q) % self.p
            for row in self.matrix
        )

    def verify(self, public_trace: tuple[int, ...], secret: tuple[int, ...]) -> bool:
        return self.trace(secret) == tuple(public_trace)
