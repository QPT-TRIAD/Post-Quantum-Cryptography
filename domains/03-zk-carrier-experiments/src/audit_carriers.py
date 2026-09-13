#!/usr/bin/env python3
"""Audit public carrier evidence and decode the stored seeded-data examples."""
import hashlib,json
from pathlib import Path
from seed_carrier_demo import decode
HERE=Path(__file__).resolve().parent;DOMAIN=HERE.parent
FIXTURES=DOMAIN/'fixtures';RESULTS=DOMAIN/'results';HISTORY=DOMAIN/'history'

def main():
    rows=[]
    # The version 1.28 working directory kept underscore file names; the domain's
    # retained results for the current generation use hyphens. Each file is read
    # from the location the file map gives it.
    for run,frames,name,public_name,negative_name,suffix,expected_checks in [
            (HISTORY/'v1.28',FIXTURES,'encode_{}.json','public_verification.json',
             'public_negative_checks.json','pf28',20),
            (RESULTS,FIXTURES,'encode-{}.json','public-verification.json',
             'public-negative-checks.json','pf2p',22)]:
        public=json.loads((run/public_name).read_text())
        assert public['recovered_indices']==list(range(22))
        assert public['qpt_128_qualified'] is False and public['complete_32KiB_QCs_accepted']==0
        negative=json.loads((run/negative_name).read_text());assert negative['checks_passed']==expected_checks
        for j,frame in enumerate(public['frames']):
            case=f'case{j}';raw=(frames/case/f'trace43_rate3.{suffix}').read_bytes()
            old=(FIXTURES/case/'trace43_rate3.proof').read_bytes()
            assert frame['sha256']==hashlib.sha256(raw).hexdigest()
            assert frame['expanded_native_sha256']==hashlib.sha256(old).hexdigest()
            assert frame['native_verified'] and not frame['private_input_opened'] and not frame['complete_QC_accepted']
            assert not (frames/case/'PRIVATE_TRACE_WITNESS.bin').exists()
            d=json.loads((run/name.format(case)).read_text());c=d['codec']
            fields=16*sum(s.get('transmitted_scalars',0) for s in c['sections'])
            hashes=32*sum(s.get('boundary_hashes',0) for s in c['sections'])
            fixed=c['header_bytes']+c['native_prefix_bytes']+sum(s.get('terminal_encoded_bytes',0) for s in c['sections'])
            assert fields+hashes+fixed==c['encoded_bytes']
            assert len(raw)==c['encoded_bytes']+5712==frame['frame_bytes']
            if suffix=='pf2p':
                layers=[s for s in c['sections'] if s.get('polynomial_mode')]
                assert len(layers)==1 and layers[0]['polynomial_carrier_coefficients']==512
                assert layers[0]['regenerated_codeword_scalars']==4096 and layers[0]['boundary_hashes']==0
            rows.append({'representation':c['format'],'case':case,'native_sha256':frame['expanded_native_sha256'],
                'complete_frame_bytes':len(raw),'field_value_bytes':fields,'boundary_hash_bytes':hashes,'fixed_and_terminal_bytes':fixed,
                'saved_from_QVT1':c['saved_from_previous_codec'],'same_native_proof':True,'public_negative_controls':expected_checks})
    seed_rows=[]
    for path in sorted((FIXTURES/'seed-demo').glob('*.scd')):
        raw=path.read_bytes();leaves=decode(raw);assert len(raw)==588 and len(leaves)==1023
        seed_rows.append({'file':path.name,'carrier_bytes':len(raw),'reconstructed_leaves':len(leaves),'sha256':hashlib.sha256(raw).hexdigest()})
    assert len(seed_rows)==5
    result={'scope':'EXPERIMENTAL_CARRIER_AUDIT_NOT_SECURITY_THEOREM','real_proof_representations':rows,'seeded_data_only':seed_rows,
            'complete_original_goal_QCs':0,'qpt_128_qualified':False,'distributed_authorization_implemented':False}
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/'carrier-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
