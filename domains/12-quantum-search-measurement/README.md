# 12 — Quantum search, measured

This domain builds **real reversible oracle circuits** — not matrices, not lookup tables standing in
for circuits — for scaled instances of the relations behind QPT-128, runs **exact statevector**
Grover against them, and counts what the circuits cost.

**What it establishes.** Two things that an amplitude recursion over `(M, N)` cannot establish, and
one negative result about a number the record leans on.

1. *The iteration law holds on the record's own game, measured rather than assumed.* On the reduced
   LM-OTS game the measured success peak equals the textbook Grover iteration count at **every width
   tested**, with the success probability tracking `sin²((2k+1)θ)` to within 5.6 × 10⁻¹⁶ … 2.4 ×
   10⁻¹⁴. Fitted exponent **0.5294** against the record's assumed 0.5; the multi-target law fits
   **−0.5176** against an assumed −0.5.
2. *A reversible SHA-256 compression circuit exists here and is verified bit-for-bit.* 801 qubits,
   **45,392 Toffoli**, 150,128 CNOT, 2,394 X, in an X/CNOT/Toffoli gate set only. It is checked
   against a reference implementation on the FIPS 180-4 vectors, on **every one-block message
   length** (0 … 55 bytes), under property-based random input, and on **64/64 random one-block
   messages** in the campaign run that counted it.
3. *The record's 2^18-gates-per-hash-query floor holds per query, by under one bit — and does not
   hold per hash evaluation.* Counted on that circuit: a query is **2^18.60** gates as built
   (published optimised figure 2^18.83); a single hash evaluation is **2^17.59** as built
   (published optimised T-count 2^17.80), which is **below** 2^18.

**What it does not establish, and this is the load-bearing sentence of the whole domain.** A built
circuit is an **upper** bound on the cost of hashing, while the record uses 2^18 as a **lower**
bound. This domain can therefore show that the floor is consistent with the cheapest circuits
exhibited; it **cannot prove the floor**. Nor is any of it a fault-tolerant cost: **no error
correction is counted**, no magic-state distillation, no depth limit. And no security conclusion is
drawn about any production parameter set — an exact statevector is `2^n` complex amplitudes, so
`n ≈ 24` is the ceiling on ordinary hardware, and a probe that found no structure at `n = 8` found
no structure at `n = 8`.

---

## 1. How to read this domain

| Order | File | What it is |
|---|---|---|
| 1 | this file | what was built, what was measured, what the measurements cannot carry |
| 2 | `src/grover_emulator/circuits/ir.py` | the gate-list IR — the single source of truth every circuit is built as, before any framework sees it |
| 3 | `src/grover_emulator/problem/` | the classical ground truth: instances, search spaces, oracle specifications |
| 4 | `src/grover_emulator/circuits/` | reversible arithmetic, the two oracle lowerings, the diffuser, the SHA-256 compression circuit, the builder |
| 5 | `src/grover_emulator/backends/` | Aer (primary), Cirq/qsim (cross-validation), tensor network (oracle only, high `n`) |
| 6 | `src/grover_emulator/analysis/` | success curve, structure probes, classical baseline, scaling fit |
| 7 | `results/infra-2026-09-20/report.md` | the iteration-law and multi-target campaign, and the structure probes |
| 8 | `results/hash-oracle-cost-2026-09-21/report.md` | what one oracle query costs, counted on the verified circuit |
| 9 | `results/qlwr-n20-truth_table-s20260913/report.md` | a full experiment run at `n = 20`, with its figures |
| 10 | `notes/` | the build log: what was verified, what was found wrong, what changed because of it |
| 11 | `VERIFICATION.md` | the re-run record: commands, environment, observed counts |

---

## 2. Why a circuit, when the closed form is exact

A diagonal phase oracle contributes **nothing** to the success curve. For any marked set the curve
depends on `M` and `N` and on nothing else: `sin²((2k+1)θ)` with `θ = arcsin(√(M/N))`. So "the curve
ran on a simulator" is *not* independent evidence for the curve — an engine executing a diagonal
phase oracle reproduces a function of `(M, N)` that the closed form already gives exactly, and
agreement between the two is a check on the harness, not on the physics.

The circuit's scientific content is two other things:

- **It certifies `M`.** The marked set the closed form is evaluated on is the marked set the circuit
  implements, enumerated at widths where the whole reachable subspace can be walked rather than
  assumed. In the `n = 20` experiment the configuration aimed at a marked fraction of 1.00 × 10⁻⁶
  and the *measured* fraction is 9.54 × 10⁻⁷ (`M = 1` of `N = 1,048,576`). The target is a design
  intention and enters no computation; `M` does.
- **It costs something.** A circuit's cost is not a function of `(M, N)` — it is a function of the
  relation being computed, and no recursion over `(M, N)` can produce it. That is the gap this
  domain exists to close, and §4 is the result.

