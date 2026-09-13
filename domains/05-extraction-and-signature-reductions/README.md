# 05 — Extraction and signature reductions

This domain answers the second half of the programme's founding question. Domain 01 defines what a
quorum is and proves the counting fact that makes blame possible; domain 02 builds the CE-QS
construction; this domain asks how a *conflict* — two accepted certificates on two conflicting
statements — is turned into something the system can act on, and what it costs to argue that a
certificate cannot be forged.

All paths in this file are relative to the repository root. The nine scripts in `src/` are the
current revisions of one reduction series, v1.34 to v1.42; their version labels are kept in the
files' own headers and in the prose here, while the filenames drop the suffix as the build map
requires. This domain has **no superseded rows**: the build map places all nine files as `copy`
rows into `src/`, so there is no `history/` directory and nothing was withheld from the record.
v1.37 and v1.38 are earlier *steps* of the series, not earlier revisions of the same file — both
are kept in full, and both still run.

## The problem

CE-QS is a 64-seat committee with quorum `q = 43` and at most `f = 21` faulty seats. Any two
43-seat quorums share at least `2q − n = 2·43 − 64 = 22` seats. That number is the whole point:
it exceeds `f`, so a seat that signs two conflicting certificates cannot hide inside the tolerated
fault budget.

A *compact* quorum certificate — the kind a post-quantum deployment needs, because concatenating
individual signatures grows linearly in the signer count — proves that a quorum approved a
statement without naming anyone in it. Detection therefore comes for free and accountability does
not: two conflicting certificates prove that someone equivocated while leaving no way to say who.
The programme's requirement is a **conflict-extractable** certificate: from two accepted
certificates on conflicting messages, *anyone* — not a privileged auditor, not the holder of a
private sidecar — can publicly name the seats that authorized both.

The requirement has a precise shape. The named set must be

- **publicly computable** from the two certificates alone, with no secret input;
- **identifiable**: each named element is a seat index, not an opaque handle;
- **large enough to be a quorum**: at least the intersection lower bound of 22 seats, so that a set
  of accused seats cannot be dodged. Any further 43-seat quorum `T` satisfies `|T ∩ S₀| ≥ 22` and
  `|T ∩ S₁| ≥ 22`, hence `|T ∩ S₀ ∩ S₁| ≥ 22 + 22 − 43 = 1` by inclusion–exclusion: no later
  certificate can be formed entirely from unaccused seats. (The sources state the 22-seat bound on
  the accused set; this last line is elementary arithmetic performed here, and is labelled as such.)
- **backed by a reduction**: the argument that producing the conflict is hard must terminate in a
  standard assumption, at a stated cost, rather than in "the handles differ".

The domain attacks this in two movements. The first (v1.34–v1.36) is *extraction*: build the public
decoder, prove the composition that turns one adversary execution into two witnesses, and give a
concrete proof backend for a relation. The second (v1.37–v1.42) is *the reduction and its audits*:
carry the extracted conflict into a forgery against a standard signature scheme, then audit a series
of proposed shortcuts to a numerical `2^-128` bound — most of which fail.

## What each script in the band does

