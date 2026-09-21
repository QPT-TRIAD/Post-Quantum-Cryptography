"""The record's reductions, as programs.

Each reduction here is a *simulated world* — it implements the same view an adversary gets from the
real game — plus a rule for turning the adversary's win into a solution of the hard problem. It is
given an instance it does not know the answer to, and it is never handed the adversary's internals:
it sees what the game's challenger would see.

:class:`FrameToAF1` follows Theorem 1's proof sentence by sentence; the sentences are quoted at the
steps that implement them. When one of them cannot be carried out, the reduction raises
:class:`SimulationFailed` and says which sentence. It does **not** quietly do something else that
happens to work: a reduction that improvises is no longer the proof's reduction, and a runner that
let it would be testing its own ingenuity.

Three further variants exist to interpret a failure, not to hide it: a *guessing* reduction (the
textbook repair, with the loss the textbook predicts), the as-written reduction run against a
*salted* scheme (a second standard repair — a candidate, not part of the record), and a
deliberately *broken* reduction, which the runner must catch or its "holds" verdicts mean nothing.
"""

from __future__ import annotations

import random

from .frame_game import FrameOutcome, judge_frame
from .problems import AF1Instance
from .scheme import (AlreadyQueried, Certificate, IdealProver, Opening, Params, RandomOracle,
                     Registry, Scheme)

__all__ = ["SimulationFailed", "FrameToAF1", "FrameToAF1Guessing", "FrameToAF1WrongSeat",
           "EvasionToCollision"]


class SimulationFailed(RuntimeError):
    """The reduction could not do what its proof says it does. The message names the step."""


