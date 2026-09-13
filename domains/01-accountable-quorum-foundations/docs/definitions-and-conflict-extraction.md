# Definitions, the counting fact, and the conflict-extraction argument

This document states the definitions this programme fixes at its start, in the form the source
states them, each with the assumption it needs. It then gives the counting argument that turns a
conflict between two quorum certificates into a named accountable signer, and states precisely how
far that argument goes.

Pointers are `path:line` into the files of this directory. A bare `:NNN` continues the file named
most recently in the same paragraph; unless another file is named, that file is
`docs/research-proof-documentation.md`, the current (v0.7) Target-A research record. Status labels are taken from the source's own vocabulary and from its
status matrix (`docs/research-proof-documentation.md:2798-2823`):

- **theorem with proof** — proved in place in the source;
- **reduction sketch** — the source states the bound and the reduction shape, but the reduction is
  not written out;
- **assumption** — taken as an input to the composition argument, not proved here;
- **measurement**, **simulation / bounded state exploration**, **estimate** — as labelled;
- **conjecture / research direction** — not a result.

Where the source proves only part of a claim, that is said at the claim.

## 1. The problem this domain starts from

The programme's question is stated at `docs/research-proof-documentation.md:16`:

> How can a BFT validator committee obtain compact, post-quantum-secure quorum certificates without
> losing the accountability, reconfiguration safety, and operational properties that classical
> BLS-based systems obtain from compact aggregate or threshold signatures?

The difficulty is a trade. Concatenating individual post-quantum signatures makes a quorum
certificate grow approximately linearly in the number of signers,
`|QC_concat| ≈ q · |σ_individual|` (`docs/research-proof-documentation.md:243-249`); at the reference
committee of `n = 64` seats with a quorum of `q = 43` (`:251-257`), a few-kilobyte signature gives a
certificate "in the hundreds-of-kilobytes range" before protocol metadata. An aggregate or threshold
signature removes that cost, but the compact object does not, by itself, name who signed it. Two
compact certificates on two conflicting statements therefore prove that a quorum misbehaved without
proving which seats did so — and a validator that approved two conflicting statements cannot be
punished on the strength of a certificate that hides its signers. Against this background the source
states the purpose of the sidecar it does build: "to retain enough public evidence to prove which
identities signed if conflicting accountable certificates later appear"
(`docs/research-proof-documentation.md:332`).

The source splits this into two targets and refuses to conflate them
(`docs/research-proof-documentation.md:422-486`):

- **Target A** (the deployable system): a compact threshold signature on the consensus hot path,
  plus an external accountability sidecar of individually attributable evidence, plus cryptographic
  binding between the two (`:424-443`). Target A is what the surviving record tries to prove.
- **Target B** (the frontier): a compact post-quantum quorum signature from which a conflicting
  signer can be extracted directly from two conflicting compact certificates, without retrieving an
  O(n)-scale sidecar (`:446-486`, `:22-24`). The source's status for Target B is *open* (`:484`).

Everything in this domain belongs to Target A except the frontier memo, which is a design-space
survey for Target B and is explicitly "not a construction, not a proof, not a claim of priority"
(`docs/frontier-conflict-extraction.md:4`).

## 2. Committee, seat, quorum, threshold

**Committee.** `n = 3f + 1` (`docs/research-proof-documentation.md:524-526`), with `n ≤ 64` for the
first implementation target (`:530-532`). A **seat** is one equal voting position: "The voting model
is equal-seat, not stake-weighted" (`:534`). Weighted voting was deliberately removed to reduce the
proof surface (`:44`, `:1975-1992`); a seat is therefore a validator, and a quorum is counted in
seats, not in stake. *Assumption needed:* none — this is a modelling choice, and the source records
what it excludes: weighted intersection, evidence weight, weighted accountability and a weighted
threshold access structure are left to a separate proof (`:1983-1989`).

