# Audit checklist v2.1 — S1–S6

Columns: **spec** = implementation does what the specification says; **numbers** = resource claims reproduced; **attack** = adversary tries to violate the property; **bound** = the formal bound supports the claim.

## S1 — Firmware / LMS (RFC 8554, SP 800-208)

Ran 11 tests in 20.051s — ALL PASS

| ID | column | what it checks | status |
|---|---|---|---|
| S1-001 | numbers | test_S1_001_sizes_from_typecodes | PASS |
| S1-002 | spec | test_S1_002_self_roundtrip_all_ots_types | PASS |
| S1-003 | spec | test_S1_003_interop_mine_to_hsslms | PASS |
| S1-004 | spec | test_S1_004_interop_hsslms_to_mine | PASS |
| S1-005 | attack | test_S1_005_state_machine_normal_and_exhaustion | PASS |
| S1-006 | attack | test_S1_006_crash_injection_never_reuses_a_leaf | PASS |
| S1-007 | attack | test_S1_007_rollback_detected_by_hardware_counter | PASS |
| S1-008 | attack | test_S1_008_concurrent_signing_unique_leaves | PASS |
| S1-009 | attack | test_S1_009_clone_shows_why_export_is_forbidden | PASS |
| S1-010 | attack | test_S1_010_attack_game_ledger | PASS |
| S1-011 | bound | test_S1_011_grover_simulation_matches_law | PASS |

## S2 — DNSSEC (MTL ladder, multiproof, sharding)

Ran 6 tests in 88.058s — ALL PASS

| ID | column | what it checks | status |
|---|---|---|---|
| S2-001 | spec | test_S2_001_wire_encoder_is_real | PASS |
| S2-002 | numbers | test_S2_002_model_numbers_remeasured | PASS |
| S2-003 | numbers | test_S2_003_worst_case_search_realistic | PASS |
| S2-004 | attack | test_S2_004_multiproof_manipulation_games | PASS |
| S2-005 | bound | test_S2_005_binding_per_query_is_2_pow_minus_n | PASS |
| S2-006 | attack | test_S2_006_multi_target_game_prefix_matters | PASS |

## S3 — TLS 1.3 / QUIC / MTC / KEMTLS

Ran 20 tests in 1.404s — ALL PASS

| ID | column | what it checks | status |
|---|---|---|---|
| S3-001 | spec | test_S3_001_encoders | PASS |
| S3-002 | spec | test_S3_002_client_hello_and_initials | PASS |
| S3-003 | spec | test_S3_003_server_hello_spills_initial | PASS |
| S3-004 | attack | test_S3_004_x509_template | PASS |
| S3-005 | numbers | test_S3_005_mtc_certificate_bytes | PASS |
| S3-006 | bound | test_S3_006_ledger_vs_model | PASS |
| S3-007 | spec | test_S3_007_quic_and_tcp_framing | PASS |
| S3-008 | numbers | test_S3_008_kemtls_flight_shape | PASS |
| S3-009 | numbers | test_S3_009_worst_case_chain | PASS |
| S3-010 | spec | test_S3_010_positive_control | PASS |
| S3-011 | attack | test_S3_011_mitm | PASS |
| S3-012 | attack | test_S3_012_server_key_substitution | PASS |
| S3-013 | spec | test_S3_013_transcript_alteration | PASS |
| S3-014 | attack | test_S3_014_replay | PASS |
| S3-015 | attack | test_S3_015_downgrade | PASS |
| S3-016 | spec | test_S3_016_cross_server_key_confusion | PASS |
| S3-017 | attack | test_S3_017_cert_substitution | PASS |
| S3-018 | attack | test_S3_018_kem_ciphertext_substitution | PASS |
| S3-019 | numbers | test_S3_019_cpu_table | PASS |
| S3-020 | spec | test_S3_020_report_is_json | PASS |

## S4 — Constrained broadcast (TESLA + LMS anchor)

Ran 14 tests in 2.761s — ALL PASS

