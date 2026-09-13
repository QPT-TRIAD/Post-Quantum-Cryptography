# The attack lab — `src/ceqs_attack_lab.py`

*Recorded write-up:* `results/attack-lab-results.md` (shipped byte-identical to the source revision;
§2–§9 correspond to the experiments below). *Re-run in this repository:*
`results/attack-lab-run.txt`, with the machine-readable report in `results/attack-lab-report.json`.

The lab asks one question — **did any attack succeed?** — and a second one behind it: **how do the
real attacks scale?** The first is answered by counting, the second by fitting, and both are subject
to the boundary in §9.

```
cd domains/09-security-games-and-attack-lab/src
python3 ceqs_attack_lab.py --self-test    # 5 tests, exits 1 on failure
python3 ceqs_attack_lab.py --all          # experiments A–F  (~2 min here; record says ~5 min)
python3 ceqs_attack_lab.py --negative|--framing|--baseline|--grover|--collision|--challenge
python3 ceqs_attack_lab.py --all --json   # the report results/attack-lab-report.json holds
```

System under test: Mode B **v1.50** (`domains/08-hidden-signers/history/hidden-signer-mode-b-v1.50.py`,
pinned by the harness) at `n = 14`, expansion 8, 64 seats, quorum 43, plus the superseded v1.46 for
the before/after comparison. Every parameter is deliberately weak.

---

## 1. Experiment A — the 24 violation attempts

**Method.** For each attempt, construct a witness, certificate or extraction input that *should* be
refused, hand it to the deployed implementation, and require the implementation itself to refuse it —
recording the reason string it gives. The last attempt is a **positive control** that must succeed,
so that "all 24 rejected" cannot be satisfied by a harness that rejects everything.

**Parameters.** `n = 14`, expansion 8, `N = 64` seats, quorum 43, domain `bytes(range(64))`,
configuration `bytes(64)`, message = a 64-byte digest.

**Result: 0 successful violations of 24.** The positive control extracted 22 seats and every blame
verified.

Each attempt, the reason observed in this repository's re-run, and the property it protects:

| # | attempt | method | observed reason | property |
|---:|---|---|---|---|
| 1 | forged opening: `s` altered | flip a byte of the opening before building the witness | `opening does not match the registry key` | witness soundness |
| 2 | unregistered credential | use an opening that is not in the registry | `opening does not match the registry key` | witness soundness |
| 3 | opening claimed under another seat | present `i`'s opening in the row for seat `j` | `43 rows with distinct seats required` | seat binding |
| 4 | duplicate validator | repeat a seat inside the witness | `43 rows with distinct seats required` | seat binding |
| 5 | witness replayed under another message | same opening, different message | `handle is not r^7 XOR L_c(s)` | handle binding to the message |
| 6 | witness replayed in another domain | same opening, different domain | `opening does not match the registry key` | domain separation |
| 7 | fewer than 43 rows | drop a row | `43 rows with distinct seats required` | quorum size |
| 8 | handles out of canonical order | permute the handle list | `handles must be strictly increasing` | encoding canonicality |
| 9 | duplicate handle | repeat a handle | `handles must be strictly increasing` | encoding canonicality |
| 10 | truncated frame | cut the payload | `payload length mismatch` | frame length |
| 11 | trailing bytes | append a byte | `payload length mismatch` | frame length |
| 12 | wrong magic | patch the header magic | `noncanonical header` | header canonicality |
| 13 | wrong version | patch the version field | `noncanonical header` | header canonicality |
| 14 | wrong suite | patch the suite field | `noncanonical header` | header canonicality |
| 15 | quorum count below 43 | patch the count field | `noncanonical header` | quorum size |
| 16 | non-64-byte message | use a short message digest | `message must be a 64-byte digest` | message domain |
| 17 | duplicate registration | register the same opening twice | `handle collision` | **see the caveat below** |
| 18 | replay of the same certificate | extract from a certificate with itself | `equal messages are not a conflict` | conflict precondition |
| 19 | equal messages | two certificates, same message | `equal messages are not a conflict` | conflict precondition |
| 20 | conflict across domains | two certificates in different domains | `domain mismatch` | domain separation of extraction |
| 21 | certificate from another registry | mix two registries | `configuration mismatch` | registry binding |
| 22 | frame an honest seat | attempt the FRAME win without an opening | fails (the attacker holds no opening) | non-frameability |
| 23 | fabricate blame | submit a blame that was not extracted | `returned False` from `verify_blame` | blame verification |
| 24 | **positive control:** honest conflict | two honest certificates, same domain, different messages | 22 seats extracted, every blame verifies | the gate is not vacuous |

