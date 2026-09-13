# The toy-field prover (v1.48): what it establishes and what it does not

`../src/mode_b_voleith_toy.py` is the only artefact in this domain that runs the **whole Mode B
pipeline end to end with a real proof in the proof slot** — registry, two conflicting frames,
verification, and public pair-search extraction — rather than evaluating a size formula. It does so
at toy width, in Python.

Run it with `--self-test` (7 tests) and `--run` (the measured size plus the extraction).

---

## 1. The toy parameters

| Parameter | Value | Production (for contrast) |
|---|---|---|
| field for s, r, handle | GF(2^16) — r⁷ is a permutation because gcd(7, 2^16 − 1) = 1 | GF(2^256) |
| key map | F: F₂^32 → F₂^48 | F: F₂^512 → F₂^812 |
| seats / quorum | 64 / 43 | 64 / 43 |
| repetitions | τ = 8, each over 2^8 parties | τ = 11 at b = 20 |
| MAC field | GF(2^64) (= τ · 8 bits) | GF(2^256) |
| committed bits | ℓ = 4,128, ℓ̂ = 4,320 | ℓ = 13,760, ℓ̂ = 15,296 |
| QuickSilver check | degree 3 (key map 2, handle 3) | degree 6 |

The source states its own security level plainly: **soundness about 2^−64 and "128-bit-free
everything"; the point is structural fidelity and a measured proof size, not security.** The toy is
not a scaled-down secure instance; it is a structurally faithful instance wide enough to run.

## 2. What it establishes

1. **Structural fidelity.** The proof system is implemented the way FAEST v2 is built — GGM seed
   trees, all-but-one vector commitments, VOLE from vector commitments with correction values, the
   VOLE consistency hash, a QuickSilver check with zero-knowledge masks, a multi-round Fiat–Shamir
   transform — over the *exact* Relation R_B, not over a stand-in.
2. **The pipeline closes.** The seven self-tests cover: GGM open/reconstruct; the r⁷ table matching
   the field; a false witness refused by the prover; a tampered proof rejected; a wrong statement
   rejected; the measured size matching the formula; and the end-to-end pipeline. `--run` verifies
   both frames, rejects a tampered proof, and extracts the 22 common seats.
3. **The size accounting is checked against code.** Measured proof size **6,696 B** against the
   FAEST v2 formula at the same (τ, ℓ, T_open, λ) with **256-bit nodes in one block: 6,924 B** — a
   3.4 % gap, i.e. the formula used for the v1.46/v1.47 sizes is not an underestimate hiding in the
   arithmetic. The λ-bit-node variant of the formula gives 5,260 B and is *below* the measurement,
   which is itself the useful signal about which formula shape the implementation matches.

## 3. What it does not establish

- **Not a production result.** No number here is a claim about a 32 KiB certificate. The 6,696 B
  figure is the toy instance's proof (frame 6,990 B at toy width); the 30,810 B production figure is
  a *ledger and formula* number, not something this file measured.
- **No security.** No soundness, no zero-knowledge and no extraction claim survives the toy width.
  The tests show the machinery behaves; they do not show an adversary cannot break it.
- **No collaborative prover.** The toy prover is a single process holding the whole witness. It says
  nothing about [the collaborative-prover problem](collaborative-prover.md).
- **The selector gap applies here too.** The relation's selector constraint is the single
  `Σ bᵢ + 1 = 0` over F₂, which fixes parity, not weight = 1. It was at *this* toy width that a
  weight-3 selector was built and accepted (see [validation-status.md](validation-status.md) item 6):
  the toy backend reports `qualified = False`, so that probe is a gap in the stated relation R_B, not
  a forgery against an honest verifier.

**Label for everything in this file: measurement / simulation.** Where a number agrees with a
formula, the agreement is a measurement of the implementation, not a proof of the formula's
soundness.