| ID | column | what it checks | status |
|---|---|---|---|
| S4-001 | spec | test_S4_001_wiring_benign_link_all_accepted | PASS |
| S4-002 | bound | test_S4_002_boundary_inequality_matches_every_grid_point_granular | PASS |
| S4-003 | bound | test_S4_003_boundary_inequality_matches_every_grid_point_continuous | PASS |
| S4-004 | spec | test_S4_004_loss_strands_original_not_fixed | PASS |
| S4-005 | spec | test_S4_005_bug1_reproduction | PASS |
| S4-006 | spec | test_S4_006_bug2_reproduction | PASS |
| S4-007 | attack | test_S4_007_forge | PASS |
| S4-008 | attack | test_S4_008_replay | PASS |
| S4-009 | attack | test_S4_009_late_and_exact_boundary | PASS |
| S4-010 | attack | test_S4_010_reorder_gaps_and_nonchaining_keys | PASS |
| S4-011 | spec | test_S4_011_key_relabel | PASS |
| S4-012 | attack | test_S4_012_anchor_forge_rollback_replay | PASS |
| S4-013 | spec | test_S4_013_byte_accounting | PASS |
| S4-014 | spec | test_S4_014_report_is_json | PASS |

## S5 — Smart card (BDS traversal, faults)

Ran 5 tests in 43.451s — ALL PASS

| ID | column | what it checks | status |
|---|---|---|---|
| S5-001 | attack | test_S5_001_exhaustive_h2_to_h12_all_k | PASS |
| S5-002 | attack | test_S5_002_state_manipulation | PASS |
| S5-003 | bound | test_S5_003_scaling_by_composition | PASS |
| S5-004 | attack | test_S5_004_fault_injection_every_hash | PASS |
| S5-005 | attack | test_S5_005_reduced_exhaustion | PASS |

## S6 — Migration (hybrid combiner, downgrade, ROM roots)

Ran 14 tests in 5.485s — ALL PASS

| ID | column | what it checks | status |
|---|---|---|---|
| S6-001 | attack | test_S6_001_game_a_classical_compromised_scales_as_2_pow_minus_n | PASS |
| S6-002 | attack | test_S6_002_game_b_pq_compromised_scales_as_2_pow_minus_n | PASS |
| S6-003 | attack | test_S6_003_game_c_correlated_components_negative_result | PASS |
| S6-004 | attack | test_S6_004_game_d_transcript_binding_detects_deletion | PASS |
| S6-005 | attack | test_S6_005_game_d_unbound_downgrade_succeeds_and_quantum_caveat | PASS |
| S6-006 | attack | test_S6_006_game_e_typecode_pinning_rejects_substitution | PASS |
| S6-007 | attack | test_S6_007_game_e_lax_prefix_compare_is_the_failure_mode | PASS |
| S6-008 | attack | test_S6_008_game_e_root_version_rollback | PASS |
| S6-009 | attack | test_S6_009_game_f_ledger_targets_cat5_deployed_not_passing | PASS |
| S6-010 | attack | test_S6_010_game_f_exact_gate_margins | PASS |
| S6-011 | attack | test_S6_011_composition_union_bound_same_game | PASS |
| S6-012 | bound | test_S6_012_composition_refuses_independent_layers | PASS |
| S6-013 | attack | test_S6_013_report_is_json_with_required_game_fields | PASS |
| S6-014 | spec | test_S6_014_truncwots_n32_reproduces_s4_wots | PASS |


**Totals: 70/70 tests pass.**

## Attack records

