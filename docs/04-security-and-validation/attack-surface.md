# Attack surface: what was attacked, what was not, and what "no violation" means

The attack lab and the adversarial games are shipped in
`domains/09-security-games-and-attack-lab/` (`src/ceqs_attack_lab.py`, `src/ceqs_games.py`,
`results/attack-lab-results.md`). The independent audit stack's layers are in
`domains/11-independent-audit-stack/`. This page is the map: what was actually run against the
constructions, at what parameters, what was never run, and how much a null result is worth.

---

## 1. Attacks that were run

| # | Attack | Parameters | Result |
|---|---|---|---|
| 1 | **Violation attempts against the real implementation.** 23 rejection cases in four groups — 7 forged or invalid witnesses (altered opening, unregistered credential, another seat's opening, duplicate validator, replay under another message, replay in another domain, fewer than 43 rows); 10 malformed encodings (handle order, duplicate handle, truncation, trailing bytes, magic, version, suite, short quorum, message length, duplicate registration); 4 extraction preconditions (same-certificate replay, equal messages, cross-domain conflict, foreign registry); 2 accountability failures (framing an honest seat, fabricated blame) — plus one positive control | toy: n = 14, expansion 8, 64 seats, quorum 43 | **23 rejected, 0 successful violations, positive control extracted 22 seats** |
| 2 | **Framing by exhaustive enumeration.** The entire candidate space of the real key map is enumerated and the marked set counted (candidates satisfying both the registry key and the published handle) | n = 8…14, full enumeration, 6 targets per point | measured mean work tracks `2^(n−1)`; the marked set is 1 in 60 of 60 instances |
| 3 | **Exact Grover simulation** on the real oracle, state vector, closed-form comparison | n = 8, 10, 11, 13 | measured peak matches `π/4·√(N/M)`; max deviation from theory **5.3 × 10⁻¹⁵** |
| 4 | **The linear-trick / binding collision attack** (real attack on the real key map) | expansion E = 2…12 | measured mean δ trials grows at slope **1.0242** (theory 1.0); E = 12 needs a mean of 15,560 trials |
| 5 | **Challenge-collision attack found by an independent pass** — the one attack in the record that broke a shipped revision | v1.46, h = n | **v1.46 broken: extraction fails after 234 messages, 2^99.7 gates — 28 bits below the 2^128 budget.** Fixed in v1.50 by moving the challenge to h = 3n; v1.50 resists the same attack by 142 bits |
| 6 | **Four adversarial games** (FRAME, SUPPRESS, EVADE, SAFETY) stated as games with a winning condition, then measured | n ≤ 17, E ≤ 12 | see below; three of the four are winnable at toy parameters |
| 7 | **Protocol-level fault injection**, 11 fault classes (loss, duplication, reorder, delay, clock skew, restart, rollback, corrupt message, corrupt signature, corrupt certificate, equivocation) | 300 schedules, 1,717 checks | 3,700 corruption attempts, **0 accepted-on-invalid**, 33 conflicts extracted, **0 honest seats named** |
| 8 | **Mutation fuzzing** of the C verifier with a property oracle (accept ⇔ byte-identical to the genuine certificate) | 81,041 executions, 43 seeds, reduced parameters | **0 crashes, 0 accept-on-invalid, 0 reject-on-genuine**; coverage 455 of 2,052 program counters |
| 9 | **Sanitizers** (ASan+LSan, UBSan strict and recovering, MSan) with a build matrix from a pinned compiler | reduced parameters, plus one production-parameter attempt | MSan clean; UBSan reports 7 sites, all unsigned shifts or implicit truncations that the code performs by design; **LSan found a real verifier-side leak** (9,568 bytes per rejected proof) |
| 10 | **Differential testing** against a second implementation and against published vectors | B0: 900 cases; ML-DSA-87/ML-KEM-1024: full ACVP groups plus 200/200 and 200/200 cross-checks | 6,701 of 6,701 comparisons agree; no disagreement with ACVP vectors; no tampered signature or key accepted |

The games deserve separate note, because they are the only part of the record that measures an
*exponent* rather than checking a rejection:

| Game | What the attacker wins by | Measured fit | Theory |
|---|---|---|---|
| **FRAME** | recovering an honest opening and naming that seat | `log₂Q = 1.0178·n − 0.931` | `1.0·n − 1.0` |
| **SUPPRESS** | a challenge collision that silences extraction | `log₂Q = 0.4498·h + 0.767` | `0.5·h + 0.326` |
| **EVADE** | equivocating with 22 corrupt seats and hiding the culprits | `log₂Q = 1.0242·E + 0.393` | slope 1.0 |
| **SAFETY** | equivocating at all with ≤ 21 corrupt seats | **impossible for C ≤ 21, possible at C = 22** | threshold 22 |

Two of the games did real work rather than confirming a prediction:

- **SAFETY found a false positive path.** At C = 22, extraction named 23 seats where 22 are genuine
  double-signers: a seat present in only one certificate can be named when its *would-be* handle
  under the other message coincides with a published handle. It is a framing attack, its rate is
  measured (0.5767 at n = 11 falling to 0.0100 at n = 17) against the prediction `42·43/2^n`, and it
  is driven by the handle width, not the registry-key width. This **corrected the ledger**: the
  false-positive row R5 moved from −943 to **−181.2**, about 760 bits larger. No verdict changed.
- **SUPPRESS is the fix made visible.** The same game is played by two revisions of the scheme on
  different output lengths, and one law fits both — the fix did not invent new hardness, it moved the
  challenge width from 256 to 768 bits.

## 2. Attacks that were not run

- **Nothing at production parameters.** Every attack above runs at 8–17-bit openings and expansions
  of 2–12. Production is a 256-bit opening with expansion 512. No attack in this repository has been
  executed against a production-size instance, and no result here is a security claim at production.
- **No cryptanalysis of the underlying problem.** No Gröbner-basis, XL, hybrid or Weil-descent
  analysis at production size. The attack-based evidence for the relation's hardness is **thinner
  than summaries elsewhere in the repository suggest**: the SAT scripts were never shipped, the one
  recorded sparse-versus-dense comparison hit its 25-minute cap inconclusively, and CryptoMiniSat was
  never run on this host.
- **No side-channel work of any kind.** No timing, cache, power, electromagnetic or physical
  fault-injection analysis, and no constant-time audit. The reference implementation is not claimed
  to be constant-time. The fault injection in row 7 is protocol-level — malformed messages and
  schedules — not physical.
- **No network-level adversary inside this model.** The target says nothing about availability, so
  denial of service is not an attack this lab can register even in principle. (The broadcast layer of
  the wider programme did run its own games and found two receiver defects including a
  denial-of-service path through an unauthenticated replay filter — recorded as entry A15, owned by
  the infrastructure domain. That work was not re-run for this package.)
- **No attack on the hidden-signer proof system**, because there is no proof system: profile B1 has a
  relation, a frame and an extractor, and `verify_b1` returns
  `STRUCTURE_ONLY_NO_QUALIFIED_PROOF` without ever reporting an authorization.
- **No attack on the ledger's premises.** The zeroed rows (registry authenticity, canonical encoding,
  durable approval state, rollback) cannot be attacked by this lab at all: they are assumptions about
  a deployment, not properties of these artifacts.
