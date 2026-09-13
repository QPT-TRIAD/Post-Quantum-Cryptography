# VERIFICATION — D2, ceqs-construction-evolution

What was re-run in this domain, with the exact commands, the recorded output it was compared
against, and the observed result. The standing rule of this project is that a number a re-run does
not reproduce is withdrawn in public with the reason; this file therefore contains one
non-reproduced line and a list of items that could not be run at all, each with its reason.

**Verdict values:** `reproduced`, `reproduced-with-difference`, `not-reproducible`, `not-run`.

## Environment

| Item | Value |
|---|---|
| Host | Linux, x86-64 |
| Shell setup | `. tooling/activate.sh` |
| Python | CPython 3.12.3 (the pinned interpreter the environment provides) |
| Third-party packages used by the checkers | none — every script under `src/` and `history/` imports only the standard library |
| Working directory for every command below | `domains/02-ceqs-construction-evolution/` (all paths are relative to it) |
| Comparison method | stdout of the script compared byte-for-byte with the matching file in `results/` (`diff`); the script's exit code recorded separately |
| Evidence file for this domain's hashes | `records/file-map.tsv` (row per copied file) and `records/rewrites.tsv` (row per mandated rewrite) |

Entry point for the whole set:

```sh
. tooling/activate.sh
cd domains/02-ceqs-construction-evolution
for f in src/*.py; do python3 "$f" > /tmp/$(basename "$f" .py).out; \
  diff -q /tmp/$(basename "$f" .py).out results/$(basename "$f" .py).txt; done
```

