"""Lattice reduction against the QLWR trace, through the verified lattice-stress engine.

The embedding that turns "find the secret" into a shortest-vector problem is easy to get subtly
wrong — the normal form, the embedding factor, the ``p*M`` artifact when ``p`` divides ``q`` — and a
wrong embedding fails *silently*: BKZ reduces the wrong lattice without complaint. The sibling
project ``qlwr-lattice-stress`` spent its whole test suite getting those right, so this attack
drives that engine (fpylll BKZ 2.0, one thread) rather than re-deriving it. Its location comes from
``QPT_CART_LATTICE_ENGINE`` or the default beside this project; without it the attack is recorded
as not run, never faked.

**What this track shows, and a prediction of mine it overturned.** Lattice hardness is not in the
dimension but in the BKZ *block size* the attack needs: while LLL (block size 2) still finds the
planted vector the work is polynomial, and the exponential cost — ``2^(0.292 * beta)`` — only
begins once the needed block size starts to climb. This docstring originally asserted that the
climb lay "far beyond" anything a desktop could reach, so the track would read polynomial. Measured
at the production ratios (``q = 2^16``, ``p = 2^8``, 2.375 rows per secret coordinate) it does not:
LLL suffices up to about ``nu = 24``, and from ``nu = 28`` the minimum block size rises — 20, then
30, then 40 and beyond, with some seeds at ``nu >= 40`` not recovered at any block size up to 40.
So the regime change happens *inside* the measurable range, the reported quantity that matters is
the **minimum block size per size** (kept in every result's ``detail``), and the wall-clock curve —
which is the cost of the whole upward sweep, failures included — bends upward with it. The
production-scale question still belongs to the lattice estimator, which the sibling project runs.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from ..primitives.qlwr_trace import QlwrTrace
from .base import AttackResult

__all__ = ["lattice_engine_path", "lattice_primal"]

#: Where the reduction engine is looked for, in order: an explicit override, then the sibling
#: package beside this one. The directory name differs between the two layouts this package is used
#: in — a numbered domain inside the research repository, or a standalone checkout — so both names
#: are tried rather than one being assumed.
SIBLING_NAMES = ("13-lattice-reduction-stress", "qlwr-lattice-stress")
BLOCK_SIZES = (2, 10, 20, 30, 40)


def candidate_engine_paths() -> list[Path]:
    override = os.environ.get("QPT_CART_LATTICE_ENGINE")
    if override:
        return [Path(override)]
    beside = Path(__file__).resolve().parents[4]
    return [beside / name / "src" for name in SIBLING_NAMES]


def lattice_engine_path() -> Path | None:
    for path in candidate_engine_paths():
        if (path / "qlwr_lattice_stress").is_dir():
            return path
    return None


def lattice_primal(trace: QlwrTrace, *, seed: int = 0, max_seconds: float = 600.0,
                   block_sizes=BLOCK_SIZES) -> AttackResult:
    def not_run(reason: str) -> AttackResult:
        return AttackResult(attack="lattice_primal_bkz", primitive="qlwr_trace", size=trace.nu,
                            seed=seed, success=False, work=None, work_unit="seconds", seconds=0.0,
                            not_run_reason=reason, provenance="not run")

    engine_path = lattice_engine_path()
    if engine_path is None:
        looked_in = ", ".join(str(p) for p in candidate_engine_paths())
        return not_run(f"lattice-stress engine not found (looked in {looked_in}; set "
                       "QPT_CART_LATTICE_ENGINE to point at it)")
    if str(engine_path) not in sys.path:
        sys.path.insert(0, str(engine_path))
    try:
        from qlwr_lattice_stress.attacks.primal_attack import find_minimum_successful_block_size
        from qlwr_lattice_stress.engines import build_engine
        from qlwr_lattice_stress.problem.qlwr_instance import LatticeQLWRInstance
    except Exception as error:
        return not_run(f"lattice-stress engine not importable: {type(error).__name__}: {error}")

    secret = trace.keygen()
    try:
        instance = LatticeQLWRInstance(nu=trace.nu, q_l=trace.q, p=trace.p, m=trace.m,
                                       secret_s=secret, base=trace.matrix, seed=seed)
    except ValueError as error:
        return not_run(f"the engine refused this instance: {error}")
    if tuple(instance.target) != trace.trace(secret):
        return not_run("the engine's rounding disagrees with this primitive's; refusing to attack a "
                       "different relation than the one exposed")

    began = time.perf_counter()
    minimum, points = find_minimum_successful_block_size(
        instance, build_engine("fpylll_bkz", threads=1), list(block_sizes),
        max_seconds_per_block_size=max_seconds)
    seconds = time.perf_counter() - began
    ok = minimum is not None
    return AttackResult(
        attack="lattice_primal_bkz", primitive="qlwr_trace", size=trace.nu, seed=seed, success=ok,
        verified=ok, work=None, work_unit="seconds (fpylll BKZ, 1 thread)", seconds=seconds,
        detail={"minimum_block_size": minimum, "rows": trace.m,
                "lattice_dimension": points[0].dimension if points else None,
                "block_sizes_tried": [p.block_size for p in points],
                "recovered_at": [p.block_size for p in points if p.recovered]},
        not_run_reason=None if ok else "no block size in the range recovered the secret",
    )
