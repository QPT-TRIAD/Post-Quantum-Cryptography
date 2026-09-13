# Theory used in this domain, and how much of it

The rule for this page is the repository's rule: for each result, state it **as this domain uses it**
— not in its textbook form — say what it justifies, say whether the whole result or only a part is
borrowed, say what part is *not* used and why the borrowed part is enough, and give the citation as
the source gives it. Where the source's citation is incomplete, this page says so and does not fill in
a reference that could not be verified.

The identifiers in the first column (`D3-01` … `D3-21`) are the domain's theory inventory. The
"source" column points at where in this repository the use is recorded.

Two conventions used throughout:

- **`[T]`** denotes a theorem, **`[A]`** an assumption, **`[C]`** a construction argument (not a
  theorem), **`[M]`** a measurement, following the programme's own labelling.
- "Full" means the domain uses the result in the form it is stated. "Partial" means a specific,
  narrower instance is used, and the page names the part left out.

---

## A. Standards and primitive specifications

| ID | Result | Statement as used here | Role | Full or partial | Citation as the source gives it |
|---|---|---|---|---|---|
| D3-01 | FIPS 203 (ML-KEM) | Key establishment with the algorithms and parameter sets of the standard, including implicit rejection; ML-KEM-1024 chosen as the category-5 parameter set | primitive choice and channel in the v1.29 authorization component | **partial** — used as a component and a constraint, explicitly "not as theorems about CE-QS" (`docs/package-assessment.md` §1) | FIPS 203, final 2024, sections 3, 6–8 — complete in the source; [S1] of `docs/package-assessment.md` |
| D3-02 | FIPS 204 (ML-DSA) | Signature generation and verification with ML-DSA-87, pure external API with empty external context | approval signature in v1.29, verified by `authorization.py:check_witness` | **partial** — algorithms and sizes checked; the source states it "is not a full errata/conformance audit" and the pending errata page is noted | FIPS 204, final 2024, sections 4–6 — complete in the source; [S2] |
| D3-03 | NIST SP 800-227 | The separation between key establishment and authentication, and the KDF/KEM-DEM structure of a channel | composition rule for the v1.29 transport | **partial** — used as a composition rule; the source states the channel is "a custom experimental composition, not a claim of implementing a named standard channel protocol", and makes no SP 800-227 conformance claim | SP 800-227, final September 2025, sections 4 and 5.2 — complete in the source; [S3] |
| D3-06 | FIPS 202 (SHAKE256) | Rate 1,088 bits / 136 bytes, capacity 512 bits, permille-level use of the 1,600-bit Keccak permutation, variable output length | counting Keccak permutations per seat, so that the circuit size is accountable | **partial** — only single-block and two-block fixed-length instances are used, and only the sponge-rate fact is used to count permutations | FIPS 202, sections 5.2 and 6.2 (linked in `history/v1.27b/assessment.md` §3) — the standard is added by the project; the source used the fact, not a theorem of the standard |
| D3-19 | HKDF (RFC 5869), AES-GCM (SP 800-38D) | Key derivation from a KEM secret and authenticated encryption of an approval, with header and KEM ciphertext bound into the derivation and associated data | transport composition in v1.29 | **partial** — the source states explicitly that no forward secrecy, secure-erasure, quantum-UC or SP 800-227 conformance claim is made | standard (added) — the v1.29 source names the constructions but does not carry an RFC/sp locator for them |

## B. Backend theory

