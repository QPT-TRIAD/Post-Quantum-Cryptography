"""Seeding: one derivation, recorded as it is used, so a reported result can be re-derived.

**Why this module is not just ``np.random.default_rng(seed)``.** The simulator this project replaces
drew its secret with an unseeded ``secrets.randbelow(N)``. The run was reproducible in the sense
that mattered to nobody: re-running it produced a different problem, a different marked-set size
``M``, and therefore a different success curve. Nothing in its recorded output said which draw had
happened, so no one could tell a genuine change in the numbers from a fresh roll of the dice.

The contract this module exists to hold is the project's: **every run is seeded, and its marked-set
size ``M`` is fixed and reported**. Three things fall out of that and each of them is a function
here.

1. Seeds are *derived*, not chosen. :func:`derive_seed` turns the names of the things a run is
   about — ``("lmots_chain", n, k, fold_bits)`` — into an integer, by a digest that is stable
   across processes, machines, and Python versions. A seed derived from a description can be
   re-derived from the same description, which is what makes a written-down result checkable.
2. The derivation is a digest rather than ``hash()``. Python's built-in string hash is salted per
   process: the same program with the same arguments gives different seeds under a different
   ``PYTHONHASHSEED``. A "reproducible" run that depends on an environment variable is not one.
3. Every seed actually used is written into a :class:`RunSeeds` record as it is handed out,
   *including a root drawn from the operating system when the caller did not supply one*. That is
   the whole trick: a run may start from entropy — it may even match the old behaviour and start
   from ``secrets`` — but the moment it does, the value is in the record, and the record alone
   reproduces the run.

The record is deliberately checkable rather than merely readable. :meth:`RunSeeds.verify`
re-derives every entry from the recorded root and the recorded parts, so a record that has been
edited, truncated, or produced by a different derivation is caught instead of being fed back into a
"reproduction" that quietly reports different numbers.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from typing import Any

import numpy as np

__all__ = [
    "DOMAIN",
    "SEED_BITS",
    "derive_seed",
    "rng_for",
    "RunSeeds",
]

DOMAIN = b"grover-oracle-emulator/seed/v1"
"""Domain separator, versioned. Changing the derivation means changing this, so an old record is
rejected by :meth:`RunSeeds.verify` rather than silently re-deriving different seeds."""

SEED_BITS = 64
"""Width of a derived seed. 64 bits is far more than the small instances here can collide on, and a
machine word keeps a seed readable in a log line."""


def _encode_part(part: str | int | bytes | None) -> bytes:
    """One part of a derivation, in a form no other part sequence can produce.

    The length prefix is the load-bearing part. Without it ``("ab", "c")`` and ``("a", "bc")``
    concatenate to the same bytes, two different problems would share a seed, and the day a caller
    renames a label the results would silently change while the record still verified. With it, the
    encoding is injective, and injective encoding is what makes "same description, same seed" a
    property rather than a hope.
    """
    if isinstance(part, bool):
        # bool is an int subclass; tagging it separately keeps `True` from silently colliding with
        # `1` in a call that meant different things.
        payload = ("1" if part else "0").encode("ascii")
        tag = b"l"
    elif isinstance(part, int):
        payload = str(part).encode("ascii")
        tag = b"i"
    elif isinstance(part, str):
        payload = part.encode("utf-8")
        tag = b"s"
    elif isinstance(part, (bytes, bytearray)):
        payload = bytes(part)
        tag = b"b"
    elif part is None:
        payload = b""
        tag = b"n"
    else:
        raise TypeError(
            f"cannot derive a seed from {part!r} ({type(part).__name__}); "
            "parts must be int, str, bytes, or None"
        )
    return tag + len(payload).to_bytes(8, "big") + payload


def derive_seed(*parts: str | int | bytes | None) -> int:
    """A stable integer seed for the description ``parts``.

    Stable means: the same request gives the same integer in a different process, under a different
    ``PYTHONHASHSEED``, on a different machine, in a later Python, and on a case-insensitive
    filesystem. It is a blake2b digest of a length-prefixed encoding of the parts under
    :data:`DOMAIN` — not ``hash()``, whose salting would make the value a property of the
    environment rather than of the description, and not a global counter, which would make it a
    property of the order the caller happened to build things in.

    Args:
        *parts: the description. Strings name the thing (``"lmots_chain"``), integers give its
            parameters (``n_qubits``, ``chain_length``, ``seed``). Order matters, types matter, and
            ``("ab", "c")`` is not ``("a", "bc")``.

    Returns:
        An integer in ``[0, 2**SEED_BITS)``.
    """
    digest = hashlib.blake2b(digest_size=SEED_BITS // 8)
    digest.update(DOMAIN)
    for part in parts:
        digest.update(_encode_part(part))
    return int.from_bytes(digest.digest(), "big")


def rng_for(seed: int) -> np.random.Generator:
    """A fresh generator for ``seed``.

    ``numpy.random.Generator`` is the modern API and, importantly here, NumPy's own compatibility
    policy guarantees a stable stream for a given bit generator and seed across versions — so a
    recorded seed really does replay, rather than replaying until the next NumPy release. The bit
    generator is left at the default (PCG64) and is deliberately not named in a record: a stream is
    reproducible from ``(seed, bit generator)`` and only the seed is worth writing down.
    """
    if seed < 0:
        raise ValueError(f"seed must be non-negative, got {seed}")
    return np.random.default_rng(seed)


def _jsonable(value: Any) -> Any:
    """Coerce the values a record is likely to hold into something JSON can write.

    NumPy scalars are the common case — ``len(...)`` of a numpy array is a Python int, but a
    measured fraction or a drawn index often is not — and a record that raises inside ``json.dumps``
    after a long run is a record that gets dropped from the results. Anything else is passed through
    unchanged so that a genuinely unserialisable value fails loudly at the point of writing rather
    than being silently stringified into a lie.
    """
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return value


@dataclass
class RunSeeds:
    """Every seed a run used, plus the measured facts that belong with them.

    Hand this around instead of a bare integer. The object *is* the reproducibility claim: seeding
    a run from :meth:`rng` and reporting :meth:`to_dict` alongside the numbers means the numbers can
    be re-derived by anyone holding the report, which is exactly what the simulator this replaces
    could not offer.

    Construction with ``root=None`` draws the root from the operating system, which is allowed and
    is recorded. That is the point: a run is free to start from entropy, because the value it drew
    goes into the record. The failure mode being avoided is not "a random start" — it is "a random
    start nobody wrote down".

    Example:
        >>> seeds = RunSeeds(root=20260913)
        >>> seeds.derive("spec", 10, 2) == seeds.derive("spec", 10, 2)
        True
        >>> seeds.rng("spec", 10, 2).integers(0, 1000)  # doctest: +SKIP
        ...

    Attributes:
        root: the root seed, whether supplied or drawn from the OS.
        auto_root: True when ``root`` came from the OS rather than from the caller. Recorded because
            a drawn root is a fact about the run — a reader is entitled to know that the instance
            was not the one a previous report described.
        derived: ``label -> {"parts": [...], "seed": int}``. The parts are kept so
            :meth:`verify` can re-derive, which is what turns the record from a log into a check.
        facts: ``label -> JSON-safe measured value``. Where the marked-set size ``M``, the truth
            table's digest, or any other reported quantity goes.
    """

    root: int
    auto_root: bool = False
    derived: dict[str, dict[str, Any]] = field(default_factory=dict)
    facts: dict[str, Any] = field(default_factory=dict)

    # -- construction ---------------------------------------------------------------------------

    @classmethod
    def new(cls, root: int | None = None) -> "RunSeeds":
        """Start a record, drawing the root from the OS when none is given.

        ``secrets.randbits`` is used rather than ``random`` so that the drawn root does not come
        from a stream some other part of the program may also be consuming — the value must be the
        run's alone, since it is the run's identity.
        """
        if root is None:
            return cls(root=secrets.randbits(SEED_BITS), auto_root=True)
        return cls(root=root)

    # -- use ------------------------------------------------------------------------------------

    def derive(self, *parts: str | int | bytes | None) -> int:
        """A seed for ``parts``, derived from the root and recorded under its label.

        Idempotent: asking twice for the same description returns the same integer and does not
        touch the record twice, so a function that needs a seed can ask for it wherever it is
        needed without coordinating with anyone.

        Raises:
            ValueError: if two different descriptions share a label AND derive different seeds —
                a collision the record could not represent. The label is the parts joined by
                ``'.'``, so this fires on ``("a.b", "c")`` versus ``("a", "b.c")``, which is rare
                and is a naming problem rather than a seeding one, but a record that silently
                dropped one of the two would be worse than an exception.
        """
        label = ".".join(_label_part(part) for part in parts)
        seed = derive_seed(self.root, *parts)
        existing = self.derived.get(label)
        if existing is None:
            self.derived[label] = {"parts": [_recorded_part(p) for p in parts], "seed": seed}
        elif existing["seed"] != seed:
            raise ValueError(
                f"label {label!r} is already recorded with a different seed; two distinct "
                "derivations must not share a label"
            )
        return seed

    def rng(self, *parts: str | int | bytes | None) -> np.random.Generator:
        """A generator for the seed of ``parts``, recorded by :meth:`derive`."""
        return rng_for(self.derive(*parts))

    def record(self, label: str, value: Any) -> None:
        """Record a measured fact — the marked-set size ``M``, a gate count, a peak.

        Facts are recorded rather than logged because the record is the artifact that reproduces
        the run, and ``M`` is fixed by the seed: a result that reports a success curve without the
        ``M`` it was computed against is not reporting a measurement.
        """
        self.facts[label] = _jsonable(value)

    def mark(self, label: str, seed: int) -> None:
        """Record a seed obtained some other way, so the record still covers every draw.

        A run that mixes derived seeds with a seed someone passed in has to record both, or the
        record no longer determines the run. This is the escape hatch that keeps that possible.
        """
        self.derived[label] = {"parts": ["<external>"], "seed": int(seed)}

    # -- reporting ------------------------------------------------------------------------------

    def verify(self) -> None:
        """Re-derive every recorded seed and raise if any of them disagrees.

        This is the difference between a record and a claim. A record produced by one version of
        the derivation, or edited after the fact, verifies against nothing — and here that shows up
        as a ``ValueError`` at the point of reading rather than as a reproduction that quietly
        produces different numbers under the same heading.
        """
        for label, entry in self.derived.items():
            if entry["parts"] == ["<external>"]:
                continue
            # The record spells a bytes part in a tagged form (see `_recorded_part`); the seed was
            # derived from the bytes themselves, so they are restored before re-deriving. Feeding
            # the recorded spelling back in would encode it under the wrong type tag and every
            # record holding a bytes part would fail its own verification.
            parts = tuple(_restored_part(part) for part in entry["parts"])
            expected = derive_seed(self.root, *parts)
            if expected != entry["seed"]:
                raise ValueError(
                    f"record entry {label!r} does not re-derive: recorded {entry['seed']}, "
                    f"derived {expected} from root {self.root} and parts {parts!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        """A JSON-safe form, for a results file or a report."""
        return {
            "root": self.root,
            "auto_root": self.auto_root,
            "derived": {k: dict(v) for k, v in self.derived.items()},
            "facts": dict(self.facts),
        }

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "RunSeeds":
        """Rebuild a record written by :meth:`to_dict`.

        The seeds come back as the integers that ran, not as a re-derivation, so a report from a
        machine with a different derivation still replays the run it describes. :meth:`verify` is
        the check that says whether that replay is the same problem.
        """
        return cls(
            root=int(record["root"]),
            auto_root=bool(record.get("auto_root", False)),
            derived={k: dict(v) for k, v in record.get("derived", {}).items()},
            facts=dict(record.get("facts", {})),
        )

    def describe(self) -> dict[str, Any]:
        """The record's shape for a report: what was drawn, and what was measured."""
        return {
            "root": self.root,
            "auto_root": self.auto_root,
            "n_derived": len(self.derived),
            "labels": sorted(self.derived),
            "facts": dict(self.facts),
        }

    def __str__(self) -> str:
        origin = "drawn" if self.auto_root else "supplied"
        return (
            f"RunSeeds(root={self.root} [{origin}], {len(self.derived)} derived, "
            f"{len(self.facts)} fact(s))"
        )


