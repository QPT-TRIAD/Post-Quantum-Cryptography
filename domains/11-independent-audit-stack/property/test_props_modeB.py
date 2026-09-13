#!/usr/bin/env python3
"""Property / malformed-input layer for T2 = hidden_signer_modeB_v1.50.py (Mode B, research),
which imports Field / QuadMap / registry / Parsed / Blame unchanged from hidden_signer_modeB_v1.46.py.

Real API (adapted): parameters are built with m46.make_params(n, expansion, seed); the module's own
toy parameters are n=32, expansion=16 (V150Tests) and those are used here. There is no `demo_256`
in v1.50 (v1.46 has demo_256() at n=256; the production field is only used for the kernel test).
  Challenge(p, cfg, domain, message): .a .b .c .ctr .cols .apply(s) .invert(t)
  handle(p, ch, (s, r)) -> bytes; encode(p, registry, secrets, domain, message, seats, proof)
  parse(p, frame) -> Parsed(cfg, domain, message, handles, proof)
  extract(p, registry, f0, f1) -> {'seats', 'complete', 'blames'} ; verify_blame(p, registry, f0, f1, blame)
  check_relation(p, registry, parsed, rows)

Run:  python3 -m pytest -q test_props_modeB.py   or   python3 test_props_modeB.py
"""
import hashlib
import importlib.util
import os
import random
import struct
import sys
import unittest

sys.dont_write_bytecode = True
from hypothesis import HealthCheck, given, settings, strategies as st, assume, example

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


M50 = _load('modeB50_audit', 'hidden_signer_modeB_v1.50.py')
M46 = M50.m46

settings.register_profile('audit', deadline=None, derandomize=True, print_blob=True,
                          suppress_health_check=list(HealthCheck))
settings.load_profile('audit')

Q, NS, MIN_OV, HB = M50.QUORUM, M50.N_SEATS, M50.MIN_OVERLAP, M46.HEADER_BYTES
P = M46.make_params(n=32, expansion=16, seed=b'audit50')
NBITS, HW = P.n, P.handle_bytes                      # 32, 4
D0, D1, D2 = bytes(range(64)), bytes(range(1, 65)), bytes(range(2, 66))
REG, SEC = M46.build_registry(P, b'epoch', (D0, D1), random.Random(5050))
CFG = M46.cfg_of(REG, P)
REG2, SEC2 = M46.build_registry(P, b'epoch-2', (D0,), random.Random(99))
ModeBError = M46.ModeBError


def enc(seats, message, domain=D0, reg=REG, sec=SEC, proof=b'STRUCTURE-ONLY'):
    try:
        return M50.encode(P, reg, sec, domain, message, list(seats), proof)
    except ModeBError as e:
        if 'handle collision' in str(e):                 # birthday event at n=32: ~2e-7 per frame
            assume(False)
        raise


def rebuild(parsed, handles, proof=None, count=Q, width=HW, magic=M50.MAGIC, version=M50.VERSION,
            suite=M50.SUITE, cfg=None, domain=None, message=None, plen=None):
    payload = b''.join(handles) + (parsed.proof if proof is None else proof)
    header = struct.pack(M46.HEADER_FORMAT, magic, version, suite,
                         parsed.cfg if cfg is None else cfg, parsed.domain if domain is None else domain,
                         parsed.message if message is None else message, count, width,
                         len(payload) if plen is None else plen)
    return header + payload


def f2_rank_nullspace(cols, n):
    """Rank and a kernel basis of the F2 matrix whose columns are cols (bit k of cols[j] = M[k][j]);
    kernel = {s : XOR_j s_j cols[j] = 0}. Independent of the module's solver."""
    rows = [sum(((cols[j] >> k) & 1) << j for j in range(n)) for k in range(n)]
    pivots, r = [], 0
    for c in range(n):
        piv = next((i for i in range(r, n) if (rows[i] >> c) & 1), None)
        if piv is None:
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        for i in range(n):
            if i != r and (rows[i] >> c) & 1:
                rows[i] ^= rows[r]
        pivots.append(c)
        r += 1
    pivset = set(pivots)
    basis = []
    for fc in (c for c in range(n) if c not in pivset):
        v = 1 << fc
        for i, pc in enumerate(pivots):
            if (rows[i] >> fc) & 1:
                v |= 1 << pc
        basis.append(v)
    return r, basis


def span(basis):
    out = {0}
    for b in basis:
        out |= {x ^ b for x in out}
    return out


