# Reproduction

The single entry point for running things. **A reader must be able to tell before starting whether
what they want to run will work**, so this page gives three tiers — cheap, minutes-long, and not
reproducible — and states the two environment facts that decide the answer before any command is
typed.

The runtimes below were **observed while this package was assembled**, on the host named at the end of
this page, and are recorded against the repository's own baseline figures in
[`VERIFICATION.md`](VERIFICATION.md). Where the two differ, both are given.

---

## Before you run anything: two facts that decide the answer

**1. The environment.** Nothing here runs without the pinned environment: a Python 3.12.3 virtual
environment, a locally built `liboqs` 0.16.0 shared library, and the formal tools. Build it from
`tooling/environment.md`, then:

```
source tooling/activate.sh
```

`tooling/activate.sh` derives the environment root from its own location, so the tree can be cloned anywhere.
Without the `liboqs` build the B0 real-signature demo reports the library as unavailable rather than
failing — that behaviour is itself recorded in `domains/07-compact-certificate-b0/results/`.

**2. `PQT_SRC`.** Some harnesses read their input files from a local copy of the read-only research
tree. That tree is **not shipped with this repository**. `tooling/activate.sh` warns if `PQT_SRC` is unset and
continues.

- **The scripts under `domains/01`–`domains/10` do not read it.** They run from the repository alone.
- **Several layers under `domains/11-independent-audit-stack` do**, and exit with a message naming
  `PQT_SRC` if it is unset. Affected: `math/math_layer.py`, `fault/fault_injection.py`, everything
  under `property/`, `fixes/make_fixes.py`, and `independent-b0/gen_b0_vectors.py`.
- **Not affected, and therefore runnable from the repository alone:** `formal/bounded_checker.py`,
  `formal/qpt128_quorum.spthy` (Tamarin), `independent-b0/b0_indep.py` and
  `independent-b0/check_vectors.py`.

`domains/11-independent-audit-stack/docs/inputs-and-provenance.md` maps every input file that a
`PQT_SRC`-dependent layer reads.

---

## Tier 1 — cheap (seconds to about a minute)

Every domain's checker is self-contained. Run them from the repository root with the environment
active.

| Command | What it gives you | Observed |
|---|---|---|
| `python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --self-test` | the B0 reference module's 39 tests | **39 tests, OK**, 0.39 s (0.83 s wall) |
| `python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --self-test` | the security target's 19 tests: definitions D1/D2/D3, lemmas L1–L5 | **19 tests, OK**, 0.095 s (0.27 s wall) |
| `python3 domains/01-accountable-quorum-foundations/src/pqaqc_finite_state_check.py` | bounded state exploration of the quorum model | exit 0, 0.78 s |
| `python3 domains/04-operator-ledger/src/operator_ledger_checks.py` | the operator ledger's 23 finite checker groups | exit 0, 0.07 s |
| `python3 domains/11-independent-audit-stack/formal/bounded_checker.py` | the exhaustive third protocol model | `RESULT: all rows ok; boundary C = 2q−N confirmed`, 0.9 s |
| `python3 domains/11-independent-audit-stack/independent-b0/b0_indep.py` | the spec-only B0 implementation's self-test | `self-test ok`, 0.1 s |
| `python3 domains/11-independent-audit-stack/independent-b0/check_vectors.py` | the independent implementation against 900 generated vectors | **6,701 agree, 0 disagree**, 11.5 s |
| the nine scripts under `domains/05-extraction-and-signature-reductions/src/` with `--self-test` | 167 tests across the extraction and reduction band | 7 of the 9 accept `--self-test` and returned OK in 0.09–1.77 s; the two that do not (`hybrid_sampling_bound_audit.py`, `slh_tree_conditioning_audit.py`) run their unittest suite on bare invocation instead |

Two notes on running these, learned by running them:

- **Some scripts exit 2 on a bare invocation by design** and print a usage message. That is not a
  failure. `domains/06-qpt128-security-target/src/qpt128_finalization.py` behaves this way; use `--self-test`.
