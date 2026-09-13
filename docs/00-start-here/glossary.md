# Glossary

Every term a reader needs, defined **as this project uses it** — not in its textbook form — with the
domain that elaborates it. Where the project uses a standard term in a narrower way than the
textbook, this page says so in the entry.

Definitions on this page were taken from the domain that owns the term; each entry names it. Nothing
here is defined from a summary of a summary. Two conventions throughout: a **link** points to the
document that elaborates the term, and **"narrower than the standard use"** marks a place where the
textbook meaning would mislead.

---

## 1. The object

**CE-QS — Conflict-Extractable Quorum Signatures.**
The programme's object. A quorum signature from which two conflicting certificates *publicly* expose
at least 22 seats that authorized both. Two targets are distinguished and never conflated:
**Target A** is the deployable system — a compact threshold signature on the consensus hot path, an
external accountability sidecar of individually attributable evidence, and a cryptographic binding
between the two. **Target B** is the frontier — a compact quorum signature from which a conflicting
signer can be extracted directly from two conflicting certificates with no O(n) sidecar to retrieve.
Target B is recorded as **open**.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`.

**Quorum certificate.**
A portable artifact proving that a quorum approved a statement.

**Compact quorum certificate.**
A quorum certificate that proves a quorum approved a statement **without naming anyone in it**. This
is a trade, not an oversight: keeping the individual signatures makes the certificate linear in the
signer count, which is the cost the design exists to remove; replacing them with one aggregate or
threshold signature removes the cost and the attribution together. Two compact certificates on two
conflicting statements therefore prove that *someone* misbehaved while leaving no way to punish
anyone for it — the certificate that shows the crime also hides the criminal.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`.

**Sidecar.**
A separate evidence file carried alongside the certificate. The programme's headline result is a
certificate that needs **no sidecar**: no external leaf list, no transcript, and no secret opener.
Target A's design does use an accountability sidecar; Target B and the B0 profile do not. Read the
word in the context of whichever target the sentence is about.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`,
`domains/07-compact-certificate-b0/README.md`.

**Conflict extraction.**
Recovering, from two accepted certificates on conflicting statements, the identity of seats that
authorized both — publicly, with no secret input. The named set must be publicly computable from the
two certificates alone, identifiable (a seat index, not an opaque handle), at least 22 seats, and
backed by a reduction that terminates in a standard assumption at a stated cost rather than in "the
handles differ".
Elaborated: `domains/05-extraction-and-signature-reductions/README.md`,
`domains/01-accountable-quorum-foundations/docs/definitions-and-conflict-extraction.md`.

---

## 2. The committee and the counting fact

**Seat.**
One validator position. Voting is **equal-seat**, not stake-weighted, and corruption is static within
an epoch with `c ≤ f`.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`.

**Committee.**
`n = 3f + 1` validators, with `n ≤ 64` at the first implementation target. The **reference committee**
used throughout the repository is **N = 64 seats** with **f = 21** faulty.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`,
`domains/07-compact-certificate-b0/docs/b0-wire-spec.md`.

**Quorum.**
`q = 2f + 1` signers, written `T = 2f + 1` where it is the threshold of the signing scheme. At the
reference committee **q = 43**.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`.

**Quorum intersection.**
Any two quorums intersect in at least `2q − N` seats. At the reference committee
`2·43 − 64 = 22`. This is the single counting fact the repository states in one place, in the general
form.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`.

**22 double-authorizers.**
At the reference committee, a conflict between two quorum certificates requires **at least 22 seats
to have authorized both statements**, while at most `f = 21` seats are Byzantine — so at least one of
the 22 is honest. That is the domain's core requirement: a conflict cannot occur without an honest
seat having signed twice, unless the signature primitive itself failed. `f + 1` is the same fact in
its general form (`22 = f + 1` at this committee); the source states the `f + 1` form and the 22 is
arithmetic on the source's two constants.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`.

