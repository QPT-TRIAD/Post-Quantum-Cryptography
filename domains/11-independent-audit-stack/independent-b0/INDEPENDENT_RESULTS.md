# Independent B0 implementation vs reference vectors

Spec-only implementation `b0_indep.py`; vectors `b0_vectors.json` (900 cases).

| category | agree | disagree |
|---|---:|---:|
| cfg | 1 | 0 |
| conflict.blame | 3200 | 0 |
| conflict.encode | 800 | 0 |
| conflict.extract | 400 | 0 |
| conflict.verify | 800 | 0 |
| conflict.verify_fields | 800 | 0 |
| mutated.verify | 100 | 0 |
| other-domain.blame_all_false(spec-derived) | 100 | 0 |
| other-domain.extract | 100 | 0 |
| same-message.blame_all_false(spec-derived) | 100 | 0 |
| same-message.extract | 100 | 0 |
| trailing.verify | 100 | 0 |
| truncated.verify | 100 | 0 |
| **total** | **6701** | **0** |

## Disagreements
None. Every frame re-encoded byte-for-byte; every verify / extract / blame verdict matched.

Rejection clauses hit: mutated -> {'7.7': 93, '7.4': 7}; truncated -> {'7.3': 100}; trailing -> {'7.3': 100}
