"""The instance is exact integers — asserted, rather than assumed from how it is usually built.

``qlwr_instance.py`` says it in its module docstring: *"all arithmetic is exact. A float anywhere in
basis construction produces a basis for a different lattice without raising."* Every construction
site in the project passes ``int``s, so the claim has always been true in practice — and nothing
made it true. ``LatticeQLWRInstance`` was a plain dataclass whose ``__post_init__`` checked ranges
and rank but never types, so

    LatticeQLWRInstance(nu=2, q_l=2**16, p=2**8, m=3, secret_s=(1.0, 2.0), base=...)

was accepted, and ``target``, ``public_samples()`` and ``error_vector()`` then came back as Python
``float``s. Nothing raised; the floats were even *correct* at this size. They stop being correct
silently, at the point where a product exceeds ``2^53``, which is the failure the docstring
describes.

Two halves, then. The refusals are what ``src`` must do with a non-integer input; the ones it did
not do were ``xfail(strict=True)`` until ``_require_integer`` was added on 2026-09-20, and pass
now with the markers removed. The properties are what every valid
instance must satisfy — every public derived quantity is an ``int``, in range, and consistent with a
relation recomputed here in ``fractions`` rather than with the instance's own arithmetic.
"""

from __future__ import annotations

import random
from fractions import Fraction

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from qlwr_lattice_stress.problem.normal_form import PivotNotFound, to_normal_form
from qlwr_lattice_stress.problem.qlwr_instance import (
    LatticeQLWRInstance,
    full_column_rank_mod,
)

PRODUCTION_Q = 1 << 16
PRODUCTION_P = 1 << 8

#: Divisor and non-divisor pairs, power-of-two and composite and prime moduli. The non-divisor
#: pairs matter here because their noise bound is *computed* by a scan rather than read off a
#: formula, which is a second code path that could let a non-integer through.
MODULI = [(PRODUCTION_Q, PRODUCTION_P), (1 << 12, 1 << 4), (61, 19), (105, 7), (251, 2)]

#: Historical: the defect as it stood before it was fixed on 2026-09-20, kept as the record of what
#: the tests below were written against. It was the xfail reason; nothing reads it now.
NO_TYPE_GUARD = (
    "src/qlwr_lattice_stress/problem/qlwr_instance.py:206-232 — LatticeQLWRInstance.__post_init__ "
    "validates ranges, lengths and rank but never types, so a non-int is accepted whenever it "
    "compares like one. Reproduce: LatticeQLWRInstance(nu=2, q_l=2**16, p=2**8, m=3, "
    "secret_s=(1.0, 2.0), base=((1,0),(0,1),(3,5))).target == (0.0, 0.0, 0.0) — floats."
)

BASE = ((1, 0), (0, 1), (3, 5))
GOOD = dict(nu=2, q_l=PRODUCTION_Q, p=PRODUCTION_P, m=3, secret_s=(1, 2), base=BASE)


def is_exact_integer(value) -> bool:
    """A Python ``int`` or a numpy integer — and not ``bool``, which is an ``int`` only by
    inheritance and means something else wherever it appears."""
    if isinstance(value, (bool, np.bool_)):
        return False
    return isinstance(value, (int, np.integer))


def make_instance(nu, m, q, p, seed, *, tries=200) -> LatticeQLWRInstance | None:
    """An instance from plain ``random``, or ``None`` if no full-rank base turned up.

    ``None`` rather than a loop without end: at ``m == nu`` over a modulus with several small prime
    factors a full-rank draw is not rare, but it is not certain either, and a property test should
    discard the draw rather than hang on it.
    """
    rng = random.Random(seed)
    for _ in range(tries):
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            return LatticeQLWRInstance(
                nu=nu, q_l=q, p=p, m=m,
                secret_s=tuple(rng.randrange(q) for _ in range(nu)), base=base, seed=seed,
            )
    return None


@st.composite
def valid_instances(draw):
    nu = draw(st.integers(min_value=1, max_value=5))
    m = draw(st.integers(min_value=nu, max_value=nu + 8))
    q, p = draw(st.sampled_from(MODULI))
    seed = draw(st.integers(min_value=0, max_value=2**32 - 1))
    instance = make_instance(nu, m, q, p, seed)
    assume(instance is not None)
    return instance


# ---------------------------------------------------------------------------------------------
# the checks are themselves checked
# ---------------------------------------------------------------------------------------------


def test_the_integer_predicate_rejects_what_it_exists_to_reject():
    """Non-vacuity. Every property below leans on this predicate; one that accepted ``1.0`` would
    make them all pass on the defect they are written for."""
    assert is_exact_integer(3) and is_exact_integer(-(2**80)) and is_exact_integer(np.int64(3))
    for impostor in (1.0, np.float64(1.0), True, False, np.bool_(True), Fraction(1), "1", None):
        assert not is_exact_integer(impostor), repr(impostor)


