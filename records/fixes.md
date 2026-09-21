# FIXES_v2.2 — audit-fix release for findings F1–F5 (2026-09-13)

Rule followed: the reference files are immutable audit history (their hashes are in
`triad-pq-devnet-v2.1/reference/HASHES.sha256`). Every fix is a NEW file derived from
its reference by exact, verified string replacement (`qpt_audit_stack/fixes/make_fixes.py`
aborts unless each pattern matches exactly once), with regression tests inside the new file.

| finding | reference (immutable) | fixed file | root cause | security impact | fix | regression | re-run |
|---|---|---|---|---|---|---|---|
| **F1** LSan leak in `verify()` | `modeB_prover_v1.50.c` | `modeB_prover_v1.51.c` | grinding-condition check returned before `free(P)` (`circ_pub_t`, 9,568 B) | rank-3 resource: a stream of rejected proofs leaks one `P` each in a long-running verifier; no acceptance impact | `free(P)` on that path (one line) | ASan+LSan reduced run: **0 leak frames in `verify`** (v1.50 run: 1 frame, 19,136 B in 2 objects); self-test verified/tampered-rejected/extracted unchanged | `implementation/production/v151_lsan_reduced.txt`, `v151_functional_reduced.txt` |
| **F2** vacuous accept of an empty multiproof; extra node accepted; exceptions instead of False | `pq_infra_s1s2_hashsig_dnssec_v2.0.py` | `pq_infra_s1s2_hashsig_dnssec_v2.2.py` | `verify` looped over zero rungs and never checked that the supplied node set equals the exact sibling set | MEDIUM: an "authorization object" proving nothing could be accepted by a caller that does not check coverage; extra nodes allowed malleable proofs | `verify(..., required=None)`: non-empty dict, typed rungs/leaves/nodes, supplied nodes == needed siblings (no extra, no missing, no duplicates), optional required-leaf coverage, structural defects → False | 5 new tests (`AuditFixTests`): empty/None/empty-rung, extra/missing/duplicate node, required coverage, malformed inputs, plus all 10 original tests | `pq_infra_s1s2_hashsig_dnssec_v2.2.py --self-test`: 15/15; property layer re-run against v2.2: 16/16 (was 11 pass / 5 fail) |
| **F3** mixed LM-OTS n / LMS m accepted; hsslms self-inconsistent on them | `pq_audit_s1_lms_v2.1.py` | `pq_audit_s1_lms_v2.2.py` | neither implementation refused non-approved combinations | LOW (ours): non-standard parameter sets accepted; MEDIUM (hsslms): its own round trip fails | `approved_pair()`: LMS m must equal LM-OTS n (SP 800-208 §4 approved sets; RFC 8554 §5.1 "the two hash functions SHOULD be the same", silent on n = m); refused at keygen (ValueError) and at verify (False) | `S1-012`; interop tests unchanged on approved sets (80/80 agreement) | 12/12; property differential 100/100 on approved sets |
| **F4** `merkle_verify` raised on malformed input | same as F2 | same as F2 | no type guards | LOW: exceptions instead of rejection | typed checks + exception guard → False | `test_f4_merkle_verify_malformed_returns_false` | in the 15/15 above |
| **F5** Mode B `encode` truncated/padded domains; `parse` accepted `bytearray`; wrong types raised TypeError | `hidden_signer_modeB_v1.50.py` | `hidden_signer_modeB_v1.51.py` | `struct '64s'` silently truncates/pads; no type guard on frame/proof | LOW (research code, never on a node): late `domain mismatch` instead of a canonical rejection | canonical 64-byte `bytes` domain, `bytes` proof, `bytes` frame, all as `ModeBError` | `test_f5_domain_canonicality`, `test_f5_parse_requires_bytes` | 7/7 (5 original + 2); property layer re-run against v1.51: 16/16 |

**F3 resolution (against the specification, not by agreement):** RFC 8554 §5.1: "these two hash
functions SHOULD be the same"; the RFC is silent on n vs m. SP 800-208 §4 Tables 1–8 list
approved LM-OTS sets with n ∈ {24, 32} and LMS sets with m ∈ {24, 32} and pairs same-hash sets;
mixed n ≠ m is not an approved set. Verdict: on approved sets both implementations agree
(80/80); on non-approved mixed sets our implementation is self-consistent and hsslms 0.1.3 is
not (`_calc_leafs` truncates leaves to n, `_calc_knots`/`verify` use m). Status:
**RESOLVED for approved sets; UNRESOLVED INTEROPERABILITY DISCREPANCY on non-approved sets,
reported upstream**; our fix refuses the non-approved sets outright.

