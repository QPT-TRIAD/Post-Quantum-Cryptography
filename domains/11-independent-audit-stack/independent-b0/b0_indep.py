"""
b0_indep.py -- independent implementation of CE-QS profile B0 (v1.44 frame
format), written from B0_wire_spec_v1.44.md ALONE.  No reference source was
consulted.  Python 3.12 stdlib only.

Section numbers in comments refer to the spec.  Every place where I had to
choose an interpretation is marked "GAP:" and listed in SPEC_GAPS.md.
"""

from __future__ import annotations

import hashlib
import hmac
import struct
from typing import Any

# ---------------------------------------------------------------------------
# §1 Parameters
# ---------------------------------------------------------------------------
N = 64
QUORUM = 43
MIN_OVERLAP = 2 * QUORUM - N          # 22
MAGIC = b"CQ44"
VERSION = 44
SUITE_B0 = 0x44B0
COUNT = QUORUM                        # 43
HEADER_BYTES = 208
MAX_FRAME_BYTES = 32768

assert MIN_OVERLAP == 22

# Header layout (§6), big-endian.
#   MAGIC(4) | VERSION u16 | SUITE u16 | cfg(64) | domain(64) | message(64)
#   | COUNT u16 | WIDTH u16 | PAYLOAD_LEN u32
_HDR_FMT = ">4sHH64s64s64sHHI"
assert struct.calcsize(_HDR_FMT) == HEADER_BYTES

CFG_LABEL = b"CQ44/cfg/B0"
VOTE_PREFIX = b"CQ44/B0/VOTE"


class B0Error(ValueError):
    """Raised for any spec violation in encode / cfg / helper paths."""


def _is_bytes(x: Any) -> bool:
    # GAP: "byte string" -- I accept bytes and bytearray, nothing else
    # (no memoryview, no str).
    return isinstance(x, (bytes, bytearray))


# ---------------------------------------------------------------------------
# §2 Hash
# ---------------------------------------------------------------------------
def H(label: bytes, *parts: bytes) -> bytes:
    """SHAKE256( for each of label, part_1..part_k:  u64be(len(part)) || part )
    squeezed to 64 bytes.  Non-bytes input is an error."""
    sh = hashlib.shake_256()
    for part in (label,) + parts:
        if not _is_bytes(part):
            raise TypeError("H: all parts must be byte strings, got %r" % type(part))
        sh.update(struct.pack(">Q", len(part)))
        sh.update(bytes(part))
    return sh.digest(64)


# ---------------------------------------------------------------------------
# §3 Registry and configuration
# ---------------------------------------------------------------------------
def _check_registry(registry: tuple[list[bytes], bytes] | dict) -> tuple[list[bytes], bytes]:
    """A registry is (public_keys: list of 64 distinct non-empty byte strings,
    scheme_id: byte string).  Accepts a (pks, scheme_id) tuple or a dict with
    keys 'public_keys' and 'scheme_id'."""
    if isinstance(registry, dict):
        pks, scheme_id = registry["public_keys"], registry["scheme_id"]
    else:
        pks, scheme_id = registry
    pks = list(pks)
    if len(pks) != N:
        raise B0Error("registry must have exactly %d public keys, got %d" % (N, len(pks)))
    for i, pk in enumerate(pks):
        if not _is_bytes(pk):
            raise B0Error("pk_%d is not a byte string" % i)
        if len(pk) == 0:
            raise B0Error("pk_%d is empty" % i)
    pks = [bytes(pk) for pk in pks]
    if len(set(pks)) != N:
        raise B0Error("registry public keys are not distinct")
    if not _is_bytes(scheme_id):
        raise B0Error("scheme_id is not a byte string")
    return pks, bytes(scheme_id)


def cfg(registry) -> bytes:
    """cfg = H(b"CQ44/cfg/B0", scheme_id, pk_0, ..., pk_63)  (64 bytes)."""
    pks, scheme_id = _check_registry(registry)
    return H(CFG_LABEL, scheme_id, *pks)


