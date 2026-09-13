# CE-QS Validation and Continuation
## v0.6 Exact-Aggregator Lifting Proof — Independent Validation + CTRS Concrete-Size Reconnaissance

**Status:** validation record + limited continuation. Not a security proof, not a priority claim, not production cryptography.
**Date:** 2026-09-08
**Scope:** `PQ_CE_QS_exact_aggregator_lifting_proof_v0.6.md` and `PQ_CE_QS_v0.6_CTRS_adapter_obligations.md`, checked against the shipped `PQ_CE_QS_v0.6_SHA256SUMS.txt` and against the real GC-TRS/CTRS paper (web-fetched in full: `eprint.iacr.org/2025/1205.pdf`), the real Feng–Liu–Li–Li–Wu DCC 2021 traceable-ring-signature paper (checked via search/citation record), and one new post-v0.5 source found during this pass, `eprint.iacr.org/2026/974.pdf` (LoTRS, Sept 2026).
**Follows:** `PQ_CE_QS_v0_5_validation_and_continuation.md` (formal proof stack validation + ELBA correction confirmation, previous session), which flagged fetching `eprint.iacr.org/2025/1205` in full as the concrete next task.
**Explicitly does not touch:** `PQAQCEpochBarrier_v0_8.tla`, its `.cfg`, the finite-state checker, or the v0.8 SHA-256 manifest. Target A (deployed, sidecar-based) remains untouched.

---

## 1. Artifact integrity

```
FILE                                                MANIFEST (v0.6 SHA256SUMS)                                          COMPUTED                                                          MATCH
PQ_CE_QS_exact_aggregator_lifting_proof_v0.6.md     a28261164712a6fde87774476ab34bb68f9481797b5586992890b50a33c2dbd7  a28261164712a6fde87774476ab34bb68f9481797b5586992890b50a33c2dbd7  YES
PQ_CE_QS_v0.6_CTRS_adapter_obligations.md           349db4e45a3e552242e91def077ed60a76e054a7bd8d0490cc077ffab0898ec8  349db4e45a3e552242e91def077ed60a76e054a7bd8d0490cc077ffab0898ec8  YES
```

**Result: PASS.** Both files are exactly what the manifest claims (`.` vs `_` in the filename is a naming-convention difference only).

---

## 2. What v0.6 is actually claiming

v0.6's own framing (Section 1) is precise about scope: it does **not** try to prove that CTRS (or any concrete backend) satisfies its new interface. Instead it asks a narrower, well-posed question — *what property must a GC-TRS/CTRS-like backend satisfy so that the v0.5 CET proofs lift unchanged?* — and answers it with a new definition, **CET-liftability** (Section 6, clauses L1–L7), plus a generic lifting theorem (Theorem 8.1) that reduces every v0.5 security property to three black-box facts about the backend (F1 exact witness existence, F2 hidden-witness simulation, F3 public CET binding).

This is a sound way to structure the remaining work: it converts "prove CE-QS is secure over every possible future backend" into "prove backend X satisfies seven checklist items (C1–C7 in the companion obligations file)," which is exactly what the companion checklist document operationalizes.

### 2.1 Spot-check of the proof logic

The lifting argument (Sections 7–15) was read in full rather than sampled.