**Byzantine bound.** Within one epoch, `c ≤ f` (`docs/research-proof-documentation.md:540-544`).
Corruption is static during an epoch; different subsets may be corrupt in different epochs only if
old threshold shares and one-time signing material are securely retired. Adaptive or mobile
corruption is explicitly not claimed (`:546-551`). *Assumption needed:* the static-corruption bound;
adaptive security is listed as not proved (`:1943-1945`).

**Quorum.** `q = 2f + 1` (`docs/research-proof-documentation.md:597-599`); the threshold parameter
of the signing scheme is written `T = 2f + 1` (`:639-641`). At the reference committee of 64 seats,
`q = 43` (`:1820-1824`).

**Network.** Safety does not require synchrony; liveness assumes eventual synchrony or partial
synchrony (`docs/research-proof-documentation.md:556-558`). *Assumption needed:* for safety claims,
none; for every liveness statement in the source, eventual synchrony.

## 3. The counting fact: two quorums intersect

The source states the intersection bound in the `3f + 1` parameterization
(`docs/research-proof-documentation.md:587-627`). For `n = 3f + 1` and `q = 2f + 1`, any two quorums
`S_0, S_1` satisfy

```
|S_0 ∩ S_1| ≥ |S_0| + |S_1| − n ≥ (2f+1) + (2f+1) − (3f+1) = f + 1,
```

and the boxed conclusion is `|S_0 ∩ S_1| ≥ f + 1` (`:617-621`). The source's comment on it is
explicit: "This is a deterministic combinatorial fact, not a post-quantum property"
(`:625`). Status: **theorem with proof**, proved in place, elementary counting; the source's status
matrix records "BFT quorum intersection — **Closed** — Elementary combinatorial theorem"
(`:2802`).

**The general form.** The middle expression is the whole fact: for two sets of sizes `q_0` and `q_1`
drawn from a universe of `N = n` seats, the intersection is at least `q_0 + q_1 − N`. When both sets
are quorums of the same size `q`, this reads

```
|S_0 ∩ S_1| ≥ 2q − N.
```

This repository states the fact once, here, in this form; other domains refer back to it. Two
instances of it matter downstream:

- `n = 3f + 1`, `q = 2f + 1` gives `2q − N = f + 1`, the source's boxed form above.
- The reference committee of the same record, `N = 64` seats and `q = 43`
  (`docs/research-proof-documentation.md:530-532`, `:1820-1824`), gives

  ```
  2q − N = 2·43 − 64 = 22.
  ```

  *This is arithmetic on the source's two constants, not a number written in the source.* With
  `n = 64 = 3f + 1`, the corpus bound is `f = 21` and `q = 2f + 1 = 43`, so the same two constants
  are consistent with the source's `3f + 1` formula. Consequently, **two conflicting quorum
  certificates at the reference committee require at least 22 seats to have authorized both
  statements** — 22 double-authorizers — and since at most `f = 21` seats are Byzantine, at least one
  of those 22 must be honest. That is the accountability requirement this domain is built on: a
  conflict cannot happen without an honest seat having signed twice, unless the primitive that
  produced the certificates failed. The source states the `f + 1` version of exactly this step:
  "Since at most `f` validators are Byzantine, two literal `2f+1`-signer evidence quorums share at
  least one honest validator" (`:623`).

*Assumption needed:* the counting is unconditional; using it to name an honest double-authorizer
needs `c ≤ f` (§2) and needs the certificates to come from *literal* quorums of 43 signing seats.
The next section shows why the source does not stop there.

## 4. From quorums to honest-support sets

The source records an error it had to correct first (`docs/research-proof-documentation.md:629-635`):
an earlier revision treated a valid compact threshold signature as if it exposed a known set of
`2f + 1` signers. "That was too strong." A threshold signature does not reveal its signer set — that
is the point of using one.

The corrected abstraction is the **honest support** of an accepted certificate `F`:

```
|HonestSupport(F)| ≥ T − c ≥ f + 1,
```

for a common signing request, except with the threshold forgery advantage
(`docs/research-proof-documentation.md:637-669`, boxed at `:661-669`). It says: an accepted threshold
signature must have received valid partial-signature support from at least `T − c` honest
participants, because at most `c` participants are under adversarial control. *Assumption needed:*
the threshold scheme's strong-unforgeability/support game — the source's words are "For a threshold
signature satisfying the required strong unforgeability/support game". This is an **assumption** on
the primitive, not a theorem of this domain; the source calls it "the correct load-bearing
interface" (`:671`).

