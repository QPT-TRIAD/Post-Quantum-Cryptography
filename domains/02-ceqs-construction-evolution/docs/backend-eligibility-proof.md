# CE-QS v1.6 — Backend Eligibility and 2026 Succinct-ZK Update
## From Open-Ended Search to a Falsifiable Compactness Test

**Status:** proof/engineering continuation from v1.5.  
**Date:** 2026-09-09.  
**Track:** hidden-signer Target \(B_1\).  
**Claim boundary:** v1.6 updates the backend landscape and defines a strict eligibility theorem. It does not claim that any current backend has passed the full 32-KiB CE-QS benchmark.

---

# 0. Main update

The 2024 statement

> "the succinct LaZer/LaBRADOR layer is not zero knowledge"

must now be treated as a **historical limitation of the 2024 artifact**, not as a statement about the current 2026 toolkit.

The current `lazer-crypto/lazer` repository contains the artifact for:

> *A Toolkit for Succinct Lattice-Based Zero Knowledge Proofs* (ePrint 2026/1289)

and pins the reproduction commit:

`59a52f74ca39584edf77b4b8b7437dbd48f9ad94`.

Its shipped succinct compression and expansion benchmarks instantiate:

`proof_statement(..., zk=zk, ...)`

and explicitly run:

`for zk in [True, False]`.

Therefore:

\[
\boxed{
\text{succinct lattice ZK is again a qualified implementation path in the 2026 toolkit.}
}
\]

This does **not** establish a CE-QS proof size.

The missing measurement is now concrete rather than conceptual.

---

# 1. Reproducibility rule

The LaZer repository contains multiple generations of artifact code.

Its README instructs:

- for the 2024 LaZer paper, check out commit  
  `10eafeca4cd53ff4fc54193dce904dbd0026fefd`;
- for the 2026 succinct-ZK toolkit, check out commit  
  `59a52f74ca39584edf77b4b8b7437dbd48f9ad94`.

Therefore no benchmark may be cited merely as "LaZer main."

Every future CE-QS benchmark record must include:

\[
\boxed{
\text{repository + exact commit + parameter file + compiler/CPU}.
}
\]

This prevents source drift from silently changing the object being measured.

---

# 2. CE-QS Backend Eligibility Interface

A backend \(P\) is eligible for the hidden-signer CE-QS production profile only if it satisfies all properties E1--E8.

## E1. Post-quantum security

The soundness/security theorem must hold against QPT adversaries, or the backend must have an explicit QPT adapter theorem accepted into the CE-QS assumption ledger.

## E2. Public transferable verification

Any third party with the public epoch configuration and QC can verify.

Designated-verifier proofs do not qualify.

## E3. Signer-witness privacy

The public transcript must provide zero knowledge or a formally sufficient witness-indistinguishability property for the CE-QS signer-anonymity game.

"Succinct" alone is insufficient.

## E4. Exact threshold / same-set binding

The proof must certify at least:

\[
Q=43
\]

distinct registered vote authorizations and bind those **same identities** to the public SCCH handle list.

Approximate threshold semantics do not qualify unless the BFT theorem is changed.

## E5. Strong conflict-handle compatibility

The backend must express or verify the SCCH S1--S6 relation, including:

- registered trace secret;
- canonical domain base;
- correct public handle;
- distinct hidden identities;
- public-list binding.

## E6. Constructible prover

No central prover may require all validator trace secrets.

Eligible realization must use either:

- v1.3 non-interactive certified contributions; or
- v1.4 collaborative distributed witness proving.

## E7. BFT liveness adapter

If proving is interactive, it must have:

- guaranteed output delivery; or
- sound identifiable abort + replacement,

under the \(F=21,Q=43\) fault model.

## E8. Byte gate

For handle bytes \(h\), proof bytes \(P\), and fixed overhead \(O\):

\[
\boxed{
43h+P+O\le32768.
}
\]

An unknown byte count means **not yet eligible**, not pass.

---

