# The B0 frame as bytes

This document is normative for the byte layout of a profile B0 frame (suite `0x44B0`). Where it and
`domains/07-compact-certificate-b0/docs/b0-wire-spec.md` differ, the specification governs; this
document adds the offset table, the worked hexadecimal examples, and the precise statement of where
the format's guarantees stop.

Everything is big-endian. "Offset" is 0-based from the first byte of the frame. Field widths in
bytes. The header is one packed structure:

```
HEADER_FORMAT = '>4sHH64s64s64sHHI'          struct.calcsize = 208
```

---

## 1. Header, bitmap, signature block

| offset | width | field | encoding | valid range and rule |
|---:|---:|---|---|---|
| 0 | 4 | `magic` | ASCII, fixed | must equal `CQ44` |
| 4 | 2 | `version` | `u16` big-endian | must equal `44` (`0x002C`) |
| 6 | 2 | `suite` | `u16` big-endian | `0x44B0` for B0, `0x44B1` for B1; any other value rejects |
| 8 | 64 | `cfg` | opaque bytes | must equal the verifier's authenticated `expected_cfg` **and** the value recomputed from the registry |
| 72 | 64 | `domain` | opaque bytes | any 64 bytes; equal in both frames of a conflict |
| 136 | 64 | `message` | opaque bytes | any 64 bytes; **different** in the two frames of a conflict |
| 200 | 2 | `count` | `u16` big-endian | must equal `43` (`0x002B`) |
| 202 | 2 | `width` | `u16` big-endian | B0: the scheme's signature width `W`, `1 ≤ W ≤ 757`; B1: `128` |
| 204 | 4 | `payload_len` | `u32` big-endian | B0: `8 + 43·W`; B1: `5,504 + proof_len`, at most `32,560`. Must equal the byte count actually after the header |
| **208** | **8** | **`bitmap`** | `u64` big-endian | popcount exactly `43`; bit value `2^i` set ⇔ seat `i` signed (seat 0 = least significant bit) |
| 216 | `43·W` | `signatures` | `W` bytes each | one per set bit of the bitmap, in **ascending seat order** |

Total frame length is `208 + 8 + 43·W = 216 + 43·W` for B0.

The **216-byte header-plus-bitmap** is the fixed prefix of every B0 frame: 208 header bytes plus the
8-byte bitmap. Only the signature block that follows varies with the scheme.

For B1 the payload after the header is 43 handles of 128 bytes each (`5,504` bytes) followed by the
proof; `width` is `128` and `payload_len` is `5,504 + proof_len`.

**What is signed.** Seat `i`'s signature covers the plain concatenation

```
vote_i = b"CQ44/B0/VOTE" ‖ cfg ‖ domain ‖ message ‖ u8(i)
```

a fixed **12 + 64 + 64 + 64 + 1 = 205 bytes** — the 12-byte literal `CQ44/B0/VOTE`, then the three
64-byte fields, then the seat index as one byte. `cfg` inside the signed message binds the signature
to the exact 64-key registry; `u8(i)` binds it to the seat. The construction of `cfg` and the hash
`H` are in `construction.md` §§2–3.

This concatenation is **plain**, with no length prefixes — unlike `H`, which prefixes every part
with its length. The two must not be confused: `cfg` is produced by `H`, the vote message is not.
The independent implementation records this as design note 15 in
`domains/11-independent-audit-stack/independent-b0/SPEC_GAPS.md`: *"an implementer who assumes
everything goes through `H` gets different bytes."*

---

## 2. Encoding a frame

Given a registry of 64 distinct non-empty keys, 64 secret keys aligned index-for-index with the
public keys, exactly 43 distinct seats in `0 … 63`, a 64-byte `domain`, a 64-byte `message`, and a
provider of width `W`:

1. `cfg = H(b"CQ44/cfg/B0", scheme_id, pk_0, …, pk_63)`.
2. Sort the seats ascending. For each, sign `vote_i` with `secret_keys[i]`. A signature that is not
   exactly `W` bytes is **refused, not padded**.
3. `bitmap = OR over the seats of (1 << i)`.
4. Emit `header ‖ bitmap.to_bytes(8, "big") ‖ sig_0 ‖ sig_1 ‖ … ‖ sig_42`, with the header built by
   `HEADER_FORMAT` and `payload_len = 8 + 43·W`.

