"""Hand the raw instances to external tools: ``fplll`` on the command line, a Sage session.

The point of stripping the primitives bare is that anyone's cryptanalysis tool can be pointed at
them, not only the attacks shipped here. Two formats:

* the key-map framing problem as a **Sage script** — a ``BooleanPolynomialRing`` and its equations,
  ready for ``ideal(...).groebner_basis()``, a SAT conversion, or whatever else;
* the QLWR trace's primal-attack lattice as an **fplll matrix file**, so that
  ``fplll -a bkz -b 20 basis.txt`` runs against exactly the basis the built-in attack reduces.

Both files carry the instance's public data only. The secret goes in a separate ``.secret.json``
so an attack script cannot read the answer by accident, and so a solver's output can be checked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .attacks.algebraic import boolean_system
from .attacks.lattice import lattice_engine_path
from .primitives.keymap import KeyMapScheme
from .primitives.qlwr_trace import QlwrTrace

__all__ = ["export_boolean_system", "export_fplll_basis"]


def export_boolean_system(scheme: KeyMapScheme, seed: int, out: Path) -> dict:
    opening, transcript = scheme.transcript(seed)
    ring, equations, _, _ = boolean_system(scheme, transcript)
    names = [str(g) for g in ring.gens()]
    body = [
        "# Key-map framing problem, exported by qpt-cart. Public data only.",
        f"# n = {scheme.n}, mode {scheme.mode.value}, E = {scheme.expansion}, "
        f"{len(equations)} equations in {len(names)} unknowns.",
        "# Usage:  sage -python this_file.py    (or load it in a Sage session)",
        "from sage.all import BooleanPolynomialRing",
        f"R = BooleanPolynomialRing(names={names!r})",
        "R.inject_variables(verbose=False)",
        "equations = [",
        *[f"    {eq}," for eq in equations],
        "]",
        "if __name__ == '__main__':",
        "    G = R.ideal(equations).groebner_basis()",
        "    print(G)",
        "",
    ]
    out.write_text("\n".join(body))
    secret_path = out.with_suffix(".secret.json")
    secret_path.write_text(json.dumps({"s": opening.s, "r": opening.r,
                                       "challenge": transcript.challenge,
                                       "handle": transcript.handle,
                                       "public_key": transcript.public_key}, indent=1))
    return {"system": str(out), "secret": str(secret_path), "unknowns": len(names),
            "equations": len(equations)}


def export_fplll_basis(trace: QlwrTrace, out: Path) -> dict:
    engine = lattice_engine_path()
    if engine is None:
        raise RuntimeError("the lattice-stress engine is needed to build the embedding; set "
                           "QPT_CART_LATTICE_ENGINE")
    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))
    from qlwr_lattice_stress.attacks.primal_attack import prepare_primal
    from qlwr_lattice_stress.problem.qlwr_instance import LatticeQLWRInstance

    secret = trace.keygen()
    instance = LatticeQLWRInstance(nu=trace.nu, q_l=trace.q, p=trace.p, m=trace.m,
                                   secret_s=secret, base=trace.matrix, seed=trace.seed)
    _, factor, basis, planted = prepare_primal(instance)
    rows = [[int(basis[i, j]) for j in range(basis.ncols)] for i in range(basis.nrows)]
    out.write_text("[" + "\n".join("[" + " ".join(map(str, row)) + "]" for row in rows) + "]\n")
    secret_path = out.with_suffix(".secret.json")
    secret_path.write_text(json.dumps({"secret": list(secret), "planted_short_vector": list(planted),
                                       "embedding_factor": factor}, indent=1))
    return {"basis": str(out), "secret": str(secret_path), "dimension": len(rows),
            "embedding_factor": factor,
            "planted_norm_squared": sum(v * v for v in planted)}
