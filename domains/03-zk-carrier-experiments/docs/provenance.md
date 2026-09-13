# Provenance: the upstream backend, the local modifications, and everything excluded

This page is the record of what this domain *does not contain* and where a reader must go to get it.
It exists because the experiments here cannot be re-run from this repository alone: they need a
third-party proof backend that is not redistributed here, four compiled adapter binaries, and one
Python wheel. Nothing below was re-executed for this repository; every number is either a digest of a
file that is in the source tree, a digest recorded by the experiment that produced it, or an
instruction reproduced from the retained reports.

## 1. The upstream proof backend

The relations in this domain are all proved with the same Rust backend.

| Field | Value |
|---|---|
| Project | Binius64 — a ZK succinct argument system over 64-bit words, with a Spartan ZK wrapper and BaseFold machinery |
| Upstream | `https://github.com/binius-zk/binius64` |
| Pinned commit | `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4` |
| Local copy in the research tree | `continuation_v1.17/binius64-source` — 767 files, ≈8.6 MB |
| Status in this repository | **excluded** (third-party source; the file map marks all 767 files `exclude-vendored`) |
| Security parameter of the pinned source | `crates/verifier/src/verify.rs` sets `SECURITY_BITS = 96` |
| Hash suite of the pinned source | SHA-256 Merkle commitments, internal `Ghash128b` arithmetic |

The pinned commit is what the experiments used. `docs/analysis-note.md` and
`history/v1.25/assessment.md` §9 both record that no unrecorded upgrade to the current upstream
repository was taken.

## 2. The local modifications

Six files under `crates/prover/` were modified for the v1.17 prover-memory work. The constraint
system, trace circuit, field arithmetic, verifier crates, Fiat–Shamir schedule, security setting and
codec are unchanged (`docs/method.md`). `results/source-comparison.json` records that all other
tracked upstream files, all verifier sources, the trace circuit and the codec are byte-identical to
upstream.

| Modified file (path within the backend) | sha256 |
|---|---|
| `crates/prover/src/protocols/intmul/mod.rs` | `92a3b171fed7ad0650d0db23794039cbb1d481dc1cd9e7d104e59ec569b7d625` |
| `crates/prover/src/protocols/intmul/prove.rs` | `da77e46bcc422cde97c45ac350bf00dc483dbd9fbd674f6e39e5a5dd36348086` |
| `crates/prover/src/protocols/intmul/recompute.rs` | `0f9470fa1e3f625b23a2cec31621edb61f558648d1941c9122a3d153e596b06f` |
| `crates/prover/src/protocols/intmul/witness.rs` | `1e13fb31ac65071cee2c70cad24d99d5a1df38dddb59bf5fbc958c45c59dff9b` |
| `crates/prover/src/prove.rs` | `322d24ec24689fabf9cab3c538e283fb4d74ccfbf3e351a507853150af4bb66d` |
| `crates/prover/src/zk_config.rs` | `89b7652a7e5165b7cda04a743236db5d7d95d1482298c22e53147201076bf817` |

`crates/prover/src/protocols/intmul/recompute.rs` is a new file, not a modified one.

The modification set is distributed in this repository as the patch `src/prover_memory.patch`:

| Field | Value |
|---|---|
| Patch | `src/prover_memory.patch` |
| sha256 | `b916606810a4b8416baddadfac531302eec91935a73b1528a201a4a189a4b563` |
| Applies to | the pinned commit above |
| Content, in one line | one layer generated when required and released before the next; leaf columns evaluated directly from their compact inputs; fixed-base trees' roots computed first and other layers reconstructed just before phase 4; the existing `GlobalAllocator` used instead of the reusable buffer pool in this ZK path; shift-key tables built lazily behind a `OnceLock`; the duplicate inner verifier constructed only when replay needs it |

What the patch is *not*: `docs/method.md` states in its own words that this is "a construction
argument for an equivalent prover, supported by differential tests and native verification. It is
not a machine-checked equivalence theorem, an independent audit of Binius, or a new QPT security
theorem." The equivalence identity used is `T_{k-1}(j) = T_k(j)·T_k(j+2^{k-1})` for the product-tree
layers, which reorders finite-field multiplications without changing any field element or encoding.

