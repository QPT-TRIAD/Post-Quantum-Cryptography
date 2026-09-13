# Profiles B0 and B1 side by side

Two profiles share one frame format and one suite identifier field. They admit different objects,
measure different things, and prove different things. This document states for each what it admits,
what was measured, what is proved, and the exact rule that accepts or rejects a signature scheme —
so that a reader can test a new scheme themselves and get the same verdict the reference gives.

---

## 1. At a glance

| | **B0** | **B1** |
|---|---|---|
| suite id | `0x44B0` | `0x44B1` |
| name in the sources | profile B0, public signer set | B1, "Mode S", hidden signer set |
| payload | 8-byte bitmap ‖ 43 fixed-width signatures | 43 handles (128 B each) ‖ one proof |
| `width` field | the scheme's signature width `W` | `128` (the handle width) |
| frame length | `216 + 43·W` | `5,712 + proof_len`, `proof_len ≤ 27,056` |
| who is named | **the 43 signers are public**: the bitmap names them | nobody: the handles are pseudonymous |
| conflict witness | the bitmap intersection plus two public signatures per seat | an algebraic decoder over the two handle lists |
| backend needed | a signature scheme of width `W ≤ 757` | a zero-knowledge proof backend — **none exists here** |
| status | executable reference; measured with real libraries | frame, relation and extractor executable; **no certificate is produced** |
| security statement | Theorem A (public signer set), conditional on EUF-CMA of the scheme | Theorem B (hidden signer set) for a ledger; no proof backend exists |

---

## 2. What B0 admits

