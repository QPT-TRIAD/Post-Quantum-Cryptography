# D3 — zk-carrier-experiments

Seven experiments, run between v1.17 and v1.29 of the CE-QS programme, that asked one question
repeatedly: **how much of a real zero-knowledge proof is information, and how much is redundancy a
decoder can regenerate?** The domain holds the relations those experiments proved, the adapters that
bound them to a real Rust proof backend, the frames that were actually produced, the negative
controls that were actually rejected, and the records of what failed.

The value of the domain is the measured answer. Every representation change here was applied to the
*same two native proofs* and re-verified by the same native verifier, so the byte differences between
frames are differences in representation only, not in what was proved. The complete quorum
certificate the programme was aiming for — one proof, all bytes inline, at most 32,768 bytes — was
**not** reached by any of them. The count of accepted complete original-goal certificates recorded in
this domain is **zero**, and that number is carried in every result file rather than only here.

*Read this file first.* It is the entry point. Everything else is reachable from the tables below.

> **Verification status, in brief.** Every pure-Python checker, auditor and fixture parser in this
> domain re-runs in the pinned environment and reproduces its recorded output byte-for-byte,
> including two independent audits of the retained evidence (`src/audit_results.py`,
> `src/audit_carriers.py`), the 15-check reference suite (`src/make_fixture.py`), the 51-check
> authorization suite (`src/test_authorization.py`) and the field-modulus certificate. **The native
> path does not re-run here:** the binary module format, key generation and proof verification all
> require the compiled adapter binaries, which are not in this repository, and the vendored proof
> backend is not in this repository either. Every item that touches them is `not-run` in
> `VERIFICATION.md`, with the missing capability named precisely. No proof size or verification
> result in this domain was re-measured; all are quoted from the retained records, and the records
> themselves are audited. One deliberate deviation from byte-identity is recorded in `VERIFICATION.md`
> §3: a working-directory prefix that named a local scratch path was removed from 21 string literals
> in 14 files, because the repository must not contain absolute local paths. No asserted fact,
> number or comparison changed.

---

## 1. The problem these experiments attack

The programme's object is a **compact, publicly verifiable, conflict-extractable post-quantum quorum
certificate**. A committee of `n = 64` seats holds `f = 21` faulty; a quorum is `q = 43`. Two
certificates for conflicting messages must let anyone recover at least `2q − n = 22` seats that
authorized both, using nothing but the two certificates and fixed public configuration. The contents
contract fixes the frame: a 208-byte header, `43 × 128` bytes of handles (5,504 B), and **one proof of
at most 27,056 bytes** — total 32,768 B. That number is a programme engineering decision, not a
cryptographic limit.

The experiments in this domain attack the last part of that contract, the **proof position**, in two
distinct ways:

1. **Shrink the relation.** v1.25, v1.27 and v1.27b each define a new 43-seat relation, prove it with
   the same Binius64 backend, and measure the resulting native circuit and frame.
2. **Shrink the representation.** v1.28 and v1.28p keep the relation of v1.27b and the *same two
   native proofs*, and replace parts of the inline transcript with algebraically reconstructed data:
   QVT2 reconstructs a final-layer coordinate from a known fold, QVT3 carries 512 polynomial
   coefficients instead of 832–816 sampled evaluations and their Merkle paths.

Around those, v1.17 attacks prover **memory** (the prover did not fit its runner), and v1.29 asks what
an *authorization* layer added on top would look like using real ML-DSA and ML-KEM.

Why it is hard, in the terms the experiments themselves established:

- The frame's fixed 5,712 bytes of header and handles are already spent before anything is proved, so
  the proof position is roughly 27 KiB for a proof of a 43-seat relation over a 512-bit binary field.
- The measured native proofs are 335,360–339,200 bytes, an order of magnitude over budget. Reducing
  the circuit by 55 % (v1.25 → v1.27b) moved the native proof by only 3,840 bytes: **the proof size
  is dominated by the backend's opening structure, not by the relation.**
