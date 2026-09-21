#!/usr/bin/env python3
"""Relocate the G6K and lattice-estimator checkouts out of the read-only research tree.

They were built in place under the read-only research tree, which this project never modifies and
which carries its own publication gate. Both import only from their checkout directory, so the
project cannot depend on them where they sit. That tree is not part of this repository: set
``QLS_SOURCE_ROOT`` to a checkout of it before re-running this script.

The sequence is **copy -> verify -> install -> delete**, never a move. Each stage is checked before
the next runs, and the deletion stage will not run without an explicit flag, because deleting out of
a tree the project is forbidden to touch is the one irreversible act here.

Why a ``.pth`` and not ``pip install -e``: the build system is *not* relocatable even though the
binaries are. ``Makefile`` bakes the original path for ``ACLOCAL``/``AUTOCONF`` and ``config.status``
records ``ac_pwd``, so an editable install -- whose ``build_ext`` runs ``make`` unconditionally --
would likely fail on a stale aux-script path. The compiled extensions have no RPATH and link only
system libraries, so a path entry is sufficient and touches nothing. ``--pip-install`` is offered
for completeness; ``--rebuild`` is the last resort.

Usage::

    python scripts/move_tools.py                  # copy + verify + install
    python scripts/move_tools.py --verify         # re-check the current state
    python scripts/move_tools.py --confirm-delete # remove the originals (after verifying)
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

#: The tree the two tools were originally built in. It is not published with this repository, so it
#: has no default here: the script reports a clear error rather than acting on a guessed path.
SOURCE_ROOT = Path(os.environ["QLS_SOURCE_ROOT"]) if os.environ.get("QLS_SOURCE_ROOT") else None
TOOLS = ("g6k", "lattice-estimator")
DEST_ROOT = Path.home() / "Documents" / "lattice-tools"
PTH_NAME = "qlwr-lattice-tools.pth"


def site_packages() -> Path:
    """This interpreter's *own* site-packages, never the user-site directory.

    Walking ``sys.path`` and taking the first ``site-packages`` finds ``~/.local/lib/...`` first on
    this box, and a ``.pth`` written there applies to every Python 3.12 interpreter the user runs --
    including the system one. That would put G6K on the path of interpreters this project has
    nothing to do with. ``sysconfig`` reports the environment the interpreter actually belongs to.
    """
    import sysconfig

    purelib = Path(sysconfig.get_paths()["purelib"])
    if "miniforge3/envs/sage" not in str(purelib):
        raise RuntimeError(
            f"expected to install into the sage env, but purelib resolved to {purelib}; "
            "run this with ~/miniforge3/envs/sage/bin/python"
        )
    return purelib


def copy_stage(force: bool = False) -> dict[str, str]:
    """Copy each checkout. Idempotent: an existing copy is left alone unless ``force``."""
    out = {}
    DEST_ROOT.mkdir(parents=True, exist_ok=True)
    for name in TOOLS:
        src, dst = SOURCE_ROOT / name, DEST_ROOT / name
        if dst.exists() and not force:
            out[name] = "copy already present, left as is"
            continue
        if not src.exists():
            out[name] = "SOURCE MISSING (already deleted?)"
            continue
        shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
        out[name] = f"copied {src} -> {dst}"
    return out


def verify_stage() -> dict[str, tuple[bool, str]]:
    """Import and *run* each tool from its copy, with the research tree off ``sys.path``.

    Running matters as much as importing: a checkout whose extension modules were built against a
    particular location would import and then fail at first use. The assertions below execute a real
    sieving tour and a real cost estimate.
    """
    results: dict[str, tuple[bool, str]] = {}
    script = r"""
import sys, json
forbidden = [p for p in sys.path if "Documents/PQT" in p]
if forbidden:
    print(json.dumps({"ok": False, "detail": f"research tree on sys.path: {forbidden}"})); raise SystemExit
