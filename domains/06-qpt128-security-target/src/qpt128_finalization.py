#!/usr/bin/env python3
r"""
# QPT-128 finalization — v1.43

2026-09-11. Scope: the complete QPT-128 target, the composed ledger, and which
concrete CE-QS instantiations meet it. Companion document:
domains/06-qpt128-security-target/docs/qpt128-finalization.md. This file is the
exact-arithmetic evidence. All paths in this file are relative to the repository
root.

Run:  python3 qpt128_finalization.py --self-test
      python3 qpt128_finalization.py --report     (JSON verdicts)
      python3 qpt128_finalization.py --explain    (this text)

One of --self-test, --report or --explain is required; a bare invocation prints
the usage message and exits 2, by design.

Standard library only. Probabilities are exact Fractions. Logarithms are
printed with 60-digit Decimal arithmetic, for display only. Every PASS/FAIL
verdict is decided by an exact rational comparison.

## 1. The target, fixed once

Adversaries are quantum circuits, and G(A) is the number of gates. When an
oracle stands for a concrete hash, each query costs g_H gates, the T-count of
that hash's circuit. Three readings of "QPT-128" occur in the project record,
and they are different statements:

  (D1) work-factor target (operators ledger, lines 28-33: 'force a quantum
       adversary to expend a minimum of 2^128 quantum gates'):
           G(A) < 2^128  ==>  Pr[Win(A)] < 1/3.
  (D2) ratio target, the rigorous strengthening used here:
           Pr[Win(A)] <= G(A) * 2^-kappa  for every A, with kappa = 130.
  (D3) fixed-budget probability target (research trail §1, §17-18, §34 and the
       closing 'Final QPT-128 theorem'):
           Pr[Win(A)] < 2^-128 for every QPT adversary.

Path note: 'operators ledger' is the file
domains/04-operator-ledger/docs/operator-ledger.md and 'research trail' is the
file docs/01-research-journey/pqt.md. Where a pointer carries a line number, the
number is the one recorded in the source files; it is not re-verified against
the repository copies.

Lemma L1 (D3 is unattainable). Suppose a uniformly random 256-bit secret
determines a winning output. Then 2^63 Grover iterations already succeed with
probability > 2^-128. Exact rational proof: theta >= sin(theta) = 2^-128 and
sin(y) >= y - y^3/6. So "Adv < 2^-128 for every QPT adversary" cannot hold for
SLH-DSA-SHAKE-256s, ML-DSA-87, AES-256 or SHAKE256-256 credentials. The
research-trail closing theorem must be restated.

Lemma L2 (queries are the wrong unit). With one gate per query:
  - 3*2^125 < 2^127 iterations reach success >= 1/3 against one 256-bit key;
  - 3*2^122 iterations do so against 64 keys.
So D1 in query units fails for every 256-bit-secret component. D1 is
attainable only with gate accounting, where each query costs its circuit:
T-count 499,200 for a SHA3-256 oracle (Amy et al. SAC 2016 Table 2), 75,580
for AES-256 (JNRV EUROCRYPT 2020 rev. Table 9). This is exactly the NIST
category-5 reading.

Lemma L3 (composition). Suppose Win ⊆ ∪ Bad_i and Pr[Bad_i] <= rho_i(G).
Then Pr[Win] <= sum_i rho_i(G). If sum_i max_G rho_i(G)/G <= 2^-130, then D2
holds with kappa = 130, and D2 implies D1 (G < 2^128 gives Pr < 1/4).
Probabilities add; exponents do not. The project's 8*2^-131 arithmetic carries
over unchanged, now applied to the per-gate coefficient.

Lemma L4 (endpoint evaluation). Let rho(q) be a polynomial in q with
non-negative coefficients, and set q = G/g. Then rho(G/g)/G is convex in
G > 0, so its maximum on [1, 2^128] is at an endpoint. The checker evaluates
both endpoints exactly on UNCAPPED envelopes.

A capped envelope min(1, rho) is not convex: its ratio can peak where the cap
starts to bind (test 19 exhibits this). So caps apply only to the D1
probability. Square-root-form rows (adaptive reprogramming) are decreasing in
G and are evaluated at G = 1.

Lemma L5 (extraction overhead). Online extraction in the QROM (DFMS CRYPTO
2022) simulates the oracle with a compressed database and runs in
O(q^2)*poly time. A reduction that USES the extracted witness to break a
standard-model primitive F therefore runs in time t_B ~ G + a*q^2*g_sim. If
F's generic bound is c*(t/g_F)^e / 2^n, D2 needs roughly

    n >= (2e-1)*128 + 130 + log2(c) + e*log2(a*g_sim) - 2e*log2(g_H) - e*log2(g_F).

In gate units:
  - a search row (e=2) with n=512 passes;
  - a collision row (e=3) needs n=1024;
  - a 256-bit signature kept INSIDE an extractable proof fails in both units;
  - a signature sent in the clear (profile B0) needs no extraction, so its
    reduction is linear and it passes.
Mode S therefore uses 512-bit credentials and 1024-bit registry keys. Both are
a single SHAKE256 absorb block, so no extra permutation is needed.

## 2. Verified constants used (sources re-checked on 2026-09-11)

  search/preimage : 8*p*(q+1)^2/2^n
                    HRS16 (ePrint 2015/1256) Thm 1, with lambda = p/2^n.
  collision       : (2e(q+1)sqrt(10(q+1)/M)+sqrt(2/M))^2
                    CFHL EUROCRYPT 2021 Thm 5.29. The checker uses the rational
                    envelope 80*e^2*(q+1)^3/M + 4/M.
  C&O extraction  : (22*ell+60)*q^3*2^-n + 20*q^2*p_triv
                    DFMS CRYPTO 2022 Thm 4.2.
  joint two-proof : add the readout term 2(v0+v1)*2^-n, with a single database
                    (project v1.35 lift of DFMS Cor. 2.7).
  FS simulation   : (3q_s/2)*sqrt((q_H+q_s+1)*gamma(Commit)) + q_s*Delta_HVZK
                    GHHM ASIACRYPT 2021 Thm 3.
  extractor time  : O(q^2)*poly, stated with DFMS Thm 4.2; premise of L5.
  gate costs      : SHA3-256 oracle T-count 499,200 (Amy et al. SAC 2016
                    Table 2); AES-256 oracle T-count 75,580 (JNRV rev. Table 9).
                    Floors used: g_H = g_F = 2^18 and g_AES-iteration = 2^17.
  NOT FOUND       : "12(q+154)^3/2^n" (stated in the research trail without a
                    reference). No source located.
                    At q=2^128, n=512 the exact CFHL leading term
                    40e^2(q+1)^3/2^n gives about 2^-119.8, not 2^-124.415;
                    the checker's rational envelope (80e^2) gives 2^-118.8.
  signatures      : category-5 signatures of at most 757 bytes exist:
                      UOV-V     260 B. Only QROM route: Kosuge-Xagawa ePrint
                                2022/1359 Thm 1, with a (2q+1)^2 loss on its
                                inversion problem.
                      SNOVA-V   232-576 B.
                      SQIsign-V 292 B, classical ROM proof.
                    B0 assumes EUF-CMA of the chosen scheme at category-5
                    generic strength. The scheme's own reduction to its hard
                    problem is a property of the signature, not of CE-QS
                    composition.

## 3. Verdicts computed below (see --report)

  Legacy D3 ledger (research-trail final theorem) ..... REFUTED by L1
  B0 public-signer QC, category-5 signature in clear .. PASS D2 (gate units)
  B1 Mode S, 512-bit credentials, 1024-bit keys:
       attack-cost accounting ......................... PASS D2 (both units)
       rigorous with extraction overhead, gate units .. PASS D2: safety,
                                                        non-frameability and
                                                        forensic completeness
       rigorous, query units .......................... FAIL
  B1 Mode S with 512-bit registry keys, rigorous ...... FAIL (collision row)
  Compat mode (ML-DSA-87 / SLH-DSA-256s inside an
  extractable proof), rigorous ........................ FAIL D2 and D1

These verdicts cover the SECURITY LEDGER only. Certificate size is decided in
domains/07-compact-certificate-b0/src/sidecar_free_certificate.py and its
document.

## 4. Non-claims

- The QROM model for SHAKE256 is a heuristic. A fixed hash is never
  indistinguishable from a random oracle (operators ledger, Lemma 8).
- Standard-model rows are named assumptions evaluated at their generic attack
  bounds. For single-block SHAKE256 inputs this is the ideal-permutation
  reading. No new cryptanalysis is performed.
- Nothing here measures a proof size, implements a zero-knowledge backend or
  runs a distributed prover.
- The collaborative prover's MPC realization is modelled as an ideal
  functionality. Its QPT secure-with-abort realization is a separate named
  premise (v1.4 Theorem 4.1).
"""

