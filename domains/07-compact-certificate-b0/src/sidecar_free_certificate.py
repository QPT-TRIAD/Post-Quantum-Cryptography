#!/usr/bin/env python3
r"""Sidecar-free CE-QS certificate profiles, v1.44 — B0 and B1 final frames.

CE-QS is a 64-seat committee with quorum Q=43 and total fault bound F=21, so any
two accepting quorums share at least 2Q-N = 22 seats. The project target is a
PORTABLE conflict-extractable quorum certificate (QC) of at most 32,768 bytes,
from which two conflicting QCs let anyone publicly extract at least 22 seats that
authorized both conflicting messages ("double-authorizers"). The certificate must
carry no per-certificate sidecar and rely on no secret opener at extraction time.

Repository copy. This is the v1.44 revision of the module; the version suffix has
been dropped from the file name. Paths that name other project files are relative to
the repository root, and a project file named here but not copied into this
repository is marked as such. The line numbers and revision labels quoted from other
revisions refer to the source tree, not to this repository.

This file finalizes the two certificate FRAMES and their public algorithms. It
implements exactly what it tests and claims nothing beyond that. In particular it
does NOT produce a compact hidden-signer QC with a qualified zero-knowledge proof
of authorization: no such proof backend exists here, and the size calculators at
the end give reproducible lower bounds showing why the compact-B1 proof obligation
is still open. Standard-library Python 3.12 suffices for every tested path; the
real signature provider is optional and never required by the test suite.

Common frame header (208 bytes, both profiles)
----------------------------------------------
The header is `struct '>4sHH64s64s64sHHI'`:
  magic          b'CQ44'          (4 bytes)
  version        u16 = 44
  suite          u16              (0x44B0 for B0, 0x44B1 for B1)
  configuration  cfg              (64 bytes)
  domain         d                (64 bytes)
  message        m                (64 bytes)
  count          u16 = 43
  width          u16              (per-item slot width; profile specific)
  payload_len    u32
A frame is header || payload with len(payload) == payload_len. Parsing rejects
truncation, trailing bytes, a wrong magic/version/suite/count, and any frame over
32,768 bytes. The hash is

  H(label, *parts) = SHAKE256( u64be(len(label))||label ||
                               u64be(len(p_0))||p_0 || ... )[:64],

i.e. an eight-byte big-endian length prefix in front of the label and of every
part, truncated to 64 bytes. This is the v1.29 domain-separated hash with an
explicit leading label argument.

Profile B0 — public signer set (suite 0x44B0). Sidecar-free and compact, NOT hidden
-----------------------------------------------------------------------------------
Registry: 64 distinct signature public keys and a scheme identifier `scheme_id`.
  cfg = H(b'CQ44/cfg/B0', scheme_id, pk_0, ..., pk_63).
Seat i's approval message is the concatenation
  b'CQ44/B0/VOTE' || cfg || d || m || bytes([i]),
signed with the scheme's PURE signing API and an empty external context.
Payload: an 8-byte big-endian bitmap (seat i is bit value 1<<i), followed by
exactly 43 fixed-width signatures in increasing seat order. Thus
  payload_len = 8 + 43*width, total frame = 216 + 43*width.
verify_b0 checks the header, that cfg equals the caller's authenticated
expected_cfg and equals the value recomputed from the registry, that the bitmap
popcount is 43, the exact length, and that every one of the 43 signatures verifies
under its seat public key on that seat's approval message. Two conflicting B0
frames publicly reveal their common signer seats: with two accepting quorums of 43
in a 64-seat house, |S0 & S1| >= 43+43-64 = 22 always. extract_b0 returns those
common seats, each with its signature position in both frames; the two signatures
at those positions are public, independently verifiable double-authorization
evidence. B0 is an EXECUTABLE REFERENCE. Its real-world security requires a
category-5, QPT-128 signature whose bytes fit the size gate
  B0_MAX_SIGNATURE_BYTES = (32768 - 216)//43 = 757.
No FIPS-standardized signature fits: ML-DSA-87 is 4,627 bytes, SLH-DSA-SHAKE-256s
29,792 and Falcon-padded-1024 1,280. Candidates in NIST's additional-signature
process do fit. UOV 'OV-V' (260 bytes), SNOVA_29_6_5 (454) and SNOVA_60_10_4 (576)
claim category 5 and are measured through liboqs 0.16.0 by --real-demo; so is the
AND-hybrid OV-V||SNOVA_29_6_5 (714). Their frames are 11,396, 19,738, 24,984 and
30,918 bytes. B0 publishes the signer bitmap, so it does NOT meet the hidden-signer
privacy requirement.

Profile B1 — hidden signer set, "Mode S" (suite 0x44B1). The full privacy target
--------------------------------------------------------------------------------
Credentials: seat i holds a 64-byte secret x_i; its registered key is the
128-byte (1024-bit) value
  K[i] = SHAKE256(b'CEQS/K1' || x_i)[:128]    (a 71-byte input, one absorb block),
and cfg = H(b'CQ44/cfg/B1', K_0, ..., K_63) with duplicate keys rejected. The
1024-bit registry keys carry the collision resistance the QPT-128 ledger relies
on to keep forensic completeness under the O(q^2) online-extraction overhead. The
context is D = H(b'CQ44/ctx', cfg, d). A seat's handle is
  pair = SHAKE256(b'CEQS/P1' || x || D)[:128]  (a 135-byte input, one absorb block)
  L = pair[:64]
  Z = ( int(pair[64:]) XOR mul(int(m), i+1) )  in GF(2)[X]/(X^512+X^8+X^5+X^2+1).
The payload is 43 handles (L||Z, 128 bytes each) strictly increasing by L, then
proof bytes: payload_len = 5504 + proof_len, total = 5712 + proof_len, and
proof_len <= 27056 so the frame never exceeds 32,768 bytes. check_relation is the
private R-relation on 43 (seat, x) rows in handle order: it checks distinct seats,
that each x opens its registered K, and that each handle is exactly handle(x, seat,
D, m). extract_b1 is the v1.34 division-free identity decoder ported over the
parsed handles (the v1.34 source is present in this repository as
domains/05-extraction-and-signature-reductions/src/ceqs29_extractor.py); it
returns ALGEBRAIC CANDIDATES ONLY. Authorization is asserted
only through a ProofBackend, and the sole backend here, StructureOnlyTestBackend,
is UNQUALIFIED (qualified=False, proof is a fixed marker, verify checks the marker
only). Therefore verify_b1 always reports
  status = 'STRUCTURE_ONLY_NO_QUALIFIED_PROOF', authorization_verified = False.

Lower-bound calculators
-----------------------
Pure arithmetic with provenance, establishing why a compact B1 proof is still open:
a keccak-f[1600] permutation has 24*1600 = 38,400 bit-level AND gates; Mode S needs
43*2 = 86 permutations; a per-AND-output correction/opening bit (VOLE-in-the-head,
or ZKBoo/KKW commit-and-open) forces at least ceil(86*38,400/8) = 412,800 bytes for
those proof families, far above 27,056. A Binius64 PCS floor pinned from the
vendored size estimators is at least 109,856 bytes at 96-bit soundness for Mode S's
committed size, also far above 27,056. These are lower bounds for the named
families on that circuit, not a claim that every proof system must exceed 27,056.

Theorem C (theorem_c_budget) covers KKW-, BN++- and FAEST-style witness-committing
proofs without fixing a circuit. It assumes one Grover iteration costs at most 2^24
gates, so fewer than 2^128 gates buy up to 2^(104 - h) iterations for a 2^h-step
challenge hash. Attacks then force tau*log2(N) + grinding bits >= 212 - 2h and
credentials of at least 218 bits (64 targets). The 27,056-byte slot leaves at most
359 witness bits per seat at N = 2^16 and 1,006 at N = 2^48 (1,258 with 32 grinding
bits). The cheapest published category-5 instantiation of the Mode S relation needs
about 2,816 bits per seat.

Non-claims
----------
No hidden-signer compact QC is produced. No qualified zero-knowledge backend exists
here. No cryptographic security level (128-bit, QPT-128, category 5) is established
for any concrete instantiation. The symbolic signature provider is a labelled test
double, not a signature scheme. The SHAKE evaluations are concrete function calls,
not collision-resistance or ideal-model claims. Sizes in SIGNATURE_SIZE_TABLE and
the Binius64 tables are transcribed/re-derived from cited public sources for
comparison, not endorsements of any scheme for CE-QS.

CLI: --self-test (unittest, verbosity 2), --explain (prints this docstring),
--report (JSON summary), --real-demo (pqcrypto and/or liboqs-python, the latter only
when OQS_INSTALL_PATH names an installed liboqs).
"""

from dataclasses import dataclass
import argparse
import hashlib
import json
import struct

# ---------------------------------------------------------------------------
# Committee, field and frame constants.
# ---------------------------------------------------------------------------
N = 64
QUORUM = 43
FAULT_BOUND = 21
MIN_OVERLAP = 2 * QUORUM - N          # 22 = the guaranteed double-authorizer count.

BITS = 512
MASK = (1 << BITS) - 1
# Field polynomial X^512 + X^8 + X^5 + X^2 + 1 == (1<<512) | 0x125, as in v1.29/v1.34.
POLY = (1 << BITS) | 0x125

MAGIC = b'CQ44'
VERSION = 44
COUNT = QUORUM
SUITE_B0 = 0x44B0
SUITE_B1 = 0x44B1

HEADER_FORMAT = '>4sHH64s64s64sHHI'
HEADER_BYTES = struct.calcsize(HEADER_FORMAT)          # 208
STATEMENT_FORMAT = '>4sHH64s64s64sHH'                  # header minus the payload_len u32
MAX_FRAME_BYTES = 32768

HANDLE_BYTES = 128
# Registry keys are 1024-bit (128-byte) for the QPT-128 ledger's registry-key
# collision-resistance requirement; the K1 absorb input stays 71 bytes.
B1_REGISTRY_KEY_BYTES = 128
B1_HANDLES_BYTES = QUORUM * HANDLE_BYTES               # 5504
B1_PREFIX_BYTES = HEADER_BYTES + B1_HANDLES_BYTES      # 5712 (header + handles, no proof)
B1_PROOF_MAX = MAX_FRAME_BYTES - B1_PREFIX_BYTES       # 27056

# B0 size gate: 216 = header (208) + bitmap (8); the remaining 43 slots share the rest.
B0_FIXED_BYTES = HEADER_BYTES + 8                       # 216
B0_MAX_SIGNATURE_BYTES = (MAX_FRAME_BYTES - B0_FIXED_BYTES) // QUORUM   # 757


class CertError(ValueError):
    """Malformed frame or violated necessary condition. Never a security verdict."""


class FrameError(CertError):
    """Header/framing/length/size violation."""


class RelationError(CertError):
    """Private R-relation violation (B1)."""


class ExtractionError(CertError):
    """Public algebraic extraction rejected a necessary condition."""


# ---------------------------------------------------------------------------
# Canonical-types parsing discipline (as in v1.34/v1.37): reject non-bytes,
# non-int, wrong length, bool-as-int, etc.
# ---------------------------------------------------------------------------
def _canonical_bytes(value, length, what):
    if type(value) is not bytes or len(value) != length:
        raise FrameError('%s must be exactly %d canonical bytes' % (what, length))
    return value


def _canonical_int(value, low, high, what):
    if type(value) is not int or type(value) is bool or not low <= value <= high:
        raise CertError('%s must be a canonical int in [%d,%d]' % (what, low, high))
    return value


# ---------------------------------------------------------------------------
# Domain-separated hash (v1.29 H with an explicit leading label).
# ---------------------------------------------------------------------------
def H(label, *parts):
    absorb = bytearray()
    for part in (label,) + parts:
        if type(part) is not bytes:
            raise FrameError('H accepts only byte strings')
        absorb += len(part).to_bytes(8, 'big') + part
    return hashlib.shake_256(bytes(absorb)).digest(64)


