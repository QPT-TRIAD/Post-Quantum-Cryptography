#!/usr/bin/env python3
r"""Mode B rigorous QPT-128 ledger (D2, gate units) and the tight-extraction glue, v1.47.

Glued idea (tested here). In B0 (v1.44) the reduction is tight because the
double-signing evidence is public. In Mode S (v1.43) it is not, because the
credential is hidden in the proof and must be EXTRACTED (O(q^2) time, Lemma L5),
which forced 512-bit credentials and 1024-bit keys. Mode B (v1.46) is hidden but
its evidence (s, r) is recovered PUBLICLY by the pair search from the two
certificates. So the framing reduction is: run the adversary once, run the public
pair search, output the preimage of the honest key. Time G + O(1), no extraction.
The 256-bit opening therefore satisfies the rigorous search row.

Rows (all evaluated as exact rationals, uncapped, at both endpoints of
G in [1, 2^128], gates per oracle/credential evaluation g = 2^18):

  R1 framing = preimage of an honest registry key via the public pair search,
     HRS16 search row 8 p (q+1)^2 / 2^256 with p = 64 T honest keys of the epoch
     (T domains), q = G/g. Tight: no extraction.
  R2 evasion = a seat with two openings of one key (defeats forensic
     completeness). The reduction must obtain both openings from the two proofs'
     witnesses, so extraction IS charged: t_B = G + q^2 g_sim (v1.43 L5). Named
     assumption: the best quantum collision attack on the expanding random
     quadratic map F: F2^N -> F2^(N+E) is the linear-trick search over delta
     (marked fraction 2^-E), bounded by 8 (t_B/g + 1)^2 / 2^E. Generic BHT on the
     full output is far smaller. E = 512 is chosen so that this row passes.
  R3 proof soundness for a false statement (fewer than 43 distinct registered
     openings behind the handles). Modelled as the DFMS22 Thm 4.2 commit-and-open
     row with tau repetitions of 2^b parties and w_g grinding bits:
     (22 ell + 60) q^3 / 2^512 + 20 q^2 2^-(tau b + w_g), ell = tau 2^b openings.
     CAVEAT: FAEST-style VOLE-in-the-head is multi-round; the DFM20 multi-round
     loss is NOT included. This row is the backend's obligation.
  R4 honest-proof simulation, GHHM21 Thm 3: (3 q_s / 2) sqrt((q_H + q_s + 1) gamma)
     with q_s = 2^64 honest certificates and gamma = 2^-512 commitment entropy.
  R5 pair-search false positive: 43*43 candidate openings against 64 keys of an
     812..1024-bit map: 64 * 1849 / 2^(N+E) per conflict, times 2^64 conflicts.
  Privacy is a separate decisional assumption (Z pseudorandom given Y), not a
  D2 row; see the v1.46 document.

Sizes use the FAEST v2 formula with the R3-derived tau (rigorous), compared with
the attack-derived tau of v1.46. Nothing here is a security theorem for the
proof system; R3 and the privacy assumption remain the backend's obligations.
"""

from fractions import Fraction
import argparse
import json
import math
import sys
import unittest

BUDGET_LOG2 = 128
KAPPA = 130
G_LOG2 = 18                     # gates per hash / F evaluation, as in v1.43
G_SIM_LOG2 = 12                 # extractor overhead per query, as in v1.43
N_BITS = 256                    # |s| = |r|
QUORUM, N_SEATS, MIN_OVERLAP = 43, 64, 22
HEADER = 208
HANDLE_BYTES = N_BITS // 8
PREFIX = HEADER + QUORUM * HANDLE_BYTES               # 1,584
PROOF_SLOT = 32768 - PREFIX                            # 31,184
Q_SIGN_LOG2 = 64
LAMBDA = 256
WITNESS_PER_SEAT = 2 * N_BITS + N_SEATS               # 576


def log2f(x):
    if x <= 0:
        return float('-inf')
    x = Fraction(x)
    return math.log2(x.numerator) - math.log2(x.denominator)


