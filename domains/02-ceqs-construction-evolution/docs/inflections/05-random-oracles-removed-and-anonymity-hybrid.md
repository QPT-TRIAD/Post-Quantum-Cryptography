# Inflection 5 — the random oracle comes out of the load-bearing theorem, and one hybrid is corrected (v1.2 → v1.3 → v1.4)

**Versions concerned:** v1.3 `docs/qpt-crs-security-proof.md` and v1.4
`docs/collaborative-quorum-proof.md`. v1.2 has **no document in this repository**; it is known only
from v1.3's description of what it left open.
**Date:** 9 September 2026.
**One sentence:** v1.2 had closed the trace adapter only in the classical random-oracle model, v1.3
replaced both remaining quantum-random-oracle dependencies with a pre-sampled trace CRS and a
simulation-extractable NIZK, and v1.4 repaired an anonymity hybrid that v1.3 had asserted more
strongly than multi-sample LWR allows.

## What v1.2 left open

v1.2's outcome is recorded by its successor (`docs/qpt-crs-security-proof.md:14–19`): it closed the
LWR-SCCH trace adapter **only in the classical ROM** and left four quantum issues —

1. quantum LWR/wPRF security;
2. statistical uniqueness under quantum attacks;
3. quantum-accessible topic-base derivation;
4. a QROM-secure simulation-extractable local proof.

Items 1 and 2 are assumptions in any case (see §3.5 of `docs/construction-end-to-end.md`); items 3
and 4 are *architectural*: they exist only because bases and proofs were derived through a random
oracle. v1.3 removes items 3 and 4 from the QROM entirely and states 1 and 2 directly as assumptions
(`docs/qpt-crs-security-proof.md:16–33`).

**v1.2 has no file, ledger, checker or recorded result in this repository.** Its content is reported
here only through v1.3's description, and nothing in this domain rests on it.

## The correction at v1.3 — two architectural changes

**Change 1: topic bases come from a pre-sampled Trace Base CRS, not from a random oracle.**
Instead of deriving bases with a random oracle, all bases for a bounded epoch are sampled as part of
a public trace CRS (`docs/qpt-crs-security-proof.md:21–23`, §3 `:145–221`). Two consequences the
source is explicit about: the CRS is polynomial but may be large (`:223`), and the domain slots are
**bounded**, which the v1.3 theorem lists as assumption 8 (assumption 8 of Theorem 26.1, `:1253`,
listed at `:1263`). A bounded slot budget must halt safely when exhausted rather than silently reuse
a base, which is why the v1.3 checker tests the halt.

**Change 2: the local and outer proofs are simulation-extractable NIZKs in the CRS model, not
Fiat–Shamir/Stern compiled proofs** (`docs/qpt-crs-security-proof.md:25–31`). The justification is
the quoted existence theorem of Jawale–Khurana (§3.6 of `docs/construction-end-to-end.md`). This
removes the QROM dependency of the local proof.

The resulting theorem is **Theorem 26.1** (`:1253–1290`), conditional on nine assumptions: QLWR for
the selected wPRF parameters and sample budget; the statistical uniqueness condition of Theorem 4.1;
polynomial quantum hardness of LWE for the Jawale–Khurana SE-NIZKs; QEUF-CMA security of the
validator vote signature; quantum collision resistance of the 384-bit challenge hash; unique registry
trace keys; canonical encoding; bounded Trace Base CRS domain slots; durable no-double-vote state.
The conclusion is a non-interactive, transferable, sidecar-free hidden-signer quorum certificate
secure against QPT adversaries with exact threshold authorization, public signer-set anonymity
*subject to explicit same-topic link leakage*, public conflict extraction, publicly verifiable blame,
extended no-split counting, honest non-frameability and post-trace separation from the authentication
key — and the theorem uses **no random oracle** (`:1253–1292`).

The source's own boundary statement: v1.3 closes theoretical post-quantum security and existence,
conditionally; it does not close practical compactness (`:1290–1300`).

## The correction at v1.4 — an anonymity hybrid that was too strong

v1.3's anonymity proof informally said that a validator's fresh handle outputs
`t_i, u_{i,1}, …, u_{i,d}` could be replaced by uniform LWR-range values while leaving that
validator's registered trace public key `y_i = F_{s_i}(A)` fixed. v1.4 states the defect plainly
(`docs/collaborative-quorum-proof.md:11–27`):

> "That is stronger than ordinary multi-sample LWR pseudorandomness and was not separately assumed."

**The repair adds no new assumption.** Instead of replacing only the fresh outputs while holding the
registered key fixed, v1.4 replaces the validator's **complete** wPRF sample bundle
`B_i = (t_i, u_{i,1}, …, u_{i,d})` — key and outputs together — so the hybrid is exactly the
multi-sample LWR experiment. The resulting anonymous bound is
`ε_ZK + N·ε_QLWR + ε_HandleColl` with `N = 64` for the reference committee
(`docs/collaborative-quorum-proof.md:86–103`), and the source records that "The main v1.3 theorem
remains structurally unchanged" (`:103`).

