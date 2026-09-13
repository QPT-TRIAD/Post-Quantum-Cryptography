#!/usr/bin/env python3
"""
PQAQC v0.7 bounded finite-state verification.

This is NOT TLC or TLAPS.

It exhaustively explores several finite abstractions that correspond to
specific proof obligations. It also runs deliberately UNSAFE mutation
controls to prove the checker can find counterexamples when key guards are
removed.

The models are decomposed intentionally to keep complete state exploration
tractable and to make the claim from each run precise.
"""

from dataclasses import dataclass
from collections import deque

N = 4
F = 1
Q = 3
NODES = tuple(range(N))
HONEST = frozenset({0,1,2})
BYZ = frozenset({3})

DOMAINS = (0,1)
MSGS = (0,1)
SESSIONS = (0,1)
PREPS = (0,1)
BOUNDARIES = (0,1)

def repl(t, i, value):
    x = list(t)
    x[i] = value
    return tuple(x)

def explore(init, successor, invariant, max_states=5_000_000):
    seen = {init}
    q = deque([init])
    parents = {init: None}
    parent_action = {}
    transitions = 0

    while q:
        s = q.popleft()

        ok, name = invariant(s)
        if not ok:
            path = []
            cur = s
            while parents[cur] is not None:
                path.append(parent_action[cur])
                cur = parents[cur]
            path.reverse()
            return {
                "states": len(seen),
                "transitions": transitions,
                "failure": name,
                "counterexample": path,
            }

        for action, t in successor(s):
            transitions += 1
            if t not in seen:
                if len(seen) >= max_states:
                    return {
                        "states": len(seen),
                        "transitions": transitions,
                        "failure": "STATE_LIMIT",
                        "counterexample": [],
                    }
                seen.add(t)
                parents[t] = s
                parent_action[t] = action
                q.append(t)

    return {
        "states": len(seen),
        "transitions": transitions,
        "failure": None,
        "counterexample": [],
    }

# -------------------------------------------------------------------------
# Model A: one honest vote per CONFLICT DOMAIN
# -------------------------------------------------------------------------

@dataclass(frozen=True)
class DomainVoteState:
    sent: frozenset   # (node, domain, message)

DV_INIT = DomainVoteState(frozenset())

def domain_vote_succ(s, unsafe=False):
    for i in HONEST:
        for d in DOMAINS:
            for m in MSGS:
                existing = {
                    mm for ii, dd, mm in s.sent
                    if ii == i and dd == d
                }
                if (unsafe or not existing) and (i,d,m) not in s.sent:
                    yield (
                        ("vote", i, d, m),
                        DomainVoteState(s.sent | {(i,d,m)})
                    )

def domain_vote_inv(s):
    for i in HONEST:
        for d in DOMAINS:
            msgs = {
                m for ii, dd, m in s.sent
                if ii == i and dd == d
            }
            if len(msgs) > 1:
                return False, "HonestVoteOncePerDomain"
    return True, ""

# -------------------------------------------------------------------------
# Model B: boundary finality DERIVED from quorum votes
# -------------------------------------------------------------------------

@dataclass(frozen=True)
class BoundaryState:
    honest_votes: frozenset  # (honest node, boundary)
    byz_votes: frozenset     # (byz node, boundary)
    certs: frozenset         # boundary

B_INIT = BoundaryState(frozenset(), frozenset(), frozenset())

def boundary_succ(s, unsafe_honest_double_vote=False):
    for i in HONEST:
        for b in BOUNDARIES:
            existing = {
                bb for ii, bb in s.honest_votes if ii == i
            }
            if (unsafe_honest_double_vote or not existing) and (i,b) not in s.honest_votes:
                yield (
                    ("honest_boundary_vote", i, b),
                    BoundaryState(
                        s.honest_votes | {(i,b)},
                        s.byz_votes,
                        s.certs,
                    )
                )

    for i in BYZ:
        for b in BOUNDARIES:
            if (i,b) not in s.byz_votes:
                yield (
                    ("byz_boundary_vote", i, b),
                    BoundaryState(
                        s.honest_votes,
                        s.byz_votes | {(i,b)},
                        s.certs,
                    )
                )

    for b in BOUNDARIES:
        voters = {
            i for i, bb in s.honest_votes if bb == b
        } | {
            i for i, bb in s.byz_votes if bb == b
        }
        if len(voters) >= Q and b not in s.certs:
            yield (
                ("form_boundary_certificate", b),
                BoundaryState(
                    s.honest_votes,
                    s.byz_votes,
                    s.certs | {b},
                )
            )

