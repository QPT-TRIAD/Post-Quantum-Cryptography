# Inflection 7 — four review claims are adjudicated, and a registry condition halves the link rows (v1.18 → v1.19 → v1.20)

**Versions concerned:** v1.19 `history/blocker-resolution-v1.19.md` (superseded, kept in `history/`)
and v1.20 `docs/blocker-resolution.md` (current in its lineage).
**Date:** 9 September 2026.
**One sentence:** v1.19 rejected four of the review's inferences — including a smaller candidate pool,
a registration-commitment shortcut and a collision/preimage conflation — with exact arithmetic and a
conditional retry theorem, and v1.20 turned one of the accepted ideas into a concrete construction
change: 176 link rows instead of 608, conditional on freezing the registry before sampling the
domain matrices.

## The situation

By v1.18 the project had concluded that no examined construction qualifies and that the remaining
work is a joint construction with a bounded byte budget (Inflection 6). Three reviews arrived
proposing shortcuts. v1.19's task was to adjudicate them against the existing source rather than
adopt them.

## v1.19 — what was rejected, and why

The disposition table (`history/blocker-resolution-v1.19.md:14–23`) is the core of the version:

| Item reviewed | Disposition |
|---|---|
| Registration commitment as a replacement for authorization/trace computation | **Rejected** as a cost-saving inference; retained only as optional registration architecture |
| A 46–50-person unfiltered pool guaranteeing 43 usable inputs | **Rejected by exact worst-case arithmetic** |
| A retry bound | At most **22 attempts**, conditional on fresh sound fault identification per failure and stable delivery/timeouts |
| An oversized conservative upper estimate proving impossibility | **Incorrect**; only an applicable lower bound or an actual oversized measurement establishes the corresponding failure |
| Treating quantum collision resistance as Grover preimage resistance | **Incorrect**; the events have different query exponents |
| Treating statistical quantum lifting as automatic adaptive-corruption security | Not supported by the examined theorem/model |
| Complete compactness, QPT security and collaborative production | Remain open |

Three of these deserve the arithmetic that supports them, because each is a case where an appealing
shortcut is *false* rather than merely inconvenient.

1. **The pool arithmetic.** After `b` distinct Byzantine identities have been soundly identified and
   excluded, the remaining fault budget is at most `21 − b`, and the sufficient worst-case candidate
   count becomes `k ≥ 43 + (21 − b) = 64 − b` (`:126–129`). A 46–50-seat pool therefore cannot
   guarantee 43 usable inputs in the worst case; the worst case needs 64. The document also notes
   that the *probability* improves if corrupt validators cooperate, if fewer than 21 are faulty, or
   if the system has prior information — "None of those is a worst-case liveness guarantee under the
   stated contract", and independent resampling of small pools does not give a deterministic bounded
   retry count (`:122`).
2. **The retry theorem is conditional and its proof uses a potential.** With `Φ = 21 − b` where `b`
   is the number of distinct soundly excluded faulty identities, each failed attempt decreases `Φ` by
   at least one; all 43 never-corrupted approving validators remain; after at most 21 such failures no
   further blame-producing failure is possible, and by assumption the next bounded attempt succeeds.
   The proof explicitly does **not** assume independence between attempts (`:136–148`). The document
   also states the limit of the bound: "A timeout does not establish culpability before message-delay
   bounds apply… they must not silently become permanent fault certificates" (`:154`).
3. **The collision/preimage distinction.** For a generic random function with `h`-bit output, the
   usual generic scales for quantum preimage and collision are `Q²/2^h` and `Q³/2^h` respectively, so
   constant-success collision query complexity has exponent `h/3`, not the preimage exponent `h/2`
   (`:193`). Consequently "a generic 256-bit collision-resistance assumption does not provide a
   128-bit quantum collision work factor" (`:195`). This is the arithmetic that later becomes the
   `h ≥ 3 log₂Q + log₂M + log₂C + 131 → 339 bits` collision requirement, as against 275 bits for
   preimage. The same section immediately bounds the claim: the observation "does not demonstrate an
   attack on any construction or prove that every soundness reduction needs that exact unrestricted
   collision game" — the actual vector-commitment/extraction analysis determines the required notion.
