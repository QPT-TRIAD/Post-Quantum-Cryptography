"""The theoretical half of the project's central comparison.

Everything here wraps `lattice-estimator` — the tool NIST PQC submissions use to justify claimed
security levels — so that a measured minimum successful block size can be set beside the model's
prediction for the *same* instance. Two things about that wrapping are load-bearing.

**The QLWR-to-LWE mapping is derived, not fitted.** QLWR is not an LWE instance with a Gaussian
error; it is a rounding, and the resulting error is exactly uniform on an interval whose width is
fixed by the modulus ratio. Handing the estimator a fitted sigma would make the comparison
meaningless in a way no later check could detect, because the estimator would faithfully estimate a
different instance. The mapping below computes both endpoints from ``q_l`` and ``p``.

**The estimator swallows exceptions by default.** ``catch_exceptions=True`` is its default, so an
attack family that fails returns a placeholder cost rather than raising. A caller who reads ``beta``
off that placeholder would report a number that came from a failure. Every extraction here goes
through :func:`_cost_field`, which raises instead.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..problem.qlwr_instance import LatticeQLWRInstance
from ..protocols import EXTRAPOLATED, SAME_SCALE, EstimatorReport, Provenance

__all__ = [
    "EstimatorUnavailable",
    "ParameterSet",
    "reference_parameter_set",
    "parameter_set_from_instance",
    "production_parameter_set",
    "lwe_parameters_for",
    "estimate",
    "estimator_revision",
]

#: Schemes the estimator ships that this project treats as published references. Names are the
#: estimator's own; a typo would fail loudly at construction rather than silently estimating
#: nothing, which is why they are resolved by attribute access rather than by a dict lookup.
PUBLISHED_LWE_SCHEMES = ("Kyber512", "Kyber768", "Kyber1024", "Frodo640", "Frodo976", "Frodo1344")

#: Dilithium ships as module-SIS instances, not LWE ones, and goes through ``SIS.estimate``. Worth
#: stating because pairing "Kyber and Dilithium" as two LWE calls is the natural mistake.
PUBLISHED_SIS_SCHEMES = (
    "Dilithium2_MSIS_WkUnf",
    "Dilithium3_MSIS_WkUnf",
    "Dilithium5_MSIS_WkUnf",
)

#: Attack families excluded from ``LWE.estimate``'s all-families sweep.
#:
#: Two reasons, and they are different.
#:
#: The first three are LWE attack families this project does not compare against — the comparison is
#: the primal/dual pair the recorded parameter set's obligation names — and computing them costs
#: real time.
#:
#: ``bdd_hybrid`` and ``bdd_mitm_hybrid`` are excluded for a defect in the estimator rather than for
#: economy. Its aggregation at ``estimator/lwe.py:182`` reads ``res["bdd_hybrid"]["rop"]``
#: unconditionally after that family has been skipped, so when any family in the sweep fails the
#: whole ``estimate`` call raises ``KeyError: 'bdd_hybrid'`` rather than returning the families that
#: did succeed. Measured on a QLWR-shaped instance, where ``bkw`` fails with "Amplifying for mu!=0
#: not implemented" and the primal hybrid fails with "The lower bound exceeds the upper bound".
#: Excluding the pair keeps the sweep on the families that work. This is a workaround for a
#: third-party bug, recorded here because a reader who later removes these entries will meet it.
DEFAULT_DENY_LIST = ("arora-gb", "bkw", "bdd", "bdd_hybrid", "bdd_mitm_hybrid")


class EstimatorUnavailable(RuntimeError):
    """Raised when the estimator cannot be imported or its checkout cannot be found."""


@dataclass(frozen=True)
class ParameterSet:
    """Parameters to estimate, in whichever form the estimator expects.

    ``kind`` selects the estimator entry point; it is not decoration, because passing a SIS instance
    to ``LWE.estimate`` produces a confident answer about the wrong problem.
    """

    name: str
    kind: Literal["lwe", "sis"]
    payload: Any
    n: int | None = None
    q: int | None = None
    m: int | None = None
    noise: str | None = None
    #: The label an estimate of this set carries. A property of the *parameter set*, not of the call
    #: that estimates it: whether a figure is "same scale" depends on whether these parameters were
    #: attacked at this scale, and the set knows that while a call site has to remember it. The
    #: production set is ``EXTRAPOLATED``; every other constructor leaves the default.
    provenance: Provenance = SAME_SCALE

    def __post_init__(self) -> None:
        if self.kind not in ("lwe", "sis"):
            raise ValueError(f"kind must be 'lwe' or 'sis', got {self.kind!r}")


def _estimator_module():
    try:
        import estimator  # noqa: F401
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise EstimatorUnavailable(
            "lattice-estimator is not importable. It is not on PyPI and is registered by "
            "scripts/move_tools.py; see README.md."
        ) from exc
    import estimator

    return estimator


def estimator_revision() -> str:
    """The estimator's git revision, recorded beside every number it produces.

    A cost estimate moves with the cost and shape models, so a bare number is not reproducible. The
    revision is what makes a later disagreement attributable rather than mysterious.
    """
    _estimator_module()
    import estimator

    root = Path(estimator.__file__).resolve().parent.parent
    try:
        return subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def reference_parameter_set(name: str) -> ParameterSet:
    """A published parameter set, by the estimator's own name for it."""
    estimator = _estimator_module()

    if name in PUBLISHED_LWE_SCHEMES:
        payload = getattr(estimator.schemes, name)
        return ParameterSet(
            name=name, kind="lwe", payload=payload,
            n=getattr(payload, "n", None), q=getattr(payload, "q", None),
        )
    if name in PUBLISHED_SIS_SCHEMES:
        payload = getattr(estimator.schemes, name)
        return ParameterSet(name=name, kind="sis", payload=payload)
    raise ValueError(
        f"unknown published scheme {name!r}; LWE: {PUBLISHED_LWE_SCHEMES}; SIS: {PUBLISHED_SIS_SCHEMES}"
    )


