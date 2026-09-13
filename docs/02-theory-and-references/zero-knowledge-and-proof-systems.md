# Zero-knowledge, proof systems and succinct backends

This document holds the proof systems the programme borrowed or screened: transparent and
collaborative SNARKs, FRI/BaseFold-style polynomial commitments, BARGs, VOLE-in-the-head provers, and
the size evidence that decides whether any of them fits a compact certificate.

Two structural facts about this group must be stated before any entry. First, the compactness target
is **open in every version of the construction**: the domain `02-ceqs-construction-evolution` status
tables record "Concrete <32-KiB outer proof: open" from v1.0 through v1.24. Second, the programme's own
backend carries `SECURITY_BITS = 96` — a *classical* soundness target, with no quantum
argument-of-knowledge theorem. Nothing in this document upgrades either fact.

---

## 1. Candidates and contrast cases

### D3-04 — Aurora (EUROCRYPT 2019)

- **Statement as used here.** Theorem 1.2 and the implementation section were inspected as a
  transparent-proof candidate for the carrier.
- **Role.** Backend candidate assessment.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Aurora, EUROCRYPT 2019, Theorem 1.2 (complete in source:
  venue and theorem number present).
- **Borrow.** Partial — the theorem and the implementation notes only.
- **Where used.** `domains/03-zk-carrier-experiments/docs/package-assessment.md`.

### D3-05 — AIM, HAETAE, Han et al., Quorus, Doerner–Kondi–Rosenbloom

- **Statement as used here.** A candidate survey: AIM (CCS 2023), HAETAE (CHES 2024), Han et al.
  (IACR CiC 3(2) 2026), Quorus (USENIX Security 2026), Doerner–Kondi–Rosenbloom (CRYPTO 2024).
- **Role.** Candidate survey; the source's rule is that **"no uninspected theorem is credited"** —
  abstracts and affiliations only.
- **Label.** `[T]`/scope per entry.
- **Citation as the source gives it.** Venues and years as above; complete enough in source.
- **Borrow.** Partial — no theorem from any of these is used.
- **Where used.** `domains/03-zk-carrier-experiments/docs/package-assessment.md`.

### D2b-17 — Ozdemir–Boneh collaborative zk-SNARKs

- **Statement as used here.** The collaborative-proving architecture (multi-party proving for a single
  statement) as the shape of the quorum prover.
- **Role.** Architecture reference.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** USENIX Security 2022, full paper §§3–5 (as given in the v1.24
  document; also cited in v1.4 and v1.18).
- **Borrow.** Partial — architecture, not a security statement.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.4, v1.18, v1.24 documents).

### D2b-18 — The 2026 collaborative CP-NIZK paper, Theorem 1

- **Statement as used here.** A "load-bearing architecture reference" for the distributed prover.
- **Role.** Architecture.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** **Incomplete in source** (no full bibliographic entry; referred
  to by the working ledger as the 2026 collaborative CP-NIZK paper).
- **Borrow.** Partial.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/source-architecture-ledger-v1.4.md`.
- **Notes.** The source records that the paper's concrete results use Groth16 and Bulletproofs and are
  therefore "not PQ evidence" for this programme. It is cited as architecture, not as security.

### D2b-04 — Jawale–Khurana

- **Statement as used here.** "Simulation-extractable, adaptive multi-theorem computational
  zero-knowledge argument for NP in the CRS model" under polynomial quantum hardness of LWE, with the
  corollary the ledger names as "Cor. 4.4".
- **Role.** Used as a **black box for both proofs** — soundness (extractability) and privacy.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** **Incomplete in source** (the authors and the corollary number
  are given; no venue, year or identifier).
- **Borrow.** Full as a black box.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/qpt-source-ledger-v1.3.md`.
- **Notes.** Because the borrow is black-box, the entry contributes nothing about the cost of the
  argument — only that such an argument exists under LWE.

### D2a-07 — seBARGs → adaptive subset-extractable monotone-policy BARGs

- **Statement as used here.** A standard-assumption route from subset-extractable BARGs to an
  adaptive monotone-policy BARG, used as an alternative backend for the v0.8 route.
- **Role.** Alternative backend route.
- **Label.** `[R]` reduction sketch.
- **Citation as the source gives it.** As cited in the v0.8 document (identifiers as given there).
- **Borrow.** Partial.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v0.8).

### D2a-02 — Chiang et al.

- **Statement as used here.** An aggregate-signature construction considered as a candidate route.
- **Role.** Candidate route.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Complete in source (DOI given).
- **Borrow.** Partial (route only).
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v0.4).

### D2a-03 — CCS 2025 anchors