def test_the_baseline_used_by_the_refusal_tests_is_itself_accepted():
    """Each refusal test changes one field of ``GOOD``. If ``GOOD`` were refused, every one of them
    would pass for a reason that has nothing to do with the field it changed."""
    instance = LatticeQLWRInstance(**GOOD)
    instance.check_relation()
    assert all(type(v) is int for v in instance.target)


# ---------------------------------------------------------------------------------------------
# refusals
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "override",
    [
        # Accepted today: the value compares and multiplies like the integer it equals.
        pytest.param({"secret_s": (1.0, 2.0)}, id="float-secret-integral"),
        pytest.param({"secret_s": (1.5, 2.0)}, id="float-secret-fractional"),
        pytest.param({"secret_s": (np.float64(1), np.float64(2))}, id="numpy-float-secret"),
        pytest.param({"secret_s": (Fraction(1), 2)}, id="fraction-secret"),
        pytest.param({"q_l": 65536.0}, id="float-q_l"),
        pytest.param({"p": 256.0}, id="float-p"),
        # Constructs, then raises TypeError from ``range(self.m)`` on the first read of ``target``:
        # the refusal arrives, but late and from the wrong place.
        pytest.param({"m": 3.0}, id="float-m"),
        pytest.param({"secret_s": (True, False)}, id="bool-secret"),
        pytest.param({"base": ((True, False), (False, True), (True, True))}, id="bool-base"),
        # Refused today — but by accident, from whichever builtin happened to choke first
        # (a slice, three-argument ``pow``, a comparison). Pinned so a type guard that replaces the
        # accident keeps refusing them.
        pytest.param({"nu": 2.0}, id="float-nu"),
        pytest.param({"base": ((1.0, 0.0), (0.0, 1.0), (3.0, 5.0))}, id="float-base"),
        pytest.param({"secret_s": ("1", "2")}, id="string-secret"),
    ],
)
def test_a_non_integer_input_is_refused(override):
    """A float, a bool, a ``Fraction`` or a string in any arithmetic field must not construct.

    ``TypeError`` or ``ValueError`` — the project uses ``ValueError`` for every other refusal in
    this constructor, and ``TypeError`` is the conventional choice for this one, so either is
    accepted. What is not accepted is an instance.
    """
    with pytest.raises((TypeError, ValueError)):
        LatticeQLWRInstance(**{**GOOD, **override})


def test_a_bool_is_refused_as_a_dimension():
    """``True == 1``, so ``nu=True, m=True`` with a one-by-one base passes every length check.

    A bool reaching ``nu`` is a caller's bug — a flag passed positionally — and a one-dimensional
    instance built from it would run without complaint.
    """
    with pytest.raises((TypeError, ValueError)):
        LatticeQLWRInstance(nu=True, q_l=PRODUCTION_Q, p=PRODUCTION_P, m=True, secret_s=(1,), base=((1,),))


def test_no_float_reaches_a_derived_quantity_by_any_route():
    """The consequence, stated on the outputs rather than the constructor.

    Whichever way ``src`` closes this — refusing the input, or coercing an integral float — the
    observable requirement is the same: no public derived quantity is ever a ``float``. Written so
    that a refusal satisfies it too.
    """
    try:
        instance = LatticeQLWRInstance(**{**GOOD, "secret_s": (1.0, 2.0)})
    except (TypeError, ValueError):
        return
    derived = [*instance.target, *instance.public_samples(), *instance.error_vector()]
    assert all(is_exact_integer(v) for v in derived), [type(v).__name__ for v in derived]


# ---------------------------------------------------------------------------------------------
# properties of every valid instance
# ---------------------------------------------------------------------------------------------


@settings(deadline=None, max_examples=60)
@given(instance=valid_instances())
def test_every_public_derived_quantity_is_an_exact_integer(instance):
    """``target``, ``error_vector()`` and everything else a caller can read, element by element.

    ``equivalent_gaussian_sigma`` is the one documented exception — a reporting convenience that is
    "never used in a computation" — and is asserted to be the *only* float in ``describe()``.
    """
    sequences = {
        "target": instance.target,
        "public_samples": instance.public_samples(),
        "error_vector": instance.error_vector(),
        "evaluate(secret)": instance.evaluate(instance.secret_s),
        "evaluate(zero)": instance.evaluate((0,) * instance.nu),
        "exact_error": tuple(instance.exact_error(i) for i in range(instance.m)),
        "inner_product": tuple(
            instance.inner_product(i, instance.secret_s) for i in range(instance.m)
        ),
    }
    for name, values in sequences.items():
        assert len(values) == instance.m, name
        assert all(is_exact_integer(v) for v in values), (name, [type(v).__name__ for v in values])

    scalars = {
        "rounding_ratio": instance.rounding_ratio,
        "noise_bound": instance.noise_bound,
        "raw_rounded": instance.raw_rounded(instance.q_l - 1),
        "sample": instance.sample(instance.q_l - 1),
    }
    for name, value in scalars.items():
        assert is_exact_integer(value), (name, type(value).__name__)

    described = instance.describe()
    floats = sorted(k for k, v in described.items() if isinstance(v, float))
    assert floats == ["equivalent_gaussian_sigma"]
    assert all(is_exact_integer(v) for v in described["noise_interval"])


