# The checker, and what it actually verifies

## What it is

A single Python file, 349 lines, 15,785 bytes, SHA-256
`6b7d8b71da21e57bf70b219707f5393dc004e88f0276da7dcc876c58eac22ecc`, held at
`src/operator_ledger_checks.py` in this domain. It is the document's own closing block, extracted by
a recorded command and byte-identical to it — see `VERIFICATION.md`.

Its docstring states its own scope, and that statement is accurate:

> Exact local mathematical checks, not a quantum attack or security proof.
> Standalone, Python 3 standard library. Prints its complete summary as JSON.
> Probability pass/fail decisions use integers and Fraction, not floating logs.

The only imports are `fractions.Fraction`, `itertools.product`, `itertools.combinations`,
`math.log2` and `json`. Nothing is fetched, nothing is timed from the clock, no random source is
read. Two runs of the same file produce byte-identical output, so a reported output block can be
diffed against a re-run without tolerance.

`math.log2` is used in one place only, `log_display`, and only to render a human-readable
`-5.3021…` beside an exact bound. No assertion and no pass/fail decision depends on it.

## How to run it, and what "PASS" means

```
. <env>/activate.sh                          # pinned interpreter; see the repository's environment notes
python3 src/operator_ledger_checks.py > /tmp/observed.json
diff results/operator_ledger_checks.json /tmp/observed.json      # expect no output
```

**Interpreter floor: Python 3.8.** The order-`r` rank enumeration calls `pow(a,-1,q)` — modular
inverse — at line 94, and the two-argument `pow` inverse was added in 3.8. The run recorded in
`VERIFICATION.md` used 3.12.3 and completed in 0.07–0.08 s wall, exit 0, empty stderr.

Each of the 23 groups is a sequence of plain `assert` statements ending in a `passed(name, detail)`
call. `passed` appends a row to the result list; it runs only if every assertion above it held. So a
row reading `"status": "PASS"` means exactly one thing: the assertions in that block did not raise,
this run. The failure mode is correspondingly blunt — `main()` is called only under
`if __name__=='__main__'` and its JSON is printed at the end, so a single failed assertion aborts
the run, prints **nothing** to stdout, writes an `AssertionError` traceback to stderr and exits 1.

That was tested rather than assumed. A scratch copy with one recorded expectation changed
(`[73,137,193,265]` → `[74,137,193,265]` in group 13) gave exit 1, **0 bytes of stdout**, and one
`AssertionError` on stderr. The pass criterion is a gate, not a label.

**Never run it with `-O` or `-OO`.** The entire pass criterion is `assert`, and `-O` strips
assertions, leaving a program that prints a well-formed summary of a run in which nothing was
checked. The negative control above demonstrates it: the same broken copy that exits 1 with no
output under a normal run exits **0 with the full 5,011-byte JSON and 23 groups marked PASS** under
`python3 -O`. Any harness that adopts this checker must invoke it without optimisation flags.

Above the floor, the result does not depend on the interpreter: the run was reproduced byte for byte
under 3.12.3 and again under 3.13.15.

## The exact-arithmetic building blocks

Everything below is written out in the file; a reader can check the checker's vocabulary in a few
minutes. This matters because "23 groups pass" is only worth what the primitives are worth.

