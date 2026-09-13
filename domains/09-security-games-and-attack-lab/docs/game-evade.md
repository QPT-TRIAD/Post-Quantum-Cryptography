# GAME 3 — EVADE

*Definition in the harness:* `GAME_EVADE` in `src/ceqs_games.py`; measured by `game_evade()` and
`_evade_consequence()`. *Recorded write-up:* `results/attack-lab-results.md` §12.3.

---

## 1. The game

```
EVADE(F, registry, d)

Attacker receives     the public parameters and registry; the openings of its own corrupt
                      seats; both certificates it is about to publish.
Does not receive      honest seats' openings.

Oracle                evaluations of F and linear solves; Q counts delta trials.

Wins if               both certificates satisfy the relation R_B, the messages differ, the
                      domain is the same, and extraction names FEWER THAN 22 seats — the
                      culprits escape, or are hidden by a seat that cannot be named.
```

This is the whole-system attack the construction exists to survive: the attacker really can
equivocate, because it holds 22 openings. The question is whether equivocation can be made
**unattributable**. Winning would mean extraction either names nobody (the v1.46 behaviour) or names
a set too small to be the culprits.

## 2. The property claimed

**Completeness of blame**: when a conflict exists, extraction names *every* double-signer among the
22-or-more seats common to the two quorums, so an evader costs exactly itself and cannot hide the
others.

The counterexample is a specific, historical defect, recorded as item 2 of the v1.49 cryptanalysis:
the old extractor **aborted** when it found fewer than 22 seats, so one seat whose handle pair
decoded to garbage took the other 21 culprits with it. The v1.50 extractor reports every seat it
identifies and sets a `complete` flag instead of aborting.

## 3. Status of the argument

| part | status | where |
|---|---|---|
| the defect existed in the v1.46/v1.49 extractor | **reproduction** (the abort behaviour is what the record documents) | `results/attack-lab-results.md` §12.3 |
| the fix removes it | **end-to-end regression**, run for real | §5 below |
| the cost of opening one registry key twice | **measurement**, 6 points, one fitted law | §4 below |
| the cost at production (`2^256` quantum) | **estimate** — the verified 0.5-slope iteration law applied to the measured density; not simulated | §4 below |
| the binding property as a whole | **assumption A-F2** in domain 08 (that the relation is binding on openings) | domain 08, `domains/08-hidden-signers/docs/mode-b-security.md` §2 |

EVADE is the game whose *scaling* is measured most cleanly, because the attack is a concrete
algorithm (the linear trick) with no appeal to a bound: what is measured is the real cost of a real
search on the real key map.

## 4. Measured results

**Method (the linear trick).** `F` is a quadratic map. For fixed `δ`, the map
`x ↦ F(x ⊕ δ) ⊕ F(x)` is **linear** in `x` (the quadratic terms cancel). So the attacker picks a
`δ`, solves the linear system `F(x ⊕ δ) ⊕ F(x) = 0`, and — if the system is consistent — obtains a
pair `x ≠ x ⊕ δ` with equal images, i.e. two openings of one registry key. `Q` counts `δ` trials.

**Parameters.** `N = 16` unknowns, 8 trials per expansion, cap 400,000 δ trials, seeds fixed
(`game/ev/<E>/<t>`).

| `E` | 2 | 4 | 6 | 8 | 10 | 12 |
|---|---:|---:|---:|---:|---:|---:|
| measured mean δ trials | 7.0 | 21.5 | 61.5 | 453.2 | 1,322.0 | 8,217.0 |
| `log₂` | 2.81 | 4.43 | 5.94 | 8.82 | 10.37 | 13.00 |
| naive prediction `2^E` | 4 | 16 | 64 | 256 | 1,024 | 4,096 |
| refined prediction `2^(E+1)` | 8 | 32 | 128 | 512 | 2,048 | 8,192 |

**Fit: `log₂ Q = 1.0242·E + 0.393`** against a theoretical slope of 1.0. At `E = 512` the fit gives
`2^524.8` against `2^512` exact — the fitted line is above theory here, which is the safe direction,
and is reported for the same reason the SUPPRESS extrapolation is (`games-methodology.md` §6.1).

