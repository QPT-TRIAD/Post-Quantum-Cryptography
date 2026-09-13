# Theory used by the QPT-128 security target

This document takes apart every result the QPT-128 ledger borrows, one entry at a time. Each entry
gives the statement **as used here** (not its textbook form), the part of the result that is used,
the part that is not used and why the borrowed part is enough, and the citation **as the sources
give it**. Where a citation in the source is incomplete, this document says so rather than filling
it in. Where a statement is a project result rather than a borrowed one, it is labelled as such.

The two source files are `src/qpt128_finalization.py` (the exact-arithmetic checker) and
`docs/qpt128-finalization.md` (the document written against it); both are cited below by section.

**A note on labels.** The programme keeps four labels apart: *theorem with proof*, *reduction
sketch*, *model-or-ledger estimate*, and *assumption*. This domain uses them exactly as the sources
do. The entry points that follow are theorems where the source has a proof, and estimates where the
source says "roughly".

---

## 1. Grover's search algorithm, in its success-probability form

**Statement as used.** Against a search space of `2^n` items with `p` marked, Grover's algorithm
run for `j` iterations succeeds with probability `sin²((2j+1)θ)`, where `sin²θ = p/2^n`. The checker
computes the exact rational lower bound

```
success >= (y − y³/6)²,  y = (2j+1)·sin θ = (2j+1)·sqrt(p/2^n)
```

under two guards: the density exponent `n − log₂p` must be even (so that `sin θ` is a rational
square root), and `y ≤ 1` (so that `(2j+1)θ` stays in the range where the inequality holds).

**Part used.** Only the closed-form success probability, the elementary inequality `θ ≥ sin θ`, and
`sin y ≥ y − y³/6` on `[0,1]`. For Lemma L1 the checker takes `n = 256`, `p = 1`, `j = 2^63`; for
Lemma L2 it takes `j = 3·2^125` (one target) and `j = 3·2^122` (64 targets); test 02 repeats L1 at
`n = 512`.

**Part not used.** Nothing of the algorithm's implementation, its circuit, or its cost; no
amplitude-amplification machinery for an unknown number of solutions; no lower bound on the number
of iterations needed. Refuting a *for-all* statement needs one admissible adversary, not an
optimal one, so a **lower** bound at one chosen iteration count is exactly the right instrument.
That asymmetry is why the lemma is a refutation and not a security claim: it says a small adversary
succeeds, never that a large one cannot.

**Statement as the sources give it.** The source document states the law without a citation
(`docs/qpt128-finalization.md` §2, Lemma L1; `src/qpt128_finalization.py`, docstring §1). The
checker's only guard is the range condition above. The programme's theory index records the
citation as "standard (added): Grover, STOC 1996" — added by the index, **not present in either
source file**.

**Where the Boyer–Brassard–Høyer–Tapp form is cited.** Not here. The `sin²((2j+1)θ)` expression is
cited to Boyer–Brassard–Høyer–Tapp §2 inside the v1.42 conditioning audit of another domain
(`domains/05-extraction-and-signature-reductions/src/slh_tree_conditioning_audit.py:213-215`). For
this domain the citation status is therefore **incomplete in the source**: the law is stated bare.

---

## 2. The union bound (Lemma L3)

**Statement as used.** If the winning event is contained in a union of bad events, `Win ⊆ ∪ Bad_i`,
and each `Bad_i` has `Pr[Bad_i] ≤ ρ_i(G)`, then `Pr[Win] ≤ Σ_i ρ_i(G)`. In the checker this becomes a
criterion: if `Σ_i max_{1≤G≤2^128} ρ_i(G)/G ≤ 2^−130`, then D2 holds with `κ = 130`.

**Part used.** Sub-additivity of probability and the cover condition. That is the whole of it. The
bound needs no independence, no disjointness, and no structure on the `Bad_i` — which is precisely
why it can compose heterogeneous rows (an extraction failure, a simulation distinguishing advantage,
a preimage search) into one number.

**Part not used.** Any refinement — no Chernoff, no martingale, no union bound over a filtered
family. The project's arithmetic rule `8·2^−131 = 2^−128` is asserted by the checker (test 05) and
is valid arithmetic **on the per-gate coefficients**; it is not the acceptance criterion. The
criterion is the exact sum of the row ratios against `2^−130`.

