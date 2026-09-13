# Signature security reductions and deployed standards

This document holds the reductions and standards that decide what the programme may claim about its
signatures: Fiat–Shamir with aborts and the corrected CMA-to-NMA step, the Fiat–Shamir simulation
charge, threshold-signature unforgeability notions, the deployed signature and KEM standards used as
constraints on parameters, and the resource vectors the reductions carry.

The group's central caution is that **a deployed standard is a constraint, not evidence**. FIPS 203,
FIPS 204 and SP 800-227 fix what the programme may do; they do not supply a quantum-security theorem.
The one place the programme's own accounting came out **below** its target (123.3 bits against 128,
`D8-11`) is kept as a negative result rather than rounded up.

---

## 1. Fiat–Shamir with aborts, and the CMA-to-NMA step

### D0-05 — Barbosa et al., Fiat–Shamir-with-aborts reduction

- **Statement as used here.** The corrected claim for signature schemes built from Fiat–Shamir with
  aborts: `ε_CMA ≤ ε_NMA + L_stat`, with the conservative value 2^-1664 in the source's table. The
  additive loss is what the programme borrows.
- **Role.** The reduction that makes the corrected CMA-to-NMA accounting available to the programme
  for the approval signature.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** The source gives the URL **ir.cwi.nl/pub/33405** and
  **Theorem 2**. **Standard (added):** CRYPTO 2023.
- **Borrow.** **Partial — the additive loss only.** The part used is the corrected statement and its
  additive loss. The part not used is the paper's full development. It suffices because the
  programme's approval-signature step needs exactly the additive-loss form.
- **Where used.** `domains/05-extraction-and-signature-reductions/`,
  `domains/06-qpt128-security-target/docs/qpt128-finalization.md`.
- **Notes.** The word **corrected** is load-bearing. An earlier treatment of the same transform was
  wrong in a way the record documents, and the corrected statement is what the programme uses. Do not
  cite the uncorrected form.

### D4 `S2` (source tag) — Barbosa et al. in the operator ledger

- **Statement as used here.** The same result, carried as source tag `S2` of the operator ledger,
  where its scope sentence is "Corrected QROM CMA-to-NMA reduction with a compatible good-key event
  and an explicit additive loss".
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** In the ledger the citation is given **without a year** and with
  the author list as "et al." — **incomplete in source (no year; author list incomplete)**; one
  citation in the ledger (line 612). **Standard (added):** CRYPTO 2023 — the same paper as `D0-05`.
- **Borrow.** Partial.
- **Where used.** `domains/04-operator-ledger/docs/operator-ledger.md` (source list, line 612).
- **Notes.** `D0-05` and `S2` are **one source in two guises**. A reader meeting both must not count
  two.

### D0-06 — Jackson–Miller–Wang, arXiv 2312.16619

- **Statement as used here.** The applicability condition `2γη′n(m+k) < ⌊q/32⌋`, which the programme
  **checks and finds failing** for ML-DSA-87.
- **Role.** **Used negatively** — a refuted route: the Fiat–Shamir-with-aborts condition does not hold
  for the deployed parameter set, so this route cannot be used at the parameters the programme needs.
- **Label.** `[T]` as cited, **used negatively**.
- **Citation as the source gives it.** arXiv 2312.16619 — **the arXiv identifier is given in
  source**.
- **Borrow.** Full as cited, used as a boundary.
- **Where used.** `domains/05-extraction-and-signature-reductions/` (via the research-journey
  catalogue).
- **Notes.** This entry is **not** support for the programme's claims. It is the reason one route was
  abandoned; the abandonment is recorded in `gaps-and-unknowns.md`.

### D0-07 — Canetti–Goldreich–Halevi

- **Statement as used here.** The plain-model / random-oracle composition statement, used for **scope
  only** — it delimits what may be composed in the random-oracle model and does not supply the
  programme's quantum-random-oracle step.
- **Role.** Background for Fiat–Shamir composition.
- **Label.** `[T]` as cited, scope only.
- **Citation as the source gives it.** **Standard (added):** JACM 51(4), 2004; cs/0010019.
- **Borrow.** Partial — the scope, not the framework's theorems.
- **Where used.** Recorded as a scope entry with no downstream use in the composed budget; its effect
  is to bound what an ROM composition argument may be extended to.
- **Notes.** Scope-only entries are never counted as support.

### D5-05 — Barbosa et al., ASIACRYPT 2024, Theorems 1 / 2 / 4

- **Statement as used here.** The v1.37/v1.38 signature-security reduction for the approval signature,
  including the `TCR_F` coefficient of **3** (equation 7 and the accompanying table).
- **Role.** The CMA-to-NMA reduction route for the approval signature.
- **Label.** `[R]` — reduction sketch, as the source labels it.
- **Citation as the source gives it.** Cited **with theorem numbers**; complete at that level. Two
  limits are recorded in the source and are carried here:
  - The **Hülsing–Kudinov 2022** work and the **ASIACRYPT 2022** paper behind it were read at
    **abstract level only** — the record says so.
