# Property / differential / malformed-input layer — findings (2026-09-11)

Targets imported read-only from the research tree (`PQT_SRC`). Engines: Hypothesis 6.151, hsslms 0.1.3
(independent RFC 8554). Run: `./run_all.sh` (~3.6 min). Logs under `logs/`.

## Per file

| file | pass | fail | what was tested |
|---|---|---|---|
| test_props_b0.py | 12 | 0 | conflict extraction == bitmap intersection + verified blames (250 examples); non-conflicts rejected (160); encode→parse round trip (100); single-byte mutation: 500 Hypothesis + **exhaustive 17,160 mutants, all raise CertError**; malformed catalogue 105/105 rejected. **Accept-on-invalid: none.** |
| differential_b0.py | — | 0 disagreements | spec-only re-implementation vs `extract_b0`/`verify_blame_b0` on **2,200 pairs** (uniform / natural / minimal 22 / full 43 / 42 overlap, single-bit and disjoint bitmaps, same message, other domain, cross-registry, corrupted signature, swapped slots); **5,632 blame checks, 0 disagreements** |
| test_props_modeB.py | 14 | 2 | round trip; extraction completeness with true openings; symmetry; non-aborting extraction; non-conflicts; 64-byte message rule; `Challenge` linear/invertible/minimal counter (smaller counters proven singular); kernel dim ≤ 2 (300 examples at n = 32; 11 triples at n = 256, dims [2,0,0,0,2,0,1,0,0,0,0]); `solve_f2` returns exactly the kernel |
| test_props_hashsig.py | 11 | 5 (3 findings) | Merkle/WOTS round trip, exhaustion, every auth-path/OTS/index tamper; MTL condensed + multiproof mutations (remove leaf, swap coordinates, foreign node, changed leaf, extra leaf); LMS round trip, every byte/path/q/typecode tamper, exhaustion; **differential LMS vs hsslms 100 cases** |
| test_props_tesla.py | 8 | 2 xfail (known S4-004/S4-005) | genuine accepted iff sync < d; interleaved forgeries never accepted and never block genuine; body/MAC bit flips; replay; late; range; 200 random packets |

## Findings (a failing property is the product)

- **H1 — MEDIUM, differential (independent implementation bug).** 80/100 LMS cases agree both ways; the **20 disagreements are exactly the mixed typecode pairs (LMS m=32 + LM-OTS n=24) and (m=24 + n=32)**. Minimal example `pair=(5,8), msg=b''`: our signature 820 B (formula), hsslms 812 B; ours→ours True, ours→hsslms True, **hsslms→hsslms False, hsslms→ours False**. Root cause in `hsslms/lms.py`: `_calc_leafs` truncates leaves to the OTS `n` while `_calc_knots`/`verify` use `m`, so hsslms's signer emits a path its own verifier rejects. Our implementation is self-consistent. **Neither implementation refuses n ≠ m at keygen** although SP 800-208 pairs n with m — a LOW finding on ours.
- **H3 — LOW/MEDIUM (our code, `pq_infra_s1s2` `MTLMultiproof.verify`).** `verify(roots, rungs, leaves, {})` returns **True** (vacuous accept of an empty proof); out-of-range leaf / unknown rung raise IndexError and a malformed node raises ValueError instead of returning False; an extra unused node is accepted (the S2 audit's independent verifier rejects it). Fix: require the proof to cover an explicit set of requested leaves and return False on any structural defect.
- **H2 — LOW (our code, `merkle_verify`).** Raises AttributeError/TypeError/KeyError instead of returning False for idx float/str/None, missing keys, an int OTS element, `{}`.
- **M1 — LOW (Mode B v1.46/v1.50, research).** `encode` accepts 63-/65-byte domains: `struct '64s'` truncates/pads, so the header domain ≠ the challenge domain and the frame only fails later with `domain mismatch`. Same class as the v1.50 message-canonicality fix.
- **M2 — LOW (Mode B).** `parse` accepts a `bytearray` frame (extraction then dies with TypeError); memoryview/str/None/int raise TypeError rather than ModeBError. By design (structure-only, no proof backend) unregistered/corrupted handles and trailing proof bytes parse; verified that `extract`/`verify_blame` never name a seat through them (25-case catalogue rejected).
- **Observation (B0).** `encode_b0` will emit a frame above 32 KiB for a 758-byte width (32,810 B); `verify_b0` rejects it, as the v1.44 demo expects — the size cap is enforced on verification, not at encoding.
- **Known-bug reproductions.** S4-004 (packet carrying K₅ lost: K₃ = H(K₄) is provably known yet interval 3 stays stranded) and S4-005 (attacker pre-sends the predicted body with a junk MAC; the genuine packet is dropped as "replay" — no key needed) reproduce as `expectedFailure`. Supporting observation: the receiver's `seen`/`pending` sets grow per unauthenticated packet.

## Limits

B0 tests use the module's symbolic signature double (framing/set/blame logic, not a scheme);
hsslms only at H5 typecodes with `num_cores=1`; Mode B extraction capped at 20 Hypothesis
examples (2.7 s each). Harness bugs found and fixed before the final run (not target findings):
the TESLA attacker was handed an undisclosed key; an empty-path "short path" case was a no-op;
stale cached LMS signatures after shrinking the corpus.
