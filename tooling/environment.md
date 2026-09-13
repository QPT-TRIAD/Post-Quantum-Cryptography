# Rebuilding the verification environment

This document rebuilds, from nothing, the environment in which every recorded result of this
repository was produced and re-checked: one pinned Python interpreter, one locally built liboqs
shared library, and three formal tools. It also states plainly what could **not** be reproduced
here, and why.

Two paths lead through this package:

- **Rebuild from scratch.** Follow §1–§6. Nothing needs to be present except the operating system,
  a C toolchain, and network access to the distribution archives and the upstream release pages
  named below.
- **Reuse an existing environment.** Skip to §3: point `PQT_ENV` at an environment that already has
  `venv/`, `liboqs/` and `tools/` in the layout of §3, set `PQT_SRC`, and source `activate.sh`.

`tooling/activate.sh` is the single entry point for every command in this repository. It is
portable: it contains no machine-specific path. The environment root defaults to the directory
holding the script, and the research tree comes from the caller's `PQT_SRC`.

---

## 1. What the environment must provide

| Layer | Provided by | Used for |
|---|---|---|
| Python 3.12 interpreter and 15 third-party distributions | `venv/` built in §4 | every checker, ledger, extractor, simulator and property test |
| A second interpreter profile with the container's mathematics pins | `venv-math-container/` built in §5 | re-checking the results recorded by the containerised mathematics layer |
| liboqs 0.16.0 shared library, built from source | `liboqs/` built in §6 | the certificate demo's real-signature runs and any script that loads `oqs` |
| `tamarin-prover` 1.12.0, `maude` 3.5.1, `proverif` 2.05, `dot` | `tools/` built in §7 | the symbolic protocol model, its equational engine, the applied-pi models, and the proof-graph rendering that the Tamarin self-test checks for |

The three formal tools are only needed for the protocol-model layer recorded in
`domains/11-independent-audit-stack/formal`. Every other layer runs on the Python environment alone.

## 2. Host requirements

The environment recorded here was built on Ubuntu 24.04.4, x86-64, kernel 7.0.0-31, with:

| Requirement | Version used | Needed for |
|---|---|---|
| Python | 3.12.3 (system) | creates both virtual environments; the pinned wheels are `cp312` |
| gcc / g++ | 14.2.0 | building liboqs; also the recorded compiler for the C provers in `domains/08-hidden-signers/src` |
| cmake | 4.4.2 | liboqs build |
| ninja | 1.11.1 | liboqs build (`-GNinja`) |
| OpenSSL development files | 3.0.13 (`libcrypto.so.3`) | liboqs links against the system OpenSSL by default |
| git, curl, unzip, tar | distribution versions | fetching liboqs, Tamarin, Maude, ProVerif and the GraphViz packages |
| `dpkg-deb` (`apt-get download` + `dpkg -x`) | distribution version | extracting GraphViz and, for ProVerif, an OCaml toolchain, without root |
| Disk | ≈2 GB free | two virtual environments (≈460 MB), liboqs source and build tree (≈800 MB), tools (≈250 MB) |

Python 3.12 is a hard requirement for the Python layer: the `pqcrypto` wheel is a `cp312` build, and
`domains/02-ceqs-construction-evolution/src/ce_qs_backend_eligibility_checker.py` needs Python ≥ 3.10
for `int | None` in a dataclass. No step needs root: the two archive-based toolchains (GraphViz,
OCaml) are extracted with `dpkg -x` into the environment rather than installed system-wide.

## 3. Layout and activation

Everything lives under one root, `PQT_ENV`:

```
tooling/                      <- this package; PQT_ENV defaults to this directory
  activate.sh                 the activation script (no machine path inside)
  environment.md              this file
  packages.md                 per-package install and trust guide
  run-everything.md           the ordered run recipe
  imports.md                  which script imports which package
  VERIFICATION.md             what was observed in the live environment
  audit-stack/
    Dockerfile                container build for the whole stack (never built; see §8)
    Dockerfile.math           container build for the mathematics layer (built once, 8/8)
  venv/                       the pinned Python environment (host profile)      [created in §4]
  venv-math-container/        the container mathematics pins                   [created in §5]
  liboqs/                     the liboqs 0.16.0 install tree                   [created in §6]
  tools/                      the formal tools and their launchers             [created in §7]
```

