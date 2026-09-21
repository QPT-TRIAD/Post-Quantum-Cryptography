"""Game Frame(i*) of the record's Theorem 1, and the interface an adversary plays it through.

    Seat i* is honest. The adversary controls every other seat, sees all public data, may query the
    random oracle, and may obtain i*'s approval of ONE message of its choice in the domain. It
    outputs two accepted certificates with the same (cfg, domain) and different messages. It wins if
    the public extraction names i* although i* approved at most one of the two messages.

An adversary sees only a :class:`FrameView`. The real game and a reduction's simulation both
implement it, so the *same adversary code* runs against both — which is what makes "the adversary
cannot tell them apart" a thing that can be measured instead of asserted.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Protocol

from .scheme import Certificate, IdealProver, Opening, Params, RandomOracle, Registry, Scheme

__all__ = ["FrameView", "FrameOutcome", "RealFrameGame", "judge_frame"]


class FrameView(Protocol):
    scheme: Scheme
    registry: Registry
    honest_seat: int
    corrupt_openings: dict[int, Opening]
    domain: int

    def challenge(self, message: bytes, salt: int = 0) -> tuple[int, int, int]: ...
    def request_approval(self, message: bytes) -> tuple[int, int]: ...          # (handle, salt)
    def certify(self, message: bytes, witnesses: list[tuple[int, Opening, int]],
                *, with_honest_approval: bool = False) -> Certificate: ...


@dataclass
class FrameOutcome:
    adversary_won: bool
    reason: str
    named: list = field(default_factory=list)
    certificates: tuple | None = None


def judge_frame(scheme: Scheme, oracle: RandomOracle, registry: Registry, prover: IdealProver,
                honest_seat: int, approved: set[bytes], output) -> FrameOutcome:
    """The game's winning condition, applied to whatever the adversary returned."""
    if not output:
        return FrameOutcome(False, "the adversary produced no certificates")
    c0, c1 = output
    if not (prover.verify(c0) and prover.verify(c1)):
        return FrameOutcome(False, "a certificate was not accepted")
    if (c0.cfg, c0.domain) != (c1.cfg, c1.domain) or c0.message == c1.message:
        return FrameOutcome(False, "the certificates are not a conflict")
    named = scheme.extract(oracle, registry, c0, c1)
    if honest_seat not in {entry.seat for entry in named}:
        return FrameOutcome(False, "the extraction did not name the honest seat", named, (c0, c1))
    if {c0.message, c1.message} <= approved:
        return FrameOutcome(False, "the honest seat really did approve both messages", named, (c0, c1))
    return FrameOutcome(True, "the honest seat was named for a message it never approved", named, (c0, c1))


class RealFrameGame:
    """The game played honestly: real keys, a real (unprogrammed) oracle, the real functionality."""

    def __init__(self, params: Params, seed: int, honest_seat: int = 0, domain: int = 1):
        rng = random.Random(seed)
        self.scheme = Scheme(params)
        self.oracle = RandomOracle(rng.getrandbits(64))
        self._openings = [self.scheme.sample_opening(rng) for _ in range(params.seats)]
        self.registry = Registry([self.scheme.public_key(o) for o in self._openings])
        self.prover = IdealProver(self.scheme, self.registry, self.oracle)
        self.honest_seat, self.domain = honest_seat, domain
        self.corrupt_openings = {i: o for i, o in enumerate(self._openings) if i != honest_seat}
        self._rng, self._approved, self._approval = rng, set(), {}

    def challenge(self, message: bytes, salt: int = 0):
        return self.scheme.challenge(self.oracle, self.registry.cfg, self.domain, message, salt)

    def request_approval(self, message: bytes) -> tuple[int, int]:
        if self._approved and message not in self._approved:
            raise PermissionError("the honest seat approves one message per domain")
        if message not in self._approval:
            salt = self._rng.getrandbits(self.scheme.params.salt_bits) if self.scheme.params.salted else 0
            triple = self.scheme.challenge(self.oracle, self.registry.cfg, self.domain, message, salt,
                                           who="honest seat")
            self._approval[message] = (self.scheme.handle(self._openings[self.honest_seat], triple), salt)
            self._approved.add(message)
        return self._approval[message]

    def certify(self, message: bytes, witnesses, *, with_honest_approval: bool = False) -> Certificate:
        witnesses = list(witnesses)
        if with_honest_approval:
            if message not in self._approved:
                raise PermissionError("the honest seat has not approved this message")
            # the trusted aggregator holds the honest seat's opening for the message it approved
            witnesses.append((self.honest_seat, self._openings[self.honest_seat],
                              self._approval[message][1]))
        return self.prover.certify(self.domain, message, witnesses)

    def judge(self, output) -> FrameOutcome:
        return judge_frame(self.scheme, self.oracle, self.registry, self.prover, self.honest_seat,
                           self._approved, output)
