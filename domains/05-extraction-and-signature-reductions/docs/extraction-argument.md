# The public extraction argument

Source: `src/ceqs29_extractor.py` (v1.34). Script: `python3 src/ceqs29_extractor.py --self-test`,
`--certificate`, or `--body0 A --body1 B --configuration HEX128`. All paths are relative to the
repository root; the version label is the one in the file's own header.

## 1. The problem, and why it is hard

Two accepted quorum certificates on conflicting messages must yield a *publicly computable* set of
seat identities — the seats that authorized both — of size at least `2q − n = 22`. "Publicly
computable" is the hard part. The natural way to make a certificate compact is to stop carrying the
per-seat evidence, and the natural way to keep it attributable is to carry a sidecar of individual
signatures. Both were tried in this programme; the first is the goal, the second is what domain 01
calls Target A. The failure mode that has to be avoided is a decoder that *appears* to work: a
procedure that turns 43 anonymous handles into 22 numbers is worthless if it also works on handles
that no validator ever produced.

An earlier version (v1.29) had an `extract_algebra` routine. It checks neither that the recovered
seats are distinct nor that there are at least 22 of them (recorded in the v1.43 material, which is
in domain 06). v1.34 replaces it with a decoder that does both, states its premises, and ships a
negative control proving that algebraic recovery alone is not authorization.

## 2. The relation and the encoding

Definitions, all from the v1.34 header:

- **Committee.** 64 seats, quorum `q = 43`, at most `f = 21` faulty. Seat `i ∈ {0,…,63}` is encoded
  by the polynomial-bit integer `κ = i + 1`.
- **Field.** `F = GF(2)[X]/(f)` with `f(X) = X^512 + X^8 + X^5 + X^2 + 1`, encoded as
  `(1 << 512) | 0x125`. Field elements are 64-byte big-endian integers encoding polynomial
  coefficients over GF(2). This is *not* arithmetic modulo an integer prime. The 512-bit dimension
  is inherited from the input construction; v1.34 states plainly that it "is not a claim of a
  512-bit, 128-bit, or other cryptographic security level".
- **Body.** 208-byte header plus exactly 43 handles of 128 bytes each: 16 bytes of suite identifier
  `CEQS29-M87-K1024`, 64 bytes configuration `C`, 64 bytes domain `d`, 64 bytes direct message `m`,
  then the handles. Total 5,712 bytes. The handles are strictly sorted by `L` with no duplicates.
- **Handle.** For a seat `i`, trace seed `t_i`, configuration `C` and domain `d`,

  ```
  L_i ‖ R_i = SHAKE256_128bytes(b'CEQS29/pair' ‖ t_i ‖ H(b'CEQS29/domain', C, d))
  Z_i       = R_i XOR (m · κ),      κ = i + 1
  ```

  The link/mask pair is independent of the message `m`. `H` length-prefixes every argument with
  eight big-endian bytes and emits 64 SHAKE256 bytes; the decoder itself never calls `H` or SHAKE.
- **The intended private relation `R29(B, w)`.** The witness `w` has, for all 43 handles, a row
  `(i, t_i, σ_i)`. Verification checks distinct seats, opens each registered trace credential,
  recomputes each handle at that *same* seat, and verifies that seat's ML-DSA approval on the
  canonical body, index and own handle. The ordinary `check_witness` routine of the v1.29
  authorization code consumes those rows; it is not an algorithm that extracts them from a proof.

The distinction the whole domain turns on is stated in the v1.34 header: the public decoder returns
**identities and positional evidence**; a joint extractor must obtain **two complete private
witnesses** for the exact adversarially output bodies, including approval signatures and trace
openings, together with the authorization experiment transcript.

## 3. Theory used

| Theory | Statement **as used here** | What it justifies | Full / partial | Citation as the source gives it |
|---|---|---|---|---|
| Rabin irreducibility test | For `f` of degree 512 over GF(2): `X^(2^512) ≡ X (mod f)` and `gcd(f, (X^(2^256) mod f) XOR X) = 1` together imply `f` is irreducible | that `F` is a field, so the decoder's division-free step is legitimate | **full** — the complete criterion at degree 512 | Greenhill, "Theoretical and experimental comparison of efficiency of finite field extensions", §2 Lemma 1, with a URL. The citation is **incomplete in the source**: no venue, no year, no DOI. This repository does not supply what is missing, and does not rest the argument on the citation — the two conditions are recomputed exactly by `--certificate` |
| Elementary GF(2) linear algebra | `T[δ·κ] = κ − 1` for `κ ∈ {1,…,64}` is a well-defined table whenever `δ ≠ 0`, because a field has no zero divisors | the decoder recovers the seat without ever computing an inverse | **full** | elementary; no external source |
| DFMS commit-and-open QROM extraction (arXiv 2202.13730) | cited in v1.34 only to delimit what this decoder is **not** | the scope boundary: an ideal-oracle extraction database is a reduction's internal object, not a certificate input | **partial** — scope only; no lemma of the paper is used in v1.34 | as given in the source: arXiv 2202.13730, Definition 3.5, §§4–5 |

