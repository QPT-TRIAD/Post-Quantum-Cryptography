# The construction, step by step, in the order a verifier executes it

This document is the operational view of profile B0. Every step gives its **purpose**, its **inputs
and outputs**, its **failure mode**, and the **assumption** it depends on. The byte-level field
table is in `wire-format.md`; the parameter values are in `parameters.md`.

Symbols: `N` = 64; `QUORUM` = 43; `F` = 21; `MIN_OVERLAP` = 22; `W` = the signature scheme's fixed
signature width in bytes; `cfg` = the 64-byte authenticated configuration; `d` = the 64-byte
conflict domain; `m` = the 64-byte message; `H` and `vote_i` are defined in §2 and §6.

Line pointers of the form `:N` refer to the reference module
`domains/07-compact-certificate-b0/src/sidecar_free_certificate.py`.

---

## 0. What the verifier holds, and what it is given

**Holds.** The authenticated 64-seat registry: an ordered list of exactly 64 distinct non-empty
public keys `pk_0 … pk_63` and a byte string `scheme_id`. It also holds the registry's authenticated
configuration `cfg`, obtained out of band from a trusted configuration source. The registry is
*fixed* data, not part of any certificate: it is the same for every certificate the committee
issues under that configuration.

**Given.** A candidate frame (a byte string), and a signature provider — the concrete
implementation of the scheme whose width `W` the frame declares.

**Not given, and never needed.** Any proof file, omitted opening, external leaf list, protocol
transcript, opener secret, or per-seat accusation proof. This is the *sidecar-free* requirement, and
it is the reason the construction is shaped the way it is.

**Produces.** On success, the tuple `(cfg, d, m, W, bitmap, seats)`: the domain, the message, the
width, the 8-byte signer bitmap, and the 43 seats as an ascending tuple.

---

## 1. Step 1 — frame framing

**Purpose.** Reject anything that is not a well-formed frame before any expensive work.

**Procedure.**

1. The frame must be a byte string (`bytes`, not `bytearray`, `memoryview` or text).
2. `208 ≤ len(frame) ≤ 32,768`.
3. Split at offset 208: the first 208 bytes are the header, the rest is the payload.
4. Unpack the header and check `magic == CQ44`, `version == 44`, `suite == 0x44B0`, `count == 43`.
5. `payload_len` (the `u32` at offset 204) must equal the number of bytes actually after the header.

**Inputs.** the candidate frame. **Outputs.** a parsed `(header, payload)` pair.

**Failure mode.** Any violation raises and the frame is rejected. Step 5's equality check is the one
that catches **truncation** and **trailing data**: a frame missing its last byte, or carrying one
extra byte, has a `payload_len` that no longer matches the tail. It is the check that fires for 100 %
of the truncated and trailing vectors in the independent vector set.

**Assumption.** None beyond deterministic parsing. The bound in (2) is the programme's portability
gate, not a cryptographic limit.

**Reference:** `parse_frame`, `:295-316`.

---

## 2. Step 2 — the hash, and why it is length-prefixed

**Purpose.** One domain-separated hash used for every derived value, so that no two distinct uses
can collide by concatenation ambiguity.

```
H(label, p_1, …, p_k) = SHAKE256( u64be(len(label)) ‖ label
                                ‖ u64be(len(p_1)) ‖ p_1
                                ‖ … ‖ u64be(len(p_k)) ‖ p_k ) squeezed to 64 bytes
```

An eight-byte big-endian length prefix precedes the label and every part. Every part must be a byte
string; anything else raises.

**Failure mode.** A non-`bytes` part raises.

**Assumption.** SHAKE256 behaves as a domain-separated hash (a concrete function, not an ideal
oracle — the reference uses `hashlib.shake_256`).

**Note — a real trap.** `H` is used in exactly two places: the configuration `cfg` of §3 and the
context `D` of profile B1. The vote message of §6 and the toy signing input are **plain
concatenations**, not `H` calls. An implementer who routes everything through `H` produces
different bytes and a different `cfg`, and will reject every frame the reference produces. This is
recorded as gap 15 of the independent implementation.