**Conflict domain.**
The unit over which a signer must not equivocate: `d = (epoch, height, view, phase)`. A durable vote
log with persist-before-send ordering enforces it.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`.

**Blame.**
Attribution of equivocation to a named seat. Two rules fix what may count as evidence: **silence is
never blame evidence**, and a share is blamable **only through its authenticated envelope**.
Individually attributable evidence is a signed accountability receipt, carried in a sidecar committed
by a Merkle root, with anchoring conditioned on the voter holding the evidence.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`.

**Epoch barrier.**
An epoch change is a **safety boundary**, not an administrative event. An epoch is crossed only after
a terminal block reaches ordinary finality, a seal certificate is formed over the finalized boundary,
and the **complete next public configuration is embedded in that boundary** rather than referenced by
hash. The barrier is what prevents two parts of the system from finalizing different boundaries around
the change. The TLA+ model in that domain is the **specification** of the mechanism — the v0.6
revision, the only one preserved — and it has **never been executed** by TLC or TLAPS. It is not a
verification result.
Elaborated: `domains/01-accountable-quorum-foundations/README.md`,
`domains/01-accountable-quorum-foundations/docs/epoch-barrier-specification.md`.

---

## 3. The certificate on the wire

**Frame.**
The bytes a certificate occupies. Both profiles share one frame layout: a **208-byte header**, then a
payload. The frame length is `208 + 8 + 43·W = 216 + 43·W` for B0, where `W` is the signature width.
Elaborated: `domains/07-compact-certificate-b0/docs/construction.md` §2.

**Header.**
208 bytes, `struct '>4sHH64s64s64sHHI'`: `magic` (`CQ44`) ‖ `version` (44) ‖ `suite` ‖ `cfg` (64) ‖
`domain` (64) ‖ `message` (64) ‖ `count` ‖ `width` ‖ `payload_len`. The 208-byte offsets are **not**
the CEQS29 body offsets (16/80/144) used by earlier revisions; that difference is a recorded finding.
Elaborated: `domains/07-compact-certificate-b0/docs/b0-wire-spec.md`.

**`cfg`.**
The authenticated configuration: `cfg = H(b'CQ44/cfg/B0', scheme_id, pk_0, …, pk_63)`, where `H` is
SHAKE256 with an eight-byte big-endian length prefix before the label and before every part, squeezed
to 64 bytes. `cfg` is inside the signed vote message, so a signature is bound to the exact 64-key
registry. Validation of the registry happens inside `cfg_b0`, so every verification that recomputes
`cfg` validates it.
Elaborated: `domains/07-compact-certificate-b0/docs/construction.md` §2.2–2.3.

**Registry.**
Exactly 64 distinct non-empty public keys `pk_0 … pk_63`, plus a byte string `scheme_id`.
Elaborated: `domains/07-compact-certificate-b0/docs/b0-wire-spec.md`.

**Wire / wire specification.**
The normative byte-level specification an implementer works from — the "wire format". The current B0
wire specification is normative at v1.44, and its §11 records the clarifications made normative *after*
the independent implementation found them.
Elaborated: `domains/07-compact-certificate-b0/docs/b0-wire-spec.md`,
`docs/03-construction/wire-format.md`.

**Bitmap (signer bitmap).**
The 8-byte field that makes B0's signer set **public**: the seats that signed are in the clear. B0
therefore does not hide signers, and the domain says so explicitly rather than leaving it to be
assumed.
Elaborated: `domains/07-compact-certificate-b0/README.md`.

**Handle.**
B1's 128-byte per-seat payload element, which replaces B0's signature. In the B1 window it is
`pair = SHAKE256(b'CEQS/P1' ‖ x ‖ D)[:128]`, split into a link `L = pair[:64]` and
`Z = int(pair[64:]) XOR mul(decode(message), i+1)` over a GF(2) polynomial ring; the XOR with a
multiple of the message is what makes two certificates on different messages collide on a seat's link.
**In domain 08's Mode B the handle is a different object** — `Z_i = r_i^7 ⊕ L_c(s_i)` with `L_c`
`F₂`-linear in `s` — and the two are not interchangeable. See *B1 / Mode S vs Mode B* in §4.
Elaborated: `domains/07-compact-certificate-b0/docs/construction.md` §6.

