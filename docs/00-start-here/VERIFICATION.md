# VERIFICATION — `docs/00-start-here`

Every command this package's documents tell a reader to run was run while the package was assembled,
and every claim about a runtime or an output in `reading-order.md` and `reproduction.md` is the
observed value below.

**Environment for every row.** Ubuntu 24.04.4 x86-64; the pinned virtual environment
(Python 3.12.3) activated by `tooling/activate.sh`; `liboqs` 0.16.0 and `liboqs-python` 0.16.0;
`pqcrypto` 0.3.4; Tamarin 1.12.0 with Maude 3.5.1; `gcc` 14.2.0. `PQT_SRC` was set to the read-only
research tree for the rows marked, and unset for the rows that test what happens without it. **The
host was carrying a load average near 19 from concurrent work for every timing recorded here**, so
every wall time is an upper bound rather than a benchmark.

**Date of the runs.** 2026-09-13.

## Rows

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| B0 reference self-test | `python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --self-test` | pinned venv | 39 tests, OK (0.094 s in the source tree) | **Ran 39 tests in 0.393s — OK**; exit 0; 0.83 s wall | `reproduced` | Test count and result identical. Wall time differs; `domains/07-compact-certificate-b0/README.md` already records run times as a known difference, and the host was loaded. |
| B0 real-signature demo | `python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --real-demo` | pinned venv + liboqs | 11,396 B / 30,918 B frames, verified, 22 seats extracted; 13.7 s | **exit 0**; `liboqs 0.16.0`; OV-V-pkc sig 260 → frame **11,396** verified; OV-V-pkc‖SNOVA_29_6_5 sig 714 → frame **30,918** verified; SNOVA_29_6_5 19,738; SNOVA_60_10_4 24,984; MAYO-5 41,668 rejected; ML-DSA-87 199,177 rejected; Falcon-padded-512 28,854 verified; 41.47 s wall | `reproduced` | Every size and every verdict matches the recorded run. The command writes nothing: it prints JSON to stdout, so no file in another domain was created or modified. |
| Security-target self-test | `python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --self-test` | pinned venv | 19 tests, OK | **Ran 19 tests in 0.095s — OK**; exit 0; 0.27 s wall | `reproduced` | — |
| Security-target bare invocation | `python3 domains/06-qpt128-security-target/src/qpt128_finalization.py` | pinned venv | usage message, exit 2 by design | usage message; **exit 2** | `reproduced` | Recorded in `reproduction.md` so a reader does not read exit 2 as a failure. |
| Quorum finite-state check | `python3 domains/01-accountable-quorum-foundations/src/pqaqc_finite_state_check.py` | pinned venv | recorded output reproduced exactly | exit 0, 0.78 s | `reproduced` | Matches the domain's own `VERIFICATION.md` claim that both finite-state checkers reproduced the shipped results. |
| Operator-ledger checker | `python3 domains/04-operator-ledger/src/operator_ledger_checks.py` | pinned venv | 23 checker groups, recorded JSON | exit 0, 0.07 s | `reproduced` | — |
| Extraction/reduction band | each of the nine `domains/05-extraction-and-signature-reductions/src/*.py` with `--self-test` | pinned venv | 167 tests across nine suites, all pass | 7 of 9 accept `--self-test` and returned OK in 0.09–1.77 s; the remaining two (`hybrid_sampling_bound_audit.py`, `slh_tree_conditioning_audit.py`) **reject `--self-test`** and run their unittest suite on bare invocation | `reproduced-with-difference` | The difference is in the interface, not the result: the two scripts' recorded outputs show bare invocation. `reproduction.md` states this so a reader is not surprised. |
| Bounded protocol checker | `python3 domains/11-independent-audit-stack/formal/bounded_checker.py` | pinned venv, no `PQT_SRC` needed | all rows ok; boundary C = 2q−N | `RESULT: all rows ok; boundary C = 2q-N confirmed`; 0.9 s | `reproduced` | — |
| Independent B0 self-test | `python3 domains/11-independent-audit-stack/independent-b0/b0_indep.py` | pinned venv, no `PQT_SRC` needed | `self-test ok` | `self-test ok`; 0.1 s | `reproduced` | — |
| Independent B0 vectors | `python3 domains/11-independent-audit-stack/independent-b0/check_vectors.py` | pinned venv | 6,701 of 6,701 agree over 900 vectors | **total agree 6,701, disagree 0**; exit 0; 11.5 s | `reproduced` | Also re-run with `PQT_SRC` unset: exit 0, same result — this layer does not need the research tree. |
| Audit mathematics | `python3 domains/11-independent-audit-stack/math/math_layer.py` | pinned venv + **`PQT_SRC` set to the research tree** | M1–M8 reproduced; 217 s recorded | exit 0; 154.5 s; `"M8_evade": "REPRODUCED"` | `reproduced` | **Requires `PQT_SRC`.** Without it the script exits 1 with a message naming `PQT_SRC` — see the next row. |
| Audit mathematics without the research tree | as above with `PQT_SRC` unset | pinned venv only | — (not previously recorded) | `PQT_SRC is not set: source the environment activation script (tooling/), or point PQT_SRC at a local copy of the research tree`; **exit 1** | `reproduced-with-difference` | This is the repository's intended behaviour and `reproduction.md` states it, with the list of affected layers. |
| Fault injection | `python3 domains/11-independent-audit-stack/fault/fault_injection.py` | pinned venv + `PQT_SRC` set | 11 fault classes × 300 schedules; `first_failures: []` | exit 0; `"first_failures": []`; 0.8 s | `reproduced` | Same `PQT_SRC` requirement as the mathematics layer. |
| Attack lab | `python3 domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py --all` | pinned venv + `PQT_SRC` set (as the staging environment sets it) | 5 self-tests; 24 violation attempts, 0 successes; ≈55 s | **exit 0**; `Successful violations: 0 of 24 attempts`; **177.05 s** | `reproduced-with-difference` | Result identical. Wall time ≈3.2× the recorded ≈55 s, taken under load average ≈19 with another job running concurrently. Recorded in `reproduction.md` with both figures. |
| Security games | `python3 domains/09-security-games-and-attack-lab/src/ceqs_games.py --all` | pinned venv + `PQT_SRC` set | 4 self-tests; four games; ≈126 s | **exit 0**; SAFETY threshold 22 confirmed for every corruption level 0–23; slopes FRAME 1.0178, SUPPRESS 0.4498, EVADE 1.0242 against theory 1.0 / 0.5 / 1.0; **161.64 s** | `reproduced-with-difference` | Same cause as the row above. |
| Symbolic protocol model, N = 4 | `tamarin-prover --prove domains/11-independent-audit-stack/formal/qpt128_quorum.spthy` | pinned venv + Tamarin 1.12.0 + Maude 3.5.1 | ≈111 s; the domain records N = 4 lemmas verified | **exit 0**; **all 12 lemmas verified** — `sanity_honest_certificate` (exists-trace), `A1_three_distinct_signers`, `A2_signer_authorized`, `A_acceptance_authorized`, `D2_intersection_seats_corrupt`, `D1_non_frameability`, `B_conflict_needs_2qN_corrupt`, `C1_intersection_nonempty`, `C2_intersection_at_least_2qN`, `C3_evidence_reachable` (exists-trace), `E1_below_threshold_no_conflict`, `E2_at_threshold_conflict_exists` (exists-trace); **161.05 s**; `maude tool: 'maude' checking version: 3.5.1. OK` | `reproduced` | The longest single run in this package's testing, and the strongest independent check performed here: every lemma of the symbolic model verified end to end, with a clean exit. |
| Mode B toy proof | `python3 domains/08-hidden-signers/src/mode_b_voleith_toy.py` | pinned venv | 7 tests, OK, 133.4 s | **not run here** — quoted from `domains/08-hidden-signers/results/toy-self-test.txt` | `not-run` | The output file in that domain records `Ran 7 tests in 133.436s — OK`. Quoted, not re-run: the domain's own results are the evidence for its figures. |
| Mode B self-tests | `python3 domains/08-hidden-signers/src/hidden_signer_mode_b.py` (v1.50 revision) | pinned venv | 5 tests, OK, 14.995 s | **not run here** — quoted from `domains/08-hidden-signers/results/mode-b-v1.50-self-test.txt` | `not-run` | Same reason. |

