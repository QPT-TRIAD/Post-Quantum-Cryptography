# Parameters

Every parameter the construction fixes. Each entry gives the **value**, **where it comes from**,
and **what breaks if it changes**. Nothing here is tunable at run time: the three parameters that a
verifier receives in the header (`count`, `width`, `payload_len`) are checked against the fixed
values, not taken on trust.

**Source of truth.** The reference module
`domains/07-compact-certificate-b0/src/sidecar_free_certificate.py` (a copy of the v1.44 source,
paths rewritten). Constants named in `CAPITALS` below are exact identifier names in that module; the
values were read from it and, where the module computes or checks them, reproduced by running it.
The normative wire specification is `domains/07-compact-certificate-b0/docs/b0-wire-spec.md`.

---

## 1. Committee parameters

| Name | Value | Comes from | What breaks if it changes |
|---|---:|---|---|
| `N` | **64** | the committee size; a programme parameter, not a derived value | The signer bitmap is **exactly 8 bytes = 64 bits**. `N > 64` needs a wider bitmap, so `B0_FIXED_BYTES` (216) and the whole frame layout change, and the gate `W ≤ 757` moves. `N < 64` shrinks the bitmap to fewer bytes and, more importantly, shrinks `MIN_OVERLAP = 2·QUORUM − N`. The registry check `len(keys) != N` and the field size `64s` in the header are both tied to it. |
| `QUORUM` | **43** | `2F + 1` at `F = 21` | Two things move together. (a) `COUNT = QUORUM` is **also the number of signature slots** and the checked value of the header's `count` field, so the frame length `216 + 43·W` and the gate `W ≤ 757` both change. (b) `MIN_OVERLAP = 2·QUORUM − N` changes, so the guaranteed double-authorizer count changes. Raising `QUORUM` above 43 also breaks the BFT identity `N = 3F + 1`, `Q = 2F + 1` (at `F = 21`: `3·21+1 = 64`, `2·21+1 = 43`). |
| `FAULT_BOUND` (`F`) | **21** | `(N−1)/3` at `N = 64` | Appears only through the identity above; `FAULT_BOUND` is **not carried in any frame** and no verifier checks it. Changing it alone changes nothing on the wire — it changes `QUORUM`, which changes everything. The safety statement (any two quorums intersect in ≥ `F+1` seats) is `MIN_OVERLAP = F + 1 = 22` and is what makes extraction work. |
| `MIN_OVERLAP` | **22** | `2·QUORUM − N`, computed in the module as `2 * QUORUM - N` | **This is the extractor's acceptance threshold**, not just a derived value: `extract_b0` requires at least `MIN_OVERLAP` common seats and raises otherwise, and `verify_blame_b0` does not restate it (domain 11's item 13). Lowering it would let attributions below the guaranteed count through; raising it would reject honest conflicts whose overlap is exactly the guaranteed minimum. The module's test `test_all_overlaps_22_to_43` covers every overlap from 22 to 43. |

The arithmetic identity, with its derivation:

```
two 43-subsets of a 64-set intersect in at least 43 + 43 − 64 = 22 seats
MIN_OVERLAP = 2·QUORUM − N = 86 − 64 = 22 = F + 1
```

**This is a counting fact, not a cryptographic one.** It holds for *any* two quorums, whatever the
signers do. The construction's work is not to create the overlap but to make it **publicly
computable from the two frames alone**.

---

## 2. Field and hash parameters

| Name | Value | Comes from | What breaks if it changes |
|---|---:|---|---|
| `BITS` | **512** | the B1 handle field is `GF(2^512)` | The handle is 128 bytes = `L` (64) ‖ `Z` (64), and `Z` is a 512-bit field element. A different `BITS` changes the handle width, `B1_HANDLES_BYTES`, `B1_PREFIX_BYTES` and `B1_PROOF_MAX`. The extractor's identity table is a 64-entry table of 512-bit values built with six `xtimes` and 64 XORs, all `BITS`-sized. |
| `MASK` | `(1 << 512) − 1` | derived from `BITS` | Canonicality bound on every field element; `mul` rejects a non-canonical factor (`0 ≤ a, b ≤ MASK`). A wrong mask admits non-canonical rows that would not round-trip through the wire. |
| `POLY` | `(1 << 512) \| 0x125`, i.e. `X^512 + X^8 + X^5 + X^2 + 1` | fixed in the module; identical in v1.29 and v1.34 | **The decoder depends on this polynomial being irreducible.** `mul` reduces modulo it, and the extraction identity `delta·(seat+1) → seat` assumes every non-zero element is invertible. A reducible polynomial makes `GF(2)[X]/(POLY)` a ring with zero divisors, and the identity table would contain collisions rather than a permutation. The reference does not verify irreducibility at run time. |
| `H` | `H(label, *parts) = SHAKE256( ‖ u64be(len(p)) ‖ p for p in (label, *parts) )[:64]` | the module's `H` | **Every part is length-prefixed with its own 8-byte big-endian length, label included.** An implementation that hashes a plain concatenation gets different bytes and cannot interoperate. This is *only* used for `cfg` and B1's context `D` — see the warning in §3. |
| hash size | **64 bytes** | `digest(64)` — also the width of `cfg`, `d`, `m` | The header has three fixed 64-byte fields. A different digest size changes the header layout and `HEADER_BYTES`. |

