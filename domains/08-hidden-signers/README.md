# Domain 08 — hidden signers within 32 KiB

**Status in one line: the hidden-signer profile does not ship.** This domain delivers a tested design,
an executed security ledger, recorded measurements, and the list of what is missing. It does not
deliver a deployable hidden-signer certificate, and one of the profile's requirements has no
construction at all. Read [the validation status](docs/validation-status.md) before citing anything
here.

---

## 1. What the profile asks

A **hidden-signer quorum certificate** must show that 43 of 64 seats approved a message, and do all
of the following at once:

1. hide *which* 43 seats approved (any two 43-subsets of 64 overlap in at least 22 seats);
2. verify publicly, with no per-signer secret at verification time;
3. fit **32,768 bytes** on the wire, including the proof;
4. let **anyone** name the double-signers — two certificates for the same epoch and domain with
   different messages must yield a public, keyless proof of which seats approved both;
5. meet the programme's category-5 post-quantum target (QPT-128: ≥ 2^18 gates per primitive
   evaluation, D1; success ≤ G·2^−130 at a gate budget G, D2).

## 2. Why it is hard

Requirement 4 fights requirement 1. The evidence that names a double-signer has to be recoverable
**from the certificate bytes by any observer**, so something derived from each seat's opening must
travel in the certificate — while the same bytes must not reveal which seats produced them. Both
modes therefore spend their design effort on a **handle**, an algebraic image of the opening keyed by
the message, and both push the rest of the proof into a VOLE-in-the-head backend.

Two consequences shaped this domain:

- **No published scheme has the combination.** The literature pass (v1.45) found the closest
  semantics in a pairing-based design that is not post-quantum, and the closest post-quantum public
  tracing at ≈ 3.4 MB for one member per signer — ≈ 104× over budget. Every family is tabulated, with
  why it fails, in [history/hidden-signer-32kib-v1.45.md](history/hidden-signer-32kib-v1.45.md) §1.
- **The prover cannot be a single party.** Whoever holds an opening can compute a second handle for
  that seat and frame it, so a prover that learns all 43 openings makes every honest seat's safety
  rest on the prover's honesty. **No collaborative prover exists** for this setting — that is the
  domain's essential gap: [docs/collaborative-prover.md](docs/collaborative-prover.md).

## 3. The two modes

| | Mode A (v1.45) | Mode B (v1.46 → v1.50 → v1.51) |
|---|---|---|
| handle | `Z = r ⊕ c(m)·s` over GF(2^336) — **linear** | `Z = r⁷ ⊕ c·s` over GF(2^256), linearized to `Z = r⁷ ⊕ L_c(s)` in v1.50 |
| key map | a keyed hash | expanding random quadratic map F: F₂^512 → F₂^812 |
| size | fits 32 KiB only at extreme settings (2^44 leaves, 2^24-step chain) with the best published key map | 30,810 B at the ledger's (2^32, w_g = 32, τ = 7) setting under the DFMS-modelled R3; **30,684 B measured** at the production setting (b = 20, τ = 11, w_g = 16, ρ = 4,096) by this build's run, `results/prover-v1.51-production-run.json` |
| security | **refuted as a security choice**: the linear handle scores ≈ 123.3 bits algebraically, below the 251-bit generic bound | attack-based ledger; 7.7-bit D2 margin at the production setting under the multi-round-loss form of R3 |
| status | a refuted candidate, kept | the design; still not a proven scheme |

Mode A's failure is a **result**, not a discarded draft: the linear handle is exactly the thing the
next design had to avoid, which is why Mode B pays for a power map. Both are described, with the
borrowed parts named, in [docs/construction.md](docs/construction.md).

### 3.1 Where this sits in the programme: profile B1 and Theorem C

The programme's certificate contract (domain 07) has one frame and two profiles. **Profile B0**
(suite `0x44B0`) replaces the 43 handles with an 8-byte signer bitmap and 43 fixed-width signatures,
and publishes the signer set. **Profile B1** (suite `0x44B1`) keeps the contract layout — a 208-byte
header, 43 handles, one joint proof — and is the profile that **hides** the signers. B1's relation,
frame, algebraic extractor and ledger are fixed; the programme records that no qualified proof
backend for B1 exists anywhere in the repository, and that its only implementation is a
structure-only marker that never reports an authorization.

**Theorem C, and what it does and does not say.** B1's own domain proves a size floor
(`docs/sidecar-free-finalization.md` §3, re-stated in `domains/07-compact-certificate-b0`): for
proofs in the KKW / BN++ / FAEST-v2 style whose repetitions each carry at least a bit per witness
bit, QPT-128 forces `τ·b + w_g ≥ s` (s = 212 with no challenge chain), credentials of ≥ 218 bits, and
a proof of at least `τ·43·(c + w)` bits — at N = 2^16 that leaves about 359 bits of witness per seat
in the 27,056-byte slot, against the 2,816 bits the cheapest published primitives need.

