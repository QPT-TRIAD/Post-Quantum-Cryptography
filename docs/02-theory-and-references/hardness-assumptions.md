# Hardness assumptions and assumption-level boundaries

This document holds what the security statements **assume** rather than prove: lattice and LWE/LWR
bases, the named project assumptions the composed budget is conditional on, the primitive-level
assumptions made about the deployed hash and code, and the entries where a cited result is used as a
**boundary** — to show what a reader must not assume it gives.

An entry in this document is not evidence for a claim; it is the price of one. Where a source states
that its own assumption is weaker, narrower or less standard than a reader might expect, the entry says
so and the label stays as the source gave it.

---

## 1. Lattice and LWE/LWR bases

### D2b-01 — LWR / QLWR

- **Statement as used here.** Learning-with-rounding as the hardness base of the handle algebra. The
  source "does not silently identify this assumption with LWE", and the quantum variant (QLWR) is the
  document's own assumption rather than a standard named problem.
- **Role.** Hardness base of the handle algebra.
- **Label.** `[A]` + `[T]` as recorded.
- **Citation as the source gives it.** For LWR: **standard (added)** — Banerjee–Peikert–Rosen,
  EUROCRYPT 2012. For the quantum variant: **the document's own assumption, project-internal**; the
  source gives no bibliographic entry for it.
- **Borrow.** Full for LWR; the QLWR statement is project.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.3).
- **Notes.** A reader who treats "QLWR" as a cited hardness assumption has added a citation the record
  does not contain. `D2b-01` is the only place in this package where a named hardness problem is
  partly project-internal, and it is flagged as such.

### D2b-02 — Yang et al., Theorem 4.1, the uniqueness counting proof, and Lemma F.1

- **Statement as used here.** A weak PRF built from LWR (Theorem 4.1), its uniqueness counting proof,
  and the one-wayness reduction of Lemma F.1, together with the distributional reduction and the
  straight-line one-wayness reduction.
- **Role.** The handle algebra's basis.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Yang et al., Theorem 4.1 and Lemma F.1; **incomplete in source
  (no venue)** at the point of use. v1.18 adds the identity.
- **Borrow.** **Partial.** The parts used are the distributional reduction, the uniqueness bound and
  the straight-line one-wayness reduction. The parts **not** used are the source's Stern-type and
  random-oracle-model analyses, which the route document drops because the programme's threat model is
  quantum. The lattice part suffices because the route is carried on lattice hardness.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.3).
- **Notes.** Dropping the ROM/Stern parts is a *choice recorded in the source*, not a claim that those
  parts are wrong. A related mis-reference is recorded in the same domain: v1.1's Theorem 26.1 item 2
  calls this a "statistical uniqueness condition" while §7 and the v1.3 ledger attribute it to
  *pseudorandomness*; the record flags it as "likely a mis-reference, unverified against the source
  paper" and this package does not resolve it (see `gaps-and-unknowns.md`).

### D10-07 — MTL, Theorem 2 (multi-message ladder, MM-SPR)

- **Statement as used here.** The security basis of the multi-message ladder — multi-user
  message-bound second-preimage resistance — with the source's own qualification that it is
  "measured only at n ≤ 14 bits".
- **Role.** The condensed multi-signature scheme's assumption.
- **Label.** `[T]` as cited, **used as an assumption**.
- **Citation as the source gives it.** Fregly–Harvey–Kaliski–Sheth, CT-RSA 2023; ePrint 2022/1730 —
  **venue and ePrint identifier both given**: complete in source.
- **Borrow.** Partial — the assumption as used, not the paper's full ladder analysis.
- **Where used.** `domains/10-digital-infrastructure/` (the DNSSEC audit, source tag S2).
- **Notes.** The `n ≤ 14` figure is a *toy-parameter* measurement (`[M]`) and cannot be read as
  evidence at production parameters. A reader taking MM-SPR as established at 256 bits has upgraded a
  toy measurement into an assumption the source did not make.

---

## 2. Named project assumptions

