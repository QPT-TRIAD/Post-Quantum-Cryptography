/* modeB_prover_v1.50.c — CE-QS Mode B hidden-signer certificate at PRODUCTION
 * parameters: prover, verifier and public pair-search extractor.
 *
 * v1.50 = v1.49 plus the two fixes from the independent cryptanalysis pass:
 *  (1) linearized handle Z = r^7 + c_a s + c_b s^2 + c_c s^4 with a 768-bit
 *      challenge (a challenge collision no longer suppresses extraction);
 *  (2) extraction reports every identified seat, never aborting on the count.
 *
 * Parameters (fixed): 64 seats, quorum 43; field GF(2^256) with
 * x^256+x^10+x^5+x^2+1 for s, r, handles and the QuickSilver MAC; key map
 * F: F2^512 -> F2^1024 (expansion 512, v1.47 ledger) as a seeded random
 * quadratic map (dense, or rho monomials per equation); handle Z = r^7 + c s.
 * Proof: VOLE-in-the-head in the structure of FAEST v2 (GGM seed trees with
 * 2^b leaves, tau repetitions, leaf commitments, VOLE corrections, VOLE
 * consistency hash, QuickSilver check of degree 6, w_g grinding bits,
 * all-but-one openings). Witness per seat: r (256 bits) and a 64-bit one-hot
 * selector; s = c^-1 (Z + r^7) is derived inside the circuit (degree 3), so the
 * key-map constraints have degree 6. ell = 43*320 = 13,760 committed bits plus
 * 1,536 mask bits; ell_hat = 15,296.
 *
 * Soundness parameters follow the FAEST v2 QROM bound (Lemma 9.39): the last
 * challenge must carry tau*b + w_g >= 230 bits (v1.47 ledger with that bound).
 * Defaults: b = 20, tau = 11, w_g = 16 (11*20 + 16 = 236).
 *
 * Build:  gcc -O3 -march=native -fopenmp -o modeB_prover modeB_prover_v1.50.c
 * Run:    ./modeB_prover --run [--b 20] [--tau 11] [--wg 16] [--rho 4096|--dense]
 *                         [--seed N] [--threads T]
 *         ./modeB_prover --vectors     (SHAKE / field test vectors for Python)
 * Prints one JSON object with sizes, timings and the extraction result.
 * Research prototype: not constant time, no side-channel protection.
 */
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifdef _OPENMP
#include <omp.h>
#endif
#ifdef __PCLMUL__
#include <wmmintrin.h>
#include <emmintrin.h>
#include <smmintrin.h>
#endif

#define N_SEATS 64
#define QUORUM 43
#define MIN_OVERLAP 22
#define NB 256
#define EXP 512
#define M_EQ (2 * NB + EXP)          /* 1024 */
#define KEY_BYTES (M_EQ / 8)         /* 128 */
#define XW 8                          /* 512-bit input words */
#define HANDLE_BYTES 32
#define HEADER_BYTES 208
#define MAX_FRAME 32768
#define LAMBDA 256
#define DEG 6
#define W_SEAT (NB + N_SEATS)        /* 320 */
#define ELL (QUORUM * W_SEAT)        /* 13760 */
#define MASK_BITS (LAMBDA + (DEG - 1) * LAMBDA)
#define ELL_HAT (ELL + MASK_BITS)    /* 15296 */
#define EHW ((ELL_HAT + 63) / 64)    /* 239 words */
#define EHB (EHW * 8)                /* 1912 bytes */
#define MAX_TAU 32
#define MAX_B 26

/* ------------------------------------------------------------ Keccak ---- */
static const uint64_t KRC[24] = {
    0x0000000000000001ULL, 0x0000000000008082ULL, 0x800000000000808aULL, 0x8000000080008000ULL,
    0x000000000000808bULL, 0x0000000080000001ULL, 0x8000000080008081ULL, 0x8000000000008009ULL,
    0x000000000000008aULL, 0x0000000000000088ULL, 0x0000000080008009ULL, 0x000000008000000aULL,
    0x000000008000808bULL, 0x800000000000008bULL, 0x8000000000008089ULL, 0x8000000000008003ULL,
    0x8000000000008002ULL, 0x8000000000000080ULL, 0x000000000000800aULL, 0x800000008000000aULL,
    0x8000000080008081ULL, 0x8000000000008080ULL, 0x0000000080000001ULL, 0x8000000080008008ULL};
static const int KROT[24] = {1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 2, 14,
                             27, 41, 56, 8, 25, 43, 62, 18, 39, 61, 20, 44};
static const int KPI[24] = {10, 7, 11, 17, 18, 3, 5, 16, 8, 21, 24, 4,
                            15, 23, 19, 13, 12, 2, 20, 14, 22, 9, 6, 1};
#define ROTL64(x, n) (((x) << (n)) | ((x) >> (64 - (n))))

static void keccakf(uint64_t st[25]) {
    for (int r = 0; r < 24; r++) {
        uint64_t bc[5], t;
        for (int i = 0; i < 5; i++) bc[i] = st[i] ^ st[i + 5] ^ st[i + 10] ^ st[i + 15] ^ st[i + 20];
        for (int i = 0; i < 5; i++) {
            t = bc[(i + 4) % 5] ^ ROTL64(bc[(i + 1) % 5], 1);
            for (int j = 0; j < 25; j += 5) st[j + i] ^= t;
        }
        t = st[1];
        for (int i = 0; i < 24; i++) {
            int j = KPI[i];
            uint64_t b0 = st[j];
            st[j] = ROTL64(t, KROT[i]);
            t = b0;
        }
        for (int j = 0; j < 25; j += 5) {
            for (int i = 0; i < 5; i++) bc[i] = st[j + i];
            for (int i = 0; i < 5; i++) st[j + i] ^= (~bc[(i + 1) % 5]) & bc[(i + 2) % 5];
        }
        st[0] ^= KRC[r];
    }
}

#define RATE 136
typedef struct { uint64_t st[25]; int pos; int squeezing; } shake_t;

static void shake_init(shake_t *c) { memset(c, 0, sizeof *c); }
static void shake_absorb(shake_t *c, const void *data, size_t n) {
    const uint8_t *d = (const uint8_t *)data;
    uint8_t *s = (uint8_t *)c->st;
    for (size_t i = 0; i < n; i++) {
        s[c->pos++] ^= d[i];
        if (c->pos == RATE) { keccakf(c->st); c->pos = 0; }
    }
}
static void shake_squeeze(shake_t *c, void *out, size_t n) {
    uint8_t *o = (uint8_t *)out, *s = (uint8_t *)c->st;
    if (!c->squeezing) {
        s[c->pos] ^= 0x1F; s[RATE - 1] ^= 0x80;
        keccakf(c->st); c->pos = 0; c->squeezing = 1;
    }
    for (size_t i = 0; i < n; i++) {
        if (c->pos == RATE) { keccakf(c->st); c->pos = 0; }
        o[i] = s[c->pos++];
    }
}
static void shake_label(shake_t *c, const char *label) {
    shake_init(c);
    shake_absorb(c, label, strlen(label) + 1);
}
static void shake2(const char *label, const void *a, size_t na, const void *b, size_t nb,
                   void *out, size_t n) {
    shake_t c; shake_label(&c, label);
    shake_absorb(&c, a, na); shake_absorb(&c, b, nb);
    shake_squeeze(&c, out, n);
}

/* --------------------------------------------------------- GF(2^256) ---- */
typedef struct { uint64_t v[4]; } gf;
static const gf GF0 = {{0, 0, 0, 0}}, GF1 = {{1, 0, 0, 0}};

static inline gf gf_add(gf a, gf b) { for (int i = 0; i < 4; i++) a.v[i] ^= b.v[i]; return a; }
static inline int gf_iszero(gf a) { return (a.v[0] | a.v[1] | a.v[2] | a.v[3]) == 0; }
static inline int gf_eq(gf a, gf b) { return memcmp(&a, &b, sizeof a) == 0; }
static inline int gf_bit(gf a, int k) { return (a.v[k >> 6] >> (k & 63)) & 1; }

