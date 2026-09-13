#!/usr/bin/env python3
"""Preserve the previous review package and add this carrier experiment.

This is the procedure that produced the version 1.28 carrier package. It takes
the *previous* review package as an intact input and adds the carrier-generation
files. That input zip is a build product and is not retained in this repository,
so it must be supplied with `--previous`; the added members are read from the
locations the file map gives them (`history/v1.28`, `src/adapter`, `fixtures`,
`results`). The vendored tree and the compiled binaries were members of the
recorded package and are excluded here, so the member list is not identical.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAIN = HERE.parent
RENAMED = ('README.md', 'SOURCE_MANIFEST.json', 'PACKAGE_VALIDATION.json', 'reproduce.sh')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', required=True, type=Path,
                        help='the retained version 1.27 carrier/review package (not in this repository)')
    parser.add_argument('--output', required=True, type=Path, help='the .zip to write')
    args = parser.parse_args()
    members = {}
    with zipfile.ZipFile(args.previous) as z:
        assert z.testzip() is None
        for name in z.namelist():
            out = 'history/v1.27_' + name if name in RENAMED else name
            members[out] = z.read(name)
    for folder in ('history/v1.28', 'src/adapter', 'fixtures', 'results'):
        for p in sorted((DOMAIN / folder).rglob('*')):
            if not p.is_file():
                continue
            if any(part in ('target', '__pycache__') or part.startswith('public-only-')
                   for part in p.relative_to(DOMAIN / folder).parts):
                continue
            if p.name == 'PRIVATE_TRACE_WITNESS.bin':
                raise RuntimeError('private member credential file present')
            if p.suffix == '.expanded':
                continue
            members[str(p.relative_to(DOMAIN))] = p.read_bytes()
    members['README.md'] = (DOMAIN / 'history/v1.28/assessment.md').read_bytes()
    members['reproduce.sh'] = (DOMAIN / 'history/v1.28/reproduce.sh').read_bytes()
    manifest = []
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(members.items()):
            assert Path(name).name != 'PRIVATE_TRACE_WITNESS.bin'
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            z.writestr(name, data)
            manifest.append({'path': name, 'bytes': len(data),
                             'sha256': hashlib.sha256(data).hexdigest()})
        z.writestr('SOURCE_MANIFEST.json', json.dumps({
            'scope': 'All members except this manifest and the subsequent package-validation '
                     'record; the vendored upstream tree and the compiled binaries of the '
                     'recorded package are excluded from this repository',
            'files': manifest}, indent=2) + '\n')
    assert args.output.stat().st_size < 50 * 1024 * 1024
    print(json.dumps({'file': str(args.output), 'bytes': args.output.stat().st_size,
                      'members': len(members) + 1, 'preserved_prior_review_members': True}))


if __name__ == '__main__':
    main()