def D_map(field, a, b, c, s):
    s2 = field.mul(s, s)
    return field.mul(a, s) ^ field.mul(b, s2) ^ field.mul(c, field.mul(s2, s2))


def triple_for_ctr(p, cfg, domain, message, ctr):
    """The (c_a, c_b, c_c) the module derives for a given counter (its documented derivation)."""
    hb = p.handle_bytes
    buf = hashlib.shake_256(b'CQ50/c' + cfg + domain + message + struct.pack('>I', ctr)).digest(3 * hb)
    o = p.field.order
    return (int.from_bytes(buf[:hb], 'big') & o, int.from_bytes(buf[hb:2 * hb], 'big') & o,
            int.from_bytes(buf[2 * hb:], 'big') & o)


msg64 = st.binary(min_size=64, max_size=64)
perm64 = st.permutations(list(range(NS)))
u32 = st.integers(0, (1 << NBITS) - 1)


@st.composite
def distinct_msgs(draw):
    m0 = draw(msg64)
    m1 = bytearray(m0)
    m1[draw(st.integers(0, 63))] ^= draw(st.integers(1, 255))
    return m0, bytes(m1)


@st.composite
def overlap_pair(draw, lo=MIN_OV, hi=Q):
    p = draw(perm64)
    k = draw(st.integers(lo, hi))
    return p[:Q], p[:k] + p[Q:2 * Q - k], k


SEATS0 = list(range(Q))
M0 = hashlib.shake_256(b'm0').digest(64)
M1 = hashlib.shake_256(b'm1').digest(64)
FRAME0 = enc(SEATS0, M0)
PARSED0 = M50.parse(P, FRAME0)


