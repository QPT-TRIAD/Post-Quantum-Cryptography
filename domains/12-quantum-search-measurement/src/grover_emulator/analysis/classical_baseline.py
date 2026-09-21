"""What the same problem costs a classical machine, counted rather than asserted.

Grover's speedup is a statement about a *specific* classical algorithm: exhaustive search. The
quadratic ratio between ``(N+1)/(M+1)`` evaluations and ``floor(pi/4 * sqrt(N/M))`` iterations is
real, it is exactly computable, and it is the number the report quotes — but it is a statement about
search and about nothing else. A relation whose secret can be recovered algebraically makes both
numbers beside the point, which is precisely why the structural probes exist and why this module's
caveat says so in the baseline's own table rather than in a footnote.

Three counts, kept apart:

* **expected** — ``(N+1)/(M+1)``, exact, in ``Fraction`` arithmetic. The marked set of a generated
  instance is a uniformly random ``M``-subset, items are examined without replacement, and the
  expectation of the index of the first marked item among ``N`` items of which ``M`` are marked is
  ``(N+1)/(M+1)``. Kept exact because it divides evenly into the speedup ratio: the ratio of two
  rationals is a rational, and rounding it into a float before reporting it would be a choice nobody
  asked for.
* **measured** — an actual search over the instance's own marked set, with the starting point drawn
  from a derived seed, counting evaluations until the first hit. It is one sample of that
  distribution, and it is reported as one sample rather than as *the* baseline; when it lands far
  from the expectation that is visible in the table rather than smoothed away.
* **worst case** — ``N - M + 1``, which for ``M = 1`` is every basis state but the last.

The work per evaluation is counted too, for the QLWR instance, because that is the half of the
comparison the cost argument is about: a Grover iteration here costs thousands of IR gates, and a
classical evaluation costs a handful of modular operations. The two are different units and the
module says so next to the ratio rather than leaving a reader to assume a gate is an operation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Mapping, Sequence

import numpy as np

from ..problem.oracle_spec import QLWROracleSpec, OracleSpec
from ..problem.search_space import theoretical_optimal_iterations
from ..utils.seeding import derive_seed, rng_for

__all__ = [
    "ClassicalBaseline",
    "ClassicalSearchMeasurement",
    "expected_queries",
    "worst_case_queries",
    "measure_classical_search",
    "per_query_cost",
    "classical_baseline",
    "BASELINE_CAVEAT",
]

BASELINE_CAVEAT = (
    "The baseline here is exhaustive search, which is the algorithm Grover is compared against and "
    "the only one for which the quadratic speedup is a statement at all. It is not the best known "
    "classical attack on the relation: a structured attack would not search, it would solve, and it "
    "would make both numbers in this table irrelevant. Whether such an attack exists is the question "
    "the structural probes ask, and this table presumes nothing about the answer."
)
"""Carried into every baseline's own output, not appended to the report."""


# -----------------------------------------------------------------------------------------------
# the counts
# -----------------------------------------------------------------------------------------------


def expected_queries(n_items: int, n_marked: int) -> Fraction:
    """``(N+1)/(M+1)`` — the exact expected number of evaluations to the first marked item.

    Exact for a uniformly random marked set of size ``M`` examined without replacement. Returned as a
    ``Fraction`` because the speedup it produces is a ratio of exact numbers, and a baseline reported
    as a float would put a rounding error into the denominator of the project's headline claim.
    """
    if not 1 <= n_marked <= n_items:
        raise ValueError(f"need 1 <= M <= N, got M={n_marked}, N={n_items}")
    return Fraction(n_items + 1, n_marked + 1)


def worst_case_queries(n_items: int, n_marked: int) -> int:
    """``N - M + 1`` evaluations — the last item examined is the last possible marked one."""
    if not 1 <= n_marked <= n_items:
        raise ValueError(f"need 1 <= M <= N, got M={n_marked}, N={n_items}")
    return n_items - n_marked + 1


@dataclass(frozen=True, slots=True)
class ClassicalSearchMeasurement:
    """One classical search, run and counted.

    Attributes:
        queries: evaluations until the first marked value was found.
        found: the marked value that was found.
        offset: where the scan started in the drawn order — the measured quantity is the number of
            evaluations from that start, so a reader can see that the measurement is one draw and not
            a claim about the distribution.
        n_items: ``N``.
        n_marked: ``M``.
        seed_parts: what the draw was derived from, so the sample is reproducible.
    """

    queries: int
    found: int
    offset: int
    n_items: int
    n_marked: int
    seed_parts: tuple[str | int | bytes | None, ...]

    @property
    def fraction_of_space(self) -> float:
        """How much of the register this particular search had examined. One sample, not an average."""
        return self.queries / self.n_items

    def to_dict(self) -> dict:
        return {
            "queries": self.queries,
            "found": self.found,
            "offset": self.offset,
            "n_items": self.n_items,
            "n_marked": self.n_marked,
            "fraction_of_space": self.fraction_of_space,
            "provenance": "measured (one classical scan, seeded)",
        }