- Interpolation helps only where the public data are already oversampled, and it can smuggle
  information out: transmitting full coefficients of an insufficiently sampled private oracle is not
  an approved substitution in this domain (v1.28 §5).

## 2. How to read this domain

| If you want… | Read |
|---|---|
| the experiment sequence and what each one measured | §3 and §6 below, then `docs/experiment-*.md` |
| the exact relation each version proves | `docs/experiment-02…` … `docs/experiment-06…`, or the version's own report under `history/` |
| which theory was borrowed, how much of it, and what was left unused | `docs/theory-as-used.md` |
| the upstream backend, its local modifications and the excluded binaries | `docs/provenance.md` |
| what cannot be re-run here and why | `docs/what-cannot-be-run-here.md`, then `VERIFICATION.md` |
| the recorded byte-level accounting | `results/evidence-audit.json`, `results/carrier-audit.json` |
| run what *can* run | §7 below |

Authored documents are `README.md`, `VERIFICATION.md` and the files under `docs/` listed in §5.
Everything under `results/`, `fixtures/`, `src/`, `history/` and the three retained documents
`docs/method.md`, `docs/analysis-note.md`, `docs/package-assessment.md` is a **source document or
source artifact**, copied from the research tree at the map's path. Line numbers cited in the authored
documents refer to those copies.

## 3. The experiments, in order

Every experiment below is recorded; the two right-hand columns say what it achieved against the
original goal and what it left open. "Native proof" means the proof bytes produced by the Binius64
backend before any codec; "frame" means the complete certificate-shaped object including the 5,712-byte
header-and-handles envelope.

| # | Version | Question it asked | Backend and relation | What it produced | Verdict |
|---|---|---|---|---|---|
| 1 | v1.17 | Can the prover fit its runner at all? | Binius64 `crates/prover`, six files patched | Layer recomputation, deferred fixed-base trees, lazy shift keys, delayed inner verifier; differential tests over 4 layer shapes and 6 transcript shapes | Memory work carried forward into every later adapter. No security change, `SECURITY_BITS` stays 96 |
| 2 | v1.25 | Can the v1.24 contents-first relation be proved and publicly verified? | Binius64 ZK prover, relation `CEQS124_DIRECT_CHALLENGE`, frame `DC25`, suite `0x2503` | Two real proofs of 43 seats; frames **289,664 / 287,712 B**; 7 Keccak permutations per seat; 14 negative controls | Relation executable and publicly verifiable. Failed the 32 KiB gate; no QPT-128; centralized prover |
| 3 | v1.27 (candidate A) | Can the relation be made smaller by fusing the link and mask derivations? | same backend, relation `CEQS127_PAIRED_TRACE`, frame `PT27`, suite `0x2703` | One 128-byte SHAKE output supplies both handle halves; 4 permutations per seat; frames **287,648 / 281,232 B** | Saved 2,016 / 6,480 B. Not a security-equivalent substitution for v1.25 without further analysis |
| 4 | v1.27b (candidate B) | Can the private witness and the hash circuits be simplified further without losing a credential check? | same backend, relation `CEQS12B_FIXED_CONTEXT`, frame `PF27`, suite `0x27b3` | Public context prehashed, fixed-width private hash inputs, 3 permutations per seat; frames **283,680 / 279,600 B**; 18 negative controls | The relation all later carriers carry. QPT-128, authorization and distributed generation all still open |
| 5 | v1.28 | Can a *decoder* replace transmitted redundancy on the real proofs? | same native proofs, codecs QVT2 and QVT3, frame `PF28`, suite `0x28b3` | QVT2 affine terminal reconstruction saves 1,664 / 1,632 B; QVT3 final-layer polynomial carrier saves 9,728 / 9,296 B against QVT1 | QVT2 and QVT3 both re-verify. Frame floor still ≫ 32 KiB |
| 6 | v1.28p | How far does the polynomial carrier go? | QVT3, frame `PF2P`, suite `0x28c3` | Frames **273,952 / 270,304 B**; 22 negative controls; final layer 8,192 B instead of 17,920 / 17,488 B | Best representation in the domain. 241,184 B over the proof budget in case 0 |
| 7 | v1.29 | What does real authorization look like above the tracing relation? | new suite `CEQS29-M87-K1024`, ML-DSA-87 + ML-KEM-1024 + AES-256-GCM | 86 real approvals, 86 transported envelopes, conflict algebra over *actual test signers*; 51 checks pass | Executable specification of approval binding. No succinct proof of it exists; zero complete QCs |

