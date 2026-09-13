# Commitment, opening and extraction

This document holds the results the programme uses to turn an accepted proof into a witness: the
commit-and-open extraction theorems, the concrete backend that satisfies their premises, the
leftover-hashing lemma that supplies the entropy argument, and the ideal-permutation and
compressed-oracle statements that bound what a random oracle can be assumed to give.

The single most important entry here is the DFMS commit-and-open bound. It appears in five domains and
in three coefficient variants (all three are the *same* source read at three different times) and it is
presented **once**, below, with the variants tabulated.

---

## 1. DFMS commit-and-open extraction

### D0-04 / D4 `S1` / D5-03 / D6-06 / D8-06 — Don–Fehr–Majenz–Schaffner commit-and-open in the QROM

- **Statement as used here.** For a Fiat–Shamir commit-and-open proof in the quantum random-oracle
  model, extraction of the committed witness succeeds with
  `p_E ≥ max(0, p − κ_J)` where `κ_J = min(1, 2(v₀+v₁)/2^h + G(Q))` and the joint loss `L_J = 1`;
  the extraction charge is a polynomial in the query count `Q` — `G(Q) ≤ (20ℓ+60)Q³/2^h + 20Q²·p_triv`
  in the v1.35 form, `(22ℓ+60)Q³/2^-n + 20q²·p_triv` in the finalization form — and the extractor runs
  in `O(Q²)·poly` time. The terminal readout disagreement is bounded by `2v/2^h` (Corollary 2.7).
- **Role.** The extraction charge of the composed error budget, and the reason the programme's
  sampler change had to pay an extraction cost at all.
- **Label.** `[T]` theorem-with-proof **under premises P1–P4** and the DFMS readout lemma (reduction
  level). The source's own scope sentence: "inspect the special-soundness and Merkle-commitment
  hypotheses before applying them".
- **Citation as the source gives it.** Don, Fehr, Majenz, Schaffner; "Efficient NIZKs and Signatures
  from Commit-and-Open Protocols in the QROM"; arXiv 2202.13730; 2022. The venue and theorem number
  appear only through the project's own finalization document, which cites it as "DFMS, CRYPTO 2022,
  Theorem 4.2". The audit stack's source list records the citation as **incomplete in source**
  (no theorem number) and D5's extractor lists it as `[S2]` by URL (arxiv.org/abs/2202.13730) with
  Definitions 3.5 and the Sections 4–5 construction.
- **Borrow.** **Partial.** The parts used are the terminal readout lemma (the disagreement bound) and
  the bad-database bound. The two-output adaptation used to extract *both* witnesses of a conflicting
  certificate pair from **one** execution is the project's own derivation and is not quoted as a theorem
  about the programme's relation from the paper. That adaptation is labelled as a theorem-with-proof for
  the project under premises P1–P4, not as a citation.
- **Where used, five guises.**
  1. Domain `docs/01-research-journey` — the route that made the extractable-quorum-signature
     programme plausible at all.
  2. Domain `04-operator-ledger` — source tag `S1`; the origin of the constants `(20ℓ+60)Q³` and
     `(72+40ℓ)Q³` in the ledger's budget-inversion lemma `L1`.
  3. Domain `05-extraction-and-signature-reductions` — the two-output joint-lift theorem
     (`domains/05-extraction-and-signature-reductions/src/joint_extractor_lift.py`).
  4. Domain `06-qpt128-security-target` — one ledger row, `dfms_extraction` in
     `domains/06-qpt128-security-target/src/qpt128_finalization.py`.
  5. Domain `08-hidden-signers` — the binding/extraction row only, with the multi-round loss omitted.
- **Notes: the three coefficient variants are one source.**

  | Variant | Where it appears | Status |
  |---|---|---|
  | `(20ℓ+60)Q³` | the v1.35 joint-extractor line | superseded, kept as history |
  | `(22ℓ+60)q³` | the finalization script and the v1.43 ledger rows | current |
  | `(72+40ℓ)Q³` | the operator ledger's budget-inversion lemma `L1`, "constants supplied workspace report v1.32" | constants not in the tree — **incomplete in source** |

  A reader meeting two of these numbers in two domains must not read them as two sources. The
  repository states which variant each consumer uses; see
  `domains/05-extraction-and-signature-reductions/src/joint_extractor_lift.py` and
  `domains/06-qpt128-security-target/docs/qpt128-finalization.md` for the reconciliation note.

