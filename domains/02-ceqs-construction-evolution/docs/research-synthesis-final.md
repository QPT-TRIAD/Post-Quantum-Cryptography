# CE-QS v0.4 — Research-Synthesis Finalization
## Sidecar-Free Conflict-Extractable Compact Post-Quantum Quorum Signatures

**Status:** construction specification finalized for implementation.  
**Date:** 2026-09-08  
**Track:** Target B only; Target A v0.8 remains unchanged.  
**Claim boundary:** this document finalizes architecture, definitions, source choices, fallback paths, and implementation gates. It does **not** claim a completed cryptographic reduction, native QROM proof, or measured CE-QS proof size.

---

# 1. Executive conclusion

After the v0.1–v0.3 algebra/relation work and a broad prior-art search, the first practical sidecar-free CE-QS construction should be frozen as:

\[
\boxed{
\text{fixed-epoch PQ threshold-ring authentication}
+
\text{public anonymous conflict-extractable tags}
}
\]

with certificate

\[
\boxed{
\Sigma =
(v,e,\tau,H(M),q,E,\Pi).
}
\]

Here:

- \(E\) is a list of distinct deterministic anonymous CET tags;
- \(\Pi\) is a post-quantum hidden-threshold proof/aggregate;
- one certificate hides signer identities;
- two conflicting certificates in one BFT conflict domain reveal the common signers;
- no sidecar and no permanent tracing authority exist.

The project should **not** return to modifying Hermine-style lattice threshold-signature masking. The best-qualified primary path is the 2025 VOLE-in-the-Head threshold-ring construction because it already contains the exact neighboring mechanisms CE-QS needs: hidden threshold membership, deterministic key-binding pseudorandom tags, anonymous contributions, and public aggregation.

The one major operational caveat is that its succinct aggregation uses an **Approximate Lower Bound Argument (ALBA)** and therefore may require the aggregator to possess more than \(q\) contributions to convince the public that at least \(q\) were known. This becomes a hard BFT feasibility constraint rather than a footnote.

---

# 2. Source qualification policy

Sources are ranked before being made load-bearing.

## Tier A — peer-reviewed primary construction/security source

Can be load-bearing.

- Chiang et al., CCS 2025 — PQ threshold ring signatures from VOLE-in-the-Head.
- Avitabile, Botta, Fiore, ESORICS 2025 — Tetris / DAPT.
- Boneh, Kim, Nikolaenko, ACNS 2017 — lattice DAPS/PAPS.
- Chaidos, Kiayias, Reyzin, Zinovyev, EUROCRYPT 2024 — ALBA.
- Baum et al., CRYPTO 2025 — improved QROM analysis for VOLE-in-the-Head signatures.
- Lin, Wang, Wen, Sun, Liang, Designs Codes and Cryptography 2025 — GC-TRS / lattice CTRS.
- Boneh, Komlo, CRYPTO 2022 — TAPS.

## Tier B — accepted/forthcoming primary paper or project preview

Useful, but not used to assert a theorem absent accessible technical details.

- TripleRing+ (ESORICS 2026 accepted) — compact PQ TRS from ML-DSA.
- LoTRS NIST Threshold Call preview 2026.

## Tier C — implementation repository

Useful to select concrete integration points, never a substitute for the paper proof.

- `jachiang/PQ-Threshold-Ring-Sigs-from-VOLEitH`.
- General-purpose VOLEitH libraries such as `libtalos_voleith` are secondary implementation aids only.

---

# 3. Schools of thought and what CE-QS borrows

## 3.1 Tetris / DAPT

Borrow:

\[
\boxed{
\text{same topic + different message + same signer}
\Rightarrow
\text{public trace}.
}
\]

Do not borrow:

- pairings;
- Groth–Sahai;
- extendability;
- ring growth;
- threshold growth after signature creation.

The BFT committee is fixed per epoch, so those capabilities only add proof surface.

---

## 3.2 PQ VOLE-in-the-Head threshold ring signatures

Borrow:

- hidden \(t\)-of-\(n\) authentication;
- anonymous signer contributions;
- deterministic key-binding tags;
- tag pseudorandomness for anonymity;
- public aggregation;
- symmetric-key-only PQ assumptions.

This is the **primary base adapter**.

---

## 3.3 DAPS/PAPS

Borrow the security pattern:

\[
\text{ordinary signatures remain safe}
\]

until

\[
\phi(M_0,M_1)=1,
\]

at which point signer-linked secret information becomes extractable.

This provides the closest PQ precedent for deliberately engineered conflict leakage.

---

## 3.4 E-cash / RLN

Borrow only the algebraic pattern:

\[
\text{one sample hides the secret;}
\qquad
\text{two forbidden samples reconstruct it}.
\]

This motivates the linear CET relation but is not a security dependency.

---

## 3.5 TAPS

Borrow the separation of:

- unforgeability;
- privacy/anonymity;
- accountability;
- framing resistance.

Do not borrow the permanent tracing key.

CE-QS tracing must be public and conflict-triggered.

---

## 3.6 GC-TRS / CTRS

Borrow as the **fallback proof architecture** if ALBA aggregation is incompatible with BFT liveness.

GC-TRS gives:

\[
\boxed{
\text{aggregated signature}
+
t\text{-out-of-}n\text{ proof}
}
\]

and lattice CTRS achieves logarithmic signature size relative to ring size.

CE-QS does not assume CET can be inserted into CTRS for free. It is the fallback research branch, not a silently interchangeable implementation.

---

# 4. Frozen CET definition

For validator \(i\):

- \(sk_i\): authentication witness;
- \(x_i\): trace secret;
- \(k_i\): mask PRF key;
- \(X_i=G_{\rm tr}(x_i)\);
- \(K_i=G_{\rm mask}(k_i)\).

For conflict domain \(\tau\):

\[
r_{i,\tau}
=
F_{k_i}
(
\texttt{CEQS-MASK-v1}
\parallel
\tau
).
\]

For message \(M\):

\[
c=
H_F
(
\texttt{CEQS-CHAL-v1}
\parallel
\tau
\parallel
H(M)
).
\]

The tag is:

\[
\boxed{
e_i(\tau,M)=r_{i,\tau}+c x_i.
}
\]

All quantities are interpreted in the chosen 256-bit field.

---

# 5. Frozen per-contribution relation

Public instance:

\[
I=(R_e,\tau,H(M),e_{\rm tag}).
\]

Hidden witness:

\[
w=(i,sk_i,x_i,k_i).
\]

Required relation:

\[
\mathcal R_{\rm CEQS}(I;w)=1
\]

iff:

\[
(pk_i,X_i,K_i)\in R_e,
\]

\[
\mathsf{AuthKeyRel}(pk_i,sk_i)=1,
\]

\[
G_{\rm tr}(x_i)=X_i,
\]

\[
G_{\rm mask}(k_i)=K_i,
\]

and

\[
e_{\rm tag}
=
F_{k_i}(\tau)+H_F(\tau,H(M))x_i.
\]

The proof hides the registry position and all three secrets.

The CET tag is public and Fiat–Shamir-bound to the contribution transcript.

---

# 6. Distinct hidden signers — finalized

For one fixed \((\tau,M)\), CET is deterministic.

Therefore:

\[
i\text{ contributes twice}
\Rightarrow
e_i=e_i.
\]

Verification rejects duplicate tags:

\[
\boxed{
|\operatorname{set}(E)|=|E|.
}
\]

However, public uniqueness alone is not sufficient cryptographic key binding.

The selected base proof must also guarantee that every accepted CET is bound to one valid hidden registered authentication key.

The resulting threshold semantics are:

\[
\boxed{
\text{at least }q
\text{ distinct valid key-bound CET contributions}.
}
\]

This is now a frozen protocol requirement.

---

# 7. Quorum anonymity — formal target finalized

Challenge:

- challenger selects one of two eligible signer sets of equal size;
- no signer violates the conflict predicate in the challenge domain;
- adversary receives the complete CE-QS certificate including \(E\);
- adversary guesses the hidden quorum.

Reduction skeleton:

1. replace each PRF mask \(F_{k_i}(\tau)\) by a uniform field element;
2. each public CET becomes uniform conditioned on the public challenge;
3. replace the ZK transcript by simulation;
4. reduce the residual view to base threshold-ring anonymity.

Target:

\[
\boxed{
\operatorname{Adv}^{Anon}_{CEQS}
\le
\operatorname{Adv}^{Anon}_{TRS}
+
q\operatorname{Adv}^{PRF}
+
\operatorname{Adv}^{ZK}.
}
\]

Permitted leakage:

- tag count \(s\);
- exact \((\tau,M)\);
- equality of a repeated same-message tag.

Signer identities and cross-topic linkage remain hidden.

---

# 8. Trace soundness — formal target finalized

`ExtractConflict` reports validator \(i\) only when some tag pair yields \(x^\*\) such that:

\[
G_{\rm tr}(x^\*)=X_i.
\]

If \(i\) did not contribute to both accepted certificates, then a successful trace implies at least one of:

1. a false relation proof was accepted;
2. key binding failed;
3. \(G_{\rm tr}\) admitted a collision/second preimage;
4. a challenge collision created an ambiguous denominator;
5. the PRF/tag relation was not the one proved.

Target:

\[
\boxed{
\operatorname{Adv}^{TraceSound}
\le
\epsilon_{\rm PoK}
+
\epsilon_{\rm keybind}
+
\epsilon_{G_{\rm tr}}
+
\epsilon_{H_F}
+
\epsilon_{\rm relation}.
}
\]

This is the exact reduction obligation.

---

# 9. Non-frameability — formal target finalized

The adversary wins if an honest validator \(i\) that did not contribute to both conflicting certificates is output by `ExtractConflict`.

Use the same bad-event partition as trace soundness, strengthened by challenger control over honest witness generation.

Target:

\[
\boxed{
\operatorname{Adv}^{Frame}_{CEQS}
\le
\operatorname{Adv}^{PoK/Sound}_{\Pi}
+
\operatorname{Adv}^{KeyBind}_{\Pi}
+
\operatorname{Adv}^{PRF}_{F}
+
\operatorname{Adv}^{Bind}_{G_{\rm tr}}
+
\operatorname{Adv}^{Coll}_{H_F}.
}
\]

The v0.2/v0.3 mock tests cover attack **shapes**, not this reduction.

---

# 10. Conflict extraction completeness — closed modulo proof soundness

For:

\[
n=3f+1,\qquad q=2f+1,
\]

accepted signer sets satisfy:

\[
|S_0\cap S_1|
\ge
2q-n
=
f+1.
\]

Every common signer supplies:

\[
e_{i,0}=r_i+c_0x_i,
\]

\[
e_{i,1}=r_i+c_1x_i.
\]

Therefore:

\[
x_i
=
(e_{i,0}-e_{i,1})
(c_0-c_1)^{-1}.
\]

So:

\[
\boxed{
|\mathsf{ExtractConflict}(\Sigma_0,\Sigma_1)|
\ge f+1
}
\]

except when the outer proof accepted invalid tag/witness relations or the challenge mapping failed.

The combinatorial/algebraic portion of this theorem is already validated by the project simulators.

---

# 11. Post-exposure security — finalized

Conflict tracing exposes only \(x_i\).

It does not expose:

\[
sk_i
\]

or

\[
k_i.
\]

A new accepted contribution still requires:

\[
\mathsf{AuthKeyRel}(pk_i,sk_i)=1
\]

and:

\[
G_{\rm mask}(k_i)=K_i.
\]

Thus extracted \(x_i\) is deliberately a **blame credential**, not an authentication credential.

Mandatory operational action:

1. slash/mark signer faulty;
2. remove it at the next safe configuration change;
3. rotate trace/mask keys before any re-admission.

Stronger optional profile:

- epoch-evolving \((x_i^{(e)},k_i^{(e)})\);
- secure erasure.

Forward-secure lattice ring-signature research shows a qualified PQ path for one-way key evolution, but v0.4 does not require importing that construction into the first fixed-epoch design.

