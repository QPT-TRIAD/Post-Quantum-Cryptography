# Conditioning arguments: why the tree cannot manufacture challenges

Source: `src/slh_tree_conditioning_audit.py` (v1.42). Script:
`python3 src/slh_tree_conditioning_audit.py` runs the 10 test groups and then prints the report; exit
0 on success. `--proof` prints the mathematical discussion. All paths are relative to the repository
root.

## 1. The claim that was audited

SLH-DSA verification walks a hypertree: it derives a digest and indices, reconstructs a FORS key,
then reconstructs successive XMSS roots and compares the final root with `PK.root`. The proposal
under audit was that this structure supplies "128 fresh one-bit challenges" whose behaviour can be
conditioned on, and that a bound of the form

```
ε_SLH  ≤  q_s · L / 2^λ  +  C(q_h)
```

could be obtained from it — with `L` called the number of leaves and `C` a nonnegative remainder.
Both parts of that proposal fail, and v1.42 shows why in a way that needs no new cryptography.

## 2. Theory used

| Theory | Statement **as used here** | What it justifies | Full / partial | Citation as the source gives it |
|---|---|---|---|---|
| FIPS 205 | Algorithms 13 and 20 (XMSS root reconstruction; the overall verifier), Table 2, §§9.2 and 11 | the facts that the verifier is deterministic for a fixed key, message, signature and hash implementation, and that it **generates no verifier challenges** | **partial** — the algorithm structure and the parameter labels, not any advantage bound | standard |
| Barbosa, Dupressoir, Hülsing, Meijers, Strub, ASIACRYPT 2024 (ePrint 2024/910) Theorems 1–4 | a published decomposition of the SPHINCS+ advantage into named terms, using an exhaustive case distinction | the 10-term ledger of eq. (7) and the coefficient 3 on the `TCR_F` term | **partial** — the games and advantages, not the constants | cited with theorem numbers |
| Hülsing–Kudinov, ASIACRYPT 2022 (ePrint 2022/346) | a Winternitz-factor correction warning | quality check on the published decomposition; the correction must be counted exactly once and the full text was not available | **partial** — abstract only | as given |
| Boyer–Brassard–Høyer–Tapp, arXiv quant-ph/9605034 §2 eq. 2 | amplitude after `j` iterations is `sin²((2j+1)θ)` | eq. (9), the exact ideal-search polynomial | **partial** — the amplitude formula only | as given |

## 3. Refactoring invariance

Let `V(pk, m, sig)` be a verifier and suppose a proposed sequential implementation computes
predicates `C₁, …, C_r` such that, for every input and every fixed oracle,

```
AND_i C_i(pk, m, sig)  =  V(pk, m, sig).                       (1)
```

Assume the adversary interface and freshness rule are unchanged and no new challenge interaction is
introduced. Then for every adversary `A`,

```
Pr[fresh and AND_i C_i(A's output)]  =  Pr[fresh and V(A's output)].   (2)
```

*Proof.* The event indicators agree pointwise for every experiment outcome; averaging over keys,
adversary randomness, quantum measurement outcomes and any initially sampled oracle preserves the
equality. A quantum adversary does not invalidate the pointwise implication for its final classical
output. Verification work may change; the accepted language does not.

The consequence is stated plainly in the source and is worth quoting, because it is easy to
over-read: "splitting a root comparison into bits, or splitting a computation into 128 stages, cannot
by itself improve the signature's acceptance probability. A decomposition might help **prove** an
existing bound if new conditional hardness lemmas are established, but it does not manufacture those
lemmas. This is not an assertion that deterministic verifiers cannot be secure."

## 4. Why a per-step conditional bound is not free

Take `E` with probability `p > 0` and define `C_i = 1_E` for every `i`. Then

```
Pr[all C_i = 1] = p,
Pr[C₁ = 1]      = p,
Pr[C_i = 1 | previous checks passed] = 1   for every i ≥ 2.    (3)
```

The chain rule is correct; the proposed uniform per-step bound is false for this example. Repeating a
deterministic verifier on the same candidate has exactly this structure, even when `p` is very small.
That is the whole obstruction in one line: conditioning on the event that the previous checks passed
tells you nothing when the checks are the same event.

The source notes what (3) is *not*: it is not a claim that the verifier is broken, and not a claim
that conditioning is illegitimate in general. It is a claim that a per-step bound has to be proved
for the specific experiment, and that repetition alone does not supply it.

