#!/usr/bin/env python3
r"""CE-QS security games with measured query complexity, v1.52.

Repository layout. This file is domains/09-security-games-and-attack-lab/src/ceqs_games.py.
Run it from this directory:

  python3 ceqs_games.py --self-test          (4 unit tests)
  python3 ceqs_games.py --all                (the four games; --json prints the
                                              report that results/ keeps)

It loads the Mode B revision this record was measured against from the hidden-signers
domain: ../../08-hidden-signers/history/hidden-signer-mode-b-v1.50.py. Companion
documents in this domain: docs/games-methodology.md, one file per game under docs/,
docs/validation-status.md and results/attack-lab-results.md (the recorded run).

Why this file exists. The v1.51 attack lab answered "did any attack succeed?".
That is the weaker question. This file states each attack as a GAME first, then
measures the attacker's query complexity Q as a function of the parameter, fits
an exponent, and compares it with the theoretical bound:

    GAME -> attacker's information -> allowed oracle queries -> winning condition
         -> attack algorithm -> measured Q(n) -> fitted exponent -> theory

Four games, three of which the attacker can actually WIN at toy parameters (a
game nobody can win teaches nothing about its exponent):

  FRAME     recover an opening of an honest seat's registry key from its public
            handle, and use it to make extraction name that seat.
            Won at every n tested. Measured slope ~1.0 (classical).
  SUPPRESS  make extraction return nothing, by finding two messages whose
            challenge maps are equal. This is the flaw the independent pass
            found in the v1.46 handle. Won against v1.46 AND against v1.50 at
            toy sizes -- the point is that the same birthday law applies to a
            different output length: h = n for v1.46, h = 3n for v1.50.
  EVADE     with at least 22 corrupt seats, make extraction name fewer than 22,
            by opening one corrupt registry key twice. Won; measured slope ~1.0
            in the expansion E.
  SAFETY    with at most 21 corrupt seats, produce two valid conflicting
            certificates at all. Provably impossible by counting; tested
            exhaustively for every corruption level 0..23.

The extrapolation caveat is the point of the exercise, not a footnote: a slope
fitted over n = 8..19 and extended to n = 256 accumulates several bits of error
(see SUPPRESS below, where it overshoots the exact birthday value by ~9 bits).
The 128-bit conclusions come from the reductions in domain 08's docs/mode-b-security.md, not
from these fits. What the fits establish is that the reduced systems obey the
laws those reductions assume.

All parameters here are deliberately weak. n must not be a multiple of 3, or
r^7 stops being a permutation of GF(2^n) and the construction refuses to build.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import sys
import time
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# The path pins the revision this record was measured against: the hidden-signers
# domain keeps the superseded Mode B v1.50 unchanged in its history/ directory.
m50 = _load('modeB50', '../../08-hidden-signers/history/hidden-signer-mode-b-v1.50.py')
m46 = sys.modules['modeB46']
N_SEATS, QUORUM, MIN_OVERLAP = m46.N_SEATS, m46.QUORUM, m46.MIN_OVERLAP
ModeBError = m46.ModeBError
CFG0, DOM0 = bytes(64), bytes(range(64))


def digest64(x):
    return hashlib.shake_256(repr(x).encode()).digest(64)


def fit(xs, ys):
    """Least squares log2 Q = a*x + b."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    return a, my - a * mx


def _instance(n, expansion, tag, attempts=64):
    """A toy registry, redrawing on toy-size birthday collisions.

    Two can occur at these widths and both are artefacts of the weak parameters,
    not faults: 64 registry keys can collide in a (2n+E)-bit key space, and 43
    handles can collide in an n-bit handle space. The construction refuses both,
    so redraw. Seeding is deterministic (Python's hash() is randomised per
    process, which would make these runs irreproducible)."""
    p = m46.make_params(n=n, expansion=expansion, seed=b'game/' + tag)
    for attempt in range(attempts):
        seed = int.from_bytes(hashlib.shake_256(
            b'game/' + tag + b'/%d/%d/%d' % (n, expansion, attempt)).digest(8), 'big')
        rng = random.Random(seed)
        try:
            registry, secrets = m46.build_registry(p, b'game-epoch', (DOM0,), rng)
            m50.encode(p, registry, secrets, DOM0, digest64('probe'), list(range(QUORUM)))
            return p, registry, secrets
        except ModeBError:
            continue
    raise RuntimeError('no collision-free toy instance in %d attempts; raise n' % attempts)


