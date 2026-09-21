"""The reduction engines, and the one invariant that makes their output usable.

A reduction engine takes a basis and returns a basis. Every engine in this project can do that, and
every one of them can return a basis of a *different lattice* while doing it. fpylll and G6K each
return something self-consistent: still square, still integer, still full rank, still reducing
perfectly well, and with a root-Hermite factor that is plausible to four decimal places. No
per-engine test can see the difference, because a per-engine test compares an engine against its own
conventions — the same reason the sibling Grover project's qubit-ordering defect survived a whole
green suite: every layer was individually correct, and the error lived only in the boundary between
two of them.

So the boundary check lives here, in the layer that crosses it, and it is not a proxy. It solves
``U @ before == after`` exactly over the rationals and requires ``U`` to be integral with
``|det U| == 1``, which *is* the definition of "the same lattice". A determinant comparison, a
dimension check, or a norm-plausibility check would each pass on a basis that spans a different
lattice; the unimodularity of the transform is the property itself.

It also runs *inside* ``reduce``, not beside it. ``ReductionEngine.reduce`` is a template method: it
copies the caller's basis, reduces the copy, checks the transform, and only then builds a result.
An engine subclass supplies a tour loop and nothing else, so a new engine cannot forget the check.
The two engines below are the first two of a series, and a check that has to be remembered by each
new author is a check that will eventually be absent.

Three measured facts about the libraries this wraps, each of which shaped the code:

* ``BKZ.reduction`` and G6K's ``Siever`` both mutate the matrix they are handed, in place. If this
  module reduced the caller's own matrix, the caller's "before" would *be* the "after", and the
  preservation check would compare a matrix against itself and pass for every input. The copy is
  what makes the check non-vacuous, not a defensive habit.
* fplll accepts a block size larger than the dimension without complaint (measured: 41 on a 40-row
  basis raises nothing). A silently clamped block size would be recorded as a run at the requested
  size. The bound is enforced here, where it can be reported.
* ``SVP.shortest_vector`` aborts the process in this build when called with its own defaults: the
  default ``pruning=True`` reaches fplll's external-enumeration path and exits on a pruning-vector
  mismatch. Enumeration is used as an oracle in the tests, so it is always called with
  ``method="proved"``. Nothing in this module calls it.
"""

from __future__ import annotations

import abc
import math
import resource
import sys
import time
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable, Sequence

from qlwr_lattice_stress.protocols import MEASURED, ReducedBasisResult
from qlwr_lattice_stress.utils.seeding import RunSeeds, derive_seed

__all__ = [
    "CONVERGENCE_EPSILON_BITS",
    "DEFAULT_MAX_TOURS",
    "INTERPRETER_BASELINE_BYTES",
    "LatticePreservationError",
    "MIN_BLOCK_SIZE",
    "RamBudgetExceeded",
    "ReductionEngine",
    "TourOutcome",
    "UNAVAILABLE_VERSION",
    "assert_same_lattice",
    "matrix_rows",
    "peak_rss_bytes_upper_bound",
]

#: The smallest block size at which a tour does any work. At block size 2 a BKZ tour reproduces
#: what LLL already did, so a run at block size 1 or 2 would be recorded as a reduction and be a
#: no-op — the "unreduced but converged" case that ``converged`` exists to distinguish.
MIN_BLOCK_SIZE = 2

#: Cap on tours per ``reduce`` call, matching fplll's own default ``max_loops``. Convergence
#: normally stops the loop after one or two tours; the cap is what makes a non-converging instance
#: terminate at all, and hitting it is recorded as ``converged=False`` rather than hidden.
DEFAULT_MAX_TOURS = 8

#: A tour that shortens ``b_0`` by less than this many bits is treated as convergence. Measured for
#: scale: a real tour at block size 40 on a 40-dimensional q-ary basis shortens ``b_0`` by 0.22 bits,
#: while a tour at block size 2 shortens it by 0.000000 bits.
CONVERGENCE_EPSILON_BITS = 1e-3

