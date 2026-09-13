# Protocol, network and ledger assumptions

This document holds the models the protocol-level reasoning is carried out **inside**: the network and
adversary models, the symbolic-model layer and its machine-checked results, the prior-art catalogues
that are recorded for contrast and scope rather than borrowed, and the deployment policies that
constrain parameters.

Two cautions run through the group. First, a catalogue entry is not a borrowing: the catalogs in §5
exist to say what has been done elsewhere, and the source marks most of them contrast-only or
scope-only. Second, a symbolic-model result is a theorem **within the model at small N**, and the record
says how it reaches the deployed parameters — through the counting identity of
`quorum-and-accountability-combinatorics.md`, not by the model's own size.

---

## 1. Network and adversary models

### D2b-15 — GST / eventual synchrony

- **Statement as used here.** The network model of the distributed prover: eventual synchrony after an
  unknown global stabilisation time.
- **Role.** Liveness model.
- **Label.** `[T]`.
- **Citation as the source gives it.** **Standard (added):** Dwork–Lynch–Stockmeyer, JACM 1988.
- **Borrow.** Full.
- **Where used.** `domains/02-ceqs-construction-evolution/docs/` (v1.4, lines 777–781).

### D6-15 — Liveness

- **Statement as used here.** A **separate conditional theorem** for liveness — conditional, and
  separate from the safety and accountability results.
- **Role.** Liveness of the quorum protocol.
- **Label.** `[R]` conditional.
- **Citation as the source gives it.** Project.
- **Borrow.** Partial.
- **Where used.** `domains/06-qpt128-security-target/` (v1.19 §4).
- **Notes.** Liveness is not covered by the safety theorems and must not be reported as if it were.

### D11-02 — Dolev–Yao symbolic model with the `signing` equational theory

- **Statement as used here.** The symbolic adversary model in which the audit stack's protocol lemmas
  are proved: all-traces lemmas A1, A2, A, D2, D1, B, C1, C2 and E1 are satisfied **in the N = 4 model**.
- **Role.** Machine-checked protocol properties.
- **Label.** `[T]` — the source's own qualification: "theorem-with-proof **within the symbolic model at
  N = 4** (machine-checked); N = 7 partial; ProVerif = expectation only (conjecture)".
- **Citation as the source gives it.** Full as a modelling choice.
- **Borrow.** Full within the model.
- **Where used.** `domains/11-independent-audit-stack/formal/qpt128_quorum.spthy`.
- **Notes.**
  - The N = 4 run verified **12/12 lemmas in 111.31 s** (v0.1) and **126.74 s** (v0.2 re-run). E2 is an
    explicit attack at **exactly 2 corruptions**, which is what makes the bound tight at that point.
  - **The re-run during the build of this repository did not reproduce that.** The prover and Maude are
    present and `tamarin-prover test` returns "All tests successful", but the proof run was killed
    during the first lemma on a host with about 7 GB free — the same memory limit the record documents
    for N = 7. The figure above is therefore carried at the record's status, not as a re-observed one.
    See `VERIFICATION.md`.
  - The **N = 7 run is partial**: 6 verified, 5–7 incomplete, **0 falsified** (lemmas A, B, C1, C2, E2,
    D1 and E1 were not completed).
  - "N = 4/7 proofs reach N = 64 only through the same counting theorem" — the record's own sentence.
    The model size is not a security parameter.
  - The model has no network messages for votes, so replay and derivation are abstracted away; there is
    no refinement link from the model to the Python or C implementations.

### D11-03 — Tamarin backward search and constraint solving

- **Statement as used here.** The tool semantics on which the symbolic results rest: `all-traces`
  lemmas are negated and a constraint system built by backward search, `[reuse]` makes a proven lemma
  available as a hypothesis, and `hide_lemma` removes it.