# 3. Backend Eligibility Theorem

### Theorem 3.1

If a concrete backend satisfies E1--E8, then it can instantiate the v1.3/v1.4 CE-QS theorem without changing the BFT accountability proof.

### Proof

E1--E3 supply the QPT soundness/privacy assumptions used by the outer proof.

E4 binds the exact \(Q\)-signer authorization set to the handle set.

E5 supplies the SCCH relation used by public conflict extraction and non-frameability.

E6 ensures the protocol is constructible without disclosing honest trace secrets.

E7 supplies the proof-generation liveness premise.

E8 establishes the project's compactness requirement.

The quorum theorem remains:

\[
|S_0\cap S_1|
\ge
2Q-N
=
22.
\]

No backend-specific algebra enters the BFT intersection proof.

\[
\blacksquare
\]

---

# 4. Eligibility status vocabulary

Every candidate is assigned one of:

### PASS

The requirement is supported by a source theorem or executed project measurement.

### FAIL

Published/source-measured evidence contradicts the requirement.

### OPEN

The requirement may hold but has not been established.

### EXPERIMENTAL

Only unaudited implementation claims or non-peer-reviewed benchmark assertions currently support it.

A backend is production-eligible only when **all E1--E8 are PASS**.

---

# 5. 2024 LaZer/LaBRADOR historical status

The 2024 LaZer artifact gives strong lattice proof/succinctness evidence and reported:

\[
73.5\text{ KB}
\]

for a 1024-Falcon aggregate proof.

For the hidden CE-QS profile it fails two v1.6 requirements as a direct instantiation:

- published 2024 succinct layer did not provide the required ZK property;
- the reported object is already above 32 KiB.

Therefore the 2024 artifact is:

\[
\boxed{\text{FAIL as a direct B1 backend}.}
\]

It remains valuable for baseline comparison.

---

# 6. 2026 Succinct Lattice-ZK Toolkit status

The 2026 toolkit materially changes E3.

The repository's benchmark code for both compression and expansion:

1. creates `proof_statement(..., zk=zk, ...)`;
2. loops over:
   `zk in [True, False]`;
3. executes `pack_prove()` and `pack_verify()` in both modes.

Therefore:

\[
\boxed{
E3\text{ is now source-supported at the toolkit-feature level.}
}
\]

But CE-QS still lacks:

- a 43-contribution CE-QS relation implementation;
- final proof bytes for that relation;
- measured prover/verifier cost;
- a project-reviewed QPT theorem mapping the toolkit's exact security model to E1.

Thus the toolkit is:

\[
\boxed{
\text{highest-priority OPEN backend, not yet PASS}.
}
\]

---

# 7. Source-pinned toolkit benchmark plan

The exact next experiment is:

1. check out:
   `59a52f74ca39584edf77b4b8b7437dbd48f9ad94`;
2. build the `python/succinct_zkp` artifact;
3. reproduce:
   - `benchmark_expansion.py`;
   - `benchmark_compression.py`;
4. run both:
   - `zk=True`;
   - `zk=False`;
5. record proof serialization length, not only proving/verifying time;
6. create an input dimension nearest the CE-QS relation scale;
7. then implement:
   - 43 vote-verification relations;
   - 43 SCCH relations;
   - distinctness;
   - public handle-list binding.

The artifact currently benchmarks dimensions:

\[
2^6,2^8,2^{10},2^{12},2^{14},2^{16}.
\]

Therefore \(2^6=64\) is already a useful first dimension-scale calibration near the 43-contribution target.

It is **not** equivalent to 43 CE-QS contributions.

---

# 8. Why no 43-byte estimate is inferred from toolkit dimensions

A CE-QS contribution is not one scalar input coordinate.

It contains:

- one PQ signature verification relation;
- one SCCH relation;
- registry/index constraints;
- distinctness/list-binding logic.

Therefore:

\[
\boxed{
\text{toolkit dimension }64
\neq
\text{CE-QS }43\text{-signer relation}.
}
\]

