#!/usr/bin/env python3
"""Check, or install from a supplied copy, the single pinned binary dependency.

The CEQS29 component needs the `pqcrypto` bindings for ML-KEM-1024 and ML-DSA-87.
The wheel that was used is a third-party compiled artefact and is not retained in
this repository; its name, byte size and sha256 are pinned below and recorded in
`docs/provenance.md` and `results/dependency-provenance.json`.

Without arguments the script only checks that the pinned package is importable,
which is the case in the documented verification environment. To install it into
a private `vendor/` directory instead, obtain the pinned wheel and pass it with
`--wheel`; the sha256 is verified before anything is installed.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = 'pqcrypto-0.3.4-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl'
SHA256 = 'b2f9bad43a1e3970f55e6f68fc1864595c9b0c6e53638aa8393b1d01216a6ebb'
BYTES = 27036304


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path,
                        help='a local copy of ' + NAME)
    parser.add_argument('--target', type=Path, default=HERE / 'vendor',
                        help='directory to install into when --wheel is given')
    args = parser.parse_args()
    if args.wheel is None:
        try:
            import pqcrypto
        except ImportError:
            raise SystemExit(
                'pqcrypto is not importable, and no --wheel was given.\n'
                'Pinned dependency: ' + NAME + '\n'
                'sha256 ' + SHA256 + ', ' + str(BYTES) + ' bytes.\n'
                'That wheel is a third-party compiled artefact and is not retained in this\n'
                'repository (see docs/provenance.md). Install the pinned version in your\n'
                'environment, or re-run with --wheel pointing at a copy of that file.')
        print('pqcrypto already importable from ' + str(Path(pqcrypto.__file__).resolve().parent)
              + '; nothing installed')
        return
    digest = hashlib.sha256(args.wheel.read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit('dependency hash mismatch: expected ' + SHA256 + ', got ' + digest)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index', '--no-deps',
                    '--upgrade', '--target', str(args.target), str(args.wheel)], check=True)


if __name__ == '__main__':
    main()
