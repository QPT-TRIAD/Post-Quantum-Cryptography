#!/usr/bin/env python3
r"""
# R29 signature-security reduction — v1.37

Scope: signature conversion only. Date: 2026-09-10.

This document proves a conditional reduction from two extracted conflicting
R29 authorization witnesses to ordinary, fresh-message ML-DSA-87 forgery.
The reference code implements the signature projection, freshness selector,
challenge-key adapter and exact loss arithmetic. It does not implement the
upstream extractor. The tests use symbolic signatures, not ML-DSA signatures.
This is a written mathematical proof with executable structural checks, not a
proof-assistant formalization or a numerical QPT-128 certification.

The main result for 64 seats, quorums of 43, and at most 21 adaptively corrupted
seats is

    p <= kappa_E + L_E (delta_B + 64 epsilon_87).                 (1)

Here extraction and body binding are explicit input premises, and epsilon_87
is a single-user ML-DSA-87 EUF-CMA advantage at the reduction's actual resources.
No proof-side, witness-row or signing-query-index guess is necessary.

## 1. Freeze the signed bytes and the signature endpoint

The recorded R29 public body B has these canonical fields, in order:

    suite: b'CEQS29-M87-K1024' (16 bytes)
    configuration: 64 bytes
    conflict domain: 64 bytes
    direct message m: 64 bytes
    43 handles h=(L,Z), each 128 bytes, strictly sorted by L.

The framing is used only to identify the exact current signed message. This
document makes no compactness or total-certificate-size claim.

For byte strings p_1,...,p_k define

    Frame(p_1,...,p_k) = concat_j (BE64(len(p_j)) || p_j),
    D(B) = SHAKE256(Frame(b'CEQS29/body', B), output_length=64 bytes).

For seat i in {0,...,63}, with its witness-selected handle h_i(B), the exact
external approval message is

    M_i(B) = b'CEQS29/VOTE/v1' || D(B) || byte(i) || h_i(B).

Approval verification is the pure FIPS 204 interface

    ML-DSA-87.Verify(pk_i, M_i(B), sigma_i, ctx=b'') = true.

HashML-DSA is a different API and is not substituted for this interface. The
body digest is application data inside the external pure-mode message. The
signature provider must use the same key-generation distribution, pure-mode
message/context handling, signing-randomness policy and validation behavior
in the simulated game and in its EUF-CMA challenger.
Only this pure-mode signing interface is available under these keys. Exposing
HashML-DSA or internal signing entry points under the same key changes the
game and requires an additional interface-composition argument.

Define SU-EUF-CMA for this interface: the challenger samples a key, gives the
public key to a quantum polynomial-time adversary, and answers classical
signing queries (ctx,M). The adversary wins by returning (ctx*,M*,sigma*) that
verifies and for which (ctx*,M*) was never submitted to the signing oracle.
Each signing query counts even if its response is later discarded. An output
with a new sigma on an already queried (ctx,M) is not a win. Strong
unforgeability is unnecessary for this reduction.

Write epsilon_87 = Adv_SU-EUF-CMA^ML-DSA-87(resources, model) for an upper bound
on this winning probability. The model must say whether internal hash access
is concrete or idealized, and supply any quantum oracle access consistently.
This argument does not convert one model into the other. It uses no
superposition signing oracle and proves no security for one.

## 2. Exact input experiment and authorization premises

An execution begins with 64 independent, correctly distributed ML-DSA-87
keypairs. If any public keys coincide, the modeled setup aborts. It does not
resample until the registry is unique. Registration and public setup must be
simulatable for an injected challenge public key without its secret key,
using only local randomness, public data and allowed signing-oracle calls.
No secret-key-dependent enrollment proof is silently assumed simulatable.
Arbitrary adversarial key registration and a differently conditioned key
sampler require their own setup argument; they are not covered here.

Let the set C contain every seat corrupted through the end of the execution.
For the safety result assume |C| <= f <= 21. The bound is on total corruptions,
not just simultaneous corruptions. There is no forward-security claim.

For each seat never corrupted, the honest approval wrapper maintains a
persistent choice for each (configuration, conflict-domain) slot. It signs
approvals only for one direct m value in that slot. It may sign multiple
bodies with the same m. Every approval-namespace request is governed by this
state. Other uses of the same pure-mode signing key must have disjoint signed
byte namespaces, or otherwise be covered by an equally strong restriction.
A caller-supplied role label is not domain separation. In particular, an
unrestricted raw signing endpoint for approval bytes invalidates this
authorization-to-freshness bridge, even though EUF-CMA itself allows raw
chosen-message queries.

The trusted global query record Q contains all submitted (i,ctx,M) triples:
every use of every key, every context, and every extractor branch. The
reference selector consumes Q but cannot verify that an externally supplied
log is complete. A separate body record records each canonical B submitted
through the approval wrapper; this is used to define the binding event.

The upstream extractor experiment returns either failure or two exact
accepted bodies and valid full witnesses for the same configuration and
domain but different direct messages m_0 != m_1. Each witness must imply 43
distinct registered seat indices, all 43 handle positions, and valid
approvals on the exact messages above. The code checks only this signature
projection; trace openings, registry authentication and proof validity are
upstream obligations, not established by the projection checker.

The required extractor is oracle-respecting and authorization-consistent:

* It can run when one secret key is absent and signing for that key is served
  by the SU challenger. It cannot demand that secret key, inverse signing
  access, a rewind of the signing oracle, or unauthorized oracle programming.
* The log Q is monotone across its entire run, including discarded branches.
  Honest authorization state also remains monotone across all actual signing
  calls. An alternative extractor making no new signing queries can satisfy
  this condition using the unchanged original history.
* All auxiliary oracles and the challenge-key setup remain compatible with
  the chosen SU security model. The challenge seat is private simulator state.

An existential statement that witnesses can be extracted does not alone
establish these interface properties. They are assumptions on the input to
this reduction. If a rewinding extractor signs m_0 in one branch and m_1 in
another, both signatures were queried and ordinary EUF-CMA gives no forgery;
forgetting the discarded branch is not a valid repair.

## 3. Fresh-target selection and the exact embedding lemma

For an execution with valid conflicting projected witnesses, define

    F = {i not in C : a row for i in either witness has a valid signature
                     and (i,b'',M_i(B_side)) not in Q}.

Set F empty on setup abort, extraction failure, malformed projections or a
nonconflicting pair. F contains distinct seats, not rows. The selector examines
both witnesses and all 86 rows. It need not restrict itself to the intersection.

Reduction B_SU operates as follows:

1. Choose J uniformly from the 64 seats, independently of all game randomness.
   Place the challenger public key at J and generate the other 63 keypairs
   locally. Perform the same duplicate-key abort as the modeled setup.
2. Run the given compatible experiment/extractor once. Enforce the wrapper
   and global logging rules. Forward signing for J to the challenger and
   sign locally for other seats. Reveal local keys on permitted corruptions.
   If J is corrupted, abort the reduction.
3. After extraction, validate the projected signatures and form the fresh
   candidate list from both witnesses and the complete Q. If it contains a
   candidate at J, return its exact (b'',M,sigma); otherwise output failure.

Lemma. For the virtual experiment defined above,

    Pr[B_SU wins] = E[ |F| / 64 ].                             (2)

Proof. Consider a virtual run that knows all 64 keys and chooses the label J
independently. Identically distributed key generation and signing mean that
J is statistically independent of the experiment's observable view and hence
of the resulting F. The virtual sampler includes setup aborts, on which F is
empty. Conditional on the entire virtual outcome, the probability J is in F
is exactly |F|/64.

Couple the actual embedded execution to this virtual run up to its first
target-corruption request. On every outcome with J in F, J was never
corrupted, so that abort never occurs. The target signatures have been
supplied by the challenge signing oracle with the correct distribution; the
remaining simulation is the same. The selector returns a verified signature
at J whose context/message pair is absent from the complete challenge query
history, which is precisely an SU-EUF-CMA win. Conversely, this reduction
returns a forgery only from such a candidate. This proves (2).

This coupling applies to quantum adversaries as well: it replaces classical
signing responses with identically distributed responses and preserves the
specified quantum oracle interface. It does not clone or rewind a quantum
state. An extractor needing more oracle access is outside the lemma.

Consequently, for any event G on which |F| >= h > 0,

    Pr[G] <= (64/h) epsilon_87.                               (3)

There is no assumption that seat failures are independent. Target-corruption
aborts are already accounted for by J in F; an extra survival factor must
not be multiplied in. A direct multi-user forgery endpoint can return
(i,b'',M,sigma) with no identity guess. The improved 64/h conversion uses
possession of h fresh-target forgeries and is not a general improvement to
the usual single-output multi-user-to-single-user bound.

## 4. From an extracted conflict to many fresh targets

Let E be successful full extraction of two conflicting accepted bodies and
witnesses. For their signer sets S_0,S_1,

    |S_0 intersect S_1| >= |S_0| + |S_1| - 64 = 22,
    |(S_0 intersect S_1) minus C| >= 22-f =: h.

Define BadBind in this same extractor experiment: among the two output
bodies and every body passed to approval signing during the complete run,
there exist unequal bodies B,B' with D(B)=D(B'). Let

    delta_B >= Pr[BadBind].

An upper bound on Pr[E and BadBind] would also suffice. No numerical value
for this term is supplied here. The code's concrete SHAKE evaluation is not
a proof of collision resistance or of an ideal-to-concrete hash connection.

Lemma. On E and not BadBind, every uncorrupted common seat belongs to F.

Proof. Fix such a seat i. Suppose neither of its two extracted approvals is
fresh. Both exact (b'',M_i(B_j)) pairs were submitted under its key. By the
namespace premise each matching request was an approval-wrapper request for
some canonical body B'_j. Equality of the signed strings gives
D(B'_j)=D(B_j). Absence of BadBind gives B'_j=B_j. Thus the honest wrapper
actually approved both distinct m_0 and m_1 in the same slot. This contradicts
its persistent authorization rule. At least one approval is therefore fresh.
The argument holds for all h common uncorrupted seats simultaneously.

Combining the lemmas,

    Pr[E] <= delta_B + (64/(22-f)) epsilon_87.                 (4)

Body binding is needed because configuration, domain and m appear in the
approval only through D(B). It cannot be replaced by the claim that distinct
bodies are automatically distinct signed messages. This proof does not
require any trace-tag or mask collision term: the seat indices and approval
signatures already come from the extracted witness. Public attribution to a
particular victim, if claimed, remains an upstream statement.

## 5. Identity losses for different corruption games

For two t-seat quorums among N seats with total corruption cap f and
h=2t-N-f>0, the adaptive result is alpha=N/h.

If the exact corrupt set of size f is fixed and known to the reduction before
key generation, choose J uniformly among its N-f eligible honest seats. The
same proof gives alpha=(N-f)/h. This smaller denominator is not available
merely because an adaptively chosen final corrupt set can be observed later.

    f        h       adaptive alpha       known-static alpha
    0       22            32/11                  32/11
   20        2               32                     22
   21        1               64                     43

For a victim i* designated before setup, if the event being bounded explicitly
requires i* to remain uncorrupted and occur in both extracted witnesses,
embed at i* directly: its identity loss is 1. A victim chosen after key
generation generally brings back the identity guess unless a stronger
multiplicity statement applies. When f>=22, quorum intersection alone gives
no guaranteed honest common seat; do not reuse the safety bound there.

## 6. Compose with, but do not prove, the extractor guarantee

Let p be the outer safety-event probability in the modeled setup. Suppose
the given compatible extractor comes with the quantitative guarantee

    p_E := Pr[E] >= (p-kappa_E)_+ / L_E,
    with L_E >= 1 and 0 <= kappa_E <= 1.

For p<=kappa_E the claim is immediate. Otherwise combine this inequality
with (4) and rearrange:

    p <= kappa_E + L_E (delta_B + alpha epsilon_87).           (5)

Here delta_B is measured after running the extractor, so it is multiplied by
L_E. Moving it outside L_E without a separate argument is incorrect.

If a separate outer-experiment comparison establishes distance Delta_setup
between the real setup and the modeled setup, then

    p_real <= min(1, Delta_setup + kappa_E
                        + L_E (delta_B + alpha epsilon_87)). (6)

No such setup distance is estimated in this document. For the exact modeled
setup Delta_setup=0. For f<=21 adaptive corruption use alpha=64; for the
known static set of size 21 use alpha=43. These are worst-case bounds; the
exact average in (2) can be better when extraction yields more fresh seats.

## 7. Resource accounting and the remaining primitive assumption

The conversion runs the assumed extractor once. Its explicit overhead is
63 local key generations, local signing for non-target seats, at most 86
signature verifications, two cached body-digest evaluations for the output
pair, and indexing/scanning the full query record and candidate list. Honest
wrapper validation and prior body hashes also count wherever performed.

The challenge signing-query bound q_S* counts all forwarded calls for J,
including other roles, contexts and extractor branches. A worst-case per-seat
bound or the total-query bound is valid. Dividing total queries by 64 is not
a valid worst-case bound. All local quantum/classical computation, shared
oracle queries and any extractor overhead must be included in resources.
If oracle calls were unit-cost in the extractor statement, add the actual
local KeyGen/Sign/Verify costs when instantiating a computational time bound.

The result establishes a protocol-to-signature-assumption reduction.
It does not assign epsilon_87=2^-128. Such a concrete assignment requires an
applicable ML-DSA-87 theorem, its complete losses and exact resource limits in
the chosen model. A NIST security category, a generic Grover recurrence or a
theorem for different Dilithium parameters does not supply that assignment.
If an external analysis supplied epsilon_87<=2^-b, this conversion alone
would contribute at most 2^(6-b) in the f=21 adaptive case before extraction
losses and additive terms. That is probability-budget arithmetic, not a
quantum attack-cost estimate or a proof of a 128-bit work factor.

## 8. Validation and limits of the reference implementation

Run this file with --self-test for the 23 deterministic test groups, or with
--explain to print this proof. The test suite checks exact current approval
bytes, selecting either side without guessing, EUF versus strong-EUF
freshness, context separation, all same-key query uses, corruption exclusions,
known-static/adaptive loss factors, malformed projections, exhaustive small
quorum intersections, exact probability and composition arithmetic, target
oracle forwarding, target-corruption aborts, duplicate-key setup aborts,
and retained queries from discarded branches.

A deliberately constant body digest is a negative control: in the synthetic
signature projection, two conflicting bodies can reuse already queried
messages and leave no fresh forgery. It is not a SHAKE collision or an attack
on the full R29 relation. Synthetic handles do not assert valid trace openings.
The SymbolicSignatures.plant test method supplies a hypothetical valid
extracted signature; it is not an operation in the actual security game.

The supplied EmbeddingAdapter is a private reduction component. Do not expose
its raw signing dispatcher to the quorum adversary. The simulator must enforce
the authorization premises and maintain all branch history. Production
providers must supply real FIPS-compliant key and signature validation.
No actual ML-DSA implementation or quantum adversary is exercised by these
tests. Passing them validates the finite reduction bookkeeping, not the
hardness assumption, full witness relation or upstream extraction guarantee.

## 9. Primary-source boundaries

[S1] NIST, FIPS 204, Module-Lattice-Based Digital Signature Standard (2024).
https://csrc.nist.gov/pubs/fips/204/final
https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.204.pdf
Used for the ML-DSA interface and distinction between pure and prehash modes.
The publication page states that ML-DSA is believed secure against quantum
adversaries; this document does not turn that statement into a numerical
SU-EUF-CMA advantage. The page currently flags potential-update errata.

[S2] Barbosa et al., Fixing and Mechanizing the Security Proof of Fiat-Shamir
with Aborts and Dilithium, Cryptology ePrint 2023/246.
https://eprint.iacr.org/2023/246
The authors identify a gap in earlier CMA-to-NMA arguments and provide
corrected ROM/QROM proofs and a concrete Dilithium analysis. The abstract
and metadata were checked. No theorem formula from this paper is copied
or asserted to instantiate final FIPS ML-DSA-87 parameters here.

[S3] Jackson, Miller and Wang, Evaluating the security of CRYSTALS-Dilithium
in the quantum random oracle model, arXiv:2312.16619v2 (2024).
https://arxiv.org/pdf/2312.16619
The paper relates SelfTargetMSIS to MLWE under additional parameter
conditions and proposes corresponding parameter sets. Its introduction also
flags omitted terms and the corrected earlier proof. It is not used as an
automatic numerical bound for the exact deployed ML-DSA-87 instance.

Equations (2)-(6), the R29-specific freshness bridge and the code are the
derivations in this artifact. The references justify the endpoint and the
limits on importing primitive security claims; they are not citations for
an already published proof of this whole R29 construction.


Path note. This file is domains/05-extraction-and-signature-reductions/src/signature_security_reduction.py.
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
SUITE = b'CEQS29-M87-K1024'
PREFIX = b'CEQS29/VOTE/v1'
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
        raise Rejected('pure ML-DSA API requires byte context/message, context <=255 bytes')


@dataclass(frozen=True)
class Body:
    raw: bytes
    configuration: bytes
    domain: bytes
    message: bytes
    handles: tuple


def parse_body(raw):
    if type(raw) is not bytes or len(raw) != BODY_BYTES or raw[:16] != SUITE:
        raise Rejected('wrong CEQS29 body framing')
    handles = tuple(raw[i:i+128] for i in range(HEADER, BODY_BYTES, 128))
    if any(a[:64] >= b[:64] for a,b in zip(handles, handles[1:])):
        raise Rejected('noncanonical handle ordering')
    return Body(raw, raw[16:80], raw[80:144], raw[144:208], handles)


def body_digest(raw):
    parts = (b'CEQS29/body', raw)
    framed = b''.join(len(p).to_bytes(8,'big')+p for p in parts)
    return hashlib.shake_256(framed).digest(64)


def approval_message(body, seat, position, digest=body_digest):
    """Exact recorded v1.29 external message; context is separately b''."""
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
    # A real provider additionally enforces ML-DSA-87 key/signature encodings.


def signature_projection(body, rows, registry, verify, digest=body_digest):
    """Validate only the signature projection implied by a valid full witness.

    verify uses FIPS order: verify(pk, message, signature, context) -> bool.
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

    queries must be the complete trusted record of forwarded pure-ML-DSA
    signing queries for all roles/contexts. Its completeness is an experiment
    premise; this function cannot certify an externally supplied log. Queries
    from discarded or rewound extractor branches must remain in the record.
    corrupted includes every seat corrupted through the end of the game.
    """
    registry_check(registry)
    left, right = parse_body(body0), parse_body(body1)
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
    """Finite TEST DOUBLE, not ML-DSA or any cryptographic signature scheme."""
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


# Executable structural validation (symbolic signatures only).
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


def main():
    import argparse
    parser = argparse.ArgumentParser(description='R29 signature-only reduction: conditional proof and structural tests.')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--explain', action='store_true', help='Print the mathematical proof and assumptions.')
    mode.add_argument('--self-test', action='store_true', help='Run symbolic structural tests; no real ML-DSA operations.')
    args = parser.parse_args()
    if args.explain:
        print(__doc__)
        return 0
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReductionTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
