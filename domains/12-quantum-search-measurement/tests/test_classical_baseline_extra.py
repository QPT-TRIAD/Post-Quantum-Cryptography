"""The classical side of the comparison, where the existing tests stop at ``M = 1``.

``tests/test_analysis.py`` pins the baseline's counts on single-marked instances, and at ``M = 1`` the
worst case ``N - M + 1`` is just ``N`` — so an implementation that returned ``N`` would pass every one
of them. This file moves off that line:

* the worst case and the expectation are checked by **brute force over every placement** of the marked
  set at small ``N``, so ``N - M + 1`` and ``(N+1)/(M+1)`` are established as the true maximum and the
  true mean of the scan they describe, rather than compared with themselves;
* the **measured scan** is replayed against the permutation it says it drew, and its average over many
  seeded draws is held to the exact expectation within a stated number of standard errors;
* :func:`expected_iterations_vs_queries`, which no test touched, is pinned on two instances and tied
  to :func:`classical_baseline`;
* and the two halves of the headline ratio are checked to be about **the same marked set** — the one
  the Grover circuit amplifies is the one the classical scan finds — in the analysis layer and in a
  real run's stored results.
"""

from __future__ import annotations

import itertools
import math
import statistics
import warnings
from fractions import Fraction

import pytest
import yaml

from grover_emulator.analysis.classical_baseline import (
    classical_baseline,
    expected_iterations_vs_queries,
    expected_queries,
    measure_classical_search,
    worst_case_queries,
)
from grover_emulator.analysis.success_probability import success_curve
from grover_emulator.problem.oracle_spec import RandomControlOracleSpec
from grover_emulator.problem.search_space import theoretical_optimal_iterations
from grover_emulator.utils.seeding import derive_seed, rng_for
from reference_statevector import ReferenceStatevector

BRUTE_FORCE_MAX_ITEMS = 9
"""Every placement of every ``M`` at every ``N`` up to here: 1013 subsets in all, enumerated outright."""

TRIALS = 2000
"""Seeded scans per statistical test. The standard error falls to about a fortieth of one scan's."""

STANDARD_ERRORS = 5.0


def _queries_to_first_hit(placement: tuple[int, ...]) -> int:
    """Evaluations a front-to-back scan spends before it meets a marked position (0-based)."""
    return min(placement) + 1


def _all_placements(n_items: int, n_marked: int):
    return itertools.combinations(range(n_items), n_marked)


# -----------------------------------------------------------------------------------------------
# the worst case, off the M = 1 line
# -----------------------------------------------------------------------------------------------


def test_worst_case_queries_is_n_minus_m_plus_one_for_several_marked_items():
    """The values an implementation returning ``N`` gets wrong."""
    assert worst_case_queries(16, 4) == 13
    assert worst_case_queries(64, 3) == 62
    assert worst_case_queries(256, 8) == 249
    assert worst_case_queries(4096, 2) == 4095
    # Everything marked: the first look succeeds. Everything but one: two looks at most.
    assert worst_case_queries(16, 16) == 1
    assert worst_case_queries(16, 15) == 2
    assert isinstance(worst_case_queries(16, 4), int)
    for n_marked in range(2, 17):
        assert worst_case_queries(16, n_marked) < 16


@pytest.mark.parametrize("n_items", range(1, BRUTE_FORCE_MAX_ITEMS + 1))
def test_worst_case_queries_is_the_true_maximum_over_every_placement(n_items):
    """Brute force: over all ``C(N, M)`` placements the longest scan is exactly ``N - M + 1``.

    By symmetry the scan order does not matter — a fixed order against every placement covers the
    same cases as every order against a fixed placement — so the maximum here is the worst case of
    the algorithm and not of one ordering. The placement attaining it is checked to be the one the
    docstring names: every marked item at the very end.
    """
    for n_marked in range(1, n_items + 1):
        counts = {
            placement: _queries_to_first_hit(placement)
            for placement in _all_placements(n_items, n_marked)
        }
        assert len(counts) == math.comb(n_items, n_marked)
        worst = max(counts.values())
        assert worst_case_queries(n_items, n_marked) == worst == n_items - n_marked + 1
        attained = [placement for placement, count in counts.items() if count == worst]
        assert attained == [tuple(range(n_items - n_marked, n_items))]
        assert min(counts.values()) == 1