| Version | File (`src/`) | What it establishes | Status |
|---|---|---|---|
| v1.34 | `src/ceqs29_extractor.py` | Division-free public decoder over GF(2^512) for the R29 body; field irreducibility certificate; the explicit statement that the joint witness extractor is missing | Closed component; conditional correctness proof; the extractor obligation is open |
| v1.35 | `src/joint_extractor_lift.py` | Joint-lift theorem: two witnesses from **one** adversary execution and one terminal database measurement, with a single additive error `κ_J` and multiplicative loss `L_J = 1` | Proved conditionally on premises P1–P4 and an imported readout lemma; classical test double only |
| v1.36 | `src/circuit_witness_extractor.py` | Concrete ZKBoo-style three-share circuit proof (`R_C`), a deterministic S-sound\* extractor `E*`, and `p_triv = (3/4)^r` | Proved for this backend; does **not** cover the R29 relation |
| v1.37 | `src/signature_security_reduction.py` | Reduction from two extracted conflicting R29 witnesses to single-user SU-EUF-CMA forgery of ML-DSA-87, with exact loss arithmetic | Proved conditionally; superseded as endpoint by v1.38 |
| v1.38 | `src/slh_dsa_signature_reduction.py` | Replaces the endpoint with SLH-DSA-SHAKE-256s; AND-hybrid projection with loss exactly 1; OR-hybrid rejected; quorum lift with `α = 64/(22−f)` | Proved conditionally; no numerical `ε_SLH` |
| v1.39 | `src/signature_margin_sweep.py` | Exact inversion of the v1.38 bound into required primitive exponents `b_min`; near-128 transitions; a separate search envelope from Zalka's optimality theorem | Exact conditional arithmetic; all 2,088 records labelled `UNESTABLISHED` |
| v1.40 | `src/phase_ghz_security_check.py` | The supplied H·T·CNOT-chain prepares a phase-GHZ state exactly, and supplies no security bound; a public-auxiliary-state simulation lemma with explicit gate cost | Dead end for security; the simulation lemma is kept |
| v1.41 | `src/hybrid_sampling_bound_audit.py` | Corrects the AND-hybrid probability argument; **refutes the proposed `exp(−256Δ²)` forgery bound as used**; gives the valid conditional replacements | Correction proved; the replacement still needs a proved conditional-mean premise |
| v1.42 | `src/slh_tree_conditioning_audit.py` | SLH-DSA tree refactoring and repetition cannot manufacture conditional one-bit challenges; a proposed `q_s·L/2^λ + C(q_h)` formula evaluated; the published 10-term SPHINCS+ dependency ledger | Obstruction lemmas proved; every one of the ten published advantage bounds still missing |

## How to read this domain in order

1. [`docs/extraction-argument.md`](docs/extraction-argument.md) — the public decoder, step by step,
   with the premise each step needs. Start here: it is the only part of the domain that is finished.
2. [`docs/joint-extractor-lift.md`](docs/joint-extractor-lift.md) — how two witnesses are obtained
   from one execution, and exactly what the lift costs.
3. [`docs/circuit-witness-extractor.md`](docs/circuit-witness-extractor.md) — the concrete proof
   backend and the relation it targets, which is **not** R29.
4. [`docs/signature-reductions.md`](docs/signature-reductions.md) — the reduction story: which
   schemes, what the loss is, and why the reduction's *running time* is charged against the security
   target. This is the point that rules out the signature-inside-proof designs.
5. [`docs/hybrid-sampling-bound.md`](docs/hybrid-sampling-bound.md) — the refuted bound and what
   replaced it. Read this one even if nothing else: it is the domain's clearest negative result.
6. [`docs/conditioning-arguments.md`](docs/conditioning-arguments.md) — why refactoring, repetition
   and conditioning cannot manufacture fresh challenges.
7. [`docs/phase-ghz-security-check.md`](docs/phase-ghz-security-check.md) — the phase-state
   proposal, why it is not a security ingredient, and the one lemma worth keeping.
8. [`results/`](results/) — the re-run outputs of all nine scripts, plus the two machine-readable
   artifacts (a 798-byte field certificate and 811,628 bytes of sweep records).
9. [`VERIFICATION.md`](VERIFICATION.md) — what was re-run, what it returned, and every difference
   from the recorded baseline.

## What is proven, what is assumed, what is refuted

**Proven (with the stated premises).** The field certificate and the division-free decoder
(v1.34, Claims 1–3). The joint-lift event bookkeeping under P1–P4 (v1.35). Lemmas 1–3 for the
circuit backend (v1.36). The selector probability identity and the loss arithmetic (v1.37, v1.38).
The exact thresholds of the v1.38 bound (v1.39). The state-preparation theorem and the
public-state simulation lemma (v1.40). The probability, reduction and density-matrix corrections,
the conditional Hoeffding form, the all-pass product bound and the exact binomial tail (v1.41).
The refactoring, conditioning and ledger lemmas (v1.42). Each of these is a finite or exact
computation, and each is exercised by the script's own test suite.

**Assumed, not proved.** An oracle-respecting authorization-consistent extractor for the full R29
relation; premises P1–P4 for an actual protocol; the interface premises (honest single-slot wrapper,
complete monotone query log across branches, simulatable registration); a numerical value for the
body-binding failure `δ_B`; a numerical `ε_SLH` or `ε_87`; a proved conditional-mean premise for the
quantum sampling argument; the ten published SPHINCS+ advantage bounds with the Winternitz-factor
correction counted once.