- **Statement as used here.** §5.1, Figure 8, Theorem 5.9 and Lemmas B.1–B.3 of a CCS 2025 paper, used
  as anchors for the v0.5 route.
- **Role.** Route anchors.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** As given (paper referred to by venue and section/lemma numbers;
  full author list not recorded) — **incomplete in source**.
- **Borrow.** Partial.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v0.5).

### D2a-04 — Brodsky–Choudhuri–Jain–Paneth (EUROCRYPT 2024)

- **Statement as used here.** The aggregate-signature interface is used **in full, black-box** — the
  strongest external use in the v0.x line.
- **Role.** The construction licence for the v0.8 interface.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Complete in source (EUROCRYPT 2024).
- **Borrow.** Full (interface).
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v0.8).

### D2a-06 — Theorem 7.6 (aggregate signatures from vPIR + local-opening hash)

- **Statement as used here.** Quoted and marked "now verified" in the v0.9 document, as the
  construction licence for the aggregate-signature step.
- **Role.** Construction licence.
- **Label.** `[T]`.
- **Citation as the source gives it.** A project-internal citation of the source paper ("Theorem 7.6"
  of the cited paper) — the theorem number is given without the paper's identity in the v0.9 text.
- **Borrow.** Partial.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v0.9).

---

## 2. Machinery inside the prover

### D2b-12 — GKR / sumcheck

- **Statement as used here.** Linear-layer composition for the circuit being proved.
- **Role.** Circuit composition in the distributed prover.
- **Label.** `[T]`.
- **Citation as the source gives it.** **No citation in source.** Standard identity added:
  Goldwasser–Kalai–Rothblum, STOC 2008; Lund–Fortnow–Karloff–Nisan, JACM 1992.
- **Borrow.** Full.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.22).

### D3-09 — Binius product-tree / prodcheck

- **Statement as used here.** Layer-by-layer recomputation of the native product tree, with the
  identity `T_{k−1}(j) = T_k(j)·T_k(j+2^{k−1})`.
- **Role.** The equivalent-prover construction behind the adapter's differential tests.
- **Label.** `[C]` **argument**, in the source's own words: "a construction argument for an equivalent
  prover, supported by differential tests and native verification. It is **not** a machine-checked
  equivalence theorem."
- **Citation as the source gives it.** Upstream Binius (the vendored tree, pinned by commit and patch
  digest — see `tooling/`).
- **Borrow.** **Partial** — only the algebraic identity of the layers. The upstream prover's own
  security analysis is not taken.
- **Where used.** `domains/03-zk-carrier-experiments/docs/method.md`.

### D3-10 — MSB-select lookup tree; bitwise occupancy

- **Statement as used here.** Lemma 1 (selector wires `s_k = i << (63−k)`) and Lemma 2
  (`O_j & E_j = 0`, `O_{j+1} = O_j ⊕ E_j`) — the wiring of the lookup circuit.
- **Role.** Circuit correctness.
- **Label.** `[T]` at implementation-semantics level (project).
- **Citation as the source gives it.** Project; no external citation.
- **Borrow.** Full.
- **Where used.** `domains/03-zk-carrier-experiments/docs/` (the assessment document).

### D3-12 — Predicate equivalence

- **Statement as used here.** The committed predicate equals the stated predicate, **conditional on gate
  semantics**.
- **Label.** `[T]` conditional on gate semantics (project).
- **Borrow.** Full.
- **Where used.** `domains/03-zk-carrier-experiments/docs/`.

### D3-13 — Conditional conflict-extraction theorem

- **Statement as used here.** Under the consistent-opening event — repeated seats use the same link and
  mask credentials, distinct seats have distinct links — public extraction returns exactly the
  intersection of the two seat sets, at least 22 seats, via
  `i+1 = (Z_i + Z'_i)·(c(m)+c(m'))^{−1}`.
- **Role.** The accountability claim of the carrier.
- **Label.** `[T]` **conditional**; the source states that the consistent-opening condition "is
  computationally motivated, not mathematically guaranteed by a finite hash".
- **Borrow.** Full as conditional.
- **Where used.** `domains/03-zk-carrier-experiments/`.
- **Notes.** The adaptive joint argument-of-knowledge theorem for the carrier is **open**. This entry
  is not the accountability claim of the quorum protocol; that one is the quorum-intersection counting
  identity in `quorum-and-accountability-combinatorics.md`.

### D3-14 — BaseFold / FRI opening structure

- **Statement as used here.** Diamond–Posen (ePrint 2024/504) as implemented upstream; Merkle-tree
  frontier minimality; the Reed–Solomon codeword as the additive NTT of a repeated message block.
