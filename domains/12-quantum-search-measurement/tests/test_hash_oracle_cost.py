"""The hash-oracle cost script: it counts only what it has verified, and it keeps the inference
pointing the right way.

The circuit itself is tested in ``test_sha256_circuit.py``. What this script owns is the *claim*
built on the count: that the circuit was re-verified in the same run that counted it, that a query
is priced as two hashes and a comparison, that counted and published numbers stay in separate
tables, and that the report never lets an upper bound on the cost read as a proof of the record's
lower bound.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import pytest

from grover_emulator.reporting.report_generator import SCOPE_BOUNDARY

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hash_oracle_cost.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("hash_oracle_cost", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def results(script):
    out = script.build_results()
    for section in ("one_hash", "oracle_query_n32_image256", "oracle_query_n24_image192"):
        out[section]["as_built_total"] = out[section]["as_built"]["total"]
    return out


def test_the_circuit_is_verified_in_the_run_that_counts_it(results):
    assert results["verified_digests"] == "64/64"
    assert "verified against hashlib in this run" in results["one_hash"]["provenance"]


def test_a_circuit_that_fails_verification_is_not_counted(script, monkeypatch):
    monkeypatch.setattr(script, "verify", lambda gl, layout, samples=64: 63)
    with pytest.raises(SystemExit, match="63/64"):
        script.build_results()


def test_a_query_is_two_hashes_and_a_comparison(results):
    one, query = results["one_hash"], results["oracle_query_n32_image256"]
    assert query["toffoli_equivalent"] == 2 * one["toffoli_equivalent"] + 255
    assert query["as_built"]["mcx"] == 1
    # the published cost of the 256-controlled NOT replaces the IR's, and only that term moves
    assert query["t_count_with_published_mcx_cost"] == 2 * 7 * 45_392 + (32 * 256 - 84)


def test_the_margins_are_what_the_logs_say(script, results):
    one, query = results["one_hash"], results["oracle_query_n32_image256"]
    assert one["t_count_at_7_per_toffoli"] == 317_744
    assert script.margin(one["log2"]["as_built_total_gates"]) < 0 < script.margin(one["log2"]["t_count"])
    for metric in ("as_built_total_gates", "t_count", "clifford_t_total_gates"):
        assert script.margin(query["log2"][metric]) > 0, "per query, every counted metric clears 2^18"
    published = results["published"]
    assert published["log2_sha256_t_count_optimised"] < 18 < published["log2_sha256_oracle_t_count"]
    assert published["log2_sha256_oracle_t_count"] == pytest.approx(math.log2(466_092))


def test_the_report_keeps_the_inference_pointing_the_right_way(script, results):
    report = script.render(results)
    assert report.index(SCOPE_BOUNDARY) < report.index("|---")
    assert "**upper** bound" in report and "**lower** bound" in report
    assert "cannot prove it" in report
    assert "**Not shown:** that no cheaper circuit exists" in report
    assert "Per single hash evaluation the floor does not hold" in report
    # counted and published figures live under separate, labelled headings
    counted, published = report.index("## Counted — this circuit"), report.index("## Published —")
    assert counted < published
    assert "228,992" not in report[counted:published]
    assert "not derived here" in report[published:]