## 5. Whole-game security does not bound a conditioned subcheck

If `F` is the full fresh-forgery event and `G` a preceding pass event, then

```
Pr[F | G]  =  Pr[F and G]/Pr[G]  ≤  min(1, ε/Pr[G])            (4)
```

whenever `Pr[F] ≤ ε` and `Pr[G] > 0`. It is **not** generally `≤ ε`; for `G = F` the conditional
probability is one. And if `F` implies a partial check `V_i`, then `Pr[F] ≤ Pr[V_i]`, so an upper
bound on `F` is not an upper bound on `V_i`. The source records that the comparison proposed in the
research trail reverses this implication — a bound on the whole game does not carry down to the
parts.

Consequently, writing

```
Pr[V_i passes | earlier passes]  ≤  Adv_SLH(B)
```

requires a **new reduction `B` for that exact conditional experiment**. Conditioning on a rare
success event is not automatically an efficient QPT simulation, and "it cannot be implemented by
merely declaring a new probability space while retaining the original resource budget or copies of a
quantum residual state."

**The min-entropy argument is misplaced.** If `Y = f(public transcript)` is deterministic, then for
every transcript `z` with positive probability, `max_y Pr[Y = y | transcript = z] = 1`. `Y`'s
conditional guessing entropy is therefore **zero**. Public path indices and public root bits are not
secret one-bit challenges. The source guards against the obvious misreading: this "does not make a
hash preimage easy to compute: computational difficulty of producing a matching preimage is a
different claim from hiding the target hash value."

**Freshness is a log property.** Freshness is the absence of the final message and context from the
complete signing-query log. Randomizing a digest does not enforce message freshness, and does not
prove that two digest values cannot coincide. The source's phrasing is exact: "A collision or repeated
randomizer is not eliminated by naming the digest 'fresh'."

## 6. The proposed numerical expression, evaluated

The research trail proposed, without a matching theorem,

```
ε_SLH  ≤  q_s · L / 2^λ  +  C(q_h).                            (5)
```

Even granting (5), the arithmetic refuses to certify the target:

| Case | Right-hand side of (5) |
|---|---|
| `λ = 128`, `q_s = 1`, `L = 2` | at least `2^−127` |
| `q_s = L = 1`, `C = 0` | **equals** `2^−128` rather than lying strictly below it |
| `q_s = 2^20`, `L = 2^9` | the first term alone is `2^−99` |

For an integer `q_s·L ≥ 1`, a target `2^−s`, and a separately supplied `C`, the expression certifies
the target only if

```
C < 2^−s        and        2^λ ≥ q_s·L / (2^−s − C).           (6)
```

At `C = 0`, `λ ≥ s + ⌈log₂(q_s·L)⌉` suffices for this expression. The source labels all of this
correctly: it is "algebra about (5), not an endorsement of (5) as an SLH security theorem". And it
draws the sharp distinction that a careless reader would miss: "An upper bound above the target does
NOT prove that an actual forgery probability exceeds the target; it means the bound cannot certify
it."

The report prints the `2^−127` line directly: `Claimed RHS at q_s=1, leaves=2, lambda=128: 2^-127
(before other terms).`

## 7. The constructive route: an exhaustive-case ledger

If the tree structure cannot be conditioned on, what can be done? The answer in v1.42 is the ordinary
one: use the published proof. Barbosa et al. bound their fixed-length stateless hypertree game by
three alternatives — WOTS-TW forgery, WOTS-key compression collision, or tree-hash collision — using
an exhaustive case distinction and summing the bounds. Those are **alternative explanations of an
accepted forgery, not independent events that must all occur**, which is why summing is legitimate
and why a product would not be.

Combining Theorems 4, 1, 2 and 3 within that paper's stated games, and abbreviating each advantage by
its role:

```
E_paper = e_SKG + e_MKG + e_ITSR + e_DSPR + 3·e_TCR_F
        + e_FORS_tree + e_FORS_compress
        + e_WOTS + e_HT_compress + e_HT_tree,                  (7)
```

and the paper's EUF-CMA advantage is at most `E_paper`. Ten distinct terms. The coefficient on
`TCR_F` is 3, and the script tests that a nested substitution of Theorem 4 into Theorems 1 and 2 and
then Theorem 3 reproduces the expanded ledger exactly, with the distinct tree-hash terms **not**
merged. Test 07 checks the other direction: a missing term raises rather than silently becoming zero.