def _pack(p, cfg, message, handles):
    import struct
    payload = b''.join(handles) + b'STRUCTURE-ONLY'
    return struct.pack(m46.HEADER_FORMAT, m50.MAGIC, m50.VERSION, m50.SUITE, cfg, DOM0,
                       message, QUORUM, p.handle_bytes, len(payload)) + payload


# ===========================================================================
# GAME 1 - FRAME
# ===========================================================================
GAME_FRAME = {
    'name': 'FRAME',
    'informal': 'Make public extraction name an honest seat that authorized nothing.',
    'attacker_receives': ['public parameters (key map F, field, challenge derivation)',
                          'the registry: all 64 public keys Y[d][i]',
                          'a certificate and all 43 published handles',
                          'the target honest seat i* and its handle Z',
                          'the domain and both messages'],
    'attacker_does_not_receive': ["any seat's opening (s, r)", 'proof randomness'],
    'oracle': 'evaluations of the public key map F (counted as Q)',
    'wins_if': "it outputs (s', r') with F(s'||r') = Y[d][i*], which lets it place a "
               "handle for i* in a second certificate so that extraction names i*",
    'attack': "for each candidate r: derive s = L_c^-1(Z + r^7) (the handle is public and "
              "L_c is invertible), then test F(s||r) = Y. This is the generic attack: the "
              "published handle collapses the search from 2^(2n) to 2^n.",
    'theory_classical': 'mean Q = 2^(n-1); slope 1.0 bits per bit of opening',
    'theory_quantum': '(pi/4) 2^(n/2) Grover iterations; slope 0.5 (measured in v1.51 '
                      'experiment C, exact state-vector simulation)',
}


def game_frame(ns=(8, 10, 11, 13, 14), expansion=8, targets=6, verbose=True):
    rows = []
    for n in ns:
        p, registry, secrets = _instance(n, expansion, b'frame')
        cfg = m46.cfg_of(registry, p)
        f = p.field
        qs, t0 = [], time.time()
        for t in range(targets):
            seat = t
            message = digest64(('frame', n, t))
            ch = m50.Challenge(p, cfg, DOM0, message)
            s_true, r_true = secrets[DOM0][seat]
            Z = f.G(r_true) ^ ch.apply(s_true)
            Y = registry.keys[DOM0][seat]
            Q, won = 0, None
            for rr in range(1 << n):
                ss = ch.invert(Z ^ f.G(rr))
                Q += 1
                if p.keymap.to_bytes(p.keymap.evaluate(m46.opening_to_input(p, ss, rr))) == Y:
                    won = (ss, rr)
                    break
            assert won is not None, 'the game must be winnable by exhaustive search'
            qs.append(Q)
        mean = sum(qs) / len(qs)
        rows.append({'n': n, 'targets': targets, 'queries': qs, 'mean_Q': mean,
                     'log2_mean_Q': math.log2(mean), 'theory_mean_Q': 2 ** (n - 1),
                     'seconds': round(time.time() - t0, 1)})
        if verbose:
            print('  n=%2d  mean Q = %9.1f  log2 = %5.2f   theory 2^(n-1) = %d   (%.1fs)'
                  % (n, mean, math.log2(mean), 2 ** (n - 1), rows[-1]['seconds']))
    a, b = fit([r['n'] for r in rows], [r['log2_mean_Q'] for r in rows])
    # Close the loop: a recovered opening really does win the game.
    demo = _frame_endgame(expansion, verbose)
    out = {'game': GAME_FRAME, 'measurements': rows,
           'fit': {'slope': round(a, 4), 'intercept': round(b, 3),
                   'theory_slope': 1.0, 'theory_intercept': -1.0},
           'extrapolation_n256_log2_classical': round(a * 256 + b, 1),
           'exact_theory_n256_log2_classical': 255.0,
           'endgame_demonstration': demo}
    if verbose:
        print('  FIT  log2 Q = %.4f n + %.3f   (theory: 1.0 n - 1.0)' % (a, b))
        print('  extrapolation to n=256: 2^%.1f   exact theory 2^255' % (a * 256 + b))
        print('  endgame: %s' % demo['result'])
    return out


