# F1–F5: the five fixes and their regression tests

The fix stage (2026-09-13) turned the five findings of the audit into new files, leaving the audited
references frozen. The rule the source states, and which this repository keeps: the reference files
are immutable audit history (their hashes are in the devnet kit's `HASHES.sha256`), so every fix is
a **new** file derived from its reference by exact, verified string replacement —
`fixes/make_fixes.py` aborts unless each pattern matches exactly once. Regeneration command:
`python3 fixes/make_fixes.py`; it writes into the research tree (`PQT_SRC`) and is therefore **not
run** when building or verifying this repository (see `docs/inputs-and-provenance.md` §1).

**What the derivation reproduces, and what it no longer reproduces.** It reproduces the four fix
files of the 2026-09-13 fix stage byte for byte from the frozen references, and those are the files
the logs in `fixes/` were produced from. It does **not** reproduce the S1/S2 model as published in
`domains/10-digital-infrastructure/src/s1s2_hashsig_dnssec.py`, and has not since **2026-09-21**,
when the S2-006 position-prefix fix was applied there — every interior Merkle node bound to
(structure id, level, parent index), with a regression class for it. That change was made downstream
of this derivation, on the published copy, and not on the frozen v2.0 reference the script reads; it
is not one of F1–F5, and it leaves the published file eleven hunks and roughly 130 lines beyond what
the replacements produce. The script was deliberately **not** extended to cover it: its output is the
v2.2 audit-fix release, described by the archived `fixes/pq_infra_s1s2_hashsig_dnssec_v2.2.py.log`
(15 tests), and folding a later design change into it would emit a file that log does not describe
and would date a 2026-09-21 change to the 2026-09-13 fix stage. Read the derivation for how F2 and
F4 were made; read the published file, whose header records S2-006 and its reason, for the current
S1/S2 model.

## 1. The five fixes

| finding | reference (immutable) | fixed file | root cause | impact | fix | regression result |
|---|---|---|---|---|---|---|
| **F1** LeakSanitizer leak in `verify()` | `modeB_prover_v1.50.c` | `modeB_prover_v1.51.c` (`domains/08-hidden-signers/src/mode_b_prover.c`) | the grinding-condition check returned before `free(P)` (`circ_pub_t`, 9,568 B) — line 803 allocated, line 815 returned | rank-3 resource: a stream of rejected proofs leaks one `P` each in a long-running verifier; acceptance behaviour unaffected | `free(P)` on that path (one line) | ASan+LSan reduced run: **0 leak frames in `verify`** (the v1.50 run: 1 frame, 19,136 B in 2 objects); self-test verified / tampered-rejected / extracted unchanged, `extracted_count 22`; 7/7 |
| **F2** vacuous accept of an empty multiproof; extra node accepted; exceptions instead of `False` | `pq_infra_s1s2_hashsig_dnssec_v2.0.py` | `pq_infra_s1s2_hashsig_dnssec_v2.2.py` | `verify` looped over zero rungs and never checked that the supplied node set equals the exact sibling set | MEDIUM: an "authorization object" proving nothing could be accepted by a caller that does not check coverage; extra nodes made proofs malleable | `verify(..., required=None)`: non-empty dict, typed rungs/leaves/nodes, supplied nodes == needed siblings (no extra, no missing, no duplicates), optional required-leaf coverage, structural defects → `False` | 15/15 (`AuditFixTests`: empty/None/empty-rung, extra/missing/duplicate node, required coverage, malformed inputs, plus the 10 original tests) |
| **F3** mixed LM-OTS n / LMS m accepted; hsslms self-inconsistent on those pairs | `pq_audit_s1_lms_v2.1.py` | `pq_audit_s1_lms_v2.2.py` | neither implementation refused non-approved combinations | LOW (ours): non-standard parameter sets accepted; MEDIUM (hsslms): its own round trip fails | `approved_pair()`: LMS m must equal LM-OTS n (SP 800-208 §4 approved sets; RFC 8554 §5.1 "the two hash functions SHOULD be the same", silent on n = m); refused at keygen (`ValueError`) and at verify (`False`) | 12/12; interop unchanged on approved sets (80/80 agreement, differential 100/100) |
| **F4** `merkle_verify` raised on malformed input | same as F2 | same as F2 | no type guards | LOW: exceptions instead of rejection | typed checks + exception guard → `False` | `test_f4_merkle_verify_malformed_returns_false`, inside the 15/15 above |
| **F5** Mode B `encode` truncated/padded domains; `parse` accepted `bytearray`; wrong types raised `TypeError` | `hidden_signer_modeB_v1.50.py` | `hidden_signer_modeB_v1.51.py` | `struct '64s'` silently truncates or pads; no type guard on frame or proof | LOW (research code, never deployed on a node): a late `domain mismatch` instead of a canonical rejection | canonical 64-byte `bytes` domain, `bytes` proof, `bytes` frame, all as `ModeBError` | `test_f5_domain_canonicality`, `test_f5_parse_requires_bytes`; 7/7 (5 original + 2) |

## 2. F3 resolved against the specification, not by agreement

RFC 8554 §5.1 says the two hash functions SHOULD be the same and is silent on n vs m; SP 800-208 §4
Tables 1–8 list approved LM-OTS sets with n ∈ {24, 32} and LMS sets with m ∈ {24, 32} and pair
same-hash sets — a mixed n ≠ m pair is **not an approved set**. Verdict: on approved sets both
implementations agree (80/80); on non-approved mixed sets our implementation is self-consistent
while hsslms 0.1.3 is not (`_calc_leafs` truncates leaves to n, `_calc_knots`/`verify` use m).
Status: **resolved for approved sets; an unresolved interoperability discrepancy on non-approved
sets, reported upstream**, with our fix refusing the non-approved sets outright.

## 3. Not fixed, documented

- The nine end-of-`main()` demo allocations in `modeB_prover_v1.5x.c` (33.6 MB reported by LSan at
  exit) are program-exit leaks in the demo driver, not in `verify()`; the `verify()` path is clean in
  v1.51. They would matter only for a long-lived library embedding, where the fix is a `qmap_free`
  at shutdown.
- The 32 KiB cap of B0 is enforced on verification, not at encoding (F6, an observation).

## 4. Two contradictions in the source, and what this repository reports

**K12 / A28 — the "16/16 and 16/16".** The v0.2 ledger's fix-stage step 1 and the stack README both
record the property layer re-run against the fixed files as "16/16 and 16/16 (was 11/16 and 14/16)",
and the archived `fixes/property_fixed/hashsig_fixed.log` agrees at first glance. Re-running
`fixes/property_fixed/test_props_hashsig_fixed.py` against the fixed files **fails at collection**:
the module aborts at import on the mixed m ≠ n pair, so **zero tests run** for the hash-signature
half. The exact error is quoted in `VERIFICATION.md`. The Mode B half is sound
(`test_props_modeB_fixed.py`: 16 passed). Following records entry A28 and the standing correction,
this domain **withdraws the "16/16 and 16/16"** and reports: Mode B 16/16; hash-signature not
collected → 0/16, hypothesis not exercised.

**K11 — the v1.51 "7/7" against its archived log.** `fixes/hidden_signer_modeB_v1.51.py.log` records
the fixed Mode B file as 7 tests with **1 ERROR** (`TypeError: object of type 'int' has no len()` in
`H`, reached through `cfg_of`). A fresh run of
`python3 $PQT_SRC/hidden_signer_modeB_v1.51.py --self-test` gives:

```
Ran 7 tests in 23.041s
OK
```

The log is an **earlier, still-failing iteration** of the same file, and the evidence for that is
twofold: the failure is inside the fix's own new test (`test_f5_parse_requires_bytes`, line 343 of
the fixed file, failing in `encode` → `cfg_of` → `H`), i.e. it is a defect of the fix's first
attempt rather than of the frozen reference; and the source archive's file metadata puts the log at
`2026-09-13 03:55:53` and the fixed file's last write at `03:56:30` — the log is 37 s older than the
file it records. The published copy of the log carries the assembly's copy time, so the mtimes are
quoted from the source archive (recorded in `VERIFICATION.md`) rather than from the file in
`fixes/`. Both facts are kept: the archived log as recorded, the fresh run as observed, and this
reading as the explanation. The F5 regression result quoted in the table above is the fresh one.

