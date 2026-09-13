# Gaps and unknowns

Everything the record **refutes, withdraws, contradicts, never re-ran, never installed, or cites
without a complete reference** — collected in one place so that a reader checking the programme's claims
does not have to reconstruct it from a dozen domain documents.

The order is deliberate: what is refuted first, then what was withdrawn or contradicted, then what never
ran, then what is cited incompletely, then what the record says **cannot be determined**.

---

## 1. Refuted

### 1.1 The original security target

**Refuted.** The target "`Adv < 2^-128` for every quantum-polynomial-time adversary" is unachievable as
stated: Grover search reaches probability ≈ 1 at roughly `2^64` queries on a 128-bit-secret game (the
finalization script's Lemma L1 proves the corresponding 256-bit-secret statement at `2^63` iterations
with probability `> 2^-128`). The target survives only as a **gate work factor**. This is register entry
`Q1` and it is the single most quotable result in the programme.

A wording discrepancy attaches to it and is recorded rather than smoothed: the refutation is attributed
in one place to "any 128-bit-secret game … ≈ 2^64 queries" and in the source script to the 256-bit statement
above. See `VERIFICATION.md`.

### 1.2 Theorem C's inequality direction

**Refuted.** The v1.44 Theorem C used the wrong **direction** of inequality: the attack argument needs an
**upper** bound on gates per hash (2^24 gates/hash → 2^104 iterations; budgets 359 / 1006 bits), not the
lower bound it was written with. This is register entry `Q2`.

### 1.3 The suppression attack's cost

**Refuted.** "Suppression of the v1.50 extraction costs `2^768`" is a **768-bit collision**, `2^252` in
the quantum model. **Three preimages had been counted instead of one collision.** The ledger was
corrected; the kernel lemma (`dim ≤ 2`) is invoked by the correction. Register entry `Q3`.

### 1.4 The pre-fix Theorem C numbers (359 / 141)

**Not preserved.** The index states that "the pre-fix figures are 359 / 141". The domain dossier states
that **359 and 141 are the current source figures** and that **the pre-fix Theorem C numbers are not
preserved**. Whatever is quoted must be the source's current numbers, with the direction correction
applied. See `VERIFICATION.md`, where this disagreement is recorded.

### 1.5 The 1,768-byte LMS profile

**Refuted.** The pre-fix LMS size of **1,768 bytes** does not follow from the profile's own parameters
(finding I6). The RFC-derived figure is **1,772 bytes**. Anything quoting 1,768 bytes is quoting a
refuted number.

### 1.6 The hybrid combiner's independence premise

**Falsified at the tested instances.** GHP18 / X-Wing protects against component failure only with
**independent** components. Register entry `A18` records that **correlated seeds let the adversary
recover `K` in 2,048 of 2,048 attempts** at each of seed bits 8/12/16 (ledger total 6,144/6,144). This
is a reproduced negative result, not merely an unproven premise.

### 1.7 The handle-as-a-security-choice claim

**Refuted.** The 123.3-bit finding: "handle as a security choice" does not hold — the hidden-signer
route's concrete accounting lands **4.7 bits below** the 128-bit target. It must not be rounded up or
re-quoted as "about 128".

### 1.8 Lemur's size

**Corrected inside the record:** 201.2 KB → **185.5 KB**. Quoting the corrected figure is the only
accurate option.

---

## 2. Withdrawn and contradicted

- **The compat-mode theorem** (the v1.37/v1.38 route for the 43-seat quorum) is **withdrawn**: the
  finalization document says "Replaced by B0 or Mode S". The v1.22 kill verdicts behind it (trace-only
  DEAD, compat mode DEAD) "rest on unsourced constants and estimates".
- **The "16/16" cell is withdrawn** (register entry A28).
- **The Mode B "7/7" claim is contradicted.**
- **The ledger's "16/16, 16/16" Hypothesis re-run claim is contradicted for hashsig and K12.**
- **The v0.1 "OOM-killed" line is an overstatement.** The claim that "(A, B, C1, C2, E2, D1, E1) are
  OOM-killed even at `-M8000m`" is wrong: exit 137 is recorded only for A, B, C1 and C2; E2 has no exit
  line; D1 and E1 never started. The runs also coincided with an 8-thread sanitizer production run. The
  overstatement must not be repeated.
- **The phase-GHZ security claim is abandoned**; only the simulation lemma is kept.
- **The v0.1 `frame_b0.ec` skeleton is admitted, not proved**, and would not type-check as written.

