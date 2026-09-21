"""The hidden-signer key map and handle, with nothing around them.

This is the raw primitive of QPT-128's hidden-signer modes, as ``hidden_signer_modeB_v1.46.py`` in
the research record defines it, lifted out of its frames, registries and proofs:

    secret      an opening ``(s, r)``, two elements of GF(2^n)
    public key  ``Y = F(s | r << n)``, where ``F : F_2^{2n} -> F_2^{2n+E}`` is a dense random
                quadratic map fixed by a public seed (one equation per output bit)
    response    the handle ``Z = G(r) + c*s`` to a public challenge ``c != 0``, with ``G(r) = r^7``
                in Mode B and ``G(r) = r`` in Mode A
    verify      ``F(s | r << n) == Y`` and ``G(r) + c*s == Z``

QPT-128 has no key *encapsulation* of its own — its only KEM is standard ML-KEM-1024 — so the three
operations exposed here are the ones this primitive actually has: ``keygen``, ``respond``,
``verify``. The attack goal is the record's framing game: given ``(Y, c, Z)``, produce an opening
that verifies.

**Scaling.** The record fixes ``n = 256`` and an expansion ``E`` of 300 (the Python reference) or
512 (the C prover and the ledger) — it disagrees with itself, so both are selectable. Shrinking
``n`` while keeping ``E`` fixed would make every small instance absurdly over-determined (at
``n = 8``, 316 equations in 16 unknowns falls to plain linearisation) and the measured curve would
describe the scaling mistake rather than the scheme. So ``E`` scales with ``n`` at the production
*ratio*, and :class:`ScalingRule` records that choice as data so a report can state it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

from .gf2n import Field

__all__ = ["HandleMode", "ScalingRule", "QuadMap", "KeyMapScheme", "Opening", "Transcript"]

PRODUCTION_N = 256


class HandleMode(str, Enum):
    A = "A"
    """Linear handle ``Z = r + c*s``. The record scores it at 148.8 classical bits at n = 256 —
    below target — because ``r`` can be eliminated, halving the unknowns."""
    B = "B"
    """Power handle ``Z = r^7 + c*s``: algebraic degree 3 in the bits of ``r``."""


@dataclass(frozen=True)
class ScalingRule:
    """How a production parameter set is shrunk to size ``n`` — recorded, so it can be reported."""

    production_n: int = PRODUCTION_N
    production_expansion: int = 300
    source: str = "hidden_signer_modeB_v1.46.py:110-112 (E = 300); modeB_prover_v1.51.c:57 uses 512"

    @property
    def ratio(self) -> float:
        return self.production_expansion / self.production_n

    def expansion_at(self, n: int) -> int:
        """``E`` at size ``n``: the production ratio, rounded, and never below one equation."""
        return max(1, round(self.ratio * n))

    def equations_at(self, n: int) -> int:
        return 2 * n + self.expansion_at(n)


class QuadMap:
    """A dense random quadratic map over F_2, one equation per output bit, from a public seed.

    Equation ``e`` is ``const[e] + <lin[e], x> + sum_{i<j} Q_e[i][j] x_i x_j``. ``rows[e][i]`` is the
    mask of ``j > i`` with ``Q_e[i][j] = 1``. Dense — every coefficient is a fair coin — which is
    the map every security estimate in the record is for; the C prover's sparse default is a
    different map that no estimate covers, and it is deliberately not what is built here.
    """

    def __init__(self, n_vars: int, m_eqs: int, seed: bytes):
        self.n_vars, self.m_eqs, self.seed = n_vars, m_eqs, seed
        nbytes = (n_vars + 7) // 8
        stream = hashlib.shake_256(b"qpt-cart/F/v1" + seed).digest(m_eqs * (1 + nbytes * (n_vars + 1)))
        mask, pos = (1 << n_vars) - 1, 0
        self.const: list[int] = []
        self.lin: list[int] = []
        self.rows: list[list[int]] = []
        for _ in range(m_eqs):
            self.const.append(stream[pos] & 1)
            pos += 1
            self.lin.append(int.from_bytes(stream[pos:pos + nbytes], "big") & mask)
            pos += nbytes
            rows = []
            for i in range(n_vars):
                row = int.from_bytes(stream[pos:pos + nbytes], "big") & mask
                pos += nbytes
                rows.append(row & ~((1 << (i + 1)) - 1))            # keep j > i only
            self.rows.append(rows)

    def equation(self, e: int, x: int) -> int:
        acc = self.const[e] ^ ((self.lin[e] & x).bit_count() & 1)
        rows = self.rows[e]
        bits = x
        while bits:
            low = bits & -bits
            acc ^= (rows[low.bit_length() - 1] & x).bit_count() & 1
            bits ^= low
        return acc

    def evaluate(self, x: int) -> int:
        """The ``m``-bit output; bit ``e`` is equation ``e``."""
        if not 0 <= x < (1 << self.n_vars):
            raise ValueError("input out of range")
        return sum(self.equation(e, x) << e for e in range(self.m_eqs))

    def matches(self, x: int, y: int) -> bool:
        """``F(x) == y``, abandoning at the first equation that disagrees.

        This is how an exhaustive attacker evaluates the map: a wrong candidate fails half the
        time on each equation, so it costs two equations on average, not ``m``. Counting a
        candidate as one unit of work is therefore fair to the attacker, which is the direction
        an attack-cost measurement has to err in.
        """
        return all(self.equation(e, x) == (y >> e) & 1 for e in range(self.m_eqs))


@dataclass(frozen=True)
class Opening:
    s: int
    r: int


@dataclass(frozen=True)
class Transcript:
    """Everything public about one seat's response: what an attacker is handed."""

    public_key: int
    challenge: int
    handle: int


