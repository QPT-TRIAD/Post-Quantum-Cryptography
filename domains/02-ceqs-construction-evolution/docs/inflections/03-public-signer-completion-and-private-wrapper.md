# Inflection 3 — both halves of the fork get a construction (v0.8 → v0.9)

**Versions concerned:** v0.8 `docs/public-signer-theoretical-completion.md` and v0.9
`docs/quantum-lift-private-wrapper-proof.md`, both following the v0.7 target split (Inflection 2).
**Date:** 8 September 2026.
**One sentence:** the public-signer target was completed at the abstract level by reducing it to
monotone-policy aggregate unforgeability, and the hidden-signer target was reduced to the same
public-signer object placed inside a zero-knowledge wrapper — which removed the previously assumed
need for a specialized compact threshold-ring backend.

## What was missing after v0.7

v0.7 had split the target (B0: public bitmap; B1: hidden signers) and proved that conflict
accountability by itself needs no conflict-extractable tags. It left both halves marked
"practical < 32 KiB backend: open". What neither half had was a *reduction*: a named primitive whose
security, if it existed, would imply the quorum property.

## v0.8 — B0 reduced to a monotone policy

The construction of the document:

1. **A bitmap induces a monotone policy.** For a public signer bitmap `B`, define
   `f_B(z_1, …, z_n)` to be the conjunction of the identities claimed by `B`
   (`docs/public-signer-theoretical-completion.md:155–182`): `f_B(z) = 1` exactly when
   `supp(B) ⊆ supp(z)`. This is the precise sense in which "these 43 seats signed" is a policy and
   not a threshold.
2. **The aggregate verifier takes the policy as input.**
   `AggVerify(crs, f_B, vk_hat, M, sigma_hat) = 1` (`:469–475`), which is exactly the interface of
   monotone-policy aggregate signatures as defined by Brodsky, Choudhuri, Jain and Paneth
   (EUROCRYPT 2024, `:46`); that paper's construction explicitly supports weighted threshold
   policies, of which `f_B` is one (`:730`).
3. **Three reductions follow**, all stated conditionally on that primitive
   (`:477–700`): soundness `Adv^{SetFrame}_{AQC} ≤ Adv^{UF}_{MPAgg}` (`:484–486`); conflict
   extraction, which returns exactly `supp(B0 ∧ B1)` — the seats that claimed in both certificates;
   and the BFT conflict composition
   `Adv^{BFTConflict}_{B0} ≤ 2·Adv^{UF}_{MPAgg} + Adv^{BaseSafety}` (`:694–700`).
4. **A numeric correction.** The current Lemur paper reports **185.5 KB** for its `N = 1024`,
   `τ = 20`, 128-bit aggregate profile, not the 201.2 KB carried since v0.7 — stated explicitly as a
   correction carried forward from the v0.7 validation and as not affecting any theorem
   (`:10–19`), and repeated in the practical-status section (`:1021`).

The claim the source makes for itself is precise and is repeated here unchanged: "Target B0 is
theoretically solved at the abstract cryptographic level" (`:811`). The same section states the two
things it is not: the monotone-policy schemes are asymptotic/theoretical rather than a production
benchmark, and it remains unresolved whether the full monotone-policy BARG/vPIR stack has a published
QPT theorem matching the required properties (`:878`, `:898`, `:1016`). The document also records a
concurrent engineering alternative — transferable quorum certificates replaced by distributed local
certificate events built from ordinary signatures and approval broadcast — and classifies it as an
engineering escape hatch rather than a solution of the aggregation problem (`:985–1005`).

## v0.9 — B1 reduced to B0 plus a wrapper

v0.9's move is a decomposition
(`docs/quantum-lift-private-wrapper-proof.md:291–470`):

```
B1 certificate = [ public-signer exact aggregate as hidden witness ]
               + [ zero-knowledge wrapper ]
               + [ public conflict-extractable tag list ]
```

The wrapper's obligations are stated as eight clauses PW1–PW8: **PW1** exact hidden threshold,
**PW2** bitmap-derived policy, **PW3** hidden aggregate verification, **PW4** trace binding,
**PW5** mask binding, **PW6** CET generation, **PW7** bijection, **PW8** public uniqueness
(`:377–470`). The theorem then proceeds from PW1 (exact hidden threshold) and PW3 (an accepted
public-signer aggregate for the bitmap policy) to the hidden-signer properties, with PW4–PW7 ranging
over the same bitmap, so the CET list and the aggregate cannot refer to different signer sets
(`:550–636`). The source calls this "the private-wrapper analogue of v0.6's same-hidden-set theorem,
but it no longer depends on a threshold-ring proof" (`:636`).

