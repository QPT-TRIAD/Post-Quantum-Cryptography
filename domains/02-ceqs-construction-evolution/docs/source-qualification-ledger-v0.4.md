# CE-QS v0.4 Source Qualification Ledger

| Source | Venue/status | CE-QS use | Load-bearing? | Main caveat |
|---|---|---|---|---|
| Chiang et al., PQ Threshold Ring from VOLEitH | ACM CCS 2025 | hidden threshold, deterministic tags, aggregation, code base | Yes | ALBA aggregation is approximate and may require >t inputs |
| Tetris / DAPT | ESORICS 2025 | public conflict-trace semantics | Yes | classical pairing-based construction; extendability not needed |
| DAPS/PAPS | ACNS 2017 | PQ conditional disclosure precedent | Yes, as proof analogy | does not provide threshold anonymity |
| Approximate Lower Bound Arguments | EUROCRYPT 2024 | aggregation-gap analysis | Yes | gap conflicts with exact 43-of-64 BFT liveness if used as sole QC |
| Shorter, Tighter, FAESTer | CRYPTO 2025 | QROM VOLEitH Fiat-Shamir route | Yes, adaptation path | does not automatically prove CE-QS |
| GC-TRS / CTRS | DCC 2025 | exact/logarithmic fallback | Fallback | CET integration unproved |
| Rejection-free lattice TRS | CSI 2025 | exact PQ TRS fallback | Fallback | CET integration unproved |
| TAPS | CRYPTO 2022 | privacy/accountability games | Definitions | uses tracing key |
| Set-membership CP-SNARKs | DCC 2023 | large-registry fallback | No for n<=64 | extra assumptions/cost |
| Forward-secure PQ ring signatures | TCS 2026 and related | optional exposure hardening | Optional | not needed for first fixed-epoch design |
| TripleRing+ | ESORICS 2026 accepted | watchlist for compact ML-DSA traceability | No | technical paper not yet available in final form |