# ---------------------------------------------------------------------------
# §4 Vote message
# ---------------------------------------------------------------------------
def vote_message(cfg_bytes: bytes, domain: bytes, message: bytes, seat: int) -> bytes:
    """vote_i = b"CQ44/B0/VOTE" || cfg || domain || message || (i as one byte).
    Plain concatenation -- NOT the length-prefixed H()."""
    if not _is_bytes(cfg_bytes) or len(cfg_bytes) != 64:
        raise B0Error("cfg must be 64 bytes")
    if not _is_bytes(domain) or len(domain) != 64:
        raise B0Error("domain must be 64 bytes")
    if not _is_bytes(message) or len(message) != 64:
        raise B0Error("message must be 64 bytes")
    if isinstance(seat, bool) or not isinstance(seat, int) or not (0 <= seat < N):
        raise B0Error("seat must be an int in 0..63")
    return VOTE_PREFIX + bytes(cfg_bytes) + bytes(domain) + bytes(message) + bytes([seat])


# ---------------------------------------------------------------------------
# §5 Toy signature provider (deterministic, for vectors)
# ---------------------------------------------------------------------------
TOY_WIDTH = 32
TOY_SCHEME_ID = b"toy-shake-32"


def toy_sk(i: int) -> bytes:
    return b"SK" + struct.pack(">H", i)


def toy_pk(i: int) -> bytes:
    return b"PK" + struct.pack(">H", i)


def toy_sign(sk: bytes, msg: bytes) -> bytes:
    """sign(sk, msg) = SHAKE256(b"TOYSIG" || sk || msg) squeezed to 32 bytes.
    Plain concatenation, no length prefixes (the spec writes it that way)."""
    sh = hashlib.shake_256()
    sh.update(b"TOYSIG" + bytes(sk) + bytes(msg))
    return sh.digest(TOY_WIDTH)


def toy_verify(pk: bytes, msg: bytes, sig: bytes) -> bool:
    """recompute with sk = b"SK" || pk[2:] and compare (constant width 32).
    GAP: the spec does not say to check pk[:2] == b"PK"; I follow the text
    literally and do not check the prefix."""
    if not _is_bytes(sig) or len(sig) != TOY_WIDTH:
        return False
    sk = b"SK" + bytes(pk)[2:]
    expected = toy_sign(sk, msg)
    return hmac.compare_digest(expected, bytes(sig))


def toy_registry() -> tuple[list[bytes], bytes]:
    return [toy_pk(i) for i in range(N)], TOY_SCHEME_ID


class ToyProvider:
    """Minimal provider object so the frame code stays generic over W."""
    width = TOY_WIDTH
    scheme_id = TOY_SCHEME_ID

    @staticmethod
    def sign_seat(seat: int, msg: bytes) -> bytes:
        # GAP: encode() is not given secret keys.  §5 defines sk_i by seat index,
        # so I sign with sk_i = b"SK" || u16be(i).  (If a registry's pk_i were not
        # b"PK" || u16be(i) the frame would not verify; the spec gives no rule.)
        return toy_sign(toy_sk(seat), msg)

    @staticmethod
    def verify(pk: bytes, msg: bytes, sig: bytes) -> bool:
        return toy_verify(pk, msg, sig)


PROVIDER = ToyProvider


# ---------------------------------------------------------------------------
# bitmap helpers (§6): bitmap u64, "bit i set <=> seat i signed"
# GAP: I read "bit i" as the value bit 2**i of the u64 (LSB = seat 0), which
# is the ordinary meaning of "bit i" of an integer; the u64 is then serialised
# big-endian.  The spec does not say "MSB-first bit 0", so this is my reading.
# ---------------------------------------------------------------------------
def seats_to_bitmap(seats) -> int:
    bm = 0
    for s in seats:
        bm |= 1 << s
    return bm


def bitmap_to_seats(bm: int) -> list[int]:
    return [i for i in range(N) if (bm >> i) & 1]


def popcount(bm: int) -> int:
    return bin(bm).count("1")


