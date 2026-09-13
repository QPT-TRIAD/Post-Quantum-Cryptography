#!/usr/bin/env python3
r"""CEQS29 public extractor, v1.34 — algorithm, proof, and reproducible checks

The public conflict decoder is implemented, with a mathematical correctness
proof under explicit relation and binding premises. It uses two public bodies
and a pinned configuration identifier. It needs no private seed, witness,
signature list, trapdoor, sidecar, or compressed-oracle database.

The separate JOINT WITNESS EXTRACTOR is NOT implemented or proved here. The
inspected v1.29 code has a full-witness relation checker, but no prover/verifier
for a proof of that full relation. Thus this artifact finalizes the public
algebraic component, not the remaining knowledge-extraction obligation.

Run this single file with:
  python3 ceqs29_extractor.py --self-test
  python3 ceqs29_extractor.py --certificate
  python3 ceqs29_extractor.py --explain
  python3 ceqs29_extractor.py --body0 left.bin --body1 right.bin \
      --configuration CONFIGURATION_HEX

The configuration argument is the authenticated expected 64-byte identifier,
encoded as 128 hexadecimal characters. Authenticating it is the caller's job.
The program does not learn it from an untrusted body. Self-tests deliberately
use synthetic/pinned fixture values and do not establish configuration trust.
The command prints candidate identities and complete positional evidence. Its
status remains ALGEBRAIC_CANDIDATES_ONLY: it does not verify a complete QC.
Python standard-library modules suffice; no dependency installation is needed.

Exact input relation and encoding

The existing CEQS29 body is parsed as:
  bytes   0..15:  b'CEQS29-M87-K1024'
  bytes  16..79:  configuration C
  bytes  80..143: domain d
  bytes 144..207: direct message m
  remaining:     exactly 43 handles (L,Z), each two 64-byte strings
Handles must be strictly sorted by L with no duplicates. Each field element is
a 64-byte big-endian integer encoding polynomial coefficients over GF(2).
Seat i in {0,...,63} is encoded by the polynomial-bit integer kappa=i+1.
This is not arithmetic modulo an integer prime.

For a fixed seat, configuration, domain, and trace seed t_i, v1.29 generates
the same link L_i and mask R_i in either body, independently of the message:
  L_i || R_i = SHAKE256_128bytes(
      b'CEQS29/pair' || t_i || H(b'CEQS29/domain', C, d))
  Z_i = R_i XOR (m * (i+1)).
H in that implementation length-prefixes every argument with eight big-endian
bytes and emits 64 SHAKE256 bytes. The decoder itself never calls H or SHAKE.
The same fixed context is essential; different domains are rejected.

The complete intended private relation R29(B,w) has witness rows (i,t_i,sigma_i)
for all 43 handles. It checks distinct seats, opening of each registered trace
credential, recomputation of each handle at that SAME seat, and verification
of that seat's ML-DSA approval on the canonical body, seat, and own handle.
The ordinary check_witness routine of the v1.29 authorization code consumes these
private rows.
It is not an algorithm that extracts them from a proof.

Claim 1 — the retained polynomial really defines a field

Let f(X)=X^512+X^8+X^5+X^2+1, encoded as (1<<512)|0x125. All arithmetic below is
in F=GF(2)[X]/(f). The independent test computes the following exact conditions:
  X^(2^512) mod f = X
  gcd(f, (X^(2^256) mod f) XOR X) = 1.
The --certificate command recomputes these residues and supplies polynomials
u,v with the independently checked, UNREDUCED polynomial identity
  u*f XOR v*((X^(2^256) mod f) XOR X) = 1.
It computes powers by 512 successive modular squarings, not by expanding an
integer exponent of astronomical size. The output includes all certificate
integers in hexadecimal. A reducible polynomial X^512+1 is a negative control.

Proof. The only prime divisor of 512 is 2. The first condition says that f
divides X^(2^512)-X, whose derivative is 1 and whose irreducible factors have
degrees dividing 512. Hence f is squarefree with such factors. Every proper
divisor of 512 divides 256. A proper-degree irreducible factor of f would
therefore divide X^(2^256)-X, contradicting the second condition. Since deg f
is 512, f is a single irreducible factor of degree 512. This proves the field
premise. The criterion is Rabin's; [S1, Lemma 1] states its general form.

This field dimension is retained from the input construction. It is not a
claim of a 512-bit, 128-bit, or other cryptographic security level.

Claim 2 — division-free identity recovery

For different direct messages m0,m1, put delta=m0 XOR m1 != 0 and form
  T[delta * kappa] = kappa-1, for kappa in {1,...,64}.
For any nonzero delta, these 64 keys are distinct and nonzero. Indeed,
delta*kappa=delta*kappa' implies delta*(kappa XOR kappa')=0. A field has no
zero divisors, so kappa=kappa'. For a common correctly formed handle,
  Z0 XOR Z1 = (R XOR m0*kappa) XOR (R XOR m1*kappa)
            = delta*kappa.
Consequently T[Z0 XOR Z1] recovers exactly the original seat i.
This is equivalent to field division by delta, without computing its inverse.

The implemented table uses basis[j]=X^j*delta, j=0,...,6, obtained with six
multiply-by-X steps. For kappa=1,...,64, let b be its least significant set
bit, j=log2(b), and p=kappa XOR b. Then p<kappa and
  product[kappa] = product[p] XOR basis[j], with product[0]=0.
Induction proves product[kappa]=delta*kappa. There are exactly 64 field XORs
after the six multiply-by-X steps. The table needs no general multiplication,
inversion, random-oracle query, or secret-dependent input. Python dictionary
lookup uses ordinary integer hashing, not a cryptographic hash oracle.

Claim 3 — complete public decoding under stated premises

Suppose both bodies satisfy R29 for an authenticated common configuration and
domain, their messages differ, and their witnesses name sets S0,S1 of exactly
43 distinct registered seats each. Further suppose trace openings are
consistent for each seat across both witnesses and different registered seats
have different links within this context. These are binding/link premises,
not conclusions from a parsing test or from field irreducibility.

The decoder merges the two strictly sorted link lists. A matching link belongs
to the same seat by link uniqueness. A common seat necessarily has the same
link and mask by opening consistency. Claim 2 therefore gives exactly that
seat. Merge traversal visits every common link once, and none is lost. Sorting
the findings by seat produces a canonical list equal to S0 intersect S1. Its
cardinality satisfies
  22 = 43+43-64 <= |S0 intersect S1| <= 43.
Under the premises, no matched link gives a zero/out-of-range identity or a
duplicate seat, so none of the defensive rejection rules triggers. Conversely,
every listed seat belongs to both witness sets. This proves conditional
correctness and completeness for all admissible messages, not just fixtures.

The 43-by-43 sorted merge uses at most 85 iterations, with at most two ordered
link comparisons per iteration. It returns every
match with its two zero-based handle positions and link bytes. Swapping inputs
preserves recovered seats and swaps evidence positions. The evidence checker
recomputes the entire canonical result: subsets, reordered lists, repeated
rows, wrong positions, wrong links, and noncanonical integer types are rejected.
Input and output lengths and loop bounds are fixed by this suite. This is a
public reference implementation, not a constant-time or formally verified
production library.

What this establishes about the actual joint-extractor blocker

The public Trace algorithm and the security reduction's joint extractor have
different output types. Trace returns identities and public positional evidence.
A joint extractor must obtain TWO complete private R29 witnesses for the exact
adversarially output accepted bodies, including approval signatures and trace
openings, with the corresponding authorization experiment transcript.

The original joint-extraction contract requires explicit efficiency and a
success guarantee, for example p_E >= max(p-kappa_J,0)/L_J, in its precisely
specified quantum experiment. This artifact supplies neither such a witness
algorithm nor values for those quantities. Running the public decoder twice,
providing already-known witnesses to check_witness, or checking ordinary
approvals is not an implementation of that contract.

In particular, a pair of public algebraic handle lists can be manufactured to
name a chosen intersection without supplying ANY registered trace opening or
approval signature. The included test does this and obtains algebraic
candidates, as expected. Thus algebraic acceptance is insufficient evidence of
authorization. It is not a forgery of an accepted full R29 certificate: no full
R29 verifier is available or invoked in this test. Even language soundness
alone would not prove knowledge of a signature: a valid signature exists for
each signing message whether or not an adversary knows one.

An ideal-oracle extraction database is allowed inside certain security
reductions. It is not a public certificate input. This distinction removes a
mistaken need for that database as a public sidecar, but does not manufacture
the missing joint witness algorithm. [S2] constructs online QROM extractors
for specified commit-and-open proof protocols with special-soundness
extractors. Those hypotheses require an actual protocol and witness decoder;
they do not turn the current ordinary R29 checker or older different-relation
proofs into that protocol. The application assessment here is an inference
from that theorem's scope and the inspected local code, not a claim by [S2].

Closure status:
  CLOSED COMPONENT: canonical public handle decoder and evidence checker.
  PROVED CONDITIONALLY: exact intersection recovery under the premises above.
  VERIFIED EXACTLY: retained field irreducibility and its polynomial certificate.
  OPEN: actual joint QPT knowledge extractor for a full R29 proof protocol.
  OPEN DEPENDENCY: that full relation's proof prover/verifier is absent in v1.29.

Validation evidence and limits

Twenty test groups passed. They cover all 512 field basis vectors times all
64 encoded seats (32,768 table comparisons), independent polynomial arithmetic
and inverse cross-checks, all overlap cardinalities 22 through 43, boundary
seats, input swapping, malformed framing, suite/context mismatches, duplicate
links/seats, invalid identities, missing matches, evidence tampering, and CLI
success/rejection. They also include the manufactured-handle negative control.

The embedded retained v1.29 public-body fixture recovers exactly seats 0..21.
It came from a transparent approval audit whose source checker originally
validated synthetic witnesses. This artifact replays only its public bodies;
it does NOT reverify those approvals or assert that they constitute a QC proof.
Expected seats are test assertions, never inputs to the decoder. No private
trace seeds or approval signatures are embedded. The fixture includes the
source audit's SHA-256 for provenance, not as a protocol security assumption.

These tests are finite implementation checks. The proofs above establish the
algebraic statements; neither the tests nor the proofs establish the missing
joint knowledge-extraction theorem. No other project blocker is addressed.

Sources

[S1] Catherine S. Greenhill, Theoretical and experimental comparison of
efficiency of finite field extensions, Section 2, Lemma 1 (Rabin criterion):
https://web.maths.unsw.edu.au/~csg/papers/fpaper.pdf

[S2] Jelle Don, Serge Fehr, Christian Majenz, Christian Schaffner,
Efficient NIZKs and Signatures from Commit-and-Open Protocols in the QROM,
especially Definition 3.5 and the extraction construction in Sections 4–5:
https://arxiv.org/abs/2202.13730

[L1] The v1.29 authorization code, actual body/handle relation:
domains/03-zk-carrier-experiments/src/authorization.py.
[L2] The v1.29 package assessment, Sections 2-3 and proof status:
domains/03-zk-carrier-experiments/docs/package-assessment.md.
[L3] The v1.30 mathematical model, Section 7.2, required joint extraction
for the exact adversarial bodies. That document is not part of this
repository; of the four inspected inputs only its content is unavailable
here, and only its recorded hash is retained. The v1.29 approval-audit
evidence is at
domains/03-zk-carrier-experiments/results/public-approval-audit.json.
SOURCE_PROVENANCE below records the SHA-256 of each inspected input under
the relative path it had in the source package.

Path note. This file is domains/05-extraction-and-signature-reductions/src/ceqs29_extractor.py.
Its own version label is the one in the first heading. All paths in this file
are relative to the repository root. The other records it cites are in the same
directory under their own version labels: v1.34 src/ceqs29_extractor.py,
v1.35 src/joint_extractor_lift.py, v1.36 src/circuit_witness_extractor.py,
v1.37 src/signature_security_reduction.py, v1.38 src/slh_dsa_signature_reduction.py,
v1.39 src/signature_margin_sweep.py, v1.40 src/phase_ghz_security_check.py,
v1.41 src/hybrid_sampling_bound_audit.py and v1.42
src/slh_tree_conditioning_audit.py. 'The research trail' is the file
docs/01-research-journey/pqt.md. Where a pointer carries a line number, the
number is the one recorded in the source files; it is not re-verified against
the repository copies.
"""