def sqrt_upper(x):
    """Rational upper bound on sqrt(x) for x >= 0 (x a Fraction)."""
    x = Fraction(x)
    if x == 0:
        return Fraction(0)
    n, d = x.numerator, x.denominator
    s = math.isqrt(n * d) + 1
    return Fraction(s, d)


# ---------------------------------------------------------------- rows ----
def r1_framing(G, T_domains):
    q = Fraction(G, 2 ** G_LOG2)
    p = N_SEATS * T_domains
    return 8 * p * (q + 1) ** 2 / Fraction(2 ** N_BITS)


def r2_evasion(G, expansion):
    q = Fraction(G, 2 ** G_LOG2)
    t_b = G + q * q * 2 ** G_SIM_LOG2
    return 8 * (t_b / 2 ** G_LOG2 + 1) ** 2 / Fraction(2 ** expansion)


def r3_soundness(G, tau, b, grinding):
    q = Fraction(G, 2 ** G_LOG2)
    ell = tau * 2 ** b
    return (22 * ell + 60) * q ** 3 / Fraction(2 ** 512) + 20 * q * q / Fraction(2 ** (tau * b + grinding))


def r3_faest_qrom(G, tau, b, grinding, degree=6, hash_bits=512):
    """FAEST v2 Lemma 9.39 transplanted: AdvSnd <= 10 (tau+1) Q^3 2^-2lambda
    + 10 Q^2 max(tau 2^-lambda, d 2^-lambda'), with lambda' = tau*b + grinding the
    entropy of the last challenge, d the QuickSilver degree (6 for the r-only
    witness of v1.49), 2lambda = hash_bits for the collision terms, and
    Q = queries + 2 tau + 12. The RBR errors are those of Lemma 9.37 with the
    degree-d check (Lemma 6.3 form d/2^lambda'). The VOLE-hash error assumes
    ell_hat within the Lemma 9.34 regime; v1.49 has ell_hat = 15,296 > 2^13, which
    changes only the (1 + 2^(B-50)) factor and stays far below the Delta term."""
    q = Fraction(G, 2 ** G_LOG2) + 2 * tau + 12
    lam_prime = tau * b + grinding
    rbr = max(Fraction(tau, 2 ** LAMBDA), Fraction(degree, 2 ** lam_prime))
    return 10 * (tau + 1) * q ** 3 / Fraction(2 ** hash_bits) + 10 * q * q * rbr


def min_tau_faest_qrom(b, grinding, share_log2=-133, degree=6):
    for tau in range(1, 200):
        if tau * b > 256:
            return None
        if ratio_log2(lambda G: r3_faest_qrom(G, tau, b, grinding, degree)) <= share_log2:
            return tau
    return None


def r4_simulation(G):
    q = Fraction(G, 2 ** G_LOG2)
    qs = Fraction(2 ** Q_SIGN_LOG2)
    return Fraction(3, 2) * qs * sqrt_upper((q + qs + 1) / Fraction(2 ** 512))


def r5_false_positive(G, expansion):
    """Naming a seat that did not double-sign.

    CORRECTED in v1.52 after the SAFETY game exposed the dominant path. A seat
    present in exactly one of the two certificates is named when its WOULD-BE
    handle under the other message coincides with one of the 43 handles published
    there: the pair then decodes to that seat's genuine opening, F matches, and
    the blame even re-verifies. 2*(43-22) = 42 seats are in exactly one
    certificate, so the rate is 42*43/2^|handle| per conflict, driven by the
    HANDLE width (256 bits) -- not by the registry-key width.

    Measured at toy widths (ceqs_games_v1.52.py): 0.2233 vs 0.2205 predicted at
    n=13, 0.0267 vs 0.0276 at n=16, 0.0100 vs 0.0138 at n=17.

    The previous version of this row modelled only a random candidate opening
    hitting a registry key, 2^64*64*43^2/2^(2n+E), which is ~760 bits rarer and
    so understated this row. The second term below keeps it. The row is nowhere
    near binding either way: -181.2 versus the -130 target."""
    absent = 2 * (QUORUM - MIN_OVERLAP)                     # 42
    handle_coincidence = Fraction(2 ** Q_SIGN_LOG2 * absent * QUORUM, 2 ** N_BITS)
    # up to 4 candidate openings per handle pair (kernel of the linearized map)
    key_coincidence = Fraction(
        2 ** Q_SIGN_LOG2 * N_SEATS * QUORUM * QUORUM * 4, 2 ** (2 * N_BITS + expansion))
    return handle_coincidence + key_coincidence


