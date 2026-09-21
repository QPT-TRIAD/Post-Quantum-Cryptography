"""The whole pipeline, and the integration pass that the sibling project showed is not optional.

Every other test file checks one layer against its own contract. This one checks that the layers
still compose, and it exists because the sibling Grover project's integration pass found three real
defects in modules that were each already green in isolation — all of them at boundaries, where two
components validated against *different* references meet.

The cross-check battery is the explicit answer to that. Each invariant below is computed two ways
from independent references, and each is shown non-vacuous: a deliberately corrupted input must be
caught by the check that claims to catch it.
"""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pytest

from qlwr_lattice_stress.analysis.hermite_factor import (
    achieved_root_hermite_factor,
    hermite_factor_from_gso,
)
from qlwr_lattice_stress.attacks import (
    find_minimum_successful_block_size,
    recover_secret_from_vector,
    run_dual_attack,
)
from qlwr_lattice_stress.engines import FpylllBKZEngine, assert_same_lattice
from qlwr_lattice_stress.lattice._exact import NotInLattice
from qlwr_lattice_stress.lattice.basis_construction import (
    assert_basis_valid,
    basis_determinant_abs,
    build_primal_embedding_basis,
    build_qary_basis,
)
from qlwr_lattice_stress.lattice.dual_embedding import assert_dual_valid, dual_basis
from qlwr_lattice_stress.lattice.planted_vector import assert_in_lattice, planted_short_vector
from qlwr_lattice_stress.problem.normal_form import invert_normal_form, to_normal_form
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)
from qlwr_lattice_stress.protocols import EXTRAPOLATED, MEASURED
from engine_helpers import matrix_rows, qary_basis  # type: ignore[import-not-found]
from qlwr_lattice_stress.reporting import (
    SCOPE_BOUNDARY,
    assert_boundary_precedes_first_table,
    generate_report,
)
from qlwr_lattice_stress.utils.seeding import RunSeeds

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8
NU, M = 32, 76


def make_instance(seed: int = 1) -> LatticeQLWRInstance:
    rng = random.Random(seed)
    while True:
        base = tuple(tuple(rng.randrange(PRODUCTION_Q) for _ in range(NU)) for _ in range(M))
        if full_column_rank_mod([list(r) for r in base], PRODUCTION_Q, NU) == NU:
            break
    return LatticeQLWRInstance(
        nu=NU, q_l=PRODUCTION_Q, p=PRODUCTION_P, m=M,
        secret_s=tuple(rng.randrange(PRODUCTION_Q) for _ in range(NU)), base=base, seed=seed,
    )


@pytest.fixture(scope="module")
def engine():
    return FpylllBKZEngine()


# ---------------------------------------------------------------------------------------------
# the pipeline runs end to end
# ---------------------------------------------------------------------------------------------


@pytest.mark.slow
def test_the_whole_pipeline_runs_and_produces_a_report(engine, tmp_path):
    """Spec to instance to normal form to lattice to attack to report, on the real engines."""
    instance = make_instance()
    minimum, results = find_minimum_successful_block_size(instance, engine, [2, 20, 30, 40])

    assert minimum is not None, "no block size recovered the secret"
    recovered = [r for r in results if r.recovered]
    assert recovered, "the minimum was reported with no successful point"

    nf = to_normal_form(instance)
    assert recover_secret_from_vector(
        planted_short_vector(nf, embedding_factor=recovered[0].embedding_factor or 3), nf, instance
    ) == tuple(instance.secret_s)

    report = generate_report(
        tmp_path,
        {},
        {
            "run_id": "e2e",
            "instance": instance.describe(),
            "minimum_block_sizes": {"primal_usvp": minimum},
            "attacks": [
                {"family": "primal_usvp", "block_size": r.block_size, "dimension": r.dimension,
                 "recovered": r.recovered, "wall_clock_s": r.wall_clock_s,
                 "root_hermite_factor": r.root_hermite_factor}
                for r in results
            ],
        },
    )
    text = report.read_text()
    assert SCOPE_BOUNDARY in text
    assert_boundary_precedes_first_table(text)


# ---------------------------------------------------------------------------------------------
# the report reads the fit that was written
# ---------------------------------------------------------------------------------------------


def _section_five(tmp_path, scaling):
    report = generate_report(tmp_path, {}, {"run_id": "s5", "scaling": scaling})
    text = report.read_text()
    return text.split("## 5.", 1)[1].split("## 6.", 1)[0]


