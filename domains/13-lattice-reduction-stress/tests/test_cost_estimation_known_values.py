"""The cost model's numbers, pinned — on a published parameter set and on the recorded production one.

The plan's acceptance line for this module is that it *"reproduces sane, sanity-checked numbers
against a known public parameter set before being trusted on QPT-128's own parameters"*. The
existing tests pin one of those numbers (Kyber512's primal block size) and none of the others: the
dual model's output is asserted nowhere, no cost in bits is asserted anywhere, and the production
estimate — the number the README quotes — has no numeric test at all.

**Which number is which, because two different ones are in circulation for Kyber512.** The
estimator's own documentation prints ``usvp rop ≈2^143.8, β 406`` and ``dual rop ≈2^149.9, β 424``.
Those costs are under the estimator's *default* reduction cost model. :func:`estimate` deliberately
uses ``ADPS16`` — core-SVP — so its costs are ``0.292 * β`` classically and ``0.265 * β`` quantumly:
118.55 and 107.59 bits for the same β = 406, which are the core-SVP figures the Kyber round-3
specification publishes for Kyber512 (118 and 107). The block sizes are common to both and are the
bridge between them. So the pins below are anchored three ways: to this module's measured output, to
the estimator documentation's block sizes and default-model costs, and to the published core-SVP
figures — which is what stops the pin from being merely the code agreeing with itself.

Tolerances are ±1 block size and ±0.5 bit throughout: tight enough that a changed cost model, a
swapped family or a dropped ``mode`` argument fails, loose enough that a rounding change does not.

Three tests here were marked ``xfail(strict=True)`` because the source was wrong, not the test — the
SIS cost read as an attribute off a dict-like ``Cost``, and the production estimate labelled
same-scale. Both were fixed on 2026-09-20 and the markers removed; the tests are unchanged.
"""

from __future__ import annotations

import builtins
import json
import math
import random

import pytest
from typer.testing import CliRunner

from qlwr_lattice_stress.analysis import cost_estimation
from qlwr_lattice_stress.analysis.cost_estimation import (
    PUBLISHED_SIS_SCHEMES,
    EstimatorUnavailable,
    estimate,
    estimator_revision,
    parameter_set_from_instance,
    production_parameter_set,
    reference_parameter_set,
)
from qlwr_lattice_stress.cli import app
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)
from qlwr_lattice_stress.protocols import EXTRAPOLATED, PROVENANCE_LABELS, SAME_SCALE

try:
    import estimator as _estimator_package  # noqa: F401

    ESTIMATOR_MISSING = False
except ImportError:  # pragma: no cover - environment dependent
    ESTIMATOR_MISSING = True

requires_estimator = pytest.mark.skipif(
    ESTIMATOR_MISSING, reason="lattice-estimator is not importable"
)

BETA_TOLERANCE = 1
BITS_TOLERANCE = 0.5

#: The core-SVP constants ``ADPS16`` applies: classical and quantum sieving.
CORE_SVP_CLASSICAL = 0.292
CORE_SVP_QUANTUM = 0.265


def assert_beta(actual, expected: int) -> None:
    assert actual is not None, "the model returned no block size"
    assert isinstance(actual, int), f"block size is {type(actual).__name__}, not a Python int"
    assert abs(actual - expected) <= BETA_TOLERANCE, f"block size {actual}, pinned at {expected}"


def assert_bits(actual, expected: float) -> None:
    assert actual is not None, "the model returned no cost"
    assert actual == pytest.approx(expected, abs=BITS_TOLERANCE)


# ---------------------------------------------------------------------------------------------
# estimates, computed once — the estimator is the slow part of this file
# ---------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def kyber512():
    return estimate(reference_parameter_set("Kyber512"))


@pytest.fixture(scope="module")
def kyber512_classical_only():
    return estimate(reference_parameter_set("Kyber512"), quantum_sieving_speedup=False)


@pytest.fixture(scope="module")
def production_rows():
    return estimate(production_parameter_set(samples="rows"))


@pytest.fixture(scope="module")
def production_exposure():
    return estimate(production_parameter_set(samples="exposure"))


# ---------------------------------------------------------------------------------------------
# Kyber512 — the known public parameter set
# ---------------------------------------------------------------------------------------------


@requires_estimator
@pytest.mark.slow
def test_kyber512_primal_is_pinned_in_block_size_and_in_bits(kyber512):
    assert_beta(kyber512.beta_usvp, 406)
    assert_bits(kyber512.rop_usvp_log2, 118.55)
    assert kyber512.minimum_over_models == "primal_usvp"
    assert_bits(kyber512.rop_classical_log2_min, 118.55)
    assert kyber512.model_parameters["inapplicable_models"] == []


