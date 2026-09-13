# Experiment 7 — v1.29: what an approval layer above the tracing relation would look like

## The problem

Every relation before this one was a **credential-preimage relation**: its witness is a set of 43
private seeds, and proving it establishes that someone knew 43 registered credentials — not that 43
members *approved a message*. The v1.29 report states the distinction the experiment has to close:
"Ordinary soundness alone does not establish knowledge or consent: valid witnesses may exist for a
statement even when an adversary does not know them."

So the question was: with real post-quantum primitives, what exactly must an authorization layer
check, what does it have to transport, and what does it still not prove? The experiment answers by
building an executable specification — and, critically, by keeping the parts that a real
zero-knowledge proof would have to certify separate from the parts that are merely *checked in the
open* by a reference implementation.

## The relation carried: `CEQS29-M87-K1024`

A new experimental suite, explicitly **not wire-compatible with `CEQS12B`**. Let `H` be SHAKE256 with
64-byte output over unsigned 64-bit big-endian length-prefixed arguments.

**Registry.** 64 ordered rows `R[i] = (K_T[i], pk_i, ek_i)` with `K_T[i] = H("CEQS29/trace-key", t_i)`.
`C` hashes the suite and all registry fields in that fixed order. The reference rejects repeated keys
within each registry column; enrollment, proof of possession and malicious-registration handling are
**prerequisites**, and duplicate-length checks do not implement an enrollment protocol.

**Handles.** For a 64-byte context `d` and 64-byte direct message challenge `m`,

```
L_i ‖ R_i = SHAKE256_128("CEQS29/pair" ‖ t_i ‖ H("CEQS29/domain", C, d)),     Z_i = R_i + m·(i+1)
```

with arithmetic in the same binary field `x^512 + x^8 + x^5 + x^2 + 1`, canonical big-endian
encodings, and an injective direct message field on 64-byte messages. Context `d` is meant to identify
the protocol instance (epoch, height, view).

**Approval.** Form a canonical public body `B` from the suite, `C, d, m` and exactly 43 handles sorted
strictly by `L`. Member `i` signs

```
A_i = "CEQS29/VOTE/v1" ‖ H("CEQS29/body", B) ‖ u8(i) ‖ L_i ‖ Z_i,      σ_i = MLDSA87.Sign(sk_i, A_i).
```

This uses the pure ML-DSA external API with empty external context and the application domain
explicitly inside the signed message — it is **not** HashML-DSA. Members approve *after* the candidate
handle list is assembled, so changing the list requires new approvals; this extra phase avoids a
circular dependency between signatures and the final proof.

**The predicate `R29(B, w)`** for a witness `w = ((i_j, t_j, σ_j))` of 43 rows requires all of:
authentic configuration binding and canonical body framing; exactly 43 distinct indices in `0..63`;
the trace credential opening `K_T[i_j]` at that index; the public handle at that row equalling the
handle computed with that credential and index; and the same registry index selecting the ML-DSA
public key whose signature verifies on `A_i`.

## The backend, and which part of its theory applies

| Component | Job as the report defines it | Theory as used |
|---|---|---|
| ML-KEM-1024 `Encaps`/`Decaps` | establish a secret with a designated receiving participant | FIPS 203, sections 3 and 6–8, used as a component and a constraint — the source states explicitly "not as theorems about CE-QS" (`D3-01`) |
| HKDF-SHA-512 and AES-256-GCM | derive transport key, protect an approval | standards used as composition, no forward-secrecy or erasure claim (`D3-19`) |
| ML-DSA-87 `Sign`/`Verify` | authenticate an explicit approval by seat `i` | FIPS 204, sections 4–6; algorithms and sizes checked, **not** a full errata/conformance audit (`D3-02`) |
| `t_i`, `K_T[i]` | bind a member's stable tracing credential | — |
| `(L_i, Z_i)`, hidden `i` | carry the public extraction data and tie authorization, registration and tracing to one seat | the extraction identity and counting bound of `D3-08`, `D3-13` |
| `π_R29` | prove all of the above without revealing the authorizers | **does not exist here** |

The backend for the tracing part is still the patched Binius64 prover; the v1.29 component itself is
**not** a proof. The report is explicit that "there are still no ML-DSA verification constraints
inside a generated succinct proof in this update. A valid proof must encode the complete standardized
verifier, including canonical signature parsing, response bounds, hints, and challenge recomputation.
A linear equation about lattice vectors is insufficient."

Surveyed but not implemented, each with the limit the report attaches: Aurora (`D3-04`, encode the
predicate as one statement — but its examples do not instantiate this proof position); AIM, HAETAE,
Han et al., Quorus, Doerner–Kondi–Rosenbloom (`D3-05` — abstracts and affiliations only, and for two
of them PDF retrieval was unavailable so no uninspected theorem is credited). The report also records
the honest-majority arithmetic `64 > 3·21` as a *possible operating regime* and states that a 43-party
substitution would not carry the same `n > 3t` guarantee (`D3-20`).

## How the adapter bridged them

`src/authorization.py` is the executable reference: `check_witness` executes the five-clause predicate
using ordinary cryptographic verification, with the private inputs present. `src/test_authorization.py`
is the 51-check suite; `src/verify_audit.py` is the **transparent** audit that replays the approvals
from public keys, bodies and signatures alone — it discloses seats by construction and says so.

The transport, which was actually executed for all 86 approvals: for each transmitted approval the
sender encapsulates a fresh secret to the recipient's ML-KEM-1024 key; HKDF-SHA-512 derives an
AES-256-GCM key with the header and KEM ciphertext bound into the derivation; associated data bind the
suite-specific transport format, sender, recipient, session, complete body digest, recipient-key
fingerprint and KEM ciphertext; a fresh nonce is used with each independently established key; and an
outer ML-DSA-87 signature authenticates the whole envelope. The receiver checks the outer signature,
decrypts, and separately verifies the **inner** approval against the claimed sender and exactly one
handle in the body; a duplicate-origin cache is updated only after all checks pass. This follows the
KEM-plus-authentication separation of SP 800-227 and is stated to be a custom experimental
composition, not a named standard channel protocol.