---

## 3. Never ran, never installed, or never completed

Numbered as the record numbers them, with the consequence for the repository.

1. **TLC never ran.** The TLA+ safety model is checked only by an independent Python enumeration; the
   specification has no executed state. **Any prose that says "model-checked" must say by what.** The
   epoch-barrier decomposition `81 = 3^4` is recorded as an explanation, **not a TLC measurement**.
2. **ProVerif and EasyCrypt never ran.** The audit stack's second and third protocol engines are
   **expectation only**; the `frame_b0.ec` proof is admitted. The ProVerif models' expected results are
   written in the models but were never observed, and one model line may not parse — unverified, because
   the tool never ran.
3. **The Tamarin N = 7 run is incomplete.** Lemmas A, B, C1, C2, E2, D1 and E1 were not completed
   (6 verified, 5–7 incomplete, **0 falsified**). Every N = 7 statement must be marked **partial**, and
   the N = 4/7 results reach the deployed N = 64 **only through the counting identity**. The N = 4 run
   itself could not be re-observed when this repository was built — the prover is present and its own
   self-test passes, but the proof run is killed on a host of the same size the record describes — and
   the invocation the archive records uses a heap flag that the installed prover version no longer
   accepts. Both facts are in `VERIFICATION.md`; the N = 4 figure is carried at the record's status.
4. **The domain-10 governance and DNSSEC numbers** were produced with `hsslms` and `dnspython` on the
   original host and are **skipped or not run** on the audit host; the ledger runs 61/64 in the best case
   with S1-011 failing. Claims resting only on the original-host runs inherit that status.
5. **Sanitizer coverage is incomplete.** MSan **timed out at 3,600 s** at production parameters
   (inconclusive); ASan was not run on v1.51 at production parameters; there is **no TSan**, and no
   valgrind, AFL++ or KLEE (no root). The "0 reports" results hold only for the executed parameter sets
   and seeds.
6. **CryptoMiniSat** is the sole support for the SAT-slope experiments and for the sparse-vs-dense
   conclusion, and its comparison run hit the **25-minute cap inconclusively**. The scripts are
   **scratchpad, not shipped** — the record is a summary, not a log.
7. **The domain-3 proof sizes came from binaries that never ran on the audit host.** The four adapter
   binaries contain AVX-512 EVEX instructions and the host has no `avx512f`; rebuilding changes their
   digest.
8. **libFuzzer coverage is thin:** 455 of 2,052 counters, 10 minutes, reduced parameters, and the
   QuickSilver arithmetic is not reached by mutation.
