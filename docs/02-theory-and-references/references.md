# References

Every reference the programme cites, grouped, **as the sources give it**, with the state of its
verification. Nothing here is completed, added to, or corrected on the citing source's behalf: where the
record gives an author list without a venue, this list shows the author list without a venue.

## How to read the verification column

| State | Meaning |
|---|---|
| **full text** | The record shows the source's own text was consulted — it cites numbered definitions, lemmas, equations or appendix items that only appear in the body. |
| **abstract only** | The record says in terms that only the title and abstract were read. No theorem from such a source is credited anywhere in the repository. |
| **unverified** | The citation is recorded but the record gives no evidence of any check against the source. This includes every entry marked *incomplete in source*. |

An entry whose citation is **incomplete in source** is also listed again in §11 with the missing field
named, because that is the list a reader needs before reusing a citation.

---

## 1. Lattice hardness and the handle algebra

| Reference, as the source gives it | State |
|---|---|
| Banerjee–Peikert–Rosen, EUROCRYPT 2012 (Learning With Rounding) — **standard identity, added**; the source gives no citation | unverified |
| Yang et al., Theorem 4.1 (wPRF from LWR), the uniqueness counting proof, Lemma F.1 (one-wayness) — **no venue** | unverified |
| Yang–Au–Lai–Xu–Yu, 2017, Theorem 5.2 (k-times anonymous authentication) — **no venue, no ePrint** | unverified |
| Jawale–Khurana (simulation-extractable adaptive multi-theorem computational ZK argument; the ledger names "Cor. 4.4") — **no venue** | unverified |
| "Quantum LWR (QLWR)" — the v1.3 document's **own named assumption**; not a standard named problem, no citation | unverified |
| Liu–Zhandry, arXiv:1811.05385v2 — **complete in source** | full text (the query exponents are cited as such) |
| Unruh, arXiv:0910.2912v1, EUROCRYPT 2010, Definition 3 / Theorem 15 — **complete in source** | full text |
| Bouman–Fehr, CRYPTO 2010, Theorem 3 | full text |

## 2. Quantum search, quantum algorithms and the accounting

| Reference, as the source gives it | State |
|---|---|
| Grover, STOC 1996 — **standard identity, added** | full text |
| Bennett–Bernstein–Brassard–Vazirani (the query lower bound) — cited in the record only as **"BBBV 1997"** | unverified |
| Brassard–Høyer–Tapp, LATIN 1998 (quant-ph/9705002) — **standard identity, added** for the collision/claw exponent | full text |
| Zalka, "Grover's quantum searching algorithm is optimal", quant-ph/9711070 — **standard identity, added**: Physical Review A 60, 2746 (1999) | full text |
| Shor, quant-ph/9508027 | unverified |
| Carolan–Poremba — the `80(T+1)²/2^min(r,c)` sampler-change term; **as given in source** | unverified |
| Chung–Fehr–Huang–Liao (CFHL), EUROCRYPT 2021, Theorem 5.29 — **complete in source** in D5/D6; **incomplete in source** in the audit stack, which cites "only the bound formula" | full text |
| Hoeffding, 1963, Theorem 2 — "as given in source" | full text |
| "The published quantum collision bound", with a pointer to an Isabelle AFP formalization — **incomplete in source: no author, no venue, no year, and the constant `12(Q+154)³` is unsourced at the point of use** | unverified |
| Watrous, *The Theory of Quantum Information*, Chapter 2 (Kraus and positive-map conventions) — complete enough in source; **standard identity, added**: Cambridge University Press, 2018 | full text |
| Cojocaru–Hhan–Liu–Yamakawa–Yun, "Quantum Lifting for Invertible Permutations and Ideal Ciphers", Corollary 6.9 and the model definitions, arXiv 2504.18188, 2025 — **complete (arXiv)**; the venue is **not** added, because it is not certain | full text |
| NIST category-5 definition ("resources comparable to AES-256 key search") — **standard identity, added** | unverified |

## 3. Commit-and-open, zero knowledge, proof systems

