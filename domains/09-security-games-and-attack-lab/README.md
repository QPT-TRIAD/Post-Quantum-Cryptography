# 09 — Security games and attack lab

This domain is the empirical half of the programme's security argument: the games the CE-QS
construction is required to survive, and the attacks that were actually run against it.

Two Python harnesses carry it. `src/ceqs_attack_lab.py` (v1.51) asks the weak question — *did any
attack succeed?* — by running 24 violation attempts against the real implementation and counting the
successes, then measuring how the real attacks scale at deliberately weak parameters.
`src/ceqs_games.py` (v1.52) asks the sharper question: it states each attack as a **game**, defines
the attacker's information and oracle, measures the query complexity `Q` as a function of the
parameter, fits an exponent, and compares it with theory. Its stated point is the reverse of a
sales pitch: the fits are shown **not** to be able to establish a 128-bit level, and the
extrapolation error is measured rather than hidden.

Neither harness proves anything about the production security level, and both say so themselves.
The security level comes from the reductions in domain 08 (`domains/08-hidden-signers/docs/mode-b-security.md`); this domain
supplies the scaling laws those reductions assume, the end-to-end demonstrations that the winning
conditions are reachable, and the negative test result that the deployed implementation rejects the
attack classes tried against it.

---

## 1. How to read this domain

| Order | File | What it is |
|---|---|---|
| 1 | this file | the two harnesses, the games, the boundary of what they establish |
| 2 | `src/ceqs_attack_lab.py`, `src/ceqs_games.py` | the harnesses; docstrings state scope and limits |
| 3 | `results/attack-lab-results.md` | the recorded write-up of both harnesses (v1.51/v1.52) |
| 4 | `docs/attack-lab.md` | every one of the 24 attempts, its method, its parameters, its result |
| 5 | `docs/games-methodology.md` | how `Q(n)` is measured, how the fits are made, the caveat |
| 6 | `docs/game-frame.md`, `docs/game-suppress.md`, `docs/game-evade.md`, `docs/game-safety.md` | one document per game: definition, property claimed, status of the argument |
| 7 | `docs/validation-status.md` | what must still be validated for these claims to count as a proof |
| 8 | `VERIFICATION.md` | the re-run record: commands, timings, counts, discrepancies |
| 9 | `results/` | the recorded results, plus the raw output of the re-runs in this repository |

`results/attack-lab-results.md` is the recorded document and is shipped byte-identical to the
source revision (sha256 `7638c8ca…`), so its file names are the historical ones. The mapping to the
repository's own layout is in §6 below.

---

## 2. The system under test, in the terms the games use

The construction is a **hidden-signer quorum certificate**. A fixed registry assigns each of
`N = 64` seats a public key in every domain `d`:

```
Y[d][i] = F(s_i ‖ r_i)          (F public, (s_i, r_i) the seat's opening)
```

`F` is a public quadratic map over GF(2^256), expanded from a 32-byte seed; in production it takes
`2n = 512` input bits and returns `1024` bits (expansion `E = 512`), with `ρ = 4,096` quadratic
monomials per equation. A certificate for a message `m` in domain `d` carries the 43 handles of a
quorum (`Q = 43` of 64, so any two quorums intersect in at least `MIN_OVERLAP = 22` seats):

```
Z_i = r_i^7 ⊕ c_a·s_i ⊕ c_b·s_i² ⊕ c_c·s_i⁴          (the v1.50 "linearized" handle)
```

where `(c_a, c_b, c_c) = H(cfg, d, m)` is a 768-bit challenge triple derived from the message and
the domain. The handle is public; the opening is not. Anyone holding a seat's opening can place
that seat's handle in a certificate, so the certificate hides *who* signed, and only a **conflict**
reveals it: given two accepted certificates of the same `(cfg, d)` with `m₀ ≠ m₁`, the public
extraction function recovers the 22-or-more common seats' openings, and a public
`verify_blame` re-checks each one.

That structure defines the four games below: an attacker either **frames** an honest seat (FRAME),
**silences** extraction (SUPPRESS), **evades** blame while equivocating (EVADE), or tries to
equivocate with too few corrupt seats (SAFETY). The properties at stake are non-frameability,
accountability, and the quorum-intersection threshold.

The toy parameters used everywhere in this domain are deliberately weak: `n = 8 … 17` bits of
opening, expansion `E = 2 … 12`. A toy instance is redrawn when the weak widths cause a birthday
collision among handles, because the implementation correctly refuses to encode an ambiguous
certificate. No measured number in this domain is a claim about the production parameters, and both
harnesses print that caveat themselves.