**Reference:** `H`, `:208-214`.

---

## 3. Step 3 — registry validation and the configuration

**Purpose.** Bind the certificate to one exact committee, so that a certificate cannot claim a
registry the verifier does not already hold.

**Procedure.**

```
cfg = H(b"CQ44/cfg/B0", scheme_id, pk_0, pk_1, …, pk_63)          (64 bytes)
```

Registry validity is part of this computation: exactly 64 keys, each a non-empty byte string, all
distinct, and `scheme_id` a byte string. Validation happens *inside* `cfg`, so every verification
that recomputes `cfg` validates the registry. This is deliberate: the wire specification §3 defines
validity but §7 does not require the verifier to check it, so an implementation that validates in
`cfg` closes the hole by construction (gap 10 of the independent implementation).

**Inputs.** the registry. **Outputs.** `cfg`, 64 bytes.

**Failure mode.** A malformed registry raises.

**Assumption.** Collision resistance of SHAKE256 at 64 bytes, and that the verifier's `cfg` came
from a trusted configuration rather than from the frame itself.

**Reference:** `cfg_b0`, `_check_registry_b0`, `:348-364`.

---

## 4. Step 4 — two-sided configuration authentication

**Purpose.** The single most load-bearing check in the construction. It is what makes the
certificate *non-transferable across registries* and what stops an adversary from presenting a frame
built for a key list of its own choosing.

**Procedure.**

```
header.cfg == expected_cfg          (the value the verifier authenticated out of band)
header.cfg == cfg_b0(registry)      (the value recomputed from the 64 keys it holds)
```

Both must hold. They are not redundant:

- the first binds the frame to the authenticator's trusted value;
- the second binds it to the key list the verifier will actually check signatures against.

**Inputs.** the parsed header, `expected_cfg` (exactly 64 bytes), the registry.
**Outputs.** none; both checks pass or the frame is rejected.

**Failure mode.** Either mismatch rejects. `expected_cfg` of the wrong length or type rejects
before any comparison.

**Assumption.** That the verifier obtained `expected_cfg` from an authenticated configuration. If
it takes `cfg` from the frame, both checks become vacuous, and the security statement of §9 no
longer applies. The construction assumes a fixed authenticated registry and approved verification
parameters; it does not try to transport them.

**Reference:** `verify_b0`, `:406-431`.

---

## 5. Step 5 — width and payload length

**Purpose.** Fix the layout of the signature block before reading it, so the signature positions are
determined by public data only.

**Procedure.**

```
header.width == provider.width      and   header.width > 0
len(payload)    == 8 + 43 · header.width
```

**Inputs.** the header, the payload, the provider. **Outputs.** the width `W` for the slot loop.

**Failure mode.** A width that differs from the provider's rejects; a payload length that is not
`8 + 43·W` rejects; a non-positive width rejects.

**Assumption.** That the provider's width is the *exact* width of every signature it produces. A
variable-length scheme does not admit a fixed-slot profile; the reference refuses a short signature
rather than padding it (`encode_b0`: "signature must be exactly the provider width";
`OqsSignatures.sign`: "variable-length signature does not fill the fixed slot"). One library binding
in the measured table (`pqcrypto`) pads a short signature instead, and the schemes exercised through
it never take that path — recorded as a package limitation, not a design change.

**Reference:** `verify_b0`, `:406-431`.

---

## 6. Step 6 — the bitmap

**Purpose.** Carry the signer set in the clear, in eight bytes. This is the object B0 does *not*
hide, and it is also the object that makes extraction cheap.

**Procedure.** `bitmap = u64be(payload[0:8])`; bit value `2^i` set ⇔ seat `i` signed (seat 0 is the
least significant bit of the integer, and the integer is serialised big-endian). The check is
`bitmap.bit_count() == 43`, exactly.

**Inputs.** the first eight payload bytes. **Outputs.** the bitmap and the ascending tuple of set
seats.

**Failure mode.** A popcount other than 43 rejects. This also catches a large class of mutations
that land in the header: a misaligned write into the message field of a symbolically-signed test
frame is rejected here with `count must be 43` before any signature is checked (finding A.10).