def ratio_log2(row):
    """max over endpoints of log2(row(G)/G) (uncapped polynomial envelopes, L4)."""
    return max(log2f(row(1)), log2f(row(2 ** BUDGET_LOG2) / Fraction(2 ** BUDGET_LOG2)))


def ledger(tau, b, grinding, expansion=512, T_domains=2 ** 10):
    rows = {
        'R1 framing (public pair search, tight)': ratio_log2(lambda G: r1_framing(G, T_domains)),
        'R2 evasion (linear-trick collision, extraction charged)': ratio_log2(lambda G: r2_evasion(G, expansion)),
        'R3 proof soundness (DFMS-modelled)': ratio_log2(lambda G: r3_soundness(G, tau, b, grinding)),
        'R4 simulation (GHHM Thm 3)': ratio_log2(r4_simulation),
        'R5 pair-search false positive': ratio_log2(lambda G: r5_false_positive(G, expansion)),
    }
    total = math.log2(sum(2 ** v for v in rows.values()))
    return {'rows': rows, 'total_ratio_log2': round(total, 3),
            'D2_pass': total <= -KAPPA, 'D2_margin_bits': round(-KAPPA - total, 3),
            'params': {'tau': tau, 'log2_parties': b, 'grinding_bits': grinding,
                       'expansion': expansion, 'domains_per_epoch': T_domains}}


def min_tau_rigorous(b, grinding, share_log2=-133):
    """Smallest tau whose R3 row alone stays below 2^share_log2 per gate."""
    for tau in range(1, 200):
        if ratio_log2(lambda G: r3_soundness(G, tau, b, grinding)) <= share_log2:
            return tau
    return None


def faest_v2_bits(tau, ell_bits, t_open, blocks, lam=LAMBDA, b_bits=16, degree=3):
    return (tau * (ell_bits + 3 * lam + b_bits) + t_open * lam + blocks * lam * tau
            + lam + 128 + 32 + (degree - 2) * lam * tau)


def certificate_bytes(tau, b, grinding):
    t_open = max(0, tau * b - grinding)          # opened nodes ~ challenge bits net of grinding
    bits = faest_v2_bits(tau, QUORUM * WITNESS_PER_SEAT, min(t_open, 245), 2)
    return PREFIX + (bits + 7) // 8


SETTINGS = ((24, 16), (24, 32), (32, 16), (32, 32), (40, 32))


def report():
    out = {'module': 'modeB_rigorous_ledger_v1.47', 'settings': []}
    for b, grinding in SETTINGS:
        tau = min_tau_rigorous(b, grinding)
        led = ledger(tau, b, grinding)
        size = certificate_bytes(tau, b, grinding)
        out['settings'].append({'log2_parties': b, 'grinding_bits': grinding,
                                'tau_rigorous': tau, 'certificate_bytes': size,
                                'fits_32KiB': size <= 32768, 'ledger': led})
    out['expansion_sweep_R2_ratio_log2'] = {
        str(E): round(ratio_log2(lambda G: r2_evasion(G, E)), 1) for E in (300, 400, 430, 512, 600)}
    out['domains_sweep_R1_ratio_log2'] = {
        str(T): round(ratio_log2(lambda G: r1_framing(G, T)), 1) for T in (1, 2 ** 10, 2 ** 16, 2 ** 20)}
    out['comparison_mode_s_v1.43'] = 'Mode S needed 512-bit credentials for the search row; Mode B keeps 256'
    # v1.49: FAEST Lemma 9.39 form of R3 for the r-only witness (degree 6, ell_hat 15,296)
    faest_rows = []
    for b, grinding in ((16, 16), (20, 16), (24, 16), (20, 32), (32, 32)):
        tau = min_tau_faest_qrom(b, grinding)
        if tau is None:
            continue
        row = ratio_log2(lambda G: r3_faest_qrom(G, tau, b, grinding))
        led = ledger(tau, b, grinding)
        led['rows']['R3 proof soundness (FAEST v2 Lemma 9.39 form, degree 6)'] = row
        total = math.log2(sum(2 ** v for v in led['rows'].values()))
        faest_rows.append({'log2_parties': b, 'grinding_bits': grinding, 'tau': tau,
                           'tau_b_plus_wg': tau * b + grinding, 'R3_faest_qrom_log2': round(row, 1),
                           'total_with_faest_row_log2': round(total, 3),
                           'D2_margin_bits': round(-KAPPA - total, 3)})
    out['faest_qrom_R3_variant_v1.49'] = faest_rows
    return out