Every metric — `toffoli_count`, `ir_depth`, `t_count` — is computed from the IR and never read off a
framework's circuit object: framework gates may carry undocumented ancillas, and two frameworks'
`depth()` mean different things. Where a decomposition assumption is unavoidable (7 T per Toffoli,
the ancilla-free MCX bound) it is a named parameter reported beside the number it produced.

---

## 3. The iteration law on the record's own game — measured

Campaign `results/infra-2026-09-20/`, seed 20260920. Widths here are at most 14 search qubits; the
record judges components at `n = 192`, `n = 256` and `T = 2^40`, and nothing below is a measurement
at those sizes.

| width `n` | `M` | textbook `k` | measured peak `k` | `P` at peak | max abs residual against `sin²` |
|---:|---:|---:|---:|---|---|
| 6 | 3 | 3 | **3** | 0.998139 | 1.44 × 10⁻¹⁵ |
| 8 | 3 | 7 | **7** | 0.996846 | 2.44 × 10⁻¹⁵ |
| 10 | 2 | 17 | **17** | 0.999448 | 7.99 × 10⁻¹⁵ |
| 12 | 1 | 50 | **50** | 0.999945 | 2.41 × 10⁻¹⁴ |
| 14 | 2 | 71 | **71** | 0.999916 | 5.55 × 10⁻¹⁶ |

Fitted exponent of `k·√M` in `n`: **0.5294** — a *fit*, not a measurement — against the record's
assumed 0.5.

Multi-target law at `n = 12`, sweeping `M`:

| `M` | 1 | 2 | 4 | 8 | 16 | 32 | 64 |
|---|---|---|---|---|---|---|---|
| textbook `k` | 50 | 35 | 25 | 17 | 12 | 8 | 6 |
| measured peak `k` | **50** | **35** | **25** | **17** | **12** | **8** | **6** |
| `P` at peak | 0.999945 | 0.999997 | 0.999461 | 0.999448 | 0.999947 | 0.995620 | 0.996586 |

Fitted exponent of `k` in `M`: **−0.5176** against an assumed −0.5.

**What the multi-target row does and does not settle.** The law holds for `M` marked inputs of *one*
oracle. Whether `T` signed objects are `T` marks of one oracle is a property of the hashing, not of
Grover: the record's S1 ledger blocks the gain with per-node domain separation and its S2 ledger
grants it to unprefixed Merkle nodes. This campaign confirms the law, not which case a deployment is
in.

**The structure probes, and one refusal.** At `n = 8`, a Simon-style probe and a QFT period probe
were run against the LM-OTS game, a positive control that must fire, and a negative control that
must not. Both controls behaved: the hidden-period control fired on both probes, the random control
on neither. Against the game itself the QFT probe did not fire; the Simon-style probe **refused to
run**, because that lowering leaves one ancilla in the predicate's codomain register where the
cancellation the probe depends on does not hold. A refusal is recorded as a refusal: it is not weak
evidence about a larger width, it is **no evidence at any width**. Silence from a probe that did run
is worth exactly as much as the positive control the same code fires on, and no more — the number of
samples needed to resolve a period grows with the width, while the widths a statevector can hold do
not.

---

## 4. What one oracle query costs — counted on a verified circuit

`results/hash-oracle-cost-2026-09-21/`. The circuit was verified before it was counted: **64/64**
random one-block messages hashed to the reference digest in the same run that produced these counts.
801 qubits; as built, 45,392 Toffoli, 150,128 CNOT, 2,394 X.

An oracle query is hash, **compare**, **un-hash** — a Grover iteration cannot leave the digest
behind, so it pays for the hash twice. One hash is half a query.

Counted here:

| object | metric | count | log₂ | margin over 2^18 |
|---|---|---:|---|---|
| one hash | gates as built (X/CNOT/Toffoli) | 197,914 | 17.59 | **−0.41** |
| one hash | T-count, 7 T per Toffoli | 317,744 | 18.28 | +0.28 |
| one hash | all Clifford+T gates | 833,402 | 19.67 | +1.67 |
| one oracle query, `n = 32` | gates as built | 396,193 | **18.60** | **+0.60** |
| one oracle query, `n = 32` | T-count, 7 T per Toffoli | 637,273 | 19.28 | +1.28 |
| one oracle query, `n = 32` | all Clifford+T gates | 1,670,993 | 20.67 | +2.67 |
| one oracle query, `n = 24` | T-count, 7 T per Toffoli | 636,825 | 19.28 | +1.28 |

Published, for comparison — Amy, Di Matteo, Gheorghiu, Mosca, Parent and Schanck, SAC 2016, **not
derived here**:

| object | metric | count | log₂ | margin over 2^18 |
|---|---|---:|---|---|
| one SHA-256 hash | T-count after T-par | 228,992 | 17.80 | −0.20 |
| one SHA-256 oracle query | T-count, eq. (9) | 466,092 | **18.83** | +0.83 |
| one SHA3-256 hash | T-count after T-par | 499,200 | 18.93 | +0.93 |