def _frame_endgame(expansion, verbose, n=14):
    """Having recovered an honest seat's opening, actually frame it end to end.

    The victim authorises honest_msg only. The attacker, holding the recovered
    opening, manufactures the victim's handle for forged_msg and publishes a
    conflicting certificate; extraction must then name the victim."""
    p, registry, secrets = _instance(n, expansion, b'frame-end')
    cfg = m46.cfg_of(registry, p)
    victim = 0
    others = [i for i in range(N_SEATS) if i != victim][:QUORUM - 1]
    recovered = secrets[DOM0][victim]           # what the search above recovers
    for k in range(64):                         # redraw on toy-size handle collisions
        honest_msg, forged_msg = digest64(('honest', k)), digest64(('forged', k))
        try:
            f0 = m50.encode(p, registry, secrets, DOM0, honest_msg, list(range(QUORUM)))
            ch = m50.Challenge(p, cfg, DOM0, forged_msg)
            handles = sorted([m50.handle(p, ch, recovered)]
                             + [m50.handle(p, ch, secrets[DOM0][i]) for i in others])
            if len(set(handles)) != QUORUM:
                continue
            res = m50.extract(p, registry, f0, _pack(p, cfg, forged_msg, handles))
        except ModeBError:
            continue
        named = victim in res['seats']
        return {'result': 'victim seat %d named by extraction: %s (a recovered opening '
                          'wins the game)' % (victim, named), 'victim_named': named,
                'seats_named': len(res['seats'])}
    return {'result': 'no collision-free toy instance', 'victim_named': False}


# ===========================================================================
# GAME 2 - SUPPRESS
# ===========================================================================
GAME_SUPPRESS = {
    'name': 'SUPPRESS',
    'informal': 'Make public extraction return nothing, so a real equivocation goes unpunished.',
    'attacker_receives': ['public parameters', 'the registry', 'the challenge derivation',
                          'freedom to choose the two conflicting messages'],
    'attacker_does_not_receive': ['any opening'],
    'oracle': 'evaluations of the public challenge derivation (counted as Q)',
    'wins_if': 'it finds m0 != m1 in one domain whose challenge maps are EQUAL, so the '
               'difference map D is identically zero and the extractor cannot solve for s',
    'attack': 'birthday search over messages',
    'v1.46_output_length': 'h = n  (a single challenge c; D(s) = (c0+c1)s)',
    'v1.50_output_length': 'h = 3n (the triple; D(s) = a s + b s^2 + c s^4)',
    'lemma': 'D is a linearized polynomial of 2-degree <= 2, so its kernel has dimension '
             '<= 2 and a PARTIAL collision leaves at most 4 candidate openings, all '
             'filtered by the registry. Only a full collision wins.',
    'theory': 'Q = sqrt(pi/2 * 2^h); slope 0.5 per bit of h',
}