- **No quantum hardware.** Grover is simulated exactly at toy sizes; no physical quantum device was
  used, and no such device could run these instances.

## 3. Three things that were not "passing" in the ordinary sense

- **Three audit suites did not run at all** after the rename this repository applies: a loader build
  from a file name broke at import, so `s2_dns_worstcase`, `s3_tls_wire` and `s4_tesla_adversarial`
  executed **0 tests**. The repair is a rewrite of the loader strings; the end-to-end totals are the
  owning domain's.
- **One recorded PASS was a coin flip.** Test S1-011's slope assertion held in 49.0 % of 200 runs in
  one measurement, 53.5 % of 200 in a second, and **52.0 % of 100** in a third made for this package
  (257 of 500 pooled; median 0.5109, range [0.313, 0.701]); the recorded PASS was a lucky draw. Its
  two exact per-seed assertions reproduce on every run.
- **One recorded property-suite claim was withdrawn.** The hash-signature "16/16" is withdrawn
  (entry A28): the module fails at collection and executes 0 tests, because the fix it was meant to
  validate correctly refuses the key it constructs at import.

## 4. "The lab found no violation" versus "there is no violation"

The difference is the whole of this section, and it is not a rhetorical one.

**What a null result establishes here.** That a specific implementation rejected a specific,
enumerated set of 23 malformations, for the stated reasons, at a stated parameter set — and that a
fuzzer could not find an input it accepts other than the genuine certificate, within 81,041
executions and roughly a fifth of the binary's basic blocks. That is a regression test of real value:
it is what tells a reader the accept/reject logic does what the specification says at those sizes.