---

# 12. Aggregation — the ALBA/BFT feasibility condition

This is the most important new systems constraint.

The 2025 VOLE-in-the-Head threshold-ring paper states that its succinct aggregation based on approximate lower-bound arguments requires the aggregator to possess **more than \(t\)** valid signatures to convince the verifier that at least \(t\) are known.

Define:

\[
\Delta_{\rm ALBA}(\lambda,\varepsilon,\text{parameters})
\]

as the required aggregation slack.

For BFT finality threshold:

\[
q=43.
\]

Then the collector must obtain:

\[
\boxed{
q_{\rm collect}
=
q+\Delta_{\rm ALBA}.
}
\]

But Byzantine-independent liveness with \(n=64,f=21\) has only:

\[
n-f=43
\]

honest validators.

Therefore:

\[
\boxed{
\Delta_{\rm ALBA}>0
\Rightarrow
\text{the approximate succinct aggregate cannot be a Byzantine-independent 43-of-64 finality primitive.}
}
\]

This is a major result of the synthesis.

It means the ALBA **succinct aggregate path cannot be the only finality verifier** for the existing \(n=64,q=43\) BFT profile unless:

- the committee threshold changes;
- the fault model changes;
- Byzantine validators are required for progress;
- or the selected ALBA parameters support exact \(q\) knowledge, which would no longer be the same approximate scheme.

None of those should be silently assumed.

---

# 13. Aggregation architecture decision

v0.4 therefore separates two modes.

## Mode A — exact sidecar-free CE-QS

Required for consensus finality.

Certificate contains at least \(q\) distinct anonymous CET contributions whose individual PQ proofs are exactly verified, or uses an exact threshold-ring construction whose theorem guarantees \(q\) signers without positive slack.

This preserves:

\[
q=43
\]

liveness with all Byzantine validators silent.

Potential cost: certificate size may remain \(O(q)\).

## Mode B — ALBA succinct aggregate

Optional optimization only.

Use when:

\[
q_{\rm collect}
=
q+\Delta_{\rm ALBA}
\]

is actually available.

It must never replace Mode A's liveness-critical semantics unless the consensus fault model is changed and re-proved.

This avoids importing an approximate cryptographic threshold into an exact BFT quorum rule.

---

# 14. Primary base choice — revised

Because of Section 12, the VOLE-in-the-Head work remains the **best implementation scaffold for anonymous contributions and CET relation proofs**, but its approximate succinct aggregation is not automatically the final BFT aggregation layer.

Primary implementation work should therefore start with:

\[
\boxed{
\text{exact verification of }q\text{ anonymous VOLEitH+CET contributions}.
}
\]

Only after that works should ALBA compression be benchmarked as an optional layer.

This is safer than building the entire project around approximate aggregation and discovering later that it requires Byzantine cooperation.

---

# 15. Fallback exact compact threshold-ring bases

If \(q\) independent VOLEitH contributions make the certificate too large, evaluate two peer-reviewed fallback lines.

## 15.1 GC-TRS / CTRS

Advantages:

- generic aggregate-signature + \(t\)-out-of-\(n\) proof structure;
- lattice instantiations;
- CTRS logarithmic in ring size.

Unknown for CE-QS:

- efficient CET binding into the aggregated signature/proof;
- compatibility with public conflict-trace tags;
- exact QROM posture for the intended adapter.

This is the strongest conceptual fallback.

## 15.2 Rejection-free lattice threshold ring signatures

Recent lattice TRS work removes rejection sampling and proves strong anonymity properties.

Advantages:

- no VOLEitH dependency;
- exact threshold semantics.

Unknown for CE-QS:

- adding DAPT/CET without destroying those proofs;
- final trace-tag binding and size.

Use only if the primary VOLEitH relation path fails size/latency gates.

---

# 16. Source-level implementation map — authors' repository

The official companion repository for the CCS 2025 VOLEitH threshold-ring work is:

`jachiang/PQ-Threshold-Ring-Sigs-from-VOLEitH`

The repository says it extends FAEST/VOLEitH with:

- standalone ring signatures;
- linkable ring signatures;
- higher-degree QuickSilver polynomials;
- large-ring disjunctions;
- multi-block public-key/tag functions.

Files visible in the repository indicate the relevant integration surfaces:

### Relation / AES proof layer

- `owf_proof.c`
- `owf_proof.h`
- `aes.c`
- `aes.h`

**WP1 action:** add CE-QS trace-secret binding, mask-key binding, and CET equation to the proved relation.

### QuickSilver constraint layer

- `quicksilver.c`
- `quicksilver.h`
- `polynomials.c`
- `polynomials.h`

**WP1 action:** express the additional key/tag constraints using the existing polynomial/field machinery.

### Signature/transcript orchestration

- `faest.c`
- `faest.h`
- `api.c`
- `api.h.in`

**WP2 action:** make `e_tag` a public transcript-bound contribution output.

### Ring parameters

The repository README states:

- ring size is configured in `config.h.in`;
- hot-vector dimension is configurable;
- security parameters are compiled for 128, 192, and 256-bit levels.

### Benchmark path

- `makeRunTests.sh`
- `bench.sh`
- `measure.py`
- `measure_print.py`

**WP6 action:** benchmark unmodified upstream first, then CE-QS fork under identical compiler/CPU settings.

This source-level map is an integration plan, not evidence that the changes have been implemented.

---

# 17. Alternative implementation scaffold

A 2026 general-purpose VOLE-in-the-Head C library exists with explicit support for arbitrary QuickSilver circuits and ring-signature modules.

It is useful because CE-QS's relation is naturally a custom circuit.

However:

- it is an implementation project, not the load-bearing peer-reviewed source;
- its designated-opener ring-signature module uses a permanent opener, which CE-QS explicitly rejects;
- it should be used only as a prototyping/reference implementation unless independently audited.

The official CCS-paper repository remains the primary code baseline.

---

# 18. Proof-size status — finalized honestly

Known exactly:

\[
|E|
=
q\cdot32.
\]

For:

\[
q=43,
\]

\[
|E|=1376\text{ bytes}.
\]

Unknown until WP1/WP2:

\[
|\Pi_{\rm CEQS}|.
\]

Therefore no document may quote a total CE-QS certificate size yet.

Engineering gates remain:

\[
|\Sigma|\le16\text{ KiB}
\Rightarrow
\text{green},
\]

\[
16<|\Sigma|\le32\text{ KiB}
\Rightarrow
\text{research-acceptable},
\]

\[
|\Sigma|>32\text{ KiB}
\Rightarrow
\text{fail practical compactness target}.
\]

If exact Mode A requires \(q\) independent VOLEitH proofs and exceeds 32 KiB, the project must either:

- implement an exact compact aggregation method;
- move to the GC-TRS/CTRS fallback branch;
- or acknowledge that Target B is sidecar-free but not compact enough.

---

# 19. QROM status — finalized honestly

The 2025 CRYPTO work on FAEST/VOLE-in-the-Head gives:

- a QROM analysis;
- a QROM analogue of the proof;
- a Fiat–Shamir transform stated to apply to VOLE-in-the-Head signature schemes.

Therefore:

\[
\boxed{
\text{QROM is a qualified adaptation path, not a solved CE-QS theorem}.
}
\]

The final CE-QS QROM proof must verify that:

1. the expanded relation is admissible under the transform;
2. CET public outputs are correctly included in the Fiat–Shamir statement/transcript;
3. anonymity hybrids remain valid under quantum oracle access;
4. extraction/non-frameability reductions compose with quantum access.

Until that is written, the project must label its first proof by the exact model actually used.

---

# 20. Why set-membership SNARKs are not load-bearing

Commit-and-prove set-membership systems are qualified technology for:

\[
u\in R_e
\land
P(u,w).
\]

But the selected threshold-ring base already proves hidden membership.

For \(n\le64\), adding an accumulator or general SNARK would duplicate functionality and assumptions.

Use this fallback only if a future registry is too large for the threshold-ring relation.

---

# 21. Why forward-secure ring signatures are not load-bearing