def game_suppress(v46_ns=(8, 10, 11, 13, 14, 16, 17), v50_ns=(8, 10, 11),
                  expansion=8, trials46=12, trials50=(6, 4, 2), cap=4_000_000,
                  verbose=True):
    pts, rows = [], []
    for n in v46_ns:
        p = m46.make_params(n=n, expansion=expansion, seed=b'game/sup')
        qs = []
        for trial in range(trials46):
            seen, Q = {}, 0
            for k in range(cap):
                msg = digest64(('s46', n, trial, k))
                Q += 1
                c = m46.challenge(p, CFG0, DOM0, msg)
                if c in seen:
                    qs.append(Q)
                    break
                seen[c] = msg
        mean = sum(qs) / len(qs)
        rows.append({'scheme': 'v1.46', 'n': n, 'h': n, 'trials': len(qs), 'mean_Q': mean,
                     'log2_mean_Q': math.log2(mean),
                     'theory_Q': math.sqrt(math.pi / 2 * 2 ** n)})
        pts.append((n, math.log2(mean)))
        if verbose:
            print('  v1.46  n=%2d h=%2d  mean Q = %10.1f  log2 = %5.2f  theory = %10.1f'
                  % (n, n, mean, math.log2(mean), rows[-1]['theory_Q']))
    for idx, n in enumerate(v50_ns):
        p = m46.make_params(n=n, expansion=expansion, seed=b'game/sup')
        h = 3 * n
        qs = []
        for trial in range(trials50[idx]):
            seen, Q = {}, 0
            for k in range(cap):
                msg = digest64(('s50', n, trial, k))
                Q += 1
                ch = m50.Challenge(p, CFG0, DOM0, msg)
                key = (ch.a, ch.b, ch.c)
                if key in seen:
                    qs.append(Q)
                    break
                seen[key] = msg
        if not qs:
            continue
        mean = sum(qs) / len(qs)
        rows.append({'scheme': 'v1.50', 'n': n, 'h': h, 'trials': len(qs), 'mean_Q': mean,
                     'log2_mean_Q': math.log2(mean),
                     'theory_Q': math.sqrt(math.pi / 2 * 2 ** h)})
        pts.append((h, math.log2(mean)))
        if verbose:
            print('  v1.50  n=%2d h=%2d  mean Q = %10.1f  log2 = %5.2f  theory = %10.1f'
                  % (n, h, mean, math.log2(mean), rows[-1]['theory_Q']))
    a, b = fit([x for x, _ in pts], [y for _, y in pts])
    out = {'game': GAME_SUPPRESS, 'measurements': rows,
           'fit_over_both_schemes': {'slope_per_bit_of_h': round(a, 4),
                                     'intercept': round(b, 3),
                                     'theory_slope': 0.5, 'theory_intercept': 0.326},
           'extrapolation': {
               'v1.46_h256_fitted_log2': round(a * 256 + b, 1),
               'v1.46_h256_exact_birthday_log2': round(math.log2(math.sqrt(math.pi / 2 * 2 ** 256)), 1),
               'v1.50_h768_fitted_log2': round(a * 768 + b, 1),
               'v1.50_h768_exact_birthday_log2': round(math.log2(math.sqrt(math.pi / 2 * 2 ** 768)), 1)},
           'quantum_costs_from_the_project_CFHL_bound': {
               'v1.46_queries_log2': 81.7, 'v1.46_gates_log2': 99.7,
               'v1.50_queries_log2': 252.4, 'v1.50_gates_log2': 270.4,
               'gate_budget_log2': 128,
               'verdict': 'v1.46 is inside the budget (broken by 28 bits); v1.50 is '
                          'outside it by 142 bits'}}
    if verbose:
        print('  FIT over both schemes: log2 Q = %.4f h + %.3f   (theory 0.5 h + 0.326)' % (a, b))
        e = out['extrapolation']
        print('  extrapolation h=256: fitted 2^%.1f vs exact 2^%.1f  (fit error %.1f bits)'
              % (e['v1.46_h256_fitted_log2'], e['v1.46_h256_exact_birthday_log2'],
                 e['v1.46_h256_fitted_log2'] - e['v1.46_h256_exact_birthday_log2']))
        print('  extrapolation h=768: fitted 2^%.1f vs exact 2^%.1f  (fit error %.1f bits)'
              % (e['v1.50_h768_fitted_log2'], e['v1.50_h768_exact_birthday_log2'],
                 e['v1.50_h768_fitted_log2'] - e['v1.50_h768_exact_birthday_log2']))
    return out


