# Project statements, ledgers and amendments

This document holds everything the programme states **in its own name**: the operator ledger's eight
lemmas, the A01–A28 investigation structure, the amendment record, the reader flags, the project
theorems of every domain, the measurements and fits, and the registers that record later corrections.

Entries here carry no external citation because there is none to give. The field says so rather than
leaving a blank, and the label is the one the source used. Three things a reader should carry from this
document before reading any project theorem:

- **A project theorem is not a borrowed theorem.** The programme's own statements are only as strong as
  their premises, and several are explicitly conditional.
- **The amendment record is part of the claim.** Where a number was corrected, the corrected number is
  the claim; the earlier one survives only as history.
- **An uncertified catalogue contributes nothing.** The ledger's own statement about its source text
  governs §4 below.

---

## 1. The operator ledger's lemmas

Source: `domains/04-operator-ledger/docs/operator-ledger.md`. The lemma numbers here are the **ledger's**
`L1`–`L8`; they are unrelated to the finalization script's `L1`, which refutes the original target (see
`quantum-search-and-accounting.md`).

### L1 — budget inversion (union bound)

- **Statement as used here.** `J ≤ τ ⇔ p_* ≤ (τ−B₀)/(20Q²)` if `B₀ < τ`, with
  `B₀ = ((72+40ℓ)Q³ + 2v)/2^h`, by union bound and **without** independence.
- **Role.** Invert the total error budget to bound the per-round challenge mass.
- **Label.** `[T]` theorem-with-proof (elementary).
- **Citation as the source gives it.** The constants are "supplied workspace report v1.32" and are
  **not in the tree: incomplete in source**. They are **superseded** by the v1.35 `(20ℓ+60)Q³` and the
  v1.43 `(22ℓ+60)q³` forms from DFMS Theorem 4.2.
- **Where used.** Verifier group 13; investigation A01 (obligation tag BOUND).
- **Notes.** The three coefficient variants of the same source are tabulated once in
  `commitment-and-opening.md`. Do not read `L1` here as the finalization's `L1`.

### L2 — adaptive contraction (tower property; ΣK†K ⪯ βI)

- **Statement as used here.** A product bound for adaptive failures and a trace contraction of a
  completely-positive instrument.
- **Role.** Bound the per-round failure probability for adaptive adversaries.
- **Label.** `[T]` proved (ledger lines 93–132).
- **Citation as the source gives it.** Conventions from source tag `S7` (Watrous, *The Theory of Quantum
  Information*, Chapter 2) — complete enough in source; **standard (added):** Cambridge University
  Press, 2018.
- **Where used.** Verifier groups 9, 11, 12; investigations A06/A07/A08 (W19, W40, W49).
- **Notes.** The proof is full **for the stated instrument**; the ledger states that **the connection to
  `p_*` is open** (line 152). `L2` is load-bearing for the D1 repetition counts and is listed as such in
  `load-bearing-theories.md`.

### L3 — robust contraction

- **Statement as used here.** `‖K‖ ≤ 2^{-1/2} + η`, with the certificate `ΣK†K ⪯ (9/16)I` allowing
  amplitude 3/4 (allowance ≈ 0.0428932).
- **Role.** Gives the repetition count under an imperfect per-round channel.
- **Label.** `[T]` full arithmetic; **the 9/16 premise is an assumption for the protocol**.
- **Citation as the source gives it.** Project.
- **Where used.** Verifier group 9; the staged-component bound groups.
- **Notes.** The premise is the assumption, and it is the reason the round counts below are conditional.

### L3-num — the staged-component rounds table (the D1 constant-success allocation)

- **Statement as used here.** `s = 32/64/92/128 → 73/137/193/265` rounds for `p_* ≤ 2^-n`, and
  `88/165/233/320` rounds for `p_* ≤ (9/16)^n`; with the boxed result
  `J(2^128, 512, (9/16)^320) ≈ 0.025346 < 1/24 ≈ 0.041667`, `log₂ ≈ −5.302071`.