- **Borrow.** **Partial.** The domain's equation "eq. D" is described in the source as a **"sourced
  partial-proof map, not an asserted QPT inequality"**. It maps which cited step covers which part of
  the argument; it is not a claim that the composed inequality holds at QPT-128.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/signature_security_reduction_v1.37.py`,
  `domains/05-extraction-and-signature-reductions/src/signature_margin_sweep_v1.39.py:151-179`.
- **Notes.** A reader who reads eq. D as a QPT inequality has upgraded a map into a claim.

### D5-09 / D6-07 / D8-05 — GHHM, Theorem 3 (the Fiat–Shamir simulation charge)

- **Statement as used here.** The Fiat–Shamir simulation loss
  `ε_sim = (3/2)·q_s·√(q + q_s + 1)·2^{−256}`, with the premise `γ ≤ 2^{−512}`. It appears as the
  composed budget's `E2` row (domain 06), in the margin sweep (domain 05), and in the hidden-signer
  privacy theorem (domain 08, Theorem 4), where the statement is
  `|Pr[β′ = β] − 1/2| ≤ ε_sim + 43·ε_P`.
- **Role.** The simulation charge of the composed budget.
- **Label.** `[T]` as cited, plus the premise `A-γ` as an assumption.
- **Citation as the source gives it.** Grilo–Hövelmanns–Hülsing–Majenz, ASIACRYPT 2021, Theorem 3 —
  **complete in source** in the v1.39 margin sweep (venue, year and theorem number all present);
  **incomplete in source** in domain 08, where only the four author names are recorded.
- **Borrow.** **Partial — one term of a bound.** The part used is the simulation-loss term and its
  `γ` premise. The part not used is the theorem's full QROM analysis. It suffices because the composed
  budget needs exactly the simulation charge for the Fiat–Shamir step.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/signature_margin_sweep.py`,
  `domains/06-qpt128-security-target/src/qpt128_finalization.py`,
  `domains/08-hidden-signers/docs/mode-b-security.md`.
- **Notes.** The `γ ≤ 2^{−512}` premise is what produces the `2^{−256}` factor rather than a generic
  loss; dropping the premise changes the term. A cross-reference to this entry appears in
  `zero-knowledge-and-proof-systems.md`; this is the single catalogued statement of it.

---

## 2. Threshold signatures, deployed standards and interface facts

### D1-02 — The threshold-signature hierarchy ("TS-sUF-2", "ts-suf-2")

- **Statement as used here.** The threshold-signature unforgeability notion hierarchy, of which the
  programme uses exactly one consequence: **"≥ T − c honest partial-signature support"**.
- **Role.** Turns "aggregate signatures" into "conflict-extractable quorum signatures".
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** **Incomplete in source in D1.** **Standard (added):** Bellare,
  Crites, Komlo, Maller, Tessaro, Zhu, "Better than Advertised Security for Non-interactive Threshold
  Signatures", CRYPTO 2022 — the paper that defines `TS-UF-0…4` / `TS-SUF-2…4`.
- **Borrow.** **Partial — only the support consequence.** The parts not used are the rest of the
  hierarchy, which the programme's construction does not claim to meet. The used part suffices because
  the accountability invariant is expressed in it.
- **Where used.** `domains/01-accountable-quorum-foundations/` (v0.5, v0.6).
- **Notes.** The domain records a **spelling mismatch** between `TS-UF-2` and `ts-suf-2` in the
  catalogue. The two spellings in the record refer to the same notion; the entry notes it rather than
  silently normalising it, and the mismatch is also carried in the infrastructure catalogue entry
  `D0-11`.

### D1-03 — Hermine (threshold FROST-like lattice signature)

- **Statement as used here.** `ts-suf-2` in the random-oracle model; the AOM-MISIS / AOM-MSIS
  intermediate problem; and the recorded fact that the **distributed key generation is outside the
  main proof**.
- **Role.** The concrete threshold backend for the adapter.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** **ePrint 2026/419** plus the NIST MPTS 2026 preview, writeup and
  slides, as given. The catalogue entry `D0-11` additionally records a **DKG source mismatch**.
- **Borrow.** **Partial** (adapter; the source describes the component as "replaceable").
- **Where used.** `domains/01-accountable-quorum-foundations/` (v0.5, lines 1446–1453, 2517–2520).
- **Notes.** A reader must not read the DKG as covered by Hermine's theorem; the record says it is not.

### D3-01 — FIPS 203 (ML-KEM)

- **Statement as used here.** §§3, 6–8: parameter sets, implicit rejection, and the security
  categories.
