# Games methodology — how `src/ceqs_games.py` measures an attacker

This document says what the harness in `src/ceqs_games.py` (v1.52) does, why each part of it is
there, and what a reader is entitled to conclude from its output. One document per game follows:
`game-frame.md`, `game-suppress.md`, `game-evade.md`, `game-safety.md`.

---

## 1. The problem, and why it is hard

Security arguments for this construction are written as reductions: "an adversary that wins game G
can be turned into an adversary that solves problem P". Those reductions are only as good as the
problems they reduce to, and a reduction usually asserts a hardness assumption without measuring
anything: it says the search space is `2^256`, or that the collision game has output length `h`.

Two things can go wrong and neither is visible from the reduction text alone. First, the reduction
can be right about the *law* and wrong about its *constant* — an attack that is genuinely `2^n` may
be `2^(n-1)` or `2^(n+1)` in practice, which changes a margin but not a conclusion. Second, and more
seriously, the object the reduction names can fail to be the object the implementation computes: the
reduction may talk about a random function while the code evaluates a quadratic map with a published
handle that collapses the search space from `2^(2n)` to `2^n` (`docs/attack-lab.md` §3, the control
at n = 8).

The games in this domain address both by taking the reduction's *statement* as the definition of a
game, running the best attack the project knows against the **real** key map at deliberately weak
parameters, and measuring how the cost grows. That converts "the reduction assumes the search costs
`2^n`" into "the search on the real function costs `2^n` at the sizes we could measure, and here is
the fitted exponent".

**Why it is hard.** Exponents cannot be measured directly; only the cost at a specific size can.
Recovering an exponent needs several sizes, a fit, and a comparison against the exact theory at
those sizes — and the fit has to be honest about the fact that a law verified at 8–17 bits does not
transfer to 256 bits by itself. §6 below measures that transfer error rather than assuming it away.

---

## 2. The shape of every game

The harness states each game in the same five-part form, and the report repeats it:

```
GAME  ->  attacker's information  ->  allowed oracle queries  ->  winning condition
      ->  attack algorithm  ->  measured Q(parameter)  ->  fitted exponent  ->  theory
```

The five keys are literal fields of each game's definition dictionary (`GAME_FRAME`,
`GAME_SUPPRESS`, `GAME_EVADE`, `GAME_SAFETY` in `src/ceqs_games.py`), and they are printed at the
top of each game's output, so a reader sees the statement of the game next to its numbers:

| key | what it fixes |
|---|---|
| `attacker_receives` | the information the adversary is given |
| `attacker_does_not_receive` | what it is *not* given — usually any opening `(s, r)` |
| `oracle` | the operation whose invocations are counted as `Q` |
| `wins_if` | the winning condition, stated as a predicate on the adversary's output |
| `attack` | the algorithm the harness runs, i.e. the best one the project has found |
| `theory` | the closed form the measured `Q` is compared against |

`attacker_receives` is part of the game, not decoration. FRAME gives the adversary the certificate,
all 43 published handles and the target's handle — because they are public on the wire — and the
measurement only means something because of that. A reader who thinks an attack gets *less* is
reading a different game.

Three of the four games are winnable at toy parameters, and the harness makes them win: a game
nobody can win teaches nothing about the exponent of the attack that would win it. The fourth
(SAFETY) is not winnable below the threshold, and there the measurement is of the threshold itself.

---

## 3. What `Q` counts

`Q` is a count of **oracle invocations**, and the oracle differs per game:

| game | oracle | the unit `Q` counts |
|---|---|---|
| FRAME | the public key map `F` | evaluations of `F` |
| SUPPRESS | the public challenge derivation `H(cfg, d, m)` | evaluations of `H` |
| EVADE | the relation `F(x ⊕ δ) = F(x)` restricted to a fixed `δ` — a linear solve | δ trials |
| SAFETY | — | not measured; the corruption level `C` is the parameter |