class FrameToAF1:
    """Theorem 1 (non-frameability, "tight"): a Frame winner becomes an A-F1 solver.

    The proof, from ``modeB_security_v1.49.md`` section 3:

        B receives an A-F1 instance (Y*, Z*, c*) for a random target and embeds it as seat i*'s key
        and handle: it sets Y[d][i*] := Y* and, when A requests i*'s approval of some m in d,
        programs c(m) := c* (a random-oracle output, uniform) and answers with Z*; all other seats'
        openings B samples itself. This simulation is perfect. When A wins, the extraction names
        i*, which means some pair decoded to (s', r') with F(s' | r') = Y*. B outputs (s', r').
    """

    name = "Theorem 1 as written: Frame -> A-F1"
    claimed_success_given_win = 1.0

    def __init__(self, params: Params, instance: AF1Instance, seed: int, honest_seat: int = 0,
                 domain: int = 1):
        rng = random.Random(seed)
        self.scheme = Scheme(params)
        self.oracle = RandomOracle(rng.getrandbits(64))
        self.instance, self.honest_seat, self.domain = instance, honest_seat, domain
        self._embed_at = self._seat_to_embed(honest_seat, params)
        # "all other seats' openings B samples itself"
        self._openings = {i: self.scheme.sample_opening(rng) for i in range(params.seats)
                          if i != self._embed_at}
        keys = [self.scheme.public_key(self._openings[i]) if i in self._openings else instance.public_key
                for i in range(params.seats)]                    # "sets Y[d][i*] := Y*"
        self.registry = Registry(keys)
        self.prover = IdealProver(self.scheme, self.registry, self.oracle)
        self.corrupt_openings = {i: o for i, o in self._openings.items() if i != honest_seat}
        self._rng, self._approved, self._approval = rng, set(), {}

    def _seat_to_embed(self, honest_seat: int, params: Params) -> int:
        return honest_seat

    # -- the simulated view ------------------------------------------------------------------------

    def challenge(self, message: bytes, salt: int = 0):
        return self.scheme.challenge(self.oracle, self.registry.cfg, self.domain, message, salt)

    def _program(self, message: bytes, salt: int) -> None:
        """"programs c(m) := c*". The challenge is the first *invertible* triple along the counter,
        so a faithful programming also lays down the non-invertible draws a real oracle would have
        produced before it — otherwise the counter would always read zero for this one message and
        the adversary could see that."""
        scheme, draws = self.scheme, []
        while True:
            triple = (self._rng.getrandbits(scheme.n), self._rng.getrandbits(scheme.n),
                      self._rng.getrandbits(scheme.n))
            if scheme.is_invertible(triple):
                break
            draws.append(triple)
        draws.append(self.instance.triple)
        for ctr, triple in enumerate(draws):
            try:
                self.oracle.program(scheme.challenge_point(self.registry.cfg, self.domain, message,
                                                           salt, ctr), scheme.pack_triple(triple))
            except AlreadyQueried as error:
                raise SimulationFailed(
                    "cannot carry out 'programs c(m) := c*': the adversary had already asked the "
                    f"oracle for the challenge of {message!r} before requesting its approval, and an "
                    "answer already given cannot be changed. The handle for the challenge it was "
                    "given needs seat i*'s opening, which the reduction does not have."
                ) from error

    def request_approval(self, message: bytes) -> tuple[int, int]:
        if self._embed_at != self.honest_seat:                       # only the broken control
            return self._honest_answer(message)
        if self._approved and message not in self._approved:
            raise PermissionError("the honest seat approves one message per domain")
        if message not in self._approval:
            salt = self._rng.getrandbits(self.scheme.params.salt_bits) if self.scheme.params.salted else 0
            self._program(message, salt)
            self._approval[message] = (self.instance.handle, salt)  # "and answers with Z*"
            self._approved.add(message)
        return self._approval[message]

    def _honest_answer(self, message: bytes) -> tuple[int, int]:
        triple = self.scheme.challenge(self.oracle, self.registry.cfg, self.domain, message, 0,
                                       who="honest seat")
        self._approved.add(message)
        self._approval[message] = (self.scheme.handle(self._openings[self.honest_seat], triple), 0)
        return self._approval[message]

    def certify(self, message: bytes, witnesses, *, with_honest_approval: bool = False) -> Certificate:
        trusted = None
        witnesses = list(witnesses)
        if with_honest_approval:
            if message not in self._approved:
                raise PermissionError("the honest seat has not approved this message")
            if self._embed_at == self.honest_seat:
                # B *is* F_Prove in its simulated world, and vouches for the one handle it cannot open
                trusted = {self.honest_seat: self._approval[message]}
            else:
                witnesses.append((self.honest_seat, self._openings[self.honest_seat], 0))
        return self.prover.certify(self.domain, message, witnesses, trusted=trusted)

    # -- turning the win into a solution -------------------------------------------------------------

    def judge(self, output) -> FrameOutcome:
        return judge_frame(self.scheme, self.oracle, self.registry, self.prover, self.honest_seat,
                           self._approved, output)

    def solve(self, outcome: FrameOutcome) -> Opening | None:
        """"the extraction names i* ... B outputs (s', r')". One public extraction, nothing else."""
        if not outcome.adversary_won:
            return None
        for entry in outcome.named:
            if entry.seat == self.honest_seat:
                return entry.opening
        return None


class FrameToAF1Guessing(FrameToAF1):
    """The textbook repair: guess *which* message the approval will be for, and program it early.

    B picks an index ``j`` uniformly from ``0..max_messages``. Index 0 bets that the approved message
    is one the adversary never looked up first (the as-written case). Index ``j >= 1`` bets on the
    ``j``-th distinct message the adversary looks up, and programs it *at that moment*, while the
    point is still fresh. A wrong bet aborts. The simulation is perfect when the bet is right, so the
    success probability is about ``1 / (max_messages + 1)`` — a loss factor of the number of oracle
    queries, which is what "tight" was claiming to avoid.
    """

    name = "Theorem 1 repaired by guessing the approval message"

    def __init__(self, params, instance, seed, honest_seat=0, domain=1, *, max_messages: int = 1):
        super().__init__(params, instance, seed, honest_seat, domain)
        self.max_messages = max_messages
        self._guess = self._rng.randrange(max_messages + 1)
        self._messages_seen: list[bytes] = []
        self._programmed: bytes | None = None
        self.claimed_success_given_win = 1.0 / (max_messages + 1)

    def challenge(self, message: bytes, salt: int = 0):
        if message not in self._messages_seen:
            self._messages_seen.append(message)
            if len(self._messages_seen) == self._guess and self._programmed is None:
                self._program(message, salt)
                self._programmed = message
        return super().challenge(message, salt)

    def request_approval(self, message: bytes) -> tuple[int, int]:
        if message not in self._approval:
            fresh = message not in self._messages_seen
            if self._programmed is None and fresh and self._guess == 0:
                self._program(message, 0)
                self._programmed = message
            if self._programmed != message:
                raise SimulationFailed(
                    f"guessed wrong: bet on message index {self._guess}, but the approval was "
                    f"requested for {message!r}")
            self._approval[message] = (self.instance.handle, 0)
            self._approved.add(message)
        return self._approval[message]


