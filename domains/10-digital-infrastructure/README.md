# D10 — digital infrastructure

Six deployment studies (S1–S6) that ask whether **one** security target — QPT-128 — can be met
across today's digital infrastructure, plus the v2.1 audit that tried to falsify them and the v2.2
fix release.

QPT-128 is fixed in the programme's security target: an attacker with fewer than 2^128 gates, at
≥ 2^18 gates per hash query, succeeds with probability below 1/3. Reference attack costs per NIST
category are 2^83 (Cat 1), 2^100 (Cat 2), 2^116 (Cat 3) and 2^148 (Cat 5) gates
(`docs/pq-infra-program.md` §1). Only Category 5 passes. The deployed hybrid ML-KEM-768 (Cat 3)
therefore sits 12 bits inside the budget and is not the finish line.

Nothing in this domain is a deployment. Everything is measured on Python models and byte encoders,
or is checked against the literature. The label of every claim is stated where the claim is made.

## The six studies, and why each was posed

| study | file | the question it was posed to answer |
|---|---|---|
| **S1** firmware / secure boot | start with `src/s1_lms.py` (the RFC 8554-exact audit, current revision); then the model `src/s1s2_hashsig_dnssec.py` and the revision it corrects, `src/s1s2_hashsig_dnssec-v2.0.py`; `history/s1_lms-v2.1.py` is the audit revision the ledger's recorded 70/70 was produced with | Firmware and boot ROMs must verify updates for decades, with hashes only — no big-integer or polynomial arithmetic. Does a stateful hash-based signature fit, and at which hash output length? |
| **S2** DNSSEC | `src/s2_dns_worstcase.py` | A DNSSEC answer must fit an unfragmented UDP datagram (1,232 B). A single ML-DSA-44 RRSIG is 2,420 B. Can any Category-5 design answer every zone shape? |
| **S3** TLS 1.3 / QUIC / Web PKI | `src/s3_tls_pki.py`, `src/s3_tls_wire.py` | The obvious Category-5 chain (ML-KEM-1024 + ML-DSA-87 everywhere) makes the server's first flight ~31 kB, past the TCP initial window and the measured "10 kB cliff". What shape keeps a Category-5 handshake inside one flight? |
| **S4** constrained broadcast | `src/s4_embedded_broadcast.py`, `src/s4_tesla_adversarial.py` | ICS, satellite, medical and embedded receivers of authenticated broadcast: here the blocker is not CPU, it is the link (51 B per LoRa SF12 frame). Where no PQ signature fits in a frame, what authenticates a message? |
| **S5** smart cards / secure elements / HSM | `src/s5_smartcard_hsm.py`, `src/s5_bds_faults.py` | PQ signatures do not fit a card (8–12 KB RAM, 256-B APDUs), and unlike firmware these devices must *sign*. Can a stateful hash-based signer live on a card, and what does state management cost? |
| **S6** migration and crypto-agility | `src/s6_migration_agility.py`, `src/s6_hybrid_games.py` | What is deployed is Category 3. What does moving each layer to Category 5 cost, which layers can rotate at all, and what does an agility mechanism have to survive? |

The unifying observation (`docs/pq-infra-program.md` §2) is that every size blocker is the same
blocker: a Category-5 signature is too big for one packet, one APDU or one link frame, and no
compact Category-5 signature is also fast. The literature already solves that three times with
Merkle trees — SP 800-208 for firmware, Merkle Tree Ladder (MTL) mode for DNSSEC, Merkle Tree
Certificates (MTC) for the Web PKI. The programme therefore builds one Merkle toolkit (WOTS+,
LM-OTS w=8, tree, ladder, multiproof, BDS traversal) and adds one glue per layer. Where a layer
must sign *online*, per-transaction work moves to a KEM (KEMTLS) or a MAC chain (TESLA).

## Reading order

1. `docs/pq-infra-program.md` — the programme's own document: the target, the six steps, the
   sizes, the four hypotheses that died during development, the standards read. Written before the
   audit; where the audit corrected it, both numbers are given below and in
   `docs/audit-method.md`.
2. `docs/studies.md` — the six studies end to end: problem, which *part* of which theory was
   borrowed, the construction step by step, the tests, the measured result, and what the study
   does not show.
3. `docs/pq-infra-audit.md` — the v2.1 audit report: what the audit changed, the corrected headline
   numbers, the untestable assumptions.
4. `docs/audit-method.md` — the four audit columns, the ledger schema, the composition rule, and
   every v2.0-claim → v2.1-measurement discrepancy stated as a discrepancy.
5. `docs/packages.md` — package by package: what each library is, how it works at the level needed
   to trust its output, how it is invoked, what it returned here, and its limitations.
6. `VERIFICATION.md` — every suite re-run in the pinned environment, with the recorded value, the
   observed value, and the verdict.
7. `results/` — the regenerated reports; `records/` — the programme's canonical recorded copies.