**Why each fails, in one line.** Attempts 1–7 fail because the relation `R_B` is checked against the
registry: a row is accepted only if the opening behind it hashes to that seat's published key in that
domain, and the witness must carry 43 distinct seats. Attempts 8–15 fail because the frame is
canonical: a certificate has exactly one accepted byte-level encoding. Attempt 16 fails because the
message is required to be a 64-byte digest, so the challenge is computed over a fixed-width input.
Attempts 18–21 fail because extraction is defined only for two accepted certificates of the same
configuration and domain with different messages — the four preconditions are checked, not assumed.
Attempt 22 fails because the attacker has no opening for the honest seat (the real cost of finding
one is measured in Experiment B and the FRAME game). Attempt 23 fails because blame is re-verified
publicly rather than trusted.

**Caveat on attempt 17 — a toy-width artefact.** The reason is `handle collision`, not a
duplicate-seat check: at `n = 14` the second registration's handle coincides with the first with
probability `1 − exp(−43·42/2/2^14) ≈ 0.054`, so the implementation refuses the *encode* for an
ambiguous handle set. At production handle width the same encode is accepted (confirmed during this
build by re-running the same construction at `n = 32`, where the duplicate registration is accepted;
the same comparison is recorded in the D9 dossier's reviewer note). The other 23 attempts have no
such artefact. **The gate is therefore "23 attempts whose rejection is structural, plus one that is
rejected for a reason that does not survive the parameter change"** — the count 0-of-24 stands, but
attempt 17 must not be read as evidence that a duplicate registration is refused.

---

## 2. Experiment B — framing: the real search space

**Method.** For each `n`, enumerate the **entire** candidate space of the real key map and count the
marked set `M` — candidates consistent with both the registry key and the published handle — for 6
targets per size, for both handle kinds. Then apply the generic attack and record at which position
it finds the true opening.

**Why enumerate rather than sample.** `M` is the density the ledger's framing row depends on. A
sampled estimate of `M` would leave open the possibility that spurious openings exist at a low rate;
enumeration at these sizes settles it exactly.

| `n` | handle | space | `M` (all 6 targets, both kinds) | mean classical cost | predicted `2^(n−1)` |
|---:|---|---:|---:|---:|---:|
| 8 | `r⁷` and linear | `2^8` | 1 | 88 | 128 |
| 10 | both | `2^10` | 1 | 580 | 512 |
| 11 | both | `2^11` | 1 | 968 | 1,024 |
| 13 | both | `2^13` | 1 | 4,702 | 4,096 |
| 14 | both | `2^14` | 1 | 9,358 | 8,192 |

- **`M = 1` in all 60 target-instances, for both handle kinds.** No spurious opening exists that
  satisfies the handle as well as the registry key.
- The classical-cost column is the rank of the true opening in the enumeration, uniform on
  `[1, 2^n]`, so its mean estimates `2^(n−1)` with a standard error near `0.12·2^n`; the fitted slope
  is **1.107 bits per bit** against a predicted 1.0. Six samples is too few to pin a constant — see
  `docs/game-frame.md` §5.
- **The two handle kinds give identical numbers at every point**, including identical `M` and
  identical mean cost. That is this harness's own evidence that the linearized handle offers the
  attacker no advantage over `r⁷` — the same conclusion the record draws partly from the unshipped
  SAT experiments (README §5).

**B2 — the control, and what the handle costs the defender.** At `n = 8`, enumerating the **joint**
`(s, r)` space without a published handle:

| setting | space | `M` |
|---|---:|---:|
| no handle published | `2^16` | 1 |
| handle published | `2^8` | 1 |

Publishing a handle collapses the attacker's work from `2^(2n)` to `2^n`: guess `r`, derive `s` from
the handle, test `F`. This is the generic attack the ledger charges, and the reason the production
framing row is `2^128` quantum rather than `2^256`.

---

## 3. Experiment C — exact Grover simulation on the real oracle

**Method.** numpy state-vector simulation of Grover's algorithm where the oracle is the **real** key
map plus handle: a candidate `r` is marked iff it opens the target registry key. Run every iteration
up to `2.5·k* + 2`, recording the success probability at each one and comparing with
`sin²((2k+1)θ)`.

**What is simulated exactly, and what is not.** The *algorithm* is exact — the state vector is the
real one, so the measured probabilities are the true ones for this oracle. The *circuit* is not
modelled at all: the oracle is applied as a diagonal phase operator, and no gate count, depth or
error-correction overhead is charged. The ledger charges `≥ 2^18` gates per oracle evaluation
separately.

| `n` | `N` | `M` | measured optimal `k` | predicted `k` | `(π/4)√(N/M)` | success at optimum | max \|sim − theory\| |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 256 | 1 | 12 | 12 | 12.6 | 0.9999 | 4.44 × 10⁻¹⁵ |
| 10 | 1,024 | 1 | 25 | 25 | 25.1 | 0.9995 | 5.33 × 10⁻¹⁵ |
| 11 | 2,048 | 1 | 35 | 35 | 35.5 | 1.0000 | 3.22 × 10⁻¹⁵ |
| 13 | 8,192 | 1 | 71 | 71 | 71.1 | 0.9999 | 2.55 × 10⁻¹⁵ |

Fitted slope of `log₂(iterations)` on `n`: **0.512** against a predicted 0.5. Extrapolated to
`n = 256, M = 1`: `(π/4)·2^128 ≈ 2^128` iterations — the ledger's framing row, here resting on a
measured `M` and a verified iteration law rather than on the formula alone.

---

## 4. Experiment D — the real collision attack (binding)

**Method.** The linear-trick attack on the real key map: fix `δ`, solve the linear system
`F(x ⊕ δ) ⊕ F(x) = 0` for `x` (linear in `x` by quadraticity), keep the first consistent `δ`. 8
trials per point, `N = 16` unknowns.

| `E` | measured mean δ trials | `log₂` | naive prediction `2^E` |
|---:|---:|---:|---:|
| 2 | 11.875 | 3.57 | 4 |
| 4 | 24.25 | 4.60 | 16 |
| 6 | 140.375 | 7.13 | 64 |
| 8 | 449.625 | 8.81 | 256 |
| 10 | 1,988.25 | 10.96 | 1,024 |
| 12 | 15,560.0 | 13.93 | 4,096 |

Fitted slope **1.037 bits per expansion bit** against a predicted 1.0. The measured cost sits about
**+1.2 bits above** `2^E`, and the gap is explained rather than left standing: `δ` always lies in the
kernel of the linear map `A_δ`, so `rank(A_δ) ≤ N − 1` and consistency costs `2^−(E+1)`, not
`2^−E`. **The ledger's `2^−E` density is therefore conservative** — it credits the attacker with
roughly twice the success rate the real attack achieves.

Quantum: Grover over `δ` at the measured density gives `2^(E/2)`; at production `E = 512` that is
`2^256`, the ledger's binding row. (The harness does not simulate this; it applies the verified
`0.5`-slope iteration law to the measured density.)

