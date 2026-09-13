# The third-party packages, one by one

This is the environment-wide guide: every third-party package the repository's scripts import, what
it is, how far its output can be trusted, how to install it, how it is used here, and where its limits
are. `environment.md` gives the commands that create the whole environment in one pass; this file
explains what those commands install and why each pin is what it is. Per-domain guides carry the
detail of a domain's own dependencies; this file is the one that covers the tree.

Versions here were read from the installed environment with the commands in `VERIFICATION.md`.

Two rules apply throughout, and they are the reason this file exists rather than a bare list of
version numbers:

- **A package is a tool, not a result.** `galois` agreeing with the project's own field arithmetic
  means two implementations agree. It does not mean the field is right for the job, and it does not
  extend to any statement the project makes on top of it.
- **A dependency that was present changes what a log means.** A log line recording
  `skipped 'hsslms not installed'` is not a pass. `imports.md` says which scripts degrade or stop
  when a package is missing; the domain documents say which recorded results were affected.

## The Python environment at a glance

| Package | Installed | Kind | Needed by |
|---|---:|---|---|
| sympy | 1.13.1 | symbolic and exact arithmetic | the mathematics layer |
| mpmath | 1.3.0 | arbitrary-precision floats (SymPy dependency) | sympy |
| galois | 0.4.11 | GF(2^m) arithmetic, by a different author than the project's own | the mathematics layer, and independently checked by the smoke test |
| numpy | 2.4.6 | arrays | mathematics layer, the infrastructure audits, the ledger |
| numba | 0.65.1 | JIT for numeric Python (used by galois) | performance of galois |
| llvmlite | 0.47.0 | LLVM bindings (numba dependency) | numba |
| hypothesis | 6.151.9 | property-based testing | the six property-test files of the audit stack |
| pytest | 9.0.2 | test runner | `property/run_all.sh` |
| hsslms | 0.1.3 | an independent LMS implementation | the hash-signature property tests and the S1 audit |
| dilithium-py | 1.4.0 | pure-Python ML-DSA (FIPS 204) | the primitives cross-check |
| kyber-py | 1.2.0 | pure-Python ML-KEM (FIPS 203) | the primitives cross-check |
| dnspython | 2.8.0 | DNS message parsing | the DNSSEC worst-case audit |
| cryptography | 46.0.0 | HKDF, AES-GCM, and other primitives | the authorization experiment |
| cffi | 2.0.0 | C bindings used by `pqcrypto` | `pqcrypto` |
| pqcrypto | 0.3.4 | compiled ML-KEM/ML-DSA bindings (PQClean-derived) | the authorization experiment and the certificate demo |
| liboqs-python (`oqs`) | 0.16.0 | Python bindings for a locally built liboqs | the certificate demo, when `OQS_INSTALL_PATH` names an installed liboqs |

Everything here is a binary wheel. Nothing in the Python layer needs a compiler.

---

## Symbolic and exact arithmetic

### sympy 1.13.1

- **What it is.** A computer-algebra system: exact rational and integer arithmetic, symbolic
  equation solving, and symbolic manipulation.
- **Why its output can be trusted here.** It is the *independent* engine in the mathematics layer:
  the layer solves the quorum-intersection inequality symbolically and separately enumerates
  `N = 4..64` exhaustively, then compares. A disagreement between the two would be a finding. SymPy's
  arithmetic is exact for the operations used; no floating-point step is involved in the results that
  are quoted.
- **How it is used.** `domains/11-independent-audit-stack/math/math_layer.py` imports it as `sp` and
  records `sp.__version__` in the `_meta` block of `math_results.json`.
- **Install.** `pip install sympy==1.13.1`. Pulled in as a distribution dependency are `mpmath`,
  and `typing_extensions` below Python 3.13 — both harmless and both pinned by the lock file.
- **Limits.** SymPy proves nothing about a cryptosystem; it evaluates the algebra it is given. The
  mathematics layer's verdicts are statements that its expressions evaluate as recorded, not
  security statements.
- **Version note.** The recorded ledgers write "SymPy 1.13"; the installed patch level is 1.13.1.
  The container profile pins 1.14.0 (`environment.md` §5), and the two profiles give the same eight
  verdicts.

