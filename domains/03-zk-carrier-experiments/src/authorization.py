#!/usr/bin/env python3
"""CEQS29 component specification and ordinary witness checker, NOT a ZK prover.

Experimental composition of real ML-KEM-1024 / ML-DSA-87. The registry and
transport keys are assumed authentically installed. No complete QC is produced.
"""
from pathlib import Path
import hashlib
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
from pqcrypto.kem import ml_kem_1024 as kem
from pqcrypto.sign import ml_dsa_87 as dsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

N, QUORUM = 64, 43
SUITE = b'CEQS29-M87-K1024'  # Fixed 16-byte contents-contract identifier.
assert len(SUITE) == 16
FIELD_POLY = (1 << 512) | 0x125
HEADER_BYTES = 208
BODY_BYTES = HEADER_BYTES + QUORUM * 128
TRANSPORT_MAGIC = b'CEQ29TR1'
TRANSPORT_HEADER = 8 + 2 + 32 + 64 + 64
WIRE_BYTES = TRANSPORT_HEADER + kem.CIPHERTEXT_SIZE + 12 + dsa.SIGNATURE_SIZE + 16 + dsa.SIGNATURE_SIZE


def H(*parts):
    return hashlib.shake_256(b''.join(len(p).to_bytes(8, 'big') + p for p in parts)).digest(64)


def mul(x, y):
    out = 0
    while y:
        if y & 1:
            out ^= x
        x <<= 1
        if x >> 512:
            x ^= FIELD_POLY
        y >>= 1
    return out


def inv(x):
    if not 0 < x < 1 << 512:
        raise ValueError('nonzero canonical element required')
    u, v, a, b = x, FIELD_POLY, 1, 0
    while u != 1:
        j = u.bit_length() - v.bit_length()
        if j < 0:
            u, v, a, b = v, u, b, a
            j = -j
        u ^= v << j
        a ^= b << j
    while a.bit_length() > 512:
        a ^= FIELD_POLY << (a.bit_length() - 513)
    return a


def trace_key(seed):
    if len(seed) != 48:
        raise ValueError('trace seed width')
    return H(b'CEQS29/trace-key', seed)


def config_id(registry):
    if len(registry) != N:
        raise ValueError('64 seats required')
    for name, width in [('trace', 64), ('vote', dsa.PUBLIC_KEY_SIZE), ('kem', kem.PUBLIC_KEY_SIZE)]:
        values = [row[name] for row in registry]
        if any(len(x) != width for x in values) or len(set(values)) != N:
            raise ValueError('registry width or duplicate key')
    return H(b'CEQS29/config', SUITE, *(row[k] for row in registry for k in ('trace', 'vote', 'kem')))


def handle(seat, seed, cfg, domain, message):
    if type(seat) is not int or not 0 <= seat < N:
        raise ValueError('seat')
    if len(seed) != 48 or any(len(x) != 64 for x in (cfg, domain, message)):
        raise ValueError('handle input width')
    # Both outputs depend on context but deliberately not message or session.
    pair = hashlib.shake_256(b'CEQS29/pair' + seed + H(b'CEQS29/domain', cfg, domain)).digest(128)
    z = int.from_bytes(pair[64:], 'big') ^ mul(int.from_bytes(message, 'big'), seat + 1)
    return pair[:64] + z.to_bytes(64, 'big')


def parse_body(body):
    if not isinstance(body, bytes) or len(body) != BODY_BYTES or body[:16] != SUITE:
        raise ValueError('body framing')
    cfg, domain, message = body[16:80], body[80:144], body[144:208]
    handles = [body[p:p+128] for p in range(208, len(body), 128)]
    if any(a[:64] >= b[:64] for a, b in zip(handles, handles[1:])):
        raise ValueError('noncanonical handle order or duplicate link')
    return cfg, domain, message, handles


def make_body(registry, domain, message, seats, seeds):
    cfg = config_id(registry)
    if len(seats) != QUORUM or len(set(seats)) != QUORUM:
        raise ValueError('43 distinct seats required')
    entries = sorted((handle(i, seeds[i], cfg, domain, message), i) for i in seats)
    body = SUITE + cfg + domain + message + b''.join(x for x, _ in entries)
    parse_body(body)
    return body, [i for _, i in entries]


def approval_message(body, seat, own_handle):
    parse_body(body)
    if type(seat) is not int or not 0 <= seat < N or len(own_handle) != 128:
        raise ValueError('approval shape')
    # Pure ML-DSA, external context empty. Application domain is in the message.
    return b'CEQS29/VOTE/v1' + H(b'CEQS29/body', body) + bytes([seat]) + own_handle


def valid_signature(pk, msg, signature):
    return len(signature) == dsa.SIGNATURE_SIZE and dsa.verify(pk, msg, signature)