def decode(message):
    """decode(m) = int.from_bytes(m,'big'); m is the 64-byte direct message."""
    _canonical_bytes(message, 64, 'message')
    return int.from_bytes(message, 'big')


# ---------------------------------------------------------------------------
# GF(2^512) arithmetic. mul() is used to build handles; multiply_by_x() and
# identity_table() are the division-free decoder ported from v1.34.
# ---------------------------------------------------------------------------
def mul(a, b):
    """Reduced product in GF(2)[X]/(POLY); bit coefficients over GF(2)."""
    if type(a) is not int or type(b) is not int or not (0 <= a <= MASK and 0 <= b <= MASK):
        raise CertError('noncanonical field factor')
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a >> BITS:
            a ^= POLY
    return out


def multiply_by_x(value):
    if type(value) is not int or type(value) is bool or not 0 <= value <= MASK:
        raise ExtractionError('noncanonical field input')
    shifted = value << 1
    return shifted ^ POLY if shifted >> BITS else shifted


def identity_table(delta):
    """delta*(seat+1) -> seat for seat in 0..63, built with six xtimes and 64 XORs.

    For a nonzero delta the 64 keys are distinct and nonzero because the field has
    no zero divisors (delta*kappa == delta*kappa' implies kappa == kappa'). Checked
    defensively. This is exactly the v1.34 construction.
    """
    if type(delta) is not int or type(delta) is bool or not 0 < delta <= MASK:
        raise ExtractionError('message difference must be nonzero and canonical')
    basis = [delta]
    for _ in range(6):
        basis.append(multiply_by_x(basis[-1]))
    products = [0] * (N + 1)
    table = {}
    for kappa in range(1, N + 1):
        low_bit = kappa & -kappa
        previous = kappa ^ low_bit
        value = products[previous] ^ basis[low_bit.bit_length() - 1]
        products[kappa] = value
        if value == 0 or value in table:
            raise ExtractionError('field/domain invariant failed')
        table[value] = kappa - 1
    return table


# ---------------------------------------------------------------------------
# Frame header parsing (shared by both profiles).
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Header:
    magic: bytes
    version: int
    suite: int
    cfg: bytes
    domain: bytes
    message: bytes
    count: int
    width: int
    payload_len: int


def pack_header(suite, cfg, domain, message, width, payload_len):
    return struct.pack(HEADER_FORMAT, MAGIC, VERSION, suite, cfg, domain, message,
                       COUNT, width, payload_len)


def parse_frame(frame, expected_suite):
    """Return (Header, payload). Rejects framing, truncation, trailing and oversize."""
    if type(frame) is not bytes:
        raise FrameError('frame must be canonical bytes')
    if len(frame) < HEADER_BYTES:
        raise FrameError('frame shorter than the 208-byte header')
    if len(frame) > MAX_FRAME_BYTES:
        raise FrameError('frame exceeds the %d-byte portability bound' % MAX_FRAME_BYTES)
    magic, version, suite, cfg, domain, message, count, width, payload_len = \
        struct.unpack(HEADER_FORMAT, frame[:HEADER_BYTES])
    if magic != MAGIC:
        raise FrameError('wrong magic')
    if version != VERSION:
        raise FrameError('wrong version')
    if suite != expected_suite:
        raise FrameError('wrong suite for this profile')
    if count != COUNT:
        raise FrameError('count must be 43')
    payload = frame[HEADER_BYTES:]
    if payload_len != len(payload):
        raise FrameError('payload_len does not match the trailing bytes (truncation or trailing data)')
    return Header(magic, version, suite, cfg, domain, message, count, width, payload_len), payload


# ===========================================================================
# Profile B0 — public signer set (suite 0x44B0).
# ===========================================================================
VOTE_PREFIX_B0 = b'CQ44/B0/VOTE'


@dataclass(frozen=True)
class RegistryB0:
    public_keys: tuple
    scheme_id: bytes


@dataclass(frozen=True)
class VerifiedB0:
    cfg: bytes
    domain: bytes
    message: bytes
    width: int
    bitmap: int
    seats: tuple


@dataclass(frozen=True)
class BlameB0:
    seat: int
    position0: int
    position1: int


def _check_registry_b0(registry):
    if type(registry) is not RegistryB0:
        raise FrameError('canonical RegistryB0 required')
    keys = registry.public_keys
    if type(keys) is not tuple or len(keys) != N:
        raise FrameError('registry must hold exactly 64 public keys')
    if any(type(pk) is not bytes or not pk for pk in keys):
        raise FrameError('public keys must be nonempty byte strings')
    if len(set(keys)) != N:
        raise FrameError('registry public keys must be distinct')
    if type(registry.scheme_id) is not bytes:
        raise FrameError('scheme_id must be bytes')


def cfg_b0(registry):
    _check_registry_b0(registry)
    return H(b'CQ44/cfg/B0', registry.scheme_id, *registry.public_keys)


def vote_message_b0(cfg, domain, message, seat):
    _canonical_bytes(cfg, 64, 'cfg')
    _canonical_bytes(domain, 64, 'domain')
    _canonical_bytes(message, 64, 'message')
    _canonical_int(seat, 0, N - 1, 'seat')
    return VOTE_PREFIX_B0 + cfg + domain + message + bytes([seat])


def _seats_from_bitmap(bitmap):
    return tuple(i for i in range(N) if (bitmap >> i) & 1)


def encode_b0(registry, provider, domain, message, secret_keys, seats):
    """Build a B0 frame. secret_keys is aligned with registry.public_keys (64 entries)."""
    cfg = cfg_b0(registry)
    _canonical_bytes(domain, 64, 'domain')
    _canonical_bytes(message, 64, 'message')
    seats = tuple(seats)
    if len(seats) != QUORUM or len(set(seats)) != QUORUM:
        raise FrameError('exactly 43 distinct seats required')
    for i in seats:
        _canonical_int(i, 0, N - 1, 'seat')
    if type(secret_keys) not in (tuple, list) or len(secret_keys) != N:
        raise FrameError('64 secret keys aligned with the registry required')
    width = provider.width
    ordered = sorted(seats)
    signatures = []
    for i in ordered:
        sig = provider.sign(secret_keys[i], vote_message_b0(cfg, domain, message, i))
        if type(sig) is not bytes or len(sig) != width:
            raise FrameError('signature must be exactly the provider width')
        signatures.append(sig)
    bitmap = 0
    for i in ordered:
        bitmap |= 1 << i
    payload = bitmap.to_bytes(8, 'big') + b''.join(signatures)
    return pack_header(SUITE_B0, cfg, domain, message, width, len(payload)) + payload


def verify_b0(frame, registry, provider, expected_cfg):
    """Verify a B0 frame end to end. Raises FrameError on any violation."""
    _canonical_bytes(expected_cfg, 64, 'expected_cfg')
    header, payload = parse_frame(frame, SUITE_B0)
    if header.cfg != expected_cfg:
        raise FrameError('cfg does not match the authenticated expected_cfg')
    if header.cfg != cfg_b0(registry):
        raise FrameError('cfg does not match the registry recomputation')
    width = header.width
    if width != provider.width:
        raise FrameError('header width does not match the provider width')
    if width <= 0:
        raise FrameError('nonpositive signature width')
    if len(payload) != 8 + QUORUM * width:
        raise FrameError('payload length is not 8 + 43*width')
    bitmap = int.from_bytes(payload[:8], 'big')
    if bitmap.bit_count() != QUORUM:
        raise FrameError('bitmap popcount is not 43')
    seats = _seats_from_bitmap(bitmap)
    for pos, seat in enumerate(seats):
        start = 8 + pos * width
        sig = payload[start:start + width]
        msg = vote_message_b0(header.cfg, header.domain, header.message, seat)
        if provider.verify(registry.public_keys[seat], msg, sig) is not True:
            raise FrameError('signature for seat %d does not verify' % seat)
    return VerifiedB0(header.cfg, header.domain, header.message, width, bitmap, seats)


def extract_b0(frame0, frame1, registry, provider, expected_cfg):
    """Publicly extract the common signer seats from two conflicting B0 frames."""
    v0 = verify_b0(frame0, registry, provider, expected_cfg)
    v1 = verify_b0(frame1, registry, provider, expected_cfg)
    if v0.cfg != v1.cfg:
        raise ExtractionError('frames use different configurations')
    if v0.domain != v1.domain:
        raise ExtractionError('frames use different conflict domains')
    if v0.message == v1.message:
        raise ExtractionError('equal messages are not a conflict')
    common = v0.bitmap & v1.bitmap
    # Two accepting quorums of 43 in a 64-seat house always share >= 43+43-64 = 22
    # seats, so this assertion never fires for two valid B0 frames.
    if common.bit_count() < MIN_OVERLAP:
        raise ExtractionError('fewer than 22 common signer seats')
    pos0 = {seat: i for i, seat in enumerate(v0.seats)}
    pos1 = {seat: i for i, seat in enumerate(v1.seats)}
    findings = [BlameB0(seat, pos0[seat], pos1[seat]) for seat in _seats_from_bitmap(common)]
    return tuple(sorted(findings, key=lambda b: b.seat))


def verify_blame_b0(frame0, frame1, registry, provider, expected_cfg, seat):
    """True iff `seat` is a verifiable double-authorizer across the two frames."""
    try:
        _canonical_int(seat, 0, N - 1, 'seat')
        v0 = verify_b0(frame0, registry, provider, expected_cfg)
        v1 = verify_b0(frame1, registry, provider, expected_cfg)
        if v0.domain != v1.domain or v0.message == v1.message:
            return False
        return bool((v0.bitmap >> seat) & 1) and bool((v1.bitmap >> seat) & 1)
    except CertError:
        return False


# ---------------------------------------------------------------------------
# B0 signature providers. Interface: keygen(), sign(sk,msg)->bytes,
# verify(pk,msg,sig)->bool, and attributes width, name, category.
# ---------------------------------------------------------------------------
class SymbolicSignatures:
    """TEST DOUBLE — NOT a cryptographic signature scheme (style of v1.37).

    Records the (pk, msg, sig) triples it issues and pads each signature to a
    declared width. It proves nothing about any real scheme; it exists only to
    exercise the B0 frame logic deterministically with stdlib.
    """
    name = 'SYMBOLIC-NON-CRYPTOGRAPHIC'
    category = 0

    def __init__(self, width=128):
        if type(width) is not int or width < 24:
            raise FrameError('symbolic width must be an int >= 24')
        self.width = width
        self._counter = 0
        self._valid = set()

    def _pk_of(self, sk):
        return b'SYM-PK-' + sk[len(b'SYM-SK-'):]

    def keygen(self):
        self._counter += 1
        seed = self._counter.to_bytes(8, 'big')
        return b'SYM-PK-' + seed, b'SYM-SK-' + seed

    def sign(self, sk, msg):
        pk = self._pk_of(sk)
        core = b'SYMSIG' + hashlib.shake_256(sk + msg).digest(16)
        sig = (core + bytes(self.width))[:self.width]
        self._valid.add((pk, msg, sig))
        return sig

    def verify(self, pk, msg, sig):
        return (pk, msg, sig) in self._valid


class RealSignatures:
    """Optional wrapper over a pqcrypto.sign module (detached-signature API).

    The pqcrypto pure API is generate_keypair(), sign(secret_key, message) which
    returns a detached signature, and verify(public_key, message, signature). For
    the padded schemes the signature length is fixed at module.SIGNATURE_SIZE, so
    the frame slot width equals that size. Tests never require this class.
    """
    def __init__(self, module, name, category):
        self._m = module
        self.name = name
        self.category = category
        self.width = module.SIGNATURE_SIZE

    def keygen(self):
        return self._m.generate_keypair()

    def sign(self, sk, msg):
        sig = self._m.sign(sk, msg)
        if len(sig) < self.width:                    # padded schemes never take this path
            sig = sig + bytes(self.width - len(sig))
        if len(sig) != self.width:
            raise FrameError('real signature is wider than the declared slot')
        return sig

    def verify(self, pk, msg, sig):
        try:
            return self._m.verify(pk, msg, sig) is True
        except Exception:
            return False


