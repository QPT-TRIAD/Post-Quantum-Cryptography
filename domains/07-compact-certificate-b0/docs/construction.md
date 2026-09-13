# CE-QS profile B0 — the compact certificate, end to end

This document explains the construction that the domain's two profile frames implement, in the
order a reader needs it: the requirement first, then the frame, then the extraction rule, then the
size arithmetic, then the result that closes the hidden-signer route, then the honest status of
every claim. Every number carries its source. Revision labels (v1.24, v1.29, v1.34, v1.43, v1.44)
are the project's own revision numbers; only the revisions that the file map copies into this
repository exist here, and a project file named below but not copied is marked as such.

Unless stated otherwise, pointers of the form `:N` into the evidence module refer to line numbers
of the source-tree revision `sidecar_free_certificate_v1.44.py`, which is copied into this
repository as `../src/sidecar_free_certificate.py`. Paths are relative to the repository root. The
copy carries the same code; it differs from the source revision only by rewritten path references,
and those additions shift the line numbers by a fixed offset that grows in steps, so a reader can
still find each pointer:

| source-revision lines | repository-copy lines | offset |
|---|---|---:|
| 1–9 | 1–9 | 0 |
| 10–88 | 16–94 | +6 |
| 90–1024 | 98–1032 | +8 |
| 1026–1065 | 1038–1077 | +12 |
| 1068–1965 | 1082–1979 | +14 |

---

## 1. The problem

CE-QS is a 64-seat committee. A quorum is `Q = 43` signatures; the fault bound is `F = 21`
corrupt seats; `2Q − N = 22 = F + 1`. A certificate is a portable object that a verifier holding
only the authenticated 64-seat registry can check, and from which two conflicting certificates
publicly expose the seats that authorized both. The project's seven requirements, as the v1.44
closure document states them (each with its own pointer there, `docs/sidecar-free-finalization.md`
§1):

| Id | Requirement |
|---|---|
| R1 | the whole certificate is at most 32,768 bytes |
| R2 | a verifier with the fixed authenticated registry checks the certificate alone |
| R3 | two conflicting accepted certificates publicly yield ≥ 22 double-authorizers |
| R4 | no proof file, omitted opening, external leaf list or transcript |
| R5 | no opener's secret at extraction time |
| R6 | seat indices and credentials stay private (hidden signers) |
| R7 | QPT-128, fixed in v1.43 as a gate work factor with gate accounting |

**Why this is hard.** Three constraints pull against each other.

1. **Overlap is a counting fact, not a cryptographic one.** Any two 43-seat sets out of 64 share
   at least `43 + 43 − 64 = 22` seats. So the conflict witness exists *if* both certificates are
   authentic. The difficulty is making that witness *publicly computable* from the two
   certificates alone, without a secret opener and without a sidecar (R4, R5).
