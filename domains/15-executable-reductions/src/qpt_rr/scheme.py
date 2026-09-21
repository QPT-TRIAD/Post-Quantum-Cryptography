"""Mode B-r at toy size: registry, challenge oracle, handle, ideal prover, verifier, extractor.

This is the construction of ``modeB_security_v1.49.md`` section 1 in its current (v1.50) form:

    registration   seat i samples (s_i, r_i) in GF(2^n)^2 and publishes Y[i] = F(s_i | r_i << n)
    challenge      (c_a, c_b, c_c) = H("c", cfg, d, m, ctr), ctr the smallest counter for which
                   L_c(s) = c_a s + c_b s^2 + c_c s^4 is invertible (it is F_2-linear in s)
    handle         Z_i = r_i^7 + L_c(s_i)
    certificate    (cfg, d, m, the quorum's handles sorted strictly, proof)
    extraction     for two certificates with equal (cfg, d) and m0 != m1, for every pair of handles
                   solve (L_c0 + L_c1)(s) = Z0 + Z1, set r = (Z0 + L_c0(s))^(1/7), and name every
                   seat i with F(s | r << n) = Y[i]

Two things are idealised, and the record idealises them too:

* **The hash is a random oracle** — lazily sampled, and *programmable*, because the proofs program
  it. :class:`RandomOracle` records every query and refuses to program a point that has already
  been answered: an oracle that silently changed an answer it had given would let a reduction
  "succeed" by cheating, which is the one thing this runner must not allow.
* **The proof is the ideal functionality F_Prove** (the record's assumption A-Prove, a trusted
  aggregator). It certifies a statement only when handed a witness that satisfies the relation, and
  the verifier accepts exactly what it certified. So the proof system's soundness error is zero
  here *by construction*, and nothing in this package tests Theorem 3.

The key map, the field and the scaling rule are the attack tester's, imported rather than copied:
they are already tested there, and a second copy would be a second thing to get wrong.
"""

from __future__ import annotations

import hashlib
import os
import random
import sys
from dataclasses import dataclass, field
from math import gcd
from pathlib import Path

# The primitives come from the sibling package beside this one, under an explicit override if one
# is set. Its directory name differs between the two layouts this package is used in — a numbered
# domain inside the research repository, or a standalone checkout — so both names are tried.
_SIBLING_NAMES = ("14-classical-attack-surface", "qpt-classical-attack-tester")
_OVERRIDE = os.environ.get("QPT_RR_PRIMITIVES")
_CANDIDATES = ([Path(_OVERRIDE)] if _OVERRIDE
               else [Path(__file__).resolve().parents[3] / name / "src" for name in _SIBLING_NAMES])
for _CART in _CANDIDATES:
    if (_CART / "qpt_cart").is_dir():
        if str(_CART) not in sys.path:
            sys.path.insert(0, str(_CART))
        break

from qpt_cart.primitives.gf2n import Field                       # noqa: E402
from qpt_cart.primitives.keymap import QuadMap, ScalingRule      # noqa: E402

__all__ = ["Params", "Opening", "Certificate", "RandomOracle", "AlreadyQueried", "HandleCoincidence", "Registry",
           "IdealProver", "Scheme", "Named"]

#: Mode B-r fixes the expansion at 512 (assumption A-F2 is stated for it), where the older Python
#: reference used 300. Scaled by ratio, as in the attack tester: E = 2n.
MODE_B_R_RULE = ScalingRule(production_expansion=512,
                            source="modeB_security_v1.49.md section 1 and assumption A-F2 (E = 512)")