## 5. Where the fixed files live

The four fixed files are published in the domains that own them (see the table and
`docs/inputs-and-provenance.md` §2); the fix logs and the two fixed-file property suites travel with
this stack under `fixes/`:

| file | content |
|---|---|
| `fixes/make_fixes.py` | the derivation script (exact single-match replacement; aborts on drift; writes into the research tree) |
| `fixes/hidden_signer_modeB_v1.51.py.log` | the archived, contradictory self-test log (K11) |
| `fixes/pq_audit_s1_lms_v2.2.py.log`, `fixes/pq_infra_s1s2_hashsig_dnssec_v2.2.py.log` | the fixed Python files' self-test logs (12/12, 15/15) |
| `fixes/property_fixed/test_props_modeB_fixed.py`, `…_hashsig_fixed.py` + `modeB_fixed.log`, `hashsig_fixed.log` | the property suites re-pointed at the fixed files, and their logs |

## 6. Limits

- The fixes are regression-tested, not proven: each repairs the specific defect its finding names,
  with tests that reproduce it first and pass afterwards. No claim is made that v1.51 is defect-free.
- F1's production-parameter confirmation is on **v1.50** (the reference); v1.51's fix was verified at
  reduced parameters only, and production ASan on v1.51 was not run (recorded as such).
- F2/F4 are fixes to a module that is not deployed by this stack; they are offered as the audited
  module's correction, without any claim about a caller this stack has not seen.
