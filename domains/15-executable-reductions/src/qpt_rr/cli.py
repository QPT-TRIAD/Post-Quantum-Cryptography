"""Command line: run the reductions, print the report."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from . import __version__
from .campaign import NOT_RUNNABLE, run_campaign
from .reporting import render_report
from .scope import SCOPE_BOUNDARY

app = typer.Typer(add_completion=False, help=__doc__)


@app.command()
def scope() -> None:
    """Print what running a reduction can and cannot establish."""
    typer.echo(SCOPE_BOUNDARY)


@app.command()
def gaps() -> None:
    """List the parts of the record's argument this runner cannot execute."""
    for title, why in NOT_RUNNABLE:
        typer.echo(f"- {title}\n    {why}")


@app.command()
def run(out: Path = typer.Option(..., help="directory for results.json and report.md"),
        n: int = typer.Option(8, help="field size in bits; not divisible by 3; production is 256"),
        trials: int = typer.Option(200, help="trials per experiment"),
        seed: int = 20260921) -> None:
    """Run every reduction against every adversary and write the report."""
    if n % 3 == 0 or n < 4:
        raise typer.BadParameter("n must be at least 4 and not divisible by 3")
    results = run_campaign(n=n, trials=trials, seed=seed,
                           progress=lambda message: typer.echo(message, err=True))
    meta = {"n": n, "trials": trials, "seed": seed, "version": __version__,
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(
        {"meta": meta, "scope_boundary": SCOPE_BOUNDARY, "not_runnable": NOT_RUNNABLE,
         "results": [r.to_dict() for r in results]}, indent=1, default=str))
    report = render_report(results, meta=meta)
    (out / "report.md").write_text(report)
    typer.echo(report)


def main() -> None:                                                # pragma: no cover
    app()


if __name__ == "__main__":                                        # pragma: no cover
    main()