from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from fractions import Fraction as F
from math import comb, isqrt
import argparse
import json
import sys
import unittest

LOG2_BUDGET = 128
KAPPA = 130
E_UPPER = F(27182818285, 10**10)          # rational upper bound on e
G_H_LOG2 = 18                              # SHA3/Keccak oracle T-count floor
G_F_LOG2 = 18                              # credential function circuit floor
G_AES_ITER_LOG2 = 17                       # two AES-256 oracle calls, T only
G_SIM_LOG2 = 12                            # per-entry compressed-oracle work
Q_SIGN = 1 << 64                           # honest proofs/signatures per key
SEATS, QUORUM, FAULTS = 64, 43, 21
CREDENTIAL_BITS = 512
LINK_BITS = 512


def pow2(e):
    if type(e) is not int:
        raise ValueError('integer exponent required')
    return F(1 << e) if e >= 0 else F(1, 1 << -e)


def log2(x):
    x = F(x)
    if x <= 0:
        raise ValueError('positive value required')
    with localcontext() as ctx:
        ctx.prec = 60
        return float((Decimal(x.numerator).ln() - Decimal(x.denominator).ln())
                     / Decimal(2).ln())


def cap(x):
    return min(F(1), x)


def sqrt_upper(x):
    """Rigorous rational upper bound on sqrt(x) for Fraction x >= 0 (2^-100 grid)."""
    x = F(x)
    if x < 0:
        raise ValueError('non-negative value required')
    scaled = x * pow2(200)
    ceil_scaled = -((-scaled.numerator) // scaled.denominator)
    return F(isqrt(ceil_scaled) + 1, 1 << 100)


# ---------------------------------------------------------------- Lemma L1/L2
def grover_success_lower_bound(n_bits, iterations, log2_targets=0):
    """Exact lower bound on sin^2((2j+1)theta), sin^2(theta) = targets/2^n.

    Requires n_bits - log2_targets even (rational square root) and
    y = (2j+1)*sin(theta) <= 1, so (2j+1)*theta stays below pi/2.
    """
    exp2 = n_bits - log2_targets
    if exp2 <= 0 or exp2 % 2:
        raise ValueError('even positive density exponent required')
    if type(iterations) is not int or iterations < 0:
        raise ValueError('non-negative integer iterations required')
    s = F(1, 1 << (exp2 // 2))
    y = (2 * iterations + 1) * s
    if y > 1:
        raise ValueError('outside the monotone range used by the lemma')
    lb = y - y**3 / 6
    return lb * lb


# ---------------------------------------------------------------- envelopes
def hrs16_search(q, n_bits, targets=1, capped=True):
    v = 8 * targets * (F(q) + 1)**2 * pow2(-n_bits)
    return cap(v) if capped else v


def cfhl_collision(q, n_bits, capped=True):
    """Rational upper bound on CFHL Thm 5.29 via (a+b)^2 <= 2a^2 + 2b^2."""
    q = F(q)
    v = 80 * E_UPPER**2 * (q + 1)**3 * pow2(-n_bits) + 4 * pow2(-n_bits)
    return cap(v) if capped else v


def dfms_extraction(q, n_bits, ell, p_triv, capped=True):
    q = F(q)
    v = (22 * ell + 60) * q**3 * pow2(-n_bits) + 20 * q * q * p_triv
    return cap(v) if capped else v


def joint_extraction(q, n_bits, ell, p_triv, verifier_queries, capped=True):
    q = F(q)
    v = (2 * verifier_queries * pow2(-n_bits)
         + (22 * ell + 60) * q**3 * pow2(-n_bits) + 20 * q * q * p_triv)
    return cap(v) if capped else v


def zkboo4_parameters(r):
    """v1.36 four-subset ZKBoo commit-and-open: ell=4r, p_triv=(3/4)^r."""
    if type(r) is not int or r < 1:
        raise ValueError('positive repetition count required')
    return dict(ell=4 * r, p_triv=F(3, 4)**r, verifier_queries_two_proofs=2 * (1 + 3 * r),
                challenge_bits=2 * r)


def unused_legacy_12q154(q, n_bits):
    """The unsourced expression stated in the research trail, kept to test the discrepancy."""
    return cap(12 * (F(q) + 154)**3 * pow2(-n_bits))


def generic_category5_signature(t_gates, g_iter_log2, capped=False):
    """Category-5 envelope: AES-256-key-search success at t gates (HRS16 form)."""
    return hrs16_search(F(t_gates) / pow2(g_iter_log2), 256, capped=capped)


# ---------------------------------------------------------------- rows
@dataclass(frozen=True)
class Row:
    name: str
    rho: object            # callable: q (Fraction, queries) -> UNCAPPED bound
    shape: str             # 'convex' (polynomial, L4) or 'decreasing'
    status: str            # 'proven-QROM', 'named-assumption', 'model-premise'
    source: str


def ratio_bound(row, g_log2):
    """Exact upper bound on max_{1<=G<=2^128} min(1,rho(G/g))/G (Lemma L4)."""
    g = pow2(g_log2)
    low = row.rho(F(1) / g)
    if row.shape == 'decreasing':
        return low
    high = row.rho(pow2(LOG2_BUDGET) / g) / pow2(LOG2_BUDGET)
    return max(low, high)


def d1_probability(row, g_log2):
    """Capped Pr bound at the D1 budget edge G = 2^128 (rows are non-decreasing in G)."""
    return cap(row.rho(pow2(LOG2_BUDGET) / pow2(g_log2)))


@dataclass
class Scenario:
    name: str
    rows: list = field(default_factory=list)

    def evaluate(self, g_log2):
        ratios = {r.name: ratio_bound(r, g_log2) for r in self.rows}
        total_ratio = sum(ratios.values(), F(0))
        d1 = cap(sum((d1_probability(r, g_log2) for r in self.rows), F(0)))
        return dict(
            scenario=self.name,
            units=('gates, one query = 2^%d gates' % g_log2) if g_log2 else 'queries (one gate per query)',
            rows={k: (None if v == 0 else round(log2(v), 3)) for k, v in ratios.items()},
            total_ratio_log2=None if total_ratio == 0 else round(log2(total_ratio), 3),
            D2_kappa130=total_ratio <= pow2(-KAPPA),
            D2_margin_bits=None if total_ratio == 0 else round(-KAPPA - log2(total_ratio), 3),
            D1_prob_at_budget_log2=None if d1 == 0 else round(log2(d1), 3),
            D1_pass=d1 < F(1, 3),
            statuses={r.name: r.status for r in self.rows},
        )


# ---------------------------------------------------------------- scenarios
def b0_public_signer(g_log2):
    """Signatures in the clear; tight linear reduction; identity loss 64."""
    g_iter = G_AES_ITER_LOG2 if g_log2 else 0
    s = Scenario('B0 public signer set, category-5 signature in clear')
    s.rows.append(Row(
        'multi-user signature forgery (x64)',
        lambda q: 64 * generic_category5_signature(q * pow2(g_log2), g_iter),
        'convex', 'named-assumption',
        'EUF-CMA at category 5 via AES-256 key-search envelope; v1.37 identity loss 64'))
    s.rows.append(Row('canonical encoding / rollback', lambda q: F(0), 'convex',
                      'model-premise', 'A7, A9 of the protocol premises (research trail §18)'))
    return s


def mode_s_rows(r, g_log2, rigorous, key_bits):
    """Bad events for Mode S (safety, non-frameability, forensic completeness)."""
    p = zkboo4_parameters(r)
    gF = G_F_LOG2 if g_log2 else 0
    rows = [Row('E1 joint online extraction (DFMS Thm 4.2 + v1.35)',
                lambda q: joint_extraction(q, 512, p['ell'], p['p_triv'],
                                           p['verifier_queries_two_proofs'], capped=False),
                'convex', 'proven-QROM', 'DFMS CRYPTO 2022 Thm 4.2; v1.35 joint lift')]

    def reduction_time_in_F_units(q):
        t = q * pow2(g_log2)
        if rigorous:
            t += q * q * pow2(G_SIM_LOG2)
        return t / pow2(gF)

    rows.append(Row('E2 honest-proof simulation (GHHM Thm 3, q_S=2^64)',
                    lambda q: F(3, 2) * F(Q_SIGN) * sqrt_upper(q + Q_SIGN + 1) * pow2(-256),
                    'decreasing', 'proven-QROM',
                    'GHHM ASIACRYPT 2021 Thm 3: (3q_s/2)sqrt((q_H+q_s+1)gamma(Commit)), '
                    'gamma<=2^-512 (commitment min-entropy premise)'))
    rows.append(Row('E3 honest credential preimage (64 targets)',
                    lambda q: hrs16_search(reduction_time_in_F_units(q), min(CREDENTIAL_BITS, key_bits),
                                           targets=SEATS, capped=False),
                    'convex', 'named-assumption',
                    'F_K one-wayness at generic bound (HRS16 form); safety and non-frameability'))
    rows.append(Row('E4 registry-key collision (%d-bit keys)' % key_bits,
                    lambda q: cfhl_collision(reduction_time_in_F_units(q), key_bits, capped=False),
                    'convex', 'named-assumption',
                    'F_K collision resistance (CFHL form); a corrupt seat with two openings '
                    'escapes public blame (forensic completeness)'))
    rows.append(Row('E5 cross-seat link coincidence in one domain (2016 pairs)',
                    lambda q: hrs16_search(reduction_time_in_F_units(q), LINK_BITS,
                                           targets=comb(SEATS, 2), capped=False),
                    'convex', 'named-assumption',
                    'registration-first: registered credentials fixed before D; search over d '
                    '(non-frameability and completeness)'))
    rows.append(Row('E6 honest-proof HVZK', lambda q: F(0), 'convex', 'model-premise',
                    'q_s*Delta_HVZK = 0 for ZKBoo with uniform tapes (GHHM Thm 3 remark)'))
    rows.append(Row('E7 collaborative prover realization', lambda q: F(0), 'convex',
                    'model-premise', 'ideal F_Prove; QPT secure-with-abort MPC (v1.4 Thm 4.1)'))
    rows.append(Row('E8 registry authenticity, canonical encoding, durable approval state',
                    lambda q: F(0), 'convex', 'model-premise',
                    'A6, A7, A9 of the protocol premises (research trail §18)'))
    return rows


def mode_s(r, g_log2, rigorous=False, key_bits=1024):
    title = 'B1 Mode S, r=%d, %d-bit registry keys, %s' % (
        r, key_bits, 'rigorous extraction overhead' if rigorous else 'attack-cost accounting')
    s = Scenario(title)
    s.rows.extend(mode_s_rows(r, g_log2, rigorous, key_bits))
    return s


def compat_inside_proof(g_log2, r=640):
    """256-bit-level signature hidden inside an extractable proof (R29/SLH)."""
    p = zkboo4_parameters(r)
    g_iter = G_AES_ITER_LOG2 if g_log2 else 0
    s = Scenario('compat mode: category-5 signature inside extractable proof, rigorous')
    s.rows.append(Row('joint online extraction', lambda q: joint_extraction(
        q, 512, p['ell'], p['p_triv'], p['verifier_queries_two_proofs'], capped=False),
        'convex', 'proven-QROM', 'DFMS Thm 4.2'))
    s.rows.append(Row('signature forgery at reduction time (x64)',
                      lambda q: 64 * generic_category5_signature(
                          q * pow2(g_log2) + q * q * pow2(G_SIM_LOG2), g_iter),
                      'convex', 'named-assumption', 'v1.37 conversion with L5 overhead'))
    return s


def extraction_row(r):
    p = zkboo4_parameters(r)
    return Row('x', lambda q: joint_extraction(q, 512, p['ell'], p['p_triv'],
                                               p['verifier_queries_two_proofs'], capped=False),
               'convex', 'proven-QROM', '')


def minimum_repetitions(g_log2, share_log2=-133):
    """Least r with the extraction row ratio <= 2^share (exact boundary check)."""
    def ok(r):
        return ratio_bound(extraction_row(r), g_log2) <= pow2(share_log2)
    lo, hi = 1, 4096
    if not ok(hi):
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def legacy_d3_refutation():
    lb = grover_success_lower_bound(256, 1 << 63)
    return dict(
        claim='closing theorem of the research trail (docs/01-research-journey/pqt.md): '
              'Adv < 2^-128 for every QPT adversary (D3)',
        grover_iterations='2^63', success_lower_bound_log2=round(log2(lb), 9),
        exceeds_two_pow_minus_128=lb > pow2(-128),
        verdict='REFUTED as stated; restate as D1/D2 with gate accounting')


def report():
    out = dict(version='1.43', definitions=dict(
        D1='G<2^128 => Pr<1/3 (work-factor target)', D2='Pr <= G*2^-130 (rigorous; implies D1)',
        D3='Pr<2^-128 for all QPT (legacy; refuted by L1)'))
    out['L1'] = legacy_d3_refutation()
    out['L2'] = dict(
        single_256bit_key_iterations_for_1_3='3*2^125 (< 2^127)',
        lower_bound=float(grover_success_lower_bound(256, 3 << 125)),
        sixty_four_keys_iterations_for_1_3='3*2^122',
        lower_bound_64=float(grover_success_lower_bound(256, 3 << 122, log2_targets=6)))
    rmin_q = minimum_repetitions(0)
    rmin_g = minimum_repetitions(G_H_LOG2)
    out['minimum_repetitions_extraction_share_2^-133'] = dict(query_units=rmin_q, gate_units=rmin_g)
    r = max(rmin_q, rmin_g)
    scenarios = []
    for g in (0, G_H_LOG2):
        scenarios.append(b0_public_signer(g).evaluate(g))
        scenarios.append(mode_s(r, g, rigorous=False, key_bits=1024).evaluate(g))
        scenarios.append(mode_s(r, g, rigorous=True, key_bits=512).evaluate(g))
        scenarios.append(mode_s(r, g, rigorous=True, key_bits=1024).evaluate(g))
        scenarios.append(compat_inside_proof(g, r).evaluate(g))
    out['scenarios'] = scenarios
    q, n = pow2(128), 512
    out['unsourced_12q154_check'] = dict(
        legacy_value_log2=round(log2(unused_legacy_12q154(q, n)), 3),
        cfhl_rational_envelope_log2=round(log2(cfhl_collision(q, n)), 3),
        note='legacy constant not found in literature; exact CFHL Thm 5.29 leading term '
             '40e^2 gives ~-119.8; the rational envelope used here (80e^2) gives the value shown')
    out['non_claims'] = ['no proof size measured', 'QROM heuristic for SHAKE256',
                         'generic-attack assumptions for F and signatures',
                         'ideal collaborative prover']
    return out


# ---------------------------------------------------------------- tests
class FinalizationTests(unittest.TestCase):
    def test_01_L1_d3_refuted_256(self):
        self.assertGreater(grover_success_lower_bound(256, 1 << 63), pow2(-128))

    def test_02_L1_scales_to_512(self):
        self.assertGreater(grover_success_lower_bound(512, 1 << 127), pow2(-256))

    def test_03_L2_query_units_fail_for_256bit_secrets(self):
        self.assertGreaterEqual(grover_success_lower_bound(256, 3 << 125), F(1, 3))
        self.assertLess(3 << 125, 1 << 127)
        self.assertGreaterEqual(grover_success_lower_bound(256, 3 << 122, 6), F(1, 3))

    def test_04_L1_range_guard(self):
        with self.assertRaises(ValueError):
            grover_success_lower_bound(256, 1 << 128)
        with self.assertRaises(ValueError):
            grover_success_lower_bound(255, 1)

    def test_05_L3_d2_implies_d1(self):
        for G in (1, 1 << 64, (1 << 128) - 1):
            self.assertLess(F(G) * pow2(-KAPPA), F(1, 3))
        self.assertEqual(8 * pow2(-131), pow2(-128))
        self.assertGreater(8 * pow2(-128), pow2(-128))

    def test_06_L4_endpoint_bound_dominates_samples_uncapped(self):
        row = Row('t', lambda q: hrs16_search(q, 200, 64, capped=False)
                  + dfms_extraction(q, 300, 40, F(1, 1 << 90), capped=False), 'convex', 'x', '')
        for g in (0, 10):
            bound = ratio_bound(row, g)
            for e in range(0, 129, 3):
                G = pow2(e)
                self.assertLessEqual(cap(row.rho(G / pow2(g))) / G, bound)
                self.assertLessEqual(row.rho(G / pow2(g)) / G, bound)

    def test_07_envelopes_monotone_and_capped(self):
        for fn in (lambda q: hrs16_search(q, 256), lambda q: cfhl_collision(q, 256)):
            self.assertLessEqual(fn(F(10)), fn(F(11)))
            self.assertEqual(fn(pow2(200)), 1)

    def test_08_zkboo4_parameters(self):
        p = zkboo4_parameters(3)
        self.assertEqual((p['ell'], p['p_triv'], p['challenge_bits']), (12, F(27, 64), 6))
        with self.assertRaises(ValueError):
            zkboo4_parameters(0)

    def test_09_minimum_repetitions_exact_boundary(self):
        for g in (0, G_H_LOG2):
            r = minimum_repetitions(g)
            self.assertLessEqual(ratio_bound(extraction_row(r), g), pow2(-133))
            self.assertGreater(ratio_bound(extraction_row(r - 1), g), pow2(-133))

    def test_10_b0_gate_units_pass_query_units_fail(self):
        gate = b0_public_signer(G_H_LOG2).evaluate(G_H_LOG2)
        self.assertTrue(gate['D2_kappa130'])
        self.assertTrue(gate['D1_pass'])
        self.assertFalse(b0_public_signer(0).evaluate(0)['D2_kappa130'])

    def test_11_mode_s_attack_cost_passes_both_units(self):
        r = max(minimum_repetitions(0), minimum_repetitions(G_H_LOG2))
        for g in (0, G_H_LOG2):
            res = mode_s(r, g, rigorous=False, key_bits=1024).evaluate(g)
            self.assertTrue(res['D2_kappa130'])
            self.assertTrue(res['D1_pass'])

    def test_12_mode_s_rigorous_needs_1024_bit_keys_and_gate_units(self):
        r = max(minimum_repetitions(0), minimum_repetitions(G_H_LOG2))
        final = mode_s(r, G_H_LOG2, rigorous=True, key_bits=1024).evaluate(G_H_LOG2)
        short = mode_s(r, G_H_LOG2, rigorous=True, key_bits=512).evaluate(G_H_LOG2)
        self.assertTrue(final['D2_kappa130'])
        self.assertTrue(final['D1_pass'])
        self.assertFalse(short['D2_kappa130'])
        self.assertFalse(short['D1_pass'])
        self.assertFalse(mode_s(r, 0, rigorous=True, key_bits=1024).evaluate(0)['D2_kappa130'])

    def test_13_compat_inside_proof_fails(self):
        for g in (0, G_H_LOG2):
            res = compat_inside_proof(g).evaluate(g)
            self.assertFalse(res['D2_kappa130'])
            self.assertFalse(res['D1_pass'])

    def test_14_unsourced_constant_discrepancy(self):
        legacy = unused_legacy_12q154(pow2(128), 512)
        cfhl = cfhl_collision(pow2(128), 512)
        self.assertAlmostEqual(log2(legacy), -124.415, places=3)
        self.assertGreater(cfhl, legacy)

    def test_15_quorum_arithmetic_unchanged(self):
        self.assertEqual(2 * QUORUM - SEATS, FAULTS + 1)
        self.assertEqual(SEATS, 3 * FAULTS + 1)
        self.assertEqual(comb(SEATS, 2), 2016)

    def test_16_model_premise_rows_are_zero_and_labelled(self):
        rows = mode_s_rows(8, 0, False, 1024) + b0_public_signer(0).rows
        for row in rows:
            if row.status == 'model-premise':
                self.assertEqual(row.rho(F(12345)), 0)

    def test_17_sqrt_upper_is_rigorous_and_tight(self):
        for x in (F(0), F(1, 3), F(2), pow2(64) + 1, pow2(-18) + pow2(64) + 1, pow2(128) / 7):
            s = sqrt_upper(x)
            self.assertGreaterEqual(s * s, x)
            self.assertLessEqual((s - pow2(-99))**2, x + pow2(-90))
        with self.assertRaises(ValueError):
            sqrt_upper(F(-1))

    def test_18_simulation_row_dominates_ghhm_theorem3(self):
        sim = [r for r in mode_s_rows(8, G_H_LOG2, False, 1024) if r.name.startswith('E2')][0]
        q_s = F(Q_SIGN)
        for q in (pow2(-18), F(1), pow2(40), pow2(110)):
            scaled = sim.rho(q) / (F(3, 2) * q_s * pow2(-256))
            self.assertGreaterEqual(scaled * scaled, q + q_s + 1)
        self.assertLessEqual(ratio_bound(sim, G_H_LOG2), pow2(-131))

    def test_19_capping_before_maximisation_is_invalid(self):
        capped = Row('c', lambda q: hrs16_search(q, 200, 64), 'convex', 'x', '')
        endpoint_only = max(capped.rho(F(1)), capped.rho(pow2(128)) / pow2(128))
        interior = capped.rho(pow2(96)) / pow2(96)
        self.assertGreater(interior, endpoint_only)
        uncapped = Row('u', lambda q: hrs16_search(q, 200, 64, capped=False), 'convex', 'x', '')
        self.assertLessEqual(interior, ratio_bound(uncapped, 0))


def main():
    parser = argparse.ArgumentParser(description='QPT-128 finalization ledger (exact arithmetic).')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--self-test', action='store_true')
    mode.add_argument('--report', action='store_true')
    mode.add_argument('--explain', action='store_true')
    args = parser.parse_args()
    if args.explain:
        print(__doc__)
        return 0
    if args.report:
        print(json.dumps(report(), indent=2))
        return 0
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FinalizationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
