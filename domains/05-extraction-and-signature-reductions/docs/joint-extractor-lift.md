# The joint-extractor lift

Source: `src/joint_extractor_lift.py` (v1.35). Script: `python3 src/joint_extractor_lift.py
--self-test` or `--explain`; the bare invocation prints the module header and exits 0. All paths are
relative to the repository root.

## 1. The problem, and why it is hard

A conflict decoder that names 22 seats is not a security reduction. To reach a standard assumption
one needs a **witness**: for each of the two conflicting bodies, all 43 private rows
`(index, trace seed, approval signature)`, obtained from the adversary's own execution. Two
single-proof extractors run in sequence do not give this. They run the adversary twice, and the two
executions need not agree on anything; the shared random oracle makes "the same execution" a
statement about one oracle simulation, not about a repeated call.

The obvious-looking fix — rewind the adversary, or run an extractor for proof 0 and then an extractor
for proof 1 — either costs a multiplicative loss factor or assumes that the two extractions share
state they do not share. The lift exists to show that neither is necessary for this particular
backend: one execution, one terminal measurement, one error term.

## 2. What is being proved, and what is imported

**Fixed.** One protocol `Π` for a fixed polynomial-time relation `R`. All of its statement data,
including any configuration or registry binding that `R` needs, must enter the canonical instance.
Its Fiat–Shamir proof verifier must be the exact classical verifier to which the backend theorem
applies.

**Premises P1–P4** (assumptions, stated in the source):

| | Premise |
|---|---|
| P1 | Oracle queries use a single quantum-accessible ideal random function `H` with `h`-bit outputs and the protocol's canonical disjoint encodings. The reduction simulates `H` by the exact compressed-oracle construction. All `H`-dependent setup and auxiliary services are generated inside the charged experiment; no free `H`-dependent advice is supplied. |
| P2 | After the adversary finishes, the two verifiers are classical. Together they make at most `v = v0 + v1` oracle calls and return both verdicts, even when the first proof is rejected. `Q` bounds **all** oracle calls through the end of those verifiers — setup, adversary and auxiliary services included — not just the adversary's advertised query count. |
| P3 | After one terminal measurement yielding `D`, a fixed deterministic polynomial-time decoder `dec(D, x, π)` uses only the classical database and ordinary local computation. It does not resume the adversary or make further oracle calls. |
| P4 | There is a global database event `B_bad` such that, for every instance and proof, `D ∉ B_bad` and `V^D(x, π) = accept` imply `R(x, dec(D, x, π)) = 1`. After at most `Q` charged queries, `Pr[D ∈ B_bad] ≤ G(Q)`. Missing database entries are bottom; `V^D` has a total reject-or-bottom rule. |

P4 is the premise that does the most work and is the easiest to weaken by accident: it must quantify
over all instances with the **same** deterministic decoder and the **same** final database. Separate
single-proof success probabilities in separate executions do not establish it, and the source says so
explicitly.

**Imported from DFMS (arXiv 2202.13730v1), not reproved here.** Don, Fehr, Majenz and Schaffner
define an extractor that simulates the oracle, verifies, measures once and decodes. Corollary 2.7
bounds disagreement between a terminal classical oracle computation and its database replay by
`2v/2^h`. Lemmas 4.1 and 5.1 bound the database events, and Theorems 4.2 and 5.2 instantiate the
approach for S-sound\* commit-and-open protocols. The source states the scope of the import plainly:
only the terminal readout lemma and the bad-database bound are used, and "the following two-output
adaptation is derived here from those ingredients; it is not quoted as a theorem about R29 from the
paper." The quantum-information identity
`Tr_D(Σ_d (I ⊗ |d⟩⟨d|) ρ (I ⊗ |d⟩⟨d|)) = Tr_D(ρ)` is used to justify keeping the adversary's
auxiliary output.

## 3. The algorithm `J`

1. Initialize **one** compressed-oracle simulation and run the adversary once, obtaining `x0, π0,
   x1, π1` and its auxiliary output `Z`. Retain the exact classical packet, including the
   authorization transcript when the correctly simulated experiment provides one.