- **Role.** The headline D1 constant-success allocation, `τ = 1/24`.
- **Label.** `[M]`/`[L]` — exact arithmetic, **premise open**.
- **Citation as the source gives it.** Project.
- **Where used.** Ledger lines 172–177; checker group "QPT staged component bounds" (lines
  19,473–19,486).
- **Notes.** The finalization document limits these numbers to **D1**; they
  **do not carry over to D2**. Quoting them for another domain is an over-extension the record forbids.

### L4 — base-b box mass

- **Statement as used here.** `p_max(h,b,t,r) = (a·t^r + C_{b,t,r}(R))/2^h`; the ternary case
  `b = 3, t = 2, h = 2, r = 2 → 3/4` (**not** 4/9); saturation from `r = 323` at `h = 512`.
- **Role.** Count the worst bad-box challenge mass.
- **Label.** `[T]` proved (lines 181–206).
- **Citation as the source gives it.** Project.
- **Where used.** Verifier group 14; investigation A11 (C48, C49).
- **Notes.** The ledger's own condition: "the decoder must imply box containment" (line 206).

### L5 — compatible good events; retry tail

- **Statement as used here.** `E[X|G1∩G2] ≤ ε(1−d1)/(1−d1−d2)`; the retry tail `q_S·p^R`; the boundary
  `R = 519`; and `p = 759/1024`.
- **Role.** Close the retry / rejection tail.
- **Label.** `[T]` proved (lines 210–227).
- **Citation as the source gives it.** `p = 759/1024` is inherited from the trail at `pqt.md:1839` —
  **incomplete in source**.
- **Where used.** Verifier group 16; investigations A13 (C41), A16 (K29).
- **Notes.** The ledger states that `p` is an assumption.

### L6 — finite-field rank; min-entropy monotonicity

- **Statement as used here.** `N_{m,n,r}(q) = ∏(q^m−q^i)(q^n−q^i)/(q^r−q^i)` and
  `H_min(f(X)|E) ≤ H_min(X|E)`.
- **Role.** Rank census and entropy monotonicity for the extraction chain.
- **Label.** `[T]` proved (lines 231–247).
- **Citation as the source gives it.** Leftover hash: source tag `S4`, Tomamichel–Schaffner–Smith–Renner,
  arXiv 1002.2436, Theorem 6 — catalogued in `commitment-and-opening.md`.
- **Where used.** Verifier groups 15, 17; investigations A14 (R26, W18, W48, W50), A15 (C45).
- **Notes.** The caveat is mandatory wherever the entropy argument is restated: "the uniformity of
  seeded module matrices is **not** established" (line 238).

### L7 — work/depth; monotone composition

- **Statement as used here.** `work = Σg_v`; the depth recursion; `ε_A ≤ acε_C + ad + b`; and the
  statement that **MAXDEPTH is not a security argument**.
- **Role.** Convert between query and gate units and charge the reductions.
- **Label.** `[T]` proved (lines 251–255).
- **Citation as the source gives it.** Search optimality: source tag `S8`, Zalka, quant-ph/9711070 —
  catalogued in `commitment-and-opening.md`, **borrowed only for the search-model interpretation**.
- **Where used.** Verifier group 18; investigation A22 (K20, K47, O9, R33–R35, R41, R42, Z43).
- **Notes.** This lemma is the accounting bridge between the query model and the gate work factor; the
  two readings must not be mixed (see the caution in `quantum-search-and-accounting.md`).

### L8 — minimax inequality; fixed-hash distinguisher

- **Statement as used here.** `sup inf ≤ inf sup`; the fixed-hash distinguisher gap `1 − 2^-h`.
- **Role.** Keep worst-case quantifiers, and expose the ideal-permutation gap rather than close it.
- **Label.** `[T]` proved (lines 259–269).
- **Citation as the source gives it.** Source tag `S3`, Cojocaru–Hhan–Liu–Yamakawa–Yun, arXiv 2504.18188,
  Corollary 6.9 — catalogued in `commitment-and-opening.md`.
- **Where used.** Verifier groups 19, 20; investigations A03 (Y1, Y2, Y4), A20 (K50, R27, R28, Z38).
- **Notes.** `S3` "applies only to uniformly random permutations" (line 267) and does not certify the
  fixed deployed permutation. The gap is what the lemma exposes.

