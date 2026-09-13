#!/usr/bin/env python3
"""Fresh private test inputs, independent equations, and reference controls."""
import json,os,struct
from pathlib import Path
from paired_reference import *
RUN=Path(__file__).resolve().parent

def main():
    root=RUN/'fixture'
    if (root/'config.json').exists():raise RuntimeError('refusing to overwrite retained fixture')
    seeds=[[os.urandom(48) for _ in range(2)] for i in range(N)]
    keys=registration(seeds);cfg=configuration(keys);d=os.urandom(64)
    config=dict(relation='CEQS127_PAIRED_TRACE',seats=64,threshold=43,seed_bytes=48,hash_bytes=64,pair_bytes=128,field_polynomial_tail=293,
                configuration=cfg.hex(),domain=d.hex(),trace_public_keys=[x.hex() for x in keys[0]],vote_public_keys=[x.hex() for x in keys[1]])
    (root/'config.json').write_text(json.dumps(config,indent=2)+'\n')
    bodies=[];checks=[];all_w=[]
    for idx,ids,m in [(0,list(range(43)),bytes(64)),(1,list(range(22))+list(range(43,64)),((1<<511)+17).to_bytes(64,'big'))]:
        body,witness=build_body(keys,d,m,ids,seeds);assert relation(keys,body,witness)
        checks.append('honest_43_seat_relation_'+str(idx));bodies.append(body);all_w.append(witness)
        folder=root/f'case{idx}';folder.mkdir()
        (folder/'statement.json').write_text(json.dumps(body,indent=2)+'\n')
        (folder/'statement.bin').write_bytes(m+b''.join(bytes.fromhex(x) for x in body['handles']))
        p=folder/'PRIVATE_TRACE_WITNESS.bin';p.write_bytes(b''.join(struct.pack('<Q',i)+b''.join(s) for i,s in witness));p.chmod(0o600)
        for role in range(2):
            changed=list(witness);i,s=witness[0];s=list(s);s[role]=seeds[(i+1)%64][role];changed[0]=(i,s)
            assert not relation(keys,body,changed);checks.append(f'other_seat_role_{role}_case_{idx}')
        mixed=json.loads(json.dumps(body));mixed['handles'][0]=mixed['handles'][0][:128]+mixed['handles'][1][128:]
        assert not relation(keys,mixed,witness);checks.append('mixed_link_mask_rejected_'+str(idx))
    assert public_trace_algebra(*bodies)==list(range(22));checks.append('expected_22_conflict_identities')
    for name in ('domain','message','configuration'):
        b=json.loads(json.dumps(bodies[0]));v=bytearray.fromhex(b[name]);v[0]^=1;b[name]=v.hex()
        assert not relation(keys,b,all_w[0]);checks.append('changed_'+name+'_rejected')
    for start in range(64):
        b,w=build_body(keys,d,bytes([255])*64,[(start+j)%64 for j in range(43)],seeds);assert relation(keys,b,w)
    checks.append('64_rotating_quorums_at_all_one_message')
    for case in json.loads((RUN/'adapter/field_vectors.json').read_text()):assert gf_mul(int(case['message'],16),case['identity'])==int(case['product'],16)
    checks.append('384_independent_field_vectors')
    # Trace exposes the pair output at this domain; it does not algebraically output either seed.
    recovered_mask_checks=0
    hs1={bytes.fromhex(x)[:64]:bytes.fromhex(x)[64:] for x in bodies[1]['handles']}
    for raw,(i,s) in zip(bodies[0]['handles'],all_w[0]):
        raw=bytes.fromhex(raw)
        if raw[:64] in hs1:
            expected=h(b'CEQS127/pair-tag',s[0],cfg,d,n=128)[64:]
            assert raw[64:]==expected;recovered_mask_checks+=1
    assert recovered_mask_checks==22;checks.append('zero_message_reveals_mask_output_not_a_seed_output')
    result=dict(scope='REFERENCE_EQUATIONS_NOT_SECURITY_THEOREM',checks_passed=len(checks),checks=checks,
                recovered_indices=list(range(22)),rotating_quorums=64,field_vectors=384,
                independent_trace_and_authorization_seeds=True,quantum_security_proved=False,real_MPC_executed=False)
    (RUN/'reference_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    (root/'provenance.json').write_text(json.dumps(dict(seed_source='128 independent os.urandom draws of 48 bytes',
        private_input_words_per_contribution=13,expected_intersection=list(range(22)),centralized_test_prover=True,
        expected_sets=[list(range(43)),list(range(22))+list(range(43,64))]),indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