**The +1.2-bit gap between measurement and `2^E` is explained, not tolerated.** `δ` always lies in
the kernel of the linear map `A_δ = F(· ⊕ δ) ⊕ F(·)`, since `F(δ ⊕ δ) ⊕ F(δ) = 0`; therefore
`rank(A_δ) ≤ N − 1` and the system is consistent with probability ≈ `2^−(E+1)`, not `2^−E`. The
measured means sit between `2^E` and `2^(E+1)`, exactly where that argument puts them.
**The ledger charges `2^−E`, so it credits the attacker with roughly twice the real success rate —
the ledger's binding row is conservative.** This is the one place in this domain where a measured
number corrects the analysis in the attacker's favour and the construction still wins.

**Quantum side.** Grover over `δ` at the measured density gives `2^(E/2)`; at `E = 512` that is
`2^256`. The harness applies the iteration law verified in `docs/attack-lab.md` §3; it does not
simulate a quantum search for `δ`, and it charges no gates.

## 5. The consequence, demonstrated end to end

`_evade_consequence()` builds both certificates for real, at `n = 14`, expansion 8, with exactly
`MIN_OVERLAP = 22` corrupt seats, and runs `m50.extract`:

- **v1.50 names the other 21 and flags `complete = False`.** The report's summary is
  `one evader costs exactly itself`.
- **v1.46 would have named nobody** — it aborted on finding fewer than 22 seats, so all 21 other
  culprits were hidden. That is the defect, and it is why this game exists.

**What the demonstration assumes, and it must be read with this in mind.** The second opening used
for the evading seat is a **fabricated opening** `(12345, 6789)`, not a genuine `F`-collision: a real
collision costs `2^E` work (Experiment D of the attack lab, and the scaling table above), which is
out of reach at `n = 14`. The code says so in a comment. So the two halves of the win condition are
measured separately:

- **obtaining** a second opening — measured, in the δ-trial table above;
- **the consequence of holding one** — demonstrated, with a placeholder that behaves to the
  extractor exactly as a genuine second opening would (a handle that does not decode to the seat's
  known opening).

The end-to-end attack is therefore not run as one continuous chain. Nothing in the construction makes
joining them hard, but this harness does not join them, and `docs/validation-status.md` records it as
an open item alongside the same gap in FRAME.

## 6. Tests

`test_evade_one_evader_costs_only_itself` asserts the §5 outcome: extraction names the other 21 seats
and flags incompleteness. It asserts nothing about v1.46 — that behaviour is what the fix changed,
and pinning a regression to a superseded revision would make the test fail for the wrong reason when
the superseded file is eventually dropped. Observed: pass (`--self-test`, 4 tests OK).

## 7. Cost of a run

The most expensive game: `game_evade()` performs 6 × 8 δ-searches, the largest capped at 400,000
trials, plus the consequence demonstration. It dominates the suite's 148.19 s wall time.

```
cd domains/09-security-games-and-attack-lab/src
python3 ceqs_games.py --evade
python3 ceqs_games.py --evade --json
```

## 8. What would falsify this, and open items

- **A measured exponent below 1.** Would mean the linear trick finds collisions more cheaply than the
  generic `2^E` — a genuine weakness, since the ledger's binding row is `2^E`/`2^256`. Measured
  1.0242. With 6 points and no error bars the interval is not computed (`games-methodology.md` §6).
- **An extractor that aborts or under-reports.** The regression covers one evader at the threshold
  `C = 22`. Untested here: more than one evader; an evader that is also a false positive; evaders at
  `C = 23…42`; an evader whose second opening is genuine rather than fabricated.
- **`complete` being ignored by a caller.** The flag exists; whether a relying party acts on it is a
  protocol question outside this domain. The harness shows the flag is set correctly, not that anyone
  reads it.
- **A real collision at toy width.** Out of reach (`2^E`), which is why §5 uses a placeholder. A
  reader who wants the full chain needs a run at `E ≤ 8` where 256 δ-trials suffice, joined to the
  consequence demonstration in one program. Not done here.
