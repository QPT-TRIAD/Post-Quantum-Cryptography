# Validation status — what is established, what is not, and what a proof would still need

This document lists, claim by claim, what this domain asserts, how strong the assertion is, and what
would have to be supplied for it to count as part of a standard proof. It is the document to read
before quoting any number from this domain.

**Labels used, and nothing else.** Every claim below carries one of the programme's own labels:
*theorem-with-proof*, *reduction-sketch*, *model-or-ledger estimate*, *measurement*, *simulation*,
*assumption*, *conjecture*. A measurement is a finite campaign on real code; a simulation is a
classical execution of an algorithm that would run on other hardware; neither is a proof.

---

## 1. The claims, with their status

| # | claim | status | contributed by | what must still be validated |
|---:|---|---|---|---|
| 1 | Honest seats cannot be framed: an adversary without a seat's opening cannot make extraction name it | **reduction-sketch**, conditional on A-F1 | domain 08, Theorem 1 | the reduction's own steps (domain 08's job); the regime in which A-F1 is stated; the handle-coincidence exception in §2 below |
| 2 | Extraction cannot be silenced: a conflict always yields the culprits | **theorem-with-proof** for the structural part; **model-or-ledger estimate** for the cost | §3 below | the challenge derivation's output is uniform enough for the collision bound; the transplant's applicability (CFHL) |
| 3 | One evader costs exactly itself: a seat with a second opening does not hide the others | **measurement** of a fix, plus **assumption A-F2** | `game-evade.md` §5 | a run with a *genuine* second opening rather than a placeholder; more than one evader; `C > 22` |
| 4 | Equivocation requires ≥ 22 corrupt seats | **theorem-with-proof** (elementary counting) | `game-safety.md` §2 | nothing mathematical; the *implementation* enforcing it is a **measurement** (exhaustive `C = 0…23`) |
| 5 | The real attacks scale as the ledger assumes | **measurement** at toy sizes (4 games, 10 experiments) | this domain | extrapolation beyond the measured range — the error is *measured* (`games-methodology.md` §6.1), not bounded |
| 6 | The production security level is ≥ 128 bits | **model-or-ledger estimate** | domain 08's ledger | the reductions, all six assumptions, the transplanted bounds, **and a reconciliation of the two ledgers whose margins differ by 21.7 bits** (§7 item 11) |
| 7 | The deployed implementation rejects the attacks tried against it | **measurement** (23 structural attempts + 1 positive control) | `attack-lab.md` §1 | attacks not on the list (`attack-lab.md` §9); the one attempt whose rejection is a toy-width artefact |
| 8 | The Grover iteration law holds on the real oracle | **simulation** (exact state vector, no gates) | `attack-lab.md` §3 | a gate-count argument for the oracle circuit; anything about real hardware |

Note what is *not* in this table: no row claims that a game is hard for all adversaries. Rows 1, 3
and 5 are about a specific attack or a specific reduction, and each is labelled accordingly.

---

## 2. The exception that qualifies claim 1

Non-frameability holds **up to the handle-coincidence effect**: at `C = 22` the SAFETY game measured
extraction naming 23 seats when 22 seats double-signed, and the extra name is an honest seat whose
*would-be* handle under the other message coincided with a published one (`game-safety.md` §5). The
effect is real, `verify_blame` re-verifies the fabricated blame, and its per-conflict rate is
`42·43/2^n` — measured 0.0900 at `n = 14` against a predicted 0.1102, and `≈ 2^−245.2` at production
width.

**What must still be validated.** The production figure `2^−245.2` is the model evaluated at
`2^256`, not a measurement, and the ledger's `R5 = −181.2` inherits the model's shape. A standard
proof needs the row as a bound rather than an estimate: a treatment of multi-coincidence terms (not
just the single-coincidence `42·43` term), and a statement of what the adversary may choose (the
seat set, the message pair) rather than the fixed split the harness builds.

---

## 3. Claim 2 in detail, because it is the strongest thing here

The structural half is a proof, and it is short: extraction solves `D(s) = Z₀ ⊕ Z₁` with
`D(s) = αs ⊕ βs² ⊕ γs⁴`, a linearized 2-polynomial of 2-degree ≤ 2 over GF(2^256); its kernel is an
`𝔽₂`-subspace of dimension ≤ 2, so `D` has at most 4 roots and extraction succeeds whenever
`(α, β, γ) ≠ 0`. Only a full challenge collision (`D ≡ 0`) suppresses it. This is
*theorem-with-proof* — it is a statement about a specific map over a specific field, and the
characteristic-2 linearity of `s ↦ s^(2^i)` is what makes it true. It justifies the extractor's
`max_free = 2` cap and it needs no assumption about `F`, `H` or the adversary.

**What must still be validated, and it is not the lemma:**

- **That `H`'s output behaves like a random 768-bit string.** The collision cost `2^(h/2)` is the
  birthday value for a random function; the harness measures that the real derivation *behaves*
  that way at toy widths but never measures its output distribution. A standard proof needs the
  derivation modelled (random oracle or a proven PRF) with the domain separation stated.
- **The transplant.** `2^81.7` and `2^252.4` come from the project's implementation of the CFHL
  bound, cited as "Chung–Fehr–Huang–Liao, EUROCRYPT 2021, Thm 5.29" — **no title, no page**, and the
  bound is applied to a function family the theorem was not written about in this programme. A
  standard proof needs the theorem's hypotheses checked against this challenge derivation, not just
  its closed form evaluated.
- **Small-sample and pooling effects.** The pooled fit's slope (0.4498) is below theory and the
  record's `−38.1`-bit "extrapolation error" is largely a pooling artefact (`game-suppress.md`
  §4.1). Neither affects the structural claim; both affect any attempt to use the fit as an estimate.