### D5-03 (detail) — what D5 adds to the borrowed statement

- **Statement as used here (project part).** `p_E ≥ max(0, p − κ_J)` with
  `κ_J = min(1, 2(v₀+v₁)/2^h + G(Q))` and `L_J = 1`; the ordinary commit-and-open bound
  `G(Q) ≤ [2eQ^{3/2}2^{−h/2} + Q√(10·max(Qℓ2^{−h}, p_triv))]²`.
- **Label.** `[T]` theorem-with-proof under premises P1–P4.
- **Borrow.** Partial, as above.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/joint_extractor_lift.py`
  (lines 95–138, 156, 214–220 of the working file).
- **Notes.** D5's own validation line is: "proven — Lemmas 1–3 for this backend; measured — finite
  tests; not established". What is missing for a standard proof is named in the same source: any
  concrete protocol satisfying premise P4 for the relation, a quantum simulator, and the
  compressed-oracle lemmas.

### D4 `S8` — Zalka, "Grover's quantum searching algorithm is optimal"

- **Statement as used here.** The search-specific optimality of Grover's iteration count, used **only**
  for the search-model interpretation of the ledger's work/depth lemma `L7`.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Christof Zalka; "Grover's quantum searching algorithm is
  optimal"; quant-ph/9711070. Complete in source (the ledger's scope sentence: "Search-specific
  resource reasoning; not a blanket hardness theorem for all quantum attacks"). Standard identity
  added: Physical Review A 60, 2746 (1999).
- **Borrow.** Partial — the search-model reading only.
- **Where used.** `domains/04-operator-ledger/docs/operator-ledger.md` (source list and lemma `L7`).

---

## 2. The concrete backend: ZKBoo and its parameterisation

### D5-04 — ZKBoo (USENIX Security 2016), §4.1, Proposition 4.2, Appendix A

- **Statement as used here.** Three passing directions force a witness (the extraction lemma); the
  decoder is `S`-sound* (the soundness notion); and `p_triv = (3/4)^r` with the extremal challenge set
  `{0,2,3}^r`.
- **Role.** The concrete commit-and-open backend that satisfies DFMS's premises — the only concrete
  backend in the programme.
- **Label.** `[T]` theorems-with-proof **for this backend**.
- **Citation as the source gives it.** "ZKBoo, USENIX Security 2016, §4.1, Prop. 4.2, App. A" as
  given; standard identity added: ZKBoo, USENIX Security 2016.
- **Borrow.** **Partial** — the share-of-witness definition and the `S`-sound* notion, plus the
  ordinary commit-and-open bound. What is not taken is the rest of the protocol's analysis.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/circuit_witness_extractor.py`.
- **Notes.** Everything else the programme says about extraction is conditional on a backend that
  satisfies DFMS's premises; this is the one that is concrete, and it is concrete only at the
  parameterisation below.

### D6-08 — ZKBoo-4 parameters

- **Statement as used here.** `ℓ = 4r` computed wires, `p_triv = (3/4)^r`, `v = 2(1+3r)`, `2r` challenge
  bits — the parameterisation fed into the ledger's extraction row.
- **Label.** Project lemma (derived from the D5 backend entry).
- **Citation as the source gives it.** Project (from the ZKBoo backend).
- **Borrow.** Full as a derivation.
- **Where used.** `domains/06-qpt128-security-target/src/qpt128_finalization.py`
  (`zkboo4_parameters`).

### D0-09 — Compressed-oracle lemma (Isabelle AFP)

- **Statement as used here.** `min(1, 12(Q+154)³/2^h)` for a uniformly random function with `h`-bit
  output.
