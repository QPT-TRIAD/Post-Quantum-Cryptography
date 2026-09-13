# Signature reductions: from a conflict to a forgery

Sources: `src/signature_security_reduction.py` (v1.37, ML-DSA-87 endpoint),
`src/slh_dsa_signature_reduction.py` (v1.38, SLH-DSA endpoint and hybrid),
`src/signature_margin_sweep.py` (v1.39, exact thresholds). Scripts:
`python3 src/signature_security_reduction.py --self-test`,
`python3 src/slh_dsa_signature_reduction.py --self-test`,
`python3 src/signature_margin_sweep.py --report`. All paths are relative to the repository root.

## 1. The problem, and why it is hard

A decoder that names 22 seats is evidence, not a security argument. The certificate has to be
*unforgeable*, and the natural claim is: producing two conflicting certificates is as hard as
forging a standard signature. Making that claim means building a reduction that turns any adversary
who produces a conflict into a forger against a named scheme — and then stating its cost honestly,
in the currency the target is denominated in.

Two things make this hard. The first is that the object being reduced is not a signature but a
*threshold* object: 43 seats each hold an approval signature, at most 21 of them may be corrupt, and
the adversary picks which. A naive reduction must guess which seat to embed its challenge key at, and
guessing costs a factor of 64. The second, and the one that decides the domain's outcome, is that the
reduction is not free to run for as long as it likes: the forger it builds has to finish inside the
same resource budget as the adversary, and that budget has to include the extraction work. Section 6
is about that second point, and it is where the design dies.

## 2. The schemes considered

| Scheme / parameter set | Numbers as stated | Category as stated | Where | Note |
|---|---|---|---|---|
| ML-DSA-87 (FIPS 204, pure mode, `ctx = b''`) | no sizes stated in this domain | "256-bit level" only implied; **no numeric advantage assigned** | `src/signature_security_reduction.py` | Sizes 4,627-byte signature and 2,592-byte public key appear elsewhere in the programme, in domain 07 |
| SLH-DSA-SHAKE-256s | `n = 32` bytes, `h = 64`, `d = 8`, `h′ = 8`, `a = 14`, `k = 22`, `log₂ w = 4`, `m = 47`; ≤ `2^64` messages per key; public key 64 bytes, signature 29,792 bytes | NIST category 5 "relative to a block-cipher comparison" | `src/slh_dsa_signature_reduction.py`, geometry repeated in `src/slh_tree_conditioning_audit.py` | citation "FIPS 205 Table 2 as given"; the values are the standard FIPS 205 values |
| SLH-DSA-SHAKE-128s | `n = 16`, `h = 63`, `d = 7`, `h′ = 9` | category 1 | `src/slh_tree_conditioning_audit.py` | comparison only, never proposed |
| SLH-DSA-SHAKE-128f | `n = 16`, `h = 66`, `d = 22`, `h′ = 3` | category 1 | `src/slh_tree_conditioning_audit.py` | comparison only |
| ECDSA-P384 / SHA-384 (secp384r1) | public key 97 bytes (uncompressed SEC1), signature 96 bytes (`r ‖ s`) | **no post-quantum hardness credited** | `src/slh_dsa_signature_reduction.py` | Shor-breakable |
| Hybrid `CEQS38-HYB-S256S` = SLH-DSA-SHAKE-256s **AND** ECDSA-P384 | sizes are the sum of the components (a typed pair) | reduces to the SLH component alone | `src/slh_dsa_signature_reduction.py` | the OR-hybrid is rejected |
| ML-KEM-1024 (FIPS 203) | — | key establishment; does not enter the composite bound | `src/slh_dsa_signature_reduction.py` | |
| SPHINCS+ | proof map only | — | `src/slh_dsa_signature_reduction.py` | the published decomposition is mapped, not proved |