**Size gate.**
`W ≤ (32,768 − 216) // 43 = 32,552 // 43 = 757`. At 757 bytes the frame is 32,767 and fits; at 758 it
is 32,810 and does not. Every scheme wider than 757 bytes is excluded by arithmetic alone, before any
cryptographic question is asked.
Elaborated: `domains/07-compact-certificate-b0/docs/construction.md` §4.

**Contents contract.**
The v1.24 contract layout that both profiles are measured against: a 208-byte header, 43 handles of
128 bytes (5,504 bytes) and one joint proof of at most 27,056 bytes — 32,768 in total. B0's
substitution of a bitmap plus 43 fixed-width signatures is permitted by the contract, which notes
that replacing the handles requires a different public extraction mechanism.
Elaborated: `domains/02-ceqs-construction-evolution/docs/32kib-contents-contract.md`.

**Profile B0 / profile B1.**
`B0` (suite `0x44B0`) publishes the signer set: an 8-byte bitmap followed by 43 fixed-width
signatures. `B1` (suite `0x44B1`, "Mode S") keeps the contract layout and hides the signers:
43 handles followed by one proof. The suite id is in the header, so the two are distinguishable on
the wire.
Elaborated: `domains/07-compact-certificate-b0/README.md`,
`docs/03-construction/profiles.md`.

**struct-only / `STRUCTURE_ONLY_NO_QUALIFIED_PROOF`.**
The status `verify_b1` returns. It is a **computed** value, not a hard-coded refusal: `status` becomes
`QUALIFIED_PROOF_VERIFIED` only if a backend declares `qualified = True` *and* the proof is
structurally accepted, and `authorization_verified` is exactly `qualified and structurally_accepted`.
The only backend in the file is a structure-only test backend with `qualified = False`, so the value
is always `False` here — because nothing in the repository can truthfully make the backend claim.
Elaborated: `domains/07-compact-certificate-b0/docs/construction.md` §6.

**`ALGEBRAIC_CANDIDATES_ONLY`.**
The status of B1's extraction, which merges two handle lists on the link and recovers a seat per
matched link. It reports that without two *qualified* authorization proofs an extracted seat is a
**candidate**, not an attribution. Its stated precondition is
`requires_before_attribution: 'Authenticate cfg and verify two qualified B1 authorization proofs.'`
Elaborated: `domains/07-compact-certificate-b0/docs/construction.md` §6.

**Seat privacy.**
The property B0 explicitly does **not** have, stated in the domain exactly rather than by implication:
the bitmap is in the clear, so the seats that signed are public.
Elaborated: `domains/07-compact-certificate-b0/docs/construction.md` §3.5.

---

## 4. The two hidden-signer lineages — read this before using "B1" or "Mode B"

**B1 / Mode S (domain 07).**
The B1 profile as specified in the compact-certificate domain: frame, relation, algebraic extractor
and QPT-128 ledger fixed, and **no qualified proof backend**. `verify_b1` never reports an
authorization. This is the lineage the top-level README's §1.3 and the B1 row of the ledger verdicts
describe.

**Mode B (domain 08).**
A **second, separate** hidden-signer line, recorded in `domains/08-hidden-signers`. It is a *tested
design* with a size **estimate** and an attack-based ledger, and its own document says so: no
zero-knowledge backend, no security theorem for the instantiated proof system, no collaborative
prover, and no dedicated cryptanalysis beyond the attack families tested. Its production form is
called **Mode B-r**. Its parameters are named `b` (leaves per tree), `τ` (repetitions) and `w_g`
(grinding bits); the production setting recorded is `b = 20, τ = 11, w_g = 16`.
Elaborated: `domains/08-hidden-signers/docs/mode-b-security.md`,
`domains/08-hidden-signers/docs/hidden-signer-32kib.md`.

**Why the distinction matters.** The two lineages use the same words — "hidden signers", "B1", "handle",
"32 KiB" — for different objects, and they reach different conclusions about what exists. Domain 07's
statement is "no qualified proof backend exists in this repository". Domain 08 records a C prover that
produced a 30,684-byte hidden-signer certificate that verified and extracted its 22 seats, with its
size given as an estimate and its limitations listed. **A reader must not carry a claim from one
lineage into the other.** The top-level README keeps them in separate subsections for this reason.

