"""The corpus's QPT-128 ledger arithmetic, as recorded constants — and one defect in it.

**Why this module is next to the lattice parameters.** The production estimate in
``notes/10-production-estimate.md`` is a number about a lattice. The corpus's QPT-128 margins are
numbers about **quantum gates** — ``log2 Pr/G`` against a ``2^130`` target, with ``2^18`` gates
charged per hash query. The two are not convertible, so neither can be quoted against the other, and
this module exists so that a reader can check that claim rather than take it. It holds no lattice
code and names no path in the research tree.

**The rule, taken from the corpus's own evidence file** (``modeB_rigorous_ledger_v1.47.py``)::

    total = math.log2(sum(2 ** v for v in rows.values()))
    D2_pass = total <= -KAPPA
    D2_margin_bits = -KAPPA - total

A union bound over the rows, with ``KAPPA = 130``. Both ledgers reproduce under it, which is what
:func:`margin_reconciliation` checks rather than assumes.

## The defect this module makes visible

The corpus's v1.49 revision replaced the proof-soundness row's *model* — from a DFMS-modelled row to
one in FAEST v2's Lemma 9.39 form, which is the form the Mode B security document argues from. In
``modeB_rigorous_ledger_v1.47.py`` that replacement is written as::

    led = ledger(tau, b, grinding)                     # computes the DFMS-modelled R3
    led['rows']['R3 proof soundness (FAEST v2 Lemma 9.39 form, degree 6)'] = row
    total = math.log2(sum(2 ** v for v in led['rows'].values()))

The new row is stored under a **different key** from the row it is meant to replace, so the original
DFMS row is still in the mapping when the total is summed. **Proof soundness is charged twice**, and
the margin the corpus quotes — 7.669, printed as 7.7 in ``modeB_security_v1.49.md:135`` and
``attack_lab_results_v1.51.md:176`` — is the margin of that two-charge ledger. Charging the row once,
under the FAEST model the revision actually argues from, gives **8.081**.

**The error is conservative, and that claim is scoped here rather than asserted widely.** The
two-charge sum is ``sum(others) + 2**dfms + 2**faest`` and the single-charge sum is
``sum(others) + 2**faest``; since ``2**dfms > 0`` the two-charge total is *always* larger and its
margin *always* smaller, for any row values at all. So the direction is a property of the rule, not
of these numbers — but it licenses only what has been checked:

* the figure reaches **three consumers** — ``modeB_security_v1.49.md:135`` and
  ``attack_lab_results_v1.51.md:176`` as prose quotes, and ``ceqs_attack_lab_v1.51.py:613`` as a
  hardcoded literal in a report dict. **No threshold, assertion, go/no-go or parameter selection
  reads it**: the ``D2_pass`` test at ``modeB_rigorous_ledger_v1.47.py:173`` is attached to the
  *plain* ledger's total from line 171, and the FAEST block at lines 222-227 emits a total and a
  margin with no test at all;
* Mode B is **absent from ``AUDIT_LEDGER_v2.1.json``** — the corpus's summary ledger has ten rows,
  S1–S6, and no hidden-signer row, so nothing downstream composes it;
* the mutation-then-sum shape occurs **nowhere else** in the corpus, including inside the shipped
  tarball copies.

**And Mode B is not the deployed profile.** ``test.md:241`` — *"Hidden-signer Mode B is research-only:
no production proof backend, no security theorem. Never compile it into a node."* The deployed
profile is **B0**, the public-signer certificate, at **+23.0 bits** (``QPT128_finalization_v1.43.md:28``,
``ledger.rs:41-42`` with ``D2_MARGIN_BITS = 23``). Every figure in this module is a Mode B research
figure, and none of them is a statement about what is deployed. See :data:`MODE_B_STATUS`.

It is recorded because a margin quoted to 0.1 bits should be reproducible from its own rows, and this
one is not until the double charge is named — not because it changes a conclusion. It does not change
one.

Three margins therefore exist for the same setting, and :func:`mode_b_margins` returns all three
rather than choosing:

===========================  =========  ===========
combination                  total      D2 margin
===========================  =========  ===========
both R3 rows (as computed)   -137.669   7.669
FAEST row only (replacement) -138.081   8.081
DFMS row only                -139.642   9.642
===========================  =========  ===========
"""