## 1. Runnable items

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| quorum-family checker (v0.7) | `python3 src/ce_qs_quorum_family_checker.py` | CPython 3.12.3, stdlib only | 5 `PASS` + 3 `EXPECTED-FAIL`; last lines `PASS n=64 f=21 q=43 combinatorial_required_columns=41107996877935680 log2=55.190269`, `PASS public_bitmap_bytes=8` | identical, byte-for-byte | reproduced | exit 0; 0.02 s; exhaustive signer-family check and omission mutant for n = 4, 7, 10 |
| bitmap-policy checker (v0.8) | `python3 src/ce_qs_bitmap_policy_checker.py` | CPython 3.12.3, stdlib only | 5 `PASS` + `EXPECTED-FAIL unbound_bitmap_attack blocked_by=f_B` + `PASS n=64 bitmap_size_bytes=8` | identical | reproduced | exit 0; 0.02 s; `f_B` equivalence exhaustive over all bitmaps for n = 3, 4, 5 |
| private-wrapper relation checker (v0.9) | `python3 src/ce_qs_private_wrapper_relation_checker.py` | CPython 3.12.3, stdlib only | 2 `PASS` + 3 `EXPECTED-FAIL`, incl. `conflict_extracts_exact_intersection intersection=[0, 1, 2]`; trailing `NOTE` line | identical | reproduced | exit 0; 0.02 s; relation mock, no MPA/NIZK implemented (stated in the recorded note) |
| distributed certified-tag checker (v1.0) | `python3 src/ce_qs_distributed_certified_tag_checker.py` | CPython 3.12.3, stdlib only | 3 `PASS` + 5 `EXPECTED-FAIL`, incl. `PASS collector_witness_contains_no_signer_secrets` | identical | reproduced | exit 0; 0.05 s; ideal proof/signature interfaces only |
| strong conflict-handle checker (v1.1) | `python3 src/ce_qs_strong_conflict_handle_checker.py` | CPython 3.12.3, stdlib only | 4 `PASS` + 4 `EXPECTED-FAIL`, incl. `PASS exact_conflict_trace identities=[0, 1, 2]`, `PASS public_verify_blame` | identical | reproduced | exit 0; 0.05 s; ideal SCCH only |
| QPT/CRS structural checker (v1.3) | `python3 src/ce_qs_qpt_crs_structural_checker.py` | CPython 3.12.3, stdlib only | 4 `PASS` + 2 `EXPECTED-FAIL`, incl. `PASS challenge_encoding_injective toy_bits=16`, `EXPECTED-FAIL cross_key_false_trace blocked_by=unique_link_base` | identical | reproduced | exit 0; 0.09 s; structural toy model; QLWR/LWE/NIZK/QCR security not executed (stated in the recorded note) |
| collaborative-quorum checker (v1.4) | `python3 src/ce_qs_collaborative_quorum_checker.py` | CPython 3.12.3, stdlib only | 8 `PASS` + 1 `EXPECTED-FAIL`, incl. `PASS reference_64_21_43 honest_in_any_quorum>=22` | identical | reproduced | exit 0; 0.05 s; exhaustive honest-majority enumeration for n = 4, 7, 10 |
| backend-eligibility checker (v1.6) | `python3 src/ce_qs_backend_eligibility_checker.py` | CPython 3.12.3, stdlib only | 6 backend rows, all `eligible=False`; `PASS score_28KiB_48B=2032`; `EXPECTED-FAIL score_28KiB_96B=-32`; `PASS eligibility_requires_all_properties toy_total=28704` | identical | reproduced | exit 0; 0.05 s; eligibility logic only, no backend benchmark executed |
| relation mock (v0.3) | `python3 src/ce_qs_relation_mock.py` | CPython 3.12.3, stdlib only | 3 `PASS` + 3 `EXPECTED-FAIL`, incl. `EXPECTED-FAIL duplicate_signer_public_rejection reason=duplicate-tag` | identical | reproduced | exit 0; 0.03 s; relation mock only, no VOLEitH ZK |
| relation mock, extended (v0.3, extension) | `python3 src/ce_qs_relation_mock_ext.py` | CPython 3.12.3, stdlib only | 1 regression line + 5 `EXPECTED-FAIL` lines; final line `ALL EXTENSION-PASS CHECKS PASSED (5 new + 1 regression gate)` | identical | reproduced | exit 0; **2.57 s** (the empirical post-exposure probe dominates); the recorded note names three games that this file does not exercise |
| trace-tag simulator (v0.2) | `python3 src/ce_qs_trace_tag_simulator.py` | CPython 3.12.3, stdlib only | 2 `PASS` + 5 `EXPECTED-FAIL`; `PASS baseline_P1_intersection trials=50 min_\|S0∩S1\|=25 (bound f+1=22)`; final line `ALL CE-QS v0.2 MUTATION CONTROLS PASSED (5/5 from Section 19 step 5)` | identical | reproduced | exit 0; 0.73 s; deterministic because the script seeds its generator (`run(seed=1234, …)`); see §2 for the superseded v0.1 script, which does not |
| integration gate (repository level) | `python3 tooling/checks/verify-repository.py` | CPython 3.12.3 | every `copy`/`copy-history` row present at its destination path; sha256 equal to the map unless the row is recorded in `records/rewrites.tsv`; no unexplained file; no empty file | for this domain: 62/62 rows present, 0 missing, **0 unexplained hash differences**, no unexplained file; the gate lists this domain's 9 authored documents under `docs/` (the two authored files at the domain root are in the gate's recognised set) | reproduced | at the time of this run the gate's overall `RESULT: FAIL` came from other domains (4 files still missing under `docs/01-research-journey` and `domains/09-…`, then being built) and no line of it concerned D2; re-run over the completed tree the gate reports `RESULT: PASS` with 0 missing and 0 unexplained |
| forbidden-content scan | `python3 tooling/checks/scan-forbidden.py domains/02-ceqs-construction-evolution --quiet` | CPython 3.12.3 | 0 hits in all six categories (`ai-name`, `ai-meta`, `abs-path`, `tracking`, `contact`, `secret`) | `ai-name 0, ai-meta 0, abs-path 0, tracking 0, contact 0, secret 0` over all 73 files of this domain, the authored documents included | reproduced | run again after the rewrites of §3 and after the authored documents were written; the categories are the tool's own |
| checksum manifest, v0.8 | compare each line of `results/sha256sums-v0.8.txt` with the repository file it names | sha256sum | 3 hashes | 3/3 `MATCH` | reproduced | manifest names the research-tree filenames; see the mapping in `README.md` §5.1 |
| checksum manifest, v1.0 | same, `results/sha256sums-v1.0.txt` | sha256sum | 4 hashes | 4/4 `MATCH` | reproduced | idem |
| checksum manifest, v1.1 | same, `results/sha256sums-v1.1.txt` | sha256sum | 4 hashes | 4/4 `MATCH` | reproduced | idem |
| superseded v0.1 trace-tag simulator | `python3 history/ce_qs_trace_tag_simulator-v0.1.py` | CPython 3.12.3, stdlib only | `results`-style file `history/ce_qs_trace_tag_simulator-v0.1.txt`, 8 lines, line 3 `minimum observed quorum intersection=26` | all lines identical **except line 3**, which read 25, 26, 25, 26, 25 over five runs | **reproduced-with-difference** | exit 0; 0.38–0.40 s; the script is not deterministic — see §2. All other lines (tag payload 1376 B, pair checks 1849, the same-topic and different-topic recovery lines, and the closing note) matched exactly. |