---

## 5. The security target and its vocabulary

**QPT-128.**
The programme's security target, stated as a **gate work factor** rather than an advantage bound.
Three definitions appear and they are not interchangeable:

- **D1 — adopted.** An adversary with fewer than `2^128` quantum gates wins with probability below
  `1/3`.
- **D2 — the rigorous strengthening.** `Pr[Win(A)] ≤ G(A) · 2^−130`, a per-gate ratio; D2 implies D1.
- **D3 — REFUTED.** `Pr[Win(A)] < 2^−128` for *every* QPT adversary. Lemma L1 shows this is
  unattainable for anything with a 256-bit secret: `2^63` Grover iterations already exceed `2^−128`.

Elaborated: `domains/06-qpt128-security-target/README.md`,
`domains/06-qpt128-security-target/docs/qpt128-finalization.md` §1.

**Gate units and query units.**
Two accounting units in the ledger. Counting **one gate per oracle query** is not enough — that is
Lemma L2 — so each query is charged its circuit cost (the reading of NIST category 5). The distinction
is not academic: B1 Mode S passes in gate units (+29.4 bits) and **fails** in query units (−40.0), and
B0's row states its margin in gate units with a separate query-unit figure. `r` denotes the ratio used
to convert between them (the repository records `r = 553` gate units against `640` query units).
Elaborated: `domains/06-qpt128-security-target/README.md`.

**Ledger (the QPT-128 ledger).**
The exact-rational computation that decides which instantiations meet D1/D2. Every row is an exact
rational comparison in the evidence file, not a floating-point approximation.
Elaborated: `domains/06-qpt128-security-target/docs/ledger.md`.

**Lemma L1 / L2 / L5 (domain 06 numbering).**
`L1` refutes D3. `L2` shows that one gate per query is the wrong unit. `L5` is the extraction-overhead
lemma: quantum online extraction runs in `O(q²)` time, so a secret hidden inside a proof needs roughly
twice the generic security of a secret sent in the clear — the single fact that decides which
instantiations pass. **The symbol `L1` means something else in the operator ledger** (a budget
inversion lemma); always check which document a lemma number comes from.
Elaborated: `domains/06-qpt128-security-target/README.md`,
`docs/02-theory-and-references/README.md` (which states the collision explicitly).

**Theorem A / Theorem B / Theorem C.**
`A` — B0's accountability, non-frameability and safety, a theorem with proof **conditional on `A-sig`**
(EUF-CMA of the chosen non-FIPS category-5 candidate at generic strength). `B` — the hidden-signer counterpart, v1.43.
`C` — a size bound for **witness-committing** proof families (KKW / BN++ / FAEST-style): the
27,056-byte slot admits at most 359 bits of witness per seat at `N = 2^16`. Theorem C is a **necessary
condition for those families**, and the domain states in the same breath that it is **not a universal
lower bound**.
Elaborated: `domains/07-compact-certificate-b0/docs/sidecar-free-finalization.md`,
`domains/07-compact-certificate-b0/docs/construction.md` §7.3.

**`A-sig` and the other named assumptions.**
`A-sig` — the chosen non-FIPS category-5 candidate is EUF-CMA at generic strength. Domain 08 names five
more for its own line: `A-F1` (one-wayness with handle), `A-F2` (binding), `A-QROM` (the
domain-separated SHAKE256 instances are quantum-accessible random oracles), `A-P` (privacy), and
`A-Prove` (the proof is produced by a party that learns the 43 openings and behaves honestly — an
*essential* assumption, not a technical one). **A named assumption is not a theorem**; the top-level
README's validation list says so as its item 3.
Elaborated: `domains/06-qpt128-security-target/README.md`,
`domains/08-hidden-signers/docs/mode-b-security.md` §2.

**QROM.**
The quantum random-oracle model. The programme's security statements that rest on it say so, and the
QROM heuristic for domain-separated SHAKE256 is named as an assumption rather than derived.
Elaborated: `domains/08-hidden-signers/docs/mode-b-security.md` §2,
`docs/02-theory-and-references/commitment-and-opening.md`.

---

## 6. The extraction machinery

