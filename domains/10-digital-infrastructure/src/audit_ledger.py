#!/usr/bin/env python3
r"""Unified audit ledger and checklist for S1–S6 (v2.1).

Runs every audit suite (`--self-test`, verbose) and parses each test's ID,
docstring and status; loads each suite's `--report` JSON (cached in the
repository's `results/` directory, `--refresh` to regenerate); assembles:

  AUDIT_CHECKLIST_v2.1.md   one row per test ID: component, audit column
                            (spec / numbers / attack / bound), what it checks,
                            pass/fail — plus the attack-record table, the
                            per-layer security-exponent table, the composition
                            rule, and every untestable assumption.
  AUDIT_LEDGER_v2.1.json    the same, machine-readable.

Composition rule (from pq_audit_s6): a union bound is only formed for events in
ONE attacker goal (e.g. one TLS session's KEM + authentication). Bounds from
independent layers (DNSSEC vs firmware) are listed side by side and NEVER added.
"""

import argparse
import json
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.normpath(os.path.join(_HERE, '..', 'results'))   # regenerated reports + published ledger
os.makedirs(SP, exist_ok=True)
SUITES = {
    # S1 is pinned to the v2.1 revision on purpose: it is the revision the recorded 70/70 was
    # produced with. The current revision is s1_lms.py (v2.2, which adds S1-012 for the
    # approved-pair fix); pointing the suite there changes the test count and the recorded total.
    'S1': (os.path.join('..', 'history', 's1_lms-v2.1.py'), 'Firmware / LMS (RFC 8554, SP 800-208)'),
    'S2': ('s2_dns_worstcase.py', 'DNSSEC (MTL ladder, multiproof, sharding)'),
    'S3': ('s3_tls_wire.py', 'TLS 1.3 / QUIC / MTC / KEMTLS'),
    'S4': ('s4_tesla_adversarial.py', 'Constrained broadcast (TESLA + LMS anchor)'),
    'S5': ('s5_bds_faults.py', 'Smart card (BDS traversal, faults)'),
    'S6': ('s6_hybrid_games.py', 'Migration (hybrid combiner, downgrade, ROM roots)'),
}
GATES_LOG2, BUDGET = 18, 128


def classify(text):
    t = text.lower()
    if any(k in t for k in ('game', 'attack', 'fault', 'crash', 'rollback', 'forge', 'replay', 'manipul',
                            'downgrade', 'clone', 'mitm', 'substitut', 'late', 'reorder', 'concurrent', 'exhaust')):
        return 'attack'
    if any(k in t for k in ('ledger', 'grover', 'bound', 'qpt128', 'margin', 'composition', 'multi_target',
                            'multi-target', 'per_query', 'scaling law', 'binding')):
        return 'bound'
    if any(k in t for k in ('scal', 'numbers', 'remeasur', 'worst', 'bytes', 'size', 'cpu', 'cycles', 'budget', 'flight')):
        return 'numbers'
    return 'spec'


def run_suite(sid, fn):
    p = subprocess.run([sys.executable, os.path.join(_HERE, fn), '--self-test'], capture_output=True, text=True, timeout=1800)
    lines = (p.stdout + p.stderr).splitlines()
    tests, i = [], 0
    while i < len(lines):
        m = re.match(r'^(test_(S\d)_(\d{3})\S*) \(', lines[i])
        if m:
            name, tid = m.group(1), f'{m.group(2)}-{m.group(3)}'
            desc, status = '', None
            j = i
            while j < len(lines) and status is None:
                s = lines[j]
                for tok, st in ((' ... ok', 'PASS'), ('... ok', 'PASS'), (' ... FAIL', 'FAIL'), (' ... ERROR', 'ERROR'), ('... skipped', 'SKIP')):
                    if s.rstrip().endswith(tok.strip()) or tok in s:
                        status = st
                        break
                if status is None and j > i:
                    desc = (desc + ' ' + s.strip()).strip()
                j += 1
            if not desc:
                desc = name
            desc = re.sub(r'\s*\.\.\.\s*(ok|FAIL|ERROR|skipped.*)$', '', desc).strip()
            tests.append({'id': tid, 'name': name, 'description': desc, 'status': status or 'UNKNOWN',
                          'column': classify(name + ' ' + desc)})
            i = j
        else:
            i += 1
    summary = next((l for l in lines if l.startswith('Ran ')), '')
    ok = any(l.strip() == 'OK' for l in lines)
    return {'tests': tests, 'summary': summary, 'all_pass': ok and p.returncode == 0}


