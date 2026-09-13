#!/usr/bin/env python3
"""Measure lossless codecs and binary subspace ranks on existing public QVT1 data."""
import bz2,hashlib,json,lzma,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;DOMAIN=HERE.parent
FIXTURES=DOMAIN/'fixtures';RESULTS=DOMAIN/'results'
OLD=DOMAIN/'history'/'v1.27b'

def rank(values):
    basis={}
    for v in values:
        while v:
            k=v.bit_length()-1
            if k in basis:v^=basis[k]
            else:basis[k]=v;break
    return len(basis)

def main():
    rows=[]
    for case in ('case0','case1'):
        raw=(FIXTURES/case/'trace43_rate3.pf27').read_bytes()
        codec=json.loads((OLD/f'encode_{case}.json').read_text())['codec'];proof=raw[5712:]
        assert len(proof)==codec['encoded_bytes']
        variants=[]
        for name,enc,dec in [('deflate9',lambda b:zlib.compress(b,9),zlib.decompress),('bzip2',bz2.compress,bz2.decompress),('xz',lambda b:lzma.compress(b,preset=9),lzma.decompress)]:
            packed=enc(raw);assert dec(packed)==raw
            variants.append({'algorithm':name,'compressed_bytes':len(packed),'roundtrip_exact':True,'is_a_new_QC_format':False})
        pos=codec['header_bytes']+codec['native_prefix_bytes'];sections=[];all_values=[];all_hashes=[]
        for s in codec['sections']:
            if 'opening' not in s:continue
            count=s['transmitted_scalars'];n=count*16
            values=[int.from_bytes(proof[j:j+16],'little') for j in range(pos,pos+n,16)];pos+=n
            hcount=s['boundary_hashes'];n=hcount*32
            hashes=[int.from_bytes(proof[j:j+32],'little') for j in range(pos,pos+n,32)];pos+=n
            assert count*16+hcount*32==s['encoded_bytes']
            all_values.extend(values);all_hashes.extend(hashes)
            sections.append({'opening':s['opening'],'field_values':count,'field_binary_span_rank':rank(values),'hash_values':hcount,'hash_binary_span_rank':rank(hashes)})
        assert pos+sum(s.get('terminal_encoded_bytes',0) for s in codec['sections'])==len(proof)
        rows.append({'case':case,'frame_sha256':hashlib.sha256(raw).hexdigest(),'frame_bytes':len(raw),
                     'lossless_codecs':variants,'sections':sections,'all_field_span_rank':rank(all_values),'all_hash_span_rank':rank(all_hashes)})
    result={'scope':'MEASUREMENTS_NOT_ENTROPY_OR_IMPOSSIBILITY_PROOF','cases':rows,
            'binary_basis_scope':'A linear subspace of raw serialized blocks only; this does not test all algorithms, field relations, or new proof protocols.'}
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/'existing-carrier-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
