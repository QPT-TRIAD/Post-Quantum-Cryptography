# Inflection 4 — the single-prover wrapper is rejected, and the trace abstraction is replaced (v0.9 → v1.0 → v1.1)

**Versions concerned:** v1.0 `docs/distributed-certified-tag-proof.md` and v1.1
`docs/strong-certified-conflict-handle-proof.md`.
**Date:** 9 September 2026 (the sequence crosses midnight between v0.9 and v1.0).
**One sentence:** v1.0 rejected v0.9's prover model as unbuildable for a BFT protocol and replaced it
with per-validator certified contributions, and v1.1 replaced the informal trace abstraction with a
named interface and six security games, because the classic traceable-ring notions do not imply the
properties the construction needs.

## What v0.9's wrapper assumed, and why it is not constructible

v0.9's private wrapper places the public-signer aggregate inside a zero-knowledge proof, with the
aggregate as the witness (Inflection 3). As a *specification* this is fine. As a *protocol* it
requires someone to hold every signer's private material. v1.0 states the objection in the plainest
terms the sequence uses (`docs/distributed-certified-tag-proof.md:19–27`):

> "That is not a constructible BFT protocol."
>
> "A leader/collector should receive votes, not every validator's private trace and mask secrets."

The v1.0 status table records the correction by name: "v0.9 collector-secret constructibility |
**corrected**" (`docs/distributed-certified-tag-proof.md:1077`).

## The correction at v1.0 — distributed certified contributions

v1.0 restructures the certificate so that no single party sees another party's secrets
(`docs/distributed-certified-tag-proof.md:220–484`):

1. Each validator produces a **local contribution** `C_i` containing a proof that does not hide `i`
   from the collector but reveals no trace secret to it: "No other validator and no collector
   receives `sk_i^T`" (`:270–272`).
2. The **collector** accepts `C_i` only if its local proof verifies against the registered keys
   (`:278`), and forms the canonical public tag list from exactly `q` accepted contributions
   (`:298`).
3. The collector then proves possession of `q` certified contributions (`:27–37`) — a proof about
   contributions, not about secrets.
4. The source notes the boundary: the collector is allowed to learn the identities from the network
   messages it receives; hiding voters **even from the collector** requires anonymous transport or
   MPC and is a separate property explicitly not claimed here (`:51–55`, `:599`).

The v1.0 proof stack is then conditional end to end: "Distributed signer contribution protocol —
specified"; "Collector learns no trace secret — **proved by construction**"; exact hidden threshold,
vote/tag same-hidden-set binding, public signer anonymity, conflict extraction `≥ f + 1`,
non-frameability composition and BFT accountability composition all "**proved conditionally**"
(`:1074–1090`).

The same revision carried the numeric correction that the 256-bit tag was insufficient: at 256 bits
the collision figure is ≈85.3 bits, so the tag width was raised to 384 bits — "384/3 = 128",
"384/2 = 192" — making the public tag payload `43 × 48 = 2064 bytes` for `q = 43`
(`docs/distributed-certified-tag-proof.md:999–1042`).

## The correction at v1.1 — the trace abstraction gets a name and games

v1.0's trace layer was still an informal abstraction (properties `TT1–TT5`). v1.1 replaces it with a
**Strong Certified Conflict Handle (SCCH)** interface — algorithms Setup, KeyGen, Handle,
VerifyHandle, SameSigner, TraceConflict, VerifyTrace — and six games
(`docs/strong-certified-conflict-handle-proof.md:32–41,150–253`):

| Game | Property |
|---|---|
| S1 | handle correctness |
| S2 | single-handle privacy / pseudorandomness |
| S3 | conflict trace completeness |
| S4 | cross-key trace soundness |
| S5 | extended exculpability / non-frameability |
| S6 | extended no-split / counting soundness |

The motivation is external and is stated as such: the 2025 preprint *Traceability for Free:
Traceable Ring Signatures Revisited* "identifies a gap in the classic Fujisaki–Suzuki security
notions" (`:13`) — the classic notions miss trace-specific attacks and do not imply unforgeability.
S6 is described as defence in depth, because distinct hidden validator indices already enforce
counting structurally in the v1.0 outer proof (`:253`). The public verification of a blame claim is
`VerifyBlame(QC_0, QC_1, beta_i) = 1` (`:297–341`), and the extraction targets a registered key
`pk_i^T` identified from the pair (`:378–404`).

