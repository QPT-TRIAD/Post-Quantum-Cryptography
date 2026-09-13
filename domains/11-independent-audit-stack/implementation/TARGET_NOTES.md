# TARGET_NOTES — modeB_prover_v1.50.c (read in full: 1,027 lines, sha256 ff8e5cd9…6adb92)

Source of record: `modeB_prover_v1.50.c` in the read-only research tree (`PQT_SRC`).
Pristine copy used for
all builds: `src/modeB_prover_v1.50.c` (same sha256). Fuzzer copy: `src/modeB_prover_v1.50_nomain.c`
= pristine + `#ifndef FUZZ_NO_MAIN` / `#endif` around `main()` (diff in `src/nomain.diff`, 2 lines).

## Expected build / run (header comment, lines 25-28)
    gcc -O3 -march=native -fopenmp -o modeB_prover modeB_prover_v1.50.c
    ./modeB_prover --run [--b 20] [--tau 11] [--wg 16] [--rho 4096|--dense] [--seed N] [--threads T]
    ./modeB_prover --vectors          # SHAKE256 / GF(2^256) test vectors (JSON)
`--run` is the self-test/demo: builds key map + 64-seat registry from `--seed` (default 49), prepares two
frames (seat sets {0..42} and {0..21} ∪ {43..63}, messages m0 = 0^64 and m1 = 0^63‖0x11), proves both,
verifies both, runs 3 single-bit tamper checks (flip in witness correction `d`, in the last opening, in
correction c_1), then runs the pair-search extractor. Prints one JSON object; process exit code 0 iff
`ok0 && ok1 && extracted == 22 && tampered_rejected`. `--vectors` exercises SHAKE, gf_mul, gf_root7, gf_inv.

## Parameter knobs
Compile-time (`#define`, lines 47-67): N_SEATS 64, QUORUM 43, MIN_OVERLAP 22, NB 256, EXP 512, M_EQ 1024,
KEY_BYTES 128, HANDLE_BYTES 32, HEADER_BYTES 208, MAX_FRAME 32768, LAMBDA 256, DEG 6, W_SEAT 320,
ELL 13760, MASK_BITS 1536, ELL_HAT 15296, EHW 239, EHB 1912, MAX_TAU 32, MAX_B 26.
Run-time (`params_t {b, tau, wg, rho, threads}`, main() lines 936-948):
- `--b`   GGM tree depth (2^b leaves per repetition), default 20, checked `b <= 26`
- `--tau` number of VOLE repetitions, default 11, checked `tau <= 32` and `tau*b <= 256`
- `--wg`  grinding bits on the third challenge, default 16 (soundness: tau*b + wg >= 230 required; 236 default)
- `--rho` quadratic monomials per key-map equation (sparse, default 4096); `--dense` = rho 0 (all 130,816)
- `--threads` OpenMP threads; `--seed` derives key-map seed, registry seed and prover randomness via SHAKE.
No lower-bound checks: `--b 0`, `--tau 0` are accepted by the argument check (tau=0 makes
`proof_size()` wrap through `(size_t)(tau-1)*EHB`); CLI-only, not reachable from certificate bytes.

## Entry points and byte layout
There is NO byte-level certificate parser in the file. `verify()` (line 795) takes an in-memory
`frame_t` (line 399): `header[208]`, `handles[43][32]`, `seat_at[43]` (prover-only), `m[64]`,
`proof`/`proof_len`. Fields actually consumed by `verify()`: `m`, `handles`, `proof`, `proof_len`,
plus the public context `registry_t R` (`cfg[64]`, `domain[64]`, `keys[64][128]`), `qmap_t q` and
`params_t p`. **The 208-byte header written by `frame_header()` (line 421: "CQ50", version 50,
0x50B0, cfg, domain, m, quorum, handle bytes, payload length) is never read by `verify()`**; a
deployment parser must bind it itself (m in the header vs. the m used for the statement hash, etc.).
Proof byte layout (`proof_size()` line 666; parse order in `verify()` lines 804-849):
    h_com[64] | corrections[(tau-1)*1912] | d[1912] | u~[32] | v~[32] | A_0..A_5[6*32] | ctr[4] |
    openings[tau * (b*32 + 64)]  (per repetition: b sibling seeds top-down, then the hidden leaf com)
Check order in `verify()`: (1) `proof_len == proof_size(p)`; (2) handles strictly increasing (memcmp);
(3) recompute challenge triple from (cfg, domain, m) incl. the 256x256 F2 inversion loop; (4) chi1 over
transcript prefix, chi2, chi3 -> h3 -> grinding condition (wg low bits zero); (5) regenerate GGM trees
from openings, compare commitment hash `h_com` and trailing-bytes check; (6) VOLE consistency;
(7) degree-6 QuickSilver check. Returns int (1 accept / 0 reject) and a reason string `*why`.
Other entry points: `prove()` line 670, `extract()` line 900 (pair-search over two frames), `frame_prepare()`
line 409, `challenge_c()` line 352, `statement_hash()` line 427.

## Reduced parameters used here (production ≈ 60 s prove on the author's box; this host: 4 cores shared)
Reference `gcc -O3` timings, 4 threads: `--b 6 --tau 3 --wg 4 --rho 64` 4.2 s; `--b 8 --tau 4 --wg 4 --rho 64`
4.5 s; `--b 10 --tau 4 --wg 8 --rho 256` 5.8 s (extract is a fixed ≈2.4 s). All three: verified [true,true],
tampered_rejected true, extracted 22, exit 0. Sanitizer runs use `--b 10 --tau 4 --wg 8 --rho 256`
(48 challenge bits; every code path of prove/verify/extract except the `--dense` key-map branch,
lines 262-270, which is ~32x slower and was not run). Fuzz harness uses `b=6 tau=4 wg=8 rho=64`
(36 challenge bits; certificate 10,436 bytes; genuine verify ≈ 8 s single-threaded under ASan+coverage).

## Toolchain facts found on this host
clang 18.1.8 is installed WITHOUT its compiler-rt runtimes (`libclang-rt-18-dev` absent: every
`-fsanitize=` link failed with "cannot find libclang_rt.*-x86_64.a", see build_log.txt history in
IMPLEMENTATION_RESULTS.md). The exact matching .deb was fetched with `apt-get download` (no root) and
extracted into a private resource dir `rt/18/` (`-resource-dir=`); ASan, UBSan, MSan and libFuzzer then
link and run. gcc 14 has libasan/libubsan only (no MSan, no libFuzzer, no `-fsanitize=integer`).
