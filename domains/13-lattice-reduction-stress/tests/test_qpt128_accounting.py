"""The corpus's QPT-128 ledger arithmetic, and the double charge inside Mode B's margin.

The module under test records two ledgers as constants so their margins can be recomputed rather
than quoted. The tests below hold it to three things, and the second is the one with teeth:

1. **Both ledgers reproduce** from their recorded rows under the corpus's own combination rule.
2. **Mode B reproduces only if proof soundness is charged twice.** The single-charge variant must
   *fail* to match the recorded total — otherwise this suite would pass on a module that had quietly
   corrected the corpus and reported a number the corpus does not contain.
3. **The double charge is conservative**, so recording it does not attenuate a security claim.

Nothing here reads the research tree; the values are constants with citations. The two guards that
enforce that for the package as a whole are in `test_config_schema.py` and `test_end_to_end.py`.
"""

from __future__ import annotations

import pytest

from qlwr_lattice_stress.problem.qpt128_accounting import (
    KAPPA,
    MODE_B_RECORDED_TOTAL,
    MODE_B_ROWS,
    MODE_S_RECORDED_TOTAL,
    MODE_S_ROWS,
    d2_margin,
    margin_reconciliation,
    mode_b_margins,
    union_bound,
)


def test_mode_s_reproduces_from_its_recorded_rows():
    """Mode S's total is a union bound over its five printed rows, to rounding.

    Its rows are recorded to three decimals, so the residual is the rounding of the inputs and
    nothing else. Asserted as a bound rather than equality because the inputs are rounded — an
    equality here would be asserting precision the citation does not carry.
    """
    report = margin_reconciliation()["mode_s"]
    assert report["residual_is_rounding"]
    assert abs(report["residual_bits"]) < 0.01

    # The recorded margin is +29.414 and the recomputation lands within a thousandth of it.
    assert d2_margin(MODE_S_RECORDED_TOTAL) == pytest.approx(29.414, abs=1e-9)
    assert report["recomputed_d2_margin_bits"] == pytest.approx(29.414, abs=0.01)


def test_mode_b_reproduces_only_when_proof_soundness_is_charged_twice():
    """**The test with teeth.** The recorded total must match the two-charge ledger and only it.

    If a future edit "fixed" the double charge in the constants, the recorded figure would stop
    reproducing and this fails — which is correct, because the corpus does contain 7.7 and a module
    that cannot reproduce it has stopped being a record of the corpus and become a correction of it.
    The second assertion is what makes the first non-vacuous: the single-charge variant must *miss*.
    """
    report = margin_reconciliation()["mode_b"]
    variants = report["variants"]

    counted_twice = variants["both_r3_rows_as_computed"]
    counted_once = variants["faest_row_only"]

    assert abs(counted_twice["total_log2"] - MODE_B_RECORDED_TOTAL) < 0.05, (
        "the two-charge ledger no longer reproduces the corpus's recorded total"
    )
    assert counted_twice["d2_margin_bits"] == pytest.approx(7.7, abs=0.05)

    # Non-vacuity: the variant that charges the row once does NOT reproduce it, so the assertion
    # above is testing something.
    assert abs(counted_once["total_log2"] - MODE_B_RECORDED_TOTAL) > 0.3
    assert counted_once["d2_margin_bits"] == pytest.approx(8.081, abs=0.01)


def test_the_two_r3_rows_are_distinct_keys_in_the_same_mapping():
    """The mechanism, asserted directly rather than inferred from the totals.

    The defect is not that a wrong value was used; it is that a replacement was stored under a key
    that did not overwrite what it replaced. Both rows must therefore be present, distinct, and both
    R3 — if they ever collapse to one key the total silently becomes the single-charge figure.
    """
    r3 = [k for k in MODE_B_ROWS if k.startswith("R3")]
    assert len(r3) == 2, f"expected two R3 rows (the alternative models), found {r3}"
    assert len(set(MODE_B_ROWS[k] for k in r3)) == 2, "the two R3 rows carry the same value"
    # The FAEST form is the stronger of the two, which is why it is the one that dominates.
    assert MODE_B_ROWS["R3 proof soundness (FAEST v2 Lemma 9.39, degree 6)"] > MODE_B_ROWS[
        "R3 proof soundness (DFMS-modelled)"
    ]