**R29 relation.**
The authorization relation of the v1.29 construction — the relation the extractor targets. The
domain states that its concrete circuit backend does **not** cover the R29 relation, and that an
oracle-respecting authorization-consistent extractor for the full relation is *assumed*, not proved.
Elaborated: `domains/05-extraction-and-signature-reductions/README.md`.

**Division-free public decoder.**
The v1.34 decoder over GF(2^512) for the R29 body, with a field irreducibility certificate. It is a
closed component with a conditional correctness proof. Its status is
`ALGEBRAIC_CANDIDATES_ONLY`: manufactured handles decode to 22 candidates with no witness at all, and
**algebraic acceptance is not authorization**.
Elaborated: `domains/05-extraction-and-signature-reductions/docs/extraction-argument.md`.

**Joint lift.**
The v1.35 theorem that obtains two witnesses from **one** adversary execution and one terminal
database measurement, with a single additive error `κ_J` and multiplicative loss `L_J = 1`. Proved
conditionally on premises P1–P4 and an imported readout lemma.
Elaborated: `domains/05-extraction-and-signature-reductions/docs/joint-extractor-lift.md`.

**`p_triv`.**
The trivial-acceptance probability of the ZKBoo-style three-share circuit backend, `(3/4)^r`. It
appears in the composed error budget as a charge on the proof.
Elaborated: `domains/05-extraction-and-signature-reductions/README.md`,
`docs/02-theory-and-references/commitment-and-opening.md`.

**DFMS bound.**
The commit-and-open extraction bound borrowed from DFMS 2022. The repository records **two coefficient
variants** — `(20ℓ+60)` in the v1.35 file and `(22ℓ+60)` in the later v1.43 material — and states the
discrepancy rather than silently substituting one for the other. The direction is not in doubt
(`22 > 20` is the more conservative), but the exact theorem statement was not re-verified against the
paper here.
Elaborated: `domains/05-extraction-and-signature-reductions/README.md`.

**Transplant.**
A specific kind of borrowing: carrying a lemma set from a published specification into the programme's
own prover **without re-deriving it** — the FAEST v2 multi-round soundness lemmas (Lemma 9.39) are the
recurring instance. Entries that use it say "transplant" and give the source's own qualification.
Elaborated: `docs/02-theory-and-references/README.md`,
`domains/08-hidden-signers/docs/mode-b-security.md` §5.

---

## 7. The claim labels — the vocabulary of evidence

**`[T]` `[R]` `[L]` `[M]` `[S]` `[A]` `[C]`.**
The seven claim labels: theorem-with-proof, reduction-sketch, model-or-ledger estimate, measurement,
simulation, assumption, conjecture. Defined once in `docs/02-theory-and-references/README.md` and
restated, with the bar each must clear and two worked instances each, in
[`claim-labels.md`](claim-labels.md).

**The label set is the programme's own convention, not an external standard.** No source in this
repository attributes it to a standards body or to any external work; `docs/02-theory-and-
references/README.md` describes the labels as **the dossier specification's** — the assembly's own
working document, which is not in this repository (*dossier*, §11). That matters because the labels
carry the repository's whole evidence discipline: they are the programme's own vocabulary for it, and a
reader who has met a similarly-named label elsewhere should not assume it means the same thing here.
The repository's own `[C]` already means two different things in two different documents, as noted
above.

**A label is never upgraded.** And a claim whose re-run does not reproduce is **withdrawn in public,
with the reason** — the repository's rule, stated in full in [`claim-labels.md`](claim-labels.md).

**Citation status: complete in source / standard (added) / incomplete in source / used as a boundary.**
Four states, not interchangeable. *Complete in source* — the record contains the full bibliographic
identity. *Standard (added)* — a well-known result whose identity is certain, given by the repository
and marked as added, never as something the source stated. *Incomplete in source* — the source names
the result without a full citation, and the entry says which field is missing instead of filling it in.
*Used as a boundary / used negatively* — the source cites the result to show what it does **not** give;
such an entry is not evidence for the programme's claims and says so.
Elaborated: `docs/02-theory-and-references/README.md`.