- **Role.** Primitive choice and channel.
- **Label.** `[T]` standard (the dossier's label for a standard used as a component fact).
- **Citation as the source gives it.** Complete in source (source tag `[S1]` in the carrier's list).
- **Borrow.** **Partial — component/constraint, "explicitly not as theorems about CE-QS"**.
- **Where used.** `domains/03-zk-carrier-experiments/` (part 2, line 130).

### D3-02 — FIPS 204 (ML-DSA)

- **Statement as used here.** §§4–6: the approval signature's algorithms and parameter sets. The record
  notes the **errata page** and states that its reading is "not a full errata/conformance audit".
- **Role.** Approval signature.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** Complete in source (source tag `[S2]`).
- **Borrow.** Partial.
- **Where used.** `domains/03-zk-carrier-experiments/` (part 2).
- **Notes.** Where a parameter or interface fact is quoted from FIPS 204 in this repository, the errata
  note applies; a reader should check the errata before quoting a formula.

### D3-03 — NIST SP 800-227

- **Statement as used here.** §§4 and 5.2 — KEM use and the authentication separation.
- **Role.** The composition rule the carrier's channel follows.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** Complete in source (source tag `[S3]`).
- **Borrow.** Partial.
- **Where used.** `domains/03-zk-carrier-experiments/` (part 2).
- **Notes.** §5.2 is the section the GHP18/X-Wing combiner use is measured against; the domain's own
  independence failure (`D10-08`) is set against that section.

### D6-09 — Kosuge–Xagawa, ePrint 2022/1359, Theorem 1

- **Statement as used here.** The UOV quantum-random-oracle route — the B0/UOV public-signer route of
  the finalization.
- **Role.** The QROM reduction for the multivariate route.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Kosuge–Xagawa, ePrint 2022/1359, Theorem 1; the ePrint
  identifier is given in source.
- **Borrow.** Partial.
- **Where used.** `domains/06-qpt128-security-target/docs/qpt128-finalization.md` (line 152).

### D2a-01 — Tetris DAPT semantics

- **Statement as used here.** The eligibility / registration / unlinkability definitions, re-stated as
  post-quantum analogues.
- **Role.** Security-definition shapes for the v0.x routes.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** **Complete in v1.1** (Avitabile–Botta–Fiore, ESORICS 2025) and
  **in v1.18** (ePrint 2025/730); **incomplete in v1.0**.
- **Borrow.** **Partial.** The model semantics are used; the **Groth–Sahai construction** in the same
  source is **not** used (the programme's constructions are not Groth–Sahai-based).
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (ledger v0.3:1163-1193; v1.0:94, 122).

---

## 3. The negative result kept as a negative result

### D8-11 — The 123.3 < 128 bit finding

- **Statement as used here.** The finding that "handle as a security choice" is **refuted as a security
  choice**: the hidden-signer route's concrete accounting lands at **123.3 bits**, below the 128-bit
  target.
- **Role.** A **negative result** — the reason the route cannot claim QPT-128 at the assessed
  parameters.
- **Label.** `[M]`/analysis, as the dossier labels it.
- **Citation as the source gives it.** Project.
- **Borrow.** Full as recorded.
- **Where used.** `domains/08-hidden-signers/docs/mode-b-security.md` (line 200).
- **Notes.** This entry is **not** to be rounded up, and it is not to be re-quoted as "about 128". It is
  a shortfall of 4.7 bits and the record keeps it as one.
- **The later correction that qualifies it, carried here so the finding is not quoted bare.** A later
  independent pass records that the **SAT experiments do not support the ranking** that produced the
  figure: any handle lets the solver guess the eliminated variable and derive the rest, and the
  ranking of one handle form over another **rests on the XL/hybrid model alone**, on an inconclusive
  solver run. The source's own sentence is that "the security bound is the generic `2^128` either
  way". The index records the same qualification in its tool catalogue, and `gaps-and-unknowns.md` §3
  carries it as an unrun/inconclusive item. The negative result stands as the dossier records it; the
  *reason* for it is a model's ranking, not a measurement.

---

## 4. The sponge's rate and capacity

### D3-06 — FIPS 202 (SHAKE256): rate, capacity and XOF

- **Statement as used here.** §§5.2 and 6.2 — the rate/capacity/extension-of-output structure, with
  **only the sponge-rate fact used**, to count permutations. The sourced observation the programme
  carries with it is that **832 output bits are not 512 bits of capacity**.
- **Role.** Permutation counting; and the reason a hash-level argument must name the *capacity*, not
  the output length.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** FIPS 202; **standard (added)**.
- **Borrow.** **Partial — single-block and two-block fixed-length instances only.**
- **Where used.** `domains/03-zk-carrier-experiments/` (parts 2 and 3).
- **Notes.** This entry exists because a plausible substitution (using the output length as if it were
  the capacity) is wrong, and the record flags it. The wiring-level entry is `D3-11` in
  `hardness-assumptions.md`; the ledger's own source tag `S5` for the Keccak specifications summary is
  in `algebraic-and-coding-tools.md`.