### D4 `S7` (source tag) — Watrous, *The Theory of Quantum Information*, Chapter 2

- **Statement as used here.** The standard finite-dimensional Kraus and positive-map conventions used
  in the elementary contraction proofs (`L2`, `L3`).
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Complete enough in source (the ledger gives the chapter and the
  author's URL). **Standard (added):** Cambridge University Press, 2018.
- **Borrow.** Full as conventions.
- **Where used.** `domains/04-operator-ledger/docs/operator-ledger.md` (source list, line 130).
- **Notes.** A source-tag / operator-ID collision at two line positions (`[S7]`/`[S9]`, lines 488/503)
  is recorded as an open reader flag; see §5 and `gaps-and-unknowns.md`.

---

## 2. The investigation structure

### D4 §A.5.4 — the A01–A28 investigations

- **What it is.** Twenty-eight investigations, each with four questions, a **mutated formula**, a
  proof basis, a claim label and an executed-checker pointer. Each active catalogue entry is routed to
  exactly one of them. The obligation tags are:
  BOUND (A01), COMPOSITION (A02), QUANTIFIERS (A03), ENDPOINTS (A04), CONTRACTION (A05),
  QUANTUM_CONTRACTION (A06), ROBUST_CONTRACTION (A07), CHALLENGE_MASS (A11, per the routed table),
  CHALLENGE_ENCODING (A12), SAMPLER (A12), MASS_SUPPORT (A11), RUNTIME_TAIL (A13), ENTROPY (A14),
  SIGNATURE_GOOD_KEYS (A15), GOOD_EVENT_GLUE (A16), SIGNATURE_SECURITY (A17), JOINT_EXTRACTOR (A18),
  PUBLIC_CE (A19), DEPLOYED_HASH (A20), HASH_PARAMETERS (A21), REDUCTION_RESOURCES (A22), VALIDATION
  (A23), AUTHORIZATION_INTERFACE (A24), RANDOMNESS_EXTRACTION (A25), TEST_LIMITS (A26), ANALOGY_FILTER
  (A27), FINAL_GLUE (A28).
- **Label.** Every A01–A28 row is labelled by the ledger as **reduction-sketch / model-or-ledger
  estimate** unless the row itself says otherwise.
- **Notes.** Each row carries the same open question the ledger names in its §B.16, and each has an
  executed-checker pointer. An obligation tag is a routing label, not a result: a reader should read
  "A18" as "the joint-extractor investigation", not as evidence about the joint extractor.

---

## 3. The amendment record

### D4 §A.5.5 — 130 amendments, and how many have support

- **What it is.** 130 amendments across the ledger: **82 in the D4a range** (CE-exec 9 including 2 weak,
  CE-text 10, STD 35, RESTR 28) and **37 in the D4b range**, plus 11 elsewhere as recorded.
- **Labels used.** FALSE_AS_STATED, DOMAIN_GAP, TYPE_GAP, FORMULA_ERROR, DEFINITION_MISMATCH,
  DIRECTION_ERROR, SIGN_ERROR, NORMALIZATION, PRECISION, UNSUPPORTED_INFERENCE, COMPLEXITY_GAP,
  TOPOLOGY_GAP, UNSUPPORTED_SECURITY, UNDEFINED_COMPOSITION, REDUNDANT_OR_UNDEFINED, plus VARIANCE_ERROR
  and FORMULA_GAP in the D4b table.
- **A count that two parts of the record state differently, and is therefore given both ways.** The
  index's amendment section totals **130**; the ledger's own part-3 header describes "**116** specific
  corrections or restrictions", and the D4b dossier's support sentence counts "the 116 amendments". The
  index's 130 is itself composed of 82 + 37 + "11 elsewhere". Neither figure should be quoted as though
  the record stated it once; the same is recorded in `VERIFICATION.md`.
- **The support count, stated plainly.** **35 of the STD amendments carry no proof and no citation**,
  and "**113 of the 116 amendments, and 34 of the 37 in this range, have no executable witness and no
  literature citation**". Only **3** of the 37 D4b amendments — **H20, R36, Y1** — have an executable
  witness.
- **Most consequential recorded corrections.** Among them: `L1` (constants), `L9`/`L10` (a majorization
  join/meet counterexample at `p = (4/5, 1/10, 1/10)`, `q = (3/5, 2/5, 0)` giving `(8/13, 4/13, 1/13)`
  and `(6/7, 1/7, 0)`), `L47` (widths do not multiply), `T8` (eigenvector not unique up to a constant),
  `Q40`, `D9`, `F8` (generator sign), `F21`/`F44`/`F47` (tempering ≠ finite memory; `E_α(t^α A)` is not
  a semigroup), `I33` (KL argument reversal), `I21`, `I1`/`I2`, `S16`/`S20`/`S21`/`S22`/`S36`,
  `M3`/`M8`/`M25`/`M33`/`M41`, `P17` ("rough-path signature is not an authentication signature"),
  `C45`, `C47`.
- **Notes.** The label taxonomy is the record's own and is reproduced rather than paraphrased. The
  support count is the part a sceptical reader needs: most corrections are corrections of the
  programme's own text with no witness behind them, and this package reports that as the record does.

---

## 4. What the catalogue contributes: nothing

### D4 §A.5.6 — named mathematical results in catalogue source text

- **What it is.** The ledger's part-3 list names results and authors across the mathematical literature
  — Crawley-Boevey, Hirzebruch, Pardoux–Peng, Adams, Adem, the alphabetical list through the end of the
  alphabet, and acronym-named results the name list does not catch (PPAD, Hedge/FTRL, BPDN/OMP/lasso,
  KMS, HKR, APS, CFR, AGV, VCG, DMRG, TRG, MERA, BGG, PBW, BSDE, BPHZ, KPZ/Φ⁴₃, LOCC, PPT, CHSH, AGM,
  ZFC and CH, LTL/CTL/μ-calculus, DPLL(T), SAT/SMT). D4a additionally names, without citation,
  Knaster–Tarski, Dilworth/Mirsky, Stanley, Karp mean cycle, Pinsker, Fano, Glivenko–Cantelli, Birkhoff
  ergodic, Sklar, Doob/Doob–Meyer, Jacobi triple product, James splitting, Hambly–Lyons,
  Chen–Strichartz, Courant–Fischer, Gelfand, Eckart–Young, Weyl, Nehari, Shale, Atiyah–Singer,
  Haglund–Haiman–Loehr, RSK/Cauchy, Hall scalar product, hook-length and Birkhoff–von Neumann.
- **Citation status.** **Incomplete in source — all of it.** The names sit in the historical "Source …"
  and "Amendment" fields, which are in source text the ledger itself calls uncertified (line 304).
- **What it contributes.** **Nothing.** These names are used in no proof in this repository, and the
  ledger's own statement about its catalogue source text governs.
- **Notes.** A reader who finds a familiar theorem name there should not infer that the programme uses
  it. This package records the catalogue as present, uncertified, and unused.

---

## 5. The nine reader flags

### D4 §A.5.7 — open questions the writers must not silently resolve

Nine flags are recorded. They are carried here as **open**, and resolving one is not this package's
business:

1. **C38's heading versus its definition** — the heading name ("Best/Birkhoff-van der Waerden") does not
   match the definition (Birkhoff–von Neumann).
2. **G44's Bott property** — stated for all `(n,k)` but apparently false at `k = n = 2`.
3. **K40** lacks the parallel amendment that K39 received.
4. **Y42's AGV** individual-rationality claim.
5. **N3's `⊠_free` versus `⊞`**.
6. **O10's amendment reuses O9's text verbatim.**
7. **Checker-scope text versus code** — group 13 does not assert event substitution; groups 4, 6, 8, 12
   and 16 compare hard-coded witnesses; **A28's contract tuple (line 775) differs from the checker's
   `FIELDS` (line 19,378)**.
8. **H16's "anti-commutes with itself: β² = 0"**.
9. **The `[S7]`/`[S9]` source-tag / operator-ID collision** at lines 488/503 — the collision must be
   resolved before anything citing `S7` is published.

---

## 6. Project theorems by domain

### D0-15 — the compat-mode theorem (v1.37/v1.38 route)

- **Statement as used here.** The "compat mode" QPT-128 route for the 43-seat quorum, over Phase VI–IX.
- **Role.** A route kept, then withdrawn.
- **Label.** `[R]`.
- **Citation.** Project theorem.
- **Status.** **Withdrawn.** `QPT128_finalization_v1.43.md:249` says "Replaced by B0 or Mode S". The
  v1.22 record's kill verdicts for trace-only and compat mode "rest on unsourced constants and
  estimates".
- **Where used.** `docs/01-research-journey` (part 1).

### D2a-09 — the project theorem chain (v0.6–v0.9)

- **What it is.** Theorem 8.1 lifting (v0.6), Theorem 10.1 same-hidden-set (v0.6), Theorem 15.1 summary
  (v0.6), Theorem 3.1 `|F| ≥ C(n,f)` (v0.7, complete short proof), Theorem 10.1 certificate soundness
  (v0.7, conditional on P1–P4), Theorem 14.1 privacy separation (v0.7), Theorem 6.1
  `Adv^SetFrame ≤ Adv^UF_MPAgg` (v0.8), Theorem 8 `ExtractConflict = supp(B0∧B1)`, `wt ≥ f+1` (v0.8),
  Theorem 9.1 `Adv^Frame ≤ 2Adv^UF` (v0.8), Theorem 10 BFT conflict (v0.8), Theorem 12.1 "Target B0
  theoretically solved at the abstract level" (v0.8, reduction sketch), Theorem 4.1 (v0.9, reduction
  sketch), Theorem 12.1 hidden quorum soundness (v0.9, reduction sketch), Theorem 13.1 (v0.9),
  Theorem 14 anonymity (v0.9), Theorem 15 public extraction ≥ f+1 (v0.9, conditional),
  Theorem 16 (v0.9), and Theorem 19.1 private wrapper `|QC_priv| = |E| + |π_ZK| + O(λ)` with
  `|E| = 1376 B` (v0.9, reduction sketch).