`Q` is *not* a gate count and not a wall-clock time. The relation between an oracle invocation and
the gates needed to evaluate it is a separate accounting step, charged in domain 08's ledger at
≥ 2¹⁸ gates per evaluation; the harness neither simulates those gates nor claims to. Experiment C of
`src/ceqs_attack_lab.py` simulates Grover's *algorithm* exactly on a real oracle, and charges no
gates at all. That split is stated in the record (`results/attack-lab-results.md` §10) and repeated
here because it is the most likely place for a reader to over-read a number.

---

## 4. The instances measured, and the redraw rule

Every measurement runs on a **toy registry** built by `_instance()`: `N = 64` seats, quorum 43,
opening width `n` bits (8–17 in this domain), expansion `E` (2–12), and a fixed epoch string, all
seeded deterministically so a re-run reproduces the same instance.

A toy instance is **redrawn** when the weak widths cause a collision among the 43 published handles.
That is not a convenience: `encode` correctly refuses to emit a certificate whose handles are
ambiguous, so the instance is not usable at all, and the rate at which it happens is itself measured
and reported (`results/attack-lab-results.md` §9: measured 0.370 at n = 11 against a predicted
0.357, down to 0.003 at n = 17 against a predicted 0.007). At production handle width the predicted
rate is 7.8 × 10⁻⁷⁵.

The redraw is a bias, and it is a bias *against* the attacker's interest: an instance with a
handle collision is discarded rather than exploited. Nothing in this domain measures what a handle
collision would be worth to an attacker — §12.5 of the record shows the same mechanism from the
other side, where a *would-be* handle coincidence makes extraction name a seat that did not
double-sign (measured rate 0.0900 at n = 14 against a predicted 0.1102).

---

## 5. The theory each game is compared against

Three standard results are used. For each: what is used, what is not, and where the citation stands.

### 5.1 The birthday bound — `Q = √(π/2 · 2^h)`

*Used in:* SUPPRESS, as `theory_Q` for both handle revisions.
*Statement as used here:* searching for a collision among the outputs of a random function with `h`
output bits takes about `√(π/2 · 2^h)` queries; the constant is the standard `√(πN/2)` birthday
value (the expected number of draws before a repeat is `√(πN/2)` in the limit).
*What is used:* the expected-query constant only.
*What is not used:* nothing else of the birthday literature — no variance, no memory trade-off, no
parallel-collision (van Oorschot–Wiener) speed-up. Those would only *lower* the cost, i.e. they would
favour the attacker, so the comparison is not weakened by leaving them out — but the harness must not
be read as having ruled them out. They are listed as an untested surface in `validation-status.md`.
*Citation:* the source states "birthday theory" and derives the constant in the line
`math.sqrt(math.pi / 2 * 2 ** h)`; **the source gives no citation at all** and this document adds
none it can verify. The programme's theory index records the birthday bound as standard, and that
index is not a published reference. A reader who needs a citable statement of the `√(πN/2)` constant
must supply it; the harness's own claim is only that its measured `Q` follows that law with the
fitted slope in `game-suppress.md`.

### 5.2 Grover's iteration law — `sin²((2k+1)θ)`, `θ = arcsin√(M/N)`

*Used in:* FRAME's quantum row, and measured for real in `src/ceqs_attack_lab.py` Experiment C.
*Statement as used here:* after `k` iterations of the amplitude-amplification operator on a search
space of size `N` with `M` marked elements, the success probability is `sin²((2k+1)θ)` with
`θ = arcsin√(M/N)`; the optimal iteration count is `k ≈ (π/2 − θ)/(2θ) ≈ (π/4)√(N/M)`.
*What is used:* the exact success-probability law, the optimal `k`, and the resulting
`(π/4)·2^(n/2)` scaling when `M = 1`.
*What is not used:* any gate-cost model, any fault-tolerance or error-correction overhead, and any
statement about how many of these iterations a real device can run. Domain 08's ledger charges the
gate cost separately with an explicit `≥ 2^18 gates` per oracle evaluation, and this domain does not
touch that number.
*Citation:* **the source states the law and cites nothing.** The programme's theory index records it
as "standard (added): Grover, STOC 1996" — the attribution was added by the index, not by the
harness. That is the incompleteness this document is required to state plainly: the formula is
standard and its exact simulation is checkable here, but the harness itself does not carry a
reference, and a formal write-up must supply one.