# ===========================================================================
# GAME 3 - EVADE  (the whole-system conflicting-certificate attack)
# ===========================================================================
GAME_EVADE = {
    'name': 'EVADE',
    'informal': 'Equivocate with 22 corrupt seats and make extraction name fewer than 22.',
    'attacker_receives': ['public parameters and registry',
                          'the openings of its own corrupt seats',
                          'both certificates it is about to publish'],
    'oracle': 'evaluations of F / linear solves, counted as delta trials',
    'wins_if': 'both certificates satisfy the relation R_B, the messages differ, the '
               'domain is the same, and extraction names fewer than 22 seats',
    'attack': "open one corrupt registry key twice: find x' != x with F(x') = F(x) by the "
              "linear trick (fix delta, solve F(x+delta)+F(x)=0, which is linear in x), "
              "then use x in one certificate and x' in the other, so that seat's handle "
              "pair decodes to garbage",
    'theory': 'mean delta trials = 2^E; measured ~2^(E+1.2) because delta always lies in '
              'the kernel of A_delta, so rank <= N-1 and consistency costs 2^-(E+1). The '
              'ledger charges 2^-E, i.e. it is conservative.',
    'note_on_the_fix': 'v1.49 cryptanalysis item 2: the old extractor ABORTED when fewer '
                       'than 22 seats were found, so one evader hid all the others. v1.50 '
                       'reports every seat it identifies and flags completeness.',
}


def game_evade(N=16, expansions=(2, 4, 6, 8, 10, 12), trials=8, cap=400000, verbose=True):
    rows = []
    for E in expansions:
        counts, t0 = [], time.time()
        for t in range(trials):
            q = m46.QuadMap(N, N + E, b'game/ev/%d/%d' % (E, t))
            rng = random.Random(500 + 31 * E + t)
            tried, found = 0, None
            while tried < cap:
                delta = rng.getrandbits(N) or 1
                tried += 1
                x = q.collision_for_delta(delta)
                if x is not None and q.evaluate(x) == q.evaluate(x ^ delta):
                    found = (x, delta)
                    break
            if found:
                counts.append(tried)
        mean = sum(counts) / len(counts)
        rows.append({'expansion': E, 'trials': len(counts), 'mean_delta_trials': mean,
                     'log2_mean': math.log2(mean), 'theory_2^E': 2 ** E,
                     'refined_theory_2^(E+1)': 2 ** (E + 1),
                     'seconds': round(time.time() - t0, 1)})
        if verbose:
            print('  E=%2d  mean delta trials = %9.1f  log2 = %5.2f  (2^E=%d, 2^(E+1)=%d)'
                  % (E, mean, math.log2(mean), 2 ** E, 2 ** (E + 1)))
    a, b = fit([r['expansion'] for r in rows], [r['log2_mean'] for r in rows])
    consequence = _evade_consequence(verbose)
    out = {'game': GAME_EVADE, 'measurements': rows,
           'fit': {'slope': round(a, 4), 'intercept': round(b, 3), 'theory_slope': 1.0},
           'extrapolation_E512_log2_classical': round(a * 512 + b, 1),
           'quantum_E512_log2': 256.0,
           'end_to_end_consequence': consequence}
    if verbose:
        print('  FIT  log2 Q = %.4f E + %.3f   (theory slope 1.0)' % (a, b))
        print('  end-to-end: %s' % consequence['summary'])
    return out


def _evade_consequence(verbose, n=14, expansion=8):
    """Build the two certificates for real and show what extraction does when one
    seat is represented by two different openings of one registry key."""
    p, registry, secrets = _instance(n, expansion, b'evade')
    cfg = m46.cfg_of(registry, p)
    corrupt = list(range(MIN_OVERLAP))                 # exactly 22 double-signers
    seats0 = list(range(QUORUM))
    seats1 = corrupt + list(range(QUORUM, N_SEATS))
    for k in range(64):                                # redraw on handle collisions
        m0, m1 = digest64(('ev0', k)), digest64(('ev1', k))
        try:
            f0 = m50.encode(p, registry, secrets, DOM0, m0, seats0)
            # Certificate 1: seat 0 is represented by an opening the registry does
            # not know -- what a genuine second opening of its key would look like
            # to the extractor (a real collision is out of reach at this width).
            ch = m50.Challenge(p, cfg, DOM0, m1)
            handles = [m50.handle(p, ch, secrets[DOM0][i]) for i in seats1 if i != 0]
            handles.append(m50.handle(p, ch, (12345, 6789)))
            handles = sorted(handles)
            if len(set(handles)) != QUORUM:
                continue
            res = m50.extract(p, registry, f0, _pack(p, cfg, m1, handles))
        except ModeBError:
            continue
        return {'corrupt_double_signers': len(corrupt),
                'seats_named_by_v1_50': res['seats'],
                'count': len(res['seats']),
                'complete_flag': res['complete'],
                'v1_46_behaviour_would_be': 'ABORT (fewer than 22) -- all 21 other '
                                            'culprits hidden',
                'summary': 'one evader costs exactly itself: v1.50 names the other %d '
                           'and flags complete=%s; v1.46 would have named nobody'
                           % (len(res['seats']), res['complete'])}
    return {'summary': 'no collision-free toy instance', 'count': None,
            'complete_flag': None}


