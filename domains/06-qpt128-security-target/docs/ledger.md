# The ledger: how the gate budget is composed and how each bound enters

This document explains the machine in `src/qpt128_finalization.py` — what a row is, how a row becomes
a number, how the numbers are added, and what the addition is allowed to mean. Every number quoted
here is from `results/qpt128_report.json`, regenerated in this repository; the recomputation is in
`results/ledger-independent-check.txt`.

---

## 1. Units and the budget

Two units exist in the ledger and they are not interchangeable:

| Unit label in the report | Meaning | Used by |
|---|---|---|
| `queries (one gate per query)` | one oracle query costs one unit | the `g_log2 = 0` scenarios |
| `gates, one query = 2^18 gates` | one oracle query costs `g_H = 2^18` T gates | the `g_log2 = 18` scenarios |

The gate system is the target's own unit (D1/D2 are statements about `G`, a gate count). The query
system is kept because it is the unit the project's earlier work was written in, and because the
difference between the two is itself a result: **B0 passes in gates (+23.0 bits) and fails in queries
(−11.0 bits)** (report scenario 6 vs scenario 1). Counting queries is a different claim.

A scenario declares its unit once. Inside a scenario every row is evaluated with `q = G/g`, where
`g = 1` in query units and `g = 2^18` in gate units. Because the rows' envelopes are polynomials in
`q` and the reduction-time term is itself divided by the oracle cost, **the same physical row carries
a different number in each unit system, and the shift is not a constant**:

| Row (Mode S, 1024-bit keys, rigorous) | query units | gate units | shift |
|---|---:|---:|---:|
| E1 joint online extraction | −133.302 | −169.302 | −36.0 |
| E2 honest-proof simulation | −159.415 | −159.415 | 0.0 |
| E3 credential preimage | −95.0 | −203.0 | −108.0 |
| E4 registry-key collision | −338.793 | −500.793 | −162.0 |
| E5 link coincidence | −90.023 | −198.023 | −108.0 |
| E6, E7, E8 (model premises) | 0 (reported `null`) | 0 (reported `null`) | — |
| **total** | **−89.978 → FAIL** | **−159.414 → PASS** | |

The shifts differ because the rigorous rows carry a `q²·2^12` term added to the reduction time, the
degree of that polynomial differs per row, and the whole reduction time is divided by the oracle cost
(`2^18` in gate units, `1` in query units). The simulation row E2 does not move at all: it is
*decreasing* in `q` and is dominated by `q_S = 2^64`, so its evaluation at `q = 1/g` is the same to
display precision in both systems.

The budget is `G ≤ 2^128` (`LOG2_BUDGET`), and D2's constant is `κ = 130` (`KAPPA`).

---

## 2. Constants

| Constant | Value | Role |
|---|---|---|
| `LOG2_BUDGET` | 128 | the D1 budget edge `G = 2^128` |
| `KAPPA` | 130 | D2's exponent: `Pr ≤ G·2^−130` |
| `E_UPPER` | `27182818285/10^10` | rational upper bound on `e`, used inside the CFHL envelope |
| `G_H_LOG2` | 18 | SHA3/Keccak oracle T-count floor (one query = 2^18 gates) |
| `G_F_LOG2` | 18 | credential-function circuit floor |
| `G_AES_ITER_LOG2` | 17 | one AES-256-key-search iteration = two AES-256 oracle calls, T gates only |
| `G_SIM_LOG2` | 12 | per-entry compressed-oracle work charged by the rigorous extractor accounting |
| `Q_SIGN` | `2^64` | honest proofs/signatures per key (the `q_S` of GHHM Thm 3) |
| `SEATS`, `QUORUM`, `FAULTS` | 64, 43, 21 | quorum arithmetic: `2·43 − 64 = 22 = 21 + 1`, `64 = 3·21 + 1`, `C(64,2) = 2016` |
| `CREDENTIAL_BITS`, `LINK_BITS` | 512, 512 | credential and link security parameters |

Every floor is a **lower** bound on the cost of an oracle call. The ledger charges the floor, so the
ledger's charges are conservative; the sources record that depth, parallelism and memory are not
charged at all (`docs/qpt128-finalization.md` §7, non-claims). The AES Grover G-cost of `1.17·2^148`
is quoted in the sources but **not** charged anywhere in the ledger.

---

## 3. Rows

A row is a named tuple `Row(name, rho, shape, status, source)`:

- `rho(q)` returns the row's **uncapped exact rational** bound as a function of `q`, the adversary's
  oracle-query count;
- `shape` is `convex` (polynomial in `q` with non-negative coefficients) or `decreasing`;
- `status` is `proven-QROM`, `named-assumption` or `model-premise` and is emitted with every row in
  the report, so a reader can see which rows are theorems and which are premises;
- `source` records where the bound comes from.

The envelope functions, exactly as the checker implements them:

| Envelope | Formula | Used for |
|---|---|---|
| `hrs16_search(q,n,targets)` | `8·targets·(q+1)²·2^−n` | E3 (64 targets, n = 512), E5 (2016 pairs, n = 512), B0's signature envelope (n = 256) |
| `cfhl_collision(q,n)` | `80·E_UPPER²·(q+1)³·2^−n + 4·2^−n` | E4 |
| `dfms_extraction(q,n,ℓ,p_triv)` | `(22ℓ+60)·q³·2^−n + 20·q²·p_triv` | the single-proof extraction form |
| `joint_extraction(…)` | `2v·2^−n + (22ℓ+60)·q³·2^−n + 20·q²·p_triv` | E1, with `v = 2(1+3r)` |
| `zkboo4_parameters(r)` | `ℓ = 4r`, `p_triv = (3/4)^r`, `v = 2(1+3r)`, `2r` challenge bits | the concrete backend |
| `unused_legacy_12q154(q,n)` | `12(q+154)³·2^−n` | **not used in any scenario**; kept only to measure the discrepancy |
| `generic_category5_signature(t,g_iter)` | `hrs16_search(t/2^{g_iter}, 256, targets=1)` | B0 and compat-mode signature forgery |

The CFHL envelope is a rational upper bound on the published `Thm 5.29` form obtained by
`(a+b)² ≤ 2a² + 2b²`: it is a factor ≈ 2 above the published leading term (`80e²` against `40e²`).
That is the conservative direction, and it is stated rather than hidden.

