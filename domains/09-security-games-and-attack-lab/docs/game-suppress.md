# GAME 2 — SUPPRESS

*Definition in the harness:* `GAME_SUPPRESS` in `src/ceqs_games.py`; measured by `game_suppress()`.
*Recorded write-up:* `results/attack-lab-results.md` §12.2. *Structural lemma:* §6.2 of the same
record, and §5 below.

---

## 1. The game

```
SUPPRESS(cfg, d, F, registry, H)

Attacker receives     the public parameters; the registry; the challenge derivation H; the
                      freedom to choose both conflicting messages.
Does not receive      any opening (s, r).

Oracle                evaluations of the public challenge derivation H(cfg, d, ·), counted
                      as Q.

Wins if               it finds m0 != m1 in one domain d whose challenge maps are EQUAL, so
                      the difference map D is identically zero and the extractor cannot
                      solve for s — extraction returns nothing and a real equivocation
                      goes unpunished.
```

The attacker is not asked to invert anything. It has to make two messages *agree* on the challenge
— a collision, not a preimage — which is why the cost is governed by the challenge **output
length** and not by its difficulty as a function.

## 2. The property claimed

**Accountability**: extraction always names the seats that double-signed, so a conflict can never be
silenced. The property is what makes the construction's "extract, don't identify" design meaningful;
without it, equivocation is free.

The two revisions play the same game with different output lengths:

| revision | challenge | output length `h` |
|---|---|---:|
| v1.46 (superseded) | a single `c`; `D(s) = (c₀ ⊕ c₁)·s` | `h = 256` at production |
| v1.50 (deployed) | the triple `(c_a, c_b, c_c)`; `D(s) = αs ⊕ βs² ⊕ γs⁴` | `h = 768` at production |

At toy widths `h = n` and `h = 3n` respectively.

## 3. Status of the argument

| part | status | where |
|---|---|---|
| the structural claim (only a full collision suppresses extraction; partial ones do not) | **elementary proof**, by the linearized-polynomial kernel lemma | §5 below |
| the kernel dimension ≤ 2 in practice | **measurement** (3,000 triples at each of `n = 16, 17`) | §5 below |
| the cost of a full collision, at toy sizes | **measurement**, 10 points, one fitted law | §4 below |
| the cost at production | **transplanted estimate**: classical birthday, and the project's CFHL bound for the quantum side | §6 below |
| the switch from `h = 256` to `h = 768` removing the attack | **measurement of the before/after behaviours**, plus the bound | §6 below |
| privacy (that the handle leaks nothing) | **not claimed here**; A-P is domain 08's, and remains decisional | `docs/validation-status.md` |

The security-relevant claim this document supports: *the only way to silence extraction is a
collision on the whole challenge, the fix moved that collision from 256 to 768 bits, and the
measured cost of collisions follows the birthday law on the real challenge derivation.*

## 4. Measured results

**Method.** Birthday search over messages: draw messages, compute the challenge, keep every triple
seen, and stop at the first repeat. Count messages tried as `Q`. Fixed seeds.

**Parameters.** v1.46: `n = 8, 10, 11, 13, 14, 16, 17` with 12 samples per point. v1.50:
`n = 8, 10, 11` (so `h = 24, 30, 33`) with 6, 4 and 2 samples respectively; search cap 4,000,000
messages.

| scheme | `h` | 8 | 10 | 11 | 13 | 14 | 16 | 17 | 24 | 30 | 33 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1.46 | `h = n` | 16.0 | 35.0 | 50.7 | 126.0 | 186.4 | 272.0 | 362.5 | | | |
| v1.50 | `h = 3n` | | | | | | | | 2,049.7 | 14,437.8 | 71,289.0 |
| birthday theory `√(π/2·2^h)` | | 20.1 | 40.1 | 56.7 | 113.4 | 160.4 | 320.8 | 453.7 | 5,133.6 | 41,068.6 | 116,159.5 |

**Pooled fit: `log₂ Q = 0.4498·h + 0.767`** (birthday theory `0.5·h + 0.326`).

The claim the fit is meant to support is that **one** birthday law covers both schemes — that the fix
did not invent a new hardness but moved `h` from 256 to 768. The support is the shared slope, and the
intercepts, which differ by 0.44 bits from theory.

