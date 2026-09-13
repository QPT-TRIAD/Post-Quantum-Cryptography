# CE-QS — empirical testing of the system (v1.51)

**Date:** 11 September 2026
**Harness:** `ceqs_attack_lab_v1.51.py` (5 self-tests; `--all` reproduces §2–§9) and `ceqs_games_v1.52.py` (4 self-tests; `--all` reproduces §12)
**System under test:** B0 (`sidecar_free_certificate_v1.44.py`) and Mode B (`hidden_signer_modeB_v1.50.py`, `modeB_prover_v1.50.c`).

> **Scope note.** The construction in the original report — SLH-DSA/ML-DSA inside the proof, QLWR traces, "Adv < 2^−128 against every QPT adversary" — was refuted and replaced (`qpt128_finalization_v1.43.py`, Lemma L1: 2^63 Grover iterations already exceed 2^−128 against any 256-bit secret). There is nothing left to test there. What follows tests the constructions that replaced it.

---

## 0. What testing can and cannot establish

| | |
|---|---|
| **Can** | Run the real implementation through violation attempts and count successes (must be 0). Build deliberately weak parameter sets and measure how the *real* attacks scale on them. Simulate Grover **exactly** on the real oracle at those sizes. Compare measured exponents with the ledger's predictions. |
| **Cannot** | Establish 128-bit quantum security. No simulation can. The quantum rows below are the proven Grover/BHT bounds evaluated at a marked-set density **measured on the real function**; the other half of the claim is the reduction (`modeB_security_v1.49.md`). |

Every experiment below uses **deliberately weak** parameters (8–14-bit openings, expansion 2–12). No result here is a security claim for the production parameters (256-bit openings, expansion 512).

---

## 1. Test suites (regression)

All 14 suites in the project, re-run together:

| Suite | Tests | Suite | Tests |
|---|---:|---|---:|
| `qpt128_finalization_v1.43` | 19 | `ceqs29_extractor_v1.34` | 20 |
| `sidecar_free_certificate_v1.44` (B0) | 39 | `joint_extractor_lift_v1.35` | 16 |
| `hidden_signer_modeA_v1.45` | 8 | `circuit_witness_extractor_v1.36` | 27 |
| `hidden_signer_modeB_v1.46` | 12 | `signature_security_reduction_v1.37` | 23 |
| `modeB_rigorous_ledger_v1.47` | 6 | `slh_dsa_signature_reduction_v1.38` | 36 |
| `modeB_voleith_toy_v1.48` | 7 | `signature_margin_sweep_v1.39` | 13 |
| `hidden_signer_modeB_v1.50` | 5 | `phase_ghz_security_check_v1.40` | 12 |
| `ceqs_attack_lab_v1.51` | 5 | | |

**248 tests, all pass.**

---

## 2. Experiment A — violation attempts (the "zero successful violations" gate)

24 attempts against the real Mode B v1.50 implementation at n = 14, expansion 8, 64 seats, quorum 43. Each must be rejected; the last row is a positive control that must *succeed*.

| Category | Attempts | Result |
|---|---:|---|
| Forged / invalid witness: altered opening, unregistered credential, opening claimed under another seat, duplicate validator, witness replayed under another message, witness replayed in another domain, fewer than 43 rows | 7 | all rejected |
| Malformed encoding: handles out of canonical order, duplicate handle, truncated frame, trailing bytes, wrong magic, wrong version, wrong suite, quorum count below 43, non-64-byte message, duplicate registration | 10 | all rejected |
| Extraction preconditions: replay of the same certificate, equal messages, conflict across domains, certificate from another registry | 4 | all rejected |
| Accountability: framing an honest seat, fabricated blame | 2 | both fail as intended |
| **Positive control:** honest conflict | 1 | 22 seats extracted, every blame verifies |