---

## 4. The six assumptions the conclusions rest on

Defined in `domains/08-hidden-signers/docs/mode-b-security.md` §2. This domain's measurements are
consistent with them; none is established by them.

| assumption | what it says | what this domain does about it |
|---|---|---|
| **A-F1** | the key map `F` is one-way on openings in the relevant regime | FRAME measures the generic search on the real `F` and finds the marked set exactly 1 at 60 instances — evidence for the generic path only. A cryptanalytic break of `F` would void it; **not attempted here** |
| **A-F2** | the relation is binding on openings | EVADE measures the cost of the real collision attack on the real `F`; the measurement *supports* the assumption's scaling but does not prove it |
| **A-QROM** | the challenge derivation is modelled in the quantum random oracle model | SUPPRESS measures collision behaviour only; the model is domain 08's |
| **A-P** | the handle leaks nothing beyond what the game allows (privacy) | **untested here.** The independent pass found no distinguisher below search; the record labels that evidence, not a reduction |
| **A-Prove** | the prover/aggregator is trusted as specified | **untested here** — a protocol assumption, not a property of these artefacts |
| **A-Reg** | the registry is honestly established | assumed by every experiment: all of them build the registry from known secrets |

---

## 5. Gaps in this domain's own evidence

These are things a reader might reasonably expect to be covered and are not. Each names what a
follow-up run would have to do.

1. **FRAME's endgame does not chain the search into the frame.** `_frame_endgame()` starts from the
   instance's true opening; the enumeration that recovers it is a separate measurement at the same
   parameters (`game-frame.md` §4). A continuous attack — search, recover, frame, extract — is not
   shipped.
2. **EVADE's endgame uses a fabricated second opening.** A genuine `F`-collision costs `2^E` work and
   is out of reach at `n = 14`; the demonstration uses a placeholder that behaves as a genuine one
   would (`game-evade.md` §5). Joining the two halves needs a run at `E ≤ 8`.
3. **Attempt 17 of the 24 is rejected for a toy-width reason.** The duplicate registration is refused
   with `handle collision`, not by a duplicate-seat check; at `n = 32` the same encode is accepted
   (`attack-lab.md` §1). The gate's count stands; that one row must not be quoted as a
   duplicate-registration defence.
4. **No confidence intervals.** `fit()` is a plain least-squares line; no standard error, no
   weighting, no goodness-of-fit (`games-methodology.md` §6). Slopes are compared to theory by eye
   and by wide test bands.
