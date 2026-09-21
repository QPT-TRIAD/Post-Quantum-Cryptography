"""Command line: the raw primitives, the attacks, and the campaign.

A thin wrapper — every command is one library call, so anything done here can be done from a test
or a notebook. ``keygen`` / ``respond`` / ``verify`` expose the key map, ``trace-keygen`` /
``trace-verify`` expose the QLWR trace, ``export-*`` hand an instance to an external tool,
``attack`` runs one attack once, and ``campaign`` maps the workload curves and writes the report.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer

from . import __version__
from .harness import PROFILES, run_campaign
from .primitives.keymap import HandleMode, KeyMapScheme, Opening, ScalingRule, Transcript
from .primitives.qlwr_trace import QlwrTrace
from .reporting import render_report
from .scope import SCOPE_BOUNDARY

app = typer.Typer(add_completion=False, help=__doc__.split("\n\n")[0])


def _scheme(n: int, mode: str, expansion: int) -> KeyMapScheme:
    try:
        return KeyMapScheme(n, HandleMode(mode.upper()), rule=ScalingRule(production_expansion=expansion))
    except ValueError as error:
        raise typer.BadParameter(str(error))


def _emit(payload: dict) -> None:
    typer.echo(json.dumps(payload, indent=1))


@app.command()
def scope() -> None:
    """Print what this tester can and cannot establish."""
    typer.echo(SCOPE_BOUNDARY)


@app.command()
def keygen(n: int = typer.Option(..., help="field size in bits; production is 256"),
           mode: str = typer.Option("B", help="handle: A (linear) or B (r^7)"),
           seed: int = 1, expansion: int = typer.Option(300, help="E at n = 256; the record uses 300 and 512")):
    """Key map: a random opening (s, r) and its public key Y = F(s | r << n)."""
    scheme = _scheme(n, mode, expansion)
    opening, public_key = scheme.keygen(seed)
    _emit({"n": n, "mode": scheme.mode.value, "equations": scheme.m_eqs, "expansion": scheme.expansion,
           "secret": {"s": opening.s, "r": opening.r}, "public_key": public_key})


@app.command()
def respond(n: int = typer.Option(...), s: int = typer.Option(...), r: int = typer.Option(...),
            challenge: int = typer.Option(...), mode: str = "B", expansion: int = 300):
    """Key map: the handle Z = G(r) + c*s for an opening and a challenge."""
    scheme = _scheme(n, mode, expansion)
    try:
        _emit({"handle": scheme.respond(Opening(s, r), challenge)})
    except ValueError as error:
        raise typer.BadParameter(str(error))


@app.command()
def verify(n: int = typer.Option(...), s: int = typer.Option(...), r: int = typer.Option(...),
           challenge: int = typer.Option(...), handle: int = typer.Option(...),
           public_key: int = typer.Option(...), mode: str = "B", expansion: int = 300):
    """Key map: does the opening satisfy both the public key and the handle? Exit 1 if not."""
    scheme = _scheme(n, mode, expansion)
    ok = scheme.verify(Transcript(public_key, challenge, handle), Opening(s, r))
    _emit({"valid": ok})
    raise typer.Exit(0 if ok else 1)


@app.command("trace-keygen")
def trace_keygen(nu: int = typer.Option(..., help="secret dimension; production is 256"), seed: int = 1):
    """QLWR trace: a secret s and its public trace b = round_p(X s)."""
    trace = QlwrTrace(nu, seed=seed)
    secret = trace.keygen()
    _emit({"nu": nu, "q": trace.q, "p": trace.p, "rows": trace.m, "secret": list(secret),
           "public_trace": list(trace.trace(secret))})


@app.command("trace-verify")
def trace_verify(nu: int = typer.Option(...), seed: int = 1,
                 secret: str = typer.Option(..., help="comma-separated integers")):
    """QLWR trace: does this secret reproduce the instance's public trace? Exit 1 if not."""
    trace = QlwrTrace(nu, seed=seed)
    candidate = tuple(int(v) for v in secret.split(","))
    ok = trace.verify(trace.trace(trace.keygen()), candidate)
    _emit({"valid": ok})
    raise typer.Exit(0 if ok else 1)


@app.command("export-system")
def export_system(out: Path, n: int = typer.Option(...), mode: str = "B", seed: int = 1,
                  expansion: int = 300):
    """Write the key-map framing problem as a Sage script, for any external algebraic solver."""
    from .export import export_boolean_system
    _emit(export_boolean_system(_scheme(n, mode, expansion), seed, out))


@app.command("export-lattice")
def export_lattice(out: Path, nu: int = typer.Option(...), seed: int = 1):
    """Write the QLWR primal-attack basis in fplll's format:  fplll -a bkz -b 20 <file>."""
    from .export import export_fplll_basis
    try:
        _emit(export_fplll_basis(QlwrTrace(nu, seed=seed), out))
    except RuntimeError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(2)


@app.command()
def attack(track: str = typer.Argument(..., help="a track key, e.g. keymap_b_brute_force"),
           size: int = typer.Option(...), seed: int = 1, max_seconds: float = 300.0, expansion: int = 300):
    """Run one attack once and print its result, including whether the recovered secret verified."""
    from .harness import _run_one
    try:
        _emit(_run_one((track, size, seed, max_seconds, expansion)).to_dict())
    except ValueError as error:
        raise typer.BadParameter(str(error))


@app.command()
def campaign(out: Path = typer.Option(..., help="directory for results.json and report.md"),
             scale: str = typer.Option("full", help=f"one of {PROFILES}"),
             expansion: int = typer.Option(300, help="E at n = 256: 300 (Python reference) or 512 (C prover, ledger)"),
             only: list[str] = typer.Option([], help="restrict subjects to these track keys; controls always run")):
    """Map the workload curves, gate them on the controls, and write the report."""
    if scale not in PROFILES:
        raise typer.BadParameter(f"scale must be one of {PROFILES}")
    outcomes = run_campaign(scale, expansion=expansion, only=tuple(only),
                            progress=lambda message: typer.echo(message, err=True))
    meta = {"scale": scale, "expansion": expansion, "version": __version__,
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(
        {"meta": meta, "scope_boundary": SCOPE_BOUNDARY,
         "tracks": [o.to_dict() for o in outcomes]}, indent=1, default=str))
    report = render_report(outcomes, meta=meta)
    (out / "report.md").write_text(report)
    typer.echo(report)


@app.command()
def report(results: Path = typer.Argument(..., help="a results.json written by `campaign`"),
           out: Path = typer.Option(None, help="where to write the report; default beside the results")):
    """Re-render the report from stored results — no attack is re-run, no number changes."""
    from .harness import TrackOutcome
    data = json.loads(results.read_text())
    outcomes = [TrackOutcome.from_dict(t) for t in data["tracks"]]
    text = render_report(outcomes, meta=data["meta"])
    (out or results.with_name("report.md")).write_text(text)
    typer.echo(text)


def main() -> None:                                                # pragma: no cover
    app()


if __name__ == "__main__":                                        # pragma: no cover
    main()