@requires_estimator
@pytest.mark.slow
def test_kyber512_dual_is_pinned_in_block_size_and_in_bits(kyber512):
    """The dual model's output, which no other test reads. The estimator's documentation gives
    β = 424 for it; under core-SVP that is ``0.292 * 424 = 123.81`` bits."""
    assert_beta(kyber512.beta_dual, 424)
    assert_bits(kyber512.rop_dual_log2, 123.81)
    # The dual is the dearer of the two here, so it must not be what the minimum reports.
    assert kyber512.rop_dual_log2 > kyber512.rop_usvp_log2
    assert kyber512.rop_classical_log2_min == kyber512.rop_usvp_log2


@requires_estimator
@pytest.mark.slow
def test_kyber512_lands_in_the_published_core_svp_window(kyber512):
    """Not self-referential: the Kyber round-3 specification publishes core-SVP hardness of 118
    bits classical and 107 quantum for Kyber512, at primal block size 406. Those are truncations of
    ``0.292 * 406`` and ``0.265 * 406``, so the report must land in ``[118, 119)`` and
    ``[107, 108)`` — a window of one bit that nothing in this repository chose."""
    assert kyber512.beta_usvp == 406
    assert 118.0 <= kyber512.rop_classical_log2_min < 119.0
    assert 107.0 <= kyber512.rop_quantum_log2_min < 108.0


@requires_estimator
@pytest.mark.slow
def test_kyber512_agrees_with_the_figures_the_estimator_documents(kyber512):
    """The estimator's README and ``LWE.estimate`` docstring print, for Kyber512,
    ``usvp rop ≈2^143.8, β 406, d 998`` and ``dual rop ≈2^149.9, β 424`` under its default cost
    model. Reproduced here directly from the library, then tied to this module's report through the
    block size — the quantity the two cost models share. If the checkout drifts from its own
    documentation this fails before anything is concluded from the numbers above."""
    import estimator

    usvp = estimator.LWE.primal_usvp(estimator.schemes.Kyber512)
    dual = estimator.LWE.dual(estimator.schemes.Kyber512)

    assert math.log2(float(usvp["rop"])) == pytest.approx(143.8, abs=BITS_TOLERANCE)
    assert math.log2(float(dual["rop"])) == pytest.approx(149.9, abs=BITS_TOLERANCE)
    assert int(usvp["d"]) == 998
    assert abs(int(usvp["beta"]) - 406) <= BETA_TOLERANCE
    assert abs(int(dual["beta"]) - 424) <= BETA_TOLERANCE

    assert kyber512.beta_usvp == int(usvp["beta"])
    assert kyber512.beta_dual == int(dual["beta"])
    # And the report's costs are the core-SVP ones, not the default model's: some 25 bits lower.
    assert kyber512.rop_usvp_log2 < math.log2(float(usvp["rop"])) - 20


@requires_estimator
@pytest.mark.slow
def test_the_reported_costs_are_core_svp_in_both_modes(kyber512):
    """``rop = c * β`` with ``c = 0.292`` classically and ``0.265`` quantumly, per family. This is
    where the report exposes core-SVP, so the classical/quantum gap is checked as the ratio of the
    constants rather than merely as "lower"."""
    classical = kyber512.model_parameters["classical"]
    quantum = kyber512.model_parameters["quantum"]
    assert set(classical) == set(quantum) == {"primal_usvp", "dual"}

    for model in ("primal_usvp", "dual"):
        beta = classical[model]["beta"]
        assert quantum[model]["beta"] == beta, "the mode changes the cost, not the block size"
        assert classical[model]["rop_log2"] == pytest.approx(CORE_SVP_CLASSICAL * beta, abs=0.01)
        assert quantum[model]["rop_log2"] == pytest.approx(CORE_SVP_QUANTUM * beta, abs=0.01)
        assert quantum[model]["rop_log2"] < classical[model]["rop_log2"]
        assert quantum[model]["rop_log2"] / classical[model]["rop_log2"] == pytest.approx(
            CORE_SVP_QUANTUM / CORE_SVP_CLASSICAL, abs=1e-3
        )

    assert_bits(kyber512.rop_quantum_log2_min, 107.59)
    assert kyber512.rop_quantum_log2_min < kyber512.rop_classical_log2_min