| Primitive | What it is |
|---|---|
| `F = Fraction` | Every probability, cost and mass is a rational. No float enters a decision. |
| `ELL = 2^20`, `V = 2(21·2^20+1)`, `TAU = 1/24` | The ledger's leaf count, verifier-call count and total-error target, as integers. |
| `joint_raw(s,h,p)` | `((72+40ℓ)Q³ + 2v)/2^h + 20Q²p` with `Q = 2^s` — the ledger's borrowed constant (lines 74–76), implemented at checker line 18. This single expression is what most of group 13 tests. |
| `minimum_rounds(s,beta,h=512)` | Exact scan for the smallest `n` with `joint_raw(s,h,beta^n) ≤ TAU`; returns `None` if no such `n` exists, because `joint_raw(s,h,0) ≥ TAU` already. No search heuristic, no floating comparison. |
| `digits`, `prefix_count`, `box_mass` | Closed-form base-`b` digit counts for the product-box mass of Lemma 4. |
| `brute_box_mass` | An independent implementation: residue counts over all `2^h` integers, every permitted `t`-subset in every coordinate enumerated, maximum taken. Group 14 asserts the two agree. |
| `mm, tr, transpose, mv, normsq, eye, sub, psd2` | 2×2 linear algebra over `Fraction`. `psd2` decides positive semidefiniteness by the exact 2×2 test `a₀₀a₁₁ ≥ a₀₁²` on a symmetric matrix. |
| `rank_mod` | Gauss–Jordan rank over `F_q` using the modular inverse. |
| `rank_count` | The rank census `∏_{i<r}(q^m−q^i)(q^n−q^i)/(q^r−q^i)`, asserted integral before returning. |
| `dag_cost` | Work `Σgᵥ` and depth `dᵥ + max` over predecessors, from a topological node list. |
| `FIELDS`, `compatible` | The five-field compatibility record of `A28`. |

## The 23 groups, by what the code asserts

Line numbers are for `src/operator_ledger_checks.py`. "Witnesses" names the entry or lemma whose
claim the group's assertions bear on.

