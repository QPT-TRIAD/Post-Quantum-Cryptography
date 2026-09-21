# 14 — Classical attack surface

This domain lifts the raw mathematical primitives out of the record — the hidden-signer key map and
its handle, and the QLWR trace — with **no network layer, no certificate framing and no proof
system** around them, exposes them as ordinary operations, runs real classical attacks against
scaled-down instances, and fits a workload curve to what the attacks cost.

**What a workload curve can do.** It can *falsify*: an attack that grows polynomially where the
security argument needs exponential growth is a shortcut, and that is a finding at any size. It can
*calibrate*: it checks that an attack costs what the record's formula says it costs, at sizes where
that can be checked. On the campaign in `results/campaign-2026-09-21-E300/`, every attack whose work
is *counted* rather than timed grew at the rate the record's formula predicts — exhaustive search at
0.983 and 0.993 bits per bit of `n` against 1.0, the structural collision at 0.983 per bit of `E`
against 1.0, the birthday collision at 0.483 per bit of `m` against 0.5.

**What it cannot do.** It cannot validate production security, and nothing here is a security
estimate. Exponential growth over sizes a desktop can reach does not prove exponential growth at
`n = 256`: algebraic attacks change regime as the solving degree steps up, lattice reduction is
polynomial across the whole toy range because LLL suffices there, and the record's own attack lab
measured fits of exactly this kind mis-extrapolating by **+4.6, −12.4 and −38.1 bits**. It also says
nothing about attacks that were not run.

**One section of the report must be read with its correction attached, and §5 below is that
correction.** The comparison of the Gröbner attack against exhaustive search compares **two
implementations, not two algorithms**. An optimised enumerator is roughly 2^12 faster than the plain
search loop used here, which reverses every row in which Gröbner appears to win. What survives the
correction is the *growth rate*, and that is the part the domain is for.

---

## 1. How to read this domain

| Order | File | What it is |
|---|---|---|
| 1 | this file | the primitives, the controls, the measured curves, the correction, the limits |
| 2 | `src/qpt_cart/scope.py` | the scope boundary, emitted verbatim above the first table of every report |
| 3 | `src/qpt_cart/primitives/` | the field, the key map and handle, the QLWR trace, and the two controls |
| 4 | `src/qpt_cart/attacks/` | exhaustive search, algebraic (Gröbner), collision (structural and birthday), lattice |
| 5 | `src/qpt_cart/harness.py` | the nine tracks, their sizes and seed counts, and the control gate |
| 6 | `src/qpt_cart/analysis/workload_curve.py` | the exponential-versus-polynomial verdict and the fit |
| 7 | `results/campaign-2026-09-21-E300/report.md`, `results.json` | the campaign: every measured point, every fit, every extrapolation |
| 8 | `VERIFICATION.md` | the re-run record: commands, environment, observed counts |

`scripts/qpt-cart scope` prints the boundary. `keygen` / `respond` / `verify` expose the key map;
`trace-keygen` / `trace-verify` expose the QLWR trace; `attack` runs one attack once; `campaign`
maps the curves and writes the report; `export-system` and `export-lattice` hand an instance to an
external solver, writing the secret to a separate file so the solver cannot read the answer by
accident.

---

## 2. The primitives, and how they are scaled

QPT-128 is a quorum-signature system and has no key encapsulation of its own — its only KEM is
standard ML-KEM-1024 — so the operations exposed are the ones its own primitives have.

| primitive | shape | operations | what an attacker wants |
|---|---|---|---|
| key map + handle (Modes A/B) | `Y = F(s ‖ r)` with `F` a **dense** random quadratic map over F₂; handle `Z = G(r) + c·s`, `G(r) = r⁷` in Mode B and `G(r) = r` in Mode A | `keygen`, `respond`, `verify` | an opening `(s, r)` that verifies (framing), or a collision of `F` |
| QLWR trace | `b = round_p(X·s)` over Z_q, recorded production values `ν = 256`, `q = 2¹⁶`, `p = 2⁸`, `m = 608` rows | `trace-keygen`, `trace-verify` | the secret `s` |

