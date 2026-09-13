#!/usr/bin/env python3
"""Bounded local runner; records resource outcomes without dumping witnesses."""
import argparse,hashlib,json,os,resource,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('mode');p.add_argument('case');p.add_argument('--count',type=int,default=43);p.add_argument('--rate',type=int,default=3);p.add_argument('--binary',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parent;binary=root/'bin/ceqs-fixed-pair-v127b'
if a.binary is not None: binary=a.binary.resolve()
folder=root/'fixture'/a.case
private=folder/'PRIVATE_TRACE_WITNESS.bin' if a.mode in ('prove','prove_native','check') else root/'PRIVATE_INPUT_IS_ABSENT'
command=[str(binary),a.mode,str(root/'fixture/config.json'),str(folder),str(private),str(a.count),str(a.rate)]
start=time.monotonic()
def limits():
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_AS,(20<<30,20<<30))
with (root/f'{a.label}.json').open('w') as out,(root/f'{a.label}.log').open('w') as err:
    try:
        run=subprocess.run(command,stdout=out,stderr=err,env=dict(os.environ,RAYON_NUM_THREADS='4',MALLOC_ARENA_MAX='1',MALLOC_TRIM_THRESHOLD_='65536'),preexec_fn=limits,timeout=1200)
        code=run.returncode
    except subprocess.TimeoutExpired:
        code=None
result={'allocator_environment':{'MALLOC_ARENA_MAX':'1','MALLOC_TRIM_THRESHOLD_':'65536','RAYON_NUM_THREADS':'4'},'binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'label':a.label,'mode':a.mode,'case':a.case,'count':a.count,'rate':a.rate,'return_code':code,
        'elapsed_seconds':time.monotonic()-start,'peak_child_rss_kib':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        'address_space_limit_bytes':20<<30,'timeout_seconds':1200}
(root/f'{a.label}_execution.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
raise SystemExit(0 if code==0 else 1)