#ifdef __PCLMUL__
static inline void clmul64(uint64_t a, uint64_t b, uint64_t *lo, uint64_t *hi) {
    __m128i x = _mm_set_epi64x(0, (long long)a), y = _mm_set_epi64x(0, (long long)b);
    __m128i p = _mm_clmulepi64_si128(x, y, 0x00);
    *lo = (uint64_t)_mm_cvtsi128_si64(p);
    *hi = (uint64_t)_mm_extract_epi64(p, 1);
}
#else
static inline void clmul64(uint64_t a, uint64_t b, uint64_t *lo, uint64_t *hi) {
    uint64_t l = 0, h = 0;
    for (int i = 0; i < 64; i++)
        if ((b >> i) & 1) { l ^= a << i; if (i) h ^= a >> (64 - i); }
    *lo = l; *hi = h;
}
#endif

static inline gf gf_reduce512(uint64_t r[8]) {
    for (int i = 7; i >= 4; i--) {
        uint64_t h = r[i]; int b = i - 4;
        r[i] = 0;
        r[b] ^= h ^ (h << 2) ^ (h << 5) ^ (h << 10);
        r[b + 1] ^= (h >> 62) ^ (h >> 59) ^ (h >> 54);
    }
    gf o; for (int i = 0; i < 4; i++) o.v[i] = r[i]; return o;
}
static inline gf gf_mul(gf a, gf b) {
    uint64_t r[8] = {0, 0, 0, 0, 0, 0, 0, 0}, lo, hi;
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++) {
            clmul64(a.v[i], b.v[j], &lo, &hi);
            r[i + j] ^= lo; r[i + j + 1] ^= hi;
        }
    return gf_reduce512(r);
}
static gf gf_pow(gf a, const uint64_t e[4]) {
    gf r = GF1;
    for (int i = 255; i >= 0; i--) {
        r = gf_mul(r, r);
        if ((e[i >> 6] >> (i & 63)) & 1) r = gf_mul(r, a);
    }
    return r;
}
static gf gf_inv(gf a) {
    const uint64_t e[4] = {0xFFFFFFFFFFFFFFFEULL, ~0ULL, ~0ULL, ~0ULL};
    return gf_pow(a, e);
}
static gf gf_pow7(gf a) { gf a2 = gf_mul(a, a), a4 = gf_mul(a2, a2); return gf_mul(gf_mul(a, a2), a4); }
static gf gf_root7(gf a) {
    /* 7^-1 mod (2^256-1) = 0x(db6 x 21)d; the four little-endian limbs differ
     * because 16 hex digits is not a multiple of the 3-digit period. */
    const uint64_t inv7[4] = {0xdb6db6db6db6db6dULL, 0x6db6db6db6db6db6ULL,
                              0xb6db6db6db6db6dbULL, 0xdb6db6db6db6db6dULL};
    return gf_pow(a, inv7);
}
static gf gf_from_bytes(const uint8_t *b) {          /* big-endian 32 bytes */
    gf o = GF0;
    for (int k = 0; k < 4; k++)
        for (int i = 0; i < 8; i++) o.v[k] |= (uint64_t)b[31 - 8 * k - i] << (8 * i);
    return o;
}
static void gf_to_bytes(gf a, uint8_t *b) {
    for (int k = 0; k < 4; k++)
        for (int i = 0; i < 8; i++) b[31 - 8 * k - i] = (uint8_t)(a.v[k] >> (8 * i));
}
static gf gf_from_shake(const char *label, const void *a, size_t na, const void *b, size_t nb) {
    uint8_t buf[32]; shake2(label, a, na, b, nb, buf, 32); return gf_from_bytes(buf);
}

/* x^k mod f for k <= 1020, and c^-1 x^j tables */
static gf XPOW[1024];
static void init_xpow(void) {
    gf x = GF0; x.v[0] = 2;
    XPOW[0] = GF1;
    for (int k = 1; k < 1024; k++) XPOW[k] = gf_mul(XPOW[k - 1], x);
}

/* ------------------------------------------------------------ helpers ---- */
static inline int bitget(const uint64_t *w, size_t p) { return (w[p >> 6] >> (p & 63)) & 1; }
static inline void bitset1(uint64_t *w, size_t p) { w[p >> 6] |= 1ULL << (p & 63); }
static inline int parity8(const uint64_t *a, const uint64_t *b) {
    uint64_t x = 0; for (int i = 0; i < 8; i++) x ^= a[i] & b[i];
    return __builtin_parityll(x);
}
static double now(void) {
#ifdef _OPENMP
    return omp_get_wtime();
#else
    return (double)clock() / CLOCKS_PER_SEC;
#endif
}
static void be16(uint8_t *p, unsigned v) { p[0] = v >> 8; p[1] = v; }
static void be32(uint8_t *p, uint32_t v) { p[0] = v >> 24; p[1] = v >> 16; p[2] = v >> 8; p[3] = v; }

/* ------------------------------------------------------------ key map ---- */
typedef struct {
    uint64_t *rows;      /* [M_EQ][512][8] bitmask of j>i */
    uint64_t *lin;       /* [M_EQ][8] */
    uint8_t *cst;        /* [M_EQ] */
    uint8_t seed[32];
    long monomials;      /* total quadratic monomials */
} qmap_t;

static void qmap_init(qmap_t *q, const uint8_t seed[32], int rho) {
    memcpy(q->seed, seed, 32);
    q->rows = calloc((size_t)M_EQ * 512 * 8, sizeof(uint64_t));
    q->lin = calloc((size_t)M_EQ * 8, sizeof(uint64_t));
    q->cst = calloc(M_EQ, 1);
    shake_t c; shake_label(&c, "CQ50/F"); shake_absorb(&c, seed, 32);
    q->monomials = 0;
    for (int e = 0; e < M_EQ; e++) {
        uint8_t byte; shake_squeeze(&c, &byte, 1); q->cst[e] = byte & 1;
        shake_squeeze(&c, &q->lin[e * 8], 64);
        uint64_t *row = &q->rows[(size_t)e * 512 * 8];
        if (rho <= 0) {                                   /* dense */
            shake_squeeze(&c, row, 512 * 64);
            for (int i = 0; i < 512; i++) {
                uint64_t *r = &row[i * 8];
                for (int w = 0; w < 8; w++) {
                    for (int t = 0; t < 64; t++) if (64 * w + t <= i) r[w] &= ~(1ULL << t);
                    q->monomials += __builtin_popcountll(r[w]);
                }
            }
        } else {
            for (int k = 0; k < rho; k++) {
                uint8_t b4[4]; shake_squeeze(&c, b4, 4);
                int i = ((b4[0] << 8) | b4[1]) & 511, j = ((b4[2] << 8) | b4[3]) & 511;
                if (i == j) continue;
                if (i > j) { int t = i; i = j; j = t; }
                uint64_t *r = &row[i * 8];
                if (!((r[j >> 6] >> (j & 63)) & 1)) { r[j >> 6] |= 1ULL << (j & 63); q->monomials++; }
            }
        }
    }
}
static void qmap_eval(const qmap_t *q, const uint64_t x[8], uint8_t out[KEY_BYTES]) {
    memset(out, 0, KEY_BYTES);
    int setbits[512], ns = 0;
    for (int i = 0; i < 512; i++) if (bitget(x, i)) setbits[ns++] = i;
    for (int e = 0; e < M_EQ; e++) {
        int acc = q->cst[e] ^ parity8(&q->lin[e * 8], x);
        const uint64_t *row = &q->rows[(size_t)e * 512 * 8];
        for (int k = 0; k < ns; k++) acc ^= parity8(&row[setbits[k] * 8], x);
        if (acc) out[e >> 3] |= 1 << (e & 7);
    }
}

/* --------------------------------------------------- registry / frame ---- */
typedef struct { gf s, r; } opening_t;
typedef struct {
    uint8_t keys[N_SEATS][KEY_BYTES];
    opening_t open[N_SEATS];             /* secrets (demo only) */
    uint8_t cfg[64];
    uint8_t domain[64];
} registry_t;