from dataclasses import dataclass
import argparse
import json
from pathlib import Path

N = 64
QUORUM = 43
MIN_OVERLAP = 2 * QUORUM - N
BITS = 512
MASK = (1 << BITS) - 1
POLY = (1 << BITS) | 0x125
SUITE = b'CEQS29-M87-K1024'
HEADER_BYTES = 208
HANDLE_BYTES = 128
BODY_BYTES = HEADER_BYTES + QUORUM * HANDLE_BYTES


class ExtractionError(ValueError):
    """Malformed input or violated necessary algebraic condition."""


@dataclass(frozen=True)
class ParsedBody:
    configuration: bytes
    domain: bytes
    message: int
    handles: tuple


@dataclass(frozen=True)
class Finding:
    seat: int
    left_position: int
    right_position: int
    link: bytes


def parse_body(body):
    if type(body) is not bytes or len(body) != BODY_BYTES:
        raise ExtractionError('body must have the exact CEQS29 byte framing')
    if body[:16] != SUITE:
        raise ExtractionError('wrong suite')
    handles = tuple((body[p:p+64], int.from_bytes(body[p+64:p+128], 'big'))
                    for p in range(HEADER_BYTES, BODY_BYTES, HANDLE_BYTES))
    if any(a[0] >= b[0] for a, b in zip(handles, handles[1:])):
        raise ExtractionError('links must be strictly increasing and distinct')
    return ParsedBody(body[16:80], body[80:144],
                      int.from_bytes(body[144:208], 'big'), handles)


def multiply_by_x(value):
    if type(value) is not int or not 0 <= value <= MASK:
        raise ExtractionError('noncanonical field input')
    shifted = value << 1
    return shifted ^ POLY if shifted >> BITS else shifted


def identity_table(delta):
    """Return delta*(seat+1) -> seat for all 64 valid field-encoded identities.

    Construction: six multiply-by-x steps and 64 field XORs. Distinct table
    keys follow from field irreducibility and delta != 0; checked defensively.
    """
    if type(delta) is not int or not 0 < delta <= MASK:
        raise ExtractionError('message difference must be nonzero and canonical')
    basis = [delta]
    for _ in range(6):
        basis.append(multiply_by_x(basis[-1]))
    products = [0] * (N + 1)
    table = {}
    for encoded_id in range(1, N + 1):
        low_bit = encoded_id & -encoded_id
        previous = encoded_id ^ low_bit
        value = products[previous] ^ basis[low_bit.bit_length()-1]
        products[encoded_id] = value
        if value == 0 or value in table:
            raise ExtractionError('field/domain invariant failed')
        table[value] = encoded_id - 1
    return table


def decode_bodies(body0, body1, expected_configuration):
    """Return a canonical tuple of all algebraically recovered candidates.

    Inputs are two PUBLIC bodies plus an authenticated configuration identifier.
    No signatures, seed, witness, trapdoor, sidecar, or oracle database is read.
    Preconditions for attribution to actual signers are in the module docstring.
    """
    if type(expected_configuration) is not bytes or len(expected_configuration) != 64:
        raise ExtractionError('expected configuration must be 64 authenticated bytes')
    left, right = parse_body(body0), parse_body(body1)
    if left.configuration != expected_configuration or right.configuration != expected_configuration:
        raise ExtractionError('configuration does not match the pinned value')
    if left.domain != right.domain:
        raise ExtractionError('different conflict domains')
    delta = left.message ^ right.message
    if delta == 0:
        raise ExtractionError('equal messages are not a conflict')
    table = identity_table(delta)
    a = b = 0
    findings = []
    seen_seats = set()
    while a < QUORUM and b < QUORUM:
        link0, z0 = left.handles[a]
        link1, z1 = right.handles[b]
        if link0 < link1:
            a += 1
        elif link0 > link1:
            b += 1
        else:
            seat = table.get(z0 ^ z1)
            if seat is None:
                raise ExtractionError('matched link gives zero or out-of-range identity')
            if seat in seen_seats:
                raise ExtractionError('distinct matched links give a duplicate identity')
            seen_seats.add(seat)
            findings.append(Finding(seat, a, b, link0))
            a += 1
            b += 1
    if len(findings) < MIN_OVERLAP:
        raise ExtractionError('fewer than 22 distinct common identities')
    return tuple(sorted(findings, key=lambda f: f.seat))


def verify_algebraic_evidence(body0, body1, expected_configuration, evidence):
    """Check completeness and exact byte/position correspondence, not QC validity."""
    if type(evidence) is not tuple:
        return False
    for f in evidence:
        if type(f) is not Finding or type(f.seat) is not int or not 0 <= f.seat < N:
            return False
        if any(type(p) is not int or not 0 <= p < QUORUM for p in (f.left_position, f.right_position)):
            return False
        if type(f.link) is not bytes or len(f.link) != 64:
            return False
    try:
        return evidence == decode_bodies(body0, body1, expected_configuration)
    except ExtractionError:
        return False


def candidate_report(body0, body1, expected_configuration):
    findings = decode_bodies(body0, body1, expected_configuration)
    return {
        'format': 'CEQS29-ALGEBRAIC-EXTRACTION-v1.34',
        'status': 'ALGEBRAIC_CANDIDATES_ONLY',
        'authorization_verified': False,
        'full_R29_proofs_verified': False,
        'configuration_hex': expected_configuration.hex(),
        'count': len(findings),
        'findings': [dict(seat=f.seat, left_position=f.left_position,
                          right_position=f.right_position, link_hex=f.link.hex()) for f in findings],
        'requires_before_attribution': 'Authenticate configuration and verify both complete R29 certificates.'
    }


