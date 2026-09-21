# Milestone 1–3 — the arithmetic lowering, and what it actually costs

**Gates passed:** every arithmetic block exhaustively verified; both QLWR lowerings agree with the
marked set on every basis state; the oracle sandwich is the identity; the full Grover curve matches
the closed form to `1e-15` at n=4.

## Why hand-built arithmetic

Two framework blocks were tried first and both were rejected on measurement, not on taste:

- `WeightedSumGate` declares 6 qubits for 3 state qubits and then cannot be synthesised without
  **three further clean ancillas**. A gate whose real width exceeds its recorded width is exactly the
  hazard that lets a RAM-budget check pass while the run swaps.
- `CDKMRippleCarryAdder` is correct but carries **no `.definition`**, so it cannot be expanded into
  IR gates and would have to be counted as an opaque blob. Not being able to count what ran is the
  thing this project exists to avoid.

So the blocks are written directly against the IR and verified exhaustively: `add_constant` for
every constant at every width `n <= 5`, controlled and uncontrolled; `less_than_constant` for every
boundary at every width `n <= 6`; `equal_to_constant` for every value at every width `n <= 5`. Each
verification also checks that the block's work ancillas come back clean, and the controlled adder
checks that it did not overwrite its own control qubit.

## The construction, and the two things that made it cheap

**Addends are reduced mod `q_L` as classical constants.** Reducing each `X_ij * 2**t` before it is
added is sound because reduction distributes over addition, and it bounds the accumulator at `q_L`
rather than at `nu * (q_L - 1)**2`. One conditional subtraction after each controlled addition
restores it to `[0, q_L)`. The accumulator is therefore `w + 1` bits rather than `2w`, and **the
circuit contains no modular reduction block at all** — the reduction is folded into the constants and
into one conditional subtraction per addition.

**The interval table is one period, not 118.** Because `round_half_up((v + k*q_L)*p, q_L) ==
round_half_up(v*p, q_L) + k*p`, the sample is periodic in the accumulator. The alternative
construction — compare the raw wide accumulator against a table repeated across every period —
needs 826 comparators for this instance. Comparing against the reduced accumulator needs **7**,
one per row. The reduction is not skipped anywhere; it is absorbed into the constants.

The wrap case is real and is handled: for `a = 0` the bucket is the **union** of the bottom interval
and the top one, because the raw rounded value `p` reduces to `0` under the trailing `mod p`. It
fires only for accumulator values in the top `1/p` of the range, which no random instance reaches,
and a circuit that omitted it would still agree with the relation on all but a handful of rows while
usually still producing `M = 1` and the right peak. It would not look like a bug. It is tested by
construction.

## The predicate contract changed, on purpose

The first version required `build_predicate` to return ancillas clean. It does not, and the
assertion that caught this was wrong rather than the circuit. A predicate is always used inside the
sandwich `predicate ; Z(flag) ; predicate.inverse()`; the inverse is exact, so every ancilla returns
to `|0>` whether or not the forward pass tidied up. Requiring cleanness would mean uncomputing the
accumulator at the end of every row, doubling the gate count of the thing being counted.

The property the tests assert is now that **the sandwich is the identity** — strictly stronger than
cleanness, and it is the property the oracle actually needs.

One consequence worth recording: the conditional-subtract controls are deliberately left dirty and
are cleaned by the row's own inverse pass. That is what lets **one pool of 12 control qubits serve
all seven rows** instead of one pool per row. Building the cleanup inside the reduction instead does
not work at all: the comparison result is not recoverable from the reduced accumulator, because the
subtraction has already changed the value it was computed from.

## The measured numbers

Instance at `n_search = 12`: `q_L = 61`, `nu = 2`, `w = 6`, `p = 19`, `m = 7`, `M = 1`,
`N = 4096`, embedding gap 375 states that encode no valid secret.

| lowering | qubits | gates | depth | Toffoli (logical) | ancillas |
|---|---:|---:|---:|---:|---:|
| truth table | 13 | 15 | 3 | 1 | 0 |
| arithmetic | 50 | 11,634 | 7,267 | 6,738 | 38 |

**The ratio is 1 : 776.** For `M = 1` the truth-table oracle is a *single* multi-controlled Z, and
the arithmetic circuit that computes the same predicate is 11,634 gates. That is the headline number
this project exists to produce: what a real circuit for the relation costs, against the algorithmic
simulation's implicit assumption that the oracle is free.

**The arithmetic lowering is 50 qubits wide and is not exact-statevector-simulable at any sweep
point.** That is forced, not tunable — the accumulator, its comparator work chain, the row flags and
the control pool are all necessary. It is validated by classical bitmask simulation instead, which is
exact and costs `8 * 2**n` bytes rather than a matrix.

## Generation

`generate_scaled_instance` does not trust the uniqueness inequality. It builds a candidate, counts
the marked set **exhaustively**, and rejects unless the count is exactly 1, widening the sample count
`m` when it must. The inequality is a lower bound with no upper bound attached; the count is the
count.

Generic primes below 64 are `{11, 13, 19, 23, 29, 37, 41, 43, 47, 53, 59, 61}` — note that 3, 5, 7,
17 and 31 are excluded as Mersenne or Fermat forms. This is why the smallest structurally faithful
instance is 12 search qubits: over `w = 5` the generic primes are `{19, 23, 29}`, which leaves
`p` in `{3, 5, 7}` against the rounding-gap requirement — and all three are special forms. There is
no admissible `p` at `w = 5`.

## The reduction theorem, confirmed exhaustively

`round((u + k*q_L) * p / q_L) == round(u * p / q_L) + k*p  (mod p)`, so reducing the inner product
mod `q_L` before rounding cannot change the marked set. Checked at `n_search = 12`: the marked sets
computed with and without the inner reduction are **identical** — both `{1067}`. The reduction is
carried anyway, behind `QLWRInstance.reduce_mod_ql`, because it is required under the alternative
reading of the relation and because a redundancy that must hold for a reason unrelated to either
implementation is the most valuable property test in the oracle.