def lwe_parameters_for(instance: LatticeQLWRInstance):
    """The QLWR instance as LWE parameters — **exactly**, with no fitted width.

    The relation is ``b_i = round_half_up(u_i * p, q_l) mod p`` with ``u_i = <X_i, s> mod q_l``.
    Lifting the sample back into ``Z_{q_l}`` as ``(q_l // p) * b_i`` makes the rounding an additive
    offset ``e_i = u_i - (q_l // p) * b_i``, and for ``u_i`` uniform on ``[0, q_l)`` that offset is
    **exactly uniform** on ``[-q_l/(2p), q_l/(2p) - 1]``. Both endpoints are integers derived from
    the modulus ratio; there is no sigma to choose, and choosing one would silently substitute a
    different instance for the one being attacked.

    The secret is uniform on ``Z_{q_l}``, which is what the corpus specifies. The estimator's own
    ``normalize()`` will then move the small distribution onto the secret — see the M2 gate test,
    which checks that this transformation and the emulator's are the same one.
    """
    estimator = _estimator_module()

    b = instance.noise_bound
    return estimator.LWE.Parameters(
        n=instance.nu,
        q=instance.q_l,
        Xs=estimator.ND.Uniform(0, instance.q_l - 1),
        Xe=estimator.ND.Uniform(-b, b - 1),
        m=instance.m,
    )


def parameter_set_from_instance(instance: LatticeQLWRInstance) -> ParameterSet:
    """The emulator's own instance, in the form the estimator consumes."""
    b = instance.noise_bound
    return ParameterSet(
        name=f"{instance.label}:nu={instance.nu},q={instance.q_l},m={instance.m}",
        kind="lwe",
        payload=lwe_parameters_for(instance),
        n=instance.nu,
        q=instance.q_l,
        m=instance.m,
        noise=f"Uniform(-{b}, {b - 1}) exact; sigma_eq={instance.equivalent_gaussian_sigma:.4f}",
    )


