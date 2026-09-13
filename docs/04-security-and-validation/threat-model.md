# Threat model

What the adversary is assumed to be able to do, the bounds the construction is stated under, what
the model deliberately leaves out, and what happens to each claim when an assumption in the list
fails. The accountability model and its counting fact belong to
`domains/01-accountable-quorum-foundations/`; the target and the assumption list belong to
`domains/06-qpt128-security-target/`.

---

## 1. The adversary

`A` is a **quantum circuit** of gate count `G(A)`, measured in gates, not in queries (see
`security-target.md` §2). It interacts with the construction as the game defines: it may query any
oracle that stands for a hash **in superposition**, and it may compute offline with unlimited depth
and parallelism. There is no separate classical adversary; classical attacks are the `G`-indexed
case of the same statement.

The adversary receives, in both profiles: the public parameters, the authenticated 64-seat registry,
every published certificate, every handle those certificates carry, and the messages they authorize.
It does not receive any seat's secret opening, and it has no access to honest seats' randomness.

## 2. Corruption and fault bounds

| Parameter | Value | Meaning |
|---|---|---|
| `n` | 64 seats | first implementation target; the model is written for `n = 3f + 1` |
| `f` | 21 | Byzantine bound within an epoch |
| `q` | 43 | quorum, `2f + 1`; certificates carry 43 fixed-width slots |
| `2q − n` | **22** | any two quorums of a 64-seat committee share at least 22 seats |

The intersection bound is elementary counting — `|S_0 ∩ S_1| ≥ |S_0| + |S_1| − n ≥ 22` — and the
source records it as what it is: a deterministic combinatorial fact that does not depend on anything
post-quantum. The post-quantum content of the construction is elsewhere: the cost of the 43
signatures or proofs, and the extraction theory that makes the shared 22 seats *publicly
computable* from two certificates without a secret opener.

**Corruption is static within an epoch.** Different subsets may be corrupt in different epochs only
if old threshold shares and one-time signing material are securely retired. **Adaptive or mobile
corruption is explicitly not claimed.** A consequence a reader should weigh: an adversary that
compromises seats incrementally over a long-lived network is outside the model, and the epoch
rotation that bounds its exposure is a system property, not a proved one.

**Faults are modelled as crash faults.** The accountability specification's `Crash` action is
`UNCHANGED vars` — a crashed seat changes nothing — and the specification models no adversary and no
network at all (see `validation-status.md` §"TLA+" for what was and was not run). The empirical fault
layer of the audit stack is broader: 300 schedules over 11 fault classes (loss, duplication,
reorder, delay, clock skew, restart, rollback, corrupt message, corrupt signature, corrupt
certificate, equivocation), 1,717 checks, 3,700 corruption attempts, **0 accepted-on-invalid**, 33
conflicts extracted and **0 honest seats named** — a reproduction of the recorded result at reduced
parameters, not a proof of anything.

## 3. What the model deliberately does not cover

1. **Network-level availability.** Safety requires no synchrony. Every liveness statement in the
   source assumes eventual or partial synchrony, and **the target D1/D2 says nothing about liveness
   at all**: an adversary that simply suppresses traffic does not violate D1 or D2, and neither claim
   is defined to notice. The one availability defect the broader programme found and recorded — an
   unauthenticated replay filter that lets an injected packet make the genuine one look like a
   replay, entry A15 in `records/failed-assumptions.md`, owned by the broadcast layer — is a
   broadcast-layer defect, not a defect of this model, and it is out of scope for D1/D2.
2. **Denial of service against the prover or the registry.** Proof generation, registration and
   certificate dissemination are outside the model. The `32 KiB` certificate budget bounds the wire
   object; it does not bound the work an adversary can force.
3. **Side channels and constant-time behaviour.** This model gives the adversary no timing, power,
   cache or fault-injection channel. That is a *modelling* exclusion, not a statement that the
   implementation resists them: **no constant-time analysis has been performed on the reference
   implementation**, and the smart-card and firmware assessments of the infrastructure domain state
   that it is not constant-time. A reader treating this repository as evidence of deployment
   readiness should treat side-channel resistance as absent.
