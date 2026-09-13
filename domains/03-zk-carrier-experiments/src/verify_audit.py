#!/usr/bin/env python3
"""Replay public signature checks, explicitly NOT a complete-QC verifier."""
import argparse
import json
from pathlib import Path
import authorization as a

def verify(path):
    data=json.loads(path.read_text())
    registry=[{k:bytes.fromhex(v) for k,v in row.items()} for row in data['registry']]
    bodies=[]
    for case in data['cases']:
        body=bytes.fromhex(case['body_hex'])
        approvals=[(r['seat'],bytes.fromhex(r['signature_hex'])) for r in case['approvals']]
        assert a.check_public_approvals(registry,body,approvals)
        bodies.append(body)
    assert len(bodies)==2
    found=a.extract_algebra(*bodies)
    assert found==list(range(22))
    print(json.dumps({'scope':'Public approval signatures and trace algebra ONLY; not trace-opening proofs',
      'public_approval_checks':86,'algebraic_intersection':found,'complete_QCs_verified':0},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('path',type=Path,nargs='?',default=Path(__file__).resolve().parent.parent/'results'/'public-approval-audit.json')
    verify(parser.parse_args().path)