### galois 0.4.11

- **What it is.** Galois-field arithmetic for Python, written by a different author from the
  project's own field code and using a different algorithmic route for the same operations.
- **Why its output can be trusted here.** The whole point of using it is *disagreement detection*:
  the mathematics layer compares `galois` against the project's own field implementation on
  multiplication, inversion, the seventh power and the seventh root, and reports the mismatch count.
  The verification pass additionally ran every one of the 65,536 products in GF(2^8) against an
  independent shift-and-add reference: **0 mismatches**. That is the strongest statement in this
  file — a complete enumeration of the smallest field, not a sample — and it is still only a
  statement about one field.
- **How it is used.** `import galois` in `math_layer.py`, under `# noqa: E402` because the script
  inserts its own path first. `numba 0.65.1` is the JIT backend it uses for speed.
- **Install.** `pip install galois==0.4.11`. It pulls in `numpy` and `numba`; both are pinned.
- **Limits.** Field arithmetic is where this package's authority ends. It says nothing about the
  choice of modulus, the encoding of field elements, or anything built on top.
- **Version note.** The recorded "galois 0.4.11" and the container pin 0.4.11 agree, and both
  profiles ran without a mismatch.

### numpy 2.4.6

- **What it is.** The array package; also the substrate for `galois`'s field elements.
- **How it is used, and where it matters.** The mathematics layer records `np.__version__` in
  `_meta`. `domains/10-digital-infrastructure/src/s1_lms.py` imports it *inside* the Grover-chain
  function, so the S1 audit needs it at that point; the hidden-signer revisions that used numpy as an
  optional evaluator fall back to a pure-Python path when it is absent.
- **Limits.** Floating-point and integer array semantics are the standard ones; no exact-arithmetic
  claim rests on numpy except where the recording engine names it.

### numba 0.65.1 / llvmlite 0.47.0

- **What they are.** A JIT compiler for numeric Python and its LLVM binding; `galois` compiles its
  field routines through them.
- **Trust.** They change *how fast* the field code runs, not what it computes; a JIT miscompilation
  would show up as a mismatch in the differential check, which reported zero mismatches over the
  full GF(2^8) sweep. Treat the pair as an implementation detail of `galois`, with one caveat: a
  different Major version of numba changes the compiled code path, which is why both profiles pin it.
- **Version note.** numba is the one package whose host version is **not recorded in any ledger**;
  0.65.1 is what the host install that produced the recorded `galois` results carries. The excluded
  container file named 0.61.2, which the container profile reproduces. Neither number is asserted by
  a document; install one of them and you have chosen a code path.

## Test-driven and property-driven checks

### hypothesis 6.151.9

- **What it is.** A property-based testing library: it generates inputs from a strategy, tries to
  falsify a stated property, and *shrinks* any counterexample to a minimal one before reporting it.
- **Why that matters for trust.** The audit stack's property layer uses it to state invariants
  ("no malformed certificate is accepted", "the differential agrees on every pair") and then attacks
  them. The value is in the falsification habit: a suite that passes reports the inputs it generated.
  The shrinking behaviour is why failures in the property logs come with a minimal reproducer.
- **How it is used.** Six files import `given`, `settings`, `strategies as st`, `HealthCheck` and
  `assume`, always unconditionally: `property/test_props_{b0,hashsig,modeB,tesla}.py` and the two
  `fixes/property_fixed/` files. `property/run_all.sh` runs them.
- **Install.** `pip install hypothesis==6.151.9`. It brings `sortedcontainers` and `attrs`-family
  helpers as small pure-Python dependencies.
- **Limits.** A passing property test is evidence about the *distribution it sampled*, not a proof.
  Several property files set explicit `max_examples`, so their coverage is bounded and recorded as
  such. The recorded property logs do contain genuine failures — read them rather than the exit
  status alone.
- **Version note.** The ledgers write "Hypothesis 6.151"; the patch level 6.151.9 comes from the
  install. The never-built full container file names 6.168.0.

### pytest 9.0.2

- **What it is.** The test runner. Also the harness for the Hypothesis suites: `python3 -m pytest`.
- **How it is used.** `domains/11-independent-audit-stack/property/run_all.sh` invokes
  `python3 -m pytest` on the four property files and writes one log per file into `property/logs/`.
