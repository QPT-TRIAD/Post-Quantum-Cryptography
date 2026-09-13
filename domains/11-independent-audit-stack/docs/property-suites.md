# Property, differential and malformed-input suites

Engine: Hypothesis 6.151 with the profile `audit` (`deadline=None`, `derandomize=True`,
`print_blob=True`, all health checks suppressed) — deterministic by construction, which is why the
recorded counts are stable across machines. Differential target: `hsslms` 0.1.3, an independent
RFC 8554 implementation. Run: `bash property/run_all.sh` (recorded 3.6 min; logs under
`property/logs/`). Targets are imported read-only from the research tree (`PQT_SRC`, see
`docs/inputs-and-provenance.md`); the harness sets `sys.dont_write_bytecode = True` so nothing is
written into that tree.

## 1. Recorded results, per file

| file | pass | fail | what it tests |
|---|---|---|---|
| `test_props_b0.py` | 12 | 0 | conflict extraction == bitmap intersection + verified blames (250 examples); non-conflicts rejected (160); encode→parse round trip (100); single-byte mutation: 500 Hypothesis + **exhaustive 17,160 mutants, all raising `CertError`**; malformed catalogue 105/105 rejected. Accept-on-invalid: none. |
| `differential_b0.py` | — | 0 disagreements | the spec-only re-implementation (`independent-b0/b0_indep.py`) vs `extract_b0` / `verify_blame_b0` on **2,200 pairs** (uniform / natural / minimal 22 / full 43 / 42 overlap, single-bit and disjoint bitmaps, same message, other domain, cross-registry, corrupted signature, swapped slots): 5,632 blame checks, 0 disagreements |
| `test_props_modeB.py` | 14 | 2 | round trip; extraction completeness with true openings; symmetry; non-aborting extraction; non-conflicts; the 64-byte message rule; `Challenge` linear/invertible with a minimal counter (smaller counters proven singular); kernel dim ≤ 2 (300 examples at n = 32; 11 triples at n = 256, dims `[2,0,0,0,2,0,1,0,0,0,0]`); `solve_f2` returns exactly the kernel |
| `test_props_hashsig.py` | 11 | 5 (3 findings) | Merkle/WOTS round trip, exhaustion, every auth-path/OTS/index tamper; MTL condensed + multiproof mutations (remove leaf, swap coordinates, foreign node, changed leaf, extra leaf); LMS round trip, every byte/path/q/typecode tamper, exhaustion; **differential LMS vs hsslms on 100 cases** |
| `test_props_tesla.py` | 8 | 2 xfail (known S4-004 / S4-005) | genuine accepted iff sync < d; interleaved forgeries never accepted and never block the genuine packet; body/MAC bit flips; replay; late; range; 200 random packets |
| `property/logs/summary.txt` | — | — | one line per file: `tesla 8 passed, 2 xfailed`; `b0 12 passed`; `hashsig 5 failed, 11 passed`; `modeB 2 failed, 14 passed`; `differential swapped_slots n=100 agree=100 accepted_by_both=0` |

The five hash-signature failures and the two Mode B failures are the *findings*, deliberately left
failing in the frozen targets; they are the F2/F4 and F5 inputs to `fixes/`. `run_all.sh` ends with
`|| true` on the summary line, so the layer always exits 0 — the pass/fail counts above are the
result, not the exit code.

## 2. Findings

- **H1 (= F3) — MEDIUM, upstream, an independent implementation's bug.** 80/100 LMS cases agree in
  both directions; the 20 disagreements are exactly the mixed typecode pairs (LMS m = 32 with LM-OTS
  n = 24 and m = 24 with n = 32). Minimal example `pair=(5,8), msg=b''`: our signature 820 B
  (formula), hsslms 812 B; ours→ours True, ours→hsslms True, **hsslms→hsslms False, hsslms→ours
  False**. Root cause in `hsslms/lms.py`: `_calc_leafs` truncates leaves to the OTS `n` while
  `_calc_knots`/`verify` use `m`, so hsslms's signer emits a path its own verifier rejects. Our
  implementation is self-consistent. **Neither implementation refused n ≠ m at keygen** although
  SP 800-208 pairs n with m — a LOW finding on ours, fixed in v2.2.