# =============================================================================
class ModeBProperties(unittest.TestCase):

    # ------------------------------------------------------------ round trip
    @given(perm64, msg64, st.sampled_from([D0, D1]), st.binary(max_size=40), st.randoms(use_true_random=False))
    @settings(max_examples=100)
    def test_encode_parse_roundtrip(self, p, m, d, proof, rnd):
        seats = p[:Q]
        f = enc(seats, m, d, proof=proof)
        self.assertEqual(len(f), HB + Q * HW + len(proof))
        parsed = M50.parse(P, f)
        self.assertEqual((parsed.cfg, parsed.domain, parsed.message, parsed.proof), (CFG, d, m, proof))
        ch = M50.Challenge(P, CFG, d, m)
        expect = sorted(M50.handle(P, ch, SEC[d][i]) for i in seats)
        self.assertEqual(list(parsed.handles), expect)
        self.assertTrue(all(parsed.handles[j] < parsed.handles[j + 1] for j in range(Q - 1)))
        shuffled = list(seats)
        rnd.shuffle(shuffled)
        self.assertEqual(enc(shuffled, m, d, proof=proof), f)      # deterministic, order independent

    # ------------------------------------------------------------ extraction
    @given(overlap_pair(), distinct_msgs())
    @settings(max_examples=20)
    def test_extraction_complete_on_conflicts(self, pair, msgs):
        """Conflict (same cfg, same domain, m0 != m1): extract names exactly the intersection,
        complete=True, every blame verifies, and each blame carries the seat's true opening."""
        left, right, k = pair
        m0, m1 = msgs
        f0, f1 = enc(left, m0), enc(right, m1)
        res = M50.extract(P, REG, f0, f1)
        inter = sorted(set(left) & set(right))
        self.assertEqual(res['seats'], inter)
        self.assertTrue(res['complete'])
        self.assertEqual(len(res['blames']), k)
        h0, h1 = M50.parse(P, f0).handles, M50.parse(P, f1).handles
        c0, c1 = M50.Challenge(P, CFG, D0, m0), M50.Challenge(P, CFG, D0, m1)
        for b in res['blames']:
            self.assertTrue(M50.verify_blame(P, REG, f0, f1, b))
            self.assertEqual((b.s, b.r), SEC[D0][b.seat])
            self.assertEqual(h0[b.position0], M50.handle(P, c0, (b.s, b.r)))
            self.assertEqual(h1[b.position1], M50.handle(P, c1, (b.s, b.r)))
        for seat in set(range(NS)) - set(inter):              # no honest seat is blamed
            self.assertNotIn(seat, res['seats'])

    @given(overlap_pair(), distinct_msgs())
    @settings(max_examples=4)
    def test_extraction_symmetric(self, pair, msgs):
        left, right, _ = pair
        m0, m1 = msgs
        f0, f1 = enc(left, m0), enc(right, m1)
        a, b = M50.extract(P, REG, f0, f1), M50.extract(P, REG, f1, f0)
        self.assertEqual(a['seats'], b['seats'])
        self.assertEqual([(x.seat, x.position0, x.position1) for x in a['blames']],
                         [(x.seat, x.position1, x.position0) for x in b['blames']])

    @given(overlap_pair(lo=MIN_OV, hi=26), distinct_msgs(), st.integers(0, 25), u32, u32)
    @settings(max_examples=8)
    def test_extraction_never_aborts_on_count(self, pair, msgs, drop, fs, fr):
        """One common seat's handle in frame1 replaced by an unregistered opening: the remaining
        common seats are still named, complete reflects the 22 threshold, nothing raises."""
        left, right, k = pair
        m0, m1 = msgs
        inter = sorted(set(left) & set(right))
        dropped = inter[drop % len(inter)]
        f0, f1 = enc(left, m0), enc(right, m1)
        c1 = M50.Challenge(P, CFG, D0, m1)
        parsed = M50.parse(P, f1)
        hs = list(parsed.handles)
        fake = M50.handle(P, c1, (fs, fr))
        assume(fake not in hs)
        hs[hs.index(M50.handle(P, c1, SEC[D0][dropped]))] = fake
        f1b = rebuild(parsed, sorted(hs))
        res = M50.extract(P, REG, f0, f1b)
        self.assertEqual(res['seats'], [s for s in inter if s != dropped])
        self.assertEqual(res['complete'], k - 1 >= MIN_OV)
        self.assertEqual(len(res['blames']), k - 1)
        self.assertTrue(all(M50.verify_blame(P, REG, f0, f1b, b) for b in res['blames']))

    @given(overlap_pair(), distinct_msgs())
    @settings(max_examples=10)
    def test_non_conflicts_rejected(self, pair, msgs):
        left, right, _ = pair
        m0, m1 = msgs
        f0 = enc(left, m0)
        with self.assertRaises(ModeBError):                   # same message
            M50.extract(P, REG, f0, enc(right, m0))
        with self.assertRaises(ModeBError):                   # different domain
            M50.extract(P, REG, f0, enc(right, m1, D1))
        with self.assertRaises(ModeBError):                   # other registry (cfg mismatch)
            M50.extract(P, REG, f0, enc(right, m1, D0, REG2, SEC2))
        with self.assertRaises(ModeBError):                   # unregistered domain in header
            M50.extract(P, REG, rebuild(M50.parse(P, f0), M50.parse(P, f0).handles, domain=D2),
                        rebuild(M50.parse(P, enc(right, m1)), M50.parse(P, enc(right, m1)).handles, domain=D2))

    # ------------------------------------------------------------ canonicality
    @given(st.binary(max_size=130).filter(lambda b: len(b) != 64))
    @example(b'')
    @example(bytes(63))
    @example(bytes(65))
    @settings(max_examples=60)
    def test_message_must_be_exactly_64_bytes(self, m):
        with self.assertRaises(ModeBError):
            M50.encode(P, REG, SEC, D0, m, SEATS0)

    def test_message_must_be_canonical_bytes(self):
        for bad in (bytearray(M0), memoryview(M0), M0.decode('latin-1'), None, 5):
            with self.assertRaises(ModeBError):
                M50.encode(P, REG, SEC, D0, bad, SEATS0)

    def test_domain_length_not_validated_FINDING(self):
        """v1.50 fix (3) requires the message to be exactly 64 bytes 'so the header field and the
        handle derivation see the same bytes'. The same rule is not applied to the domain: struct
        '64s' silently truncates a 65-byte domain / zero-pads a 63-byte one, so the challenge is
        derived from bytes the header does not carry and the frame is later unextractable
        ('domain mismatch'). Property asserted: encode rejects a non-64-byte domain."""
        long_d, short_d = bytes(range(65)), bytes(range(63))
        reg, sec = M46.build_registry(P, b'epoch-len', (long_d, short_d), random.Random(7))
        consequences = {}
        for d in (long_d, short_d):
            try:
                f = M50.encode(P, reg, sec, d, M0, SEATS0)
                parsed = M50.parse(P, f)
                consequences[len(d)] = ('encoded; header domain == input: %s' % (parsed.domain == d))
            except ModeBError as e:
                consequences[len(d)] = 'rejected: %s' % e
        for d in (long_d, short_d):
            with self.assertRaises(ModeBError, msg='domain len %d: %s' % (len(d), consequences[len(d)])):
                M50.encode(P, reg, sec, d, M0, SEATS0)

    # ------------------------------------------------------------ Challenge
    @given(st.binary(min_size=64, max_size=64), st.sampled_from([D0, D1]), msg64, u32, u32)
    @settings(max_examples=100)
    def test_challenge_invertible_linear_minimal_counter(self, cfg, d, m, s, t):
        ch = M50.Challenge(P, cfg, d, m)
        self.assertEqual(ch.apply(s ^ t), ch.apply(s) ^ ch.apply(t))       # F2-linear
        self.assertEqual(ch.apply(0), 0)
        self.assertEqual(ch.invert(ch.apply(s)), s)                         # left inverse
        self.assertEqual(ch.apply(ch.invert(t)), t)                         # right inverse
        rank, _ = f2_rank_nullspace(ch.cols, NBITS)
        self.assertEqual(rank, NBITS)                                       # L_c invertible
        self.assertEqual((ch.a, ch.b, ch.c), triple_for_ctr(P, cfg, d, m, ch.ctr))
        for ctr in range(ch.ctr):                                           # ctr is the smallest
            a, b, c = triple_for_ctr(P, cfg, d, m, ctr)
            cols = [D_map(P.field, a, b, c, 1 << j) for j in range(NBITS)]
            self.assertLess(f2_rank_nullspace(cols, NBITS)[0], NBITS)
        self.assertLess(ch.ctr, 32)

    # ------------------------------------------------------------ kernel claim
    @given(u32, u32, u32)
    @example(1, 0, 0)
    @example(0, 1, 0)
    @example(0, 0, 1)
    @example(1, 1, 1)
    @settings(max_examples=300)
    def test_kernel_dimension_at_most_2_n32(self, a, b, c):
        """D(s) = a s + b s^2 + c s^4 is F2-linear of s-degree 4: for (a,b,c) != 0 its kernel has
        at most 4 elements (dimension <= 2); with c == 0 at most 2 (dimension <= 1). The module's
        solve_f2 (max_free=2) must return exactly that kernel for rhs 0."""
        assume((a, b, c) != (0, 0, 0))
        f = P.field
        cols = [D_map(f, a, b, c, 1 << j) for j in range(NBITS)]
        rank, basis = f2_rank_nullspace(cols, NBITS)
        dim = NBITS - rank
        self.assertLessEqual(dim, 2)
        if c == 0:
            self.assertLessEqual(dim, 1)
        kernel = span(basis)
        self.assertEqual(len(kernel), 1 << dim)
        for s in kernel:
            self.assertEqual(D_map(f, a, b, c, s), 0)
        self.assertEqual(set(M50.solve_f2(cols, 0, NBITS)), kernel)

    def test_kernel_dimension_at_most_2_n256_production_field(self):
        f = M46.Field(256)
        rng = random.Random(256)
        cases = [(rng.getrandbits(256), rng.getrandbits(256), rng.getrandbits(256)) for _ in range(6)]
        cases += [(rng.getrandbits(256), rng.getrandbits(256), 0), (rng.getrandbits(256), 0, 0),
                  (0, rng.getrandbits(256), 0), (0, 0, rng.getrandbits(256)), (1, 1, 1)]
        dims = []
        for a, b, c in cases:
            cols = [D_map(f, a, b, c, 1 << j) for j in range(256)]
            rank, basis = f2_rank_nullspace(cols, 256)
            dim = 256 - rank
            dims.append(dim)
            self.assertLessEqual(dim, 2, (hex(a), hex(b), hex(c)))
            if c == 0:
                self.assertLessEqual(dim, 1)
            for s in span(basis):
                self.assertEqual(D_map(f, a, b, c, s), 0)
        print('\n[modeB] n=256 kernel dims over 11 triples:', dims)

    @given(distinct_msgs())
    @settings(max_examples=30)
    def test_extraction_difference_map_kernel_le_2(self, msgs):
        """The extraction system (L_c0 + L_c1)(s) = Z0 + Z1 has at most 4 solutions per handle pair."""
        m0, m1 = msgs
        c0, c1 = M50.Challenge(P, CFG, D0, m0), M50.Challenge(P, CFG, D0, m1)
        dcols = [x ^ y for x, y in zip(c0.cols, c1.cols)]
        assume((c0.a ^ c1.a, c0.b ^ c1.b, c0.c ^ c1.c) != (0, 0, 0))
        rank, basis = f2_rank_nullspace(dcols, NBITS)
        self.assertLessEqual(NBITS - rank, 2)
        self.assertEqual(set(M50.solve_f2(dcols, 0, NBITS)), span(basis))

    def test_all_three_coefficients_colliding_names_nobody_observation(self):
        """Documented limit: if c_a, c_b, c_c all collide (768-bit event) the difference map is 0,
        solve_f2 gives up (free > 2) and extraction names nobody, silently (no error)."""
        zero = [0] * NBITS
        self.assertEqual(f2_rank_nullspace(zero, NBITS)[0], 0)
        self.assertEqual(M50.solve_f2(zero, 0, NBITS), [])
        self.assertEqual(M50.solve_f2(zero, 12345, NBITS), [])

    # ------------------------------------------------------------ relation
    @given(perm64, msg64)
    @settings(max_examples=8)
    def test_check_relation_accepts_honest_rejects_tampered(self, p, m):
        seats = p[:Q]
        f = enc(seats, m)
        parsed = M50.parse(P, f)
        ch = M50.Challenge(P, CFG, D0, m)
        by = {M50.handle(P, ch, SEC[D0][i]): i for i in seats}
        rows = [(by[z],) + SEC[D0][by[z]] for z in parsed.handles]
        self.assertTrue(M50.check_relation(P, REG, parsed, rows))
        for bad in ([(rows[0][0], rows[0][1] ^ 1, rows[0][2])] + rows[1:],
                    [(rows[0][0], rows[0][1], rows[0][2] ^ 1)] + rows[1:],
                    [(rows[1][0],) + rows[0][1:]] + rows[1:],                # duplicate seat
                    rows[1:] + rows[:1],                                      # misaligned
                    rows[:-1]):
            with self.assertRaises(ModeBError):
                M50.check_relation(P, REG, parsed, bad)

    # ------------------------------------------------------------ malformed catalogue
    def _catalogue(self):
        F, p0 = FRAME0, PARSED0
        hs = list(p0.handles)
        c0 = M50.Challenge(P, CFG, D0, M0)
        unreg = M50.handle(P, c0, (0x1234567, 0x89ABCDE))
        corrupt = bytes([hs[5][0]]) + bytes([hs[5][1] ^ 0x40]) + hs[5][2:]
        parse = lambda fr: M50.parse(P, fr)                                # noqa: E731
        must_reject = [
            ('empty', lambda: parse(b'')),
            ('truncated_minus_1', lambda: parse(F[:-1])),
            ('truncated_below_min', lambda: parse(F[:HB + Q * HW - 1])),
            ('truncated_header_only', lambda: parse(F[:HB])),
            ('trailing_byte', lambda: parse(F + b'\x00')),
            ('duplicated_entry', lambda: parse(rebuild(p0, [hs[0], hs[0]] + hs[2:]))),
            ('duplicate_signer_same_handle_twice', lambda: parse(rebuild(p0, hs[:5] + [hs[5]] + hs[5:-1]))),
            ('reordered_swap_0_1', lambda: parse(rebuild(p0, [hs[1], hs[0]] + hs[2:]))),
            ('reordered_reversed', lambda: parse(rebuild(p0, hs[::-1]))),
            ('oversized_32769', lambda: parse(rebuild(p0, hs, proof=bytes(32769 - HB - Q * HW)))),
            ('count_42', lambda: parse(rebuild(p0, hs, count=42))),
            ('count_44', lambda: parse(rebuild(p0, hs, count=44))),
            ('width_plus_1', lambda: parse(rebuild(p0, hs, width=HW + 1))),
            ('width_zero', lambda: parse(rebuild(p0, hs, width=0))),
            ('invalid_length_plen_minus_1', lambda: parse(rebuild(p0, hs, plen=len(F) - HB - 1))),
            ('invalid_length_plen_plus_1', lambda: parse(rebuild(p0, hs, plen=len(F) - HB + 1))),
            ('wrong_magic', lambda: parse(rebuild(p0, hs, magic=b'CQ46'))),
            ('wrong_version_46', lambda: parse(rebuild(p0, hs, version=46))),
            ('wrong_suite_46B0', lambda: parse(rebuild(p0, hs, suite=0x46B0))),
            ('invalid_encoding_bytearray', lambda: parse(bytearray(F))),
            ('invalid_encoding_memoryview', lambda: parse(memoryview(F))),
            ('invalid_encoding_str', lambda: parse(F.decode('latin-1'))),
            ('invalid_encoding_none', lambda: parse(None)),
            ('invalid_encoding_int', lambda: parse(7)),
            ('encode_42_seats', lambda: M50.encode(P, REG, SEC, D0, M0, list(range(42)))),
            ('encode_duplicate_seat', lambda: M50.encode(P, REG, SEC, D0, M0, list(range(42)) + [0])),
            ('encode_oversized_proof', lambda: M50.encode(P, REG, SEC, D0, M0, SEATS0, bytes(32769 - HB - Q * HW))),
            ('extract_same_message', lambda: M50.extract(P, REG, F, enc(list(range(21, 64)), M0))),
            ('extract_cfg_mismatch', lambda: M50.extract(P, REG2, F, enc(list(range(21, 64)), M1))),
            ('extract_unregistered_domain', lambda: M50.extract(P, REG, rebuild(p0, hs, domain=D2), rebuild(p0, hs, domain=D2, message=M1))),
        ]
        # Structure-only parse: the proof slot is opaque and unverified (no qualified backend),
        # so parse cannot know whether a handle opens a registered key. These are accepted by
        # design; the property that IS offered is that extract / verify_blame never name a seat
        # through such a handle.
        by_design = [
            ('signer_not_in_set_unregistered_handle', rebuild(p0, sorted(hs[:-1] + [unreg]))),
            ('corrupted_handle_byte', rebuild(p0, sorted(hs[:5] + [corrupt] + hs[6:]))),
            ('trailing_bytes_absorbed_into_proof', rebuild(p0, hs, proof=p0.proof + b'\x00' * 7)),
        ]
        return must_reject, by_design

    def test_malformed_catalogue(self):
        must_reject, by_design = self._catalogue()
        accepted, wrong_exc, rejected = [], [], {}
        for name, fn in must_reject:
            try:
                fn()
                accepted.append(name)
            except ModeBError as e:
                rejected[name] = str(e)
            except Exception as e:                                          # noqa: BLE001
                wrong_exc.append((name, type(e).__name__, str(e)[:60]))
        design = {}
        f_other = enc(list(range(21, 64)), M1)
        for name, frame in by_design:
            try:
                parsed = M50.parse(P, frame)
                res = M50.extract(P, REG, frame, f_other)
                design[name] = 'parse ACCEPTS (structure-only); extract names %d seats, all registered'\
                    % len(res['seats'])
                self.assertTrue(all(0 <= s < NS for s in res['seats']))
                handles = set(parsed.handles)
                for b in res['blames']:                                     # no blame through a bad handle
                    self.assertTrue(M50.verify_blame(P, REG, frame, f_other, b))
                    self.assertIn(parsed.handles[b.position0], handles)
            except ModeBError as e:
                design[name] = 'rejected: %s' % e
        print('\n[modeB catalogue] rejected=%d accepted=%d wrong-exception=%d' % (len(rejected), len(accepted), len(wrong_exc)))
        for n in sorted(rejected):
            print('  REJECT %-45s %s' % (n, rejected[n]))
        for n in accepted:
            print('  ACCEPT %s   <-- FINDING' % n)
        for n, t, m in wrong_exc:
            print('  EXC    %-45s %s: %s' % (n, t, m))
        for n, v in design.items():
            print('  DESIGN %-45s %s' % (n, v))
        self.assertEqual(accepted, [], 'ACCEPT-ON-INVALID: %r' % accepted)
        self.assertEqual(wrong_exc, [], 'rejected with a non-ModeBError exception: %r' % wrong_exc)

    def test_unregistered_or_corrupted_handle_never_blamed(self):
        """Precise property offered by the code: a handle that does not open a registered key is
        never named by extract and never verifies as a blame, for either position."""
        _, by_design = self._catalogue()
        f_other = enc(list(range(21, 64)), M1)
        for name, frame in by_design[:2]:
            res = M50.extract(P, REG, frame, f_other)
            self.assertLessEqual(len(res['seats']), MIN_OV)
            for pos in range(Q):
                for seat in range(NS):
                    s, r = SEC[D0][seat]
                    fake = M46.Blame(seat, pos, 0, s, r)
                    if M50.verify_blame(P, REG, frame, f_other, fake):
                        self.assertIn(seat, res['seats'], name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