#: What ``pipeline._fit_across_the_sweep`` actually writes. Reproduced here rather than imported so
#: the test fails when the *shape* changes, which is the failure it exists to catch.
_CROSS_SWEEP_SCALING = {
    "kind": "block_size_growth",
    "measured": {
        "slope": 0.5984, "intercept": -21.066, "r_squared": 0.9294,
        "n_points": 5, "fitted_dimension_min": 40, "fitted_dimension_max": 130,
    },
    "extrapolated": {
        "target_dimension": 160, "predicted_block_size": 74.67,
        "core_svp_log2_cost": 21.8, "core_svp_c": 0.292, "provenance": EXTRAPOLATED,
    },
    "scope": "fitted across the sweep",
}


def test_the_cross_sweep_fit_is_rendered_not_dashed(tmp_path):
    """A reader who sees ``—`` in every cell reads "no fit was produced", which is false.

    This is the defect it is written against: the fit began writing a nested ``measured`` /
    ``extrapolated`` shape while section 5 still read the old flat one, and the report rendered a
    full table of dashes. Every test in the suite passed — the fit was correct, the renderer was
    correct, and only their disagreement was wrong. The assertion is therefore on the *rendered*
    text, because that is the only place the disagreement existed.
    """
    section = _section_five(tmp_path, _CROSS_SWEEP_SCALING)
    assert "0.5984" in section, "the fitted slope did not reach the report"
    assert "0.9294" in section, "the fit's R squared did not reach the report"
    assert "74.67" in section, "the extrapolated block size did not reach the report"
    assert "160" in section

    # The dashes are checked as a set: a row that *should* carry a number and shows a dash is the
    # failure, and listing them keeps the message specific when one reappears.
    for label in ("slope (block sizes per unit dimension)", "R squared", "predicted block size there"):
        row = next(r for r in section.splitlines() if r.startswith(f"| {label} "))
        assert "| — |" not in row, f"{label!r} rendered as a dash: {row}"


def test_the_per_run_fit_still_renders(tmp_path):
    """The older flat shape remains reachable — ``run_experiment`` writes it when a single run
    supplies enough points. Supporting the new shape must not have removed the old one."""
    section = _section_five(
        tmp_path,
        {"c": 0.292, "intercept": 7.0, "r_squared": 0.99, "n_points": 5,
         "fitted_beta_min": 20, "fitted_beta_max": 60, "extrapolates_outside_fitted_domain": True},
    )
    assert "0.292" in section and "R squared" in section


def test_a_run_with_no_fit_says_so_rather_than_showing_a_table(tmp_path):
    """The third state. "No fit was produced" and "the fit produced no numbers" are different
    claims, and only the first is a fact about the run."""
    section = _section_five(tmp_path, {})
    assert "No fit was produced" in section
    assert "|" not in section


def test_the_pipeline_writes_a_fit_the_report_can_read(tmp_path):
    """The boundary that actually broke, driven through the real producer.

    Reading a stored results tree would test the same thing only when that tree happens to be
    complete, and would false-alarm during a sweep — the fit is written into every run at the *end*,
    so a mid-flight tree legitimately has runs without it. Driving ``_fit_across_the_sweep`` on
    synthetic outcomes tests the producer-to-renderer contract directly, and tests it always.

    The defect this pins: the producer began writing a nested ``measured`` / ``extrapolated`` shape
    while the renderer still read the old flat one. Both sides were internally consistent and the
    suite was green; the reports rendered a full table of dashes.
    """
    from qlwr_lattice_stress.config.schema import load_config
    from qlwr_lattice_stress.pipeline import _fit_across_the_sweep

    config = load_config(Path(__file__).resolve().parents[1] / "config" / "default_experiment.yaml")
    # Only the sweep's target dimension is read from the config, so the shipped one is fine.
    outcomes = []
    for dimension, block_size in ((40, 10), (60, 10), (80, 20), (100, 40)):
        run_dir = tmp_path / f"d{dimension}"
        run_dir.mkdir()
        outcomes.append({
            "run_id": f"d{dimension}",
            "run_dir": str(run_dir),
            "instance": {"qary_lattice_dimension": dimension},
            "minimum_block_sizes": {"primal_usvp": block_size},
            "attacks": [
                {"family": "primal_usvp", "block_size": block_size, "dimension": dimension + 1,
                 "provenance": MEASURED, "recovered": True, "wall_clock_s": float(block_size)},
            ],
        })

    _fit_across_the_sweep(outcomes, config)

    scaling = outcomes[0]["scaling"]
    assert scaling["kind"] == "block_size_growth", "the producer wrote no fit"
    assert scaling["measured"]["n_points"] == 4
    assert scaling["extrapolated"]["provenance"] == EXTRAPOLATED

    # And the report generated by that same call renders it, rather than a table of dashes.
    rendered = (tmp_path / "d40" / "report.md").read_text()
    section = rendered.split("## 5.", 1)[1].split("## 6.", 1)[0]
    assert "| slope (block sizes per unit dimension) | — |" not in section, (
        "the producer wrote a fit the renderer could not read — this is the defect, reproduced"
    )
    assert f"{scaling['extrapolated']['predicted_block_size']:.4g}" in section, (
        "the extrapolated block size did not reach the report"
    )


