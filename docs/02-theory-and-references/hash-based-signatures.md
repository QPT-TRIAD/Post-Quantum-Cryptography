# Hash-based signatures

This document holds the hash-based signature results: the XMSS/WOTS+ security theorems and their
standards, the LMS/HSS wire format, SLH-DSA and SPHINCS+ parameters, the size formulas the programme
uses to argue for or against a route, and the implementation-level resource figures recorded on
constrained-device hardware.

Two facts govern the whole group and are repeated wherever a number from it is used. First, the
programme's **QPT-128 target is not available** from any of these schemes at their standard
parameters: the search charges in `quantum-search-and-accounting.md` apply to each of them, and the
one size argument that once claimed otherwise (the pre-fix 1,768-byte figure, `D10-11`) is recorded as
**refuted**. Second, every size quoted here is a standard's or a source's number; this package
recomputes none of them.

---

## 1. XMSS / WOTS+ security

### D10-01 — T1: XMSS and WOTS+ are EUF-CMA secure

- **Statement as used here.** "Winternitz OTS + Merkle tree: EUF-CMA from second-preimage resistance
  of the node hash" — the security basis of the firmware-signature route.
- **Role.** Firmware-signature security basis.
- **Label.** `[T]` as cited, **not re-proved**.
- **Citation as the source gives it.** Buchmann–Dahmen–Hülsing, 2011 — **incomplete in source (no
  venue)**. **Standard (added):** RFC 8391, Hülsing et al. 2018 (used as the source of T1).
- **Borrow.** Partial — borrowed as stated.
- **Where used.** `domains/10-digital-infrastructure/` (the S1 model).
- **Notes.** The standard-model character of this theorem is the reason the infrastructure route
  survives the quantum threat model at all; the search charge is separate and is in
  `quantum-search-and-accounting.md`.

### D10-02 — T2 and T3

- **Statement as used here.** The domain's second and third stated theorems, as declared in the S1
  model's docstring: protocol-level bounds built on T1.
- **Role.** Protocol-level bounds.
- **Label.** `[T]` as stated in the source.
- **Citation as the source gives it.** As given in source.
- **Borrow.** Partial.
- **Where used.** `domains/10-digital-infrastructure/` (the S1 model).

### D10-03 — BDS traversal (Buchmann–Dahmen–Schneider 2008)

- **Statement as used here.** "At most `(h−k)/2` leaf computations per signature and an `O(h²)`-bounded
  state", as in the RFC 8391 reference implementation (`bds_round` / `bds_treehash_update`).
- **Role.** Stateful signing on constrained devices.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** As given in source; the structure is recorded per RFC 8391.
- **Borrow.** Partial.
- **Where used.** `domains/10-digital-infrastructure/` (the on-card LMS configuration `n = 32, w = 8,
  h = 20`).
- **Notes.** The traversal is where the scheme's **statefulness** comes from: a reused leaf index is a
  forgery, and the domain's operational discussion turns on that, not on the reduction.

---

## 2. LMS / HSS

### D10-04 — RFC 8554 (LMS/HSS)

- **Statement as used here.** The exact wire format the audit re-implements: typecodes;
  `D_PBLC`/`D_MESG`/`D_LEAF`/`D_INTR`; `coef()`; the checksum; node numbering `r = 1 … 2^(h+1)−1`;
  Appendix A's pseudorandom key generation; the **two type fields in the signature (1,772 B)**; and
  §5.1's sentence that "these two hash functions SHOULD be the same".
- **Role.** The wire format the audit stack re-implements.
- **Label.** `[T]` as given by number.
- **Citation as the source gives it.** **Standard (added):** RFC 8554, McGrew–Curcio–Fluhrer 2019.
- **Borrow.** Full.
- **Where used.** `domains/10-digital-infrastructure/`,
  `domains/10-digital-infrastructure/src/pq_audit_s1_lms_v2.2.py`,
  `domains/11-independent-audit-stack/`.
- **Notes.** The §5.1 sentence is a **SHOULD**, not a MUST. A reader must not turn it into a
  requirement of the standard; the domain's DNS/zone-size consequences are its own.

### D10-05 — RFC 8391 (XMSS)

