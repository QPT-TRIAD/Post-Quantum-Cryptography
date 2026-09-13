# The hybrid sampling bound: a refuted bound and what replaced it

Source: `src/hybrid_sampling_bound_audit.py` (v1.41). Script:
`python3 src/hybrid_sampling_bound_audit.py` runs the 10 test groups and then prints the report; exit
0 on success, exit 1 if a test fails. `--proof` prints the module header. All paths are relative to
the repository root.

This document is the domain's clearest negative result. A reader who takes one thing from this
domain should take this one.

## 1. The claim that was audited

The proposal under audit was that the signature term of the conflict bound could be discharged by a
concentration inequality over the sampling behaviour of a publicly prepared GHZ state:

```
ε_SLH  :=  exp(−256 Δ²).
```

At `Δ = 1/2` the exponent is 64, and `exp(−64) ≈ 1.6·10^−28`. The expression is the one-sided
Hoeffding bound `exp(−2NΔ²)` at `N = 128`; `256 = 2·128`. The proposal thus reads a 128-qubit state
as 128 independent verification trials whose mismatch rate concentrates.

## 2. What is refuted, and what is not

v1.41 states the result twice, in the two places a reader will look first:

- §1: "the proposed `exp(-256 Delta^2)` signature-forgery bound **is not established**";
- §6: "**There is no justified substitution** `epsilon_SLH := exp(-256 Delta^2)`".

Both statements are about the **substitution** — about using that expression as the value of
`ε_SLH` in the quorum bound. Neither refutes Hoeffding's inequality:

- **Hoeffding 1963 Theorem 2 is not refuted.** It is a theorem, and v1.41 reproduces its
  one-sided form in eq. (4) and its standard proof in §3.
- **The arithmetic of the expression is not refuted.** v1.41 §5 evaluates
  `b_H = 2NΔ²/ln 2` exactly, and the script prints the values: at `N = 128`, `Δ = 1/4` gives
  23.083121, `Δ = 1/2` gives 92.332483, and `Δ = sqrt(ln 2/2) ≈ 0.588705` gives 128.

What fails is the *application*: the bound requires either independent trials or a **proved**
sequential conditional-mean premise, and the correlated public GHZ sampling proposed for this
construction supplies neither. The source's own summary is that a "Hoeffding substitution with
`Delta=1/2` fails because its probabilistic premises have been dropped".

The consolidated theory index summarises this entry as "refutes the proposed `exp(−256Δ²)` bound".
That summary is right about the conclusion and slightly wide about the object, and the README records
the difference. The form used in this document is the narrower, supported one.

## 3. The counterexample

One `n`-qubit GHZ state is not `n` independent verification trials. Computational-basis measurement
gives `X₁ = … = X_n = B` with `B` a fair bit. In this distribution every `E[X_i] = 1/2`, but

```
Pr[(X₁ + … + X_n)/n = 0]  =  1/2,
```

which exceeds `exp(−n/2)` for every `n ≥ 2`. The point is not subtle and does not need the quantum
formalism: the variables are perfectly correlated, so the average concentrates nowhere. The same
failure appears in the all-pass test of the script: for `n ∈ {2, 32, 64, 92, 128}` the correlated
all-pass probability is `1/2`, which is greater than the Hoeffding bound throughout.

The source is careful about the status of the illustration: "These `X_i` are an illustrative
correlated distribution, not a specified decoy test." It is a counterexample to the *inference*, not
an attack on a construction.

A second, independent obstruction sits beside it. The state is public and efficiently preparable.
For any verifier accept effect `0 ≤ M_{k,x} ≤ I`, even one chosen using secret verifier randomness
`k`,

```
Pr[accept honest state | k, x]   =  Tr(M_{k,x} ρ_x)
                                 =  Pr[accept reproduced state | k, x],
```

because both tests receive the same density operator and measurement outcome probabilities are
linear in it; averaging over `k` preserves the equality. Secret measurement choices alone therefore
do not distinguish an honest state from a reproduced one, and the state contributes **no** positive
honest-versus-reproduction mismatch gap `Δ`. For the ideal state-only projector
`Π = |ψ_n⟩⟨ψ_n|`, the reproduced state passes with `Tr(Π²) = Tr(Π) = 1` — acceptance of *that state
test*, which is not probability one of forging a signature.