---

## 3. Worked example — a complete B0 frame, decoded

The example below is produced by the repository's reference module with its symbolic test double at
width 32. It is reproducible with the command in §7. Every value here was read from that run.

**Parameters of the example.** `W = 32`, 43 seats `0 … 42`, `domain = 00 01 02 … 3F` (the 64 bytes
`0x00` to `0x3F`), `message =` 64 zero bytes, `scheme_id = CQ44/test-scheme`, registry keys
`pk_i = "SYM-PK-" ‖ u64be(i+1)`.

**Frame length.** `216 + 43·32 = 216 + 1,376 = 1,592` bytes. Signals:
`payload_len = 1,384` (`0x00000568`).

### 3.1 The 208-byte header

```
43513434 002c 44b0
c1c661b846acc0f11334373cc4d8be288a4ae4649cacd4513b07390c287cf240
822368af909aa1c98d627d52eef4709efccef595d6452300f8c16fb319a5d13f
000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
002b 0020 00000568
```

Field by field, with offsets:

| offset | bytes | value | reading |
|---:|---|---|---|
| 0–3 | `43513434` | `CQ44` | magic |
| 4–5 | `002c` | 44 | version |
| 6–7 | `44b0` | `0x44B0` | **profile B0** |
| 8–71 | `c1c6…f240` | 64 bytes | `cfg`, the SHAKE256-derived configuration |
| 72–135 | `0001…3e3f` | 64 bytes | `domain` (the ramp `0x00…0x3F`) |
| 136–199 | `0000…0000` | 64 zero bytes | `message` |
| 200–201 | `002b` | 43 | `count` |
| 202–203 | `0020` | 32 | `width` `W` |
| 204–207 | `00000568` | 1,384 | `payload_len` `= 8 + 43·32` |

Header digest: SHA-256 of the 208 header bytes is
`6fb2fed1e2593eac9a42e623b99b7fcb20c970070454fe6da73239171b25dbd9`.

The `cfg` value is a function of the registry only. With the toy registry above it is
`c1c661b846acc0f11334373cc4d8be288a4ae4649cacd4513b07390c287cf240822368af909aa1c98d627d52eef4709efccef595d6452300f8c16fb319a5d13f`.
A different key list gives a different `cfg` and every frame built for it is rejected by a verifier
holding the first.

### 3.2 The 8-byte bitmap

```
000007ffffffffff
```

As an integer: `0x000007FFFFFFFFFF`, which is `2^43 − 1`; its popcount is **43**. Bit `i` is set for
every `i` in `0 … 42`, so the frame's signer set is seats 0 through 42.

A second frame on a different message, with seats `0 … 21` and `43 … 63`, carries

```
fffff800003fffff
```

which is `0xFFFFF800003FFFFF`: again popcount 43, with bits `0 … 21` and `43 … 63` set. The
intersection of the two bitmaps is `0x00000000003FFFFF`, whose popcount is **22** — the two frames
share exactly seats `0 … 21`, the minimum possible.

### 3.3 The signature block

The block begins at offset 216. The first two slots, in ascending seat order (seat 0 then seat 1),
are:

```
seat 0 slot (offset 216): 53594d5349479b0c7d53a2abb5772bcac5c6f9d3ca3900000000000000000000
seat 1 slot (offset 248): 53594d534947f97d8e77ed8609ae0931aea18ba66b5100000000000000000000
seat 42 slot (offset 216+42·32 = 1560): 53594d5349479749dd8753043056ae09484fcdcb500200000000000000000000
```

The first six bytes `53594d534947` are ASCII `SYMSIG`, the marker of the symbolic test double used
for the example. The signature is 32 bytes; the trailing ten zero bytes are the test double's
padding, not a property of any real scheme. A real scheme's 32-byte signature would fill the slot
with 32 bytes of its own output, and the frame length would be identical.

The whole frame hashes (SHA-256) to
`f82f800dbe7f9e63347f57b3d7013111de1de87bf555b670453f9eaa569f0a4e`; the conflicting frame of §3.2
to `fd7c2a774ea390f47850e2d48ba860b4472f0d0fa1675255eea361ec9aba38c0`.

