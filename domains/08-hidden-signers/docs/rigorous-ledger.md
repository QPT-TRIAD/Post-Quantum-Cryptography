# The rigorous ledger (v1.47): rows, constants and provenance

`../src/mode_b_rigorous_ledger.py` computes the domain's gate-unit security ledger. It is the Mode B
instance of the programme's QPT-128 accounting (domain 06), and it is executable: `--self-test` runs
7 tests, `--report` prints every row, sweep and comparison reproduced below
(`../results/ledger-report.json`).

**What kind of thing this is.** Every row is a **model-or-ledger estimate** expressed in gate units
with exact rationals and *uncapped endpoints* — the endpoints are not clipped at 2^128 gates, so a
row that is favourable at a smaller budget is not silently flattered at the target budget. The rows
are not measurements of an attack, and three of the five rest on assumptions (A-F1, A-F2, and the
proof system's soundness) rather than on theorems about a deployed object.

---

## 1. The accounting, and where each constant comes from

| Constant | Value | Where it comes from |
|---|---|---|
| gate cost of one primitive evaluation | ≥ 2^18 gates per hash or key-map evaluation | QPT-128 D1 (domain 06, v1.43 conventions) — project decision, not a literature constant |
| adversary budget | G = 2^128 gates | D2 |
| target | success probability ≤ G·2^−130, i.e. `log₂(Pr/G) ≤ −130` | D2; the ledger's margin column is `total − (−130)` |
| targets for the framing row | 64 · 2^10 (p ≤ 64 keys × 2^10 domains) | the profile's registry shape |
| search bound | `8(q+1)²/2^256`, q = G/2^18 | HRS16 (ePrint 2015/1256), the standard multi-target Grover-with-classical-search bound |
| binding / collision | `8(t_B/2^18 + 1)²/2^512`, expansion E = 512 | A-F2; E is a design choice swept below |
| extraction charge | `t_B = G + q²·2^12` | DFMS22 Theorem 4.2 (binding row) with the v1.43 **L5** accounting for the online QROM extractor |
| MAC field | λ = 256 | the proof system's field |
| QuickSilver degree | d_QS = 6 | R_B's circuit (key map degree 2 composed with the degree-3 derivation of s) |
| committed bits | ℓ = 13,760, ℓ̂ = 15,296 (> 2^13) | 43 seats × 320 bits plus masks; the > 2^13 condition is FAEST v2 Lemma 9.34's |
| last-challenge entropy | λ′ = τ·b + w_g, required ≥ **230** | FAEST v2 Lemma 9.39 form; this is what fixes τ per b |
| simulation | ε_sim = (3q_s/2)·√((q_H+q_s+1)·2^−512), 2^64 certificates | GHHM21 Theorem 3 |
| false positive | seat-present-in-one-certificate coincidence, `2^64·42·43/2^256`, plus the rarer key-coincidence path `2^64·64·43²·4/2^1024` | v1.52 correction; information-theoretic, driven by the **handle** width |

---

## 2. The five rows, as the executable computes them

At the settings (log₂ parties, w_g, τ) = (32, 32, 7) — the settings whose certificate fits 32 KiB:

| Row | log₂ Pr/G at 2^128 gates | Meaning | Status |
|---|---:|---|---|
| **R1** framing (public pair search, tight) | −145.0 | Theorem 1; the reduction is tight because the evidence is recovered from the certificate bytes, exactly as in B0 | theorem-backed |
| **R2** evasion (linear-trick collision, extraction charged) | −209.0 | Theorem 2's ε_bind, with E = 512 | theorem-backed, given A-F2 |
| **R3** proof soundness | −159.7 (DFMS-modelled) / −157.9 (FAEST-9.39 form at τ·b + w_g = 256) | the backend's obligation | **modelled** |
| **R4** simulation | −159.415037499… | GHHM21 Theorem 3 | theorem-backed for the simulator |
| **R5** pair-search false positive | −181.18141782251917 | handle coincidence; corrected in v1.52 | information-theoretic, from a measured law |

**The R3 caveat, stated as the package requires.** In its default form the ledger's R3 row is
modelled with DFMS22 and **omits the DFM20 multi-round loss**. Only the alternative row computed from
the FAEST v2 Lemma 9.39 form (`faest_qrom_R3_variant`) carries the multi-round loss. A reader must not
read the default total as if the loss were included.

Every row's totals over the settings the file sweeps:

| log₂ parties | w_g | τ | certificate | fits 32 KiB | total log₂ Pr/G | D2 margin |
|---:|---:|---:|---:|---|---:|---:|
| 24 | 16 | 9 | 37,646 B | no | −135.676 | 5.676 |
| 24 | 32 | 9 | 37,134 B | no | −144.986 | 14.986 |
| 32 | 16 | 7 | 31,322 B | **yes** | −143.193 | 13.193 |
| 32 | 32 | 7 | 30,810 B | **yes** | −145.0 | **15.0** |
| 40 | 32 | 5 | 23,462 B | yes | −135.676 | 5.676 |

and under the FAEST-9.39 form of R3 (`τ·b + w_g ≥ 230`):

| log₂ parties | w_g | τ | τ·b + w_g | total log₂ Pr/G | D2 margin |
|---:|---:|---:|---:|---:|---:|
| 16 | 16 | 14 | 240 | −141.541 | 11.541 |
| 20 | 16 | 11 | 236 | −137.669 | **7.669** |
| 24 | 16 | 9 | 232 | −133.678 | 3.678 |
| 20 | 32 | 10 | 232 | −133.678 | 3.678 |
| 32 | 32 | 7 | 256 | −145.0 | 15.0 |

**Read this table honestly.** The production setting the security document uses, (2^20, τ = 11,
w_g = 16), carries a margin of **7.669 bits** under the form of R3 that includes the multi-round
loss. That is thin. It is also the only setting for which a prover was executed — at *reduced*
parameters, never at production parameters (see
[prover-and-sanitizers.md](prover-and-sanitizers.md)). The fitted-exponent extrapolations elsewhere
in the programme carry ±4–38 bits of error, so the 128-bit conclusions rest on the reductions, not on
the fits.

---

## 3. The sweeps

**Expansion (R2).** log₂ Pr/G for E ∈ {300, 400, 430, 512, 600} = {3.0, −97.0, −127.0, −209.0,
−297.0}. The row is *positive* at E = 300: at that expansion the linear-trick collision is cheaper
than the budget allows, which is why E = 512 is the ledger's setting and why expansion is a security
parameter and not a size knob.

**Domains per epoch (R1).** log₂ Pr/G for T ∈ {1, 1024, 65,536, 1,048,576} = {−155.0, −145.0, −139.0,
−135.0}. The framing row degrades by 1 bit per doubling of the domain count — the registry cost row
in [validation-status.md](validation-status.md) states the same fact as an operational limit: the
framing row **fails above 2^24 domains per epoch**.

**Comparison with Mode S (v1.43).** The ledger prints why Mode B can keep 256-bit credentials where
Mode S needed 512-bit ones for the search row: B0's public-evidence reduction applies because the
evidence is recovered publicly here too. That is the whole reason the hidden-signer profile becomes
sizing-feasible at all.

---

## 4. What the ledger does not cover

- It does not cover the **collaborative prover**, which does not exist
  ([collaborative-prover.md](collaborative-prover.md)); A-Prove is a premise of the rows, not a cost
  in them.
- It does not price a **dedicated cryptanalysis** of the expanding random MQ key map + power handle;
  the attack rows use the semi-regularity heuristic.
- It does not certify the **selector parity gap** (see [validation-status.md](validation-status.md)).
- It is a model of an adversary in the QROM, not a simulation of one: no attack was executed at the
  ledger's settings, and none is claimed.
