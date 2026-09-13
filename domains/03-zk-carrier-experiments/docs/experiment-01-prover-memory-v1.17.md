# Experiment 1 — v1.17: making the prover fit, without changing what it proves

## The problem

The native proof of the 43-seat trace relation did not fit its runner. For 6,957,056 multiplication
constraints the native protocol pads to `2^23` rows, and the original prover's *named* multiplication
witness buffers alone subtotal **26.5 GiB** before any other working memory
(`docs/method.md`, "Memory accounting"). The constraint system, the trace circuit, the field
arithmetic, the verifier, the Fiat–Shamir schedule, the security setting and the codec all had to stay
exactly as they were: the whole point of this experiment was to change the prover's *memory
behaviour*, not the statement it proves, and any change to the transcript would have invalidated the
comparison with everything that follows in this domain.

## The relation carried

The exact trace relation of v1.16, unchanged: hidden registered seats, 256-coordinate secrets, full
A/B/C LWR computations, exact SHAKE links, masked identities, 43 distinct seats, canonical public
handles and context/message binding. **No ML-DSA vote-verification constraints** — the synthetic
fixture generator checks real ML-DSA signatures *outside* the proof, and `docs/method.md` states this
plainly.

## The backend, and which part of its theory applies

Backend: Binius64's prover, at the pinned commit (see `docs/provenance.md`). The part of its theory
that is used here is one algebraic identity of the product tree — the domain's `D3-09`.

For a row with base `g` and 64-bit exponent `b`, the original bit-column leaf is
`L_z = g^{2^z}` if `b_z = 1` and `1` otherwise. The recomputed layer with `2^k` columns is

```
T_k(j) = Π_{t=0}^{2^{6-k}-1} L_{j + t·2^k},        0 ≤ j < 2^k,
```

so `T_6` is the original leaf layer, `T_0` is its product root, and

```
T_{k-1}(j) = T_k(j) · T_k(j + 2^{k-1}).
```

That is exactly the native product tree's half-buffer pairing, and reordering finite-field
multiplications changes neither the field element nor its encoding. Rows beyond the supplied operand
columns keep zero exponents and therefore multiplicative-one leaves, matching the original padding
convention.

**Only this identity is borrowed.** No claim is made that the modified prover is *equivalent* in any
machine-checked sense. `docs/method.md` says so directly: this is "a construction argument for an
equivalent prover, supported by differential tests and native verification. It is not a machine-checked
equivalence theorem, an independent audit of Binius, or a new QPT security theorem."

## How the adapter bridged it

Six files under `crates/prover/` were changed, distributed here as `src/prover_memory.patch`
(sha256 in `docs/provenance.md`; the full digest table of the six modified sources is in
`results/source-comparison.json`):

1. **Layer-at-a-time generation.** One layer is generated when required, fed to the existing native
   MLE-check prover, and released before the next is generated. The prover still walks layers 1
   through 6 in the original order and calls the same
   `bivariate_product_mle::new_split_half` and `prove_single_mlecheck` functions.
2. **Direct leaf evaluation.** The original leaf columns are evaluated directly from their compact
   inputs when their final claims are needed, instead of being materialized twice.
3. **Deferred fixed-base trees.** Their roots are computed first; the other layers are discarded and
   reconstructed just before phase 4 consumes them.
4. **Allocator.** The existing `GlobalAllocator` replaces the reusable buffer pool in this ZK path, so
   released layers are not all retained in the pool. No custom unsafe allocator and no change to the
   pool's implementation.
5. **Lazy shift keys.** Shift-key tables are built at the shift phase behind a `OnceLock` using the
   same deterministic key builder; prebuilt keys still use the eager constructor.
6. **Delayed inner verifier.** The duplicate inner verifier is constructed only when replay needs it,
   after the large multiplication buffers have been consumed; the native-proof producer releases its
   external verifier after prover setup, and generation and verification run in separate processes.

The producer explicitly reports that its output requires independent verification; a successful byte
generation is never treated as cryptographic acceptance.

## Tests

The compiled diagnostic checks every tree layer and all final leaf evaluations against the original
implementation for **four row-count shapes: 1, 3, 17 and 64** — exercising scalar and packed paths and
implicit padding. It then proves complete multiplication protocols with both implementations for
**six transcript shapes: row counts 1, 3, 5, 32, 33 and 129**, with inputs including zero, maximum
64-bit values, high-bit products and random full-width operands. Every output claim and complete
transcript is byte-identical, and the unchanged verifier accepts each transcript.

Recorded result, `results/recompute-final-checks.json` (retained verbatim):

```json
{ "all_passed": true, "layer_and_leaf_fixture_shapes": 4,
  "complete_transcript_fixture_shapes": 6, "oracle_protocol_unchanged": true,
  "native_verifier_checks_retained": true }
```

This is a re-run in this repository only in the sense that the JSON is readable here; **the diagnostic
binary is not present and the check was not re-run.** What *was* checked here is that every later
version's size ledger uses this patch's parameters unchanged.

## Sizes and cost

| Buffer during the new largest variable-base reduction | Size |
|---|---:|
| One 64-column variable-base layer | 8 GiB |
| Native MLE-check equality tensor | 2 GiB |
| Three fixed-base roots | 0.375 GiB |
| **Named phase-1 subtotal** | **10.375 GiB** |

The source is explicit that this is **not** a bound on total prover memory: it excludes the constraint
system, keys, witness, oracle commitments, transcript, other phases and allocation overhead. The older
26.5 GiB figure counted named witness buffers; the new subtotal additionally names the active MLE
equality tensor. `docs/method.md` states that end-to-end run records, not subtraction of those
subtotals, determine whether the process fits the runner.

## Verification results

Recorded evidence `results/source-comparison.json`, which is also the provenance record for the
backend: all other tracked upstream files are byte-identical; **all verifier sources are
byte-identical; the trace circuit is byte-identical; the codec is byte-identical**. The original
verifier binary's sha256 and the modified prover binary's sha256 are both recorded there, which is
what makes the equivalence claim checkable in principle: the verifier that accepts the new transcripts
is the *unmodified* one.

## Negative controls, and a correction the experiment had to publish

The experiment's first runner selected the **original v1.16 executable** because a basename
replacement did not match a full path string. Those runs are baseline reruns, and their memory
failures do **not** evaluate the patched prover; the absence of new phase logs in them is no evidence
about which phase of the patched prover would fail. `docs/method.md` states that earlier commentary
drawing that inference is superseded by the correction, and that later records carry the executable's
absolute path and SHA-256. The affected label list is in `runner_correction.json` (a record of the
experiment, not retained in this repository).

A second, unrelated limitation is recorded rather than hidden: the ordinary upstream `cargo test`
entry point could not resolve an uncached development dependency in offline mode, so the comparison
checks were built and executed through the included `check_recompute` binary instead. **No upstream
test-suite pass is claimed.** Some local multi-unit builds failed with empty object files; the final
adapter configuration uses one code-generation unit for the modified prover and adapter packages. That
is a build setting, not a proof parameter.

## Conclusion

The patch was carried forward into every adapter in this domain, and the equivalence of the *transcript*
— not just of the memory profile — is what made the later size comparisons meaningful: v1.25, v1.27,
v1.27b, v1.28 and v1.28p all compare proofs produced by a prover with this patch, verified by a
verifier without it. Nothing here qualifies the protocol: `SECURITY_BITS` remains 96, and the
experiment explicitly does not add a 128-bit QPT qualification, an LWR hardness analysis, an extraction
theorem or a distributed prover.
