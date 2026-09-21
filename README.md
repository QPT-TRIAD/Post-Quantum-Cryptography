# Post-Quantum Cryptography

This repository is the complete research record of a programme that set out to build **compact,
conflict-extractable, post-quantum quorum certificates**: a certificate that proves a supermajority of
a 64-seat validator committee approved a message, that fits inside the consensus message itself in at
most 32,768 bytes with no sidecar proof file, that verifies against a fixed authenticated registry and
no secret opener, and from which **two conflicting certificates publicly expose at least 22 seats that
authorized both** — enough to identify the offenders rather than merely detect the crime. Two
profiles were specified: **B0**, which publishes the signer set and was built, measured with real
post-quantum signatures and demonstrated end to end; and **B1** ("Mode S"), which hides the signer set
and has a fixed relation, frame, algebraic extractor and security ledger, but no qualified proof
backend. The project set out to show that accountability and compactness need not be traded against
each other under post-quantum signatures; for the public-signer profile it showed exactly that, and
for hidden signers it showed why the size cap and the hiding requirement collide, and quantified the
collision.

Everything here carries its own label — theorem with proof, reduction sketch, model-or-ledger
estimate, measurement, simulation, assumption. Labels are never upgraded, refuted results are named
rather than removed, and where a re-run did not reproduce a recorded number the number was withdrawn
in place with the reason. Each domain states what it proves and what it does not.

---

## 1. The result

### 1.1 The certificate profiles

Both profiles share one frame. The contract layout is a 208-byte header, 43 handles of 128 bytes
(5,504 bytes) and one joint proof of at most 27,056 bytes — 32,768 in total. Profile **B0**
(suite `0x44B0`) replaces the handles with an 8-byte signer bitmap followed by 43 fixed-width
signatures, so its frame is `208 + 8 + 43·W = 216 + 43·W` for a signature width `W`. That substitution
is permitted by the contract, which notes that replacing the handles requires a different public
extraction mechanism; the bitmap and the public signatures are B0's. Profile **B1** (suite `0x44B1`)
keeps the contract layout and hides the signers.

### 1.2 Measured sizes, with the arithmetic

Measured with real signatures through liboqs 0.16.0 (liboqs-python 0.16.0) and pqcrypto 0.3.4 for the
rows pqcrypto provides, on Ubuntu 24.04.4 x86-64 with Python 3.12.3. Every frame in the table was
encoded, verified and conflict-extracted:

| Scheme (claimed category) | Signature `W` (B) | Signature block `43·W` | Frame `216 + 43·W` | Outcome |
|---|---:|---:|---:|---|
| **OV-V-pkc** (5) | 260 | 11,180 | **11,396** | fits, margin 21,372 B |
| SNOVA_29_6_5 (5) | 454 | 19,522 | 19,738 | fits, margin 13,030 B |
| SNOVA_60_10_4 (5) | 576 | 24,768 | 24,984 | fits, margin 7,784 B |
| **OV-V-pkc‖SNOVA_29_6_5** (5) | 714 | 30,702 | **30,918** | fits, margin 1,850 B |
| MAYO-5 (5) | 964 | 41,452 | 41,668 | rejected, over by 8,900 B |
| ML-DSA-87 (5) | 4,627 | 198,961 | 199,177 | rejected, over by 166,409 B |
| Falcon-padded-512 (1) | 666 | 28,638 | 28,854 | fits, but claimed category 1 |

The size gate is exact and asserted by the tests: `W ≤ (32,768 − 216) // 43 = 32,552 // 43 = 757` —
the 216 being the 208-byte header plus the 8-byte signer bitmap — so 757 bytes gives 32,767 and fits
while 758 gives 32,810 and does not. Every scheme wider than 757 bytes
is excluded by arithmetic alone before any cryptographic question is asked; that is why the two rows
marked rejected are rejected, and no FIPS-standardized signature is among the schemes that fit
(ML-DSA-87 is 4,627 bytes and SLH-DSA-SHAKE-256s is 29,792). The category column is each library's
`claimed_nist_level` — a submitter claim, not an established one.

The `216 + 43·260 = 11,396` and `216 + 43·714 = 30,918` frames were each verified, each extracted its
22 common seats under two conflicting certificates, each assigned blame on those seats, and each
rejected tampering. The two rejected rows were not verified — they fail the size gate before
verification. The Falcon-padded-512 row verifies but its claimed category is 1, so it does not meet
QPT-128 and is not admissible.

