# Milestone 10–11 — reporting, integration, and what the cross-checks caught

**All 294 tests pass; the milestone-0 probe reports 19 of 19 checks.** The reporting layer emits
seven sections with the scope boundary structurally guaranteed, and the end-to-end test exercises
the pipeline from instance to report.

## The cross-check battery earned its place

The project's design put a battery of invariants in place — each computed two ways from independent
references — on the explicit reasoning that the sibling Grover project's integration pass found
three real defects in modules that were each already green in isolation. **This build's battery
caught three defects of the same kind**, and each was a case where every check that existed at the
time passed.

| what it caught | how it looked in isolation | which check found it |
|---|---|---|
| The normal form's pivot could leave a rank-deficient `A'` | The relation held, `\|det B\| = q^m` held, every structural check passed — while the lattice's short-vector structure was different | the dual construction, which **cannot be built at all** from a deficient `A'` |
| `GSO.Mat.get_r(i,i)` returns the **squared** Gram-Schmidt norm, so `prod(r_ii) = det²` | A root-Hermite factor of 0.937 where the truth was 1.018 — a perfectly believable value | cross-check 5, the exact-determinant route |
| The embedded lattice always contains `(0, …, 0, p·M)` when `p \| q` | **Membership passed.** The planted vector really was in the lattice; the attack was simply not attacking it | the two-sided recovery test — recovery at a high block size *and not at a low one* |

**All three were invisible to every check that existed before them**, and two of the three produced
numbers that looked entirely reasonable. That is the argument for computing each invariant twice
from different references, made concretely rather than in principle.

The third is the most instructive. A membership check answers "is this lattice right"; a
shortest-vector check answers "is this attack meaningful", and the two failure modes do not overlap.
The project had the first and not the second, and the gap was exactly where the defect lived.

## Cross-check 6 — the one to keep

`assert_same_lattice` solves `U·B = B_red` exactly and asserts `U` is integral with `|det U| = 1`.
Both engines are individually self-consistent, and a reduction that silently changed the lattice
would produce a plausible basis and a plausible root-Hermite factor. No per-engine test can see it.
It is the lattice analogue of the bit-ordering bug that survived a whole suite in the sibling
project, and it is verified non-vacuously here: a single-coordinate perturbation is caught.

## The report's structure is enforced, not remembered

| requirement | how it is guaranteed |
|---|---|
| the scope boundary appears | emitted on every path through `generate_report`, with no argument that suppresses it |
| **before** the first table | an index comparison, not a substring check — a boundary in a footnote after three tables of results would satisfy `in text` while defeating the purpose |
| measured and extrapolated never blend | each section carries its provenance in its own heading, drawn from the protocol's labels so heading and datum cannot drift apart |
| a disagreement is named | `ComparisonResult` refuses to hold a discrepancy outside tolerance with no anomaly |

The seventh section is an addition to the design document's six, and the reason is that the build
found things it did not resolve. A report ending at the anomalies would read as a clean result; it
is not one. Six items are carried forward unconditionally, because none is a property of a
particular run.

## What integration did *not* change

The pipeline composed without a further defect, which is worth stating plainly rather than dressing
up: the boundaries were frozen as code before the layers were built, and the three defects above
were caught *during* the milestones by checks designed for them rather than at the end by luck.

## Both of the open items are now closed

- `cli.py` and `scripts/run_experiment.py`, `scripts/sweep_dimensions.py` exist, with `probe`, `run`,
  `sweep`, `report`, `planted-check` and `estimate` as subcommands. Every capability the design
  document names is reachable from a command line as well as as a library call.
- The sweep across the configured dimension range has been run. **It did not survive contact
  unchanged** — the fit as specified measures the machine rather than the model, and was replaced.
  That is recorded in `09-scaling-and-the-sweep.md`, along with a boundary defect the *report*
  carried: it read one shape of the fit while the pipeline wrote another, and rendered a full table
  of dashes. Four tests now guard the rendering.

The second item is the one to read. A fit that was green in every test was wrong in its first real
use, and the report that was supposed to carry it displayed nothing — a second wrong thing, agreeing
with the first, in a way no unit test on either side could see.