**Successful violations: 0 of 24.** Each rejection is reported with the reason the implementation gave (e.g. `handle is not r^7 XOR L_c(s)`, `handles must be strictly increasing`, `configuration mismatch`).

---

## 3. Experiment B — framing: how the real search space scales

For each n the lab **enumerates the entire candidate space** of the real key map and counts the marked set M (candidates that satisfy both the registry key and the published handle), for 6 targets per point.

| n | handle | space | M (every target) | measured mean classical cost | predicted 2^(n−1) |
|---:|---|---:|---:|---:|---:|
| 8 | r⁷ / linear | 2^8 | 1 | 88 | 128 |
| 10 | r⁷ / linear | 2^10 | 1 | 580 | 512 |
| 11 | r⁷ / linear | 2^11 | 1 | 968 | 1,024 |
| 13 | r⁷ / linear | 2^13 | 1 | 4,702 | 4,096 |
| 14 | r⁷ / linear | 2^14 | 1 | 9,358 | 8,192 |

- **M = 1 exactly, in all 60 target-instances.** The real key map admits no spurious opening consistent with the handle, so there is no shortcut below exhaustive search over the space. This is the fact the ledger's framing row depends on.
- The classical-cost column is the position of the true opening in the enumeration — uniform on [1, 2^n], so its mean estimates 2^(n−1) with a wide error bar at 6 samples. Fitted slope **1.107 bits per bit** (predicted 1.0).
- The r⁷ and linear handles give identical M. That matches the independent cryptanalysis (the SAT slopes show no r⁷-over-linear advantage); the r⁷ ranking rests on the XL model, and **the generic bound is the same for both**.

### 3.1 Control — what the handle costs the defender

At n = 8, enumerating the **joint** (s, r) space without a published handle:

| setting | space | M |
|---|---:|---:|
| no handle | 2^16 | 1 |
| with handle | 2^8 | 1 |

Publishing a handle collapses the attacker's search from 2^(2n) to 2^n: guess r, derive s, test F. This is exactly the generic attack the ledger charges — and why the production framing bound is 2^(256/2) = **2^128 quantum**, not 2^256.

---

## 4. Experiment C — exact Grover simulation on the real oracle

State-vector simulation (numpy). The oracle is the real key map plus handle: a candidate r is marked iff it opens the target registry key. This simulates the *algorithm* exactly; it does not model the gate cost of building the oracle circuit.

| n | N = 2^n | M | measured optimal iterations | predicted | (π/4)√(N/M) | success at optimum | max \|sim − theory\| |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 256 | 1 | 12 | 12 | 12.6 | 0.9999 | 4.4 × 10⁻¹⁵ |
| 10 | 1,024 | 1 | 25 | 25 | 25.1 | 0.9995 | 5.3 × 10⁻¹⁵ |
| 11 | 2,048 | 1 | 35 | 35 | 35.5 | 1.0000 | 3.2 × 10⁻¹⁵ |
| 13 | 8,192 | 1 | 71 | 71 | 71.1 | 0.9999 | 2.6 × 10⁻¹⁵ |

The simulated success probability tracks sin²((2k+1)·arcsin√(M/N)) to double-precision noise at **every** iteration, and the measured optimal iteration count equals the predicted one exactly. Fitted slope of log₂(iterations) against n: **0.512** (predicted 0.5).

Extrapolating the verified law to production: n = 256, M = 1 → (π/4)·2^128 ≈ **2^128 iterations**. That is the framing row of the ledger, now resting on a measured M and a verified iteration law rather than on the formula alone.

---

## 5. Experiment D — binding: the real collision attack

The lab runs the actual linear-trick attack on the real key map: pick δ, solve the linear system F(x⊕δ) ⊕ F(x) = 0, keep the first consistent δ. 8 trials per point, N = 16 unknowns.