### 5.3 The CFHL collision bound — `40e²(q+1)³/M`

*Used in:* SUPPRESS, in the two extrapolated quantum rows only.
*Statement as used here:* Chung–Fehr–Huang–Liao, EUROCRYPT 2021, Theorem 5.29 gives a bound on a
quantum adversary's collision-finding advantage with leading term `40e²(q+1)³/M` for a function into
`M` outputs and `q` queries; domain 06 implements a rational upper bound
`80·e²·(q+1)³·2^−n + 4·2^−n` (the leading term doubled by the `(a+b)² ≤ 2a² + 2b²` step) and solves
it for advantage `1/3`.
*What is used:* that one collision-finding term, at `h = 256` and `h = 768`, to say whether
suppressing the old and the new handle are inside or outside a `2^128`-gate budget.
*What is not used:* the theorem's generality (arbitrary function families, other query models) —
it is not re-proved here and the harness does not exercise the theorem, only its closed form.
*Citation:* the record cites "the project's own CFHL collision bound
(`qpt128_finalization_v1.43.py:cfhl_collision`)". **The citation names the theorem and that is
all**: no title, no page. Domain 06's `domains/06-qpt128-security-target/docs/theory.md` §8 carries the fuller form
("Chung–Fehr–Huang–Liao, EUROCRYPT 2021, Thm 5.29") and marks it incomplete there in the same way.
*Provenance of the printed numbers, checked in this build:* `src/ceqs_games.py` does **not** call
the CFHL checker; it prints four constants (`81.7`, `99.7`, `252.4`, `270.4`). This build re-derived
them from domain 06's `cfhl_collision` by binary-searching the smallest query count whose bound
exceeds `1/3`: `2^81.74` for `h = 256` and `2^252.40` for `h = 768`, i.e. `81.7` and `252.4`
queries, and `99.7` and `270.4` gates at `2^18` gates per query. The constants reproduce exactly.
The check is a row in `VERIFICATION.md`; the derivation is not shipped, because the function it
calls is shipped by domain 06 for exactly this purpose.

### 5.4 The transplant this domain does *not* perform

Nothing here re-derives the QROM soundness row of the proof system; it is transplanted from FAEST v2
Lemma 9.39 by domain 08 (`results/attack-lab-results.md` §10). The Harada–Rogaway–Reyzin search bound
(`8(q+1)²/2^n`; domain 06 `domains/06-qpt128-security-target/docs/theory.md` §7 cites it as HRS16) **is not used anywhere in this
domain** — it is named here only so that a reader comparing the two domains does not go looking for
it. It *is* load-bearing in domain 08: assumption A-F1 is stated in terms of it
(`domains/08-hidden-signers/docs/mode-b-security.md` §2, A-F1: no algorithm with `q` evaluations of
`F` beats `8(q+1)²/2^256` per target), so a weakness in that bound would reach this domain's
conclusions through A-F1 rather than through anything measured here.

---

## 6. How the fit is made, and what it can and cannot show

`fit(xs, ys)` is a two-line ordinary least-squares regression of `log₂ Q` on the parameter. It
computes a slope and an intercept and nothing else: **no standard error, no confidence interval, no
weighting, no goodness-of-fit statistic** is reported. That is deliberate and it is the main caveat
of this document.

What the fits therefore establish: the measured cost follows the theory's *law* — slope and
intercept land within a fraction of a bit per bit of the predicted line, on 5 to 13 points.

What they do **not** establish: how tightly that law is pinned down. With 5 points and no error bars,
a slope of `1.0178` against a theory of `1.0` is consistent with the theory, but the interval around
it is not computed and is not claimed. The harness does not use the fit's own uncertainty — instead
it measures the extrapolation error directly against the exact theory, which is stronger and is the
subject of §6.1.