### 4.1 What the pooled slope is measuring — a decomposition the record does not give

The fitted slope is **below** the theoretical 0.5, and the record attributes the resulting
extrapolation error to fitting over a limited range and extending it. Fitting the two clusters
separately shows where the deficit comes from:

| points fitted | slope | intercept | production estimate | exact | error |
|---|---:|---:|---:|---:|---:|
| v1.46 cluster only (7 points, `h = 8…17`) | 0.5078 | 0.101 | `2^130.1` at `h = 256` | `2^128.3` | **+1.8 bits** |
| v1.50 cluster only (3 points, `h = 24…33`) | 0.5547 | −2.439 | `2^423.6` at `h = 768` | `2^384.3` | **+39.3 bits** |
| pooled (10 points, `h = 8…33`) | 0.4498 | 0.767 | `2^346.2` at `h = 768` | `2^384.3` | **−38.1 bits** |

Three facts follow, and none of them is in the record:

1. **Every one of the three v1.50 points lies below the birthday curve at its own `h`** — 2,049.7
   against 5,133.6 (−1.3 bits), 14,437.8 against 41,068.6 (−1.5 bits), 71,289.0 against 116,159.5
   (−0.7 bits). The pooled line is therefore pivoted downward by the join between the clusters, and
   the reported `−38.1` bits of "extrapolation error" is mostly a **pooling artefact**, not evidence
   that the birthday law degrades at large `h`. The exact birthday value at `h = 768` is not in
   question; only the fitted line is.
2. **The single-scheme fits are not usable either.** The v1.50 cluster has three points, so its own
   slope (0.5547) is unstable and overshoots by 39 bits; the v1.46 cluster's slope (0.5078) is
   closer, but it is fitted over a range whose largest point is `h = 17` and is then used at 256.
3. **The harness does not distinguish the two explanations for the low v1.50 points.** They could be
   small-sample underestimates — the samples are 6, 4 and 2 of a heavily right-skewed law, and a
   sample mean understates the mean with high probability — or there could be a structural reason
   (a smaller effective output space in the toy triple derivation). The harness computes no
   confidence intervals, so it cannot tell these apart, and the point at `h = 33` rests on **two
   samples**.

That last point is the honest summary: the SUPPRESS measurement establishes that collisions cost
about `2^(h/2)` on the real challenge derivation, and it does **not** pin the constant. The 128-bit
conclusion does not use the fit at all — it uses the collision length and the reductions
(`docs/validation-status.md` §3).

## 5. Why partial collisions are useless — the kernel lemma

The extractor solves

```
D(s) = Z0 ⊕ Z1,   D(s) = α·s ⊕ β·s² ⊕ γ·s⁴  over GF(2^256),
```

with `α, β, γ` the coefficient-wise differences of the two challenge triples. `D` is a **linearized
(2-)polynomial** of 2-degree ≤ 2: a linear map over `GF(2)` in disguise, so its kernel is an
`𝔽₂`-subspace of dimension ≤ 2 and `D` has at most **4** roots. Therefore:

- whenever `(α, β, γ) ≠ 0`, the solve returns at most 4 candidate openings, each filtered by the
  registry lookup — extraction works;
- extraction is suppressed **only** when `D ≡ 0`, i.e. **all three coefficients collide**.

This is what justifies the extractor's `max_free = 2` cap: the cap is a limit on a subspace whose
dimension is provably at most 2, not a heuristic.

**Measured.** Over 3,000 random nonzero triples at each of `n = 16` and `n = 17`: the kernel
dimension never exceeded 2, with the distribution ≈ 33 % / 50 % / 16 % for dimensions 0 / 1 / 2.
Constructed partial collisions behave exactly as the lemma predicts:

| collision | kernel dimension | candidates | extraction |
|---|---:|---:|---|
| `c_a` only | 1 | ≤ 2 | works |
| `c_a` and `c_b` | 0 | 1 | works |
| all three | — (`D ≡ 0`) | — | suppressed |