Intersecting two honest-support sets gives the sharper conflict statement: with total honest
population `n − c` and each support set of size at least `T − c`,

```
|H_0 ∩ H_1| ≥ 2(T − c) − (n − c) = 2T − n − c = 2(2f+1) − (3f+1) − c = f + 1 − c,
```

and since `c ≤ f`, the boxed conclusion is `|H_0 ∩ H_1| ≥ 1`
(`docs/research-proof-documentation.md:675-729`, boxed at `:725-729`). Status: **theorem with proof
conditional on the previous line** — elementary counting, but only as strong as the support
assumption it consumes. Its content: two conflicting compact certificates require at least one
honest participant to have supported both signing requests "unless the threshold primitive's
security property fails" (`:731-733`).

This is the accountability interface the whole programme uses. Note what it does and does not give.
It gives an *existence* statement about an honest double-supporter. It does not, by itself, produce a
publishable proof naming that seat: the compact certificate still hides it. Producing that proof
requires the second, independent layer of §6 below.

## 5. Conflict domain and vote-once

The domain over which a signer must not equivocate is

```
d = (e, h, v, φ)   — epoch, height, view, phase,
```

(`docs/research-proof-documentation.md:1394-1398`). The validator durably stores `VoteLog_i[d]`, and
"Before sending a threshold share, it persists the message identity" (`:1406`). The claimed invariant
is boxed as

```
Vote_i(M_0, d) ∧ Vote_i(M_1, d)  ⇒  M_0 = M_1
```

"except under persistent rollback or a collision in whatever digest is used in the durable log"
(`:1412-1420`). Status: the source's status matrix records "Crash-safe vote-once — **Closed at
abstract state level** — Needs durable-storage refinement" (`:2811`). *Assumptions needed:* durable
storage that does not roll back, and collision resistance of the durable log's digest — both named
by the source in the same sentence.

The domain is what makes extraction well-posed. Two certificates on conflicting statements are only
an equivocation if they fall in the same domain; a later correction in the security-target domain of
this repository observes that keying a conflict on a threshold-signing *session id* rather than on
the domain would let equivocations escape, because the session identifier hashes the block and so
differs between the conflicting statements (`../06-qpt128-security-target/docs/qpt128-finalization.md`,
correction 11). Extraction must key on the domain.

## 6. Blame: what counts as evidence

The programme's blame rule is stated as a rule about the network, not about cryptography
(`docs/research-proof-documentation.md:837-881`):

- "absence of a message is not public cryptographic evidence" (`:843-847`); non-response is a
  timeout, never an offense (`:849-853`);
- a share can be publicly blamed only if the signer authenticated the share envelope; the blame
  object is the authenticated envelope plus the invalid partial share (`:855-881`).

The individually attributable object is the accountability receipt

```
η_i = Sign_{sk_i^I}(enc(PQ-EVID-V1, i, M)),
```

with a sidecar `E = {(i, η_i)}_{i∈S}`, `|S| ≥ 2f+1`, bound by `C = MerkleRoot(E)`
(`docs/research-proof-documentation.md:303-332`, `:804-819`). Its framing bound is boxed as

```
Adv^EvidenceFrame ≤ Adv^{MU-QEUF}_ID
```