Two consequences the source draws explicitly:

- **The hidden bitmap and hidden aggregate do not contribute to public certificate size**
  (`:890–898`); at the then-current scalar profile the public tag list is
  `|E| = 43 × 32 = 1376 bytes` (`:898`), which is where v0.9's repeated "1376 bytes" figure comes
  from, and the reason the hidden-signer branch looked affordable.
- **A specialized anonymous threshold-ring signature is no longer necessary**
  (`:905–920`), summarised as "The threshold-ring machinery can be replaced by: public-signer exact
  aggregate as hidden witness + zero-knowledge wrapper + public CET list".

The same document reduces B0's own quantum question to a specific primitive chain (§§1–5; Q1–Q6 in
§21, `:935–965`) whose two remaining blocks it names as QPT MPA adaptive-subset extraction and QPT
CET trace-soundness (`:967`).

## Evidence that these were corrections

Both versions ship a checker, and both checkers' recorded results are re-runnable in this domain.

**v0.8 — `src/ce_qs_bitmap_policy_checker.py`** (`results/ce_qs_bitmap_policy_checker.txt`):

```
PASS bitmap_policy_equivalence n=3
PASS bitmap_policy_equivalence n=4
PASS bitmap_policy_equivalence n=5
PASS bft_intersection n=4 f=1 q=3 minimum=2
PASS bft_intersection n=7 f=2 q=5 minimum=3
EXPECTED-FAIL unbound_bitmap_attack blocked_by=f_B
PASS n=64 bitmap_size_bytes=8
```

The `f_B` equivalence is checked **exhaustively** at `n = 3, 4, 5` — all bitmaps against all signer
sets. The `EXPECTED-FAIL unbound_bitmap_attack` line is the "failed before" evidence: a bitmap that
claims seats unrelated to the aggregate is accepted by a count-based rule and refused by the policy
`f_B`, which is precisely the error v0.8 fixes. The last two lines compute the B0 overhead at the
target committee size: an 8-byte bitmap.

**v0.9 — `src/ce_qs_private_wrapper_relation_checker.py`**
(`results/ce_qs_private_wrapper_relation_checker.txt`):

```
PASS valid_private_wrapper_relation
EXPECTED-FAIL aggregate_bitmap_mismatch
EXPECTED-FAIL bitmap_cet_set_mismatch
EXPECTED-FAIL hidden_below_threshold
PASS conflict_extracts_exact_intersection intersection=[0, 1, 2]
NOTE: logical relation mock only; no MPA or NIZK implemented.
```

The three `EXPECTED-FAIL` lines are the exactly the failure modes the wrapper must exclude, including
`bitmap_cet_set_mismatch` — the case where the aggregate's bitmap and the CET list describe different
seat sets, which is the same-index condition of PW4–PW7. The `intersection=[0, 1, 2]` line is the
worst-case extraction at `n = 7`: the extractor recovers the full three-element intersection
`2q − n = f + 1 = 3`, not an average-case sample.

Both checkers are mocks, and both say so in their own output. They test *relations*, not
cryptography: "no MPA or NIZK implemented".

## What this inflection left behind

- The **size problem moved, it did not disappear.** v0.9's public list is 1376 bytes at a 32-byte
  tag, and the C1 tag-hiding argument was later found insufficient at quantum collision resistance —
  v1.0 raised the tag to 384 bits, making the same list 2064 bytes
  (`docs/distributed-certified-tag-proof.md:999–1042`). v1.24 now allocates 5,504 bytes for the
  handle list.
- The **constructibility problem was created by v0.9 and fixed at v1.0**: see Inflection 4.
- The **same-index condition** survives every later revision, and is expressible in v1.24 as the
  shared selector `e_{j,i}` driving all three key tables
  (`docs/32kib-contents-contract.md:87–91`).

See also: `docs/public-signer-theoretical-completion.md` (v0.8),
`docs/quantum-lift-private-wrapper-proof.md` (v0.9), and Inflection 4 for the correction of v0.9's
prover model.