| ID | Result | Statement as used here | Role | Full or partial | Citation as the source gives it |
|---|---|---|---|---|---|
| D3-04 | Aurora (EUROCRYPT 2019) | Transparent succinct arguments for R1CS: encode the whole predicate as one proof statement; use polynomial structure rather than transmitting the witness | candidate for the missing `pi_R29` in v1.29 | **partial** — abstract, Theorem 1.2 and the implementation section were inspected; the source states the paper's example proofs and plausibly-post-quantum claim "do not instantiate this 27,056-byte proof position or its QPT-128 reduction" | [S4] Ben-Sasson et al., ePrint 2018/828, EUROCRYPT 2019 |
| D3-09 | Binius product-tree / prodcheck | The layer identity `T_{k-1}(j) = T_k(j)·T_k(j+2^{k-1})` lets a prover generate one tree layer at a time, in the original order, and call the same native `bivariate_product_mle::new_split_half` and `prove_single_mlecheck` | the v1.17 prover-memory construction, carried into every later adapter | **partial** — the algebraic identity of the layers only. The source labels the whole result `[C]`: "a construction argument for an equivalent prover, supported by differential tests and native verification. It is not a machine-checked equivalence theorem" | upstream Binius, vendored at a pinned commit; `docs/method.md` states that no machine-checked equivalence is claimed |
| D3-14 | BaseFold / FRI opening structure | The verifier's final-layer check is a linear fold `y = Σ w_j v_j`; terminal polynomial coefficients are already fully present in QVT1; Merkle frontiers are what the boundary-hash bytes are | the redundancy that QVT2 and QVT3 exploit, and the accounting of what remains | **partial** — soundness is inherited from the native verifier call, not re-derived. Complete for Diamond–Posen ePrint 2024/504; the source states the citation is incomplete for WHIR, Khatam, BaseFold in the list-decoding regime and HyperFond | Diamond–Posen ePrint 2024/504, as implemented upstream |
| D3-15 | Linearised FRI fold, uniqueness of the interpolating polynomial, additive NTT over the Gao–Mateer basis | A degree-below-512 polynomial through 512 distinct points is unique, so the 512 coefficients determine the whole 4,096-element final oracle; the actual evaluation coordinates come from an NTT of a degree-one basis vector, not from array indices | correctness of the QVT2/QVT3 codecs | **full** for the fold and interpolation facts, **partial** for the NTT — the NTT correctness is not proved here but checked by full-transcript equality | elementary / standard; the source cites none for the fold and interpolation, and calls the NTT a backend part checked by exact replay |
| D3-17 | SHAKE256 as a PRG | Seed expansion generates the demonstration tapes | the seeded-data carrier | **partial**, labelled `[A]` — the source states that the finite check "is not a proof of computational hiding" | none — the source claims no citation |
| D3-21 | Backend scope facts | `SECURITY_BITS = 96`; no quantum argument-of-knowledge or QROM extraction theorem for Spartan + BaseFold/FRI; FRI soundness charges only the query phase; the constraint system is not absorbed into the Fiat–Shamir transcript | the reason no carrier in this domain can be called QPT-128 | n/a — this is a stated negative, recorded as a limitation rather than a borrowed result | project records: `continuation_v1.27b/assessment.md` §6, and the programme's own finalization document quoted in the theory index |

## C. Construction algebra

| ID | Result | Statement as used here | Role | Full or partial | Citation as the source gives it |
|---|---|---|---|---|---|
| D3-07 | Rabin irreducibility criterion | `f(X) = X^512 + X^8 + X^5 + X^2 + 1` is irreducible over F₂, certified by `X^(2^512) = X mod f`, `gcd(X^(2^256) − X, f) = 1`, and 2 the only prime divisor of 512 | the field GF(2^512) in which every mask, identity and extraction equation in this domain lives | **full** for this single polynomial | the source's citation is **incomplete** — it cites v1.23's field checks; the standard identity (Rabin, *SIAM J. Comput.* 9(2), 1980) is added by the project, and `src/audit_results.py` re-derives the certificate |
| D3-08 | Inclusion–exclusion counting bound | `|S₀ ∩ S₁| ≥ |S₀| + |S₁| − N`, hence `43 + 43 − 64 = 22` common seats | the only reason conflict extraction returns anything at all | **full** — elementary; nothing is lost | none needed |
| D3-10 | MSB-select lookup tree; bitwise occupancy | Lemma 1: selector wires `s_k = i << (63−k)` make six levels of `select(s,t,f)` read exactly the bits of `i`. Lemma 2: with `E_j = 1 << i_j`, `O_j & E_j = 0` and `O_{j+1} = O_j ⊕ E_j` enforces distinctness, because a repeated seat fails the AND-zero test before XOR could cancel it | circuit correctness for shared seat selection and for 43 distinct seats | **full** at the implementation-semantics level: the source states it assumes the documented native gate semantics and the correctness of the Keccak gadget | project — these are the experiment's own lemmas, proved in `history/v1.25/assessment.md` §3 |
| D3-11 | Keccak wiring lemma | The 16-byte label aligns the private seed at word offset 2 or 4; an 80-byte and a 64-byte registration input each need one SHAKE rate block; a 128-byte paired input fits in one block; the 224-byte two-block tracing input of v1.25 needs two. Hence 3 permutations per seat in v1.27b, 4 in v1.27, 7 in v1.25 | cost accounting and the circuit-size differences between versions | **partial**, labelled `[A]` + `[M]` — the source says it "assumes correct implementation of the pinned Keccak and word-gate library" and calls the result implementation evidence, not a machine-checked proof | pinned upstream; the wire-level claims were checked against the local pinned source |
| D3-12 | Predicate equivalence | An accepted canonical body has a satisfying circuit witness **iff** it has a witness for the stated relation, conditional on gate semantics and the Keccak gadget | binding each relation to the circuit that is actually proved | **full**, conditional on gate semantics; the source adds that this is "an implementation-level argument plus independent execution checks, not a machine-checked compiler proof" | project — Proposition in `history/v1.25/assessment.md` §3 and Circuit lemma in `history/v1.27b/assessment.md` §4 |
| D3-13 | Conditional conflict-extraction theorem | Under the *consistent-opening event* (repeated seats use the same link and mask credentials; distinct seats have distinct links in the fixed context), public extraction from two accepted bodies with the same `C,d` and different messages returns exactly their common witness seats, at least 22, via `i + 1 = (Z_i + Z'_i)·(c(m) + c(m'))⁻¹` | the accountability claim of every carrier here | **full as a conditional statement**; the condition itself "is computationally motivated, not mathematically guaranteed by a finite hash", and the adaptive joint argument-of-knowledge theorem that would make it unconditional is **open** in every version | project — proved in `history/v1.25/assessment.md` §4 and `history/v1.27b/assessment.md` §4; the source states the open obligation plainly |
| D3-18 | Gaussian elimination over GF(2) | Binary span ranks of the serialized sections, used to show that the queried-field sections have full 128-bit span | why generic compression does not help on this data | **full** — standard linear algebra | none needed; scope field: "a linear subspace of raw serialized blocks only" |