Two further properties of the fit are worth stating because they are choices:

- **`log₂ Q` is fitted, not `Q`.** The theory predicts exponential growth, so the linear model is in
  the exponent; fitting `Q` linearly would be fitting the wrong model.
- **All points are weighted equally**, including the largest, which is also the most expensive and
  therefore the one measured with the fewest samples. FRAME's per-point sample count is 6 at every
  size; EVADE's is 8 per point (with a cap of 400,000 δ trials); SUPPRESS's falls from 12 samples at
  the small v1.46 sizes to 2 at the largest v1.50 size, because each sample is a `2^16`-ish birthday
  search. `game-suppress.md` §5 states the consequence.

### 6.1 The extrapolation error, measured rather than assumed

Fitting over `n = 8…19` and extending to production accumulates error in both directions. The
harness computes it:

| game | fitted at production | exact theory | error |
|---|---:|---:|---:|
| FRAME (classical) | `2^259.6` | `2^255` | **+4.6 bits** |
| SUPPRESS at `h = 256` | `2^115.9` | `2^128.3` | **−12.4 bits** |
| SUPPRESS at `h = 768` | `2^346.2` | `2^384.3` | **−38.1 bits** |

The SUPPRESS row is the important one: the fit *understates* the production cost, and by more the
larger `h` gets, because the fitted intercept is used at an `h` far outside the measured range. A
reader who took the fits as the production estimate would understate the collision cost by 38 bits at
`h = 768`. This is why the domain states in three places — the harness docstring, the record
(§12.6) and the README — that the 128-bit conclusions come from the reductions in domain 08's
`domains/08-hidden-signers/docs/mode-b-security.md` and never from these fits.

---

## 7. Tests

```
cd domains/09-security-games-and-attack-lab/src
python3 ceqs_games.py --self-test      # 4 tests
python3 ceqs_games.py --all            # the four games, ~2.5 min
python3 ceqs_games.py --frame|--suppress|--evade|--safety
python3 ceqs_games.py --all --json     # the report that results/games-report.json holds
```

`--self-test` runs four tests, one per game, and **exits 1 if any of them fails** (the mode returns
`0 if r.wasSuccessful() else 1`). `--all` is a report mode: it prints measurements and returns 0 by
construction, so its verdict lives in the report body — the fitted slopes, the measured threshold and
the violation counts — not in an exit code. Every command's observed exit code is recorded in
`VERIFICATION.md`, and the failure path of `--self-test` is demonstrated there by a probe that
injects a failing assertion into a copy of the harness outside this repository.

| test | asserts | why it is the right assertion |
|---|---|---|
| `test_frame_is_winnable_and_scales` | the endgame frames the victim for real, and the fitted classical slope is inside `[0.85, 1.15]` | a frame that does not actually name the victim measures nothing; the band is wide enough not to encode the fitted value |
| `test_suppress_law_holds_for_both_schemes` | the two schemes' fits share one slope near `0.5` and their intercepts differ by less than 1 bit | the claim is "one birthday law, two output lengths", so the *intercepts* must agree — a per-scheme slope would refute it |
| `test_evade_one_evader_costs_only_itself` | with one corrupt double-signer, extraction names the other 21 and flags incompleteness; it does not assert the reverse for v1.46 | the v1.46 behaviour is what the fix changed; asserting it would pin the regression to a superseded revision |
| `test_safety_threshold_is_22` | equivocation is impossible for `C ≤ 21` and possible for `C ≥ 22`, no genuine double-signer is missed, and at most 3 extra names appear at `C ∈ {22, 23}` | the threshold is the claim; the extra-name bound is the measured handle-coincidence effect of §12.5 |

The last assertion deserves a note: extraction naming *more* seats than there are double-signers is
not an error, and the test allows up to 3 of them rather than 0. That is a real property of the
construction (a would-be handle coincidence at weak handle width), it is measured and modelled in
`game-safety.md` §4, and the test's job is to keep the effect bounded, not to pretend it is absent.

---

## 8. Sizes, cost, and what a run takes

