"""Collisions on the key map: the generic birthday search beside the structural shortcut.

Two attackers want ``x != x'`` with ``F(x) = F(x')``:

* **Birthday** treats ``F`` as a black box: hash random inputs until two outputs meet. About
  ``sqrt(pi/2 * 2^m)`` evaluations for an ``m``-bit output — the meet-in-the-middle-style
  time-for-memory attack that applies to *any* function.
* **The linear trick** uses what ``F`` is. For a fixed difference ``delta`` the quadratic terms of
  ``F(x + delta) + F(x)`` cancel, leaving a system that is *linear* in ``x``: ``m`` equations in
  ``2n`` unknowns, consistent with probability about ``2^-(m-2n) = 2^-E``. So a collision costs
  about ``2^E`` tries of ``delta``, each a Gaussian elimination — against ``2^{m/2} = 2^{n+E/2}``
  for the birthday search. With the record's ``E = 300`` at ``n = 256`` that is ``2^300`` against
  ``2^406``: the structural attack wins by a hundred bits, and the record knows it
  (``hidden_signer_modeB_v1.46.py:582``). What the record never does is *run* either one. Here both
  are run, and the measured exponents are set beside those two formulas.
"""

from __future__ import annotations

import hashlib
import time

from ..primitives.keymap import QuadMap
from .base import AttackResult

__all__ = ["birthday_collision", "linear_trick_collision", "difference_system"]


def _stream(label: bytes, seed: int, nbytes: int):
    counter = 0
    while True:
        block = hashlib.shake_256(label + seed.to_bytes(8, "big") + counter.to_bytes(8, "big")).digest(
            nbytes * 4096)
        for i in range(0, len(block), nbytes):
            yield int.from_bytes(block[i:i + nbytes], "big")
        counter += 1


def birthday_collision(qmap: QuadMap, *, seed: int = 0, max_seconds: float = 120.0) -> AttackResult:
    """The size this curve is drawn against is ``m``, the output width: the attack sees nothing else."""
    size = qmap.m_eqs
    mask, began, seen, tried, found = (1 << qmap.n_vars) - 1, time.perf_counter(), {}, 0, None
    for raw in _stream(b"qpt-cart/birthday", seed, (qmap.n_vars + 7) // 8):
        x = raw & mask
        y = qmap.evaluate(x)
        tried += 1
        other = seen.setdefault(y, x)
        if other != x:
            found = (other, x)
            break
        if not tried & 0xFF and time.perf_counter() - began > max_seconds:
            break
    seconds = time.perf_counter() - began
    ok = found is not None and found[0] != found[1] and qmap.evaluate(found[0]) == qmap.evaluate(found[1])
    return AttackResult(
        attack="birthday_collision", primitive="keymap/F", size=size, seed=seed, success=ok,
        verified=ok, work=float(tried), work_unit="evaluations of F", seconds=seconds,
        detail={"output_bits": qmap.m_eqs, "n": qmap.n_vars // 2,
                "expected_mean_work_log2": 0.5 * qmap.m_eqs + 0.326},
        not_run_reason=None if ok else f"budget of {max_seconds}s exhausted after {tried} evaluations",
    )


def difference_system(qmap: QuadMap, delta: int, symmetric: list[list[int]]):
    """``F(x + delta) + F(x) = 0`` as ``(coefficient mask over x, right-hand side)`` per equation.

    The coefficient of ``x_i`` in equation ``e`` is ``sum_j (Q + Q^T)_{ij} delta_j`` — the XOR of the
    symmetric matrix's rows selected by ``delta`` — and the constant is ``<lin, delta> + delta^T Q delta``.
    """
    for e in range(qmap.m_eqs):
        coeff, rhs, rows, sym = 0, (qmap.lin[e] & delta).bit_count() & 1, qmap.rows[e], symmetric[e]
        bits = delta
        while bits:
            low = bits & -bits
            i = low.bit_length() - 1
            coeff ^= sym[i]
            rhs ^= (rows[i] & delta).bit_count() & 1
            bits ^= low
        yield coeff, rhs


def _symmetric(qmap: QuadMap) -> list[list[int]]:
    out = []
    for rows in qmap.rows:
        sym = list(rows)
        for i, row in enumerate(rows):
            bits = row
            while bits:
                low = bits & -bits
                sym[low.bit_length() - 1] |= 1 << i
                bits ^= low
        out.append(sym)
    return out


def _solve(system) -> int | None:
    """One solution of a GF(2) linear system, or ``None`` at the first inconsistency."""
    pivots: dict[int, tuple[int, int]] = {}
    for coeff, rhs in system:
        while coeff:
            top = coeff.bit_length() - 1
            if top not in pivots:
                pivots[top] = (coeff, rhs)
                break
            pc, pr = pivots[top]
            coeff, rhs = coeff ^ pc, rhs ^ pr
        else:
            if rhs:
                return None
    x = 0
    for top in sorted(pivots):
        coeff, rhs = pivots[top]
        if rhs ^ ((coeff & x & ~(1 << top)).bit_count() & 1):
            x |= 1 << top
    return x


def linear_trick_collision(qmap: QuadMap, *, seed: int = 0, max_seconds: float = 120.0) -> AttackResult:
    """The size this curve is drawn against is ``E = m - 2n``, the over-determination: the cost is
    ``2^E`` whatever ``n`` is, and drawing it against ``n`` would only add the rounding of ``E``."""
    size = qmap.m_eqs - qmap.n_vars
    mask, began, tried, found = (1 << qmap.n_vars) - 1, time.perf_counter(), 0, None
    symmetric = _symmetric(qmap)
    for raw in _stream(b"qpt-cart/linear-trick", seed, (qmap.n_vars + 7) // 8):
        delta = raw & mask
        if not delta:
            continue
        tried += 1
        x = _solve(difference_system(qmap, delta, symmetric))
        if x is not None:
            found = (x, x ^ delta)
            break
        if not tried & 0x3F and time.perf_counter() - began > max_seconds:
            break
    seconds = time.perf_counter() - began
    ok = found is not None and found[0] != found[1] and qmap.evaluate(found[0]) == qmap.evaluate(found[1])
    expansion = qmap.m_eqs - qmap.n_vars
    return AttackResult(
        attack="linear_trick_collision", primitive="keymap/F", size=size, seed=seed, success=ok,
        verified=ok, work=float(tried), work_unit="differences tried (one elimination each)",
        seconds=seconds, detail={"expansion": expansion, "n": qmap.n_vars // 2,
                                 "expected_mean_work_log2": float(expansion)},
        not_run_reason=None if ok else f"budget of {max_seconds}s exhausted after {tried} differences",
    )
