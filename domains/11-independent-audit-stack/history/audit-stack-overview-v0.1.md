# AUDIT_STACK.md — QPT-128 / CE-QS independent audit stack v0.1, results ledger

Date: 2026-09-11 (evening). Method: every layer attempts to **disprove** a claim with a
counterfactual; the ledger records the claim, the attack, the verdict, and what the
verdict does *not* mean. "Executed here" = run natively on the authoring host; layers
whose tool is absent are marked NOT RUN and are wired into the `Dockerfile`.

## 0. One-line status per layer

| layer | tool | executed here | verdict |
|---|---|---|---|
| Mathematics (M1–M8) | SymPy 1.13, galois 0.4.11 (SageMath: Docker only) | yes, 217 s | **8/8 reproduced**; every counterfactual behaved as theory predicts |
| Protocol, bounded checker (3rd model) | Python exhaustive | yes, 0.45 s | boundary at C = 2q−N confirmed for N = 4, 5, 7, 10; min intersection exactly 2q−N; no honest seat ever named; every corrupt subset enumerated for N ≤ 7 |
| Protocol, Tamarin | 1.12.0 + Maude 3.5.1 (binaries; `tamarin-prover test` 55/55) | yes: N = 4 in 111 s (`-M2500m`); N = 7 partial | **N = 4: all 12 lemmas verified** (A1/A2/A, B, C1/C2/C3, D1/D2, E1/E2, sanity), none falsified or weakened; **N = 7: 6 verified** (sanity, A1, A2, D2, D2b, C3), A/B/C1/E2/D1 not completed (heap/timeouts), nothing falsified |
| Protocol, ProVerif | absent (Docker: opam) | no | model written, **unexecuted** |
| Primitives | liboqs 0.16.0, dilithium-py 1.4.0, kyber-py 1.2.0, NIST ACVP | yes, 38 s | **0 disagreements** over 25+25 keyGen, 60 sigVer, 120 sigGen, 55 encapDecap, 800 cross-ops, 200 tampers |
| Implementation | clang-18 ASan/UBSan/MSan, libFuzzer | yes (reduced params) | **1 leak (F1)**, 0 memory errors, 0 UB, **81,041 fuzz execs: 0 crashes, 0 accept-on-invalid** |
| Property / differential / malformed | Hypothesis 6.151, hsslms 0.1.3 | yes, 3.6 min | B0: 17,660 mutants + 105 malformed all rejected, 2,200-pair differential 0 disagreements; **findings F2–F5** |
| Fault injection | Python, 11 fault classes | yes | 300 schedules, 1,717 checks, 3,700 corruptions rejected, 33 conflicts extracted, **0 failures** |
| Devnet (other repository) | 64-seat sweep + 4-node matrix | yes | sweep `complete: true`, 28/28 points, **measured threshold 22 = 2q−N**; matrix complete |
| Independent implementation | — | partial | B0 extraction rule (spec-only re-implementation, 0 disagreements) and LMS (hsslms) only |
| EasyCrypt | — | deferred | not started, by design |

## 1. Claims, counterfactuals, verdicts

