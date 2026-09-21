#!/usr/bin/env python3
"""Measure what this machine can actually do, rather than predicting it.

The plan carries a hardware-feasibility table derived from G6K's source constants --
``db_size(beta) = db_size_factor * db_size_base**beta`` with ``db_size_base = (4/3)**0.5`` and
``db_size_factor = 3.2``, times a per-entry cost estimated at ~850 B. That table is a *prediction*.
This script tests it, because two of its inputs are not readable from the source: the real
per-entry overhead (bucket arrays, sorted-hash tables and the lift list are not in the struct), and
where the machine actually stops coping.

The distinction matters more here than usual. Swap on this host is already ~90% consumed, so an
over-budget run does not raise ``MemoryError`` -- it makes the machine stop responding while the
sieve walks a nearly-full swap file. That is why every step is preceded by a budget check that
*refuses*, and why the refusal is recorded as a result rather than being an absence of one.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# Measurements are flushed to disk after every single row. The first run of this script computed all
# twelve sieving points and then lost them, because the file was only written at the end and the
# sweep was killed during the slower enumeration section. A long unattended measurement whose result
# exists only in a process's memory has no result.
_PROGRESS: dict = {"sieve": [], "bkz": [], "summary": {}}
_OUT_PATH: Path | None = None


def _flush() -> None:
    if _OUT_PATH is None:
        return
    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUT_PATH.write_text(json.dumps(_PROGRESS, indent=2) + "\n")


def mem_available_bytes() -> int:
    """``MemAvailable`` -- the kernel's own estimate, which accounts for reclaimable cache."""
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    raise RuntimeError("MemAvailable not in /proc/meminfo")


def peak_rss_bytes() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


def db_size_entries(block_size: int, base: float, factor: float) -> float:
    """G6K's own database-size model, read from the installed ``SieverParams`` defaults."""
    return factor * base**block_size


def estimate_sieve_bytes(block_size: int, base: float, factor: float, entry_bytes: int = 850) -> int:
    """Predicted peak bytes for a sieving run, with a safety factor for non-entry overhead.

    The safety factor is the part that is a guess, and the whole point of measuring is to replace
    it. It is applied here so the *refusal* is conservative (better to refuse a run that would have
    fitted than to attempt one that thrashes).
    """
    return int(db_size_entries(block_size, base, factor) * entry_bytes * 2.0)


