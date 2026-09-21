"""Exhaustive search: the baseline every other attack has to beat.

Against the key map the search runs over ``r`` only. The handle is linear in ``s``, so each guess of
``r`` fixes ``s = c^-1 (Z + G(r))`` and the pair is tested against the public key — ``2^n``
candidates, not ``2^{2n}``. That is the record's own framing attack (its attack lab measures a mean
of ``2^{n-1}``), and it is the curve the "128-bit" in QPT-128 ultimately rests on at ``n = 256``.

The search starts at a seeded random offset and walks the space in order, so the work to hit a
fixed secret is uniform on ``[1, 2^n]`` with mean ``2^{n-1}``: the measured curve is compared with
that, not with ``2^n``. (Where the function has other preimages the first hit comes sooner — see
:mod:`qpt_cart.primitives.controls` for the ``2^n / e`` this gives a random function.)
"""

from __future__ import annotations

import hashlib
import time

from ..primitives.keymap import KeyMapScheme, Opening, Transcript
from .base import AttackResult

__all__ = ["brute_force_keymap", "brute_force_function"]


def _offset(seed: int, size: int) -> int:
    return int.from_bytes(hashlib.sha256(b"qpt-cart/bf/offset" + seed.to_bytes(8, "big")).digest(),
                          "big") % (1 << size)


def brute_force_keymap(scheme: KeyMapScheme, transcript: Transcript, *, seed: int = 0,
                       max_seconds: float = 120.0) -> AttackResult:
    n, field, start = scheme.n, scheme.field, _offset(seed, scheme.n)
    c_inv, space, began = field.inv(transcript.challenge), 1 << scheme.n, time.perf_counter()
    found, tried = None, 0
    for step in range(space):
        r = (start + step) % space
        s = field.mul(c_inv, transcript.handle ^ scheme.G(r))
        tried += 1
        if scheme.map.matches(s | (r << n), transcript.public_key):
            found = Opening(s, r)
            break
        if not tried & 0x3FF and time.perf_counter() - began > max_seconds:
            break
    seconds = time.perf_counter() - began
    ok = found is not None and scheme.verify(transcript, found)
    return AttackResult(
        attack="brute_force", primitive=f"keymap/mode{scheme.mode.value}", size=n, seed=seed,
        success=ok, verified=ok, work=float(tried), work_unit="openings tried", seconds=seconds,
        detail={"space_log2": n, "expected_mean_work_log2": n - 1, "equations": scheme.m_eqs},
        not_run_reason=None if ok else f"budget of {max_seconds}s exhausted after {tried} openings",
    )


def brute_force_function(control, public: int, *, seed: int = 0, max_seconds: float = 120.0,
                         name: str = "control") -> AttackResult:
    """Exhaustive preimage search on anything with ``n`` and ``evaluate`` — the controls."""
    n, start, space, began = control.n, _offset(seed, control.n), 1 << control.n, time.perf_counter()
    found, tried = None, 0
    for step in range(space):
        x = (start + step) % space
        tried += 1
        if control.evaluate(x) == public:
            found = x
            break
        if not tried & 0x3FF and time.perf_counter() - began > max_seconds:
            break
    seconds = time.perf_counter() - began
    ok = found is not None
    return AttackResult(
        attack="brute_force", primitive=name, size=n, seed=seed, success=ok, verified=ok,
        work=float(tried), work_unit="inputs tried", seconds=seconds,
        # no expected mean is recorded: it depends on how many preimages the function gives the
        # target, which is the function's business and not this search's
        detail={"space_log2": n},
        not_run_reason=None if ok else f"budget of {max_seconds}s exhausted after {tried} inputs",
    )
