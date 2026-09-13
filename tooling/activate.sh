# Source me:  source tooling/activate.sh
#
# Portable activation for the verification environment of this repository.
# No machine-specific path appears in this file: the environment root is derived from
# this script's own location, so the tree can be cloned anywhere and still work.
#
#   PQT_ENV  environment root. Defaults to the directory holding this script, which is
#            where the rebuild guide (environment.md) builds venv/, liboqs/ and tools/.
#            Set it before sourcing only if the environment lives somewhere else.
#   PQT_SRC  a local copy of the read-only research tree the harnesses read their input
#            files from. It is not shipped with this repository and is never guessed here.
#
# Both are exported for the scripts in this repository; several of them read PQT_SRC.
#
# Export PQT_SRC on its own line before sourcing this file. `PQT_SRC=... source activate.sh`
# looks equivalent and is not: the assignment is undone when the source command returns, so the
# harnesses run afterwards see no PQT_SRC. `export PQT_SRC=...` on a line of its own persists.

_pqt_env="${PQT_ENV:-}"
if [ -z "$_pqt_env" ]; then
    _pqt_env="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
export PQT_ENV="$_pqt_env"

if [ -z "${PQT_SRC:-}" ]; then
    echo "activate.sh: PQT_SRC is unset - it must name a local copy of the read-only research tree that the harnesses read their input files from, so export it on a line of its own before sourcing this script (export PQT_SRC=/path/to/research-tree, then source tooling/activate.sh), because an assignment written on the same line as the source command is undone when that command returns (see tooling/README.md and tooling/environment.md)." >&2
else
    export PQT_SRC
fi

if [ -f "$PQT_ENV/venv/bin/activate" ]; then
    . "$PQT_ENV/venv/bin/activate"                              # python/python3/pip -> the pinned interpreter
else
    echo "activate.sh: no Python environment at $PQT_ENV/venv - create it as described in tooling/environment.md." >&2
fi

export PATH="$PQT_ENV/tools/bin:$PATH"                          # tamarin-prover, maude, proverif, dot
export MAUDE_LIB="$PQT_ENV/tools/maude-3.5.1"                   # prelude.maude and the rest of the Maude library
export OQS_INSTALL_PATH="$PQT_ENV/liboqs"                       # liboqs shared library: certificate demo and liboqs-python
export LD_LIBRARY_PATH="$PQT_ENV/liboqs/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$PQT_ENV/liboqs/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export PYTHONDONTWRITEBYTECODE=1                                # never write __pycache__ into the research tree