from __future__ import annotations

import math

__all__ = [
    "KAPPA",
    "DEPLOYED_PROFILE",
    "DEPLOYED_PROFILE_MARGIN_BITS",
    "MODE_B_STATUS",
    "STATUS_CITATION",
    "MODE_B_MARGIN_CONSUMERS",
    "MODE_B_ALTERNATIVE_SETTINGS_MARGINS",
    "COMBINATION_RULE_CONTRACT",
    "LEDGER_RULE",
    "MODE_S_ROWS",
    "MODE_S_RECORDED_TOTAL",
    "MODE_S_CITATION",
    "MODE_B_ROWS",
    "MODE_B_RECORDED_TOTAL",
    "MODE_B_CITATION",
    "d2_margin",
    "union_bound",
    "mode_b_margins",
    "margin_reconciliation",
]

#: The D2 baseline: ``Pr <= G * 2^-KAPPA``. From ``modeB_rigorous_ledger_v1.47.py:52``.
KAPPA = 130

#: **Which profile the corpus actually deploys, and what Mode B is.** Recorded because every margin
#: in this module belongs to Mode B, and Mode B is not deployed — a reader who takes 7.7 (or the
#: corrected 8.081) for a deployment figure has read the wrong line of the corpus's own status
#: tables. The distinction is stated flatly in the corpus: ``test.md:241`` — *"Hidden-signer Mode B
#: is research-only: no production proof backend, no security theorem. Never compile it into a
#: node."* The deployed profile is B0, whose margin is produced by an entirely separate ledger.
DEPLOYED_PROFILE = "B0"
DEPLOYED_PROFILE_DESCRIPTION = "public signer set, 43 category-5 signatures in the clear"
DEPLOYED_PROFILE_MARGIN_BITS = 23.0
MODE_B_STATUS = "research only, never deployed"
STATUS_CITATION = (
    "test.md:25,241 (Mode B research-only); QPT128_finalization_v1.43.md:28 (B0 +23.0); "
    "ledger.rs:12-13,41-42 (SIGNATURE_PROFILE = ML-DSA-87, D2_MARGIN_BITS = 23); "
    "QPT128_LEDGER.md §2"
)

#: Where the quoted figure reaches, established by enumerating the consumers rather than assumed.
#: The scoping matters more than the list: this is what bounds the conservative-direction claim.
MODE_B_MARGIN_CONSUMERS = (
    "modeB_security_v1.49.md:135 (prose quote)",
    "attack_lab_results_v1.51.md:176 (prose quote)",
    "ceqs_attack_lab_v1.51.py:613 (hardcoded literal in a report dict)",
)

#: The settings in the v1.49 FAEST block are **all** double-charged, not just the production row, so
#: the defect is a family rather than a single figure. Values as the corpus quotes them at
#: ``modeB_security_v1.49.md:137``.
MODE_B_ALTERNATIVE_SETTINGS_MARGINS = {
    "(16, 14, 16)": 11.5,
    "(24, 9, 16)": 3.7,
    "(32, 7, 32)": 15.0,
}

#: The corpus's own statement of the combination rule, from the ledger-auditor contract: probabilities
#: add, exponents do not. The defect is therefore **not** in the rule — it is the failure to remove a
#: superseded row before applying a correct rule.
COMBINATION_RULE_CONTRACT = "Probabilities add; exponents do not."

#: How the corpus combines its rows, quoted from the evidence file rather than paraphrased.
LEDGER_RULE = "total = log2(sum(2**v for v in rows.values())); margin = -KAPPA - total"

