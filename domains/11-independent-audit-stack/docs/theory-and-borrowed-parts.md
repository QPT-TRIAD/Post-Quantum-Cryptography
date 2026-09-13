# Theory used per layer, and which part was borrowed

An audit layer is rarely theory-free: it recomputes somebody else's bound, instantiates somebody
else's model, or checks somebody else's standard. This file states, layer by layer, which theory
each layer uses, **which part of it is borrowed** (as opposed to re-derived here), and the claim
label that goes with it. The labels are the programme's, kept as the source gives them:
theorem-with-proof / reduction-sketch / model-or-ledger estimate / measurement / simulation /
assumption / conjecture.

Two rules were followed in compiling it. First, a citation is repeated exactly as the source gives
it, including where the source says the citation is incomplete — the ledger's own note that a
legacy constant has **no located source** is part of the record and is reproduced below rather
than tidied away. Second, an audit result never inherits the label of the thing it audits: re-running
a symbolic proof produces a machine-checked symbolic proof, not a theorem about deployed ML-DSA.

## 0. Summary

| layer | theory used | part borrowed | label of the layered claim |
|---|---|---|---|
| `math/` M1, M4, M6–M8 | quorum counting `\|Q₁∩Q₂\| ≥ 2q−N`; kernel structure of `D(s) = αs + βs² + γs⁴`; birthday/multi-target work factors | counting identity (one line, full); linearized-polynomial root structure (standard algebra); multi-target Grover with *T* marked items (full) | **simulation** (exact arithmetic, exhaustive or sampled) |
| `math/` M2 | attack-cost arithmetic: Grover/BBHT, CFHL collision, DFMS extraction, GHHM simulation, gate counts | the CFHL bound **formula only** (`80e²(q+1)³2⁻ⁿ + 4·2⁻ⁿ` at success 1/3), as in v1.43; citation incomplete in the source | **model-or-ledger estimate** |
| `math/` M7 | EUF-CMA as the abstraction of "forgery" | only the direction "one forgery ⇒ frame succeeds" is exercised | **simulation** (toy PoW signature) + **assumption** for ML-DSA-87 |
| `formal/` Tamarin | Dolev–Yao symbolic model with the `signing` equational theory (EUF-CMA-ideal signature); quorum counting instantiated at N = 4 and N = 7 | the model and its semantics, in full, as a modelling assumption | **machine-checked symbolic proof output** |
| `formal/` bounded checker | same abstraction, third model: plain set enumeration | nothing — the checker is written from the abstraction | **simulation** (exhaustive within the bound) |
| `formal/` ProVerif | applied pi-calculus model of the same abstraction | the tool's semantics; the models were **unexecuted on the audit host**, so their recorded output is expectation only — they were run for this repository (ProVerif 2.05) and the expectations became observations, one of them falsified (§4 of `formal-models.md`) | **model-or-ledger estimate** (recorded), **measurement** (this repository's run) |
| `formal/frame_b0.ec` | EUF-CMA (full definition); guessing reduction with loss N | the game-hop plan | **reduction-sketch**, unexecuted, proof `admit`ted |
| `primitives/` | FIPS 204 (ML-DSA), FIPS 203 (ML-KEM), NIST ACVP vectors; RFC 8554 (LMS), SP 800-208 (approved parameter sets) | the standards' algorithms and the published vectors, in full | **measurement** (three implementations agreeing) |
| `implementation/` | sanitizer and fuzzing semantics (ASan/UBSan/MSan, libFuzzer); the target's FAEST-v2 / QuickSilver design | only the tools' semantics; the target's design is not re-derived here | **measurement** (one run, one seed) |
| `property/` | property-based testing (Hypothesis); RFC 8554 round trip; the module's symbolic signature double | the engines; the target's own semantics are what is being tested | **measurement** (test outcomes, mutation counts) |
| `fault/` | an adversarial network model: loss, duplication, reordering, delay, skew, restart, rollback, corruption, equivocation | the fault set (classic modes, no citation claimed by the source); the signature is the module's symbolic double | **simulation** |
| `independent-b0/` | the B0 wire specification (v1.44) | the specification text only — no reference code was consulted | **measurement** (a second implementation agreeing with the first) |
| `fixes/` | the five findings' own root causes | the corrected code, derived from the frozen reference by exact single-match replacement | **measurement** (regression tests) |

## 1. Mathematics and cryptanalysis

**Counting.** `|Q₁ ∩ Q₂| ≥ 2q − N` for two q-subsets of an N-set is used in full; it is one line of
counting and the formal layer's own findings call it "the one-line theorem the implementation relies
on (22 shared signers for the ratified parameters)". What the audit adds is exhaustive verification
of the threshold at every N = 4…64 and the boundary behaviour at N = 4, 5, 7, 10 — simulation, not
proof.

**Cost arithmetic (M2).** The sources the source itself lists, quoted as it lists them
(`domains/06-qpt128-security-target/src/qpt128_finalization.py`, "Verified constants used (sources
re-checked on 2026-09-11)"):

- search/preimage: HRS16 (ePrint 2015/1256) Thm 1 — borrowed: the formula `8p(q+1)²/2ⁿ`.
- collision: CFHL EUROCRYPT 2021 Thm 5.29 — borrowed: **the rational envelope only**,
  `80·e²·(q+1)³/M + 4/M`. The source's own note: the legacy constant `12(q+154)³/2ⁿ` is
  "NOT FOUND … No source located", and the exact CFHL leading term `40e²(q+1)³/2ⁿ` gives about
  2⁻¹¹⁹·⁸ at q = 2¹²⁸, n = 512, not the 2⁻¹²⁴·⁴¹⁵ the legacy row claimed. The audit re-solved the
  module's bound at its own claim point and reports 81.74 / 252.40 bits for n = 256 / 768, with the
  module's bound at 2^81.7 queries = 0.3333.