- **Role.** How the prover's output is to be trusted.
- **Label.** Tool semantics.
- **Citation as the source gives it.** Tamarin 1.12.0 (with Maude 3.5.1).
- **Borrow.** Full.
- **Where used.** `domains/11-independent-audit-stack/` (the formal layer).
- **Notes.** The exit-code vocabulary matters when reading the record: **251** = heap exhausted,
  **137** = out-of-memory, **124** = timeout. A reader who sees "the run did not finish" should check
  which of the three it was. Version mismatch is also recorded: the container pins Tamarin 1.10.0 and
  Maude 3.5 while the host ran 1.12.0 and 3.5.1. That mismatch has a consequence beyond the version
  string: the recorded command line passes the heap cap as `-M2500m`, which **Tamarin 1.12.0 rejects**
  outright (`Unknown flag: -M`), while on 1.12.0 the same cap must be written as an RTS option
  (`+RTS -M… -RTS`). A reader who reproduces the recorded command on the newer binary will see it fail
  before any lemma is attempted. The record does not state which of the two versions accepted the
  original flag; the container's pin is recorded separately and is the likelier source.

---

## 2. Primitive-layer independence of the audit stack

### D11-10 — NIST ACVP vectors and independent projections

- **Statement as used here.** Cross-validation of the deployed primitives against a second
  implementation, with the external-μ Algorithm 8 derivation taken from library internals.
- **Role.** Primitive-layer independence.
- **Label.** `[M]`.
- **Citation as the source gives it.** ACVP (NIST) vectors, master commit
  `975de31eb83d87039ec88934fdc47d8c312b892d` (2026-08-12); DER OIDs as given. Full as recorded.
- **Borrow.** Full as recorded.
- **Where used.** `domains/11-independent-audit-stack/primitives/cross_validate.py`.
- **Notes.** Two limits the source records and this package repeats: the harness **computes** part of
  what it calls the reference (the M′ and external-μ derivations), and the ACVP vector files themselves
  are **not in the archive** — only a `SOURCE.txt` with their recorded SHA-256 digests. The vector
  material must be described as recorded, not as shipped.

---

## 3. Deployment policy and size constraints

### D10-09 — KEMTLS, RFC 4082 (TESLA) and Galileo OSNMA

- **Statement as used here.** The TLS/PKI and broadcast-authentication baselines for the infrastructure
  routes.
- **Role.** Deployment baselines.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** TESLA and OSNMA are **incomplete in source**; KEMTLS as given.
- **Borrow.** Partial.
- **Where used.** `domains/10-digital-infrastructure/` (source tags S3/S4).

### D10-12 — DNS size constants

- **Statement as used here.** DNS Flag Day 2020's UDP buffer **1,232 B = 1,280 − 48**; RFC 9715 §3.1's
  recommended maximum DNS/UDP payload **1,400 B**; and the response bases **A 97 / DNSKEY 113 /
  NXDOMAIN(NSEC3) 436 / NSEC 331 / compact 226** bytes, with 1,400 B common to the pq_infra and s1/s2
  variants.
- **Role.** DNSSEC feasibility.
- **Label.** `[M]`/`[L]` as recorded per figure.
- **Citation as the source gives it.** DNS Flag Day 2020 — **incomplete in source (no URL)**;
  RFC 9715 given.
- **Borrow.** Full as recorded.
- **Where used.** `domains/10-digital-infrastructure/` (the S2 tables),
  `domains/10-digital-infrastructure/src/pq_infra_s1s2_hashsig_dnssec_v2.2.py`.
- **Notes.** The domain records that several DNS/DNSSEC governance and size figures were **skipped or
  not run** on the audit host (the `dnspython` dependency is absent there, and the ledger runs 61/64 in
  the best case with S1-011 failing). Claims resting only on the original-host runs inherit that
  status — see `gaps-and-unknowns.md`.

### D10-14 — CNSA 2.0 advisory / FAQ v2.1

- **Statement as used here.** LMS and XMSS are approved; organisations should "begin transitioning
  immediately" and be exclusively post-quantum by 2030; NSA prefers LMS with SHA-256/192; HSS and
  XMSS^MT are not allowed in national-security systems.
