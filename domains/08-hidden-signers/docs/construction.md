# The hidden-signer profile: constructions and theory, per mode

This document states what the two Mode A and Mode B constructions are, which parts are borrowed and
which are the project's own, and what each borrowed part is asked to carry. Every claim carries a
label: **theorem-with-proof**, **reduction-sketch**, **model-or-ledger estimate**, **measurement**,
**simulation**, **assumption**, **conjecture**. Numbers here are the numbers the executable files in
`../src/` and `../history/` produce; where a figure comes from the literature instead, the source is
named.

---

## 1. The profile, as used

The task these constructions attack is fixed by the programme's QPT-128 target (domain 06,
`qpt128-security-target`):

| Condition | Statement |
|---|---|
| **D1** | every algorithm that evaluates the primitives uses ≥ 2^18 gates per hash or key-map evaluation |
| **D2** | a quantum adversary with a gate budget G has success probability ≤ 1/3 below G = 2^128 gates, and ≤ G·2^−130 at G = 2^128 |

and the certificate profile itself asks for all five of:

1. **Hidden quorum.** A certificate shows that 43 of 64 seats approved (min overlap between any two
   43-subsets: 22), without revealing which 43.
2. **Public verification**, no per-signer secret at verification time.
3. **≤ 32,768 bytes** on the wire, including a proof slot.
4. **Public, keyless tracing**: two certificates for the same (epoch, domain) with different messages
   must let *any* observer name the seats that signed both — using published data only.
5. **Category-5 post-quantum security** under D1/D2.

Requirement 4 is what makes the problem hard, and it is the one that reshapes the witness. Because
the identifying evidence has to be extractable *from the certificate bytes by anyone*, the opening
that identifies a seat must appear, transformed, in the certificate. That is why both modes spend
their design effort on a **handle** — a per-seat algebraic image of the opening, keyed by the
message — rather than on hiding the signer set inside a proof.

What the profile explicitly does not require, and what the constructions therefore do not claim: that
the proof be produced without a trusted party (it is not, see
[the collaborative-prover problem](collaborative-prover.md)), that any part of it be deployed, or
that it be a proof of the same things B0 proves.

---

## 2. Mode A (v1.45) — the linear handle, and why it is refuted as a security choice

### 2.1 Construction

- **Field.** F = GF(2)[X]/(X³³⁶ + X⁷ + X⁴ + X + 1); a handle is 42 bytes.
- **Registry.** Per epoch and domain d, seat i draws a one-time opening (s, r), s ∈ F₂^224,
  r ∈ F, and registers Y[d][i] = K(D_A, s, r), where D_A = H("CQ45/A/K", epoch, d) and K is a
  SHAKE256-based key map.
- **Handle.** c(m) = SHAKE256("CQ45/A/c" ‖ cfg ‖ d ‖ m) as a 336-bit field element, and

      Z = r ⊕ c(m)·s   (42 B).

- **Certificate.** header 208 B ‖ 43 strictly increasing handles (1,806 B) ‖ proof ≤ 30,754 B.
- **Relation R_A.** Rows (i_j, s_j, r_j) with distinct i_j, s_j < 2^224, K(D_A, s_j, r_j) = Y[d][i_j]
  and Z_j = r_j ⊕ c(m)·s_j. The handle equation is linear, and free; selecting a registry key is
  linear in the one-hot selector.
- **Extraction.** For two accepted certificates with equal (cfg, d) and m₀ ≠ m₁, set δ = c₀ ⊕ c₁ and,
  for each of the 43×43 = 1,849 handle pairs, s′ = (Z₀_j ⊕ Z₁_k)/δ, r′ = Z₀_j ⊕ c₀·s′; keep s′ < 2^224
  and look K(D_A, s′, r′) up among the domain's 64 keys. A hit names the seat, and (s′, r′, j, k) is
  public evidence checked by `verify_blame`.

### 2.2 The negative result that killed it

The handle is **linear in the opening**: for fixed δ, s′ = (Z₀ ⊕ Z₁)/δ is an explicit function of the
two published handles. Nothing is hidden behind it that a solver has to find — the algebraic attack
therefore costs what the keyed hash costs, and the v1.45 round's own tests put the algebraic attack
at **≈123.3 bits**, i.e. *below* the generic Grover bound of 251 bits for the same 256-bit secret with
43×64 targets.

