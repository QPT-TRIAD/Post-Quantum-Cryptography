# CE-QS v1.0 Assumption and Proof Ledger

| Component | Required property | Current status |
|---|---|---|
| Auth signature | QEUF-CMA, registered-key binding | Standard PQ signature adapter available |
| Trace-tag primitive | TT1–TT5: key validity, trace completeness, cross-key soundness, pseudorandomness, non-frameability | Abstract; Tetris supplies exact classical definitions |
| Local TagZK | PQ completeness, soundness, zero knowledge | PQ NIZK existence from LWE is known; concrete circuit open |
| Outer BatchZK | PQ soundness + ZK + succinct proof | Theoretical BARG→NIZK route exists; concrete bytes open |
| Same-set binding | B3–B5 use same hidden identity tuple | Proved in v1.0 relation |
| BFT intersection | 2q-n=f+1 | Closed |
| Linear CET one-tag hiding | QPRF hybrid | Conditional |
| Linear CET false trace | QROM affine-claw resistance | **Open** |
| Generic quantum collision/claw screen | ~2^(kappa/3) | Motivates kappa=384 |
| 384-bit tag payload | 43 × 48 B = 2064 B (2.016 KiB) | Closed arithmetic |
| Generic DAPT trace checks | q^2 n = 118,336 at 64/43 | Closed arithmetic |
| Final certificate size | 2064 B + |BatchZK proof| + O(lambda) | Proof bytes open |
| Collector privacy | Collector knows signer identities | Explicitly not claimed |
| Public signer privacy | BatchZK + tag pseudorandomness | Conditionally proved |