- **Role.** Redundancy recomputation in the carrier.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Complete for Diamond–Posen (ePrint 2024/504);
  **incomplete in source** for WHIR, Khatam, BaseFold list-decoding and HyperFond.
- **Borrow.** **Partial** — soundness is inherited from the native verifier call, not re-derived.
- **Where used.** `domains/03-zk-carrier-experiments/`.

### D3-15 — Linearised FRI fold; interpolating-polynomial uniqueness; additive NTT

- **Statement as used here.** The elementary facts behind `fold_chunk` and the codec: the linearised
  fold, uniqueness of the interpolating polynomial, and the additive NTT over the Gao–Mateer basis.
- **Label.** `[T]` elementary for the fold and interpolation; **partial** for the NTT (correctness
  checked by full-transcript equality rather than by a proof).
- **Citation as the source gives it.** None for the elementary facts; the NTT basis as standard.
- **Borrow.** Full (fold, interpolation); partial (NTT).
- **Where used.** `domains/03-zk-carrier-experiments/`.

### D3-16 — GGM-style puncturable seed tree

- **Statement as used here.** The seed-tree structure for the puncturable-seed argument, cited as
  precedent from FAEST v2.
- **Label.** `[T]` as precedent.
- **Citation as the source gives it.** FAEST v2, **incomplete in source** (the specification is named
  without a full bibliographic entry).
- **Borrow.** Partial.
- **Where used.** `domains/03-zk-carrier-experiments/`.

### D8-02 — QuickSilver degree-≤3 multilinear check

- **Statement as used here.** A degree bound via the "Lemma 6.3 form" `d/2^{λ'}`, used for the
  VOLE-in-the-head consistency check.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** QuickSilver — **incomplete in source** (name only; no venue, year
  or identifier).
- **Borrow.** Partial.
- **Where used.** `domains/08-hidden-signers/docs/mode-b-security.md`.

### D8-09 — The Mode B design and size sources

- **Statement as used here.** MQOM2 and KuMQuat "One Tree" (ePrint 2024/490), the Ding–Yang cubic,
  the FAEST v2 size formula, QuickSilver, DFMS22 and GHHM21, used for the minimal-perfect-hash/handle
  design and for size evidence.
- **Label.** `[L]`.
- **Citation as the source gives it.** **All incomplete in source** — names and ePrint identifiers
  only, no full bibliographic entries.
- **Borrow.** Partial.
- **Where used.** `domains/08-hidden-signers/docs/`.

---

## 3. The hidden-signer soundness statement (a transplant)

### D8-01 — FAEST v2 Lemma 9.39 and its lemma set

- **Statement as used here.** Quantum-random-oracle multi-round soundness: a bad-transcript predicate on
  the compressed-oracle database, `(τ+4)`-local witnesses, the `(Σ_{k≤Q}√(10δ(k)))²` bound, a case
  analysis in six items carried over unchanged, per-tree rather than batched openings, `ℓ̂ = 15,296 >
  2^13`, and Lemma 3.1 (RBR) with `ε₃ = d_QS·2^{−λ'}`, `λ' = τ·b + w_g`. The accompanying lemma set is
  Lemma 9.38 (which is Lemma 1 of the underlying FAEST paper), Lemmas 9.34 and 9.37, Corollary 9.35,
  the Lemma 6.3 form, and Claim 1 of Lemma 9.34.
