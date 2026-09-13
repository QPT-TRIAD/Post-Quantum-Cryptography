# Quorum and accountability combinatorics

This document holds the results that make a quorum protocol *accountable*: the counting identity that
forces any two conflicting certificates to share a named signer, the tracing and exculpability notions
the constructions borrow, and the methodology the programme uses to check that its own tests can fail.

The first entry is the only claim in the programme that is **fully proved, exhaustively checked, and
independent of every quantum assumption**. It is also the claim that appears in the most guises — four
domains, four notations — so it is presented once, here, with the guises tabulated.

---

## 1. The counting identity

### D1-01 / D4-QI / D3-08 / D11-01 — quorum intersection `|S0∩S1| ≥ |S0|+|S1|−N`

- **Statement as used here.** Two quorums of size `q` out of `N` intersect in at least `2q − N`
  members; a threshold `t` gives `≥ 2t − N`; at the programme's parameters (N = 64, t = 43) the
  intersection is at least **22** seats. The consequence the accountability claim uses is that two
  conflicting certificates must share at least one **named** signer, hence at least 22 of them.
- **Role.** The base accountability invariant of the whole programme.
- **Label.** `[T]` theorem-with-proof — the source's own words: "proved in place", "full as set
  counting", "counting theorem".
- **Citation as the source gives it.** **Not needed (elementary)**; the D11 records it as a
  counting theorem.
- **Borrow.** Full.
- **Where used — the four guises, and the notation each uses.**

  | Guise | Where | Statement there |
  |---|---|---|
  | D1-01 | `domains/01-accountable-quorum-foundations/`, `files/PQ_AQC_research_proof_documentation_v0.5.md:401-439` | `\|S0∩S1\| ≥ \|S0\|+\|S1\|−N`; the protocol safety/accountability premise |
  | D3-08 | `domains/03-zk-carrier-experiments/` (part 2) | inclusion–exclusion counting bound inside the carrier argument |
  | D4-QI | `domains/04-operator-ledger/` (group 22; A24) | set counting, exercised on **441 pairs** at N = 7, t = 5 |
  | D11-01 | `domains/11-independent-audit-stack/` (claim C1; `math/math_layer.py:76-78`) | `C = 2q − N`; **22** at (64, 43); exhaustively recomputed |

- **Notes and the conditions the source attaches.** The ledger states that the counting identity
  "still needs distinct registered signer identities, actual valid signatures, canonical statements and
  message/epoch binding" (ledger line 717). Those four conditions are what the protocol layer must
  supply; the counting itself gives none of them, and this entry does not claim it does.
- **A recorded disagreement.** The identity's notation is not uniform across the record, and the
  discrepancy is recorded rather than normalised: the index writes it with a generic `N` and `2t − N`;
  the v0.5 source writes `|S0∩S1| ≥ |S0|+|S1|−n` with `n = 3f+1` and `q = 2f+1`, giving `f+1`; the
  audit stack writes `C = 2q − N`. The three are the same counting fact under three parameterisations.
  Where a domain's parameterisation is used, its own form is the accurate one to quote. See
  `VERIFICATION.md`.

---

## 2. Tracing, guilt and exculpability

### D2b-03 — Yang–Au–Lai–Xu–Yu 2017, Theorem 5.2 (k-times anonymous authentication)

- **Statement as used here.** The handle algebra, the public tracing equation, and the exculpability
  proof pattern.
- **Role.** Tracing and exculpability.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** **Incomplete in source (no venue, no ePrint)**.
- **Borrow.** **Partial — the group-manager architecture is removed** (v1.1, line 886). What is used is
  the tracing and exculpability structure; what is not taken is the group-manager trust model. The used
  part suffices because the programme's accountability layer supplies the registry itself.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.1, lines 616–708, 834–906,
  993–997).

### D2b-05 — Fujisaki–Suzuki classic traceable-ring-signature notions

- **Statement as used here.** The linkability and exculpability definitions.
- **Role.** Definitions.
- **Label.** `[T]`.
- **Citation as the source gives it.** **Incomplete in source.** **Standard (added):** PKC 2007.
- **Borrow.** Partial.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.1, lines 15–19).

### D1-05 — Fujisaki–Suzuki traceable ring signature

- **Statement as used here.** A per-signer tag derived from a weak PRF and bound to the message and
  issue.
- **Role.** The tracing mechanism **shape**.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** **Incomplete in source.** **Standard (added):** PKC 2007.
- **Borrow.** **Partial — the tracing shape only.**
- **Where used.** `domains/01-accountable-quorum-foundations/` (the working memo, lines 54, 58, 82).
- **Notes.** D1-05 and D2b-05 are the same source used for two different things: the tracing mechanism
  here, the linkability/exculpability definitions there. The record uses both; this package presents the
  source's identity once and the two uses separately.

