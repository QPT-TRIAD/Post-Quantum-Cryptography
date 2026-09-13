#!/usr/bin/env python3
r"""PQ infrastructure program — adversarial audit of S4's TESLA broadcast authenticator (v2.1).

Audits (does not re-implement) `TeslaSender` / `TeslaReceiver` / `WOTS` from
pq_infra_s4_embedded_broadcast_v2.0.py, imported via importlib.

  1. Adversarial network simulator: discrete-event link, sender clock as reference
     (integer ms), receiver clock = sender clock + skew (|skew| <= eps), per-packet
     delay in [0, dt] (uniform or forced), loss, duplication; delivery in arrival
     order so reordering emerges from delay variance. Two receiver time models:
     'granular' (the S4 receiver: local interval + sync = ceil(eps/T)) and
     'continuous' (RFC 4082 §3.5: upper bound floor((t_r + eps)/T) on the sender's
     interval).
  2. Boundary sweep over d, dt, eps (T fixed): every genuine packet is accepted iff
        S4 granular receiver:  ceil((dt + eps)/T) + ceil(eps/T) <= d - 1
        RFC 4082 continuous:   ceil((dt + 2*eps)/T)             <= d - 1
     (the RFC 4082 §3.4 rule d = ceil((dt + 2*eps)/T) + 1). Asserted at every grid
     point; forged acceptance asserted 0 at every grid point.
  3. Attack games FORGE / REPLAY / LATE / REORDER / KEY / ANCHOR, each with a
     positive control that proves the harness would have detected a win.
  4. Byte accounting from real send() output, link framing (LoRa, Iridium SBD),
     anchor amortisation.
  5. Untestable assumptions listed explicitly.
Bugs found in the S4 receiver are NOT patched there: `FixedTeslaReceiver` below is a
subclass that fixes them; each bug has a minimal reproduction test (S4-005, S4-006).
"""

import argparse
import heapq
import hmac
import importlib.util
import json
import os
import random
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('s4', os.path.join(_HERE, 's4_embedded_broadcast.py'))
s4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s4)
s1s2 = s4.s1s2
H, N, WOTS, TeslaSender, TeslaReceiver, _mac = s4.H, s4.N, s4.WOTS, s4.TeslaSender, s4.TeslaReceiver, s4._mac
MerkleSigner, merkle_verify = s1s2.MerkleSigner, s1s2.merkle_verify

LATE = 'key may already be disclosed'
T_MS = 1000
GRID_D, GRID_DT, GRID_EPS = (1, 2, 3, 4, 6, 8), (0, 250, 500, 1000, 1500, 2000, 3000, 4000, 6000), (0, 250, 500, 1000, 2000)


