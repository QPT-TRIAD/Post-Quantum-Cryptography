# PQ CE-QS v1.21 — Quantified kill/keep resolution of the three remaining blockers

Date: 9 September 2026. Status: **analytical resolution; no new implementation claimed.**
This note attacks the three open blockers of v1.20 with exact arithmetic and rules each
sub-branch in or out. Everything below is either machine-verified arithmetic or a labeled
estimate with its assumptions stated. Nothing here is a measurement of an unbuilt system.

## Lane 1 — Size: 722,528 bytes vs 32,768

### 1.1 Where the bytes actually are (verified)

- Encoded frame / native gate ratio: 722,528 / 9,800,861 = **0.0737 B/gate** (native: 0.0881).
- Committed slots: 16,777,216 -> 268 MB of committed leaf space. The bytes are dominated by
  Merkle openings over this committed witness, **not** by any information-theoretic floor.
  The gate count is a property of this arithmetization, not a lower bound (v1.19 already ruled
  this correctly).
- Prefix obstruction is exact: 46,080 + 16 + 4,128 + 160 = **50,384 > 32,768** (identical
  arithmetic under both the old 4,288-byte and new 160-byte envelopes). Query-only compression
  of this layout is dead. The 176->150-row statistical lever saves only 3.2% of products and
  does not touch the obstruction.
- Per-seat proof budget inside the cap: 28,480 / 43 = **662 bytes/seat**.

### 1.2 Branch kill table (verified implications)

| Branch | Required B/kgate for cap | Best known IOP constants (10-100 B/kgate) | Verdict |
|---|---|---|---|
| Trace-only, current arithmetization (9.8M gates) | <= 2.9 | not reachable at 128-bit QPT | **DEAD** (implementation-bound, not bound-in-principle) |
| Compat mode: +43 ML-DSA-65 verifies (est. 53-96M gates total; estimate: ~1-2M gates/verify from ~11 NTTs + ExpandA pointwise + hashes) | <= 0.30-0.54 | orders of magnitude out | **DEAD, quantified** |
| Linear layers via GKR/sumcheck (public matrices A, B_d, C_d): 9,158,656 products leave the committed witness; only Keccak, challenge algebra, distinctness, and authorization remain in-circuit | core drops to ~0.5M gates | 20-50 B/kgate reachable | **KEPT** |
| + arithmetization-native hash (Poseidon2-class over the 384-bit mask field) replacing 2 in-circuit Keccak/seat | trace core ~60-100k gates + SoK verify ~2-5M gates -> total ~3-6M gates | need <= 5-10 B/kgate: frontier but in known range | **KEPT, tight** |
| SoK authorization mode replacing 43 ML-DSA verifications (SE-NIZK signature-of-knowledge; Groth-Maller concept, PQ instantiation) | same row | same | **KEPT, required** — compat mode is dead, so Mode S is not optional |

Conclusion: the only branch not ruled out by quantified argument is **Mode S**: GKR linear
layer + native-hash trace core + lattice SoK authorization, targeting ~3-6M in-circuit gates
at <= ~10 B/kgate. Feasibility is *tight but not refuted*; it is the candidate experiment the
v1.20 conclusion names. Byte budget: envelope 160 + handles 4,128 + proof <= 28,480.

New obligations created by this branch (each must be closed, not inherited):
1. Poseidon2-class hash -> re-derive H_link/H_challenge collision and extraction algebra;
   link width and the F_{2^384} mask equation may be retained, but the hash security pin
   (Lane 2) must be re-stated against the new primitive.
2. Lattice SoK suite -> registered independent authorization keys, chosen-message security,
   collaborative signing, same-seat equation with the trace layer (v1.20 Section 6).
3. GKR composition -> the extraction theorem must be re-proved for the composed protocol;
   public inputs (L_i, Z_i) and the identity equation are preserved, but knowledge soundness
   now spans two arguments.

## Lane 2 — Concrete QPT: from "open" to "pinned with named unknowns" (verified arithmetic)

Budget allocation with the shipped exact statistical terms:

- Statistical total: eps_A + eps_B-pair <= 2^-154.88 (exact rationals in the v1.20 JSON).
  Consumed share of the 2^-128 target: ~2^-23 of headroom lost -- negligible.
- Remaining for the five computational terms (cfg binding, H_link, H_challenge,
  joint-extract, vote-forge): effectively the full 2^-128; at 8 terms of <= 2^-131 each the
  sum is <= 2^-128.
- H_link at 384-bit output, collision structure Q^3/2^384 <= 2^-131 pins
  **log2 Q <= 84.33**; the preimage structure would permit 2^126.5. Using the wrong event
  inflates the claimed allowance by 2^42 in query count.
- **Resource pins the ledger can adopt today (conditional on C = M = 1 constants being
  discharged by the eventual reduction):** quantum queries to H_link <= 2^84.3 for any term
  relying on generic collision resistance; classical preprocessing bounded separately per the
  BHT-type tradeoff if claimed.

Named unknowns that still block qualification: the reduction constants C and multiplicity M
for the actual vector-commitment/extraction analysis; LWR hardness at the 176-row exposure
(the v1.20 row reduction makes exposure smaller but does not analyze it); privacy and
distributed-prover theorems. The ledger is now a finite checklist, not an open-ended one.

## Lane 3 — Distributed production: kill the naive branch, keep the packed one (verified arithmetic)

- BGW active security with n = 64, t = 21 satisfies n > 3t (64 > 63). The threshold is met.
- Naive per-gate BGW multiplication on a ~6M-gate nonlinear core: 6M x 4096 shares x 48 B
  = **~1.18 TB per proof. DEAD.**
- Packed secret sharing with O(n) amortized communication: ~6M x 64 x 48 B = **~18 GB per
  proof. Heavy but bounded** -- viable for rare certificate ceremonies, not per-slot.
- The 9,158,656 linear products distribute essentially for free: each seat locally computes
  its share contributions <a, s_i>; only the public sum enters the protocol. The MPC
  bottleneck is the nonlinear core, which Lane 1 has already minimized (~3-6M gates).
- Required new protocol (still open): packed actively-secure MPC for the nonlinear core with
  an identifiable-abort interface feeding the v1.19 retry theorem, plus a composition proof
  that share-level simulation preserves the public extraction algebra of v1.20 Section 3.
  AbortBlame and ExtractConflict remain separate interfaces (v1.20 Section 6 is correct).

## Consolidated verdict

| Blocker | This resolution | Status |
|---|---|---|
| Size | Only Mode S survives quantified attack; byte budget and gate budget stated | Open; now a finite engineering experiment, not an open question |
| Authorization in proof | Compat mode dead (0.3-0.5 B/kgate requirement); SoK mode required | Open; new suite obligation |
| Concrete QPT | Statistical terms exact; computational terms pinned to Q <= 2^84.3 etc. with named unknowns C, M, LWR | Open; finite checklist |
| Distributed production | Naive MPC dead (1.18 TB); packed branch (~18 GB) viable for ceremonies | Open; new protocol obligation |

Honest bottom line: no analytical step can cross these four lines -- they require the
candidate experiment (Mode S proof system), the SoK suite, the C/M/LWR reductions, and the
packed-MPC protocol respectively. What this resolution removes is the *search space*: every
other branch is now killed by arithmetic, so effort cannot be defensibly spent elsewhere.
Sign-off condition (unchanged): F-CONSTRUCT -> F-PROOF -> F-SIZE -> F-LIVE -> F-VERIFY,
with the Mode S branch as F-CONSTRUCT's content.