@pytest.mark.parametrize("n_items", range(1, BRUTE_FORCE_MAX_ITEMS + 1))
def test_expected_queries_is_the_true_mean_over_every_placement(n_items):
    """The same enumeration, averaged exactly: ``(N+1)/(M+1)`` as a ``Fraction``, to the last digit."""
    for n_marked in range(1, n_items + 1):
        counts = [_queries_to_first_hit(p) for p in _all_placements(n_items, n_marked)]
        mean = Fraction(sum(counts), len(counts))
        assert expected_queries(n_items, n_marked) == mean == Fraction(n_items + 1, n_marked + 1)
        assert 1 <= mean <= worst_case_queries(n_items, n_marked)


def test_the_counts_refuse_a_marked_set_that_cannot_exist():
    for bad in ((8, 0), (8, 9), (8, -1), (0, 0)):
        with pytest.raises(ValueError, match="1 <= M <= N"):
            worst_case_queries(*bad)
        with pytest.raises(ValueError, match="1 <= M <= N"):
            expected_queries(*bad)


# -----------------------------------------------------------------------------------------------
# the measured scan
# -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n_marked", [1, 3, 8])
def test_the_measured_scan_is_the_first_hit_in_the_permutation_it_drew(n_marked):
    """Replayed element by element, the way a classical machine would actually run it.

    The module says where its scan order comes from — a permutation seeded from the module's own
    label, the spec's name and width, and the caller's parts — so the order is rebuilt here and
    walked with a plain loop. That the vectorised position lookup in the source equals this loop is
    the claim that ``queries`` is a count of evaluations and not of something near it.
    """
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=n_marked, seed=9)
    marked = spec.marked_set()
    for trial in range(25):
        parts = ("replay", trial)
        measurement = measure_classical_search(spec, parts)
        order = rng_for(
            derive_seed("analysis/classical_baseline", spec.name, spec.search_width(), *parts)
        ).permutation(1 << 6)
        assert sorted(order) == list(range(1 << 6)), "a scan without replacement visits each value once"

        evaluations = 0
        for candidate in order:
            evaluations += 1
            if int(candidate) in marked:
                break
        assert measurement.queries == evaluations
        assert measurement.found == int(candidate)
        assert measurement.offset == evaluations - 1
        assert measurement.n_marked == n_marked and measurement.n_items == 64
        assert measurement.seed_parts == parts


@pytest.mark.parametrize(("n_qubits", "n_marked"), [(6, 1), (6, 3), (8, 8)])
def test_the_measured_scan_averages_to_the_exact_expectation(n_qubits, n_marked):
    """``TRIALS`` seeded scans against ``(N+1)/(M+1)``, within five standard errors of the mean.

    The standard error is not estimated from the sample: the first-hit position of ``M`` marked items
    among ``N`` has variance ``M (N+1) (N-M) / ((M+1)^2 (M+2))``, so the tolerance is fixed before a
    single scan is drawn. The seeds are fixed too, which makes the test deterministic; the tolerance
    is what makes it a statement about the scan rather than about these seeds.
    """
    spec = RandomControlOracleSpec(n_qubits=n_qubits, n_marked=n_marked, seed=21)
    n_items = 1 << n_qubits
    worst = worst_case_queries(n_items, n_marked)
    marked = spec.marked_set()

    counts = []
    for trial in range(TRIALS):
        measurement = measure_classical_search(spec, ("expectation", trial))
        assert 1 <= measurement.queries <= worst
        assert measurement.found in marked
        counts.append(measurement.queries)

    expectation = float(expected_queries(n_items, n_marked))
    variance = n_marked * (n_items + 1) * (n_items - n_marked) / ((n_marked + 1) ** 2 * (n_marked + 2))
    standard_error = math.sqrt(variance / TRIALS)
    assert statistics.fmean(counts) == pytest.approx(expectation, abs=STANDARD_ERRORS * standard_error)
    # The spread is the distribution's own, so the draws are neither constant nor the mean relabelled.
    assert statistics.pvariance(counts) == pytest.approx(variance, rel=0.15)
    assert len(set(counts)) > 20
    assert min(counts) == 1, "with 2000 draws some scan starts on a marked value"


