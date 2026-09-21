# QPT-128 primitives: classical attack workload curves

This tester runs real classical attacks — exhaustive search, Groebner-basis algebraic solving, collision finding, lattice reduction — against scaled-down instances of the QPT-128 primitives, and measures how the attacker's work grows with the size parameter. It cannot run any of them at production size; that is the point of the design being tested. A workload curve measured at small sizes can do two things. It can FALSIFY: if an attack's work grows polynomially where the security argument needs it to grow exponentially, that is a shortcut, and it is a finding at any size. And it can CALIBRATE: it checks that an attack costs what the record's formula says it costs, at sizes where that can be checked. It cannot VALIDATE production security. Exponential growth over the sizes measured here does not mathematically prove exponential growth at n = 256: algebraic attacks change regime as the solving degree steps up, lattice reduction is polynomial (LLL suffices) across the whole toy range, and the record's own attack lab found small-size fits mis-extrapolating by +4.6, -12.4 and -38.1 bits. It also says nothing about attacks that were not run. Every number below is labelled measured, fitted, or extrapolated, and the three are never mixed.

Campaign `full`, key-map expansion E = 300 at n = 256 (ratio 1.172), generated 2026-09-20T23:23:58+00:00.

## Findings

The controls held: the tester called the random function exponential at the known rate and caught the linear map as polynomial. The subject verdicts are therefore meaningful *for the attacks and sizes run*.
- Key map, Mode B (r^7 handle): exhaustive search over r: exponential in range, at the rate the record's formula gives (1.000).
- Key map, Mode A (linear handle): exhaustive search over r: exponential in range, at the rate the record's formula gives (1.000).
- Key map collision: the structural 'linear trick' (drawn against E): exponential in range, at the rate the record's formula gives (1.000).
- Key map collision: generic birthday search (drawn against m): exponential in range, at the rate the record's formula gives (0.500).
- Key map, Mode A: Groebner basis (PolyBoRi), r eliminated: inconclusive — neither model is clearly better (RSS exponential 2.5568, polynomial 2.5745; a verdict needs a factor of 3.0).
- Key map, Mode B: Groebner basis (PolyBoRi), quadrics + cubics: exponential in range.
- QLWR trace: primal lattice attack (fpylll BKZ, 1 thread): exponential in range.

## 1. Controls — can this tester tell exponential from polynomial?

### Control: preimage of a random function, exhaustive search

Role: control: must be exponential.

Unit of work: inputs tried. Provenance: **measured**.

| size | runs finished | mean work | log2 | median seconds | note |
|---|---|---|---|---|---|
| 8 | 64/64 | 94.94 | 6.57 | 0.000104 |  |
| 10 | 64/64 | 344.4 | 8.43 | 0.000444 |  |
| 12 | 64/64 | 1,717 | 10.75 | 0.00197 |  |
| 14 | 64/64 | 6,094 | 12.57 | 0.0094 |  |
| 16 | 64/64 | 2.418e+04 | 14.56 | 0.0282 |  |
| 18 | 64/64 | 8.202e+04 | 16.32 | 0.0809 |  |
| 20 | 64/64 | 3.849e+05 | 18.55 | 0.255 |  |

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: exponential in range** — the exponential model fits 18.4x better (RSS 0.0972 against 1.7866)
- growth rate: 0.992 bits of work per unit of size (95% interval 0.958..1.026); as a power law, degree 8.99
- agrees with the expected 1.000 — one bit of work per bit of n; mean 2^n / e (extra preimages)

### Control: preimage of a linear map, Gaussian elimination

Role: control: must be polynomial.

Unit of work: bit operations (row XORs x n). Provenance: **measured**.

| size | runs finished | mean work | log2 | median seconds | note |
|---|---|---|---|---|---|
| 16 | 3/3 | 3,072 | 11.58 | 8.69e-05 |  |
| 24 | 3/3 | 1.064e+04 | 13.38 | 0.000194 |  |
| 32 | 3/3 | 2.471e+04 | 14.59 | 0.000364 |  |
| 48 | 3/3 | 8.23e+04 | 16.33 | 0.000802 |  |
| 64 | 3/3 | 1.993e+05 | 17.60 | 0.00121 |  |
| 96 | 3/3 | 6.607e+05 | 19.33 | 0.00254 |  |
| 128 | 3/3 | 1.582e+06 | 20.59 | 0.00446 |  |
| 192 | 3/3 | 5.314e+06 | 22.34 | 0.00931 |  |
| 256 | 3/3 | 1.259e+07 | 23.59 | 0.0148 |  |

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: polynomial in range** — the polynomial model (degree 3.00) fits 10718.8x better (RSS 0.0015 against 16.4554)
- growth rate: 0.046 bits of work per unit of size (95% interval 0.031..0.062); as a power law, degree 3.00
- for comparison: O(n^3) bit operations