def boundary_inv(s):
    for i in HONEST:
        choices = {
            b for ii, b in s.honest_votes if ii == i
        }
        if len(choices) > 1:
            return False, "HonestBoundaryDoubleVote"

    if len(s.certs) > 1:
        return False, "BoundaryFinalityFork"

    return True, ""

def boundary_uniqueness_only(s):
    if len(s.certs) > 1:
        return False, "BoundaryFinalityFork"
    return True, ""

# -------------------------------------------------------------------------
# Model C: durable/volatile vote + preprocessing + crash/restart
# -------------------------------------------------------------------------

@dataclass(frozen=True)
class CrashState:
    running: bool

    durable_vote: tuple
    volatile_vote: tuple
    sent_votes: frozenset

    prep_phase: tuple      # 0=U,1=R,2=E,3=B
    prep_sid: tuple
    volatile_prep: tuple
    sent_shares: frozenset

C_INIT = CrashState(
    True,
    (-1,) * len(DOMAINS),
    (-1,) * len(DOMAINS),
    frozenset(),
    (0,) * len(PREPS),
    (-1,) * len(PREPS),
    (-1,) * len(PREPS),
    frozenset(),
)

def crash_succ(s, unsafe_volatile_send=False):
    if s.running:
        # Begin ordinary vote in volatile memory.
        for d in DOMAINS:
            if s.volatile_vote[d] == -1:
                for m in MSGS:
                    if s.durable_vote[d] in (-1, m):
                        yield (
                            ("begin_vote", d, m),
                            CrashState(
                                True,
                                s.durable_vote,
                                repl(s.volatile_vote, d, m),
                                s.sent_votes,
                                s.prep_phase,
                                s.prep_sid,
                                s.volatile_prep,
                                s.sent_shares,
                            )
                        )

        # Persist ordinary vote.
        for d in DOMAINS:
            m = s.volatile_vote[d]
            if m != -1 and s.durable_vote[d] in (-1, m):
                yield (
                    ("persist_vote", d, m),
                    CrashState(
                        True,
                        repl(s.durable_vote, d, m),
                        repl(s.volatile_vote, d, -1),
                        s.sent_votes,
                        s.prep_phase,
                        s.prep_sid,
                        s.volatile_prep,
                        s.sent_shares,
                    )
                )

        # Safe send requires durable state.
        for d in DOMAINS:
            m = s.durable_vote[d]
            if m != -1 and (d,m) not in s.sent_votes:
                yield (
                    ("send_durable_vote", d, m),
                    CrashState(
                        True,
                        s.durable_vote,
                        s.volatile_vote,
                        s.sent_votes | {(d,m)},
                        s.prep_phase,
                        s.prep_sid,
                        s.volatile_prep,
                        s.sent_shares,
                    )
                )

        # Unsafe mutation: transmit before persist.
        if unsafe_volatile_send:
            for d in DOMAINS:
                m = s.volatile_vote[d]
                if m != -1 and (d,m) not in s.sent_votes:
                    yield (
                        ("UNSAFE_send_volatile_vote", d, m),
                        CrashState(
                            True,
                            s.durable_vote,
                            s.volatile_vote,
                            s.sent_votes | {(d,m)},
                            s.prep_phase,
                            s.prep_sid,
                            s.volatile_prep,
                            s.sent_shares,
                        )
                    )

        # Begin preprocessing reservation in volatile memory.
        for p in PREPS:
            if s.prep_phase[p] == 0 and s.volatile_prep[p] == -1:
                for sid in SESSIONS:
                    yield (
                        ("begin_prep_reserve", p, sid),
                        CrashState(
                            True,
                            s.durable_vote,
                            s.volatile_vote,
                            s.sent_votes,
                            s.prep_phase,
                            s.prep_sid,
                            repl(s.volatile_prep, p, sid),
                            s.sent_shares,
                        )
                    )

        # Persist preprocessing reservation.
        for p in PREPS:
            sid = s.volatile_prep[p]
            if sid != -1 and s.prep_phase[p] == 0:
                yield (
                    ("persist_prep_reserve", p, sid),
                    CrashState(
                        True,
                        s.durable_vote,
                        s.volatile_vote,
                        s.sent_votes,
                        repl(s.prep_phase, p, 1),
                        repl(s.prep_sid, p, sid),
                        repl(s.volatile_prep, p, -1),
                        s.sent_shares,
                    )
                )

        # Use only persisted preprocessing.
        for p in PREPS:
            if s.prep_phase[p] == 1:
                yield (
                    ("use_persisted_prep", p, s.prep_sid[p]),
                    CrashState(
                        True,
                        s.durable_vote,
                        s.volatile_vote,
                        s.sent_votes,
                        repl(s.prep_phase, p, 2),
                        s.prep_sid,
                        s.volatile_prep,
                        s.sent_shares,
                    )
                )

        # Send only after persisted reserve + use.
        for p in PREPS:
            sid = s.prep_sid[p]
            if s.prep_phase[p] == 2 and (p,sid) not in s.sent_shares:
                yield (
                    ("send_persisted_share", p, sid),
                    CrashState(
                        True,
                        s.durable_vote,
                        s.volatile_vote,
                        s.sent_votes,
                        s.prep_phase,
                        s.prep_sid,
                        s.volatile_prep,
                        s.sent_shares | {(p,sid)},
                    )
                )

        # Unsafe mutation: use and send volatile preprocessing.
        if unsafe_volatile_send:
            for p in PREPS:
                sid = s.volatile_prep[p]
                if sid != -1 and (p,sid) not in s.sent_shares:
                    yield (
                        ("UNSAFE_send_volatile_share", p, sid),
                        CrashState(
                            True,
                            s.durable_vote,
                            s.volatile_vote,
                            s.sent_votes,
                            s.prep_phase,
                            s.prep_sid,
                            s.volatile_prep,
                            s.sent_shares | {(p,sid)},
                        )
                    )

        for p in PREPS:
            if s.prep_phase[p] in (1,2):
                yield (
                    ("burn_prep", p),
                    CrashState(
                        True,
                        s.durable_vote,
                        s.volatile_vote,
                        s.sent_votes,
                        repl(s.prep_phase, p, 3),
                        s.prep_sid,
                        s.volatile_prep,
                        s.sent_shares,
                    )
                )

        # Crash drops ONLY volatile memory.
        yield (
            ("crash",),
            CrashState(
                False,
                s.durable_vote,
                (-1,) * len(DOMAINS),
                s.sent_votes,
                s.prep_phase,
                s.prep_sid,
                (-1,) * len(PREPS),
                s.sent_shares,
            )
        )

    else:
        # Restart conservatively burns persisted reserved/emitted preps.
        phases = tuple(
            3 if x in (1,2) else x
            for x in s.prep_phase
        )
        yield (
            ("restart",),
            CrashState(
                True,
                s.durable_vote,
                (-1,) * len(DOMAINS),
                s.sent_votes,
                phases,
                s.prep_sid,
                (-1,) * len(PREPS),
                s.sent_shares,
            )
        )

