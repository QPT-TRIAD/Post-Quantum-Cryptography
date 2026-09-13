#!/usr/bin/env python3
r"""Joint witness extraction, v1.35: a conditional joint-lift proof and driver.

Result: the TWO-OUTPUT composition step can be proved for the particular
terminal-database commit-and-open extractor described below. Both witnesses
come from one adversary execution and one final database measurement. This
removes the need to ASSUME an additional multiplicative joint-extraction loss
once that backend's hypotheses have actually been established.

This does NOT implement a quantum compressed oracle or the missing full R29
proof protocol. The executable code is a classical orchestration driver with
test doubles. Its tests do not certify QPT security. The remaining concrete
object is the special-soundness witness decoder for a proof of the full R29
relation, together with a matching prover/verifier and proof of its hypotheses.

Run:
  python3 joint_extractor_lift.py --self-test
  python3 joint_extractor_lift.py --explain
Only Python's standard library is required. There is no deployment mode.

Target and premises

The visible project record defines R29(B,w) using 43 distinct registry seats,
each seat's trace-seed opening, the handle computed from that same seat and
seed, and that seat's valid approval signature on the canonical body, index,
and own handle. A witness has all 43 (index, seed, signature) rows. Two public
conflict-tracing identities are not two such witnesses.

For the theorem below, FIX ONE protocol Pi for a fixed polynomial-time relation
R. All its statement data, including any configuration/registry binding needed
by R, must enter the canonical instance. Its Fiat-Shamir proof verifier must
be the exact classical verifier to which the backend theorem applies.

Assume these concrete backend properties:

  P1. Oracle queries use a single quantum-accessible ideal random function H
      with h-bit outputs and the protocol's canonical disjoint encodings.
      The reduction simulates H by the exact compressed-oracle construction.
      All H-dependent setup and auxiliary services are generated within the
      charged experiment; no free H-dependent advice is supplied.

  P2. After the adversary finishes, the two verifiers are classical. Together
      they make at most v=v0+v1 oracle calls. They return both verdicts, even
      when the first proof is rejected. Q bounds ALL oracle calls through the
      end of those verifiers, including setup, adversary, and auxiliary-service
      calls. Q is not just the adversary's advertised query count.

  P3. After one terminal measurement yielding D, a fixed deterministic
      polynomial-time decoder dec(D,x,pi) uses only the classical database
      and ordinary local computation. It does not resume the adversary or
      make any further calls to the ideal extraction oracle.

  P4. There is a GLOBAL database event Bbad such that, for every instance/proof,
      D outside Bbad and V^D(x,pi)=accept imply
          R(x,dec(D,x,pi))=1.
      After at most Q charged queries, Pr[D in Bbad] <= G(Q).
      Missing database entries are bottom; V^D has a total reject/bottom rule.

P4 must quantify over all instances with the SAME deterministic decoder and
the SAME final database. Separate single-proof success probabilities in
different executions do not establish P4.

Imported primary-source results (not new claims by this artifact)

Don, Fehr, Majenz and Schaffner [S1] define an extractor that simulates the
oracle, verifies, measures once, and decodes. Corollary 2.7 bounds disagreement
between a terminal classical oracle computation and its database replay by
2v/2^h. Their collision and failure properties quantify over all instances.
Lemmas 4.1 and 5.1 bound those database events. Theorems 4.2 and 5.2 instantiate
this approach for S-sound* commit-and-open protocols; S-sound* requires an
efficient decoder that finds a witness without being handed a successful
challenge set. The definition allows auxiliary quantum output.

The following two-output adaptation is derived here from those ingredients;
it is not quoted as a theorem about R29 from the paper.

The joint algorithm J

  1. Initialize one compressed-oracle simulation and run the adversary once,
     obtaining x0,pi0,x1,pi1 and its auxiliary output Z. Retain the exact
     classical packet, including the authorization transcript when provided
     by the correctly simulated experiment.
  2. In the SAME oracle execution, run V(x0,pi0), then V(x1,pi1), obtaining
     a0,a1. Do not stop after a rejection or measure the database between them.
  3. Measure the compressed-oracle database once, yielding classical D.
  4. Compute w0=dec(D,x0,pi0) and w1=dec(D,x1,pi1). Check R(x0,w0) and
     R(x1,w1) by local deterministic computation.
  5. Output the original packet, both verdicts, and both witness results,
     including failure markers. Do not retry or discard failed executions.

This is a reduction's extractor, not a public conflict tracer. Its internal D
is not an extra public certificate field or sidecar. The full quantum simulator
is a mathematical backend in this artifact; the Python test backend is not it.

Joint-lift theorem

Let Gamma be any classical event on the original packet/log, such as the
specific conflicting-body event required by the security game. Set
  p = Pr_real[Gamma and a0=1 and a1=1].
Under P1-P4 and the source's terminal readout lemma,
  p_E >= max(0, p - kappa_J),
  kappa_J = min(1, 2(v0+v1)/2^h + G(Q)).
Here p_E counts outputs satisfying Gamma, both original acceptances, and
valid witnesses for THOSE SAME x0,x1. In the project's contract this is L_J=1
for this composition step, conditional on an instantiated matching backend.
The backend's own error, resource costs, and hypotheses have not disappeared.

Proof.

First, simulate the entire real execution through both classical verifiers
using the source's exact oracle simulation. Let F be their combined classical
computation with output (a0,a1), on the adversary's fixed classical packet.
Define d0,d1 by replaying that same computation with D as its partial oracle,
and define ReadoutBad = {(a0,a1)!=(d0,d1)}. Applying the readout lemma ONCE to
F, using its combined query bound v, gives Pr[ReadoutBad] <= 2v/2^h.

Outside ReadoutBad and Bbad, if both real verdicts accept, then d0=d1=1.
Applying the universal implication in P4 twice, in this SAME D, gives
R(x0,w0)=R(x1,w1)=1. Pointwise, therefore,
  {a0=a1=1 and at least one invalid witness}
      is a subset of ReadoutBad union {D in Bbad}.
The union bound gives error at most 2v/2^h+G(Q). Intersecting the successful
event with Gamma subtracts at most this same unconditional failure bound.
No independence is assumed and no probability is divided by p or by
Pr[Gamma]. There is a single global database term, not two copies of G(Q).

It remains to justify retaining the original packet and auxiliary output.
The simulation through both verifiers is exact under P1. Terminal measurement
and classical decoding act only on the extractor's register D. If their
classical results are ignored, that local trace-preserving operation does
not change the reduced state of the other registers. In symbols, for the
pre-measurement joint state rho_ZD,
  Tr_D(sum_d (I tensor |d><d|) rho_ZD (I tensor |d><d|)) = Tr_D(rho_ZD).
This preserves the unconditioned original view, including correlations with
the original classical packet. It does NOT assert that conditioning on an
extracted witness or successful extraction leaves Z unchanged. That is why
the algorithm returns failures and never postselects/retries. This completes
the two-output proof under the premises.

This argument needs neither quantum cloning nor sequential rewinding nor a
claim that two unrelated single-proof extractors share an execution. The
initial idea of re-running a selected verifier is unnecessary here: the
combined-verifier readout lemma addresses both outputs directly.

Explicit backend error, still symbolic

For the ordinary commit-and-open construction of [S1], let ell be its number
of commitments and p_triv its specified trivial challenge-success parameter.
Lemma 4.1 supplies the following admissible G after squaring its transition
capacity bound:
  G(Q) <= [2e Q^(3/2) 2^(-h/2)
           + Q sqrt(10 max(Q ell 2^(-h), p_triv))]^2.

For a convenient rational upper bound, (a+b)^2 <= 2a^2+2b^2, 8e^2<60, and
max(s,t)<=s+t yield
  G(Q) <= (20ell+60) Q^3 / 2^h + 20 Q^2 p_triv.
Consequently an admissible joint error is
  kappa_J <= min(1,
    [2(v0+v1)+(20ell+60)Q^3]/2^h + 20Q^2 p_triv).
For precision, this displays an upper bound on the achievable error term;
the right side itself may be selected as kappa_J in the success guarantee.
The executable ordinary_error_bound returns exactly that conservative value
using rational arithmetic. It does not infer ell, p_triv, h, Q, or a security
level for an absent R29 protocol. The Merkle variant needs its own Lemma 5.1
expression and parser; ordinary and Merkle parameters must not be mixed.

Where this stops for R29

The special-soundness decoder must actually reconstruct all 43 complete
(index, seed, approval signature) rows for EACH exact body, and its relation
must verify all the original trace and approval conditions. It must work
when an appropriate accepting challenge set exists without being handed
that set; an exponential search over all challenge subsets is insufficient.
Merely validating already supplied witness rows does not implement this.

To apply P1-P4, the proof protocol must expose a canonical commitment/opening
format and a proved efficient E* with those properties. The previous project
record says that the v1.29 full R29 prover/verifier is absent. The old public
decoder and earlier proofs of another relation cannot instantiate E*.
This artifact makes no new claim about the source bytes: the v1.29 package
was not available for inspection while it was written, so integration could
not be checked. Its authorization code is in this repository at
domains/03-zk-carrier-experiments/src/authorization.py, and work against that
exact relation needs the package in full, prover and verifier included.

The signature algorithms and concrete hashing inside the fixed relation can
be treated as deterministic circuits here. The proof's ideal oracle is a
separate explicitly modeled interface. Identifying it with a deployed hash
requires its own justification; this extraction-only result does not do that.
Likewise, faithfully simulating any signing/authorization service is a premise
of the chosen experiment, not a theorem obtained from the driver tests.

Validation and exact closure status

The driver never runs two adversary instances, measures between verifications,
or sends decoded witnesses back into the adversary. It preserves exact body
bytes and the auxiliary reference. Its inverse index is canonical and reads
one immutable classical D. Both witnesses must satisfy the supplied relation
on their own original instance before the result is marked joint_success.
These properties are tested with a deliberately simple classical test double.

The checker also exhausts the Boolean failure-event implication, confirms
the rational bound's algebra, and records counterexamples to independence
and to postselection preserving the original packet distribution. Those
finite checks validate the driver and event bookkeeping, not the imported
quantum-oracle lemmas, a full protocol, or QPT-128 security.
Recorded validation: all 16 test groups passed on 2026-09-09, including all
100 Boolean assignments satisfying the global database premise.

Established here: a conditional joint-lift derivation with L_J=1 and one
global database-error term; executable classical control flow and negative
controls. Still missing: the actual full-R29 special-soundness decoder and
matching proof backend. The original actual-extractor blocker is therefore
partially reduced, not finalized.

Primary source

[S1] Jelle Don, Serge Fehr, Christian Majenz, Christian Schaffner,
Efficient NIZKs and Signatures from Commit-and-Open Protocols in the QROM,
arXiv:2202.13730v1 (2022). Corollary 2.7; Definitions 3.1 and 3.5;
Equation (6); Lemmas 4.1/5.1; Theorems 4.2/5.2.
https://arxiv.org/pdf/2202.13730

Path note. This file is domains/05-extraction-and-signature-reductions/src/joint_extractor_lift.py.
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
from itertools import product
from types import MappingProxyType
import sys
import unittest


@dataclass(frozen=True)
class Packet:
    instances: tuple
    proofs: tuple
    authorization_log: tuple = ()
    auxiliary: object = None


@dataclass(frozen=True)
class JointResult:
    packet: Packet
    verdicts: tuple
    witnesses: tuple
    joint_success: bool


def inverse_index(database):
    """Canonical D^{-1}; None represents bottom. No hash/oracle calls."""
    inverse = {}
    for x, y in database.items():
        if type(x) is not bytes or (y is not None and type(y) is not bytes):
            raise ValueError('database keys/values must be bytes or bottom values')
        if y is not None and (y not in inverse or x < inverse[y]):
            inverse[y] = x
    return MappingProxyType(inverse)


def extract_joint(adversary, backend, decoder, relation):
    """Classical driver ONLY. Its supplied backend is a theorem obligation.

    Required backend: run_once(A), verify(x,proof), measure_once().
    decoder(x,proof,D,inverse) and relation(x,w) must be deterministic, local,
    total on permitted inputs, and make no further ideal-oracle calls.
    Backend semantics and decoder purity cannot be certified by this wrapper.
    """
    packet = backend.run_once(adversary)
    if type(packet) is not Packet:
        raise ValueError('canonical two-output packet required')
    for values in (packet.instances, packet.proofs):
        if type(values) is not tuple or len(values) != 2 or any(type(x) is not bytes for x in values):
            raise ValueError('exactly two canonical byte strings required')
    if type(packet.authorization_log) is not tuple:
        raise ValueError('classical authorization log must be a tuple')
    # Evaluate both; do not use an `and` expression that short-circuits.
    verdicts = tuple(backend.verify(x, pi) for x, pi in zip(packet.instances, packet.proofs))
    if any(type(v) is not bool for v in verdicts):
        raise ValueError('verdicts must be booleans')
    database = MappingProxyType(dict(backend.measure_once()))
    inverse = inverse_index(database)
    witnesses = []
    for x, pi in zip(packet.instances, packet.proofs):
        w = decoder(x, pi, database, inverse)
        # Here None is the failure marker, not a permitted relation witness.
        witnesses.append(w if w is not None and relation(x, w) is True else None)
    witnesses = tuple(witnesses)
    return JointResult(packet, verdicts, witnesses,
                       all(verdicts) and all(w is not None for w in witnesses))


def ordinary_error_bound(*, total_queries, verifier_queries, hash_bits,
                         commitments, trivial_probability):
    """Exact conservative joint error for the stated ordinary C&O premises."""
    for n in (total_queries, verifier_queries, hash_bits, commitments):
        if type(n) is not int:
            raise ValueError('canonical integer parameters required')
    if not (1 <= total_queries and 0 <= verifier_queries <= total_queries and
            1 <= hash_bits and 1 <= commitments):
        raise ValueError('invalid parameter range or uncharged verifier queries')
    if type(trivial_probability) is not Fraction or not 0 <= trivial_probability <= 1:
        raise ValueError('trivial probability must be an exact Fraction in [0,1]')
    q, v, h, ell, t = (total_queries, verifier_queries, hash_bits,
                       commitments, trivial_probability)
    bound = Fraction(2*v+(20*ell+60)*q**3, 1 << h) + 20*q*q*t
    return min(Fraction(1), bound)


class DemoBackend:
    """CLASSICAL TEST DOUBLE. Not a proof verifier or quantum simulator."""
    def __init__(self, database, verdicts=(True, True)):
        self.database = dict(database)
        self.verdicts = verdicts
        self.events = []
        self.runs = 0
        self.verifications = 0
        self.measurements = 0

    def run_once(self, adversary):
        if self.runs:
            raise RuntimeError('adversary reused')
        self.runs += 1
        self.events.append('adversary')
        return adversary()

    def verify(self, instance, proof):
        if self.measurements:
            raise RuntimeError('verification after measurement')
        n = self.verifications
        self.verifications += 1
        self.events.append(('verify', instance, proof))
        return self.verdicts[n]

    def measure_once(self):
        if self.measurements or self.verifications != 2:
            raise RuntimeError('requires two verifications and a single measurement')
        self.measurements += 1
        self.events.append('measure')
        return self.database


class JointTests(unittest.TestCase):
    def setUp(self):
        self.auxiliary = object()
        self.packet = Packet((b'body0', b'body1'), (b'commit0', b'commit1'),
                             (b'original-auth-log',), self.auxiliary)
        self.database = {b'full-witness0': b'commit0', b'full-witness1': b'commit1'}
        self.valid = {b'body0': b'full-witness0', b'body1': b'full-witness1'}
        self.backend = DemoBackend(self.database)

    def relation(self, x, w):
        return self.valid.get(x) == w

    @staticmethod
    def decode(x, pi, database, inverse):
        return inverse.get(pi)

    def run_driver(self, backend=None, decoder=None, adversary=None):
        return extract_joint(adversary or (lambda: self.packet), backend or self.backend,
                             decoder or self.decode, self.relation)

    def test_01_exact_joint_witnesses(self):
        result = self.run_driver()
        self.assertTrue(result.joint_success)
        self.assertEqual(result.witnesses, (b'full-witness0', b'full-witness1'))

    def test_02_one_run_and_terminal_measurement(self):
        calls = []
        def adversary():
            calls.append(1)
            return self.packet
        self.run_driver(adversary=adversary)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.backend.measurements, 1)
        self.assertEqual(self.backend.events,
            ['adversary', ('verify', b'body0', b'commit0'),
             ('verify', b'body1', b'commit1'), 'measure'])

    def test_03_first_rejection_does_not_short_circuit(self):
        backend = DemoBackend(self.database, (False, True))
        result = self.run_driver(backend=backend)
        self.assertFalse(result.joint_success)
        self.assertEqual(backend.verifications, 2)
        self.assertEqual(backend.measurements, 1)
        self.assertIs(result.packet, self.packet)

    def test_04_auxiliary_and_log_preserved(self):
        result = self.run_driver()
        self.assertIs(result.packet.auxiliary, self.auxiliary)
        self.assertIs(result.packet.authorization_log, self.packet.authorization_log)
        self.assertIs(result.packet, self.packet)

    def test_05_wrong_body_witnesses_rejected(self):
        def swapped(x, pi, database, inverse):
            return inverse[b'commit1' if pi == b'commit0' else b'commit0']
        result = self.run_driver(decoder=swapped)
        self.assertFalse(result.joint_success)
        self.assertEqual(result.witnesses, (None, None))

    def test_06_missing_preimage_is_failure(self):
        backend = DemoBackend({b'full-witness0': b'commit0'})
        result = self.run_driver(backend=backend)
        self.assertEqual(result.witnesses, (b'full-witness0', None))
        self.assertFalse(result.joint_success)

    def test_07_measured_database_is_readonly(self):
        def mutating(x, pi, database, inverse):
            with self.assertRaises(TypeError):
                database[b'new'] = b'value'
            with self.assertRaises(TypeError):
                inverse[b'value'] = b'new'
            return inverse.get(pi)
        self.assertTrue(self.run_driver(decoder=mutating).joint_success)

    def test_08_inverse_is_canonical_with_bottom(self):
        inv = inverse_index({b'z': b'same', b'a': b'same', b'b': None})
        self.assertEqual(dict(inv), {b'same': b'a'})
        for malformed in [{1: b'v'}, {b'x': 1}, {b'x': False}]:
            with self.assertRaises(ValueError):
                inverse_index(malformed)

    def test_09_no_late_verification_or_second_measurement(self):
        self.run_driver()
        with self.assertRaises(RuntimeError):
            self.backend.measure_once()
        with self.assertRaises(RuntimeError):
            self.backend.verify(b'body0', b'commit0')
        with self.assertRaises(RuntimeError):
            self.backend.run_once(lambda: self.packet)

    def test_10_packet_shape_and_verdict_types(self):
        for packet in [None, Packet([b'a', b'b'], (b'p', b'q')),
                       Packet((b'a',), (b'p', b'q')),
                       Packet((b'a', bytearray(b'b')), (b'p', b'q'))]:
            with self.assertRaises(ValueError):
                self.run_driver(backend=DemoBackend(self.database), adversary=lambda: packet)
        with self.assertRaises(ValueError):
            self.run_driver(backend=DemoBackend(self.database, (1, True)))

    def test_11_global_failure_implication_exhaustive(self):
        considered = 0
        for a0, a1, d0, d1, w0, w1, bad in product((False, True), repeat=7):
            # P4: outside bad, each database acceptance implies a valid witness.
            if not bad and ((d0 and not w0) or (d1 and not w1)):
                continue
            considered += 1
            readout_bad = (a0, a1) != (d0, d1)
            failure = a0 and a1 and not (w0 and w1)
            self.assertFalse(failure and not (readout_bad or bad))
        self.assertEqual(considered, 100)

    def test_12_marginals_do_not_imply_joint_success(self):
        outcomes = [(True, False), (False, True)]
        p0 = Fraction(sum(a for a, b in outcomes), 2)
        p1 = Fraction(sum(b for a, b in outcomes), 2)
        joint = Fraction(sum(a and b for a, b in outcomes), 2)
        self.assertEqual((p0, p1, joint), (Fraction(1,2), Fraction(1,2), Fraction(0)))
        self.assertNotEqual(p0*p1, joint)

    def test_13_shared_bad_event_need_not_be_counted_twice(self):
        states = [('bad', False, False)] + [('good', True, True)]*3
        bad_probability = Fraction(sum(s == 'bad' for s,a,b in states), len(states))
        joint_failure = Fraction(sum(not(a and b) for s,a,b in states), len(states))
        self.assertEqual(joint_failure, bad_probability)

    def test_14_postselection_changes_packet_distribution(self):
        states = [(b'packet0', True), (b'packet1', False)]
        original = Fraction(sum(p == b'packet0' for p, ok in states), len(states))
        kept = [p for p, ok in states if ok]
        conditional = Fraction(sum(p == b'packet0' for p in kept), len(kept))
        self.assertEqual((original, conditional), (Fraction(1,2), Fraction(1)))

    def test_15_exact_error_arithmetic_and_ranges(self):
        q, v, h, ell, t = 3, 2, 32, 4, Fraction(1, 1 << 40)
        expected = Fraction(2*v+(20*ell+60)*q**3, 1 << h) + 20*q*q*t
        self.assertEqual(ordinary_error_bound(total_queries=q, verifier_queries=v,
                         hash_bits=h, commitments=ell, trivial_probability=t), expected)
        args = dict(total_queries=q, verifier_queries=v, hash_bits=h,
                    commitments=ell, trivial_probability=t)
        for field, invalid in [('total_queries', True), ('verifier_queries', q+1),
                               ('hash_bits', 0), ('commitments', 0),
                               ('trivial_probability', 0.5), ('trivial_probability', Fraction(-1))]:
            with self.assertRaises(ValueError):
                ordinary_error_bound(**(args | {field: invalid}))
        self.assertEqual(ordinary_error_bound(**(args | {'trivial_probability': Fraction(1)})), 1)

    def test_16_coefficient_bound_with_exact_e_upper_bound(self):
        # e=sum(1/n!), n=0..4 plus a tail <= (1/5!)/(1-1/6).
        e_upper = Fraction(65,24) + Fraction(1,120)/(1-Fraction(1,6))
        self.assertLess(8*e_upper*e_upper, 60)
        for s, t in product([Fraction(0), Fraction(1,7), Fraction(1)], repeat=2):
            self.assertLessEqual(max(s,t), s+t)


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    elif sys.argv[1:] in ([], ['--explain']):
        print(__doc__)
    else:
        raise SystemExit('Use --self-test or --explain. No R29 backend is implemented.')
