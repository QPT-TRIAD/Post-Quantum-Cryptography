# QPT-128 Mode B-r: the security reductions, run

A reduction-based security proof has two halves. One is a CONVERSION: a recipe that turns any adversary who breaks the scheme into a solver for a named hard problem. The other is a HARDNESS ASSUMPTION: that nobody can solve that problem. This runner executes the conversion. It builds adversaries that genuinely break toy-sized instances, feeds them to the reduction exactly as the proof writes it, and checks three things: that the adversary cannot tell the reduction's simulated world from the real one, that whatever the reduction outputs really is a solution of the hard problem, and that it succeeds as often as the theorem claims. If those hold, the logic of the proof has been confirmed by running it rather than by reading it. If they fail, the proof has a hole, and the failure is a finding at any size. What this runner CANNOT do is say anything about the hardness assumption: it shows 'if the problem is hard then the scheme is secure', never that the problem is hard. It also runs only the reductions that can be run. The proof system's own soundness theorem lives in the quantum random-oracle model and is replaced here by an ideal prover, so nothing below tests it; and where the record gives no constructive reduction at all, the runner lists that as a gap instead of passing over it. A reduction that survives every adversary tried here has survived those adversaries, not every adversary.

Toy size n = 10 bits, 100 trials per experiment, seed 20260921, generated 2026-09-21T00:10:41+00:00. Source of the reductions: `modeB_security_v1.49.md` sections 1-4.

## What was found

The runner's controls behaved: it caught a deliberately broken reduction, and no reduction produced an answer for an adversary that never won.
- **Theorem 1's reduction, run as its proof is written, does not survive a legitimate adversary.** Against a framer that requests the approval first it is perfect (100/100 wins converted). Against one that looks the challenge up *before* requesting the approval — a public hash of the message, which nothing in the game forbids querying — the adversary wins 100/100 real games and the reduction cannot be carried out in 100/100: the oracle has already answered, so 'programs c(m) := c*' is impossible, and the reduction has no opening with which to answer honestly. The proof's sentence 'This simulation is perfect' does not hold for this adversary.
- The textbook repair — guess which message will be approved — is sound and converts at 0.17 against a predicted 0.20: a loss factor equal to the number of messages the adversary looked up. In the theorem's bound that factor is the adversary's query count q, so the bound reads q times weaker and the word 'tight' does not survive this repair.
- A second standard repair, *not in the record*: a random salt in the challenge. Against the same pre-querying adversary the as-written reduction then holds (100/100 converted, 0 failures), because the approval's oracle point is fresh when the reduction programs it. This shows the repair restores *this* reduction in *this* model; what a salt does to extraction, certificate size and the other theorems is not examined here.
- Theorem 2 step 2: holds. Every evasion (15/15) yielded a genuine collision of F — *given* the two openings, which here come from the ideal prover and in the record from a quantum online extractor that is not run.

## 1. Controls — does the runner itself work?

| experiment | adversary wins real game | wins in simulation | simulation failed | solved the hard problem | wrong outputs | conversion (claimed) | verdict |
|---|---|---|---|---|---|---|---|
| `t1_lazy` | 0/100 | 0/100 | 0 | 0 | 0 | — (1.00) | **NOT EXERCISED** |
| `control_broken` | 100/100 | 100/100 | 0 | 0 | 100 | 0.00 (1.00) | **FAILS** |
| `t2_plain` | 0/100 | 0/100 | 0 | 0 | 0 | — (1.00) | **NOT EXERCISED** |

## 2. The reductions, run

