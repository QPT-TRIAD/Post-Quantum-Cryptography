# Packages

Every third-party package this domain mentions, what it is, how it works at the level needed to
trust its output, how it is installed and invoked, what it returned here, and its limitations.

**Which of the two package guides to read.** This file is the domain's own: it covers what D10 itself
imports, where each import sits, and what it returned *here*. The repository's environment-wide guide
is `tooling/packages.md`, which covers the whole pinned environment package by package — liboqs and
liboqs-python, sympy, galois, hypothesis, hsslms, dnspython, cryptography, pqcrypto, dilithium-py,
kyber-py and the formal tools — and how the environment is built in one pass. Read that one for the
tree-wide view and for the installation commands; read this one for anything D10-specific, for which
**this file is authoritative**. The two agree on every version this domain touches (`hsslms` 0.1.3,
`numpy` 2.4.6, `dnspython` 2.8.0, and the pins listed in §B). Where they would ever disagree on a
version or a returned value, the disagreement is to be stated in both places rather than settled
silently in one; none is outstanding at the time of writing.

The list is split in two, because the split is a finding. **Three** packages are actually imported
by a file in this domain: `hsslms`, `numpy` and `dnspython`. The rest are pinned in the programme's
environment and named as domain dependencies, but no D10 file imports them — they belong to other
parts of the programme, and a reader who assumes otherwise will misread what was verified here.

Pins are from the programme's environment manifest: Python 3.12.3, a dedicated virtual environment
activated by `tooling/activate.sh` before every command, `PYTHONDONTWRITEBYTECODE=1`. The import facts
below come from an AST scan of every `.py` file in the programme (96 files, including imports nested
in functions and `try:` blocks and `importlib.import_module("...")` string literals), which labels
each import `guarded(try)` or `unconditional`.

---

## A. Imported by a file in this domain

### A.1 `hsslms` — 0.1.3

**What it is.** An independent, third-party pure-Python implementation of LMS and HSS per RFC 8554
and NIST SP 800-208: Lehmer/Merkle signature schemes where a secret key is a chain and a public key
is the root of a Merkle tree over many one-time keys.

**How it works at the level that matters here.** It is a *second implementation from a different
author* of the same RFC this domain re-implemented from the RFC text. That is the whole reason it is
in the environment: two implementations of one byte format disagree loudly if either is wrong, and
`hsslms` is the far side of the comparison in both directions. It exposes the same objects the RFC
names — `LMOTS_SHA256_N32_W8`, `LMS_SHA256_M32_H20` and the other typecode parameter sets — with
`keygen`, `sign` and a verify routine. It is *not* used for anything cryptographic beyond the LMS
protocol; it is not a general toolkit.

**How it is installed and invoked.** `pip install hsslms==0.1.3` inside the pinned venv; recorded as
a dependency in the programme's audit document. In this domain it appears as

```python
try:
    import hsslms                                      # independent implementation
except ImportError:
    hsslms = None
```

in `src/s1_lms.py` and `history/s1_lms-v2.1.py` — *guarded*, so the two suites still run when it is
absent and the two interop tests then report themselves as skipped rather than silently passing.

**What it returned here.** With `hsslms` 0.1.3 installed, tests S1-003 and S1-004 both **PASS**:
signatures produced by `src/s1_lms.py` verify under `hsslms`, and signatures produced by `hsslms`
verify under `src/s1_lms.py`. The S1 report records `independent_implementation: "hsslms 0.1.3"`
(`results/s1_audit_report.json`). This is a byte-format agreement between two independent
implementations of RFC 8554, not a security evaluation of either.

**Limitations.** It is a single-maintainer pure-Python package with no security review, no
constant-time property and no side-channel hardening; its size and its agreement with this
domain's encoder say nothing about whether either implementation is safe to deploy. The version pin
matters: a different `hsslms` could change the typecode handling and the interop result with it.

---

### A.2 `numpy` — 2.4.6

**What it is.** The standard numerical array library for Python; `numpy.ndarray` plus vectorised
operations over them (`abs`, `argmax`, `conj`, `einsum`), and the complex arithmetic they rest on.

