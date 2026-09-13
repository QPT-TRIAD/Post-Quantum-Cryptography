# IMPLEMENTATION_RESULTS — modeB_prover_v1.50.c (implementation-safety layer, 2026-09-11)
Target read in full (1,027 lines); pristine copy `src/modeB_prover_v1.50.c` sha256 ff8e5cd9…6adb92; nothing under PQT modified. Host: clang 18.1.8, gcc 14.2, 4 cores (taskset). Scripts: build.sh, run_sanitizers.sh, run_fuzz.sh, run_asan_production.sh.

## Build matrix (build_log.txt)
Blocker: `libclang-rt-18-dev` not installed → every clang `-fsanitize` link failed: `/usr/bin/ld: cannot find /usr/lib/llvm-18/lib/clang/18/lib/linux/libclang_rt.asan-x86_64.a: No such file or directory`
(same for ubsan_standalone, msan). Fixed without root: `apt-get download` of the exact matching .deb, `dpkg-deb -x`, private resource dir `rt/18/` (`-resource-dir=`).
| binary | flags | result |
|---|---|---|
| ref_gcc_O3 | gcc -O3 -march=native -fopenmp (header's build line) | OK |
| asan_ubsan (a) | clang -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -march=native -fopenmp | OK (-fopenmp kept, libomp present) |
| ubsan_strict (b) | clang -O1 -g -fsanitize=undefined,integer,implicit-conversion -fno-sanitize-recover=all -fno-omit-frame-pointer -march=native -fopenmp | OK |
| ubsan_recover (b') | same checks, -fsanitize-recover=all (to enumerate all sites) | OK |
| msan (c) | clang -O1 -g -fsanitize=memory -fno-omit-frame-pointer -march=native (no -fopenmp: libomp uninstrumented) | OK |
| fuzz_verify | clang -O1 -g -fsanitize=fuzzer,address,undefined -march=native -DFUZZ_NO_MAIN fuzz_verify.c | OK (1 warning: FUZZ_NO_MAIN redefined) |

## Sanitizer runs — `--run --b 10 --tau 4 --wg 8 --rho 256` (48 challenge bits), 4 threads, 20-min timeout, plus `--vectors`
(a) asan_ubsan_output.txt: `--vectors` clean, exit 0. `--run` with detect_leaks=1: NO ASan or UBSan diagnostics; at exit
`ERROR: LeakSanitizer: detected memory leaks … SUMMARY: AddressSanitizer: 33675304 byte(s) leaked in 11 allocation(s)`, exit 1
(LSan's `_exit` dropped the block-buffered JSON). Re-run (a1) detect_leaks=0, 1 thread: no diagnostics, exit 0, wall 88.5 s,
JSON `"verified":[true,true] … "tampered_rejected":true,"extracted_count":22`.
  VERIFIER-SIDE LEAK (real bug, low severity): `Direct leak of 19136 byte(s) in 2 object(s) allocated from: #0 malloc #1 verify
  src/modeB_prover_v1.50.c:803:21 #2 main src/modeB_prover_v1.50.c:1001:13` = `circ_pub_t *P` (9,568 B) malloc'd at line 803 and never
  freed on the "grinding condition" early `return 0` at line 815 (every rejected proof whose transcript changes before `ctr`, i.e. the
  demo's tamper cases 0 and 2). Fuzz-side reproduction with leak detection on (logs/leak_probe.txt): seed `corpus/A_zero` (QuickSilver
  A coefficients zeroed) → `Direct leak of 9568 byte(s) … #1 verify src/modeB_prover_v1.50_nomain.c:803:21 #2 LLVMFuzzerTestOneInput
  fuzz_verify.c:146:14`; artifact `artifacts/leak-05e0ceaa36a8ede190f99bfc174668fc37284143` (== corpus/A_zero), `artifacts/leak_report.txt`.
  The other 9 leaked objects are demo-only end-of-main allocations (main:974/975/982, qmap_init:253-255, prove:700) — not verifier state.
(b) ubsan_output.txt, ubsan_strict: aborts at the FIRST diagnostic in both `--vectors` and `--run` (exit 1, 0.35 s):
  `src/modeB_prover_v1.50.c:88:35: runtime error: left shift of 9223372036854775808 by 1 places cannot be represented in type 'uint64_t' (aka 'unsigned long')` (keccakf, ROTL64).
(b') ubsan_recover: 7 distinct sites (UBSan reports each location once); self-test JSON OK, exit 0, 21.4 s. Verbatim kinds:
  88:35 and 95:21 (keccakf ROTL64) and 169:24 / 169:35 / 169:46 (gf_reduce512 `h<<2`, `h<<5`, `h<<10`): `left shift of <v> by 1|6|2|5|10 places
  cannot be represented in type 'uint64_t'`; 239:66 (be16): `implicit conversion from type 'unsigned int' of value 20656 (32-bit, unsigned)
  to type 'uint8_t' (aka 'unsigned char') changed the value to 176 (8-bit, unsigned)`; 240:98 (be32): `… of value 10884 … changed the value to 132`.
  Assessment: all 7 are `unsigned-shift-base` / `implicit-unsigned-integer-truncation` (clang "suspicious", not C UB): rotate and carry-less
  reduction discard high bits by design (re-added via `h>>62/59/54` on line 170); be16/be32 are big-endian byte serialization. No signed
  overflow, bounds, alignment, shift-exponent, null-deref or sign-change diagnostics anywhere.
(c) msan_output.txt: `--vectors` and `--run` both clean — no MemorySanitizer reports, exit 0, wall 53.8 s (single-threaded), JSON OK.
(a2) PRODUCTION parameters (b=20, tau=11, wg=16, rho=4096) under asan_ubsan, 2 threads, detect_leaks=0: killed by the 20-min timeout (exit 124, 1200.0 s) before finishing; 0 diagnostics emitted in that window (stderr is unbuffered, so any ASan/UBSan report would be present) — INCONCLUSIVE, not a clean pass.

## Fuzzing (fuzz_verify.c; logs in fuzz_log.txt = parent stdout + logs/fuzz/fuzz-0.log + fuzz-1.log)
Harness: certificate = m(64) || handles(43×32) || proof(8,996) = 10,436 B at b=6 tau=4 wg=8 rho=64 (36 challenge bits), seed 49; the genuine
certificate is produced by prove() in LLVMFuzzerInitialize (≈21 s under ASan+coverage) and verified once. Property on every input:
verify()==TRUE ⇒ input byte-identical to the genuine certificate, else abort() ("ACCEPT-ON-INVALID", region of first differing byte printed);
genuine rejected ⇒ abort() ("REJECT-ON-GENUINE"). Proof buffer sized exactly to the input so ASan catches over-reads. 43 seeds (genuine,
empty, truncations, duplication, oversized, reordered handles/corrections/openings/siblings, bit flips in every region, ctr±, zero/0xff proofs).
Campaign: `-max_len=20872 -jobs=2 -workers=2 -timeout=30 -max_total_time=600 -detect_leaks=0` (leak detection off only because the known
line-803 leak would end every job within seconds; it is documented above).
Results (20:43:28-20:54:38, exit 0): total execs 81,041 (job0 40,311 + job1 40,730), 67 exec/s per worker, cov 455 (of 2,052 PCs in the
binary incl. harness/libFuzzer stubs) and ft 982 in both jobs, corpus 65/63 units, peak RSS 516 MB. Crashes: 0. Timeouts: 0. OOM: 0.
ACCEPT-ON-INVALID (property check abort): **0**. REJECT-ON-GENUINE: 0. Artifacts: one `slow-unit-ba24afc2…` (11 s) which is byte-identical
to the genuine certificate (full QuickSilver verify under ASan) — not a bug; the `leak-05e0ceaa…` from the leak probe (line 803 leak, above).

## Could not run / honest limits
- valgrind, AFL++, KLEE: not installed, no root to install → not attempted. MSan DID run (clean). All clang sanitizers needed the private compiler-rt (above).
- Reduced parameters throughout (production ≈ 60 s prove natively and 4 shared cores here); the `--dense` key-map branch (rho=0, lines 262-270) was not exercised.
- No byte-level certificate parser exists in the target: the fuzzer drives verify()'s in-memory input (m, handles, proof, proof_len) with a fixed public
  context; the 208-byte frame header is never read by verify() (TARGET_NOTES.md) — a deployment parser must bind it itself.
- verify() recomputes the 256×256 F2 challenge inversion per call (≈15 ms under ASan) → ≈67 exec/s per worker; essentially every mutant is rejected at the
  length / handle-order / grinding / commitment-hash / VOLE stages, so the degree-6 QuickSilver arithmetic is exercised by the sanitizer self-tests
  (prove+verify+tamper+extract), not by mutation. Fuzz binary single-threaded (no OpenMP); 36 challenge bits ⇒ a chance alternate-ctr accept ≈ 81k·2⁻³⁶, negligible.