def test_different_seed_parts_draw_different_scans_of_the_same_marked_set():
    spec = RandomControlOracleSpec(n_qubits=8, n_marked=8, seed=21)
    draws = {measure_classical_search(spec, ("vary", trial)).queries for trial in range(40)}
    assert len(draws) > 10
    assert measure_classical_search(spec, ("vary", 0)) == measure_classical_search(spec, ("vary", 0))


# -----------------------------------------------------------------------------------------------
# both sides as one small table
# -----------------------------------------------------------------------------------------------


def test_expected_iterations_vs_queries_on_a_three_marked_instance():
    """``N = 64, M = 3``: ``65/4`` evaluations against ``floor(pi/4 * sqrt(64/3)) = 3`` iterations."""
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=3, seed=9)
    table = expected_iterations_vs_queries(spec)
    assert table == {
        "n_items": 64,
        "n_marked": 3,
        "queries_expected": "65/4",
        "grover_iterations": 3,
        "speedup_exact": "65/12",
        "speedup": pytest.approx(65 / 12),
        "quadratic_reference": pytest.approx(math.sqrt(64 / 3)),
    }
    assert Fraction(table["speedup_exact"]) == Fraction(table["queries_expected"]) / 3


def test_expected_iterations_vs_queries_on_the_worked_instance(qlwr_spec):
    """The headline ratio, ``4097/100``, from the table that builds nothing."""
    table = expected_iterations_vs_queries(qlwr_spec)
    assert table["n_items"] == 4096 and table["n_marked"] == 1
    assert table["queries_expected"] == "4097/2"
    assert table["grover_iterations"] == 50
    assert table["speedup_exact"] == "4097/100"
    assert table["speedup"] == pytest.approx(40.97)
    assert table["quadratic_reference"] == pytest.approx(64.0)


@pytest.mark.parametrize(("n_qubits", "n_marked"), [(5, 1), (6, 3), (8, 8), (8, 30)])
def test_the_quick_table_and_the_full_baseline_are_the_same_comparison(n_qubits, n_marked):
    """Two entry points, one set of numbers: neither may quote a ratio the other would not."""
    spec = RandomControlOracleSpec(n_qubits=n_qubits, n_marked=n_marked, seed=4)
    table = expected_iterations_vs_queries(spec)
    baseline = classical_baseline(spec, ("same-comparison",))
    assert table["n_items"] == baseline.n_items == 1 << n_qubits
    assert table["n_marked"] == baseline.n_marked == n_marked
    assert Fraction(table["queries_expected"]) == baseline.queries_expected
    assert table["grover_iterations"] == baseline.grover_iterations
    assert table["grover_iterations"] == theoretical_optimal_iterations(1 << n_qubits, n_marked)
    assert Fraction(table["speedup_exact"]) == baseline.speedup_expected
    assert table["speedup"] == pytest.approx(float(baseline.speedup_expected))
    # A quadratic speedup: the exact ratio is within a small constant of sqrt(N/M).
    assert 0.5 * table["quadratic_reference"] < table["speedup"] < 2.0 * table["quadratic_reference"]
    assert baseline.queries_worst_case == (1 << n_qubits) - n_marked + 1