**How it works at the level that matters here.** The state-vector Grover simulation in `src/s1_lms.py`
holds the whole amplitude vector of the reduced game as a complex `ndarray` of length N = 2^n for
n ∈ {8, 10, 12, 14}, applies the oracle as a diagonal sign flip and the diffusion operator as a
rank-one update, and reads the first peak off the resulting probability vector. At n ≤ 14 that is at
most 16,384 complex amplitudes, so the "quantum" part is exact linear algebra and the only thing
being trusted is that numpy's complex `float64` arithmetic rounds the way IEEE-754 double
arithmetic does. There is no tolerance knob to abuse: the simulation is exact arithmetic on a small
vector.

**How it is installed and invoked.** `pip install numpy==2.4.6` inside the pinned venv;
`import numpy as np`, **unconditional**, in `src/s1_lms.py` and `history/s1_lms-v2.1.py`. It is the
only hard third-party dependency of the two S1 suites and hence of the ledger's S1 row.

**What it returned here.** The exact per-seed assertions in S1-011 — `|k_measured − k_predicted| ≤ 1`
and the success probability equal to its closed form to 1e-9 — hold **200/200** in both the
programme's measurement and every re-measurement made for this repository. The simulation runs at
n ≤ 14; see the flakiness discussion in `VERIFICATION.md` for the one statistic that is not stable.

**Limitations.** `numpy` 2.4.6 is pinned because the programme's other parts pin it; nothing in D10
exercises a numpy feature that changed between major versions. The simulation is a *simulation*: it
shows that the counting law holds for a reduced, exactly-representable instance. It is not a
measurement of a deployed oracle and does not make the Grover-law statement a measurement.

---

### A.3 `dnspython` — 2.8.0

**What it is.** The reference DNS library for Python: message construction and parsing, the wire
format of RFC 1035, the DNSSEC record types of RFC 4034/4035/5155, name compression, and the EDNS
OPT pseudo-record.

**How it works at the level that matters here.** S2's whole claim is a byte size, so it cannot be
made by arithmetic alone. `src/s2_dns_worstcase.py` builds every message as a real `dns.message.Message`
with real `dns.rrset` / `dns.rdata` objects, lets dnspython do the DNS-specific work that is easiest
to get wrong by hand — name compression, the RRSIG/NSEC/NSEC3/DNSKEY rdata layouts, the OPT
pseudo-record, EDNS buffer advertisement — then calls `to_wire()`, and the *length of those bytes* is
the measurement. It then parses the same bytes back with `from_wire()` and checks the RRSIG count it
intended, so an encoding that silently dropped a record is caught rather than counted.

**How it is installed and invoked.** `pip install dnspython==2.8.0` inside the pinned venv; recorded
in the S2 audit file's own docstring and in the programme's container recipe.
`import dns.message, dns.name, dns.rrset, dns.rdata, dns.rdatatype, dns.rdataclass, dns.rcode, dns.flags`
— **unconditional** — in `src/s2_dns_worstcase.py`. With it absent, S2 does not run at all.

**What it returned here.** The exact wire sizes quoted throughout `docs/studies.md` §2 and in
`results/s2_audit_report.json` — for example 954 B for the model's own baseline zone shape (the
model had claimed 1,129 B) and 1,839 B for the worst legal NSEC3 denial. It also produced the
per-query binding-game counts of 109/24,576 unprefixed and 145/24,576 prefixed against an expected
2^−8 = 0.00390625, and the multi-target counts 90/1 and 401/2 per 100,000 queries at n = 16.

**Limitations.** dnspython encodes and parses bytes; it makes **no** security claim and validates
nothing here. Two protocol decisions in the S2 messages are the audit's own, not dnspython's and not
any IETF draft: the first RRSIG of a shard carries MTL-Type 2 plus the multiproof while the others
carry MTL-Type 3 plus a 4-byte leaf index, and ALG = 18 (the ML-DSA-44 code point) is used as a
placeholder. The message shapes are therefore *legal DNS* rather than *a standardised MTL
deployment*. And a correct encoder cannot settle the deployment question the study is about:
resolver and middlebox behaviour above 1,232 B and 1,400 B is cited from the literature, not
measured.

