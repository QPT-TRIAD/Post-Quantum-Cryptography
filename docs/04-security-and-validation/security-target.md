# The security target, exactly

This page states the repository's security target, the relation between its three historical
readings, the argument for the unit it is stated in, and the exact arithmetic behind every verdict.
The owning domain is `domains/06-qpt128-security-target/`; the numbers below are that domain's, and
its `VERIFICATION.md` records the commands that re-produced them.

---

## 1. The three statements

`A` is an adversary modelled as a quantum circuit, `G(A)` its gate count, `Win(A)` the event that it
wins the game (a certificate that authorizes something the honest seats did not authorize, or a
framing of an honest seat).

| Id | Statement | Status |
|---|---|---|
| **D1** | `G(A) < 2^128 ⟹ Pr[Win(A)] < 1/3` | **adopted as the target**; implied by D2 |
| **D2** | `Pr[Win(A)] ≤ G(A)·2^−130` for every `A` | **the rigorous statement**; proved from the ledger |
| **D3** | `Pr[Win(A)] < 2^−128` for every quantum polynomial-time adversary | **refuted** by Lemma L1 |

**D2 implies D1, exactly.** If `G(A) < 2^128` then `Pr[Win] ≤ G·2^−130 < 2^128·2^−130 = 2^−2 = 1/4`,
and `1/4 < 1/3`. Both comparisons are exact rational comparisons in the checker (`test_05`).

**D3 is false.** Lemma L1 exhibits a uniformly random 256-bit secret against which `2^63` Grover
iterations succeed with probability strictly greater than `2^−128`. Nothing in this repository claims
D3; the refutation is permanent record in `records/failed-assumptions.md` entry Q1, and the checker's
verdict string is `REFUTED as stated; restate as D1/D2 with gate accounting`. The refutation is a
statement about *any* primitive with a 256-bit secret, not a defect of the construction.

## 2. Why the target is stated in gates rather than queries

A query to an oracle is not free. If the oracle stands for a concrete hash, one query costs at least
the T-count of that hash's circuit, and a query count and a gate count are different units. Counting
queries would make the target fail for every component with a 256-bit secret:

- **Lemma L2.** `3·2^125 < 2^127` Grover iterations reach success probability ≥ `1/3` against one
  256-bit key; `3·2^122` suffices against 64 keys. The checker's exact lower bound is
  `0.46197509765625`, above `1/3`, for both the one-key and the 64-key case.
- Charging each oracle evaluation at least `2^18` T gates is the cost floor the ledger uses. It is
  the reading under which "resources comparable to AES-256 key search" is defined.

The consequence is visible in the verdicts and is not hidden: **B0 passes D2 with a margin of +23.0
bits in gate units and fails it with −11.0 bits in query units.** The repository keeps both tables;
`domains/06-qpt128-security-target/docs/ledger.md` §9 item 5 states that D2 is claimed in gate units and that a reader should not mix
them. A reader who rejects the `2^18` floor has not been given D2 for B0.

## 3. The lemmas

| Lemma | Statement as used | Label |
|---|---|---|
| **L1** | `2^63` Grover iterations against a uniformly random 256-bit secret succeed with probability > `2^−128`; scales to 512 bits at `2^127` iterations. So D3 is unattainable. | theorem with proof, checked exactly (tests 01, 02) |
| **L2** | `3·2^125 (< 2^127)` iterations reach success ≥ 1/3 against one 256-bit key, `3·2^122` against 64. So a query-counted D1 fails and gate charging is required. | theorem with proof (test 03) |
| **L3** | If `Win ⊆ ∪ Bad_i` and `Pr[Bad_i] ≤ ρ_i(G)`, then `Pr[Win] ≤ Σ ρ_i(G)`; if `Σ_i max_{1≤G≤2^128} ρ_i(G)/G ≤ 2^−130` then D2 holds. | theorem with proof (union bound, test 05) |
| **L4** | For `ρ` a polynomial in `q = G/g` with non-negative coefficients, `ρ(G/g)/G` is convex in `G`, so its maximum on `[1, 2^128]` is at an endpoint; caps break convexity and are applied only to the D1 probability. | theorem with proof, elementary (tests 06, 19) — **the convexity claim is stated in the source, not written out** |
| **L5** | DFMS's QROM online extractor runs in `O(q²)·poly` time, so a reduction using an extracted witness runs in `t_B ≈ G + a·q²·g_sim`; D2 then needs `n ≥ (2e−1)·128 + 130 + log₂c + e·log₂(a·g_sim) − 2e·log₂g_H − e·log₂g_F`. | **model-or-ledger estimate** — the source's own word is "roughly" |

