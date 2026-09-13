# CE-QS at its current revision — the construction end to end

This document explains the CE-QS construction as it stands at the current revision of the
sequence, **v1.24** (`docs/32kib-contents-contract.md`, 9 September 2026), and states for each step
which assumption it needs and which part of which theory justifies it. Every symbol is defined
where it first appears. Every number carries a pointer to the file it comes from.

**Status of this document.** It is an explanation of the sources, not a new result. Where the
sources label a claim *proved*, *conditional*, *measured*, *design allocation* or *open*, that
label is repeated here. Two separate objects must be kept apart while reading:

- the **certificate contract** (what bytes the certificate contains and which relation the proof
  must establish), which is current at v1.24; and
- the **security theorem** (why the construction is sound, extractable and anonymous), which is
  current at v1.3 (`docs/qpt-crs-security-proof.md`) for the non-interactive mode and v1.4
  (`docs/collaborative-quorum-proof.md`) for the collaborative mode. No revision after v1.4
  re-proves the theorem for the executed parameterization.

---

## 1. The problem

A Byzantine-fault-tolerant committee of `n` validators must produce a single compact object — the
quorum certificate — that proves "a quorum of the committee approved this message". Let

- `n` = committee size = **64**;
- `f` = maximum number of faulty validators the protocol tolerates = **21**;
- `q` = quorum size = **43**.

The relations `n = 3f + 1` and `q = 2f + 1` hold for these numbers.

Three requirements are imposed at once, and they pull against each other.

**(a) Accountability without a sidecar.** If two valid certificates exist for two different messages
`M ≠ M'` in the same conflict domain `τ` (a "topic" or "domain" — a public label under which a
validator must not approve two different messages), then the two certificates alone must let anyone
identify *every* validator that approved both. In particular, a validator that builds their
certificate correctly at one revision of the rules (v1.24 §47 states that the configuration `cfg`
identifies the message, domain, registry and relation).

