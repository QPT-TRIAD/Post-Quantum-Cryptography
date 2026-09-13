# GAME 1 — FRAME

*Definition in the harness:* `GAME_FRAME` in `src/ceqs_games.py`; measured by `game_frame()`.
*Recorded write-up:* `results/attack-lab-results.md` §12.1.

---

## 1. The game

```
FRAME(F, registry, d, i*, cert)

Attacker receives     the public parameters (the key map F, the field, the challenge
                      derivation); the registry — all 64 public keys Y[d][i]; a
                      certificate and all 43 published handles in it; the target seat
                      i*; the target seat's handle Z; the domain d and both messages.
Does not receive      any seat's opening (s, r); the prover's randomness.

Oracle                evaluations of the public key map F, counted as Q.

Wins if               it outputs (s', r') with F(s' ‖ r') = Y[d][i*] — a preimage of an
                      honest seat's registry key. Holding that opening, it can place a
                      handle for i* in a second certificate for a different message, so
                      that public extraction names i* as a double-signer.
```

The winning condition is stated as a preimage, then *closed* by the harness: `_frame_endgame()`
takes such an opening and drives the attack to the end, publishing an honest certificate for
`honest_msg` alongside a forged one for `forged_msg` that carries the victim's handle, and calling
`extract`. The game is only interesting if the second step really works, and §4 shows it does.

## 2. The property claimed

**Non-frameability of honest seats**: an adversary that does not hold a seat's opening cannot make
the public extraction procedure name that seat. Equivalently, a seat named by extraction really did
authorise both conflicting messages — up to the handle-coincidence effect measured in
`game-safety.md` §4.

