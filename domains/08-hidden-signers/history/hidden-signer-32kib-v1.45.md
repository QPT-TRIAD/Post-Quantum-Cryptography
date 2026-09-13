# CE-QS — hidden signers within 32 KiB (v1.45)

> **Superseded in part by v1.46** (`hidden_signer_32KiB_v1.46.md`, `hidden_signer_modeB_v1.46.py`): the linear handle of Mode A below was found to leak (≈123-bit quantum at 256 bits), and a power-map handle with an expanding quadratic key map ("Mode B") gives the first sizing under 32 KiB.

**Date:** 11 September 2026
**Evidence:** `hidden_signer_modeA_v1.45.py` (8 tests; `--report`)
**Builds on:**
- `sidecar_free_finalization_v1.44.md`: B0 and Theorem C;
- `QPT128_finalization_v1.43.md`: definitions D1/D2 and Theorems A/B.

---

## 0. Answer

**Hidden signers within 32 KiB are not solved, and cannot be with published post-quantum cryptography today.** This revision makes three contributions:
1. **Literature:** it establishes that no published scheme has the required combination.
2. **Mode A:** a new design that reduces the problem to exactly two missing components. Its frame, relation and public extractor are implemented and tested.
3. **Exact target:** it quantifies what those components must achieve.

| Question | Result |
|---|---|
| Does any published scheme provide a hidden 43-of-64 quorum, public verification, ≤ 32,768 B, public keyless tracing of double-signers, and category-5 PQ security? | **No** (§1) |
| Closest semantics | Tetris (ePrint 2025/730): hides the signers and publicly reveals S₀∩S₁ on conflict. It is pairing-based with a trusted setup, so **not post-quantum** |
| Closest post-quantum scheme with public tracing | 43 × 79.3 KB lattice traceable ring signatures ≈ **3.4 MB** (≈ 104× over) |
| Best new design | **Mode A** (§2). It fits 32 KiB only if one seat's key map needs at most 80–611 witness bits in the proof (for 2^24–2^40-leaf trees) |
| Best published key map for Mode A | Two Rain₃-256 evaluations, 1,024 witness bits: **41,635 B at 2^40 leaves**. It fits (32,415 B) only at an extreme setting (§3): 2^45 leaf expansions and a 2^24-step challenge hash chain |
| Who can produce the proof? | No known collaborative prover (§4). A single aggregator that sees the openings can frame seats |

**What would close it.** Either of these:
- **(a)** Both of the following:
  - a key map with ≤ ~600 witness bits that is one-way on 224-bit openings, collision-resistant at ≥ 313 bits, and hiding under the linear handle leakage;
  - a collaborative VOLE-in-the-head prover secure against 21 of 64 corruptions for 2^32–2^40-leaf trees, with a QROM extraction bound that can enter the v1.43 ledger.
- **(b)** A post-quantum analogue of Tetris.

**What can ship now.** B0 (v1.44) meets the stated main goal but publishes the signer set.

---

## 1. Literature (primary sources read for this survey)

