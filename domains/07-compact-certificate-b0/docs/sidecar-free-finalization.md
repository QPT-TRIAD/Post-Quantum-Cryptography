# CE-QS — 32-KiB certificate requirement: closure (v1.44)

**Date:** 11 September 2026
**Evidence:** `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` — 39 tests,
`--report`, and `--real-demo` with real signatures through liboqs 0.16.0.
**Security theorems used:** `domains/06-qpt128-security-target/docs/qpt128-finalization.md`
(v1.43; Theorem A for public signers, Theorem B for hidden signers).
**Follow-up:** hidden signers within 32 KiB are analyzed in the v1.45 document
(`domains/08-hidden-signers/history/hidden-signer-32kib-v1.45.md`); that analysis is
carried further in `domains/08-hidden-signers/docs/hidden-signer-32kib.md`.

**Paths.** Paths that name other project files are relative to the repository root, and
version suffixes have been dropped from file names. Where a pointer carries a line
number, that number is the one recorded in the source tree; it is not re-verified
against the repository copies. A project file named here that is not copied into this
repository is marked as such.

---

## 0. Result

The 32-KiB requirement bundles seven properties (§1). This revision closes everything current cryptography can close, measures it with real signatures, and bounds what blocks the rest.

| Certificate | R1 ≤ 32,768 B | R2 public verify | R3 extract ≥ 22 | R4 no sidecar | R5 no opener | R6 hidden signers | R7 QPT-128 |
|---|---|---|---|---|---|---|---|
| **B0 + OV-V** | **11,396 B, measured** | yes, real signatures | yes, 22 seats, blame verified | yes | yes | **no: bitmap public** | Theorem A, +23.0 bits, under EUF-CMA of OV-V |
| **B0 + OV-V‖SNOVA_29_6_5** | **30,918 B, measured** | yes | yes | yes | yes | **no** | Theorem A; secure if *either* scheme is EUF-CMA |
| B0 + SNOVA_29_6_5 / SNOVA_60_10_4 | 19,738 / 24,984 B, measured | yes | yes | yes | yes | no | Theorem A, under SNOVA |
| B1 Mode S (hidden signers) | 5,712 B + proof | relation fixed and tested | algebra tested | yes | yes | **yes** | Theorem B, +29.4 bits |
| B1 proof within 27,056 B | **none known** (Theorem C, §3) | — | — | — | — | — | — |

**Status.**
- **Main goal met.** The project's main goal, stated on 11 September 2026, is
  conflict-extractable, compact post-quantum quorum signatures without a sidecar. That
  is R1–R5 plus R7. Profile B0 meets it: it is executable, uses real signatures of
  claimed category 5, and fits 32 KiB with a margin of up to 21,372 bytes.
- **Hidden signers (R6) together with R1 remain open.** R6 is part of the CE-QS security
  experiment (`docs/01-research-journey/pqt.md:130`) and was part of the stated goal. The
  gap is quantified:
  - **Witness-committing proofs** (KKW, BN++ or FAEST-style) fit the 27,056-byte slot only if each seat's witness is at most 359 bits at N = 2^16. That rises to 1,006 bits at N = 2^48, or 1,258 bits with 32 grinding bits (Theorem C, §3.1). Theorem C assumes one Grover iteration costs at most 2^24 gates.
  - **Cheapest known instantiation:** the Mode S relation needs 2,816 bits per seat with the cheapest published primitives (§3.3).
  - **Succinct systems:** published sizes exceed the slot. A single category-5 ring signature hiding one signer among 64 already takes 21.49 KB (§3.4).

---

## 1. The requirement, as the project states it

