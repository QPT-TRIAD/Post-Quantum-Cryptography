# D11 — independent audit stack

The QPT-128 / CE-QS programme (64 seats, threshold q = 43, overlap 2q − N = 22) is a
construction whose every step was derived by the same programme that wrote this audit. This
domain is the layer that tries to *disprove* the programme's claims rather than restate them:
it recomputes the mathematics, re-models the protocol, re-tests the primitives against other
implementations, fuzzes and sanitizes the C prover, property-tests the Python encoders, injects
faults into the certificate pipeline, and writes a second, spec-only implementation of the B0
wire format.

A counterfactual that succeeds is the product. Findings F1–F6 (one real leak, one vacuous
verifier, one upstream implementation bug, two input-validation defects, one documented size
asymmetry) and specification gaps S1–S18 are the results of this domain, together with eight
claim families that survived every attack.

## What "independent" means here — and what it does not

**Independent in method, not in organisation.**

- *In method:* each layer attacks a claim with a different tool, a different model, or a
  different implementation of the same object — SymPy/galois for the algebra, Tamarin and Maude
  for the protocol, an exhaustive Python checker as a third protocol model, liboqs versus
  dilithium-py/kyber-py versus NIST ACVP vectors for the primitives, clang sanitizers and
  libFuzzer for the C code, Hypothesis for the Python encoders, and an implementation of the B0
  wire format written from the specification alone. Two of these are genuinely third-party
  (Tamarin/Maude, liboqs/dilithium-py/kyber-py/hsslms, the ACVP vectors); the rest are written
  by the same programme as the code they check.
- *Not in organisation:* there is no external auditor. The same programme wrote the reference
  implementation, the specification, and the audit. The spec-only B0 implementation
  (`independent-b0/`) was written from `B0_wire_spec_v1.44.md` and the vector files without
  consulting the reference source — that is a real procedural separation, and it is the
  strongest independence claim this domain makes — but it was still the same programme holding
  both documents.
- *Not for every layer:* the property, fault and implementation layers *consume* the reference
  code (`sidecar_free_certificate_v1.44.py`, `hidden_signer_modeB_v1.46/1.50.py`,
  `pq_infra_s1s2_hashsig_dnssec_v2.0.py`, `pq_audit_s1_lms_v2.1.py`, `modeB_prover_v1.50.c`).
  They test it, they do not re-implement it. Only `independent-b0/b0_indep.py` and
  `formal/bounded_checker.py` are independent implementations of a reference object.
- *Not a security proof:* nothing here proves QPT-128 secure. See "What this stack does not
  claim" below and `docs/audit-stack-overview.md` §3.

## The layers

| directory | what it is | entry point | recorded runtime |
|---|---|---|---|
| `math/` | exact recomputation of M1–M8 (quorum counting, CFHL/Grover arithmetic, GF(2^256) differential against `galois`, kernel lemma, Grover scaling, multi-target, toy FRAME, EVADE) | `math/math_layer.py` | 217 s (v0.1 log); 82.6 s (v0.2 `math/math_results.json`); 235.8 s re-run |
| `formal/` | protocol properties A–E in three models: Tamarin 1.12.0 + Maude 3.5.1, an exhaustive Python bounded checker, and two ProVerif models (recorded unexecuted, run here with ProVerif 2.05); plus an unexecuted EasyCrypt skeleton | `formal/qpt128_quorum.spthy`, `formal/bounded_checker.py`, `formal/perlemma_n4|n7|n7_8g/`, `results/proverif-run/` | 111 s (N=4, all 12 lemmas); 0.35 s / 0.25 s (ProVerif variants) |
| `primitives/` | liboqs 0.16.0 vs dilithium-py 1.4.0 / kyber-py 1.2.0 vs NIST ACVP vectors, plus cross-implementation and tamper runs | `primitives/cross_validate.py` | 24.7 s recorded; 59 s on re-run |
| `implementation/` | clang-18 ASan/UBSan/MSan and libFuzzer on `modeB_prover_v1.50.c`, at reduced and at production parameters | `implementation/build.sh`, `run_sanitizers.sh`, `run_fuzz.sh`, `run_asan_production.sh` | 88.5 s reduced; 2,194 s production ASan |
| `property/` | Hypothesis property suites for B0, Mode B, hash-signatures (LMS/MTL) and TESLA, plus a differential B0 comparison | `property/run_all.sh` | 3.6 min recorded; 2.5 min on re-run |
| `fault/` | 11 fault classes × 300 seeded schedules over the certificate/extraction pipeline | `fault/fault_injection.py` | < 1 s |
| `independent-b0/` | the spec-only B0 implementation, its vectors, its checker, 18 specification gaps | `independent-b0/check_vectors.py` | 9.6 s |
| `fixes/` | F1–F5 fixed as new versions (v1.51 C, v2.2 Python) with regression tests, derived by exact single-match replacement from the frozen references | `fixes/make_fixes.py` | aborts rather than drift |
| `history/` | the ten v0.1 files that differ from their v0.2 twins, version in the filename | — | — |
| `results/` | the recorded `run_all.sh` console and log | — | — |

