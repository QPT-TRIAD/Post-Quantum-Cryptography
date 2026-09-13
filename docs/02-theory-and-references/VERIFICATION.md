# Verification

What was checked while this package was built, how, and what disagreed.

The package's own work is transcription: it restates what the theory-and-package index records and
points at the source file behind each entry. Verification therefore has one primary form — **re-open
the source file named by the entry and confirm the statement, label, citation and numbers against it**
— and a secondary form, where the source ships a runnable check and the claim is numeric: **run it**.

Two standing rules governed the pass. Nothing under the read-only source tree was written to: every
script was executed from a scratch working directory with bytecode writing disabled (`python3 -B`,
`PYTHONDONTWRITEBYTECODE=1`), and the one archive that had to be opened was extracted outside the tree.
And no value was "confirmed" from memory: each row below names the command that produced the observed
value.

Verdicts are `reproduced`, `reproduced-with-difference`, `not-reproducible`, `not-run`.

---

## 1. Entries checked against a source file

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| `D6-01` / register `Q1` — Lemma L1 statement | read `qpt128_finalization_v1.43.py:33-34`; `QPT128_finalization_v1.43.md:78` | read-only source tree | a uniformly random **256-bit** secret; `2^63` Grover iterations; success probability `> 2^-128` | both files carry that sentence verbatim ("After j = 2^63 Grover iterations the success probability exceeds 2^−128") | reproduced | The provenance of the refutation, and the wording disagreement in §2 below. |
| `D6-01` — the refutation reaches the ledger as a refutation | grep `REFUTED` in `qpt128_finalization_v1.43.py` | read-only source tree | the legacy target is marked refuted, not merely superseded | line 116 `Legacy D3 ledger (pqt.md final theorem) ... REFUTED by L1`; line 426 `D3='Pr<2^-128 for all QPT (legacy; refuted by L1)'` | reproduced | Two independent sites. |
| `D6-10` — Lemma L3 union bound | `python3 -B qpt128_finalization_v1.43.py --self-test`, test `test_05_L3_d2_implies_d1` | Python 3.12, scratch cwd | `8 · 2^-131 = 2^-128` exactly, checked at `G ∈ {1, 2^64, 2^128−1}` | `ok`; the assertion is exact-Fraction, not floating point | reproduced | The union-bound half of load-bearing entry 1. |
| the whole finalization ledger | `python3 -B qpt128_finalization_v1.43.py --self-test` | Python 3.12, scratch cwd | 19 tests | `Ran 19 tests in 0.043s` / `OK`, exit 0 | reproduced | Covers L1, L2, L3, L4, the ZKBoo parameters, the B0 gate-vs-query rows and the GHHM row dominance. |
| `D5-09`/`D6-07`/`D8-05` — DFMS coefficient actually used | read `qpt128_finalization_v1.43.py:230-239` | read-only source tree | the ledger's extraction row uses `(22ℓ+60)·q³·2^-n + 20q²·p_triv` | `v = (22 * ell + 60) * q**3 * pow2(-n_bits) + 20 * q * q * p_triv`, and the same term inside `joint_extraction` | reproduced | The `22ℓ+60` variant, not `20ℓ+60` or `72+40ℓ`. The three-variant table in `commitment-and-opening.md` §1 is therefore complete as written. |
| `D5-04`/`D6-08` — ZKBoo parameterisation | read `qpt128_finalization_v1.43.py:243-247` | read-only source tree | `ℓ = 4r`, `p_triv = (3/4)^r`, `v = 2(1+3r)` | all three, in the docstring and the return value | reproduced | |
| `D5-07`/`D6-04`/`D8-04` — HRS16 search term | read `qpt128_finalization_v1.43.py:84`; `modeB_rigorous_ledger_v1.47.py:87` | read-only source tree | `8·p·(q+1)²/2^n` | the same expression in both files (the ledger uses exact `Fraction`) | reproduced | |
| `D0-03`/`D5-08`/`D6-05`/`D9-04`/`D11-07` — CFHL collision envelope | read `QPT128_finalization_v1.43.md:120` | read-only source tree | leading term `40e²(q+1)³/M ≈ 295.6(q+1)³/M`, attributed to Chung–Fehr–Huang–Liao, EUROCRYPT 2021, Thm 5.29 | line present with that attribution and that constant | reproduced | Only the leading term is borrowed, as the entry says. |
| `D7` Theorem C budget — the current figures | `python3 -B sidecar_free_certificate_v1.44.py --self-test` | Python 3.12, scratch cwd | `τ = 14`, challenge 212, credential 218, **per-seat 359**, **max wires 141**; `theorem_c_budget(48) = 1006`; `grinding_bits=32 → τ 4 / 1258`; `challenge_hash_steps_log2=16 → τ 12 / 419`; `ggm_seeds → 280 / 770`; `theorem_c_budget(8)['max_wires_per_seat'] == -1` | `Ran 39 tests in 1.087s` / `OK`, exit 0, `test_theorem_c_wire_budget` among them | reproduced | This is the source of the §2 disagreement about which numbers are "pre-fix". |
| `D7-06` — Binius64 PCS floor | read `sidecar_free_certificate_v1.44.py:1074,1095,1862`; self-test above | Python 3.12 | `≥ 109,856 B` at 96-bit, versus the `27,056`-byte slot | `binius64_min_bytes(16) == 109856` asserted and passing; line 1095 states it "versus 27,056" | reproduced | Load-bearing entry 12. |
| `D7` — the hidden-signer slot | read `sidecar_free_certificate_v1.44.py:85,166` | read-only source tree | proof must fit `27,056 B` so the frame stays under 32,768 | `B1_PROOF_MAX = MAX_FRAME_BYTES - B1_PREFIX_BYTES  # 27056` | reproduced | |
| `D1-01`/`D3-08`/`D11-01` — quorum-intersection identity | `python3 -B bounded_checker.py` (audit-stack archive, extracted outside the tree) | Python 3.12, scratch cwd | boundary at `C = 2q−N`; `2q−N = 22` at `N = 64, q = 43` | exit 0; every row `ok`; `boundary C = 2q-N confirmed for N in [4, 5, 7, 10]`; final line: "ratified parameters: N=64 q=43 2q-N=22" | reproduced | Load-bearing entry 3, and the only one of the five that is fully proved. The same run reports the minimum intersection as exactly `2q−N` for `N ∈ {4, 5, 7, 10}`. |
| the audit stack's own math layer, `M1`–`M8` | `python3 -B math_layer.py` (audit-stack archive, extracted outside the tree) | Python 3.12 with `sympy` 1.13.1, `galois` 0.4.11, `numpy` 2.4.6; `sage` not installed | the recorded verdicts `M1`–`M8` = REPRODUCED | exit 0 after **230.4 s**; all eight verdicts `REPRODUCED` | reproduced | `M1` gives the symbolic threshold `−N + 2q`, `N64_q43 = 22`, and **no mismatches** over an exhaustive sweep `N = 4…64`. `M2` carries the CFHL query/gate logarithms and the multi-target pass/fail boundary. This is the strongest single re-run behind the counting identity. |
| `D8-07`/`D9-03`/`D11-05`/`D12-04`/`D12-06` — the linearized kernel lemma and the `9,756/20,000` fibre statistic | `python3 -B math_layer.py`, entry `M4` | Python 3.12 with `sympy` and `galois` | `D(s) = αs ⊕ βs² ⊕ γs⁴` has kernel dimension ≤ 2, tight; a non-linearized `s³` gives affine fibres `{0, 1, 3}` in `9,756/20,000` cases; an `s⁸` term reaches dimension 3 | exact match: GF(2^4) exhaustive over `4,095` triples, GF(2^6) over `262,143`, random GF(2^8)/GF(2^12); `max_dim = 2` and `non_subspace_cases = 0` in every field; `counterfactual_s3_non_subspace_cases = 9756`; `counterfactual_s8_max_dim = 3`; verdict `REPRODUCED` | reproduced | The record's own caveat is carried with it: the result is field-independent and says nothing about GF(2^256) being special. |
| `D8-11` — the 123.3-bit finding, and its later qualification | read `hidden_signer_32KiB_v1.46.md:22,83,85` | read-only source tree | `123.3` bits, below the 128-bit target, for the linear handle | line 83 gives the per-handle table (`148.8` classical / `123.3` quantum for the linear handle); line 85 adds a **later correction**: the SAT experiments do not support the r⁷-over-linear ranking, the ranking "rests on the XL/hybrid model only", and "the security bound is the generic `2^128` either way" | reproduced-with-difference | The index records the finding on its `D8-11` row and records the qualification in its **tool** catalogue (CryptoMiniSat, "not run here", the comparison "inconclusive"). A reader who saw only the `D8-11` row would miss the qualification, so the package now carries both on the entry. |
| `D4` `L3-num` — the rounds table | read `operators_1000_QPT128_amended_v1.33.md:160-177` | read-only source tree | `s = 32/64/92/128 → 73/137/193/265` and `88/165/233/320`; `J(2^128, 512, (9/16)^320) ≈ 0.025346 < 1/24 ≈ 0.041667`; `log₂ ≈ −5.302071` | the table and both boxed values appear exactly as the index records them, and the ledger states the comparison is exact-rational while the decimals are rounded | reproduced | The entry keeps the ledger's own qualifier: it is a conditional extraction component bound, not a forgery probability. |
| `D10-11`/register `I6` — the LMS size | read `FAILED_ASSUMPTIONS.md:28`; `pq_audit_s1_lms_v2.2.py:360` | read-only source tree | `1,768 ≠ 1,772`; the RFC figure is 1,772 | register row `I6` reads "1,768 ≠ 1,772 ... RFC 8554 carries two type fields"; the suite asserts `lms_sizes(8, 4)['sig'] == 1772` | reproduced | The 1,768-byte profile is refuted, not merely superseded. |
| register `A18` — the hybrid combiner | read `FAILED_ASSUMPTIONS.md:53` | read-only source tree | correlated seeds let the adversary recover `K` in `2,048/2,048` | the row says exactly that and records the fix as "independence listed as an untestable assumption; negative result kept" | reproduced | Both halves must be quoted together, as the domain document does. |
| `D6-13`/`D8` — GHHM Theorem 3 form | read `QPT128_finalization_v1.43.md:123`; `modeB_security_v1.49.md:118` | read-only source tree | `(3q_s/2)·√((q_H + q_s + 1)·γ(Commit))`, `γ ≤ 2^-512`, cited Grilo–Hövelmanns–Hülsing–Majenz, ASIACRYPT 2021, Thm 3 | both files carry that form and that attribution | reproduced | Cited by theorem number; the full text was never held. |
| `D8-01` — FAEST v2 Lemma 9.39 | read `modeB_security_v1.49.md:5,17,106,108` | read-only source tree | the soundness row is a **transplant** of FAEST v2 Lemma 9.39, deviations listed | the source states "proof by transplant of FAEST v2 Lemma 9.39; deviations listed, §5", and §5 lists them | reproduced | The citation is by lemma number only — no venue and no year anywhere in the source. The index states the stronger fact itself: one source "whose **full text the programme never held**", used three different ways across four domains. |
| `D10-07` — MTL Theorem 2 (MM-SPR) | read `pq_infra_program_v2.0.md:106,279` | read-only source tree | a citation with venue **and** ePrint number: Fregly–Harvey–Kaliski–Sheth, CT-RSA 2023; ePrint 2022/1730 | the author list and CT-RSA 2023 at line 106; `ePrint 2022/1730` at line 279 | reproduced | The entry is marked `[T]` **used as an assumption**, and the index's own qualifier — "measured only at n ≤ 14 bits" — is carried in the package. This is one the first draft had wrongly marked incomplete. |
| `D11-02` — the Tamarin N = 4 result (`12/12` lemmas, `111.31 s`) | `tamarin-prover --prove qpt128_quorum.spthy`; then `tamarin-prover --prove +RTS -M3000m -RTS qpt128_quorum.spthy`; then `tamarin-prover test` (all against the extracted archive copy, outside the tree) | Tamarin 1.12.0 with Maude 3.5.1, on a 15 GB host with ~7 GB available and swap exhausted | N = 4: all 12 lemmas verified, `111.31 s` (v0.1) / `126.74 s` (v0.2 re-run) | **not obtained.** The archive's own recorded invocation `tamarin-prover -M2500m --prove` is **rejected** by the installed 1.12.0 (`Unknown flag: -M`, exit 1); the heap cap has to be written as an RTS option, `+RTS -M… -RTS`, on that version. In that form the run starts, translates and closes the theory, then is killed during the first lemma with no lemma line and no error written; the same thing happens with no heap flag. `tamarin-prover test` returns "All tests successful", so the tool itself is sound and the kill is a host limit | not-reproducible | The record already documents this failure mode for the N = 7 run on the same class of host ("OOM-killed even at `-M8000m` … ~5 GB available"). Two independent findings are recorded rather than hidden: the **recorded command does not run as written** on the tool version the repository ships, and the re-run needs more memory than this host has free. The claim is therefore carried at the record's status and not upgraded, and the package's `D11-02` entry retains the record's own qualifications (small N; N = 4/7 reaches N = 64 only through the counting identity; no refinement link to the code). |
| `D0-10`–`D0-14` — the prior-art catalogues | read the catalogue sections of the research-journey records | read-only source tree | catalogue entries are contrast- or scope-only; none contributes a proof step | the records mark them as prior art and list them without use in any proof | reproduced | The package states this explicitly so a catalogue entry is not mistaken for a borrowing. |

