# Domain 07 — compact certificate (profile B0)

**What this domain attacks.** CE-QS authorizes decisions with 43 of 64 committee seats (quorum 43,
fault bound 21). A *certificate* is the portable artifact those 43 seats produce. This domain asks
whether such a certificate can be a **single object of at most 32,768 bytes** that a verifier
holding only the authenticated 64-seat registry can check **alone** — with no sidecar, no external
leaf list, no transcript, and **no secret opener**, and from which **two conflicting certificates
publicly expose at least 22 seats that authorized both**. The last property exists because any two
43-subsets of a 64-set share at least `43 + 43 − 64 = 22` seats; the work is in making that
intersection *publicly computable* from the two certificates alone.

**The answer this domain records.** Profile **B0** (suite `0x44B0`) meets that requirement with real
post-quantum signatures: a 216-byte header-plus-bitmap followed by 43 fixed-width signature slots,
measured at **11,396 bytes** with OV-V-pkc (260-byte signatures) and **30,918 bytes** with the
OV-V-pkc‖SNOVA_29_6_5 hybrid (714 bytes) — both inside the 32,768-byte bound, both verified and
conflict-extracted in a full run. Profile **B1** / "Mode S" (suite `0x44B1`) adds hidden signers and
does **not** meet the bound: **no qualified proof backend exists in this repository**, and `verify_b1`
never reports an authorization. B0 publishes its signer bitmap, so it does not hide signers either.
That gap is quantified here (Theorem C) and is the domain's main open item.

## Read in this order

| # | File | What it gives you |
|---|---|---|
| 1 | `README.md` (this file) | problem, answer, file map, what is measured vs proven |
| 2 | `docs/construction.md` | the construction end to end: frame layout, extraction, blame, sizes, the two profiles, the measured table with its provenance, Theorem C and its status |
| 3 | `docs/b0-wire-spec.md` | the **normative** wire specification: 216-byte header+bitmap, 43 slots, suite ids, registry authentication, vectors, and the implementer's gap list |
| 4 | `docs/sidecar-free-finalization.md` | the closure document: the seven requirements, the measurements, Theorem C in full, rejected designs, recommendation, falsification criterion |
| 5 | `src/sidecar_free_certificate.py` | the executable reference (39 tests, `--self-test`, `--report`, `--real-demo`) |
| 6 | `results/` | the raw outputs of this build's re-runs, plus the A.10/F6 probe |
| 7 | `VERIFICATION.md` | every command re-run, its recorded baseline, its observed result and verdict |

`vectors/` is **not** in this directory. The map assigns the independent B0 implementation, the 900
generated vectors and the check results to the independent-audit-stack domain
(`domains/11-independent-audit-stack/independent-b0/`: `b0_indep.py`, `gen_b0_vectors.py`,
`check_vectors.py`, `b0_vectors.json`, `SPEC_GAPS.md`, `INDEPENDENT_RESULTS.md`,
`independent_results.json`). This domain refers to them and does not duplicate them. Everything the
map does place here is under `docs/` and `src/`.

## Files

```
docs/construction.md              this domain's own exposition (written for this repository)
docs/b0-wire-spec.md              copy of the normative v1.44 specification, paths rewritten
docs/sidecar-free-finalization.md copy of the v1.44 closure document, paths rewritten
src/sidecar_free_certificate.py   copy of the v1.44 reference module, paths rewritten
results/self-test.txt             raw output of --self-test
results/report.json               raw output of --report
results/real-demo.json            raw output of --real-demo (in the pinned environment)
results/real-demo-unavailable.json  raw output of --real-demo without that environment (documented behaviour)
results/probe_a10_f6.py           the build-time probe for findings A.10 and F6
results/probe_a10_f6.txt          its raw output
results/README.md                 provenance of every file in results/
VERIFICATION.md                   recorded vs observed for every command
```

The three copied files carry the source's content with relative paths substituted; their digests
therefore differ from the source-tree digests, which `VERIFICATION.md` lists side by side.

## The measured size table

Frame size is `216 + 43·W` for a signature width `W`: `208` bytes of header (`magic`, `version`,
`suite`, `cfg`, `domain`, `message`, `count`, `width`, `payload_len`), `8` bytes of signer bitmap,
then 43 slots. The gate is `W ≤ (32,768 − 216) // 43 = 757` (757 → 32,767 bytes fits; 758 → 32,810
does not).