def try_load_real_providers():
    """Return {'falcon_padded_512', 'ml_dsa_87', ...} providers, or None if absent."""
    try:
        from pqcrypto.sign import (falcon_padded_512, ml_dsa_87,
                                    falcon_padded_1024, sphincs_shake_256s_simple)
    except Exception:
        return None
    return {
        'falcon_padded_512': RealSignatures(falcon_padded_512, 'Falcon-padded-512', 1),
        'ml_dsa_87': RealSignatures(ml_dsa_87, 'ML-DSA-87', 5),
        'falcon_padded_1024': RealSignatures(falcon_padded_1024, 'Falcon-padded-1024', 5),
        'sphincs_shake_256s_simple': RealSignatures(sphincs_shake_256s_simple,
                                                    'SLH-DSA-SHAKE-256s', 5),
    }


class OqsSignatures:
    """Optional wrapper over liboqs-python's oqs.Signature. Tests never require it.

    B0 slots are fixed width, so a scheme is admitted only if every signature has
    exactly length_signature bytes; a shorter signature is refused, not padded.
    """
    def __init__(self, oqs_module, alg, category):
        self._oqs = oqs_module
        self.name = alg
        with oqs_module.Signature(alg) as probe:
            details = probe.details
        if details['claimed_nist_level'] != category:
            raise FrameError('liboqs claimed level differs from the declared category')
        self.category = category
        self.width = details['length_signature']

    def keygen(self):
        with self._oqs.Signature(self.name) as signer:
            pk = signer.generate_keypair()
            sk = signer.export_secret_key()
        return pk, sk

    def sign(self, sk, msg):
        with self._oqs.Signature(self.name, sk) as signer:
            sig = signer.sign(msg)
        if len(sig) != self.width:
            raise FrameError('variable-length signature does not fill the fixed slot')
        return sig

    def verify(self, pk, msg, sig):
        try:
            with self._oqs.Signature(self.name) as verifier:
                return verifier.verify(msg, sig, pk) is True
        except Exception:
            return False