static void opening_to_x(const opening_t *o, uint64_t x[8]) {
    for (int k = 0; k < 4; k++) { x[k] = o->s.v[k]; x[4 + k] = o->r.v[k]; }
}
static void registry_build(registry_t *R, const qmap_t *q, const uint8_t rseed[32]) {
    shake_t c; shake_label(&c, "CQ50/reg"); shake_absorb(&c, rseed, 32);
    for (int i = 0; i < N_SEATS; i++) {
        uint8_t buf[64]; shake_squeeze(&c, buf, 64);
        R->open[i].s = gf_from_bytes(buf); R->open[i].r = gf_from_bytes(buf + 32);
        uint64_t x[8]; opening_to_x(&R->open[i], x);
        qmap_eval(q, x, R->keys[i]);
    }
    shake_t h; shake_label(&h, "CQ50/cfg"); shake_absorb(&h, q->seed, 32);
    shake_absorb(&h, R->keys, sizeof R->keys); shake_squeeze(&h, R->cfg, 64);
    for (int i = 0; i < 64; i++) R->domain[i] = (uint8_t)i;
}
/* v1.50 linearized handle. The message challenge is a triple (c_a, c_b, c_c) and
 * L_c(s) = c_a s + c_b s^2 + c_c s^4 (F2-linear in s). The public counter ctr is
 * the smallest one making L_c invertible (expected ~3 tries), so s = L_c^-1(t)
 * is a function of t = Z + r^7 inside the circuit. Z = r^7 + L_c(s). Suppressing
 * extraction by a challenge collision now needs c_a, c_b, c_c to collide: 768 bits
 * (v1.49 cryptanalysis item 1). */
typedef struct { gf a, b, c; uint32_t ctr; gf cols[256]; gf inv[256]; } chal_t;

static gf lin_apply(const chal_t *ch, gf s) {
    gf s2 = gf_mul(s, s), s4 = gf_mul(s2, s2);
    return gf_add(gf_add(gf_mul(ch->a, s), gf_mul(ch->b, s2)), gf_mul(ch->c, s4));
}
static void cols_to_rows(const gf cols[256], gf rows[256]) {
    for (int k = 0; k < 256; k++) {
        rows[k] = GF0;
        for (int j = 0; j < 256; j++) if (gf_bit(cols[j], k)) rows[k].v[j >> 6] |= 1ULL << (j & 63);
    }
}
/* Gauss-Jordan over F2; rows[k] bit j = M[k][j]. Returns 1 with inverse rows. */
static int gf2_invert256(const gf rows_in[256], gf inv_rows[256]) {
    gf rows[256], inv[256];
    for (int k = 0; k < 256; k++) { rows[k] = rows_in[k]; inv[k] = GF0; inv[k].v[k >> 6] = 1ULL << (k & 63); }
    for (int col = 0; col < 256; col++) {
        int piv = -1;
        for (int r = col; r < 256; r++) if (gf_bit(rows[r], col)) { piv = r; break; }
        if (piv < 0) return 0;
        if (piv != col) { gf t = rows[piv]; rows[piv] = rows[col]; rows[col] = t; t = inv[piv]; inv[piv] = inv[col]; inv[col] = t; }
        for (int r = 0; r < 256; r++)
            if (r != col && gf_bit(rows[r], col)) { rows[r] = gf_add(rows[r], rows[col]); inv[r] = gf_add(inv[r], inv[col]); }
    }
    for (int k = 0; k < 256; k++) inv_rows[k] = inv[k];
    return 1;
}
static void challenge_c(const registry_t *R, const uint8_t m[64], chal_t *ch) {
    for (uint32_t ctr = 0;; ctr++) {
        shake_t c; shake_label(&c, "CQ50/c");
        shake_absorb(&c, R->cfg, 64); shake_absorb(&c, R->domain, 64); shake_absorb(&c, m, 64);
        uint8_t cb[4]; be32(cb, ctr); shake_absorb(&c, cb, 4);
        uint8_t buf[96]; shake_squeeze(&c, buf, 96);
        ch->a = gf_from_bytes(buf); ch->b = gf_from_bytes(buf + 32); ch->c = gf_from_bytes(buf + 64); ch->ctr = ctr;
        for (int j = 0; j < 256; j++) ch->cols[j] = lin_apply(ch, XPOW[j]);
        gf rows[256]; cols_to_rows(ch->cols, rows);
        if (gf2_invert256(rows, ch->inv)) return;
    }
}
static gf handle_of(const opening_t *o, const chal_t *ch) { return gf_add(gf_pow7(o->r), lin_apply(ch, o->s)); }

/* Solve M s = rhs over F2 with M given by columns; enumerate up to 4 solutions
 * (kernel dimension <= 2 unless all three challenge coefficients collide). */
static int solve_lin(const gf dcols[256], gf rhs, gf sols[4]) {
    gf rows[256]; cols_to_rows(dcols, rows);
    int rhsb[256], pivcol[256], is_piv[256] = {0}, rank = 0;
    for (int k = 0; k < 256; k++) rhsb[k] = gf_bit(rhs, k);
    for (int col = 0; col < 256 && rank < 256; col++) {
        int piv = -1;
        for (int r = rank; r < 256; r++) if (gf_bit(rows[r], col)) { piv = r; break; }
        if (piv < 0) continue;
        if (piv != rank) { gf t = rows[piv]; rows[piv] = rows[rank]; rows[rank] = t; int tb = rhsb[piv]; rhsb[piv] = rhsb[rank]; rhsb[rank] = tb; }
        for (int r = 0; r < 256; r++)
            if (r != rank && gf_bit(rows[r], col)) { rows[r] = gf_add(rows[r], rows[rank]); rhsb[r] ^= rhsb[rank]; }
        pivcol[rank] = col; is_piv[col] = 1; rank++;
    }
    for (int r = rank; r < 256; r++) if (rhsb[r]) return 0;
    int nfree = 256 - rank; if (nfree > 2) return 0;
    int freec[2], nf = 0;
    for (int col = 0; col < 256; col++) if (!is_piv[col]) freec[nf++] = col;
    int nsol = 0;
    for (int mask = 0; mask < (1 << nfree); mask++) {
        gf s = GF0;
        for (int i = 0; i < nfree; i++) if ((mask >> i) & 1) s.v[freec[i] >> 6] |= 1ULL << (freec[i] & 63);
        for (int r = 0; r < rank; r++) {
            int val = rhsb[r];
            for (int i = 0; i < nfree; i++) if (((mask >> i) & 1) && gf_bit(rows[r], freec[i])) val ^= 1;
            if (val) s.v[pivcol[r] >> 6] |= 1ULL << (pivcol[r] & 63);
        }
        sols[nsol++] = s;
    }
    return nsol;
}

typedef struct {
    uint8_t header[HEADER_BYTES];
    uint8_t handles[QUORUM][HANDLE_BYTES];
    int seat_at[QUORUM];                 /* prover side: seat behind each sorted handle */
    uint8_t m[64];
    uint8_t *proof; size_t proof_len;
} frame_t;

static int cmp32(const void *a, const void *b) { return memcmp(a, b, 32); }

static void frame_prepare(frame_t *f, const registry_t *R, const uint8_t m[64], const int *seats) {
    chal_t *ch = malloc(sizeof *ch); challenge_c(R, m, ch);
    uint8_t tmp[QUORUM][33];
    for (int k = 0; k < QUORUM; k++) {
        gf_to_bytes(handle_of(&R->open[seats[k]], ch), tmp[k]); tmp[k][32] = (uint8_t)seats[k];
    }
    free(ch);
    qsort(tmp, QUORUM, 33, cmp32);
    for (int k = 0; k < QUORUM; k++) { memcpy(f->handles[k], tmp[k], 32); f->seat_at[k] = tmp[k][32]; }
    memcpy(f->m, m, 64);
    f->proof = NULL; f->proof_len = 0;
}
static void frame_header(frame_t *f, const registry_t *R, uint32_t payload_len) {
    uint8_t *h = f->header;
    memcpy(h, "CQ50", 4); be16(h + 4, 50); be16(h + 6, 0x50B0);
    memcpy(h + 8, R->cfg, 64); memcpy(h + 72, R->domain, 64); memcpy(h + 136, f->m, 64);
    be16(h + 200, QUORUM); be16(h + 202, HANDLE_BYTES); be32(h + 204, payload_len);
}
static void statement_hash(const registry_t *R, const frame_t *f, uint8_t out[64]) {
    shake_t c; shake_label(&c, "CQ50/stmt");
    shake_absorb(&c, R->cfg, 64); shake_absorb(&c, R->domain, 64); shake_absorb(&c, f->m, 64);
    shake_absorb(&c, f->handles, sizeof f->handles); shake_squeeze(&c, out, 64);
}