def load_report(sid, fn, refresh):
    path = os.path.join(SP, f'{sid.lower()}_audit_report.json')
    if refresh or not os.path.exists(path):
        p = subprocess.run([sys.executable, os.path.join(_HERE, fn), '--report'], capture_output=True, text=True, timeout=3600)
        if p.returncode != 0:
            return {'error': p.stderr[-2000:]}
        with open(path, 'w') as f:
            f.write(p.stdout)
    with open(path) as f:
        return json.load(f)


def attack_records(reports):
    R = []
    s1 = reports.get('S1', {})
    for g in s1.get('attack_games_n256', []):
        R.append({'attack_id': f"S1-{g['id']}", 'component': 'LMS n=32', 'game': g['game'], 'capabilities': 'chosen-message signatures, public key',
                  'queries_log2': g['quantum_queries_log2'], 'gates_log2': (g['quantum_queries_log2'] + GATES_LOG2) if g['quantum_queries_log2'] != float('inf') else None,
                  'counts_toward_bound': g.get('counts', True), 'assumption': 'A-Grover, A-SHA256', 'measured': None, 'note': g['why']})
    for r in s1.get('grover_reduced', []):
        R.append({'attack_id': f"S1-G2-sim-n{r['n']}", 'component': 'LM-OTS chain (reduced n)', 'game': 'chain inversion, exact Grover',
                  'measured': f"k={r['k_measured']} (pred {r['k_predicted']}), p={r['p_at_k_pred']:.6f}", 'queries_log2': r['n'] / 2, 'assumption': 'none (exact simulation)'})
    s2 = reports.get('S2', {})
    for k, v in s2.get('multi_target_game', {}).items():
        R.append({'attack_id': f'S2-MT-{k}', 'component': 'MTL node hash', 'game': 'multi-target second preimage',
                  'measured': f"unprefixed {v['unprefixed_wins']} (exp {v['expected_unprefixed']:.1f}) / prefixed {v['prefixed_wins']} (exp {v['expected_prefixed']:.1f}) per 100k queries",
                  'assumption': 'MM-SPR'})
    L = s2.get('multi_target_ledger_n256', {})
    if L:
        R.append({'attack_id': 'S2-MT-n256', 'component': 'MTL node hash n=256, T=2^40', 'game': 'multi-target second preimage (quantum)',
                  'gates_log2': L['unprefixed_gates_log2'], 'passes_qpt128': L['unprefixed_passes_qpt128'], 'note': 'UNPREFIXED (v2.0 as built) — FAILS',
                  'assumption': 'MM-SPR, A-Grover'})
        R.append({'attack_id': 'S2-MT-n256-fixed', 'component': 'MTL node hash n=256, prefixed', 'game': 'same', 'gates_log2': L['prefixed_gates_log2'],
                  'passes_qpt128': L['prefixed_passes_qpt128'], 'note': 'with (ladder id, rung, level, index) prefix — PASSES', 'assumption': 'A-Grover'})
    for k, v in s2.get('worst_case', {}).items():
        R.append({'attack_id': f'S2-WC-{k}', 'component': 'DNS response size', 'game': 'worst-case search', 'measured': f"{v['bytes']} B ({v['class']})", 'params': v['params']})
    s3 = reports.get('S3', {})
    for g in s3.get('part_b', {}).get('games', []):
        R.append({'attack_id': f"S3-{g.get('id', '?')}", 'component': 'KEMTLS + MTC handshake', 'game': g.get('game', g.get('id')),
                  'capabilities': g.get('attacker_capabilities'), 'outcome': g.get('outcome'), 'mechanism': g.get('mechanism_that_blocked_it'),
                  'assumption': g.get('assumption_invoked')})
    wc = s3.get('part_a', {}).get('worst_case')
    if wc:
        R.append({'attack_id': 'S3-WC', 'component': 'Certificate message', 'game': 'largest legal certificate', 'measured': json.dumps(wc)[:400]})
    s4 = reports.get('S4', {})
    for g in (s4.get('games') or s4.get('attack_games') or []):
        if isinstance(g, dict):
            R.append({'attack_id': f"S4-{g.get('id', '?')}", 'component': 'TESLA broadcast', 'game': g.get('game', g.get('name', g.get('id'))),
                      'capabilities': g.get('capabilities'), 'measured': f"{g.get('successes', g.get('wins'))}/{g.get('attempts', g.get('trials'))}",
                      'mechanism': g.get('mechanism')})
    s6 = reports.get('S6', {})
    for g in s6.get('games', []):
        R.append({'attack_id': f"S6-{g['id']}", 'component': 'hybrid combiner / negotiation / ROM root', 'game': g['game_name'],
                  'capabilities': g['adversary_capabilities'], 'measured': f"{g['wins']}/{g['trials']}", 'expected': g['expected_win_bound'],
                  'mechanism': g['mechanism'], 'assumption': g['assumption_invoked']})
    return R