`venv/` is ignored by this repository's `.gitignore`. The build trees of §6 and §7 bring several
hundred megabytes; keep them out of version control.

Activate with:

```sh
export PQT_SRC=/path/to/research-tree
source tooling/activate.sh
```

Two lines, not one: in bash an assignment written on the same line as `source` is undone when that
command returns, so the harnesses run afterwards would see `PQT_SRC` unset and report themselves not
run. The activation script says so itself when it finds the variable unset.

`PQT_SRC` names a local copy of the read-only research tree that this repository was built from. It
is **not** shipped here: the harnesses in `domains/11-independent-audit-stack` read their input files
from it, so they need it at run time. If `PQT_SRC` is unset, `activate.sh` prints one sentence saying
what it is for and how to point at a local copy, and continues.

The variables it exports, and why each one matters:

| Variable | Value | Read by |
|---|---|---|
| `PQT_ENV` | the environment root | this package's scripts |
| `PQT_SRC` | the caller's research-tree path | `property/*.py`, `property/run_all.sh`, `math/math_layer.py`, `fault/fault_injection.py`, `independent-b0/gen_b0_vectors.py`, `fixes/make_fixes.py` |
| `PATH` | `$PQT_ENV/tools/bin` first | `tamarin-prover`, `maude`, `proverif`, `dot` |
| `MAUDE_LIB` | `$PQT_ENV/tools/maude-3.5.1` | Maude: its prelude and library files |
| `OQS_INSTALL_PATH` | `$PQT_ENV/liboqs` | `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` (real-signature demo) and the `oqs` Python module |
| `LD_LIBRARY_PATH` | `$PQT_ENV/liboqs/lib` prepended | the loader, for `liboqs.so.9` |
| `PKG_CONFIG_PATH` | `$PQT_ENV/liboqs/lib/pkgconfig` prepended | anything that probes liboqs through `pkg-config` |
| `PYTHONDONTWRITEBYTECODE` | `1` | keeps `__pycache__` out of the research tree, which is read-only |

## 4. Step 1 — the pinned Python environment (host profile)

```sh
cd tooling
python3 -m venv venv
. venv/bin/activate
pip install --only-binary :all: \
  sympy==1.13.1 mpmath==1.3.0 galois==0.4.11 numpy==2.4.6 \
  numba==0.65.1 llvmlite==0.47.0 hypothesis==6.151.9 pytest==9.0.2 \
  hsslms==0.1.3 dilithium-py==1.4.0 kyber-py==1.2.0 dnspython==2.8.0 \
  cryptography==46.0.0 cffi==2.0.0 liboqs-python==0.16.0
pip install --no-deps pqcrypto==0.3.4
```

The versions above are the pins the host-side results were produced with. The last two lines deserve
a note each:

- `pqcrypto` 0.3.4 is installed with `--no-deps` because its only dependency, `cffi`, is installed
  explicitly above; the original environment installed it from a wheel bundled in the research tree
  (`continuation_v1.29/dependencies/pqcrypto-0.3.4-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`,
  27,036,304 bytes). The bundled wheel is **not** redistributed in this repository; its recorded
  SHA-256 is `b2f9bad43a1e3970f55e6f68fc1864595c9b0c6e53638aa8393b1d01216a6ebb`, which was checked to
  be the PyPI release file. Verify whichever copy you install:

  ```sh
  python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" \
      <path-to>/pqcrypto-0.3.4-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
  ```

- `pytest` is a dependency of the property-test runner (`domains/11-independent-audit-stack/property/run_all.sh`
  invokes `python3 -m pytest`) but is not imported by any scanned source file; `numba` is the
  compiled backend `galois` uses; `cffi` is the ABI layer `pqcrypto` is built on.

### Package table, with where each pin comes from