#: Reported by :meth:`ReductionEngine.version` when the engine's library cannot be imported. Never a
#: fabricated version string: a result that claims a version it could not read is worse than one
#: that says it does not know.
UNAVAILABLE_VERSION = "unavailable"

#: The interpreter's own footprint, present in every measurement this project has taken and reported
#: as a process peak: the hardware calibration's cumulative peak was <=97 MiB with all twelve
#: configurations inside one process, and the sieving sweep never went below ~90 MiB. Included in
#: both engines' estimates because the budget question ("will this run fit?") is about the process,
#: not about one data structure inside it. 100 MiB is above every baseline measured so far.
INTERPRETER_BASELINE_BYTES = 100 * (1 << 20)


class LatticePreservationError(AssertionError):
    """A reduction returned a basis that spans a different lattice.

    An ``AssertionError`` so that a caller who reaches for ``assert`` semantics still catches it,
    and a named type so that this specific failure — which invalidates every number derived from
    the run — cannot be swallowed by a ``except AssertionError`` written for something else.
    """


class RamBudgetExceeded(RuntimeError):
    """A block size's estimated footprint exceeds the budget it was checked against.

    Raised *before* the run, never after: a run that is killed at the budget leaves a partial basis
    and a wall-clock time that looks like a completed measurement.
    """


@dataclass(frozen=True, slots=True)
class TourOutcome:
    """What a tour loop did, before it is folded into a result.

    Carried as a separate type so that ``n_tours`` and ``converged`` cannot be dropped on the way
    from the loop to the result: they are the difference between a result and a bound on how hard
    the instance might be, and the two look identical in a basis.
    """

    n_tours: int
    converged: bool
    threads: int


def matrix_rows(matrix: Any) -> list[list[int]]:
    """The integer rows of ``matrix``, whatever representation it arrives in.

    Accepts an fpylll ``IntegerMatrix`` (anything exposing ``nrows``/``ncols`` and tuple indexing),
    a nested sequence, or a numpy array. Rows are *copied*: this is used to snapshot a basis before
    a library mutates it, so sharing storage would defeat the purpose.
    """
    if hasattr(matrix, "nrows") and hasattr(matrix, "ncols") and hasattr(matrix, "__getitem__"):
        return [[int(matrix[i, j]) for j in range(matrix.ncols)] for i in range(matrix.nrows)]
    if hasattr(matrix, "tolist"):
        matrix = matrix.tolist()
    return [[int(value) for value in row] for row in matrix]


def _check_square(rows: list[list[int]], what: str) -> int:
    if not rows:
        raise ValueError(f"{what} has no rows; a lattice basis is a non-empty square matrix")
    width = len(rows[0])
    for index, row in enumerate(rows):
        if len(row) != width:
            raise ValueError(f"{what} row {index} has {len(row)} entries, expected {width}")
    if width != len(rows):
        raise ValueError(
            f"{what} is {len(rows)}x{width}; a lattice basis is square, and a non-square pair "
            "cannot be tested for spanning the same lattice by a square transform"
        )
    return len(rows)