4. **The composition arithmetic.** `Σ_{j=1..8} ε_j ≤ 8·2⁻¹³¹ = 2⁻¹²⁸` (`:202`), and the warning that
   follows: eight terms each bounded only by `2⁻¹²⁸` give `2⁻¹²⁵` — "Add probabilities, not bit
   exponents. The existence of eight obligation labels alone does not establish the necessary
   composition inequality" (`:205`). "128-bit security" is not a numerical failure-probability ledger;
   the experiment needs a resource profile — quantum queries and computation, signing queries, users,
   sessions, epochs, corruption and exposure (`:191`).

The relation inventory v1.19 supplies is the first exact one: 13,914,112 scalar products,
6,957,056 packed native multiplications, 215 Keccak permutations, 22,176,863 native internal wires,
142,287 bytes of ML-DSA signature witness before proof encoding
(`history/blocker-resolution-v1.19.md:68–84`), with the arithmetic `43(608 + 608 + 48)·256 =
13,914,112` written out (`:84`). The document also preserves the prior evidence honestly: the v1.17
source ledger records two accepted native trace components and 27 public-pair diagnostic checks, and
its files establish neither full vote authorization nor a complete 32 KiB certificate — "Valid
full-QC count remains zero" (`:261`).

## v1.20 — one idea accepted, and converted into a construction change

v1.20's opening states the one change and the one correction
(`docs/blocker-resolution.md:5`): **176 link rows instead of 608**, conditional on fixing the
registry *before* sampling fresh domain matrices; and a correction of the addendum's claim that
public conflict extraction requires a secret opener.

**The frozen-registry bound** (`docs/blocker-resolution.md:76–108`):

1. The old argument needed 608 rows because link injectivity had to hold over *every possible*
   secret. A frozen registry needs only separation of the 64 registered secrets.
2. The registry is fixed first; **after** that freeze, fresh independent uniform 176-row `B_d` and
   48-row `C_d` matrices are sampled per configured domain and published as fixed public
   configuration (`:84`).
3. The resulting bound is

   ```
   ε_B-pair <= 1024 * C(64,2) * 2^-176 = 63 * 2^-161 ~ 2^-155.0227200765
   ```

   (`:104–105`), covering maliciously chosen registered secrets as well as honest ones, **provided
   they are bound before the matrix sampling** (`:108`).
4. With that term, the total is `ε_new ≤ ε_A + 1024·C(64,2)·2⁻¹⁷⁶ ≈ 2⁻¹⁵⁴·⁸⁸⁰⁰¹⁸¹³³⁴⁴⁵⁴`
   (`:127–128`).

The source states the limit of the claim as plainly as the claim: "It is not a claim that a 176-row
map is injective on the entire secret space. The short-link result must not be applied to
registrations chosen after seeing those matrices" (`:108`). That sentence is the entire content of
the condition, and it is a *setup ordering* requirement, which is why it is checkable.

**The corrected conflict theorem** (`docs/blocker-resolution.md:23–70`) rejects two related
shortcuts: a 22-of-64 secret opener committee "changes that interface: extraction needs secret shares
or a post-conflict service. Public verifiability of an opening does not make its generation publicly
computable" (`:23`); and "online extractable" accountable ring signatures do not automatically give a
public conflict opening, because the matched paper's opener has a public/secret key pair and its
knowledge extractor is a security-proof mechanism, not the desired public two-certificate algorithm
(`:31`). The document also disposes of a proposed zero-knowledge contradiction: a ZK simulator
preserves the public statement including `(L_i, Z_i)`, and those inputs can already disclose
identities when paired with conflicting inputs; simulation hides the private witness, it does not
erase public-input information, and access to a simulation trapdoor is not an ordinary signing
capability (`:70`).

**The measurement v1.20 adds** is an executed trace circuit, not an extrapolation
(`docs/blocker-resolution.md:7,141–166`):

| Quantity | Before (v1.19) | v1.20 |
|---|---:|---:|
| Native gates | 14,988,983 | **9,800,861** |
| Packed integer multiplications | 6,957,056 | **4,579,328** |
| Native internal wires | 22,176,863 | **14,638,877** |
| Registration / link / mask rows per seat | 608 / 608 / 48 | 608 / **176** / 48 |
| First verified encoded diagnostic frame | 863,744 B | **722,528 B** |