@settings(deadline=None, max_examples=60)
@given(instance=valid_instances())
def test_the_derived_quantities_lie_in_their_integer_ranges(instance):
    """Types alone would be satisfied by garbage. ``target`` is in ``Z_p``, the lifted samples in
    ``Z_q``, the inner products in ``Z_q``, and the error inside the instance's own noise bound."""
    q, p, bound = instance.q_l, instance.p, instance.noise_bound
    assert all(0 <= v < p for v in instance.target)
    assert all(0 <= v < q for v in instance.public_samples())
    assert all(0 <= instance.inner_product(i, instance.secret_s) < q for i in range(instance.m))
    assert all(-bound <= e <= bound for e in instance.error_vector())
    assert 1 <= bound <= q // 2


@settings(deadline=None, max_examples=60)
@given(instance=valid_instances())
def test_check_relation_holds_on_every_generated_instance(instance):
    """``A s - b - e == 0 (mod q)`` — through ``check_relation``, and again without it.

    The second half recomputes the sample from the definition in ``fractions``:
    ``floor(u * p / q + 1/2) mod p``, lifted by ``q // p``. ``check_relation`` alone could not fail
    here, because ``exact_error`` *defines* ``e`` as the residual; what can fail is the residual
    being something other than the rounding error of the relation as the corpus states it.
    """
    instance.check_relation()

    q, p = instance.q_l, instance.p
    b = instance.public_samples()
    e = instance.error_vector()
    for i, row in enumerate(instance.base):
        u = sum(int(x) * int(s) for x, s in zip(row, instance.secret_s)) % q
        rounded = (Fraction(u * p, q) + Fraction(1, 2)).__floor__() % p
        assert instance.target[i] == rounded
        assert b[i] == (q // p) * rounded
        assert (u - b[i] - e[i]) % q == 0


@settings(deadline=None, max_examples=25)
@given(instance=valid_instances())
def test_the_normal_form_stays_in_integer_arrays(instance):
    """The instance hands its numbers to numpy at the normal form, which is where an ``int`` most
    easily becomes a ``float64`` without anybody writing the word. Integer dtype on all four arrays,
    and the transformed relation still exact."""
    assume(instance.m >= instance.nu + 2)
    try:
        nf = to_normal_form(instance)
    except PivotNotFound:
        assume(False)
    for name in ("a", "b", "x", "e"):
        array = getattr(nf, name)
        assert array.dtype.kind in "iO", (name, array.dtype)
        assert all(is_exact_integer(v) for v in array.ravel().tolist()), name
    assert is_exact_integer(nf.noise_bound) and is_exact_integer(nf.q)
    lhs = [
        (sum(int(nf.a[i, j]) * int(nf.x[j]) for j in range(nf.n)) + int(nf.e[i])) % nf.q
        for i in range(nf.m)
    ]
    assert lhs == [int(v) % nf.q for v in nf.b]


def test_the_relation_is_exact_at_a_modulus_no_double_can_hold():
    """Where a float would actually be *wrong*, not merely the wrong type.

    At ``q = 2^80`` an inner product has 80 significant bits and a double keeps 53. Any float on the
    path from ``base`` to ``target`` would change the rounded sample for most rows; the reference
    here is pure ``fractions``. This is the production failure mode in miniature — at
    ``q = 2^16, nu = 256`` the *products* are what overflow a double, not the modulus.
    """
    q, p, nu, m = 1 << 80, 1 << 8, 3, 8
    instance = make_instance(nu, m, q, p, seed=7)
    assert instance is not None
    instance.check_relation()
    for i, row in enumerate(instance.base):
        u = sum(x * s for x, s in zip(row, instance.secret_s)) % q
        expected = (Fraction(u * p, q) + Fraction(1, 2)).__floor__() % p
        assert instance.target[i] == expected
        assert type(instance.target[i]) is int

    # And a float route really would differ, or this test would be decoration.
    float_route = [
        int(round(float(sum(x * s for x, s in zip(row, instance.secret_s)) % q) * p / q)) % p
        for row in instance.base
    ]
    exact_errors = instance.error_vector()
    assert all(-(q // (2 * p)) <= e <= q // (2 * p) for e in exact_errors)
    # The float route agrees on the *sample* (it keeps the top bits) but cannot represent the
    # error, which lives in the bits it dropped: reconstructing e from floats loses it entirely.
    lossy = [
        float(sum(x * s for x, s in zip(row, instance.secret_s)) % q) - float((q // p) * t)
        for row, t in zip(instance.base, float_route)
    ]
    assert any(int(v) != e for v, e in zip(lossy, exact_errors))