---

## 5. Experiment E — the independent pass's attack, before and after the fix

**Method.** Reproduce the flaw found in v1.46: two messages whose challenges collide make extraction
divide by zero. Then run the same style of search against v1.50.

| | v1.46 handle (single challenge) | v1.50 handle (linearized triple) |
|---|---|---|
| collision found after | 234 messages (birthday on 14 bits) | 172 messages, on the **first coefficient only** |
| coefficients equal | `c` collides ⇒ attack | `c_a` equal; `c_b`, `c_c` differ |
| extraction result | **FAILED: "inverse of zero"** — nobody named | **named all 22 seats** |
| work to suppress | collision on a 256-bit challenge | collision on the whole 768-bit triple |

**Why partial collisions are useless.** The extractor solves `D(s) = Z₀ ⊕ Z₁` with
`D(s) = αs ⊕ βs² ⊕ γs⁴`, a **linearized (2-)polynomial** of 2-degree ≤ 2 over GF(2^256): its kernel
is an 𝔽₂-subspace of dimension ≤ 2, so it has at most 4 roots. Hence whenever `(α, β, γ) ≠ 0` the
solve returns at most 4 candidate openings, each filtered by the registry lookup, and extraction
still works. Extraction is suppressed **only** when `D ≡ 0`, i.e. all three coefficients collide.
This is what justifies the extractor's `max_free = 2` cap, and it is what makes the fix a genuine
change of output length rather than a new mechanism.