def _run_one_sieve_config(beta: int, threads: int, seed: int, result_queue) -> None:
    """**The child.** One configuration, in a process that has done nothing else.

    This exists because ``ru_maxrss`` is a process-wide high-water mark that never decreases. Running
    every configuration in one process — which is what this script did first — makes the second
    configuration's "delta" the difference between its peak and the *first* configuration's, so
    every configuration except the largest records a delta of zero. The measured/predicted ratio the
    M1 gate depends on was therefore computed from one usable point, and the rest were noise the
    report presented as measurements.

    A fresh process per configuration is the fix, and it has to be a fresh *process* rather than a
    reused worker: a pool recycles its workers and the high-water mark would accumulate across tasks
    exactly as before. The parent forks before importing anything heavy, so every child starts from
    the same small baseline and its peak is its own.
    """
    import cysignals.signals  # noqa: F401  (G6K resolves symbols through the loaded table)
    from fpylll import IntegerMatrix, LLL
    from g6k import Siever
    from g6k.algorithms.bkz import pump_n_jump_bkz_tour as bkz
    from g6k.siever_params import SieverParams
    from g6k.utils.stats import dummy_tracer

    try:
        d = max(beta + 10, 60)
        A = IntegerMatrix(d, d, int_type="mpz")
        A.randomize("qary", k=d // 2, bits=10)
        LLL.reduction(A)

        params = SieverParams()
        params.threads = threads
        t0 = time.perf_counter()
        g6k = Siever(A, params, seed=seed)
        bkz(g6k, dummy_tracer, beta)
        elapsed = time.perf_counter() - t0
        result_queue.put({
            "status": "measured",
            "dimension": d,
            "wall_clock_s": round(elapsed, 3),
            "peak_rss_bytes": peak_rss_bytes(),
        })
    except Exception as exc:  # noqa: BLE001
        result_queue.put({"status": "error", "reason": f"{type(exc).__name__}: {exc}"})


class _Collected:
    """Stands in for the result queue *inside* the child, so the wrapper sees the row first."""

    def __init__(self) -> None:
        self.items: list[dict] = []

    def put(self, item: dict) -> None:
        self.items.append(item)


def _child_with_its_own_baseline(beta: int, threads: int, seed: int, result_queue) -> None:
    """Run one configuration, with the baseline **and** the peak both read inside the child.

    The baseline used to be the *parent's* ``ru_maxrss``, read just before the fork. That is the
    parent's high-water mark, not what the child starts with: a forked child's mark restarts at the
    resident set it was forked with. So a parent that had ever been heavier than it is now — 500 MiB
    touched and released, say, or a test runner with pandas loaded — handed every child a
    subtrahend larger than the child's own peak, the ``max(0, ...)`` clipped the difference, and a
    300 MiB allocation was reported as costing nothing. Reading both ends here makes the figure a
    property of the child alone, whatever the parent's history.

    The workload is looked up at call time and handed a stand-in queue, so it stays what it was — a
    function that measures nothing about baselines — and the arithmetic stays in one place.
    """
    baseline = peak_rss_bytes()
    collected = _Collected()
    _run_one_sieve_config(beta, threads, seed, collected)
    result = collected.items[-1] if collected.items else {
        "status": "error", "reason": "the configuration returned no result",
    }
    result_queue.put(result | {"fork_baseline_bytes": baseline})


def profile_sieve(block_sizes, thread_counts, budget_bytes: int, seed: int = 0) -> list[dict]:
    """Run one sieving tour per (block size, threads), **each in its own process**.

    The fork is not incidental. ``ru_maxrss`` never decreases, so a single-process loop reports a
    per-configuration footprint that is only correct for the largest configuration in the loop; see
    :func:`_run_one_sieve_config`. Each child records its own baseline as well as its own peak — see
    :func:`_child_with_its_own_baseline` for what went wrong when the parent supplied the baseline.
    The parent here still deliberately imports no sieving machinery: a forked child starts with the
    parent's *current* resident set, so the lighter the parent, the smaller the floor under every
    child's figure.
    """
    import multiprocessing

    # G6K's database-size constants are read from a throwaway child, so the parent stays clean.
    base, factor = _db_size_constants()
    import_overhead = _import_overhead_bytes()
    print(f"  per-process import overhead: {import_overhead / 2**20:.0f} MiB "
          f"(subtracted from each configuration's delta)", flush=True)

    ctx = multiprocessing.get_context("fork")
    rows = _PROGRESS["sieve"]

    for beta in block_sizes:
        predicted = estimate_sieve_bytes(beta, base, factor)
        for threads in thread_counts:
            row = {
                "engine": "g6k",
                "block_size": beta,
                "threads": threads,
                "predicted_bytes": predicted,
                "available_bytes": mem_available_bytes(),
            }
            if predicted > budget_bytes:
                row |= {
                    "status": "refused",
                    "reason": (
                        f"predicted {predicted / 2**30:.2f} GiB exceeds the "
                        f"{budget_bytes / 2**30:.2f} GiB budget; refusal is the result, "
                        "not an absence of one"
                    ),
                }
                rows.append(row)
                _flush()
                print(f"  beta={beta:3d} threads={threads}  REFUSED  "
                      f"({predicted / 2**30:.2f} GiB predicted > budget)", flush=True)
                continue

            queue = ctx.SimpleQueue()
            process = ctx.Process(
                target=_child_with_its_own_baseline, args=(beta, threads, seed, queue), daemon=False
            )
            process.start()
            result = queue.get()
            process.join()

            # The child's own mark at the moment it was forked — not the parent's high-water mark,
            # which is what this was and which clipped every delta to zero in a parent with a past.
            baseline = result.pop("fork_baseline_bytes")
            row |= result
            if result["status"] == "measured":
                peak = result["peak_rss_bytes"]
                delta = max(0, peak - baseline)
                # The delta now also contains the cost of importing fpylll and G6K, which is a fixed
                # per-process cost that has nothing to do with the sieve database. At beta = 60 the
                # database is ~16 MiB and the imports are larger than it, so comparing the raw delta
                # against the model would fail the gate for a reason that is not about the model.
                # Measured once, separately, and taken out.
                sieve_only = max(0, delta - import_overhead)
                row |= {
                    "fork_baseline_bytes": baseline,
                    "import_overhead_bytes": import_overhead,
                    "peak_rss_delta_from_before": delta,
                    "peak_rss_bytes_sieve_only": sieve_only,
                }
                print(f"  beta={beta:3d} threads={threads}  {result['wall_clock_s']:7.2f}s  "
                      f"peakRSS={peak / 2**20:.0f} MiB  "
                      f"(sieve-only {sieve_only / 2**20:.0f} MiB, "
                      f"predicted {predicted / 2**20:.0f} MiB)", flush=True)
            else:
                row["peak_rss_delta_from_before"] = None
                row["peak_rss_bytes_sieve_only"] = None
                print(f"  beta={beta:3d} threads={threads}  ERROR  {result['reason']}", flush=True)
            rows.append(row)
            _flush()
    return rows


def _import_overhead_bytes() -> int:
    """Peak RSS a child reaches importing the sieving machinery and doing nothing else.

    Subtracted from each configuration's delta so the figure compared against
    :func:`estimate_sieve_bytes` is the sieve's own footprint. Without this the gate would compare
    a fixed interpreter-and-imports cost against a database size and fail at the small block sizes
    for a reason that says nothing about G6K's model.
    """
    import multiprocessing

    ctx = multiprocessing.get_context("fork")
    queue = ctx.SimpleQueue()

    def measure(queue):
        # Both ends inside the child, for the reason :func:`_child_with_its_own_baseline` gives: the
        # parent's high-water mark is not this process's starting point, and against a parent with a
        # heavier past the difference clipped to zero — an import that "cost nothing".
        baseline = peak_rss_bytes()
        import cysignals.signals  # noqa: F401
        import fpylll  # noqa: F401
        import g6k  # noqa: F401

        queue.put(max(0, peak_rss_bytes() - baseline))

    process = ctx.Process(target=measure, args=(queue,), daemon=False)
    process.start()
    overhead = queue.get()
    process.join()
    return overhead


def _db_size_constants() -> tuple[float, float]:
    """G6K's ``db_size_base`` and ``db_size_factor``, read in a child so the parent stays light."""
    import multiprocessing

    ctx = multiprocessing.get_context("fork")
    queue = ctx.SimpleQueue()

    def read(queue):
        from g6k.siever_params import SieverParams

        sp = SieverParams()
        queue.put((sp.db_size_base, sp.db_size_factor))

    process = ctx.Process(target=read, args=(queue,), daemon=False)
    process.start()
    constants = queue.get()
    process.join()
    return constants


# Enumeration cost grows steeply in both dimension and block size: measured here, d=100 went from
# 0.058 s at beta=20 to 30.9 s at beta=40 -- roughly 500x for twenty block sizes. At d=160, beta=50
# is hours, which is a fact worth recording rather than a set of points worth running. The guard
# below refuses a point whose *measured* cost at the next-lower block size already predicts it will
# exceed the budget, so an unattended profile cannot silently run for a day.
_BKZ_REFERENCE = {(100, 40): 30.9}


def profile_bkz(dimensions, block_sizes, max_loops: int = 2, max_seconds: float = 300.0) -> list[dict]:
    """fpylll BKZ (enumeration) is time-bound, not memory-bound; measure the time."""
    from fpylll import BKZ, IntegerMatrix, LLL

    rows = _PROGRESS["bkz"]
    for d in dimensions:
        previous: dict[int, float] = {}
        for beta in sorted(block_sizes):
            if previous:
                last_beta, last_s = max(previous.items())
                # Growth observed between the two most recent block sizes at this dimension,
                # applied to the step to the next one. A guard, not a model: it exists so an
                # unattended run stops, and its estimate is recorded when it fires.
                if last_s > 0 and last_beta < beta:
                    projected = last_s * (30.0 ** ((beta - last_beta) / 20.0))
                    if projected > max_seconds:
                        rows.append({
                            "engine": "fpylll_bkz", "dimension": d, "block_size": beta,
                            "max_loops": max_loops, "status": "refused",
                            "reason": (
                                f"projected {projected:.0f}s from the measured {last_s:.1f}s at "
                                f"beta={last_beta} exceeds the {max_seconds:.0f}s guard; enumeration "
                                "cost grows steeply in both dimension and block size"
                            ),
                        })
                        _flush()
                        print(f"  fpylll d={d:4d} beta={beta:3d}  REFUSED "
                              f"(projected {projected:.0f}s > {max_seconds:.0f}s guard)", flush=True)
                        continue

            A = IntegerMatrix.random(d, "qary", k=d // 2, bits=10)
            LLL.reduction(A)
            t0 = time.perf_counter()
            BKZ.reduction(A, BKZ.Param(block_size=beta, max_loops=max_loops, flags=BKZ.AUTO_ABORT))
            elapsed = time.perf_counter() - t0
            previous[beta] = elapsed
            rows.append({"engine": "fpylll_bkz", "dimension": d, "block_size": beta,
                         "max_loops": max_loops, "wall_clock_s": round(elapsed, 3),
                         "status": "measured"})
            _flush()
            print(f"  fpylll d={d:4d} beta={beta:3d}  {elapsed:8.3f}s", flush=True)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--block-sizes", default="40,60,80,90")
    ap.add_argument("--threads", default="1,2,4")
    ap.add_argument("--budget-gb", type=float, default=6.0)
    ap.add_argument("--bkz-dimensions", default="100,160")
    ap.add_argument("--bkz-blocks", default="20,30,40")
    ap.add_argument("--bkz-max-seconds", type=float, default=300.0,
                    help="refuse an enumeration point whose projected cost exceeds this")
    ap.add_argument("--skip-sieve", action="store_true")
    ap.add_argument("--skip-bkz", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    global _OUT_PATH
    _OUT_PATH = (
        Path(args.out) if args.out
        else Path(__file__).resolve().parents[1] / "results" / "hardware_profile.json"
    )

    block_sizes = [int(x) for x in args.block_sizes.split(",")]
    threads = [int(x) for x in args.threads.split(",")]
    budget = int(args.budget_gb * 2**30)

    print("=" * 78)
    print(" qlwr-lattice-stress: hardware calibration")
    print("=" * 78)
    print(f" available RAM: {mem_available_bytes() / 2**30:.2f} GiB   budget: {args.budget_gb} GiB")
    print()

    print("-- G6K sieving --")
    sieve_rows = [] if args.skip_sieve else profile_sieve(block_sizes, threads, budget)
    print("\n-- fpylll BKZ (enumeration) --")
    bkz_rows = [] if args.skip_bkz else profile_bkz(
        [int(x) for x in args.bkz_dimensions.split(",")],
        [int(x) for x in args.bkz_blocks.split(",")],
        max_seconds=args.bkz_max_seconds,
    )

    measured = [r for r in sieve_rows if r["status"] == "measured"]
    # The **sieve-only** figure, not the raw delta: the raw one carries a fixed interpreter-and-import
    # cost per process that dominates at small block sizes and says nothing about G6K's model.
    ratios = [
        r["peak_rss_bytes_sieve_only"] / r["predicted_bytes"]
        for r in measured
        if r["predicted_bytes"] > 0 and (r.get("peak_rss_bytes_sieve_only") or 0) > 0
    ]
    summary = {
        "mem_available_bytes": mem_available_bytes(),
        "budget_bytes": budget,
        "largest_completed_block_size": max((r["block_size"] for r in measured), default=None),
        "refused_block_sizes": sorted({r["block_size"] for r in sieve_rows if r["status"] == "refused"}),
        "measured_over_predicted_ratio_max": (max(ratios) if ratios else None),
        "thread_scaling": {
            str(b): {str(r["threads"]): r.get("wall_clock_s") for r in measured if r["block_size"] == b}
            for b in block_sizes
        },
    }

    print("\n-- summary --")
    print(f"  largest completed block size : {summary['largest_completed_block_size']}")
    print(f"  refused block sizes          : {summary['refused_block_sizes'] or 'none'}")
    if summary["measured_over_predicted_ratio_max"] is not None:
        print(f"  measured/predicted RSS ratio : max {summary['measured_over_predicted_ratio_max']:.2f}"
              f"  (the model is validated if this is < 3.0)")

    _PROGRESS["summary"] = summary
    _flush()
    print(f"\n  wrote {_OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
