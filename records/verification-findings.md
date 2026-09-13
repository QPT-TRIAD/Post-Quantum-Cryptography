# Verification findings

These are the findings of the verification pass that ran on 2026-09-13 while this repository was
assembled. Each finding states what had been recorded, the command that was run, the environment, the
numbers that were observed, and the disposition. Findings are marked **verified here** when the
command was re-run during this pass, and **attributed** when the number comes from the package that
owns the code and holds the working.

Nothing here upgrades a claim. Where a recorded result failed to reproduce, both the recorded value
and the observed value are kept, and the reason is given.

## How these findings are grouped

Three kinds of entry, kept apart on purpose:

- **A re-run contradicted the record** — findings 1, 2, 5 and 7. The recorded result was reproduced
  as a command, and the command returned something else, or returned nothing at all.
- **Reading the record against its own output showed it counted something that did not happen** —
  findings 3 and 6. No re-run is needed for these: the record's own numbers do not add up, or count
  an event that the same output says was skipped.
- **What the assembly changed, and a hazard found while checking** — finding 4 (wordings and
  machine-specific paths removed during assembly) and finding 8 (a checker whose entire pass
  criterion vanishes under interpreter optimisation).

## Environment for every command in this document

The pinned reproduction environment described under `tooling/`: a Python interpreter with the pinned
package set (the state-vector Grover simulation needs `numpy`; the LMS interop tests need
`hsslms` 0.1.3), activated before each command. The commands below were run on one x86-64 host, on
2026-09-13. Runtimes are given where they matter.

---

## 1. A recorded PASS that does not reproduce — S1-011 `grover_simulation_matches_law`

**Verified here.** Cause identified; disposition recorded.

**Recorded.** `records/audit-checklist.md` lists test `S1-011`,
`test_S1_011_grover_simulation_matches_law`, column `bound`, status **PASS**, and states the suite
total as **70/70 tests pass**. Suite S1 runs in the audit ledger; the test asserts three things over
`n ∈ {8, 10, 12, 14}`:

1. `|k_measured − k_predicted| ≤ 1`, the measured first peak against the closed-form iteration count;
2. the success probability at the closed-form iteration count, equal to the closed form to 1e-9;
3. the four-point least-squares slope of `log2(k_measured)` against `n`, within `0.06` of `0.5`.

**Re-run.** The slope assertion failed. Observed value on the re-run:
`0.6415715949019362` against an expected `0.5 ± 0.06` (attributed to
`domains/10-digital-infrastructure/`, which owns the suite and holds the full run). This pass
observed the same assertion fail live in a controlled run of the suite: `AssertionError:
0.579178497043281 != 0.5 within 0.06 delta (0.07917849704328095 difference)`.

**Cause, measured over 200 independent runs** (`grover_chain_inversion` draws its secret with
`secrets.randbelow(N)`):

- the marked-set size M is therefore random — observed **1 to 4**;
- the four-point slope of `log2(k)` against `n` consequently ranges **0.268 to 0.726**;
- the recorded assertion holds in **98 of 200 runs (49.0 %, median 0.511)**.

The test was a coin flip, and the recorded PASS was a lucky draw.

**Re-measured in this pass, 200 independent runs**, loading the same function from
`domains/10-digital-infrastructure/src/s1_lms.py`:

```
python3 - <<'PY'
import importlib.util, math, statistics
spec = importlib.util.spec_from_file_location("s1_lms", "domains/10-digital-infrastructure/src/s1_lms.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
g = m.grover_chain_inversion
def slope(rows):
    xs = [r['n'] for r in rows]; ys = [math.log2(r['k_measured']) for r in rows]
    mx, my = sum(xs)/4, sum(ys)/4
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)
runs = [slope([g(n) for n in (8,10,12,14)]) for _ in range(200)]
print("median %.6f min %.6f max %.6f" % (statistics.median(runs), min(runs), max(runs)))
print("within 0.06 of 0.5: %d/200" % sum(1 for s in runs if abs(s-0.5) <= 0.06))
PY
```

