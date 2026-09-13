# Quantum search, and the accounting built on it

This document holds the results that decide what a quantum adversary can do to a secret of a given
length, and the arithmetic the programme uses to combine error terms into a single budget. It is the
document in which the programme's original security target is **refuted**: the target
`Adv < 2^-128 for every QPT adversary` does not hold, and the refutation is the reason every later
claim is stated as a gate work factor.

Two numbering systems meet here and must not be confused. The **operator ledger** (domain
`04-operator-ledger`) numbers its own lemmas `L1`–`L8`; those are catalogued in
`project-statements-and-amendments.md`. The **finalization script** (domain
`06-qpt128-security-target`) numbers its own lemmas `L1`–`L5` independently. Where this document writes
"finalization `L1`" it means the second. The two are different statements.

---

## 1. Grover search and the query lower bound

### D0-02 — Grover / BBBV query lower bound

- **Statement as used here.** Search on a 128-bit secret succeeds at approximately `2^64` queries.
  The bound is used both as an attack (Grover) and as a lower bound (BBBV, Zalka), so no algorithm
  does asymptotically better in the query model.
- **Role.** The reason the query-model target could not hold, and the starting point for the
  gate-unit re-definition of the target.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Standard (added): Grover, STOC 1996; BBBV; Zalka,
  quant-ph/9711070.
- **Borrow.** Full as cited.
- **Where used.** Domain `docs/01-research-journey` and, through it, domains 06, 09, 10, 11.
- **Notes.** The query-model reading is the weakest of the three readings the programme later
  distinguishes; see D6-01 and D6-10.

### D6-01 — Grover success law (finalization `L1`, `L2`)

- **Statement as used here.** The success probability of `j` Grover iterations on a uniformly random
  secret is `sin²((2j+1)θ)` with `sin²θ` the marked fraction. Finalization `L1` states the refutation
  in this form: *"Suppose a uniformly random 256-bit secret determines a winning output. Then 2^63
  Grover iterations already succeed with probability > 2^-128."* The exact-rational chain used is
  `θ ≥ sin θ = 2^-128` together with `sin y ≥ y − y³/6`. Finalization `L2` states the same fact in
  query units: `3·2^125 < 2^127` iterations reach success `≥ 1/3` against one 256-bit key, and
  `3·2^122` iterations do so against 64 keys.
- **Role.** Refutes the third reading of the target (a fixed-budget probability target) in the query
  model and forces the gate-unit definition of QPT-128.
- **Label.** `[T]` theorem-with-proof (the script decides the comparison by exact rational arithmetic).
- **Citation as the source gives it.** Standard (added): Grover, STOC 1996.
- **Borrow.** Full.
- **Where used.** `domains/06-qpt128-security-target/src/qpt128_finalization.py` (lemma block
  `grover_success_lower_bound`, and the `legacy_d3_refutation` verdict); the refutation is reported
  outward in `records/failed-assumptions.md` as entry Q1 and in
  `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` (the Grover landing lemma).
- **Notes (a discrepancy worth stating).** The failed-assumptions register words the same refutation
  differently: *"Grover on any 128-bit-secret game"*, result *"Grover gives Pr ≈ 1 at 2^64 queries"*,
  attributed to the same lemma `L1`. The two wordings are different statements — a 256-bit secret at
  `2^63` iterations reaching probability `> 2^-128`, versus a 128-bit secret at `2^64` queries reaching
  probability near 1. Both are true of Grover; the first is what the script's `L1` proves and the
  second is a textbook reading. The script is the artifact that runs; the register row is the summary.

### D6-02 — Union bound (finalization `L3`)

- **Statement as used here.** If `Win ⊆ ∪ Bad_i` and `Pr[Bad_i] ≤ ρ_i(G)`, then
  `Pr[Win] ≤ Σ_i ρ_i(G)`. If `Σ_i max_G ρ_i(G)/G ≤ 2^-130` the ratio target holds with `κ = 130`, and
  the ratio target implies the gate target. The self-test evaluates this at `G ∈ {1, 2^64, 2^128−1}`
  and checks `8·2^-131 = 2^-128` exactly.
- **Role.** Composition of error terms into the ledger; the arithmetic behind "probabilities add,
  exponents do not".
- **Label.** `[T]` elementary.
- **Citation as the source gives it.** Elementary; no citation in source.
- **Borrow.** Full.
- **Where used.** `domains/06-qpt128-security-target/src/qpt128_finalization.py`
  (`test_05_L3_d2_implies_d1`).
- **Notes.** The same discipline appears as the operator ledger's `L1` (budget inversion) and as the
  composition rule in domain `10-digital-infrastructure` — see D1-08, D10-13 and the ledger lemmas in
  `project-statements-and-amendments.md`. It is one elementary fact in three places.