The programme's security statement for B0 is **Theorem A**: accountability holds with no probability
at all (the 22-seat intersection is a counting fact), and non-frameability and safety reduce tightly
and linearly to the EUF-CMA security of the chosen signature scheme. Under the programme's gate
accounting the QPT-128 target holds with a **+23.0-bit margin**, conditional on the named assumption
`A-sig` that the chosen non-FIPS category-5 candidate is EUF-CMA at generic strength.

**The main goal, as the programme states it** — conflict-extractable, compact post-quantum quorum
signatures without a sidecar — is recorded as met by B0. Hidden signers together with the 32 KiB cap
remain open.

### 1.3 Hidden signers

Profile B1's relation, frame, algebraic extractor and ledger are fixed and its ledger passes with a
+29.4-bit margin, but **no qualified proof backend exists in this repository**: the only
implementation is a structure-only marker, and `verify_b1` never reports an authorization. Theorem C
quantifies the obstruction for witness-committing proof families (KKW, BN++, FAEST-style): the
27,056-byte slot admits at most **359 bits of witness per seat at N = 2^16**, against a Mode S
relation that needs 2,816 bits per seat with the cheapest published primitives — and the budget falls
to 1,006 bits at N = 2^48, or 1,258 bits with 32 grinding bits. Theorem C is a necessary condition
**for those families**, not a universal lower bound.

A second, separate hidden-signer line is recorded in `domains/08-hidden-signers`. It is a tested
design with a size **estimate** and an attack-based ledger, not a proven scheme, and its own README
says so: it has no zero-knowledge backend, no security theorem for the instantiated proof system, no
collaborative prover, and no dedicated cryptanalysis beyond the attack families tested. What it
records is that a production-parameter C prover produced a **30,684-byte** hidden-signer certificate
that verified and extracted its 22 seats, with the D2 ledger passing at a 7.7-bit margin at its
production setting under the multi-round-loss form of its proof-soundness row. Its stated limitations
are as much part of the result as its size: the size figures are estimates under a modelled backend,
the proof-soundness row is the backend's obligation and the ledger's default form of it omits the
multi-round loss, and two of its security rows are set under named assumptions rather than derived.

---

## 2. What is proven, what is measured, what is estimated, what is refuted

Every claim in this repository carries one of seven labels, and the labels are never upgraded:

| Label | Meaning |
|---|---|
| `[T]` theorem with proof | a written proof, for the statement given, with its assumptions named |
| `[R]` reduction sketch | the reduction is described and the loss accounted, but the steps are not written out in full |
| `[L]` model-or-ledger estimate | produced by an explicit model or ledger with named constants; a computation, not a proof |
| `[M]` measurement | observed by running something on a named build and host; not a bound and not a security statement |
| `[S]` simulation | produced by a simulator, a toy field or a reduced parameter set |
| `[A]` assumption | taken as given, not proved; the reason is stated |
| `[C]` conjecture | stated as believed, not proved |

**Proven, with the assumptions named.** The quorum-intersection counting fact (`2·43 − 64 = 22`) and
the honest-support intersection that follows from it. Lemmas L1, L2 and L3 of the security target —
including L1, which refutes the programme's original definition of the target. The field certificate
and the division-free public decoder. The joint-lift event bookkeeping and the selector probability
identity under stated premises. The exact thresholds of the signature reduction. Theorem A for B0,
conditional on `A-sig`. Theorem C for witness-committing proof families, under its stated hypotheses.

**Measured.** Every frame size in §1.2, on the named library builds and host. The output sizes of the
proof-carrier experiments, quoted from the retained result files and re-checked on disk against the
records; the native proofs those experiments produced are 335,360–339,200 bytes, an order of magnitude
over the proof position. The audit suites' own counts. The devnet platform observations.

**Estimated, and labelled as such.** The linear-family bound of 412,800 bytes and the Binius64
polynomial-commitment floor of 109,856 bytes. The Mode B certificate sizes. The "no known primitive
fits" verdict for B1, which is an assessment of published primitives, not an impossibility proof. The
ledger's cost floors and its model-premise rows, several of which are set to zero rather than proved.

