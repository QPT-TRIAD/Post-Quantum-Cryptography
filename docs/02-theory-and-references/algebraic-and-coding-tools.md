# Algebraic and coding-theoretic tools

This document holds the small mathematical machinery the constructions rest on: the finite fields and
their irreducibility certificates, the linearized-polynomial kernel lemma of the handle algebra, the
rank and entropy facts, the hash wiring, and the algebraic and MPC primitives used inside the
constructions.

Most entries here are elementary. That is the point: they are the places where a construction's
correctness is decided, and several of them are *elementary in a way that a plausible-looking
alternative is not*. One of them — the kernel lemma — is the object of two recorded corrections
(`Q3`, `Q4`) and one recorded counterfactual refutation (`A22`), and is catalogued once, below, with
its four guises tabulated.

---

## 1. Fields and irreducibility

### D3-07 / D5-01 / D8-10 — Rabin's irreducibility criterion (one criterion, three domains)

- **Statement as used here.** Rabin's criterion applied to the field polynomial, with the recorded
  certificate for `f = X^512 + X^8 + X^5 + X^2 + 1`: `tail 293`, `frobenius_512_equals_x`,
  `gcd_x_2pow256_minus_x = 1`, `irreducible: true`.
- **Role.** The GF(2^512) field validity on which the adapters, the v1.34 decoder's Claim 1, and the
  Mode-B field construction all rest.
- **Label.** `[T]` computational (D3)/`[T]` theorem-with-proof (D5's Claim 1, `[T]` in D8).
- **Citation as the source gives it.**
  - **D5** gives it as: Greenhill, "Theoretical and experimental comparison of efficiency of finite
    field extensions", **§2 Lemma 1**, with a URL at the point of use — **incomplete in source (no
    venue, no year)**.
  - **D3** and **D8** record the criterion itself as **incomplete in source**.
  - **Standard (added):** Rabin, SIAM Journal on Computing 9(2), 1980.
- **Borrow.** Full for the single polynomial. The criterion is applied to one modulus, not to a family.
- **Where used.** `domains/03-zk-carrier-experiments/` (the executed field certificate),
  `domains/05-extraction-and-signature-reductions/src/ceqs29_extractor_v1.34.py` (Claim 1),
  `domains/08-hidden-signers/` (the Mode B field).
- **Notes.** The audit stack additionally uses a **different** modulus for GF(2^256):
  `x^256 + x^10 + x^5 + x^2 + 1`. That run records the modulus's irreducibility as **not checked**
  (it compares two implementations on 400 random inputs instead), so the GF(2^256) modulus's
  irreducibility is an unevidenced step in the audit stack and this package says so rather than
  filling it in.

### D5-02 — GF(2) linear-algebra identity of the decoder

- **Statement as used here.** `T[Z0 XOR Z1] = seat`, computed in 6 `xtime` operations and 64 XORs
  (Claim 2 of the v1.34 decoder).
