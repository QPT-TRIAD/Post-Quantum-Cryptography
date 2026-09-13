# The audit method

How the v2.1 audit is built, what its four columns mean and how they are actually assigned, what the
ledger records, the one composition rule, and every v2.0-claim → v2.1-measurement discrepancy stated
as a discrepancy.

---

## 1. The four columns, and how they are assigned

Every test ID carries one column:

| column | definition as printed in the checklist |
|---|---|
| **spec** | implementation does what the specification says |
| **numbers** | resource claims reproduced |
| **attack** | adversary tries to violate the property |
| **bound** | the formal bound supports the claim |

**They are assigned by a keyword classifier, and that is stated wherever the counts are quoted.**
`src/audit_ledger.py` → `classify(text)` lower-cases the text and returns the first bucket that
matches, in this priority order:

1. **attack** — `game`, `attack`, `fault`, `crash`, `rollback`, `forge`, `replay`, `manipul`,
   `downgrade`, `clone`, `mitm`, `substitut`, `late`, `reorder`, `concurrent`, `exhaust`
2. **bound** — `ledger`, `grover`, `bound`, `qpt128`, `margin`, `composition`, `multi_target`,
   `multi-target`, `per_query`, `scaling law`, `binding`
3. **numbers** — `scal`, `numbers`, `remeasur`, `worst`, `bytes`, `size`, `cpu`, `cycles`, `budget`,
   `flight`
4. **spec** — everything else, i.e. the default

**What the classifier actually reads.** It is called as `classify(name + ' ' + desc)` where `desc` is
the free-text captured between the test's name line and its status token in unittest's verbose
output. In practice that capture is always empty — the status sits on the same line as the name — so
`desc` falls back to the name and the classifier sees the **test method name, twice**. Verified: all
70 rows in `results/AUDIT_LEDGER_v2.1.json` have `description == name` (0 exceptions). The
checklist's "what it checks" column is therefore `name[:160]`, not prose. A test's docstring is
**never** read.

**Consequences a reader must carry.**

- The column is a property of how a test was *named*, not of what it does. A test that adversarially
  manipulates a proof but is named `..._numbers_remeasured` would be filed under `numbers`.
- The priority order matters: `attack` beats `bound` beats `numbers` beats `spec`. `S1-011`
  (Grover simulation) lands in `bound`; `S1-010` (`attack_game_ledger`) lands in `attack`.
- Reading the columns as a coverage audit would overstate them. They are a reading aid for a
  checklist of 70 rows. The two aggregates that follow from them are stated for the same reason and
  carry the same caveat.

**The counts over the ledger of 70 tests.**

| column | tests |
|---|---|
| attack | 36 |
| spec | 20 |
| numbers | 7 |
| bound | 7 |
| total | 70 |

---

## 2. How a suite is run and parsed

`src/audit_ledger.py` → `run_suite(sid, fn)`:

- runs `sys.executable <fn> --self-test` with a **1800 s** timeout, capturing stdout and stderr
  together;
- finds lines matching `^(test_(S\d)_(\d{3})\S*) \(`, extracting the method name and the test ID;
- walks forward until it sees `... ok` / `... ok` / `... FAIL` / `... ERROR` / `... skipped`, mapping
  them to `PASS` / `FAIL` / `ERROR` / `SKIP`;
- takes the summary from the first line beginning `Ran `;
- marks the whole suite `all_pass` only if some line is exactly `OK` **and** the process exit code is
  zero.

A suite that crashes before printing `Ran ` yields no tests and `all_pass: False`. A test that is
skipped is recorded as `SKIP`, not as a pass — which is why the `hsslms` interop tests are recorded
as `PASS` and not silently optimised away (see §5.3).

`load_report(sid, fn, refresh)` writes/reads `results/<sid>_audit_report.json`: with `--refresh` (or
when the file is missing) it runs `<fn> --report` with a **3600 s** timeout and stores stdout; a
non-zero exit is recorded as `{'error': stderr[-2000:]}`, which is how a broken report surfaces as an
error in the ledger rather than as missing numbers. Without `--refresh`, the cached report beside the
ledger is read as-is.

**The cache is a hazard, and it has already fired once.** The programme's recorded ledger was
generated while `results/s5_audit_report.json` on that machine was a stale copy predating the
`v2_0_claims_remeasured` block, so the recorded ledger's `model_discrepancies.S5` is **`null`**. The
regenerated ledger from a `--refresh` run has it populated. See §5.2.

---

## 3. What the ledger contains

`results/AUDIT_LEDGER_v2.1.json`, top-level keys:

| key | what it holds |
|---|---|
| `suites` | per suite: `tests` (id, name, description, status, column), `summary` (the `Ran` line), `all_pass`, `title` |
| `attack_records` | one row per named attack game across S1–S6: attack id, component, game, capabilities, measured/outcome, cost in log2 gates, whether it counts toward the QPT-128 bound, and the assumptions it rests on |
| `security_exponents` | the cheapest-attack gate exponent **per layer at production parameters**, with its source test, and whether it passes QPT-128 |
| `composition` | the single permitted union bound, the refused sums, and why |
| `untestable_assumptions` | per suite, the assumptions that no test in this repository can discharge (6 suites' worth) |
| `model_discrepancies` | the v2.0-claim → v2.1-measurement differences, per suite (S2, S3, S4, S5) |

`results/AUDIT_CHECKLIST_v2.1.md` is the same data as prose: a table per suite, the totals line, the
attack-record table, the security-exponent table, the composition paragraph and the assumptions.

**Where the canonical copies live.** `records/audit-checklist.md` and `records/audit-ledger.json`
are the programme's own recorded copies, byte-identical to the source tree. The files in
`results/` are **regenerated** by `src/audit_ledger.py --refresh` in this repository. The domain
README and `docs/studies.md` link to the records rather than duplicating them; where the two differ,
the difference is a finding and is reported in `VERIFICATION.md`.

---

## 4. The composition rule

`src/audit_ledger.py` → `composition()`, taken from `pq_audit_s6`.

A union bound `Pr[A ∨ B] ≤ Pr[A] + Pr[B]` is a statement about **two events in one probability
space** — one experiment, one adversary, one winning condition. Adding ε's across layers with
different adversaries, keys and goals is not a conservative step; it is a step whose precondition is
false, and it can move a verdict.

- **The one same-goal union formed:** break one TLS session (confidentiality or authentication).
  Parts: ephemeral KEM ML-KEM-1024 (148), server long-term KEM ML-KEM-1024 (148), MTC/transcript hash
  with prefixed nodes (146) → **−log2(2^−148 + 2^−148 + 2^−146) = 145.42** log2 gates. The ledger
  states the form as `Pr[break] <= G * 2^-(union)` in D2 units.
- **Refused:** `S1 firmware + S2 DNSSEC`, `S2 DNSSEC + S3 TLS`, `S4 TESLA + S5 card`, and any
  cross-layer sum. The reason recorded in the ledger: the layers have different adversaries, keys and
  goals, so `epsilon_total` is **not** their sum.

Note what the union *is*: a 145.42 figure that is **worse** than any single component (the strongest
hinge is the 146-bit transcript hash). Composition inside a goal does not strengthen a chain; it can
only weaken it, and the arithmetic shows by how much.

---

## 5. Every v2.0-claim → v2.1-measurement discrepancy, stated as a discrepancy

These are recorded in `results/AUDIT_LEDGER_v2.1.json` → `model_discrepancies`. Below, each is given
in the shape *the v2.0 claim was X; the v2.1 measurement is Y; the difference is Z*. None of these
was applied by editing the claim in place.

### 5.1 S2 — the DNS worst case, and the multi-target node hash

| v2.0 | v2.1 | difference |
|---|---|---|
| "UDP-safe for any zone size" | realistic worst case **1,839 B** (NSEC3, 3 labels, 30-char apex, shard 2^10); the model's own baseline shape is **954 B**, not 1,129 B | the claim is **withdrawn**. Typical shapes are safe at 1,232 B; realistic worst cases need RFC 9715's 1,400 B and small shards. |
| MTL ladders and multiproofs hash interior nodes as `H("node", l, r)`, no position prefix | at n = 256 with T = 2^40 signed structures, the multi-target second preimage costs **2^126 gates** — *inside* the 2^128 budget — versus **2^146** for the prefixed variant | the v2.0 construction **fails QPT-128**. The zero-byte fix (`H(node, ladder_id, rung, level, index, l, r)`) is implemented **inside the audit file only** (`prefixed_multiproof_build` / `prefixed_multiproof_verify`) and was **not applied to the design files**. The MTC prototype in S3 has the same exposure, flagged and unmeasured. |
| the multiproof's distinct denials need separate condensed signatures | multiproof 988 B vs 1,071 B at 2^10 names; 1,244 B vs 1,455 B at 2^14 | the multiproof saves 83 B and 211 B at those sizes — a real but modest win, and it does not rescue the worst case. Worst-case rows in the ledger: NXDOMAIN 1,839 / CNAME 1,513 / WILDCARD 1,260 / DNSKEY 822 / A 661 B realistic; 2,120 / 3,830 / 1,597 / 912 / 790 B pathological. |

Also recorded: an earlier reading that unprefixed node hashing loses a factor `log2(depth)` was a
**per-trial/per-query mis-accounting**; at n = 8 the measured per-query rates are 109/24,576
unprefixed and 145/24,576 prefixed against an expected 2^−8 = 0.00390625. The corrected statement is
that *single-structure* security is the same for both; it is the **multi-target** game that separates
them. The correction is kept on the record as A3.

### 5.2 S5 — smart card state and hash counts, including a `null` in the recorded ledger

**First, the ledger-level difference, which is a difference in the *record*, not in the code.**
`records/audit-ledger.json` (the canonical recorded copy) has `model_discrepancies.S5 = null`; the
regenerated `results/AUDIT_LEDGER_v2.1.json` has it populated. The cause is the report cache
described in §2: the recorded ledger was built on a machine whose cached `results/s5_audit_report.json`
predated the `v2_0_claims_remeasured` block. **Nothing was overwritten** — both ledgers are kept and
the difference is reported in `VERIFICATION.md`.

The populated block then states four v2.0 → v2.1 differences:

| v2.0 claim | v2.1 measurement | verdict as recorded |
|---|---|---|
| BDS state at h = 8, k = 2 is **664 B** | peak **828 B** | "claim was the END state; peak during the run is higher" |
| **30,466** hashes/signature at h = 8 | **30,445.5** | **confirmed** |
| maximum at h = 20 is **≤ 86,720** hashes | maximum **95,775** | "claim too low: BDS needs (h−k)/2 **+ 1** leaf computations in the worst round, not (h−k)/2" |
| persistent state **< 2 KB** | **2,148 B at h = 20** | "2.1 KB at h = 20" — the claim does not hold |

The mean law `(h−k)/2` is *validated*, at h = 8…16: measured 3.0078, 4.0020, 5.0005, 6.0001, 7.00003
against 3, 4, 5, 6, 7 — and the composed model is 0.36 % high at h = 8 (30,555.1 vs 30,445.5) and
0.26 % high at h = 10 (39,210.0 vs 39,109.9). So the discrepancy is precisely at the **worst round**,
not in the average.

### 5.3 S3 — the handshake, four items, no verdict changes

| v2.0 claim | v2.1 measurement | difference |
|---|---|---|
| the KEMTLS first flight includes a **Finished** (40 B) | there is **no** CertificateVerify and **no** Finished in that flight: the server's Finished follows the client's KEM ciphertext; the **client's** second flight is **1,626 B** | the flight shape was wrong; the byte total happened to be close |
| MTC + OV-V: **449,972 B** server flight | **NOT ENCODABLE**: `TLSSubjectInfo.public_key` is `opaque<1..2^16-1>` and a 446,992-B key overflows the length field | the configuration is not merely large, it cannot be expressed |
| ServerHello with a hybrid ML-KEM: no packet count given | it **exceeds one 1,200-B Initial datagram**; the server spends 2 padded Initial datagrams (2,400 B) of its 7,200-B budget on ServerHello alone | a packet-boundary fact the model did not have |
| model server-flight sizes | exact handshake bytes, all ten configs | deltas +34 to +62 B, and **−80 B** on the three MTC configs; `verdict_changes: []` — exact framing changed no fit/no-fit verdict, which was itself hypothesis H1 and it was **refuted** |

The exact encodings are in `docs/studies.md` §3.4; the recommended configuration, MTC + KEMTLS with
ML-KEM-1024, is **4,148 B** exact handshake (4,203 B on TCP), against a model figure of 4,280 B.

### 5.4 S4 — five recorded model discrepancies

1. "52 B per message" holds for intervals `i > d` **only**; the first `d` packets of a chain carry no
   disclosed key and are **20 B** (measured).
2. The `TeslaReceiver` docstring says the receiver's clock "may lead the sender by at most `sync`";
   the code and RFC 4082 bound the **sender** leading the receiver — the dangerous direction is
   receiver **lag**.
3. The granular receiver is **stricter** than RFC 4082's continuous rule at **13 of 270** grid points
   (where ε is not a multiple of T), by 1 in the sync term.
4. The 1,772-B anchor figure is the LMS w8 size **formula**; the only executable Merkle signer in the
   repository is WOTS w16 (2,820 B at h = 20 including the randomiser).
5. Pending buckets are never pruned: any injected index inside the safe window allocates receiver
   memory — a **denial-of-service surface**, not a forgery.

Two receiver bugs sit alongside these, fixed **only in the audit's `FixedTeslaReceiver` subclass**:
BUG-1, where a lost key-disclosing packet strands buffered packets that are in fact derivable
(liveness), and BUG-2, where the replay filter keys on the **unauthenticated** (index, body) so a
pre-injected junk packet makes the genuine one look like a replay (DoS).

---

## 6. What the columns and the ledger are not

- The four columns are a keyword classification over test method names (§1). They are not a review.
- The attack-record table's `measured` field is `None` for the S1 production-parameter games — those
  are **accounting** rows (gate counts from the Grover law), not measured events. Only the four
  `S1-G2-sim-n*` rows carry measured `k` and `p`, because only those are simulated.
- The ledger records pass/fail, not strength. A `PASS` on a test whose assertion is vacuous is a
  `PASS`; one such assertion is on the record in `src/s5_bds_faults.py` (an `… or True` clause, with
  the effective check on the following line).
- `all_pass` requires an `OK` line *and* exit code 0, but it does **not** notice a test that was
  removed from the suite. The 70 count is a count of what ran.
- No column, and no ledger field, records runtimes as a result: the `Ran N tests in T s` strings move
  between runs and are not a measured quantity of the study.
