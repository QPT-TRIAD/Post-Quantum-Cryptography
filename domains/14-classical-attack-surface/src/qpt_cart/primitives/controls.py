"""Two primitives whose answer is known in advance, so the tester's verdicts can be trusted.

A tester that has only ever said "exponential" is indistinguishable from one that cannot say
anything else. So every campaign also runs:

* :class:`RandomFunctionControl` — preimage search on a truncated hash. There is no shortcut, and
  the work grows by one bit per bit of ``n``. The tester must call it **exponential** at that rate;
  if it does not, its "exponential" verdicts are worthless. (The *mean* is ``2^n / e``, not
  ``2^(n-1)``: an ``n``-bit to ``n``-bit random function gives the target a Poisson(1) number of
  extra preimages, and the first hit among ``1 + K`` uniform points lands at ``2^n * E[1/(K+2)]``,
  which sums to exactly ``2^n / e``. Measured over 128 seeds: 0.36 of ``2^n``. The expanding key
  map is injective with overwhelming probability, so *its* search does sit at ``2^(n-1)`` — a
  difference in intercept between control and subject that is real, and is not a growth-rate
  difference.)
* :class:`LinearMapControl` — preimage of a random *linear* map over F_2. Gaussian elimination
  solves it in ``O(n^3)``. It is a deliberately broken primitive: the tester must catch it as
  **polynomial**, or it has not shown that it could catch a real shortcut either.

If either control comes back wrong, the campaign report says its other verdicts are void.
"""

from __future__ import annotations

import hashlib

__all__ = ["RandomFunctionControl", "LinearMapControl"]


class RandomFunctionControl:
    """``f(x)`` = the first ``n`` bits of SHA-256 over a domain-separated ``x``."""

    def __init__(self, n: int, seed: int = 0):
        self.n, self.seed = n, seed

    def evaluate(self, x: int) -> int:
        digest = hashlib.sha256(b"qpt-cart/control/rf" + self.seed.to_bytes(8, "big")
                                + self.n.to_bytes(2, "big") + x.to_bytes((self.n + 7) // 8, "big")).digest()
        return int.from_bytes(digest, "big") >> (256 - self.n)

    def keygen(self) -> tuple[int, int]:
        """``(secret x, public f(x))``."""
        secret = int.from_bytes(hashlib.sha256(b"qpt-cart/control/rf/secret"
                                               + self.seed.to_bytes(8, "big")).digest(), "big") % (1 << self.n)
        return secret, self.evaluate(secret)


class LinearMapControl:
    """``f(x) = A x`` over F_2 with ``A`` a random ``2n x n`` matrix: injective with overwhelming
    probability, and trivially invertible by elimination."""

    def __init__(self, n: int, seed: int = 0):
        self.n, self.seed = n, seed
        nbytes = (n + 7) // 8
        stream = hashlib.shake_256(b"qpt-cart/control/lin" + seed.to_bytes(8, "big")
                                   + n.to_bytes(2, "big")).digest(2 * n * nbytes)
        mask = (1 << n) - 1
        self.rows = [int.from_bytes(stream[i * nbytes:(i + 1) * nbytes], "big") & mask
                     for i in range(2 * n)]

    def evaluate(self, x: int) -> int:
        return sum(((row & x).bit_count() & 1) << i for i, row in enumerate(self.rows))

    def keygen(self) -> tuple[int, int]:
        secret = int.from_bytes(hashlib.sha256(b"qpt-cart/control/lin/secret"
                                               + self.seed.to_bytes(8, "big")).digest(), "big") % (1 << self.n)
        return secret, self.evaluate(secret)
