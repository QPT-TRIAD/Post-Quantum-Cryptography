# The phase-GHZ security check

Source: `src/phase_ghz_security_check.py` (v1.40). Script:
`python3 src/phase_ghz_security_check.py --self-test` runs 12 test groups; `--explain` prints the
mathematical discussion; the bare invocation exits 2 with an argparse usage message. All paths are
relative to the repository root.

## 1. The proposal, and why it was worth checking

The proposal under audit was a circuit — a Hadamard, a `T` gate, then a chain of CNOTs on `n = 128`
qubits — offered as a security ingredient: a source of phase structure that would make the quorum
construction harder to attack, and ultimately contribute to a `2^−128` failure exponent.

It is worth checking rather than dismissing because the state it prepares is genuinely non-classical:
it is entangled, its phase is not a global phase, and it can be prepared with `n + 1` gates. The
question is whether any of that creates a *security* property. The audit's answer is no, and the
reason is instructive: preparation theorems and security theorems have different quantifier shapes,
and the gap between them cannot be closed by substituting `n = 128`.

## 2. What the circuit does — exactly

The theorem, proved by induction in the source and checked in exact arithmetic over
`Q[ζ]/(ζ⁴ + 1)` with `ζ = exp(iπ/4)`:

```
P_n |0⟩^⊗n  =  ( |0⟩^⊗n  +  ζ |1⟩^⊗n ) / √2.                   (1)
```

At `n = 128` this uses `n + 1 = 129` ideal logical gates and has serial depth 129. A binary-tree
fanout schedule achieves 7 CNOT layers plus `H` and `T`, i.e. 9 layers — the source states this as an
achievable schedule and explicitly "not a claim of optimal hardware depth". The phase variants were
tabulated, including the per-link conditional phase `ζ^n` with `ζ^128 = 1`.

The state's information content is exactly one bit: computational-basis measurement yields two
outcomes with probability 1/2 each, so the Shannon entropy is 1 bit; every bipartition of the qubits
carries 1 ebit of entanglement; and

```
⟨X^⊗n⟩  =  1/√2,
```

against 1 for the standard GHZ state. The phase is real and detectable — and public.

## 3. Theory and standards used

| Reference | Statement **as used here** | What it justifies | Full / partial |
|---|---|---|---|
| IBM Qiskit `TGate` documentation; IBM Learning on global versus relative phase | the definition of the `T` gate and the distinction between a global and a relative phase | the state theorem and the phase-variant table | **definitions only** |
| Watrous, "Quantum Computational Complexity" | the definition of BQP | the quantifier correction of §4: `QPT` names a class of algorithms, and state preparation supplies no decision problem | **definition only** |
| FIPS 205 §1.1 | the security basis of SLH-DSA | the interface of the game the lemma is inserted into | **partial** |

No cryptographic theorem is imported, because the file's conclusion is that none applies. The
simulation lemma of §5 is the project's own, and it is stated with its cost.

## 4. The quantifier error

The circuit theorem establishes the existential statement

```
There exists an efficient P_n that prepares the specified state.
```

A signature-security theorem needs a universally quantified bound of a different form:

```
For every adversary A in a specified quantum resource class R,
Pr[A outputs a valid fresh-message forgery]  ≤  ε_R.            (2)
```

In an asymptotic theorem the probability must be negligible as the security parameter grows; a
concrete theorem additionally fixes parameter sets, query counts, computational resources and the
target success bound. The preparation `P_n` contains no challenge public key, no signing oracle, no
hash-security game and no acceptance rule for a forged signature. Consequently (1) provides **no**
upper bound for (2). The source calls this "a logical gap, not a missing factor that can be supplied
by substituting `n = 128`". Nothing in the file is a measurement of any physical device, and no
physical error rate is measured.

Two related conflations are named and refused. State preparation alone supplies no decision problem
or acceptance criterion that has been shown to be in BQP, so "BQP" does not turn a prepared state
into a difficulty statement; and neither term defines cryptographic strength by the number of qubits
used.

## 5. The lemma worth keeping

The audit's positive contribution is a simulation lemma, and it is the reason v1.41 cites this file.

Fix an arbitrary signature game `G` and an adversary `A` that is initially given the state `|ψ_n⟩` in
a fresh register. Assume the register is independent of the key, the challenge, the oracle state and
`A`'s other initial registers. *This independence refers to the moment of preparation*; `A` may
afterwards interact the register with public data or oracle responses.

Construct `B` in the ordinary game: initialise `n` zero qubits, apply `P_n`, then run `A` with that
register, forwarding every permitted oracle interaction exactly as in `G`. After preparation the
joint states in the two experiments are identical, and the continuation is the same quantum process,
measurements and adaptive classical interactions included. Hence the transcript distributions and the
final output distributions coincide, and

```
Pr[B wins ordinary G]  =  Pr[A wins G with supplied ψ_n].       (3)
```

The extra preparation uses `n + 1` logical gates and **no** signing or hash-oracle queries. In a
compatible gate-count model, if `A` has a `t`-gate continuation,

```
Adv_{G,ψ_n}(t, q_H, q_S)  ≤  Adv_G(t + n + 1, q_H, q_S).        (4)
```

Three qualifications travel with (4) and the source states all three. The initialised `n`-qubit
register must be included in the width and memory budget; (4) suppresses that coordinate only to
simplify notation, and "it does not say that the advantages at the same strict time budget are
equal". For polynomial `n` the simulator is still QPT whenever `A` is. And the lemma grants no
inverse signing-oracle access, no hidden keys, and no permission to erase signing-query history.

For `c` independent copies the extra cost is `c(n + 1)`. This construction does not clone an unknown
quantum state, and an extractor that reinitialises adversaries or requires extra copies must include
those costs.