def production_parameter_set(*, samples: str = "rows") -> ParameterSet:
    """The **recorded production parameter set**, in the form the estimator consumes.

    This is the module's only path to the corpus's numbers, and it is deliberately a different shape
    from the two above. ``reference_parameter_set`` borrows a scheme the estimator ships;
    ``parameter_set_from_instance`` borrows an instance this project built. This one takes the values
    from :mod:`~qlwr_lattice_stress.problem.production_parameters`, where they are recorded as named
    constants with their citations — so nothing here reads the research tree, and a run reproduces
    without it.

    **No lattice is built from these values and no reduction runs on them.** At ``nu = 256`` the
    uSVP dimension is 609; the largest lattice this project has reduced is 161. The estimator is a
    cost model, and what it returns is a model output — its credibility rests on the same-scale
    comparison the scaled sweep supplies, not on this call.

    ``samples`` selects which of the corpus's two sample counts to estimate against. They are
    different amounts of data to an attack, and the corpus does not say which one a cost should be
    quoted against — so it is a required choice rather than a default that hides the reading. Both
    are meant to be reported side by side.
    """
    from ..problem.production_parameters import (
        PRODUCTION_M,
        PRODUCTION_NOISE_BOUND,
        PRODUCTION_NU,
        PRODUCTION_P,
        PRODUCTION_Q_L,
        sample_count_readings,
    )

    estimator = _estimator_module()

    readings = sample_count_readings()
    if samples not in readings:
        raise ValueError(
            f"unknown sample reading {samples!r}; the corpus supports {sorted(readings)}. The two "
            "are different amounts of data to an attack, and a cost is only meaningful alongside "
            "which one it was made under."
        )
    m = readings[samples]

    payload = estimator.LWE.Parameters(
        n=PRODUCTION_NU,
        q=PRODUCTION_Q_L,
        Xs=estimator.ND.Uniform(0, PRODUCTION_Q_L - 1),
        Xe=estimator.ND.Uniform(-PRODUCTION_NOISE_BOUND, PRODUCTION_NOISE_BOUND - 1),
        m=m,
    )
    return ParameterSet(
        name=f"production_recorded:nu={PRODUCTION_NU},q={PRODUCTION_Q_L},p={PRODUCTION_P},m={m}",
        kind="lwe",
        payload=payload,
        n=PRODUCTION_NU,
        q=PRODUCTION_Q_L,
        m=m,
        noise=(
            f"Uniform(-{PRODUCTION_NOISE_BOUND}, {PRODUCTION_NOISE_BOUND - 1}) exact — the rounding "
            "error is deterministic and exactly uniform, so there is no fitted width. Samples taken "
            f"as the corpus's {samples!r} reading, {m}."
        ),
        # Nothing was attacked at this scale — the docstring's second paragraph — so an estimate of
        # this set is not a same-scale figure. Said here, once, so that the library call, the CLI's
        # ``production-estimate`` and any future caller all emit the label without each having to
        # remember it; they used to emit ``theoretical_same_scale``, because ``estimate`` defaulted
        # to it and no caller overrode it.
        provenance=EXTRAPOLATED,
    )


def _cost_field(cost: Any, field_name: str, *, attack: str) -> Any:
    """Read one field off an estimator cost, refusing to read a placeholder.

    The estimator runs each attack family under ``catch_exceptions=True``, so a family that failed
    returns something rather than raising. Reading ``beta`` off that would put a number produced by
    a failure into the report's theoretical section, where it would look exactly like a real one.
    """
    if cost is None:
        raise ValueError(f"attack {attack!r} returned nothing")
    if isinstance(cost, Exception):
        raise ValueError(f"attack {attack!r} failed: {type(cost).__name__}: {cost}")

    # ``Cost`` is a dict subclass, so its fields are reached by *item* access — ``cost["beta"]``,
    # not ``cost.beta``. Attribute access silently finds the dict's own methods instead and reports
    # a missing field that is in fact present, which is a confusing way to fail.
    if hasattr(cost, "__getitem__"):
        try:
            return cost[field_name]
        except (KeyError, TypeError):
            pass
    if hasattr(cost, field_name):
        return getattr(cost, field_name)

    if isinstance(cost, dict):
        available = sorted(cost.keys())
    else:
        available = [a for a in dir(cost) if not a.startswith("_")]
    raise ValueError(
        f"attack {attack!r} produced {type(cost).__name__} with no {field_name!r}; "
        f"available: {available[:12]}"
    )


