"""The experiment pipeline, as a library function the CLI and scripts both wrap.

Kept out of ``cli.py`` deliberately and for the same reason the design document gives: everything
reachable from a command line should be reachable as a library call, so a result can be reproduced
without going through an argument parser and so a test can exercise the pipeline without one.

## Three instance sources, and what each is for

``synthetic_scaled`` builds an instance at the recorded modulus pair. It is what the lattice
attacks run on and what the loaded-bearing planted-vector test uses.

``random_lattice_control`` builds a q-ary lattice with **no planted vector**: a uniform base and
*uniform samples*, which no secret explains. It is the negative control: a correct attack must run
and fail to recover anything, at every block size where it recovers the synthetic instance. Without
it, "the attack succeeded" carries no weight — a probe that always fires and an attack that always
succeeds are indistinguishable from correct ones. (Until 2026-09-20 this source built a genuinely
planted instance under the control's label, recovered at block size 2; see
``notes/10-test-completion-audit.md``.)

``published_reference`` runs the estimator against a scheme the estimator ships. It is the
estimator validating itself, and it is the only source that produces no lattice attack, because
these are parameter sets whose security is already published rather than instances to attack.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from .analysis.cost_estimation import (
    PUBLISHED_LWE_SCHEMES,
    PUBLISHED_SIS_SCHEMES,
    estimate,
    parameter_set_from_instance,
    reference_parameter_set,
)
from .analysis.empirical_vs_theoretical import compare_block_sizes
from .analysis.scaling_extrapolation import (
    fit_block_size_growth,
    fit_core_svp_model,
    measurements_to_frame,
)
from .attacks import find_minimum_successful_block_size, run_dual_attack
from .config.schema import ExperimentConfig, InstanceSource, dump_config
from .engines import RamBudgetExceeded, assert_within_ram_budget, build_engine, select_engine
from .lattice.basis_construction import build_qary_basis
from .problem.normal_form import to_normal_form
from .problem.qlwr_instance import LatticeQLWRInstance, full_column_rank_mod
from .protocols import EXTRAPOLATED, MEASURED, NOT_RUN, SAME_SCALE
from .utils.seeding import RunSeeds, root_from_environment

__all__ = ["build_instance", "run_experiment", "run_sweep", "lattice_widths_by_family"]


#: How many uniform bases ``build_instance`` draws before concluding the shape admits none.
_MAX_BASE_DRAWS = 64


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def build_instance(config: ExperimentConfig, seeds: RunSeeds) -> LatticeQLWRInstance:
    """Build the instance a config names.

    The sample count follows the config's ``nu_over_m`` ratio rather than being chosen, because that
    ratio is what the scaling rule preserves — and because below a ratio of about 1.6 the estimator's
    models stop applying altogether, which would make the comparison vacuous rather than favourable.
    """
    source = config.instance.source
    if source is InstanceSource.PUBLISHED_REFERENCE:
        raise ValueError(
            "published_reference produces no lattice instance: those are parameter sets whose "
            "security is published, and the estimator is run against them directly. Use `estimate`."
        )

    nu_over_m_num, nu_over_m_den = config.instance.nu_over_m
    m = config.instance.target_dimension
    nu = max(2, round(m * nu_over_m_num / nu_over_m_den))
    # The schema already refuses a ratio at or above one. This is the part it cannot see: the
    # floor of two, and rounding, can still bring ``nu`` up to ``m`` at a small dimension. The
    # normal form consumes ``nu`` samples, so ``nu == m`` leaves a lattice of width zero, and
    # ``nu > m`` makes full column rank unreachable — which used to be an endless loop below rather
    # than an error.
    if nu >= m:
        raise ValueError(
            f"nu_over_m={config.instance.nu_over_m} at target_dimension={m} gives nu={nu}, which "
            f"leaves {m - nu} sample(s) after the normal form consumes nu of them; need nu < m"
        )

    q, p = 1 << 16, 1 << 8
    rng = seeds.rng("instance", source.value, m)

    # Bounded, where it was ``while True``. A uniform m x nu base over Z/2^16 has full column rank
    # with probability above 1 - 2^-(m - nu), so the first draw almost always passes and sixty-four
    # failures in a row mean the shape is wrong, not the luck. The draws themselves are unchanged, so
    # every recorded seed still builds the instance it built before.
    for _ in range(_MAX_BASE_DRAWS):
        base = tuple(tuple(int(v) for v in rng.integers(0, q, size=nu)) for _ in range(m))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    else:
        raise RuntimeError(
            f"no full-column-rank {m} x {nu} base over Z/{q} in {_MAX_BASE_DRAWS} draws; refusing "
            "to keep drawing, because a loop that cannot end is indistinguishable from a slow one"
        )

    if source is InstanceSource.RANDOM_LATTICE_CONTROL:
        # Nothing is planted: the samples are *drawn*, uniform over the values a sample can take
        # (``(q // p) * v`` for ``v`` in ``Z_p``), instead of being derived from the secret. A secret
        # is still recorded — the type requires one — and explains nothing; the attack is expected
        # to run and recover nothing, and that expectation is the control. Drawn after the secret so
        # the base and the secret keep the stream positions they had when this branch planted one.
        secret = tuple(int(v) for v in rng.integers(0, q, size=nu))
        samples = tuple((q // p) * int(v) for v in rng.integers(0, p, size=m))
        return LatticeQLWRInstance(
            nu=nu, q_l=q, p=p, m=m, secret_s=secret, base=base,
            seed=int(seeds.derive("control", m)), label=source.value, control_samples=samples,
        )

    return LatticeQLWRInstance(
        nu=nu, q_l=q, p=p, m=m,
        secret_s=tuple(int(v) for v in rng.integers(0, q, size=nu)),
        base=base, seed=int(seeds.root), label=source.value,
    )


def lattice_widths_by_family(normal_form) -> dict[str, int]:
    """The width of the lattice each attack family actually reduces.

    **They are not the same lattice**, so a single number for both is wrong for at least one of
    them:

    ``primal_usvp``
        embeds the normal-form q-ary lattice — one row and one column — so its width is
        ``nf.m + nf.n + 1``.
    ``dual``
        reduces the dual of that lattice, which lives in ``Z^nf.m``.

    The value this replaced was ``instance.m + instance.nu + 1`` used for both. That double-counts
    ``nu`` and so describes the embedding you get if the normal form is *skipped* — the lattice this
    project established contains no short vector. Measured in the dimension-160 sweep: refused
    primal points were labelled 228 beside measured ones labelled 161, in the same column of the
    same table, and section 6's anomaly text inherited the 228.

    The identity that makes ``instance.m + 1`` the same number as ``nf.m + nf.n + 1``: normalising
    consumes ``nu`` samples and adds ``nu`` unknowns, so ``nf.m + nf.n == instance.m`` exactly. Only
    one of the two expressions says *which lattice it means*, and only this one also covers the
    dual.
    """
    return {
        "primal_usvp": normal_form.m + normal_form.n + 1,
        "dual": normal_form.m,
    }


def _estimate_for(instance: LatticeQLWRInstance, config: ExperimentConfig):
    """The estimator's prediction **for the instance that was attacked**, not for production.

    The same-scale comparison is the one that means something: a model evaluated at a different
    scale would make the discrepancy a measure of the extrapolation rather than of the physics.
    """
    if not config.cost_model.use_lattice_estimator:
        return None
    return estimate(
        parameter_set_from_instance(instance),
        models=tuple(config.cost_model.models),
        quantum_sieving_speedup=config.cost_model.quantum_sieving_speedup,
    )


def _engine_for(config: ExperimentConfig):
    """The engine the config's **whole** preference list selects — not its head.

    This used to be ``build_engine(config.engine.preference[0].value, ...)``: no availability check
    and no look at ``preference[1:]``, so the shipped ``[g6k, fpylll_bkz]`` raised from the first
    reduction on a machine without G6K, where the YAML promises "falls back automatically, with a
    warning, never silently". ``select_engine`` owns that policy and logs the WARNING naming both
    engines; the rows then carry the engine that actually ran, because they take it from the
    reduction outcome rather than from the request.

    A preference naming **one** engine is a request for that engine or nothing, which is what
    ``build_engine`` is for. It is checked here rather than left to fail inside the first reduction,
    so the refusal arrives before the instance has been normalised and calibrated for nothing. Only
    the engines the list names are ever constructed, so an enumeration-only run never imports G6K.
    """
    names = [name.value for name in config.engine.preference]
    if len(names) == 1:
        engine = build_engine(
            names[0], threads=config.engine.threads, gauss_crossover=config.engine.gauss_crossover
        )
        if not engine.available():
            raise RuntimeError(
                f"engine {names[0]!r} is unavailable ({engine.unavailable_reason()}) and "
                "engine.preference names no other; refusing rather than running something the "
                "config did not ask for"
            )
        return engine
    return select_engine({
        "preference": names,
        "threads": config.engine.threads,
        "gauss_crossover": config.engine.gauss_crossover,
    })


def _refused_by_ram_budget(engine, block_size: int, budget_gb: float) -> str | None:
    """The refusal's reason if ``block_size`` is over the RAM budget, else ``None``.

    ``assert_within_ram_budget`` raises, deliberately; the pipeline turns that into a recorded
    refusal because that is how it records every other point it did not run — a sweep that aborts at
    its first over-budget block size reports a shorter range as though it were the configured one.
    """
    try:
        assert_within_ram_budget(engine, block_size, budget_gb)
    except RamBudgetExceeded as exc:
        return str(exc)
    return None


def _not_run_primal_row(block_size: int, dimension: int, engine, reason: str) -> dict[str, Any]:
    """A primal point the pipeline itself refused, shaped like the rows the sweep returns.

    ``threads`` is ``None`` for the reason ``attacks.primal_attack.not_run`` gives: nothing ran.
    """
    return {
        "family": "primal_usvp",
        "block_size": block_size,
        "dimension": dimension,
        "recovered": False,
        "wall_clock_s": 0.0,
        "root_hermite_factor": None,
        "engine": getattr(engine, "name", None),
        "threads": None,
        "provenance": NOT_RUN,
        "not_run_reason": reason,
    }


def _write_outputs(run_dir: Path, config: ExperimentConfig, results: dict[str, Any]) -> None:
    """Write what ``output.formats`` asks for — and ``metrics.json`` regardless.

    ``formats`` was validated and read nowhere: a ``[json]`` run still got a ``report.md``, and
    ``png`` produced nothing because ``reporting.plots`` had no caller. Now ``markdown`` decides the
    report and ``png`` the figure. ``metrics.json`` is **not** optional, and ``json`` in the list is
    accepted without being required: it is the run's record, the report regenerates from it, and a
    sweep writes its fit back into it. A run that left only a rendered report could not be re-read.
    """
    from .reporting import generate_report, plot_block_size_curve

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.json").write_text(json.dumps(_jsonable(results), indent=2) + "\n")
    if "markdown" in config.output.formats:
        generate_report(run_dir, config, results)
    if "png" in config.output.formats:
        # Measured points only, which is all this figure may hold; a run with none has no curve, and
        # says so in its record (``run_experiment`` adds the entry before this is called) rather
        # than leaving an empty axis that reads as "measured, and found nothing".
        points = _measured_primal_points(results)
        if points:
            plot_block_size_curve(
                points,
                dimension=results["instance"]["usvp_lattice_dimension"],
                out_path=run_dir / "figures" / "block_size_curve.png",
            )


def _measured_primal_points(results: Mapping[str, Any]) -> list[tuple[int, float]]:
    return [
        (a["block_size"], a["wall_clock_s"])
        for a in results.get("attacks", [])
        if a.get("family") == "primal_usvp" and a.get("provenance") == MEASURED
    ]


def run_experiment(config: ExperimentConfig, *, run_id: str | None = None) -> dict[str, Any]:
    """Run one experiment and return the results mapping, with the report already written.

    Every step records its refusals. A run that could not estimate, could not fit, or could not
    attack records that with a reason — because a results file that lists only successes cannot be
    distinguished from one where the missing work was never attempted.
    """
    started = time.time()
    seeds = RunSeeds(root=root_from_environment(config.instance.seed))
    identifier = run_id or config.run_id or (
        f"{config.instance.source.value}-d{config.instance.target_dimension}-s{seeds.root}"
    )
    run_dir = Path(config.output.dir) / identifier

    results: dict[str, Any] = {
        "run_id": identifier,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "seed": seeds.root,
        "config": dump_config(config),
        "not_run": [],
        "notes": [],
    }

    if config.instance.source is InstanceSource.PUBLISHED_REFERENCE:
        scheme = config.instance.reference_scheme
        if not scheme:
            raise ValueError("published_reference needs instance.reference_scheme set")
        known = PUBLISHED_LWE_SCHEMES + PUBLISHED_SIS_SCHEMES
        if scheme not in known:
            raise ValueError(f"unknown published scheme {scheme!r}; known: {list(known)}")
        report = estimate(
            reference_parameter_set(scheme),
            models=tuple(config.cost_model.models),
            quantum_sieving_speedup=config.cost_model.quantum_sieving_speedup,
        )
        results["instance"] = {"label": "published_reference", "scheme": scheme}
        results["estimator_same_scale"] = _jsonable(report)
        results["notes"].append(
            "A published reference set: the estimator validating itself. No lattice attack runs "
            "here, because these parameters are published rather than attacked."
        )
    else:
        instance = build_instance(config, seeds)
        results["instance"] = instance.describe()

        engine = _engine_for(config)
        attack_results = []
        minima: dict[str, int | None] = {}

        # The normal form is computed once and reused: it fixes both the dual lattice's dimension
        # and the uSVP dimension the primal comparison is made at. It is cheap beside a reduction,
        # and two independent calls would be two chances for the two to disagree.
        normal_form = to_normal_form(instance)
        dimension_of = lattice_widths_by_family(normal_form)

        # The estimate comes *before* the attack now, because ``search_beyond_prediction`` bounds
        # the sweep by it. It is the same call on the same instance either way; only the order moved.
        report = _estimate_for(instance, config)

        # Two refusals are decided before any reduction, per block size, and both are recorded.
        #
        # The RAM budget: ``engine.ram_budget_gb`` was read nowhere, so a 1 MiB budget ran every
        # point. ``assert_within_ram_budget`` documents itself as belonging "at the point where a
        # block size is about to be attempted", and this is that point.
        #
        # The search bound: block sizes more than ``attack.search_beyond_prediction`` above the
        # estimator's uSVP block size are not attempted. They become rows only if nothing below
        # them recovered — a sweep that found its minimum never reached them, bound or no bound.
        predicted = getattr(report, "beta_usvp", None)
        search_limit = (
            None if predicted is None else predicted + config.attack.search_beyond_prediction
        )
        to_try: list[int] = []
        over_budget: list[dict[str, Any]] = []
        beyond_search: list[int] = []
        for block_size in sorted(config.attack.block_size_range):
            refusal = _refused_by_ram_budget(engine, block_size, config.engine.ram_budget_gb)
            if refusal is not None:
                over_budget.append(_not_run_primal_row(
                    block_size, dimension_of["primal_usvp"], engine, refusal
                ))
                results["not_run"].append({
                    "step": f"primal attack, block size {block_size}", "reason": refusal,
                })
            elif search_limit is not None and block_size > search_limit:
                beyond_search.append(block_size)
            else:
                to_try.append(block_size)

        if to_try:
            primal_min, primal_points = find_minimum_successful_block_size(
                instance, engine, to_try,
                max_seconds_per_block_size=config.attack.max_seconds_per_block_size,
            )
        else:
            primal_min, primal_points = None, []
        minima["primal_usvp"] = primal_min
        attack_results.extend(
            {
                "family": "primal_usvp",
                "block_size": r.block_size,
                "dimension": r.dimension,
                "recovered": r.recovered,
                "wall_clock_s": r.wall_clock_s,
                "root_hermite_factor": r.root_hermite_factor,
                # Carried, not dropped. ``engine`` and ``threads`` decide whether this point is a
                # measurement or a single draw: G6K is bit-reproducible at one thread and is not
                # above it, so a minimum block size found at four threads cannot be re-derived from
                # its recorded seed. A record holding only the number makes the two look the same.
                "engine": r.engine,
                "threads": r.threads,
                "provenance": r.provenance,
                "not_run_reason": r.not_run_reason,
            }
            for r in primal_points
        )
        if primal_min is None:
            attack_results.extend(
                _not_run_primal_row(
                    block_size, dimension_of["primal_usvp"], engine,
                    f"block size {block_size} is more than attack.search_beyond_prediction="
                    f"{config.attack.search_beyond_prediction} above the estimator's predicted "
                    f"uSVP block size {predicted}; the search gave up at {search_limit}. Not a "
                    "failure — the point was not attempted.",
                )
                for block_size in beyond_search
            )
        attack_results.extend(over_budget)

        if any(t.value == "dual" for t in config.attack.types):
            # The block size has to be clamped to the *dual* lattice's dimension, which is the
            # sample count after normalisation — not the embedded dimension the primal attack uses,
            # and not the config's maximum. Measured: at the shipped config the dual lattice is 58
            # wide while the block-size range reaches 80, so the request is refused by the engine on
            # a limit that does not apply to this attack.
            dual_dimension = normal_form.m
            dual_block_size = min(max(config.attack.block_size_range), dual_dimension)
            minima["dual"] = None
            dual_refusal = _refused_by_ram_budget(
                engine, dual_block_size, config.engine.ram_budget_gb
            )
            if dual_refusal is not None:
                # The same budget, the same point: before the reduction. Nothing ran, so the row
                # carries no time and no advantage — only the refusal and the lattice it was for.
                attack_results.append({
                    "family": "dual",
                    "block_size": dual_block_size,
                    "dimension": dual_dimension,
                    "recovered": False,
                    "advantage": 0.0,
                    "wall_clock_s": 0.0,
                    "provenance": NOT_RUN,
                    "not_run_reason": dual_refusal,
                })
                results["not_run"].append({"step": "dual attack", "reason": dual_refusal})
            else:
                dual = run_dual_attack(instance, engine, dual_block_size)
                attack_results.append({
                    "family": "dual",
                    "block_size": dual.block_size,
                    "dimension": dual.dimension,
                    "recovered": False,
                    "advantage": dual.advantage,
                    "wall_clock_s": dual.wall_clock_s,
                    "provenance": dual.provenance,
                    "not_run_reason": dual.not_run_reason,
                })
                if dual.provenance == NOT_RUN:
                    results["not_run"].append({
                        "step": "dual attack",
                        "reason": dual.not_run_reason,
                    })

        results["attacks"] = attack_results
        results["minimum_block_sizes"] = minima

        if report is None:
            results["not_run"].append({"step": "cost estimation", "reason": "disabled in config"})
        else:
            results["estimator_same_scale"] = _jsonable(report)
            # Each family is compared at the width of the lattice it reduces — see
            # `lattice_widths_by_family`, which carries the reasoning and the identity.
            comparisons = []
            for family in ("primal_usvp", "dual"):
                if family not in (m for m in config.cost_model.models) and family != "primal_usvp":
                    continue
                comparisons.append(
                    _jsonable(
                        compare_block_sizes(
                            dimension=dimension_of[family],
                            measured_min_block_size=minima.get(family),
                            report=report,
                            family=family,
                        )
                    )
                )
            results["comparisons"] = comparisons

            measured = [
                r for r in primal_points if r.provenance == MEASURED and r.wall_clock_s > 0
            ]
            if len(measured) >= 3:
                frame = measurements_to_frame(measured)
                try:
                    fitted = fit_core_svp_model(frame)
                    results["scaling"] = _jsonable(fitted.model)
                except Exception as exc:  # noqa: BLE001
                    results["not_run"].append({"step": "scaling fit", "reason": str(exc)})
            else:
                results["not_run"].append({
                    "step": "scaling fit",
                    "reason": (
                        f"{len(measured)} usable measured point(s); a fit needs at least 3, since "
                        "two determine a line exactly and it could not be contradicted by its own "
                        "data"
                    ),
                })

    results["seeds"] = seeds.to_dict()
    results["environment"] = _environment_summary()

    if "png" in config.output.formats and not _measured_primal_points(results):
        results["not_run"].append({
            "step": "figures",
            "reason": "output.formats asks for png, and this run has no measured primal point to draw",
        })

    _write_outputs(run_dir, config, results)
    results["run_dir"] = str(run_dir)
    return results


def run_sweep(config: ExperimentConfig) -> list[dict[str, Any]]:
    """Run one experiment per dimension in the sweep, refusing over-budget points.

    Each point is a full run, so a refusal is recorded as its own result rather than aborting the
    sweep: a sweep that stops at the first point it cannot run reports a shorter range as though it
    were the configured one.
    """
    outcomes = []
    for dimension in config.sweep.dimension_range:
        if dimension > 200 and not config.sweep.long_run_opt_in:
            outcomes.append({"dimension": dimension, "provenance": NOT_RUN,
                             "reason": "above the dimension limit; set long_run_opt_in to exceed it"})
            continue
        point = config.model_copy(update={
            "instance": config.instance.model_copy(update={"target_dimension": dimension}),
            "run_id": None,
        })
        try:
            outcomes.append(run_experiment(point))
        except Exception as exc:  # noqa: BLE001
            outcomes.append({"dimension": dimension, "provenance": NOT_RUN,
                             "reason": f"{type(exc).__name__}: {exc}"})

    _fit_across_the_sweep(outcomes, config)
    return outcomes


def _fit_across_the_sweep(outcomes: list[dict[str, Any]], config: ExperimentConfig) -> None:
    """Fit the cost model across dimensions, and write it into each run's results.

    **Where the evidence actually is.** The design document's fit is over
    ``(dimension, minimum successful block size, wall-clock time)`` triples — across dimensions. A
    per-run fit cannot supply that: a run stops at its first success, so it contributes one or two
    points, below the three-point floor, and correctly refuses. Exercising a sweep is what surfaced
    the difference between "the fit works" (tested against a known slope) and "a sweep feeds it".

    The per-dimension minima and their costs are written back into each run's ``metrics.json`` and
    report, so a run records the fit it participates in rather than only the fit it could make alone.

    **A refused fit is written back too.** It used to be appended to the in-memory outcomes only, so
    the stored record of a two-dimension sweep did not say a cross-sweep fit had been refused — the
    silent omission every other step of this pipeline is written to avoid.
    """
    import pandas as pd

    import math

    rows = []
    for outcome in outcomes:
        minimum = (outcome.get("minimum_block_sizes") or {}).get("primal_usvp")
        if outcome.get("provenance") == NOT_RUN or minimum is None:
            continue
        dimension = outcome.get("instance", {}).get("qary_lattice_dimension")
        if dimension is None:
            continue
        attacks = [
            a for a in outcome.get("attacks", [])
            if a.get("family") == "primal_usvp"
            and a.get("provenance") == MEASURED
            and (a.get("wall_clock_s") or 0) > 0
        ]
        succeeded = [a for a in attacks if a.get("recovered")] or attacks
        cost = max(a["wall_clock_s"] for a in succeeded) if succeeded else 0.0
        rows.append({
            "dimension": int(dimension),
            "block_size": int(minimum),
            "wall_clock_s": cost,
            "log2_cost": math.log2(cost) if cost > 0 else None,
        })

    if len(rows) < 3:
        for outcome in outcomes:
            if isinstance(outcome, dict) and "run_id" in outcome:
                outcome.setdefault("not_run", []).append({
                    "step": "scaling fit",
                    "reason": (
                        f"{len(rows)} dimension(s) reached a minimum block size; a fit across the "
                        "sweep needs at least 3. Dimensions where the attack did not reach within "
                        "the configured block-size range contribute no point — that is the range "
                        "being too short rather than the fit failing."
                    ),
                })
                _rewrite_record(outcome, config)
        return

    frame = pd.DataFrame(rows)
    try:
        growth = fit_block_size_growth(frame)
    except Exception as exc:  # noqa: BLE001
        for outcome in outcomes:
            if isinstance(outcome, dict) and "run_id" in outcome:
                outcome.setdefault("not_run", []).append(
                    {"step": "block-size growth fit", "reason": str(exc)}
                )
                _rewrite_record(outcome, config)
        return

    # Core-SVP is applied at the *configured production dimension* when the config names one, and at
    # the sweep's own maximum otherwise. The cost is always labelled extrapolated, even where the
    # block size was interpolated from measurements — the block size may be a measured-relationship
    # output, but the cost is the model's, and calling it measured would be the blend the reports
    # exist to prevent.
    target_dimension = max(config.sweep.dimension_range)
    beta_at_target, _ = growth.block_size_at(target_dimension)
    cost_at_target, _ = growth.core_svp_log2_cost_at(target_dimension)

    for outcome in outcomes:
        if not isinstance(outcome, dict) or "run_id" not in outcome:
            continue
        outcome["scaling"] = {
            "kind": "block_size_growth",
            "measured": _jsonable(growth),
            "extrapolated": {
                "target_dimension": target_dimension,
                "predicted_block_size": beta_at_target,
                "core_svp_log2_cost": cost_at_target,
                "core_svp_c": 0.292,
                "provenance": EXTRAPOLATED,
            },
            "scope": (
                "fitted across the sweep: the required block size against lattice dimension, over "
                "the dimensions that reached one. Core-SVP is applied afterwards at the target "
                "dimension. The two steps are separate and separately labelled."
            ),
        }
        _rewrite_record(outcome, config)


def _rewrite_record(outcome: dict[str, Any], config: ExperimentConfig) -> None:
    """Rewrite one sweep point's stored record after the sweep has added to it.

    Both halves, every time: the report's sections 5 and 6 render what the sweep adds (the fit, or
    the refusal to fit), and a report regenerated from ``metrics.json`` has to match the one on
    disk — so neither file may be left describing the run as it stood before the sweep finished.
    """
    _write_outputs(Path(outcome["run_dir"]), config, outcome)


def _environment_summary() -> dict[str, Any]:
    """The toolchain a result was produced under, recorded beside the result."""
    import sys

    import fpylll

    summary: dict[str, Any] = {
        "python": sys.version.split()[0],
        "fpylll": fpylll.__version__,
    }
    try:
        import g6k

        summary["g6k"] = getattr(g6k, "__version__", "present")
    except ImportError:
        summary["g6k"] = "absent"
    try:
        from .analysis.cost_estimation import estimator_revision

        summary["estimator_revision"] = estimator_revision()
    except Exception:  # noqa: BLE001
        summary["estimator_revision"] = "unknown"
    return summary