Two features of that table matter. Every parameter set is used as **published**; the domain does not
propose a truncated or custom parameter set, and v1.39 says so explicitly. And the hybrid is a
*mandatory AND*: sub-128-bit post-quantum security is never granted to the traditional component. A
projection theorem for the AND hybrid is what makes the hybrid's security equal to the SLH
component's, and the OR construction is rejected because it gives up that equality.

## 3. Theory used

| Theory | Statement **as used here** | What it justifies | Full / partial | Citation as the source gives it |
|---|---|---|---|---|
| FIPS 204 | the pure-mode interface `ML-DSA-87.Verify(pk, M, σ, ctx = b'')` and the pure-versus-HashML split | the v1.37 endpoint's interface conformance | **partial** — interface only, no security claim imported | standard |
| FIPS 205 | Algorithms 22 and 24 (`slh_sign`, `slh_verify(M, SIG, ctx, PK)`), §11 parameters, Table 2 parameter sets, and the pure-mode string `C(ctx, M) = 0x00 ‖ byte(len ctx) ‖ ctx ‖ M` | the v1.38 endpoint and its context separation | **partial** — full interface and parameters, but **no numerical advantage** is taken from the standard | standard |
| FIPS 203 | the role of the KEM | excludes key establishment from the signature bound under key independence | **partial** | standard |
| Zalka, "Grover's quantum searching algorithm is optimal", arXiv quant-ph/9711070v2, Eq. (6), §3 | optimality before the first maximum for a uniformly random single marked element, turned into `min(1, (2Q+1)²/2^n)` via `\|sin kθ\| ≤ k\|sin θ\|` | the separate search envelope of v1.39 | **partial** — the optimality statement only | as given in the source |
| Hülsing–Kudinov, ePrint 2022/346 | a Winternitz-factor correction warning | quality check on the published decomposition | **partial** — abstract and metadata only; the source states the full text was not available | as given |
| Barbosa–Dupressoir–Hülsing–Meijers–Strub, ASIACRYPT 2024 (ePrint 2024/910) Theorems 1, 2, 4 | a published decomposition of the SPHINCS+ advantage into named terms | the "sourced partial-proof map" of eq. D, expanded into a 10-term ledger in `src/slh_tree_conditioning_audit.py` | **partial** — the decomposition, not the constants | cited with theorem numbers |
| Jackson–Miller–Wang, arXiv 2312.16619v2; Barbosa et al., ePrint 2023/246 | cited as limits on what can be imported into the ML-DSA setting | scope boundary only | **partial** | as given |
| Roetteler et al., arXiv 1706.06752 | Shor breaks ECC | why P-384 earns no post-quantum hardness | **partial** | as given |
| OpenTitan OTBN documentation and lowRISC RFC #26846 | an implementation route for the hash-based endpoint | feasibility context | **used as context only** — the source notes it is "not readiness of a particular board" | as given |

The reduction's own argument — the coupling of a hidden seat to a challenge key, and the improvement
from `64/ε` to a `64`-in-`h` hit rate using `h` fresh targets — is derived in the source, not
imported. The source states it as the standard multi-user-to-single-user guessing technique,
improved.

## 4. The argument, step by step

**Setup.** Inject the challenge (SLH or ML-DSA) public key at a uniformly random seat `J` among the
64, generate the other 63 keys locally, and simulate every ancillary primitive with independent
secrets. The reduction must be a single-slot honest wrapper: an honest seat stays single-slot across
restarts.

*Assumption.* The setup is simulatable and `J` is independent of the adversary's view. This is one of
the interface premises listed in §7; it is not proved.

**Step 1 — the hit rate.** Because `J` is independent of the virtual experiment,
`Pr[the target key is not corrupted] = E[|F|/64]`, where `F` is the set of uncorrupted seats
common to the two conflicting signer sets. The same reasoning applies after the hybrid projection
and adds no further multiplicative loss. There is no proof-side guess, witness-row guess, message
guess or extra corruption-survival factor.