---

## B. Pinned and named as domain dependencies, but imported by no D10 file

These are in the programme's environment and in the D10 dependency list. None is imported by any
file under `domains/10-digital-infrastructure/`. Each is listed with the file that does own it, so a
reader can tell what a claim rests on and what it does not.

| package | pin | what it is | where it actually appears |
|---|---|---|---|
| `cryptography` | 46.0.0 | the pyca crypto library — HKDF, AES-GCM, hashes — via the OpenSSL bindings | the ML-KEM/ML-DSA experiment's `authorization.py` and its tests (2 files, both unconditional). Not in D10. |
| `galois` | 0.4.11 | finite-field arithmetic over GF(p^m) with a numba backend | the audit stack's `math/math_layer.py` (unconditional). Not in D10. |
| `sympy` | 1.13.1 | symbolic mathematics | the audit stack's math layer. Not in D10. |
| `kyber-py` | 1.2.0 | a pure-Python ML-KEM (Kyber) implementation | the D3 ML-KEM/ML-DSA experiment. Not in D10. |
| `dilithium-py` | 1.4.0 | a pure-Python ML-DSA (Dilithium) implementation | `primitives/cross_validate.py` inside the audit-stack archive. Not in D10. |
| `pqcrypto` | 0.3.4 | libpqcrypto bindings (SPHINCS+, Kyber, Dilithium, Falcon, …) | 2 files of the ML-KEM/ML-DSA experiment (1 unconditional). Not in D10. Installed from a **bundled wheel**, sha256 `b2f9bad4…6ebb`, not from PyPI — reinstalling from PyPI gets a different build. |
| `liboqs-python` | 0.16.0 | bindings to liboqs (module name `oqs`) | the sidecar-free finalisation work (1 file, guarded). Not in D10. |
| `hypothesis` | 6.151.9 | property-based testing (generates inputs and shrinks counterexamples) | 6 files, all inside the audit-stack archive — the property tests for the hash-signature, modeB and TESLA modules. Not in D10. |
| `pytest` | 9.0.2 | the test runner | runs the audit stack's `property/run_all.sh`. Every D10 suite is plain `unittest` and takes `--self-test` or `--report`; **no D10 command needs pytest**. |

Also in the environment host-wide but not recorded in any ledger and not used here: `cffi` 2.0.0,
`mpmath` 1.3.0, `numba` 0.65.1, `llvmlite` 0.47.0, `Pygments` 2.21.0, `packaging` 26.3,
`pluggy` 1.6.0, `iniconfig` 2.3.0, `sortedcontainers` 2.4.0, `typing_extensions` 4.16.0.

A second, separate environment exists for the containerised math layer (`Dockerfile.math`, base
`python:3.12-slim`) with **different** pins: `sympy==1.14.0`, `galois==0.4.11`, `numpy==2.2.6`,
`numba==0.61.2`, `llvmlite==0.44.0`. That is the container's maths reproduction, not the D10
environment, and the two `numpy` and `sympy` pins must not be conflated: D10's S1 suites run against
`numpy` **2.4.6** on the host profile. No D10 file imports `sympy`, `galois` or `numba` at all.

---

## C. What D10 needs from the standard library

For completeness, since a reader checking "can this be reproduced" needs the whole dependency set:
`argparse`, `collections`, `functools`, `hashlib`, `heapq`, `hmac`, `importlib.util`, `json`, `math`,
`os`, `random`, `secrets`, `statistics`, `struct`, `sys`, `threading`, `time`, `unittest`. Nothing
else. Every suite is `python3 <file> --self-test` or `python3 <file> --report`, and the loaders that
pull one module into another use `importlib.util.spec_from_file_location` with a path built from the
importing file's own directory — so the modules must remain **siblings** of each other for the
cross-checks to work. See `docs/studies.md` and `VERIFICATION.md`.