| Reference, as the source gives it | State |
|---|---|
| Don–Fehr–Majenz–Schaffner, "Efficient NIZKs and Signatures from Commit-and-Open Protocols in the QROM", arXiv 2202.13730, 2022. The venue and theorem number appear only through the project's own finalization document: "DFMS, CRYPTO 2022, Theorem 4.2". The audit stack records the citation as **incomplete in source (no theorem number)**. Definitions 3.1/3.5, Equation (6), Lemmas 4.1/5.1, Theorems 4.2/5.2, Corollary 2.7 are cited by number | full text |
| ZKBoo, USENIX Security 2016, §4.1, Proposition 4.2, Appendix A — **standard identity, added** | full text |
| Tomamichel–Schaffner–Smith–Renner, "Leftover Hashing Against Quantum Side Information", Theorem 6, arXiv 1002.2436 — **standard identity, added**: IEEE Transactions on Information Theory 57(8), 2011 | full text |
| "compressed oracles" — named in the research-journey catalogue as a technique, with no author or venue recorded | unverified |
| Aurora, EUROCRYPT 2019, Theorem 1.2 and the implementation section | full text |
| AIM (CCS 2023), HAETAE (CHES 2024), Han et al. (IACR CiC 3(2) 2026), Quorus (USENIX Security 2026), Doerner–Kondi–Rosenbloom (CRYPTO 2024) — **abstracts and affiliations only; "no uninspected theorem is credited"** | abstract only |
| Ozdemir–Boneh, USENIX Security 2022, §§3–5 (collaborative zk-SNARKs) | full text |
| "the 2026 collaborative CP-NIZK paper", Theorem 1 — **incomplete in source**; its concrete results use Groth16 and Bulletproofs and are recorded as "not PQ evidence" | unverified |
| Brodsky–Choudhuri–Jain–Paneth, EUROCRYPT 2024 (aggregate-signature interface) | full text |
| Chiang et al. — **complete in source (DOI given)** | unverified |
| A CCS 2025 paper, §5.1, Figure 8, Theorem 5.9, Lemmas B.1–B.3 — cited by section and lemma numbers; the author list is not recorded at the point of use | unverified |
| "Theorem 7.6" (aggregate signatures from vPIR plus a local-opening hash) — a **project-internal** citation of the source paper | unverified |
| seBARGs → adaptive subset-extractable monotone-policy BARGs — **as cited in v0.8** | unverified |
| Goldwasser–Kalai–Rothblum, STOC 2008 and Lund–Fortnow–Karloff–Nisan, JACM 1992 (GKR / sumcheck) — **standard identities, added**; the source gives no citation | full text |
| Grassi–Khovratovich–Schofnegger, AFRICACRYPT 2023 (Poseidon2) — **standard identity, added**; the source gives no citation | unverified |
| Franklin–Yung, STOC 1992 (packed secret sharing) — **standard identity, added**; the source gives no citation | unverified |
| Ben-Or–Goldwasser–Wigderson, STOC 1988 (`n > 3t` threshold MPC) — **standard identity, added**; incomplete in source in D3 | full text |
| Diamond–Posen, ePrint 2024/504 (BaseFold) | full text |
| WHIR, Khatam, BaseFold list-decoding, HyperFond — **incomplete in source** | unverified |
| QuickSilver — **incomplete in source (name only)** | unverified |
| LaZer, LaBRADOR, SmallWood, spartan-whir, Orthus, Fusion, Lazarus, mutable BARGs, Ishai–Su–Wu, TripleRing — mixed: most carry ePrint identifiers; **Fusion, Lazarus, mutable BARGs, Ishai–Su–Wu and TripleRing are incomplete in source** | unverified |
| "LaBRADOR paper" — **incomplete in source (no venue, year or identifier)** | unverified |
| MQOM round-2 specification, Tables 6–7; ePrint 2021/692, Figure 5, §5.2.1; ePrint 2022/588, Appendix B.2 — the specification tables carry no full bibliographic entry | unverified |
| MQOM2 and KuMQuat "One Tree", ePrint 2024/490; the Ding–Yang cubic; the FAEST v2 size formula — **all incomplete in source** | unverified |
| Binius64 (the vendored, patched prover) — workspace 0.1.0, pinned commit `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4`; **no `.git` directory, so the pin cannot be verified locally** | full text (the tree is present) |

## 4. Hash-based signatures