/* --------------------------------------------------- polynomials in X ---- */
typedef struct { gf c[DEG + 1]; } poly;   /* homogeneous polys; degree known from context */

static inline void poly_mul_into(gf *acc, const gf *a, int da, const gf *b, int db, int shift) {
    for (int x = 0; x <= da; x++) {
        if (gf_iszero(a[x])) continue;
        for (int y = 0; y <= db; y++) {
            if (gf_iszero(b[y])) continue;
            acc[shift + x + y] = gf_add(acc[shift + x + y], gf_mul(a[x], b[y]));
        }
    }
}

/* ------------------------------------------------------------- params ---- */
typedef struct { int b, tau, wg, rho, threads; } params_t;

/* per-seat public data for the circuit */
typedef struct { gf inv[256]; gf Z[QUORUM]; } circ_pub_t;   /* inv[k] bit j: s_k = sum_j inv[k][j] t_j */

static void circ_pub_init(circ_pub_t *P, const chal_t *ch, const frame_t *f) {
    memcpy(P->inv, ch->inv, sizeof P->inv);
    for (int k = 0; k < QUORUM; k++) P->Z[k] = gf_from_bytes(f->handles[k]);
}

/* ---------------------------------------------------- GGM tree (prover) -- */
typedef struct {
    uint64_t u[EHW];
    uint64_t v[MAX_B][EHW];
    shake_t comhash;
    uint8_t h[64];
} rep_state_t;

static void node_children(const uint8_t node[32], uint8_t left[32], uint8_t right[32]) {
    uint8_t z = 0, o = 1;
    shake2("CQ50/node", node, 32, &z, 1, left, 32);
    shake2("CQ50/node", node, 32, &o, 1, right, 32);
}
static void leaf_process_prover(rep_state_t *S, const uint8_t leaf[32], uint32_t index, int b) {
    uint8_t com[64]; shake2("CQ50/com", leaf, 32, NULL, 0, com, 64);
    shake_absorb(&S->comhash, com, 64);
    uint64_t prg[EHW]; shake2("CQ50/prg", leaf, 32, NULL, 0, prg, EHB);
    for (int w = 0; w < EHW; w++) S->u[w] ^= prg[w];
    for (int t = 0; t < b; t++)
        if ((index >> t) & 1) for (int w = 0; w < EHW; w++) S->v[t][w] ^= prg[w];
}
static void dfs_prover(rep_state_t *S, const uint8_t node[32], int depth, uint32_t index, int b) {
    if (depth == b) { leaf_process_prover(S, node, index, b); return; }
    uint8_t l[32], r[32]; node_children(node, l, r);
    dfs_prover(S, l, depth + 1, index << 1, b);
    dfs_prover(S, r, depth + 1, (index << 1) | 1, b);
}

/* ------------------------------------------------- GGM tree (verifier) -- */
typedef struct {
    uint64_t q[MAX_B][EHW];
    shake_t comhash;
    uint8_t h[64];
    uint32_t delta;
} vrep_state_t;

static void leaf_process_verifier(vrep_state_t *S, const uint8_t leaf[32], uint32_t index, int b) {
    uint8_t com[64]; shake2("CQ50/com", leaf, 32, NULL, 0, com, 64);
    shake_absorb(&S->comhash, com, 64);
    uint64_t prg[EHW]; shake2("CQ50/prg", leaf, 32, NULL, 0, prg, EHB);
    for (int t = 0; t < b; t++)
        if (((index ^ S->delta) >> t) & 1) for (int w = 0; w < EHW; w++) S->q[t][w] ^= prg[w];
}
static void dfs_verifier(vrep_state_t *S, const uint8_t node[32], int depth, uint32_t index, int b) {
    if (depth == b) { leaf_process_verifier(S, node, index, b); return; }
    uint8_t l[32], r[32]; node_children(node, l, r);
    dfs_verifier(S, l, depth + 1, index << 1, b);
    dfs_verifier(S, r, depth + 1, (index << 1) | 1, b);
}

/* ------------------------------------------------------- QuickSilver ---- */
/* Prover: per-seat contribution to A[0..6], starting with chi2 power `cp`. */
static void qs_prover_seat(const qmap_t *q, const registry_t *R, const circ_pub_t *P, int pos,
                           const uint64_t *w, const gf *V, gf chi2, gf cp, gf A[DEG + 1]) {
    size_t base = (size_t)pos * W_SEAT;
    static __thread poly *Pw = NULL, *r2 = NULL, *r4 = NULL, *t1 = NULL, *t2 = NULL, *sp = NULL, *As = NULL;
    if (!Pw) {
        Pw = calloc(W_SEAT, sizeof(poly)); r2 = calloc(256, sizeof(poly)); r4 = calloc(256, sizeof(poly));
        t1 = calloc(256, sizeof(poly)); t2 = calloc(256, sizeof(poly)); sp = calloc(256, sizeof(poly));
        As = calloc(512, sizeof(poly));
    }
    for (int i = 0; i < W_SEAT; i++) {
        memset(&Pw[i], 0, sizeof(poly));
        Pw[i].c[0] = V[base + i];
        Pw[i].c[1] = bitget(w, base + i) ? GF1 : GF0;
    }
    /* r^2, r^4 bits: linear in r bits */
    memset(r2, 0, 256 * sizeof(poly)); memset(r4, 0, 256 * sizeof(poly));
    for (int i = 0; i < 256; i++) {
        gf x2 = XPOW[2 * i], x4 = XPOW[4 * i];
        for (int k = 0; k < 256; k++) {
            if (gf_bit(x2, k)) { r2[k].c[0] = gf_add(r2[k].c[0], Pw[i].c[0]); r2[k].c[1] = gf_add(r2[k].c[1], Pw[i].c[1]); }
            if (gf_bit(x4, k)) { r4[k].c[0] = gf_add(r4[k].c[0], Pw[i].c[0]); r4[k].c[1] = gf_add(r4[k].c[1], Pw[i].c[1]); }
        }
    }
    /* t1 = r * r^2 (degree 2): A_s = sum_{i+j=s} P_i r2_j */
    memset(As, 0, 512 * sizeof(poly));
    for (int i = 0; i < 256; i++) for (int j = 0; j < 256; j++)
        poly_mul_into(As[i + j].c, Pw[i].c, 1, r2[j].c, 1, 0);
    memset(t1, 0, 256 * sizeof(poly));
    for (int s = 0; s < 511; s++) for (int k = 0; k < 256; k++)
        if (gf_bit(XPOW[s], k)) for (int d = 0; d <= 2; d++) t1[k].c[d] = gf_add(t1[k].c[d], As[s].c[d]);
    /* t2 = t1 * r^4 (degree 3) */
    memset(As, 0, 512 * sizeof(poly));
    for (int i = 0; i < 256; i++) for (int j = 0; j < 256; j++)
        poly_mul_into(As[i + j].c, t1[i].c, 2, r4[j].c, 1, 0);
    memset(t2, 0, 256 * sizeof(poly));
    for (int s = 0; s < 511; s++) for (int k = 0; k < 256; k++)
        if (gf_bit(XPOW[s], k)) for (int d = 0; d <= 3; d++) t2[k].c[d] = gf_add(t2[k].c[d], As[s].c[d]);
    /* s_k = sum_j [CI_j]_k (t2_j + Z_j X^3)   (degree 3) */
    memset(sp, 0, 256 * sizeof(poly));
    for (int j = 0; j < 256; j++) {
        poly tj = t2[j];
        if (gf_bit(P->Z[pos], j)) tj.c[3] = gf_add(tj.c[3], GF1);
        for (int k = 0; k < 256; k++)
            if (gf_bit(P->inv[k], j)) for (int d = 0; d <= 3; d++) sp[k].c[d] = gf_add(sp[k].c[d], tj.c[d]);
    }
    /* key-map constraints, degree 6 */
    for (int e = 0; e < M_EQ; e++) {
        gf acc[DEG + 1]; memset(acc, 0, sizeof acc);
        const uint64_t *row = &q->rows[(size_t)e * 512 * 8];
        for (int i = 0; i < 512; i++) {
            const uint64_t *ri = &row[i * 8];
            const gf *ui = (i < 256) ? sp[i].c : Pw[i - 256].c; int di = (i < 256) ? 3 : 1;
            for (int wd = 0; wd < 8; wd++) {
                uint64_t bits = ri[wd];
                while (bits) {
                    int t = __builtin_ctzll(bits); bits &= bits - 1;
                    int j = 64 * wd + t;
                    const gf *uj = (j < 256) ? sp[j].c : Pw[j - 256].c; int dj = (j < 256) ? 3 : 1;
                    poly_mul_into(acc, ui, di, uj, dj, DEG - di - dj);
                }
            }
        }
        for (int i = 0; i < 512; i++) if (bitget(&q->lin[e * 8], i)) {
            const gf *ui = (i < 256) ? sp[i].c : Pw[i - 256].c; int di = (i < 256) ? 3 : 1;
            for (int d = 0; d <= di; d++) acc[DEG - di + d] = gf_add(acc[DEG - di + d], ui[d]);
        }
        if (q->cst[e]) acc[DEG] = gf_add(acc[DEG], GF1);
        for (int i2 = 0; i2 < N_SEATS; i2++) if ((R->keys[i2][e >> 3] >> (e & 7)) & 1) {
            acc[DEG - 1] = gf_add(acc[DEG - 1], Pw[256 + i2].c[0]);
            acc[DEG] = gf_add(acc[DEG], Pw[256 + i2].c[1]);
        }
        for (int d = 0; d <= DEG; d++) A[d] = gf_add(A[d], gf_mul(cp, acc[d]));
        cp = gf_mul(cp, chi2);
    }
    /* selector: sum b_i + 1 = 0 (degree 1, shifted by 5) */
    {
        gf acc[DEG + 1]; memset(acc, 0, sizeof acc);
        for (int i2 = 0; i2 < N_SEATS; i2++) {
            acc[DEG - 1] = gf_add(acc[DEG - 1], Pw[256 + i2].c[0]);
            acc[DEG] = gf_add(acc[DEG], Pw[256 + i2].c[1]);
        }
        acc[DEG] = gf_add(acc[DEG], GF1);
        for (int d = 0; d <= DEG; d++) A[d] = gf_add(A[d], gf_mul(cp, acc[d]));
    }
}

