# 15 — Executable reductions

A security reduction is a program: it turns an adversary that breaks the scheme into a solver for a
named hard problem. On paper that program is prose. This domain writes it out as code, follows the
proof sentence by sentence, and **runs** it against adversaries that really do break toy-sized
instances of Mode B-r — then checks whether the thing that comes out is a genuine solution, as often
as the theorem says.

**What it establishes.** One of the record's reductions, implemented as its proof is written, cannot
be carried out against a legitimate adversary. Theorem 1 (non-frameability, stated as *tight*) needs
to program the challenge oracle at the message the honest seat is asked to approve. The challenge is
a deterministic public hash of the message, with no signer randomness in it, so an adversary is free
to ask for it first; by the time the reduction wants to program that point the oracle has already
answered, and an answer already given cannot be changed. Measured at `n = 8` over 200 trials: the
adversary wins **200/200** real games and the simulation fails **200/200**. The proof's sentence
"This simulation is perfect" does not hold for that adversary class. The same result recurs at
`n = 10` over 100 trials.

**What it does not establish, and this has to be read before anything else.** *This is a hole in a
proof, not a break of the scheme.* Every adversary in this domain wins by exhaustive search over a
key whose width is 7 to 10 bits; the same search costs about 2^255 at production size. What failed
is the *argument* that framing is as hard as assumption A-F1 — for one class of adversary that
argument cannot be carried out, so for that class the theorem's bound is **unproven, not shown
false**. Whether framing is actually hard is exactly as open as it was before. Nothing here bears on
the hardness of A-F1 or A-F2, and four parts of the record's argument have nothing this domain can
execute at all (§6).

---

## 1. How to read this domain

| Order | File | What it is |
|---|---|---|
| 1 | this file | the finding, the experiments, the boundary |
| 2 | `src/qpt_rr/scope.py` | the scope boundary, emitted verbatim at the head of every report |
| 3 | `src/qpt_rr/scheme.py` | Mode B-r at toy size: registry, programmable random oracle, handle, ideal prover, verifier, extractor |
| 4 | `src/qpt_rr/reductions.py` | the reductions themselves — Theorem 1 as written, the guessing repair, the salted variant, the broken control, Theorem 2 step 2 |
| 5 | `src/qpt_rr/adversaries.py`, `src/qpt_rr/frame_game.py` | the adversaries and the game they play |
| 6 | `src/qpt_rr/runner.py`, `src/qpt_rr/campaign.py` | one trial, and the nine experiments a campaign runs |
| 7 | `results/run-2026-09-21-n8/`, `results/run-2026-09-21-n10/` | the two campaigns: `report.md` and `results.json` |
| 8 | `VERIFICATION.md` | the re-run record: commands, environment, observed counts |

`scripts/qpt-rr scope` prints the boundary; `scripts/qpt-rr gaps` prints the list in §6.

---

## 2. What is run

The construction is Mode B-r of the record's Mode B security document, section 1, in its current
(v1.50) form, at `n = 8` or `n = 10` bits of opening instead of 256:

```
registration   seat i samples (s_i, r_i) and publishes  Y[i] = F(s_i ‖ r_i)
challenge      (c_a, c_b, c_c) = H("c", cfg, d, m, ctr)
handle         Z_i = r_i^7 + L_c(s_i),   L_c(s) = c_a·s + c_b·s² + c_c·s⁴
extraction     for two certificates with equal (cfg, d) and m₀ ≠ m₁, solve
               (L_c0 + L_c1)(s) = Z₀ + Z₁, recover r, and name every seat with F(s ‖ r) = Y[i]
```

Two idealisations, both of which the record also makes:

- **The hash is a programmable random oracle.** It is sampled lazily and records every query. It
  **refuses to program a point it has already answered** — an oracle that silently rewrote an answer
  would let a reduction "succeed" by cheating, and that refusal is exactly what produces the finding
  in §3.
- **The proof is the ideal functionality F_Prove** (the record's assumption A-Prove, a trusted
  aggregator). Its soundness error is zero by construction, so nothing here tests Theorem 3.

Every campaign runs at 6 seats with quorum 4. Each trial plays the adversary twice from the same
seed — once in the **real game**, once inside the **reduction's simulation** — and asks four
questions in order: is the reduction *sound* (it never outputs a non-solution)? did the simulation
*run*? is it *indistinguishable* (the two win rates agree)? is it as *tight* as claimed?

The field, the key map and the scaling rule are imported from domain 14 rather than copied, because
they are tested there and a second copy would be a second thing to get wrong.

---

## 3. The finding