- **Role.** The soundness of the hidden-signer prover (domain 08's Theorem 3) and the cross-domain
  citation for hidden-signer soundness in domain 11.
- **Label.** The source's own words: "**theorem stated, transplant not re-derived**" — the lemma set is
  carried over, not proved line by line for the programme's relation `Π_B`.
- **Citation as the source gives it.** FAEST v2 specification, NIST round 2, by lemma numbers only —
  **incomplete in source** (no full bibliographic entry; the programme never held the full text).
- **Borrow.** **Partial — a transplant.** What is taken is the FAEST structure and the named lemmas.
  What is not taken is any re-derivation. Domain 08's Theorem 3 inherits the transplant status and must
  be quoted with it.
- **Where used, four guises (one source).**
  1. Domain `03-zk-carrier-experiments` — cited precedent for the puncturable seed tree.
  2. Domain `07-compact-certificate-b0` — the *size-formula family* that Theorem C rules out. This is a
     different use of the same source and is **not** the soundness statement.
  3. Domain `08-hidden-signers` — the transplanted soundness bound
     (`domains/08-hidden-signers/docs/mode-b-security.md`).
  4. Domain `11-independent-audit-stack` — the hash-consistency and QROM-soundness citation; recorded
     there as **incomplete in source**.
- **Notes.** Three different uses of one source whose full text the programme never held. A reader
  checking domain 08's Theorem 3 should read it as "the cited lemma set, if it applies to this
  relation".

### Cross-reference — the Fiat–Shamir simulation term (`D5-09` / `D6-07` / `D8-05`)

Domain 08's privacy theorem (Theorem 4) uses the GHHM Fiat–Shamir simulation loss together with
`43·ε_P`. That term is a signature-reduction result, appears in three domains, and is catalogued
**once** — in `signature-security-reductions.md` §1. It is not restated here.

---

## 4. Size evidence for and against a compact backend

### D2b-19 — Backend size and feasibility evidence

- **Statement as used here.** LaZer, LaBRADOR, SmallWood, spartan-whir, Orthus, Fusion, Lazarus,
  mutable BARGs and Ishai–Su–Wu, screened as candidates for a `< 32 KiB` backend. **Every benchmark is
  cited, not reproduced.**
- **Role.** Eligibility screening.
- **Label.** `[L]`.
- **Citation as the source gives it.** Mixed: complete (ePrint identifiers) for most; **incomplete in
  source** for Fusion, Lazarus, mutable BARGs, Ishai–Su–Wu and TripleRing.
- **Borrow.** Partial.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.7–v1.9, v1.24).
- **Notes.** One of these citations was later corrected inside the record itself: Lemur's figure was
  corrected from 201.2 KB to 185.5 KB. Quoted numbers must use the corrected figure.

### D7-06 — Binius64 PCS floor

- **Statement as used here.** `≥ 109,856` bytes at 96-bit soundness, with **no QROM analysis**.
- **Role.** The load-bearing negative size evidence for "no succinct backend fits 27,056 bytes"
  (domain 07's Theorem C).
- **Label.** `[L]` — a literature value as recorded, computed from the pinned source.
- **Citation as the source gives it.** The pinned Binius64 source (workspace 0.1.0, pinned commit and
  patch digest; see `tooling/` for the pin). The 109,856-byte figure is a project computation from that
  source, not a number the upstream project publishes.
- **Borrow.** Partial.
- **Where used.** `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md`.

### D7-07 — LaBRADOR

- **Statement as used here.** Approximately 58 KB at `2^20` R1CS constraints, **and not
  zero-knowledge**.
- **Role.** Succinct-backend comparison.
- **Label.** `[L]` as recorded.
- **Citation as the source gives it.** "LaBRADOR paper" — **incomplete in source** (no venue, year or
  identifier).
- **Borrow.** Partial.
- **Where used.** `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md`.
- **Notes.** The "not zero-knowledge" qualification is part of the entry; dropping it would overstate
  the candidate.

### D7-08 — MQOM round-2 tables and two ePrint appendices

- **Statement as used here.** MQOM round-2 specification Tables 6–7; ePrint 2021/692 Figure 5 §5.2.1;
  ePrint 2022/588 Appendix B.2 — the succinct table used for the primitive assessment.
- **Role.** Backend assessment.
- **Label.** `[L]` as recorded.
- **Citation as the source gives it.** As given (specification tables and ePrint identifiers; no full
  bibliographic entries for the specification).
- **Borrow.** Partial.
- **Where used.** `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md`.

### D3-21 — Backend scope facts (a stated negative)

- **Statement as used here.** `SECURITY_BITS = 96`; there is no quantum argument-of-knowledge or QROM
  extraction theorem for the Spartan + BaseFold/FRI backend; the FRI soundness charge covers **only the
  query phase**; and the constraint system is **not** absorbed into the Fiat–Shamir transcript.
- **Role.** Why no carrier can claim QPT-128.
- **Label.** Recorded limitation (project). This is a *stated negative*, not a borrowed result.
- **Where used.** `domains/03-zk-carrier-experiments/docs/`,
  `domains/06-qpt128-security-target/docs/qpt128-finalization.md`.
- **Notes.** The concrete mechanism is in the FRI test-query count
  `ceil(SECURITY_BITS / −log2((1+ρ)/2))`, which counts query-phase soundness and nothing else. A reader
  should treat the 96-bit label as what it is: a classical query-phase target.

### Size and claim status of the `< 32 KiB` target

The domain-02 status tables say "Concrete <32-KiB outer proof: open" for every version, and domain 08's
own statement is that no proof system in the assessed families fits the 27,056-byte hidden-signer slot.
The size arithmetic that makes this precise — Theorem C, its budget formula and the corrected
inequality direction — is catalogued in `project-statements-and-amendments.md`.