## What each path is

| path | what it is |
|---|---|
| `src/s1s2_hashsig_dnssec.py` | S1/S2 model, revision v2.2 (current); supersedes the v2.0 file for S1/S2. |
| `src/s1s2_hashsig_dnssec-v2.0.py` | S1/S2 model, revision v2.0. **Still a live import target**: `src/s3_tls_pki.py` and `src/s4_embedded_broadcast.py` load it by filename as a cross-check oracle. |
| `src/s3_tls_pki.py` | S3 TLS/Web PKI model (only revision). |
| `src/s4_embedded_broadcast.py` | S4 constrained-broadcast model (only revision). |
| `src/s5_smartcard_hsm.py` | S5 smart-card/HSM model (only revision); loads the S4 model for its hash counter. |
| `src/s6_migration_agility.py` | S6 migration/agility model (only revision); loads the S1/S2, S3 and S4 models. |
| `src/s1_lms.py` | S1 audit, revision v2.2 (current): RFC 8554-exact LMS from the RFC text, hsslms interop, state machine, hardware counter, and S1-012, the regression for the approved-pair fix. Its report is identical to the v2.1 report in every recorded number; only the random Grover draw differs. |
| `history/s1_lms-v2.1.py` | S1 audit, revision v2.1 — superseded by v2.2, but **the revision the ledger runs as suite S1** (the recorded 70/70 was produced with it). |
| `src/s2_dns_worstcase.py` | S2 audit: real DNS wire encoder (dnspython), worst-case search, multiproof games, multi-target game. |
| `src/s3_tls_wire.py` | S3 audit: exact RFC 8446 / QUIC / DER / MTC byte encoders, KEMTLS games on an ideal-KEM toy, CPU from literature. |
| `src/s4_tesla_adversarial.py` | S4 audit: discrete-event adversarial network, boundary sweep, six attack games, byte accounting. |
| `src/s5_bds_faults.py` | S5 audit: exhaustive BDS-vs-naive comparison, state manipulation, fault injection after every hash call. |
| `src/s6_hybrid_games.py` | S6 audit: hybrid-combiner games, downgrade games, ROM root games, agility ledger, gate margins. |
| `src/audit_ledger.py` | The ledger generator: runs all six suites, parses the test IDs, loads each suite's `--report` JSON, writes the checklist and the ledger into `results/`. |
| `docs/` | The programme and audit documents, plus the three guides written for this repository. |
| `results/` | Regenerated by `src/audit_ledger.py --refresh`: `s1..s6_audit_report.json`, `AUDIT_CHECKLIST_v2.1.md`, `AUDIT_LEDGER_v2.1.json`. |
| `records/` | The programme's canonical recorded copies of the checklist and the ledger, byte-identical to the source tree. This domain **links** to them rather than duplicating them. |

### Naming and layout

`src/` holds **thirteen** files, flat — every module is a sibling of the others it imports, which is
what the cross-module loaders require (see `VERIFICATION.md` §6). One further Python file, the
superseded S1 audit revision, is under `history/`. The fourteen divide three ways.

**The six suites the ledger runs**, one per study, which are the 70 tests the checklist reports:
`history/s1_lms-v2.1.py` (S1), `src/s2_dns_worstcase.py` (S2), `src/s3_tls_wire.py` (S3),
`src/s4_tesla_adversarial.py` (S4), `src/s5_bds_faults.py` (S5), `src/s6_hybrid_games.py` (S6).

**The five design models and the current S1 audit revision**, which carry the studies' claims and are
what those claims are checked against: `src/s1s2_hashsig_dnssec.py` (the S1 and S2 model — one file
carries both), `src/s3_tls_pki.py`, `src/s4_embedded_broadcast.py`, `src/s5_smartcard_hsm.py`,
`src/s6_migration_agility.py`, and `src/s1_lms.py` (the S1 audit at its current revision). Plus
`src/audit_ledger.py`, which runs the six suites and writes the checklist and the ledger.

**One file carries a version in its name**: `src/s1s2_hashsig_dnssec-v2.0.py`, the earlier revision of
`src/s1s2_hashsig_dnssec.py`, kept beside its successor because both are still needed. The v2.0 work
corrected this study's DNSSEC worst-case hash-signature sizing, so a reader checking that correction
needs the claim and its revision together; and it is a **live import target** — `src/s3_tls_pki.py` and
`src/s4_embedded_broadcast.py` each load it by filename as a cross-check oracle, so removing it would
break those two models. Every other file is the current revision of what it does and carries no
version suffix; a suffix is used only where an earlier revision is also present and still read.

`history/s1_lms-v2.1.py` is the revision the recorded **70/70** was produced with, which is why the
ledger's S1 row runs *it* rather than the current `src/s1_lms.py`. The two reports are identical in
every recorded number — sizes, gate margins, the cheapest attack game, the untestable assumptions,
the `hsslms` interop result — and differ only in the random Grover draw, which differs between runs of
either file. The current revision adds one test, S1-012, the regression for the approved-pair fix.

