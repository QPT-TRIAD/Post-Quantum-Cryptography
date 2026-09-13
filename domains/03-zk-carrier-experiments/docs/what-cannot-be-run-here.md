# What a reader cannot re-run in this repository, and why

This page is the plain statement required of every domain: which parts of this domain's evidence a
reader can reproduce from the repository alone, and which parts need material that is deliberately
absent. Nothing here is a limitation of the experiments; it is a limitation of what was copied.

## 1. The three missing capabilities

Every item in `VERIFICATION.md` marked `not-run` is missing exactly one or more of these.

| Capability | Present here? | Why not |
|---|---|---|
| The **pinned** Rust toolchain (Rust 1.97.1) | **no** | the environment this repository was assembled in carries rustc 1.96.0, not the pinned 1.97.1; the pinned version was never bundled by any version of the experiment either |
| Vendored proof backend `continuation_v1.17/binius64-source` (767 files, ≈8.6 MB) | **no** | third-party source; excluded from the file map and from the research tree this repository was copied from, so the adapters' relative path dependencies do not resolve here. Obtainable from upstream at pinned commit `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4` |
| Compiled adapter executables (four of them, 5.5–5.7 MB each) | **no** | build products; excluded. Rebuild from the adapter sources in this repository |
| `pqcrypto` 0.3.4 wheel (27,036,304 B) | **no** | excluded 27 MB binary; the pinned digest is recorded in `results/dependency-provenance.json` |
| Python 3.12 with `cffi`, `cryptography`, and the pinned environment | **yes** | the checkers, auditors and the authorization suite all run |

Consequently: **no proof was generated, no binary was rebuilt, and no native proof was verified for
this repository.** Every frame size and every `native_verified: true` in `results/` and `history/` is a
record made by the experiment that produced it, audited here against its own files, and never
presented as a measurement taken now.

## 2. What each binary-dependent script does here

Run in the pinned Python environment with no binary present and no `CEQS_BINARY` set. The messages
below were observed; they are quoted exactly.

| Script | Invocation that reaches the guard | Observed |
|---|---|---|
| `src/verify_public.py` | `python3 src/verify_public.py --config fixtures/config.json --frame fixtures/case0/trace43_rate3.pf2p` | exit 1, `native carrier binary not present: …/src/bin/ceqs-polycarrier-v128` followed by the note that the compiled adapter is not part of this repository and a pointer to `docs/provenance.md` |
| `src/check_public_mutations.py` | `python3 src/check_public_mutations.py` | exit 1, same message for the same binary |
| `src/run_native.py` | `python3 src/run_native.py prove_case0 prove_native case0` | exit 1, same message; the script requires three positional arguments — a label, a mode and a case |
| `src/regenerate.py` | `python3 src/regenerate.py --output NEW_DIRECTORY` | exit 1, `native paired-trace binary not present: …/src/bin/ceqs-fixed-pair-v127b` plus the rebuild instruction |
| `history/v1.27/verify_public.py`, `history/v1.27b/verify_public.py`, `history/v1.28/verify_public.py` | e.g. `PYTHONPATH=src python3 history/v1.27b/verify_public.py --config fixtures/config.json --frame fixtures/case0/trace43_rate3.pf27 --output OUT.json` | exit 1 with `FileNotFoundError: [Errno 2] No such file or directory: '…/bin/ceqs-fixed-pair-v127b'` |
| `history/v1.27/run_native.py`, `history/v1.28/run_native.py`, and the historical mutation checkers | same shape | same `FileNotFoundError` for their own binary name |

Two details worth knowing before blaming the repository:

- The **historical** scripts under `history/` were kept byte-identical, so they have no guard: they
  attempt the subprocess and fail with `FileNotFoundError`. Their sibling `paired_reference.py` is
  imported by module name, so they must be run with `src/` on `PYTHONPATH` (or with a copy of
  `paired_reference.py` beside them, which is what `src/regenerate.py` arranges). This is how the
  package was built, not damage from copying.
- The **current** scripts under `src/` carry an explicit guard that names the missing executable, the
  reason, and the rebuild path. That guard is an addition made for this repository; the recorded
  results were produced by the historical scripts.

