# CE-QS v0.5 Proof-Driven Corrections

1. **ELBA naming:** v0.4 must say ELBA (Expanded ALBA), not ALBA, for the CCS 2025 tagged-signature aggregation layer.

2. **43-of-64 ELBA liveness claim:** the statement "any positive ELBA slack forces >43 contributions" is too strong.
   - ELBA may use `n_f=42`, `n_p=43`.
   - This is theoretically complete with exactly 43 contributions.
   - The practical problem is proof size: equation (13) gives `u >= 3991` at 128/128 security.
   - With the paper's 9.91 KB linkable AES128 signature at ring size 64, the naive Telescope-style proof is about 38.6 MiB.

3. **Exact VOLEitH concatenation:**
   - 43 × 9.91 KB = 426.13 KB (~0.416 MiB).
   - Therefore the exact Figure-8 threshold-ring baseline is sidecar-free but not compact enough for the project's 32-KiB gate.

4. **New missing link:**
   - exact compact anonymous PQ aggregation with witness extraction and CET binding;
   - GC-TRS/CTRS is the strongest published family currently identified for this slot.

5. **Proof status:**
   - R1 one-tag hiding: written;
   - R2 anonymity: written;
   - R3 registered-key trace soundness / non-frameability: written for registration-first classical ROM;
   - R4 post-exposure authentication security: written;
   - QROM-specific R3 remains open.