| # | Line | Group name | What the code asserts, from the code | Witnesses |
|---:|---:|---|---|---|
| 1 | 136 | L1 threshold meet | On the chain `{0, ¼, ½, 1}` the admissible set for the threshold meet is empty, so the result is `0`, not the input `¼`. One counterexample, exact. | L1 |
| 2 | 143 | L9/L10 majorization | For `p=(4/5,1/10,1/10)`, `q=(3/5,2/5,0)`, the normalized coordinatewise `max` is `(8/13,4/13,1/13)` and the normalized `min` is `(6/7,1/7,0)`; each fails at `k=1` against `p`. | L9, L10 |
| 3 | 151 | L35/L47 order | In the 2×2 product order, the maximum antichain has width 2 and lexicographic order on the second projection is not a linear extension. | L35, L47 |
| 4 | 156 | T7 cycle mean | `max(-1/1, -2/2) = -1` differs from `max(-1,-2)/2 = -1/2`. **Both values are literals**; the two traces are not computed from a matrix. | T7 |
| 5 | 161 | T8 eigenvector uniqueness | Two vectors, `(0,0)` and `(0,½)`, each satisfy `xᵢ = maxⱼ(Aᵢⱼ + xⱼ)` for `A = [[0,-1],[-1,0]]`, and are not translates of one another. | T8 |
| 6 | 166 | T42 softmin | The literal 2×2 matrix `[[-¼,¼],[¼,-¼]]` is symmetric with a negative eigenvalue (and its negation is PSD), so it is not a valid Hessian. **The matrix is a literal**; it is not derived by differentiating a softmin. | T42 |
| 7 | 179 | Q40/D9 signs | 54 exact cases (q ∈ {½,2,3} × x ∈ {⅓,1,2} × n ∈ 0..5) satisfy the `q`-commutator identity `Δ_q f(qx) − Δ_q f(x) = (q−1)Δ_q f(qx)` on monomials. Then `assert (1-2)==-1`, a **vacuous** restatement of the D9 sign claim. | Q40, D9 |
| 8 | 186 | I21/I33 entropy corrections | A uniform density on `[0,2]` translated to `[7,9]` has the same width and the same density `½`. Then `source_mass=1`, `correct_mass=½` are compared as **literals**. | I21, I33 |
| 9 | 195 | Contraction instruments | `KᵀK = ½I` for `K = ½[[1,1],[1,-1]]`, `KᵀK = (9/16)I` for `K = ¾I`, and `I − KᵀK ⪰ 0`. These are exactly Lemma 2's and Lemma 3's certificates, constructed. | Lemma 2, Lemma 3 |
| 10 | 201 | Spectral-radius substitution rejected | The nilpotent `[[0,2],[0,0]]` has `A² = 0` and spectral radius 0, yet maps `(0,1)` to a vector of squared norm 4 and fails the PSD certificate. Spectral radius is not a norm bound on a failure instrument. | A09 |
| 11 | 208 | Measurement order | `⟨v₀\|ZΠZ\|v₀⟩ = ¼` while `⟨v₀\|ΠZΠ\|v₀⟩ = ½`. Order matters; both computed. | Lemma 2, A10 |
| 12 | 213 | Marginals do not multiply | Two literals: `joint_bad = ½ > marginal_product = ¼`. An illustration of the point, not a computation — the correlated joint is never built. | A08 |
| 13 | 228 | QPT staged component bounds | For `s ∈ {32,64,92,128}`, scans for the exact minimum round counts and asserts them equal to `[73,137,193,265]` (ideal `β=½`) with `[88,165,233,320]` (robust `β=9/16`), each minimal in the asserted sense (`n` suffices, `n−1` does not); `joint_raw(128,512,1/2^128) > 1`; and `minimum_rounds(128,½,h=256)` is `None`. The **only** group whose numbers the ledger's headline rests on. | Lemma 3, Priority 1 |
| 14 | 245 | Generalized prefix-box lemma | Cross-checks `prefix_count` against brute-force digit enumeration (490 cases) and `box_mass` against `brute_box_mass` (156 cases) over bases 2–5, digit limits 1–5, radii 1–3, heights 1–6; then `box_mass(2,3,2,2) = 3/4`, `box_mass(512,3,2,324) = box_mass(512,3,2,512)` (saturation), and the 720-bit instance falls under `TAU`. The brute force is a genuinely independent implementation. | Lemma 4, A11 |
| 15 | 254 | Deterministic entropy | For four weight vectors and all 8 maps `{0,1,2}→{0,1}`, the maximum output weight is at least the maximum input weight — 32 cases. That is guessing-probability monotonicity for a deterministic classical map, which is the exact statement Lemma 6 needs. | Lemma 6, A14 |
| 16 | 262 | Good events and retry tail | With `d₁ = d₂ = ¼`, `ε = ⅓`, asserts `ε(1−d₁)/(1−d₁−d₂) = ½` where `½` is a **literal**; asserts `1−d₁−d₂ > 0`; and pins the exact truncation boundary `2^64·(759/1024)^519 ≤ 2^-160` **and** `2^64·(759/1024)^518 > 2^-160`. The boundary pair is real exact arithmetic; the conditioning half is an arithmetic identity at chosen parameters, and **no four-outcome space is constructed** despite the group's scope string. | Lemma 5, A13, A16 |
| 17 | 273 | Finite-field rank | Enumerates every matrix over `F_q` for `(q,m,n) ∈ {(2,2,2),(2,2,3),(2,3,3),(3,2,2)}` — `2⁴ + 2⁶ + 2⁹ + 3⁴ = 673` matrices — and asserts the rank census equals the closed form in every case, with the counts summing to `q^{mn}`. | Lemma 6, A15 |
| 18 | 278 | Work/depth and reduction composition | `dag_cost` on a 4-node DAG gives work 37, depth 7 — computed. Then `2·128==256` and `(λt. 3(2t+1)+4)(10)==67` — **arithmetic identities** wearing the label "affine resource maps composed explicitly". | Lemma 7, A04, A22 |
| 19 | 285 | Fixed-hash versus independent oracle | Over a 2-input, 4-output table space: 4 of 16 tables agree with a fixed value at the queried point, so the equality-test advantage is `1 − ¼ = ¾`. This instantiates the `1 − 2^-h` gap at `h=2`; it is not the deployed hash. | Lemma 8, A20 |
| 20 | 291 | Y1 minimax direction | For matching pennies, `maxmin = −1 < minmax = 1` — computed. Pure-strategy values do not coincide, so weak duality is strict here. | Y1 |
| 21 | 318 | H20/R36 counterexamples | Enumerates the 7 valid matchings between two two-point distributions with diagonal cost `((b−a)/2)²` and asserts `min(costs) = 2`, i.e. `W₂ = √2`; the "bottleneck distance is one" half is a **code comment**, not asserted. Then builds an explicit CPTP map `E_k = \|0⟩⟨k\|`, verifies `ΣE_k†E_k = I` as matrices and that it sends the two-qubit Bell state to `\|00⟩⟨00\|`. | H20, R36 |
| 22 | 325 | Quorum set intersection | All 441 ordered pairs of 5-subsets of `{0..6}` intersect in at least `5+5−7 = 3`. The counting fact `A24` states, exhaustively at small `N`. | A24 |
| 23 | 337 | Contract negative mutations | With a good 5-field record: each field set to `'incompatible'` and each field deleted is rejected (10 mutations), and a record matching itself is still `cryptographic_theorem_verified: False`. | A28 |