- **Role.** Decoder correctness.
- **Label.** `[T]`.
- **Citation as the source gives it.** Elementary; no citation in source.
- **Borrow.** Full.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/ceqs29_extractor_v1.34.py`
  (lines 82–101).

### D3-18 — Gaussian elimination over GF(2)

- **Statement as used here.** Standard linear algebra over GF(2), used for the carrier's systems.
- **Role.** Linear algebra.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** None.
- **Borrow.** Full.
- **Where used.** `domains/03-zk-carrier-experiments/` (part 2).

---

## 2. The kernel lemma of the handle algebra

### D8-07 / D9-03 / D11-05 / D12-04 / D12-06 — the linearized-polynomial kernel lemma

- **Statement as used here.** `D(s) = αs ⊕ βs² ⊕ γs⁴` is a **linearized** (additive) polynomial over
  GF(2^n); therefore `D` is GF(2)-linear; therefore its kernel has dimension at most 2
  (`max_free = 2`); therefore partial collisions cannot be turned into a second preimage by the route
  that was proposed. The supporting elementary fact (D12 A22) is that `s(a + b·s²) = 0` has **exactly
  two** roots in characteristic 2 — squaring is a bijection — and that the extractor solves the
  **affine** equation `D(s) = t`.
- **Role.** The handle algebra's structural lemma, and the corrector of the attack economics.
- **Label.** `[T]` theorem-with-proof (elementary); D12 labels the A22 reasoning `[R]` with the note
  "the reasoning is elementary" and that its counts are not checked (D11).
- **Citation as the source gives it.** **Standard (added):** the theory of linearized / additive
  polynomials over finite fields. The D12 entry records the criterion as elementary and gives no
  external citation.
- **Borrow.** Full.
- **Where used — the five guises of one lemma.**

  | Guise | Where | What it does there |
  |---|---|---|
  | D8-07 | `domains/08-hidden-signers/docs/mode-b-security.md:188-192` | the §9.0 structural lemma of the power handle |
  | D9-03 | `domains/09-security-games-and-attack-lab/` | the search-space bound, with the measured fibre statistics below |
  | D11-05 | `domains/11-independent-audit-stack/` (claim C4) | the added standard algebra of the audit stack |
  | D12-04 | `records/failed-assumptions.md` | invoked by `Q3`, `Q4` and `A22`–`A26` |
  | D12-06 | `records/failed-assumptions.md` (A22) | the characteristic-2 affine-point reasoning that refutes a counterfactual |

- **Notes.**
  - The **measured** companion, from the attack lab: the fibres of `D` were observed to be `{0,1,3}` in
    **9,756 of 20,000** cases and were **never a coset**, while a linearized `D` always gives `2^d`
    elements — the measurement is `[M]` and the lemma is what explains it.
  - The two corrections that touch this lemma are the register's `Q3` (a 768-bit **collision** cost,
    2^252 in the quantum model, after three preimages had been counted instead of one collision) and
    `Q4`. Both are catalogued in `project-statements-and-amendments.md`; neither changes the lemma, and
    neither is re-derived here.

---

## 3. Counting, concentration and rank facts

### D2b-16 — Hypergeometric distribution

- **Statement as used here.** The small-sample probability used in the parameter audit.
- **Role.** Audit arithmetic.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** Elementary.
- **Borrow.** Full.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.19, line 287).

### Rank census and entropy monotonicity (operator-ledger lemma `L6`)

The ledger's `L6` proves the finite-field rank census
`N_{m,n,r}(q) = ∏(q^m−q^i)(q^n−q^i)/(q^r−q^i)` and the min-entropy monotonicity
`H_min(f(X)|E) ≤ H_min(X|E)`, and pairs them with the leftover-hash theorem. The lemma is catalogued
in full with the other ledger lemmas in `project-statements-and-amendments.md`; its borrowed half —
the leftover-hash theorem — is catalogued in `commitment-and-opening.md`, with the ledger's own
caveat that **the uniformity of seeded module matrices is not established** (ledger line 238).

---

## 4. Hash structure and wiring

### D4 `S5` (source tag) — Keccak specifications summary

- **Statement as used here.** The standard-instance table: "SHAKE256 has rate 1088 and capacity 512
  bits with variable output length; **output width is not capacity**".
- **Role.** The sponge fact behind the ledger's permutation counting.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** Keccak designers, "Keccak specifications summary", the
  standard-instance table, keccak.team — **incomplete in source (a web page, no date)**. **Standard
  (added):** the normative specification is NIST FIPS 202 (2015) — **and the ledger does not cite it**.
- **Borrow.** Partial.
- **Where used.** `domains/04-operator-ledger/docs/operator-ledger.md` (source list).
- **Notes.** A reader who wants the normative statement should use FIPS 202, which is catalogued as
  `D3-06` in `signature-security-reductions.md`. The ledger relying on a web-page summary rather than
  the standard is recorded here, not smoothed over.

### D3-11 — Keccak wiring lemma (cross-reference)

The wiring facts — 80 bytes of registration input is one SHAKE block, 224 bytes of tracing input is
two blocks, 7 Keccak permutations per seat — are catalogued in `hardness-assumptions.md` (`D3-11`),
where they sit with the implementation-evidence label the source gives them.

---

## 5. Algebraic and MPC primitives used inside the constructions

### D2b-13 — Poseidon2

- **Statement as used here.** An algebraically structured hash, kept in the design as **"tight"**.
- **Role.** The MPC-friendly hash of the v1.22 construction.
- **Label.** `[T]`.
- **Citation as the source gives it.** **No citation in source.** **Standard (added):**
  Grassi–Khovratovich–Schofnegger, AFRICACRYPT 2023.
- **Borrow.** Full.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.22, line 30).
- **Notes.** The "tight" assessment is the source's; the added citation is an identity, not a security
  claim.

### D2b-14 — Packed secret sharing

- **Statement as used here.** Secret sharing with a packed layout, used at the MPC layer.
- **Role.** MPC layer of the v1.22 construction.
- **Label.** `[T]`.
- **Citation as the source gives it.** **No citation in source.** **Standard (added):** Franklin–Yung,
  STOC 1992.
- **Borrow.** Full.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.22, line 75).

### D2b-08 / D3-20 — BGW honest majority, `n > 3t`

- **Statement as used here.** The `n > 3t` threshold MPC base — the classical MPC model of the
  distributed prover. One result in two domains, presented once here.
- **Role.** The classical MPC base of the distributed prover.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** **Standard (added):** Ben-Or, Goldwasser, Wigderson, STOC 1988.
  In D3 the source's own citation is **incomplete in source**.
- **Borrow.** **Partial — the threshold only.** The source states plainly that this is "not an adaptive
  QPT implementation theorem".
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.19, v1.22, v1.24),
  `domains/03-zk-carrier-experiments/` (part 2, line 274).
- **Notes.** The honest-majority premise is an availability and modelling premise, not a
  post-quantum security property; the source says so and this entry repeats it.

### D3-19 — HKDF (RFC 5869) and AES-GCM (SP 800-38D)

- **Statement as used here.** The data-channel transport primitives.
- **Role.** Transport of the carrier's channel.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** **Standard (added):** RFC 5869 (HKDF); NIST SP 800-38D
  (AES-GCM) — the source names neither.
- **Borrow.** **Partial** — and the source's scope sentence is explicit: **no forward-secrecy,
  erasure, quantum-UC or SP 800-227 conformance claim** is made.
- **Where used.** `domains/03-zk-carrier-experiments/` (part 1 item 9, part 2).

---

## 6. What is not here

The counting identity `|S0∩S1| ≥ |S0|+|S1|−N` is elementary counting, not algebra; it is catalogued
with its four guises in `quorum-and-accountability-combinatorics.md`. The Grover search law and the
collision / birthday terms are in `quantum-search-and-accounting.md`. The finite-field rank census is
part of the operator ledger's lemma set, catalogued in `project-statements-and-amendments.md`.