*Assumption.* Corruption is adaptive, within `f ≤ 21`, and the adversary cannot tell which seat holds
the challenge key. If it could, `|F|` would not be independent of its view.

**Step 2 — the common seat is a double-signer.** For the two 43-seat signer sets `S0, S1`,

```
|(S0 ∩ S1) \ C|  ≥  2·43 − 64 − f  =  22 − f.
```

Outside the body-binding failure event `BadBind`, if both output approvals for a common uncorrupted
seat were queried, signed-string equality and body binding would show that the honest wrapper
approved two conflicting direct messages — contradicting persistent authorization. Hence `|F| ≥ 22 − f`
on the conflict event and outside `BadBind`. Therefore

```
Pr[E]  ≤  δ_B + α · ε_sig,
α = 64/(22 − f)   for adaptive corruption,
α = (64 − f)/(22 − f)   for a corrupt set of exact size f fixed and known before setup.
```

At `f = 21` these losses are 64 and 43 respectively. **Neither value comes from the SLH tree
dimensions** — a point worth stating because the tree's parameters invite exactly that confusion.

*Assumption.* Body binding with failure probability `δ_B`, and that the honest wrapper's approval
state is durable per configuration and domain. `δ_B` has no numerical value in this domain.

**Step 3 — composition.** If the extractor satisfies
`Pr[E] ≥ (p − κ_E)_+ / L_E` with `L_E ≥ 1`, then

```
p  ≤  κ_E + L_E (δ_B + α · ε_sig).
```

Body-binding failure stays inside `L_E` because it is measured in the extractor experiment; a
separately justified outer setup-distance term is added outside. The v1.38 source records that
placing `δ_B` outside is a real error, and test 15 checks the placement with the concrete
counterexample `3·(1e-5 + 64e-6)`.

**Step 4 — the hybrid projection.** For the mandatory-AND hybrid with independently generated keys,
`Adv_Hybrid(A) ≤ Adv_SLH(R_S)` with component-projection success loss **exactly 1**. The reduction
receives an SLH challenge public key, generates the traditional keypair locally, publishes the
composite key, forwards the SLH component of every composite signing query, supplies the traditional
component itself, and returns the SLH component of a fresh accepted composite forgery. Acceptance of
the composite implies acceptance of the SLH component, and global freshness implies the pair was
never queried. The time overhead of local ECDSA work is still counted.
*Assumption.* Dedicated component keys with no extra signing interface, so that the complete SLH
query log — including standalone calls, if the modeled environment has any — implies freshness.
The source notes that independent key generation permits revealing the ECDSA secret key in the
SLH-only experiment, which is the right behaviour for a quantum threat model in which P-384 does not
survive Shor.

**Step 5 — exact inversion, and what the numbers say.** v1.39 inverts the bound exactly. With
`F = Δ + κ_E + L_E δ_B`, `L = L_E` and `U = min(1, F + L α ε_SLH)`, the sufficient signature
condition for target `s ≥ 1` is

```
ε_SLH  ≤  R/(L α),   R = 2^−s − F,   when R > 0;
b_min  =  max(0, ⌈log₂(L α / R)⌉)   for an envelope ε_SLH ≤ 2^−b.
```

If `R = 0` no finite positive exponent suffices, and if `R < 0` even a zero signature term cannot
make the stated bound meet the target. The source is careful about what that means: "Neither case is
an attack or a proof that the actual scheme is insecure." With `F = 0` and `L = 2^ℓ` the formula
collapses to the memorable

```
b_min = s + ℓ + 6,
```

where the six bits come from the identity-selection factor 64 and have nothing to do with quantum
execution time. At `F = 2^−130` and target `s = 128` the arithmetic transitions are:

| Case | `U` | Sufficient? |
|---|---|---|
| `b = 134`, adaptive | `(5/4)·2^−128` | no |
| `b = 135`, adaptive | `(3/4)·2^−128` | yes |
| `b = 134`, known-static | `(59/64)·2^−128` | yes |