| Package | Pinned | Why this version |
|---|---:|---|
| sympy | 1.13.1 | the exact-arithmetic engine of the host mathematics run; `math/math_results.json` `_meta.engines` records it, and the ledgers write "SymPy 1.13" |
| mpmath | 1.3.0 | SymPy dependency, host install |
| galois | 0.4.11 | recorded in the audit-stack documentation, `math_results.json`, and both container files |
| numpy | 2.4.6 | `math_results.json` `_meta.engines` (host run) |
| numba | 0.65.1 | **no host version is recorded in any ledger**; taken from the host user-site install that `galois` used. The container pin is 0.61.2 (see §5) |
| llvmlite | 0.47.0 | numba 0.65.1 dependency, host install |
| hypothesis | 6.151.9 | the ledgers record "Hypothesis 6.151"; the patch level comes from the host install. The never-built full container file names 6.168.0 |
| pytest | 9.0.2 | **not recorded anywhere**; host install |
| hsslms | 0.1.3 | recorded in the infrastructure audit documents |
| dilithium-py | 1.4.0 | recorded in the audit-stack documentation |
| kyber-py | 1.2.0 | recorded in the audit-stack documentation |
| dnspython | 2.8.0 | recorded in the DNSSEC study's own docstring and in the container file |
| cryptography | 46.0.0 | recorded in the authorization experiment's runtime evidence; the host user-site install carries 46.0.6 |
| cffi | 2.0.0 | **not recorded** beyond "cffi is required"; host install |
| pqcrypto | 0.3.4 | recorded in the authorization experiment; the wheel's SHA-256 is checked against PyPI |
| liboqs-python | 0.16.0 | recorded in the B0 finalization document, matching the liboqs build of §6 |
| dependencies pulled by pip | mpmath 1.3.0, typing_extensions 4.16.0, iniconfig 2.3.0, pluggy 1.6.0, packaging 26.3, pycparser 3.0, Pygments 2.21.0, sortedcontainers 2.4.0 | resolved automatically |

Three pins — numba, pytest, cffi — are marked above because the record does not name a version for
them. They are the versions of the host installs that produced the recorded results, not versions
any document asserts. Install something else and you have changed an untested input.

Every wheel is binary (`--only-binary :all:`); nothing needs compiling from source, and no
compiler is required for this step.

Not installed, deliberately: `scipy` (listed in the never-built container file, imported by no
source file) and SageMath / passagemath (see §8).

## 5. Step 2 — the container mathematics profile

The mathematics layer also has a container file, `tooling/audit-stack/Dockerfile.math`, whose run
log records specific versions. A second virtual environment reproduces those pins on the host:

```sh
cd tooling
python3 -m venv venv-math-container
. venv-math-container/bin/activate
pip install --only-binary :all: sympy==1.14.0 galois==0.4.11 numba==0.61.2 numpy==2.2.6
```

That yields sympy 1.14.0, galois 0.4.11, numba 0.61.2, llvmlite 0.44.0, numpy 2.2.6, mpmath 1.3.0.
The container base was `python:3.12-slim`; this environment uses the host's Python 3.12.3.

The two profiles differ on purpose. Where a result depends on the difference — for example a
mathematics answer that only reproduces under the container pins — the domain documents say so.
Verify either profile with the same commands as §9.

## 6. Step 3 — liboqs 0.16.0

The certificate layer calls real post-quantum implementations through liboqs. The build recorded
here is a full build (all algorithms), shared library, installed into `tooling/liboqs`:

```sh
cd tooling
git clone --depth 1 --branch 0.16.0 https://github.com/open-quantum-safe/liboqs src/liboqs
cmake -S src/liboqs -B src/liboqs/build -GNinja -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON -DOQS_DIST_BUILD=ON \
      -DCMAKE_INSTALL_PREFIX="$PWD/liboqs"
cmake --build src/liboqs/build
cmake --install src/liboqs/build
```

- **Version:** 0.16.0, tag `0.16.0`, commit `5a1a854b0dc9f2141bdc771c555ee60c37950183` — the commit
  recorded in the B0 finalization document and in the audit-stack primitives results.
- **Build time:** 2 min 54 s wall on 12 cores (recorded).
- **Result:** `liboqs/lib/liboqs.so` → `liboqs.so.9` → `liboqs.so.0.16.0`, headers under
  `liboqs/include/oqs`, `pkg-config` file under `liboqs/lib/pkgconfig`.
- **SHA-256 of `liboqs.so.0.16.0`:** `710d951bd840b02b8a35cd671185c269432eec0fdc2605ddeed3e565871d0311`.
  Check your build against it:

  ```sh
  sha256sum tooling/liboqs/lib/liboqs.so.0.16.0
  ```

  A different compiler, a different OpenSSL, or a different CPU-feature target will change this
  digest while leaving the library correct. The digest identifies the build the recorded
  measurements were taken on; it is not a correctness test.