def test_a_marked_set_needing_no_iterations_is_refused_with_a_reason():
    """``M = 12`` of ``N = 16``: the search is over before it starts, and both entry points say so."""
    spec = RandomControlOracleSpec(n_qubits=4, n_marked=12, seed=2)
    assert theoretical_optimal_iterations(16, 12) == 0
    with pytest.raises(ValueError, match="needs no iterations"):
        classical_baseline(spec)
    with pytest.raises(ValueError, match="no iterations"):
        expected_iterations_vs_queries(spec)


# -----------------------------------------------------------------------------------------------
# the quantum and the classical side are about the same marked set
# -----------------------------------------------------------------------------------------------


def test_the_baseline_and_the_curve_at_one_width_share_one_marked_set():
    """``M``, ``N`` and the optimum are read from the same spec by both, and the hit is in its set."""
    spec = RandomControlOracleSpec(n_qubits=6, n_marked=3, seed=9)
    curve = success_curve(spec, ReferenceStatevector())
    baseline = classical_baseline(spec, ("same-set",))

    assert baseline.n_items == curve.n_items == 64
    assert baseline.n_marked == curve.n_marked == len(spec.marked_set()) == 3
    assert baseline.grover_iterations == curve.optimal_iterations == curve.peak_measured.iteration
    assert baseline.measurement.found in spec.marked_set()
    # The speedup's two halves, recomputed from the curve's own record of the problem.
    assert baseline.speedup_expected == Fraction(curve.n_items + 1, curve.n_marked + 1) / (
        curve.optimal_iterations
    )


def test_the_classical_hit_follows_the_specs_marked_set_not_the_width():
    """Two controls at one width and one ``M``: each scan finds a value of *its own* marked set.

    A baseline keyed on ``(N, M)`` alone would pass the test above; this one separates two problems
    that share both numbers, and requires the scans to tell them apart.
    """
    first = RandomControlOracleSpec(n_qubits=8, n_marked=4, seed=1)
    second = RandomControlOracleSpec(n_qubits=8, n_marked=4, seed=2)
    assert first.marked_set().isdisjoint(second.marked_set()), "pick seeds whose sets do not overlap"
    for trial in range(50):
        parts = ("own-set", trial)
        assert measure_classical_search(first, parts).found in first.marked_set()
        assert measure_classical_search(second, parts).found in second.marked_set()
        assert measure_classical_search(first, parts).found not in second.marked_set()


def test_a_real_run_compares_grover_and_the_scan_on_the_marked_set_it_stored(tmp_path):
    """The pipeline's own results: the curve's marked set is the baseline's, value for value."""
    from grover_emulator.cli import run_experiment

    config = tmp_path / "control.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "oracle": {"type": "random_control", "target_qubits": 6, "marked_fraction": 0.05},
                "sweep": {"qubit_range": [6]},
                "backend": {"shots": 100},
                "output": {"dir": (tmp_path / "results").as_posix(), "formats": ["json", "markdown"]},
            }
        ),
        encoding="utf-8",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        _run_dir, results = run_experiment(config)

    baseline = results["classical_baseline"]
    marked = results["marked_set"]
    assert results["marked_set_size"] == len(marked) == 3  # round(0.05 * 64)
    assert baseline["n_marked"] == len(marked) and baseline["n_items"] == results["n_items"] == 64
    assert baseline["search_measurement"]["found"] in marked
    assert baseline["grover_iterations"] == results["optimal_iterations"]
    assert baseline["queries_worst_case"] == 64 - 3 + 1
    assert Fraction(baseline["queries_expected"]) == Fraction(65, 4)
    assert 1 <= baseline["queries"] <= baseline["queries_worst_case"]
    # And the quantum side of the same results amplified exactly those values: the measured peak is
    # the closed form for this M, which a curve over any other sized set would miss.
    peak = max(results["curve"], key=lambda record: record["empirical_p_success"])
    assert peak["iteration"] == baseline["grover_iterations"]
    theta = math.asin(math.sqrt(len(marked) / 64))
    assert peak["empirical_p_success"] == pytest.approx(
        math.sin((2 * peak["iteration"] + 1) * theta) ** 2, abs=1e-12
    )