All 2,088 records the `--json` mode emits — 864 budget records and 1,224 search records, with
statuses 756 `CONDITIONAL_BUDGET`, 96 `STATED_ERROR_BOUND_EXCEEDS_TARGET` and 12
`ZERO_SIGNATURE_BOUND_REQUIRED` — carry the status `UNESTABLISHED`. The four-way budget allocation
gives each contribution a quarter and yields `b ≥ 136 + ℓ` for `s = 128`.

## 5. What the reduction does **not** say

The reduction never assigns `ε_sig`. v1.37 states it: "It does not assign ε_87 = 2^-128", and notes
that "If an external analysis supplied ε_87 ≤ 2^-b, this conversion alone would contribute at most
2^(6−b) in the f=21 adaptive case". The `b` of v1.39 is "a proposed theorem input, not a
measurement". A parameter-set label is not a bound: QPT names a class of adversaries, not a family of
classes called QPT-127 and QPT-129, and the labels 128, 192 and 256 in FIPS 205 specify parameter
families rather than supplying `ε_SLH = 2^-128, 2^-192, 2^-256` for a chosen adversary and resource
profile. v1.38's closure status is "The signature-assumption replacement is established
conditionally; a numerical QPT-128 success or work-factor claim is not."

The separate search envelope must not be confused with any of this. v1.39 gives
`min(1, (2Q+1)²/2^n)` with width `2w + s + 9` — 266 bits at `p ≤ 1/2` and 393 bits at
`p ≤ 2^-128` for `Q = 2^128` — and labels it `HYPOTHETICAL`, recording that "No reduction from all
SLH forgeries to this single-marked search game has been established." A probability exponent and a
query-work exponent are different quantities; three different assertions hide behind the string
"128", and v1.41 restates the rule: a 128-qubit register, a `2^−128` bound on a specified event, and
a `2^128`-operation lower bound are not interchangeable.

## 6. Why the reduction's running time is charged against the security target

This is the section that decides the outcome of the whole extraction line, so it is worth setting out
plainly.

**The accounting rule.** A security target that says "no adversary running in `G` gates wins with
probability more than `ρ`" must charge the *reduction* the same currency. If the forger built by the
reduction is allowed to run far longer than the adversary it was built from, the result proves
nothing about `G`-gate adversaries. Two accountings exist in the programme:

- **attack-cost accounting** charges only the adversary's own work;
- **rigorous accounting** in gate units charges the adversary *plus* every simulation, extraction
  and key-generation step the reduction performs.

The second is the one the target is stated in.

**The charge itself.** The extractor that produces the witnesses this reduction consumes is not free.
The DFMS online extractor for Fiat–Shamir commit-and-open proofs in the QROM runs in `O(q²)·poly`
time. Any reduction that uses an extracted witness to break a standard-model primitive `F` therefore
runs in time roughly `t_B ≈ G + a·q²·g_sim`, where `G` is the adversary's budget and `g_sim` is the
per-step simulation cost. Substituting that into a generic attack bound of the form
`c·(t/g_F)^e/2^n` gives a required hash output length of roughly

```
n  ≥  (2e − 1)·128 + 130 + log₂ c + e·log₂(a·g_sim) − 2e·log₂ g_H − e·log₂ g_F.
```

The consequences in gate units are stated in the v1.43 material (domain 06): a preimage/search row
(`e = 2`) passes with `n = 512`; a collision row (`e = 3`) needs `n = 1024`; **a 256-bit signature
inside the proof fails**. A signature sent in the clear needs no extraction and its reduction is
linear — which is exactly why the public-signer profile survives and the design that hides the
signature inside an extractable proof does not.

