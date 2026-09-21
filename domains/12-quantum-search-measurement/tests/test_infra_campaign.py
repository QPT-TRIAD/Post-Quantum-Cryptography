"""The infrastructure campaign script: what it measures, and what it must never imply.

The campaign's numbers are the project's ordinary success curves and probes, tested elsewhere. What
is tested here is the script's own responsibility: that the laws it reports are read off measured
peaks, that a fit is labelled a fit, that a probe which refused to run is never rendered as a probe
that ran and stayed silent, and that the one term of the record's formula the emulator cannot reach
is said to be outside this campaign, with where it *is* counted, rather than quietly dropped.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from grover_emulator.backends.qiskit_aer_backend import QiskitAerBackend
from grover_emulator.reporting.report_generator import SCOPE_BOUNDARY

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "infra_campaign.py"


@pytest.fixture(scope="module")
def campaign():
    spec = importlib.util.spec_from_file_location("infra_campaign", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def results(campaign):
    """One small real run, shared: widths 4-8 and M up to 8 keep it to a few seconds."""
    backend = QiskitAerBackend()
    saved = campaign.WIDTHS, campaign.MULTI_TARGET_WIDTH, campaign.MULTI_TARGET_COUNTS
    campaign.WIDTHS, campaign.MULTI_TARGET_WIDTH, campaign.MULTI_TARGET_COUNTS = (4, 6, 8), 8, (1, 2, 4, 8)
    try:
        return {
            "iteration_law": campaign.iteration_law(backend),
            "multi_target_law": campaign.multi_target_law(backend),
            "structure": campaign.structure(backend, width=6),
        }
    finally:
        campaign.WIDTHS, campaign.MULTI_TARGET_WIDTH, campaign.MULTI_TARGET_COUNTS = saved


def test_every_measured_peak_is_the_textbook_count_or_the_one_before(results):
    """``floor(pi/4 sqrt(N/M))`` can overshoot the true peak by one; it never undershoots."""
    for law in ("iteration_law", "multi_target_law"):
        for row in results[law]["rows"]:
            assert row["provenance"] == "measured"
            assert row["measured_peak_iteration"] in (
                row["textbook_iterations"], row["textbook_iterations"] - 1)
            assert row["max_abs_residual"] < 1e-9


def test_the_multi_target_peak_falls_as_the_marked_count_rises(results):
    peaks = [row["measured_peak_iteration"] for row in results["multi_target_law"]["rows"]]
    assert peaks == sorted(peaks, reverse=True)
    assert peaks[0] > peaks[-1]


def test_the_fitted_exponents_have_the_sign_and_size_the_record_assumes(results):
    assert results["iteration_law"]["fitted_exponent"] == pytest.approx(0.5, abs=0.15)
    assert results["multi_target_law"]["fitted_exponent"] == pytest.approx(-0.5, abs=0.15)
    for law in ("iteration_law", "multi_target_law"):
        assert "not a measurement" in results[law]["provenance_of_fit"]


def test_the_controls_discriminate_beside_the_subject(results):
    fired = {name: [p["fired"] for p in probes if p["status"] == "measured"]
             for name, probes in results["structure"].items()}
    positive = next(v for k, v in fired.items() if k.startswith("hidden_period"))
    negative = next(v for k, v in fired.items() if k.startswith("random_control"))
    assert positive and all(positive)
    assert negative and not any(negative)


def test_a_refused_probe_is_never_rendered_as_a_silent_one(campaign, results):
    """The record of a refusal carries ``fired: False`` — the same value as a genuine silence."""
    refused = [(name, p) for name, probes in results["structure"].items()
               for p in probes if p["status"] != "measured"]
    assert refused, "the LM-OTS lowering keeps a work qubit, so the Simon-style probe refuses it"
    report = campaign.render(results)
    for name, probe in refused:
        row = next(line for line in report.splitlines()
                   if line.startswith(f"| {name} | {probe['probe']} |"))
        assert "no measurement" in row
        assert "| False |" not in row
        assert f"{name} / {probe['probe']} did not run" in report


def test_the_report_states_the_boundary_first_and_what_it_did_not_measure(campaign, results):
    report = campaign.render(results)
    assert report.index(SCOPE_BOUNDARY) < report.index("|---")
    assert "## D. Not measured in this campaign: the 2^18 gates-per-query floor" in report
    assert "Nothing in A–C bears on that term" in report
    assert "scripts/hash_oracle_cost.py" in report, "the term is counted elsewhere, and D says where"
    # a truth-table gate count must not appear dressed as a hash-circuit cost
    assert "gate_count" not in report
    for line in report.splitlines():
        if "Fitted exponent" in line:
            assert "fit, not measurement" in line
