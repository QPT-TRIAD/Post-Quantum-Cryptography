"""The hard problems the reductions target, as instances with checkers.

A reduction's output is only worth something if it is checked by a party that does not trust the
reduction. These checkers know the instance and nothing else: they are handed a candidate and say
yes or no.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .scheme import Opening, Scheme

__all__ = ["AF1Instance", "sample_af1", "solves_af1", "is_collision"]


@dataclass(frozen=True)
class AF1Instance:
    """Assumption A-F1, "one-wayness with handle": given ``(Y, Z, c)`` with ``Y = F(s | r)`` and
    ``Z = r^7 + L_c(s)`` for a random opening and a random invertible challenge, find any ``(s', r')``
    with ``F(s' | r') = Y``. The opening is kept by the challenger and never shown to a reduction."""

    public_key: int
    handle: int
    triple: tuple[int, int, int]


def sample_af1(scheme: Scheme, rng: random.Random) -> tuple[AF1Instance, Opening]:
    opening, triple = scheme.sample_opening(rng), scheme.sample_invertible_triple(rng)
    return AF1Instance(scheme.public_key(opening), scheme.handle(opening, triple), triple), opening


def solves_af1(scheme: Scheme, instance: AF1Instance, candidate: Opening | None) -> bool:
    return candidate is not None and scheme.public_key(candidate) == instance.public_key


def is_collision(scheme: Scheme, pair: tuple[Opening, Opening] | None) -> bool:
    """Assumption A-F2, binding: ``x != x'`` with ``F(x) = F(x')``."""
    if pair is None:
        return False
    a, b = pair
    return scheme.pack(a) != scheme.pack(b) and scheme.public_key(a) == scheme.public_key(b)