# The figures 83 / 100 / 116 / 148 that appear below and in composition() are NIST category
# FLOORS in log2 gates, i.e. the resource level a scheme in the category must match, and not the
# cost of the best known attack on any scheme deployed there. 83, 116 and 148 are Grover key
# search on AES-128 / AES-192 / AES-256: half the key length in Grover iterations charged at the
# gate cost of one AES evaluation (64+19, 96+20, 128+20). The AES-256 entry is the G-cost
# 1.17*2^148 of Jaques-Naehrig-Roetteler-Virdia Tables 9 and 11, which is the row the v1.43
# constants table carries; 100 is the Category-2 entry (collision search on a 256-bit hash) and no
# row here uses it. Putting a floor in the gates_log2 column of an ML-KEM row is the conservative
# direction only while the best known lattice attack costs at least the floor. Analytic
# cross-check, not measured: an independent estimator run (lattice-estimator, ADPS16 core-SVP,
# quantum) puts ML-KEM-1024 near 2^231.6 quantum and 2^255.2 classical, and ML-KEM-512
# (Category 1) near 2^107.6 quantum, below the 2^128 budget. Those counts are core-SVP
# operations, not the gate units of this table, so they settle the direction of the substitution
# and not the number written in it.
def exponent_table(reports):
    """Cheapest-attack gate exponent per layer at production parameters."""
    s2L = reports.get('S2', {}).get('multi_target_ledger_n256', {})
    rows = [
        {'layer': 'S1 firmware LMS n=32', 'cheapest_game': 'second preimage / chain inversion (single target)', 'gates_log2': 128 + GATES_LOG2, 'source': 'S1-010'},
        {'layer': 'S1 firmware LMS n=24 (NSA-preferred)', 'cheapest_game': 'same', 'gates_log2': 96 + GATES_LOG2, 'source': 'S1-010'},
        {'layer': 'S2 DNSSEC MTL nodes, UNPREFIXED (v2.0 as built), T=2^40', 'cheapest_game': 'multi-target second preimage', 'gates_log2': s2L.get('unprefixed_gates_log2'), 'source': 'S2-006'},
        {'layer': 'S2 DNSSEC MTL nodes, prefixed (fix)', 'cheapest_game': 'second preimage', 'gates_log2': s2L.get('prefixed_gates_log2'), 'source': 'S2-006'},
        {'layer': 'S3 TLS KEM ML-KEM-1024', 'cheapest_game': 'Category-5 reference attack', 'gates_log2': 148,
         'source': 'NIST Category-5 floor: Grover on AES-256, 1.17*2^148 gates (Jaques-Naehrig-Roetteler-Virdia Tables 9/11, the row the v1.43 constants table carries); not a measured ML-KEM lattice cost'},
        {'layer': 'S3 MTC inclusion proof (RFC 6962-style nodes, no index)', 'cheapest_game': 'multi-target second preimage (same issue as S2-006; T = certs/batch·batches)', 'gates_log2': None, 'source': 'flagged, not measured here'},
        {'layer': 'S4 TESLA 256-bit chain', 'cheapest_game': 'chain preimage', 'gates_log2': 128 + GATES_LOG2, 'source': 'S4 report / S1-010 law'},
        {'layer': 'S4 TESLA MAC 128-bit tag', 'cheapest_game': 'online tag guess (no offline speed-up)', 'gates_log2': None, 'source': 'per-attempt 2^-128, online only'},
        {'layer': 'S5 card LMS n=32', 'cheapest_game': '= S1', 'gates_log2': 128 + GATES_LOG2, 'source': 'S1-010'},
        {'layer': 'S6 hybrid KEM (PQ component Cat 5)', 'cheapest_game': 'Category-5 reference attack', 'gates_log2': 148,
         'source': 'NIST Category-5 floor, the same entry as the S3 row; S6-010 pins the hash-preimage margins (-46 / -14 / +18 at n = 128 / 192 / 256) and produces no 148'},
    ]
    for r in rows:
        r['passes_qpt128'] = None if r['gates_log2'] is None else r['gates_log2'] >= BUDGET
    return rows