- **Label.** As labelled per entry (theorem-with-proof / reduction-sketch / theorem-with-proof
  conditional).
- **Citation.** Project theorems — no external citation.
- **Notes.** **No proof assistant was used anywhere in this domain.** Theorem 25.1's counterpart in
  D2b has a proof body that is "∎" only; the analogous caution applies here — a "theorem" in this chain
  is a written argument, and where it is conditional the condition is part of it.

### D2a-10 — the quantum lift criterion, items 1–6

- **Statement as used here.** The criterion a quantum-random-oracle lift must meet: classical
  reductions must never rewind, never program the oracle, and never reveal the witness.
- **Role.** The criterion the v0.8 route measures itself against.
- **Label.** `[R]` conditional.
- **Citation.** Project.
- **Notes.** The criterion is a checklist, not a proof that the route passes it.

### D2b-21 — the project theorem chain (v1.0–v1.24)

- **Statement as used here.** Theorem 25.1 (strong CE-QS composition), whose proof body is "∎" only, by
  reference to earlier sections; Theorem 26.1 (which contains a recorded internal mis-reference);
  Theorem 27.1 (the final collaborative theorem); §20 (a QROM screen); and the §23/§28 status tables.
- **Label.** `[L]`/`[R]` as labelled; §20 explicitly a screen.
- **Citation.** Project.
- **Notes.** **The `< 32 KiB` target is open in every version**: the status tables read "Concrete
  <32-KiB outer proof: open" from v1.0 through v1.24. A reader must not read the final collaborative
  theorem as closing it.