/* Verifier: per-seat contribution to C, with field values Q and Delta. */
static gf qs_verifier_seat(const qmap_t *q, const registry_t *R, const circ_pub_t *P, int pos,
                           const gf *Q, gf Delta, const gf Dp[DEG + 1], gf chi2, gf cp) {
    size_t base = (size_t)pos * W_SEAT;
    static __thread gf *qr2 = NULL, *qr4 = NULL, *qt1 = NULL, *qt2 = NULL, *qs = NULL, *Bs = NULL;
    if (!qr2) { qr2 = calloc(256, sizeof(gf)); qr4 = calloc(256, sizeof(gf)); qt1 = calloc(256, sizeof(gf));
                qt2 = calloc(256, sizeof(gf)); qs = calloc(256, sizeof(gf)); Bs = calloc(512, sizeof(gf)); }
    const gf *Qr = &Q[base];
    memset(qr2, 0, 256 * sizeof(gf)); memset(qr4, 0, 256 * sizeof(gf));
    for (int i = 0; i < 256; i++) {
        gf x2 = XPOW[2 * i], x4 = XPOW[4 * i];
        for (int k = 0; k < 256; k++) {
            if (gf_bit(x2, k)) qr2[k] = gf_add(qr2[k], Qr[i]);
            if (gf_bit(x4, k)) qr4[k] = gf_add(qr4[k], Qr[i]);
        }
    }
    memset(Bs, 0, 512 * sizeof(gf));
    for (int i = 0; i < 256; i++) for (int j = 0; j < 256; j++) Bs[i + j] = gf_add(Bs[i + j], gf_mul(Qr[i], qr2[j]));
    memset(qt1, 0, 256 * sizeof(gf));
    for (int s = 0; s < 511; s++) for (int k = 0; k < 256; k++) if (gf_bit(XPOW[s], k)) qt1[k] = gf_add(qt1[k], Bs[s]);
    memset(Bs, 0, 512 * sizeof(gf));
    for (int i = 0; i < 256; i++) for (int j = 0; j < 256; j++) Bs[i + j] = gf_add(Bs[i + j], gf_mul(qt1[i], qr4[j]));
    memset(qt2, 0, 256 * sizeof(gf));
    for (int s = 0; s < 511; s++) for (int k = 0; k < 256; k++) if (gf_bit(XPOW[s], k)) qt2[k] = gf_add(qt2[k], Bs[s]);
    memset(qs, 0, 256 * sizeof(gf));
    for (int j = 0; j < 256; j++) {
        gf tj = qt2[j];
        if (gf_bit(P->Z[pos], j)) tj = gf_add(tj, Dp[3]);
        for (int k = 0; k < 256; k++) if (gf_bit(P->inv[k], j)) qs[k] = gf_add(qs[k], tj);
    }
    gf C = GF0;
    for (int e = 0; e < M_EQ; e++) {
        gf bk[DEG + 1]; memset(bk, 0, sizeof bk);           /* buckets by degree */
        const uint64_t *row = &q->rows[(size_t)e * 512 * 8];
        for (int i = 0; i < 512; i++) {
            const uint64_t *ri = &row[i * 8];
            gf ui = (i < 256) ? qs[i] : Qr[i - 256]; int di = (i < 256) ? 3 : 1;
            for (int wd = 0; wd < 8; wd++) {
                uint64_t bits = ri[wd];
                while (bits) {
                    int t = __builtin_ctzll(bits); bits &= bits - 1;
                    int j = 64 * wd + t;
                    gf uj = (j < 256) ? qs[j] : Qr[j - 256]; int dj = (j < 256) ? 3 : 1;
                    bk[di + dj] = gf_add(bk[di + dj], gf_mul(ui, uj));
                }
            }
        }
        for (int i = 0; i < 512; i++) if (bitget(&q->lin[e * 8], i)) {
            if (i < 256) bk[3] = gf_add(bk[3], qs[i]); else bk[1] = gf_add(bk[1], Qr[i - 256]);
        }
        if (q->cst[e]) bk[0] = gf_add(bk[0], GF1);
        for (int i2 = 0; i2 < N_SEATS; i2++) if ((R->keys[i2][e >> 3] >> (e & 7)) & 1)
            bk[1] = gf_add(bk[1], Qr[256 + i2]);
        gf val = GF0;
        for (int d = 0; d <= DEG; d++) if (!gf_iszero(bk[d])) val = gf_add(val, gf_mul(bk[d], Dp[DEG - d]));
        C = gf_add(C, gf_mul(cp, val));
        cp = gf_mul(cp, chi2);
    }
    {
        gf val = GF0;
        for (int i2 = 0; i2 < N_SEATS; i2++) val = gf_add(val, Qr[256 + i2]);
        val = gf_add(gf_mul(val, Dp[DEG - 1]), Dp[DEG]);
        C = gf_add(C, gf_mul(cp, val));
    }
    (void)Delta;
    return C;
}

/* --------------------------------------------------------------- prove -- */
typedef struct { double tree, vole_hash, quicksilver, grind, total; } ptimes_t;

static size_t proof_size(const params_t *p) {
    return 64 + (size_t)(p->tau - 1) * EHB + EHB + 32 + 32 + DEG * 32 + 4 + (size_t)p->tau * (p->b * 32 + 64);
}