### 3.4 Verifying and extracting the example

Verifying the first frame returns seats `(0, 1, …, 42)` and width 32. Verifying the second returns
`(0, 1, …, 21, 43, 44, …, 63)`. Extraction over the pair returns, ascending by seat,

```
(0, 0, 0) (1, 1, 1) … (21, 21, 21)
```

i.e. seat `s` found at 0-based position `s` in both frames — 22 triples, each naming the seat and the
positions of its two signatures. `verify_blame_b0` returns `true` for seat 0 and `false` for seat 30
(seat 30 is set in the first bitmap but not the second).

---

## 4. A B0 frame with a real scheme

The same layout at each measured width `W`, with frame length `216 + 43·W`. The widths `W` are
**measured** (the library's declared signature length, recorded per scheme in
`domains/07-compact-certificate-b0/results/real-demo.json`); the `payload_len` and its hex are
**arithmetic** on `W` (`8 + 43·W`), which the same run asserts equals the emitted frame's length.
Nothing here was read out of a frame's bytes.

| Scheme | `width` field (`u16` hex) | `payload_len` (`u32` hex) | Frame length |
|---|---:|---:|---:|
| OV-V-pkc | `0104` (260) | `00002BB4` (11,188 = 8 + 11,180) | 11,396 |
| SNOVA_29_6_5 | `01C6` (454) | `00004C4A` (19,530) | 19,738 |
| SNOVA_60_10_4 | `0240` (576) | `000060C8` (24,776) | 24,984 |
| OV-V-pkc‖SNOVA_29_6_5 | `02CA` (714) | `000077F6` (30,710) | 30,918 |
| MAYO-5 (oversize) | `03C4` (964) | `0000A1F4` (41,460) | 41,668 — rejected |
| ML-DSA-87 (oversize) | `1213` (4,627) | `00030939` (198,969) | 199,177 — rejected |
| Falcon-padded-512 (category 1) | `029A` (666) | `00006FE6` (28,646) | 28,854 |

Only the `width` and `payload_len` fields and the length of the signature block change. Every other
byte of the header is the same for a given registry, domain and message. These four frames were
produced and verified by the `--real-demo` run recorded at
`domains/07-compact-certificate-b0/results/real-demo.json`; the sizes and their provenance are in
`sizes.md`.

---

## 5. A B1 header, for contrast

A B1 frame for the same domain and a zero message, with 43 handles and the 40-byte structure-only
marker as its "proof", has this header:

```
43513434002c44b1
a9076a6c49d0c062b2ae0f7b3846a68537a00c9e90dc1c18301bc78f0d7995e2
bd5a0c60274d42580c116fbc8d8400ef0a74cb5ddd33b6d9bafdba00d79c4011
000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000000
002b 0080 000015a8
```

Only two header fields differ from the B0 example: `suite` is `44b1` (profile B1) and `width` is
`0080` (128). `payload_len` is `0x15A8` = 5,544 = 5,504 handles + 40 proof bytes, and the frame is
5,752 bytes. The first handle (offset 208, 128 bytes) is

```
0836273792ec84dcc3abc7a61f8badb791b069d9c350e189e69b7e9857b033b6
69da10af9ba758cb16539fae983c5a26ce30657cabbb3c7170fabd8b7809337b
5ba95c93d8dc3eed14b22458b538646bfd28d686379e697ccc5441b74000798
2965eec3a118a86b997a4233ca02faaad24afb1d6117e676ca5eac2dc1c3d8849
```

whose first 64 bytes are the link `L` and whose last 64 bytes are the masked identity `Z`. The proof
region holds the ASCII marker `STRUCTURE-ONLY/NOT-A-PROOF/CQ44-B1/v1.44` (`5354525553545552452d4f4e4c592f4e4f542d412d50524f4f462f435134342d42312f76312e3434`).
`verify_b1` on this frame reports `STRUCTURE_ONLY_NO_QUALIFIED_PROOF` and
`authorization_verified = False` — the marker is not a proof, and no qualified backend exists.

---

## 6. Where the guarantees of this format stop

### 6.1 The encode-side size cap is not enforced (finding F6)