The 64-dimension benchmark is a proof-system calibration only.

A byte estimate obtained by proportional scaling would be unsupported.

---

# 9. Fusion direct-backend rejection

Fusion is a post-quantum lattice aggregate-signature family.

Its paper reports at 128-bit security approximately:

- Fusion Light aggregate:
  \[
  46.8\text{ KB};
  \]
- Fusion Mid aggregate:
  roughly 46.56 KB;
- Fusion Heavy aggregate:
  roughly 46.08 KB.

Thus even before:

- signer privacy proof;
- SCCH handles;
- CE-QS metadata,

the aggregate itself exceeds:

\[
32\text{ KiB}.
\]

Therefore:

\[
\boxed{
\text{Fusion FAILS E8 as a direct CE-QS backend at those published parameters.}
}
\]

Fusion remains useful evidence that very large signer sets can be aggregated to roughly constant tens-of-KB objects.

---

# 10. CoSNIZK status

The published collaborative lattice DAA construction reports roughly:

\[
38\text{ KB}.
\]

It has strong architectural alignment with Mode CP and signer-witness privacy.

But:

\[
38\text{ KB}>32\text{ KiB}
\]

before CE-QS handles.

Therefore the published DAA parameterization:

\[
\boxed{\text{FAILS E8}.}
\]

The framework itself remains eligible for future parameter/protocol optimization.

---

# 11. Lazarus status

The public Lazarus repository self-reports:

| relation size | proof |
|---:|---:|
| 1k gates | 28 KB |
| 10k gates | 32 KB |

These figures are interesting because:

\[
28\text{ KiB}
\]

would leave only:

\[
32768-28672
=
4096\text{ bytes}
\]

for handles + overhead.

At \(Q=43\), ignoring overhead:

\[
h_{\max}
=
4096/43
\approx
95.26\text{ bytes}.
\]

Thus a 28-KiB proof is compatible with:

- 48-byte handles;
- 64-byte handles;
- marginally 95-byte handles;

but not 96-byte handles once fixed overhead is included.

However the repository describes itself as under development and not production-audited.

No CE-QS relation has been encoded.

Therefore Lazarus is:

\[
\boxed{\text{EXPERIMENTAL, not a qualified PASS}.}
\]

---

# 12. Mutable BARG alternative

ICALP 2026 introduces mutable BARGs with privacy from standard assumptions.

Its informal results include, under LWE, mutable BARGs for monotone-policy batch-NP mutations with succinctness, soundness, and privacy.

The work also derives multi-signer signature applications, including locally verifiable aggregate signatures, from standard falsifiable assumptions.

This is relevant because CE-QS itself is a privacy-sensitive batch-NP statement over many signer witnesses.

But the paper does not provide a concrete CE-QS-sized implementation or proof byte count.

Therefore mutable BARGs are:

\[
\boxed{
\text{a theoretical B1 aggregation/privacy alternative, E8 OPEN}.
}
\]

They are especially interesting if future work tries to mutate/extract conflict-relevant information from an already-compressed batch proof rather than carry \(Q\) explicit handles.

---

# 13. Privacy-preserving aggregate signatures 2026/836

A 2026 ePrint paper titled:

> *Privacy-Preserving Aggregate-Signatures: Generic Constructions and Practical Instantiations*

by Wei, Han, and Liu is now in the literature.

This is directly relevant by title and topic.

In this proof pass, independently accessible primary technical text sufficient to establish:

- post-quantum security;
- exact signer-set privacy semantics;
- concrete size;
- compatibility with conflict tracing,

was not obtained.

Therefore it is assigned:

\[
\boxed{\text{HIGH-PRIORITY WATCHLIST / OPEN}.}
\]

No theorem in CE-QS depends on it yet.

---

# 14. Current candidate matrix