- **Limits and note.** No source file imports pytest, so it never appears in `imports.md`; the
  property layer stops at the runner if it is missing. **No version is recorded** anywhere in the
  repository for it — 9.0.2 is the host install.

## Post-quantum primitive implementations (independent of liboqs)

### dilithium-py 1.4.0

- **What it is.** A pure-Python implementation of ML-DSA (FIPS 204 final) by Giacomo Pope. The
  round-3 Dilithium scheme lives in a separate module (`dilithium_py.dilithium`); the FIPS 204 code
  is `dilithium_py.ml_dsa`.
- **Why its output can be trusted here.** It is one of three independent implementations of the same
  standard that the primitives cross-check compares: liboqs (C), dilithium-py (pure Python), and the
  NIST ACVP vector files. The cross-check drives named ACVP test groups through each implementation
  and records agreement *and* the cases where an interface does not exist (for example liboqs exposes
  no HashML-DSA entry point, so it is recorded as `n/a`, never as a pass).
- **How it is used.** `from dilithium_py.ml_dsa import ML_DSA_87` in
  `domains/11-independent-audit-stack/primitives/cross_validate.py`, unconditionally. Seeded key
  generation goes through `key_derive(seed)`.
- **Install.** `pip install dilithium-py==1.4.0`.
- **Limits.** Pure Python, so it is a correctness reference, not a performance one. Like any
  implementation it inherits its library's assumptions; it has not been independently audited here.

### kyber-py 1.2.0

- **What it is.** The same author's pure-Python ML-KEM (FIPS 203). Round-3 Kyber is a separate module.
- **Trust and use.** The KEM half of the same three-way cross-check, imported as
  `ML_KEM_1024` in the same file. It raises on malformed encapsulation keys and on decapsulation
  hash checks, so its exceptions are part of the recorded behaviour rather than a silent return.
- **Install.** `pip install kyber-py==1.2.0`.
- **Limits.** As above: a correctness reference for a KEM, not a claim about the scheme.

### pqcrypto 0.3.4

- **What it is.** Python bindings to PQClean-derived C implementations of ML-KEM and ML-DSA
  (`pqcrypto.kem.ml_kem_1024`, `pqcrypto.sign.ml_dsa_87`, and the Falcon/ML-DSA/Frodo families used
  by the certificate demo).
- **Why the pin is tight.** It is a compiled artefact: the wheel that was used is
  `pqcrypto-0.3.4-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`, 27,036,304 bytes,
  SHA-256 `b2f9bad43a1e3970f55e6f68fc1864595c9b0c6e53638aa8393b1d01216a6ebb`, checked to be the PyPI
  release file for 0.3.4. That digest identifies the executed implementation; it is not a
  conformance certification or a side-channel audit.
- **How it is used.** `domains/03-zk-carrier-experiments/src/authorization.py` imports the KEM and
  the signature scheme unconditionally, so the authorization experiment cannot start without it.
  `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` imports the signature family
  inside a `try:`, so its `--real-demo` mode degrades to `"real_demo": "unavailable"` with a named
  reason instead of failing.
- **Install.** The wheel is **not** retained in this repository. Install the pinned version from
  PyPI and check the digest, or supply a copy:
  `pip install --no-deps pqcrypto==0.3.4`, then
  `python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <wheel>`
  against the value above. `domains/03-zk-carrier-experiments/src/install_dependency.py` accepts a
  `--wheel` path, verifies that digest before installing anything, and otherwise only reports whether
  the pinned package is already importable.
- **Limits.** A binding is only as good as the C it binds. It is a second implementation for
  cross-checking, not an audited one; the repository uses it as a witness, never as the root of a
  security claim.
- **Version note.** `cryptography` must be at least 46.0.0 for the recorded behaviour of the
  authorization experiment; `cffi` is required and is installed explicitly rather than as a
  transitive dependency, so that `--no-deps` can be used above.

### hsslms 0.1.3

- **What it is.** An independent implementation of LMS (RFC 8554 / SP 800-208), a stateful
  hash-based signature scheme.