try:
    import cysignals.signals
    from g6k import Siever
    from fpylll import IntegerMatrix, LLL
    from g6k.algorithms.bkz import pump_n_jump_bkz_tour as bkz
    from g6k.utils.stats import dummy_tracer
    d = 40
    A = IntegerMatrix(d, d, int_type="mpz"); A.randomize("qary", k=d // 2, bits=10); LLL.reduction(A)
    n0 = sum(float(A[0, j]) ** 2 for j in range(d))
    bkz(Siever(A), dummy_tracer, 20)
    n1 = sum(float(A[0, j]) ** 2 for j in range(d))
    assert n1 <= n0, "sieving tour did not shrink the basis"
    print(json.dumps({"ok": True, "detail": "sieving BKZ shrank |b1|"}))
except Exception as e:
    print(json.dumps({"ok": False, "detail": f"{type(e).__name__}: {e}"}))
"""
    est_script = r"""
import sys, json
forbidden = [p for p in sys.path if "Documents/PQT" in p]
if forbidden:
    print(json.dumps({"ok": False, "detail": f"research tree on sys.path: {forbidden}"})); raise SystemExit
try:
    from estimator import LWE, schemes
    r = LWE.estimate(schemes.Kyber512, quiet=True)
    assert r["usvp"]["beta"] == 406, f"usvp beta={r['usvp']['beta']}, expected 406"
    print(json.dumps({"ok": True, "detail": "Kyber512 usvp beta=406 reproduced"}))
except Exception as e:
    print(json.dumps({"ok": False, "detail": f"{type(e).__name__}: {e}"}))
"""
    import json

    for name, code in (("g6k", script), ("lattice-estimator", est_script)):
        proc = subprocess.run(
            [sys.executable, "-B", "-c", code],
            capture_output=True, text=True, cwd="/tmp",
            env={**__import__("os").environ, "PYTHONPATH": str(DEST_ROOT / name)},
        )
        try:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
            results[name] = (payload["ok"], payload["detail"])
        except Exception:  # noqa: BLE001
            results[name] = (False, f"verifier produced no verdict: {proc.stdout[-200:]} {proc.stderr[-200:]}")
    return results


def install_stage() -> str:
    """Write one ``.pth`` naming both checkout directories. Idempotent."""
    pth = site_packages() / PTH_NAME
    body = "# qlwr-lattice-stress: relocated tool checkouts (see scripts/move_tools.py)\n" + "".join(
        f"{DEST_ROOT / name}\n" for name in TOOLS
    )
    pth.write_text(body)
    return f"wrote {pth}"


def check_import_without_pythonpath() -> dict[str, tuple[bool, str]]:
    """The real gate: import both tools with no ``PYTHONPATH`` and an unrelated cwd."""
    import json
    import os

    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    code = r"""
import sys, json
forbidden = [p for p in sys.path if "Documents/PQT" in p]
if forbidden:
    print(json.dumps({"ok": False, "detail": f"research tree on sys.path: {forbidden}"})); raise SystemExit
try:
    import cysignals.signals, g6k
    from estimator import LWE
    print(json.dumps({"ok": True, "detail": f"g6k <- {g6k.__file__}"}))
except Exception as e:
    print(json.dumps({"ok": False, "detail": f"{type(e).__name__}: {e}"}))
"""
    proc = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, cwd="/tmp", env=env)
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
        return {"both": (payload["ok"], payload["detail"])}
    except Exception:  # noqa: BLE001
        return {"both": (False, f"no verdict: {proc.stdout[-200:]} {proc.stderr[-200:]}")}


def delete_stage() -> str:
    """Remove the originals. Only ever called after every other stage has passed."""
    removed = []
    for name in TOOLS:
        target = SOURCE_ROOT / name
        if target.exists():
            shutil.rmtree(target)
            removed.append(str(target))
    return f"removed {removed}" if removed else "nothing to remove (already gone)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true", help="re-check the current state and exit")
    ap.add_argument("--confirm-delete", action="store_true", help="remove the originals from the research tree")
    ap.add_argument("--force-copy", action="store_true", help="re-copy even if the destination exists")
    ap.add_argument("--pip-install", action="store_true", help="use pip install -e instead of a .pth")
    args = ap.parse_args()

    # Every stage but --verify reads the original tree, which this repository does not carry.
    if SOURCE_ROOT is None and not args.verify:
        print("QLS_SOURCE_ROOT is not set. The research tree these tools were built in is not part "
              "of this repository; point that variable at a checkout of it, or run --verify to "
              "check an installation that is already in place.")
        return 2

    if not args.verify:
        for name, detail in copy_stage(args.force_copy).items():
            print(f"  copy    {name:20s} {detail}")

    print("\n  verify (copies, research tree off the path):")
    results = verify_stage()
    for name, (ok, detail) in results.items():
        print(f"    [{'ok' if ok else 'FAIL'}] {name:20s} {detail}")
    if not all(ok for ok, _ in results.values()):
        print("\n  Verification failed. Nothing was deleted and nothing was installed.")
        return 1

    if args.verify:
        print("\n  current state verified; no changes made")
        return 0

    if args.pip_install:
        for name in TOOLS:
            print(f"\n  pip install -e {DEST_ROOT / name}")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", str(DEST_ROOT / name),
                 "--no-build-isolation", "--no-deps"],
                check=False,
            )
    else:
        print(f"\n  install {install_stage()}")

    print("\n  gate: import with no PYTHONPATH, cwd=/tmp")
    gate = check_import_without_pythonpath()
    for name, (ok, detail) in gate.items():
        print(f"    [{'ok' if ok else 'FAIL'}] {name:20s} {detail}")
    if not all(ok for ok, _ in gate.values()):
        print("\n  The import gate failed. The originals were NOT deleted.")
        return 1

    if args.confirm_delete:
        print(f"\n  delete  {delete_stage()}")
    else:
        where = (f"    {SOURCE_ROOT / 'g6k'}\n    {SOURCE_ROOT / 'lattice-estimator'}"
                 if SOURCE_ROOT is not None else
                 "    (set QLS_SOURCE_ROOT to name them; this repository does not carry that tree)")
        print(
            "\n  Both tools now import without the research tree on the path.\n"
            "  The originals are still in place. Re-run with --confirm-delete to remove them:\n"
            + where
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
