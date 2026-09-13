# PRIMITIVES layer: ML-DSA-87 (FIPS 204) / ML-KEM-1024 (FIPS 203) cross-validation
Generated 2026-09-13T03:34:15Z, Linux-7.0.0-31-generic-x86_64-with-glibc2.39, Python 3.12.3, runtime 24.7 s. Machine-readable detail (every failing test id) is in results.json.
**Scope: this layer validates the PQ primitives only. It does NOT validate the QPT-128 construction, its encodings, aggregation, or quorum logic.**
## Implementations and vectors
- liboqs 0.16.0 tag 0.16.0 commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`; ML-DSA-87 = FIPS204 (mldsa-native, x86_64), ML-KEM-1024 = FIPS203 (mlkem-native, x86_64); own ctypes wrapper `oqs_ctypes.py` (no `oqs` pip package).
- dilithium-py 1.4.0 (`dilithium_py.ml_dsa`, final FIPS 204; round-3 Dilithium is a separate module) and kyber-py 1.2.0 (`kyber_py.ml_kem`, final FIPS 203). Seeded keygen via `key_derive(seed)`.
- NIST ACVP-Server internalProjection.json for ML-DSA keyGen/sigVer/sigGen and ML-KEM keyGen/encapDecap, full files, all ML-DSA-87 / ML-KEM-1024 groups (commit + sha256 in vectors/SOURCE.txt).
- liboqs seeded ops: `OQS_KEM_keypair_derand`/`encaps_derand` AVAILABLE; `OQS_SIG_keypair_derand` NOT AVAILABLE in 0.16.0, so ML-DSA seed / rnd were injected through `OQS_randombytes_custom_algorithm` (call count asserted).
## (a) ACVP keyGen: seed -> (pk, sk) byte-exact
| Set | vectors | pure-Python pass/fail | liboqs pass/fail |
|---|---|---|---|
| ML-DSA-87 | 25 | dilithium-py 25/0 | 25/0 |
| ML-KEM-1024 | 25 | kyber-py 25/0 | 25/0 |
## (b) ACVP sigVer ML-DSA-87: verdict == testPassed (n/a = interface not exposed by liboqs public API)
| Interface | tgId | vectors (valid/invalid) | liboqs agree/disagree/n-a | dilithium-py agree/disagree/n-a | same verdict |
|---|---|---|---|---|---|
| external/pure | 5 | 15 (3/12) | 15/0/0 | 15/0/0 | 15/15 |
| external/preHash (HashML-DSA-87) | 6 | 15 (3/12) | 0/0/15 | 15/0/0 | 0/0 |
| internal/externalMu | 11 | 15 (3/12) | 0/0/15 | 15/0/0 | 0/0 |
| internal/raw M' | 12 | 15 (3/12) | 0/0/15 | 15/0/0 | 0/0 |
## (b') ACVP sigGen ML-DSA-87: regenerated signature == vector (deterministic: rnd = 0^32; hedged: vector rnd)
| Interface | tgIds | vectors | liboqs pass/fail/n-a | dilithium-py pass/fail/n-a |
|---|---|---|---|---|
| external/pure | 5,17 | 30 | 30/0/0 | 30/0/0 |
| external/preHash (HashML-DSA-87) | 6,18 | 30 | 0/0/30 | 30/0/0 |
| internal/externalMu | 11,23 | 30 | 0/0/30 | 30/0/0 |
| internal/raw M' | 12,24 | 30 | 0/0/30 | 30/0/0 |
## (c) ACVP encapDecap ML-KEM-1024 (decapsulation group includes 'modified ciphertext' implicit-rejection cases)
| Function | tgId | vectors | reasons | liboqs pass/fail | kyber-py pass/fail |
|---|---|---|---|---|---|
| encapsulation | 3 | 25 | - 25 | 25/0 | 25/0 |
| decapsulation | 6 | 10 | modified ciphertext 5, valid decapsulation 5 | 10/0 | 10/0 |
| decapsulationKeyCheck | 11 | 10 | modified H 5, valid decapsulation key 5 | 10/0 | 10/0 |
| encapsulationKeyCheck | 12 | 10 | valid encapsulation key 5, noisy linear system values too large 5 | 10/0 | 10/0 |
## (d) Cross-implementation: 200 random messages (random ctx 0-16 B) and 200 random keypairs, keys alternately from each side
| Direction | pass | fail | Direction | pass | fail |
|---|---|---|---|---|---|
| liboqs sign -> dilithium-py verify | 200 | 0 | dilithium-py sign -> liboqs verify | 200 | 0 |
| liboqs encaps -> kyber-py decaps | 200 | 0 | kyber-py encaps -> liboqs decaps | 200 | 0 |
Sizes checked on every object: ML-DSA-87 pk 2592 / sk 4896 / sig 4627; ML-KEM-1024 ek 1568 / dk 3168 / ct 1568 / ss 32 -> ALL as expected.
## (e) Failure behaviour: one byte XOR-flipped at 50 random positions per target
| Target | liboqs | dilithium-py / kyber-py | cross-impl agreement |
|---|---|---|---|
| dsa_signature | rejected 50, accepted 0 | rejected 50, accepted 0 | both reject |
| dsa_public_key | rejected 50, accepted 0 | rejected 50, accepted 0 | both reject |
| kem_ciphertext | different key 50, same key 0 | different key 50, same key 0 | identical implicit-rejection key 50/50 |
| kem_public_key | ek rejected 10, different key 40, same key 0 | ek rejected 10, different key 40, same key 0 | same validity verdict 50/50 |
## (f) Timing: median ms (informational only; single core, Python-driven; NOT a benchmark)
- liboqs: dsa_keygen 0.063, dsa_sign 0.108, dsa_verify 0.059, kem_keygen 0.025, kem_encaps 0.027, kem_decaps 0.02
- dilithium-py: dsa_keygen 9.278, dsa_sign 38.175, dsa_verify 10.688; kyber-py: kem_keygen 3.171, kem_encaps 4.083, kem_decaps 5.267
## Findings
- Harness negative control: one corrupted vector per ACVP group was flagged by 27/27 exercised (table, implementation) pairs (none missed).
- CRITICAL findings: none. No implementation accepted a tampered signature or public key.
- Disagreements: none. liboqs, dilithium-py and kyber-py agree with each other and with every NIST ACVP ML-DSA-87 / ML-KEM-1024 vector above; no test case id to report.
- Restated: this is a primitives-only result. Correct ML-DSA-87 / ML-KEM-1024 primitives are necessary, not sufficient, for QPT-128; the construction is validated by the other layers of the audit stack.