Measured over 3,000 random nonzero triples at each of `n = 16` and `n = 17`: kernel dimension never
exceeded 2 (distribution ≈ 33 % / 50 % / 16 % for dimensions 0 / 1 / 2), and constructed partial
collisions behave as the lemma predicts — `c_a` only: 1-dimensional kernel, ≤ 2 candidates,
extraction works; `c_a` and `c_b`: 0, one candidate, works; all three: `D ≡ 0`, suppressed.

**A correction carried by the record, not made here.** An earlier draft of the record said
suppressing v1.50 costs "2^768" — treating three 256-bit coefficients as three independent preimage
searches. The adversary does not have to *find* the coefficients; it has to make two messages *agree*
on them, which is a collision on a 768-bit output. Using the project's CFHL bound solved for
advantage 1/3 (provenance and re-derivation: `docs/games-methodology.md` §5.3):

| | v1.46: 256-bit challenge | v1.50: 768-bit triple |
|---|---:|---:|
| classical birthday | `2^128` | `2^384` |
| quantum queries (CFHL bound) | **`2^81.7`** | **`2^252.4`** |
| in gate units at `2^18` gates/query | **`2^99.7`** | **`2^270.4`** |
| against the `2^128` gate budget | **broken by 28 bits** | safe by 142 bits |

So the fix moved this row from 28 bits inside the budget to 142 bits outside it. The correct headline
is "a 768-bit collision", never "2^768"; the record states the correction in the open, and this
document repeats it rather than quietly using the corrected figure.

---

## 6. Experiment F — measured exponents and the production ledger

| quantity | measured (toy) | predicted | extrapolation to production |
|---|---:|---:|---|
| framing, classical | slope 1.107 | 1.0 | `2^255` |
| framing, quantum (iterations) | slope 0.512 | 0.5 | **`2^128`** |
| binding collision, classical | slope 1.037 | 1.0 | `2^512` |
| binding collision, quantum | — (density measured) | — | `2^256` |
| marked set `M`, framing | 1 (60/60 instances) | 1 | 1 |
| Grover law deviation | ≤ 5.3 × 10⁻¹⁵ | 0 | — |

Production rows these feed (`domains/08-hidden-signers/src/mode_b_rigorous_ledger.py`, gate units,
`log₂ Pr/G` at `2^128` gates): R1 framing −145.0, R2 binding −209.0, R3 proof soundness −138.1,
R4 simulation −159.4, R5 false positive **−181.2** (corrected from −943 — see
`docs/game-safety.md` §4), total **−137.7**, D2 margin 7.7 bits.

