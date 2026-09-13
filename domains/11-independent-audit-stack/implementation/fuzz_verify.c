/* fuzz_verify.c -- libFuzzer harness for verify() of modeB_prover_v1.50.c
 *
 * The target has no byte-level certificate parser: verify() consumes a frame_t
 * whose verifier-relevant fields are m[64], handles[QUORUM][32] and
 * proof/proof_len (the 208-byte header written by frame_header() is never read
 * by verify()).  The harness therefore defines the certificate byte string as
 *
 *     cert = m(64) || handles(QUORUM*32 = 1376) || proof(proof_size(p))
 *
 * i.e. exactly the bytes verify() consumes, in the frame's own order.  Fuzzer
 * input shorter than 1440 bytes is zero-padded on the m/handles part and gets
 * proof_len = 0; longer input has proof = bytes[1440..size).  The proof lives in
 * a heap block sized exactly to the input, so ASan catches any over-read.
 *
 * Public context (fixed, generated in LLVMFuzzerInitialize with the same seed
 * derivation as main(), seed 49): key map q, registry R, params p.  One genuine
 * certificate is produced by prove() at the reduced parameters below and
 * verified once (the harness aborts at init if the genuine one is rejected).
 *
 * Property checked on every input:
 *     verify(input) == TRUE   =>   input is byte-identical to the genuine cert
 * A violation prints ACCEPT-ON-INVALID with the first differing region and
 * calls abort() (libFuzzer then saves the input as crash-*).  The converse
 * (genuine input rejected) also aborts (REJECT-ON-GENUINE).
 *
 * Build:  clang -O1 -g -fsanitize=fuzzer,address,undefined -march=native
 *               -DFUZZ_NO_MAIN -o bin/fuzz_verify fuzz_verify.c
 *         (no -fopenmp: each libFuzzer worker is its own process; the
 *          "#pragma omp" lines are then ignored)
 */
#define FUZZ_NO_MAIN
#include "src/modeB_prover_v1.50_nomain.c"
#include <unistd.h>

#ifndef FUZZ_B
#define FUZZ_B 6
#endif
#ifndef FUZZ_TAU
#define FUZZ_TAU 4
#endif
#ifndef FUZZ_WG
#define FUZZ_WG 8
#endif
#ifndef FUZZ_RHO
#define FUZZ_RHO 64
#endif
#ifndef FUZZ_SEED
#define FUZZ_SEED 49
#endif
#define CERT_PREFIX (64 + QUORUM * HANDLE_BYTES)   /* 1440: m || handles */

static params_t FP;
static qmap_t *FQ;
static registry_t *FR;
static uint8_t *genuine;
static size_t genuine_len;

/* Name of the certificate region containing byte offset `off` (for reports). */
static const char *region_of(size_t off, size_t *rel) {
    size_t o = off;
    if (o < 64) { *rel = o; return "m"; }
    o -= 64;
    if (o < (size_t)QUORUM * HANDLE_BYTES) { *rel = o; return "handles"; }
    o -= (size_t)QUORUM * HANDLE_BYTES;
    if (o < 64) { *rel = o; return "proof.h_com"; }
    o -= 64;
    if (o < (size_t)(FP.tau - 1) * EHB) { *rel = o; return "proof.corrections"; }
    o -= (size_t)(FP.tau - 1) * EHB;
    if (o < EHB) { *rel = o; return "proof.witness_correction_d"; }
    o -= EHB;
    if (o < 32) { *rel = o; return "proof.vole_hash_u~"; }
    o -= 32;
    if (o < 32) { *rel = o; return "proof.vole_hash_v~"; }
    o -= 32;
    if (o < (size_t)DEG * 32) { *rel = o; return "proof.quicksilver_A"; }
    o -= (size_t)DEG * 32;
    if (o < 4) { *rel = o; return "proof.grind_ctr"; }
    o -= 4;
    if (o < (size_t)FP.tau * (FP.b * 32 + 64)) { *rel = o; return "proof.openings"; }
    o -= (size_t)FP.tau * (FP.b * 32 + 64);
    *rel = o; return "beyond_proof_end";
}

static void dump_input(const uint8_t *data, size_t size, const char *tag) {
    char name[256];
    snprintf(name, sizeof name, "%s-%lu.bin", tag, (unsigned long)getpid());
    FILE *fp = fopen(name, "wb");
    if (fp) { fwrite(data, 1, size, fp); fclose(fp); fprintf(stderr, "  input saved to %s\n", name); }
}

