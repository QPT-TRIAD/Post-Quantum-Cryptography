## What changed in the prover

The experimental source copy changes six files under `crates/prover/`. The
constraint system, trace circuit, field arithmetic, verifier crates, Fiat–Shamir
schedule, security setting and QVT1 codec are unchanged. The supplied patch applies
to Binius64 commit `37e9cd64e82243cde0e79c7d8ac0dc319f1cbeb4`.

The original multiplication prover keeps the 64 variable-base leaf columns, a
second copy of them inside a product tree, and the other product-tree layers.
The new prover generates one layer when required, feeds it to the existing native
MLE-check prover, and releases it before generating the next. It evaluates the
original leaf columns directly from their compact inputs when their final claims
are needed.

The fixed-base trees are also deferred. Their roots are computed first; their
other layers are discarded and reconstructed just before phase 4 consumes them.
The existing `GlobalAllocator` replaces the reusable buffer pool in this ZK proving
path, so released layers are not all retained in the pool. No custom unsafe
allocator or change to the pool's implementation is introduced.

Shift-key tables are built lazily at the shift phase, using the same deterministic
key builder and a `OnceLock`. Supplied prebuilt keys still use the existing eager
constructor. This keeps those tables out of the multiplication phase.

A duplicate inner verifier is constructed only when replay needs it, after the
large multiplication buffers have been consumed. The native-proof producer also
releases its external verifier after prover setup. Generation and verification
then run in separate processes. The producer explicitly reports that its output
requires independent verification; it never treats successful byte generation as
cryptographic acceptance.

## Why layer recomputation preserves the protocol

For a row with base `g` and 64-bit exponent `b`, let the original bit-column leaf be

\[
L_z = \begin{cases} g^{2^z}, & b_z=1,\\1,& b_z=0.\end{cases}
\]

Define the recomputed layer with `2^k` columns as

\[
T_k(j)=\prod_{t=0}^{2^{6-k}-1} L_{j+t2^k},\qquad 0\le j<2^k.
\]

Then `T_6` is the original leaf layer, `T_0` is its product root, and

\[
T_{k-1}(j)=T_k(j)T_k(j+2^{k-1}).
\]

This is exactly the native product tree's half-buffer pairing. Reordering these
finite-field multiplications changes neither the field element nor its encoding.
Rows beyond the supplied operand columns retain zero exponents and therefore
multiplicative-one leaves, matching the original padding convention.

The prover walks layers 1 through 6 in the original order and calls the same
native `bivariate_product_mle::new_split_half` and `prove_single_mlecheck`
functions. It sends the same pair of evaluations, samples the same recombination
challenge and forms the same next claim at each step. The final leaf claims are
the same inner products with the equality tensor; they are accumulated without
materializing all 64 columns simultaneously.

The other integer-multiplication phases call the existing native methods. Fixed
power tables and reconstructed fixed-base trees have the same field values.
Allocation, deterministic recomputation and delayed construction consume no new
transcript challenges or prover randomness.

This is a construction argument for an equivalent prover, supported by differential
tests and native verification. It is not a machine-checked equivalence theorem,
an independent audit of Binius, or a new QPT security theorem.

## Differential tests

The compiled diagnostic checks every tree layer and all final leaf evaluations
against the original implementation for four row-count shapes: 1, 3, 17 and 64.
These exercise scalar and packed paths and implicit padding.

It then proves complete multiplication protocols with both implementations for
row counts 1, 3, 5, 32, 33 and 129. Inputs include zero, maximum 64-bit values,
high-bit products and random full-width operands. Every output claim and complete
transcript is byte-identical, and the unchanged verifier accepts each transcript.
The optimization is therefore tested beyond the 16-bit-secret special case used
by the trace circuit. The final diagnostic run is recorded in
`recompute_final_checks.json`.

The ordinary upstream `cargo test` entry point could not resolve an uncached
development dependency in offline mode. The same added comparison checks were
built and executed through the included `check_recompute` binary, using the
available dependency set. No upstream test-suite pass is claimed.

Some local multi-unit builds failed with empty object files.
The final adapter configuration uses one code-generation unit for the modified
prover and adapter packages; the successful build log is retained. This is a build
setting, not a proof parameter.

## Memory accounting

For 6,957,056 multiplication constraints, the native protocol pads to `2^23` rows.
The old named multiplication witness buffers subtotal 26.5 GiB before other
working memory. During the new largest variable-base reduction, the named live
allocations are:

| Buffer | Size |
|---|---:|
| One 64-column variable-base layer | 8 GiB |
| Native MLE-check equality tensor | 2 GiB |
| Three fixed-base roots | 0.375 GiB |
| **Named phase-1 subtotal** | **10.375 GiB** |

This is not a bound on total prover memory. It excludes the constraint system,
keys, witness, oracle commitments, transcript, other phases and allocation
overhead. The older 26.5 GiB figure counted named witness buffers, whereas the new
subtotal additionally names the active MLE equality tensor. End-to-end run records,
not subtraction of those subtotals, determine whether the process fits the runner.

## Correction to the initial retry records

The first v1.17 runner mistakenly selected the original v1.16 executable. Its
basename replacement did not match the full path string. Those runs are baseline
reruns, and their memory failures do **not** evaluate the patched prover. The
absence of new phase logs in those runs also provides no evidence about which
phase of the patched prover would fail. Earlier commentary drawing that inference
is superseded by this correction.

`runner_correction.json` identifies the affected labels and the actual executable.
All subsequent `patched_*` execution records contain the executable's absolute
path and SHA-256. Independent verification explicitly selects the original
v1.16 executable. Differential multiplication tests had directly invoked their
patched diagnostic binary and were not affected by the runner error.

## Security and scope

This work concerns the exact trace relation from v1.16: hidden registered seats,
256-coordinate secrets, full A/B/C LWR computations, exact SHAKE links, masked
identities, 43 distinct seats, canonical public handles and context/message
binding. It does not add ML-DSA vote-verification constraints.

The native `SECURITY_BITS` setting remains **96**. There is no new 128-bit QPT
qualification, LWR hardness analysis, extraction theorem or distributed prover.
The synthetic fixture generator centrally holds trace secrets and checks real
ML-DSA signatures outside the proof. It is not an MPC implementation.

The original complete-QC limit remains 32,768 bytes with a 28,480-byte proof
payload. The original `CQ10` parser, missing-backend exception and conflict-
accusation entry point remain unchanged. A successful trace-component proof
cannot authenticate independent votes or establish actual vote equivocation.

Private trace-witness outputs are excluded from the review archive and deleted
after the last proving run. Public configuration, proof bytes, frames, logs,
source and checksums provide the review evidence. The pinned upstream repository
is unchanged; the separate experimental source copy is represented by the patch
and modified source files.
