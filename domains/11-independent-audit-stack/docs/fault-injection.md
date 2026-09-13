# Fault injection on the certificate / extraction pipeline

`fault/fault_injection.py` — recorded result `fault/fault_results.json`; 300 seeded schedules in
**0.8 s**. Deterministic and replayable (`--seed`, default 11; schedule *i* builds `World(seed =
1000·seed + i)`), so the recorded JSON is byte-stable across runs — the re-run for this repository
reproduces it exactly (same digest of content, 300/300 `ok`).

## 1. The model

An adversarial network sits between 64 signers, a collector, an archive and the extractor, running
profile B0 (`sidecar_free_certificate_v1.44.py`, imported read-only). Fault classes (11):
`loss`, `duplication`, `reorder`, `delay`, `clock_skew` (stale coordinate), `restart` (archive
re-read), `rollback` (archive restored to an older snapshot), `corrupt_message`,
`corrupt_signature`, `corrupt_certificate`, `equivocation` (a validator signing both sides).

Each of the 300 schedules draws a random non-empty subset of the fault classes (1…11 of them; each
class appears in 150–166 schedules) and a corruption count `C ∈ {0, 1, 5, 21, 22, 23, 26, 30}`
(30–42 schedules each) — the values straddle the threshold `2q − N = 22`, which is the only place
where the boundary can be observed. Corruption flips one bit at a random offset, biased by class
(inside the message field for message corruption, inside the last `q·32` bytes for signature
corruption, uniformly otherwise).

The signature scheme is the module's **symbolic test double** (width 32). As the file says: this
layer tests pipeline logic under faults, not cryptographic strength.

## 2. The five properties, and the recorded result

| id | property | recorded |
|---|---|---|
| P1 | invalid state rejected: every corrupted frame is rejected by `verify_b0` | 3,700 corruptions attempted, **0 accepted** |
| P2 | liveness where expected: with ≥ q honest votes delivered, a certificate forms | checked per schedule; matches expectation in all 300 |
| P3 | no false blame: extraction never names a seat that signed one side | **0 honest seats named** |
| P4 | no lost evidence: if two conflicting frames ever existed in the archive, every double-signer is named after recovery/replay | 33 conflicts extracted, all fully attributed |
| P5 | no contradictory acceptance: two frames with the same message are never a conflict; a rolled-back archive cannot un-name a double-signer | holds in all 300 |

Totals from the recorded JSON: `schedules 300, failures 0, checks_total 1,717`,
`p1_corruptions_attempted 3700`, `p1_accepted_on_invalid 0`, `conflicts_extracted 33`,
`honest_named_total 0`, `verdict REPRODUCED`, `first_failures []`. 300/300 schedules `ok`.

The P5 rollback check records its own shape: it rolls the archive back to an older snapshot and
re-checks that a double-signer previously named is still nameable — the recorded value
`B_still_reachable: null` on schedules with no conflict means "nothing to re-name", and `ok: true`
for those schedules is a statement about the absence of a conflict, not evidence about rollback. The
schedules where a conflict does exist are the ones that exercise the property, and they pass.

## 3. Re-run for this repository

Run in a sandbox (the recorded `fault_results.json` was not overwritten): exit 0, 0.82 s, summary
identical to the recorded one — same 300 schedules, same 1,717 checks, same 3,700 corruptions, same
0 accepted, same 33 conflicts, same 0 honest seats named, `verdict REPRODUCED`. Because the layer is
seeded, this is an exact reproduction rather than a re-measurement.

## 4. Limits

- Single-process model: the "network", the archive and the extractor are Python objects, not
  processes; message loss and duplication are modelled, partition and Byzantine liveness of a real
  network are not.
- The fault model is the audit's own choice, not a citation: the 11 classes are standard failure
  modes, and no claim is made that they cover all of them (no timing side channels, no
  resource-exhaustion faults, no equivocation *between verifiers*).
- The symbolic signature double means "0 accepted on invalid" is a statement about the pipeline's
  validation logic, not about ML-DSA.
- The corruption count `C` is the number of seats the adversary controls, injected by corrupting
  the pipeline's inputs — it is not an adversary that adaptively chooses which seats to corrupt.