| experiment | adversary wins real game | wins in simulation | simulation failed | solved the hard problem | wrong outputs | conversion (claimed) | verdict |
|---|---|---|---|---|---|---|---|
| `t1_plain` | 100/100 | 100/100 | 0 | 100 | 0 | 1.00 (1.00) | **HOLDS** |
| `t1_quarter` | 24/100 | 24/100 | 0 | 24 | 0 | 1.00 (1.00) | **HOLDS** |
| `t1_prequery` | 100/100 | 0/100 | 100 | 0 | 0 | 0.00 (1.00) | **FAILS** |
| `t1_guessing` | 100/100 | 17/100 | 83 | 17 | 0 | 0.17 (0.20) | **HOLDS, WITH LOSS** |
| `t1_salted` | 100/100 | 100/100 | 0 | 100 | 0 | 1.00 (1.00) | **HOLDS** |
| `t2_evader` | 15/16 | 15/16 | 0 | 15 | 0 | 1.00 (1.00) | **HOLDS** |

*Conversion* is how often the reduction solved its instance, relative to how often the adversary won the real game. The two worlds are played on independent instances, so for an adversary that wins only sometimes the ratio scatters around its true value and can land above 1; the z-score in section 3 is the test of whether the two win rates differ.

## 3. Why each verdict

### `t1_plain` — Theorem 1 (non-frameability, 'tight')

Reduction: Theorem 1 as written: Frame -> A-F1. Adversary: brute-force framer (approval, then challenge).

**HOLDS** (expected before the run: HOLDS).

- sound, simulated in every trial, indistinguishable (z = 0.0), conversion 1.00 against a claimed 1.00
- 3 trial(s) redrawn because two 8-bit-scale handles coincided — a toy-width artefact the real verifier's 'sorted strictly' rule also rejects.

### `t1_quarter` — Theorem 1 (non-frameability, 'tight')

Reduction: Theorem 1 as written: Frame -> A-F1. Adversary: brute-force framer with a quarter of the search budget. A probabilistic winner: the real and simulated win rates must match.

**HOLDS** (expected before the run: HOLDS).

- sound, simulated in every trial, indistinguishable (z = 0.0), conversion 1.00 against a claimed 1.00
- 1 trial(s) redrawn because two 8-bit-scale handles coincided — a toy-width artefact the real verifier's 'sorted strictly' rule also rejects.

### `t1_lazy` — Theorem 1 (non-frameability, 'tight')

Reduction: Theorem 1 as written: Frame -> A-F1. Adversary: lazy framer (gives up). The reduction must output nothing at all.

**NOT EXERCISED** (expected before the run: NOT EXERCISED).

- the adversary never won, so the conversion was never exercised; what this shows is only that the reduction output nothing wrong

### `t1_prequery` — Theorem 1 (non-frameability, 'tight')

Reduction: Theorem 1 as written: Frame -> A-F1. Adversary: pre-querying framer (challenge, then approval). The adversary looks the challenge up before asking for the approval.

**FAILS** (expected before the run: FAILS).

- the simulation could not be carried out in 100 of 100 trials
- distinguishable: the adversary wins 100/100 real games but 0/100 simulated ones (z = 14.1)
- conversion 0.00 is below the claimed 1.00
- 100 x simulation stopped: cannot carry out 'programs c(m) := c*': the adversary had already asked the oracle for the challenge of b'pay alice' before requesting its approval, and an answer already given cannot be changed. The handle for the challenge it was given needs seat i*'s opening, which the reduction does not have.
- 1 trial(s) redrawn because two 8-bit-scale handles coincided — a toy-width artefact the real verifier's 'sorted strictly' rule also rejects.

### `t1_guessing` — Theorem 1 (non-frameability, 'tight')

Reduction: Theorem 1 repaired by guessing the approval message. Adversary: pre-querying framer hiding its target among 3 decoys. Holds only at the reduced rate 1/5: the guessing loss.

**HOLDS, WITH LOSS** (expected before the run: HOLDS, WITH LOSS).

