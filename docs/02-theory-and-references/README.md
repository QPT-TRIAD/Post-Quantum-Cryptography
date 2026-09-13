# 02 — Theory and references

This package is the programme's consolidated account of every theory, lemma, bound, standard and
model that the research record uses: what each one says *as used here*, what it was used for, how the
source labels it, what citation the source gives, and — where only part of a result is used — which
part was taken and which part was not. It is the package a reader opens to check whether a claim in
`domains/` is borrowed honestly.

Nothing in this package is new. Every entry restates a statement the sources already make and names
the file it comes from. Where a source's citation is incomplete, the entry says so and does not fill
it in. Where a source's claim was later refuted, withdrawn or contradicted, the entry leads with that.

## How to read this package

| Document | What it holds |
|---|---|
| `hardness-assumptions.md` | The assumptions the security statements rest on: lattice and LWE/LWR bases, named project assumptions, primitive-level assumptions, and the boundaries where a cited result does *not* give what a reader might assume it gives. |
| `quantum-search-and-accounting.md` | Grover search and the query/gate accounting built on it, the collision and birthday terms, the union-bound composition discipline, and the refutation of the programme's original target. |
| `commitment-and-opening.md` | Commit-and-open extraction in the quantum random-oracle model: the DFMS bound in all its guises, the ZKBoo concrete backend, the compressed-oracle lemma, leftover hashing against quantum side information. |
| `zero-knowledge-and-proof-systems.md` | Proof systems and succinct backends: transparent and collaborative SNARKs, FRI/BaseFold, BARGs, VOLE-in-the-head, and the size evidence used for (and against) a compact backend. |
| `hash-based-signatures.md` | XMSS/WOTS+, LMS/HSS, SLH-DSA and SPHINCS+, their standards, their size formulas and their search terms. |
| `signature-security-reductions.md` | Fiat–Shamir-with-aborts, the corrected CMA-to-NMA reductions, threshold-signature unforgeability, the deployed signature and KEM standards used as constraints, and the resource vectors of the reductions. |
| `algebraic-and-coding-tools.md` | Finite fields, the irreducibility certificate, the linearized-polynomial kernel lemma, rank and entropy facts, hash wiring, and the small algebraic tools used inside the constructions. |
| `quorum-and-accountability-combinatorics.md` | The quorum-intersection counting identity, tracing and exculpability notions, accountable multi-signatures, and the negative-control methodology. |
| `protocol-and-ledger-assumptions.md` | Network and adversary models, the symbolic-model layer, the prior-art catalogues (contrast and scope only), and the deployment policies that constrain parameters. |
| `project-statements-and-amendments.md` | Everything the programme states in its own name: the operator ledger's eight lemmas, the A01–A28 investigation structure, the amendment taxonomy, the reader flags, and the project theorem chains. |
| `load-bearing-theories.md` | The handful of results without which the main claims do not stand, with the load path and what breaks if one fails. |
| `references.md` | The bibliography: every reference the programme cites, as the sources give it, with its verification status. |
| `gaps-and-unknowns.md` | What is refuted, withdrawn, never re-run, never installed, or cited without a complete reference. |
| `VERIFICATION.md` | Which entries were checked against a source file, by what command, with the re-run results, and every place the index and a source disagree. |

## The shape of an entry

Every entry is a block with the same fields, in the same order:

```
### <ID> — <the name as the source words it>

- **Statement as used here.** The form the programme actually uses, not the textbook form.
- **Role.** What the result is used to justify.
- **Label.** One of the seven claim labels, exactly as the source labels it.
- **Citation as the source gives it.** Verbatim where the source is verbatim; "incomplete in source
  (missing field)" where it is incomplete; "standard (added)" where the identity is added by this
  repository and not stated by the source.
- **Borrow.** Full, or partial with the part used, the part not used, and why the used part suffices.
- **Where used.** The domain and the file, as a repository-relative path.
- **Notes.** Refutations, later corrections, and the caveats the source itself attaches.
```

The IDs (`D0-01`, `L1`, `S3`, `D11-02`) are stable catalogue handles: `D<n>-<k>` is the k-th theory
entry recorded against domain `<n>` (the domains are numbered `01`–`11` in `domains/`), `L1`–`L8` are
the operator ledger's own lemma numbers, and `S1`–`S8` are the operator ledger's source tags. Two
different results can share a number across documents — `L1` in the operator ledger is a budget
inversion lemma, `L1` in the finalization script is the refutation of the original target. The
document always says which.

## The seven claim labels

The labels are the dossier specification's, and they are never upgraded:

| Label | Meaning |
|---|---|
| `[T]` | theorem-with-proof — a written proof, in the source, for the statement given. |
| `[R]` | reduction-sketch — a reduction described but not carried through in full. |
| `[L]` | model-or-ledger estimate — a number produced by a ledger, a model or an estimate. |
| `[M]` | measurement — a number observed by running something. |
| `[S]` | simulation — a number produced by simulating a process (including exact state-vector simulation). |
| `[A]` | assumption — taken as given, not proved. |
| `[C]` | conjecture — stated as believed, not proved. |

Two rules follow from this and are applied throughout:

1. **A measurement never becomes a proof.** Where a source records a test result, the entry says
   `[M]` or `[S]` and reports the number with its test. Where a source records a proof, the entry says
   `[T]` and reports the proof's actual scope — including the case where the proof is written for one
   instrument and the source says the connection to the protocol's quantity is open.
2. **A conditional theorem stays conditional.** Several project theorems are proved only under a named
   premise (a consistent-opening event, a compatible good-key event, a 9/16 contraction certificate).
   The entry carries the premise; it never restates the conclusion without it.

## Citation status

Four states appear, and they are not interchangeable:

- **complete in source** — the record contains the bibliographic identity (authors, venue, year, URL,
  arXiv or ePrint identifier).
- **standard (added)** — a well-known result whose standard identity is certain; the identity is given
  by this repository and is marked as added, never as something the source stated.
- **incomplete in source** — the record names the result without a full citation. The missing field is
  stated explicitly in the entry and in `references.md`.
- **used as a boundary / used negatively** — the source cites the result to show what it does *not*
  give. Such an entry is not evidence for the programme's claims and says so.

## Full borrowings and partial borrowings

A **full** borrowing uses the result in its own form, or restates an elementary fact that has no
form to lose. A **partial** borrowing takes a named part of a result and leaves the rest. Every
partial entry states three things: the part used, the part not used, and why the part used suffices
for the step it serves. Three recurring patterns:

- **One term of a bound.** The programme borrows the collision term of a composed error budget and
  not the rest of the source's theorem (for example the CFHL collision envelope).
- **One row of a table.** The programme borrows the extraction or the search row of a ledger and not
  the full reduction (for example the DFMS commit-and-open row, the HRS16 search row).
- **A transplant.** The programme carries a lemma set from a published specification into its own
  prover without re-deriving it (FAEST v2's multi-round soundness lemmas). The entry says
  "transplant" and gives the source's own qualification.

A result that appears in several domains in different guises is presented **once**, in the document
that owns it, and cross-referenced from the others. The guises are listed under "Where used", so a
reader who meets the number elsewhere can see whether it is the same fact or a different one. The
recurring cases are: the quorum-intersection counting identity (four domains); the DFMS commit-and-
open bound (three coefficient variants, one source); the CFHL collision envelope (four domains); the
linearized-polynomial kernel lemma (four domains); Rabin's criterion (three domains); and the
Grover search law (nine domains).

## Finding the theory behind a domain's claim

| The claim is about … | Open |
|---|---|
| the accountability invariant (conflicting certificates share named signers) | `quorum-and-accountability-combinatorics.md` |
| the QPT-128 gate work factor, or why the original target was refuted | `quantum-search-and-accounting.md`, then `load-bearing-theories.md` |
| the composed error budget and its charges (extraction, search, collision, simulation) | `quantum-search-and-accounting.md` and `commitment-and-opening.md` |
| the extraction of a conflict witness from a proof | `commitment-and-opening.md` |
| the compact-certificate size limits | `zero-knowledge-and-proof-systems.md` |
| the hidden-signer soundness statement | `zero-knowledge-and-proof-systems.md` (the FAEST v2 transplant) |
| the approval signature and its CMA-to-NMA step | `signature-security-reductions.md` |
| deployed hash-based signatures and their wire formats | `hash-based-signatures.md` |
| fields, irreducibility, the handle algebra | `algebraic-and-coding-tools.md` |
| the ledger's own lemmas and the amendment record | `project-statements-and-amendments.md` |
| the audit stack's symbolic model and its limits | `protocol-and-ledger-assumptions.md` |
| a package version, install path or container | `tooling/` — this package does not restate a version |

The programme's own statements — project lemmas, project theorem chains, measurements, simulations and
the amendment record — are catalogued together in `project-statements-and-amendments.md`. They carry no
external citation because there is none to give; the field says so rather than leaving a blank.

## What this package deliberately does not do

- It does not restate a package's version, install command or container recipe. Those live in
  `tooling/`, which is their single writer; this package names a tool only where a theory entry
  depends on what the tool returned.
- It does not recompute a size, a probability or a byte count. Every number is the source's, with the
  source's label; where a test was re-run during the build of this repository, the re-run is in
  `VERIFICATION.md` and the number is reported with both results.
- It does not resolve a source's open question. The nine reader flags recorded against the operator
  ledger, the unverified citations, and the contradictions between versions are carried forward as
  open, in `gaps-and-unknowns.md`.

## Gaps in one paragraph

Stated in full in `gaps-and-unknowns.md`. In short: the original target `Adv < 2^-128 for every QPT
adversary` is **refuted** (Grover on a 256-bit secret reaches that probability at 2^63 iterations) and
survives only as a gate work factor. The compact hidden-signer route under 27,056 bytes has no
accepted instantiation. Four tools named in the record never ran (TLC, ProVerif, EasyCrypt,
CryptoMiniSat), the Tamarin N=7 run is incomplete (and the N=4 run could not be re-observed when this
repository was built — `VERIFICATION.md` gives the command and the reason), the production-parameter
sanitizer run timed out,
and the four compiled adapter binaries that produced the recorded proof frames never executed on the
audit host. The operator ledger's 515-entry catalogue contributes no claim: its source-property fields
are uncertified by the ledger's own statement. Most of the hidden-signer domain's citations are
incomplete in source, and every entry in that domain's theory list carries that status.