**Applied to this domain's reductions.** The v1.37 and v1.38 conversions are correct: the algebra
`p ≤ κ_E + L_E(δ_B + 64·ε_sig)` holds, and the selector argument is sound. But `ε_sig` must be
evaluated *at the reduction's running time*, and that time includes the `O(q²)` extractor. With a
category-5 signature, whose secret is at the 256-bit level, the signature row at `2^128` gates is
`+55` in gate units and `+161` in query units, measured in `log₂(Pr/G)`; the resulting ledger fails
the target by **185 bits in gate units**. Under attack-cost accounting, which ignores reduction time,
the design would pass just as the public-signer design does — and the v1.43 record says outright that
this "is not a proof".

**What replaced it.** The v1.43 decision is "replaced, not patched": the signature-inside-proof
designs — SLH-DSA inside the closing theorem's proof, and ML-DSA-87 in R29 — are withdrawn, and two
designs take over. Domain 06 holds that material and the ledger that records the margins
(+29.4 bits in gate units for the hidden-signer Mode S construction, and the `−185.0` row for compat
mode). This domain's contribution to the decision is the reduction itself and the honest statement of
its cost: the conversions are kept and reused, the *placement* of the signature is what failed.

The v1.37 random-seat selector argument is reused **without an extractor** for the public-signer
profile, where no witness has to be extracted and the reduction is therefore linear. That reuse is
the clearest evidence that the failure was about charging time, not about the algebra.

## 7. Tests

| Script | Groups | What the groups assert |
|---|---|---|
| `src/signature_security_reduction.py --self-test` | 23, all OK | worst-case single honest common seat (seat 21, side 1); adaptive hit rate `1/64` and a safety loss of 64; the known-static rate `1/43`; all `f = 0…21` with fresh seats `{f…21}` and losses `64/(22−f)`, `(64−f)/(22−f)`; the selector picks either side; a new signature on a queried message is not a forgery; a raw same-key query disqualifies; context is part of freshness; a corrupted-through-end seat is excluded and `f = 22` is rejected; signature and projection tampering; slot and conflict checks; domain separation by signed bytes; a forced constant body digest blocks freshness (negative control); exact approval bytes and one digest per body; `δ_B` placed inside `L_E`; parameter validation and clipping to 1; exhaustive small quorum intersections `(5,4,1)`, `(6,4,1)`, `(7,5,2)`; the expected fresh fraction without independence; embedding forwards only target queries with 63 local keygens; target corruption aborts; duplicate-key setup aborts without resampling; query and registry canonicality; a discarded-branch query cannot be erased |
| `src/slh_dsa_signature_reduction.py --self-test` | 36, all OK | groups 01–23 as v1.37 with the CEQS38 constants, plus: native API order without double framing; pure-context encoding injective on a 4×4 domain with `C(b'', b'm') = 00 00 6d` and contexts longer than 255 rejected; the AND truth table; the OR negative control; a fresh projection returns the same SLH signature object; a component-only query disqualifies while another context's query does not; a valid P-384 component cannot bypass an invalid SLH component; component encodings and a 256-byte context rejected; the legacy `CEQS29-M87-K1024` and mixed suites rejected; the hybrid suite uses new messages; an always-true ECDSA callback cannot rescue a bad SLH component; canonical query tuples and exact booleans |
| `src/signature_margin_sweep.py --self-test` | 13, all OK | `b_min = s + ℓ + 6` for `s = 1…256`, `ℓ ∈ {0,1,6,20}`; minimality for non-dyadic `α ∈ {43, 64, 64/22}` with `L ∈ {1,3,64}` and `F = 2^−s/3`; `F = 2^−130` gives `ZERO_SIGNATURE_BOUND_REQUIRED` at `s = 130` and `EXCEEDS` at `s = 131`; no false floating-point pass (the exponent stays 129); the `F`-floor boundary at 135 versus 134 (static); the four-term allocation sums exactly to `2^−s`; monotonicity; the search width is exactly `2w + s + 9`; the integer query bound is tight; amplitude ratios 1/2 per bit and 1/3 with `F`; loss versus overhead bits (`+1` versus `+2`); limits, units and type checks; every record `UNESTABLISHED`, with 1,224 search records and 864 + 1,224 total |