#: Mode S, the hidden-signer *profile* of ``QPT128_finalization_v1.43.md`` §5 Corollary B, at
#: ``r = 640`` (checker rows, gate units). Values as printed at that file's line 210, to the three
#: decimals the document gives — so :func:`margin_reconciliation` reports a residual against the
#: recorded total, which is rounding and nothing else.
MODE_S_ROWS = {
    "E1 extraction": -169.302,
    "E2 simulation": -159.415,
    "E3 honest preimage": -203.0,
    "E4 key collision (1024-bit)": -500.793,
    "E5 link coincidence": -198.023,
}

MODE_S_RECORDED_TOTAL = -159.414
MODE_S_CITATION = "QPT128_finalization_v1.43.md:205-210 (§5 Corollary B, gate units, r = 640)"

#: Mode B at the production setting — 2^20 leaves, ``tau = 11``, ``w_g = 16`` — with **both** R3 rows
#: kept separate, because the defect above is precisely that they are not alternatives in the code
#: that sums them. Three rows are exact rationals evaluated by the evidence file and quoted to one
#: decimal in the corpus; the values here are the exact ones, obtained by executing
#: ``modeB_rigorous_ledger_v1.47.py`` at this setting, and the recorded one-decimal forms are given
#: beside them so the correspondence is checkable.
MODE_B_ROWS = {
    "R1 framing": -145.0,               # recorded -145.0
    "R2 binding": -209.0,               # recorded -209.0
    "R3 proof soundness (DFMS-modelled)": -139.678072,
    "R3 proof soundness (FAEST v2 Lemma 9.39, degree 6)": -138.093109,   # recorded -138.1
    "R4 simulation": -159.41503749927887,
    "R5 false positive": -181.18141782251917,                            # recorded -181.2
}

MODE_B_RECORDED_TOTAL = -137.7
MODE_B_CITATION = (
    "modeB_rigorous_ledger_v1.47.py (values executed at tau=11, b=20, w_g=16); quoted at "
    "modeB_security_v1.49.md:135 and attack_lab_results_v1.51.md:176"
)

#: The two keys that are alternatives to each other and are summed as though they were not.
_MODE_B_R3_KEYS = (
    "R3 proof soundness (DFMS-modelled)",
    "R3 proof soundness (FAEST v2 Lemma 9.39, degree 6)",
)


def d2_margin(total_log2: float) -> float:
    """The D2 margin in bits: how far ``log2 Pr/G`` sits below the ``-KAPPA`` target."""
    return -KAPPA - total_log2


def union_bound(rows) -> float:
    """``log2`` of the summed probabilities — the corpus's combination rule, as a function.

    ``rows`` is any iterable of ``log2`` values. A union bound cannot come out below its largest
    term, and the difference between the two is what the corpus's totals are made of; a total below
    its own largest row would mean the rule is not this one.
    """
    values = list(rows)
    if not values:
        raise ValueError("a union bound needs at least one row")
    if any(v > 0 for v in values):
        raise ValueError("rows are log2 probabilities and cannot exceed 0")
    return math.log2(sum(2.0 ** v for v in values))


def mode_b_margins() -> dict:
    """The three margins Mode B admits, each labelled, rather than one chosen silently.

    Returning all three is the point. The corpus quotes only the first, which is the one the code
    computes and which charges proof soundness twice; the second is the same ledger with that row
    charged once, which is what the v1.49 revision says it is doing.
    """
    others = {k: v for k, v in MODE_B_ROWS.items() if k not in _MODE_B_R3_KEYS}
    dfms = MODE_B_ROWS[_MODE_B_R3_KEYS[0]]
    faest = MODE_B_ROWS[_MODE_B_R3_KEYS[1]]

    def entry(label: str, values: list[float], note: str) -> dict:
        total = union_bound(values)
        return {
            "combination": label,
            "rows_counted": len(values),
            "total_log2": round(total, 3),
            "d2_margin_bits": round(d2_margin(total), 3),
            "note": note,
        }

    return {
        "both_r3_rows_as_computed": entry(
            "both R3 rows",
            list(others.values()) + [dfms, faest],
            "what modeB_rigorous_ledger_v1.47.py sums, because the FAEST row is stored under a "
            "key distinct from the DFMS row it replaces. This is the figure the corpus quotes.",
        ),
        "faest_row_only": entry(
            "FAEST row only",
            list(others.values()) + [faest],
            "the v1.49 revision read as a replacement, which is what its name says it is. This is "
            "the margin the arithmetic supports.",
        ),
        "dfms_row_only": entry(
            "DFMS row only",
            list(others.values()) + [dfms],
            "the pre-v1.49 model, kept for reference; the corpus argues from the FAEST form.",
        ),
    }


