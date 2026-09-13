# The theory the ledger borrows

The ledger borrows eight external sources, states eight lemmas of its own, and carries one counting
fact that several other domains in this repository also use. For each item below: what it is, the
statement *as used here* rather than its textbook form, what it is used to justify, which part is
borrowed, which part is not used and why the borrowed part suffices, and the citation exactly as the
ledger gives it. Line numbers are for `operator-ledger.md` in the parent directory.

The listing is deliberately unsentimental about citation quality. Where the ledger's reference is
incomplete, that is stated; no reference has been completed from memory or from a search.

## The eight formal sources `[S1]`–`[S8]`

Defined at lines 284–298. The ledger prefaces the list with a scope sentence of its own (286):
"These are theorem/definition sources, not interchangeable components. The new algebraic proofs
above are supplied in full. The original catalog's unrelated mathematical claims are not all
independently literature-certified by this amendment."

| Tag | As the ledger gives it | Where cited | Which part is borrowed, and why that part suffices |
|---|---|---|---|
| `[S1]` | Don, Fehr, Majenz and Schaffner; "Efficient NIZKs and Signatures from Commit-and-Open Protocols in the QROM"; arXiv 2202.13730; 2022 — with the scope sentence "inspect the special-soundness and Merkle-commitment hypotheses before applying them" (288) | 89 (Lemma 1's boundary), 507 (`A10`), 627 (`A18`) | Only the extraction theorems for commit-and-open under special-soundness and Merkle-commitment hypotheses. Those are what bound the joint-extraction expression `J` and what the decoder interface of `A18` is being pulled back from. The whole paper is not used: nothing else in it bears on the contraction, sampler or signature obligations. **The hypotheses are explicitly not shown for the current verifier** — "This document does not establish that the current verifier satisfies those hypotheses" (89). The ledger gives no theorem number. |
| `[S2]` | Barbosa et al.; "Fixing and Mechanizing the Security Proof of Fiat-Shamir with Aborts and Dilithium"; **Theorem 2**; ir.cwi.nl/pub/33405; no year (289) | 612 (`A17`) | Theorem 2 only: the corrected QROM CMA-to-NMA reduction with a compatible good-key event and an explicit additive loss. Used to turn a signature-security label into a resource-mapped reduction (`A17`). The additive-loss reduction alone is not a bound on the adversary's NMA advantage, and the ledger says so in the `A17` contract (612): the mechanized proof in the paper is the ROM proof. The author list is truncated to "et al." and no year is given. |
| `[S3]` | Cojocaru, Hhan, Liu, Yamakawa and Yun; "Quantum Lifting for Invertible Permutations and Ideal Ciphers"; **Corollary 6.9** and model definitions; arXiv 2504.18188; 2025 (290) | 267 (Lemma 8), 657 (`A20`), 672 (`A21`) | Only the ideal-permutation sponge collision bounds, under the paper's stated access and call counts. Used to keep the hash obligation property-specific. The rest of the paper is not used. The ledger's own scope sentence is the limit: it "does not certify the fixed deployed permutation" (290, 267). Cited with an arXiv identifier and a corollary number; no venue is given, and none is added here. |
| `[S4]` | Tomamichel, Schaffner, Smith and Renner; "Leftover Hashing Against Quantum Side Information"; **Theorem 6** and the conditional guessing interpretation; arXiv 1002.2436 (291) | 247 (Lemma 6), 567 (`A14`), 732 (`A25`) | Only the leftover hash lemma with quantum side information for independently seeded two-universal hashing. Used for `A14`'s entropy discipline and `A25`'s extraction-with-seed-premise rule. The ledger states the boundary twice: it "applies to independently seeded two-universal hashing with a suitable conditional min-entropy bound. The exact distance convention and smoothing parameters must match an application" (291), and it "is not a theorem about extracting a quorum witness from a public proof" (268, 732). No venue or year; the arXiv identifier is complete. |
| `[S5]` | Keccak designers; "Keccak specifications summary", standard-instance table; keccak.team (292) | 672 (`A21`) | One parameter fact only: SHAKE256 has rate 1088 bits and capacity 512 bits with variable output length, and output width is not capacity. This is what `A21` rests on when it refuses to let a 720-bit or 832-bit challenge source raise the underlying permutation's strength. Nothing else in the specification is used. **The reference is a web page with no date and no version.** The normative specification for the deployed function is a NIST standard; the ledger does not cite it. |
| `[S6]` | NIST; "FIPS 204: Module-Lattice-Based Digital Signature Standard"; 2024 (293) | 612 (`A17`) | Only the algorithms and parameter sets, as the target the implementation adapter must match. The ledger adds: "this document does not alter them" (293). Used to keep `A17`'s reduction contract anchored to a specific parameter set rather than to a NIST category, and the ledger warns in the same contract that "a NIST category is not a theorem about every specified gate/probability budget" (612). Reference complete as given. |
| `[S7]` | John Watrous; "The Theory of Quantum Information", channel and instrument definitions in **Chapter 2** (294) | 130 (Lemma 2) | Only the finite-dimensional Kraus and positive-map conventions used in Lemma 2's contraction proof. The textbook's results are not otherwise used. This is the right and sufficient borrow: Lemma 2 is a statement about a completely positive trace-nonincreasing instrument, and what it needs from the literature is the definition of one, not a theorem about it. |
| `[S8]` | Christof Zalka; "Grover's quantum searching algorithm is optimal"; arXiv quant-ph/9711070 (295) | 255 (Lemma 7) | Only search-specific resource reasoning — the parallel-search work/depth trade-off that Lemma 7's second reading uses. The ledger states the limit in the source list itself: "not a blanket hardness theorem for all quantum attacks" (295). Nothing is borrowed from it about lattice algorithms. |

### Citation quality of the eight

Checked over the whole document:

- **8 URLs**, all in the source list (lines 288–295), none with query or tracking parameters.
- **4 arXiv identifiers**: 2202.13730 (288), 2504.18188 (290), 1002.2436 (291), quant-ph/9711070 (295).
- **4 theorem/corollary/chapter locators**: "Theorem 2" (289), "Corollary 6.9" (290), "Theorem 6" (291), "Chapter 2" (294).
- **0** IACR ePrint, RFC, DOI, ISBN or NIST SP locators. **0** conference names anywhere in a citation.
- **2 SHA-256 digests**, both for absent input files (300, 302).
- **14 citation instances** in the whole document, on 12 lines: 5 in bracketed form `[S#]` (lines
  89, 130, 247, 255, 267) and 9 in the unbracketed form "External reference(s) S#", on 7 lines —
  612 and 672 each name two sources. Per source: `S1` 3, `S2` 1, `S3` 3, `S4` 3, `S5` 1, `S6` 1,
  `S7` 1, `S8` 1. Every one of them is in the lemma or investigation sections. **None falls on a
  catalogue entry.** The eight lines of the source list itself (288–295) are definitions, not
  citations, and are excluded from this count.

Gaps a reader must know about:

- `[S1]` is cited without a theorem number, so the exact extraction theorem being borrowed cannot be
  located from the ledger alone. A later project document, held in domain D6 of this
  repository, identifies the paper as a CRYPTO 2022 publication and cites its Theorem 4.2; that
  identification is that document's, not the ledger's, and is not evidence that the ledger's constants match.
- `[S2]` has no year and a truncated author list.
- `[S5]` is a web page with no date. The normative specification of the deployed function is a NIST
  standard, and the ledger does not cite it.
- `[S3]`'s venue is not given.
- The ledger uses `[S1]`–`[S8]` as source tags while `S1`–`S50` are also *spectral operators* in
  family S. At line 488 `[S7](#op-s7)` and at line 503 `[S9](#op-s9)` are operator links, not
  citations. A reader or a `grep` can mistake them for sources. The same collision exists for `D`
  (the reduction's compressed-oracle database versus the discrete-difference family), `Q` (the query
  count versus the q-deformed family, and the quorum size in other domains), and `L1` (lattice
  operator L1 versus a lemma of a later project document).

## The eight lemmas (lines 66–270)

Preceded by the ledger's own scope sentence (68): "elementary derivations for this amendment. They
are not claims of new results in the mathematics literature. Any protocol-level application must
discharge the stated premises." Each has its proof written out in the text. The label below is the
ledger's own; the premise column is what the lemma needs before it says anything about the protocol.

| Lemma | Statement as used | What it justifies | Label | Premise the protocol application needs |
|---|---|---|---|---|
| 1 — budget inversion (70–90) | With `J = B₀ + 20Q²p_*` and `B₀ = ((72+40ℓ)Q³ + 2v)/2^h`: for `Q > 0`, `p_* ≥ 0`, `J ≤ τ` iff `p_* ≤ (τ − B₀)/(20Q²)`, provided `B₀ < τ`; `B₀ = τ` allows only `p_* = 0`, `B₀ > τ` is infeasible. Union bound without independence via `1_(∪Eᵢ) ≤ Σ1_(Eᵢ)`. | Inverting the total error budget into a per-round bound on the nonextractable challenge mass; `A01`. | theorem-with-proof (elementary algebra) | That the `J` expression applies to the current verifier at all. The ledger: "This is algebraic inversion, not a proof that the desired `p_*` can be achieved" (85). |
| 2 — adaptive failure contraction (91–133) | Classical: if `Pr[B_t \| H_{t−1}] ≤ β_t` uniformly over reachable all-failed histories, then `Pr[∩B_t] ≤ ∏β_t`. Quantum: for a completely positive failure map `Φ_t(ρ) = Σ_j K_{t,j}ρK_{t,j}†`, the certificate `Σ_j K†K ⪯ β_t I` on every reachable failure subspace gives `tr Φ_t(ρ) ≤ β_t tr ρ`. | Bounding per-round failure for an adaptive adversary; `A05`, `A06`, `A08`. | theorem-with-proof (tower property; [S7] conventions) | That the certificate holds for the real verifier's failure instrument. The ledger: the connection to `p_*` is **open** (152). It also warns (130) that conditioning on survival and renormalising "would discard exactly the probability being bounded", and that a unitary alone does not produce this contraction. |
| 3 — robust contraction (134–178) | `‖K‖ ≤ ‖K₀‖ + ‖K − K₀‖ ≤ 2^{-1/2} + η`, applied to the stacked map `A: v ↦ Σ\|j⟩⊗K_j v` because `A†A = ΣK_j†K_j`. A sufficient certificate is `ΣK_j†K_j ⪯ (9/16)I`, giving amplitude `3/4` and an allowance of at most `3/4 − 1/√2 ≈ 0.0428932` over the ideal `1/√2`. | The repetition count under an imperfect per-round channel, and the 320-round figure. | theorem-with-proof for the arithmetic; the `9/16` premise is an **assumption** for the protocol | That some concrete instrument satisfies the `9/16` certificate. "No such allowance has yet been proved for the actual protocol" (150). The perturbation must be proved for the whole stacked map; per-entry numerical errors cannot stand in for `η` (138–142). One wording caution: line 150 reads "the sufficient absolute perturbation allowance is at most `3/4 − 1/√2`", which means an allowance `η ≤ 3/4 − 1/√2` suffices, not that larger `η` is inadmissible. |
| 4 — exact maximal mass for base-b product boxes (179–207) | Write `2^h = a·b^r + R` with `0 ≤ R < b^r`, let `C_{b,t,r}(R)` count the `x < R` whose every base-`b` digit is below `t`, and the maximal mass of a box allowing at most `t` digits per coordinate is `p_max(h,b,t,r) = (a·t^r + C_{b,t,r}(R))/2^h`. | Counting the worst bad-box challenge mass; `A11`. Explains the earlier ternary failure as saturation. | theorem-with-proof, machine-checked at small sizes | That every nonextractable challenge set lies in such a product box. "The decoder must imply the product-box containment. A general nonextractable family may not have this structure … no generic conversion from three-response to two-response special soundness follows" (206). |
| 5 — compatible good events and finite retry tails (208–228) | If `X ≥ 0`, `Pr[G₁ᶜ] ≤ d₁`, `Pr[G₂ᶜ] ≤ d₂`, `d₁ + d₂ < 1` and `E[X \| G₁] ≤ ε`, then `E[X \| G₁ ∩ G₂] ≤ ε(1−d₁)/(1−d₁−d₂)`. Retry tail: conditional rejection at most `p` in every reachable history gives `p^R`, and a union over `q_S` sessions gives `q_S·p^R`. | Gluing good-key events without assuming independence; `A13`, `A16`. | theorem-with-proof; the input bound `p` is an assumption | Two of them. That `G₁` and `G₂` are the actual good-key events, and that `p ≤ 759/1024` holds uniformly rather than on average. The ledger: "The input bound `p` remains a condition, not a fact established by this test" (227). |
| 6 — finite-field rank counting and entropy discipline (229–248) | `N_{m,n,r}(q) = ∏_{i<r} (q^m − q^i)(q^n − q^i)/(q^r − q^i)` for rank-`r` `m×n` matrices over `F_q`, with the counts summing to `q^{mn}`. And `H_min(f(X) \| E) ≤ H_min(X \| E)` for deterministic `f`, because merging the POVM cannot lower the guessing probability. | The rank census behind `A15`, and the entropy monotonicity behind `A14`. | theorem-with-proof | For the rank count, a uniform finite-field distribution: "This does not make a seeded, module-structured matrix uniform; that distribution step is separate" (238). For the entropy statement, nothing — the monotonicity is unconditional, and the limitation is in what it is about. |
| 7 — resource composition; the limited MAXDEPTH reading (249–256) | Total work is `Σ_v g_v`; critical-path depth is `depth(v) = d_v + max` over predecessors. Fewer processors or a shared oracle add constraints and "do not reduce total work" (251). Monotone time maps compose as `g(f(·))` and affine advantage losses as `ε_A ≤ a·c·ε_C + a·d + b`; "probability loss and time inflation are distinct" (253). | Work/depth accounting and reduction-cost composition; `A04`, `A22`. | theorem-with-proof (elementary); **MAXDEPTH is not a security argument** | None for the arithmetic. The limit is stated in the lemma itself: MAXDEPTH "cannot be used to erase unrelated proof obligations" (255), and the search model of `[S8]` "does not establish security against lattice algorithms, arbitrary quantum algorithms, or attacks on the actual signature". |
| 8 — quantifier and idealisation substitutions (257–270) | Weak duality `sup_y inf_x u ≤ inf_x sup_y u`; pure matching pennies realises `−1` and `1`, so equality needs a minimax theorem with mixed strategies. A fixed public hash `H₀` is distinguishable from an independent random oracle by a one-query equality test at `x₀`, with acceptance gap `1 − 2^-h`. | Keeping the worst-case quantifiers (`A03`) and refusing generic random-oracle equivalence (`A20`). Also the type-level obstruction of `A19`: a public trace cannot use a reduction-only database without an explicit algorithmic route. | theorem-with-proof | None for the weak-duality half. For the hash half, the conclusion is a negative one: `[S3]` "works with a uniformly random permutation, not a proof that a fixed named permutation is random" (267). The lemma refutes a *generic* fixed-function-versus-independent-oracle premise; it does not refute ideal-permutation indifferentiability with a simulator, nor a separately assumed game-specific hash property. |

## The one counting fact

**Quorum intersection.** `|S₀ ∩ S₁| ≥ |S₀| + |S₁| − N`; a threshold `t` therefore yields at least
`2t − N` common identities. The ledger states it in the `A24` contract (715) and labels it "only a
set-counting lemma" (717). The checker exhausts 441 ordered pairs of 5-element subsets of `{0..6}`,
confirming every pair intersects in at least `5 + 5 − 7 = 3`.

This is elementary set counting, and the ledger's own caveat is what a reader should carry away:
the relation still needs "distinct registered signer identities, actual valid signatures, canonical
statements and message/epoch binding. Economic equilibria do not supply authorization" (717). A
counting fact about intersections is not an authorization theorem.

The same fact appears in other domains of this repository as the quorum safety premise with this
project's parameters `N = 64`, `t = 43`, giving `22`; the ledger itself does not state those
parameters. It is one elementary fact stated in several places, and the repository presents it once.

## The borrowed constant, and its two later divergences

The joint-extraction expression at lines 74–76,

```
J(Q, h, p_*) = ((72 + 40ℓ)Q³ + 2v)/2^h + 20Q²p_*
```

is the quantitative core of the first half, and its provenance is the weakest part of the record.
The ledger's only attribution is "the supplied workspace report v1.32" (89) and, in its own words,
"A conservative bound obtained from the paper's database lemma" with "This extension is my
derivation from the published lemmas". The report is absent from the tree. The checker implements
the same expression at its line 19276. **No theorem number, no page, no equation.**

Two later project documents diverge from it, neither of which flags the ledger as wrong:

| Constant | Where | Basis |
|---|---|---|
| `(72 + 40ℓ)Q³ + 2v` | This ledger, lines 74–76 and checker 19276 | "supplied workspace report v1.32"; self-derived extension of `[S1]` |
| `(20ℓ + 60)Q³ + 2(v₀ + v₁)` | A later script in this repository, held in domain D5 | Re-derived from the commit-and-open database lemma |
| `(22ℓ + 60)q³ + 20q²·p_triv` | A later finalisation document in this repository, held in domain D6 | Recorded as the published commit-and-open theorem's bound |

The coefficient `72 + 40ℓ` is larger than `22 + 60` in the `Q³` term, so on that reading it is
conservative — but the reading is that of another document, and no document in this repository
proves the derivation. At `Q = 2^128`, `h = 512` the `Q³` term is about `2^-102.68` under this
ledger's constants, `2^-103.68` under the first later variant and `2^-103.54` under the second. The
minimum-round tables of Lemma 3 are identical under all three, so the headline numbers do not move;
only the record's consistency does. Cross-domain links to the two later documents are in the domain
README.