- **Linked against:** system OpenSSL 3.0.13 (`libcrypto.so.3`), which is the `OQS_USE_OPENSSL=ON`
  default, with `OQS_OPT_TARGET=auto`.
- **Enabled:** all 221 signature and all 41 KEM identifiers offered by 0.16.0, including ML-DSA-44/65/87,
  ML-KEM-512/768/1024, the OV and SNOVA families, MAYO, Falcon, SLH-DSA, and the conservative
  candidates. Stateful hash-based signatures (XMSS/LMS) are off, as in the default; no script here
  uses them. The complete enabled list is printed by the liboqs smoke check in §9.

How the scripts find it:

| Caller | Mechanism |
|---|---|
| `domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` (real-signature demo) | `OQS_INSTALL_PATH`; it tries `lib/liboqs.so` then `lib64/`, loads it with `ctypes`, then imports the `oqs` module. Without the variable it falls back to `pqcrypto` only |
| `domains/11-independent-audit-stack/primitives/oqs_ctypes.py` | a **hard-coded relative default**, two directories above the stack — `primitives/../..` — then `tools/liboqs-0.16.0/build/lib/liboqs.so`; the `LibOQS(path)` constructor overrides it, but `cross_validate.py` calls `LibOQS()` with no argument, so it uses the default. **In this repository that resolves to `domains/tools/liboqs-0.16.0/`, not to `tooling/tools/`** — see the compatibility note below |
| every other script | no liboqs: it uses `pqcrypto`, `dilithium-py`, `kyber-py`, or the standard library only |

**The compatibility directory the primitives layer needs.** The build above installs into
`tooling/liboqs`, and `OQS_INSTALL_PATH` is what the certificate demo reads. The audit stack's
primitives layer does not read that variable: it computes `primitives/../..` and looks for
`tools/liboqs-0.16.0/build/lib/liboqs.so` and, for the recorded liboqs commit,
`tools/liboqs-0.16.0/COMMIT.txt`. In the layout of this repository `primitives/../..` is the
`domains/` directory, so those two files must appear under `domains/tools/liboqs-0.16.0/`. Create
them once, from the repository root, after the build:

```sh
mkdir -p tooling/tools/liboqs-0.16.0/build
ln -s ../../../src/liboqs/build/lib tooling/tools/liboqs-0.16.0/build/lib
printf '%s\n' '5a1a854b0dc9f2141bdc771c555ee60c37950183 tag 0.16.0' \
      > tooling/tools/liboqs-0.16.0/COMMIT.txt
ln -s ../tooling/tools domains/tools
```

The last line makes the whole `tools/` directory — the liboqs build tree and the four formal tools
placed in §7 — visible at `domains/tools`, which is the single point the primitives layer looks at.
`COMMIT.txt` is a one-line compatibility file, not part of liboqs: it carries the commit the
recorded primitives results cite. Nothing else in the tree needs it, and without either file the
primitives layer raises `FileNotFoundError`/`OSError` when it loads the library, with the commit
field recorded as `unknown` if only the library is present.

## 7. Step 4 — the formal tools

| Tool | Version | Obtained from | SHA-256 | Notes |
|---|---|---|---|---|
| Tamarin prover | 1.12.0 | `github.com/tamarin-prover/tamarin-prover` release 1.12.0, asset `tamarin-prover-1.12.0-linux64-ubuntu.tar.gz` | tarball `201be06f469e47cff554df6ca93db8366fc2c69d70c61fcbd1370a1074b469c6`; binary `9d3fcbaa65aeea244cff5b8074338d129427161cc8b02e5aee72d30ee072acc9` | self-test passes 55/55 (§9) |
| Maude | 3.5.1 | `github.com/maude-lang/Maude` release `Maude3.5.1`, asset `Maude-3.5.1-linux-x86_64.zip` | zip `72ed1ca87e3b3d0dfc6ee1436baf154bf04c45ff97d521bec040c5e8dfc8f92c`; binary `9dd4044e693944aae97ad72086bc70275fa34bf635f9b377a5b2100bf3ed8655` | requires `MAUDE_LIB`; 3.5.1 is the newest version Tamarin 1.12 accepts |
| GraphViz `dot` | 2.43.0 (Ubuntu package 2.42.2-9ubuntu0.1) | Ubuntu noble `.deb` files fetched with `apt-get download`, extracted with `dpkg -x` | see the recorded package hash list | a small launcher script in `tools/bin` sets `LD_LIBRARY_PATH` and `GVBINDIR` |
| ProVerif | 2.05 | `https://proverif.inria.fr/proverif2.05.tar.gz` (SHA-256 `4871f53c32ab4a04669a060c4886ba5d9080496963fb980a9a62d2c429ceabc4`), built with `./build -nointeract` against OCaml 4.14.1 | binary `68a09c71d9c35e832bb6a8aa62cf4b360ca492db122445ccafc459355c8519dc` | no distribution package exists for ProVerif; the OCaml toolchain was extracted from Ubuntu `.deb` files into build scratch and was not kept |