**Refuted, rejected or withdrawn — named rather than omitted.**

- **The original security target, D3**, is refuted. D3 was `Pr[Win] < 2^−128` for *every* QPT
  adversary; Lemma L1 shows this is unattainable for anything with a 256-bit secret, because `2^63`
  Grover iterations already exceed `2^−128`. The target was redefined as a gate work factor (D1, and
  the stronger D2, `Pr[Win] ≤ G·2^−130`). Recorded in `records/failed-assumptions.md` entry `Q1` and
  in `domains/06-qpt128-security-target`.
- **The sampling bound is not established.** The proposed substitution `ε_SLH := exp(−256Δ²)` for the
  signature-forgery term is refuted by the domain's own counterexample: the bound needs either
  independent trials or a proved sequential conditional-mean premise, and the correlated public
  sampling proposed for this construction supplies neither. Hoeffding's inequality itself is a
  theorem and is not in question; its application here is what fails. The audit reports
  "Conditional bounds only; QPT-128 is not established" and substitutes no sampling endpoint.
  Recorded in `domains/05-extraction-and-signature-reductions`.
- **A recorded property count is withdrawn.** `records/fixes.md` recorded the property layer as
  "16/16 and 16/16". A re-run produced 16 passes for the Mode B module and a collection error with
  **zero tests executed** for the hash-signature module, which builds a mixed `m ≠ n` parameter pair
  that the fix now refuses. The "16/16" is withdrawn; the rest of the line reproduced and is kept.
  Recorded as `records/failed-assumptions.md` entry `A28` (2026-09-13).
- **Compat mode** — a category-5 signature inside an extractable proof — is withdrawn. The conversion
  is correct, but `ε_sig` must be evaluated at the reduction's running time, which includes the
  `O(q²)` extractor charge; the row then fails by 185 bits in gate units.
- **Further refutations**, each with its own regression test: the `exp(−256Δ²)` product-of-advantages
  rule for the AND hybrid; the OR hybrid; two-special soundness for the circuit backend; algebraic
  acceptance as a substitute for authorization; SLH-DSA tree structure as a source of fresh
  one-bit challenges; the qubit-count-implies-security inference; a recorded PASS in the S1-011
  Grover slope assertion, which fails 51.3 % of the time over 400 pooled runs and was replaced by a
  multi-seed median.
- **A recorded figure the sources do not support.** The operator ledger's amendment count as measured
  against the document itself: 15 of 116 amendments have an executable witness (10 on a strict
  reading), 0 of 116 carry any literature citation, and therefore 101 of 116 have neither. The
  earlier figure counted the second half of the file alone.

**The shape of the evidence, stated plainly.** The QPT-128 conclusions rest on named assumptions —
EUF-CMA of the non-FIPS category-5 candidates at generic strength, generic bounds for single-block
SHAKE256, the QROM heuristic, T-count floors, and the protocol-level assumptions — not on derivations
from first principles. Lemma L5 is a model-or-ledger estimate whose source's own word is "roughly".
Lemma L4's convexity claim is stated without the proof being written out; that is a gap in the
exposition, not in the arithmetic the checker performs. Several rows in the hidden-signer ledger are
set to zero under model premises rather than proved. No measured frame size in this repository is a
security bound or a proof of anything; the measurements say what these library builds produced on the
host named in the text.

---

## 3. What acceptance as a standard proof would require

What is still missing is stated here rather than left for a reader to infer. The consolidated list is
carried in full in `docs/04-security-and-validation/`. In summary, for the programme's results to be
accepted as a *standard proof* rather than as a well-documented research record, the following are
missing:

1. **A proof backend for hidden signers.** B1's relation, frame, extractor and ledger are fixed, but
   no size-conforming proof system exists; the only backend is a structure-only marker. Theorem C
   explains the obstruction but is not a universal lower bound.
2. **Constants provenance.** Each cited bound must be verified against the full text of the cited
   paper. "Checked against the full texts" is at present an unrecorded process claim, not a
   reproducible check. One coefficient discrepancy is recorded open rather than silently resolved.
3. **Named assumptions are not theorems.** `A-sig`, the QROM model, the T-count floors, the
   protocol-level assumptions and the model-premise rows all remain assumptions. The honest signer
   set in the hidden-signer analysis ultimately requires a *collaborative* prover that does not exist.