### D6-03 — Convexity and endpoint bounds (finalization `L4`, `L5`)

- **Statement as used here.** For a polynomial envelope `ρ(q)` with non-negative coefficients evaluated
  at `q = G/g`, the ratio `ρ(G/g)/G` is convex in `G > 0`, so its maximum on `[1, 2^128]` is at an
  endpoint; a capped envelope `min(1, ρ)` is *not* convex and the checker therefore evaluates both
  endpoints on uncapped envelopes. `L5` covers the composition and extraction-overhead endpoints.
- **Role.** Makes the endpoint evaluation exact rather than sampled.
- **Label.** `[T]` elementary; the source gives "no proof text beyond the statement".
- **Citation as the source gives it.** Project; elementary.
- **Borrow.** Full.
- **Where used.** `domains/06-qpt128-security-target/src/qpt128_finalization.py`.
- **Notes.** The cap caveat is load-bearing: the source records that a capped envelope's ratio can
  peak away from the endpoints, which is why the checker keeps uncapped envelopes for the bound.

### D2b-20 — Row/width bounds of the challenge encodings

- **Statement as used here.** `8·2^-131 = 2^-128` for the eight-row encoding; the challenge width
  satisfies `h ≥ 3·log₂Q + log₂M + log₂C + 131`, which at the *hypothetical* setting `Q = 2^64`,
  `M = 2^16`, `C = 1` gives **339 bits** for the collision event and **275 bits** if the preimage
  exponent is used instead; the uniqueness error is `log₂ ε_uniqueness ≈ −148.2870623165`.
- **Role.** Parameter arithmetic: which event is counted changes the required width by 64 bits.
- **Label.** `[L]` / exact rational; the source's own words are that these are demonstrations, "not
  recommended parameters".