def cli():
    parser = argparse.ArgumentParser(description='Public CEQS29 algebraic candidates only; complete R29 proofs are not verified.')
    parser.add_argument('--body0', required=True, help='first CEQS29 binary body')
    parser.add_argument('--body1', required=True, help='second CEQS29 binary body')
    parser.add_argument('--configuration', required=True, help='authenticated 64-byte configuration as hex')
    args = parser.parse_args()
    try:
        result = candidate_report(Path(args.body0).read_bytes(), Path(args.body1).read_bytes(),
                                  bytes.fromhex(args.configuration))
    except (OSError, ValueError) as exc:
        parser.exit(2, 'Extraction rejected: '+str(exc)+'\n')
    print(json.dumps(result, indent=2))



# Reproducible tests and public fixtures. No private witnesses follow.
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

E = sys.modules[__name__]

ROOT = Path(__file__).resolve().parent
CFG = bytes.fromhex('19' * 64)
DOMAIN = bytes.fromhex('29' * 64)


def clmul(a, b):
    """Independent unreduced polynomial multiplication, bit coefficients."""
    result = 0
    while b:
        if b & 1:
            result ^= a
        a <<= 1
        b >>= 1
    return result


def divrem(a, b):
    if b <= 0:
        raise ValueError('zero polynomial divisor')
    q = 0
    while a.bit_length() >= b.bit_length():
        s = a.bit_length() - b.bit_length()
        q ^= 1 << s
        a ^= b << s
    return q, a


def mul_ref(a, b):
    return divrem(clmul(a, b), E.POLY)[1]


def egcd(a, b):
    u0, u1, v0, v1 = 1, 0, 0, 1
    while b:
        q, rem = divrem(a, b)
        a, b = b, rem
        u0, u1 = u1, u0 ^ clmul(q, u1)
        v0, v1 = v1, v0 ^ clmul(q, v1)
    return a, u0, v0


def irreducibility_certificate(poly=E.POLY):
    """Rabin test for this degree-512 polynomial (only prime divisor: 2)."""
    if poly.bit_length() != 513:
        raise ValueError('degree must be 512')
    residue = 2
    halfway = None
    for step in range(1, 513):
        # Squaring by bit spreading is independent of the decoder's xtime.
        square = sum(((residue >> i) & 1) << (2*i) for i in range(512))
        residue = divrem(square, poly)[1]
        if step == 256:
            halfway = residue
    g, u, v = egcd(poly, halfway ^ 2)
    identity = clmul(u, poly) ^ clmul(v, halfway ^ 2)
    return {
        'polynomial_hex': hex(poly), 'degree': 512,
        'prime_divisors_of_degree': [2],
        'x_to_2_pow_256_mod_f_hex': hex(halfway),
        'x_to_2_pow_512_mod_f_hex': hex(residue),
        'gcd_hex': hex(g), 'bezout_u_hex': hex(u), 'bezout_v_hex': hex(v),
        'bezout_identity_hex': hex(identity),
        'irreducible': residue == 2 and g == 1 and identity == 1,
    }


def synthetic_values(seat):
    """Public reproducible values; deliberately NOT private R29 seed openings."""
    raw = hashlib.shake_256(b'PUBLIC-ALGEBRA-TEST/' + bytes([seat])).digest(128)
    return raw[:64], int.from_bytes(raw[64:], 'big')


def make_body(seats, message, cfg=CFG, domain=DOMAIN):
    handles = []
    for seat in seats:
        link, mask = synthetic_values(seat)
        handles.append((link, mask ^ mul_ref(message, seat + 1)))
    return encode_body(cfg, domain, message, sorted(handles))


def encode_body(cfg, domain, message, handles):
    return (E.SUITE + cfg + domain + message.to_bytes(64, 'big') +
            b''.join(link + z.to_bytes(64, 'big') for link, z in handles))


def overwrite_z(body, link, value):
    p = E.parse_body(body)
    return encode_body(p.configuration, p.domain, p.message,
                       [(l, value if l == link else z) for l, z in p.handles])


class ExtractorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seats0 = set(range(43))
        cls.seats1 = set(range(22)) | set(range(43, 64))
        cls.m0, cls.m1 = 0, (1 << 511) | 17
        cls.b0 = make_body(cls.seats0, cls.m0)
        cls.b1 = make_body(cls.seats1, cls.m1)
        cls.findings = E.decode_bodies(cls.b0, cls.b1, CFG)

    def reject(self, b0=None, b1=None, cfg=CFG):
        with self.assertRaises(E.ExtractionError):
            E.decode_bodies(self.b0 if b0 is None else b0,
                            self.b1 if b1 is None else b1, cfg)

    def test_01_field_certificate(self):
        cert = irreducibility_certificate()
        self.assertTrue(cert['irreducible'])
        self.assertEqual(cert['x_to_2_pow_256_mod_f_hex'],
            '0x53dc5bb4cbe67ab31ef525dbd35fa656a39eb247ca005dadf2aa192f8d81a6c9eb0aff4ea1b1da4ff1fefbce484d7ed2a60793cd8b79a0703d352c26e604da4a')

    def test_02_reducible_polynomial_rejected(self):
        self.assertFalse(irreducibility_certificate((1 << 512) | 1)['irreducible'])

    def test_03_all_basis_vectors_and_identities(self):
        for bit in range(512):
            delta = 1 << bit
            table = E.identity_table(delta)
            self.assertEqual(len(table), 64)
            for encoded_id in range(1, 65):
                self.assertEqual(table.get(mul_ref(delta, encoded_id)), encoded_id-1)

    def test_04_reference_inverse_and_random_differences(self):
        rng = random.Random(3401)
        for delta in [1, 1 << 511, E.MASK] + [rng.getrandbits(512) or 1 for _ in range(32)]:
            g, _, inverse = egcd(E.POLY, delta)
            self.assertEqual(g, 1)
            inverse = divrem(inverse, E.POLY)[1]
            for product, seat in E.identity_table(delta).items():
                self.assertEqual(mul_ref(product, inverse), seat + 1)

    def test_05_all_possible_overlap_counts(self):
        rng = random.Random(3402)
        for overlap in range(22, 44):
            # Permutations exercise seat 63 as a common seat, too.
            permutation = list(range(64))
            rng.shuffle(permutation)
            left = set(permutation[:43])
            right = set(permutation[:overlap] + permutation[43:86-overlap])
            self.assertEqual(len(right), 43)
            m0, m1 = rng.getrandbits(512), rng.getrandbits(512)
            f = E.decode_bodies(make_body(left, m0), make_body(right, m1), CFG)
            self.assertEqual([x.seat for x in f], sorted(left & right))
            self.assertEqual(len(f), overlap)

    def test_06_both_boundary_seats(self):
        seats = set(range(42)) | {63}
        f = E.decode_bodies(make_body(seats, 1), make_body(seats, E.MASK), CFG)
        self.assertEqual([x.seat for x in f], sorted(seats))

    def test_07_swap_symmetry(self):
        swapped = E.decode_bodies(self.b1, self.b0, CFG)
        expected = tuple(replace(f, left_position=f.right_position,
                                 right_position=f.left_position) for f in self.findings)
        self.assertEqual(swapped, expected)

    def test_08_replay_public_v29_bodies(self):
        fixture = PUBLIC_FIXTURE
        b0, b1 = [bytes.fromhex(x) for x in fixture['bodies_hex']]
        f = E.decode_bodies(b0, b1, bytes.fromhex(fixture['configuration_hex']))
        self.assertEqual([x.seat for x in f], fixture['expected_common_seats'])
        self.assertEqual([x.seat for x in f], list(range(22)))

    def test_09_exact_framing_and_types(self):
        for bad in [self.b0[:-1], self.b0 + b'\0', b'', bytearray(self.b0), None]:
            with self.assertRaises(E.ExtractionError):
                E.decode_bodies(bad, self.b1, CFG)
        for cfg in [b'', CFG[:-1], CFG + b'\0', bytearray(CFG), None]:
            self.reject(cfg=cfg)

    def test_10_suite_configuration_domain(self):
        self.reject(b0=b'X' + self.b0[1:])
        self.reject(cfg=bytes.fromhex('20' * 64))
        self.reject(b1=make_body(self.seats1, self.m1, cfg=b'c'*64))
        self.reject(b1=make_body(self.seats1, self.m1, domain=b'd'*64))

    def test_11_equal_messages(self):
        self.reject(b1=make_body(self.seats1, self.m0))

    def test_12_unsorted_and_duplicate_links(self):
        p = E.parse_body(self.b1)
        hs = list(p.handles)
        hs[0], hs[1] = hs[1], hs[0]
        self.reject(b1=encode_body(CFG, DOMAIN, self.m1, hs))
        hs[1] = hs[0]
        self.reject(b1=encode_body(CFG, DOMAIN, self.m1, hs))

    def test_13_zero_and_out_of_range_identity(self):
        link = self.findings[0].link
        z0 = dict(E.parse_body(self.b0).handles)[link]
        self.reject(b1=overwrite_z(self.b1, link, z0))
        self.reject(b1=overwrite_z(self.b1, link, z0 ^ mul_ref(self.m1, 65)))

    def test_14_duplicate_recovered_seat(self):
        first, second = self.findings[:2]
        z0 = dict(E.parse_body(self.b0).handles)[second.link]
        changed = z0 ^ mul_ref(self.m1, first.seat + 1)
        self.reject(b1=overwrite_z(self.b1, second.link, changed))

    def test_15_insufficient_matches(self):
        common = {f.link for f in self.findings}
        p = E.parse_body(self.b1)
        hs = [(b'\xff'*64 if l == min(common) else l, z) for l, z in p.handles]
        self.reject(b1=encode_body(CFG, DOMAIN, self.m1, sorted(hs)))

    def test_16_evidence_completeness_and_canonical_order(self):
        self.assertTrue(E.verify_algebraic_evidence(self.b0, self.b1, CFG, self.findings))
        for evidence in [list(self.findings), self.findings[:-1],
                         self.findings + (self.findings[0],), tuple(reversed(self.findings))]:
            self.assertFalse(E.verify_algebraic_evidence(self.b0, self.b1, CFG, evidence))

    def test_17_evidence_tampering(self):
        first = self.findings[0]
        for changed in [replace(first, seat=True), replace(first, seat=64),
                        replace(first, seat=1), replace(first, left_position=True),
                        replace(first, left_position=-1), replace(first, right_position=43),
                        replace(first, right_position=(first.right_position+1) % 43),
                        replace(first, link=b'\0'*64), replace(first, link=bytearray(first.link))]:
            self.assertFalse(E.verify_algebraic_evidence(
                self.b0, self.b1, CFG, (changed,) + self.findings[1:]))

    def test_18_noncanonical_table_input(self):
        for value in [0, -1, 1 << 512, True, 1.0, None]:
            with self.assertRaises(E.ExtractionError):
                E.identity_table(value)
        for value in [-1, 1 << 512, True, 1.0, None]:
            with self.assertRaises(E.ExtractionError):
                E.multiply_by_x(value)

    def test_19_algebra_acceptance_is_not_authorization(self):
        # These publicly manufactured handles have NO R29 witness/proof supplied.
        report = E.candidate_report(self.b0, self.b1, CFG)
        self.assertEqual(report['count'], 22)
        self.assertEqual(report['status'], 'ALGEBRAIC_CANDIDATES_ONLY')
        self.assertIs(report['authorization_verified'], False)
        self.assertIs(report['full_R29_proofs_verified'], False)

    def test_20_cli_success_and_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            p0, p1 = Path(d)/'b0.bin', Path(d)/'b1.bin'
            p0.write_bytes(self.b0)
            p1.write_bytes(self.b1)
            command = [sys.executable, str(Path(__file__).resolve()), '--body0', str(p0),
                       '--body1', str(p1), '--configuration', CFG.hex()]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['count'], 22)
            p1.write_bytes(self.b0)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')