The DFMS import is worth stating precisely because it is the domain's most easily misread step.
v1.34 says the opposite of a claim: the paper's extractors require an actual protocol with a
special-soundness extractor, and the ordinary R29 checker is not that protocol. The assessment is
described in the source as "an inference from that theorem's scope and the inspected local code,
not a claim by [the paper]".

## 4. The argument, step by step

**Claim 1 — the retained polynomial defines a field.**
*Steps.* Compute `X^(2^512) mod f` by 512 successive modular squarings (not by expanding an integer
exponent) and `gcd(f, (X^(2^256) mod f) XOR X)`. The first condition says `f` divides `X^(2^512) − X`,
whose derivative is 1; hence `f` is squarefree with irreducible factors whose degrees divide 512.
Every proper divisor of 512 divides 256, so a proper-degree irreducible factor would also divide
`X^(2^256) − X`, contradicting the second condition. Since `deg f = 512`, `f` is a single
irreducible factor of degree 512.
*Assumptions.* None beyond the arithmetic. This is a theorem with proof, and the two conditions are
recomputed independently by the program; `--certificate` additionally emits polynomials `u, v` with
the unreduced identity `u·f XOR v·((X^(2^256) mod f) XOR X) = 1`, checked by the caller and by the
tests. A reducible polynomial `X^512 + 1` is used as a negative control (test 02).

**Claim 2 — division-free identity recovery.**
*Steps.* For two bodies with `m0 ≠ m1`, put `δ = m0 XOR m1 ≠ 0` and build the 64-entry table
`T[δ·κ] = κ − 1`. The keys are distinct and nonzero: `δ·κ = δ·κ′` implies `δ·(κ XOR κ′) = 0`, and a
field has no zero divisors, so `κ = κ′`. For a common, correctly formed handle,
`Z0 XOR Z1 = (R XOR m0·κ) XOR (R XOR m1·κ) = δ·κ`. Therefore `T[Z0 XOR Z1]` is exactly the original
seat. This is equivalent to dividing by `δ` without computing `δ^-1`. The implementation builds the
table from `basis[j] = X^j·δ` for `j = 0,…,6` using six multiply-by-X steps, then
`product[κ] = product[κ XOR lowbit] XOR basis[log2 lowbit]`, which is exactly 64 field XORs and no
general multiplication, no inversion, no random-oracle query and no secret-dependent input.
*Assumptions.* Only that both handles exist at the same seat with the same trace seed and the same
configuration and domain. If any of those fail, the recovered value is not guaranteed to be a seat,
which is why the caller applies the range and duplicate checks below.

**Claim 3 — complete public decoding under stated premises.**
*Steps.* Merge the two strictly sorted 43-entry link lists in at most 85 iterations with at most two
ordered comparisons per iteration. A matching link belongs to the same seat by link uniqueness; a
common seat necessarily has the same link and mask by opening consistency; Claim 2 then gives
exactly that seat. Sorting the findings by seat yields a canonical list equal to `S0 ∩ S1` with
`22 = 43 + 43 − 64 ≤ |S0 ∩ S1| ≤ 43`. Under the premises no matched link produces a zero or
out-of-range identity or a duplicate seat, so none of the defensive rejections fires; conversely
every listed seat belongs to both witness sets.
*Assumptions.* This is the claim whose premises carry all the weight, and v1.34 says so: both bodies
satisfy `R29` for an *authenticated common* configuration and domain; the messages differ; the
witnesses name sets of exactly 43 *distinct registered* seats each; trace openings are consistent for
each seat across both witnesses; and different registered seats have different links within this
context. The source labels these "binding/link premises, not conclusions from a parsing test or from
field irreducibility". Nothing in the decoder proves them.

**The status label, and why it matters.**
The command prints candidate identities and complete positional evidence, and its status remains
`ALGEBRAIC_CANDIDATES_ONLY`: it does not verify a complete quorum certificate. The negative control
(test 19) manufactures a pair of public handle lists that name a chosen 22-seat intersection with no
registered trace opening and no approval signature, and the decoder returns those 22 candidates, as
it should. Algebraic acceptance is therefore insufficient evidence of authorization. The test is not
a forgery of an accepted full R29 certificate either — no full R29 verifier is available or invoked.
The source adds the sharper point: even language soundness alone would not prove knowledge of a
signature, because a valid signature exists for each signing message whether or not an adversary
knows one.