- sound, and converts at 0.17 against the 0.20 it claims — a loss factor of about 5.9, paid in 83 aborted simulations of 100
- 22 x simulation stopped: guessed wrong: bet on message index 2, but the approval was requested for b'pay alice'
- 19 x simulation stopped: guessed wrong: bet on message index 3, but the approval was requested for b'pay alice'
- 18 x simulation stopped: guessed wrong: bet on message index 0, but the approval was requested for b'pay alice'
- 5 trial(s) redrawn because two 8-bit-scale handles coincided — a toy-width artefact the real verifier's 'sorted strictly' rule also rejects.

### `t1_salted` — Theorem 1 (non-frameability, 'tight')

Reduction: Theorem 1 as written: Frame -> A-F1 — on a SALTED scheme (not in the record). Adversary: pre-querying framer (challenge, then approval). Candidate repair: the approving seat adds a random salt to the challenge.

**HOLDS** (expected before the run: HOLDS).

- sound, simulated in every trial, indistinguishable (z = 0.0), conversion 1.00 against a claimed 1.00

### `control_broken` — Theorem 1 (non-frameability, 'tight')

Reduction: CONTROL: a broken reduction (instance embedded in the wrong seat). Adversary: brute-force framer (approval, then challenge). The runner must catch this.

**FAILS** (expected before the run: FAILS).

- UNSOUND: 100 output(s) did not solve the hard problem
- conversion 0.00 is below the claimed 1.00
- 1 trial(s) redrawn because two 8-bit-scale handles coincided — a toy-width artefact the real verifier's 'sorted strictly' rule also rejects.

### `t2_evader` — Theorem 2 step 2 (binding / evasion)

Reduction: Theorem 2 step 2: evasion -> collision of F. Adversary: collision evader (two openings of one key). Openings come from the ideal prover, standing in for the online extractor.

**HOLDS** (expected before the run: HOLDS).

- sound, simulated in every trial, indistinguishable (z = 0.0), conversion 1.00 against a claimed 1.00
- 1 trial(s) redrawn because two 8-bit-scale handles coincided — a toy-width artefact the real verifier's 'sorted strictly' rule also rejects.

### `t2_plain` — Theorem 2 step 2 (binding / evasion)

Reduction: Theorem 2 step 2: evasion -> collision of F. Adversary: plain double-signer (one opening per key). Forensic completeness: every double-signing seat must be named.

**NOT EXERCISED** (expected before the run: NOT EXERCISED).

- the adversary never won, so the conversion was never exercised; what this shows is only that the reduction output nothing wrong
- 8 trial(s) redrawn because two 8-bit-scale handles coincided — a toy-width artefact the real verifier's 'sorted strictly' rule also rejects.

## 4. Not run, and why

A step that is not executed here is not thereby confirmed. These are the parts of the record's argument this runner has nothing to execute for:

- **Theorem 3 — QROM soundness of the proof system.** A quantum random-oracle bound, and by the record's own account transplanted from FAEST v2 Lemma 9.39 rather than re-derived. There is no classical program to run; here the proof system is replaced by an ideal prover whose soundness error is zero by construction.
- **Theorem 2 step 2 — obtaining the two openings.** The record runs a QROM online extractor on both proofs (DFMS22, time O(q^2)). This runner reads the openings the ideal prover was shown instead. The collision logic is tested; the extraction that feeds it is not.
- **Assumption A-P — privacy from one-wayness.** The record says: 'We do not claim a tight decision-to-search reduction.' No constructive reduction is given, so there is nothing to run. Theorem 4 (privacy) rests on A-P as a separate assumption.
- **Theorem 4 — privacy.** A simulation argument in the QROM (GHHM21 adaptive reprogramming) over the real proof system; not executable against an ideal prover.

## 5. What this does not say

Nothing above bears on whether A-F1 or A-F2 is *hard*. A reduction that holds shows 'if the problem is hard, this part of the scheme is secure'; a reduction that fails shows the proof does not establish even that, which is a statement about the proof and not an attack on the scheme. The failing case here was found by a model with an ideal prover and a classical random oracle; in the quantum random-oracle model, where an adversary can query the challenge of every message in superposition, programming a point the adversary chose is harder, not easier.