- **Statement as used here.** The XMSS parameter set `XMSS-SHA2_20_256` at **2,820 bytes**; §5 as the
  source of T1.
- **Role.** Size input to the infrastructure's budget; source of the security statement.
- **Label.** `[T]`.
- **Citation as the source gives it.** **Standard (added):** RFC 8391, Hülsing et al. 2018.
- **Borrow.** Full.
- **Where used.** `domains/10-digital-infrastructure/`.
- **Notes.** 2,820 bytes is the XMSS parameter set as standardised. It is *not* the SLH-DSA figure
  (29,792 bytes, below); the two are different schemes over the same underlying hash.

### D10-06 — NIST SP 800-208

- **Statement as used here.** The approved LMS/HSS and XMSS/XMSS^MT parameter sets, and the rule that
  `approved_pair()` requires the LMS `m` to equal the LM-OTS `n`.
- **Role.** The compliance gate.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** **Standard (added)**; complete in source.
- **Borrow.** Full.
- **Where used.** `domains/10-digital-infrastructure/`,
  `domains/11-independent-audit-stack/` (§4, the approved sets).

---

## 3. SLH-DSA / SPHINCS+ and FIPS 205

### D5-06 — FIPS 205 (SLH-DSA) parameters

- **Statement as used here.** `SLH-DSA-SHAKE-256s`: `n = 32 B`, `h = 64`, `d = 8`, `h′ = 8`, `a = 14`,
  `k = 22`, `log₂w = 4`, `m = 47`; at most `2^64` messages per key; public key 64 bytes; signature
  **29,792 bytes**; NIST category 5.
- **Role.** The hash-based replacement signature, and the concrete size the extraction domain measures
  its slot against.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** "FIPS 205 Table 2 as given"; **standard (added)** — the values
  are the standard's.
- **Borrow.** Partial (sizes and parameters).
- **Where used.** `domains/05-extraction-and-signature-reductions/src/slh_dsa_signature_reduction_v1.38.py`,
  `domains/05-extraction-and-signature-reductions/src/slh_tree_conditioning_audit_v1.42.py`.
- **Notes.** 29,792 bytes is more than the 27,056-byte hidden-signer slot — that is the point of the
  entry. It must not be quoted against a larger slot.

### D5-15 — FIPS 204 interface facts

- **Statement as used here.** The pure vs HashML-DSA interface split.
- **Role.** Interface conformance of the approval signature.
- **Label.** `[T]` standard.
- **Citation as the source gives it.** **Standard (added)**. (The domain-level FIPS 204 entry is
  `D3-02`, catalogued with its errata note in `signature-security-reductions.md`.)
- **Borrow.** Partial — the interface split only.
- **Where used.** `domains/05-extraction-and-signature-reductions/` (theory line 421; lines 335–341).
- **Notes.** The programme's use of one mode rather than the other is a design choice inside the
  standard's interface and is recorded as such; it is not a security claim about the modes.

---

## 4. Search charges and size formulas

### D5-07 / D6-04 / D8-04 — HRS16, Theorem 1

- **Statement as used here.** The quantum search charge `8·p·(q+1)²/2^n` with `λ = p/2^n` — one result
  in three domains, presented **once** here.
- **Role.** The search term of the composed budget for hash-based signature routes, and the
  SPHINCS+/SLH-DSA branch term.
- **Label.** `[T]` cited theorem (quantum random-oracle model).
- **Citation as the source gives it.** Hülsing–Rijneveld–Song, **ePrint 2015/1256**, Theorem 1.
  Complete (the ePrint identifier is given).
- **Borrow.** **Partial — one row / one term of the bound.** The part used is the multi-target search
  term. The part not used is the theorem's full accounting. It suffices because the composed budget
  needs exactly the search charge on the hash-based route.
- **Where used.** `domains/05-extraction-and-signature-reductions/` (v1.38),
  `domains/06-qpt128-security-target/src/qpt128_finalization.py` (the `hrs16_search` row),
  `domains/08-hidden-signers/` (`d2_attack_cost_row_log2`),
  `domains/10-digital-infrastructure/` (the gate-unit comparison against deployed XMSS/LMS).
