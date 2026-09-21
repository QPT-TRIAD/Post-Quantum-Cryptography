"""Adversaries that really win, at sizes where winning is affordable.

A reduction can only be exercised by an adversary that breaks the scheme, and at toy sizes that is
available for the price of a loop. None of these is clever. What matters is that they are
*legitimate*: each does only what the game allows, through the same view whether it is facing the
real game or a reduction's simulation, and none knows which of the two it is facing.

The framers differ in one respect, and it is the respect that matters. :class:`BruteForceFramer`
asks for the honest seat's approval first and only then looks at the challenge.
:class:`PreQueryFramer` looks the challenge up *first* — it is a public hash of the message, and
nothing in the game forbids asking — and then requests the approval of that same message. Both win
the real game equally often. Whether a reduction survives both is what the runner is for.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .scheme import Opening

__all__ = ["BruteForceFramer", "PreQueryFramer", "LazyFramer", "CollisionEvader", "HonestDoubleSigner"]


def _recover_opening(view, triple, handle: int, budget: float, rng: random.Random) -> Opening | None:
    """Exhaustive search over ``r``; the handle fixes ``s``. ``budget`` is the fraction of the space
    searched, from a random start — so an adversary with budget 1/4 wins a quarter of the time, in
    *any* world where the handle it was given is consistent with the challenge it was given."""
    scheme, space = view.scheme, 1 << view.scheme.n
    target, start = view.registry.keys[view.honest_seat], rng.randrange(space)
    for step in range(int(budget * space)):
        r = (start + step) % space
        for s in scheme.solve_linearized(triple, handle ^ scheme.field.pow(r, 7)):
            opening = Opening(s, r)
            if scheme.public_key(opening) == target:
                return opening
    return None


@dataclass
class BruteForceFramer:
    """Approval first, challenge second. ``budget`` below 1 makes the win probabilistic, which is
    what lets a real-versus-simulated win rate be compared at all."""

    budget: float = 1.0
    name: str = "brute-force framer (approval, then challenge)"

    def messages(self, rng) -> tuple[bytes, bytes, list[bytes]]:
        return b"pay alice", b"pay mallory", []

    def run(self, view, rng: random.Random):
        m0, m1, _ = self.messages(rng)
        handle, salt = view.request_approval(m0)
        triple = view.challenge(m0, salt)
        return self._finish(view, rng, m0, m1, handle, salt, triple)

    def _finish(self, view, rng, m0, m1, handle, salt, triple):
        opening = _recover_opening(view, triple, handle, self.budget, rng)
        if opening is None:
            return None
        quorum = view.scheme.params.quorum
        helpers = sorted(view.corrupt_openings)[: quorum - 1]
        salt_of = lambda: rng.getrandbits(view.scheme.params.salt_bits) if view.scheme.params.salted else 0  # noqa: E731
        first = view.certify(m0, [(i, view.corrupt_openings[i], salt_of()) for i in helpers],
                             with_honest_approval=True)
        # the frame: a second certificate, for a message the honest seat never saw, carrying a
        # handle made from the stolen opening
        second = view.certify(m1, [(i, view.corrupt_openings[i], salt_of()) for i in helpers]
                              + [(view.honest_seat, opening, salt_of())])
        return first, second


@dataclass
class PreQueryFramer(BruteForceFramer):
    """Challenge first, approval second — for the target message and for ``decoys`` others, in a
    random order, so that nothing about the order of its queries says which one it will use."""

    decoys: int = 0
    name: str = "pre-querying framer (challenge, then approval)"

    def run(self, view, rng: random.Random):
        m0, m1 = b"pay alice", b"pay mallory"
        candidates = [m0] + [b"decoy %d" % k for k in range(self.decoys)]
        rng.shuffle(candidates)
        seen = {message: view.challenge(message, 0) for message in candidates}
        handle, salt = view.request_approval(m0)
        # unsalted, the challenge of m0 is the one already seen; salted, the salt is news and the
        # pre-query was of no use — which is the whole effect of salting
        triple = seen[m0] if salt == 0 and not view.scheme.params.salted else view.challenge(m0, salt)
        return self._finish(view, rng, m0, m1, handle, salt, triple)


@dataclass
class LazyFramer:
    """Never wins. A reduction must output nothing for it — never a wrong answer."""

    name: str = "lazy framer (gives up)"

    def run(self, view, rng: random.Random):
        view.challenge(b"pay alice", 0)
        return None


# -- evasion -------------------------------------------------------------------------------------


@dataclass
class CollisionEvader:
    """A double-signer who dodges the extractor with two openings of one key.

    It finds a collision ``F(x) = F(x')`` with the linear trick, registers ``F(x)`` as seat 0's key,
    and approves the first message with ``x`` and the second with ``x'``. The pair search assumes one
    opening per seat, so seat 0's two handles decode to nothing and it is not named — the record's
    section 9 item 2.
    """

    name: str = "collision evader (two openings of one key)"
    max_seconds: float = 120.0

    def run(self, view, rng: random.Random):
        scheme = view.scheme
        pair = _collision_pair(scheme, rng, self.max_seconds)
        if pair is None:
            return None
        mask = (1 << scheme.n) - 1
        a, b = (Opening(x & mask, x >> scheme.n) for x in pair)
        return _double_sign(view, rng, {0: (a, b)})


def _collision_pair(scheme, rng, max_seconds: float) -> tuple[int, int] | None:
    """The attack tester's linear trick, kept to the pair it finds: about ``2^E`` differences, each
    one Gaussian elimination, ``E = 2n`` at this scheme's ratio."""
    import time

    from qpt_cart.attacks.collision import _solve, _symmetric, difference_system

    symmetric, mask, began = _symmetric(scheme.map), (1 << scheme.map.n_vars) - 1, time.perf_counter()
    while time.perf_counter() - began < max_seconds:
        delta = rng.getrandbits(scheme.map.n_vars) & mask
        if not delta:
            continue
        x = _solve(difference_system(scheme.map, delta, symmetric))
        if x is not None and scheme.map.evaluate(x) == scheme.map.evaluate(x ^ delta):
            return x, x ^ delta
    return None


@dataclass
class HonestDoubleSigner:
    """Double-signs with the same opening both times. Every common seat must be named."""

    name: str = "plain double-signer (one opening per key)"

    def run(self, view, rng: random.Random):
        return _double_sign(view, rng, {})


def _double_sign(view, rng, special: dict[int, tuple[Opening, Opening]]):
    scheme, params = view.scheme, view.scheme.params
    openings = {i: (scheme.sample_opening(rng),) * 2 for i in range(params.seats)}
    openings.update(special)
    view.register([scheme.public_key(openings[i][0]) for i in range(params.seats)])
    # two quorums sharing exactly the minimum: seats 0..overlap-1 sign both blocks
    first_seats = list(range(params.quorum))
    second_seats = list(range(params.overlap)) + list(range(params.quorum, params.seats))
    c0 = view.certify(b"block A", [(i, openings[i][0], 0) for i in first_seats])
    c1 = view.certify(b"block B", [(i, openings[i][1], 0) for i in second_seats])
    return c0, c1