The nine stages of the final JSON are not a separate group: they are the per-`s` rows accumulated
inside group 13, plus the two top-level fields `robust_128_raw_bound_log2_display` and
`full_QPT128_established: false`.

## Where the code asserts less than its scope string

The scope strings are the ledger's prose about its own checks. Four of them overstate, and a reader
who reads only the recorded JSON table will be misled in these specific ways:

1. **Group 13** — "wrong event substitution remains forbidden" is not tested by this block. Nothing
   in group 13 touches an event field. The refusal lives in group 23, and there it is a check on
   `compatible()`'s five string fields, not on any mathematical event.
2. **Groups 4, 6, 8, 16** — the counterexample is carried by **literals**. `T7`'s two traces,
   `T42`'s Hessian, `I21`/`I33`'s two masses and group 16's conditioning value are written into the
   file as constants and compared with other constants or with a formula evaluated at chosen
   parameters. They check that the corrected value differs from the source value; they do not
   recompute it from the objects the amendment is about.
3. **Group 7** — the second half of "54 commutator cases and an odd-order difference
   counterexample" is `assert (1-2)==-1`. The commutator half is real.
4. **Group 18** — "affine resource maps composed explicitly" is two arithmetic identities. The DAG
   half is real.
5. **Group 12** — "perfectly correlated half-probability failures remain probability 1/2" compares
   two literals; no joint distribution over rounds is constructed.
6. **Group 21** — the bottleneck-distance half of the `H20` claim is a comment.

Fifteen amended entries are named by a group. On the stricter reading that a witness must *compute*
the corrected value rather than restate it, the entries with a computed witness are `L1`, `L9`,
`L10`, `L35`, `L47`, `T8`, `Q40`, `Y1`, `H20` and `R36` — **10 of the 15**. The five that fall away
are `T7`, `T42`, `D9`, `I21` and `I33`, each carried by a literal or by `assert (1-2)==-1`. Every
other group in the table witnesses a lemma, a contract or a negative result, not an amendment.
`docs/validation-status.md` carries that count and the check on the `113` claim.

## What the checker does not do

- **No quantum cryptanalysis is executed**, as the file's own scope string says. There is no
  quantum circuit, no simulator, no attack, no adversary.
- **It does not model the protocol.** No verifier, no sampler, no extractor, no signature scheme
  appears in it. Every group is a finite or rational-arithmetic fact about a *formula*.
- **It does not establish any of the seven open premises** listed in its own output: the actual
  joint relation decoder, a public conflict extractor without sidecar data, the `p_*` bridge for
  the actual protocol and sampler, concrete signature hardness at the reduction's resources, a
  compatible good-key event with a standardised algorithm adapter, the deployed hash's game
  properties, and concrete gate/depth/memory accounting.
- **It never certifies a theorem.** `cryptographic_theorem_verified` is the literal `False` in
  `compatible()`'s return, and group 23 asserts it stays `False` even for a record that matches
  itself. The final JSON carries `"full_QPT128_established": false`.
- **It does not check the deployed hash, the deployed permutation or the deployed parameter set.**
  Group 19 is a 2-input, 4-output table; group 13 is arithmetic on the borrowed expression.
- **It gives no error bars and no tolerance.** Being exact, it either holds or aborts. The evidence
  it produces is therefore of one kind only: a finite exact check. Everything else in the ledger —
  the 116 amendments, the eight sources, the seven premises — is outside it.

One structural consequence deserves naming, because it is the checker's real limit: the groups were
written by the same pass that wrote the corrections. Where a group asserts a literal value, the
literal is that pass's own corrected value, so the assertion cannot detect an error in the
correction itself. Only groups 14 and 17 contain an independently derived counterpart (brute-force
digit enumeration, and exhaustive matrix enumeration against a closed form), and those are the two
groups whose PASS carries information beyond self-consistency.