Observed: median **0.4967**, range **[0.3195, 0.7261]**, within `0.06` of `0.5` in **107 of 200 runs
(53.5 %)**; marked-set sizes observed in `{1, 2, 3, 5}`. Wall time 45 s for the whole measurement.

**The two 200-run passes disagree on the frequency** — 49.0 % in the first, 53.5 % in the second.
Both are sample estimates of a statistic that is close to a coin flip; pooled, 205 of 400 runs
(51.3 %) hold the assertion. This does not weaken the finding, and it is recorded here because the
recorded 49.0 % is itself a sample rather than a constant of the test.

**What does reproduce on every run** (both passes, 200/200 each, over all four sizes): the two exact
per-seed assertions — `|k_measured − k_predicted| ≤ 1` and the success probability equal to the
closed form to 1e-9.

**Disposition.** Both exact per-seed assertions are kept. The single-sample slope assertion is
replaced by the median of the same slope over **41 random secrets**, asserted within `0.06` of `0.5`.

| estimator | trials within 0.06 of 0.5 | range |
|---|---|---|
| median of 41 (recorded) | 20/20 | [0.4819, 0.5316] |
| median of 41 (re-measured here) | 20/20 | [0.4765, 0.5256] |
| median of 5 (recorded) | 17/20 | — |
| median of 5 (re-measured here) | 14/20 | — |

Five is not enough samples for this estimator; forty-one is. The claim label of the Grover-law
statement stays **simulation** — it is a state-vector simulation of a reduced game, not a proof and
not a measurement of a deployed system.

**Affected package:** `domains/10-digital-infrastructure/` (the suite and its `VERIFICATION.md`).

---

## 2. Three suites did not run at all as shipped — a rename broke a loader chain

**Verified here** (the mechanism and the repair, in controlled copies); the ledger's end-to-end
totals are **attributed** to `domains/10-digital-infrastructure/`.

**Recorded.** The audit suites and the checklist the ledger writes, with the suite total
**70/70 tests pass**.

**Cause.** The audit scripts load three versioned cross-check references **by filename from their own
directory** (`importlib.util.spec_from_file_location` with a name built from `_HERE`), and two of
those three references load the third the same way. After the clean rename that this repository
applies, the loader strings named files that no longer existed. In the read-only sources the loader
sites are:

| loader site | loads |
|---|---|
| `s3_tls_pki` (own directory) | the hash-signature reference |
| `embedded_broadcast` (own directory) | the hash-signature reference |
| `s2_dns_worstcase`, `s1_lms`, `s4_tesla_adversarial`, `s3_tls_wire` | the embedded-broadcast reference (the first two), the TLS-PKI reference (the fourth) |

**Reproduction run in this pass.** Four of the suites, plus the two reference files they load, were
copied into a scratch directory under the names this repository gives them, so that the loader
strings named files that no longer exist — the state after the rename:

- `s2_dns_worstcase`, `s3_tls_wire`, `s4_tesla_adversarial`: each dies **at module import** with
  `FileNotFoundError` and executes **0 tests**. The load is at module level in each, so the suite
  never starts. These are the three suites that did not run at all.
- `s1_lms`: its load is inside a test, so the module imports and the suite runs — `Ran 12 tests`,
  one error (`FileNotFoundError` on the embedded-broadcast reference), the rest passing.
- The chain is two links deep: with the first link repointed, `s1_lms` then failed with
  `FileNotFoundError` on the hash-signature reference, raised from inside the embedded-broadcast
  reference's own loader block. The notes' account of the chain is exact.

**Repair, re-run in the same scratch copy.** With both loader strings repointed at the renamed files
and nothing else changed: `Ran 12 tests in 15.229s` — **OK**, exit status 0. The repair is a rewrite
of the loader strings, which is what the domain's notes record.

**Ledger, end-to-end** (attributed to `domains/10-digital-infrastructure/`): the first end-to-end
re-run after the rename produced `0/0 tests pass; suites S1:FAIL … S6:FAIL`; after the repair it
reproduces the recorded total exactly: `70/70 tests pass; suites S1:ALL … S6:ALL`. That total
includes the flaky test of finding 1, which is why finding 1 is recorded alongside it and why the
checklist's own PASS for S1-011 is not by itself evidence that the suite is sound.