Forms of sidecar in the source's sense (v1.24 §22): no additional proof file, no omitted opening, no
external leaf list, no opener secret, no accusation proof per recovered validator, and no need to
re-obtain the proving transcript at verification time ("A scheme that needs those messages again to
verify has failed this contract").

**(b) Optional signer-set privacy.** The certificate may be asked to hide *which* 43 validators
approved. The sequence discovered that this is a separable requirement, not part of accountability
itself (see §3.2 below), and named the two targets:

- **Target B0** — compact exact post-quantum multisignature plus a **public** signer bitmap;
- **Target B1** — compact exact post-quantum quorum with **hidden** signers and conflict-only
  extraction.

**(c) Compactness — at most 32,768 bytes.** This number is a **project engineering decision**, not a
cryptographic limit. v0.3 recorded the gates as green ≤ 16 KiB, acceptable 16–32 KiB, fail > 32 KiB,
explicitly calling the choice a project engineering decision (`docs/finalized-construction.md`).
The pressure is real: the direct evidence payload for 43 ML-DSA-65 signatures was measured at
the 100 KiB class, and the retained-format floor derived at v1.18 is `|QC| ≥ 50,496 > 32,768` bytes
(`docs/research-qualification.md:167`).

### 1.1 Why it is hard

Three independent obstacles, in the order the sequence hit them.

1. **Quorum semantics are not threshold semantics.** A `q`-of-`n` quorum for `q = 43, n = 64`
   is 67 % of the committee with the fault set ranging over *all* 21-subsets. A succinct aggregate
   with a positive collection slack `Δ` forces the collector to obtain `q + Δ > 43` approvals,
   and only `n − f = 43` honest validators exist — so any positive slack loses Byzantine-independent
   liveness. This is v0.4's argument (`docs/research-synthesis-final.md:559–573`), which v0.5 then
   *corrected*: with the right parameterization the exactness is theoretically attainable, at a
   catastrophic 38.6 MiB cost (`docs/inflections/01-elba-impossibility-retracted.md`).
2. **Compactness is an arithmetic obstruction, not an engineering shortfall.** v1.18 derived a
   format-level floor of `4,288 + 16 + 46,192 = 50,496` bytes for the retained frame
   (`docs/research-qualification.md:167`); v1.21 measured `0.0737` encoded bytes per native gate
   against a 28,480-byte proof slot (`docs/size-path-resolution.md:12,17,21`).
3. **Quantum soundness.** Challenge-collision resistance, the extraction of a knowledge error, and
   the anonymity hybrid all have to hold against a *quantum* adversary, and the classical lattice
   threshold-signature stack does not supply that. v1.3 removes the random oracle from the
   load-bearing theorem; v1.4 corrects an anonymity hybrid that v1.3 had stated too weakly.

The immediate predecessor of CE-QS is the D1 lineage — the idea of modifying the masking randomness
*inside* a lattice threshold signature so that a conflicting pair exposes the signer. v0.1 abandoned
that shape because the threshold signature's own proof would have to be modified, and instead
separated the hidden-threshold proof from the trace tags (`docs/frontier.md`).

---

## 2. The certificate, as currently specified

v1.24 fixes the contents before choosing any proof system:

```
QC = ( context , { (L_j, Z_j) }_{j=1..43} , pi_joint )
```

- **context** — an identifier binding the certificate to the committee registry, the conflict
  domain `τ`, the message `M`, the relation and the canonical encoding. Its byte layout is header
  fields `magic[4], version[2], suite[2], cfg[64], d[64], m[64], count[2], width[2], proof_length[4]`
  (`docs/32kib-contents-contract.md:21`).
- **`{(L_j, Z_j)}`** — 43 **handles**: `L_j` is the repeatable **link tag** of the `j`-th selected
  seat and `Z_j` its **masked identity**, computed in §2.2 below. Sorting them canonically is what
  makes the list message-independent.
- **`pi_joint`** — one zero-knowledge argument of knowledge over the same `X` that establishes the
  relation of §2.3.

The allocation, fixed by purpose before any proof system was chosen
(`docs/32kib-contents-contract.md:15–21`):

| Object | Allocation | Why it must be present |
|---|---:|---|
| context and framing | 208 bytes | binds the certificate to registry, domain, message, relation, canonical encoding |
| 43 handle pairs `(L_j, Z_j)` | 5,504 bytes | lets a future public extractor match repeated seats and recover identities |
| joint proof `pi_joint` | 27,056 bytes | proves distinct membership, credential knowledge, correct handles and context binding, hiding the witness |
| **total** | **32,768 bytes** | the project gate of §1(c) |

The 5,504 bytes are arithmetic from the stated output widths, not a measurement: each of `L_j` and
`Z_j` is a 64-byte string (SHAKE256 with 64-byte outputs, `docs/32kib-contents-contract.md:48`), so
`43 × (64 + 64) = 5,504`. The allocation is a **design allocation**; the source states explicitly
that these are not measurements of a finished certificate and that no qualifying compact proof has
been produced (`docs/32kib-contents-contract.md:3,21`).

The inventory assumes the verifier already holds the **fixed authenticated 64-seat registry** and
the approved verification parameters. The registry is not certificate-specific: its identifier
authenticates a *known* registry, it cannot reconstruct an unknown one
(`docs/32kib-contents-contract.md:23`).

### 2.1 Registration

Each validator seat `i ∈ {0, …, 63}` holds three independent secret credentials
`a_i, b_i, v_i` and publishes three registration keys (`docs/32kib-contents-contract.md:40–46`):

```
K_L[i] = H("link-key", a_i)
K_R[i] = H("mask-key", b_i)
K_V[i] = H("vote-key", v_i)
```

`H` is a domain-separated hash; the literal strings `link-key`, `mask-key`, `vote-key` are the
domain separators. The revisions from v0.3 onward use the three secrets for three distinct roles —
repeatable link, maskable identity, and the per-message authorization credential — the same
separation that v0.2/v0.3's relation mock tests (`src/ce_qs_relation_mock.py`,
`docs/finalized-construction.md:150–300`).

