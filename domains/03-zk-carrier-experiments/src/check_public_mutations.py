#!/usr/bin/env python3
"""Public binding and canonical-format negative controls using actual proof bytes."""
import json,tempfile
from pathlib import Path
from verify_public import FIXTURES,RESULTS,verify
from paired_reference import configuration

def main():
    cfg=FIXTURES/'config.json';original=(FIXTURES/'case0/trace43_rate3.pf2p').read_bytes();checks=[]
    cases={}
    for name,pos in [('configuration',8),('domain',72),('message',136),('link',208),('mask',272),('proof',6000),('suite',7),('count',201),('proof_length',207)]:
        b=bytearray(original);b[pos]^=1;cases[name]=bytes(b)
    prefix=int.from_bytes(original[5720:5724],'little')
    b=bytearray(original);b[5712+16+prefix]^=1;cases['preloaded_terminal_coefficient']=bytes(b)
    b=bytearray(original);b[5712:5716]=b'QVT1';cases['previous_codec_magic']=bytes(b)
    b=bytearray(original);b[-1]^=1;cases['polynomial_coefficient']=bytes(b)
    b=bytearray(original);b[5712:5716]=b'QVT2';cases['previous_affine_codec_magic']=bytes(b)
    previous=bytearray(original);previous[:8]=bytes.fromhex('50463238001c28b3');cases['previous_suite_header']=bytes(previous)
    other=(FIXTURES/'case1/trace43_rate3.pf2p').read_bytes()
    b=bytearray(original[:5712]);b[204:208]=(len(other)-5712).to_bytes(4,'big');cases['other_message_proof']=bytes(b)+other[5712:]
    cases['truncated']=original[:-1];cases['trailing']=original+b'\0';cases['proof_absent']=original[:5712]
    b=bytearray(original);b[336:464]=b[208:336];cases['duplicate_public_handle']=bytes(b)
    for name,blob in cases.items():
        try:verify(blob,cfg)
        except ValueError:checks.append(name)
        else:raise AssertionError('accepted mutation: '+name)
    with tempfile.TemporaryDirectory() as td:
        c=json.loads(cfg.read_text());c['vote_public_keys'][0]='ff'*64;p=Path(td)/'config.json';p.write_text(json.dumps(c))
        try:verify(original,p)
        except ValueError:checks.append('changed_registry_without_rebinding')
        else:raise AssertionError('accepted inconsistent registry')
    for name in ('domain_rebound_in_frame_and_config','registry_rebound_in_frame_and_config'):
        with tempfile.TemporaryDirectory() as td:
            c=json.loads(cfg.read_text());blob=bytearray(original)
            if name.startswith('domain'):
                value=bytearray.fromhex(c['domain']);value[0]^=1;c['domain']=value.hex();blob[72:136]=value
            else:
                c['vote_public_keys'][0]='fe'*64
                keys=[[bytes.fromhex(x) for x in c[k]] for k in ('trace_public_keys','vote_public_keys')]
                c['configuration']=configuration(keys).hex();blob[8:72]=bytes.fromhex(c['configuration'])
            p=Path(td)/'config.json';p.write_text(json.dumps(c))
            try:verify(bytes(blob),p)
            except ValueError:checks.append(name)
            else:raise AssertionError('accepted rebound context: '+name)
    result=dict(checks_passed=len(checks),rejected=checks,scope='FINITE_NEGATIVE_CONTROLS_NOT_A_SECURITY_THEOREM')
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/'public-negative-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