**Where the union bound is legitimate, and where it is not.** It is legitimate only over a family
that provably covers the winning event, and the ledger's coverage is argued per scenario in
`docs/qpt128-finalization.md` §4 and §5 (Theorem A cases, Theorem B cases). It is **not** legitimate
as a way of importing unproved terms: four rows (E6, E7, E8 and B0's canonical-encoding/rollback
row) are set to exactly zero because their content is a model premise — HVZK on uniform tapes, an
ideal collaborative prover, canonical encoding and durable state. Zero is a statement about the
model, not a proof that the events cannot occur. `docs/ledger.md` §5 states the same limitation in
the ledger's own terms.

**Citation.** Elementary; no citation is given in either source. Not a borrowed result.

---

## 3. Convexity and endpoint evaluation (Lemma L4)

**Statement as used.** Let `ρ(q)` be a polynomial in `q = G/g` with non-negative coefficients. Then
`ρ(G/g)/G` is convex in `G > 0`, so its maximum over the interval `[1, 2^128]` is attained at an
endpoint. The checker therefore evaluates the uncapped envelope at `G = 1` and `G = 2^128` and takes
the larger ratio (`ratio_bound`). Rows whose envelope is a decreasing square-root form are evaluated
at `G = 1`.

**Part used.** The convexity of a polynomial with non-negative coefficients divided by its argument,
and the resulting endpoint criterion.

**Part not used, and the trap it avoids.** A **capped** envelope `min(1, ρ)` is not convex: its ratio
can peak in the interior where the cap begins to bind. The checker therefore never maximises a capped
envelope — caps are applied only to the D1 probability at the budget edge. Test 19 exhibits a capped
envelope whose interior ratio exceeds both endpoint ratios, and shows that the uncapped endpoint bound
still dominates the interior value.

**Citation.** Elementary, and stated as such; the source gives no proof text beyond the statement. The
programme's theory index records this entry as "elementary convexity, 'no proof text beyond the
statement'". For a standard proof, the convexity step would need to be written out; as arithmetic it
is checked by tests 06 and 19 at 43 sampled budgets.

---

## 4. Commit-and-open extraction in the QROM — DFMS Theorem 4.2

**Statement as used.**

```
epsilon_ex <= (22*ell + 60) * q^3 * 2^-n  +  20 * q^2 * p_triv
```

together with the fact that the online extractor runs in `O(q²)·poly` time. Here `q` is the number
of oracle queries, `n` the challenge/commitment security parameter, `ell` the number of committed
bits per repetition and `p_triv` the probability that a repetition is trivially answerable.

**Part used.** The bound's shape, with a rational envelope, and the running-time statement. The
running-time statement is the premise of Lemma L5 — the charge that decides which instantiations
pass — and it is used only in that form (`t_B ≈ G + a·q²·g_sim`).

**Part not used.** The extractor's construction, its measurement of the compressed-oracle database,
and the two-output case. The two-output (joint) case is supplied by the project's own lift, entry 5
below.

**The project's Lemma L5, which is made of this running-time statement.** L5 is not a borrowed
result; it is the consequence the sources draw from the running time above. Its statement as used is
(`docs/qpt128-finalization.md` §2, Lemma L5):

```
any reduction that uses an extracted witness runs in time  t_B ~= G + a*q^2*g_sim,
and if F's generic attack bound is c*(t/g_F)^e / 2^n, then D2 requires roughly
  n >= (2e-1)*128 + 130 + log2 c + e*log2(a*g_sim) - 2e*log2 g_H - e*log2 g_F.
```

Two things follow, and the sources keep them apart. The **shape** — that an extracted witness doubles
the exponent of the generic attack — is what makes compat mode fail and what forces the 1024-bit
registry keys. The **inequality** is labelled an estimate: the source's own word is "roughly", no
proof text accompanies it, and the checker never evaluates it — the checker evaluates the exact rows
instead. It is therefore a model-or-ledger estimate, not a theorem, and it decides no verdict in the
report.

**Citation as the sources give it.** "Don–Fehr–Majenz–Schaffner, CRYPTO 2022, Thm 4.2"
(`docs/qpt128-finalization.md` §3). No paper title and no ePrint/arXiv identifier appear in either
D6 source file, so **the citation is incomplete in D6**; the identifier is recorded elsewhere in the
programme (the research trail carries the arXiv id, and the D5 domain gives the title).

