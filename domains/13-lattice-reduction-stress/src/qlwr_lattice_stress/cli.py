"""Command-line front end. A thin wrapper: every command is a library call with arguments bound.

The design document asks for this shape and the reason is reproducibility — a result should be
reproducible by calling the same function, not by reconstructing the command line someone typed.
``scripts/run_experiment.py`` and ``scripts/sweep_dimensions.py`` are two-line wrappers over the
same entry points, so the library path is the one that gets exercised.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from .config.schema import load_config

app = typer.Typer(add_completion=False, help="Lattice-reduction stress test for a scaled QLWR instance.")


@app.command()
def probe() -> None:
    """Run the milestone-0 API probe: every third-party API this project calls, executed."""
    from .utils.api_probe import format_report, probe_all, required_failures

    checks = probe_all()
    typer.echo(format_report(checks))
    raise typer.Exit(1 if required_failures(checks) else 0)


@app.command()
def run(
    config: Path = typer.Option(..., "--config", "-c", exists=True, dir_okay=False),
    run_id: str | None = typer.Option(None, "--run-id"),
) -> None:
    """Run one experiment from a config, writing results and a report."""
    from .pipeline import run_experiment

    loaded = load_config(config)
    results = run_experiment(loaded, run_id=run_id)

    typer.echo(f"run id     : {results['run_id']}")
    typer.echo(f"run dir    : {results['run_dir']}")
    if "instance" in results:
        typer.echo(f"instance   : {results['instance'].get('label')} "
                   f"nu={results['instance'].get('nu')} m={results['instance'].get('m')}")
    minima = results.get("minimum_block_sizes") or {}
    if minima:
        typer.echo("minimum block size by family:")
        for family, value in minima.items():
            typer.echo(f"  {family:12s} {value if value is not None else 'not reached'}")
    for refusal in results.get("not_run", []):
        typer.echo(f"not run    : {refusal['step']} — {refusal['reason']}")


@app.command()
def sweep(config: Path = typer.Option(..., "--config", "-c", exists=True, dir_okay=False)) -> None:
    """Run the configured dimension sweep, one experiment per point."""
    from .pipeline import run_sweep

    loaded = load_config(config)
    outcomes = run_sweep(loaded)
    for outcome in outcomes:
        if outcome.get("provenance") == "not_run":
            typer.echo(f"  dimension {outcome.get('dimension')}: not run — {outcome.get('reason')}")
            continue
        minima = outcome.get("minimum_block_sizes") or {}
        summary = ", ".join(f"{k}={v}" for k, v in minima.items())
        typer.echo(f"  dimension {outcome['instance'].get('qary_lattice_dimension')}: {summary}")


@app.command()
def report(
    run_dir: Path = typer.Argument(..., exists=True, file_okay=False),
) -> None:
    """Regenerate a report from a stored results directory."""
    from .reporting import generate_report_from_run_dir

    typer.echo(f"wrote {generate_report_from_run_dir(run_dir)}")


@app.command("planted-check")
def planted_check(
    dimension: int = typer.Option(76, "--dimension", "-d"),
    seed: int = typer.Option(1, "--seed"),
) -> None:
    """The load-bearing check: is the planted vector in the lattice, and is it the shortest?

    Runs before any reduction, in seconds, at any dimension — and it is the cheapest thing that
    distinguishes a correct construction from one that is self-consistent and wrong.
    """
    import random

    from .lattice.basis_construction import build_primal_embedding_basis
    from .lattice.planted_vector import assert_in_lattice, planted_norm_squared, planted_short_vector
    from .lattice.primal_embedding import calibrate_embedding_factor
    from .problem.normal_form import to_normal_form
    from .problem.qlwr_instance import LatticeQLWRInstance, full_column_rank_mod

    q, p, nu = 1 << 16, 1 << 8, max(2, round(dimension * 256 / 608))
    rng = random.Random(seed)
    while True:
        base = tuple(tuple(rng.randrange(q) for _ in range(nu)) for _ in range(dimension))
        if full_column_rank_mod([list(r) for r in base], q, nu) == nu:
            break
    instance = LatticeQLWRInstance(
        nu=nu, q_l=q, p=p, m=dimension,
        secret_s=tuple(rng.randrange(q) for _ in range(nu)), base=base, seed=seed,
    )
    nf = to_normal_form(instance)
    factor, measurement = calibrate_embedding_factor(nf)
    basis = build_primal_embedding_basis(nf, embedding_factor=factor)
    planted = planted_short_vector(nf, embedding_factor=factor)

    assert_in_lattice(list(planted), basis)
    typer.echo(f"dimension       : {dimension} (nu={nu}, embedded {basis.nrows})")
    typer.echo(f"embedding factor: {factor}  (analytic bound {measurement['analytic_lower_bound']})")
    typer.echo(f"planted ||v||^2 : {planted_norm_squared(nf, embedding_factor=factor)}")
    typer.echo(f"artifact (p*M)  : {measurement['artifact_norm']}  "
               f"exceeds planted: {measurement['artifact_exceeds_planted']}")
    typer.echo("membership      : exact integer combination of the basis rows")


@app.command("estimate")
def estimate_command(
    scheme: str = typer.Option("Kyber512", "--scheme"),
) -> None:
    """Run the cost model against a published parameter set — the estimator validating itself."""
    from .analysis.cost_estimation import estimate, reference_parameter_set

    report = estimate(reference_parameter_set(scheme))
    typer.echo(json.dumps({
        "scheme": scheme,
        "usvp_beta": report.beta_usvp,
        "dual_beta": report.beta_dual,
        "log2_rop_classical_min": report.rop_classical_log2_min,
        "log2_rop_quantum_min": report.rop_quantum_log2_min,
        "estimator_revision": report.estimator_revision,
    }, indent=2))


@app.command("production-estimate")
def production_estimate_command(
    samples: str = typer.Option(
        None, "--samples",
        help="'rows' or 'exposure'. Both are reported when this is omitted, because the corpus "
             "does not say which one a cost should be quoted against and the two are different "
             "amounts of data to an attack.",
    ),
) -> None:
    """Run the cost model against the **recorded production parameters**.

    This crosses the build's stop point deliberately. No lattice is built and no reduction runs:
    at nu = 256 the uSVP dimension is 609, far beyond this host. What it produces is the model's
    number, and it is a model's number — read it beside the same-scale comparison the scaled sweep
    supplies, which is what bounds how much the model can be trusted.

    Both sample readings are reported unless one is named, because a cost estimate is only
    meaningful alongside which reading it was made under.
    """
    from .analysis.cost_estimation import estimate, production_parameter_set
    from .problem.production_parameters import (
        PRODUCTION_NU,
        PRODUCTION_PARAMETER_SUMMARY,
        SAMPLE_COUNT_SATURATION,
        sample_count_readings,
        samples_after_normal_form,
    )

    readings = [samples] if samples else ["rows", "exposure"]
    out: dict = {"production_parameters": PRODUCTION_PARAMETER_SUMMARY(), "estimates": {}}
    for reading in readings:
        report = estimate(production_parameter_set(samples=reading))
        nf = samples_after_normal_form(reading)
        m = sample_count_readings()[reading]
        out["estimates"][reading] = {
            "samples_available": m,
            # Above the saturation point the primal cost is constant, so the two readings are not
            # two points on a curve with an unknown value between them — the higher one is a flat
            # region and the lower one is still on the slope. Reported because without it a reader
            # comparing the two rows sees a 17-bit gap and no way to tell which end is which. This
            # is a measurement (`scripts/sample_count_saturation.py`) pinned by a test, unlike the
            # dual-cap flag that was removed from this block for being a prediction about another
            # library's internals.
            "at_or_above_saturation": m >= SAMPLE_COUNT_SATURATION,
            "saturation_m_over_nu": round(SAMPLE_COUNT_SATURATION / PRODUCTION_NU, 4),
            # Reported per reading because it changes what the dual column means, and no downstream
            # consumer can recover it: the estimator normalises internally and never reports the
            # sample count it ended up with. Left as the count rather than as a flag about whether
            # the dual hit a cap — that cap is a fact about the estimator's internals, and a boolean
            # asserting it would be a prediction that breaks silently on an upgrade. The measurement
            # behind it is in `notes/10-production-estimate.md`.
            "samples_after_normal_form": nf,
            "usvp_beta": report.beta_usvp,
            "dual_beta": report.beta_dual,
            "log2_rop_classical_min": report.rop_classical_log2_min,
            "log2_rop_quantum_min": report.rop_quantum_log2_min,
            "minimum_over_models": report.minimum_over_models,
            "estimator_revision": report.estimator_revision,
            "provenance": report.provenance,
        }
    # The scope travels with the numbers in the same JSON, so a consumer that reads the estimates
    # and ignores the prose still receives what they are and are not.
    out["scope"] = (
        "Model outputs for the recorded production parameters. Not measured, and not a security "
        "claim about the scheme: this is the estimator's cost for an instance with these "
        "(n, q, m, error distribution), and its applicability at this scale is what the "
        "same-scale comparison in the scaled sweep tests."
    )
    out["what_this_number_is_for"] = PRODUCTION_PARAMETER_SUMMARY()["qlwr_status"]
    out["obligation_filled"] = PRODUCTION_PARAMETER_SUMMARY()["qlwr_obligation_citations"]
    typer.echo(json.dumps(out, indent=2))


def main() -> int:
    app()
    return 0


if __name__ == "__main__":
    sys.exit(main())