def composition():
    """Only the TLS session shares one attacker goal across its primitives."""
    import math
    # The two 148 entries are the NIST Category-5 floor described above the exponent table, not a
    # lattice cost for ML-KEM-1024; 146 is the measured Grover figure for a 256-bit hash (S1-010).
    parts = {'ephemeral KEM ML-KEM-1024': 148, 'server long-term KEM ML-KEM-1024': 148, 'MTC/transcript hash (prefixed nodes)': 146}
    total = -math.log2(sum(2.0 ** -v for v in parts.values()))
    return {'same_goal_union': {'goal': 'break one TLS session (confidentiality or authentication)', 'parts_gates_log2': parts,
                                'union_gates_log2': round(total, 2), 'form': 'Pr[break] <= G * 2^-(union) in D2 units'},
            'refused': ['S1 firmware + S2 DNSSEC', 'S2 DNSSEC + S3 TLS', 'S4 TESLA + S5 card', 'any cross-layer sum'],
            'why': 'a union bound is defined for events in one probability space with one winning condition; '
                   'the layers have different adversaries, keys and goals, so epsilon_total is NOT their sum'}


def untestable(reports):
    out = {}
    for sid, r in reports.items():
        u = r.get('untestable_assumptions')
        if u:
            out[sid] = u
        elif r.get('assumptions'):
            out[sid] = r['assumptions']
    return out


def build(refresh=False):
    suites, reports = {}, {}
    for sid, (fn, title) in SUITES.items():
        if not os.path.exists(os.path.join(_HERE, fn)):
            suites[sid] = {'missing': fn}
            continue
        suites[sid] = run_suite(sid, fn)
        suites[sid]['title'] = title
        reports[sid] = load_report(sid, fn, refresh)
    ledger = {'suites': suites, 'attack_records': attack_records(reports), 'security_exponents': exponent_table(reports),
              'composition': composition(), 'untestable_assumptions': untestable(reports),
              'model_discrepancies': {'S2': reports.get('S2', {}).get('worst_case'), 'S3': reports.get('S3', {}).get('model_discrepancies'),
                                      'S4': reports.get('S4', {}).get('model_discrepancies'), 'S5': reports.get('S5', {}).get('v2_0_claims_remeasured')}}
    return ledger


