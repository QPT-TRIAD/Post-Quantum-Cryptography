# CE-QS v1.1 Source and Assumption Ledger

| School / source | What it contributes | CE-QS status |
|---|---|---|
| Liu 2025/2026, *Traceability for Free* | Shows legacy TRS notions are insufficient; extended linkability/exculpability; validity-gated O(1) tracing | **Load-bearing semantics** |
| Avitabile–Botta–Fiore, Tetris 2025 | DAPT and threshold trace semantics | **Load-bearing definition precedent** |
| Feng et al., CT-RSA 2020 / DCC 2021 | PQ/QROM traceable ring signatures; logarithmic size in ring | **PQ existence evidence; strengthened-semantics adapter still required** |
| Yang–Au–Lai–Xu–Yu 2017 | LWR wPRF with efficient ZK; two-challenge identity extraction; anonymity/detectability/exculpability proof | **Concrete classical-ROM SCCH adapter pattern** |
| Boneh–Kim–Nikolaenko 2017 | First lattice PQ DAPS/PAPS | **Conditional-disclosure precedent** |
| Camenisch–Hohenberger–Lysyanskaya compact e-cash | Identify + proof/VerifyGuilt separation | **Blame-interface design** |
| Bitansky et al., STOC 2024 | Noninteractive BARG + OWF implies noninteractive computational ZK; stronger hiding implications | **Outer BatchZK existence route** |
| Feng–Tang waNIZK | Anti-framing witness authentication and identifier uniqueness | Optional local-proof strengthening |
| TripleRing+ ESORICS 2026 | Accepted paper titled *Compact Post-Quantum Traceable Ring Signatures from ML-DSA* | **Watchlist only; technical details unavailable** |
| SAC 2023 comparison | Feng lattice TRS ~138.2 KB at ring 64 in its NIST-5 comparison | Benchmark-only secondary evidence |
| Revised DDH TRS 2025/2026 | 928 B/signature at n=64; 38.97 KiB for q=43 | Classical comparison only |

## Current proof boundary

- Strong SCCH composition theorem: **conditional**
- Public `VerifyBlame` interface: **specified and compositionally proved**
- Direct strong-TRS quorum theorem: **proved conditionally**
- 2017 LWR-SCCH algebra/local-proof feasibility: **source-backed**
- Exact CE-QS adaptation of 2017 Theorem 5.2: **open**
- QROM strengthening of either 2017 LWR-SCCH or 2021 PQ TRS to the 2025 extended notions: **open**
- Concrete <32-KiB BatchZK + handle instantiation: **open**
