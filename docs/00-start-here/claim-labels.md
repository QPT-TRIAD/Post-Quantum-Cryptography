# Claim labels

Every claim in this repository carries one of seven labels. The labels are the dossier
specification's; they are defined once, in `docs/02-theory-and-references/README.md`, and they are
used with the same meaning in every domain unless a document states a different legend (see
*Two legends, one symbol* below).

## The rule that governs the whole repository

> **A label is never upgraded. A claim whose re-run does not reproduce is withdrawn in public, with
> the reason.**

Two consequences follow, and both are visible in the tree rather than merely promised:

- **A measurement never becomes a proof**, and a conditional theorem stays conditional. Where a source
  records a test result, the claim says `[M]` or `[S]` and reports the number with its test. Where a
  source records a proof, the claim says `[T]` and reports the proof's actual scope — including the
  case where the proof is written for one instrument and the connection to the protocol's quantity is
  still open.
- **Withdrawal is in place, with the date and the reason.** The withdrawn text is not edited to agree
  with the correction; the register keeps both. Four published withdrawals:

  | Withdrawn | Why | Recorded in |
  |---|---|---|
  | the property-layer figure "16/16 and 16/16" | a re-run gave 16 passes for the Mode B module and a **collection error with zero tests executed** for the hash-signature module, which builds a mixed `m ≠ n` parameter pair that the fix now refuses | `records/failed-assumptions.md` entry `A28` (2026-09-13) |
  | a recorded `PASS` in the S1-011 Grover slope assertion | it fails **51.3 % of the time** over 400 pooled runs; replaced by a multi-seed median | top-level `README.md` §2 |
  | **compat mode** — a category-5 signature inside an extractable proof | `ε_sig` must be evaluated at the reduction's running time, which includes the `O(q²)` extractor charge; the row then fails by **185 bits** in gate units | top-level `README.md` §2, `domains/06-qpt128-security-target/` |
  | the operator ledger's amendment count | measured against the document itself: **15 of 116** amendments have an executable witness (10 on a strict reading), **0 of 116** carry any literature citation, so **101 of 116** have neither | `domains/04-operator-ledger/README.md` |

  A fifth is a boundary rather than a withdrawal and is stated the same way: the original security
  target **D3** is refuted by Lemma L1 and survives only as a gate work factor.

---

## The seven labels

Each entry gives the label's meaning, the bar a claim carrying it must clear, and two instances in
this repository.

### `[T]` — theorem-with-proof

**Meaning.** A written proof, in the source, for the statement given.
**Bar.** The proof must be written, for *that* statement, with its assumptions **named**. A theorem
proved only under a named premise carries the premise in the same breath as the conclusion — it is
never restated without it. Where a proof is written for one instrument and the connection to the
protocol's quantity is open, the label says so.

1. **The quorum-intersection counting fact** — any two quorums intersect in at least `2q − N` seats
   (`2·43 − 64 = 22` at the reference committee), and the honest-support intersection
   `|H_0 ∩ H_1| ≥ f + 1 − c ≥ 1` that follows once the threshold-support assumption is granted.
   Both are elementary counting; the second is only as strong as the primitive assumption it consumes.
   → `domains/01-accountable-quorum-foundations/README.md`, section *What these documents establish*.
2. **Lemma L1**, which refutes the programme's own original target: `Pr[Win] < 2^-128` for every QPT
   adversary is unattainable for anything with a 256-bit secret, because `2^63` Grover iterations
   already exceed `2^-128`. Stated with its lemmas L2–L5 and their verdicts in the same document.
   → `domains/06-qpt128-security-target/docs/qpt128-finalization.md`, §1 and §3.3.

*A conditional `[T]` for contrast:* **Theorem A** for B0 is a theorem with proof, conditional on
`A-sig` (EUF-CMA of the chosen non-FIPS category-5 candidate at generic strength). The condition is
part of the claim. → `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md`.

### `[R]` — reduction-sketch

**Meaning.** The reduction is described and the loss accounted, but the steps are not written out in
full.
**Bar.** It must name what it reduces to, state the loss, and state which steps are missing. A sketch
that does not terminate in a standard assumption at a stated cost is not `[R]`; it is `[C]`.

