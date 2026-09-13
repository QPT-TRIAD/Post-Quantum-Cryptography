#!/usr/bin/env python3
r"""
# SLH-DSA tree conditioning and the signature proof map — v1.42

2026-09-10. A companion to src/hybrid_sampling_bound_audit.py (v1.41).
Scope: signature-security reduction. No signature-suite parameters are changed.

Result: the proposed resolution still assumes its crucial conditional bound.
SLH-DSA tree verification does not establish 128 fresh one-bit challenges.
This file proves why refactoring verification cannot itself amplify security,
checks the proposed numerical formula, and extends the existing proof map
through the published hypertree theorem. The concrete QPT-128 endpoint
remains unestablished.

Run: python3 slh_tree_conditioning_audit.py
Read the mathematical discussion: add --proof.
All executable checks use synthetic probability laws or exact arithmetic.

## 1. Pin the standard and avoid changing the security target

SLH-DSA means Stateless Hash-Based Digital Signature Algorithm, not
"Spherical Linear-Tree-Based". FIPS 205's verifier is deterministic for a
fixed public key, message, signature and hash implementation. Algorithm 20
derives the digest and indices, reconstructs a FORS key, and calls Algorithm
13, which reconstructs successive XMSS roots and compares the final root
with PK.root. It generates no verifier challenges. WOTS+ supplies one-time
signatures; XMSS builds authentication trees; FORS is the few-time component.
Both deterministic and hedged signing are specified [S1].

The earlier proposed suite uses SLH-DSA-SHAKE-256s. The following comparison
does not replace it with a category-1 suite:

| FIPS 205 suffix | n (bytes) | h | d | h'=h/d | category |
|---|---:|---:|---:|---:|---:|
| SHAKE-128s | 16 | 63 | 7 | 9 | 1 |
| SHAKE-128f | 16 | 66 | 22 | 3 | 1 |
| SHAKE-256s | 32 | 64 | 8 | 8 | 5 |

These are parameter labels and geometry, not measured conditional pass
probabilities. NIST categories compare attack resources; category 1 does not
assert forgery probability <=2^-128 for every QPT adversary [S1, Section 11].

The prefix "128" must not stand simultaneously for qubit count, hash output
width, security parameter, failure exponent and attack-work exponent.
Concrete security needs an explicit resource profile, including time or
gates, hash queries, signing queries, targets and reduction overhead.

## 2. Refactoring invariance: the precise obstruction

Let V(pk,m,sig) be a verifier. Suppose a proposed sequential implementation
computes predicates C_1,...,C_r and, for every input and every fixed oracle,

    AND_i C_i(pk,m,sig) = V(pk,m,sig).                       (1)

Assume the adversary interface and freshness rule are unchanged and no new
challenge interaction is introduced. Then for every adversary A,

    Pr[fresh and AND_i C_i(A's output)]
       = Pr[fresh and V(A's output)].                       (2)

Proof: the event indicators agree pointwise for every experiment outcome.
Averaging over keys, adversary randomness, quantum measurement outcomes
and any initially sampled oracle preserves equality. A quantum adversary
does not invalidate this pointwise implication for its final classical
output. Verification work may change; the accepted language does not.

Thus splitting a root comparison into bits, or splitting a computation into
128 stages, cannot by itself improve the signature's acceptance probability.
A decomposition might help PROVE an existing bound if new conditional
hardness lemmas are established, but it does not manufacture those lemmas.
This is not an assertion that deterministic verifiers cannot be secure.

An elementary example makes the conditional issue explicit. Let E have
probability p>0 and define C_i=1_E for every i. Then

    Pr[all C_i=1]=p,
    Pr[C_1=1]=p,
    Pr[C_i=1 | previous checks passed]=1 for every i>=2.     (3)

The chain rule is correct; the proposed uniform per-step bound is false
for this example. Repeating a deterministic verifier on the same candidate
has exactly this structure, even when p is very small.

## 3. Whole-game security does not bound each conditioned subcheck

If F is the full fresh-forgery event and G is a preceding pass event, then

    Pr[F | G] = Pr[F and G]/Pr[G]
               <= min(1, epsilon/Pr[G])                    (4)

whenever Pr[F]<=epsilon and Pr[G]>0. It is not generally <=epsilon.
For G=F the conditional probability is one. Also, if F implies a partial
check V_i, then Pr[F]<=Pr[V_i], so an upper bound on F is not an upper
bound on V_i. The comparison proposed in the research trail reverses this implication.

Consequently, writing

    Pr[V_i passes | earlier passes] <= Adv_SLH(B)

requires a new reduction B for that exact conditional experiment. Conditioning
on a rare success event is not automatically an efficient QPT simulation.
It cannot be implemented by merely declaring a new probability space while
retaining the original resource budget or copies of a quantum residual state.

The min-entropy argument is also misplaced. If Y=f(public transcript) is
deterministic, then for every transcript z with positive probability,

    max_y Pr[Y=y | transcript=z]=1.

Thus Y's conditional guessing entropy is zero. Public path indices and
public root bits are not secret one-bit challenges. This does not make a
hash preimage easy to compute: computational difficulty of producing a
matching preimage is a different claim from hiding the target hash value.

Freshness is the absence of the final message/context from the complete
signing-query log. Randomizing a digest does not enforce message freshness
or prove that two digest values cannot coincide. A collision or repeated
randomizer is not eliminated by naming the digest "fresh".

## 4. The proposed numerical expression fails its own budget

The research trail proposed, without a matching theorem,

    epsilon_SLH <= q_s * L / 2^lambda + C(q_h),              (5)

where L was called "number of leaves" and C is nonnegative. Even granting
(5), with lambda=128, q_s=1 and L=2 its right-hand side is at least 2^-127.
For q_s=L=1 and C=0 it equals, rather than lies strictly below, 2^-128.
With q_s=2^20 and L=2^9, its first term is 2^-99.

For an integer q_s L>=1, a target 2^-s, and a separately supplied C, this
expression certifies the target only if

    C < 2^-s,
    2^lambda >= q_s L / (2^-s-C).                           (6)

At C=0, lambda>=s+ceil(log2(q_s L)) suffices for this expression. This is
algebra about (5), not an endorsement of (5) as an SLH security theorem.
An upper bound above the target does NOT prove that an actual forgery
probability exceeds the target; it means the bound cannot certify it.

## 5. Correct constructive route: an exhaustive-case reduction

Here is the extension to the earlier proof map. Barbosa et al. [S2,
Theorem 3] bound their fixed-length stateless hypertree game by three
alternatives: WOTS-TW forgery, WOTS-key compression collision, or tree-hash
collision. They use an exhaustive case distinction and sum its bounds.
These are alternative explanations of an accepted forgery, not independent
events that must all occur.

Within that paper's stated games, combine Theorems 4, 1, 2 and 3. Abbreviate
each advantage by its role, retaining the respective reduction adversaries,
target limits, tweak constraints and hash collections. The resulting ledger is

    E_paper = e_SKG + e_MKG + e_ITSR + e_DSPR + 3 e_TCR_F
              + e_FORS_tree + e_FORS_compress
              + e_WOTS + e_HT_compress + e_HT_tree,          (7)

and the paper's EUF-CMA advantage is at most E_paper. The underlying terms are:

| Ledger name | Exact property / construction in [S2] |
|---|---|
| e_SKG | PRF of SKG |
| e_MKG | PRF of MKG |
| e_ITSR | ITSR of MCO with CM |
| e_DSPR | SM-DT-DSPR of F |
| e_TCR_F | SM-DT-TCR of F; coefficient 3 from Theorem 2 |
| e_FORS_tree | SM-DT-TCR-C of TRH in the M-FORS collection |
| e_FORS_compress | SM-DT-TCR-C of TRCO |
| e_WOTS | M-EUF-GCMA of WOTS-TW$ in the hypertree collection |
| e_HT_compress | SM-DT-TCR-C of PKCO |
| e_HT_tree | SM-DT-TCR-C of TRH in the hypertree collection |

Proof of the combination: Theorem 4 contributes the two PRF terms plus
M-FORS$ and hypertree advantages. Substitute Theorem 1 for M-FORS$, then
Theorem 2 for its OpenPRE term. Substitute Theorem 3 for the hypertree
advantage. All coefficients are nonnegative, so each substitution preserves
the inequality. The FORS and hypertree TRH terms retain different games
and target limits even though they share a hash-role name.

For the hypertree, put ell=2^h' and R_i=ell^(d-i-1), the inner-tree count
at layer i. Theorem 3's target bounds are

    T_WOTS = T_HT_compress = ell * sum_{i=0}^{d-1} R_i,
    T_HT_tree = (ell-1) * sum_{i=0}^{d-1} R_i.               (8)

The latter simplifies exactly to ell^d-1=2^h-1. These are target-universe
limits of the theorem; they are not signing-query counts or a requirement
to materialize every tree. They do not justify multiplying q_s by a generic
leaf count. The FORS terms have their own distinct target bounds.

For intuition about the additive structure alone, let F be accepted
forgery and let B_1,B_2,B_3 be exhaustive explanations. Set D_1=F and B_1,
D_2=F and not B_1 and B_2, and D_3=F and not B_1 and not B_2 and B_3.
The D_i are disjoint and cover F, so Pr[F]=sum_i Pr[D_i]. Proving a
reduction for each D_i gives a sum of advantages, without independence.
This elementary event proof is separate from the nontrivial reductions
and game restrictions supplied in [S2].

Equation (7) is a partial-proof composition in the PUBLISHED games.
It is not silently relabeled as a concrete QPT theorem for deployed FIPS 205.
The applicable quantum games, resource overhead, WOTS bound, address/API
match and concrete hash-property advantages still require justification.
The corrected quantum analysis by Hulsing and Kudinov [S3] is relevant;
only its author abstract was available here, so no uninspected constants
from that paper are inserted. Its abstract reports a Winternitz-factor
correction, which must not be lost or charged twice in later composition.

## 6. A concrete partial oracle calculation: query budgets matter

Consider ONLY the ideal search problem with one uniformly hidden marked
element among N=2^b candidates. Its random-guess success is p=2^-b.
Boyer et al. [S4, Section 2] give the success of j Grover iterations as

    sin^2((2j+1) theta),   sin^2(theta)=p.

At j=1, the triple-angle identity gives the exact value

    p_1 = p (3-4p)^2.                                      (9)

For b>=2, this is greater than p. This ideal calculation is enough to show
why a label of b bits alone cannot give a query-independent 2^-b success
bound. It is an achievable success in the ideal search experiment, not an
upper bound on SLH forgery, nor a claim that a searched hash preimage
automatically yields a signature. One phase-oracle iteration need not equal
one evaluation of a concrete hash function; reversible evaluation and
uncomputation must be charged in a real reduction.

For a full SLH bound, neither this one-target experiment nor an unspecified
collision term replaces the distinct PRF, ITSR, DSPR, TCR and WOTS games in
(7). Random-oracle bounds also do not by themselves prove equivalent bounds
for a fixed SHAKE or SHA-2 implementation. A theorem must state whether it
assumes concrete hash properties or an ideal oracle, and preserve that scope.

## 7. What the current hybrid proof can conclude

With the same complete freshness and key-binding premises as v1.38,

    Adv_Hybrid(A) <= Adv_SLH(B).                             (10)

If both component reductions are justified, the minimum is taken over
Adv_Trad(B_T) and Adv_SLH(B_S), with their OWN simulators and resource counts.
Message binding does not make their success events independent. Crediting
no traditional post-quantum hardness leaves (10) unchanged.

The earlier conditional quorum conversion remains

    p_conflict <= kappa_E + L_E (delta_B + 64 epsilon_SLH).  (11)

Consequently, epsilon_SLH<=2^-128 alone would not certify a 2^-128 quorum
failure bound via (11). At L_E=1 and zero other errors the required
primitive bound is <=2^-134. Actual L_E and other errors must be carried.

The v1.41 all-pass lemma remains correct when its per-history premise is
proved. It has not been instantiated by SLH's existing tree structure.
The useful progress here is (2), (4), the arithmetic rejection of (5)'s
claimed conclusion, and the expanded dependency ledger (7). None implies
that SLH-DSA is broken. None certifies QPT-128 for the proposed system.

## 8. Validation scope and sources

The tests check event-preserving refactoring, conditioning on success,
known-value guessing, counterexamples to the proposed budget, disjoint
case accounting, distinct proof terms, the target-count identity and the
exact ideal-search polynomial. They use no real signing keys or forgery
code. No empirical pass frequency is treated as a bound over all QPT
adversaries. An absent hash-property bound is reported as absent, never zero.

[S1] NIST, FIPS 205, Algorithms 13 and 20, Table 2, Sections 9.2 and 11.
https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf

[S2] Barbosa, Dupressoir, Hulsing, Meijers and Strub. A Tight Security Proof
for SPHINCS+, Formally Verified. ASIACRYPT 2024 proceedings (2025),
Theorems 1–4. Full paper inspected; the modular games remain explicit.
https://pure.tue.nl/ws/portalfiles/portal/350450713/978-981-96-0894-2_2.pdf

[S3] Hulsing and Kudinov. Recovering the Tight Security Proof of SPHINCS+.
ASIACRYPT 2022. Author abstract inspected; the full text was not available.
https://eprint.iacr.org/2022/346
https://research.tue.nl/en/publications/recovering-thetight-security-proof-ofsphincs/

[S4] Boyer, Brassard, Hoyer and Tapp. Tight Bounds on Quantum Searching,
arXiv:quant-ph/9605034, Section 2, equation (2).
https://arxiv.org/pdf/quant-ph/9605034

Path note. This file is domains/05-extraction-and-signature-reductions/src/slh_tree_conditioning_audit.py.
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
from fractions import Fraction as F
from itertools import product
import argparse
import unittest


@dataclass(frozen=True)
class Geometry:
    n_bytes: int
    h: int
    d: int
    category: int

    @property
    def h_prime(self):
        if self.h % self.d:
            raise ValueError('equal-height layers required')
        return self.h // self.d

    def target_counts(self):
        ell = 1 << self.h_prime
        trees = sum(ell**i for i in range(self.d))
        return {'WOTS': ell*trees, 'HT_compress': ell*trees,
                'HT_tree': (ell-1)*trees}


PARAMETERS = {
    'SLH-DSA-SHAKE-128s': Geometry(16, 63, 7, 1),
    'SLH-DSA-SHAKE-128f': Geometry(16, 66, 22, 1),
    'SLH-DSA-SHAKE-256s': Geometry(32, 64, 8, 5),
}


COEFFICIENTS = {
    'PRF_SKG': 1,
    'PRF_MKG': 1,
    'ITSR': 1,
    'DSPR_F': 1,
    'TCR_F': 3,
    'FORS_tree': 1,
    'FORS_compress': 1,
    'WOTS': 1,
    'HT_compress': 1,
    'HT_tree': 1,
}


def paper_bound(terms):
    """Combine supplied paper-game bounds; this is not a QPT certificate."""
    if set(terms) != set(COEFFICIENTS):
        raise ValueError('every distinct theorem term must be supplied explicitly')
    if any(not isinstance(x, F) or not 0 <= x <= 1 for x in terms.values()):
        raise ValueError('exact rational advantage bounds required')
    return sum((COEFFICIENTS[k]*terms[k] for k in COEFFICIENTS), F(0))


def claimed_rhs(q_s, leaves, width, collision_bound=F(0)):
    """Arithmetic of the unsourced expression from the research trail, not a theorem."""
    if any(type(x) is not int for x in (q_s, leaves, width)):
        raise ValueError('integer counts required')
    if q_s < 0 or leaves < 1 or width < 1:
        raise ValueError('invalid counts')
    if not isinstance(collision_bound, F) or collision_bound < 0:
        raise ValueError('nonnegative exact error term required')
    return F(q_s*leaves, 1 << width) + collision_bound


def postselection_bound(epsilon, preceding_event_probability):
    if not 0 <= epsilon <= 1 or not 0 < preceding_event_probability <= 1:
        raise ValueError('valid probability bounds required')
    return min(F(1), epsilon / preceding_event_probability)


def ideal_search_one_iteration(bits):
    """Exact success polynomial in the abstract single-marked search game."""
    if type(bits) is not int or bits < 1:
        raise ValueError('positive integer width required')
    p = F(1, 1 << bits)
    return p*(3-4*p)**2


def first_explanation(bits):
    """Disjoint case selector for a synthetic union of bad events."""
    return next((i for i, value in enumerate(bits) if value), None)


class TreeConditioningTests(unittest.TestCase):
    def test_01_refactoring_preserves_acceptance(self):
        # Equality of two synthetic public 8-bit values; not SLH validation.
        for candidate in range(256):
            target = 0b10110101
            whole = candidate == target
            checks = [((candidate >> i) & 1) == ((target >> i) & 1)
                      for i in range(8)]
            self.assertEqual(whole, all(checks))
            self.assertEqual(whole, all(checks*16))

    def test_02_repetition_does_not_amplify_and_conditioning_can_equal_one(self):
        for exponent in (1, 32, 64, 92, 128):
            p = F(1, 1 << exponent)
            # Distribution: all-pass with mass p, all-fail otherwise.
            marginal = p
            intersection = p
            conditional_after_success = intersection/marginal
            self.assertEqual(conditional_after_success, 1)
            self.assertGreater(intersection, p**128)
            self.assertEqual(postselection_bound(p, p), 1)
            self.assertEqual(postselection_bound(p, F(1)), p)

    def test_03_public_deterministic_value_has_no_guessing_entropy(self):
        # The transcript includes the target. This tests entropy, not preimages.
        for target in range(256):
            conditional_law = {target: F(1)}
            self.assertEqual(max(conditional_law.values()), 1)

    def test_04_proposed_formula_cannot_certify_claimed_threshold(self):
        target = F(1, 1 << 128)
        self.assertEqual(claimed_rhs(1, 1, 128), target)
        self.assertEqual(claimed_rhs(1, 2, 128), 2*target)
        self.assertGreater(claimed_rhs(1, 2, 128), target)
        self.assertEqual(claimed_rhs(1 << 20, 1 << 9, 128), F(1, 1 << 99))
        for s in (32, 64, 92, 127, 128, 129):
            for loss_bits in (0, 1, 9, 29):
                rhs = claimed_rhs(1, 1 << loss_bits, s+loss_bits)
                self.assertEqual(rhs, F(1, 1 << s))
                self.assertGreater(rhs+F(1, 1 << (s+10)), F(1, 1 << s))

    def test_05_exhaustive_cases_are_a_sum(self):
        # Every three-event truth assignment; no cryptographic implementation.
        for outcomes in product((False, True), repeat=3):
            selected = first_explanation(outcomes)
            disjoint = [selected == i for i in range(3)]
            self.assertEqual(sum(disjoint), int(any(outcomes)))
        self.assertTrue(any((True, False, False)))
        self.assertFalse(all((True, False, False)))

    def test_06_nested_theorem_substitution_matches_expanded_ledger(self):
        terms = {k: F(i+1, 1 << 20) for i, k in enumerate(COEFFICIENTS)}
        openpre = terms['DSPR_F']+3*terms['TCR_F']
        fors = terms['ITSR']+openpre+terms['FORS_tree']+terms['FORS_compress']
        ht = terms['WOTS']+terms['HT_compress']+terms['HT_tree']
        nested = terms['PRF_SKG']+terms['PRF_MKG']+fors+ht
        self.assertEqual(paper_bound(terms), nested)
        # Shared hash-role name does not merge distinct game advantages.
        for name in ('FORS_tree', 'HT_tree', 'TCR_F'):
            changed = dict(terms)
            changed[name] += F(1, 1 << 20)
            self.assertEqual(paper_bound(changed)-nested,
                             F(COEFFICIENTS[name], 1 << 20))

    def test_07_missing_bounds_are_never_zero(self):
        with self.assertRaises(ValueError):
            paper_bound({})
        terms = {k: F(0) for k in COEFFICIENTS}
        for k in COEFFICIENTS:
            incomplete = {name: value for name, value in terms.items() if name != k}
            with self.assertRaises(ValueError):
                paper_bound(incomplete)

    def test_08_hypertree_target_identity(self):
        for hp in (1, 2, 3, 8, 9):
            for layers in range(1, 9):
                g = Geometry(16, hp*layers, layers, 1)
                counts = g.target_counts()
                self.assertEqual(counts['WOTS'], counts['HT_compress'])
                self.assertEqual(counts['HT_tree'], (1 << g.h)-1)
        for name, g in PARAMETERS.items():
            self.assertEqual(g.h_prime*g.d, g.h)
            self.assertNotEqual(g.d, 128)

    def test_09_ideal_query_success_exceeds_query_free_guess(self):
        for bits in (2, 3, 32, 64, 92, 127, 128, 129, 256):
            self.assertGreater(ideal_search_one_iteration(bits), F(1, 1 << bits))
            self.assertLessEqual(ideal_search_one_iteration(bits), 1)
        self.assertEqual(ideal_search_one_iteration(2), 1)
        # Two-dimensional amplitude recurrence from the ideal search paper,
        # with amplitudes scaled by sqrt(N), independently checks polynomial.
        for bits in (2, 8, 32, 128):
            n = 1 << bits
            amplitude_scaled = F(n-2, n)+F(2*(n-1), n)
            self.assertEqual(amplitude_scaled**2/n, ideal_search_one_iteration(bits))

    def test_10_quorum_conversion_keeps_the_identity_loss(self):
        target = F(1, 1 << 128)
        self.assertEqual(64*F(1, 1 << 134), target)
        self.assertGreater(64*F(1, 1 << 128), target)


def report():
    print('SLH TREE CONDITIONAL LIMIT: UNESTABLISHED')
    print('CONCRETE QPT-128 SIGNATURE BOUND: UNESTABLISHED')
    print('Refactoring/repetition gives no automatic probability amplification.')
    print('Claimed RHS at q_s=1, leaves=2, lambda=128: 2^-127 (before other terms).')
    print('Published dependency ledger: 10 distinct terms; TCR_F coefficient is 3.')
    print('Quantum/FIPS/hash matches and numerical property bounds remain required.')
    print('Parameter comparison: name | n bytes | layers | height per layer')
    for name, g in PARAMETERS.items():
        print(f'{name} | {g.n_bytes} | {g.d} | {g.h_prime}')
    print('No parameter-set label or finite test result is a security certificate.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SLH tree-conditioning proof audit')
    parser.add_argument('--proof', action='store_true')
    args = parser.parse_args()
    if args.proof:
        print(__doc__)
    else:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TreeConditioningTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
        report()