class KeyMapScheme:
    """The primitive at size ``n``: ``keygen``, ``respond``, ``verify``."""

    POWER = 7

    def __init__(self, n: int, mode: HandleMode = HandleMode.B, *, rule: ScalingRule | None = None,
                 seed: bytes = b"qpt-cart/keymap-seed/v1"):
        self.n, self.mode = n, HandleMode(mode)
        self.rule = rule or ScalingRule()
        self.field = Field(n)
        if self.mode is HandleMode.B and not self.field.power_is_permutation(self.POWER):
            raise ValueError(
                f"r -> r^7 is not a permutation of GF(2^{n}) (7 divides 2^{n} - 1, i.e. 3 | n); the "
                "production field n = 256 has it as one, so a scaled instance must too — choose n "
                "not divisible by 3"
            )
        self.expansion = self.rule.expansion_at(n)
        self.m_eqs = self.rule.equations_at(n)
        self.map = QuadMap(2 * n, self.m_eqs, seed + n.to_bytes(2, "big"))

    # -- the three operations ------------------------------------------------------------------

    def keygen(self, seed: int) -> tuple[Opening, int]:
        """A uniformly random opening and its public key, deterministic in ``seed``."""
        nbytes = (self.n + 7) // 8
        stream = hashlib.shake_256(b"qpt-cart/keygen/v1" + seed.to_bytes(8, "big")
                                   + self.n.to_bytes(2, "big")).digest(2 * nbytes)
        s = int.from_bytes(stream[:nbytes], "big") & self.field.order
        r = int.from_bytes(stream[nbytes:], "big") & self.field.order
        opening = Opening(s, r)
        return opening, self.public_key(opening)

    def pack(self, opening: Opening) -> int:
        return opening.s | (opening.r << self.n)

    def public_key(self, opening: Opening) -> int:
        return self.map.evaluate(self.pack(opening))

    def G(self, r: int) -> int:
        return self.field.pow(r, self.POWER) if self.mode is HandleMode.B else r

    def respond(self, opening: Opening, challenge: int) -> int:
        """The handle ``Z = G(r) + c*s``."""
        if not 0 < challenge <= self.field.order:
            raise ValueError("the challenge must be a non-zero field element")
        return self.G(opening.r) ^ self.field.mul(challenge, opening.s)

    def verify(self, transcript: Transcript, opening: Opening) -> bool:
        return (
            0 <= opening.s <= self.field.order and 0 <= opening.r <= self.field.order
            and self.respond(opening, transcript.challenge) == transcript.handle
            and self.map.matches(self.pack(opening), transcript.public_key)
        )

    def transcript(self, seed: int, challenge: int | None = None) -> tuple[Opening, Transcript]:
        """A keypair and one honest response — the attacker's input, with the answer beside it."""
        opening, public_key = self.keygen(seed)
        if challenge is None:
            digest = hashlib.shake_256(b"qpt-cart/challenge/v1" + seed.to_bytes(8, "big")).digest(
                (self.n + 7) // 8)
            challenge = (int.from_bytes(digest, "big") & self.field.order) or 1
        return opening, Transcript(public_key, challenge, self.respond(opening, challenge))

    def s_from_r(self, transcript: Transcript, r: int) -> int:
        """The handle is linear in ``s``, so each guess of ``r`` determines ``s`` — which is why
        exhaustive search runs over ``2^n`` openings and not ``2^{2n}``."""
        return self.field.mul(self.field.inv(transcript.challenge), transcript.handle ^ self.G(r))