4. **Complete proofs for the remaining lemmas.** L4 and L5 have statements and sketches; the
   extractor-overhead lemma is approximate.
5. **Cryptanalysis of the programme's own new assumption** — expanding random multivariate quadratic
   systems with a power handle. Current evidence is attack-based (XL and hybrid solvers, SAT), not a
   reduction to a standard problem, and the SAT evidence is reported as a summary rather than a
   reproducible run. A dedicated Gröbner and Weil-descent analysis is open.
6. **A second, independent implementation of the full certificate path**, including the extractor,
   beyond the independent checks already in the audit stack. What exists today is an independent
   implementation of the B0 wire format alone — which is not nothing: it agreed with the reference on
   6,701 of 6,701 checks over 900 generated vectors — and it is the source of 18 recorded
   specification gaps.
7. **Formal verification of the wire format and the extractor.** The specification gaps the
   independent implementation found must be closed, and a machine-checked model of the extractor's
   guarantees completed.
8. **Constant-time and side-channel analysis.** The reference implementation is not constant-time
   today, and the smart-card and firmware studies say so explicitly.
9. **Registration practicality.** The category-5 public keys the public-signer profile needs are
   large — OV-V alone is 446,992 bytes per seat — and their encodings overflow some deployment
   fields; the infrastructure studies record which.
10. **Beyond this host.** The platform evidence at 64 seats is single-host, storage-sensitive local
    observation. Partition tolerance and liveness at scale are `not_run`, not passed.

---

## 4. The domains

| Directory | What it holds, and what it establishes |
|---|---|
| `docs/00-start-here` | The entry point: reading order, glossary, claim labels, reproduction entry point. |
| `docs/01-research-journey` | The chronological trail: what was attempted in what order, what was concluded, what was refuted and what was abandoned. A record, not an argument. |
| `docs/02-theory-and-references` | Every theory, lemma, bound, standard and model the record uses — its statement *as used here*, its label, its citation status, and which part was borrowed when only part applies. |
| `docs/03-construction` | The construction end to end in the order a verifier executes it, the B0 wire format as bytes, and the two profiles side by side. |
| `docs/04-security-and-validation` | The security target, the games, the attack lab, and the consolidated validation status — including the full list summarised in §3 above. |
| `docs/05-devnet-evidence` | What a separate ledger testbed measured about the operational premises the security claims rest on. Platform evidence, not part of the cryptographic chain. |
| `domains/01-accountable-quorum-foundations` | The formal starting point: committee, seat, quorum and blame; the intersection counting fact; the epoch-barrier specification. Establishes the counting fact by proof and specifies the barrier. |
| `domains/02-ceqs-construction-evolution` | The version ladder of the construction, each version with its checker and its result. Its reductions are conditional theorems over unnamed advantages; no version has ever produced a valid full certificate. |
| `domains/03-zk-carrier-experiments` | Carrying the relation through a real proof backend: adapters, fixtures, negative controls, and the measured evidence that the representation is not the obstacle. The count of accepted complete original-goal certificates is zero. |
| `domains/04-operator-ledger` | The 1,000-operator catalogue screened against one question — can any of it discharge a real proof obligation. Reports review coverage, not theorems. |
| `domains/05-extraction-and-signature-reductions` | The extractor, the joint-lift composition, the signature reductions, and the audits that refuted the proposed sampling shortcut. Its clearest result is a negative one. |
| `domains/06-qpt128-security-target` | The security target stated once and evaluated exactly: lemmas L1–L5, Theorems A and B, and the exact-rational ledger that decides which constructions meet the target. |
| `domains/07-compact-certificate-b0` | The 32 KiB certificate: the wire specification, the two profiles, the size gate, the measured table, and Theorem C. |
| `domains/08-hidden-signers` | Hiding the signer set: the Mode A and Mode B designs, the written reductions for the production form, and the ledger. The hidden-signer profile **does not ship**: Mode A's linear handle is refuted as a security choice, Mode B is a tested design with attack-based evidence and no proven scheme, and one of the profile's requirements has no construction at all. |
| `domains/09-security-games-and-attack-lab` | The games the construction must survive and the attacks actually run against it: 24 violation attempts against the real implementation, zero successful violations, at deliberately weak parameters. |
| `domains/10-digital-infrastructure` | Six deployment studies — firmware signing, DNSSEC, TLS and the Web PKI, constrained broadcast, smart cards and HSMs, and category migration — each measured, none a deployment. |
| `domains/11-independent-audit-stack` | Independent checks that attempt to disprove the claims: mathematics, symbolic protocol models, primitives against conformance vectors, sanitizers and fuzzing, property and differential testing, fault injection, and a specification-only re-implementation of the B0 wire format. |
| `domains/12-quantum-search-measurement` | Exact simulation of quantum search against oracle circuits that are actually built, including a reversible SHA-256 compression function verified against a reference implementation. Measures the two search laws the ledgers assume, and prices one oracle query in gates instead of assuming the price. |
| `domains/13-lattice-reduction-stress` | Real lattice reduction against the rounding-based trace function at dimensions a desktop reaches, plus the community estimator at full scale. Its own measurement code is the subject of four recorded defects, two of which changed previously recorded numbers. |
| `domains/14-classical-attack-surface` | The raw primitives with no framing or proof layer around them, attacked classically at scaled sizes to map how the work grows. Every campaign is gated by controls whose verdicts are known in advance, and refuses to report subject verdicts when a control misbehaves. |
| `domains/15-executable-reductions` | The security reductions of the hidden-signer design, implemented as programs and run against adversaries that genuinely win. Records that the non-frameability reduction, as written, cannot be carried out against one legitimate adversary class — a gap in a proof, not a break of the scheme. |
| `records/` | The programme's own mistakes: the register of refuted hypotheses, the release record of the fixes, canonical copies of the audit ledger and checklist, the findings of the verification pass, and the provenance of every file. |
| `tooling/` | How to rebuild the environment and re-run everything, with the package guide and the import inventory. |