**Claim boundary stated at v1.1**: the SCCH interface is a definition plus games; the document also
records, as cost evidence against the direct constructions, a lattice traceable ring signature at
≈5.80 MiB for 43 signatures (`:559`) and a classical DDH/Bulletproof construction at 38.97 KiB
(`:607`) — compare the 32,768-byte gate.

## Evidence that these were corrections

**v1.0 — `src/ce_qs_distributed_certified_tag_checker.py`**
(`results/ce_qs_distributed_certified_tag_checker.txt`):

```
PASS valid_distributed_relation
PASS collector_witness_contains_no_signer_secrets
EXPECTED-FAIL duplicate_hidden_identity
EXPECTED-FAIL vote_tag_identity_mismatch
EXPECTED-FAIL forged_local_tag_proof
EXPECTED-FAIL public_tag_list_mismatch
EXPECTED-FAIL below_threshold
PASS conflict_extracts_exact_intersection intersection=[0, 1, 2]
NOTE: ideal proof/signature interfaces only; no real ZK or PQ signatures.
```

The decisive line for this inflection is `PASS collector_witness_contains_no_signer_secrets`: the
property v0.9's model could not have — stated as a test on the collector's witness — is now a
checked property of the relation. `duplicate_hidden_identity` is the same-distinctness failure that
v0.2's algebra layer could not detect (see `results/ce_qs_trace_tag_simulator.txt`, mutation
"uniqueness must be enforced by the outer ZK relation, NOT by this algebra layer"); here it is
rejected by the relation itself.

**v1.1 — `src/ce_qs_strong_conflict_handle_checker.py`**
(`results/ce_qs_strong_conflict_handle_checker.txt`):

```
PASS valid_qcs
PASS exact_conflict_trace identities=[0, 1, 2]
PASS public_verify_blame
EXPECTED-FAIL false_identity_blame
EXPECTED-FAIL handle_not_bound_to_qc_signer_set
EXPECTED-FAIL duplicate_identity_threshold_evasion
PASS same_message_link_without_conflict_blame
EXPECTED-FAIL cross_key_false_trace
NOTE: ideal SCCH only; no lattice/ROM/QROM cryptography implemented.
```

Two lines carry the "failed before, passes after" evidence.

- `cross_key_false_trace` (S4) is rejected by `blocked_by=unique_link_base` in the v1.3 checker and is
  the exact failure mode that the informal `TT1–TT5` abstraction could not even *state*: a handle
  produced under one key being traced to another. Under the v1.0 abstraction there was no game in
  which to fail; under S4 there is.
- `PASS same_message_link_without_conflict_blame` is the converse property, and it is the one that
  protects honest validators: two honest approvals of the *same* message are linkable by
  construction (the link tag is message-independent) but must not produce blame. A scheme that
  conflated linkability with guilt would fail this line.
- `duplicate_identity_threshold_evasion` (S6) is the counting attack: a quorum reached by counting one
  identity many times. It is rejected here and, later, by an explicit column-occupancy equation in
  v1.24 (`docs/32kib-contents-contract.md:93–100`).

Both checkers are ideal-model mocks and say so: "no lattice/ROM/QROM cryptography implemented".

## What this inflection left behind

- The **distribution model** it introduced is still the current one: v1.24 keeps 64 logical
  participants with at most 21 corrupt or withholding, and computes one joint proof, explicitly
  noting that a 43-party protocol cannot invoke the `n > 3f` theorem
  (`docs/32kib-contents-contract.md:110–124`).
- The **tag width** it fixed (384 bits → 48-byte tags → 2064-byte public list) was superseded in
  format but not in spirit: v1.24 carries 5,504 bytes of handles because each handle pair is
  2 × 64 bytes (Inflection 8).
- The **trace games** became the obligation list that v1.2/v1.3 then had to discharge without a
  random oracle — see Inflection 5.

See also: `docs/distributed-certified-tag-proof.md` (v1.0),
`docs/strong-certified-conflict-handle-proof.md` (v1.1), and Inflection 5 for what remained
unproved in S3–S4 once the random oracle was removed.