`src/verify_public.py` additionally checks the frame's generation before anything else: presented with
a `PF27` frame it exits with `ValueError: wrong format or incomplete quorum`, because it accepts only
`PF2P` (QVT3). To parse an older generation, use that generation's own script under `history/`.

## 3. What *does* run, and what it establishes

| What | How | What it establishes |
|---|---|---|
| Fixture generation | `python3 src/make_fixture.py` (honours `CEQS_FIXTURES`) | the 15-check reference suite: honest 43-seat relation at both cases, other-seat role substitutions, mixed link/mask rejection, the 22 expected conflict identities, changed domain/message/configuration rejection, 64 rotating quorums, 384 independent field vectors, and the zero-message observation |
| Field-modulus certificate | part of the evidence audit | the Rabin certificate for `X^512 + X^8 + X^5 + X^2 + 1`: `X^(2^512) = X`, `gcd(X^(2^256) − X, f) = 1`, 2 the only prime divisor of 512 |
| Evidence audit | `python3 src/audit_results.py` | re-derives the per-version size accounting over all four frame generations and re-checks the field certificate; reproduces `results/evidence-audit.json` byte-for-byte |
| Carrier audit | `python3 src/audit_carriers.py` | re-reads the four retained current-generation frames, their extended native digests and their negative-control records; reproduces `results/carrier-audit.json` byte-for-byte |
| Compression and span measurements | `python3 src/analyze_existing_carriers.py` | re-measures DEFLATE/bzip2/XZ on the retained frames and the binary span ranks per section; reproduces `results/existing-carrier-results.json` byte-for-byte (about one second on this host) |
| Authorization suite | `python3 src/test_authorization.py` | the 51 checks of the v1.29 component with freshly generated synthetic keys, using the `pqcrypto` package already installed in the pinned environment |
| Transparency audit | `python3 src/verify_audit.py` | replays 86 recorded ML-DSA approvals from public keys, bodies and signatures alone |
| Seeded-data demonstration | `python3 src/seed_carrier_demo.py` | rebuilds the five 588-byte carriers from fresh randomness, decodes each of them back, and re-checks truncation, trailing bytes and altered-seed rejection. **Note:** it *writes* `fixtures/seed-demo/*.scd` and `results/seed-carrier-results.json`, so running it in place replaces the retained carriers with new ones of the same size and shape; the retained carriers' digests are recorded in `results/carrier-audit.json` |
| Packaging integrity | `python3 src/package_update.py --previous ARCHIVE --output OUT.zip` | only with a recorded archive supplied by the reader; the prior archive is not in this repository |
| Everything at once | `sh src/reproduce.sh` | installs/checks the dependency, runs the transparency audit, runs the 51 checks, and writes `results/replay-evidence/` |

None of the above proves anything about the native proof backend. They establish that the *records*
are internally consistent, that the relations' reference equations hold, and that the retained frames
have the structure and size the records claim.

## 4. What would be needed to attack the missing part

In the order a reader would need them, for the current generation (v1.28p / QVT3):

1. Fetch the backend at commit `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4`.
2. Apply `src/prover_memory.patch` (sha256 in `docs/provenance.md`).
3. `cargo build --locked --release --manifest-path src/adapter/Cargo.toml` with Rust 1.97.1, and place
   the resulting executable where `CEQS_BINARY` points (default `src/bin/ceqs-polycarrier-v128`).
4. `python3 src/verify_public.py --config fixtures/config.json --frame fixtures/case0/trace43_rate3.pf2p --frame fixtures/case1/trace43_rate3.pf2p --output OUT.json`
   to attempt the public re-verification that produced `results/public-verification.json`, and
   `python3 src/check_public_mutations.py` for the 22 negative controls.
5. To regenerate rather than re-verify, build the v1.27b adapter instead and run
   `python3 src/regenerate.py --output NEW_DIRECTORY`. Expect *different* frame bytes: fresh
   credentials and fresh proving randomness change every frame hash. The retained comparison record
   `results/regeneration-validation.json` shows exactly that, with frames of 285,136 and 283,184
   bytes where the shipped pair is 283,680 and 279,600.

If a re-run of step 4 produces a different verdict from `results/public-verification.json`, the
programme's own rule applies: the recorded number is withdrawn in public with the reason. This
repository does not claim otherwise on its behalf.
