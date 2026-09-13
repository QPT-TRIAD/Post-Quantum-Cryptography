#!/usr/bin/env python3
r"""
# What the sqrt(i)-phase circuit proves — v1.40

2026-09-10. Scope: assess the supplied quantum circuit as an input to the
existing signature-security reduction.

The supplied GHZ preparation is correct in the ideal H/T/CNOT gate model.
It proves efficient state preparation. It does not prove 128-bit security
against quantum adversaries. The useful additional result is an exact
simulation lemma: the proposed public, efficiently prepared state can be
included in the existing adversary model with explicit preparation costs.

## 1. Exact state-preparation theorem

Use zeta=exp(i*pi/4), the principal square root of i. Then

    T=diag(1,zeta),     |zeta|=1,     T^8=I.

The two real components of zeta have magnitude 1/sqrt(2), but the complex
number itself has magnitude one. Repeated T gates rotate relative phases;
they do not attenuate amplitudes, lower failure probabilities or create
extra cryptographic entropy. The T-gate matrix and its phase convention
match the standard definition [S1].

Let P_n apply H to qubit 0, T to qubit 0, and then CNOT(k,k+1) for
k=0,...,n-2, on the initial state |0>^n. For every n>=1,

    P_n |0>^n = (|0>^n + zeta |1>^n)/sqrt(2).                (1)

Proof by induction. After H and T, the state is

    (|0> + zeta|1>)/sqrt(2) tensor |0>^(n-1).

After k CNOT links, the invariant is

    (|0>^(k+1) + zeta|1>^(k+1))/sqrt(2)
      tensor |0>^(n-k-1).

The next CNOT leaves the all-zero branch unchanged. On the other branch,
its control is 1 and its target is initially 0, so the target becomes 1.
CNOT permutes computational-basis states without adding any phase. This
preserves the invariant with k replaced by k+1 and proves (1).

The count is 1 H + 1 T + (n-1) CNOTs = n+1 logical gates. At n=128 it is
129 gates. Executing that exact sequence serially has depth 129. The
family is uniformly constructible and has O(n) gate count and O(n) serial
depth; its fixed 128-qubit member is one instance of that family.

This depth is not a physical MAXDEPTH lower bound. For example, if arbitrary
pairs can interact, an alternative binary-tree fanout prepares the same
state with seven disjoint-CNOT layers at n=128 after H and T: nine layers
total and the same 129 gate count. This is an achievable alternative,
not a claim of optimal hardware depth. Connectivity, routing, physical
gate times and fault-tolerant overhead have not been modeled.

## 2. Resolve the extra phase at every interaction

The premise that every entangling operation injects sqrt(i) needs an actual
gate definition. It is not a property of standard CNOT. Three interpretations
give different answers:

| Gate model | Relative phase in the final two-branch state |
|---|---|
| One initial T; ordinary CNOTs | zeta |
| One initial T; each CNOT multiplied by a global zeta | zeta; an overall zeta^(n-1) is unobservable |
| One initial T; an additional T on the control at each link | zeta^n |

The third case follows because all n-1 link controls are 1 on the growing
all-one branch and 0 on the other branch. At n=128, zeta^128=1. The
result is the ordinary positive-phase GHZ state, rather than (1). Across
n=127,128,129 its relative phases are zeta^7,1,zeta, a modulo-eight cycle.
Those transitions describe phase accumulation, not changes in security.

Global and relative phase are distinct: a global phase cancels from every
density-matrix entry, while a relative phase can affect measurement
statistics after another transformation [S2]. A one-qubit T gate also does
not itself create entanglement from a product state; entanglement here
arises from the CNOTs applied after superposition is present.

## 3. The size of the Hilbert space gives no security bound

The register Hilbert space has dimension 2^128. Equation (1), however, has
only two nonzero computational-basis amplitudes. Measuring all qubits in
that basis gives

    Pr[0^128]=1/2,      Pr[1^128]=1/2,

with zero probability for every other string. That distribution has one
bit of Shannon entropy. It is not a uniform distribution over 2^128 strings.

For n>=2 and any nonempty proper bipartition A|B, the two terms in (1) are
orthogonal on each side. Tracing out B removes their cross terms, giving

    rho_A = (|0>^|A|<0|^|A| + |1>^|A|<1|^|A|)/2.

Its two nonzero eigenvalues are 1/2 and 1/2, so the entanglement entropy
across that cut is one bit. This does not deny GHZ multipartite entanglement;
it identifies the exact quantity being counted.

The relative phase is real physical information, but it is publicly known.
For example,

    <X tensor ... tensor X> = Re(zeta)=1/sqrt(2),

whereas the ordinary positive-phase GHZ state's corresponding expectation
is 1. The exact sparse simulator checks both facts. This particular circuit
family is also classically tractable using its two-amplitude representation;
no claim about efficient simulation of arbitrary 128-qubit circuits follows.

## 4. Correct the security quantifiers

QPT describes quantum polynomial-time algorithms. BQP classifies decision
(or promise) problems solvable by suitable uniform polynomial-size quantum
circuit families with bounded error [S3]. State preparation alone supplies
no decision problem or acceptance criterion that has been shown to be in
BQP. Neither term defines 128-bit cryptographic strength by the number
of qubits used.

The circuit theorem establishes the existential statement

    There exists an efficient P_n that prepares the specified state.

A signature-security theorem needs a bound of a different form:

    For every adversary A in a specified quantum resource class R,
    Pr[A outputs a valid fresh-message forgery] <= epsilon_R. (2)

In an asymptotic theorem, the probability must be negligible as the
security parameter grows. A concrete theorem additionally fixes parameter
sets, query counts, computational resources and the target success bound.
A 128-bit failure exponent and a 2^128-operation work threshold are different
claims, as established in the previous margin sweep.

The preparation P_n contains no SLH-DSA challenge public key, signing
oracle, hash-security game or acceptance rule for a forged signature.
Consequently, (1) provides no upper bound for (2). This is a logical gap,
not a missing factor that can be supplied by substituting n=128.

## 5. The actual proof contribution: public-state simulation

Fix an arbitrary signature game G and an adversary A that is initially
given the state |psi_n> from (1) in a fresh register. Assume this register
is independent of the key, challenge, oracle state and A's other initial
registers. This independence refers to the moment of preparation; A may
subsequently interact it with public data or oracle responses.

Construct B in the ordinary game: initialize n zero qubits, apply P_n,
then execute A with that register and forward every permitted oracle
interaction exactly as in G. After preparation the joint states in the
two experiments are identical. The continuation is the same quantum
process, including measurements and adaptive classical interactions.
Therefore the distributions of the entire transcripts and final output
are identical, and

    Pr[B wins ordinary G] = Pr[A wins G with supplied psi_n]. (3)

The extra preparation uses n+1 logical gates and no signing or hash-oracle
queries. In a compatible gate-count model, if A has a t-gate continuation,

    Adv_G,psi_n(t,q_H,q_S)
        <= Adv_G(t+n+1,q_H,q_S).                             (4)

The initialized n-qubit register must be included in the width/memory
budget; (4) suppresses that coordinate only to simplify notation. It
does not say that the advantages at the same strict time budget are equal.
For polynomial n, the simulator is still QPT whenever A is QPT.

If c independent copies are needed, prepare each one: the extra gate
cost is c(n+1). This construction does not clone an unknown quantum state.
An extractor that reinitializes adversaries or requires extra copies must
include those costs. The lemma does not grant inverse signing-oracle
access, hidden keys, or permission to erase signing-query history.

If a physical preparation supplies a state within trace distance eta of
the ideal one, contractivity under quantum processing bounds the change
in any final event probability by eta for one supplied copy. A hybrid
argument gives at most c*eta for c independent preparations with that
guarantee. This conditional observation requires an actual distance bound;
no physical error rate is measured here. The ideal gate model has eta=0.

The same point can be seen for a classical key K before any subsequent
interaction: rho_KQ=rho_K tensor |psi_n><psi_n|, so the auxiliary register
by itself has zero mutual information with K. This is not a claim that
an adversary cannot learn from later public-key or oracle interactions.

## 6. Insert the lemma into the current signature reduction

Retain the v1.38 premises and define epsilon_SLH as the ordinary single-user
SLH-DSA-SHAKE-256s fresh-message forgery advantage at stated resources.
The quantum adversary model already permits H, T and CNOT gates.

If its reduction uses c fresh copies of this 128-qubit state, a conservative
way to charge their preparation is

    p_conflict <= kappa_E + L_E [delta_B
                  + 64 epsilon_SLH(t_R+129c,q_H,q_S)].       (5)

Here t_R counts the other reduction work. Equation (5) assumes the exact
modeled setup; any separately justified outer setup-distance term is added
as before. The same width, oracle model, complete query log and
oracle-respecting extractor requirements remain in force. If state
preparation is already counted in t_R, do not add it again.

For the known static set of 21 corrupt seats, the existing identity factor
43 applies instead of 64. The mandatory P-384/SLH-DSA AND-hybrid still
projects to the SLH component. Neither hardware acceleration, ML-KEM nor
this public state changes these signature-conversion factors.

Thus the phase proposal closes a modeling question: adversaries using this
specific resource fit the same security game after accounting for its
preparation. It does not lower epsilon_SLH or turn it into 2^-128. The
remaining numerical primitive bound still has to come from the applicable
SLH/hash-property security argument. FIPS 205 itself bases SLH-DSA security
on hash preimage and related properties [S4].

## 7. Exact validation performed

The executable section uses the cyclotomic field Q[zeta]/(zeta^4+1) with
rational coefficients. It stores only populated computational basis states,
so it handles this 128-qubit family without allocating 2^128 entries.
Twelve test groups check the exact target state, normalization, reverse
preparation, two-outcome probabilities, relative-phase interference,
global-phase invariance, per-link phase accumulation, reduced density
matrices, an alternative fanout schedule and supplied-versus-prepared
state equivalence in a finite example.

The count sweep covers n=120..136 and comparison values 1,2,32,64,92,256.
The general statements are proved above; finite tests only check their
implementation. No cryptographic signatures, hardware circuits, physical
coherence times or numerical security advantages are tested.

Sources:

[S1] IBM Quantum, TGate documentation. Matrix and phase convention.
https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.TGate

[S2] IBM Quantum Learning, Limitations on quantum information. Global and
relative phase distinction.
https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/quantum-circuits/limitations-on-quantum-information

[S3] John Watrous, Quantum Computational Complexity. Quantum circuit
families and the BQP definition.
https://cs.uwaterloo.ca/~watrous/Papers/QuantumComputationalComplexity.pdf

[S4] NIST, FIPS 205, Section 1.1. The signature-security assumptions.
https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf

Equations (1) and the phase variants are direct derivations of the supplied
circuit. Equations (3)-(5) are the public-state simulation argument developed
here. These sources are not cited as proofs of the complete quorum scheme.

Run --explain to print this addendum or --self-test to reproduce the checks.


Path note. This file is domains/05-extraction-and-signature-reductions/src/phase_ghz_security_check.py.
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

from fractions import Fraction as F
import argparse
import unittest

# Exact arithmetic in Q[zeta]/(zeta^4+1), zeta=exp(i*pi/4).
# No floating point, quantum hardware or cryptographic signing is used.
ZERO=(F(0),F(0),F(0),F(0))
ONE=(F(1),F(0),F(0),F(0))
ZETA=(F(0),F(1),F(0),F(0))
INV_SQRT2=(F(0),F(1,2),F(0),F(-1,2))


def add(a,b):
    return tuple(x+y for x,y in zip(a,b))


def scale(a,s):
    return tuple(x*s for x in a)


def mul(a,b):
    out=[F(0)]*4
    for i,x in enumerate(a):
        for j,y in enumerate(b):
            k=i+j
            out[k%4]+=x*y*(-1 if k>=4 else 1)
    return tuple(out)


def zeta_power(k):
    k%=8
    out=[F(0)]*4
    out[k%4]=F(-1 if k>=4 else 1)
    return tuple(out)


def conjugate(a):
    out=ZERO
    for k,c in enumerate(a):
        out=add(out,scale(zeta_power(-k),c))
    return out


def abs_squared(a):
    result=mul(conjugate(a),a)
    if result[1:]!=(F(0),F(0),F(0)):
        raise ValueError('this helper is restricted to rational probabilities')
    return result[0]


def norm(state):
    return sum((abs_squared(a) for a in state.values()),F(0))


def validate_n(n):
    if type(n) is not int or n<1:
        raise ValueError('positive qubit count required')


def deposit(state,x,amplitude):
    value=add(state.get(x,ZERO),amplitude)
    if value==ZERO:
        state.pop(x,None)
    else:
        state[x]=value


def hadamard(state,q):
    out={}
    for x,a in state.items():
        bit=(x>>q)&1
        low=x&~(1<<q)
        value=mul(a,INV_SQRT2)
        deposit(out,low,value)
        deposit(out,low|(1<<q),scale(value,-1 if bit else 1))
    return out


def phase(state,q,power=1):
    return {x:mul(a,zeta_power(power)) if (x>>q)&1 else a for x,a in state.items()}


def cnot(state,control,target):
    if control==target:
        raise ValueError('distinct CNOT wires required')
    return {x^(1<<target) if (x>>control)&1 else x:a for x,a in state.items()}


def prepare(n,variant='one_T'):
    """Sparse exact simulation of the supplied circuit family, not arbitrary QC.

    q0 is the least-significant bit in the integer basis label.
    conditional_per_link inserts T on the control after each CNOT.
    global_per_link multiplies the entire state by zeta after each CNOT.
    """
    validate_n(n)
    if variant not in ('one_T','conditional_per_link','global_per_link'):
        raise ValueError('unknown circuit variant')
    state=phase(hadamard({0:ONE},0),0)
    for q in range(n-1):
        state=cnot(state,q,q+1)
        if variant=='conditional_per_link':
            state=phase(state,q)
        elif variant=='global_per_link':
            state={x:mul(a,ZETA) for x,a in state.items()}
    return state


def reverse_preparation(state,n):
    for q in reversed(range(n-1)):
        state=cnot(state,q,q+1)
    return hadamard(phase(state,0,-1),0)


def x_parity_expectation(state,n):
    mask=(1<<n)-1
    result=ZERO
    for x,a in state.items():
        result=add(result,mul(conjugate(a),state.get(x^mask,ZERO)))
    return result


def density(state):
    return {(x,y):mul(a,conjugate(b)) for x,a in state.items() for y,b in state.items()}


def reduced_density(state,keep):
    """Partial trace retaining the wire subset keep; exact and sparse."""
    keep=tuple(keep)
    mask=sum(1<<q for q in keep)
    def project(x):
        return sum(((x>>q)&1)<<j for j,q in enumerate(keep))
    out={}
    for x,a in state.items():
        for y,b in state.items():
            if x&~mask==y&~mask:
                key=(project(x),project(y))
                out[key]=add(out.get(key,ZERO),mul(a,conjugate(b)))
    return {k:v for k,v in out.items() if v!=ZERO}


def binary_tree_schedule(n):
    """Alternative all-to-all schedule: disjoint CNOTs in each layer."""
    validate_n(n)
    layers=[]
    populated=1
    while populated<n:
        take=min(populated,n-populated)
        layers.append(tuple((q,populated+q) for q in range(take)))
        populated+=take
    return tuple(layers)


def prepare_tree(n):
    state=phase(hadamard({0:ONE},0),0)
    for layer in binary_tree_schedule(n):
        for c,t in layer:
            state=cnot(state,c,t)
    return state


def independent_bit_state(secret):
    """Synthetic classical bit, not a cryptographic secret or security game."""
    if secret not in (0,1):
        raise ValueError('bit required')
    return {secret:ONE}


def tensor_with_ghz(secret,n):
    # Qubit 0 stores the synthetic bit; the public GHZ register uses 1..n.
    return {(x<<1)|secret:a for x,a in prepare(n).items()}


class PhaseTests(unittest.TestCase):
    def test_01_phase_is_unit_modulus(self):
        self.assertEqual(mul(ZETA,conjugate(ZETA)),ONE)
        for k in range(-16,17):
            self.assertEqual(abs_squared(zeta_power(k)),1)
        self.assertEqual(zeta_power(8),ONE)
        self.assertEqual(mul(INV_SQRT2,INV_SQRT2),scale(ONE,F(1,2)))

    def test_02_exact_128_qubit_state(self):
        state=prepare(128)
        self.assertEqual(state,{0:INV_SQRT2,(1<<128)-1:mul(INV_SQRT2,ZETA)})
        self.assertEqual(norm(state),1)
        self.assertEqual(1+1+127,129)

    def test_03_incremental_qubit_counts(self):
        for n in tuple(range(120,137))+(1,2,32,64,92,256):
            state=prepare(n)
            self.assertEqual(len(state),2)
            self.assertEqual(norm(state),1)
            self.assertEqual(state[(1<<n)-1],mul(INV_SQRT2,ZETA))

    def test_04_reverse_circuit_returns_initial_state(self):
        for n in (1,2,32,127,128,129):
            self.assertEqual(reverse_preparation(prepare(n),n),{0:ONE})

    def test_05_computational_measurements_have_two_outcomes(self):
        state=prepare(128)
        probabilities={x:abs_squared(a) for x,a in state.items()}
        self.assertEqual(probabilities,{0:F(1,2),(1<<128)-1:F(1,2)})

    def test_06_relative_phase_is_visible_in_other_basis(self):
        self.assertEqual(x_parity_expectation(prepare(128),128),INV_SQRT2)
        standard_ghz=phase(prepare(128),0,-1)
        self.assertEqual(x_parity_expectation(standard_ghz,128),ONE)

    def test_07_global_phase_changes_no_density_matrix(self):
        for n in (2,127,128,129):
            self.assertEqual(density(prepare(n)),density(prepare(n,'global_per_link')))

    def test_08_extra_conditional_phases_wrap_modulo_eight(self):
        for n in range(120,137):
            state=prepare(n,'conditional_per_link')
            self.assertEqual(state[(1<<n)-1],mul(INV_SQRT2,zeta_power(n)))
        self.assertEqual(x_parity_expectation(prepare(128,'conditional_per_link'),128),ONE)
        self.assertNotEqual(prepare(128),prepare(128,'conditional_per_link'))

    def test_09_nontrivial_bipartition_has_two_equal_eigenvalues(self):
        state=prepare(128)
        for keep in ((0,),tuple(range(64)),tuple(range(127))):
            last=(1<<len(keep))-1
            self.assertEqual(reduced_density(state,keep),{(0,0):scale(ONE,F(1,2)),(last,last):scale(ONE,F(1,2))})

    def test_10_binary_tree_schedule_has_valid_disjoint_layers(self):
        for n in (1,2,3,32,127,128,129):
            layers=binary_tree_schedule(n)
            self.assertEqual(sum(len(layer) for layer in layers),n-1)
            for layer in layers:
                wires=[q for pair in layer for q in pair]
                self.assertEqual(len(wires),len(set(wires)))
            self.assertEqual(prepare_tree(n),prepare(n))
        self.assertEqual(2+len(binary_tree_schedule(128)),9)

    def test_11_independent_auxiliary_state_has_same_reduced_state_for_both_bits(self):
        keep=tuple(range(1,6))
        self.assertEqual(reduced_density(tensor_with_ghz(0,5),keep),
                         reduced_density(tensor_with_ghz(1,5),keep))
        # Finite illustration of independence. General security simulation
        # is proved in the accompanying text, not inferred from two cases.

    def test_12_gate_sequence_simulates_independent_state_input_exactly(self):
        n=5
        for bit in (0,1):
            supplied=tensor_with_ghz(bit,n)
            constructed=phase(hadamard(independent_bit_state(bit),1),1)
            for q in range(1,n):
                constructed=cnot(constructed,q,q+1)
            self.assertEqual(constructed,supplied)
            # A subsequent interaction is also identical in the two runs.
            self.assertEqual(cnot(constructed,0,1),cnot(supplied,0,1))


def main():
    parser=argparse.ArgumentParser(description='Exact phase-GHZ validation and public auxiliary-state simulation lemma; no QPT-128 certification.')
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--explain',action='store_true')
    modes.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.explain:
        print(__doc__)
        return 0
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PhaseTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