def _label_part(part: str | int | bytes | None) -> str:
    return part.decode("utf-8", "replace") if isinstance(part, (bytes, bytearray)) else str(part)


_BYTES_KEY = "bytes_hex"
"""The key that marks a recorded part as bytes. No other part type records as a mapping."""


def _recorded_part(part: str | int | bytes | None) -> Any:
    """The part as it goes into a record: JSON cannot hold bytes, so they are spelled as tagged hex.

    A bytes part is recorded as ``{"bytes_hex": "..."}`` rather than as decoded text, for two
    reasons. The derivation is typed — ``b"abc"`` and ``"abc"`` are different descriptions with
    different seeds — so a text spelling would come back from the record as a ``str`` and
    :meth:`RunSeeds.verify` would re-derive a seed that never ran. And decoding is lossy: bytes that
    are not valid UTF-8 would be recorded as replacement characters, from which nothing re-derives.
    Hex under a tag is exact, JSON-safe, and cannot be mistaken for any other part type, so a bytes
    part round-trips through :meth:`RunSeeds.to_dict` and :meth:`RunSeeds.from_dict` and
    :meth:`RunSeeds.verify` still checks the seed that actually ran. ``str``, ``int`` and ``None``
    parts are recorded as themselves, exactly as before, so existing records stay valid. The
    readable spelling of a bytes part is the entry's label (see :func:`_label_part`).
    """
    if isinstance(part, (bytes, bytearray)):
        return {_BYTES_KEY: bytes(part).hex()}
    return part


def _restored_part(recorded: Any) -> Any:
    """The typed part a recorded one stands for — the inverse of :func:`_recorded_part`.

    Anything that is not the tagged bytes form is returned unchanged, so a record edited into a
    shape no derivation produces still reaches ``derive_seed`` and fails there or at the comparison,
    rather than being quietly repaired here.
    """
    if isinstance(recorded, dict) and set(recorded) == {_BYTES_KEY}:
        return bytes.fromhex(recorded[_BYTES_KEY])
    return recorded
