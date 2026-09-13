#!/usr/bin/env python3
"""Preserve the prior package and add the new reproducible component.

This is the procedure that produced the version 1.29 package. It takes the
previous carrier package as an intact input and adds the CEQS29 component. That
input zip is a build product and is not retained in this repository, so it must
be supplied with `--previous`; the added members are read from the locations the
file map gives them (`src/`, `results/`, `docs/`). No private material is added,
and no new complete quorum certificate is claimed.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAIN = HERE.parent
RENAMED = ('README.md', 'SOURCE_MANIFEST.json', 'PACKAGE_VALIDATION.json', 'reproduce.sh')
ADDED_DIRS = ('src', 'results', 'docs')
SKIP_PARTS = ('vendor', '__pycache__', 'replay-evidence', 'target')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', required=True, type=Path,
                        help='the retained version 1.28 carrier package (not in this repository)')
    parser.add_argument('--output', required=True, type=Path, help='the .zip to write')
    args = parser.parse_args()
    members = {}
    previous = {}
    with zipfile.ZipFile(args.previous) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            data = archive.read(name)
            target = ('history/v1.28_' + name) if name in RENAMED else name
            members[target] = data
            previous[name] = {'path': target, 'sha256': hashlib.sha256(data).hexdigest()}
    members['reproduce_previous.sh'] = archive.read('reproduce.sh')
    for folder in ADDED_DIRS:
        for path in sorted((DOMAIN / folder).rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(DOMAIN)
            if any(part in SKIP_PARTS for part in rel.parts):
                continue
            if path.name == 'PRIVATE_TRACE_WITNESS.bin' or path.suffix == '.expanded':
                continue
            if path.name in ('package-validation.json',):
                continue
            members[str(rel)] = path.read_bytes()
    members['README.md'] = (DOMAIN / 'docs/package-assessment.md').read_bytes()
    members['reproduce.sh'] = (DOMAIN / 'src/reproduce.sh').read_bytes()
    validation = {
        'scope': 'Packaging integrity and prior-file preservation; no new security certification',
        'previous_package_sha256': hashlib.sha256(args.previous.read_bytes()).hexdigest(),
        'previous_package_members': len(previous),
        'prior_members': previous,
        'new_full_QC_count': 0,
        'excluded_from_recorded_package': ['continuation_v1.29/vendor (the pqcrypto wheel)',
                                           'compiled adapter binaries']}
    members['PACKAGE_VALIDATION.json'] = (json.dumps({
        'scope': validation['scope'], 'previous_package_sha256':
            validation['previous_package_sha256'], 'prior_members': previous,
        'new_full_QC_count': 0}, indent=2) + '\n').encode()
    manifest = []
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert 'PRIVATE_TRACE_WITNESS' not in name
            archive.writestr(name, data)
            manifest.append({'path': name, 'bytes': len(data),
                             'sha256': hashlib.sha256(data).hexdigest()})
        archive.writestr('SOURCE_MANIFEST.json', json.dumps({'files': manifest}, indent=2) + '\n')
    assert args.output.stat().st_size < 50 * 1024 * 1024
    with zipfile.ZipFile(args.output) as archive:
        assert archive.testzip() is None
        for record in manifest:
            assert hashlib.sha256(archive.read(record['path'])).hexdigest() == record['sha256']
        for record in previous.values():
            assert hashlib.sha256(archive.read(record['path'])).hexdigest() == record['sha256']
    result = {'path': str(args.output), 'bytes': args.output.stat().st_size,
              'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
              'preserved_prior_members': len(previous),
              'manifest_members_checked': len(manifest), 'zip_crc_check': 'pass',
              'prior_bytes_preserved': True}
    args.output.with_suffix('.validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
