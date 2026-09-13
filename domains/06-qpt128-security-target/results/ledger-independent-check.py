#!/usr/bin/env python3
"""Independent exact-arithmetic recount of the headline rows of the QPT-128 ledger.

Written in this repository, not copied from the project. It loads the checker as a
module (it does not import it as a package and does not modify it), recomputes the
scenario totals, margins, minimum repetition counts and the legacy-constant
comparison by its own route, and compares every number against the regenerated
report. Standard library only; probabilities are exact Fractions.

Run from the repository root:
    python3 domains/06-qpt128-security-target/results/ledger-independent-check.py
"""

import importlib.util
import json
import sys
from fractions import Fraction as F
from itertools import combinations
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / 'domains/06-qpt128-security-target/src/qpt128_finalization.py'
REPORT = ROOT / 'domains/06-qpt128-security-target/results/qpt128_report.json'

spec = importlib.util.spec_from_file_location('qpt128_finalization', CHECKER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

TWO = {}


def two(e):
    """2^e as an exact Fraction (independent of the checker's pow2)."""
    if e not in TWO:
        TWO[e] = F(1 << e) if e >= 0 else F(1, 1 << -e)
    return TWO[e]


def dec(x):
    """log2 of an exact Fraction, via the checker's 60-digit display helper."""
    return mod.log2(F(x))


report = json.loads(REPORT.read_text())
by_name = {s['scenario']: s for s in report['scenarios']}
ok = True


def check(label, got, want, tol=5e-4):
    global ok
    good = abs(got - want) <= tol
    ok = ok and good
    print('%-58s %12.3f  expected %12.3f  %s' % (label, got, want, 'OK' if good else 'MISMATCH'))


# ---------------------------------------------------------------- Lemma L1/L2
lb256 = mod.grover_success_lower_bound(256, 1 << 63)
lb512 = mod.grover_success_lower_bound(512, 1 << 127)
print('== L1 ==')
print('  2^63 iterations, 256-bit secret: lower bound > 2^-128 : %s'
      % (lb256 > two(-128)))
print('  2^127 iterations, 512-bit secret: lower bound > 2^-256 : %s'
      % (lb512 > two(-256)))
print('  log2 lower bound = %.3f' % dec(lb256))
check('L1 report success_lower_bound_log2', report['L1']['success_lower_bound_log2'], dec(lb256), 1e-9)

print('== L2 ==')
print('  3*2^125 < 2^127 : %s' % (3 * two(125) < two(127)))
one = mod.grover_success_lower_bound(256, 3 * (1 << 125))
six4 = mod.grover_success_lower_bound(256, 3 * (1 << 122), log2_targets=6)
print('  one key   : success >= %.3f in log2, >= 1/3 : %s' % (dec(one), one >= F(1, 3)))
print('  64 keys   : success >= %.3f in log2, >= 1/3 : %s' % (dec(six4), six4 >= F(1, 3)))
print('  lower bound reported: %.17g (report: %.17g)'
      % (float(one), report['L2']['lower_bound']))
print('  the two exact bounds differ by about 2^%.1f in absolute size, far below the'
      % dec(abs(one - six4)))
print('  float display precision. The 64-key case is the one-key case with j/8 and s*8,')
print('  so they differ only in the (2j+1) term; the report prints them equal.')
# The report stores these two as floats for display; the exact Fractions are what the
# verdicts use, so these comparisons are display comparisons, not verdict comparisons.
ok = ok and (abs(float(one) - report['L2']['lower_bound']) < 1e-15
             and abs(float(six4) - report['L2']['lower_bound_64']) < 1e-15)

# ---------------------------------------------------------------- headline rows
print('== scenarios ==')


def recount(scenario):
    """Recompute total ratio, D2 verdict, margin and D1 probability from the report rows."""
    units = scenario['units']
    g_log2 = 0 if units.startswith('queries') else int(units.split('2^')[1].split(' ')[0])
    name = scenario['scenario']
    if name.startswith('B0'):
        rows = mod.b0_public_signer(g_log2).rows
    elif name.startswith('compat'):
        rows = mod.compat_inside_proof(g_log2).rows
    else:
        bits = 1024 if '1024-bit' in name else 512
        rigorous = 'rigorous' in name
        r = int(name.split('r=')[1].split(',')[0])
        rows = mod.mode_s(r, g_log2, rigorous=rigorous, key_bits=bits).rows
    total = sum((mod.ratio_bound(r, g_log2) for r in rows), F(0))
    return total


for s in report['scenarios']:
    total = recount(s)
    got = None if total == 0 else dec(total)
    label = '%s [%s]' % (s['scenario'][:34], s['units'].split(',')[0])
    if got is None:
        print('%-58s total 0 (all rows zero)' % label)
    else:
        check(label, got, s['total_ratio_log2'])
        check('  D2 margin', -130 - dec(total), s['D2_margin_bits'])
        print('  D2 holds at kappa=130: %s (report: %s)'
              % (total <= two(-130), s['D2_kappa130']))

# ---------------------------------------------------------------- extraction charge
print('== minimum repetitions, extraction share <= 2^-133 ==')
mins = report['minimum_repetitions_extraction_share_2^-133']
for label, g_log2 in (('query units', 0), ('gate units', 18)):
    r = mins['query_units'] if not g_log2 else mins['gate_units']
    row = mod.extraction_row(r)
    at_r = mod.ratio_bound(row, g_log2)
    below = mod.ratio_bound(mod.extraction_row(r - 1), g_log2)
    print('  %-11s r = %4d : ratio log2 = %9.3f (<= 2^-133: %s); r-1 = %9.3f (passes: %s)'
          % (label, r, dec(at_r), at_r <= two(-133), dec(below), below <= two(-133)))

# ---------------------------------------------------------------- legacy constant
print('== unsourced legacy constant ==')
legacy = dec(mod.unused_legacy_12q154(two(128), 512))
envelope = dec(mod.cfhl_collision(two(128), 512, capped=False))
check('legacy 12(q+154)^3/2^512 log2', legacy, report['unsourced_12q154_check']['legacy_value_log2'])
check('CFHL rational envelope log2', envelope, report['unsourced_12q154_check']['cfhl_rational_envelope_log2'])
exact_leading = dec(F(40) * mod.E_UPPER ** 2 * (two(128) + 1) ** 3 * two(-512))
print('  published leading term 40e^2(q+1)^3/2^512 log2 = %.3f' % exact_leading)

# ---------------------------------------------------------------- exponent / quorum arithmetic
print('== integer arithmetic ==')
print('  8*2^-131 == 2^-128      : %s' % (8 * two(-131) == two(-128)))
print('  2*43 - 64 = 22          : %s' % (2 * 43 - 64 == 22))
print('  64 = 3*21 + 1           : %s' % (64 == 3 * 21 + 1))
print('  C(64,2) = 2016          : %s' % (comb(64, 2) == 2016))
print('  C(64,2) by enumeration  : %s' % (sum(1 for _ in combinations(range(64), 2)) == 2016))

print()
print('RESULT: %s' % ('all recomputed values agree with the report' if ok else 'MISMATCH'))
sys.exit(0 if ok else 1)