## 5. Tests

`python3 src/ceqs29_extractor.py --self-test` runs 20 test groups and exits 0 with unittest `OK`.

| Group | What it asserts |
|---|---|
| 01 | field certificate and the pinned residue `X^(2^256) mod f = 0x53dc5bb4…04da4a` |
| 02 | `X^512 + 1` is rejected (reducibility control) |
| 03 | all 512 field basis differences × all 64 encoded seats: 32,768 table comparisons |
| 04 | extended-gcd inverse cross-check for `1`, `2^511`, the mask, and 32 random deltas (seed 3401) |
| 05 | all overlap cardinalities 22…43 with shuffled seats (seed 3402) |
| 06 | boundary seats `{0…41, 63}` |
| 07 | input-swap symmetry: recovered seats preserved, evidence positions swapped |
| 08 | replay of the retained v1.29 public bodies recovers exactly seats 0…21 |
| 09 | exact framing and types |
| 10 | suite, configuration and domain mismatch are rejected |
| 11 | equal messages |
| 12 | unsorted and duplicate links |
| 13 | zero and out-of-range identity (`κ = 65`) |
| 14 | duplicate recovered seat |
| 15 | fewer than 22 matches |
| 16 | evidence completeness and canonical order |
| 17 | nine evidence mutations rejected |
| 18 | non-canonical table inputs |
| 19 | manufactured handles: count 22, status `ALGEBRAIC_CANDIDATES_ONLY`, `authorization_verified` false |
| 20 | CLI: exit 0 with count 22 on a good pair, exit 2 with empty stdout on a bad one |

Group 20 invokes the file as a subprocess inside a `tempfile.TemporaryDirectory()`, so it exercises
the real command-line path rather than the in-process one. It writes only into that temporary
directory.

## 6. Sizes and cost

| Quantity | Value |
|---|---|
| Body | 208-byte header + 43 × 128 bytes = 5,712 bytes |
| Field certificate output | 798 bytes of JSON (`results/ceqs29_extractor.certificate.json`, reproduced byte-identically) |
| Table construction | 6 multiply-by-X steps + 64 field XORs |
| Merge | at most 85 iterations, at most 2 ordered comparisons each |
| Source file | 56,649 bytes, 892 lines |
| Recorded runtime | 0.718 s for the 20-group suite; 0.138 s for `--certificate` (lock wait included) |
| Re-run here | 1.141 s for the suite, 0.14 s class for the certificate; see `VERIFICATION.md` |

## 7. Packages and tools used

Nothing beyond the Python standard library, and nothing beyond the interpreter is needed to trust
the output: `dataclasses`, `argparse`, `json`, `pathlib`, `hashlib`, `random`, `subprocess`, `sys`,
`tempfile`, `unittest`. There is no third-party dependency, no `galois`, no solver, no prover.

Two of these deserve a note.

- `hashlib.shake_256` (OpenSSL 3.0.13 backend in the recorded environment) is used for the retained
  fixture and for the `H` of the handle construction. It is used as a concrete function and never as
  an ideal-oracle proof: a fixed hash is not a random oracle, and the field argument does not depend
  on it.
- `random` is used only to generate test deltas and seat shuffles, with fixed seeds (3401, 3402) so
  the tests are deterministic.

## 8. Validation status

- **Proven.** Claim 1 (field irreducibility, with an exact certificate recomputed by the program).
  Claims 2 and 3 are theorems-with-proof conditional on the stated premises — the premises are
  binding and link *properties of the deployment*, not of the decoder.
- **Measured.** Replay of the retained v1.29 public bodies; the 32,768-entry table check; the exact
  certificate output. These are measurements of exact computations, not of a deployed system.
- **Assumed.** Trace-opening consistency and link uniqueness across the two witnesses; that the
  configuration argument the caller supplies is the authenticated one. The program explicitly does
  not learn it from an untrusted body, and the self-tests use synthetic values that "do not
  establish configuration trust".
- **Missing.** The full R29 proof protocol and the joint knowledge extractor (see
  [`joint-extractor-lift.md`](joint-extractor-lift.md) and
  [`circuit-witness-extractor.md`](circuit-witness-extractor.md)). The implementation is described
  by its own source as "a public reference implementation, not a constant-time or formally verified
  production library".

## 9. Open items

1. No prover/verifier exists for the full R29 relation, so the decoder's premises cannot be
   discharged by running the protocol.
2. The decoder returns identities, not witnesses; the two output types are not interchangeable and
   the source says running the public decoder twice is not an implementation of the extractor
   contract.
3. The measured fixture covers seats 0…21 only. Larger intersections are covered combinatorially by
   tests, not by replay of real material.
4. The decoder is not constant-time and has not been formally verified.