**A coefficient discrepancy, recorded and not resolved.** The D5 derivation of the project's lift
uses `20ℓ + 60`, D6's row uses `22ℓ + 60`, and the D4 source ledger records `72 + 40ℓ`. The programme's
index treats these as one source read at three different times. This domain does not choose between
them: the checker uses `22ℓ + 60` and test 09 fixes the repetition counts exactly under that choice.
If the coefficient is smaller, the row is smaller and the verdicts move in the safe direction; that
is an observation about monotonicity, not a re-derivation.

---

## 5. The project's joint two-proof lift (v1.35)

**Statement as used.** Joint extraction of two accepted proofs adds the readout term `2(v₀+v₁)·2^−n`
over a single measured database, on top of the DFMS bound. In the checker this is

```
joint_extraction(q, n, ell, p_triv, v) = 2*v*2^-n + (22*ell + 60)*q^3*2^-n + 20*q^2*p_triv
```

with `v = 2(1+3r)` for the four-subset backend (§9).

**Part used.** The additive readout term and the single-database accounting — the property that makes
one extraction charge cover both proofs.

**Part not used.** The v1.35 document's full case analysis; the ledger uses only the row value.

**Citation.** A project result, not borrowed theory; the source cites it as "project v1.35 lift of
DFMS Cor. 2.7", with the code pointer
`domains/05-extraction-and-signature-reductions/src/joint_extractor_lift.py:95-138`. It is a reduction
sketch in the programme's own classification (D5 records the joint-lift theorem as such).

---

## 6. Fiat–Shamir simulation — GHHM Theorem 3

**Statement as used.**

```
epsilon_sim <= (3*q_s/2) * sqrt((q_H + q_s + 1) * gamma(Commit))  +  q_s * Delta_HVZK
```

with `q_s = 2^64` honest proofs per key, commitment min-entropy premise `γ ≤ 2^−512`, and `Δ_HVZK`
set to zero (row E6, a model premise).

**Part used.** The first term only. The checker takes a rigorous rational upper bound on the square
root (`sqrt_upper`, using `math.isqrt` on a `2^−100` grid) so that the row dominates the theorem's
bound exactly; test 17 checks the bound is rigorous and tight for six values of `x` and test 18
checks that the row dominates `(3/2)·q_s·√(q+q_s+1)·2^−256` at four query counts and that its ratio
is ≤ `2^−131` in gate units.

**Part not used.** The `q_s·Δ_HVZK` term. Setting it to zero is the model premise "HVZK with uniform
tapes" (row E6). The source states this as a premise; it is not proved here.

**Citation as the source gives it.** "Grilo–Hövelmanns–Hülsing–Majenz, ASIACRYPT 2021, Thm 3"
(`docs/qpt128-finalization.md` §3). No title → **incomplete in the source**.

---

## 7. Search and preimage — HRS16 Theorem 1

**Statement as used.**

```
hrs16_search(q, n, p) = 8 * p * (q+1)^2 / 2^n          (capped at 1 for the D1 probability)
```

with `λ = p/2^n` the marked fraction and `p` the number of targets: `p = 64` for E3 (the 64 honest
credentials, `n = 512`, so the row is `8·64·(t_B/g_F + 1)²/2^512`), `p = C(64,2) = 2016` for E5, and
`p = 1` with `n = 256` for the category-5 signature envelope of B0.

**Part used.** The bound's closed form in the QROM, with the multi-target factor `p` carried
explicitly. The multi-target factor is why the ledger's rows differ between "one key" and "64
keys" — the same structure that Lemma L2 uses on the attack side.

**Part not used.** The underlying compressed-oracle/QROM framework, its reprogramming step, and the
proof of the bound. The ledger needs a number and a target multiplicity; it does not need the
mechanism.

**Citation as the sources give it.** "Hülsing–Rijneveld–Song, ePrint 2015/1256, Thm 1 (λ = p/2^n)"
(`docs/qpt128-finalization.md` §3). The ePrint identifier is given, the **title is not** →
incomplete in the source.

---

## 8. Collision — CFHL Theorem 5.29

**Statement as used.** The published form is

```
(2e(q+1) * sqrt(10(q+1)/M) + sqrt(2/M))^2          leading term 40*e^2*(q+1)^3/M ≈ 295.6*(q+1)^3/M
```