**Assumption.** None. The bit numbering is a convention and was made normative after the independent
implementation flagged it (gap 1): the alternative reading (the i-th bit of the big-endian byte
string) produces different bytes for every frame.

**Reference:** `verify_b0`, `_seats_from_bitmap`, `:418-421`.

---

## 7. Step 7 — the 43-signature block

**Purpose.** Carry one signature per signing seat, in a fixed width, in a position determined by the
bitmap alone.

**Procedure.** For each set bit `i` in ascending seat order, let `p` be its 0-based position among
the set bits. The signature for seat `i` occupies `payload[8 + p·W : 8 + (p+1)·W]`. It must verify
under `pk_i` over `vote_i`.

```
vote_i = b"CQ44/B0/VOTE" ‖ cfg ‖ d ‖ m ‖ u8(i)
```

signed with the scheme's pure signing API and an empty external context.

**Inputs.** the payload, the bitmap, the header's `cfg`, `d`, `m`, the registry, the provider.
**Outputs.** 43 verified signature checks (or the first failure).

**Failure mode.** Any signature that does not verify rejects the frame with
`signature for seat i does not verify`. This check is what fires for the *aligned* message mutation
of finding A.10.

**Assumption.** **EUF-CMA security of the signature scheme.** This is the assumption the whole
security statement rests on, and it is a named assumption (`A-sig`) about schemes that are
candidates in NIST's additional-signature process rather than FIPS standards. Its own QROM proof, for
UOV, carries a `(2q+1)²` loss.

**Why the message is built this way.** `cfg` is inside the signed message, so a signature is bound
to the exact 64-key registry. `d` and `m` are separate fields, so two certificates can conflict on
the message while sharing the domain — which is exactly the case extraction must handle. `u8(i)` is
a single byte, so a signature cannot be replayed into another seat's slot.

**Why 43 slots and not a bitmap-and-list.** A fixed slot per seat makes the payload length a
function of `W` alone, so the extraction positions of §9 are computable from public data. A
variable-length or deduplicated encoding would make the positions depend on the signatures
themselves.

**Reference:** `vote_message_b0`, `:367-372`; `encode_b0`, `:379-403`; the slot loop of
`verify_b0`, `:424-431`.

---

## 8. Step 8 — conflict detection

**Purpose.** Decide whether two frames constitute a conflict at all. Equal messages are not a
conflict, and a certificate is not evidence against a seat that approved the same message twice.

**Procedure.** Given two frames `frame0`, `frame1`:

1. Verify both completely — all 86 signatures. Any failure rejects the pair.
2. `v0.cfg == v1.cfg` (same configuration), else reject.
3. `v0.domain == v1.domain` (same conflict domain), else reject.
4. `v0.message != v1.message`; **equal messages reject**, because there is nothing to extract.

**Inputs.** two frames, the registry, the provider, `expected_cfg`. **Outputs.** two verified
results, or a rejection.

**Failure mode.** Each of the four conditions has its own rejection. Conditions 2 and 3 cannot fire
against two frames that both passed the two-sided `cfg` check of §4, and condition 4 is the one that
does real work. The independent implementation recorded that the same-message vectors are rejected
with the clause `8.2 messages equal (not a conflict)` and the other-domain vectors with
`8.2 domain differ`.

**Assumption.** That "conflict domain" is a label under which a seat must not approve two different
messages. That rule is the protocol's, not the certificate's; the certificate only enforces that the
domain is equal and the message is not.

**Reference:** `extract_b0`, `:434-452`.

---

## 9. Step 9 — extraction of the conflicting seats

**Purpose.** Turn a conflict into a public, individually verifiable attribution of double
authorization — with no opener and no sidecar.

**Procedure.** Compute the bitwise intersection `common = bitmap0 AND bitmap1`. Reject if its
popcount is below 22. Then output, ascending by seat,

```
(seat, position0, position1)
```

for every set bit of `common`, where `position0` and `position1` are the seat's 0-based positions
among the set bits of each frame. The two signatures at those positions are the evidence: anyone can
verify them against the registry's public keys on the two conflicting messages.

