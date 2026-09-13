#!/usr/bin/env python3
"""Differential test: an INDEPENDENT re-implementation of B0 verification/extraction, written from
the specification sentences only, compared against T1 (sidecar_free_certificate_v1.44.py) on
>= 2,000 generated frame pairs.

Specification used (and nothing else from T1's code):
  * frame = header || payload; header = struct '>4sHH64s64s64sHHI' =
    magic 'CQ44', version 44, suite 0x44B0, cfg(64), domain(64), message(64), count 43,
    width (per-slot bytes), payload_len; frames > 32,768 bytes are invalid.
  * payload = signer bitmap u64 (big-endian, seat i = bit 1<<i) || exactly 43 fixed-width
    signatures, entries sorted ascending by seat index; popcount must be 43.
  * transcript for seat i: b'CQ44/B0/VOTE' || cfg || domain || message || bytes([i]).
  * conflict at equal (cfg, domain) [the (phase,epoch,height,view,set) coordinate] and different
    message [the candidate]; extraction = set intersection of the two bitmaps;
    blame for seat i = both of i's signatures verify over their own transcripts.
  * two valid quorums share >= 2*43-64 = 22 seats.
The provider (SymbolicSignatures) is shared: the differential is about frame parsing, set logic
and blame semantics, not about the signature scheme.

Run:  python3 differential_b0.py    (exit 0 iff zero disagreements)   or   python3 -m pytest -q differential_b0.py
"""
import importlib.util
import os
import random
import struct
import sys

sys.dont_write_bytecode = True
# Reference source tree: the read-only inputs this layer audits. The verification
# environment exports PQT_SRC; see docs/inputs-and-provenance.md.
PQT = os.environ.get('PQT_SRC')
if not PQT or not os.path.isdir(PQT):
    raise SystemExit('PQT_SRC is not set: source the environment activation script '
                     '(tooling/), or point PQT_SRC at a local copy of the research tree')


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PQT, filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


T1 = _load('sfc44_diff', 'sidecar_free_certificate_v1.44.py')

# ------------------------------------------------------------ independent reference
HEADER = '>4sHH64s64s64sHHI'
HLEN = struct.calcsize(HEADER)           # 208
MAX_FRAME = 32768
QUORUM, SEATS, MIN_COMMON = 43, 64, 22


class RefReject(Exception):
    pass


def ref_parse(frame, width):
    if type(frame) is not bytes:
        raise RefReject('not bytes')
    if len(frame) < HLEN or len(frame) > MAX_FRAME:
        raise RefReject('length')
    magic, version, suite, cfg, domain, message, count, w, plen = struct.unpack(HEADER, frame[:HLEN])
    if magic != b'CQ44' or version != 44 or suite != 0x44B0 or count != QUORUM:
        raise RefReject('header constants')
    if w != width or w <= 0:
        raise RefReject('width')
    payload = frame[HLEN:]
    if plen != len(payload) or len(payload) != 8 + QUORUM * w:
        raise RefReject('payload length')
    bitmap = int.from_bytes(payload[:8], 'big')
    seats = [i for i in range(SEATS) if (bitmap >> i) & 1]
    if len(seats) != QUORUM:
        raise RefReject('popcount')
    sigs = [payload[8 + k * w: 8 + (k + 1) * w] for k in range(QUORUM)]
    return {'cfg': cfg, 'domain': domain, 'message': message, 'bitmap': bitmap,
            'seats': seats, 'sigs': sigs}


def ref_transcript(cfg, domain, message, seat):
    return b'CQ44/B0/VOTE' + cfg + domain + message + bytes([seat])


def ref_verify(frame, public_keys, provider, expected_cfg):
    p = ref_parse(frame, provider.width)
    if p['cfg'] != expected_cfg:
        raise RefReject('cfg')
    for k, seat in enumerate(p['seats']):                 # ascending by index by construction
        if provider.verify(public_keys[seat], ref_transcript(p['cfg'], p['domain'], p['message'], seat),
                           p['sigs'][k]) is not True:
            raise RefReject('signature seat %d' % seat)
    return p


def ref_extract(f0, f1, public_keys, provider, expected_cfg):
    v0 = ref_verify(f0, public_keys, provider, expected_cfg)
    v1 = ref_verify(f1, public_keys, provider, expected_cfg)
    if v0['cfg'] != v1['cfg'] or v0['domain'] != v1['domain']:
        raise RefReject('different coordinate')
    if v0['message'] == v1['message']:
        raise RefReject('same candidate')
    common = [i for i in range(SEATS) if (v0['bitmap'] >> i) & (v1['bitmap'] >> i) & 1]
    if len(common) < MIN_COMMON:
        raise RefReject('overlap below 22 (impossible for two valid quorums)')
    out = []
    for seat in common:
        p0, p1 = v0['seats'].index(seat), v1['seats'].index(seat)
        ok0 = provider.verify(public_keys[seat], ref_transcript(v0['cfg'], v0['domain'], v0['message'], seat), v0['sigs'][p0])
        ok1 = provider.verify(public_keys[seat], ref_transcript(v1['cfg'], v1['domain'], v1['message'], seat), v1['sigs'][p1])
        if ok0 is True and ok1 is True:
            out.append((seat, p0, p1))
    return out


