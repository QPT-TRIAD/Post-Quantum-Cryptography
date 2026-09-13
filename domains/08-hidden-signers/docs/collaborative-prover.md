# The collaborative-prover problem

**This is the essential gap of the domain.** Everything else in Mode B is a design with a size
estimate and an executed ledger; this is the part for which no construction exists at all.

---

## 1. The requirement, stated as a problem

Let the registry be as in the [construction](construction.md): seat i holds a one-time opening
(s_i, r_i) per (epoch, domain), registered as Y[d][i] = F(s_i‖r_i), and its approval of a message m is
the handle Z_i = r_i⁷ ⊕ c(m)·s_i.

**Problem (collaborative proving).** Produce, for a set S of 43 seats, a certificate whose proof slot
is accepted by the public verifier of Π_B, such that:

1. **No party learns an honest seat's opening.** Formally: there is no efficient coalition of at most
   21 of the 64 seats (plus the network) that can compute (s_i, r_i) for an honest i; and the proof's
   producer can be distributed so that no single machine holds all 43 openings.
2. **The proof is simulatable and extractable as the ledger requires** — the same QROM bound that
   Theorem 3 supplies must still apply to the distributed prover, in the same gate accounting.
3. **It costs what the profile can pay.** The published setting is 2^32-leaf seed trees with an
   expansion of ℓ̂ = 15,296 bits per leaf; the sizes in the ledger assume the whole tree is
   computable.

## 2. Why the obvious answer does not work

### 2.1 A single aggregator can frame

Anyone who holds an opening (s_i, r_i) can compute a **second handle** for seat i under a different
message, Z_i′ = r_i⁷ ⊕ c(m′)·s_i, and prove it. That is a valid approval for a message seat i never
saw, and the public pair search will name seat i as a double-signer. So the proof may not be produced
by a party that learns an honest seat's opening — the security of the honest seats rests on the
producer's *honesty*, not on cryptography. This is assumption **A-Prove** in
`modeB_security_v1.49.md` §2, and the source marks it **essential, not technical**.

A trusted aggregator is a legitimate design point — it is exactly the "ideal F_Prove" premise
(v1.43 Theorem B premise E7) that Mode S already carried — but it is not what the profile asks for,
and a reader of any Mode B document must not take the theorems to cover it.

### 2.2 VOLE-in-the-head resists splitting

The proof's witness is the vector of committed bits (the seeds of the GGM trees, the corrections,
the ZK masks). Splitting it across parties is not a matter of sharding the computation:

- the **seed trees must stay hidden** — each party learns its own leaves only, and the all-but-one
  openings are on *leaves*, so the parties must jointly hold a tree nobody can reconstruct;
- the **correlation** (VOLE) is the resource that makes the check cheap, and generating it
  multi-party is the hard part: the honest parties must jointly produce the random VOLE instances
  *and* commit to them consistently;
- the **challenges are hashes of the commitments**, so every party's commitments must be fixed before
  any challenge is derived, and a single corrupt party that waits can bias or abort.

### 2.3 The published negative and the published cost

| Result | What it rules out / costs |
|---|---|
| Doerner–Kondi–Rosenbloom (CRYPTO'24) | **impossibility** for joint provers against **all-but-one** corruption with black-box hashing |
| Carozza–Couteau (2024/1897) | a **naive distributed FAEST-128s** needs ≈ 937 GB of seed trees |
| Feneuil et al. (2026/1125) | threshold MPC-in-the-head signature: a **single shared witness**, no ring, λ = 128 |
| v1.45 §4 | the hidden-quorum case needs ≤ 21 of 64 corruptions, which is the honest-majority regime |

The honest-majority case is **not ruled out** by the impossibility result. It is also not
constructed: no protocol for this setting was found in the literature search, and none was built
here.

## 3. What a solution must deliver

Restating the requirement in the form the ledger consumes (this is the acceptance test a future
collaborative prover has to pass, not a description of anything built here):

1. a **collaborative VOLE-in-the-head prover**, secure against **21 of 64** corruptions, for the
   Relation R_B's circuit (degree-6 QuickSilver check over ℓ = 13,760 committed bits + 1,536 masks);
2. running on **2^32–2^40-leaf** GGM trees without any party reconstructing a tree;
3. with a **QROM extraction bound** whose form can enter the v1.43 ledger — i.e. the multi-round
   loss accounted for, not modelled away (the DFMS-modelled R3 row of the ledger explicitly omits
   it; see [rigorous-ledger.md](rigorous-ledger.md));
4. at a cost the ledger can charge: the extraction charge in R2 already assumes an online extractor
   at time O(q²), and a distributed prover must not raise the exponent.

## 4. Status

**Open. Nothing of this exists in this domain.** There is no collaborative prover, no prototype, no
partial protocol and no simulation of one. The delivered artefacts verify that a *centralized*
prover's output is correct and that the extraction and ledger arithmetic hold; they do not touch
requirement 1 above. Any reading of this domain that treats the hidden-signer profile as solved has
missed this document.