It "still contains **zero ML-DSA verification constraints**" (`:7`), and the frame is "well above the
32,768-byte complete-certificate limit". The native proof suite retains its earlier 96-bit security
label, and the document states that this experiment makes no QPT-128 qualification; the two producer
runs used approximately 13.0 GiB peak RSS under a 20 GiB address-space limit, and timing differences
between randomized fixtures are recorded as observations, not as a performance theorem (`:166`).

## Evidence, and its limits

This inflection's evidence is arithmetic and documentary, and the sources label it as such. No
checker for v1.19 or v1.20 is present in this repository; the artifacts they cite are named and
listed as `not-run` in `VERIFICATION.md`.

- v1.19 reports an executable artifact with **116 passing checks** covering all 22 pool sizes from 43
  through 64, independent small-population enumeration of the sampling formula, ideal retry paths for
  every fault count 0–21, size-evidence classification, relation-count agreement, statistical
  arithmetic, and rejection of the incomplete security ledger — "These are arithmetic and ideal-model
  checks; they do not validate a cryptographic MPC implementation or a full QC"
  (`history/blocker-resolution-v1.19.md:259`). **That artifact is not in this repository.**
- v1.20 reports that `bound_audit.py` independently reconstructs the old expression, compares exact
  fractions, checks all 16 order cases and checks the rounding argument on an exhaustively enumerated
  small modulus, with **154 named checks passing** including one summarizing **992 distinct
  secret-pair cases** — followed immediately by the limit: "These are arithmetic checks, not 154
  cryptographic security proofs" (`docs/blocker-resolution.md:131`). **`bound_audit.py` is not in
  this repository.** The exact rationals are recorded in `PQ_CE_QS_exact_bounds_v1_20.json`, also
  absent.
- v1.20 reports an evidence checker passing **27 consistency checks** and recovering the **22 expected
  synthetic trace indices** from two public handle lists, plus **86 real ML-DSA signatures** verified
  and **86 wrong-seat public-key substitutions** rejected — with the boundary stated: "These private
  checks do not put authorization inside either public proof" (`:164`).

The one part of this inflection a reader can verify inside this repository is the arithmetic itself:
`1024 · C(64,2) · 2⁻¹⁷⁶ = 63 · 2⁻¹⁶¹`, the values of `C(64,2) = 2016` and `C(64,43) ≈ 2^55.19`, and
the count `43(608+608+48)·256 = 13,914,112` — all of which are elementary and can be recomputed by
hand. The domain's own v0.7 checker independently computes the `2^55.19` figure
(`results/ce_qs_quorum_family_checker.txt`).

## The "failed before, passes after" reading

- **608 → 176 rows.** The 608-row demand is the "before": it makes the link map injective over an
  unbounded secret space, which is exactly the over-strength that made the format unaffordable. The
  correction is not a smaller-margin trick but a *different property* — separation on a set fixed in
  advance — and the resulting ε is *better* than needed (2⁻¹⁵⁵ per pair against a 2⁻¹²⁸ target) while
  the transaction count drops by 71 %. The condition (register before sampling) is the price.
- **Zero ML-DSA constraints.** Every executed circuit — before and after — contains none. The
  corrections do not hide this; v1.20's own §2 states the actionable backend task is "a complete
  joint authorization-and-trace relation in a proof protocol with a different size profile", and that
  in the compatibility mode it must include all 43 ML-DSA verifications (`:205`). The gap that
  v1.24's hash-credential design is meant to close is stated here first.
- **The opener.** The review's secret-opener committee would have made extraction depend on a service
  — a sidecar by another name. Rejecting it preserves the property the whole sequence is built on:
  verification and extraction use the two certificate byte strings and fixed public configuration
  only (`:11`).

See also: `history/blocker-resolution-v1.19.md`, `docs/blocker-resolution.md`,
`docs/multitrack-verification.md`, and Inflection 8 for what v1.21 concluded about which branches
survived this measurement.