- **Notes.** Domain 08's Theorem 1 reuses the same `8p(q+1)²/2^256` shape for non-frameability. The
  term is a **query-model** charge; in the composed budget it must be read alongside the gate-work-
  factor reading of the same number, and mixing the two readings is the accounting error this package
  warns about. In domain 10 the same result is cited with the added identity "standard (added)".

### D10-11 — XMSS / LMS / LM-OTS size formulas

- **Statement as used here.** The RFC-derived wire-size formulas the audit uses:
  - XMSS: `4` (index) `+ 32` (randomness) `+ 67·32 + 20·32 = 2,820 B` — with the recorded note that
    the v2.0 code omits the randomness field and the test adds 32 back;
  - LM-OTS `W8`: `1,124 B = 4 + n + p·n`;
  - LMS `M32_H20_W8`: `1,772 B = 4 + 1,124 + 4 + 20·32`;
  - LMS public key: 56 B;
  - LMS `M24_H20` / `N24_W8`: 1,140 B.
- **Role.** The wire-size audit of the infrastructure route.
- **Label.** `[M]` — **measured against the RFCs**.
- **Citation as the source gives it.** The formulas are RFC-derived; the RFCs are the standards above.
- **Borrow.** Full.
- **Where used.** `domains/10-digital-infrastructure/` (per-step tables).
- **Notes.** The **pre-fix 1,768-byte** figure — an LMS size bug recorded as finding I6 — is
  **refuted**. Anything quoting 1,768 bytes is quoting a refuted number. The refutation is carried in
  `gaps-and-unknowns.md`.

---

## 5. Literature and implementation figures as recorded

The three entries below are recorded figures, not measurements taken by the programme. Each says so.

### D10-15 — Kampanakis et al., ePrint 2021/041, Table 2

- **Statement as used here.** `LMS256H20W8` verifier: code 2.15 KB, stack 1.81 KB, 2.857 Mcycles;
  `SPX256H20w256` stack 4.25 KB.
- **Role.** Constrained-device feasibility — recorded in the source as **"literature, not measured"**.
- **Label.** `[L]`.
- **Citation as the source gives it.** The ePrint number is given.
- **Borrow.** Partial (the table's figures).
- **Where used.** `domains/10-digital-infrastructure/` (source tag S5).

### D10-16 — pqm4 context counts

- **Statement as used here.** The pqm4 stack figures as recorded: ML-DSA-44 `m4fstack` 5,080 B sign /
  2,712 B verify; ML-DSA-65 6,616 / 2,712.
- **Role.** On-card feasibility.
- **Label.** `[L]` as given.
- **Citation as the source gives it.** As given.
- **Borrow.** Partial.
- **Where used.** `domains/10-digital-infrastructure/` (source tag S5, T3).
- **Notes.** These counts are for **ML-DSA**, not for a hash-based scheme; they belong to the domain's
  assessment of what the card can hold, and are not evidence about XMSS or LMS. The record gives no
  pqm4 version at the point of use — see the incomplete-citation list in `references.md`.

### D5-14 — OTBN / SLH-DSA resource counts

- **Statement as used here.** Equation D (Barbosa et al. Theorem 4) treated as a sourced
  partial-proof map; 63 local key generations and at most 86 verifications; **OTBN contributes no
  numeric term**.
- **Role.** The resource vector of the reduction.
- **Label.** `[L]`.
- **Citation as the source gives it.** As cited in source.
- **Borrow.** Partial.
- **Where used.** `domains/05-extraction-and-signature-reductions/src/slh_tree_conditioning_audit_v1.42.py`
  (lines 220–264).
- **Notes.** "OTBN contributes no numeric term" is the recorded finding; a reader must not supply one.

---

## 6. Where these figures are spent

The sizes and resource vectors in this document feed two arguments and no others:

- the infrastructure route's zone-size and response-size budgets, where the XMSS, LMS and SLH-DSA
  figures are measured against the DNS size constants catalogued in
  `protocol-and-ledger-assumptions.md` (`D10-12`);
- the compact-certificate argument, where the 27,056-byte hidden-signer slot is smaller than the
  SLH-DSA signature. The size arithmetic of that argument (Theorem C, its budget formula and the
  corrected inequality direction) is in `project-statements-and-amendments.md`.
