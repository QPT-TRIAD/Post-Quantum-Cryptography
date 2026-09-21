# Test-completion audit — what the new tests pinned, and what was fixed (2026-09-20)

**The suite was green and the code was wrong.** A completion audit added test
files whose failing tests were marked `xfail(strict=True)`, one marker per defect, each naming a
file and a line. This note records each defect, the fix, and the one consequence that reaches
outside the source tree: **numbers already stored under `results/`**.

Every marker is now removed and the test bodies are unchanged, with one exception recorded at the
end. None of these defects raised. Each produced a plausible record.

## Stored results carry the un-rooted Hermite factor

**Every `results/` directory written before 2026-09-20 records `||b1|| / det^(1/d)` — the Hermite
factor, with no `d`-th root — under the key `root_hermite_factor`, and in the report column headed
`root-Hermite`.** `engines/base_engine.py::root_hermite_factor` omitted the root; the primal attack
and the pipeline copied its value unchanged. At dimension 61 a stored run says ~1.0117 where the
metric the design document defines (and `analysis.achieved_root_hermite_factor` computes) is
~1.0002.

**The stored files are not rewritten.** They are the evidence the earlier notes cite, and
`notes/09`'s determinism table (3.11695792, 3.78538167, 3.55510025, 1.22330782 at dimension 80) is
a table of *un-rooted* values. Its argument — four identical four-thread processes, three distinct
values — is untouched, because taking a root is monotone and distinct values stay distinct. To
compare a stored figure with a new one, take the stored figure to the power `1/d`, where `d` is
that row's `dimension` column.

Two consequences inside the code:

- the report's `root-Hermite` column printed four significant digits, which was enough for 1.012
  and renders every rooted value as `1`. It prints seven now (`report_generator.py`,
  `_section_measured`).
- three existing tests pinned un-rooted values and were re-pinned to their `d`-th roots:
  `test_engine_lattice_preservation.py` (`REDUCED_HERMITE_FACTOR`, `PERTURBED_HERMITE_FACTOR`) and
  `test_g6k_sieve_engine.py::test_a_dual_mode_run_records_the_mode_only_for_that_call`. The
  one-entry corruption the first of those demonstrates now moves the reported figure by 2.2e-6
  rather than 8.7e-5 — forty times harder to see, which is that test's point made stronger.

## Defects fixed before this pass (markers removed here)

| defect | where | fix |
|---|---|---|
| both Hermite routes floored the leading norm with `math.isqrt`; `[[1,1],[-1,1]]` reported 0.8409 for a factor of exactly 1, *from both routes, in agreement* | `analysis/hermite_factor.py` | the norm is no longer floored |
| `root_hermite_factor` returned the un-rooted factor | `engines/base_engine.py` | takes the `d`-th root; the helper in `test_fpylll_bkz_engine.py` omitted the same root and was corrected with it |
| `LatticeQLWRInstance` checked ranges and rank but never types; a float secret constructed and `target` came back as floats | `problem/qlwr_instance.py` | `_require_integer`; `bool` refused by name |
| `artifact_norm` required `q // p == 2B`, true only for an even ratio; at `q=105, p=7` it reported no artifact while `(0,…,0,p·M)` sat in the lattice | `lattice/primal_embedding.py` | the condition is `(q // p) // 2 == B` |

## Defects fixed in this pass

### The negative control was a planted instance

`random_lattice_control` built a `LatticeQLWRInstance` exactly as `synthetic_scaled` does — uniform
base, uniform secret, **samples derived from that secret** — under a different label. The primal
attack recovered it at block size 2. The one experiment that could show the attack firing on
nothing could not fail to fire.