4. **Implementation faults.** Memory-safety and API-level behaviour are covered only to the extent
   the audit stack exercised them: sanitizer runs and fuzzing on one C implementation at reduced
   parameters, with a production-parameter sanitizer run that **timed out without finishing and is
   therefore inconclusive, not a clean pass**, and a real verifier-side memory leak that leaks one
   9,568-byte allocation per rejected proof (finding F1 of the fix release; a one-line fix exists in
   the next revision, and the audit stack's evidence was taken against the revision that carries the
   leak). The model treats the implementation as correct.
5. **Trusted setup, registry authentication and key lifecycle.** The authenticated registry is an
   input. Rows E6, E7 and E8 (registry authenticity, canonical encoding, durable approval state) and
   B0's rollback row are **set to zero in the ledger**: they are premises. The devnet record contains
   a rollback observation (entry A27). Nothing in D1/D2 proves that a registry cannot be
   substituted or that a rollback cannot resurrect a retired key.
6. **An ideal collaborative prover.** Profile B1's proof of knowledge over hidden signers is stated
   with `A-MPC`, an ideal functionality `F_Prove` for a collaborative prover. **That prover does not
   exist**, and neither does a size-conforming proof backend for the relation. The assumption is not
   a convenience that could be discharged by building slightly more carefully; it is the reason
   profile B1 has no qualified backend today.
7. **The random-oracle model.** `A-QROM` models SHAKE256 as a quantum random oracle. A fixed hash is
   never indistinguishable from a random oracle; this is a model in which the theorem holds, not a
   property of the deployed hash.
8. **Weighted or stake-based voting.** Deliberately excluded to reduce proof surface. A seat is one
   vote.

## 4. If an assumption fails

Each row states what breaks. "Claim" refers to D2/D1 as defined in `security-target.md`.

| Assumption | What it carries | If it fails |
|---|---|---|
| **A-sig** — the chosen non-FIPS category-5 signature is EUF-CMA at category-5 generic strength | B0's non-frameability and safety; the entire E-row structure for B0 | B0's accountability survives (it is the counting fact) but safety and non-frameability do not. Nothing in this repository re-derives EUF-CMA for these candidates; they are not standardized primitives |
| **A-cost** — ≥ `2^18` T gates per oracle evaluation | the conversion from queries to gates, and therefore **every passing margin** | the gate-unit margins collapse toward the query-unit rows, where B0 fails by 11 bits and Mode S by 40. This is the single most load-bearing assumption in the table |
| **A-QROM** — SHAKE256 as a quantum random oracle | Theorem B's bounds in the QROM | Theorem B's proofs do not apply to a fixed hash; no replacement is offered |
| **A-F** — generic bounds for the single-block SHAKE256 credential functions | rows E3, E4, E5 | the credential-collision margins (E3 −203.0, E4 −500.793, E5 −198.023 in gate units) are the widest in the ledger; they would have to be re-derived |
| **A-γ, A-protocol** — protocol-level premises of the hidden-signer analysis | Mode S's composition | Mode S's margins are conditional on them; no weaker statement is available |
| **A-MPC** — an ideal collaborative prover `F_Prove` | B1's honest-signer premise | already unrealizable; no such prover exists |
| **L5 / the `a` coefficient** | the extraction charge E1 in every witness-bearing row | the coefficient is one of three readings (`22ℓ+60`, `20ℓ+60`, `72+40ℓ`); a larger coefficient shrinks the margins, and no re-derivation exists to bound it |
| **static corruption** | the model as a whole | adaptive corruption is not claimed, and no refresh mechanism is proved here |
| **the model-premise rows set to zero (E6–E8, rollback)** | the margins' completeness | each one that is false is an uncharged bad event: the union bound is then over an incomplete set, and the margin is not a lower bound on the true one |
| **the `2^−133` extraction-share convention** | the repetition count `r` (553 gates, 640 queries) | a different share moves `r` and every extraction row; the checker states the convention in the key name rather than defending it |
| **the `2^18` / `2^17` floors as T-counts** | the ledger's cost model | the floors are measurements from published circuits; depth, parallelism and memory are uncharged, so the ledger is not a circuit-level cost model |

---

## Validation status

The statements above carry their labels. What must still be validated for this work to be accepted
as a standard proof, and what is missing, is in `validation-status.md`; the commands re-run for this
package, with their recorded baselines, are in `VERIFICATION.md`.