---

## 3. The games, in the order a reader should meet them

The general shape of every game is fixed by `docs/games-methodology.md`:

```
GAME -> attacker's information -> allowed oracle queries -> winning condition
     -> attack algorithm -> measured Q(n) -> fitted exponent -> theoretical bound
```

| Game | Winning condition | Property claimed | Status of the argument |
|---|---|---|---|
| **FRAME** | output `(s′, r′)` with `F(s′‖r′) = Y[d][i*]` for an honest seat `i*`, so that a handle for `i*` can be placed in a conflicting certificate and extraction names it | non-frameability of honest seats | security level: a **reduction** (domain 08, Theorem 1, conditional on assumption A-F1); this domain: **measurement** of the scaling and a demonstration that the win is reachable |
| **SUPPRESS** | find `m₀ ≠ m₁` in one domain whose challenge *triples* are equal, so the difference map `D ≡ 0` and extraction cannot solve for `s` | accountability: extraction always names the culprits | structural part: **elementary proof** (linearized-polynomial kernel lemma, kernel dimension ≤ 2); costs: **measurement** here and a **transplanted bound** (CFHL Theorem 5.29, via domain 06) |
| **EVADE** | equivocate with 22 corrupt seats and make extraction name fewer than 22 | completeness of blame: a single evader must not hide the others | **measurement** of the linear-trick cost, plus an end-to-end regression of the domain 08 fix; binding assumption is A-F2 |
| **SAFETY** | with `C ≤ 21` corrupt seats, produce two accepted conflicting certificates at all | the quorum-intersection threshold: equivocation requires `C ≥ 22` | **counting argument** (elementary), tested exhaustively `C = 0 … 23`; completeness of blame measured; extra names are bounded handle coincidences |

Measured results (recorded in `results/attack-lab-results.md` §12 and reproduced in this
repository):

- **FRAME**: mean `Q` = 144.7, 664.8, 1,153.3, 4,942.5, 10,414.0 at `n` = 8, 10, 11, 13, 14
  (theory `2^(n−1)` = 128, 512, 1,024, 4,096, 8,192); fit `log₂Q = 1.0178·n − 0.931`
  (theory `1.0·n − 1.0`). The endgame demonstration frames the victim for real.
- **SUPPRESS**: one birthday law over both schemes, fit `log₂Q = 0.4498·h + 0.767`
  (theory `0.5·h + 0.326`), with `h = n` for the v1.46 handle and `h = 3n` for the v1.50 handle.
- **EVADE**: mean δ trials 7.0, 21.5, 61.5, 453.2, 1,322.0, 8,217.0 at `E` = 2 … 12;
  fit `log₂Q = 1.0242·E + 0.393` (theory slope 1.0). One evader costs exactly itself.
- **SAFETY**: measured threshold `22 =` theoretical threshold; no genuine double-signer was ever
  missed for `C ∈ {22, 23}`.

---

## 4. The attack lab: what was attacked, with what, and what happened

`src/ceqs_attack_lab.py --all` runs six experiments (A–F) at toy parameters:

- **A — negative tests.** 24 attempts to violate the deployed Mode B v1.50 implementation at
  `n = 14`, expansion 8, 64 seats, quorum 43: forged or invalid witnesses (7), malformed encodings
  (10), extraction preconditions (4), accountability attacks (2), and one **positive control**
  (an honest conflict) that must succeed. Each attempt must be rejected with the implementation's
  own reason. **Result: 0 successful violations of 24**; the positive control extracted 22 seats
  and every blame verified.
- **B — framing scaling.** Full enumeration of the real key map: the marked set `M` (openings
  consistent with both the registry key and the published handle) was **1 in all 60
  target-instances**, for the power handle and the linear handle alike, so there is no shortcut
  below exhaustive search. Fitted classical slope 1.107 bits per bit (theory 1.0). A control at
  `n = 8` shows what the published handle costs the defender: with no handle the search space is
  `2^(2n) = 2^16`, with the handle it is `2^n = 2^8` — guess `r`, derive `s`, test `F`.
- **C — exact Grover simulation.** numpy state-vector simulation of the real oracle: the measured
  optimal iteration count equals the predicted one at every size, and the success probability
  tracks `sin²((2k+1)θ)` to within `5.3 × 10⁻¹⁵` at every iteration; fitted slope of
  `log₂(iterations)` against `n` is 0.512 (theory 0.5).
