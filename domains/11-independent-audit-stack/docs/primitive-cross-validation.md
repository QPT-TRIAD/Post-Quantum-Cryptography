# Primitive cross-validation: liboqs vs dilithium-py / kyber-py vs NIST ACVP

`primitives/cross_validate.py` — recorded run `primitives/RESULTS.md` + `primitives/results.json`
(2026-09-13T03:34:15Z, runtime 24.7 s). Scope statement, from the layer's own file: **"this layer
validates the PQ primitives only. It does NOT validate the QPT-128 construction, its encodings,
aggregation, or quorum logic."**

## 1. Implementations and vectors

| item | version / identity | role |
|---|---|---|
| liboqs | 0.16.0, tag 0.16.0, commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`; ML-DSA-87 = FIPS204 (mldsa-native, x86_64), ML-KEM-1024 = FIPS203 (mlkem-native, x86_64) | reference C implementation |
| `primitives/oqs_ctypes.py` | written for this layer | ctypes wrapper (the `oqs` pip package is not used) |
| dilithium-py | 1.4.0 (`dilithium_py.ml_dsa`, final FIPS 204; round-3 Dilithium is a separate module) | independent Python implementation |
| kyber-py | 1.2.0 (`kyber_py.ml_kem`, final FIPS 203) | independent Python implementation |
| NIST ACVP `internalProjection.json` | ML-DSA keyGen/sigVer/sigGen and ML-KEM keyGen/encapDecap; upstream commit `975de31eb83d87039ec88934fdc47d8c312b892d` (2026-08-12) | published test vectors |

Seeded key generation is used wherever the interface exists: `key_derive(seed)` in both Python
libraries, `OQS_KEM_keypair_derand` / `encaps_derand` in liboqs. `OQS_SIG_keypair_derand` is **not
available** in liboqs 0.16.0, so the ML-DSA seed and `rnd` are injected through
`OQS_randombytes_custom_algorithm` with the call count asserted — recorded because it is the one
place where the harness, not the library, supplies determinism.

The five vector files are **not redistributed** with this repository;
`primitives/vectors/SOURCE.txt` carries the source URL, the download time, the upstream commit and
the sha256 of each file. A re-run needs them on disk first (see
`docs/inputs-and-provenance.md` §3).

## 2. What was checked, and what matched

| check | vectors | liboqs | dilithium-py / kyber-py |
|---|---|---|---|
| (a) ACVP keyGen, seed → (pk, sk) byte-exact: ML-DSA-87 / ML-KEM-1024 | 25 + 25 | 25/0, 25/0 | 25/0, 25/0 |
| (b) ACVP sigVer ML-DSA-87, verdict == `testPassed`: external/pure (tgId 5) | 15 (3 valid / 12 invalid) | 15/0/0 | 15/0/0 |
| (b) same, external/preHash (6), internal/externalMu (11), internal/raw M' (12) | 15 each (3/12) | 0/0/15 each — **interface not exposed by the liboqs public API** | 15/0/0 each |
| (b') ACVP sigGen ML-DSA-87, regenerated signature == vector (deterministic `rnd = 0³²` and hedged) | 30 per interface | 30/0/0 external/pure; n/a on the other three | 30/0/0 on all four |
| (c) ACVP encapDecap ML-KEM-1024 (encapsulation; decapsulation incl. modified ciphertext; decapsulationKeyCheck; encapsulationKeyCheck) | 25 + 10 + 10 + 10 | 25/0, 10/0, 10/0, 10/0 | same |
| (d) cross-implementation round trips: 200 random messages (random ctx 0–16 B), 200 random keypairs with keys alternating between sides | 800 operations | liboqs sign → Python verify 200/0; liboqs encaps → Python decaps 200/0 | Python sign → liboqs verify 200/0; Python encaps → liboqs decaps 200/0 |
| (e) failure behaviour: one byte XOR-flipped at 50 random positions per target | 5 targets × 50 | dsa_signature 50 rejected / 0 accepted; dsa_public_key 50/0; kem_ciphertext 50 different-key / 0 same-key; kem_public_key 10 rejected / 40 different-key | identical verdicts in every row; implicit-rejection key identical 50/50 on kem_ciphertext |
| sizes on every object | — | ML-DSA-87 pk 2,592 / sk 4,896 / sig 4,627; ML-KEM-1024 ek 1,568 / dk 3,168 / ct 1,568 / ss 32 — all as expected | same |

**Findings: none.** No implementation accepted a tampered signature or public key; there is no
failing test id to report. Harness negative control: one deliberately corrupted vector per ACVP
group was flagged by 27/27 exercised (table, implementation) pairs.

Timings in the recorded file (median ms, informational only, single core, Python-driven, explicitly
**not a benchmark**): liboqs DSA keygen 0.063 / sign 0.108 / verify 0.059, KEM keygen 0.025 /
encaps 0.027 / decaps 0.020; dilithium-py 9.278 / 38.175 / 10.688; kyber-py 3.171 / 4.083 / 5.267.

## 3. Re-run for this repository, and what differed

Re-run in a sandbox copy (the recorded `results.json` and `RESULTS.md` were left untouched):
exit 0, `disagreements=0 critical=0`, runtime 59.2 s. Comparing the two JSON files field by field,
**40 lines differ**, all of them in four classes:

1. **Metadata** — `generated_utc`, the liboqs `.so` path (recorded as `<workdir>/…`), `runtime_s`.
2. **The liboqs identity string**: the re-run reports commit `unknown`, because the sandbox's
   liboqs build tree has no git metadata. The version tag (0.16.0) and every behavioural check are
   unaffected; the commit hash remains the recorded one, which is the value to cite.
3. **One tamper row drifts**: `kem_public_key` recorded `rejected_ek 10 / different_key 40`; the
   re-run gives `rejected_ek 9 / different_key 41` — for liboqs *and* kyber-py *together*
   (`impls_agree_on_ek_validity 50`, `impls_differ []` in both runs). The harness flips one byte at
   50 random positions and liboqs key generation in this test is unseeded, so which flipped
   encapsulation keys happen to fall outside the valid-key set varies run to run. This is a
   genuinely stochastic row, not a disagreement between implementations — both runs are kept here
   because the recorded number is not the only honest one.
4. **The timing table** — higher across the board on the re-run (e.g. dilithium-py sign 38.175 →
   87.333 ms), consistent with a loaded host. The file itself says this table is informational only.

Everything else — all ACVP verdicts, all 800 cross-operations, the other four tamper rows, the size
checks, the negative control — reproduced exactly.

## 4. What this does and does not establish

- It establishes that three independent implementations of ML-DSA-87 and ML-KEM-1024 agree with
  each other and with the published ACVP vectors on every check above, at one point in time.
- It does **not** establish that the QPT-128 construction, its encodings, its aggregation or its
  quorum logic are correct — that is what the other layers are for, and the layer says so itself.
- The ACVP coverage is the coverage of the files listed: they exercise ML-DSA external/pure,
  pre-hash, external-mu and raw-M' interfaces and the ML-KEM encapsulation/decapsulation/key-check
  groups, not every parameter set in FIPS 204/203, and not ML-DSA-44/65 (out of scope here).
- liboqs is used through a ctypes wrapper written for this layer; a defect in that wrapper would
  show up as a disagreement with the Python implementations, and none was found, but the wrapper is
  itself unaudited code.