Two records in the domain are not experiments but controls on them: `history/regeneration-check/`
holds the fixture of a **fresh** end-to-end run of the v1.27b pipeline in a new directory
(frames 285,136 / 283,184 B — deliberately *not* equal to the retained frames, because fresh
credentials and fresh proving randomness change every byte), and `results/recompute-final-checks.json`
records the v1.17 differential diagnostic.

## 4. Backends carried and abandoned

| Backend or component | Status | Reason, as the sources state it |
|---|---|---|
| Binius64 ZK prover/verifier at pinned commit, with the v1.17 memory patch | **Carried** through v1.25, v1.27, v1.27b, v1.28, v1.28p | Only backend actually instantiated; produces real proofs that a public verifier accepts |
| QVT1 exact transcript codec (`DC25`, `PT27`, `PF27`) | **Carried**; still the fallback inside QVT2/QVT3 | Lossless reconstruction of the whole native transcript, verified by the ordinary native verifier |
| QVT2 affine terminal reconstruction | **Carried** into v1.28p as the fallback when the polynomial form is unavailable | Cheap, exact, no sampling assumption |
| QVT3 polynomial carrier | **Carried** as the current representation | Applied only to the final oracle, where the public sample count exceeds the degree bound |
| Seeded-data carrier (`seed_carrier_demo.py`) | **Not carried forward as a certificate component** | 588-byte carriers reconstruct 1,023 leaves, but the demo generates its data from seeds in the first place; it cannot compress an arbitrary existing proof, and the excluded leaf check is not a hiding proof |
| Generic compression (DEFLATE / bzip2 / XZ) | **Abandoned for this data** | Measured larger than the raw frame on both cases; every queried-field section had full binary span. Recorded as a measurement, not an entropy proof |
| ML-KEM + ML-DSA + HKDF + AES-GCM authorization and transport | **Kept as a component**, in v1.29 only | 86 real signatures verified and 86 envelopes transported; none of it is inside a succinct proof, so the certificate it belongs to does not exist yet |
| Aurora, AIM, HAETAE, Quorus, Han et al., Doerner–Kondi–Rosenbloom, WHIR, Khatam, HyperFond, BaseFold list-decoding | **Surveyed, not implemented** | Each is recorded in v1.28/v1.29 with the part that would be usable and the reason it does not transfer. No query or parameter was changed on the strength of an uninstantiated theorem |

## 5. The files