| Id | Requirement | Where stated |
|---|---|---|
| R1 | The whole certificate is at most 32,768 bytes | `docs/01-research-journey/pqt.md:1382, 1422`; `domains/02-ceqs-construction-evolution/docs/32kib-contents-contract.md:15-21` |
| R2 | A verifier holding the fixed, authenticated 64-seat registry checks the certificate alone | contract `:21-23` |
| R3 | Two conflicting accepted certificates publicly yield ≥ 22 double-authorizers | contract `:27, 56-62`; `pqt.md:1515` |
| R4 | No proof file, omitted opening, external leaf list or protocol transcript is needed | contract `:21, 124` |
| R5 | No opener's secret is used at extraction | contract `:27` |
| R6 | Seat indices and credentials stay private (hidden-signer privacy) | `pqt.md:130, 606-622`; contract `:18, 25` |
| R7 | QPT-128, fixed in v1.43 as a work factor with gate accounting | `domains/06-qpt128-security-target/docs/qpt128-finalization.md` §2 |

**Contract layout and B0.** The contract lays out the certificate as context (208 B), 43 handles (5,504 B) and one joint proof (≤ 27,056 B) (contract `:7-19`). It assigns contents "by purpose, before selecting a proof system" (`:13`). It does not forbid another layout, but notes that replacing the handles needs a different public extraction mechanism (`:27`). B0 is such a layout: the bitmap and the public signatures are its extraction mechanism.

---

## 2. Closing R1–R5 and R7: profile B0, measured

**Frame** (`domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`, suite 0x44B0):

```
header (208 B) ‖ bitmap (8 B, exactly 43 bits set) ‖ 43 signatures in seat order
|QC| = 216 + 43·s        fits  ⇔  s ≤ 757 bytes
```

- **Approval message.** Seat i signs `"CQ44/B0/VOTE" ‖ cfg ‖ d ‖ m ‖ u8(i)`, where cfg = H("CQ44/cfg/B0", scheme_id, pk₀..pk₆₃).
- **Verification** (`verify_b0`). Checks, in order:
  - the header is canonical;
  - cfg equals both the authenticated value and the value recomputed from the registry;
  - exactly 43 seats are set;
  - the frame has the exact expected length;
  - every signature verifies.
- **Extraction** (`extract_b0`). Verifies both frames and requires equal cfg and d but different m. It returns bitmap₀ ∧ bitmap₁: at least 43 + 43 − 64 = 22 seats, each with both signatures at recorded positions.