- **`--self-test` is not universal.** Where a script does not accept it, its recorded output file in
  that domain's `results/` shows the invocation that produced it.

The B0 real-signature demo sits at the long end of this tier:

```
python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --real-demo
```

It signs a real 64-seat registry, encodes two conflicting frames, verifies, extracts 22 seats, assigns
blame and rejects tampered variants, for every scheme the pinned libraries provide. Observed: exit 0,
**43.4 s** on a loaded host and 25.8 s on the same host earlier; the repository's baseline is 13.7 s.

---

## Tier 2 — minutes-long

| Command | What it gives you | Observed | Repository baseline |
|---|---|---|---|
| `python3 domains/09-security-games-and-attack-lab/src/ceqs_attack_lab.py --all` | 24 violation attempts against the real Mode B implementation, plus the framing, Grover, binding and extraction experiments | exit 0, **177.1 s**, "Successful violations: 0 of 24 attempts" | ≈55 s |
| `python3 domains/09-security-games-and-attack-lab/src/ceqs_games.py --all` | the four games (FRAME, SUPPRESS, EVADE, SAFETY) with measured query complexity fitted against theory | exit 0, **161.6 s**; SAFETY threshold 22 confirmed for every corruption level 0–23 | ≈126 s |
| `tamarin-prover --prove domains/11-independent-audit-stack/formal/qpt128_quorum.spthy` | the symbolic protocol model at N = 4 | exit 0, **161.05 s**, **all 12 lemmas verified** | ≈111 s |
| `python3 domains/11-independent-audit-stack/math/math_layer.py` | exact recomputation of M1–M8 | exit 0, **154.5 s**, M8_evade `REPRODUCED`; **requires `PQT_SRC`** | 217 s |
| `bash domains/11-independent-audit-stack/property/run_all.sh` | the Hypothesis property layer | recorded 3.6 min, re-run 2.5 min; **requires `PQT_SRC`** | 2.5–3.6 min |

**Run them one at a time.** The figures above were taken while the host was carrying a load average
near 19 from other work, which is why the attack lab and the games are three times their baseline. A
reader on an idle host should expect times closer to the baseline column; a reader running several of
these at once should expect the observed column or worse. The two Tamarin rows are the exception: the
symbolic model is genuinely minutes per run and is the slowest thing in the tree.

**What the Tamarin run means, exactly.** The proof was run in full at N = 4 and every lemma —
`sanity_honest_certificate`, `A1_three_distinct_signers`, `A2_signer_authorized`,
`A_acceptance_authorized`, `D2_intersection_seats_corrupt`, `D1_non_frameability`,
`B_conflict_needs_2qN_corrupt`, `C1_intersection_nonempty`, `C2_intersection_at_least_2qN`,
`C3_evidence_reachable`, `E1_below_threshold_no_conflict`, `E2_at_threshold_conflict_exists` —
verified. It is machine-checked **at N = 4**. The N = 7 runs are resource-limited, and the domain's own
record of which lemmas were killed, which have no exit line and which never started is in
`domains/11-independent-audit-stack/formal/perlemma_n7_8g/` and
`domains/11-independent-audit-stack/docs/formal-models.md`. Two further layers of the same domain —
one production-parameter sanitizer run under ASan and UBSan (2,194 s) and one MemorySanitizer run that
timed out at 3,600 s — are minutes-to-an-hour items; the first reproduced, the second is recorded as
inconclusive.

---

## Tier 3 — what cannot be reproduced here, and why

Stated so a reader does not spend an afternoon discovering it. The full account, with what each item
would need, is `tooling/environment.md` §8.

**Excluded from the repository, so the runnable thing is absent.**

- **The vendored proof backend.** The proof-carrier experiments ran against a vendored copy of an
  upstream succinct-proof backend — **767 files, 6,524,451 bytes**, at a pinned commit. It is not here.
  The Rust toolchain is not installed in the environment this repository was assembled in.
  `domains/03-zk-carrier-experiments/docs/provenance.md` names the upstream repository and commit, and
  the six local modifications ship as a patch.