# ===========================================================================
# GAME 4 - SAFETY
# ===========================================================================
GAME_SAFETY = {
    'name': 'SAFETY',
    'informal': 'With at most 21 corrupt seats, equivocate at all.',
    'attacker_receives': ['the openings of its corrupt seats',
                          'honest approvals for one message per domain'],
    'wins_if': 'it assembles two certificates of 43 valid seats each, same domain, '
               'different messages',
    'why_it_cannot': 'each certificate needs 43 seats; an honest seat contributes to at '
                     'most one message per domain; so 43 + 43 <= 64 + C, i.e. C >= 22',
    'theory': 'impossible for C <= 21; possible and fully attributable for C >= 22',
}


def game_safety(n=14, expansion=8, corruption_levels=tuple(range(0, 24)), verbose=True):
    p, registry, secrets = _instance(n, expansion, b'safety')
    rows = []
    for C in corruption_levels:
        corrupt = list(range(C))
        honest = [i for i in range(N_SEATS) if i not in corrupt]
        half = len(honest) // 2
        seats0 = corrupt + honest[:QUORUM - C] if C <= QUORUM else corrupt[:QUORUM]
        remaining = honest[QUORUM - C:] if C <= QUORUM else []
        seats1 = corrupt + remaining[:QUORUM - C] if C <= QUORUM else corrupt[:QUORUM]
        feasible = (len(set(seats0)) == QUORUM and len(set(seats1)) == QUORUM
                    and len(set(seats0) & set(seats1)) >= 0
                    and not (set(seats0) & set(seats1)) - set(corrupt))
        row = {'corrupt_seats': C, 'two_conflicting_certificates_possible': bool(feasible)}
        if feasible:
            for k in range(64):               # redraw on toy-size handle collisions
                m0, m1 = digest64(('sf0', C, k)), digest64(('sf1', C, k))
                try:
                    f0 = m50.encode(p, registry, secrets, DOM0, m0, seats0)
                    f1 = m50.encode(p, registry, secrets, DOM0, m1, seats1)
                    res = m50.extract(p, registry, f0, f1)
                except ModeBError:
                    continue
                genuine = set(seats0) & set(seats1)
                named = set(res['seats'])
                row['seats_named'] = len(named)
                row['genuine_double_signers'] = len(genuine)
                row['missed'] = sorted(genuine - named)          # completeness failures
                row['false_positives'] = sorted(named - genuine)  # handle coincidences
                row['all_named_are_corrupt'] = named <= set(corrupt)
                break
        rows.append(row)
        if verbose:
            mark = 'EQUIVOCATION POSSIBLE' if feasible else 'impossible (counting)'
            extra = ''
            if feasible and 'seats_named' in row:
                extra = ('  -> names %d of %d genuine double-signers, missed %d, '
                         'handle-coincidence false positives %s'
                         % (row['seats_named'], row['genuine_double_signers'],
                            len(row['missed']), row['false_positives']))
            print('  C=%2d  %-22s%s' % (C, mark, extra))
    threshold = min((r['corrupt_seats'] for r in rows
                     if r['two_conflicting_certificates_possible']), default=None)
    return {'game': GAME_SAFETY, 'measurements': rows,
            'measured_threshold': threshold, 'theory_threshold': MIN_OVERLAP,
            'matches_theory': threshold == MIN_OVERLAP}