def measure_classical_search(
    spec: OracleSpec, seed_parts: Sequence[str | int | bytes | None] = ()
) -> ClassicalSearchMeasurement:
    """Run one classical scan of the instance's own marked set and count the evaluations.

    The scan order is a permutation drawn from a seed derived from the spec and the caller's parts, so
    the measurement is reproducible and two runs of the same report agree. The permutation is
    materialised rather than emulated by drawing with replacement: an algorithm that could re-examine
    the same value would be a different (and worse) algorithm than the one Grover is compared against.
    """
    n_items = spec.space().n_items
    rng = rng_for(
        derive_seed("analysis/classical_baseline", spec.name, spec.search_width(), *seed_parts)
    )
    order = rng.permutation(n_items)
    position = np.empty(n_items, dtype=np.int64)
    position[order] = np.arange(n_items, dtype=np.int64)
    marked = sorted(spec.marked_set())
    positions = position[marked]
    nearest = int(np.argmin(positions))
    offset = int(positions[nearest])
    return ClassicalSearchMeasurement(
        queries=offset + 1,
        found=marked[nearest],
        offset=offset,
        n_items=n_items,
        n_marked=len(marked),
        seed_parts=tuple(seed_parts),
    )


def per_query_cost(spec: OracleSpec) -> dict[str, Any]:
    """The elementary operations one classical evaluation of this relation costs.

    Named term by term, and only for the arithmetic relation, which is the one this project builds a
    circuit for. The count is of *operations*, not of seconds: two multiplications mod a small prime
    are not one IR gate and one IR gate is not one classical operation either. The number is here
    because the cost comparison is meaningless without it, and it is labelled as the model it is.
    """
    if not isinstance(spec, QLWROracleSpec):
        return {
            "applicable": False,
            "reason": (
                f"{spec.name} has no arithmetic form to cost; its marked set is a lookup table, which "
                "is exactly the negative control's point"
            ),
        }
    instance = spec.instance
    multiplications = instance.m * instance.nu
    additions = instance.m * instance.nu
    reductions = instance.m * instance.nu
    roundings = instance.m
    mod_p = instance.m
    return {
        "applicable": True,
        "multiplications": multiplications,
        "additions": additions,
        "reductions_mod_ql": reductions,
        "roundings": roundings,
        "reductions_mod_p": mod_p,
        "elementary_operations": multiplications + additions + reductions + roundings + mod_p,
        "form": "sum_j X_ij * s_j mod q_l, rounded, mod p — per row, over m rows",
        "provenance": "counted from the instance's own (nu, m), not measured on hardware",
    }


# -----------------------------------------------------------------------------------------------
# the baseline
# -----------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ClassicalBaseline:
    """Both sides of the comparison, with their units named and their limits stated.

    The field order is deliberate: ``queries`` is what a report reads first, because a speedup quoted
    without its denominator is not a speedup.
    """

    queries: int
    """The measured scan: one draw from the search, not the expectation."""
    queries_expected: Fraction
    """``(N+1)/(M+1)``, exact."""
    queries_worst_case: int
    n_items: int
    n_marked: int
    grover_iterations: int
    measurement: ClassicalSearchMeasurement
    per_query: Mapping[str, Any] = field(default_factory=dict)
    oracle_gate_count: int | None = None

    # -- the ratio, exactly ---------------------------------------------------------------------

    @property
    def speedup_expected(self) -> Fraction:
        """``expected queries / Grover iterations``, as an exact rational.

        This is the quadratic speedup for this instance, and it is a ratio of exact numbers: both the
        expectation and the optimum are rationals (the optimum is an integer). Reporting it as
        ``Fraction(2049, 100)`` and also as a decimal for a reader is the honest pair; reporting only
        the decimal would be rounding the project's headline claim.
        """
        return self.queries_expected / self.grover_iterations

    @property
    def total_classical_work(self) -> Fraction | None:
        """``expected queries * elementary operations per query``, in classical operations."""
        if not self.per_query.get("applicable"):
            return None
        return self.queries_expected * int(self.per_query["elementary_operations"])

    @property
    def total_grover_work(self) -> int | None:
        """``iterations * IR gates per iteration``, in IR gates. ``None`` without a gate count."""
        if self.oracle_gate_count is None:
            return None
        return self.grover_iterations * self.oracle_gate_count

    @property
    def work_ratio(self) -> Fraction | None:
        """Classical operations against IR gates — different units, and named as such.

        Not a speedup. A logical gate and a modular multiplication are not the same amount of work,
        and a ratio between them is only meaningful once a reader has decided what the conversion is.
        It is reported because the direction and the order of magnitude are the point: one Grover
        iteration at the arithmetic lowering costs thousands of gates, so the count of gates is not a
        count of evaluations.
        """
        classical = self.total_classical_work
        quantum = self.total_grover_work
        if classical is None or quantum is None or quantum == 0:
            return None
        return classical / quantum

    def to_dict(self) -> dict:
        """The mapping a report renders. ``queries`` first, and no number without its provenance."""
        record: dict[str, Any] = {
            "queries": self.queries,
            "queries_provenance": "measured (one seeded scan of the marked set)",
            "queries_expected": str(self.queries_expected),
            "queries_expected_float": float(self.queries_expected),
            "queries_expected_provenance": "exact closed form (N+1)/(M+1)",
            "queries_worst_case": self.queries_worst_case,
            "grover_iterations": self.grover_iterations,
            "speedup_exact": str(self.speedup_expected),
            "speedup": float(self.speedup_expected),
            "n_items": self.n_items,
            "n_marked": self.n_marked,
            "search_measurement": self.measurement.to_dict(),
            "per_query_cost": dict(self.per_query),
            "caveat": BASELINE_CAVEAT,
        }
        if self.total_classical_work is not None:
            record["total_classical_work_operations"] = float(self.total_classical_work)
            record["total_classical_work_provenance"] = "expected queries x operations per query"
        if self.oracle_gate_count is not None:
            record["oracle_gate_count"] = self.oracle_gate_count
            record["total_grover_work_ir_gates"] = self.total_grover_work
        if self.work_ratio is not None:
            record["work_ratio_classical_ops_per_ir_gate"] = float(self.work_ratio)
            record["work_ratio_note"] = (
                "different units: classical operations against IR gates, not a speedup"
            )
        return record

    def describe(self) -> dict:
        """Alias of :meth:`to_dict`, so a run can hand either to the report."""
        return self.to_dict()