static int prove(const params_t *p, const qmap_t *q, const registry_t *R, frame_t *f,
                 const uint8_t rnd[32], ptimes_t *T) {
    double t0 = now();
    uint8_t stmt[64]; statement_hash(R, f, stmt);
    chal_t *ch = malloc(sizeof *ch); challenge_c(R, f->m, ch);
    circ_pub_t *P = malloc(sizeof *P); circ_pub_init(P, ch, f); free(ch);
    /* witness */
    uint64_t *w = calloc(EHW, 8);
    for (int k = 0; k < QUORUM; k++) {
        const opening_t *o = &R->open[f->seat_at[k]];
        size_t base = (size_t)k * W_SEAT;
        for (int i = 0; i < 256; i++) if (gf_bit(o->r, i)) bitset1(w, base + i);
        bitset1(w, base + 256 + f->seat_at[k]);
    }
    { uint8_t mask[MASK_BITS / 8]; shake2("CQ50/mask", rnd, 32, NULL, 0, mask, sizeof mask);
      for (int i = 0; i < MASK_BITS; i++) if ((mask[i >> 3] >> (i & 7)) & 1) bitset1(w, ELL + i); }
    /* trees and VOLEs */
    rep_state_t *S = calloc(p->tau, sizeof(rep_state_t));
    uint8_t roots[MAX_TAU][32];
    for (int j = 0; j < p->tau; j++) { uint8_t jj = (uint8_t)j; shake2("CQ50/root", rnd, 32, &jj, 1, roots[j], 32); }
#pragma omp parallel for schedule(dynamic, 1)
    for (int j = 0; j < p->tau; j++) {
        shake_label(&S[j].comhash, "CQ50/coms");
        dfs_prover(&S[j], roots[j], 0, 0, p->b);
        shake_squeeze(&S[j].comhash, S[j].h, 64);
    }
    uint8_t hcom[64];
    { shake_t hc; shake_label(&hc, "CQ50/hcom"); for (int j = 0; j < p->tau; j++) shake_absorb(&hc, S[j].h, 64); shake_squeeze(&hc, hcom, 64); }
    /* proof buffer */
    size_t plen = proof_size(p);
    uint8_t *pr = malloc(plen); size_t off = 0;
    memcpy(pr + off, hcom, 64); off += 64;
    for (int j = 1; j < p->tau; j++) { uint64_t cj[EHW]; for (int x = 0; x < EHW; x++) cj[x] = S[0].u[x] ^ S[j].u[x]; memcpy(pr + off, cj, EHB); off += EHB; }
    { uint64_t d[EHW]; for (int x = 0; x < EHW; x++) d[x] = w[x] ^ S[0].u[x]; memcpy(pr + off, d, EHB); off += EHB; }
    /* V values */
    gf *V = calloc(ELL_HAT, sizeof(gf));
    for (size_t pp = 0; pp < ELL_HAT; pp++)
        for (int j = 0; j < p->tau; j++) for (int t = 0; t < p->b; t++)
            if (bitget(S[j].v[t], pp)) { int bitpos = j * p->b + t; V[pp].v[bitpos >> 6] |= 1ULL << (bitpos & 63); }
    T->tree = now() - t0; double t1 = now();
    /* chi1 and VOLE hash */
    gf chi1 = gf_from_shake("CQ50/chi1", stmt, 64, pr, off);
    gf ut = GF0, hv = GF0, cpow = GF1;
    for (size_t pp = 0; pp < ELL; pp++) {
        if (bitget(S[0].u, pp)) ut = gf_add(ut, cpow);
        hv = gf_add(hv, gf_mul(cpow, V[pp]));
        cpow = gf_mul(cpow, chi1);
    }
    for (int t = 0; t < LAMBDA; t++) {
        if (bitget(S[0].u, ELL + t)) ut = gf_add(ut, XPOW[t]);
        hv = gf_add(hv, gf_mul(XPOW[t], V[ELL + t]));
    }
    gf_to_bytes(ut, pr + off); off += 32; gf_to_bytes(hv, pr + off); off += 32;
    T->vole_hash = now() - t1; double t2 = now();
    /* chi2 and QuickSilver */
    gf chi2 = gf_from_shake("CQ50/chi2", stmt, 64, pr, off);
    gf A[DEG + 1]; memset(A, 0, sizeof A);
    int nth = 1;
#ifdef _OPENMP
    nth = omp_get_max_threads();
#endif
    gf (*Apart)[DEG + 1] = calloc(nth, sizeof *Apart);
    uint64_t stride[4] = {(uint64_t)(M_EQ + 1), 0, 0, 0};
    gf chi_stride = gf_pow(chi2, stride);
#pragma omp parallel for schedule(dynamic, 1)
    for (int k = 0; k < QUORUM; k++) {
        int tid = 0;
#ifdef _OPENMP
        tid = omp_get_thread_num();
#endif
        uint64_t ek[4] = {(uint64_t)k, 0, 0, 0};
        gf cp = gf_pow(chi_stride, ek);
        qs_prover_seat(q, R, P, k, w, V, chi2, cp, Apart[tid]);
    }
    for (int t = 0; t < nth; t++) for (int d = 0; d <= DEG; d++) A[d] = gf_add(A[d], Apart[t][d]);
    if (!gf_iszero(A[DEG])) { fprintf(stderr, "prover: top coefficient nonzero (witness invalid)\n"); return 1; }
    gf As[DEG], Bs[DEG];                 /* masks k = 1..5 -> index k-1 */
    for (int k = 1; k < DEG; k++) {
        size_t mb = ELL + LAMBDA + (size_t)(k - 1) * LAMBDA;
        gf a = GF0, bm = GF0;
        for (int t = 0; t < LAMBDA; t++) { if (bitget(w, mb + t)) a = gf_add(a, XPOW[t]); bm = gf_add(bm, gf_mul(XPOW[t], V[mb + t])); }
        As[k] = a; Bs[k] = bm;
    }
    gf Ap[DEG];
    Ap[0] = gf_add(A[0], Bs[1]);
    for (int k = 1; k <= DEG - 2; k++) Ap[k] = gf_add(gf_add(A[k], As[k]), Bs[k + 1]);
    Ap[DEG - 1] = gf_add(A[DEG - 1], As[DEG - 1]);
    for (int k = 0; k < DEG; k++) { gf_to_bytes(Ap[k], pr + off); off += 32; }
    T->quicksilver = now() - t2; double t3 = now();
    /* chall3 with grinding */
    uint8_t base3[64]; shake2("CQ50/chi3", stmt, 64, pr, off, base3, 64);
    uint32_t ctr = 0; uint8_t h3[64];
    for (;;) {
        uint8_t cb[4]; be32(cb, ctr);
        shake2("CQ50/grind", base3, 64, cb, 4, h3, 64);
        int ok = 1;
        for (int i = 0; i < p->wg; i++) if ((h3[32 + (i >> 3)] >> (i & 7)) & 1) { ok = 0; break; }
        if (ok) break;
        ctr++;
    }
    be32(pr + off, ctr); off += 4;
    gf Delta = gf_from_bytes(h3);
    for (int t = p->tau * p->b; t < 256; t++) Delta.v[t >> 6] &= ~(1ULL << (t & 63));  /* committed bits only */
    T->grind = now() - t3;
    /* openings */
    for (int j = 0; j < p->tau; j++) {
        uint32_t dj = 0;
        for (int t = 0; t < p->b; t++) if (gf_bit(Delta, j * p->b + t)) dj |= 1u << t;
        uint8_t node[32]; memcpy(node, roots[j], 32);
        for (int lvl = 0; lvl < p->b; lvl++) {
            uint8_t l[32], r[32]; node_children(node, l, r);
            int bit = (dj >> (p->b - 1 - lvl)) & 1;
            memcpy(pr + off, bit ? l : r, 32); off += 32;
            memcpy(node, bit ? r : l, 32);
        }
        shake2("CQ50/com", node, 32, NULL, 0, pr + off, 64); off += 64;
    }
    if (off != plen) { fprintf(stderr, "internal: proof size %zu != %zu\n", off, plen); return 1; }
    f->proof = pr; f->proof_len = plen;
    T->total = now() - t0;
    free(w); free(S); free(V); free(Apart); free(P);
    return 0;
}