**Measured with real signatures** (`--real-demo`; the output JSON records liboqs 0.16.0 and liboqs-python 0.16.0; commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`). For every scheme the demo:
- generated 64 keys and two conflicting frames with exactly 22 common seats;
- verified both frames, extracted the common seats and checked every blame;
- flipped one byte inside the first signature (for the hybrid, one byte inside each half).

| Scheme (claimed category) | Signature | Public key | Frame | Verified | Extracted | Blame verified | Tamper rejected |
|---|---:|---:|---:|---|---:|---|---|
| **OV-V-pkc** (5) | 260 | 446,992 | **11,396** | yes | 22 | yes | yes |
| **SNOVA_29_6_5** (5) | 454 | 2,716 | **19,738** | yes | 22 | yes | yes |
| **SNOVA_60_10_4** (5) | 576 | 8,016 | **24,984** | yes | 22 | yes | yes |
| **OV-V-pkc‖SNOVA_29_6_5** (5) | 714 | 449,712 | **30,918** | yes | 22 | yes | yes, both halves |
| MAYO-5 (5) | 964 | 5,554 | 41,668 | rejected as oversize | — | — | — |
| ML-DSA-87 (5), via pqcrypto and liboqs | 4,627 | 2,592 | 199,177 | rejected as oversize | — | — | — |
| Falcon-padded-512 (1) | 666 | 897 | 28,854 | yes, but category 1 | 22 | yes | yes |

- **Runs.** The demo makes eight runs over seven distinct schemes; ML-DSA-87 runs under both libraries.
- **Sizes not run by `--real-demo`:**
  - Falcon-padded-1024 (1,280 B) was executed only in the separate liboqs probe;
  - SQIsign-V (292 B, 12,772-byte frame, fits) comes from its specification;
  - HAWK-1024 (1,221 B, does not fit) comes from its specification.

**Security (R7).** Theorem A of v1.43 applies unchanged.
- **Accountability** is deterministic: at least 22 seats, each with two verifying signatures.
- **Non-frameability and safety** reduce tightly to EUF-CMA of Σ, with a loss of 64 and no extractor.
- **Quorum unforgeability.** With at most 21 corrupt seats, every accepted certificate on (d, m) carries at least 22 honest-seat signatures on m. So at least 22 honest seats really approved m, except with probability at most 64·Adv_Σ.
- **QPT-128 margin.** With the category-5 envelope in gate units, D2 holds with a **+23.0-bit margin**, and Pr ≤ 2^−25 at 2^128 gates.

**Hybrid.** A hybrid slot σ_a‖σ_b verifies only if both halves verify under independent keys.
- **Why it holds.** A forgery on an unqueried message contains a forgery of each scheme. The reduction to either scheme embeds the challenge key in that half and generates the other half's keys itself. It answers each signing query with one oracle call plus one local signature. So Adv_hybrid ≤ min(Adv_OV, Adv_SNOVA) at essentially the same running time.
- **When to use it.** The hybrid is the defensive choice: SNOVA's structure is newer than UOV's, although both are multivariate.

**Limits of B0.**
1. **No hidden signers (R6):** the bitmap names the 43 signers.
2. **Not standardized:** OV and SNOVA are candidates in NIST's additional-signature process, not FIPS standards. A-sig (EUF-CMA at category 5) is a named assumption about them.
3. **Registry size:** OV-V-pkc public keys total 64 × 446,992 B ≈ 28.6 MB. This is fixed registry data (contract `:23`), not per certificate.

---

## 3. Why R1 and R6 are not currently met together

A hidden-signer certificate must prove a hidden relation: 43 distinct registered seats, knowledge of their credentials, and correctly formed handles. The contract gives that proof 27,056 bytes = **216,448 bits**. B1 Mode S fixes the relation, frame, extractor and QPT-128 ledger (v1.43 Theorem B); only the proof is missing.

### 3.1 Theorem C — witness-committing proofs

**Setting.** The proof for R_S uses τ parallel repetitions in the style of KKW, BN++ or FAEST v2. In each repetition:
- **(i)** a prover without a witness is accepted with probability ≥ 2^−b, for example by guessing the unopened party among N = 2^b;
- **(ii)** at least one bit is carried per bit of the extended witness: the 43 credentials of c bits plus w further bits per seat (nonlinear wire outputs or intermediate states).

Both published size formulas have form (ii):
- FAEST v2, §3.1: τ·(ℓ + 3λ + B) + T_open·λ + …;
- BN++/AIMer: τ·(3λ + λ⌈log₂N⌉ + (2C+1)·log₂|F|).

The challenge is a hash chain of 2^h steps over a suffix the prover chooses, such as the grinding counter or the unopened commitment. There is optionally a grinding condition of w_g bits.

Two families are **not covered**, because they violate (ii):
- ZKB++, which sends the third input share in only 2 of 3 challenges;
- Ligero-style sublinear proofs.

**Cost assumption.** The bounds are necessary conditions obtained from attacks, so they need an *upper* bound on attack cost. The analysis assumes one Grover iteration costs at most 2^24 gates.
- The Keccak-f[1600] T-count alone is 499,200 < 2^19.
- The factor 2^5 is an allowance for uncomputation and Clifford gates.
- So fewer than 2^128 gates allow up to 2^(104−h) iterations.

**Theorem C.** If such a proof is QPT-128 (D1), then:
- **Challenge:** τ·b + w_g ≥ s, where s = 212 at h = 0 and s = 180 at h = 16;
- **Credentials:** c ≥ 218 bits;
- **Seeds** (with per-repetition GGM openings, hypothesis (iii)): each opened seed has ≥ 212 bits;
- **Size:** at least τ·43·(c + w) bits, plus τ·b·212 bits under (iii).

It therefore fits the proof slot only if the per-seat witness c + w is at most the budget in the table below. Budgets are in bits and include the credential.

| log₂ N = b | τ (base) | Base budget | 32 grinding bits | 2^16-step chain + 32 grinding bits | With GGM seed term (iii) | Prover leaf expansions τ·2^b |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 27 | 186 (none fit) | 218 | 264 | 146 (none fit) | 6.9 × 10³ |
| 12 | 18 | 279 | 335 | 387 | 220 | 7.4 × 10⁴ |
| **16** | 14 | **359** | 419 | 503 | 280 | 9.2 × 10⁵ |
| 20 | 11 | 457 | 559 | 629 | 359 | 1.2 × 10⁷ |
| 24 | 9 | 559 | 629 | 719 | 440 | 1.5 × 10⁸ |
| 32 | 7 | 719 | 838 | 1,006 | 561 | 3.0 × 10¹⁰ |
| 40 | 6 | 838 | 1,006 | 1,258 | 641 | 6.6 × 10¹² |
| 48 | 5 | **1,006** | **1,258** | 1,258 | 770 | 1.4 × 10¹⁵ |

- **Units:** "none fit" means even a 218-bit credential exceeds the budget.
- **Honest verifier costs:** 32 grinding bits cost about 4.3 × 10⁹ hashes per certificate. A 2^16-step chain costs 65,536 sequential hashes per proof and per verification.
- **2^18-gate variant:** assuming at most 2^18 gates per hash instead gives the same or smaller budgets (`--report`).

*Proof.*
1. **Challenge.** Fix the transcript except for the prover-chosen suffix, and search that suffix until the challenge equals the cheating prover's guesses and passes grinding. The marked fraction is 2^−(τb + w_g); each Grover iteration costs one chain evaluation, i.e. at most 2^(24+h) gates. Suppose τb + w_g < s. Then `grover_reaches_one_third` exhibits a success probability ≥ 1/3 within 2^(104−h) iterations:
   - for p ≥ 1/2, zero iterations suffice;
   - for 1/16 ≤ p ≤ 1/4, one iteration gives sin²(3θ) > 0.47;
   - for p ≤ 1/32, steps of 2√p ≤ 0.354 < 19/50 let some k land y = (2k+1)√p in [31/50, 1]. There sin²((2k+1)θ) ≥ (y − y³/6)² ≥ 1/3, checked exactly.

   D1 therefore fails.
2. **Credentials.** The 64 honest credentials are marked points among 2^c. If c ≤ 217, Grover finds a preimage of an honest key within 2^104 iterations, which frames that seat.
3. **Seeds.** Under (iii), a hidden seed of ≤ 211 bits is recovered from its commitment. Together with the opened seeds it reveals that repetition's witness: x = Δx ⊕ Σ shares, or w = d ⊕ Σ PRG(leaves).
4. **Counting.** Hypothesis (ii) gives τ·43·(c + w). `theorem_c_budget` solves for the budget: see `--report`, key `theorem_c_witness_committing`, and tests `test_grover_threshold_exact` and `test_theorem_c_wire_budget`. ∎

### 3.2 What the per-seat relation must contain

Per seat, R_S (contract `:71-77`; Mode S) needs:
- **a key map** from the credential to the registered key. It must be one-way and collision-resistant, since a second opening defeats completeness (v1.43, E4).
- **a domain PRF** that produces the link L and the mask behind Z, keyed by the credential.
- **a selector** that picks the registered key and enforces distinctness. Its one-hot row costs about 64 products per seat; selecting the public keys is then linear.

### 3.3 Known primitives against the budget

**Smallest verified category-5 witnesses for one evaluation** (read in the primary sources):

| Primitive (scheme) | Witness per evaluation | Output | Collision-resistant at ≥ 336 bits? | Source |
|---|---:|---:|---|---|
| MQ map, x ∈ F₂³²⁰ (MQOM2-L5-gf2) | 320 bits | quadratic map | no | MQOM round-2 spec, Tables 6–7 |
| Rain₃, n = 256 (Rainier; BN++ drops the last Δt) | 768 bits (1,024 without BN++) | 256 bits | no | ePrint 2021/692 Fig. 5, §5.2.1; 2022/588 App. B.2 |
| LowMC-255, 4 × 85 S-boxes (Picnic3-L5) | 1,020 AND outputs + 255 key bits | 255 bits | no | Picnic spec v3.0, Table 2, §6 |
| AIM2-V (AIMer v2.1) | 1,024 bits | 256 bits | no | AIMer v2.1, Table 3, Alg. 8 |
| SDitH2-L5-gf2 | 1,144 bits | syndrome | not a hash | SDitH round-2 spec, Tables 3–4 |
| AES-256-EM (FAEST-EM-256) | 2,688 bits | 256 bits | no | FAEST v2 spec, Table 3.3 |
| AES-256 (FAEST-256) | 3,104 bits | 256 bits | no | FAEST v2 spec, Table 3.3 |

The MQ map fails collision resistance structurally: for a fixed δ, F(x) = F(x+δ) is linear in x.

**One Mode S seat needs:**
- a key map with ≥ 336-bit collision resistance. That takes ≥ 2 evaluations of any 256-bit-output primitive above; no wider MPC-friendly primitive appears in the verified sources.
- link and mask outputs L ≥ 256 bits (row E5) and R = 512 bits, i.e. ≥ 768 pseudorandom bits. That takes ≥ 3 further 256-bit evaluations.

**Result.**
- **Rain₃ instantiation.** Rain₃ with one shared 256-bit key and the BN++ saving on every public output costs 256 + 5 × 512 = **2,816 bits per seat**. That is 2.2× the most generous budget in the table (1,258) and 3.9× the base budget at b = 32 (719).
- **The bare MQ key relation.** MQOM's 320 bits would fit from b = 16, but it gives neither collision resistance nor PRF security. Publishing G_D(x) for many domains D linearizes after about n(n+1)/2 ÷ 768 ≈ 67 domains, which exposes the credential.
- **Keccak** (Mode S as specified) costs 38,400 AND gates per permutation.

**No known primitive meets the per-seat budget.** This is an assessment of the published primitives, not an impossibility proof.

### 3.4 Succinct and ring-signature evidence (outside Theorem C)

Theorem C does not cover proofs whose size is sublinear in the witness. For those, only published measurements exist, all at lower security than QPT-128 unless stated otherwise.

| System | Published size | Security / properties | Source |
|---|---:|---|---|
| Binius64 PCS for Mode S's committed size (≥ 51,600 words) | ≥ 109,856 B | 96-bit, no QROM analysis | vendored estimators, `binius64_min_bytes` |
| LaBRADOR, 2^20 R1CS | ≈ 58 KB | not zero-knowledge | LaBRADOR paper |
| Lattice ZK toolkit (Biasioli et al. 2026) | ≈ 110 KB | with zero knowledge | as recorded in v1.43 §7 item 14 (`domains/06-qpt128-security-target/docs/qpt128-finalization.md`) |
| SmallWood | ≥ 40.8 KB | — | as recorded in the v1.43 research (`domains/06-qpt128-security-target/docs/qpt128-finalization.md`) |
| VOLE-in-the-head ring signature, AES-256-EM: **one** hidden signer among 2^6 | 21.49 KB | λ = 256, not linkable | Chiang et al., CCS'25, ePrint 2025/113, Table 2 |
| Same scheme, linkable, AES-256, ring 2^6 | 51.27 KB | λ = 256, linkable | same |
| LowMC ring signature, ring 2^7 | 52 KB | described as 128-bit post-quantum | Goel et al., PoPETs 2022, Table 2 |

- **Succinct systems:** none fits 27,056 B, even at its own lower security level.
- **Ring signatures:** a single non-linkable category-5 ring signature for one hidden signer among 64 already takes 79% of the slot. The certificate needs 43 distinct hidden signers with linkable handles.
- **Threshold ring signatures:** no category-5 sizes were found.

### 3.5 Designs that trade away R2, R4 or R5 instead

These were examined and rejected for this contract:
- **Per-domain shuffled rosters of one-time keys.** Verification then needs per-domain data outside the certificate, which fails R4. Public identity recovery after a double signature needs a Lamport-size tripwire, which fails R1.
- **Fixed pseudonym rosters.** Pseudonyms link across certificates, so R6 fails under adaptive scheduling. Mapping a pseudonym back to a seat needs an opener, which fails R5.
- **Encrypted bitmap.** A public verifier must know which key checks each signature, which fails R2 or R6.
- **Key blinding** (for example, isomorphism-of-polynomials blinding of OV keys). Membership of a blinded key needs a zero-knowledge proof over the 64 registry keys, which leads back to §3.1–§3.4.

---

## 4. Recommendation and open extension

| Option | Benefit | Cost |
|---|---|---|
| **A. Adopt B0 (meets the main goal)**: OV-V, or OV-V‖SNOVA_29_6_5 for defence in depth | A measured certificate of 11,396 or 30,918 B. Real verification, public extraction of ≥ 22 seats, no sidecar, no opener. QPT-128 by Theorem A. | Hidden-signer privacy (R6). Reliance on non-FIPS signature candidates. |
| B. Keep R6 and 32 KiB | The full v1.24 contract | Open until a proof meeting §4.1 exists; see `domains/08-hidden-signers/docs/hidden-signer-32kib.md` |
| C. Keep R6, drop 32 KiB | Mode S, QPT-128 by Theorem B (+29.4 bits) | Megabyte certificates with known witness-committing proofs (3.3M AND gates per certificate for the Keccak circuit) |

### 4.1 Falsifiable acceptance criterion for option B

A backend closes R1 + R6 if and only if **all** of the following hold for its relation:
1. **Size:** the proof, plus handles and header, is at most **32,768 bytes**.
2. **Zero knowledge:** it is zero-knowledge, with simulation charged in the v1.43 ledger (row E2).
3. **Extraction:** it is online-extractable in the QROM or a stated model. Its extraction error and extractor time are entered into
`domains/06-qpt128-security-target/src/qpt128_finalization.py` so that D2 holds in gate units.
4. **Witness budget:** if it is witness-committing, its per-seat extended witness is at most the §3.1 budget for its own b, w_g and h. The column "2^16-step chain + 32 grinding bits" applies exactly when it uses those settings.
5. **Execution:** it runs, and its frame round-trips through `parse_b1`. `verify_b1` reports `authorization_verified = True` with a backend declared `qualified`.

---

## 5. Reproduce

```
python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --self-test
    # 39 tests, OK (stdlib only); ~0.09-0.16 s
python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --report
    # size tables, Theorem C
OQS_INSTALL_PATH=<liboqs 0.16.0 install> PYTHONPATH=<liboqs-python 0.16.0> \
python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --real-demo
    # measured table in §2; 8 runs, exit 0
python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --self-test
    # 19 tests, OK
```

**liboqs build:** tag `0.16.0`, commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`, built as a shared library with `-DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON -DOQS_DIST_BUILD=ON`.
- **Without `OQS_INSTALL_PATH`:** the demo never imports liboqs-python.
- **With it:** the exact library is loaded with ctypes before the wrapper is imported, so the wrapper's clone-and-build fallback cannot run.

The digests below are the ones recorded in the source tree for the two v1.44 evidence
files (the revision the numbers in this document were produced with). The repository
copies carry rewritten relative paths, so their digests differ; the digest of the
repository copy of this document's evidence file is recorded in
`domains/07-compact-certificate-b0/VERIFICATION.md`.

| Source-tree file (v1.44 revision) | sha256 |
|---|---|
| `sidecar_free_certificate_v1.44.py` | `a30f1078ffee7f395bbd82a1b7b9a37f9c5518a71e63a4d5a85b0446146e68a8` |
| `qpt128_finalization_v1.43.py` | `2762b2c2880ea514dceb60a5fe344327f5eb2c546e9e40be6b2fcb7fe4156bb4` |

**Non-claims.**
- **Certificate:** no hidden-signer certificate of at most 32 KiB is produced.
- **Signature schemes:** no claim that OV or SNOVA meets category 5 beyond their submitters' claims.
- **Theorem C:**
  - it covers only KKW-, BN++- and FAEST-style witness-committing proofs;
  - it rests on the stated upper bound of 2^24 gates per Grover iteration;
  - succinct systems remain open.
- **Real demo:** it measures frames, verification, extraction and tamper rejection. It does not cover network protocols, key management or liveness.