B0 is **generic over a signature scheme with a fixed signature width**. It requires a provider with
this interface (the reference's provider contract, `:470-475`):

| member | type | meaning |
|---|---|---|
| `keygen()` | `→ (pk, sk)` | one keypair for one seat |
| `sign(sk, msg)` | `→ bytes` | a signature of exactly `width` bytes |
| `verify(pk, msg, sig)` | `→ bool` | true iff the signature is valid |
| `width` | int, bytes | the fixed signature length `W` |
| `category` | int | the claimed NIST category |

The scheme is used through its **pure signing API with an empty external context** — no pre-hashing
performed by the caller, no context string supplied by the certificate.

### 2.1 The acceptance rule

A signature scheme is admissible for B0 if and only if all five conditions hold. The first three are
checked mechanically by the reference before any frame is built; the last two are checked by running
the full demo procedure of §2.2.

1. **Fixed width.** The provider exposes one `width` `W` and produces signatures of exactly that
   length. A shorter signature is **refused, not padded** (`encode_b0`: *"signature must be exactly
   the provider width"*; `OqsSignatures.sign`: *"variable-length signature does not fill the fixed
   slot"*). A scheme whose signatures vary in length cannot be used, and no padding rule is defined
   for it.
2. **Size.** `216 + 43·W ≤ 32,768`, equivalently `W ≤ (32,768 − 216) // 43 = 757`. The reference's
   `b0_fits(757)` is `true` and `b0_fits(758)` is `false`.
3. **Claimed category.** The library's claimed NIST level must equal the declared category, or the
   provider refuses to construct: `OqsSignatures.__init__` raises *"liboqs claimed level differs
   from the declared category"* when `details['claimed_nist_level'] != category`. For B0 acceptance
   the declared category is **5**. A scheme that fits but claims a lower category is admissible as a
   *frame* and inadmissible as a *QPT-128 instantiation*.
4. **Availability.** For a library-backed provider, the scheme must be enabled in the local library
   build (`alg in oqs.get_enabled_sig_mechanisms()`); otherwise the provider is skipped, not failed.
5. **Behaviour.** Running the fixed procedure of §2.2 must produce: both frames verifying, exactly 22
   seats extracted, every extracted seat blaming true, and the tampered frame rejected.

### 2.2 The fixed procedure every measured row went through

Stated exactly, because a reader re-testing a scheme must run the same thing to get a comparable
row.

1. Generate the registry: 64 consecutive `keygen()` calls; `pk_i`, `sk_i` aligned index-for-index.
2. `cfg = cfg_b0(registry)` with `scheme_id = b"CQ44/real-demo/"`, `domain = bytes(range(64))`,
   `message0 = 64 zero bytes`, `message1 = 63 zero bytes ‖ b"\x11"`.
3. `seats0 = 0 … 42`; `seats1 = 0 … 21 ∪ 43 … 63`. The two sets overlap in exactly 22 seats, the
   minimum a conflict can have.
4. `frame0 = encode_b0(…, message0, seats0)`, `frame1 = encode_b0(…, message1, seats1)`.
5. Record `name`, `category`, `signature_bytes = W`, `public_key_bytes = len(pk_0)`,
   `frame_bytes = len(frame0)`, and `b0_frame_bytes_formula = 216 + 43·W`. The demo asserts the
   frame length equals the formula.
6. If `b0_fits(W)`: verify both frames; extract (must return 22 seats); check `verify_blame_b0` for
   every extracted seat; then flip one bit at offset `216 + W//2` — inside the first signature — and
   require the verifier to reject. For the hybrid, flip one bit inside each half.
7. If not `b0_fits(W)`: `verify_b0(frame0)` must raise
   `frame exceeds the 32768-byte portability bound`, recorded as `oversize_rejected: true`.

### 2.3 The measured outcomes, with the exact rejection reasons

All rows below are **measurements** from the recorded `--real-demo` run
(`domains/07-compact-certificate-b0/results/real-demo.json`), reproduced in this repository against
liboqs 0.16.0 (commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`), liboqs-python 0.16.0 and
pqcrypto 0.3.4. The category column is the library's `claimed_nist_level`, a submitter claim.

| Scheme | Library | Claimed cat. | `W` | Public key | Frame | Verdict, and the exact reason |
|---|---|---:|---:|---:|---:|---|
| **OV-V-pkc** | liboqs | 5 | 260 | 446,992 | **11,396** | accepted; 22 extracted; blame ok; tamper rejected |
| SNOVA_29_6_5 | liboqs | 5 | 454 | 2,716 | 19,738 | accepted; 22 extracted; blame ok; tamper rejected |
| SNOVA_60_10_4 | liboqs | 5 | 576 | 8,016 | 24,984 | accepted; 22 extracted; blame ok; tamper rejected |
| **OV-V-pkc‖SNOVA_29_6_5** | liboqs | 5 | 714 | 449,712 | **30,918** | accepted; 22 extracted; blame ok; **both halves** tamper-rejected |
| MAYO-5 | liboqs | 5 | 964 | 5,554 | 41,668 | **rejected as oversize**: `frame exceeds the 32768-byte portability bound` |
| ML-DSA-87 | liboqs | 5 | 4,627 | 2,592 | 199,177 | **rejected as oversize**: same reason |
| ML-DSA-87 | pqcrypto | 5 | 4,627 | 2,592 | 199,177 | **rejected as oversize**: same reason |
| Falcon-padded-512 | pqcrypto | **1** | 666 | 897 | 28,854 | frame verified and extracted, **but category 1 — does not meet QPT-128** |

The demo makes eight runs over seven distinct schemes; ML-DSA-87 runs under both libraries. Its own
closing field names the four that satisfy every condition:

```
"category5_fitting_verified": ["OV-V-pkc", "OV-V-pkc||SNOVA_29_6_5",
                               "SNOVA_29_6_5", "SNOVA_60_10_4"]
```

**Why the rejections are load-bearing evidence.** They are not a formality. They are the measured
demonstration that the size budget excludes the standardized post-quantum signature family
altogether: ML-DSA-87 exceeds the budget by a factor of `199,177 / 32,768 = 6.1`, and at `W = 4,627`
a single signature is 6.1 times the entire per-seat slot of 757 bytes. The admissible set is
therefore confined to NIST's additional-signature candidates, and that confinement is a measured
fact about the frame, not a preference. Equally, Falcon-padded-512 shows that "fits" and "meets the
target" are different verdicts: it fits with 3,914 bytes to spare and is still inadmissible, because
its claimed category is 1.

### 2.4 Rows in the size table that are *not* runs

The reference's size table also carries four entries that no recorded run covers. They are quoted,
not measured, and must be read as such:

| Entry | `W` | Frame `216 + 43·W` | Provenance |
|---|---:|---:|---|
| SLH-DSA-SHAKE-256s | 29,792 | 1,281,272 | FIPS 205 Table 2. The table's `source` string also says "measured liboqs 0.16.0", but the recorded demo does not run this scheme — see `sizes.md` §4 |
| Falcon-padded-1024 | 1,280 | 55,256 | Falcon round-3 padded signature size; executed only in a separate library probe that was not archived |
| SQIsign-V | 292 | 12,772 | SQIsign round-2 specification; **not executed** |
| HAWK-1024 | 1,221 | 52,719 | HAWK round-2 specification; **not executed** |

SQIsign-V would fit if its specification size were realised in an implementation. It is still not
admissible today, because no local run has confirmed its width, its category claim, or its
behaviour under the procedure of §2.2.

---

## 3. What B1 admits

B1 admits no signature scheme. It admits **one relation** and one backend interface.

### 3.1 The relation

- **Credentials.** Seat `i` holds a 64-byte secret `x_i`. Its registered key is
  `K[i] = SHAKE256(b"CEQS/K1" ‖ x_i)[:128]` — a 71-byte absorb input, one SHAKE256 block, 128 bytes
  of output. `cfg = H(b"CQ44/cfg/B1", K_0, …, K_63)` with duplicate keys rejected.
- **Context.** `D = H(b"CQ44/ctx", cfg, d)`.
- **Handle.** `pair = SHAKE256(b"CEQS/P1" ‖ x ‖ D)[:128]` (135-byte input, one block);
  `L = pair[:64]` is the link; `Z = int(pair[64:]) XOR mul(int(m), i+1)` in
  `GF(2)[X]/(X^512 + X^8 + X^5 + X^2 + 1)`.
- **Payload.** 43 handles strictly increasing by `L`, then the proof bytes.
- **Relation `check_relation`.** The 43 seats are distinct, each credential opens its registered key,
  and each handle recomputes. The reference checks this by *seeing the private rows*. That is the
  relation a qualified backend would have to prove in zero knowledge; it is not a proof.

### 3.2 The backend interface, and why it admits nothing

`verify_b1` returns exactly this verdict shape, and there is no way to make it report an
authorization without a backend that declares itself qualified:

```
'status': 'QUALIFIED_PROOF_VERIFIED'            if backend.qualified and structurally accepted
          'STRUCTURE_ONLY_NO_QUALIFIED_PROOF'   otherwise
'authorization_verified': backend.qualified and structurally accepted
```

The only backend in the module is `StructureOnlyTestBackend`, with `qualified = False` and a proof
that is a fixed 40-byte marker
(`STRUCTURE-ONLY/NOT-A-PROOF/CQ44-B1/v1.44`) which `verify` compares by equality. So
`authorization_verified` is `False` **by construction**, not by failure of some run. This is stated
in the module's own return dictionary and in the wire specification, and it is the single most
important fact about B1.

### 3.3 What B1's extractor returns

`extract_b1` is the v1.34 division-free decoder ported over parsed handles: it merges the two handle
lists on `L`, recovers `seat = table[Z₀ XOR Z₁]` for each matched link through a `delta·(seat+1) →
seat` identity table built with six `xtimes` and 64 XORs, rejects a zero or out-of-range identity and
a duplicate identity, and requires at least 22 findings. Its output carries:

```
'status': 'ALGEBRAIC_CANDIDATES_ONLY'
'authorization_verified': False
'requires_before_attribution': 'Authenticate cfg and verify two qualified B1 authorization proofs.'
```

Without those two proofs, an extracted seat is a **candidate**, not an attribution. The reference
supplies neither.

### 3.4 What B1 does *not* prove

- B1's Theorem B (the hidden-signer ledger, `+29.4 bits`) is a statement about the **ledger a working
  backend would rest on**. It is not a statement about an implemented certificate, because no
  backend exists.
- The single-witness figure for a ring signature hiding **one** signer among 64 — 21.49 KB at
  `λ = 256`, from a published table — is a **lower bound** on what a hidden-signer proof costs. It is
  not an estimate of B1's certificate, and B1's matrix needs 43 distinct hidden signers with
  linkable handles.
- **Theorem C is not a proof of a working scheme.** It bounds the size of witness-committing proofs
  (KKW-, BN++- and FAEST-style) for the hidden-signer relation, under the assumption that one Grover
  iteration costs at most `2^24` gates. It is a **necessary condition for those families** — not a
  universal lower bound — and it says nothing about a certificate that does not exist.

---

## 4. What each profile proves, by claim

| Claim | B0 | B1 |
|---|---|---|
| frame logic (encode, verify, extract, blame) | 39 unit tests in the reference; independently, 6,701/6,701 checks over 900 vectors by a spec-only implementation | frame, relation, extractor covered by tests; no backend |
| ≥ 22 seats extracted from a conflict | set arithmetic, unconditional; tested for every overlap 22 … 43 | algebraic candidates only; requires two qualified proofs to become attribution |
| sizes | measured with real libraries, and asserted by tests | `5,712 + proof_len` arithmetic; `proof_len ≤ 27,056` |
| security | Theorem A: accountability deterministic; non-frameability and safety reduce tightly to EUF-CMA of the scheme (assumption `A-sig`); D2 holds with a **+23.0-bit** margin | Theorem B for the ledger; **no proof system meeting the slot exists** |
| hidden signers | **not met** — the bitmap is public | aimed at it; **not achieved** |

**The asymmetry worth stating plainly.** B0's reduction is tight because the evidence is public
bytes: a signature anyone can verify. B1's reduction must run an online extractor to recover an
opening from a proof, and pays for it. That is why hidden signers are not just a privacy feature B0
lacks — they change the cost structure of the security statement.

---

## 5. Requirements, profile by profile

The programme's seven requirements (stated in full in `parameters.md` §4).

| Id | Requirement | B0 | B1 |
|---|---|---|---|
| R1 | whole certificate ≤ 32,768 bytes | **met**, 11,396 – 30,918 measured | `5,712 + proof_len`; **no proof fits** |
| R2 | verifier holding the fixed authenticated registry checks it alone | **met** | would be met |
| R3 | two conflicting accepted certificates publicly yield ≥ 22 double-authorizers | **met**, measured (22 seats, blame verified) | algebraically tested; attribution needs proofs |
| R4 | no proof file, omitted opening, external leaf list or transcript | **met** | intended |
| R5 | no opener's secret at extraction | **met** | intended |
| R6 | seat indices and credentials stay private | **not met** — the bitmap names the signers | intended; **no backend** |
| R7 | QPT-128 as a gate work factor | **met** by Theorem A, +23.0 bits, under `A-sig` | Theorem B for the ledger |

The programme's main goal is conflict-extractable, compact post-quantum quorum signatures without a
sidecar — R1–R5 plus R7. **B0 meets it. R6 together with R1 is open.**

---

## 6. Designs that were examined and rejected

Recorded so that a reader does not re-derive them. Each trades away a requirement the profile needs.

| Design | Why it was rejected |
|---|---|
| Per-domain shuffled rosters of one-time keys | verification needs per-domain data outside the certificate → fails R4; public identity recovery after a double signature needs a Lamport-size tripwire → fails R1 |
| Fixed pseudonym rosters | pseudonyms link across certificates → fails R6 under adaptive scheduling; mapping a pseudonym to a seat needs an opener → fails R5 |
| Encrypted bitmap | a public verifier must know which key checks each signature → fails R2 or R6 |
| Key blinding (e.g. isomorphism-of-polynomials blinding of OV keys) | membership of a blinded key needs a zero-knowledge proof over the 64 registry keys, which leads back to the size arguments that already fail |

**What would close R1 together with R6.** A backend is admissible for that purpose if and only if
all five of the following hold for its relation — this is the falsification criterion the closure
document states:

1. **Size:** the proof, plus handles and header, is at most 32,768 bytes.
2. **Zero knowledge:** it is zero-knowledge, with simulation charged in the QPT-128 ledger.
3. **Extraction:** it is online-extractable in the QROM or a stated model, and its extraction error
   and extractor time are entered into the QPT-128 module so the target holds in gate units.
4. **Witness budget:** if it is witness-committing, its per-seat extended witness is at most the
   Theorem C budget for its own `log₂N = b`, grinding `w_g` and chain depth `h`.
5. **Execution:** it runs, and its frame round-trips through the B1 parser with `verify_b1`
   reporting `authorization_verified = True` from a backend declared `qualified`.

None of the five items is met today.
