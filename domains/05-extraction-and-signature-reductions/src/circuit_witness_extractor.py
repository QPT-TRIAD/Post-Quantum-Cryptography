#!/usr/bin/env python3
r"""Concrete circuit witness extraction, v1.36 — 2026-09-10

This update supplies a concrete deterministic special-soundness extractor E*
for a candidate Boolean-circuit proof backend, plus a matching circuit-level
prover/verifier. E* reconstructs the complete witness bit vector from fixed
committed views. It finds an extractable repetition by scanning, without
being handed a successful challenge set or searching exponentially many
challenge combinations. Two exact witnesses were recovered from one shared
classical test database after both circuit proofs had verified.

This is a NEW candidate backend, not a patch to or proof of the old R29 backend.
The R29 authorization relation has not been compiled into this circuit format.
The test database records ordinary classical SHAKE calls; it is not a quantum
compressed-oracle implementation. Consequently no full-R29 extraction or
QPT-128 security claim is made.

Run this self-contained file:
  python3 circuit_witness_extractor.py --self-test
  python3 circuit_witness_extractor.py --explain
The standard library suffices. There is no deployment CLI. The file contains
the complete circuit code, witness extractor, and synthetic tests.

Public statement and relation

A statement x encodes a fixed acyclic Boolean circuit C, public context bytes,
and a repetition count r. Gates are CONST, NOT, XOR and AND, with references
only to earlier wires. The relation implemented here is
  R_C(x,w) = [w is an n-bit vector and C(w)=1].
Canonical encodings bind each view to the complete x, repetition and party.
The context label alone does not constrain C's semantics: an application must
pin its approved circuit and correct public inputs. A proof for C=constant-1
does not prove R29 just because it is labeled with an R29 context string.

For R29 integration, C must be the audited circuit for the ENTIRE fixed
authorization predicate on the body and authenticated registry. That includes
43 distinct indices, every trace credential opening, recomputation of each
handle using the same index, and full approval-signature verification for
that same seat and canonical approval message. A proved witness-bit encoding
must map the extracted vector back to all 43 (index, seed, signature) rows.
Neither a supplied Boolean `authorized` flag nor a circuit that checks only
the handle algebra can substitute for those conditions.

Source ingredients and adaptation

ZKBoo [S1, Section 4.1 and Proposition 4.2] supplies a three-share circuit
decomposition and a three-special-soundness argument. Its text explicitly
rejects two-special soundness: two openings may reveal all input shares while
leaving a computation branch unchecked. DFMS [S2, Definition 3.5] requires
an efficient S-sound* decoder that finds a witness without being supplied an
accepting challenge set. Its ordinary commit-and-open framework uses distinct
subsets of committed messages as challenges. These are imported ingredients;
the encoding, driver, tests and adaptation proved below are this update's work.

Three-view arithmetic and local verification

Party indices below are i=0,1,2 modulo 3. For each input witness bit w, choose
two uniform shares w0,w1 and set w2=w XOR w0 XOR w1. Each view contains its
own wire shares and independent random mask bits for all AND gates. No
pseudorandom tape generator or new hardness assumption is needed for the
algebraic statements here; the reference prover samples those bits directly.

CONST(b) has shares (b,0,0). A NOT flips party 0's share. XOR is evaluated
sharewise. For an AND gate on wire triples a,b, using fresh masks rho_i, set
  z_i = a_i b_i XOR a_(i+1) b_i XOR a_i b_(i+1)
        XOR rho_i XOR rho_(i+1).
Products in this equation are bit ANDs. A local check at direction i sees
views i and i+1 and verifies every local recurrence for party i, their
metadata, both opened output shares, and the declared output reconstruction.
It does not certify the unverified neighbor's own AND recurrence.

The first message declares three output-share bits per repetition, whose XOR
must be 1. These outputs enter the Fiat-Shamir challenge input along with all
commitments and the complete statement. Every opened view's output must
equal the declaration at its own party position. In DFMS notation these
declarations are the additional first-message string a-circle; they may be
included in the augmented instance, with R unchanged on the original x,w.

Lemma 1: three passing local directions yield a witness

Suppose the three fixed views of a repetition pass directions 0,1,2. Every
party's gate recurrence is therefore correct. XOR the three AND equations.
Each rho_i occurs twice and cancels. The remaining nine product terms are
exactly all a_i b_j, i,j in {0,1,2}, so
  z0 XOR z1 XOR z2 = (a0 XOR a1 XOR a2) AND (b0 XOR b1 XOR b2).
The same reconstruction property follows directly for CONST, NOT and XOR.
Induction in the circuit's topological order therefore shows that the XOR
of the three shares on each wire equals ordinary circuit evaluation on
w = input0 XOR input1 XOR input2. At the output, all three declared bits
are matched to the views, and their XOR is 1. Thus C(w)=1.

The implemented helper special_soundness_extract scans repetition triples,
checks all three directions, reconstructs every input bit, and evaluates C(w)
again as a defensive invariant check. It skips missing or malformed triples
and can succeed on a later intact repetition. The full protocol decoder
special_soundness_extract_messages handles the four commitment slots below.
It receives neither the witness nor a preferred accepting challenge set.

Why two checks are insufficient

A negative test uses the false witness (0,0) for C(w)=w0 AND w1. It generates
correct shares, flips only branch 1's final output share, and updates the
declared output so its XOR becomes 1. Directions 0 and 2 still pass, while
direction 1 fails. All input shares are present, but their reconstruction is
still (0,0), which does not satisfy C. E* correctly returns failure. Thus
the rule "two openings expose all shares, therefore extract" is invalid.

Four distinct challenge subsets

Each repetition commits to four messages: three views and a public dummy
message bound to x and the repetition. A two-bit symbol chooses these slots:
  symbol 0: {0,1},       checking direction 0;
  symbol 1: {1,2},       checking direction 1;
  symbol 2: {2,0},       checking direction 2;
  symbol 3: {0,1,3},     checking direction 0 plus the exact dummy opening.
All four subsets are distinct. The dummy has no witness-recovery role; it
makes the fourth subset distinct while preserving binary challenge sampling.
An earlier draft merely mapped symbols 0 and 3 to the same opening pair.
That was insufficient to identify four distinct subsets in the source
theorem, so this implementation was amended before finalization.

There are ell=4r commitments and exactly 4^r distinct global challenge
subsets. The challenge is the first 2r bits of the ideal h-bit hash output,
read in canonical most-significant-first two-bit symbols. The prototype uses
h=512 and 1<=r<=256, so no rejection sampling, modulo bias or extra hash
stream is involved. A public verifier makes at most 1+3r hash calls: one
challenge call and at most three commitment-opening checks per repetition.

Lemma 2: the implemented decoder is S-sound*

Define S to be the monotone family of sets of global challenges for which
there exists a repetition j whose selected local directions cover {0,1,2}.
Suppose the fixed committed messages admit accepting responses to every
challenge in some member of S. At that j all three local directions must
pass with the SAME three fixed view messages. Lemma 1 yields a valid witness.
The decoder tests every j and every local direction, so it finds a witness
without receiving that member of S. Missing dummy messages may invalidate
symbol 3, but are unnecessary for reconstruction once the three directions
pass. This proves the S-sound* property needed by the chosen backend.

Three arbitrary distinct GLOBAL challenges are not enough: (0,0), (0,3),
(3,0) are distinct but select only local direction 0 in either repetition.
The checker includes this negative control. The theorem requires local
three-direction coverage at some repetition, not just a count of transcripts.

Finding a witness requires O(r(n+g)) local gate/vector operations for n input
bits and g gates, plus canonical parsing/encoding work polynomial in their
encoded lengths. There is no 4^r search. Enumeration in one small test only
checks the combinatorial claim; the actual extractor never enumerates global
challenges. Large R29-circuit performance has not been measured.

Lemma 3: exact combinatorial trivial-success parameter

If a challenge set is outside S, every repetition's projection misses at
least one local direction. Missing direction 1 or 2 excludes at least one
of the four symbols; missing direction 0 excludes two symbols. Thus each
coordinate permits at most three symbols. The whole challenge set lies
inside a product of such coordinate sets and has size at most 3^r.
The set {0,2,3}^r attains this size and is outside S. Therefore
  p_triv = 3^r/4^r = (3/4)^r.
This proof does not assume that a malicious challenge set factorizes or that
different repetitions' cheating events are independent. It is a counting
statement about S and a uniformly sampled global challenge. It is not the
complete Fiat-Shamir extraction error against quantum oracle queries.

From database preimages to both exact witnesses

The implemented circuit prover commits using the domain-separated input
  b'CEQS136/commit\x00' || canonical_message.
Its challenge uses a different prefix and includes the full canonical first
message and statement. verify checks the challenge, every selected hash
opening, dummy contents when selected, and local direction constraints.

After a reduction measures its oracle database D, extract_from_database
builds the canonical inverse map, looks up each commitment's preimage,
checks the commit-domain prefix, and passes the recovered messages or bottom
markers into E*. It makes no hash queries. The canonical inverse chooses
the lexicographically smallest preimage if several are present; collision
cases remain in the backend's bad-database event. No source of private
witness material is added to the public proof.

extract_two_from_database uses one inverse index of one ALREADY MEASURED D
for the two original statement/proof pairs. It supplies neither private
witnesses nor a decoding hint. The test creates two circuit proofs with
different complete input vectors, verifies both, freezes the shared test
oracle, and recovers those exact vectors. A separate check disables SHAKE
during postprocessing and confirms that witness recovery makes no hash calls.

The record of a public verifier's classical calls is insufficient for this
decoder: it contains only the two circuit views opened in each repetition,
and possibly the dummy. The corresponding test returns failure. The shared
honest-prover test log contains all committed preimages and enables extraction.
This distinction is deliberate. The classical log is an experimental stand-in
for an ALREADY MEASURED reduction database, not an implementation or proof
of quantum database extraction and not a proposed public sidecar.

Connection to the v1.35 joint-extraction derivation

That derivation runs the adversary once, verifies both proofs in one exact
compressed-oracle simulation, measures once, and applies the deterministic
decoder twice. The common bad-database event is global over instances; a
single readout event covers both verifiers. These give the conditional form
  p_E >= max(0, p-kappa_J), with joint multiplier L_J=1.

For this candidate's ordinary commit-and-open protocol, the decoder and
combinatorial slots are now explicit:
  E*       = special_soundness_extract_messages;
  R        = R_C, not yet R29;
  ell      = 4r;
  p_triv   = (3/4)^r;
  v0+v1    <= 2+6r;
  h        = 512 in the reference hash interface.
For example, inserting these symbols into the conservative v1.35 ordinary
bound gives an admissible error term
  kappa_J = min(1,
       [4+12r+(80r+60)Q^3]/2^512 + 20Q^2(3/4)^r),
where Q includes ALL charged oracle calls through both verifications. This
is symbolic bookkeeping under the exact QROM backend assumptions; it is not
a selected parameter set or a numerical QPT-128 claim. The finite test log
does not instantiate the quantum simulator or the deployed-hash assumption.

Experimental validation and closure status

The final bundled tests cover all 512 assignments for the AND reconstruction
identity, honest three-direction recovery, incomplete/corrupt views, later
extractable repetitions, all four challenge formats, all small global
challenge sets used in the counting checks, and 40 deterministic randomly
generated acyclic circuits. They also cover circuit/context substitution,
false witnesses, canonical parsing, selected proof mutations, public-only
database failure, complete witness-vector recovery, exact two-witness recovery,
and the observed verifier hash-call counts against the stated maximum.

All 27 test groups passed on 2026-09-10. These are finite implementation
checks. The gate induction, S-sound* proof, and challenge counting argument
above establish the corresponding mathematical claims. They do not establish
zero knowledge for this variant, a deployed-hash QPT bound, or the full R29
relation. The prototype is not a production proof system.

Closed component: concrete polynomial-time witness decoder for this circuit
backend, with matching circuit prover/verifier and the S-sound* argument.
Next required component: a pinned, audited compilation of the entire R29
authorization relation, with a proved witness encoding and equivalence
  C_R29(public_input, Encode(w))=1 iff R29(public_input,w)=1.
The visible project record supplies R29's intended conditions, but its
implementation package was not available for inspection while this revision
was written. It therefore does not claim source integration or an accepted
original-goal quorum certificate.

Primary sources

[S1] Irene Giacomelli, Jesper Madsen, Claudio Orlandi, ZKBoo: Faster
Zero-Knowledge for Boolean Circuits, USENIX Security 2016, Section 4.1,
Proposition 4.2, Appendix A.
https://www.usenix.org/system/files/conference/usenixsecurity16/sec16_paper_giacomelli.pdf

[S2] Jelle Don, Serge Fehr, Christian Majenz, Christian Schaffner, Efficient
NIZKs and Signatures from Commit-and-Open Protocols in the QROM,
arXiv:2202.13730v1, Definition 3.5, Lemma 4.1, Theorem 4.2.
https://arxiv.org/pdf/2202.13730

[L1] src/joint_extractor_lift.py (v1.35), the preceding conditional joint-lift
derivation and classical driver. No earlier missing source file was reread.

Path note. This file is domains/05-extraction-and-signature-reductions/src/circuit_witness_extractor.py.
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
import sys

from dataclasses import dataclass, replace
from fractions import Fraction
import hashlib
import json
import random

VERSION = 'CEQS-CIRCUIT-EXTRACTOR-136'
COMMIT_TAG = b'CEQS136/commit\x00'
CHALLENGE_TAG = b'CEQS136/challenge\x00'
HASH_BYTES = 64
PAIR_MAP = (0, 1, 2, 0)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def load_canonical(raw):
    if type(raw) is not bytes:
        raise ValueError('canonical bytes required')
    obj = json.loads(raw)
    if canonical(obj) != raw:
        raise ValueError('noncanonical JSON')
    return obj


def exact_keys(obj, keys):
    if type(obj) is not dict or set(obj) != set(keys):
        raise ValueError('wrong fields')


def exact_int(value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError('noncanonical integer')
    return value


def bit_list(values, length):
    if type(values) not in (list, tuple) or len(values) != length:
        raise ValueError('wrong bit-vector length')
    return tuple(exact_int(v, 0, 1) for v in values)


def unhex(text, length=None):
    if type(text) is not str:
        raise ValueError('hex string required')
    raw = bytes.fromhex(text)
    if raw.hex() != text or (length is not None and len(raw) != length):
        raise ValueError('noncanonical hex')
    return raw


@dataclass(frozen=True)
class Circuit:
    inputs: int
    gates: tuple
    output: int

    def validate(self):
        exact_int(self.inputs, 1, 2**32-1)
        if type(self.gates) is not tuple:
            raise ValueError('gate tuple required')
        for k, gate in enumerate(self.gates):
            if type(gate) is not tuple or not gate:
                raise ValueError('invalid gate')
            op = gate[0]
            if op == 'CONST' and len(gate) == 2:
                exact_int(gate[1], 0, 1)
            elif op == 'NOT' and len(gate) == 2:
                exact_int(gate[1], 0, self.inputs+k-1)
            elif op in ('XOR', 'AND') and len(gate) == 3:
                for index in gate[1:]:
                    exact_int(index, 0, self.inputs+k-1)
            else:
                raise ValueError('unsupported gate')
        exact_int(self.output, 0, self.inputs+len(self.gates)-1)
        return self

    @property
    def and_count(self):
        return sum(g[0] == 'AND' for g in self.gates)

    def evaluate(self, witness):
        self.validate()
        wires = list(bit_list(witness, self.inputs))
        for gate in self.gates:
            op = gate[0]
            if op == 'CONST':
                value = gate[1]
            elif op == 'NOT':
                value = wires[gate[1]] ^ 1
            elif op == 'XOR':
                value = wires[gate[1]] ^ wires[gate[2]]
            else:
                value = wires[gate[1]] & wires[gate[2]]
            wires.append(value)
        return wires[self.output]


@dataclass(frozen=True)
class Statement:
    circuit: Circuit
    context: bytes
    repetitions: int

    def encode(self):
        self.circuit.validate()
        exact_int(self.repetitions, 1, 256)  # 2r challenge bits <= 512.
        if type(self.context) is not bytes:
            raise ValueError('context bytes required')
        return canonical(dict(version=VERSION, context=self.context.hex(),
                              repetitions=self.repetitions, inputs=self.circuit.inputs,
                              gates=self.circuit.gates, output=self.circuit.output))

    @classmethod
    def parse(cls, raw):
        obj = load_canonical(raw)
        exact_keys(obj, ('version', 'context', 'repetitions', 'inputs', 'gates', 'output'))
        if obj['version'] != VERSION or type(obj['gates']) is not list:
            raise ValueError('wrong statement format')
        if any(type(g) is not list for g in obj['gates']):
            raise ValueError('invalid gates')
        result = cls(Circuit(obj['inputs'], tuple(tuple(g) for g in obj['gates']), obj['output']),
                     unhex(obj['context']), obj['repetitions'])
        if result.encode() != raw:
            raise ValueError('noncanonical statement')
        return result


def local_value(party, gate, wire0, wire1, tape0, tape1, and_index):
    op = gate[0]
    if op == 'CONST':
        return gate[1] if party == 0 else 0
    if op == 'NOT':
        return wire0[gate[1]] ^ (party == 0)
    a, b = gate[1:]
    if op == 'XOR':
        return wire0[a] ^ wire0[b]
    return ((wire0[a] & wire0[b]) ^ (wire1[a] & wire0[b]) ^
            (wire0[a] & wire1[b]) ^ tape0[and_index] ^ tape1[and_index])


def make_views(statement, witness, repetition, rng):
    """Honest local decomposition; no distributed protocol is executed."""
    x = statement.encode()
    circuit = statement.circuit
    witness = bit_list(witness, circuit.inputs)
    exact_int(repetition, 0, statement.repetitions-1)
    wires = [[rng.getrandbits(1) for _ in witness] for _ in range(2)]
    wires.append([w ^ a ^ b for w,a,b in zip(witness, wires[0], wires[1])])
    tapes = [[rng.getrandbits(1) for _ in range(circuit.and_count)] for _ in range(3)]
    and_index = 0
    for gate in circuit.gates:
        values = [local_value(i, gate, wires[i], wires[(i+1)%3],
                              tapes[i], tapes[(i+1)%3], and_index) for i in range(3)]
        for i in range(3):
            wires[i].append(values[i])
        and_index += gate[0] == 'AND'
    return tuple(canonical(dict(statement=x.hex(), repetition=repetition, party=i,
                                wires=wires[i], tape=tapes[i])) for i in range(3))


def parse_view(raw, statement, repetition, party):
    obj = load_canonical(raw)
    exact_keys(obj, ('statement', 'repetition', 'party', 'wires', 'tape'))
    if obj['statement'] != statement.encode().hex():
        raise ValueError('view belongs to another statement')
    if exact_int(obj['repetition'], 0, statement.repetitions-1) != repetition:
        raise ValueError('wrong repetition')
    if exact_int(obj['party'], 0, 2) != party:
        raise ValueError('wrong party')
    c = statement.circuit
    wires = bit_list(obj['wires'], c.inputs+len(c.gates))
    tape = bit_list(obj['tape'], c.and_count)
    return wires, tape


def check_pair(statement, repetition, pair_index, raw0, raw1, outputs):
    """Check branch i using the adjacent views i,i+1, plus output binding."""
    try:
        exact_int(pair_index, 0, 2)
        outputs = bit_list(outputs, 3)
        if outputs[0] ^ outputs[1] ^ outputs[2] != 1:
            return False
        i, j = pair_index, (pair_index+1)%3
        wires0, tape0 = parse_view(raw0, statement, repetition, i)
        wires1, tape1 = parse_view(raw1, statement, repetition, j)
        c = statement.circuit
        if wires0[c.output] != outputs[i] or wires1[c.output] != outputs[j]:
            return False
        and_index = 0
        for k, gate in enumerate(c.gates):
            if wires0[c.inputs+k] != local_value(i, gate, wires0, wires1, tape0, tape1, and_index):
                return False
            and_index += gate[0] == 'AND'
        return True
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError):
        return False


def validate_outputs(statement, outputs):
    if type(outputs) not in (list, tuple) or len(outputs) != statement.repetitions:
        raise ValueError('wrong repetition output count')
    values = tuple(bit_list(row, 3) for row in outputs)
    if any(a ^ b ^ c != 1 for a,b,c in values):
        raise ValueError('declared output must be one in every repetition')
    return values


def special_soundness_extract(statement, outputs, partial_views):
    """Concrete E*: scan r triples, never enumerate challenge vectors.

    partial_views is a 3r tuple of fixed committed preimages, or None for bottom.
    This is an extraction-stage API; supplying arbitrary views proves no hash
    commitment or public proof validity on its own.
    """
    statement.encode()
    outputs = validate_outputs(statement, outputs)
    if type(partial_views) is not tuple or len(partial_views) != 3*statement.repetitions:
        raise ValueError('exactly 3r partial views required')
    for rep in range(statement.repetitions):
        views = partial_views[3*rep:3*rep+3]
        if any(type(v) is not bytes for v in views):
            continue
        if not all(check_pair(statement, rep, i, views[i], views[(i+1)%3], outputs[rep])
                   for i in range(3)):
            continue
        shares = [parse_view(views[i], statement, rep, i)[0][:statement.circuit.inputs]
                  for i in range(3)]
        witness = tuple(a ^ b ^ c for a,b,c in zip(*shares))
        if statement.circuit.evaluate(witness) != 1:
            raise RuntimeError('special-soundness invariant violated')
        return witness
    return None


def special_soundness_extract_messages(statement, outputs, partial_messages):
    """Full ordinary C&O E*: four committed messages per repetition.

    Slots 0,1,2 hold views; slot 3 distinguishes the fourth challenge subset.
    The auxiliary dummy message is unnecessary for witness reconstruction.
    """
    if type(partial_messages) is not tuple or len(partial_messages) != 4*statement.repetitions:
        raise ValueError('exactly 4r partial messages required')
    triples = tuple(partial_messages[4*rep+i]
                    for rep in range(statement.repetitions) for i in range(3))
    return special_soundness_extract(statement, outputs, triples)


def dummy_message(statement, repetition):
    exact_int(repetition, 0, statement.repetitions-1)
    return canonical(dict(statement=statement.encode().hex(), repetition=repetition, dummy=1))


def opened_slots(symbol):
    exact_int(symbol, 0, 3)
    return ((0,1), (1,2), (2,0), (0,1,3))[symbol]


def parse_first(statement, first):
    exact_keys(first, ('commitments', 'outputs'))
    if type(first['commitments']) is not list or len(first['commitments']) != 4*statement.repetitions:
        raise ValueError('wrong commitment count')
    commitments = tuple(unhex(v, HASH_BYTES) for v in first['commitments'])
    outputs = validate_outputs(statement, first['outputs'])
    return commitments, outputs


def challenge_input(statement_bytes, first):
    return CHALLENGE_TAG + canonical(dict(statement=statement_bytes.hex(), first=first))


def challenge_symbols(digest, repetitions):
    if type(digest) is not bytes or len(digest) != HASH_BYTES:
        raise ValueError('wrong challenge digest')
    exact_int(repetitions, 1, 256)
    # Canonical most-significant-first 2-bit symbols.
    return tuple((digest[(2*j)//8] >> (6-(2*j)%8)) & 3
                 for j in range(repetitions))


def prove(statement, witness, oracle, rng=None):
    """Circuit-only Fiat-Shamir prototype, not a full R29 prover."""
    x = statement.encode()
    if statement.circuit.evaluate(witness) != 1:
        raise ValueError('witness does not satisfy circuit')
    rng = random.SystemRandom() if rng is None else rng
    triples = [make_views(statement, witness, rep, rng) for rep in range(statement.repetitions)]
    messages = tuple(v for rep,triple in enumerate(triples)
                     for v in triple+(dummy_message(statement, rep),))
    outputs = [[parse_view(triples[rep][i], statement, rep, i)[0][statement.circuit.output]
                for i in range(3)] for rep in range(statement.repetitions)]
    first = dict(commitments=[oracle(COMMIT_TAG+v).hex() for v in messages], outputs=outputs)
    parse_first(statement, first)
    symbols = challenge_symbols(oracle(challenge_input(x, first)), statement.repetitions)
    openings = [[messages[4*rep+i].hex() for i in opened_slots(symbol)]
                for rep,symbol in enumerate(symbols)]
    return canonical(dict(first=first, openings=openings))


def verify(statement_bytes, proof_bytes, oracle):
    """Verify the implemented circuit proof using the supplied hash interface."""
    try:
        statement = Statement.parse(statement_bytes)
        proof = load_canonical(proof_bytes)
        exact_keys(proof, ('first', 'openings'))
        commitments, outputs = parse_first(statement, proof['first'])
        if type(proof['openings']) is not list or len(proof['openings']) != statement.repetitions:
            return False
        symbols = challenge_symbols(oracle(challenge_input(statement_bytes, proof['first'])), statement.repetitions)
        for rep, symbol in enumerate(symbols):
            i = PAIR_MAP[symbol]
            pair = proof['openings'][rep]
            slots = opened_slots(symbol)
            if type(pair) is not list or len(pair) != len(slots):
                return False
            raws = tuple(unhex(v) for v in pair)
            for slot, raw in zip(slots, raws):
                if oracle(COMMIT_TAG+raw) != commitments[4*rep+slot]:
                    return False
            if symbol == 3 and raws[2] != dummy_message(statement, rep):
                return False
            if not check_pair(statement, rep, i, raws[0], raws[1], outputs[rep]):
                return False
        return True
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError):
        return False


def invert_database(database):
    inverse = {}
    for x, y in database.items():
        if type(x) is not bytes or (y is not None and (type(y) is not bytes or len(y) != HASH_BYTES)):
            raise ValueError('invalid database entry')
        if y is not None and (y not in inverse or x < inverse[y]):
            inverse[y] = x
    return inverse


def extract_from_database(statement_bytes, proof_bytes, database, inverse=None):
    """Post-measurement witness decoder; makes ZERO hash/oracle calls."""
    statement = Statement.parse(statement_bytes)
    proof = load_canonical(proof_bytes)
    exact_keys(proof, ('first', 'openings'))
    commitments, outputs = parse_first(statement, proof['first'])
    inverse = invert_database(database) if inverse is None else inverse
    partial_views = []
    for root in commitments:
        preimage = inverse.get(root)
        partial_views.append(preimage[len(COMMIT_TAG):]
                             if type(preimage) is bytes and preimage.startswith(COMMIT_TAG) else None)
    return special_soundness_extract_messages(statement, outputs, tuple(partial_views))


def extract_two_from_database(instance0, proof0, instance1, proof1, database):
    """Two fixed proof outputs, one ALREADY MEASURED classical database.

    This does not perform or emulate the quantum measurement. Both proofs must
    first be verified in the shared simulation specified by the joint theorem.
    """
    inverse = invert_database(database)
    return (extract_from_database(instance0, proof0, database, inverse),
            extract_from_database(instance1, proof1, database, inverse))


def protocol_parameters(repetitions):
    r = exact_int(repetitions, 1, 256)
    return dict(commitments=4*r, hash_bits=8*HASH_BYTES,
                max_verifier_queries_per_proof=1+3*r,
                trivial_probability=Fraction(3,4)**r)


class RecordingHash:
    """Classical SHAKE fixture ONLY; its log is not a quantum compressed oracle."""
    def __init__(self):
        self.database = {}
        self.calls = 0
        self.frozen = False

    def __call__(self, payload):
        if self.frozen:
            raise RuntimeError('oracle called after test database was frozen')
        if type(payload) is not bytes:
            raise ValueError('oracle input must be bytes')
        answer = hashlib.shake_256(payload).digest(HASH_BYTES)
        self.database[payload] = answer
        self.calls += 1
        return answer

import unittest
from itertools import product
from unittest.mock import patch
E = sys.modules[__name__]


class CircuitExtractorTests(unittest.TestCase):
    def setUp(self):
        self.circuit = E.Circuit(3, (('AND', 0, 1),), 3)
        self.statement = E.Statement(self.circuit, b'synthetic-body-A', 3)
        self.witness = (1, 1, 0)

    def transcript(self, statement=None, witness=None, seed=136):
        statement = self.statement if statement is None else statement
        witness = self.witness if witness is None else witness
        views = tuple(v for rep in range(statement.repetitions)
                      for v in E.make_views(statement, witness, rep, E.random.Random(seed+rep)))
        outputs = tuple(tuple(E.parse_view(views[3*rep+i], statement, rep, i)[0][statement.circuit.output]
                              for i in range(3)) for rep in range(statement.repetitions))
        return outputs, views

    def test_01_all_gate_arithmetic_cases(self):
        # All 2^9 assignments of the three x, y and mask shares.
        for bits in product((0,1), repeat=9):
            xs, ys, rs = bits[:3], bits[3:6], bits[6:]
            zs = [E.local_value(i, ('AND',0,1), (xs[i],ys[i]),
                                (xs[(i+1)%3],ys[(i+1)%3]), (rs[i],),
                                (rs[(i+1)%3],), 0) for i in range(3)]
            self.assertEqual(zs[0]^zs[1]^zs[2], (xs[0]^xs[1]^xs[2]) & (ys[0]^ys[1]^ys[2]))

    def test_02_three_checks_reconstruct_full_input(self):
        outputs, views = self.transcript()
        for rep in range(3):
            for i in range(3):
                self.assertTrue(E.check_pair(self.statement, rep, i, views[3*rep+i],
                                             views[3*rep+(i+1)%3], outputs[rep]))
        self.assertEqual(E.special_soundness_extract(self.statement, outputs, views), self.witness)

    def test_03_partial_database_later_repetition_suffices(self):
        outputs, views = self.transcript()
        partial = (None,)*6 + views[6:9]
        self.assertEqual(E.special_soundness_extract(self.statement, outputs, partial), self.witness)

    def test_04_missing_one_view_in_every_repetition(self):
        outputs, views = self.transcript()
        partial = tuple(None if i%3 == 0 else v for i,v in enumerate(views))
        self.assertIsNone(E.special_soundness_extract(self.statement, outputs, partial))

    def test_05_malformed_unused_repetition_does_not_block_extraction(self):
        outputs, views = self.transcript()
        partial = (b'bad', b'also-bad', b'not-json') + views[3:]
        self.assertEqual(E.special_soundness_extract(self.statement, outputs, partial), self.witness)

    def test_06_wrong_statement_party_and_repetition(self):
        outputs, views = self.transcript()
        for field, value in [('statement', b'wrong'.hex()), ('party', 2), ('repetition', 1)]:
            changed = E.load_canonical(views[0])
            changed[field] = value
            self.assertFalse(E.check_pair(self.statement, 0, 0, E.canonical(changed), views[1], outputs[0]))
        self.assertFalse(E.check_pair(self.statement, 0, 0, views[1], views[0], outputs[0]))

    def test_07_tampered_wires_and_random_tapes(self):
        outputs, views = self.transcript()
        for field, index in [('wires', self.circuit.output), ('tape', 0)]:
            changed = E.load_canonical(views[0])
            changed[field][index] ^= 1
            self.assertFalse(E.check_pair(self.statement, 0, 0, E.canonical(changed), views[1], outputs[0]))

    def test_08_two_accepting_checks_can_hide_false_computation(self):
        statement = E.Statement(E.Circuit(2, (('AND',0,1),), 2), b'false-branch-control', 1)
        outputs, views = self.transcript(statement, (0,0))
        # Flip only branch 1's final AND share and bind the changed output.
        # Directions 0 and 2 still pass, although reconstructed input is false.
        changed = E.load_canonical(views[1])
        changed['wires'][2] ^= 1
        views = (views[0], E.canonical(changed), views[2])
        out = list(outputs[0]); out[1] ^= 1
        checks = tuple(E.check_pair(statement, 0, i, views[i], views[(i+1)%3], out) for i in range(3))
        self.assertEqual(checks, (True, False, True))
        self.assertIsNone(E.special_soundness_extract(statement, (out,), views))
        shares = [E.parse_view(views[i], statement, 0, i)[0][:2] for i in range(3)]
        reconstructed = tuple(a^b^c for a,b,c in zip(*shares))
        self.assertEqual(reconstructed, (0,0))
        self.assertEqual(statement.circuit.evaluate(reconstructed), 0)

    def test_09_binary_challenge_distribution_and_repetition_bound(self):
        masks = [set(i for i in range(3) if mask & (1<<i)) for mask in range(7)]
        for accepting in masks:
            count = sum(pair in accepting for pair in E.PAIR_MAP)
            self.assertLessEqual(count, 3)
        self.assertEqual(sum(pair in {0,2} for pair in E.PAIR_MAP), 3)
        for repetitions in range(1,5):
            count = sum(all(E.PAIR_MAP[c] in {0,2} for c in challenge)
                        for challenge in product(range(4), repeat=repetitions))
            self.assertEqual(E.Fraction(count, 4**repetitions), E.Fraction(3,4)**repetitions)

    def test_10_random_topological_circuits(self):
        rng = E.random.Random(13610)
        for k in range(40):
            n, gates = 5, []
            witness = tuple(rng.getrandbits(1) for _ in range(n))
            for j in range(16):
                op = rng.choice(('CONST','NOT','XOR','AND'))
                gates.append((op, rng.getrandbits(1)) if op == 'CONST' else
                             (op, rng.randrange(n+j)) if op == 'NOT' else
                             (op, rng.randrange(n+j), rng.randrange(n+j)))
            circuit = E.Circuit(n, tuple(gates), n+len(gates)-1)
            if circuit.evaluate(witness) == 0:
                circuit = E.Circuit(n, circuit.gates+(('NOT', circuit.output),), n+len(gates))
            statement = E.Statement(circuit, str(k).encode(), 2)
            outputs, views = self.transcript(statement, witness)
            self.assertEqual(E.special_soundness_extract(statement, outputs, views), witness)

    def test_11_noncanonical_circuit_rejected(self):
        for circuit in [E.Circuit(True, (), 0), E.Circuit(1, (('AND',0,1),), 1),
                        E.Circuit(1, (('CONST',2),), 1), E.Circuit(1, (('BOGUS',0),),1),
                        E.Circuit(1, (), -1), E.Circuit(1, [('NOT',0)], 1)]:
            with self.assertRaises(ValueError):
                circuit.validate()

    def test_12_noncanonical_view_rejected(self):
        outputs, views = self.transcript()
        for field in ('wires','tape'):
            obj = E.load_canonical(views[0]); obj[field][0] = True
            self.assertFalse(E.check_pair(self.statement, 0, 0, E.canonical(obj), views[1], outputs[0]))
        self.assertFalse(E.check_pair(self.statement, 0, 0, views[0]+b' ', views[1], outputs[0]))
        obj = E.load_canonical(views[0]); obj['extra'] = 1
        self.assertFalse(E.check_pair(self.statement, 0, 0, E.canonical(obj), views[1], outputs[0]))

    def test_13_complete_circuit_proof_and_database_extraction(self):
        oracle = E.RecordingHash()
        proof = E.prove(self.statement, self.witness, oracle, E.random.Random(13613))
        self.assertTrue(E.verify(self.statement.encode(), proof, oracle))
        before = oracle.calls
        oracle.frozen = True
        with patch('hashlib.shake_256', side_effect=AssertionError('post-extraction hash call')):
            got = E.extract_from_database(self.statement.encode(), proof, oracle.database)
        self.assertEqual(got, self.witness)
        self.assertEqual(oracle.calls, before)

    def test_14_joint_same_database_exact_two_witnesses(self):
        oracle = E.RecordingHash()
        other = E.Statement(self.circuit, b'synthetic-body-B', 3)
        w1 = (1,1,1)
        proof0 = E.prove(self.statement, self.witness, oracle, E.random.Random(13614))
        proof1 = E.prove(other, w1, oracle, E.random.Random(13615))
        self.assertTrue(E.verify(self.statement.encode(), proof0, oracle))
        self.assertTrue(E.verify(other.encode(), proof1, oracle))
        oracle.frozen = True
        got = E.extract_two_from_database(self.statement.encode(), proof0, other.encode(), proof1, oracle.database)
        self.assertEqual(got, (self.witness, w1))

    def test_15_wrong_instance_proof_fails(self):
        oracle = E.RecordingHash()
        proof = E.prove(self.statement, self.witness, oracle, E.random.Random(13615))
        other = E.Statement(self.circuit, b'changed-body', 3)
        self.assertFalse(E.verify(other.encode(), proof, oracle))
        self.assertIsNone(E.extract_from_database(other.encode(), proof, oracle.database))

    def test_16_public_openings_alone_do_not_supply_full_views(self):
        prover_oracle = E.RecordingHash()
        proof = E.prove(self.statement, self.witness, prover_oracle, E.random.Random(13616))
        public_oracle = E.RecordingHash()
        self.assertTrue(E.verify(self.statement.encode(), proof, public_oracle))
        # Each repetition exposes only two committed views to the verifier.
        self.assertIsNone(E.extract_from_database(self.statement.encode(), proof, public_oracle.database))
        self.assertEqual(E.extract_from_database(self.statement.encode(), proof, prover_oracle.database), self.witness)

    def test_17_public_proof_mutations_rejected(self):
        oracle = E.RecordingHash()
        proof = E.prove(self.statement, self.witness, oracle, E.random.Random(13617))
        for mutation in ('root','output','opening','missing','extra','space'):
            obj = E.load_canonical(proof)
            if mutation == 'root': obj['first']['commitments'][0] = '00'*64
            if mutation == 'output': obj['first']['outputs'][0][0] ^= 1
            if mutation == 'opening': obj['openings'][0][0] = b'bad'.hex()
            if mutation == 'missing': obj['openings'].pop()
            if mutation == 'extra': obj['extra'] = 0
            changed = E.canonical(obj)+(b' ' if mutation == 'space' else b'')
            self.assertFalse(E.verify(self.statement.encode(), changed, oracle), mutation)

    def test_18_failed_relation_cannot_use_honest_prover(self):
        with self.assertRaises(ValueError):
            E.prove(self.statement, (0,0,0), E.RecordingHash())

    def test_19_output_and_partial_view_shape(self):
        outputs, views = self.transcript()
        for out, partial in [(outputs[:-1], views), (outputs, views[:-1]),
                             (((0,0,0),)*3, views)]:
            with self.assertRaises(ValueError):
                E.special_soundness_extract(self.statement, out, partial)

    def test_20_parameter_mapping_and_hash_query_count(self):
        oracle = E.RecordingHash()
        proof = E.prove(self.statement, self.witness, oracle, E.random.Random(13620))
        start = oracle.calls
        self.assertTrue(E.verify(self.statement.encode(), proof, oracle))
        params = E.protocol_parameters(self.statement.repetitions)
        actual_calls = oracle.calls-start
        symbols = E.challenge_symbols(oracle(E.challenge_input(self.statement.encode(),
                          E.load_canonical(proof)['first'])), self.statement.repetitions)
        self.assertEqual(actual_calls, 1+sum(len(E.opened_slots(s)) for s in symbols))
        self.assertLessEqual(actual_calls, params['max_verifier_queries_per_proof'])
        self.assertEqual(params['commitments'], 12)
        self.assertEqual(params['trivial_probability'], E.Fraction(27,64))
        for r in (0, 257, True):
            with self.assertRaises(ValueError): E.protocol_parameters(r)

    def test_21_recovery_returns_entire_bit_vector(self):
        witness = (1,) + tuple(E.random.Random(13621+i).getrandbits(1) for i in range(256))
        statement = E.Statement(E.Circuit(len(witness), (), 0), b'full-vector-test', 1)
        outputs, views = self.transcript(statement, witness)
        self.assertEqual(E.special_soundness_extract(statement, outputs, views), witness)

    def test_22_canonical_database_inverse_and_commit_domain(self):
        digest = b'x'*64
        self.assertEqual(E.invert_database({b'z':digest, b'a':digest, b'b':None}), {digest:b'a'})
        for db in ({b'a':b'short'}, {b'a':True}, {1:digest}):
            with self.assertRaises(ValueError): E.invert_database(db)
        oracle = E.RecordingHash()
        proof = E.prove(self.statement, self.witness, oracle, E.random.Random(13622))
        roots = E.parse_first(self.statement, E.load_canonical(proof)['first'])[0]
        bogus_database = {b'wrong-domain'+bytes([i]):root for i,root in enumerate(roots)}
        self.assertIsNone(E.extract_from_database(self.statement.encode(), proof, bogus_database))

    def test_23_four_challenges_are_distinct_opening_sets(self):
        subsets = {frozenset(E.opened_slots(s)) for s in range(4)}
        self.assertEqual(len(subsets), 4)
        self.assertEqual(subsets, {frozenset((0,1)), frozenset((1,2)),
                                  frozenset((2,0)), frozenset((0,1,3))})
        for r in range(1,5):
            global_sets = {frozenset(4*j+i for j,s in enumerate(c) for i in E.opened_slots(s))
                           for c in product(range(4), repeat=r)}
            self.assertEqual(len(global_sets), 4**r)

    def test_24_full_message_decoder_ignores_unneeded_dummy(self):
        outputs, views = self.transcript()
        messages = tuple(views[3*j+i] if i < 3 else None
                         for j in range(self.statement.repetitions) for i in range(4))
        self.assertEqual(E.special_soundness_extract_messages(self.statement, outputs, messages), self.witness)
        with self.assertRaises(ValueError):
            E.special_soundness_extract_messages(self.statement, outputs, messages[:-1])

    def test_25_all_four_challenge_opening_formats(self):
        statement = E.Statement(self.circuit, b'forced-challenge-tests', 1)
        for symbol in range(4):
            base = E.RecordingHash()
            def controlled(payload):
                if payload.startswith(E.CHALLENGE_TAG):
                    value = bytes([symbol<<6])+b'\0'*63
                    base.database[payload] = value
                    base.calls += 1
                    return value
                return base(payload)
            proof = E.prove(statement, self.witness, controlled, E.random.Random(13625))
            self.assertTrue(E.verify(statement.encode(), proof, controlled))
            obj = E.load_canonical(proof)
            self.assertEqual(len(obj['openings'][0]), len(E.opened_slots(symbol)))
            if symbol == 3:
                obj['openings'][0].pop()
                self.assertFalse(E.verify(statement.encode(), E.canonical(obj), controlled))

    def test_26_distinct_global_challenges_need_local_coverage(self):
        # Three distinct global challenges can all select only local direction 0.
        challenges = ((0,0), (0,3), (3,0))
        self.assertEqual(len(set(challenges)), 3)
        for coordinate in range(2):
            self.assertEqual({E.PAIR_MAP[c[coordinate]] for c in challenges}, {0})
        self.assertFalse(any({E.PAIR_MAP[c[j]] for c in challenges} == {0,1,2} for j in range(2)))
        covered = ((0,0), (1,0), (2,0))
        self.assertTrue(any({E.PAIR_MAP[c[j]] for c in covered} == {0,1,2} for j in range(2)))

    def test_27_circuit_must_be_pinned_by_the_application(self):
        # A generic proof of a weak circuit is valid, but is not a proof of the
        # intended circuit merely because it carries the same context label.
        weak = E.Statement(E.Circuit(3, (('CONST',1),), 3), self.statement.context, 3)
        oracle = E.RecordingHash()
        proof = E.prove(weak, (0,0,0), oracle, E.random.Random(13627))
        self.assertTrue(E.verify(weak.encode(), proof, oracle))
        self.assertFalse(E.verify(self.statement.encode(), proof, oracle))



if __name__ == '__main__':
    if sys.argv[1:] == ['--self-test']:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    elif sys.argv[1:] in ([], ['--explain']):
        print(__doc__)
    else:
        raise SystemExit('Use --self-test or --explain. This is a circuit extractor prototype.')