- **Theorem 8.1's reduction is the right shape.** It correctly identifies that every v0.5 reduction only ever touches the certificate backend through T2 (extraction), T3 (simulation), and T4+L5 (public binding) — never the internal representation of `σ_agg` or the t-out-of-n proof. This is a legitimate black-box argument: if F1–F3 hold, substituting them into the v0.5 hybrid sequences (PRF-to-uniform replacement, anonymity switching, extraction) changes nothing about the *steps*, only the additive error terms. The claimed loss term `ε_Lift = ε_TOP-ext + ε_TOP-zk + ε_TOP-bind` is the correct sum for a black-box substitution of this kind.
- **The same-hidden-set binding theorem (Section 10, Theorem 10.1) is the load-bearing new idea in v0.6, and it is correctly identified as such.** The document explicitly flags (Section 17) that a backend proving only "some ≥q authenticated" and separately "some ≥q tagged" — without tying them to the *same* index variables `i_1,...,i_s` — would not support conflict extraction, because a malicious combiner could attach a stolen or mismatched tag list to a validly-aggregated signature. Requiring L1–L6 to share index variables is exactly what closes this gap, and the accompanying attack sketch (Section 17: "a malicious combiner could attach tags belonging to a different set") is a genuine, non-trivial soundness concern for *any* naive lift, not a strawman. This is good practice: v0.6 identifies the one place a lift is allowed to go wrong and designs the interface specifically to block it.
- **The conflict-extraction bound (Section 12, `|ExtractConflict| ≥ f+1`) is derived correctly** from T2 + L1–L6 + the v0.5 CET identity, and is arithmetically the same `2q−n = f+1` bound established in every prior version (v0.1 through v0.5) — nothing about the lift changes this number, which is correct: the lift is supposed to preserve, not improve or weaken, the quorum-intersection bound.
- **Section 3.2's lattice-native mask adapter is appropriately hedged.** It presents the rounding-PRF form `F^H(u,Γ) = ⌊H(Γ)u⌉_p` as a *qualified candidate*, not a proved one, and explicitly notes "concrete tag length... is not frozen until its parameters are selected." This is the correct level of confidence for a primitive being proposed for adaptation rather than one already proved for this exact use.
- **No overclaiming found in the "proof status" table (Section 21).** It marks the generic lifting theorem "proved conditionally," CTRS's concrete CET-liftability "open," and CTRS's concrete 64/43 byte size "not established from accessible source material" — all of which turn out, on independent fetch (Section 4 below), to have been the accurate and appropriately cautious calls.

**No logical gaps were found in this pass.** The proof-sketch-level review standard used for v0.5 is applied again here; v0.6 meets it.

---

## 3. External check: does the real GC-TRS/CTRS paper support what v0.6 says about it?

The actual paper — Lin, Wang, Wen, Sun, Liang, *Generic Construction of Threshold Ring Signatures and Lattice-based Instantiations*, DCC 2025 / ePrint 2025/1205 — was fetched in full (not just abstract/search-indexed material, closing the gap v0.5 flagged).

| v0.6 claim | Checked against paper | Result |
|---|---|---|
| Final signature contains "one aggregated signature + one t-out-of-n proof" (Sections 16, 22) | Paper's own abstract and Introduction: the construction is built so the final signature "contains only one aggregated signature and one proof," explicitly contrasted with prior schemes that include ≥t partial signatures | **Confirmed exactly.** |
| CTRS achieves logarithmic size "in ring size" specifically, not naively "logarithmic overall" (Section 16: "CTRS further claims logarithmic final signature size in ring size") | Paper's Table 1: CTRS signature size is `t·log n` — logarithmic in `n`, linear in `t`. The paper's own intro states CTRS "has a logarithmic signature size at the expense of a linear factor in t." | **Confirmed exactly, including the caveat v0.6 correctly omitted overclaiming on.** v0.6 never claimed CTRS is logarithmic in `t`; it only ever says "in ring size," which matches. |
| GC-TRS/CTRS structurally matches the `(σ_agg, π_lift)` public syntax the lifting theorem requires (Section 16) | Paper Section 3.2 (`GC-TRS` construction, Algorithm 4): signature is exactly `Σ = (com, z, ω, z′)` — one aggregate commitment/response pair plus one t-out-of-n proof transcript | **Confirmed.** The generic construction really does have the two-part shape v0.6 assumes. |
| The Feng–Liu–Li–Li–Wu DCC 2021 paper is a real, applicable PQ traceable-ring-signature framework with lattice/QROM instantiation (Section 24, source 2) | Springer/dblp/Semantic Scholar records confirm: Feng, Liu, Li, Li, Wu, *Traceable ring signatures: general framework and post-quantum security*, Des. Codes Cryptogr. 89(6), 1111–1145 (2021); builds a general TRS framework instantiated with lattice building blocks and QROM security, following on the same authors' CT-RSA 2020 paper | **Confirmed as a real, correctly attributed source.** The exact rounding-PRF formula `F^H(u,Γ) = ⌊H(Γ)u⌉_p` quoted in v0.6 Section 3.2 was not independently re-derived from the primary text in this pass (only the paper's existence, authorship, and general PRF/lattice/QROM approach were confirmed via secondary sources) — this is a minor completeness gap in this validation, not a red flag, since v0.6 already hedges this adapter as "qualified" rather than proved. |