| expansion E | measured mean δ's tried | log₂ | naive prediction 2^E |
|---:|---:|---:|---:|
| 2 | 12 | 3.57 | 4 |
| 4 | 24 | 4.60 | 16 |
| 6 | 140 | 7.13 | 64 |
| 8 | 450 | 8.81 | 256 |
| 10 | 1,988 | 10.96 | 1,024 |
| 12 | 15,560 | 13.93 | 4,096 |

Fitted slope **1.037 bits per expansion bit** (predicted 1.0). The measured cost sits about **+1.2 bits above** 2^E, which is explained: δ always lies in the kernel of A_δ, so rank(A_δ) ≤ N−1 and the consistency probability is ≈ 2^−(E+1), not 2^−E. **The ledger's 2^−E density is therefore conservative** — it credits the attacker with roughly twice the success rate the real attack achieves.

Quantum: Grover over δ at the measured density gives 2^(E/2); at the production expansion E = 512 that is **2^256**, the ledger's binding row.

---

## 6. Experiment E — the attack found by the independent pass, before and after the fix

The v1.49 cryptanalysis found that with the v1.46 handle Z = r⁷ ⊕ c·s, two messages whose challenges collide make extraction divide by zero and name nobody. Reproduced at n = 14:

| | v1.46 handle (single challenge) | v1.50 handle (linearized) |
|---|---|---|
| collision found after | 234 messages (birthday on 14 bits) | 172 messages, on the **first coefficient only** |
| coefficients equal | c collides ⇒ attack | c_a equal, **c_b and c_c differ** |
| extraction result | **FAILED: "inverse of zero"** — nobody named | **named all 22 seats** |
| work to suppress | collision on a 256-bit challenge | collision on the whole 768-bit triple |

The fix is confirmed empirically: a collision that destroys the old handle is harmless against the new one, and costs nothing in certificate size.

### 6.1 Correction — this is a collision game, not a 768-bit search

An earlier draft of this file said suppressing v1.50 costs "2^768". **That was wrong**: it treated three 256-bit coefficients as three independent preimage searches. The adversary does not have to *find* the coefficients — it has to make two messages *agree* on them, which is a collision on a 768-bit output. The correct costs, using the project's own CFHL collision bound (`qpt128_finalization_v1.43.py:cfhl_collision`, solved for advantage 1/3):

| | v1.46: 256-bit challenge | v1.50: 768-bit triple |
|---|---:|---:|
| classical birthday | 2^128 | 2^384 |
| quantum queries (CFHL bound) | **2^81.7** | **2^252.4** |
| in gate units at 2^18 gates/query | **2^99.7** | **2^270.4** |
| against the 2^128 gate budget | **BROKEN by 28 bits** | safe by 142 bits |

So the fix moved this row from 28 bits *inside* the budget to 142 bits outside it. The correct headline is "a 768-bit collision", never "2^768".

### 6.2 Why partial collisions are useless — the kernel is provably small

The extractor solves D(s) = Z₀ ⊕ Z₁ where D(s) = αs ⊕ βs² ⊕ γs⁴, with α, β, γ the differences of the two challenge triples. D is a **linearized (2-)polynomial** of 2-degree ≤ 2 over GF(2^256): it has at most 4 roots, and they form an 𝔽₂-subspace of dimension ≤ 2. Therefore:

- whenever (α, β, γ) ≠ 0, the solve returns **at most 4 candidate openings**, each filtered by the registry lookup — extraction works;
- extraction is suppressed **only** when D ≡ 0, i.e. all three coefficients collide.

This is what justifies the extractor's `max_free = 2` cap. Measured over 3,000 random nonzero triples at each of n = 16 and 17: kernel dimension never exceeded 2 (distribution ≈ 33% / 50% / 16% for dimensions 0 / 1 / 2). Constructed partial collisions behave as the lemma predicts:

| collision | kernel dim | candidates | extraction |
|---|---:|---:|---|
| c_a only | 1 | ≤ 2 | works |
| c_a and c_b | 0 | 1 | works |
| all three | — | D ≡ 0 | suppressed |