**Borrow: full / partial / transplant.**
A **full** borrowing uses the result in its own form, or restates an elementary fact that has no form
to lose. A **partial** borrowing takes a named part and leaves the rest; every partial entry states
the part used, the part not used, and why the part used suffices for the step it serves. Recurring
partial patterns: one term of a bound, one row of a table, and the transplant above.
Elaborated: `docs/02-theory-and-references/README.md`, `docs/02-theory-and-references/*.md`.

**A warning about `[C]`.** `domains/03-zk-carrier-experiments/docs/theory-as-used.md` uses the same
symbol `[C]` for **"construction argument"**, not for "conjecture", and uses `[T]`, `[A]` and `[M]`
with the meanings above. The two conventions are both in the repository. Check which legend a
document states before reading its labels.
Elaborated: `domains/03-zk-carrier-experiments/docs/theory-as-used.md`.

---

## 8. Reproduction vocabulary

**Verdict vocabulary for a re-run.** `reproduced`; `reproduced-with-difference` (both results kept, and
the difference marked); `not-reproducible` (with the missing capability named); `not-run` (with the
reason). Every domain's `VERIFICATION.md` carries a row per item in the form
`item | command | environment | expected (recorded) | observed | verdict | notes`.
Elaborated: `tooling/environment.md`, and each domain's `VERIFICATION.md`.

**`PQT_ENV`.**
The environment root, derived from `tooling/activate.sh`'s own location so the tree can be cloned
anywhere. It holds `venv/`, `liboqs/` and `tools/`.

**`PQT_SRC`.**
A local copy of the read-only research tree that some harnesses read their input files from. It is
**not shipped with this repository** and is never guessed. `tooling/activate.sh` warns if it is unset.
The scripts under `domains/01`–`domains/10` do not read it; several layers under
`domains/11-independent-audit-stack` do, and `domains/11-independent-audit-stack/docs/inputs-and-provenance.md`
maps every input. See [`reproduction.md`](reproduction.md) for which layers are affected.
Elaborated: `tooling/activate.sh`, `domains/11-independent-audit-stack/README.md`.

**"The research tree".**
The unpublished source tree this repository was assembled from. The repository is not that tree; it is
assembled from it under a file map with one row per source file.
Elaborated: `records/provenance.md`, and §7 of the top-level `README.md`.

---

## 9. Infrastructure studies (domain 10)

Six deployment studies, each labelled `S1`–`S6`, each measured and none a deployment. The terms below
are used as domain 10 uses them, and several are **narrower than the standard use** — in every case
because the study measures one configuration of the mechanism rather than the mechanism in general.

**S1–S6.** `S1` firmware signing; `S2` DNSSEC; `S3` TLS and the Web PKI; `S4` constrained broadcast
(ICS, satellite, medical links); `S5` smart cards, secure elements and HSMs; `S6` category migration
and agility. Elaborated: `domains/10-digital-infrastructure/docs/pq-infra-program.md`.

**MTL ladder.** Merkle tree ladder mode for hash-based signatures: one underlying signature per
ladder, with a per-record **condensed** proof. *Condensed signature* at `2^20` leaves is 645 bytes
each — the measurement that refuted the hypothesis "MTL mode alone rescues NXDOMAIN". **Narrower than
the standard use:** the study measures the draft's ladder at the leaf counts and shard sizes it names.

**Canonical-order multiproof.** A glue the programme adds: RRsets are put in the ladder in canonical
order so that several records plus their denial can be proven with **one** Merkle multiproof.
Measured worst case 988 bytes at `2^10` names, against 1,071 bytes for three separate condensed
signatures. Elaborated: `domains/10-digital-infrastructure/docs/pq-infra-program.md`.

**NSEC / NSEC3.** The two authenticated-denial mechanisms of DNSSEC, used as the denial component of
the DNSSEC study. They are the reason the study reports two worst cases: 1,530 bytes (NSEC) and
1,839 bytes (NSEC3) on real wire format. **Narrower than the standard use:** the study's numbers are
for the zone shape it names — 3×20-character labels, a 30-character apex, two keys double-signing
during rollover, `2^14`-leaf shards.