- **D — the real collision attack.** The linear-trick attack on the real key map: measured mean δ
  trials sit about **+1.2 bits above** `2^E`, fitted slope 1.037 (theory 1.0). The gap is
  explained, not unexplained: δ always lies in the kernel of `A_δ`, so `rank(A_δ) ≤ N − 1` and
  consistency costs `2^−(E+1)`. **The ledger's `2^−E` density is therefore conservative.**
- **E — the challenge-collision fix, before and after.** Reproduces the break against the v1.46
  handle (a challenge collision after 234 messages makes extraction fail with "inverse of zero"
  and names nobody) and shows the v1.50 handle surviving a first-coefficient collision (the same
  style of collision, found after 172 messages, names all 22 seats).
- **F — the ledger.** Measured exponents beside the predicted ones, and the production ledger rows
  they feed: framing −145.0, binding −209.0, proof soundness −138.1, simulation −159.4, false
  positive −181.2, total **−137.7** (a margin of 7.7 bits against the D2 target). These rows are
  domain 08's ledger (`domains/08-hidden-signers/src/mode_b_rigorous_ledger.py`), printed by the lab
  and **not recomputed here**. They are also **not reconciled** with the target domain's own ledger
  (rows E1–E8, +29.4 bits in gate units): the programme's validation package records the 21.7-bit gap
  between the two margins as an open item naming this domain as a co-owner
  (`docs/04-security-and-validation/validation-status.md`, missing item 5). See
  `docs/validation-status.md` §7.

**What this proves, and what it does not.** A lab that finds no violation is *evidence*, not proof:
it is a finite campaign over one parameter set, one seed schedule and one revision of the
implementation. `results/attack-lab-results.md` §10 states the same boundary: no security level is
proven here; the proof system's QROM soundness row is transplanted from FAEST v2 Lemma 9.39, not
re-derived; gate costs are not simulated (Experiment C counts oracle invocations, and the ledger
charges ≥ 2¹⁸ gates per evaluation separately); privacy (A-P) remains decisional — the search-based
screen found no distinguisher, which is evidence, not a reduction; and the trusted-aggregator
premise (A-Prove) is a protocol assumption, not a property of these artefacts.

**Which attacks were not attempted.** Nothing in this domain runs: a cryptanalytic attack on the
key map `F` itself (XL / hybrid / algebraic elimination) — that evidence lives in domain 08's
cryptanalysis section and its XL model estimates; any lattice, code-based or Gröbner attack on the
underlying quadratic system; a real quantum execution (Experiment C simulates the algorithm
classically and charges no gates); side-channel, fault-injection or implementation attacks;
attacks on the proof system's zero-knowledge or on VOLE-in-the-head; anything at production
parameters — every measured exponent is at 8–17-bit openings, and §7 of
`results/attack-lab-results.md` records the production implementation runs (certificate sizes
30,684 B / 28,708 B, prove 60 s / 219 s) as a separate, size-and-time measurement.

---

## 5. The unshipped SAT experiments, and what depends on them

`domains/08-hidden-signers` records SAT experiments (`sat_attack.py` — CryptoMiniSat encodings of the
key map plus handle —, `sat_scale.py`, `collision_sat.py`, and neighbours such as `dreg.py`,
`modeb_hybrid.py`, `collision_trick.py`). Those scripts are **not in this repository**: the
hidden-signers record itself labels them "analysis scripts, not shipped with this record"
(`domains/08-hidden-signers/docs/hidden-signer-32kib.md`, the paragraph naming them). What survives is
a summary in `domains/08-hidden-signers/docs/mode-b-security.md` §9: SAT slopes of 2.42 bits per bit
with no handle, 1.29–1.58 with the linear handle, 0.90–0.93 with `r⁷`.

How strong that is, stated as the programme's validation package states it
(`docs/04-security-and-validation/validation-status.md`, the excluded-pieces table and correction 5):
the scripts are scratchpad material, the one published comparison (sparse versus dense) hit its
25-minute cap **inconclusively**, and **CryptoMiniSat was never run on the verification host and its
version is not recorded**. The honest formulation is that the evidence bearing on the handle ranking
is attack-based and **thinner than a summary of "SAT slopes" suggests**. The ranking of `r⁷` above the
linearized handle survives only on the **XL / hybrid model**, and the generic bound is `2^128` for
both handles either way.

Checked against the sources, the precise consequence for **this** domain is:

- **The harnesses do not depend on them.** `src/ceqs_attack_lab.py` and `src/ceqs_games.py` import
  only the Python standard library, numpy (Experiment C), and the Mode B implementation they test.
  No SAT solver, no SAT script, no SAT result file is imported or read. Everything this domain
  measures therefore re-runs in full in this repository (see `VERIFICATION.md`).
- **One sentence of the record depends on them.** `results/attack-lab-results.md` §3 says of the
  measured `M = 1` result that "the SAT slopes show no r⁷-over-linear advantage". A reader cannot
  re-derive that sentence here, and per the validation package the slopes it names are scratchpad
  evidence. **This domain labels that sentence a model estimate, not a measurement.** The lab's
  *own* evidence for the same conclusion is independent and re-runnable: the full enumeration of
  Experiment B gives identical marked sets for both handle kinds in all 60 target-instances, so there
  is no observed shortcut for either — that part is a measurement, and it stands without the SAT
  experiments.
- **The ranking is a model estimate either way.** Domain 08's own correction (`domains/08-hidden-signers/docs/mode-b-security.md`
  §9 item 5) states that the `r⁷`-over-linear ranking rests on the XL model, not on the SAT
  experiments, and that the security bound is the generic `2^128` for both handles.

---

## 6. Names: the record's file names and the repository's

`results/attack-lab-results.md` is shipped byte-identical to the source revision, so it names files
by their historical (versioned) names. The repository's copies are:

| Name in the record | Repository path |
|---|---|
| `ceqs_attack_lab_v1.51.py` | `src/ceqs_attack_lab.py` (this domain) |
| `ceqs_games_v1.52.py` | `src/ceqs_games.py` (this domain) |
| `hidden_signer_modeB_v1.50.py` | `domains/08-hidden-signers/history/hidden-signer-mode-b-v1.50.py` |
| `hidden_signer_modeB_v1.46.py` | `domains/08-hidden-signers/history/hidden-signer-mode-b-v1.46.py` |
| `modeB_prover_v1.50.c` | `domains/08-hidden-signers/history/mode-b-prover-v1.50.c` |
| `modeB_rigorous_ledger_v1.47.py` | `domains/08-hidden-signers/src/mode_b_rigorous_ledger.py` |
| `modeB_security_v1.49.md` | `domains/08-hidden-signers/docs/mode-b-security.md` |
| `sidecar_free_certificate_v1.44.py` | `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` |
| `qpt128_finalization_v1.43.py` | `domains/06-qpt128-security-target/src/qpt128_finalization.py` |

The two harnesses **pin the revision they were written against**: they load
`../../08-hidden-signers/history/hidden-signer-mode-b-v1.50.py`, which loads the v1.46 base module
from the same directory. That is the revision the recorded results were measured against, and it is
kept unchanged in the hidden-signers domain for exactly this purpose.

Domain 08's current Mode B revision is v1.51, which adds input-canonicality checks to v1.50 — `encode`
now requires a 64-byte `domain` and a `bytes` `proof`, `parse` requires `bytes` — and those checks add
rejection paths, so they are exactly what could change a rejection reason. Both suites were therefore
re-run against that revision during this build, end to end: the lab's 24 attempts produce the same 24
reasons, and the two full runs are identical to the v1.50 transcripts in all 87 and all 62 content
lines once the provenance header and the per-phase seconds are stripped — no measured value moves
(`VERIFICATION.md` records the comparison and both digests). A reader who wants the current revision
under test can change the one load line in each harness.

---

## 7. What this domain does not establish

- **No security level.** Every measured exponent is at 8–17-bit openings. Fitting an exponent over
  those sizes and extending it to 256 bits accumulates several bits of error in both directions —
  FRAME `+4.6` bits, SUPPRESS `−12.4` bits at `h = 256` and `−38.1` bits at `h = 768`, all measured
  and reproduced here. The 128-bit conclusions come from the reductions in domain 08, never from
  these fits.
- **No proof of non-frameability, binding or privacy.** The games measure the *cost* of attacks;
  they do not prove that no better attack exists.
- **No implementation security.** Timing, faults and side channels were not tested.
- **No re-derivation of the transplanted bounds.** The CFHL collision bound (Chung–Fehr–Huang–Liao,
  EUROCRYPT 2021, Theorem 5.29) enters through domain 06's checker; the QROM soundness row enters
  through FAEST v2 Lemma 9.39 (domain 08).
- **No SAT evidence.** §5 above.

`docs/validation-status.md` lists, claim by claim, what would still have to be supplied for these
results to count as part of a standard proof.