| Reference, as the source gives it | State |
|---|---|
| Buchmann–Dahmen–Hülsing, 2011 — **incomplete in source (no venue)**; **standard identity, added**: RFC 8391, Hülsing et al. 2018 | unverified |
| Buchmann–Dahmen–Schneider (BDS traversal) — **no venue, no year at the point of use** | unverified |
| Hülsing–Rijneveld–Song, ePrint 2015/1256, Theorem 1 — **complete**; also cited in the record as "HRS16" | full text |
| Fregly–Harvey–Kaliski–Sheth, CT-RSA 2023 — **venue given**; MTL, Theorem 2 (MM-SPR); ePrint 2022/1730 also given | unverified |
| Kampanakis et al., ePrint 2021/041, Table 2 | unverified |
| pqm4 — named without a version or commit | unverified |
| GHP18 / "X-Wing 2024" — **incomplete in source (no venue, no identifier)** | unverified |
| KEMTLS; RFC 4082 (TESLA); Galileo OSNMA — TESLA and OSNMA are **incomplete in source** | unverified |

## 5. Signature security, Fiat–Shamir and standards for signatures and KEMs

| Reference, as the source gives it | State |
|---|---|
| Barbosa et al., "Fixing and Mechanizing the Security Proof of Fiat-Shamir with Aborts and Dilithium", Theorem 2, **ir.cwi.nl/pub/33405**, no year — **standard identity, added**: CRYPTO 2023 | full text |
| Barbosa et al., ASIACRYPT 2024, Theorems 1, 2 and 4 | full text |
| Hülsing–Kudinov, 2022 — **abstract only** in the record's own words | abstract only |
| The ASIACRYPT 2022 paper behind that line — **abstract only** | abstract only |
| Jackson–Miller–Wang, arXiv 2312.16619 | full text |
| Canetti–Goldreich–Halevi — **standard identity, added**: JACM 51(4), 2004; cs/0010019 | unverified |
| Bellare, Crites, Komlo, Maller, Tessaro, Zhu, "Better than Advertised Security for Non-interactive Threshold Signatures", CRYPTO 2022 — **standard identity, added** (defines `TS-UF-0…4` / `TS-SUF-2…4`); incomplete in source in D1 | unverified |
| Hermine, ePrint 2026/419; plus the NIST MPTS 2026 preview, writeup and slides as given. The catalogue also records a **`TS-UF-2` vs `ts-suf-2` mismatch** and a **DKG source mismatch** | full text |
| Kosuge–Xagawa, ePrint 2022/1359, Theorem 1 | full text |
| Avitabile–Botta–Fiore, ESORICS 2025 — the Tetris DAPT semantics; also at ePrint 2025/730 in v1.18; **incomplete in source in v1.0** | full text |
| FIPS 202, 203, 204, 205 — **standard identities, added** at the points where the source names the primitive without a citation | full text |
| NIST SP 800-227, §§4 and 5.2; NIST SP 800-208; RFC 8554; RFC 8391; RFC 5869 (HKDF); NIST SP 800-38D (AES-GCM); RFC 9715 §3.1 — **standard identities, added** where the source does not cite them | full text |
| CNSA 2.0 advisory / FAQ v2.1 — **incomplete in source (no URL, no document number)** | unverified |
| DNS Flag Day 2020 — **incomplete in source (no URL)** | unverified |
| OpenTitan / OTBN, the BLS draft, P-384 / ECDSA (arXiv 1706.06752), MAXDEPTH, deterministic CBOR/protobuf — **as given** | unverified |

## 6. Finite fields, algebra and coding

| Reference, as the source gives it | State |
|---|---|
| Greenhill, "Theoretical and experimental comparison of efficiency of finite field extensions", **§2 Lemma 1**, with a URL at the point of use — **incomplete in source (no venue, no year)** | unverified |
| Rabin, SIAM Journal on Computing 9(2), 1980 — **standard identity, added** for the irreducibility criterion | unverified |
| The theory of linearized / additive polynomials over finite fields — **standard identity, added** for the kernel lemma | unverified |
| The semi-regular degree of regularity (`dreg`) and XL at `ω = 2` — the record's own **semi-regularity heuristic**, "heuristic, not a theorem"; **incomplete in source** | unverified |

## 7. Protocol, network and consensus

