#!/usr/bin/env python3
"""Property / differential / malformed-input layer for T1 = sidecar_free_certificate_v1.44.py,
profile B0 (public signer bitmap + 43 fixed-width per-seat signatures).

Real API:
  encode_b0(registry, provider, domain, message, secret_keys, seats)   -> frame bytes
  verify_b0(frame, registry, provider, expected_cfg)                    -> VerifiedB0 | raises CertError
  extract_b0(frame0, frame1, registry, provider, expected_cfg)          -> tuple(BlameB0(seat,pos0,pos1))
  verify_blame_b0(frame0, frame1, registry, provider, expected_cfg, seat) -> bool (never raises)
  parse_frame(frame, suite) -> (Header, payload)
Signature scheme: there is no `_demo_scheme` scheme object; the stdlib test double is
SymbolicSignatures (verify == "this exact (pk,msg,sig) triple was issued"). liboqs is not used.
Quorums are exactly 43 of 64 (encode_b0 refuses any other size), so "size >= q" means == 43 and
the overlap bound 2q-N = 22 is automatic.

Run:  python3 -m pytest -q test_props_b0.py      or      python3 test_props_b0.py
"""
import importlib.util
import os
import struct
import sys
import unittest

sys.dont_write_bytecode = True                      # never write __pycache__ into the read-only tree
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


T1 = _load('sfc44_audit', 'sidecar_free_certificate_v1.44.py')

settings.register_profile('audit', deadline=None, derandomize=True, print_blob=True,
                          suppress_health_check=list(HealthCheck))
settings.load_profile('audit')

N, Q, MIN_OV, HB = T1.N, T1.QUORUM, T1.MIN_OVERLAP, T1.HEADER_BYTES
PROVIDER = T1.SymbolicSignatures(width=128)
W = PROVIDER.width
NAMES = ['magic', 'version', 'suite', 'cfg', 'domain', 'message', 'count', 'width', 'payload_len']


def _registry(provider, tag):
    pks, sks = [], []
    for _ in range(N):
        pk, sk = provider.keygen()
        pks.append(pk)
        sks.append(sk)
    return T1.RegistryB0(tuple(pks), tag), sks


REG, SKS = _registry(PROVIDER, b'AUDIT/B0/main')
CFG = T1.cfg_b0(REG)
REG2, SKS2 = _registry(PROVIDER, b'AUDIT/B0/other')
CFG2 = T1.cfg_b0(REG2)
D0, D1 = bytes(range(64)), bytes(range(1, 65))
M0, M1 = bytes(64), bytes(63) + b'\x01'


def enc(seats, message, domain=D0, reg=REG, sks=SKS):
    return T1.encode_b0(reg, PROVIDER, domain, message, sks, list(seats))


def slot(frame, k):
    a = HB + 8 + k * W
    return frame[a:a + W]


def patch_header(frame, **fields):
    h = list(struct.unpack(T1.HEADER_FORMAT, frame[:HB]))
    for k, v in fields.items():
        h[NAMES.index(k)] = v
    return struct.pack(T1.HEADER_FORMAT, *h) + frame[HB:]


def build(bitmap, slots, cfg=CFG, domain=D0, message=M0, width=W):
    payload = bitmap.to_bytes(8, 'big') + b''.join(slots)
    return T1.pack_header(T1.SUITE_B0, cfg, domain, message, width, len(payload)) + payload


def sig_for(seat, message=M0, domain=D0, cfg=CFG, sks=SKS):
    return PROVIDER.sign(sks[seat], T1.vote_message_b0(cfg, domain, message, seat))


def bitmap_of(seats):
    b = 0
    for i in seats:
        b |= 1 << i
    return b


SEATS0 = list(range(Q))
SEATS1 = list(range(MIN_OV)) + list(range(Q, N))
FRAME0 = enc(SEATS0, M0)
FRAME1 = enc(SEATS1, M1)
SLOTS0 = [slot(FRAME0, k) for k in range(Q)]


def verify(frame, reg=REG, cfg=CFG):
    return T1.verify_b0(frame, reg, PROVIDER, cfg)


# ----------------------------------------------------------------- strategies
msg64 = st.binary(min_size=64, max_size=64)
perm64 = st.permutations(list(range(N)))


@st.composite
def distinct_msgs(draw):
    m0 = draw(msg64)
    k, v = draw(st.integers(0, 63)), draw(st.integers(1, 255))
    m1 = bytearray(m0)
    m1[k] ^= v
    return m0, bytes(m1)