def ref_blame(f0, f1, public_keys, provider, expected_cfg, seat):
    try:
        found = ref_extract(f0, f1, public_keys, provider, expected_cfg)
    except RefReject:
        return False
    return any(s == seat for s, _, _ in found)


# ------------------------------------------------------------ pair generation
def make_registry(provider, tag):
    pks, sks = [], []
    for _ in range(SEATS):
        pk, sk = provider.keygen()
        pks.append(pk)
        sks.append(sk)
    return T1.RegistryB0(tuple(pks), tag), sks


def raw_frame(cfg, domain, message, width, seats, sigs):
    bitmap = 0
    for i in seats:
        bitmap |= 1 << i
    payload = bitmap.to_bytes(8, 'big') + b''.join(sigs)
    return struct.pack(HEADER, b'CQ44', 44, 0x44B0, cfg, domain, message, QUORUM, width, len(payload)) + payload


def generate_pairs(rng, provider, reg, sks, reg2, sks2):
    """Yield (category, f0, f1, registry, cfg)."""
    cfg, cfg2 = T1.cfg_b0(reg), T1.cfg_b0(reg2)
    D0, D1 = bytes(range(64)), bytes(range(1, 65))

    def msg():
        return rng.randbytes(64)

    def enc(seats, m, d=D0, r=reg, s=sks):
        return T1.encode_b0(r, provider, d, m, s, list(seats))

    def sig(seat, m, d=D0, c=cfg, s=sks):
        return provider.sign(s[seat], ref_transcript(c, d, m, seat))

    def two_msgs():
        m0 = msg()
        m1 = bytearray(m0)
        m1[rng.randrange(64)] ^= rng.randrange(1, 256)
        return m0, bytes(m1)

    def perm():
        p = list(range(SEATS))
        rng.shuffle(p)
        return p

    def overlap_sets(k):
        p = perm()
        return p[:QUORUM], p[:k] + p[QUORUM:2 * QUORUM - k]

    for _ in range(800):                                             # uniform overlap 22..43
        left, right = overlap_sets(rng.randint(MIN_COMMON, QUORUM))
        m0, m1 = two_msgs()
        yield 'overlap_uniform', enc(left, m0), enc(right, m1), reg, cfg
    for _ in range(300):                                             # natural overlap
        m0, m1 = two_msgs()
        yield 'overlap_natural', enc(perm()[:QUORUM], m0), enc(perm()[:QUORUM], m1), reg, cfg
    for _ in range(100):                                             # minimal overlap
        left, right = overlap_sets(MIN_COMMON)
        m0, m1 = two_msgs()
        yield 'overlap_min_22', enc(left, m0), enc(right, m1), reg, cfg
    for _ in range(100):                                             # full overlap
        left = perm()[:QUORUM]
        m0, m1 = two_msgs()
        yield 'overlap_full_43', enc(left, m0), enc(left, m1), reg, cfg
    for _ in range(100):                                             # two-bit bitmap difference
        left, right = overlap_sets(QUORUM - 1)
        m0, m1 = two_msgs()
        yield 'overlap_42_two_bit_diff', enc(left, m0), enc(right, m1), reg, cfg
    for _ in range(100):                                             # single-bit bitmap difference
        left = sorted(perm()[:QUORUM])
        m0, m1 = two_msgs()
        f0 = enc(left, m0)
        bit = rng.randrange(SEATS)
        if bit in left:                                              # drop one seat -> popcount 42
            seats = [i for i in left if i != bit]
        else:                                                        # add one seat -> popcount 44
            seats = sorted(left + [bit])
        f1 = raw_frame(cfg, D0, m1, provider.width, seats, [sig(i, m1) for i in seats])
        yield 'single_bit_bitmap_diff_invalid', f0, f1, reg, cfg
    for _ in range(100):                                             # disjoint (invalid popcounts)
        p = perm()
        m0, m1 = two_msgs()
        a, b = sorted(p[:32]), sorted(p[32:])
        f0 = raw_frame(cfg, D0, m0, provider.width, a, [sig(i, m0) for i in a])
        f1 = raw_frame(cfg, D0, m1, provider.width, b, [sig(i, m1) for i in b])
        yield 'disjoint_invalid', f0, f1, reg, cfg
    for _ in range(100):                                             # disjoint: 43 vs 21
        p = perm()
        m0, m1 = two_msgs()
        b = sorted(p[QUORUM:])
        f1 = raw_frame(cfg, D0, m1, provider.width, b, [sig(i, m1) for i in b])
        yield 'disjoint_43_vs_21_invalid', enc(p[:QUORUM], m0), f1, reg, cfg
    for _ in range(100):                                             # same candidate
        left, right = overlap_sets(rng.randint(MIN_COMMON, QUORUM))
        m = msg()
        yield 'same_message', enc(left, m), enc(right, m), reg, cfg
    for _ in range(100):                                             # different coordinate
        left, right = overlap_sets(rng.randint(MIN_COMMON, QUORUM))
        m0, m1 = two_msgs()
        yield 'different_domain', enc(left, m0), enc(right, m1, D1), reg, cfg
    for _ in range(100):                                             # cross registry
        left, right = overlap_sets(rng.randint(MIN_COMMON, QUORUM))
        m0, m1 = two_msgs()
        yield 'cross_registry', enc(left, m0), enc(right, m1, D0, reg2, sks2), reg, cfg
    for _ in range(100):                                             # one corrupted signature byte
        left, right = overlap_sets(rng.randint(MIN_COMMON, QUORUM))
        m0, m1 = two_msgs()
        f1 = bytearray(enc(right, m1))
        pos = HLEN + 8 + rng.randrange(QUORUM * provider.width)
        f1[pos] ^= rng.randrange(1, 256)
        yield 'corrupted_signature', enc(left, m0), bytes(f1), reg, cfg
    for _ in range(100):                                             # swapped slots
        left, right = overlap_sets(rng.randint(MIN_COMMON, QUORUM))
        m0, m1 = two_msgs()
        f1 = bytearray(enc(right, m1))
        w = provider.width
        i, j = rng.sample(range(QUORUM), 2)
        a, b = HLEN + 8 + i * w, HLEN + 8 + j * w
        f1[a:a + w], f1[b:b + w] = f1[b:b + w], f1[a:a + w]
        yield 'swapped_slots', enc(left, m0), bytes(f1), reg, cfg