### D2b-06 — Liu, ePrint 2025/1807, *Traceability for Free*

- **Statement as used here.** Extended linkability and exculpability, plus `O(1)` validity-gated
  tracing.
- **Role.** Design target.
- **Label.** `[T]`.
- **Citation as the source gives it.** **Incomplete in v1.1; complete in v1.18** (ePrint 2025/1807).
- **Borrow.** **Partial — the definitions and the gating target, not the DDH construction.**
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.1, lines 13–30, 973–976; v1.18,
  line 360).
- **Notes.** The source's construction is DDH-based and therefore not post-quantum; only its
  *definitions* are borrowed. A reader must not take the "for free" in the title as a post-quantum
  claim.

### D2b-07 — Camenisch–Hohenberger–Lysyanskaya compact e-cash

- **Statement as used here.** The `Identify` / `VerifyGuilt` split — the pattern by which a protocol
  separates "find the guilty party" from "prove the party is guilty".
- **Role.** Guilt attribution.
- **Label.** `[T]`.
- **Citation as the source gives it.** **Incomplete in source.** **Standard (added):** EUROCRYPT 2005.
- **Borrow.** Partial.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.1, lines 1005–1008).

### D1-06 — Signature-in-signature / hidden-until-disclosed accountability

- **Statement as used here.** The design pattern of hiding an extractable object inside signature
  randomness, to be revealed only when accountability is invoked.
- **Role.** Design pattern.
- **Label.** `[C]`/pattern.
- **Citation as the source gives it.** **Incomplete in source (no author, no venue)** — the source
  names the pattern, not a paper.
- **Borrow.** **Partial — the pattern only.**
- **Where used.** `domains/01-accountable-quorum-foundations/` (the working memo, lines 60–62).
- **Notes.** This is a design idea recorded in the trail, not a cited result. It carries `[C]` for
  exactly that reason, and the incomplete-citation list in `references.md` records it.

---

## 3. Contrast cases and scope

### D1-04 — Boneh–Drijvers–Neven accountable subgroup multi-signatures

- **Statement as used here.** The compact multi-signature contrast case, with full disclosure of the
  signer set.
- **Role.** **Contrast only, not borrowed.**
- **Label.** Not applicable — the source marks it as a contrast case.
- **Citation as the source gives it.** **Incomplete in source.** **Standard (added):** ASIACRYPT 2018.
- **Borrow.** None.
- **Where used.** `domains/01-accountable-quorum-foundations/` (the working memo, lines 50–52).
- **Notes.** Recording a contrast case is not a borrowing. A reader must not find a BDN-derived step
  in the programme's proofs; there is none.

### D1-09 — Epoch-barrier decomposition counting

- **Statement as used here.** `81 = 3^4` have/anchor combinations per node, with sub-machines sharing
  no guards.
- **Role.** Justifies decomposing the TLA+ model.
- **Label.** `[C]` — the source records it as **"an explanation, not a TLC measurement"**, and TLC
  never ran (see `gaps-and-unknowns.md`).
- **Citation as the source gives it.** None.
- **Borrow.** Full as an argument.
- **Where used.** `domains/01-accountable-quorum-foundations/` (v0.6).
- **Notes.** Because TLC never executed, this decomposition is an argument about the model, not a
  result about it. Any prose that says the model was "model-checked" must say by what — and in this
  repository the answer is the project's own Python bounded checker, catalogued in
  `protocol-and-ledger-assumptions.md`.

---

## 4. Methodology

### D1-10 — Negative-control / mutation testing

- **Statement as used here.** Deliberately unsafe mutants must **fail** — the discipline that makes a
  passing test mean something.
- **Role.** Methodology, not a mathematical result.
- **Label.** Methodology.
- **Citation as the source gives it.** No citation.
- **Borrow.** Full.
- **Where used.** `domains/01-accountable-quorum-foundations/` (v0.7, lines 219–226); the audit stack's
  negative controls are its largest instance.
- **Notes.** Two recorded results depend on this discipline being applied honestly: the audit stack's
  ACVP negative control (**27/27** corrupted vectors flagged) and its `hsslms` differential (**100/100**
  on approved parameter sets, **20/100** disagreement on non-approved mixed `m ≠ n` typecodes). The
  second of those is a **failure of the reference implementation**, reported upstream by the programme;
  it is not a failure of the programme's own code, and this package records it as the source does.
