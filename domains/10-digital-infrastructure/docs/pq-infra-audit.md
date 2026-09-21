# Audit v2.1 of the S1–S6 program — what survived, what changed, what is open

Date: 2026-09-11. Method: the QPT-128 treatment applied to S1–S6 — every claim
became a test ID in one of four columns (spec conformance / reproduced numbers /
attack game / bound), reduced-size attack experiments where a game permits,
an independent implementation where one exists, and a ledger that sums only
inside one attacker goal. Generated artifacts: `AUDIT_CHECKLIST_v2.1.md`
(70 test rows, attack records, exponents, composition, untestable assumptions)
and `AUDIT_LEDGER_v2.1.json`; regenerate with `python3 pq_audit_ledger_v2.1.py`.
Permanent failure record: `FAILED_ASSUMPTIONS.md` (21 new entries).

**Result: 70/70 audit tests pass** — but several v2.0 *claims* did not survive
unchanged. That is the point of the exercise; the corrected claims are below.

## Per-step verdicts

| Step | Spec | Numbers | Attack | Bound | Claim after audit |
|---|---|---|---|---|---|
| S1 firmware | RFC 8554-exact LMS, **interop both directions with hsslms 0.1.3** (5 typecode pairs incl. n=24), sizes derived from typecodes | 1,772 / 2,828 / 1,140 B reproduced | crash injection at every step, rollback (hardware counter), 16-thread concurrency, exhaustion, clone demo | games G1–G5 enumerated; cheapest = 2^(n/2) single-target (domain separation blocks multi-target); exact Grover on the keyed chain matches closed form at n=8..14 | **Unchanged**: n=32 passes (2^146), NSA-preferred n=24 fails (2^114) |
| S2 DNSSEC | real wire encoder (dnspython), responses parse back with the right RRSIG counts | baseline shape **954 B** exact (model said 1,129) | automated worst-case search; multiproof manipulation; multi-target game | per-query 2^-n both variants; **multi-target: unprefixed nodes give T·2^-n** | **Narrowed**: "UDP-safe for any zone size" is false as stated — realistic worst 1,530 B (NSEC, rollover) / 1,839 B (NSEC3); ≤1,232 for typical shapes; ≤1,400 with shard ≤2^10 outside rollover. **Fix required, and applied**: prefix nodes with (ladder id, rung, level, index) — unprefixed at n=256, T=2^40 is 2^126 gates, inside the budget; the design files now carry the prefix (see §1 below) |
| S3 TLS/PKI | RFC 8446 / QUIC / DER / MTC exact encoder | KEMTLS flight **4,148 B** exact (model 4,280); no fit verdict flips | 8 KEMTLS games blocked with positive control; hostname claim is load-bearing | B and T reported on separate axes; SQIsign-V configs 6.7 handshakes/s/core | **Unchanged in bytes, qualified**: the largest *legal* certificate (100 × 253-char SANs) breaks every config → a name-count cap belongs in the deployment spec; MTC's index-free node hashing had the same multi-target exposure as S2 (flagged, never measured, and now carrying the same position prefix) |
| S4 broadcast | existing TESLA audited, not rewritten | 52 B steady-state; first d packets 20 B; +26–30 B link framing | 6 games, 561 attempts, 0 wins; **2 bugs in the v2.0 receiver** (stranded pending packets; unauthenticated replay filter = DoS) | boundary `ceil((Δt+ε)/T)+ceil(ε/T) ≤ d−1` matched at 270/270 grid points | **Corrected**: use `FixedTeslaReceiver`; overhead claim restated as steady-state |
| S5 smart card | BDS == naive for every leaf, h=2..12, every k (>20k paths) | full sweeps h=8..16, prefix windows 18/20; mean = (h−k)/2 exactly; composition within 0.4 % of the real signer | power loss after every hash (~120 points), no leaf reuse; rollback / corruption / restore | inherits S1 | **Corrected**: max at h=20 is **95,775** hashes (not 86,720: BDS worst round = (h−k)/2 **+1** leaves); mean 82,700; peak state **2,148 B** at h=20 (828 B at h=8, not 664). **Fix applied**: the card tree hashed interior nodes with no position, the same defect as S2 — all six places the BDS traversal forms or refolds a node now bind (public seed, level, parent index); no byte count and no counted hash moves (§1 below) |
| S6 migration | — | 768→1024 byte deltas | Games A–E with measured slopes (−0.999 / −0.931); **Game C negative**: correlated components defeat the combiner 2,048/2,048; unbound negotiation downgrades 256/256, bound 0/256; lax root verifier accepts n=24/16 forgeries | gate margins n=128/192/256 = −46 / −14 / +18 bits | **Qualified**: combiner theorem needs independence (untestable); "refuse Cat 0" policy needed against a quantum downgrade that re-MACs; ROM must pin the typecode |