| # | claim | counterfactual attempted | result | verdict | does not mean |
|---|---|---|---|---|---|
| C1 | \|Q₁∩Q₂\| ≥ 2q−N; 22 at (64,43) | SymPy solve + exhaustive split search N = 4..64; bounded protocol checker N = 4,5,7 all C | no counter-example; threshold exact at every N | **reproduced** | — (counting theorem) |
| C2 | CFHL collision cost 2^81.7 queries (256-bit), 2^252.4 (768-bit) | solve 80e²(q+1)³2^-n + 4·2^-n = 1/3 symbolically | 81.74 / 252.40; module's own bound at that q = 0.3333 | **reproduced** | the CFHL constant is the paper's |
| C3 | unprefixed Merkle nodes at n=256, T=2^40 cost 2^126 gates (< 2^128) | symbolic crossover; classical & quantum multi-target experiments | crossover at **T = 2^36**; slopes shared −1.08 / prefixed −0.06 (classical), −0.51 (Grover with T marked) | **reproduced** (S2-006 regression) | prefixed nodes are only 2^146 under the same accounting |
| C4 | kernel of D(s)=αs+βs²+γs⁴ has dim ≤ 2 | exhaustive GF(2^4) 4,095 triples, GF(2^6) 262,143, random GF(2^8)/GF(2^12); s⁸ term; non-linearized s³ | max dim 2 (tight); s⁸ → dim 3 appears; s³ affine fibers {0,1,3} (never cosets, 9,756/20,000) | **reproduced** | says nothing about GF(2^256) being special — it is field-independent |
| C5 | SUPPRESS needs equality of all three challenge coefficients (2^-3m) vs one (2^-m) | measured collision counts m = 3..6 | slopes −3.03 / −1.00 | **reproduced** | — |
| C6 | Grover: 2^(n/2) iterations, single target | exact simulation n = 8..18, independent fit | k_measured = k_predicted at every n; slope 0.505 | **reproduced** | validates scaling only; no 128/256-bit attack executed |
| C7 | FRAME on B0 = one signature forgery (tight) | toy PoW signature, brute-force forge for an honest seat, insert into the conflicting frame | frame succeeds exactly when the forgery is found; slope 0.98 in bits | **reproduced** (and shows frameability = EUF-CMA of the profile) | toy scheme; ML-DSA-87's 2^148 is an assumption (A-sig) |
| C8 | EVADE impossible on B0 (public bitmap) | exhaustive signer-set pairs N = 7 | 0 pairs below 2q−N; every double-signer in the intersection | **reproduced** | structural, no cryptography |
| C9 | GF(2^256) arithmetic of the reference is correct | galois with the same polynomial; 400 random mul/inv/x⁷/⁷√; toy fields 8/10/16 | 0 mismatches; polynomials irreducible by galois | **reproduced** | — |
| C10 | ML-DSA-87 / ML-KEM-1024 implementations are correct | three implementations vs NIST ACVP; tamper 200× | 0 disagreements; negative control caught 27/27 | **reproduced** | validates primitives, not the construction |
| C11 | the C prover/verifier is memory-safe and rejects every mutant | ASan/UBSan/MSan; libFuzzer with accept-on-invalid abort | **leak F1** on the grinding early-exit; 0 crashes; 0 accept-on-invalid in 81,041 execs | **partially disproved** (F1) | reduced parameters; verify() never reads the 208-B header (Python layer does) |
| C12 | B0 encode/parse/extract/blame reject every malformed input | 17,660 exhaustive single-byte mutants; 105-case catalogue; 500 Hypothesis mutants | all rejected | **reproduced** | symbolic signature double |
| C13 | B0 extraction equals its specification | spec-only re-implementation, 2,200 pairs, 5,632 blame checks | 0 disagreements | **reproduced** | partial independent implementation (extraction rule only) |
| C14 | MTL multiproof verifier rejects every malformed proof | empty proof; extra node; type garbage | **empty proof accepted (vacuous True); extra unused node accepted; exceptions instead of False** | **disproved (F2)** | fix: require the requested leaf set; return False on structural defects |
| C15 | RFC 8554 LMS implementation agrees with an independent one | hsslms both directions, 100 cases | 80/100 agree; 20 mixed-typecode cases: **hsslms fails its own round trip**; ours accepts non-standard m≠n pairs | **independent impl. bug (F3)**; ours: LOW | SP 800-208 pairs n with m; refuse mixes at keygen |
| C16 | Mode B research code validates inputs canonically | 63/65-byte domains; bytearray; wrong types | truncation/padding accepted; bytearray accepted | **disproved (F5, LOW)** | research code, never on a node |
| C17 | TESLA receiver: liveness under loss; replay filter safe | known S4-004/S4-005 | reproduced as expected failures | **known, fixed in `FixedTeslaReceiver`** | — |
| C18 | Pipeline under faults: reject invalid, live when expected, no false blame, no lost evidence, no contradictory acceptance | 300 seeded schedules over 11 fault classes | 0 failures; 3,700 corruptions rejected; 33 conflicts fully attributed; rollback of one replica cannot un-name | **reproduced** | toy signatures; single-process model |
| C19 | 43-of-64 accountability under real consensus; threshold 22 | 64-seat sweep C = 0..26 + one-sided | 28/28 passed; C-21 no pair (503 + 44 > 43); C-22 pair, 22 named, 0 honest | **reproduced on the devnet** | a devnet result is never a security level |
| C20 | protocol properties A–E hold | Tamarin N=4 (12 lemmas) and N=7 (partial); ProVerif (unexecuted); bounded checker N=4,5,7,10 | Tamarin N=4: A–E all verified incl. E2's explicit attack trace at C=2 (forged s0,s1 with leaked keys + honest s3); N=7: 6 verified, none falsified; checker: boundary exact, honest never named | **two independent models agree; ProVerif unexecuted** | N=4/7 proofs reach N=64 only through the same counting theorem; a first D2 lemma with the wrong corruption ordering was caught before running (modelling artifact, not a property violation) |

