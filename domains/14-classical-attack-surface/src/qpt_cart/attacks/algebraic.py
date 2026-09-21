"""Algebraic attacks: write the primitive as polynomial equations over F_2 and solve them.

This is the attack family the record's security estimate for the key map rests on and never runs:
its ``n = 256`` figures (385.8 / 378.2 / 148.8 classical bits for "F alone", Mode B, Mode A) come
from a degree-of-regularity formula evaluated on paper, in a table that is hard-coded. Here the
system is actually built and handed to a Groebner-basis engine — SageMath's PolyBoRi, the standard
tool for Boolean polynomial systems — and the time it takes is measured as ``n`` grows.

**The two formulations, as the record models them.**

* Mode A, linear handle ``Z = r + c*s``: ``r`` is a *linear* function of ``s``, so it is
  substituted away. ``n`` unknowns, ``2n + E`` quadratic equations — heavily over-determined, which
  is why the record scores Mode A a hundred-odd bits below Mode B.
* Mode B, power handle ``Z = r^7 + c*s``: ``r^7 = r * r^2 * r^4`` and squaring is linear over F_2,
  so each handle bit is a *cubic* in the bits of ``r``. ``2n`` unknowns, ``2n + E`` quadratics plus
  ``n`` cubics.

**Work is wall-clock here**, because the engine exposes no operation count. The time reported is
the Groebner computation alone; building the system is timed separately and not charged to the
attacker. The engine runs in a child process so a budget can be enforced — a Groebner computation
cannot be interrupted politely — and a run that exceeds its budget is recorded as not finished,
which is a statement about the budget and not about the primitive.

The Gaussian-elimination attack on the linear control lives here too: it is the degenerate
algebraic attack (degree one), and it is what a shortcut looks like when there is one.
"""

from __future__ import annotations

import multiprocessing
import time

from ..primitives.controls import LinearMapControl
from ..primitives.keymap import HandleMode, KeyMapScheme, Opening, Transcript
from .base import AttackResult

__all__ = ["groebner_keymap", "gaussian_preimage", "sage_available", "boolean_system"]


def sage_available() -> bool:
    try:
        import sage.all  # noqa: F401
        return True
    except Exception:
        return False


# -- the linear control ----------------------------------------------------------------------------


def gaussian_preimage(control: LinearMapControl, public: int, *, seed: int = 0) -> AttackResult:
    """Solve ``A x = y`` over F_2. Work is counted in row XORs — ``O(n^2)`` of them, each ``O(n)``."""
    began, operations = time.perf_counter(), 0
    n = control.n
    pivots: dict[int, int] = {}                         # leading bit -> augmented row (bit n = rhs)
    for i, row in enumerate(control.rows):
        vec = row | (((public >> i) & 1) << n)
        while vec & ((1 << n) - 1):
            top = (vec & ((1 << n) - 1)).bit_length() - 1
            if top not in pivots:
                pivots[top] = vec
                break
            vec ^= pivots[top]
            operations += 1
    x = 0
    for top in sorted(pivots):
        vec = pivots[top]
        operations += 1
        if ((vec >> n) & 1) ^ ((vec & x & ~(1 << top) & ((1 << n) - 1)).bit_count() & 1):
            x |= 1 << top
    ok = control.evaluate(x) == public
    return AttackResult(
        attack="gaussian_elimination", primitive="control/linear_map", size=n, seed=seed, success=ok,
        verified=ok, work=float(operations * n), work_unit="bit operations (row XORs x n)",
        seconds=time.perf_counter() - began, detail={"row_xors": operations},
    )


# -- the key map as a Boolean polynomial system ----------------------------------------------------


def _field_product(field, a, b, zero):
    """Coordinates of ``a*b`` in GF(2^n) when ``a``, ``b`` are vectors of Boolean polynomials."""
    n = field.n
    out = [zero] * n
    for i in range(n):
        for j in range(n):
            basis = field.mul(1 << i, 1 << j)
            if basis:
                term = a[i] * b[j]
                for k in range(n):
                    if (basis >> k) & 1:
                        out[k] = out[k] + term
    return out


def _apply_linear(rows, vector, zero):
    out = []
    for mask in rows:
        acc = zero
        for j, value in enumerate(vector):
            if (mask >> j) & 1:
                acc = acc + value
        out.append(acc)
    return out