## 4. Valid replacements

The audit does not leave the hybrid unsupported. Four routes are given, each with its premise stated.

**(a) Projection, which needs no concentration at all.** For one common experiment, let `T` and `S` be
the events that the respective components validate the fresh output. Then

```
Pr[T and S]  =  Pr[T]·Pr[S | T]  ≤  min(Pr[T], Pr[S]).
```

Because a reduction `B` receives the SLH challenge public key, generates the traditional key locally,
forwards SLH signing requests, supplies traditional signatures locally, and returns the SLH component
of a fresh accepted hybrid output,

```
Adv_Hybrid(A)  ≤  Adv_SLH(B),
```

with **no probability loss**. This is the route the domain actually uses (see
[`signature-reductions.md`](signature-reductions.md) §4), and it makes the concentration question
unnecessary for the hybrid — which is worth saying plainly, because it means the refuted bound was
never load-bearing for the hybrid's security.

**The product rule is not available as a shortcut.** Independent keys do not make `T` and `S`
independent: they share an adversary, a transcript and an output. The counterexample `T = S = E` with
`Pr[E] = 1/2` gives an intersection of `1/2` and a product of marginals of `1/4`. A general product
rule for advantages is thereby disproved. The script tests this over all 4-atom laws with
denominator 8.

**(b) Conditional Hoeffding.** Take independent `X_i ∈ [0,1]` representing mismatches, `μ = N⁻¹Σ E[X_i]`,
and suppose acceptance requires `X̄ ≤ a` while every relevant attack satisfies `μ ≥ a + Δ` with
`Δ > 0`. Hoeffding gives

```
Pr[accept]  ≤  exp(−2NΔ²).                                    (4)
```

Independence can be replaced by a proved sequential condition, which is what an adaptive adversary
needs. Let `F_i` be the classical history through measured outcome `i` and `μ_i = E[X_i | F_{i−1}]`.
Require `μ_i ≥ a + Δ` almost surely for every `i` and every allowed attacker. Then (4) still holds:
`D_i = X_i − μ_i` is conditionally centered with conditional range width at most one, the conditional
exponential-moment lemma gives `E[exp(−λD_i) | F_{i−1}] ≤ exp(λ²/8)`, iterated conditioning gives
`E[exp(−λΣD_i)] ≤ exp(Nλ²/8)`, acceptance implies `ΣD_i ≤ −NΔ`, Markov bounds the probability by
`exp(−λNΔ + Nλ²/8)`, and `λ = 4Δ` proves (4).

The premise is the whole content, and the source says exactly how far it reaches: "This derivation
applies to the classical outcomes of a quantum experiment only if the conditional-mean premise is
proved for all allowed quantum strategies and their residual states. It does not assume that quantum
measurements automatically establish that premise." The correlated GHZ example fails this stronger
premise too: after observing `X₁ = 0`, the next conditional mismatch mean is zero.

**(c) The exact all-pass product — the sharpest route.** Let `V_i` indicate a passed check and
suppose that, for every permitted adversary and every reachable prior transcript on which all earlier
checks passed,

```
Pr[V_i = 1 | that transcript]  ≤  r_i.                        (5)
```

The `r_i` are **fixed upper bounds, not guessed marginal frequencies**. With `G_i` the event that the
first `i` checks all passed, `Pr[G_i] ≤ r_i·Pr[G_{i−1}]`, so by induction `Pr[G_N] ≤ ∏ r_i`. In
particular, if every `r_i = 1/2`,

```
Pr[all N checks pass]  ≤  2^−N.                               (6)
```

This is a legitimate product of **conditional** guarantees, and it needs neither independent keys nor
independent trials. At `N = 128` and `r_i = 1/2` it gives **exactly** `2^−128`.

**(d) The exact binomial tail with `t` tolerated failures.** Under the stronger premise that
`Pr[V_i = 1 | F_{i−1}] ≤ r` holds on *every* reachable history including previous failures, the
mismatch count stochastically dominates `Bin(N, 1−r)`, so

