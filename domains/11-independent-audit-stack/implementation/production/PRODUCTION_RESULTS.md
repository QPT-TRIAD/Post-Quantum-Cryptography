# Production-parameter sanitizer runs (step 3 of the fix stage, 2026-09-13)

Target: `implementation/src/modeB_prover_v1.50.c` (the frozen reference), binaries built by
`implementation/build.sh` with the private compiler-rt (`rt/18`). Parameters: b = 20, τ = 11,
wg = 16, ρ = 4096 (τ·b + wg = 236 ≥ 230, the FAEST-v2 QROM requirement). Script:
`run_production.sh`; done-marker `done`.

| run | binary | threads | wall | exit | sanitizer reports | verdict |
|---|---|---|---:|---:|---|---|
| ASan + UBSan, `--run` (prove, verify genuine and tampered, extract) | `bin/asan_ubsan` (v1.50) | 8 (OpenMP) | 2,194 s | 1 (LeakSanitizer at exit) | 0 AddressSanitizer errors, 0 UndefinedBehaviorSanitizer errors over the whole run; LeakSanitizer: 11 allocations, 33,714,488 B | **memory-safe and UB-free at production parameters; F1 reproduced** |
| MSan, `--run` | `bin/msan` (v1.50) | 1 (libomp is uninstrumented, so no OpenMP) | 3,600 s | 124 (timeout) | none before the timeout | **inconclusive** — not a pass |

## Leak classification (LeakSanitizer output, `asan_ubsan_production.txt`)

| bytes | objects | allocation site | class |
|---:|---:|---|---|
| 19,136 | 2 | `verify` line 803 (`circ_pub_t *P`) | **F1**: the grinding-condition early return leaks P per rejected verification; two rejections in this run (tampered cases) → 2 × 9,568 B. Fixed in `modeB_prover_v1.51.c` (regression: 0 `verify` frames in `v151_lsan_reduced.txt`). |
| 12,416 + 1,840 + 1,840 + 64 | 4 | `main` lines 974, 975, 982 | process-lifetime allocations never freed before `exit` (keymap, registry, buffers) — not growth; no finding beyond tidiness |
| 33,554,432 + 65,536 | 2 | `qmap_init` lines 253–254 (called from `main`:974) | the 32 MiB seeded quadratic map and its index, owned by the objects above — same class |
| 29,100 + 29,100 + 1,024 | 3 | `prove` line 700 and children | proof buffers reachable from the unfreed `main` objects — same class |

The only per-call leak is F1. The remaining 33.7 MB is the process's working set at exit, freed
by the OS; it would matter only for a long-lived library embedding, where a `qmap_free` at
shutdown is the fix (not applied to the frozen reference).

## What this does and does not establish

- The C reference at production parameters ran prove + verify + extract once under ASan/UBSan
  with no memory-safety or undefined-behaviour report. One run, one seed: coverage evidence,
  not a proof of memory safety.
- MSan at production parameters did not finish in 60 min single-threaded (ASan needed 37 min
  with 8 threads; MSan is ≈ 3× slower per thread). Completing it needs an MSan-instrumented
  libomp or a multi-hour budget. MSan **is** clean at reduced parameters (`msan_output.txt`,
  53.8 s).
- The functional JSON of the production run is absent from the ASan log because LeakSanitizer's
  non-zero exit discards buffered stdout (known; the v1.51 reduced functional run used
  `detect_leaks=0` + `stdbuf`).
- v1.51 was not re-run at production parameters under ASan; its F1 fix is regression-tested at
  reduced parameters only.