- **Role.** Comparison for the QROM extraction term — a sanity figure for what an ideal oracle gives.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** "The published quantum collision bound" with a pointer to a
  formalization (Isabelle AFP) — **incomplete in source**: the record names no author, no venue, no
  year, and the constant `12(Q+154)³` is unsourced at the point of use. **Do not fill this in.**
- **Borrow.** Partial.
- **Where used.** `docs/01-research-journey/pqt.md` (the component result and the conditional
  quorum-safety bound that quotes it). The same constant reappears inside the operator ledger's `L1`
  constant `B₀ = ((72+40ℓ)Q³+2v)/2^h`.
- **Notes.** The source is explicit that this "establishes an ideal-oracle component result, not a
  theorem about the complete implementation".

### D2a-05 — Merkle local opening

- **Statement as used here.** A standard Merkle-tree local opening, used as the local-opening primitive
  in the v0.8 aggregate-signature route.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** Elementary; no citation in source.
- **Borrow.** Full.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (the v0.8 route document).

---

## 3. Entropy: leftover hashing against quantum side information

### D4 `S4` — Tomamichel–Schaffner–Smith–Renner, Theorem 6

- **Statement as used here.** Leftover hashing against quantum side information, applied to
  independently seeded two-universal hashing.
- **Role.** The entropy step of the extraction chain.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Tomamichel, Schaffner, Smith, Renner; "Leftover Hashing Against
  Quantum Side Information"; Theorem 6; arXiv 1002.2436. Complete in source. Standard identity added:
  IEEE Transactions on Information Theory 57(8), 2011.
- **Borrow.** **Partial with a stated caveat.** The source's scope sentence is: "Applies to
  independently seeded two-universal hashing … the exact distance convention and smoothing parameters
  must match an application." The operator ledger states plainly that "the uniformity of seeded module
  matrices is **not** established". **Every restatement of the entropy argument in this repository must
  repeat that caveat.**
- **Where used.** `domains/04-operator-ledger/docs/operator-ledger.md` (source list; lemma `L6`).

---

## 4. Ideal permutations and the fixed-hash gap

### D4 `S3` — Cojocaru–Hhan–Liu–Yamakawa–Yun, Corollary 6.9

- **Statement as used here.** Ideal-permutation bounds covering sponge collision behaviour for
  invertible permutations and ideal ciphers.
- **Role.** Used inside the operator ledger's `L8` (minimax inequality and the fixed-hash
  distinguisher) to expose the ideal-permutation gap.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Cojocaru, Hhan, Liu, Yamakawa, Yun; "Quantum Lifting for
  Invertible Permutations and Ideal Ciphers"; Corollary 6.9 and the model definitions; arXiv 2504.18188;
  2025. Complete (arXiv); the venue is **not** added because it is not certain.
- **Borrow.** **Partial, with a hard limitation the source states**: the result "applies only to
  uniformly random permutations" and "does not certify the fixed deployed permutation". The fixed-hash
  distinguisher gap `1 − 2^-h` is what the ledger exposes rather than closes.
- **Where used.** `domains/04-operator-ledger/docs/operator-ledger.md` (source list; lemma `L8`).

### D4 `S1` (source tag) and `S2`, `S5`, `S6`, `S7` — the other operator-ledger source tags

The operator ledger defines eight source tags at the point where it introduces its lemmas. Each is
catalogued where its content belongs: `S1` (DFMS) here; `S2` (Barbosa et al., Fiat–Shamir with aborts)
in `signature-security-reductions.md`; `S3` and `S4` here; `S5` (Keccak specifications summary) in
`algebraic-and-coding-tools.md`; `S6` (FIPS 204) in `signature-security-reductions.md`; `S7` (Watrous,
Chapter 2, Kraus and positive-map conventions) in `project-statements-and-amendments.md` with the
ledger's contraction lemmas `L2` and `L3`; `S8` (Zalka) above.

A known hazard is recorded with them: the ledger carries a source-tag/operator-ID collision at two
line positions (`[S7]`/`[S9]`), listed in `gaps-and-unknowns.md` as an open reader flag. The collision
must be resolved before anything citing `S7` is published.
