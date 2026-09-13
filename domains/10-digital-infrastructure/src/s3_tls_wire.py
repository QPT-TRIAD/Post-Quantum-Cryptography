#!/usr/bin/env python3
r"""AUDIT v2.1 of pq_infra_s3_tls_pki_v2.0.py: exact bytes on the wire, KEMTLS attack games, CPU separation.

Part A replaces the model's round-number overheads (CH_BASE=260, CERT_TBS=350, RECORD_OVERHEAD=60, FINISHED=40, ...) with
a real RFC 8446 handshake encoder, a DER X.509 template, the draft-ietf-plants-merkle-tree-certs assertion+proof encoding,
TLS record framing, QUIC (RFC 9000) packet/datagram framing and TCP segmentation: every ledger number is len() of
constructed bytes (choices not fixed by the RFCs: ASSUMPTIONS).  Part B runs KEMTLS (Schwabe-Stebila-Wiggers, CCS 2020) on
an ideal-KEM toy with the Part A encoders as transcript, then eight network-adversary games plus a positive control.
Part C lists server CPU from verified literature only; B (bytes) and T (CPU) are separate axes.  Tests S3-001..S3-020
assert the MEASURED behaviour; contradictions with the model are listed under "model_discrepancies" in `--report`.
"""
import argparse, hashlib, hmac, importlib.util, json, os, random, secrets, sys, unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('s3', os.path.join(_HERE, 's3_tls_pki.py'))
s3 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(s3)
SIG, KEM, MTCBatch, H, CONFIGS = s3.SIG, s3.KEM, s3.MTCBatch, s3.H, s3.CONFIGS

ASSUMPTIONS = {
    'cipher_suite': 'TLS_AES_256_GCM_SHA384 (Finished 48 B) when the KEM is Category 5, else TLS_AES_128_GCM_SHA256 (32 B)',
    'client_hello': 'SNI www.example.com, 3 suites, 5 groups, 10 sig schemes, 1 hybrid key share (X25519||ML-KEM), 32-B legacy_session_id (compat), '
                    'one 32-B trust anchor id (draft-ietf-tls-trust-anchor-ids)',
    'x509': 'DER v3: 20-B serial, 9-B algorithm OIDs (NIST arc; assumed for schemes without one), C/O/CN names, UTCTime, SKI/AKI 20 B, KU, EKU, SAN, '
            'OCSP AIA; chain = leaf + 1 intermediate; ECDSA sizes taken raw (64 B)',
    'mtc': 'Assertion{subject_type u16, TLSSubjectInfo{scheme u16, public_key<1..2^16-1>}, Claim{dns names}} + Proof{trust_anchor<1..2^8-1> (12 B), '
           'proof_data<0..2^16-1> = index u64, landmark u32, path<0..2^16-1>}; CertificateEntry carries a trust_anchors ext with the batch id',
    'records': 'ServerHello plaintext record, 6-B compat CCS, one AEAD record (5+1+16 B) per <=2^14-B fragment of each later message',
    'quic': 'Initial: 30-B long header (DCID/SCID 8/8, empty token, 2-B length, 4-B pkt no) + 16-B tag; Handshake: 29 + 16; 5-B ACK frame in '
            'the first server Initial; datagrams holding an Initial are capped and padded to 1,200 B, later ones 1,252 (v4) / 1,232 (v6)',
    'kemtls': "server first flight = SH, EE, Certificate; NO CertificateVerify and NO Finished (server Finished follows the "
              "client's KEM ciphertext); client 2nd flight carries ClientKemCiphertext + Finished",
}

# ------------------------------------------------------------------ Part A: TLS 1.3 encoder (RFC 8446 §4) ----
def u8(v): return v.to_bytes(1, 'big')
def u16(v): return v.to_bytes(2, 'big')
def vec(body, n):
    if len(body) >= 1 << (8 * n): raise ValueError(f'vector of {len(body)} B exceeds opaque<0..2^{8 * n}-1>')
    return len(body).to_bytes(n, 'big') + body
def ext(t, body): return u16(t) + vec(body, 2)
def hs(t, body): return u8(t) + vec(body, 3)

EXT_SNI, EXT_GROUPS, EXT_SIGALGS, EXT_ALPN, EXT_SCT, EXT_VERSIONS, EXT_PSK_MODES, EXT_KEY_SHARE = 0, 10, 13, 16, 18, 43, 45, 51
EXT_TRUST_ANCHORS = 0xCA34                     # draft-ietf-tls-trust-anchor-ids early codepoint
HS_CH, HS_SH, HS_EE, HS_CERT, HS_CV, HS_FIN, HS_KEMCT = 1, 2, 8, 11, 15, 20, 0xF0   # 0xF0: KEMTLS ClientKemCiphertext (no IANA type)
GROUP_CAT5, GROUP_CAT3, GROUPS = 0x11EE, 0x11EC, (0x11EE, 0x11EC, 0x001D, 0x0017, 0x0018)   # X25519MLKEM1024 (private), X25519MLKEM768
DEFAULT_SANS = ('www.example.com', 'example.com')


def client_hello(key_share, host='www.example.com', groups=GROUPS, ks_group=GROUP_CAT5, ta_ids=(bytes(32),), rnd=bytes(32)):
    exts = (ext(EXT_SNI, vec(u8(0) + vec(host.encode(), 2), 2)) + ext(EXT_GROUPS, vec(b''.join(u16(g) for g in groups), 2))
            + ext(EXT_SIGALGS, vec(b'\x08\x04' * 10, 2)) + ext(EXT_VERSIONS, vec(u16(0x0304), 1)) + ext(EXT_PSK_MODES, vec(u8(1), 1))
            + ext(EXT_KEY_SHARE, vec(u16(ks_group) + vec(key_share, 2), 2)) + ext(EXT_TRUST_ANCHORS, vec(b''.join(vec(t, 1) for t in ta_ids), 2)))
    return hs(HS_CH, u16(0x0303) + rnd + vec(bytes(32), 1) + vec(b'\x13\x02\x13\x01\x13\x03', 2) + vec(b'\x00', 1) + vec(exts, 2))


def server_hello(ct, group=GROUP_CAT5, rnd=bytes(32), suite=0x1302):
    exts = ext(EXT_VERSIONS, u16(0x0304)) + ext(EXT_KEY_SHARE, u16(group) + vec(ct, 2))
    return hs(HS_SH, u16(0x0303) + rnd + vec(bytes(32), 1) + u16(suite) + u8(0) + vec(exts, 2))


def encrypted_extensions(alpn=b'h2'): return hs(HS_EE, vec(ext(EXT_SNI, b'') + ext(EXT_ALPN, vec(vec(alpn, 1), 2)), 2))
def certificate_verify(sig, scheme=0x0905): return hs(HS_CV, u16(scheme) + vec(sig, 2))
def finished(mac): return hs(HS_FIN, mac)
def kem_ciphertext(ct): return hs(HS_KEMCT, vec(ct, 2))
def certificate_msg(entries): return hs(HS_CERT, vec(b'', 1) + vec(b''.join(vec(c, 3) + vec(e, 2) for c, e in entries), 3))


# DER / X.509 template -------------------------------------------------------------------------------------------
SEQ, SET, INT, BITS, OCT, OID, UTF8, PRINT, UTC, BOOL = 0x30, 0x31, 0x02, 0x03, 0x04, 0x06, 0x0C, 0x13, 0x17, 0x01
OIDS = {'CN': b'\x55\x04\x03', 'O': b'\x55\x04\x0a', 'C': b'\x55\x04\x06', 'SAN': b'\x55\x1d\x11', 'KU': b'\x55\x1d\x0f',
        'EKU': b'\x55\x1d\x25', 'BC': b'\x55\x1d\x13', 'SKI': b'\x55\x1d\x0e', 'AKI': b'\x55\x1d\x23', 'AIA': b'\x2b\x06\x01\x05\x05\x07\x01\x01',
        'serverAuth': b'\x2b\x06\x01\x05\x05\x07\x03\x01', 'ocsp': b'\x2b\x06\x01\x05\x05\x07\x30\x01'}