class HybridSignatures:
    """AND-combiner of two providers with independent keys. A slot is sig_a||sig_b
    and verifies only if both halves verify, so a forgery must forge both schemes.
    The combined public key is u32be(len(pk_a))||pk_a||pk_b."""
    def __init__(self, first, second):
        self._a = first
        self._b = second
        self.name = first.name + '||' + second.name
        self.category = min(first.category, second.category)
        self.width = first.width + second.width

    @property
    def tamper_offsets(self):
        """One byte inside each half, used by the real demo's tamper check."""
        return (self._a.width // 2, self._a.width + self._b.width // 2)

    def keygen(self):
        pk_a, sk_a = self._a.keygen()
        pk_b, sk_b = self._b.keygen()
        return struct.pack('>I', len(pk_a)) + pk_a + pk_b, (sk_a, sk_b)

    def sign(self, sk, msg):
        return self._a.sign(sk[0], msg) + self._b.sign(sk[1], msg)

    def verify(self, pk, msg, sig):
        if type(pk) is not bytes or len(pk) < 4:
            return False
        if type(sig) is not bytes or len(sig) != self.width:
            return False
        la = struct.unpack('>I', pk[:4])[0]
        if 4 + la >= len(pk):
            return False
        wa = self._a.width
        return (self._a.verify(pk[4:4 + la], msg, sig[:wa]) is True
                and self._b.verify(pk[4 + la:], msg, sig[wa:]) is True)


OQS_B0_SCHEMES = (('OV-V-pkc', 5), ('SNOVA_29_6_5', 5), ('SNOVA_60_10_4', 5),
                  ('MAYO-5', 5), ('ML-DSA-87', 5))


def try_load_oqs_providers():
    """Return liboqs providers keyed by name (plus the OV-V||SNOVA hybrid), or None.

    liboqs-python clones and builds liboqs whenever it cannot load an installed
    library, and raises SystemExit if that build fails. So the exact library under
    OQS_INSTALL_PATH is loaded with ctypes first, and the wrapper is imported only
    if that succeeds. SystemExit during the import counts as unavailable, and the
    wrapper's import-time output is kept off stdout and stderr."""
    import contextlib
    import ctypes
    import io
    import os
    root = os.environ.get('OQS_INSTALL_PATH')
    if not root:
        return None
    candidates = [os.path.join(root, sub, 'liboqs.so') for sub in ('lib', 'lib64')]
    library = next((path for path in candidates if os.path.exists(path)), None)
    if library is None:
        return None
    try:
        ctypes.CDLL(library)
    except OSError:
        return None
    try:
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            import oqs
        enabled = set(oqs.get_enabled_sig_mechanisms())
    except (Exception, SystemExit):
        return None
    providers = {}
    for alg, category in OQS_B0_SCHEMES:
        if alg not in enabled:
            continue
        try:
            providers[alg] = OqsSignatures(oqs, alg, category)
        except Exception:
            continue
    if 'OV-V-pkc' in providers and 'SNOVA_29_6_5' in providers:
        hybrid = HybridSignatures(providers['OV-V-pkc'], providers['SNOVA_29_6_5'])
        providers[hybrid.name] = hybrid
    return providers


# ---------------------------------------------------------------------------
# B0 size gate and the extensible size table.
# ---------------------------------------------------------------------------
def b0_frame_bytes(sig_bytes):
    _canonical_int(sig_bytes, 0, 1 << 40, 'sig_bytes')
    return B0_FIXED_BYTES + QUORUM * sig_bytes


def b0_fits(sig_bytes):
    return b0_frame_bytes(sig_bytes) <= MAX_FRAME_BYTES


# Only verifiable, sourced entries. NIST categories are the claimed levels, not a
# QPT-128 verdict for CE-QS. "measured" means signed, verified and tamper-rejected
# through liboqs 0.16.0 (commit 5a1a854b0dc9f2141bdc771c555ee60c37950183).
SIGNATURE_SIZE_TABLE = [
    {'name': 'ML-DSA-87', 'nist_category': 5, 'signature_bytes': 4627,
     'source': 'FIPS 204, Table 2; measured liboqs 0.16.0'},
    {'name': 'SLH-DSA-SHAKE-256s', 'nist_category': 5, 'signature_bytes': 29792,
     'source': 'FIPS 205, Table 2; measured liboqs 0.16.0'},
    {'name': 'Falcon-padded-1024', 'nist_category': 5, 'signature_bytes': 1280,
     'source': 'Falcon round-3 padded signature size; measured liboqs 0.16.0'},
    {'name': 'Falcon-padded-512', 'nist_category': 1, 'signature_bytes': 666,
     'source': 'Falcon round-3 padded signature size'},
    {'name': 'OV-V', 'nist_category': 5, 'signature_bytes': 260,
     'public_key_bytes': 2869440, 'public_key_bytes_pkc': 446992,
     'source': 'UOV, NIST additional signatures; measured liboqs 0.16.0'},
    {'name': 'SNOVA_29_6_5', 'nist_category': 5, 'signature_bytes': 454,
     'public_key_bytes': 2716,
     'source': 'SNOVA, NIST additional signatures; measured liboqs 0.16.0'},
    {'name': 'SNOVA_60_10_4', 'nist_category': 5, 'signature_bytes': 576,
     'public_key_bytes': 8016,
     'source': 'SNOVA, NIST additional signatures; measured liboqs 0.16.0'},
    {'name': 'OV-V||SNOVA_29_6_5', 'nist_category': 5, 'signature_bytes': 714,
     'source': 'AND-hybrid of the two measured entries above'},
    {'name': 'MAYO-5', 'nist_category': 5, 'signature_bytes': 964,
     'public_key_bytes': 5554,
     'source': 'MAYO, NIST additional signatures; measured liboqs 0.16.0'},
    {'name': 'SQIsign-V', 'nist_category': 5, 'signature_bytes': 292,
     'source': 'SQIsign round-2 specification; not executed here'},
    {'name': 'HAWK-1024', 'nist_category': 5, 'signature_bytes': 1221,
     'source': 'HAWK round-2 specification; not executed here'},
]


# ===========================================================================
# Profile B1 — hidden signer set, "Mode S" (suite 0x44B1).
# ===========================================================================
@dataclass(frozen=True)
class RegistryB1:
    keys: tuple                                       # 64 registered K[i], 128 bytes each


def register_key_b1(x):
    """K1(x) = SHAKE256(b'CEQS/K1' || x)[:128]. Input length is 7 + 64 = 71 bytes,
    one SHAKE256 absorb block; the 128-byte (1024-bit) output is one squeeze and
    carries the registry-key collision resistance the QPT-128 ledger relies on."""
    _canonical_bytes(x, 64, 'credential x')
    absorb = b'CEQS/K1' + x
    if len(absorb) != 71:
        raise RelationError('K1 absorb input must be 71 bytes')
    return hashlib.shake_256(absorb).digest(B1_REGISTRY_KEY_BYTES)


def _check_registry_b1(registry):
    if type(registry) is not RegistryB1:
        raise FrameError('canonical RegistryB1 required')
    keys = registry.keys
    if type(keys) is not tuple or len(keys) != N:
        raise FrameError('registry must hold exactly 64 keys')
    for k in keys:
        _canonical_bytes(k, B1_REGISTRY_KEY_BYTES, 'registered key')
    if len(set(keys)) != N:
        raise FrameError('registered keys must be distinct')


def cfg_b1(registry):
    _check_registry_b1(registry)
    return H(b'CQ44/cfg/B1', *registry.keys)


def context_b1(cfg, domain):
    _canonical_bytes(cfg, 64, 'cfg')
    _canonical_bytes(domain, 64, 'domain')
    return H(b'CQ44/ctx', cfg, domain)


def handle_b1(x, seat, D, message):
    """L||Z (128 bytes). The pair input b'CEQS/P1'||x||D is 135 bytes, one absorb block."""
    _canonical_bytes(x, 64, 'credential x')
    _canonical_int(seat, 0, N - 1, 'seat')
    _canonical_bytes(D, 64, 'context D')
    absorb = b'CEQS/P1' + x + D
    if len(absorb) != 135:
        raise RelationError('pair absorb input must be 135 bytes (one SHAKE256 block)')
    pair = hashlib.shake_256(absorb).digest(128)
    L = pair[:64]
    Z = (int.from_bytes(pair[64:], 'big') ^ mul(decode(message), seat + 1)).to_bytes(64, 'big')
    return L + Z


def statement_bytes_b1(cfg, domain, message, handles, width=HANDLE_BYTES):
    """Canonical proof statement: the header fields EXCEPT payload_len, then the
    5,504 handle bytes. payload_len is excluded because it depends on the proof
    length; every field the relation binds (cfg, domain, message, count, width and
    the handles) is included exactly once, in header order."""
    _canonical_bytes(cfg, 64, 'cfg')
    _canonical_bytes(domain, 64, 'domain')
    _canonical_bytes(message, 64, 'message')
    if type(handles) not in (tuple, list) or len(handles) != QUORUM:
        raise FrameError('exactly 43 handles required for the statement')
    body = b''.join(handles)
    if len(body) != B1_HANDLES_BYTES:
        raise FrameError('handles must total 5504 bytes')
    return struct.pack(STATEMENT_FORMAT, MAGIC, VERSION, SUITE_B1, cfg, domain,
                       message, COUNT, width) + body


def check_relation(cfg, domain, message, handles, rows, registry_keys):
    """Executable R-relation on 43 (seat, x) rows in handle order. Raises RelationError.

    (1) each seat is an int in 0..63 and the 43 seats are DISTINCT (explicit check);
    (2) K1(x) equals K[seat];
    (3) the handle at that position equals handle(x, seat, D, m).
    Seeing the private rows, this is not a zero-knowledge proof; it is the relation
    a qualified backend would have to prove in zero knowledge.
    """
    D = context_b1(cfg, domain)
    if type(registry_keys) not in (tuple, list) or len(registry_keys) != N:
        raise RelationError('64 registry keys required')
    if type(handles) not in (tuple, list) or len(handles) != QUORUM:
        raise RelationError('exactly 43 handles required')
    if type(rows) not in (tuple, list) or len(rows) != QUORUM:
        raise RelationError('exactly 43 rows required')
    seats = []
    for row in rows:
        if type(row) not in (tuple, list) or len(row) != 2:
            raise RelationError('each row is a (seat, x) pair')
        seat, x = row
        _canonical_int(seat, 0, N - 1, 'seat')
        seats.append(seat)
    if len(set(seats)) != QUORUM:                     # explicit distinctness check (1)
        raise RelationError('the 43 seats must be distinct')
    for pos, (seat, x) in enumerate(rows):
        if register_key_b1(x) != registry_keys[seat]:                       # (2)
            raise RelationError('credential does not open the registered key for seat %d' % seat)
        if handles[pos] != handle_b1(x, seat, D, message):                  # (3)
            raise RelationError('handle at position %d does not recompute' % pos)
    return True


def distinctness_lemma(seat, x_a, x_b, cfg, domain, message, registry_keys):
    """Demonstrate the v0.5 distinctness lemma for two rows that share `seat`.

    If two accepted rows share a seat index then either their credentials differ,
    in which case at most one opens the registered K (barring a K collision), or
    the rows are identical, in which case their handles are equal so the strict
    link ordering of the payload is violated. Returns a dict describing the branch.
    """
    D = context_b1(cfg, domain)
    if x_a != x_b:
        return {
            'branch': 'credentials_differ',
            'k_check_a': register_key_b1(x_a) == registry_keys[seat],
            'k_check_b': register_key_b1(x_b) == registry_keys[seat],
        }
    ha = handle_b1(x_a, seat, D, message)
    hb = handle_b1(x_b, seat, D, message)
    return {
        'branch': 'identical_rows',
        'links_equal': ha[:64] == hb[:64],
        'strict_link_ordering_violated': not (ha[:64] < hb[:64]),
    }


# ---------------------------------------------------------------------------
# B1 proof backends. Only the unqualified structure-only backend exists.
# ---------------------------------------------------------------------------
class StructureOnlyTestBackend:
    """NOT A PROOF. qualified=False. The 'proof' is a fixed marker and verify()
    checks only that marker. It certifies nothing about the relation or authorization.
    It exists so the B1 frame path is executable end to end with stdlib.
    """
    qualified = False
    MARKER = b'STRUCTURE-ONLY/NOT-A-PROOF/CQ44-B1/v1.44'

    def prove(self, statement_bytes, rows):
        if type(statement_bytes) is not bytes:
            raise RelationError('statement bytes required')
        return self.MARKER

    def verify(self, statement_bytes, proof):
        return proof == self.MARKER


def encode_b1(registry, domain, message, rows, backend):
    """Build a B1 frame from 43 (seat, x) rows and a proof backend."""
    cfg = cfg_b1(registry)
    _canonical_bytes(domain, 64, 'domain')
    _canonical_bytes(message, 64, 'message')
    if type(rows) not in (tuple, list) or len(rows) != QUORUM:
        raise FrameError('exactly 43 rows required')
    D = context_b1(cfg, domain)
    built = []
    for row in rows:
        if type(row) not in (tuple, list) or len(row) != 2:
            raise FrameError('each row is a (seat, x) pair')
        seat, x = row
        _canonical_int(seat, 0, N - 1, 'seat')
        built.append((handle_b1(x, seat, D, message), (seat, x)))
    built.sort(key=lambda item: item[0][:64])
    handles = [h for h, _ in built]
    ordered_rows = [r for _, r in built]
    for a, b in zip(handles, handles[1:]):
        if a[:64] >= b[:64]:
            raise FrameError('handles must be strictly increasing by link')
    statement = statement_bytes_b1(cfg, domain, message, handles)
    proof = backend.prove(statement, ordered_rows)
    if type(proof) is not bytes:
        raise FrameError('backend must return bytes')
    if len(proof) > B1_PROOF_MAX:
        raise FrameError('proof exceeds the %d-byte budget' % B1_PROOF_MAX)
    payload = b''.join(handles) + proof
    return pack_header(SUITE_B1, cfg, domain, message, HANDLE_BYTES, len(payload)) + payload


def _parse_handles_b1(handle_region):
    if len(handle_region) != B1_HANDLES_BYTES:
        raise FrameError('handle region must be 5504 bytes')
    handles = [handle_region[p:p + HANDLE_BYTES]
               for p in range(0, B1_HANDLES_BYTES, HANDLE_BYTES)]
    for a, b in zip(handles, handles[1:]):
        if a[:64] >= b[:64]:
            raise FrameError('links must be strictly increasing and distinct')
    return handles


@dataclass(frozen=True)
class ParsedB1:
    cfg: bytes
    domain: bytes
    message: bytes
    handles: tuple
    proof: bytes


def parse_b1(frame):
    header, payload = parse_frame(frame, SUITE_B1)
    if header.width != HANDLE_BYTES:
        raise FrameError('B1 width must be 128')
    if len(payload) < B1_HANDLES_BYTES:
        raise FrameError('payload shorter than the 43 handles')
    proof = payload[B1_HANDLES_BYTES:]
    if len(proof) > B1_PROOF_MAX:
        raise FrameError('proof exceeds the %d-byte budget' % B1_PROOF_MAX)
    handles = _parse_handles_b1(payload[:B1_HANDLES_BYTES])
    return ParsedB1(header.cfg, header.domain, header.message, tuple(handles), proof)


def verify_b1(frame, registry, backend, expected_cfg):
    """Structure verifier. With no qualified backend, authorization is never verified."""
    _canonical_bytes(expected_cfg, 64, 'expected_cfg')
    parsed = parse_b1(frame)
    if parsed.cfg != expected_cfg:
        raise FrameError('cfg does not match the authenticated expected_cfg')
    if parsed.cfg != cfg_b1(registry):
        raise FrameError('cfg does not match the registry recomputation')
    statement = statement_bytes_b1(parsed.cfg, parsed.domain, parsed.message, parsed.handles)
    structurally_accepted = backend.verify(statement, parsed.proof) is True
    qualified = bool(getattr(backend, 'qualified', False))
    return {
        'format': 'CQ44-B1-MODE-S-v1.44',
        'status': ('QUALIFIED_PROOF_VERIFIED' if (qualified and structurally_accepted)
                   else 'STRUCTURE_ONLY_NO_QUALIFIED_PROOF'),
        'qualified_backend': qualified,
        'proof_structurally_accepted': structurally_accepted,
        # No qualified backend exists in this file, so this is always False.
        'authorization_verified': qualified and structurally_accepted,
        'cfg_hex': parsed.cfg.hex(),
        'proof_len': len(parsed.proof),
    }


def extract_b1(frame0, frame1, expected_cfg):
    """Port of the v1.34 division-free decoder over the parsed B1 handles.

    Returns ALGEBRAIC CANDIDATES ONLY. Attribution to actual signers additionally
    requires two qualified authorization proofs, which this file does not verify.
    """
    _canonical_bytes(expected_cfg, 64, 'expected_cfg')
    left, right = parse_b1(frame0), parse_b1(frame1)
    if left.cfg != expected_cfg or right.cfg != expected_cfg:
        raise ExtractionError('configuration does not match the authenticated value')
    if left.domain != right.domain:
        raise ExtractionError('frames use different conflict domains')
    if left.message == right.message:
        raise ExtractionError('equal messages are not a conflict')
    delta = decode(left.message) ^ decode(right.message)
    if delta == 0:
        raise ExtractionError('message difference is zero')
    table = identity_table(delta)
    left_h = [(h[:64], int.from_bytes(h[64:], 'big')) for h in left.handles]
    right_h = [(h[:64], int.from_bytes(h[64:], 'big')) for h in right.handles]
    a = b = 0
    findings = []
    seen = set()
    while a < QUORUM and b < QUORUM:
        l0, z0 = left_h[a]
        l1, z1 = right_h[b]
        if l0 < l1:
            a += 1
        elif l0 > l1:
            b += 1
        else:
            seat = table.get(z0 ^ z1)
            if seat is None:
                raise ExtractionError('matched link gives a zero or out-of-range identity')
            if seat in seen:
                raise ExtractionError('distinct matched links give a duplicate identity')
            seen.add(seat)
            findings.append({'seat': seat, 'left_position': a, 'right_position': b,
                             'link_hex': l0.hex()})
            a += 1
            b += 1
    if len(findings) < MIN_OVERLAP:
        raise ExtractionError('fewer than 22 recovered identities')
    findings.sort(key=lambda f: f['seat'])
    return {
        'format': 'CQ44-B1-ALGEBRAIC-EXTRACTION-v1.44',
        'status': 'ALGEBRAIC_CANDIDATES_ONLY',
        'authorization_verified': False,
        'count': len(findings),
        'findings': findings,
        'requires_before_attribution':
            'Authenticate cfg and verify two qualified B1 authorization proofs.',
    }


# ===========================================================================
# Lower-bound calculators. Pure arithmetic with provenance.
# ===========================================================================
# A keccak-f[1600] permutation applies the chi (theta/rho/pi/chi/iota) step to 1600
# bits over 24 rounds; the chi step is the only nonlinear step and uses one AND per
# state bit, i.e. 1600 AND gates per round, 24*1600 = 38,400 per permutation.
KECCAK_F1600_BIT_AND_GATES = 24 * 1600                 # 38,400

# Binius64 counts AND CONSTRAINTS, not bit-level gates, packing 64 bits per word.
# Provenance: the snapshot files keccak.snap and sha3_512.snap of the vendored Binius64
# tree (continuation_v1.17/binius64-source/crates/examples/snapshots; upstream
# binius-zk/binius64, pinned commit 37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4). That tree
# is not copied into this repository; its provenance records live under
# domains/03-zk-carrier-experiments/ (results/source-comparison.json, docs/method.md).
#   keccak.snap    : 4,779 AND used for 8 keccak-f permutations == 8*600 - 21.
#   sha3_512.snap  : 8,983 AND used for 15 permutations         == 15*600 - 17.
# The per-permutation figure is thus 600 AND constraints, with small fixed slack.
BINIUS64_AND_PER_KECCAK_PERMUTATION = 600
_KECCAK_SNAP_AND = 4779                                # 8*600 - 21
_SHA3_512_SNAP_AND = 8983                              # 15*600 - 17

# Mode S hashes 43 seats, two SHAKE256 absorb blocks' worth of keccak-f each in the
# handle+key derivations that a proof must cover: 43*2 = 86 permutations.
MODE_S_KECCAK_PERMUTATIONS = QUORUM * 2                 # 86


def linear_size_proof_lower_bound_bytes(and_bits):
    """ceil(and_bits/8) bytes.

    VOLE-in-the-head transmits at least one correction bit per AND-gate output;
    ZKBoo/KKW-style commit-and-open reveals at least one party's AND outputs per
    repetition. Either way the proof carries at least one bit per AND gate output,
    so its size is at least ceil(and_bits/8) bytes. This is a lower bound for those
    proof FAMILIES on the given circuit, not a universal proof-size lower bound.
    """
    _canonical_int(and_bits, 0, 1 << 60, 'and_bits')
    return (and_bits + 7) // 8


def mode_s_linear_lower_bound_bytes():
    """86 permutations * 38,400 AND bits each = 3,302,400 bits = 412,800 bytes,
    versus the 27,056-byte Mode S proof budget."""
    return linear_size_proof_lower_bound_bytes(
        MODE_S_KECCAK_PERMUTATIONS * KECCAK_F1600_BIT_AND_GATES)


def per_seat_witness_bit_budget(fixed_proof_bytes):
    """floor((27056 - fixed)*8 / 43): witness bits per seat after fixed proof overhead."""
    _canonical_int(fixed_proof_bytes, 0, B1_PROOF_MAX, 'fixed_proof_bytes')
    return (B1_PROOF_MAX - fixed_proof_bytes) * 8 // QUORUM


# Pinned Binius64 PCS proof sizes at 96-bit soundness, indexed by log2 of the
# committed word count. Provenance: crates/iop/src/fri/size_estimation.rs and
# crates/iop/src/whir/size_estimation.rs in the vendored Binius64 source (upstream
# binius-zk/binius64 at the pinned commit above; that tree is not copied into this
# repository, see domains/03-zk-carrier-experiments/), reproduced here by an
# independent re-implementation of those estimators.
BINIUS64_PCS_MIN_BYTES_96BIT = {
    #  log2 : (FRI best-rate bytes, WHIR bytes)
    8:  (19776, 17744),
    9:  (27200, 23968),
    10: (38720, 30560),
    12: (69184, 45808),
    16: (135680, 109856),
    20: (214048, 188320),
}


def binius64_min_bytes(log2_committed):
    """Smallest pinned proof size at or above the given committed log2 size.

    Returns the smaller of the FRI and WHIR entries at the smallest tabulated log2
    that is >= log2_committed. Because proof size grows with the committed size,
    this is a floor for any committed size up to that log2.
    """
    _canonical_int(log2_committed, 0, 64, 'log2_committed')
    for k in sorted(BINIUS64_PCS_MIN_BYTES_96BIT):
        if k >= log2_committed:
            fri, whir = BINIUS64_PCS_MIN_BYTES_96BIT[k]
            return min(fri, whir)
    raise ValueError('log2_committed beyond the pinned table')


# Mode S commits at least 86*600 = 51,600 words > 2^15, so the relevant floor is at
# least the log2=16 entry, 109,856 bytes even at 96-bit soundness, versus 27,056.
MODE_S_COMMITTED_WORDS_MIN = MODE_S_KECCAK_PERMUTATIONS * BINIUS64_AND_PER_KECCAK_PERMUTATION


def _ceil_log2(value):
    if value <= 1:
        return 0
    return (value - 1).bit_length()


# ---------------------------------------------------------------------------
# Theorem C: size floor for witness-committing proofs of the hidden-signer
# relation.
#
# Family: KKW-, BN++- and FAEST-style proofs with tau parallel repetitions. Each
# repetition (i) accepts a prover without a witness with probability at least
# 2^-b (b = log2 of the party count N), and (ii) carries at least one correction
# bit per extended-witness bit: the seat credentials plus further witness bits
# (nonlinear wire outputs or intermediate states). ZKB++ (the third input share
# is sent in only 2 of 3 challenges) and Ligero-style sublinear proofs violate
# (ii) and are not covered. The challenge is a hash chain of 2^h steps over a
# suffix the prover chooses (a grinding counter or the unopened commitment),
# optionally with a w_g-bit grinding condition.
#
# The bounds are NECESSARY conditions obtained from attacks, so they use an UPPER
# bound on the cost of one Grover iteration. The named assumption is at most 2^24
# gates per hash evaluation; the Keccak-f[1600] T-count alone is 499,200 < 2^19,
# and 2^5 is allowed for uncomputation and Clifford gates. Fewer than 2^128 gates
# then allow up to 2^(104 - h) iterations. The report also shows 2^18 gates.
# ---------------------------------------------------------------------------
ATTACK_GATE_BUDGET_LOG2 = 128
ATTACK_GATES_PER_HASH_LOG2 = 24
GROVER_ITERATIONS_LOG2 = ATTACK_GATE_BUDGET_LOG2 - ATTACK_GATES_PER_HASH_LOG2   # 104


def grover_reaches_one_third(log2_space, log2_marked=0,
                             iterations_log2=GROVER_ITERATIONS_LOG2):
    """True if at most 2^iterations_log2 - 1 Grover iterations reach success >= 1/3
    against 2^log2_marked marked points among 2^log2_space (sufficient condition).

    Let p = 2^(marked - space) and sin^2(theta) = p.
    - p >= 1/2: k = 0 already succeeds.
    - 1/16 <= p <= 1/4: k = 1 gives 3 theta in [0.758, pi/2], so
      sin^2(3 theta) > 0.47.
    - p <= 1/32: put y = (2k+1)sqrt(p). Consecutive k move y by 2 sqrt(p) <= 0.354,
      which is less than 19/50, and k = 0 gives y < 31/50. So whenever the largest
      allowed k gives y >= 31/50, some k puts y in [31/50, 1]. There
      (2k+1)theta lies in [y, 1.02 y], inside [0, pi/2], and
      sin^2((2k+1)theta) >= sin^2(y) >= (y - y^3/6)^2 >= 1/3 (checked exactly in
      the tests at y = 31/50)."""
    _canonical_int(log2_space, 0, 1 << 16, 'log2_space')
    _canonical_int(log2_marked, 0, log2_space, 'log2_marked')
    _canonical_int(iterations_log2, 0, 256, 'iterations_log2')
    gap = log2_space - log2_marked
    if gap <= 1:
        return True
    if gap <= 4:
        return iterations_log2 >= 1
    two_k_plus_1 = 2 * ((1 << iterations_log2) - 1) + 1
    # y^2 = two_k_plus_1^2 * 2^(marked - space) >= (31/50)^2
    return (two_k_plus_1 ** 2 * 2500) << log2_marked >= 961 << log2_space


def min_secure_bits(log2_marked=0, iterations_log2=GROVER_ITERATIONS_LOG2):
    """Smallest search-space size in bits that the generic Grover attack above does
    not break: a necessary size for QPT-128 under the per-iteration cost bound."""
    bits = log2_marked
    while grover_reaches_one_third(bits, log2_marked, iterations_log2):
        bits += 1
    return bits


def _theorem_c_parameters(log2_parties, attack_gates_log2, challenge_hash_steps_log2,
                          grinding_bits, ggm_seeds):
    _canonical_int(log2_parties, 1, 128, 'log2_parties')
    _canonical_int(attack_gates_log2, 0, 127, 'attack_gates_log2')
    _canonical_int(challenge_hash_steps_log2, 0, 127 - attack_gates_log2,
                   'challenge_hash_steps_log2')
    _canonical_int(grinding_bits, 0, 256, 'grinding_bits')
    iterations = ATTACK_GATE_BUDGET_LOG2 - attack_gates_log2
    s = min_secure_bits(0, iterations - challenge_hash_steps_log2)
    tau = max(1, -(-(s - grinding_bits) // log2_parties))
    credential_bits = min_secure_bits(6, iterations)
    fixed = tau * log2_parties * min_secure_bits(0, iterations) if ggm_seeds else 0
    return tau, s, credential_bits, fixed


def theorem_c_budget(log2_parties, attack_gates_log2=ATTACK_GATES_PER_HASH_LOG2,
                     challenge_hash_steps_log2=0, grinding_bits=0, ggm_seeds=False):
    """Per-seat witness budget that Theorem C allows in the 27,056-byte proof slot.

    Grover on the challenge suffix runs up to 2^(128 - g - h) iterations against the
    marked fraction 2^-(tau*b + w_g), so tau*b + w_g >= s, where
    s = min_secure_bits(0, 128 - g - h). The credential search does not involve the
    challenge hash, so credentials need c = min_secure_bits(6, 128 - g) bits for 64
    targets. With ggm_seeds, each repetition also opens b seeds of at least
    min_secure_bits(0, 128 - g) bits. FAEST's batched opening lies outside that
    hypothesis, so the seed term is off by default. per_seat_budget_bits includes
    the credential; max_wires_per_seat is what remains beyond it (-1 if negative)."""
    tau, s, credential_bits, fixed = _theorem_c_parameters(
        log2_parties, attack_gates_log2, challenge_hash_steps_log2, grinding_bits,
        ggm_seeds)
    budget = B1_PROOF_MAX * 8 - fixed
    per_seat = budget // (tau * QUORUM) if budget >= 0 else -1
    return {'tau': tau, 'challenge_bits_required': s,
            'credential_bits': credential_bits, 'per_seat_budget_bits': per_seat,
            'max_wires_per_seat': max(-1, per_seat - credential_bits)}


def max_wires_per_seat(log2_parties, **kwargs):
    """Alias of theorem_c_budget, kept for the v1.44 report key names."""
    return theorem_c_budget(log2_parties, **kwargs)


def witness_committing_floor(log2_parties, witness_bits_per_seat,
                             attack_gates_log2=ATTACK_GATES_PER_HASH_LOG2,
                             challenge_hash_steps_log2=0, grinding_bits=0,
                             ggm_seeds=False):
    """Theorem C lower bound in bits for a proof in which every seat uses
    witness_bits_per_seat extended-witness bits, credential included."""
    _canonical_int(witness_bits_per_seat, 0, 1 << 40, 'witness_bits_per_seat')
    tau, s, _, fixed = _theorem_c_parameters(
        log2_parties, attack_gates_log2, challenge_hash_steps_log2, grinding_bits,
        ggm_seeds)
    return {'tau': tau, 'challenge_bits_required': s,
            'proof_bits_floor': tau * QUORUM * witness_bits_per_seat + fixed}


THEOREM_C_LOG2_PARTIES = (8, 12, 16, 20, 24, 32, 40, 48)


# ===========================================================================
# JSON report.
# ===========================================================================
def build_report():
    size_table = []
    for entry in SIGNATURE_SIZE_TABLE:
        sb = entry['signature_bytes']
        size_table.append({
            **entry,
            'b0_frame_bytes': b0_frame_bytes(sb),
            'b0_fits': b0_fits(sb),
        })
    log2_committed = _ceil_log2(MODE_S_COMMITTED_WORDS_MIN)
    return {
        'module': 'sidecar_free_certificate',
        'constants': {
            'N': N, 'QUORUM': QUORUM, 'FAULT_BOUND': FAULT_BOUND,
            'MIN_OVERLAP': MIN_OVERLAP,
            'MAX_FRAME_BYTES': MAX_FRAME_BYTES, 'HEADER_BYTES': HEADER_BYTES,
            'B0_MAX_SIGNATURE_BYTES': B0_MAX_SIGNATURE_BYTES,
            'HANDLE_BYTES': HANDLE_BYTES,
            'registry_key_bytes': B1_REGISTRY_KEY_BYTES,
            'B1_PREFIX_BYTES': B1_PREFIX_BYTES, 'B1_PROOF_MAX': B1_PROOF_MAX,
            'SUITE_B0': hex(SUITE_B0), 'SUITE_B1': hex(SUITE_B1),
            'field_poly_hex': hex(POLY),
        },
        'b0_size_table': size_table,
        'b0_size_gate': {
            'sig_bytes_757_fits': b0_fits(757),
            'sig_bytes_758_fits': b0_fits(758),
            'frame_bytes_at_757': b0_frame_bytes(757),
        },
        'b1_budgets': {
            'proof_max_bytes': B1_PROOF_MAX,
            'per_seat_witness_bit_budget_fixed_0': per_seat_witness_bit_budget(0),
            'body_bytes_header_plus_handles': B1_PREFIX_BYTES,
        },
        'lower_bounds': {
            'keccak_f1600_and_gates': KECCAK_F1600_BIT_AND_GATES,
            'binius64_and_per_keccak_permutation': BINIUS64_AND_PER_KECCAK_PERMUTATION,
            'mode_s_keccak_permutations': MODE_S_KECCAK_PERMUTATIONS,
            'mode_s_linear_lower_bound_bytes': mode_s_linear_lower_bound_bytes(),
            'mode_s_committed_words_min': MODE_S_COMMITTED_WORDS_MIN,
            'mode_s_committed_log2_ceiling': log2_committed,
            'binius64_pcs_floor_bytes': binius64_min_bytes(log2_committed),
            'proof_budget_bytes': B1_PROOF_MAX,
            'linear_floor_exceeds_budget': mode_s_linear_lower_bound_bytes() > B1_PROOF_MAX,
            'binius64_floor_exceeds_budget': binius64_min_bytes(log2_committed) > B1_PROOF_MAX,
        },
        'theorem_c_witness_committing': {
            'attack_gates_per_hash_log2_upper_bound': ATTACK_GATES_PER_HASH_LOG2,
            'grover_iterations_log2': GROVER_ITERATIONS_LOG2,
            'challenge_bits_required': min_secure_bits(0),
            'credential_bits_required_64_targets': min_secure_bits(6),
            'tau': {str(b): theorem_c_budget(b)['tau'] for b in THEOREM_C_LOG2_PARTIES},
            'per_seat_budget_bits': {
                str(b): theorem_c_budget(b)['per_seat_budget_bits']
                for b in THEOREM_C_LOG2_PARTIES},
            'per_seat_budget_bits_32_grinding': {
                str(b): theorem_c_budget(b, grinding_bits=32)['per_seat_budget_bits']
                for b in THEOREM_C_LOG2_PARTIES},
            'per_seat_budget_bits_2^16_hash_chain_and_32_grinding': {
                str(b): theorem_c_budget(b, challenge_hash_steps_log2=16,
                                         grinding_bits=32)['per_seat_budget_bits']
                for b in THEOREM_C_LOG2_PARTIES},
            'per_seat_budget_bits_with_ggm_seed_term': {
                str(b): theorem_c_budget(b, ggm_seeds=True)['per_seat_budget_bits']
                for b in THEOREM_C_LOG2_PARTIES},
            'per_seat_budget_bits_if_2^18_gates_per_hash': {
                str(b): theorem_c_budget(b, attack_gates_log2=18)['per_seat_budget_bits']
                for b in THEOREM_C_LOG2_PARTIES},
        },
        'flags': {
            'hidden_signer_compact_qc_produced': False,
            'qualified_zero_knowledge_backend_available': False,
            'b0_public_signer_profile':
                'executable reference; security requires a category-5 signature of '
                'at most 757 bytes; OV-V (260), SNOVA_29_6_5 (454) and SNOVA_60_10_4 '
                '(576) are measured via liboqs 0.16.0; the signer bitmap is public',
        },
    }


# ===========================================================================
# Real-signature demonstration (only when pqcrypto is importable).
# ===========================================================================
def _demo_scheme(provider, domain, m0, m1, scheme_id, seats0, seats1):
    pks, sks = [], []
    for _ in range(N):
        pk, sk = provider.keygen()
        pks.append(pk)
        sks.append(sk)
    registry = RegistryB0(tuple(pks), scheme_id + provider.name.encode())
    cfg = cfg_b0(registry)
    frame0 = encode_b0(registry, provider, domain, m0, sks, seats0)
    frame1 = encode_b0(registry, provider, domain, m1, sks, seats1)
    record = {
        'name': provider.name,
        'nist_category': provider.category,
        'signature_bytes': provider.width,
        'public_key_bytes': len(pks[0]),
        'frame_bytes': len(frame0),
        'b0_frame_bytes_formula': b0_frame_bytes(provider.width),
        'fits_32KiB': b0_fits(provider.width),
    }
    if b0_fits(provider.width):
        verify_b0(frame0, registry, provider, cfg)
        verify_b0(frame1, registry, provider, cfg)
        findings = extract_b0(frame0, frame1, registry, provider, cfg)
        record['verified'] = True
        record['extracted_common_seats'] = [b.seat for b in findings]
        record['extracted_count'] = len(findings)
        record['blame_verified'] = all(
            verify_blame_b0(frame0, frame1, registry, provider, cfg, b.seat)
            for b in findings)
        offsets = getattr(provider, 'tamper_offsets', (provider.width // 2,))
        rejected = []
        for offset in offsets:
            tampered = bytearray(frame0)
            tampered[B0_FIXED_BYTES + offset] ^= 0x01           # inside the first signature
            try:
                verify_b0(bytes(tampered), registry, provider, cfg)
                rejected.append(False)
            except FrameError:
                rejected.append(True)
        record['tamper_offsets_in_first_signature'] = list(offsets)
        record['tampered_signature_rejected'] = all(rejected)
    else:
        record['verified'] = False
        try:
            verify_b0(frame0, registry, provider, cfg)
            record['oversize_rejected'] = False
        except FrameError as exc:
            record['oversize_rejected'] = True
            record['rejection'] = str(exc)
    if provider.category < 5:
        record['caveat'] = 'category %d: does NOT meet QPT-128' % provider.category
    elif not b0_fits(provider.width):
        record['caveat'] = 'category 5 but does NOT fit the 32 KiB frame'
    else:
        record['caveat'] = ('claimed category 5 and fits; QPT-128 via Theorem A rests on '
                            'this scheme\'s EUF-CMA; the signer bitmap is public')
    return record


def real_demo():
    domain = bytes(range(64))
    m0 = bytes(64)
    m1 = bytes(63) + b'\x11'
    scheme_id = b'CQ44/real-demo/'
    seats0 = list(range(QUORUM))
    seats1 = list(range(MIN_OVERLAP)) + list(range(QUORUM, N))
    providers = []
    loaded = try_load_real_providers()
    if loaded is not None:
        providers += [('pqcrypto', loaded['falcon_padded_512']),
                      ('pqcrypto', loaded['ml_dsa_87'])]
    oqs_loaded = try_load_oqs_providers()
    if oqs_loaded is not None:
        providers += [('liboqs', p) for p in oqs_loaded.values()]
    if not providers:
        print(json.dumps({'real_demo': 'unavailable',
                          'reason': 'neither pqcrypto nor an installed liboqs-python '
                                    'imports'}, indent=2))
        return 1
    out = {'real_demo': 'available', 'schemes': {}}
    oqs_module = sys.modules.get('oqs')
    if oqs_module is not None:
        try:
            out['liboqs_version'] = oqs_module.oqs_version()
            out['liboqs_python_version'] = oqs_module.oqs_python_version()
        except Exception:
            out['liboqs_version'] = 'unavailable'
    for library, provider in providers:
        record = _demo_scheme(provider, domain, m0, m1, scheme_id, seats0, seats1)
        record['library'] = library
        out['schemes'][library + ':' + provider.name] = record
    closing = sorted(r['name'] for r in out['schemes'].values()
                     if r['nist_category'] >= 5 and r['fits_32KiB'] and r.get('verified')
                     and r.get('extracted_count', 0) >= MIN_OVERLAP
                     and r.get('blame_verified') and r.get('tampered_signature_rejected'))
    out['category5_fitting_verified'] = closing
    out['summary'] = (
        'Among the locally available schemes, these claimed-category-5 schemes produced '
        'verified B0 frames of at most 32,768 bytes, with public extraction of at least '
        '22 seats and tamper rejection: %s. B0 publishes the signer bitmap, so it does '
        'not meet the hidden-signer requirement.' % (', '.join(closing) or 'none'))
    print(json.dumps(out, indent=2))
    return 0


# ===========================================================================
# Deterministic unittest suite (stdlib only).
# ===========================================================================
import random
import sys
import unittest

E = sys.modules[__name__]

_DOMAIN = bytes(range(64))
_DOMAIN2 = bytes(range(64, 128))


def _msg(value):
    return value.to_bytes(64, 'big')


def _b0_registry(provider, seed=0):
    rng = random.Random(seed)
    pks, sks = [], []
    for _ in range(N):
        # Deterministic keys keyed to the provider's own keygen counter.
        pk, sk = provider.keygen()
        pks.append(pk)
        sks.append(sk)
    del rng
    return RegistryB0(tuple(pks), b'CQ44/test-scheme'), sks


def _b1_setup(seed=0):
    rng = random.Random(seed)
    secrets = [rng.getrandbits(512).to_bytes(64, 'big') for _ in range(N)]
    keys = tuple(register_key_b1(x) for x in secrets)
    return RegistryB1(keys), secrets


class B0Tests(unittest.TestCase):
    def setUp(self):
        self.provider = SymbolicSignatures(width=128)
        self.registry, self.sks = _b0_registry(self.provider)
        self.cfg = cfg_b0(self.registry)
        self.m0, self.m1 = _msg(0), _msg((1 << 400) | 7)
        self.seats0 = list(range(QUORUM))
        self.seats1 = list(range(MIN_OVERLAP)) + list(range(QUORUM, N))
        self.frame0 = encode_b0(self.registry, self.provider, _DOMAIN, self.m0,
                                self.sks, self.seats0)
        self.frame1 = encode_b0(self.registry, self.provider, _DOMAIN, self.m1,
                                self.sks, self.seats1)

    def test_valid_encode_verify(self):
        v = verify_b0(self.frame0, self.registry, self.provider, self.cfg)
        self.assertEqual(len(v.seats), QUORUM)
        self.assertEqual(len(self.frame0), b0_frame_bytes(self.provider.width))

    def test_popcount_42_and_44_rejected(self):
        for seats in (list(range(42)), list(range(44))):
            payload_seats = sorted(seats)
            sigs = [self.provider.sign(self.sks[i],
                    vote_message_b0(self.cfg, _DOMAIN, self.m0, i)) for i in payload_seats]
            bitmap = 0
            for i in payload_seats:
                bitmap |= 1 << i
            payload = bitmap.to_bytes(8, 'big') + b''.join(sigs)
            frame = pack_header(SUITE_B0, self.cfg, _DOMAIN, self.m0,
                                self.provider.width, len(payload)) + payload
            with self.assertRaises(FrameError):
                verify_b0(frame, self.registry, self.provider, self.cfg)

    def test_wrong_seat_signature_rejected(self):
        # Swap the signatures for the two lowest seats -> both slots verify wrong.
        w = self.provider.width
        body = bytearray(self.frame0)
        base = HEADER_BYTES + 8
        s0 = body[base:base + w]
        s1 = body[base + w:base + 2 * w]
        body[base:base + w] = s1
        body[base + w:base + 2 * w] = s0
        with self.assertRaises(FrameError):
            verify_b0(bytes(body), self.registry, self.provider, self.cfg)

    def test_wrong_message_rejected(self):
        tampered = bytearray(self.frame0)
        tampered[144:208] = self.m1                    # header message field
        with self.assertRaises(FrameError):
            verify_b0(bytes(tampered), self.registry, self.provider, self.cfg)

    def test_wrong_domain_rejected(self):
        tampered = bytearray(self.frame0)
        tampered[80:144] = _DOMAIN2                    # header domain field
        with self.assertRaises(FrameError):
            verify_b0(bytes(tampered), self.registry, self.provider, self.cfg)

    def test_wrong_cfg_rejected(self):
        other = bytes((b ^ 0xFF) for b in self.cfg)
        with self.assertRaises(FrameError):
            verify_b0(self.frame0, self.registry, self.provider, other)
        tampered = bytearray(self.frame0)
        tampered[16:80] = other                        # header cfg field
        with self.assertRaises(FrameError):
            verify_b0(bytes(tampered), self.registry, self.provider, other)

    def test_truncated_and_trailing_rejected(self):
        with self.assertRaises(FrameError):
            verify_b0(self.frame0[:-1], self.registry, self.provider, self.cfg)
        with self.assertRaises(FrameError):
            verify_b0(self.frame0 + b'\x00', self.registry, self.provider, self.cfg)

    def test_width_mismatch_rejected(self):
        tampered = bytearray(self.frame0)
        struct.pack_into('>H', tampered, 206, self.provider.width + 1)   # width field
        with self.assertRaises(FrameError):
            verify_b0(bytes(tampered), self.registry, self.provider, self.cfg)

    def test_extraction_range_43_vs_22_63(self):
        findings = extract_b0(self.frame0, self.frame1, self.registry, self.provider, self.cfg)
        self.assertEqual([b.seat for b in findings], list(range(MIN_OVERLAP)))

    def test_all_overlaps_22_to_43(self):
        rng = random.Random(99)
        for overlap in range(MIN_OVERLAP, QUORUM + 1):
            perm = list(range(N))
            rng.shuffle(perm)
            left = perm[:QUORUM]
            right = perm[:overlap] + perm[QUORUM:2 * QUORUM - overlap]
            self.assertEqual(len(set(right)), QUORUM)
            f0 = encode_b0(self.registry, self.provider, _DOMAIN, _msg(1), self.sks, left)
            f1 = encode_b0(self.registry, self.provider, _DOMAIN, _msg(2), self.sks, right)
            findings = extract_b0(f0, f1, self.registry, self.provider, self.cfg)
            self.assertEqual([b.seat for b in findings], sorted(set(left) & set(right)))
            self.assertEqual(len(findings), overlap)

    def test_same_message_not_a_conflict(self):
        f1b = encode_b0(self.registry, self.provider, _DOMAIN, self.m0, self.sks, self.seats1)
        with self.assertRaises(ExtractionError):
            extract_b0(self.frame0, f1b, self.registry, self.provider, self.cfg)

    def test_different_domain_rejected_in_extract(self):
        f1b = encode_b0(self.registry, self.provider, _DOMAIN2, self.m1, self.sks, self.seats1)
        with self.assertRaises(ExtractionError):
            extract_b0(self.frame0, f1b, self.registry, self.provider, self.cfg)

    def test_verify_blame(self):
        for seat in range(MIN_OVERLAP):
            self.assertTrue(verify_blame_b0(self.frame0, self.frame1, self.registry,
                                            self.provider, self.cfg, seat))
        for seat in range(QUORUM, N):
            self.assertFalse(verify_blame_b0(self.frame0, self.frame1, self.registry,
                                             self.provider, self.cfg, seat))

    def test_honest_seat_framing_rejected(self):
        # Seat 30 is in frame0 but NOT in frame1; fabricate a slot for it in a
        # frame1 variant. It never signed m1, so verify rejects the frame.
        honest = 30
        self.assertNotIn(honest, self.seats1)
        seats = sorted(self.seats1[:-1] + [honest])
        sigs = []
        for i in seats:
            if i == honest:
                sigs.append((b'FAKE' + bytes(self.provider.width))[:self.provider.width])
            else:
                sigs.append(self.provider.sign(self.sks[i],
                            vote_message_b0(self.cfg, _DOMAIN, self.m1, i)))
        bitmap = 0
        for i in seats:
            bitmap |= 1 << i
        payload = bitmap.to_bytes(8, 'big') + b''.join(sigs)
        frame = pack_header(SUITE_B0, self.cfg, _DOMAIN, self.m1,
                            self.provider.width, len(payload)) + payload
        with self.assertRaises(FrameError):
            verify_b0(frame, self.registry, self.provider, self.cfg)

    def test_size_gate(self):
        self.assertEqual(B0_MAX_SIGNATURE_BYTES, 757)
        self.assertTrue(b0_fits(757))
        self.assertFalse(b0_fits(758))
        by_name = {e['name']: e for e in SIGNATURE_SIZE_TABLE}
        self.assertFalse(b0_fits(by_name['ML-DSA-87']['signature_bytes']))
        self.assertFalse(b0_fits(by_name['SLH-DSA-SHAKE-256s']['signature_bytes']))
        self.assertTrue(b0_fits(by_name['Falcon-padded-512']['signature_bytes']))
        self.assertEqual(by_name['Falcon-padded-512']['nist_category'], 1)
        for name in ('OV-V', 'SNOVA_29_6_5', 'SNOVA_60_10_4', 'OV-V||SNOVA_29_6_5',
                     'SQIsign-V'):
            self.assertTrue(b0_fits(by_name[name]['signature_bytes']))
            self.assertEqual(by_name[name]['nist_category'], 5)
        self.assertEqual(b0_frame_bytes(by_name['OV-V']['signature_bytes']), 11396)
        self.assertEqual(b0_frame_bytes(by_name['OV-V||SNOVA_29_6_5']['signature_bytes']),
                         30918)
        self.assertFalse(b0_fits(by_name['MAYO-5']['signature_bytes']))
        self.assertFalse(b0_fits(by_name['HAWK-1024']['signature_bytes']))
        self.assertFalse(b0_fits(by_name['Falcon-padded-1024']['signature_bytes']))

    def test_wrong_suite_rejected(self):
        tampered = bytearray(self.frame0)
        struct.pack_into('>H', tampered, 6, SUITE_B1)   # suite field
        with self.assertRaises(FrameError):
            verify_b0(bytes(tampered), self.registry, self.provider, self.cfg)

    def test_hybrid_and_combiner(self):
        hybrid = HybridSignatures(SymbolicSignatures(64), SymbolicSignatures(80))
        self.assertEqual(hybrid.width, 144)
        pks, sks = zip(*(hybrid.keygen() for _ in range(N)))
        registry = RegistryB0(tuple(pks), b'hybrid-test')
        cfg = cfg_b0(registry)
        right = list(range(MIN_OVERLAP)) + list(range(QUORUM, N))
        f0 = encode_b0(registry, hybrid, _DOMAIN, _msg(1), list(sks), list(range(QUORUM)))
        f1 = encode_b0(registry, hybrid, _DOMAIN, _msg(2), list(sks), right)
        self.assertEqual(len(f0), b0_frame_bytes(144))
        found = extract_b0(f0, f1, registry, hybrid, cfg)
        self.assertEqual([b.seat for b in found], list(range(MIN_OVERLAP)))
        for offset in (B0_FIXED_BYTES + 10, B0_FIXED_BYTES + 64 + 10):   # half a, half b
            bad = bytearray(f0)
            bad[offset] ^= 1
            with self.assertRaises(FrameError):
                verify_b0(bytes(bad), registry, hybrid, cfg)


class B1Tests(unittest.TestCase):
    def setUp(self):
        self.registry, self.secrets = _b1_setup()
        self.cfg = cfg_b1(self.registry)
        self.domain = _DOMAIN
        self.D = context_b1(self.cfg, self.domain)
        self.backend = StructureOnlyTestBackend()

    def _rows(self, seats, message):
        return [(i, self.secrets[i]) for i in seats], message

    def _frame(self, seats, message):
        rows = [(i, self.secrets[i]) for i in seats]
        return encode_b1(self.registry, self.domain, message, rows, self.backend)

    def _handles_rows(self, seats, message):
        built = []
        for i in seats:
            built.append((handle_b1(self.secrets[i], i, self.D, message), (i, self.secrets[i])))
        built.sort(key=lambda item: item[0][:64])
        return [h for h, _ in built], [r for _, r in built]

    def test_handle_input_is_135_bytes(self):
        absorb = b'CEQS/P1' + self.secrets[0] + self.D
        self.assertEqual(len(absorb), 135)
        self.assertEqual(len(b'CEQS/K1' + self.secrets[0]), 71)

    def test_registry_key_is_128_bytes(self):
        self.assertEqual(B1_REGISTRY_KEY_BYTES, 128)
        self.assertEqual(len(register_key_b1(self.secrets[0])), 128)
        self.assertTrue(all(len(k) == 128 for k in self.registry.keys))

    def test_relation_holds_for_honest_rows(self):
        seats = list(range(QUORUM))
        handles, rows = self._handles_rows(seats, _msg(5))
        self.assertTrue(check_relation(self.cfg, self.domain, _msg(5),
                                       handles, rows, self.registry.keys))

    def test_64_rotating_quorums(self):
        for start in range(N):
            seats = [(start + k) % N for k in range(QUORUM)]
            handles, rows = self._handles_rows(seats, _msg(start + 1))
            self.assertTrue(check_relation(self.cfg, self.domain, _msg(start + 1),
                                           handles, rows, self.registry.keys))

    def test_key_mismatch_rejected(self):
        seats = list(range(QUORUM))
        handles, rows = self._handles_rows(seats, _msg(5))
        bad = list(rows)
        # Replace one credential with an unregistered one at the same seat.
        seat0 = bad[0][0]
        bad[0] = (seat0, bytes((b ^ 0xFF) for b in bad[0][1]))
        with self.assertRaises(RelationError):
            check_relation(self.cfg, self.domain, _msg(5), handles, bad, self.registry.keys)

    def test_wrong_seat_rejected(self):
        seats = list(range(QUORUM))
        handles, rows = self._handles_rows(seats, _msg(5))
        bad = list(rows)
        seat0, x0 = bad[0]
        other = (seat0 + 1) % N
        bad[0] = (other, x0)                            # x0 no longer opens K[other]
        with self.assertRaises(RelationError):
            check_relation(self.cfg, self.domain, _msg(5), handles, bad, self.registry.keys)

    def test_wrong_message_rejected(self):
        seats = list(range(QUORUM))
        handles, rows = self._handles_rows(seats, _msg(5))
        with self.assertRaises(RelationError):
            check_relation(self.cfg, self.domain, _msg(6), handles, rows, self.registry.keys)

    def test_wrong_domain_rejected(self):
        seats = list(range(QUORUM))
        handles, rows = self._handles_rows(seats, _msg(5))
        with self.assertRaises(RelationError):
            check_relation(self.cfg, _DOMAIN2, _msg(5), handles, rows, self.registry.keys)

    def test_unsorted_and_duplicate_links_rejected(self):
        seats = list(range(QUORUM))
        handles, _ = self._handles_rows(seats, _msg(5))
        swapped = list(handles)
        swapped[0], swapped[1] = swapped[1], swapped[0]
        payload = b''.join(swapped) + self.backend.MARKER
        frame = pack_header(SUITE_B1, self.cfg, self.domain, _msg(5), HANDLE_BYTES,
                            len(payload)) + payload
        with self.assertRaises(FrameError):
            parse_b1(frame)
        dup = list(handles)
        dup[1] = dup[0]
        payload = b''.join(dup) + self.backend.MARKER
        frame = pack_header(SUITE_B1, self.cfg, self.domain, _msg(5), HANDLE_BYTES,
                            len(payload)) + payload
        with self.assertRaises(FrameError):
            parse_b1(frame)

    def test_distinctness_lemma_both_branches(self):
        seat = 3
        x_reg = self.secrets[seat]
        x_other = bytes((b ^ 0x5A) for b in x_reg)
        branch1 = distinctness_lemma(seat, x_reg, x_other, self.cfg, self.domain,
                                     _msg(5), self.registry.keys)
        self.assertEqual(branch1['branch'], 'credentials_differ')
        # Exactly the registered credential opens K[seat]; the other does not.
        self.assertTrue(branch1['k_check_a'])
        self.assertFalse(branch1['k_check_b'])
        branch2 = distinctness_lemma(seat, x_reg, x_reg, self.cfg, self.domain,
                                     _msg(5), self.registry.keys)
        self.assertEqual(branch2['branch'], 'identical_rows')
        self.assertTrue(branch2['links_equal'])
        self.assertTrue(branch2['strict_link_ordering_violated'])
        # And a duplicated seat is refused by the explicit distinctness check.
        seats = [seat, seat] + [i for i in range(N) if i != seat][:QUORUM - 2]
        handles, rows = self._handles_rows(list(range(QUORUM)), _msg(5))
        dup_rows = [(seat, x_reg)] + rows[1:]
        dup_rows[1] = (seat, self.secrets[rows[1][0]])
        with self.assertRaises(RelationError):
            check_relation(self.cfg, self.domain, _msg(5), handles, dup_rows,
                           self.registry.keys)

    def test_extraction_range_and_all_overlaps(self):
        f0 = self._frame(list(range(QUORUM)), _msg(0))
        f1 = self._frame(list(range(MIN_OVERLAP)) + list(range(QUORUM, N)), _msg(7))
        result = extract_b1(f0, f1, self.cfg)
        self.assertEqual([f['seat'] for f in result['findings']], list(range(MIN_OVERLAP)))
        self.assertEqual(result['status'], 'ALGEBRAIC_CANDIDATES_ONLY')
        rng = random.Random(4242)
        for overlap in range(MIN_OVERLAP, QUORUM + 1):
            perm = list(range(N))
            rng.shuffle(perm)
            left = perm[:QUORUM]
            right = perm[:overlap] + perm[QUORUM:2 * QUORUM - overlap]
            g0 = self._frame(left, _msg(rng.getrandbits(512)))
            g1 = self._frame(right, _msg(rng.getrandbits(512)))
            found = extract_b1(g0, g1, self.cfg)
            self.assertEqual([f['seat'] for f in found['findings']],
                             sorted(set(left) & set(right)))
            self.assertEqual(found['count'], overlap)

    def test_identity_table_keys_distinct_for_all_512_basis(self):
        for bit in range(512):
            table = identity_table(1 << bit)
            self.assertEqual(len(table), N)
            for kappa in range(1, N + 1):
                self.assertEqual(table[mul(1 << bit, kappa)], kappa - 1)

    def test_delta_zero_out_of_range_and_duplicate_rejected(self):
        with self.assertRaises(ExtractionError):
            identity_table(0)
        # Two full-overlap frames (seats 0..42, different messages). Because L
        # depends only on (x, D), the sorted handle order is identical position by
        # position across the two frames, so we can tamper Z by position.
        f0 = self._frame(list(range(QUORUM)), _msg(0))
        f1 = self._frame(list(range(QUORUM)), _msg(7))
        p0, p1 = parse_b1(f0), parse_b1(f1)
        delta = decode(p0.message) ^ decode(p1.message)
        z0 = [int.from_bytes(h[64:], 'big') for h in p0.handles]
        links = [h[:64] for h in p0.handles]

        def _frame1_with(position, new_z):
            handles = list(p1.handles)
            handles[position] = links[position] + new_z.to_bytes(64, 'big')
            payload = b''.join(handles) + p1.proof
            return pack_header(SUITE_B1, p1.cfg, p1.domain, p1.message, HANDLE_BYTES,
                               len(payload)) + payload

        # Out-of-range: force position 0 to decode to kappa 65 (>64) -> table miss.
        with self.assertRaises(ExtractionError):
            extract_b1(f0, _frame1_with(0, z0[0] ^ mul(delta, 65)), self.cfg)
        # Duplicate recovered seat: force position 1 to decode to position 0's seat.
        seat0 = identity_table(delta)[z0[0] ^ int.from_bytes(p1.handles[0][64:], 'big')]
        with self.assertRaises(ExtractionError):
            extract_b1(f0, _frame1_with(1, z0[1] ^ mul(delta, seat0 + 1)), self.cfg)

    def test_body_5712_and_proof_budget(self):
        frame = self._frame(list(range(QUORUM)), _msg(1))
        parsed = parse_b1(frame)
        self.assertEqual(B1_PREFIX_BYTES, 5712)
        self.assertEqual(len(frame) - len(parsed.proof), B1_PREFIX_BYTES)
        # A proof of exactly 27,056 bytes is accepted structurally...
        handles, _ = self._handles_rows(list(range(QUORUM)), _msg(1))
        big = b'\x00' * B1_PROOF_MAX
        payload = b''.join(handles) + big
        ok_frame = pack_header(SUITE_B1, self.cfg, self.domain, _msg(1), HANDLE_BYTES,
                               len(payload)) + payload
        self.assertEqual(len(ok_frame), MAX_FRAME_BYTES)
        parse_b1(ok_frame)
        # ...but one byte more overflows the 32,768-byte frame bound: parse_b1
        # rejects the oversize frame, and encode_b1 refuses an over-budget proof.
        over_payload = b''.join(handles) + big + b'\x00'
        over_frame = pack_header(SUITE_B1, self.cfg, self.domain, _msg(1), HANDLE_BYTES,
                                 len(over_payload)) + over_payload
        with self.assertRaises(FrameError):
            parse_b1(over_frame)

        class _OverBackend:
            qualified = False
            def prove(self, statement_bytes, rows):
                return b'\x00' * (B1_PROOF_MAX + 1)
            def verify(self, statement_bytes, proof):
                return False
        with self.assertRaises(FrameError):
            encode_b1(self.registry, self.domain, _msg(1),
                      [(i, self.secrets[i]) for i in range(QUORUM)], _OverBackend())

    def test_verify_b1_never_authorizes(self):
        frame = self._frame(list(range(QUORUM)), _msg(1))
        result = verify_b1(frame, self.registry, self.backend, self.cfg)
        self.assertEqual(result['status'], 'STRUCTURE_ONLY_NO_QUALIFIED_PROOF')
        self.assertIs(result['authorization_verified'], False)
        self.assertIs(result['qualified_backend'], False)
        self.assertTrue(result['proof_structurally_accepted'])

    def test_duplicate_registered_keys_rejected(self):
        keys = list(self.registry.keys)
        keys[1] = keys[0]
        with self.assertRaises(FrameError):
            cfg_b1(RegistryB1(tuple(keys)))


class CalculatorTests(unittest.TestCase):
    def test_mode_s_linear_lower_bound(self):
        self.assertEqual(KECCAK_F1600_BIT_AND_GATES, 38400)
        self.assertEqual(MODE_S_KECCAK_PERMUTATIONS, 86)
        self.assertEqual(mode_s_linear_lower_bound_bytes(), 412800)
        self.assertGreater(mode_s_linear_lower_bound_bytes(), B1_PROOF_MAX)

    def test_binius64_provenance_and_floor(self):
        self.assertEqual(8 * BINIUS64_AND_PER_KECCAK_PERMUTATION - 21, _KECCAK_SNAP_AND)
        self.assertEqual(15 * BINIUS64_AND_PER_KECCAK_PERMUTATION - 17, _SHA3_512_SNAP_AND)
        self.assertEqual(binius64_min_bytes(16), 109856)
        self.assertEqual(MODE_S_COMMITTED_WORDS_MIN, 51600)
        self.assertGreater(MODE_S_COMMITTED_WORDS_MIN, 1 << 15)
        self.assertGreater(binius64_min_bytes(_ceil_log2(MODE_S_COMMITTED_WORDS_MIN)),
                           B1_PROOF_MAX)

    def test_per_seat_budget(self):
        self.assertEqual(per_seat_witness_bit_budget(0), 5033)

    def test_grover_threshold_exact(self):
        import math
        from fractions import Fraction
        y = Fraction(31, 50)
        self.assertGreaterEqual((y - y ** 3 / 6) ** 2, Fraction(1, 3))
        self.assertEqual(GROVER_ITERATIONS_LOG2, 104)
        self.assertTrue(grover_reaches_one_third(211))
        self.assertFalse(grover_reaches_one_third(212))
        self.assertEqual(min_secure_bits(0), 212)
        self.assertEqual(min_secure_bits(6), 218)
        self.assertEqual(min_secure_bits(0, 110), 224)
        self.assertEqual(min_secure_bits(6, 110), 230)
        # Small gaps: k = 0 suffices for p >= 1/2, k = 1 for 1/16 <= p <= 1/4.
        self.assertTrue(grover_reaches_one_third(1, 0, 0))
        self.assertFalse(grover_reaches_one_third(4, 0, 0))
        self.assertTrue(grover_reaches_one_third(4, 0, 1))
        for p in (1 / 16, 1 / 8, 1 / 4):
            self.assertGreater(math.sin(3 * math.asin(math.sqrt(p))) ** 2, 0.47)
        # For p <= 1/32 the step 2*sqrt(p) is below the 19/50 landing window.
        self.assertLess(2 * math.sqrt(1 / 32), 19 / 50)

    def test_theorem_c_wire_budget(self):
        self.assertEqual(theorem_c_budget(16),
                         {'tau': 14, 'challenge_bits_required': 212, 'credential_bits': 218,
                          'per_seat_budget_bits': 359, 'max_wires_per_seat': 141})
        self.assertEqual(theorem_c_budget(48)['per_seat_budget_bits'], 1006)
        self.assertEqual(theorem_c_budget(48, grinding_bits=32)['tau'], 4)
        self.assertEqual(theorem_c_budget(48, grinding_bits=32)['per_seat_budget_bits'], 1258)
        self.assertEqual(theorem_c_budget(16, challenge_hash_steps_log2=16)['tau'], 12)
        self.assertEqual(
            theorem_c_budget(16, challenge_hash_steps_log2=16)['per_seat_budget_bits'], 419)
        self.assertEqual(theorem_c_budget(16, ggm_seeds=True)['per_seat_budget_bits'], 280)
        self.assertEqual(theorem_c_budget(48, ggm_seeds=True)['per_seat_budget_bits'], 770)
        self.assertEqual(theorem_c_budget(8)['max_wires_per_seat'], -1)
        self.assertEqual(max_wires_per_seat(16), theorem_c_budget(16))
        self.assertEqual(witness_committing_floor(16, 0, grinding_bits=256)['tau'], 1)
        # The cheapest published per-seat instantiation (2,816 bits) exceeds every
        # budget, even with 32 grinding bits and a 2^16-step challenge chain.
        for b in THEOREM_C_LOG2_PARTIES:
            best = theorem_c_budget(b, challenge_hash_steps_log2=16, grinding_bits=32)
            self.assertLess(best['per_seat_budget_bits'], 2816)

    def test_report_flags(self):
        report = build_report()
        flags = report['flags']
        self.assertIs(flags['hidden_signer_compact_qc_produced'], False)
        self.assertIs(flags['qualified_zero_knowledge_backend_available'], False)
        self.assertEqual(flags['b0_public_signer_profile'],
                         'executable reference; security requires a category-5 signature of '
                         'at most 757 bytes; OV-V (260), SNOVA_29_6_5 (454) and SNOVA_60_10_4 '
                         '(576) are measured via liboqs 0.16.0; the signer bitmap is public')
        self.assertEqual(report['theorem_c_witness_committing']['challenge_bits_required'], 212)


# ===========================================================================
# CLI.
# ===========================================================================
def _run_self_test():
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (B0Tests, B1Tests, CalculatorTests):
        suite.addTests(loader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='CE-QS sidecar-free certificate profiles B0/B1 (v1.44). '
                    'Executable reference; no compact hidden-signer QC is produced.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--self-test', action='store_true',
                       help='Run the deterministic unittest suite (verbosity 2).')
    group.add_argument('--explain', action='store_true',
                       help='Print the module docstring.')
    group.add_argument('--report', action='store_true',
                       help='Print a JSON summary of constants, gates and lower bounds.')
    group.add_argument('--real-demo', action='store_true',
                       help='Real B0 frames with pqcrypto and/or liboqs-python '
                            '(the latter only when OQS_INSTALL_PATH names an installed '
                            'liboqs).')
    args = parser.parse_args(argv)
    if args.explain:
        print(__doc__)
        return 0
    if args.report:
        print(json.dumps(build_report(), indent=2))
        return 0
    if args.real_demo:
        return real_demo()
    return _run_self_test()


if __name__ == '__main__':
    raise SystemExit(main())
