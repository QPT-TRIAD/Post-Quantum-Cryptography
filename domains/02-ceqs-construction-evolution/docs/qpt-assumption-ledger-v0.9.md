# CE-QS v0.9 QPT Assumption Ledger

| Component | Classical status | QPT status in this record | CE-QS consequence |
|---|---|---|---|
| Base individual signatures | standard interface | use QEUF-CMA PQ signature | not a blocker |
| Hash/local opening | classical Merkle theorem | QCRH gives QPT opening binding by straight-line collision extraction | closed conditionally |
| seBARG index hiding/extraction | used by MPA paper | exact QPT analogue not located for adaptive-subset chain | **B0 blocker** |
| 2-composable vPIR | proved classically from seBARG + local-opening hash | lifts conditionally if seBARG properties are QPT | **B0 blocker inherited from seBARG** |
| Threshold adaptive-subset BARG | Theorem 7.5 | QPT theorem not located | **B0 blocker** |
| MPA aggregate | Theorem 7.6 classical PPT game | QPT lift conditional on above | **B0 blocker** |
| Generic NIZK for NP | known from LWE | PQ simulation-extractable NIZK existence known from LWE | B1 privacy interface available |
| CET mask PRF | abstract | requires QPRF with public binding | B1 assumption |
| CET false trace | classical registration-first ROM proof | QROM/standard-model proof still open | **B1 blocker** |
| Private-wrapper succinctness | relation proved abstractly | concrete PQ proof size unknown | **B1 practical blocker** |