1. **The end-to-end extraction argument** of domain 01 — the evidence-framing bound, the
   boundary-uniqueness bound and the extraction argument. The source states the inequality and the
   shape of the reduction and does not write the reduction out; the domain's own file marks the status
   `reduction sketch` at the line that states it.
   → `domains/01-accountable-quorum-foundations/docs/definitions-and-conflict-extraction.md`.
2. **The signature reductions** (v1.37 and v1.38): from two extracted conflicting R29 witnesses to
   single-user SU-EUF-CMA forgery, first against ML-DSA-87 and then against SLH-DSA-SHAKE-256s, with
   exact loss arithmetic and an AND-hybrid projection whose loss is exactly 1. The source labels them
   `[R]`. Their decisive property is qualitative: the reduction's **running time** is charged against
   the security target, which is what rules out the signature-inside-proof designs.
   → `domains/05-extraction-and-signature-reductions/docs/signature-reductions.md`;
   the label as the source gives it is recorded in
   `docs/02-theory-and-references/signature-security-reductions.md`.

### `[L]` — model-or-ledger estimate

**Meaning.** A number produced by a ledger, a model or an estimate.
**Bar.** The model must be explicit and its constants named; the result is a **computation, not a
proof**. A row whose premise is set rather than proved must say so — several rows in the hidden-signer
ledger are set to zero under model premises rather than derived, and they are marked as such.

1. **The linear-size family bound of 412,800 bytes** for witness-committing proofs, derived from a
   Keccak-f[1600] round model. The document's own section heading carries the label.
   → `domains/07-compact-certificate-b0/docs/construction.md` §7.1.
2. **The Binius64 polynomial-commitment floor of 109,856 bytes** (96-bit), from re-implemented
   estimators. Same document, same section, same label: an estimate from re-implemented estimators,
   not a measurement of a running system.
   → `domains/07-compact-certificate-b0/docs/construction.md` §7.2.

*Read beside them:* the "no known primitive fits" verdict for B1 is an assessment of published
primitives and is labelled as an assessment — **not** an impossibility proof, and the domain says so
in the same paragraph.

### `[M]` — measurement

**Meaning.** A number observed by running something on a named build and host.
**Bar.** The build and the host must be named, and the number must not be read as a bound or as a
security statement. The repository's own sentence: *no measured frame size in this repository is a
security bound or a proof of anything; the measurements say what these library builds produced on the
host named in the text.*

1. **The B0 size table** — 11,396 bytes with OV-V-pkc and 30,918 bytes with the OV-V-pkc‖SNOVA_29_6_5
   hybrid, each verified, each extracting 22 seats, each assigning blame and rejecting tampering.
   Measured through `liboqs` 0.16.0 / `liboqs-python` 0.16.0 and `pqcrypto` 0.3.4 on Ubuntu 24.04.4
   x86-64 with Python 3.12.3.
   → `domains/07-compact-certificate-b0/results/real-demo.json`, and the `--real-demo` command in
   [`reproduction.md`](reproduction.md).
2. **The attack lab's violation count: 0 of 24 attempts**, each rejection reported with the reason the
   implementation gave, with a positive control that must succeed and does. At n = 14, expansion 8 —
   deliberately weak parameters.
   → `domains/09-security-games-and-attack-lab/results/attack-lab-results.md` §2.

*A third, worth knowing:* the independent B0 implementation agreed with the reference on **6,701 of
6,701** checks over 900 generated vectors. → `domains/11-independent-audit-stack/independent-b0/`.

### `[S]` — simulation

**Meaning.** A number produced by a simulator, a toy field or a reduced parameter set.
**Bar.** Which of the three must be stated, and the claim must say that the result is **not** a
security claim for the production parameters. A simulation of an algorithm is not a simulation of the
circuit that would run it, and the repository's own output says so where that distinction matters.

1. **Exact Grover simulation on the real oracle** (Experiment C): state-vector simulation over the
   real key map plus handle, at `n = 8` to `13`. The simulated success probability tracks
   `sin²((2k+1)·arcsin√(M/N))` to double-precision noise at every iteration, and the measured optimal
   iteration count equals the predicted one exactly; fitted slope 0.512 against 0.5. The document
   states the limit plainly: this simulates the *algorithm* exactly and **does not model the gate cost
   of building the oracle circuit**.
   → `domains/09-security-games-and-attack-lab/results/attack-lab-results.md` §4.
