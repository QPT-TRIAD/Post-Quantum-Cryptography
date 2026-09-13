# 06 — QPT-128 security target

This domain is the programme's security target, stated once and evaluated exactly. It defines what
"QPT-128" means for a quantum adversary, proves two lemmas about that definition, refutes the older
reading the programme had been using, and carries the ledger that decides which constructions meet
the target.

Two files carry the domain. `src/qpt128_finalization.py` is the exact-arithmetic evidence: a
single-file Python program (standard library only) that defines the target, computes every bound as
an exact rational number, and emits a JSON verdict report. `docs/qpt128-finalization.md` is the
human-readable closure of the question, written against that program. The remaining documents in
`docs/` take the theory and the ledger apart for a reader who has not seen the project.

---

## 1. The problem

A quorum certificate must survive a quantum adversary. Saying so precisely turned out to be the
hard part, and the project had been saying it in three different ways (`docs/qpt128-finalization.md` §2):

| Id | Statement as recorded | Status here |
|---|---|---|
| **D1** | `G(A) < 2^128 ⟹ Pr[Win(A)] < 1/3` — a work factor on the adversary's gate count `G(A)` | adopted as the target |
| **D2** | `Pr[Win(A)] ≤ G(A)·2^−130` for every adversary `A` | the rigorous strengthening used here; D2 implies D1 |
| **D3** | `Pr[Win(A)] < 2^−128` for every QPT adversary | **refuted** by Lemma L1 |

`A` is a quantum circuit, `G(A)` its gate count, `Win(A)` the event that it breaks the scheme. When
an oracle stands for a concrete hash, one query costs `g_H` gates — at least the T-count of that
hash's circuit — so a query count and a gate count are different units, and the target is stated in
the second.

**Why gates rather than queries.** Counting queries assumes a query is free. It is not: one 256-bit
key falls with probability ≥ 1/3 after `3·2^125 < 2^127` Grover iterations, which is far below the
`2^128` budget, so a query-counted D1 fails for every component whose secret is 256 bits (Lemma L2,
below). Charging each query its circuit is exactly how NIST category 5 — "resources comparable to
AES-256 key search" — is defined, and it is the reading the programme adopted.