def check_public_approvals(registry, body, approvals):
    """Transparent audit ONLY: exposes seats and does not prove trace openings."""
    try:
        cfg, _, _, hs = parse_body(body)
        if cfg != config_id(registry) or len(approvals) != QUORUM:
            return False
        if len({i for i, _ in approvals}) != QUORUM:
            return False
        for (i, signature), h in zip(approvals, hs):
            if type(i) is not int or not 0 <= i < N:
                return False
            if not valid_signature(registry[i]['vote'], approval_message(body, i, h), signature):
                return False
        return True
    except (ValueError, TypeError, KeyError, IndexError):
        return False


def check_witness(registry, body, witness):
    """Executable R29(x,w); sees all witnesses. No privacy or proof output."""
    try:
        if len(witness) != QUORUM:
            return False
        approvals = [(i, sig) for i, seed, sig in witness]
        if not check_public_approvals(registry, body, approvals):
            return False
        cfg, domain, message, hs = parse_body(body)
        return all(trace_key(seed) == registry[i]['trace'] and
                   handle(i, seed, cfg, domain, message) == h
                   for (i, seed, _), h in zip(witness, hs))
    except (ValueError, TypeError, KeyError, IndexError):
        return False


def extract_algebra(body0, body1):
    """Algebra only. A production entry must FIRST verify TWO complete QCs."""
    c, d, m, hs = parse_body(body0)
    c1, d1, m1, hs1 = parse_body(body1)
    if (c, d) != (c1, d1) or m == m1:
        raise ValueError('not a conflicting context')
    divisor = inv(int.from_bytes(m, 'big') ^ int.from_bytes(m1, 'big'))
    other = {h[:64]: int.from_bytes(h[64:], 'big') for h in hs1}
    result = []
    for h in hs:
        if h[:64] in other:
            seat = mul(int.from_bytes(h[64:], 'big') ^ other[h[:64]], divisor)
            if not 1 <= seat <= N:
                raise ValueError('bad extracted identity')
            result.append(seat - 1)
    return sorted(result)


def transport_header(registry, body, sender, recipient, session):
    if len(session) != 32 or not 0 <= sender < N or not 0 <= recipient < N:
        raise ValueError('transport header')
    return (TRANSPORT_MAGIC + bytes([sender, recipient]) + session +
            H(b'CEQS29/body', body) + H(b'CEQS29/recipient', registry[recipient]['kem']))


def transport_key(shared, header, kem_ct):
    return HKDF(algorithm=hashes.SHA512(), length=32,
                salt=H(b'CEQS29/channel-salt', header, kem_ct),
                info=b'CEQS29/approval-transport/AES256GCM').derive(shared)


def seal(registry, body, sender, recipient, session, approval, sender_sk):
    """Transport only an approval, never a trace seed or ML-DSA private key."""
    if len(approval) != dsa.SIGNATURE_SIZE:
        raise ValueError('approval width')
    header = transport_header(registry, body, sender, recipient, session)
    kem_ct, shared = kem.encrypt(registry[recipient]['kem'])
    nonce = secrets.token_bytes(12)  # Fresh independent KEM key for each envelope.
    ct = AESGCM(transport_key(shared, header, kem_ct)).encrypt(nonce, approval, header + kem_ct)
    unsigned = header + kem_ct + nonce + ct
    sig = dsa.sign(sender_sk, b'CEQS29/TRANSPORT/v1' + unsigned)
    wire = unsigned + sig
    assert len(wire) == WIRE_BYTES
    return wire


def receive(registry, body, recipient, session, recipient_sk, wire, seen):
    """Returns (seat, approval); recipient learns the sender. Single-session cache."""
    if len(wire) != WIRE_BYTES or wire[:8] != TRANSPORT_MAGIC:
        raise ValueError('wire framing')
    sender = wire[8]
    header = transport_header(registry, body, sender, recipient, session)
    if wire[:TRANSPORT_HEADER] != header:
        raise ValueError('wire context')
    token = (session, H(b'CEQS29/body', body), recipient, sender)
    if token in seen:
        raise ValueError('duplicate sender in session')
    unsigned, outer_sig = wire[:-dsa.SIGNATURE_SIZE], wire[-dsa.SIGNATURE_SIZE:]
    if not valid_signature(registry[sender]['vote'], b'CEQS29/TRANSPORT/v1' + unsigned, outer_sig):
        raise ValueError('transport signature')
    start = TRANSPORT_HEADER
    kem_ct = wire[start:start+kem.CIPHERTEXT_SIZE]
    start += kem.CIPHERTEXT_SIZE
    nonce, ct = unsigned[start:start+12], unsigned[start+12:]
    shared = kem.decrypt(recipient_sk, kem_ct)  # Implicit rejection: still returns a key.
    approval = AESGCM(transport_key(shared, header, kem_ct)).decrypt(nonce, ct, header + kem_ct)
    # The sender may have sent an invalid inner approval; outer authentication is insufficient.
    hs = parse_body(body)[3]
    matches = [h for h in hs if valid_signature(registry[sender]['vote'],
               approval_message(body, sender, h), approval)]
    if len(matches) != 1:
        raise ValueError('inner approval does not bind exactly one handle')
    seen.add(token)  # Invalid packets do not reserve an origin.
    return sender, approval
