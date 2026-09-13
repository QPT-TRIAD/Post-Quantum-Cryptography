# Recorded runs

Every file here is the raw, unedited output of a command that this build re-ran in the pinned
verification environment, on 2026-09-13, against the repository copy of the reference module
(`../src/sidecar_free_certificate.py`). None of them is a hand-written summary.

**Environment.** Ubuntu 24.04.4, x86_64, kernel 7.0.0-31, CPython 3.12.3; the environment
activation script puts liboqs 0.16.0 (locally built shared library, `OQS_INSTALL_PATH`) and
liboqs-python 0.16.0 on the path. The last file in the list is the one run *without* that
environment.

| File | Command | Exit | Result |
|---|---|---:|---|
| `self-test.txt` | `python3 ../src/sidecar_free_certificate.py --self-test` | 0 | `Ran 39 tests`, `OK` |
| `report.json` | `python3 ../src/sidecar_free_certificate.py --report` | 0 | size tables, size gate, lower bounds, Theorem C budgets |
| `real-demo.json` | `python3 ../src/sidecar_free_certificate.py --real-demo` | 0 | 8 runs over 7 schemes with real signature libraries; the measured table |
| `real-demo-unavailable.json` | `python3 ../src/sidecar_free_certificate.py --real-demo` outside the environment | 1 | `{"real_demo": "unavailable", ...}` — the documented behaviour |
| `probe_a10_f6.txt` | `python3 probe_a10_f6.py` (script in this directory) | 0 | findings A.10 and F6, replayed |

Run times in this build: self-test 0.18–0.19 s, `--report` 0.10 s, `--real-demo` 24.0 s (recorded
later in the same day: 19.8 s; the recorded baseline is 13.7 s). The spread is host load — the
same 8 runs produce the same numbers.

**Two deliberate differences from the recorded baseline, both recorded in `../VERIFICATION.md`:**

1. `report.json` has `"module": "sidecar_free_certificate"` where the recorded baseline has
   `"module": "sidecar_free_certificate_v1.44"`. That is the single content change of the
   file-rename rewrite; every other top-level key of the report is identical to the baseline run.
2. `real-demo.json` is byte-identical to the recorded `--real-demo` run in every field
   (`real_demo`, `schemes`, `liboqs_version`, `liboqs_python_version`,
   `category5_fitting_verified`, `summary`), including the four frame sizes 11,396 / 19,738 /
   24,984 / 30,918 and both ML-DSA-87 rows at 199,177.

`report.json` and the two `real-demo` files hold only programme output: no host paths, no
environment names, no timings that depend on the source tree.