**Related defect removed in the same rewrite.** Three audit scripts put a dead scratch directory on
`sys.path` before importing `hsslms` (the directory no longer exists on any host). Removing the
assignment alone is not enough: the guard and the `sys.path.insert` line that follow it raise
`NameError`. All three lines were removed from each script; the `try: import hsslms` guard below them
already handles the package's absence.

---

## 3. A figure in the reading record that the sources do not support

**Verified here** (the count, measured against the document); the strict reading and the working are
**attributed** to `domains/04-operator-ledger/`.

**Recorded.** The reading record states that **113 of the 116** ledger amendments have no executable
witness and no citation.

**Measured directly against the document** (`domains/04-operator-ledger/docs/operator-ledger.md`,
1,000 catalogued operators, 116 `Amendment (LABEL)` paragraphs):

- **15 of 116 amendments are witnessed by a checker group.** They are the entries named by a group in
  the document's own 23-row checker-results table: `L1`, `L9`, `L10`, `L35`, `L47`, `T7`, `T8`,
  `T42`, `Q40`, `D9`, `I21`, `I33`, `H20`, `R36`, `Y1`.
- **10 of 116 on a strict reading** of "witness", in which the assertion must compute the corrected
  value rather than restate it. Five witnesses (`T7`, `T42`, `D9`, `I21`, `I33`) are hard-coded or
  vacuous comparisons and are discounted.
- **0 of 116 carry any literature citation.** No amendment text contains a source tag, a URL, an
  arXiv identifier, a FIPS or RFC number, or any other locator. The document's eight formal sources
  are cited only in the lemma and investigation sections, never in a catalogue amendment.
- **Therefore 101 of 116 amendments have neither an executable witness nor a citation (106 on the
  strict reading).**

The reproduction used in this pass (run from the repository root; it reproduces 116 / 15 / 0 / 101):

```
python3 - <<'PY'
import re
from pathlib import Path
lines = Path("domains/04-operator-ledger/docs/operator-ledger.md").read_text(encoding="utf-8").splitlines()
cut = next(i for i, l in enumerate(lines) if l.startswith("## Executed adversarial checks"))
ENTRY = re.compile(r"^####\s+([A-Z]{1,2}\d{1,3})\.\s+`")
amend, cur = [], None
for l in lines[:cut]:
    m = ENTRY.match(l)
    if m: cur = m.group(1)
    if l.startswith("**Amendment ("): amend.append((cur, l))