**The assumption this rests on:** the field is `GF(2^256)` and `s ↦ s^(2^i)` is `𝔽₂`-linear there —
i.e. the arithmetic is characteristic 2 and the coefficient differences are taken in the same field.
Both hold by construction. What the lemma does *not* need is any assumption about `H`: it constrains
the extractor's algebra, not the challenge derivation's randomness.

## 6. The before/after demonstration, and the transplant

**Run for real** (`src/ceqs_attack_lab.py`, Experiment E; `docs/attack-lab.md` §5): against the v1.46
handle a challenge collision was found after **234 messages** (birthday on 14 bits) and extraction
**failed with "inverse of zero"**, naming nobody. Against the v1.50 handle, a collision on the
**first coefficient only**, found after **172 messages**, left extraction working: it **named all 22
seats**. A collision that destroys the old handle is harmless against the new one.

**The production costs** come from a transplanted bound, not from this measurement:

| | v1.46: 256-bit challenge | v1.50: 768-bit triple |
|---|---:|---:|
| classical birthday | `2^128` | `2^384` |
| quantum queries (the project's CFHL bound, advantage 1/3) | **`2^81.7`** | **`2^252.4`** |
| in gate units at `2^18` gates/query | **`2^99.7`** | **`2^270.4`** |
| against the `2^128` gate budget | **broken by 28 bits** | safe by 142 bits |

`docs/games-methodology.md` §5.3 states the provenance: the citation names the theorem
(Chung–Fehr–Huang–Liao, EUROCRYPT 2021, Theorem 5.29) and no more — no title, no page — and the four
numbers are **constants transcribed from a solve performed with domain 06's checker**, not computed
by this harness. This build re-derived them from that checker and reproduced them exactly
(`VERIFICATION.md`). A reader who distrusts the bound must check domain 06, not this domain.

**The correction the record carries in the open.** An earlier draft said suppressing v1.50 costs
`2^768`, treating three 256-bit coefficients as three independent preimage searches. It is a
**collision** on a 768-bit output: the attacker makes two messages agree, it does not find specified
values. `docs/attack-lab.md` §5 repeats the correction rather than quietly using the corrected
figure, and the rounded `2^768` appears nowhere in this domain's documentation as a cost.

## 7. Tests

`test_suppress_law_holds_for_both_schemes` asserts that the two schemes' fits **share a slope** near
`0.5` and that their intercepts differ by less than 1 bit. That is the claim of §4 — one law, two
output lengths. It deliberately does not assert the pooled slope's value or the production
extrapolation, both of which §4.1 shows to be artefacts of fitting a line through two clusters.

Observed: pass (`--self-test`, 4 tests OK).

## 8. Cost of a run

The most expensive game in wall-clock terms after EVADE: `game_suppress()` performs 10 birthday
searches, the largest capped at 4,000,000 messages. In `--all` (148.19 s wall) it is a substantial
fraction.

```
cd domains/09-security-games-and-attack-lab/src
python3 ceqs_games.py --suppress
python3 ceqs_games.py --suppress --json
```

## 9. What would falsify this, and open items

- **A partial collision that suppresses extraction.** Would refute the kernel lemma as used, or show
  the extractor's implementation differs from the lemma. Checked by construction at three collision
  shapes and by 6,000 sampled triples; not proved about the implementation by a machine-checked
  proof.
- **A collision cost materially below `2^(h/2)`** — a structural weakness in the challenge
  derivation. The measurements cannot detect this: the v1.50 points already sit 0.7–1.5 bits below
  theory and are too few to tell a fluctuation from a signal (§4.1).
- **`h` not being what the code says.** The whole argument is that the fix moved the collision target
  from 256 to 768 bits. The harness verifies the *behaviour* (a first-coefficient collision is
  survived) but takes the challenge length from the implementation rather than measuring the entropy
  of the derivation. Not measured here: whether `H`'s 768-bit output is uniform enough for the
  collision bound to apply. That is an assumption of both this domain and domain 06's bound.
- **Quantum side.** No quantum collision search is simulated. The `2^81.7` / `2^252.4` rows are the
  bound's arithmetic; a tighter or looser collision bound would move them, and would move the
  "broken by 28 bits / safe by 142 bits" verdict for the v1.46 row. It would not move the structural
  conclusion, nor any measured quantity here.
