# Import inventory

Which script imports which package, and what stops working when a package is missing.

The table below was produced by walking every `.py` file in this repository with an AST parser — so
imports nested inside functions and inside `try:` blocks count, and so do
`importlib.import_module("...")` string literals — and then classifying each imported name as a
standard-library module, a project-local module, or a third-party package. The result was checked by
re-scanning the repository as shipped: 95 `.py` files, no parse failures, 11 third-party import
names, 6 project-local module names. Spot checks of individual lines were then made by hand against
the shipped sources; the line numbers below are those of the shipped files.

Two columns matter and are easy to conflate:

- **hard** — the import runs unconditionally when the file is imported or when the function holding
  it is reached. Without the package the script stops.
- **guarded** — the import sits inside a `try:`. Without the package the script continues along a
  documented fallback path, which is *not* the same as passing.

## Summary

| import name | pip distribution | files | hard | guarded |
|---|---|---:|---:|---:|
| `cryptography` | cryptography | 2 | 2 | 0 |
| `dilithium_py` | dilithium-py | 1 | 1 | 0 |
| `dns` | dnspython | 1 | 1 | 0 |
| `galois` | galois | 1 | 1 | 0 |
| `hsslms` | hsslms | 4 | 2 | 2 |
| `hypothesis` | hypothesis | 6 | 6 | 0 |
| `kyber_py` | kyber-py | 1 | 1 | 0 |
| `numpy` | numpy | 4 | 3 | 1 |
| `oqs` | liboqs-python (module `oqs`) | 1 | 0 | 1 |
| `pqcrypto` | pqcrypto | 3 | 2 | 1 |
| `sympy` | sympy | 1 | 1 | 0 |

Six packages installed in the environment are imported by **no** source file and so do not appear
above: `mpmath` and `llvmlite` (dependencies of sympy and numba), `numba` (used by galois at
runtime), `pytest` (invoked as a command by `property/run_all.sh`), `cffi` (required by the
`pqcrypto` wheel) and `liboqs` itself (loaded through `ctypes` and through the `oqs` binding rather
than imported by name). `packages.md` covers them.

## Package by package

### `cryptography` → cryptography 46.0.0

- `domains/03-zk-carrier-experiments/src/authorization.py`:15–17 — `hashes`, `HKDF`, `AESGCM` — hard
- `domains/03-zk-carrier-experiments/src/test_authorization.py`:30 — `InvalidTag` (inside a test) and
  `:163` — the version string recorded in the test output — hard

**If it is missing:** the authorization experiment cannot start. Its `reproduce.sh` and its 51
component checks have no fallback.

### `dilithium_py` → dilithium-py 1.4.0

- `domains/11-independent-audit-stack/primitives/cross_validate.py`:38 — `ML_DSA_87` — hard

**If it is missing:** the primitives cross-check stops. It is one of the three implementations being
compared; without it the layer has two and cannot cross-check.

### `dns` → dnspython 2.8.0

- `domains/10-digital-infrastructure/src/s2_dns_worstcase.py`:39 — `dns.message`, `dns.name`,
  `dns.rrset`, `dns.rdata`, `dns.rdatatype`, `dns.rdataclass`, `dns.rcode`, `dns.flags` — hard

**If it is missing:** the DNSSEC worst-case layer stops at its import line. This is what the recorded
baseline shows for every one of its three invocations:
`ModuleNotFoundError: No module named 'dns'`, exit 1. In the pinned environment of this repository
the package is present, so a re-run behaves differently from the baseline — see the note at the end.

### `galois` → galois 0.4.11

- `domains/11-independent-audit-stack/math/math_layer.py`:39 — hard

**If it is missing:** the whole mathematics layer stops. `galois` is the independent field engine the
layer is built around; there is no fallback.

### `hsslms` → hsslms 0.1.3

- `domains/10-digital-infrastructure/src/s1_lms.py`:39 — guarded, `HAVE_HSSLMS = False` on failure
- `domains/10-digital-infrastructure/history/s1_lms-v2.1.py`:38 — guarded, same pattern
- `domains/11-independent-audit-stack/property/test_props_hashsig.py`:36 — hard
- `domains/11-independent-audit-stack/fixes/property_fixed/test_props_hashsig_fixed.py`:36 — hard

**If it is missing:** two different outcomes, and the difference matters.

- The S1 audit continues. It reports `OK (skipped=2)` with `skipped 'hsslms not installed'` for
  S1-003 and S1-004, and records `"independent_implementation": null` in its report. A skipped
  differential check is not a passed differential check.
- The hash-signature property suite does **not** run: the two `test_props_hashsig*` files import the
  package unconditionally, and pytest reports a collection error.

### `hypothesis` → hypothesis 6.151.9

- `domains/11-independent-audit-stack/property/test_props_b0.py`:25
- `domains/11-independent-audit-stack/property/test_props_hashsig.py`:16
- `domains/11-independent-audit-stack/property/test_props_modeB.py`:25
- `domains/11-independent-audit-stack/property/test_props_tesla.py`:22
- `domains/11-independent-audit-stack/fixes/property_fixed/test_props_hashsig_fixed.py`:16
- `domains/11-independent-audit-stack/fixes/property_fixed/test_props_modeB_fixed.py`:25

All six are hard. **If it is missing:** the entire property layer fails, and with it the layer of the
audit stack that attempts falsification rather than confirmation. `property/run_all.sh` writes one
log per file into `property/logs/`, so the failure is visible per file.

### `kyber_py` → kyber-py 1.2.0

- `domains/11-independent-audit-stack/primitives/cross_validate.py`:39 — `ML_KEM_1024` — hard

**If it is missing:** the primitives cross-check stops, for the same reason as `dilithium-py`.

### `numpy` → numpy 2.4.6