5. **The SUPPRESS points are unevenly sampled** — 12 samples at the v1.46 sizes, 6/4/**2** at the
   v1.50 sizes, with the mean of a right-skewed law under-estimated in small samples
   (`game-suppress.md` §4.1). The `h = 33` point rests on two samples.
6. **The two harnesses pin a superseded revision.** They load Mode B v1.50, as the record did; the
   domain's current revision is v1.51 (input-canonicality checks). Both suites were re-run against
   v1.51 during this build with identical measured values, but the *shipped* configuration is v1.50.
7. **No negative control for the games.** A game that could not be won would be detected only by its
   own test asserting winnability (FRAME, SUPPRESS, EVADE). SAFETY is not winnable below 22 by
   design, and its "impossible" branch is the counting argument, not a failed search.
8. **One sentence of the record rests on evidence that is not in this repository.** The record's §3
   cites the SAT slopes for the claim that the linearized handle is no worse than `r⁷`. The SAT
   scripts are not shipped (README §5). This domain's own, re-runnable evidence for the same
   conclusion is the identical marked sets and identical mean costs for both handle kinds at all 60
   target-instances.

---

## 6. The unshipped SAT experiments, stated precisely

`domains/08-hidden-signers` records SAT experiments (`sat_attack.py`, `sat_scale.py`,
`collision_sat.py` and neighbours) and states that those analysis scripts are not shipped with the
record. `domains/08-hidden-signers/docs/mode-b-security.md` §9 summarises them: slopes of 2.42 bits
per bit with no handle, 1.29–1.58 with the linear handle, 0.90–0.93 with `r⁷`, plus the statement
that the project's own sparse-vs-dense comparison hit a 25-minute cap inconclusively. Domain 08's own
correction says the `r⁷`-over-linear *ranking* rests on the XL model, not on the SAT experiments, and
that the generic bound is `2^128` for both handles.

**What depends on them here:** one sentence of `results/attack-lab-results.md` §3, and nothing else.
Neither harness imports, reads or invokes a SAT solver; every measured number in this domain re-runs
in full from the repository (`VERIFICATION.md`).

**How strong the SAT evidence actually is.** The programme's validation package states it more
bluntly than the record does: the SAT scripts are scratchpad material and are not shipped; their one
published comparison (sparse versus dense) hit its 25-minute cap **inconclusively**; and
**CryptoMiniSat was never run on the verification host, with no version recorded**
(`docs/04-security-and-validation/validation-status.md`, excluded-pieces table and correction 5).
The honest formulation is that the attack-based evidence for the handle ranking is **thinner than a
summary of "SAT slopes" suggests**, and that the ranking of `r⁷` above the linearized handle survives
only on the **XL / hybrid model** — with the generic bound `2^128` for both handles either way.
**This domain therefore labels that ranking a model estimate, not a measurement**, wherever it
appears.

**What must still be validated** if the record's sentence is to be used: the SAT scripts and their
logs would have to be shipped and the reported slopes re-derived, or the sentence replaced by the
marked-set measurement this domain does ship. A reader cannot check the SAT slopes from this
repository.

---

## 7. What a standard proof would still need — the checklist

Working down from the outermost claim:

1. **The reduction, written out.** Frame, suppress, evade and safety games stated with their
   adversary classes; the six assumptions stated where they are used; every step of the reduction to
   the underlying hard problems. Domain 08 owns this; this domain supplies the scaling evidence the
   steps assume.
2. **The hard problems pinned down with parameters.** One-wayness of the quadratic map at the
   production parameter set, and the binding property — with published cryptanalysis, not a model
   estimate. Domain 08's XL-model estimates are `model-or-ledger estimate`.
3. **The transplanted bounds re-derived or checked against their hypotheses.** The CFHL collision
   bound (no page in the citation) and FAEST v2 Lemma 9.39 (the QROM soundness row). Until then they
   are borrowings.
4. **The random-oracle model for `H` made explicit**, including domain separation and the exact
   output length argument that makes SUPPRESS cost `2^(h/2)`.
5. **The false-positive row as a bound**, with the multi-coincidence terms and an adversarial choice
   of seat sets (§2).
6. **The measurements re-run in a range that brackets, not merely precedes, the conclusion** — or the
   extrapolation error bounded rather than measured (`games-methodology.md` §6.1). Fits over 8–17-bit
   openings do not support statements at 256-bit openings; the domain says this in three places.
7. **A cryptanalysis campaign against `F`** — the largest single untested surface. Nothing in this
   domain touches it.
8. **A gate-count argument for the oracle**, since every quantum row here counts evaluations and
   charges the circuit separately (`≥ 2^18` gates).
9. **The trusted-aggregator premise (A-Prove) either justified or removed** from the protocol.
10. **Implementation security** — timing, faults, side channels — not attempted anywhere in this
    domain.
11. **Reconcile the two ledgers for the hidden-signer profile.** The target domain's ledger gives a D2
    margin of **+29.4 bits** in gate units over rows E1–E8; the hidden-signers ledger this domain
    quotes (`domains/08-hidden-signers/src/mode_b_rigorous_ledger.py`, printed by the attack lab) gives **+7.7 bits** over rows
    R1–R5. Both pass, the margins differ by **21.7 bits**, and neither document cross-references the
    other's row set. The programme's validation package records this as a missing item naming
    `domains/06-qpt128-security-target`, `domains/08-hidden-signers` and **this domain** as co-owners
    (`docs/04-security-and-validation/validation-status.md`, Part II item 5). **This domain does not
    resolve it**: it quotes domain 08's rows as the record does, and states here that the quoted
    margin is one of two in the programme. What a resolution needs: a row-by-row mapping between
    E1–E8 and R1–R5, the charged/uncharged terms aligned, and the unit question settled — the
    validation package notes that the same construction passes at `+23.0` bits in gate units and fails
    at `−11.0` in query units, and that the assumption carrying the difference (`A-cost`) is not
    proved.

---

## 8. What this build verified, and what it did not

Verified by re-running (details and exit codes in `VERIFICATION.md`): both suites in full; the 24
attempts and 0 violations; the fitted exponents and the measured threshold; the self-tests; the
production ledger values as printed; the CFHL constants re-derived from domain 06's checker.

**Not verified, and not claimed:** anything the record measured that requires resources absent here
(the production prover runs of the record's §8 were not re-run — they are a size-and-time measurement
of a C prover, and their numbers are quoted from the record); the unshipped SAT experiments; the
independent pass's own artifacts; anything under the six assumptions.