**Physical preparation.** If a physical preparation supplies a state within trace distance `η` of the
ideal one, contractivity under quantum processing bounds the change in any final event probability by
`η` for one supplied copy, and a hybrid argument gives at most `c·η` for `c` independent preparations
with that guarantee. The source labels this a conditional observation requiring an actual distance
bound; the ideal gate model has `η = 0`, and no physical error rate is measured here.

**A classical sanity check.** Before any subsequent interaction, for a classical key `K` the joint
state is `ρ_KQ = ρ_K ⊗ |ψ_n⟩⟨ψ_n|`, so the auxiliary register alone has **zero** mutual information
with `K`. The source is careful about the scope of that remark: it "is not a claim that an adversary
cannot learn from later public-key or oracle interactions."

**Public-state reproduction.** v1.41 §2 carries the argument one step further and is where the state's
security role ends: for any verifier accept effect `0 ≤ M_{k,x} ≤ I`, even one chosen using secret
verifier randomness, acceptance probabilities for the honest and the reproduced state are equal,
because both tests receive the same density operator. No unknown state must be cloned or intercepted,
and the state contributes no positive honest-versus-reproduction mismatch gap.

## 6. Inserting the lemma into the signature reduction

Retaining the v1.38 premises and defining `ε_SLH` as the ordinary single-user fresh-message forgery
advantage at stated resources, if the reduction uses `c` fresh copies of this 128-qubit state then a
conservative charge is

```
p_conflict  ≤  κ_E + L_E [ δ_B + 64·ε_SLH(t_R + 129c, q_H, q_S) ].   (5)
```

Here `t_R` counts the other reduction work, and the `64` is the identity-selection factor for the
adaptive case; for the known static set of 21 corrupt seats the existing factor 43 applies instead.
The source adds two guards: if state preparation is already counted in `t_R`, do not add it again, and
"any separately justified outer setup-distance term is added as before".

The insertion is a **resource** charge. It is not a probability multiplier, and it is not a security
argument in the state's favour.

## 7. Tests

`python3 src/phase_ghz_security_check.py --self-test` runs 12 test groups and exits 0, in exact
arithmetic over `Q[ζ]/(ζ⁴+1)` with sparse basis-state dictionaries and `INV_SQRT2 = (0, 1/2, 0, −1/2)`.

| Group | What it asserts |
|---|---|
| 01 | `\|ζ\| = 1`, `ζ⁸ = 1`, `(1/√2)² = 1/2` |
| 02 | the exact 128-qubit state and its norm (including a constant check that `1 + 1 + 127 == 129`) |
| 03 | the state theorem for `n ∈ 120…136 ∪ {1, 2, 32, 64, 92, 256}` |
| 04 | the reverse circuit returns `\|0⟩` |
| 05 | two measurement outcomes, each with probability 1/2 |
| 06 | X-parity `1/√2` versus 1 for standard GHZ |
| 07 | a global per-link phase leaves the density matrix unchanged |
| 08 | conditional per-link phases `ζ^n` for `n = 120…136`, and standard GHZ at 128 |
| 09 | reduced density matrices for three cuts |
| 10 | the tree schedule is valid and gives the same state in 9 layers at 128 |
| 11 | an independent auxiliary state has the same reduced state for both bit values (`n = 5`) |
| 12 | the constructed and the supplied state are identical (`n = 5`) |

Group 07 is the one that carries the security conclusion: a phase that leaves the density matrix
unchanged cannot be a security resource.

## 8. Sizes and cost

| Quantity | Value |
|---|---|
| Source file | 21,244 bytes, 526 lines |
| Recorded runtime | 0.173 s (12 tests), exit 0 |
| Gate count | `n + 1` = 129 at `n = 128`; depth 129 |
| Alternative schedule | 9 layers (7 CNOT + `H` + `T`) at `n = 128`, stated as achievable, not optimal |
| Entropy | 1 bit; 1 ebit per bipartition |
| `⟨X^⊗n⟩` | `1/√2`, versus 1 for standard GHZ |
| Simulation cost | `n + 1` gates per copy, `c(n + 1)` for `c` copies, plus the width of the register |

## 9. Packages and tools used

Python standard library only: `fractions`, `argparse`, `unittest`. The state algebra is exact — sparse
dictionaries over the basis of `Q[ζ]/(ζ⁴+1)` with `Fraction` coefficients — so the "128-qubit state"
checks are exact rational computations rather than floating-point approximations of a large vector.
There is no quantum simulator, no hardware, and no third-party package; the state preparation is
computed algebraically, which is why the tests can reach `n = 256` and still be exact.

## 10. Validation status

- **Proven.** Eq. (1) by induction; the gate and depth counts; the entropy and entanglement
  statements; the X-parity; the simulation lemma (3)–(4) and its cost; the `c·η` trace-distance
  observation under its premise.
- **Measured.** The twelve exact finite checks; no cryptographic or physical measurement is
  performed.
- **Abandoned.** The security claim. The source's own summary is that the circuit gives no bound of
  form (2), and the "qubit count or phase implies 128-bit security" inference is dropped.
- **Kept and reused.** The simulation lemma, cited by `src/hybrid_sampling_bound_audit.py` (v1.41) as
  the source of the `129c` gate charge.

## 11. Open items

1. No security bound of form (2) was ever obtained from this circuit, and none is currently expected.
2. The trace-distance term `η` has no measured value; the ideal model sets it to zero by assumption.
3. The lemma's independence premise is at the moment of preparation; a construction that entangles
   the auxiliary register with key material at preparation time is outside its scope.
4. The charge `129c` is a gate count in a compatible model. It is not a probability and does not
   enter the bound as one.
