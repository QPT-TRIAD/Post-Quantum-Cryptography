# 00 — Start here

This package is the front door to the repository. The repository's top-level `README.md` states the
programme's result; this package is where a reader goes to act on it: what to read in what order, what
every term means *as this project uses it*, what each claim label obliges a claim to show, and what
can and cannot be re-run.

Read this page first, and nothing else, and you should hold an accurate belief about the work. That
is the test this page is written to pass.

---

## What the programme claims, in one paragraph

The programme set out to build **compact, conflict-extractable, post-quantum quorum certificates**: a
certificate that proves a supermajority of a 64-seat validator committee approved a message, that fits
inside the consensus message itself in at most 32,768 bytes with **no sidecar proof file**, that
verifies against a fixed authenticated registry and **no secret opener**, and from which **two
conflicting certificates publicly expose at least 22 seats that authorized both**. Two profiles were
specified. **B0** publishes the signer set and was built, measured with real post-quantum signatures
and demonstrated end to end: **11,396 bytes** with OV-V-pkc and **30,918 bytes** with the
OV-V-pkc‖SNOVA_29_6_5 hybrid, both inside the 32,768-byte bound. **B1** ("Mode S") hides the signer
set; its relation, frame, algebraic extractor and security ledger are fixed, and **no qualified proof
backend exists in this repository** — `verify_b1` never reports an authorization.

**The construction has not been independently peer-reviewed.** Nothing here has been through external
review, and no part of it is a standard, a deployment, or an audit-ready artifact. What it is: a
research record in which every claim carries its own label, refuted results are named rather than
removed, and a claim whose re-run does not reproduce is withdrawn in public with the reason.

## What to believe, by evidential category

The repository's seven claim labels are the vocabulary for this, defined once in
[`../02-theory-and-references/README.md`](../02-theory-and-references/README.md) and restated with
their obligations in [`claim-labels.md`](claim-labels.md). Reused here exactly:

| | What is in it |
|---|---|
| **Proven** `[T]` | The quorum-intersection counting fact (`2·43 − 64 = 22`) and the honest-support intersection that follows from it. Lemmas L1, L2 and L3 of the security target — L1 refutes the programme's own original target definition. The field certificate and the division-free public decoder. The joint-lift event bookkeeping and the selector probability identity, under stated premises. **Theorem A** for B0, conditional on `A-sig`. **Theorem C** for witness-committing proof families, under its stated hypotheses. |
| **Measured** `[M]` | Every frame size in the top-level README's result table, on the named library builds (`liboqs` 0.16.0, `liboqs-python` 0.16.0, `pqcrypto` 0.3.4) and host (Ubuntu 24.04.4 x86-64, Python 3.12.3). The audit suites' own counts. The devnet platform observations. |
| **Estimated** `[L]` | The linear-family bound of 412,800 bytes; the Binius64 polynomial-commitment floor of 109,856 bytes; the Mode B certificate sizes; the "no known primitive fits" verdict for B1 — an assessment of published primitives, not an impossibility proof. |
| **Simulated** `[S]` | Exact state-vector Grover simulation at reduced sizes; the games at deliberately weak parameters. |
| **Assumed** `[A]` | `A-sig` (EUF-CMA of the non-FIPS category-5 candidates at generic strength), the QROM heuristic, the T-count floors, the protocol-level assumptions, several ledger rows set to zero under model premises rather than proved. |
| **Conjecture** `[C]` | Stated as believed, not proved. The Target B design direction in domain 01; the hidden-signer design pattern. |
| **Reduction sketch** `[R]` | The extraction and accountability reductions in domains 01 and 05: the reduction is described and the loss accounted, but the steps are not written out in full. |

**The categories do not move.** A measurement never becomes a proof. A conditional theorem stays
conditional. A label is never upgraded — see [`claim-labels.md`](claim-labels.md) for the rule and for
two worked instances of each label.

## What is *not* claimed

Stated plainly, because a reader who reads only this page must not come away with a stronger belief
than the evidence supports:

- **The original security target, D3, is refuted.** `Pr[Win] < 2^-128` for *every* QPT adversary is
  unattainable for anything with a 256-bit secret: `2^63` Grover iterations already exceed that.
  The target survives only as a gate work factor, D1, with the stronger D2 as its rigorous form.
- **QPT-128 is not established.** The conclusions rest on named assumptions, not derivations from
  first principles. The audit stack's own words are "Conditional bounds only".
- **Hidden signers within 32 KiB are open.** B1's frame, relation, extractor and ledger are fixed and
  its ledger passes; the proof backend does not exist here. A second, separate hidden-signer line in
  `domains/08-hidden-signers` is a *tested design* with a size **estimate** and an attack-based
  ledger — no zero-knowledge backend, no security theorem for the instantiated proof system.
- **No measured frame size is a security bound or a proof of anything.** The measurements say what
  these library builds produced on the host named in the text.
- **The reference implementation is not constant-time**, and is not audit-ready.
- **Two records are withdrawn.** The property-layer figure "16/16 and 16/16" is withdrawn (a re-run
  gives 16 passes for one module and a collection error with zero tests executed for the other), and
  a recorded `PASS` in an S1-011 Grover slope assertion is withdrawn (it fails 51.3 % of the time over
  400 pooled runs). Both are recorded in `records/failed-assumptions.md`.

## The shape of the evidence

The programme's own list of what acceptance as a *standard proof* would still require is ten items,
carried in full in [`../04-security-and-validation/`](../04-security-and-validation/) and summarised
in §3 of the top-level `README.md`. The load-bearing ones: a proof backend for hidden signers;
constants verified against the full text of each cited paper rather than against a prior summary;
named assumptions that are still assumptions; proofs for lemmas L4 and L5 that are at present
statements with sketches; cryptanalysis of the programme's own new assumption, which today is
attack-based rather than a reduction; a second independent implementation of the full certificate
path; machine-checked verification of the wire format and the extractor; constant-time analysis;
registration practicality for the large category-5 public keys; and platform evidence beyond a single
host.

## Where to go next

| If you want | Go to |
|---|---|
| the result, stated once, with its arithmetic | the top-level [`README.md`](../../README.md) — §1 for the result, §2 for what is proven and what is refuted, §7 for provenance and exclusions |
| a route through the repository, by reader | [`reading-order.md`](reading-order.md) |
| a term defined as this project uses it | [`glossary.md`](glossary.md) |
| what a claim label obliges a claim to show | [`claim-labels.md`](claim-labels.md) |
| to run something, or to learn what cannot be run | [`reproduction.md`](reproduction.md) |
| what was re-run while this package was assembled | [`VERIFICATION.md`](VERIFICATION.md) |

This package does not restate a domain's result. Where a domain's own `README.md` qualifies a result,
that qualification is the operative one.
