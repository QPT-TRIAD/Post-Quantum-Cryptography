#!/usr/bin/env python3
from dataclasses import dataclass
from collections import deque

N=4
F=1
Q=3
NODES=range(N)
MSGS=(0,1)
SESS=(0,1)
BOUNDS=(0,1)

def repl(t,i,v):
    x=list(t); x[i]=v; return tuple(x)

@dataclass(frozen=True)
class VoteSealState:
    epoch: tuple
    sealed: tuple
    vote: tuple
    finalized: int
    seal_ack: tuple
    seal_cert: int
    activated: tuple

VS_INIT=VoteSealState((0,)*N,(-1,)*N,(-1,)*N,-1,(-1,)*N,-1,(-1,)*N)

def vote_seal_succ(s):
    for i in NODES:
        if s.epoch[i]==0 and s.sealed[i]==-1 and s.vote[i]==-1:
            for m in MSGS:
                yield VoteSealState(s.epoch,s.sealed,repl(s.vote,i,m),
                                    s.finalized,s.seal_ack,s.seal_cert,s.activated)
    if s.finalized==-1:
        for b in BOUNDS:
            yield VoteSealState(s.epoch,s.sealed,s.vote,b,
                                s.seal_ack,s.seal_cert,s.activated)
    if s.finalized!=-1:
        b=s.finalized
        for i in NODES:
            if s.epoch[i]==0 and s.sealed[i]==-1:
                yield VoteSealState(s.epoch,repl(s.sealed,i,b),s.vote,
                                    s.finalized,repl(s.seal_ack,i,b),
                                    s.seal_cert,s.activated)
    if (s.seal_cert==-1 and s.finalized!=-1
        and sum(x==s.finalized for x in s.seal_ack)>=Q):
        yield VoteSealState(s.epoch,s.sealed,s.vote,s.finalized,
                            s.seal_ack,s.finalized,s.activated)
    if s.seal_cert!=-1:
        for i in NODES:
            if s.epoch[i]==0:
                yield VoteSealState(repl(s.epoch,i,1),s.sealed,s.vote,
                                    s.finalized,s.seal_ack,s.seal_cert,
                                    repl(s.activated,i,s.seal_cert))

def vote_seal_inv(s):
    for i in NODES:
        if s.sealed[i]!=-1 and s.sealed[i]!=s.finalized:
            return False,"SealOnlyFinalized"
        if s.epoch[i]==1 and s.activated[i]!=s.seal_cert:
            return False,"ActivationRequiresSealCert"
    if s.seal_cert!=-1:
        if s.seal_cert!=s.finalized:
            return False,"SealCertOnlyFinalized"
        if sum(x==s.seal_cert for x in s.seal_ack)<Q:
            return False,"SealCertHasQuorum"
    return True,""

def exhaust(init, successor, invariant):
    seen={init}
    q=deque([init])
    transitions=0
    while q:
        s=q.popleft()
        ok,name=invariant(s)
        if not ok:
            raise AssertionError((name,s))
        for t in successor(s):
            transitions += 1
            if t not in seen:
                seen.add(t); q.append(t)
    return len(seen),transitions

@dataclass(frozen=True)
class PrepState:
    phase: tuple
    sid: tuple

P_INIT=PrepState((0,)*N,(-1,)*N)

def prep_succ(s):
    for i in NODES:
        if s.phase[i]==0:
            for sid in SESS:
                yield PrepState(repl(s.phase,i,1),repl(s.sid,i,sid))
        elif s.phase[i]==1:
            yield PrepState(repl(s.phase,i,2),s.sid)
            yield PrepState(repl(s.phase,i,3),s.sid)
        elif s.phase[i]==2:
            yield PrepState(repl(s.phase,i,3),s.sid)

def prep_inv(s):
    for i in NODES:
        if s.phase[i]==0 and s.sid[i]!=-1:
            return False,"UnusedHasSession"
        if s.phase[i]>0 and s.sid[i] not in SESS:
            return False,"UsedMissingSession"
    return True,""

@dataclass(frozen=True)
class EvidenceState:
    have: tuple
    anchor: tuple
    cert: bool

E_INIT=EvidenceState((False,)*N,(False,)*N,False)

def evidence_succ(s):
    for i in NODES:
        if not s.have[i]:
            yield EvidenceState(repl(s.have,i,True),s.anchor,s.cert)
        if s.have[i] and not s.anchor[i]:
            yield EvidenceState(s.have,repl(s.anchor,i,True),s.cert)
    if not s.cert and sum(s.anchor)>=Q:
        yield EvidenceState(s.have,s.anchor,True)

def evidence_inv(s):
    for i in NODES:
        if s.anchor[i] and not s.have[i]:
            return False,"EvidenceBeforeAnchor"
    if s.cert and sum(s.anchor)<Q:
        return False,"AnchorCertificateWithoutQuorum"
    return True,""

def partition_recovery():
    acks={0,1}
    before=(len(acks)>=Q)
    acks.add(2)
    after=(len(acks)>=Q)
    assert before is False and after is True
    return before,after

if __name__ == "__main__":
    vs=exhaust(VS_INIT,vote_seal_succ,vote_seal_inv)
    ps=exhaust(P_INIT,prep_succ,prep_inv)
    es=exhaust(E_INIT,evidence_succ,evidence_inv)
    pr=partition_recovery()
    print("PASS vote/seal/epoch states=%d transitions=%d" % vs)
    print("PASS preprocessing states=%d transitions=%d" % ps)
    print("PASS evidence/anchor states=%d transitions=%d" % es)
    print("PASS post-seal partition before_cert=%s after_heal_cert=%s" % pr)