# ---------------------------------------------------------------------------
# §6 Encoding
# ---------------------------------------------------------------------------
def encode(registry, domain: bytes, message: bytes, seats, provider=PROVIDER) -> bytes:
    """Build a B0 frame.  Requires exactly 43 distinct seats in 0..63, a
    64-byte domain and message, and every signature exactly W bytes."""
    pks, scheme_id = _check_registry(registry)
    if not _is_bytes(domain) or len(domain) != 64:
        raise B0Error("domain must be exactly 64 bytes")
    if not _is_bytes(message) or len(message) != 64:
        raise B0Error("message must be exactly 64 bytes")
    seats = list(seats)
    for s in seats:
        if isinstance(s, bool) or not isinstance(s, int) or not (0 <= s < N):
            raise B0Error("seat %r out of range 0..63" % (s,))
    if len(seats) != QUORUM or len(set(seats)) != QUORUM:
        raise B0Error("encode requires exactly %d distinct seats" % QUORUM)
    seats = sorted(seats)   # signatures in ascending seat order of the set bits
    W = provider.width
    if not (0 < W <= 0xFFFF):
        raise B0Error("provider width out of u16 range")

    c = H(CFG_LABEL, scheme_id, *pks)
    bitmap = seats_to_bitmap(seats)
    sigs = []
    for i in seats:
        sig = provider.sign_seat(i, vote_message(c, domain, message, i))
        if len(sig) != W:
            raise B0Error("signature for seat %d is not %d bytes" % (i, W))
        sigs.append(sig)
    payload = struct.pack(">Q", bitmap) + b"".join(sigs)
    payload_len = 8 + QUORUM * W
    assert len(payload) == payload_len
    header = struct.pack(_HDR_FMT, MAGIC, VERSION, SUITE_B0, c, bytes(domain),
                         bytes(message), COUNT, W, payload_len)
    frame = header + payload
    if len(frame) > MAX_FRAME_BYTES:
        raise B0Error("frame exceeds MAX_FRAME_BYTES")
    return frame


# ---------------------------------------------------------------------------
# §7 Verification
# ---------------------------------------------------------------------------
def verify_reason(frame, registry, expected_cfg, provider=PROVIDER):
    """Returns (result_dict, None) on success or (None, reason_string) on
    rejection.  Every check of §7 is performed; any failure rejects."""
    # 1. frame is a byte string; 208 <= len(frame) <= 32768
    if not _is_bytes(frame):
        return None, "7.1 frame is not a byte string"
    frame = bytes(frame)
    if len(frame) < HEADER_BYTES:
        return None, "7.1 frame shorter than header (%d < %d)" % (len(frame), HEADER_BYTES)
    if len(frame) > MAX_FRAME_BYTES:
        return None, "7.1 frame longer than MAX_FRAME_BYTES (%d)" % len(frame)

    magic, version, suite, hcfg, domain, message, count, width, payload_len = \
        struct.unpack(_HDR_FMT, frame[:HEADER_BYTES])

    # 2. header constants
    if magic != MAGIC:
        return None, "7.2 bad MAGIC %r" % magic
    if version != VERSION:
        return None, "7.2 bad VERSION %d" % version
    if suite != SUITE_B0:
        return None, "7.2 bad SUITE 0x%04x" % suite
    if count != COUNT:
        return None, "7.2 bad COUNT %d" % count

    # 3. PAYLOAD_LEN == number of bytes after the header
    payload = frame[HEADER_BYTES:]
    if payload_len != len(payload):
        return None, "7.3 PAYLOAD_LEN %d != actual %d" % (payload_len, len(payload))

    # 4. header cfg == expected_cfg and == recomputed cfg(registry)
    if not _is_bytes(expected_cfg) or len(expected_cfg) != 64:
        return None, "7.4 expected_cfg is not 64 bytes"
    try:
        rcfg = cfg(registry)
    except Exception as e:  # malformed registry -> reject
        return None, "7.4 registry invalid: %s" % e
    if not hmac.compare_digest(hcfg, bytes(expected_cfg)):
        return None, "7.4 header cfg != expected_cfg"
    if not hmac.compare_digest(hcfg, rcfg):
        return None, "7.4 header cfg != recomputed registry cfg"

    # 5. WIDTH == provider width, positive; payload length == 8 + 43*WIDTH
    if width <= 0 or width != provider.width:
        return None, "7.5 WIDTH %d != provider width %d" % (width, provider.width)
    if len(payload) != 8 + QUORUM * width:
        return None, "7.5 payload length %d != 8 + 43*%d" % (len(payload), width)

    # 6. bitmap popcount exactly 43
    bitmap = struct.unpack(">Q", payload[:8])[0]
    if popcount(bitmap) != QUORUM:
        return None, "7.6 bitmap popcount %d != %d" % (popcount(bitmap), QUORUM)

    # 7. each signature verifies under pk_i over vote_i
    pks, _ = _check_registry(registry)
    seats = bitmap_to_seats(bitmap)
    for p, i in enumerate(seats):
        off = 8 + p * width
        sig = payload[off:off + width]
        msg = vote_message(hcfg, domain, message, i)
        if not provider.verify(pks[i], msg, sig):
            return None, "7.7 signature at position %d (seat %d) does not verify" % (p, i)

    return {
        "cfg": hcfg,
        "domain": domain,
        "message": message,
        "width": width,
        "bitmap": bitmap,
        "seats": seats,
    }, None