@requires_estimator
@pytest.mark.slow
def test_without_the_quantum_speedup_no_quantum_figure_is_reported(kyber512, kyber512_classical_only):
    """Off means absent — not a copy of the classical figure, and not zero. The classical half must
    be untouched by the switch."""
    report = kyber512_classical_only
    assert report.rop_quantum_log2_min is None
    assert report.model_parameters["quantum"] == {}

    assert report.beta_usvp == kyber512.beta_usvp
    assert report.beta_dual == kyber512.beta_dual
    assert report.rop_usvp_log2 == kyber512.rop_usvp_log2
    assert report.rop_dual_log2 == kyber512.rop_dual_log2
    assert report.rop_classical_log2_min == kyber512.rop_classical_log2_min
    # With it on, the quantum figure exists and is strictly lower.
    assert kyber512.rop_quantum_log2_min is not None
    assert kyber512.rop_quantum_log2_min < report.rop_classical_log2_min


@requires_estimator
@pytest.mark.slow
def test_the_dual_model_alone_reports_only_the_dual(kyber512):
    report = estimate(reference_parameter_set("Kyber512"), models=("dual",))
    assert report.beta_usvp is None and report.rop_usvp_log2 is None
    assert report.beta_dual == kyber512.beta_dual
    assert report.minimum_over_models == "dual"
    assert report.rop_classical_log2_min == kyber512.rop_dual_log2


@requires_estimator
def test_a_published_estimate_is_same_scale_and_names_its_revision(kyber512):
    assert kyber512.provenance == SAME_SCALE
    assert kyber512.estimator_revision == estimator_revision()
    assert kyber512.estimator_revision != "unknown"
    assert kyber512.model_parameters["scheme"] == "Kyber512"
    assert (kyber512.model_parameters["n"], kyber512.model_parameters["q"]) == (512, 3329)


# ---------------------------------------------------------------------------------------------
# the inapplicable case, and the unavailable one
# ---------------------------------------------------------------------------------------------


def _square_instance(nu: int = 32, seed: int = 3) -> LatticeQLWRInstance:
    """``m = nu``: as many samples as unknowns, which the normal form then consumes entirely."""
    rng = random.Random(seed)
    q, p = 1 << 16, 1 << 8
    while True:
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(nu))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    return LatticeQLWRInstance(
        nu=nu, q_l=q, p=p, m=nu,
        secret_s=tuple(rng.randrange(q) for _ in range(nu)), base=base, seed=seed,
    )


@requires_estimator
def test_an_instance_with_too_few_samples_has_no_cost_rather_than_an_infinite_one():
    """At ``m = nu`` every family's cost is infinite. That is reported as *absent* — ``None`` and a
    named list of inapplicable models — never as a number a reader could compare against real ones,
    and never as "secure"."""
    report = estimate(parameter_set_from_instance(_square_instance()))

    assert report.beta_usvp is None and report.beta_dual is None
    assert report.rop_usvp_log2 is None and report.rop_dual_log2 is None
    assert report.rop_classical_log2_min is None
    assert report.rop_quantum_log2_min is None
    assert report.minimum_over_models is None
    assert report.model_parameters["inapplicable_models"] == ["primal_usvp", "dual"]
    for model in ("primal_usvp", "dual"):
        entry = report.model_parameters["classical"][model]
        assert entry["applicable"] is False
        assert "infinite cost" in entry["why"]
        assert "beta" not in entry, "a block size read off an inapplicable model is a failure's number"
    assert report.model_parameters["m"] == report.model_parameters["n"] == 32


def test_a_missing_estimator_is_named_rather_than_surfacing_as_an_import_error(monkeypatch):
    """The dependency is made to fail at the import hook; the functions under test are untouched.
    Every entry point must raise :class:`EstimatorUnavailable` with the remedy in the message."""
    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "estimator" or name.startswith("estimator."):
            raise ImportError(f"No module named {name!r}", name=name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)

    with pytest.raises(EstimatorUnavailable, match="not importable") as excinfo:
        reference_parameter_set("Kyber512")
    assert "move_tools.py" in str(excinfo.value)
    assert isinstance(excinfo.value, RuntimeError)
    assert isinstance(excinfo.value.__cause__, ImportError)

    with pytest.raises(EstimatorUnavailable):
        production_parameter_set(samples="rows")
    with pytest.raises(EstimatorUnavailable):
        estimator_revision()
    with pytest.raises(EstimatorUnavailable):
        estimate(cost_estimation.ParameterSet(name="anything", kind="lwe", payload=None))
    with pytest.raises(EstimatorUnavailable):
        parameter_set_from_instance(_square_instance(nu=4))