- **H3 (= F2) — LOW/MEDIUM, our code, `MTLMultiproof.verify`.** `verify(roots, rungs, leaves, {})`
  returns **True** (vacuous accept of an empty proof); an out-of-range leaf or unknown rung raises
  `IndexError`, a malformed node raises `ValueError` instead of returning False; an extra unused node
  is accepted (the S2 audit's independent verifier rejects it). Fixed in v2.2 by requiring the proof
  to cover an explicit requested leaf set and returning False on any structural defect.
- **H2 (= F4) — LOW, our code, `merkle_verify`.** Raises `AttributeError` / `TypeError` / `KeyError`
  instead of returning False for idx float/str/None, missing keys, an int OTS element, `{}`. Fixed in
  v2.2.
- **M1 (= F5) — LOW, Mode B v1.46/v1.50, research code.** `encode` accepts 63-/65-byte domains:
  `struct '64s'` truncates or pads, so the header domain ≠ the challenge domain and the frame only
  fails later with `domain mismatch`. Same class as the v1.50 message-canonicality fix. Fixed in
  v1.51.
- **M2 — LOW, Mode B.** `parse` accepts a `bytearray` frame (extraction then dies with `TypeError`);
  `memoryview`/str/None/int raise `TypeError` rather than `ModeBError`. By design (structure-only,
  no proof backend) unregistered handles and trailing proof bytes parse; the tests verify that
  `extract`/`verify_blame` never name a seat through them (25-case catalogue rejected).
- **Observation (F6), B0.** `encode_b0` will emit a frame above 32 KiB for a 758-byte width
  (32,810 B) while `verify_b0` rejects it, as the v1.44 demo expects — the size cap is enforced on
  verification, not at encoding. Documented, not fixed.
- **Known-bug reproductions.** S4-004 (a packet carrying K₅ is lost: K₃ = H(K₄) is provably known yet
  interval 3 stays stranded) and S4-005 (an attacker pre-sends the predicted body with a junk MAC;
  the genuine packet is dropped as a "replay" — no key needed) reproduce as `expectedFailure`.
  Supporting observation: the receiver's `seen`/`pending` sets grow per unauthenticated packet.

## 3. The mutation count: 17,160, not 17,660

The v0.1 and v0.2 ledgers both record **17,660** exhaustive single-byte mutants (claim C12); the
property layer's own findings record **17,160**, and the number the test computes is 17,160:
3 XOR masks (`0x01`, `0x80`, `0xFF`) over a 5,720-byte frame (208-byte header + 8 + 43 × 128-byte
votes) = 17,160. The ledger's figure is not divisible by 3 and therefore cannot be produced by that
loop at all; the code-verified value is the one used here. The ledger is left as recorded — this is
a correction (K14) reported in `VERIFICATION.md`, not an edit to the source.

## 4. The withdrawn "16/16 and 16/16" (A28), and the fixed-file re-run

Both the v0.2 ledger (step 1 of §3b) and the stack README record the property layer re-run against
the *fixed* files as **16/16 and 16/16** (from 11/16 and 14/16). Records entry A28 and the archived
log withdraw that: `fixes/property_fixed/hashsig_fixed.log` stops at import with a failure, and a
re-run of `fixes/property_fixed/test_props_hashsig_fixed.py` against the fixed files fails at
**collection** — the hash-signature module aborts at module level (0 tests run) on the mixed m ≠ n
typecode pair, with the exact error quoted in `VERIFICATION.md`. The Mode B half is sound:
`test_props_modeB_fixed.py` passes 16. The correct statement is therefore: **Mode B 16/16,
hash-signature 0 collected (withdrawn), not "16/16 and 16/16"** — this domain reports the
withdrawn form, per the standing correction.

## 5. Limits

- The B0 tests use the module's symbolic signature double (framing, set and blame logic — not a
  scheme). The fault layer's signatures are the same double. Nothing here validates ML-DSA.
- hsslms is exercised only at H5 typecodes with `num_cores=1`.
- Mode B extraction is capped at 20 Hypothesis examples (≈2.7 s each), so the Mode B properties are
  sampled, not exhaustive.
- Harness bugs found and fixed before the final run (not target findings, recorded in the layer's
  findings file): the TESLA attacker was handed an undisclosed key; an empty-path "short path" case
  was a no-op; stale cached LMS signatures survived a corpus shrink.