def _solve_transform(before: list[list[int]], after: list[list[int]]) -> list[list[Fraction]] | None:
    """The unique ``U`` with ``U @ before == after``, over the rationals, or ``None`` if singular.

    Substituting ``U`` back into ``U @ before == after`` gives, for each row ``i`` of ``U``,
    ``before^T @ U[i] == after[i]``. All rows share the coefficient matrix ``before^T``, so the
    augmented system ``[before^T | after^T]`` is reduced once and the transform read off it: after
    elimination the right block is ``(before^T)^-1 @ after^T == U^T``, hence ``U[i][j]`` is entry
    ``(j, i)`` of the reduced right block.

    Exact rational arithmetic throughout, and deliberately so: the whole point of the check is to
    be right where a floating-point comparison would be plausibly wrong. Measured cost at
    ``q_l = 2^16``: 0.02 s at dimension 40, 0.07 s at 60, 0.31 s at 100 — against reductions that
    cost 58.6 s for ``d=160, beta=40`` and 193 s for sieving at block size 90.
    """
    n = len(before)
    augmented = [
        [Fraction(before[k][column]) for k in range(n)]
        + [Fraction(after[k][column]) for k in range(n)]
        for column in range(n)
    ]
    for pivot_column in range(n):
        pivot_row = next(
            (r for r in range(pivot_column, n) if augmented[r][pivot_column] != 0), None
        )
        if pivot_row is None:
            return None
        if pivot_row != pivot_column:
            augmented[pivot_column], augmented[pivot_row] = (
                augmented[pivot_row],
                augmented[pivot_column],
            )
        pivot = augmented[pivot_column][pivot_column]
        for row in range(n):
            if row != pivot_column and augmented[row][pivot_column] != 0:
                factor = augmented[row][pivot_column] / pivot
                augmented[row] = [
                    augmented[row][c] - factor * augmented[pivot_column][c] for c in range(2 * n)
                ]
    return [
        [augmented[j][n + i] / augmented[j][j] for j in range(n)] for i in range(n)
    ]


def _multiply(
    transform: Sequence[Sequence[Fraction]], rows: Sequence[Sequence[int]]
) -> list[list[Fraction]]:
    """``transform @ rows``, exactly.

    Exact for a transform that is *not* integral, which is the case it most needs to be valid for:
    a truncating cast would turn a correct solution into a failed substitution and report a
    non-existent solver defect instead of the lattice change that is actually there.
    """
    return [
        [
            sum((coefficient * rows[k][column] for k, coefficient in enumerate(row)), Fraction(0))
            for column in range(len(rows[0]))
        ]
        for row in transform
    ]


def _det_abs(matrix: Sequence[Sequence[Fraction]]) -> Fraction:
    """``|det(matrix)|`` exactly, by rational elimination."""
    n = len(matrix)
    work = [list(row) for row in matrix]
    determinant = Fraction(1)
    for column in range(n):
        pivot_row = next((r for r in range(column, n) if work[r][column] != 0), None)
        if pivot_row is None:
            return Fraction(0)
        if pivot_row != column:
            work[column], work[pivot_row] = work[pivot_row], work[column]
            determinant = -determinant
        determinant *= work[column][column]
        for row in range(column + 1, n):
            if work[row][column] != 0:
                factor = work[row][column] / work[column][column]
                work[row] = [work[row][c] - factor * work[column][c] for c in range(n)]
    return abs(determinant)


