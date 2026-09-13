#!/usr/bin/env python3
"""Exact local mathematical checks, not a quantum attack or security proof.

Standalone, Python 3 standard library. Prints its complete summary as JSON.
Probability pass/fail decisions use integers and Fraction, not floating logs.
"""
from fractions import Fraction as F
from itertools import product, combinations
from math import log2
import json

ELL=1<<20
V=2*(ELL*21+1)
TAU=F(1,24)

def joint_raw(s,h,p):
    q=1<<s
    return F((72+40*ELL)*q**3+2*V,1<<h)+20*q*q*p

def log_display(x):
    x=F(x)
    if x<=0: return None
    def logint(n):
        shift=max(0,n.bit_length()-53)
        return log2(n>>shift)+shift
    return logint(x.numerator)-logint(x.denominator)

def minimum_rounds(s,beta,h=512):
    beta=F(beta)
    if not 0<beta<1: raise ValueError('require 0<beta<1')
    if joint_raw(s,h,F(0))>=TAU: return None
    p=F(1); n=0
    while joint_raw(s,h,p)>TAU:
        p*=beta; n+=1
    return n

def digits(x,b,r):
    out=[]
    for _ in range(r):
        x,d=divmod(x,b); out.append(d)
    return tuple(reversed(out))

def prefix_count(R,b,t,r):
    """Count x<R with r base-b digits each in [0,t)."""
    if not (2<=b and 1<=t<b and r>=0 and 0<=R<=b**r):
        raise ValueError('invalid digit parameters')
    if R==b**r: return t**r
    total=0
    for j,d in enumerate(digits(R,b,r)):
        remaining=r-j-1
        total+=min(d,t)*t**remaining
        if d>=t: return total
    return total

def box_mass(h,b,t,r):
    if h<0: raise ValueError('h must be nonnegative')
    a,R=divmod(1<<h,b**r)
    return F(a*t**r+prefix_count(R,b,t,r),1<<h)

def brute_box_mass(h,b,t,r):
    # Independent enumeration of every permitted t-subset in every coordinate.
    subsets=list(combinations(range(b),t))
    residue_counts=[0]*(b**r)
    for u in range(1<<h): residue_counts[u%(b**r)]+=1
    best=0
    for box in product(subsets,repeat=r):
        total=0
        for ds in product(*box):
            x=0
            for d in ds: x=b*x+d
            total+=residue_counts[x]
        best=max(best,total)
    return F(best,1<<h)

def mm(a,b):
    return [[sum((a[i][k]*b[k][j] for k in range(len(b))),F(0))
             for j in range(len(b[0]))] for i in range(len(a))]

def tr(a): return sum((a[i][i] for i in range(len(a))),F(0))
def transpose(a): return [list(x) for x in zip(*a)]
def normsq(v): return sum((x*x for x in v),F(0))
def mv(a,v): return [sum((x*y for x,y in zip(row,v)),F(0)) for row in a]
def eye(a=F(1)): return [[a,F(0)],[F(0),a]]
def sub(a,b): return [[x-y for x,y in zip(u,v)] for u,v in zip(a,b)]
def psd2(a):
    return a==transpose(a) and a[0][0]>=0 and a[1][1]>=0 and a[0][0]*a[1][1]>=a[0][1]**2

def rank_mod(a,q):
    a=[list(row) for row in a]; m=len(a); n=len(a[0]); r=0
    for col in range(n):
        pivot=next((i for i in range(r,m) if a[i][col]%q),None)
        if pivot is None: continue
        a[r],a[pivot]=a[pivot],a[r]
        inv=pow(a[r][col]%q,-1,q)
        a[r]=[(v*inv)%q for v in a[r]]
        for i in range(m):
            if i!=r:
                coef=a[i][col]
                a[i]=[(x-coef*y)%q for x,y in zip(a[i],a[r])]
        r+=1
        if r==m: break
    return r

def rank_count(m,n,r,q):
    if not 0<=r<=min(m,n): return 0
    v=F(1)
    for i in range(r): v*=F((q**m-q**i)*(q**n-q**i),q**r-q**i)
    assert v.denominator==1
    return v.numerator

def dag_cost(nodes):
    """Nodes are already topologically ordered: (name,gates,depth,preds)."""
    depth={}; work=0
    for name,g,d,preds in nodes:
        if min(g,d)<0 or name in depth: raise ValueError('invalid DAG cost')
        depth[name]=d+max((depth[p] for p in preds),default=0)
        work+=g
    return work,max(depth.values(),default=0)