**Inputs.** the two verified frames. **Outputs.** at least 22 triples of `(seat, position0,
position1)`.

**Failure mode.** The popcount check is *unreachable* for two valid frames: any two 43-subsets of a
64-set share at least 22 seats, so the check can never fire on inputs that passed §7. It is retained
as defence in depth. The reference says so in a comment at the check, and a test exercises every
overlap from 22 to 43. The independent implementation flagged it as unreachable (gap 12).

**Where the correctness of "at least 22" comes from.** It is elementary set arithmetic over the
quorum family: for `N = 3F + 1` and `Q = 2F + 1`, `|S₀ ∩ S₁| ≥ 2Q − N = F + 1 = 22`. The
programme uses it in the stronger form "at least one seat that approved both is **honest**", since
`22 = F + 1`. The statement is used **in full** — nothing is borrowed and abandoned — and it is
exercised exhaustively by the quorum-family checker in
`domains/02-ceqs-construction-evolution/src/ce_qs_quorum_family_checker.py` for `n = 4, 7, 10` and
instantiated at `n = 64`. It is a counting fact, not a cryptographic one, and it holds
unconditionally.

**Where the *public* computability comes from.** From §6 and §7 together: the bitmap is in the
clear, and each signature sits at a position fixed by the bitmap. Extraction is therefore a bitmap
intersection plus 86 signature verifications, and needs no secret. This is the property that makes
B0 conflict-extractable (requirements R3, R4 and R5 of `parameters.md` §4).

**Assumption.** None beyond the assumptions of §4, §6 and §7. In particular, attribution requires
no knowledge beyond the two certificates and the public registry.

**Reference:** `extract_b0`, `:434-452`.

---

## 10. Step 10 — blame, one seat at a time

**Purpose.** The per-seat query a caller makes after extraction: "is *this* seat a verifiable
double-authorizer?"

**Procedure.** `verify_blame_b0(frame0, frame1, registry, provider, expected_cfg, seat)` returns
true iff

1. `seat` is an integer, is not a boolean, and lies in `0 … 63`;
2. both frames verify;
3. the domains are equal;
4. the messages differ;
5. the seat's bit is set in **both** bitmaps.

Any error path returns `false`.

**Inputs and outputs.** a seat index and two frames; a boolean.

**Failure mode.** Every exception maps to `false`. A rejection is never an acceptance in this
procedure.

**Why it is a wrapper, not a mechanism.** It re-verifies both frames, so it adds no evidence of its
own; it is a convenience over §8 and §9 with a fixed shape. Blame reports `false` for a seat that is
absent from either bitmap even when that seat did sign the other message — correctly, because blame
answers "did this seat authorize both", not "did this seat authorize something".

**Assumption.** Same as §9.

**Reference:** `verify_blame_b0`, `:455-465`.

---

## 11. Where each step's correctness comes from

| Step | Correctness source | Label |
|---|---|---|
| 1 framing | deterministic parsing; the `payload_len` equality | construction, checked by tests |
| 2 hash | SHAKE256 domain separation with length prefixes | concrete-function assumption |
| 3 registry/`cfg` | collision resistance of SHAKE256 at 64 bytes | standard assumption |
| 4 two-sided `cfg` | registry authentication: frame cannot claim a foreign key list | construction |
| 5 width/length | fixed-slot layout | construction, checked by tests |
| 6 bitmap | popcount = 43; bit numbering normative | construction, checked by tests |
| 7 signature block | **EUF-CMA of the chosen scheme (`A-sig`)** | named assumption about non-FIPS candidates |
| 8 conflict detection | equal `cfg`, equal domain, different message | construction |
| 9 extraction ≥ 22 | `|S₀ ∩ S₁| ≥ 2Q − N = 22` — set arithmetic | proved, and exhaustively checked at small `n` |
| 9 extraction public | bitmap in the clear + positions fixed by the bitmap | construction |
| 10 blame | re-verification plus a seat test | construction |