---

## 7. Ledger — measured against predicted

| Quantity | Measured (toy) | Predicted | Extrapolation to production |
|---|---:|---:|---|
| Framing, classical | slope 1.107 | 1.0 | 2^255 |
| Framing, quantum (Grover iterations) | slope 0.512 | 0.5 | **2^128** |
| Binding collision, classical | slope 1.037 | 1.0 | 2^512 |
| Binding collision, quantum | — (density measured) | — | 2^256 |
| Marked set M, framing | 1 (60/60 instances) | 1 | 1 |
| Grover law, deviation | ≤ 5.3 × 10⁻¹⁵ | 0 | — |

Production ledger rows they feed (`modeB_rigorous_ledger_v1.47.py`, gate units, log₂ Pr/G at 2^128 gates): R1 framing −145.0, R2 binding −209.0, R3 proof soundness −138.1, R4 simulation −159.4, R5 false positive **−181.2** (corrected in v1.52, §12.5 — it was −943); **total −137.7, D2 margin 7.7 bits**.

---

## 8. Implementation runs (production parameters)

`modeB_prover_v1.50.c`, GF(2^256), 1,024-equation key map, degree-6 QuickSilver:

| Trees | τ | w_g | τ·b + w_g | Certificate | Fits 32 KiB | Verified | Extracted | Prove | Verify |
|---:|---:|---:|---:|---:|---|---|---:|---:|---:|
| 2^20 | 11 | 16 | 236 | **30,684 B** | yes | both, tampering rejected | 22 | 60 s | 56 s |
| 2^22 | 10 | 16 | 236 | **28,708 B** | yes | both, tampering rejected | 22 | 219 s | 195 s |
| 2^12 | 20 | 8 | 248 | 49,108 B | no | both, tampering rejected | 22 | 2.4 s | 1.1 s |

Both production-valid settings clear the ledger's τ·b + w_g ≥ 230 requirement and fit 32 KiB. They bracket the trade-off: doubling the tree depth removes one repetition, which shaves **1,976 bytes** off the certificate but costs **3.6× the prover time** (tree expansion is τ·2^b leaves, each expanded to ℓ̂ bits). Extraction is unaffected (1.9 s both).

---

## 9. A toy-size artifact, measured and understood

At toy handle widths, 43 handles collide by birthday and the implementation **refuses to encode** an ambiguous certificate (correct behaviour). Measured rate over 300 trials vs 1 − exp(−43·42/2/2^n):

| n | 11 | 13 | 14 | 16 | 17 | 256 |
|---|---:|---:|---:|---:|---:|---:|
| measured | 0.370 | 0.100 | 0.067 | 0.017 | 0.003 | — |
| predicted | 0.357 | 0.104 | 0.054 | 0.014 | 0.007 | 7.8 × 10⁻⁷⁵ |

The harness redraws openings when this happens; at production width it is impossible in practice.

---

## 10. What is still not established by testing

- **No security level is proven here.** The measured slopes confirm the *scaling laws* the ledger assumes; the ledger's absolute rows depend on the reductions in `modeB_security_v1.49.md` and on the named assumptions A-F1, A-F2, A-P, A-Prove, A-Reg, A-QROM.
- **The proof system's QROM soundness row is transplanted** from FAEST v2 Lemma 9.39, not re-derived for this relation.
- **Gate costs are not simulated.** Experiment C counts oracle *invocations*; the circuit cost of the oracle is charged separately in the ledger (≥ 2^18 gates per evaluation).
- **A-P (privacy) remains decisional.** The independent pass found no distinguisher below search, but that is evidence, not a reduction.
- **The trusted-aggregator premise (A-Prove) is untested** — it is a protocol assumption, not a property of these artefacts.

---

## 11. Reproduce

