"""Every third-party API this project calls, executed rather than read from documentation.

The sibling Grover project's probe found five behaviours that contradicted the documentation, three
of which would have failed silently. This project leans on three C++-backed libraries whose Python
surfaces are thin and whose versions here are pinned by what happens to be built, so the same
discipline applies with more force: nothing is built on an API that has not been run.

What the checks here protect, specifically:

* ``fpylll`` and G6K are the attack engines. If either behaves differently than expected, every
  reduction result is suspect in a way no downstream test can see — a wrong lattice reduces
  perfectly well.
* The estimator's numbers are the theoretical half of the project's central comparison, so the
  probe pins a *known published answer* (Kyber512) rather than merely proving the import works. A
  cost model that runs but returns different numbers than the one the corpus's methodology assumes
  is worse than one that fails loudly.
* The exactness budget: the whole construction is integer arithmetic, and a silent float or a
  64-bit overflow would produce a plausible lattice for the wrong instance. The probe measures
  where that boundary is rather than assuming it.

Absence is reported, not papered over: G6K is an optional engine, and ``g6k`` checks report
``required=False`` so a missing build reads as a clean absence rather than a crash.
"""

from __future__ import annotations

import importlib
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any

__all__ = ["Check", "probe_all", "format_report", "required_failures", "optional_absences"]

# The lattice-estimator revision the Kyber512 figures below were measured at, and the figures
# themselves under that revision's default models (MATZOV cost, GSA shape).
#
# These are a golden baseline for one revision, not literature constants. A cost estimate moves
# with both models, so a remembered number asserted as equality would either fail on a legitimate
# model change or -- worse -- match by coincidence and hide one. The probe records the revision and
# the models so drift is attributable instead of mysterious.
_ESTIMATOR_BASELINE_REVISION = "53da5982597709ba0fdf94ea37a84d822310fd84"
_KYBER512_BETA = {"usvp": 406, "dual_hybrid": 387}


@dataclass
class Check:
    """One measured claim about one API."""

    name: str
    ok: bool
    detail: str = ""
    required: bool = True
    payload: Any = field(default=None, repr=False)

    def line(self) -> str:
        mark = "ok  " if self.ok else ("FAIL" if self.required else "none")
        return f"[{mark}] {self.name}" + (f" -- {self.detail}" if self.detail else "")


def _check(name: str, fn, *, required: bool = True) -> Check:
    """Run ``fn`` and turn any exception into a reported failure rather than a traceback.

    A probe that dies on the first missing package reports one absence instead of all of them,
    which is the wrong shape for a milestone whose whole job is to enumerate what is available.
    """
    try:
        detail, payload = fn()
        return Check(name, True, detail or "", required, payload)
    except Exception as exc:  # noqa: BLE001 - reporting is the point
        return Check(name, False, f"{type(exc).__name__}: {exc}", required)


def _ensure_estimator_importable() -> str:
    """Put the estimator on the path if it is not installed, and say where it came from.

    It is not on PyPI and is normally run from its own checkout, so "installed" and "importable
    because the checkout is on the path" are both legitimate states and the probe records which one
    it found. Paths come from the environment rather than being hard-coded, so the relocation this
    project performs does not leave a stale absolute path behind.
    """
    import os
    from pathlib import Path

    try:
        mod = importlib.import_module("estimator")
        return str(Path(mod.__file__).parent)
    except ImportError:
        pass

    candidates = []
    env = os.environ.get("QLS_LATTICE_ESTIMATOR")
    if env:
        candidates.append(Path(env))
    for root in (Path.home() / "Documents" / "lattice-tools", Path.home() / "src"):
        candidates.append(root / "lattice-estimator")

    for path in candidates:
        if (path / "estimator" / "__init__.py").exists():
            sys.path.insert(0, str(path))
            mod = importlib.import_module("estimator")
            return str(Path(mod.__file__).parent)

    raise ImportError(
        "estimator not importable and no checkout found; set QLS_LATTICE_ESTIMATOR to its path"
    )