def assert_same_lattice(before: Any, after: Any, *, context: str = "") -> None:
    """Assert that ``after`` spans exactly the lattice ``before`` spans. Raise if it does not.

    Solves ``U @ before == after`` over the rationals, then requires ``U`` to be integral with
    ``|det U| == 1``. That is the definition of the two bases generating the same lattice — not a
    determinant comparison (which a scaled basis would pass under a signed permutation), and not a
    norm or dimension check (which any basis would pass).

    Every engine in this package runs this before returning a result, which is why the failure is
    raised here rather than returned as a status: a caller that ignored a returned ``False`` would
    publish a plausible Hermite factor for a lattice nobody asked about.

    ``context`` is free text (the engine name, block size, dimension) prefixed to the message, so
    that a failure in a sweep of two hundred runs says which run it came from.

    Raises:
        ValueError: if either argument is not a non-empty square matrix of integers.
        LatticePreservationError: if the transform is not integral, or is integral but not
            unimodular, or if ``before`` is singular and no transform exists.
    """
    where = f"{context}: " if context else ""
    before_rows = matrix_rows(before)
    after_rows = matrix_rows(after)
    dimension = _check_square(before_rows, "before")
    _check_square(after_rows, "after")
    if len(after_rows) != dimension:
        raise ValueError(
            f"{where}before is {dimension}-dimensional and after is {len(after_rows)}-dimensional; "
            "lattice preservation is only defined between bases of one lattice"
        )

    if before_rows == after_rows:
        # The identity transform is unimodular, so there is nothing to solve. This is the whole
        # behaviour of a converged run at a small block size, and it is frequent enough to be worth
        # the short circuit rather than a 0.02 s elimination per call.
        return

    transform = _solve_transform(before_rows, after_rows)
    if transform is None:
        raise LatticePreservationError(
            f"{where}the input basis is singular, so no transform exists and the output cannot be "
            "compared against it. A singular basis does not span a lattice at all, so this is a "
            "defect in what the engine was given or in what it returned."
        )

    # Substituting the transform back is an exact integer multiply, and it is checked before the
    # integrality test below for a specific reason: if the elimination itself were wrong, every
    # conclusion drawn from it — including "the lattice changed" — would be wrong too, and this is
    # the only place that can tell those two failures apart. A solver defect must not be reported
    # as a lattice defect, because the response to each is different.
    if _multiply(transform, before_rows) != after_rows:
        raise LatticePreservationError(
            f"{where}the exact solver returned a transform that does not satisfy U @ before == "
            "after. The elimination is unsound; treat this as a defect in the checker itself, not "
            "as a benign result or as evidence about the engine."
        )

    for i, row in enumerate(transform):
        for j, coefficient in enumerate(row):
            if coefficient.denominator != 1:
                raise LatticePreservationError(
                    f"{where}the returned basis is not the lattice spanned by the input: the "
                    f"transform row {i} entry {j} is {coefficient}, not an integer. The change of "
                    "basis is not a change of basis, and every number derived from this run — "
                    "Hermite factor included — describes a lattice that was not the one attacked."
                )

    determinant = _det_abs(transform)
    if determinant != 1:
        raise LatticePreservationError(
            f"{where}the returned basis spans a sublattice or superlattice of the input: the "
            f"transform is integral but |det U| == {determinant}, and lattice equality requires "
            "exactly 1."
        )


def peak_rss_bytes_upper_bound() -> int:
    """The process's peak resident set size, in bytes, as an **upper bound**.

    ``ru_maxrss`` is monotonic per process and process-wide, so this is a ceiling on everything the
    process has done so far, not the footprint of the run that just finished. The hardware
    calibration measured per-configuration deltas this way and got noise — a later configuration
    reporting *less* memory than an earlier one, which is physically impossible — because twelve
    configurations shared one process. The field in the result is named for what it is.

    Linux and the BSDs report KiB here and macOS reports bytes; the scale is applied explicitly
    rather than assumed, because a silent factor of 1024 in a memory number is exactly the kind of
    error that only shows up in a report somebody has already quoted.
    """
    rusage = resource.getrusage(resource.RUSAGE_SELF)
    scale = 1 if sys.platform == "darwin" else 1024
    return int(rusage.ru_maxrss) * scale


def _first_row_norm_squared(matrix: Any) -> int:
    """``||b_0||^2`` exactly, from the integer matrix itself rather than from its Gram-Schmidt.

    Exactness matters here beyond hygiene: this value drives the convergence decision, and a
    floating-point norm that jittered in the last bits would make a stall look like an improvement
    and vice versa.
    """
    return sum(int(matrix[0, j]) ** 2 for j in range(matrix.ncols))


def _reject_unknown_kwargs(kwargs: dict[str, Any], allowed: Sequence[str], engine: str) -> None:
    """Refuse keyword arguments the engine does not implement.

    Silently accepting them is the failure this project keeps designing against: a caller who asks
    for a dual-mode reduction and is given a primal-mode one has no way to see it in the result,
    and the report will say the dual attack was measured.
    """
    unknown = sorted(set(kwargs) - set(allowed))
    if unknown:
        supported = ", ".join(allowed) if allowed else "none"
        raise TypeError(
            f"{engine} does not take the keyword argument(s) {', '.join(unknown)}; it supports "
            f"{supported}. Ignoring them would silently run something other than what was asked "
            "for, and the result would not record the difference."
        )