def _log2(value: Any) -> float | None:
    """``log2`` of a cost, or ``None`` when the model does not apply.

    An infinite cost is the estimator's way of saying "this attack has no valid parameters for this
    instance", not "this attack is impossible at any cost", and the two mean different things in a
    report. Returning ``None`` records the absence; returning ``inf`` would put a number into a
    table where a reader would compare it against real ones.
    """
    from math import isinf, log2

    try:
        f = float(value)
    except Exception:  # noqa: BLE001
        return None
    if isinf(f):
        return None
    return round(log2(f), 2) if f > 0 else None


def estimate(
    params: ParameterSet,
    *,
    models: tuple[str, ...] = ("primal_usvp", "dual"),
    quantum_sieving_speedup: bool = True,
    jobs: int = 1,
    provenance: Provenance | None = None,
) -> EstimatorReport:
    """Run the cost models against one parameter set.

    ``provenance`` defaults to the parameter set's own label (``params.provenance``): same-scale
    for a published scheme or an instance this project built, extrapolated for the recorded
    production set. It can be passed to make a label *more* cautious, never less: asking for a
    same-scale label on a set that is not same-scale is refused, because that is the blend the
    reports exist to prevent.

    Both a classical and a quantum-sieving figure are produced whenever ``quantum_sieving_speedup``
    is set, because the two differ by a constant factor that matters when comparing against a
    claimed bit-security level, and a report that gave only one would leave the reader to guess
    which. The classical/quantum distinction is a property of the *cost model*
    (``ADPS16``'s ``mode``), not of the shape model.
    """
    if provenance is None:
        provenance = params.provenance
    elif provenance == SAME_SCALE and params.provenance != SAME_SCALE:
        raise ValueError(
            f"{params.name} is labelled {params.provenance!r}; an estimate of it cannot be "
            f"relabelled {SAME_SCALE!r}"
        )

    estimator = _estimator_module()
    if params.kind == "sis":
        return _estimate_sis(estimator, params, provenance=provenance)

    # ``RC.ADPS16`` is an *instance* of the cost model, not the class, so calling it invokes the
    # cost function itself and raises on a keyword it never expected. The class is reachable from
    # its defining module. Verified: at beta=500 the two modes give 2^146.00 and 2^132.50, which
    # are 500 * 0.292 and 500 * 0.265 exactly — the core-SVP constants.
    from estimator.reduction import ADPS16

    def run(mode: str) -> dict[str, Any]:
        return estimator.LWE.estimate(
            params.payload,
            red_cost_model=ADPS16(mode=mode),
            deny_list=DEFAULT_DENY_LIST,
            jobs=jobs,
            quiet=True,
        )

    classical = run("classical")
    quantum = run("quantum") if quantum_sieving_speedup else None

    family_of = {"primal_usvp": "usvp", "dual": "dual", "dual_hybrid": "dual_hybrid"}

    def pick(result: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for model in models:
            family = family_of.get(model, model)
            cost = result.get(family)
            if cost is None:
                out[model] = {"family": family, "applicable": False,
                              "why": "the estimator did not return this family"}
                continue

            rop_log2 = _log2(_cost_field(cost, "rop", attack=family))
            if rop_log2 is None:
                # An infinite cost is the estimator's way of saying this attack has no valid
                # parameters for this instance. That is a *finding*, not a failure — but it is a
                # finding **about a sample count**, and the earlier version of this comment said it
                # without that qualifier, which made it read as a property of QLWR instances.
                #
                # Measured at the production modulus pair (q = 2^16, p = 2^8) and nu = 256, in
                # `scripts/applicability_threshold.py`:
                #
                #     m < 532              no family applies at all — every cost is infinite
                #     532 <= m < 536       `usvp` applies, `dual` does not
                #     m >= 536             both apply
                #
                # So `usvp` — the family that supplies the production estimate's headline — is not
                # inapplicable to QLWR; it is inapplicable *below a sample count*, and the recorded
                # rows reading of 608 clears that threshold by 76 samples. An instance just under it
                # yields "no applicable attack", which is not the same statement as "secure" and
                # must not be rendered as one.
                out[model] = {
                    "family": family,
                    "applicable": False,
                    "rop_log2": None,
                    "why": (
                        "the estimator returned an infinite cost: this attack has no valid "
                        "parameters for the instance as modelled"
                    ),
                }
                continue

            # `beta` is only meaningful when the model applied, so it is required here and not
            # before. Requiring it unconditionally is what made a legitimate inapplicability look
            # like a missing field.
            # Cast to a Python int. The estimator runs under Sage and returns Sage ``Integer``
            # objects, which compare and print exactly like ints but are not JSON-serialisable —
            # so the failure surfaces at the reporting boundary rather than here, which is the
            # worst place to discover it: after a run has completed and its results cannot be
            # written.
            out[model] = {
                "family": family,
                "applicable": True,
                "beta": int(_cost_field(cost, "beta", attack=family)),
                "rop_log2": rop_log2,
            }
        return out

    classical_picked = pick(classical)
    quantum_picked = pick(quantum) if quantum else {}

    def min_rop(picked: dict[str, Any]) -> float | None:
        values = [v["rop_log2"] for v in picked.values() if v.get("rop_log2") is not None]
        return min(values) if values else None

    inapplicable = [
        name for name, v in classical_picked.items() if not v.get("applicable", False)
    ]
    applicable = {k: v for k, v in classical_picked.items() if v.get("applicable")}
    best = (
        min(applicable.items(), key=lambda kv: kv[1]["rop_log2"])[0] if applicable else None
    )

    return EstimatorReport(
        beta_usvp=classical_picked.get("primal_usvp", {}).get("beta"),
        beta_dual=classical_picked.get("dual", {}).get("beta")
        or classical_picked.get("dual_hybrid", {}).get("beta"),
        rop_usvp_log2=classical_picked.get("primal_usvp", {}).get("rop_log2"),
        rop_dual_log2=classical_picked.get("dual", {}).get("rop_log2"),
        rop_classical_log2_min=min_rop(classical_picked),
        rop_quantum_log2_min=min_rop(quantum_picked) if quantum_picked else None,
        minimum_over_models=best,
        model_parameters={
            "requested_models": list(models),
            "classical": classical_picked,
            "quantum": quantum_picked,
            # Families the model does not apply to, named rather than dropped. A report whose
            # theoretical section silently omitted the primal attack would read as though the
            # primal attack had been considered and found no easier than the dual one.
            "inapplicable_models": inapplicable,
            "deny_list": list(DEFAULT_DENY_LIST),
            "scheme": params.name,
            "n": params.n,
            "q": params.q,
            "m": params.m,
            "noise": params.noise,
        },
        estimator_revision=estimator_revision(),
        red_cost_model=f"ADPS16(classical/quantum), estimator default shape",
        red_shape_model="GSA",
        provenance=provenance,
    )


def _estimate_sis(estimator, params: ParameterSet, *, provenance: Provenance) -> EstimatorReport:
    """SIS instances go through a different estimator and report different quantities.

    Dilithium ships as module-SIS, so the LWE machinery does not apply and forcing it would answer a
    question about a different problem. The lattice-estimator returns a single cost here rather than
    a family of attacks, which is why the report's LWE-specific fields are left empty rather than
    filled with something plausible.
    """
    result = estimator.SIS.estimate(params.payload, quiet=True)
    lattice = None
    if isinstance(result, dict):
        lattice = result.get("lattice") or result.get("sis")
    # Through ``_cost_field``, like every LWE family above. This read ``getattr(lattice, "rop",
    # None)``, and ``Cost`` is a dict subclass: the attribute does not exist, the default was
    # returned, and Dilithium2/3/5 all reported ``None`` where the estimator had said 2^152.2,
    # 2^211.5 and 2^288.2 — a missing number that looked like an inapplicable model.
    rop_log2 = _log2(_cost_field(lattice, "rop", attack="sis")) if lattice is not None else None
    return EstimatorReport(
        beta_usvp=None,
        beta_dual=None,
        rop_usvp_log2=None,
        rop_dual_log2=None,
        rop_classical_log2_min=rop_log2,
        rop_quantum_log2_min=None,
        minimum_over_models="sis",
        model_parameters={"scheme": params.name, "kind": "sis"},
        estimator_revision=estimator_revision(),
        red_cost_model="SIS default",
        red_shape_model=None,
        provenance=provenance,
    )