int LLVMFuzzerInitialize(int *argc, char ***argv) {
    (void)argc; (void)argv;
    init_xpow();
    FP.b = FUZZ_B; FP.tau = FUZZ_TAU; FP.wg = FUZZ_WG; FP.rho = FUZZ_RHO; FP.threads = 1;
    if (FP.tau * FP.b > 256 || FP.b > MAX_B || FP.tau > MAX_TAU || FP.tau < 1 || FP.b < 1) {
        fprintf(stderr, "fuzz_verify: bad parameters\n"); abort();
    }
    double t0 = now();
    /* same seed derivation as main() */
    uint8_t mseed[32], rseed[32], rnd0[32], sb[4];
    be32(sb, (uint32_t)FUZZ_SEED);
    shake2("CQ50/seeds", sb, 4, NULL, 0, mseed, 32);
    shake2("CQ50/seeds", sb, 4, "r", 1, rseed, 32);
    shake2("CQ50/seeds", sb, 4, "0", 1, rnd0, 32);
    FQ = malloc(sizeof *FQ); qmap_init(FQ, mseed, FP.rho);
    FR = malloc(sizeof *FR); registry_build(FR, FQ, rseed);
    int left[QUORUM]; for (int k = 0; k < QUORUM; k++) left[k] = k;
    uint8_t m0[64] = {0};
    frame_t *f0 = calloc(1, sizeof *f0);
    frame_prepare(f0, FR, m0, left);
    ptimes_t T;
    if (prove(&FP, FQ, FR, f0, rnd0, &T)) { fprintf(stderr, "fuzz_verify: prove() failed at init\n"); abort(); }
    double secs = 0; const char *why = "?";
    int ok = verify(&FP, FQ, FR, f0, &secs, &why);
    if (!ok) { fprintf(stderr, "fuzz_verify: genuine certificate REJECTED at init (%s)\n", why); abort(); }
    genuine_len = CERT_PREFIX + f0->proof_len;
    genuine = malloc(genuine_len);
    memcpy(genuine, f0->m, 64);
    memcpy(genuine + 64, f0->handles, (size_t)QUORUM * HANDLE_BYTES);
    memcpy(genuine + CERT_PREFIX, f0->proof, f0->proof_len);
    const char *dump = getenv("FUZZ_DUMP_CERT");
    if (dump) {
        FILE *fp = fopen(dump, "wb");
        if (fp) { fwrite(genuine, 1, genuine_len, fp); fclose(fp); }
        fprintf(stderr, "fuzz_verify: wrote genuine certificate (%zu bytes) to %s\n", genuine_len, dump);
    }
    fprintf(stderr, "fuzz_verify: params b=%d tau=%d wg=%d rho=%d seed=%d; cert = m(64)||handles(%d)||proof(%zu) = %zu bytes;"
                    " init %.1fs (prove %.2fs, verify %.2fs, genuine ok=%d '%s')\n",
            FP.b, FP.tau, FP.wg, FP.rho, FUZZ_SEED, QUORUM * HANDLE_BYTES, f0->proof_len, genuine_len,
            now() - t0, T.total, secs, ok, why);
    free(f0->proof); free(f0);
    return 0;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    size_t alloc = size < CERT_PREFIX ? CERT_PREFIX : size;
    uint8_t *buf = malloc(alloc);
    if (size < CERT_PREFIX) memset(buf, 0, CERT_PREFIX);
    if (size) memcpy(buf, data, size);
    frame_t *f = calloc(1, sizeof *f);
    memcpy(f->m, buf, 64);
    memcpy(f->handles, buf + 64, (size_t)QUORUM * HANDLE_BYTES);
    f->proof = buf + CERT_PREFIX;                     /* 1440 = 8*180: keeps the uint64_t casts in verify() 8-aligned */
    f->proof_len = size > CERT_PREFIX ? size - CERT_PREFIX : 0;
    double secs = 0; const char *why = "?";
    int ok = verify(&FP, FQ, FR, f, &secs, &why);
    int same = (size == genuine_len && memcmp(data, genuine, size) == 0);
    if (ok && !same) {
        size_t first = 0, rel = 0;
        size_t n = size < genuine_len ? size : genuine_len;
        while (first < n && data[first] == genuine[first]) first++;
        const char *reg = region_of(first, &rel);
        fprintf(stderr, "ACCEPT-ON-INVALID: verify() returned TRUE (why='%s') for an input that differs from the genuine certificate:"
                        " size %zu (genuine %zu), first differing byte at offset %zu = region %s+%zu\n",
                why, size, genuine_len, first, reg, rel);
        dump_input(data, size, "accept-on-invalid");
        abort();
    }
    if (!ok && same) {
        fprintf(stderr, "REJECT-ON-GENUINE: verify() returned FALSE (why='%s') for the genuine certificate\n", why);
        abort();
    }
    free(f); free(buf);
    return 0;
}