@dataclass(frozen=True)
class Params:
    """``n`` bits of field; ``seats`` and ``quorum`` keep the record's shape, where any two quorums
    overlap (production: 64 seats, quorum 43, overlap at least 22)."""

    n: int = 8
    seats: int = 6
    quorum: int = 4
    salted: bool = False
    """Not in the record. When set, an approving seat draws a random salt and the challenge is
    ``H("c", cfg, d, m, salt, ctr)``. It exists so the runner can show what a standard repair does
    to a reduction that fails without it; it is a candidate, not a vetted change to the scheme."""
    salt_bits: int = 64

    def __post_init__(self):
        if self.n % 3 == 0:
            raise ValueError("r -> r^7 must permute GF(2^n): choose n not divisible by 3")
        if not 0 < self.quorum <= self.seats or 2 * self.quorum <= self.seats:
            raise ValueError("need quorum <= seats < 2 * quorum, so that any two quorums overlap")

    @property
    def overlap(self) -> int:
        return 2 * self.quorum - self.seats


@dataclass(frozen=True)
class Opening:
    s: int
    r: int


@dataclass(frozen=True)
class Certificate:
    cfg: bytes
    domain: int
    message: bytes
    handles: tuple[int, ...]
    salts: tuple[int, ...]            # aligned with ``handles``; all zero when the scheme is unsalted
    token: bytes


@dataclass(frozen=True)
class Named:
    """One seat named by the public extraction, with the opening that is the evidence."""

    seat: int
    opening: Opening


class HandleCoincidence(ValueError):
    """Two handles of one certificate are equal, so they cannot be "sorted strictly".

    At production size this is the record's false-positive row (about ``2^-181``). At ``n = 8`` it
    is a few per cent, purely because a handle is eight bits wide. The runner redraws such a trial
    in both worlds and counts it, rather than relax a rule the real verifier enforces."""


class AlreadyQueried(RuntimeError):
    """A reduction tried to program an oracle point whose answer has already been given out."""


class RandomOracle:
    """A lazily sampled random oracle that can be programmed — once, and only at a fresh point."""

    def __init__(self, seed: int):
        self._rng = random.Random(seed)
        self._table: dict[tuple, int] = {}
        self.log: list[tuple[str, tuple]] = []            # (who asked, point)

    def query(self, point: tuple, bits: int, *, who: str = "adversary") -> int:
        self.log.append((who, point))
        if point not in self._table:
            self._table[point] = self._rng.getrandbits(bits)
        return self._table[point]

    def program(self, point: tuple, value: int) -> None:
        if point in self._table:
            raise AlreadyQueried(f"oracle point {point!r} was already answered; it cannot be reprogrammed")
        self._table[point] = value

    def answered(self, point: tuple) -> bool:
        return point in self._table

    def queries_by(self, who: str) -> list[tuple]:
        return [point for asker, point in self.log if asker == who]