class Tests(unittest.TestCase):
    def test_r1_tight_passes_at_256_bits(self):
        self.assertLess(ratio_log2(lambda G: r1_framing(G, 2 ** 10)), -133)
        self.assertLess(ratio_log2(lambda G: r1_framing(G, 2 ** 20)), -133)
        self.assertGreater(ratio_log2(lambda G: r1_framing(G, 2 ** 24)), -133)   # too many domains

    def test_r2_needs_expansion_over_430(self):
        self.assertGreater(ratio_log2(lambda G: r2_evasion(G, 300)), -130)
        self.assertLess(ratio_log2(lambda G: r2_evasion(G, 512)), -133)

    def test_r3_tau_and_fit(self):
        self.assertEqual(min_tau_rigorous(32, 32), 7)
        self.assertEqual(min_tau_rigorous(24, 16), 9)
        self.assertLessEqual(certificate_bytes(7, 32, 32), 32768)
        self.assertLessEqual(certificate_bytes(7, 32, 16), 32768)
        self.assertGreater(certificate_bytes(9, 24, 16), 32768)

    def test_r5_handle_coincidence_dominates(self):
        r5 = ratio_log2(lambda G: r5_false_positive(G, 512))
        self.assertAlmostEqual(r5, -181.2, places=1)          # was -943 before v1.52
        self.assertLess(r5, -133)                             # still far from binding
        # the handle path dominates the registry-key path by a wide margin
        absent = 2 * (QUORUM - MIN_OVERLAP)
        handle = Fraction(2 ** Q_SIGN_LOG2 * absent * QUORUM, 2 ** N_BITS)
        key = Fraction(2 ** Q_SIGN_LOG2 * N_SEATS * QUORUM * QUORUM * 4,
                       2 ** (2 * N_BITS + 512))
        self.assertGreater(log2f(handle) - log2f(key), 700)

    def test_full_ledger_passes(self):
        led = ledger(7, 32, 32)
        self.assertTrue(led['D2_pass'])
        self.assertGreater(led['D2_margin_bits'], 3)

    def test_faest_qrom_row(self):
        # tau*b + w_g >= 230 is what the Lemma 9.39 form requires at 2^18 gates/query.
        self.assertEqual(min_tau_faest_qrom(20, 16), 11)
        self.assertEqual(min_tau_faest_qrom(24, 16), 9)
        self.assertEqual(min_tau_faest_qrom(32, 32), 7)
        self.assertLess(ratio_log2(lambda G: r3_faest_qrom(G, 11, 20, 16)), -133)
        self.assertGreater(ratio_log2(lambda G: r3_faest_qrom(G, 10, 20, 16)), -133)

    def test_faest_reproduction(self):
        self.assertEqual(faest_v2_bits(22, 3104, 245, 3, degree=2), 20696 * 8)
        self.assertEqual(faest_v2_bits(22, 2688, 218, 2, degree=2), 17984 * 8)


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--report', action='store_true')
    a = ap.parse_args(argv)
    if a.report:
        print(json.dumps(report(), indent=2))
        return 0
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if r.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