2. **The toy VOLE-in-the-head proof** over a toy field at a reduced parameter set — the same proof
   pipeline as the production prover with none of its parameters: 7 tests covering GGM opening
   reconstruction, false-witness refusal, tampered-proof rejection, statement binding, and the
   measured-size formula.
   → `domains/08-hidden-signers/src/mode_b_voleith_toy.py`,
   `domains/08-hidden-signers/results/toy-self-test.txt`.

### `[A]` — assumption

**Meaning.** Taken as given, not proved.
**Bar.** The reason must be stated, and the claim must name where the assumption enters. An assumption
that is *essential* rather than technical must be marked as such, not folded into the proof.

1. **`A-sig`** — the chosen non-FIPS category-5 candidate is EUF-CMA at generic strength. Theorem A's
   non-frameability and safety reduce tightly and linearly to it, and the QPT-128 margin of +23.0 bits
   for B0 is conditional on it.
   → `domains/06-qpt128-security-target/README.md`, `domains/07-compact-certificate-b0/README.md`.
2. **Domain 08's five named assumptions** — `A-F1` one-wayness with handle, `A-F2` binding, `A-QROM`
   the quantum random-oracle model for the domain-separated SHAKE256 instances, `A-P` privacy, and
   `A-Prove` — the last marked **essential, not technical**: whoever holds an opening can frame that
   seat, so the honest fraction of a hidden-signer prover is an assumption the construction cannot do
   without.
   → `domains/08-hidden-signers/docs/mode-b-security.md` §2.

**The standing caveat.** A named assumption is not a theorem. The top-level README's validation list
makes this its item 3: `A-sig`, the QROM model, the T-count floors, the protocol-level assumptions and
the model-premise rows all remain assumptions.

### `[C]` — conjecture

**Meaning.** Stated as believed, not proved.
**Bar.** It must be identified as a belief or a direction, never as a result — and it must not be
carried into a later document as though it had been established.

1. **The Target B design direction** — extract a conflicting signer directly from two conflicting
   certificates with no sidecar. The memo is explicitly "not a construction, not a proof, not a claim
   of priority", and the domain states that its candidate direction was later **dropped**.
   → `domains/01-accountable-quorum-foundations/docs/frontier-conflict-extraction.md`.
2. **The signature-in-signature / hidden-until-disclosed accountability pattern** — hiding an
   extractable object inside signature randomness, revealed only when accountability is invoked.
   Recorded as a design idea in the trail, not a cited result; it carries `[C]` for exactly that
   reason, and the incomplete-citation list records it.
   → `docs/02-theory-and-references/quorum-and-accountability-combinatorics.md` (entry `D1-06`).

---

## Two legends, one symbol

`domains/03-zk-carrier-experiments/docs/theory-as-used.md` states its own legend, and in it **`[C]`
means "construction argument", not "conjecture"**, while `[T]`, `[A]` and `[M]` keep the meanings
above. Both conventions are live in the repository. The document states its legend at the top, and a
reader meeting a bare label should check which legend the document declares before interpreting it.

A related collision to watch: **`L1` is two different results.** In the security target it is the
lemma that refutes D3; in the operator ledger it is a budget inversion lemma.
`docs/02-theory-and-references/README.md` states the collision explicitly, and the entries always say
which document a lemma number comes from.

---

## Where the labels are defined and audited

- **Defined:** `docs/02-theory-and-references/README.md` — the seven labels, the two rules that follow
  from them, the four citation states, and the full/partial/transplant borrowing vocabulary.
- **Applied:** every domain. `docs/02-theory-and-references/` restates each entry with its label as the
  source gives it, and `gaps-and-unknowns.md` collects what is refuted, withdrawn, never re-run, never
  installed, or cited without a complete reference.
- **Audited:** `domains/11-independent-audit-stack/`, whose layers attempt to *disprove* the claims
  rather than restate them, and `records/`, which keeps the refutations in place.
