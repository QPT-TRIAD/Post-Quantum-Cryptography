"""Seeded, reproducible randomness — and a record that makes reproducibility checkable.

Two failures motivate this module rather than ad-hoc ``np.random.default_rng`` calls.

The first is an unseeded draw. The sibling Grover project's corpus oracle inherited one from the
research code it reproduced: a secret drawn with an unseeded generator, so the size of the marked
set varied per run and a recorded result could not be reproduced. Here that would be worse than
inconvenient — a lattice instance whose secret, base and pivot rows differ between runs produces a
different lattice, so a recorded Hermite factor would describe an instance that no longer exists.

The second is subtler: a run that *was* seeded but cannot be re-derived from what it recorded. A
seed that is only in the process's memory is not a reproducibility guarantee. ``RunSeeds`` carries
the root seed and every derived one into the results file, and :meth:`RunSeeds.verify` re-derives
them from that record, so the record is checked rather than trusted.

Derivation is by domain-separated hashing rather than by a counter, so a new draw can be added in
the middle of a pipeline without changing the seed of anything already after it. A counter would
silently renumber every subsequent draw — the kind of change that alters results while looking like
a refactor.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
from dataclasses import dataclass, field
from typing import Any

__all__ = ["DOMAIN", "derive_seed", "rng_for", "RunSeeds", "SEED_BITS"]

#: Namespace for every hash in this project, so a seed derived here can never collide with one
#: derived by a different tool from the same words.
DOMAIN = b"qlwr-lattice-stress/seed/v1"

#: Seeds are 64-bit. numpy's Generator accepts arbitrary non-negative ints, and fpylll and G6K take
#: plain ints; 64 bits is comfortably beyond what any of them consume.
SEED_BITS = 64
_SEED_MODULUS = 1 << SEED_BITS


def _hash(parts: tuple[Any, ...]) -> bytes:
    h = hashlib.sha256()
    h.update(DOMAIN)
    for part in parts:
        if isinstance(part, bytes):
            payload = part
        elif isinstance(part, str):
            payload = part.encode("utf-8")
        elif isinstance(part, int):
            # Sign byte plus minimal big-endian magnitude. A fixed-width signed encoding cannot
            # represent the whole non-negative range (``struct.pack(">q", 2**64 - 1)`` raises), and
            # a seed derivation that rejects large indices is a trap for a caller who has one. This
            # form covers every int and keeps -1 distinct from every unsigned value.
            sign = b"\x01" if part < 0 else b"\x00"
            magnitude = abs(part)
            payload = sign + magnitude.to_bytes(max(1, (magnitude.bit_length() + 7) // 8), "big")
        else:
            raise TypeError(f"seed part {part!r} is {type(part).__name__}; use str, int or bytes")
        h.update(struct.pack(">I", len(payload)))
        h.update(payload)
    return h.digest()


def derive_seed(root: int, *parts: Any) -> int:
    """A seed for one named draw, from a root seed and a path.

    ``parts`` identify the draw, e.g. ``derive_seed(root, "instance", "base", seed)``. Adding a new
    part in the middle changes only the seeds below it, which is what makes the pipeline safe to
    extend.
    """
    if not isinstance(root, int) or root < 0:
        raise ValueError(f"root seed must be a non-negative int, got {root!r}")
    return int.from_bytes(_hash((root, *parts))[:8], "big") % _SEED_MODULUS


def rng_for(root: int, *parts: Any):
    """A ``numpy.random.Generator`` for one named draw.

    numpy is imported here rather than at module scope so that the exact-arithmetic parts of the
    project can use :func:`derive_seed` without pulling in a dependency they do not need.
    """
    import numpy as np

    return np.random.default_rng(derive_seed(root, *parts))


@dataclass
class RunSeeds:
    """The root seed of a run, and every seed derived from it.

    The derived seeds are recorded as they are handed out rather than recomputed at the end,
    because a pipeline that branches will not necessarily take the same branch twice — and a record
    that only lists the seeds a run *happened* to use is the record that makes a re-run differ.
    """

    root: int
    # Keyed by the parts *tuple*, not by a joined string. Flattening to a string and splitting it
    # back loses the type of every part -- ("sweep", 0) returns as ("sweep", "0") -- and an
    # integer part is precisely what the derivation distinguishes from its string form.
    _used: dict[tuple, int] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.root, int) or self.root < 0:
            raise ValueError(f"root seed must be a non-negative int, got {self.root!r}")

    def derive(self, *parts: Any) -> int:
        """Derive and *record* a seed. Prefer this over calling :func:`derive_seed` directly."""
        key = tuple(parts)
        if key in self._used:
            # Re-deriving the same path is legitimate (a function called twice with the same
            # arguments should get the same seed), but it must genuinely be the same seed.
            recomputed = derive_seed(self.root, *parts)
            if recomputed != self._used[key]:
                raise AssertionError(f"seed for {key!r} is not stable across derivations")
            return recomputed
        seed = derive_seed(self.root, *parts)
        self._used[key] = seed
        return seed

    def rng(self, *parts: Any):
        import numpy as np

        return np.random.default_rng(self.derive(*parts))

    def verify(self) -> None:
        """Re-derive every recorded seed from the root, and raise if any does not match.

        This is the check that a results file can be turned back into the run it describes. A
        mismatch means the derivation changed since the run — which would make the recorded results
        irreproducible while the file still looked complete.
        """
        for parts, recorded in self._used.items():
            recomputed = derive_seed(self.root, *parts)
            if recomputed != recorded:
                raise AssertionError(
                    f"seed {parts!r} recorded as {recorded} but re-derives to {recomputed}; "
                    "the derivation has changed since the run and the results are no longer "
                    "reproducible from their own record"
                )

    def to_dict(self) -> dict[str, Any]:
        # Serialised as a list of {parts, seed} rather than a mapping, because a JSON object key
        # would have to be a string -- which is exactly the type loss this records to avoid.
        return {
            "root": self.root,
            "derived": [
                {"parts": [str(p) if isinstance(p, str) else p for p in parts], "seed": seed}
                for parts, seed in sorted(self._used.items(), key=lambda kv: repr(kv[0]))
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RunSeeds:
        obj = cls(root=int(payload["root"]))
        for entry in payload.get("derived", []):
            parts = entry["parts"]
            obj._used[tuple(parts)] = int(entry["seed"])
        return obj

    def __str__(self) -> str:  # pragma: no cover - diagnostics
        return json.dumps(self.to_dict(), indent=2)


def root_from_environment(default: int) -> int:
    """A root seed from ``QLS_SEED``, so a sweep can be replayed without editing a config."""
    raw = os.environ.get("QLS_SEED")
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"QLS_SEED={raw!r} is not an integer") from exc