# The two v1.29 bodies of the retained fixture, with the source package's own
# relative path and SHA-256 for provenance, as recorded at inspection time.
PUBLIC_FIXTURE = {'description': 'Public-body algebra replay from v1.29 transparent approval '
                'audit; no R29 proof is supplied or verified.',
 'source_relative_path': 'continuation_v1.29/evidence/public_approval_audit.json',
 'source_sha256': '1152a3b1bf3bcb4767507357a0da1660dc1fd47d7422c2be1f24651e4a3aad36',
 'configuration_hex': 'f7abb68c259ffd80b9de0863c19f01a0e9e87f43e90343dbe90e04f18b4f71928d192bac33f16d827f809c755767d29615d3a5bd15a8b696a3ab54d87cdb19c8',
 'expected_common_seats': [0,
                           1,
                           2,
                           3,
                           4,
                           5,
                           6,
                           7,
                           8,
                           9,
                           10,
                           11,
                           12,
                           13,
                           14,
                           15,
                           16,
                           17,
                           18,
                           19,
                           20,
                           21]}
PUBLIC_FIXTURE['bodies_hex'] = [
    (
        '4345515332392d4d38372d4b31303234f7abb68c259ffd80b9de0863c19f01a0e9e87f43e90343dbe90e04f18b4f71928d192bac33f16d827f809c75'
        '5767d29615d3a5bd15a8b696a3ab54d87cdb19c8ab6e052a32a123fde8141fd2742072a207f937178e7ce8dc0f6d3bbaf7dcccd6b90f25819845d246'
        'dbea4672403341e7fffd85ec7b44be57ac56f1c7ea478e68000000000000000000000000000000000000000000000000000000000000000000000000'
        '000000000000000000000000000000000000000000000000000000000041b37092fc6b2144b8c9c4d1a6bbf73a55cb2f22b13fe396ebfb8b1766a426'
        'cd64c9f18344c19d17c31d9b7a19f9d4c58df8e9be928da8024d3416f9fd1ba3dcfb325b96e618aa7844b8da1a8276374eefd5137238c75d6f647189'
        'a35df8b833a683061723f39f816a2abf9bfed0db84e7f44127947906fda2c3a04a943f7c0063186f5208c157ebc5a2b3286a696a1be42afaf615dda6'
        'b0733ec205e4402e1f27bac49ca6f6772dc452af1810e7824123ace0167dda4510716bf05c271be59e77402f083769dc284277257999b6ad07f4cdab'
        'b3583cb0cf9b72352700258059116c700558df956830d58e7c312eebb799631667039bd753793ec07a5403ac046895aa345f182325e8065af2998a97'
        '42721ec5e5a643f12a449f96572405da3e89286f95f132ee05f1859330492b66835e88793a11af59a524bfd1bdd786fbda2e17deea4f39e3bc99d3d3'
        '80c9456f4c6d2ecd258dfaabf5a890537d99037f88b07ccfa0eef5dd7dd29dbf169da10665ae678e5954b2a2cc0413391178ad9106f54a12c67d304d'
        'ca37790047758878ac4456a78412120fc083da58c15d8c339bcf1a0c2e614a73c624519a5697ac8983953093e5ac0ea5fdd9ec9d7429a1c9cb65d996'
        '8ee52360962a377d0ea2e4a99914579a184e17a783e7107fdd910fbd3c70fa0a29197fd8f38dc081ab054117eb0cfda09f2c6911663cb8590c425c07'
        '0dc6d1022edbdcca3f7f35d56c5080a7ad613719f080cfe5e458ac9741ef4d1b25f762ee2f80de3791455cb850dafd88d28ab24a4569e4e0e4a72a46'
        '25cb19c8528737f73198eb5252aa9ba22d82d051e2cb0e46880d11f0e5ce661b45dc2cebaf8df5825714aad70674b1f2b5450288efa8e22c1d8e070f'
        'eec5cb937be10993128b7a4b445df46692f3a03d1ccfcf2dc9f11ae4bab0a4cfb7d836e9ff9e8c7231a2d4942d9ccc0e7dbd2f4871baf1a629a5194f'
        '7de889dbfb39ec16ddf48fe324ce2cac2db1992f3d1c96466f146bd86b12798cf55f61c7d44c92ff33eabd2f7df94c174ec612e0a8862fcaa807df4d'
        '438562d565c341749ed6eed2d6c18f2912da0bf8ff3e50e0c5dba37d0f437b40dea12df4e13160d07742d92b04cac7474e9d2672fb9c836d5ed2ccdf'
        '5bf1406769ea0e571b8b08f94ecea7127df7729f8b53f834154e849eb801d3ee6645be8fc3c880e683fb61accd87da0136eb45a40f479b7022850373'
        'db25c0267d42f47026aaeb611b0b99d46111192e14acf4bf14cee751216bd780c640f1a7bd0ac09a9c89960cb4aa94f66099a673f6618546bc5993bc'
        '1512d0c2c33e2153cac447880414f64c26d2604a1a882a1b8d3982879ca4358794bacc90add2eb0a3ad61c22981f73a8e063b855dd96abfae1c9194e'
        'f3ec6dc0f175b46a6180a057173417a804d6e40bbc422efc09125756b196a4ac152e721847b054f0885b08abef441c6be27d4d18527b7aaa53453f97'
        '0ebe004f1bfc2dd298747b5996661cefd3a663c28ddbf5432278a3a89fa00f73deb506c6a4312442b3e486994fd87dbea96827eab4434ebdc82fd4fa'
        '1c2347cbf130e737a707f1efc51698735cb2d7f201a13d1aee0d1e245a1d8c4167ab6c089189c5b11ad75efaa91efd132c504b43db22754a43d512bb'
        '5f412bdaecd92c2faabfdf859fbe6f7dbc641ca6cdbe0f3c0d6a85b8ebd0514fcac33c294798bf04266960be3ec3e709afaa7f5f4519698fd43b7461'
        '7f1293b813304cd38ac4b515c15d78038da9a38f49050729ab92e807f212c66157d58285982b08f18202bb73f6e34516221765f78a35cb9f7edfd101'
        'f6103c02eb96c56ab4c0285ff47f04a62c6798909f6ea7be2908584dbc6767a0b73f95976e1f66d4e11676b7e3e111fad9f7e6e82b556677ea5c28d0'
        '5ae7630e67359c65518eb4dea1ebe9c01d4b1396b168aa2cdf693e9b62e406d6389810e81aa76bf8525fdad55ca0678816182bd5bfb7dade28b8b0d2'
        '462080e73911964abd20c75889fdc49b093bce92d5c60600397c67ab30411ff6a93286d4531a3a92437ac2440d849fa48dd3af799ded3be9fd97f8e0'
        'cd8f25ba499d09ecb2adfb6d12f963d41732fbb4be2737c944ec4b1a0e76333e92bf1027adf069d21ebad32fd6ac2e983eb0a91727f37bc65bc873eb'
        'dcc8066136d579410e852aa6b886e25ddd183a37a58e0e26004a9c9ae5d05c36ff7b01b36d611a1db79be97a5daf736d6ee28d396bd4c2cc4b55fe7c'
        '5b7602bd41c74e63820c5c42e745892b4ea5bc3f29982ee71d67f0627710293f011415f7901f33693b6042929337ee3c065f60866ead68d5a8ece27e'
        '764b84ab60992fff1a166f953c2442ef9562b0fd7b41382bcc8861aace95b9de0f895ac5af422b3010a157f843ae29101cb13e749a9f7f5eb2065417'
        '2e1b991e1e329c91ce46c615cf1f2bb635bd3ebb2d7887e3e48eeee4d86b76ff9ae0b77c029d915c0185aea550e9b4f2b00c7a6f0cfed65a511c43a1'
        '9024e7a00d8587e30e70bb9a1d73a2b1565a819b3d9310d604ee6c2d34ea4c7e5fa29396e663dc1236f5cad15d84ebfba30a7f0e423d63d368c4f405'
        '3d8788323f79491f69efc360a3ef0992a8e97bea9d626ca3b258d20edc6ef87ac45afc2a529b36d0bf3d12aef0cfa77a4a45a34d206643e32f857476'
        '12f9e4a68033dd7c344e2e60166615d2859abb5c9178f1222e6ccc213d9d7a0961f4d198545532e68cb7e3c4fa7034a17d0875ec8059d9aa6ecf28ff'
        'b5eaa0ccc4b9df97cf526e03c6cf3ce02ec852d8e8eabae585138666a13bd9fc5070ead2f8fa6a25175b27090baca14b6f12be7367ea142749594a8a'
        '7d277f63e12db012ae6a0bd504504c00e19a68034e99b871d08f5930f8d82c7a9fc24ff63f5379a67a57321c497d0a185c8e267696be8c0fecf883de'
        '4a85a19d694c33bbda7b261b3f3ae921ba5f2b28f2ec727b650a115eff75352c4fb00ac6da6727d5b7dca93fa3fc17ea9c18dcd863202e491a328aea'
        '0058d95c44f5f8e37254289f04c7518930bf36ecb7b43b2085fbc04ba57df4f8218a2d199f48b38966770d734a51a533ed6ed82a2c5656d9c4513054'
        '714634ae2338c5906e4e326d1198a1d282b70393d2c5223f899af9d37d894fd36b8a5b3be7b91c3ae5935fadaa185d81d9cb45f347fd0dd41cb620e5'
        '630f10017f4cc95e41474d79b4ba787d097e3dc85aaca79e7d4adbe5dcc05f0084e3d0b5a551deedf350f7023572db4ae5e1743f5485a49ff6a0c2ea'
        '41b72e7ba690cb4f8df3b9c245cf817ef1102742ad021913006b0980cd3bbc1ee52591a58d1a9e4f082eb5eb6eaa26fc9357fb5fd82bb5a5fb45524f'
        'e2a4d55b3a17bc41fd03ca19f4279985db480f932310eb7c40674058a6476e4fbb9864eec361cd8a609c36c49489afbaa9148e830bbadd48cb98e744'
        '551ddaaf7823d4642db55d62614bdd3a17847af0eccbe7a445b25549eb3110ec0dedc1b71bb0246bd8e75860417cd7de5d673ade196b7dca3ef6c597'
        '5f44271eec8f6c42db23b9d304e5263404713e464b7fbd6cd5d60352b427269012cd825cee860fd3e0819d6bd4ba391f748e6c98b1436d7492c61645'
        '0f3ae7ea44c515005a53b2f27655096662afe8583206f13f5cbb6e864468d06ae040b2a8206c9b1f559b0169aa4a6532d017508c7ebf8d322a09a5da'
        'b9c8026b6483971f31b55ffd8cd4d919321e4b62093f56fb925bbd407fdd62ac76f774c3e0c7e7f06a827568e79d87fc9e1e16c4bbfcb7afa46a4848'
        '3feb06516a191f2b4c890d65fdc6a143679f991cbae4663d8694f2aa02425c632dedc3fc3a0afc06102d01270cb952d17b65e7d5c6fccc1310f6b2f2'
        'd2fa4b900150e5dec81c1c31fd3335ae1e42ce3c5548ab71345e050a8f98c16e12314cc16db2208c6f81d7d1996388b8663bb348b300abc423f3586f'
        'c62e201c3690191de8bf9fd2f548481292996fbb55482e6072bdf3fa426353f0598c40e90d8426f0b1ca1b5997ec24634b9daf7658ae8d8a1bc6c1fe'
        '4f17ed4e9027d7c5a95a5887acf5872f5cec52cb17fdec55d394ffb1dfa655a09cf11d153c75c4d1b3d74c25dfdc369ed47348ad24da37863e1e5cc8'
        '5a73de419775d7853f9a174d0d561e3a260896b51d08d702cf55b2ebdc599844771eef776884e71163d3592a6fc1b8321fe2626bc894f261c8ce15b5'
        'bd3fc019fcaae00ff80e4783a17b768f65e8d91da80de98308385ddc7cdd00b6f2fe99266de49cbcea1c20a4963d6ee760940a630eb1e11905b92bfe'
        'df1785cf807e1f8f375e6221ae2e23e2355832fccd6e02bf9873ca7ad687c56b4f0394a0000323fb77930560844993d0eddb291eaf7ba36301bcee09'
        'a266f233a238a493b2725a65c9a7432978e2a5821140b01a92d684dc60c21f1d2532eefdb18163a13314dbfc128918955d17f44c013e8286ef270a8a'
        '37d3c080b9f3fd218b2ec4120a7d40d27d6f2bb7c7d6e420ce8027dba5e3e89ab01beca1129e0a934396299b9fb5c67080856862d024a564fb399ee3'
        '18dd5fea840d6aef500e7bd46e7bd07116a084fbb2e7072ff34b512456411cf338ac43583eb550aea55162561b6c6e78dc373a0036134f24b637371c'
        '8c21ffaa29a63da19a13101582fb04f0946c5533b74656d4935b5075210fa5f4c9151c9638606832c330eb15b7b012c0b6c0c71af9d7b7658671b7e7'
        'd2600526dd812ea33e413728a07a474001fcf5d9814a34caf291d9779f6ae3ba4a82e32233de944a5ef376da5f7dc8d0098b5ab65338691ecd6b865b'
        '5824dd0e0f1235322866c76443a66a306a0f8984ca125e3edb0f8bbea6e20f0603463cbbd44793d479e3ef0f0e63ad49b392ddd06fab2e2351be2478'
        '8d50b9928f8a6d1cfd2dd20edc10560be6bf1ff85253ad8e693275f70c051f55bfb000568819a7bd8055202fd25b3b8d14342c4fe3257f7603312843'
        '1af1d6297fc95614818da404ccd927336142c96c1677177b886a9401a509d746714640fa8b3fb945b9852617b7b8a9abd93fd680d3dee5e143012943'
        '3eb31dcf9727efd968967d9292bfc7ddd321565b019599d77a27450e147a2c13069e2323b231d96fc09cbdcf9f2b0954dba9d4ed10b77bf66e3a8fe0'
        'd3eff4482745d3b29cc8f51edeacf29e5a2fef1cf2a781cf58d3cd7b135ea70230889578f993f8e8ac4410b7a4dec3843fc71354c63a411985aca8bf'
        '29cf008d57ace762086e1b8c10dee90194ec6a29937072e249a093df8c1633e0869d09aca6ca60b17bd9f86790784f6f948e55a37152d3e05f43c611'
        'f15f1b89e8b3c26b6da22a5669c3a3687b150d23506149d51b9ffcfb3eace909fce3e8b05b8d9ac538c23c9242e8780b28cb0118bc2cf54570a87105'
        '54c4d93ba3e3938ac51d6958c4b4114dc5e7ed1bf22c7edb2c30addb93ee28a094653266ee8bfc7bda486649ad5e6f154f19ae2db6e4bfce681fbb11'
        '85f190456cd6e474bd21a16d50f03c6bfc0ef614167bbb24fe3216cbee4956c0a2b8c59d4baff785a07ced96f3bee31b3c59896a880d3ae404314950'
        'c8cc5b7ce21da36bb120673a109d7a03319c0260af55e840957593e4250dba29441602e699d029de9da438855c01243168913cd55dc68d78ca3831f0'
        '09ec2f07430aaf45606e7af43db46e4bbb4594cff5f6989cd462099969c27bd1bc19e4e85065ee2a5ee47a90bb6766e48ad0a93c4892f964b278f502'
        '249326b8e8d6e4e1bbaeb75918597c5a952d937ea85dc6ea022c99435e38cb0ee9247c136327bb26e94f9935a2a3d9ef24006f728b605d1b065fb079'
        '1d5d4cfb08d75da2fd61fc6bb877bad0d72bb4ad23af5c6b20e5669377654a4973c1d5be0308bfbc098d19377a657ba73bf96b48e5c2fcf41a593ede'
        '0e742df47ef8713a426aec3c2b0e3e15b269ca963bc1bc97eea25abbc2cb9478416764ae78ff0cfdd737720fd4441c96459f37c3a3f56a039019df20'
        'd0cc5610fa3956fc5108e59276da4dc381def4a26ab0a6f65b29292b0501f9710d2bde4a6ab0430d5364de56e14bbe5c5b305425d84c647e5c9236bd'
        'ef0638c43d463802c952fbdb691a6a5bbfc5074bb4812b17021ddd90e5849753c53997b74eec5f6ea40902ed29f6babfdca07d48cd30fcf523a2dc29'
        'a88a9a37d9bed4fc4fc0c0bf47c0f581b4661d749dc7a3fc3b9f90e36fd14914958518ec5712cba9aaac1c208991c1288a75d7399901b935c00e7002'
        'c9c7d3bf8926bb22ea747ca60d33f6d4d544440515b5e0f9b28e2097c024e34d5a7ac3140183fdfdf80919762baf955d02934b39a5125909ccceecd8'
        '573efe123174cc02aba942ff41e2975e5724884db75ba468f51c49e325750b1187817e83b5696ce1d9bc0326aabf3ed17757e330b357f8ef01c79fb9'
        'a3b91f0b5be7a9333048d4218e74c9167e39f37c2620918b9dd3082a2d3ff7ee321c779ecccf556a614ccf75acfa8f2774aaafee56bc157360e0e4e6'
        '6588eddbeb55655efdba7c7964f1a169bdf11941e2300df7514eef3cc8355358d035c4561c37195bd98f7bbe285e3bf6d9db203d23abe46debd8dc2b'
        '184d8bda1b8e58dd81021e652addad50c296a9533f10fb637ceda268188f01edb7fcf5a5d8e6464f6dd45641e02cbe846a641288c1ffd2a8d94657c6'
        '497669bd5bb97c9eac90e2b99229859aaf3899bb038f834ec12ced167cf4e9e52ebe6f2a1f3c64e40f1b9587c6816b08e4cadbf3dc0f16043417cfd2'
        '302fb1226e1c80e7ff2fa2fafb56c9b890fe35cee6ada7fba113ced148b9a6c2897832db4e3daed3ad33ff04033f59484e8503cf4aa8156a317c8040'
        '013315b28c8e95688b88d3e6ca7b138b93695551f4383e15d19400feb6db8b13c99e771bee2efc7001d6d1d8e7fda408a62d100008161814d2066f92'
        '701bcddb62eeccd71c79cb0210d5d3caa11f004dbb5dcfa3769fc6b8ecd6ca434909d68be06ea6479fcb93b5074fa69e4a1fa3189bede5bd80b89bbd'
        'f5935933f267d228698c4720d1ef00ce73d1ce6b31444f3b0a60e8eee637dc8a1582b21b3e1f3c3bd8fccf63190b5033ea7482e2e1c66fdc8c2557eb'
        '26732d0098a0b6095bce4d190ffd76c09a8f9f4ceaae2661af96ff30c7e09df1fc482211d2464efd6e0dee4dfd2bafba175fce62478e654987f878fa'
        '15cb66edf89b8fa4797328b86baed19330cde662379a342cc9d636517a2bed398d1c87ffce13320574cfcb2734f0de60e962e564f8b1c4d227caf1f0'
        '1ece2f9b1b24a1f4fb83f9afad82c8a808b44594d1837490f43f3e1cb49910f86e1290ad3e6b87a476286ab90b845d95f9910abff19f0c9e2235099a'
        '94db42d8647d3aa32e1afabb9974f20520fdaf5aadf97cec8a5dd4efe6fbee9ad96d45fbf39ebaa00c1971a53b12cd068de46edd94a73900ee7aa685'
        '8f1e64c3c610d063d05382e59a2bc273a162fd3cf044796dbba5c9879fa851db0e2c505ddf2a8f9467d5d349947852bf72e044877d120146a2474e87'
        '91e7da08cd7c2fef67087b1a204e4a4dd1f6c2e306b724208e0d777cf33cd95ebd6d385cd5ab4be7cfac0ba7d1392e47c9fa73a8d112d551c90fea67'
        'fb349a49f7c5a6cb4da56fb02cab7307cf101e6cc09097fb765d8b0f55f84c06eefe569d9b848999d3cc77cf54fee10c82df7d7c7f362d562e42d507'
        '8269bb4d1aa2fb418da9a01fb095867455ad73ef3435901f50c5ef1c34a1503f61de9326ba17e3bf6ee09f04542e859e3d140f4e8bc8e73a394e83d1'
        '3b9a36c4e291f522ab22fd8e'
    ),
    (
        '4345515332392d4d38372d4b31303234f7abb68c259ffd80b9de0863c19f01a0e9e87f43e90343dbe90e04f18b4f71928d192bac33f16d827f809c75'
        '5767d29615d3a5bd15a8b696a3ab54d87cdb19c8ab6e052a32a123fde8141fd2742072a207f937178e7ce8dc0f6d3bbaf7dcccd6b90f25819845d246'
        'dbea4672403341e7fffd85ec7b44be57ac56f1c7ea478e68800000000000000000000000000000000000000000000000000000000000000000000000'
        '000000000000000000000000000000000000000000000000000000110063186f5208c157ebc5a2b3286a696a1be42afaf615dda6b0733ec205e4402e'
        '1f27bac49ca6f6772dc452af1810e7824123ace0167dda4510716bf05c271be51e77402f083769dc284277257999b6ad07f4cdabb3583cb0cf9b7235'
        '2700258059116c700558df956830d58e7c312eebb799631667039bd753793ec07a540b850dc6d1022edbdcca3f7f35d56c5080a7ad613719f080cfe5'
        'e458ac9741ef4d1b25f762ee2f80de3791455cb850dafd88d28ab24a4569e4e0e4a72a4625cb19c8528737f73198eb5252aa9ba22d82d051e2cb0e46'
        '880d11f0e5ce661b45dc2cebaf8df5825714aad70674b1f2b5450288efa8e22c1d8e070feec5cb937be10c88128b7a4b445df46692f3a03d1ccfcf2d'
        'c9f11ae4bab0a4cfb7d836e9ff9e8c7231a2d4942d9ccc0e7dbd2f4871baf1a629a5194f7de889dbfb39ec16ddf48fe3a4ce2cac2db1992f3d1c9646'
        '6f146bd86b12798cf55f61c7d44c92ff33eabd2f7df94c174ec612e0a8862fcaa807df4d438562d565c341749ed6eed2d6c1882d14cee751216bd780'
        'c640f1a7bd0ac09a9c89960cb4aa94f66099a673f6618546bc5993bc1512d0c2c33e2153cac447880414f64c26d2604a1a882a1b8d3982879ca43587'
        '94bacc90add2eb0a3ad61c22981f73a8e063b855dd96abfae1c9194ef3ec6dc0f175b46a6180a057173417a804d6e40bbc422efc09125756b196a6a2'
        '152e721847b054f0885b08abef441c6be27d4d18527b7aaa53453f970ebe004f1bfc2dd298747b5996661cefd3a663c28ddbf5432278a3a89fa00f73'
        'deb506c624312442b3e486994fd87dbea96827eab4434ebdc82fd4fa1c2347cbf130e737a707f1efc51698735cb2d7f201a13d1aee0d1e245a1d8c41'
        '67ab6c089189c7ae160e725197e196df746f5bdf8276c06def0e2086697fab8dcb52682f2eb8314ad63fdc5ca0cc58ac404ba25afc37d99008e767f9'
        'd955751951dcec5653190674a4771a200e177e6a0745b778a67ed19849e4b91c67dc00c73a0743edfaa8ede3153e5dce926b6d42864a95876ba5e4c0'
        'a34d95806d8ca0556b05068a816c56ef1afd37a5ba1f51b7d57d0c0768a5577ade53b539296142b521bc3d6d6e0a5bfddec971551b86b483133ddc98'
        'ab770e1d347e759156969c0ac99e08b36635b4c0b8250d2b6c625cc2dd633bc95226e835a4428f6ba1400080b5ee08808531aac7b2f991b0ca325a4c'
        '0c861002707652e44781f8a391a4c76352f2cb755da3c58b1e1a43988f1f76bd27cb6a9261343fa23d6dd299abb2f983fefddc21ce1154b8caa70901'
        '29d5218d9af4da9eef1530a5f4a094a8433ef5f267b7ea03394e8df0c2df9de73b330c46382db1a8af462f61f8d4e165d94c0c5ad288c4099bb28f3c'
        '4a6969e408c6679f03f8678b7e2fbdf333ac370b4159e532bac356f0759b4a1921919f062ae1b3dcf1052dff3ca47e1efc1a2142fff593a32972d1d2'
        '3ea85122cfcb866d01f68a66cf9b5814ee00447f8f9f73d31bae4daabd561687580ce76c4bb0ad45c642f40419456a47b1556d2a9e52bcf107371e5d'
        'bda636000a3fc3254bf559e786b3ec9ddd670ad78d1b175523e6df44825b2e117517f19455d84d23221765f78a35cb9f7edfd101f6103c02eb96c56a'
        'b4c0285ff47f04a62c6798909f6ea7be2908584dbc6767a0b73f95976e1f66d4e11676b7e3e111fad9f7e6e8ab556677ea5c28d05ae7630e67359c65'
        '518eb4dea1ebe9c01d4b1396b168aa2cdf693e9b62e406d6389810e81aa76bf8525fdad55ca0678816182bd5bfb7d9c63124eea88c613fdfd7cfd1ed'
        'ae83c2ca87bfc1462dcbebdaaad54bbc16ec8219ce7f566dde5e580d0ce872495ae00a3fb49a5a7f296d9d6e5a4da1330479e6138a7c52ede899c771'
        '36662d0d2f4617877a5e818e5902aa5491e73bd70b1e15e71bc649adf5cf006c6848ebe2e2e15735031f3b558c4c580ccf8a3b5b84fd66973d9d7a09'
        '61f4d198545532e68cb7e3c4fa7034a17d0875ec8059d9aa6ecf28ffb5eaa0ccc4b9df97cf526e03c6cf3ce02ec852d8e8eabae585138666a13bd9fc'
        'd070ead2f8fa6a25175b27090baca14b6f12be7367ea142749594a8a7d277f63e12db012ae6a0bd504504c00e19a68034e99b871d08f5930f8d82c7a'
        '9fc246d83f5379a67a57321c497d0a185c8e267696be8c0fecf883de4a85a19d694c33bbda7b261b3f3ae921ba5f2b28f2ec727b650a115eff75352c'
        '4fb00ac6da6727d5b7dca93fa3fc17ea9c18dcd863202e491a328aea0058d95c44f5f8e37254289f04c7518930bf36ecb7b43b2085fbc04ba57df4f8'
        '218a2d199f48b3896677044c4a51a533ed6ed82a2c5656d9c4513054714634ae2338c5906e4e326d1198a1d282b70393d2c5223f899af9d37d894fd3'
        '6b8a5b3be7b91c3ae5935fadaa185d81d9cb45f347fd0dd41cb620e5630f10017f4cc95e41474d79b4ba787d097e3dc85aaca79e7d4adbe5dcc05f00'
        '84e3d0b5a551deedf350f7023572db4ae5e177364f0897602e953f7f11adf8629a9334f623dc463189b7db7cb7ae23577b183e848d1fc340654256db'
        '93a47ff0dbb92df39a1d177836962f962940c5f36e085b2998b271ffebc4b0286f858352d65c5705a178dc4b587ad5d32c946383896369b7a25bbed2'
        'ddfec0e5ce08f781560fba8599084032738071c7c52f10e4dbfda7ad51423eb9706786e093fb053a233c46f0d30c2b77ff652dbb02187dfcd249fdd1'
        'ceeeda5d45ffef4cd32b87225c9ece693549b0f170322a85d29617c9c220a06388507eaf090f7916bfb9d27938db2f34c6c3b3049bbe36d38942479f'
        '99a5b48978acf61f9a1f06e3a4d50bcf14eefcadf740d32636839ca065f755214be57b66527bea9356f83611162426dfbb22e6ac8143ed282a84d09e'
        'eb3008c24800dd17cbd8f44eb9ff83097438de43174b610f68719db74eaf3b101358890c8d3e03a426db2c98d575f2fd63eee7337404ba8dbef389a0'
        '011dd601ac27172577a228f8dea3ae24b8009c7ac142a8ff57c0f274f94fa6c2c082258e1a40f029171e766a5485a49ff6a0c2ea41b72e7ba690cb4f'
        '8df3b9c245cf817ef1102742ad021913006b0980cd3bbc1ee52591a58d1a9e4f082eb5eb6eaa26fc9357fb5fd82bb5a57b45524fe2a4d55b3a17bc41'
        'fd03ca19f4279985db480f932310eb7c40674058a6476e4fbb9864eec361cd8a609c36c49489afbaa9148e830bbadd48cb98e755551ddaaf7823d464'
        '2db55d62614bdd3a17847af0eccbe7a445b25549eb3110ec0dedc1b71bb0246bd8e75860417cd7de5d673ade196b7dca3ef6c5975f44271e6c8f6c42'
        'db23b9d304e5263404713e464b7fbd6cd5d60352b427269012cd825cee860fd3e0819d6bd4ba391f748e6c98b1436d7492c616450f3ae7ea44c5100a'
        '5a53b2f27655096662afe8583206f13f5cbb6e864468d06ae040b2a8206c9b1f559b0169aa4a6532d017508c7ebf8d322a09a5dab9c8026b6483971f'
        '31b55ffd8cd4d919321e4b62093f56fb925bbd407fdd62ac76f774c3e0c7e7f06a827568e79d87fc9e1e16c4bbfcb7afa46a48483feb06516a191f2b'
        '4c890d65fdc6a0445b9bca77f1b80276d3570fcbb93e8bfdf246c9329603885ff5330fff1900769f88b99d81b24433d239d2577c2ac918dc14e12668'
        '7a998a1c0b5c34403a6ad824f9cfd6467a48f01742401434d73289d2988c4171b0cec3766fd0803b9e6555104fdbfd8a6c32ce314a4ef5b2ca2c6469'
        '936e1ab94c4ab17af27295ce0d0a0c425da4f32a9285b1858fd84823efaefb9b74aa897bcf1d6cb6a4ae910ccf4f63d9bf80aab25522b9754d37e75c'
        'd35db337432f0c87d73f6c79642cd5c42386cac20e8e9c4e05486c285ffc2467e6d95d3d11da1438aadc55e1901853b001526d7d8d824996d693c98d'
        '8d7431b97bbb3e9e907d24401722fc93402bf8c96fcf0f6d679f991cbae4663d8694f2aa02425c632dedc3fc3a0afc06102d01270cb952d17b65e7d5'
        'c6fccc1310f6b2f2d2fa4b900150e5dec81c1c31fd3335ae1e42ce3cd548ab71345e050a8f98c16e12314cc16db2208c6f81d7d1996388b8663bb348'
        'b300abc423f3586fc62e201c3690191de8bf9fd2f548481292996fbb55482a6d72bdf3fa426353f0598c40e90d8426f0b1ca1b5997ec24634b9daf76'
        '58ae8d8a1bc6c1fe4f17ed4e9027d7c5a95a5887acf5872f5cec52cb17fdec55d394ffb1dfa655a09cf11d153c75c4d1b3d74c25dfdc369ed47348ad'
        '24da37863e1e5cc85a73de419775d7853f9a174d0d561e3a260896b51d08d702cf55b2ebdc59907c771eef776884e71163d3592a6fc1b8321fe2626b'
        'c894f261c8ce15b5bd3fc019fcaae00ff80e4783a17b768f65e8d91da80de98308385ddc7cdd00b6f2fe9926ede49cbcea1c20a4963d6ee760940a63'
        '0eb1e11905b92bfedf1785cf807e1f8f375e6221ae2e23e2355832fccd6e02bf9873ca7ad687c56b4f0394a0000322ed77930560844993d0eddb291e'
        'af7ba36301bcee09a266f233a238a493b2725a65c9a7432978e2a5821140b01a92d684dc60c21f1d2532eefdb18163a13314dbfc128918955d17f44c'
        '013e8286ef270a8a37d3c080b9f3fd218b2ec4120a7d40d27d6f2bb7c7d6e420ce8027dba5e3e89ab01beca1129e0a934396299b9fb5cd418f8a6d1c'
        'fd2dd20edc10560be6bf1ff85253ad8e693275f70c051f55bfb000568819a7bd8055202fd25b3b8d14342c4fe3257f76033128431af1d6297fc95614'
        '818da404ccd927336142c96c1677177b886a9401a509d746714640fa8b3fb945b9852617b7b8a9abd93fd680d3dee5e1430129433eb31dcf9727efd9'
        '689677a492bfc7ddd321565b019599d77a27450e147a2c13069e2323b231d96fc09cbdcf9f2b0954dba9d4ed10b77bf66e3a8fe0d3eff4482745d3b2'
        '9cc8f51edeacf29eda2fef1cf2a781cf58d3cd7b135ea70230889578f993f8e8ac4410b7a4dec3843fc71354c63a411985aca8bf29cf008d57ace762'
        '086e1b8c10dee90194ec6c2a9413396a8d88d337a207e381486eff9734cf5fe8104433fd858af03eb627185e7f998b490f12eca8440c58c52988d7da'
        '6fbac7f2135339db243356642e3f7bc59340a690473475100d3ca732d1bc334070bcda09a3f1912ad83eca622883f34b973e5aae3562a5dc1b2bc203'
        '33fdedb96d40d33209527a306dffaf5ef2f4b4d39cc494881b96eaee810beb8f25b6dc25ea6a7d21ebc7e2359844fdfcab8f70917302becad5e61e66'
        '4652fc796260913519bf405ca5377861f2b58fe6ed8c9608acdfee13dead99449f41bdaab62ab1e9b6771b239c531c2d4444a25f5ca2e1d6e10362c2'
        'ab2e69f4fedce9c050d7da8321abfd0a64e077c4401e5f3096f170aea2a3d9ef24006f728b605d1b065fb0791d5d4cfb08d75da2fd61fc6bb877bad0'
        'd72bb4ad23af5c6b20e5669377654a4973c1d5be0308bfbc098d19377a657ba73bf96b48e5c2fcf41a593ede0e742df47ef8713a426aec3c2b0e3e15'
        'b269ca963bc1bc97eea25abbc2cb9478416764ae78ff0cfdd737720fd4441c96459f31d1a3f56a039019df20d0cc5610fa3956fc5108e59276da4dc3'
        '81def4a26ab0a6f65b29292b0501f9710d2bde4a6ab0430d5364de56e14bbe5c5b305425d84c647edc9236bdef0638c43d463802c952fbdb691a6a5b'
        'bfc5074bb4812b17021ddd90e5849753c53997b74eec5f6ea40902ed29f6babfdca07d48cd30fcf523a2d60ea9856d79023f9668b4c26fdf583665b9'
        'edb82062d6fe5ecff165946886e6eeef6deb25b5fccc990527c3c1cf1e86db07a6a4cd807099ee50181e990bb380c845cbb18a37de199a4f1df32dfe'
        'b2fbaab08543f0744276d7e29c1de8287ce9c6a8c397262c52b577ae1cf700493e04700b22e778c40f39683d4d870f056deb74faaba942ff41e2975e'
        '5724884db75ba468f51c49e325750b1187817e83b5696ce1d9bc0326aabf3ed17757e330b357f8ef01c79fb9a3b91f0b5be7a9333048d4218e74c916'
        '7e39f37c2620918b9dd3082a2d3ff7ee321c779ecccf556a614ccf75acfa8f2774aaafee56bc157360e0e4e66588eddbeb55655efdba7c7964f1a575'
        'b307713968fc8cd140f7d879f1a80be3ab283f549c6f514f0c7ab2baceedc89bea60e9320ae53259eb390bcb53a86a737789cd60d0e071f734d7be47'
        '214373f3e94e69ee0b878417e45ea015ddf76cdcbb2bd9a53c57232a3b29bfa0b39036c3121a291bcf4a64852b23d1b5180c3ec32c091197a8cc172e'
        'b51df15f687d8c18c65c4c002044101ba12d5865f598b432c75582becf9408f282bf91cf4820b4d6a375e6a88bab4d4ef1b81213e18d418f6efef8ae'
        '9c5dca341547a3f1818105c370603db7b1ce6e4ca4e351f04c8cfec37a118b40640065fb6028ec2593cb60c221da335a6de895c1953f76baec335fe1'
        '3f3411f23374695180d0e40db2d15620cb6b045c18d05776077b8d535c56e8eb7fccae0b9f6cec9690760a41ab461a39a99bff90349c27d5e76505c8'
        '8d88434104df83dfa225642763627acafe796ad774dac50d3f8b61cb940c4141ab4d6e20b303e94e7d6d8555aaf7536838f11752a90050760e3125cd'
        'c8124a5f8efcb76a52f063879af7d3066e4337139b18c2b1cf10d01faaed627cedb2ce90167e32497b9c9360d087584167dce7e54558a80f8617a213'
        'ccf00b166a2ea60f444ea6bda28ef7381f275073c7dbcf6a8fd2c9286e1a001188a5703eb6532ef4054d901b0aa0186b5584d85c9c5eba1e10115b6d'
        'b7aa04044225d3b9a8a267857f7cd96b51c6dcf92c4d3c1b0f5606b288397b9ad5e785f014d486a268ce679162f57465d7d5b8989bce231c6ab0c0dc'
        '9750adbc7e0282415b4450738e33fff232bde89cbefcf969d6546dad2daccfb86971bdfdce1b7ec8286a0ef3f4291261ace35131513e3ffd01f8ee6b'
        'f4b7acc8b18c3c3907c9e2d11aa935366a6648e59bc711379f90160cf4fde780466344246e742dade1f2fc7a58a78f0624264bc483f2a69ccc3a8530'
        '45f3b13a34e7ad36576220278f5c8ad6b599be585a303efbcb47a3cee0c2ab086501204f92fe8ef6c0f325e45996c6b0c9b3993a3d3ff8d23e95f9e9'
        '3a2d4d2f86ed9665d0c040cbff0d562703546ffd32eec3c7da8a4ab347e8358f8cb028c2cb8d84ad1582fddf92c2f627ea791e91607e4e85b0f8a0d4'
        '1bea9f3672d15f8e82e225db06886c2efcaed3a5fa5d480475e2839c50608b814e5e962486086a44183de431b8f573fc82a051f1e11b5b63616a95fd'
        'f041caa032ba14a2e840241b940a7630ad3acd20a2ceea3f37fda9d40691bca72a92a8b00cebc1b6e687ed9218a3c03a6e788ccac4324346ebd36458'
        '02c51a831f712e332fec90e04d8a19c270c8d0cad50ef9185b8722ae7ac122cd3a5c0b919fd894eef0809d40d7230b04dcf8687c5d1a08a6edb930ef'
        '7b7ec709ae009191405aa93832d55810bee507df69f8a165eca7a9a7750e41446258003656b348b9a753a9a4e8f7679460b9630f6c90db64cdb8203d'
        'a5dea155f7c5a6cb4da56fb02cab7307cf101e6cc09097fb765d8b0f55f84c06eefe569d9b848999d3cc77cf54fee10c82df7d7c7f362d562e42d507'
        '8269bb4d1aa2fb418da9a01fb095867455ad73ef3435901f50c5ef1c34a1503f61de9326ba17e3bf6ee09f04542e859e3d140f4e8bc8e73a394e83d1'
        '3b9a36c4e291f522ab22fa9b'
    ),
]

SOURCE_PROVENANCE = {'continuation_v1.29/assessment.md': 'c7f9e583d697ce6fc875fbcd6505247db757b3c545f7915bd4fd62d76c962dd4',
 'continuation_v1.29/authorization.py': 'cec05e5837f1f4a00a1da2a0e2881475918698bb71fe137d10562797496ef71d',
 'continuation_v1.29/evidence/public_approval_audit.json': '1152a3b1bf3bcb4767507357a0da1660dc1fd47d7422c2be1f24651e4a3aad36',
 'continuation_v1.30/mathematical_model.md': 'd3e5b978f0b1d51690c59486d956492810d55756edc3604e558100d8e34f3d07'}

if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    elif sys.argv[1:] == ['--certificate']:
        print(json.dumps(irreducibility_certificate(), indent=2))
    elif sys.argv[1:] == ['--explain']:
        print(__doc__)
    else:
        cli()