## 2. Subjects — measured

### Key map, Mode B (r^7 handle): exhaustive search over r

Unit of work: openings tried. Provenance: **measured**.

| size | runs finished | mean work | log2 | median seconds | note |
|---|---|---|---|---|---|
| 8 | 64/64 | 131.8 | 7.04 | 0.00169 |  |
| 10 | 64/64 | 517.3 | 9.01 | 0.00875 |  |
| 11 | 64/64 | 1,188 | 10.21 | 0.0246 |  |
| 13 | 64/64 | 4,185 | 12.03 | 0.0998 |  |
| 14 | 64/64 | 7,329 | 12.84 | 0.186 |  |
| 16 | 64/64 | 3.589e+04 | 15.13 | 1.12 |  |
| 17 | 64/64 | 6.604e+04 | 16.01 | 2.03 |  |
| 19 | 64/64 | 2.279e+05 | 17.80 | 4.42 |  |

### Key map, Mode A (linear handle): exhaustive search over r

Unit of work: openings tried. Provenance: **measured**.

| size | runs finished | mean work | log2 | median seconds | note |
|---|---|---|---|---|---|
| 8 | 64/64 | 131.8 | 7.04 | 0.000783 |  |
| 10 | 64/64 | 517.3 | 9.01 | 0.00358 |  |
| 12 | 64/64 | 2,156 | 11.07 | 0.0176 |  |
| 14 | 64/64 | 7,329 | 12.84 | 0.0687 |  |
| 16 | 64/64 | 3.589e+04 | 15.13 | 0.456 |  |
| 18 | 64/64 | 1.236e+05 | 16.92 | 1.26 |  |

### Key map collision: the structural 'linear trick' (drawn against E)

Unit of work: differences tried (one elimination each). Provenance: **measured**.

| size | runs finished | mean work | log2 | median seconds | note |
|---|---|---|---|---|---|
| 6 | 64/64 | 184 | 7.52 | 0.00211 |  |
| 8 | 64/64 | 447.4 | 8.81 | 0.00987 |  |
| 9 | 64/64 | 1,073 | 10.07 | 0.0348 |  |
| 12 | 64/64 | 6,669 | 12.70 | 0.33 |  |
| 13 | 64/64 | 1.779e+04 | 14.12 | 1.3 |  |
| 15 | 64/64 | 7.808e+04 | 16.25 | 6.6 |  |
| 16 | 64/64 | 1.294e+05 | 16.98 | 10.5 |  |

### Key map collision: generic birthday search (drawn against m)

Unit of work: evaluations of F. Provenance: **measured**.

| size | runs finished | mean work | log2 | median seconds | note |
|---|---|---|---|---|---|
| 13 | 32/32 | 118.6 | 6.89 | 0.00152 |  |
| 16 | 32/32 | 627 | 9.29 | 0.0123 |  |
| 19 | 32/32 | 1,013 | 9.98 | 0.0213 |  |
| 22 | 32/32 | 2,127 | 11.05 | 0.0585 |  |
| 25 | 32/32 | 8,316 | 13.02 | 0.404 |  |
| 32 | 32/32 | 7.24e+04 | 16.14 | 5.38 |  |
| 35 | 32/32 | 2.688e+05 | 18.04 | 15 |  |

### Key map, Mode A: Groebner basis (PolyBoRi), r eliminated

Unit of work: seconds (Groebner basis, PolyBoRi). Provenance: **measured**.

| size | runs finished | median seconds | log2 | note |
|---|---|---|---|---|
| 16 | 3/3 | 0.04195 | -4.58 |  |
| 18 | 3/3 | 0.06318 | -3.98 |  |
| 20 | 3/3 | 0.1357 | -2.88 |  |
| 22 | 3/3 | 1.135 | 0.18 |  |
| 24 | 3/3 | 2.944 | 1.56 |  |
| 26 | 3/3 | 5.348 | 2.42 |  |
| 28 | 3/3 | 8.854 | 3.15 |  |

### Key map, Mode B: Groebner basis (PolyBoRi), quadrics + cubics

Unit of work: seconds (Groebner basis, PolyBoRi). Provenance: **measured**.

| size | runs finished | median seconds | log2 | note |
|---|---|---|---|---|
| 7 | 3/3 | 0.1314 | -2.93 |  |
| 8 | 3/3 | 0.2013 | -2.31 |  |
| 10 | 3/3 | 0.9008 | -0.15 |  |
| 11 | 3/3 | 2.08 | 1.06 |  |
| 13 | 3/3 | 14.26 | 3.83 |  |
| 14 | 3/3 | 22.75 | 4.51 |  |

