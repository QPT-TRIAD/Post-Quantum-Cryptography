# Load-bearing theories

This document names the results without which the programme's main claims do not stand. "Main claims"
here means the five the record itself treats as the programme's results: (a) the accountability claim —
a conflicting certificate pair shares at least 22 signers, each nameable; (b) the QPT-128 **gate work
factor** for profile B0 (Theorem A); (c) the impossibility-shaped Theorem C for hidden signers under
27,056 bytes; (d) Mode S soundness (Theorem 3); (e) the handle algebra; and (f) the refutation of the
original `Adv < 2^-128` target.

For each entry: why it is load-bearing, exactly where it is used, and **what breaks** if it is removed
or corrected. Full statements, labels and citations are in the domain documents this list points to.

---

## First rank — the five that carry the most

### 1. Grover search, with the union bound as used in the finalization's Lemma L1

- **Why.** It is the only theory that changed the **definition** of the programme's security target.
  Without it there is neither the refutation of the original target (f) nor the gate-work-factor
  redefinition in which every other claim (b)(c) is stated.
- **Where used.** `domains/06-qpt128-security-target/src/qpt128_finalization.py` (Lemma L1 and the
  finalization's L2/L3); the gate-unit rows of
  `domains/10-digital-infrastructure/` and `domains/08-hidden-signers/`; the exact state-vector
  simulations of `domains/09-security-games-and-attack-lab/` and
  `domains/11-independent-audit-stack/`; and the register entry `Q1`.
- **What breaks.** Remove it and the programme has a target it cannot meet and no replacement
  definition: Theorem A's "QPT-128" would be an unquantified phrase, and Theorem C's cost assumption
  would have no unit. **If the union-bound half is removed**, the composition arithmetic loses the step
  that turns per-round failures into a total budget.
- **Detail.** `quantum-search-and-accounting.md` §1–§2; `commitment-and-opening.md` §1 for the ledger's
  `L1`, which is a different lemma with the same number.

### 2. DFMS commit-and-open — the terminal readout lemma and the bad-database bound

- **Why.** Every reduction constant of the ledger is derived from it. The ledger's budget-inversion
  lemma is **written in terms of `B₀` built from these constants**, and the extraction domain's
  joint-lift theorem is its two-output adaptation.
- **Where used.** `domains/04-operator-ledger/docs/operator-ledger.md` (source tag `S1`);
  `domains/05-extraction-and-signature-reductions/src/joint_extractor_lift.py`;
  `domains/06-qpt128-security-target/src/qpt128_finalization.py` (the `dfms_extraction` row);
  `domains/08-hidden-signers/` (binding row only).
- **What breaks.** Remove it and **the composition arithmetic has no cited source at all**: the
  extraction charge would be an unsourced term. If only the **two-output adaptation** fails — the part
  that is the project's own derivation and not a quoted theorem — extraction of *both* witnesses of a
  conflicting pair from one execution fails, and with it the accountability claim's recovery step,
  while the single-witness extraction survives.
- **Detail.** `commitment-and-opening.md` §1, including the three coefficient variants of the one
  source.

### 3. Quorum intersection counting `|S0∩S1| ≥ |S0|+|S1|−N`, i.e. `2q − N`

- **Why.** The accountability claim (a) — **the one claim that is fully proved and independent of every
  quantum assumption** — rests on it, and the audit stack verifies it exhaustively.
- **Where used.** `domains/01-accountable-quorum-foundations/`;
  `domains/03-zk-carrier-experiments/` (the carrier's counting bound);
  `domains/04-operator-ledger/` (group 22, A24; 441 pairs exercised at N = 7, t = 5);
  `domains/11-independent-audit-stack/` (claim C1; exhaustively recomputed).
- **What breaks.** Remove it and four domains lose their central invariant, and the protocol layer's
  "≥ 22 named signers" statement has nothing behind it. Note that the counting gives **no** identity,
  signature validity, statement canonicity or epoch binding; those four conditions are supplied by the
  protocol and the record says so.
- **Detail.** `quorum-and-accountability-combinatorics.md` §1, with the four guises and the notation
  disagreement recorded.

### 4. CFHL Theorem 5.29 — the collision envelope

- **Why.** The collision charge appears in every error-ledger row set, and in the suppression/EVADE cost
  recomputations.
- **Where used.** `domains/05-extraction-and-signature-reductions/`,
  `domains/06-qpt128-security-target/src/qpt128_finalization.py` (the `cfhl_collision` row),
  `domains/09-security-games-and-attack-lab/`, `domains/11-independent-audit-stack/`.
- **What breaks.** Remove it and **the composed budget under-counts multi-target collisions** — the
  ledger would read as if a single-target collision were the only collision cost.
- **Detail.** `quantum-search-and-accounting.md` §3. The source's leading term is `40e² ≈ 295.6`
  beyond the `4/M`, and only the leading term is borrowed.

### 5. FAEST v2 Lemma 9.39 and its accompanying lemma set

- **Why.** It is **the only quantum-random-oracle soundness bound recorded for the hidden-signer
  prover** (Theorem 3), and the size-formula family Theorem C reasons about is the same source.
- **Where used.** `domains/08-hidden-signers/docs/mode-b-security.md` (Theorem 3 — a transplant);
  `domains/03-zk-carrier-experiments/` (cited precedent for the puncturable seed tree);
  `domains/07-compact-certificate-b0/` (the size-formula family Theorem C rules out);
  `domains/11-independent-audit-stack/` (the cross-domain soundness citation).
- **What breaks.** Remove it and **Mode S has no soundness statement at all**. Its status is weaker than
  its role, and both facts are true at once: the lemma set is **carried over, not re-derived** for the
  programme's relation, and the full text was **never held** by the programme — the citation is by lemma
  number only.
- **Detail.** `zero-knowledge-and-proof-systems.md` §3.

---

## Second rank — load-bearing, one step out

### 6. GHHM Theorem 3 — the Fiat–Shamir simulation loss

- **Why.** Without it the composition is missing one of its three named charges; the `E2` term would be
  a placeholder.
- **Where used.** The composed ledger's `E2` row (domain 06), the margin sweep (domain 05), the
  hidden-signer privacy theorem (domain 08).
- **What breaks.** The composed budget would have an empty simulation slot, and any statement of the
  composed error would be an inequality with an unstated term. Its `γ ≤ 2^{−512}` premise is what
  produces the `2^{−256}` factor; dropping the premise changes the term's form.
- **Detail.** `signature-security-reductions.md` §1.

### 7. ZKBoo §4.1 — Lemmas 1–3 and `p_triv = (3/4)^r`

- **Why.** It is **the only concrete commit-and-open backend** in the programme. Everything else about
  extraction is conditional on a backend that satisfies DFMS's premises.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/circuit_witness_extractor.py`;
  the parameterisation `ℓ = 4r`, `v = 2(1+3r)` in domain 06.
- **What breaks.** Remove it and the extraction charge becomes an existence statement — "if some backend
  satisfies P1–P4" — with no instantiation, and the ledger's extraction row loses its parameters.
- **Detail.** `commitment-and-opening.md` §2.

### 8. HRS16 search, `8·p·(q+1)²/2^n`

- **Why.** The search term of the hash-based branch, in four domains.
- **Where used.** The SLH-DSA reduction (domain 05), the "search / preimage" ledger row (domain 06), the
  attack-ledger row and Theorem 1's shape (domain 08), the deployed-key comparison (domain 10).
- **What breaks.** The hash-based routes lose their search charge; and because the same shape is reused
  for domain 08's non-frameability bound, removing it would leave that theorem's bound unsourced too.
- **Detail.** `hash-based-signatures.md` §4.

### 9. The kernel lemma — `D(s) = αs ⊕ βs² ⊕ γs⁴` has kernel dimension ≤ 2

- **Why.** The handle algebra's structural fact, and the corrector of the attack economics: the
  register's `Q3` correction rests on it.
- **Where used.** Domain 08 (§9.0), domain 09 (the search-space bound with measured fibre statistics),
  domain 11 (claim C4), and the register (`D12-04`, `D12-06`/A22).
- **What breaks.** Remove it and the handle search bound loses its justification, and the suppression
  attack's corrected cost (`2^252` quantum, from a 768-bit collision rather than three preimages) loses
  the step that rules out the cheaper route.
- **Detail.** `algebraic-and-coding-tools.md` §2, with the five guises and the `9,756/20,000` fibre
  measurement.

### 10. The operator ledger's `L2` + `L3`, and the 9/16 certificate

- **Why.** The headline D1 constant-success allocation `τ = 1/24` is theirs alone. These are **project**
  lemmas, not borrowed theory, and they are listed because the allocation depends on them.
- **Where used.** `domains/04-operator-ledger/docs/operator-ledger.md` (lemmas and the rounds table
  `73/137/193/265` and `88/165/233/320`).
- **What breaks.** The round counts are conditional on the 9/16 premise, which is an **assumption**, and
  the ledger states that **the connection of the contraction to `p_*` is open**. If that connection
  does not close, the round counts are arithmetic about an instrument, not about the protocol.
- **Detail.** `project-statements-and-amendments.md` §1.

### 11. Barbosa et al. Theorems 1/2/4 — the corrected CMA-to-NMA route

- **Why.** Without it the signature-security step is **a sketch with no verified good-key event**.
- **Where used.** The v1.37/v1.38 reduction and the v1.39 margin sweep (domain 05); the
  Fiat–Shamir-with-aborts basis of the ledger's source tag `S2`; the research-journey catalogue.
- **What breaks.** The approval signature's unforgeability would rest on an uncorrected transform — the
  exact error the "corrected" in the title exists to fix. The domain's equation "eq. D" is a **sourced
  partial-proof map, not an asserted QPT inequality**, and the composition's concrete numbers depend on
  the map being read as a map.
- **Detail.** `signature-security-reductions.md` §1.

### 12. The Binius64 PCS size floor (≥ 109,856 B at 96-bit) and the 96-bit backend label

- **Why.** Not a security theory — the load-bearing **negative** evidence for "no succinct backend fits
  27,056 B" (Theorem C). Together with the backend's stated limits (96-bit classical target; no quantum
  argument-of-knowledge theorem; FRI soundness covering only the query phase) it is why the answer to
  "use a SNARK" is no.
- **Where used.** `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md`;
  `domains/03-zk-carrier-experiments/`.
- **What breaks.** Without the floor, Theorem C's "no backend fits" leg has only the family argument;
  without the 96-bit label, a backend that *did* fit would be quoted at a security level its own
  parameterisation does not claim.
- **Detail.** `zero-knowledge-and-proof-systems.md` §4.

---

## What is **not** load-bearing

This is a positive statement, not a hedge. The following are present in the record and carry **no
claim**:

- **The operator-ledger catalogue** — hundreds of entries of which the overwhelming majority are parked,
  with "Source property" fields the ledger itself calls **uncertified**. It contributes no claim.
- **The named mathematical results in that catalogue's source text** — the alphabetical name list and
  the acronym list — are **cited without any reference** and are used in **no proof**.
- **The v0.x construction mocks** (hash-as-random-oracle algebra) are models, not constructions.
- **The phase-GHZ line** (domain 05) is abandoned as security and kept only as a simulation lemma.
- **Every tool that was named but never used** — Coq, Ivy, the Lattice Estimator, TLC/TLAPS, EasyCrypt,
  ProVerif, SageMath, the lattice estimators, the SNARK/ZK libraries — contributes nothing, and the
  record's own tool catalogue says so.

A sceptical reader can start here: if a claim in `domains/` rests on something in the list above, the
claim is not supported by it. If it rests on one of the twelve entries above, the entries say what it
rests on, and what would break it.