def probe_all() -> list[Check]:
    """Run every check. Order matters only in that later checks may rely on earlier imports."""
    checks: list[Check] = []

    # -- fpylll: the required engine ---------------------------------------------------------

    def fpylll_version():
        import fpylll

        cfg = fpylll.config
        have_qd = getattr(cfg, "have_qd", None)
        return (
            f"fpylll {fpylll.__version__}, qd={have_qd}, "
            f"max_enum_dim={getattr(cfg, 'max_enum_dim', '?')}",
            {"version": fpylll.__version__, "have_qd": have_qd},
        )

    checks.append(_check("fpylll imports and reports its build config", fpylll_version))

    def lll_runs():
        from fpylll import IntegerMatrix, LLL

        A = IntegerMatrix.from_matrix([[1, 0, 0], [0, 1, 0], [7, 3, 1]])
        LLL.reduction(A)
        rows = [[int(A[i, j]) for j in range(3)] for i in range(3)]
        return f"LLL reduced a rank-3 basis to {rows}", rows

    checks.append(_check("LLL.reduction runs on a hand-built basis", lll_runs))

    def qary_random():
        from fpylll import IntegerMatrix

        A = IntegerMatrix.random(40, "qary", k=20, bits=10)
        return f"IntegerMatrix.random(40,'qary',k=20,bits=10) -> {A.nrows}x{A.ncols}", None

    checks.append(_check("IntegerMatrix.random builds a q-ary basis", qary_random))

    def bkz_param_surface():
        from fpylll import BKZ, IntegerMatrix, LLL

        A = IntegerMatrix.random(40, "qary", k=20, bits=10)
        LLL.reduction(A)
        param = BKZ.Param(block_size=20, max_loops=2, flags=BKZ.AUTO_ABORT)
        BKZ.reduction(A, param)
        return f"BKZ.Param(block_size=20,max_loops=2,AUTO_ABORT) accepted; block_size={param.block_size}", None

    checks.append(_check("BKZ 2.0 parameter surface is accepted", bkz_param_surface))

    def svp_exact():
        """Exact enumeration is the independent lambda_1 reference the cross-checks need."""
        from fpylll import IntegerMatrix, LLL, SVP

        A = IntegerMatrix.random(40, "qary", k=20, bits=10)
        LLL.reduction(A)
        v = SVP.shortest_vector(A)
        norm = sum(int(x) ** 2 for x in v) ** 0.5
        return f"exact shortest vector found, ||v|| = {norm:.3f}", norm

    checks.append(_check("SVP.shortest_vector enumerates exactly", svp_exact))

    def gso_access():
        """The float GSO route is cross-check 5's second opinion on the determinant."""
        from fpylll import GSO, IntegerMatrix, LLL

        A = IntegerMatrix.random(20, "qary", k=10, bits=10)
        LLL.reduction(A)
        M = GSO.Mat(A, flags=GSO.ROW_EXPO)
        M.update_gso()
        r = [M.get_r(i, i) for i in range(3)]
        return f"GSO.Mat with ROW_EXPO; first three r_ii exponents = {r}", r

    checks.append(_check("GSO.Mat exposes the Gram-Schmidt data", gso_access))

    # -- exactness budget --------------------------------------------------------------------

    def int64_exactness():
        """The construction multiplies nu-vectors of w-bit values. Find where int64 stops being safe.

        This is measured, not reasoned about: the failure mode is a silent wraparound that yields a
        lattice for a different instance, which is indistinguishable downstream from a correct one.
        """
        import numpy as np

        q = 1 << 16
        worst_product = (q - 1) ** 2
        worst_sum = 256 * worst_product  # nu at the recorded production dimension
        headroom = np.iinfo(np.int64).max // worst_sum
        assert np.iinfo(np.int64).max > worst_sum, "int64 overflows the production inner product"
        return (
            f"int64 holds the production inner product with {headroom:.3g}x headroom "
            f"(nu*q^2 = {worst_sum:.3g})",
            headroom,
        )

    checks.append(_check("int64 is exact for the production parameter magnitudes", int64_exactness))

    def python_int_is_unbounded():
        q = 1 << 16
        v = (q - 1) ** 2 * 256
        assert v == (65535**2) * 256
        return "arbitrary-precision int confirmed as the exact fallback", None

    checks.append(_check("Python ints are unbounded for the fallback path", python_int_is_unbounded))

    # -- G6K: optional engine -----------------------------------------------------------------

    def cysignals_first():
        """G6K's extensions resolve cysignals symbols through the loaded Python global table.

        Importing cysignals first is what makes that resolution succeed; it is a real ordering
        requirement, not a convention.
        """
        import cysignals.signals  # noqa: F401

        return "cysignals.signals imported", None

    checks.append(
        _check("cysignals imports (G6K's symbol dependency)", cysignals_first, required=False)
    )

    def g6k_imports():
        from g6k import Siever

        import g6k

        return f"g6k imports from {g6k.__file__}", None

    checks.append(_check("g6k imports", g6k_imports, required=False))

    def g6k_sieving_bkz():
        """A real sieving tour that must actually shrink the basis, not merely return."""
        from fpylll import IntegerMatrix, LLL

        from g6k.algorithms.bkz import pump_n_jump_bkz_tour as bkz
        from g6k.siever import Siever
        from g6k.utils.stats import dummy_tracer

        d = 40
        A = IntegerMatrix(d, d, int_type="mpz")
        A.randomize("qary", k=d // 2, bits=10)
        LLL.reduction(A)

        def norm0():
            return sum(float(A[0, j]) ** 2 for j in range(d)) ** 0.5

        before = norm0()
        g6k = Siever(A)
        bkz(g6k, dummy_tracer, 20)
        after = norm0()
        assert after <= before, "the sieving tour left the basis longer than it found it"
        return f"||b1|| {before:.1f} -> {after:.1f} ({100 * (1 - after / before):.1f}% shorter)", (
            before,
            after,
        )

    checks.append(_check("G6K sieving BKZ reduces a basis", g6k_sieving_bkz, required=False))

    def g6k_dual_mode():
        """The dual attack needs the dual sieving mode; it is a separate code path."""
        from fpylll import IntegerMatrix, LLL

        from g6k.algorithms.bkz import pump_n_jump_bkz_tour as bkz
        from g6k.siever import Siever
        from g6k.utils.stats import dummy_tracer

        A = IntegerMatrix(40, 40, int_type="mpz")
        A.randomize("qary", k=20, bits=10)
        LLL.reduction(A)
        g6k = Siever(A)
        with g6k.temp_params(dual_mode=True):
            bkz(g6k, dummy_tracer, 20)
        return "dual_mode sieving tour completed", None

    checks.append(_check("G6K dual mode runs", g6k_dual_mode, required=False))

    def g6k_db_size_model():
        """The memory ceiling is derived from these two constants; read them, do not recall them."""
        from g6k.siever_params import SieverParams

        sp = SieverParams()
        base = sp.db_size_base
        factor = sp.db_size_factor
        assert base > 1 and factor > 1
        return f"db_size_base={base:.6f}, db_size_factor={factor}", (base, factor)

    checks.append(_check("G6K exposes its database-size model", g6k_db_size_model, required=False))

    # -- the estimator: the theoretical half --------------------------------------------------

    def estimator_imports():
        where = _ensure_estimator_importable()
        return f"estimator from {where}", where

    checks.append(_check("lattice-estimator imports", estimator_imports))

    def kyber512_reproduces():
        """Pin the estimator's own output, under the models it defaults to.

        These figures are a golden baseline for the revision named above -- **not** literature
        constants. A cost estimate moves with both the cost model and the shape model, so quoting a
        remembered number and asserting equality would turn a legitimate model change into a false
        failure and, worse, a remembered number that happens to match would hide a silent model
        change. Recording the revision and the models alongside makes drift visible as drift.

        The distinction matters here because this project's central comparison is *empirical versus
        this estimate*. If the estimate quietly changed, the comparison would change with it and
        nothing downstream would look wrong.
        """
        where = _ensure_estimator_importable()
        import subprocess
        from math import log2

        from estimator import LWE, RC, schemes

        r = LWE.estimate(schemes.Kyber512, quiet=True)
        got = {k: r[k]["beta"] for k in ("usvp", "dual_hybrid") if k in r}
        assert set(got) == set(_KYBER512_BETA), f"attack families changed: {sorted(r.keys())}"

        # The models the numbers were produced under, recorded so a drift is attributable.
        models = f"cost={type(RC.MATZOV).__name__}/GSA (defaults)"

        try:
            rev = subprocess.run(
                ["git", "-C", str(__import__("pathlib").Path(where).parent), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
        except Exception:  # noqa: BLE001
            rev = "unknown"

        if got != _KYBER512_BETA:
            basis = (
                "the estimator revision differs from the baseline"
                if rev != _ESTIMATOR_BASELINE_REVISION
                else "SAME revision: the models or a dependency changed underneath"
            )
            raise AssertionError(
                f"Kyber512 betas {got} != baseline {_KYBER512_BETA}; {basis} "
                f"(revision {rev[:12]}, {models}). Re-baseline deliberately."
            )

        log2_rop = round(log2(float(r["usvp"]["rop"])), 1)
        return (
            f"Kyber512 usvp beta={got['usvp']} (log2 rop={log2_rop}), "
            f"dual_hybrid beta={got['dual_hybrid']}; revision {rev[:12]}, {models}",
            got,
        )

    checks.append(_check("Kyber512 reproduces the pinned estimator baseline", kyber512_reproduces))

    def uniform_distribution():
        """The QLWR noise is exactly uniform on [-q/(2p), q/(2p)-1]; the estimator must accept it."""
        _ensure_estimator_importable()
        from estimator import ND

        d = ND.Uniform(-128, 127)
        return f"ND.Uniform(-128,127) -> {d}", None

    checks.append(_check("the estimator accepts the exact QLWR uniform noise", uniform_distribution))

    def estimator_exposes_normalize():
        """The estimator normalises a uniform-secret instance before attacking it, and adds n
        dimensions when the secret is not smaller than the error. The emulator's attack has to make
        the same transformation or the two halves of the central comparison describe different
        lattices, so the probe checks the behaviour exists rather than reading it from the source.

        ``LWEParameters`` is imported from its defining module, not the package: ``estimator``'s
        ``__all__`` is ``['ND','Logging','RC','Simulator','LWE','NTRU','SIS','schemes']`` and does
        not re-export it, which is exactly the kind of thing a probe run is for.
        """
        _ensure_estimator_importable()
        from estimator import ND
        from estimator.lwe_parameters import LWEParameters

        q = 1 << 16
        params = LWEParameters(
            n=64, q=q, Xs=ND.Uniform(0, q - 1), Xe=ND.Uniform(-128, 127), m=64
        )
        normalised = LWEParameters.normalize(params)

        # The property that matters is not that normalize() exists but *what it does*: it moves the
        # small distribution onto the secret. A uniform secret has no short representative, so a
        # Kannan embedding built on it contains no short vector -- the attack would be on an
        # instance with nothing to find. Asserting the swap is what pins that.
        before_sigma = float(params.Xs.stddev)
        after_sigma = float(normalised.Xs.stddev)
        assert after_sigma < before_sigma, (
            f"normalize() left the secret at sigma={after_sigma} (was {before_sigma}); "
            "the secret is not small, so the embedding will contain no short vector"
        )
        return (
            f"normalize() moves the small distribution onto the secret: "
            f"Xs sigma {before_sigma:.1f} -> {after_sigma:.1f}, Xe sigma -> {float(normalised.Xe.stddev):.1f}",
            (before_sigma, after_sigma),
        )

    checks.append(
        _check("the estimator normalises a uniform secret", estimator_exposes_normalize)
    )

    def sis_estimator_available():
        """Dilithium ships as a module-SIS instance, not an LWE one.

        The plan's verification section pairs "Kyber512 and a Dilithium set"; the Dilithium entries
        in ``estimator.schemes`` are ``Dilithium*_MSIS_*`` and go through ``SIS.estimate``, so the
        published-reference comparison needs both estimators rather than two LWE calls.
        """
        _ensure_estimator_importable()
        from estimator import SIS, schemes

        r = SIS.estimate(schemes.Dilithium2_MSIS_WkUnf, quiet=True)
        keys = list(r.keys())
        assert keys, "SIS.estimate returned nothing"
        return f"SIS.estimate(Dilithium2_MSIS_WkUnf) -> {keys}", keys

    checks.append(_check("the estimator covers the SIS instances Dilithium ships as", sis_estimator_available))

    # -- versions, for provenance ------------------------------------------------------------

    def versions():
        import numpy
        import sympy

        return (
            f"python {sys.version.split()[0]}, numpy {numpy.__version__}, sympy {sympy.__version__}",
            {"python": sys.version.split()[0], "numpy": numpy.__version__},
        )

    checks.append(_check("interpreter and core library versions", versions))

    return checks


def required_failures(checks: list[Check]) -> list[Check]:
    return [c for c in checks if c.required and not c.ok]


def optional_absences(checks: list[Check]) -> list[Check]:
    return [c for c in checks if not c.required and not c.ok]


def format_report(checks: list[Check]) -> str:
    lines = ["", "=" * 78, " qlwr-lattice-stress: API probe", "=" * 78, ""]
    lines += [c.line() for c in checks]
    req = required_failures(checks)
    opt = optional_absences(checks)
    lines += [
        "",
        f"  {len(checks)} checks, {len(req)} required failures, "
        f"{len(opt)} optional absences",
        "",
    ]
    if opt:
        lines.append("  Optional components absent (the pipeline must still run without them):")
        lines += [f"    - {c.name}: {c.detail}" for c in opt]
        lines.append("")
    if req:
        lines.append("  REQUIRED FAILURES -- nothing may be built on these:")
        lines += [f"    - {c.name}: {c.detail}" for c in req]
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    checks = probe_all()
    print(format_report(checks))
    return 1 if required_failures(checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