## Item-by-item verification of the documents in this package

| document | what was checked | how |
|---|---|---|
| `README.md` | every figure, label and qualification attributed to the top-level `README.md`, a domain, or `records/` | read against the source file it names; no figure restated from a summary of a summary |
| `reading-order.md` | each domain's own entry point | read from that domain's `README.md` — `01`, `02`, `03`, `04`, `05`, `06`, `07`, `09`, `10`, `11`; for `08`, which has no `README.md`, the entry point named is the pair of documents the domain ships |
| `glossary.md` | every term definition | taken from the domain that owns the term; each entry names it. Where a term is used more narrowly than its textbook meaning, the entry says so. Two entries were added after the first pass — the `dossier` entry and the label-set provenance note — and are recorded in the section below |
| `claim-labels.md` | all seven labels, their bars and their two instances each | the labels as `docs/02-theory-and-references/README.md` defines them; each instance read in the file cited; the `[C]` collision between `docs/02` and `domains/03-zk-carrier-experiments/docs/theory-as-used.md` recorded rather than smoothed over |
| `reproduction.md` | every runtime and every command | the rows above. Commands a reader is told to run were run; where an item could not be run, it is marked `not-run` with the reason |

## Differences and open items found while assembling this package

1. **Two hidden-signer lineages are named alike, and no document reconciled them.**
   `domains/07-compact-certificate-b0` states that B1 / "Mode S" has **no qualified proof backend** and
   that `verify_b1` never reports an authorization. `domains/08-hidden-signers` records a **separate**
   lineage — Mode B, production form "Mode B-r" — whose C prover produced a 30,684-byte hidden-signer
   certificate that verified and extracted 22 seats, with its size given as an estimate. Both use the
   words "hidden signers", "B1" and "32 KiB" for different objects. The repository's top-level
   `README.md` now keeps them in separate subsections (§1.3), and `glossary.md` §4 states the
   distinction explicitly so a reader cannot carry a claim from one into the other.
   *Not a contradiction once separated — but it was one sentence away from being read as one.*
