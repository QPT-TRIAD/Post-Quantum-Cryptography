# GAME 4 — SAFETY

*Definition in the harness:* `GAME_SAFETY` in `src/ceqs_games.py`; measured by `game_safety()`.
*Recorded write-up:* `results/attack-lab-results.md` §12.4 and §12.5 (which also carries the ledger
correction this game triggered).

---

## 1. The game

```
SAFETY(F, registry, d)

Attacker receives     the openings of its corrupt seats; honest approvals for one message
                      per domain.
Does not receive      anything else — in particular it cannot choose the honest approvals.

Oracle                —  (no query cost is counted; the parameter is the corruption level C)

Wins if               with C corrupt seats it assembles TWO certificates of 43 valid seats
                      each, in the same domain, for different messages.
```

SAFETY is the one game of the four that is **not winnable** below the threshold, and the measurement
is of the threshold itself. It is included because a domain that only measures attacks that work
would leave the construction's central counting claim untested.

## 2. The property claimed

**The quorum-intersection threshold**: equivocation requires at least `MIN_OVERLAP = 22` corrupt
seats; with `C ≤ 21` it is impossible, and with `C ≥ 22` it is possible *and fully attributable*.

The argument is elementary and complete:

```
Each certificate needs 43 distinct valid seats.
An honest seat contributes to at most one message per domain.
Two conflicting certificates therefore need 43 + 43 = 86 seat-contributions
from at most 64 honest seats plus C corrupt ones:
        86 <= 64 + C   <=>   C >= 22.
```

Equivalently: two quorums of 43 seats drawn from 64 intersect in at least `43 + 43 − 64 = 22`
seats, and every seat in the intersection signed both messages — so extraction has at least 22
culprits to name.

**This is a proof, not a measurement.** It is a counting argument over sets, and it needs no
assumption about `F`, the challenge derivation, or the adversary's computational power: it holds
against an unbounded adversary. The harness tests it rather than proving it, because the property
that matters operationally is that the *implementation* enforces the same threshold — an
implementation that accepted a 42-seat "quorum" would break the argument while leaving it true.

## 3. Status of the argument

| part | status | where |
|---|---|---|
| `C ≤ 21` ⇒ no two conflicting certificates | **proof** (elementary counting, above) | §2 |
| the implementation enforces exactly this threshold | **measurement**, exhaustive `C = 0…23` | §4 |
| completeness of blame at `C = 22, 23` | **measurement** (no genuine double-signer missed) | §4 |
| extraction names extra, non-double-signing seats | **measurement** plus a modelled rate; a real but astronomically unlikely framing path | §5 |
| the production probability of that path (`2^−245.2` per conflict) | **estimate** from the model, not measured at production width | §5 |
| the ledger's false-positive row `R5 = −181.2` | **correction of an earlier estimate**, now computed by domain 08's ledger | §5 |

## 4. Measured results

**Method.** For each `C` from 0 to 23, construct the most favourable two 43-seat sets the counting
argument allows — the corrupt seats in both, honest seats split between them — check whether two
certificates are even *feasible*, and where they are, encode both for real and run `m50.extract`.
Sixteen redraws are attempted at each `C` to avoid toy-width handle collisions.

**Parameters.** `n = 14`, expansion 8, `N = 64`, quorum 43, `MIN_OVERLAP = 22`.

| `C` | 0 … 21 | 22 | 23 |
|---|---|---|---|
| two conflicting certificates | **impossible (counting)** | possible | possible |
| extraction result | — | names 23 seats: 22 genuine double-signers, **missed 0**, one handle-coincidence name (seat 40) | names 23 seats: 23 genuine, **missed 0**, no coincidences |

**Measured threshold 22 = theoretical threshold 22.** No genuine double-signer was ever missed. The
harness reports `matches_theory: true`.

## 5. The false positive — a real framing path, measured and modelled

At `C = 22`, extraction names **23** seats when there are 22 double-signers. The cause is not a
counting error, and it is worth stating fully because it is a genuine (if vanishingly improbable)
way to frame an honest seat:

> A seat present in **exactly one** of the two certificates is named when its *would-be* handle
> under the other message coincides with one of the 43 handles actually published there. The pair
> then decodes to that seat's genuine opening, `F` matches, and public `verify_blame` re-verifies it.

