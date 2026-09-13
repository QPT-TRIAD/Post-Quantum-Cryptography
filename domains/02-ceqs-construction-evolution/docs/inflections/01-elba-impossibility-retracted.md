# Inflection 1 — an impossibility claim is retracted (v0.4 → v0.5)

**Versions concerned:** v0.4 `docs/research-synthesis-final.md` → v0.5
`docs/formal-proof-stack.md`, with the retraction formally recorded in
`docs/proof-corrections-v0.5.md`.
**Date:** 8 September 2026.
**One sentence:** v0.4 declared exact 43-of-64 aggregation impossible with the 2025 succinct
aggregation suite; v0.5 showed that claim to be false as a theoretical statement and replaced it with
a size statement.

## What v0.4 asserted

v0.4's synthesis recorded that the 2025 VOLE-in-the-Head threshold-ring paper's succinct aggregation
"requires the aggregator to possess **more than `t`** valid signatures to convince the verifier that
at least `t` are known". Writing `q = 43` for the BFT finality threshold and
`Δ_ALBA(λ, ε, parameters)` for the required aggregation slack, the collector would need
`q_collect = q + Δ_ALBA`, while Byzantine-independent liveness with `n = 64, f = 21` supplies only
`n − f = 43` honest validators. Hence (`docs/research-synthesis-final.md:559–573`):

> `Δ_ALBA > 0 ⇒ the approximate succinct aggregate cannot be a Byzantine-independent 43-of-64
> finality primitive.`

v0.4 called this "a major result of the synthesis" and split the work into Mode A (exact, the
consensus-critical path) and Mode B (succinct aggregate, an optional optimization)
(`docs/research-synthesis-final.md:594–626`).

## What was wrong

Two separate errors were bundled into one claim.

1. **Wrong scheme name.** The source audit established that the CCS 2025 paper uses **ELBA (Expanded
   ALBA)**, not plain ALBA, for partially unique tagged signatures
   (`docs/formal-proof-stack.md:13`). The parameter structure is therefore `n_f < n_p`
   (completeness at `n_p` known items, knowledge soundness extracting strictly more than `n_f`), not
   the single threshold `t` that v0.4 reasoned about.
2. **Wrong conclusion from that parameter structure.** Setting `n_f = 42, n_p = 43` proves an exact
   43-signer lower bound at exactly 43 contributions:

   > `ELBA does not theoretically require more than 43 contributions to prove a 43-signer lower
   > bound.` (`docs/formal-proof-stack.md:50`)

   So `Δ_ALBA` does not have to be positive for a 43-of-64 quorum, and the impossibility statement is
   false as written.

The corrected conclusion is not that the path is open — it is that the obstacle had been mislocated
(`docs/formal-proof-stack.md:110`):

> `zero-slack ELBA is theoretically compatible with 43-of-64 liveness but catastrophically non-compact
> at these parameters.`

## The correction, in numbers

Telescope-style ALBA/ELBA equation (13) as the source writes it
(`docs/formal-proof-stack.md:55–85`):

```
u >= ( lambda_sound + log2 lambda_comp + 1 - log2 log2 e ) / log2( n_p / n_f )
```

| Parameters | Result |
|---|---|
| `λ_sound = λ_comp = 128`, `n_p = 43`, `n_f = 42` | `u ≥ 3991` repetitions |
| at the paper's ≈9.91 KB per linkable AES128 ring signature, ring size 64 | `3991 × 9.91 KB ≈ 38.6 MiB` |
| full participation `n_p = 64`, `n_f = 42` | `u ≥ 223` ≈ 2.2 MiB before overhead |
| plain concatenation of 43 signatures (`43 × 9.91 KB`) | `426.13 KB` ≈ 0.416 MiB |

Both paths exceed the 32,768-byte gate — one by three orders of magnitude, the other by a factor of
13. v0.5 therefore kept Mode A as the consensus-critical requirement and kept Mode B strictly as an
optimization that "must never replace Mode A's liveness-critical semantics unless the consensus fault
model is changed and re-proved" (`docs/research-synthesis-final.md:610–626`).

## Evidence that this was a correction

This inflection has a **documentary** record rather than a checker record; the sources say so
themselves.

- The retraction is tabulated explicitly in the v0.5 proof-status table
  (`docs/formal-proof-stack.md:1434`):

  | Result | Status |
  |---|---|
  | BFT conflict impossibility | proved conditionally |
  | **ELBA 43-of-64 impossibility** | **retracted: false as a theoretical statement** |
  | ELBA practical compactness at 43/42 | shown infeasible by published parameter formula |

- The successor document states the relation between the two versions in one line: "This replaces
  the stronger v0.4 impossibility claim." (`docs/formal-proof-stack.md:115`), and §17 repeats the
  full corrected derivation with the conclusion "This is stronger and more precise than saying ELBA
  is simply incompatible with BFT liveness" (`docs/formal-proof-stack.md:1280`).
- The stand-alone correction ledger keeps the three numbers side by side
  (`docs/proof-corrections-v0.5.md:8–12`): `u >= 3991` at 128/128 security, ≈38.6 MiB for the naive
  Telescope-style proof, `43 × 9.91 KB = 426.13 KB` for concatenation.
- **No checker exists for this inflection.** Nothing in `src/` tests ELBA, and the domain's
  verification record (`VERIFICATION.md`) therefore carries no runnable item for it. The numbers are
  reproduced by evaluating equation (13) as printed — arithmetic, not a program.

## Why the wrong turn is kept

The wrong version is kept in this repository on purpose: v0.4's claim is what caused the project to
separate an exact mode from a succinct mode at all, and the retraction is what redirected the next
four versions toward an exact, backend-neutral aggregator interface (Inflection 2). Deleting v0.4
would delete the reason the later architecture has the shape it has.

See also: `docs/research-synthesis-final.md` §12–13 (the v0.4 claim and the mode split),
`docs/formal-proof-stack.md` §0 and §17 (the correction), `docs/proof-corrections-v0.5.md`
(the three numbers), and Inflection 2 for what v0.6 did with the corrected picture.