### QLWR trace: primal lattice attack (fpylll BKZ, 1 thread)

Unit of work: seconds (fpylll BKZ, 1 thread). Provenance: **measured**.

| size | runs finished | median seconds | log2 | note |
|---|---|---|---|---|
| 12 | 2/2 | 0.121 | -3.05 | min block size [2] |
| 16 | 2/2 | 0.3335 | -1.58 | min block size [2] |
| 20 | 2/2 | 0.8011 | -0.32 | min block size [2] |
| 24 | 2/2 | 1.581 | 0.66 | min block size [2] |
| 28 | 2/2 | 5.248 | 2.39 | min block size [2, 20] |
| 32 | 2/2 | 14.01 | 3.81 | min block size [10, 30] |
| 40 | 1/2 | 44.39 | 5.47 | dropped from the fit: no block size in the range recovered the secret min block size [30] |
| 48 | 1/2 | 201.2 | 7.65 | dropped from the fit: no block size in the range recovered the secret min block size [40] |

## 2b. Algebraic attack beside exhaustive search, as implemented here — measured and derived

Same machine, same sizes, in seconds. The record scores the linear handle (Mode A) far below the power handle (Mode B) — 148.8 against 378.2 classical bits at n = 256 — from a formula it never ran. This is that comparison, run.

**This compares two implementations, not two algorithms — read it that way.** The Groebner engine is optimised C++. The exhaustive search is this package's plain Python loop, tens of thousands of CPU cycles per opening, where an optimised enumerator (libFES-style, bit-sliced Gray code) spends a few: a factor of roughly 2^12. Applied to the table below, that factor **reverses every 'Groebner wins' row** — and the MQ estimator of the CryptographicEstimators library agrees, naming exhaustive search the cheapest attack at all of these sizes (2^31 bit operations at n = 28, against about 2^35 cycles measured for Groebner). So the 'faster' column says which *program* finished first on this machine and nothing about which attack is cheaper. What does carry over is the **growth rate** in section 3: an algebraic attack that grows by less than one bit per bit of n must overtake any exhaustive search eventually, however well optimised, and one that grows by more than one bit never will.

**What a loss for Groebner here does and does not mean.** It means *this* formulation, in *this* engine, lost. Mode B is modelled as the record models it — 2n unknowns, quadrics plus cubics — and an attacker is free to do otherwise: eliminate s and solve degree-6 equations in n unknowns, guess some bits first (hybrid), or use an F4/F5 engine faster than PolyBoRi. None of those was run, so 'exhaustive search wins' is a statement about the attack tried, not a proof that no algebraic attack on Mode B beats it.

### Mode A

Exhaustive search measured at 11.5 microseconds per opening.

| n | Groebner (C++), median s | exhaustive search (Python), mean s | search time is | finished first |
|---|---|---|---|---|
| 16 | 0.0419 | 0.45 | measured | Groebner, by 10.7x |
| 18 | 0.0632 | 1.41 | measured | Groebner, by 22.3x |
| 20 | 0.136 | 6.02 | derived (measured rate x 2^(n-1)) | Groebner, by 44.4x |
| 22 | 1.13 | 24.1 | derived (measured rate x 2^(n-1)) | Groebner, by 21.2x |
| 24 | 2.94 | 96.4 | derived (measured rate x 2^(n-1)) | Groebner, by 32.7x |
| 26 | 5.35 | 385 | derived (measured rate x 2^(n-1)) | Groebner, by 72.1x |
| 28 | 8.85 | 1.54e+03 | derived (measured rate x 2^(n-1)) | Groebner, by 174.1x |

### Mode B

Exhaustive search measured at 26.2 microseconds per opening.

| n | Groebner (C++), median s | exhaustive search (Python), mean s | search time is | finished first |
|---|---|---|---|---|
| 7 | 0.131 | 0.00168 | derived (measured rate x 2^(n-1)) | the Python search loop, by 78.3x |
| 8 | 0.201 | 0.00181 | measured | the Python search loop, by 111.1x |
| 10 | 0.901 | 0.00919 | measured | the Python search loop, by 98.0x |
| 11 | 2.08 | 0.0244 | measured | the Python search loop, by 85.3x |
| 13 | 14.3 | 0.094 | measured | the Python search loop, by 151.7x |
| 14 | 22.7 | 0.187 | measured | the Python search loop, by 121.4x |

## 3. Subjects — fitted

