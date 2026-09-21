# Milestone 0 — framework API probe

**Gate:** `scripts/probe_apis.py` exits 0. **Result:** 59 checks, 0 required failures, exit 0.
Verified against qiskit 2.5.2, qiskit-aer 0.17.2, cirq 1.7.0, qsimcirq 0.22.1, quimb 1.15.0,
cotengra 0.8.2, sympy 1.14.0, numpy 2.5.3, numba 0.67.0.

The design pass named the framework classes this project would use, on the strength of documentation
reading. Documentation is not execution. This milestone turns each of those claims into something
that runs, and five of them did not survive.

## Findings

**1. `MCZGate` does not exist in qiskit 2.5.2.** It was listed as confirmed-present-and-usable. It is
not in `qiskit.circuit.library` at all. `MCPhaseGate` is. The substitution is exact and verified:
`MCPhaseGate(pi, k-1)` is diagonal and applies `-1` on exactly the all-ones state, checked over every
basis state at `k = 3`. The IR's `mcz` is therefore lowered through `MCPhaseGate` — or, if that ever
changes, as `H · MCX · H` on the last qubit, which is always available.

**2. `WeightedSumGate` cannot be synthesised inside its own declared width.** With 3 state qubits it
declares 6 qubits, and the high-level-synthesis plugin then demands **3 further clean ancillas** to
synthesise at all: `Cannot synthesize a WeightedSumGate on 3 state qubits with less than 3 clean
auxiliary qubits. Only 0 are available.` This is precisely the hazard the build plan flags — a
framework gate whose *real* width exceeds its *recorded* width would let a RAM-budget check pass and
the run swap. **Decision: the dot product is built from conditional constant-adds against the IR, and
`WeightedSumGate` is not used.** Its weight-to-qubit ordering was measured anyway, before the
decision: `weights[i] -> qubit i`, little-endian, matching this project — so the reversal hazard the
plan warned about does not actually bite. The gate is dropped for the ancilla reason, not that one.

**3. `CDKMRippleCarryAdder` is not ancilla-free.** It was described as ancilla-free with
`num_qubits = n + 1`. Measured: `num_qubits = 2n + 2` for `kind='full'` and `'half'`, `2n + 1` for
`'fixed'` — i.e. two operands of `n` qubits each, plus one or two ancillas. The class adds two
*n*-qubit registers; it is not a constant-adder. It remains the right block, but the budget
arithmetic carries the extra qubits and the conditional-constant-add wraps it in one control.

**4. `PermutationGate` permutes qubit *positions*, not basis states.** This is the finding that would
have been hardest to notice later. The class name and its `pattern` argument read as though they
expressed a permutation of computational basis states — which is what the IR's `perm` gate means, and
what a nonlinear S-box needs. They do not: `num_qubits` is `len(pattern)`, and the operation is a
relabelling of qubit indices. The consequence is a group-order argument, not a preference — qubit
relabellings on `b` qubits have order `b!`, basis-state permutations have order `2**b!`. On two
qubits that is 2 maps against 24, and the probe measures exactly that. Substituted lowering,
verified exact on all 8 basis states of a deliberately nonlinear 3-bit S-box: `UnitaryGate` of the
permutation matrix.

**5. `QuadraticFormGate`'s convention is well-behaved.** The one gate whose documentation was too
thin to build on, and it came back clean: over 48 inputs across 3 random `(A, b, c)` at `N = 4`,
`m = 1`, the gate matches `x^T A x + x^T b + c` with `A` used **as given**, not symmetrised and not
read as a triangle. The hand-built Toffoli fallback is not needed.

**6. `PhaseOracle` and `IntegerComparator` are still present** — deprecated but not removed, so a
dependency on them would work today and break later. Both are non-required checks; the project uses
neither. `BooleanExpression` and the whole `qiskit.circuit.classicalfunction` module are confirmed
**removed**, as the plan predicted.

## What this changes

- `ir.py`'s `mcz` lowers through `MCPhaseGate`, not `MCZGate`.
- The QLWR accumulate stage is hand-built; `WeightedSumGate` is out.
- The adder's ancilla cost enters the width formula as `2n + 1` or `2n + 2`, not `n + 1`.
- `perm` lowers through `UnitaryGate`, verified; `PermutationGate` is unusable for it.
- `QuadraticFormGate` is available for the Mode-B key map without a fallback.

Every one of these was a name that appeared to exist and behave as documented. The probe is cheap;
each of the five would have been expensive to find later, and three of them would have failed
silently rather than loudly.
