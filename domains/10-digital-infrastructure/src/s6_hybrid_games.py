#!/usr/bin/env python3
r"""PQ infrastructure program — audit S6 v2.1: security games on the S6 hybrid /
migration toy models.  Read-only consumer of pq_infra_s6_migration_agility_v2.0
(ToyKEM, combine, migration_ledger) and pq_infra_s4_embedded_broadcast_v2.0
(WOTS, qpt128_hash_preimage_ok).  Nothing in either module is modified.

Every game is an executable experiment on the toy model.  The report states, per
game, the adversary's capabilities, its oracle access, the winning condition, the
number of trials, the wins, the bound the game should obey, the mechanism that
enforces it and the assumption the bound rests on.  Where a bound is MEASURED
the secret is truncated to n bits (n in 8..16) so the 2^-n scaling is visible at
2,048 trials per point and can be fitted (slope of log2 rate vs n).

  A  classical component fully compromised -> IND game on the combined key
  B  PQ component compromised (mirror of A, classical secret truncated)
  C  correlated randomness between the two components -> NEGATIVE result
  D  TLS group downgrade with / without transcript binding (+ quantum caveat)
  E  ROM root configuration substitution: typecode, prefix compare, rollback
  F  agility ledger + exact QPT-128 gate margins
  composition: union bound is only defined inside ONE game (documented refusal)

A seeded random.Random supplies the honest parties' coins in the toy (including
ToyKEM's, via _seeded) so every number below is reproducible run to run; it is
not a security RNG and is not meant as one.
"""

import argparse, contextlib, functools, hashlib, hmac, importlib.util, json, math, os, random, sys, unittest

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fn))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


s6 = _load('s6', 's6_migration_agility.py')
s4 = _load('s4', 's4_embedded_broadcast.py')
ToyKEM, combine = s6.ToyKEM, s6.combine


@contextlib.contextmanager
def _seeded(rng):
    """Route s6.ToyKEM's `secrets.token_bytes` to the game's seeded PRNG for the
    duration of one game (swapped in and out; the source module is not modified)
    so every game is reproducible.  Only the honest parties' coins are affected;
    no adversary strategy reads it."""
    saved, s6.secrets = s6.secrets, type('_Secrets', (), {'token_bytes': staticmethod(rng.randbytes)})
    try:
        yield rng
    finally:
        s6.secrets = saved


N_BITS = (8, 10, 12, 14, 16)      # truncated-secret sizes for the measured games
TRIALS = 2048                     # >= 2,000 trials per measured point
QUERIES = 64                      # combiner (random-oracle) queries per IND trial
LABEL = b'X25519MLKEM1024'