The frame logic as a whole is **not formally verified**. It is checked by the reference's 39 unit
tests and by the independent implementation's 6,701 of 6,701 agreement over 900 vectors. Those are
checks, not proofs.

---

## 12. The security statement that uses all of this

The construction above is the *mechanism*. The *statement* about it is Theorem A of the QPT-128
finalization (`domains/06-qpt128-security-target/`), which says, for the public-signer profile:

- **Accountability is deterministic.** Two accepted certificates on different messages expose at
  least 22 seats, each with two verifying signatures. There is no probability in this part.
- **Non-frameability and safety reduce tightly and linearly to EUF-CMA of the signature scheme**,
  with a loss of 64 and no extractor. That tightness is a property of B0 specifically: the evidence
  is the public signature, so the reduction does not have to run an online extractor. A hidden-signer
  profile cannot do this, and its reduction must pay the extractor's cost.
- **Quorum unforgeability.** With at most 21 corrupt seats, every accepted certificate on `(d, m)`
  carries at least 22 honest-seat signatures on `m`. So at least 22 honest seats really approved
  `m`, except with probability at most `64·Adv_Σ`.
- **QPT-128.** With the category-5 envelope in gate units, the programme's target D2 holds with a
  **+23.0-bit margin**, and `Pr ≤ 2^−25` at `2^128` gates.

The label on all of this is **theorem with proof under the named assumption `A-sig`**. It is not a
statement that OV-V, SNOVA or any other scheme *is* category 5: that is the submitters' claim.

---

## 13. Profile B1 in the same order (for contrast)

B1 shares steps 1 to 4 unchanged, with `suite = 0x44B1` and `width = 128`. It then diverges.

| Step | B0 | B1 |
|---|---|---|
| 5 width/length | `W` = scheme width, `payload_len = 8 + 43·W` | `W = 128`, `payload_len = 5,504 + proof_len`, `proof_len ≤ 27,056` |
| 6 signer set | 8-byte bitmap, popcount 43 | 43 handles, **strictly increasing by the 64-byte link** `L`; no bitmap |
| 7 slots | 43 signatures over `vote_i` | 43 `(L, Z)` pairs plus one proof over the handle list |
| 8 conflict | equal `cfg`, equal `d`, different `m` | same |
| 9 extraction | bitmap intersection | merge the two handle lists on `L`; for each matched link recover `seat` from `Z₀ XOR Z₁` through a division-free identity table; reject a zero or out-of-range identity and a duplicate identity; require at least 22 findings |
| result label | verified attribution | `ALGEBRAIC_CANDIDATES_ONLY` |

The handle is

```
pair = SHAKE256(b"CEQS/P1" ‖ x ‖ D)[:128]     (135-byte input)
L    = pair[:64]
Z    = (int(pair[64:]) XOR mul(int(m), seat+1)) in GF(2)[X]/(X^512 + X^8 + X^5 + X^2 + 1)
```

so `L` repeats across messages in the same domain and `Z` carries the message linearly. The XOR with
`mul(m, seat+1)` is what makes two certificates on different messages cancel on a seat's link.

**Two facts must be stated whenever B1 is described.**

1. `verify_b1` returns `status = STRUCTURE_ONLY_NO_QUALIFIED_PROOF` and
   `authorization_verified = False`, **by construction**: the only backend in the module is
   `StructureOnlyTestBackend` (`qualified = False`, its "proof" is a fixed 40-byte marker that
   `verify` compares). A qualified backend does not exist in this repository.
2. `extract_b1` returns algebraic candidates and says so in its own output:
   `requires_before_attribution: "Authenticate cfg and verify two qualified B1 authorization
   proofs."` Without those proofs an extracted seat is a candidate, not an attribution.

B1's extractor is a port of the v1.34 division-free decoder, owned by
`domains/05-extraction-and-signature-reductions/`. That layer is what makes the whole profile
tractable at all; `domains/05-extraction-and-signature-reductions/` carries the argument for why the
extractor is the load-bearing part.

**Reference:** `register_key_b1`, `context_b1`, `handle_b1`, `check_relation`, `parse_b1`,
`verify_b1`, `extract_b1`, `:731-1013`.