---

## 3. Domain separators

Every separator is a fixed ASCII literal. Changing one changes the bytes hashed, and therefore
invalidates every existing frame.

| Literal | Length | Used for | If it changes |
|---|---:|---|---|
| `b"CEQS/K1"` | 7 | B1: `K[i] = SHAKE256(b"CEQS/K1" ‖ x_i)[:128]`; the absorb input is `7 + 64 = 71` bytes, one Keccak rate block | every B1 registry key changes |
| `b"CEQS/P1"` | 7 | B1: `pair = SHAKE256(b"CEQS/P1" ‖ x ‖ D)[:128]`; absorb input `7 + 64 + 64 = 135` bytes, one block | every B1 handle changes; extraction fails |
| `b"CQ44/cfg/B0"` | 11 | B0 registry fingerprint: `cfg = H(b"CQ44/cfg/B0", scheme_id, pk_0, …, pk_63)` | every B0 `cfg` changes; every signature is over a different message |
| `b"CQ44/cfg/B1"` | 11 | B1 registry fingerprint over 128-byte keys, duplicates rejected | as above |
| `b"CQ44/ctx"` | 8 | B1 context: `D = H(b"CQ44/ctx", cfg, d)`, absorbing `cfg` then the domain | every B1 handle changes |
| `b"CQ44/B0/VOTE"` | **12** | B0 signed-message prefix | every B0 signature is over a different message |
| `b"CQ44/real-demo/"` | 15 | the demo's `scheme_id`; a **test value**, not part of the protocol | changes `cfg` in the demo only; the protocol takes `scheme_id` from the deployment |
| `b"CQ44/test-scheme"` | 16 | the module's test registry `scheme_id` | test-only |

**The one thing to get right here.** `cfg` goes through `H`, and so is length-prefixed. The vote
message does **not**:

```
vote_i = b"CQ44/B0/VOTE" ‖ cfg ‖ d ‖ m ‖ u8(i)      plain concatenation, 12 + 64 + 64 + 64 + 1 = 205 bytes
```

The literal is 12 bytes and the concatenation is 205 bytes; both figures are exact and neither is a
hash input, so no length prefix appears anywhere in it. An implementer who assumes everything goes
through `H` produces different bytes for `vote_i`, and every signature fails. This is design note 15
of the independent implementation
(`domains/11-independent-audit-stack/independent-b0/SPEC_GAPS.md`).

---

## 4. Frame constants

| Name | Value | Comes from | What breaks if it changes |
|---|---:|---|---|
| `MAGIC` | `b"CQ44"` | bytes `0–3` of every frame | A reader cannot recognise the format. Note that the *older* revision of this construction used the marker `CEQS`/`CEQS29`; finding A.10 is exactly the confusion between CEQS-era body offsets and CQ44 header offsets in two of the module's own tests. That confusion is recorded, not fixed. |
| `VERSION` | **44** | `u16` at bytes `4–5`, checked by `verify_b0` | Version gating. The suite identifiers below also embed `0x44`. |
| `SUITE_B0` | **`0x44B0`** | `u16` at bytes `6–7` | `verify_b0` requires it exactly. A B0 frame carrying `0x44B1` is rejected, and vice versa. This is the **profile identifier** — the single field that tells a reader which payload layout follows the header. |
| `SUITE_B1` | **`0x44B1`** | same field | as above |
| `COUNT` | **43** | `u16` at bytes `200–201`, checked to equal `QUORUM` | The `count must be 43` check is the one that fires for the *misaligned* message mutation of finding A.10. Changing it changes the slot count and the frame length. |
| `HEADER_FORMAT` | `'>4sHH64s64s64sHHI'` | the header struct | Defines every offset in `wire-format.md` §1. Non-native, big-endian, no padding, no alignment. |
| `HEADER_BYTES` | **208** | `struct.calcsize(HEADER_FORMAT)`, computed and asserted | 4 + 2 + 2 + 64 + 64 + 64 + 2 + 2 + 4. Any field resize moves every offset after it. |
| `STATEMENT_FORMAT` | `'>4sHH64s64s64sHH'` | the header minus `payload_len`; `calcsize` = **204** | The statement a signature commits to, if a deployment binds one explicitly. Not used by `vote_message_b0`. |
| field widths | `cfg`, `domain`, `message` are `64s` each | fixed | Enforced by `_canonical_bytes(value, 64, …)`: a value of any other length raises `FrameError`. There is no variable-length encoding and no padding rule. |
| `width` | `u16` at bytes `202–203` | **chosen per scheme**; the only field a deployment varies | Must equal the provider's width or the check `header width does not match the provider width` fires. As a `u16` it can express 0–65,535, but `MAX_FRAME_BYTES` restricts it to ≤ 757 — *implicitly* (SPEC_GAPS item 16). |
| `payload_len` | `u32` at bytes `204–207` | must equal the trailing byte count | `payload_len does not match the trailing bytes (truncation or trailing data)`. As a `u32` it can express far more than any admissible frame; the binding constraint is elsewhere. |
| `MAX_FRAME_BYTES` | **32,768** | the programme's requirement R1 — a portability bound, not a cryptographic one | The budget everything else is measured against. **It is enforced on the verify side only**: `verify_b0` raises `frame exceeds the 32768-byte portability bound`, while `encode_b0` does not check it at all. This is finding **F6**, a documented gap — see §7. |
| `B0_FIXED_BYTES` | **216** | `HEADER_BYTES + 8`, computed | Header plus bitmap. |
| `B0_MAX_SIGNATURE_BYTES` | **757** | `(MAX_FRAME_BYTES − B0_FIXED_BYTES) // QUORUM`, computed | The gate. `b0_fits(757) = True`, `b0_fits(758) = False`. The remainder `32,552 mod 43 = 1` is unspent: the largest admissible frame is 32,767 bytes, leaving one byte of budget unused. |

