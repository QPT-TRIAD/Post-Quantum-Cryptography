# qpt128_audit_stack — independent audit of QPT-128 / CE-QS (v0.2: v0.1 + fix stage + production sanitizers, 2026-09-13)

Seven independent layers, each trying to **disprove** a claim with a
counterfactual rather than confirm it. Results and the claim-by-claim ledger
are in `AUDIT_STACK.md`; the permanent failure log (including this stack's own
harness mistakes) is `reference/FAILED_ASSUMPTIONS.md` in the project.

```
MATHEMATICS   math/math_layer.py          SymPy + galois (SageMath in Docker)   M1–M8
PROTOCOL      formal/                     Tamarin (1.12.0 + Maude 3.5.1), ProVerif model, bounded checker (3rd model)
PRIMITIVES    primitives/cross_validate.py liboqs 0.16.0 vs dilithium-py/kyber-py vs NIST ACVP
IMPLEMENTATION implementation/            clang-18 ASan/UBSan(/MSan), libFuzzer accept-on-invalid harness
PROPERTY      property/                   Hypothesis properties, malformed catalogue, differential B0 + LMS
FAULT         fault/fault_injection.py    11 fault classes over the certificate/extraction pipeline
DEVNET        (repo) ceqs/ + ceqs/devnet-v2/   64-seat sweep C = 0…26 complete; matrix kit v2.1 (14 scenarios after 2026-09-13)
--- v0.2 additions (AUDIT_STACK.md section 3b) ---
FIXES         fixes/make_fixes.py         F1–F5 fixed as NEW versions (v1.51 C, v2.2 Python) with regressions; FIXES_v2.2.md in the project
INDEPENDENT   independent/                spec-only B0 implementation vs reference: 6,701/6,701; 18 spec gaps (S1–S4 observable) closed in spec §11
PRODUCTION    implementation/production/  ASan+UBSan at b=20/τ=11/wg=16/ρ=4096: 2,194 s, 0 errors, F1 reproduced; MSan timed out (inconclusive)
FORMAL+       formal/perlemma_n7_8g, formal/frame_b0.ec   Tamarin N=7 resource-limited; EasyCrypt FRAME(B0) skeleton, admitted
MATH-DOCKER   Dockerfile.math             8/8 reproduced inside python:3.12-slim + SymPy + galois
```

## Run

```bash
./run_all.sh                       # every layer; absent tools report NOT RUN, never a pass
python3 math/math_layer.py         # ~4 min: exact recomputation + counterfactual attacks
python3 fault/fault_injection.py --schedules 300
python3 primitives/cross_validate.py
bash property/run_all.sh
python3 formal/bounded_checker.py
```

Reproducible environment: `Dockerfile` (SageMath via passagemath, SymPy, galois,
Hypothesis, liboqs, dilithium-py/kyber-py, Tamarin + Maude, ProVerif via opam,
clang sanitizers + libFuzzer, AFL++, valgrind, ACVP vectors). Not built on the
authoring host; pin versions before citing.

## Tool status on the authoring host (2026-09-11)

| tool | status | used for |
|---|---|---|
| SymPy 1.13 / galois 0.4.11 | present | M1–M8 exact arithmetic, GF(2^m) |
| SageMath | **absent** (Docker: passagemath) | — |
| Tamarin 1.12.0 + Maude 3.5.1 | downloaded binaries, run | protocol lemmas A–E at N = 4 |
| ProVerif | **absent** (Docker: opam) | model written, unexecuted |
| liboqs 0.16.0 | built from source | primitives |
| dilithium-py 1.4.0 / kyber-py 1.2.0 | pip | independent FIPS 204/203 |
| NIST ACVP vectors | fetched (master @ 975de31e) | keyGen/sigVer/sigGen/encapDecap |
| clang-18 ASan/UBSan/libFuzzer | present | C prover |
| MSan | ran with the private compiler-rt: clean at reduced parameters; production run timed out (60 min, single-threaded) | C prover |
| valgrind / AFL++ / KLEE | absent (no root) | Docker (KLEE: separate image) |
| Hypothesis 6.151 | present | property layer (re-run against the fixed files: 16/16, 16/16) |
| EasyCrypt | absent; `formal/frame_b0.ec` skeleton written, proof admitted, unexecuted | game-hopping proofs (later stage) |

## What this stack does not claim

It does not prove QPT-128 secure. When complete it can say, layer by layer:
mathematical claims independently reproduced; protocol properties modelled and
bounded-checked (Tamarin at small N); primitives independently tested;
implementation fuzzed and sanitizer-tested; security games experimentally
attacked at reduced sizes; concrete bounds independently recomputed; devnet
adversarially exercised; known failures documented and regression-tested. The
independent *second implementation* of the whole construction remains open
(only the B0 extraction rule and LMS have independent counterparts).