checker = "\n".join(lines[cut:])
named = sorted({i for i, _ in amend if re.search(r"\b%s\b" % re.escape(i), checker)})
cite = re.compile(r"https?://|doi\.org|arXiv|RFC\s*\d+|§\s*\d|\bsee\s+[A-Z][a-z]+\s+(?:et al\.?,?\s*)?\d{4}")
print(len(amend), len(named), sum(1 for _, t in amend if cite.search(t)), len(amend) - len(named))
PY
```

**Why the recorded figure is wrong.** The claim is a figure for the whole file, and the recorded
**113 is exactly `116 − 3`**. Three is the witness count for the *second half* of the file alone
(`H20`, `R36`, `Y1`) — a half-range count applied to a whole-file denominator. That half is where the
claim's own qualifying clause puts it, and the same sentence's other figure, "34 of the 37 in this
range", is correct. The ledger's own header is more careful than either: its checker table states
that the tests "do not test all 116 editorial amendments".

**The record's halving of the file is also wrong.** The same record gives the ledger "130 amendments
(82 in the D4a range, 37 in the D4b range, 11 elsewhere)". The document contains **116** amendments,
and the ledger's own header and provenance table both say 116. By the half boundary the record itself
defines — `C35`/`C36`, with the record naming the second half `C36`–`Z50` — the split by line range
is **79 + 37 = 116**. The 82 is the sum of the ledger's per-family counts for families `L`–`C` taken
as whole families; that spans the boundary and includes `C44`, `C45` and `C47`, which the 37 already
counts. The "11 elsewhere" and the total "130" have no reading found here. One figure of the sentence
does hold: 37 amendments in the second half, 34 of them without a witness.

**Detailed working, do not restate it here:** `domains/04-operator-ledger/README.md`, section
"Amendment witnesses: the count actually measured", and `domains/04-operator-ledger/docs/validation-status.md`.
An amendment with no witness and no citation is an editorial opinion about a mathematical statement;
the working explains what that implies for the ledger's status. Cite the package; the arithmetic is
its.

---

## 4. AI-tool-adjacent wordings and machine-specific paths removed during assembly

**Verified here** for the measurements below; the line-by-line list is the integration scrub's.

**What was done.** For the assembled repository, two classes of text were removed from historical
documents and from logs and scripts:

1. wording that attributes a document or a change to a language model, or addresses the reader as
   one — in the D2, D8 and D10 documents;
2. machine-specific locations — a scratch directory that no longer exists on any host, and
   hard-coded home directories — in the audit-stack logs and scripts.

Nothing was silently deleted: scratch directories were replaced by the visible placeholders
`<workdir>` and `<home>/`, the read-only source tree by `<source-tree>`, so that a reader can see that
a path was removed rather than be shown a path that looks real. **No claim, count or result was
changed by any of those substitutions**; every number in the affected files is the number that was
there before.

**The assembly notes give** 22 lines of AI-sense vocabulary across the D2, D8 and D10 documents and
278 lines carrying a dead scratch directory or a hard-coded host path across the audit-stack logs and
scripts.

**Measured in this pass**, and this is where the two figures and the measurement part company:

- A scan of exactly the files the map copies, using the repository's own rule set, finds **276 lines**
  in these two classes: **D2 14, D10 10, D11 252**. **No D8 file is affected.** The D2 figure agrees
  with that domain's own record, which counts **14 single-line rewrites in six files** replacing one
  two-word phrase with the phrase the same corpus already uses for the idea — the same class of
  change, counted the same way.
- The rewrite classification over the assembled tree records **22 lines in 19 files** as path
  removals — all of them in the audit stack — and **284 lines in 35 files** as model-adjacent wording
  — spanning D2, D10 and D11.

So the split the notes give is not the split that is there: the 22 lines this pass measures are the
*path* removals in the audit stack, and the wording removals number in the hundreds, not 22, because
the same scratch-path string also trips the model-name rule. Both figures are of the order the notes
give and both come from the same assembly, but a reader checking either number against the repository
will not find the assignment of classes the notes describe, and no D8 file carries a hit in either
measurement. The counts also move while the packages are being written. The definitive,
line-by-line list of substitutions — path, line, rule, before, after — is `scrub-report.tsv` in this
directory, which is produced by the integration scrub and not by this package.

**The gate that holds it.** The repository's own scanner is run over the finished tree and must report
zero findings, in all of its classes: model and vendor names, model-attribution phrases and AI-sense
vocabulary, machine-specific absolute paths, campaign-tracking parameters, e-mail addresses and
token shapes. A finding in the published tree is a defect in this repository, not in the source.

---

## 5. A recorded value that does not reproduce — the superseded v0.1 trace-tag simulator

**Verified here** (the nondeterminism, over five runs); the recorded spread and the disposition are
**attributed** to `domains/02-ceqs-construction-evolution/` (`VERIFICATION.md` §2, `README.md` §3.1
and §6).

**Recorded.** `domains/02-ceqs-construction-evolution/history/ce_qs_trace_tag_simulator-v0.1.txt`,
line 3: `minimum observed quorum intersection=26`, produced by the superseded v0.1 simulator beside
it (`domains/02-ceqs-construction-evolution/history/ce_qs_trace_tag_simulator-v0.1.py`, in `history/` because a later revision supersedes
it).

**Re-run.** Five consecutive runs of the same command in the same environment in this pass read
**26, 25, 25, 26, 25**; the domain records **25, 26, 25, 26, 25** over its five runs, and its
`README` gives the observed set as **24, 25 or 26**. Every other line of the recorded output matched
exactly (tag payload 1,376 B, pair checks 1,849, both recovery lines and the closing note).

**Cause, from the source.** The v0.1 script draws its quorums from Python's module-level `random`
generator and never seeds it (`random.sample(range(n), q)`), so the number on line 3 is a **sample
minimum over 50 random trials**, not a computed bound — and a minimum over a random sample is the
statistic most sensitive to which sample was drawn. The v0.2 revision that supersedes it seeds all
randomness, including key material (`run(seed=1234, …)`), and is byte-for-byte reproducible.

**Disposition.** The recorded value stays in the historical file; it is not adjusted. The domain
states the spread and the reason beside it, and **no claim rests on the exact number**. The line is a
**simulation observation, not a bound**: the bound the same line quotes, `f + 1 = 22` for `n = 64`,
`q = 43`, is arithmetic and unaffected, and every observed value (24, 25 or 26) is above it. The
exact worst-case statement lives in the v0.9 checker (`conflict_extracts_exact_intersection
intersection=[0, 1, 2]`) and the exact arithmetic in the v0.7 checker, both of which reproduce.

---

## 6. A recorded "5/5" that counts a test which never ran, and one that cannot fail

**Attributed to `domains/02-ceqs-construction-evolution/`** (`README.md` §3.1, the v0.2 row;
`history/validation-and-continuation-v0.2.md` §4; the simulator's own final line).

**Recorded.** The v0.2 mutation-control suite prints, and the record repeats,
`ALL CE-QS v0.2 MUTATION CONTROLS PASSED (5/5 from Section 19 step 5)`.

**Read against the suite's own output**, two of the five are not what the total says:

1. **One control never executed.** `EXPECTED-FAIL mutation_challenge_collision SKIPPED: no colliding
   message found in probe budget`. The challenge-collision branch (`denom = 0`) was never reached, so
   no behaviour of it was demonstrated; the control is counted in the 5/5.
2. **One control cannot fail here.** `EXPECTED-FAIL mutation_duplicate_signer distinct-signer-count=42
   < q=43; tag algebra still traces only the true intersection (uniqueness must be enforced by the
   outer ZK relation, NOT by this algebra layer)`. Distinctness of the hidden signer set is deferred
   by the construction to the outer zero-knowledge relation Π, so a duplicate-seat mutant is not
   something this algebra layer can reject: the control confirms a delegation, not a property.

**Therefore the suite demonstrates three effective controls** — wrong-mask substitution, forged tag,
absent signer — not five. The historical file is not adjusted; the domain records both facts beside
the 5/5, and the same gap is what the v0.3 relation mock later closes with public duplicate-tag
rejection. This is the same class of entry as finding 3: nothing needed re-running, and the record
had counted something its own output says did not happen.

---

## 7. A recorded statement the surviving artifact contradicts — `Domains` and `Preps`

**Attributed to `domains/01-accountable-quorum-foundations/`**
(`docs/epoch-barrier-specification.md` §5, item 2, and its §4 defect list).

**Recorded.** Among the model-check output the domain ships as recorded:

```
ARTIFACT CONSISTENCY
--------------------
PASS every INVARIANT named in the CFG is defined in the TLA+ module
PASS Domains and Preps are referenced by the actual TLA+ state/actions
```

**Contradicted by the only surviving revision of the module.** In
`domains/01-accountable-quorum-foundations/formal/epoch-barrier.tla` (v0.6) both identifiers appear
only in the `CONSTANTS` line (`:4`) — `Nodes`, `F`, `Q`, `Epochs`, `Domains`, `Messages`, `Sessions`,
`Preps`, `EvidenceRoots`, `Boundaries` — and no state, guard, action or invariant references them
(`Epochs` likewise occurs only there). The configuration instantiates them
(`domains/01-accountable-quorum-foundations/formal/epoch-barrier.cfg:7-11`), which makes them look load-bearing.

**Why it is a correction to the record, not a defect in the specification.** The artifact-consistency
line is consistent with the v0.7 module the record describes, in which conflict domains and
preprocessing objects became real model dimensions — and the record itself confirms the v0.6 defect:
v0.6 "declared `Domains` and `Preps` but did not use them in the state machine", with `Epochs` later
removed as "a misleading unused parameter". The v0.7 files are not preserved, so the line is an
artifact-scope claim about a revision this repository does not hold and cannot re-run. Stated
precisely: **the surviving module does not support that line; the specification it describes is not
thereby wrong.**

**Related, and recorded the same way.** The recorded model-check output belongs to the *original*
module name, and no TLC or TLAPS run has been performed at any point in the record: the shipped
results files say `TLC status: NOT RUN in this environment`, and their PASS lines come from an
independent finite-state Python checker, not a model checker. TLC/TLAPS is not installed in the
verification environment of this pass either, so the recorded output is quoted as recorded, not
re-run. The file's own header comment records the one naming deviation this repository had to
accept — see `provenance.md` under the naming rules.

---

## 8. The ledger checker's only pass criterion disappears under optimisation

**Verified here** (reproduced in this pass on a scratch copy); recorded as a hazard in
`domains/04-operator-ledger/VERIFICATION.md`, row 7.

**The checker.** `domains/04-operator-ledger/src/operator_ledger_checks.py` — the extracted checker
for the operator ledger, copied byte-identical from the ledger document's own closing code block. Its
entire pass criterion is `assert`.

**Reproduction, this pass.** One expectation was broken on a scratch copy outside the repository
(`==[73,137,193,265]` → `==[74,137,193,265]`, checker line 223); the shipped file was not modified.

| command | exit | stdout | stderr |
|---|---|---|---|
| `python3 broken.py` | **1** | 0 bytes | `AssertionError` |
| `python3 -O broken.py` | **0** | the full 5,011-byte JSON summary, **23 groups `PASS`** | empty |

**The hazard.** `python3 -O` (or `PYTHONOPTIMIZE`) strips assertions, so the knowingly broken checker
reports a complete, well-formed, all-green result. A reader who reproduces this suite under
optimisation gets a pass that means nothing. **Remedy: do not run this checker with optimisations.**
The domain's `VERIFICATION.md` names the interpreter it used (CPython 3.12.3) and records that the
result does not depend on the interpreter above the 3.8 floor — which is not the same as being
indifferent to optimisation.

**Not an error in the record.** The document never claims otherwise. It is recorded because any
harness adopting the checker without knowing this would produce vacuous green results.

---

## What this pass could not verify

- **The audit ledger end-to-end.** The ledger's before/after totals in finding 2, and the 70/70 in
  `records/audit-checklist.md`, are the numbers `domains/10-digital-infrastructure/` records; this
  pass verified the loader chain and the repair on a controlled copy of four suites, and did not run
  the full ledger across all six suites.
- **The sanitizer and fuzzing evidence for finding F1**, the LMS interop differential for F3, the
  DNS wire tests (A2–A5, A21), and the devnet cross-reference A27: each needs a toolchain, a package
  or a host that the verification environment does not provide. The affected entries in
  `failed-assumptions.md` say so in their own rows, and the owning packages' `VERIFICATION.md` files
  record which of them were reproduced and which were not.
- **The wording removals of finding 4 are not visible in this package.** They are rewrites applied in
  the packages that own the documents; this package records the measurement and the gate, not the
  diffs.
- **The epoch-barrier model checks (finding 7).** No TLC or TLAPS run exists at any revision of that
  model, here or in the record, and neither is installed in the verification environment. The
  recorded output is quoted as recorded; the contradiction stands on reading the surviving module,
  which needs no toolchain.
- **The exact sample the v0.1 simulator drew (finding 5).** This pass observed 25 and 26 over five
  runs; the domain's set also contains 24. The value is a sample minimum, so the samples need not
  agree — the finding is the spread and the unseeded cause, both of which reproduce.
- **The internal workings of the two half-range amendment figures (finding 3).** The counts and the
  two corrections are attributable to `domains/04-operator-ledger/` and were confirmed here against
  the document; the classification of a witness as "computed" rather than "restated" is a reading of
  each cited test, and the domain's own working is the authority for it.

---

# Addendum — the D10 domain's own re-run

Findings 1 and 2 above are about `domains/10-digital-infrastructure/`: the fault they name lives in
its suites. This addendum is the other half of the record — the re-run performed **by the domain
itself**, in the pinned environment, after the repair. It is appended rather than merged because it is
a second, independent pass over the same ground, and the numbers it produced are additional samples,
not corrections. The domain's full account is `domains/10-digital-infrastructure/VERIFICATION.md`.

## 9. The ledger, end to end, after the repair

**Verified here.** The ledger was run to completion over all six suites:

```
python3 domains/10-digital-infrastructure/src/audit_ledger.py --refresh
→ 70/70 tests pass; suites: S1:ALL, S2:ALL, S3:ALL, S4:ALL, S5:ALL, S6:ALL
→ exit 0, wall time 7m29.8s (user 7m29.2s, sys 0.4s)
```

This closes the gap this pass left open above — *"the ledger's end-to-end totals … are attributed to
`domains/10-digital-infrastructure/`"*. They are now reproduced by the domain, at the recorded total.
The eight files the ledger wrote are kept as evidence.

The same sentence as finding 1 applies, and the domain's `README.md` and `VERIFICATION.md` carry it
too: the total came out on a run where the S1-011 slope statistic landed right, so **70/70 is not to
be reported as a stable reproduction**.

## 10. S1-011 — a third independent measurement of the flaky statistic

Finding 1 recorded two 200-run samples of the single-draw slope assertion: **98/200 (49.0 %)** in the
programme's measurement and **107/200 (53.5 %)** in this pass's re-measurement. The domain's own
re-measurement, importing the shipped
`domains/10-digital-infrastructure/src/s1_lms.py` and run after the repair, is a third:

| sample | runs satisfying `|slope − 0.5| ≤ 0.06` | range | median |
|---|---|---|---|
| the programme's | 98/200 = 49.0 % | 0.268–0.726 | 0.511 |
| this pass's | 107/200 = 53.5 % | [0.3195, 0.7261] | 0.4967 |
| the domain's | **108/200 = 54.0 %** | **[0.3195, 0.7255]** | **0.5097** |

Pooled across all three samples: **313 of 600 (52.2 %)**. Finding 1's pooled figure of 205/400
(51.3 %) was correct for the two samples it had; this is the same statistic over three samples, and it
does not change the finding — the recorded `PASS` was a favourable draw from a statistic that is
close to a coin flip.

The estimator that replaced it was re-measured too, 20 independent trials of 41 draws each:

| estimator | recorded | this pass | the domain |
|---|---|---|---|
| median of 41 draws | 20/20, [0.4819, 0.5316] | 20/20, [0.4765, 0.5256] | **20/20**, [0.4877, 0.5494] |
| median of 5 draws (rejected) | 17/20 | 14/20 | 15/20, range [0.4265, 0.6244] |

All three agree that 41 draws suffices and 5 does not. The rewritten test passed in every run the
domain performed, which is evidence and not a guarantee; the Grover-law statement stays a
**simulation**.

## 11. A difference between the canonical record and its regeneration: `model_discrepancies.S5`

**Verified here.**

**Recorded.** `records/audit-ledger.json` has `model_discrepancies.S5 = null`.

**Regenerated.** Running the ledger with `--refresh` produces the same ledger **except** that `S5` is
populated — with the four v2.0-claim → v2.1-measurement entries for the smart-card study: BDS state at
h = 8 is 664 B claimed against 828 B measured peak; 30,466 hashes/signature confirmed at 30,445.5; the
h = 20 maximum of ≤ 86,720 refuted at 95,775; and "state < 2 KB" refuted at 2,148 B.

**Cause.** `load_report()` reads a cached
`domains/10-digital-infrastructure/results/s5_audit_report.json` unless `--refresh` is given, and the
recorded ledger was generated against a cache that predated the `v2_0_claims_remeasured` block.

**Disposition.** Nothing was overwritten: both ledgers stand, and the domain states the difference in
its `domains/10-digital-infrastructure/VERIFICATION.md` §5.2 and
`domains/10-digital-infrastructure/docs/audit-method.md` §5.2. `model_discrepancies.S2`, `.S3` and
`.S4` match between the two exactly, so this is the only S-level difference in the whole ledger. It is
a property of the record's cache, not of the smart-card measurements, which do not change.

The rest of the regeneration diff is fully explained and carries no claim: the six suites'
`Ran N tests in T s` timing strings (which moved in both directions between hosts) and the two random
simulator draws `S1-G2-sim-n8` / `n10`. Every test ID, column, description and status is identical, in
the same order, and both files carry `**Totals: 70/70 tests pass.**` at line 118.

## 12. The revision files' names and placement, recorded rather than left to be discovered

Three files whose source names in the research tree end `_v2.0.py` are placed flat in `src/` beside
the domain's other Python, on the paths `records/file-map.tsv` gives:

| source name | path here |
|---|---|
| `pq_infra_s1s2_hashsig_dnssec_v2.0.py` | `domains/10-digital-infrastructure/src/s1s2_hashsig_dnssec-v2.0.py` |
| `pq_infra_s3_tls_pki_v2.0.py` | `domains/10-digital-infrastructure/src/s3_tls_pki.py` |
| `pq_infra_s4_embedded_broadcast_v2.0.py` | `domains/10-digital-infrastructure/src/s4_embedded_broadcast.py` |

Only the first keeps a version marker in its name, because dropping it would collide with the current
revision beside it, `domains/10-digital-infrastructure/src/s1s2_hashsig_dnssec.py` (assembled from
`pq_infra_s1s2_hashsig_dnssec_v2.2.py`). That revision is still imported by two files, so it is kept
rather than retired.

The choice is functionally inert: every cross-module load builds its path from the importing file's
own directory, so the modules only have to be siblings of each other, and a flat `src/` satisfies that
for every loader. Each load string was rewritten and then confirmed by re-running the whole ledger and
every individual suite. The domain states the layout in its `VERIFICATION.md` §6 rather than leaving
it to be discovered by comparing directory listings.

## 13. The forbidden-string gate on the domain tree

**Verified here.** `python3 tooling/checks/scan-forbidden.py domains/10-digital-infrastructure/`
reports **0 findings in all six categories over the 29 files of the domain**, exit 0. The two
byte-identical canonical copies this domain contributes to `records/` (`audit-checklist.md`,
`audit-ledger.json`) were scanned separately: 0 findings each.

This is the other half of finding 4 above. The wordings removed during assembly, and the
machine-specific paths that were carried in four scripts' `_PYLIB` lines, are gone from this domain's
tree — and the check is not a one-off reading, it is a command that returns exit 0.

## 14. The map gate, and the defect this domain reported in the rewrites table

The domain's first re-run of `python3 tooling/checks/verify-repository.py` reported **131** files whose
sha256 differed from the hash `records/file-map.tsv` records for their source, with **0** of them
explained — 14 of the 131 this domain's, all 14 of them recorded rewrites. The cause was mechanical
and this domain reported it rather than working around it: the verifier tests each differing
destination path against the `files` column of `records/rewrites.tsv`, and that column then held
source names, so a recorded rewrite could not be matched by the file it produced. With the table
regenerated destination-keyed, the same command now reports `sha256 differences: 0 (explained by
rewrites: 132)`, `UNEXPLAINED files: 0`, `RESULT: PASS`, exit 0, and all 14 of this domain's rows are
explained. No file in this domain changed between the two runs.

The verdict recorded in the domain's own `VERIFICATION.md` §5.3 is kept there in both forms, the
superseded failure quoted and the current pass stated, so the two observations can be read against
each other.