```
python3 ceqs_attack_lab_v1.51.py --self-test   # 5 tests
python3 ceqs_attack_lab_v1.51.py --all         # every number above, ~5 min
python3 ceqs_attack_lab_v1.51.py --negative    # experiment A only
python3 ceqs_attack_lab_v1.51.py --grover      # experiment C only
```

| File | sha256 |
|---|---|
| `ceqs_attack_lab_v1.51.py` (5 tests) | `78c9b204c10fd1db6bf1958d600950cc673e254487d3cd5615e7bfd62df96b31` |
| `ceqs_games_v1.52.py` (4 tests) | `885bbfe705dd62f3b21640450c3a72410b853872b9698da57cc10c1d0879f62e` |
| `attack_lab_results_v1.51.md` | (this file) |
| `hidden_signer_modeB_v1.50.py` | `e094a605f4e5ffa8b70f71f178c415ad64b23b315c0a44c26f477ec1dcc82bf1` |
| `modeB_prover_v1.50.c` | `ff8e5cd9f5c84cde3d0ac6e654b7bfc5a26e21b7331b8098649b36f0fe6adb92` |
| `modeB_rigorous_ledger_v1.47.py` (7 tests) | `074f06454a4aaf11d4a801683194485211cc0bc4c31bf2433195ab3de96541ac` |
| `sidecar_free_certificate_v1.44.py` | `a30f1078ffee7f395bbd82a1b7b9a37f9c5518a71e63a4d5a85b0446146e68a8` |
| `qpt128_finalization_v1.43.py` | `2762b2c2880ea514dceb60a5fe344327f5eb2c546e9e40be6b2fcb7fe4156bb4` |

---

## 12. Security games with measured query complexity (v1.52)

`ceqs_attack_lab_v1.51.py` answers "did any attack succeed?". That is the weaker question. `ceqs_games_v1.52.py` states each attack as a **game** first, then measures the attacker's query complexity Q as a function of the parameter, fits an exponent, and compares it with theory:

```
GAME -> attacker's information -> allowed oracle queries -> winning condition
     -> attack algorithm -> measured Q(n) -> fitted exponent -> theoretical bound
```

Three of the four games are **winnable at toy parameters** — a game nobody can win teaches nothing about its exponent.

### 12.1 FRAME — recover an honest opening and name that seat

*Attacker receives:* public parameters, the full registry, a certificate and all 43 handles, the target seat's handle. *Does not receive:* any opening. *Oracle:* evaluations of the public key map F, counted. *Wins if:* it outputs (s′, r′) with F(s′‖r′) = Y[d][i*], which lets it place a handle for i* in a conflicting certificate so extraction names i*.

| n | 8 | 10 | 11 | 13 | 14 |
|---|---:|---:|---:|---:|---:|
| measured mean Q | 144.7 | 664.8 | 1,153.3 | 4,942.5 | 10,414.0 |
| theory 2^(n−1) | 128 | 512 | 1,024 | 4,096 | 8,192 |

**Fit: log₂ Q = 1.0178·n − 0.931** (theory 1.0·n − 1.0). The winning condition was then demonstrated end to end: using a recovered opening the harness manufactures the victim's handle for a message it never authorized, and extraction **names the victim**. So the game's difficulty is exactly the search cost measured above.

### 12.2 SUPPRESS — silence extraction by a challenge collision

*Wins if:* it finds m₀ ≠ m₁ in one domain whose challenge maps are equal, so the difference map D ≡ 0 and the extractor cannot solve for s. This is the flaw the independent pass found in v1.46. Both schemes play the **same game on different output lengths**: h = n for v1.46 (a single challenge), h = 3n for v1.50 (the triple).

| scheme | h | 8 | 10 | 11 | 13 | 14 | 16 | 17 | 24 | 30 | 33 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1.46 | h = n | 16.0 | 35.0 | 50.7 | 126.0 | 186.4 | 272.0 | 362.5 | | | |
| v1.50 | h = 3n | | | | | | | | 2,049.7 | 14,437.8 | 71,289.0 |