### D6-13 — A-sig (the signature-forgery assumption of the composed target)

- **Statement as used here.** EUF-CMA of the non-FIPS signature candidates at category-5 generic
  strength — the assumption under which domain 06's Theorem A holds.
- **Role.** The premise of Theorem A (public signer set, profile B0).
- **Label.** `[A]` — the dossier lists it under "named assumptions are not theorems".
- **Citation as the source gives it.** None — there is no citation to give; the source says so.
- **Borrow.** Full as an assumption.
- **Where used.** `domains/06-qpt128-security-target/docs/qpt128-finalization.md` (§D),
  `domains/06-qpt128-security-target/src/qpt128_finalization.py`.
- **Notes.** Everything the composed target concludes about adversarial forgery is conditional on this
  assumption. A restatement of the composed target's conclusion that omits A-sig is an upgraded claim.

### D2a-08 — A7: auxiliary-input PRF

- **Statement as used here.** A non-standard auxiliary-input PRF used in the v0.9 privacy proof.
- **Role.** The privacy route of the v0.x line.
- **Label.** `[A]`.
- **Citation as the source gives it.** **Incomplete in source**, and the source **flags the assumption
  itself as needing replacement**.
- **Borrow.** Partial.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v0.9, flagged at line 853 of the
  working file).
- **Notes.** This is an open assumption-level gap, not a resolved one. `gaps-and-unknowns.md` carries
  it.

### D10-08 — GHP18 / X-Wing combiner theorem

- **Statement as used here.** A hybrid KEM combiner that protects against any component failure
  **only when the components are independent**.
- **Role.** The hybrid migration step of the infrastructure routes.
- **Label.** `[T]` as cited (in the random-oracle model).
- **Citation as the source gives it.** "X-Wing 2024" — **incomplete in source** (no venue, no
  ePrint/arXiv identifier). The combiner's independence requirement is recorded in the source as
  "untestable".
- **Borrow.** Partial — the combiner's shape and its premise.
- **Where used.** `domains/10-digital-infrastructure/` (source tag S6).
- **Notes.** The domain's own negative result is recorded against this: D12's A18 reports that
  correlated seeds let the adversary recover `K` in **2,048 of 2,048** attempts at each of seed bits
  8/12/16 (ledger total 6,144/6,144). The premise is therefore not merely unproven — it is
  **reproducibly falsified** at the tested instances. Read this entry together with A18, catalogued in
  `project-statements-and-amendments.md` and in `gaps-and-unknowns.md`.

### D5-11 — Bouman–Fehr (CRYPTO 2010), Theorem 3

- **Statement as used here.** The square-root/entropy statement that supplies the conditional-mean
  premise of the extraction chain's hybrid argument.
- **Role.** Conditional-mean premise.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Bouman–Fehr (CRYPTO 2010), Theorem 3 — **as given** in the
  source.
- **Borrow.** Partial — the premise, not the theorem's full development.
- **Where used.** `domains/05-extraction-and-signature-reductions/` (v1.41).
- **Notes.** Related to, but not the same as, the leftover-hash entry in
  `commitment-and-opening.md`, which carries its own uniformity caveat. The lemma that consumes this
  premise (`D5-13`, the all-pass lemma) is catalogued in
  `project-statements-and-amendments.md`.

### D8-03 — Semi-regular degree of regularity (`dreg`) and XL at ω = 2

- **Statement as used here.** The algebraic attack-cost rows of the hidden-signer ledger, built on the
  semi-regular degree of regularity and on XL at `ω = 2`.
- **Role.** The algebraic attack row of the hidden-signer assessment.
- **Label.** `[L]` — the source calls it the **semi-regularity heuristic**: "heuristic, not a theorem".
- **Citation as the source gives it.** **Incomplete in source**.
- **Borrow.** Partial.
- **Where used.** `domains/08-hidden-signers/docs/` (v1.49).

---

## 3. Primitive-level assumptions and measured boundaries

### D3-17 — SHAKE256 as a PRG