2. **The size budget is tight for post-quantum signatures.** 32,768 bytes for 43 signatures leaves
   757 bytes per signature (this section's arithmetic in §4). FIPS-standardized signatures do not
   fit: ML-DSA-87 is 4,627 bytes and SLH-DSA-SHAKE-256s is 29,792 bytes. The candidates that fit
   are in NIST's additional-signature process, not FIPS standards.
3. **Privacy and size collide.** If the signers must stay hidden (R6), each seat contributes a
   handle plus a share of one joint proof, and the whole proof must fit 27,056 bytes. As of this
   revision no proof system that meets R7 fits (Theorem C, §7). This is the *unmet* half of the
   requirement, and it is stated as unmet everywhere it appears.

The v1.24 contents contract lays the certificate out as a 208-byte context, 43 handles (5,504 B)
and one joint proof (≤ 27,056 B). It does not forbid a different layout, but a replacement must
supply its own public extraction mechanism (contract `docs/02-ceqs-construction-evolution/docs/
32kib-contents-contract.md`; as cited in the v1.44 closure document §1). Profile B0 is such a
replacement: the bitmap and the public signatures *are* the extraction mechanism.

---

## 2. The frame: one header, two profiles

### 2.1 Header (208 bytes, both profiles)

`struct '>4sHH64s64s64sHHI'`, `HEADER_BYTES = 208` (`:155-156`):

| offset (B) | field | type / value |
|---:|---|---|
| 0–3 | magic | ASCII `CQ44` |
| 4–5 | version | u16 = 44 |
| 6–7 | suite | u16: `0x44B0` (B0, public signer set) or `0x44B1` (B1, hidden signers) |
| 8–71 | `cfg` | 64 bytes, the authenticated configuration |
| 72–135 | `domain` | 64 bytes, the conflict domain |
| 136–199 | `message` | 64 bytes |
| 200–201 | `count` | u16 = 43 |
| 202–203 | `width` | u16: signature width `W` in B0; 128 in B1 |
| 204–207 | `payload_len` | u32, number of bytes after the header |

`parse_frame` rejects a non-`bytes` frame, a frame shorter than 208 bytes, a frame longer than
32,768 bytes, a wrong magic/version/suite/count, and any mismatch between `payload_len` and the
trailing byte count — that last check is what catches truncation and trailing data (`:295-316`).

These offsets are **not** the CEQS29 body offsets (16/80/144) used by earlier revisions. The
consequence of that difference is recorded in §9.

### 2.2 Hash

`H(label, p_1, …, p_k) = SHAKE256( u64be(len(label))‖label ‖ u64be(len(p_1))‖p_1 ‖ … )[:64]` —
an eight-byte big-endian length prefix before the label and before every part, squeezed to 64 bytes
(`:208-214`). Every part must be `bytes`; anything else raises. This is the domain-separated hash
of the v1.29 revision with an explicit leading label.

### 2.3 Registry, configuration, vote message

A registry is exactly 64 distinct non-empty public keys `pk_0 … pk_63` plus a byte string
`scheme_id`; `cfg = H(b'CQ44/cfg/B0', scheme_id, pk_0, …, pk_63)` (`:348-364`). Validation of the
registry happens inside `cfg_b0`, so every verification that recomputes `cfg` validates it.

Seat `i`'s approval message is a plain concatenation, not an `H` call (`:367-372`):

```
vote_i = b'CQ44/B0/VOTE' ‖ cfg ‖ domain ‖ message ‖ bytes([i])
```

signed with the scheme's pure signing API and an empty external context. `cfg` is in the signed
message, so a signature is bound to the exact 64-key registry, and `domain` and `message` are
bound separately, so two certificates can conflict on the message while sharing the domain.

### 2.4 The two profiles

| | B0 (suite `0x44B0`) | B1 (suite `0x44B1`) |
|---|---|---|
| payload | 8-byte bitmap ‖ 43 fixed-width signatures | 43 handles (128 B each) ‖ one proof |
| `payload_len` | `8 + 43·W` | `5,504 + proof_len` |
| frame | `216 + 43·W` | `5,712 + proof_len`, `proof_len ≤ 27,056` |
| signers | public (bitmap) | hidden |
| status | executable reference, measured | frame and relation executable; **no qualified proof backend** |

`B0_FIXED_BYTES = HEADER_BYTES + 8 = 216`; `B1_PREFIX_BYTES = HEADER_BYTES + 5,504 = 5,712`;
`B1_PROOF_MAX = 32,768 − 5,712 = 27,056` (`:158-170`).

---

## 3. Profile B0 end to end

Each step names the property it needs.

### 3.1 Encoding (`encode_b0`, `:379-403`)

Requires: a registry of 64 distinct non-empty keys; 64 secret keys aligned index-for-index with the
public keys; exactly 43 distinct seats in `0..63`; a 64-byte domain and message; and a provider
whose signature width is the *exact* slot width (a signature that is not exactly `width` bytes is
refused, not padded).

1. compute `cfg = cfg_b0(registry)`;
2. sort the seats ascending and sign `vote_i` for each with `secret_keys[i]`;
3. build the bitmap as `OR(1 << i)` over the seats;
4. emit `header ‖ bitmap.to_bytes(8,'big') ‖ sig_0 ‖ … ‖ sig_42`.

The 43 signatures appear in ascending seat order, and the bitmap says which seats they belong to.
Note the asymmetry that finding F6 records (§9): the encoder does **not** itself refuse a frame
longer than 32,768 bytes, although the wire specification makes that refusal normative.

### 3.2 Verification (`verify_b0`, `:406-431`)

All eight checks, any failure rejects:

1. `expected_cfg` is exactly 64 bytes;
2. `parse_frame` (§2.1), including the 32,768-byte bound;
3. header `cfg` equals the caller's authenticated `expected_cfg`;
4. header `cfg` equals `cfg_b0(registry)` (which validates the registry);
5. header `width` equals the provider's width, and is positive;
6. `len(payload) == 8 + 43·width`;
7. `bitmap.bit_count() == 43`;
8. for each set bit `i`, at position `p` among the set bits, `provider.verify(pk_i, vote_i,
   payload[8+p·W : 8+(p+1)·W]) is True`.

Checks 3 and 4 together are the registry authentication: a caller who holds the registry's
authenticated `cfg` (for example from a trusted configuration) rejects any frame whose keys differ
from that registry, and the recomputation from the registry rejects a frame built for a different
key list. A certificate therefore cannot claim a registry that the verifier does not already hold.

`VerifiedB0` returns `(cfg, domain, message, width, bitmap, seats)`.

### 3.3 Extraction (`extract_b0`, `:434-452`)

1. verify both frames completely — all 86 signatures;
2. reject if the two `cfg` differ, if the domains differ, or if the **messages are equal**
   (equal messages are not a conflict);
3. `common = bitmap0 AND bitmap1`; reject if `popcount(common) < 22`;
4. output, ascending by seat, `(seat, position0, position1)` for every common seat, where a
   position is the seat's 0-based index among its frame's set bits.

The two signatures at `(position0, position1)` are the public evidence: anyone can verify them
against the registry's public keys on the two conflicting messages. This is the property that
makes the certificate *conflict-extractable* with no opener (R3–R5): extraction is a bitmap
intersection plus 86 signature verifications, and the witness is public data.

Step 3's rejection cannot fire for two valid frames — `|S0 ∩ S1| ≥ 43 + 43 − 64 = 22` for any two
43-subsets of a 64-set — which the module says in a comment and the tests exercise for every
overlap from 22 to 43 (`:445-448`, `B0Tests.test_all_overlaps_22_to_43`).

### 3.4 Blame (`verify_blame_b0`, `:455-465`)

True iff the seat is an int in `0..63`, both frames verify, the domains are equal, the messages
differ, and the seat bit is set in both bitmaps. Any error path returns `False`. Blame is the
per-seat query a caller makes after extraction; it re-verifies both frames, so it is a convenience
wrapper, not an extra mechanism.

### 3.5 The seat-privacy property, stated exactly

B0 publishes an 8-byte bitmap. The seats that signed, their positions, and their public keys are
therefore public to anyone who has the registry. What stays private is only the *secret keys*: the
scheme's signatures reveal nothing about the signing keys beyond the standard signature security
notion. **B0 does not meet R6.** Any reader who needs hidden signers must look at §6, where the
status is that no proof system meeting R7 fits the slot.

---

## 4. Sizes and the size gate: the exact arithmetic

The tests assert these identities exactly, so they are arithmetic, not estimates.

```
|frame|      = 208 (header) + 8 (bitmap) + 43·W  =  216 + 43·W
W ≤ (32,768 − 216) // 43 = 32,552 // 43 = 757          (757 → 32,767 B fits)
                                                       (758 → 32,810 B does not fit)
216 + 43 · 260 = 216 + 11,180 = 11,396                 (OV-V-pkc)
216 + 43 · 714 = 216 + 30,702 = 30,918                 (OV-V-pkc‖SNOVA_29_6_5)
```

`B0_MAX_SIGNATURE_BYTES = 757` (`:170`); `test_size_gate` asserts `b0_fits(757) is True`,
`b0_fits(758) is False`, and the two frame sizes 11,396 and 30,918 (`:1588-1606`). The `--report`
output carries `b0_size_gate = {'sig_bytes_757_fits': true, 'sig_bytes_758_fits': false,
'frame_bytes_at_757': 32767}`.

Margins against the 32,768-byte bound: 32,768 − 11,396 = **21,372 bytes** for OV-V-pkc;
32,768 − 30,918 = **1,850 bytes** for the hybrid; 32,768 − 24,984 = 7,784 for SNOVA_60_10_4;
32,768 − 19,738 = 13,030 for SNOVA_29_6_5.

B1's arithmetic: `208 + 43·128 = 5,712`; `32,768 − 5,712 = 27,056` bytes for the proof,
`27,056 · 8 = 216,448` bits.

Registry cost, which is *not* per certificate: 64 OV-V-pkc public keys of 446,992 bytes each are
64 × 446,992 = 28,607,488 bytes ≈ 28.6 MB of fixed registry data. The hybrid registry is
64 × 449,712 ≈ 28.8 MB (public key `u32be(len(pk_a)) ‖ pk_a ‖ pk_b` = 4 + 446,992 + 2,716 =
449,712). For comparison, SNOVA_29_6_5 keys are 2,716 bytes and SNOVA_60_10_4 keys 8,016 bytes,
so a SNOVA-only registry is under 0.6 MB.

---

## 5. The measured size table, and what each number is

The module measures B0 frames with real signature libraries. The table below is the module's own
table (`docs/sidecar-free-finalization.md` §2), reproduced by `--real-demo` on 2026-09-13 in the
pinned verification environment, with every number equal to the recorded one.

**Environment of the measurement.** liboqs 0.16.0, tag `0.16.0`, commit
`5a1a854b0dc9f2141bdc771c555ee60c37950183`, built as a shared library with
`-DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON -DOQS_DIST_BUILD=ON`; liboqs-python 0.16.0;
pqcrypto 0.3.4 (the pqcrypto version of the original measurement was not recorded — see the open
items). Host: Ubuntu 24.04.4, x86_64, kernel 7.0.0-31, Python 3.12.3; the demo runs 8 scheme runs
over 7 distinct schemes and completed in 13.67 s in the recorded run and 19.8 s in this build's
re-run (host load, not a result change).

| Scheme (claimed category) | Signature B | Public key B | Frame B | Verified | Extracted | Blame | Tamper rejected |
|---|---:|---:|---:|---|---:|---|---|
| **OV-V-pkc** (5) | 260 | 446,992 | **11,396** | yes | 22 | yes | yes |
| SNOVA_29_6_5 (5) | 454 | 2,716 | 19,738 | yes | 22 | yes | yes |
| SNOVA_60_10_4 (5) | 576 | 8,016 | 24,984 | yes | 22 | yes | yes |
| **OV-V-pkc‖SNOVA_29_6_5** (5) | 714 | 449,712 | **30,918** | yes | 22 | yes | yes, both halves |
| MAYO-5 (5) | 964 | 5,554 | 41,668 | rejected as oversize | — | — | — |
| ML-DSA-87 (5), via pqcrypto and liboqs | 4,627 | 2,592 | 199,177 | rejected as oversize | — | — | — |
| Falcon-padded-512 (1) | 666 | 897 | 28,854 | yes, but category 1 | 22 | yes | yes |

**What kind of number each column is.**

- *Frame B* is arithmetic on the measured signature width (`216 + 43·W`); the width itself is
  taken from the library (`length_signature` for liboqs, `SIGNATURE_SIZE` for pqcrypto) and the
  demo asserts the frame length equals the formula.
- *Verified / Extracted / Blame / Tamper* are measurement outcomes of the demo's fixed procedure:
  64 keygens, two conflicting frames with exactly 22 common seats (`seats0 = 0..42`,
  `seats1 = 0..21 ∪ 43..63`), both frames verified, extraction required to return 22 seats, every
  blame checked, and one byte flipped inside the first signature (for the hybrid, one byte inside
  each half) with rejection required. Oversize frames are recorded as
  `oversize_rejected` with the message `frame exceeds the 32768-byte portability bound`.
- *Category* is the value the library claims (`claimed_nist_level`), which `OqsSignatures` requires
  to equal the declared category; it is a submitter claim, not this project's verdict.
- *Not measured here:* Falcon-padded-1024 (1,280 B, 55,256-byte frame) was executed only in a
  separate liboqs probe that is not archived; SQIsign-V (292 B → 12,772 B) and HAWK-1024
  (1,221 B → 52,719 B) are specification values, not runs.

**The bottom line of the table.** Four claimed-category-5 configurations produced verified frames
of at most 32,768 bytes with 22 publicly extracted seats and tamper rejection: OV-V-pkc,
SNOVA_29_6_5, SNOVA_60_10_4 and the OV-V-pkc‖SNOVA_29_6_5 hybrid. The hybrid's security claim is a
reduction sketch, not a theorem: a forgery on the combined slot contains a forgery of each half, so
`Adv_hybrid ≤ min(Adv_OV, Adv_SNOVA)` at essentially the same running time
(`docs/sidecar-free-finalization.md` §2, "Hybrid").

---

## 6. Profile B1 (hidden signers): what exists and what does not

B1 fixes a frame, a relation, an algebraic extractor and a QPT-128 ledger, and **no usable
certificate**. The reader must not read the B1 code as an implementation of R6.

- **Credentials and keys.** Seat `i` holds a 64-byte secret `x_i`; its registered key is
  `K[i] = SHAKE256(b'CEQS/K1' ‖ x_i)[:128]` (a 71-byte absorb input, one SHAKE256 block, 128-byte
  output); `cfg = H(b'CQ44/cfg/B1', K_0, …, K_63)` with duplicates rejected; the context is
  `D = H(b'CQ44/ctx', cfg, d)` (`:731-762`).
- **Handle.** `pair = SHAKE256(b'CEQS/P1' ‖ x ‖ D)[:128]` (135-byte input, one block);
  `L = pair[:64]` is the link; `Z = int(pair[64:]) XOR mul(decode(message), i+1)` in
  `GF(2)[X]/(X^512 + X^8 + X^5 + X^2 + 1)`, where `decode` reads the 64-byte message as a field
  element (`:765-776`). The XOR with a multiple of the message is what makes two certificates on
  different messages collide on a seat's link.
- **Payload.** 43 handles strictly increasing by `L`, then proof bytes (`:873-901`, `:904-934`).
- **Relation `check_relation`** (`:796-826`): the 43 seats are distinct, each credential opens its
  registered key, and each handle recomputes. It is checked by *seeing the private rows*, so it is
  the relation a qualified backend would have to prove in zero knowledge, not a proof.
- **Verification `verify_b1`** (`:937-958`) returns `status =
  'STRUCTURE_ONLY_NO_QUALIFIED_PROOF'` and `authorization_verified = False`. Those values are the
  computed ones — `status` is `QUALIFIED_PROOF_VERIFIED` only if the backend declares
  `qualified = True` *and* the proof is structurally accepted, and `authorization_verified` is
  exactly `qualified and structurally_accepted`, so a backend can only reach them by claiming
  qualified status itself. The only backend in the file is `StructureOnlyTestBackend`
  (`qualified = False`, its "proof" is a fixed marker that `verify` compares), and no qualified
  proof backend exists in this repository. The value is therefore always `False` here, but the
  reader should not mistake the constant for a hard-coded refusal: it is the composition of a
  structural check with a backend claim that nothing in this repository can truthfully make.
- **Extraction `extract_b1`** (`:961-1013`) is the v1.34 division-free decoder over parsed
  handles: it merges the two handle lists on `L`, recovers `seat = table[Z0 XOR Z1]` for each
  matched link, rejects a zero or out-of-range identity and a duplicate identity, and requires at
  least 22 findings. It reports `status = 'ALGEBRAIC_CANDIDATES_ONLY'` and
  `requires_before_attribution: 'Authenticate cfg and verify two qualified B1 authorization
  proofs.'` — without those proofs, an extracted seat is a candidate, not an attribution.

So R6 is *specified* and *algebraically tested*, and it is not *achieved*: no certificate produced
by this repository, or by any system this project could measure, both hides its signers and fits
32,768 bytes. The reason is quantified in §7.

---

## 7. Why hidden signers do not fit: Theorem C and the size arguments

### 7.1 The linear-size family bound (model-or-ledger estimate)

A Keccak-f[1600] permutation has 24 rounds of 1,600 bit-level AND gates (χ is the only nonlinear
step), i.e. 38,400 AND gates. Mode S needs 43·2 = 86 permutations for the key and handle
derivations a proof must cover. A VOLE-in-the-head proof transmits at least one correction bit per
AND output, and a ZKBoo/KKW-style commit-and-open reveals at least one party's AND outputs per
repetition. So those families need at least ⌈86 · 38,400 / 8⌉ = **412,800 bytes**, against a
27,056-byte slot (`:1038-1055`). The module labels this exactly: a lower bound for those proof
*families* on that circuit, not a universal proof-size lower bound.

### 7.2 The Binius64 PCS floor (estimate from re-implemented estimators)

Binius64 counts AND *constraints*, packing 64 bits per word: the vendored snapshots pin 600 AND
constraints per Keccak permutation (`keccak.snap` 4,779 = 8·600 − 21; `sha3_512.snap` 8,983 =
15·600 − 17). Mode S commits at least 86 · 600 = 51,600 words > 2^15, so the relevant pinned PCS
size is the log2 = 16 entry, min(FRI 135,680, WHIR 109,856) = **109,856 bytes** at 96-bit
soundness — above 27,056, and at a lower security level than QPT-128, with no QROM analysis
(`:1064-1102`; provenance in D3).

### 7.3 Theorem C (theorem with proof, under named assumptions)

**Statement as used here.** Let a proof for the hidden-signer relation use τ parallel repetitions
in the style of KKW, BN++, or FAEST v2, where (i) a prover without a witness is accepted in one
repetition with probability at least 2^−b (e.g. by guessing the unopened party among `N = 2^b`),
and (ii) each repetition carries at least one bit per bit of the extended witness — the 43
credentials of `c` bits plus `w` further bits per seat (nonlinear wire outputs or intermediate
states). Let the challenge be a hash chain of 2^h steps over a prover-chosen suffix, optionally
with a `w_g`-bit grinding condition; hypothesis (iii) adds per-repetition GGM seed openings. If
such a proof is QPT-128 (D1), then

- `τ·b + w_g ≥ s`, with `s = 212` at `h = 0` and `s = 180` at `h = 16`;
- `c ≥ 218` bits for the 64 credentials;
- under (iii) each opened seed has at least 212 bits;
- proof size ≥ `τ·43·(c + w)` bits, plus `τ·b·212` bits under (iii).

**Hypotheses, exactly.** (1) One Grover iteration costs **at most 2^24 gates** — this bound is used
in the direction the attack needs, an upper bound on attack cost; the Keccak-f[1600] T-count alone
is 499,200 < 2^19 and 2^5 is allowed for uncomputation and Clifford gates, giving up to 2^(104−h)
iterations below 2^128 gates. (2) Family membership of the named systems, asserted from their
published size formulas (`docs/sidecar-free-finalization.md` §3.1). Theorem C does **not** cover
ZKB++ (the third input share is sent in only 2 of 3 challenges) or Ligero-style sublinear proofs.

**Status.** Theorem with proof under those hypotheses: the proof is an attack argument in four
steps (Grover on the challenge suffix, Grover for a credential preimage, seed recovery, counting),
with the Grover landing lemma checked by exact arithmetic — `min_secure_bits(0) = 212`,
`min_secure_bits(6) = 218`, and the `y = 31/50` threshold `(y − y³/6)² ≥ 1/3` verified over the
rationals (`:1130-1164`, `test_grover_threshold_exact`). It is a *necessary* condition for those
proof families, not a universal lower bound, and its budget direction was wrong before correction
Q2 (see §9).

**The budgets.** `theorem_c_budget(b)` returns `τ = ⌈(s − w_g)/b⌉` and the per-seat budget
`⌊(27,056·8 − fixed)/(τ·43)⌋` bits, which includes the credential (`:1182-1201`). At `b = 16`:
`τ = 14`, budget **359** bits per seat including the 218-bit credential, i.e. **141** bits beyond
it. The full table, as `--report` prints it and the closure document tabulates:

| log2 N = b | τ | base budget (bits, incl. credential) | 32 grinding bits | 2^16-step chain + 32 grinding | with GGM seed term | at 2^18 gates/hash |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 27 | 186 (none fit) | 218 | 264 | 146 (none fit) | 179 |
| 12 | 18 | 279 | 335 | 387 | 220 | 264 |
| **16** | **14** | **359** | 419 | 503 | 280 | 359 |
| 20 | 11 | 457 | 559 | 629 | 359 | 419 |
| 24 | 9 | 559 | 629 | 719 | 440 | 503 |
| 32 | 7 | 719 | 838 | 1,006 | 561 | 719 |
| 40 | 6 | 838 | 1,006 | 1,258 | 641 | 838 |
| 48 | 5 | 1,006 | 1,258 | 1,258 | 770 | 1,006 |

Column notes, all from the closure document §3.1 and the `--report` output: "none fit" means even
a 218-bit credential exceeds the budget there. The last column is the variant in which one hash
evaluation is assumed to cost at most 2^18 gates instead of 2^24; it is never larger than the base
column. The prover's own leaf expansions, which the closure document tabulates beside these, are
τ·2^b: 9.2 × 10⁵ at `b = 16`, up to 1.4 × 10¹⁵ at `b = 48`. Honest-verifier cost: 32 grinding bits
cost about 4.3 × 10⁹ hashes per certificate, and a 2^16-step chain costs 65,536 sequential hashes
per proof and per verification. This domain reproduces the closure document's own table for the
first five columns; the sixth is a `--report` key, not a column of that table.

**What the per-seat relation needs (assessment of published primitives, not a theorem).** A seat
needs a one-way collision-resistant key map (≥ 336-bit collision resistance), a domain PRF for the
link and the mask (≥ 768 pseudorandom bits), and a selector of about 64 products per seat.
Verified category-5 witness sizes per evaluation in the cited sources range from 320 bits (MQOM2,
not collision-resistant: `F(x) = F(x+δ)` is linear in `x` for fixed δ) to 3,104 bits (AES-256,
FAEST). The cheapest published instantiation that meets both requirements is Rain₃ with a shared
256-bit key: 256 + 5 × 512 = **2,816 bits per seat**, which is 2.2× the most generous budget above
(1,258) and 3.9× the base budget at `b = 32` (719). The module's own conclusion is an assessment of
the published primitives, **not an impossibility proof** (`docs/sidecar-free-finalization.md`
§3.2–3.3).

### 7.4 Succinct and ring-signature evidence (literature values as recorded)

Theorem C says nothing about proofs whose size is sublinear in the witness. For those only
published sizes exist, and none fits: Binius64 PCS ≥ 109,856 B (96-bit); LaBRADOR ≈ 58 KB at 2^20
R1CS and not zero-knowledge; a lattice ZK toolkit ≈ 110 KB; SmallWood ≥ 40.8 KB; and a
VOLE-in-the-head ring signature for **one** hidden signer among 2^6 takes 21.49 KB at λ = 256 —
79% of the 27,056-byte slot for one signer, where the certificate needs 43 distinct hidden signers
with linkable handles. Threshold ring signatures with category-5 sizes were not found. Several of
these citations are incomplete in the source; they are reproduced as the source gives them and are
not upgraded here.

---

## 8. Theory used, with its status

| # | Result (as used here) | What it justifies | Label | Citation as the source gives it |
|---|---|---|---|---|
| 1 | v1.34 division-free decoder | the B1 extraction path: identity table `delta·(seat+1) → seat`, strict merge on the link | ported proof (from D5) | project; v1.34 revision, copied to this repository as `domains/05-extraction-and-signature-reductions/src/ceqs29_extractor.py` |
| 2 | Theorem A of v1.43 (public signer set) | B0's accountability, non-frameability and safety; QPT-128 with +23.0-bit margin | theorem with proof under the named assumption A-sig (EUF-CMA of the chosen category-5 scheme) | `domains/06-qpt128-security-target/docs/qpt128-finalization.md` |
| 3 | Theorem B of v1.43 (hidden signer set) | the B1 ledger, i.e. what a working hidden-signer proof would rest on | theorem with proof under named assumptions; **no proof system fits 32 KiB** | same |
| 4 | Grover search and the landing lemma | Theorem C's challenge-searching attack | theorem with proof (elementary, exact arithmetic) | project; `:1130-1164` |
| 5 | Theorem C | the size gate for witness-committing proof families | theorem with proof under the 2^24-gates-per-iteration assumption and the family hypotheses | project; `:1105-1223` |
| 6 | KKW / BN++ / FAEST v2 size-formula structure | only the "one bit per extended-witness bit" property in hypothesis (ii) | partial label; formula membership asserted from the sources' size formulas | FAEST v2 §3.1; BN++/AIMer; **citations incomplete in source** |
| 7 | Keccak χ AND count | 24 × 1,600 = 38,400 bit-level AND gates per permutation | standard construction fact | standard |
| 8 | Binius64 size estimators (FRI, WHIR) | the 109,856-byte PCS floor | literature value as recorded, from a re-implementation of the vendored estimators | `domains/03-zk-carrier-experiments/` |
| 9 | FIPS 204 / 205 sizes, NIST additional-signature sizes | the size table's non-measured rows | standard (added) for FIPS 204/205; submitter figures otherwise | FIPS 204 Table 2; FIPS 205 Table 2 |
| 10 | Hybrid `min(Adv)` composition | the OV-V‖SNOVA hybrid's security claim | reduction sketch | project |

The programme's consolidated theory-and-package index assigns these results the identifiers D7-01 …
D7-11. The labels above are the ones this domain carries for them; a reader who needs a stricter
label than the source supports will not find one here.

---

## 9. What the tests and probes actually returned

- `--self-test` (39 tests): **39/39 OK**, recorded at 0.094 s. Reproduced in this repository at
  0.093 s (repository copy) and 0.158 s (source copy) — see `../VERIFICATION.md`.
- `--report`: identical in every number to the tables above; the size gate reports
  `757 fits / 758 does not`, and the lower bounds 412,800 B and 109,856 B both exceed the
  27,056-byte slot.
- `--real-demo` in the pinned environment: 8 runs, exit 0, every recorded number reproduced.
- `--real-demo` with an interpreter that has neither `pqcrypto` nor an installed liboqs-python:
  `{"real_demo": "unavailable", "reason": "neither pqcrypto nor an installed liboqs-python
  imports"}`, exit 1. This is the documented behaviour of the demo, not a defect.
- **Finding A.10 (this domain's review found it; recorded here and in `../VERIFICATION.md`).**
  Two B0 tests mutate at CEQS29 body offsets while their names claim CQ44 header checks:
  `test_wrong_message_rejected` writes bytes `144:208` (the v1.29–v1.38 message offset), and
  `test_width_mismatch_rejected` packs a u16 at offset 206 (the old payload-length field, where
  the low half of the payload length sits). Replaying both, and the correct offsets 136 and 202:
  the misaligned message mutation is rejected by `count must be 43`; the aligned one by
  `signature for seat 0 does not verify`; the misaligned width mutation by `payload_len does not
  match the trailing bytes`; the aligned one by `header width does not match the provider width`.
  Both tests pass, but neither exercises the check its name claims. Fixing or relabelling them is
  an open item; the reference is not silently altered here.
- **Finding F6 (documented gap, not fixed here).** The encode side does not enforce the 32 KiB
  cap: `encode_b0` with a provider of width 758 emits a **32,810-byte** frame without raising,
  and `verify_b0` then rejects it with `frame exceeds the 32768-byte portability bound`. The wire
  specification §11 item 10 makes the encode-side refusal normative (gaps 16 and 17 of the
  independent implementation); the v1.44 reference does not implement it. This is stated as an
  open item rather than patched, so the reference stays the revision the measurements were taken
  on.
- **Specification gaps found by the independent implementation (D11).** An implementation written
  from the wire specification alone agreed with the reference on 6,701 of 6,701 checks over 900
  vectors and reported 18 points where the text left a choice; both the encode-side cap and the
  header-offset/width-field items above are among them. The gaps, the vectors and the check
  results are held by the independent-audit-stack domain
  (`domains/11-independent-audit-stack/independent-b0/`) and are not duplicated here.

---

## 10. Packages and tools

| Name | Version | What it is / how it is used | Returned here | Limitations |
|---|---|---|---|---|
| CPython | 3.12.3 | `struct`, `hashlib.shake_256`, `unittest`, `random`, `hmac` | 39/39 tests; the whole B0/B1 logic | SHAKE is a concrete function, not an ideal oracle |
| liboqs | 0.16.0, commit `5a1a854b0dc9f2141bdc771c555ee60c37950183` | C library of post-quantum signatures; loaded by `ctypes.CDLL` from `$OQS_INSTALL_PATH/{lib,lib64}/liboqs.so` **before** `import oqs`, because liboqs-python otherwise clones and builds liboqs | OV-V-pkc, SNOVA_29_6_5, SNOVA_60_10_4, MAYO-5, ML-DSA-87 frames | claimed levels are submitter claims; `SystemExit` during import counts as unavailable |
| liboqs-python (`oqs`) | 0.16.0 | wrapper; `Signature(alg)` exposes `details['claimed_nist_level']` and `details['length_signature']`, which the code requires to match | the measured widths | import-time output suppressed by the module; auto build guarded |
| pqcrypto | 0.3.4 in the reproduction environment (the original run's version was not recorded) | Python bindings to PQClean; `generate_keypair`, `sign`, `verify`, `SIGNATURE_SIZE` | Falcon-padded-512 and ML-DSA-87 rows | `RealSignatures.sign` zero-pads a short signature, which the tested schemes never do |
| Binius64 estimators | vendored revision, upstream `binius-zk/binius64` at `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4` | FRI/WHIR proof-size estimation; the pinned numbers are re-implemented in the module | 109,856-byte floor | 96-bit soundness, no QROM analysis; the re-implementation itself is in D3, not here |

---

## 11. Validation status

| Claim | Status |
|---|---|
| B0 frame logic (encode, verify, extract, blame) | proven/checked by 39 tests, and independently by a spec-only implementation on 900 vectors (D11); not formally verified here |
| B0 sizes 11,396 B and 30,918 B, and the 757/758 gate | arithmetic asserted by tests, and measured with real libraries: **measurement** |
| B0 security (accountability, safety, non-frameability, QPT-128 margin) | Theorem A of v1.43, a theorem under the named assumption A-sig; the assumption is about non-FIPS candidates |
| Hybrid `Adv ≤ min(Adv_OV, Adv_SNOVA)` | reduction sketch |
| Theorem C | theorem with proof under the 2^24-gate assumption and the family hypotheses; a necessary condition for those families, not a universal lower bound |
| Linear-family bound 412,800 B, Binius64 floor 109,856 B | model-or-ledger estimates / literature values, as labelled |
| "No known primitive meets the per-seat budget" | assessment of published primitives, not an impossibility proof |
| B1 hidden signers | frame, relation and algebraic extractor executable and tested; **no qualified proof backend exists, and `verify_b1` never reports authorization** |

**What would still be needed for a hidden-signer certificate to be acceptable as a standard proof:**
a backend that is zero-knowledge with simulation charged in the v1.43 ledger, online-extractable in
a stated model with its extraction error and time entered into the D6 module so that D2 holds in
gate units, whose per-seat extended witness fits the Theorem C budget for its own `b`, `w_g` and
`h`, and whose frame round-trips through `parse_b1` with `verify_b1` reporting
`authorization_verified = True` from a backend declared `qualified`. That list is the v1.44 closure
document's §4.1 criterion, and none of its five items is met today.

---

## 12. Open items

1. **R6 with R1** is unmet: no proof system fits 27,056 bytes at QPT-128 as the project defines it.
2. **A-sig.** EUF-CMA at category-5 generic strength for OV-V and SNOVA is a named assumption;
   UOV's own QROM proof carries a (2q+1)² loss.
3. **Measurement provenance.** The raw JSON of the original `--real-demo` run was never archived.
   This build's re-run is archived at `../results/real-demo.json`; that is the only raw record.
   The separate Falcon-padded-1024 probe and the pqcrypto version of the original run remain
   unarchived and unknown.
4. **Reference vs normative spec.** Implement the encode-side cap (F6, §9); fix or relabel the two
   mislabelled tests and add a dedicated width-field test; add vectors for the specification's
   §11 items 3, 5 and 6 (non-canonical public key, `bytearray` inputs, typed errors).
5. **Theorem C's hypotheses** (the 2^24 gates per Grover iteration, and FAEST v2 / BN++ family
   membership asserted from size formulas) are assumptions with incomplete citations.
6. **Theorem C's pre-correction figures are not preserved anywhere.** The numbers in §7.3 — 359 at
   `b = 16` and 141 bits beyond the credential — are the corrected figures the v1.44 revision
   prints. The values that stood before correction Q2 exist in no file, so no earlier number may be
   quoted. A figure of "46 nonlinear wires per seat" that circulated in private working notes
   occurs in no source file and must not be used: the code's unit is bits of extended witness,
   which equals "nonlinear wire outputs" only if each wire contributes one bit.
7. **B1 `extract_b1`** deliberately does not recompute `cfg` from a registry or verify proofs; it
   returns algebraic candidates and says so in its own output.
8. **Registry practicality.** 64 OV-V-pkc keys are ≈ 28.6 MB of fixed data, and OV-V keys overflow
   TLS subject-key fields (recorded in the operator-ledger domain, item A11).
9. **Not constant time.** The reference implementation is not a constant-time implementation, and
   no side-channel testing was performed.
10. **Coverage.** The demo covers frames only: no network protocol, key management or liveness.

---

## 13. Where to go next

- `b0-wire-spec.md` — the normative, implementation-independent specification of the B0 frame.
- `sidecar-free-finalization.md` — the closure document: requirements, measured table, Theorem C,
  rejected designs, recommendation and falsification criterion.
- `../src/sidecar_free_certificate.py` — the executable reference (39 tests).
- `../results/` — this build's recorded outputs of its runs, with their provenance.
- `domains/11-independent-audit-stack/independent-b0/` — the spec-only implementation, the 900
  vectors, the 6,701/6,701 check result, the 18 specification gaps it reported, and the recorded
  results (owned by that domain).
- `domains/06-qpt128-security-target/` — Theorems A and B and the QPT-128 gate ledger that B0's
  security statement rests on.
- `domains/08-hidden-signers/` — the continuation of the hidden-signer question past 32 KiB.