- `domains/11-independent-audit-stack/math/math_layer.py`:37 — hard
- `domains/10-digital-infrastructure/src/s1_lms.py`:323 — hard (imported inside the Grover-chain
  function, so the failure surfaces when that function runs)
- `domains/10-digital-infrastructure/history/s1_lms-v2.1.py`:311 — hard, same pattern
- `domains/08-hidden-signers/history/hidden-signer-mode-b-v1.46.py`:491 — guarded, inside
  `numpy_evaluator()`

**If it is missing:** the mathematics layer stops; the S1 Grover-chain computation stops. The D8
v1.46 revision falls back to a pure-Python evaluator, which is correct but far slower, and the run
then records `"evaluator": "pure-python"` where the recorded baseline records `"evaluator":
"numpy"` — a difference in the log that is about speed, not about the result.

Note that the *current* revision `domains/08-hidden-signers/src/hidden_signer_mode_b.py` (v1.51)
imports no numpy at all; the guarded import belongs to the v1.46 base revision it loads from
`history/`. A repository-wide scan sees it there, and that is the file the row above refers to.

### `oqs` → liboqs-python 0.16.0

- `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`:668 — guarded

**If it is missing:** the certificate demo's `--real-demo` mode reports
`{"real_demo": "unavailable", "reason": ...}` and exits 1; the rest of the script runs. The module
also tries `pqcrypto` first, so a machine with `pqcrypto` but no liboqs still produces real
signatures — from a smaller scheme set.

### `pqcrypto` → pqcrypto 0.3.4

- `domains/03-zk-carrier-experiments/src/authorization.py`:13–14 — the ML-KEM-1024 KEM and the
  ML-DSA-87 signature scheme — hard
- `domains/03-zk-carrier-experiments/src/install_dependency.py`:35 — guarded, used to check whether
  the pinned package is importable
- `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`:551 — guarded, the signature
  family used by the real-signature demo

**If it is missing:** the authorization experiment cannot start. The certificate demo falls back to
liboqs for real signatures, and if neither is available reports itself unavailable. The wheel is not
retained in this repository; `packages.md` gives the digest and the install command.

### `sympy` → sympy 1.13.1

- `domains/11-independent-audit-stack/math/math_layer.py`:38 — hard

**If it is missing:** the mathematics layer stops. `sympy` is the exact-arithmetic engine; `galois`
does not replace it.

## Project-local modules

These are not installable. They resolve through the directory of the script that loads them, so they
work exactly as long as the files are kept where the map places them. None of them needs a
`PYTHONPATH` entry.

| module | loaded by | how |
|---|---|---|
| `authorization` | `domains/03-zk-carrier-experiments/src/test_authorization.py`:14, `verify_audit.py`:6 | ordinary import, same directory |
| `oqs_ctypes` | `domains/11-independent-audit-stack/primitives/cross_validate.py`:37 | ordinary import, same directory |
| `b0_indep` | `domains/11-independent-audit-stack/independent-b0/check_vectors.py`:18 | ordinary import, same directory |
| `paired_reference` | `domains/03-zk-carrier-experiments/src/{make_fixture,verify_public,check_public_mutations}.py` and the three history revisions | ordinary import, same directory |
| `seed_carrier_demo` | `domains/03-zk-carrier-experiments/src/audit_carriers.py`:5 | ordinary import, same directory |
| `verify_public` | `domains/03-zk-carrier-experiments/src/check_public_mutations.py`:5 | ordinary import, same directory |

Three further module loads are dynamic rather than syntactic, so no import statement names them, and
they are the ones that break if a file is moved:

| file | loads | from |
|---|---|---|
| `domains/08-hidden-signers/src/hidden_signer_mode_b.py`:41 | `modeB46` = the v1.46 base revision | `../history/hidden-signer-mode-b-v1.46.py` |
| `domains/08-hidden-signers/src/mode_b_voleith_toy.py`:69 | the v1.46 base revision | `../history/hidden-signer-mode-b-v1.46.py` |
| `domains/09-security-games-and-attack-lab/src/{ceqs_games,ceqs_attack_lab}.py` | `modeB50` = the v1.50 revision | the same directory, by filename |

The last row is the one to watch: those two scripts load the D8 v1.50 revision by name from their own
directory. The repository places that revision under
`domains/08-hidden-signers/history/hidden-signer-mode-b-v1.50.py`, so the loader path in the shipped
file has to point there. If a re-run stops with a `FileNotFoundError` naming
`hidden_signer_modeB_v1.50.py`, that path is what to check.

## Differences from the pre-publication scan

This repository is a renamed and reorganised copy of an earlier source tree (the layout rules and the
exclusions are recorded under `records/`). Two differences between the scan of that earlier tree and
the scan of this repository are worth recording, because both would otherwise look like mistakes:

1. **`pqcrypto` has three importing files here, not two.** `install_dependency.py` — the script
   `reproduce.sh` calls — checks whether the pinned package is importable, and that check is an
   import.
2. **`numpy` no longer appears in the current hidden-signer revision.** The original tree's
   `hidden_signer_modeB_v1.46.py` carried the guarded numpy evaluator; in the shipped tree that
   revision is a history file and the current revision v1.51 has no numpy import. The package is
   still a hard dependency of the mathematics and S1 layers, so the environment still needs it.

## Availability note, stated once

The recorded baseline logs and the pinned environment of this repository disagree about two
packages: `hsslms` and `dnspython`. The baseline was produced with neither available, which is why
it shows two skipped S1 tests and a DNS layer that died at its import line. Both packages are
installed in the environment this repository ships instructions for. A re-run therefore produces
*more* than the baseline in those two places. That is an availability difference, not a change in any
cryptographic result, and it is recorded here so that a reader comparing a fresh run against the
baseline is not surprised by it.