---

## 2. Where the index and a source file disagree

Recorded as they are. None of these was smoothed over in the package documents.

### 2.1 The wording of the refutation (`Q1`)

- **Index.** Its summary of the refutation reads "Lemma L1: Grover on any **128-bit**-secret game gives
  `Pr ≈ 1` at ~`2^64` queries"; the same summary appears on the index's `D0-02` row ("search on a
  128-bit secret succeeds at ≈`2^64` queries").
- **The register in the source tree agrees with the index**, not with the script: its refutation row
  reads "Grover on any 128-bit-secret game … Grover gives `Pr ≈ 1` at `2^64` queries".
- **Source.** `qpt128_finalization_v1.43.py:33` proves the **256-bit** statement: a uniformly random
  256-bit secret, `2^63` iterations, success probability `> 2^-128`. The same wording is at
  `QPT128_finalization_v1.43.md:78`.
- **Exact disagreement.** The stated secret width (128 vs 256) and the stated iteration count
  (`2^64` vs `2^63`) differ, and the stated conclusion (`Pr ≈ 1` vs `Pr > 2^-128`) differs. The
  disagreement is therefore **inside the source tree** as well: the register and the script state the
  same lemma at different parameters, and the index carries the register's form.
- **Which is used here.** Both are quoted, each with its own provenance: the 128-bit/`2^64` form is
  attributed to the index and the register entry, the 256-bit/`2^63` form to the finalization script
  and its lemma number. The 128-bit form is consistent with the *original target* — which was an
  `Adv < 2^-128` claim — while the proof is carried out for the 256-bit secret the deployed key has.
  `gaps-and-unknowns.md` §1.1 and `quantum-search-and-accounting.md` §2 both carry this.

