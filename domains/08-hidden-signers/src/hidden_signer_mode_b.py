# hidden_signer_modeB_v1.51.py — audit-fix release of v1.50 (2026-09-13): F5 canonical input checks.
# Research code (Mode B); never compiled into a node. v1.50 is preserved immutably.
#!/usr/bin/env python3
r"""Mode B design reference, v1.50: the two fixes from the independent
cryptanalysis pass (v1.49 §9) applied to the v1.46 design, plus a canonicality fix.

  (1) Linearized handle. v1.46 used Z = r^7 XOR c*s with one 256-bit challenge c.
      Two messages with c(m0) = c(m1) (a 256-bit collision: 2^128 classical,
      about 2^85 quantum with QRAM) made the extraction divide by zero and name
      nobody. v1.50 derives a triple (c_a, c_b, c_c) and uses
          Z = r^7 XOR L_c(s),   L_c(s) = c_a s + c_b s^2 + c_c s^4,
      an F2-linear map of s. The public counter in the challenge derivation is
      the smallest one making L_c invertible, so s = L_c^-1(Z XOR r^7) is a
      function of r inside the proof circuit (degree 3, as before). Extraction
      solves the F2-linear system (L_c0 + L_c1)(s) = Z0 + Z1, which has at most
      four solutions; suppressing it needs all three coefficients to collide
      (768 bits).
  (2) Extraction never aborts on the count. One seat with two openings of its
      key could previously trigger the '< 22' error and hide the other
      double-signers. Every identified seat is now reported, with a
      'complete' flag.
  (3) Messages must be exactly 64 bytes (a hash), so the header field and the
      handle derivation see the same bytes.

Everything else (key map, registry, frame, relation, tests of the v1.46
attacks) is imported unchanged from the v1.46 base module, which keeps its
version in its name and lives in this repository at
../history/hidden-signer-mode-b-v1.46.py.
"""

import hashlib
import importlib.util
import os
import random
import struct
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
# The superseded v1.46 base module keeps its version in its filename and sits in history/.
_spec = importlib.util.spec_from_file_location(
    'modeB46', os.path.join(_HERE, os.pardir, 'history', 'hidden-signer-mode-b-v1.46.py'))
m46 = importlib.util.module_from_spec(_spec)
sys.modules['modeB46'] = m46
_spec.loader.exec_module(m46)

N_SEATS, QUORUM, MIN_OVERLAP = m46.N_SEATS, m46.QUORUM, m46.MIN_OVERLAP
ModeBError = m46.ModeBError
MAGIC, VERSION, SUITE = b'CQ50', 50, 0x50B0


class Challenge:
    """(c_a, c_b, c_c, ctr) with L_c invertible; stores L_c as column images and
    its inverse as row masks over F2."""

    def __init__(self, p, cfg, domain, message):
        self.p = p
        f = p.field
        n = p.n
        for ctr in range(1 << 20):
            buf = hashlib.shake_256(b'CQ50/c' + cfg + domain + message + struct.pack('>I', ctr)).digest(3 * p.handle_bytes)
            hb = p.handle_bytes
            self.a = int.from_bytes(buf[:hb], 'big') & f.order
            self.b = int.from_bytes(buf[hb:2 * hb], 'big') & f.order
            self.c = int.from_bytes(buf[2 * hb:], 'big') & f.order
            self.cols = [self.apply(1 << j) for j in range(n)]
            inv = _invert_f2(self.cols, n)
            if inv is not None:
                self.inv_rows, self.ctr = inv, ctr
                return
        raise ModeBError('no invertible challenge found')

    def apply(self, s):
        f = self.p.field
        s2 = f.mul(s, s)
        return f.mul(self.a, s) ^ f.mul(self.b, s2) ^ f.mul(self.c, f.mul(s2, s2))

    def invert(self, t):
        s = 0
        for k, row in enumerate(self.inv_rows):
            if bin(row & t).count('1') & 1:
                s |= 1 << k
        return s


def _invert_f2(cols, n):
    """Rows of M^-1 for the F2 matrix whose columns are cols (bit k of cols[j] = M[k][j])."""
    rows = [sum(((cols[j] >> k) & 1) << j for j in range(n)) for k in range(n)]
    inv = [1 << k for k in range(n)]
    for col in range(n):
        piv = next((r for r in range(col, n) if (rows[r] >> col) & 1), None)
        if piv is None:
            return None
        rows[col], rows[piv] = rows[piv], rows[col]
        inv[col], inv[piv] = inv[piv], inv[col]
        for r in range(n):
            if r != col and (rows[r] >> col) & 1:
                rows[r] ^= rows[col]
                inv[r] ^= inv[col]
    return inv