| Path | What it is |
|---|---|
| `README.md`, `VERIFICATION.md`, `docs/experiment-*.md`, `docs/theory-as-used.md`, `docs/provenance.md`, `docs/what-cannot-be-run-here.md` | authored for this repository |
| `docs/method.md` | v1.17 patch: what changed in the prover, why layer recomputation preserves the protocol, differential tests, memory accounting, and the correction to the initial retry records |
| `docs/analysis-note.md` | v1.26: the three remaining requirements and why the compact-threshold-signature replacement needs an additional theorem |
| `docs/package-assessment.md` | v1.29: the ML-KEM + ML-DSA authorization experiment, its relation, transport, gates and sources |
| `src/` | the current-generation experiment code: fixture generation, native driver, public verifier, negative controls, auditors, the v1.29 authorization suite and its transparency audit |
| `src/adapter/` | the Rust adapter for the current relation (v1.27b) and the QVT2/QVT3 codecs (`codec.rs`, `codec_v1.rs`), plus 384 field vectors |
| `src/prover_memory.patch` | the v1.17 patch against the pinned upstream commit |
| `fixtures/` | the retained 43-seat statements, the four frame formats for both cases, the two native proofs, the fixed configuration and the fixture provenance |
| `fixtures/seed-demo/*.scd` | five 588-byte seeded-data carriers, each reconstructing 1,023 leaves |
| `results/` | every recorded result of the current generation, including the two independent audits, the negative-control records, the regeneration validation and the dependency provenance. The current generation is a union of two stages: `check-case*.json` and `prove-case*.json` are the v1.27b constraint-check and proving records (renamed from underscore names), while `encode-case*.json`, `domains/03-zk-carrier-experiments/results/public-verification.json` and `domains/03-zk-carrier-experiments/results/public-negative-checks.json` are the v1.28p carrier records |
| `history/v1.25/`, `history/v1.27/`, `history/v1.27b/`, `history/v1.28/` | superseded versions, each keeping its own adapters, fixtures, records and report; the version stays in the filename |
| `history/regeneration-check/` | the fixture of a fresh end-to-end run, kept as a second, independent fixture |
| `vectors/` | empty by design: the map places no file here, and the field vectors live at `src/adapter/field_vectors.json` |

`results/` and `history/` filenames differ deliberately: the current generation uses hyphens
(`domains/03-zk-carrier-experiments/results/encode-case0.json`, `domains/03-zk-carrier-experiments/results/check-case0.json`, `domains/03-zk-carrier-experiments/results/public-verification.json`), the historical generations use
underscores (`encode_case0.json`, `check_case0.json`, `public_verification.json`). The audit scripts
know both conventions and are the best documentation of the mapping.

## 6. What was measured

All frame and proof sizes below are **recorded measurements by the experiments that produced them**,
quoted from the retained result files; none was re-measured for this repository, and the retained
frame files' bytes were re-checked on disk against the records (`VERIFICATION.md` §2, item 12).

| Version | Relation carried | Case 0 frame | Case 1 frame | Native proof, each case | Gates, case 0 / case 1 |
|---|---|---:|---:|---:|---:|
| v1.25 | `CEQS124_DIRECT_CHALLENGE` | 289,664 | 287,712 | 339,200 | 899,429 / 904,933 |
| v1.27 | `CEQS127_PAIRED_TRACE` | 287,648 | 281,232 | 339,104 | 521,717 / 527,221 |
| v1.27b | `CEQS12B_FIXED_CONTEXT` | 283,680 | 279,600 | 335,360 | 402,306 / 407,810 |
| v1.28 (QVT2) | same as v1.27b | 282,016 | 277,968 | 335,360 (identical) | same |
| v1.28p (QVT3) | same as v1.27b | **273,952** | **270,304** | 335,360 (identical) | same |
| target | — | 32,768 | 32,768 | ≤ 27,056 proof position | — |

The QVT2 and QVT3 rows are the *same two native proofs* re-encoded; the unchanged proof digests are
recorded in `results/carrier-audit.json` (`same_native_proof: true`).

Inside the QVT3 case-0 proof position, as `results/encode-case0.json` accounts for it: 78,080 bytes of
field coefficients and queried values, 172,736 bytes of Merkle boundary hashes, 17,424 bytes of prefix,
terminal and codec data — 268,240 bytes total against a 27,056-byte budget, i.e. 241,184 bytes over.
Even assigning every remaining boundary hash zero cost would leave 95,504 bytes in case 0 and 94,672
in case 1; v1.28 §7 states plainly that this is accounting for these representations, not a lower
bound against another protocol.

## 7. What is not in this repository, and where it comes from instead

This is the largest exclusion in the domain, and it is the reason most of `VERIFICATION.md` is
`not-run`. Three things a reader would need in order to re-run the proofs are **not** here:

| Not here | Size | Where it comes from |
|---|---:|---|
| the vendored upstream proof backend `continuation_v1.17/binius64-source` (767 files) | ≈8.6 MB | upstream `https://github.com/binius-zk/binius64` at pinned commit `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4`; six local modifications, patch `src/prover_memory.patch`, sha256 `b916606810a4b8416baddadfac531302eec91935a73b1528a201a4a189a4b563` |
| the four compiled adapter binaries (one each for v1.27, v1.27b, v1.28, v1.28p) | 5,531,152 – 5,721,256 B each | rebuild from the adapter sources in this repository with Rust 1.97.1 and `cargo build --locked --release` |
| the vendored `pqcrypto` wheel used by the v1.29 authorization component | 27,036,304 B | `pqcrypto` 0.3.4, sha256 `b2f9bad43a1e3970f55e6f68fc1864595c9b0c6e53638aa8393b1d01216a6ebb`, verified against the publisher's PyPI release metadata in `results/dependency-provenance.json` |

`docs/provenance.md` names each of the four excluded adapter binaries with its sha256 and size (and
the fifth, v1.25's, which is absent from the research tree altogether), lists the six modified
upstream files with theirs, and gives the exact rebuild commands. The adapter `Cargo.toml`
files keep their relative path dependencies into the excluded tree, each now carrying a header
comment that says the target is outside the repository and points to that page; nothing was silently
deleted. `src/install_dependency.py` reports the required wheel and refuses to invent one. Two
further kinds of material are absent for reasons outside this domain: the superseded frame binaries
excluded by the file map (their sha256 and sizes are in `docs/provenance.md` as well, since a rebuild
will not reproduce them), and the recorded review/package archives themselves, which are build
products — the packaging scripts in `src/` take the previous archive as a required `--previous`
argument and say so.

The vendored backend and the compiled adapters are not in this repository, and the pinned Rust 1.97.1
toolchain is not installed in the environment this repository was assembled in (a rebuild was also
outside this domain's scope), so **no rebuild was attempted** and **no proof was re-run**. See
`docs/what-cannot-be-run-here.md`.

## 8. What this domain does not establish

Carried verbatim in substance from the retained reports; the labels are theirs.

1. **No complete certificate.** Zero complete quorum certificates satisfying all original
   requirements were generated in any version here, and every result file carries
   `valid_QCs_generated: 0` or `complete_QC_verified: false`.
2. **No QPT-128.** The pinned backend's `SECURITY_BITS` is 96; there is no instantiated quantum
   argument-of-knowledge composition theorem for Spartan + BaseFold/FRI here, and the constraint
   system is not absorbed into the Fiat–Shamir transcript. Larger application hash outputs do not
   qualify the backend.
3. **No authorization theorem.** The relations are credential-preimage relations. Witness existence
   does not establish a fresh approval event, and the v1.29 approvals are ordinary signature
   verifications performed in the open by a reference implementation, not constraints inside a
   succinct proof.
4. **No distributed prover.** Every run here is centralized: one process holds all 43 credentials.
   The target function is stated, and the honest-majority arithmetic `64 > 3·21` identifies a
   possible regime, but no robust MPC was executed. The reports are explicit that a 43-party
   substitution would not carry the same `n > 3t` guarantee.
5. **No privacy proof for the composed protocol.** Native ZK mode is used, and the codecs are public
   post-processing, but repeated links remain linkable within a conflict domain by design, and the
   joint pseudorandomness of the two halves of one XOF output is an added assumption, not a theorem.
6. **The extraction identity is conditional.** `i+1 = (Z_i + Z'_i)(c(m) + c(m'))^{-1}` holds under an
   explicitly stated consistent-opening condition, which is computationally motivated and not
   guaranteed by a finite hash. Bounding its failure is listed as open in every version.
7. **Negative controls are finite.** "22 mutations rejected" is evidence about those 22 mutations; the
   records say so in their own `scope` fields.