Two boundaries apply throughout. The repository is **not** the ledger implementation: the consensus
node, its devnet harness and its configuration belong to a separate repository and are not copied
here. And the record **does not restate a domain's claim more strongly than that domain states it** —
where a domain's own `README.md` qualifies a result, that qualification is the operative one.

---

## 5. How to read this repository

Start with `docs/00-start-here/reading-order.md`, which gives the routes and the vocabulary. Four
routes serve four different readers:

1. **The result.** `docs/03-construction` for the object and its sizes, then
   `domains/07-compact-certificate-b0` for the specification, the measurements and the impossibility
   result. `domains/06-qpt128-security-target` for what the security statement actually is and what
   it is conditional on.
2. **The evidence.** `domains/11-independent-audit-stack`, then `records/` — the refutation register
   and the verification findings. This route is the one to take before believing any number on this
   page.
3. **The route that produced it.** `docs/01-research-journey` for the chronology and the dead ends,
   `docs/02-theory-and-references` for the theory with its partial borrowings marked.
4. **A specific domain.** Each domain directory has its own `README.md` stating what it proves and
   what it does not, and its own `VERIFICATION.md` recording, for every claim that can be re-run, the
   command, the environment, the recorded result, the observed result and the verdict. Where a
   directory records its re-runs under another name, that record is named too: the audit stack's is
   `domains/11-independent-audit-stack/docs/audit-stack-overview.md` with its `results/` directory,
   and `records/`'s is `records/verification-findings.md`.

`records/` is worth a fifth route of its own. When a number in this repository was later refuted, the
refutation is in those files in place, with the reason and the date, and the superseded text was not
edited to agree with it.

---

## 6. How to reproduce

The verification environment is built by `tooling/environment.md` and activated by
`tooling/activate.sh`. It provides one pinned Python 3.12.3 environment with the fifteen third-party
distributions the suites use, a second interpreter profile reproducing the container mathematics
pins, a locally built liboqs 0.16.0 shared library, and the three formal tools (Tamarin 1.12.0 with
Maude 3.5.1, and ProVerif 2.05) plus GraphViz. A full rebuild takes roughly 30–40 minutes and needs
no root. `tooling/packages.md` says what each package is and how far its output can be trusted;
`tooling/imports.md` says which script needs which package.