- **Why it is used.** Two different things depend on it, and they behave differently when it is
  absent — this is the single most important availability caveat in this file:
  - `domains/10-digital-infrastructure/src/s1_lms.py` imports it inside a `try:` and continues
    without it. The S1 audit then **skips two tests** (S1-003, S1-004) and reports
    `OK (skipped=2)`, and its report records `"independent_implementation": null`. A skipped test is
    not a pass; the recorded baseline log says so explicitly.
  - `domains/11-independent-audit-stack/property/test_props_hashsig.py` and
    `fixes/property_fixed/test_props_hashsig_fixed.py` import it **unconditionally**, so the
    hash-signature property suite cannot run at all without it.
- **Install.** `pip install hsslms==0.1.3`. Pure Python; it uses `hashlib` for the tree hashes.
- **Limits.** It is a second implementation used for differential checking. It does not make the
  stateful-signature management correct, which is what the surrounding audits examine.

### dnspython 2.8.0

- **What it is.** DNS message construction and parsing.
- **How it is used.** `domains/10-digital-infrastructure/src/s2_dns_worstcase.py` imports
  `dns.message`, `dns.name`, `dns.rrset`, `dns.rdata`, `dns.rdatatype`, `dns.rdataclass`,
  `dns.rcode` and `dns.flags` **unconditionally**. Without the package the layer stops at the import
  line: the recorded baseline shows all three invocations failing with
  `ModuleNotFoundError: No module named 'dns'`.
- **Install.** `pip install dnspython==2.8.0`.
- **Limits.** It parses and builds DNS on the wire. Every DNSSEC statement in that layer is the
  project's own; the package contributes the message format and the presentation notation.
- **Version note.** The DNSSEC study's own docstring and the container file both record dnspython;
  2.8.0 is the installed version observed here.

### cryptography 46.0.0

- **What it is.** The `cryptography` library: HKDF, AES-GCM, hashes, and the primitives behind them.
- **How it is used.** `domains/03-zk-carrier-experiments/src/authorization.py` imports HKDF, SHA-512
  and AESGCM unconditionally; `test_authorization.py` imports `InvalidTag` to assert that a tampered
  envelope is rejected rather than silently accepted, and records
  `cryptography.__version__` in its output.
- **Install.** `pip install cryptography==46.0.0`. The wheel bundles its own OpenSSL, so the
  version on the host does not change its behaviour — which is also why it is pinned.
- **Limits.** It supplies the standard primitives; the composition around them (KEM plus
  authenticated envelope, nonce handling, duplicate-origin cache) is the project's, and the
  experiment's own document states that it is a custom experimental composition rather than an
  implementation of a named channel standard.

### cffi 2.0.0

- **What it is.** C Foreign Function Interface: the ABI layer `pqcrypto`'s bindings are built on.
- **How it is used.** Not imported by any source file; it is a hard requirement of the `pqcrypto`
  wheel, installed explicitly so that `pqcrypto` itself can be installed with `--no-deps`.
- **Limits and note.** No version is recorded in the repository; 2.0.0 is the host install.

### liboqs-python (`oqs`) 0.16.0, with liboqs 0.16.0

- **What they are.** liboqs is the C library of post-quantum schemes; `liboqs-python` is its Python
  binding. Here liboqs is **built locally from source** (`environment.md` §6) rather than fetched by
  the binding, because the binding would otherwise clone and build its own copy at import time, which
  is neither pinned nor reproducible from this repository alone.
- **Why it is used.** It is the third independent implementation in the set, and the only one that
  offers the wide scheme range (OV-V, SNOVA, MAYO, and the rest) the certificate layer's real-signature
  demo needs. The verification pass drove ML-DSA-87 and ML-KEM-1024 through the project's own
  `ctypes` wrapper against it and confirmed the recorded signature width of 4,627 bytes for ML-DSA-87,
  a successful verify, and rejection of both a wrong message and a tampered signature.
- **How it is used.**
  - `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` reads `OQS_INSTALL_PATH`,
    loads `lib/liboqs.so` (or `lib64/`) with `ctypes` **before** importing `oqs`, and treats a
    `SystemExit` during import as "unavailable".
  - `domains/11-independent-audit-stack/primitives/oqs_ctypes.py` is a thin `ctypes` wrapper that
    uses only the public `OQS_SIG`/`OQS_KEM` API and no Python binding at all; its default library
    path is resolved relative to the audit stack, and its `LibOQS(path)` argument overrides it.
    `environment.md` §6 gives the compatibility link this needs.