("if an accepted evidence set contains an honest validator that did not produce its receipt, then the
adversary has forged that validator's individual signature", `:821-831`). Status: **reduction
sketch** — the source states the inequality and the argument in one paragraph; no reduction is
written out. *Assumption needed:* multi-user quantum existential unforgeability of the identity
signatures (`Adv^{MU-QEUF}_ID`), which the source uses as an assumption.

The seal acknowledgment `η_i^{seal} = Sign_{sk_i^I}(enc(EPOCH-SEAL-V1, e, H(B_e†), H(FinalityProof_e)))`
(`docs/research-proof-documentation.md:1087-1117`) is the same kind of object for the epoch
boundary, and is the material a boundary fork is extracted from.

## 7. Evidence anchoring

A Merkle root alone proves nothing about availability: a leader could commit to evidence nobody else
holds. Hence the invariant

```
AnchorVote_i(C) ⇒ HaveEvidence_i(C),
```

("An honest anchor voter must retrieve, verify, and persist the complete evidence sidecar before
voting for its root", `docs/research-proof-documentation.md:921-961`; also `:336-358`). Consequence:
an anchor certificate with `2f+1` votes contains at least `f+1` honest voters, so "at least `f+1`
honest validators possess the sidecar" at the moment of anchoring (`:949-955`). Status: the source
calls this a theorem at the abstract state level; the status matrix records "Evidence-before-anchor —
**Closed at abstract state level** — Needs implementation refinement" (`:2809`). The source adds the
limit in the same breath: "This is an availability fact at the time of anchoring. Long-term
retrievability additionally depends on storage and network assumptions" (`:957-959`).

## 8. The epoch boundary and its uniqueness

An epoch change happens only after a terminal block `B_e†` reaches ordinary BFT finality, and the
barrier is drained: finalize, then seal, then activate — no live prepare or lock state crosses it
(`docs/research-proof-documentation.md:360-387`, `:990-1017`, `:1059-1085`). `B_e†` embeds the
complete next public configuration `Config_{e+1}` and setup descriptor rather than their hashes
(`:1001-1056`), which closes the configuration-distribution seam (`:2035-2051`).

The boundary certificate is `BC_e = (B_e†, FinalityProof_e, S_e)` with `S_e` at least `2f+1` seal
signatures (`docs/research-proof-documentation.md:1144-1179`). Uniqueness is argued by the counting
fact of §3: two verifying boundary certificates have signer sets intersecting in at least `f+1`
seats, at most `f` are Byzantine, so an honest validator would have had to seal two different
finalized boundaries. The bound is boxed as

```
Adv^BoundaryFork ≤ Adv^{MU-QEUF}_ID + ε_rollback + Adv^BaseSafety
```

(`:1181-1223`, boxed at `:1211-1221`). Status: **reduction sketch**. The three terms name the three
ways out: a forged identity signature, a persistent-state rollback (`ε_rollback`), or a failure of
the base consensus protocol's own finality theorem. *Assumptions needed:* identity-signature
unforgeability, durable non-rollback storage, and base BFT safety. The source's status matrix records
"Boundary uniqueness — **Paper proof + bounded quorum abstraction checked**" (`:2815`).

## 9. What a conflict yields, end to end

Putting §3–§8 together, the argument the source claims *conditionally*
(`docs/research-proof-documentation.md:1885-1929`, `:2677-2713`) runs:

1. A valid compact certificate has honest support `≥ T − c ≥ f + 1` (§4), assuming the threshold
   support game.
2. Two conflicting certificates have honest support sets intersecting in `≥ f + 1 − c ≥ 1` seat
   (§4), same assumption.
3. An honest seat that supported both requests would have had to vote twice in one conflict domain
   (§5), assuming durable vote state.
4. Therefore a conflict implies either an honest vote-once violation, or a failure of the threshold
   primitive (`:1893-1895`). At the reference committee the literal-quorum count of §3 says the same
   thing numerically: at least 22 seats must have authorized both statements, at most 21 of which
   can be Byzantine.
5. To *name* the offender publicly, the programme uses the evidence sidecar and its anchoring (§6,
   §7): the source's system theorem lists "two conflicting audited evidence quorums expose at least
   `f+1` common identities" as one of its conditional conclusions (`:2710`).

Step 5 is the gap between this domain and Target B. Step 4 tells an auditor that an honest seat
equivocated; the sidecar is what turns that into a verifiable accusation against a named seat.

## 10. Target B: extraction without a sidecar, and why it is hard

Target B asks for `ExtractConflict(M_0, σ_0, M_1, σ_1) → (i, π_i)` with
`VerifyBlame(M_0, σ_0, M_1, σ_1, i, π_i) = 1`, from the two compact certificates alone
(`docs/research-proof-documentation.md:446-478`). Status: *open*, in every revision
(`:484`, `:1969-1972`).

Two facts bound the problem:

- **Information-theoretic pressure.** A self-contained certificate that must reveal an exact signer
  subset of size `t` among `n` must distinguish `C(n,t)` subsets, so it needs at least
  `log_2 C(n,t)` bits "merely to encode the exact signer-set choice in the worst case"
  (`docs/research-proof-documentation.md:490-514`). The source is careful about what this does and
  does not say: "This does not prove a compact conflict-extractable scheme exists. It explains why
  weakening the happy-path attribution requirement is a rational direction" (`:512-514`).
- **The design tension.** The frontier memo states the central obstacle: threshold lattice
  signatures of the Fiat-Shamir-with-aborts family (Hermine, Threshold Raccoon and other
  NIST-preview candidates) use pairwise masks and rejection sampling precisely to prevent
  conditional algebraic leakage from repeated or related signing, while Target B wants leakage that
  is impossible for one message and provable for two — "unconditionally hiding for one message and
  conditionally, verifiably openable for two" (`docs/frontier-conflict-extraction.md:64-68`).

The memo's candidate direction, trace-tagged threshold signing, and its five stated obstacles
(`docs/frontier-conflict-extraction.md:72-100`) are **conjecture / research direction**, not results.
The direction was later dropped in favour of the PQ hidden-threshold proof plus anonymous conflict
trace tags carried on in `../02-ceqs-construction-evolution/docs/frontier.md`, when it became clear
that deriving masking randomness inside a lattice threshold signature collides with rejection
sampling and the leakage-prevention mechanisms. Neither the memo nor this document claims any part
of Target B.

## 11. Assumption inventory

Every row is an input to the argument above, not a result of it. The last column points at what
would break if the assumption failed.

| Assumption | As used | Where | What depends on it |
|---|---|---|---|
| Static corruption `c ≤ f` per epoch | adversary controls at most a third of seats, fixed within the epoch | `docs/research-proof-documentation.md:540-551` | the `≥ f+1` and `≥ 1` intersections; accountability |
| Threshold support game (`ts-suf-2`-shaped) | accepted certificate has honest support `≥ T − c`, except with the forgery advantage | `:637-669`, `:1628-1655` | support/intersection statements |
| Identity signatures multi-user unforgeable | `Adv^{MU-QEUF}_ID` | `:821-831`, `:1905-1907` | evidence framing, boundary uniqueness |
| Quantum collision resistance of digests | 384-bit commitment target, `≈ 2^{m/3}` generic quantum collision search | `:885-919` | evidence binding, vote log |
| Durable, non-rolling-back storage | persist-before-send, `VoteLog`, seal state | `:1406`, `:1420`, `:1424-1482` | vote-once, seal uniqueness |
| Base BFT protocol safety | finality of `B_e†` under an ideal QC abstraction | `:2691`, `:2799-2805` | cross-epoch and global safety |
| Eventual synchrony | liveness only | `:554-559`, `:1119-1142` | post-seal recovery, activation |
| Setup/DKG | `δ_setup`, deliberately not called negligible | `:1587-1626` | every use of the threshold key |
| Query bounds | `Counter_e ≤ Q_Sign^deploy < Q_Sign^proof` with `SafeHalt` | `:1484-1522` | the primitive's theorem applies at all |

## 12. Open items in this document's scope

1. `ε_rollback` is an operational term, not a cryptographic negligible; the no-rollback premise was
   later violated on a restore path and fixed operationally (`../../records/failed-assumptions.md`,
   entry A27).
2. Adaptive corruption, weighted seats, and proactive refresh are outside the proved profile
   (`docs/research-proof-documentation.md:1943-1945`, `:1975-2011`).
3. The extraction argument of §9 names an honest equivocator only with the sidecar; Target B remains
   open (§10).
4. The conflict-domain keying correction (session id versus domain) is recorded in the
   security-target domain, not fixed in this domain's text.
