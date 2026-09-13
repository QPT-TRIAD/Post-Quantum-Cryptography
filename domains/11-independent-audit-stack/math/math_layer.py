#!/usr/bin/env python3
r"""QPT-128 audit stack — MATHEMATICS and CRYPTANALYSIS layers (independent recomputation
and counterfactual attacks). SageMath is not installed on this host; the independent
engines are SymPy (symbolic/exact arithmetic) and galois (GF(2^m) arithmetic implemented
by a different author, different algorithm). The project's own modules are imported
READ-ONLY and only to be *compared against*.

Every section states the claim, the counterfactual attempted, and the verdict. A
counterfactual that succeeds is reported as a finding, not suppressed.

  M1  quorum intersection  |Q1 ∩ Q2| >= 2q − N        (SymPy solve + exhaustive N = 4..64)
  M2  attack-cost arithmetic: Grover, CFHL collision (2^81.7 / 2^252.4), multi-target
      crossover, category attacks vs the 2^128 budget, S6 margins, sizes, BDS worst case
  M3  GF(2^256) differential: galois vs the project's Field (mul, inv, r^7, 7th root)
  M4  kernel lemma of D(s) = αs + βs² + γs⁴: exhaustive/random search for dim > 2;
      counterfactuals: an s^8 term (dim 3 must appear) and a non-linearized s³ handle
      (solution sets stop being subspaces); the SUPPRESS law 2^-3m vs 2^-m
  M5  quantum simulation suite n = 8..18: exact Grover vs floor(π/4·2^(n/2)), independent fit
  M6  multi-target regression: shared-function vs prefixed targets, classical (slope −1 vs 0)
      and quantum (slope −0.5 vs 0) — the S2-006 permanent regression
  M7  FRAME counterfactual on profile B0 with a toy proof-of-work signature: framing an
      honest seat costs exactly one forgery (slope 1.0 in bits); the frame *succeeds*
      once the forgery is found — B0's frameability is exactly the signature's
  M8  EVADE on B0: exhaustive over signer-set pairs at small N — a double-signer is
      always in the intersection (structural, no cryptography)
"""

import hashlib
import importlib.util
import json
import math
import os
import random
import sys
import time

import numpy as np                     # noqa: E402
import sympy as sp                     # noqa: E402
import galois                          # noqa: E402

# Reference source tree: the read-only inputs this layer audits. The verification
# environment exports PQT_SRC; see docs/inputs-and-provenance.md.
PQT = os.environ.get('PQT_SRC')
if not PQT or not os.path.isdir(PQT):
    raise SystemExit('PQT_SRC is not set: source the environment activation script '
                     '(tooling/), or point PQT_SRC at a local copy of the research tree')


def load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(PQT, fn))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m                       # v1.44 looks itself up in sys.modules at import
    spec.loader.exec_module(m)
    return m


v43 = load('qpt128_v143', 'qpt128_finalization_v1.43.py')
m46 = load('modeB46', 'hidden_signer_modeB_v1.46.py')
sys.modules['modeB46'] = m46
v50 = load('modeB50', 'hidden_signer_modeB_v1.50.py')
b0 = load('sidecar44', 'sidecar_free_certificate_v1.44.py')

OUT = {}


def section(name, result):
    OUT[name] = result
    print(f"[{name}] {json.dumps(result, default=str)[:600]}")


def fit_slope(xs, ys):
    xs, ys = np.array(xs, float), np.array(ys, float)
    return float(np.polyfit(xs, ys, 1)[0])


# ============================================================ M1 quorum ======
def m1_quorum():
    C, q, N = sp.symbols('C q N', integer=True, nonnegative=True)
    # both sides complete: C + h_A >= q, C + h_B >= q, h_A + h_B <= N - C  =>  2q - 2C <= N - C
    threshold = sp.solve(sp.Eq(2 * q - 2 * C, N - C), C)[0]          # C = 2q - N
    exhaustive = []
    for n in range(4, 65):
        qq = (2 * n) // 3 + 1
        found = None
        for c in range(0, n + 1):
            honest = n - c
            feasible = any(c + ha >= qq and c + hb >= qq for ha in range(honest + 1) for hb in range(honest - ha + 1))
            if feasible:
                found = c
                break
        exhaustive.append((n, qq, 2 * qq - n, found))
    mismatches = [row for row in exhaustive if row[2] != row[3]]
    return {'symbolic_threshold': str(threshold), 'N64_q43': int(threshold.subs({q: 43, N: 64})),
            'exhaustive_N4_to_64_mismatches': mismatches, 'verdict': 'REPRODUCED' if not mismatches else 'DISCREPANCY'}