- **Citation as the source gives it.** Project derivation with a recorded exact-rational reproduction.
- **Borrow.** Full.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/blocker-resolution.md` (the v1.19
  document) and the v1.19 model and loss ledger.
- **Notes.** The source states explicitly that `C = 1`, the multiplicity and the resource profile were
  never proved or selected for the construction. The two numbers must be quoted together or not at all.

### D2b-11 — Grover preimage / BHT collision-claw

- **Statement as used here.** `2^{κ/2}` for preimage search, `2^{κ/3}` for collision and claw finding
  (Brassard–Høyer–Tapp).
- **Role.** Parameter screening only — the source calls it a screen and explicitly "not the final QROM
  proof".
- **Label.** `[L]` (screen).
- **Citation as the source gives it.** Standard (added): Grover, STOC 1996; Brassard–Høyer–Tapp,
  LATIN 1998.
- **Borrow.** Full as a screen.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (the v1.0 and v1.3 documents).
- **Notes.** The same `2^{κ/3}` collision exponent is what the CFHL envelope later formalises for the
  oracle model; see the CFHL entry below.

---

## 2. The refuted target and what replaced it

### D0-01 — QPT-128 target definition

- **Statement as used here.** `Adv < 2^-128 for every QPT adversary`, later refined to a gate work
  factor: `G(A) < 2^128 ⇒ Pr[Win(A)] < 1/3`, and the ratio form
  `Pr[Win(A)] ≤ G(A)·2^-κ` with `κ = 130`.
- **Role.** The security target the whole programme is measured against.
- **Label.** `[A]`/`[L]` as recorded; **refuted** in the query model by finalization `L1`.
- **Citation as the source gives it.** Not a citation — a project definition.
- **Borrow.** Full (project definition).
- **Where used.** `docs/01-research-journey/pqt.md` (closing statement) and
  `domains/06-qpt128-security-target/`.
- **Notes.** Three readings of "QPT-128" occur in the record and the finalization script lists them
  separately: the work-factor reading, the ratio reading, and the fixed-budget probability reading.
  Only the first two survive. Every downstream claim must say which reading it uses.

### D6-10 — NIST category-5 definition

- **Statement as used here.** "Resources comparable to AES-256 key search" — the reading that makes the
  gate-unit definition of the target the natural one, since a query costs the querying circuit's T-count
  (the script records 499,200 T-gates for a SHA3-256 oracle and 75,580 for AES-256).
- **Role.** Normalises the target against a published category.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** Standard (added): NIST category 5.
- **Borrow.** Partial — the definition only.
- **Where used.** `domains/06-qpt128-security-target/docs/qpt128-finalization.md`.

### D9-05 — The refuted target, as the reason the attack lab exists

- **Statement as used here.** The old construction's `Adv < 2^-128` claim; the attack lab records it as
  out of scope for testing and as the motivation for the lab.
- **Role.** Boundary statement.
- **Label.** `[T]` refuted (by finalization `L1`).
- **Citation as the source gives it.** Project / the finalization work.
- **Where used.** `domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py`.

---

## 3. Collision, birthday and multi-target terms

### D0-03 — Multi-target / collision screen

- **Statement as used here.** `(2^64)³/2^256 = 2^-64` for the collision term and `2^-108` for the
  multi-target term; these show that the pasted Category-5 parameters do not reach the target.
- **Role.** The first demonstration that the target was not reachable by search accounting alone.
- **Label.** `[L]` (arithmetic in source).
- **Citation as the source gives it.** Elementary arithmetic in the source; no external citation.
- **Borrow.** Full (elementary).
- **Where used.** Domain `docs/01-research-journey` (the pasted claim analysed in `pqt.md`).

### The CFHL collision envelope — D5-08 / D6-05 / D9-04 / D11-07 (one result, four domains)

- **Statement as used here.** `Pr[collision] ≤ 80·e²·(q+1)³/M + 4/M`, a rational upper bound on the
  source theorem obtained through `(a+b)² ≤ 2a² + 2b²`; the source theorem it bounds is
  `(2e(q+1)√(10(q+1)/M) + √(2/M))²`, whose leading coefficient is `40e² ≈ 295.6` beyond the `4/M` term.
- **Role.** The collision charge in every error-ledger row set.
- **Label.** `[T]` cited theorem plus the elementary square expansion.
- **Citation as the source gives it.** Chung–Fehr–Huang–Liao, EUROCRYPT 2021, Theorem 5.29
  (complete: the venue and the theorem number are both in the record).
- **Borrow.** **Partial** — the bound formula and its leading term are used; the rest of the source
  theorem is not. Domain `11-independent-audit-stack` records the borrow as "the bound formula only",
  and domain 11's citation of it is listed as incomplete in source.
- **Where used, four guises.** Domain 05/06: the collision term of the composed ledger. Domain 09: the
  recomputed suppression cost (a 256-bit case recomputed at 81.74 query bits / 99.74 gate bits).
  Domain 11: the collision row of the audit arithmetic. **One result; the numbers must not be restated
  with a different constant convention.**
- **Notes.** The constant convention in the record is the doubled one (`80e²`), not the source's
  `40e²`; both appear in the record and the entry names which is which.

### D9-02 / D11-06 — Birthday bound

- **Statement as used here.** Collision cost `√(π/2·2^h)`; the fitted collision curve is
  `log₂ Q = 1.0178·n − 0.931` against the theory `1.0·n − 1.0`.
- **Role.** Game accounting for collision attacks.
- **Label.** `[S]` simulation (domain 09) and `[T]` elementary (domain 11).
- **Citation as the source gives it.** Standard; no citation in source.
- **Borrow.** Full.
- **Where used.** `domains/09-security-games-and-attack-lab/`, `domains/11-independent-audit-stack/`.
- **Notes.** The fit is a small-`n` fit; see D9-07 and the extrapolation caveat below.

### D9-07 — Birthday theory for the suppression bug

- **Statement as used here.** `0.5·h + 0.326`, the birthday law behind the 768-bit collision /
  `2^252` quantum correction of the suppression cost.
- **Role.** Fixes the attack economics of the suppression path.
- **Label.** `[M]` (recorded against the failed-assumption register's Q3).
- **Citation as the source gives it.** Project.
- **Where used.** `domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py`.
- **Notes.** Q3 corrected an earlier error in which three preimages had been counted instead of one
  collision; the kernel lemma (`dim ≤ 2`, see `algebraic-and-coding-tools.md`) is what makes one
  collision the right count.

### D9-01 / D11-04 — Grover exact state-vector simulation

- **Statement as used here.** An exact state-vector simulation of Grover on a 64-qubit-class register
  reproduces `sin²((2j+1)θ)` to within `max |sim − theory| ≤ 5.3×10^-15` at every iteration, with a
  fitted `log₂(iterations)` slope of **0.512** against the theory's 0.5, extrapolating to
  `(π/4)·2^128 ≈ 2^128` iterations at `n = 256`.
- **Role.** Validates the simulator against the theory it is used to extrapolate.
- **Label.** `[S]` simulation (a measurement of a simulation).
- **Citation as the source gives it.** Standard (added): Grover, STOC 1996.
- **Borrow.** Full.
- **Where used.** `domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py` (the
  `grover_matches_theory` test) and, independently re-simulated, `domains/11-independent-audit-stack/`
  (the math layer's Grover check, `n = 8…18`, `k = 12/25/50/100/201/402`, slope 0.505).
- **Notes.** The simulator models the algorithm-level unitary exactly and the oracle's gate cost not at
  all. The `2^128` extrapolation is an extrapolation; the repository's standing rule is that 128-bit
  claims come from reductions, not from fitted slopes (see the extrapolation row below).

### D11-06 — Birthday collision probability

- Used in the multi-target and EVADE rows of the audit stack; `[T]` elementary, no citation in source.

---

## 4. The gate-unit floor and the attack-lab rows

### D10-10 — Grover / BBBV in gate units

- **Statement as used here.** A floor of `≥ 2^18` gates per oracle query, giving Grover gate counts of
  `2^114` at `n = 192` and `2^146` at `n = 256`.
- **Role.** The QPT-128 gate comparison against deployed key sizes.
- **Label.** `[L]` — a ledger estimate built on `[T]` as cited.
- **Citation as the source gives it.** "BBBV 1997" — **incomplete in source** (no full reference; the
  record gives the year and the acronym only).
- **Borrow.** Partial (the gate floor as applied to deployed parameters).
- **Where used.** `domains/10-digital-infrastructure/docs/pq-infra-program.md`.
- **Notes.** The same floor appears inside the finalization script's `L2` in the form of per-hash
  T-counts. Both are the programme's own accounting; neither is a citation.

### D5-10 — Hoeffding 1963, Theorem 2

- **Statement as used here.** The concentration inequality used to **refute** a proposed
  `exp(−256Δ²)` hybrid-sampling bound and to give the valid conditional bound in its place.
- **Role.** A refutation with a replacement.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** "Hoeffding 1963 Theorem 2", as given in source (the reference
  is given by year and theorem number; the record does not supply a venue).
- **Borrow.** Full.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/hybrid_sampling_bound_audit.py`.
- **Notes.** The refuted bound stays in the record beside the valid one; the source is explicit that the
  running bound is conditional on the mean premise of eq. 4 of that audit.