`docs/method.md` also records a correction: the first v1.17 runner selected the *original* v1.16
executable, so its memory failures are baseline reruns and say nothing about the patched prover.
Later `patched_*` records carry the executable's path and SHA-256; the differential multiplication
tests invoked their patched diagnostic directly and were unaffected.

## 3. Rebuilding the adapters

A compatible Rust toolchain is required. The workspace build used **Rust 1.97.1** with its existing
offline dependency cache; the Cargo dependencies and the toolchain are not bundled anywhere, here or
in the recorded packages.

```bash
cargo build --locked --release --manifest-path history/v1.27b/adapter/Cargo.toml
```

The adapter manifests keep their relative path dependencies into the excluded backend tree, for
example `binius-*` entries pointing at `continuation_v1.17/binius64-source/crates/...`. Each of the
four `Cargo.toml` files in this repository (`src/adapter/`, `history/v1.27/adapter/`,
`history/v1.27b/adapter/`, `history/v1.28/adapter/`) carries a header comment stating that this
target is outside the repository, naming the upstream URL and commit, giving the patch path and its
sha256, and pointing back to this page. The dependencies were **kept**, not deleted, so that a reader
who obtains the pinned upstream tree can reproduce the original layout. `Cargo.lock` files are kept
as they were; their "generated by Cargo" line is a documented false positive of the identifier scan,
not a modification claim.

Each version's report gives its own build command and output name. The v1.25 report
(`history/v1.25/assessment.md` §8) additionally records `RUSTFLAGS='-C target-cpu=native'` and the
producer name `ceqs-direct-proof-v125`; the shipped binaries were built for an x86-64 Linux host with
`target-cpu=native`, so another host may require rebuilding. Rebuilding changes the binary digest, and
fresh proof randomness changes every frame hash: the retained hash evidence refers specifically to the
shipped experiment, and the regeneration record shows exactly this, with fresh frames of 285,136 and
283,184 bytes where the retained ones are 283,680 and 279,600.

## 4. The excluded compiled binaries

Four compiled adapter executables are **not** in this repository. Each is a build product of the
adapter sources that *are* here (or of the pinned backend plus those sources), and each can be
rebuilt with the command in §3. The digests are the ones recorded by the experiments that ran them.

| Version | Path in the research tree | Bytes | sha256 |
|---|---|---:|---|
| v1.27 | `continuation_v1.27/bin/ceqs-paired-trace-v127` | 5,533,208 | `3a74de19ad48f50a659f9611f49ad2f95c1399579ecf54d826b4931eb1c9300a` |
| v1.27b | `continuation_v1.27b/bin/ceqs-fixed-pair-v127b` | 5,531,152 | `dfa90585c22c692a66b6bc9ab689ec1c44e68cb7b128e9bd883ce265930975c5` |
| v1.28 | `continuation_v1.28/bin/ceqs-carrier-v128` | 5,699,400 | `8db8a47e5b3606b9fd0c52d14882b578dc9044627c9dbcb2ecb7aa836cbd1c6d` |
| v1.28p | `continuation_v1.28p/bin/ceqs-polycarrier-v128` | 5,721,256 | `77f4c11c4521729557f09fd3e8a5a09a3d73a54d82ef762fe7ded392416b181e` |

The v1.27b digest is the one that appears as `binary_sha256` in `history/v1.27b/public_verification.json`
and in the regeneration record; the v1.28p digest is the one in `results/public-verification.json`.
The v1.27 digest is reported by `history/v1.27/public_verification.json`.

The **v1.25** producer/verifier binary is a further case: `history/v1.25/assessment.md` §6 records its
sha256 as `5a212125c67105e66bde6b59232fceba6402f9535bf8df3f3e490d7cdf38367b`, but that executable is
not present in the research tree at all — no file map row for it exists, and `continuation_v1.25/bin/`
does not appear in the map. Only the v1.25 report and its three result records survive. The v1.25
adapter source is therefore also absent, and a v1.25 proof cannot be rebuilt from this repository.

## 5. Other excluded material

**Superseded frame binaries.** The file map excludes frames that are byte-distinct from the retained
ones in the same format. Their digests are recorded here because a rebuild will not reproduce them.

