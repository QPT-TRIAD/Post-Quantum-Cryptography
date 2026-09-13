#!/usr/bin/env python3
"""Public binding and canonical-format negative controls using actual proof bytes."""
import json,tempfile
from pathlib import Path
from verify_public import RUN,verify

def main():
    cfg=RUN/'fixture/config.json';original=(RUN/'fixture/case0/trace43_rate3.pt27').read_bytes();checks=[]
    cases={}
    for name,pos in [('configuration',8),('domain',72),('message',136),('link',208),('mask',272),('proof',6000),('suite',7),('count',201),('proof_length',207)]:
        b=bytearray(original);b[pos]^=1;cases[name]=bytes(b)
    previous=bytearray(original);previous[:8]=bytes.fromhex('4443323500192503');cases['previous_suite_header']=bytes(previous)
    cases['truncated']=original[:-1];cases['trailing']=original+b'\0';cases['proof_absent']=original[:5712]
    b=bytearray(original);b[336:464]=b[208:336];cases['duplicate_public_handle']=bytes(b)
    for name,blob in cases.items():
        try:verify(blob,cfg)
        except ValueError:checks.append(name)
        else:raise AssertionError('accepted mutation: '+name)
    with tempfile.TemporaryDirectory(dir=RUN) as td:
        c=json.loads(cfg.read_text());c['vote_public_keys'][0]='ff'*64;p=Path(td)/'config.json';p.write_text(json.dumps(c))
        try:verify(original,p)
        except ValueError:checks.append('changed_registry_without_rebinding')
        else:raise AssertionError('accepted inconsistent registry')
    result=dict(checks_passed=len(checks),rejected=checks,scope='FINITE_NEGATIVE_CONTROLS_NOT_A_SECURITY_THEOREM')
    (RUN/'public_negative_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