**Fit over both schemes: log₂ Q = 0.4498·h + 0.767** (birthday theory 0.5·h + 0.326). One law, two instantiations — the fix did not invent a new hardness, it moved h from 256 to 768.

### 12.3 EVADE — equivocate with 22 corrupt seats and hide the culprits

*Wins if:* both certificates satisfy the relation, the messages differ, the domain is the same, and extraction names fewer than 22 seats. *Attack:* open one corrupt registry key twice (the linear trick).

| E | 2 | 4 | 6 | 8 | 10 | 12 |
|---|---:|---:|---:|---:|---:|---:|
| measured mean δ trials | 7.0 | 21.5 | 61.5 | 453.2 | 1,322.0 | 8,217.0 |

**Fit: log₂ Q = 1.0242·E + 0.393** (theory slope 1.0). End-to-end consequence, run for real: with 22 corrupt double-signers and one of them represented by a second opening, **v1.50 names the other 21 and flags `complete = False`; v1.46 would have named nobody.** One evader costs exactly itself — which is the v1.49 item-2 fix, now a regression test.

### 12.4 SAFETY — equivocate at all with ≤ 21 corrupt seats

Each certificate needs 43 seats and an honest seat contributes to at most one message per domain, so 43 + 43 ≤ 64 + C, i.e. C ≥ 22. Tested exhaustively for C = 0…23:

| C | 0 … 21 | 22 | 23 |
|---|---|---|---|
| equivocation | **impossible** | possible | possible |
| extraction | — | names 22 genuine + 1 coincidence, **missed 0** | names 23 genuine, **missed 0** |

**Measured threshold 22 = the theoretical threshold.** No genuine double-signer was ever missed.

### 12.5 What the SAFETY game discovered — and a ledger correction

At C = 22 extraction named **23** seats, one of them not a double-signer. The cause is not a counting error. A seat present in exactly one certificate is named when its *would-be* handle under the other message coincides with one of the 43 handles published there: the pair then decodes to that seat's genuine opening, F matches, and `verify_blame` even re-verifies. It is a real, if astronomically unlikely, framing — and it is driven by the **handle width**, not the registry-key width.

Measured rate against the predicted 42·43/2ⁿ (42 = the seats present in exactly one certificate):

| n | 11 | 13 | 14 | 16 | 17 |
|---|---:|---:|---:|---:|---:|
| measured | 0.5767 | 0.2233 | 0.0900 | 0.0267 | 0.0100 |
| predicted | 0.8818 | 0.2205 | 0.1102 | 0.0276 | 0.0138 |

(The union bound loosens as the probability approaches 1, hence the gap at n = 11.)

**Ledger correction.** The R5 row modelled only a random candidate opening hitting a registry key, 2^64·64·43²/2^(2n+E) = −943. The dominant path is the handle coincidence: 2^64·42·43/2^256 → **R5 = −181.2**, about 760 bits larger. The row is nowhere near binding either way, so the total (−137.7) and the D2 margin (7.7 bits) are unchanged; `modeB_rigorous_ledger_v1.47.py` now computes both paths and asserts the corrected value.

### 12.6 The extrapolation caveat, measured

Fitting an exponent over n = 8…19 and extending it to n = 256 accumulates several bits of error — in both directions:

| game | fitted at production | exact theory | error |
|---|---:|---:|---:|
| FRAME (classical) | 2^259.6 | 2^255 | **+4.6 bits** |
| SUPPRESS at h = 256 | 2^115.9 | 2^128.3 | **−12.4 bits** |
| SUPPRESS at h = 768 | 2^346.2 | 2^384.3 | **−38.1 bits** |

This is why the 128-bit conclusions come from the reductions in `modeB_security_v1.49.md`, never from these fits. What the fits establish is that the reduced systems obey the laws those reductions assume — which is the strongest thing an experiment can say here.