The two `q`-scaling traps the checkers' tests pin down: `hrs16` and `cfhl` are capped at 1 by default
(used only when a row's value is read as a probability), and the scenario rows call them with
`capped=False` because the capping happens later, at the D1 step.

---

## 4. From a row to a number: the endpoint rule

The ledger must bound `max_{1 ≤ G ≤ 2^128} ρ(G/g)/G`, not `ρ` at one point. Lemma L4 supplies the rule:

- for a `convex` row, the maximum is at an endpoint, so the checker takes
  `max(ρ(1/g), ρ(2^128/g)/2^128)`;
- for a `decreasing` row, the maximum is at `G = 1`, so the checker takes `ρ(1/g)`.

**Capping must not be done before maximisation.** `min(1, ρ)` is not convex, and its ratio can peak
in the interior: test 19 constructs a capped envelope whose interior ratio exceeds both endpoint
ratios and shows that the uncapped endpoint bound still dominates it. The checker therefore never
maximises a capped envelope. Caps are applied in exactly one place — to each row's probability at the
budget edge, in `d1_probability` — and never to a ratio.

For D1 the probability is evaluated at the budget edge `G = 2^128` only, which is sound because the
rows are non-decreasing in `G`; that monotonicity is a property of the envelopes, not something
proved separately.

Each row's ratio is an exact `Fraction`. The report writes an exactly-zero row as `null` (the three
model-premise rows in Mode S, and B0's rollback row); `null` is the report's convention for an exact
zero, not a missing value.

---

## 5. The union-bound rule, and where it is and is not legitimate

**The rule.** If `Win ⊆ ∪ Bad_i` and `Pr[Bad_i] ≤ ρ_i(G)` for every `i` and every admissible `G`, then
`Pr[Win(A)] ≤ Σ_i ρ_i(G)`. Dividing by `G` and taking the supremum,

```
Σ_i max_{1≤G≤2^128} ρ_i(G)/G  ≤  2^−130        ⟹   Pr[Win] ≤ G·2^−130  for every A with G ≤ 2^128,
```

which is D2. D2 is used as the working target because it implies D1: for `G < 2^128`,
`G·2^−130 < 2^128·2^−130 = 2^−2 < 1/3`. Test 05 checks this implication at three budgets
(`G = 1`, `2^64`, `2^128 − 1`) and checks the exponent identity `8·2^−131 = 2^−128` which the project
uses as shorthand for its per-gate coefficients. **That identity is arithmetic on coefficients; it is not the acceptance
test.** The acceptance test is the exact comparison of the summed ratios against `2^−130`.

The report's verdicts are therefore: `D2_kappa130 = (total ≤ 2^−130)`, `D2_margin_bits = −130 −
log₂(total)`, and `D1_pass = (Σ capped row probabilities < 1/3)`. Note the two comparisons differ in
strictness: D2 uses `≤`, D1 uses a strict `<` against `1/3`. Note also that when D2 fails badly the D1
probability caps at exactly 1 (the report prints `0.0` in log₂), i.e. the union bound alone then says
nothing about success — it is the *sum of probabilities*, not the sum of exponents, that decides.

**Where it is legitimate.** Only over a family that provably covers the winning event. The coverage
is argued per scenario in `docs/qpt128-finalization.md` §4 (Theorem A, public signers) and §5
(Theorem B, hidden signers), where each bad event is tied to a step of the game.

**Where it is not.**

1. **It is not a licence to import unproved terms.** Four rows are exactly zero by premise:
   `E6` (HVZK on uniform tapes, the `q_S·Δ_HVZK` term of GHHM Thm 3), `E7` (an ideal collaborative
   prover), `E8` (registry authenticity, canonical encoding, durable approval state) and B0's
   "canonical encoding / rollback". Test 16 asserts that these rows are zero **and** labelled
   `model-premise`. A zero row means "the model makes this event impossible", not "this event cannot
   happen". They are the largest single gap in the ledger: a scenario's margin is not a lower bound
   on the true margin unless those premises hold.
2. **It is not legitimate across unit systems.** Query-unit and gate-unit rows may not be added: one
   query is `2^18` gates, so mixing them under-counts by 18 bits per query of the offending rows.
   Every scenario declares one unit and stays in it.
3. **It is not legitimate across keys or across model changes without re-deriving the cover.** The
   512-bit registry-key scenarios inherit Mode S's event list but not its numbers; the result is a
   −141.2-bit failure in gates, which is a result about that parameter choice, not about the proof
   system.
4. **It does not compose with the withdrawal.** Compat mode is kept in the report as a failing row
   so that the withdrawal is visible in the arithmetic, not just in prose: −291.0 bits in queries and
   −185.0 in gates.

---

## 6. The extraction charge

Every scenario that needs a witness — all of Mode S, and compat mode — pays the same charge, `E1`:

```
joint_extraction(q, 512, ℓ, p_triv, v)  with  ℓ = 4r,  p_triv = (3/4)^r,  v = 2(1+3r)
```

The charge is the DFMS bound for a single proof with the v1.35 joint lift's readout term added, and
it enters the ledger with `capped=False` (a ratio, not a probability). The ledger gives it a share of
at most `2^−133` and finds the **minimum repetition count** by exact binary search:

| Unit system | minimum `r` | ratio at `r` | ratio at `r−1` |
|---|---:|---:|---:|
| queries | **640** | `2^−133.302` (passes) | `2^−132.887` (fails) |
| gates | **553** | `2^−133.194` (passes) | `2^−132.779` (fails) |

Test 09 checks the boundary exactly in both directions. The scenarios use the larger, `r = 640`,
which is why a Mode S certificate needs 640 repetitions of a four-subset commit-and-open protocol —
that number, not the signature size, is what decides whether the hidden-signer route exists at all.

The difference between the "attack-cost accounting" and "rigorous extraction overhead" scenarios is
one term: whether the extractor's own running time (`q²·2^12` operations, `G_SIM_LOG2 = 12`) is added
to the reduction time when the signature row is evaluated. Adding it is what makes the 512-bit-key
configuration fail and forces 1024-bit registry keys.

---

## 7. The exact-arithmetic method

- **Probabilities and ratios are `fractions.Fraction`.** No float enters a verdict. `pow2(e)` returns
  `F(1 << e)` or `F(1, 1 << -e)` and refuses a non-integer exponent, so an accidental fractional
  exponent raises rather than silently rounding.
- **Square roots are rigorous.** `sqrt_upper(x)` returns `(isqrt(⌈x·2^200⌉) + 1)/2^100`, an upper
  bound on `√x` on a `2^−100` grid. Test 17 checks `s² ≥ x` for six values of `x`, checks the reverse
  direction up to the grid (`(s − 2^−99)² ≤ x + 2^−90`, i.e. `s` is never more than one grid step
  above `√x`), and checks that a negative argument raises.
- **Logarithms are display only.** `log2(x)` computes `(ln x_num − ln x_den)/ln 2` in 60-digit
  `Decimal` arithmetic and returns a float; the report rounds it to 3 or 9 decimals. No comparison in
  the checker or in any verdict uses a logarithm.
- **The reporting convention that follows from this.** The cleanest example is L1's own row: the
  report prints `"success_lower_bound_log2": −128.0`, because the exact lower bound is `2^−128` plus a
  term far below the printed precision — while `"exceeds_two_pow_minus_128": true` beside it is the
  strict exact comparison that carries the refutation. The same effect makes the L2 row for 64 keys
  print a bound equal to the one-key row's (the two exact bounds differ by about `2^−125.2`); see
  `results/ledger-independent-check.txt`.
- **Where a verdict is a comparison.** `D2_kappa130` is `total ≤ 2^−130` on `Fraction`s;
  `D1_pass` is `Σ capped probabilities < 1/3`; `exceeds_two_pow_minus_128` is `lb > 2^−128`. All
  three are exact.

---

## 8. Verdict table

Report order, with the `g_log2` each scenario was evaluated at:

| # | Scenario | Units | total log₂ | D2 (κ=130) | margin (bits) | D1 |
|---:|---|---|---:|---|---:|---|
| 1 | B0 public signers, signature in clear | queries | −119.000 | fail | −11.000 | fail |
| 2 | Mode S, r=640, 1024-bit keys, attack-cost | queries | −133.302 | **pass** | +3.302 | pass |
| 3 | Mode S, r=640, 512-bit keys, rigorous | queries | +173.207 | fail | −303.207 | fail |
| 4 | Mode S, r=640, 1024-bit keys, rigorous | queries | −89.978 | fail | −40.022 | fail |
| 5 | compat mode, rigorous | queries | +161.000 | fail | −291.000 | fail |
| 6 | B0 public signers, signature in clear | gates | −153.000 | **pass** | +23.000 | pass |
| 7 | Mode S, r=640, 1024-bit keys, attack-cost | gates | −159.414 | **pass** | +29.414 | pass |
| 8 | Mode S, r=640, 512-bit keys, rigorous | gates | +11.207 | fail | −141.207 | fail |
| 9 | Mode S, r=640, 1024-bit keys, rigorous | gates | −159.414 | **pass** | +29.414 | pass |
| 10 | compat mode, rigorous | gates | +55.000 | fail | −185.000 | fail |

The D1 probability at the budget edge is `2^−25.0` (B0, gates), `2^−41.302` (Mode S rigorous 1024-bit,
gates), and capped at 1 in every failing scenario.

The ledger's own summary of the legacy route, kept for the record: D3's ledger is **refuted**, not
failed — L1 exhibits a 256-bit-secret game where `2^63` iterations exceed `2^−128` (report key `L1`,
verdict string `REFUTED as stated; restate as D1/D2 with gate accounting`), and the unsourced
collision constant `12(q+154)³/2^512` (log₂ = −124.415) is superseded by the CFHL envelope
(log₂ = −118.793) — the published leading term alone gives −119.793.

---

## 9. Open items

1. **Model-premise rows are zero.** E6, E7, E8 and B0's rollback row need arguments or explicit
   charges; today they are premises, and the margins are conditional on them.
2. **The floors are measurements, not bounds.** `2^18` and `2^17` are T-counts of published circuits;
   depth, parallelism and memory are uncharged (in the safe direction for a floor, but it means the
   ledger is not a circuit-level cost model).
3. **The extraction coefficient is one of three readings** (`22ℓ+60` here, `20ℓ+60` in D5,
   `72+40ℓ` in D4). Smaller would only increase the margins; that is an observation, not a
   re-derivation.
4. **The signature row is an envelope, not a proof.** B0's row is AES-256-key-search strength at the
   reduction's running time; the scheme's own QROM proof (Kosuge–Xagawa) contributes no number here.
5. **Unit-system dependence.** D2 is claimed in gate units. The query-unit table is kept for
   comparison and fails in four of five families; a reader should not mix the two.
6. **`r = 640` is set by the extraction share only.** The choice of a `2^−133` share is a ledger
   convention; a different share moves the minimum repetition count, and the report states the
   convention explicitly in the key name
   (`minimum_repetitions_extraction_share_2^-133`).
