"""The campaign, its report, the exporters and the command line.

What is tested here is the tester's honesty as a system: that a campaign whose controls fail
*refuses to stand behind its subject verdicts*; that the report leads with the scope boundary and
keeps measured, fitted and extrapolated numbers in separate sections; that a polynomial verdict on
the lattice track is explained rather than shouted; that the exported files really are attackable
by an external tool and do not contain the secret; and that the CLI's raw-primitive commands agree
with the library.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from qpt_cart.analysis.workload_curve import Verdict, fit_curve
from qpt_cart.attacks.algebraic import sage_available
from qpt_cart.attacks.base import AttackResult
from qpt_cart.attacks.lattice import lattice_engine_path
from qpt_cart.cli import app
from qpt_cart.harness import (
    CONTROL_EXPONENTIAL,
    CONTROL_POLYNOMIAL,
    SUBJECT,
    Track,
    TrackOutcome,
    _tracks,
    controls_hold,
    run_track,
)
from qpt_cart.primitives.keymap import HandleMode, KeyMapScheme, Opening, ScalingRule, Transcript
from qpt_cart.reporting import findings, render_report
from qpt_cart.scope import SCOPE_BOUNDARY

needs_sage = pytest.mark.skipif(not sage_available(), reason="SageMath not importable")
needs_lattice_engine = pytest.mark.skipif(lattice_engine_path() is None,
                                          reason="lattice-stress engine not found")
runner = CliRunner()
META = {"scale": "test", "expansion": 300, "generated_utc": "2026-09-21T00:00:00+00:00"}


def synthetic(role, key, title, sizes, log2_values, **track_kwargs) -> TrackOutcome:
    track = Track(key, title, role, tuple(sizes), 1, "work", **track_kwargs)
    results = [AttackResult(key, "p", n, 1, True, 2.0 ** v, "units", 0.5) for n, v in zip(sizes, log2_values)]
    fit = fit_curve(sizes, log2_values, expected_exponent=track.expected_exponent,
                    production_size=track.production_size)
    return TrackOutcome(track, results, fit)


SIZES = [8, 10, 12, 14, 16, 18]
GOOD_CONTROLS = [
    synthetic(CONTROL_EXPONENTIAL, "c1", "exp control", SIZES, [n - 1.4 for n in SIZES], expected_exponent=1.0),
    synthetic(CONTROL_POLYNOMIAL, "c2", "poly control", [16, 32, 64, 128, 256],
              [3 * math.log2(n) for n in (16, 32, 64, 128, 256)]),
]


# -- the gate --------------------------------------------------------------------------------------


def test_the_controls_hold_when_each_gets_the_verdict_it_must():
    held, problems = controls_hold(GOOD_CONTROLS)
    assert held and problems == []


def test_a_control_with_the_wrong_verdict_voids_the_campaign():
    blind = synthetic(CONTROL_POLYNOMIAL, "c2", "poly control", SIZES, [n - 1.0 for n in SIZES])
    held, problems = controls_hold([GOOD_CONTROLS[0], blind])
    assert not held and "poly control" in problems[0]
    subject = synthetic(SUBJECT, "s", "a subject", SIZES, [n - 1.0 for n in SIZES], production_size=256)
    report = render_report([GOOD_CONTROLS[0], blind, subject], meta=META)
    assert "The controls did not hold" in report
    assert "verdicts in section 3 are void" in report
    assert "no track qualified" in report, "nothing is extrapolated from a campaign whose gate failed"


def test_a_control_at_the_wrong_rate_or_a_missing_control_also_fails_the_gate():
    slow = synthetic(CONTROL_EXPONENTIAL, "c1", "exp control", SIZES, [0.5 * n for n in SIZES], expected_exponent=1.0)
    assert not controls_hold([slow, GOOD_CONTROLS[1]])[0]
    held, problems = controls_hold([GOOD_CONTROLS[0]])
    assert not held and "must be polynomial" in problems[0]


# -- the report ------------------------------------------------------------------------------------


def test_the_report_leads_with_the_boundary_and_keeps_the_three_kinds_of_number_apart():
    subject = synthetic(SUBJECT, "s", "exhaustive subject", SIZES, [n - 1.0 for n in SIZES],
                        expected_exponent=1.0, production_size=256)
    report = render_report(GOOD_CONTROLS + [subject], meta=META)
    assert report.index(SCOPE_BOUNDARY) < report.index("|---")
    order = [report.index(h) for h in ("## 1. Controls", "## 2. Subjects — measured",
                                       "## 3. Subjects — fitted", "## 4. Extrapolated to production size")]
    assert order == sorted(order)
    measured = report[order[1]:order[2]]
    assert "Verdict" not in measured and "255.0" not in measured
    extrapolated = report[order[3]:]
    assert "| exhaustive subject | 256 | 255.0 |" in extrapolated
    assert "They are not security estimates" in extrapolated and "-38.1" in extrapolated


def test_the_scope_boundary_refuses_the_inference_the_tester_was_asked_to_make():
    """The brief said an exponential curve 'mathematically validates' the 128-bit claim. It does
    not, and the boundary has to say so in words a reader cannot miss."""
    assert "cannot VALIDATE production security" in SCOPE_BOUNDARY
    assert "does not mathematically prove" in SCOPE_BOUNDARY
    assert "FALSIFY" in SCOPE_BOUNDARY and "attacks that were not run" in SCOPE_BOUNDARY
    assert runner.invoke(app, ["scope"]).stdout.strip() == SCOPE_BOUNDARY


def test_a_polynomial_subject_is_a_headline_finding_unless_the_track_explains_it():
    poly = [3 * math.log2(n) for n in (16, 32, 64, 128, 256)]
    unexplained = synthetic(SUBJECT, "s1", "mystery attack", [16, 32, 64, 128, 256], poly)
    explained = synthetic(SUBJECT, "s2", "lattice attack", [16, 32, 64, 128, 256], poly,
                          note="the known LLL regime, not a break.")
    lines = findings(GOOD_CONTROLS + [unexplained, explained])
    assert any("mystery attack: polynomial in range" in l and "shortcut" in l for l in lines)
    assert any("lattice attack: polynomial in range" in l and "LLL regime" in l and "shortcut" not in l
               for l in lines)


def test_a_rate_that_disagrees_with_the_records_formula_is_called_a_disagreement():
    off = synthetic(SUBJECT, "s", "cheap attack", SIZES, [0.5 * n for n in SIZES], expected_exponent=1.0)
    assert any("a disagreement" in l for l in findings(GOOD_CONTROLS + [off]))


# -- real tracks, small ------------------------------------------------------------------------------


def test_the_quick_profile_controls_hold_on_real_runs():
    """The gate, exercised for real: if this fails, no campaign on this machine means anything."""
    quick = {t.key: t for t in _tracks("quick", ScalingRule())}
    outcomes = [run_track(quick["control_random_function"]), run_track(quick["control_linear_map"])]
    held, problems = controls_hold(outcomes)
    assert held, problems
    assert outcomes[0].fit.exponent_bits_per_unit == pytest.approx(1.0, abs=0.1)
    assert outcomes[1].fit.polynomial_degree == pytest.approx(3.0, abs=0.3)


def test_every_track_in_both_profiles_is_runnable_and_has_a_role():
    for scale in ("quick", "full"):
        tracks = _tracks(scale, ScalingRule())
        roles = {t.role for t in tracks}
        assert {CONTROL_EXPONENTIAL, CONTROL_POLYNOMIAL, SUBJECT} <= roles
        for track in tracks:
            assert len(track.sizes) >= 4 and max(track.sizes) / min(track.sizes) >= 1.5
            if track.key in ("keymap_b_brute_force", "keymap_b_groebner"):
                assert all(n % 3 for n in track.sizes), "Mode B needs r -> r^7 to be a permutation"


def test_the_collision_tracks_are_drawn_against_the_parameter_that_drives_them():
    quick = {t.key: t for t in _tracks("quick", ScalingRule())}
    outcome = run_track(Track("keymap_linear_trick", "t", SUBJECT, (4, 5, 7), 4, "work"))
    rule = ScalingRule()
    assert sorted({r.size for r in outcome.results}) == [rule.expansion_at(n) for n in (4, 5, 7)]
    assert quick["keymap_linear_trick"].production_size == 300
    assert quick["keymap_birthday"].production_size == 812


def test_a_timed_track_stops_climbing_once_a_size_exceeds_its_budget(monkeypatch):
    """Larger sizes are recorded as not run — about the budget, never about the primitive — and the
    sizes that did not finish are dropped from the fit instead of being averaged over survivors."""
    import qpt_cart.harness as harness
    calls = []

    def fake(job):
        _, size, seed, budget, _ = job
        calls.append((size, seed))
        over = size >= 12
        return AttackResult("fake", "p", size, seed, not over, None, "seconds", 0.1 * size,
                            not_run_reason=f"budget of {budget}s exhausted" if over else None)

    monkeypatch.setattr(harness, "_run_one", fake)
    outcome = run_track(Track("fake", "t", SUBJECT, (8, 10, 12, 14, 16), 2, "seconds", max_seconds=5.0))
    assert calls == [(8, 1), (8, 2), (10, 1), (10, 2), (12, 1)], "one trip, then no more budgets spent"
    skipped = [r for r in outcome.results if (r.not_run_reason or "").startswith("skipped")]
    assert len(skipped) == 5 and all(r.provenance == "not run" for r in skipped)
    assert outcome.fit.dropped_sizes == [12, 14, 16]
    assert outcome.fit.verdict == Verdict.INSUFFICIENT


def _timed(key, title, rows):
    track = Track(key, title, SUBJECT, tuple(n for n, _ in rows), 1, "seconds")
    results = [AttackResult(key, "p", n, 1, True, None, "seconds", sec) for n, sec in rows]
    return TrackOutcome(track, results, fit_curve([n for n, _ in rows], [math.log2(s) for _, s in rows]))


def _counted(key, title, rows, per_opening):
    track = Track(key, title, SUBJECT, tuple(n for n in rows), 1, "work")
    results = [AttackResult(key, "p", n, 1, True, 2.0 ** (n - 1), "openings tried",
                            per_opening * 2.0 ** (n - 1)) for n in rows]
    return TrackOutcome(track, results, fit_curve(list(rows), [n - 1.0 for n in rows]))


def test_the_algebraic_attack_is_set_beside_exhaustive_search_in_seconds_with_its_provenance():
    """Measured where the search was run, *derived* and labelled so where it was not."""
    brute = _counted("keymap_a_brute_force", "bf A", [8, 10, 12, 14], per_opening=1e-5)
    fast = _timed("keymap_a_groebner", "gb A", [(12, 0.001), (14, 0.002), (16, 0.004), (20, 0.01)])
    report = render_report(GOOD_CONTROLS + [brute, fast], meta=META)
    section = report[report.index("## 2b."):report.index("## 3.")]
    assert "10.0 microseconds per opening" in section
    row12 = next(l for l in section.splitlines() if l.startswith("| 12 |"))
    row20 = next(l for l in section.splitlines() if l.startswith("| 20 |"))
    assert "| measured |" in row12 and "Groebner, by" in row12
    assert "derived (measured rate x 2^(n-1))" in row20
    assert f"{1e-5 * 2 ** 19:.3g}" in row20
    assert "not a proof that no algebraic attack" in section and "None of those was run" in section
    # the comparison is between programs, and the report must not let it read as one between attacks
    assert "two implementations, not two algorithms" in section
    assert "reverses every 'Groebner wins' row" in section
    assert "finished first" in section and "| faster |" not in section


def test_a_groebner_size_that_did_not_finish_is_left_out_of_the_comparison():
    brute = _counted("keymap_b_brute_force", "bf B", [8, 10, 11, 13], per_opening=2e-5)
    slow = _timed("keymap_b_groebner", "gb B", [(8, 0.2), (10, 0.9), (11, 2.0), (13, 14.0)])
    slow.results.append(AttackResult("keymap_b_groebner", "p", 14, 1, False, None, "seconds", 1200.0,
                                     not_run_reason="budget of 1200s exhausted", provenance="not run"))
    section = render_report(GOOD_CONTROLS + [brute, slow], meta=META)
    section = section[section.index("## 2b."):section.index("## 3.")]
    sizes = [l.split("|")[1].strip() for l in section.splitlines() if l.startswith("| ") and l[2].isdigit()]
    assert sizes == ["8", "10", "11", "13"], "the unfinished size 14 has no row"
    assert all("the Python search loop, by" in l for l in section.splitlines() if l.startswith(("| 8 |", "| 13 |")))


def test_a_timed_track_has_one_seconds_column_not_two():
    table = render_report(GOOD_CONTROLS + [_timed("x", "timed thing", [(8, 1.0), (16, 2.0), (24, 4.0), (32, 8.0)])],
                          meta=META)
    header = next(l for l in table[table.index("### timed thing"):].splitlines() if l.startswith("| size"))
    assert header.count("seconds") == 1


def test_a_report_re_rendered_from_stored_results_is_identical(tmp_path):
    subject = synthetic(SUBJECT, "s", "exhaustive subject", SIZES, [n - 1.0 for n in SIZES],
                        expected_exponent=1.0, production_size=256)
    outcomes = GOOD_CONTROLS + [subject]
    stored = tmp_path / "results.json"
    stored.write_text(json.dumps({"meta": META, "tracks": [o.to_dict() for o in outcomes]}, default=str))
    result = runner.invoke(app, ["report", str(stored)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "report.md").read_text() == render_report(outcomes, meta=META)


# -- exporters -------------------------------------------------------------------------------------


@needs_sage
def test_the_exported_system_is_solvable_by_an_external_sage_process_and_holds_no_secret(tmp_path):
    out = tmp_path / "system.py"
    result = runner.invoke(app, ["export-system", str(out), "--n", "8", "--mode", "A", "--seed", "4"])
    assert result.exit_code == 0, result.output
    secret = json.loads(out.with_suffix(".secret.json").read_text())
    text = out.read_text()
    assert str(secret["s"]) not in text.replace("s" + str(secret["s"]), ""), "the answer is kept apart"
    solved = subprocess.run([sys.executable, str(out)], capture_output=True, text=True, timeout=300)
    assert solved.returncode == 0, solved.stderr[-500:]
    # a unique solution gives a basis of linear polynomials s_i or s_i + 1
    basis = solved.stdout
    recovered = sum((1 << i) for i in range(8) if f"s{i} + 1" in basis)
    assert recovered == secret["s"]


@needs_lattice_engine
def test_the_exported_basis_is_in_fplll_format_and_contains_the_planted_vector(tmp_path):
    out = tmp_path / "basis.txt"
    result = runner.invoke(app, ["export-lattice", str(out), "--nu", "8", "--seed", "2"])
    assert result.exit_code == 0, result.output
    info = json.loads(result.stdout)
    text = out.read_text().strip()
    assert text.startswith("[[") and text.endswith("]]")
    from fpylll import LLL, IntegerMatrix
    basis = IntegerMatrix.from_file(str(out))
    assert basis.nrows == basis.ncols == info["dimension"]
    LLL.reduction(basis)
    shortest = sum(int(basis[0, j]) ** 2 for j in range(basis.ncols))
    assert shortest == info["planted_norm_squared"], "LLL finds exactly the planted vector at this size"


# -- the raw primitives on the command line ---------------------------------------------------------


def test_keygen_respond_verify_round_trip_through_the_cli_and_agree_with_the_library():
    made = json.loads(runner.invoke(app, ["keygen", "--n", "10", "--mode", "B", "--seed", "9"]).stdout)
    scheme = KeyMapScheme(10, HandleMode.B)
    opening, public_key = scheme.keygen(9)
    assert (made["secret"]["s"], made["secret"]["r"], made["public_key"]) == (opening.s, opening.r, public_key)

    common = ["--n", "10", "--s", str(opening.s), "--r", str(opening.r), "--challenge", "77"]
    handle = json.loads(runner.invoke(app, ["respond", *common]).stdout)["handle"]
    assert handle == scheme.respond(opening, 77)
    ok = runner.invoke(app, ["verify", *common, "--handle", str(handle), "--public-key", str(public_key)])
    assert ok.exit_code == 0 and json.loads(ok.stdout)["valid"] is True
    bad = runner.invoke(app, ["verify", *common, "--handle", str(handle ^ 1), "--public-key", str(public_key)])
    assert bad.exit_code == 1 and json.loads(bad.stdout)["valid"] is False
    assert scheme.verify(Transcript(public_key, 77, handle), Opening(opening.s, opening.r))


def test_the_cli_refuses_a_mode_b_size_that_breaks_the_handle_and_an_unknown_track():
    assert runner.invoke(app, ["keygen", "--n", "9", "--mode", "B"]).exit_code != 0
    assert runner.invoke(app, ["attack", "no_such_track", "--size", "8"]).exit_code != 0


def test_the_trace_commands_round_trip():
    made = json.loads(runner.invoke(app, ["trace-keygen", "--nu", "5", "--seed", "3"]).stdout)
    secret = ",".join(map(str, made["secret"]))
    assert runner.invoke(app, ["trace-verify", "--nu", "5", "--seed", "3", "--secret", secret]).exit_code == 0
    wrong = ",".join(map(str, [made["secret"][0] ^ 1] + made["secret"][1:]))
    assert runner.invoke(app, ["trace-verify", "--nu", "5", "--seed", "3", "--secret", wrong]).exit_code == 1


def test_a_single_attack_run_through_the_cli_reports_a_verified_win():
    out = json.loads(runner.invoke(app, ["attack", "keymap_a_brute_force", "--size", "8", "--seed", "3"]).stdout)
    assert out["success"] and out["verified"] and out["work_unit"] == "openings tried"
