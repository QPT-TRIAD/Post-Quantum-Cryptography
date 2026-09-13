# Inflection 2 — an exact aggregator becomes mandatory, and the target splits in two (v0.5 → v0.6 → v0.7)

**Versions concerned:** v0.6 `docs/exact-aggregator-lifting-proof.md` and v0.7
`docs/quorum-family-privacy-fork-proof.md`, both responding to v0.5 `docs/formal-proof-stack.md`.
**Date:** 8 September 2026.
**One sentence:** v0.5 showed that no naive composition meets the byte gate, v0.6 turned "find a
better backend" into a named adapter property (CET-liftability) with a lifting theorem, and v0.7
removed half the problem by showing that public signers need no conflict-extractable-tag machinery
at all.

## What v0.5 left open

v0.5 completed a paper-proof pass conditional on assumptions A1–A9 and established that
`n − f = 43` honest validators leave no room for aggregation slack: the exact aggregation path must
be exact in the knowledge-soundness sense, and the naive one is 426.13 KB (Inflection 1). But v0.5
stated the requirement in terms of *one* candidate family (threshold-ring proofs with masked tags),
which left the actual engineering question unanswered: **what property must a backend have for the
v0.5 proof stack to lift onto it?**

## The correction at v0.6 — name the missing property

v0.6's answer is a new adapter property, **CET-liftability**
(`docs/exact-aggregator-lifting-proof.md:37`), and a lifting theorem that takes it as a parameter.
The construction of the document:

1. **Remove backend-specific mask assumptions.** The mask interface is abstracted into four
   properties (`docs/exact-aggregator-lifting-proof.md:76–130`): **M1** determinism, **M2**
   auxiliary-input pseudorandomness, **M3** key binding, **M4** proof compatibility.
2. **Abstract the exact aggregate** (`:212`) and list the exact hidden-threshold proof's own
   obligations (`:261–319`): **T1** completeness, **T2** exact knowledge extraction, **T3** zero
   knowledge / quorum witness indistinguishability, **T4** public-statement binding.
3. **State CET-liftability** (`:325–435`) as seven clauses the backend's threshold proof must satisfy
   while keeping T1–T4: **L1** registry membership, **L2** authentication witness, **L3**
   trace-secret binding, **L4** mask-key binding, **L5** correct CET, **L6** aggregate
   authentication, **L7** identity distinctness.
4. **The CET-Lifting Theorem 8.1** (`:527–607`): if the backend is CET-liftable and the mask satisfies
   M1–M3, every v0.5 reduction lifts to the backend — with the proof split into F1 exact witness
   existence, F2 hidden-witness simulation, F3 public CET binding.
5. **The same-hidden-set theorem 10.1** (`:649–675`): L6 and L1–L5 must use the *same index
   variables*, which is the abstract form of the condition that the 43 handles are 43 distinct seats.
   The v1.24 relation conditions 1 and 2 (`docs/32kib-contents-contract.md:73–74`) are the modern
   spelling of this clause.
6. **An anonymity lifting theorem** (`:701+`), conditional on hypotheses H0, H1.

**Claim boundary the source states for itself**: v0.6 proves a generic lifting theorem; it "does not
prove that CTRS or any other concrete backend satisfies the new CET-liftability interface with
acceptable concrete size" (`docs/exact-aggregator-lifting-proof.md:7`). The accompanying obligation
list is `docs/ctrs-adapter-obligations-v0.6.md`.

## The correction at v0.7 — split the target

v0.7 attacks a different half of the problem: how much of the difficulty is inherent to quorum
accountability, and how much is caused by hiding the signers?

- **Structured Quorum Coverage Theorem 3.1** (`docs/quorum-family-privacy-fork-proof.md:96–120`): with
  `q = n − f`, if every admissible signer set has size at least `q` and the family `F` has full
  `f`-fault coverage, then `{V \ B : B ∈ B_f} ⊆ F`. Consequence: a family of signer sets that is
  *structured* (a fixed shape, as in structured threshold-ring schemes) can cover the quorum
  requirement only if it covers the whole fault family — which is what a "trichotomy" result then
  rules out for arbitrary-BFT faults.
- **Privacy Separation Theorem 14.1** (`:665–700`): without signer-set privacy, conflict
  accountability reduces to exact multisignature signer-set binding **plus an `n`-bit bitmap**; with
  signer-set privacy, a valid certificate must hide the quorum while retaining a latent relation
  enabling conflict-only extraction. Hence the target split:

  ```
  Target B0 = compact exact PQ multisignature + public signer bitmap
  Target B1 = compact exact PQ quorum + hidden signers + conflict-only extraction
  ```

  and the conclusion that "The current CET research solves the trace layer needed by B1. It is
  unnecessary for B0." (`:690–698`).

For a 64-seat committee the bitmap is 8 bytes, so the observation has immediate engineering weight:
do not spend a multi-kilobyte tag machinery to hide 8 bytes unless hiding is itself the requirement.

The v0.7 status table marks the two theorems **proved**, the B0 soundness/extraction/non-frameability
and BFT-composition results **proved conditionally**, and both practical backends — "Practical
<32 KiB B0 backend", "Practical <32 KiB hidden-signer B1 backend" — **open**
(`docs/quorum-family-privacy-fork-proof.md:886–899`).

## Evidence that these were corrections

- **v0.6's lifting theorem is stated with explicit hypotheses and an explicit claim boundary**
  (`docs/exact-aggregator-lifting-proof.md:7`), which is what makes it checkable at all: the seven
  L-clauses are the failure points to test for any candidate backend.
- **Checker evidence exists for the fork, and it is the kind that can fail.** v0.7 is the first
  version in the sequence with its own checker, `src/ce_qs_quorum_family_checker.py`
  (`results/ce_qs_quorum_family_checker.txt`):
  - exhaustive coverage validation and a **fault-family mutant** for `n = 4, 7, 10` — a deliberate
    construction of a signer-set family missing one admissible set, which the checker must reject;
  - the instantiated arithmetic at the target size:
    `n=64 ... combinatorial_required_columns=41107996877935680 log2=55.190269`;
  - `PASS public_bitmap_bytes=8` — the B0 cost, computed rather than asserted.
  Run: `python3 src/ce_qs_quorum_family_checker.py` (verdict `reproduced`; see `VERIFICATION.md`).
- **The mutant is the "failed before" evidence.** A family-based policy that omits one admissible
  signer set is exactly the error the trichotomy warns about; the checker refuses it, where a
  count-based rule would have accepted it.

## What changed downstream

- v0.8 (`docs/public-signer-theoretical-completion.md`) is the direct consequence of the B0 branch:
  the bitmap conjunction becomes a monotone policy `f_B`, and accountability reduces to
  monotone-policy aggregate unforgeability (Inflection 3).
- v0.9 (`docs/quantum-lift-private-wrapper-proof.md`) is the direct consequence of the B1 branch: the
  bitmap goes *inside* a zero-knowledge wrapper instead of being published.
- Every later revision of the relation keeps the L6/L1–L5 same-index condition: at v1.24 it is the
  statement that the same selector `e_{j,i}` drives all three key tables
  (`docs/32kib-contents-contract.md:87–91`), and that the 43 indices are distinct
  (`:73`).

See also: `docs/exact-aggregator-lifting-proof.md` (v0.6), `docs/ctrs-adapter-obligations-v0.6.md`
(the obligations that were never discharged), `docs/quorum-family-privacy-fork-proof.md` (v0.7),
and Inflection 3 for both branches' next step.
