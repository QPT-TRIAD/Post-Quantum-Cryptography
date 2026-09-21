"""Exhaustive verification of the arithmetic blocks.

Every test here applies the block to **every** basis state at small widths and compares against
Python's own integer arithmetic, so there is no sampling and no tolerance. That is affordable
because a reversible block on a basis state is a bit permutation: the cost is one machine word per
state, not a matrix.

``sample_intervals`` gets the same treatment, and it is the one that matters most — the ``a = 0``
wrap bucket fires only for accumulator values in the top ``1/p`` of the range, so a circuit that
omitted it would still agree with the relation on all but a handful of rows, would still usually
produce ``M = 1``, and would still peak at the right ``k``. It would not look like a bug.
"""

from __future__ import annotations

import math

import pytest

from grover_emulator.circuits.reversible_arithmetic import (
    add_constant,
    equal_to_constant,
    less_than_constant,
    multi_controlled_x,
    sample_intervals,
    verify_add_constant,
    verify_equal_to_constant,
    verify_less_than_constant,
)
from grover_emulator.circuits.ir import GateList, GateName
from grover_emulator.problem.qlwr_instance import round_half_up


# ---------------------------------------------------------------------------------------------
# exhaustive
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_add_constant_exhaustive(n):
    for constant in range(1 << n):
        verify_add_constant(n, constant, controlled=False)
        verify_add_constant(n, constant, controlled=True)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6])
def test_less_than_constant_exhaustive(n):
    for constant in range((1 << n) + 3):
        verify_less_than_constant(n, constant)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_equal_to_constant_exhaustive(n):
    for value in range(1 << n):
        verify_equal_to_constant(n, value)


def test_controlled_add_preserves_its_control():
    """A controlled adder that overwrote its control would pass a register-only comparison."""
    verify_add_constant(3, 5, controlled=True)


def test_less_than_constant_demands_enough_work_ancillas():
    gl = GateList(5)
    with pytest.raises(ValueError):
        less_than_constant(gl, [0, 1, 2], 4, 3, [4])  # 3 needed, 1 given


def test_add_constant_rejects_a_constant_that_does_not_fit():
    gl = GateList(2)
    with pytest.raises(ValueError):
        add_constant(gl, [0, 1], 4)


def test_multi_controlled_x_picks_the_smallest_gate_that_fits():
    """Counting a two-control X as a multi-controlled one would inflate every Toffoli-equivalent
    number in the project."""
    gl = GateList(6)
    multi_controlled_x(gl, (), 0)
    multi_controlled_x(gl, (0,), 1)
    multi_controlled_x(gl, (0, 1), 2)
    multi_controlled_x(gl, (0, 1, 2), 3)
    assert [g.name for g in gl.gates] == [
        GateName.X,
        GateName.CX,
        GateName.CCX,
        GateName.MCX,
    ]


# ---------------------------------------------------------------------------------------------
# the interval table
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("q_l,p", [(61, 19), (61, 13), (251, 83), (43, 11)])
def test_intervals_partition_one_period_exactly(q_l, p):
    """Every accumulator value in ``[0, q_l)`` belongs to exactly one bucket."""
    counts = [0] * q_l
    for a in range(p):
        for lo, hi in sample_intervals(q_l, p, a):
            for v in range(lo, hi + 1):
                counts[v] += 1
    assert counts == [1] * q_l


@pytest.mark.parametrize("q_l,p", [(61, 19), (61, 13), (43, 11)])
def test_intervals_agree_with_the_relation_arithmetic(q_l, p):
    """Bucket membership must equal the relation's own definition of the sample."""
    for a in range(p):
        intervals = sample_intervals(q_l, p, a)
        for v in range(q_l):
            in_bucket = any(lo <= v <= hi for lo, hi in intervals)
            assert in_bucket == (round_half_up(v * p, q_l) % p == a), (
                f"q_l={q_l} p={p} a={a} v={v}"
            )


def test_the_zero_bucket_wraps_and_that_is_the_trap():
    """``a = 0`` is the union of the bottom interval and the top one, because the raw rounded value
    ``p`` reduces to ``0``. If this ever becomes a single interval the wrap case has been lost."""
    intervals = sample_intervals(61, 13, 0)
    assert len(intervals) == 2, intervals
    assert intervals[0][0] == 0
    assert intervals[-1][1] >= 61 - 1


def test_the_wrap_case_is_reachable_by_construction():
    """A value that only the wrap interval covers, so a circuit omitting it is caught."""
    q_l, p = 61, 13
    intervals = sample_intervals(q_l, p, 0)
    wrap_lo, wrap_hi = intervals[-1]
    probe = wrap_hi
    assert wrap_lo <= probe <= wrap_hi
    assert round_half_up(probe * p, q_l) % p == 0
    assert probe > intervals[0][1], "the probe must not also be in the primary interval"


@pytest.mark.parametrize("q_l,p", [(61, 19), (43, 11)])
def test_repeated_intervals_partition_the_full_range(q_l, p):
    v_max = 2 * (q_l - 1) ** 2
    counts = [0] * (v_max + 1)
    for a in range(p):
        for lo, hi in sample_intervals(q_l, p, a, v_max):
            for v in range(lo, hi + 1):
                counts[v] += 1
    assert counts == [1] * (v_max + 1)


def test_repeated_intervals_agree_with_the_relation(q_l=61, p=19):
    """The periodic table is what lets the circuit avoid a modular reduction block entirely."""
    v_max = 2 * (q_l - 1) ** 2
    for a in range(p):
        intervals = sample_intervals(q_l, p, a, v_max)
        for v in range(0, v_max + 1, 37):  # a stride, so this stays a test and not a sweep
            in_bucket = any(lo <= v <= hi for lo, hi in intervals)
            assert in_bucket == (round_half_up(v * p, q_l) % p == a)


def test_single_period_needs_few_comparators():
    """The reason the accumulator is reduced at every step rather than compared wide: the
    unreduced table needs one interval per period, which for this instance is hundreds."""
    q_l, p = 61, 19
    v_max = 2 * (q_l - 1) ** 2
    single = sum(len(sample_intervals(q_l, p, a)) for a in range(p))
    repeated = sum(len(sample_intervals(q_l, p, a, v_max)) for a in range(p))
    # p intervals, plus one more because a = 0 is the union of two.
    assert single == p + 1, single
    assert repeated > 100 * single, (single, repeated)