---

## 5. B1 constants

| Name | Value | Comes from | What breaks if it changes |
|---|---:|---|---|
| `HANDLE_BYTES` | **128** | one handle is `L` (64) ‖ `Z` (64) | 43 handles are 5,504 bytes; the handle is the payload's fixed part. A wider handle directly eats the proof budget. |
| `B1_REGISTRY_KEY_BYTES` | **128** | the module's comment: 1024-bit keys carry the collision resistance the QPT-128 ledger relies on | A 64-bit key would need a birthday-collision charge of 2^32 in the ledger; the ledger requires 128. The `K1` absorb input stays 71 bytes regardless — the key *length* is the output length, not the input. |
| `B1_HANDLES_BYTES` | **5,504** | `QUORUM * HANDLE_BYTES`, computed | — |
| `B1_PREFIX_BYTES` | **5,712** | `HEADER_BYTES + B1_HANDLES_BYTES` = `208 + 5,504`, computed | The floor under every B1 frame. |
| `B1_PROOF_MAX` | **27,056** | `MAX_FRAME_BYTES − B1_PREFIX_BYTES` = `32,768 − 5,712`, computed | The entire budget for a zero-knowledge proof, **and it applies to the whole proof, not per seat.** A hidden-signer certificate is admissible only if the proof fits here. No proof system meeting it exists in this programme. |
| `verify_b1` verdict | `STRUCTURE_ONLY_NO_QUALIFIED_PROOF` | hard-coded unless a backend declares `qualified = True` | `authorization_verified` is `False` **by construction** — there is no parameter that turns it true without a qualified backend. |

**Measured consequence.** With mode B-r and Mode B at 30,684 bytes the programme does have a
*verified hidden-signer certificate* (`domains/08-hidden-signers/`), but it is not a B1 frame: it is
a different construction at `n = 256` over `GF(2^256)`. B1's 27,056-byte proof slot remains unfilled.

---

## 6. QPT-128 gate parameters

The security target is a **gate work factor**, not a query count, because a query-counted target
fails for every component whose secret is 256 bits (domain 06, Lemma L2).