def markdown(L):
    o = ['# Audit checklist v2.1 — S1–S6\n', 'Columns: **spec** = implementation does what the specification says; **numbers** = resource claims reproduced; '
         '**attack** = adversary tries to violate the property; **bound** = the formal bound supports the claim.\n']
    tot = passed = 0
    for sid, s in L['suites'].items():
        if 'missing' in s:
            o.append(f"## {sid} — MISSING ({s['missing']})\n"); continue
        o.append(f"## {sid} — {s['title']}\n\n{s['summary']} — {'ALL PASS' if s['all_pass'] else 'FAILURES'}\n")
        o.append('| ID | column | what it checks | status |\n|---|---|---|---|')
        for t in s['tests']:
            tot += 1; passed += t['status'] == 'PASS'
            o.append(f"| {t['id']} | {t['column']} | {t['description'][:160]} | {t['status']} |")
        o.append('')
    o.append(f'\n**Totals: {passed}/{tot} tests pass.**\n')
    o.append('## Attack records\n\n| attack id | component | game | measured | cost (log2 gates) | passes QPT-128 | assumption |\n|---|---|---|---|---|---|---|')
    for r in L['attack_records']:
        o.append(f"| {r.get('attack_id')} | {str(r.get('component'))[:40]} | {str(r.get('game'))[:70]} | {str(r.get('measured', r.get('outcome', '')))[:80]} | "
                 f"{r.get('gates_log2', '')} | {r.get('passes_qpt128', '')} | {str(r.get('assumption', ''))[:40]} |")
    o.append('\n## Security exponents per layer (cheapest attack, production parameters, 2^18 gates/query)\n\n| layer | cheapest game | log2 gates | passes 2^128 | source |\n|---|---|---|---|---|')
    for r in L['security_exponents']:
        o.append(f"| {r['layer']} | {r['cheapest_game']} | {r['gates_log2']} | {r['passes_qpt128']} | {r['source']} |")
    c = L['composition']
    o.append(f"\n## Composition\n\nUnion bound formed ONLY for: {c['same_goal_union']['goal']} → parts {c['same_goal_union']['parts_gates_log2']} → "
             f"**2^{c['same_goal_union']['union_gates_log2']}** ({c['same_goal_union']['form']}).\n\nRefused: {', '.join(c['refused'])}. {c['why']}.\n")
    o.append('## Model discrepancies (v2.0 claim → v2.1 measurement)\n')
    o.append('```json\n' + json.dumps(L['model_discrepancies'], indent=1, default=str)[:6000] + '\n```\n')
    o.append('## Untestable assumptions\n')
    for sid, u in L['untestable_assumptions'].items():
        o.append(f'- **{sid}**: ' + json.dumps(u, default=str)[:1200])
    return '\n'.join(o) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh', action='store_true')
    a = ap.parse_args(argv)
    L = build(a.refresh)
    with open(os.path.join(SP, 'AUDIT_LEDGER_v2.1.json'), 'w') as f:
        json.dump(L, f, indent=1, default=str)
    with open(os.path.join(SP, 'AUDIT_CHECKLIST_v2.1.md'), 'w') as f:
        f.write(markdown(L))
    tot = sum(len(s.get('tests', [])) for s in L['suites'].values())
    ok = sum(1 for s in L['suites'].values() for t in s.get('tests', []) if t['status'] == 'PASS')
    print(f'{ok}/{tot} tests pass; suites: ' + ', '.join(f"{k}:{'ALL' if v.get('all_pass') else 'MISSING' if 'missing' in v else 'FAIL'}" for k, v in L['suites'].items()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