### Key map, Mode B (r^7 handle): exhaustive search over r

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: exponential in range** — the exponential model fits 13.0x better (RSS 0.1037 against 1.3515)
- growth rate: 0.983 bits of work per unit of size (95% interval 0.951..1.016); as a power law, degree 8.67
- agrees with the expected 1.000 — record: generic framing costs 2^(n-1) mean (attack lab FRAME experiment)

### Key map, Mode A (linear handle): exhaustive search over r

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: exponential in range** — the exponential model fits 18.8x better (RSS 0.0537 against 1.0120)
- growth rate: 0.993 bits of work per unit of size (95% interval 0.954..1.031); as a power law, degree 8.45
- agrees with the expected 1.000 — same search; the handle's form does not help a black-box attacker

### Key map collision: the structural 'linear trick' (drawn against E)

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: exponential in range** — the exponential model fits 6.8x better (RSS 0.4284 against 2.9324)
- growth rate: 0.983 bits of work per unit of size (95% interval 0.900..1.065); as a power law, degree 6.95
- agrees with the expected 1.000 — record: 2^E differences (hidden_signer_modeB_v1.46.py:582)

### Key map collision: generic birthday search (drawn against m)

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: exponential in range** — the exponential model fits 3.6x better (RSS 0.8541 against 3.0584)
- growth rate: 0.483 bits of work per unit of size (95% interval 0.430..0.537); as a power law, degree 7.48
- agrees with the expected 0.500 — sqrt(pi/2 * 2^m) evaluations for an m-bit output

### Key map, Mode A: Groebner basis (PolyBoRi), r eliminated

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: inconclusive** — neither model is clearly better (RSS exponential 2.5568, polynomial 2.5745; a verdict needs a factor of 3.0)
- growth rate: 0.722 bits of work per unit of size (95% interval 0.548..0.895); as a power law, degree 10.75
- for comparison: record scores Mode A at 148.8 classical bits at n = 256, from a formula

### Key map, Mode B: Groebner basis (PolyBoRi), quadrics + cubics

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: exponential in range** — the exponential model fits 3.5x better (RSS 0.3743 against 1.3049)
- growth rate: 1.120 bits of work per unit of size (95% interval 0.981..1.258); as a power law, degree 7.78
- for comparison: record scores Mode B at 378.2 classical bits at n = 256, from a formula

### QLWR trace: primal lattice attack (fpylll BKZ, 1 thread)

Provenance: **fitted (to measured points; not a measurement)**.

- **Verdict: exponential in range** — the exponential model fits 7.0x better (RSS 0.1426 against 1.0051)
- growth rate: 0.337 bits of work per unit of size (95% interval 0.306..0.368); as a power law, degree 4.72
- for comparison: expected polynomial across this range: LLL suffices until the block size must grow
- sizes dropped because a seed did not finish: [40, 48]
- A 'polynomial in range' verdict here is the known LLL regime, not a break.

## 4. Extrapolated to production size — not measured

Provenance of every row: **extrapolated (model-based; not measured)**. These are straight lines continued far outside the measured range. They are shown so the measured growth rate can be set beside the record's formula, and for no other purpose. **They are not security estimates.**

| track | production size | extrapolated log2 work | 95% band | warning |
|---|---|---|---|---|
| Key map, Mode B (r^7 handle): exhaustive search over r | 256 | 250.9 | 242.6..259.2 | a straight-line extrapolation across a factor of 13 in size; the record's own attack lab found fits like this off by +4.6, -12.4 and -38.1 bits |
| Key map, Mode A (linear handle): exhaustive search over r | 256 | 253.2 | 243.4..263.1 | a straight-line extrapolation across a factor of 14 in size; the record's own attack lab found fits like this off by +4.6, -12.4 and -38.1 bits |
| Key map collision: the structural 'linear trick' (drawn against E) | 300 | 296.1 | 271.4..320.8 | a straight-line extrapolation across a factor of 19 in size; the record's own attack lab found fits like this off by +4.6, -12.4 and -38.1 bits |
| Key map collision: generic birthday search (drawn against m) | 812 | 393.2 | 349.8..436.6 | a straight-line extrapolation across a factor of 23 in size; the record's own attack lab found fits like this off by +4.6, -12.4 and -38.1 bits |
| Key map, Mode B: Groebner basis (PolyBoRi), quadrics + cubics | 256 | 275.6 | 240.1..311.1 | a straight-line extrapolation across a factor of 18 in size; the record's own attack lab found fits like this off by +4.6, -12.4 and -38.1 bits |

Only tracks with an *exponential* verdict are extrapolated. A timed track's line is in log2 seconds on this machine, not in operations.
