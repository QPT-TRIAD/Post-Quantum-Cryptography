# Inflection 6 — from an eight-property checklist to a joint construction, and a floor that ends the search (v1.5/v1.6 → v1.18)

**Versions concerned:** v1.5 `docs/compactness-source-ledger-v1.5.md`, v1.6
`docs/backend-eligibility-proof.md`, and v1.18 `docs/research-qualification.md`. The versions
v1.7–v1.17 have **no documents in this repository**; what is known of them is in the ladder of
`README.md` §3.3 and is marked there as reported material.
**Date:** 9 September 2026.
**One sentence:** v1.6 turned an open-ended search for a backend into a falsifiable eight-property
test, every candidate failed it, and v1.18 concluded that the obstacle is a joint construction and
security qualification rather than a missing positive flag — with an arithmetic floor of 50,496 bytes
against the 32,768-byte gate.

## The state before

v1.3 and v1.4 had produced conditional theorems and left one practical question open, stated in both
documents in the same words: `< 32 KiB` end-to-end certificate. Between v1.5 and v1.17 the project
worked that question by building and measuring frames — a sequence of numbers with no surviving
proof documents (reported: 96-byte handles, link-hash proofs at 328,672 bytes, a 96-byte-handle frame
at 269,648 bytes, single-contributor frames at 506,848 bytes, frames of 776,736 / 785,456 bytes with
22 trace identities recovered). Those numbers are recorded in `README.md` §3.3 as reported; no claim
in this domain rests on them, because the documents that would support them are absent.

Two things did survive from that stretch and they are this inflection.

## v1.5 — a hard byte budget, as a ledger

`docs/compactness-source-ledger-v1.5.md` records the compactness sources and fixes the gate that
every later version measures against (`docs/32kib-contents-contract.md:11` uses the same form):

```
43h + P + O <= 32768
```

where `h` is the per-handle width in bytes, `P` the proof payload and `O` the fixed overhead. The
ledger also records, as a negative finding, that the then-known succinct lattice aggregate is not
zero-knowledge — i.e. compactness was being bought at the price of a missing required property.

Making the budget an equation rather than a target is the first half of the correction: it converts
"too large" into a per-component allowance that can be spent, checked and blamed.

## v1.6 — eight properties, and a test that can fail

v1.6 states the eligibility properties **E1–E8** and a theorem: a backend meeting E1–E8 instantiates
the v1.3/v1.4 stack unchanged (`docs/backend-eligibility-proof.md`). As the v1.6 checker implements
them, they are: post-quantum security, public verifiability, witness privacy, exact
threshold/same-set binding, SCCH compatibility, constructible prover, liveness adapter, and the byte
gate E8 `43h + P + O ≤ 32768`.

v1.6 also reclassifies a limitation that had been treated as disqualifying — the "not
zero-knowledge" finding of the 2026 suite — as historical, i.e. superseded by later work in that
suite. That reclassification is itself a correction and it is the reason the search could continue
at all.

## v1.18 — every candidate fails, and the obstacle is re-stated

v1.18 records a literature screen of 32 papers plus one repository with a single verdict
(`docs/research-qualification.md:7`):

> "The literature search identifies useful construction paths, but no examined construction qualifies
> for the complete target. Valid full QCs generated remain zero."

and states what the actual obstacle is: "a joint construction and security qualification, not a
missing positive flag in the eligibility checker". The same document retires the v1.6 checklist
framing explicitly.

It also derives the number that closes the format-level question
(`docs/research-qualification.md:167`):

```
|QC| >= 4,288 + 16 + 46,192 = 50,496 > 32,768
```

i.e. a retained-format certificate has a floor of 50,496 bytes against a 32,768-byte gate, and the
format-level obstruction is arithmetic rather than an estimate. The corresponding combinatorial
figure is `C(64,43) = 41,107,996,877,935,680 ≈ 2^55.19` (`:179`) — the number of 43-seat subsets a
certificate must be equivalent to, which is the same 55.19-bit figure the v0.7 checker computed as
`combinatorial_required_columns` (`results/ce_qs_quorum_family_checker.txt`).

## Evidence that these were corrections

**v1.6 — `src/ce_qs_backend_eligibility_checker.py`**
(`results/ce_qs_backend_eligibility_checker.txt`):

```
LaZer-2024-succinct        eligible=False byte_status=FAIL total=75300
LaZer-Toolkit-2026         eligible=False byte_status=OPEN total=None
CoSNIZK-published-DAA      eligible=False byte_status=FAIL total=38912
Fusion-direct              eligible=False byte_status=FAIL total=47185
Lazarus-repo               eligible=False byte_status=PASS total=30736
Mutable-BARG-theory        eligible=False byte_status=OPEN total=None
PASS score_28KiB_48B=2032
EXPECTED-FAIL score_28KiB_96B=-32
PASS eligibility_requires_all_properties toy_total=28704
```

This result file is the inflection's core evidence, and three lines deserve naming.

- The six candidate rows. Five of them fail the byte gate or have no number at all; the one that
  passes the byte gate — `Lazarus-repo`, 30,736 bytes — is still `eligible=False`, because the
  decision is a conjunction of all eight properties and not a size comparison. That is the v1.6
  correction in a single line: size alone was never going to decide this.
- `PASS score_28KiB_48B=2032` versus `EXPECTED-FAIL score_28KiB_96B=-32`. With 48-byte handles the
  per-seat proof budget inside the cap is 2,032 bytes; with 96-byte handles it is **−32** — the frame
  cannot even hold its own handles. This pair is the "fits before, fails after" evidence that
  motivated the handle-width question, and it is the direct ancestor of v1.24's purpose-based
  allocation of 208 / 5,504 / 27,056 bytes (`docs/32kib-contents-contract.md:15–19`): a 5,504-byte
  handle block leaves 27,056 for the proof.
- `PASS eligibility_requires_all_properties toy_total=28704` — a backend under the byte gate is still
  refused when any other property is missing, i.e. the checker does not reduce eligibility to bytes.

**v1.18 — no checker.** The document's evidence for itself is the screen of 32 papers plus one
repository, an audited artifact of 34 checks that is **not in this repository**, and the two
arithmetic results above. The absent artifact is recorded as a `not-run` line in `VERIFICATION.md`
with its reason; the arithmetic (`4,288 + 16 + 46,192 = 50,496`; `C(64,43) ≈ 2^55.19`) is
re-computable by hand and by the v0.7 checker's independent path.

## Why this is an inflection and not just a review

Before v1.18 the project was looking for a backend that would pass a checklist. After v1.18 the
project's own conclusion is that no examined backend passes, that the missing object is a *joint*
construction of the certificate and its proof, and that the remaining work is bounded by arithmetic
rather than open-ended search. Every subsequent version is a step in that construction — v1.19 and
v1.20 measure and reduce the circuit (Inflection 7), v1.21 quantifies which branches survive, and
v1.24 fixes the contents of the object being built (Inflection 8).

See also: `docs/compactness-source-ledger-v1.5.md`, `docs/backend-eligibility-proof.md`,
`docs/research-qualification.md`, and `README.md` §3.3 for the reported-only v1.7–v1.17 numbers.