| attack id | component | game | measured | cost (log2 gates) | passes QPT-128 | assumption |
|---|---|---|---|---|---|---|
| S1-G1 | LMS n=32 | second preimage of the message hash Q = H(I||q||D_MESG||C||m) for a si | None | 146.0 |  | A-Grover, A-SHA256 |
| S1-G2 | LMS n=32 | invert one LM-OTS chain node H(I||q||i||j||.) to lower a digit | None | 146.0 |  | A-Grover, A-SHA256 |
| S1-G3 | LMS n=32 | hash collision on Q to sign two messages with one OTS leaf | None | 103.33333333333333 |  | A-Grover, A-SHA256 |
| S1-G4 | LMS n=32 | forge a Merkle path to a fresh leaf (second preimage on an interior no | None | 146.0 |  | A-Grover, A-SHA256 |
| S1-G5 | LMS n=32 | find a message whose digit vector dominates a signed one (no inversion | None | None |  | A-Grover, A-SHA256 |
| S1-G2-sim-n8 | LM-OTS chain (reduced n) | chain inversion, exact Grover | k=7 (pred 7), p=0.996846 |  |  | none (exact simulation) |
| S1-G2-sim-n10 | LM-OTS chain (reduced n) | chain inversion, exact Grover | k=17 (pred 17), p=0.999448 |  |  | none (exact simulation) |
| S1-G2-sim-n12 | LM-OTS chain (reduced n) | chain inversion, exact Grover | k=35 (pred 35), p=0.999997 |  |  | none (exact simulation) |
| S1-G2-sim-n14 | LM-OTS chain (reduced n) | chain inversion, exact Grover | k=100 (pred 100), p=1.000000 |  |  | none (exact simulation) |
| S2-MT-n=16,T=64 | MTL node hash | multi-target second preimage | unprefixed 90 (exp 97.7) / prefixed 1 (exp 1.5) per 100k queries |  |  | MM-SPR |
| S2-MT-n=16,T=256 | MTL node hash | multi-target second preimage | unprefixed 401 (exp 390.6) / prefixed 2 (exp 1.5) per 100k queries |  |  | MM-SPR |
| S2-MT-n256 | MTL node hash n=256, T=2^40 | multi-target second preimage (quantum) |  | 126.0 | False | MM-SPR, A-Grover |
| S2-MT-n256-fixed | MTL node hash n=256, prefixed | same |  | 146.0 | True | A-Grover |
| S2-WC-NXDOMAIN/realistic | DNS response size | worst-case search | 1839 B (EDNS-only (fragmentation risk)) |  |  |  |
| S2-WC-CNAME/realistic | DNS response size | worst-case search | 1513 B (EDNS-only (fragmentation risk)) |  |  |  |
| S2-WC-DNSKEY/realistic | DNS response size | worst-case search | 822 B (UDP-safe) |  |  |  |
| S2-WC-WILDCARD/realistic | DNS response size | worst-case search | 1260 B (UDP-safe (RFC 9715 1400)) |  |  |  |
| S2-WC-A/realistic | DNS response size | worst-case search | 661 B (UDP-safe) |  |  |  |
| S2-WC-NXDOMAIN/pathological | DNS response size | worst-case search | 2120 B (EDNS-only (fragmentation risk)) |  |  |  |
| S2-WC-CNAME/pathological | DNS response size | worst-case search | 3830 B (EDNS-only (fragmentation risk)) |  |  |  |
| S2-WC-DNSKEY/pathological | DNS response size | worst-case search | 912 B (UDP-safe) |  |  |  |
| S2-WC-WILDCARD/pathological | DNS response size | worst-case search | 1597 B (EDNS-only (fragmentation risk)) |  |  |  |
| S2-WC-A/pathological | DNS response size | worst-case search | 790 B (UDP-safe) |  |  |  |
| S3-POSITIVE-CONTROL | KEMTLS + MTC handshake | POSITIVE-CONTROL | HANDSHAKE COMPLETED: both accept, keys_equal=True |  |  | n/a |
| S3-MITM | KEMTLS + MTC handshake | MITM | BLOCKED: server: decrypt_error (client Finished MAC) |  |  | IND-CCA of the long-term KEM; collision  |
| S3-SERVER-KEY-SUBSTITUTION | KEMTLS + MTC handshake | SERVER-KEY-SUBSTITUTION | BLOCKED: pk_S -> pk_A, proof unchanged: client: bad_certificate (inclusion proof |  |  | second-preimage resistance of H; CA root |
| S3-TRANSCRIPT-ALTERATION | KEMTLS + MTC handshake | TRANSCRIPT-ALTERATION | BLOCKED: 13 single-field mutations across 7 messages all rejected by the receive |  |  | PRF security of HMAC-SHA3; collision res |
| S3-REPLAY | KEMTLS + MTC handshake | REPLAY | BLOCKED: forwarded to server: server: decrypt_error (client Finished MAC) | forg |  |  | IND-CCA of both KEMs; fresh client rando |
| S3-DOWNGRADE | KEMTLS + MTC handshake | DOWNGRADE | BLOCKED: delete Cat-5 group: client: illegal_parameter (selected group has no ke |  |  | collision resistance of the transcript h |
| S3-CROSS-SERVER-KEY-CONFUSION | KEMTLS + MTC handshake | CROSS-SERVER-KEY-CONFUSION | BLOCKED: client: bad_certificate (hostname not in assertion claims) |  |  | the CA only certifies names the applican |
| S3-CERT-SUBSTITUTION | KEMTLS + MTC handshake | CERT-SUBSTITUTION | BLOCKED: rogue batch, unknown trust anchor: client: unknown_ca (trust anchor id  |  |  | root distribution is authentic; second-p |
| S3-KEM-CIPHERTEXT-SUBSTITUTION | KEMTLS + MTC handshake | KEM-CIPHERTEXT-SUBSTITUTION | BLOCKED: server: decrypt_error (client Finished MAC) |  |  | IND-CCA of the ephemeral KEM; PRF securi |
| S3-WC | Certificate message | largest legal certificate | {"x509": {"form": "x509", "config": "X.509 + SQIsign-V, Cat 5", "max_certificate |  |  |  |
| S4-FORGE | TESLA broadcast | FORGE | 0/463 |  |  |  |
| S4-REPLAY | TESLA broadcast | REPLAY | 0/3 |  |  |  |
| S4-LATE | TESLA broadcast | LATE | 0/8 |  |  |  |
| S4-REORDER | TESLA broadcast | REORDER | 0/4 |  |  |  |
| S4-KEY | TESLA broadcast | KEY | 0/78 |  |  |  |
| S4-ANCHOR | TESLA broadcast | ANCHOR | 0/5 |  |  |  |
| S6-S6-A | hybrid combiner / negotiation / ROM root | IND-combined-key, classical component fully compromised | 5250/10240 |  |  | H (SHA3-256 in combine()) modelled as a  |
| S6-S6-B | hybrid combiner / negotiation / ROM root | IND-combined-key, PQ component compromised | 5372/10240 |  |  | H (SHA3-256 in combine()) modelled as a  |
| S6-S6-C | hybrid combiner / negotiation / ROM root | NEGATIVE: correlated randomness across the two components | 6144/6144 |  |  | independence of the two KEM components ( |
| S6-S6-D | hybrid combiner / negotiation / ROM root | TLS group downgrade (offer [Cat5, Cat3, classical]) | 850/7424 |  |  | HMAC-SHA3 is a PRF; the negotiated key i |
| S6-S6-E | hybrid combiner / negotiation / ROM root | ROM root configuration substitution / rollback | 8/3365 |  |  | ROM immutability (verifier code and pinn |
| S6-S6-F | hybrid combiner / negotiation / ROM root | algorithm agility ledger + QPT-128 gate margins | 0/0 |  |  | v1.43 gate accounting (2^18 gates/query) |

## Security exponents per layer (cheapest attack, production parameters, 2^18 gates/query)

| layer | cheapest game | log2 gates | passes 2^128 | source |
|---|---|---|---|---|
| S1 firmware LMS n=32 | second preimage / chain inversion (single target) | 146 | True | S1-010 |
| S1 firmware LMS n=24 (NSA-preferred) | same | 114 | False | S1-010 |
| S2 DNSSEC MTL nodes, UNPREFIXED (v2.0 as built), T=2^40 | multi-target second preimage | 126.0 | False | S2-006 |
| S2 DNSSEC MTL nodes, prefixed (fix) | second preimage | 146.0 | True | S2-006 |
| S3 TLS KEM ML-KEM-1024 | Category-5 reference attack | 148 | True | v1.43 ledger |
| S3 MTC inclusion proof (RFC 6962-style nodes, no index) | multi-target second preimage (same issue as S2-006; T = certs/batch·batches) | None | None | flagged, not measured here |
| S4 TESLA 256-bit chain | chain preimage | 146 | True | S4 report / S1-010 law |
| S4 TESLA MAC 128-bit tag | online tag guess (no offline speed-up) | None | None | per-attempt 2^-128, online only |
| S5 card LMS n=32 | = S1 | 146 | True | S1-010 |
| S6 hybrid KEM (PQ component Cat 5) | Category-5 reference attack | 148 | True | S6-010 |

## Composition

Union bound formed ONLY for: break one TLS session (confidentiality or authentication) → parts {'ephemeral KEM ML-KEM-1024': 148, 'server long-term KEM ML-KEM-1024': 148, 'MTC/transcript hash (prefixed nodes)': 146} → **2^145.42** (Pr[break] <= G * 2^-(union) in D2 units).

Refused: S1 firmware + S2 DNSSEC, S2 DNSSEC + S3 TLS, S4 TESLA + S5 card, any cross-layer sum. a union bound is defined for events in one probability space with one winning condition; the layers have different adversaries, keys and goals, so epsilon_total is NOT their sum.

## Model discrepancies (v2.0 claim → v2.1 measurement)

```json
{
 "S2": {
  "NXDOMAIN/realistic": {
   "bytes": 1839,
   "class": "EDNS-only (fragmentation risk)",
   "params": {
    "n_names": 2000,
    "label_len": 1,
    "n_labels": 3,
    "apex_len": 30,
    "n_keys": 1,
    "n_sigs": 2,
    "denial": "nsec3",
    "bitmap_windows": 2,
    "cname_len": 0,
    "shard_log2": 10
   }
  },
  "CNAME/realistic": {
   "bytes": 1513,
   "class": "EDNS-only (fragmentation risk)",
   "params": {
    "n_names": 1024,
    "label_len": 20,
    "n_labels": 3,
    "apex_len": 30,
    "n_keys": 2,
    "n_sigs": 2,
    "denial": "nsec",
    "bitmap_windows": 2,
    "cname_len": 4,
    "shard_log2": 14
   }
  },
  "DNSKEY/realistic": {
   "bytes": 822,
   "class": "UDP-safe",
   "params": {
    "n_names": 2000,
    "label_len": 1,
    "n_labels": 3,
    "apex_len": 30,
    "n_keys": 3,
    "n_sigs": 2,
    "denial": "nsec3",
    "bitmap_windows": 2,
    "cname_len": 0,
    "shard_log2": 12
   }
  },
  "WILDCARD/realistic": {
   "bytes": 1260,
   "class": "UDP-safe (RFC 9715 1400)",
   "params": {
    "n_names": 2000,
    "label_len": 20,
    "n_labels": 3,
    "apex_len": 30,
    "n_keys": 2,
    "n_sigs": 2,
    "denial": "nsec",
    "bitmap_windows": 1,
    "cname_len": 0,
    "shard_log2": 14
   }
  },
  "A/realistic": {
   "bytes": 661,
   "class": "UDP-safe",
   "params": {
    "n_names": 2000,
    "label_len": 20,
    "n_labels": 3,
    "apex_len": 30,
    "n_keys": 2,
    "n_sigs": 2,
    "denial": "nsec",
    "bitmap_windows": 1,
    "cname_len": 0,
    "shard_log2": 14
   }
  },
  "NXDOMAIN/pathological": {
   "bytes": 2120,
   "class": "EDNS-only (fragmentation risk)",
   "params": {
    "n_names": 2000,
    "label_len": 1,
    "n_labels": 4,
    "apex_len": 60,
    "n_keys": 1,
    "n_sigs": 2,
    "denial": "nsec3",
    "bitmap_windows": 3,
    "cname_len": 0,
    "shard_log2": 10
   }
  },
  "CNAME/pathological": {
   "bytes": 3830,
   "class": "EDNS-only (fragmentation risk)",
   "params": {
    "n_names": 16,
    "label_len": 63,
    "n_labels": 3,
    "apex_len": 30,
    "n_keys": 2,
    "n_sigs": 2,
    "denial": "nsec",
    "bitmap_windows": 3,
    "cname_len": 8,
    "shard_log2": 14
   }
  },
  "DNSKEY/pathological": {
   "bytes": 912,
   "class": "UDP-safe",
   "params": {
    "n_names": 2000,
    "label_len": 1,
    "n_labels": 3,
    "apex_len": 60,
    "n_keys": 3,
    "n_sigs": 2,
    "denial": "nsec3",
    "bitmap_windows": 2,
    "cname_len": 0,
    "shard_log2": 12
   }
  },
  "WILDCARD/pathological": {
   "bytes": 1597,
   "class": "EDNS-only (fragmentation risk)",
   "params": {
    "n_names": 2000,
    "label_len": 40,
    "n_labels": 4,
    "apex_len": 60,
    "n_keys": 1,
    "n_sigs": 2,
    "denial": "compact",
    "bitmap_windows": 2,
    "cname_len": 1,
    "shard_log2": 10
   }
  },
  "A/pathological": {
   "bytes": 790,
   "class": "UDP-safe",
   "params": {
    "n_names": 2000,
    "label_len": 63,
    "n_labels": 3,
    "apex_len": 30,
    "n_keys": 2,
    "n_sigs": 2,
    "denial": "nsec",
    "bitmap_windows": 1,
    "cname_len": 0,
    "shard_log2": 14
   }
  }
 },
 "S3": [
  {
   "item": "KEMTLS first flight",
   "model": "adds FINISHED=40 B",
   "measured": "no Finished in the first flight (server Finished follows the client KEM ciphertext); the client 2nd flight carries ClientKemCiphertext+Finished",
   "client_second_flight_bytes": 1626
  },
  {
   "item": "MTC + OV-V (pk in handshake)",
   "model": "449972 B",
   "measured": "NOT ENCODABLE: MTC TLSSubjectInfo.public_key is opaque<1..2^16-1>; a 446,992-B key overflows"
  },
  {
   "item": "ServerHello with hybrid ML-KEM-1024 (and X25519MLKEM768)",
   "model": "no packet count",
   "measured": "exceeds one 1,200-B Initial datagram: the server spends 2 padded Initial datagrams (2,400 B) of the 7,200-B budget on ServerHello"
  },
  {
   "item": "classical today",
   "model_server_flight": 1520,
   "exact_handshake_bytes": 1554,
   "delta": 34,
   "exact_tcp_bytes": 1653,
   "exact_quic_udp_bytes": 1708,
   "verdict_changes": []
  },
  {
   "item": "deployed hybrid (2024-26)",
   "model_server_flight": 2608,
   "exact_handshake_bytes": 2642,
   "delta": 34,
   "exact_tcp_bytes": 2741,
   "exact_quic_udp_bytes": 2847,
   "verdict_changes": []
  },
  {
   "item": "naive PQ chain, Cat 2/3",
   "model_server_flight": 16884,
   "exact_handshake_bytes": 16930,
   "delta": 46,
   "exact_tcp_bytes": 17029,
   "exact_quic_udp_bytes": 17735,
   "verdict_changes": []
  },
  {
   "item": "naive PQ chain, Cat 5",
   "model_server_flight": 30959,
   "exact_handshake_bytes": 31021,
   "delta": 62,
   "exact_tcp_bytes": 31142,
   "exact_quic_udp_bytes": 32396,
   "verdict_changes": []
  },
  {
   "item": "X.509 + SQIsign-V, Cat 5",
   "model_server_flight": 4358,
   "exact_handshake_bytes": 4416,
   "delta": 58,
   "exact_tcp_bytes": 4515,
   "exact_quic_udp_bytes": 4671,
   "verdict_changes": []
  },
  {
   "item": "MTC + ML-DSA-87, Cat 5",
   "model_server_flight": 9939,
   "exact_handshake_bytes": 9859,
   "delta": -80,
   "exact_tcp_bytes": 9958,
   "exact_quic_udp_bytes": 10364,
   "verdict_changes": []
  },
  {
   "item": "MTC + SQIsign-V, Cat 5",
   "model_server_flight": 3141,
   "exact_handshake_bytes": 3061,
   "delta": -80,
   "exact_tcp_bytes": 3160,
   "exact_quic_udp_bytes": 3266,
   "verdict_changes": []
  },
  {
   "item": "MTC + MAYO-5, Cat 5",
   "model_server_flight": 9238,
   "exact_handshake_bytes": 9158,
   "delta": -80,
   "exact_tcp_bytes": 9257,
   "exact_quic_udp_bytes": 9613,
   "verdict_changes": []
  },
  {
   "item": "MTC + KEMTLS ML-KEM-1024, Cat 5",
   "model_server_flight": 4280,
   "exact_handshake_bytes": 4148,
   "delta": -132,
   "exact_tcp_bytes": 4203,
   "exact_quic_udp_bytes": 4403,
   "verdict_changes": []
  }
 ],
 "S4": [
  "\"52 B per message\" holds for intervals i > d only; packets for i <= d carry no disclosed key and are 20 B (measured).",
  "TeslaReceiver docstring says the receiver clock \"may lead the sender by at most sync\"; the code 
```

## Untestable assumptions

- **S1**: ["A-NoExport: the private key state never leaves the hardware module (SP 800-208 \u00a78.1); S1-009 shows the consequence if it does.", "A-Grover: 2^(n/2) queries is optimal for unstructured search (BBBV 1997 lower bound \u2014 a theorem in the query model); the >= 2^18 gates/query floor is an engineering assumption.", "A-SHA256: SHA-256 truncated to n bytes behaves as a random function for (second-)preimage; no structural attack better than generic is known."]
- **S2**: ["MM-SPR of the node hash (MTL Thm 2) \u2014 measured only at n \u2264 14 bits", "resolver behaviour above 1,232/1,400 B (fragmentation/TCP fallback) is from literature, not measured here", "the batch-reference RRSIG encoding (MTL-Type 2/3) is this audit's protocol decision, not an IETF draft"]
- **S3**: {"cipher_suite": "TLS_AES_256_GCM_SHA384 (Finished 48 B) when the KEM is Category 5, else TLS_AES_128_GCM_SHA256 (32 B)", "client_hello": "SNI www.example.com, 3 suites, 5 groups, 10 sig schemes, 1 hybrid key share (X25519||ML-KEM), 32-B legacy_session_id (compat), one 32-B trust anchor id (draft-ietf-tls-trust-anchor-ids)", "x509": "DER v3: 20-B serial, 9-B algorithm OIDs (NIST arc; assumed for schemes without one), C/O/CN names, UTCTime, SKI/AKI 20 B, KU, EKU, SAN, OCSP AIA; chain = leaf + 1 intermediate; ECDSA sizes taken raw (64 B)", "mtc": "Assertion{subject_type u16, TLSSubjectInfo{scheme u16, public_key<1..2^16-1>}, Claim{dns names}} + Proof{trust_anchor<1..2^8-1> (12 B), proof_data<0..2^16-1> = index u64, landmark u32, path<0..2^16-1>}; CertificateEntry carries a trust_anchors ext with the batch id", "records": "ServerHello plaintext record, 6-B compat CCS, one AEAD record (5+1+16 B) per <=2^14-B fragment of each later message", "quic": "Initial: 30-B long header (DCID/SCID 8/8, empty token, 2-B length, 4-B pkt no) + 16-B tag; Handshake: 29 + 16; 5-B ACK frame in the first server Initial; datagrams holding an Initial are capped and padded to 1,200 B, later ones 1,252 (v4) /
- **S4**: ["Loose time synchronisation: the receiver holds a TRUE bound eps on |receiver clock - sender clock|; a violated bound is undetectable from inside the protocol and breaks the safe-packet test.", "PRF security of HMAC-SHA3-256 (truncated to 128 bits): forgery probability 2^-128 per online attempt; no offline advantage.", "One-wayness (preimage resistance) of the SHAKE256-256 chain hash: recovering K_{i+1} from K_i costs 2^256 classically / 2^128 Grover queries.", "Second-preimage resistance of the hash inside the WOTS/Merkle anchor signature and correct one-time-key state management at the signer."]
- **S5**: ["atomic persistence of the {q, bds} record (a real card must use a journaling NVM write)", "hardware SHA-256 throughput (~1 us/hash) used to convert hash counts to time"]
- **S6**: [{"assumption": "random-oracle / PRF modelling of the combiner hash (SHA3-256 in combine())", "used_by": ["S6-A", "S6-B", "S6-D"], "why_untestable": "the reduction treats H as a random oracle; no experiment on outputs can separate \"SHA3 is a PRF\" from \"SHA3 is a random oracle\" -- the games measure scaling under the model, not the model"}, {"assumption": "independence of the two KEM components (key material, randomness, implementation)", "used_by": ["S6-A", "S6-B"], "why_untestable": "S6-C shows the bound collapses when violated, but whether a deployment shares a DRBG, entropy pool or code path is a property of the implementation, not of the algorithm"}, {"assumption": "ROM immutability: verifier code, pinned typecode, root and version counter cannot be altered", "used_by": ["S6-E", "S6-F"], "why_untestable": "a mask-ROM / OTP property of the silicon; software can only assume the verifier runs as written"}, {"assumption": "ToyKEM stands in for ML-KEM-1024 / X25519; IND-CCA of ML-KEM (Module-LWE) and the v1.43 category gate costs", "used_by": ["S6-A", "S6-B", "S6-D", "S6-F"], "why_untestable": "lattice hardness and the reference attack costs are inputs from the QPT-128 ledger, no