**Label: measurement / analysis (negative result).** The finding is preserved rather than deleted: it
is why the second design uses a power map. Mode A is kept in the repository as the refuted candidate
that fixes the requirement the next design must meet (a key map with ≤ ~600 witness bits that is
one-way on 224-bit openings, collision-resistant at ≥ 313 bits, and hiding under the handle
leakage) — a requirement the executable sizing table in `../src/hidden_signer_mode_a.py --report`
makes numeric, and which no published primitive meets.

### 2.3 What is borrowed

| Borrowed part | Source | What it carries here | Status |
|---|---|---|---|
| Traceable-ring handle algebra | Fujisaki–Suzuki traceable ring signatures; v1.24 contract | the "reveal on double-signing" shape | **borrowed**, partial — the project supplies the hidden-quorum instantiation |
| Key map as a one-way function with a public registry | v1.44 §3.3 | the registry form | project |

**Statement as used.** Mode A's security sketch names assumptions and is explicitly **not a
theorem** — the source file says so in its own §2. Nothing in Mode A is a proof.

---

## 3. Mode B (v1.46 → v1.50 → v1.51) — the power handle

### 3.1 Construction

**Parameters.** n = 256; field GF(2^256) with x^256 + x^10 + x^5 + x^2 + 1 (irreducibility checked by
the Rabin test, theory entry D8-10); key map **F: F₂^512 → F₂^812**, a random quadratic map expanded
from a 32-byte seed, so every verifier regenerates it (ρ monomials per equation at production, dense
supported); **G(r) = r⁷**, a permutation of the field because 7 ∤ 2^256 − 1 — x³ would *not* be one
(3 | 2^256 − 1). Expansion E = 512 at the ledger's settings; the executable sweeps E ∈
{300, 400, 430, 512, 600}.

**Registry.** Per epoch and domain d, seat i draws a one-time opening (s, r) ∈ F₂^256 × F₂^256 and
registers Y[d][i] = F(s‖r), 102 bytes. cfg commits to the epoch, the key-map seed and every Y.

**Handle** (v1.46): c = SHAKE256("CQ46/c" ‖ cfg ‖ d ‖ m) as a nonzero field element,

    Z = r⁷ ⊕ c·s   (32 B).

**Certificate.** header 208 B ‖ 43 strictly increasing handles (1,376 B) ‖ proof ≤ 31,184 B.

**Relation R_B.** Rows (i_j, s_j, r_j) aligned with the handles, F(s_j‖r_j) = Y[d][i_j],
Z_j = r_j⁷ ⊕ c·s_j. Committed witness per seat: s, r and a one-hot selector = 576 bits; constraints
812 quadratic (key map; the selected key is linear in the one-hot bits), 256 cubic (r⁷ = r·r²·r⁴,
Frobenius factors linear), 65 one-hot. Distinct seats follow from strict ordering plus binding of F.

**Extraction.** For two accepted certificates with equal (cfg, d) and m₀ ≠ m₁, each of the 43×43
handle pairs gives s = (Z₀ ⊕ Z₁)/(c₀ ⊕ c₁) and r = (Z₀ ⊕ c₀·s)^{1/7}; F(s‖r) is looked up among the
domain's 64 keys. A hit names the seat and (s, r) with both handles is the public evidence. A
double-signer always hits; a wrong pair gives a random 812-bit value, so a spurious hit has
probability 64·2^−812 before the v1.52 false-positive correction (see
[the ledger](rigorous-ledger.md)).

### 3.2 The three revisions, and what each was fixing

| Version | Change | Why |
|---|---|---|
| v1.46 | the design above | first sizing under 32 KiB with a power handle |
| v1.50 | **linearized handle** `Z = r⁷ ⊕ L_c(s)`, `L_c(s) = c_a s ⊕ c_b s² ⊕ c_c s⁴`, with a public counter making `L_c` invertible; **report-all extraction** (never abort on the count); messages must be exactly 64 bytes | a single 256-bit challenge could collide (c(m₀) = c(m₁), ≈2^85 quantum with QRAM): extraction divided by zero and named nobody. Three colliding coefficients (768 bits) are now needed, and `s = L_c⁻¹(Z ⊕ r⁷)` is still degree 3 inside the circuit, so the key-map constraints stay degree 6. Report-all closes a denial path in which one seat with two openings of its key hid the other double-signers behind a "< 22" abort |
| v1.51 | **F1 leak fix**: `verify()` returned on the grinding-condition check without freeing the `circ_pub_t *P` allocated at its top, leaking 9,568 B per rejected proof | found by the audit stack's LeakSanitizer pass (rank-3 resource finding); recorded as `records/FAILED_ASSUMPTIONS.md` F1 |

### 3.3 Theory

