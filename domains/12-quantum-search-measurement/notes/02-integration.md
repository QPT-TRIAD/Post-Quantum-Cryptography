# Milestone 10 — integration, and the three bugs that only composition revealed

**Starting point:** 262 tests passing, every layer green in isolation.
**What integration found:** three real defects, two of them in modules that were already "frozen and
verified", plus two measurement traps that made wrong comparisons look right.

The pattern is worth stating once. None of these was caught by a layer testing itself, because in
each case the layer was self-consistent. They only appear when two things that were validated
against *different* references are put next to each other.

## 1. The cirq `PERM` lowering ran a different permutation than qiskit

`to_cirq` passed the permutation matrix straight to `cirq.MatrixGate`. But qiskit reads qubit 0 as
the **least** significant bit and cirq reads the first qubit of an operation as the **most**
significant one. The same matrix therefore describes two different operations, and cirq executed
the wrong one for every `PERM` gate.

**Why the existing tests could not see it.** `test_round_trip_both_frameworks_is_exact` compares
*gate lists* — names and qubits. Both stayed perfectly correct while the operation they denoted
differed. A round-trip is convention-independent by construction, and this bug lives entirely in
the convention. The same is true of `assert_round_trip`.

**How it was measured.** Comparing raw unitaries fails for a reason that has nothing to do with
either lowering — the two frameworks write *every* multi-qubit gate as a different matrix. So the
cirq unitary is re-indexed by the bit-reversal permutation before comparison:

| circuit | aligned `allclose` before | after |
|---|---|---|
| `X,H,CX,CCX,T,MCZ` on 4 qubits | True | True |
| `PERM` on 2 qubits | **False** | True |
| `PERM` on 3 qubits | **False** | True |
| `PERM` on qubits (0,1,3) of 4 | **False** | True |
| `PERM` on qubits (1,3,4) of 5 | **False** | True |

**The fix had to be symmetric.** Two one-sided fixes both fail: reversing the qubits passed to
`.on()` breaks `from_cirq`, which reads `tuple(int(q.x) for q in op.qubits)` in that same order; and
transforming only the matrix breaks the params round-trip, because `from_cirq` recovers the table by
reading the matrix back. So `_cirq_matrix_convention()` conjugates by the bit-reversal permutation
and is applied on **both** sides — it is an involution, so one function serves as its own inverse.

The regression test is proven non-vacuous: it fails on the old lowering and passes on the new one.

## 2. `ancilla_width` counted the flag, and `oracle_width` counted it again

The abstract method documents itself as "Ancillas the predicate needs, **between the search register
and the flag**". The truth-table branch honours that and returns `0`. The arithmetic branch
computed `len(layout["total"]) - n_search`, and `layout["total"]` includes the `("flag", 1)` entry.

So the two lowerings disagreed about whether the flag is an ancilla, and only one of them was
following its own contract:

| lowering | `oracle_width` before | circuit width | after |
|---|---:|---:|---:|
| truth table | 13 | 13 | 13 |
| arithmetic | **51** | **50** | 50 |

A report that names a width no circuit in the project has is a small lie, but it is not a harmless
one: the width feeds the RAM refusal arithmetic, where 50 qubits is 32 PiB and 51 is 64 PiB. The
invariant both lowerings now satisfy is stated as a relationship rather than a constant, so a future
off-by-one fails loudly instead of matching a stale number:

```
oracle_width(spec, low) == build_phase_oracle(spec, low).num_qubits
```

## 3. `configure_logging()` rejected its own default

The signature is `configure_logging(level: int | str | None = None, ...)`, so `None` is annotated as
valid — and the body raised `TypeError: level must be an int, a str, or None, got NoneType` on it.
The no-argument call, which is the obvious call, did not work. `None` now resolves through
`log_level_from_env()` and falls back to `INFO`; genuinely invalid input still raises, and the CLI's
workaround was removed once the default was measured identical across four environment states.

## Two measurement traps

Both of these produced a *passing* or *almost-passing* result that meant nothing. They are recorded
because they will recur.

**qsim's dtype lies.** `CirqQsimBackend` sets `precision="single"` deliberately, but the statevector
comes back as `complex128`. Aer is exact (`norm² − 1 = 0.0`); qsim is off by `1.86e-07`, which is
≈1.5× float32 epsilon. A tolerance chosen from the dtype would be wrong by seven orders of
magnitude.

**The overlap can be negative.** Because qsim's norm lands slightly *above* one, `|<a|b>|` can
exceed 1 and make the shortfall `1 − |<a|b>|` come out **negative** — reading as agreement even
where there is none. Measured: `−5.6e-08` raw, `9.3e-15` after renormalising. The end-to-end test
now asserts the shortfall's **sign** as well as its magnitude, so skipping the renormalisation fails
instead of passing.

**And the agreement predicate has to be the overlap, not an elementwise difference.** Over a circuit
whose two oracle passes are ~46,000 gates, an elementwise bound of `1e-9` fails at `1.16e-9` purely
on amplitude drift. Asserting on amplitudes reports an engine disagreement that does not exist.

## 4. The negative control was not a negative control

`conftest.py`'s `random_spec` marked two values and its docstring claimed "no structure to find, so
a probe that fires on it is broken". But **any** two-element set is closed under `x → x ^ (a ^ b)`:
it has a genuine XOR-period, `verify_period` returns True, and the probe firing on it was *correct
behaviour*. A control that a correct probe must fail on is not a control.

Replaced with `n_marked = 8`, chosen by measurement rather than taste: every non-zero candidate
period `s ∈ [1, 255]` was tested and none closes the set, both probes stay silent at 4000 and 20000
samples, and at 4000 the silence is the strong kind (`nullity == 0` — "the sampled support is the
whole space") rather than the weak "too few samples" kind. Seeds 1–12 are all silent. `M = 8` is
also the floor `test_cli.py` needs: `k_opt(M=8) = 4` exactly, where `M = 16` would give `k_opt = 3`
and break it. The two-element degeneracy is retained as a test in `test_analysis.py`, so the
reasoning is not lost.

## What the suite asserts now

The end-to-end test is the one that checks the layers still compose: spec → gate list → real engine
→ measured curve, with the peak at the derived optimum, the closed form matched to `1e-9`, the
ancillas returning clean (no amplitude outside the search register), the reported metrics equal to
the ones the IR computes, and the scope-boundary preamble present byte-for-byte in a generated
report. The machine limit is asserted as a refusal in both directions — 50 qubits raises, 12 does
not — so the refusal is a real decision rather than a blanket one.