The arithmetic behind L1 and L2 is the Grover success law `sin²((2j+1)θ)` with `sin θ = 2^−128`,
together with `sin y ≥ y − y³/6`.

**L4 is a gap in exposition, not in arithmetic.** The checker performs the endpoint evaluations; the
claim that the maximum is at an endpoint is asserted rather than proved in the source. A referee
would ask for the one-line convexity computation.

**L5 is the load-bearing estimate.** Every scenario that needs an extracted witness — all of Mode S
and all of compat mode — pays its charge. The lemma is approximate in the source's own words, and the
`a` coefficient is not pinned down: the repository carries three readings of the same term,
`22ℓ+60` in `domains/06-qpt128-security-target/docs/ledger.md`, `20ℓ+60` in the extraction domain, and `72+40ℓ` in the operator
ledger's account. The checker uses one of them and records the others. Smaller coefficients would
only increase the margins, which is an observation, not a re-derivation.

## 4. The ledger

D2 is not proved directly. The proof is L3 applied to a ledger of named bad events, each row
evaluated at the budget edge `G = 2^128`:

| Row | What it bounds | Mode S, query units | Mode S, gate units |
|---|---|---:|---:|
| E1 joint online extraction | the reduction's own extractor, charged by L5 | −133.302 | −169.302 |
| E2 honest-proof simulation | simulator advantage | −159.415 | −159.415 |
| E3 credential preimage | single-block SHAKE256 credential functions | −95.0 | −203.0 |
| E4 registry-key collision | 1024-bit registry keys | −338.793 | −500.793 |
| E5 link coincidence | handle coincidence between the two certificates | −90.023 | −198.023 |
| E6, E7, E8 | registry authenticity, canonical encoding, durable approval state | 0 | 0 |
| **total** | | **−89.978 → fails D2** | **−159.414 → passes, +29.4 bits** |

The rows are `log₂` of the exact ratio `ρ_i(G)/G`. The shifts between the two unit systems are not
constant, because the rows are polynomials in `q = G/g` of different degree and the reduction-time
term is itself divided by the oracle cost.

The full verdict table, in report order:

| # | Scenario | Units | `log₂` total | D2 (κ = 130) | margin (bits) | D1 |
|---:|---|---|---:|---|---:|---|
| 1 | B0 public signers | queries | −119.000 | fail | −11.000 | fail |
| 2 | Mode S, r = 640, 1024-bit keys, attack-cost | queries | −133.302 | pass | +3.302 | pass |
| 3 | Mode S, r = 640, 512-bit keys, rigorous | queries | +173.207 | fail | −303.207 | fail |
| 4 | Mode S, r = 640, 1024-bit keys, rigorous | queries | −89.978 | fail | −40.022 | fail |
| 5 | compat mode, rigorous | queries | +161.000 | fail | −291.000 | fail |
| 6 | B0 public signers | gates | −153.000 | pass | +23.000 | pass |
| 7 | Mode S, r = 640, 1024-bit keys, attack-cost | gates | −159.414 | pass | +29.414 | pass |
| 8 | Mode S, r = 640, 512-bit keys, rigorous | gates | +11.207 | fail | −141.207 | fail |
| 9 | Mode S, r = 640, 1024-bit keys, rigorous | gates | −159.414 | pass | +29.414 | pass |
| 10 | compat mode, rigorous | gates | +55.000 | fail | −185.000 | fail |

