# CE-QS v0.4 Validation and Corrections
## Research-Synthesis Finalization + Source Qualification Ledger

**Status:** validation/audit record only — no new construction work, no continuation this pass.
**Date:** 2026-09-08
**Scope:** `PQ_CE_QS_research_synthesis_final_v0.4.md` and `PQ_CE_QS_v0.4_source_qualification_ledger.md`, checked against the shipped `PQ_CE_QS_v0.4_SHA256SUMS.txt` and against the real cited literature (web search).

---

## 1. Artifact integrity

Both files were re-hashed and compared to the shipped manifest.

```
FILE                                              MANIFEST                                                          COMPUTED                                                          MATCH
PQ_CE_QS_research_synthesis_final_v0.4.md         852c2bca5d0a4aac7f264c68722ae88144498a716a545e5a6c4a2b8b21f3d97c  852c2bca5d0a4aac7f264c68722ae88144498a716a545e5a6c4a2b8b21f3d97c  YES
PQ_CE_QS_v0.4_source_qualification_ledger.md      c36badd1d2584c1774631c6f9993158c51382dc82ee1584dabcf4bfeb997390f  c36badd1d2584c1774631c6f9993158c51382dc82ee1584dabcf4bfeb997390f  YES
```

**Result: PASS.** Both files are exactly what the manifest claims.

---

## 2. Internal consistency

### 2.1 Math

- `|S0∩S1| ≥ 2q−n = f+1` (Section 10): for `n=3f+1, q=2f+1`, `2q−n = 2(2f+1)−(3f+1) = f+1`. **Correct**, and consistent with every earlier v0.1–v0.3 document.
- The central new claim of v0.4 — that any positive ALBA aggregation slack (`Δ_ALBA > 0`) makes the succinct aggregate incompatible with Byzantine-independent 43-of-64 liveness (Section 12) — rests on `q = n−f = 43`. Checking the identity generally: `q = 2f+1` and `n−f = (3f+1)−f = 2f+1`, so `q = n−f` **exactly**, with zero slack, for this parameterization. The claim is arithmetically sound: since the honest-validator floor and the certificate threshold are numerically identical, *any* required slack above `q` demands more contributions than the honest set can ever supply. This is a genuine and correctly derived constraint, not an overstatement.

### 2.2 Cross-references

Section 22's game list points to definitions elsewhere in the same document:

| Reference | Target section | Target section title | Match? |
|---|---|---|---|
| G3 — quorum anonymity | Section 7 | "Quorum anonymity — formal target finalized" | Yes |
| G7 — trace soundness | Section 8 | "Trace soundness — formal target finalized" | Yes |
| G8 — non-frameability | Section 9 | "Non-frameability — formal target finalized" | Yes |
| G11 — QROM | Section 19 | "QROM status — finalized honestly" | Yes |

All four resolve correctly.

### 2.3 Synthesis vs. ledger

The standalone ledger's "Load-bearing?" and "Main caveat" columns were checked against the synthesis document's Section 2 (Tier policy) and Section 25 (final source decision matrix) row by row. **No contradictions found** — every source's tier/status and caveat in the ledger matches the synthesis document's own characterization (e.g. ALBA is "Yes / gap conflicts with exact 43-of-64 BFT liveness" in the ledger and "load-bearing liveness constraint" in Section 25; TripleRing+ is "No / not yet available in final form" in the ledger and "accepted/forthcoming, not load-bearing" in Section 25; TAPS is "Definitions / uses tracing key" in the ledger and "definition reference only" in Section 25). The two documents were clearly generated to agree, and they do.

**Result: PASS**, no internal corrections needed.

---

## 3. External fact-checking (Tier A sources — the ones marked "can be load-bearing")

Every Tier A citation in Section 2 was checked against real bibliographic records.

| Citation as given | Checked against | Result |
|---|---|---|
| Chiang, Damgård, Duro, Engan, Kolby, Scholl — CCS 2025, DOI 10.1145/3719027.3744854 | ACM DL, dblp, ePrint 2025/113 | **Confirmed exactly** — authors, venue, DOI, and page range (4664–4678) all correct. |
| Avitabile, Botta, Fiore — Tetris/DAPT, ESORICS 2025, ePrint 2025/730 | ePrint, dblp, Springer LNCS 16054 | **Confirmed exactly.** |
| Chaidos, Kiayias, Reyzin, Zinovyev — ALBA, EUROCRYPT 2024 | ACM DL reference list, Springer, dblp | **Confirmed exactly** (LNCS 14654, pp. 55–84). |
| Baum et al. — "Shorter, Tighter, FAESTer," CRYPTO 2025 | Author's own publication page (Peter Scholl) | **Confirmed** — full author list and venue match. |
| Lin, Wang, Wen, Sun, Liang — GC-TRS/CTRS, Designs, Codes and Cryptography 2025 | Springer, ePrint 2025/1205 | **Confirmed** — author order and venue match; the paper does introduce GC-TRS with LTRS and CTRS instantiations, CTRS being logarithmic in ring size, exactly as Section 15.1 describes. |
| `jachiang/PQ-Threshold-Ring-Sigs-from-VOLEitH` repository | GitHub | **Confirmed to exist**, with a README describing AES/AES-EM ring signature builds and a `config.h.in` ring-size parameter — consistent with, though not exhaustive confirmation of, every specific filename listed in Section 16. |

