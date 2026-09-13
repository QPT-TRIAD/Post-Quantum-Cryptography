# Validation status

Two parts. **Part I** states what a referee would demand for this work to be accepted as a *standard
proof* rather than a well-documented research record, and where the work stands on each item.
**Part II** is the missing list, most blocking first, each entry naming the domain that would have
to supply it.

Nothing here softens a claim. Where a domain's own statement is weaker than a summary elsewhere in
the repository, this document follows the domain, and the differences are recorded.

---

# Part I — What acceptance as a standard proof would require

## 1. A complete reduction from a named hardness assumption, with no gaps

**A referee demands** a theorem of the form *"if hardness assumption `X` holds, then
`Pr[Win(A)] ≤ G(A)·2^−130`"*, with the reduction written out, every loss term accounted for, and the
reduction's own running time inside the same budget. The assumption must be named, published, and
one the community already accepts.

**Where this work stands.** No part of D1 or D2 is proved from a hardness assumption end to end.

- **D2 is proved from a ledger**, not from an assumption. The composition is a union bound (Lemma
  L3) over named bad events, each row an exact rational comparison of a bound *used as its source
  states it*. The rows are correct arithmetic about borrowed estimates; they are not a reduction.
- **Theorem A (public signers, B0)** is a tight linear reduction of non-frameability and safety to
  the EUF-CMA security of a category-5 signature — but the signature candidate is **not
  standardized and not FIPS-approved**, so "EUF-CMA at category-5 generic strength" is assumption
  `A-sig`, not a theorem this repository proves.
- **Theorem B (hidden signers, Mode S)** is conditional on six named assumptions
  (`A-QROM`, `A-F`, `A-cost`, `A-γ`, `A-MPC`, `A-protocol`), one of which — an ideal collaborative
  prover — **cannot be instantiated at all**.
- **The impossibility result that bounds the alternative (Theorem C)** is a theorem with proof under
  stated hypotheses, and it applies to a *family* of proof systems (KKW / BN++ / FAEST-style). It is
  explicitly **not a universal lower bound**. The accompanying size figures — the linear-family bound
  of 412,800 bytes and the Binius64 PCS floor of 109,856 bytes — are **estimates**, computed by
  re-implemented estimators.

**Verdict: not met.** The gap is not a missing lemma; it is that the reduction's hypothesis is a
non-standard signature assumption and the hidden-signer route has no instantiable backend.

## 2. Independently reproduced measurements

**A referee demands** that someone other than the authors reproduce the numbers, from the shipped
artifacts, on a different host — and that the artifacts still be buildable.

**Where this work stands.** Reproduction *within* the programme is unusually strong and is recorded
in this package's `VERIFICATION.md` and in each domain's own table:

- the ledger recomputed by an independent script from the shipped checker, all values agreeing;
- a second B0 implementation written from the specification alone, 6,701 of 6,701 comparisons in
  agreement;
- ML-DSA-87 and ML-KEM-1024 cross-validated against NIST ACVP vectors and a second implementation,
  with no disagreement, including 200/200 and 200/200 cross-signature and cross-encapsulation checks;
- the attack lab and the four games re-run here, output identical to the recorded run.

**What remains missing.**

- Every number in the repository was produced on **one host**, by **one programme**, and in several
  cases by a build process that also wrote the document quoting the number.
- The D10 governance and DNSSEC numbers were produced on the original host with packages that the
  audit host does not provide; the ledger runs 61/64 in the best case there, and claims resting only
  on the original-host runs inherit that status. This repository did **not** run the ledger
  end-to-end across all six suites.
- **The D3 proof sizes trace to binaries that never ran on the audit host** and cannot be rebuilt to
  the same digest (AVX-512 code paths). Those frames and byte tables are reported, not reproduced.
- The D2a/D2b artifacts (relation, checkers, ledgers, bounds JSON, frame adapter) are **absent from
  the tree**; their numbers can be carried only as reported.

**Verdict: partially met, within one programme and one host.**

## 3. A peer-refereed write-up

**A referee demands** a paper: a venue, referees, a version of record.