At the budget edge the D1 probability is `2^−25.0` for B0 (gates) and `2^−41.302` for Mode S
(rigorous, 1024-bit, gates); it is capped at 1 in every failing scenario.

**Two ledger variants and one unreconciled number.** The rows above are one ledger — the target
domain's. A second ledger, `modeB_rigorous_ledger_v1.47.py`, owned by the hidden-signers domain and
quoted by the attack lab, composes a differently named row set for the hidden-signer construction in
gate units (framing −145.0, binding −209.0, proof soundness −138.1, simulation −159.4, false
positive −181.2) and totals **−137.7 — a D2 margin of 7.7 bits**, where the table above gives +29.4
for the same profile. Both totals pass; the margins differ by 21.7 bits. Neither document
cross-references the other's row set, and no source reconciles the two. A referee would have to
establish whether the row sets differ in scope, in unit convention, or in an error.

**Two corrections that are part of the record.** The compat-mode row is a *withdrawal*: the
conversion is correct, but `ε_sig` must be evaluated at the reduction's running time, and the row
then fails by 185 bits in gate units. The false-positive row R5 was −943 in the earlier ledger,
modelled only as a random candidate opening hitting a registry key; the dominant path is a handle
coincidence, and the corrected value is −181.2, about 760 bits larger. The total moved from −137.7's
predecessor accordingly, and no verdict changed.

**Repetitions and the extraction share.** The ledger fixes the extraction rows' share at ≤ `2^−133`
and binary-searches the minimum repetition count: **r = 553 in gate units and r = 640 in query
units**. The report uses the larger, `r = 640`. The share is a ledger convention, not a derived
quantity, and the report's key name says so
(`minimum_repetitions_extraction_share_2^-133`).

## 5. The exact arithmetic, and what the decimals are not

Every comparison in the checker is a `Fraction` comparison. The decimal logarithms in the report and
in the document's tables are computed in 60-digit decimal arithmetic, rounded to 3 or 9 places, and
are **display only**.

The clearest case is Lemma L1's own row: the report prints

```
"success_lower_bound_log2": −128.0
"exceeds_two_pow_minus_128": true
```

The printed `−128.0` is a rounding of a value strictly above `2^−128`; the boolean beside it is the
exact comparison, and the boolean is the evidence. A reader who greps the decimals for the security
level will find rounded display strings; the verdicts are elsewhere in the same JSON.

The independent recomputation in
`domains/06-qpt128-security-target/results/ledger-independent-check.py` loads the checker by path,
recomputes every scenario total, both D2 margins, the minimum repetition counts at `r` and `r−1`, the
legacy-constant comparison and the quorum identities by its own route, and reports agreement on
every value. Its output is kept as `domains/06-qpt128-security-target/results/ledger-independent-check.txt`.

`--report` is deterministic: two runs are byte-identical. `--self-test` runs 19 tests, all passing.

## 6. What the verdicts do not establish

- The borrowed constants (`22ℓ+60`, the T-count floors, the DFMS and CFHL envelopes) are used as
  their sources state them. They have not been re-derived in this repository, and the sources' claim
  that they were checked against the full texts is a **process claim**, not a reproducible check.
- The model-premise rows E6–E8 and B0's rollback row are **set to zero**. They are assumptions; the
  margins are conditional on them, and they are the largest single gap in the ledger.
- The floors `2^18` and `2^17` are T-counts of published circuits. Depth, parallelism and memory are
  uncharged. The ledger is not a circuit-level cost model.
- `n ≥ …` in L5 is an inequality on parameters, not a proof that the reduction's loss terms compose;
  Theorem B is a theorem about a construction, conditional on named assumptions
  (A-QROM, A-F, A-cost, A-γ, A-MPC, A-protocol).

---

## Validation status

The statements above carry their labels. What must still be validated for this work to be accepted
as a standard proof, and what is missing, is in `validation-status.md`; the commands re-run for this
package, with their recorded baselines, are in `VERIFICATION.md`.