**This domain is the attempted escape from Theorem C, and it is not a refutation of it.** Mode B does
two things Theorem C's hypotheses assume away: it removes the witness from the proof (s is *derived*
inside the circuit from r, so a seat's committed witness is r plus a one-hot selector — 320 bits, not
2,816), and it recovers the identifying evidence by public pair search rather than by proof
extraction. **Theorem C is a necessary condition for the named witness-committing families, not a
universal lower bound and not an impossibility result for hidden signers.** A reader who takes it as
the latter will be misled; a reader who takes Mode B as having escaped it should note that Mode B's
proof soundness is a transplant and that its own ledger's margin is 7.7 bits.

### 3.2 What is proven, measured, estimated, assumed

| Kind | Items |
|---|---|
| **Theorem with proof** | Mode B Theorem 1 (non-frameability, tight) and Theorem 2 (safety / forensic completeness, modulo Theorem 3); the v1.51 linearized-polynomial lemma (elementary); the field's irreducibility by the Rabin test |
| **Reduction sketch / transplant** | Mode B Theorem 3 (a transplant of FAEST v2 Lemma 9.39, "not re-derived line by line"); Theorem 4 (privacy, GHHM21 Theorem 3 with named simulation error) |
| **Ledger estimate (model)** | every row of the v1.47 ledger; the R3 proof-soundness row is *modelled* with DFMS22 and, in its default form, **omits the multi-round loss** |
| **Measurement** | the sizes and timings of the executables here: the toy proof's 6,696 B against the 6,924 B formula; the reduced C-prover run's 47,524-byte proof; the demo-256 extraction; the Mode A negative result (123.3 bits) |
| **Assumption** | A-F1, A-F2, A-QROM, A-P, A-Prove (the collaborative prover — essential), A-Reg |
| **Simulation** | the reviewer selector-parity probe (validation status item 6) |

**Not a proven scheme.** There is no qualified proof backend for the hidden-signer relation in this
repository or in this domain, no collaborative prover, and no theorem here that is not either a
transplant or conditional on the named assumptions.

## 4. Reading order

1. [docs/construction.md](docs/construction.md) — the two modes, their theory, what is borrowed.
2. [docs/collaborative-prover.md](docs/collaborative-prover.md) — **the essential gap**; read this
   before believing any theorem in the design.
3. [docs/rigorous-ledger.md](docs/rigorous-ledger.md) — the gate-unit ledger, its constants, its
   sweeps and the thin margin.
4. [docs/prover-and-sanitizers.md](docs/prover-and-sanitizers.md) — the C prover and what its
   sanitizer runs do and do not show.
5. [docs/toy-field.md](docs/toy-field.md) — the only end-to-end run, and its toy width.
6. [docs/validation-status.md](docs/validation-status.md) — the full open-items list.
7. The source revisions, in the order they were written:
   [history/hidden-signer-32kib-v1.45.md](history/hidden-signer-32kib-v1.45.md) (Mode A),
   [docs/hidden-signer-32kib.md](docs/hidden-signer-32kib.md) (Mode B v1.46),
   [docs/mode-b-security.md](docs/mode-b-security.md) (v1.49: the theorems, the ledger, the
   independent cryptanalysis).
8. [VERIFICATION.md](VERIFICATION.md) — what was re-run here, with commands and observed results.

## 5. What is in this domain