**Where this work stands.** There is none. No part of this work has been submitted for publication.
The theory it builds on is peer-reviewed; the composition, the construction, the ledger and the
impossibility result are not. The repository is the record of a research programme, and a sceptical
reader should price the absence of refereeing into every claim that is not a reproduction of someone
else's theorem.

**Verdict: not met, and not attempted.**

## 4. A specification stable enough to be implemented from

**A referee demands** that a competent implementer, given only the specification, produce an
interoperable implementation — and that the specification's normative clauses be the ones the
reference enforces.

**Where this work stands.** The B0 wire specification
(`domains/07-compact-certificate-b0/docs/b0-wire-spec.md`) is normative and was implemented from
directly by an independent implementation. That exercise produced 18 recorded ambiguities, of which
**4 are observable** — they can change wire bytes or verdicts:

1. bitmap bit numbering (value bit `2^i` versus the i-th bit of a big-endian byte string);
2. the encode side has no secret-key input, so a permuted registry has no defined encoding;
3. the toy verifier's prefix check is not specified, so a malformed public key can verify;
4. the vector-file format, including the encoding of `scheme_id`.

Two further findings stand against the reference rather than the specification:

- **F6** — the encoder does not enforce the 32,768-byte cap that the specification makes normative:
  at width 758 `encode_b0` emits 32,810 bytes without raising, and `verify_b0` rejects the result.
- **A.10** — two B0 tests mutate the frame at the wrong offsets relative to their names, so they pass
  without exercising the check they claim to test.

**Verdict: close for B0, with recorded gaps; not met for the hidden-signer profile**, which has a
frame, a relation and an extractor but no proof backend.

## 5. An independent second implementation, agreeing byte-for-byte

**A referee demands** a second implementation by a party that did not write the first, agreeing on
the wire bytes and on every accept/reject verdict.

**Where this work stands.** The audit stack contains exactly this, for B0: an implementation written
from the specification alone, checked against 900 generated cases — 6,701 comparisons covering
configuration, encoding, verification, extraction and blame, with the rejection clauses enumerated
(93 and 7 cases at clause 7.7/7.4, 100 at 7.3 in two families) and **no disagreement**.

**What it is not.** It is not an implementation by a party outside the programme; the vectors it is
checked against were generated inside the programme; and the hidden-signer path — the one with the
open problem — has no independent implementation.

**Verdict: met for B0 within the programme; not met for Mode S, and not met in the sense of external
independence.**

## 6. Formal proofs checked by a machine, with the run recorded

**A referee demands** machine-checked proofs, and the log of the machine's run.

**Where this work stands, layer by layer.** This is the area where the record is most easily
overstated, so each engine is listed with exactly what exists.

| Engine | What exists | Status |
|---|---|---|
| bounded exhaustive checker (a third, independent model) | exact enumeration of the counting fact and the extraction boundary for N ∈ {4, 5, 7, 10}; all rows ok; boundary `C = 2q − N` confirmed; three-candidate sanity re-check | **run recorded**; 0.45 s |
| Tamarin | N = 4: all 12 lemmas verified (111 s). N = 7: **6 of 12** verified; lemmas A, B, C1, C2, E2 and D1 did not complete (heap, timeout, or never started at 8 GB) | **partial** |
| bounded checker in the accountability domain | a separate Python finite-state checker: five PASS models with state and transition counts, three deliberately broken models that fail as expected, partition recovery, artifact-consistency lines; the earlier revision shows three PASS models and the line `TLC status: NOT RUN` | **run recorded** — but see the next row |
| **TLC / TLAPS** | the TLA+ specification of the accountability and epoch-barrier model | **never run, at any point in the record.** The specification is a specification document. All nine configured invariants hold *by construction* — they are type predicates or guard-enforced — so a TLC run would confirm that the module's guards are what they are; it would not independently discover a safety property |
| ProVerif | two protocol models | **never executed** — expectation only |
| EasyCrypt | a `frame_b0.ec` skeleton | **admitted, not proved**; never run |
| SageMath | — | **not installed**; the mathematics layer ran on SymPy and galois (8 of 8 checks REPRODUCED) |
| CryptoMiniSat | — | **never run here**; version not recorded |

