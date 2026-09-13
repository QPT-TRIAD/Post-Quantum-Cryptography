# SPEC_GAPS — ambiguities and underspecification in B0_wire_spec_v1.44.md

Recorded while implementing `b0_indep.py` from the specification alone (no reference
source consulted). For each item: the clause, the ambiguity, and the reading I chose.
Items marked **[observable]** could change wire bytes or verdicts; the rest affect only
API shape or unreachable branches.

## Observable on the wire / on verdicts

1. **§6 bitmap bit numbering [observable].** "bitmap u64 (bit i set ⇔ seat i signed)" does
   not say whether "bit i" is the value bit `2^i` (LSB = seat 0) or the i-th bit of the
   big-endian byte string (MSB-first). I chose the value bit `2^i`, serialised as u64 BE.
   The other reading would produce different bytes for every frame.
2. **§6 encode has no secret-key input [observable for non-canonical registries].**
   `encode(registry, domain, message, seats)` must sign, but §5 only defines `sk_i` by
   *index* (`b"SK" ‖ u16be(i)`) while toy `verify` derives `sk` from the *registry pk*
   (`b"SK" ‖ pk[2:]`). These coincide only when `pk_i = b"PK" ‖ u16be(i)`. I sign with
   `sk_i` by seat index. For a permuted/non-canonical registry the spec gives no rule.
3. **§5 toy `verify` prefix check [observable for odd pks].** "recompute with
   `sk = b"SK" ‖ pk[2:]`" never says to check `pk[:2] == b"PK"`, so a pk such as
   `b"ZZ\x00\x05"` verifies seat-5 signatures. I followed the text literally (no check).
4. **§10 vector-file format [observable for the checker].** §10 describes per-case
   `registry` and a single `frame`; the actual file has one top-level `registry`/`cfg`,
   cases with `frame0/frame1`, `message0/message1`, `seats0/seats1`, `kind`,
   `expected_extract`, `expected_verify`. Public keys are hex but `scheme_id` is a plain
   string; the encoding of `scheme_id` is unspecified (I try hex, else UTF-8).

## Rejection / result shape

5. **§7 / §8 form of rejection.** "any failure rejects" does not say raise vs return
   None/False; §9's "any exception path → False" suggests raising is expected somewhere.
   I return `None` (and expose `verify_reason` / `extract_reason` with clause strings).
6. **§7.1 "frame is a byte string".** `bytes` only, or also `bytearray` / `memoryview`?
   I accept `bytes` and `bytearray`.
7. **§7.4 `expected_cfg` type.** Length/type not stated; whether `None` means "skip" is
   not stated. I require exactly 64 bytes and reject otherwise.
8. **§9 `seat` type.** "0 ≤ seat ≤ 63" — `bool` is an `int` subclass in Python, and
   `3.0 == 3`. I require `int` and refuse `bool`/float.
9. **§2 error type** for non-bytes parts is unspecified ("is an error"); I raise
   `TypeError`. Whether such an error inside `verify` counts as a rejection is implied
   only by §9. (Only reachable through a malformed registry.)
10. **§3 registry validation location.** §3 defines validity (64 distinct non-empty
    keys) but §7 never says the verifier must validate the registry; I validate it
    inside `cfg()` so §7.4 rejects a malformed registry.

## Redundant / unreachable clauses (cannot be exercised by vectors)

11. **§7.5 vs §7.3.** Once `PAYLOAD_LEN == len(payload)` (7.3) and `WIDTH == W` (7.5),
    "payload length = 8 + 43·WIDTH" is an independent check only if `PAYLOAD_LEN` was
    forged consistently with a wrong tail; both orders reject the same frames.
12. **§8.2 "reject if cfg differ"** is unreachable: §7.4 forces both cfgs to equal
    `expected_cfg`. Likewise **§8.3** (overlap < 22) is unreachable for two valid frames,
    as the spec itself notes. Neither branch can be validated by vectors.
13. **§9 blame** does not restate cfg equality or the ≥ 22 overlap; both are implied by
    §7 but an implementer might add them. No behavioural difference.
14. **§7 check order** is unspecified; only reason strings differ, not accept/reject.

## Design notes (clear, but easy to misread)

15. **§4 and §5 use plain concatenation** (`vote_i`, `TOYSIG ‖ sk ‖ msg`) while §2/§3
    use length-prefixed `H`. The text is unambiguous, but an implementer who assumes
    everything goes through `H` gets different bytes. Worth a one-line warning.
16. **§6 bound on W** is implicit: `WIDTH` is u16 and `MAX_FRAME_BYTES = 32768` imply
    `W ≤ 757`; encode's obligation to reject oversize frames is not stated (I check it).
17. **§7.1 MAX_FRAME_BYTES** is inert for the toy provider (every frame is 1592 bytes);
    `trailing` vectors are rejected by §7.3, never by §7.1.
18. **§5 "constant width 32"** — presumably "constant-time compare of fixed width"; I
    use `hmac.compare_digest`. No effect on verdicts.