- **Install.** `pip install liboqs-python==0.16.0` for the binding; the library comes from the
  build in `environment.md` §6, with `OQS_INSTALL_PATH` and `LD_LIBRARY_PATH` set by `activate.sh`.
- **Limits.** liboqs is a collection of implementations with a shared API, not a single audited
  artifact; scheme availability and claimed security levels come from the submitters. The
  certificate layer therefore records, for each scheme, whether it produced a frame at all, whether
  the frame verified, and whether tampering was rejected — and it records the claimed-level caveat
  rather than treating a successful signature as security evidence. The primitives layer states its
  own boundary in its first paragraph: it validates the primitives and says nothing about the
  construction built on them.

---

## The formal tools

### tamarin-prover 1.12.0

- **What it is.** A symbolic protocol verifier: given a multiset-rewriting model of a protocol and
  its equational theory, it decides reachability and equivalence properties by constraint solving,
  and prints a proof or a counterexample trace.
- **How far its output can be trusted here.** Tamarin is the strongest tool in this stack, and its
  authority stops exactly where the *model* does. It proves that no trace of the given rules satisfies
  the given lemma. Whether those rules are the protocol is a separate question, and the repository's
  formal layer states which lemmas are about the model and which are about the construction.
  Independently, the tool's own self-test was re-run during the verification pass: 55 cases tried,
  55 successful, 0 errors, 0 failures, exit 0.
- **How it is run.**
  `tamarin-prover --prove formal/qpt128_quorum.spthy` from
  `domains/11-independent-audit-stack`, which is what `run_all.sh` does; it needs Maude and, for its
  tool-availability check, GraphViz `dot`. The recorded run took 111 s and verified all twelve
  lemmas. The larger instantiation (`qpt128_quorum_n7.spthy`) does **not** finish: the recorded
  batch run was stopped at 1,200 s, and a per-lemma run leaves several lemmas with no result. That
  gap is recorded as a gap, not as a pass.
- **Install.** The published `tamarin-prover-1.12.0-linux64-ubuntu.tar.gz` binary release, with
  `maude` on `PATH` and `MAUDE_LIB` set. Digests in `environment.md` §7.
- **Limits.** Bounded by the model and by the equational theory; it tells you nothing about
  computational security, key sizes, or the implementation.

### maude 3.5.1

- **What it is.** A rewriting-logic engine. Tamarin uses it as its equational solver, so a lemma
  that Tamarin reports as verified is only as good as Maude's answer to the equational questions
  Tamarin asks.
- **How it is run.** Never directly by this repository; Tamarin invokes it. `activate.sh` sets
  `MAUDE_LIB` to the distribution directory, which is what Maude needs to find its prelude.
  3.5.1 is the newest release that Tamarin 1.12 accepts, and Tamarin's own version check
  (`checking version: 3.5.1. OK.`) is visible in the recorded output.
- **Limits.** Same as above, one level down: it is the equational engine, not a verifier of the
  protocol claim.

### proverif 2.05

- **What it is.** An automatic verifier for the applied pi-calculus: it takes a process-algebra model
  with cryptographic primitives given by rewrite rules and proves or refutes correspondence and
  observational-equivalence properties.
- **Why it is here.** It is an independent second formal engine for the same protocol family. The
  repository ships two models (`formal/qpt128_quorum.pv` and `formal/qpt128_quorum_C1.pv`).
- **How it is run.** `proverif formal/qpt128_quorum.pv` from the audit stack, guarded by a
  `command -v proverif` test in `run_all.sh`. The recorded baseline of the full stack shows
  **`ProVerif NOT RUN (proverif not on PATH)`** — the environment at that moment did not expose it,
  and the script says so rather than reporting a pass. In the environment built for this repository,
  ProVerif is present and its distribution example
  (`examples/pitype/secr-auth/NeedhamSchroederPK-corr.pv`) reproduces its documented expected
  result, which is how its installation is checked.