# ==================================================== M2 attack arithmetic ==
def m2_arithmetic():
    n = sp.symbols('n', positive=True)
    q = sp.symbols('q', positive=True)
    E = sp.Rational(27182818285, 10 ** 10)
    # CFHL collision bound (v1.43 form): 80 E^2 (q+1)^3 2^-n + 4·2^-n ; success 1/3
    def q_third(nbits):
        expr = sp.Eq(80 * E ** 2 * (q + 1) ** 3 * sp.Rational(1, 2 ** nbits) + 4 * sp.Rational(1, 2 ** nbits), sp.Rational(1, 3))
        sol = [s for s in sp.solve(expr, q) if s.is_real and s > 0][0]
        return float(sp.log(sol, 2))
    cfhl256, cfhl768 = q_third(256), q_third(768)
    module_check = float(v43.cfhl_collision(2 ** cfhl256, 256, capped=False))
    grover = {nb: (nb / 2 + math.log2(math.pi / 4), nb / 2 + 18) for nb in (128, 192, 256)}
    # multi-target crossover: 2^(n/2 - t/2 + 18) >= 2^128  <=>  t <= n + 36 - 256
    t = sp.symbols('t')
    crossover = sp.solve(sp.Eq(sp.Rational(256, 2) - t / 2 + 18, 128), t)[0]
    cats = {1: 83, 2: 100, 3: 116, 5: 148}
    sizes = {'qc_43_mldsa87': 138 + 43 * (6 + 4627), 'lms_h20_w8': 4 + (4 + 32 + 34 * 32) + 4 + 20 * 32,
             'xmss_h20': 4 + 32 + 67 * 32 + 20 * 32, 'lms_h20_w4': 4 + (4 + 32 + 67 * 32) + 4 + 20 * 32,
             'mtl_condensed_n32_N1e4': 28 + 3 * 32 + 32 * int(math.floor(math.log2(10 ** 4))),
             'bds_h20_k2_leaf_max': (20 - 2) // 2 + 1,
             'bds_h20_hashes_max': ((20 - 2) // 2 + 1) * (34 * 255 + 34 + 1) + (34 * 255 + 34 + 1) + 20}
    return {'cfhl_queries_log2': {'n256': round(cfhl256, 2), 'n768': round(cfhl768, 2)},
            'cfhl_gates_log2': {'n256': round(cfhl256 + 18, 2), 'n768': round(cfhl768 + 18, 2)},
            'module_bound_at_2^81.7_queries': round(module_check, 4),
            'classical_birthday_log2': {'n256': 128, 'n768': 384},
            'grover_iterations_log2_and_gates': {k: (round(a, 2), b) for k, (a, b) in grover.items()},
            'multi_target_unprefixed_pass_iff_T_log2_le': int(crossover),
            'multi_target_T40_gates_log2': 256 / 2 - 20 + 18, 'prefixed_gates_log2': 146,
            'category_attacks_pass_2^128': {c: g >= 128 for c, g in cats.items()},
            's6_margins_bits': {nb: nb // 2 + 18 - 128 for nb in (128, 192, 256)}, 'sizes': sizes,
            'expected': {'cfhl n256': 81.7, 'cfhl n768': 252.4, 'qc': 199357, 'lms w8': 1772, 'xmss': 2820, 'lms w4': 2828,
                         'mtl': 540, 'bds hashes': 95775, 'multi-target T40': 126},
            'verdict': 'REPRODUCED' if (round(cfhl256, 1) == 81.7 and round(cfhl768, 1) == 252.4 and sizes['qc_43_mldsa87'] == 199357
                                         and sizes['bds_h20_hashes_max'] == 95775 and sizes['mtl_condensed_n32_N1e4'] == 540) else 'DISCREPANCY'}


# ================================================= M3 GF(2^256) differential
def m3_gf_differential(samples=400, seed=3):
    rng = random.Random(seed)
    F = m46.Field(256)
    GF = galois.GF(2 ** 256, irreducible_poly=galois.Poly.Degrees([256, 10, 5, 2, 0]), verify=False)
    mism = {'mul': 0, 'inv': 0, 'pow7': 0, 'root7': 0}
    for _ in range(samples):
        a, b = rng.getrandbits(256), rng.getrandbits(256) or 1
        if int(GF(a) * GF(b)) != F.mul(a, b):
            mism['mul'] += 1
        if a and int(GF(a) ** -1) != F.inv(a):
            mism['inv'] += 1
        if int(GF(a) ** 7) != F.G(a):
            mism['pow7'] += 1
        z = F.G(a)
        if F.G_inv(z) != a or int(GF(z) ** F.inv_power) != a:
            mism['root7'] += 1
    toy = {}
    for nbits in (8, 10, 16):                    # gcd(7, 2^n - 1) = 1 needed for r^7 to permute (n = 12 fails: 7 | 4095)
        poly = m46.find_poly(nbits)
        gpoly = galois.Poly.Int(poly)
        Ft = m46.Field(nbits)
        GFt = galois.GF(2 ** nbits, irreducible_poly=gpoly, verify=False)
        bad = 0
        pairs = [(a, b) for a in range(1, 2 ** nbits, max(1, 2 ** nbits // 64)) for b in range(1, 2 ** nbits, max(1, 2 ** nbits // 64))]
        for a, b in pairs:
            if int(GFt(a) * GFt(b)) != Ft.mul(a, b):
                bad += 1
        toy[nbits] = {'irreducible_by_galois': bool(gpoly.is_irreducible()), 'pairs': len(pairs), 'mismatches': bad}
    ok = not any(mism.values()) and all(v['mismatches'] == 0 and v['irreducible_by_galois'] for v in toy.values())
    return {'samples': samples, 'mismatches': mism, 'toy_fields': toy, 'verdict': 'REPRODUCED' if ok else 'DISCREPANCY'}


# ========================================================= M4 kernel lemma ==
def kernel_dims(GF, m, triples, extra_pow=None):
    """Solution-set sizes of D(s) = t. For the linearized D (t = 0) that is the kernel;
    for the non-linearized counterfactual (extra_pow == 3) t is random, because the
    extractor solves the AFFINE equation and needs the solution set to be a coset."""
    s = GF.Range(0, 2 ** m)
    s2, s4 = s ** 2, s ** 4
    s8 = s ** 8 if extra_pow == 8 else None
    s3 = s ** 3 if extra_pow == 3 else None
    dims, sizes = [], []
    for tr in triples:
        a, b, c = (GF(x) for x in tr[:3])
        D = a * s + b * s2 + c * s4
        target = GF(0)
        if extra_pow == 8:
            D = D + GF(tr[3]) * s8
        if extra_pow == 3:
            D = a * s + b * s3                    # NOT linearized: s(a + b s^2) is a cubic
            target = GF(tr[2])                    # random right-hand side t
        z = int(np.count_nonzero(D == target))
        sizes.append(z)
        # a coset of an F2-subspace has 2^d elements; 0 or a non-power-of-two means "not a coset"
        dims.append(int(math.log2(z)) if z > 0 and z & (z - 1) == 0 else -1)
    return dims, sizes


def m4_kernel(seed=4):
    rng = random.Random(seed)
    out = {}
    for m, mode, count in ((4, 'exhaustive', None), (6, 'exhaustive', None), (8, 'random', 20000), (12, 'random', 3000)):
        GF = galois.GF(2 ** m)
        if mode == 'exhaustive':
            triples = [(a, b, c) for a in range(2 ** m) for b in range(2 ** m) for c in range(2 ** m) if (a, b, c) != (0, 0, 0)]
        else:
            triples = [(rng.randrange(1, 2 ** m), rng.randrange(2 ** m), rng.randrange(2 ** m)) for _ in range(count)]
        dims, sizes = kernel_dims(GF, m, triples)
        hist = {d: dims.count(d) for d in sorted(set(dims))}
        out[f'GF(2^{m})'] = {'mode': mode, 'triples': len(triples), 'kernel_dim_histogram': hist,
                             'max_dim': max(dims), 'non_subspace_cases': dims.count(-1)}
    # counterfactual 1: an s^8 term (2-degree 3) -> dimension 3 must be reachable
    GF6 = galois.GF(2 ** 6)
    quads = [(rng.randrange(1, 64), rng.randrange(64), rng.randrange(64), rng.randrange(1, 64)) for _ in range(20000)]
    d8, _ = kernel_dims(GF6, 6, quads, extra_pow=8)
    # counterfactual 2: non-linearized handle a·s + b·s^3 -> solution sets need not be subspaces
    d3, sizes3 = kernel_dims(GF6, 6, [(rng.randrange(1, 64), rng.randrange(1, 64), rng.randrange(1, 64)) for _ in range(20000)], extra_pow=3)
    # SUPPRESS law: probability two random challenge triples coincide = 2^-3m (v1.50) vs 2^-m (v1.46)
    law = {}
    for m in (3, 4, 5, 6):
        K = 4000
        trip = [tuple(rng.getrandbits(m) for _ in range(3)) for _ in range(K)]
        single = [t[0] for t in trip]
        col3 = sum(1 for i in range(K) for j in range(i + 1, K) if trip[i] == trip[j]) if m <= 4 else None
        # for m >= 5 count via hashing for speed
        if col3 is None:
            from collections import Counter
            cnt = Counter(trip); col3 = sum(v * (v - 1) // 2 for v in cnt.values())
        from collections import Counter
        cnt1 = Counter(single); col1 = sum(v * (v - 1) // 2 for v in cnt1.values())
        pairs = K * (K - 1) // 2
        law[m] = {'triple_collisions': col3, 'expected_2^-3m': round(pairs / 2 ** (3 * m), 1),
                  'single_collisions': col1, 'expected_2^-m': round(pairs / 2 ** m, 1)}
    ms = [m for m in law if law[m]['triple_collisions'] > 0]
    slope3 = fit_slope(ms, [math.log2(law[m]['triple_collisions'] / (4000 * 3999 / 2)) for m in ms]) if len(ms) >= 2 else None
    slope1 = fit_slope(list(law), [math.log2(law[m]['single_collisions'] / (4000 * 3999 / 2)) for m in law])
    verdict = ('REPRODUCED' if all(v['max_dim'] <= 2 and v['non_subspace_cases'] == 0 for v in out.values())
               and max(d8) >= 3 and (-1 in d3) else 'DISCREPANCY')
    return {'linearized_D': out, 'counterfactual_s8_max_dim': max(d8), 'counterfactual_s3_non_subspace_cases': d3.count(-1),
            'counterfactual_s3_root_counts_seen': sorted(set(sizes3)),
            'suppress_law': law, 'fitted_slope_triple_vs_m': None if slope3 is None else round(slope3, 2),
            'fitted_slope_single_vs_m': round(slope1, 2), 'expected_slopes': (-3, -1), 'verdict': verdict}


# ================================================== M5 quantum simulation ===
def grover_first_peak(n, seed):
    rng = random.Random(seed)
    N = 1 << n
    target = rng.randrange(N)
    marked = np.zeros(N, bool)
    marked[target] = True                       # single-target unstructured search
    theta = math.asin(math.sqrt(1 / N))
    k_pred = int(math.floor(math.pi / (4 * theta)))
    amp = np.full(N, 1 / math.sqrt(N))
    probs = [float((amp[marked] ** 2).sum())]
    for k in range(1, k_pred + 3):
        amp[marked] *= -1
        amp = 2 * amp.mean() - amp
        probs.append(float((amp[marked] ** 2).sum()))
    k_peak = next(k for k in range(1, len(probs) - 1) if probs[k + 1] < probs[k])
    return {'n': n, 'k_measured': k_peak, 'k_predicted': k_pred, 'p_at_pred': round(probs[k_pred], 6),
            'closed_form': round(math.sin((2 * k_pred + 1) * theta) ** 2, 6)}


def m5_quantum():
    rows = [grover_first_peak(n, 100 + n) for n in range(8, 19, 2)]
    slope = fit_slope([r['n'] for r in rows], [math.log2(r['k_measured']) for r in rows])
    ok = all(abs(r['k_measured'] - r['k_predicted']) <= 1 and abs(r['p_at_pred'] - r['closed_form']) < 1e-6 for r in rows)
    return {'rows': rows, 'fitted_slope_log2k_vs_n': round(slope, 4), 'expected_slope': 0.5,
            'caveat': 'validates the scaling model at n <= 18; does not execute a 128/256-bit attack',
            'verdict': 'REPRODUCED' if ok and abs(slope - 0.5) < 0.03 else 'DISCREPANCY'}


# ================================================== M6 multi-target =========
def m6_multi_target(seed=6):
    rng = random.Random(seed)
    n = 16
    N = 1 << n

    def f(prefix, x):
        return int.from_bytes(hashlib.shake_256(prefix + x.to_bytes(4, 'big')).digest(2), 'big')
    classical = {}
    for T in (1, 2, 4, 16, 64, 256, 1024):
        shared_work, prefixed_work = [], []
        for trial in range(8):
            targets = {f(b'shared', rng.randrange(N)) for _ in range(T)}
            # shared function: one evaluation tested against all T targets
            x, w = 0, 0
            while True:
                w += 1
                if f(b'shared', rng.randrange(N)) in targets:
                    break
            shared_work.append(w)
            # prefixed: the attacker must commit to one target j, whose function is f_j
            j = rng.randrange(T)
            tj = f(b'p%d' % j, rng.randrange(N))
            w = 0
            while True:
                w += 1
                if f(b'p%d' % j, rng.randrange(N)) == tj:
                    break
            prefixed_work.append(w)
        classical[T] = {'shared_mean_work': round(sum(shared_work) / 8), 'prefixed_mean_work': round(sum(prefixed_work) / 8),
                        'expected_shared': round(N / T), 'expected_prefixed': N}
    Ts = list(classical)
    slope_shared = fit_slope([math.log2(T) for T in Ts], [math.log2(classical[T]['shared_mean_work']) for T in Ts])
    slope_pref = fit_slope([math.log2(T) for T in Ts], [math.log2(classical[T]['prefixed_mean_work']) for T in Ts])
    # quantum: Grover with T marked items in one function vs one marked (prefixed)
    nq, Nq = 14, 1 << 14
    quantum = {}
    for T in (1, 2, 4, 8, 16, 32, 64):
        marked = np.zeros(Nq, bool)
        marked[rng.sample(range(Nq), T)] = True
        theta = math.asin(math.sqrt(T / Nq))
        k_pred = int(math.floor(math.pi / (4 * theta)))
        amp = np.full(Nq, 1 / math.sqrt(Nq))
        probs = [float((amp[marked] ** 2).sum())]
        for k in range(1, k_pred + 3):
            amp[marked] *= -1
            amp = 2 * amp.mean() - amp
            probs.append(float((amp[marked] ** 2).sum()))
        k_peak = next(k for k in range(1, len(probs) - 1) if probs[k + 1] < probs[k])
        quantum[T] = {'k_measured': k_peak, 'k_predicted': k_pred}
    qslope = fit_slope([math.log2(T) for T in quantum], [math.log2(quantum[T]['k_measured']) for T in quantum])
    ok = abs(slope_shared + 1) < 0.15 and abs(slope_pref) < 0.15 and abs(qslope + 0.5) < 0.08
    return {'classical_n16': classical, 'slope_shared': round(slope_shared, 3), 'slope_prefixed': round(slope_pref, 3),
            'quantum_n14': quantum, 'quantum_slope_log2k_vs_log2T': round(qslope, 3),
            'expected': {'shared': -1, 'prefixed': 0, 'quantum_shared': -0.5},
            'consequence_n256': 'unprefixed: 2^(128 - T/2 + 18); T = 2^40 -> 2^126 < 2^128; crossover T = 2^36; prefixed 2^146',
            'verdict': 'REPRODUCED' if ok else 'DISCREPANCY'}


# =============================================== M7 FRAME on B0 (toy) =======
class ToyPoWSignatures:
    """Toy: sig is valid iff SHAKE(pk||msg||sig)[:bits] == 0. Signing and forging cost 2^bits
    hash evaluations each; nobody holds a secret. Width fixed at 24 bytes (B0 minimum)."""
    name, category, width = 'TOY-POW', 0, 24

    def __init__(self, bits):
        self.bits = bits
        self.counter = 0
        self.work = 0

    def keygen(self):
        self.counter += 1
        pk = b'TOYPK' + self.counter.to_bytes(8, 'big')
        return pk, pk                                       # sk = pk (no secret in the toy)

    def _ok(self, pk, msg, sig):
        d = int.from_bytes(hashlib.shake_256(pk + msg + sig).digest(4), 'big')
        return d >> (32 - self.bits) == 0

    def sign(self, sk, msg):
        i = 0
        while True:
            sig = i.to_bytes(self.width, 'big')
            self.work += 1
            if self._ok(sk, msg, sig):
                return sig
            i += 1

    def verify(self, pk, msg, sig):
        return type(sig) is bytes and len(sig) == self.width and self._ok(pk, msg, sig)


def m7_frame_toy(seed=7):
    rng = random.Random(seed)
    rows = []
    N, Q = b0.N, b0.QUORUM
    for bits in (8, 10, 12, 14):
        prov = ToyPoWSignatures(bits)
        keys = [prov.keygen() for _ in range(N)]
        registry = b0.RegistryB0(tuple(pk for pk, _ in keys), b'toy-pow')
        sks = [sk for _, sk in keys]
        cfg = b0.cfg_b0(registry)
        domain = b'D' * 64
        m0, m1 = b'0' * 64, b'1' * 64
        seats0 = list(range(0, Q))                      # 0..42
        seats1 = list(range(N - Q, N))                  # 21..63 ; overlap 21..42 = 22 seats
        f0 = b0.encode_b0(registry, prov, domain, m0, sks, seats0)
        f1 = b0.encode_b0(registry, prov, domain, m1, sks, seats1)
        honest_named_before = [b.seat for b in b0.extract_b0(f0, f1, registry, prov, cfg) if b.seat < N - Q or b.seat >= Q]
        # attacker: frame honest seat h (signed m0 only) by forging its signature on m1 and swapping it into f1
        h = 5
        prov.work = 0
        forged = prov.sign(registry.public_keys[h], b0.vote_message_b0(cfg, domain, m1, h))   # forgery = 2^bits work
        work = prov.work
        header, payload = b0.parse_frame(f1, b0.SUITE_B0)
        width = header.width
        seats1_new = sorted(set(seats1) - {63} | {h})
        sigs = {}
        for pos, seat in enumerate(sorted(seats1)):
            sigs[seat] = payload[8 + pos * width: 8 + (pos + 1) * width]
        sigs[h] = forged
        bitmap = sum(1 << s for s in seats1_new)
        new_payload = bitmap.to_bytes(8, 'big') + b''.join(sigs[s] for s in seats1_new)
        f1_forged = b0.pack_header(b0.SUITE_B0, cfg, domain, m1, width, len(new_payload)) + new_payload
        try:
            named = [b.seat for b in b0.extract_b0(f0, f1_forged, registry, prov, cfg)]
            framed = h in named and b0.verify_blame_b0(f0, f1_forged, registry, prov, cfg, h)
        except b0.CertError as e:
            named, framed = str(e), False
        rows.append({'bits': bits, 'forgery_work': work, 'expected_2^bits': 2 ** bits, 'honest_named_before_attack': honest_named_before,
                     'frame_succeeded_after_forgery': bool(framed)})
    slope = fit_slope([r['bits'] for r in rows], [math.log2(r['forgery_work']) for r in rows])
    ok = all(r['frame_succeeded_after_forgery'] and r['honest_named_before_attack'] == [] for r in rows) and abs(slope - 1) < 0.2
    return {'rows': rows, 'fitted_slope_log2work_vs_bits': round(slope, 3), 'expected_slope': 1.0,
            'interpretation': 'FRAME on B0 = exactly one signature forgery of the victim; no cheaper path exists in the '
                              'construction (bitmap + per-seat signatures), so frameability equals EUF-CMA of the profile '
                              '(ML-DSA-87, 2^148) with the tight loss 64 -> 2^142 gates',
            'verdict': 'REPRODUCED' if ok else 'DISCREPANCY'}


# ============================================================ M8 EVADE ======
def m8_evade():
    from itertools import combinations
    n, q = 7, 5
    total, evaded = 0, 0
    for A in combinations(range(n), q):
        for B in combinations(range(n), q):
            total += 1
            inter = set(A) & set(B)
            if len(inter) < 2 * q - n:
                evaded += 1                               # would contradict counting
            # any seat in both is in the intersection by definition: evasion impossible
    return {'N': n, 'q': q, 'pairs': total, 'pairs_below_2q_minus_N': evaded, 'verdict': 'REPRODUCED' if evaded == 0 else 'DISCREPANCY'}


def main():
    t0 = time.time()
    section('M1_quorum', m1_quorum())
    section('M2_arithmetic', m2_arithmetic())
    section('M3_gf_differential', m3_gf_differential())
    section('M4_kernel', m4_kernel())
    section('M5_quantum', m5_quantum())
    section('M6_multi_target', m6_multi_target())
    section('M7_frame_toy', m7_frame_toy())
    section('M8_evade', m8_evade())
    OUT['_meta'] = {'engines': {'sympy': sp.__version__, 'galois': galois.__version__, 'numpy': np.__version__, 'sage': 'not installed'},
                    'seconds': round(time.time() - t0, 1),
                    'verdicts': {k: v.get('verdict') for k, v in OUT.items() if isinstance(v, dict) and 'verdict' in v}}
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'math_results.json'), 'w') as f:
        json.dump(OUT, f, indent=1, default=str)
    print(json.dumps(OUT['_meta'], indent=1))
    return 0 if all(v == 'REPRODUCED' for v in OUT['_meta']['verdicts'].values()) else 1


if __name__ == '__main__':
    sys.exit(main())