**MTC.** Merkle Tree Certificates — the transparency-log-style certificate mechanism used in the TLS
study. The study carries an important caveat: MTC's **index-free node hashing has the same
multi-target exposure** as the unprefixed DNSSEC nodes (finding S2-006). Elaborated:
`domains/10-digital-infrastructure/docs/pq-infra-audit.md`.

**KEMTLS.** Replacing the handshake signature with a KEM, so the server flight needs no per-handshake
signing. The study's measured figure is **4,148 bytes** exact on real DER/QUIC wire format (the v2.0
model said 4,280). Elaborated: `domains/10-digital-infrastructure/docs/pq-infra-audit.md`.

**TESLA.** The broadcast authentication mechanism, deployed with 128-bit keys in Galileo's OSNMA. The
study's contribution is an audited 256-bit TESLA anchored by LMS, measured at **52 bytes per message
in steady state** — with the correction that the first `d` packets cost about 20 bytes and link
framing adds 26–30 bytes, so "52 bytes/message" is a **steady-state** figure and not a per-message
bound. Elaborated: `domains/10-digital-infrastructure/docs/pq-infra-audit.md`.

**BDS traversal.** The state-traversal algorithm for on-card hash-based signing, used in the smart-card
study. **Narrower than the standard use, twice over:** the study corrects its own earlier figure — the
worst round at `h = 20` is 95,775 hashes, not 86,720, because the BDS worst round is `(h−k)/2 + 1`
leaves — and the peak state is **2,148 bytes** at `h = 20`, not the 664 bytes the earlier revision
recorded at `h = 8`. Elaborated: `domains/10-digital-infrastructure/docs/pq-infra-audit.md`.

**LM-OTS / LMS / HSS; typecode.** The Leighton–Micali one-time signature, the LMS tree over it, and the
hierarchical variant; the **typecode** names the parameter set on the wire. The study's headline
verdict turns on it: `n = 32` passes at `2^146`, while NSA-preferred `n = 24` fails at `2^114`.
**Narrower than the standard use:** these are the RFC 8554 mechanisms at the typecodes the study
tests, and the S2 attack surface is measured only at `n ≤ 16`.

**Position-prefixed node hashing.** The audit's design finding, applying to S2 and to S3's MTC
prototype: hashing interior nodes as `H(l‖r)` gives `2^-n` per query for a single structure, but an
adversary holding `T` signed nodes across all zones tests one evaluation against all `T`. At
`n = 256`, `T = 2^40` that is 2^126 gates — inside the 2^128 budget. The fix costs zero bytes:
`H(node, ladder_id, rung, level, index, l, r)`.

**Cycle counts.** Every cycle-count figure in the infrastructure studies is labelled as taken from the
**literature**, not measured on the study's host. It is on the audit's untestable-assumptions list.
Elaborated: `domains/10-digital-infrastructure/docs/pq-infra-audit.md`.

---

## 10. The audit stack and the games (domains 11 and 09)

**The seven layers (domain 11).** `math/` (exact recomputation), `formal/` (three protocol models),
`primitives/` (cross-validation against other implementations and conformance vectors),
`implementation/` (sanitizers and fuzzing), `property/` (property and differential testing),
`fault/` (fault injection over the certificate pipeline), `independent-b0/` (a spec-only second
implementation of the B0 wire format). Each layer attacks a claim with a different tool.
Elaborated: `domains/11-independent-audit-stack/README.md`.

**"Independent in method, not in organisation."**
The audit stack's own statement of what its independence is and is not. It is independent in method —
different tools, models and implementations — and **not** independent organisationally. Two of its
checks are genuinely third-party. The independent *second implementation of the whole construction*
remains open: only the B0 extraction rule and LMS have independent counterparts.
Elaborated: `domains/11-independent-audit-stack/README.md`.

**F1–F6; S1–S18 (domain 11).**
The audit's findings — one real leak, one vacuous verifier, one upstream implementation bug, two
input-validation defects, one documented size asymmetry — and the specification gaps the independent
implementation found (18 of them, with S1–S4 observable).
Elaborated: `domains/11-independent-audit-stack/docs/audit-stack-overview.md`.