### D0-08 — Carolan–Poremba sampling-change term

- **Statement as used here.** `80(T+1)²/2^min(r,c)` as an alternative accounting for the sampling-loss
  term of a distantly-sampled signature.
- **Role.** Comparison for the sampler-change accounting; **scope only** — the programme uses the DFMS
  route instead.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** As given in source (author pair and formula; no venue, no year,
  no identifier recorded) — **incomplete in source**.
- **Borrow.** Scope only; not borrowed.
- **Where used.** Domain `docs/01-research-journey` reference catalogue.

### Extrapolation limits (D9-06, D6-04 in part)

- The attack lab fits exponents from small instances and states explicitly that the fits do **not**
  extrapolate to `n = 256`: the recorded errors are `+4.6`, `−12.4` and `−38.1` bits, and the standing
  conclusion is that "128-bit claims come from reductions only" (`records/failed-assumptions.md`,
  entry Q6). Any fitted slope in this repository is a small-`n` measurement, and the caveat travels
  with the number.

---

## 5. Composition discipline

### D1-08 — Generic single-user → multi-user union bound

- **Statement as used here.** `Adv_multi ≤ Σ Adv_single`: the single-user security of each signer is
  lifted to the quorum by a union bound over signers.
- **Role.** Lifts single-user security to the quorum setting.
- **Label.** `[T]` elementary.
- **Citation as the source gives it.** Textbook hybrid/union bound — **incomplete in source** (no
  reference given).
- **Borrow.** Full (elementary).
- **Where used.** `domains/01-accountable-quorum-foundations/history/research-proof-documentation-v0.6.md`.

### D10-13 — Difference lemma; union bound

- **Statement as used here.** `Adv ≤ Q/2^n` by the difference lemma, and the discipline that "a union
  bound is formed only for events inside one attacker goal".
- **Role.** Composition rule for the infrastructure audits.
- **Label.** `[R]` elementary.
- **Citation as the source gives it.** Elementary; no citation in source.
- **Borrow.** Full.
- **Where used.** `domains/10-digital-infrastructure/` (the hybrid-game audit and the composition rule
  in the program document).
- **Notes.** The discipline sentence is the reason the programme's composed ledgers keep the extraction,
  search, collision and simulation charges in separate rows rather than summing them across goals.

### Ledger row sets that consume these results

The composed ledger rows that use the terms above are catalogued in
`commitment-and-opening.md` (extraction), `signature-security-reductions.md` (the Fiat–Shamir
simulation charge, GHHM `E2`) and this document (search and collision). The three named charges of the
composed composition are `E1` (joint extraction), `E2` (Fiat–Shamir simulation) and `E3`; the
finalization script's verdict table is the executable face of that ledger.