**Refuted, rejected or withdrawn.**

- **The proposed `exp(−256Δ²)` signature-forgery bound is not established.** This is the domain's
  headline negative result and v1.41 states it in two places: "the proposed `exp(-256 Delta^2)`
  signature-forgery bound is not established" (§1) and "There is no justified substitution
  `epsilon_SLH := exp(-256 Delta^2)`" (§6). The Hoeffding inequality itself is not refuted — it is
  a theorem, and v1.41 reproduces it. What is refuted is its application here: the bound needs
  either independent trials or a *proved* sequential conditional-mean premise, and the correlated
  public GHZ sampling proposed for this construction supplies neither. See
  [`docs/hybrid-sampling-bound.md`](docs/hybrid-sampling-bound.md) for the exact statement, the
  counterexample, and the valid replacements.
- The **product-of-advantages rule** for the AND hybrid is disproved by the counterexample `T = S = E`
  with `Pr[E] = 1/2` (v1.41 §1): the product of marginals is 1/4, the true intersection is 1/2.
- The **OR-hybrid** gives no guarantee and is rejected (v1.38).
- **Two-special soundness** for the circuit backend is rejected: two openings can reveal all input
  shares and still leave a computation branch unchecked (v1.36, test 08).
- **Algebraic acceptance is not authorization.** Manufactured handles decode to 22 "candidates"
  with no witness at all (v1.34, test 19); the decoder's status stays `ALGEBRAIC_CANDIDATES_ONLY`.
- **SLH-DSA tree structure cannot supply 128 fresh one-bit challenges**, and conditioning on success
  can be 1 (v1.42, eqq. 1–4).
- The **qubit-count / phase ⇒ 128-bit-security** inference is abandoned (v1.40).

**A constant that must be flagged rather than silently resolved.** v1.35 derives the ordinary
commit-and-open term with coefficient `(20ℓ+60)` from DFMS Lemma 4.1; the later v1.43 record cites
DFMS Theorem 4.2 as `(22ℓ+60)q³2^-n + 20q²p_triv` and uses that. The two differ. The direction is
not in doubt — `22 > 20` is the more conservative coefficient — but the exact theorem statement was
not re-verified against the paper here, and this repository does not silently substitute one for the
other. Both plain forms appear in the placed files: `(20ℓ+60)` in `src/joint_extractor_lift.py`
(v1.35) and `(22ℓ+60)` in the v1.43 material held by domain 06, which is where the difference has to
be settled.

### A note on how the refuted bound is worded

The consolidated theory index summarises entry D5-10 as "refutes the proposed `exp(−256Δ²)` bound".
Read against the source, that summary is right about the conclusion and slightly wide about the
object: v1.41 refutes the *proposed substitution*, i.e. the use of that expression as `ε_SLH`, not
Hoeffding's theorem, and not the arithmetic of the expression itself — v1.41 §5 evaluates
`2NΔ²/ln 2` exactly and the script's `--report` prints those values. This README states the
narrower and supported form, and records the wider wording so a reader meeting the index first is
not misled in either direction.

## Sizes and cost

The band is cheap to re-run. On the recorded baseline the whole set runs in seconds: the extractor's
`--self-test` is the slowest at 0.718 s recorded; every other suite is below 0.35 s. The two
machine-readable artifacts are the largest outputs: `results/signature_margin_sweep.records.json` is
811,628 bytes (2,088 records) and `results/ceqs29_extractor.certificate.json` is 798 bytes. Both
reproduced byte-identically here. The nine test suites total 167 tests and all pass.

## What this domain does not do

It does not implement a quantum compressed oracle, does not compile the R29 authorization relation
into any proof format, does not assign a numerical advantage to any signature scheme, and does not
certify a QPT-128 security level. Every numerical result in the band is either an exact conditional
threshold ("if `ε_SLH ≤ 2^-b` then this bound reaches `2^-s`") or a probability correction. The
numerical security question is not answered here; it is handed to domain 06, where the target is
fixed and the compat-mode design that these reductions were attached to is withdrawn.