- **Role.** Policy constraints on parameters.
- **Label.** `[M]` as quoted.
- **Citation as the source gives it.** **Incomplete in source (no URL, no document number)**.
- **Borrow.** Full as quoted.
- **Where used.** `domains/10-digital-infrastructure/`.
- **Notes.** Policy statements are constraints, not evidence. The "exclusively by 2030" date is the
  advisory's, quoted as such.

### D10-17 — Honest-majority / accountable-signature route

- **Statement as used here.** The accountability layer's own construction for migration and agility.
- **Role.** Migration and agility of the infrastructure route.
- **Label.** Project.
- **Citation as the source gives it.** None — project.
- **Borrow.** Not applicable.
- **Where used.** `domains/10-digital-infrastructure/` (source tag S6).
- **Notes.** This is a project statement, and it is cross-referenced from
  `project-statements-and-amendments.md`.

### D10-18 — The audit's own verdict on the infrastructure stack

- **Statement as used here.** "70/70 audit tests pass — but several v2.0 claims did not survive
  unchanged", together with the **21 new FAILED_ASSUMPTIONS entries A1–A21** the audit produced.
- **Role.** The audit's own verdict on the domain.
- **Label.** `[M]`.
- **Citation as the source gives it.** Project.
- **Borrow.** Full.
- **Where used.** `domains/10-digital-infrastructure/` (part 1).
- **Notes.** The two halves of this entry are one statement and must be quoted together. A "70/70"
  quoted without the second half is a different claim from the one the record makes.

---

## 4. The prior-art catalogues (contrast and scope only)

The research-journey catalogue records ten catalogue entry groups. They are listed here so that a reader
can find them, and so that no reader mistakes a catalogue entry for a borrowed result. **None of these
contributes a step to any proof in this repository.**

### D0-10 — BFT / consensus catalogue (10 entries)

- **Statement as used here.** Prior art for the accountable-quorum setting: HotStuff (arXiv 1803.05069),
  Jolteon/Fast-HotStuff (arXiv 2106.10362), DiemBFT/LibraBFT, Narwhal/Bullshark (arXiv 2105.11827),
  Tendermint, DQS (arXiv 2607.17700), Simple-IT/Sailfish++, IA-CCF (arXiv 2105.13116), and further
  entries at arXiv 2203.14711, 2407.02167 and 1703.05121.
- **Role.** Prior art.
- **Label.** `[T]` as cited per entry.
- **Citation as the source gives it.** HotStuff: **standard (added)** PODC 2019; the rest as given
  (arXiv identifiers or venue names).
- **Borrow.** **Contrast/scope only** unless a D1 entry records otherwise.

### D0-11 — PQ threshold / multisignature / ring-signature catalogue (~30 entries)

- **Statement as used here.** Size and security baselines: Squirrel (4,096 signatures ≈ 771 KB),
  Chipmunk (≈ 136 KB / 8,192 at 112-bit), Lemur (≈ 380 KB / 10^6), Threshold Raccoon (≈ 13 KiB),
  Ringtail (13.4 KB at 1,024; ePrint 2024/1113), Olingo (9.7 KB), Tanuki, Hermine (ePrint 2026/419,
  ≈ 11 KB), Mithril, Quorus, NIST IR 8214C / TCall-1, AOM-MLWE (CRYPTO 2024), [ZT25], ePrint 2025/436,
  ePrint 2025/871, the Bellare et al. TS-UF hierarchy, TAPS/DeTAPS, DAPS/PAPS, PQ traceable ring
  signatures 2021, accountable threshold ring signatures 2024, ePrint 2020/135, LastRings/LaZer,
  LAPQ-LRS, LUNA (ePrint 2022/1690), Aurora/AIM/AIMer/HAETAE, Ozdemir (USENIX Security 2022), ZKBoo
  (USENIX Security 2016), SmallWood (floor 79,632 B), and FRI/BaseFold.
