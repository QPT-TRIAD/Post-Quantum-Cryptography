"""The hardware profiler's per-configuration memory figure, and whether it is per-configuration.

``scripts/profile_hardware.py`` first ran every sieving configuration inside one process.
``ru_maxrss`` is a high-water mark that never decreases, so the second configuration's "delta" was
its peak minus the *first* configuration's, and every configuration but the largest recorded zero.
The script now forks one process per configuration; nothing tested that the fork buys what it is
there to buy. These tests do, with a child that allocates a **known** amount, so the expected figure
is a number rather than a plausibility.

Two decisions that shape the file:

**The body runs in a fresh interpreter, started through a small launcher.** The profiler's
baseline was the *parent's* ``ru_maxrss`` when this file was written (each child reads its own now;
the last test below is what required that). Inside a pytest process that has already imported fpylll,
the estimator and pandas, that mark sits hundreds of MiB above anything a small child reaches, and
every delta clips to zero — which would make an isolation test pass or fail for a reason unrelated
to isolation. A fresh interpreter is not enough on its own, and this was measured rather than
assumed: Linux folds the *spawning* process's high-water mark into the new program at ``exec``, so
``python -c`` started directly from a 400 MiB pytest reports a 412 MiB peak before it has done
anything, and 12 MiB when a small launcher sits in between. Hence the launcher.

**The child is replaced, the measurement is not.** ``_run_one_sieve_config`` is the workload; what
is under test is ``profile_sieve``'s forking and arithmetic, which run unmodified, as do
``_import_overhead_bytes`` and ``_db_size_constants``. Those two read G6K in a child of their own,
and a child that cannot import it never answers its queue — so the module is gated on G6K rather
than left to hang.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from qlwr_lattice_stress.engines.g6k_sieve_engine import G6KSieveEngine

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "profile_hardware.py"
SHIPPED_PROFILE = REPO / "results" / "hardware_profile.json"

MIB = 1 << 20
FIRST_MIB, SECOND_MIB = 300, 20

pytestmark = pytest.mark.skipif(
    not G6KSieveEngine().available(),
    reason="profile_sieve reads G6K's constants in a forked child, which never answers without G6K",
)

#: Run inside ``python -c``. ``argv`` carries the script path and how many MiB the *parent* should
#: touch and release before profiling — zero for a clean history, large to give it a past peak.
_BODY = r"""
import importlib.util, json, os, sys

