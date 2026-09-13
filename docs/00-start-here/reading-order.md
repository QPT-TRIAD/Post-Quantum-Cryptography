# Reading order

Three routes, for three readers. Each is a numbered list: what the step gives you, and what you need
before you can take it. Route (a) is short and its commands are given verbatim and were run while this
package was assembled — the observed results are in [`VERIFICATION.md`](VERIFICATION.md).

The top-level [`README.md`](../../README.md) §5 lists the same material from a different angle, as
four routes by reader. Routes (a) and (b) here are its route 1 ("the result") and its routes 2 and 4
("the evidence", then "a specific domain"); route (c) here is its route 3 ("the route that produced
it"). Where the two differ, this file adds the *order* and the prerequisites; the top-level README
states the result.

Each domain directory also has its own `README.md` — with one exception at the time of writing,
`domains/08-hidden-signers`, whose two documents under `docs/` are its entry point — and each
`README.md` ends with its own entry point: a numbered list or an "if you want…, read…" table. Those
are the operative orders inside a domain; the routes below point at them rather than replacing them.

---

## Route (a) — verify the central claim

**For the reader who wants the two size numbers and the security statement reproduced, and nothing
else.** The shortest path from a fresh clone to the sentence "I have seen 11,396 and 30,918 bytes, and
I have seen what the security statement is conditional on."

**What you need beforehand:** no cryptography. A Unix-like host, Python 3, and the pinned environment
for step 3. About ten minutes of wall time with the environment already built; add the environment
build itself — roughly 30–40 minutes, and no root is needed — if you do not have it.

1. **The result, stated once.** Read the top-level [`README.md`](../../README.md) §1. It gives the
   frame formula `216 + 43·W`, the size gate `W ≤ 757`, and the measured table. *Gives you:* the claim
   in the form the repository makes it. *Needs:* nothing.

2. **How to run anything at all.** Read [`reproduction.md`](reproduction.md) — specifically which tier
   each command falls into and what cannot be reproduced. *Gives you:* the ability to tell before
   starting whether a run will work. *Needs:* nothing.

3. **The environment.** Follow `tooling/environment.md` to build it, then
   `source tooling/activate.sh` (set `PQT_SRC` first if a harness you plan to run reads the read-only
   research tree; the scripts under `domains/01`–`domains/10` do not, and
   `domains/11-independent-audit-stack` states per layer which do). *Gives you:* the pinned Python
   3.12.3 environment, the locally built `liboqs` 0.16.0 shared library, and the formal tools.
   *Needs:* Ubuntu 24.04-class x86-64, `gcc`, `cmake`, `ninja`, OpenSSL headers; roughly 30–40
   minutes; no root.

4. **The B0 reference suites.** With the environment active:

   ```
   python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --self-test
   python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --real-demo
   ```

   The first runs the reference module's 39 tests. The second signs a real 64-seat registry with real
   post-quantum signatures through `liboqs` 0.16.0 and `pqcrypto` 0.3.4, encodes two conflicting
   frames, verifies them, extracts the 22 common seats, assigns blame and rejects tampered variants.
   *Gives you:* the measured table, produced on your host. *Needs:* the environment, and specifically
   the `liboqs` shared library — without it the demo reports the library as unavailable rather than
   failing, and that behaviour is itself recorded in `domains/07-compact-certificate-b0/results/`.

5. **The security statement.** With the environment active:

   ```
   python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --self-test
   ```

   Then read `domains/06-qpt128-security-target/docs/qpt128-finalization.md` §0, which is the result
   table, and `domains/06-qpt128-security-target/README.md`, which states which of the targets D1, D2
   and D3 was adopted, which was refuted, and by which lemma. *Gives you:* what the security claim
   actually is, and the exact-rational ledger that decides which configurations meet it. *Needs:*
   `sympy` and `mpmath` from the pinned environment.

6. **The raw artifacts, without running anything.** Read
   `domains/07-compact-certificate-b0/results/real-demo.json` beside
   `domains/07-compact-certificate-b0/results/README.md` (provenance of every file in that
   directory), then `domains/06-qpt128-security-target/VERIFICATION.md` (recorded against observed for
   every command in that domain). *Gives you:* the numbers and their provenance, and every place a
   re-run disagreed with the record. *Needs:* nothing.

7. **The two profiles side by side.** Read `docs/03-construction/profiles.md`, then
   `domains/07-compact-certificate-b0/docs/b0-wire-spec.md` — the normative wire specification, which
   is what an implementer works from. *Gives you:* B0 as bytes, and B1's frame beside it. *Needs:*
   step 4's vocabulary (`frame`, `handle`, `bitmap`, `cfg`); see [`glossary.md`](glossary.md).

**Stop here if that is all you wanted.** Route (a) does not reproduce any proof, and it does not
reproduce Theorem A or Theorem C — it reproduces the measurements and identifies the security
statement's assumptions. For those, take route (b).

---

## Route (b) — audit the argument

**For the reader who wants to check the chain rather than the numbers:** definitions → counting fact →
construction → extractor → reduction → security target → formal models → games.

**What you need beforehand:** comfort with reduction arguments, the random-oracle model in its quantum
form, and Fiat–Shamir-with-aborts. This route is long — the operator-ledger document alone is 846 KB —
and it is the one to take before believing any number in the repository.

1. **The terms of reference.** `domains/01-accountable-quorum-foundations/README.md`, then follow its
   own "How to read this domain, in order" list of seven items. Start with
   `docs/definitions-and-conflict-extraction.md`. *Gives you:* committee, seat, quorum, quorum
   intersection, the 22 double-authorizers requirement, the conflict domain, blame — and the counting
   fact everything later rests on, by proof. *Needs:* nothing beyond careful reading. Note the
   domain's own split between Target A (deployable, built) and Target B (frontier, open).

2. **The construction's history.** `domains/02-ceqs-construction-evolution/README.md` §2 for the
   domain's own "if you want…, read…" table, then `docs/construction-end-to-end.md`. The 24-version
   ladder is the record of what was tried; v1.24 is the current revision, and the domain states
   plainly that a reader looking for a security theorem must not use it. *Gives you:* the shape of the
   construction and the reason the version ladder exists. *Needs:* step 1's vocabulary.

3. **Extraction and the reductions.** `domains/05-extraction-and-signature-reductions/README.md`, then
   its own nine-item order. Read `docs/hybrid-sampling-bound.md` even if you read nothing else there:
   it is the domain's clearest negative result, and it refutes a bound the programme had used.
   *Gives you:* how two accepted certificates become two witnesses, and how a witness becomes a
   forgery against a standard scheme at a stated loss. *Needs:* step 1, and enough probability to
   follow a union bound. Watch for the two DFMS coefficients `(20ℓ+60)` and `(22ℓ+60)`, which the
   domain records as a discrepancy rather than resolving it.

4. **The security target, evaluated.** `domains/06-qpt128-security-target/README.md`, then its own
   four-item order: `docs/qpt128-finalization.md`, `docs/theory.md`, `docs/ledger.md`,
   `VERIFICATION.md`. *Gives you:* D1, D2 and D3 stated once; lemmas L1–L5; Theorems A and B; and the
   exact-rational ledger's verdicts, including the rows that fail. *Needs:* steps 1 and 3.

5. **The certificate.** `domains/07-compact-certificate-b0/README.md` and its own "Read in this order"
   table of seven rows: `docs/construction.md`, `docs/b0-wire-spec.md`,
   `docs/sidecar-free-finalization.md`, `src/sidecar_free_certificate.py`, `results/`,
   `VERIFICATION.md`. *Gives you:* Theorem A and Theorem C with their hypotheses, the two recorded
   findings A.10 and F6, and the size arithmetic asserted by the tests. *Needs:* steps 1 and 4.

6. **Hidden signers, both lines.** Read `domains/08-hidden-signers/docs/hidden-signer-32kib.md` and
   then `domains/08-hidden-signers/docs/mode-b-security.md`. These are **two different lineages**, and
   the glossary entry `B1 / Mode S vs Mode B` states how they differ. *Gives you:* why hiding the
   signer set collides with the size cap, and what the second line claims and does not claim.
   *Needs:* step 5. Note that this domain's directory has no `README.md` at the time of writing; its
   two documents are the entry point.

7. **The independent pass.** `domains/11-independent-audit-stack/README.md`, then its own nine-item
   order. Its first item, `docs/audit-stack-overview.md`, is the claim-by-claim ledger of
   counterfactuals attempted and verdicts reached. *Gives you:* the layer that tries to disprove the
   programme's claims rather than restate them, and the disagreements it records rather than smooths
   over — including the withdrawn "16/16 and 16/16" property figure. *Needs:* the environment of route
   (a) step 3 for the layers you want to re-run, and `PQT_SRC` for several of them.

8. **The formal models.** With the environment active:

   ```
   python3 domains/11-independent-audit-stack/formal/bounded_checker.py
   tamarin-prover --prove domains/11-independent-audit-stack/formal/qpt128_quorum.spthy
   ```

   The first is the exhaustive third protocol model and returns in about a second. The second is the
   symbolic model; it is the slowest thing in the repository, minutes per run. *Gives you:* the
   protocol properties in two independent models, one of them machine-checked at N = 4. *Needs:* the
   environment; the Tamarin binary, Maude and their library path come from `tooling/activate.sh`. Read
   `domains/11-independent-audit-stack/docs/formal-models.md` for what each lemma establishes and for
   the N = 7 record, which is resource-limited and partly absent.

9. **The games and the attack lab.** `domains/09-security-games-and-attack-lab/README.md` and its own
   nine-item order: the harnesses, the recorded write-up (`results/attack-lab-results.md`), then one
   document per game (`docs/game-frame.md`, `docs/game-suppress.md`, `docs/game-evade.md`,
   `docs/game-safety.md`), the methodology, and the domain's validation status. *Gives you:* 24
   violation attempts with zero successes at deliberately weak parameters, and four games whose
   measured exponents are compared with theory. *Needs:* the environment and the `domains/08` modules
   the lab loads; the commands and the runtimes observed while this package was assembled are in
   [`reproduction.md`](reproduction.md). Note that no result here is a security claim for production
   parameters.

10. **The mistakes, in place.** `records/failed-assumptions.md` (entries Q1–Q6, I1–I8, A1–A28, F1–F6),
    `records/fixes.md`, and `docs/02-theory-and-references/gaps-and-unknowns.md`. *Gives you:* every
    refutation, withdrawal and unreproduced claim, with its date and reason. *Needs:* nothing. This is
    the step that makes the rest auditable; a reader who reads only one step of route (b) should read
    this one.

---

## Route (c) — understand the programme

**For the reader who wants to know what was attempted, in what order, what it cost, and what the
infrastructure studies found** — the research journey and the deployment studies, rather than the
proof chain.

**What you need beforehand:** nothing specialist. Some steps assume you can read a ledger or a
specification.

1. **The chronology.** `docs/01-research-journey/README.md`, then `chronology.md`, then `dead-ends.md`
   and `decisions.md`. *Gives you:* the trail in order — what was attempted, what was concluded, what
   was refuted, what was abandoned — as a record rather than an argument. *Needs:* nothing. Read the
   README's note on `pqt.md` before opening that file: it is the historical artefact written *before*
   the security target was redefined, and it is not annotated in place.

2. **The theory, with its borrowings marked.** `docs/02-theory-and-references/README.md` and the
   document it points to for whatever you are checking. *Gives you:* every theory, lemma, bound,
   standard and model the record uses — its statement *as used here*, its label, its citation status,
   and which part was borrowed when only part applies. *Needs:* nothing; the entry shape is stated in
   that README.

3. **The version ladder.** `domains/02-ceqs-construction-evolution/README.md` and
   `docs/inflections/`. *Gives you:* 24 versions of one construction, what changed between them and
   why. *Needs:* nothing.

4. **Carrying the relation through a real proof backend.** `domains/03-zk-carrier-experiments/README.md`
   and its own "if you want…, read…" table, then `docs/experiment-*.md`. *Gives you:* the measured
   evidence that the *representation* of the relation is not the obstacle — and the count of accepted
   complete original-goal certificates, which is zero. *Needs:* nothing for the reading; the native
   path is `not-run` here and the domain says why.

5. **The operator ledger.** `domains/04-operator-ledger/README.md` and its eight-item order. *Gives
   you:* a 1,000-operator catalogue screened against one question — can any of it discharge a real
   proof obligation — and a measurement that corrects an earlier count in the same document.
   *Needs:* nothing, but the domain tells you which parts to read on a first pass and which to skip.

6. **The infrastructure studies.** `domains/10-digital-infrastructure/README.md` and its own seven-item
   reading order, for the six deployment studies (firmware signing, DNSSEC, TLS and the Web PKI,
   constrained broadcast, smart cards and HSMs, and category migration). The order matters here: read
   `docs/pq-infra-program.md` (the programme's own document, written *before* the audit) and
   `docs/studies.md` first, then `docs/pq-infra-audit.md` — the v2.1 audit, which corrected several of
   the programme's own headlines — and `docs/audit-method.md`, which states every programme-claim →
   audit-measurement discrepancy **as a discrepancy**. *Gives you:* measured bytes and hashes per
   study, the four hypotheses that died during development, and the boundary of what was measured.
   *Needs:* nothing.

7. **What a live node measured.** `docs/05-devnet-evidence/README.md` — read its standing caveat
   first, then `test-campaign.md` and `measurements.md`. *Gives you:* the operational premises the
   security claims rest on, as observed on a controlled single-host fixture. *Needs:* nothing. This is
   platform evidence, not part of the cryptographic chain.

8. **Where the programme's own record disagrees with itself.** `records/` — the refutation register,
   the release record of the fixes, and the provenance of every file. *Gives you:* the disagreements
   in place, with dates and reasons. *Needs:* nothing.

---

## A note on what "read in order" means here

Where a domain README gives its own order, that order is about that domain: it assumes you have taken
route (a) or (b) at least as far as the vocabulary in [`glossary.md`](glossary.md). The three routes
above are the cross-domain orders. They are not prerequisites for each other — a reader who wants only
the infrastructure studies can start at route (c) step 6 — but a reader who intends to *believe* a
security claim should take route (b) step 10 and route (c) step 8 before doing so.
