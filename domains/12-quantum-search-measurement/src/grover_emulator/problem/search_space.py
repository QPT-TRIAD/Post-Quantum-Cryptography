"""The search space, and the closed form every measurement is compared against.

This module is pure data and pure arithmetic. It knows nothing about circuits, which is deliberate:
the closed form here is the *theory oracle* for the whole project, and a theory oracle that shares
code with the thing it is checking is not an oracle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

__all__ = ["SearchSpace", "theoretical_optimal_iterations"]


def theoretical_optimal_iterations(n_items: int, n_marked: int) -> int:
    """``floor(pi/4 * sqrt(N/M))`` — the textbook Grover optimum.

    Args:
        n_items: the size of the search space, ``N``.
        n_marked: the number of marked items, ``M``.

    Returns:
        The textbook count: the number of whole iterations that fit before the rotated angle
        ``(2k + 1) * theta`` reaches ``pi/2``, computed with the small-angle approximation
        ``theta ~ sqrt(M/N)``. It is *not* guaranteed to be the iteration at which the success
        probability is closest to 1. The exact angle is ``asin(sqrt(M/N)) > sqrt(M/N)``, so the
        true maximiser can be one lower whenever an integer falls between the two: ``N = 128``,
        ``M = 19`` returns 2 (``p = 0.8435``) while ``k = 1`` gives ``p = 0.8595``. At ``M = 1``
        — the QLWR case — the two agree at every width this project simulates. For the measured
        peak of the closed form itself use :meth:`SearchSpace.first_peak_iteration`.

    Raises:
        ValueError: if ``M`` is not in ``[1, N]``.

    This is a *count*, not a probability, and it is only optimal for an unstructured search with a
    known ``M``. That assumption is exactly what the structural probes exist to test, so a run that
    deviates from this number is a finding rather than a bug — see
    :mod:`grover_emulator.analysis.success_probability`.
    """
    if not 1 <= n_marked <= n_items:
        raise ValueError(f"need 1 <= M <= N, got M={n_marked}, N={n_items}")
    return int(math.floor((math.pi / 4.0) * math.sqrt(n_items / n_marked)))


@dataclass(frozen=True, slots=True)
class SearchSpace:
    """A search register of ``n_qubits`` and the set of basis states that are marked.

    The marked set is stored as the concrete set of integers it is, never as a predicate plus a
    count. Every downstream consumer — the truth-table lowering, the probe validation, the success
    curve's ``M`` — reads the same frozen object, so the ``M`` in the closed form and the ``M`` the
    circuit implements cannot drift apart.
    """

    n_qubits: int
    marked_items: frozenset[int]

    def __post_init__(self) -> None:
        if self.n_qubits < 1:
            raise ValueError(f"n_qubits must be >= 1, got {self.n_qubits}")
        n = 1 << self.n_qubits
        if not self.marked_items:
            raise ValueError("the marked set is empty; Grover has nothing to amplify")
        if len(self.marked_items) >= n:
            raise ValueError(
                f"the marked set covers all {n} basis states; Grover has nothing to search for"
            )
        bad = [x for x in self.marked_items if not 0 <= x < n]
        if bad:
            raise ValueError(
                f"{len(bad)} marked item(s) outside 0..{n - 1}, e.g. {bad[0]}"
            )

    # -- the two numbers the closed form needs ---------------------------------------------

    @property
    def n_items(self) -> int:
        """``N`` — the size of the search space."""
        return 1 << self.n_qubits

    @property
    def n_marked(self) -> int:
        """``M`` — the number of marked items."""
        return len(self.marked_items)

    @property
    def marked_fraction(self) -> float:
        return self.n_marked / self.n_items

    # -- the closed form ---------------------------------------------------------------------

    @property
    def theta(self) -> float:
        """``arcsin(sqrt(M/N))`` — the Grover rotation angle."""
        return math.asin(math.sqrt(self.marked_fraction))

    @property
    def optimal_iterations(self) -> int:
        return theoretical_optimal_iterations(self.n_items, self.n_marked)

    def success_probability(self, iterations: int) -> float:
        """``sin^2((2k+1) * theta)`` — the exact success probability after ``k`` iterations.

        Exact for an unstructured search that starts from a uniform superposition and applies the
        standard diffuser. It is *not* exact for a search whose oracle has structure, which is why
        a measured curve that departs from this is treated as a finding.
        """
        if iterations < 0:
            raise ValueError(f"iterations must be >= 0, got {iterations}")
        return math.sin((2 * iterations + 1) * self.theta) ** 2

    def first_peak_iteration(self, max_iterations: int) -> int | None:
        """The first ``k >= 1`` at which the closed form stops rising, or None if it never does.

        Returns None rather than raising when the curve is monotone across the sampled window.
        The upstream code this mirrors used ``next(...)`` with no default and raised
        ``StopIteration`` whenever ``M = 0`` or the window was too short to contain the peak; a
        missing peak is a fact about the window, and it is reported as one.
        """
        best: int | None = None
        previous = self.success_probability(0)
        for k in range(1, max_iterations + 1):
            current = self.success_probability(k)
            if current < previous:
                best = k - 1
                break
            previous = current
        return best