| Name | Value | Comes from | What breaks if it changes |
|---|---:|---|---|
| `ATTACK_GATE_BUDGET_LOG2` | **128** | the QPT-128 budget `G(A) < 2^128` | Defines the adversary's whole gate allowance. Halving it would make every component easier. |
| `ATTACK_GATES_PER_HASH_LOG2` | **24** | the assumption that one Grover iteration costs at most `2^24` gates per hash evaluation (Keccak-f[1600]'s T-count alone is 499,200 < 2^19, and 2^5 is allowed for uncomputation and Clifford gates) | **This is an assumption, not a measurement.** A cheaper hash gives the adversary more iterations. The report also evaluates `2^18`. |
| `GROVER_ITERATIONS_LOG2` | **104** | `128 − 24`, computed | Fewer than `2^128` gates buy up to `2^(104−h)` iterations for a `2^h`-step hash. |
| D1 | `G(A) < 2^128 ⟹ Pr[Win(A)] < 1/3` | domain 06; adopted as the target | — |
| D2 | `Pr[Win(A)] ≤ G(A)·2^−130` | domain 06; the rigorous strengthening used here; D2 implies D1 | The extra 2 bits of slack beyond 2^128 are what make the union bound over components close. |
| B0's realised margin | **+23.0 bits** | domain 06 `domains/06-qpt128-security-target/results/qpt128_report.json`; B0 passes with `Pr ≤ 2^−25` at `2^128` gates | The margin is the slack in D2. Conditional on assumption `A-sig`. |
| `KECCAK_F1600_BIT_AND_GATES` | **38,400** | `24 · 1600` bit-level AND gates per permutation | A cost constant in the Mode S lower bound. |
| `BINIUS64_AND_PER_PERMUTATION` | **600** | Binius64 counts AND *constraints*, packing 64 bits per word | The Binius64 floor changes directly with it. |
| `MODE_S_KECCAK_PERMUTATIONS` | **86** | the Mode S handle computation needs 86 permutations | The linear lower bound `86 · 38,400 = 3,302,400` AND gates is the module's own arithmetic; the byte figure derived from it (412,800) is an **estimate**. |
| Theorem C working points | `τ·b + w_g ≥ s`, `s = 212` at `h = 0` and `180` at `h = 16`; `c ≥ 218` bits | module `theorem_c_budget` | **A necessary condition for witness-committing proof families** (KKW / BN++ / FAEST-style), not a universal lower bound. Changing `τ`, `b`, `w_g` or the grinding budget moves the per-seat allowance — the full table is in `--report`. |

**Every number in this section is an estimate, a bound or an assumption.** None of them is a
measured certificate size, and none is a proof that a hidden-signer certificate is impossible.

---

## 7. The one parameter that is specified but not enforced

`MAX_FRAME_BYTES = 32,768` is **normative on the verify side and inert on the encode side**.

| side | behaviour | evidence |
|---|---|---|
| `verify_b0` | raises `FrameError: frame exceeds the 32768-byte portability bound` | measured here: a width-758 frame is rejected |
| `encode_b0` | **emits the oversize frame with no error** | measured here: `encode_b0` at width 758 emits **32,810 bytes** |
| `b0_fits(758)` | `False` | measured here; `--report`'s `b0_size_gate` |
| getter | `b0_frame_bytes(758)` returns the length without complaint | — |

This is finding **F6**, and the independent implementation's SPEC_GAPS item 16 records the same
thing from the specification side: *"`WIDTH` is u16 and `MAX_FRAME_BYTES = 32768` imply `W ≤ 757`;
encode's obligation to reject oversize frames is not stated (I check it)."*

**Stated as a gap, not fixed.** An implementation that follows this package must enforce the cap on
**both** sides — a producer that overflows the budget would otherwise emit frames that no conforming
verifier accepts, and would only discover it at verification time. See `wire-format.md` §6.1.

---

## 8. What no parameter controls

- **Hidden signers.** No value of `W`, `N`, `QUORUM` or the B1 constants makes B0 hide its signers;
  the bitmap is in the clear. B1 aims at it and has no proof backend. R6 is not a tuning question.
- **The security of the signature scheme.** `A-sig` (EUF-CMA of the chosen category-5 scheme) is an
  assumption about a scheme the programme did not design. No parameter here strengthens it.
- **Constant-time behaviour.** No parameter makes the reference constant-time, and no side-channel
  testing was performed.
- **Liveness, networking, key management.** The construction is a frame plus its checks; nothing in
  it addresses how 43 seats agree on a message.

---

## 9. Changing a parameter: what a reader must re-derive

If you change anything above, the following are **not** automatically valid and must be redone:

1. **The size gate.** `B0_MAX_SIGNATURE_BYTES = (MAX_FRAME_BYTES − B0_FIXED_BYTES) // QUORUM`. Any
   change to `N` (bitmap bytes), `QUORUM` (slot count) or `MAX_FRAME_BYTES` moves it, and with it
   which schemes are admissible. `sizes.md` has the measured widths to re-test against.
2. **The overlap guarantee.** `MIN_OVERLAP = 2·QUORUM − N`, and with it `F = MIN_OVERLAP − 1` and the
   `N = 3F + 1` / `Q = 2F + 1` identity. If the identity breaks, the fault-tolerance argument that
   makes the overlap meaningful does not carry over.
3. **Every domain separator's absorb length.** The B1 handles assume one Keccak rate block
   (135 ≤ 136 bytes). A longer credential or key pushes `CEQS/P1` absorption into a second block and
   changes the cost accounting in domain 06.
4. **The B1 proof budget.** `B1_PROOF_MAX = 32,768 − (208 + 43·HANDLE_BYTES)`. A wider handle is
   taken directly out of the proof.
5. **The QPT-128 ledger.** Parameters that change a hash's cost, a witness's length, or a registry
   key's length enter the gate accounting in domain 06 and must be re-evaluated there in gate units,
   not in queries.