Theorem 1's reduction, as written, embeds its A-F1 instance in the honest seat's public key and
answers the adversary's one approval request by programming the challenge of the approved message to
the instance's challenge `c*`. That step is the whole proof. It requires the challenge of the
approved message to be **unqueried** at the moment the approval is requested.

Nothing in the game forbids the adversary from querying it. The challenge is a public hash of the
message and carries no signer randomness, so the adversary can look it up — for its target and for
any number of decoys — and only then ask for the approval. The reduction then has an answer it
cannot change, and no opening for the honest seat with which to answer honestly.

| adversary | order of operations | real wins | simulated wins | simulation failures | conversion (claimed) | verdict |
|---|---|---|---|---|---|---|
| brute-force framer | approval, then challenge | 200/200 | 200/200 | 0 | 1.00 (1.00) | **HOLDS** |
| pre-querying framer | challenge, then approval | 200/200 | 0/200 | **200** | 0.00 (1.00) | **FAILS** |

(`n = 8`, 200 trials, seed 20260921.) The failing rows all carry one message: *cannot carry out
"programs c(m) := c\*": the adversary had already asked the oracle for the challenge of the target
message before requesting its approval, and an answer already given cannot be changed.* The two
worlds are distinguishable by the widest margin the runner can report, `z = 20.0`.

**The textbook repair works and costs the word "tight".** The reduction may guess *which* message
the approval will be for and program that one early. With the adversary looking up its target plus
3 decoys, the reduction bets on one of 5 possibilities, so it claims a conversion of 0.20. Measured:
**0.185** at `n = 8` (37 simulations of 200 survived; 163 aborted on a wrong bet) and **0.17** at
`n = 10`. The reduction is sound throughout — it never emitted a non-solution — but in the theorem's
bound the loss factor is the adversary's query count, so the bound reads that many times weaker and
**"tight" does not survive the repair**.

**A salted challenge restores the as-written reduction — and is not part of the record.** If the
approving seat mixes a fresh 64-bit salt into the challenge, the approval's oracle point is
unqueried when the reduction programs it, and the same reduction against the same pre-querying
adversary converts **200/200** with 0 failures. This is recorded as a *candidate* repair only. What
a salt does to extraction, to certificate size, and to the other theorems **was not examined**.

**Theorem 2 step 2 holds.** Every evasion yielded a genuine collision of the key map `F` — 30 of 30
wins at `n = 7` in the first campaign, 15 of 15 in the second — *given* the two openings. Here those
openings come from the ideal prover. In the record they come from a quantum online extractor that is
not run (§6).

---

## 4. The nine experiments, both campaigns

`n = 8`, 200 trials (the evasion tracks run at `n = 7`), seed 20260921:

| experiment | reduction | adversary | real wins | simulated wins | sim. failures | solved | wrong outputs | conversion (claimed) | verdict |
|---|---|---|---|---:|---:|---:|---:|---|---|
| `t1_plain` | Theorem 1 as written | brute-force framer | 200/200 | 200/200 | 0 | 200 | 0 | 1.00 (1.00) | HOLDS |
| `t1_quarter` | Theorem 1 as written | framer with a quarter of the budget | 45/200 | 53/200 | 0 | 53 | 0 | 1.18 (1.00) | HOLDS |
| `t1_lazy` | Theorem 1 as written | framer that gives up | 0/200 | 0/200 | 0 | 0 | 0 | — (1.00) | NOT EXERCISED |
| `t1_prequery` | Theorem 1 as written | pre-querying framer | 200/200 | 0/200 | 200 | 0 | 0 | 0.00 (1.00) | **FAILS** |
| `t1_guessing` | Theorem 1, guessing repair | pre-querying framer, 3 decoys | 200/200 | 37/200 | 163 | 37 | 0 | 0.18 (0.20) | HOLDS, WITH LOSS |
| `t1_salted` | Theorem 1 as written, salted scheme | pre-querying framer | 200/200 | 200/200 | 0 | 200 | 0 | 1.00 (1.00) | HOLDS |
| `control_broken` | instance embedded in the wrong seat | brute-force framer | 200/200 | 200/200 | 0 | 0 | **200** | 0.00 (1.00) | **FAILS** (as required) |
| `t2_evader` | Theorem 2 step 2 | collision evader, two openings | 30/33 | 30/33 | 0 | 30 | 0 | 1.00 (1.00) | HOLDS |
| `t2_plain` | Theorem 2 step 2 | plain double-signer | 0/200 | 0/200 | 0 | 0 | 0 | — (1.00) | NOT EXERCISED |

`n = 10`, 100 trials (evasion tracks again at `n = 7`), same seed:

| experiment | real wins | simulated wins | sim. failures | solved | wrong outputs | conversion (claimed) | verdict |
|---|---|---|---:|---:|---:|---|---|
| `t1_plain` | 100/100 | 100/100 | 0 | 100 | 0 | 1.00 (1.00) | HOLDS |
| `t1_quarter` | 24/100 | 24/100 | 0 | 24 | 0 | 1.00 (1.00) | HOLDS |
| `t1_lazy` | 0/100 | 0/100 | 0 | 0 | 0 | — (1.00) | NOT EXERCISED |
| `t1_prequery` | 100/100 | 0/100 | 100 | 0 | 0 | 0.00 (1.00) | **FAILS** |
| `t1_guessing` | 100/100 | 17/100 | 83 | 17 | 0 | 0.17 (0.20) | HOLDS, WITH LOSS |
| `t1_salted` | 100/100 | 100/100 | 0 | 100 | 0 | 1.00 (1.00) | HOLDS |
| `control_broken` | 100/100 | 100/100 | 0 | 0 | **100** | 0.00 (1.00) | **FAILS** (as required) |
| `t2_evader` | 15/16 | 15/16 | 0 | 15 | 0 | 1.00 (1.00) | HOLDS |
| `t2_plain` | 0/100 | 0/100 | 0 | 0 | 0 | — (1.00) | NOT EXERCISED |

Two readings of this table need stating, because both are easy to get wrong:

- **Conversion can exceed 1.** The real game and the simulation are played on *independent*
  instances, so for an adversary that wins only sometimes the ratio scatters around its true value.
  `t1_quarter` at `n = 8` reads 1.18; its z-score is −0.9, which is the actual test of whether the
  two win rates differ.
- **A redrawn trial is a toy-width artefact, not a discarded failure.** Trials are redrawn when two
  handles at 7-to-10-bit width coincide, which the real verifier's "sorted strictly" rule also
  rejects: 22, 6, 0, 10, 15, 10, 10, 4 and 21 redraws across the `n = 8` experiments in table order.

---

## 5. The controls

Two of the nine experiments exist only to test the runner itself, and both behaved:

- **A deliberately broken reduction was caught.** `control_broken` embeds the instance in the wrong
  seat. The adversary wins and the simulation runs — so a runner that only counted wins would call
  it a success — but **all 200 outputs (100 at `n = 10`) were flagged as not solving the hard
  problem**, and the verdict is FAILS.
- **No reduction produced output for an adversary that never won.** `t1_lazy` and `t2_plain` win 0
  games; both reductions emitted nothing at all, with 0 wrong outputs.

If either control misbehaves, the report declares its own subject verdicts void. It did not have to.

---

## 6. What could not be executed, and is listed rather than passed over

A step that is not executed here is not thereby confirmed.

| step | why there is nothing to run |
|---|---|
| **Theorem 3** — soundness of the proof system | a quantum random-oracle bound, and by the record's own account **transplanted from FAEST v2 Lemma 9.39 rather than re-derived**. Here the proof system is the ideal prover, whose soundness error is zero by construction |
| **Theorem 2 step 2, obtaining the two openings** | the record runs a quantum online extractor on both proofs (DFMS22, time O(q²)). This domain reads the openings the ideal prover was shown. The collision logic is tested; the extraction that feeds it is not |
| **Assumption A-P** — privacy from one-wayness | the record states that it *does not claim a tight decision-to-search reduction*. No constructive reduction is given, so there is nothing to run |
| **Theorem 4** — privacy | a simulation argument in the quantum random-oracle model over the real proof system; not executable against an ideal prover |

---

## 7. What this domain does not establish

- **Nothing about hardness.** A reduction that holds shows "if the problem is hard, this part of the
  scheme is secure". It never shows that the problem is hard. A-F1 and A-F2 are untouched.
- **No break of the scheme.** Every adversary here wins by exhaustive search over a 7-to-10-bit key.
  The failing case is a statement about an argument, not an attack.
- **No production-parameter result.** Nothing was run at `n = 256`, and no figure here is a security
  level.
- **The failure is model-dependent in the direction that favours the scheme.** It was found with an
  ideal prover and a *classical* random oracle. In the quantum random-oracle model, where an
  adversary can query the challenge of every message in superposition, programming a point the
  adversary chose is harder, not easier.
- **The salt is a candidate, not a fix.** It is not in the record; its effect on extraction,
  certificate size and the other theorems was not examined.
- **A reduction that survived these adversaries survived these adversaries**, not every adversary.
  Four experiments are subjects, two are controls, two were never exercised, and the whole campaign
  is nine experiments at two widths on one seed.
