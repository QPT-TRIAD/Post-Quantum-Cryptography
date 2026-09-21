"""The judge, the campaign and the report — the parts that turn counts into claims."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from qpt_rr.campaign import NOT_RUNNABLE, run_campaign
from qpt_rr.cli import app
from qpt_rr.reporting import controls_hold, headline, render_report
from qpt_rr.runner import FAILS, HOLDS, HOLDS_WITH_LOSS, VACUOUS, Experiment, Result, _judge
from qpt_rr.scope import SCOPE_BOUNDARY

runner = CliRunner()
META = {"n": 8, "trials": 40, "seed": 1, "generated_utc": "2026-09-21T00:00:00+00:00"}


def result(key="x", expect=HOLDS, role="subject", **counts) -> Result:
    base = dict(trials=100, real_wins=100, simulated_wins=100, simulation_failures=0, solved=100,
                invalid_outputs=0, claimed_conversion=1.0)
    out = Result(Experiment(key, "T", "reduction", "adversary", expect, role), **(base | counts))
    _judge(out)
    return out


def test_one_wrong_output_fails_a_reduction_whatever_else_is_true():
    judged = result(invalid_outputs=1, solved=99)
    assert judged.verdict == FAILS and "UNSOUND" in judged.reasons[0]


def test_a_simulation_that_cannot_run_fails_even_though_nothing_wrong_was_output():
    judged = result(simulated_wins=0, simulation_failures=100, solved=0)
    assert judged.verdict == FAILS
    assert any("could not be carried out" in r for r in judged.reasons)
    assert any("distinguishable" in r for r in judged.reasons)


def test_a_gap_between_the_two_win_rates_is_distinguishability():
    assert result(real_wins=60, simulated_wins=20, solved=20).verdict == FAILS
    assert result(real_wins=45, simulated_wins=53, solved=53).verdict == HOLDS, "noise is not a gap"


def test_an_adversary_that_never_wins_exercises_nothing():
    judged = result(real_wins=0, simulated_wins=0, solved=0)
    assert judged.verdict == VACUOUS and judged.conversion is None


def test_a_reduction_that_claims_to_abort_is_judged_on_its_rate_and_never_called_tight():
    guessing = result(simulated_wins=19, simulation_failures=81, solved=19, claimed_conversion=0.2,
                      aborting_is_claimed=True)
    assert guessing.verdict == HOLDS_WITH_LOSS and "loss factor" in guessing.reasons[0]
    short = result(simulated_wins=3, simulation_failures=97, solved=3, claimed_conversion=0.2,
                   aborting_is_claimed=True)
    assert short.verdict == FAILS, "below even the rate it claims"


@pytest.fixture(scope="module")
def campaign():
    return run_campaign(n=8, trials=40, seed=7)


def test_every_experiment_comes_out_as_predicted_before_the_run(campaign):
    assert {r.experiment.key: r.verdict for r in campaign} == {r.experiment.key: r.experiment.expect
                                                               for r in campaign}
    by_key = {r.experiment.key: r for r in campaign}
    assert by_key["t1_prequery"].real_wins == 40 and by_key["t1_prequery"].simulation_failures == 40
    assert by_key["control_broken"].invalid_outputs == 40
    assert all(r.invalid_outputs == 0 for r in campaign if r.experiment.key != "control_broken")


def test_the_runners_controls_gate_the_report(campaign):
    assert controls_hold(campaign) == (True, [])
    blind = [r for r in campaign if r.experiment.key != "control_broken"]
    held, problems = controls_hold(blind)
    assert not held and "was not run" in problems[0]
    assert "nothing below may be relied on" in headline(blind)[0]


def test_the_report_leads_with_the_boundary_names_the_failure_and_lists_what_was_not_run(campaign):
    report = render_report(campaign, meta=META)
    assert report.index(SCOPE_BOUNDARY) < report.index("|---")
    assert "does not survive a legitimate adversary" in report
    assert "'This simulation is perfect' does not hold" in report
    assert "*not in the record*" in report, "the salt is labelled as a candidate, not as the scheme"
    for title, _ in NOT_RUNNABLE:
        assert title in report
    assert "not an attack on the scheme" in report
    # and the disclaimer sits in the headline, above the first table, where a skimmer will meet it
    assert report.index("a hole in a proof, not a break of the scheme") < report.index("|---")
    assert "unproven — not shown false" in report
    assert "Nothing above bears on whether A-F1 or A-F2 is *hard*" in report


def test_the_scope_boundary_separates_the_conversion_from_the_assumption():
    assert "CANNOT do is say anything about the hardness assumption" in SCOPE_BOUNDARY
    assert "has survived those adversaries, not every adversary" in SCOPE_BOUNDARY
    assert runner.invoke(app, ["scope"]).stdout.strip() == SCOPE_BOUNDARY


def test_the_cli_runs_a_campaign_and_lists_the_gaps(tmp_path):
    out = runner.invoke(app, ["run", "--out", str(tmp_path), "--trials", "12", "--n", "8"])
    assert out.exit_code == 0, out.output
    stored = json.loads((tmp_path / "results.json").read_text())
    assert len(stored["results"]) == 9 and stored["scope_boundary"] == SCOPE_BOUNDARY
    assert (tmp_path / "report.md").read_text().startswith("# QPT-128 Mode B-r")
    gaps = runner.invoke(app, ["gaps"]).stdout
    assert "Theorem 3" in gaps and "A-P" in gaps
    assert runner.invoke(app, ["run", "--out", str(tmp_path), "--n", "9"]).exit_code != 0