def crash_inv(s):
    for d, m in s.sent_votes:
        if s.durable_vote[d] != m:
            return False, "SentVoteWithoutDurableReservation"

    for d in DOMAINS:
        msgs = {m for dd,m in s.sent_votes if dd == d}
        if len(msgs) > 1:
            return False, "CrashInducedVoteEquivocation"

    for p, sid in s.sent_shares:
        if s.prep_sid[p] != sid:
            return False, "SentShareWithoutDurablePrepBinding"

    for p in PREPS:
        sids = {sid for pp,sid in s.sent_shares if pp == p}
        if len(sids) > 1:
            return False, "PreprocessingReuse"

        if s.prep_phase[p] == 0 and s.prep_sid[p] != -1:
            return False, "UnusedPrepHasDurableSession"

        if s.prep_phase[p] != 0 and s.prep_sid[p] == -1:
            return False, "UsedPrepMissingDurableSession"

    if not s.running:
        if any(x != -1 for x in s.volatile_vote):
            return False, "CrashRetainedVolatileVote"
        if any(x != -1 for x in s.volatile_prep):
            return False, "CrashRetainedVolatilePrep"

    return True, ""

def crash_equivocation_only(s):
    for d in DOMAINS:
        msgs = {m for dd,m in s.sent_votes if dd == d}
        if len(msgs) > 1:
            return False, "CrashInducedVoteEquivocation"

    for p in PREPS:
        sids = {sid for pp,sid in s.sent_shares if pp == p}
        if len(sids) > 1:
            return False, "PreprocessingReuse"

    return True, ""