- **Statement as used here.** SHAKE256 is used as the seed-expansion primitive, and the soundness of
  the seed expansion rests on it.
- **Role.** Seed handling in the carrier.
- **Label.** `[A]` — with the source's own scope line: "this finite check is not a proof of
  computational hiding".
- **Citation as the source gives it.** None for the PRG property; the primitive itself is
  SHAKE256/SHA-3.
- **Borrow.** Partial.
- **Where used.** `domains/03-zk-carrier-experiments/` (part 2, `assessment.md:58`).
- **Notes.** Where a construction's hiding depends on challenge unpredictability, that dependence is
  an instance of this assumption, not a theorem about the deployed sponge.

### D3-11 — Keccak wiring lemma

- **Statement as used here.** 80 bytes of registration input is one SHAKE block; 224 bytes of tracing
  input is two blocks; **7 Keccak permutations per seat**.
- **Role.** Cost accounting in the carrier.
- **Label.** `[A]` + `[M]` — the source's scope: "assumes correct implementation of the pinned Keccak
  and word-gate library … implementation evidence, not a machine-checked proof".
- **Citation as the source gives it.** The pinned upstream Keccak implementation; the ledger's own
  source tag `S5` (Keccak specifications summary) is catalogued in
  `algebraic-and-coding-tools.md`.
- **Borrow.** Partial.
- **Where used.** `domains/03-zk-carrier-experiments/` (part 1).

### D1-07 — ML-DSA-65 parameter facts

- **Statement as used here.** Category 3, 192-bit RBG, signature 3,309 bytes.
- **Role.** Size and category screening in the accountability stack.
- **Label.** `[M]`.
- **Citation as the source gives it.** **Incomplete in source** at the point of use; **standard
  (added)**: FIPS 204, August 2024.
- **Borrow.** **Partial** — and the source's own words are that "the category-to-bits subtraction is a
  screening heuristic by the source's own words".
- **Where used.** `domains/01-accountable-quorum-foundations/` (v0.6).
- **Notes.** A category is not a bit strength; the mapping is the programme's screening choice, and the
  entry labels it as such rather than as an equivalence.

---

## 4. Two results used as boundaries

Two entries in this group are cited to show what a reader must **not** assume.

### D2b-09 — Unruh, Definition 3 / Theorem 15

- **Statement as used here.** A fixed corruption set implies no adaptive corruption — cited to show
  what the result does **not** give the source's route.
- **Role.** **Used negatively** — a boundary on the v1.19 argument, not support for it.
- **Label.** `[T]` as cited, used as a boundary.
- **Citation as the source gives it.** Unruh, arXiv:0910.2912v1, EUROCRYPT 2010, Definition 3 and
  Theorem 15 — **complete in source**.
- **Borrow.** Partial (the boundary).
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.19).
- **Notes.** An entry used as a boundary must never be counted as support.

### D2b-10 — Liu–Zhandry

- **Statement as used here.** The quantum query-complexity **exponents** for the problem, cited as a
  scope boundary: "asymptotic statements do not provide concrete constants".
- **Role.** Scope boundary.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Liu–Zhandry, arXiv:1811.05385v2 — **complete in source**.
- **Borrow.** **Partial** — the query exponents only, explicitly not the full theorem and not any
  time-complexity statement.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.19).
- **Notes.** Query-complexity exponents are a **query model** statement. They are not a gate count and
  must not be multiplied into the composed budget; the accounting distinction is set out in
  `quantum-search-and-accounting.md`.

---

## 5. What this document does not contain

Standards (FIPS 202/203/204/205, RFC 8554, RFC 8391, SP 800-208, SP 800-227, CNSA 2.0, RFC 5869,
SP 800-38D) are catalogued with the signature and KEM reductions in
`signature-security-reductions.md`. The network, synchrony and symbolic-model assumptions are in
`protocol-and-ledger-assumptions.md`. The two entries above that are used as boundaries are kept here
because their *effect* is an assumption-level boundary on the programme's own claims.
