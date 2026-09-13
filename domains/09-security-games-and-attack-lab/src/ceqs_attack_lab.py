#!/usr/bin/env python3
r"""CE-QS attack lab, v1.51 — empirical testing of the deployed constructions.

Repository layout. This file is
domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py. Run it from this
directory:

  python3 ceqs_attack_lab.py --self-test     (5 unit tests)
  python3 ceqs_attack_lab.py --all           (experiments A-F; --json prints the
                                              report that results/ keeps)

It loads the Mode B revision this record was measured against from the hidden-signers
domain: ../../08-hidden-signers/history/hidden-signer-mode-b-v1.50.py, which in turn
loads the v1.46 base module from the same directory. Companion documents in this
domain: docs/attack-lab.md (what each experiment asserts), docs/validation-status.md
(what this does and does not establish) and results/attack-lab-results.md (the
recorded run).

Scope. The system under test is the CURRENT stack, not the superseded one:
  B0        public-signer certificate (domain 07, src/sidecar_free_certificate.py)
  Mode B    hidden-signer certificate (domain 08; the v1.50 revision pinned above,
            and the production prover history/mode-b-prover-v1.50.c)
The SLH-DSA/QLWR/"Adv < 2^-128 for every QPT adversary" construction of the old
report was refuted (domain 06, src/qpt128_finalization.py, Lemma L1) and replaced;
there is nothing left to test there.

What this file does, and what it cannot do.
  CAN: run the real implementation through violation attempts and count successes
       (must be zero); build deliberately weak parameter sets and measure how the
       real attacks scale on them; simulate Grover EXACTLY on the real oracle at
       those sizes; compare measured exponents with the ledger's predictions.
  CANNOT: establish 128-bit quantum security. No simulation can. The quantum rows
       below are the proven Grover/BHT bounds evaluated at a marked-set density
       that is MEASURED on the real function, which is the honest half of the
       claim; the other half is the reduction, in domain 08's docs/mode-b-security.md.

Experiments
  A  Negative tests (--negative): 21 violation attempts against Mode B v1.50 at
     toy parameters; every one must be rejected.
  B  Framing scaling (--framing): for n = 8..14 bits of opening, enumerate the
     whole search space of the real key map, measure the marked-set size M (how
     many openings satisfy both the registry key and the handle) and the classical
     search cost, for the r^7 handle, the linear handle and no handle.
  C  Grover simulation (--grover): exact state-vector simulation of Grover's
     algorithm on the real oracle from B (numpy), measured success probability per
     iteration against sin^2((2k+1)*arcsin(sqrt(M/N))), and the measured optimal
     iteration count against (pi/4)*sqrt(N/M).
  D  Collision scaling (--collision): run the real linear-trick attack on the real
     key map for expansion E = 2..12 and measure the number of deltas tried
     (predicted 2^E), i.e. the density that the quantum bound 2^(E/2) is applied to.
  E  Challenge-collision fix (--challenge): reproduce the attack the independent
     cryptanalysis found against the v1.46 handle (a challenge collision silences
     extraction) and show it fails against the v1.50 linearized handle.
  F  Ledger (--ledger): measured exponents vs the predicted ones, and the
     extrapolation to production parameters.

--all runs A-F. --self-test runs a fast subset as unit tests.
Toy parameters are DELIBERATELY WEAK (8-14 bit openings). No result here is a
security claim for the production parameters.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import struct
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


# v1.50 loads v1.46 itself and registers it as 'modeB46'; load v1.50 FIRST and
# then take that same instance, so the lab and the implementation share one copy
# of ModeBError (two copies would make every `except ModeBError` miss).
# The path pins the revision this record was measured against: the hidden-signers
# domain keeps the superseded Mode B v1.50 unchanged in its history/ directory.
m50 = _load('modeB50', '../../08-hidden-signers/history/hidden-signer-mode-b-v1.50.py')
m46 = sys.modules['modeB46']

N_SEATS, QUORUM, MIN_OVERLAP = m46.N_SEATS, m46.QUORUM, m46.MIN_OVERLAP
ModeBError = m46.ModeBError

# n must not be a multiple of 3, else 7 | 2^n - 1 and r^7 is not a permutation.
SAFE_N = (8, 10, 11, 13, 14, 16, 17)


def digest64(x):
    return hashlib.shake_256(repr(x).encode()).digest(64)


# ===========================================================================
# A. Negative tests against the real Mode B v1.50 implementation.
# ===========================================================================
def negative_tests(n=14, expansion=8, seed=1151, verbose=True):
    p = m46.make_params(n=n, expansion=expansion, seed=b'lab/neg')
    d0, d1 = bytes(range(64)), bytes(range(1, 65))
    seats0 = list(range(QUORUM))
    seats1 = list(range(MIN_OVERLAP)) + list(range(QUORUM, N_SEATS))
    m0, m1 = digest64('m0'), digest64('m1')
    # At toy handle widths, 43 handles collide with birthday probability
    # 1 - exp(-43*42/2/2^n) (45% at n=11, 5.6% at n=14); the implementation
    # refuses to encode such a certificate, so redraw the openings when it does.
    for attempt in range(32):
        rng = random.Random(seed + attempt)
        registry, secrets = m46.build_registry(p, b'lab-epoch', (d0, d1), rng)
        cfg = m46.cfg_of(registry, p)
        try:
            f0 = m50.encode(p, registry, secrets, d0, m0, seats0)
            f1 = m50.encode(p, registry, secrets, d0, m1, seats1)
            break
        except ModeBError:
            continue
    else:
        raise RuntimeError('no collision-free toy instance in 32 attempts; raise n')
    hb = p.handle_bytes
    HDR = m46.HEADER_BYTES

    def rows_of(frame, domain, seats, message):
        ch = m50.Challenge(p, cfg, domain, message)
        by = {m50.handle(p, ch, secrets[domain][i]): i for i in seats}
        return [(by[z],) + secrets[domain][by[z]] for z in m50.parse(p, frame).handles]

    rows0 = rows_of(f0, d0, seats0, m0)
    results = []

    def check(name, fn):
        """fn must raise ModeBError (or return False) for the attempt to count as
        correctly rejected."""
        try:
            outcome = fn()
            rejected = outcome is False
            detail = 'accepted' if not rejected else 'returned False'
        except ModeBError as exc:
            rejected, detail = True, str(exc)[:60]
        except (struct.error, ValueError, KeyError, IndexError) as exc:
            rejected, detail = True, type(exc).__name__
        results.append({'test': name, 'rejected': rejected, 'detail': detail})
        if verbose:
            print(('  PASS  ' if rejected else '  VIOLATION  ') + name + '   [' + detail + ']')
        return rejected

    # --- forged / invalid witnesses -------------------------------------
    def t_forged_opening():
        bad = list(rows0)
        i, s, r = bad[0]
        bad[0] = (i, s ^ 1, r)
        return m50.check_relation(p, registry, m50.parse(p, f0), bad)
    check('forged opening (s altered) rejected by the relation', t_forged_opening)

    def t_unregistered_credential():
        bad = list(rows0)
        i, s, r = bad[0]
        bad[0] = (i, rng.getrandbits(n), rng.getrandbits(n))
        return m50.check_relation(p, registry, m50.parse(p, f0), bad)
    check('unregistered credential rejected', t_unregistered_credential)

    def t_wrong_seat_label():
        bad = list(rows0)
        i, s, r = bad[0]
        bad[0] = ((i + 1) % N_SEATS, s, r)
        return m50.check_relation(p, registry, m50.parse(p, f0), bad)
    check('opening claimed under another seat rejected', t_wrong_seat_label)

    def t_duplicate_seat():
        bad = list(rows0)
        bad[1] = (rows0[0][0],) + rows0[1][1:]
        return m50.check_relation(p, registry, m50.parse(p, f0), bad)
    check('duplicate validator in the witness rejected', t_duplicate_seat)

    def t_wrong_message():
        return m50.check_relation(p, registry, m50.parse(p, f1), rows0)
    check('witness replayed under another message rejected', t_wrong_message)

    def t_wrong_domain():
        g = m50.encode(p, registry, secrets, d1, m0, seats0)
        return m50.check_relation(p, registry, m50.parse(p, g), rows0)
    check('witness replayed in another domain rejected', t_wrong_domain)

    def t_short_witness():
        return m50.check_relation(p, registry, m50.parse(p, f0), rows0[:-1])
    check('witness with fewer than 43 rows rejected', t_short_witness)

    # --- malformed encodings --------------------------------------------
    def t_unsorted():
        body = bytearray(f0)
        a, b = HDR, HDR + hb
        body[a:b], body[b:b + hb] = body[b:b + hb], body[a:b]
        return m50.parse(p, bytes(body))
    check('handles out of canonical order rejected', t_unsorted)

    def t_duplicate_handle():
        body = bytearray(f0)
        body[HDR + hb:HDR + 2 * hb] = body[HDR:HDR + hb]
        return m50.parse(p, bytes(body))
    check('duplicate handle rejected', t_duplicate_handle)

    check('truncated frame rejected', lambda: m50.parse(p, f0[:-1]))
    check('frame with trailing bytes rejected', lambda: m50.parse(p, f0 + b'\x00'))

    def t_bad_magic():
        return m50.parse(p, b'XXXX' + f0[4:])
    check('wrong magic rejected', t_bad_magic)

    def t_bad_version():
        body = bytearray(f0)
        struct.pack_into('>H', body, 4, 49)
        return m50.parse(p, bytes(body))
    check('wrong version rejected', t_bad_version)

    def t_bad_suite():
        body = bytearray(f0)
        struct.pack_into('>H', body, 6, 0x46B0)
        return m50.parse(p, bytes(body))
    check('wrong suite rejected', t_bad_suite)

    def t_bad_count():
        body = bytearray(f0)
        struct.pack_into('>H', body, 200, QUORUM - 1)
        return m50.parse(p, bytes(body))
    check('quorum count below 43 rejected', t_bad_count)

    def t_short_message():
        return m50.encode(p, registry, secrets, d0, b'short', seats0)
    check('non-canonical (non-64-byte) message rejected', t_short_message)

    def t_dup_registration():
        keys = list(registry.keys[d0])
        keys[1] = keys[0]
        bad = m46.Registry(registry.epoch, registry.domains, {d0: tuple(keys), d1: registry.keys[d1]})
        return m50.encode(p, bad, secrets, d0, m0, seats0)
    check('duplicate registration rejected', t_dup_registration)

    # --- extraction preconditions ---------------------------------------
    check('replay of the same certificate is not a conflict',
          lambda: m50.extract(p, registry, f0, f0))

    def t_equal_messages():
        g = m50.encode(p, registry, secrets, d0, m0, seats1)
        return m50.extract(p, registry, f0, g)
    check('equal messages are not a conflict', t_equal_messages)

    def t_cross_domain():
        g = m50.encode(p, registry, secrets, d1, m1, seats1)
        return m50.extract(p, registry, f0, g)
    check('conflict across different domains rejected', t_cross_domain)

    def t_cross_config():
        other, other_secrets = m46.build_registry(p, b'other-epoch', (d0,), random.Random(99))
        g = m50.encode(p, other, other_secrets, d0, m1, seats1)
        return m50.extract(p, registry, f0, g)
    check('certificate from another registry rejected', t_cross_config)

    # --- framing and blame ----------------------------------------------
    def t_framing():
        """An adversary that does not hold seat 0's opening builds a conflicting
        certificate; extraction must not name seat 0."""
        alt = list(range(1, QUORUM + 1))
        g = m50.encode(p, registry, secrets, d0, m1, alt)
        res = m50.extract(p, registry, f0, g)
        return 0 not in res['seats']          # True means the framing failed
    ok = t_framing()
    results.append({'test': 'framing an honest seat fails', 'rejected': ok, 'detail': 'seat 0 not named'})
    if verbose:
        print(('  PASS  ' if ok else '  VIOLATION  ') + 'framing an honest seat fails')

    def t_fabricated_blame():
        res = m50.extract(p, registry, f0, f1)
        b = res['blames'][0]
        fake = m46.Blame(b.seat, b.position0, b.position1, b.s ^ 1, b.r)
        return m50.verify_blame(p, registry, f0, f1, fake)
    check('fabricated blame fails public verification', t_fabricated_blame)

    # --- the positive control: honest extraction must still work ---------
    res = m50.extract(p, registry, f0, f1)
    honest_ok = (res['seats'] == list(range(MIN_OVERLAP)) and res['complete']
                 and all(m50.verify_blame(p, registry, f0, f1, b) for b in res['blames']))
    results.append({'test': 'positive control: honest conflict extracts 22 seats',
                    'rejected': honest_ok, 'detail': 'extracted %d' % len(res['seats'])})
    if verbose:
        print(('  PASS  ' if honest_ok else '  FAILURE  ') + 'positive control: 22 seats extracted')

    violations = [r['test'] for r in results if not r['rejected']]
    return {'parameters': {'n': n, 'expansion': expansion, 'seats': N_SEATS, 'quorum': QUORUM},
            'attempts': len(results), 'violations': violations,
            'successful_violations': len(violations), 'results': results}


# ===========================================================================
# B. Framing scaling: enumerate the real search space at weak parameters.
# ===========================================================================
def _framing_instance(p, registry, secrets, domain, message, seat, handle_kind):
    """Return (Y, Z, apply, unapply) for one honest target."""
    f = p.field
    s, r = secrets[domain][seat]
    Y = registry.keys[domain][seat]
    cfg = m46.cfg_of(registry, p)
    if handle_kind == 'power':                      # Mode B: Z = r^7 + L_c(s)
        ch = m50.Challenge(p, cfg, domain, message)
        Z = f.G(r) ^ ch.apply(s)
        return Y, Z, (lambda rr: ch.invert(Z ^ f.G(rr)))
    if handle_kind == 'linear':                     # Mode A: Z = r + c*s
        c = m46.challenge(p, cfg, domain, message)
        ci = f.inv(c)
        Z = r ^ f.mul(c, s)
        return Y, Z, (lambda rr: f.mul(Z ^ rr, ci))
    if handle_kind == 'none':                       # no handle published
        return Y, None, None
    raise ValueError(handle_kind)


def framing_scaling(ns=(8, 10, 11, 13, 14), expansion=8, targets=6, kinds=('power', 'linear'),
                    verbose=True):
    """For each n, enumerate every candidate r and count how many give a valid
    opening of the target key. Records the marked-set size M and the position of
    the true opening (the classical search cost for that target)."""
    out = []
    for n in ns:
        p = m46.make_params(n=n, expansion=expansion, seed=b'lab/frame')
        rng = random.Random(4000 + n)
        d0 = bytes(range(64))
        registry, secrets = m46.build_registry(p, b'lab-epoch', (d0,), rng)
        space = 1 << n
        for kind in kinds:
            marks, positions, t0 = [], [], time.time()
            for t in range(targets):
                seat = t
                message = digest64(('frame', n, kind, t))
                Y, Z, derive = _framing_instance(p, registry, secrets, d0, message, seat, kind)
                true_s, true_r = secrets[d0][seat]
                marked = []
                for rr in range(space):
                    s2 = derive(rr)
                    if p.keymap.to_bytes(p.keymap.evaluate(m46.opening_to_input(p, s2, rr))) == Y:
                        marked.append(rr)
                marks.append(len(marked))
                positions.append(true_r + 1)          # 1-based classical search cost
                assert true_r in marked, 'true opening not marked'
            row = {'n': n, 'handle': kind, 'space': space, 'targets': targets,
                   'marked_sizes': marks, 'mean_marked': sum(marks) / len(marks),
                   'mean_classical_cost': sum(positions) / len(positions),
                   'predicted_classical_cost': space / 2,
                   'grover_optimal_iterations': round(math.pi / 4 * math.sqrt(space / max(1, marks[0]))),
                   'seconds': round(time.time() - t0, 1)}
            out.append(row)
            if verbose:
                print('  n=%2d %-6s space=2^%d  M=%s  classical mean %.0f (pred %.0f)  %.1fs'
                      % (n, kind, n, marks, row['mean_classical_cost'],
                         row['predicted_classical_cost'], row['seconds']))
    return out


def no_handle_baseline(n=8, expansion=8, targets=3, verbose=True):
    """Control for experiment B. Without a published handle the attacker must
    search (s, r) jointly: 2^(2n) candidates instead of 2^n. Enumerates the whole
    joint space, so only the smallest n is practical."""
    p = m46.make_params(n=n, expansion=expansion, seed=b'lab/base')
    rng = random.Random(5000 + n)
    d0 = bytes(range(64))
    registry, secrets = m46.build_registry(p, b'lab-epoch', (d0,), rng)
    space = 1 << (2 * n)
    marks, t0 = [], time.time()
    for t in range(targets):
        Y = registry.keys[d0][t]
        found = 0
        for s2 in range(1 << n):
            for r2 in range(1 << n):
                if p.keymap.to_bytes(p.keymap.evaluate(m46.opening_to_input(p, s2, r2))) == Y:
                    found += 1
        marks.append(found)
    row = {'n': n, 'joint_space': space, 'log2_joint_space': 2 * n,
           'log2_space_with_handle': n, 'marked_sizes': marks,
           'predicted_classical_cost_no_handle': space / 2,
           'predicted_classical_cost_with_handle': (1 << n) / 2,
           'seconds': round(time.time() - t0, 1)}
    if verbose:
        print('  n=%d  no handle: space 2^%d, M=%s   with handle: space 2^%d'
              '   -> the handle costs the defender n bits of search space  (%.1fs)'
              % (n, 2 * n, marks, n, row['seconds']))
    return row


# ===========================================================================
# C. Exact Grover simulation on the real oracle.
# ===========================================================================
def grover_simulation(ns=(8, 10, 11, 13), expansion=8, handle_kind='power', verbose=True):
    """State-vector simulation (numpy). The oracle is the REAL key map + handle:
    a candidate r is marked iff it yields a valid opening of the target key.
    This simulates the algorithm exactly; it does not model the gate cost of
    implementing the oracle as a circuit."""
    import numpy as np
    out = []
    for n in ns:
        p = m46.make_params(n=n, expansion=expansion, seed=b'lab/grover')
        rng = random.Random(7000 + n)
        d0 = bytes(range(64))
        registry, secrets = m46.build_registry(p, b'lab-epoch', (d0,), rng)
        space = 1 << n
        message = digest64(('grover', n))
        Y, Z, derive = _framing_instance(p, registry, secrets, d0, message, 0, handle_kind)
        t0 = time.time()
        marked = np.zeros(space, dtype=bool)
        for rr in range(space):
            s2 = derive(rr)
            if p.keymap.to_bytes(p.keymap.evaluate(m46.opening_to_input(p, s2, rr))) == Y:
                marked[rr] = True
        M = int(marked.sum())
        phase = np.where(marked, -1.0, 1.0)
        psi = np.full(space, 1.0 / math.sqrt(space))
        theta = math.asin(math.sqrt(M / space))
        k_opt = round((math.pi / 2 - theta) / (2 * theta))
        k_max = min(int(2.5 * k_opt) + 2, 4000)
        probs, theory, best = [], [], (0.0, 0)
        for k in range(k_max + 1):
            pr = float((psi[marked] ** 2).sum())
            th = math.sin((2 * k + 1) * theta) ** 2
            probs.append(pr)
            theory.append(th)
            if pr > best[0]:
                best = (pr, k)
            psi = psi * phase
            psi = 2.0 * psi.mean() - psi
        err = max(abs(a - b) for a, b in zip(probs, theory))
        row = {'n': n, 'space': space, 'marked': M, 'theta': theta,
               'predicted_optimal_iterations': k_opt,
               'measured_optimal_iterations': best[1],
               'measured_success_at_optimum': round(best[0], 6),
               'theory_success_at_optimum': round(math.sin((2 * k_opt + 1) * theta) ** 2, 6),
               'max_abs_deviation_from_theory': err,
               'pi_over_4_sqrt_N_over_M': round(math.pi / 4 * math.sqrt(space / M), 1),
               'seconds': round(time.time() - t0, 1)}
        out.append(row)
        if verbose:
            print('  n=%2d N=2^%d M=%d  k*: measured %d vs predicted %d (pi/4 sqrt(N/M)=%.1f)  '
                  'p=%.4f  max|sim-theory|=%.2e  %.1fs'
                  % (n, n, M, best[1], k_opt, row['pi_over_4_sqrt_N_over_M'], best[0], err,
                     row['seconds']))
    return out


# ===========================================================================
# D. Collision scaling on the real key map (the binding assumption).
# ===========================================================================
def collision_scaling(N=16, expansions=(2, 4, 6, 8, 10, 12), trials=8, cap=400000, verbose=True):
    """Run the real linear-trick attack: pick delta, solve the linear system
    F(x+delta)+F(x)=0, keep the first consistent one. Measures the number of
    deltas tried, whose expectation is 2^E."""
    out = []
    for E in expansions:
        counts, t0 = [], time.time()
        for t in range(trials):
            q = m46.QuadMap(N, N + E, b'lab/coll/%d/%d' % (E, t))
            rng = random.Random(900 + 17 * E + t)
            tried = 0
            found = None
            while tried < cap:
                delta = rng.getrandbits(N) or 1
                tried += 1
                x = q.collision_for_delta(delta)
                if x is not None and q.evaluate(x) == q.evaluate(x ^ delta) and delta != 0:
                    found = (x, delta)
                    break
            counts.append(tried if found else None)
        good = [c for c in counts if c is not None]
        row = {'N_unknowns': N, 'expansion': E, 'trials': trials,
               'deltas_tried': counts,
               'mean_deltas_tried': (sum(good) / len(good)) if good else None,
               'predicted_mean_2^E': 2 ** E,
               'measured_log2': round(math.log2(sum(good) / len(good)), 2) if good else None,
               'quantum_bound_2^(E/2)': 2 ** (E / 2),
               'seconds': round(time.time() - t0, 1)}
        out.append(row)
        if verbose:
            print('  E=%2d  deltas tried %s  mean %s (pred 2^%d=%d)  log2 %s  %.1fs'
                  % (E, counts, row['mean_deltas_tried'], E, 2 ** E, row['measured_log2'],
                     row['seconds']))
    return out


# ===========================================================================
# E. The challenge-collision attack, before and after the v1.50 fix.
# ===========================================================================
def challenge_fix(n=14, expansion=8, max_messages=4000, verbose=True):
    """The independent cryptanalysis found that in the v1.46 handle Z = r^7 + c*s,
    two messages with c(m0) = c(m1) make extraction divide by zero and name nobody.
    Reproduce it, then run the SAME colliding messages against the v1.50 handle
    Z = r^7 + c_a s + c_b s^2 + c_c s^4, where suppression needs all three
    coefficients to collide."""
    p = m46.make_params(n=n, expansion=expansion, seed=b'lab/chal')
    d0 = bytes(range(64))
    seats0 = list(range(QUORUM))
    seats1 = list(range(MIN_OVERLAP)) + list(range(QUORUM, N_SEATS))
    for attempt in range(32):                 # redraw on a toy-size handle collision
        rng = random.Random(31337 + attempt)
        registry, secrets = m46.build_registry(p, b'lab-epoch', (d0,), rng)
        cfg = m46.cfg_of(registry, p)
        try:
            m50.encode(p, registry, secrets, d0, digest64('probe'), seats0)
            m46.encode(p, registry, secrets, d0, digest64('probe'), seats0)
            break
        except ModeBError:
            continue
    else:
        raise RuntimeError('no collision-free toy instance in 32 attempts; raise n')

    # --- birthday search on the v1.46 single challenge -------------------
    seen, pair46, tries46 = {}, None, 0
    for k in range(max_messages):
        msg = digest64(('chal', k))
        tries46 += 1
        c = m46.challenge(p, cfg, d0, msg)
        if c in seen and seen[c] != msg:
            pair46 = (seen[c], msg)
            break
        seen[c] = msg
    # --- birthday search on the v1.50 FIRST coefficient only -------------
    seen_a, pair_a, tries_a = {}, None, 0
    for k in range(max_messages):
        msg = digest64(('chalA', k))
        tries_a += 1
        a = m50.Challenge(p, cfg, d0, msg).a
        if a in seen_a and seen_a[a] != msg:
            pair_a = (seen_a[a], msg)
            break
        seen_a[a] = msg

    result = {'field_bits': n, 'birthday_predicted_tries': round(math.sqrt(math.pi / 2 * 2 ** n), 1),
              'v1.46_challenge_collision_found_after': tries46 if pair46 else None,
              'v1.50_first_coefficient_collision_found_after': tries_a if pair_a else None}

    # --- v1.46 behaviour on its colliding pair ---------------------------
    if pair46:
        m_a, m_b = pair46
        try:
            g0 = m46.encode(p, registry, secrets, d0, m_a, seats0)
            g1 = m46.encode(p, registry, secrets, d0, m_b, seats1)
        except ModeBError:
            pair46 = None
    if pair46:
        same_handles = sum(1 for h in m46.parse(p, g0).handles if h in set(m46.parse(p, g1).handles))
        try:
            blames = m46.extract(p, registry, g0, g1)
            result['v1.46_extraction'] = 'named %d seats' % len(blames)
            result['v1.46_broken'] = False
        except ModeBError as exc:
            result['v1.46_extraction'] = 'FAILED: ' + str(exc)[:50]
            result['v1.46_broken'] = True
        result['v1.46_identical_handles_across_the_two_certificates'] = same_handles
    # --- v1.50 behaviour on a first-coefficient collision -----------------
    if pair_a:
        m_a, m_b = pair_a
        ca, cb = m50.Challenge(p, cfg, d0, m_a), m50.Challenge(p, cfg, d0, m_b)
        result['v1.50_coefficients_equal'] = {'c_a': ca.a == cb.a, 'c_b': ca.b == cb.b,
                                              'c_c': ca.c == cb.c}
        try:
            h0 = m50.encode(p, registry, secrets, d0, m_a, seats0)
            h1 = m50.encode(p, registry, secrets, d0, m_b, seats1)
        except ModeBError:
            pair_a = None
    if pair_a:
        try:
            res = m50.extract(p, registry, h0, h1)
            result['v1.50_extraction'] = 'named %d seats' % len(res['seats'])
            result['v1.50_survives'] = (res['seats'] == list(range(MIN_OVERLAP)))
        except ModeBError as exc:
            result['v1.50_extraction'] = 'FAILED: ' + str(exc)[:50]
            result['v1.50_survives'] = False
    result['work_to_suppress_v1.50'] = 'collision on all three coefficients: 3n = %d bits' % (3 * n)
    if verbose:
        print('  v1.46: challenge collision after %s messages -> extraction %s'
              % (result.get('v1.46_challenge_collision_found_after'), result.get('v1.46_extraction')))
        print('  v1.50: first-coefficient collision after %s messages -> extraction %s'
              % (result.get('v1.50_first_coefficient_collision_found_after'),
                 result.get('v1.50_extraction')))
    return result


# ===========================================================================
# F. Ledger: measured vs predicted, and the extrapolation.
# ===========================================================================
def fit_slope(xs, ys):
    nn = len(xs)
    mx, my = sum(xs) / nn, sum(ys) / nn
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else float('nan')


def ledger(framing_rows, grover_rows, collision_rows):
    power = [r for r in framing_rows if r['handle'] == 'power']
    xs = [r['n'] for r in power]
    ys = [math.log2(r['mean_classical_cost']) for r in power]
    slope_classical = fit_slope(xs, ys) if len(xs) > 1 else float('nan')
    gx = [r['n'] for r in grover_rows]
    gy = [math.log2(max(1, r['measured_optimal_iterations'])) for r in grover_rows]
    slope_quantum = fit_slope(gx, gy) if len(gx) > 1 else float('nan')
    cx = [r['expansion'] for r in collision_rows if r['measured_log2'] is not None]
    cy = [r['measured_log2'] for r in collision_rows if r['measured_log2'] is not None]
    slope_collision = fit_slope(cx, cy) if len(cx) > 1 else float('nan')
    return {
        'framing_classical': {'measured_slope_bits_per_bit': round(slope_classical, 3),
                              'predicted_slope': 1.0,
                              'extrapolation_n256_log2': 255.0},
        'framing_quantum_grover': {'measured_slope_bits_per_bit': round(slope_quantum, 3),
                                   'predicted_slope': 0.5,
                                   'extrapolation_n256_log2': 128.0,
                                   'note': 'iterations; gate cost not modelled'},
        'binding_collision_classical': {'measured_slope_bits_per_expansion_bit': round(slope_collision, 3),
                                        'predicted_slope': 1.0,
                                        'extrapolation_E512_log2': 512.0},
        'binding_collision_quantum': {'predicted_log2_at_E512': 256.0,
                                      'basis': 'Grover over delta at the measured density 2^-E'},
        'production_rows_from_the_ledger': {
            'R1_framing_log2_Pr_over_G': -145.0, 'R2_binding': -209.0,
            'R3_proof_soundness': -138.1, 'R4_simulation': -159.4,
            # corrected in v1.52: the dominant false-positive path is a handle
            # coincidence (42*43/2^256), not a registry-key coincidence (-943).
            'R5_false_positive': -181.2,
            'total': -137.7, 'D2_margin_bits': 7.7},
        'caveat': 'Toy parameters. Measured exponents test the SCALING of the real '
                  'attacks, not the production security level.'}


# ===========================================================================
# Runner.
# ===========================================================================
def run_all(verbose=True):
    report = {'module': 'ceqs_attack_lab'}
    if verbose:
        print('\nA. Negative tests (Mode B v1.50, n=14):')
    report['A_negative'] = negative_tests(verbose=verbose)
    if verbose:
        print('\nB. Framing scaling (real key map, full enumeration):')
    report['B_framing'] = framing_scaling(verbose=verbose)
    if verbose:
        print('\nB2. No-handle baseline (joint (s,r) enumeration):')
    report['B2_no_handle_baseline'] = no_handle_baseline(verbose=verbose)
    if verbose:
        print('\nC. Grover simulation (exact state vector, real oracle):')
    report['C_grover'] = grover_simulation(verbose=verbose)
    if verbose:
        print('\nD. Collision scaling (real linear-trick attack):')
    report['D_collision'] = collision_scaling(verbose=verbose)
    if verbose:
        print('\nE. Challenge-collision attack, v1.46 vs v1.50:')
    report['E_challenge_fix'] = challenge_fix(verbose=verbose)
    report['F_ledger'] = ledger(report['B_framing'], report['C_grover'], report['D_collision'])
    if verbose:
        print('\nF. Ledger:')
        print(json.dumps(report['F_ledger'], indent=2))
        print('\nSuccessful violations: %d of %d attempts'
              % (report['A_negative']['successful_violations'], report['A_negative']['attempts']))
    return report


class LabTests(unittest.TestCase):
    def test_no_violations(self):
        r = negative_tests(n=14, expansion=8, verbose=False)
        self.assertEqual(r['successful_violations'], 0, r['violations'])
        self.assertGreaterEqual(r['attempts'], 20)

    def test_marked_set_is_the_true_opening_only(self):
        rows = framing_scaling(ns=(8, 10), targets=2, kinds=('power',), verbose=False)
        for row in rows:
            self.assertEqual(row['marked_sizes'], [1] * row['targets'])

    def test_grover_matches_theory(self):
        rows = grover_simulation(ns=(8, 10), verbose=False)
        for row in rows:
            self.assertLess(row['max_abs_deviation_from_theory'], 1e-9)
            self.assertLessEqual(abs(row['measured_optimal_iterations']
                                     - row['predicted_optimal_iterations']), 1)

    def test_collision_density(self):
        rows = collision_scaling(expansions=(2, 4, 6), trials=3, verbose=False)
        for row in rows:
            self.assertIsNotNone(row['mean_deltas_tried'])
            self.assertLess(abs(row['measured_log2'] - row['expansion']), 2.0)

    def test_challenge_fix(self):
        r = challenge_fix(n=14, verbose=False)
        self.assertTrue(r['v1.46_broken'])
        self.assertTrue(r['v1.50_survives'])
        self.assertTrue(r['v1.50_coefficients_equal']['c_a'])
        self.assertFalse(r['v1.50_coefficients_equal']['c_b'])


def main(argv=None):
    ap = argparse.ArgumentParser(description='CE-QS attack lab (v1.51).')
    g = ap.add_mutually_exclusive_group(required=True)
    for flag in ('all', 'negative', 'framing', 'baseline', 'grover', 'collision', 'challenge',
                 'self-test'):
        g.add_argument('--' + flag, action='store_true')
    ap.add_argument('--json', action='store_true', help='print the JSON report only')
    a = ap.parse_args(argv)
    verbose = not a.json
    if a.self_test:
        r = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(LabTests))
        return 0 if r.wasSuccessful() else 1
    if a.all:
        rep = run_all(verbose=verbose)
    elif a.negative:
        rep = negative_tests(verbose=verbose)
    elif a.framing:
        rep = framing_scaling(verbose=verbose)
    elif a.baseline:
        rep = no_handle_baseline(verbose=verbose)
    elif a.grover:
        rep = grover_simulation(verbose=verbose)
    elif a.collision:
        rep = collision_scaling(verbose=verbose)
    else:
        rep = challenge_fix(verbose=verbose)
    if a.json:
        print(json.dumps(rep, indent=2, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
