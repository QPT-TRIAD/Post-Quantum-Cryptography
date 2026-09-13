# CE-QS v1.5 Compactness Source Ledger

| Source / backend | Relevant fact | v1.5 interpretation |
|---|---|---|
| LaZer CCS 2024 | 1024 Falcon aggregate: 73.5 KB; 100k: 72.3 KB | Strong succinctness benchmark, above gate |
| LaZer CCS 2024 | Succinct proof system at publication time supports succinctness but not yet ZK | **Cannot directly instantiate hidden-signer CE-QS B1** |
| LaZer GitHub | Aggregate demo exposes `sig_num`; 3 witness polynomials and 1 constraint per signature | Concrete 43-relation calibration path |
| Orthus CRYPTO 2026 | Sublinear verification; ~9x verifier improvement at 2^17 Falcon signatures | Verification backend candidate; proof-size gate not established |
| CoSNIZK 2024 | Collaborative lattice privacy; ~38 KB DAA; proof size unchanged from single-prover setting | Architecture evidence, but concrete object already above 32 KiB |
| Loquat | ~197 KB Aurora / ~145 KB recursive Fractal for 32 signatures | Negative benchmark |
| Ishai–Su–Wu lattice zkSNARK | ~16 KB designated-verifier proof in large example | Byte-regime evidence; wrong public-verifier model |
| TripleRing / TripleRing+ | Candidate compact trace handle families | Need S1–S6 strengthening and exact bytes |
| v1.3/v1.4 | Final QC is E + one outer proof in both NI and CP modes | Collaborative mode saves relation complexity, not public proof multiplicity |

## Hard project gate

`43*h + P + O <= 32768`.

Screening values ignoring O:

- P=16 KiB -> h <= 381.0 B.
- P=20 KiB -> h <= 285.8 B.
- P=24 KiB -> h <= 190.5 B.
- P=28 KiB -> h <= 95.3 B.
- P=30 KiB -> h <= 47.6 B.
- h=48 B -> P <= 29.98 KiB.
- h=96 B -> P <= 27.97 KiB.
- h=256 B -> P <= 21.25 KiB.