PQ forward-secure ring signatures now exist, including QROM/logarithmic-size constructions.

They validate the idea that post-exposure protection through one-way key evolution is feasible.

But v0.4 already obtains its first exposure boundary by:

- separating \(x_i\) from \(sk_i,k_i\);
- fixed epochs;
- mandatory re-key/removal after blame.

Therefore forward-secure ring signatures remain an optional hardening track, not part of the minimal proof.

---

# 22. Games that are now fully specified but not proved

The uploaded continuation correctly states that quorum anonymity, formal trace soundness, formal non-frameability, and QROM cannot be tested by the Python relation mock.

v0.4 closes the **specification gap**, not the proof gap.

The exact remaining games are:

## G3 — quorum anonymity

Defined in Section 7.

## G7 — trace soundness

Defined in Section 8.

## G8 — non-frameability

Defined in Section 9.

## G11 — QROM

Adaptation obligations defined in Section 19.

No additional mock tests can discharge these.

The next evidence must be a reduction or a real proof-system transcript experiment.

---

# 23. Formal proof work package

Write four separate reductions.

## R1 — one-tag hiding

Hybrid:

\[
PRF
\rightarrow
uniform\ mask
\rightarrow
uniform\ CET.
\]

## R2 — quorum anonymity

Compose R1 for all \(q\) tags with base threshold-ring anonymity and ZK simulation.

## R3 — trace soundness / non-frameability

Assume false trace, identify first bad event among:

- proof soundness;
- key binding;
- trace-commitment binding;
- PRF relation;
- challenge collision.

Reduce to corresponding primitive game.

## R4 — post-exposure authentication security

Give the adversary \(x_i\) explicitly and reduce any new accepted contribution to:

- authentication-key forgery;
- mask-key binding/PRF break;
- proof soundness break.

These are the first reductions to mechanize.

---

# 24. BFT theorem adapter

The BFT layer should depend on one abstract interface:

\[
\mathsf{VerifyCEQS}(R_e,\tau,M,q,\Sigma).
\]

The required theorem is:

> If `VerifyCEQS` accepts, then at least \(q\) distinct registered validators contributed valid hidden witnesses to the exact \((\tau,M)\), except with cryptographic failure probability.

Then existing quorum intersection gives:

\[
|S_0\cap S_1|\ge f+1.
\]

The conflict extractor converts those common hidden witnesses into publicly identifiable faults.

No BFT proof needs to know whether the exact threshold-ring backend is VOLEitH, CTRS, or another future adapter.

---

# 25. Final source decision matrix

| Source line | Use in CE-QS | Status |
|---|---|---|
| Tetris / DAPT | conflict-trace semantics | **load-bearing definition reference** |
| VOLEitH PQ threshold ring | primary hidden-threshold + key-binding-tag implementation scaffold | **primary implementation base** |
| DAPS/PAPS | PQ conditional-disclosure proof precedent | **load-bearing proof analogy** |
| ALBA | understand optional succinct aggregation and its gap | **load-bearing liveness constraint** |
| CRYPTO 2025 FAEST QROM | QROM upgrade methodology | **load-bearing adaptation reference, not automatic theorem** |
| TAPS | privacy/accountability game separation | **definition reference only** |
| GC-TRS / CTRS | exact/logarithmic fallback | **fallback branch** |
| rejection-free lattice TRS | alternative exact threshold/anonymity base | **fallback branch** |
| set-membership CP-SNARKs | large-registry fallback | **not used in v0.4 base** |
| forward-secure PQ ring sigs | post-exposure hardening | **optional** |
| TripleRing+ 2026 | watchlist for compact PQ trace tags | **accepted/forthcoming, not load-bearing** |

---

# 26. What is actually finalized

The following no longer need another literature-survey round:

- Target syntax.
- Fixed-epoch committee assumption.
- CET algebra.
- Dedicated trace-secret/key separation.
- Public duplicate-tag rejection.
- Hidden membership/key-binding relation.
- Conflict extractor.
- Quorum-intersection theorem adapter.
- Anonymity game.
- Trace-soundness game.
- Non-frameability game.
- Post-exposure policy.
- Primary proof-system family.
- Primary implementation repository.
- Fallback threshold-ring research branches.
- Certificate size gates.
- QROM adaptation path.
- Exact-vs-approximate aggregation distinction.