- **Install.** No distribution package exists. It is built from the upstream source tarball with
  `./build -nointeract`, which needs an OCaml compiler; `environment.md` §7 records how the compiler
  was obtained without root.
- **Limits.** Same shape as Tamarin's, with a different trust surface: the result is about the model
  under its abstraction. Where a ProVerif and a Tamarin model of the same protocol disagree, that is
  a finding about the models, and it is treated as one.

### graphviz `dot` 2.43.0

- **What it is.** Graph layout, used to render attack and proof graphs.
- **How it is run.** `tamarin-prover` calls it; nothing in this repository calls it directly. Its
  presence is needed for Tamarin's tool check to pass, and for the interactive/graph output. The
  unification self-test passes 55/55 with or without it.
- **Install.** Ubuntu packages fetched with `apt-get download` and unpacked with `dpkg -x` into the
  environment, with a small launcher on `PATH` that sets `LD_LIBRARY_PATH` and `GVBINDIR`
  (`environment.md` §7).
- **Limits.** It draws pictures. It has no bearing on any verdict.

---

## Statements in other packages that disagree with what was observed

Two disagreements were found while writing this guide. Both are reported rather than reconciled,
because neither is this package's file to change.

1. **hsslms and dnspython: "not installed on the host".** The theory and package index records
   hsslms and dnspython as not installed, and the recorded baseline logs agree with it in the
   behaviour they show (`skipped 'hsslms not installed'`; `ModuleNotFoundError: No module named
   'dns'`). In the pinned environment built for this repository **both are installed and
   importable** (hsslms 0.1.3, dnspython 2.8.0). The two are not in contradiction once the
   interpreter is named: the index's statement is about the *audit host's system interpreter*, while
   the pinned environment adds both packages. The practical consequence matters, so it is stated
   plainly: **a re-run with the environment sourced will not skip S1-003/S1-004 and will not fail
   the DNS layer at its import line**, so those layers will produce results where the recorded
   baseline produced skips and import errors. Any re-run therefore differs from the baseline in
   exactly this way, and the difference is about availability, not about the cryptography.
2. **The bundled pqcrypto wheel.** `domains/03-zk-carrier-experiments/docs/package-assessment.md`
   §8 says `reproduce.sh` "installs the bundled pinned `pqcrypto` wheel into a local `vendor`
   directory". In the tree as shipped, the wheel is not retained, and
   `domains/03-zk-carrier-experiments/src/install_dependency.py` — which `reproduce.sh` calls —
   only *checks* that the pinned package is importable and installs nothing unless it is given an
   explicit `--wheel` path, in which case it verifies the digest first. The script's behaviour is the
   accurate description of the shipped tree, and it is the behaviour this guide documents. The two
   words that conflict — "bundled" in that sentence, and "the included wheel's SHA-256" two
   paragraphs below it — are contradicted by the same domain's own `domains/03-zk-carrier-experiments/docs/provenance.md`, which says
   the wheel "is excluded (27 MB of third-party binary)" and that `domains/03-zk-carrier-experiments/results/dependency-provenance.json`
   retains the publisher's filename, URL and digests instead, and by the script's module docstring,
   which says the wheel "is not retained in this repository". So the §8 wording is a stale line
   inside a package that otherwise describes the shipped tree correctly — not a disagreement about
   how to install anything, and not something a reader can act on wrongly: the command in §8 and the
   command this guide gives reach the same state.

A third item is not a disagreement, and it was a blind spot that has since been closed. The
repository's forbidden-string scanner reads files by suffix, and when this guide was first written
it did not treat `.math` as text, so `tooling/audit-stack/Dockerfile.math` was never scanned. Its
example `docker run` line used to carry a machine-specific mount path for the read-only tree, in a
comment; no gate would have found it, and it was caught by reading the file. It has since been
redacted by the file's owner to a neutral mount, and the suffix has been added to the scanner's text
set by that package's owner, so the file is now examined and passes clean. What remains worth
knowing is the shape of the boundary rather than this instance: any file whose suffix is outside the
scanner's text set is published unexamined, and the set is what decides. See `VERIFICATION.md` §4.4
for the observation and `environment.md` §8 for what that means if you add a file of your own.