def boolean_system(scheme: KeyMapScheme, transcript: Transcript):
    """``(ring, equations, s-polynomials, r-polynomials)`` whose common zeros are the valid openings."""
    from sage.all import BooleanPolynomialRing

    n, field = scheme.n, scheme.field
    c_rows = field.mul_matrix(transcript.challenge)
    z_bits = [(transcript.handle >> i) & 1 for i in range(n)]

    if scheme.mode is HandleMode.A:
        ring = BooleanPolynomialRing(n, [f"s{i}" for i in range(n)])
        zero, s = ring.zero(), list(ring.gens())
        cs = _apply_linear(c_rows, s, zero)
        r = [cs[i] + z_bits[i] for i in range(n)]                 # r = Z + c*s: no new unknowns
        equations = []
    else:
        ring = BooleanPolynomialRing(2 * n, [f"s{i}" for i in range(n)] + [f"r{i}" for i in range(n)])
        zero, gens = ring.zero(), list(ring.gens())
        s, r = gens[:n], gens[n:]
        squares = [field.mul(1 << j, 1 << j) for j in range(n)]    # (X^j)^2: squaring is linear
        square_rows = [sum(((squares[j] >> i) & 1) << j for j in range(n)) for i in range(n)]
        r2 = _apply_linear(square_rows, r, zero)
        r4 = _apply_linear(square_rows, r2, zero)
        r7 = _field_product(field, _field_product(field, r, r2, zero), r4, zero)
        cs = _apply_linear(c_rows, s, zero)
        equations = [r7[i] + cs[i] + z_bits[i] for i in range(n)]  # n cubic handle equations

    x = s + r
    products = {(i, j): x[i] * x[j] for i in range(2 * n) for j in range(i + 1, 2 * n)}
    qmap = scheme.map
    for e in range(qmap.m_eqs):
        acc = zero + (qmap.const[e] ^ ((transcript.public_key >> e) & 1))
        for k in range(2 * n):
            if (qmap.lin[e] >> k) & 1:
                acc = acc + x[k]
            row = qmap.rows[e][k]
            while row:
                low = row & -row
                acc = acc + products[(k, low.bit_length() - 1)]
                row ^= low
        equations.append(acc)
    return ring, equations, s, r


MEMORY_CAP_BYTES = 6 << 30
"""Address-space cap on the Groebner child. A Boolean Groebner basis can grow without warning, and
an attack that takes the desktop down with it measures nothing; a run that hits the cap is recorded
as not finished, with the cap named as the reason."""


def _groebner_worker(scheme: KeyMapScheme, transcript: Transcript, queue) -> None:
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_CAP_BYTES, MEMORY_CAP_BYTES))
        built = time.perf_counter()
        ring, equations, s, r = boolean_system(scheme, transcript)
        build_seconds = time.perf_counter() - built
        began = time.perf_counter()
        basis = ring.ideal(equations).groebner_basis()
        seconds = time.perf_counter() - began
        openings = []
        if list(basis) != [ring.one()]:
            for point in ring.ideal(list(basis)).variety():
                values = {str(k): int(v) for k, v in point.items()}
                s_val = sum(values.get(f"s{i}", 0) << i for i in range(scheme.n))
                if scheme.mode is HandleMode.A:
                    r_val = transcript.handle ^ scheme.field.mul(transcript.challenge, s_val)
                else:
                    r_val = sum(values.get(f"r{i}", 0) << i for i in range(scheme.n))
                openings.append((s_val, r_val))
        queue.put({"seconds": seconds, "build_seconds": build_seconds, "openings": openings,
                   "basis_size": len(basis), "unknowns": ring.ngens(),
                   "equations": len(equations),
                   "max_degree": max(int(f.degree()) for f in equations)})
    except Exception as error:                                      # pragma: no cover - reported
        queue.put({"error": f"{type(error).__name__}: {error}"})


def groebner_keymap(scheme: KeyMapScheme, transcript: Transcript, *, seed: int = 0,
                    max_seconds: float = 300.0) -> AttackResult:
    primitive = f"keymap/mode{scheme.mode.value}"
    if not sage_available():
        return AttackResult(attack="groebner", primitive=primitive, size=scheme.n, seed=seed,
                            success=False, work=None, work_unit="seconds", seconds=0.0,
                            not_run_reason="SageMath is not importable in this interpreter",
                            provenance="not run")
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    process = context.Process(target=_groebner_worker, args=(scheme, transcript, queue))
    began = time.perf_counter()
    process.start()
    try:
        outcome = queue.get(timeout=max_seconds)
    except Exception:
        outcome = None
    if process.is_alive():
        process.kill()
    process.join()
    if outcome is None or "error" in outcome:
        reason = (f"budget of {max_seconds}s exhausted" if outcome is None else outcome["error"])
        return AttackResult(attack="groebner", primitive=primitive, size=scheme.n, seed=seed,
                            success=False, work=None, work_unit="seconds",
                            seconds=time.perf_counter() - began, not_run_reason=reason,
                            provenance="not run" if outcome is None else "measured")
    valid = [Opening(s, r) for s, r in outcome["openings"] if scheme.verify(transcript, Opening(s, r))]
    ok = bool(valid)
    return AttackResult(
        attack="groebner", primitive=primitive, size=scheme.n, seed=seed, success=ok, verified=ok,
        work=None, work_unit="seconds (Groebner basis, PolyBoRi)", seconds=outcome["seconds"],
        detail={k: outcome[k] for k in ("build_seconds", "basis_size", "unknowns", "equations",
                                        "max_degree")} | {"openings_found": len(valid)},
        not_run_reason=None if ok else "the basis had no opening that verifies",
    )