**Why D3 had to be dropped.** Lemma L1 shows `Pr[Win] < 2^−128` for *every* QPT adversary is
unattainable for anything with a 256-bit secret: `2^63` Grover iterations already exceed `2^−128`.
The refutation is recorded permanently in `records/failed-assumptions.md` entry Q1 (hypothesis
"`Adv < 2^-128 for every QPT adversary` is achievable" → "Refuted (Lemma L1)" → fix "QPT-128
redefined as gate work factor D1/D2").

---

## 2. What is in this directory

| Path | What it is |
|---|---|
| `src/qpt128_finalization.py` | the evidence file: target definitions, lemmas L1–L5, the seven envelope functions, the five scenario families, 19 unit tests, and the `--report` JSON |
| `docs/qpt128-finalization.md` | the recorded closure document: result, verdict table, what was read, target and lemmas, constants with sources, Theorem A (public signers), Theorem B (hidden signers), the compat-mode withdrawal, 14 corrections to the record, reproduction commands, non-claims |
| `docs/theory.md` | every borrowed result, its statement *as used here*, which part is used and which is not, and the citation as the source gives it |
| `docs/ledger.md` | how the gate budget is composed, how each bound enters, the union-bound rule and its limits, and the exact-arithmetic method |
| `results/qpt128_report.json` | the `--report` output, regenerated in this repository |
| `results/ledger-independent-check.txt` | an independent exact-arithmetic recomputation of the headline rows, run in this repository |
| `results/ledger-independent-check.py` | the script that produces it: loads the checker by path and recomputes the totals, margins, minimum repetition counts and the legacy-constant comparison by its own route |
| `VERIFICATION.md` | the required table: each item, its command, the recorded result, the observed result and the verdict |

Everything is invoked with one command set, and one of the three options must be given: a bare
invocation prints its usage message and exits 2 **by design** (see `VERIFICATION.md`).

```
python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --self-test
python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --report
python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --explain
```

**Every verdict is an exact `Fraction` comparison.** The decimal logarithms in the report and in the
document's tables are computed in 60-digit decimal arithmetic, rounded to 3 or 9 decimal places, and
are display only. The clearest example is Lemma L1's own row: the report prints
`"success_lower_bound_log2": −128.0`, because the true value is `2^−128` plus a term too small to
show at 9 decimals — while the verdict beside it, `"exceeds_two_pow_minus_128": true`, is the strict
exact comparison. The log2 figure is not evidence; the comparison is.

---

## 3. What the domain establishes

### 3.1 Lemmas

| Lemma | Statement | Label |
|---|---|---|
| **L1** | `2^63` Grover iterations against a uniformly random 256-bit secret succeed with probability > `2^−128`; so D3 is unattainable | theorem with proof, checked exactly (test 01); scales to 512 bits at `2^127` iterations (test 02) |
| **L2** | `3·2^125 (< 2^127)` iterations reach success ≥ 1/3 against one 256-bit key, `3·2^122` against 64 keys; so query-counted D1 fails and gate charging is required | theorem with proof (test 03) |
| **L3** | if `Win ⊆ ∪ Bad_i` and `Pr[Bad_i] ≤ ρ_i(G)` then `Pr[Win] ≤ Σ ρ_i(G)`; if `Σ_i max_{1≤G≤2^128} ρ_i(G)/G ≤ 2^−130` then D2 holds, and D2 implies D1 | theorem with proof (union bound; test 05) |
| **L4** | for `ρ` a polynomial in `q = G/g` with non-negative coefficients, `ρ(G/g)/G` is convex in `G`, so its maximum on `[1, 2^128]` is at an endpoint; caps break convexity and are applied only to the D1 probability | theorem with proof, elementary (tests 06, 19); **the convexity claim is stated, not written out** |
| **L5** | DFMS's QROM online extractor runs in `O(q²)·poly` time, so a reduction that uses an extracted witness runs in `t_B ≈ G + a·q²·g_sim`, and D2 then needs `n ≥ (2e−1)·128 + 130 + log₂c + e·log₂(a·g_sim) − 2e·log₂g_H − e·log₂g_F` | **model-or-ledger estimate** — the source's own word is "roughly"; the checker evaluates the exact rows instead |

The proof system that gives L1 and L2 their arithmetic is the Grover success law
`sin²((2j+1)θ)` with `sin θ = 2^−128`, together with `sin y ≥ y − y³/6`; `docs/theory.md` §1 gives
its statement as used, its provenance and the citation status.

### 3.2 Theorems

- **Theorem A — public signer set (profile B0).** Accountability holds with no probability at all:
  two 43-of-64 certificates share at least 22 signers, and every one of them is named by the two
  certificates themselves. Non-frameability and safety reduce to the EUF-CMA security of the
  category-5 signature, tightly and linearly (`docs/qpt128-finalization.md` §4).
- **Theorem B — hidden signer set (profile B1, "Mode S").** Safety, non-frameability and forensic
  completeness are bounded by sums of bad events E1–E5, in the QROM and under the named assumptions
  listed in §5 of the document.

### 3.3 Ledger verdicts (gate units unless stated)

| Instantiation | D2 margin | D1 | Source |
|---|---:|---|---|
| **B0**, public signers, signature in the clear | **+23.0 bits** | PASS, `Pr ≤ 2^−25` at `2^128` gates | `results/qpt128_report.json` |
| **B1 Mode S**, 1024-bit registry keys, rigorous extraction overhead | **+29.4 bits** | PASS, `Pr ≤ 2^−41.3` | same |
| B1 Mode S, attack-cost accounting | +29.4 (gates), +3.3 (queries) | PASS | same |
| B1 Mode S, 512-bit registry keys, rigorous | −141.2 | FAIL | same |
| B1 Mode S, rigorous, **query** units | −40.0 | FAIL | same |
| Compat mode: category-5 signature inside an extractable proof | −185.0 | FAIL | same |
| B0, **query** units | −11.0 | FAIL | same |
| Legacy D3 ledger | — | refuted by L1 | same |

The extraction rows are given a share ≤ `2^−133`; the minimum repetition counts are **r = 553** in
gate units and **r = 640** in query units (exact binary search in the checker, test 09), and the
report uses the larger, `r = 640`.

---

## 4. Proven, assumed, refuted — stated plainly

**Complete proofs (exact rational checks in the checker).** Lemmas L1, L2, L3 and the quorum
arithmetic `2·43 − 64 = 22`, `64 = 3·21 + 1`, `C(64,2) = 2016`. L4 is a theorem with an elementary
proof, but the source states the convexity claim without writing the proof out; that is a gap in the
exposition, not in the arithmetic the checker performs.

**Sketches.** Lemma L5 is a model-or-ledger estimate ("roughly"), not a derivation. Theorem A's and
Theorem B's proofs are given in outline with their loss terms accounted; Theorem B is a theorem
*about a construction* and is conditional on named assumptions.

**Assumed.** Theorem A rests on one named assumption: the chosen category-5 signature is EUF-CMA at
category-5 generic strength. Theorem B rests on A-QROM (SHAKE256 modelled as a quantum random
oracle — a model, since a fixed hash is never indistinguishable from a random oracle), A-F (generic
bounds for the single-block SHAKE256 credential functions), A-cost (≥ `2^18` T gates per oracle
evaluation), A-γ, A-MPC (an ideal collaborative prover) and A-protocol. The rows for E6–E8 and for
canonical encoding/rollback are **set to zero** under model premises: they are assumptions, not
proved terms, and the ledger's arithmetic treats them as zero.

**Refuted or withdrawn, and where that is recorded.**

- **D3** (`Pr < 2^−128` for every QPT adversary) is refuted by Lemma L1 — `docs/qpt128-finalization.md`
  §2 and §7 item 1, and `records/failed-assumptions.md` entry Q1.
- **Compat mode** (ML-DSA-87 or SLH-DSA-SHAKE-256s signatures inside an extractable proof) is
  withdrawn: the conversion is correct, but `ε_sig` must be evaluated at the reduction's running
  time, which includes the `O(q²)` extractor, and the row then fails by 185 bits in gate units
  (`docs/qpt128-finalization.md` §6, §7 item 5).
- The constant `12(q+154)³/2^n`, used in the research trail, has **no source**; the checker keeps it
  only to measure the discrepancy against the published bound (§3 of the document, test 14).
- Fourteen further corrections to the project record are listed in §7 of the document.

**What is missing for acceptance as a standard proof.** The constants borrowed from the literature
are used as the sources state them but have not been re-derived here; the named assumptions above
are not theorems; the model-premise rows are set to zero rather than proved; L5 is approximate; and
the hidden-signer route (B1) has no proof system that fits the 32 KiB certificate budget (that
negative result belongs to `domains/07-compact-certificate-b0`). A fuller list is in §15 of
`docs/theory.md` and §9 of `docs/ledger.md`.

---

## 5. How to read this domain

1. `docs/qpt128-finalization.md` — the source document; §0 is the result table.
2. `docs/theory.md` — the borrowed theory, entry by entry, with the part that is used and the part
   that is not.
3. `docs/ledger.md` — the machinery: units, constants, envelopes, the endpoint rule, the union
   bound, the extractor charge, and the exact-arithmetic method.
4. `VERIFICATION.md` — what was re-run here and what it returned, including the one difference from
   the recorded output.

**Where to go next.** The certificate itself, its size gate and the impossibility result for hidden
signers under 32 KiB are in `domains/07-compact-certificate-b0`. The extraction theory this ledger
charges for is in `domains/05-extraction-and-signature-reductions`. The signature reductions the
compat-mode withdrawal refers to are there too. The games and the attack lab that test the
construction are in `domains/09-security-games-and-attack-lab`, and the refutation register is
`records/failed-assumptions.md`.