class Scheme:
    """The arithmetic of Mode B-r at one size. No state: keys live in :class:`Registry`."""

    def __init__(self, params: Params, *, map_seed: bytes = b"qpt-rr/F/v1"):
        self.params = params
        self.n = params.n
        self.field = Field(params.n)
        self.map = QuadMap(2 * params.n, MODE_B_R_RULE.equations_at(params.n),
                           map_seed + params.n.to_bytes(2, "big"))
        order = self.field.order
        assert gcd(7, order) == 1
        self._seventh_root_exponent = pow(7, -1, order)

    # -- field pieces ------------------------------------------------------------------------------

    def L(self, triple: tuple[int, int, int], s: int) -> int:
        f = self.field
        s2 = f.mul(s, s)
        return f.mul(triple[0], s) ^ f.mul(triple[1], s2) ^ f.mul(triple[2], f.mul(s2, s2))

    def _columns(self, triple) -> list[int]:
        return [self.L(triple, 1 << j) for j in range(self.n)]

    def solve_linearized(self, triple, target: int) -> list[int]:
        """Every ``s`` with ``L_triple(s) = target`` — an affine space, enumerated (at most 4 when
        the map has 2-degree at most 2 and is not identically zero)."""
        n, columns = self.n, self._columns(triple)
        if not any(columns):
            return []                                     # D = 0: the two challenges coincide
        pivots: dict[int, tuple[int, int]] = {}          # leading output bit -> (image, preimage)
        kernel: list[int] = []
        for j, image in enumerate(columns):
            pre = 1 << j
            while image:
                top = image.bit_length() - 1
                if top not in pivots:
                    pivots[top] = (image, pre)
                    break
                image, pre = image ^ pivots[top][0], pre ^ pivots[top][1]
            else:
                kernel.append(pre)
        particular, rest = 0, target
        while rest:
            top = rest.bit_length() - 1
            if top not in pivots:
                return []
            rest, particular = rest ^ pivots[top][0], particular ^ pivots[top][1]
        solutions = [particular]
        for vector in kernel:
            solutions += [x ^ vector for x in solutions]
        return solutions

    def is_invertible(self, triple) -> bool:
        return len(self.solve_linearized(triple, 0)) == 1

    def seventh_root(self, x: int) -> int:
        return self.field.pow(x, self._seventh_root_exponent)

    def handle(self, opening: Opening, triple) -> int:
        return self.field.pow(opening.r, 7) ^ self.L(triple, opening.s)

    def pack(self, opening: Opening) -> int:
        return opening.s | (opening.r << self.n)

    def public_key(self, opening: Opening) -> int:
        return self.map.evaluate(self.pack(opening))

    def sample_opening(self, rng: random.Random) -> Opening:
        return Opening(rng.getrandbits(self.n), rng.getrandbits(self.n))

    def sample_invertible_triple(self, rng: random.Random) -> tuple[int, int, int]:
        while True:
            triple = (rng.getrandbits(self.n), rng.getrandbits(self.n), rng.getrandbits(self.n))
            if self.is_invertible(triple):
                return triple

    # -- the challenge -----------------------------------------------------------------------------

    def challenge_point(self, cfg: bytes, domain: int, message: bytes, salt: int, ctr: int) -> tuple:
        return ("c", cfg, domain, message, salt, ctr)

    def challenge(self, oracle: RandomOracle, cfg: bytes, domain: int, message: bytes, salt: int = 0,
                  *, who: str = "adversary") -> tuple[int, int, int]:
        """The first invertible triple along ``ctr = 0, 1, 2, ...`` — exactly the record's rule."""
        mask = (1 << self.n) - 1
        for ctr in range(1 << 16):
            raw = oracle.query(self.challenge_point(cfg, domain, message, salt, ctr), 3 * self.n, who=who)
            triple = (raw & mask, (raw >> self.n) & mask, raw >> (2 * self.n))
            if self.is_invertible(triple):
                return triple
        raise RuntimeError("no invertible challenge in 65536 counters")   # pragma: no cover

    def pack_triple(self, triple) -> int:
        return triple[0] | (triple[1] << self.n) | (triple[2] << (2 * self.n))

    # -- extraction --------------------------------------------------------------------------------

    def extract(self, oracle: RandomOracle, registry: "Registry", c0: Certificate, c1: Certificate
                ) -> list[Named]:
        """The public pair search. Every identified seat is reported; nothing aborts on a count."""
        if (c0.cfg, c0.domain) != (c1.cfg, c1.domain) or c0.message == c1.message:
            raise ValueError("extraction needs equal (cfg, domain) and two different messages")
        by_key = {key: seat for seat, key in enumerate(registry.keys)}
        named: dict[int, Named] = {}
        for z0, salt0 in zip(c0.handles, c0.salts):
            t0 = self.challenge(oracle, c0.cfg, c0.domain, c0.message, salt0, who="extractor")
            for z1, salt1 in zip(c1.handles, c1.salts):
                t1 = self.challenge(oracle, c1.cfg, c1.domain, c1.message, salt1, who="extractor")
                difference = (t0[0] ^ t1[0], t0[1] ^ t1[1], t0[2] ^ t1[2])
                for s in self.solve_linearized(difference, z0 ^ z1):
                    opening = Opening(s, self.seventh_root(z0 ^ self.L(t0, s)))
                    seat = by_key.get(self.public_key(opening))
                    if seat is not None:
                        named.setdefault(seat, Named(seat, opening))
        return [named[seat] for seat in sorted(named)]