**Not fixed (documented):** the 9 end-of-`main()` demo allocations in `modeB_prover_v1.5x.c`
(33.6 MB reported by LSan) are program-exit leaks in the demo driver, not in `verify()`; the
`verify()` path is clean in v1.51. The 32 KiB cap of B0 is enforced on verification, not at
encoding (F6, observation).

Regeneration: `python3 qpt_audit_stack/fixes/make_fixes.py` (aborts on any pattern drift).

## Correction (2026-09-13, evening)

The property-layer line above stated 16/16 for both fixed files. A re-run in a rebuilt environment
gives **16 passed for Mode B**, but the **hash-signature property module fails at collection
(0 tests executed)**: it constructs a mixed m ≠ n LMS key at import, which the F3 fix correctly
refuses. The hash-signature "16/16" is withdrawn; see `FAILED_ASSUMPTIONS.md` A28. The Mode B v1.51
self-test re-runs 7/7.

## Correction (2026-09-21): position-prefixed Merkle nodes, and the category table's provenance

Two defects recorded by the v2.1 audit but left unrepaired in the constructions have now been
repaired, and one attribution has been corrected.

**S2-006, position-prefixed node hashing, applied to the design files.** The audit measured that
interior nodes hashed as `H('node', l, r)` carry no position commitment, so an adversary facing `T`
structures signed under one key tests one hash evaluation against all `T` at once. At n = 256 with
T = 2^40 the ledger's own formula gives 128 - 20 + 18 = 2^126 gates, inside the 2^128 budget: the
construction as built failed its own target, against 2^146 for the prefixed variant. The fix had been
implemented inside the S2 audit file only (`prefixed_multiproof_build` / `prefixed_multiproof_verify`)
and the verification record stated it was not applied to the constructions. It is now applied, using
the convention `H('node', <structure id>, level, parent index, l, r)`, with the structure id being the
rung for the ladder, the public seed for the tree, and the batch id for the certificate batch:

| file | sites | structure id |
|---|---|---|
| `s1s2_hashsig_dnssec.py` | tree construction and verification, ladder construction and verification, multiproof verification | public seed, rung |
| `s3_tls_pki.py` | batch construction and verification | batch id |
| `s5_smartcard_hsm.py`, `s5_bds_faults.py` | traversal, authentication path, root, verification | per-device seed |

The tree in S1 needed the fix and did not have it: the leaf address reached the chain and compression
functions only, so interior nodes of every key pair shared one function. The preserved v2.0 file is
deliberately unchanged, since it is the record of what v2.0 was. Wire sizes are unaffected, the fix
being zero bytes; three hash-call counts moved and are recorded rather than re-recorded — the S1
verify count in `docs/studies.md` §1.5 and the two S5 composition means in §5.5 of the same file. In
each case the position prefix changed the tree root, the message digest is a function of the root,
and the number of chain steps is a function of the digest, so the count is a draw and not a constant;
every count that is counted rather than drawn, and every byte count, is unchanged. The new tests were
checked against a copy with only the hashing reverted, and fail there.

**The category table is a floor, not a lattice cost.** `CATEGORY_ATTACK_GATES = {1: 83, 2: 100,
3: 116, 5: 148}` was read as the cost of the reference attack on the deployed lattice schemes. The
values are NIST's category definitions: 64+19, 96+20 and 128+20, Grover key search on AES-128, AES-192
and AES-256. The figure 148 does appear in the v1.43 constants table, correctly labelled there as an
AES-256 oracle at 1.17 * 2^148 gates with its citation; what was wrong was re-using it downstream
under the heading "Category-5 reference attack" for ML-KEM. The entries 83, 100 and 116 appear in
that source nowhere. The rows now name the floor and say what it is not, and an independent estimator
run at full scale is recorded in `domains/13-lattice-reduction-stress/results/infra-2026-09-21/`:
every deployed parameter set clears its floor, and ML-KEM-512 sits below the 2^128 budget.

**Not regenerated, deliberately.** `records/audit-checklist.md`, `records/audit-ledger.json` and the
copies under `domains/10-digital-infrastructure/results/` still carry the string `v1.43 ledger` at the
rows above. They are the dated artifacts of the v2.1 release and record what that run produced;
rewriting them would make the register disagree with the release it documents. The sources they were
produced from are corrected, so a regeneration under the v2.2 sources will not reproduce them, and
that is the expected difference rather than a fault.