The suite counts are recorded in v1.43's reading log as "20 + 16 + 27 + 23 + 36 + 13 + 12 + v1.41 +
v1.42, all OK", and all nine were re-run for this build; see `VERIFICATION.md`.

## 8. Sizes and cost

| Quantity | Value |
|---|---|
| Source files | v1.37 42,636 bytes / 893 lines; v1.38 49,757 bytes / 1,046 lines; v1.39 27,245 bytes / 568 lines |
| Recorded suite runtimes | 0.132 s (23 tests), 0.136 s (36 tests), 0.083 s (13 tests) |
| Machine-readable sweep output | 811,628 bytes, 2,088 records — reproduced byte-identically here |
| Reduction resources | 63 local keygens; at most 86 verifications |
| Projection loss | exactly 1 |
| Quorum loss | `α = 64/(22 − f)` adaptive, `(64 − f)/(22 − f)` known-static |
| Composition | `p ≤ κ_E + L_E(δ_B + α·ε_sig)` |

## 9. Packages and tools used

Python standard library only, across the three scripts: `dataclasses`, `fractions`, `hashlib`,
`itertools`, `json`, `math.isqrt`, `argparse`, `unittest`, `sys`. `fractions.Fraction` carries every
probability comparison exactly; `math.isqrt` is used for exact integer square roots in the threshold
arithmetic rather than floating-point logarithms. The ML-DSA and SLH-DSA endpoints are modelled
symbolically with length-enforcing adapters (`SLH_PK_BYTES = 64`, `SLH_SIG_BYTES = 29792`,
`ECDSA_PK_BYTES = 97`, `ECDSA_SIG_BYTES = 96`); **no real signature is produced or verified by these
scripts**, and no implementation of either standard is called. That is a limitation, not a
convenience: it means the tests check the reduction's bookkeeping and interface framing, not the
schemes.

## 10. Validation status

- **Proven.** The selector probability identity; the common-seat counting; the composition and the
  placement of `δ_B`; the AND-hybrid projection with loss 1; the concrete rejection of the OR
  construction; and, in v1.39, the exact thresholds of the v1.38 bound — conditional thresholds, not
  statements about SLH-DSA hardness.
- **Assumed.** An oracle-respecting, authorization-consistent extractor that the reduction consumes;
  a complete monotone query log across all branches; simulatable setup; the honest single-slot
  wrapper; and the values `ε_87`, `ε_SLH`, `δ_B` and `Δ_setup`, none of which is assigned.
- **Measured.** The finite symbolic test groups. v1.37's own header is explicit that these are "not a
  proof-assistant formalization".
- **Missing.** Any numerical ML-DSA-87 or SLH-DSA quantum bound for the final FIPS parameters; the
  ten published advantage bounds of the SPHINCS+ decomposition in a stated quantum model, with the
  Winternitz-factor correction counted exactly once (see
  [`conditioning-arguments.md`](conditioning-arguments.md)); the upstream extractor; a value for
  `δ_B`; and the hash-to-ideal-oracle bridge that would connect a deployed SHAKE256 to the model.

## 11. Open items

1. `ε_sig` is never assigned, so the bound is never instantiated. This is the domain's central open
   item and it does not close here.
2. The extractor the reduction consumes exists only as a premise. The circuit backend of
   [`circuit-witness-extractor.md`](circuit-witness-extractor.md) is a different relation.
3. The interface premises (single-slot honesty, complete monotone query log, simulatable setup) are
   assumptions. One implementation-level violation of the single-slot premise is on record elsewhere
   in the programme as a failed assumption.
4. The extraction-time charge of §6 is stated in the v1.43 material for the design as a whole. This
   domain records the reductions that the charge applies to; it does not recompute the ledger, which
   belongs to domain 06.
5. Real signature implementations were not exercised; only symbolic adapters with enforced lengths.