## 2. Findings register (this stage)

| id | severity | where | what | status |
|---|---|---|---|---|
| F1 | rank-3 resource | modeB_prover_v1.50.c `verify` 803→815 | `circ_pub_t *P` (9,568 B) leaked on grinding-condition early return; reproducible with seed `A_zero` | open (reference frozen); fix in any production port |
| F2 | MEDIUM | pq_infra_s1s2 `MTLMultiproof.verify` | empty proof → True; extra node accepted; exceptions instead of False | open; must take requested leaves |
| F3 | MEDIUM (upstream) / LOW (ours) | hsslms 0.1.3; pq_audit_s1 | hsslms self-inconsistent on mixed m≠n typecodes; ours accepts non-standard mixes | report upstream; refuse mixes |
| F4 | LOW | pq_infra_s1s2 `merkle_verify` | raises on malformed objects | return False |
| F5 | LOW | Mode B v1.46/v1.50 | domain truncation/padding; bytearray accepted | canonical checks |
| F6 | observation | sidecar v1.44 | 32 KiB cap enforced on verify, not encode | documented |
| — | observation | modeB_prover_v1.50.c | verify() does not read the 208-byte frame header (the Python layer parses it) | design note |

Harness mistakes of this stage (A22–A26) are in `reference/FAILED_ASSUMPTIONS.md`.

## 3. What the stack can say now

- **Mathematical claims:** independently reproduced (SymPy + galois; SageMath pending in Docker).
- **Protocol properties:** formally modelled and verified in Tamarin at N = 4 (12/12 lemmas), partially at N = 7 (6 verified, none falsified), and bounded-checked exhaustively at N = 4, 5, 7, 10 by an independent third model; ProVerif model written, unexecuted.
- **Primitive implementations:** independently tested (three implementations + ACVP, 0 disagreements).
- **Implementation:** fuzzed and sanitizer-tested at reduced parameters; one leak found.
- **Security games:** experimentally attacked at reduced sizes (FRAME, SUPPRESS, EVADE, SAFETY, multi-target, Grover).
- **Concrete bounds:** independently recomputed (all match).
- **Devnet:** adversarially exercised (28/28 sweep points; matrix complete).
- **Known failures:** documented and regression-tested (F1–F6, A22–A26, plus the 35 earlier entries).
- **Independent implementation:** cross-validated for the B0 extraction rule and LMS only — the full second implementation remains open.

## 4. Not done / next

Tamarin N = 7 remaining lemmas (A, B, C1, E2, D1: need > 4 GB or a leaner theory), ProVerif run, SageMath re-run (Docker),
production-parameter sanitizer run, KLEE on `verify/extract`, valgrind, AFL++ campaign,
EasyCrypt game hops, a from-spec second implementation of the whole construction, and the
KEY_ROLLBACK/STALE_STATE/MULTI_TARGET devnet scenarios of the v2.1 kit.