| Backend | PQ | Public verify | ZK/privacy | Exact CE relation | Constructible | <32 KiB demonstrated | Status |
|---|---|---|---|---|---|---|---|
| LaZer 2024 succinct aggregate | PASS | PASS | FAIL for B1 historical succinct layer | OPEN | PASS | FAIL | Reject direct |
| LaZer Toolkit 2026 | likely/needs exact theorem adapter | PASS | **source-feature PASS** (`zk=True`) | OPEN | PASS | OPEN | **Priority 1** |
| Orthus 2026 | PASS lattice | PASS | OPEN for CE relation | OPEN | PASS | OPEN | Priority 2 |
| CoSNIZK published DAA | PASS | PASS | PASS | OPEN | PASS collaborative | FAIL (~38 KB before handles) | Reject current params |
| Fusion | PASS | PASS | FAIL/OPEN for B1 privacy | OPEN | PASS | FAIL (~46 KB aggregate) | Reject direct |
| Lazarus | claimed lattice | claimed | claimed ZK framework | OPEN | likely | EXPERIMENTAL 28 KB @1k gates | Experimental |
| Mutable BARG | LWE theoretical | theoretical | privacy theorem | OPEN | theoretical | OPEN | Theoretical alternative |
| PP Aggregate Sig 2026/836 | OPEN in this ledger | OPEN | title suggests privacy | OPEN | OPEN | OPEN | Watchlist |

The word `PASS` in this table means only the named row property is source-supported; it does not make the whole backend eligible.

---

# 15. Backend dominance rule

### Definition 15.1

Backend \(A\) **dominates** backend \(B\) for CE-QS screening if:

1. every established security/property PASS of \(B\) is also PASS for \(A\);
2. \(A\) has no additional FAIL;
3. \(A\) has a strictly better established byte/prover/verifier metric.

Dominance may be based only on measured/source-supported results, never on asymptotic hope.

### Consequence

The 2026 LaZer toolkit supersedes the 2024 LaZer artifact as the **research target** because it adds an explicit ZK mode while preserving the same implementation ecosystem.

It does **not yet dominate on measured CE-QS bytes**, because those have not been measured.

---

# 16. Exact byte-gate classifier

For candidate proof size \(P\), handle size \(h\), overhead \(O\):

\[
Score(P,h,O)
=
32768-(P+43h+O).
\]

Interpretation:

- `Score > 0`: byte headroom;
- `Score = 0`: exactly at gate;
- `Score < 0`: fails gate.

Examples with \(O=0\):

### Lazarus 28-KiB repository claim + 48-byte handles

\[
Score
=
32768-28672-2064
=
2032\text{ B}.
\]

### Lazarus 28-KiB + 96-byte handles

\[
Score
=
32768-28672-4128
=
-32\text{ B}.
\]

Thus even before fixed encoding overhead:

\[
\boxed{
28\text{-KiB proof}+96\text{-B handles fails}.
}
\]

This is a useful illustration of why handle and proof work cannot be evaluated separately.

---

# 17. A stronger eligibility theorem for integrated handles

The explicit-handle equation:

\[
43h+P+O\le32768
\]

assumes all conflict handles are transmitted independently of the proof.

A future backend may **integrate handle information into the proof** while still allowing conflict extraction from two certificates.

Define integrated public conflict state \(C\) with byte length \(|C|\).

Then the general gate is:

\[
\boxed{
|C|+P+O\le32768.
}
\]

It qualifies only if there exists a public algorithm:

\[
ExtractConflict(C_0,P_0,C_1,P_1)
\]

that reveals a common signer without any external opening data.

This recovers the old conflict-intersection-sketch frontier as a first-class backend class.

---

# 18. Mutable-BARG route to integrated conflict state

Mutable BARGs are conceptually interesting for this integrated class.

A batch proof represents many witness/instance pairs and supports privacy-preserving mutations.

A future CE-QS construction could attempt to define a mutation:

\[
\mathsf{ConflictIntersect}
\]

on two certified batch proofs that outputs a proof of a common signer or a blame identifier.

No current source in this record supplies that mutation.

Therefore:

\[
\boxed{
\text{this is a new research direction, not a solved consequence of mutable BARGs}.
}
\]

But it is more targeted than the original open-ended "conflict-intersection sketch" because the batch-proof mutation abstraction now exists in the literature.

---

# 19. Why Fusion still matters despite failing the gate

Fusion demonstrates a useful compression phenomenon:

thousands of independent one-time lattice signatures can be aggregated into an object around 46--47 KB.

Thus it provides evidence that lattice algebra can drive aggregate size toward a near-fixed regime.

For CE-QS, however:

1. the published aggregate alone exceeds the gate;
2. the one-time-key model adds state/registry complexity;
3. public signer privacy and SCCH binding remain separate.

So Fusion is a **negative direct candidate but positive design precedent**.

---

# 20. Current main experimental target

The highest-value next measurement is no longer the historical 2024 aggregate demo.

It is the **2026 succinct-ZK toolkit at its pinned paper commit**.

Minimum benchmark record:

- commit:
  `59a52f74ca39584edf77b4b8b7437dbd48f9ad94`;
- CPU;
- compiler;
- Sage version;
- `zk=True`;
- input dimension;
- serialized proof length;
- prover time;
- verifier time;
- memory.

First reproduce Tables 1--4.

Only then modify the relation.

This is mandatory because current source trees can evolve independently of the paper artifact.

---

# 21. CE-QS-specific experiment ladder

## E0 — artifact reproduction

Reproduce toolkit tables at pinned commit.

## E1 — 64-dimension ZK calibration

Run compression/expansion:

\[
dim=64,
\qquad
zk=True.
\]

Record proof bytes.

## E2 — 43 independent linear relations

Construct 43 small lattice relations of comparable algebraic width to a candidate SCCH.

## E3 — add distinctness/list binding

Encode 43 hidden validator identities, distinctness, and public handle list.

## E4 — add vote verification

Use a lattice-native PQ signature relation if available.

## E5 — full NI mode

Verify 43 local certified contributions.

## E6 — full CP/direct mode

Prove 43 vote+SCCH relations directly.

## E7 — byte-gate verdict

Compute:

\[
Score(P,h,O).
\]

No interpolation from E1/E2 may substitute for E7.

---

# 22. v1.6 proof-status update

| Question | Status |
|---|---|
| QPT sidecar-free hidden CE-QS existence | conditionally closed in v1.3 |
| NI/CP security architecture | conditionally closed |
| 32-KiB gate equation | closed |
| 2024 LaZer succinct-ZK limitation | historical only |
| 2026 toolkit has explicit ZK benchmark mode | **confirmed from source code** |
| 2026 toolkit CE-QS proof bytes | open |
| Fusion direct size eligibility | **fails published 128-bit size gate** |
| CoSNIZK published DAA size eligibility | fails current gate |
| Lazarus 28-KB claim | experimental only |
| Mutable BARG privacy aggregation | theoretical qualified alternative |
| 2026/836 privacy-preserving aggregate signatures | watchlist pending full technical qualification |
| Practical <32-KiB CE-QS | **open** |

---

# 23. Main conclusion

v1.5's compactness conclusion must be updated:

\[
\boxed{
\text{the 2024 lattice succinct-proof stack was not enough for B1,}
}
\]

but:

\[
\boxed{
\textbf{the 2026 LaZer toolkit explicitly implements succinct ZK mode, so the path is reopened.}
}
\]

No proof-size victory is claimed.

The project now has one primary falsifiable implementation question:

\[
\boxed{
\textbf{At the pinned 2026 toolkit commit, what are the actual serialized proof bytes for the full 43-voter CE-QS relation with }zk=True?
}
\]

If that proof plus conflict state satisfies:

\[
P+43h+O\le32768,
\]

the existing v1.3/v1.4 security theorem already supplies the cryptographic composition.

If not, the next frontier is integrated conflict state / mutable-batch-proof mutation rather than another redesign of quorum intersection.