Scaling keeps the production **ratios**, not the absolute sizes: `E/n = 300/256` (ratio 1.172), and
608 rows per 256 secret coordinates. Keeping `E = 300` at `n = 8` would make a toy instance fall to
plain linearisation, and the curve would then measure the scaling mistake rather than the attack.
Mode B sizes must not be divisible by 3, so that `r → r⁷` stays a permutation as it does at
`n = 256`. `F` is dense — every coefficient a fair coin — because that is the map the record's
estimates are for; the C prover's sparse default is a different map that no estimate covers, and it
is deliberately not what is built here.

Every recovered secret is checked with the primitive's own `verify`. A run that exhausts its budget
is recorded as *not finished*, never as "the primitive held".

---

## 3. The controls, which gate every campaign

Two tracks exist only to ask whether the tester can tell exponential from polynomial at all. If
either verdict comes out wrong, the report declares its own subject verdicts **void**.

| control | must come out | measured growth | verdict | how decisive |
|---|---|---|---|---|
| preimage of a random function, exhaustive search (7 sizes, 64 seeds each) | exponential, one bit of work per bit of size | **0.992** bits per unit (95 % 0.958…1.026), against a known 1.000 | exponential in range | exponential model fits **18.4×** better (RSS 0.0972 against 1.7866) |
| preimage of a linear map, Gaussian elimination (9 sizes, 3 seeds each) | polynomial, and caught as such | 0.046 bits per unit (95 % 0.031…0.062); as a power law, **degree 3.00** | polynomial in range | polynomial model fits **10,718.8×** better (RSS 0.0015 against 16.4554) |

Both held on the campaign below, so its subject verdicts are meaningful *for the attacks and sizes
run* — which is the only thing they are meaningful for.

---

## 4. The measured curves

Campaign `full`, key-map expansion `E = 300` at `n = 256`, generated 2026-09-20T23:23:58Z. Work is
*counted* for the first four subjects and *timed* for the last three; a timed track's fit is in
log₂ seconds on one machine, not in operations, and the two are never mixed.

| subject | unit of work | sizes × seeds | growth rate (95 % interval) | record's formula | verdict |
|---|---|---|---|---|---|
| key map, Mode B (`r⁷` handle): exhaustive search over `r` | openings tried | 8 sizes × 64 | **0.983** (0.951…1.016) | 1.000 — generic framing costs `2^(n−1)` mean | exponential in range (13.0× better) |
| key map, Mode A (linear handle): exhaustive search over `r` | openings tried | 6 sizes × 64 | **0.993** (0.954…1.031) | 1.000 — the same search; the handle's form does not help a black-box attacker | exponential in range (18.8× better) |
| key-map collision: the structural "linear trick", drawn against `E` | differences tried | 7 sizes × 64 | **0.983** (0.900…1.065) | 1.000 — `2^E` differences | exponential in range (6.8× better) |
| key-map collision: generic birthday search, drawn against `m` | evaluations of `F` | 7 sizes × 32 | **0.483** (0.430…0.537) | 0.500 — `√(π/2 · 2^m)` evaluations | exponential in range (3.6× better) |
| key map, Mode A: Gröbner basis (PolyBoRi), `r` eliminated | seconds | 7 sizes × 3 | 0.722 (0.548…0.895) | the record scores Mode A at 148.8 classical bits at `n = 256`, **from a formula it never ran** | **inconclusive** — see §6 |
| key map, Mode B: Gröbner basis (PolyBoRi), quadrics + cubics | seconds | 6 sizes × 3 | **1.120** (0.981…1.258) | the record scores Mode B at 378.2 classical bits at `n = 256`, from the same formula | exponential in range (3.5× better) |
| QLWR trace: primal lattice attack (fpylll BKZ, 1 thread) | seconds | 8 sizes × 2 | 0.337 (0.306…0.368) | expected polynomial across this range: LLL suffices until the block size must grow | exponential in range (7.0× better) |

Two readings of the last row: the sizes 40 and 48 were **dropped from the fit** because a seed did
not finish, and the column to read is the minimum block size that recovered the secret, not the
seconds — block size 2 up to size 24, then `[2, 20]` at 28, `[10, 30]` at 32, `[30]` at 40 and
`[40]` at 48. A "polynomial in range" verdict there would be the known LLL regime and not a break.

Representative measured points, to show what the fits are fitted to:

| track | smallest size → mean work | largest size → mean work |
|---|---|---|
| Mode B exhaustive search | `n = 8` → 131.8 openings (2^7.04) | `n = 19` → 227,900 (2^17.80) |
| Mode A exhaustive search | `n = 8` → 131.8 (2^7.04) | `n = 18` → 123,600 (2^16.92) |
| structural collision | `E = 6` → 184 differences (2^7.52) | `E = 16` → 129,400 (2^16.98) |
| birthday collision | `m = 13` → 118.6 evaluations (2^6.89) | `m = 35` → 268,800 (2^18.04) |

---

## 5. The correction that must travel with §2b of the report

The report sets the Gröbner attack beside exhaustive search in seconds on one machine, because the
record scores Mode A far below Mode B (148.8 against 378.2 classical bits at `n = 256`) from a
formula it never ran, and that is the comparison run. **Read as a race between programs it is
misleading, and the report says so in the same place it prints the table.**

- The Gröbner engine is optimised C++. The exhaustive search is this domain's plain Python loop —
  tens of thousands of CPU cycles per opening, measured at **11.5 µs** per opening in Mode A and
  **26.2 µs** in Mode B — where an optimised enumerator (libFES-style, bit-sliced Gray code) spends
  a few: **a factor of roughly 2^12**.
- Applied to the table, that factor **reverses every row where Gröbner appears to win**. Mode A's
  seven rows all read "Gröbner, by 10.7× … 174.1×" as printed; with the factor applied none of them
  does.
- The MQ estimator of the CryptographicEstimators library agrees, naming exhaustive search the
  cheapest attack at all of these sizes — 2^31 bit operations at `n = 28`, against about 2^35 cycles
  measured for Gröbner. **That estimator figure is cited by the report, not computed here**; this
  domain does not run that library.

**What survives the correction is the growth rate**, and it is the reason the section is kept rather
than deleted. An algebraic attack that grows by *less* than one bit per bit of `n` must eventually
overtake any exhaustive search, however well optimised; one that grows by *more* never will. Mode A
fits 0.722 and Mode B fits 1.120. So the honest statement is: **Mode A's algebraic attack must
overtake search at some size this domain cannot reach, and Mode B's must not.**

And a loss for Gröbner here is a loss for *this* formulation in *this* engine. Mode B is modelled as
the record models it — `2n` unknowns, quadrics plus cubics — and an attacker is free to do
otherwise: eliminate `s` and solve degree-6 equations in `n` unknowns, guess bits first (hybrid), or
use an F4/F5 engine faster than PolyBoRi. None of those was run.

---

## 6. Why Mode A's verdict is "inconclusive", and why that is the useful result

The Mode A Gröbner track reports neither model: exponential RSS **2.5568** against polynomial RSS
**2.5745**, where the harness requires a factor of 3.0 before it will name a winner. That is not a
failed measurement. The track carries its own expectation, written into the harness before the run:
*expect a staircase, not a line — within one solving degree the cost is polynomial in `n`, and it
jumps when the degree steps up. A staircase fits neither model, so "inconclusive" here is a
description, not a failure.*

The measured medians are the staircase: 0.042, 0.063, 0.136 s at `n = 16, 18, 20`, then **1.135 s**
at `n = 22`, then 2.944, 5.348, 8.854. One step, between `n = 20` and `n = 22`, is larger than the
whole range on either side of it.

This is the domain's clearest worked example of the limit stated at the top: a curve measured below
the first step extrapolates to one answer and a curve measured above it to another, and neither
knows where the next step is. Every extrapolated row of the report inherits that objection.

---

## 7. What this domain does not establish

- **No production security.** Nothing was run at `n = 256`. The five extrapolated rows of the
  report's §4 are straight lines continued far outside the measured range — across factors of 13 to
  23 in size — and are printed so the measured growth rate can be set beside the record's formula
  and **for no other purpose. They are not security estimates.**
- **No statement about attacks that were not run.** No hybrid attack, no F4/F5 engine, no
  alternative Mode B formulation, no dual lattice attack, no side channel, no fault injection.
- **No algorithm comparison.** §5 above. The "finished first" column names a program, not an attack.
- **Nothing about the framing, the certificate or the proof system.** Those layers are deliberately
  absent; this domain attacks the primitives alone. The games against the full construction are
  domain 09's, and the reductions are domain 15's.
- **No re-derivation of the record's formulas.** 148.8 and 378.2 classical bits are quoted from the
  record as figures produced by a formula, and are set beside a measurement rather than confirmed
  by one.
- **No use of the read-only research tree at run time.** The record's parameters are recorded in
  this domain's own sources as named constants with their source lines.