@st.composite
def overlap_pair(draw):
    """Two 43-seat quorums with a chosen overlap k in [22, 43] (the module's own construction)."""
    p = draw(perm64)
    k = draw(st.integers(MIN_OV, Q))
    return p[:Q], p[:k] + p[Q:2 * Q - k], k


def all_seats_false(f0, f1):
    return all(not T1.verify_blame_b0(f0, f1, REG, PROVIDER, CFG, s) for s in range(N))


# =============================================================================
class B0Properties(unittest.TestCase):

    # ---------------------------------------------------------------- (i)
    @given(overlap_pair(), distinct_msgs())
    @settings(max_examples=150)
    def test_i_conflict_extraction_is_exact_intersection(self, pair, msgs):
        """Conflicting pair (same cfg, same domain, m0 != m1): extract_b0 returns exactly the
        bitmap intersection, positions index the sorted seat lists, every blame verifies, no other
        seat verifies as blame, and extraction is symmetric in the two frames."""
        left, right, k = pair
        m0, m1 = msgs
        f0, f1 = enc(left, m0), enc(right, m1)
        found = T1.extract_b0(f0, f1, REG, PROVIDER, CFG)
        inter = sorted(set(left) & set(right))
        self.assertEqual([b.seat for b in found], inter)
        self.assertEqual(len(found), k)
        self.assertGreaterEqual(len(found), MIN_OV)
        sl, sr = sorted(left), sorted(right)
        for b in found:
            self.assertEqual((b.position0, b.position1), (sl.index(b.seat), sr.index(b.seat)))
            self.assertTrue(T1.verify_blame_b0(f0, f1, REG, PROVIDER, CFG, b.seat))
        for seat in set(range(N)) - set(inter):
            self.assertFalse(T1.verify_blame_b0(f0, f1, REG, PROVIDER, CFG, seat))
        back = T1.extract_b0(f1, f0, REG, PROVIDER, CFG)
        self.assertEqual([(b.seat, b.position1, b.position0) for b in back],
                         [(b.seat, b.position0, b.position1) for b in found])

    @given(perm64, perm64, distinct_msgs())
    @settings(max_examples=100)
    def test_i_conflict_extraction_natural_overlap(self, p0, p1, msgs):
        """Same as above with two independent random quorums (natural overlap distribution)."""
        left, right = p0[:Q], p1[:Q]
        m0, m1 = msgs
        f0, f1 = enc(left, m0), enc(right, m1)
        found = T1.extract_b0(f0, f1, REG, PROVIDER, CFG)
        inter = sorted(set(left) & set(right))
        self.assertEqual([b.seat for b in found], inter)
        self.assertGreaterEqual(len(inter), MIN_OV)          # 2q - N pigeonhole
        self.assertTrue(all(T1.verify_blame_b0(f0, f1, REG, PROVIDER, CFG, b.seat) for b in found))

    # ---------------------------------------------------------------- (ii)
    @given(overlap_pair(), msg64)
    @settings(max_examples=60)
    def test_ii_same_message_is_not_a_conflict(self, pair, m):
        left, right, _ = pair
        f0, f1 = enc(left, m), enc(right, m)
        with self.assertRaises(T1.ExtractionError):
            T1.extract_b0(f0, f1, REG, PROVIDER, CFG)
        self.assertTrue(all_seats_false(f0, f1))

    @given(overlap_pair(), distinct_msgs())
    @settings(max_examples=60)
    def test_ii_different_domain_is_not_a_conflict(self, pair, msgs):
        left, right, _ = pair
        m0, m1 = msgs
        f0, f1 = enc(left, m0, D0), enc(right, m1, D1)
        with self.assertRaises(T1.ExtractionError):
            T1.extract_b0(f0, f1, REG, PROVIDER, CFG)
        self.assertTrue(all_seats_false(f0, f1))

    @given(overlap_pair(), distinct_msgs())
    @settings(max_examples=40)
    def test_ii_different_registry_rejected(self, pair, msgs):
        left, right, _ = pair
        m0, m1 = msgs
        f0, f1 = enc(left, m0), enc(right, m1, reg=REG2, sks=SKS2)
        with self.assertRaises(T1.CertError):
            T1.extract_b0(f0, f1, REG, PROVIDER, CFG)
        with self.assertRaises(T1.CertError):
            T1.extract_b0(f0, f1, REG2, PROVIDER, CFG2)
        self.assertTrue(all_seats_false(f0, f1))

    # ---------------------------------------------------------------- (iii)
    @given(perm64, msg64, st.sampled_from([D0, D1]), st.randoms(use_true_random=False))
    @settings(max_examples=100)
    def test_iii_encode_parse_roundtrip(self, p, m, d, rnd):
        seats = p[:Q]
        f = enc(seats, m, d)
        self.assertEqual(len(f), T1.b0_frame_bytes(W))
        header, payload = T1.parse_frame(f, T1.SUITE_B0)
        self.assertEqual(tuple(getattr(header, n) for n in NAMES),
                         (b'CQ44', 44, 0x44B0, CFG, d, m, Q, W, 8 + Q * W))
        v = verify(f)
        self.assertEqual((v.cfg, v.domain, v.message, v.width), (CFG, d, m, W))
        self.assertEqual(v.seats, tuple(sorted(seats)))
        self.assertEqual(v.bitmap, bitmap_of(seats))
        for k, seat in enumerate(sorted(seats)):
            self.assertTrue(PROVIDER.verify(REG.public_keys[seat],
                                            T1.vote_message_b0(CFG, d, m, seat), slot(f, k)))
        shuffled = list(seats)
        rnd.shuffle(shuffled)
        self.assertEqual(enc(shuffled, m, d), f)             # deterministic, seat-order independent

    # ---------------------------------------------------------------- (iv)
    # Property (precise): for a valid frame F and any F' obtained by changing exactly one byte,
    # verify_b0(F') raises CertError (never returns). With SymbolicSignatures "verifies" means
    # the exact issued triple; for a real scheme the same statement needs strong unforgeability
    # of the fixed-width encoding (no signature malleability).
    @given(st.sampled_from([0, 1]), st.integers(0, len(FRAME0) - 1), st.integers(1, 255))
    @settings(max_examples=500)
    def test_iv_single_byte_mutation_rejected(self, which, idx, xor):
        f = (FRAME0, FRAME1)[which]
        m = bytearray(f)
        m[idx] ^= xor
        with self.assertRaises(T1.CertError):
            verify(bytes(m))

    def test_iv_single_byte_mutation_exhaustive(self):
        accepted, wrong_exc = [], []
        for idx in range(len(FRAME0)):
            for xor in (0x01, 0x80, 0xFF):
                m = bytearray(FRAME0)
                m[idx] ^= xor
                try:
                    verify(bytes(m))
                    accepted.append((idx, xor))
                except T1.CertError:
                    pass
                except Exception as e:                        # noqa: BLE001
                    wrong_exc.append((idx, xor, type(e).__name__))
        self.assertEqual(accepted, [], 'ACCEPT-ON-INVALID single-byte mutations: %r' % accepted[:10])
        self.assertEqual(wrong_exc, [], 'non-CertError exceptions: %r' % wrong_exc[:10])

    # ---------------------------------------------------------------- (v)
    def _catalogue(self):
        F = FRAME0
        s0 = SLOTS0
        big = T1.SymbolicSignatures(width=758)             # 216 + 43*758 = 32810 > 32768
        big_reg, big_sks = _registry(big, b'big')
        oversized = T1.encode_b0(big_reg, big, D0, M0, big_sks, SEATS0)
        items = [
            ('empty', lambda: verify(b'')),
            ('truncated_minus_1', lambda: verify(F[:-1])),
            ('truncated_header_only', lambda: verify(F[:HB])),
            ('truncated_mid_header', lambda: verify(F[:100])),
            ('truncated_bitmap_only', lambda: verify(F[:HB + 8])),
            ('truncated_len_patched', lambda: verify(patch_header(F[:-W], payload_len=8 + (Q - 1) * W))),
            ('trailing_byte', lambda: verify(F + b'\x00')),
            ('trailing_byte_len_patched', lambda: verify(patch_header(F + b'\x00', payload_len=8 + Q * W + 1))),
            ('duplicated_entry_slot1_eq_slot0', lambda: verify(build(bitmap_of(SEATS0), [s0[0], s0[0]] + s0[2:]))),
            ('duplicated_entry_appended_len_patched', lambda: verify(build(bitmap_of(SEATS0), s0 + [s0[0]]))),
            ('reordered_entries_swap_0_1', lambda: verify(build(bitmap_of(SEATS0), [s0[1], s0[0]] + s0[2:]))),
            ('reordered_entries_swap_last_two', lambda: verify(build(bitmap_of(SEATS0), s0[:-2] + [s0[-1], s0[-2]]))),
            ('reordered_entries_reversed', lambda: verify(build(bitmap_of(SEATS0), s0[::-1]))),
            ('oversized_width_758_frame_32810', lambda: T1.verify_b0(oversized, big_reg, big, T1.cfg_b0(big_reg))),
            ('oversized_padded_to_32769', lambda: verify(patch_header(F + bytes(32769 - len(F)), payload_len=32769 - HB))),
            # "invalid index": the bitmap is a u64 and N == 64, so no out-of-range seat index is
            # representable; the nearest malformed bitmaps are tested instead.
            ('bitmap_zero', lambda: verify(build(0, s0))),
            ('bitmap_all_ones', lambda: verify(build((1 << 64) - 1, s0))),
            ('bitmap_popcount_42', lambda: verify(build(bitmap_of(range(42)), [sig_for(i) for i in range(42)]))),
            ('bitmap_popcount_44', lambda: verify(build(bitmap_of(range(44)), [sig_for(i) for i in range(44)]))),
            ('bitmap_seat0_swapped_for_63_sigs_stale', lambda: verify(build(bitmap_of(range(1, Q)) | (1 << 63), s0))),
            # "duplicate signer": a bitmap cannot express one seat twice; the closest frame is one
            # signature byte-string occupying two slots (already 'duplicated_entry'); also a seat's
            # signature placed under another seat's slot:
            ('duplicate_signer_seat0_sig_in_slot_of_seat1', lambda: verify(build(bitmap_of(SEATS0), [s0[0], s0[0]] + s0[2:]))),
            ('signer_not_in_set_seat63_slot_signed_by_seat42_key',
             lambda: verify(build(bitmap_of(range(42)) | (1 << 63), s0[:42] + [PROVIDER.sign(SKS[42], T1.vote_message_b0(CFG, D0, M0, 63))]))),
            ('signer_not_in_set_seat63_slot_signed_by_other_registry_key',
             lambda: verify(build(bitmap_of(range(42)) | (1 << 63), s0[:42] + [sig_for(63, sks=SKS2)]))),
            ('signer_not_in_set_fake_bytes', lambda: verify(build(bitmap_of(range(42)) | (1 << 63), s0[:42] + [b'FAKE' + bytes(W - 4)]))),
            ('corrupted_signature_padding_byte_slot0', lambda: verify(build(bitmap_of(SEATS0), [s0[0][:-1] + b'\x01'] + s0[1:]))),
            ('invalid_length_payload_len_minus_1', lambda: verify(patch_header(F, payload_len=8 + Q * W - 1))),
            ('invalid_length_payload_len_plus_1', lambda: verify(patch_header(F, payload_len=8 + Q * W + 1))),
            ('invalid_length_payload_len_zero', lambda: verify(patch_header(F, payload_len=0))),
            ('width_field_plus_1', lambda: verify(patch_header(F, width=W + 1))),
            ('width_field_minus_1', lambda: verify(patch_header(F, width=W - 1))),
            ('width_field_zero', lambda: verify(patch_header(F, width=0))),
            ('count_field_42', lambda: verify(patch_header(F, count=42))),
            ('count_field_44', lambda: verify(patch_header(F, count=44))),
            ('count_field_0', lambda: verify(patch_header(F, count=0))),
            ('wrong_magic', lambda: verify(patch_header(F, magic=b'CQ43'))),
            ('wrong_version_43', lambda: verify(patch_header(F, version=43))),
            ('wrong_version_45', lambda: verify(patch_header(F, version=45))),
            ('wrong_suite_B1', lambda: verify(patch_header(F, suite=T1.SUITE_B1))),
            ('suite_zero', lambda: verify(patch_header(F, suite=0))),
            ('cfg_field_zeroed', lambda: verify(patch_header(F, cfg=bytes(64)))),
            ('cfg_field_other_registry', lambda: verify(patch_header(F, cfg=CFG2))),
            ('expected_cfg_other_registry', lambda: verify(F, cfg=CFG2)),
            ('expected_cfg_63_bytes', lambda: verify(F, cfg=CFG[:63])),
            ('expected_cfg_bytearray', lambda: verify(F, cfg=bytearray(CFG))),
            ('domain_field_changed_sigs_stale', lambda: verify(patch_header(F, domain=D1))),
            ('message_field_changed_sigs_stale', lambda: verify(patch_header(F, message=M1))),
            ('invalid_encoding_bytearray', lambda: verify(bytearray(F))),
            ('invalid_encoding_memoryview', lambda: verify(memoryview(F))),
            ('invalid_encoding_str', lambda: verify(F.decode('latin-1'))),
            ('invalid_encoding_none', lambda: verify(None)),
            ('invalid_encoding_int', lambda: verify(12345)),
            ('invalid_encoding_list', lambda: verify(list(F))),
            ('registry_with_63_keys', lambda: T1.cfg_b0(T1.RegistryB0(REG.public_keys[:63], b'x'))),
            ('registry_with_duplicate_key', lambda: T1.cfg_b0(T1.RegistryB0(REG.public_keys[:63] + (REG.public_keys[0],), b'x'))),
            ('registry_with_empty_key', lambda: T1.cfg_b0(T1.RegistryB0(REG.public_keys[:63] + (b'',), b'x'))),
            ('registry_keys_as_list', lambda: T1.cfg_b0(T1.RegistryB0(list(REG.public_keys), b'x'))),
            ('encode_42_seats', lambda: enc(range(42), M0)),
            ('encode_44_seats', lambda: enc(range(44), M0)),
            ('encode_duplicate_seat', lambda: enc(list(range(42)) + [0], M0)),
            ('encode_seat_64', lambda: enc(list(range(42)) + [64], M0)),
            ('encode_message_63_bytes', lambda: enc(SEATS0, M0[:63])),
            ('encode_domain_65_bytes', lambda: enc(SEATS0, M0, D0 + b'x')),
        ]
        for k in range(Q):                                    # corrupted signature, every slot
            items.append(('corrupted_signature_slot_%02d' % k,
                          (lambda k=k: verify(build(bitmap_of(SEATS0), s0[:k] + [bytes([s0[k][0] ^ 1]) + s0[k][1:]] + s0[k + 1:])))))
        return items

    def test_v_malformed_catalogue_all_rejected(self):
        accepted, wrong_exc, rejected = [], [], {}
        for name, fn in self._catalogue():
            try:
                fn()
                accepted.append(name)
            except T1.CertError as e:
                rejected[name] = type(e).__name__
            except Exception as e:                            # noqa: BLE001
                wrong_exc.append((name, type(e).__name__))
        print('\n[B0 catalogue] rejected(CertError)=%d accepted=%d wrong-exception=%d'
              % (len(rejected), len(accepted), len(wrong_exc)))
        for n in sorted(rejected):
            print('  REJECT %-55s %s' % (n, rejected[n]))
        for n in accepted:
            print('  ACCEPT %s   <-- FINDING' % n)
        for n, t in wrong_exc:
            print('  EXC    %-55s %s' % (n, t))
        self.assertEqual(accepted, [], 'ACCEPT-ON-INVALID: %r' % accepted)
        self.assertEqual(wrong_exc, [], 'rejected with a non-CertError exception: %r' % wrong_exc)

    def test_v_invalid_index_in_verify_blame_returns_false(self):
        for seat in (64, -1, 65, 1 << 40, True, False, 3.0, '3', None, b'\x03', [3]):
            self.assertIs(T1.verify_blame_b0(FRAME0, FRAME1, REG, PROVIDER, CFG, seat), False, seat)

    @given(st.binary(max_size=400), st.binary(max_size=400),
           st.one_of(st.integers(-5, 70), st.booleans(), st.floats(), st.text(max_size=3), st.none()))
    @settings(max_examples=150)
    def test_v_verify_blame_on_junk_never_raises(self, f0, f1, seat):
        self.assertIs(T1.verify_blame_b0(f0, f1, REG, PROVIDER, CFG, seat), False)
        self.assertIs(T1.verify_blame_b0(FRAME0, f1, REG, PROVIDER, CFG, seat), False)

    def test_encoder_size_gate_observation(self):
        """Observation (not a failure): encode_b0 emits frames above 32,768 bytes without error;
        the gate is enforced by parse_frame/verify_b0 only (consistent with the module's --real-demo
        that records 'oversize_rejected' at verify time)."""
        big = T1.SymbolicSignatures(width=758)
        reg, sks = _registry(big, b'big2')
        f = T1.encode_b0(reg, big, D0, M0, sks, SEATS0)
        self.assertGreater(len(f), T1.MAX_FRAME_BYTES)
        with self.assertRaises(T1.FrameError):
            T1.verify_b0(f, reg, big, T1.cfg_b0(reg))
        self.assertFalse(T1.b0_fits(758))
        self.assertTrue(T1.b0_fits(757))


if __name__ == '__main__':
    unittest.main(verbosity=2)