Discrepancy count: **1** (`reproduced-with-difference`). Every other runnable item reproduced
byte-for-byte.

## 2. The discrepancy: the superseded v0.1 simulator is not deterministic

**Item:** `history/ce_qs_trace_tag_simulator-v0.1.py` (superseded; kept in `history/` with its
version in the filename, per the domain shape rule).

**Recorded line:** `minimum observed quorum intersection=26`
(`history/ce_qs_trace_tag_simulator-v0.1.txt`, line 3).

**Observed:** `25`, `26`, `25`, `26`, `25` over five consecutive runs of the same command in the same
environment. Line 3 of the recorded file was the only difference; `diff` reported exactly that one
line.

**Cause, from the source itself:** the v0.1 script draws its quorums from the module-level `random`
generator (`random.sample(range(n), q)`) and its key material from `secrets`, and never seeds either
— unlike the v0.2 revision, which is explicit about the change
(`src/ce_qs_trace_tag_simulator.py:34–78` routes key material through a seeded generator and
`run(seed=1234, …)` at `:119–120`). The quantity reported on line 3 is therefore a **sample minimum
over 50 random trials**, not a computed bound; its true value under repeated sampling is at most the
recorded 26 and in the observed runs 25 or 26.

**What this does and does not affect.** The *bound* the same line quotes — `f + 1 = 22` for
`n = 64, q = 43` — is arithmetic and is unaffected: every observed minimum (24, 25 or 26) is above
22. The line is a simulation observation at v0.1 and must not be read as a property any later version
relies on. The exact worst-case statement is made by the v0.9 checker instead
(`conflict_extracts_exact_intersection intersection=[0, 1, 2]`, the `2q − n = f + 1 = 3` worst case
at `n = 7`), and the exact arithmetic by the v0.7 checker (`combinatorial_required_columns`), which
reproduce exactly.

**Consequence recorded:** the v0.1 line is not withdrawn as false — it is a random variable reported
without its distribution — but no claim in this domain cites it. `README.md` §3.1 and §6 carry the
same statement, and the v0.1 row of the version ladder marks the line as nondeterministic.

## 3. Rewrites applied to the copied files

Files reach this repository byte-identical to their source **except** where a rewrite is mandated and
recorded. Fourteen single-line rewrites were applied, in six files, each replacing a two-word phrase that named
the working occasion as a session (the word *session* preceded by *this*) with the phrase
*this pass* — the term the same corpus already uses for the same idea. One phrase per line, meaning
preserved, nothing else on those lines changed:

| File (repository path) | lines rewritten |
|---|---:|
| `docs/exact-aggregator-lifting-proof.md` | 1 |
| `docs/validation-and-continuation.md` | 1 |
| `history/validation-and-continuation-v0.2.md` | 2 |
| `history/validation-and-continuation-v0.3.md` | 2 |
| `history/validation-and-continuation-v0.5.md` | 3 |
| `history/validation-and-continuation-v0.6.md` | 5 |
| **total** | **14** |

One of those pairs is a quotation: `history/validation-and-continuation-v0.6.md:61` quotes
`docs/exact-aggregator-lifting-proof.md:1092` verbatim, so both the quotation and the quoted line
were rewritten together and the quotation remains true.

**Record:** these six files are listed in `records/rewrites.tsv` with their map hash, their
repository hash and the class `scrub-ai` (count per file 1, 1, 2, 2, 3, 5 — fourteen in total). The
integration gate therefore reports 0 unexplained hash differences for this domain. **56 of the 62
copied files are byte-identical to the source; the 6 above differ only on the lines named.**

Verification after the rewrites:

```sh
python3 tooling/checks/verify-repository.py | grep 02-ceqs      # no HASH, MISSING or UNEXPLAINED line
python3 tooling/checks/scan-forbidden.py domains/02-ceqs-construction-evolution --quiet   # 0 in all categories
python3 -c "import pathlib,hashlib; ..."   # per-file sha256 against records/file-map.tsv: 56 identical, 6 as recorded in records/rewrites.tsv
```

## 4. Items not run