2. In the **same** oracle execution, run `V(x0, π0)` and then `V(x1, π1)`, obtaining `a0, a1`. Do
   not stop after a rejection, and do not measure the database between them.
3. Measure the compressed-oracle database once, yielding the classical `D`.
4. Compute `w0 = dec(D, x0, π0)` and `w1 = dec(D, x1, π1)`; check `R(x0, w0)` and `R(x1, w1)` by
   local deterministic computation.
5. Output the original packet, both verdicts, and both witness results, failure markers included. Do
   not retry and do not discard failed executions.

`J` is a reduction's extractor, not a public conflict tracer. Its internal `D` is not an extra
certificate field and not a sidecar.

## 4. The joint-lift theorem

Let `Γ` be any classical event on the original packet or log — for the security game, the specific
conflicting-body event. Set

```
p = Pr_real[ Γ and a0 = 1 and a1 = 1 ].
```

Under P1–P4 and the imported terminal readout lemma,

```
p_E  ≥  max(0, p − κ_J),
κ_J  =  min(1, 2(v0 + v1)/2^h + G(Q)),
```

where `p_E` counts outputs satisfying `Γ`, both original acceptances, **and** valid witnesses for
those same `x0, x1`. In the project's extraction contract this composition step has multiplicative
loss `L_J = 1`, conditional on an instantiated matching backend.

*Proof sketch as given.* Simulate the entire real execution through both classical verifiers using
the source's exact oracle simulation. Let `F` be their combined classical computation with output
`(a0, a1)` on the adversary's fixed classical packet. Define `d0, d1` by replaying that same
computation with `D` as its partial oracle, and let
`ReadoutBad = {(a0,a1) ≠ (d0,d1)}`. Applying the readout lemma **once** to `F` with its combined
query bound `v` gives `Pr[ReadoutBad] ≤ 2v/2^h`. Outside `ReadoutBad` and `B_bad`, if both real
verdicts accept then `d0 = d1 = 1`; applying P4's universal implication twice in the **same** `D`
gives `R(x0, w0) = R(x1, w1) = 1`.

Two features of that argument carry the weight. The readout lemma is applied once to the combined
computation, which is why the two outputs need not be extracted separately and why no multiplicative
loss appears. And both implications are drawn from the *same* `D`, which is the reason for the
single terminal measurement.

## 5. What the lift costs

The cost is the additive `κ_J`, and it has two parts: the readout term `2(v0+v1)/2^h` and the
bad-database bound `G(Q)`.

**Ordinary commit-and-open backend.** With `ℓ` commitments and trivial challenge-success parameter
`p_triv`, DFMS Lemma 4.1 supplies, after squaring its transition-capacity bound,

```
G(Q) ≤ [ 2e Q^(3/2) 2^(−h/2)  +  Q sqrt(10 · max(Q ℓ 2^(−h), p_triv)) ]².
```

For a rational upper bound the source uses `(a+b)² ≤ 2a² + 2b²`, `8e² < 60` and
`max(s,t) ≤ s + t`, giving

```
G(Q) ≤ (20ℓ + 60) Q³ / 2^h  +  20 Q² p_triv,
κ_J ≤ min(1, [2(v0 + v1) + (20ℓ + 60)Q³] / 2^h  +  20 Q² p_triv).
```

The executable `ordinary_error_bound` returns exactly that conservative value in rational
arithmetic. It does not infer `ℓ`, `p_triv`, `h`, `Q` or a security level for an absent R29
protocol, and the source warns that the Merkle variant needs its own Lemma 5.1 expression: ordinary
and Merkle parameters must not be mixed.

**A constant that must not be silently changed.** v1.35 derives the coefficient `(20ℓ + 60)`. The
later v1.43 record cites DFMS Theorem 4.2 as `(22ℓ + 60)q³2^-n + 20q²p_triv` and uses that form.
The exact theorem statement was not re-verified against the paper in this build, and the two forms
are not interchangeable at the level of a coefficient. The direction is safe — `22 > 20` is the more
conservative choice — but a reader moving between this domain and domain 06 must know that the
number changed and that the change is unresolved here. Nothing in this repository silently replaces
one with the other.