def run(seed=2026, verbose=True):
    rng = random.Random(seed)
    provider = T1.SymbolicSignatures(width=64)
    reg, sks = make_registry(provider, b'DIFF/main')
    reg2, sks2 = make_registry(provider, b'DIFF/other')
    stats, disagreements = {}, []
    blame_checks = blame_disagree = 0
    for n, (cat, f0, f1, r, cfg) in enumerate(generate_pairs(rng, provider, reg, sks, reg2, sks2)):
        try:
            t1 = [(b.seat, b.position0, b.position1) for b in T1.extract_b0(f0, f1, r, provider, cfg)]
        except T1.CertError as e:
            t1 = 'REJECT:' + type(e).__name__
        try:
            ref = ref_extract(f0, f1, r.public_keys, provider, cfg)
        except RefReject as e:
            ref = 'REJECT'
        agree = (isinstance(t1, str) and isinstance(ref, str)) or (t1 == ref)
        s = stats.setdefault(cat, {'n': 0, 'agree': 0, 'accepted': 0})
        s['n'] += 1
        s['agree'] += agree
        s['accepted'] += not isinstance(ref, str)
        if not agree:
            disagreements.append((n, cat, t1 if isinstance(t1, str) else t1[:5], ref if isinstance(ref, str) else ref[:5]))
        if n % 25 == 0:                                              # blame semantics, all 64 seats
            for seat in range(SEATS):
                blame_checks += 1
                a = T1.verify_blame_b0(f0, f1, r, provider, cfg, seat)
                b = ref_blame(f0, f1, r.public_keys, provider, cfg, seat)
                if a != b:
                    blame_disagree += 1
                    disagreements.append((n, cat + '/blame seat %d' % seat, a, b))
    total = sum(s['n'] for s in stats.values())
    if verbose:
        print('differential_b0: %d pairs, %d disagreements, blame checks %d (%d disagree)'
              % (total, len(disagreements), blame_checks, blame_disagree))
        for cat, s in stats.items():
            print('  %-32s n=%4d agree=%4d accepted_by_both=%4d' % (cat, s['n'], s['agree'], s['accepted']))
        for d in disagreements[:20]:
            print('  DISAGREE', d)
    return total, disagreements, blame_checks


def test_differential_b0():
    total, disagreements, _ = run(verbose=True)
    assert total >= 2000
    assert disagreements == [], disagreements[:5]


if __name__ == '__main__':
    total, dis, _ = run()
    sys.exit(0 if not dis and total >= 2000 else 1)