The wire specification makes the refusal normative. Section 11 item 10 of
`domains/07-compact-certificate-b0/docs/b0-wire-spec.md` states: *"`encode` must refuse to emit a
frame longer than 32,768 bytes (`W ≤ 757` for the 208 + 8 + 43·W layout)"*. This is gaps 16 and 17
of the independent implementation, which found the obligation implicit in §6 and implemented it.

**The v1.44 reference does not implement it.** Measured, not inferred:

```
encode_b0 width=758: emitted 32810 bytes (gate is 32768); b0_fits(758)=False
verify_b0 of the oversize frame: FrameError: frame exceeds the 32768-byte portability bound
```

So an encoder built from the reference at `W = 758` produces a 32,810-byte frame without raising,
and a conforming verifier then rejects that frame at the first check. This is a **documented gap**,
recorded as an open item, deliberately not silently fixed: the reference must stay the revision the
measurements were taken on. An implementer of this specification must add the encode-side refusal
themselves; an implementation that omits it produces frames no conforming verifier will accept.

### 6.2 Two reference tests do not exercise the check they name (finding A.10)

This is a defect in the test suite, not in the format, but it is a place where a reader could be
misled about coverage. Two tests mutate the frame at offsets from the *earlier* CEQS29 body layout
while their names claim the CQ44 header checks:

| test | offset it writes | field it meant to write | rejection actually produced |
|---|---|---|---|
| `test_wrong_message_rejected` | `144:208` | message, offsets `136:200` | `count must be 43` (misaligned) — the aligned write gives `signature for seat 0 does not verify` |
| `test_width_mismatch_rejected` | `206` | width, offset `202` | `payload_len does not match the trailing bytes` (misaligned) — the aligned write gives `header width does not match the provider width` |

Both tests pass, and neither exercises the check its name claims. The correct offsets are `136` for
the message and `202` for the width; both were replayed and produce the intended rejections. This is
also an open item: fix or relabel the two tests, and add a dedicated width-field test.

### 6.3 The bound itself is a project decision, not a cryptographic limit

32,768 bytes is an engineering gate the programme chose. It is not derived from any security
parameter. Nothing in §1 changes if the gate moves; only the value of `W` that fits changes, and
with it the set of admissible signature schemes.

### 6.4 What the format does not bind

- It does not bind a *raw* message. `message` is a 64-byte field, and for B0 any 64 bytes are
  accepted; canonicalisation of an upstream raw message into those 64 bytes is outside this format.
- It does not bind liveness, key management, or any network protocol. It is a frame format and a
  pair of public algorithms over it.
- The reference implementation is not constant-time, and no side-channel testing was performed.

---

## 7. Reproducing the worked examples

The examples of §§3 and 5 come from the repository's reference module and need no third-party
package. From the repository root, in an environment with Python 3:

```
python3 - <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location(
    'sc', 'domains/07-compact-certificate-b0/src/sidecar_free_certificate.py')
m = importlib.util.module_from_spec(spec); sys.modules['sc'] = m
spec.loader.exec_module(m)
p = m.SymbolicSignatures(width=32)
reg, sks = m._b0_registry(p)
cfg = m.cfg_b0(reg)
f0 = m.encode_b0(reg, p, m._DOMAIN, m._msg(0), sks, list(range(m.QUORUM)))
f1 = m.encode_b0(reg, p, m._DOMAIN, m._msg((1 << 400) | 7), sks,
                 list(range(m.MIN_OVERLAP)) + list(range(m.QUORUM, m.N)))
print(len(f0), f0[:208].hex(), f0[208:216].hex(), f0[216:248].hex(), sep='\n')
print([(x.seat, x.position0, x.position1) for x in m.extract_b0(f0, f1, reg, p, cfg)][:3])
PY
```

Expected output: `1592`, the header of §3.1, the bitmap `000007ffffffffff`, the seat-0 slot of §3.3,
and `[(0, 0, 0), (1, 1, 1), (2, 2, 2)]`.

`SymbolicSignatures` is a labelled test double, not a signature scheme: it records the triples it
issued and verifies by membership. It exists so the frame logic can be exercised deterministically
without a real library. The vectors of the independent implementation use the specification's own
deterministic SHAKE toy scheme (`scheme_id = toy-shake-32`, also 32 bytes wide), so their frames are
the same length as the ones here but carry different signature bytes.