`records/file-map.tsv` records, for each of these files, the source path it came from.

## What the studies prove, and what they explicitly do not

**What they establish (with the label the source gives).**

- S1: at n = 256 the cheapest counting attack on LMS/LM-OTS is a second preimage at 2^128 queries
  = 2^146 gates, which passes QPT-128; the NSA-preferred SHA-256/192 fails it by 14 bits
  (2^114). Sizes are exact and reproduced against hsslms 0.1.3 in both directions
  [M]. Firmware signing is solved *in the standard* and the QPT-128 parameter choice is forced.
- S2: a Merkle multiproof over the denial RRsets plus canonical-order sharding keeps typical zone
  shapes UDP-safe, and the corrected statement is "typical zone shapes are safe at 1,232 B;
  realistic worst cases need RFC 9715's 1,400 B and small shards; rollover windows should be
  TCP-tolerant" [M of a model + encoders]. The v2.0 claim "UDP-safe for any zone size" is
  withdrawn.
- S3: MTC + KEMTLS with ML-KEM-1024 is 4,148 B of exact handshake bytes (4,203 B on TCP) and is
  the only Category-5 configuration in the table with no per-handshake signature [M of an exact
  byte encoder]; every network attack tried against it was blocked [M on an ideal-KEM toy].
- S4: 256-bit TESLA anchored by one hash-based signature costs 52 B per message in steady state
  (20 B for the first d packets of a chain), and 561 forgery attempts across six games won zero
  times [M]. Two receiver bugs were found and fixed in the audit's subclass.
- S5: on-card LMS with BDS traversal needs at most 95,775 hash calls per signature at h = 20
  (mean 82,727) and peaks at 2,148 B of persistent state — both **above** the v2.0 figures of
  ≤ 86,720 and < 2 KB [M]. Fault injection after every hash call reused no leaf.
- S6: the hybrid combiner is IND-CCA if either component is and the hash is a random oracle, but
  component independence is *necessary*, not merely sufficient, and a quantum downgrade that
  re-MACs beats transcript binding unless the client refuses Category 0 [M].

**What none of them show.**

- No hardware was touched. Every cycle count, RAM figure and stack figure in these studies comes
  from the literature, is cited as such, and several are `None` because no number was verified.
- No constant-time, side-channel-hardened or independently audited implementation exists here;
  these are Python models and prototypes over SHAKE256 / SHA-256 / SHA3 toys.
- The ≥ 2^18 gates per hash query floor is an engineering assumption, not a theorem. Grover
  optimality is a theorem in the query model only.
- The reduced-size experiments run at n ≤ 16 bits. They demonstrate counting arguments; they do
  not measure the deployed parameters.
- The multi-target weakness in unprefixed Merkle nodes (2^126 gates at T = 2^40, inside the
  budget) is **flagged and given a zero-byte fix, but the fix is not applied to the design files**
  — neither the MTL ladders/multiproofs nor the MTC prototype.
- The two S4 receiver bugs are fixed only in the audit subclass; no fixed design file exists.
- S5's claim "state < 2 KB" does not survive; S2's "for any zone size" does not survive; S4's
  "52 B per message" holds only in steady state; S6's ledger strings still carry superseded v2.0
  figures.
- The audit's own four-column classifier is a keyword match over test names, and the ledger never
  captures test docstrings — the columns are a reading aid, not a reviewed classification.

## One discrepancy that must be stated, not hidden

`S1-011` (`grover_simulation_matches_law`) asserted that the least-squares slope of log2(k) against
n over one random draw is 0.5 ± 0.06. The simulator draws its secret with
`secrets.randbelow(N)`, so the marked-set size M is random and that slope is a coin flip: in the
programme's own measurement 98 of 200 runs satisfied it (49.0 %); a re-measurement made for this
repository got 108 of 200 (54.0 %). The recorded `PASS` was a favourable draw. The test has been
rewritten to keep both exact per-seed assertions (`|k_measured − k_predicted| ≤ 1` and
`|p_at_k_pred − p_predicted_at_k_pred| < 1e-9`, both 200/200) and to assert the slope on the
median over 41 draws instead (20/20 in 20 independent trials, range 0.4877–0.5494 here; the
programme measured 20/20 over 0.4819–0.5316). `VERIFICATION.md` records the commands, the numbers
and the residual risk. The Grover law remains a *simulation*, not a measurement and not a proof.

## References

- The programme's own documents: `docs/pq-infra-program.md`, `docs/pq-infra-audit.md`.
- The canonical recorded checklist and ledger: `../../records/audit-checklist.md`,
  `../../records/audit-ledger.json`.
- Reproduction: `VERIFICATION.md` in this directory gives the exact commands and the observed
  output for every suite.