# ---------------------------------------------------------------------------------------------
# Dilithium — the SIS path
# ---------------------------------------------------------------------------------------------


@requires_estimator
def test_the_sis_schemes_resolve_and_are_routed_as_sis():
    import estimator

    for name in PUBLISHED_SIS_SCHEMES:
        assert hasattr(estimator.schemes, name), name
        assert reference_parameter_set(name).kind == "sis"

    report = estimate(reference_parameter_set("Dilithium2_MSIS_WkUnf"))
    assert report.minimum_over_models == "sis"
    assert report.model_parameters == {"scheme": "Dilithium2_MSIS_WkUnf", "kind": "sis"}
    # The LWE-specific fields are left empty on purpose; a SIS instance has no uSVP block size.
    assert report.beta_usvp is None and report.beta_dual is None


@requires_estimator
def test_dilithium2_returns_a_numeric_cost():
    """``SIS.estimate(Dilithium2_MSIS_WkUnf)`` returns ``lattice: rop ≈2^152.2, β 427`` — the figure
    the estimator's documentation prints. The report must carry it; today it carries ``None``."""
    import estimator

    direct = estimator.SIS.estimate(estimator.schemes.Dilithium2_MSIS_WkUnf, quiet=True)
    expected = math.log2(float(direct["lattice"]["rop"]))
    assert expected == pytest.approx(152.2, abs=BITS_TOLERANCE), "the estimator itself has moved"

    report = estimate(reference_parameter_set("Dilithium2_MSIS_WkUnf"))
    assert report.rop_classical_log2_min is not None, "the SIS report carries no cost at all"
    assert isinstance(report.rop_classical_log2_min, float)
    assert report.rop_classical_log2_min == pytest.approx(expected, abs=BITS_TOLERANCE)


# ---------------------------------------------------------------------------------------------
# the recorded production parameter set
# ---------------------------------------------------------------------------------------------


@requires_estimator
def test_the_production_estimate_under_the_rows_reading_is_pinned(production_rows):
    """The headline the README quotes: 608 samples, 124.39 bits classical."""
    report = production_rows
    assert_beta(report.beta_usvp, 426)
    assert_beta(report.beta_dual, 351)
    assert_bits(report.rop_usvp_log2, 124.39)
    assert_bits(report.rop_dual_log2, 249.63)
    assert_bits(report.rop_classical_log2_min, 124.39)
    assert_bits(report.rop_quantum_log2_min, 112.89)
    assert report.minimum_over_models == "primal_usvp"
    assert report.model_parameters["inapplicable_models"] == []
    assert (report.model_parameters["n"], report.model_parameters["q"],
            report.model_parameters["m"]) == (256, 1 << 16, 608)
    # The primal figures are core-SVP; the quantum one follows from the same block size.
    assert report.rop_usvp_log2 == pytest.approx(CORE_SVP_CLASSICAL * report.beta_usvp, abs=0.01)
    assert report.rop_quantum_log2_min == pytest.approx(CORE_SVP_QUANTUM * report.beta_usvp, abs=0.01)


@requires_estimator
def test_the_production_estimate_under_the_exposure_reading_is_pinned(production_exposure):
    report = production_exposure
    assert_beta(report.beta_usvp, 368)
    assert_beta(report.beta_dual, 387)
    assert_bits(report.rop_usvp_log2, 107.46)
    assert_bits(report.rop_dual_log2, 113.0)
    assert_bits(report.rop_classical_log2_min, 107.46)
    assert_bits(report.rop_quantum_log2_min, 97.52)
    assert report.minimum_over_models == "primal_usvp"
    assert report.model_parameters["m"] == 672_352


@requires_estimator
def test_more_samples_make_the_attack_cheaper_and_never_dearer(production_rows, production_exposure):
    """The two readings are different amounts of data to an attack. The larger one cannot cost more:
    an attacker may always ignore samples. Measured gap: 16.9 bits classical."""
    assert production_exposure.beta_usvp < production_rows.beta_usvp
    assert production_exposure.rop_classical_log2_min < production_rows.rop_classical_log2_min
    assert production_exposure.rop_quantum_log2_min < production_rows.rop_quantum_log2_min
    gap = production_rows.rop_classical_log2_min - production_exposure.rop_classical_log2_min
    assert gap == pytest.approx(16.93, abs=2 * BITS_TOLERANCE)
    # The dual only becomes competitive with the samples to feed it.
    assert production_rows.rop_dual_log2 - production_rows.rop_usvp_log2 > 100
    assert production_exposure.rop_dual_log2 - production_exposure.rop_usvp_log2 < 10