9. **The full container image was never built.** Only the math image was, and it reproduced 8/8. The full
   `Dockerfile` has recorded wiring defects (path mismatch on the ACVP fetch, a liboqs install path the
   wrapper does not read, an unused variable, and tool pins that differ from the host's).
10. **The domain-2a / 2b package artifacts are absent from the tree** — the v1.10 relation and checker,
    the v1.17 source ledger and fixtures, the v1.18 checker, the v1.19 model and loss ledger, the v1.20
    bounds JSON and frame adapter, the v1.21–v1.23 packages, and the v1.24 `contents_contract.py`. Their
    numbers can be carried only as **"reported"**.
11. **Claim C19** (43-of-64 accountability under real consensus, 28/28 passed) is **not verifiable from
    the audit-stack archives**; it belongs to the excluded devnet material.
12. **The "16/16, 16/16" re-run claim is contradicted** (repeat, because it is a claim about the
    repository's own testing discipline).

---

## 4. Open, not resolved

- **The `< 32 KiB` outer proof is open in every version** — the status tables read "Concrete <32-KiB
  outer proof: open" from v1.0 through v1.24. The final collaborative theorem does not close it.
- **No proof system fits the 27,056-byte hidden-signer slot** in the assessed families, and the
  hidden-signer verification path **never reports success** in code.
- **The carrier's backend carries `SECURITY_BITS = 96`**, a classical target, with **no quantum
  argument-of-knowledge or quantum-random-oracle extraction theorem** for Spartan + BaseFold/FRI, FRI
  soundness charging **only the query phase**, and the constraint system **not absorbed** into the
  Fiat–Shamir transcript.
- **The adaptive joint argument-of-knowledge theorem** for the carrier is open.
- **The consistent-opening condition** behind the conditional conflict-extraction theorem "is
  computationally motivated, not mathematically guaranteed by a finite hash".
- **The `9/16` contraction certificate is an assumption**, and the ledger states that the connection of
  the contraction to `p_*` is **open**.
- **The uniformity of seeded module matrices is not established** — the mandatory caveat on every
  restatement of the entropy argument.
- **The fixed deployed permutation is not certified** by the ideal-permutation bound; the gap
  `1 − 2^-h` is exposed rather than closed.
- **The A7 auxiliary-input PRF is flagged as needing replacement** and has not been replaced.
- **The GF(2^256) modulus used by the audit stack** (`x^256 + x^10 + x^5 + x^2 + 1`) has its
  irreducibility **unchecked** in that run.
- **The NIST ACVP vector files themselves are not in the archive**, only their recorded digests.

## 5. The nine reader flags on the operator ledger

Recorded as **open**; this package does not resolve any of them.

1. `C38`'s heading name ("Best/Birkhoff-van der Waerden") versus its definition (Birkhoff–von Neumann).
2. `G44`'s Bott property, stated for all `(n,k)` but apparently false at `k = n = 2`.
3. `K40` lacks the parallel amendment `K39` received.
4. `Y42`'s AGV individual-rationality claim.
5. `N3`'s `⊠_free` versus `⊞`.
6. `O10`'s amendment reuses `O9`'s text verbatim.
7. Checker-scope text versus code: group 13 does not assert event substitution; groups 4, 6, 8, 12 and
   16 compare hard-coded witnesses; `A28`'s contract tuple (line 775) differs from the checker's
   `FIELDS` (line 19,378).
8. `H16`'s "anti-commutes with itself: `β² = 0`".
9. **The `[S7]`/`[S9]` source-tag / operator-ID collision** at lines 488/503 — this must be resolved
   before anything citing `S7` is published.

An additional recorded inconsistency that behaves like a flag: **v1.1's Theorem 26.1 item 2** calls
Theorem 4.1 a "statistical uniqueness condition" while §7 and the v1.3 ledger attribute it to
*pseudorandomness*. The dossier marks it "likely a mis-reference, unverified against the source paper".

---

## 6. Cited without a complete reference

Reproduced in full in `references.md` §11. In summary:

- **Operator ledger:** `S1` (no theorem number), `S2` (no year, "et al."), `S5` (a web page, no date);
  **35 STD amendments carry no proof and no citation**, and **113 of 116 amendments have no executable
  witness**; only **H20, R36 and Y1** have one.
- **Domain 05:** Greenhill (no venue, no year); Hülsing–Kudinov 2022 and the ASIACRYPT 2022 paper
  **abstract only**; the share-of-witness definition.
- **Domains 06 / 07:** LaBRADOR; the KKW / BN++ / FAEST v2 size formulas; the MQOM round-2 tables.
- **Domain 08:** **every** cited source in its theory list.
- **Domain 10:** Buchmann–Dahmen–Hülsing 2011; "BBBV 1997"; DNS Flag Day 2020; the CNSA 2.0 FAQ; X-Wing;
  TESLA/OSNMA.
- **Domain 11:** CFHL ("the bound formula only"); FAEST v2.
- **Domains 02a / 02b:** the RLN specification, MinHash, TripleRing+, the LoTRS venue,
  `libtalos_voleith`, the DQS paper, DeTAPS, the FAESTer author list, "signature-in-signature".
- **Domains 09 and 12** inherit the citations of domains 06 and 08; domain 12 additionally records the
  four **pointer corrections** (A9, A10, A11, A15) and the four **wording corrections** (A18, A19, A20,
  I4) that **must be applied before any citation is carried into a bibliography**.

---

## 7. What could not be determined

**Do not guess these.** The record states that the following cannot be established from the sources:

- the interpreter version used for **any** pre-v1.29 Python run;
- the **pytest** version;
- the **GMP** version;
- whether **CryptoMiniSat** has a recorded version at all;
- whether the **Binius64 patch applies cleanly** to its pinned commit (asserted by the source, never
  re-tested);
- the **licence status** of the vendored Binius64 copy after patching (dual Apache-2.0 / MIT upstream;
  the added file carries the host crate's licence).

---

## 8. What this list is for

A reader who finds a claim in `domains/` should be able to check it against this list in one pass. If the
claim depends on one of the items above, the claim is **not** stronger than the item's status — a
refutation, a withdrawal, an unrun tool, an incomplete citation or an undetermined version. Where a
domain document quotes such a claim, this package's domain document carries the same qualification, and
`VERIFICATION.md` records which of these entries were checked against a source file during the build of
this repository and how.
