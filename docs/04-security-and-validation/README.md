# Security and validation

This package states the security claim the repository makes, the model it is made in, what was
actually run against it, and — in `validation-status.md` — what would have to be true for the work
to be accepted as a **standard proof**, together with what is missing today. The last document is
the one a sceptical reader should read first.

| File | What it contains |
|---|---|
| `README.md` (this file) | the claim as the repository makes it, in one page, and what it rests on |
| `security-target.md` | D1, D2 and the refuted D3 stated exactly, the relation between them, the work-factor argument, and the exact arithmetic behind the ledger |
| `threat-model.md` | what an adversary is assumed able to do, the corruption and fault bounds, what the model deliberately excludes, and what happens to each claim if an assumption fails |
| `validation-status.md` | the evidence a referee would demand and where this work stands on each item; then the missing list, most blocking first |
| `attack-surface.md` | what was attacked and what was not, the difference between "the lab found no violation" and "there is no violation", and where a sceptical reader should start |
| `VERIFICATION.md` | every command this package re-ran, with its recorded baseline, its observed output and its verdict |

---

## The claim

Let `A` be an adversary modelled as a quantum circuit with gate count `G(A)`, playing a game whose
winning event is `Win(A)` — producing a quorum certificate that authorizes a decision the honest
seats did not authorize, or framing an honest seat. The repository's target is:

- **D2** — `Pr[Win(A)] ≤ G(A)·2^−130` for every `A`. This is the rigorous statement.
- **D1** — `G(A) < 2^128 ⟹ Pr[Win(A)] < 1/3`. This is the work-factor reading, and D2 implies it
  exactly: `G·2^−130 < 2^128·2^−130 = 2^−2 < 1/3`.
- **D3** — `Pr[Win(A)] < 2^−128` for every quantum polynomial-time adversary. **This was refuted and
  is not a claim of this repository.** Lemma L1 exhibits a 256-bit secret for which `2^63` Grover
  iterations already succeed with probability strictly above `2^−128`. It is retained only as
  history (`records/failed-assumptions.md`, entry Q1).

The target is defined and evaluated in
`domains/06-qpt128-security-target/`, which owns every number quoted below.

## What the claim actually rests on

D1 is **not** proved end-to-end from a hardness assumption. It is proved from D2, and D2 is proved
from a ledger: a union bound over named bad events, each row an exact rational comparison. The
subtraction is:

| Part | Status |
|---|---|
| the implication D2 ⟹ D1, the union bound, the endpoint rule, the quorum arithmetic | **theorem with proof**, checked exactly |
| the rows of the ledger, evaluated exactly at the budget edge | **exact arithmetic on borrowed bounds** — the bounds themselves are used as their sources state them, not re-derived here |
| the reductions that carry those rows | **reduction sketches** in outline, with loss terms accounted |
| the ≤ 2^18 T-gate cost floor, the QROM model, the single-block credential bounds, the ideal collaborative prover | **named assumptions** |
| the model-premise rows (registry authenticity, canonical encoding, durable approval state, rollback) | set to **zero** — premises, not proved terms |

The two constructions the repository ships:

| Profile | Certification | D2 margin, gate units | D2 margin, query units |
|---|---|---:|---:|
| **B0**, public signer set, signature in the clear | a category-5 signature per seat, 11,396 B certificate | **+23.0 bits** | −11.0 bits (fails) |
| **B1 / Mode S**, hidden signers, 1024-bit registry keys | a witness-committing proof; **no qualified backend exists** | **+29.4 bits** | −40.0 bits (fails) under rigorous extraction accounting; +3.3 bits under attack-cost accounting |
| compat mode (ML-DSA-87 or SLH-DSA inside an extractable proof) | withdrawn | −185.0 bits | −291.0 bits |

Both margins are conditional on the assumptions above, and both are stated in gate units: one oracle
evaluation is charged at least `2^18` T gates. **The verdict depends on that choice of unit.** Under
query counting — one gate per query — B0 fails D2 by 11 bits. The repository's position is that
query counting is the wrong unit, and Lemma L2 is the argument: a 256-bit key falls with probability
≥ 1/3 after fewer than `2^127` Grover iterations, so any query-counted target fails for every
component with a 256-bit secret. A reader who does not accept the cost floor does not get D2 for B0.

## What was actually tested

- **24 violation attempts** against the real hidden-signer implementation, executed end to end:
  **0 succeeded**, and the positive control extracted 22 seats
  (`domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py`).
- **Four adversarial games** (FRAME, SUPPRESS, EVADE, SAFETY) with measured query complexity fitted
  against theory (`…/src/ceqs_games.py`). The fits test the *scaling laws* the ledger assumes; they
  are not measurements of production security, and their extrapolation error to production sizes is
  measured at +4.6, −12.4 and −38.1 bits.
- **An exact state-vector Grover simulation** on the real oracle, agreeing with the closed form to
  ≤ 5.3 × 10⁻¹⁵ — a **simulation** of a reduced game, at toy sizes.
- **Independent implementation and cross-checks** in the audit stack: a second B0 implementation
  written from the specification agrees on 6,701 of 6,701 vector cases; ML-DSA-87 and ML-KEM-1024
  cross-validate against ACVP vectors and a second implementation with no disagreement.
- **Formal and semi-formal checks**: a Tamarin model at N = 4 verifies all 12 lemmas; at N = 7, 6 of
  12 complete. The TLA+ specification of the accountability model **has never been run under TLC or
  TLAPS**, and ProVerif and EasyCrypt were never executed. Those are specification documents.

No simulation establishes a security level, and nothing in this package should be read as saying
one does.

---

## Claim labels used in this package

| Label | Meaning |
|---|---|
| **theorem with proof** | proved in place; where arithmetic is involved it is checked exactly |
| **reduction sketch** | a proof given in outline, with its loss terms accounted |
| **model-or-ledger estimate** | a quantity computed inside a stated model or by a ledger convention, not derived |
| **measurement** | a number produced by running something, on a named host, at named parameters |
| **simulation** | a reduced game simulated exactly |
| **assumption** | a named premise; not proved here |
| **conjecture** | stated without proof |

## Validation status

Every statement in this package carries its label where it appears. What must still be validated for
this work to be accepted as a standard proof, and what is missing today, is set out in
`validation-status.md`; the empirical boundaries are in `attack-surface.md`. The commands this
package re-ran, with their recorded baselines, are in `VERIFICATION.md`.