Place the four executables (or launchers) in `tooling/tools/bin/`, so that `activate.sh` puts them on
`PATH`, with the tool trees beside them under `tooling/tools/`. `MAUDE_LIB` must point at the Maude
distribution directory, not at the binary.

The GraphViz launcher exists only because `tamarin-prover test` performs a tool-availability check
that fails without `dot`; the 55 unification cases pass with or without it. Tamarin otherwise runs
headless.

`domains/11-independent-audit-stack/run_all.sh` treats an absent prover as **NOT RUN**, never as a
pass, and prints exactly which tool was missing.

## 8. What could not be reproduced here

These are recorded in the theory and package index as tools the programme depended on or planned to
use, but which were **not** run in this environment. Each is listed with the reason, so that no
reader mistakes a plan for a result.

| Not available | Why, and what that costs |
|---|---|
| SageMath / passagemath | not installed, not attempted. The mathematics layer has no Sage code path at all — `math/math_layer.py` hard-codes `'sage': 'not installed'` — so installing it would change nothing. References to SageMath in earlier artifacts are requirements, not results |
| EasyCrypt | not installed. `domains/11-independent-audit-stack/formal/frame_b0.ec` is a proof skeleton that is `admit`ted on purpose; it was never checked, and the file records that |
| TLA+ / TLC / TLAPS | the `tla2tools.jar` distribution is absent, and a Java runtime was never pinned for it. The TLA+ specification `domains/01-accountable-quorum-foundations/formal/epoch-barrier.tla` therefore has no executed state; the invariants it states were checked by an independent enumeration script, not by TLC |
| KLEE | not installed |
| AFL++ | not installed |
| valgrind | not installed; the leak checks that were run came from AddressSanitizer/LeakSanitizer under clang instead |
| opam | not installed; ProVerif was built directly from source with `./build -nointeract` |
| Docker | not used for any recorded run. `tooling/audit-stack/Dockerfile` (the full stack image) was **never built or tested**, and its own header says so; `tooling/audit-stack/Dockerfile.math` was built once and its run log records 8/8 reproduced. Container-reproducibility claims for the rest of the stack are therefore untested |
| NIST ACVP vector files | the five `internalProjection.json` conformance-vector files used by the primitives cross-check are **not** in this repository; only `primitives/vectors/SOURCE.txt`, which records the upstream commit and the file digests, is shipped. The cross-check reports NOT RUN without them |
| CryptoMiniSat | not run; there is no recorded version. The SAT-slope experiments it supported are reported as summaries, not reproducible runs |
| Binius64 adapter binaries | the four compiled adapters whose sizes the proof-carrier experiments record contain AVX-512 instructions and were never executed on a host without `avx512f`. Rebuilding them changes their digests, so the recorded sizes cannot be re-derived byte-for-byte here |
| GMP development headers | absent, which is why one earlier succinct-backend build stopped |
| clang sanitizers and libFuzzer | clang 18.1.8 is present on the recorded host and the sanitizer and fuzzing scripts are shipped, but they were **not** re-executed during the verification pass, and at production parameters one run timed out. Treat those results as recorded, not re-run |
| A Java runtime for TLC | never pinned |

**The two container files, and what to check if you edit one.** `tooling/audit-stack/Dockerfile`
builds the whole stack; it was never built, and its own header says so — treat anything that depends
on it as untested. `tooling/audit-stack/Dockerfile.math` builds the mathematics layer; it was built
and run, and the log kept beside the domain's results records all eight groups reproduced under the
container pins.

Nothing in either file needs editing before a build. `Dockerfile.math`'s example `docker run` line
mounts the read-only research tree at the neutral path `/src` and passes that location in `PQT_SRC`:

```sh
docker run --rm -v /path/to/PQT:/src:ro -e PQT_SRC=/src -v "$PWD/math:/audit/math" qpt128-math:0.1
```

Substitute your own tree's location for `/path/to/PQT` and mount it wherever you like; what the
layer reads is `PQT_SRC`, and it raises `SystemExit` with one line naming the variable if it is
unset, so a missing value fails immediately instead of reading a stale path. (The line was not
always neutral: as first placed it carried an absolute path from the machine that recorded the run,
and the scanner did not read `.math` files at that time, so it was found by inspection and reported
to the file's owner rather than by the tree's own gate. The owner has redacted it, and `.math` is
now in the scanner's text set — `VERIFICATION.md` §4.4 records both halves.)

Both files were placed in this directory by the package that owns them, and they are the only files
under `tooling/` that this package does not describe from the inside. The forbidden-string scanner
described in `VERIFICATION.md` reads files by suffix: when this paragraph was first written the
`.math` suffix was not in its set, so `Dockerfile.math` was the one file under `tooling/` that no
gate opened. That gap was reported to the owner of the scanner and is closed — the suffix is in the
set now, and the file scans clean (`python3 tooling/checks/scan-forbidden.py tooling` reads twelve
files, that one among them, and reports 0 findings). `VERIFICATION.md` §4.4 records the observation.
The set is still the boundary, though: a file whose suffix is not in it — what you add yourself, for
instance — is a file no gate opens, so read it by eye.

## 9. Checking the build

Source `activate.sh` first — that is what puts the four tools on `PATH` and sets the liboqs
variables — then run these. They are the shipped equivalents of the checks that were re-run for
`VERIFICATION.md`, and `VERIFICATION.md` records the exact output each one produced there.

```sh
# 1. the pinned interpreter imports every distribution, and the symbols the sources use resolve
python3 -c "import cryptography, dilithium_py.ml_dsa, dns, galois, hsslms, hypothesis, \
kyber_py.ml_kem, numpy, oqs, pqcrypto.sign, pqcrypto.kem, sympy; print('imports OK')"

# 2. liboqs through the project's own ctypes wrapper: ML-DSA-87 sign/verify, ML-KEM-1024 round trip
python3 domains/11-independent-audit-stack/primitives/oqs_ctypes.py   # needs the §6 compat directory

# 3. the field library, and with it the whole mathematics layer (eight groups; about 217 s)
python3 domains/11-independent-audit-stack/math/math_layer.py

# 4. Tamarin self-test (needs dot, maude and tamarin-prover on PATH)
tamarin-prover test

# 5. ProVerif, against a distribution example with a published expected result
proverif tooling/tools/proverif-2.05/examples/pitype/secr-auth/NeedhamSchroederPK-corr.pv
```

The path in check 5 is where §7 places the ProVerif tree — the tarball is named `proverif2.05`, and
the directory it extracts to is spelled `proverif-2.05`. The third check subsumes the GF(2^8) smoke check the environment build used — an
exhaustive 65,536-product sweep against an independent shift-and-add reference, recorded in
`VERIFICATION.md` — which was a one-off script belonging to the environment build rather than to the
research record, and is therefore not shipped here.

Quick checks of the individual tools, which need no environment at all except where noted:

```sh
python3 -V                        # expect: Python 3.12.3
tamarin-prover --version          # expect: tamarin-prover 1.12.0
maude --version < /dev/null       # expect: 3.5.1  (without the redirect Maude opens a REPL and waits)
proverif -h | head -2             # expect: Proverif 2.05
dot -V                            # expect: graphviz version 2.43.0
sha256sum tooling/liboqs/lib/liboqs.so.0.16.0
```

`import oqs` is deliberately **not** on that list as a bare check: liboqs-python will clone and
build its own copy of the library when it finds none, which is slow and needs the network. It must
be run with the environment sourced (`OQS_INSTALL_PATH`, `LD_LIBRARY_PATH`), where it prints
`0.16.0 0.16.0` in a moment.

## 10. Provenance of the version numbers

Every version in this document was read from the live environment, not from a ledger, at the time of
writing. Where a ledger records a different string for the same tool — for example "SymPy 1.13"
against the installed 1.13.1, or "Hypothesis 6.151" against 6.151.9 — the ledger's wording is kept in
the domain documents and the installed patch level is recorded here. `VERIFICATION.md` lists each
package with the command that observed it.