The harness prints these rows; it does not recompute them. They come from the ledger module in
domain 08, and R5's correction was made there (`domains/08-hidden-signers/src/mode_b_rigorous_ledger.py` now computes both
paths), triggered by what the SAFETY game found.

---

## 7. Tests

| test | asserts |
|---|---|
| `test_no_violations` | all 24 attempts behave as Experiment A requires: 23 refusals and one positive control that extracts 22 seats |
| `test_marked_set_is_the_true_opening_only` | `M = 1` for both handle kinds at the sizes Experiment B enumerates |
| `test_grover_matches_theory` | measured optimal iteration count equals the predicted one, and the simulated probabilities track the closed form |
| `test_collision_density` | the measured δ density lies above `2^E` as the kernel argument predicts |
| `test_challenge_fix` | v1.46 is broken by a challenge collision and v1.50 survives a first-coefficient collision with all coefficients not equal |

`--self-test` exits 1 if any fails. Observed in this repository: `Ran 5 tests in 2.832s … OK`,
exit 0.

---

## 8. Sizes and cost

| artefact | bytes | |
|---|---:|---|
| `src/ceqs_attack_lab.py` | 34,708 | 732 lines |
| `results/attack-lab-results.md` | 20,946 | the record, byte-identical to its source revision |
| `results/attack-lab-run.txt` | 5,709 | this repository's re-run transcript |
| `results/attack-lab-report.json` | `--all --json` output | machine-readable report |

Measured here (pinned environment, from `src/`): `--all` exit 0, **54.95 s** in a confirmation run on a
quiet host and **113.51 s** for the run whose transcript is shipped, against a recorded 54.5 s;
`--all --json` 59.63 s and 69.06 s. Another package in this repository measured the same file
independently at 87.6 s. The wall clock moves by up to 3× in both directions with host load — the
recorded baseline ran under a shared host lock alongside the other builds of that session — and
**every measured value is identical in all of those runs**; `VERIFICATION.md` carries each observation
and the reason. The record's own estimate for `--all` is "~5 min", which the recorded 54.5 s already
beat, so that estimate is not a usable comparison in either direction.

---

## 9. The boundary: evidence, not proof

A lab that finds no violation is **evidence, not proof**. It is a finite campaign: one parameter set,
one seed schedule, one pinned revision of the implementation, and 24 attempts chosen by this project.
It shows those attempts fail and that the real attacks scale as the ledger assumes. It does not show
that no attack succeeds, and the record says so in its own words
(`results/attack-lab-results.md` §10, reproduced here as the domain's position):

- **No security level is proven here.** The measured slopes confirm the *scaling laws* the ledger
  assumes; the ledger's absolute rows depend on the reductions in `domains/08-hidden-signers/docs/mode-b-security.md`
  and on the named assumptions A-F1, A-F2, A-P, A-Prove, A-Reg, A-QROM.
- **The proof system's QROM soundness row is transplanted** from FAEST v2 Lemma 9.39, not re-derived
  for this relation.
- **Gate costs are not simulated.** Experiment C counts oracle invocations; the circuit cost is
  charged separately at `≥ 2^18` gates per evaluation.
- **A-P (privacy) remains decisional.** The independent pass found no distinguisher below search;
  that is evidence, not a reduction.
- **The trusted-aggregator premise (A-Prove) is untested** — a protocol assumption, not a property of
  these artefacts.

**Attacks not attempted anywhere in this domain:** cryptanalysis of the key map `F` itself (XL,
hybrid, algebraic elimination, Gröbner, lattice or code-based methods); a real quantum execution;
side-channel, fault-injection and implementation attacks; attacks on the proof system's
zero-knowledge or on VOLE-in-the-head; anything at production parameters — the production runs in the
record's §8 are a size-and-time measurement of the prover and verifier, not an attack. The complete
list, with what each omission would change, is in `docs/validation-status.md`.