**No fabricated or misattributed claim was found.** Everything checked resolves in v0.6's favor.

---

## 4. The concrete question v0.5 flagged, now answered — and it cuts against CTRS being the fix

v0.5 explicitly scoped its next task (its Section 4) as: fetch ePrint 2025/1205 in full and extract CTRS's real proof-size formula and any reported concrete numbers, to give the feasibility study real numbers against the 32 KiB gate. v0.6 itself, writing without that fetch, correctly declined to guess a number (Section 19: "the accessible material in this pass did not expose a defensible concrete byte-size table for n=64, q=43. Therefore v0.6 does not claim a CTRS byte estimate.") — this was the right call at the time.

Having now fetched the paper in full, its **Table 2** does report concrete sizes, at ring sizes and thresholds it evaluated (not CE-QS's exact `n=64, q=43`):

| Scheme | n=2¹⁰, t=10 | n=2¹⁰, t=50 | n=2¹⁵, t=10 | n=2²⁰, t=10 |
|---|---|---|---|---|
| CTRS | **1.37 MB** | **5.53 MB** | 1.73 MB | 2.07 MB |
| LTRS | 1.75 MB | 1.87 MB | 41.3 MB | 1636.8 MB |
| Bettaieb et al. (prior SIS-based TRS) | 3.63 MB | 18.11 MB | 42.9 MB | 1263.5 MB |

The paper's own smallest evaluated case — `n=1024, t=10` — already produces a **1.37 MB** CTRS signature. This is orders of magnitude above the project's 32 KiB gate, and the paper does not evaluate anything near CE-QS's much smaller `n=64`, so this is not a direct measurement of the CE-QS operating point — but it is now real evidence, not silence, and it points the wrong way for CTRS as a drop-in compact backend. Independent corroboration for this reading comes from a source outside CE-QS's own document chain: **LoTRS** (Jagganath, Esgin, Steinfeld, Sakzad, Saarinen, Liu, *LoTRS: Practical Post-Quantum Structured Threshold Ring Signatures from Lattices*, ePrint 2026/974 — dated after CE-QS's v0.5 session, found only because this pass searched rather than assumed), which states plainly in its related-work section that "GC-TRS frameworks fall far behind practical expectations with signature sizes around MBs," and reports the GC-TRS(CTRS) row in its own comparison table with asymptotic complexity noted but no usable concrete figure at practical parameters, alongside these actual 2025–2026 state-of-the-art figures for the same problem shape:

| Scheme | Concrete size (N=100, T=50) | Meets 32 KiB gate? |
|---|---|---|
| RFTRS (2025) | 168 KB | No |
| LastRings (2025) | 122 KB | No |
| LoTRS (2026) | 36 KB (35.8 KiB measured) | No — but closest by far |
| LoTRS, smaller params (N=32, T=16) | 25 KB | **Yes** |

This is worth stating plainly for the record: **as of this pass, no scheme found in the literature search — CTRS included — is known to meet CE-QS's 32 KiB gate at anything resembling CE-QS's actual target shape (n=64, q=43, i.e. threshold ≈ 67% of ring size).** The one candidate that gets under 32 KiB anywhere (LoTRS, at the much smaller and much lower-threshold-fraction `N=32,T=16`) uses a structurally different anonymity mechanism — a two-round lattice multisignature plus a *1-out-of-N* selection proof, rather than a *T-out-of-N* proof — specifically because, per its own stated design rationale, "GC-TRS frameworks fall far behind practical expectations" when built on an explicit T-out-of-N proof.

This does not retract anything in v0.6: v0.6's own status table already marked CTRS's concrete size "not established" rather than claiming compactness, so nothing here is a correction to v0.6 the way the ALBA→ELBA fix was a correction to v0.4. It is new information that sharpens the picture v0.6 correctly left open.

---

## 5. A structural implication for the next milestone: LoTRS's design is a candidate the current CE-QS proof stack cannot yet evaluate

This is the substantive continuation this pass adds. v0.6's CET-liftability definition (Section 6, L1–L7) is written specifically against backends of the `(σ_agg, π_lift)` shape, where `π_lift` is a proof of *T-out-of-N membership*. LoTRS is not built that way: it separates the threshold-authenticity relation (enforced algebraically, via a two-round lattice multisignature that only produces a valid aggregate when `T` distinct secret keys contribute) from the anonymity relation (a *1-out-of-N* proof that hides which *column* of a structured `T×N` public-key table was used — not which `T`-subset of an unstructured ring).

Concretely, this means:

- **LoTRS is not directly a CET-liftable backend in v0.6's sense**, because its public syntax is `σ̃ = (π, z̃, r̃, ẽ)` with `π` a 1-out-of-N selection proof, not a T-out-of-N membership proof over the whole ring. v0.6's L1–L7 clauses (and the CTRS adapter obligations checklist's C1–C7) are phrased in terms of a proof that directly certifies `s ≥ q` hidden registry identities; LoTRS's proof instead certifies one hidden *column*, with the threshold guarantee coming from the signing protocol rather than the anonymity proof.
- **This is not necessarily bad news for CE-QS — it may be a better-shaped opportunity than CTRS.** LoTRS's actual measured sizes (25–36 KiB at practical parameters) are the closest anything in the literature search comes to the 32 KiB gate, and its structural idea — *don't make the anonymity proof carry the threshold burden* — is precisely the kind of design insight that could inform a CE-QS-native adapter rather than an off-the-shelf lift. But evaluating it honestly requires **a different, LoTRS-shaped adapter definition**, not a checkbox pass against the existing CTRS-shaped C1–C7 list. Force-fitting LoTRS's `(π, z̃, r̃, ẽ)` syntax into v0.6's `(σ_agg, E, π_lift)` shape without redefining the liftability clauses would either misrepresent LoTRS's actual guarantees or silently drop its efficiency advantage.
- **LoTRS's anonymity notion is also weaker in a specific, quantifiable way that CE-QS would need to evaluate on its own merits, not inherit by analogy.** LoTRS's own paper is explicit that its "structured" anonymity (hiding one column among `N` candidate columns) gives *stronger per-signer* anonymity than an unstructured `(T,N)`-TRS at matched signer-set anonymity, but at the cost of a smaller admissible-set family — a `(20,2000)`-sTRS has only 100 candidate signer sets, versus up to `C(100,20) ≈ 5.4×10²⁰` for an unstructured `(20,100)`-TRS at similar per-signer anonymity. Whether CE-QS's quorum-anonymity requirement (Theorem 15.1's "Quorum privacy" clause) is compatible with this structured-family model, or whether CE-QS's BFT setting (`n=3f+1` validators, not an open ad-hoc ring) actually makes the structured model a *natural* fit rather than a compromise, is an open question this pass raises but does not resolve.

---

## 6. What this pass does and does not change

- **Does not retract or correct any v0.6 claim.** Every claim v0.6 makes about the real literature (Sections 2–3 above) checks out exactly, including the claims v0.6 was careful *not* to make (a CTRS byte estimate).
- **Fills the concrete gap v0.5 flagged**, and the answer is unfavorable to CTRS-as-written: the paper's own smallest reported concrete CTRS figure (1.37 MB at `n=1024,t=10`) and independent 2026 literature both describe GC-TRS-style `T`-out-of-`N` proof backends as landing in the megabyte range in practice, far above the 32 KiB gate, even though CTRS remains asymptotically the best-scaling *published* member of that specific family for very large `n`.
- **Surfaces a new, more promising but structurally different candidate (LoTRS, 2026)** that the current CET-liftability definition cannot evaluate as written, and identifies precisely why (1-out-of-N selection proof + algebraic threshold enforcement, vs. v0.6's T-out-of-N proof shape) plus the specific anonymity-model tradeoff (structured vs. unstructured signer-set families) that any adaptation attempt would need to state honestly rather than inherit by analogy.
- **Leaves every one of v0.6's own listed open items open** (Section 21 of v0.6): the generic lifting theorem is still only "proved conditionally," CTRS's concrete CET-liftability is still "open" (and now, additionally, its concrete compactness looks unlikely rather than merely unestablished), and the QROM CE-QS adapter is still open. This document adds evidence and a new candidate; it closes nothing.

---

## 7. Recommended next concrete task

Two options, not mutually exclusive:

1. **Finish the CTRS question as scoped**, even though the size outlook is now poor: attempt C1–C7 for CTRS at `n=64, q=43` specifically (not `n=1024`), since CTRS's `t·log n` scaling means the ring-size term shrinks sharply at `n=64` (`log₂64=6` vs `log₂1024=10`) even though the paper's own Table 2 doesn't evaluate a ring that small. This is a bounded, well-defined extrapolation task: take the paper's own size formula (not yet extracted in this pass — the paper reports Table 2 numbers but this pass did not locate the underlying closed-form byte formula in the fetched text) and evaluate it at CE-QS's actual parameters before concluding CTRS is ruled out on the strength of a `n=1024` data point alone.
2. **Open a parallel track scoping a LoTRS-shaped adapter definition** — a "1-out-of-N-liftable" analogue of Section 6's CET-liftability, phrased against `(π, z̃, r̃, ẽ)` rather than `(σ_agg, E, π_lift)` — and separately assess whether CE-QS's BFT deployment setting (fixed validator set, not an open ring) makes LoTRS's structured-anonymity model a natural fit or a real weakening of what CE-QS currently promises.

Both are bounded, well-scoped tasks in the same spirit as v0.5's "fetch and check" recommendation — not new conceptual work, but the next honest increment of exactly this kind.

---

## Appendix A — Sources fetched and used in this pass

- `eprint.iacr.org/2025/1205.pdf` — Lin, Wang, Wen, Sun, Liang, *Generic Construction of Threshold Ring Signatures and Lattice-based Instantiations*, DCC 2025 (fetched in full; used for §3, §4, Table 1, Table 2, Algorithm 4, Sections 1.1–1.2).
- `eprint.iacr.org/2026/974.pdf` — Jagganath, Esgin, Steinfeld, Sakzad, Saarinen, Liu, *LoTRS: Practical Post-Quantum Structured Threshold Ring Signatures from Lattices* (fetched in full; used for §4, §5, Table 1, Table 3, Table 4, Section 1.1, "Comparing TRS and sTRS anonymity").
- Springer/dblp/Semantic Scholar bibliographic records — Feng, Liu, Li, Li, Wu, *Traceable ring signatures: general framework and post-quantum security*, DCC 89(6), 2021 (existence, authorship, and general approach confirmed via secondary sources; primary text not fetched in full this pass).

**Scope note:** none of these sources, this document, or the v0.6 files it validates modify or are referenced by `PQAQCEpochBarrier_v0_8.tla`, `PQAQCEpochBarrier_v0_8.cfg`, `pqaqc_finite_state_check_v0_8.py`, `pqaqc_modelcheck_v0_8_results.txt`, `verify_pqaqc_v0_8_artifacts.py`, or `PQ_AQC_v0_8_SHA256SUMS.txt`. The v0.8 Target A release remains exactly as previously audited.