The security statement is `../docs/mode-b-security.md` (v1.49, copied unchanged apart from the
mandated rewrites recorded in the [README](../README.md)). Its four theorems, **as used**:

| Theorem | Statement as used | Label | Borrowed part |
|---|---|---|---|
| **1** non-frameability | `Pr[Frame(i*)] ≤ 8·p·(q+1)²/2^256`, tight: the reduction runs the adversary once and performs one public extraction | theorem-with-proof | HRS16 search bound; the tightness is the project's glue onto B0's public-evidence reduction |
| **2** safety / forensic completeness | `Pr ≤ ε_snd + ε_bind + ε_fp + Pr[Frame]`, with ≤ 21 corrupt seats | theorem-with-proof, modulo Theorem 3 | DFMS22 Theorem 4.2 for the binding row and the extraction charge |
| **3** QROM soundness of Π_B | `Pr[accept] ≤ 10(τ+1)Q³2^−512 + 10Q²·max(τ·2^−256, d_QS·2^−λ′)` | **transplant** — FAEST v2 Lemma 9.39 "not re-derived line by line for Π_B"; its Lemma 3.1 is imported from FAEST v2 Lemma 9.34/9.37 with [AHJ+23] Lemma 1 and BBD+23 Theorem 2 | yes: the entire QROM machinery |
| **4** privacy | `|Pr[β′ = β] − 1/2| ≤ ε_sim + 43·ε_P` | reduction-sketch | GHHM21 Theorem 3 |

Two further pieces of theory are the project's own: the **linearized/additive-polynomial lemma**
(§9.0 of the security document: `D(s) = αs ⊕ βs² ⊕ γs⁴` is linearized, partial collisions cannot
yield a second preimage, kernel dimension ≤ 2) — labelled theorem-with-proof (elementary) — and the
**Rabin irreducibility check** that validates the field (standard; Rabin 1980, cited as incomplete in
the source and completed here by name).

**Assumptions, as used** (from the security document §2): **A-F1** one-wayness with the handle;
**A-F2** binding of F; **A-QROM** the domain-separated SHAKE256 instances are quantum-accessible
random oracles; **A-P** decisional pseudorandomness of the handle; **A-Prove** the proof is produced
by a party that learns all 43 openings and behaves honestly; **A-Reg** registry authenticity and
one approval per seat per domain. A-Prove is **essential, not technical** — see
[the collaborative-prover problem](collaborative-prover.md). A-F1, A-F2 and A-P are non-standard and
rest on attack-based evidence (XL/hybrid and SAT), not on a reduction to a standard problem.

### 3.4 What is borrowed, and how much of it

| Borrowed part | Source | What it carries | How completely |
|---|---|---|---|
| VOLE-in-the-head, GGM seed trees, all-but-one vector commitments, VOLE consistency hash | FAEST v2 (NIST round 2; ePrint) | the whole proof structure and the QROM soundness analysis | structure and lemma numbers only — **incomplete in source** (no full bibliographic entries) |
| QuickSilver degree-3 check | QuickSilver | the consistency check, raised to degree 6 here | as cited |
| "One Tree" quadratic-map witness economy | MQOM2 / KuMQuat (ePrint 2024/490) | a quadratic key map needs no intermediate witness: 2n + 64 witness bits per seat | as cited |
| Extraction charge for the binding row | DFMS22 Theorem 4.2 (arXiv 2202.13730) | R2, and the DFMS model of R3 | binding row only |
| Power S-boxes as permutations | Gold, inverse functions; MiMC's x³; Rain | the idea that a low-degree power permutation of the secret blocks linear elimination | standard |
| Size formula | FAEST v2 | the certificate-size arithmetic — it reproduces FAEST-256s/f and FAEST-EM-256s/f to the byte | as cited |

**Statement as used.** Mode B is a tested design with a size estimate and an attack-based ledger. It
has **no zero-knowledge backend of its own, no security theorem that is not a transplant, no
collaborative prover, and no dedicated cryptanalysis** beyond the attack families tested. The
estimates use the standard XL/hybrid model under the **semi-regularity heuristic** — explicitly
"heuristic, not a theorem" in the source. See [validation status](validation-status.md).

---

## 4. Cross-references

- The rigorous ledger and where its constants come from: [rigorous-ledger.md](rigorous-ledger.md).
- The toy prover and what it does and does not establish: [toy-field.md](toy-field.md).
- The C prover and its sanitizer runs: [prover-and-sanitizers.md](prover-and-sanitizers.md).
- What is missing for a standard proof: [validation-status.md](validation-status.md).