def test_the_double_charge_is_conservative():
    """It must understate the margin, never inflate it.

    This is the claim that makes the finding safe to record: a defect that shrinks a security margin
    errs against the scheme, so no claim in the corpus is made stronger by it. If the inequality ever
    flips, the finding stops being conservative and becomes the opposite kind of problem.
    """
    report = margin_reconciliation()["mode_b"]
    assert report["error_is_conservative"]
    assert report["double_charge_costs_bits"] > 0

    twice = report["variants"]["both_r3_rows_as_computed"]["d2_margin_bits"]
    once = report["variants"]["faest_row_only"]["d2_margin_bits"]
    assert twice < once


def test_the_margin_gap_between_the_modes_is_the_price_of_the_proof():
    """+29.4 against +7.7 is a row appearing, not an estimate being revised.

    Mode S's ledger has no proof-soundness row and Mode B's has two; that is the whole difference in
    kind. The arithmetic consequence is that Mode B's margin must be smaller, and by a margin-sized
    amount rather than a rounding one.
    """
    mode_s_rows = set(MODE_S_ROWS)
    assert not any("proof" in k.lower() or "soundness" in k.lower() for k in mode_s_rows), (
        "Mode S is a profile with 'only the proof missing'; a proof row in its ledger would mean "
        "the reconciliation in this module is describing a different pair of documents"
    )
    assert any("soundness" in k for k in MODE_B_ROWS)

    gap = d2_margin(MODE_S_RECORDED_TOTAL) - d2_margin(MODE_B_RECORDED_TOTAL)
    assert gap == pytest.approx(21.714, abs=0.01)


def test_a_union_bound_cannot_fall_below_its_largest_row():
    """The rule's one hard property, and the thing that identifies a total as a union bound.

    Both of the corpus's totals sit just above their own largest row, which is what a dominating term
    looks like. A total *below* its largest row would mean the combination is not this one and every
    reconciliation in this module would be describing something else.
    """
    assert union_bound([-10.0]) == pytest.approx(-10.0)
    assert union_bound([-10.0, -10.0]) == pytest.approx(-9.0)   # two equal terms: one bit up
    # A second term within representable range lifts the total, and only slightly when it is far
    # below. Ten bits down is comfortably inside double precision.
    assert union_bound([-10.0, -20.0]) > -10.0
    assert union_bound([-10.0, -20.0]) == pytest.approx(-9.99859, abs=1e-4)

    # **And it saturates.** A row more than ~52 bits below the largest is absorbed entirely by double
    # precision, so the sum *is* the largest term and the total comes back equal to it. This is a
    # property of `math.log2(sum(2**v))` — the same expression the corpus's ledger uses — and not of
    # the rule. Recorded because it means a deeply dominated row contributes nothing to a total in
    # this arithmetic, which is why the two ledgers' totals sit so close to their dominant rows.
    assert union_bound([-10.0, -100.0]) == -10.0

    for rows in (MODE_S_ROWS, MODE_B_ROWS):
        total = union_bound(rows.values())
        assert total >= max(rows.values()), "a union bound came out below its largest term"
        # ...and only just, when one term dominates. That is the shape both ledgers have.
        assert total <= max(rows.values()) + 1.0

    with pytest.raises(ValueError):
        union_bound([])


def test_the_module_records_that_mode_b_is_not_the_deployed_profile():
    """**The scoping test.** Every margin here is Mode B's, and Mode B is research-only.

    Without this, the module is a precise record of a number that a reader will take for a
    deployment figure — which is exactly the over-reading the module exists to prevent. The corpus
    states it flatly (`test.md:241`: *"Never compile it into a node"*), and the deployed profile is
    B0, whose margin comes from a different ledger entirely.
    """
    report = margin_reconciliation()
    assert report["mode_b_status"] == "research only, never deployed"
    assert report["deployed_profile"]["name"] == "B0"
    assert report["deployed_profile"]["margin_bits"] == 23.0
    # The deployed figure is not one of the figures this module computes — that is the point.
    computed = {
        report["mode_b"]["recorded_d2_margin_bits"],
        *[v["d2_margin_bits"] for v in report["mode_b"]["variants"].values()],
    }
    assert 23.0 not in computed