and the checker uses the rational envelope

```
cfhl_collision(q, n) = 80 * e^2 * (q+1)^3 * 2^-n + 4 * 2^-n
```

obtained from the published form by `(a+b)² ≤ 2a² + 2b²` with `e` replaced by the rational upper
bound `27182818285/10^10`.

**Part used.** The closed form of the bound only, and the leading constant. The checker's envelope is
deliberately a factor ≈ 2 above the published leading term (`80e²` against `40e²`), which is
conservative: tests 07 and 14 pin the envelope's behaviour and its relation to the unsourced legacy
constant of §13.

**Part not used.** The compressed-oracle technique that proves the bound, and the `M`-dependence
beyond the closed form.

**Citation as the sources give it.** "Chung–Fehr–Huang–Liao, EUROCRYPT 2021, Thm 5.29"
(`docs/qpt128-finalization.md` §3). No title → **incomplete in the source**.

---

## 9. The four-subset ZKBoo backend parameters (v1.36, project)

**Statement as used.** For `r` repetitions of the v1.36 four-subset commit-and-open protocol:
`ell = 4r` committed bits per repetition, `p_triv = (3/4)^r` trivial-answer probability, `v = 2(1+3r)`
verifier queries for the joint two-proof case, and `2r` challenge bits per repetition. The checker
encodes exactly this in `zkboo4_parameters(r)`; test 08 checks `r = 3` gives `(12, 27/64, 6)`.

**Part used.** The parameterisation, because the extraction row's `p_triv` term is what forces
`r = 553` (gates) or `r = 640` (queries) to bring the row's ratio to `2^−133`. The dominant term at
the budget edge is `20q²(3/4)^r/2^128`.

**Part not used.** The protocol's own soundness and zero-knowledge proofs, which belong to D5, and the
protocol itself — no backend is implemented in this domain.

**Citation.** A project result (v1.36), recorded in the checker as
`zkboo4_parameters(r)`: "v1.36 four-subset ZKBoo commit-and-open". It is the only *concrete* backend
in the programme, and the ledger's extraction row is conditional on it satisfying DFMS's premises.

---

## 10. The UOV QROM route — Kosuge–Xagawa Theorem 1

**Statement as used.** A cited route for the B0 signature's QROM security: UOV's proof goes through
Kosuge–Xagawa, ePrint 2022/1359, Thm 1, which carries a `(2q+1)²` loss on the underlying inversion
problem. The source states that this loss belongs to the scheme's own security proof and not to the
CE-QS composition.

**Part used.** Its existence, as evidence that at least one size-conforming category-5 signature has
a recorded QROM proof route. **It contributes no numeric term to the ledger** — B0's row is evaluated
with the AES-256 key-search envelope (§12), not with the scheme's proof.

**Citation as the source gives it.** "Kosuge–Xagawa, ePrint 2022/1359, Thm 1" — ePrint identifier
given, no title → incomplete in the source.

---

## 11. The NIST category-5 definition

**Statement as used.** Category 5 means "resources comparable to AES-256 key search"
(`docs/qpt128-finalization.md` §2, Lemma L2). The source uses it for one purpose only: to justify
charging each oracle query its circuit cost, i.e. to justify counting gates rather than queries.

**Part used.** The definition as a calibration of the budget.

**Part not used.** Any of NIST's document structure, its category tables, or its parameter sets. No
NIST document number, version or date appears in the source → the citation is **incomplete in the
source**; the definition is quoted, not referenced.

---

## 12. Circuit-cost measurements (T-counts)

**Statement as used.** Two literature numbers set the ledger's floors:

| Quantity | Value as recorded | Used as |
|---|---|---|
| SHA3-256/Keccak oracle T-count | 499,200 (≈ 2^18.93) | floor `g_H = g_F = 2^18` |
| SHA3-256 Grover preimage total cost | 2^166.5 | the "why gates" argument (L2) |
| AES-256 oracle T-count | 75,580 | floor `g_AES-iteration = 2^17` |
| AES-256 Grover G-cost | 1.17·2^148 without a depth limit | quoted, not charged |

The emitted `--report` units are "queries (one gate per query)" and "gates, one query = 2^18 gates";
the AES iteration floor `2^17` is used inside the B0 and compat rows, where one Grover iteration
counts as two AES-256 oracle calls, T-gates only.