Two consequences follow. First, the effect is driven by the **handle width**, not the registry-key
width — the coinciding quantity is a handle, not a key. Second, it is the mechanism that forces the
non-frameability statement in `docs/game-frame.md` §2 to be qualified "up to the handle-coincidence
effect" rather than stated absolutely.

**Measured rate against the model.** With 42 seats present in exactly one certificate (since
`43 + 43 − 2·22 = 42`) and 43 published handles, the model predicts
`1 − exp(−42·43/2^n) ≈ 42·43/2^n`:

| `n` | 11 | 13 | 14 | 16 | 17 |
|---|---:|---:|---:|---:|---:|
| measured | 0.5767 | 0.2233 | 0.0900 | 0.0267 | 0.0100 |
| predicted `42·43/2^n` | 0.8818 | 0.2205 | 0.1102 | 0.0276 | 0.0138 |

The model tracks the measurement; the union bound loosens as the probability approaches 1, which is
why `n = 11` is the outlier (0.5767 measured against 0.8818 predicted).

**At production width** the same model gives `42·43/2^256 ≈ 2^−245.2` per conflict, i.e. the effect
is real and irrelevant — but it is the largest term in the ledger's false-positive row, which is why
it matters that it is modelled rather than assumed away.

**The ledger correction this game forced.** The `R5` row had modelled only a *random candidate
opening* hitting a registry key: `2^64 · 64 · 43² / 2^(2n+E) ≈ 2^−943`. The dominant path is the
handle coincidence:

```
R5 = log2( 2^64 · 42 · 43 / 2^256 ) = 64 + log2(1806) − 256 = −181.2
```

about 760 bits larger than the old value. The row is nowhere near binding either way — the total
(`−137.7`) and the D2 margin (7.7 bits) are unchanged — but the corrected value is the one the ledger
now computes and asserts, in `domains/08-hidden-signers/src/mode_b_rigorous_ledger.py`. This is the
clearest example in the programme of a measurement finding something a model had missed, and the
record states it as such rather than silently updating the number.

## 6. Tests

`test_safety_threshold_is_22` asserts: equivocation impossible for `C ≤ 21`, possible for `C ≥ 22`,
**no genuine double-signer missed** at either feasible level, and **at most 3 extra names**. The last
clause is deliberate: the correct assertion is that the false-positive count is *bounded*, not that it
is zero, because §5 shows it is a real effect. Asserting `0` would make the test fail on a legitimate
reseed at `n = 14` where the predicted rate is 0.11 — and would be a claim the construction does not
support.

Observed: pass (`--self-test`, 4 tests OK).

## 7. Cost of a run

Cheap: 24 corruption levels, two encodes and one extract each. A small fraction of the suite's
148.19 s wall time.

```
cd domains/09-security-games-and-attack-lab/src
python3 ceqs_games.py --safety
python3 ceqs_games.py --safety --json
```

## 8. What would falsify this, and open items

- **An implementation that accepts fewer than 43 distinct seats.** Would break the counting argument
  in practice while leaving it true in theory. The lab's Experiment A exercises this (attempts 7 and
  15, both rejected); the SAFETY game would be refuted by a single counterexample.
- **A genuine double-signer missed at `C = 22` or 23.** Would refute completeness. Not observed;
  exercised once per level, not statistically.
- **More than one false positive at `C = 22`.** The model is a single-coincidence model (`42·43/2^n`);
  at production width double coincidences are far below `2^−245` and are ignored. At toy widths the
  measured rates are consistent with the single-coincidence model, so no evidence for the
  double-coincidence term was seen — but the toy widths are also where it would be most visible.
- **`C ≥ 24`.** Not exercised: the counting argument is strongest in the middle of its range, and the
  harness stops at 23 because `C = 23` already has all honest seats in one certificate. Untested:
  whether extraction stays complete when the corrupt set is large enough that the two quorums'
  intersection is chosen adversarially rather than inherited from the split.
- **The rate at production width is an estimate, not a measurement.** `2^−245.2` is the model
  evaluated at `2^256`, and the ledger's `R5 = −181.2` inherits the model's shape. A reader who
  needs the row to be a proven bound rather than a modelled estimate must supply the argument.