def _integer_matrix(rows: list[list[int]]) -> Any:
    """An fpylll ``IntegerMatrix`` holding ``rows``, with arbitrary-precision entries.

    ``int_type="mpz"`` rather than the machine-word type: the project's exactness budget covers the
    *inner product* at production parameters, not the intermediates a reduction produces, whose
    magnitudes are bounded by the lattice determinant (``q_l^m``, 320 bits at ``d=40`` and far
    beyond a machine word at the dimensions a scaled sweep reaches).
    """
    from fpylll import IntegerMatrix

    matrix = IntegerMatrix(len(rows), len(rows[0]), int_type="mpz")
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            matrix[i, j] = int(value)
    return matrix


def lll_reduce(matrix: Any) -> None:
    """LLL-reduce ``matrix`` in place, using the library's default parameters.

    Called by ``reduce`` before the tour loop for both engines, for the same reason in both cases:
    a tour's behaviour is defined relative to a reduced basis, so starting from a raw q-ary basis
    would make the two engines differ in ways that have nothing to do with sieving versus
    enumeration. It is a unimodular transform, so it cannot change which lattice is being reduced —
    and the preservation check would catch it if it did.
    """
    from fpylll import LLL

    LLL.reduction(matrix)


def root_hermite_factor(matrix: Any) -> float | None:
    """``(||b_0|| / det(L)^(1/d))^(1/d)`` for the basis as it stands, or ``None`` if not computable.

    The *root* Hermite factor, i.e. ``delta_0`` — the same quantity as
    :func:`~qlwr_lattice_stress.analysis.hermite_factor.achieved_root_hermite_factor`, and about
    1.01-1.02 for LLL/BKZ output. This function once returned the un-rooted ``||b_0|| / det^(1/d)``
    under this name (1.68 where the rooted value is 1.013, at dimension 40), and the number reached
    ``metrics.json`` and the report's measured section as a "root Hermite factor".

    Read from fpylll's own Gram-Schmidt data rather than recomputed from the instance, so that the
    number describes the basis that was actually returned. ``None`` rather than a substituted
    value when it cannot be computed: a fabricated Hermite factor is indistinguishable downstream
    from a measured one, which is the failure the whole provenance field exists to prevent.
    """
    from fpylll import GSO

    try:
        dimension = matrix.nrows
        gram_schmidt = GSO.Mat(matrix, float_type="double")
        gram_schmidt.update_gso()
        squared_norms = [gram_schmidt.get_r(i, i) for i in range(dimension)]
        if any(value is None or value <= 0.0 for value in squared_norms):
            return None
        # Logs, not the product: det(L) is q_l^m, which overflows a double long before the
        # dimensions this project sweeps. The sum of logs is compared against an analytic
        # determinant in the tests and agrees to 8e-16 relative.
        log_det = 0.5 * math.fsum(math.log(value) for value in squared_norms)
        log_hermite_factor = 0.5 * math.log(squared_norms[0]) - log_det / dimension
        return float(math.exp(log_hermite_factor / dimension))
    except Exception:
        return None