v1.4 also removes nested local proofs in collaborative mode, defines the collaborative relation
`R_Collab`, and proves a final conditional theorem **Theorem 27.1** — a QPT-secure, hidden-signer,
sidecar-free, publicly accountable certificate with public conflict extraction of at least `F + 1`
seats, conditional on the v1.3 SCCH assumptions, QEUF-CMA vote signatures, a QPT-secure NIZK for
`R_Collab`, a QPT malicious-secure MPC protecting honest trace witnesses against at most `F` corrupt
validators, and durable no-double-vote state (`:1071–1100`).

What v1.4 records as closed and open is worth quoting in full because it is the honest state of the
hidden-signer track (`:1134–1155`):

- **closed** — v1.3 anonymity-hybrid gap corrected; central-prover knowledge of trace secrets avoided;
  need for public/per-witness local proofs in collaborative mode removed; generic collaborative
  soundness/privacy theorem established conditionally; exact BFT honest-majority condition proved;
  abort safety/liveness distinction made explicit; identifiable-abort termination bound proved
  conditionally.
- **still open** — concrete QPT collaborative MPC implementation and rounds; concrete proof bytes for
  `R_Collab`; compact SCCH handle; `< 32 KiB` end-to-end certificate; strengthened
  TripleRing/TripleRing+ adapter; whether the named proof systems can instantiate the direct
  collaborative relation efficiently.

## Evidence that these were corrections

**v1.3 — `src/ce_qs_qpt_crs_structural_checker.py`** (`results/ce_qs_qpt_crs_structural_checker.txt`):

```
PASS challenge_encoding_injective toy_bits=16
PASS same_key_conflict_extract
EXPECTED-FAIL cross_key_false_trace blocked_by=unique_link_base
PASS setup_sampled_domain_base_immutable
EXPECTED-FAIL domain_budget_exhaustion safe_halt
PASS outer_witness_no_signer_secrets
NOTE: structural toy model only; QLWR/LWE/NIZK/QCR security not executed.
```

Three lines carry the correction evidence.

- `PASS challenge_encoding_injective toy_bits=16` — all 65,536 digests of a 16-bit toy challenge are
  exercised and the encoding is injective. This is the property that, at v1.24, lets the message
  digest itself serve as the field element (Inflection 8). It is the "no extra collision assumption"
  claim in test form.
- `PASS setup_sampled_domain_base_immutable` and `EXPECTED-FAIL domain_budget_exhaustion safe_halt` —
  the two obligations the CRS created. Bases sampled at setup must be immutable (a mutable base
  would let the party who changes it re-derive link bases), and an exhausted domain budget must
  halt, not wrap.
- `EXPECTED-FAIL cross_key_false_trace blocked_by=unique_link_base` — S4 of v1.1 (Inflection 4),
  now blocked by a property available **without a random oracle**. Under v1.2 the same rejection
  rested on `unique_link_base` derived in the ROM; the checker asserts the block on the CRS-derived
  base. This is the clearest before/after pair of the inflection: the same false-trace outcome is
  refused, by the CRS construction rather than by an oracle.

**v1.4 — `src/ce_qs_collaborative_quorum_checker.py`**
(`results/ce_qs_collaborative_quorum_checker.txt`):

```
PASS collaborative_quorum_honest_majority n=4 f=1 q=3
PASS collaborative_quorum_honest_majority n=7 f=2 q=5
PASS collaborative_quorum_honest_majority n=10 f=3 q=7
PASS collector_has_no_trace_secret
PASS one_final_proof_no_local_proof_list
PASS same_hidden_set_vote_handle_binding
PASS identifiable_abort_converges aborts=2 remaining_honest=5
EXPECTED-FAIL non_identifiable_abort_no_progress
PASS reference_64_21_43 honest_in_any_quorum>=22
```

The honest-majority property is checked **exhaustively** for `n = 4, 7, 10` — every quorum against
every adversarial set within the fault bound — and then instantiated at the reference committee:
`reference_64_21_43 honest_in_any_quorum>=22`, i.e. `2q − n = f + 1 = 22` honest seats in every
quorum, which is the density the collaborative prover needs. `non_identifiable_abort_no_progress` is
an `EXPECTED-FAIL` because an abort that cannot be attributed to a specific seat gives the protocol
no way to make progress by replacing it; the source devotes a section to why this is insufficient
(`docs/collaborative-quorum-proof.md:840+`), and the v1.21 review later found the same distinction
resurfacing on the size side (`docs/size-path-resolution.md`).

Both checkers are structural toy models; both say so in their own notes ("QLWR/LWE/NIZK/QCR security
not executed", "no MPC/NIZK/PQ cryptography implemented").

## Why this inflection matters for the current revision

- The v1.24 challenge step (§2.2) is the direct descendant of
  `PASS challenge_encoding_injective`: interpret the digest as a field element bijectively, and the
  separate challenge hash — and its collision assumption — is removed.
- The bounded-domain discipline introduced here is still required: v1.24 states that comparison is
  only permitted between certificates with the same configuration and domain
  (`docs/32kib-contents-contract.md:62`).
- The collaborative prover that v1.4 proved conditionally is the direct ancestor of v1.24's
  `MPC[SelectAndProve_{R_43}]` with 64 participants and at most 21 corrupt
  (`docs/32kib-contents-contract.md:110–124`).

See also: `docs/qpt-crs-security-proof.md` (v1.3, Theorem 26.1),
`docs/collaborative-quorum-proof.md` (v1.4, §0–1 correction and Theorem 27.1), and Inflection 6 for
the turn from theorems to byte budgets.