Every line below is a number or a result asserted by a source document in this domain that **cannot
be re-run here**, because the artifact that produced it is not in the repository. Naming the absent
artifact is the reason; nothing is inferred about the result's truth.

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| v1.24 certificate-contents reference test | `python3 continuation_v1.24/contents_contract.py` (as named in `docs/32kib-contents-contract.md:139`) | — | 44 reference and contract checks passed; recovery of indices 0–21 from two 43-seat statements with 22 common seats; 64 rotating quorums; selector and MPC-threshold checks | not run | not-run | the package `continuation_v1.24/` is not part of this domain and is not in the repository (not a `copy` row in the file map) |
| v1.24 support data | `contents_contract.json`, `public_statement_examples.json`, `contents_check_results.json` (named at `:143`) | — | public/private/fixed-setup/generation-only object inventory; unproved public examples; recorded check results | not run | not-run | absent, same reason |
| v1.23 native proofs | the seven native proofs of the earlier hashed-challenge relation (named at `:143`) | — | seven proofs of the *v1.23* relation, explicitly not proofs of the v1.24 relation | not run | not-run | absent; the source states the limitation itself |
| v1.20 bound audit | `bound_audit.py` (named at `docs/blocker-resolution.md:131`) | — | 154 named checks pass, including one summarizing 992 distinct secret-pair cases; exact fractions compared; all 16 order cases; rounding argument on an exhaustively enumerated small modulus | not run | not-run | absent. The source states these are arithmetic checks, not 154 cryptographic proofs |
| v1.20 exact bounds data | `PQ_CE_QS_exact_bounds_v1_20.json` (named at `:131`) | — | complete integer numerator and denominator of each ε term and the total | not run | not-run | absent; the arithmetic is independently recomputable — see §5 |
| v1.20 trace-evidence checker | the evidence checker named at `:164` | — | 27 consistency checks pass; the 22 expected synthetic trace indices recovered from two public handle lists; 86 real ML-DSA signatures verified; 86 wrong-seat public-key substitutions rejected | not run | not-run | absent. The source states these private checks do not put authorization inside either public proof |
| v1.20 executed trace circuit | the two producer runs named at `:7,159–166` | — | 9,800,861 native gates (from 14,988,983); 4,579,328 packed multiplications (from 6,957,056); first verified encoded diagnostic frame 722,528 bytes; ≈13.0 GiB peak RSS under a 20 GiB limit | not run | not-run | the circuit and its encoded frames are not in the repository. This is a **measurement** and is labelled as one; it is not repeated as a theorem anywhere in this domain |
| v1.19 blocker model | `ce_qs_blocker_model_v1_19.py` (named in `history/blocker-resolution-v1.19.md:259`) | — | 116 passing checks: all 22 pool sizes 43–64; small-population enumeration of the sampling formula; ideal retry paths for fault counts 0–21; size-evidence classification; relation-count agreement; statistical arithmetic; rejection of the incomplete security ledger | not run | not-run | absent. The source states these are arithmetic and ideal-model checks |
| v1.19 relation inventory | the inventory named at `:68–84` | — | 13,914,112 scalar products; 6,957,056 packed multiplications; 215 Keccak permutations; 22,176,863 wires; 142,287 B ML-DSA witness | not run | not-run | absent. The counts are recomputable from their own printed expression — see §5 |
| v1.18 research screen | the 34-check audited artifact named in `docs/research-qualification.md` | — | 32 papers and one repository screened; no examined construction qualifies; the 50,496-byte floor derived | not run | not-run | absent; the document's negative verdict is quoted, not re-derived here |
| v1.2 | any file | — | — | not run | not-run | **no document, ledger, checker or recorded result exists** for v1.2 in the source tree or the map. Its content is known only from v1.3's description of what it left open (`docs/qpt-crs-security-proof.md:14–19`) |
| v1.5 main proof document | any file | — | — | not run | not-run | only the compactness ledger (`docs/compactness-source-ledger-v1.5.md`) exists |
| v1.7–v1.17, v1.22, v1.23 | any file | — | — | not run | not-run | eleven version numbers with no document in this repository. The ladder records them as **reported** material only; no claim in this domain rests on them |
| ELBA equation (13) arithmetic | reproduced by hand and by a calculator, not by a shipped program | CPython 3.12.3 | `u ≥ 3991`; ≈38.6 MiB at 43/42; `u ≥ 223` and ≈2.2 MiB at 64/42; `43 × 9.91 KB = 426.13 KB` | recomputed: 3990.63 → ceil 3991; 38.62 MiB; 222.93 → ceil 223; 2.16 MiB; 426.13 KB | reproduced | see §5. No checker exists for this in any version; the source says so by shipping none |

## 5. Arithmetic recomputed here

Where a source states a number as arithmetic rather than as a measurement, it was recomputed
independently. All of the following agree with the cited source.