Two properties the report will not overstate: the plaintext is an approval signature, and **no trace
seed or signing secret is passed to the recipient** — but the recipient does learn the sender and the
corresponding handle, so the channel is **not anonymous to the recipient**, and the public audit
deliberately publishes the synthetic approving seats. A private distributed prover still needs a
protocol that hides the witness *and* the activity pattern; sending a full credential encrypted to a
coordinator would protect it only from outsiders.

## Tests

| Test | What it asserts | Recorded result |
|---|---|---|
| The 51-check component suite (`src/test_authorization.py`) | exact approval binding, missing and repeated authorizers, cross-context reuse, registered trace openings, transport authentication, decryption integrity, replay state, and the algebraic intersection | **51/51 passed**; `results/authorization-evidence.json`, `checks_total: 51` |
| Approval counts | — | 86 actual ML-DSA-87 approval signatures; 86 encrypted approvals received; 43 per case |
| Conflict algebra over *real* signers | the extracted set is the actual approving set, not a witness set | `actual_conflict_intersection: [0..21]` |
| Transparent public audit (`src/verify_audit.py`) | the approvals verify from public data alone | 86 approvals, intersection `0..21`, `complete_QCs_verified: 0`; `results/public-approval-audit.json` |
| ML-KEM implicit rejection | a changed ciphertext after a valid outer signature must still be rejected | AEAD check rejects; an authenticated, successfully decrypted envelope carrying an invalid inner approval is also rejected |
| **The decisive negative control** | an incorrect trace mask, with the synthetic authorizers *genuinely signing* that incorrect body | **signature-only auditing accepts; the full witness predicate rejects** — "this does not attack ML-DSA. It demonstrates why replacing the predicate proof with ordinary or threshold signatures does not establish truthful tracing" |

Timing, as recorded: main cryptographic case work ≈ **1.45 s**, entire component run ≈ **1.64 s** on
the recording host (Python 3.12.14, `pqcrypto` 0.3.4, `cryptography` 46.0.0). The report labels this a
local simulation, not a distributed performance measurement.

## Sizes and the contents contract

| Required public content | Representation in this candidate | Status |
|---|---|---|
| suite, registry reference, context and message | fixed 208-byte body header | implemented |
| publicly computable conflict evidence | 43 complete 128-byte handles | implemented at equation level |
| truth of the 43-seat authorization and trace relation | one private-witness proof `π_R29` | **not implemented** |

Body 5,712 bytes; proof position **27,056 bytes**; transport envelope **11,020 bytes** — and the record
states plainly that `transport_envelopes_are_not_final_QC_bytes: true`. The report explains why the
envelope must not be confused with the certificate: ML-KEM ciphertexts are production messages and need
not be final-QC data **only if** verification of the eventual complete QC is independent of them — and
"the current prototype has no such QC verifier, so it cannot yet claim the no-sidecar property."

It also closes three tempting shortcuts by name: a KEM shared secret can expand to a large private
random tape, but a public verifier cannot decapsulate from `ek` and the ciphertext alone, and
publishing the shared secret makes the tape public; the short seed of an ML-DSA private key cannot be
published, because it regenerates the signing authority; and a public decoder for members' private
keys is not a proof of hidden signatures.

## Gates, at the end of this experiment

| Gate | Result |
|---|---|
| Actual ML-DSA approval predicate in executable reference | implemented and tested |
| Authenticated ML-KEM transport of approvals | implemented and tested as a local component |
| Same-seat authorization/trace binding in executable reference | implemented and tested |
| Same checks certified inside a succinct ZK proof | **open** |
| Complete QC at most 32 KiB | **open** |
| Whole-system QPT-128 qualification | **open** |
| Private distributed production robust to 21 faults | **open** |
| Accepted complete original-goal QCs | **0** |

`results/authorization-evidence.json` carries the same list as `blockers`, and adds that
`private_witnesses_centralized_in_test_harness: true` and
`transport_recipient_learns_signers: true`.

## Accountability: the conditional argument, and what it needs

The report's reduction is conditional on four things it names: an authenticated fixed registry;
consistent trace openings across the two proofs; distinct context links for different registered
seats; an appropriate **joint QPT argument-of-knowledge extractor** for two accepted proofs of `R29`;
and multi-user unforgeability of the approval signatures in the required quantum model. Given those,
extraction gives two sets of 43 distinct registry seats, so at least 22 are common; for a common seat
the mask and link repeat while the message changes, so `(Z_i^(0) + Z_i^(1))/(m_0 + m_1) = i+1`, with a
nonzero denominator. Because correct relation proofs ensure the recovered identity is the same index
whose approval signature verified, extracting an approval for a message an uncorrupted member never
signed yields a signature forgery unless one of the assumptions failed. The report writes the failure
bound schematically with each term defined for the whole experiment and states that **no numerical
bound is claimed**.

## Conclusion

v1.29 resolved the *executable specification* of approval binding and validated the transport
primitives with real implementations and real signatures. It did not resolve the proof-engineering
task, and the report says the next decisive implementation step is "a circuit or native proof relation
for the full ML-DSA verifier plus same-seat tracing, followed by an actual private proof with all bytes
included." Its most useful output for a reader may be the negative control: it is the clearest
demonstration in this domain of why a signature-based audit is not a substitute for the relation
proof, since with a corrupted trace mask the signatures are perfectly valid.
