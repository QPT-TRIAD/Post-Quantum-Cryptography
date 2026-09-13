# Validation status, and the open items

**The hidden-signer profile does not ship.** No part of this domain is a deployed or deployable
hidden-signer certificate: the design has no zero-knowledge backend of its own, no collaborative
prover, and no security theorem that is not a transplant. What ships is a tested design, an executed
ledger, recorded measurements, and this list of what is missing.

---

## 1. What was validated by execution (in this build, on this host)

| Item | Evidence |
|---|---|
| Mode A self-test | `Ran 8 tests … OK` |
| Mode A sizing report | `--report` reproduces the §3 table, including the FAEST-256s/f and FAEST-EM-256s/f reproduction to the byte |
| Mode B v1.46 self-test | `Ran 12 tests … OK` |
| Mode B v1.46 full-size demo | `--demo-256`: 64 registry keys, two 1,584-byte frames, extraction over all 1,849 candidate openings recovered exactly the 22 common seats, every blame re-verified |
| v1.50 self-test | `Ran 5 tests … OK` |
| v1.51 self-test | `Ran 7 tests … OK` (5 v1.50 tests + 2 F5 regressions) |
| v1.47 ledger | self-test 7/7; `--report` reproduces every row, sweep and comparison |
| v1.48 toy prover | self-test 7/7; `--run` verified both frames, extracted 22, measured proof **6,696 B** vs formula **6,924 B** |
| C provers ×3 | compile clean, `--vectors` identical on all three, reduced smoke run verified / tamper-rejected / extracted 22 |
| C prover, production parameters | one run at b = 20, τ = 11, w_g = 16, ρ = 4,096: proof **29,100 B**, frame **30,684 B**, fits 32 KiB, both frames verified, tamper rejected, 22 seats — the §8 size table of `mode-b-security.md` reproduced to the byte (236.84 s wall) |
| ASan+LSan (gcc, reduced) | leaks only; 9 records; no `verify()` frame; no UBSan diagnostic |
| Property layer (audit stack, re-run here) | Mode B property module **16 passed**; hash-signature property module **fails at collection** — see §4 |

Every command, host and observed result is in [../VERIFICATION.md](../VERIFICATION.md), with verdicts
and, for everything not run, the reason.

## 2. The essential gap

**No collaborative prover exists.** The certificate requires a party that learns all 43 openings, and
whoever holds an opening can frame that seat, so the scheme is a **trusted-aggregator** design: its
theorems hold under A-Prove, which the security document calls essential rather than technical. No
protocol was found or built for the honest-majority (≤ 21 of 64) setting, and VOLE-in-the-head
resists splitting. This alone is enough to say the profile does not ship. See
[collaborative-prover.md](collaborative-prover.md).

## 3. Validation gaps in what is shipped

1. **Theorem 3 is a transplant, not a re-derivation** — FAEST v2 Lemma 9.39, "not re-derived line by
   line for Π_B". Its numerical consequence (τ·b + w_g ≥ 230) is used; the proof is borrowed.
2. **The DFMS-modelled R3 in the ledger omits the DFM20 multi-round loss.** Only the alternative row
   computed from the FAEST-9.39 form carries it. The default total must not be read as including it.
3. **Non-standard assumptions** A-F1, A-F2, A-P: evidence is attack-based (XL/hybrid and SAT), not a
   reduction to a standard problem. A-P is decisional and only informally implied by A-F1.
4. **No dedicated cryptanalysis** of "expanding random MQ + power handle". The estimates use the
   semi-regularity heuristic, explicitly "heuristic, not a theorem" in the source; the sparse-vs-dense
   comparison the domain attempted is **inconclusive by design**.
5. **The margin is thin: 7.7 bits** at the production setting (2^20, τ = 11, w_g = 16) under the form
   of R3 that includes the multi-round loss. Elsewhere in the programme the fitted-exponent
   extrapolations carry ±4–38 bits of error, so the 128-bit conclusions rest on the reductions, not on
   the fits.
6. **The selector constraint is a parity check, not a weight-1 enforcement** (see item 6 in §5).
7. **No production-parameter run in the source rounds.** The 30,684-byte frame in
   `mode-b-security.md` §8 was a size-formula table entry, and the rounds that produced these
   documents did not execute it. This build executed it once (see §1) and it agreed to the byte;
   that single plain-build run is a reproduction of a size table, not a security result, and it was
   not repeated under a sanitizer.
8. **The sanitizer evidence is a reduced gcc run**, not the recorded clang production run; it shows
   leaks and their absence inside `verify()`, not memory safety in general.

## 4. The property layer, stated exactly (record A28)

The programme's property-layer re-run (recorded as entry **A28** in the repository's records) has two
outcomes, and both must be read as stated:

- **Mode B property module: 16 passed.** Re-run here to confirm: `16 passed in 268.22s` (recorded
  baseline earlier the same day: 90.82 s — host load).
- **Hash-signature property module: fails at collection, 0 tests executed** — by design of the F3
  fix. The module builds an `LmsPrivate` with a mixed m ≠ n typecode pair at import, which F3 now
  refuses (`ValueError: F3: LMS m and LM-OTS n must match`). Re-run here to confirm: the same
  collection error.

Consequently the fix-stage record's **"16/16" reading is withdrawn** — the hash-signature suite
executed nothing, and its count is supported neither by the archived log nor by a re-run. The F2/F4
fixes themselves stay regression-tested by their own self-test. The property module must build only
approved n = m pairs (or assert the F3 refusal) before any count can be restated.

## 5. Open items (domain level)

1. **No collaborative prover (A-Prove)** — the essential gap; see §2.
2. **Theorem 3 is a transplant**; the DFMS-modelled ledger R3 omits the multi-round loss; only the
   FAEST-9.39 form carries it.
3. **Non-standard assumptions A-F1, A-F2, A-P**, with attack-based evidence only.
4. **No dedicated cryptanalysis** of the key map + handle composition; the semi-regularity heuristic
   is the basis of every algebraic row; the domain's own sparse-vs-dense experiment is inconclusive
   by design.
5. **Thin margin (7.7 bits)** at the production setting.
6. **Selector constraint is only a parity check (reviewer probe).** The relation commits a 64-bit
   selector and one constraint `Σ bᵢ + 1 = 0` over F₂ — parity, not weight = 1. Corrupt registry keys
   `Y[k] = F(x*) ⊕ Y[a₁] ⊕ Y[a₂]` with a **weight-3 selector** `{k, a₁, a₂}` were accepted by the toy
   prover (0 unsatisfied constraints, `verify = True`), and the public pair search then named only the
   two honest anchors, not the crafted seats. Label: **simulation (reviewer probe)**. This is a gap
   in the stated relation R_B, **not** a demonstrated forgery of an accepted certificate against an
   honest verifier (the toy backend reports `qualified = False`). Distinctness and soundness therefore
   rest on binding of F plus the pair-search filter, not on the selector constraint; whether a 1-hot
   enforcement — or an argument that parity suffices given binding — is needed for R_B soundness is
   **open** and must be resolved before any formal claim.
7. **Registry cost and domain limits.** 102 B per seat-domain (128 B at E = 512); 6.7 MB per seat for
   2^16 domains; the framing row R1 fails above 2^24 domains per epoch.
8. **Operational premise A27 (records).** A state rollback can turn an honest seat into a
   double-signer and push the corruption count from ≤ 21 to ≥ 22; the safety and threshold claims hold
   only for seats whose signer state is monotone. The live rollback re-run is **pending**, and the
   node material is out of scope for copying.

**Second reviewer probe, carried in as required:** "duplicate registration rejected" in the v1.46
tests is a **toy-width artefact** — it follows from the test's registry width, not from a production
registry property, and must not be cited as registry robustness.

## 6. Theory entries that are incomplete in the source

The programme's theory index marks every D8 row's citation status. Twelve entries are recorded for
this domain; the ones marked **incomplete in source** (names, ePrint identifiers or lemma numbers
without full bibliographic entries) are: D8-01 (FAEST v2 Lemmas 9.34–9.39 and [AHJ+23] Lemma 1),
D8-02 (QuickSilver), D8-03 (semi-regular degree of regularity / XL — heuristic), D8-05 (GHHM Theorem
3), D8-06 (DFMS22 Theorem 4.2, binding row only), D8-09 (MQOM2/KuMQuat, Ding–Yang, FAEST v2 size
formula, QuickSilver, DFMS22, GHHM21), and D8-10 (Rabin irreducibility — standard, completed here by
name). D8-04 (HRS16, ePrint 2015/1256) and D8-07 (linearized polynomials) carry citations; D8-07 is
the project's own elementary theorem-with-proof. D8-11 (the 123.3 < 128 finding) and D8-12 (recorded
size/table results) are project results.

## 7. Non-claims

- No compact hidden-signer certificate is produced by any file in this domain.
- No zero-knowledge backend of this domain's own exists; the structure-only marker in the Python
  modes is **not** a proof backend, and the toy prover's `qualified` flag is `False`.
- No security theorem is claimed for Mode A, and none that is not a transplant for Mode B.
- The toy-width demonstration is not a production result, and the one production-parameter run in §1
  reproduces a size table — it is not evidence of security, and it is not a sanitizer run.
- The withdrawn "16/16" property-layer figure is not restated.