### D5-12 — the phase-GHZ circuit simulation lemma

- **Statement as used here.** An `H·T·CNOT` chain prepares a phase-GHZ state, giving **no security
  bound**; the simulation lemma (equations 3–5) is kept and the gate cost is explicit.
- **Role.** A dead end for security; a kept simulation lemma.
- **Label.** `[S]` simulation lemma; **the security claim is abandoned**.
- **Citation.** Project.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/phase_ghz_security_check_v1.40.py:120-138`.
- **Notes.** Full as a simulation, **none** as security. This entry is the clearest example in the
  package of a simulation that must not be read as a proof.

### D5-13 — the all-pass lemma

- **Statement as used here.** `Pr[G_N] ≤ ∏ r_i`, i.e. `2^{−N}`.
- **Role.** Hybrid correctness.
- **Label.** `[T]` **conditional on the conditional-mean premise** (equation 4, which is D5-11's
  Bouman–Fehr premise).
- **Citation.** Project.
- **Where used.** `domains/05-extraction-and-signature-reductions/` (v1.41, equation 6).
- **Notes.** The premise is the borrowed half; the lemma is the project half. Dropping the premise
  turns a conditional statement into an unconditional one.

### D6-11 — Theorem A (public signer set, profile B0)

- **Statement as used here.** Accountability is deterministic (≥ 22 seats, two verifying signatures
  each); non-frameability and safety reduce **tightly and linearly**.
- **Role.** The accepted QPT-128 result for public signers.
- **Label.** `[T]` theorem-with-proof, reduction tight and linear.
- **Citation.** Project — **full under the named assumption A-sig** (`D6-13`, catalogued in
  `hardness-assumptions.md`).
- **Where used.** `domains/06-qpt128-security-target/docs/qpt128-finalization.md:138-147`.

### D6-12 — Theorem B (hidden signer set, profile B1, "Mode S")

- **Statement as used here.** Safety `≤ E1 + E2 + E3`; non-frameability.
- **Role.** The hidden-signer route.
- **Label.** `[T]` theorem-with-proof **under named assumptions**.
- **Citation.** Project.
- **Where used.** `domains/06-qpt128-security-target/docs/qpt128-finalization.md:185-197`.
- **Notes.** Two recorded facts belong with this theorem and must be quoted with it: **no proof system
  fits 32 KiB** (Theorem C, below), and **B1 verification in code never reports success**.

### D6-14 — the checker verdict table

- **Statement as used here.** 19 verdict rows, verified equal to the ledger.
- **Role.** The executable face of the ledger.
- **Label.** `[M]`.
- **Citation.** Project (CPython 3.12.3; 19/19 OK).
- **Where used.** `domains/06-qpt128-security-target/docs/qpt128-finalization.md:26-36`.

### D7-01 — the v1.34 division-free decoder

- **Statement as used here.** A full port of the extraction decoder.
- **Role.** Extraction of the conflict witness.
- **Label.** `[T]` (ported proof from domain 05).
- **Citation.** Project.
- **Where used.** `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py:249-271, 961-1013`.

### D7-02 — the Grover landing lemma

- **Statement as used here.** `p ≥ 1/2 → k = 0`, with the landing behaviour above one third —
  the probability of *arriving at* the target, not merely of searching for it.
- **Role.** The attack-based necessary condition inside Theorem C.
- **Label.** `[T]` theorem-with-proof **under the named cost assumption and family hypotheses (i)–(iii)**.
- **Citation.** Project.
- **Where used.** `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py:1130-1155`.
- **Notes.** A "landing" statement is weaker than a success statement; the difference is the content of
  the lemma and is not to be smoothed over.

### D7-03 — Theorem C (the lower-bound family)

- **Statement as used here.** Proof families in the style of KKW, BN++ and FAEST v2 with `τ` parallel
  seats **cannot fit 27,056 bytes** at the required security.
- **Role.** The impossibility-shaped result that closes the hidden-signer `< 32 KiB` route.
- **Label.** `[T]` theorem-with-proof **under assumptions** (2^24 gates per Grover iteration including a
  2^5 allowance; membership of FAEST v2 / BN++ in families (i)–(ii)).
- **Citation as the source gives it.** The size formulas come from KKW / BN++ / FAEST v2 —
  **incomplete in source**.
- **Borrow.** **Partial — only the "one bit per extended-witness bit" property.** This is **not** a
  universal lower bound.
- **Where used.** `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py:95-113, 1019-1223`,
  `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md:103-212`.

### D7-04 — Theorem C's budget arithmetic

- **Statement as used here.** `τ = ⌈(s − w_g)/b⌉` and the per-seat budget
  `⌊(27,056·8 − fixed)/(τ·43)⌋`, in the `b = 16` and `b = 48` cases.
- **Role.** The quantitative gate of Theorem C.
- **Label.** `[L]` computed by exact arithmetic.
- **Citation.** Project.
- **Where used.** `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py:1182-1201`
  (`test_theorem_c_wire_budget`).
- **Notes.** Two corrections attach to this arithmetic and both are carried here: the **direction** of
  the inequality was **wrong before `Q2`**, and the pre-fix numbers are not the current ones. See §7.

### D7-05 — the KKW / BN++ / FAEST v2 size-formula structure

- **Statement as used here.** Used **only** for the one-bit-per-witness-bit property that defines
  Theorem C's family.
- **Label.** `[L]` partial.
- **Citation as the source gives it.** **Incomplete in source** — "asserted from their size formulas".
- **Where used.** `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py:1019-1223`.

### D7-10 — the distinctness lemma

- **Statement as used here.** An illustrative demonstrator, with both branches tested.
- **Role.** Uniqueness of seats.
- **Label.** `[S]` demonstrator.
- **Citation.** Project.
- **Where used.** `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py:829-850`.

### D7-11 — hybrid `min(Adv)`

- **Statement as used here.** The hybrid security argument for the B0 certificate — a composition over
  signature families.
- **Label.** `[R]` reduction sketch.
- **Citation.** Project.
- **Where used.** `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md` §A.
- **Notes.** A sketch of a hybrid argument is not a hybrid argument carried through.

### D8-08 — Theorems 1–4 of the hidden-signer domain

- **Statement as used here.** Theorem 1 non-frameability, tight:
  `Pr[Frame(i*)] ≤ 8·p·(q+1)²/2^256`. Theorem 2 safety plus forensic completeness (≤ 21 corrupt seats).
  Theorem 3 QROM soundness with the multi-round loss. Theorem 4 privacy.
- **Label.** Theorem 1 `[T]`; Theorem 2 `[T]`; **Theorem 3 `[T]` by transplant**; Theorem 4 `[R]`.
- **Citation.** Project.
- **Where used.** `domains/08-hidden-signers/docs/mode-b-security.md:67-122`.
- **Notes.** The transplant status of Theorem 3 is part of the theorem: it is the FAEST v2 lemma set,
  carried over, "not re-derived line by line for `Π_B`" (catalogued in
  `zero-knowledge-and-proof-systems.md`).

### D8-12 — the recorded size and table results

- **Statement as used here.** The Theorem 3 loss table (9 at `b = 24`; 7 at `b = 32`, `w_g = 32`);
  `ℓ̂ = 15,296`; and the production-prover results.
- **Label.** `[M]`.
- **Citation.** Project (reproduced by the ledger).
- **Where used.** `domains/08-hidden-signers/docs/mode-b-security.md:110` and the run log.

### D9-06 — the FRAME / SUPPRESS / EVADE / SAFETY game results

- **Statement as used here.** Measured fit slopes **FRAME 1.0178** (theory 1.0), **SUPPRESS 0.4498**
  (theory 0.5), **EVADE 1.0242** (theory 1.0); measured `Q(n)` of 144.7, 664.8, 1153.3, 4942.5 and
  10414.0 at `n = 8, 10, 11, 13, 14` against theory `2^(n−1) = 128, 512, 1024, 4096, 8192`; and the
  **SAFETY threshold measured at 22, equal to the theory's 22**, with one evader costing ≈ `2^(E+1.2)`.
- **Role.** Empirical validation of the construction's claims.
- **Label.** `[M]` measurement plus fit, **with the extrapolation caveat as the point**.
- **Citation.** Project.
- **Where used.** `domains/09-security-games-and-attack-lab/`, `attack_lab_results_v1.51.md:135-146`.
- **Notes.** The record's own sentence is that "the fix did not invent a new hardness". The fits are
  measured at small `n` and the extrapolation is what the caveat is about; the SAFETY row is the one
  that lands exactly on the theoretical value.

### D11-09 — the EasyCrypt game `frame_b0.ec`

- **Statement as used here.** A game skeleton for the B0 frame.
- **Role.** The formal-methods layer.
- **Label.** `[R]` skeleton, **not run** — the file says "UNEXECUTED … the proof is `admit`ted on
  purpose".
- **Citation as the source gives it.** EasyCrypt is **not installed**.
- **Where used.** `domains/11-independent-audit-stack/formal/frame_b0.ec:2-5`.
- **Notes.** The skeleton would not type-check as written. It is a plan, not a result.

### D11-11 — the claim register C1–C20

- **Statement as used here.** Each claim with its counterfactual, its result, its verdict and a "does
  not mean" line.
- **Role.** The audit's own statement of what it shows.
- **Label.** Mixed per row (`[T]`/`[M]`/`[S]`).
- **Citation.** Project.
- **Where used.** `domains/11-independent-audit-stack/` (the ledger, lines 28–47; identical wording in
  the earlier ledger except C11).
- **Notes.** The "does not mean" lines are part of each claim: a claim quoted without its "does not
  mean" line is a different claim.

---

## 7. The corrections register

### D12-01 … D12-06 — the failed-assumptions register

- **D12-01 (Q1).** The refuted `Adv < 2^-128` target — the register's first refutation. Carried in
  `quantum-search-and-accounting.md` together with the wording discrepancy recorded against it.
- **D12-02 (Q2).** The Theorem C **direction** correction: the attack needs an **upper** bound on
  gates per hash — 2^24 gates/hash giving 2^104 iterations, with budgets 359 / 1006 bits — refuting the
  v1.44 Theorem C inequality direction.
- **D12-03 (Q3).** The collision analysis: "suppression of v1.50 extraction costs 2^768" is a 768-bit
  **collision**, 2^252 in the quantum model; **three preimages had been counted instead of one
  collision**. Corrected in the ledger; the kernel lemma (`dim ≤ 2`) is invoked by the correction.
- **D12-04.** The linearized handle over GF(2^n) and the kernel lemma `dim ≤ 2`, invoked by Q3, Q4 and
  A22–A26. Catalogued as a guise of the kernel lemma in `algebraic-and-coding-tools.md`.
- **D12-05 (A18).** The GHP18 / X-Wing independence requirement: the hybrid combiner protects against a
  component failure **only with independent components**; **correlated seeds recover `K` in 2,048 of
  2,048 attempts** at each of seed bits 8/12/16 (ledger total **6,144/6,144**). A reproduced negative
  result — `[T]` as cited plus `[M]`.
- **D12-06 (A22).** Elementary characteristic-2 reasoning: `s(a + b·s²) = 0` has **exactly two** roots in
  characteristic 2 (squaring is a bijection), and the extractor solves the **affine** equation
  `D(s) = t`. The register labels the reasoning `[R]` and notes that **the counts are not checked** (by
  the audit stack).

### The register's accompanying corrections

- **Four pointer corrections (A9/A10/A11/A15)** and **four wording corrections (A18/A19/A20/I4)** are
  recorded and **must be applied before any citation from those entries is carried into a
  bibliography**.
- **A withdrawn cell:** the "16/16" figure is **withdrawn** (A28).
- **A contradicted claim:** the Mode B "7/7" claim is **contradicted**.
- **D11's recorded overstatements, carried forward and not smoothed:** the v0.1 "Not done" line
  claiming that "(A, B, C1, C2, E2, D1, E1) are OOM-killed even at `-M8000m`" is **overstated** — exit
  137 is recorded only for A, B, C1 and C2; E2 has no exit line; D1 and E1 never started; and the runs
  coincided with an 8-thread sanitizer production run. **Claim C19** (43-of-64 accountability under real
  consensus, 28/28 passed) is **not verifiable from the D11 archives**; it belongs to the excluded
  devnet material.

The details of each of these corrections, and the gaps they leave, are in `gaps-and-unknowns.md`.