**What it does not establish.**

1. **It is not a lower bound on attack cost.** 24 attempts that failed say nothing about the
   attempt that was not tried. An adversary's cost is bounded only by an argument, and the arguments
   here are the ledger's rows.
2. **It does not transfer across parameters.** Nothing tested at n = 14 bounds n = 256. Every attack
   in the lab is a *scaling probe*: what the fits establish is that the reduced systems obey the laws
   the ledger assumes — which is the strongest thing an experiment can say here.
3. **The extrapolations carry measured error.** Fitting an exponent at n = 8…19 and extending it to
   n = 256 accumulates bits in both directions: FRAME **+4.6 bits**, SUPPRESS at h = 256 **−12.4
   bits**, SUPPRESS at h = 768 **−38.1 bits**. This is why the 128-bit conclusions come from the
   reductions, never from these fits.
4. **The security level is nowhere measured.** No experiment in this repository, at any parameter
   set, measures a 128-bit security level. The quantum rows are proven Grover/BHT bounds evaluated at
   a marked-set density measured on the real function; the other half of the claim is a reduction
   that is conditional on named assumptions.
5. **The counter-example is in the record.** The lab is not decoration: an independent pass found a
   genuine break in a shipped revision (row 5 above), and the SAFETY game found a genuine framing
   path and a 760-bit ledger error. A reader should treat the null results as *this lab has found
   what it could find*, not as *there is nothing to find*.

## 5. Where a sceptical reader should start

In rough order of return on effort:

1. **Read the query-unit rows.** `python3 domains/06-qpt128-security-target/results/ledger-independent-check.py`
   recomputes every headline value independently. The same script shows B0 passing D2 at +23.0 bits
   in gates and failing at −11.0 bits in queries. The cost floor is what separates those two rows;
   a reader who does not accept it has not been given the target for B0.
2. **Attack the zeroed rows.** A demonstration that one of E6, E7, E8 or B0's rollback row is false
   in a real deployment is enough: each one that fails is an uncharged bad event, and the margin
   stops being a lower bound.
3. **Attack the cost floor.** Exhibit an oracle circuit below 2^18 T gates, or a depth/parallelism
   argument the ledger does not charge. Every passing margin moves with it.
4. **Try to instantiate the hidden-signer backend.** The relation is over 43 hidden signers with a
   size budget of 757 bytes per slot. The repository's own impossibility result covers one family of
   proof systems and is explicitly not universal — a backend outside that family would be a genuine
   result.
5. **Try the encoder's size gate (F6).** `encode_b0` at width 758 emits 32,810 bytes without raising,
   while the specification makes refusal normative and `verify_b0` rejects the result. A deployment
   that trusts the encoder's output will hand out frames that its own verifier refuses.
6. **Implement from the wire specification alone and count the ambiguities encountered.** Four are
   already known to be observable; the specification is otherwise normative and was implemented
   from directly.
7. **Push the games past their measured range.** Extend the fits to larger n and larger E, and check
   whether the exponents hold — remembering the measured ±bits of extrapolation error, and that a
   better attack than the one the game encodes is exactly what a fit cannot rule out.
8. **Work the model's blind side.** Denial of service, liveness under partition, censorship of
   evidence holders and adaptive corruption are all outside the target. Nothing in D1/D2 forbids
   them, and no experiment here tests for them.
9. **Re-run the production-parameter validation that never finished.** The sanitizer run at
   production parameters timed out without completing and is recorded as inconclusive, not clean;
   the fuzz campaign ran at reduced parameters and never reached the degree-6 arithmetic by mutation.
   That region is the least-exercised part of the implementation.
10. **Rebuild the D3-era evidence.** Those proof sizes trace to binaries that never ran on the audit
    host; a successful rebuild with matching digests would close one of the largest gaps in the
    measurement record.

---

## Validation status

The statements above carry their labels. What must still be validated for this work to be accepted
as a standard proof, and what is missing, is in `validation-status.md`; the commands re-run for this
package, with their recorded baselines, are in `VERIFICATION.md`.