**What follows.**

- **Per oracle query the floor holds against every figure here**, counted or published — but the
  cheapest is 2^18.60, a margin of **+0.60 bits**. That is under one bit: the floor is *consistent
  with* the cheapest circuits exhibited, not comfortably below them.
- **Per single hash evaluation the floor does not hold.** 2^17.80 published, 2^17.59 as built — both
  under 2^18. The record is safe on this point only because what Grover calls is the query, not the
  hash. Any ledger line that charges 2^18 to a single classical-style hash evaluation inside a
  quantum attack is charging too much.
- **The floor cites a SHA3-256 figure (499,200 T) but is applied to SHA-256 components.** For
  SHA3-256 one hash alone clears 2^18 by +0.93 bits; for SHA-256 it takes the whole query.

**What does not follow.**

- **That no cheaper circuit exists.** A future construction more than 0.60 bits cheaper per query
  would put the floor above the truth, and every ledger row using it would lose that many bits.
- **That the floor is proved.** A built circuit bounds the cost from *above*; the record needs a
  bound from *below*. These two facts do not meet, and this domain does not pretend they do.
- **Anything fault-tolerant.** No error correction is counted here. The published estimate puts the
  full fault-tolerant SHA-256 preimage attack at about 2^166 logical-qubit-cycles against 2^128
  queries — overhead entirely in the defender's favour, which the record conservatively does not
  claim.

The oracles of §3 are deliberately **not** counted as hash-circuit costs: they are lowered from a
truth table, so the hash is evaluated classically and its answers wired in. Nothing in §3 bears on
the gates-per-query term, and the campaign report says so in its own §D rather than letting a reader
infer it.

---

## 5. Defects this domain found in itself, because composition revealed them

Recorded in `notes/02-integration.md`; each was invisible to a layer testing itself, because in each
case the layer was self-consistent.

| defect | what was wrong | why no existing test saw it |
|---|---|---|
| the Cirq `PERM` lowering ran a different permutation | one framework reads qubit 0 as least significant, the other reads the first qubit of an operation as most significant; the same matrix denotes two operations | the round-trip test compares *gate lists*, which stayed correct while the operation they denoted differed. The fix conjugates by the bit-reversal permutation on **both** sides, because either one-sided fix breaks the other direction |
| `ancilla_width` counted the flag and `oracle_width` counted it again | the truth-table branch returned 0 as documented; the arithmetic branch included the flag, reporting width 51 for a 50-qubit circuit | nothing compared the reported width against a built circuit. The width feeds the RAM refusal arithmetic, where 50 qubits is 32 PiB and 51 is 64 PiB. The invariant is now a relationship, not a constant |
| `configure_logging()` rejected its own default | `None` is annotated valid and the body raised on it | the obvious no-argument call was never made in a test |
| the negative control was not a negative control | a two-element marked set is closed under `x → x ⊕ (a ⊕ b)`, so it has a genuine XOR-period and a correct probe **must** fire on it | a control a correct probe must fail on is not a control. Replaced with `M = 8`, chosen by measurement: every non-zero candidate period in `[1, 255]` was tested and none closes the set, both probes stay silent at 4,000 and 20,000 samples, and seeds 1–12 are all silent |

Two measurement traps are recorded in the same note because they produced almost-passing results
that meant nothing: qsim's statevector comes back as `complex128` although single precision was
requested deliberately, so a tolerance chosen from the dtype would be wrong by seven orders of
magnitude (Aer is exact, `norm² − 1 = 0.0`; qsim is off by 1.86 × 10⁻⁷, about 1.5× float32 epsilon);
and because that norm lands slightly *above* one, the shortfall `1 − |⟨a|b⟩|` can come out
**negative** — reading as agreement where there is none. Measured −5.6 × 10⁻⁸ raw, 9.3 × 10⁻¹⁵
after renormalising. The end-to-end test now asserts the shortfall's **sign** as well as
its magnitude.

---

## 6. What this domain does not establish

- **No security conclusion about any production parameter set.** Every circuit is built and
  simulated at a width where the state space fits in memory on one machine.
- **The gates-per-query floor is not proved.** §4: upper bound against lower bound. The strongest
  honest statement is consistency, with a margin under one bit.
- **No error correction, no fault tolerance, no depth budget.** These are logical gate counts.
- **No real quantum execution.** Everything is exact classical simulation of the algorithm.
- **A silent probe bounds nothing.** Absence of detected structure at `n = 8` is evidence about
  `n = 8`. The refused probe is not even that.
- **Every value above the statevector ceiling is a fit**, labelled as a fit wherever it appears, and
  never quoted in place of a measurement. The fitted exponents 0.5294 and −0.5176 are fits to five
  and seven measured points.
- **The published SAC 2016 figures are transplanted, not re-derived.** They are printed beside the
  counted ones so a reader can see both; nothing here reproduces them.
