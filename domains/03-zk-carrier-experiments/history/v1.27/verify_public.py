#!/usr/bin/env python3
"""Public-only verification of experimental PT27 relation proofs, never QC admission."""
import argparse,hashlib,json,os,resource,struct,subprocess,sys,tempfile
from pathlib import Path
RUN=Path(__file__).resolve().parent
from paired_reference import configuration,public_trace_algebra
HEADER=struct.Struct('>4sHH64s64s64sHHI')
BINARY=RUN/'bin/ceqs-paired-trace-v127'

def validate_config(config):
    if [config[x] for x in ('seats','threshold','seed_bytes','hash_bytes','field_polynomial_tail')]!=[64,43,48,64,293]:
        raise ValueError('wrong relation parameters')
    if config['relation']!='CEQS127_PAIRED_TRACE' or config['pair_bytes']!=128:raise ValueError('wrong paired suite')
    keys=[[bytes.fromhex(x) for x in config[name]] for name in ('trace_public_keys','vote_public_keys')]
    if configuration(keys).hex()!=config['configuration'] or len(bytes.fromhex(config['domain']))!=64:
        raise ValueError('configuration inconsistency')

def parse_frame(blob,config):
    if not 5712+16<=len(blob)<=1048576+5712:raise ValueError('experimental frame size')
    magic,version,suite,cfg,d,m,count,width,n=HEADER.unpack_from(blob)
    if (magic,version,suite,count,width)!=(b'PT27',27,0x2703,43,128):raise ValueError('wrong format or incomplete quorum')
    if cfg.hex()!=config['configuration'] or d.hex()!=config['domain']:raise ValueError('wrong context')
    if len(blob)!=5712+n:raise ValueError('noncanonical proof length')
    handles=[blob[i:i+128] for i in range(208,5712,128)]
    if any(a[:64]>=b[:64] for a,b in zip(handles,handles[1:])):raise ValueError('unsorted or duplicate links')
    return dict(relation='CEQS127_PAIRED_TRACE',configuration=cfg.hex(),domain=d.hex(),message=m.hex(),handles=[h.hex() for h in handles])

def limits():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(20<<30,20<<30))

def verify(blob,config_path):
    config=json.loads(config_path.read_text());validate_config(config);body=parse_frame(blob,config)
    with tempfile.TemporaryDirectory(prefix='public-only-',dir=RUN) as td:
        folder=Path(td);(folder/'trace43_rate3.pt27').write_bytes(blob)
        result=subprocess.run([str(BINARY),'verify',str(config_path.resolve()),str(folder),str(folder/'PRIVATE_ABSENT'), '43','3'],
                              text=True,capture_output=True,timeout=1200,preexec_fn=limits,
                              env=dict(os.environ,RAYON_NUM_THREADS='4',MALLOC_ARENA_MAX='1',MALLOC_TRIM_THRESHOLD_='65536'))
        if result.returncode:raise ValueError('native cryptographic verification rejected')
        native=json.loads(result.stdout)
        if not native['public_only_verified'] or native['private_input_opened'] or not native['full_quorum_relation_verified']:
            raise ValueError('native verifier did not establish full public relation')
    return body,dict(sha256=hashlib.sha256(blob).hexdigest(),native_verified=True,frame_bytes=len(blob),
                    complete_QC_accepted=False,all_proof_bytes_inline=True,private_input_opened=False,
                    native_proof_bytes=native['native_proof_bytes'],encoded_proof_bytes=native['encoded_proof_bytes'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True,type=Path);p.add_argument('--frame',required=True,action='append',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    if len(a.frame) not in (1,2):raise ValueError('one proof or one pair')
    bodies=[];records=[]
    for path in a.frame:
        body,record=verify(path.read_bytes(),a.config);bodies.append(body);records.append(record)
    recovered=public_trace_algebra(*bodies) if len(bodies)==2 else None
    if recovered is not None and (len(recovered)<22 or len(set(recovered))!=len(recovered)):
        raise ValueError('insufficient distinct intersection')
    result=dict(scope='ACTUAL_CEQS127_RELATION_PROOFS_EXPERIMENTAL',binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                only_verification_inputs='authenticated public configuration and complete inline frame bytes',frames=records,
                recovered_indices=recovered,qpt_128_qualified=False,actual_authorization_or_nonframing_proved=False,
                complete_32KiB_QCs_accepted=0)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