## 6. Tests

`python3 src/joint_extractor_lift.py --self-test` runs 16 test groups and exits 0.

| Group | What it asserts |
|---|---|
| 01 | exact joint witnesses are produced |
| 02 | one adversary run, with event order adversary → verify → verify → measure |
| 03 | the first rejection does not short-circuit the second verification |
| 04 | auxiliary output and log are preserved by the trace identity |
| 05 | swapped witnesses are rejected |
| 06 | a missing preimage yields a failure marker rather than a wrong witness |
| 07 | the measured database is read-only (`MappingProxyType`) |
| 08 | the canonical inverse (smallest preimage) with bottom entries |
| 09 | no late verification, no second measurement, no second adversary run |
| 10 | packet shape and boolean verdicts |
| 11 | exhaustive Boolean implication over all `2^7` assignments, with exactly 100 satisfying P4 |
| 12 | marginals are not the joint law |
| 13 | a shared bad event is counted once |
| 14 | postselection changes the packet distribution |
| 15 | exact error arithmetic and range checks |
| 16 | `8·e_upper² < 60` with `e_upper = 65/24 + (1/120)/(5/6)`, the rational fact behind the `(20ℓ+60)` simplification |

Test 11 is the one that matters most: it checks P4's implication exhaustively on a small Boolean
model, which is what "quantifies over all instances with the same decoder and database" means in a
testable size. Test 13 is the guard against double-counting the bad event, which is exactly the
error a two-extractor composition would introduce.

## 7. Sizes and cost

| Quantity | Value |
|---|---|
| Source file | 24,572 bytes, 498 lines |
| Recorded suite runtime | 0.001 s (16 tests); the bare invocation prints 13,047 bytes of header |
| Composition loss | `L_J = 1` — no multiplicative loss for this step |
| Additive error | `κ_J = min(1, 2(v0+v1)/2^h + G(Q))` |
| Re-run here | suite `OK`, 16 tests; bare invocation exit 0; see `VERIFICATION.md` |

## 8. Packages and tools used

Python standard library only: `dataclasses`, `fractions`, `itertools`, `types.MappingProxyType`,
`sys`, `unittest`. No file is read or written. `fractions.Fraction` is what makes the error
arithmetic exact rather than floating point, and there is no third-party dependency to install and
no prover to run.

## 9. Validation status

- **Proven.** The event-bookkeeping composition: given P1–P4 and the imported readout lemma, `J`
  succeeds whenever `Γ` holds and both original verifications accept, except on a set of probability
  at most `κ_J`. This is a reduction-level proof; the quantum oracle simulation itself is imported,
  not reimplemented.
- **Imported.** The terminal readout lemma (Corollary 2.7) and the bad-database bounds (Lemmas
  4.1/5.1) from DFMS. The two-output adaptation is this project's own derivation.
- **Measured.** The 16 test groups against a deliberately simple classical test double. The executable
  backend is a stand-in; the source states that it "does not certify QPT security".
- **Missing.** Any concrete protocol satisfying P4 for R29; a quantum simulator implementation; the
  special-soundness witness decoder for a proof of the full R29 relation with a matching
  prover/verifier; and the justification that identifies the proof's ideal oracle with a deployed
  hash. That last one the source flags explicitly: "Identifying it with a deployed hash requires its
  own justification; this extraction-only result does not do that."

## 10. Open items

1. P4 has no instantiation. Every downstream number that uses `κ_J` inherits that gap.
2. The coefficient discrepancy of §5 is unresolved in this repository.
3. The lift's `Γ` is an abstract event. Nothing here shows that a real conflict-production game
   implies a `Γ` for which the lift's hypotheses hold at the stated resources.
4. The v1.29 source package was not available during the writing of v1.35, so integration against
   the exact relation could not be checked. Its authorization code is placed in this repository at
   `domains/03-zk-carrier-experiments/src/authorization.py`; the full package, prover and verifier
   included, is still needed for work against that exact relation.