Two further identities belong to the ledger.

**Hypertree target counts.**

```
T_HT_tree = 2^h − 1,        h′·d = h.                          (8)
```

**One Grover iteration.** For an ideal search with success probability `p` per iteration, one
iteration of the amplitude recurrence gives

```
p(3 − 4p)².                                                    (9)
```

The source labels (9) precisely: an exact ideal-search polynomial, "not an upper bound on SLH
forgery". Test 09 checks that one iteration beats a random guess, that it equals 1 at `b = 2`, and
the amplitude recurrence itself.

## 8. Tests

`python3 src/slh_tree_conditioning_audit.py` runs 10 test groups and then prints the report; exit 0.

| Group | What it asserts |
|---|---|
| 01 | bitwise refactoring equals the whole comparison (256 candidates × 16 repetitions) |
| 02 | repetition does not amplify; conditioning on success can be 1; `postselection_bound` |
| 03 | a known public value has maximum probability 1 |
| 04 | the proposed formula: equals `2^−128` at `q_s = L = 1`, `2^−127` at `L = 2`, `2^−99` at `q_s = 2^20`, `L = 2^9` |
| 05 | the first-explanation selector partitions the cases |
| 06 | the nested Theorem 4 ← 1 ← 2 and 3 substitution equals the 10-term ledger, with distinct `TRH` terms not merged |
| 07 | a missing term raises rather than becoming zero |
| 08 | the hypertree target identity and `h′·d = h` |
| 09 | one Grover iteration beats a random guess, equals 1 at `b = 2`, and satisfies the amplitude recurrence |
| 10 | `64·2^−134 = 2^−128` |

## 9. Sizes and cost

| Quantity | Value |
|---|---|
| Source file | 22,746 bytes, 500 lines |
| Recorded runtime | 0.003 s (10 tests), exit 0 |
| Report length | 2,100 bytes |
| Ledger | 10 distinct terms; `TCR_F` coefficient 3 |
| Parameter comparison printed | 128s `(n = 16, h = 63, d = 7, h′ = 9)`, 128f `(16, 66, 22, 3)`, 256s `(32, 64, 8, 8)` |

The report's two status lines are the domain's conclusion in its own words:

```
SLH TREE CONDITIONAL LIMIT: UNESTABLISHED
CONCRETE QPT-128 SIGNATURE BOUND: UNESTABLISHED
```

and its closing line, which is a standing instruction rather than a remark: "No parameter-set label or
finite test result is a security certificate."

## 10. Packages and tools used

Python standard library only: `dataclasses`, `fractions`, `itertools`, `argparse`, `unittest`. The
parameter set `PARAMETERS` and the ledger coefficients `COEFFICIENTS` are data tables in the file.
Every probability comparison is exact rational arithmetic; no decimal, no floating point, no external
package.

## 11. Validation status

- **Proven.** Eqq. (1)–(4), the min-entropy observation, the algebra of eqq. (5)–(6), the ledger
  identity (7) as a substitution check, the counting identity (8), and the ideal-search polynomial
  (9).
- **Measured.** The ten finite test groups.
- **Not established.** Every one of the ten advantage bounds for FIPS 205 in a stated quantum model;
  the tweakable-hash-to-SHAKE bridge that would connect the ledger to a deployed hash; and the
  Winternitz-factor correction, whose full source was not available and which must be counted exactly
  once.
- **Missing for acceptance as a standard proof.** For each of the ten terms: a statement of the game,
  the reduction, the resource count of the reduction adversary, and the hash property it consumes.
  The ledger gives the shape; it does not give the terms.

## 12. Open items

1. Ten advantage bounds, each with its own game and reduction, none of which exists here.
2. The Hülsing–Kudinov Winternitz-factor correction is a warning that could change a coefficient.
   The full text was not available, so the correction is recorded as a warning, not applied.
3. No bridge from tweakable hash functions as modelled in the paper to SHAKE256 as deployed.
4. The `C(q_h)` remainder of eq. (5) is never specified, and eq. (6) shows the expression certifies
   the target only for a strictly smaller `C`.
5. Freshness remains a log property; no digest randomization route is proposed or claimed.