| Path | What it is |
|---|---|
| `docs/` | the two source documents, plus the six documents written for this build |
| `src/` | the current implementations: Mode A, Mode B (v1.51), the ledger (v1.47), the toy prover (v1.48), and the C prover (v1.51, version in the source file's own header) |
| `history/` | the superseded revisions: v1.45 Mode A, the v1.46 base module, the v1.50 module, the v1.49 and v1.50 C provers |
| `results/` | raw outputs of every run recorded for this domain ([results/README.md](results/README.md)) |
| `VERIFICATION.md` | one row per claim: the command, the environment, the recorded expectation, what was observed, the verdict — including the rows that were **not** run and why |
| `SHA256SUMS.txt` | sha256 of every file in this domain except itself |

### Source name → repository path

The copied files keep their own recorded names inside their text (including their "Reproduce"
blocks, which name the files as they were when written). The mapping is:

| Recorded name | Path here |
|---|---|
| `hidden_signer_modeA_v1.45.py` | `src/hidden_signer_mode_a.py` |
| `hidden_signer_modeB_v1.46.py` | `history/hidden-signer-mode-b-v1.46.py` |
| `hidden_signer_modeB_v1.50.py` | `history/hidden-signer-mode-b-v1.50.py` |
| `hidden_signer_modeB_v1.51.py` | `src/hidden_signer_mode_b.py` |
| `modeB_rigorous_ledger_v1.47.py` | `src/mode_b_rigorous_ledger.py` |
| `modeB_voleith_toy_v1.48.py` | `src/mode_b_voleith_toy.py` |
| `modeB_prover_v1.49.c` | `history/mode-b-prover-v1.49.c` |
| `modeB_prover_v1.50.c` | `history/mode-b-prover-v1.50.c` |
| `modeB_prover_v1.51.c` | `src/mode_b_prover.c` |
| `hidden_signer_32KiB_v1.45.md` | `history/hidden-signer-32kib-v1.45.md` |
| `hidden_signer_32KiB_v1.46.md` | `docs/hidden-signer-32kib.md` |
| `modeB_security_v1.49.md` | `docs/mode-b-security.md` |

Every file was placed byte-identical to its source, except for the rewrites registered in §6. The
C sources' build comments name the file's own versioned name (e.g. `modeB_prover_v1.51.c`); the
command that builds the copy here is:

    gcc -O3 -march=native -fopenmp -Wall -o modeB_prover src/mode_b_prover.c

## 6. Rewrite register

Six of the twelve mapped files carry rewrites; the other six were placed byte-identical to their
source, which the digest table in [VERIFICATION.md](VERIFICATION.md) shows as equal repository and
source sha256 values. Every rewrite removes a trace of the working context in which the source was
produced, or repairs a name that the repository's rename invalidated. Two of the six are text
corrections applied by hand, so their effect is larger than the two import repairs.

| File | Rewrite |
|---|---|
| `src/hidden_signer_mode_b.py` | the import of the v1.46 base module points at `../history/hidden-signer-mode-b-v1.46.py` (the base module was renamed on the way into the repository, so a same-directory import could not resolve), and the docstring sentence naming its location was updated to match. The module name other files import (`hidden_signer_mode_b.py`) is unchanged |
| `src/mode_b_voleith_toy.py` | the same import repair and docstring sentence, for the same reason |
| `history/hidden-signer-mode-b-v1.50.py` | the same import repair (sibling path in `history/`) and docstring sentence |
| `docs/hidden-signer-32kib.md` | line 13: the instruction-framing clause replaced by the substantive one ("Treating this as frontier work — borrowing partial ideas across papers, gluing them, and testing each decision"); line 85: the correction attribution reads "v1.49 independent analysis"; line 189: the script list no longer names the working directory the scripts ran in |
| `history/hidden-signer-32kib-v1.45.md` | line 39: the heading reads "Literature (primary sources read for this survey)" |
| `docs/mode-b-security.md` | line 21 and line 182: the pending-report references read "the independent analysis report" and "the independent analysis jobs"; line 167: the adversarial pass is described without the working directory its experiments ran in |

**Considered and not rewritten.** `docs/mode-b-security.md` §9 refers to "the reviewer" in several
places. The referent is the independent cryptanalysis pass of that section — a role, not a tool —
and the sentences carry meaning the section depends on (which findings that pass did and did not
finish). It is therefore kept, and named here so no reader has to guess.

## 7. Reproducing

From this directory, in the pinned environment described in
[tooling/environment.md](../../tooling/environment.md):

    python3 src/hidden_signer_mode_a.py --self-test          # 8 tests
    python3 src/hidden_signer_mode_a.py --report             # the Mode A sizing table
    python3 history/hidden-signer-mode-b-v1.46.py --self-test # 12 tests
    python3 history/hidden-signer-mode-b-v1.46.py --demo-256  # full-size registry, frames, extraction
    python3 history/hidden-signer-mode-b-v1.50.py --self-test # 5 tests
    python3 src/hidden_signer_mode_b.py --self-test          # 7 tests
    python3 src/mode_b_rigorous_ledger.py --self-test        # 7 tests
    python3 src/mode_b_rigorous_ledger.py --report           # every ledger row and sweep
    python3 src/mode_b_voleith_toy.py --self-test            # 7 tests
    python3 src/mode_b_voleith_toy.py --run                  # the measured toy proof size
    gcc -O3 -march=native -fopenmp -Wall -o modeB_prover src/mode_b_prover.c
    ./modeB_prover --vectors
    ./modeB_prover --run --b 12 --tau 20 --wg 8 --rho 1024   # documented reduced smoke run

The observed results, timings and verdicts are in [VERIFICATION.md](VERIFICATION.md); the raw outputs
are in [results/](results/README.md).

## 8. Non-claims

- No hidden-signer certificate ships; no file here is a deployment artefact.
- **No collaborative prover exists**, so the design is a trusted-aggregator design.
- The structure-only marker in the Python modes is **not** a proof backend; the toy prover is a
  structural simulation at toy width and reports itself unqualified.
- No security theorem is claimed for Mode A; Mode B's Theorem 3 is a transplant of FAEST v2 Lemma
  9.39 and its ledger's default proof-soundness row omits the multi-round loss.
- The toy-width demonstration is not a production result. The production-parameter run **was** performed
  once in this build (it produced the 30,684-byte frame cited above, archived with its output) — but it
  was **not** performed in the rounds that produced these sources, where that figure was a size-formula
  entry, and neither the source documents nor this README claims otherwise. One run at one setting is a
  reproduction of a size table, not evidence of security.
- The withdrawn property-layer "16/16" figure is not restated anywhere in this domain; see
  [docs/validation-status.md](docs/validation-status.md) §4.