| artefact | bytes | what it is |
|---|---:|---|
| `src/ceqs_games.py` | 29,038 | the whole games harness, 573 lines |
| `results/games-run.txt` | 3,943 | the transcript of the re-run in this repository |
| `results/games-report.json` | the `--all --json` report | the machine-readable form |
| `results/attack-lab-results.md` | 20,946 | the record; §12 is this harness's write-up |

Measured in this repository, in the pinned environment (Python 3.12.3, numpy 2.4.6), from
`domains/09-security-games-and-attack-lab/src`:

| command | wall clock | exit | result |
|---|---:|---:|---|
| `--self-test` | 2.41 s (confirmation run) | 0 | `Ran 4 tests … OK` |
| `--all` | 56.11 s (confirmation run) and 148.19 s (shipped transcript) | 0 | all four games; recorded baseline 126.1 s |
| `--all --json` | 55.54 s and 88.78 s | 0 | the machine-readable report |

The spread is host load, and it runs in **both** directions: the recorded 126.1 s sits inside the
observed range, another package in this repository measured the same files at 122.7 s and 168.58 s,
and every run — all of them — produced identical measured values. `VERIFICATION.md` carries each
observation and the reason.

Per-mode costs measured in one sequential pass (wall clock, exit 0 for each): `--frame` 9.74 s,
`--suppress` 34.02 s, `--evade` 13.14 s, `--safety` 0.72 s. The four sum to 57.62 s, which is within a
second of the `--all` wall measured in the same period (56.11 s) — the small excess is four extra
interpreter start-ups. That agreement is the point: `--all` runs exactly these four and prints a
summary, and the two numbers match once they are taken under comparable load. An earlier draft of this
section compared per-mode figures taken under one load against `--all` figures taken under another and
drew a conclusion from the gap; the gap was the host, not the work.

---

## 9. Packages and tools, and what a different answer would change

**Python 3.12.3** (the programme's pinned interpreter) and **numpy 2.4.6**, and nothing else. The
games harness imports only the standard library — `argparse`, `hashlib`, `importlib.util`, `json`,
`math`, `os`, `random`, `sys`, `time`, `unittest` — plus the Mode B implementation it tests. numpy
is used by the attack lab's Grover simulation, not by the games.

There is **no solver, estimator or external tool in the loop.** That matters for how a result here
could be wrong, so it is worth being explicit about the three things that could move a number:

1. **The random draw.** Every measured quantity is a mean over a finite number of samples of an
   attack whose cost is a geometric/birthday random variable with a long right tail. A different seed
   moves the means by amounts comparable to the sampling error at 2–12 samples, which is why the
   tests assert wide bands and why the fitted slopes — not individual means — are compared to theory.
   The seeds are fixed in the source, so a re-run reproduces the same means exactly; a reader who
   wants the sampling error must change the seed and re-run, and the harness provides no flag for it.
2. **numpy's floating point.** Experiment C's agreement with `sin²((2k+1)θ)` is `5.3 × 10⁻¹⁵`, which
   is double-precision noise; a different BLAS or a different numpy would move that figure within its
   own precision but could not change the measured *iteration counts*, which are integers read off a
   probability array. No conclusion in this domain rests on the size of that deviation.
3. **The CFHL constants.** `81.7`, `99.7`, `252.4`, `270.4` are transcribed constants (see §5.3). A
   revised collision bound would change those four printed values and the verdict sentence on the
   v1.46 row. It would **not** change any measured quantity, and it would not change the structural
   conclusion of SUPPRESS, which is that the fix moved the collision output length from 256 bits to
   768 — a fact about the challenge derivation, verified by Experiment E's before/after run, not by
   the bound.

If the project's hardness assumption for the key map were wrong — i.e. if solving the quadratic
system were materially cheaper than generic search — every fit here would still hold at toy sizes
and every conclusion about production would be void. That is the single largest untested dependency
of this domain, and it is domain 08's cryptanalysis surface, not this one's; it is listed in
`validation-status.md`.