---

# 27. What cannot be finalized by research survey

These require new project work:

1. **Actual CE-QS QuickSilver/VOLEitH relation code.**
2. **Measured CE-QS proof bytes.**
3. **Measured sign/aggregate/verify latency.**
4. **Exact ALBA slack for chosen parameters and whether it is usable anywhere in the BFT stack.**
5. **Formal reductions R1–R4.**
6. **CE-QS-specific QROM proof.**
7. **Independent cryptographic review.**

These are no longer ambiguous research questions. They are implementation/proof deliverables.

---

# 28. v0.4 go/no-go sequence

## Gate 1 — exact contribution mode

Implement CE-QS relation on top of the official VOLEitH threshold-ring code.

PASS if:

- one contribution verifies;
- wrong CET/wrong registry tuple fails;
- duplicate tags reject;
- cross-topic behavior matches reference relation.

## Gate 2 — exact 43-of-64 certificate

Produce an exact sidecar-free certificate from 43 distinct contributions.

PASS if:

\[
|\Sigma|\le32\text{ KiB}.
\]

If not, go to fallback branch.

## Gate 3 — conflict extraction

Two 43-of-64 conflicting certificates must publicly extract every common CET signer in test fixtures.

## Gate 4 — formal reductions

R1–R4 reviewed internally before QROM work.

## Gate 5 — QROM adapter

Only after the classical/ROM proof structure is stable.

## Gate 6 — external cryptographic review

No production claim before this gate.

---

# 29. Final construction claim

The strongest accurate statement after the broad search is:

\[
\boxed{
\textbf{CE-QS is now a fully specified research construction with qualified primitive adapters and explicit proof/implementation gates.}
}
\]

It is not yet a proven cryptographic primitive.

The central design is:

\[
\boxed{
\Sigma=
(
q\text{ distinct anonymous key-bound CET contributions},
\text{PQ hidden-membership proofs/aggregate}
).
}
\]

Two conflicting certificates reveal common signers because quorum intersection supplies the same hidden identities in both certificates and CET algebra converts their two deterministic same-topic tags into public trace secrets.

No external sidecar or permanent tracing authority is required.

The most important qualification discovered in v0.4 is that **approximate succinct aggregation cannot silently replace an exact BFT quorum certificate**. For the existing \(n=64,f=21,q=43\) profile, any positive ALBA collection slack would require more than the 43 guaranteed honest validators, so exact threshold semantics must remain the consensus-critical baseline.

---

# 30. Primary references

- Chiang, Damgård, Duro, Engan, Kolby, Scholl. *Post-Quantum Threshold Ring Signature Applications from VOLE-in-the-Head*. ACM CCS 2025. DOI 10.1145/3719027.3744854.
- Avitabile, Botta, Fiore. *Tetris! Traceable Extendable Threshold Ring Signatures and More*. ESORICS 2025. ePrint 2025/730.
- Boneh, Kim, Nikolaenko. *Lattice-Based DAPS and Generalizations: Self-Enforcement in Signature Schemes*. ACNS 2017.
- Chaidos, Kiayias, Reyzin, Zinovyev. *Approximate Lower Bound Arguments*. EUROCRYPT 2024.
- Baum et al. *Shorter, Tighter, FAESTer: Optimizations and Improved (QROM) Analysis for VOLE-in-the-Head Signatures*. CRYPTO 2025.
- Lin, Wang, Wen, Sun, Liang. *Generic Construction of Threshold Ring Signatures and Lattice-based Instantiations*. Designs, Codes and Cryptography 93(9), 2025.
- Boneh, Komlo. *Threshold Signatures with Private Accountability*. CRYPTO 2022.
- Benarroch et al. *Zero-Knowledge Proofs for Set Membership: Efficient, Succinct, Modular*. Designs, Codes and Cryptography 2023.