**Assumption.** `H` is a collision-resistant, quantum-safe hash with the stated domain separation,
and the registration keys are bound *before* the confirmation matrices of §3.4 are sampled (the
order matters — see v1.20's frozen-registry condition, `docs/blocker-resolution.md:76–108`).

### 2.2 The message challenge, the link and the masked identity

The context already carries a canonical 64-byte message digest `m`. v1.24 removes the separate
challenge hash by reading those bytes directly as a field element
(`docs/32kib-contents-contract.md:29–38`):

```
F  = GF(2)[x] / (x^512 + x^8 + x^5 + x^2 + 1)
c_m = decode_F(m)
```

`decode_F` is the bijection between 64-byte strings and elements of `F` given by the polynomial
basis. Because it is a bijection, `m ≠ m' ⇒ c_m ≠ c_m'`, so no *additional* collision assumption is
introduced for this step. Every nonzero difference is invertible in a field; division is used only
on `c_m + c_m'` with `m ≠ m'`, so zero is a legal message challenge.

For a selected seat `i` (`docs/32kib-contents-contract.md:50–54`):

```
L_i = H("link-tag", a_i, cfg, d)                        -- the link tag
r_i = decode_F( H("mask-pad", b_i, cfg, d) )            -- the mask pad
Z_i = r_i + c_m * embed(i + 1)                          -- the masked identity
```

- `cfg` is the configuration identifier: it commits to the exact relation (all `CEQS124/` labels)
  and to the registry.
- `d` is the conflict domain `τ` (the source writes `d` in the handle equations and `τ` in prose;
  they are the same object).
- `embed(i+1)` maps the integer `1 … 64` into `F` (injective by construction); `i+1` is used so that
  seat 0 does not map to the field element 0.
- `L_i` and `r_i` depend on the **domain, not the message** — this is what makes them *repeatable*
  across two conflicting certificates.

**Assumption.** The mask pad `r_i` behaves as a pseudorandom field element under the chosen hash
(one-tag hiding, carried over from v0.5's assumption A1, `docs/formal-proof-stack.md`), and
`embed` is injective on `{1, …, 64}` in `F`.

### 2.3 Extraction on conflict

Given two accepted certificates for `M ≠ M'` in the same domain and with the same configuration, the
extractor matches handles by link, so for a doubly-approving seat the same `i` appears in both, and
computes (`docs/32kib-contents-contract.md:56–62`):

```
ihat = integer( (Z_i + Z_i') * (c_m + c_m')^{-1} ) - 1
```

Substituting `Z_i = r_i + c_m·embed(i+1)` and `Z_i' = r_i + c_m'·embed(i+1)`, the mask pads cancel
and the quotient is exactly `embed(i+1)`, so `ihat = i`. The recovery uses no secret, no
per-certificate sidecar and no proving transcript, and it exposes only seats that signed **both**
messages. Acceptance requires the recovered field value to encode an identity in the range identified
by the registry, and comparison is only permitted between certificates with the same `cfg` and `d`.

**Assumption.** The field was validated independently at v1.23 and v1.24 adds boundary tests for
zero, high-bit and all-one message encodings (`docs/32kib-contents-contract.md:62,139`).

### 2.4 The relation the proof must establish

Let (`docs/32kib-contents-contract.md:64–79`)

```
X = ( cfg, d, m, (L_j, Z_j)_{j=1..43} )                       -- public statement
W = ( (i_j, a_j, b_j, v_j) )_{j=1..43}                        -- witness
```

A public parser first establishes *exactly 43* complete, canonically sorted handles and the expected
context. The proof must then establish that there **exists** a witness `W` with

1. every `i_j` an index in `0 … 63`, and the 43 indices **distinct**;
2. for each row, all three secret credentials open the three registered keys at that **same** index;
3. each public link is computed from the registered link credential and this configuration/domain;
4. each public masked identity is computed from the registered mask credential, the existing message
   bytes, and that same index;
5. every public input is bound to the proof, including the complete handle list and the exact
   relation/suite identifier.

The requirement is an **argument of knowledge**, not merely a short proof that the NP statement is
satisfiable, and it must be zero knowledge. The source states plainly which obligations are *not*
discharged by any of this: actual authorization, non-framing, adaptive joint quantum extraction and
the numerical QPT-128 loss budget must be established in the approval-oracle experiment
(`docs/32kib-contents-contract.md:79`). A parser, a witness checker, or a proof of possession without
the matching message-binding theorem does not discharge them.

### 2.5 Distinctness by column occupancy

Condition 1 of §2.4 (43 distinct seats) is expressed algebraically for an odd-prime-field proof
system. Give handle row `j` six private Boolean selector bits `b_{j,k}`, and let `i_k` be the bits of
a public index `i` (six bits suffice for `0 … 63`). Then
(`docs/32kib-contents-contract.md:81–100`):

```
e_{j,i} = PROD_{k=0..5} ( (1 - i_k)(1 - b_{j,k}) + i_k * b_{j,k} )
```

For Boolean selector bits this is exactly 1 at the selected index and 0 elsewhere — a one-hot
selector. The same coefficients select **all three** key tables bit by bit:

```
K^(r)_{j,ell} = SUM_{i=0..63} e_{j,i} * K^(r)_{i,ell},     r in {L, R, V}
```

so that identity scaling and registry membership cannot refer to different seats. Distinctness is
then enforced through **column occupancies**:

```
s_i = SUM_{j=1..43} e_{j,i},        s_i (s_i - 1) = 0   in F_p,  p > 43
```

Each `s_i` is an integer in `0 … 43`; because the field characteristic exceeds 43, its residue is 0
or 1 only when the actual count is 0 or 1. With 43 one-hot rows, exactly 43 different seats are
selected — distinctness without ever exposing a bitmap. The source attaches two explicit warnings:
these equations must **not** be transposed unchanged into characteristic two (counts collapse to
parity), and the construction of the selector has its own cost, so no whole-circuit performance
improvement is claimed (`docs/32kib-contents-contract.md:100`). Field arithmetic used:

```
z_AND = x * y ,    z_XOR = x + y - 2xy ,    b (b - 1) = 0
```

**Assumption.** A proof system over `F_p` with `p > 43` and sound Boolean encodings. The test field
`101` used by the reference test checks the count equations only and is **not** a cryptographic
parameter proposal (`docs/32kib-contents-contract.md:108`).

### 2.6 Distributed generation

The certificate is produced jointly, without recursion
(`docs/32kib-contents-contract.md:110–124`):

```
(X, pi) <- MPC[ SelectAndProve_{R_43} ]( (eta_i, a_i, b_i, v_i)_{i=0..63} ; rho )
```

- `eta_i` — seat `i`'s private approval of the exact public configuration/domain/message;
- `rho` — the joint randomness;
- `SelectAndProve_{R_43}` — inside the secure computation: validate approving inputs against their
  authenticated seat slots, choose 43 valid approvals if available, build their sorted public
  handles, and run the ordinary randomized prover.

Only `X, pi` are output. In an ideal execution the output is an ordinary direct proof: it contains
neither 43 proofs of individual contributions nor a proof verifying those proofs. For robustness the
design keeps **64 logical MPC participants** and tolerates at most **21 corrupt or withholding
participants in total**, for which the classical threshold `n > 3f` is numerically compatible
(`64 > 63`). The source is explicit about the limits of that citation: a protocol involving only 43
parties cannot invoke the theorem to tolerate 21 Byzantine parties; synchrony, authenticated private
channels, active security and the corruption model must match the chosen theorem; and the classical
BGW result is **not** by itself a completed quantum-composable instantiation — Unruh's lifting
theorem applies only once the necessary statistical classical UC-security premise has been
established (`docs/32kib-contents-contract.md:122`).

Protocol messages exchanged while generating the proof may be large; they are not part of later
verification or tracing, and a scheme that needs them again has failed the contract.

---

## 3. Theory used, and which part of it

Each entry gives the statement **as the source uses it**, what it justifies, whether the whole result
or only a part is used, and the citation exactly as the source gives it. Where the source's citation
is incomplete, that is stated rather than filled in.

### 3.1 Byzantine quorum arithmetic (used in full)

For `n = 3f + 1`, `q = 2f + 1`, any two quorums satisfy

```
|S0 ∩ S1| >= 2q - n = 2(2f+1) - (3f+1) = f + 1 = 22
```

used in this project as: at least one seat that approved both conflicting messages is **honest**, so
extraction identifies a genuine equivocator rather than only a pair intersection. The statement as
used is elementary set arithmetic over the quorum family; it is exercised exhaustively by
`src/ce_qs_quorum_family_checker.py` for `n = 4, 7, 10` and instantiated at `n = 64` with
`combinatorial_required_columns = 41107996877935680`, `log2 = 55.190269`
(`results/ce_qs_quorum_family_checker.txt`). Used in **full** — nothing is borrowed and abandoned.

### 3.2 Privacy Separation Theorem (used as the reason for the B0/B1 split)

Statement as used (`docs/quorum-family-privacy-fork-proof.md:665–700`): for a fixed `n ≤ 64` BFT
committee, **without** signer-set privacy conflict accountability reduces to exact multisignature
signer-set binding plus an `n`-bit bitmap; **with** signer-set privacy a valid certificate must hide
the quorum while retaining a latent relation enabling conflict-only extraction. Consequence drawn by
the source: CET/DAPT-style cryptography is needed for *privacy-preserving accountability*, not for
conflict accountability by itself, so the target splits into B0 and B1. Only this separation is
used; the theorem says nothing about size, which is why both B0 and B1 still carry an open
"practical < 32 KiB backend" line in the v0.7 status table
(`docs/quorum-family-privacy-fork-proof.md:888–895`). Citation: the source gives none beyond its own
numbering — record as stated by the source.

### 3.3 Monotone-policy aggregate signatures — part used: the weighted-threshold instantiation

Name and citation as the source gives it: Brodsky, Choudhuri, Jain and Paneth, EUROCRYPT 2024
(`docs/public-signer-theoretical-completion.md:46`). Statement as used: there exists an aggregate
signature for **monotone policies** whose verification takes a public policy `f`; the construction
explicitly supports **weighted threshold** policies, of which the certificate's bitmap-conjunction
policy `f_B` is one (`:730`). Used to justify the whole B0 reduction:
`Adv^{SetFrame}_{AQC} ≤ Adv^{UF}_{MPAgg}` (`:484–486`), the conflict-extraction theorem
`supp(B0 ∧ B1)` and the BFT conflict bound `2·Adv^{UF}_{MPAgg} + Adv^{BaseSafety}` (`:694–700`).

**Part not used.** The paper's aggregate-size and verification-time theorem is quoted as
`185.5 KB` for the `N = 1024`, `τ = 20`, 128-bit profile (`:16–19`), correcting an earlier figure of
201.2 KB; that number is 5.7× the whole certificate budget and is therefore *evidence against*
compactness, not a justification of it. The B0 result is explicitly labelled
"Theoretical… at the abstract cryptographic level" (`:811`), and the source lists as unresolved
whether the full monotone-policy BARG/vPIR stack has a published QPT theorem matching the needed
properties (`:898`). Underlying machinery the source names: adaptive subset-extractable monotone-policy
BARGs and vPIR (`:825–827`).

### 3.4 Conflict-extractable tags — DAPT lineage (used as the trace-layer idea only)

The certificate's tag shape is the project's own: `e_i(τ, M) = r_{i,τ} + c · x_i`, extracted by
`x_i = (e_0 − e_1)(c_0 − c_1)^{-1}` (`docs/finalized-construction.md:240`). The source names the
lineage as **Tetris / DAPT — Doubly-Authentication-Preventing Tags**, with deterministic
`Tag(sk, topic, message)` and public `TagTrace` on two different messages under one topic, and with
threshold-ring traceability definitions requiring identification of guilty signers rather than mere
detection (`docs/finalized-construction.md:42–46`). **Only the interface idea is used**: that a tag
can be deterministic in `(key, topic)` and message-dependent in an invertible linear way, so that a
conflicting pair cancels the pad. No Tetris construction, proof or parameter is imported. The source
gives no bibliographic citation for Tetris/DAPT at that point — the citation is incomplete and is
left as the source states it.

At v1.24 the algebra is specialized: the "secret" `x_i` disappears and the extracted quantity is the
embedded public identity `embed(i+1)` (§2.3). The general form remains the fallback in the B1
lineages v1.0 and v1.1.

### 3.5 Weak pseudorandomness from LWR, and its quantum form QLWR (used: the assumption, stated
directly)

`LWR` = learning with rounding; `QLWR` as the source defines it (`docs/qpt-crs-security-proof.md:278`):
the ordinary LWR distinguishing experiment, except the distinguisher is a quantum polynomial-time
machine receiving polynomially many **classical** random samples. `v1.3` uses it for the
Yang–Au–Lai–Xu–Yu function as a weak pseudorandom function against QPT distinguishers with classical
random-sample access (`:315`). **Part not used:** the source declines to derive QLWR from LWE
("Known LWE-to-LWR reductions are parameter/sample dependent", `:302`) and instead states QLWR
directly as an assumption (`:306–307`). That is the honest reading: the security theorem is
conditional on QLWR, not reduced to LWE.

### 3.6 Simulation-extractable NIZK in the CRS model (used: existence, quoted verbatim)

As the source states it (`docs/qpt-crs-security-proof.md:523`): "Assuming polynomial quantum hardness
of LWE, there exists a simulation-extractable, adaptive multi-theorem computationally zero-knowledge
argument for NP in the common reference string model." Attributed in the source to Jawale–Khurana
(`:31`). Used to replace Fiat–Shamir/Stern compilation, which would keep a random-oracle dependency
in the load-bearing theorem. Only the **existence** statement is used; no concrete instantiation,
size estimate or implementation is taken from it, and the source labels the resulting setup cost as
polynomial but possibly large (`:223`).

### 3.7 Strong Certified Conflict Handles (used: the interface and the games; not a construction)

Introduced by this project at v1.1 to replace the informal `TT1–TT5` trace abstraction
(`docs/strong-certified-conflict-handle-proof.md:32`), with syntax (Setup, KeyGen, Handle,
VerifyHandle, SameSigner, TraceConflict, VerifyTrace) and six games S1–S6 (`:150–253`). The stated
motivation is a gap the source attributes to the 2025 preprint *Traceability for Free: Traceable Ring
Signatures Revisited*, which "identifies a gap in the classic Fujisaki–Suzuki security notions"
(`:13`), i.e. classic traceable-ring notions miss trace-specific attacks and do not imply
unforgeability. **Part used:** the property list, as the target interface that a backend must meet.
**Part not used:** no SCCH construction is adopted. The source records instead that the direct
strong traceable ring signatures it examines miss compactness — a lattice construction at
≈5.80 MiB for 43 signatures (`:559`) and a classical DDH/Bulletproof construction at 38.97 KiB
(`:607` vs. the 32,768-byte gate) — and that a strengthening/adaptation theorem would be required
before using the latter as the load-bearing instance (`:528`).

### 3.8 VOLE-in-the-Head threshold ring signatures (used: the exactness/near-miss lesson)

Cited as Chiang et al., *Post-Quantum Threshold Ring Signature Applications from VOLE-in-the-Head*,
CCS 2025 (`docs/formal-proof-stack.md:1559`). **Part used:** the source's own warning that its
succinct aggregation based on approximate lower-bound arguments requires the aggregator to hold
**more than `t`** valid signatures (`docs/research-synthesis-final.md:530–556`) — the fact that
forced the `Δ > 0` discussion, and, after correction, the telescope parameter formula of §3.9.
**Part not used:** no VOLEitH proof system is instantiated; v0.3's relation mock and v1.24's
relation are both reference code, not a VOLEitH implementation.

### 3.9 Telescope / ELBA equation (13) — used as arithmetic, in one direction only

As used at v0.5 (`docs/formal-proof-stack.md:55–85`):

```
u >= ( lambda_sound + log2 lambda_comp + 1 - log2 log2 e ) / log2( n_p / n_f )
```

with `λ_sound = λ_comp = 128`, `n_p = 43`, `n_f = 42` giving `u ≥ 3991`, and, at the paper's
reported ≈9.91 KB for one linkable AES128 ring signature at ring size 64, a naive proof of
`3991 × 9.91 KB ≈ 38.6 MiB`. At full participation (`n_p = 64, n_f = 42`) the same formula gives
`u ≥ 223` ≈ 2.2 MiB. **Part used:** the formula, purely to bound size and to *retract* v0.4's
impossibility claim. **Part not used:** ELBA is not part of the construction — v0.5 states "ELBA is
**not** used in this exact semantic definition" (`docs/formal-proof-stack.md:299`).

### 3.10 BGW threshold and Unruh lifting (used: the numerical condition only)

Ben-Or, Goldwasser, Wigderson, STOC 1988 — as the source cites it, via the author-institution record,
for the Byzantine threshold `n > 3f` (`docs/32kib-contents-contract.md:153`). Unruh,
*Universally Composable Quantum Multi-Party Computation* (`:154`), whose lifting is used **only with
its stated premise**. Used to justify that 64 MPC participants tolerate 21 Byzantine participants
numerically; explicitly **not** used to claim a quantum-composable MPC instantiation.

### 3.11 MPC prover decomposition (used: the architecture, not an implementation)

Ozdemir–Boneh, USENIX Security 2022 — generic MPC proving, aborts, concrete implementations
(`docs/32kib-contents-contract.md:151`); Liu et al., USENIX Security 2025 — scalable collaborative
proofs, whose paper explicitly leaves the malicious-privacy extension as future work (`:152`). Used
to justify that a *joint* prover for one proof is a known architecture. **Part not used:** the
implemented efficient choices in the first are pairing-based and therefore not post-quantum, and
their abort model does not establish this project's progress condition; the second's prototype is
not the robust post-quantum prover this contract needs (`:132–133`).

---

## 4. The register of what is proven, measured and open

| Claim | Label in the source | Where |
|---|---|---|
| Two quorums share ≥ 22 seats; coverage of the fault family | proved / exhaustive computation | `docs/quorum-family-privacy-fork-proof.md:96`; `results/ce_qs_quorum_family_checker.txt` |
| Bitmap-conjunction policy `f_B` equals the claimed-signer-set conjunction | proved (exhaustive n = 3, 4, 5) | `docs/public-signer-theoretical-completion.md:155–182`; `results/ce_qs_bitmap_policy_checker.txt` |
| B0 accountability reduces to monotone-policy aggregate unforgeability | conditional reduction | `docs/public-signer-theoretical-completion.md:484–486,694–700,704` |
| "Target B0 is theoretically solved at the abstract cryptographic level" | claim, conditional on the QPT stack | `docs/public-signer-theoretical-completion.md:811`, caveat `:898` |
| Private wrapper for B1, PW1–PW8 | conditional theorem over abstract primitives | `docs/quantum-lift-private-wrapper-proof.md:550` |
| v1.0 per-validator certified tags + collector | conditional theorem; collector secret-constructibility **corrected** vs v0.9 | `docs/distributed-certified-tag-proof.md:19–37,448–484,1077` |
| SCCH interface S1–S6 and `VerifyBlame` | definition + security games | `docs/strong-certified-conflict-handle-proof.md:150–253,297–341` |
| QPT conditional theorem for the hidden-signer construction | conditional theorem, nine assumptions | `docs/qpt-crs-security-proof.md` (claim boundary `:8`) |
| Collaborative prover composition + corrected anonymity hybrid | conditional theorem, correction of v1.3 | `docs/collaborative-quorum-proof.md:7,11–103,624` |
| Backend eligibility properties E1–E8 and the instantiation theorem | definition + conditional theorem | `docs/backend-eligibility-proof.md` |
| No examined construction qualifies; valid full QCs generated = 0 | negative screening result | `docs/research-qualification.md:7` |
| Retained-format floor 50,496 B > 32,768 B | exact arithmetic | `docs/research-qualification.md:167` |
| 176 link rows suffice for a frozen registry | arithmetic bound, conditional on registration order | `docs/blocker-resolution.md:76–108` |
| Executed trace circuit 9,800,861 gates, 722,528-byte frame | measurement | `docs/blocker-resolution.md:7,159` |
| 0.0737 encoded bytes/gate; 662 bytes/seat; 50,384-byte prefix | measurement + arithmetic | `docs/size-path-resolution.md:12,17,21` |
| v1.24 certificate contents and relation; 44 reference checks pass | specification + reference test | `docs/32kib-contents-contract.md:139–145` |
| One self-contained QPT proof inside 27,056 bytes | **open** — the stated remaining target | `docs/32kib-contents-contract.md:145` |
| Measured CE-QS proof size; distributed prover; QPT-128 loss budget with constants | **open** | `docs/32kib-contents-contract.md:145`; `docs/size-path-resolution.md:89–99` |

---

## 5. What must still be validated for this to stand as a standard proof

Stated by the sources themselves; repeated here without softening.

1. **A concrete proof.** No proof system has been instantiated for the relation of §2.4. The v1.24
   reference test checks information sufficiency, the extraction algebra and the count equations; it
   writes no proof. "The present work does not yet supply that cryptographic proof"
   (`docs/32kib-contents-contract.md:145`).
2. **Authorization inside the proof.** Every executed circuit contains **zero ML-DSA verification
   constraints** (`docs/blocker-resolution.md:7`); the v1.24 design replaces them with hash
   credentials in the relation, which is a *proposal* — "This choice does not establish ML-DSA
   compatibility" (`docs/32kib-contents-contract.md:25`).
3. **A distributed prover.** The MPC architecture removes recursive verifier arithmetization from
   the *proposed* architecture, "not from an already completed distributed implementation"
   (`docs/32kib-contents-contract.md:120`).
4. **The QPT-128 account.** v1.19 corrected `8·2⁻¹³¹ = 2⁻¹²⁸` and stated that eight terms each
   bounded only by `2⁻¹²⁸` give `2⁻¹²⁵` — probabilities are added, not bit exponents
   (`history/blocker-resolution-v1.19.md:202–205`). The project must carry a resource profile
   (quantum queries and computation, signing queries, users, sessions, epochs, corruption and
   exposure), not the phrase "128-bit security" (`:191`).
5. **The anonymity admissibility condition.** Open since the v1.3 → v1.4 correction
   (`docs/collaborative-quorum-proof.md:11–27`); the same wording recurs in v0.6 and v0.9.
6. **A machine-checked or fully formal proof.** None exists in this domain; every theorem above is
   paper-level and conditional.

## 6. Open items

- Produce the proof of §2.4 inside 27,056 bytes, or lower the claim.
- Decide the authorization mechanism inside the relation and qualify it (hash credentials as
  specified, or another route), including its quantum security.
- Qualify one of the two candidate direct-proof routes named at v1.24 (succinct lattice proofs;
  Spartan-style constraints with WHIR openings) against the complete relation
  (`docs/32kib-contents-contract.md:130–131`).
- Establish the distributed prover's security in the corruption model actually used, and the
  classical UC premise that Unruh lifting would need.
- Reconcile the retained measured frames (722,528 / 729,728 B) with the 32,768-byte gate; the gap is
  a factor of ≈22 on measurement and ≈2 on the arithmetic floor of the retained format.
- Supply the missing version documents (v1.2, v1.5 main document, v1.7–v1.17, v1.22, v1.23) or
  remove the dependence of the ladder on them. Today no claim in this domain rests on a missing
  document — see `README.md` §3.5.