**FRAME / SUPPRESS / EVADE / SAFETY (domain 09).**
Four games, stated **as games** and then measured: FRAME recovers an opening of an honest seat's
registry key from its published handle; SUPPRESS makes extraction return nothing by finding two
messages whose challenge maps are equal; EVADE, with at least 22 corrupt seats, makes extraction name
fewer than 22; SAFETY, with at most 21 corrupt seats, produces two valid conflicting certificates at
all. Three of the four are winnable at toy parameters — deliberately, because a game nobody can win
teaches nothing about its exponent. SAFETY's threshold of 22 is the counting fact, tested
exhaustively for every corruption level 0–23.
Elaborated: `domains/09-security-games-and-attack-lab/src/ceqs_games.py`,
`domains/09-security-games-and-attack-lab/results/attack-lab-results.md`.

**"Toy parameters" / "deliberately weak parameters".**
8–14-bit openings and expansions of 2–12 in the games and the attack lab. **No result at toy
parameters is a security claim for the production parameters** (256-bit openings, expansion 512); the
measured exponents test the *scaling* of the real attacks, not the production security level. The
phrases appear in the repository's own output for exactly this reason.
Elaborated: `domains/09-security-games-and-attack-lab/results/attack-lab-results.md`.

---

## 11. Records and provenance

**The refutation register.** `records/failed-assumptions.md` — every hypothesis that failed, with an
identifier, the hypothesis as stated, the verdict and the fix. Prefixes group it by investigation: `Q`
for the CE-QS / QPT-128 line, `I` for the infrastructure line, `A` for the audit line, `F` for the
findings. **`A28`** is the entry that withdraws the "16/16 and 16/16" property figure; **`Q1`** is the
entry that refutes the original security target.
Elaborated: `records/failed-assumptions.md`, `records/README.md`.

**Provenance and the file map.** The repository is assembled from an unpublished research tree under a
file map with one row per source file, carrying the original path, the SHA-256 digest, the size, the
assigned domain, the action taken, the destination path and a note. The map has 1,369 rows, of which
930 were not copied. The digests let any file here be checked against its source.
Elaborated: `records/provenance.md`, §7 of the top-level `README.md`.

**`dossier`.** One of the assembly's own working documents: a reading of a body of source material that
records what it contained, what should be carried into this repository and what should not. The notes
in the file map cite them by name — `D0 dossier`, `D3 dossier`, `D11 dossier` — as the point at which
each exclusion decision was taken.
**A dossier is not in this repository, and is not a pointer to follow.** They describe the assembly
rather than the cryptography, and they quote the same machine-specific strings and third-party material
the repository excludes. So where a note says "excluded per the D3 dossier", the note itself is the
record of what that dossier said on that point. Where the underlying reason is something a reader can
check, the note states it directly: the vendored-tree note gives the upstream repository, the commit
and the licence — the checkable part — and names the dossier only as where the decision was made.
Elaborated: `records/provenance.md` §1 and §7.

**"The brief" and "the coordinator".** The same kind of term: a description and a role from the
assembly, neither of them in this repository. Where a package compares what it did against a
description it cannot show you, it states the thing it did on its own terms instead; the record of the
decisions taken is `records/provenance.md` §1, §5 and §7.

**The naming rule.** The current revision of a document or script carries **no version suffix**;
superseded revisions keep theirs and live under `history/`. One consequence is recorded in the files
themselves: dropping a suffix changes the module name a script reports, and that is the only
content-level effect the rename has.
Elaborated: §7 of the top-level `README.md`, and each domain's `VERIFICATION.md`.

**Not-run, and why — the recurring list.** The vendored proof backend and the compiled adapter
binaries (excluded; the recorded proof sizes cannot be re-derived byte for byte); the TLA+ model
checks (never executed; no pinned distribution or Java runtime); ProVerif (models written,
unexecuted); EasyCrypt (an admitted skeleton); the SAT experiments (scripts not shipped; no run
finished inside its time cap); the third-party conformance vectors (not redistributed; the fetch
instructions ship instead); the devnet runs (a separate repository). The full list, with what each
would need, is in [`reproduction.md`](reproduction.md) and in `tooling/environment.md` §8.
