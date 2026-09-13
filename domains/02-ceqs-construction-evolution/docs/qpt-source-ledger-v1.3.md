# CE-QS v1.3 QPT / Source Ledger

| Component | Proof/source basis | v1.3 status |
|---|---|---|
| LWR wPRF pseudorandomness | Yang et al. Theorem 4.1 says reduction is direct from LWR | **QPT conditional on QLWR** |
| wPRF uniqueness | Yang et al. statistical counting proof; displayed bound <= nu/2^nu | **information-theoretically quantum-safe** |
| wPRF one-wayness | Yang et al. Lemma F.1, straight-line two-sample reduction | **QPT conditional on QLWR + uniqueness** |
| Local proof | Jawale–Khurana Cor. 4.4: post-quantum simulation-extractable adaptive multi-theorem NIZK for NP from quantum LWE | **QPT closed conditionally** |
| Outer proof | Same generic PQ SE-NIZK for NP | **QPT theoretical existence closed** |
| Topic bases | Pre-sampled bounded CRS matrices | **no QRO in theorem** |
| Challenge | 384-bit QCR hash, injective base-p encoding | **QPT conditional on QCRH** |
| Vote signature | Any QEUF-CMA PQ signature | adapter |
| Hidden threshold | Outer NIZK + QEUF signatures | **conditionally proved** |
| Public anonymity | Outer QPT ZK + QLWR handle hybrid | **conditionally proved** |
| Cross-key trace soundness | local extraction + statistical uniqueness | **conditionally proved** |
| Extended no-split | registry/base uniqueness | **conditionally proved** |
| Extended exculpability | SE extraction + uniqueness + QPT wPRF one-wayness + QCRH | **conditionally proved** |
| BFT f+1 extraction | quorum intersection + trace correctness | **conditionally proved** |
| Full hidden sidecar-free QPT CE-QS | Theorem 26.1 | **theoretical existence conditionally closed** |
| <32 KiB certificate | handle list + outer proof | **OPEN** |
| Base CRS practical size | polynomial but potentially large | **OPEN engineering issue** |

## New compactness candidates

- Tran et al. 2026/1885: compact standard-model lattice NIZK for set membership, logarithmic in set cardinality; useful for registry-membership subrelations, not a full batch-NP proof.
- Orthus (CRYPTO 2026 / ePrint 2026/398): practical succinct lattice proofs with sublinear verification; serious batch-layer implementation candidate.
- LaZer / LaBRADOR: transparent/native module-lattice ZK stack; candidate if both vote and handle relations are lattice-native.
- Ishai–Su–Wu: ~16 KB designated-verifier lattice zkSNARK benchmark; proves the byte regime is achievable under designated verification, not sufficient for public transferable QCs.
- Florentz-Konopnicki–Rothblum CRYPTO 2026: black-box OWF ZK has improved communication but retains a leading witness-size term; does not close CE-QS compactness.
