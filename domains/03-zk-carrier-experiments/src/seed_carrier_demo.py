#!/usr/bin/env python3
"""Demonstrate a small generative carrier. This is NOT a CE-QS proof or a FAEST implementation."""
import hashlib,json,os,struct
from pathlib import Path
HEADER=struct.Struct('>4sBBHI32s64s')
HERE=Path(__file__).resolve().parent;DOMAIN=HERE.parent
FIXTURES=Path(os.environ.get('CEQS_FIXTURES',DOMAIN/'fixtures'))
RESULTS=Path(os.environ.get('CEQS_RESULTS',DOMAIN/'results'))

def xof(tag,*parts,n):return hashlib.shake_256(tag+b''.join(parts)).digest(n)
def children(seed,salt,node):
    pair=xof(b'CEQS128/demo-tree',salt,node.to_bytes(4,'big'),seed,n=96)
    return pair[:48],pair[48:]
def frontier(depth,hidden):
    out=[]
    def visit(node,level,start):
        width=1<<(depth-level)
        if not start<=hidden<start+width:out.append((node,level,start));return
        if level<depth:
            visit(2*node,level+1,start);visit(2*node+1,level+1,start+width//2)
    visit(1,0,0);return out

def descend(seed,salt,node,level,start,depth):
    if level==depth:return {start:seed}
    left,right=children(seed,salt,node);half=1<<(depth-level-1)
    return descend(left,salt,2*node,level+1,start,depth)|descend(right,salt,2*node+1,level+1,start+half,depth)

def tapes_digest(leaves,salt,tape_bytes):
    h=hashlib.shake_256(b'CEQS128/demo-output')
    for i,seed in sorted(leaves.items()):
        h.update(i.to_bytes(4,'big'));h.update(xof(b'CEQS128/demo-tape',salt,i.to_bytes(4,'big'),seed,n=tape_bytes))
    return h.digest(64)

def encode(seed,salt,depth,hidden,tape_bytes=1024):
    nodes={1:seed}
    for node in range(1,1<<depth):nodes[2*node],nodes[2*node+1]=children(nodes[node],salt,node)
    leaves={i:nodes[(1<<depth)+i] for i in range(1<<depth) if i!=hidden}
    digest=tapes_digest(leaves,salt,tape_bytes)
    head=HEADER.pack(b'SCD1',1,depth,tape_bytes,hidden,salt,digest)
    payload=b''.join(nodes[node] for node,_,_ in frontier(depth,hidden))
    return head+payload,leaves

def decode(blob):
    if not HEADER.size<=len(blob)<=32768:raise ValueError('size')
    magic,version,depth,tape_bytes,hidden,salt,expected=HEADER.unpack_from(blob)
    if magic!=b'SCD1' or version!=1 or not 1<=depth<=10 or not 1<=tape_bytes<=4096 or hidden>=1<<depth:raise ValueError('shape')
    front=frontier(depth,hidden)
    if len(blob)!=HEADER.size+48*len(front):raise ValueError('length')
    leaves={}
    for j,(node,level,start) in enumerate(front):
        seed=blob[HEADER.size+48*j:HEADER.size+48*(j+1)]
        leaves.update(descend(seed,salt,node,level,start,depth))
    if hidden in leaves or len(leaves)!=(1<<depth)-1:raise ValueError('coverage')
    if tapes_digest(leaves,salt,tape_bytes)!=expected:raise ValueError('checksum')
    return leaves

def main():
    folder=FIXTURES/'seed-demo';folder.mkdir(parents=True,exist_ok=True);rows=[]
    for hidden in (0,1,17,511,1023):
        blob,leaves=encode(os.urandom(48),os.urandom(32),10,hidden)
        assert decode(blob)==leaves
        for bad in (blob[:-1],blob+b'\0',blob[:HEADER.size]+bytes([blob[HEADER.size]^1])+blob[HEADER.size+1:]):
            try:decode(bad)
            except ValueError:pass
            else:raise AssertionError('malformed demonstration carrier accepted')
        (folder/f'case_{hidden}.scd').write_bytes(blob)
        rows.append({'hidden_index':hidden,'carrier_bytes':len(blob),'seed_frontier_count':10,
                     'reconstructed_leaf_seeds':1023,'equivalent_leaf_seed_bytes':1023*48,
                     'expanded_tape_bytes':1023*1024,'exact_reconstruction':True,
                     'excluded_leaf_absent_from_decoder_output':True,'negative_controls':3})
    result={'scope':'SEEDED_DATA_DEMONSTRATION_NOT_A_QUORUM_CERTIFICATE','cases':rows,
            'seed_source':'fresh OS randomness; no member credentials used',
            'checksum_is_not_an_authentication_proof':True,'quantum_security_proved':False,
            'algorithm_is_not_FAEST_implementation':True,'complete_original_goal_QCs':0}
    RESULTS.mkdir(parents=True,exist_ok=True)
    (RESULTS/'seed-carrier-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
