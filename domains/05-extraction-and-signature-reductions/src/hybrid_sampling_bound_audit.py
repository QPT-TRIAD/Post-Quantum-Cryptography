#!/usr/bin/env python3
r"""
# Hybrid forgery and quantum sampling: corrected proof — v1.41

2026-09-10. Signature-security scope only. Continues v1.38–v1.40.

Result: the proposed exp(-256 Delta^2) signature-forgery bound is not
established. The hybrid projection remains valid; a public GHZ state does
not provide an authentication gap. Below are rigorous conditional sampling
lemmas, including a sharper route to a 2^-128 probability bound, and the
precise premise that the proposed state fails to supply.

Run: python3 hybrid_sampling_bound_audit.py
Read this proof: python3 hybrid_sampling_bound_audit.py --proof

## 1. Security game and the correct AND reduction

EUF-CMA means existential unforgeability under chosen-message attack. The
adversary wins by producing one accepted signature on a fresh message; it
does not need universal forgery. Here messages include the complete context,
suite, configuration, domain, seat, and approval binding fixed in v1.38.
Signing queries are classical, although the adversary may compute quantumly.

Retain independently generated ECDSA-P384 and SLH-DSA-SHAKE-256s keys,
authenticated binding of the full key bundle and acceptance policy, canonical
framing of the same logical message, mandatory AND verification, and a
complete SLH signing-query log. Freshness must hold against that full log,
including any extra component interface. Dedicated keys avoid cross-use.

For one common experiment, let T and S be the events that the respective
components validate the fresh output. Then

    Pr[T and S] = Pr[T] Pr[S | T] <= min(Pr[T], Pr[S]).       (1)

The conditional expression assumes Pr[T]>0; otherwise the intersection is
zero. Independent keys do not make these events independent: they share an
adversary, transcript and output. For example, T=S=E with Pr[E]=1/2 gives
intersection 1/2 and product of marginals 1/4. This probability counterexample
disproves a general product rule; it is not an attack on a real signature.

The cryptographic proof is projection. A reduction B receives the SLH
challenge public key, generates the traditional key locally, forwards SLH
signing requests, and supplies traditional signatures locally. On a fresh
accepted hybrid output it returns the SLH component. Acceptance and complete
freshness imply B wins the SLH EUF-CMA game on every hybrid success. Thus

    Adv_Hybrid(A) <= Adv_SLH(B).                              (2)

There is no probability loss in this projection, but local key generation,
signing and all simulation work count toward B's resources. A separate
projection to the traditional component gives a minimum of applicable
component bounds at their respective resource counts, not their product.

Taking epsilon_Trad=1 is a conservative upper bound that credits no
traditional security. It is not a proof that Shor succeeds with probability
one on a 128-qubit device. Even granting this upper bound, a valid PQ bound
is still required. In particular, (2) does not supply a numerical SLH bound.

## 2. A public state cannot supply the claimed authentication gap

Let zeta=exp(i*pi/4) and

    |psi_n> = (|0^n> + zeta |1^n>)/sqrt(2).

The v1.40 induction proves that H, T, and n-1 CNOTs prepare it using n+1
ideal logical gates. Its phase and preparation are public. At n=128 this
costs 129 logical gates, so preparing a fresh copy is efficient.

More generally, suppose the honest auxiliary state is an efficiently
preparable rho_x determined entirely by public x. For any verifier accept
effect 0<=M_{k,x}<=I, even one chosen using secret verifier randomness k,

    Pr[accept honest state | k,x] = Tr(M_{k,x} rho_x)
                                 = Pr[accept reproduced state | k,x]. (3)

Proof: both tests receive the same density operator; measurement outcome
probabilities are linear functions of that operator. Averaging over k
preserves equality. Thus secret measurement choices alone do not distinguish
these two sources. No unknown state must be cloned or intercepted.

For the ideal state-only projector Pi=|psi_n><psi_n|, the reproduced state
passes with Tr(Pi^2)=Tr(Pi)=1. This is acceptance of that state test, NOT
probability one of forging an SLH or hybrid signature. For any other test,
the two acceptance probabilities still agree. The state contributes no
positive honest-versus-reproduction mismatch gap Delta.

Equation (3) is scoped to the public auxiliary state. It does not rule out
protocols with secret-dependent states, authenticated distribution, or a
separately secure signature binding. Those mechanisms require their own
specification and proof; none follows from the phase zeta itself.

Also, one n-qubit GHZ state is not n independent verification trials.
Computational-basis measurement gives X_1=...=X_n=B with B a fair bit. In
this distribution every E[X_i]=1/2, but

    Pr[(X_1+...+X_n)/n = 0] = 1/2,

which exceeds exp(-n/2) for n>=2. A Hoeffding substitution with Delta=1/2
fails because its probabilistic premises have been dropped. These X_i are
an illustrative correlated distribution, not a specified decoy test.

## 3. What actually makes the proposed exponential bound valid

Classical version: take independent X_i in [0,1], representing mismatches.
Write mu=N^-1 sum_i E[X_i]. If acceptance requires Xbar<=a, and every
relevant attack satisfies mu>=a+Delta with Delta>0, Hoeffding gives

    Pr[accept] <= exp(-2 N Delta^2).                          (4)

This is the one-sided version of Hoeffding's bounded-variable inequality
[S1, Theorem 2]. Independence can be replaced by a proved sequential
condition, which is often more useful for an adaptive adversary:

Let F_i be the classical history through measured outcome i, and set
mu_i=E[X_i | F_{i-1}]. Require mu_i>=a+Delta almost surely for every i and
every allowed attacker. Then (4) also holds, without independence.

Proof. D_i=X_i-mu_i is conditionally centered and has conditional range
width at most one. The conditional form of Hoeffding's exponential-moment
lemma gives E[exp(-lambda D_i)|F_{i-1}]<=exp(lambda^2/8).
Iterated conditioning gives

    E[exp(-lambda sum_i D_i)] <= exp(N lambda^2/8).

Acceptance implies sum_i D_i<=-N Delta. Markov's inequality bounds its
probability by exp(-lambda N Delta+N lambda^2/8). Choosing lambda=4 Delta
proves (4). This derivation applies to the classical outcomes of a quantum
experiment only if the conditional-mean premise is proved for all allowed
quantum strategies and their residual states. It does not assume that
quantum measurements automatically establish that premise.

The correlated example fails this stronger premise too: after observing
X_1=0, the next conditional mismatch mean is zero. Public-state reproduction
also prevents the proposed positive authentication gap.

## 4. Sharper partial theorem: all-pass amplification

An exact sequential bound can be stronger than (4). Let V_i indicate a
passed check. Suppose, for every permitted adversary and every reachable
prior transcript on which all earlier checks passed,

    Pr[V_i=1 | that transcript] <= r_i.                      (5)

The r_i are fixed upper bounds, not guessed marginal frequencies. If G_i
is the event that the first i checks all passed, then

    Pr[G_i] = E[1_{G_{i-1}} Pr[V_i=1 | F_{i-1}]]
            <= r_i Pr[G_{i-1}].

Induction proves Pr[G_N]<=product_i r_i. In particular, if every r_i=1/2,

    Pr[all N checks pass] <= 2^-N.                           (6)

This is a legitimate product of CONDITIONAL guarantees. It needs neither
independent keys nor independent trials. To bound a signature forgery,
one must additionally prove that a fresh accepted forgery implies G_N
and that (5) holds for that actual cryptographic experiment. No such bridge
or r_i=1/2 guarantee is supplied by the public GHZ state. For its ideal
projector test, reproduction instead gives r_i=1 on every surviving path.

For tolerance of up to t mismatches, assume the stronger uniform premise
Pr[V_i=1 | F_{i-1}]<=r on EVERY reachable history, including previous
failures. Then the mismatch count stochastically dominates Bin(N,1-r), so

    Pr[at most t mismatches]
      <= sum_{j=0}^t binom(N,j) (1-r)^j r^(N-j).             (7)

Proof by coupling the classical outcome law: at step i use a fresh uniform
U_i, with mismatch probability p_i(history)>=1-r. Define X_i=1[U_i<=p_i]
and Y_i=1[U_i<=1-r]. This realizes the adaptive law for X, gives independent
Bernoulli(1-r) variables Y, and X_i>=Y_i pointwise. This is a mathematical
coupling of measured classical outcomes, not copying quantum registers.

At r=1/2, N=128 and t=0, (7) is exactly 2^-128. At t=1 it is
129*2^-128, approximately 2^-120.988773. These are conditional calculations;
the experiment has not been shown to meet their premises. Zero tolerance
can also cause honest rejection under noise; correctness and adversarial
soundness must both be established for an actual protocol.

## 5. Evaluate the supplied formula, without mistaking it for a proof

If (4)'s premises did hold, its failure exponent would be

    b_H = -log2(exp(-2 N Delta^2)) = 2 N Delta^2 / ln(2).

At N=128:

| Delta | Failure exponent supplied by Hoeffding |
|---|---:|
| 0 | 0: bound is 1 |
| 1/4 | 23.083121 |
| 1/2 | 92.332483 |
| sqrt(ln(2)/2), about 0.588705 | 128 |

At Delta=1/2, exp(-64) is about 1.60381e-28, which is greater than 2^-128.
The number of trials sufficient for this particular bound is

    N >= ceil(b ln(2) / (2 Delta^2)).                        (8)

| Target exponent b | Hoeffding trials at Delta=1/2 | All-pass trials at r=1/2 |
|---|---:|---:|
| 32 | 45 | 32 |
| 64 | 89 | 64 |
| 92 | 128 | 92 |
| 127 | 177 | 127 |
| 128 | 178 | 128 |
| 129 | 179 | 129 |
| 134 | 186 | 134 |
| 136 | 189 | 136 |

The two columns use different bounds; the right column also requires
all-pass acceptance. Failure of a loose Hoeffding estimate to reach 128
does not prove impossibility: (6) can be sharper under its actual premises.
Neither column makes the public-state proposal secure by increasing N.

Quantum sampling needs its own theorem-to-protocol match. Bouman and Fehr
[S2, Theorem 3] bound their quantum sampling error, defined using trace
distance to suitable ideal states, by the square root of their classical
sampling error. Thus a matching classical error 2^-b would give at most
2^(-b/2) under that conversion. This quantity is not automatically a
signature-forgery probability. Applying that framework requires a specified
sampling strategy, ideal-state property and subsequent security argument.
It cannot be replaced by a generic claim about decoy photons. Conversely,
do not append a square-root loss to (4) or (6) when they have already been
proved directly for the experiment's classical acceptance event.

## 6. Consequence for the existing signature reduction

Under the still-explicit v1.38 extractor, setup, approval and oracle premises,
with at most 21 adaptive corruptions among 64 seats, the signature term is

    p_conflict <= kappa_E + L_E (delta_B + 64 epsilon_SLH).   (9)

Here kappa_E and L_E are extractor error/loss, delta_B is body-binding
failure in the extractor experiment, and epsilon_SLH is single-user
fresh-message forgery advantage at the reduction's actual resources.
The public-state simulation in v1.40 charges 129c gates for c independently
prepared copies, unless already counted. It adds no success-probability
multiplier. A separately justified outer setup error is added as before.

There is no justified substitution epsilon_SLH := exp(-256 Delta^2).
SLH-DSA's numerical bound must match its hash properties, parameter set,
oracle model, signing interface and resource budget. FIPS 205 describes
EUF-CMA strength categories through resource comparisons, not a qubit count
or an automatically applicable failure probability [S3, Section 11].

For illustration ONLY, if a valid primitive bound epsilon_SLH<=2^-b were
established and L_E=1, kappa_E=delta_B=0, then (9) requires b>=134 to
obtain p_conflict<=2^-128. Reserving one quarter of the total failure budget
for the signature term would require b>=136. These are inherited reduction
budgets, not established primitive advantages or sample-count prescriptions.

QPT denotes quantum polynomial-time adversaries. A 128-qubit register,
a bound 2^-128 on a specified event, and a lower bound of 2^128 operations
are different assertions. None may be silently substituted for another.

Closed here: the AND probability error, the public-state mismatch claim,
the missing concentration hypotheses, and the loose-versus-exact sampling
calculation. Still open: an applicable concrete SLH signature-security bound.
The publicly known phase state does not discharge it.

## 7. Validation and sources

The executable checks exact finite probability counterexamples, the GHZ
projector identity in Q[zeta]/(zeta^4+1), adaptive outcome trees, exact
binomial tails, noise tolerance and the factor-64 budget. Decimal arithmetic
at 80-digit precision evaluates transcendental expressions; those decimal
checks are numerical validation, not interval-certified proofs. General
statements are proved above. No real signature, quantum hardware, primitive
hardness, extractor or deployed hash security is certified by these tests.

[S1] Wassily Hoeffding. Probability Inequalities for Sums of Bounded Random
Variables. JASA 58(301), 13–30, 1963. Theorem 2 and exponential-moment method.
https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf
https://doi.org/10.1080/01621459.1963.10500830

[S2] Niek Bouman and Serge Fehr. Sampling in a Quantum Population, and
Applications. CRYPTO 2010; arXiv:0907.4246v3. Definitions and Theorem 3.
https://ir.cwi.nl/pub/16828/16828B.pdf

[S3] NIST. FIPS 205: Stateless Hash-Based Digital Signature Standard.
https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf

Equations (1)–(3) are direct probability, reduction and density-matrix
arguments. The sequential derivations and calculations in (4)–(9) are given
here with their premises. These sources do not certify this quorum scheme.

Path note. This file is domains/05-extraction-and-signature-reductions/src/hybrid_sampling_bound_audit.py.
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

from decimal import Decimal, localcontext, ROUND_CEILING
from fractions import Fraction as F
from itertools import product
from math import comb
import argparse
import unittest


def dec(x):
    if isinstance(x, F):
        return Decimal(x.numerator) / Decimal(x.denominator)
    return Decimal(x)


def hoeffding(n, gap):
    with localcontext() as ctx:
        ctx.prec = 80
        return (-2 * Decimal(n) * dec(gap) ** 2).exp()


def hoeffding_samples(bits, gap):
    if bits <= 0 or gap <= 0:
        raise ValueError('positive target and positive proved gap required')
    with localcontext() as ctx:
        ctx.prec = 80
        x = Decimal(bits) * Decimal(2).ln() / (2 * dec(gap) ** 2)
        return int(x.to_integral_value(rounding=ROUND_CEILING))


def binomial_tail(n, tolerated_failures, pass_bound=F(1, 2)):
    """Conditional theorem endpoint; does not establish its premise."""
    if type(n) is not int or n < 1:
        raise ValueError('positive integer sample count required')
    if type(tolerated_failures) is not int or not 0 <= tolerated_failures <= n:
        raise ValueError('failure tolerance must be an integer in [0,n]')
    if not isinstance(pass_bound, F) or not 0 <= pass_bound <= 1:
        raise ValueError('exact rational pass bound in [0,1] required')
    return sum((F(comb(n, j)) * (1-pass_bound)**j * pass_bound**(n-j)
                for j in range(tolerated_failures+1)), F(0))


def outcome_tree(n, conditional_pass):
    """Enumerate a small classical joint law; 1 is pass and 0 is fail."""
    law = {(): F(1)}
    for _ in range(n):
        following = {}
        for history, mass in law.items():
            q = conditional_pass(history)
            if not isinstance(q, F) or not 0 <= q <= 1:
                raise ValueError('invalid conditional probability')
            for value, chance in ((1, q), (0, 1-q)):
                if mass * chance:
                    following[history+(value,)] = mass * chance
        law = following
    return law


def acceptance(law, tolerated_failures):
    return sum((mass for h, mass in law.items()
                if h.count(0) <= tolerated_failures), F(0))


# Exact scalar arithmetic for the two-dimensional GHZ support. It is not
# a simulation of an arbitrary 128-qubit state or of a signature algorithm.
ZERO = (F(0),) * 4
ONE = (F(1), F(0), F(0), F(0))
ZETA = (F(0), F(1), F(0), F(0))


def cadd(a, b):
    return tuple(x+y for x, y in zip(a, b))


def cscale(a, s):
    return tuple(x*s for x in a)


def cmul(a, b):
    result = [F(0)] * 4
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            k = i+j
            result[k % 4] += x*y*(-1 if k >= 4 else 1)
    return tuple(result)


def conj(a):
    result = ZERO
    for k, x in enumerate(a):
        power = (-k) % 8
        term = [F(0)] * 4
        term[power % 4] = x*(-1 if power >= 4 else 1)
        result = cadd(result, tuple(term))
    return result


def matrix_mul(a, b):
    return tuple(tuple(cadd(cmul(a[i][0], b[0][j]), cmul(a[i][1], b[1][j]))
                       for j in range(2)) for i in range(2))


class AuditTests(unittest.TestCase):
    def test_01_marginal_product_counterexample(self):
        # Same success event E in both components, two equiprobable atoms.
        law = {(False, False): F(1, 2), (True, True): F(1, 2)}
        t = sum(m for (a, b), m in law.items() if a)
        s = sum(m for (a, b), m in law.items() if b)
        joint = law[(True, True)]
        self.assertEqual(joint, F(1, 2))
        self.assertEqual(t*s, F(1, 4))
        self.assertGreater(joint, t*s)
        self.assertEqual(joint/t, 1)  # Conditional success differs from s.
        self.assertLessEqual(joint, min(t, s))

    def test_02_intersection_minimum_for_finite_laws(self):
        # All distributions on four atoms with denominator eight.
        for weights in product(range(9), repeat=3):
            d = 8-sum(weights)
            if d < 0:
                continue
            a, b, c = map(lambda x: F(x, 8), weights)
            joint = F(d, 8)
            self.assertEqual(a+b+c+joint, 1)
            self.assertLessEqual(joint, min(b+joint, c+joint))

    def test_03_public_phase_projector_accepts_reproduction(self):
        # Pi in basis [|0^n>,|1^n>], for any n>=1.
        self.assertEqual(cmul(ZETA, conj(ZETA)), ONE)
        half = cscale(ONE, F(1, 2))
        pi = ((half, cscale(conj(ZETA), F(1, 2))),
              (cscale(ZETA, F(1, 2)), half))
        squared = matrix_mul(pi, pi)
        self.assertEqual(squared, pi)
        self.assertEqual(cadd(squared[0][0], squared[1][1]), ONE)

    def test_04_correlated_samples_violate_naive_hoeffding(self):
        # All bits equal one fair bit; each marginal failure mean is 1/2.
        def q(history):
            return F(1, 2) if not history else F(history[0])
        law = outcome_tree(8, q)
        self.assertEqual(acceptance(law, 0), F(1, 2))
        self.assertEqual(q((1,)), 1)  # Violates conditional pass <=1/2.
        for n in (2, 32, 64, 92, 128):
            self.assertGreater(Decimal('0.5'), hoeffding(n, F(1, 2)))

    def test_05_dependent_checks_obey_conditional_tail(self):
        # Depends on previous outcomes, yet pass chance is always <=1/2.
        def q(history):
            return F(1, 2) if history.count(0) % 2 == 0 else F(1, 4)
        for n in range(1, 9):
            law = outcome_tree(n, q)
            self.assertEqual(sum(law.values()), 1)
            self.assertEqual(acceptance(law, 0), F(1, 1 << n))
            for t in range(n+1):
                self.assertLessEqual(acceptance(law, t), binomial_tail(n, t))
                if F(t, n) < F(1, 2):
                    with localcontext() as ctx:
                        ctx.prec = 80
                        self.assertLessEqual(dec(acceptance(law, t)),
                                             hoeffding(n, F(1, 2)-F(t, n)))

    def test_06_uniform_conditional_bound_has_exact_all_pass_endpoint(self):
        for n in (32, 64, 92, 127, 128, 129, 134, 136):
            self.assertEqual(binomial_tail(n, 0), F(1, 1 << n))
        # IID law attains the tail, checked by enumerating small experiments.
        for r in (F(1, 4), F(1, 2), F(3, 4)):
            law = outcome_tree(7, lambda h: r)
            for t in range(8):
                self.assertEqual(acceptance(law, t), binomial_tail(7, t, r))

    def test_07_noise_tolerance_changes_the_budget(self):
        self.assertEqual(binomial_tail(128, 1), F(129, 1 << 128))
        self.assertGreater(binomial_tail(128, 1), F(1, 1 << 128))
        # With one permitted failure, fair-check endpoint first reaches 128
        # at N=136: 135 is insufficient and 136 is sufficient.
        self.assertGreater(binomial_tail(135, 1), F(1, 1 << 128))
        self.assertLessEqual(binomial_tail(136, 1), F(1, 1 << 128))

    def test_08_hoeffding_numerical_thresholds(self):
        expected = {32: 45, 64: 89, 92: 128, 127: 177, 128: 178,
                    129: 179, 134: 186, 136: 189}
        with localcontext() as ctx:
            ctx.prec = 80
            for bits, n in expected.items():
                self.assertEqual(hoeffding_samples(bits, F(1, 2)), n)
                target = dec(F(1, 1 << bits))
                self.assertLessEqual(hoeffding(n, F(1, 2)), target)
                self.assertGreater(hoeffding(n-1, F(1, 2)), target)
            b = Decimal(64)/Decimal(2).ln()
            self.assertTrue(Decimal('92.33248') < b < Decimal('92.33249'))
            gap = (Decimal(2).ln()/2).sqrt()
            self.assertTrue(Decimal('.588705') < gap < Decimal('.588706'))

    def test_09_no_gap_and_certain_public_test_give_no_amplification(self):
        for n in (32, 64, 92, 128, 256, 512):
            self.assertEqual(hoeffding(n, F(0)), Decimal(1))
            self.assertEqual(binomial_tail(n, 0, F(1)), F(1))

    def test_10_square_root_and_quorum_losses_are_not_free(self):
        # Exact bookkeeping only, not a match of the sampling theorem to SLH.
        for b in (32, 64, 92, 128, 256):
            self.assertEqual(F(1, 1 << b)**2, F(1, 1 << (2*b)))
        self.assertEqual(64*F(1, 1 << 134), F(1, 1 << 128))
        self.assertEqual(64*F(1, 1 << 136), F(1, 4)*F(1, 1 << 128))
        self.assertGreater(64*F(1, 1 << 128), F(1, 1 << 128))


def report():
    with localcontext() as ctx:
        ctx.prec = 80
        ln2 = Decimal(2).ln()
        print('Conditional bounds only; QPT-128 is not established.')
        print('N=128, Delta=1/2: Hoeffding failure exponent =',
              f'{Decimal(64)/ln2:.9f}')
        print('N=128, all-pass conditional r=1/2: exact endpoint = 2^-128')
        print('N=128, one failure allowed, r=1/2: failure exponent =',
              f'{128-Decimal(129).ln()/ln2:.9f}')
        print('Public GHZ projector reproduction: state-test acceptance = 1')
        print('target | Hoeffding N at Delta=1/2 | all-pass N at r=1/2')
        for b in (32, 64, 92, 127, 128, 129, 134, 136):
            print(f'{b:6} | {hoeffding_samples(b, F(1, 2)):27} | {b:21}')
        print('No sampling endpoint is substituted for epsilon_SLH.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Proof audit and probability checks')
    parser.add_argument('--proof', action='store_true', help='print the full proof')
    args = parser.parse_args()
    if args.proof:
        print(__doc__)
    else:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(AuditTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
        report()