## D. Distributed and generative structure

| ID | Result | Statement as used here | Role | Full or partial | Citation as the source gives it |
|---|---|---|---|---|---|
| D3-16 | GGM-style puncturable seed tree | A canonical frontier of ten 48-byte seeds determines 1,023 leaf seeds while the excluded leaf stays absent from the decoder's output | the seeded-data demonstration only | **partial** — the source cites FAEST v2 as precedent and states the citation is incomplete; the structure is used as a demonstration, not as a component of any certificate | FAEST v2, sections 2 and 5 (linked in `history/v1.28/assessment.md` §2) |
| D3-20 | Honest-majority BGL-style `n > 3t` | `64 > 3·21` identifies a possible operating regime for a distributed prover; a 43-party substitution would not carry the same guarantee | the distributed-generation target | **partial** — used as a model constraint only; the source states that it "does not implement active-secure multiplication, private selection of 43 inputs, biased-abort handling, or a quantum-secure realization" | the source's citation is incomplete; the standard identity (Ben-Or–Goldwasser–Wigderson, STOC 1988) is added by the project |
| D3-05 | Candidate survey: AIM (CCS 2023), HAETAE (CHES 2024), Han et al. (IACR CiC 3(2) 2026), Quorus (USENIX Security 2026), Doerner–Kondi–Rosenbloom (CRYPTO 2024) | One row per source, each with the component it could supply and the limit that stops it transferring | eligibility judgments for v1.29 | **partial by construction** — abstracts and affiliations only; the source states that for two of them "PDF retrieval was unavailable, so no uninspected theorem or parameter table is credited" | [S5]–[S9] of `docs/package-assessment.md`, each with its ePrint/venue locator; regional attribution follows verified affiliations, not venue |

## E. What is deliberately *not* used

Three declarations matter as much as the borrowings, because a reader will otherwise assume more than
was done:

1. **No theorem from any surveyed paper is applied to a parameter or a query count.** The v1.28
   report records that WHIR, Khatam and BaseFold-in-the-list-decoding-regime are relevant to a
   justified query schedule, and that "no query was removed on the strength of an uninstantiated
   theorem in this experiment". A factor reported in another setting is not multiplied into these
   frames.
2. **The compression measurements are not an entropy bound.** `results/existing-carrier-results.json`
   carries `scope: MEASUREMENTS_NOT_ENTROPY_OR_IMPOSSIBILITY_PROOF`, and the report states the
   counting argument for fixed-length decoders explicitly "does not rule out a 32 KiB CE-QS proof".
3. **The extraction theorem is not an authorization theorem.** Turning witness identities into
   *actual equivocating authorizers* needs the adaptive joint argument-of-knowledge result and the
   approval game, both listed as open. The v1.29 negative control shows why: when the synthetic
   authorizers genuinely sign an incorrect trace mask, **signature-only auditing accepts while the full
   witness predicate rejects**.