| Reference, as the source gives it | State |
|---|---|
| Dwork–Lynch–Stockmeyer, JACM 1988 (GST / eventual synchrony) — **standard identity, added** | unverified |
| Dolev–Yao — the symbolic adversary model | unverified |
| HotStuff, arXiv 1803.05069 — **standard identity, added**: PODC 2019 | unverified |
| Jolteon / Fast-HotStuff (arXiv 2106.10362), DiemBFT/LibraBFT, Narwhal/Bullshark (arXiv 2105.11827), Tendermint, DQS (arXiv 2607.17700), Simple-IT / Sailfish++, IA-CCF (arXiv 2105.13116), arXiv 2203.14711, arXiv 2407.02167, arXiv 1703.05121 | unverified |
| Boneh–Drijvers–Neven — **standard identity, added**: ASIACRYPT 2018; incomplete in source | unverified |
| Fujisaki–Suzuki — **standard identity, added**: PKC 2007; incomplete in source | unverified |
| Camenisch–Hohenberger–Lysyanskaya — **standard identity, added**: EUROCRYPT 2005; incomplete in source | unverified |
| Liu, ePrint 2025/1807, *Traceability for Free* — incomplete in v1.1, complete in v1.18 | full text |
| Bellare et al. TS-UF hierarchy — **standard identity, added**: CRYPTO 2022 | unverified |
| NIST IR 8214C / TCall-1; AOM-MLWE (CRYPTO 2024); TAPS/DeTAPS; DAPS/PAPS; [ZT25]; ePrint 2025/436; ePrint 2025/871; ePrint 2020/135; LastRings/LaZer; LAPQ-LRS; LUNA (ePrint 2022/1690); Ringtail (ePrint 2024/1113); Squirrel; Chipmunk; Lemur; Threshold Raccoon; Olingo; Tanuki; Mithril; SmallWood — **as given per entry** | unverified |
| The RLN specification, MinHash, TripleRing+, the LoTRS venue, `libtalos_voleith`, the DQS paper, DeTAPS, the FAESTer author list — **incomplete in source** | unverified |
| "signature-in-signature / hidden-until-disclosed accountability" — **no author, no venue** | unverified |
| SPHINCS+ games; a formally verified tight proof, ePrint 2024/910; Alagic et al.; the Hoeffding notes; T-gate/GHZ material — **as given in source** | unverified |

## 8. Deployed implementations and datasets cited as evidence