# -------------------------------------------------------------------------
# Model D: evidence possession -> anchor
# -------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceState:
    have: tuple
    anchor: tuple
    cert: bool

E_INIT = EvidenceState(
    (False,) * N,
    (False,) * N,
    False,
)

def evidence_succ(s):
    for i in HONEST:
        if not s.have[i]:
            yield (
                ("receive_evidence", i),
                EvidenceState(
                    repl(s.have, i, True),
                    s.anchor,
                    s.cert,
                )
            )

        if s.have[i] and not s.anchor[i]:
            yield (
                ("anchor_vote", i),
                EvidenceState(
                    s.have,
                    repl(s.anchor, i, True),
                    s.cert,
                )
            )

    if not s.cert and sum(s.anchor[i] for i in HONEST) >= Q:
        yield (
            ("form_anchor_cert",),
            EvidenceState(s.have, s.anchor, True)
        )

def evidence_inv(s):
    for i in HONEST:
        if s.anchor[i] and not s.have[i]:
            return False, "EvidenceBeforeAnchor"

    if s.cert and sum(s.anchor[i] for i in HONEST) < Q:
        return False, "AnchorCertWithoutQuorum"

    return True, ""

# -------------------------------------------------------------------------
# Model E: actual seal message delivery across partition/heal
# -------------------------------------------------------------------------

@dataclass(frozen=True)
class SealNetState:
    honest_produced: tuple
    byz_produced: frozenset
    link_up: tuple
    delivered: frozenset
    cert: bool

SN_INIT = SealNetState(
    (-1,) * N,
    frozenset(),
    (True,) * N,
    frozenset(),
    False,
)

FINAL_BOUNDARY = 0

def seal_net_succ(s):
    # Honest seal production for the already-finalized boundary.
    for i in HONEST:
        if s.honest_produced[i] == -1:
            yield (
                ("produce_seal", i),
                SealNetState(
                    repl(s.honest_produced, i, FINAL_BOUNDARY),
                    s.byz_produced,
                    s.link_up,
                    s.delivered,
                    s.cert,
                )
            )

    for i in BYZ:
        if (i,FINAL_BOUNDARY) not in s.byz_produced:
            yield (
                ("byz_produce_seal", i),
                SealNetState(
                    s.honest_produced,
                    s.byz_produced | {(i,FINAL_BOUNDARY)},
                    s.link_up,
                    s.delivered,
                    s.cert,
                )
            )

    # Explicit partition/heal actions.
    for i in NODES:
        if s.link_up[i]:
            yield (
                ("partition", i),
                SealNetState(
                    s.honest_produced,
                    s.byz_produced,
                    repl(s.link_up, i, False),
                    s.delivered,
                    s.cert,
                )
            )
        else:
            yield (
                ("heal", i),
                SealNetState(
                    s.honest_produced,
                    s.byz_produced,
                    repl(s.link_up, i, True),
                    s.delivered,
                    s.cert,
                )
            )

    # Delivery requires both production and connectivity.
    for i in NODES:
        produced = (
            s.honest_produced[i] == FINAL_BOUNDARY
            if i in HONEST
            else (i,FINAL_BOUNDARY) in s.byz_produced
        )
        if (
            s.link_up[i]
            and produced
            and (i,FINAL_BOUNDARY) not in s.delivered
        ):
            yield (
                ("deliver_seal", i),
                SealNetState(
                    s.honest_produced,
                    s.byz_produced,
                    s.link_up,
                    s.delivered | {(i,FINAL_BOUNDARY)},
                    s.cert,
                )
            )

    delivered_voters = {
        i for i,b in s.delivered if b == FINAL_BOUNDARY
    }
    if not s.cert and len(delivered_voters) >= Q:
        yield (
            ("form_seal_cert",),
            SealNetState(
                s.honest_produced,
                s.byz_produced,
                s.link_up,
                s.delivered,
                True,
            )
        )