def solve_f2(cols, rhs, n, max_free=2):
    """All s with sum_j s_j cols[j] = rhs (at most 2^max_free of them)."""
    rows = [sum(((cols[j] >> k) & 1) << j for j in range(n)) for k in range(n)]
    rhsb = [(rhs >> k) & 1 for k in range(n)]
    pivcol, rank = [], 0
    for col in range(n):
        piv = next((r for r in range(rank, n) if (rows[r] >> col) & 1), None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        rhsb[rank], rhsb[piv] = rhsb[piv], rhsb[rank]
        for r in range(n):
            if r != rank and (rows[r] >> col) & 1:
                rows[r] ^= rows[rank]
                rhsb[r] ^= rhsb[rank]
        pivcol.append(col)
        rank += 1
    if any(rhsb[r] for r in range(rank, n)):
        return []
    free = [c for c in range(n) if c not in set(pivcol)]
    if len(free) > max_free:
        return []
    sols = []
    for mask in range(1 << len(free)):
        s = 0
        for i, fc in enumerate(free):
            if (mask >> i) & 1:
                s |= 1 << fc
        for r in range(rank):
            val = rhsb[r] ^ (bin(rows[r] & s).count('1') & 1)
            if val:
                s |= 1 << pivcol[r]
        sols.append(s)
    return sols


def handle(p, ch, opening):
    s, r = opening
    return (p.field.G(r) ^ ch.apply(s)).to_bytes(p.handle_bytes, 'big')


def encode(p, registry, secrets, domain, message, seats, proof=b'STRUCTURE-ONLY'):
    if type(message) is not bytes or len(message) != 64:
        raise ModeBError('message must be a 64-byte digest')
    if type(domain) is not bytes or len(domain) != 64:                 # F5: '64s' silently truncated/padded
        raise ModeBError('domain must be a 64-byte canonical string')
    if type(proof) is not bytes:
        raise ModeBError('proof must be bytes')
    if len(seats) != QUORUM or len(set(seats)) != QUORUM:
        raise ModeBError('exactly 43 distinct seats')
    cfg = m46.cfg_of(registry, p)
    ch = Challenge(p, cfg, domain, message)
    handles = sorted(handle(p, ch, secrets[domain][i]) for i in seats)
    if len(set(handles)) != QUORUM:
        raise ModeBError('handle collision')
    payload = b''.join(handles) + proof
    header = struct.pack(m46.HEADER_FORMAT, MAGIC, VERSION, SUITE, cfg, domain, message,
                         QUORUM, p.handle_bytes, len(payload))
    frame = header + payload
    if len(frame) > m46.MAX_FRAME_BYTES:
        raise ModeBError('frame exceeds 32,768 bytes')
    return frame


def parse(p, frame):
    if type(frame) is not bytes:                                       # F5: bytearray/str/None were not typed errors
        raise ModeBError('frame must be canonical bytes')
    if len(frame) > m46.MAX_FRAME_BYTES or len(frame) < m46.HEADER_BYTES + QUORUM * p.handle_bytes:
        raise ModeBError('frame size out of bounds')
    magic, version, suite, cfg, domain, message, count, width, plen = struct.unpack(
        m46.HEADER_FORMAT, frame[:m46.HEADER_BYTES])
    if (magic, version, suite, count, width) != (MAGIC, VERSION, SUITE, QUORUM, p.handle_bytes):
        raise ModeBError('noncanonical header')
    if plen != len(frame) - m46.HEADER_BYTES:
        raise ModeBError('payload length mismatch')
    body = frame[m46.HEADER_BYTES:]
    w = p.handle_bytes
    handles = tuple(body[j * w:(j + 1) * w] for j in range(QUORUM))
    if any(handles[j] >= handles[j + 1] for j in range(QUORUM - 1)):
        raise ModeBError('handles must be strictly increasing')
    return m46.Parsed(cfg, domain, message, handles, body[QUORUM * w:])


def check_relation(p, registry, parsed, rows):
    if parsed.cfg != m46.cfg_of(registry, p) or parsed.domain not in registry.keys:
        raise ModeBError('wrong configuration or unregistered domain')
    if len(rows) != QUORUM or len({i for i, _, _ in rows}) != QUORUM:
        raise ModeBError('43 rows with distinct seats required')
    ch = Challenge(p, parsed.cfg, parsed.domain, parsed.message)
    for (i, s, r), z in zip(rows, parsed.handles):
        if not 0 <= i < N_SEATS or not 0 <= s <= p.field.order or not 0 <= r <= p.field.order:
            raise ModeBError('row out of range')
        if p.keymap.to_bytes(p.keymap.evaluate(m46.opening_to_input(p, s, r))) != registry.keys[parsed.domain][i]:
            raise ModeBError('opening does not match the registry key')
        # the circuit derives s from r: check that derivation too
        t = int.from_bytes(z, 'big') ^ p.field.G(r)
        if ch.invert(t) != s or handle(p, ch, (s, r)) != z:
            raise ModeBError('handle is not r^7 XOR L_c(s)')
    return True


def extract(p, registry, frame0, frame1):
    """Public pair search; returns {'seats': [...], 'complete': bool, 'blames': [...]}.
    Never raises on the count."""
    p0, p1 = parse(p, frame0), parse(p, frame1)
    if p0.cfg != p1.cfg or p0.cfg != m46.cfg_of(registry, p):
        raise ModeBError('configuration mismatch')
    if p0.domain != p1.domain or p0.domain not in registry.keys:
        raise ModeBError('domain mismatch')
    if p0.message == p1.message:
        raise ModeBError('equal messages are not a conflict')
    c0 = Challenge(p, p0.cfg, p0.domain, p0.message)
    c1 = Challenge(p, p1.cfg, p1.domain, p1.message)
    dcols = [a ^ b for a, b in zip(c0.cols, c1.cols)]
    table = {key: i for i, key in enumerate(registry.keys[p0.domain])}
    found = {}
    for j, z0 in enumerate(p0.handles):
        a = int.from_bytes(z0, 'big')
        for k, z1 in enumerate(p1.handles):
            for s in solve_f2(dcols, a ^ int.from_bytes(z1, 'big'), p.n):
                r = p.field.G_inv(a ^ c0.apply(s))
                y = p.keymap.to_bytes(p.keymap.evaluate(m46.opening_to_input(p, s, r)))
                seat = table.get(y)
                if seat is not None and seat not in found:
                    found[seat] = m46.Blame(seat, j, k, s, r)
    seats = sorted(found)
    return {'seats': seats, 'complete': len(seats) >= MIN_OVERLAP,
            'blames': [found[i] for i in seats]}


def verify_blame(p, registry, frame0, frame1, blame):
    p0, p1 = parse(p, frame0), parse(p, frame1)
    if p0.domain != p1.domain or p0.message == p1.message or p0.cfg != p1.cfg:
        return False
    y = p.keymap.to_bytes(p.keymap.evaluate(m46.opening_to_input(p, blame.s, blame.r)))
    if y != registry.keys[p0.domain][blame.seat]:
        return False
    c0 = Challenge(p, p0.cfg, p0.domain, p0.message)
    c1 = Challenge(p, p1.cfg, p1.domain, p1.message)
    return (handle(p, c0, (blame.s, blame.r)) == p0.handles[blame.position0]
            and handle(p, c1, (blame.s, blame.r)) == p1.handles[blame.position1])


class V150Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = m46.make_params(n=32, expansion=16, seed=b'test50')
        cls.rng = random.Random(5050)
        cls.d0 = bytes(range(64))
        cls.registry, cls.secrets = m46.build_registry(cls.p, b'epoch', (cls.d0,), cls.rng)
        cls.cfg = m46.cfg_of(cls.registry, cls.p)

    def _msg(self, k):
        return hashlib.shake_256(k.to_bytes(8, 'big')).digest(64)

    def test_challenge_invertible_and_linear(self):
        ch = Challenge(self.p, self.cfg, self.d0, self._msg(1))
        rng = random.Random(1)
        for _ in range(20):
            s, t = rng.getrandbits(self.p.n), rng.getrandbits(self.p.n)
            self.assertEqual(ch.apply(s ^ t), ch.apply(s) ^ ch.apply(t))     # F2-linear
            self.assertEqual(ch.invert(ch.apply(s)), s)                     # invertible
        self.assertLess(ch.ctr, 32)

    def test_extraction_all_overlaps(self):
        rng = random.Random(9)
        for overlap in (MIN_OVERLAP, 30, QUORUM):
            perm = list(range(N_SEATS)); rng.shuffle(perm)
            left = perm[:QUORUM]
            right = perm[:overlap] + perm[QUORUM:2 * QUORUM - overlap]
            f0 = encode(self.p, self.registry, self.secrets, self.d0, self._msg(10 + overlap), left)
            f1 = encode(self.p, self.registry, self.secrets, self.d0, self._msg(99 + overlap), right)
            res = extract(self.p, self.registry, f0, f1)
            self.assertEqual(res['seats'], sorted(set(left) & set(right)))
            self.assertTrue(res['complete'])
            self.assertTrue(all(verify_blame(self.p, self.registry, f0, f1, b) for b in res['blames']))

    def test_relation(self):
        seats = list(range(QUORUM)); m = self._msg(3)
        f0 = encode(self.p, self.registry, self.secrets, self.d0, m, seats)
        ch = Challenge(self.p, self.cfg, self.d0, m)
        by = {handle(self.p, ch, self.secrets[self.d0][i]): i for i in seats}
        rows = [(by[z],) + self.secrets[self.d0][by[z]] for z in parse(self.p, f0).handles]
        self.assertTrue(check_relation(self.p, self.registry, parse(self.p, f0), rows))
        bad = list(rows); i, s, r = bad[0]; bad[0] = (i, s ^ 1, r)
        with self.assertRaises(ModeBError):
            check_relation(self.p, self.registry, parse(self.p, f0), bad)

    def test_partial_extraction_reports_found_seats(self):
        # Overlap 22 but one common seat replaced by an unrelated handle in frame 1:
        # 21 seats are still named, with complete=False (no '< 22' abort).
        seats0 = list(range(QUORUM))
        seats1 = list(range(MIN_OVERLAP)) + list(range(QUORUM, N_SEATS))
        f0 = encode(self.p, self.registry, self.secrets, self.d0, self._msg(1), seats0)
        m2 = self._msg(2)
        ch = Challenge(self.p, self.cfg, self.d0, m2)
        # frame 1: seat 0's handle replaced by one from an unregistered opening,
        # then re-sorted and re-packed so the frame stays canonical.
        handles = [handle(self.p, ch, self.secrets[self.d0][i]) for i in seats1 if i != 0]
        handles.append(handle(self.p, ch, (12345, 6789)))
        payload = b''.join(sorted(handles)) + b'STRUCTURE-ONLY'
        f1 = struct.pack(m46.HEADER_FORMAT, MAGIC, VERSION, SUITE, self.cfg, self.d0, m2,
                         QUORUM, self.p.handle_bytes, len(payload)) + payload
        res = extract(self.p, self.registry, f0, f1)
        self.assertEqual(res['seats'], list(range(1, MIN_OVERLAP)))
        self.assertFalse(res['complete'])
        self.assertEqual(len(res['blames']), MIN_OVERLAP - 1)

    def test_message_canonicality(self):
        with self.assertRaises(ModeBError):
            encode(self.p, self.registry, self.secrets, self.d0, b'short', list(range(QUORUM)))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--self-test', action='store_true', required=True)
    ap.parse_args(argv)
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(V150Tests),
                                unittest.defaultTestLoader.loadTestsFromTestCase(AuditFixTests)])
    r = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if r.wasSuccessful() else 1