script, parent_history_mib = sys.argv[1], int(sys.argv[2])
spec = importlib.util.spec_from_file_location("profile_hardware_under_test", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

MIB = 1 << 20
ALLOCATION = {40: %(first)d * MIB, 42: %(second)d * MIB}
out_path_on_import = mod._OUT_PATH

def allocating_child(beta, threads, seed, result_queue):
    # bytes filled with a non-zero value, so every page is written and therefore resident; a
    # zeroed buffer is mapped lazily and would not move the high-water mark at all.
    held = b"\x01" * ALLOCATION[beta]
    result_queue.put({
        "status": "measured", "dimension": 60, "wall_clock_s": 0.0,
        "peak_rss_bytes": mod.peak_rss_bytes(), "child_pid": os.getpid(), "held": len(held),
    })

mod._run_one_sieve_config = allocating_child

if parent_history_mib:
    history = b"\x01" * (parent_history_mib * MIB)
    del history

stdout, sys.stdout = sys.stdout, sys.stderr      # the profiler prints progress; keep stdout for JSON
rows = mod.profile_sieve([40, 42], [1], 64 << 30)
refused = mod.profile_sieve([40], [1], 1)
sys.stdout = stdout
print(json.dumps({
    "parent_pid": os.getpid(),
    "parent_peak_bytes": mod.peak_rss_bytes(),
    "rows": rows[:2],
    "refused": refused[-1],
    "out_path_on_import": out_path_on_import,
    "out_path_after": mod._OUT_PATH,
    "cwd_entries": sorted(os.listdir(".")),
}))
""" % {"first": FIRST_MIB, "second": SECOND_MIB}

#: Does nothing but start the real interpreter, so that what the profiler's parent inherits at
#: ``exec`` is this process's few MiB rather than the test runner's few hundred.
_LAUNCHER = "import subprocess, sys; raise SystemExit(subprocess.run(sys.argv[1:]).returncode)"


def _profile_in_a_fresh_interpreter(workdir: Path, *, parent_history_mib: int) -> dict:
    proc = subprocess.run(
        [sys.executable, "-B", "-c", _LAUNCHER,
         sys.executable, "-B", "-c", _BODY, str(SCRIPT), str(parent_history_mib)],
        capture_output=True, text=True, cwd=workdir, timeout=300,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def clean_parent(tmp_path_factory) -> dict:
    """Two configurations profiled from a parent with no memory history: 300 MiB, then 20 MiB."""
    before = SHIPPED_PROFILE.stat().st_mtime_ns if SHIPPED_PROFILE.exists() else None
    payload = _profile_in_a_fresh_interpreter(
        tmp_path_factory.mktemp("profile-clean"), parent_history_mib=0
    )
    payload["shipped_profile_untouched"] = (
        (SHIPPED_PROFILE.stat().st_mtime_ns if SHIPPED_PROFILE.exists() else None) == before
    )
    return payload


# ---------------------------------------------------------------------------------------------
# isolation: the second configuration's figure is its own
# ---------------------------------------------------------------------------------------------


def test_the_second_configuration_is_not_charged_for_the_first(clean_parent):
    """The defect the fork exists to remove, stated as numbers.

    Configuration one holds 300 MiB and configuration two holds 20 MiB. In one process the second
    could only report ``max(0, 20 - 300) = 0`` or, measured from the start, at least 300. Forked,
    it must report something near 20 — and the order (large first) is the one that contaminates.
    """
    first, second = clean_parent["rows"]
    assert first["status"] == second["status"] == "measured"
    assert first["held"] == FIRST_MIB * MIB and second["held"] == SECOND_MIB * MIB

    first_delta = first["peak_rss_delta_from_before"] / MIB
    second_delta = second["peak_rss_delta_from_before"] / MIB
    assert 0.8 * FIRST_MIB <= first_delta <= FIRST_MIB + 40, first_delta
    assert 5 <= second_delta <= SECOND_MIB + 40, (
        f"the 20 MiB configuration reported a delta of {second_delta:.0f} MiB after a 300 MiB one"
    )
    assert second["peak_rss_bytes"] < first["peak_rss_bytes"] / 2, (
        "the second child's own high-water mark carries the first child's allocation"
    )


def test_each_configuration_ran_in_its_own_process(clean_parent):
    """A *fresh* process each, not a reused worker: a pool would accumulate exactly as before."""
    pids = [row["child_pid"] for row in clean_parent["rows"]]
    assert len(set(pids)) == len(pids) == 2
    assert clean_parent["parent_pid"] not in pids


def test_the_parent_stays_light_so_the_children_start_small(clean_parent):
    """The parent imports no sieving machinery, which is what keeps the inherited baseline small.
    Were the 300 MiB child run in-process, this mark would sit above 300 MiB."""
    assert clean_parent["parent_peak_bytes"] < 100 * MIB
    assert clean_parent["rows"][0]["fork_baseline_bytes"] < 100 * MIB


def test_the_import_overhead_is_measured_and_taken_out(clean_parent):
    """``peak_rss_bytes_sieve_only`` is the delta less a fixed per-process import cost, floored at
    zero. The arithmetic is asserted rather than the magnitude, which belongs to the host."""
    for row in clean_parent["rows"]:
        overhead = row["import_overhead_bytes"]
        assert overhead > 0, "importing fpylll and G6K cost nothing, so nothing was measured"
        assert row["peak_rss_bytes_sieve_only"] == max(
            0, row["peak_rss_delta_from_before"] - overhead
        )


def test_an_over_budget_configuration_is_refused_without_forking(clean_parent):
    """A refusal is a row, and it carries no measurement — the child must never have run."""
    refused = clean_parent["refused"]
    assert refused["status"] == "refused"
    assert "budget" in refused["reason"]
    assert "child_pid" not in refused and "peak_rss_bytes" not in refused


def test_importing_the_script_writes_nothing(clean_parent):
    """``_OUT_PATH`` is ``None`` until ``main`` sets it, so ``_flush`` is a no-op under import and a
    test of the profiler cannot overwrite the calibration the notes cite."""
    assert clean_parent["out_path_on_import"] is None
    assert clean_parent["out_path_after"] is None
    assert clean_parent["cwd_entries"] == []
    assert clean_parent["shipped_profile_untouched"]


# ---------------------------------------------------------------------------------------------
# the baseline the delta is taken from
# ---------------------------------------------------------------------------------------------


def test_a_parent_with_a_memory_history_does_not_clip_the_deltas(tmp_path):
    """The same two configurations, from a parent that touched 500 MiB earlier and released it.

    Nothing about the children changed, so their figures must not either. What changes today is the
    subtrahend: the parent's high-water mark is 500 MiB, the 300 MiB child peaks below it, and the
    profiler reports that a 300 MiB allocation cost nothing.
    """
    payload = _profile_in_a_fresh_interpreter(tmp_path, parent_history_mib=500)
    first, second = payload["rows"]
    assert first["held"] == FIRST_MIB * MIB

    first_delta = first["peak_rss_delta_from_before"] / MIB
    second_delta = second["peak_rss_delta_from_before"] / MIB
    assert 0.8 * FIRST_MIB <= first_delta <= FIRST_MIB + 40, (
        f"a child holding {FIRST_MIB} MiB reported a delta of {first_delta:.0f} MiB against a "
        f"fork baseline of {first['fork_baseline_bytes'] / MIB:.0f} MiB"
    )
    assert 5 <= second_delta <= SECOND_MIB + 40, second_delta
    assert first["import_overhead_bytes"] > 0