ALG_OID_LEN = 9


def der(tag, body):
    n = len(body)
    L = u8(n) if n < 0x80 else u8(0x80 | ((n.bit_length() + 7) // 8)) + n.to_bytes((n.bit_length() + 7) // 8, 'big')
    return u8(tag) + L + body


def der_walk(b):
    """Structural DER check: returns element count, recursing into constructed tags; raises on overrun."""
    i, n = 0, 0
    while i < len(b):
        tag, L = b[i], b[i + 1]; i += 2
        if L & 0x80: k = L & 0x7F; L = int.from_bytes(b[i:i + k], 'big'); i += k
        if i + L > len(b): raise ValueError('DER overrun')
        if tag & 0x20: der_walk(b[i:i + L])
        i += L; n += 1
    return n


def alg_id(): return der(SEQ, der(OID, bytes(ALG_OID_LEN)))
def rdn(k, v, tag=UTF8): return der(SET, der(SEQ, der(OID, OIDS[k]) + der(tag, v.encode())))
def dn(cn, o='', c='US'): return der(SEQ, (rdn('C', c, PRINT) if c else b'') + (rdn('O', o) if o else b'') + rdn('CN', cn))
def extn(k, value, critical=False): return der(SEQ, der(OID, OIDS[k]) + (der(BOOL, b'\xff') if critical else b'') + der(OCT, value))


def x509_cert(pk, sig, subject_cn='www.example.com', sans=DEFAULT_SANS, issuer_cn='Example PQ CA 1', issuer_o='Example Trust Services',
              subject_o='', ca=False, serial_len=20, ocsp_url='http://ocsp.example.com'):
    exts = [extn('SKI', der(OCT, bytes(20))), extn('AKI', der(SEQ, der(0x80, bytes(20)))), extn('KU', der(BITS, b'\x05\xa0'), True)]
    if ca: exts.append(extn('BC', der(SEQ, der(BOOL, b'\xff') + der(INT, b'\x00')), True))
    else:
        exts += [extn('EKU', der(SEQ, der(OID, OIDS['serverAuth']))), extn('SAN', der(SEQ, b''.join(der(0x82, s.encode()) for s in sans)))]
        if ocsp_url: exts.append(extn('AIA', der(SEQ, der(SEQ, der(OID, OIDS['ocsp']) + der(0x86, ocsp_url.encode())))))
    tbs = der(SEQ, der(0xA0, der(INT, b'\x02')) + der(INT, b'\x01' + bytes(serial_len - 1)) + alg_id() + dn(issuer_cn, issuer_o)
              + der(SEQ, der(UTC, b'260911000000Z') * 2) + dn(subject_cn, subject_o) + der(SEQ, alg_id() + der(BITS, b'\x00' + pk))
              + der(0xA3, der(SEQ, b''.join(exts))))
    return der(SEQ, tbs + alg_id() + der(BITS, b'\x00' + sig))


# MTC (draft-ietf-plants-merkle-tree-certs) -------------------------------------------------------------------------
def assertion_bytes(a):
    dns = vec(b''.join(vec(n.encode(), 1) for n in a['dns']), 2)
    return u16(0) + vec(u16(a['scheme']) + vec(a['pk'], 2), 2) + vec(u16(0) + vec(dns, 2), 2)


def proof_bytes(p):
    data = p['index'].to_bytes(8, 'big') + p.get('landmark', 0).to_bytes(4, 'big') + vec(b''.join(p['path']), 2)
    return vec(p['batch_id'], 1) + vec(data, 2)


def certificate_mtc(a, p): return certificate_msg([(assertion_bytes(a) + proof_bytes(p), ext(EXT_TRUST_ANCHORS, vec(p['batch_id'], 1)))])


def cert_message(cfg, sans=DEFAULT_SANS, subject_cn='www.example.com', issuer_cn='Example PQ CA 1', subject_o='', issuer_o='Example Trust Services',
                 serial_len=20, n_inter=1, scts=None, ocsp_url='http://ocsp.example.com', depth=None):
    auth = cfg['server_auth']
    leaf_pk = bytes(KEM[auth][0] if auth in KEM else SIG[auth][0])
    if cfg['pki'] == 'x509':
        cpk, csig = SIG[cfg['chain_sig']][:2]; n_sct = cfg['scts'] if scts is None else scts
        sct = u8(0) + bytes(40) + vec(b'', 2) + b'\x08\x04' + vec(bytes(csig), 2)        # RFC 6962 §3.2 SignedCertificateTimestamp
        sct_ext = ext(EXT_SCT, vec(b''.join(vec(sct, 2) for _ in range(n_sct)), 2)) if n_sct else b''
        leaf = x509_cert(leaf_pk, bytes(csig), subject_cn, sans, issuer_cn, issuer_o, subject_o, False, serial_len, ocsp_url)
        inter = x509_cert(bytes(cpk), bytes(csig), issuer_cn, (), 'Example Root PQ CA', issuer_o, issuer_o, True, serial_len, '')
        return certificate_msg([(leaf, sct_ext)] + [(inter, b'')] * n_inter)
    a = {'scheme': 0, 'pk': leaf_pk, 'dns': list(sans)}
    p = {'batch_id': bytes(12), 'index': 0, 'path': [bytes(32)] * (cfg['batch_log2'] if depth is None else depth)}
    return certificate_mtc(a, p)


def flight_exact(cfg, **cert_kw):
    """Server first flight as (name, bytes) handshake messages, each with its 4-B header."""
    pk, ct, kcat = s3.kem_bytes(*cfg['kems']); hlen = 48 if kcat >= 5 else 32
    auth = cfg['server_auth']
    msgs = [('ServerHello', server_hello(bytes(ct), suite=0x1302 if hlen == 48 else 0x1301)), ('EncryptedExtensions', encrypted_extensions()),
            ('Certificate', cert_message(cfg, **cert_kw))]
    if auth in SIG: msgs += [('CertificateVerify', certificate_verify(bytes(SIG[auth][1]))), ('Finished', finished(bytes(hlen)))]
    return msgs


# Record / QUIC / TCP framing -----------------------------------------------------------------------------------------
REC_HDR, AEAD_TAG, MAX_PLAINTEXT, MSS, INITCWND = 5, 16, 1 << 14, 1460, 10
QUIC_INITIAL_HDR, QUIC_HS_HDR, QUIC_TAG, ACK_FRAME, UDP, IPV4, IPV6 = 30, 29, 16, 5, 8, 20, 40
DGRAM_INITIAL, DGRAM_V4, DGRAM_V6, AMP = 1200, 1252, 1232, 3


def tls_records(msgs):
    recs = [REC_HDR + len(msgs[0][1]), 6]                    # plaintext ServerHello record + compat ChangeCipherSpec
    for _, m in msgs[1:]:
        recs += [REC_HDR + 1 + AEAD_TAG + len(m[i:i + MAX_PLAINTEXT]) for i in range(0, len(m), MAX_PLAINTEXT)]
    return recs


def vl(v): return 1 if v < 64 else 2 if v < 16384 else 4 if v < 1 << 30 else 8


def _fit(space, off, remaining):
    """Largest CRYPTO chunk c <= remaining with 1 + varint(off) + varint(c) + c <= space."""
    c = max(0, min(remaining, space - 1 - vl(off) - vl(min(remaining, space))))
    while c < remaining and 1 + vl(off) + vl(c + 1) + c + 1 <= space: c += 1
    return c


def quic_client_datagrams(ch_len):
    off, n = 0, 0
    while off < ch_len: off += _fit(DGRAM_INITIAL - QUIC_INITIAL_HDR - QUIC_TAG, off, ch_len - off); n += 1
    return n


def quic_server_datagrams(msgs, ipv6=False):
    """Greedy split: ServerHello in Initial packets, the rest in Handshake packets, coalesced; returns UDP payload sizes."""
    init, hsd, oi, oh, out, first = len(msgs[0][1]), sum(len(m) for _, m in msgs[1:]), 0, 0, [], True
    while oi < init or oh < hsd:
        has_init = oi < init; cap = DGRAM_INITIAL if has_init else (DGRAM_V6 if ipv6 else DGRAM_V4); used = 0
        if has_init:
            fixed = QUIC_INITIAL_HDR + QUIC_TAG + (ACK_FRAME if first else 0)
            c = _fit(cap - fixed, oi, init - oi); used += fixed + 1 + vl(oi) + vl(c) + c; oi += c
        if oh < hsd:
            c = _fit(cap - used - QUIC_HS_HDR - QUIC_TAG, oh, hsd - oh)
            if c > 0: used += QUIC_HS_HDR + QUIC_TAG + 1 + vl(oh) + vl(c) + c; oh += c
        out.append(max(used, DGRAM_INITIAL) if has_init else used); first = False   # RFC 9000 §14.1: server pads Initial datagrams
    return out


def audit_row(cfg, model_row, **cert_kw):
    ch = client_hello(bytes(s3.kem_bytes(*cfg['kems'])[0]))
    n_cli = quic_client_datagrams(len(ch)); budget = AMP * DGRAM_INITIAL * n_cli
    row = {'config': cfg['name'], 'client_hello': len(ch), 'client_initial_datagrams': n_cli, 'quic_budget': budget, 'model_server_flight': model_row['server_flight']}
    try: msgs = flight_exact(cfg, **cert_kw)
    except ValueError as e: row.update(encodable=False, why=str(e), quic_fits_3x=False, tcp_fits_initcwnd=False); return row
    recs, d4, d6 = tls_records(msgs), quic_server_datagrams(msgs), quic_server_datagrams(msgs, True)
    hsb, tcp = sum(len(m) for _, m in msgs), sum(recs)
    row.update(encodable=True, handshake_bytes=hsb, messages={n: len(m) for n, m in msgs}, records=len(recs), tcp_bytes=tcp,
               tcp_segments=-(-tcp // MSS), tcp_fits_initcwnd=tcp <= INITCWND * MSS, quic_datagrams=len(d4), quic_datagrams_v6=len(d6), quic_udp_bytes=sum(d4),
               wire_ipv4=sum(d4) + (UDP + IPV4) * len(d4), wire_ipv6=sum(d6) + (UDP + IPV6) * len(d6), quic_fits_3x=sum(d4) <= budget,
               delta_handshake_vs_model=hsb - model_row['server_flight'])
    if cfg['server_auth'] in KEM: row['kemtls_client_second_flight'] = len(kem_ciphertext(bytes(KEM[cfg['server_auth']][1]))) + len(finished(bytes(48)))
    row['verdict_changes'] = [k for k, mk in (('quic_fits_3x', 'quic_fits_first_flight'), ('tcp_fits_initcwnd', 'tcp_initcwnd_fits')) if row[k] != model_row[mk]]
    return row


def audit_ledger():
    model = {r['config']: r for r in s3.ledger()}
    return [audit_row(cfg, model[cfg['name']]) for cfg in CONFIGS]


# Worst-case chain search ---------------------------------------------------------------------------------------------
X509_SPACE = {'subject_cn': (1, 64), 'issuer_cn': (1, 64), 'subject_o': (0, 64), 'issuer_o': (0, 64), 'k_san': (1, 100), 'san_len': (4, 253),
              'serial_len': (1, 20), 'n_inter': (1, 2), 'scts': (0, 3), 'ocsp_len': (0, 100)}     # X.520 ub-common-name 64, RFC 1035 253, CA/B <=20-B serial
MTC_SPACE = {'k_san': (1, 100), 'san_len': (4, 253), 'depth': (10, 32)}


def _san(L):
    """DNS name of exactly L chars with labels <= 63 (RFC 1035)."""
    labels = []
    while L > 0: n = min(63, L) - (L - min(63, L) == 1); labels.append('a' * n); L -= n + (L > n)
    return '.'.join(labels)


def cert_size(cfg, p):
    sans = [_san(p['san_len'])] * p['k_san']
    if cfg['pki'] == 'mtc': return len(cert_message(cfg, sans=sans, depth=p['depth']))
    return len(cert_message(cfg, sans=sans, subject_cn='c' * p['subject_cn'], issuer_cn='i' * p['issuer_cn'], subject_o='o' * p['subject_o'],
                            issuer_o='o' * p['issuer_o'], serial_len=p['serial_len'], n_inter=p['n_inter'], scts=p['scts'], ocsp_url='u' * p['ocsp_len']))


def worst_case_search(cfg, space, n=2000, seed=7):
    rng, best = random.Random(seed), None
    for _ in range(n // 2):                                                  # random phase
        p = {k: rng.randint(*v) for k, v in space.items()}; s = cert_size(cfg, p)
        if best is None or s > best[0]: best = (s, p)
    for _ in range(n - n // 2):                                              # hill-climbing phase
        p, k = dict(best[1]), rng.choice(list(space)); lo, hi = space[k]
        p[k] = min(hi, max(lo, p[k] + rng.choice((-1, 1)) * rng.randint(1, max(1, (hi - lo) // 4)))); s = cert_size(cfg, p)
        if s >= best[0]: best = (s, p)
    return {'form': cfg['pki'], 'config': cfg['name'], 'max_certificate_bytes': best[0], 'params': best[1], 'samples': n,
            'analytic_max': cert_size(cfg, {k: v[1] for k, v in space.items()})}


# ------------------------------------------------------------------ Part B: KEMTLS on an ideal-KEM toy --------
class ToyKEM:
    """S6-style toy KEM: the encapsulator's randomness is stored in _REG keyed by (pk, ct), so honest decaps needs only (sk, ct).
    The adversary never reads _REG (the IND-CCA assumption); it may encapsulate to any pk and decapsulate with keys it owns.
    Unknown ciphertexts decapsulate to an implicit-rejection key, as ML-KEM does."""
    _REG = {}
    def __init__(self, tag=b'kem'): self.sk = secrets.token_bytes(32); self.pk = hashlib.sha3_256(b'pk' + tag + self.sk).digest()
    @classmethod
    def encaps(cls, pk):
        r = secrets.token_bytes(32); ct = hashlib.sha3_256(b'ct' + pk + r).digest(); ss = hashlib.sha3_256(b'ss' + pk + ct + r).digest()
        cls._REG[(pk, ct)] = ss; return ct, ss
    def decaps(self, ct): return self._REG.get((self.pk, ct), hashlib.sha3_256(b'reject' + self.sk + ct).digest())


class Reject(Exception): pass


def kdf(label, *parts):
    h = hmac.new(label, digestmod=hashlib.sha3_256)
    for p in parts: h.update(len(p).to_bytes(4, 'big') + p)
    return h.digest()


def th(tr): return hashlib.sha3_256(b''.join(tr)).digest()
def mac(k, m): return hmac.new(k, m, hashlib.sha3_256).digest()
def wire(m):
    t = m['type']
    if t == 'CH': return client_hello(m['key_share'], m['host'], m['groups'], m['ks_group'], m['ta_ids'], m['random'])
    if t == 'SH': return server_hello(m['ct'], m['group'], m['random'])
    if t == 'EE': return encrypted_extensions(m['alpn'])
    if t == 'CERT': return certificate_mtc(m['assertion'], m['proof'])
    if t == 'CKC': return kem_ciphertext(m['ct'])
    return finished(m['mac'])


class Client:
    def __init__(self, host, roots, groups=(GROUP_CAT5, GROUP_CAT3), check_host=True):
        self.host, self.roots, self.groups, self.check_host, self.kem, self.tr, self.key = host, roots, list(groups), check_host, ToyKEM(b'e'), [], None
    def hello(self):
        m = {'type': 'CH', 'random': secrets.token_bytes(32), 'host': self.host, 'groups': self.groups, 'ks_group': self.groups[0],
             'key_share': self.kem.pk, 'ta_ids': sorted(self.roots)}
        self.tr.append(wire(m)); return m
    def server_flight(self, sh, ee, cert):
        if sh['group'] != self.groups[0]: raise Reject('client: illegal_parameter (selected group has no key share)')
        ss_e = self.kem.decaps(sh['ct']); self.tr.append(wire(sh)); self.hs = kdf(b'hs', ss_e, th(self.tr)); self.tr += [wire(ee), wire(cert)]
        a, p = cert['assertion'], cert['proof']
        if p['batch_id'] not in self.roots: raise Reject('client: unknown_ca (trust anchor id not in store)')
        if not MTCBatch.verify(self.roots[p['batch_id']], assertion_bytes(a), p): raise Reject('client: bad_certificate (inclusion proof fails)')
        if self.check_host and self.host not in a['dns']: raise Reject('client: bad_certificate (hostname not in assertion claims)')
        ct_s, ss_s = ToyKEM.encaps(a['pk']); ckc = {'type': 'CKC', 'ct': ct_s}; self.tr.append(wire(ckc))
        self.ahs = kdf(b'ahs', self.hs, ss_s, th(self.tr))
        fin = {'type': 'FIN', 'mac': mac(kdf(b'fk_c', self.ahs), th(self.tr))}; self.tr.append(wire(fin)); return ckc, fin
    def server_finished(self, sfin):
        if not hmac.compare_digest(sfin['mac'], mac(kdf(b'fk_s', self.ahs), th(self.tr))): raise Reject('client: decrypt_error (server Finished MAC)')
        self.tr.append(wire(sfin)); self.key = kdf(b'ms', self.ahs, th(self.tr))


class Server:
    def __init__(self, host, kem, cert, groups=(GROUP_CAT5, GROUP_CAT3)): self.host, self.kem, self.cert, self.groups, self.key = host, kem, cert, groups, None
    def hello(self, ch):
        self.tr = [wire(ch)]
        if ch['ks_group'] not in self.groups: raise Reject('server: handshake_failure')
        ct_e, ss_e = ToyKEM.encaps(ch['key_share'])
        sh = {'type': 'SH', 'random': secrets.token_bytes(32), 'group': ch['ks_group'], 'ct': ct_e}; self.tr.append(wire(sh))
        self.hs = kdf(b'hs', ss_e, th(self.tr)); ee = {'type': 'EE', 'alpn': b'h2'}; self.tr += [wire(ee), wire(self.cert)]
        return sh, ee, self.cert
    def client_flight(self, ckc, cfin):
        ss_s = self.kem.decaps(ckc['ct']); self.tr.append(wire(ckc)); self.ahs = kdf(b'ahs', self.hs, ss_s, th(self.tr))
        if not hmac.compare_digest(cfin['mac'], mac(kdf(b'fk_c', self.ahs), th(self.tr))): raise Reject('server: decrypt_error (client Finished MAC)')
        self.tr.append(wire(cfin)); sfin = {'type': 'FIN', 'mac': mac(kdf(b'fk_s', self.ahs), th(self.tr))}; self.tr.append(wire(sfin))
        self.key = kdf(b'ms', self.ahs, th(self.tr)); return sfin


def run_kemtls(client, server, tamper=lambda stage, m: m):
    """The adversary owns the network: tamper(stage, msg) returns whatever is delivered."""
    out = {'client_accepts': False, 'server_accepts': False, 'reject': None}
    try:
        sh, ee, cert = server.hello(tamper('CH', client.hello()))
        ckc, cfin = client.server_flight(tamper('SH', sh), tamper('EE', ee), tamper('CERT', cert))
        sfin = server.client_flight(tamper('CKC', ckc), tamper('CFIN', cfin)); out['server_accepts'] = True
        client.server_finished(tamper('SFIN', sfin)); out['client_accepts'] = True
    except Reject as e: out['reject'] = str(e)
    out['keys_equal'] = client.key is not None and client.key == server.key
    return out


def pki_setup(hosts=('a.example', 'b.example'), batch_id=b'ca1/2026-09/0'):
    kems = {h: ToyKEM(b'S') for h in hosts}
    asserts = {h: {'scheme': 0, 'pk': kems[h].pk, 'dns': [h]} for h in hosts}
    leaves = [assertion_bytes(asserts[h]) for h in hosts] + [H(b'filler', i.to_bytes(2, 'big')) for i in range(14)]
    batch = MTCBatch(leaves, batch_id)
    servers = {h: Server(h, kems[h], {'type': 'CERT', 'assertion': asserts[h], 'proof': batch.proof(i)}) for i, h in enumerate(hosts)}
    return servers, {batch_id: batch.root}


def _rec(id_, caps, win, out, mech, assume, extra=None):
    blocked = not out['client_accepts'] and not out['server_accepts']
    r = {'id': id_, 'attacker_capabilities': caps, 'winning_condition': win, 'blocked': blocked,
         'outcome': ('BLOCKED: ' if blocked else 'ATTACK SUCCEEDED: ') + (out['reject'] or f"accepted, keys_equal={out['keys_equal']}"),
         'mechanism_that_blocked_it': mech, 'assumption_invoked': assume}
    if extra: r.update(extra)
    return r


def _merge(recs):
    """Combine several attack variants: the attack succeeds if ANY variant is accepted."""
    return {'client_accepts': any(o['client_accepts'] for _, o in recs), 'server_accepts': any(o['server_accepts'] for _, o in recs),
            'reject': ' | '.join(f'{v}: {o["reject"]}' for v, o in recs), 'keys_equal': False}


CAPS = 'controls the network; holds all public keys, ciphertexts and transcripts; oracle access to honest client and server'


def game_positive_control():
    S, roots = pki_setup(); c = Client('a.example', roots); out = run_kemtls(c, S['a.example']); ok = out['client_accepts'] and out['server_accepts'] and out['keys_equal']
    return {**_rec('POSITIVE-CONTROL', 'none (honest network)', 'n/a: both parties must accept with equal keys', out, 'n/a', 'n/a'),
            'blocked': None, 'outcome': f'HANDSHAKE {"COMPLETED" if ok else "FAILED"}: both accept, keys_equal={out["keys_equal"]}', 'both_accept_equal_keys': ok}


def game_mitm():
    S, roots = pki_setup(); c = Client('a.example', roots); A, st = ToyKEM(b'A'), {}
    def tamper(stage, m):
        if stage == 'CH': st['pk_e'] = m['key_share']; return {**m, 'key_share': A.pk}
        if stage == 'SH': st['ss_srv'] = A.decaps(m['ct']); ct2, st['ss_cli'] = ToyKEM.encaps(st['pk_e']); return {**m, 'ct': ct2}
        return m
    out = run_kemtls(c, S['a.example'], tamper)
    return _rec('MITM', CAPS + '; substitutes its own ephemeral KEM key share and re-encapsulates (knows both ephemeral secrets)',
                'client accepts a key the adversary knows, or server accepts the honest client Finished on a split transcript', out,
                'server authentication = decapsulation of ct_S under pk_S (only the server holds sk_S) + Finished over the full transcript',
                'IND-CCA of the long-term KEM; collision resistance of the transcript hash', {'adversary_knows_both_ephemeral_secrets': True})


def game_server_key_substitution():
    S, roots = pki_setup(); A = ToyKEM(b'A'); recs = []
    S2, roots2 = pki_setup(('evil.example',), b'ca1/2026-09/1'); roots.update(roots2); evil = S2['evil.example']   # A holds a LEGIT cert in batch 1
    for variant, tamper in (('pk_S -> pk_A, proof unchanged', lambda s, m: {**m, 'assertion': {**m['assertion'], 'pk': A.pk}} if s == 'CERT' else m),
                            ("pk_S -> pk_A, proof from A's own batch-1 cert", lambda s, m: {**m, 'assertion': {**m['assertion'], 'pk': evil.kem.pk}, 'proof': evil.cert['proof']} if s == 'CERT' else m)):
        recs.append((variant, run_kemtls(Client('a.example', roots), S['a.example'], tamper)))
    return _rec('SERVER-KEY-SUBSTITUTION', CAPS + '; owns a legitimately certified key in another batch', 'client accepts pk_A for a.example', _merge(recs),
                'Merkle inclusion proof binds (claims, pk) as one leaf under a trusted batch root', 'second-preimage resistance of H; CA root distribution')


def game_transcript_alteration():
    S, roots = pki_setup(); fails, total, cap = [], 0, {}
    def paths(m, pre=''):                      # every bytes field, first list element, and the proof index, recursively
        for k, v in m.items():
            if (isinstance(v, bytes) and v) or k == 'index' or (isinstance(v, list) and v and isinstance(v[0], bytes)): yield pre + k
            if isinstance(v, dict): yield from paths(v, pre + k + '.')
    def flip(m, path):                         # applied to the LIVE message: flip one byte (or +1 on the index)
        k, _, rest = path.partition('.'); v = m[k]
        if rest: return {**m, k: flip(v, rest)}
        if isinstance(v, int): return {**m, k: v + 1}
        if isinstance(v, list): return {**m, k: [bytes([v[0][0] ^ 1]) + v[0][1:]] + v[1:]}
        return {**m, k: bytes([v[0] ^ 1]) + v[1:]}
    receiver = {'CH': 'server', 'SH': 'client', 'EE': 'client', 'CERT': 'client', 'CKC': 'server', 'CFIN': 'server', 'SFIN': 'client'}
    run_kemtls(Client('a.example', roots), S['a.example'], lambda s, m: cap.setdefault(s, m))
    for stage in receiver:
        for path in paths(cap[stage]):
            total += 1
            out = run_kemtls(Client('a.example', roots), S['a.example'], lambda s, m, p=path: flip(m, p) if s == stage else m)
            if out[receiver[stage] + '_accepts']: fails.append((stage, path, out['reject']))     # the party RECEIVING the altered message must reject
    out = {'client_accepts': bool(fails), 'server_accepts': bool(fails), 'reject': f'{total} single-field mutations across 7 messages all rejected by the receiver', 'keys_equal': False}
    return _rec('TRANSCRIPT-ALTERATION', CAPS + '; flips one byte of any field of any message', 'the honest party receiving a modified message accepts', out,
                'Finished MACs over the hash of the full transcript; implicit rejection for altered ciphertexts; proof check for altered certs',
                'PRF security of HMAC-SHA3; collision resistance of SHA3-256', {'mutations_tried': total, 'mutations_accepted': len(fails)})


def game_replay():
    S, roots = pki_setup(); c1 = Client('a.example', roots); cap = {}
    run_kemtls(c1, S['a.example'], lambda s, m: cap.setdefault(s, m))                  # session 1 recorded; A also learns c1's full state
    replay = lambda s, m: cap[s] if s in ('SH', 'EE', 'CERT') else m                    # old server flight delivered to the new client
    via_server = run_kemtls(Client('a.example', roots), S['a.example'], replay)         # (a) client's reply forwarded to the real server
    c2 = Client('a.example', roots); c2.hello(); c2.server_flight(cap['SH'], cap['EE'], cap['CERT'])   # (b) adversary answers itself ...
    forged = {'type': 'FIN', 'mac': mac(kdf(b'fk_s', c1.ahs), th(c2.tr))}               # ... forging Finished with the compromised old keys
    try: c2.server_finished(forged); direct = {'client_accepts': True, 'server_accepts': False, 'reject': None, 'keys_equal': False}
    except Reject as e: direct = {'client_accepts': False, 'server_accepts': False, 'reject': str(e), 'keys_equal': False}
    return _rec('REPLAY', CAPS + '; recorded a full previous session INCLUDING that client\'s ephemeral secret key and all derived keys',
                'new client accepts the replayed server flight', _merge([('forwarded to server', via_server), ('forged Finished from old keys', direct)]),
                'client freshness: ct_e was encapsulated to the OLD ephemeral pk (new sk decapsulates to an implicit-rejection key) and ss_S is fresh per session',
                'IND-CCA of both KEMs; fresh client randomness')


def game_downgrade():
    S, roots = pki_setup(); A = ToyKEM(b'A'); recs = []
    def strip(s, m): return {**m, 'groups': [GROUP_CAT3], 'ks_group': GROUP_CAT3, 'key_share': A.pk} if s == 'CH' else m
    def strip_and_mask(s, m): return {**m, 'group': GROUP_CAT5} if s == 'SH' else strip(s, m)     # also hide the downgrade from the client
    for v, t in (('delete Cat-5 group', strip), ('delete Cat-5 group and rewrite SH.group back', strip_and_mask)):
        recs.append((v, run_kemtls(Client('a.example', roots), S['a.example'], t)))
    return _rec('DOWNGRADE', CAPS + '; removes the Category-5 group from the offer and supplies a Cat-3 key share', 'a handshake completes on the Cat-3 group',
                _merge(recs), 'client policy (selected group must be the one it sent a key share for) AND the ClientHello bytes are in both transcripts',
                'collision resistance of the transcript hash')


def game_cross_server_key_confusion():
    S, roots = pki_setup(); out = run_kemtls(Client('a.example', roots), S['b.example'])       # B is legitimately certified and holds sk_B
    unchecked = run_kemtls(Client('a.example', roots, check_host=False), S['b.example'])
    return _rec('CROSS-SERVER-KEY-CONFUSION', CAPS + '; IS server b.example (holds sk_B and a valid cert/proof for b.example)',
                'client connecting to a.example accepts b.example\'s certificate', out,
                'hostname binding: the SNI hostname must appear in the assertion\'s dns claims (the ONLY barrier: all MACs verify)',
                'the CA only certifies names the applicant controls',
                {'without_hostname_check_attack_succeeds': unchecked['client_accepts'] and unchecked['keys_equal']})


def game_cert_substitution():
    S, roots = pki_setup(); rogue, _ = pki_setup(('a.example',), b'rogue-ca/0'); recs = []
    legit_proof = S['a.example'].cert['proof']
    for v, t in (('rogue batch, unknown trust anchor', lambda s, m: rogue['a.example'].cert if s == 'CERT' else m),
                 ('rogue assertion under the legit trust anchor id', lambda s, m: {**rogue['a.example'].cert, 'proof': {**rogue['a.example'].cert['proof'], 'batch_id': legit_proof['batch_id']}} if s == 'CERT' else m),
                 ('rogue assertion with the legit proof', lambda s, m: {**rogue['a.example'].cert, 'proof': legit_proof} if s == 'CERT' else m)):
        recs.append((v, run_kemtls(Client('a.example', roots), S['a.example'], t)))
    return _rec('CERT-SUBSTITUTION', CAPS + '; runs its own CA/batch and issues itself a cert for a.example', 'client accepts a cert not issued under a trusted root',
                _merge(recs), 'trust-anchor id lookup + Merkle inclusion proof against the stored root', 'root distribution is authentic; second-preimage resistance of H')


def game_kem_ciphertext_substitution():
    S, roots = pki_setup(); pk_S = S['a.example'].kem.pk
    out = run_kemtls(Client('a.example', roots), S['a.example'], lambda s, m: {'type': 'CKC', 'ct': ToyKEM.encaps(pk_S)[0]} if s == 'CKC' else m)
    return _rec('KEM-CIPHERTEXT-SUBSTITUTION', CAPS + '; replaces ct_S with its own encapsulation to pk_S (knows that shared secret)',
                'server accepts the honest client Finished, or client accepts', out,
                'ct_S is in the transcript and its shared secret keys both Finished MACs; the adversary lacks ss_e for the server-side key',
                'IND-CCA of the ephemeral KEM; PRF security of the key schedule')


GAMES = [game_positive_control, game_mitm, game_server_key_substitution, game_transcript_alteration, game_replay, game_downgrade,
         game_cross_server_key_confusion, game_cert_substitution, game_kem_ciphertext_substitution]

# ------------------------------------------------------------------ Part C: CPU (verified literature only) ----
GHZ, CPU_MCYCLES = 3.4, {     # Mcycles; None = not verified here (no number is invented)
    'SQIsign-V sign': (507.5, 'SQIsign specification v2.0 (2025), Table 2, NIST level V, Intel i7-13700K'),
    'SQIsign-V verify': (35.7, 'SQIsign specification v2.0 (2025), Table 2, NIST level V, Intel i7-13700K'),
    'ML-KEM-1024 encaps': (None, 'not verified here'), 'ML-KEM-1024 decaps': (None, 'not verified here'),
    'ML-DSA-87 sign': (None, 'not verified here'), 'ML-DSA-87 verify': (None, 'not verified here'),
    'MAYO-5 sign': (None, 'not verified here'), 'MAYO-5 verify': (None, 'not verified here'),
}
SERVER_OPS = {'MTC + SQIsign-V, Cat 5': ['SQIsign-V sign'], 'X.509 + SQIsign-V, Cat 5': ['SQIsign-V sign'],
              'MTC + KEMTLS ML-KEM-1024, Cat 5': ['ML-KEM-1024 decaps'], 'MTC + ML-DSA-87, Cat 5': ['ML-DSA-87 sign'], 'MTC + MAYO-5, Cat 5': ['MAYO-5 sign']}
CLIENT_OPS = {'MTC + SQIsign-V, Cat 5': ['SQIsign-V verify'], 'X.509 + SQIsign-V, Cat 5': ['SQIsign-V verify'] * 5,     # leaf, CA, 2 SCTs, CertificateVerify
              'MTC + KEMTLS ML-KEM-1024, Cat 5': ['ML-KEM-1024 encaps']}


def cpu_table():
    rows = []
    for cfg, ops in SERVER_OPS.items():
        vals = [CPU_MCYCLES[o][0] for o in ops]; tot = sum(vals) if all(v is not None for v in vals) else None
        cv = [CPU_MCYCLES[o][0] for o in CLIENT_OPS.get(cfg, [])]; ctot = sum(cv) if cv and all(v is not None for v in cv) else None
        rows.append({'config': cfg, 'server_ops': ops, 'server_mcycles_per_handshake': tot, 'server_handshakes_per_s_per_core_at_3.4GHz': round(GHZ * 1000 / tot, 2) if tot else None,
                     'client_verify_mcycles': ctot, 'note': None if tot else 'KEM/signature cycle count not verified here; excluded (no number invented)'})
    return {'ghz': GHZ, 'constants_mcycles': {k: {'mcycles': v[0], 'source': v[1]} for k, v in CPU_MCYCLES.items()}, 'rows': rows,
            'axes_note': 'B (bytes on the wire, Part A) and T (server CPU, Part C) are independent axes reported separately; no combined score is formed.'}


# ------------------------------------------------------------------ report + tests ----
def model_discrepancies(ledger):
    L = {r['config']: r for r in ledger}
    out = [{'item': 'KEMTLS first flight', 'model': 'adds FINISHED=40 B', 'measured': 'no Finished in the first flight (server Finished follows the client KEM '
            'ciphertext); the client 2nd flight carries ClientKemCiphertext+Finished', 'client_second_flight_bytes': L['MTC + KEMTLS ML-KEM-1024, Cat 5']['kemtls_client_second_flight']},
           {'item': 'MTC + OV-V (pk in handshake)', 'model': f"{L['MTC + OV-V (pk in handshake)']['model_server_flight']} B", 'measured': 'NOT ENCODABLE: MTC TLSSubjectInfo.public_key is opaque<1..2^16-1>; a 446,992-B key overflows'},
           {'item': 'ServerHello with hybrid ML-KEM-1024 (and X25519MLKEM768)', 'model': 'no packet count', 'measured': 'exceeds one 1,200-B Initial datagram: the server spends 2 padded Initial datagrams (2,400 B) of the 7,200-B budget on ServerHello'}]
    return out + [{'item': n, 'model_server_flight': r['model_server_flight'], 'exact_handshake_bytes': r['handshake_bytes'], 'delta': r['delta_handshake_vs_model'],
                   'exact_tcp_bytes': r['tcp_bytes'], 'exact_quic_udp_bytes': r['quic_udp_bytes'], 'verdict_changes': r['verdict_changes']} for n, r in L.items() if r['encodable']]


REFUTED = ['H1 "exact framing flips a fits/does-not-fit verdict": refuted — 0 verdict changes; |delta| <= 132 B against 7,200 / 14,600-B budgets',
           'H2 "the KEMTLS server first flight carries a Finished" (model): refuted — the server Finished follows the client KEM ciphertext',
           'H3 "the ServerHello fits one Initial packet" (implicit in a flat byte budget): refuted — 2 padded Initial datagrams for any ML-KEM hybrid',
           'H4 "OV-V (447-KB pk) can be an MTC subject": refuted — TLSSubjectInfo.public_key is bounded by 2^16-1',
           'H5 "hostname binding is redundant given the Finished MACs": refuted — with the check off, server B is accepted for A with equal keys (S3-016)']


def worst_case_report():
    out = {'x509': worst_case_search(CONFIGS[4], X509_SPACE), 'mtc': worst_case_search(CONFIGS[6], MTC_SPACE), 'recommended_under_worst_case': []}
    model = {r['config']: r for r in s3.ledger()}
    for cfg in (CONFIGS[6], CONFIGS[8], CONFIGS[4]):
        p = out['mtc' if cfg['pki'] == 'mtc' else 'x509']['params']; sans = [_san(p['san_len'])] * p['k_san']
        kw = {'sans': sans, 'depth': p['depth']} if cfg['pki'] == 'mtc' else {'sans': sans, 'n_inter': p['n_inter'], 'scts': p['scts']}
        pick = lambda r: {k: r[k] for k in ('handshake_bytes', 'quic_datagrams', 'quic_fits_3x', 'tcp_fits_initcwnd')}
        out['recommended_under_worst_case'].append({'config': cfg['name'], 'worst_case': pick(audit_row(cfg, model[cfg['name']], **kw)),
                                                    'typical_25x30char_sans': pick(audit_row(cfg, model[cfg['name']], sans=[_san(30)] * 25))})
    return out


def report():
    ledger = audit_ledger()
    return {'audit': 'pq_audit_s3_tls_wire_v2.1', 'model': 's3_tls_pki.py', 'assumptions': ASSUMPTIONS,
            'part_a': {'ledger': ledger, 'verdict_changes': [(r['config'], r['verdict_changes']) for r in ledger if r.get('verdict_changes')],
                       'worst_case': worst_case_report()},
            'model_discrepancies': model_discrepancies(ledger), 'part_b': {'games': [g() for g in GAMES]}, 'part_c': cpu_table(),
            'refuted_hypotheses': REFUTED, 'axes': 'B (bytes) from Part A and T (CPU) from Part C are reported separately.'}


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.L = {r['config']: r for r in audit_ledger()}; cls.M = {r['config']: r for r in s3.ledger()}

    def test_S3_001_encoders(self):
        """S3-001: TLS vectors, DER lengths, record fragmentation and QUIC varints are exact."""
        self.assertEqual(vec(b'ab', 2), b'\x00\x02ab'); self.assertEqual(hs(HS_FIN, bytes(48))[:4], b'\x14\x00\x00\x30')
        self.assertEqual(der(SEQ, bytes(130))[:4], b'\x30\x81\x82\x00'); self.assertEqual(der(OCT, bytes(300))[:4], b'\x04\x82\x01\x2c')
        self.assertEqual(der_walk(x509_cert(bytes(129), bytes(292))), 1)
        with self.assertRaises(ValueError): vec(bytes(65536), 2)
        recs = tls_records([('ServerHello', bytes(100)), ('Certificate', bytes(40000))])
        self.assertEqual(recs, [105, 6, 22 + 16384, 22 + 16384, 22 + 40000 - 2 * 16384]); self.assertEqual([vl(63), vl(64), vl(16384)], [1, 2, 4])

    def test_S3_002_client_hello_and_initials(self):
        """S3-002: exact ClientHello vs model CH_BASE; client Initial datagram counts."""
        for kems, n in ((['X25519'], 1), (['X25519', 'ML-KEM-768'], 2), (['X25519', 'ML-KEM-1024'], 2)):
            pk = s3.kem_bytes(*kems)[0]; ch = client_hello(bytes(pk))
            self.assertEqual(len(ch) - pk, 211); self.assertEqual(quic_client_datagrams(len(ch)), n); self.assertEqual(n, -(-s3.client_hello_bytes(kems) // 1200))
        self.assertEqual(s3.CH_BASE - 211, 49)                                        # model over-counts the CH base by 49 B

    def test_S3_003_server_hello_spills_initial(self):
        """S3-003: ServerHello = 90 B + ct (model SH_BASE exact); with ML-KEM it needs two Initial packets."""
        for kems in (['X25519', 'ML-KEM-768'], ['X25519', 'ML-KEM-1024']):
            ct = s3.kem_bytes(*kems)[1]; sh = server_hello(bytes(ct)); self.assertEqual(len(sh), 90 + ct)
            self.assertGreater(len(sh) + 4 + ACK_FRAME + QUIC_INITIAL_HDR + QUIC_TAG, DGRAM_INITIAL)
            d = quic_server_datagrams([('ServerHello', sh)]); self.assertEqual(len(d), 2); self.assertEqual(d[0], 1200)
        self.assertEqual(len(quic_server_datagrams([('ServerHello', server_hello(bytes(32)))])), 1)

    def test_S3_004_x509_template(self):
        """S3-004: DER X.509 template is well-formed; TBS overhead vs model CERT_TBS=350."""
        leaf, ca = x509_cert(bytes(129), bytes(292)), x509_cert(bytes(129), bytes(292), ca=True)
        der_walk(leaf); der_walk(ca); ovh_leaf, ovh_ca = len(leaf) - 129 - 292, len(ca) - 129 - 292
        self.assertTrue(300 <= ovh_leaf <= 450, ovh_leaf); self.assertLess(ovh_ca, ovh_leaf); self.assertLess(ovh_ca, s3.CERT_TBS)
        self.assertEqual(len(x509_cert(bytes(129), bytes(292), sans=DEFAULT_SANS + ('a.example.com',))) - len(leaf), 15)   # SAN of 13 chars = 2 + 13

    def test_S3_005_mtc_certificate_bytes(self):
        """S3-005: MTC Certificate message exact bytes; proof verifies with the model's MTCBatch; vs model mtc_proof_bytes."""
        a = {'scheme': 0, 'pk': bytes(1568), 'dns': list(DEFAULT_SANS)}
        p = {'batch_id': bytes(12), 'index': 0, 'path': [bytes(32)] * 24}
        self.assertEqual(len(proof_bytes(p)), 13 + 2 + 8 + 4 + 2 + 24 * 32); self.assertEqual(len(assertion_bytes(a)), 2 + 2 + 4 + 1568 + 2 + 2 + 2 + 2 + 16 + 12)
        self.assertEqual(len(certificate_mtc(a, p)), 4 + 1 + 3 + 3 + len(assertion_bytes(a)) + len(proof_bytes(p)) + 2 + 4 + 13)
        self.assertEqual(len(proof_bytes(p)) - s3.mtc_proof_bytes(24), 13 + 2 + 8 + 4 + 2 - 4 - 8 - 16)
        S, roots = pki_setup(); c = S['a.example'].cert
        self.assertTrue(MTCBatch.verify(roots[c['proof']['batch_id']], assertion_bytes(c['assertion']), c['proof']))

    def test_S3_006_ledger_vs_model(self):
        """S3-006: exact per-config numbers vs the model; the fits/doesn't-fit verdict set is the audit result."""
        L, M = self.L, self.M
        changes = [(n, r['verdict_changes']) for n, r in L.items() if r.get('verdict_changes')]
        self.assertEqual(changes, [])                       # MEASURED: no fit verdict changes under exact accounting
        self.assertFalse(L['MTC + OV-V (pk in handshake)']['encodable'])
        for n, r in L.items(): self.assertTrue(not r['encodable'] or -132 <= r['delta_handshake_vs_model'] <= 62, n)   # MEASURED delta range
        self.assertEqual(L['MTC + KEMTLS ML-KEM-1024, Cat 5']['messages'].get('Finished'), None)
        self.assertLess(L['MTC + KEMTLS ML-KEM-1024, Cat 5']['handshake_bytes'], M['MTC + KEMTLS ML-KEM-1024, Cat 5']['server_flight'])
        self.assertLess(L['MTC + SQIsign-V, Cat 5']['tcp_bytes'], L['MTC + KEMTLS ML-KEM-1024, Cat 5']['tcp_bytes'])
        fits = sorted(n for n, r in L.items() if r['quic_fits_3x'] and r['tcp_fits_initcwnd'] and self.M[n]['qpt128_eligible'])
        self.assertEqual(fits, ['MTC + KEMTLS ML-KEM-1024, Cat 5', 'MTC + SQIsign-V, Cat 5', 'X.509 + SQIsign-V, Cat 5'])

    def test_S3_007_quic_and_tcp_framing(self):
        """S3-007: datagram split, 3x budget with exact client Initials, IPv4/IPv6 wire totals, TCP segments vs initcwnd."""
        r = self.L['MTC + KEMTLS ML-KEM-1024, Cat 5']
        self.assertEqual(r['client_initial_datagrams'], 2); self.assertEqual(r['quic_budget'], 7200)
        self.assertEqual(r['wire_ipv4'], r['quic_udp_bytes'] + 28 * r['quic_datagrams']); self.assertGreaterEqual(r['wire_ipv6'], r['quic_udp_bytes'] + 48 * r['quic_datagrams_v6'])
        self.assertGreaterEqual(r['quic_udp_bytes'], r['handshake_bytes'] + 2 * 45); self.assertLessEqual(r['quic_udp_bytes'], r['quic_budget'])
        self.assertEqual(r['tcp_segments'], -(-r['tcp_bytes'] // 1460)); self.assertTrue(r['tcp_fits_initcwnd'])
        naive = self.L['naive PQ chain, Cat 5']; self.assertGreater(naive['tcp_segments'], 10); self.assertGreater(naive['quic_udp_bytes'], 7200)
        for cfg in CONFIGS[:-1]:                                                           # (OV-V is not encodable)
            d = quic_server_datagrams(flight_exact(cfg)); self.assertTrue(all(x <= 1252 for x in d) and d[0] == 1200); self.assertEqual(sum(d), self.L[cfg['name']]['quic_udp_bytes'])

    def test_S3_008_kemtls_flight_shape(self):
        """S3-008: KEMTLS server first flight has no CertificateVerify/Finished; the client's 2nd flight carries ct_S + Finished."""
        msgs = dict(flight_exact(CONFIGS[8])); self.assertEqual(sorted(msgs), ['Certificate', 'EncryptedExtensions', 'ServerHello'])
        r = self.L['MTC + KEMTLS ML-KEM-1024, Cat 5']; self.assertEqual(r['kemtls_client_second_flight'], 4 + 2 + 1568 + 4 + 48)
        # MEASURED headline numbers (model said 4,280 B incl. a Finished that is not in this flight):
        self.assertEqual((r['handshake_bytes'], r['tcp_bytes'], r['quic_udp_bytes'], r['quic_datagrams'], r['delta_handshake_vs_model']), (4148, 4203, 4403, 4, -132))
        s = self.L['MTC + SQIsign-V, Cat 5']; self.assertEqual((s['handshake_bytes'], s['tcp_bytes'], s['quic_udp_bytes'], s['quic_datagrams']), (3061, 3160, 3266, 3))

    def test_S3_009_worst_case_chain(self):
        """S3-009: random + hill-climb (2,000 samples) finds the largest legal Certificate for MTC and X.509 forms."""
        w = worst_case_report()
        for form in ('x509', 'mtc'):
            self.assertEqual(w[form]['samples'], 2000); self.assertEqual(w[form]['max_certificate_bytes'], w[form]['analytic_max'])   # search converges
            self.assertEqual(w[form]['params']['k_san'], 100); self.assertEqual(w[form]['params']['san_len'], 253)
        self.assertGreater(w['mtc']['max_certificate_bytes'], 25_000); self.assertGreater(w['x509']['max_certificate_bytes'], 25_000)
        for r in w['recommended_under_worst_case']:                                       # MEASURED: 100 x 253-char SANs breaks every recommended config
            self.assertFalse(r['worst_case']['quic_fits_3x'] or r['worst_case']['tcp_fits_initcwnd']); self.assertGreater(r['worst_case']['handshake_bytes'], 28_000)
            self.assertTrue(r['typical_25x30char_sans']['quic_fits_3x'] and r['typical_25x30char_sans']['tcp_fits_initcwnd'])   # 25 SANs of 30 chars still fit

    def _game(self, fn, id_):
        r = fn(); self.assertEqual(r['id'], id_); self.assertTrue(r['blocked'], r['outcome']); return r

    def test_S3_010_positive_control(self):
        """S3-010: unmodified KEMTLS handshake: both accept, equal keys, equal transcripts."""
        S, roots = pki_setup(); c = Client('a.example', roots); out = run_kemtls(c, S['a.example'])
        self.assertTrue(out['client_accepts'] and out['server_accepts'] and out['keys_equal']); self.assertEqual(th(c.tr), th(S['a.example'].tr))
        self.assertTrue(game_positive_control()['both_accept_equal_keys'])

    def test_S3_011_mitm(self):
        """S3-011: ephemeral key-share substitution fails even though the adversary knows both ephemeral secrets."""
        r = self._game(game_mitm, 'MITM'); self.assertIn('server: decrypt_error', r['outcome'])

    def test_S3_012_server_key_substitution(self):
        """S3-012: replacing pk_S (with or without a proof from another batch) fails the inclusion proof."""
        r = self._game(game_server_key_substitution, 'SERVER-KEY-SUBSTITUTION'); self.assertEqual(r['outcome'].count('inclusion proof fails'), 2)

    def test_S3_013_transcript_alteration(self):
        """S3-013: flipping one byte in any field of any of the 7 messages is rejected."""
        r = self._game(game_transcript_alteration, 'TRANSCRIPT-ALTERATION'); self.assertEqual(r['mutations_tried'], 13); self.assertEqual(r['mutations_accepted'], 0)

    def test_S3_014_replay(self):
        """S3-014: a replayed server flight plus a Finished forged from the compromised old session is rejected by the new client."""
        r = self._game(game_replay, 'REPLAY'); self.assertIn('client: decrypt_error', r['outcome']); self.assertIn('server: decrypt_error', r['outcome'])

    def test_S3_015_downgrade(self):
        """S3-015: deleting the Cat-5 group is caught by client policy, and by transcript binding when the SH is masked."""
        r = self._game(game_downgrade, 'DOWNGRADE'); self.assertIn('illegal_parameter', r['outcome']); self.assertIn('decrypt_error', r['outcome'])

    def test_S3_016_cross_server_key_confusion(self):
        """S3-016: server B's valid certificate is rejected by a client for A solely via the hostname claim (all MACs verify)."""
        r = self._game(game_cross_server_key_confusion, 'CROSS-SERVER-KEY-CONFUSION'); self.assertIn('hostname not in assertion claims', r['outcome'])
        self.assertTrue(r['without_hostname_check_attack_succeeds'])                    # the hostname check is load-bearing

    def test_S3_017_cert_substitution(self):
        """S3-017: a rogue-CA certificate for the right hostname fails on trust-anchor lookup or proof, in all three splicings."""
        r = self._game(game_cert_substitution, 'CERT-SUBSTITUTION'); self.assertIn('unknown_ca', r['outcome']); self.assertEqual(r['outcome'].count('inclusion proof fails'), 2)

    def test_S3_018_kem_ciphertext_substitution(self):
        """S3-018: replacing ct_S with the adversary's own encapsulation to pk_S is rejected at the server's Finished check."""
        r = self._game(game_kem_ciphertext_substitution, 'KEM-CIPHERTEXT-SUBSTITUTION'); self.assertIn('server: decrypt_error', r['outcome'])

    def test_S3_019_cpu_table(self):
        """S3-019: CPU numbers only from verified literature; ML-KEM decaps is None; B and T reported separately."""
        t = cpu_table(); rows = {r['config']: r for r in t['rows']}
        self.assertEqual(rows['MTC + SQIsign-V, Cat 5']['server_mcycles_per_handshake'], 507.5)
        self.assertAlmostEqual(rows['MTC + SQIsign-V, Cat 5']['server_handshakes_per_s_per_core_at_3.4GHz'], 6.7, places=1)
        self.assertIsNone(rows['MTC + KEMTLS ML-KEM-1024, Cat 5']['server_mcycles_per_handshake']); self.assertIsNone(t['constants_mcycles']['ML-KEM-1024 decaps']['mcycles'])
        self.assertEqual(rows['X.509 + SQIsign-V, Cat 5']['client_verify_mcycles'], 5 * 35.7); self.assertIn('separately', t['axes_note'])

    def test_S3_020_report_is_json(self):
        """S3-020: --report is valid JSON with the required sections and per-game records."""
        d = json.loads(json.dumps(report()))
        for k in ('part_a', 'part_b', 'part_c', 'model_discrepancies', 'assumptions'): self.assertIn(k, d)
        self.assertEqual(len(d['part_b']['games']), 9); self.assertEqual(len(d['refuted_hypotheses']), 5)
        for g in d['part_b']['games']:
            for k in ('id', 'attacker_capabilities', 'winning_condition', 'outcome', 'mechanism_that_blocked_it', 'assumption_invoked'): self.assertIn(k, g)
        self.assertTrue(all(g['blocked'] for g in d['part_b']['games'][1:])); self.assertTrue(d['part_b']['games'][0]['both_accept_equal_keys'])


def main(argv=None):
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true'); g.add_argument('--report', action='store_true'); a = ap.parse_args(argv)
    if a.report: print(json.dumps(report(), indent=2)); return 0
    return 0 if unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests)).wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