@requires_estimator
def test_the_provenance_argument_is_carried_into_the_report():
    """The mechanism exists: a caller that asks for the extrapolated label gets it."""
    report = estimate(
        production_parameter_set(samples="rows"), models=("primal_usvp",),
        quantum_sieving_speedup=False, provenance=EXTRAPOLATED,
    )
    assert report.provenance == EXTRAPOLATED
    assert PROVENANCE_LABELS[report.provenance] == "extrapolated — not measured"


@requires_estimator
@pytest.mark.parametrize("samples", ["rows", "exposure"])
def test_the_production_estimate_is_labelled_extrapolated(samples, production_rows, production_exposure):
    report = {"rows": production_rows, "exposure": production_exposure}[samples]
    assert report.provenance != SAME_SCALE, (
        "the production parameters were not attacked at any scale, so this is not a same-scale figure"
    )
    assert report.provenance == EXTRAPOLATED


# ---------------------------------------------------------------------------------------------
# the same numbers through the CLI
# ---------------------------------------------------------------------------------------------


class CommandFailed(RuntimeError):
    """The CLI exited non-zero. Deliberately not an ``AssertionError``: inside a test that is
    expected to fail on an assertion, this must still be reported as a failure."""


def _invoke_production_estimate(*arguments: str) -> dict:
    result = CliRunner().invoke(app, ["production-estimate", *arguments])
    if result.exit_code != 0:
        raise CommandFailed(
            f"production-estimate {' '.join(arguments)} exited {result.exit_code}: "
            f"{result.exception!r}\n{result.output[-600:]}"
        )
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def cli_both_readings():
    return _invoke_production_estimate()


@pytest.fixture(scope="module")
def cli_rows_only():
    return _invoke_production_estimate("--samples", "rows")


@requires_estimator
def test_the_cli_reports_both_readings_when_none_is_named(cli_both_readings):
    """A broken command fails this test; it does not skip it."""
    estimates = cli_both_readings["estimates"]
    assert list(estimates) == ["rows", "exposure"]

    rows, exposure = estimates["rows"], estimates["exposure"]
    assert rows["samples_available"] == 608
    assert exposure["samples_available"] == 672_352
    assert_beta(rows["usvp_beta"], 426)
    assert_beta(rows["dual_beta"], 351)
    assert_bits(rows["log2_rop_classical_min"], 124.39)
    assert_bits(rows["log2_rop_quantum_min"], 112.89)
    assert_beta(exposure["usvp_beta"], 368)
    assert_beta(exposure["dual_beta"], 387)
    assert_bits(exposure["log2_rop_classical_min"], 107.46)
    assert_bits(exposure["log2_rop_quantum_min"], 97.52)
    for entry in (rows, exposure):
        assert entry["minimum_over_models"] == "primal_usvp"
        assert entry["log2_rop_quantum_min"] < entry["log2_rop_classical_min"]
        assert entry["estimator_revision"] not in (None, "", "unknown")
        assert entry["provenance"] in PROVENANCE_LABELS
    assert rows["at_or_above_saturation"] is False
    assert exposure["at_or_above_saturation"] is True

    assert "Not measured" in cli_both_readings["scope"]
    assert cli_both_readings["what_this_number_is_for"]
    assert cli_both_readings["obligation_filled"]


@requires_estimator
def test_the_cli_reports_one_reading_when_it_is_named(cli_rows_only, cli_both_readings):
    assert list(cli_rows_only["estimates"]) == ["rows"]
    # Naming the reading selects a row; it must not change the row.
    assert cli_rows_only["estimates"]["rows"] == cli_both_readings["estimates"]["rows"]


@requires_estimator
def test_the_cli_refuses_a_reading_the_corpus_does_not_have():
    result = CliRunner().invoke(app, ["production-estimate", "--samples", "columns"])
    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)
    assert "unknown sample reading 'columns'" in str(result.exception)


@requires_estimator
@pytest.mark.parametrize("named", [False, True], ids=["without --samples", "with --samples rows"])
def test_the_cli_labels_the_production_estimate_extrapolated(named, cli_both_readings, cli_rows_only):
    payload = cli_rows_only if named else cli_both_readings
    assert payload["estimates"], "no estimates were emitted"
    for reading, entry in payload["estimates"].items():
        assert entry["provenance"] == EXTRAPOLATED, (
            f"the {reading!r} reading is emitted as {entry['provenance']!r}"
        )