# ---------------------------------------------------------------------------------------------
# the cross-check battery
# ---------------------------------------------------------------------------------------------


def test_cross_check_1_the_planted_vector_is_in_the_lattice():
    """Route 1: constructed from the instance's own recorded error. Route 2: an exact solve against
    the basis. They meet at the vector, and a corrupted vector must NOT solve."""
    nf = to_normal_form(make_instance())
    basis = build_primal_embedding_basis(nf, embedding_factor=3)
    planted = list(planted_short_vector(nf, embedding_factor=3))
    assert_in_lattice(planted, basis)

    planted[0] = int(planted[0]) + 1
    with pytest.raises(NotInLattice):
        assert_in_lattice(planted, basis)


def test_cross_check_4_basis_validity_two_independent_checks():
    """Structural (every row satisfies the relation) and volumetric (|det| = q^m). They fail for
    different bugs, and each is shown to fail on a corruption the other accepts."""
    from fpylll import IntegerMatrix

    nf = to_normal_form(make_instance())
    basis = build_qary_basis(nf)
    assert_basis_valid(basis, nf)
    assert basis_determinant_abs(basis) == nf.q**nf.m

    def copy_of(b):
        c = IntegerMatrix(b.nrows, b.ncols, int_type="mpz")
        for i in range(b.nrows):
            for j in range(b.ncols):
                c[i, j] = int(b[i, j])
        return c

    structurally_broken = copy_of(basis)
    structurally_broken[0, 0] = int(structurally_broken[0, 0]) + 1
    with pytest.raises(AssertionError, match="not in the lattice"):
        assert_basis_valid(structurally_broken, nf)

    volumetrically_broken = copy_of(basis)
    for j in range(basis.ncols):
        volumetrically_broken[nf.n, j] = 2 * int(volumetrically_broken[nf.n, j])
    with pytest.raises(AssertionError, match="volume|det"):
        assert_basis_valid(volumetrically_broken, nf)


def test_cross_check_4b_the_dual_invariants_are_independent():
    """Annihilation is the definition; the volume is a different property. A basis can satisfy one
    and fail the other.

    Both halves, each matched on its own message. This used to break annihilation only and accept
    any ``AssertionError`` — so the volume check was never exercised, and "independent" was asserted
    by a test that would have passed with one of the two checks deleted.
    """
    from fpylll import IntegerMatrix

    nf = to_normal_form(make_instance())
    dual = dual_basis(nf)
    primal = build_qary_basis(nf)
    assert_dual_valid(dual, primal, nf)

    def copy_of_the_dual():
        copied = IntegerMatrix(dual.nrows, dual.ncols, int_type="mpz")
        for i in range(dual.nrows):
            for j in range(dual.ncols):
                copied[i, j] = int(dual[i, j])
        return copied

    # Out of the dual altogether: one entry moved by one. Annihilation sees it first.
    not_dual = copy_of_the_dual()
    not_dual[0, 0] = int(not_dual[0, 0]) + 1
    with pytest.raises(AssertionError, match="not orthogonal to a primal sample row"):
        assert_dual_valid(not_dual, primal, nf)

    # Still in the dual — a doubled row annihilates everything the row did — but an index-2
    # sublattice of it. Annihilation passes; only the exact determinant can object.
    sublattice = copy_of_the_dual()
    for j in range(sublattice.ncols):
        sublattice[0, j] = 2 * int(sublattice[0, j])
    with pytest.raises(AssertionError, match="span a different volume"):
        assert_dual_valid(sublattice, primal, nf)