The property is owned by domain 08: the reduction is Theorem 1 of
`domains/08-hidden-signers/docs/mode-b-security.md`, conditional on assumption A-F1 (that the key
map `F` is one-way on the seats' openings in the relevant regime). This domain does not restate or
re-prove it.

## 3. Status of the argument

| part | status | where |
|---|---|---|
| the security claim (no framing within the A-F1 regime) | **reduction**, conditional on A-F1 | domain 08, Theorem 1 |
| A-F1 (one-wayness of `F` on openings) | **assumption**, with a model-based estimate | domain 08 |
| the search cost on the **real** function, at toy sizes | **measurement** (this domain, 5 sizes × 6 targets) | §5 below |
| the marked set `M` on the **real** function | **measurement** (full enumeration, 60 instances) | §5 below |
| reachability of the winning condition | **demonstration** (end-to-end, §4) | §4 below |
| the cost at production parameters | **not claimed here** — a fit extrapolated from 8–17 bits, with the error measured | `results/attack-lab-results.md` §12.6 |

Nothing in this document is a proof. The concrete claim it supports is: *on the deployed key map at
the sizes that could be enumerated, the framing attack costs what the reduction assumes, and the
marked set is as small as the theory says*.

## 4. The attack, step by step, and the assumption each step needs

1. **Derive `s` from a guessed `r`.** The published handle is `Z = r⁷ ⊕ c_a·s ⊕ c_b·s² ⊕ c_c·s⁴`.
   For a guessed `r`, everything except a linearized polynomial in `s` is known, and `L_c` is
   invertible over GF(2^n), so the attacker computes a unique `s`. *Needs:* the handle to be a
   public, invertible-in-`s` function — true by construction, and the reason the search is `2^n` and
   not `2^(2n)`.
2. **Test the guess.** Evaluate `F(s ‖ r)` and compare with `Y[d][i*]`. *Needs:* `F` to be public
   and efficiently evaluable — true; it is the registry key map, expanded from a public seed.
3. **Enumerate.** Repeat over the `2^n` candidate `r`. *Needs:* nothing beyond steps 1–2. The cost
   is exactly the number of `F`-evaluations, which is what `Q` counts.
4. **Win.** Having found `(s', r')`, place the seat's handle in a conflicting certificate and
   publish it. *Needs:* the extractor to name the seat — verified end to end, below, rather than
   assumed.

**The endgame, run for real.** `_frame_endgame()` at `n = 14`, expansion 8: the victim authorises
`honest_msg`; the attacker, holding the recovered opening, manufactures the victim's handle for
`forged_msg` and publishes a conflicting certificate containing it plus 42 other seats' handles;
`m50.extract` then **names the victim**. Reported in the run as
`victim seat 0 named by extraction: True`.

**What the endgame does and does not do.** It demonstrates that *possession of the opening* wins the
game — the winning condition is reachable and the extraction path names the victim. It does **not**
chain the search of step 3 into step 4: `_frame_endgame` starts from the instance's true opening
(the same value the search returns, since the marked set is 1 — see below). The two halves are
measured separately at the same parameters. A reader who wants one continuous attack must connect
them; nothing in the construction makes that step hard, but the harness does not perform it, and it
is recorded as an open item in `validation-status.md`.

## 5. Measured results

**Query complexity** (expansion 8, 6 targets per size, target seat = the enumeration index):

| `n` | 8 | 10 | 11 | 13 | 14 |
|---|---:|---:|---:|---:|---:|
| measured mean `Q` | 144.7 | 664.8 | 1,153.3 | 4,942.5 | 10,414.0 |
| theory `2^(n−1)` | 128 | 512 | 1,024 | 4,096 | 8,192 |
| `log₂ Q` | 7.18 | 9.38 | 10.17 | 12.27 | 13.35 |

**Fit:** `log₂ Q = 1.0178·n − 0.931` against a theory of `1.0·n − 1.0`.

The per-target `Q` is the rank of the true `r` in the enumeration, uniform on `[1, 2^n]`, so its
mean estimates `2^(n−1) + 1/2` with a standard error of about `2^n/√(12·6) ≈ 0.12·2^n` — at `n = 8`
that is ±15 on a mean of 144.7, and the measured 144.7 is inside it. **Six samples is not enough to
pin a constant to better than a fifth of a bit**, which is why the test asserts a band on the slope
and not a value for the mean.

**The marked set `M`.** Full enumeration of the real key map for both handle kinds — the superseded
`r⁷` handle and the deployed linearized handle — over 6 targets at each of `n = 8, 10, 11, 13, 14`
(`src/ceqs_attack_lab.py`, Experiment B): **`M = 1` in all 60 target-instances**, both kinds. No
candidate other than the true opening satisfies the registry key and the published handle, so there
is no shortcut below exhaustive search at these sizes. This is the fact the ledger's framing row
depends on, and it is measured on the real function, not on a model of it.

**The two handle kinds cost the same to frame.** Identical `M` for both. That is the harness's own
evidence for the claim the record makes from the unshipped SAT experiments (see the README §5, and
`docs/validation-status.md` §6).

**The control at `n = 8`** — what publishing a handle costs the defender (Experiment B §3.1):

| setting | search space | `M` |
|---|---:|---:|
| no handle published | `2^(2n) = 2^16` | 1 |
| handle published | `2^n = 2^8` | 1 |

The handle moves the framing search from `2^256` to `2^128` at production width. That is the whole
reason the ledger's framing row is `2^128` and not `2^256`, and it is a property of the
construction's design, not a defect found later.

## 6. The quantum side

`GAME_FRAME`'s `theory_quantum` states `(π/4)·2^(n/2)` Grover iterations by `M = 1`, i.e. slope 0.5.
It is **not** measured by this harness. It is measured by `src/ceqs_attack_lab.py` Experiment C —
exact state-vector simulation on the real oracle — which reported `max |sim − theory| ≤ 5.3 × 10⁻¹⁵`
and a fitted slope of **0.512** over `n = 8, 10, 11, 13`; see `docs/attack-lab.md` §4 for that
measurement and its limits (it counts oracle invocations and charges no gates).

Extrapolated: `n = 256, M = 1` → `(π/4)·2^128 ≈ 2^128` iterations, the ledger's framing row.

## 7. Tests

`test_frame_is_winnable_and_scales` asserts two things: that the endgame names the victim, and that
the fitted classical slope lies in `[0.85, 1.15]`. It **does not** assert the fitted value, the
intercept, or any individual mean — a test that pinned `1.0178` would fail on a legitimate reseed
and would stop being evidence. Observed: pass, in `--self-test` (4 tests OK, 2.956 s in-run).

## 8. Cost and size

`game_frame()` runs 5 sizes × 6 targets, each target enumerating up to `2^n` `F`-evaluations, plus
the endgame's encode/extract. It is the cheapest of the four games; in `--all` (whole suite 148.19 s
wall) FRAME is a small fraction. To run it alone:

```
cd domains/09-security-games-and-attack-lab/src
python3 ceqs_games.py --frame            # 13.5 s measured here, exit 0
python3 ceqs_games.py --frame --json     # the same report the JSON file carries
```

## 9. What would falsify this, and open items

- **A marked set larger than 1.** If enumeration of the real key map at any size produced `M > 1`,
  the reduction's "the adversary must find the true opening" step would be wrong and framing would be
  cheaper than `2^n`. Checked at 60 instances; not checked above `n = 14` (full enumeration past
  `2^14` is not affordable here).
- **A slope materially below 1.** Would mean a structural shortcut exists. The measured `1.0178` is
  above 1; with 5 points and no error bars, the interval around it is not computed (see
  `games-methodology.md` §6).
- **A real cryptanalytic attack on `F`** (XL, hybrid, algebraic elimination) that beats generic
  search would break the premise of the whole game, at every size. **Not attempted here** — that
  surface belongs to domain 08, and its XL-model estimates live there.
- **The endgame's missing link** (§4): the search's output is not fed into the extraction call. The
  two halves are demonstrated at the same parameters but not chained.
- **Quantum rows are not re-measured here.** Experiment C measures the iteration law; the games do
  not, and gate costs are charged elsewhere (`docs/games-methodology.md` §5.2).
