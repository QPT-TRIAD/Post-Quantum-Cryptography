# Inflection 8 — contents first, and the challenge hash removed (v1.21 → v1.24)

**Versions concerned:** v1.21 `docs/size-path-resolution.md` and v1.24
`docs/32kib-contents-contract.md`, with v1.22 and v1.23 reported only (no documents in this
repository).
**Date:** 9 September 2026.
**One sentence:** v1.21 quantified that only one branch of the search survives, and v1.24 responded by
choosing what the certificate must *contain* before choosing a proof system — which changed the byte
inventory, removed the challenge hash entirely and moved distinctness from pairwise inequalities to
column occupancies.

## What v1.21 established

v1.21 is an analytical resolution with a stated status: "**analytical resolution; no new
implementation claimed**", and "Nothing here is a measurement of an unbuilt system"
(`docs/size-path-resolution.md:1–5`). Its two load-bearing results:

**The bytes are in the wrong place.** The encoded frame to native gate ratio is
`722,528 / 9,800,861 = 0.0737 B/gate` (native: 0.0881), the committed leaf space for the witness
slots is 268 MB, and "the bytes are dominated by Merkle openings over this committed witness, **not**
by any information-theoretic floor" (`:12–14`). The prefix obstruction is exact and identical under
both the old 4,288-byte and the new 160-byte envelopes:
`46,080 + 16 + 4,128 + 160 = 50,384 > 32,768`, so query-only compression of that layout is dead and
the 176→150-row statistical lever saves only 3.2 % of products without touching the obstruction
(`:17–19`). Inside the cap the per-seat proof budget is `28,480 / 43 = 662 bytes/seat` (`:21`).

**One branch survives.** The kill table (`:23–31`) rules out the trace-only current arithmetization
(needs ≤ 2.9 B/gate, not reachable at 128-bit QPT — "implementation-bound, not bound-in-principle"),
rules out compatibility mode with 43 in-circuit ML-DSA verifications (needs ≤ 0.30–0.54 B/gate,
"orders of magnitude out"), and keeps a Mode S: GKR/sumcheck for the public linear layers, an
arithmetization-native hash for the trace core, and a signature-of-knowledge authorization mode
replacing the 43 ML-DSA verifications — targeting ~3–6 M in-circuit gates at ≤ ~10 B/gate,
"tight but not refuted".

v1.21 also pins the collision/preimage distinction into a query bound: with a 384-bit link hash, the
collision structure `Q³/2³⁸⁴ ≤ 2⁻¹³¹` gives `log₂ Q ≤ 84.33`, where the preimage structure would
have permitted `2^126.5` — "Using the wrong event inflates the claimed allowance by 2^42 in query
count" (`:58`). Three obligations are created and explicitly not inherited: re-derive the link and
challenge algebra against the new hash, build the SoK suite with its own registered authorization
keys and same-seat equation, and re-prove the extraction theorem for the composed (GKR + argument)
protocol (`:35–44`).

## The correction at v1.24 — invert the order of decisions

v1.24's opening states the change of method: "start with the certificate's required information and
then choose a proof that validates it" (`docs/32kib-contents-contract.md:3`), with the rule stated
in bold: **"Contents are assigned by purpose, before selecting a proof system."** (`:13`).

This is a correction of method, not of a number. The preceding versions had all searched for a proof
system small enough for the frame; the frame's contents were inherited from the previous
construction. v1.24 fixes three objects and their allowances — context 208 B, 43 handle pairs
5,504 B, one joint proof 27,056 B, totalling the 32,768-byte gate
(`docs/32kib-contents-contract.md:15–21`) — and states plainly that these are design allocations and
not measurements of a finished certificate (`:21`).

**Three concrete changes follow.**

1. **The challenge hash is removed.** The context already carries a canonical 64-byte message digest
   `m`. Its bytes are interpreted directly as an element of
   `F = GF(2)[x]/(x^512 + x^8 + x^5 + x^2 + 1)` via a bijection, so
   `m ≠ m' ⇒ c_m ≠ c_m'` without a further challenge-hash collision assumption, and every nonzero
   difference is invertible (`:29–38`). The source is careful about what this does *not* remove:
   collision assumptions for an upstream raw-message digest, the registry and the link hash remain;
   and configuration and domain remain bound through the handle equations and the proof statement
   (`:38`). It also states what the change *is*: "It is a **new relation family**, not a
   parser-only reinterpretation of a v1.23 proof." The old field was `F_{2^384}`; the worked field
   here is `GF(2^512)`, chosen so that the 64-byte digest decodes exactly.