**Result: every Tier A source checked is a real, accurately attributed publication.** No fabricated or misattributed citations were found among the load-bearing sources.

---

## 4. Correction: "ALBA" vs. "ELBA" (Tier A, load-bearing — this one matters)

This is the one substantive correction from this pass.

The actual CCS 2025 paper (Chiang et al.) does **not** apply the original ALBA primitive directly. Its own abstract and text state that standard ALBA requires **fully unique signatures**, which are not available from their PQ threshold-ring construction. To work around this, the paper defines a new, distinct primitive it names **ELBA (Expanded ALBA)**, built specifically for signatures that are only *partially* unique — i.e., unique on one tag component rather than the whole signature. The deterministic key-binding tags are exactly what supplies that partial uniqueness.

`PQ_CE_QS_research_synthesis_final_v0.4.md` refers to this aggregation mechanism as **"ALBA"** throughout — Sections 1, 12, 13, 14, 25, and the primary-references list — and never names ELBA. The source ledger does the same ("ALBA aggregation is approximate and may require >t inputs").

**Why this is worth correcting rather than treating as a harmless simplification:**

1. It's not a paraphrase of the same idea — ELBA is a separate, explicitly defined primitive in the source paper, introduced *because* plain ALBA doesn't apply to this setting. Citing "ALBA" for a scheme that actually uses ELBA is citing the wrong (if closely related) object.
2. **It cuts in CE-QS's favor once corrected**, so this isn't a case of the document overclaiming — if anything, v0.4 slightly undersold its own fit. ELBA's defining feature is that it works from tags that are unique-per-key rather than whole-signature uniqueness. CET tags are exactly that shape: one deterministic, key-bound 256-bit tag per signer. This is a stronger, more specific alignment between CE-QS's own design and the base paper's aggregation primitive than "ALBA" (unqualified) suggests — it's not a coincidental reuse of a general tool, it's the same partial-uniqueness pattern the base paper built ELBA around.
3. The slack-requirement finding in Section 12 (`Δ_ALBA > 0`) is unaffected by this correction — the CCS 2025 paper's own text confirms the aggregator must hold more than the proven threshold count regardless of which name is used for the aggregation primitive, so v0.4's central BFT-feasibility conclusion (Sections 12–13, 29) stands as stated.

**Recommended correction, if this document is revised:** replace "ALBA" with "ELBA (Expanded ALBA)" in Sections 1, 12, 13, 14, 25, and the source ledger's Chiang-et-al. row, with one line noting ELBA's relationship to the original ALBA primitive (Chaidos et al.) the way Section 12 already explains the slack requirement. The Tier A entry for Chaidos, Kiayias, Reyzin, Zinovyev remains correctly cited as the source of the underlying ALBA concept — that citation itself needs no change, only the description of how the CCS 2025 paper uses it.

---

## 5. Items checked but not independently confirmed

Time-boxed to Tier A (load-bearing) sources per Section 3. Two Tier-B/fallback citations were not independently verified and should be treated as unverified rather than confirmed:

- **"Rejection-free lattice threshold ring signatures, CSI 2025"** (ledger, Section 15.2 of synthesis) — no matching venue was located in this pass. "CSI" is not a venue abbreviation this search recognized with confidence. This should be re-checked before the fallback-branch citation is treated as load-bearing for anything.
- **"Forward-secure PQ ring signatures, TCS 2026 and related"** (ledger) — plausible (Theoretical Computer Science does publish forward-secure/ring-signature work, and a 2026 volume is not yet fully indexed), but not independently confirmed in this pass.

Neither of these is marked load-bearing in the synthesis document (both are "optional"/"fallback"), so this doesn't affect the finalized construction claims — it's flagged for completeness.

---

## 6. Bottom line

- **Artifact integrity: PASS.** Both files match the shipped SHA-256 manifest exactly.
- **Internal consistency: PASS.** The math (quorum-intersection bound, zero-ALBA-slack-tolerance argument), the cross-section references, and the agreement between the synthesis document and the standalone source ledger all check out with no contradictions.
- **External citation accuracy: PASS for all six Tier A sources checked**, with **one correction**: the CCS 2025 base paper's aggregation primitive is specifically **ELBA (Expanded ALBA)**, not the unqualified ALBA primitive the document names throughout. This is a citation-precision fix, not a retraction — correcting it slightly strengthens, not weakens, the fit argument between CET's tag design and the base scheme's aggregation layer, and it does not change the Section 12 BFT-feasibility conclusion, which is independently confirmed by the base paper's own stated requirement that the aggregator hold more than the proven threshold count.

No changes are needed to the v0.8 Target A artifacts, and this pass does not add any new CE-QS construction or implementation work — per the request, this is validation and correction only.