| Family | Best published point | Why it fails |
|---|---|---|
| Post-quantum threshold ring signatures | LoTRS (ePrint 2026/974): 25.0 KiB for N=32, T=16 | 128-bit only; quorum is a hidden column of a T×N key grid, so 43-of-64 is not expressible; no tracing |
| | LastRings (2025/1633): ≥ 108 kB | No tags, 128-bit only |
| | Chiang et al. (2025/113): t linkable partials | t = 43 at λ = 256 is ≈ 2.2 MB; the tags link but never identify |
| Post-quantum traceable ring signatures, public tracing, N = 64 | Wei et al. (SAC'23), lattice NIST-5 parameters: 79.3 KB | One per member: 43× ≈ 3.4 MB |
| | Scafuro–Zhang (2021/1054), λ = 256: 524 KB | One per member |
| Accountable / private threshold signatures | Boneh–Komlo TAPS, lattice TAPS (CT-RSA'24: 42.34 KB at N=32) | Tracing needs a **secret key**, which violates R5 |
| Hidden quorum with public equivocation tracing | Tetris (2025/730) | Pairings + Groth–Sahai + CRS: not post-quantum |
| Joint provers for MPC-in-the-head / VOLE-in-the-head | Doerner–Kondi–Rosenbloom (CRYPTO'24): impossibility against all-but-one corruption with black-box hashing | We need ≤ 21 of 64; no protocol for that setting found |
| | Carozza–Couteau (2024/1897): naive distributed FAEST-128s needs ≈ 937 GB of seed trees | Impractical |
| | Feneuil et al. (2026/1125): threshold MPC-in-the-head signature | Single shared witness, no ring, λ = 128 |
| Witness-free OWFs at L5 | MQOM2/KuMQuat: MQ over F₂, n = m = 320, ≈ 11.7 kB for **one** key | Degree 2, so no collision resistance and linearizable (v1.44 §3.3) |
| | FAEST-d7 (2024/490) halves the AES witness | L1 only |
| | Sparse cubic hash (Ding–Yang) | Broken (Aumasson–Meier) |

---

## 2. Mode A — the design that minimizes the hidden relation

**Idea.** Mode S proves two credential-keyed hash evaluations per seat: a key map, and a domain PRF for the link and mask. Mode A removes the PRF and the link tag.

**Registry epoch** (fixed, authenticated, not certificate-specific):
- For each domain d of the epoch, seat i draws a one-time opening (s, r): s is 224 bits and r is 336 bits.
- The seat registers Y[d][i] = K(D_A, s, r), where D_A = H("CQ45/A/K", epoch, d).
- cfg commits to the epoch, the domains and every Y.

**Handle.** For message m, c(m) = SHAKE256("CQ45/A/c" ‖ cfg ‖ d ‖ m) is a 336-bit field element in F = GF(2)[X]/(X³³⁶+X⁷+X⁴+X+1). The seat's handle is

  Z = r ⊕ c(m)·s   (42 bytes).

**Certificate.**

  header 208 B ‖ 43 handles (strictly increasing, 1,806 B) ‖ proof ≤ 30,754 B

The proof slot is 3,698 B larger than Mode S's, because a handle is 42 bytes instead of 128.

**Relation R_A.** There exist rows (i_j, s_j, r_j) such that:
1. the i_j are distinct in [0, 64);
2. s_j < 2^224;
3. K(D_A, s_j, r_j) = Y[d][i_j];
4. Z_j = r_j ⊕ c(m)·s_j.

Per seat the witness is s, r, a 6-bit index and K's internal witness. The handle equation is linear and free; selecting a registry key is linear in the one-hot selector.

**Public extraction** (`extract`). Given two accepted certificates with equal (cfg, d) and m₀ ≠ m₁:
- Set δ = c₀ ⊕ c₁. For every pair (Z₀_j, Z₁_k), 1,849 in total, compute s′ = (Z₀_j ⊕ Z₁_k)/δ and r′ = Z₀_j ⊕ c₀·s′.
- Keep s′ < 2^224, and look K(D_A, s′, r′) up in the domain's 64 keys.
- A hit names the seat. The public evidence (s′, r′, j, k) is checked by `verify_blame`.
- **Tested:** every overlap from 22 to 43 recovers exactly the common seats, and every blame verifies. A frame that cannot know seat 0's opening does not name seat 0. Equal messages and differing domains are rejected.

**Security sketch.** This is informal and names assumptions; it is **not** a theorem.

| Property | Argument | Assumption |
|---|---|---|
| Privacy within a domain | An honest seat reveals one handle per domain; r is uniform and independent of s, so Z is uniform | K hides (s, r); proof is zero-knowledge |
| Privacy across domains | Openings are fresh per domain | same |
| Non-frameability | A second handle for seat i requires s_i, which is hidden by r in Z and one-way in K; otherwise the proof is unsound | K one-way; proof extractable |
| Completeness | A double-signer's two handles share the registered opening, unless it opens Y twice | K collision-resistant (binding) |
| Distinctness | Enforced by the relation | proof soundness |
| Cost of fresh openings | The registry needs 64 × T × 64 B: 268 MB per epoch of 2^16 domains | (A5) |

---

## 3. Mode A sizing (FAEST v2 formula; reproduces FAEST-256s/f and FAEST-EM-256s/f to the byte)

**Parameters.** The challenge and credential sizes are the attack-derived minimums at ≤ 2^24 gates per hash (v1.44 Theorem C):
- challenge bits: 212, or 180 with a 2^16-step chain, or 164 with a 2^24-step chain;
- credential: 224 bits (43 handles × 64 keys as targets);
- per seat: 224 + 336 + 6 + key-map witness bits;
- T_open = challenge bits − grinding bits; 2 leaf-commit blocks; λ = 256.

These settings **favour fitting**. A security claim would need at least the 2^18-gate bound and a rigorous extraction ledger.

| Setting (tree leaves, grinding bits, chain) | τ | Max key-map witness that fits | SHAKE256, 1 block (38,400) | Rain₃ ×2 (1,024) | AES-256-EM ×2 (4,864) | Hypothetical witness-free (0) |
|---|---:|---:|---:|---:|---:|---:|
| 2^16, 0, none | 14 | none fit | 2,943,310 | 130,766 | 419,726 | 53,710 |
| 2^24, 16, 2^16 | 7 | 80 | 1,474,544 | 68,272 | 212,752 | **29,744** |
| 2^32, 16, 2^16 | 6 | 193 | 1,264,940 | 59,564 | 183,404 | **26,540** |
| 2^32, 32, 2^16 | 5 | 370 | 1,054,824 | 50,344 | 153,544 | **22,824** |
| 2^40, 32, 2^16 | 4 | 611 | 845,219 | 41,635 | 124,195 | **19,619** |
| 2^44, 32, 2^24 | 3 | 1,045 | 635,103 | **32,415** | 94,335 | **15,903** |

Certificate sizes are in bytes; bold marks sizes ≤ 32,768 B. "none fit" means even a zero-witness key map exceeds 32,768 B.

**Reading the table.**
- **Witness-free key map:** Mode A would fit comfortably from 2^24-leaf trees. No such primitive is known.
- **Best published key map (two Rain₃-256 evaluations):**
  - It misses by 27% at 2^40 leaves.
  - It fits only at 2^44 leaves with a 2^24-step chain: about 2^45 leaf expansions per certificate, and ≈ 1.7 × 10⁷ sequential hashes for every verification.
  - Rain is analyzed as a one-way function, not in this two-block, collision-resistant use.
  - All of this is with fitting-favourable parameters.
- **The executable SHAKE256 reference and AES-based key maps** are 3× to 90× over.

---

## 4. The collaborative-prover barrier

Whoever computes the proof must hold all 43 openings (s, r). With one opening and one handle, anyone can compute a second handle Z′ = r ⊕ c(m′)·s, then prove it, which frames that seat. So the proof must be produced **without any party learning an honest seat's opening**. The v1.43 Theorem B premise E7 (an ideal F_Prove) is exactly this assumption.

For VOLE-in-the-head the seed trees must stay hidden, so the 2^32–2^40-leaf expansions would run inside MPC among 64 parties. That is far beyond the ≈ 937 GB that Carozza–Couteau already report for naive distributed FAEST-128s. Doerner–Kondi–Rosenbloom rule out black-box distribution against all-but-one corruption. The honest-majority case (≤ 21 of 64) is not ruled out, but no protocol exists.

---

## 5. Options

| Option | Status |
|---|---|
| **Ship B0** (v1.44): 11,396 B with OV-V, or 30,918 B with the hybrid | Available now; signers public |
| **Research track A1:** a low-degree key map with ≤ ~600 witness bits that is one-way, binding and hiding under linear leakage, plus cryptanalysis | Open. The requirement is exact (§3); sparse cubic designs have a history of breaks |
| **Research track A3/A4:** an honest-majority collaborative VOLE-in-the-head prover and its QROM extraction bound | Open (§4) |
| **Hidden signers above 32 KiB** | Two routes: Mode A with Rain₃ at ≈ 42–68 KB under fitting-favourable sizing, with no prover and no theorem; or Mode S with v1.43 Theorem B at megabytes, with an ideal prover |
| **Non-post-quantum hidden quorum** | Tetris-style pairings; excluded by R7 |

---

## 6. Reproduce

```
python3 hidden_signer_modeA_v1.45.py --self-test   # 8 tests, OK
python3 hidden_signer_modeA_v1.45.py --report      # §3 table, FAEST reproduction
```

| File | sha256 |
|---|---|
| `hidden_signer_modeA_v1.45.py` | `1aef787f4096c8647cf3af0a19e723e6dabcc4bef675739c059f51022f54ac94` |

**Non-claims.**
- No compact hidden-signer certificate is produced.
- No zero-knowledge backend exists in this file.
- No security theorem is given for Mode A.
- The sizing is an estimate built on the FAEST v2 formula, with attack-derived minimum parameters.