2. **Distinctness becomes a column occupancy.** The 43 selected seats are proved distinct by giving
   each handle row six private Boolean selector bits, deriving a one-hot selector
   `e_{j,i} = Π_k ((1−i_k)(1−b_{j,k}) + i_k b_{j,k})`, using the *same* coefficients to select all
   three key tables, and constraining `s_i = Σ_j e_{j,i}` with `s_i(s_i − 1) = 0` in `F_p`, `p > 43`
   (`:81–100`). With 43 one-hot rows the count must be 43 distinct seats. Two warnings come with it:
   the equations must not be transposed into characteristic two, where counts collapse to parity; and
   the selector construction has its own cost, so no whole-circuit speed-up is claimed (`:100`).
   The test field 101 checks the count equations only and is not a parameter proposal (`:108`).
3. **Generation is joint, without recursion.** One MPC computes an ordinary direct proof:
   `(X, π) ← MPC[SelectAndProve_{R_43}]((η_i, a_i, b_i, v_i); ρ)`, with 64 logical participants and
   at most 21 corrupt or withholding in total (`:110–124`). This removes recursive verifier
   arithmetization from the proposed architecture — and the source says exactly that much: it
   "removes recursive verifier arithmetization from the **proposed architecture**, not from an
   already completed distributed implementation" (`:120`).

**What v1.24 refuses to claim** is as important as what it specifies: the certificate need not
disclose its witness, but "This choice does not establish ML-DSA compatibility" (`:25`); the 43
ML-DSA verifications that v1.21 proved unaffordable are *replaced by design* with hash credentials,
not proved equivalent; and the remaining target is stated in one sentence — "one self-contained,
zero-knowledge, appropriately QPT knowledge-sound proof of this full relation inside the reserved
proof slot, with a secure distributed prover. The present work does not yet supply that cryptographic
proof." (`:145`)

## Evidence that this was a correction

**The design is reference-tested, and the test result is recorded in the document.**
`contents_contract.py` creates public deterministic test data for two 43-seat statements with exactly
22 common seats, checks the entire witness relation in ordinary reference code, discards the witness
from the public extraction inputs and recovers exactly indices 0 through 21; it also tests 64
rotating arbitrary quorums, same-seat credential substitutions, incomplete trace handles, missing
context, duplicate seats, changed messages, selector equations and the MPC threshold conditions.
"All **44 reference and contract checks passed**… The ideal selection model produces 43 approvals
with 21 missing inputs and refuses a 42-approval instance. This is an ideal-function test, not a
networked MPC run. No dummy proof was written, and no placeholder-filled 32 KiB object was accepted."
(`docs/32kib-contents-contract.md:139–141`). **That artifact is not in this repository** and is
recorded as `not-run` in `VERIFICATION.md`.

**The property the new challenge relies on has a prior checker.**
`src/ce_qs_qpt_crs_structural_checker.py` already tests the underlying claim — the challenge encoding
is injective — over all 65,536 digests of a 16-bit toy challenge
(`PASS challenge_encoding_injective toy_bits=16`, `results/ce_qs_qpt_crs_structural_checker.txt`).
The v1.24 change is the extreme case of that property: use the digest itself, so no separate
challenge hash exists to collide.

**The obstruction the new inventory answers is arithmetic and was measured.** The old layout's exact
obstruction `50,384 > 32,768` (`docs/size-path-resolution.md:17`) came from `46,080` proof bytes plus
`4,128` handle bytes plus `160` envelope plus `16`; v1.24 replaces that inventory with
`208 + 5,504 + 27,056 = 32,768` exactly. The gain is not a smaller proof of the same relation — it is
a *different object list*, sized by purpose, whose proof slot (27,056 B) is still an unattained
target. The two numbers must not be read as a compression result.

**The v1.23 evidence is preserved with its limitation stated.** The v1.23 package contains seven
actual native proofs of the earlier hashed-challenge relation; v1.24 keeps them "useful evidence for
that relation" and states that they "**are not proofs of the revised v1.24 relation**"
(`docs/32kib-contents-contract.md:143`). The document also notes that the field had been validated at
v1.23 and that the new reference tests exercise zero, high-bit and all-one message encodings
(`:62,139`).

## What remains, stated by the v1.24 document itself

- One self-contained, zero-knowledge, QPT knowledge-sound proof inside 27,056 bytes (`:145`).
- A secure distributed prover (`:120`).
- Authorization, non-framing, adaptive joint QPT extraction and the numerical QPT-128 losses
  established in the approval-oracle experiment — a parser, a witness checker, or a proof of
  possession does not discharge them (`:79`).
- Full SHAKE arithmetization, wire binding, zero-knowledge masking and proof-system field/security
  parameters implemented and verified (`:108`).
- A qualification of one of the two candidate direct-proof routes (`:130–131`).
- The distributed generation security, including the corruption model, synchrony, authenticated
  private channels and active security matching the chosen MPC theorem, and the classical UC premise
  Unruh's lifting theorem requires (`:122`).

See also: `docs/size-path-resolution.md` (v1.21), `docs/32kib-contents-contract.md` (v1.24), and
`docs/construction-end-to-end.md` for the construction at this revision explained end to end.
