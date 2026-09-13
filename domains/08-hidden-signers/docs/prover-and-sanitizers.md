# The C prover, and what its sanitizer runs do and do not show

`../src/mode_b_prover.c` is the v1.51 release (`modeB_prover_v1.51.c` under the versioned name);
`../history/mode-b-prover-v1.50.c` and `../history/mode-b-prover-v1.49.c` are the two predecessors,
kept because each one is the reference for a fix. All three are a single file holding the **prover,
the verifier and the public pair-search extractor** for Mode B.

---

## 1. Design

**Fixed parameters.** 64 seats, quorum 43. Field GF(2^256) with x^256 + x^10 + x^5 + x^2 + 1 for s, r,
handles and the QuickSilver MAC. Key map F: F₂^512 → F₂^1024 (expansion 512, the v1.47 ledger's
setting) as a **seeded random quadratic map**, either dense or ρ monomials per equation. Handle
Z = r⁷ ⊕ c·s in v1.49, and Z = r⁷ ⊕ L_c(s) with L_c(s) = c_a·s ⊕ c_b·s² ⊕ c_c·s⁴ from v1.50 (a
public counter makes L_c invertible). Witness per seat: r (256 bits) and a 64-bit one-hot selector;
s = c⁻¹(Z ⊕ r⁷) is derived inside the circuit (degree 3), so the key-map constraints have degree 6.
ℓ = 43·320 = 13,760 committed bits plus 1,536 mask bits; ℓ̂ = 15,296. Soundness parameters follow the
FAEST v2 QROM bound (Lemma 9.39): the last challenge must carry τ·b + w_g ≥ 230 bits; defaults
b = 20, τ = 11, w_g = 16 (236).

**Proof.** VOLE-in-the-head in the structure of FAEST v2: GGM seed trees with 2^b leaves, τ
repetitions, leaf commitments, VOLE corrections, the VOLE consistency hash, a QuickSilver check of
degree 6, w_g grinding bits, all-but-one openings.

**Implementation.** SHAKE256 for every hash and PRG (checked against Python on test vectors),
carry-less multiplication via PCLMUL for GF(2^256), OpenMP over repetitions (trees) and seats
(QuickSilver). The file prints one JSON object with sizes, timings and the extraction result, and
carries a `--vectors` mode for the cross-language self-check. **It is a research prototype: not
constant time, no side-channel protection** — the source says so itself.

**Two bugs found and fixed before v1.49** are documented in all three files: an `inv7` constant error
and a Δ-masking error. Both are the kind of defect only an implementation exposes, which is why the
three revisions are preserved rather than squashed.

## 2. What was run here

| Run | Command | Result |
|---|---|---|
| build ×3 | `gcc -O3 -march=native -fopenmp -Wall -o <bin> <file>.c` | exit 0, **no warnings**, on all three |
| test vectors ×3 | `<bin> --vectors` | identical JSON on all three: SHAKE256("abc"), `a·b` in GF(2^256), `x_times_x255_low64`, `root7_ok`, `inv_ok` |
| reduced smoke run ×3 | `<bin> --run --b 12 --tau 20 --wg 8 --rho 1024` (the documented reduced setting, `mode-b-security.md` §10) | proof **47,524 B**, frame 49,108 B, `verified: [true,true]`, `tampered_rejected: true`, **22 seats extracted**, 6.8–11 s on 12 threads |
| **production-parameter run** (v1.51) | `./modeB_prover --run --b 20 --tau 11 --wg 16 --rho 4096` | proof **29,100 B**, frame **30,684 B**, `fits_32768: true`, `verified: [true,true]`, tamper rejected, 22 seats; 236.84 s wall on 12 threads |

The three versions agree on the reduced run, which is expected: v1.49 → v1.50 changed the challenge
derivation and the extraction reporting, and v1.51 fixed a leak — none of these changes the
reduced-parameter output.

**Two things a reader must not take from this table.** The reduced run's 47,524-byte proof does *not*
fit 32 KiB — it is a *fast* setting, chosen to be runnable, not a size setting; the size claim comes
from the ledger's settings, and the certificate-size figures belong to
[rigorous-ledger.md](rigorous-ledger.md). And the production-parameter run is **one run, once**. It
agrees with `mode-b-security.md` §8's size table to the byte, and that table was a *formula* entry in
the rounds that produced these sources — the production-parameter run had not been performed then.
Running the size table once is not a security result, and nothing here re-runs it at a sanitizer. The
output is `../results/prover-v1.51-production-run.json`.

## 3. Sanitizer runs: recorded, reproduced, and the difference

The recorded baselines live in the verification environment's audit stack, not in this domain:

| Recorded run | Binary | Finding |
|---|---|---|
| ASan+UBSan, production parameters, 8 threads, 3,600 s timeout | v1.50, sanitizer build | `AddressSanitizer: 33,714,488 byte(s) leaked in 11 allocation(s)`, exit 1; two of those allocations (19,136 B) are inside `verify()` |
| LSan, reduced parameters | v1.51, sanitizer build | `AddressSanitizer: 33,656,168 byte(s) leaked in 9 allocation(s)`; **no frame inside `verify()`** |

Those runs were built with the audit stack's clang-based sanitizer toolchain. **That build cannot be
reproduced in this environment:** clang 18's compiler runtime is absent
(`libclang_rt.asan_static-x86_64.a` is not installed), while gcc 14's `libasan`/`liblsan` are present.

**What was reproduced here** is therefore a *reduced* ASan+LSan run of the v1.51 source built with
**gcc 14.2.0** (`-fsanitize=address,undefined -g`), at the same documented reduced setting:

    AddressSanitizer: 33,732,200 byte(s) leaked in 9 allocation(s)

- **Same shape as the record**: 9 leak records, no frame inside `verify()` — i.e. the F1 leak fix is
  visible in the report, and the 11-allocation v1.50 set is not.
- **No memory-safety error**: no out-of-bounds, no use-after-free, no stack trace of that kind, and
  **no UBSan runtime diagnostic** in either the functional or the leak-checked run.
- **Not byte-identical to the record** (33,732,200 vs 33,656,168): a different compiler and
  allocator, so allocation sizes and the byte total differ. The leak *count* and the absence of a
  `verify()` frame agree.

`../results/prover-v1.51-asan-lsan-reduced.txt` holds the sanitizer report with the build directories
normalised; `../results/prover-v1.51-asan-run.json` holds the functional output of the same
sanitizer-built binary. One implementation detail worth recording, because it is why the leak
transcript has no JSON in it: **LeakSanitizer's exit path does not flush stdio**, so the run's JSON
never reaches stdout under `detect_leaks=1`; the functional output is captured from a second run of
the same binary with `detect_leaks=0`, which flushes normally. (`stdbuf` cannot be used to work
around this — its `LD_PRELOAD` collides with the ASan runtime: "ASan runtime does not come first in
initial library list".)

## 4. What these runs do not show

- They are **not** the recorded production-parameter sanitizer runs, and they are not a substitute for
  them: the only production-parameter run in this domain was a plain (non-sanitizer) build.
- They are **not** a memory-safety proof. Sanitizers report what the executed paths touch; nothing
  here is a coverage argument, and the parallel OpenMP paths were exercised only at the reduced
  setting.
- They say nothing about **side channels** — the code is explicitly not constant time, and it was not
  written to be.
- They say nothing about **security**: a clean sanitizer run of a prover is a statement about
  memory, not about soundness, zero-knowledge or the collaborative-prover requirement, none of which
  this file addresses.