```
Pr[at most t mismatches]  ≤  Σ_{j=0..t} C(N,j) (1−r)^j r^(N−j).   (7)
```

The proof is an explicit coupling of the classical outcome law: at step `i` draw a fresh uniform
`U_i`, set `X_i = 1[U_i ≤ p_i(history)]` and `Y_i = 1[U_i ≤ 1−r]`; this realises the adaptive law for
`X`, gives independent `Bernoulli(1−r)` variables `Y`, and `X_i ≥ Y_i` pointwise. The source notes
this is "a mathematical coupling of measured classical outcomes, not copying quantum registers".

At `r = 1/2` and `N = 128`: `t = 0` gives exactly `2^−128`, and `t = 1` gives
`129·2^−128 ≈ 2^−120.988773` — the value the report prints as 120.988772745.

**What none of these routes supplies.** Each is conditional. To bound a *signature forgery*, one must
additionally prove that a fresh accepted forgery implies `G_N`, and that (5) holds for that actual
cryptographic experiment. The source states it directly: "No such bridge or `r_i = 1/2` guarantee is
supplied by the public GHZ state. For its ideal projector test, reproduction instead gives
`r_i = 1` on every surviving path." Zero tolerance also causes honest rejection under noise, so
correctness and adversarial soundness must both be established for an actual protocol.

## 5. Numbers, with their status

The report prints, in order:

```
N=128, Delta=1/2: Hoeffding failure exponent = 92.332482617
N=128, all-pass conditional r=1/2: exact endpoint = 2^-128
N=128, one failure allowed, r=1/2: failure exponent = 120.988772745
Public GHZ projector reproduction: state-test acceptance = 1
target | Hoeffding N at Delta=1/2 | all-pass N at r=1/2
    32 |                          45 |                    32
    64 |                          89 |                    64
    92 |                         128 |                    92
   127 |                         177 |                   127
   128 |                         178 |                   128
   129 |                         179 |                   129
   134 |                         186 |                   134
   136 |                         189 |                   136
No sampling endpoint is substituted for epsilon_SLH.
```

Two details about that table deserve care. The two columns use **different bounds** — a loose
Hoeffding estimate and a sharp conditional all-pass bound — so "Hoeffding needs 178 trials for 128
bits while all-pass needs 128" is a statement about the bounds, not about the state. And the all-pass
column also requires all-pass acceptance, so the two columns are not alternatives for the same event.
The source is explicit that "failure of a loose Hoeffding estimate to reach 128 does not prove
impossibility", and equally explicit that "neither column makes the public-state proposal secure by
increasing `N`".

The boundaries printed here are computed in 80-digit `Decimal`, and the source records the status:
those decimal checks "are numerical validation, not interval-certified proofs". The script's tests do
pin the boundary from both sides in exact rational arithmetic as well: `92.33248 < 64/ln 2 <
92.33249` and `0.588705 < sqrt(ln 2 / 2) < 0.588706`.

## 6. Consequence for the quorum bound

Under the reduction's premises, with at most 21 adaptive corruptions among 64 seats, the signature
term is

```
p_conflict  ≤  κ_E + L_E (δ_B + 64·ε_SLH),                     (9)
```

and the audit's conclusion about the substituted value is unambiguous: "There is no justified
substitution `epsilon_SLH := exp(-256 Delta^2)`." SLH-DSA's numerical bound must match its hash
properties, parameter set, oracle model, signing interface and resource budget; FIPS 205 §11
describes EUF-CMA strength categories through resource comparisons, not a qubit count and not an
automatically applicable failure probability.

For illustration only — and the source labels it as illustration — if a valid primitive bound
`ε_SLH ≤ 2^−b` were established with `L_E = 1` and `κ_E = δ_B = 0`, then (9) requires `b ≥ 134` for
`p_conflict ≤ 2^−128`, and reserving one quarter of the total failure budget for the signature term
requires `b ≥ 136`. Those are inherited reduction budgets, not established primitive advantages and
not sample-count prescriptions.