class ReductionEngine(abc.ABC):
    """One way of reducing a basis, behind a uniform interface and one shared invariant.

    Subclasses supply three things — availability, a version string, a memory model — and a tour
    loop. They do not supply ``reduce``: the base class runs it as a template so that the input
    copy, the block-size bounds and :func:`assert_same_lattice` are applied to every engine that
    will ever exist, including ones written later by someone who has not read this file.

    Attributes:
        name: The engine's identifier, recorded in every result. Two engines that report the same
            ``name`` produce results a reader cannot tell apart.
    """

    name: str = ""

    def __init__(
        self,
        *,
        seed: int = 0,
        seeds: RunSeeds | None = None,
        threads: int | None = None,
        max_tours: int = DEFAULT_MAX_TOURS,
    ) -> None:
        """
        Args:
            seed: Root seed for anything this engine randomises. Seeds are *derived* per call via
                :func:`qlwr_lattice_stress.utils.seeding.derive_seed` rather than consumed in
                sequence, so adding a knob shifts nothing that already had a seed.
            seeds: A :class:`RunSeeds` to derive from, which additionally *records* each derived
                seed so the run can be re-derived from its own results file. Takes precedence over
                ``seed``.
            threads: Threads for the engine's own parallelism. ``None`` means the engine's measured
                default, which is not the same number for every engine.
            max_tours: Cap on tours per reduction. Recorded as ``converged=False`` when hit.
        """
        if seed < 0:
            raise ValueError(f"seed must be non-negative, got {seed}")
        if max_tours < 1:
            raise ValueError(f"max_tours must be at least 1, got {max_tours}")
        if threads is not None and threads < 1:
            raise ValueError(f"threads must be at least 1, got {threads}")
        self.seed = seed
        self.seeds = seeds
        self.max_tours = max_tours
        self.threads = self.default_threads if threads is None else threads

    # -- what a subclass must supply ----------------------------------------------------------

    @property
    @abc.abstractmethod
    def default_threads(self) -> int:
        """The thread count this engine measured best, used when the caller does not choose one."""

    @abc.abstractmethod
    def unavailable_reason(self) -> str | None:
        """Why this engine cannot run in this interpreter, or ``None`` if it can.

        The reason is a sentence naming the import that failed, because it is logged when the
        engine selector falls back and a reader has to be able to tell "not built here" from
        "imported but the extension is broken".
        """

    @abc.abstractmethod
    def version(self) -> str:
        """The engine library's version, or :data:`UNAVAILABLE_VERSION` if it cannot be read."""

    @abc.abstractmethod
    def estimate_memory_bytes(self, block_size: int) -> int:
        """Estimated upper bound on the process footprint of a run at ``block_size``.

        A *model*, not a measurement, and documented as one in each engine. It exists to refuse a
        runaway before it starts, not to set the sweep's ceiling: the measured peak at block size
        90 is 231 MiB against 7.5 GiB available, so what limits this project is wall-clock time.
        """

    @abc.abstractmethod
    def _run_tours(self, matrix: Any, block_size: int, **kwargs: Any) -> TourOutcome:
        """Reduce ``matrix`` in place at ``block_size`` and report what the loop did.

        ``matrix`` is the engine's own copy, already LLL-reduced, and the caller's basis is not
        reachable from here — an engine that mutated its argument would otherwise destroy the
        evidence the preservation check compares against.
        """

    # -- the template -------------------------------------------------------------------------

    def available(self) -> bool:
        """Whether this engine can run here. ``unavailable_reason`` is the single source of truth.

        Evaluated per call rather than cached, deliberately: the tests that check the unavailability
        path replace the module an engine imports, and a cached ``True`` from an earlier call in the
        same process would make that path untestable.
        """
        return self.unavailable_reason() is None

    def reduce(self, basis: Any, block_size: int, **kwargs: Any) -> ReducedBasisResult:
        """Reduce ``basis`` at ``block_size`` and return a measured result.

        The input is not modified: the engine works on a copy, so ``basis`` remains the "before"
        that :func:`assert_same_lattice` compares the result against. ``wall_clock_s`` covers the
        tour loop — the block-size-dependent work — and excludes the LLL preprocessing, which is
        shared between engines and is not what a block-size sweep is measuring.

        Args:
            basis: An fpylll ``IntegerMatrix`` or any nested integer sequence, square and full rank.
            block_size: BKZ block size, from :data:`MIN_BLOCK_SIZE` to the dimension inclusive.
            **kwargs: Engine-specific options. Unknown options raise rather than being ignored.

        Raises:
            RuntimeError: if the engine is not available here.
            ValueError: if the basis is not a non-empty square matrix, or the block size is out of
                range. fplll accepts a block size past the dimension without complaint, so the
                bound is enforced here instead of being trusted to the library.
            LatticePreservationError: if the reduction changed the lattice.
        """
        reason = self.unavailable_reason()
        if reason is not None:
            raise RuntimeError(
                f"engine {self.name!r} cannot run in this interpreter: {reason}. Check "
                "available() before reducing, or select an engine through the selector so that the "
                "substitution is recorded."
            )

        before = matrix_rows(basis)
        dimension = _check_square(before, "basis")
        self._check_block_size(block_size, dimension)

        matrix = _integer_matrix(before)
        lll_reduce(matrix)

        started = time.perf_counter()
        outcome = self._run_tours(matrix, block_size, **kwargs)
        wall_clock_s = time.perf_counter() - started

        after = matrix_rows(matrix)
        assert_same_lattice(
            before,
            after,
            context=f"{self.name} at block size {block_size} on a {dimension}-dimensional basis",
        )

        return ReducedBasisResult(
            basis=matrix,
            block_size=block_size,
            wall_clock_s=wall_clock_s,
            root_hermite_factor=root_hermite_factor(matrix),
            engine=self.name,
            engine_version=self.version(),
            threads=outcome.threads,
            n_tours=outcome.n_tours,
            converged=outcome.converged,
            peak_rss_bytes_upper_bound=peak_rss_bytes_upper_bound(),
            dimension=dimension,
            provenance=MEASURED,
        )

    # -- shared machinery ---------------------------------------------------------------------

    @staticmethod
    def _check_block_size(block_size: int, dimension: int) -> None:
        if isinstance(block_size, bool) or not isinstance(block_size, int):
            raise TypeError(f"block_size must be an int, got {type(block_size).__name__}")
        if block_size < MIN_BLOCK_SIZE:
            raise ValueError(
                f"block size {block_size} is below {MIN_BLOCK_SIZE}; a tour there redoes what LLL "
                "already did, and recording it as a reduction would report the LLL basis as a "
                "reduced one"
            )
        if block_size > dimension:
            raise ValueError(
                f"block size {block_size} exceeds the basis dimension {dimension}. fplll accepts "
                "this without complaint, so it would be recorded as a run at the requested size "
                "while the library was doing something else."
            )

    def _tour_loop(
        self,
        matrix: Any,
        block_size: int,
        run_one_tour: Callable[[int], None],
        max_tours: int,
    ) -> tuple[int, bool]:
        """Run tours until the first vector stops shortening, and report both outcomes.

        Convergence is judged on ``||b_0||``, the quantity the reported root-Hermite factor is
        computed from. A tour that does not shorten it by
        :data:`CONVERGENCE_EPSILON_BITS` bits is the last one: further tours cost real time and
        leave the basis unchanged, and stopping is what makes ``converged`` mean "no further
        progress was available" rather than "the loop was allowed to finish".

        The loop is honest in both directions. A run that stalls at a small block size reports
        ``converged=True`` on a basis that is barely reduced, which is a *result* about the instance
        at that block size; a run that is still improving when ``max_tours`` runs out reports
        ``converged=False``, which is a bound on how hard the instance might be. Without the pair, a
        results file holds two identical-looking bases that mean different things.
        """
        n_tours = 0
        converged = False
        best = _first_row_norm_squared(matrix)
        for _ in range(max_tours):
            run_one_tour(block_size)
            n_tours += 1
            current = _first_row_norm_squared(matrix)
            previous_best = best
            best = min(best, current)
            if best <= 0:
                # A zero first vector means the basis is degenerate, which LLL cannot produce from
                # a valid input and the preservation check rejects. Stop rather than take log2(0).
                converged = True
                break
            improvement_bits = 0.5 * math.log2(previous_best / best)
            if improvement_bits <= CONVERGENCE_EPSILON_BITS:
                converged = True
                break
        return n_tours, converged

    def _seed_for(self, *parts: Any) -> int:
        """A seed for one random draw, derived and — when a :class:`RunSeeds` was supplied — recorded.

        Recorded matters: a pipeline that seeds from a value held only in memory produces a run that
        cannot be re-derived from its own results file, which is the second failure the seeding
        module exists to prevent.
        """
        if self.seeds is not None:
            return self.seeds.derive(self.name, *parts)
        return derive_seed(self.seed, self.name, *parts)