def _fit_slope(pts):
    """Ordinary least squares slope of y on x for [(x, y), ...]."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


# ------------------------------------------------- Games A / B: IND-combined-key
@functools.lru_cache(maxsize=None)
def game_ab(compromised):
    """IND game on K = combine(label, ss_pq, ss_cl, ct_cl, pk_cl).
    Challenger flips b; b=0 -> K_real, b=1 -> uniform 32 bytes.  The adversary
    holds EVERYTHING of the compromised component (its sk, ss, ct, pk) plus the
    label, ct_cl, pk_cl; the other component's shared secret is truncated to n
    bits and is its only unknown.  It may evaluate the combiner QUERIES times
    (distinct guesses) and outputs b'.  Difference lemma: Adv <= Pr[some query
    hits the real secret] = Q/2^n.  Both the raw IND wins and the hit event are
    recorded; the hit rate in the real world (b=0) is what is fitted vs n."""
    rng = random.Random(0x5601 if compromised == 'classical' else 0x5602)
    rows, pts = [], []
    with _seeded(rng):
        pq, cl = ToyKEM(b'mlkem'), ToyKEM(b'x25519', broken=(compromised == 'classical'))
        for n in N_BITS:
            space, ind_wins, hits, real = 2 ** n, 0, 0, 0
            for _ in range(TRIALS):
                ct_cl, ss_cl, _r = cl.encaps(cl.pk)
                ss_pq = pq.encaps(pq.pk)[1]
                sec = rng.getrandbits(n).to_bytes(2, 'big')
                if compromised == 'classical':
                    ss_pq = sec                # adversary knows ss_cl; n-bit ss_pq is the unknown
                else:
                    ss_cl = sec                # adversary knows ss_pq; n-bit ss_cl is the unknown
                k_real = combine(LABEL, ss_pq, ss_cl, ct_cl, cl.pk)
                b = rng.getrandbits(1)
                k_chal = k_real if b == 0 else rng.randbytes(32)
                guesses = (g.to_bytes(2, 'big') for g in rng.sample(range(space), min(QUERIES, space)))
                hit = any((combine(LABEL, gb, ss_cl, ct_cl, cl.pk) if compromised == 'classical'
                           else combine(LABEL, ss_pq, gb, ct_cl, cl.pk)) == k_chal for gb in guesses)   # stops at first hit
                b_out = 0 if hit else rng.getrandbits(1)
                ind_wins += b_out == b
                real += b == 0
                hits += hit and b == 0
            rate = hits / real
            rows.append({'n_bits': n, 'trials': TRIALS, 'real_world_trials': real, 'query_hits': hits,
                         'hit_rate': rate, 'bound_Q_over_2n': QUERIES / space, 'ind_wins': ind_wins,
                         'ind_advantage_est': 2 * ind_wins / TRIALS - 1})
            if hits >= 6:
                pts.append((n, math.log2(rate)))
    slope = _fit_slope(pts) if len(pts) >= 3 else None
    return {'queries_per_trial': QUERIES, 'rows': rows, 'fit_points': len(pts),
            'fitted_slope_log2_rate_vs_n': slope, 'expected_slope': -1.0}


# ------------------------------------------------- Game C: correlated components
@functools.lru_cache(maxsize=None)
def game_c():
    """NEGATIVE RESULT.  Both encapsulations draw their randomness from ONE
    n_seed-bit seed (shared DRBG state / shared entropy pool).  The adversary sees
    only public data (pk_cl, ct_cl), precomputes the table seed -> ct_cl once, and
    recovers K exactly although the PQ component is never 'broken'.  The combiner
    theorem (Giacon-Heuer-Poettering 2018; X-Wing 2024) assumes the two
    components are independent; combine() cannot restore independence that the
    implementation never had.  Recorded as a failure the combiner does not cover."""
    rows = []
    for n_seed in (8, 12, 16):
        rng = random.Random(0x5603 + n_seed)
        with _seeded(rng):
            pq, cl = ToyKEM(b'mlkem'), ToyKEM(b'x25519')

        def enc(kem, seed):     # ToyKEM.encaps with its randomness derived from the shared seed
            r = hashlib.sha3_256(b'drbg' + kem.tag + seed).digest()
            ct = hashlib.sha3_256(b'ct' + kem.tag + kem.pk + r).digest()
            return ct, hashlib.sha3_256(b'ss' + kem.tag + kem.pk + ct + r).digest()

        table = {enc(cl, s.to_bytes(2, 'big'))[0]: s.to_bytes(2, 'big') for s in range(2 ** n_seed)}
        wins = 0
        for _ in range(TRIALS):
            seed = rng.getrandbits(n_seed).to_bytes(2, 'big')
            _ct_pq, ss_pq = enc(pq, seed)
            ct_cl, ss_cl = enc(cl, seed)
            k = combine(LABEL, ss_pq, ss_cl, ct_cl, cl.pk)
            s_guess = table.get(ct_cl)
            if s_guess is not None:
                wins += combine(LABEL, enc(pq, s_guess)[1], enc(cl, s_guess)[1], ct_cl, cl.pk) == k
        rows.append({'seed_bits': n_seed, 'trials': TRIALS, 'wins': wins, 'win_rate': wins / TRIALS,
                     'adversary_work_hashes_log2': n_seed + 1, 'pq_secret_bits': 256,
                     'bound_if_components_were_independent_log2': n_seed - 256})
    return rows


# ------------------------------------------------- Game D: negotiation downgrade
GROUPS = ('X25519MLKEM1024', 'X25519MLKEM768', 'X25519')
GROUP_CAT = {'X25519MLKEM1024': 5, 'X25519MLKEM768': 3, 'X25519': 0}


def client_hello(rnd, groups):
    body = b''.join(len(g).to_bytes(1, 'big') + g.encode() for g in groups)
    return b'\x01' + rnd + len(groups).to_bytes(1, 'big') + body


def parse_groups(ch):
    out, i = [], 34
    for _ in range(ch[33]):
        out.append(ch[i + 1:i + 1 + ch[i]].decode())
        i += 1 + ch[i]
    return out


def handshake(rng, offer, delete=(), bound=True, tag_bits=256, client_min_cat=0, quantum_forge=False):
    """One TLS-like negotiation.  Client offers `offer`; the MITM deletes the
    groups in `delete` from the ClientHello in transit; the server picks the
    strongest offered group.  Key schedule: bound=True hashes the exact ClientHello
    bytes each side saw (client: as sent; server: as received) into the transcript;
    bound=False omits the offer list.  Returns (client_accepts, chosen_group)."""
    cl, pq = ToyKEM(b'x25519', broken=True), ToyKEM(b'mlkem')
    ch_sent = client_hello(rng.randbytes(32), offer)
    ch_seen = client_hello(ch_sent[1:33], [g for g in offer if g not in delete]) if delete else ch_sent
    chosen = next(g for g in GROUPS if g in parse_groups(ch_seen))
    ct_cl, ss_cl, _ = cl.encaps(cl.pk)
    ss_pq = pq.encaps(pq.pk)[1] if chosen != 'X25519' else b''
    k = combine(chosen.encode(), ss_pq, ss_cl, ct_cl, cl.pk)
    sh = b'\x02' + rng.randbytes(32) + chosen.encode()

    def finished(key, ch):
        th = hashlib.sha3_256((ch if bound else b'') + sh).digest()
        mac = hmac.new(key, b'server finished' + th, hashlib.sha3_256).digest()
        return int.from_bytes(mac, 'big') >> (256 - tag_bits)

    fin = finished(k, ch_seen)                       # what the honest server sends
    if delete and quantum_forge and chosen == 'X25519':
        fin = finished(k, ch_sent)                   # adversary broke X25519 online: knows K, re-MACs
    elif delete and tag_bits < 256:
        fin = rng.getrandbits(tag_bits)              # blind forgery of a t-bit Finished tag
    accept = fin == finished(k, ch_sent) and GROUP_CAT[chosen] >= client_min_cat
    return accept, chosen


@functools.lru_cache(maxsize=None)
def game_d():
    rng = random.Random(0x5604)
    T = 256

    def run(trials=T, **kw):
        w, chosen = 0, None
        with _seeded(rng):
            for _ in range(trials):
                a, chosen = handshake(rng, GROUPS, **kw)
                w += a
        return {'trials': trials, 'client_accepts': w, 'chosen': chosen, 'chosen_cat': GROUP_CAT[chosen],
                'downgrade_wins': w if GROUP_CAT[chosen] < 5 else 0, **{k: str(v) for k, v in kw.items()}}

    rows = {'positive_control_bound_no_mitm': run(),
            'bound_delete_cat5': run(delete=('X25519MLKEM1024',)),
            'UNBOUND_delete_cat5': run(delete=('X25519MLKEM1024',), bound=False),
            'bound_delete_all_pq_quantum_adversary': run(delete=('X25519MLKEM1024', 'X25519MLKEM768'), quantum_forge=True),
            'bound_delete_all_pq_quantum_adversary_client_min_cat3': run(
                delete=('X25519MLKEM1024', 'X25519MLKEM768'), quantum_forge=True, client_min_cat=3)}
    guess, pts = [], []
    for t in (3, 5, 7):          # expected wins 256 / 64 / 16 of 2,048: every point fittable
        r = run(trials=TRIALS, delete=('X25519MLKEM1024',), tag_bits=t)
        r['bound_2^-t'] = 2.0 ** -t
        guess.append(r)
        if r['downgrade_wins'] >= 6:
            pts.append((t, math.log2(r['downgrade_wins'] / TRIALS)))
    return {'variants': rows, 'finished_tag_guessing': guess,
            'fitted_slope_log2_rate_vs_tag_bits': _fit_slope(pts) if len(pts) >= 3 else None}


# ------------------------------------------------- Game E: ROM root substitution
TYPECODES = {0x08: ('LMS_SHA256_M32_H20 / LMOTS w=8 (RFC 8554)', 32, 256),
             0x0D: ('LMS_SHA256_M24_H20 / LMOTS w=8 (SP 800-208, NSA-preferred)', 24, 256),
             0xF0: ('toy M16 w=8', 16, 256),
             0xF1: ('toy M1 w=4 (brute-forceable in the game)', 1, 16)}
LEAVES = 2


class TruncWOTS(s4.WOTS):
    """s4.WOTS with the hash output truncated to n bytes (LMS 'M24' style).
    n=32 reproduces s4.WOTS exactly (checked in S6-014)."""

    def __init__(self, w, n=32):
        super().__init__(w)
        self.n = n
        self.len1 = (8 * n) // self.lg
        self.len2 = math.floor(math.log2(self.len1 * (w - 1)) / self.lg) + 1
        self.len = self.len1 + self.len2

    def _H(self, *parts):
        return s4.H(*parts)[:self.n]

    def chain(self, x, start, steps, ps, addr, i):
        for s in range(start, start + steps):
            x = self._H(b'ch', ps, addr, i.to_bytes(2, 'big'), s.to_bytes(2, 'big'), x)
        return x

    def keygen(self, seed, ps, addr):
        sk = [self._H(b'sk', seed, addr, i.to_bytes(2, 'big')) for i in range(self.len)]
        return sk, self._H(b'pk', ps, addr, *[self.chain(sk[i], 0, self.w - 1, ps, addr, i) for i in range(self.len)])

    def pk_from_sig(self, d, sig, ps, addr):
        dg = self.digits(d)
        return self._H(b'pk', ps, addr, *[self.chain(sig[i], dg[i], self.w - 1 - dg[i], ps, addr, i)
                                          for i in range(self.len)])


def _addr(q):
    return q.to_bytes(4, 'big')


class RootSigner:
    """Manufacturer root under one (typecode, I): LEAVES one-time keys, root = H(leaf pks).
    Signs 'root records' (version || product_root) that a ROM verifier installs."""

    def __init__(self, typecode, seed):
        self.typecode = typecode
        _, n, w = TYPECODES[typecode]
        self.W, self.ps = TruncWOTS(w, n), hashlib.sha3_256(b'I' + seed).digest()[:16]
        self.keys = [self.W.keygen(seed, self.ps, _addr(q)) for q in range(LEAVES)]
        self.root = self.W._H(b'mroot', *[pk for _, pk in self.keys])

    def sign_root_record(self, q, version, product_root):
        payload = version.to_bytes(4, 'big') + product_root
        sig = self.W.sign(self.W._H(b'rec', payload), self.keys[q][0], self.ps, _addr(q))
        return {'typecode': self.typecode, 'ps': self.ps, 'q': q, 'sig': sig,
                'pks': [pk for _, pk in self.keys], 'version': version, 'product_root': product_root}


class RomVerifier:
    """Firmware ROM verifier pinned at manufacture to (typecode, root, version).
    check_typecode=False and full_compare=False are the two failure modes under test:
    the parameter set is then taken from the attacker-supplied record and the root is
    compared only on the first n bytes that those parameters produce."""

    def __init__(self, typecode, root, check_typecode=True, full_compare=True, monotonic=True):
        self.typecode, self.root, self.version = typecode, root, 0
        self.check_typecode, self.full_compare, self.monotonic = check_typecode, full_compare, monotonic

    def verify(self, rec):
        if self.check_typecode and rec['typecode'] != self.typecode:
            return False, 'typecode mismatch'
        if rec['typecode'] not in TYPECODES:
            return False, 'unknown typecode'
        _, n, w = TYPECODES[rec['typecode']]
        W = TruncWOTS(w, n)
        if len(rec['sig']) != W.len or not 0 <= rec['q'] < LEAVES or len(rec['pks']) != LEAVES:
            return False, 'malformed'
        payload = rec['version'].to_bytes(4, 'big') + rec['product_root']
        pks = list(rec['pks'])
        pks[rec['q']] = W.pk_from_sig(W._H(b'rec', payload), rec['sig'], rec['ps'], _addr(rec['q']))
        cand = W._H(b'mroot', *pks)
        if not (cand == self.root if self.full_compare else cand == self.root[:len(cand)]):
            return False, 'root mismatch'
        if self.monotonic and rec['version'] <= self.version:
            return False, 'rollback'
        self.version = rec['version']
        return True, 'accepted'


@functools.lru_cache(maxsize=None)
def game_e():
    rng = random.Random(0x5605)
    mfr = RootSigner(0x08, rng.randbytes(32))
    v1 = mfr.sign_root_record(0, 1, hashlib.sha3_256(b'product-root-v1').digest())
    v2 = mfr.sign_root_record(1, 2, hashlib.sha3_256(b'product-root-v2').digest())
    evil = hashlib.sha3_256(b'adversary product root').digest()
    strict = RomVerifier(0x08, mfr.root)
    out = {'pinned_typecode': '0x08', 'pinned_root_hex': mfr.root.hex(),
           'genuine_v1_strict': strict.verify(v1), 'genuine_v2_strict': strict.verify(v2)}
    # (i)/(ii) substitution under n=24 / n=16 with the adversary's own key set
    sub = {}
    for tc in (0x0D, 0xF0):
        name, n, _w = TYPECODES[tc]
        rec = RootSigner(tc, rng.randbytes(32)).sign_root_record(0, 9, evil)
        sub[hex(tc)] = {'params': name, 'n_bytes': n,
                        'strict_verifier': RomVerifier(0x08, mfr.root).verify(rec),
                        'no_typecode_check_full_compare': RomVerifier(0x08, mfr.root, check_typecode=False).verify(rec),
                        'lax_prefix_verifier': RomVerifier(0x08, mfr.root, False, False).verify(rec),
                        'lax_forgery_cost_classical_log2': 8 * n,
                        'lax_forgery_gates_quantum_log2': 4 * n + int(math.log2(s4.GATES_PER_HASH_QUERY)),
                        'lax_passes_qpt128': 4 * n + int(math.log2(s4.GATES_PER_HASH_QUERY)) >= 128}
    # (ii) executable: with the toy typecode (n=1) the prefix collision is found by brute force
    runs = []
    for _ in range(8):
        tries = 0
        while True:
            tries += 1
            adv = RootSigner(0xF1, rng.randbytes(16))
            if adv.root == mfr.root[:1]:
                break
        rec = adv.sign_root_record(0, 9, evil)
        runs.append({'keygen_trials': tries, 'lax_prefix_verifier': RomVerifier(0x08, mfr.root, False, False).verify(rec),
                     'strict_verifier': RomVerifier(0x08, mfr.root).verify(rec)})
    # (iii) rollback of the root record itself
    mono, nomono = RomVerifier(0x08, mfr.root), RomVerifier(0x08, mfr.root, monotonic=False)
    for v in (mono, nomono):
        v.verify(v1), v.verify(v2)
    out.update({'substitution': sub, 'toy_prefix_bruteforce': runs,
                'toy_prefix_mean_trials': sum(r['keygen_trials'] for r in runs) / len(runs),
                'toy_prefix_expected_trials': 2 ** 8,
                'rollback_replay_v1_monotonic': mono.verify(v1), 'rollback_replay_v1_no_counter': nomono.verify(v1)})
    return out


# ------------------------------------------------- Game F: ledger + gate margins
def gate_margin_log2(n_bits, gates_per_query_log2=18):
    """log2(Grover preimage gates) - 128 for an n-bit hash: 2^(n/2) queries x 2^18 gates."""
    return n_bits // 2 + gates_per_query_log2 - 128


@functools.lru_cache(maxsize=None)
def game_f():
    gpq = int(math.log2(s4.GATES_PER_HASH_QUERY))
    return {'ledger': [{k: r[k] for k in ('layer', 'deployed', 'deployed_passes_qpt128', 'target',
                                          'target_passes_qpt128', 'rotatable_in_field')} for r in s6.migration_ledger()],
            'gates_per_query_log2': gpq,
            'gate_margins': {str(n): {'grover_gates_log2': n // 2 + gpq, 'margin_vs_2^128_log2': gate_margin_log2(n, gpq),
                                      'qpt128_hash_preimage_ok': s4.qpt128_hash_preimage_ok(n)} for n in (128, 192, 256)}}


# ------------------------------------------------- composition
def compose_union_bound(bounds):
    """Union bound over per-layer advantage bounds (log2 values), returned ONLY when
    every bound belongs to the same attacker goal inside one security game.

    Why the refusal: Pr[A or B] <= Pr[A] + Pr[B] is a statement about two events in
    ONE probability space -- one experiment, one adversary, one winning condition.
    'Break this TLS session' = (break the KEM) or (forge the authentication) is such
    a pair: same session, same adversary, so their bounds add.  A DNSSEC forger and
    a firmware forger are different experiments with different adversaries and
    different winning conditions; the sum of their bounds is not the probability of
    any event and answers no question (it is neither the system's failure
    probability nor a per-layer margin).  Independent layers are reported side by
    side -- the weakest link is the max -- and never added.
    Returns (log2_bound, reason) or (None, reason)."""
    if not bounds:
        return None, 'refused: no bounds given'
    goals = sorted({b['goal'] for b in bounds})
    if len(goals) != 1:
        return None, (f'refused: bounds span {len(goals)} attacker goals {goals}; a union bound is only '
                      f'defined for sub-events of one game')
    return math.log2(sum(2.0 ** b['adv_log2'] for b in bounds)), f'union bound over {len(bounds)} sub-events of goal {goals[0]!r}'


# ------------------------------------------------- report
def report():
    A, B, C, D, E, F = game_ab('classical'), game_ab('pq'), game_c(), game_d(), game_e(), game_f()
    ro = 'H (SHA3-256 in combine()) modelled as a random oracle / PRF (GHP18 Thm 3.1; X-Wing 2024)'
    ind = 'independence of the two KEM components (keys, randomness, implementation)'
    games = [
        {'id': 'S6-A', 'game_name': 'IND-combined-key, classical component fully compromised',
         'adversary_capabilities': 'knows sk_cl, ss_cl, ct_cl, pk_cl, label; PQ shared secret truncated to n bits',
         'oracle_access': f'{QUERIES} combiner evaluations per trial (distinct guesses of the n-bit secret)',
         'winning_condition': "b' == b for K_b (b=0: combine(...), b=1: uniform)",
         'trials': sum(r['trials'] for r in A['rows']), 'wins': sum(r['ind_wins'] for r in A['rows']),
         'expected_win_bound': 'IND wins <= 1/2 + Q/2^(n+1); real-world hit rate = Q/2^n (measured, slope vs n fitted)',
         'mechanism': 'combine(): the unknown n-bit ss_pq enters the hash; without it K is a fresh RO output',
         'assumption_invoked': f'{ro}; {ind}', 'measurements': A},
        {'id': 'S6-B', 'game_name': 'IND-combined-key, PQ component compromised',
         'adversary_capabilities': 'knows sk_pq, ss_pq, ct_cl, pk_cl, label; classical shared secret truncated to n bits',
         'oracle_access': f'{QUERIES} combiner evaluations per trial',
         'winning_condition': "b' == b", 'trials': sum(r['trials'] for r in B['rows']),
         'wins': sum(r['ind_wins'] for r in B['rows']), 'expected_win_bound': 'as S6-A with the roles swapped',
         'mechanism': 'combine() is symmetric in which component survives', 'assumption_invoked': f'{ro}; {ind}',
         'measurements': B},
        {'id': 'S6-C', 'game_name': 'NEGATIVE: correlated randomness across the two components',
         'adversary_capabilities': 'public data only (pk_cl, ct_cl); knows both components share one n_seed-bit seed',
         'oracle_access': 'offline: 2^n_seed table seed -> ct_cl; online: one lookup + 4 hashes per trial',
         'winning_condition': 'outputs K exactly', 'trials': sum(r['trials'] for r in C), 'wins': sum(r['wins'] for r in C),
         'expected_win_bound': 'combiner theorem gives Q/2^256 = 2^(n_seed-256) ONLY IF components are independent; '
                               'hypothesis violated -> no bound applies; measured 1.0',
         'mechanism': 'none: the combiner cannot manufacture independence; fix is at the RNG/implementation layer',
         'assumption_invoked': ind + ' -- shown NECESSARY, not just sufficient', 'measurements': C},
        {'id': 'S6-D', 'game_name': 'TLS group downgrade (offer [Cat5, Cat3, classical])',
         'adversary_capabilities': 'MITM edits the ClientHello group list in transit; may guess a t-bit Finished tag; '
                                   'quantum variant: breaks X25519 online and learns ss_cl',
         'oracle_access': 'network only; no key oracle', 'winning_condition': 'client completes with a group weaker than its best offer',
         'trials': sum(v['trials'] for v in D['variants'].values()) + sum(g['trials'] for g in D['finished_tag_guessing']),
         'wins': sum(v['downgrade_wins'] for v in D['variants'].values()) + sum(g['downgrade_wins'] for g in D['finished_tag_guessing']),
         'expected_win_bound': 'bound transcript: 2^-t per Finished guess (t=256 -> 0); unbound: 1 (downgrade succeeds); '
                               'bound + quantum X25519 break: 1 unless client refuses Cat 0 (policy, not binding)',
         'mechanism': 'key schedule hashes the exact ClientHello bytes as sent; Finished = HMAC(K, transcript hash)',
         'assumption_invoked': 'HMAC-SHA3 is a PRF; the negotiated key is unknown to the adversary', 'measurements': D},
        {'id': 'S6-E', 'game_name': 'ROM root configuration substitution / rollback',
         'adversary_capabilities': 'chooses typecode, root record, signature and version; own key sets under n=24, n=16, toy n=1',
         'oracle_access': 'verifier as a black box; unlimited keygen', 'winning_condition': 'verifier installs a root record not signed under the pinned parameter set, or an older one',
         'trials': sum(r['keygen_trials'] for r in E['toy_prefix_bruteforce']),
         'wins': sum(r['lax_prefix_verifier'][0] for r in E['toy_prefix_bruteforce']),
         'expected_win_bound': 'strict: 2^-256 per keygen (Grover 2^128 x 2^18 gates); lax prefix: 2^-(8n) per keygen -> n=24: 2^114 gates, '
                               'n=16: 2^82 gates (both below QPT-128); toy n=1: 2^-8 measured',
         'mechanism': 'pinned typecode checked before parsing; full-length root compare; monotonic root version',
         'assumption_invoked': 'ROM immutability (verifier code and pinned typecode/root/counter cannot be changed); '
                               'second-preimage resistance of the n=32 hash', 'measurements': E},
        {'id': 'S6-F', 'game_name': 'algorithm agility ledger + QPT-128 gate margins',
         'adversary_capabilities': 'reference attacks of the v1.43 ledger; Grover with 2^18 gates per hash query',
         'oracle_access': 'n/a (accounting)', 'winning_condition': 'attack gates < 2^128', 'trials': 0, 'wins': 0,
         'expected_win_bound': 'every target Cat 5; no deployed entry passes; margins n=128: -46, n=192: -14, n=256: +18 bits',
         'mechanism': 'per-layer migration ledger; ROM layer chosen Cat 5 at manufacture because it cannot rotate',
         'assumption_invoked': 'v1.43 gate accounting (2^18 gates/query); category reference attack costs', 'measurements': F}]
    same = [{'layer': 'TLS key exchange', 'goal': 'break TLS session', 'adv_log2': -128},
            {'layer': 'TLS authentication', 'goal': 'break TLS session', 'adv_log2': -128}]
    diff = [{'layer': 'DNSSEC', 'goal': 'forge DNSSEC answer', 'adv_log2': -128},
            {'layer': 'Firmware', 'goal': 'forge firmware root', 'adv_log2': -128}]
    return {'module': os.path.basename(__file__), 'version': '2.1',
            'inputs': ['s6_migration_agility.py', 's4_embedded_broadcast.py'],
            'games': games,
            'composition': {'same_game_tls_session': compose_union_bound(same), 'independent_layers': compose_union_bound(diff),
                            'rule': compose_union_bound.__doc__},
            'untestable_assumptions': [
                {'assumption': 'random-oracle / PRF modelling of the combiner hash (SHA3-256 in combine())',
                 'used_by': ['S6-A', 'S6-B', 'S6-D'],
                 'why_untestable': 'the reduction treats H as a random oracle; no experiment on outputs can separate '
                                   '"SHA3 is a PRF" from "SHA3 is a random oracle" -- the games measure scaling under the model, not the model'},
                {'assumption': 'independence of the two KEM components (key material, randomness, implementation)',
                 'used_by': ['S6-A', 'S6-B'],
                 'why_untestable': 'S6-C shows the bound collapses when violated, but whether a deployment shares a DRBG, '
                                   'entropy pool or code path is a property of the implementation, not of the algorithm'},
                {'assumption': 'ROM immutability: verifier code, pinned typecode, root and version counter cannot be altered',
                 'used_by': ['S6-E', 'S6-F'],
                 'why_untestable': 'a mask-ROM / OTP property of the silicon; software can only assume the verifier runs as written'},
                {'assumption': 'ToyKEM stands in for ML-KEM-1024 / X25519; IND-CCA of ML-KEM (Module-LWE) and the v1.43 category gate costs',
                 'used_by': ['S6-A', 'S6-B', 'S6-D', 'S6-F'],
                 'why_untestable': 'lattice hardness and the reference attack costs are inputs from the QPT-128 ledger, not re-derived'}]}


# ------------------------------------------------- tests
class Tests(unittest.TestCase):
    def _scaling(self, G):
        for r in G['rows']:
            self.assertGreaterEqual(r['trials'], 2000)
            exp = r['bound_Q_over_2n'] * r['real_world_trials']
            self.assertLessEqual(r['query_hits'], exp + 4 * math.sqrt(exp) + 3)             # never beats Q/2^n
            self.assertLess(abs(r['ind_advantage_est']), r['bound_Q_over_2n'] + 4 / math.sqrt(r['trials']))
        self.assertAlmostEqual(G['rows'][0]['hit_rate'], QUERIES / 2 ** 8, delta=0.06)   # n=8 point is tight, not just bounded
        self.assertGreaterEqual(G['fit_points'], 3)
        self.assertTrue(-1.4 <= G['fitted_slope_log2_rate_vs_n'] <= -0.6, G['fitted_slope_log2_rate_vs_n'])

    def test_S6_001_game_a_classical_compromised_scales_as_2_pow_minus_n(self):
        self._scaling(game_ab('classical'))

    def test_S6_002_game_b_pq_compromised_scales_as_2_pow_minus_n(self):
        self._scaling(game_ab('pq'))

    def test_S6_003_game_c_correlated_components_negative_result(self):
        for r in game_c():
            self.assertEqual(r['win_rate'], 1.0)                                    # adversary always recovers K
            self.assertLess(r['bound_if_components_were_independent_log2'], -200)   # bound would be ~0 if the theorem applied

    def test_S6_004_game_d_transcript_binding_detects_deletion(self):
        D = game_d()['variants']
        pc = D['positive_control_bound_no_mitm']
        self.assertEqual((pc['client_accepts'], pc['chosen']), (pc['trials'], 'X25519MLKEM1024'))
        d = D['bound_delete_cat5']
        self.assertEqual((d['chosen'], d['client_accepts'], d['downgrade_wins']), ('X25519MLKEM768', 0, 0))

    def test_S6_005_game_d_unbound_downgrade_succeeds_and_quantum_caveat(self):
        G = game_d()
        u = G['variants']['UNBOUND_delete_cat5']
        self.assertEqual((u['chosen'], u['downgrade_wins']), ('X25519MLKEM768', u['trials']))
        q = G['variants']['bound_delete_all_pq_quantum_adversary']
        self.assertEqual((q['chosen'], q['downgrade_wins']), ('X25519', q['trials']))      # binding alone does not help
        self.assertEqual(G['variants']['bound_delete_all_pq_quantum_adversary_client_min_cat3']['downgrade_wins'], 0)
        for g in G['finished_tag_guessing']:
            exp = g['bound_2^-t'] * g['trials']
            self.assertLessEqual(g['downgrade_wins'], exp + 4 * math.sqrt(exp) + 3)
        self.assertTrue(-1.4 <= G['fitted_slope_log2_rate_vs_tag_bits'] <= -0.6)

    def test_S6_006_game_e_typecode_pinning_rejects_substitution(self):
        E = game_e()
        self.assertEqual(E['genuine_v1_strict'], (True, 'accepted'))
        self.assertEqual(E['genuine_v2_strict'], (True, 'accepted'))
        for tc in ('0xd', '0xf0'):
            self.assertEqual(E['substitution'][tc]['strict_verifier'], (False, 'typecode mismatch'))
            self.assertEqual(E['substitution'][tc]['no_typecode_check_full_compare'], (False, 'root mismatch'))

    def test_S6_007_game_e_lax_prefix_compare_is_the_failure_mode(self):
        E = game_e()
        self.assertEqual(E['substitution']['0xd']['lax_forgery_gates_quantum_log2'], 114)   # n=24 -> below 2^128
        self.assertEqual(E['substitution']['0xf0']['lax_forgery_gates_quantum_log2'], 82)
        self.assertFalse(E['substitution']['0xd']['lax_passes_qpt128'])
        for r in E['toy_prefix_bruteforce']:
            self.assertEqual(r['lax_prefix_verifier'], (True, 'accepted'))         # ACCEPTS the forgery
            self.assertEqual(r['strict_verifier'], (False, 'typecode mismatch'))
        self.assertTrue(64 <= E['toy_prefix_mean_trials'] <= 1024, E['toy_prefix_mean_trials'])   # ~2^8

    def test_S6_008_game_e_root_version_rollback(self):
        E = game_e()
        self.assertEqual(E['rollback_replay_v1_monotonic'], (False, 'rollback'))
        self.assertEqual(E['rollback_replay_v1_no_counter'], (True, 'accepted'))    # failure mode without the counter

    def test_S6_009_game_f_ledger_targets_cat5_deployed_not_passing(self):
        L = game_f()['ledger']
        self.assertEqual(len(L), 6)
        for r in L:
            self.assertTrue(r['target_passes_qpt128'], r['layer'])
            self.assertIsNot(r['deployed_passes_qpt128'], True, r['layer'])
        self.assertTrue(any(r['rotatable_in_field'].startswith('NO') for r in L))

    def test_S6_010_game_f_exact_gate_margins(self):
        self.assertFalse(s4.qpt128_hash_preimage_ok(192))
        self.assertTrue(s4.qpt128_hash_preimage_ok(256))
        m = game_f()['gate_margins']
        self.assertEqual({k: v['margin_vs_2^128_log2'] for k, v in m.items()}, {'128': -46, '192': -14, '256': 18})
        self.assertEqual([v['qpt128_hash_preimage_ok'] for v in m.values()], [False, False, True])

    def test_S6_011_composition_union_bound_same_game(self):
        b, why = compose_union_bound([{'layer': 'TLS KEM', 'goal': 'g', 'adv_log2': -128},
                                      {'layer': 'TLS auth', 'goal': 'g', 'adv_log2': -128}])
        self.assertAlmostEqual(b, -127.0)
        self.assertIn('union bound', why)

    def test_S6_012_composition_refuses_independent_layers(self):
        b, why = compose_union_bound([{'layer': 'DNSSEC', 'goal': 'forge DNSSEC', 'adv_log2': -128},
                                      {'layer': 'Firmware', 'goal': 'forge firmware', 'adv_log2': -128}])
        self.assertIsNone(b)
        self.assertTrue(why.startswith('refused'))
        self.assertIsNone(compose_union_bound([])[0])

    def test_S6_013_report_is_json_with_required_game_fields(self):
        rep = json.loads(json.dumps(report()))
        need = {'id', 'game_name', 'adversary_capabilities', 'oracle_access', 'winning_condition', 'trials', 'wins',
                'expected_win_bound', 'mechanism', 'assumption_invoked'}
        self.assertEqual([g['id'] for g in rep['games']], ['S6-A', 'S6-B', 'S6-C', 'S6-D', 'S6-E', 'S6-F'])
        for g in rep['games']:
            self.assertTrue(need <= set(g), g['id'])
        self.assertEqual(len(rep['untestable_assumptions']), 4)
        self.assertIsNone(rep['composition']['independent_layers'][0])

    def test_S6_014_truncwots_n32_reproduces_s4_wots(self):
        seed, ps, addr = b's' * 32, b'p' * 32, b'\x00\x00\x00\x01'
        d = s4.H(b'firmware blob')
        for w in (16, 256):
            a, b = s4.WOTS(w), TruncWOTS(w, 32)
            (ska, pka), (skb, pkb) = a.keygen(seed, ps, addr), b.keygen(seed, ps, addr)
            self.assertEqual((ska, pka, a.len), (skb, pkb, b.len))
            self.assertEqual(b.pk_from_sig(d, a.sign(d, ska, ps, addr), ps, addr), pka)
        self.assertEqual((TruncWOTS(256, 24).len, TruncWOTS(256, 16).len, TruncWOTS(16, 1).len), (26, 18, 4))


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test', action='store_true')
    g.add_argument('--report', action='store_true')
    a = ap.parse_args(argv)
    if a.report:
        print(json.dumps(report(), indent=2)); return 0
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    return 0 if r.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