`docs/` holds the theory and method documents (see the reading order below); `docs/audit-stack-overview.md`
is the stack's own claim-by-claim ledger (C1–C20, F1–F6, S1–S4) and `docs/stack-readme.md` is the
stack's own introduction, both carried from the source with only the path corrections the
publication rules require. They are **records, published as recorded**: every name in them that
points outside this repository is translated here, and every claim of theirs this domain withdraws is
listed in the disagreement table below with the file that supersedes it.

| name inside the recorded documents | what it is, and where it is published |
|---|---|
| `AUDIT_STACK.md` | the stack's own ledger — this repository's `docs/audit-stack-overview.md` |
| `README.md` (in the stack root) | the stack's own introduction — `docs/stack-readme.md` |
| `reference/FAILED_ASSUMPTIONS.md` | the programme's failure log — `records/failed-assumptions.md` |
| `FIXES_v2.2.md` | the programme's fix register — `records/fixes.md` |
| `AUDIT_LEDGER_v2.1.json`, `AUDIT_CHECKLIST_v2.1.md` | the programme's ledger and checklist — `records/audit-ledger.json`, `records/audit-checklist.md` |
| `independent/` | the spec-only B0 work — this domain's `independent-b0/` |
| `tests/`, `ceqs/`, `ceqs/devnet-v2/`, `(repo)`, `(other sessions)` | the **devnet** repository, which this repository does not carry; its recorded evidence is under `docs/05-devnet-evidence/` |
| `Dockerfile`, `Dockerfile.math` | the stack's own containers, carried under `tooling/audit-stack/` and not built here |

Two further names the recorded documents use for **this** repository's own vocabulary:
`<workdir>/`, `<source-tree>/` (see `docs/inputs-and-provenance.md` §4), and `PQT_SRC` /
`AUDIT_PYLIB` (§5). Nothing else in a recorded file was edited.

## How to read this domain in order

1. `docs/audit-stack-overview.md` — the ledger: each claim, the counterfactual attempted, the
   verdict, and what the verdict does *not* mean. Start here; it is the map of everything else.
2. `docs/inputs-and-provenance.md` — where the audited inputs come from (`PQT_SRC`), what the
   repository ships and what it does not, and the placeholder conventions.
3. `docs/theory-and-borrowed-parts.md` — per layer: the theory used, the *part* of it that was
   borrowed, its label (theorem-with-proof / simulation / measurement / assumption), and the
   citation exactly as the source gives it.
4. `docs/formal-models.md` — the three protocol models and what each lemma establishes.
5. `docs/primitive-cross-validation.md` — the library and vector cross-validation.
6. `docs/property-suites.md`, `docs/fault-injection.md` — the property and fault layers.
7. `docs/independent-b0.md` — the spec-only implementation and its 18 specification gaps.
8. `docs/fixes-f1-f5.md` — the five fixes and their regression tests.
9. `VERIFICATION.md` — what was re-run for this repository, what was quoted as recorded, and
   every discrepancy between the two.

## Where disagreements are recorded rather than smoothed over