class FrameToAF1WrongSeat(FrameToAF1):
    """A deliberately broken reduction — the runner's own control.

    It embeds the instance in a seat *other* than the honest one. Everything still runs, the
    adversary still wins, and the reduction still outputs an opening: the honest seat's, which the
    reduction sampled itself and which has nothing to do with the instance. A runner that does not
    flag this output as not solving the problem cannot be trusted when it says another reduction holds.
    """

    name = "CONTROL: a broken reduction (instance embedded in the wrong seat)"

    def _seat_to_embed(self, honest_seat: int, params: Params) -> int:
        return (honest_seat + 1) % params.seats

    def _program(self, message, salt):                               # never reached
        raise AssertionError("the broken control answers approvals honestly")


class EvasionToCollision:
    """Theorem 2, step 2 (binding): a double-signer the extractor misses yields a collision of F.

        If (s, r) != (s', r') then x = s|r != x' = s'|r' with F(x) = F(x'), a collision. To output
        it, the reduction needs both openings: it runs the QROM online extractor of Pi_B on both
        proofs.

    A-F2 is a plain search problem on the public map, so there is nothing to embed and the simulated
    world *is* the real one. What is idealised is the step the record itself flags as costly: the
    openings come from :attr:`IdealProver.seen` — the witnesses the ideal functionality was shown —
    standing in for the online extractor. That extractor is part of Theorem 3's machinery and is
    not run here; this checks the logic *given* the openings, and says so in the report.
    """

    name = "Theorem 2 step 2: evasion -> collision of F (openings via the ideal prover)"
    claimed_success_given_win = 1.0

    def __init__(self, params: Params, seed: int, domain: int = 1):
        self.scheme = Scheme(params)
        self.oracle = RandomOracle(random.Random(seed).getrandbits(64))
        self.domain, self.registry, self.prover = domain, None, None

    def register(self, keys: list[int]) -> None:
        self.registry = Registry(list(keys))
        self.prover = IdealProver(self.scheme, self.registry, self.oracle)

    def certify(self, message: bytes, witnesses) -> Certificate:
        return self.prover.certify(self.domain, message, list(witnesses))

    def judge(self, output) -> FrameOutcome:
        """The adversary wins if a seat that signed both messages is missing from the extraction."""
        if not output:
            return FrameOutcome(False, "the adversary produced no certificates")
        c0, c1 = output
        if not (self.prover.verify(c0) and self.prover.verify(c1)) or c0.message == c1.message:
            return FrameOutcome(False, "not two accepted, conflicting certificates")
        named = self.scheme.extract(self.oracle, self.registry, c0, c1)
        signed = [set(entry["openings"]) for entry in self.prover.seen]
        common = signed[0] & signed[1]
        missing = sorted(common - {entry.seat for entry in named})
        if missing:
            return FrameOutcome(True, f"double-signing seat(s) {missing} were not named", named, (c0, c1))
        return FrameOutcome(False, f"all {len(common)} double-signing seats were named", named, (c0, c1))

    def solve(self, outcome: FrameOutcome) -> tuple[Opening, Opening] | None:
        if not outcome.adversary_won:
            return None
        first, second = (entry["openings"] for entry in self.prover.seen[:2])
        for seat in sorted(set(first) & set(second)):
            if first[seat] != second[seat]:
                return first[seat], second[seat]
        return None
