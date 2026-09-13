# CE-QS v1.4 Source / Architecture Ledger

| Source / school | Qualified contribution | CE-QS use |
|---|---|---|
| Ozdemir–Boneh collaborative zk-SNARKs | Generic distributed-prover compiler via MPC | Collaborative-prover theorem donor |
| Collaborative CP-NIZKs (2026) | Restates theorem: NIZK + secure-with-abort MPC prover => collaborative NIZK AoK; t-ZK; final verifier sees normal proof | **Load-bearing architecture reference** |
| Chen–Hough–El Kassem CoSNIZK 2024 | Lattice collaborative/segregated NIZK protecting TPM key from corrupt host; PQ DAA ~38 KB | **Closest PQ collaborative implementation evidence** |
| Jawale–Khurana PQ SE-NIZK | QPT base NIZK from quantum-LWE | QPT security adapter |
| Orthus CRYPTO 2026 | Practical lattice proof with sublinear verification; 9x Falcon batch-verifier improvement at 2^17 | Batch/proof backend candidate |
| Nguyen–Seiler CRYPTO 2022 | Practical sublinear lattice R1CS proof, sqrt witness scaling | Batch/proof backend candidate |
| Loquat CRYPTO 2024 | SNARK-friendly PQ signature; 145 KB recursive aggregate / 197 KB Aurora for 32 | Negative compactness benchmark |
| TripleRing 2023 | Practical Module-SIS/MLWE TRS; >=93% shorter than prior PQ TRS at ring 64 | Small-handle candidate, semantics strengthening open |
| TripleRing+ ESORICS 2026 | Accepted "Compact Post-Quantum Traceable Ring Signatures from ML-DSA" | Watchlist only |

## Reference arithmetic

- `N=64, F=21, Q=43`.
- Any Q-prover group contains at least `Q-F = 22` honest provers.
- Honest majority: `22 > 21`.
- CoSNIZK DAA benchmark: ~38 KB, which is 6.0 KiB above the project's 32-KiB gate before CE-QS handles.
- Collaborative mode final proof count: one base NIZK proof; no q-sized local proof list.

## Security / liveness split

- Safety: QPT secure-with-abort MPC is sufficient.
- Liveness option A: honest-majority MPC with guaranteed output delivery after GST.
- Liveness option B: sound identifiable abort + remove/replace culprit; at most F Byzantine abort eliminations.
- Non-identifiable abort: insufficient for liveness.

## Open concrete questions

- QPT MPC rounds/communication for the chosen direct lattice relation.
- Whether CoSNIZK/LNP or Orthus/LaZer can prove the CE-QS relation under 32 KiB.
- Compact SCCH handle instantiation with 2025-strength exculpability.