**Fix.** The instance type gained `control_samples`: when set, those values *are* the public
samples, drawn uniformly over the values a sample can take (`(q // p) · v`, `v ∈ Z_p`). A secret is
still recorded and explains nothing. `to_normal_form` skips `check_small` for a control — refusing
it would be *true* but would turn every control point into a not-run, and "the attack ran and
recovered nothing" is the statement a control exists to make. `describe()` records `planted:
false`. `synthetic_scaled` draws are unchanged, so every recorded seed rebuilds its instance.

### The pipeline, five ways

| defect | fix |
|---|---|
| **Fallback.** `run_experiment` built `preference[0]` and never looked at the rest; the shipped `[g6k, fpylll_bkz]` raised `RuntimeError` without G6K where the YAML promises a logged fallback | `select_engine` accepts a `preference` list (head requested, tail the only permitted substitutes) and the pipeline passes the whole list. One WARNING names both engines. A one-engine preference is that engine or a refusal, decided before any work. An enumeration-only run never constructs or imports G6K |
| **RAM budget.** `engine.ram_budget_gb` was read nowhere; a 1 MiB budget ran every point | `assert_within_ram_budget` is called per block size before the sweep and before the dual reduction. An over-budget point is a `not_run` row *and* a `results["not_run"]` entry |
| **`output.formats`.** Read nowhere: `[json]` still wrote `report.md`; `png` wrote nothing, because `reporting/plots.py` had no caller | `markdown` decides the report, `png` draws `figures/block_size_curve.png` from the measured primal points. `metrics.json` is written regardless — it is the record the report regenerates from and the sweep writes back into |
| **Sweep refusal.** Fewer than three fitted dimensions appended the refusal to the in-memory outcomes only | the refusal — and a failed growth fit — is written back to each run's `metrics.json` and report |
| **Instance builder.** `while True` until a full-rank base appeared; `nu_over_m = (3, 2)` made that impossible and the loop never ended | bounded at 64 draws with an error, and `nu >= m` is refused before drawing |

### Config fields that changed nothing

| field | what it does now |
|---|---|
| `engine.gauss_crossover` | handed to G6K's `SieverParams.gauss_crossover` (the sieving dimension below which G6K uses its Gauss sieve). 50 is G6K's own default, so the shipped value changes no result |
| `attack.search_beyond_prediction` | block sizes more than this far above the estimator's uSVP prediction are not attempted; if nothing below recovered, they become `not_run` rows. The estimate is therefore computed before the attack. At the shipped sweep the bound never binds below a measured minimum: the predictions are 40, 40, 44, 69 and 88 at d = 60, 80, 100, 130 and 160 against `notes/09`'s minima of 10, 20, 40 and 60 at the first four (none was found at 160), and at d = 40 the model returns no uSVP block size, so the whole range is tried |
| `instance.nu_over_m` | validated: two positive integers, numerator strictly below denominator. `(1, 0)` was a `ZeroDivisionError` downstream, `(3, 2)` a hang, `(-1, 2)` silently clamped to `nu = 2` |

### Limits and defaults that contradicted the design document or the measurements

- **Block-size ceiling.** The design document requires an explicit opt-in above dimension 200 or
  block size **60**; the schema said 90. `sieve_block_size_max` defaults to 60.
  `BLOCK_SIZE_HARD_MAX = 90` is the ceiling the opt-in itself stops at — the largest block size
  calibrated, and the bound the G6K engine's reading of `MAX_SIEVING_DIM` leans on. The schema's
  default `block_size_range` now stops at 60, so `ExperimentConfig()` passes its own validator.
  **The shipped YAML keeps its range to 80 and sets `long_run_opt_in: true`**, with the reason
  beside it.
- **Thread default.** 4 in the schema, the selector and the G6K engine; `notes/09` measured more
  than one thread as not reproducible, and the shipped YAML already pinned 1. All three default to
  1. Three existing tests pinned the 4 and were updated — they were pinning the defect.

### Reporting

- `SCOPE_BOUNDARY` was commented "verbatim from section 7 of the design document" over a
  paraphrase, and the design document has no section 7. It is now the paragraph from the top of
  that document, verbatim after the bold run-in label, followed by this project's one added
  sentence. The literal is embedded in `tests/test_report_structure.py`.
- Section 3 labels a refused row "not run — see section 6", and section 6 rendered `comparisons`
  only. It now lists every `not_run_reason` and every `results["not_run"]` entry, once each.

### Cost estimation

- `_estimate_sis` read the cost with `getattr(lattice, "rop", None)`; the estimator's `Cost` is a
  dict subclass, so Dilithium2/3/5 all reported `None`. Read through `_cost_field`, they report
  2^152.2, 2^211.5 and 2^288.2.
- The production estimate was labelled `theoretical_same_scale`. **Nothing was attacked at that
  scale.** `ParameterSet` carries a `provenance`; `production_parameter_set` sets `extrapolated`,
  `estimate()` defaults to the set's own label, and refuses to relabel a non-same-scale set as
  same-scale. The library call and the CLI's `production-estimate` both emit the label without
  either having to remember it.

### The hardware profiler

`scripts/profile_hardware.py` forked a child per configuration and subtracted the **parent's**
`ru_maxrss`. That is the parent's high-water mark, not the child's starting point: a parent that
had ever been heavier than it is now clipped every delta to zero, and a 300 MiB allocation was
reported as costing nothing. Each child now reads its own baseline at entry and its own peak; the
import-overhead measurement does the same.

## Weak tests strengthened

- `test_attacks.py::test_the_distinguisher_separates_real_from_uniform_when_it_can` — **deleted.**
  It handed the statistic a unit vector its own comment said is not in the dual, and asserted two
  fractions lay in `[0, 1]`. `tests/test_dual_attack_measured.py` supersedes it fully.
- `test_attacks.py::test_a_block_size_the_engine_refuses_becomes_a_result_not_an_exception` accepted
  either provenance; it asserts `not_run` and the reason.
- `test_end_to_end.py::test_cross_check_4b_the_dual_invariants_are_independent` broke annihilation
  only. It now breaks each check alone — a doubled row stays in the dual and changes only the
  volume — and matches each message.
- `test_production_parameters.py::test_the_cli_reports_what_the_number_is_for` skipped on any
  non-zero exit. It skips only when the estimator is absent, decided before the command runs.

## Not resolved

`tests/test_report_structure.py::test_no_measured_number_is_labelled_extrapolated` formats the
root-Hermite factor as `f"{value:.4g}"` and requires that string in section 3 and absent from
section 5. With the root taken, that string is `1` — the same string as section 5's `R squared`
for a flat fit. The test was written against un-rooted values and cannot pass against rooted ones
with its body unchanged: either the report prints a column of ones, or the test's string is not in
section 3. The report was given the digits it needs; the test body was left alone, as instructed,
and **fails**. The repair is one line — format that key with the report's seven digits.

`reporting.plots.plot_measured_vs_extrapolated` still has no caller in `src/`. Its natural inputs
here would be log2 *seconds* against log2 *operations* on one axis, which is a blend of units the
reports exist to prevent; it was left uncalled rather than wired to a figure that misleads.