class AuditFixTests(unittest.TestCase):
    """F5 regressions (audit stack v0.1, property layer M1/M2)."""

    @classmethod
    def setUpClass(cls):
        cls.p = m46.make_params(n=32, expansion=16, seed=b'v151-fix')
        import random
        rng = random.Random(151)
        cls.registry, cls.secrets = m46.build_registry(cls.p, b'epoch', (b'D' * 64,), rng)

    def test_f5_domain_canonicality(self):
        seats = list(range(QUORUM))
        for bad in (b'D' * 63, b'D' * 65, 'D' * 64, None):
            with self.assertRaises(ModeBError):
                encode(self.p, self.registry, self.secrets, bad, b'M' * 64, seats)
        with self.assertRaises(ModeBError):
            encode(self.p, self.registry, self.secrets, b'D' * 64, b'M' * 64, seats, proof='not-bytes')

    def test_f5_parse_requires_bytes(self):
        frame = encode(self.p, self.registry, self.secrets, b'D' * 64, b'M' * 64, list(range(QUORUM)))
        parse(self.p, frame)
        for bad in (bytearray(frame), memoryview(frame), frame.decode('latin1'), None, 7):
            with self.assertRaises(ModeBError):
                parse(self.p, bad)

if __name__ == '__main__':
    sys.exit(main())