def seal_net_inv(s):
    for i,b in s.delivered:
        produced = (
            s.honest_produced[i] == b
            if i in HONEST
            else (i,b) in s.byz_produced
        )
        if not produced:
            return False, "DeliveredSealWithoutProducedSeal"

    if s.cert:
        voters = {i for i,b in s.delivered if b == FINAL_BOUNDARY}
        if len(voters) < Q:
            return False, "SealCertWithoutDeliveredQuorum"

    return True, ""

def take_action(state, successor, action):
    candidates = [
        t for a,t in successor(state)
        if a == action
    ]
    if not candidates:
        raise AssertionError(
            "Requested action is not reachable from state: %r" % (action,)
        )
    return candidates[0]

def real_partition_recovery_path():
    """
    This path uses the SAME seal transition relation as the exhaustive model.
    It is an existence/reachability witness, not a fairness/liveness proof.
    """
    s = SN_INIT
    trace = []

    for action in [
        ("produce_seal", 0),
        ("deliver_seal", 0),
        ("produce_seal", 1),
        ("deliver_seal", 1),
        ("partition", 2),
        ("produce_seal", 2),
    ]:
        s = take_action(s, seal_net_succ, action)
        trace.append(action)

    # At this point two honest seals are delivered, the third exists
    # durably but is partitioned, so no certificate is available.
    assert not s.cert
    assert len({i for i,b in s.delivered if b == FINAL_BOUNDARY}) == 2
    assert s.honest_produced[2] == FINAL_BOUNDARY
    assert s.link_up[2] is False

    for action in [
        ("heal", 2),
        ("deliver_seal", 2),
        ("form_seal_cert",),
    ]:
        s = take_action(s, seal_net_succ, action)
        trace.append(action)

    assert s.cert
    return trace

# -------------------------------------------------------------------------
# Main run
# -------------------------------------------------------------------------

def main():
    results = {}

    results["domain_votes_safe"] = explore(
        DV_INIT,
        lambda s: domain_vote_succ(s, unsafe=False),
        domain_vote_inv,
    )

    results["boundary_safe"] = explore(
        B_INIT,
        lambda s: boundary_succ(s, unsafe_honest_double_vote=False),
        boundary_inv,
    )

    results["crash_safe"] = explore(
        C_INIT,
        lambda s: crash_succ(s, unsafe_volatile_send=False),
        crash_inv,
    )

    results["evidence_safe"] = explore(
        E_INIT,
        evidence_succ,
        evidence_inv,
    )

    results["seal_network_safe"] = explore(
        SN_INIT,
        seal_net_succ,
        seal_net_inv,
    )

    # Negative controls / mutation tests.
    results["domain_votes_MUTANT"] = explore(
        DV_INIT,
        lambda s: domain_vote_succ(s, unsafe=True),
        domain_vote_inv,
    )

    results["boundary_MUTANT"] = explore(
        B_INIT,
        lambda s: boundary_succ(s, unsafe_honest_double_vote=True),
        boundary_uniqueness_only,
    )

    results["crash_MUTANT"] = explore(
        C_INIT,
        lambda s: crash_succ(s, unsafe_volatile_send=True),
        crash_equivocation_only,
    )

    partition_trace = real_partition_recovery_path()

    print("SAFE MODEL RESULTS")
    for name in [
        "domain_votes_safe",
        "boundary_safe",
        "crash_safe",
        "evidence_safe",
        "seal_network_safe",
    ]:
        r = results[name]
        assert r["failure"] is None, (name, r)
        print(
            "PASS %-22s states=%d transitions=%d"
            % (name, r["states"], r["transitions"])
        )

    print()
    print("NEGATIVE CONTROL RESULTS")
    for name in [
        "domain_votes_MUTANT",
        "boundary_MUTANT",
        "crash_MUTANT",
    ]:
        r = results[name]
        assert r["failure"] is not None, (
            "mutation unexpectedly passed", name, r
        )
        print(
            "EXPECTED-FAIL %-17s property=%s path=%s"
            % (name, r["failure"], r["counterexample"])
        )

    print()
    print("PARTITION RECOVERY REACHABILITY")
    print("PASS path=%s" % (partition_trace,))

    return results, partition_trace

if __name__ == "__main__":
    main()