| Reference, as the source gives it | State |
|---|---|
| liboqs 0.16.0 (tag 0.16.0, commit `5a1a854b0dc9f2141bdc771c555ee60c37950183`) | full text (built and exercised) |
| NIST ACVP vectors, master commit `975de31eb83d87039ec88934fdc47d8c312b892d` (2026-08-12), downloaded 2026-09-11 — **the vector JSON files are not in the archive**; only `SOURCE.txt` with their recorded SHA-256 digests | unverified (vectors absent) |
| dilithium-py 1.4.0 | full text (exercised) |
| kyber-py 1.2.0 (host); **unpinned** in the container | full text (exercised) |
| pqcrypto 0.3.4 wheel, sha256 `b2f9bad43a1e3970f55e6f68fc1864595c9b0c6e53638aa8393b1d01216a6ebb` | full text (exercised) |
| Python `cryptography` 46.0.0 (dossier replay 46.0.6) | full text (exercised) |
| hsslms 0.1.3 (PyPI) — used as the independent RFC 8554 implementation | full text (exercised on the original host; **skipped on the audit host**) |
| dnspython 2.8.0 — **not installed on the audit host** | partial (original host only) |
| CryptoMiniSat — **not run here; no version recorded** | unverified |
| Tamarin prover 1.12.0 (Git revision `82780bbaf3328a45f624ddb41e51bf75425f851c`, branch master, compiled 2026-03-07) and Maude 3.5.1 | full text (executed) |
| ProVerif (models written for ≥ 2.04) — **not installed; never executed** | unverified |
| EasyCrypt — **not installed**; `formal/frame_b0.ec` is admitted | unverified |
| TLA+ / TLC / TLAPS — **never executed**; `tla2tools.jar` absent | unverified |
| gcc 14.2.0; clang 18.1.8 with compiler-rt 1:18.1.8 | full text (executed) |
| numpy 2.4.6 (host) / 2.2.6 (container); SymPy 1.13.1 (host) / 1.14.0 (container); galois 0.4.11; CPython 3.12.3 (hosts) / 3.12.14 (D3's v1.29 runs) | full text (executed) |
| Rust 1.97.1 (`8bab26f4f 2026-07-14`); crate lock v4, 104 packages | full text (built) |
| SageMath / passagemath — **not installed; no version recorded** | unverified |
| LaZer (commits `59a52f74ca39584edf77b4b8b7437dbd48f9ad94` and `10eafeca4cd53ff4fc54193dce904dbd0026fefd`) — **planned; build failed at missing GMP headers** | unverified |
| `jachiang/PQ-Threshold-Ring-Sigs-from-VOLEitH` — **not cloned, not executed** | unverified |
| The devnet kit and `ops/devnet-chaos/pumba_control.py` — **excluded material**; results are cited only and cannot be verified from the archives | unverified |

## 9. Project-internal statements (no citation to give)

The eight operator-ledger lemmas `L1`–`L8` and the rounds table; the A01–A28 investigations; the 130
amendments; the reader flags; the project theorem chains of domains 01, 02, 06, 07, 08, 09 and 11; the
finalization's `L1`–`L5`; the register entries `Q1`–`Q4` and `A18`; the claim register `C1`–`C20`; the
`frame_b0.ec` skeleton; and every measurement and fit taken by the programme. These are catalogued in
`project-statements-and-amendments.md`, `quantum-search-and-accounting.md` and the domain documents.
They carry no external citation because there is none to give, and the field says so rather than
leaving a blank.

---

## 10. Where the record itself corrects a reference

Two corrections inside the record change a number that would otherwise be carried into this list:

- **Lemur's size was corrected from 201.2 KB to 185.5 KB.** Use the corrected figure.
- **The pre-fix figure of 1,768 bytes for the LMS profile is refuted** (finding I6). Use the
  RFC-derived 1,772 bytes.

Neither is a citation error; both are corrections of the programme's own arithmetic, and both are
recorded because a bibliography that carried the uncorrected numbers forward would be carrying refuted
values.

---

## 11. Citations incomplete in the source — the list a reader needs before reusing one

Reproduced from the record, grouped as the record groups it. **Each entry's missing field is named; none
is filled in here.**

- **Operator ledger:** `S1` (no theorem number), `S2` (no year; author list is "et al."), `S5` (a web
  page, no date) — plus **35 STD amendments that carry no proof and no citation**, and the record's
  statement that **113 of 116 amendments have no executable witness**.
- **Domain 05:** Greenhill's Rabin-test reference (no venue, no year); Hülsing–Kudinov 2022 and the
  ASIACRYPT 2022 paper read as **abstracts only**; the share-of-witness definition incomplete.
- **Domains 06 and 07:** LaBRADOR (no venue); the KKW / BN++ / FAEST v2 size formulas "asserted from
  their size formulas"; MQOM round-2 tables cited without full bibliographic entries.
- **Domain 08: every cited source in its theory list is recorded as incomplete in source** — FAEST v2
  by lemma numbers only; QuickSilver; MQOM2 / KuMQuat; DFMS22; GHHM21; the semi-regular `dreg`
  heuristic.
- **Domain 10:** Buchmann–Dahmen–Hülsing 2011 (no venue); "BBBV 1997" alone; DNS Flag Day 2020 (no
  URL); the CNSA 2.0 FAQ (no document number); X-Wing (no venue); the TESLA and OSNMA citations.
- **Domain 11:** CFHL cited as "the bound formula only"; FAEST v2 as above.
- **Domains 02a and 02b:** the RLN specification, MinHash, TripleRing+, the LoTRS venue,
  `libtalos_voleith`, the DQS paper, DeTAPS, the FAESTer author list, and "signature-in-signature".
- **Domains 09 and 12** inherit the domain 06 and domain 08 citations.

**Before any citation from the register is carried into this list**, the record requires that the four
**pointer corrections** (A9, A10, A11, A15) and the four **wording corrections** (A18, A19, A20, I4) be
applied. They are listed in `gaps-and-unknowns.md` and in
`project-statements-and-amendments.md` §7.