# ===========================================================================
# Runner
# ===========================================================================
def run_all(verbose=True):
    rep = {'module': 'ceqs_games'}
    if verbose:
        print('\nGAME 1 - FRAME (recover an honest opening and name that seat):')
    rep['FRAME'] = game_frame(verbose=verbose)
    if verbose:
        print('\nGAME 2 - SUPPRESS (silence extraction by a challenge collision):')
    rep['SUPPRESS'] = game_suppress(verbose=verbose)
    if verbose:
        print('\nGAME 3 - EVADE (equivocate with 22 corrupt seats, hide the culprits):')
    rep['EVADE'] = game_evade(verbose=verbose)
    if verbose:
        print('\nGAME 4 - SAFETY (equivocate at all with <= 21 corrupt seats):')
    rep['SAFETY'] = game_safety(verbose=verbose)
    if verbose:
        print('\nSummary of measured vs theoretical exponents:')
        print('  FRAME    classical slope %.4f  (theory 1.0)'
              % rep['FRAME']['fit']['slope'])
        print('  SUPPRESS slope per bit of output %.4f  (theory 0.5)'
              % rep['SUPPRESS']['fit_over_both_schemes']['slope_per_bit_of_h'])
        print('  EVADE    slope per expansion bit %.4f  (theory 1.0)'
              % rep['EVADE']['fit']['slope'])
        print('  SAFETY   threshold %s  (theory %d)'
              % (rep['SAFETY']['measured_threshold'], MIN_OVERLAP))
    return rep


class GameTests(unittest.TestCase):
    def test_frame_is_winnable_and_scales(self):
        r = game_frame(ns=(8, 10, 11), targets=4, verbose=False)
        self.assertTrue(0.7 < r['fit']['slope'] < 1.4)
        self.assertTrue(r['endgame_demonstration']['victim_named'])

    def test_suppress_law_holds_for_both_schemes(self):
        r = game_suppress(v46_ns=(8, 10, 11), v50_ns=(8,), trials46=6, trials50=(4,),
                          verbose=False)
        self.assertTrue(0.35 < r['fit_over_both_schemes']['slope_per_bit_of_h'] < 0.75)
        self.assertTrue(any(m['scheme'] == 'v1.50' for m in r['measurements']))

    def test_evade_one_evader_costs_only_itself(self):
        c = _evade_consequence(verbose=False)
        self.assertEqual(c['count'], MIN_OVERLAP - 1)
        self.assertFalse(c['complete_flag'])

    def test_safety_threshold_is_22(self):
        r = game_safety(corruption_levels=tuple(range(18, 24)), verbose=False)
        self.assertEqual(r['measured_threshold'], MIN_OVERLAP)
        for row in r['measurements']:
            if row.get('two_conflicting_certificates_possible'):
                # Completeness is the security property: no genuine double-signer
                # may be missed. Extra names are handle coincidences, whose rate is
                # ~42*43/2^n at toy width and ~2^-244 at production width; they are
                # bounded, not forbidden (see game_safety's note).
                self.assertEqual(row['missed'], [])
                self.assertLessEqual(len(row['false_positives']), 3)


def main(argv=None):
    ap = argparse.ArgumentParser(description='CE-QS security games (v1.52).')
    g = ap.add_mutually_exclusive_group(required=True)
    for flag in ('all', 'frame', 'suppress', 'evade', 'safety', 'self-test'):
        g.add_argument('--' + flag, action='store_true')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    verbose = not a.json
    if a.self_test:
        r = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(GameTests))
        return 0 if r.wasSuccessful() else 1
    rep = (run_all(verbose) if a.all else
           game_frame(verbose=verbose) if a.frame else
           game_suppress(verbose=verbose) if a.suppress else
           game_evade(verbose=verbose) if a.evade else
           game_safety(verbose=verbose))
    if a.json:
        print(json.dumps(rep, indent=2, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