| Scheme (claimed category) | Signature B | Public key B | Frame B | Outcome |
|---|---:|---:|---:|---|
| **OV-V-pkc** (5) | 260 | 446,992 | **11,396** | verified, 22 seats extracted, blame ok, tamper rejected |
| SNOVA_29_6_5 (5) | 454 | 2,716 | 19,738 | verified, 22 extracted, blame ok, tamper rejected |
| SNOVA_60_10_4 (5) | 576 | 8,016 | 24,984 | verified, 22 extracted, blame ok, tamper rejected |
| **OV-V-pkc‖SNOVA_29_6_5** (5) | 714 | 449,712 | **30,918** | verified, 22 extracted, blame ok, tamper rejected |
| MAYO-5 (5) | 964 | 5,554 | 41,668 | rejected as oversize |
| ML-DSA-87 (5) | 4,627 | 2,592 | 199,177 | rejected as oversize |
| Falcon-padded-512 (1) | 666 | 897 | 28,854 | verified, but **category 1 — does not meet QPT-128** |

Arithmetic, exactly as the tests assert it: `216 + 43·260 = 216 + 11,180 = 11,396` and
`216 + 43·714 = 216 + 30,702 = 30,918`. The library builds and the host are named in
`docs/construction.md` §5: **liboqs 0.16.0** (commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`),
liboqs-python 0.16.0, **pqcrypto 0.3.4** for the rows it provides, on Ubuntu 24.04.4 x86_64 with
Python 3.12.3.

## What is measured, and on what — and what is proven

- **Measured on a real library build:** the seven rows above (signature width, public-key width,
  and the outcome of verifying, extracting, blaming and tamper-rejecting two conflicting frames).
  Reproduced in this build on 2026-09-13; the raw output is `results/real-demo.json`.
- **Arithmetic asserted by tests, not by a run:** the frame formula and the 757/758 gate.
- **Proven, under a named assumption:** B0's accountability, non-frameability and safety properties
  are Theorem A of the v1.43 finalization (a theorem with proof, conditional on EUF-CMA of the
  chosen category-5 scheme — the assumption `A-sig`), reproduced in
  `domains/06-qpt128-security-target/`.
- **Theorem with proof under stated hypotheses:** Theorem C, which bounds the size of
  witness-committing proofs (KKW / BN++ / FAEST-style) for the hidden-signer relation. It is a
  necessary condition *for those families*, **not a universal lower bound**.
- **Estimates, labelled as such:** the linear-family bound of 412,800 bytes; the Binius64 PCS floor
  of 109,856 bytes (96-bit, from re-implemented estimators); the "no known primitive fits" verdict,
  which is an assessment of published primitives, not an impossibility proof.
- **Not implemented, stated here so a reader does not assume otherwise: there is no hidden-signer
  certificate.** B1 has a frame, a relation, an algebraic extractor and a ledger, and no qualified
  proof backend; `verify_b1` returns `STRUCTURE_ONLY_NO_QUALIFIED_PROOF` with
  `authorization_verified = False` by construction. B0 hides nothing: the signer bitmap is in the
  clear, so the seats that signed are public.
- **Not a bound:** no measured frame size in this domain is a security bound or a proof of anything.
  The measurements say what these library builds produced on this host.

## Recorded baseline vs this build's re-run

Every command reproduced. Two differences, both expected and recorded in `VERIFICATION.md`:

1. `results/report.json` prints `"module": "sidecar_free_certificate"` where the source-tree run
   printed `"sidecar_free_certificate_v1.44"` — the single content-level effect of dropping the
   version suffix from the file name. Every other field of the report is identical.
2. Run times differ (self-test 0.18 s now vs 0.094 s recorded; `--real-demo` 24.0 s now vs 13.7 s
   recorded). The output does not: `results/real-demo.json` matches the recorded run in every field.

Two findings recorded rather than patched, because the reference must stay the revision the
measurements were taken on:

- **A.10** — two B0 tests mutate the frame at CEQS29 body offsets while their names claim CQ44
  header checks, so they pass without exercising the check they name. `results/probe_a10_f6.txt`
  replays both mutations at both offsets and shows the check that actually fires.
- **F6** — the encode side does not enforce the 32,768-byte cap, although the wire specification
  makes that refusal normative: `encode_b0` at width 758 emits 32,810 bytes without raising, and
  `verify_b0` rejects the result. Recorded as an open item, not silently fixed.