| disagreement | recorded in |
|---|---|
| the property layer's "16/16 and 16/16" against the fixed files is **withdrawn** (A28): the hash-signature module fails at *collection* on a mixed m ≠ n typecode pair, so 0 tests run; Mode B passes 16 | `VERIFICATION.md`, `docs/audit-stack-overview.md` (annotation at step 1 of §3b), `records/failed-assumptions.md` A28 |
| the v0.1 "Not done" line claiming all seven N=7 lemmas were OOM-killed at `-M8000m` is overstated: exit 137 is recorded for A, B, C1, C2 only; E2 has no exit line; D1 and E1 never started | `formal/perlemma_n7_8g/RESULT.txt` (as recorded), `VERIFICATION.md`, `docs/formal-models.md` |
| F5's "7/7" against the archived log (`fixes/hidden_signer_modeB_v1.51.py.log` shows 7 tests, 1 ERROR) | `VERIFICATION.md`, `docs/fixes-f1-f5.md` |
| the exhaustive mutant count is 17,660 in the ledger and 17,160 in the property layer's own findings | `VERIFICATION.md`, `docs/property-suites.md` |
| the SUPPRESS triple-collision slope is written as **−3.03** in the stack's own ledger row C5 (`docs/audit-stack-overview.md`) and stored as **−3.07** in the results JSON that row reports (`math/math_results.json`, key `fitted_slope_triple_vs_m`, line 179, identical in the v0.1 and v0.2 runs); the domain quotes the JSON, because that is the machine-written value the prose is describing | `VERIFICATION.md` §3.9, `math/math_results.json` |
| hsslms 0.1.3 disagrees with itself on mixed m ≠ n typecodes (F3, upstream, unresolved on non-approved sets) | `docs/property-suites.md`, `docs/fixes-f1-f5.md`, `implementation`/`property` findings |
| the recorded ledger says the ProVerif models are **unexecuted** (`docs/audit-stack-overview.md`, the tool-status and C20 rows): true of the audit host, but this repository's verification environment provides ProVerif 2.05, so both variants were run here. Every documented expectation holds except one: in the C = 1 variant the model's own header expects `Evidence` to be unreachable, and the run reaches it (the adversary double-signs with the published `sk0`). The EasyCrypt game remains a skeleton with the proof admitted and was **not** run | `VERIFICATION.md` §1 rows 12–13 and §2, `docs/formal-models.md` §4, `results/proverif-run/qpt128_quorum_C1.out` |

Nothing in this domain is edited to remove a disagreement. The v0.1 → v0.2 history is kept in
`history/`, and the source's own claim labels are preserved verbatim.

## Running it

```bash
. env/activate.sh                    # pinned python3, tamarin-prover, maude, proverif, liboqs
export PQT_SRC=/path/to/research-tree # read-only inputs; the environment activation script sets this
bash run_all.sh                      # every layer; absent tools report NOT RUN, never a pass
```

Two environment variables replace what were machine-specific absolute paths in the source:

- **`PQT_SRC`** (required by every layer that loads an audited input) — the read-only research
  tree. Scripts raise `SystemExit` if it is unset or not a directory. The file-by-file map from
  that tree to this repository is in `docs/inputs-and-provenance.md`.
- **`AUDIT_PYLIB`** (optional, no longer needed) — an extra site-packages directory. The pinned
  verification environment now provides every package the stack imports, so nothing sets it by
  default; it is kept only for a reader who has installed the pinned packages elsewhere.

The stack's own convention for tools that used to live beside it is `<stack root>/../tools/`
(Tamarin, Maude, liboqs); `formal/perlemma_n7_8g/run.sh` and `primitives/cross_validate.py` still
expect that layout. Log files and JSON results record the machine's working directory as
`<workdir>/` and the research tree as `<source-tree>/`; those two placeholders appear only in
recorded text, never in code.

## What this stack does not claim

It does not prove QPT-128 secure, and it does not prove the C prover memory-safe (one production
run, one seed). Layer by layer it can say: mathematical claims independently recomputed; protocol
properties modelled and machine-checked at N = 4 (12/12 lemmas), partially at N = 7, exhaustively
bounded-checked for N ≤ 10, and re-checked in two ProVerif variants run here (all documented
expectations hold except one sanity expectation, falsified — see the disagreement table);
primitives independently tested with no disagreement;
the implementation sanitized and fuzzed with one leak found, fixed and regression-tested; security
games attacked experimentally at reduced sizes; concrete bounds recomputed; the certificate pipeline
fault-injected with zero failures; and the B0 extraction rule reproduced by an implementation that
saw only the specification. The independent *second implementation of the whole construction*
remains open — only the B0 extraction rule, the bounded checker and LMS have independent
counterparts.

Measurements here are labelled as measurements. Reduced-parameter sanitizer and fuzz results are
not production-parameter results, and a devnet or reduced-size experiment is never a security
level.