def cdiv(a, b):
    return -(-a // b)


def boundary_granular(d, dt, eps, T=T_MS):
    """Derived: worst genuine packet is sent at iT-1, delayed dt, seen by a receiver
    leading by eps -> local interval i + ceil((dt+eps)/T); passes the S4 test
    r + sync < i + d (sync = ceil(eps/T)) iff ceil((dt+eps)/T) + ceil(eps/T) <= d-1."""
    return cdiv(dt + eps, T) + cdiv(eps, T) <= d - 1


def boundary_continuous(d, dt, eps, T=T_MS):
    """RFC 4082 §3.5 test on the sender-clock upper bound t_r + eps: safe iff
    floor((t_r+eps)/T)+1 < i+d; worst case gives ceil((dt+2*eps)/T) <= d-1."""
    return cdiv(dt + 2 * eps, T) <= d - 1


# ------------------------------------------------ 1. adversarial network ----
class Net:
    def __init__(self, T, max_delay, skew, rng, loss=0.0, dup=0.0, eps=0, model='granular'):
        self.T, self.dt, self.skew, self.rng, self.loss, self.dup, self.eps, self.model = T, max_delay, skew, rng, loss, dup, eps, model
        self.q, self.n, self.lost = [], 0, []

    def r_interval(self, t_sender):
        t_r = t_sender + self.skew                       # receiver's local clock
        if self.model == 'continuous':                   # RFC 4082 §3.5 upper bound on sender interval (use with sync=0)
            return (t_r + self.eps) // self.T + 1
        return t_r // self.T + 1                         # S4: local interval, sync handled inside the receiver

    def send(self, t, pkt, tag='genuine', delay=None, lossy=True):
        if lossy and self.rng.random() < self.loss:
            self.lost.append((t, tag)); return
        d = self.dt if delay == 'max' else (self.rng.randint(0, self.dt) if delay is None else delay)
        heapq.heappush(self.q, (t + d, self.n, pkt, tag)); self.n += 1
        if self.rng.random() < self.dup:
            heapq.heappush(self.q, (t + self.rng.randint(0, self.dt), self.n, pkt, tag)); self.n += 1

    def run(self, rx):
        """Deliver in arrival order. Returns [(tag, index, t_arrival, reasons-for-this-index)]."""
        out = []
        while self.q:
            t, _, pkt, tag = heapq.heappop(self.q)
            nr = len(rx.rejected)
            rx.receive(pkt, self.r_interval(t))
            i = int.from_bytes(pkt[:4], 'big')
            out.append((tag, i, t, [why for j, why in rx.rejected[nr:] if j == i]))
        return out


# ------------------------------------------------- wrappers (bug fixes) -----
class FixedTeslaReceiver(TeslaReceiver):
    """BUG-1 fix: the chain walk records every intermediate key and every pending
    bucket whose key became derivable is drained (S4 only drains i-d of the packet
    that carried the key, so a lost/late disclosure strands buffered packets).
    BUG-2 fix: duplicate suppression moves AFTER authentication (S4 keys its
    replay filter on the unauthenticated (index, body), so a pre-injected
    junk-MAC copy makes the genuine packet a 'replay')."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.delivered = set()

    def _authenticate_key(self, i, k):
        j = max(x for x in self.known if x <= i)
        chain = [k]
        for _ in range(i - j):
            chain.append(H(b'tesla-chain', chain[-1]))
        if chain[-1] != self.known[j]:
            return False
        for step, key in enumerate(chain[:-1]):
            self.known[i - step] = key
        return True

    def receive(self, packet, receiver_interval):
        self.seen = set()                                  # disable the pre-authentication filter
        na = len(self.accepted)
        super().receive(packet, receiver_interval)
        for m in [m for m in self.pending if m in self.known]:
            for b, t in self.pending.pop(m):
                if hmac.compare_digest(_mac(self.known[m], b, self.tag_len), t):
                    self.accepted.append((m, b[4:]))
                else:
                    self.rejected.append((m, 'bad mac'))
        fresh, self.accepted = self.accepted[na:], self.accepted[:na]
        for m, p in fresh:                                 # post-authentication duplicate suppression
            if (m, p) in self.delivered:
                self.rejected.append((m, 'replay'))
            else:
                self.delivered.add((m, p)); self.accepted.append((m, p))


def anchor_msg(chain_id, anchor, chain_len, T, start):
    return chain_id.to_bytes(4, 'big') + anchor + chain_len.to_bytes(4, 'big') + T.to_bytes(4, 'big') + start.to_bytes(8, 'big')


class AnchoredReceiver:
    """Anchor install with an LMS-style (MerkleSigner) signature plus a monotonic
    chain-id / start-time rule (rejects rolled-back and replayed anchors)."""

    def __init__(self, root, pubseed, height, d, sync):
        self.root, self.pubseed, self.h, self.d, self.sync = root, pubseed, height, d, sync
        self.chain_id, self.start, self.rx, self.log = -1, -1, None, []

    def install(self, msg, sig):
        if len(msg) != 52 or not merkle_verify(self.root, self.pubseed, self.h, msg, sig):
            self.log.append('bad anchor signature'); return False
        cid, anchor, L, T, t0 = int.from_bytes(msg[:4], 'big'), msg[4:36], int.from_bytes(msg[36:40], 'big'), int.from_bytes(msg[40:44], 'big'), int.from_bytes(msg[44:52], 'big')
        if cid <= self.chain_id or t0 <= self.start:
            self.log.append('anchor rollback/replay'); return False
        self.chain_id, self.start, self.T = cid, t0, T
        self.rx = FixedTeslaReceiver(anchor, L, self.d, self.sync)
        self.log.append('anchor installed'); return True


# --------------------------------------------------- 2. boundary sweep ------
def sweep_point(d, dt, eps, T=T_MS, L=12, seed=1, rx_cls=TeslaReceiver, loss=0.0, model='granular'):
    rng = random.Random(f'{d}/{dt}/{eps}/{seed}/{model}')
    s = TeslaSender(b'sweep', L + d, d)
    sync = cdiv(eps, T) if model == 'granular' else 0
    c = dict(genuine=0, delivered_safe=0, accepted=0, late=0, forged=0, forged_accepted=0)
    for skew in (eps, rng.randint(-eps, eps)):           # worst case for false rejection, then random
        net = Net(T, dt, skew, rng, loss, eps=eps, model=model)
        rx = rx_cls(s.anchor, L + d, d, sync)
        pay = {}                                         # tag -> (interval, payload)
        for i in range(1, L + 1):
            w, r = 'W%03d' % i, 'R%03d' % i
            pay[w], pay[r] = (i, w.encode()), (i, r.encode())
            net.send(i * T - 1, s.send(i, pay[w][1]), w, delay='max')         # end of interval, max delay
            net.send((i - 1) * T + rng.randrange(T), s.send(i, pay[r][1]), r)
            if i - d >= 1:   # adversary at interval i holds K_1..K_{i-d}: forge for i+1 with newest key
                body = (i + 1).to_bytes(4, 'big') + b'FORGE%03d' % i
                net.send((i - 1) * T, body + _mac(s.keys[i - d], body, 16) + s.keys[i - d], 'forged', delay=0, lossy=False)
        for i in range(L + 1, L + d + 1):                # trailer: disclose the last d keys
            net.send((i - 1) * T, s.send(i, b'T%03d' % i), 'trailer', delay=0, lossy=False)
        out = net.run(rx)
        got = set(rx.accepted)
        c['genuine'] += len(pay); c['accepted'] += sum(v in got for v in pay.values())
        c['delivered_safe'] += len({tag for tag, i, t, why in out if tag in pay and not why})
        c['late'] += sum(1 for tag, i, t, why in out if tag in pay and LATE in why)
        c['forged'] += sum(tag == 'forged' for tag, *_ in out)
        c['forged_accepted'] += sum(p.startswith(b'FORGE') for _, p in got)
    c['all_accepted'] = c['late'] == 0 and c['accepted'] == c['genuine']
    return c


def boundary_sweep(model='granular', T=T_MS):
    pred = boundary_granular if model == 'granular' else boundary_continuous
    rows, mism = [], []
    for d in GRID_D:
        for dt in GRID_DT:
            for eps in GRID_EPS:
                c = sweep_point(d, dt, eps, T, model=model)
                p = pred(d, dt, eps, T)
                rows.append({'d': d, 'dt': dt, 'eps': eps, 'accepted_frac': round(c['accepted'] / c['genuine'], 3),
                             'late_frac': round(c['late'] / c['genuine'], 3), 'forged_accepted': c['forged_accepted'],
                             'predicted': p, 'measured': c['all_accepted']})
                if p != c['all_accepted'] or c['forged_accepted']:
                    mism.append(rows[-1])
    return rows, mism


# -------------------------------------------------------- 3. attack games ---
def game(gid, capabilities, win, attempts, successes, control, mechanism):
    return {'id': gid, 'capabilities': capabilities, 'winning_condition': win, 'attempts': attempts,
            'successes': successes, 'control': control, 'mechanism': mechanism}


def game_forge():
    L, d, c = 32, 2, 12                                   # adversary at interval c holds K_1..K_{c-d} and the transcript
    s = TeslaSender(b'forge', L, d)
    rx = FixedTeslaReceiver(s.anchor, L, d, 0)
    for i in range(1, c + 1):
        rx.receive(s.send(i, b'g%02d' % i), i)
    known = s.keys[1:c - d + 1]
    genuine_next = s.send(c + 1, b'g%02d' % (c + 1))
    tries, f = [], c + 1
    for k in known:                                        # (a) known key, future index, key re-labelled as K_{f-d}
        body = f.to_bytes(4, 'big') + b'ATTACK'
        tries.append(body + _mac(k, body, 16) + k)
        tries.append(body + _mac(k, body, 16) + s.keys[f - d - 1])   # (b) MAC with known key, latest genuine key field
    for bit in range(len(genuine_next) * 8):               # (c) every single-bit flip of the genuine next packet
        m = bytearray(genuine_next); m[bit // 8] ^= 1 << (bit % 8); tries.append(bytes(m))
    tries += [genuine_next[:-1], genuine_next[:20], genuine_next[:4]]       # truncations
    rx.receive(genuine_next, c + 1)
    for p in tries:
        rx.receive(p, c + 1)
    for i in range(c + 2, c + d + 3):                      # let the sender disclose K_{c+1}, K_{c+2}
        rx.receive(s.send(i, b'g%02d' % i), i)
    acc = set(rx.accepted)
    wins = sum(1 for j, p in acc if p != b'g%02d' % j)
    ctrl = FixedTeslaReceiver(s.anchor, L, d, 0)           # positive control: the real K_{c+1} (sender secret)
    body = (c + 1).to_bytes(4, 'big') + b'ATTACK'
    ctrl.receive(body + _mac(s.keys[c + 1], body, 16) + s.keys[c + 1 - d], c + 1)
    for i in range(c + 2, c + d + 2):
        ctrl.receive(s.send(i, b'x'), i)
    return game('FORGE', 'all disclosed keys K_1..K_{c-d}, full transcript, injection, bit-flips of in-flight packet',
                'a packet with adversarial payload appears in accepted', len(tries), wins,
                {'attempts': 1, 'successes': int((c + 1, b'ATTACK') in ctrl.accepted), 'with': 'true undisclosed K_{c+1}'},
                'MAC keyed by an undisclosed chain key; disclosed keys verified by chain walk; bit-flips fail MAC/key')


def game_replay():
    L, d = 32, 2
    s = TeslaSender(b'replay', L, d)
    rx = FixedTeslaReceiver(s.anchor, L, d, 0)
    pk = {i: s.send(i, b'cmd%02d' % i) for i in range(1, 12)}
    for i in range(1, 12):
        rx.receive(pk[i], i)
    n0 = len(rx.accepted)
    rx.receive(pk[3], 11)                                  # old authenticated packet, later interval (outside window)
    rx.receive(pk[9], 9)                                   # immediate re-delivery (inside window)
    rx.receive(pk[8], 9)
    for i in range(12, 14):
        rx.receive(s.send(i, b'cmd%02d' % i), i)
    wins = len(rx.accepted) - n0 - 2                       # cmd12, cmd13 are the only new legitimate acceptances
    why = [w for _, w in rx.rejected]
    fresh = TeslaReceiver(s.anchor, L, d, 0)               # control: state-less receiver (reboot) inside the window
    fresh.receive(pk[9], 9); fresh.receive(pk[11], 11)
    orig = TeslaReceiver(s.anchor, L, d, 0)                # original S4 receiver, same script
    for i in range(1, 12):
        orig.receive(pk[i], i)
    orig.receive(pk[3], 11); orig.receive(pk[9], 9)
    return game('REPLAY', 'record and re-deliver authenticated packets, any time', 'a replayed packet accepted twice',
                3, wins, {'attempts': 1, 'successes': int((9, b'cmd09') in fresh.accepted),
                          'with': 'receiver state lost (fresh instance) + immediate replay inside safe window'},
                f'late replay -> {LATE!r}; immediate replay -> post-auth duplicate ({why.count("replay")} replay rejections); '
                f'S4 original rejects both via (index, body) seen-set ({[w for _, w in orig.rejected]})')


def game_late():
    L, d, T, i = 32, 3, T_MS, 5
    attempts, wins, rows = 0, 0, []
    for eps in (0, 250, 500, 1000):
        s = TeslaSender(b'late', L, d)
        sync = cdiv(eps, T)
        rx = FixedTeslaReceiver(s.anchor, L, d, sync)
        net = Net(T, 0, -eps, random.Random(0))            # receiver LAGS by eps: sender is ahead (dangerous direction)
        t_disc = (i + d - 1) * T                           # sender discloses K_i in packet i+d, sent at this instant
        net.send(t_disc, s.send(i, b'late'), 'late', delay=0)                  # exactly at disclosure -> must reject
        net.send(t_disc + 1, s.send(i, b'later'), 'later', delay=0)
        for k in range(i + 1, i + d + 2):                  # disclosure packets, sent on time
            net.send((k - 1) * T, s.send(k, b'ok%02d' % k), delay=0)
        out = net.run(rx)
        attempts += 2; wins += sum(p in (b'late', b'later') for _, p in rx.accepted)
        r_edge = i + d - 1 - sync                          # last receiver interval the S4 rule accepts
        r2 = FixedTeslaReceiver(s.anchor, L, d, sync)
        r2.receive(s.send(i, b'edge'), r_edge); r2.receive(s.send(i, b'past'), r_edge + 1)
        for k in range(i + 1, i + d + 2):
            r2.receive(s.send(k, b'k'), k - sync)
        rows.append({'eps': eps, 'sync': sync, 'late_rejected': [w for tag, j, t, w in out if tag in ('late', 'later')],
                     'edge_interval': r_edge, 'edge_accepted': (i, b'edge') in r2.accepted, 'past_edge_accepted': (i, b'past') in r2.accepted})
    ctrl = FixedTeslaReceiver(s.anchor, L, d, -10 ** 6)    # positive control: safety test disabled
    ctrl.receive(s.send(i, b'late'), i + d + 5)
    for k in range(i + 1, i + d + 2):
        ctrl.receive(s.send(k, b'k'), k)
    return game('LATE', 'delay a genuine packet until its key is public (sender ahead of receiver by eps)',
                'a packet delivered at/after disclosure of its key is accepted', attempts, wins,
                {'attempts': 1, 'successes': int((i, b'late') in ctrl.accepted), 'with': 'safety test disabled'},
                'RFC 4082 §3.5 safe-packet test with sync = ceil(eps/T); boundary rows: %s' % json.dumps(rows))


def game_reorder():
    L, d = 32, 2
    s = TeslaSender(b'reorder', L, d)
    pk = {i: s.send(i, b'm%02d' % i) for i in range(1, 16)}
    rx = FixedTeslaReceiver(s.anchor, L, d, 0)
    order = [2, 1, 3, 5, 4, 7, 6, 8]                       # swapped packets and out-of-order disclosures, all inside the window
    orig = TeslaReceiver(s.anchor, L, d, 0)
    for r in (rx, orig):
        for n, i in enumerate(order):
            r.receive(pk[i], max(order[:n + 1]))           # receiver clock = latest interval seen so far
        for i in (12, 13, 14):                             # gap: packets 9, 10, 11 lost -> K_10 skips K_7..K_9
            r.receive(pk[i], i)
    stranded = sorted(set(dict(rx.accepted)) - set(dict(orig.accepted)))
    bad = TeslaReceiver(s.anchor, L, d, 0)                 # keys that do not chain to the anchor (S4 chain walk)
    other = TeslaSender(b'other-chain', L, d)
    attempts, wins = 0, 0
    for n, junk in enumerate((H(b'junk'), other.keys[3], s.keys[6], s.keys[4])):   # wrong chain / K_6, K_4 labelled K_3
        body = (5).to_bytes(4, 'big') + b'k%d' % n
        bad.receive(body + _mac(s.keys[5], body, 16) + junk, 5); attempts += 1
    wins += sum(1 for j in bad.known if j and bad.known[j] != s.keys[j])
    return game('REORDER', 'reorder, swap, drop disclosure packets; substitute disclosed keys', 'a key not chaining to the anchor is recorded as known',
                attempts, wins, {'attempts': 1, 'successes': int(sorted(dict(rx.accepted)) == [1, 2, 3, 4, 5, 6, 7, 8, 12]),
                                 'with': 'genuine out-of-order and gapped disclosures (fixed receiver accepts 1-8 and 12)'},
                f'chain walk to the latest known key handles gaps; S4 original accepted {sorted(dict(orig.accepted))}, '
                f'stranded {stranded} (BUG-1); rejections {[w for _, w in bad.rejected]}')


def game_key():
    L, d = 32, 2
    s = TeslaSender(b'key', L, d)
    rx = FixedTeslaReceiver(s.anchor, L, d, 0)
    for i in range(1, 9):
        rx.receive(s.send(i, b'g%02d' % i), i)             # K_1..K_6 disclosed and known to the adversary
    attempts, wins, now = 0, 0, 8                          # every injection is delivered at the receiver's CURRENT interval
    for j in range(1, 7):
        for jp in range(1, 12):
            if jp == j:
                continue
            body = (jp + d).to_bytes(4, 'big') + b'KEY'    # (1) K_j presented as the disclosure of K_{j'}
            rx.receive(body + _mac(s.keys[j], body, 16) + s.keys[j], now); attempts += 1
            if jp > now:                                   # (2) K_j as the MAC key of a packet for a future interval j'
                body = jp.to_bytes(4, 'big') + b'MACKEY'
                rx.receive(body + _mac(s.keys[j], body, 16) + H(b'nokey'), now); attempts += 1
    for i in range(9, 16):
        rx.receive(s.send(i, b'g%02d' % i), i)
    wins += sum(p in (b'KEY', b'MACKEY') for _, p in rx.accepted) + sum(rx.known[j] != s.keys[j] for j in rx.known)
    ctrl = FixedTeslaReceiver(s.anchor, L, d, 0)
    ok = ctrl._authenticate_key(5, s.keys[5])
    return game('KEY', 'all disclosed keys; relabel K_j as K_{j\'}; MAC with K_j for interval j\'',
                'a relabelled key is recorded or a packet MACed under K_j is accepted for j\' != j', attempts, wins,
                {'attempts': 1, 'successes': int(ok and ctrl.known[5] == s.keys[5]), 'with': 'K_5 presented as K_5'},
                'H^(j\'-j0)(K_j) equals the known K_{j0} iff j == j\'; MAC key is bound to the packet index via the chain position')


def game_anchor():
    h, d, T = 4, 2, T_MS
    signer = MerkleSigner(h, b'\x07' * 32)
    rcv = AnchoredReceiver(signer.root, signer.pubseed, h, d, 0)
    chains = {cid: TeslaSender(b'chain-%d' % cid, 64, d) for cid in (1, 2, 3)}
    msgs = {cid: anchor_msg(cid, chains[cid].anchor, 64, T, 10 ** 6 * cid) for cid in chains}
    sigs = {cid: signer.sign(msgs[cid]) for cid in chains}
    attempts, wins = 0, 0
    def attempt(msg, sig):
        nonlocal attempts, wins
        attempts += 1; wins += int(rcv.install(msg, sig))
    assert rcv.install(msgs[2], sigs[2])                   # genuine chain 2 installed (positive control)
    forged = anchor_msg(9, H(b'evil'), 64, T, 10 ** 8)
    attempt(forged, sigs[3])                               # signature of another message
    attempt(forged, MerkleSigner(h, b'\x66' * 32).sign(forged))   # adversary's own tree
    attempt(msgs[3][:4] + H(b'evil') + msgs[3][36:], sigs[3])     # anchor key substituted under a valid signature
    attempt(msgs[1], sigs[1])                              # rollback: genuinely signed older chain
    attempt(msgs[2], sigs[2])                              # replay of the current anchor
    old_verifies = merkle_verify(signer.root, signer.pubseed, h, msgs[1], sigs[1])
    # a packet from the rolled-back chain 1 is useless against the chain-2 receiver
    rcv.rx.receive(chains[1].send(5, b'old'), 5); rcv.rx.receive(chains[1].send(7, b'old'), 7)
    cross = (5, b'old') in rcv.rx.accepted
    ok3 = rcv.install(msgs[3], sigs[3])                    # forward roll to chain 3 is allowed
    return game('ANCHOR', 'inject anchors: forged, re-signed with own key, key-substituted, rolled back (validly signed), replayed',
                'a non-genuine or non-monotonic anchor is installed', attempts, wins + int(cross),
                {'attempts': 2, 'successes': int(ok3) + int(old_verifies), 'with': 'genuine chain 3 installs; old chain-1 anchor still VERIFIES (signature alone does not stop rollback)'},
                f'MerkleSigner(h={h}) signature over chain_id||anchor||L||T||start (52 B) + monotonic (chain_id, start) rule; log={rcv.log}')


# -------------------------------------------------------- 4. byte accounting -
LINK_FRAMING = {'LoRa SF12 EU868': (13, 51), 'Iridium SBD': (30, 340)}      # (framing bytes per frame, max payload per frame)


def byte_accounting():
    s = TeslaSender(b'bytes', 64, 2)
    out = {'packets': {}, 'anchor': {}, 'not_included': [
        'link framing (PHY preamble/header/CRC: LoRa 13 B, Iridium SBD ~30 B) and fragmentation into link frames',
        'the anchor message (52 B) and its hash-based signature (1,772 B LMS w8 h20 claimed; the executable MerkleSigner here is WOTS w16)',
        'the first d packets of a chain carry NO disclosed key: they are 20 B, not 52 B (measured)',
        'time-synchronisation traffic (RFC 4082 §3.5 needs a loose sync bound before any packet can be judged safe)',
        'retransmissions, chain roll-over, per-receiver state (pending buffers, known keys)']}
    for plen in (0, 20):
        pkt, early = s.send(10, b'x' * plen), s.send(1, b'x' * plen)
        row = {'packet_bytes': len(pkt), 'packet_bytes_first_d_intervals': len(early), 'payload': plen,
               'decomposition': {'index': 4, 'payload': plen, 'mac': 16, 'disclosed_key': 32},
               'authentication_overhead': len(pkt) - plen, 'links': {}}
        assert 4 + plen + 16 + 32 == len(pkt) and len(early) == 4 + plen + 16
        for link, (fr, mtu) in LINK_FRAMING.items():
            frames = cdiv(len(pkt), mtu)
            row['links'][link] = {'frames': frames, 'total_bytes_on_link': len(pkt) + frames * fr, 'framing_bytes': frames * fr}
        out['packets'][f'payload_{plen}'] = row
    lms = WOTS(256).sig_bytes(20)
    sig = MerkleSigner.sig_bytes(20) + N
    out['anchor'] = {'lms_w8_h20_signature_bytes': lms, 'anchor_message_bytes': 52, 'anchor_total_bytes': lms + 52,
                     'executable_signer_bytes_xmss_w16_h20': sig,
                     'amortised_per_message': {f'2^{k}': round((lms + 52) / 2 ** k, 4) for k in (10, 12, 16)}}
    return out


UNTESTABLE = [
    'Loose time synchronisation: the receiver holds a TRUE bound eps on |receiver clock - sender clock|; a violated bound is undetectable from inside the protocol and breaks the safe-packet test.',
    'PRF security of HMAC-SHA3-256 (truncated to 128 bits): forgery probability 2^-128 per online attempt; no offline advantage.',
    'One-wayness (preimage resistance) of the SHAKE256-256 chain hash: recovering K_{i+1} from K_i costs 2^256 classically / 2^128 Grover queries.',
    'Second-preimage resistance of the hash inside the WOTS/Merkle anchor signature and correct one-time-key state management at the signer.',
]

MODEL_DISCREPANCIES = [
    '"52 B per message" holds for intervals i > d only; packets for i <= d carry no disclosed key and are 20 B (measured).',
    'TeslaReceiver docstring says the receiver clock "may lead the sender by at most sync"; the code (and RFC 4082) bound the SENDER leading the receiver: the dangerous direction is receiver lag.',
    'The S4 receiver is interval-granular: with sync = ceil(eps/T) it needs ceil((dt+eps)/T)+ceil(eps/T) <= d-1, stricter than RFC 4082 continuous ceil((dt+2eps)/T) <= d-1 whenever eps is not a multiple of T (grid points differing counted in report).',
    'The 1,772 B anchor figure is the LMS w8 size formula (WOTS(256).sig_bytes); the only executable Merkle signer in the repo is WOTS w16 (2,820 B at h=20 incl. randomiser).',
    'pending buckets are never pruned: any injected index in the safe window allocates receiver memory (DoS surface, not a forgery).',
]

BUGS = [
    {'id': 'BUG-1', 'severity': 'liveness', 'where': 'TeslaReceiver.receive / _authenticate_key',
     'summary': 'Only pending[i-d] of the packet that carried a key is drained; if the packet disclosing K_i is lost or late, packets buffered for interval i are stranded although K_i = H(K_{i+1}) is derivable from the next disclosure.',
     'reproduction': "s=TeslaSender(b'x',16,1); r=TeslaReceiver(s.anchor,16,1,0); r.receive(s.send(1,b'one'),1); "
                     "r.receive(s.send(3,b'three'),3)  # packet 2 lost -> r.accepted == [] , r.pending has 1, r.known has 2",
     'fix': 'FixedTeslaReceiver records intermediate chain keys and drains every pending bucket whose key is known'},
    {'id': 'BUG-2', 'severity': 'denial of service (pre-injection)', 'where': 'TeslaReceiver.receive seen-set',
     'summary': 'Replay filter keys on the UNAUTHENTICATED (index, body): an adversary who guesses/observes the payload injects a junk-MAC copy first; the genuine packet is then rejected as replay and never authenticated.',
     'reproduction': "s=TeslaSender(b'x',16,1); r=TeslaReceiver(s.anchor,16,1,0); r.receive((3).to_bytes(4,'big')+b'STATUS'+bytes(48),3); "
                     "r.receive(s.send(3,b'STATUS'),3); r.receive(s.send(4,b''),4)  # -> (3,'replay') and accepted == []",
     'fix': 'FixedTeslaReceiver suppresses duplicates after MAC verification on (index, payload)'},
]


# ------------------------------------------------------------------ tests ----
class Tests(unittest.TestCase):
    def test_S4_001_wiring_benign_link_all_accepted(self):
        s = TeslaSender(b'w', 24, 2); rx = TeslaReceiver(s.anchor, 24, 2, 0)
        net = Net(T_MS, 0, 0, random.Random(0))
        for i in range(1, 21):
            net.send((i - 1) * T_MS + 10, s.send(i, b'p%02d' % i))
        net.run(rx)
        self.assertEqual(sorted(dict(rx.accepted)), list(range(1, 19)))       # 19, 20 pending (keys not yet disclosed)
        self.assertEqual(len(s.send(10, b'')), 52)

    def test_S4_002_boundary_inequality_matches_every_grid_point_granular(self):
        rows, mism = boundary_sweep('granular')
        self.assertEqual(len(rows), len(GRID_D) * len(GRID_DT) * len(GRID_EPS))
        self.assertEqual(mism, [])
        self.assertTrue(any(r['measured'] for r in rows) and any(not r['measured'] for r in rows))
        self.assertFalse(boundary_granular(1, 250, 0))                        # d=1 needs dt = eps = 0

    def test_S4_003_boundary_inequality_matches_every_grid_point_continuous(self):
        rows, mism = boundary_sweep('continuous')
        self.assertEqual(mism, [])
        diff = [r for r in rows if boundary_continuous(r['d'], r['dt'], r['eps']) != boundary_granular(r['d'], r['dt'], r['eps'])]
        self.assertTrue(all(r['eps'] % T_MS for r in diff) and diff)          # granularity costs only when eps not multiple of T

    def test_S4_004_loss_strands_original_not_fixed(self):
        o_acc = o_safe = 0
        for seed in range(1, 5):                            # 50 % loss: both copies of a disclosure are lost 1/4 of the time
            o = sweep_point(4, 500, 0, seed=seed, loss=0.5, rx_cls=TeslaReceiver)
            f = sweep_point(4, 500, 0, seed=seed, loss=0.5, rx_cls=FixedTeslaReceiver)
            self.assertEqual(f['accepted'], f['delivered_safe'])            # fixed: every safe delivery authenticated
            self.assertEqual((o['forged_accepted'], f['forged_accepted']), (0, 0))
            o_acc += o['accepted']; o_safe += o['delivered_safe']
        self.assertLess(o_acc, o_safe)                                      # original: BUG-1 strands safe packets

    def test_S4_005_bug1_reproduction(self):
        s = TeslaSender(b'x', 16, 1); r = TeslaReceiver(s.anchor, 16, 1, 0)
        r.receive(s.send(1, b'one'), 1); r.receive(s.send(3, b'three'), 3)
        self.assertEqual(r.accepted, []); self.assertIn(1, r.pending); self.assertIn(2, r.known)
        f = FixedTeslaReceiver(s.anchor, 16, 1, 0)
        f.receive(s.send(1, b'one'), 1); f.receive(s.send(3, b'three'), 3)
        self.assertEqual(f.accepted, [(1, b'one')])

    def test_S4_006_bug2_reproduction(self):
        s = TeslaSender(b'x', 16, 1)
        pre = (3).to_bytes(4, 'big') + b'STATUS' + bytes(48)
        r = TeslaReceiver(s.anchor, 16, 1, 0); f = FixedTeslaReceiver(s.anchor, 16, 1, 0)
        for rx in (r, f):
            rx.receive(pre, 3); rx.receive(s.send(3, b'STATUS'), 3); rx.receive(s.send(4, b''), 4)
        self.assertIn((3, 'replay'), r.rejected); self.assertEqual(r.accepted, [])
        self.assertEqual(f.accepted, [(3, b'STATUS')])
        f.receive(s.send(3, b'STATUS'), 3)                                     # exact replay inside the window
        self.assertIn((3, 'replay'), f.rejected); self.assertEqual(len(f.accepted), 1)

    def _check(self, g):
        self.assertEqual(g['successes'], 0, g); self.assertGreater(g['attempts'], 0)
        self.assertGreater(g['control']['successes'], 0, g)
        return g

    def test_S4_007_forge(self):
        g = self._check(game_forge()); self.assertGreater(g['attempts'], 400)

    def test_S4_008_replay(self):
        g = self._check(game_replay()); self.assertIn('replay', g['mechanism'])

    def test_S4_009_late_and_exact_boundary(self):
        g = self._check(game_late())
        rows = json.loads(g['mechanism'].split('rows: ', 1)[1])
        for r in rows:
            self.assertEqual(r['late_rejected'], [[LATE], [LATE]]); self.assertTrue(r['edge_accepted']); self.assertFalse(r['past_edge_accepted'])

    def test_S4_010_reorder_gaps_and_nonchaining_keys(self):
        g = self._check(game_reorder()); self.assertIn('bad disclosed key', g['mechanism'])

    def test_S4_011_key_relabel(self):
        g = self._check(game_key()); self.assertGreaterEqual(g['attempts'], 60)

    def test_S4_012_anchor_forge_rollback_replay(self):
        g = self._check(game_anchor()); self.assertEqual(g['attempts'], 5); self.assertEqual(g['control']['successes'], 2)

    def test_S4_013_byte_accounting(self):
        b = byte_accounting()
        self.assertEqual(b['packets']['payload_0']['authentication_overhead'], 52)
        self.assertEqual(b['packets']['payload_20']['packet_bytes'], 72)
        self.assertEqual(b['packets']['payload_0']['packet_bytes_first_d_intervals'], 20)
        self.assertEqual(b['packets']['payload_0']['links']['LoRa SF12 EU868']['frames'], 2)
        self.assertEqual(b['anchor']['lms_w8_h20_signature_bytes'], 1772)
        self.assertLess(b['anchor']['amortised_per_message']['2^16'], 0.03)

    def test_S4_014_report_is_json(self):
        rep = json.loads(json.dumps(report()))
        for k in ('boundary', 'games', 'bytes', 'bugs_found', 'untestable_assumptions', 'model_discrepancies'):
            self.assertIn(k, rep)
        self.assertTrue(all(g['successes'] == 0 for g in rep['games']))


def report():
    gran, mg = boundary_sweep('granular'); cont, mc = boundary_sweep('continuous')
    diff = sum(1 for r in gran if boundary_continuous(r['d'], r['dt'], r['eps']) != boundary_granular(r['d'], r['dt'], r['eps']))
    return {'audited_module': 's4_embedded_broadcast.py', 'T_ms': T_MS,
            'boundary': {'derived_granular_S4': 'ceil((dt+eps)/T) + ceil(eps/T) <= d-1   (sync = ceil(eps/T))',
                         'derived_continuous_rfc4082': 'ceil((dt+2*eps)/T) <= d-1   (RFC 4082 §3.4: d = ceil((dt+2eps)/T)+1)',
                         'grid': {'d': GRID_D, 'dt_ms': GRID_DT, 'eps_ms': GRID_EPS}, 'grid_points': len(gran),
                         'mismatches_granular': mg, 'mismatches_continuous': mc,
                         'forged_accepted_total': sum(r['forged_accepted'] for r in gran + cont),
                         'grid_points_where_granularity_costs_an_interval': diff,
                         'sweep_granular': gran},
            'games': [game_forge(), game_replay(), game_late(), game_reorder(), game_key(), game_anchor()],
            'bytes': byte_accounting(), 'bugs_found': BUGS,
            'untestable_assumptions': UNTESTABLE, 'model_discrepancies': MODEL_DISCREPANCIES}


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true'); g.add_argument('--report', action='store_true')
    a = ap.parse_args(argv)
    if a.report:
        print(json.dumps(report(), indent=1, default=str)); return 0
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if r.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