def verify(frame, registry, expected_cfg, provider=PROVIDER):
    """§7: returns the result dict, or None if the frame is rejected."""
    try:
        res, _ = verify_reason(frame, registry, expected_cfg, provider)
    except Exception:
        return None
    return res


# ---------------------------------------------------------------------------
# §8 Extraction
# ---------------------------------------------------------------------------
def extract_reason(frame0, frame1, registry, expected_cfg, provider=PROVIDER):
    """Returns (list_of_triples, None) or (None, reason)."""
    r0, why0 = verify_reason(frame0, registry, expected_cfg, provider)
    if r0 is None:
        return None, "8.1 frame0 rejected: " + why0
    r1, why1 = verify_reason(frame1, registry, expected_cfg, provider)
    if r1 is None:
        return None, "8.1 frame1 rejected: " + why1
    if r0["cfg"] != r1["cfg"]:
        return None, "8.2 cfg differ"
    if r0["domain"] != r1["domain"]:
        return None, "8.2 domain differ"
    if r0["message"] == r1["message"]:
        return None, "8.2 messages equal (not a conflict)"
    common = r0["bitmap"] & r1["bitmap"]
    if popcount(common) < MIN_OVERLAP:
        return None, "8.3 popcount(common)=%d < %d" % (popcount(common), MIN_OVERLAP)
    pos0 = {s: p for p, s in enumerate(r0["seats"])}
    pos1 = {s: p for p, s in enumerate(r1["seats"])}
    out = [(s, pos0[s], pos1[s]) for s in bitmap_to_seats(common)]   # ascending by seat
    return out, None


def extract(frame0, frame1, registry, expected_cfg, provider=PROVIDER):
    """§8: list of (seat, position0, position1) ascending by seat, or None
    when the pair is rejected."""
    try:
        out, _ = extract_reason(frame0, frame1, registry, expected_cfg, provider)
    except Exception:
        return None
    return out


# ---------------------------------------------------------------------------
# §9 Blame
# ---------------------------------------------------------------------------
def blame(frame0, frame1, registry, expected_cfg, seat, provider=PROVIDER) -> bool:
    """True iff 0 <= seat <= 63, both frames verify, domains equal, messages
    differ, and seat is set in both bitmaps.  Any exception path -> False."""
    try:
        # GAP: seat type.  bool is an int subclass in Python; I refuse it, and
        # refuse anything that is not an int.
        if isinstance(seat, bool) or not isinstance(seat, int):
            return False
        if not (0 <= seat < N):
            return False
        r0 = verify(frame0, registry, expected_cfg, provider)
        if r0 is None:
            return False
        r1 = verify(frame1, registry, expected_cfg, provider)
        if r1 is None:
            return False
        if r0["domain"] != r1["domain"]:
            return False
        if r0["message"] == r1["message"]:
            return False
        return bool((r0["bitmap"] >> seat) & 1) and bool((r1["bitmap"] >> seat) & 1)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# self-test (spec-only sanity, no vectors)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    reg = toy_registry()
    c = cfg(reg)
    d = bytes(range(64))
    m0 = bytes([1] * 64)
    m1 = bytes([2] * 64)
    s0 = list(range(0, 43))
    s1 = list(range(21, 64))
    f0 = encode(reg, d, m0, s0)
    f1 = encode(reg, d, m1, s1)
    assert len(f0) == HEADER_BYTES + 8 + 43 * 32 == 1592
    assert verify(f0, reg, c) is not None and verify(f1, reg, c) is not None
    ex = extract(f0, f1, reg, c)
    assert ex is not None and len(ex) == 22 and ex[0] == (21, 21, 0), ex
    assert extract(f0, encode(reg, d, m0, s1), reg, c) is None      # same message
    assert blame(f0, f1, reg, c, 21) and not blame(f0, f1, reg, c, 0)
    assert not blame(f0, f1, reg, c, 64) and not blame(f0, f1, reg, c, -1)
    assert verify(f0[:-1], reg, c) is None and verify(f0 + b"\0", reg, c) is None
    bad = bytearray(f0); bad[300] ^= 1
    assert verify(bytes(bad), reg, c) is None
    print("self-test ok; cfg =", c.hex())