| Path in the research tree | Bytes | sha256 |
|---|---:|---|
| `continuation_v1.27/fixture/case0/trace43_rate3.proof` | 339,104 | `c13efd6f0d77fdfd46f15ee261f153fecabcddccb918ee3f44d61217d4da160c` |
| `continuation_v1.27/fixture/case1/trace43_rate3.proof` | 339,104 | `bee927fbe6dc43308d98aff49aff5af6ec9f3343b74e13e10ac454d3371fa0c8` |
| `regeneration_check/fixture/case0/trace43_rate3.pf27` | 285,136 | `0cce0aebfd57e71cd6689ad221aa4e1e314a274d6a86f333b9041842fcffeeff` |
| `regeneration_check/fixture/case0/trace43_rate3.proof` | 335,360 | `97f4eac0a1ec36a07e59a980c4138f125a9f759b72b258268a5d7695867843ee` |
| `regeneration_check/fixture/case1/trace43_rate3.pf27` | 283,184 | `77a812c417c39606d98ac50d840088e8255586b3b8cae94f19401180bf4d5cec` |
| `regeneration_check/fixture/case1/trace43_rate3.proof` | 335,360 | `6292dfdd3df4d03dcf190332f28f44c32150a184ae650522f897d4ebdb0209f4` |

The regeneration check's statements and configuration *are* retained
(`history/regeneration-check/fixture/`), and the record of what its frames verified is retained in
`results/regeneration-validation.json`; only the large frame bytes are absent. The two v1.27 native
`.proof` files are excluded for the same reason, while the retained v1.27b native proofs are present
at `fixtures/case0/trace43_rate3.proof` and `fixtures/case1/trace43_rate3.proof` (335,360 bytes each).

**Scratch directories.** Three `tmp*/config.json` files (17,384 bytes each) written by a build or
prover run are excluded as non-evidence. The current `src/check_public_mutations.py` no longer creates
such directories: the temporary-directory call no longer pins its parent to the run directory. This
is a change to the *current* script only and is recorded in `VERIFICATION.md` §4.

**The `pqcrypto` wheel.** The v1.29 authorization component uses `pqcrypto` 0.3.4, distributed as

```
pqcrypto-0.3.4-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl
sha256 b2f9bad43a1e3970f55e6f68fc1864595c9b0c6e53638aa8393b1d01216a6ebb
27,036,304 bytes
```

The wheel itself is excluded (27 MB of third-party binary). `results/dependency-provenance.json`
retains the publisher's release filename, URL and digests (`blake2b_256`, `md5`, `sha256`), the
upload timestamp, the local digest, and the flag `hash_matches_pypi: true`. `src/install_dependency.py`
checks whether `pqcrypto` is importable, reports where it was found, and otherwise exits with the
pinned name, sha256 and size and a pointer to this page; it installs only from a wheel the caller
supplies, verifying the digest first.

**The recorded packages.** The three review/carrier packages assembled during the programme are build
products and are not in this repository. Their packaging procedures are: `src/build_review_bundle.py`
(v1.27 review bundle), `src/package_carriers.py` (v1.28 carrier package) and `src/package_update.py`
(v1.29 update). Each takes the previous archive as a required `--previous` argument and states in its
docstring that the archive is not retained here, and each keeps its private-material guards: a
`PRIVATE_TRACE_WITNESS.bin` or an `.expanded` intermediate aborts the build rather than being written
into an archive. `results/package-validation.json` and `results/package-replay.json` record the
integrity and replay results of the recorded packages, including the prior-member digests.

## 6. What a reader needs, in one list

1. The pinned upstream tree at commit `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4`.
2. `src/prover_memory.patch` (sha256 above), applied to that tree.
3. Rust 1.97.1 and the Cargo dependencies from the retained lockfiles.
4. The adapter source for the version of interest, from `src/adapter/` or `history/*/adapter/`, built
   with `cargo build --locked --release`.
5. For the v1.29 authorization component only: `pqcrypto` 0.3.4 at the digest above, plus Python 3.12,
   `cffi` and `cryptography`.
6. Nothing else. The fixtures, statements, frames, native proofs of v1.27b, field vectors,
   configuration and every recorded result are in this repository.