- **The four compiled adapter binaries**, 5,531,152 / 5,533,208 / 5,699,400 and 5,721,256 bytes. They
  contain AVX-512 instructions and were never executed on a host without them. They can be rebuilt
  from the adapter sources in this repository with the recorded Rust version and
  `cargo build --locked --release`, **but rebuilding changes their digests**, so the recorded proof
  sizes cannot be re-derived byte for byte. The rebuild command and the digests are recorded.
- **The `pqcrypto` 0.3.4 wheel**, 27,036,304 bytes, used by one experiment: install from PyPI. Its
  SHA-256 and its verification against the publisher's release metadata are in
  `domains/03-zk-carrier-experiments/results/dependency-provenance.json`.

**Present as a model or a script, but never executed.**

- **The TLA+ model checks.** `domains/01-accountable-quorum-foundations/formal/epoch-barrier.tla` has
  **never been executed** by TLC or TLAPS: the TLA+ distribution and a Java runtime were never pinned.
  The recorded model-check outputs ship as text files and are quoted as recorded. The file is the
  mechanism's *specification* — and note that it was renamed internally to `MODULE epoch_barrier`,
  because a TLA+ identifier cannot contain a hyphen, so any TLC run must account for the mismatch.
- **ProVerif.** Models are written (`domains/11-independent-audit-stack/formal/qpt128_quorum.pv`,
  `qpt128_quorum_C1.pv`) and **unexecuted**. The D11 record lists ProVerif as expectation only.
- **EasyCrypt.** `domains/11-independent-audit-stack/formal/frame_b0.ec` is a skeleton with the proof
  **admitted** and never executed.
- **The SAT experiments.** Three solver scripts stand behind the SAT-slope figures. They are analysis
  scripts and are **not shipped**, and no solver run finished inside its time cap — so the figures are
  reported as summaries rather than reproducible runs. The record also withdraws the ranking they were
  once used to support: a later independent analysis found the SAT behaviour does not distinguish the
  handle designs, and the ranking now rests on the algebraic model alone.

**Absent for reasons outside the file map.**

- **Third-party conformance vectors.** The primitives cross-check needs five NIST ACVP vector files
  that are not redistributed here. `domains/11-independent-audit-stack/primitives/vectors/SOURCE.txt`
  records the upstream commit and the SHA-256 of each file so they can be fetched and checked.
  **Without them the cross-check reports not run rather than passing** — which is the repository's
  standing convention: an absent tool reports NOT RUN, never a pass.
- **The devnet runs.** They were made on a separate ledger implementation in another repository, on
  its own harness. Nothing from it is copied here; `docs/05-devnet-evidence` records what it measured
  and nothing else.
- **The Docker path, and the tools that path would have provided.** The container mathematics profile,
  SageMath, KLEE, AFL++ and valgrind were not available on the authoring host and their Docker paths
  are recorded as not run. The MemorySanitizer production run timed out; it is inconclusive, not
  passed.

---

## After you run something

Record what you saw. That is the repository's own convention, and it is what makes the next reader's
answer different from yours: every domain carries a `VERIFICATION.md` with one row per item in the form

```
item | command | environment | expected (recorded) | observed | verdict | notes
```

with `verdict` taking one of **`reproduced`**, **`reproduced-with-difference`**, **`not-reproducible`**
or **`not-run`** — and where a re-run disagreed with the record, **both results are kept and the
disagreement is marked**. If your re-run disagrees with the record, that is a result; the repository's
rule for what happens next is in [`claim-labels.md`](claim-labels.md).

---

## The host these figures came from

Ubuntu 24.04.4 x86-64, Python 3.12.3 in the pinned virtual environment, `liboqs` 0.16.0
(commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`) and `liboqs-python` 0.16.0, `pqcrypto` 0.3.4,
Tamarin 1.12.0 with Maude 3.5.1, `gcc` 14.2.0. Timings were taken with the host under a load average
near 19 from concurrent work, so they are upper bounds rather than a benchmark.
