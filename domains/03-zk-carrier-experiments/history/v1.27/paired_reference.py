#!/usr/bin/env python3
"""Independent Python equations for CEQS127; no cryptographic security claim."""
import hashlib
N,Q=64,43
MASK=(1<<512)-1
TAIL=0x125
META=b'PAIRED-TRACE/DIRECT-CHALLENGE/GF512/64/43/2x48/v1.27'
LABELS=(b'CEQS127/tracekey',b'CEQS127/vote-key')

def h(*parts,n=64):
    return hashlib.shake_256(b''.join(len(p).to_bytes(8,'big')+p for p in parts)).digest(n)

def gf_mul(x,y):
    out=0
    while y:
        if y&1:out^=x
        x<<=1
        if x>>512:x^=(1<<512)|TAIL
        y>>=1
    return out

def gf_inv(x):
    if not 0<x<=MASK:raise ValueError('nonzero canonical field element required')
    u,v=x,(1<<512)|TAIL;a,b=1,0
    while u!=1:
        j=u.bit_length()-v.bit_length()
        if j<0:u,v=v,u;a,b=b,a;j=-j
        u^=v<<j;a^=b<<j
    while a.bit_length()>512:a^=((1<<512)|TAIL)<<(a.bit_length()-513)
    return a

def registration(seeds):
    return [[h(label,seeds[i][role]) for i in range(N)] for role,label in enumerate(LABELS)]

def configuration(keys):
    if len(keys)!=2 or any(len(row)!=64 or len(set(row))!=64 or any(len(x)!=64 for x in row) for row in keys):raise ValueError('registry shape or duplicate keys')
    return h(b'CEQS127/config',META,*(k for row in keys for k in row))

def handle(i,seeds,cfg,d,m):
    if not 0<=i<64 or len(seeds)!=2 or any(len(s)!=48 for s in seeds):raise ValueError('witness shape')
    if any(len(x)!=64 for x in (cfg,d,m)):raise ValueError('context width')
    pair=h(b'CEQS127/pair-tag',seeds[0],cfg,d,n=128)
    z=int.from_bytes(pair[64:],'big')^gf_mul(int.from_bytes(m,'big'),i+1)
    return pair[:64]+z.to_bytes(64,'big')

def build_body(keys,d,m,ids,seeds):
    cfg=configuration(keys)
    rows=sorted((handle(i,seeds[i],cfg,d,m),i,seeds[i]) for i in ids)
    return dict(relation='CEQS127_PAIRED_TRACE',configuration=cfg.hex(),domain=d.hex(),message=m.hex(),handles=[x[0].hex() for x in rows]),[(i,s) for _,i,s in rows]

def parse_body(body):
    if body['relation']!='CEQS127_PAIRED_TRACE':raise ValueError('wrong relation')
    cfg,d,m=(bytes.fromhex(body[x]) for x in ('configuration','domain','message'))
    if any(len(x)!=64 for x in (cfg,d,m)):raise ValueError('context width')
    hs=[bytes.fromhex(x) for x in body['handles']]
    if len(hs)!=43 or any(len(x)!=128 for x in hs) or any(a[:64]>=b[:64] for a,b in zip(hs,hs[1:])):raise ValueError('noncanonical handles')
    return cfg,d,m,hs

def relation(keys,body,witness):
    try:
        cfg,d,m,hs=parse_body(body)
        if configuration(keys)!=cfg or len(witness)!=43 or len({i for i,s in witness})!=43:return False
        return all(0<=i<64 and len(s)==2 and all(len(x)==48 for x in s) and
                   all(h(label,s[role])==keys[role][i] for role,label in enumerate(LABELS)) and
                   pub==handle(i,s,cfg,d,m) for pub,(i,s) in zip(hs,witness))
    except (ValueError,KeyError,IndexError,TypeError):return False

def public_trace_algebra(left,right):
    c,d,m,hs=parse_body(left);c2,d2,m2,hs2=parse_body(right)
    if (c,d)!=(c2,d2) or m==m2:raise ValueError('not one conflicting context')
    inv=gf_inv(int.from_bytes(m,'big')^int.from_bytes(m2,'big'))
    others={x[:64]:int.from_bytes(x[64:],'big') for x in hs2};found=[]
    for x in hs:
        if x[:64] in others:
            a=gf_mul(int.from_bytes(x[64:],'big')^others[x[:64]],inv)
            if not 1<=a<=64:raise ValueError('invalid extracted identity')
            found.append(a-1)
    return sorted(found)