def test_the_conservative_claim_is_scoped_to_enumerated_consumers():
    """The claim is bounded by a consumer list, so the list is part of the record, not commentary.

    "No security claim is inflated by it" is true of the three consumers below and is not claimed
    beyond them. Asserting the enumeration keeps the scoping honest: if a fourth consumer appears,
    this list is stale and the claim has to be re-derived rather than inherited.
    """
    consumers = margin_reconciliation()["mode_b_margin_consumers"]
    assert len(consumers) == 3
    assert any("modeB_security_v1.49.md" in c for c in consumers)
    assert any("attack_lab_results_v1.51.md" in c for c in consumers)
    assert any("ceqs_attack_lab_v1.51.py" in c for c in consumers)
    # No threshold test is among them — the double-charged total carries no pass/fail anywhere.
    assert not any("modeB_rigorous_ledger" in c for c in consumers)


def test_the_double_charge_affects_every_setting_in_the_block_not_just_the_headline():
    """It is one line applied to a loop, so the quoted alternatives carry it too.

    Recorded because the corrected figure is not a single number to replace a single number: the
    whole v1.49 settings table moves, and a reader comparing "7.7 against 11.5 against 3.7" is
    comparing three double-charged values.
    """
    margins = margin_reconciliation()["mode_b_alternative_settings_margins"]
    assert margins == {"(16, 14, 16)": 11.5, "(24, 9, 16)": 3.7, "(32, 7, 32)": 15.0}
    report = margin_reconciliation()
    assert "one line applied to every setting" in report["mode_b_double_charge_is_a_family"]


def test_the_rule_is_correct_and_the_defect_is_the_stale_row():
    """Recorded so the finding is not mistaken for a dispute about how to combine a ledger.

    The corpus's own auditor contract states the rule — probabilities add, exponents do not — and
    `log2(sum(2**v))` is that rule. What is wrong is that a superseded row was left in the mapping,
    not how the mapping is summed. That distinction decides who has to fix it.
    """
    report = margin_reconciliation()
    assert report["rule_contract"] == "Probabilities add; exponents do not."
    assert "probabilities add" in report["rule_contract"].lower()
    assert "sum(2**v" in report["rule"]


def test_the_module_refuses_the_cross_currency_comparison():
    """A lattice number and a gate-unit margin are not convertible, and the module says so.

    The most likely misreading of this work is that 107.46 bits of sieving cost can be set against a
    +7.7-bit gate-unit margin. Nothing in the corpus supplies a conversion, so the module carries the
    refusal next to the numbers rather than leaving it to a reader's judgement.
    """
    note = margin_reconciliation()["note"]
    assert "gate units" in note
    assert "sieving operations" in note
    assert "no conversion" in note
    assert KAPPA == 130


def test_the_recorded_constants_are_the_ones_the_corpus_prints():
    """Pins the transcription itself, so a typo in a constant is caught rather than reconciled.

    The three exact values are checked because the corpus prints them rounded and the rounding is
    documented: -138.1, -159.4, -181.2. If a transcribed value stopped rounding to its printed form,
    the module would be reconciling a ledger the corpus does not contain.
    """
    assert MODE_B_ROWS["R3 proof soundness (FAEST v2 Lemma 9.39, degree 6)"] == pytest.approx(-138.1, abs=0.05)
    assert MODE_B_ROWS["R4 simulation"] == pytest.approx(-159.4, abs=0.05)
    assert MODE_B_ROWS["R5 false positive"] == pytest.approx(-181.2, abs=0.05)
    assert MODE_B_RECORDED_TOTAL == -137.7
    assert MODE_S_RECORDED_TOTAL == -159.414

    # The simulation row is the one row the two ledgers share, to full precision on Mode B's side
    # and to rounding on Mode S's. Its survival is what shows the ledgers describe one construction's
    # lineage rather than two unrelated ones.
    assert MODE_S_ROWS["E2 simulation"] == pytest.approx(MODE_B_ROWS["R4 simulation"], abs=0.01)