FIELDS=('event','relation','key_distribution','oracle_interface','resources')
def compatible(a,b):
    missing=[f for f in FIELDS if f not in a or f not in b]
    mismatch=[f for f in FIELDS if f in a and f in b and a[f]!=b[f]]
    return {'structurally_compatible':not missing and not mismatch,
            'missing':missing,'mismatch':mismatch,'cryptographic_theorem_verified':False}

def main():
    checks=[]
    def passed(name,detail): checks.append({'test':name,'status':'PASS','scope':detail})

    # 1: exact counterexample to threshold-meet idempotence.
    chain=[F(0),F(1,4),F(1,2),F(1)]
    admissible=[z for z in chain if z<=F(1,4) and z>=F(1,2)]
    result=max(admissible,default=F(0))
    assert result!=F(1,4)
    passed('L1 threshold meet','Finite complete-chain counterexample.')

    p=[F(4,5),F(1,10),F(1,10)]; q=[F(3,5),F(2,5),F(0)]
    upper=[max(a,b) for a,b in zip(p,q)]; lower=[min(a,b) for a,b in zip(p,q)]
    upper=[x/sum(upper) for x in upper]; lower=[x/sum(lower) for x in lower]
    assert upper==[F(8,13),F(4,13),F(1,13)] and upper[0]<p[0]
    assert lower==[F(6,7),F(1,7),F(0)] and lower[0]>p[0]
    passed('L9/L10 majorization','Both normalized envelopes fail at k=1.')

    # Cover/product/order issues are witnessed on finite structures.
    points=list(product(range(2),repeat=2))
    def le(x,y): return all(a<=b for a,b in zip(x,y))
    width=max(len(c) for k in range(5) for c in combinations(points,k)
              if all(not le(x,y) and not le(y,x) for x,y in combinations(c,2)))
    assert width==2 and (0,1)<(1,0) and not 1<=0
    passed('L35/L47 order','Lexicographic second projection fails; product width is two.')

    # Negative diagonal self-loops: trace(A)=-1, trace(A^2)=-2.
    correct=max(F(-1,1),F(-2,2)); source=F(max(-1,-2),2)
    assert correct==F(-1) and source==F(-1,2)
    passed('T7 cycle mean','Maximum of normalized traces differs from normalization after maximum.')

    a=[[0,-1],[-1,0]]
    for x in ([F(0),F(0)],[F(0),F(1,2)]):
        assert [max(F(a[i][j])+x[j] for j in range(2)) for i in range(2)]==x
    passed('T8 eigenvector uniqueness','Two non-translation-equivalent max-plus eigenvectors.')

    # Softmin Hessian at (0,0), beta=1 is negative semidefinite, not positive.
    soft_hessian=[[F(-1,4),F(1,4)],[F(1,4),F(-1,4)]]
    assert not psd2(soft_hessian) and psd2([[-x for x in row] for row in soft_hessian])
    passed('T42 softmin','Exact Hessian refutes convexity.')

    # Jackson commutator on monomials for several rational q,x values.
    qcases=0
    for qv in (F(1,2),F(2),F(3)):
        for x in (F(1,3),F(1),F(2)):
            for n in range(6):
                f=lambda z:z**n
                dq=lambda z:(f(qv*z)-f(z))/((qv-1)*z)
                lhs=(f(qv*qv*x)-f(qv*x))/((qv-1)*x)-dq(qv*x)
                assert lhs==(qv-1)*dq(qv*x)
                qcases+=1
    assert (1-2)==-1  # (I-E)x=-1, while (E-I)x=1.
    passed('Q40/D9 signs',f'{qcases} commutator cases and an odd-order difference counterexample.')

    # Uniform interval has unchanged density after translation; min divergence orientation.
    width_before=F(2)-F(0); width_after=F(9)-F(7)
    assert width_before==width_after and F(1)/width_before==F(1)/width_after
    source_mass=F(1); correct_mass=F(1,2)
    assert source_mass!=correct_mass
    passed('I21/I33 entropy corrections','Uniform interval translation preserves density; swapped support masses differ.')

    # K^T K exactly certifies subnormalized contraction; no state sampling needed.
    k=[[F(1,2),F(1,2)],[F(1,2),F(-1,2)]]
    kt_k=mm(transpose(k),k)
    assert kt_k==eye(F(1,2))
    robust=eye(F(3,4))
    assert mm(transpose(robust),robust)==eye(F(9,16))
    assert psd2(sub(eye(),kt_k))
    passed('Contraction instruments','Exact K^T K=(1/2)I and robust K^T K=(9/16)I certificates.')

    nonnormal=[[F(0),F(2)],[F(0),F(0)]]
    assert mm(nonnormal,nonnormal)==eye(F(0))
    assert normsq(mv(nonnormal,[F(0),F(1)]))==4
    assert not psd2(sub(eye(),mm(transpose(nonnormal),nonnormal)))
    passed('Spectral-radius substitution rejected','Nilpotent norm-two map is not a valid failure instrument.')

    z=[[F(1),F(0)],[F(0),F(0)]]
    plus=[[F(1,2),F(1,2)],[F(1,2),F(1,2)]]
    v0=[F(1),F(0)]
    assert normsq(mv(mm(z,plus),v0))==F(1,4)
    assert normsq(mv(mm(plus,z),v0))==F(1,2)
    passed('Measurement order','Two projection orders yield probabilities 1/4 and 1/2.')

    # Correlated Bernoulli rounds demonstrate the need for conditional bounds.
    joint_bad=F(1,2); marginal_product=F(1,4)
    assert joint_bad>marginal_product
    passed('Marginals do not multiply','Perfectly correlated half-probability failures remain probability 1/2.')

    stages=[]
    for s in (32,64,92,128):
        exact=minimum_rounds(s,F(1,2)); robust_n=minimum_rounds(s,F(9,16))
        for beta,n in ((F(1,2),exact),(F(9,16),robust_n)):
            assert joint_raw(s,512,beta**n)<=TAU
            assert n>0 and joint_raw(s,512,beta**(n-1))>TAU
        stages.append({'query_exponent':s,'ideal_half_rounds':exact,'robust_9_16_rounds':robust_n,
                       'robust_bound_log2_display':log_display(joint_raw(s,512,F(9,16)**robust_n))})
    assert [x['ideal_half_rounds'] for x in stages]==[73,137,193,265]
    assert stages[-1]['robust_9_16_rounds']==320
    assert joint_raw(128,512,F(1,1<<128))>1
    assert joint_raw(128,512,F(9,16)**320)<TAU
    assert minimum_rounds(128,F(1,2),h=256) is None
    passed('QPT staged component bounds','Exact minimum-round boundary checks at 32,64,92,128; wrong event substitution remains forbidden.')

    # Exact source sampler vs independent enumeration, including non-ternary cases.
    boxcases=0; prefixcases=0
    for b in range(2,6):
        for t in range(1,b):
            for r in range(1,4 if b<=4 else 3):
                for R in range(b**r+1):
                    brute=sum(all(d<t for d in digits(x,b,r)) for x in range(R))
                    assert prefix_count(R,b,t,r)==brute
                    prefixcases+=1
                for h in range(1,7):
                    assert box_mass(h,b,t,r)==brute_box_mass(h,b,t,r)
                    boxcases+=1
    assert box_mass(2,3,2,2)==F(3,4)
    assert box_mass(512,3,2,324)==box_mass(512,3,2,512)
    assert joint_raw(128,720,box_mass(720,3,2,454))<=TAU
    passed('Generalized prefix-box lemma',f'{prefixcases} prefix counts and {boxcases} maximum-box instances checked exhaustively.')

    # Unconditional entropy cannot increase through a deterministic classical map.
    maps=0
    for weights in ((1,1,1),(1,2,3),(0,1,5),(5,0,1)):
        for f in product(range(2),repeat=3):
            out=[sum(weights[i] for i in range(3) if f[i]==j) for j in range(2)]
            assert max(out)>=max(weights)
            maps+=1
    passed('Deterministic entropy',f'{maps} small maps checked; the quantum-side-information extension is proved in the text.')

    d1=d2=F(1,4); epsilon=F(1,3)
    conditional=F(1,2)
    assert conditional==epsilon*(1-d1)/(1-d1-d2)
    assert (1-d1-d2)>0
    assert (1<<64)*F(759,1024)**519<=F(1,1<<160)
    assert (1<<64)*F(759,1024)**518>F(1,1<<160)
    passed('Good events and retry tail','Tight four-outcome conditioning example; 519/518 exact truncation boundary.')

    rankcases=0
    for qv,m,n in ((2,2,2),(2,2,3),(2,3,3),(3,2,2)):
        counts=[0]*(min(m,n)+1)
        for flat in product(range(qv),repeat=m*n):
            matrix=[flat[i*n:(i+1)*n] for i in range(m)]
            counts[rank_mod(matrix,qv)]+=1
        assert counts==[rank_count(m,n,r,qv) for r in range(min(m,n)+1)]
        assert sum(counts)==qv**(m*n)
        rankcases+=qv**(m*n)
    passed('Finite-field rank',f'{rankcases} matrices enumerated; no seeded-module distribution claim follows.')

    nodes=[('a',10,3,()),('b',20,5,()),('join',7,2,('a','b'))]
    assert dag_cost(nodes)==(37,7)
    assert 2*128==256 and (lambda t:3*(2*t+1)+4)(10)==67
    passed('Work/depth and reduction composition','Parallel work 37 vs depth 7; affine resource maps composed explicitly.')

    # A fixed publicly computable function is distinguishable from an independent RO.
    # Finite oracle table enumeration on two inputs with four possible outputs.
    matches=sum(table[0]==2 for table in product(range(4),repeat=2))
    assert F(matches,16)==F(1,4)
    assert F(1)-F(matches,16)==F(3,4)
    passed('Fixed-hash versus independent oracle','Equality test gap is 1-2^-h; no claim about simulator-based indifferentiability.')

    game=[[1,-1],[-1,1]]
    minmax=min(max(row) for row in game)
    maxmin=max(min(game[i][j] for i in range(2)) for j in range(2))
    assert maxmin==-1 and minmax==1 and maxmin<minmax
    passed('Y1 minimax direction','Pure-strategy matching-pennies values give -1<1.')

    # Other false source properties use simple exact witnesses.
    pd0=[(0,6),(20,26)]; pd1=[(1,7),(21,27)]
    def diagcost(pt): return F(pt[1]-pt[0],2)**2
    costs=[]
    for assignment in product((-1,0,1),repeat=2):
        used=[j for j in assignment if j!=-1]
        if len(used)!=len(set(used)): continue
        cost=sum((diagcost(pd0[i]) if j==-1 else
                  F(max(abs(x-y) for x,y in zip(pd0[i],pd1[j])))**2)
                 for i,j in enumerate(assignment))
        cost+=sum(diagcost(pd1[j]) for j in range(2) if j not in used)
        costs.append(cost)
    assert min(costs)==2  # W_2=sqrt(2), while bottleneck distance is one.
    # Explicit CPTP local reset on a two-qubit Bell density operator.
    bell=[[F(0) for _ in range(4)] for _ in range(4)]
    for i,j in product((0,3),repeat=2): bell[i][j]=F(1,2)
    output=[[F(0) for _ in range(4)] for _ in range(4)]
    completeness=[[F(0) for _ in range(4)] for _ in range(4)]
    for k0 in range(4):
        e=[[F(0) for _ in range(4)] for _ in range(4)]; e[0][k0]=F(1)
        term=mm(mm(e,bell),transpose(e)); ce=mm(transpose(e),e)
        for i,j in product(range(4),repeat=2):
            output[i][j]+=term[i][j]; completeness[i][j]+=ce[i][j]
    assert output[0][0]==1 and sum(map(sum,output))==1
    assert completeness==[[F(i==j) for j in range(4)] for i in range(4)]
    passed('H20/R36 counterexamples','Two-feature Wasserstein squared cost two; local-reset Schmidt rank decreases.')

    intersectioncases=0
    sets=[set(c) for c in combinations(range(7),5)]
    for a,b in product(sets,repeat=2):
        assert len(a&b)>=5+5-7
        intersectioncases+=1
    passed('Quorum set intersection',f'{intersectioncases} pairs checked; no signature/authorization premise supplied.')

    good=dict(event='bad-box-mass',relation='quorum-v1',key_distribution='uniform-model',
              oracle_interface='QROM-shared',resources='queries<=2^128')
    assert compatible(good,good)['structurally_compatible']
    rejected=0
    for field in FIELDS:
        other=dict(good); other[field]='incompatible'
        assert not compatible(good,other)['structurally_compatible']; rejected+=1
        other=dict(good); del other[field]
        assert not compatible(good,other)['structurally_compatible']; rejected+=1
    assert not compatible(good,good)['cryptographic_theorem_verified']
    passed('Contract negative mutations',f'{rejected} mismatches/missing fields rejected; compatible records never self-certify a theorem.')

    return {'version':'1.33','test_groups_passed':len(checks),'checks':checks,'stages':stages,
            'robust_128_raw_bound_log2_display':log_display(joint_raw(128,512,F(9,16)**320)),
            'full_QPT128_established':False,
            'open_premises':['actual joint relation decoder','public conflict extractor without sidecar',
                'p_star bridge for actual protocol and sampler','concrete signature hardness at reduction resources',
                'compatible signature good-key event and standardized algorithm adapter',
                'deployed-hash game properties','concrete gate/depth/memory accounting'],
            'scope':'Exact arithmetic, finite counterexamples and component-bound checks; no quantum cryptanalysis executed.'}

if __name__=='__main__':
    print(json.dumps(main(),indent=2))
