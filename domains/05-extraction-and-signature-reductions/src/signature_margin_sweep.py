#!/usr/bin/env python3
r"""
# Incremental signature-security margins around 128 — v1.39

2026-09-10. Scope: the SLH-DSA signature-security reduction from v1.38.

Result: the incremental sweep establishes exact, conditional requirements
on the primitive advantage. It does not establish a new concrete QPT security
level. We test every integer target from 120 through 136 and retain wider
comparison points 32, 64, 92, 96, 112, 144 and 160. The quantum-query-work
comparison also uses every integer exponent from 120 through 136.

The proposed SLH-DSA-SHAKE-256s parameters and the optional mandatory-AND
P-384 hybrid are unchanged. No bit truncation, custom SLH parameter set,
new extractor or hardware modification is made.

## 1. Give each kind of bit count its own variable

QPT describes a class of adversaries, not a family of classes called QPT-127
and QPT-129. Concrete security additionally needs a resource profile and a
winning probability. We use three separate quantities:

* s: desired system failure exponent, meaning p <= 2^-s at specified resources.
* b: an assumed primitive advantage exponent, epsilon_SLH <= 2^-b at the
  reduction's resources. This is a proposed theorem input, not a measurement.
* w: an oracle-query-work exponent, Q=2^w, in a separate search experiment.

Neither b nor s is a signature length, key length, quantum-gate count or
NIST category. Oracle-query counts are also different from gate work,
circuit depth, memory and parallel hardware. FIPS 205 uses comparisons to
generic block-cipher resources rather than identifying a category with one
failure-probability exponent [S1].

In particular, the SLH-DSA labels 128, 192 and 256 specify parameter families.
They do not supply epsilon_SLH=2^-128, 2^-192 or 2^-256 for our chosen
adversary and resource profile. These sweeps do not substitute such values.

## 2. Exact inversion of the existing reduction

The conditional v1.38 reduction gives

    p <= Delta + kappa_E + L_E (delta_B + alpha epsilon_SLH).

Its premises still include valid oracle-respecting extraction, persistent
honest authorization, complete signing-query logs across all branches,
independent correctly distributed keys, and the specified corruption game.
The new SLH relation must have its own applicable extractor guarantee.

Define

    F = Delta + kappa_E + L_E delta_B,
    L = L_E,
    U = min(1, F + L alpha epsilon_SLH).

F is the non-signature contribution to this particular upper bound. Calling
it an error floor describes the proof expression, not a lower bound on the
real adversary's success probability. A pessimistic F can be improved by a
better proof. Delta is a separately justified outer-experiment distance, if
one is needed; the exact modeled setup uses Delta=0.

For target s>=1, put R=2^-s-F. The exact sufficient signature condition is

    epsilon_SLH <= R/(L alpha),        when R>0.               (1)

If R=0, this expression needs a zero signature-advantage upper bound. No
finite exponent b for the positive envelope 2^-b can suffice. If R<0, even
setting that term to zero cannot make this stated bound meet the target.
Neither case is an attack or a proof that the actual scheme is insecure.

For an assumed envelope epsilon_SLH<=2^-b and R>0, the minimum nonnegative
integer exponent that makes this bound sufficient is

    b_min = max(0, ceil(log2(L alpha/R))).                     (2)

Proof: solve F+L alpha 2^-b <= 2^-s for 2^-b, take a monotone logarithm,
and choose the least integer. The implementation uses exact rational
comparisons instead of floating logarithms, and checks that b_min-1 fails
whenever b_min>0. This proves sufficiency and minimality for the given bound,
not necessity for the real cryptographic system.

For adaptive corruption with 64 seats, 43-seat quorums, and at most 21 total
corruptions, alpha=64. If F=0 and L=2^ell, then exactly

    b_min = s + ell + 6.                                      (3)

Every extra target probability bit costs one primitive probability bit;
each doubling of the extraction probability loss does the same. The six
bits come from the identity-selection factor 64. They do not refer to
quantum execution time. A known, fixed set of 21 corrupt seats gives alpha=43.
Its probability penalty is log2(43), about 5.426 bits, so its zero-floor
integer-b threshold is still s+ell+6. Its smaller constant can nevertheless
change a boundary with nonzero F.

## 3. Learn from the near-128 transitions

Baseline: L=1 and F=0, strictly a diagnostic limit with all other terms
temporarily zero. The system envelope from epsilon_SLH<=2^-b is

    U = 2^{-(b-6)} for b>=6.

Thus b=128 supports the conditional exponent s=122; b=132 supports s=126;
b=134 supports s=128; and b=136 supports s=130. These are not validations
of SLH-DSA at any of those levels. They describe what a supplied primitive
theorem would imply through the reduction.

Nonzero-error experiment: hold L=1 and F=2^-130. One way to obtain this
hypothetical F is kappa_E=delta_B=2^-131 and Delta=0. At the target s=128:

    b=134, adaptive: U=(5/4) 2^-128, so the bound misses.
    b=135, adaptive: U=(3/4) 2^-128, so the bound suffices.
    b=134, known static: U=(59/64) 2^-128, so it already suffices.

The experiment exhibits a real arithmetic transition instead of assuming
that changing the label from 127 to 128 upgrades security. Increasing b
without changing F eventually stops helping: every finite positive signature
envelope leaves U>2^-130. It cannot certify s=130, although floating-point
rounding can falsely report equality when b is very large.

A practical proof-budget allocation gives each of four contributions at
most one quarter of the desired failure bound:

    Delta <= 2^{-(s+2)},
    kappa_E <= 2^{-(s+2)},
    delta_B <= 2^{-(s+ell+2)},
    epsilon_SLH <= 2^{-(s+ell+8)}.                             (4)

For alpha=64 and L=2^ell, their composed sum is at most 2^-s.
For target s=128, the last requirement is b>=136+ell: b=136 with L=1,
b=142 with L=64, and b=152 with L=65536. If Delta=0, its quarter is spare
budget and can instead be reallocated using (1). Equation (4) is a possible
allocation to prove; it is not a statement that the four terms have those
values. It also does not prove that a scheme needs that allocation.

## 4. Independently test quantum-query work

To understand quantum scaling without claiming a proof about SLH, use a
different, precisely specified model: a uniformly chosen single marked
element in an otherwise structureless oracle over N=2^n_search positions.
The initial information is independent of the marked location; the oracle
is the only way to learn it. There is no signing oracle or SLH public key.

Zalka proves the relevant optimality of Grover search and gives its success
probability before the first maximum [S2]. This implies the convenient bound

    epsilon_search(Q,n_search)
         <= min(1, (2Q+1)^2 / 2^n_search).                     (5)

For completeness, with theta=arcsin(1/sqrt(N)), Grover's expression is
sin^2((2Q+1)theta). For integer k, |sin(k theta)|<=k|sin(theta)|, by induction
using the sine addition formula. If (2Q+1)^2/N<1, the angle is before the
first maximum, since arcsin(x)<=(pi/2)x; Zalka's optimality applies there.
Otherwise the bound by one is sufficient. The probability is averaged over
the uniformly random marked location. Multiple targets and SLH-specific
public information are not silently inserted into this theorem.

If some separate reduction justified using this search term with the same
probability coefficients, the required domain width would be

    n_search >= ceil(log2(L alpha (2Q_R+1)^2 / R)),            (6)
    Q_R = 2^rho * 2^w + Q_0,

where rho and Q_0 explicitly describe query overhead. This hypothetical
composition is only a diagnostic. No reduction from all SLH forgeries to
this single-marked search game has been established here, so (5) is not
substituted for epsilon_SLH in a claimed security theorem.

At F=0, L=1, alpha=64, rho=0, Q_0=0, and w in 120..136, the exact minimum
integer width is 2w+s+9. For example, at Q=2^128 queries:

    target p<=1/2:       n_search>=266 in this envelope;
    target p<=2^-128:    n_search>=393 in this envelope.

Those are search-domain widths, not recommended SLH hash or key sizes.
They show why a 128-bit success exponent and 2^128 quantum queries cannot be
interchanged. A successful model check at these widths establishes nothing
about an unmodified SLH-DSA-SHAKE-256s key.

Within a quadratic query envelope, multiplying a probability term by 64
shrinks the admissible query scale by sqrt(64)=8, approximately three query
exponent bits at large Q, not six. Exact arithmetic acts on 2Q+1, so integer
rounding and the +1 remain in the implementation. Doubling query overhead
requires about two more search-domain bits; doubling a probability-loss
coefficient requires one. A gate-work claim must also charge oracle circuit
cost, non-oracle gates and extraction overhead.

## 5. Where the earlier square-root recurrence is valid

Write the continuous envelope limit as

    A_s = sqrt(2^n_search (2^-s-F)/(L alpha)),
    2Q+1 <= A_s.

If F=0 and the other coefficients are fixed, then exactly

    A_{s+1} = (sqrt(2)/2) A_s.

This is a valid use of the proposed recurrence: it describes tightening a
search-model probability budget by one bit. It does not measure coherence,
physical MAXDEPTH or total quantum gate work. The integer query limit is
floor((A_s-1)/2), computed with integer square roots in this implementation.

If F>0, then while both residual budgets are positive,

    A_{s+1}/A_s = sqrt((2^{-(s+1)}-F)/(2^-s-F)).               (7)

The ratio is smaller than sqrt(2)/2. With F=2^-130, going from s=128 to 129
gives sqrt(1/3); the next step has no positive residual budget. A constant
shrink factor therefore fails precisely where the proof's other error terms
dominate. Measuring actual depth would additionally require an oracle-depth
cost and a specified parallelism/memory model.

## 6. Validation and interpretation

The program evaluates 2,088 exact scenarios: 864 probability-budget cases
and 1,224 hypothetical query-work cases. Thirteen test groups check boundary
minimality, monotonicity, non-power-of-two losses, budget allocation, floor
equality, very small rational tails, integer search thresholds, recurrence
ratios and the distinction between probability loss and query overhead.
The tests include probability targets 1..256 for the closed-form identity.

Every scenario retains the actual-scheme status UNESTABLISHED. No nearby
point is used to infer an unproved claim at 128. The calculations execute
inequalities on large integers; they do not run 2^128 operations, attempt a
signature forgery, estimate rare-event probabilities by sampling, or measure
hardware. Passing a finite Monte Carlo experiment would not establish such
small security advantages either.

What is now established: the exact conditional threshold and the reason it
changes at each adjacent target. What is still needed for concrete QPT-128:
a matching SLH-DSA quantum advantage function at specified resources and
applicable values for the extractor/binding/setup terms. The corrected
SPHINCS+ proof remains relevant [S3]; its terms cannot be filled by assuming
that a nearby label or a toy search bound is the deployed primitive bound.

For the signature work, the useful next mathematical target is the function
epsilon_SLH(t,q_H,q_S,parameters,model), including all derived hash-property
terms, then applying (1) at the transformed reduction resources. This revision
does not claim to have supplied that function. Changing the target from 128
to 127 or 129 changes its required value, not the obligation to prove it.

## Sources and provenance

[S1] NIST, FIPS 205, Section 11 and Table 2. Used for the distinction between
SLH parameter labels, security categories and concrete computational models.
https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf

[S2] Christof Zalka, Grover's quantum searching algorithm is optimal,
arXiv:quant-ph/9711070v2 (1999), Eq. (6) and the optimality argument in
Section 3. Restricted here to a uniformly random single marked element.
https://arxiv.org/pdf/quant-ph/9711070

[S3] Andreas Hulsing and Mikhail Kudinov, Recovering the tight security proof
of SPHINCS+, ePrint 2022/346. Author abstract describes the corrected proof,
its additional Winternitz-factor loss, and quantum hash-property analysis.
https://eprint.iacr.org/2022/346

The quorum reduction coefficients come from the v1.38 record,
src/slh_dsa_signature_reduction.py. Equations (1)-(4), the diagnostic
compositions (6)-(7), the code and the resulting tables are calculations
made for this record. No citation
is used to claim an already published proof of this entire quorum system.

Usage: --report prints this text and every compact results table; --json
prints all scenario records; --self-test runs the exact arithmetic checks.


Path note. This file is domains/05-extraction-and-signature-reductions/src/signature_margin_sweep.py.
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
from math import isqrt
import argparse
import json
import unittest


def integer(x, minimum=0):
    if type(x) is not int or x < minimum:
        raise ValueError('canonical integer outside permitted range')
    return x


def power2(e):
    if type(e) is not int:
        raise ValueError('integer exponent required')
    return F(1 << e) if e >= 0 else F(1, 1 << -e)


def exact(x):
    if type(x) is not F:
        raise ValueError('exact Fraction required')
    return x


def ceil_log2(x):
    exact(x)
    if x <= 0:
        raise ValueError('positive argument required')
    e = x.numerator.bit_length()-x.denominator.bit_length()
    while power2(e) < x:
        e += 1
    while power2(e-1) >= x:
        e -= 1
    return e


def parameters(alpha, loss, error_floor):
    if exact(alpha) < 1 or exact(loss) < 1 or exact(error_floor) < 0:
        raise ValueError('invalid reduction parameters')


@dataclass(frozen=True)
class Budget:
    status: str
    max_signature_advantage: F | None
    minimum_integer_exponent: int | None


def required_primitive_exponent(target, *, alpha=F(64), loss=F(1), error_floor=F(0)):
    """Solve the stated upper-bound budget; this is not a hardness certificate."""
    integer(target,1)
    parameters(alpha, loss, error_floor)
    remaining = power2(-target)-error_floor
    if remaining < 0:
        return Budget('STATED_ERROR_BOUND_EXCEEDS_TARGET', None, None)
    if remaining == 0:
        return Budget('ZERO_SIGNATURE_BOUND_REQUIRED', F(0), None)
    maximum = remaining/(loss*alpha)
    return Budget('CONDITIONAL_BUDGET', maximum, max(0, ceil_log2(1/maximum)))


def composed_probability(primitive_exponent, *, alpha=F(64), loss=F(1), error_floor=F(0)):
    integer(primitive_exponent)
    parameters(alpha, loss, error_floor)
    return min(F(1), error_floor+loss*alpha*power2(-primitive_exponent))


def probability_exponent(bound):
    """Largest integer s with bound <= 2^-s; None means zero model bound."""
    exact(bound)
    if not 0 <= bound <= 1:
        raise ValueError('probability required')
    return None if bound == 0 else -ceil_log2(bound)


def quantum_search_envelope(queries, search_width):
    """Uniform single-marked-element oracle model only; NOT SLH-DSA."""
    integer(queries)
    integer(search_width, 1)
    return min(F(1), F((2*queries+1)**2, 1 << search_width))


def required_search_width(work_exponent, *, target=1, alpha=F(64), loss=F(1),
                          error_floor=F(0), query_overhead=0, fixed_queries=0):
    """Hypothetical reduction to single-marked search; no such SLH lift claimed.

    Q_reduction = 2^query_overhead * 2^work_exponent + fixed_queries.
    work_exponent counts oracle queries, not quantum gates or circuit depth.
    """
    integer(work_exponent)
    integer(query_overhead)
    integer(fixed_queries)
    budget=required_primitive_exponent(target,alpha=alpha,loss=loss,error_floor=error_floor)
    if budget.status != 'CONDITIONAL_BUDGET':
        return None
    q=(1 << (work_exponent+query_overhead))+fixed_queries
    return max(1,ceil_log2(F((2*q+1)**2)/budget.max_signature_advantage))


def maximum_search_queries(search_width, *, target=1, alpha=F(64), loss=F(1), error_floor=F(0)):
    """Exact largest Q satisfying the envelope, or -1 if even Q=0 fails it."""
    integer(search_width,1)
    budget=required_primitive_exponent(target,alpha=alpha,loss=loss,error_floor=error_floor)
    if budget.status != 'CONDITIONAL_BUDGET':
        return -1
    squared_limit=budget.max_signature_advantage*power2(search_width)
    root=isqrt(squared_limit.numerator//squared_limit.denominator)
    return (root-1)//2


def square_amplitude_limit(search_width, target, *, alpha=F(64), loss=F(1), error_floor=F(0)):
    """A^2 for A=2Q+1. Exact ratios recover the square-root shrink law."""
    integer(search_width,1)
    budget=required_primitive_exponent(target,alpha=alpha,loss=loss,error_floor=error_floor)
    return None if budget.status!='CONDITIONAL_BUDGET' else budget.max_signature_advantage*power2(search_width)


TARGETS=tuple(sorted(set((32,64,92,96,112,144,160)+tuple(range(120,137)))))
EXTRACTION_LOSS_BITS=(0,1,2,4,8,16)
ACTUAL_DEPLOYED_ASSESSMENT='UNESTABLISHED: no applicable numerical SLH/extractor/binding resource profile supplied'


def sweep():
    records=[]
    # 24 targets x 6 extraction losses x 2 corruption games x 3 budget rules.
    for target in TARGETS:
        for ell in EXTRACTION_LOSS_BITS:
            loss=power2(ell)
            for game,alpha in (('adaptive',F(64)),('known_static_21',F(43))):
                floors=(('zero_error_baseline',F(0)),
                        ('signature_gets_one_quarter',3*power2(-target-2)),
                        ('fixed_error_floor_2^-130',power2(-130)))
                for scenario,floor in floors:
                    budget=required_primitive_exponent(target,alpha=alpha,loss=loss,error_floor=floor)
                    records.append(dict(target_probability_exponent=target,extraction_loss_exponent=ell,
                                        corruption_game=game,scenario=scenario,
                                        status=budget.status,minimum_primitive_exponent=budget.minimum_integer_exponent,
                                        actual_cryptographic_assessment=ACTUAL_DEPLOYED_ASSESSMENT))
    for w in range(120,137):
        for ell in EXTRACTION_LOSS_BITS:
            for game,alpha in (('adaptive',F(64)),('known_static_21',F(43))):
                for rho in (0,1,2):
                    for target in (1,128):
                        records.append(dict(scenario='HYPOTHETICAL_single_marked_search',
                                            query_work_exponent=w,query_overhead_exponent=rho,
                                            extraction_loss_exponent=ell,corruption_game=game,
                                            target_probability_exponent=target,
                                            minimum_search_width=required_search_width(w,target=target,alpha=alpha,
                                                                                       loss=power2(ell),query_overhead=rho),
                                            actual_cryptographic_assessment=ACTUAL_DEPLOYED_ASSESSMENT))
    return records


class SweepTests(unittest.TestCase):
    def test_01_exact_known_losses_across_target_grid(self):
        for s in range(1,257):
            for ell in (0,1,6,20):
                got=required_primitive_exponent(s,loss=power2(ell))
                self.assertEqual(got.minimum_integer_exponent,s+ell+6)

    def test_02_inverse_is_minimal_with_non_dyadic_and_error_terms(self):
        for s in range(120,137):
            for alpha in (F(43),F(64),F(64,22)):
                for loss in (F(1),F(3),F(64)):
                    floor=power2(-s)/3
                    b=required_primitive_exponent(s,alpha=alpha,loss=loss,error_floor=floor).minimum_integer_exponent
                    self.assertLessEqual(composed_probability(b,alpha=alpha,loss=loss,error_floor=floor),power2(-s))
                    self.assertGreater(composed_probability(b-1,alpha=alpha,loss=loss,error_floor=floor),power2(-s))

    def test_03_floor_equality_is_zero_only_not_impossibility(self):
        self.assertEqual(required_primitive_exponent(130,error_floor=power2(-130)).status,'ZERO_SIGNATURE_BOUND_REQUIRED')
        self.assertEqual(required_primitive_exponent(131,error_floor=power2(-130)).status,'STATED_ERROR_BOUND_EXCEEDS_TARGET')

    def test_04_nonzero_floor_prevents_false_floating_point_pass(self):
        for b in (136,160,256,1024):
            p=composed_probability(b,error_floor=power2(-130))
            self.assertGreater(p,power2(-130))
            self.assertEqual(probability_exponent(p),129)

    def test_05_fixed_floor_changes_adaptive_static_boundary(self):
        self.assertEqual(required_primitive_exponent(128,error_floor=power2(-130)).minimum_integer_exponent,135)
        self.assertEqual(required_primitive_exponent(128,alpha=F(43),error_floor=power2(-130)).minimum_integer_exponent,134)

    def test_06_four_term_allocation(self):
        for s in range(120,137):
            for ell in EXTRACTION_LOSS_BITS:
                loss=power2(ell)
                setup=power2(-s-2); kappa=power2(-s-2)
                delta=power2(-s-ell-2)
                b=s+ell+8
                self.assertEqual(setup+kappa+loss*(delta+64*power2(-b)),power2(-s))

    def test_07_monotonicity(self):
        for b in range(120,161):
            self.assertLess(composed_probability(b+1),composed_probability(b))
            self.assertGreater(composed_probability(b,loss=F(2)),composed_probability(b))
            self.assertGreater(composed_probability(b,error_floor=power2(-130)),composed_probability(b))

    def test_08_search_width_threshold_is_exact(self):
        for w in range(120,137):
            for target in (1,128):
                n=required_search_width(w,target=target)
                q=1 << w
                self.assertLessEqual(64*quantum_search_envelope(q,n),power2(-target))
                self.assertGreater(64*quantum_search_envelope(q,n-1),power2(-target))
                self.assertEqual(n,2*w+target+9)

    def test_09_integer_query_bound(self):
        for n in range(8,40):
            for s in (1,4,8):
                q=maximum_search_queries(n,target=s)
                if q>=0:
                    self.assertLessEqual(64*quantum_search_envelope(q,n),power2(-s))
                self.assertGreater(64*quantum_search_envelope(q+1,n),power2(-s))

    def test_10_shrink_factor_applies_to_shifted_amplitude(self):
        for s in range(120,137):
            a2=square_amplitude_limit(256,s)
            next_a2=square_amplitude_limit(256,s+1)
            self.assertEqual(next_a2/a2,F(1,2))
        a=square_amplitude_limit(256,128,error_floor=power2(-130))
        b=square_amplitude_limit(256,129,error_floor=power2(-130))
        self.assertEqual(b/a,F(1,3))

    def test_11_query_overhead_and_probability_loss_have_distinct_roles(self):
        for w in range(120,137):
            base=required_search_width(w)
            self.assertEqual(required_search_width(w,loss=F(2)),base+1)
            self.assertEqual(required_search_width(w,query_overhead=1),base+2)

    def test_12_limits_and_units(self):
        self.assertEqual(quantum_search_envelope(0,256),power2(-256))
        self.assertEqual(quantum_search_envelope(1 << 256,256),1)
        self.assertEqual(probability_exponent(F(1)),0)
        self.assertIsNone(probability_exponent(F(0)))
        for bad in (True,0,-1,1.5):
            with self.assertRaises(ValueError):required_primitive_exponent(bad)
        with self.assertRaises(ValueError):required_primitive_exponent(128,loss=1.0)

    def test_13_nearby_points_do_not_claim_a_cryptographic_certificate(self):
        records=sweep()
        self.assertTrue(records)
        self.assertTrue(all(r['actual_cryptographic_assessment'].startswith('UNESTABLISHED') for r in records))
        self.assertEqual(sum(r['scenario']=='HYPOTHETICAL_single_marked_search' for r in records),1224)
        self.assertEqual(len(records),len(TARGETS)*6*2*3+1224)


def tables():
    lines=['## Computed results (conditional arithmetic only)','',
           'Target s means system failure <= 2^-s at a fixed adversary resource profile.',
           'b means an ASSUMED primitive bound epsilon_SLH <= 2^-b at the reduction resources.','',
           '| s | Minimum b: L=1, F=0 | Minimum b: L=64, F=0 | Minimum b: L=1, signature gets 1/4 |',
           '|---:|---:|---:|---:|']
    for s in TARGETS:
        vals=(required_primitive_exponent(s).minimum_integer_exponent,
              required_primitive_exponent(s,loss=F(64)).minimum_integer_exponent,
              required_primitive_exponent(s,error_floor=3*power2(-s-2)).minimum_integer_exponent)
        lines.append(f'| {s} | {vals[0]} | {vals[1]} | {vals[2]} |')
    lines+=['','## Fixed primitive assumptions near the 128 target','',
            'L=1; hypothetical combined non-signature upper bound F=2^-130. Ratios are relative to 2^-128.','',
            '| Assumed b | Adaptive bound / 2^-128 | Meets 128 budget? | Static bound / 2^-128 | Meets 128 budget? |',
            '|---:|---:|:---|---:|:---|']
    for b in range(130,139):
        pa=composed_probability(b,error_floor=power2(-130))
        ps=composed_probability(b,alpha=F(43),error_floor=power2(-130))
        lines.append(f'| {b} | {pa/power2(-128)} | {pa<=power2(-128)} | {ps/power2(-128)} | {ps<=power2(-128)} |')
    lines+=['','## Separate hypothetical single-marked search model','',
            'Q=2^w queries; F=0; L=1; alpha=64; zero extra query overhead. No reduction from SLH to this model is claimed.',
            'n_search is a search-domain width, NOT an SLH-DSA parameter proposal.','',
            '| Query exponent w | Minimum n_search for p<=1/2 | Minimum n_search for p<=2^-128 |',
            '|---:|---:|---:|']
    for w in range(120,137):
        lines.append(f'| {w} | {required_search_width(w)} | {required_search_width(w,target=128)} |')
    records=sweep()
    lines+=['',f'Total exact scenario evaluations: {len(records)}.',
            f'Actual scheme assessment for every row: {ACTUAL_DEPLOYED_ASSESSMENT}.','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description='Exact signature reduction margin sweeps; does not certify cryptographic hardness.')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--report',action='store_true',help='Print the derivations and computed tables.')
    mode.add_argument('--json',action='store_true',help='Print all exact scenario evaluations.')
    mode.add_argument('--self-test',action='store_true',help='Validate exact inequalities and boundaries.')
    args=parser.parse_args()
    if args.report:
        print(__doc__)
        print(tables())
        return 0
    if args.json:
        print(json.dumps(sweep(),indent=2))
        return 0
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(SweepTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