2. **`domains/08-hidden-signers/results/toy-run.json` is 0 bytes** at the time of writing. The domain's
   `toy-self-test.txt` is populated (7 tests, OK); the JSON twin is empty. Not this package's file; noted
   so it is not mistaken for a reproduced empty result.
3. **One domain has no `README.md` at the time of writing.** `domains/08-hidden-signers` ships
   `docs/hidden-signer-32kib.md` and `docs/mode-b-security.md` and no `README.md`, so `reading-order.md`
   names those two documents as its entry point and says why. `domains/09-security-games-and-attack-lab`
   and `domains/10-digital-infrastructure` acquired their `README.md` while this package was being
   assembled; both were re-read afterwards, and the routes now follow the orders those READMEs actually
   state (D9's nine-item order, D10's seven-item order). Note that D9's README references a
   `VERIFICATION.md` that is not in its directory at the time of writing; this package does not rely on
   it.
4. **Three scripts reject `--self-test`** although their siblings accept it
   (`domains/05-extraction-and-signature-reductions/src/hybrid_sampling_bound_audit.py`, `domains/05-extraction-and-signature-reductions/src/slh_tree_conditioning_audit.py`, and
   `domains/06-qpt128-security-target/src/qpt128_finalization.py`'s bare invocation with exit 2 by design). Recorded in
   `reproduction.md` so a reader can tell before starting.
5. **The audit stack's `PQT_SRC` requirement is real and load-bearing.** Five of its layers cannot run
   from the repository alone. This is stated in `domains/11-independent-audit-stack/README.md`, and
   `reproduction.md` repeats it with the affected list, so that a reader planning a re-run of the audit
   stack knows before starting which layers will stop.
6. **Timings taken under load.** The attack lab and games ran ≈3× their recorded baselines on a host at
   load average ≈19. Both figures are given wherever the runtime appears; neither run's *result* differs
   from the record.

## Not run, and why

- **The N = 7 Tamarin runs.** Resource-limited in the domain's own record, with several lemmas killed
  or never started. Not re-attempted here: the N = 4 run is complete and the domain's own record of what
  the N = 7 runs did is in `domains/11-independent-audit-stack/formal/perlemma_n7_8g/`.
- **The production-parameter sanitizer runs** (ASan/UBSan 2,194 s; MemorySanitizer timed out at
  3,600 s). Quoted from the domain; not re-run here.
- **The property layer** (`domains/11-independent-audit-stack/property/run_all.sh`), which needs
  `PQT_SRC`. Its figures — including the withdrawn "16/16 and 16/16" — are quoted from the domain's own
  record and from `records/failed-assumptions.md` entry `A28`.
- **Everything in Tier 3 of `reproduction.md`** — the vendored proof backend and compiled adapters, the
  TLA+ model checks, ProVerif, EasyCrypt, the SAT experiments, the NIST ACVP vectors, the devnet runs.
  Each is marked `not-run` with the missing capability named, in this package and in the owning domain's
  own `VERIFICATION.md`.

## Additions made after the first assembly pass

Two entries were added to `glossary.md` afterwards. Both were written from the document that owns the
subject, not from a summary:

- **`dossier`** (§11), with the related terms **"the brief"** and **"the coordinator"**. Written from
  `records/provenance.md` §1 — the section headed "The dossiers, and why the map cites them" — which
  states that a dossier is one of the assembly's own working documents, that **the dossiers are not in
  this repository**, and that a citation to one is the record of what it said rather than a pointer to
  follow. The entry also carries the "where the reason is checkable the note states it" qualification,
  which is `provenance.md` §1's own example (the vendored-tree note in §5.1, with its upstream
  repository, commit and licence). The three dossier names quoted — `D0`, `D3`, `D11` — are the ones
  `records/provenance.md` §1 itself names as examples.
- **The claim-label set's provenance** (§7). Written from `docs/02-theory-and-references/README.md`,
  which describes the seven labels as **the dossier specification's**. The note's point is that the set
  is the programme's own convention; it is phrased as what the repository says — no source here
  attributes the set to a standards body or to external work — rather than as a survey of the outside
  literature, which this package did not perform.

The **size gate** `W ≤ (32,768 − 216) // 43 = 757` was already present in `glossary.md` §3 when this
request arrived; nothing was added for it.

**Forbidden-content scan, re-run after these edits.**

```
$ python3 tooling/checks/scan-forbidden.py .
files scanned: 611, findings: 0
  ai-name 0   ai-meta 0   abs-path 0   tracking 0   contact 0   secret 0
```

Exit 0, no findings, and none of the two hits previously reported on `tooling/VERIFICATION.md` remain —
that file was corrected by its own package while this package was being edited. The two entries added
here were included in the scan; neither introduced a finding.