| Quantity | Source | Recomputed |
|---|---|---|
| `2q − n` at `n = 64, q = 43` | `docs/formal-proof-stack.md` §15 | `22 = f + 1` |
| `C(64,43)` and its bit length | `docs/research-qualification.md:179`; `results/ce_qs_quorum_family_checker.txt` | `41,107,996,877,935,680`, `log2 = 55.190269` |
| retained-format floor | `docs/research-qualification.md:167` | `4,288 + 16 + 46,192 = 50,496 > 32,768` |
| v1.18/v1.21 prefix obstruction | `docs/size-path-resolution.md:17` | `46,080 + 16 + 4,128 + 160 = 50,384 > 32,768` |
| v1.24 allocation | `docs/32kib-contents-contract.md:15–19` | `208 + 5,504 + 27,056 = 32,768`; `43 × (64 + 64) = 5,504` |
| per-seat proof budget | `docs/size-path-resolution.md:21` | `28,480 / 43 = 662.33 → 662` |
| encoded bytes per native gate | `docs/size-path-resolution.md:12` | `722,528 / 9,800,861 = 0.073721`; native `863,744 / 9,800,861 = 0.088129` |
| circuit reduction, v1.19 → v1.20 | `docs/blocker-resolution.md:141–146` | `14,988,983 − 9,800,861 = 5,188,122` gates; `6,957,056 − 4,579,328 = 2,377,728` products |
| frozen-registry pair bound | `docs/blocker-resolution.md:104–105` | `1024 · C(64,2) · 2⁻¹⁷⁶ = 2,064,384 · 2⁻¹⁷⁶ = 63 · 2⁻¹⁶¹` exactly, since `63 · 2¹⁵ = 2,064,384`; `log₂(63) = 5.97728` → `2^−155.02272`, against the source's `2^−155.0227200765` |
| relation inventory | `history/blocker-resolution-v1.19.md:84` | `43 × (608 + 608 + 48) × 256 = 13,914,112` |
| ELBA repetition bound | `docs/formal-proof-stack.md:55–85` | `(128 + 7 + 1 − log₂ log₂ e) / log₂(43/42) = 3990.63` → `ceil = 3991`; `× 9.91 KB = 38.62 MiB`. At `n_p = 64`: `222.93` → `ceil = 223`, `2.16 MiB`. Plain concatenation `43 × 9.91 KB = 426.13 KB` |

## 6. Known deviations and cross-reference notes

1. **Stale internal references were not repointed in this domain.** Six of the copied files still
   name research-tree filenames inside their text (for example `PQ_CE_QS_frontier_v0_1.md` in
   `src/ce_qs_trace_tag_simulator.py:8,242` and in the trailing note of
   `results/ce_qs_trace_tag_simulator.txt`; `PQ_CE_QS_finalized_construction_v0_3.md` in
   `src/ce_qs_relation_mock_ext.py:6`). The file map records these rows as byte-identical copies and
   `records/rewrites.tsv` lists them only under `scrub-ai`, not under a path-repointing class, so
   the references were **left as the sources wrote them**. The `README.md` §5.1 table maps every
   original filename to its path in this repository, so nothing is unreachable. Two history
   documents additionally name artifacts that are absent everywhere (`ce_qs_blocker_model_v1_19.py`,
   `ce_qs_relation_v1_10.py`, `PQ_CE_QS_security_loss_ledger_v1_19.json`) — those are listed as
   `not-run` above.
2. **One duplicate was not copied by design.** `PQ_CE_QS_blocker_resolution_v1.19.txt` is marked
   `exclude-duplicate` in the file map because it is byte-identical to the `.md` at
   `history/blocker-resolution-v1.19.md`. The `.md` is the copy; the `.txt` is not in the repository.
3. **No TRIAD blockchain material** was copied into this domain; the domain contains construction
   documents, checkers and their results only.
4. **Nothing was written under the read-only source tree.** All authored files are in
   `domains/02-ceqs-construction-evolution/`.
5. **Authored documents** (`README.md`, this file, `docs/construction-end-to-end.md`,
   `docs/inflections/01…08`) are new writing for this repository. They contain no new result: every
   number in them is traceable to a source file and line, to a recorded result in `results/`, or to
   the recomputations in §5, and each is labelled with the source's own status word (proved,
   conditional, measured, design allocation, reported, open). The integration gate classifies them
   as authored documents, which is correct.

## 7. Summary

| Verdict | Count |
|---|---:|
| reproduced | 11 current checkers + 3 checksum manifests + integration gate + forbidden-content scan + ELBA arithmetic = **17** |
| reproduced-with-difference | **1** — the superseded v0.1 simulator (§2) |
| not-reproducible | **0** |
| not-run | **13** items, each with the absent artifact named (§4) |

The single discrepancy is in a superseded script that no later version depends on, its cause is
identified in the script's own source, and the bound the line quotes (`f + 1 = 22`) is unaffected.