- extraction: DFMS CRYPTO 2022 Thm 4.2; the joint two-proof row is the project's own v1.35 lift of
  DFMS Cor. 2.7. Simulation: GHHM ASIACRYPT 2021 Thm 3.
- gate costs: SHA3-256 oracle T-count 499,200 (Amy et al. SAC 2016 Table 2); AES-256 oracle T-count
  75,580 (JNRV rev. Table 9); floors g_H = g_F = 2¹⁸, g_AES-iteration = 2¹⁷.
- signatures: B0 assumes EUF-CMA of the chosen scheme at category-5 generic strength; the source's
  own qualification is that "the scheme's own reduction to its hard problem is a property of the
  signature, not of CE-QS composition". The ledger's C7 row labels the ML-DSA-87 figure of 2¹⁴⁸ an
  **assumption** (A-sig).

**Quantum search.** Grover's iteration count `⌊π/4·2^(n/2)⌋` and the BBHT form are used in full; M5
simulates n = 8…18 exactly and fits the slope (0.505) — a scaling check, not a 128- or 256-bit
attack. The programme's own amendment cites Zalka (quant-ph/9711070) as "search-specific resource
reasoning; not a blanket hardness theorem for all quantum attacks" — a caveat this layer repeats
rather than drops.

**Kernel lemma.** `dim ker D ≤ 2` for `D(s) = αs + βs² + γs⁴` is standard linearized-polynomial
algebra; the audit's contribution is exhaustive GF(2⁴)/GF(2⁶) and sampled GF(2⁸)/GF(2¹²) search,
plus two counterfactuals (an `s⁸` term, which must and does produce dim 3; a non-linearized `s³`
handle, whose solution sets must and do stop being subspaces), and the SUPPRESS slope measurement.

## 2. Formal models

Dolev–Yao with Tamarin's `signing` equational theory (an EUF-CMA-ideal signature — modelling
assumption, not a proof about ML-DSA), instantiated at N = 4 (q = 3) and N = 7 (q = 5). ProVerif
models are the same abstraction in applied pi-calculus, **written but unexecuted on the host that
produced them** (they were run for this repository; see `formal-models.md` §4). The EasyCrypt
skeleton `formal/frame_b0.ec` states FRAME(B0) → EUF-CMA with loss N; it is a **reduction-sketch**
whose proof is `admit`ted, and it is not machine-checked. Three concrete defects are visible in the
file itself to a reader who opens it (nothing has ever compiled it, so they are reading findings,
not compiler errors): a `Frame_Adv` that expects the `Scheme` interface while being handed an
oracle, a `corrupted` set that is initialised and never updated, so corruption is not modelled at
all, and a `EUF_CMA.sk` reference that occurs after the submodule that declares it. Those defects are
recorded here, not repaired: an unexecuted artifact is reported as unexecuted.

## 3. Primitives

The borrowed objects are the standards themselves — FIPS 204 (ML-DSA key generation, signing,
verification, the external-mu and pre-hash interfaces), FIPS 203 (ML-KEM key generation,
encapsulation, decapsulation including implicit rejection), RFC 8554 (LMS/LM-OTS), SP 800-208 §4
(which LM-OTS sets are approved alongside which LMS sets) — and the NIST ACVP vector files
(borrowed wholesale, with the upstream commit and per-file sha256 recorded in
`primitives/vectors/SOURCE.txt`). The layer's own claim is only that three implementations agree;
that is a measurement. Its label for the target is the source's: the primitives are necessary, not
sufficient, for QPT-128.

## 4. Implementation, property and fault layers

These layers borrow their **tools' semantics**, not results: sanitizer reports mean what ASan/UBSan/
MSan define (a report-free run is "no report on this run", which is what its own results file says:
"One run, one seed: coverage evidence, not a proof of memory safety"), libFuzzer coverage is a
measurement, Hypothesis shrinks counterexamples under the profile the file sets, and the fault
layer's fault set is a model of an adversarial network. The target's own theory (FAEST v2's proof
system with a degree-6 QuickSilver check, the QROM requirement `τ·b + w_g ≥ 230` that sets the
production parameters, and the FAEST v2 Lemma 6.3 grinding form) is quoted from the source's security
document and used only to choose parameters and interpret diagnostics; nothing in this domain
re-proves it. The fault and property layers both use the module's symbolic signature double — their
files say so plainly ("tests pipeline logic under faults, not cryptographic strength").

## 5. What is not borrowed, and where the programme's labels are deliberately kept weak

- The two **independent implementations** in this domain — `independent-b0/b0_indep.py` (from the
  wire specification alone) and `formal/bounded_checker.py` (from the abstraction alone) — borrow no
  reference code. That is the strongest independence claim here, and it is still qualified: the
  specification and the abstraction were written by the same programme that wrote the reference.
- The programme's own documents carry caveats that this domain repeats rather than upgrades. The
  operator amendment states that its counts "describe review coverage, not 1,000 certified
  mathematical theorems", that "[t]he complete deployed QPT-128 claim remains **OPEN**", and that
  its new algebraic lemmas (1–8) are supplied in full while the protocol-specific bridge obligations
  remain open. Those statements govern every "reproduced" verdict in this domain: reproduced means
  the recorded computation repeats, never that the construction is proven.
- Where a citation is incomplete in the source (the CFHL row above; the "legacy constant" with no
  located source), the incompleteness is carried forward and cross-referenced in `VERIFICATION.md`,
  not repaired with a citation the programme never made.