/* -------------------------------------------------------------- verify -- */
static int verify(const params_t *p, const qmap_t *q, const registry_t *R, const frame_t *f,
                  double *secs, const char **why) {
    double t0 = now();
    *why = "ok";
    if (f->proof_len != proof_size(p)) { *why = "proof length"; return 0; }
    for (int k = 0; k + 1 < QUORUM; k++) if (memcmp(f->handles[k], f->handles[k + 1], 32) >= 0) { *why = "handles not strictly increasing"; return 0; }
    uint8_t stmt[64]; statement_hash(R, f, stmt);
    chal_t *ch = malloc(sizeof *ch); challenge_c(R, f->m, ch);
    circ_pub_t *P = malloc(sizeof *P); circ_pub_init(P, ch, f); free(ch);
    const uint8_t *pr = f->proof; size_t off = 0;
    const uint8_t *hcom = pr; off += 64;
    const uint8_t *corr = pr + off; off += (size_t)(p->tau - 1) * EHB;
    const uint64_t *d = (const uint64_t *)(pr + off); off += EHB;
    size_t off1 = off;
    gf chi1 = gf_from_shake("CQ50/chi1", stmt, 64, pr, off1);
    gf ut = gf_from_bytes(pr + off); off += 32; gf hv = gf_from_bytes(pr + off); off += 32;
    gf chi2 = gf_from_shake("CQ50/chi2", stmt, 64, pr, off);
    gf Ap[DEG]; for (int k = 0; k < DEG; k++) { Ap[k] = gf_from_bytes(pr + off); off += 32; }
    uint8_t base3[64]; shake2("CQ50/chi3", stmt, 64, pr, off, base3, 64);
    uint8_t h3[64]; shake2("CQ50/grind", base3, 64, pr + off, 4, h3, 64); off += 4;
    for (int i = 0; i < p->wg; i++) if ((h3[32 + (i >> 3)] >> (i & 7)) & 1) { *why = "grinding condition"; return 0; }
    gf Delta = gf_from_bytes(h3);
    for (int t = p->tau * p->b; t < 256; t++) Delta.v[t >> 6] &= ~(1ULL << (t & 63));  /* committed bits only */
    /* trees */
    vrep_state_t *S = calloc(p->tau, sizeof(vrep_state_t));
    const uint8_t *openings = pr + off;
    int bad = 0;
#pragma omp parallel for schedule(dynamic, 1)
    for (int j = 0; j < p->tau; j++) {
        const uint8_t *op = openings + (size_t)j * (p->b * 32 + 64);
        uint32_t dj = 0;
        for (int t = 0; t < p->b; t++) if (gf_bit(Delta, j * p->b + t)) dj |= 1u << t;
        S[j].delta = dj;
        shake_label(&S[j].comhash, "CQ50/coms");
        /* left siblings top-down, then hidden com, then right siblings bottom-up */
        for (int lvl = 0; lvl < p->b; lvl++) {
            int bit = (dj >> (p->b - 1 - lvl)) & 1;
            if (bit == 1) { uint32_t prefix = ((dj >> (p->b - lvl)) << 1) | 0; dfs_verifier(&S[j], op + lvl * 32, lvl + 1, prefix, p->b); }
        }
        shake_absorb(&S[j].comhash, op + p->b * 32, 64);
        for (int lvl = p->b - 1; lvl >= 0; lvl--) {
            int bit = (dj >> (p->b - 1 - lvl)) & 1;
            if (bit == 0) { uint32_t prefix = ((dj >> (p->b - lvl)) << 1) | 1; dfs_verifier(&S[j], op + lvl * 32, lvl + 1, prefix, p->b); }
        }
        shake_squeeze(&S[j].comhash, S[j].h, 64);
        if (j >= 1) {
            const uint64_t *cj = (const uint64_t *)(corr + (size_t)(j - 1) * EHB);
            for (int t = 0; t < p->b; t++) if ((dj >> t) & 1) for (int x = 0; x < EHW; x++) S[j].q[t][x] ^= cj[x];
        }
    }
    uint8_t hc2[64];
    { shake_t hc; shake_label(&hc, "CQ50/hcom"); for (int j = 0; j < p->tau; j++) shake_absorb(&hc, S[j].h, 64); shake_squeeze(&hc, hc2, 64); }
    if (memcmp(hc2, hcom, 64) != 0) { *why = "commitment hash"; bad = 1; }
    off += (size_t)p->tau * (p->b * 32 + 64);
    if (off != f->proof_len) { *why = "trailing bytes"; bad = 1; }
    if (bad) { free(S); free(P); return 0; }
    /* Q values */
    gf *Qraw = calloc(ELL_HAT, sizeof(gf)), *Q = calloc(ELL_HAT, sizeof(gf));
    for (size_t pp = 0; pp < ELL_HAT; pp++) {
        gf v = GF0;
        for (int j = 0; j < p->tau; j++) for (int t = 0; t < p->b; t++)
            if (bitget(S[j].q[t], pp)) { int bp = j * p->b + t; v.v[bp >> 6] |= 1ULL << (bp & 63); }
        Qraw[pp] = v;
        Q[pp] = bitget(d, pp) ? gf_add(v, Delta) : v;
    }
    /* VOLE consistency */
    gf lhs = GF0, cpow = GF1;
    for (size_t pp = 0; pp < ELL; pp++) { lhs = gf_add(lhs, gf_mul(cpow, Qraw[pp])); cpow = gf_mul(cpow, chi1); }
    for (int t = 0; t < LAMBDA; t++) lhs = gf_add(lhs, gf_mul(XPOW[t], Qraw[ELL + t]));
    if (!gf_eq(lhs, gf_add(hv, gf_mul(Delta, ut)))) { *why = "VOLE consistency"; free(S); free(P); free(Qraw); free(Q); return 0; }
    /* QuickSilver */
    gf Dp[DEG + 1]; Dp[0] = GF1; for (int k = 1; k <= DEG; k++) Dp[k] = gf_mul(Dp[k - 1], Delta);
    int nth = 1;
#ifdef _OPENMP
    nth = omp_get_max_threads();
#endif
    gf *Cpart = calloc(nth, sizeof(gf));
    uint64_t stride[4] = {(uint64_t)(M_EQ + 1), 0, 0, 0};
    gf chi_stride = gf_pow(chi2, stride);
#pragma omp parallel for schedule(dynamic, 1)
    for (int k = 0; k < QUORUM; k++) {
        int tid = 0;
#ifdef _OPENMP
        tid = omp_get_thread_num();
#endif
        uint64_t ek[4] = {(uint64_t)k, 0, 0, 0};
        gf cp = gf_pow(chi_stride, ek);
        Cpart[tid] = gf_add(Cpart[tid], qs_verifier_seat(q, R, P, k, Q, Delta, Dp, chi2, cp));
    }
    gf C = GF0; for (int t = 0; t < nth; t++) C = gf_add(C, Cpart[t]);
    for (int k = 1; k < DEG; k++) {
        size_t mb = ELL + LAMBDA + (size_t)(k - 1) * LAMBDA;
        gf qstar = GF0;
        for (int t = 0; t < LAMBDA; t++) qstar = gf_add(qstar, gf_mul(XPOW[t], Q[mb + t]));
        C = gf_add(C, gf_mul(Dp[k - 1], qstar));
    }
    gf rhs = GF0; for (int k = 0; k < DEG; k++) rhs = gf_add(rhs, gf_mul(Ap[k], Dp[k]));
    int ok = gf_eq(C, rhs);
    if (!ok) *why = "QuickSilver check";
    free(S); free(P); free(Qraw); free(Q); free(Cpart);
    *secs = now() - t0;
    return ok;
}

/* ------------------------------------------------------------ extract -- */
static int extract(const qmap_t *q, const registry_t *R, const frame_t *f0, const frame_t *f1,
                   int seats_out[N_SEATS], double *secs) {
    double t0 = now();
    chal_t *c0 = malloc(sizeof *c0), *c1 = malloc(sizeof *c1);
    challenge_c(R, f0->m, c0); challenge_c(R, f1->m, c1);
    gf dcols[256];
    for (int j = 0; j < 256; j++) dcols[j] = gf_add(c0->cols[j], c1->cols[j]);
    int found[N_SEATS] = {0}; int nfound = 0;
    /* Never abort on the count: pair-search soundness is per seat, so every
     * identified seat is reported even if fewer than 22 are found
     * (v1.49 cryptanalysis item 2). */
#pragma omp parallel for collapse(2) schedule(dynamic, 8)
    for (int j = 0; j < QUORUM; j++) for (int k = 0; k < QUORUM; k++) {
        gf z0 = gf_from_bytes(f0->handles[j]), z1 = gf_from_bytes(f1->handles[k]);
        gf sols[4]; int ns = solve_lin(dcols, gf_add(z0, z1), sols);
        for (int si = 0; si < ns; si++) {
            gf s = sols[si];
            gf r = gf_root7(gf_add(z0, lin_apply(c0, s)));
            opening_t o = {s, r}; uint64_t x[8]; opening_to_x(&o, x);
            uint8_t y[KEY_BYTES]; qmap_eval(q, x, y);
            for (int i = 0; i < N_SEATS; i++) if (memcmp(y, R->keys[i], KEY_BYTES) == 0) {
#pragma omp critical
                { if (!found[i]) { found[i] = 1; nfound++; } }
            }
        }
    }
    free(c0); free(c1);
    int n = 0; for (int i = 0; i < N_SEATS; i++) if (found[i]) seats_out[n++] = i;
    *secs = now() - t0;
    return n;
}

