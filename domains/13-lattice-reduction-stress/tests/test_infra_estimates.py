"""The infrastructure estimate script: a floor is not a cost, and a classical number is not quantum.

The estimator's values are pinned elsewhere (``test_cost_estimation_known_values.py``). What is
tested here is what this script is responsible for: that the record's table is carried as the
category floor it decodes to, that each scheme is judged against the floor of its own category, that
a path with no quantum figure is judged on its classical one *and says so*, and that nothing in the
report reads as measured.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from qlwr_lattice_stress.reporting.report_generator import SCOPE_BOUNDARY

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "infra_estimates.py"

try:
    import estimator  # noqa: F401
    HAVE_ESTIMATOR = True
except Exception:  # pragma: no cover - environment dependent
    HAVE_ESTIMATOR = False
needs_estimator = pytest.mark.skipif(not HAVE_ESTIMATOR, reason="lattice-estimator not importable")


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("infra_estimates", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_floors_are_grover_on_aes_at_the_gate_costs_they_decode_to(script):
    """83, 116, 148 = key bits / 2 + log2(gates per AES call): the definition of categories 1, 3, 5."""
    floors = script.RECORD_CATEGORY_FLOOR_LOG2_GATES
    assert floors == {1: 83, 2: 100, 3: 116, 5: 148}
    for category, key_bits, per_call in ((1, 128, 19), (3, 192, 20), (5, 256, 20)):
        assert floors[category] == key_bits // 2 + per_call
        assert str(key_bits) in script.FLOOR_DECODES_AS[category]


def test_every_scheme_is_judged_against_its_own_category(script):
    categories = {name: category for _, name, category, _ in script.SCHEMES}
    assert categories == {"ML-KEM-512": 1, "ML-KEM-768": 3, "ML-KEM-1024": 5,
                          "ML-DSA-44": 2, "ML-DSA-65": 3, "ML-DSA-87": 5}


@needs_estimator
def test_the_lowest_category_clears_its_floor_but_not_the_budget(script):
    """Kyber512's quantum core-SVP sits in the Kyber spec's [107, 108) window: above 83, below 128."""
    row = script.row_for("Kyber512", "ML-KEM-512", 1, "test")
    assert 107 <= row["quantum_log2"] < 108
    assert row["judged_on"] == "quantum core-SVP"
    assert row["clears_record_floor"] is True
    assert row["clears_qpt128_budget"] is False
    assert row["margin_over_floor_bits"] == pytest.approx(row["quantum_log2"] - 83, abs=0.01)
    assert "not measured" in row["provenance"]


@needs_estimator
def test_a_classical_only_path_is_judged_on_the_classical_figure_and_says_so(script):
    row = script.row_for("Dilithium2_MSIS_WkUnf", "ML-DSA-44", 2, "test")
    assert row["quantum_log2"] is None
    assert row["classical_log2"] is not None
    assert "classical only" in row["judged_on"]
    assert row["margin_over_floor_bits"] == pytest.approx(row["classical_log2"] - 100, abs=0.01)


def _row(**overrides):
    base = {"scheme": "X", "estimator_parameter_set": "x", "nist_category": 5, "used_in": "-",
            "beta_usvp": 10, "beta_dual": None, "classical_log2": 140.0, "quantum_log2": None,
            "cost_model": "m", "cheapest_attack": "a", "record_floor_log2_gates": 148,
            "judged_on": "classical only - this estimator path reports no quantum figure",
            "clears_record_floor": False, "margin_over_floor_bits": -8.0,
            "clears_qpt128_budget": True, "provenance": "theoretical", "estimator_revision": "0" * 40}
    return base | overrides


def test_the_report_leads_with_the_boundary_and_never_says_measured_of_a_number(script):
    report = script.render({"rows": [_row()]})
    assert report.index(SCOPE_BOUNDARY) < report.index("|---")
    assert "Everything in this report is theoretical" in report
    assert "category floor, not a lattice cost" in report
    table = [line for line in report.splitlines() if line.startswith("| X |")]
    # a missing quantum figure is a dash, a failed floor is shown as failed, not omitted
    assert table and "| — |" in table[0] and "| False |" in table[0] and "-8.00" in table[0]


def test_the_script_does_not_name_the_research_tree(script):
    text = SCRIPT.read_text()
    assert "Documents/" not in text