- **Role.** Size and security baselines; several become the partial-theory sources catalogued elsewhere
  in this package.
- **Label.** `[T]`/`[L]` as cited per entry.
- **Citation as the source gives it.** Bellare et al. and ZKBoo: **standard (added)**. **Hermine
  carries a recorded `TS-UF-2` vs `ts-suf-2` mismatch and a DKG source mismatch.** The rest as given.
- **Borrow.** See the per-domain entries for which part each domain borrows.
- **Notes.** One figure in this catalogue was corrected inside the record itself: **Lemur's 201.2 KB
  was corrected to 185.5 KB**. A reader quoting Lemur must use the corrected figure.

### D0-12 — Standards catalogue

- **Statement as used here.** Parameter and size references: FIPS 204 (sizes 2,420 / 3,309 / 4,627 B),
  FIPS 205, FIPS 203, the BLS draft, SHAKE256/Keccak (384-bit commitments; "832 output bits ≠ 512
  capacity"), P-384/ECDSA (arXiv 1706.06752), OpenTitan/OTBN, MAXDEPTH, AES/SHA constants, and
  deterministic CBOR/protobuf.
- **Role.** Parameter and size references.
- **Label.** `[T]`/`[M]` as cited.
- **Citation as the source gives it.** FIPS 202/203/204/205: **standard (added)**; the BLS draft and
  OpenTitan as given.
- **Borrow.** Full as standards; the per-domain borrow varies.

### D0-13 — Quantum-algorithm / proof-theory catalogue

- **Statement as used here.** The reduction and quantum-attack material reused by the later domains:
  Shor (quant-ph/9508027), Grover (STOC 1996), Brassard–Høyer–Tapp (quant-ph/9705002), Zalka
  (quant-ph/9711070), compressed oracles, DFMS, Barbosa et al., Jackson–Miller–Wang, Canetti–Goldreich–
  Halevi, Carolan–Poremba, Cojocaru et al., Alagic et al., SPHINCS+ games, a formally verified tight
  proof (ePrint 2024/910), Watrous, Hoeffding notes, and T-gate / GHZ material.
- **Role.** Source of the reduction and quantum-attack entries catalogued in this package.
- **Label.** `[T]`/`[R]` as cited.
- **Citation as the source gives it.** Shor, Grover and CGH: **standard (added)**; the others as given in
  source.
- **Borrow.** Per entry — see the per-domain sections of this package.

### D0-14 — Tools named but never executed in the research journey

- **Statement as used here.** EasyCrypt, Coq, TLA+, Ivy, the Lattice Estimator, TLC/TLAPS and Docker
  chaos tooling.
- **Role.** Recommended tooling, recorded as project-internal vocabulary **with no cryptographic
  weight**.
- **Label.** Not applicable.
- **Citation as the source gives it.** None.
- **Borrow.** Not borrowed.
- **Notes.** This entry is the record's own statement that naming a tool proves nothing. The current
  status of each tool — which ran, which did not — is in `gaps-and-unknowns.md`.

---

## 5. Cross-domain citation fixes recorded by the audit stack

### D11-08 — RFC 8554 §5.1, SP 800-208 §4, FAEST v2 Lemma 9.39

- **Statement as used here.** The three citations the audit stack uses inside its cross-domain entries:
  the hash-consistency sentence (RFC 8554 §5.1), the approved parameter sets (NIST SP 800-208 §4), and
  the hidden-signer QROM soundness bound (FAEST v2 Lemma 9.39).
- **Role.** Cross-domain fix justification.
- **Label.** `[T]` as cited.
- **Citation as the source gives it.** The RFC and SP are given by number; **FAEST v2 is incomplete in
  source**.
- **Borrow.** Partial.
- **Where used.** `domains/11-independent-audit-stack/` (part 3); the RFC 8554 details are catalogued
  in full in `hash-based-signatures.md`, and the FAEST v2 transplant in
  `zero-knowledge-and-proof-systems.md`.