/* --------------------------------------------------------------- main -- */
static void hex(const uint8_t *b, int n) { for (int i = 0; i < n; i++) printf("%02x", b[i]); }

#ifndef FUZZ_NO_MAIN
int main(int argc, char **argv) {
    params_t p = {20, 11, 16, 4096, 0};
    unsigned seed = 49; int vectors = 0, run = 0;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--vectors")) vectors = 1;
        else if (!strcmp(argv[i], "--run")) run = 1;
        else if (!strcmp(argv[i], "--b") && i + 1 < argc) p.b = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--tau") && i + 1 < argc) p.tau = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--wg") && i + 1 < argc) p.wg = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--rho") && i + 1 < argc) p.rho = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--dense")) p.rho = 0;
        else if (!strcmp(argv[i], "--seed") && i + 1 < argc) seed = (unsigned)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--threads") && i + 1 < argc) p.threads = atoi(argv[++i]);
    }
#ifdef _OPENMP
    if (p.threads > 0) omp_set_num_threads(p.threads);
#endif
    init_xpow();
    if (vectors) {
        uint8_t out[32]; shake_t c; shake_init(&c); shake_absorb(&c, "abc", 3); shake_squeeze(&c, out, 32);
        printf("{\"shake256_abc\":\""); hex(out, 32); printf("\",");
        gf x = GF0; x.v[0] = 2; gf x255 = XPOW[255]; gf pr = gf_mul(x, x255);
        printf("\"x_times_x255_low64\":\"%016llx\",", (unsigned long long)pr.v[0]);
        uint8_t ab[32] = {0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
                          0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10, 0x0f, 0x1e, 0x2d, 0x3c, 0x4b, 0x5a, 0x69, 0x78};
        uint8_t bb[32] = {0xde, 0xad, 0xbe, 0xef, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c,
                          0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c};
        gf a = gf_from_bytes(ab), b = gf_from_bytes(bb), m = gf_mul(a, b); uint8_t mb[32]; gf_to_bytes(m, mb);
        printf("\"a_times_b\":\""); hex(mb, 32); printf("\",");
        gf r7 = gf_root7(gf_pow7(a)); printf("\"root7_ok\":%d,", gf_eq(r7, a));
        gf ia = gf_mul(a, gf_inv(a)); printf("\"inv_ok\":%d}\n", gf_eq(ia, GF1));
        return 0;
    }
    if (!run) { fprintf(stderr, "usage: --run | --vectors\n"); return 2; }
    if (p.tau * p.b > 256 || p.b > MAX_B || p.tau > MAX_TAU) { fprintf(stderr, "tau*b must be <= 256, b <= %d\n", MAX_B); return 2; }
    double t0 = now();
    uint8_t mseed[32], rseed[32], rnd0[32], rnd1[32];
    { uint8_t sb[4]; be32(sb, seed); shake2("CQ50/seeds", sb, 4, NULL, 0, mseed, 32);
      shake2("CQ50/seeds", sb, 4, "r", 1, rseed, 32); shake2("CQ50/seeds", sb, 4, "0", 1, rnd0, 32); shake2("CQ50/seeds", sb, 4, "1", 1, rnd1, 32); }
    qmap_t *q = malloc(sizeof *q); qmap_init(q, mseed, p.rho);
    registry_t *R = malloc(sizeof *R); registry_build(R, q, rseed);
    double t_setup = now() - t0;
    int left[QUORUM], right[QUORUM];
    for (int k = 0; k < QUORUM; k++) left[k] = k;
    for (int k = 0; k < MIN_OVERLAP; k++) right[k] = k;
    for (int k = MIN_OVERLAP; k < QUORUM; k++) right[k] = QUORUM + (k - MIN_OVERLAP);
    uint8_t m0[64] = {0}, m1[64] = {0}; m1[63] = 0x11;
    frame_t *f0 = calloc(1, sizeof *f0), *f1 = calloc(1, sizeof *f1);
    frame_prepare(f0, R, m0, left); frame_prepare(f1, R, m1, right);
    ptimes_t T0, T1;
    if (prove(&p, q, R, f0, rnd0, &T0)) return 1;
    if (prove(&p, q, R, f1, rnd1, &T1)) return 1;
    frame_header(f0, R, (uint32_t)(QUORUM * HANDLE_BYTES + f0->proof_len));
    frame_header(f1, R, (uint32_t)(QUORUM * HANDLE_BYTES + f1->proof_len));
    size_t frame_bytes = HEADER_BYTES + QUORUM * HANDLE_BYTES + f0->proof_len;
    double v0s, v1s; const char *why0, *why1;
    int ok0 = verify(&p, q, R, f0, &v0s, &why0);
    int ok1 = verify(&p, q, R, f1, &v1s, &why1);
    /* tamper checks: flip one bit in the witness correction and in an opening */
    int tamper_rejected = 1;
    for (int which = 0; which < 3; which++) {
        frame_t *g = calloc(1, sizeof *g); memcpy(g, f0, sizeof *g);
        g->proof = malloc(f0->proof_len); memcpy(g->proof, f0->proof, f0->proof_len);
        size_t pos = which == 0 ? 64 + (size_t)(p.tau - 1) * EHB + 100 : which == 1 ? f0->proof_len - 40 : 64 + 5;
        g->proof[pos] ^= 1;
        double ts; const char *w2;
        if (verify(&p, q, R, g, &ts, &w2)) tamper_rejected = 0;
        free(g->proof); free(g);
    }
    int seats[N_SEATS]; double es;
    int n = extract(q, R, f0, f1, seats, &es);
    double total = now() - t0;
    printf("{\"params\":{\"handle\":\"r^7 + c_a s + c_b s^2 + c_c s^4 (v1.50)\",\"b\":%d,\"tau\":%d,\"wg\":%d,\"rho\":%d,\"tau_b_plus_wg\":%d,\"n_bits\":%d,\"keymap_equations\":%d,"
           "\"keymap_monomials_per_eq\":%.0f,\"ell\":%d,\"ell_hat\":%d,\"degree\":%d,\"threads\":%d},",
           p.b, p.tau, p.wg, p.rho, p.tau * p.b + p.wg, NB, M_EQ, (double)q->monomials / M_EQ, ELL, ELL_HAT, DEG,
#ifdef _OPENMP
           omp_get_max_threads()
#else
           1
#endif
           );
    printf("\"sizes\":{\"proof_bytes\":%zu,\"frame_bytes\":%zu,\"fits_32768\":%s,\"prefix_bytes\":%d,"
           "\"breakdown\":{\"h_com\":64,\"corrections\":%zu,\"witness_correction\":%d,\"vole_hash\":64,\"quicksilver\":%d,\"grind_ctr\":4,\"openings\":%zu}},",
           f0->proof_len, frame_bytes, frame_bytes <= MAX_FRAME ? "true" : "false", HEADER_BYTES + QUORUM * HANDLE_BYTES,
           (size_t)(p.tau - 1) * EHB, EHB, DEG * 32, (size_t)p.tau * (p.b * 32 + 64));
    printf("\"verified\":[%s,%s],\"reasons\":[\"%s\",\"%s\"],\"tampered_rejected\":%s,", ok0 ? "true" : "false", ok1 ? "true" : "false", why0, why1, tamper_rejected ? "true" : "false");
    printf("\"extracted_count\":%d,\"extracted_seats\":[", n);
    for (int i = 0; i < n; i++) printf("%s%d", i ? "," : "", seats[i]);
    printf("],\"seconds\":{\"setup_keymap_registry\":%.2f,\"prove_tree\":%.2f,\"prove_vole_hash\":%.2f,\"prove_quicksilver\":%.2f,"
           "\"prove_grind\":%.2f,\"prove_total\":%.2f,\"verify\":%.2f,\"extract\":%.2f,\"total\":%.2f}}\n",
           t_setup, T0.tree, T0.vole_hash, T0.quicksilver, T0.grind, T0.total, v0s, es, total);
    return (ok0 && ok1 && n == MIN_OVERLAP && tamper_rejected) ? 0 : 1;
}
#endif /* FUZZ_NO_MAIN */