**Nearly everything reproduces from this repository alone; five layers do not.** The scripts under
`domains/01`–`domains/10` run from the repository alone, and so do most of the audit stack. The four
engines in `domains/12`–`domains/15` are installable packages with their own test suites, run with
`pytest` from the domain directory; each names the third-party packages it needs in its own README,
and each is written so that a missing engine is recorded as a run that did not happen rather than
silently skipped. Five
layers under `domains/11-independent-audit-stack` do not: they read their audited input files from a
local copy of the read-only research tree, that tree is **not shipped with this repository**, and
without it they exit 1 with a message naming `PQT_SRC`. The five, all named relative to
`domains/11-independent-audit-stack/`, are `math/math_layer.py`, `fault/fault_injection.py`,
everything under `property/`, `fixes/make_fixes.py`, and `independent-b0/gen_b0_vectors.py`. `PQT_SRC`
is the environment variable that names the tree — the read-only research source tree named in
`records/provenance.md` §1 — and this repository carries the published copies of the inputs those
layers read, mapped layer by layer in
`domains/11-independent-audit-stack/docs/inputs-and-provenance.md`; a reader who wants to re-run them
must supply the tree itself. `tooling/activate.sh` warns if `PQT_SRC` is unset and carries on.
Unaffected, and therefore runnable from a clone: `formal/bounded_checker.py`,
`formal/qpt128_quorum.spthy`, `independent-b0/b0_indep.py` and `independent-b0/check_vectors.py`, again
relative to that directory.

**Cheap checks**, seconds to a couple of minutes each. Every domain's checker is self-contained:

```
python3 domains/06-qpt128-security-target/src/qpt128_finalization.py --self-test
python3 domains/07-compact-certificate-b0/src/sidecar_free_certificate.py --self-test
```

The first runs 19 tests and the second 39. The whole extraction and signature-reduction band is
167 tests across nine scripts and runs in seconds. The operator-ledger checker executes its 23 finite
groups and reproduces its recorded JSON. In the audit stack the differential and independent-B0 layers
are cheap, and the independent B0 check is the one that agreed 6,701 times out of 6,701; the property
layer is not runnable from a clone, for the reason given above.

**Expensive checks.** The symbolic protocol model is the longest run in the tree: Tamarin over
`domains/11-independent-audit-stack/formal/qpt128_quorum.spthy` at N = 4 completes in **161.05 s**
with **all 12 lemmas verified** and exit 0. The attack lab runs its 24 violation attempts and its
framing, Grover, binding and extraction experiments in about 177 s, and the four games in about 162 s.
Those three figures were taken while the host was carrying a load average near 19 from other work,
which is why the attack lab and the games are roughly three times their recorded baselines of about
55 s and 126 s; a reader on an idle host should expect the baselines, and a reader running several at
once should expect these figures or worse. Run them one at a time. One production-parameter sanitizer
run took 2,194 seconds under ASan and UBSan; the MemorySanitizer run at production parameters timed
out at 3,600 seconds and is recorded as inconclusive.

**What cannot be reproduced here, and why.**

- **The five `PQT_SRC`-dependent layers.** They read their audited inputs from the research tree, which
  is not published here, so they cannot be re-run from a clone alone. Their results are recorded, and the
  published copies of those inputs are in this repository with
  `domains/11-independent-audit-stack/docs/inputs-and-provenance.md` mapping which layer reads which;
  what a reader has to supply is the tree itself, named in `records/provenance.md` §1.
- **The vendored proof backend and the compiled adapters.** The proof-carrier experiments were run
  against a vendored copy of an upstream succinct-proof backend (767 files, 6,524,451 bytes, at a
  pinned commit) and four compiled adapter binaries of 5,531,152, 5,533,208, 5,699,400 and 5,721,256
  bytes.
  Neither is in this repository. The Rust toolchain is not installed in the environment this
  repository was assembled in,
  the adapters contain AVX-512 instructions and were never executed on a host without them, and
  rebuilding them changes their digests — so the recorded proof sizes cannot be re-derived byte for
  byte. The rebuild command, the pinned upstream commit, the six local modifications and the digests
  are all recorded, and `domains/03-zk-carrier-experiments/VERIFICATION.md` marks every item that
  touches them `not-run` with the missing capability named precisely. No proof was re-run and no proof
  size was re-measured.
- **The model checks.** The TLA+ specification in `domains/01-accountable-quorum-foundations/formal/`
  has never been executed: the TLA+ distribution and a Java runtime were never pinned, and the
  recorded model-check outputs ship as text files, quoted as recorded. ProVerif models are written and
  unexecuted, EasyCrypt is an `admit`ted skeleton, and the TLC, CryptoMiniSat and Docker paths are
  recorded as not run with their reasons in `tooling/environment.md`.