**Verdict: partially met.** The strongest machine-checked artifacts are the bounded checker and the
N = 4 Tamarin run. Every claim that says "model-checked" must say by which engine; for the
accountability safety model the answer is a Python enumeration, not TLC.

## 7. The threat model stated, and matched by the argument

**A referee demands** that the adversary the argument is about be the adversary the model describes:
the same corruption bound, the same access, the same units, the same excluded powers.

**Where this work stands.** The model is stated explicitly (`threat-model.md`) and the argument is
bounded inside it. Three qualifications a referee would raise:

- **Units.** D2 is claimed in gate units, where B0 passes by 23.0 bits; in query units B0 fails by
  11.0 bits. The model's cost floor (`A-cost`, ≥ `2^18` T gates per oracle evaluation) is what
  carries the difference. The repository states the convention and keeps both tables rather than
  hiding the query-unit rows; it does not prove the floor.
- **Static corruption.** Corruption is static within an epoch. Adaptive or mobile corruption is
  explicitly not claimed, and the epoch rotation that bounds exposure is a system property.
- **Model-premise rows.** Four rows of the ledger (registry authenticity, canonical encoding, durable
  approval state, and B0's rollback row) are **set to zero**. They are premises; the margins are
  conditional on them, and they are the largest single gap in the ledger.

**Verdict: stated and matched, with the three qualifications above — none of which is a defect of the
exposition, all of which bound the claim.**

## 8. The excluded pieces accounted for

**A referee demands** that things the work did not do be listed as not done, with the reason.

**Where this work stands.** They are accounted for, and this document restates them because their
absence is load-bearing:

| Excluded piece | Status |
|---|---|
| a collaborative prover for the honest signer set (B1) | **does not exist**; `A-MPC` is an ideal functionality, and no size-conforming proof backend exists for the relation |
| TLC / TLAPS runs for the accountability specification | **never performed** |
| the SAT experiments behind the SAT-slope and sparse-versus-dense questions | the scripts (`sat_attack.py`, `sat_scale.py`, `collision_sat.py`) are **scratchpad material and are not shipped**; only summaries appear, and the sparse-versus-dense comparison hit its 25-minute cap **inconclusively** |
| EasyCrypt, ProVerif, SageMath | never executed |
| the full Docker image | never built; only the mathematics image was, and it reproduced 8 of 8 checks |
| MSan at production parameters | **inconclusive** (timed out without finishing, no diagnostics in the window); ASan at production parameters not run; no TSan, no valgrind, no AFL++, no KLEE |
| D11 claim C19 ("43-of-64 accountability under real consensus, 28/28") | **not verifiable from that domain's own archives**; it belongs to the excluded devnet material |
| the "16/16, 16/16" hash-signature property re-run | **withdrawn** (entry A28): the hash-signature property module fails at collection and executes **0 tests** |
| 116 operator-ledger amendments | **101 of 116 carry neither an executable witness nor a citation** (106 on a strict reading of "witness"). The earlier figure of 113 was measured against the second half of the file only and is superseded; three further witnesses are hard-coded or vacuous comparisons |
| the audit checklist total | the recorded `70/70 tests pass` includes test S1-011, which is a coin flip: over 200 runs the recorded assertion held in 49.0 %, a second 200-run pass in 53.5 %, and a third 100-run measurement made for this package in **52.0 %** (257 of 500 pooled; median 0.5109, range [0.313, 0.701]). The two exact per-seed assertions reproduce on every run; the slope assertion was replaced by a median over 41 random secrets |

**Verdict: met — the exclusions are recorded, and the two figures that were wrong (113/116, 16/16)
were corrected rather than rounded.**

---

# Part II — What is missing, most blocking first

Each entry names the domain that would have to supply it. "Blocking" means: without it, a reader
cannot decide whether the corresponding claim is true.

1. **A qualified proof backend for hidden signers, or a decision to drop profile B1.** No
   size-conforming proof system exists for the hidden-signer relation; `verify_b1` returns
   `STRUCTURE_ONLY_NO_QUALIFIED_PROOF` with `authorization_verified = False` by construction. Since
   B0 publishes its signer bitmap, **the repository has no profile that hides signers and is
   implemented**. Owner: `domains/07-compact-certificate-b0`, `domains/08-hidden-signers`.
2. **The value of `a` in the extractor-overhead lemma L5, and the provenance of every borrowed
   constant.** The extraction charge E1 enters every witness-bearing row, and the same coefficient
   appears as `22ℓ+60` (target domain), `20ℓ+60` (extraction domain) and `72+40ℓ` (operator ledger).
   The sources' claim that constants were checked against the full texts is a **process claim**, not
   a reproducible check; a live coefficient discrepancy is on record. Owner:
   `domains/06-qpt128-security-target`, with `domains/05-extraction-and-signature-reductions` and
   `domains/04-operator-ledger`.
3. **Charge or argue the model-premise rows (E6, E7, E8, and B0's rollback row).** They are set to
   zero; a margin is not a lower bound on the true margin unless they hold. Owner:
   `domains/06-qpt128-security-target`, with `domains/01-accountable-quorum-foundations`.
4. **Justify the cost floor `A-cost` at the level the verdicts depend on, or state D2 in query
   units.** The floor is a T-count of published circuits; depth, parallelism and memory are
   uncharged. Owner: `domains/06-qpt128-security-target`.
5. **Reconcile the two ledgers for the hidden-signer profile.** The target domain's ledger gives a D2
   margin of +29.4 bits in gate units over rows E1–E8; `modeB_rigorous_ledger_v1.47.py`, owned by the
   hidden-signers domain and quoted by the attack lab, gives 7.7 bits over rows R1–R5. Both pass, the
   margins differ by 21.7 bits, and neither document cross-references the other's row set. Owner:
   `domains/06-qpt128-security-target`, `domains/08-hidden-signers`, `domains/09-security-games-and-attack-lab`.
6. **Machine-check the things that are only enumerated.** TLC/TLAPS has never run on the
   accountability specification; ProVerif has never run; the EasyCrypt skeleton is admitted; Tamarin
   N = 7 is 6 of 12. Owner: `domains/01-accountable-quorum-foundations`,
   `domains/11-independent-audit-stack`.
7. **Complete the proofs that are sketches.** Lemma L4's convexity claim is stated but not written
   out; Lemma L5 is an estimate in the source's own word ("roughly"). Owner:
   `domains/06-qpt128-security-target`.
8. **Close the specification gaps and the encoder defect.** Four observable ambiguities in the B0
   wire specification; the encoder does not enforce the normative 32 KiB cap (F6); two tests
   misdescribe the offsets they mutate (A.10). Owner: `domains/07-compact-certificate-b0`,
   `domains/11-independent-audit-stack`.
9. **Cryptanalyse the construction's own new assumption.** The evidence for the expanding-random-MQ
   relation with a power handle is attack-based, and the attack-based evidence is *weaker than the
   repository summary suggests*: the SAT experiments were never shipped and their one published
   comparison was inconclusive, and CryptoMiniSat was never run on this host. A Gröbner-basis or
   Weil-descent analysis is open. Owner: `domains/03-zk-carrier-experiments`,
   `domains/08-hidden-signers` (the SAT slopes), `domains/02-ceqs-construction-evolution`.
10. **An independent implementation of the hidden-signer path, and external independence for B0.**
    The reasoning domains have no Mode S independent implementation; the B0 one exists but is
    internal to the programme. Owner: `domains/11-independent-audit-stack`.
11. **Constant-time and side-channel analysis.** None has been performed; the infrastructure
    assessments state the reference implementation is not constant-time. Owner:
    `domains/10-digital-infrastructure`, `domains/11-independent-audit-stack`.
12. **Reproducible builds for the D3-era evidence.** Those proof sizes trace to binaries that never
    ran on the audit host and are not rebuildable to the same digest. Owner:
    `domains/11-independent-audit-stack`.
13. **The missing D2a/D2b artifacts.** Relation, checkers, ledgers, bounds JSON and frame adapter are
    not in the tree; the numbers are carried as reported. Owner:
    `domains/02-ceqs-construction-evolution`.
14. **A referee.** No paper, no venue, no external review. Owner: the programme as a whole; no domain
    can supply it.
15. **Registration practicality.** The category-5 public keys the public-signer profile needs are
    large — OV-V alone is 446,992 bytes per seat, ≈ 28.6 MB for 64 seats — and their encodings
    overflow deployment fields in the infrastructure studies. Owner:
    `domains/07-compact-certificate-b0`, `domains/10-digital-infrastructure`.
16. **Evidence beyond one host.** Platform evidence at 64 seats is single-host, local-control
    observation; partition tolerance and liveness at scale are `not_run`, not passed. Owner:
    `domains/10-digital-infrastructure`, `docs/05-devnet-evidence`.
17. **Fix or replace the ledger and suite totals that are host-limited.** The audit ledger's 61/64
    and the checklist's 70/70 are host-dependent and the second includes a flaky test; the ledger has
    not been run end-to-end in this repository. Owner: `domains/10-digital-infrastructure`.
18. **Withdraw or substantiate D11's claim C19 (28/28).** It is not verifiable from that domain's own
    archives. Owner: `domains/11-independent-audit-stack`.

---

# Corrections to the drafted acceptance list

The drafted list this document was asked to check, extend and correct appears in the repository
summary. Item by item, what changed:

| Drafted item | Correction |
|---|---|
| 1. A proof backend for hidden signers (B1) | kept, and **strengthened**: Theorem C is conditional *for a family* of proof systems, not a universal lower bound, and B0 does not hide signers either — so the repository has no implemented profile that hides them |
| 2. Constants provenance | kept, and **sharpened**: a live coefficient discrepancy (`22ℓ+60` / `20ℓ+60` / `72+40ℓ`) is on record in the same repository, which is what the missing check costs in practice |
| 3. Named assumptions are not theorems | kept, and **extended**: the assumption list must be given in full (`A-sig`, `A-QROM`, `A-F`, `A-cost`, `A-γ`, `A-MPC`, `A-protocol`), because `A-cost` — not `A-sig` — is the assumption that carries every passing margin |
| 4. Complete proofs for the remaining lemmas | kept, and **corrected in weight**: L4's gap is exposition (the checker performs the endpoint evaluations); L5 is the load-bearing estimate, and its coefficient is one of three readings |
| 5. Cryptanalysis of the programme's own new assumption | **corrected**: the drafted wording implies SAT evidence exists. The SAT scripts were never shipped and their published comparison was inconclusive; CryptoMiniSat was never run on this host. The honest statement is that the evidence is attack-based *and thinner than the summary says* |
| 6. A second, independent implementation of the full certificate path | **corrected**: a second B0 implementation *does* exist inside the programme and agrees on 6,701 of 6,701 comparisons, including the extractor. What is missing is independence of provenance, and any implementation of the hidden-signer path |
| 7. Formal verification of the wire format and the extractor | **extended** with what has actually run: a bounded exhaustive checker and Tamarin N = 4 (all 12 lemmas); N = 7 is 6 of 12; TLC, TLAPS, ProVerif, EasyCrypt and SageMath have never run. Any prose saying "model-checked" must say by which engine |
| 8. Constant-time and side-channel analysis | kept; **extended** with the implementation-fault evidence that does exist and its limits (production-parameter sanitizer run inconclusive, thin fuzz coverage, a real verifier-side leak) |
| 9. Registration practicality | kept; the figure (OV-V, 446,992 bytes per seat, ≈ 28.6 MB for 64 seats) is the domain's |
| 10. Beyond this host | kept, and **extended** with the items the draft omits: the D3-era binaries are not rebuildable; the D2a/D2b artifacts are absent; D11's C19 is unverifiable; the withdrawn "16/16"; the flaky S1-011 inside the 70/70 total; 101 of 116 amendments without witness or citation; and the two ledgers whose margins differ by 21.7 bits |
| — | **added**: D2's verdict depends on the unit of account. B0 passes at +23.0 bits in gate units and fails at −11.0 in query units, and the assumption that carries the difference (`A-cost`) is not proved — so the unit question belongs in the acceptance list, not only in the target's own notes |
