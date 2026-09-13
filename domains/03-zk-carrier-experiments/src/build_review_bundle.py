#!/usr/bin/env python3
"""Assemble the focused public review bundle; private witness files are forbidden.

This is the procedure that produced the version 1.27 review package. Two of its
historical sources are not retained in this repository — the vendored upstream
tree `continuation_v1.17/binius64-source` (third-party source) and the compiled
adapter binaries under `*/bin/` — so the member list produced here is not
identical to the recorded package. Everything else is added from its retained
location, and the same private-material guards apply: a private trace witness or
an expanded proof aborts the build instead of being written into the archive.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAIN = HERE.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='the .zip to write')
    args = parser.parse_args()
    files = {}

    def add(path, name=None):
        assert path.is_file(), path
        assert path.name != 'PRIVATE_TRACE_WITNESS.bin', path
        key = name or str(path.relative_to(DOMAIN))
        assert key not in files, key
        files[key] = path

    for folder in ('history/v1.27', 'history/v1.27b'):
        for p in sorted((DOMAIN / folder).rglob('*')):
            if not p.is_file():
                continue
            if any(part in ('target', '.git', '__pycache__') or part.startswith('public-only-')
                   for part in p.relative_to(DOMAIN / folder).parts):
                continue
            if p.name == 'PRIVATE_TRACE_WITNESS.bin' or p.suffix == '.expanded':
                raise RuntimeError('private or intermediate proof expansion present: ' + str(p))
            add(p)
    for name in ('encode_case0.json', 'encode_case1.json', 'public_verification.json',
                 'assessment.md'):
        add(DOMAIN / 'history/v1.25' / name)
    add(DOMAIN / 'docs/method.md')
    add(DOMAIN / 'results/source-comparison.json')
    add(DOMAIN / 'results/recompute-final-checks.json')
    add(DOMAIN / 'src/prover_memory.patch')
    add(DOMAIN / 'docs/analysis-note.md')
    add(DOMAIN / 'history/v1.27b/assessment.md', 'README.md')
    add(DOMAIN / 'history/v1.27b/reproduce.sh', 'reproduce.sh')
    for p in sorted((DOMAIN / 'history/regeneration-check/fixture').rglob('*')):
        if p.is_file():
            if p.name == 'PRIVATE_TRACE_WITNESS.bin':
                raise RuntimeError('extra test private file present')
            add(p, 'regeneration_check/fixture/'
                + str(p.relative_to(DOMAIN / 'history/regeneration-check/fixture')))
    manifest = []
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, path in sorted(files.items()):
            data = path.read_bytes()
            z.writestr(name, data)
            manifest.append({'path': name, 'bytes': len(data),
                             'sha256': hashlib.sha256(data).hexdigest()})
        z.writestr('SOURCE_MANIFEST.json', json.dumps({
            'scope': 'Every primary member except this manifest and the subsequent '
                     'PACKAGE_VALIDATION.json; the vendored upstream tree and the compiled '
                     'binaries of the recorded package are excluded from this repository',
            'files': manifest}, indent=2) + '\n')
    assert args.output.stat().st_size < 50 * 1024 * 1024
    print(json.dumps({'file': str(args.output), 'bytes': args.output.stat().st_size,
                      'members': len(files) + 1, 'private_witness_files': 0,
                      'excluded_from_recorded_package': ['continuation_v1.17/binius64-source',
                                                         'compiled adapter binaries']}))


if __name__ == '__main__':
    main()