@pytest.mark.slow
def test_cross_check_6_the_engine_preserves_the_lattice(engine):
    """The strongest invariant in the project.

    fpylll and G6K each return something self-consistent, and a reduction that silently changed the
    lattice would produce a plausible basis and a plausible root-Hermite factor. No per-engine test
    can see it — it is the lattice analogue of a bit-ordering bug that survived a whole suite in the
    sibling project because every layer was individually correct.
    """
    nf = to_normal_form(make_instance())
    basis = build_qary_basis(nf)
    outcome = engine.reduce(basis, 20)
    assert_same_lattice(basis, outcome.basis)

    from fpylll import IntegerMatrix

    corrupted = IntegerMatrix(basis.nrows, basis.ncols, int_type="mpz")
    for i in range(basis.nrows):
        for j in range(basis.ncols):
            corrupted[i, j] = int(basis[i, j])
    corrupted[0, 0] = int(corrupted[0, 0]) + 1
    with pytest.raises(Exception):
        assert_same_lattice(basis, corrupted)


def test_cross_check_5_the_hermite_routes_agree(engine):
    """Exact integer determinant against the library's Gram-Schmidt data."""
    nf = to_normal_form(make_instance())
    basis = build_qary_basis(nf)
    outcome = engine.reduce(basis, 20)
    exact = achieved_root_hermite_factor(outcome.basis)
    via_gso = hermite_factor_from_gso(outcome.basis)
    assert exact == pytest.approx(via_gso, rel=1e-9)


def test_cross_check_7_a_recorded_seed_re_derives_its_draws():
    """The seed bookkeeping half of reproducibility.

    **This is only half, and its earlier name claimed the whole.** It was called "a run is
    reproducible from its own record", which is a claim about reductions; the body re-derives seeds
    from a root and never reduces anything, so it certified a property it could not observe. The
    reduction half is ``test_cross_check_7b``, and it is the half that fails when an engine is
    configured to run in a way that is not bit-reproducible.
    """
    seeds = RunSeeds(root=20260913)
    for i in range(5):
        seeds.derive("sweep", i)
    seeds.verify()

    restored = RunSeeds.from_dict(seeds.to_dict())
    restored.verify()
    assert restored.derive("sweep", 3) == seeds.derive("sweep", 3)


def test_cross_check_7b_the_reduction_half_of_reproducibility(engine):
    """The half the row above cannot reach: does the same input reduce to the same basis?

    Two things are asserted, and the second is the one that was missing.

    **One.** At one thread, a seeded engine returns a bit-identical basis — this is a measurement,
    not a policy, and it is what makes a recorded seed worth recording.

    **Two.** Every recorded attack point carries the engine and the thread count that produced it.
    Without them a minimum block size found at four threads — a single draw, not a measurement — is
    indistinguishable in the results file from one found at one thread. That is how the dimension
    sweep's minima came to be fitted as though they were measurements when they were not: the
    engine layer recorded the thread count honestly, and the attack layer dropped it.
    """
    instance = make_instance()
    engine = FpylllBKZEngine(threads=1)

    first = engine.reduce(qary_basis(dimension=40), 20)
    second = engine.reduce(qary_basis(dimension=40), 20)
    assert matrix_rows(first.basis) == matrix_rows(second.basis), (
        "one thread is supposed to be bit-reproducible; if this fails, no recorded seed "
        "reproduces anything and the results files describe nothing"
    )

    minimum, results = find_minimum_successful_block_size(
        instance, engine, [2, 10], max_seconds_per_block_size=1e-9
    )
    assert results, "the sweep produced no points to check"
    for r in results:
        assert r.engine, (
            f"a block-size-{r.block_size} point records no engine, so a reader cannot tell which "
            "implementation produced it"
        )
    measured = [r for r in results if r.provenance == MEASURED]
    assert measured, "no measured point, so the thread check below would be vacuous"
    for r in measured:
        assert r.threads == 1, (
            f"a point that ran reports threads={r.threads}; the field means what ran. If the engine "
            "ran above one thread this point is a single draw and must say so."
        )


# ---------------------------------------------------------------------------------------------
# the boundary stays where it was put
# ---------------------------------------------------------------------------------------------


def test_the_dual_attack_is_recorded_as_inapplicable_rather_than_absent(engine):
    """The asymmetry found at M7 is a result, and it must survive into the pipeline rather than
    being silently dropped as a missing number."""
    result = run_dual_attack(make_instance(), engine, 20)
    assert result.provenance == "not_run"
    assert result.not_run_reason


def test_no_source_file_names_the_research_tree():
    """The boundary as a property of the code, not of anyone's memory."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "src"
    offenders = [
        str(p.relative_to(root)) for p in root.rglob("*.py")
        if "Documents/PQT" in p.read_text()
    ]
    assert not offenders, offenders