**Part used.** The T-counts, as floors. Both are *measurements* on published circuit constructions,
not bounds: the ledger treats them as lower bounds on the true cost of an oracle call, which is the
direction that makes the ledger's charges conservative.

**Part not used.** The circuit constructions themselves, and the depth-limited AES costing (which
would raise the cost). The source says plainly that depth, parallelism and memory are not charged.

**Citation as the sources give it.** "Amy et al., SAC 2016, Tables 2–3" and
"Jaques–Naehrig–Roetteler–Virdia (revised), Tables 9 and 11". Venue and table numbers are given; no
titles, no DOIs, no ePrint identifiers → **incomplete in the source**.

---

## 13. The unsourced constant `12(q+154)³/2^n` — not a borrowed result

The research trail used this expression for the collision term at `pqt.md:1667-1675` without a
reference. It is **not found** in any source the programme consulted. The checker keeps it in one
function, `unused_legacy_12q154`, solely to measure the discrepancy: at `q = 2^128`, `n = 512` the
legacy value's logarithm is −124.415, the published CFHL leading term gives ≈ −119.8, and the
checker's rational envelope gives −118.793 (report key `unsourced_12q154_check`, test 14). The
correction is recorded in `docs/qpt128-finalization.md` §7 item 2. This entry is listed here so that
nobody later mistakes the expression for a citation.

---

## 14. Citations the programme's index adds, and which the sources do not contain

The D6 sources give author lists, venues, theorem numbers, table numbers and one ePrint identifier —
and no paper titles. The programme's theory-and-package index supplies the identifications below and
marks them as *added* knowledge, not as citations made by the source files. They are reproduced here
with that mark, so that a reader can find the papers; **they are not presented as the sources'
references, and no attempt was made here to verify them against the papers.**

| Source as cited | Identification recorded in the index as added |
|---|---|
| Grover, STOC 1996 | search algorithm citation, standard |
| Hülsing–Rijneveld–Song, ePrint 2015/1256 | "Mitigating Multi-Target Attacks in Hash-based Signatures" (PKC 2016) |
| Chung–Fehr–Huang–Liao, EUROCRYPT 2021 | "On the Compressed-Oracle Technique, and Post-Quantum Security of Proofs of Sequential Work" |
| Don–Fehr–Majenz–Schaffner, CRYPTO 2022 | "Efficient NIZKs and Signatures from Commit-and-Open Protocols in the QROM" (the title is present in the D5 sources, not in D6) |
| Grilo–Hövelmanns–Hülsing–Majenz, ASIACRYPT 2021 | "Tight Adaptive Reprogramming in the QROM" |
| Amy et al., SAC 2016 | "Estimating the Cost of Generic Quantum Pre-image Attacks on SHA-2 and SHA-3" |
| Jaques–Naehrig–Roetteler–Virdia (revised) | "Implementing Grover Oracles for Quantum Key Search on AES and LowMC" (EUROCRYPT 2020) |

The source document additionally states that its constants were "all checked against full texts"
(§3 title) and that formulas were checked against the papers. That is a **process claim**: it is not
reproducible from the files, and this repository records it as a claim, not as a verification. It is
the first open item below.

---

## 15. Open items for this theory set

1. **Constants provenance.** Each borrowed bound — the DFMS coefficient (`22ℓ+60` here, `20ℓ+60` in
   D5, `72+40ℓ` in D4), the CFHL form, HRS16 with `λ = p/2^n`, GHHM Theorem 3, the two T-counts —
   should be checked against the full text of the paper. Today the check is a process claim.
2. **Citations are incomplete in the source.** No paper titles appear in the D6 sources; §14's
   identifications come from the programme's index and carry its "added" label.
3. **Named assumptions are not theorems.** A-sig, A-QROM, A-F, A-cost, A-γ, A-MPC and A-protocol
   (`docs/qpt128-finalization.md` §5) are premises of Theorems A and B.
4. **Model-premise rows are set to zero** (E6, E7, E8, and B0's rollback row). Each needs its own
   argument or an explicit charge.
5. **L4's convexity claim is stated, not written out**; L5 is an estimate whose word is "roughly".
6. **The QROM is a model.** The programme records that a fixed hash is never indistinguishable from
   a random oracle; no treatment of the QROM-to-SHAKE256 gap is offered.

Where these items bear on the numbers, `docs/ledger.md` says so in place.
