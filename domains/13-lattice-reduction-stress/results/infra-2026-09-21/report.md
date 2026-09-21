# PQ infrastructure program: the lattice numbers beside the estimator's

**Scope boundary.** This system cannot run BKZ or sieving at your full production dimension/modulus if those parameters are large — reduction cost grows exponentially in the block size needed, by design (that's what makes the scheme secure). What it *can* do: run the actual algorithms exactly, correctly, and completely at scaled-down dimensions, measure real empirical hardness there, and extrapolate to the full parameter set using the same cost models NIST uses for PQC categories 1–5. Any generated report must present measured and extrapolated numbers in clearly separate sections — never blend them. Nothing here is a security claim about the production parameters.

**Everything in this report is theoretical.** No lattice was built or reduced: these are the estimator's analytic costs at full scale. Core-SVP under-counts an attack's cost, and the record's floors are gate counts, so each comparison below errs toward the attacker.

## The record's table is a category floor, not a lattice cost

Stated at: pq_infra_s6_migration_agility_v2.0.py:50 (CATEGORY_ATTACK_GATES); pq_audit_ledger_v2.1.py:151,156,166 (148 as 'ML-KEM-1024'); attributed to the v1.43 finalization, which does not contain the table.

| category | record, log2 gates | decodes as |
|---|---|---|
| 1 | 83 | 64 + 19  (Grover on AES-128) |
| 2 | 100 | — |
| 3 | 116 | 96 + 20  (Grover on AES-192) |
| 5 | 148 | 128 + 20 (Grover on AES-256) |

## Estimator cost of the best known lattice attack — theoretical

| scheme | cat | β usvp | β dual | classical log2 | quantum log2 | record floor | margin (bits) | ≥ floor | ≥ 2^128 budget | judged on |
|---|---|---|---|---|---|---|---|---|---|---|
| ML-KEM-512 | 1 | 406 | 424 | 118.55 | 107.59 | 83 | 24.59 | True | False | quantum core-SVP |
| ML-KEM-768 | 3 | 624 | 648 | 182.21 | 165.36 | 116 | 49.36 | True | True | quantum core-SVP |
| ML-KEM-1024 | 5 | 874 | 904 | 255.21 | 231.61 | 148 | 83.61 | True | True | quantum core-SVP |
| ML-DSA-44 | 2 | — | — | 152.16 | — | 100 | 52.16 | True | True | classical only - this estimator path reports no quantum figure |
| ML-DSA-65 | 3 | — | — | 211.49 | — | 116 | 95.49 | True | True | classical only - this estimator path reports no quantum figure |
| ML-DSA-87 | 5 | — | — | 288.21 | — | 148 | 140.21 | True | True | classical only - this estimator path reports no quantum figure |

Cost models: ADPS16(classical/quantum), estimator default shape; SIS default. Estimator revision 53da59825977.