@dataclass
class Registry:
    """The epoch's public keys, one per seat, and the configuration hash that commits to them."""

    keys: list[int]
    cfg: bytes = field(default=b"")

    def __post_init__(self):
        if not self.cfg:
            digest = hashlib.sha256(b"qpt-rr/cfg")
            for key in self.keys:
                digest.update(key.to_bytes((key.bit_length() + 7) // 8 or 1, "big") + b"|")
            self.cfg = digest.digest()[:8]


class IdealProver:
    """F_Prove: certifies exactly the statements it is shown a valid witness for.

    ``witnesses`` holds, per handle, the seat, its opening and the salt. The functionality checks the
    relation R_B of the record — distinct seats, the right count, ``F(opening) = Y[seat]`` — computes
    the handles itself, and remembers what it issued. :meth:`verify` accepts a certificate iff it was
    issued, unmodified. Every witness it is shown is kept in :attr:`seen`: that is this model's
    stand-in for the online extractor the record's Theorem 2 runs on the proofs, and it is labelled
    as an idealisation wherever it is used.
    """

    def __init__(self, scheme: Scheme, registry: Registry, oracle: RandomOracle):
        self.scheme, self.registry, self.oracle = scheme, registry, oracle
        self._issued: set[bytes] = set()
        self.seen: list[dict] = []

    def _token(self, cfg, domain, message, handles, salts) -> bytes:
        return hashlib.sha256(repr((cfg, domain, message, handles, salts)).encode()).digest()

    def certify(self, domain: int, message: bytes, witnesses: list[tuple[int, Opening, int]],
                *, trusted: dict[int, tuple[int, int]] | None = None) -> Certificate:
        """``trusted`` maps a seat to a ``(handle, salt)`` the functionality accepts without an
        opening. The real functionality never uses it. A *reduction* simulating F_Prove does, for
        the one seat whose opening it does not know — and that is legitimate exactly because the
        reduction is the functionality in its simulated world."""
        trusted = trusted or {}
        seats = [seat for seat, _, _ in witnesses] + list(trusted)
        if len(seats) != self.scheme.params.quorum or len(set(seats)) != len(seats):
            raise ValueError("a certificate needs exactly one handle from each of `quorum` distinct seats")
        entries = []
        for seat, opening, salt in witnesses:
            if self.scheme.public_key(opening) != self.registry.keys[seat]:
                raise ValueError(f"the opening offered for seat {seat} does not match its public key")
            triple = self.scheme.challenge(self.oracle, self.registry.cfg, domain, message, salt,
                                           who="prover")
            entries.append((self.scheme.handle(opening, triple), salt))
        entries += [trusted[seat] for seat in trusted]
        entries.sort()
        handles, salts = tuple(h for h, _ in entries), tuple(s for _, s in entries)
        if len(set(handles)) != len(handles):
            raise HandleCoincidence("handles must be strictly sorted; two coincide")
        self.seen.append({"domain": domain, "message": message,
                          "openings": {seat: opening for seat, opening, _ in witnesses}})
        token = self._token(self.registry.cfg, domain, message, handles, salts)
        self._issued.add(token)
        return Certificate(self.registry.cfg, domain, message, handles, salts, token)

    def verify(self, certificate: Certificate) -> bool:
        return (certificate.cfg == self.registry.cfg
                and len(certificate.handles) == self.scheme.params.quorum
                and list(certificate.handles) == sorted(set(certificate.handles))
                and certificate.token == self._token(certificate.cfg, certificate.domain,
                                                     certificate.message, certificate.handles,
                                                     certificate.salts)
                and certificate.token in self._issued)