### 2.2 Theorem C's "pre-fix figures are 359 / 141"

- **Index.** States that the **pre-fix** figures are `359 / 141`.
- **Source.** `sidecar_free_certificate_v1.44.py:1892-1895` asserts, as the current shipped values,
  `{'tau': 14, 'challenge_bits_required': 212, 'credential_bits': 218, 'per_seat_budget_bits': 359,
  'max_wires_per_seat': 141}`. The pre-fix numbers are not preserved anywhere in the tree.
- **Exact disagreement.** `359 / 141` are the **current** source figures, not pre-fix figures; the
  pre-fix figures are unrecoverable.
- **Which is used here.** The package reports `359 / 141` as the current source values and records the
  pre-fix numbers as **not preserved**. `gaps-and-unknowns.md` §1.4.

### 2.3 The counting identity's notation

- **Index.** Writes the identity as `|S0 ∩ S1| ≥ |S0| + |S1| − N` and the threshold as `2q − N`.
- **Sources.** The construction-evolution record writes `|S0 ∩ S1| ≥ |S0| + |S1| − n` with `n = 3f + 1`
  and `q = 2f + 1`; the audit stack's checker writes `C = 2q − N` and prints `2q-N=22` at `N = 64,
  q = 43`; the bounded checker's own final line names the parameters "N=64 q=43".
- **Exact disagreement.** The letter naming the quorum size (`N` vs `n`) and the fault-model
  parameterisation (`N = 3f+1` with `q = 2f+1` versus a free `(N, q)`) differ between sources; the
  inequality itself does not.
- **Which is used here.** The package uses the index's `N` / `2q − N` form for the identity and records
  the source's `n` / `3f+1` form alongside it, so a reader meeting either letter knows which source it
  came from. `quorum-and-accountability-combinatorics.md` §1, with the four guises.

### 2.4 The amendment count (`130` versus `116`)

- **Index.** Its amendment section totals **130** amendments, composed as 82 in one range, 37 in
  another, and "11 elsewhere as recorded".
- **Sources.** The operator ledger's own section header describes "**116** specific corrections or
  restrictions, 28 operator mutations, 112 focused research questions"; the ledger-part-2 dossier's
  support sentence counts "**113 of the 116** amendments … have no executable witness".
- **Exact disagreement.** `130` (index) versus `116` (the ledger's own header and the dossier that
  the index is quoting). The index's own breakdown sums to 119 before the "11 elsewhere" term is
  added.
- **Which is used here.** Both figures are given with their provenance and neither is presented as
  the record's single number; the support sentence is quoted with the count the dossier uses.
  `project-statements-and-amendments.md` §3.

---

## 3. Checked against the index only

These entries rest on the index's own transcription. No source file behind them was re-opened during
this build — in most cases because the source is a dossier rather than a file in the read-only tree, or
because the value is a summary the index itself computed. A reader who needs one of these at the
strongest level must go to the pointer the entry names.

- The family-level catalogue counts and the operator-family amendment breakdowns.
- The nine reader flags on the operator ledger, and the extra v1.1 Theorem-26.1 mis-reference note.
- The prior-art catalogue entries taken from the research-journey records by identifier (arXiv numbers,
  venue names).
- **Lemur's corrected size** (`201.2 KB → 185.5 KB`). The correction is recorded in the index; the
  package repeats the corrected figure and does not attempt to re-derive it.
- The `9,756 / 20,000` fibre measurement, recorded in the dossier layer.
- The nine package-level gaps and the "what could not be determined" list, which are the index's own
  statements about its record.

---

## 4. Not run, and why

| item | why it was not run |
|---|---|
| The Tamarin N = 4 proof re-run | Attempted three times and **not reproduced** — see the row in §1. The prover and Maude are present and the prover's own self-test passes, so the failure is the host's memory headroom, the same limit the record documents for N = 7. Two side findings: the invocation the archive records uses a flag the shipped tool version no longer accepts, and the container pins an **older** Tamarin (1.10.0) than the host that produced the result (1.12.0), so the recorded command and the installed tool are not the same pair. |
| The Tamarin N = 7 run | The record itself reports it as **incomplete** (6 verified, none falsified) and resource-limited on the original host. Re-running it would not make the record complete, and the package's entry marks every N = 7 statement **partial** for that reason. |
| ProVerif, EasyCrypt and TLC | None of the three ever ran for this programme, so there is no recorded result to reproduce. The package records that status; it does not attempt the runs. `frame_b0.ec` is recorded as **admitted**, and would not type-check as written. |
| The domain test suites (domains 01–12) | Owned by their domain packages. The two suites re-run here are the ones whose numbers this package transcribes directly (the finalization ledger and the Theorem C budget); everything else is cross-referenced, not duplicated. |
| The infrastructure suites (`pq_infra_*`, `pq_audit_*`) | Their dependencies (`hsslms`, `dnspython`, an AVX-512 host) are absent or unavailable, and the record already marks their results as skipped or not-run outside the original host. |
| The container image | The full image was never built by the programme either; only the math image was, and the `Dockerfile` has recorded wiring defects. Building it here would prove nothing about the record. |
| Any sanitizer, fuzzing or SAT run | Not shipped as scripts (the SAT scripts are recorded as scratchpad), and the recorded runs are marked inconclusive or parameter-reduced. |

---

## 5. What this file is not

It is not a re-derivation of the mathematics. Where a source states a theorem and cites it, this
package confirms that the source states and cites it as recorded — not that the theorem is true. The
distinction matters for every entry whose citation is **incomplete in source** or **used as a
boundary**: those entries say so, and this file confirms only that they say so accurately.