- **The SAT experiments.** The three solver scripts behind the SAT-slope figures are analysis scripts
  and are not shipped; no solver run was finished inside its time cap, and the figures are reported as
  summaries rather than reproducible runs. The record also withdraws the ranking they were once used
  to support — a later independent analysis found the SAT behaviour does not distinguish the handle
  designs, and the ranking now rests on the algebraic model alone, with a dedicated cryptanalysis of
  the sparse regime listed open.
- **Third-party conformance vectors.** The primitives cross-check needs five NIST ACVP vector files
  that are not redistributed here. `domains/11-independent-audit-stack/primitives/vectors/SOURCE.txt`
  records the upstream commit and the SHA-256 of each file so they can be fetched and checked; without
  them the cross-check reports not run rather than passing.
- **The devnet runs.** They were made on a separate ledger implementation in another repository, on
  its own harness. Nothing from it is copied here; `docs/05-devnet-evidence` records what it measured
  and nothing else.

Where a result depends on a specific library build or commit, the build or commit is named in the text
and in the corresponding `VERIFICATION.md`, or in whichever record that domain keeps its re-runs in.
Where the recorded result and a re-run disagreed, both are kept and the disagreement is marked.

---

## 7. Provenance, naming and exclusions

**How the tree was assembled.** This repository is assembled from a research tree that is not itself
published. The assembly is driven by a file map with one row per source file, carrying the original
path, the SHA-256 digest, the size, the domain it was assigned to, the action taken, the destination
path and a note. The map has 1,369 rows: **326 files copied** to the destination it names, **113
superseded revisions** kept with their version in the filename, and **930 rows not copied** — 767
files of one vendored third-party source tree, 79 regenerable caches, 62 duplicates carried once
elsewhere, 10 binaries, 4 items of third-party devnet material, 3 scratch directories written by build
and prover runs, 3 archives whose extracted trees are the authoritative copy, and 2 raw working
transcripts whose narrative is newly written in `docs/01-research-journey/`.

The map's own summary, the exclusion policy in full, and the naming rules applied are in
`records/provenance.md`; the digests let any file here be checked against its source. The map's own
notes were scanned for machine-specific absolute paths, e-mail addresses and campaign-tracking
parameters, and carry none.

**The naming rule.** The current revision of a document or script carries no version suffix.
Superseded revisions keep theirs and live under `history/`. This makes the current revision
identifiable at a glance and leaves the version ladder intact. One consequence is recorded in the
files themselves: dropping a suffix changes the module name a script reports, and that is the only
content-level effect the rename has.

**What was excluded, and where it lives instead.** Vendored third-party source trees, binary wheels,
compiled build outputs and caches are identified in the provenance records but not copied. Three of
them a reader is most likely to want:

| Excluded | Where to obtain it |
|---|---|
| The vendored succinct-proof backend, 767 files at a pinned commit | The upstream repository and commit named in `domains/03-zk-carrier-experiments/docs/provenance.md`, with the six local modifications available as a single patch in this repository and the patch's digest recorded. |
| The four compiled adapter binaries, 5.5 MB each | Rebuild from the adapter sources in this repository with the recorded Rust version and `cargo build --locked --release`. Their digests will differ from the recorded ones, so the recorded sizes cannot be re-derived byte for byte. |
| The `pqcrypto` 0.3.4 wheel used by one experiment, 27,036,304 bytes | Install from PyPI; the wheel's SHA-256 and its verification against the publisher's release metadata are recorded in `domains/03-zk-carrier-experiments/results/dependency-provenance.json`. |

Two further kinds of material are absent for reasons outside the file map: files a document
references that were already missing from the research tree, and build products such as package
archives, whose absence the sourcing scripts report rather than paper over.

**Third-party material is not redistributed as if it were ours.** Where a result depends on a
third-party library, the version and the way it was used are recorded in the text. Where a source's
citation is incomplete, the record says so and does not fill in a reference it cannot verify.

**Scope.** The repository records research. It contains no deployed system, no network protocol, no
key management and no liveness mechanism. It is not audit-ready, not constant-time, and not a
standard. Where the work is incomplete, it says so in the same voice as the successes.