def classical_baseline(
    spec: OracleSpec,
    seed_parts: Sequence[str | int | bytes | None] = (),
    oracle_gate_count: int | None = None,
) -> ClassicalBaseline:
    """The classical side of the comparison for this spec, measured and closed-formed.

    Args:
        spec: the oracle. Its marked set supplies ``M``; nothing here takes a config's target
            density, because the baseline and the circuit have to describe the same problem.
        seed_parts: identifies the scan's draw.
        oracle_gate_count: IR gates in one Grover iteration, if the caller has counted them. Supplying
            it adds the operations-against-gates comparison; omitting it leaves that comparison out
            rather than filling it with a guess.

    Raises:
        ValueError: if the spec's search space is empty of marked values, which is not a baseline
            question but a broken instance.
    """
    space = spec.space()
    measurement = measure_classical_search(spec, seed_parts)
    iterations = theoretical_optimal_iterations(space.n_items, space.n_marked)
    if iterations < 1:
        raise ValueError(
            f"M={space.n_marked} of N={space.n_items} needs no iterations at all; there is no "
            "comparison to make against a search that is already over"
        )
    return ClassicalBaseline(
        queries=measurement.queries,
        queries_expected=expected_queries(space.n_items, space.n_marked),
        queries_worst_case=worst_case_queries(space.n_items, space.n_marked),
        n_items=space.n_items,
        n_marked=space.n_marked,
        grover_iterations=iterations,
        measurement=measurement,
        per_query=per_query_cost(spec),
        oracle_gate_count=oracle_gate_count,
    )


def expected_iterations_vs_queries(spec: OracleSpec) -> dict:
    """Both sides as a small table, for a quick look without building anything.

    ``math.sqrt`` appears here and only for display: the *counts* it is compared with are exact, and
    the closed form that produces them is the same one :mod:`grover_emulator.problem.search_space`
    owns.

    Raises:
        ValueError: if the optimum is 0 iterations — a marked set so dense that the search is over
            before it starts. The speedup is a ratio over that count, and the refusal is the same
            one :func:`classical_baseline` makes for the same spec, rather than the bare
            ``ZeroDivisionError`` the division would raise with no word about why.
    """
    space = spec.space()
    queries = expected_queries(space.n_items, space.n_marked)
    iterations = theoretical_optimal_iterations(space.n_items, space.n_marked)
    if iterations < 1:
        raise ValueError(
            f"M={space.n_marked} of N={space.n_items} needs no iterations at all; there is no "
            "comparison to make against a search that is already over"
        )
    return {
        "n_items": space.n_items,
        "n_marked": space.n_marked,
        "queries_expected": str(queries),
        "grover_iterations": iterations,
        "speedup_exact": str(queries / iterations),
        "speedup": float(queries / iterations),
        "quadratic_reference": float(math.sqrt(space.n_items / space.n_marked)),
    }