The public-state simulation contributes a resource cost of `129c` gates for `c` independently
prepared copies, unless already counted, and **no** success-probability multiplier. A gate count and
a probability are different currencies, and the audit's closing line holds the whole domain to that
distinction: "QPT denotes quantum polynomial-time adversaries. A 128-qubit register, a bound
`2^-128` on a specified event, and a lower bound of `2^128` operations are different assertions.
None may be silently substituted for another."

## 7. Tests

`python3 src/hybrid_sampling_bound_audit.py` runs 10 test groups and then prints the report; exit 0.

| Group | What it asserts |
|---|---|
| 01 | the `T = S = E` counterexample: intersection 1/2 versus product 1/4 |
| 02 | the intersection bound `≤ min` over all 4-atom laws with denominator 8 |
| 03 | the GHZ projector identity `Π² = Π`, `Tr Π = 1` |
| 04 | correlated bits: all-pass probability 1/2, and `0.5 >` the Hoeffding bound for `n ∈ {2, 32, 64, 92, 128}` |
| 05 | the adaptive law with pass probability `≤ 1/2` obeys `2^−n` and both the binomial and Hoeffding tails (`n ≤ 8`) |
| 06 | the binomial endpoint is exact, and the IID law attains the tail |
| 07 | `t = 1` gives `129·2^−128`; `N = 136` is the first trial count reaching `2^−128` and 135 is insufficient |
| 08 | the sample thresholds 45/89/128/177/178/179/186/189, plus `92.33248 < 64/ln 2 < 92.33249` and `0.588705 < sqrt(ln 2/2) < 0.588706` |
| 09 | `Δ = 0` and `r = 1` give no amplification |
| 10 | `64·2^−134 = 2^−128` and `64·2^−136 = 2^−130` |

Groups 05–07 are the ones that carry the replacement results; group 04 is the counterexample; group
09 is the guard against reading amplification into a parameter that has none.

## 8. Sizes and cost

| Quantity | Value |
|---|---|
| Source file | 23,658 bytes, 524 lines |
| Recorded runtime | 0.028 s (10 tests), exit 0 |
| Report length | 2,269 bytes |
| Public-state preparation | 129 logical gates per copy at `n = 128` (from `src/phase_ghz_security_check.py`); `129c` for `c` copies |
| Decimal precision | 80 digits, explicitly **not** interval-certified |

## 9. Packages and tools used

Python standard library only: `decimal` (with `prec = 80`, `ln`, `exp`), `fractions`, `itertools`,
`math.comb`, `argparse`, `unittest`. `decimal.Decimal` is used for the transcendental expressions and
`fractions.Fraction` for every exact probability comparison. No external library, no interval
arithmetic package, and no formal prover.

The limitation of the decimal route is recorded by the source and repeated here: the decimal checks
are "numerical validation, not interval-certified proofs". The general statements above are proved in
the text; the printed digits are a check on them, not a substitute.

## 10. Validation status

- **Proven.** Eq. (1) (probability), eq. (2) (reduction), eq. (3) (density-matrix linearity); the
  conditional Hoeffding derivation under its stated premise; the all-pass product bound under (5);
  the binomial tail and its coupling under the uniform premise.
- **Refuted as used.** The substitution `ε_SLH := exp(−256Δ²)`, for want of the premise. This is the
  domain's headline negative result.
- **Torn down.** The general product-of-advantages rule for the AND hybrid.
- **Measured, not certified.** The 80-digit decimal evaluations.
- **Open.** "An applicable concrete SLH signature-security bound" — the source's own closure line
  for this file. Also open: any bridge from a real cryptographic experiment to the premises of (5),
  and any treatment of honest rejection under the zero-tolerance reading.

## 11. Open items

1. No concrete SLH-DSA bound is supplied, and the audit explicitly refuses to supply a sampling
   endpoint as one.
2. The conditional-mean premise of the sequential Hoeffding form is not proved for any quantum
   strategy set used here.
3. The bridge from "a fresh accepted forgery" to the all-pass event `G_N` does not exist.
4. Zero-tolerance acceptance and honest rejection under noise are not balanced; no protocol-level
   error parameter is chosen.
5. The public-state reproduction result kills the authentication-gap route, and no other route
   through the phase state was found. See [`phase-ghz-security-check.md`](phase-ghz-security-check.md).
