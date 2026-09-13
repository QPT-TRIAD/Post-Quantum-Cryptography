#!/usr/bin/env python3
r"""
# SLH-DSA replacement and P-384 hybrid reduction — v1.38

Signature-security scope only. 2026-09-10.

Result: SLH-DSA can replace the ML-DSA signature assumption. An optional
ECDSA-P384 / SLH-DSA hybrid also reduces to SLH-DSA alone when verification
requires both components on the same approval. ML-KEM-1024 and OTBN do not
remove or numerically discharge the signature-security assumption.

This is a new proposed signature suite and a conditional mathematical
reduction. It is not a deployed R29 upgrade, a hardware implementation,
a newly constructed extractor, or a concrete QPT-128 certification.

## 1. Roles of the proposed components

| Component | Role in this analysis | Effect on the signature reduction |
|---|---|---|
| SLH-DSA-SHAKE-256s | Proposed pure-mode approval signature | Replaces the ML-DSA forgery endpoint with a hash-based signature endpoint |
| secp384r1 / NIST P-384 | Interpreted here as ECDSA-P384 with SHA-384 | Optional additional signature; no post-quantum hardness is credited to it |
| ML-KEM-1024 | Independent key-establishment primitive | Its IND-CCA property does not itself imply public signature unforgeability |
| OpenTitan / OTBN | Implementation platform | Does not change the abstract acceptance or fresh-message forgery games |

SLH-DSA is standardized in FIPS 205 and is based on SPHINCS+ [S1]. The chosen
candidate has n=32 bytes, h=64, d=8, h'=8, a=14, k=22, log2(w)=4 and m=47.
The 256 designation is a parameter label, not a proven numerical success
probability for our system. NIST describes this parameter set using category
5, relative to a block-cipher comparison; category labels are not substituted
for concrete advantage bounds. FIPS 205's stated usage bound for these
parameter sets is at most 2^64 messages per key [S1].

FIPS 203 describes ML-KEM as a mechanism to establish shared secret keys
[S2]. If P-384 was instead intended to mean ECDH, it also belongs to key
establishment and contributes no signature component here. No hybrid KEM
combiner or authenticated-channel theorem is constructed in this work.

The OpenTitan OTBN documentation lists P-384 operations and current PQC
extensions, while warning that the development documentation can differ
from RTL/simulator versions [S3,S4]. The approved PQC RFC directs its vector
extension work toward polynomial arithmetic; it describes SLH-DSA support
through Ibex and existing SHA-2/SHA-3 accelerators [S5]. This establishes a
possible implementation route, not readiness of a particular board or build.

## 2. Pin the new approval suites

Old approvals must not be relabeled as SLH-DSA approvals. The reference model
uses new 16-byte suite identifiers:

    b'CEQS38-SLH-S256S' : pure SLH-DSA-SHAKE-256s
    b'CEQS38-HYB-S256S' : SLH-DSA-SHAKE-256s AND ECDSA-P384/SHA-384

The public body retains the previous field structure: suite, 64-byte
configuration, 64-byte conflict domain, direct 64-byte message, and 43 sorted
128-byte handles. Only framing is specified here; full trace-witness
validation remains upstream. The new digest/message definitions are

    D38(B) = SHAKE256(Frame(b'CEQS38/body', B), 64 output bytes),
    M_i(B) = b'CEQS38/VOTE/v1' || D38(B) || byte(i) || h_i(B),
    ctx = b''.

Frame prefixes every part with its 8-byte big-endian length. Trusted
configuration must bind each seat to its full public-key bundle, exact
parameter set, signature mode and acceptance policy. It must authorize the
new suite explicitly. There is no negotiation-controlled classical fallback.
The paired conflicting bodies use the same suite and same configuration.
Registered SLH public keys are distinct; independent sampling with duplicate
abort is the setup distribution proved here.

For pure SLH-DSA, FIPS 205 Algorithm 24 has native argument order

    slh_verify(M, SIG, ctx, PK).

It internally uses the injective string

    C(ctx,M) = 0x00 || byte(len(ctx)) || ctx || M,

for contexts of length at most 255. The reference callback adapter preserves
that native API. It does not pre-apply C before calling pure verification.
HashSLH-DSA and internal signing APIs under the same key are excluded from
the modeled interface. The public key and signature encodings must be those
of the pinned parameter set; syntactic checks alone are not verification.

The hybrid signs one logical (ctx,M) pair using independent keys:

    sigma_S = SLH.Sign(sk_S, M, ctx),
    sigma_E = ECDSA-P384-SHA384.Sign(sk_E, C(ctx,M)),
    sigma_H = (sigma_S, sigma_E),

    Verify_H = SLH.Verify(pk_S,M,sigma_S,ctx)
               AND ECDSA-P384-SHA384.Verify(pk_E,C(ctx,M),sigma_E).

The reference hybrid uses a typed pair and canonical component lengths;
it is not a complete network serialization specification. Its ECDSA callback
must hash the framed message with SHA-384 exactly once and perform full
curve/key/signature validation. The SLH callback accepts raw M and ctx and
performs its own FIPS-defined processing. A complete deployment must validate
and bind both registered keys; the reduction does not assume a key binding
can be inferred from unauthenticated metadata.

## 3. The hybrid projection theorem

Consider the composite chosen-message game with an independently generated
SLH key and ECDSA key. On each composite signing query (ctx,M), generate both
components for that pair. Retain every call to the SLH signing oracle in a
global log, including standalone calls if the modeled environment has any.
A fresh composite message is sufficient for this theorem only when its
(ctx,M) pair is also absent from that complete SLH log. Dedicated component
keys with no extra signing interface ensure this implication automatically.

Reduction R_S receives an SLH challenge public key, generates the ECDSA
keypair locally, and publishes the authenticated composite public key in the
modeled setup. On composite signing queries it forwards (ctx,M) to the SLH
challenger and supplies the ECDSA signature locally. Given a fresh accepted
composite forgery, it returns the same M, ctx and sigma_S.

Proof: acceptance of Verify_H implies acceptance of the SLH component.
Global freshness implies the output pair was never asked of the SLH
challenger. Thus the returned component is an ordinary SU-EUF-CMA forgery.
The simulation generates the other component itself, so its success does
not depend on ECDSA being difficult to forge. At the appropriate resource
bounds,

    Adv_Hybrid(A) <= Adv_SLH(R_S).                            (H)

The component-projection success loss is exactly 1. The time overhead of
local ECDSA generation/signing/verification is still counted. Independent
key generation also permits revealing the ECDSA secret key in this SLH-only
security experiment, provided doing so does not reveal SLH secrets or
change the honest SLH approval policy. This is useful for the intended
quantum threat model because P-384 does not withstand Shor's algorithm [S6].

If independent symmetric reductions to both components are justified in
their respective models, one can upper-bound the composite advantage by
the minimum of those two component bounds at their own resource counts.
There is no product-of-advantages rule and no addition of security-bit
labels. The event of breaking both need not have independent probability.

An OR verifier does not satisfy (H): an accepted ECDSA-only component need
not provide any SLH signature. A policy that changes to ECDSA-only on SLH
failure has the same problem. The structural tests include this negative
control without attacking either real signature algorithm.

## 4. Lift the projection into the quorum reduction

Retain the previous explicit premises, now for SLH:

1. Sixty-four independent correctly distributed SLH keypairs with duplicate
   public-key abort; public setup and any auxiliary keys are simulatable
   without the selected target SLH secret key. Corruptions reveal locally
   generated secrets, and corrupting the selected target aborts the reduction.
2. A QPT adversary with classical signing queries in one specified hash model.
   Pure-mode signing behavior and randomness match the primitive challenger.
3. A total corruption set C, including every seat ever corrupted through the
   end of extraction, with |C| <= f <= 21.
4. An oracle-respecting extractor producing two valid full witnesses, each
   implying 43 distinct registered seats and their verified SLH approvals.
   For hybrid witnesses it first validates the mandatory ECDSA components;
   the signature projection then retains the SLH component of each row.
5. Persistent honest authorization of only one direct message for each
   configuration/domain slot. All approval-namespace SLH calls enforce this
   policy. Other key uses cannot bypass it through an unfiltered raw API.
6. A complete, monotone raw SLH query log, across all contexts and all extractor
   branches. Authorization state also cannot be rolled back to sign conflicting
   values in different branches. No target secret key, inverse signing oracle,
   or incompatible random-oracle programming is supplied to the extractor.

Let E be successful extraction and F the set of never-corrupted seats with
a valid SLH signature on an unqueried (ctx,M) pair in either output witness.
Set F empty on malformed or nonconflicting outcomes and setup/extraction
failure. The selector checks all 86 rows, including both sides.

Inject the SU-SLH challenge at a hidden uniformly chosen seat J, generate
the other 63 SLH keys locally, and simulate all ancillary primitives locally
using independent secrets. On J in F, the target was not corrupted; forwarding
its signing calls creates the same distribution as the all-keys-known virtual
experiment. Since J is independent of that virtual view,

    Pr[SU-SLH forgery] = E[ |F| / 64 ].                       (A)

There is no proof-side guess, witness-row guess, message guess or extra
corruption-survival factor. The same reasoning applies to the hybrid after
projection (H); it introduces no additional multiplicative success loss.

Let BadBind mean that distinct bodies among the output bodies and every
body actually submitted to approval signing during extraction have equal
D38 digests. Set delta_B >= Pr[BadBind] in that extractor experiment.

For the two 43-seat signer sets S0,S1,

    |(S0 intersect S1) minus C| >= 2*43-64-f = 22-f.

Outside BadBind, if both output approvals for a common uncorrupted seat
were queried, signed-string equality and body binding would show that its
honest wrapper approved both conflicting direct messages. That contradicts
persistent authorization. Thus |F| >= 22-f on E and not BadBind, and

    Pr[E] <= delta_B + alpha epsilon_SLH,
    alpha = 64/(22-f) for adaptive corruption.                (B)

For a corrupt set of exact size f fixed and known before setup, selecting J
from its 64-f honest seats yields alpha=(64-f)/(22-f). At f=21 these losses
are 64 and 43 respectively. Neither value comes from the SLH tree dimensions.

Suppose the given compatible extractor satisfies

    Pr[E] >= (p-kappa_E)_+ / L_E,    L_E >= 1.

Then

    p <= kappa_E + L_E (delta_B + alpha epsilon_SLH).          (C)

For adaptive f<=21, use alpha=64. Body-binding failure stays inside L_E
because it is measured in the extractor experiment. A separately justified
outer setup/simulation-distance term can be added outside this expression;
none is estimated here. Changes to the witness's signature algorithm require
a matching upstream relation and extractor guarantee; the previous numerical
values of L_E and kappa_E are not silently inherited.

ML-KEM does not appear in (C). In this game KEM keys and computations can be
generated locally, and the signature reduction need not establish their
secrecy. This conclusion depends on key independence and on honest approval
decisions not being granted merely because a KEM session succeeded. If a
channel secret authorizes signing or can expose an SLH seed, the game changes
and this omission is no longer justified. OTBN similarly supplies no numeric
security term without a separate implementation/simulation claim.

## 5. What changes in the primitive proof route

The ML-DSA-specific lattice assumption is replaced by the hash-based SLH
endpoint. It does not disappear. A useful published modular decomposition is
Theorem 4 of Barbosa et al. [S8], schematically with the paper's own games:

    epsilon_SPHINCS+ <= epsilon_PRF(SKG) + epsilon_PRF(MKG)
                         + epsilon_EUF(M-FORS$)
                         + epsilon_EUF-NAGCMA(FL-SL-XMSSMT$). (D)

Theorem 1 further reduces M-FORS$ to ITSR, a tweakable-hash OpenPRE term,
and two distinct tweakable-hash TCR-C terms. These expose the concrete items
that need bounds. They are not interchangeable with ordinary collision
resistance. Theorem 2 bounds the relevant OpenPRE term by DSPR plus three
times TCR. The publication's formal verification concerns its defined games;
it is not a certificate for this code, OTBN firmware or our complete QPT game.

Hulsing and Kudinov [S7] provide the corrected SPHINCS+ proof and analyze
quantum query bounds for the relevant hash properties. Their abstract notes
an additional Winternitz-factor loss compared with an earlier flawed proof.
One must not use the old formula or append that factor a second time to a
bound that already includes it.

For a valid numerical substitution in (C), a proof still must match FIPS 205's
exact hash instantiations, address processing, randomness and pure-mode API
to the selected quantum security theorem; carry every query and target count;
and justify any step from ideal oracles to the actual SHAKE computation.
Equation (D) is a sourced partial-proof map, not an asserted QPT inequality
for FIPS 205 obtained simply by renaming epsilon_SPHINCS+ as epsilon_SLH.
No such unproved substitution is made in this artifact.

Resource counts include the extractor, 63 local SLH key generations, all
simulated non-target signing, up to 86 SLH verifications and the complete
oracle history. The hybrid additionally requires its ECDSA simulation and
verification. Total target signing queries cannot be replaced with the
average across 64 seats. Merely running on an accelerator changes costs,
not the definition of winning the signature game.

## 6. Validation

The file is self-contained: --explain prints this addendum and --self-test
runs structural tests. It retains the previous 23 reduction checks adapted
to the proposed SLH suite and adds tests for FIPS API order, pure-context
encoding, AND-versus-OR acceptance, component freshness, suite separation,
hybrid projection, mandatory ECDSA verification and component key framing.

All signature-validity test answers are supplied by explicit symbolic test
doubles. They exercise bookkeeping, byte framing and reduction logic.
They do not run SLH-DSA, ECDSA, ML-KEM or an OTBN simulator, and they do not
test quantum hardness. No earlier artifact in this domain is replaced.

## Sources and precise use

[S1] NIST FIPS 205, Algorithms 22/24 and Section 11; SLH-DSA interface and
parameter definition. https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf

[S2] NIST FIPS 203 publication page; KEM functionality.
https://csrc.nist.gov/pubs/fips/203/final

[S3] OpenTitan, Introduction to OTBN; P-384 operations and implementation role.
https://opentitan.org/book/hw/ip/otbn/doc/otbn_intro.html

[S4] OpenTitan OTBN technical specification; development-status qualification.
https://opentitan.org/book/hw/ip/otbn/index.html

[S5] lowRISC OpenTitan RFC #26846; accelerator strategy and SLH-DSA placement.
https://github.com/lowRISC/opentitan/issues/26846

[S6] Roetteler et al., Quantum resource estimates for computing elliptic curve
discrete logarithms (2017); quantum vulnerability of prime-field ECC.
https://arxiv.org/abs/1706.06752

[S7] Hulsing and Kudinov, Recovering the tight security proof of SPHINCS+,
ASIACRYPT 2022. Checked author abstract/metadata, not the inaccessible PDF.
https://eprint.iacr.org/2022/346

[S8] Barbosa et al., A Tight Security Proof for SPHINCS+, Formally Verified,
ASIACRYPT 2024 proceedings (2025), Theorems 1, 2 and 4. Full publisher paper
obtained from the authors' institutional repository:
https://pure.tue.nl/ws/portalfiles/portal/350450713/978-981-96-0894-2_2.pdf
https://eprint.iacr.org/2024/910

The suite identifiers, hybrid lemma (H), and protocol composition (A)-(C)
are proposed/derived here. The cited papers are not claimed to have proved
this quorum protocol. The signature-assumption replacement is established
conditionally; a numerical QPT-128 success or work-factor claim is not.


Path note. This file is domains/05-extraction-and-signature-reductions/src/slh_dsa_signature_reduction.py.
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
from fractions import Fraction
import hashlib

N = 64
QUORUM = 43
SUITE = b'CEQS38-SLH-S256S'
HYBRID_SUITE = b'CEQS38-HYB-S256S'
SUITES = (SUITE, HYBRID_SUITE)
PREFIX = b'CEQS38/VOTE/v1'
HEADER = 208
BODY_BYTES = HEADER + 128*QUORUM


class Rejected(ValueError):
    pass


class TargetCorrupted(RuntimeError):
    pass


class SetupAborted(RuntimeError):
    pass


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise Rejected('noncanonical integer')
    return value


def context_and_message(context, message):
    if type(context) is not bytes or len(context) > 255 or type(message) is not bytes:
        raise Rejected('pure SLH-DSA API requires byte context/message, context <=255 bytes')


@dataclass(frozen=True)
class Body:
    raw: bytes
    configuration: bytes
    domain: bytes
    message: bytes
    handles: tuple


def parse_body(raw):
    if type(raw) is not bytes or len(raw) != BODY_BYTES or raw[:16] not in SUITES:
        raise Rejected('wrong CEQS38 body framing')
    handles = tuple(raw[i:i+128] for i in range(HEADER, BODY_BYTES, 128))
    if any(a[:64] >= b[:64] for a,b in zip(handles, handles[1:])):
        raise Rejected('noncanonical handle ordering')
    return Body(raw, raw[16:80], raw[80:144], raw[144:208], handles)


def body_digest(raw):
    parts = (b'CEQS38/body', raw)
    framed = b''.join(len(p).to_bytes(8,'big')+p for p in parts)
    return hashlib.shake_256(framed).digest(64)


def approval_message(body, seat, position, digest=body_digest):
    """Proposed v1.38 external message; context is separately b''."""
    integer(seat, 0, N-1)
    integer(position, 0, QUORUM-1)
    h = digest(body.raw)
    if type(h) is not bytes or len(h) != 64:
        raise Rejected('body digest must be 64 bytes')
    return PREFIX+h+bytes([seat])+body.handles[position]


@dataclass(frozen=True)
class SignatureRow:
    seat: int
    position: int
    signature: bytes


@dataclass(frozen=True)
class SigningQuery:
    seat: int
    context: bytes
    message: bytes


@dataclass(frozen=True)
class ForgeryCandidate:
    seat: int
    side: int
    position: int
    context: bytes
    message: bytes
    signature: bytes


def registry_check(registry):
    if type(registry) is not tuple or len(registry) != N:
        raise Rejected('64 registry public keys required')
    if any(type(pk) is not bytes or not pk for pk in registry) or len(set(registry)) != N:
        raise Rejected('public keys must be distinct byte strings')
    # A real provider additionally enforces SLH-DSA-SHAKE-256s key/signature encodings.


def signature_projection(body, rows, registry, verify, digest=body_digest):
    """Validate only the signature projection implied by a valid full witness.

    verify is normalized: verify(pk, message, signature, context) -> bool.
    Native FIPS 205 order is (message, signature, context, pk); use the adapter.
    No trace-seed opening, registry authentication or proof extraction is done.
    """
    if type(rows) is not tuple or len(rows) != QUORUM:
        raise Rejected('43 signature rows required')
    h = digest(body.raw)
    def cached_digest(_raw):
        return h
    seats, positions = set(), set()
    result = []
    for row in rows:
        if type(row) is not SignatureRow:
            raise Rejected('canonical signature row required')
        integer(row.seat, 0, N-1)
        integer(row.position, 0, QUORUM-1)
        if row.seat in seats or row.position in positions:
            raise Rejected('repeated seat or handle position')
        if type(row.signature) is not bytes or not row.signature:
            raise Rejected('signature bytes required')
        seats.add(row.seat); positions.add(row.position)
        message = approval_message(body, row.seat, row.position, cached_digest)
        if verify(registry[row.seat], message, row.signature, b'') is not True:
            raise Rejected('invalid member approval signature')
        result.append((row, message))
    return tuple(result)


def fresh_candidates(body0, rows0, body1, rows1, registry, queries, corrupted,
                     verify, digest=body_digest):
    """Select actual fresh-message candidates from BOTH projected witnesses.

    queries must be the complete trusted record of forwarded pure-SLH-DSA
    signing queries for all roles/contexts. Its completeness is an experiment
    premise; this function cannot certify an externally supplied log. Queries
    from discarded or rewound extractor branches must remain in the record.
    corrupted includes every seat corrupted through the end of the game.
    """
    registry_check(registry)
    left, right = parse_body(body0), parse_body(body1)
    if left.raw[:16] != right.raw[:16]:
        raise Rejected('conflicting bodies must use the same registered suite')
    if (left.configuration, left.domain) != (right.configuration, right.domain):
        raise Rejected('different authorization slots')
    if left.message == right.message:
        raise Rejected('not conflicting direct messages')
    if type(corrupted) is not frozenset:
        raise Rejected('canonical corruption set required')
    for i in corrupted: integer(i, 0, N-1)
    if type(queries) is not tuple:
        raise Rejected('canonical complete query transcript required')
    queried = set()
    for q in queries:
        if type(q) is not SigningQuery:
            raise Rejected('canonical signing-query record required')
        integer(q.seat, 0, N-1)
        context_and_message(q.context, q.message)
        queried.add((q.seat, q.context, q.message))
    projections = (signature_projection(left, rows0, registry, verify, digest),
                   signature_projection(right, rows1, registry, verify, digest))
    candidates = []
    for side, projection in enumerate(projections):
        for row, message in projection:
            if row.seat not in corrupted and (row.seat, b'', message) not in queried:
                candidates.append(ForgeryCandidate(row.seat, side, row.position, b'', message, row.signature))
    return tuple(sorted(candidates, key=lambda c:(c.seat, c.side)))


def select_target(candidates, target):
    """No guess of side/row: scan for an existing fresh candidate at target."""
    integer(target, 0, N-1)
    return next((c for c in candidates if c.seat == target), None)


def safety_loss(*, users=N, quorum=QUORUM, faults=21, static_known=False):
    for v in (users, quorum, faults):
        if type(v) is not int: raise Rejected('integer parameters required')
    if not (1 <= quorum <= users and 0 <= faults < users):
        raise Rejected('invalid quorum parameters')
    if type(static_known) is not bool:
        raise Rejected('static_known must be Boolean')
    honest_overlap = 2*quorum-users-faults
    if honest_overlap <= 0:
        raise Rejected('no guaranteed honest quorum intersection')
    candidates = users-faults if static_known else users
    return Fraction(candidates, honest_overlap)


def composed_bound(*, extraction_error, extraction_loss, binding_error,
                   signature_advantage, identity_loss, setup_distance=Fraction(0)):
    """All probabilities exact; binding_error is in the EXTRACTOR experiment."""
    for p in (extraction_error, binding_error, signature_advantage, setup_distance):
        if type(p) is not Fraction or not 0 <= p <= 1:
            raise Rejected('probability must be an exact Fraction in [0,1]')
    for loss in (extraction_loss, identity_loss):
        if type(loss) is not Fraction or loss < 1:
            raise Rejected('loss must be an exact Fraction >=1')
    return min(Fraction(1), setup_distance+extraction_error+
               extraction_loss*(binding_error+identity_loss*signature_advantage))


class EmbeddingAdapter:
    """Single-user challenge embedding for a supplied signature implementation.

    This is a private REDUCTION interface for an oracle-respecting simulator,
    not an unrestricted signing API handed to the quorum adversary. The
    simulator must enforce honest authorization state and role separation.
    Its authorization state and this query log must not roll back across
    extractor branches; the challenger signing oracle cannot be rewound.
    Local keygen must match the challenger's distribution; signing modes must
    also match. The object does not run the missing extractor or a quantum VM.
    """
    def __init__(self, challenge_pk, challenge_sign, keygen, local_sign, target):
        integer(target, 0, N-1)
        if type(challenge_pk) is not bytes or not challenge_pk:
            raise Rejected('challenge public key required')
        self._target, self._challenge_sign, self._local_sign = target, challenge_sign, local_sign
        self._secret_keys, public_keys = {}, []
        for seat in range(N):
            if seat == target:
                public_keys.append(challenge_pk)
            else:
                pk, sk = keygen()
                public_keys.append(pk)
                self._secret_keys[seat] = sk
        self.registry = tuple(public_keys)
        try:
            registry_check(self.registry)
        except Rejected as exc:
            # The proved setup game also aborts on duplicate keys; it does not
            # silently condition/resample the registry distribution.
            raise SetupAborted(str(exc)) from exc
        self.queries = []
        self.corrupted = set()

    def sign(self, seat, context, message):
        integer(seat, 0, N-1)
        context_and_message(context, message)
        self.queries.append(SigningQuery(seat, context, message))
        if seat == self._target:
            return self._challenge_sign(context, message)
        return self._local_sign(self._secret_keys[seat], context, message)

    def corrupt(self, seat):
        integer(seat, 0, N-1)
        self.corrupted.add(seat)
        if seat == self._target:
            raise TargetCorrupted('abort: target secret key is unavailable')
        return self._secret_keys[seat]


class SymbolicSignatures:
    """Finite TEST DOUBLE, not SLH-DSA or any cryptographic signature scheme."""
    def __init__(self):
        self.valid = set()
        self.counter = 0

    def plant(self, pk, message, context=b''):
        # Models an already-available valid signature in a hypothetical witness.
        # Planting is never an operation available in the actual security game.
        self.counter += 1
        signature = b'SYMBOLIC-'+self.counter.to_bytes(8,'big')
        self.valid.add((pk, message, signature, context))
        return signature

    def verify(self, pk, message, signature, context):
        return (pk, message, signature, context) in self.valid


from dataclasses import replace
from itertools import combinations
import unittest
import sys
E = sys.modules[__name__]

CFG, DOMAIN = b'C'*64, b'D'*64


def synthetic_body(seats, message, cfg=CFG, domain=DOMAIN):
    # Framing only. These handles do NOT claim valid hidden trace openings.
    handles = [(i+1).to_bytes(64,'big')+b'Z'*64 for i in sorted(seats)]
    return E.SUITE+cfg+domain+message.to_bytes(64,'big')+b''.join(handles)


def fixture(faults=21, digest=E.body_digest):
    signatures = E.SymbolicSignatures()
    registry = tuple(b'pk-'+bytes([i]) for i in range(64))
    seats0, seats1 = set(range(43)), set(range(22)) | set(range(43,64))
    bodies = (synthetic_body(seats0,0), synthetic_body(seats1,1))
    corrupted = frozenset(range(faults))
    rows, queries = [], []
    for side, seats in enumerate((seats0, seats1)):
        body = E.parse_body(bodies[side])
        projected = []
        for pos, seat in enumerate(sorted(seats)):
            message = E.approval_message(body, seat, pos, digest)
            signature = signatures.plant(registry[seat], message)
            projected.append(E.SignatureRow(seat, pos, signature))
            # Common honest seats approved only body0. Unique honest seats
            # approved their only body. The second common signature is planted
            # as a hypothetical extracted forgery, NOT obtained by an attack.
            if seat not in corrupted and (side == 0 or seat not in seats0):
                queries.append(E.SigningQuery(seat, b'', message))
        rows.append(tuple(projected))
    return dict(bodies=bodies, rows=tuple(rows), registry=registry, queries=tuple(queries),
                corrupted=corrupted, signatures=signatures, digest=digest)


def candidates(f, **overrides):
    args = dict(body0=f['bodies'][0], rows0=f['rows'][0], body1=f['bodies'][1], rows1=f['rows'][1],
                registry=f['registry'], queries=f['queries'], corrupted=f['corrupted'],
                verify=f['signatures'].verify, digest=f['digest'])
    return E.fresh_candidates(**(args | overrides))


class ReductionTests(unittest.TestCase):
    def test_01_worst_case_single_honest_common_seat(self):
        f = fixture()
        got = candidates(f)
        self.assertEqual([(g.seat,g.side) for g in got], [(21,1)])
        self.assertEqual(got[0].signature, f['rows'][1][21].signature)
        self.assertEqual(got[0].context, b'')

    def test_02_exact_adaptive_target_probability(self):
        f = fixture()
        got = candidates(f)
        hits = sum(E.select_target(got, j) is not None for j in range(64))
        self.assertEqual(E.Fraction(hits,64), E.Fraction(1,64))
        self.assertEqual(E.safety_loss(), 64)

    def test_03_known_static_corruption_probability(self):
        f = fixture()
        got = candidates(f)
        eligible = set(range(64))-f['corrupted']
        hits = sum(E.select_target(got,j) is not None for j in eligible)
        self.assertEqual(E.Fraction(hits,len(eligible)), E.Fraction(1,43))
        self.assertEqual(E.safety_loss(static_known=True), 43)

    def test_04_all_fault_counts_and_multi_target_gain(self):
        for faults in range(22):
            f = fixture(faults)
            got = candidates(f)
            fresh_seats = {g.seat for g in got}
            self.assertEqual(fresh_seats, set(range(faults,22)))
            self.assertEqual(E.safety_loss(faults=faults), E.Fraction(64,22-faults))
            self.assertEqual(E.safety_loss(faults=faults, static_known=True),
                             E.Fraction(64-faults,22-faults))
            self.assertEqual(sum(E.select_target(got,j) is not None for j in range(64)), 22-faults)

    def test_05_selector_can_choose_either_side_without_guessing(self):
        f = fixture()
        body0, body1 = map(E.parse_body, f['bodies'])
        m0 = E.approval_message(body0,21,21)
        m1 = E.approval_message(body1,21,21)
        qs = tuple(q for q in f['queries'] if not(q.seat == 21 and q.message == m0))
        qs += (E.SigningQuery(21,b'',m1),)
        got = candidates(f, queries=qs)
        self.assertEqual([(g.seat,g.side) for g in got], [(21,0)])

    def test_06_new_signature_on_queried_message_is_not_EUF(self):
        f = fixture()
        row = f['rows'][1][21]
        message = E.approval_message(E.parse_body(f['bodies'][1]),21,21)
        original = f['signatures'].plant(f['registry'][21], message)
        self.assertNotEqual(original, row.signature)
        qs = f['queries']+(E.SigningQuery(21,b'',message),)
        self.assertEqual(candidates(f, queries=qs), ())

    def test_07_other_use_of_key_must_remain_in_raw_log(self):
        f = fixture()
        message = candidates(f)[0].message
        # A raw same-key query is disqualifying regardless of a caller's role label.
        qs = f['queries']+(E.SigningQuery(21,b'',message),)
        self.assertEqual(candidates(f, queries=qs), ())

    def test_08_external_context_is_part_of_freshness(self):
        f = fixture()
        message = candidates(f)[0].message
        qs = f['queries']+(E.SigningQuery(21,b'other-context',message),)
        self.assertEqual([(c.seat,c.context) for c in candidates(f, queries=qs)], [(21,b'')])

    def test_09_corruption_through_end_excludes_candidate(self):
        f = fixture()
        self.assertEqual(candidates(f, corrupted=f['corrupted']|{21}), ())
        with self.assertRaises(E.Rejected): E.safety_loss(faults=22)

    def test_10_signature_and_projection_tampering(self):
        f = fixture()
        base = f['rows'][1]
        for changed in (replace(base[21], signature=b'invalid'), replace(base[21], seat=20),
                        replace(base[21], seat=True), replace(base[21], position=20)):
            with self.assertRaises(E.Rejected):
                candidates(f, rows1=base[:21]+(changed,)+base[22:])
        with self.assertRaises(E.Rejected): candidates(f, rows1=base[:-1])

    def test_11_slot_and_conflict_checks(self):
        f = fixture()
        b = f['bodies'][1]
        for changed in (b[:16]+b'X'*64+b[80:], b[:80]+b'X'*64+b[144:],
                        b[:144]+b'\0'*64+b[208:], b[:-1], b+ b'\0'):
            with self.assertRaises(E.Rejected): candidates(f, body1=changed)

    def test_12_role_domain_separation_by_signed_bytes(self):
        f = fixture()
        message = candidates(f)[0].message
        qs = f['queries']+(E.SigningQuery(21,b'',b'CEQS29/TRANSPORT/v1'+message),)
        self.assertEqual(len(candidates(f,queries=qs)),1)

    def test_13_forced_body_hash_collision_blocks_freshness_bridge(self):
        f = fixture(digest=lambda _body: b'\0'*64)
        self.assertNotEqual(f['bodies'][0], f['bodies'][1])
        self.assertEqual(candidates(f), ())
        # This checks the projected signature relation only. It is not a
        # collision in SHAKE and not a valid full R29 proof or attack.

    def test_14_original_approval_bytes_and_cached_hashes(self):
        f = fixture()
        b = E.parse_body(f['bodies'][0])
        expected = E.PREFIX+E.body_digest(b.raw)+bytes([21])+b.handles[21]
        self.assertEqual(E.approval_message(b,21,21), expected)
        calls=[]
        def measured(raw): calls.append(raw); return E.body_digest(raw)
        candidates(f,digest=measured)
        self.assertEqual(calls, list(f['bodies']))

    def test_15_loss_factors_and_error_placement(self):
        F=E.Fraction
        got=E.composed_bound(extraction_error=F(1,10000), extraction_loss=F(3),
                             binding_error=F(1,100000), signature_advantage=F(1,1000000),
                             identity_loss=F(64), setup_distance=F(1,10000))
        self.assertEqual(got,F(1,10000)+F(1,10000)+3*(F(1,100000)+64*F(1,1000000)))
        wrong=F(1,10000)+F(1,10000)+F(1,100000)+3*64*F(1,1000000)
        self.assertNotEqual(got,wrong)

    def test_16_parameter_validation_and_clipping(self):
        for kwargs in ({'faults':True},{'faults':-1},{'quorum':65},{'static_known':1}):
            with self.assertRaises(E.Rejected): E.safety_loss(**kwargs)
        args=dict(extraction_error=E.Fraction(0),extraction_loss=E.Fraction(1),
                  binding_error=E.Fraction(0),signature_advantage=E.Fraction(1),identity_loss=E.Fraction(64))
        self.assertEqual(E.composed_bound(**args),1)
        with self.assertRaises(E.Rejected): E.composed_bound(**(args|{'signature_advantage':0.1}))

    def test_17_small_universe_quorum_intersections_exhaustive(self):
        for n,t,f in ((5,4,1),(6,4,1),(7,5,2)):
            universe=set(range(n))
            for s0 in combinations(range(n),t):
                for s1 in combinations(range(n),t):
                    common=set(s0)&set(s1)
                    for bad in combinations(range(n),f):
                        self.assertGreaterEqual(len(common-set(bad)),2*t-n-f)

    def test_18_exact_expected_fresh_fraction_without_independence(self):
        outcomes=((E.Fraction(1,3),frozenset({1})),
                  (E.Fraction(1,6),frozenset({1,2,3})),
                  (E.Fraction(1,2),frozenset()))
        expected=sum(prob*E.Fraction(len(fresh),64) for prob,fresh in outcomes)
        enumerated=sum(prob*sum(j in fresh for j in range(64))/64 for prob,fresh in outcomes)
        self.assertEqual(expected,enumerated)

    def test_19_embedding_forwards_only_target_queries(self):
        seen=[]; serial=[0]
        def keygen():
            serial[0]+=1; key=serial[0].to_bytes(2,'big'); return b'pk'+key,b'sk'+key
        def target_sign(ctx,msg): seen.append(('target',ctx,msg)); return b'target-sig'
        def local_sign(sk,ctx,msg): seen.append(('local',sk,ctx,msg)); return b'local-sig'
        adapter=E.EmbeddingAdapter(b'challenge-pk',target_sign,keygen,local_sign,21)
        self.assertEqual(serial[0],63)
        self.assertEqual(adapter.registry[21],b'challenge-pk')
        self.assertEqual(adapter.sign(21,b'',b'm0'),b'target-sig')
        self.assertEqual(adapter.sign(0,b'',b'm1'),b'local-sig')
        self.assertEqual(adapter.queries,[E.SigningQuery(21,b'',b'm0'),E.SigningQuery(0,b'',b'm1')])
        self.assertEqual(seen[0],('target',b'',b'm0'))
        self.assertEqual(seen[1][0],'local')

    def test_20_target_corruption_aborts_without_secret_key(self):
        serial=[0]
        def keygen(): serial[0]+=1; k=bytes([serial[0]]); return b'pk'+k,b'sk'+k
        adapter=E.EmbeddingAdapter(b'challenge',lambda c,m:b'sig',keygen,lambda s,c,m:b'sig',21)
        self.assertTrue(adapter.corrupt(0).startswith(b'sk'))
        with self.assertRaises(E.TargetCorrupted): adapter.corrupt(21)
        self.assertEqual(adapter.corrupted,{0,21})

    def test_21_duplicate_key_setup_aborts_without_resampling(self):
        calls=[]
        def keygen(): calls.append(1); return b'challenge',b'sk'
        with self.assertRaises(E.SetupAborted):
            E.EmbeddingAdapter(b'challenge',lambda c,m:b'sig',keygen,lambda s,c,m:b'sig',21)
        self.assertEqual(len(calls),63)

    def test_22_query_and_registry_canonicality(self):
        f=fixture()
        for query in (E.SigningQuery(True,b'',b'm'),E.SigningQuery(21,b'x'*256,b'm'),
                      E.SigningQuery(21,b'',bytearray(b'm'))):
            with self.assertRaises(E.Rejected): candidates(f,queries=f['queries']+(query,))
        with self.assertRaises(E.Rejected): candidates(f,registry=(f['registry'][0],)*64)
        with self.assertRaises(E.Rejected): candidates(f,corrupted=set(f['corrupted']))

    def test_23_discarded_branch_query_cannot_be_erased(self):
        f=fixture()
        alleged=candidates(f)[0]
        discarded_branch=E.SigningQuery(alleged.seat,alleged.context,alleged.message)
        complete=f['queries']+(discarded_branch,)
        self.assertEqual(candidates(f,queries=complete),())
        # An incomplete branch-local log falsely labels this as fresh. The
        # selector cannot recover missing oracle history from the witness.
        self.assertEqual(len(candidates(f,queries=f['queries'])),1)
        self.assertNotEqual(complete,f['queries'])


SLH_PK_BYTES = 64
SLH_SIG_BYTES = 29792
ECDSA_PK_BYTES = 97  # Canonical uncompressed SEC1 P-384 point.
ECDSA_SIG_BYTES = 96  # Fixed-width r || s; provider verifies ranges.


def pure_internal_message(context, message):
    """Injective FIPS pure-mode framing; not pre-applied to the native API."""
    context_and_message(context, message)
    return b'\x00'+bytes([len(context)])+context+message


def slh_verify_adapter(native_verify):
    """Normalize FIPS 205 slh_verify(M,SIG,ctx,PK) to the reduction callback.

    The supplied provider must implement SLH-DSA-SHAKE-256s verification.
    Length checks do not themselves establish validity.
    """
    def verify(pk, message, signature, context):
        try:
            context_and_message(context, message)
        except Rejected:
            return False
        if type(pk) is not bytes or len(pk) != SLH_PK_BYTES:
            return False
        if type(signature) is not bytes or len(signature) != SLH_SIG_BYTES:
            return False
        return native_verify(message, signature, context, pk) is True
    return verify


@dataclass(frozen=True)
class HybridPublicKey:
    slh: bytes
    ecdsa: bytes


@dataclass(frozen=True)
class HybridSignature:
    slh: bytes
    ecdsa: bytes


def hybrid_verify(key, message, signature, context, native_slh_verify, ecdsa_verify):
    """Both components are mandatory, using one authenticated key bundle.

    ecdsa_verify(pk, framed_message, signature) must do full ECDSA-P384
    verification with SHA-384, hashing framed_message exactly once.
    This routine does not authenticate key registration or negotiate suites.
    """
    if type(key) is not HybridPublicKey or type(signature) is not HybridSignature:
        return False
    if type(key.ecdsa) is not bytes or len(key.ecdsa) != ECDSA_PK_BYTES or key.ecdsa[:1] != b'\x04':
        return False
    if type(signature.ecdsa) is not bytes or len(signature.ecdsa) != ECDSA_SIG_BYTES:
        return False
    verify_slh = slh_verify_adapter(native_slh_verify)
    if not verify_slh(key.slh, message, signature.slh, context):
        return False
    return ecdsa_verify(key.ecdsa, pure_internal_message(context, message), signature.ecdsa) is True


def project_hybrid_forgery(key, message, signature, context, slh_query_log,
                           native_slh_verify, ecdsa_verify):
    """Return the unchanged fresh SLH component, or None.

    slh_query_log contains every (context,message) call under this SLH key,
    including component-only calls and discarded extractor branches.
    """
    if type(slh_query_log) is not tuple:
        raise Rejected('complete immutable SLH query record required')
    seen = set()
    for query in slh_query_log:
        if type(query) is not tuple or len(query) != 2:
            raise Rejected('context/message pair required')
        context_and_message(*query)
        seen.add(query)
    if not hybrid_verify(key, message, signature, context, native_slh_verify, ecdsa_verify):
        return None
    if (context, message) in seen:
        return None
    return (key.slh, message, signature.slh, context)


class ReplacementTests(unittest.TestCase):
    """Test fixtures of component validity, not actual cryptographic signatures."""
    def setUp(self):
        self.pk = HybridPublicKey(b'P'*SLH_PK_BYTES, b'\x04'+b'E'*96)
        self.sig = HybridSignature(b'S'*SLH_SIG_BYTES, b'C'*ECDSA_SIG_BYTES)
        self.message, self.context = b'CEQS38/VOTE/v1-fixture', b''
        self.native_calls, self.ec_calls = [], []

    def native(self, message, signature, context, pk):
        self.native_calls.append((message,signature,context,pk))
        return (message,signature,context,pk)==(self.message,self.sig.slh,self.context,self.pk.slh)

    def ecdsa(self, pk, message, signature):
        self.ec_calls.append((pk,message,signature))
        return (pk,message,signature)==(self.pk.ecdsa,pure_internal_message(self.context,self.message),self.sig.ecdsa)

    def test_24_native_api_order_and_no_double_framing(self):
        verifier=slh_verify_adapter(self.native)
        self.assertTrue(verifier(self.pk.slh,self.message,self.sig.slh,self.context))
        self.assertEqual(self.native_calls,[(self.message,self.sig.slh,self.context,self.pk.slh)])
        self.assertNotEqual(self.native_calls[0][0],pure_internal_message(self.context,self.message))

    def test_25_context_encoding_is_injective_on_small_domain(self):
        contexts=(b'',b'a',b'ab',b'\x00')
        messages=(b'',b'b',b'ab',b'\x00')
        encoded={pure_internal_message(c,m) for c in contexts for m in messages}
        self.assertEqual(len(encoded),len(contexts)*len(messages))
        self.assertEqual(pure_internal_message(b'',b'm'),b'\x00\x00m')
        with self.assertRaises(Rejected): pure_internal_message(b'x'*256,b'm')

    def test_26_and_requires_both_components(self):
        for slh_ok in (False,True):
            for ec_ok in (False,True):
                accepted=hybrid_verify(self.pk,self.message,self.sig,b'',
                                       lambda *a:slh_ok,lambda *a:ec_ok)
                self.assertEqual(accepted,slh_ok and ec_ok)

    def test_27_or_has_no_slh_projection_guarantee(self):
        slh_ok, ec_ok=False,True
        self.assertTrue(slh_ok or ec_ok)  # Negative-control policy only.
        self.assertFalse(hybrid_verify(self.pk,self.message,self.sig,b'',
                                       lambda *a:slh_ok,lambda *a:ec_ok))

    def test_28_fresh_projection_preserves_slh_signature(self):
        got=project_hybrid_forgery(self.pk,self.message,self.sig,b'',(),self.native,self.ecdsa)
        self.assertEqual(got,(self.pk.slh,self.message,self.sig.slh,b''))
        self.assertIs(got[2],self.sig.slh)
        self.assertEqual(self.ec_calls[0][1],pure_internal_message(b'',self.message))

    def test_29_component_only_query_disqualifies_forgery(self):
        complete=((b'',self.message),)
        self.assertIsNone(project_hybrid_forgery(self.pk,self.message,self.sig,b'',complete,
                                                self.native,self.ecdsa))

    def test_30_other_context_does_not_erase_freshness(self):
        got=project_hybrid_forgery(self.pk,self.message,self.sig,b'',((b'other',self.message),),
                                   self.native,self.ecdsa)
        self.assertIsNotNone(got)

    def test_31_p384_component_cannot_bypass_invalid_slh(self):
        self.assertIsNone(project_hybrid_forgery(self.pk,self.message,self.sig,b'',(),
                                                lambda *a:False,lambda *a:True))

    def test_32_component_encodings_and_bad_contexts(self):
        changed_keys=(replace(self.pk,slh=b'bad'),replace(self.pk,ecdsa=b'\x03'+b'E'*96))
        changed_sigs=(replace(self.sig,slh=b'bad'),replace(self.sig,ecdsa=b'bad'))
        for key in changed_keys:
            self.assertFalse(hybrid_verify(key,self.message,self.sig,b'',lambda *a:True,lambda *a:True))
        for sig in changed_sigs:
            self.assertFalse(hybrid_verify(self.pk,self.message,sig,b'',lambda *a:True,lambda *a:True))
        self.assertFalse(hybrid_verify(self.pk,self.message,self.sig,b'x'*256,lambda *a:True,lambda *a:True))

    def test_33_legacy_and_mixed_suites_rejected(self):
        f=fixture()
        old=b'CEQS29-M87-K1024'+f['bodies'][0][16:]
        with self.assertRaises(Rejected): parse_body(old)
        mixed=HYBRID_SUITE+f['bodies'][1][16:]
        with self.assertRaises(Rejected): candidates(f,body1=mixed)

    def test_34_hybrid_suite_slh_projection_uses_exact_new_messages(self):
        f=fixture()
        bodies=tuple(HYBRID_SUITE+b[16:] for b in f['bodies'])
        symbolic=SymbolicSignatures()
        newrows=[]; queries=[]
        for side in (0,1):
            body=parse_body(bodies[side]); rows=[]
            for row in f['rows'][side]:
                msg=approval_message(body,row.seat,row.position)
                sig=symbolic.plant(f['registry'][row.seat],msg)
                rows.append(replace(row,signature=sig))
                if row.seat not in f['corrupted'] and (side==0 or row.seat>=43):
                    queries.append(SigningQuery(row.seat,b'',msg))
            newrows.append(tuple(rows))
        got=fresh_candidates(bodies[0],newrows[0],bodies[1],newrows[1],f['registry'],
                             tuple(queries),f['corrupted'],symbolic.verify)
        self.assertEqual([(c.seat,c.side) for c in got],[(21,1)])
        self.assertNotEqual(got[0].message,candidates(f)[0].message)
        # This validates only the SLH projection of a hypothetical hybrid
        # witness; full mandatory ECDSA checks remain the caller's obligation.

    def test_35_honest_slh_component_suffices_even_when_ec_is_unrestricted(self):
        # A callback accepting every ECDSA token models a broken component.
        # It cannot make an invalid SLH component pass the AND verifier.
        self.assertTrue(hybrid_verify(self.pk,self.message,self.sig,b'',self.native,lambda *a:True))
        bad=replace(self.sig,slh=b'X'*SLH_SIG_BYTES)
        self.assertFalse(hybrid_verify(self.pk,self.message,bad,b'',self.native,lambda *a:True))

    def test_36_queries_must_be_canonical_and_checks_exact_booleans(self):
        with self.assertRaises(Rejected):
            project_hybrid_forgery(self.pk,self.message,self.sig,b'',((b'',),),self.native,self.ecdsa)
        self.assertFalse(hybrid_verify(self.pk,self.message,self.sig,b'',lambda *a:1,lambda *a:True))


def main():
    import argparse
    parser=argparse.ArgumentParser(description='SLH-DSA replacement and P-384 AND-hybrid: conditional proof and symbolic structural tests.')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--explain',action='store_true',help='Print the proof, assumptions and source map.')
    mode.add_argument('--self-test',action='store_true',help='Run symbolic tests; no real signatures or OTBN operations.')
    args=parser.parse_args()
    if args.explain:
        print(__doc__)
        return 0
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c)
                             for c in (ReductionTests,ReplacementTests))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    raise SystemExit(main())