## The two findings that change the design

1. **Position-prefixed node hashing (S2-006, applies to S3's MTC prototype and
   the S5 card tree too).**
   The v2.0 ladders hash interior nodes as H(l‖r). Single-structure security is
   2^-n per query, but an adversary holding T signed nodes across all zones
   tests one evaluation against all T: quantum 2^(n/2)/√T. At n = 256 and
   T = 2^40 that is 2^108 queries = **2^126 gates — inside the 2^128 budget**.
   Measured at n=16: 90 wins vs 97.7 expected (T=64), 401 vs 390.6 (T=256);
   prefixed variant 1–2 wins vs 1.5 expected. Fix costs zero bytes:
   H(node, ladder_id, rung, level, index, l, r) — exactly what RFC 8554's
   (I, r) and XMSS-T's addresses do. Same analysis applies to any RFC 6962-style
   Merkle certificate tree; the MTC drafts should be checked for it.
   **Applied.** `src/s1s2_hashsig_dnssec.py` binds each interior node of the S1
   Merkle tree to (public seed, level, parent index) and each node of the MTL
   ladder, condensed proof and multiproof to (rung, level, parent index);
   `src/s3_tls_pki.py` binds each MTC node to (batch id, level, parent index);
   `src/s5_smartcard_hsm.py` binds each node of the card tree to (public seed,
   level, parent index) at all five places the BDS traversal forms one — the
   key-generation stack, the round that rebuilds `auth[tau]`, a treehash update,
   the independent naive recomputation and the card's own verifier — and
   `src/s5_bds_faults.py` binds the node its state self-check refolds. The six
   have to agree exactly, because BDS reaches the same node by several routes;
   the level and index each one needs are already in the traversal state.
   Every field is already held by the verifier, so no wire size changes. All
   three files carry regressions that fail against the previous hashing. v2.0
   keeps the defect as the record of what v2.0 was.

2. **DNSSEC claim narrowed by worst-case search (S2-003).** On real wire format
   with 3×20-char labels, a 30-char apex, two keys double-signing during
   rollover and 2^14-leaf shards, NXDOMAIN is 1,530 B (NSEC) / 1,839 B (NSEC3).
   The levers, measured: no double-signing → 1,361; plus shards of 2^10 →
   1,287 (≤ 1,400, > 1,232). The corrected statement: typical zone shapes are
   UDP-safe at 1,232; realistic worst cases need RFC 9715's 1,400 and small
   shards, and rollover windows should be TCP-tolerant. CNAME chains of 4
   (5 RRSIGs) exceed 1,232 under every variant.

## Corrected resource numbers

| Claim (v2.0) | Audit (v2.1) |
|---|---|
| KEMTLS + MTC server flight 4,280 B | 4,148 B exact; client second flight 1,626 B (ct + Finished) |
| DNSSEC worst NXDOMAIN 1,129 B | 954 B for that zone shape; 1,530–1,839 B realistic worst; 2,120 B pathological |
| Card: 30,466 hashes/sig at h=8 | 30,445 (confirmed) |
| Card: ≤ 86,720 at h=20 | max 95,775; mean 82,700; peak state 2,148 B |
| TESLA 52 B/message | 52 B steady state; 20 B for the first d packets; +26–30 B link framing |

## Untestable assumptions (collected)

A-NoExport (SP 800-208 §8.1) · A-Grover optimality is a theorem in the query
model, the 2^18 gates/query floor is engineering · SHA-256 / SHAKE256 as random
functions · MM-SPR at n=256 (measured only at n ≤ 16) · loose time-sync bound ε
· HMAC-SHA3 PRF · independence of hybrid components (Game C shows it is
necessary) · ROM immutability and atomic NVM writes · resolver/middlebox
behaviour above 1,232/1,400 B (literature) · all cycle counts (literature).

## Not done

- **No independent implementation for TESLA, BDS, MTC or the multiproof** —
  only LMS has one (hsslms). The independent multiproof *verifier* here is a
  second style of the same author's code, which is weaker evidence.
- **Blockchain integration** (S1–S6 through the TRIAD devnet) was not run; the
  kit's devnet phases C0–C7 remain `not_started`.
- MTC multi-target exposure was flagged and never measured, so the position
  prefix now in `src/s3_tls_pki.py` rests on the S2 measurement and the counting
  argument, not on an MTC-specific game; SQIsign v3.0 timings,
  MAYO-5 / ML-DSA-87 signing costs and ML-KEM-1024 decapsulation cycles were
  not verified here (left `None`, never invented).
- Hardware: no card, no radio, no HSM was touched; every cycle count is from
  the cited papers.