def margin_reconciliation() -> dict:
    """Both ledgers recomputed from their recorded rows, with the residual against each total.

    The residual is the check. A union bound over the printed rows must reproduce the printed total;
    if it does not, either the rule is not a union bound or a row is missing from the transcription.
    Mode S's residual is pure rounding (its rows are recorded to three decimals). Mode B's is the
    double charge, and it is reported rather than absorbed.
    """
    mode_s_total = union_bound(MODE_S_ROWS.values())
    mode_b = mode_b_margins()
    recorded_b = MODE_B_RECORDED_TOTAL

    return {
        "rule": LEDGER_RULE,
        "rule_contract": COMBINATION_RULE_CONTRACT,
        "kappa": KAPPA,
        # Stated before the numbers, because the numbers are Mode B's and Mode B is not deployed.
        "deployed_profile": {
            "name": DEPLOYED_PROFILE,
            "description": DEPLOYED_PROFILE_DESCRIPTION,
            "margin_bits": DEPLOYED_PROFILE_MARGIN_BITS,
            "citation": STATUS_CITATION,
        },
        "mode_b_status": MODE_B_STATUS,
        "mode_b_margin_consumers": list(MODE_B_MARGIN_CONSUMERS),
        "mode_s": {
            "citation": MODE_S_CITATION,
            "rows": dict(MODE_S_ROWS),
            "recomputed_total_log2": round(mode_s_total, 3),
            "recorded_total_log2": MODE_S_RECORDED_TOTAL,
            "residual_bits": round(mode_s_total - MODE_S_RECORDED_TOTAL, 4),
            "recomputed_d2_margin_bits": round(d2_margin(mode_s_total), 3),
            "residual_is_rounding": abs(mode_s_total - MODE_S_RECORDED_TOTAL) < 0.01,
        },
        "mode_b": {
            "citation": MODE_B_CITATION,
            "rows": dict(MODE_B_ROWS),
            "recorded_total_log2": recorded_b,
            "recorded_d2_margin_bits": round(d2_margin(recorded_b), 3),
            "variants": mode_b,
            "reproducing_variant": "both_r3_rows_as_computed",
            "residual_bits": round(
                mode_b["both_r3_rows_as_computed"]["total_log2"] - recorded_b, 4
            ),
            "double_charge_costs_bits": round(
                mode_b["faest_row_only"]["d2_margin_bits"]
                - mode_b["both_r3_rows_as_computed"]["d2_margin_bits"],
                3,
            ),
            "error_is_conservative": (
                mode_b["both_r3_rows_as_computed"]["d2_margin_bits"]
                < mode_b["faest_row_only"]["d2_margin_bits"]
            ),
        },
        "mode_b_alternative_settings_margins": dict(MODE_B_ALTERNATIVE_SETTINGS_MARGINS),
        "mode_b_double_charge_is_a_family": (
            "Every setting in the v1.49 FAEST block is double-charged, not only the production row: "
            "the block builds each ledger with ledger() and then adds the FAEST row under a second "
            "key. The defect is one line applied to every setting, so correcting it moves all of "
            "them, and the quoted alternatives at modeB_security_v1.49.md:137 carry it too."
        ),
        "note": (
            "Recorded constants, recomputed here rather than quoted. **These are Mode B figures and "
            "Mode B is not deployed** — the deployed profile is B0 at +23.0 bits. The two ledgers "
            "here are also in a different currency from the lattice estimate in "
            "notes/10-production-estimate.md: these are log2 Pr/G in gate units, that is sieving "
            "operations, and no conversion between them exists in the corpus, so none of these "
            "margins can be set against a lattice figure and vice versa."
        ),
    }
