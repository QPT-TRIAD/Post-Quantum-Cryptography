# 1,000 operators amended for the QPT-128 proof effort

Version 1.33 · 9 September 2026

## What this amendment establishes

All 1,000 source entries have been read and retained with stable IDs. This amendment adds **116 specific corrections or restrictions**, **28 operator mutations**, **112 focused research questions**, and an applicability disposition for every entry. The mutations involve **182 distinct original operators**. The remaining **818** are parked until a concrete connection to a security obligation is supplied. These counts describe review coverage, not 1,000 certified mathematical theorems.

The main new quantitative result is a robust version of the proposed shrink rule. Under the explicit **challenge-mass premise** below, a per-round factor of **9/16 in probability**, equivalent to an amplitude factor of **3/4**, still lets **320 rounds** meet the existing extraction allocation at **Q=2^128**. Exact arithmetic checks the boundary. A general base-b prefix-count lemma extends the earlier ternary sampler calculation. Neither result provides the missing protocol-specific premise.

The complete deployed QPT-128 claim remains **OPEN**. In particular, a reduction's compressed-oracle database is not a public input automatically available to a conflict extractor. The actual joint decoder, concrete signature-hardness bound at the reduction's resources, and deployed-hash connection still need evidence. This amendment makes those missing pieces precise and rejects several ways of accidentally declaring them solved.

This pass concentrates on the 128-bit security proof. The 32-, 64-, and 92-bit rows are diagnostic evaluations of the same equations. They are not new primitive parameter sets. Certificate size is not recalculated here.

### How to use this document

1. Use the variable map and closure conditions to choose a proof obligation.
2. Open the linked investigation and answer its four questions with algorithms, a lemma, or a counterexample.
3. Read the corresponding corrected catalog entries; source claims remain visible for comparison.
4. Run the standalone Python checker in the final appendix. Its output validates arithmetic and finite examples, not an unimplemented cryptographic protocol.

The original assertion that 100–150 operators are novel is withdrawn: novelty was not established. Also, R, C and Q are fields; Z is a ring. An operator name containing “quantum,” “signature,” “lattice” or “entropy” does not supply a cryptographic theorem. Source cross-references are retained as historical text and may point to the wrong mathematical operation; the investigation membership lists are the curated links for this amendment.

## Target, variables and proof obligations

Use the following concrete target convention, inherited from v1.32:

\[
\forall A\text{ within the stated resource model},\quad
G(A)<2^{128}\Longrightarrow\Pr[\mathrm{Win}(A)]<1/3.
\]

This requires a gate set, treatment of classical work, memory/advice/precomputation assumptions, oracle access and success experiment. QPT means quantum polynomial time in an asymptotic security parameter; it does not, on its own, define this concrete gate budget. A query-model bound evaluated at Q=2^128 is only one component of the target. It also does not mean success must be at most 2^-128 at that entire query budget.

| Symbol or function | Required meaning | Useful mutated operators | Evidence needed |
|---|---|---|---|
| pp, roster, epoch, version | Public parameters and conflict domain | C20, O13, K32 | Canonical, unambiguous encoding and registry binding |
| id_i, pk_i | Distinct signer identity and its registered key | L25, L32, C45 | Registration and distinctness predicates; field/ring types fixed |
| sk_i, sigma_i | Secret signing key and authorization signature | I19, M2, Z35 | Exact signing game, good-key event, security reduction |
| R(x,w) | Complete quorum authorization relation | K29, K32, O41 | Witness schema, actual verification algorithm and relation theorem |
| cert_0, cert_1 | Public conflicting certificates | O13, P14, C20 | Both bind to the correct public statements |
| D | Reduction's shared compressed-oracle database | S9, N19, O9 | Exact oracle ownership, measurement timing and access model |
| Decode | Reconstruct both relation witnesses from D and proofs | K29, K33, K34 | Actual algorithm, joint correctness and resource proof |
| Trace | Public conflict-extraction algorithm | P17, H38, O13 | An algorithm using its declared public inputs, without importing D |
| Q, v, ell, h | Accounted query count, verifier queries, leaf bound, ideal output width | T3, T5, C1, A01 | Bound-specific accounting; no confusion with sponge capacity |
| b,t,r,p_* | Alphabet, allowed digits per bad coordinate, repetitions, maximum nonextractable mass | C1, C4, C48, M37 | Decoder-implied bad-set family and exact sampler distribution |
| Phi_t, K_(t,j), beta_t | Failure instrument, Kraus operators and uniform contraction bound | S15, S19, M2 | Matrix inequality on every reachable failure state |
| G1,G2,d1,d2 | Compatible good-key events and their failure probabilities | I19, M33, K29 | Both events on the same key-generation distribution |
| p,q_S,R_cap | Rejection bound, signing sessions, retry cap | M20, M10, C41 | Uniform conditional rejection and runtime-tail bounds |
| epsilon_sig(rho) | Signature advantage at resource vector rho | K20, R42, O41 | Remaining hardness term and adapters to deployed ML-DSA |
| H0, H, pi | Deployed hash, ideal function, ideal permutation | I7, I31, K50 | Distinct interfaces and property-specific assumptions/reductions |
| G,D_max,M | Gates, maximum logical depth, memory | T1–T5, L44, R33 | Actual circuit/resource model and composed reduction costs |

### Smallest concrete results that would close the main gaps

| Gap | Required deliverable | Investigations | Current state |
|---|---|---|---|
| Actual joint extraction | Decoder code/pseudocode plus a theorem for the exact relation and shared oracle experiment | A10, A18, A23 | Open |
| Public conflict extraction | Public-input Trace algorithm with verifiable culprit evidence | A19, A24 | Open; reduction-only D cannot be assumed available |
| Challenge-mass connection | Proof that the actual sampler's nonextractable family satisfies p_*<=beta^r, or an exact alternative bound | A05–A12 | General arithmetic/lemmas closed; protocol connection open |
| Concrete signature security | Bound on the remaining signature-hardness adversary at the composed resource vector | A13, A15–A17, A22 | Open |
| Compatible signature model | Same good-key event, actual key distribution and standardized-algorithm adapter | A13, A15, A16 | Conditional composition lemma closed; inputs open |
| Deployed hash | Game-specific properties for the exact hash and oracle interfaces, with concrete bounds | A20, A21, A25 | Open |
| Resource accounting | Query, gate, depth, memory and precomputation bounds for every reduction | A04, A22 | Algebraic composition closed; concrete inputs open |

## Partial proofs and substitutions

The following are elementary derivations for this amendment. They are not claims of new results in the mathematics literature. Any protocol-level application must discharge the stated premises.

### Lemma 1: budget inversion and event composition

Keep the conditional v1.32 extraction expression

\[
J(Q,h,p_*)=B_0+20Q^2p_*,\qquad
B_0=\frac{(72+40\ell)Q^3+2v}{2^h}.
\]

For Q>0 and p_*>=0, J<=tau is equivalent to

\[
p_*\le\frac{\tau-B_0}{20Q^2}.
\]

For a strictly positive admissible mass this requires B0<tau. If B0=tau only p_*=0 is feasible, which a nonempty positive-mass bad set cannot achieve. If B0>tau there is no feasible nonnegative mass. This is algebraic inversion, not a proof that the desired p_* can be achieved.

For events E_i in one probability space, 1_(union E_i)<=sum_i 1_(E_i) pointwise. Taking expectations proves the union bound without independence. Conversely, if both a and b bound the **same** probability, their minimum is also an upper bound. Taking a minimum across distinct failure events, or normalizing their coordinatewise maxima, has no such justification.

**Source boundary.** The inherited expression is a conditional extension of a commit-and-open QROM analysis. The primary paper [S1] supplies extraction theorems for protocols satisfying its specified soundness and commitment hypotheses. This document does not establish that the current verifier satisfies those hypotheses. The extension and its budget inputs come from the supplied workspace report v1.32.

### Lemma 2: adaptive failure contraction

**Classical version.** Let B_t be failure in round t and H_(t-1) a reachable history in which all earlier rounds failed. Suppose

\[
\Pr[B_t\mid H_{t-1}]\le\beta_t
\]

uniformly over those histories, with 0<=beta_t<=1. The tower property gives

\[
\Pr[B_1\cap\cdots\cap B_n]\le\prod_{t=1}^n\beta_t.
\]

Indeed, multiply the conditional inequality by the indicator of earlier failure, average, and induct. Marginal bounds alone do not suffice: taking every B_t to be the same fair-coin event leaves their intersection probability at 1/2 for all n.

**Quantum version.** Represent retained failure branches by the completely positive map

\[
\Phi_t(\rho)=\sum_j K_{t,j}\rho K_{t,j}^{\dagger}.
\]

Assume the positive-semidefinite inequality

\[
\sum_jK_{t,j}^{\dagger}K_{t,j}\preceq\beta_t I
\tag{QC}
\]

on every reachable input failure subspace. For any positive, possibly subnormalized state rho on that subspace,

\[
\operatorname{tr}\Phi_t(\rho)
=\operatorname{tr}\!\left(\rho\sum_jK_{t,j}^{\dagger}K_{t,j}\right)
\le\beta_t\operatorname{tr}\rho.
\]

The inequality survives tensoring with an arbitrary identity on a reference system because positive-semidefinite order does. Thus entanglement with an external reference does not defeat this uniform certificate. Adaptive classical branches can be included in a block-diagonal history register, provided (QC) holds in every block. Trace-preserving adversarial interleavings are admissible only when the next certificate covers all states they can reach. Induction then proves the same product bound for the unnormalized retained-failure state.

This is a statement about an explicitly specified instrument. All other outcomes must be accounted for, and failure must correspond to the event under study. Conditioning on survival and renormalizing to trace one would discard exactly the probability being bounded. A full unitary preserves norm. Neither renormalization nor a unitary alone produces this contraction. Standard channel/instrument conventions are described in [S7].

With beta_t=1/2, the probability factor is 2^-n and its square-root amplitude factor is 2^(-n/2), matching the user's recurrence.

### Lemma 3: robust contraction and a 128-bit component calculation

For a single failure operator, the triangle inequality gives

\[
\|K\|\le\|K_0\|+\|K-K_0\|\le2^{-1/2}+\eta.
\]

For several Kraus operators the same argument applies to the stacked map A:v->sum_j |j> tensor K_j v, since A^dagger A=sum_j K_j^dagger K_j. Therefore a proved perturbation bound on that **whole** map is sufficient; per-entry numerical errors cannot simply be substituted for eta.

A convenient exact certificate is

\[
\sum_jK_j^{\dagger}K_j\preceq\frac9{16}I,
\]

which permits amplitude norm 3/4. Relative to the original norm 1/sqrt(2), the sufficient absolute perturbation allowance is at most 3/4-1/sqrt(2), approximately 0.042893. No such allowance has yet been proved for the actual protocol.

**Essential bridge obligation.** To insert the product bound into J, prove that it bounds J's particular p_*: the maximum mass of a **nonextractable challenge set under the exact challenge map**. Contracting an unrelated error, witness norm, numerical residual or verifier-rejection state is not enough. The checker rejects contract records whose event fields differ. Quantum contraction is one possible proof tool; it is not a replacement for the decoder-implied bad-set theorem.

Conditional on that bridge, fix

\[
Q=2^s,\quad h=512,\quad \ell=2^{20},\quad
v=2(21\ell+1),\quad\tau=1/24.
\]

The exact minimum-round tests give:

| Query exponent s | Rounds with p_*<=2^-n | Rounds with p_*<=(9/16)^n |
|---:|---:|---:|
| 32 | 73 | 88 |
| 64 | 137 | 165 |
| 92 | 193 | 233 |
| 128 | 265 | 320 |

For every row, the program checks that n passes and n-1 fails the allocation with exact rational arithmetic. In the last robust row,

\[
\boxed{J(2^{128},512,(9/16)^{320})
\approx0.025346\;<\;1/24\approx0.041667.}
\]

The displayed decimal is rounded; pass/fail uses the exact rational expression. Its base-two logarithm is approximately -5.302071. This is a conditional extraction component bound, not a 2^-128 forgery probability and not a proof of complete QPT-128. The round count is also not a measured gate depth: even a serial implementation needs setup_depth+n*round_depth, with both terms supplied.

### Lemma 4: exact maximal mass for base-b product boxes

Let b>=2, 1<=t<b, r>=0 and U uniform on {0,...,2^h-1}. The sampler outputs the r-digit base-b representation of U mod b^r. A permitted bad box has at most t allowed digits in each coordinate. Write

\[
2^h=ab^r+R,\qquad0\le R<b^r,
\]

and define

\[
C_{b,t,r}(R)=\#\{x<R:\text{every one of its r base-b digits is smaller than }t\}.
\]

Then the maximum mass of a bad box is exactly

\[
\boxed{p_{\max}(h,b,t,r)=\frac{at^r+C_{b,t,r}(R)}{2^h}.}
\tag{BOX}
\]

**Proof.** Enlarge each coordinate set to t digits, which cannot reduce mass. Every residue receives a preimages, plus one if below R. The full-cycle contribution is therefore at^r. Sort the allowed digits in each coordinate as d_0<...<d_(t-1). The coordinatewise map d_i->i is injective and never increases the resulting base-b integer because d_i>=i. It sends any box point below R to a point below R in the all-{0,...,t-1} box. Thus that box maximizes the prefix intersection and attains C_(b,t,r)(R). Dividing by 2^h proves (BOX).

The prefix counter reads R from its most significant digit. At digit d with k lower positions, add min(d,t)*t^k for all smaller allowed leading digits. If d>=t, stop; otherwise continue on the remaining suffix. R=b^r is the endpoint with count t^r. This is an exact integer algorithm with O(r) digit steps; the bit complexity of big-integer arithmetic still has to be charged if used in a resource-sensitive algorithm.

When b^r>=2^h, increasing r only adds leading zeroes, so the worst box mass stops improving. For the ternary case b=3,t=2, h=2,r=2 yields 3/4, not the uniform-ternary guess 4/9. The checker independently enumerates all coordinate subsets in small instances. At h=512 it also checks equality between r=324 and r=512. The inherited 720-bit ideal-source ternary example still passes its component bound, but remains an ideal-source example.

**Use limit.** The decoder must imply the product-box containment. A general nonextractable family may not have this structure. Changing b or t changes that proof obligation; no generic conversion from three-response to two-response special soundness follows.

### Lemma 5: compatible good events and finite retry tails

Let X>=0, Pr(G1^c)<=d1, Pr(G2^c)<=d2, d1+d2<1, and E[X|G1]<=epsilon. Write g=Pr(G1). Since

\[
\mathbb E[X1_{G_1\cap G_2}]\le\epsilon g,
\quad\Pr[G_1\cap G_2]\ge g-d_2,
\]

we have

\[
\mathbb E[X\mid G_1\cap G_2]
\le\epsilon\frac{g}{g-d_2}
\le\epsilon\frac{1-d_1}{1-d_1-d_2}.
\]

The second inequality holds because g/(g-d2) is nonincreasing for g>d2, and g>=1-d1. The intersection's failure probability is at most d1+d2. This proof uses neither independence nor a replacement key distribution. A four-equiprobable-outcome example in the checker achieves the inflation factor exactly.

If each retry rejects with conditional probability at most p under every reachable history in that common good event, Lemma 2 gives at most p^R for R consecutive rejections. A union bound over q_S signing sessions gives q_S p^R. The exact boundary q_S=2^64, p=759/1024, target 2^-160 is R=519; R=518 does not suffice. The input bound p remains a condition, not a fact established by this test.

### Lemma 6: finite-field rank counting and entropy discipline

**Rank.** For a uniformly sampled m-by-n matrix over the finite field F_q, the number with rank r is

\[
N_{m,n,r}(q)=
\prod_{i=0}^{r-1}\frac{(q^m-q^i)(q^n-q^i)}{q^r-q^i}.
\]

To prove this, choose its r-dimensional image in F_q^m. Count its ordered bases as product_i(q^m-q^i) and divide by product_i(q^r-q^i) to count subspaces. For each fixed image, the surjective linear maps from F_q^n onto it correspond, after choosing a basis, to r independent rows: product_i(q^n-q^i) choices. Multiply. The formula sums to q^(mn) because every matrix has one rank. This does not make a seeded, module-structured matrix uniform; that distribution step is separate.

**Entropy.** Let X be classical and E arbitrary quantum side information. From any POVM {M_x} guessing X, form N_y=sum_(x:f(x)=y) M_x. This is a POVM guessing f(X), and its success includes every successful guess of X. Hence

\[
p_{\rm guess}(f(X)\mid E)\ge p_{\rm guess}(X\mid E),\qquad
H_{\min}(f(X)\mid E)\le H_{\min}(X\mid E).
\]

A deterministic transform cannot increase this secret-entropy quantity. An independently seeded quantum-proof randomness extractor has a different contract, including a pre-existing entropy bound and a loss depending on output length and error. The relevant leftover-hash theorem is [S4]. It is not a theorem about extracting a quorum witness from a public proof.

### Lemma 7: resource composition and the limited MAXDEPTH interpretation

For an explicit acyclic circuit whose node v has gate count g_v and sequential depth d_v, total counted work is sum_v g_v. If arbitrary parallel execution is available and only the stated dependencies constrain it, the critical-path recursion depth(v)=d_v+max_(u predecessor v)depth(u) gives the schedule depth. Fewer processors, communication or a shared quantum oracle may introduce further constraints. They do not reduce total work by definition.

For monotone resource maps, time(B)<=f(time(A)) and time(C)<=g(time(B)) imply time(C)<=g(f(time(A))). Similarly, if advantages satisfy epsilon_A<=a*epsilon_B+b and epsilon_B<=c*epsilon_C+d with a,c>=0, then epsilon_A<=a*c*epsilon_C+a*d+b. Every function is evaluated at its appropriate resource vector; probability loss and time inflation are distinct.

The user's recurrence has a second, separate interpretation for normalized partitioned search: with search space N, P=2^n processors and ideal per-processor iterations a_n=sqrt(N/P), total iterations are sqrt(NP). Reducing per-processor depth increases total work in this model. It does not establish security against lattice algorithms, arbitrary quantum algorithms, or attacks on the actual signature. Search optimality results have a specified oracle/search model [S8]; MAXDEPTH cannot be used to erase unrelated proof obligations.

### Lemma 8: reject quantifier and idealization substitutions

For any payoff u(x,y), inf_x u(x,y)<=u(x,y)<=sup_y u(x,y). Taking the suitable extrema yields

\[
\sup_y\inf_xu(x,y)\le\inf_x\sup_yu(x,y).
\]

Pure-strategy matching pennies gives -1 and 1, respectively. Equality needs extra structure; it cannot justify choosing security parameters after an adversary is revealed.

For a fixed publicly computable h-bit function H0, choose a fixed input x0 and precompute y0=H0(x0), charging that computation. Query the provided oracle at x0 and test equality with y0. Against H0 the equality always holds; against an independent uniform random function it holds with probability 2^-h. The acceptance-probability gap is 1-2^-h. Therefore generic indistinguishability from an independent random oracle is the wrong deployed-hash premise. A property-specific game or a simulator-based idealization has a different definition and must be analyzed on that definition. In particular, [S3] works with a uniformly random permutation, not a proof that a fixed named permutation is random.

Finally, type-compatible records do not prove their contents. A classical public Trace algorithm cannot use a reduction-only database D unless an explicit algorithm makes the required information available through its allowed public inputs. This observation leaves room for a new construction; it prevents an unavailable object from masquerading as that construction.

## Priority investigation sequence

| Priority | Work to do | Stop/go criterion |
|---:|---|---|
| 1 | A18–A19: write Decode and public Trace interfaces for the actual certificates | If either needs undeclared data, repair the architecture before tuning numerical parameters |
| 2 | A11–A12: derive the nonextractable family and exact sampler | Obtain a proved p_* bound for this relation; do not relabel the challenge alphabet |
| 3 | A06–A08: try an exact contraction certificate | Verify the whole failure instrument and its connection to p_*; the 9/16 target is a concrete sufficient goal |
| 4 | A15–A17: finish the signature reduction | Supply the remaining hardness bound and same-distribution good-event proof at transformed resources |
| 5 | A20–A22: close hash and cost interfaces | Specify deployed-hash assumptions and actual gate/depth/memory costs; reject generic RO equivalence |
| 6 | A28: compose only the discharged contracts | Check the constant-success target with all residual terms included |

The first priority is essential even though the arithmetic now has room: no amount of contraction in the wrong event, or accuracy in a model with unavailable extraction data, closes the desired theorem.

## Primary sources used for the cryptographic interfaces

These are theorem/definition sources, not interchangeable components. The new algebraic proofs above are supplied in full. The original catalog's unrelated mathematical claims are not all independently literature-certified by this amendment.

- **[S1]** Don, Fehr, Majenz and Schaffner, [Efficient NIZKs and Signatures from Commit-and-Open Protocols in the QROM](https://arxiv.org/pdf/2202.13730), 2022. Definitions and extraction theorems for the specified commit-and-open setting; inspect the special-soundness and Merkle-commitment hypotheses before applying them.
- **[S2]** Barbosa et al., [Fixing and Mechanizing the Security Proof of Fiat-Shamir with Aborts and Dilithium](https://ir.cwi.nl/pub/33405/33405.pdf), Theorem 2. Corrected QROM CMA-to-NMA reduction with a compatible good-key event and an explicit additive loss. The mechanized proof described in the paper is the ROM proof; a small additive loss is not the remaining hardness bound.
- **[S3]** Cojocaru, Hhan, Liu, Yamakawa and Yun, [Quantum Lifting for Invertible Permutations and Ideal Ciphers](https://arxiv.org/pdf/2504.18188), 2025, Corollary 6.9 and model definitions. Covers ideal-permutation sponge collision bounds under the stated access and call counts. It does not certify the fixed deployed permutation.
- **[S4]** Tomamichel, Schaffner, Smith and Renner, [Leftover Hashing Against Quantum Side Information](https://arxiv.org/pdf/1002.2436), Theorem 6 and the conditional guessing interpretation. Applies to independently seeded two-universal hashing with a suitable conditional min-entropy bound. The exact distance convention and smoothing parameters must match an application.
- **[S5]** Keccak designers, [Keccak specifications summary](https://keccak.team/keccak_specs_summary.html), standard-instance table. SHAKE256 has rate 1088 and capacity 512 bits with variable output length; output width is not capacity.
- **[S6]** NIST, [FIPS 204: Module-Lattice-Based Digital Signature Standard](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.204.pdf), 2024. Specifies ML-DSA algorithms and parameter sets. An implementation adapter must match those algorithms; this document does not alter them.
- **[S7]** John Watrous, [The Theory of Quantum Information](https://cs.uwaterloo.ca/~watrous/TQI/TQI.pdf), channel and instrument definitions in Chapter 2. Supplies standard finite-dimensional Kraus/positive-map conventions used in the elementary contraction proof.
- **[S8]** Christof Zalka, [Grover's quantum searching algorithm is optimal](https://arxiv.org/pdf/quant-ph/9711070). Search-specific resource reasoning; not a blanket hardness theorem for all quantum attacks.

**Workspace baseline:** `continuation_v1.32/report.md` supplied the prior conditional joint-bound settings and ternary comparison. No new claim is made that all earlier attachments were independently re-audited in this pass.

## Review provenance and coverage
Attached source: `operators_1000(1).md`; SHA-256 `95e846198d956426a348d9f1bc8aa8692e36971b11340a1b3d6c28d446da1e95`.

Workspace baseline report SHA-256: `ebdcd6e82374c3f8d5af98d58f11af524027e0a5b85cdedfa388e398ddddb4b8`.

The original source property is preserved as historical, unverified text in every entry. A specific amendment supersedes it for this project where provided. No amendment means **not certified**, not “true.” Parked means no direct QPT-128 contribution was established here; it does not assert that the mathematics is useless. All 1,000 eligibility questions are preliminary triage prompts; the 112 questions in A01–A28 are the focused investigation register.

| Family | Entries retained | Active investigation members | Entries with specific amendments |
|---|---:|---:|---:|
| L: Lattice and order | 50 | 17 | 16 |
| T: Tropical and idempotent algebra | 50 | 8 | 8 |
| F: Fractional calculus | 50 | 5 | 7 |
| Q: q-deformed operators | 50 | 6 | 8 |
| D: Discrete difference calculus | 50 | 6 | 7 |
| I: Information theory | 50 | 18 | 8 |
| P: Paths and loops | 50 | 3 | 8 |
| S: Spectral operators | 50 | 18 | 7 |
| M: Probability and measure | 50 | 18 | 7 |
| C: Combinatorics and generating functions | 50 | 11 | 6 |
| H: Topology and homology | 50 | 1 | 3 |
| K: Category theory | 50 | 11 | 3 |
| N: Noncommutative algebra | 50 | 1 | 2 |
| X: Stochastic calculus | 50 | 2 | 3 |
| G: Geometry and Lie/Clifford operators | 50 | 1 | 0 |
| R: Quantum resource theory | 50 | 12 | 9 |
| O: Logic and verification | 50 | 21 | 5 |
| W: Multiscale transforms | 50 | 10 | 2 |
| Y: Games and decisions | 50 | 8 | 5 |
| Z: Hybrid constructions | 50 | 5 | 2 |

## Mutated operators and focused research questions

Each mutation is a proposed use with a precise contract. The formula is established only to the extent stated in the linked lemma; it is not evidence that a deployed protocol realizes the map. Member IDs refer to the full catalog below.

| Mutation | Purpose | Obligation |
|---|---|---|
| [A01](#a01) | Invert a valid error budget | BOUND |
| [A02](#a02) | Compose failure events without independence | COMPOSITION |
| [A03](#a03) | Keep the worst-case quantifiers | QUANTIFIERS |
| [A04](#a04) | Count serial work and parallel depth separately | RESOURCES |
| [A05](#a05) | Give the shrink recurrence a measurable meaning | CONTRACTION |
| [A06](#a06) | Certify quantum contraction by a matrix inequality | QUANTUM_CONTRACTION |
| [A07](#a07) | Allow certified imperfections in the shrink factor | ROBUST_CONTRACTION |
| [A08](#a08) | Handle dependent repetitions | ADAPTIVITY |
| [A09](#a09) | Reject spectral shortcuts | QUANTUM_CONTRACTION |
| [A10](#a10) | Treat measurement and copying as explicit operations | JOINT_EXTRACTOR |
| [A11](#a11) | Count the actual challenge distribution | CHALLENGE_MASS |
| [A12](#a12) | Make a sampler change a protocol change | CHALLENGE_ENCODING |
| [A13](#a13) | Bound rejection and finite runtime | RUNTIME_TAIL |
| [A14](#a14) | Use guessing entropy and forbid free entropy creation | ENTROPY |
| [A15](#a15) | Use finite-field rank for the actual distribution | SIGNATURE_GOOD_KEYS |
| [A16](#a16) | Glue good-key events without inventing independence | GOOD_EVENT_GLUE |
| [A17](#a17) | Turn a security label into a reduction contract | SIGNATURE_SECURITY |
| [A18](#a18) | Construct the actual joint decoder interface | JOINT_EXTRACTOR |
| [A19](#a19) | Separate a reduction extractor from public conflict extraction | PUBLIC_CE |
| [A20](#a20) | Make the fixed-hash bridge property-specific | DEPLOYED_HASH |
| [A21](#a21) | Track hash width separately from sponge capacity | HASH_PARAMETERS |
| [A22](#a22) | Account for proof-reduction resource inflation | REDUCTION_RESOURCES |
| [A23](#a23) | Make finite checks proof aids with explicit scope | VALIDATION |
| [A24](#a24) | Keep distributed authorization in the witness relation | AUTHORIZATION_INTERFACE |
| [A25](#a25) | Use randomness extraction only where its seed premise holds | RANDOMNESS_EXTRACTION |
| [A26](#a26) | Replace random-looking tests with finite guarantees | TEST_LIMITS |
| [A27](#a27) | Do not turn smoothing into a security assumption | ANALOGY_FILTER |
| [A28](#a28) | Replace the master operator by a compatibility record | FINAL_GLUE |

<a id="a01"></a>

### A01: Invert a valid error budget

**Original operators:** [L1](#op-l1), [L2](#op-l2), [L3](#op-l3), [L4](#op-l4), [L16](#op-l16), [O3](#op-o3).

**Mutated formula or interface:** p_allowed=(tau-B0)/(20*Q^2), provided B0<tau; otherwise the proposed bound has no feasible p>=0.

**Contract and proof scope:** Replace a threshold meet by a typed feasibility predicate on proven nonnegative bounds. B0, Q and tau belong to one specified game. Lemma 1 proves the inversion.

1. **A01-Q1.** Which exact event is being bounded, and are Q, h, leaf count and verifier calls from that same experiment?
2. **A01-Q2.** At Q=2^128 and h=512, how small must the nonextractable challenge mass be after the hash term is reserved?
3. **A01-Q3.** Does a proposed improvement reduce an actual summand, or merely rename the threshold?
4. **A01-Q4.** Can the checker reject B0>=tau and a missing input instead of silently substituting zero?

<a id="a02"></a>

### A02: Compose failure events without independence

**Original operators:** [L9](#op-l9), [L10](#op-l10), [T32](#op-t32), [I17](#op-i17), [M1](#op-m1), [M25](#op-m25).

**Mutated formula or interface:** Pr(union_i E_i)<=sum_i epsilon_i; for two proved bounds on the SAME event use min(epsilon_a,epsilon_b).

**Contract and proof scope:** Replace normalized majorization envelopes with unnormalized event budgets. Events must be defined on one joint experiment, or connected by explicit hybrid reductions. Lemma 1.

1. **A02-Q1.** Can extractor failure, binding failure, signature forgery and truncation failure be defined on one coupled execution?
2. **A02-Q2.** Are two reported bounds alternatives for one event, or errors of separate components that must be added?
3. **A02-Q3.** Is a failure term counted twice after good-key conditioning, and where is that event charged?
4. **A02-Q4.** Does the total conditional bound stay below the chosen constant-success threshold without assuming independent failures?

<a id="a03"></a>

### A03: Keep the worst-case quantifiers

**Original operators:** [Y1](#op-y1), [Y2](#op-y2), [Y4](#op-y4), [L7](#op-l7), [L8](#op-l8), [L49](#op-l49).

**Mutated formula or interface:** sup_adversary inf_design u <= inf_design sup_adversary u; deployment fixes the design before the attack.

**Contract and proof scope:** Correct minimax direction. A Pareto frontier compares already valid bounds; it does not interchange a key, adversary or extractor quantifier. Lemma 8.

1. **A03-Q1.** Does the claimed extractor exist uniformly for all adversaries, or is a different uncomputable extractor selected after seeing each attack?
2. **A03-Q2.** Was an average over generated keys replaced by a bound for every key without a bad-key event?
3. **A03-Q3.** Does searching a finite collection of attacks produce only lower bounds on attack success?
4. **A03-Q4.** Which candidate parameters minimize the worst proved error with all required resources charged?

<a id="a04"></a>

### A04: Count serial work and parallel depth separately

**Original operators:** [T1](#op-t1), [T2](#op-t2), [T3](#op-t3), [T4](#op-t4), [T5](#op-t5), [T37](#op-t37), [L44](#op-l44), [L45](#op-l45), [L47](#op-l47).

**Mutated formula or interface:** work=sum_v g_v; depth(v)=d_v+max_(u predecessor v) depth(u); peak live memory is a separate quantity.

**Contract and proof scope:** Mutate tropical path operators to an explicit finite circuit DAG with nonnegative gate costs. MAXDEPTH restricts sequential depth, not total work. Lemma 7.

1. **A04-Q1.** Which gates, oracle evaluations, uncomputations and output checks appear in the actual circuit DAG?
2. **A04-Q2.** When a branch is duplicated to reduce depth, how many processors and gates does that duplication add?
3. **A04-Q3.** Does a dependency through a shared oracle prevent the proposed parallel schedule?
4. **A04-Q4.** Are the depth cap and the total gate cap both satisfied after the extractor is included?

<a id="a05"></a>

### A05: Give the shrink recurrence a measurable meaning

**Original operators:** [D1](#op-d1), [D7](#op-d7), [D30](#op-d30), [D46](#op-d46), [D48](#op-d48), [Q1](#op-q1), [Q3](#op-q3), [Q10](#op-q10), [Q11](#op-q11), [Q40](#op-q40).

**Mutated formula or interface:** a_n=a_0*2^(-n/2); p_n=a_n^2=p_0*2^(-n); n_min=min{n:B0+20*Q^2*2^(-n)<=tau}.

**Contract and proof scope:** Use the recurrence for a specified unnormalized failure amplitude, not the norm of a full unitary state. Counting rounds and bounding their effect are separate obligations. Lemma 2.

1. **A05-Q1.** What state vector or failure event does a_n denote in the real proof protocol?
2. **A05-Q2.** Can each repetition be shown to halve its failure probability under the adversarial history?
3. **A05-Q3.** Why are 128 halvings insufficient when the security reduction multiplies their probability by 20*Q^2?
4. **A05-Q4.** Do exact boundary tests give 73, 137, 193 and 265 rounds for the four chosen query caps?

<a id="a06"></a>

### A06: Certify quantum contraction by a matrix inequality

**Original operators:** [S11](#op-s11), [S15](#op-s15), [S19](#op-s19), [S27](#op-s27), [S32](#op-s32), [S46](#op-s46), [W40](#op-w40).

**Mutated formula or interface:** sum_j K_(t,j)^* K_(t,j) <= beta_t I implies tr Phi_t(rho)<=beta_t tr rho; iterate on the full failure state.

**Contract and proof scope:** Use a completely positive, trace-nonincreasing FAILURE instrument. Include private memory and adaptivity in the model. The inequality must hold on every reachable failure-state subspace. Lemma 2.

1. **A06-Q1.** Can the real verifier/extractor transition be expressed as Kraus operators including every retained failure branch?
2. **A06-Q2.** Can an exact positive-semidefinite certificate establish sum K* K<=beta I, rather than sampling a few vectors?
3. **A06-Q3.** Does the certificate remain valid with an arbitrary entangled reference system?
4. **A06-Q4.** Can an adversarial interleaving move amplitude into an unbounded subspace or reintroduce already removed failure paths?

<a id="a07"></a>

### A07: Allow certified imperfections in the shrink factor

**Original operators:** [S27](#op-s27), [S15](#op-s15), [S19](#op-s19), [W19](#op-w19), [W49](#op-w49).

**Mutated formula or interface:** ||K-K0||<=eta and ||K0||<=1/sqrt(2) give ||K||<=1/sqrt(2)+eta. A sufficient tested replacement is K*K<=9I/16.

**Contract and proof scope:** For several Kraus operators apply the norm perturbation to their stacked operator. The error is a rigorous implementation/reduction bound, not an empirical standard deviation. Lemma 3.

1. **A07-Q1.** Can a total per-round amplitude norm of at most 3/4 be proved for the actual transition?
2. **A07-Q2.** Does the exact inequality B0+20*2^256*(9/16)^320<=1/24 hold?
3. **A07-Q3.** What is the minimum repetition count at 32, 64, 92 and 128 under this weaker contraction?
4. **A07-Q4.** If only a numerical matrix norm is known, what certified rounding enclosure makes it safe to use?

<a id="a08"></a>

### A08: Handle dependent repetitions

**Original operators:** [M2](#op-m2), [M14](#op-m14), [M15](#op-m15), [I19](#op-i19), [M33](#op-m33).

**Mutated formula or interface:** Pr(B_t | B_1,...,B_(t-1), history)<=beta_t implies Pr(all B_t)<=product_t beta_t.

**Contract and proof scope:** Use conditional bounds and the tower property instead of claiming independent rounds. A marginal Pr(B_t)<=1/2 for each t is insufficient. Lemma 2 gives both classical and quantum versions.

1. **A08-Q1.** Is the bound uniform over all reachable histories, including previous rejection outcomes?
2. **A08-Q2.** Can two individually half-probability failures be perfectly correlated in this protocol?
3. **A08-Q3.** Which information is visible when the next challenge is sampled?
4. **A08-Q4.** Can the same conditional guarantee be maintained after both conflicting certificates have been selected?

<a id="a09"></a>

### A09: Reject spectral shortcuts

**Original operators:** [S7](#op-s7), [S18](#op-s18), [S21](#op-s21), [S22](#op-s22), [S34](#op-s34), [T8](#op-t8).

**Mutated formula or interface:** rho(K)<1 does not imply ||K||<1; K=[[0,2],[0,0]] has rho(K)=0 and ||K||=2.

**Contract and proof scope:** Use singular values or a certified weighted Lyapunov inequality, charging the equivalence constants of any changed norm. This is a necessary repair before the recurrence is applied.

1. **A09-Q1.** Was an eigenvalue bound mistakenly used as a one-step failure-amplitude bound for a nonnormal matrix?
2. **A09-Q2.** Do truncation or Krylov residuals hide a larger singular value?
3. **A09-Q3.** If a weighted norm contracts, what factor converts its bound back to physical trace/probability?
4. **A09-Q4.** Is the purported spectral gap attached to a valid quantum channel or only to a classical diagnostic matrix?

<a id="a10"></a>

### A10: Treat measurement and copying as explicit operations

**Original operators:** [N19](#op-n19), [G1](#op-g1), [S9](#op-s9), [S12](#op-s12), [S16](#op-s16), [R21](#op-r21), [K14](#op-k14), [K17](#op-k17), [O9](#op-o9), [O11](#op-o11).

**Mutated formula or interface:** The shared oracle state is used once; two classical witnesses may be computed from one measured database. Independent projective checks commute only under a proved condition.

**Contract and proof scope:** A tensor symbol does not clone an unknown state. Terminal measurement avoids a future-continuation claim; it still needs the correct global bad-database theorem and decoder. External reference S1; elementary measurement counterexample in the checker.

1. **A10-Q1.** Can both verifiers run before the one terminal database measurement in the intended security game?
2. **A10-Q2.** Is a classical copy operation being applied only after the data have become classical?
3. **A10-Q3.** Where would an earlier measurement change the probability of the second verification?
4. **A10-Q4.** Does the application require continuing with the same quantum oracle after extraction, which needs a stronger theorem?

<a id="a11"></a>

### A11: Count the actual challenge distribution

**Original operators:** [C1](#op-c1), [C4](#op-c4), [C5](#op-c5), [C48](#op-c48), [C49](#op-c49), [D19](#op-d19).

**Mutated formula or interface:** p_max(h,b,t,r)=(a*t^r+C_(b,t,r)(R))/2^h, where 2^h=a*b^r+R and C counts prefix integers with every digit<t.

**Contract and proof scope:** Assume every nonextractable challenge set lies in a product box with at most t allowed digits per coordinate. This generalizes the v1.32 ternary lemma; it does not prove that containment for a new protocol. Lemma 4.

1. **A11-Q1.** What exact family of accepted challenge sets fails to reveal the required witness?
2. **A11-Q2.** Is it contained in t-of-b product boxes, or does the decoder require a different set system?
3. **A11-Q3.** What is the maximal mass of that family under the implemented bit-to-challenge map?
4. **A11-Q4.** Does adding leading digits after b^r>=2^h leave the worst bad-box mass unchanged?

<a id="a12"></a>

### A12: Make a sampler change a protocol change

**Original operators:** [M36](#op-m36), [M37](#op-m37), [I7](#op-i7), [I32](#op-i32), [I38](#op-i38), [C19](#op-c19), [C20](#op-c20), [O13](#op-o13), [K31](#op-k31).

**Mutated formula or interface:** Uniform binary prefixes have point mass 2^(-r) for r<=h; U_h mod b^r generally does not give uniform b-ary challenges.

**Contract and proof scope:** Provide canonical serialization and an exact sampling map. Changing ternary to binary needs a new special-soundness theorem, not just a different encoding.

1. **A12-Q1.** Is the hash input unambiguously bound to protocol version, roster, epoch, message and commitment?
2. **A12-Q2.** Are reductions using the identical challenge map and domain separation as the verifier?
3. **A12-Q3.** For a binary replacement, which two distinct accepted responses reconstruct the actual quorum witness?
4. **A12-Q4.** Does a proposed distribution-distance bound remain meaningful after adaptive quantum queries to its generating oracle?

<a id="a13"></a>

### A13: Bound rejection and finite runtime

**Original operators:** [M20](#op-m20), [M21](#op-m21), [M10](#op-m10), [M11](#op-m11), [M12](#op-m12), [C41](#op-c41).

**Mutated formula or interface:** If each attempt rejects with conditional probability at most p, Pr(R consecutive rejections)<=p^R; q_S sessions cost at most q_S*p^R by a union bound.

**Contract and proof scope:** A key-averaged rejection estimate does not provide the uniform conditional premise. Fresh randomness, correlated retries and total executed attempts must be specified. Lemma 5.

1. **A13-Q1.** Is the rejection probability bounded for every key in the SAME good-key event used by the signature reduction?
2. **A13-Q2.** At q_S<=2^64 and p<=759/1024, does R=519 suffice for a 2^-160 truncation budget and R=518 fail it?
3. **A13-Q3.** How does aborting after R attempts change signing correctness and the security experiment?
4. **A13-Q4.** For rejection sampling of challenges, are all additional oracle calls and possible adversarial retry choices counted?

<a id="a14"></a>

### A14: Use guessing entropy and forbid free entropy creation

**Original operators:** [I1](#op-i1), [I2](#op-i2), [I20](#op-i20), [I30](#op-i30), [I33](#op-i33), [I34](#op-i34), [R26](#op-r26), [W18](#op-w18), [W48](#op-w48), [W50](#op-w50).

**Mutated formula or interface:** H_min(X|E)=-log2 p_guess(X|E); H_min(f(X)|E)<=H_min(X|E) for deterministic f.

**Contract and proof scope:** Distinguish secret randomness extraction from witness extraction. A reversible change of coordinates preserves information; a deterministic compressor cannot create secret entropy. Lemma 6; external reference S4.

1. **A14-Q1.** Which variable is secret, and what classical/quantum side information does E contain at the time of use?
2. **A14-Q2.** Does the operator improve conditional guessing probability or only a Shannon-entropy/visual statistic?
3. **A14-Q3.** What entropy assumption survives after the public key, transcript and rejection information are revealed?
4. **A14-Q4.** If compression discards information, is that information necessary to verify authorization or extract a conflict witness?

<a id="a15"></a>

### A15: Use finite-field rank for the actual distribution

**Original operators:** [Q5](#op-q5), [C45](#op-c45), [C15](#op-c15), [C14](#op-c14), [S24](#op-s24), [S25](#op-s25), [S30](#op-s30).

**Mutated formula or interface:** N_(m,n,r)(q)=product_(i=0..r-1) ((q^m-q^i)*(q^n-q^i))/(q^r-q^i), for rank-r m-by-n matrices over F_q.

**Contract and proof scope:** Uniform finite-field counts require a uniform finite-field distribution. A real SVD, integer Smith form, seeded module matrix and CRT components are different objects; the required distribution adapter remains open.

1. **A15-Q1.** Which rank deficiency controls the signature entropy estimate, over which field or module?
2. **A15-Q2.** Can the exact rank-count identity replace a loose union bound in that SAME distribution?
3. **A15-Q3.** Does the standardized XOF-expanded matrix have the independence used by the rank calculation?
4. **A15-Q4.** Can the entropy and rejection good-key events be intersected without invalidating either estimate?

<a id="a16"></a>

### A16: Glue good-key events without inventing independence

**Original operators:** [I17](#op-i17), [I19](#op-i19), [M2](#op-m2), [M33](#op-m33), [K29](#op-k29).

**Mutated formula or interface:** Pr(G1 intersect G2)>=1-d1-d2; E[X|G1 intersect G2]<=epsilon*(1-d1)/(1-d1-d2) if E[X|G1]<=epsilon, Pr(Gi^c)<=di.

**Contract and proof scope:** Require X>=0 and d1+d2<1. The formula follows by maximizing g/(g-d2) over g>=1-d1, not by assuming G1 and G2 independent. Lemma 5.

1. **A16-Q1.** Are both good-key events defined on exactly the same key-generation probability space?
2. **A16-Q2.** Does the entropy estimate concern a nonnegative per-key quantity?
3. **A16-Q3.** How much does conditioning on the extra rejection event inflate the earlier average estimate?
4. **A16-Q4.** Are d1 and d2 proved bounds, or unexplained numerical inputs?

<a id="a17"></a>

### A17: Turn a security label into a reduction contract

**Original operators:** [Z35](#op-z35), [O14](#op-o14), [O41](#op-o41), [K9](#op-k9).

**Mutated formula or interface:** Adv_CMA(A)<=Adv_NMA(B)+L(q_S,q_H,p,epsilon,delta,zeta_zk), with an explicit resource map A->B.

**Contract and proof scope:** Use the corrected CMA-to-NMA theorem only under its hypotheses. The additive loss alone is not a bound on Adv_NMA, and a NIST category is not a theorem about every specified gate/probability budget. External references S2 and S6.

1. **A17-Q1.** What exact hardness assumption bounds the remaining NMA adversary for the fixed ML-DSA parameter set?
2. **A17-Q2.** Is that hardness bound valid at the transformed time, query and memory costs of B?
3. **A17-Q3.** Does an idealized Dilithium theorem cover the standardized algorithms, encodings and rejection behavior being deployed?
4. **A17-Q4.** Can a contract checker keep the missing NMA term visibly unresolved even when L is tiny?

<a id="a18"></a>

### A18: Construct the actual joint decoder interface

**Original operators:** [K29](#op-k29), [K32](#op-k32), [K33](#op-k33), [K34](#op-k34), [P9](#op-p9), [P14](#op-p14), [O6](#op-o6), [O20](#op-o20).

**Mutated formula or interface:** Decode(D,x0,pi0,x1,pi1)->(w0,w1) or bottom, with R(x0,w0) and R(x1,w1) on the specified good database event.

**Contract and proof scope:** The pullback is a compatibility test on statement, roster, oracle and witness types. The decoder must be supplied and proved for the actual relation; an existence metaphor is insufficient. External reference S1.

1. **A18-Q1.** Which committed values does D contain and which deterministic algorithm reconstructs each complete witness?
2. **A18-Q2.** Are the two roots, public statements and witness encodings uniquely tied to the same roster and epoch?
3. **A18-Q3.** Can every accepted database-consistent proof on the good event be decoded, including correlated pairs?
4. **A18-Q4.** Does the proof apply to the current verifier, or only to a proposed commit-and-open replacement?

<a id="a19"></a>

### A19: Separate a reduction extractor from public conflict extraction

**Original operators:** [P17](#op-p17), [H38](#op-h38), [C20](#op-c20), [O13](#op-o13), [Z35](#op-z35).

**Mutated formula or interface:** Trace(pp,x0,cert0,x1,cert1)->culprit evidence must use only its declared public inputs; a reduction-only oracle database is not automatically available to Trace.

**Contract and proof scope:** This is a type-level obstruction, not a new impossibility theorem. Preserve the distinction between public conflict extraction and secret/simulation access used in a proof of knowledge.

1. **A19-Q1.** Does the requested conflict extractor have public certificates only, or is it allowed a trapdoor?
2. **A19-Q2.** Where in its actual input does it obtain the information that the compressed-oracle reduction reads from D?
3. **A19-Q3.** Is a proposed hidden-witness recovery step secretly asking for an unavailable sidecar or secret key?
4. **A19-Q4.** Can a concrete public algorithm return verifiable double-authorization evidence from two conflicting certificates?

<a id="a20"></a>

### A20: Make the fixed-hash bridge property-specific

**Original operators:** [I7](#op-i7), [I31](#op-i31), [I39](#op-i39), [I40](#op-i40), [I42](#op-i42), [K50](#op-k50), [R27](#op-r27), [R28](#op-r28), [Z38](#op-z38).

**Mutated formula or interface:** For fixed public H0 and independent ideal H, a one-query equality test at x0 distinguishes them with probability gap 1-2^(-h).

**Contract and proof scope:** This refutes a generic fixed-function-versus-independent-RO indistinguishability premise. It does not refute ideal-permutation indifferentiability with a simulator or a separately assumed game-specific hash property. Lemma 8; external reference S3.

1. **A20-Q1.** Which property does each reduction actually need: collision resistance, preimages, collapsing, or programmable oracle access?
2. **A20-Q2.** Is a random ideal permutation being silently replaced with the known Keccak permutation?
3. **A20-Q3.** Can a property-specific assumption and reduction cover the complete deployed hash interface and all its uses?
4. **A20-Q4.** Do empirical output tests or a larger digest merely leave that computational premise untouched?

<a id="a21"></a>

### A21: Track hash width separately from sponge capacity

**Original operators:** [S28](#op-s28), [W31](#op-w31), [W42](#op-w42), [W44](#op-w44), [R12](#op-r12), [R13](#op-r13), [Z34](#op-z34).

**Mutated formula or interface:** SHAKE256: output length is variable; capacity remains 512 bits and rate 1088 bits. Ideal-output bounds and ideal-permutation bounds are different contracts.

**Contract and proof scope:** A wider squeeze, transform basis or entropy label does not change the underlying permutation capacity. Use the deployed construction parameter record and the chosen theorem. External references S3 and S5.

1. **A21-Q1.** Does the chosen 720- or 832-bit challenge source actually have the ideal distribution required by the sampler lemma?
2. **A21-Q2.** What theorem charges every absorb/squeeze call and grants the same adversarial access as the implementation?
3. **A21-Q3.** If a published bound becomes uninformative, is that being reported as a proof gap rather than an attack?
4. **A21-Q4.** Would changing the sponge parameters change the protocol and its implementation compatibility obligations?

<a id="a22"></a>

### A22: Account for proof-reduction resource inflation

**Original operators:** [K20](#op-k20), [K47](#op-k47), [O9](#op-o9), [R33](#op-r33), [R34](#op-r34), [R35](#op-r35), [R41](#op-r41), [R42](#op-r42), [Z43](#op-z43).

**Mutated formula or interface:** If time(B)<=f(time(A)) and time(C)<=g(time(B)), compose to time(C)<=g(f(time(A))); compose success losses in the same order.

**Contract and proof scope:** Budget queries, gates, depth, memory and setup separately. A Q^2 simulation at Q=2^128 has scale 2^256 before constants, not scale 2^128. Lemma 7.

1. **A22-Q1.** Is a polynomial-time extractor being called concretely efficient without evaluating its polynomial at the target budget?
2. **A22-Q2.** Do the downstream signature or hash hardness assumptions cover the inflated resource vector?
3. **A22-Q3.** Are setup costs, cached advice or precomputation inside the target adversary budget?
4. **A22-Q4.** Can a tighter simulation reduce a concrete bottleneck without changing the admissible attack model?

<a id="a23"></a>

### A23: Make finite checks proof aids with explicit scope

**Original operators:** [O7](#op-o7), [O16](#op-o16), [O17](#op-o17), [O18](#op-o18), [O19](#op-o19), [O27](#op-o27), [O29](#op-o29), [O38](#op-o38), [O39](#op-o39), [O40](#op-o40), [O41](#op-o41), [O42](#op-o42).

**Mutated formula or interface:** Finite enumeration proves the enumerated statement. A general lemma needs a proof; a solver result needs a checkable certificate and the exact encoded domain.

**Contract and proof scope:** Keep arithmetic tests, finite-model proofs, literature theorems and unproved protocol assumptions as separate statuses. A green eligibility flag is not itself a cryptographic proof.

1. **A23-Q1.** Which quantified domain was exhausted, and which parameters remain symbolic?
2. **A23-Q2.** Can independent brute force check a closed-form counter without reusing its recurrence?
3. **A23-Q3.** Does a negative mutation such as swapping a sign, deleting a domain tag or replacing missing data by zero get rejected?
4. **A23-Q4.** Can each claimed closure be traced to a written lemma or an external theorem whose hypotheses are satisfied?

<a id="a24"></a>

### A24: Keep distributed authorization in the witness relation

**Original operators:** [L25](#op-l25), [L32](#op-l32), [L33](#op-l33), [L34](#op-l34), [O31](#op-o31), [O32](#op-o32), [Y15](#op-y15), [Y16](#op-y16), [Y49](#op-y49).

**Mutated formula or interface:** |S0 intersect S1|>=|S0|+|S1|-N; threshold t gives at least 2t-N common identities.

**Contract and proof scope:** This is only a set-counting lemma. The relation still needs distinct registered signer identities, actual valid signatures, canonical statements and message/epoch binding. Economic equilibria do not supply authorization.

1. **A24-Q1.** Does the extracted witness contain distinct roster-bound keys rather than a threshold-sized list with duplicates?
2. **A24-Q2.** Can the current relation demonstrate two different authorized messages in the same conflict domain?
3. **A24-Q3.** Which public evidence proves that a common signer actually signed both statements?
4. **A24-Q4.** Does a quorum intersection proof get incorrectly treated as proof that shares were collected through a secure distributed protocol?

<a id="a25"></a>

### A25: Use randomness extraction only where its seed premise holds

**Original operators:** [I2](#op-i2), [I34](#op-i34), [I7](#op-i7), [R7](#op-r7), [R27](#op-r27).

**Mutated formula or interface:** With an independent uniform seed selecting a two-universal family, output length must be below conditional min-entropy by an explicit security margin.

**Contract and proof scope:** External reference S4 supplies a quantum-side-information leftover-hash theorem. This is not a proof of Fiat-Shamir programmability or a public witness extractor, and an adversarially chosen transcript is not automatically a secret high-entropy source.

1. **A25-Q1.** Where does the independent seed come from, and when is it sampled relative to the source and adversary?
2. **A25-Q2.** What lower bound on H_min(X|E) is already proved before extraction?
3. **A25-Q3.** Can the precise theorem yield the allocated trace-distance error including smoothing and seed exposure?
4. **A25-Q4.** Does this operation solve a genuine secret-randomness requirement or is it being misapplied to publicly fixed challenges?

<a id="a26"></a>

### A26: Replace random-looking tests with finite guarantees

**Original operators:** [M41](#op-m41), [M46](#op-m46), [M47](#op-m47), [M48](#op-m48), [M49](#op-m49), [X35](#op-x35), [Y38](#op-y38), [Y39](#op-y39), [I47](#op-i47), [I48](#op-i48), [I49](#op-i49).

**Mutated formula or interface:** A finite sample can falsify a universal property, but observing zero failures is not evidence of a 2^-128 probability bound without a justified statistical model and sample size.

**Contract and proof scope:** Use simulation to find counterexamples and validate exact finite formulas. Do not equate compression ratios, empirical entropy, bootstrap intervals or learned attacks with a quantum hardness theorem.

1. **A26-Q1.** What failure modes can this experiment actually detect at its sample size?
2. **A26-Q2.** Can a constructed rare event fool all empirical tests while violating the target bound?
3. **A26-Q3.** Is the attack class being tested narrower than the QPT adversaries in the theorem?
4. **A26-Q4.** What symbolic invariant learned from a failed test can subsequently be proved for all parameters?

<a id="a27"></a>

### A27: Do not turn smoothing into a security assumption

**Original operators:** [F8](#op-f8), [F21](#op-f21), [F44](#op-f44), [F47](#op-f47), [F50](#op-f50), [X4](#op-x4), [W9](#op-w9), [W40](#op-w40).

**Mutated formula or interface:** A smoothing or dissipative operator must be replaced by a finite, physically admissible map and a proved inequality for the actual security event before it can contribute.

**Contract and proof scope:** Heat flow, fractional memory and geometric shrinkage are useful analytic analogies. Norm preservation, boundary conditions, rounding and discarded branches must be reconciled with the cryptographic game.

1. **A27-Q1.** What finite-dimensional state and actual protocol step correspond to the proposed differential operator?
2. **A27-Q2.** Does smoothing lower the adversary success probability or merely erase information needed by honest verification?
3. **A27-Q3.** Does a postselection normalization cancel the apparent amplitude shrinkage?
4. **A27-Q4.** Is any truncation of long memory accompanied by a rigorous tail bound and a counted computational cost?

<a id="a28"></a>

### A28: Replace the master operator by a compatibility record

**Original operators:** [Z50](#op-z50), [K29](#op-k29), [K32](#op-k32), [O13](#op-o13), [O38](#op-o38), [O41](#op-o41).

**Mutated formula or interface:** Contract=(game,relation,key_distribution,oracle_interface,adversary_resources,conclusion,evidence). Composition requires explicit matching or a proved adapter.

**Contract and proof scope:** The checker may establish arithmetic and refuse incompatible records; it cannot validate a cryptographic theorem merely because a string or boolean says proved. Missing evidence remains an open obligation.

1. **A28-Q1.** Do all component contracts use the same deployed relation, key distribution and oracle interfaces?
2. **A28-Q2.** Which exact adapters justify every change of model between consecutive components?
3. **A28-Q3.** Is there a concrete decoder and a concrete signature-hardness bound at the transformed resources?
4. **A28-Q4.** Can the final report distinguish closed elementary lemmas from the still-open QPT-128 theorem?

## Complete amended catalog

Read “source” fields as the original material under review. The project amendment and the typed mutation contract govern any use in the QPT-128 argument.

### Family L: Lattice and order

<a id="op-l1"></a>

#### L1. `⊓_θ` — θ-threshold meet

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** L × L × [0,1] → L

**Source definition.** x ⊓_θ y := sup{ z ≤ x ∧ y : ν(z) ≥ θ }, where ν is a valuation on L.

**Source property — not certified.** Idempotent and θ-monotone: increasing θ shrinks the result.

**Source use — context only.** Robust feature intersection in fuzzy ontologies — only commits to a shared concept when confidence exceeds θ.

**Amendment (FALSE_AS_STATED).** Do not assert idempotence on all inputs. On a complete lattice, totalize an empty supremum as bottom; idempotence at x requires that the supremum of admissible elements below x actually equals x. For example, x=1/4, nu(z)=z and theta=1/2 give bottom, not x.

**QPT-128 substitution.** Use only through [A01](#a01), with each contract and its four research questions.

**Eligibility question for L1.** Which exact event is being bounded, and are Q, h, leaf count and verifier calls from that same experiment? Identify the exact role of this operator in that derivation.

<a id="op-l2"></a>

#### L2. `⊔_θ` — θ-threshold join

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** L × L × [0,1] → L

**Source definition.** x ⊔_θ y := inf{ z ≥ x ∨ y : ν(z) ≤ 1 - θ }, dual to ⊓_θ.

**Source property — not certified.** Self-dual to ⊓_θ under lattice anti-isomorphism.

**Source use — context only.** Confidence-bounded set union in evidence aggregation.

**Amendment (DOMAIN_GAP).** An empty admissible infimum must be top in a complete lattice. State the valuation direction and admissibility assumptions before claiming an idempotent join.

**QPT-128 substitution.** Use only through [A01](#a01), with each contract and its four research questions.

**Eligibility question for L2.** At Q=2^128 and h=512, how small must the nonextractable challenge mass be after the hash term is reserved? Identify the exact role of this operator in that derivation.

<a id="op-l3"></a>

#### L3. `⤳` — residual implication

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** L × L → L (L a residuated lattice)

**Source definition.** (a ⤳ b) := sup{ x ∈ L : a ⊗ x ≤ b }.

**Source property — not certified.** Galois adjoint to ⊗: (a ⊗ x ≤ b) ⇔ (x ≤ a ⤳ b).

**Source use — context only.** Material implication in many-valued logic and proof-theoretic semantics.

**QPT-128 substitution.** Use only through [A01](#a01), with each contract and its four research questions.

**Eligibility question for L3.** Does a proposed improvement reduce an actual summand, or merely rename the threshold? Identify the exact role of this operator in that derivation.

<a id="op-l4"></a>

#### L4. `⤙` — left residual

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** L × L → L (non-commutative ⊗)

**Source definition.** (b ⤙ a) := sup{ x : x ⊗ a ≤ b }.

**Source property — not certified.** Distinct from ⤳ when ⊗ is non-commutative; both reduce in the commutative case.

**Source use — context only.** Type-checking in substructural / linear-logic-based programming languages.

**QPT-128 substitution.** Use only through [A01](#a01), with each contract and its four research questions.

**Eligibility question for L4.** Can the checker reject B0>=tau and a missing input instead of silently substituting zero? Identify the exact role of this operator in that derivation.

<a id="op-l5"></a>

#### L5. `⊟` — lattice difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L × L → L (Heyting algebra)

**Source definition.** x ⊟ y := inf{ z : x ≤ y ∨ z }.

**Source property — not certified.** Dual to Heyting implication; recovers set difference in 𝒫(X).

**Source use — context only.** Concept lattice subtraction in formal concept analysis.

**Amendment (DOMAIN_GAP).** Use a co-Heyting algebra with its co-residual, or prove that the displayed infimum is attained and satisfies its residuation law. A Heyting structure alone does not provide this dual operation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L5.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l6"></a>

#### L6. `¬_H` — Heyting negation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L → L

**Source definition.** ¬_H x := (x ⤳ ⊥).

**Source property — not certified.** Satisfies ¬¬¬x = ¬x but not in general ¬¬x = x.

**Source use — context only.** Intuitionistic negation in constructive proof assistants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L6.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l7"></a>

#### L7. `∂_↑` — upper boundary operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** 𝒫(P) → 𝒫(P)

**Source definition.** ∂_↑ S := { p ∈ S : ∀q > p, q ∉ S }.

**Source property — not certified.** Idempotent; fixed points are antichains in P.

**Source use — context only.** Pareto frontier extraction in multi-objective optimization.

**QPT-128 substitution.** Use only through [A03](#a03), with each contract and its four research questions.

**Eligibility question for L7.** Does searching a finite collection of attacks produce only lower bounds on attack success? Identify the exact role of this operator in that derivation.

<a id="op-l8"></a>

#### L8. `∂_↓` — lower boundary operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** 𝒫(P) → 𝒫(P)

**Source definition.** ∂_↓ S := { p ∈ S : ∀q < p, q ∉ S }.

**Source property — not certified.** Dual to ∂_↑ under order reversal.

**Source use — context only.** Minimal-element extraction in cost-monotone search.

**QPT-128 substitution.** Use only through [A03](#a03), with each contract and its four research questions.

**Eligibility question for L8.** Which candidate parameters minimize the worst proved error with all required resources charged? Identify the exact role of this operator in that derivation.

<a id="op-l9"></a>

#### L9. `⇈` — majorization sup

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Δ_n × Δ_n → Δ_n

**Source definition.** (p ⇈ q)_k := max(p^↓_k, q^↓_k), restored to a probability vector by renormalization.

**Source property — not certified.** Majorizes both inputs in the Hardy-Littlewood-Pólya order.

**Source use — context only.** Worst-case resource bounds in entanglement theory.

**Amendment (FALSE_AS_STATED).** Normalized coordinatewise maximum/minimum need not be a majorization join/meet. For p=(4/5,1/10,1/10), q=(3/5,2/5,0), they give (8/13,4/13,1/13) and (6/7,1/7,0), respectively; both claimed bounds fail at the first partial sum. For failure budgets keep unnormalized coordinate bounds and use event-wise union bounds.

**QPT-128 substitution.** Use only through [A02](#a02), with each contract and its four research questions.

**Eligibility question for L9.** Can extractor failure, binding failure, signature forgery and truncation failure be defined on one coupled execution? Identify the exact role of this operator in that derivation.

<a id="op-l10"></a>

#### L10. `⇊` — majorization inf

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Δ_n × Δ_n → Δ_n

**Source definition.** (p ⇊ q)_k := min(p^↓_k, q^↓_k), renormalized.

**Source property — not certified.** Common lower bound in the majorization order.

**Source use — context only.** Robust prior selection under partial information.

**Amendment (FALSE_AS_STATED).** Normalized coordinatewise maximum/minimum need not be a majorization join/meet. For p=(4/5,1/10,1/10), q=(3/5,2/5,0), they give (8/13,4/13,1/13) and (6/7,1/7,0), respectively; both claimed bounds fail at the first partial sum. For failure budgets keep unnormalized coordinate bounds and use event-wise union bounds.

**QPT-128 substitution.** Use only through [A02](#a02), with each contract and its four research questions.

**Eligibility question for L10.** Are two reported bounds alternatives for one event, or errors of separate components that must be added? Identify the exact role of this operator in that derivation.

<a id="op-l11"></a>

#### L11. `◇_κ` — κ-closure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 𝒫(X) → 𝒫(X)

**Source definition.** ◇_κ S := { x : |U ∩ S| ≥ κ for every neighborhood U of x }, κ a cardinal.

**Source property — not certified.** Monotone in κ; ◇_1 is topological closure.

**Source use — context only.** Density-based clustering with cardinality threshold.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L11.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l12"></a>

#### L12. `⬓` — core operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 𝒫(P) → 𝒫(P)

**Source definition.** ⬓ S := { p : ↑p ⊆ S }, the set of points whose entire up-set lies in S.

**Source property — not certified.** Right adjoint to the up-set functor.

**Source use — context only.** Safe-set computation in reachability analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L12.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l13"></a>

#### L13. `⌐` — Stone complement

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L → L (distributive lattice with 0)

**Source definition.** ⌐x := sup{ y : x ∧ y = 0 }.

**Source property — not certified.** Coincides with classical complement when L is Boolean.

**Source use — context only.** Disjoint-support detection in measure-theoretic decomposition.

**Amendment (DOMAIN_GAP).** Assume a pseudocomplemented distributive lattice; arbitrary distributive lattices with bottom need not contain the required greatest disjoint element.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L13.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l14"></a>

#### L14. `⨅_↗` — directed meet

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Dir(L) → L

**Source definition.** ⨅_↗ D := inf D for a downward-directed subset D ⊆ L.

**Source property — not certified.** Continuous with respect to the Scott topology on the dual.

**Source use — context only.** Greatest-lower-bound semantics for nondeterministic programs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L14.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l15"></a>

#### L15. `⨆_↗` — directed join

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Dir(L) → L

**Source definition.** ⨆_↗ D := sup D for an upward-directed D.

**Source property — not certified.** Scott-continuous; cornerstone of domain theory.

**Source use — context only.** Fixed-point semantics for recursive types.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L15.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l16"></a>

#### L16. `Φ_LFP` — least fixed point

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Mon(L,L) → L

**Source definition.** Φ_LFP(f) := inf{ x : f(x) ≤ x }, defined for monotone f.

**Source property — not certified.** Knaster-Tarski: exists for any monotone endo-map on a complete lattice.

**Source use — context only.** Reachable-state computation in model checking.

**QPT-128 substitution.** Use only through [A01](#a01), with each contract and its four research questions.

**Eligibility question for L16.** Can the checker reject B0>=tau and a missing input instead of silently substituting zero? Identify the exact role of this operator in that derivation.

<a id="op-l17"></a>

#### L17. `Φ_GFP` — greatest fixed point

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Mon(L,L) → L

**Source definition.** Φ_GFP(f) := sup{ x : x ≤ f(x) }.

**Source property — not certified.** Dual to Φ_LFP; gives coinductive definitions.

**Source use — context only.** Bisimulation equivalence in process algebra.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L17.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l18"></a>

#### L18. `⊕_L` — Galois join

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Gal(L,M) × Gal(L,M) → Gal(L,M)

**Source definition.** (F ⊕_L G)(x) := F(x) ∨_M G(x), with adjoint accordingly.

**Source property — not certified.** Galois connections form a complete lattice under pointwise order.

**Source use — context only.** Combining abstract interpretations in static program analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L18.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l19"></a>

#### L19. `⊠_L` — lattice tensor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L × M → L ⊗ M

**Source definition.** Universal bimorphism: (x ⊠_L y) ∨ (x' ⊠_L y') ≤ (x ∨ x') ⊠_L (y ∨ y') with separation in each argument.

**Source property — not certified.** Universal property: bimorphisms factor uniquely.

**Source use — context only.** Concurrent-resource composition in linear logic.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L19.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l20"></a>

#### L20. `⌊·⌋_L` — lattice floor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L → S ⊆ L

**Source definition.** ⌊x⌋_S := sup{ s ∈ S : s ≤ x }, S a sub-meet-semilattice.

**Source property — not certified.** Idempotent retraction onto S.

**Source use — context only.** Rounding to a discrete spec lattice in numerical types.

**Amendment (DOMAIN_GAP).** For a floor that belongs to S, require closure of S under the relevant joins, including the empty join when needed. Meet closure alone does not ensure this.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L20.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l21"></a>

#### L21. `⌈·⌉_L` — lattice ceiling

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L → S ⊆ L

**Source definition.** ⌈x⌉_S := inf{ s ∈ S : s ≥ x }, S a sub-join-semilattice.

**Source property — not certified.** Idempotent retraction onto S; dual to ⌊·⌋_L.

**Source use — context only.** Capacity allocation in tiered resource systems.

**Amendment (DOMAIN_GAP).** For a ceiling that belongs to S, require closure of S under the relevant meets, including the empty meet when needed. Join closure alone does not ensure this.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L21.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l22"></a>

#### L22. `⨡` — Birkhoff projection

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L → J(L)

**Source definition.** ⨡(x) := { j ∈ J(L) : j ≤ x }, J(L) the join-irreducibles.

**Source property — not certified.** Restores x via x = sup ⨡(x) when L is finite distributive.

**Source use — context only.** Atomic-decomposition of concepts in FCA.

**Amendment (TYPE_GAP).** The representation maps an element of a finite distributive lattice to a downset of its join-irreducibles: codomain Down(J(L)), not a single element of J(L).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L22.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l23"></a>

#### L23. `⤓` — down-set operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 𝒫(P) → 𝒪(P)

**Source definition.** ⤓ S := { p : ∃s ∈ S, p ≤ s }.

**Source property — not certified.** Idempotent; image is the lattice of down-sets 𝒪(P).

**Source use — context only.** History-closed event sets in causal structures.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L23.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l24"></a>

#### L24. `⤒` — up-set operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 𝒫(P) → 𝒰(P)

**Source definition.** ⤒ S := { p : ∃s ∈ S, p ≥ s }.

**Source property — not certified.** Idempotent; dual to ⤓.

**Source use — context only.** Future-closed obligation sets in deontic logic.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L24.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l25"></a>

#### L25. `⨹_α` — α-cut

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** [0,1]^X × [0,1] → 𝒫(X)

**Source definition.** ⨹_α f := { x : f(x) ≥ α }.

**Source property — not certified.** Anti-monotone in α; recovers f via f(x) = sup{ α : x ∈ ⨹_α f }.

**Source use — context only.** Defuzzification of fuzzy memberships.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for L25.** Does the extracted witness contain distinct roster-bound keys rather than a threshold-sized list with duplicates? Identify the exact role of this operator in that derivation.

<a id="op-l26"></a>

#### L26. `Λ_⊗` — quantale convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Q^X × Q^X → Q^X (Q a quantale)

**Source definition.** (f Λ_⊗ g)(x) := sup_{yz=x} f(y) ⊗ g(z).

**Source property — not certified.** Associative when Q is associative and the indexing monoid is.

**Source use — context only.** Weighted-automaton path-weight composition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L26.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l27"></a>

#### L27. `⨳` — lattice symmetric difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L × L → L (Boolean)

**Source definition.** x ⨳ y := (x ∧ ¬y) ∨ (¬x ∧ y).

**Source property — not certified.** Forms a Boolean group with ⨳ as addition.

**Source use — context only.** Belief revision via symmetric update.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L27.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l28"></a>

#### L28. `◁_<` — predecessor relation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** P → 𝒫(P)

**Source definition.** ◁_<(p) := { q : q < p ∧ ∄r, q < r < p }.

**Source property — not certified.** Captures the Hasse diagram covering relation.

**Source use — context only.** Graph extraction for partial-order visualization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L28.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l29"></a>

#### L29. `▷_<` — successor relation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** P → 𝒫(P)

**Source definition.** ▷_<(p) := { q : p < q ∧ ∄r, p < r < q }.

**Source property — not certified.** Dual to ◁_<.

**Source use — context only.** Next-step generation in event-structure unfolding.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L29.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l30"></a>

#### L30. `Cov` — covering number

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** P → ℕ ∪ {∞}

**Source definition.** Cov(p) := |▷_<(p)|.

**Source property — not certified.** Order-invariant; equals 1 in chains.

**Source use — context only.** Branching-factor analysis of search trees.

**Amendment (FALSE_AS_STATED).** A chain need not give cover count one. A maximum has no upper cover; a dense chain has no adjacent covers. State endpoint and discreteness assumptions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L30.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l31"></a>

#### L31. `Δ_lat` — lattice gap

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L × L → L

**Source definition.** Δ_lat(x,y) := (x ∨ y) ⊟ (x ∧ y).

**Source property — not certified.** Vanishes iff x = y; measures comparability defect.

**Source use — context only.** Inconsistency quantification in merged knowledge bases.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L31.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l32"></a>

#### L32. `μ_L` — Möbius function

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Int(P) → Z

**Source definition.** μ_L(p,p) = 1; μ_L(p,r) = -Σ_{p ≤ q < r} μ_L(p,q).

**Source property — not certified.** Möbius inversion: g(r) = Σ_{p ≤ r} f(p) ⇔ f(r) = Σ_{p ≤ r} μ_L(p,r) g(p).

**Source use — context only.** Inclusion-exclusion generalization on arbitrary posets.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for L32.** Does a quorum intersection proof get incorrectly treated as proof that shares were collected through a secure distributed protocol? Identify the exact role of this operator in that derivation.

<a id="op-l33"></a>

#### L33. `ζ_L` — zeta function

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Int(P) → Z

**Source definition.** ζ_L(p,q) := 1 if p ≤ q, else 0.

**Source property — not certified.** Convolution-inverse of μ_L in the incidence algebra.

**Source use — context only.** Generating-function methods on posets.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for L33.** Does the extracted witness contain distinct roster-bound keys rather than a threshold-sized list with duplicates? Identify the exact role of this operator in that derivation.

<a id="op-l34"></a>

#### L34. `⊛_inc` — incidence convolution

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** I(P) × I(P) → I(P)

**Source definition.** (f ⊛_inc g)(p,r) := Σ_{p ≤ q ≤ r} f(p,q) g(q,r).

**Source property — not certified.** Associative; makes the incidence algebra a ring.

**Source use — context only.** Counting saturated chains in finite posets.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for L34.** Can the current relation demonstrate two different authorized messages in the same conflict domain? Identify the exact role of this operator in that derivation.

<a id="op-l35"></a>

#### L35. `⨃_lex` — lexicographic join

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** P × Q → P × Q

**Source definition.** ((p,q) ≤_lex (p',q')) ⇔ (p < p') ∨ (p = p' ∧ q ≤ q').

**Source property — not certified.** Order-preserves projections; ill-founded if either factor is.

**Source use — context only.** Priority queues with secondary tie-breaking.

**Amendment (FALSE_AS_STATED).** The first lexicographic projection is monotone, but the second generally is not: (0,1)<lex(1,0).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L35.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l36"></a>

#### L36. `⨃_⊗` — product order

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** P × Q → P × Q

**Source definition.** ((p,q) ≤_⊗ (p',q')) ⇔ p ≤ p' ∧ q ≤ q'.

**Source property — not certified.** Coarsest order making both projections monotone.

**Source use — context only.** Pareto dominance in vector optimization.

**Amendment (FALSE_AS_STATED).** The componentwise order is the largest relation for which both projections are monotone. Equality is a smaller such relation; do not call the product order the coarsest without a different explicit convention.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L36.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l37"></a>

#### L37. `Λ_↑` — upward closure under f

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (P → P) × 𝒫(P) → 𝒫(P)

**Source definition.** Λ_↑(f, S) := ⤒(f(S)) ∪ S, iterated to fixpoint.

**Source property — not certified.** Fixed-point closure under f and ≤.

**Source use — context only.** Invariant generation in monotone abstract interpretation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L37.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l38"></a>

#### L38. `Λ_↓` — downward closure under f

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (P → P) × 𝒫(P) → 𝒫(P)

**Source definition.** Λ_↓(f, S) := ⤓(f(S)) ∪ S, iterated.

**Source property — not certified.** Dual to Λ_↑.

**Source use — context only.** Backwards reachability under monotone transitions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L38.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l39"></a>

#### L39. `κ_dim` — Krull dimension

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L → ℕ ∪ {∞}

**Source definition.** κ_dim(L) := sup of n such that a strict chain p_0 < p_1 < ... < p_n exists.

**Source property — not certified.** Lattice invariant under order-isomorphism.

**Source use — context only.** Dimension of varieties via their lattices of subvarieties.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L39.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l40"></a>

#### L40. `⨀_lat` — lattice trace

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** End(L) → L

**Source definition.** ⨀_lat(f) := inf{ x : f(x) ≤ x } ∨ sup{ x : f(x) ≥ x } when both exist.

**Source property — not certified.** Combines LFP and GFP; equals the unique fixed point when f is contractive.

**Source use — context only.** Equilibrium detection in monotone economic models.

**Amendment (REDUNDANT_OR_UNDEFINED).** For a monotone endomap of a complete lattice, lfp<=gfp, so their join is simply gfp. Contractivity requires a specified metric and constant.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L40.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l41"></a>

#### L41. `Π_p` — principal filter

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** P → 𝒫(P)

**Source definition.** Π_p(q) := ↑q = { r : r ≥ q }.

**Source property — not certified.** Anti-monotone in q under inclusion.

**Source use — context only.** Compatibility constraint generation in version solvers.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L41.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l42"></a>

#### L42. `∇_lat` — lattice difference quotient

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L^P → L^P (P chain)

**Source definition.** (∇_lat f)(p) := f(▷_<(p)) ⊟ f(p) when ▷_<(p) is a singleton.

**Source property — not certified.** Recovers discrete derivative when L = R.

**Source use — context only.** Marginal-value computation on ordered states.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L42.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l43"></a>

#### L43. `⨎` — antichain decomposition operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** 𝒫(P) → ℕ → 𝒫(P)

**Source definition.** ⨎_k(S) := the k-th antichain in Dilworth's decomposition of S into the minimum number of chains.

**Source property — not certified.** Number of antichains equals width(P).

**Source use — context only.** Optimal scheduling on partial-order tasks.

**Amendment (FALSE_AS_STATED).** Distinguish Dilworth (minimum chain partition size equals width) from Mirsky (minimum antichain partition size equals height) for finite posets.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L43.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l44"></a>

#### L44. `Wid` — width operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** P → ℕ ∪ {∞}

**Source definition.** Wid(P) := max size of an antichain in P.

**Source property — not certified.** Equals the minimum number of chains covering P (Dilworth's theorem).

**Source use — context only.** Parallelism bound in dependency-graph execution.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for L44.** Are the depth cap and the total gate cap both satisfied after the extractor is included? Identify the exact role of this operator in that derivation.

<a id="op-l45"></a>

#### L45. `Hgt` — height operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** P → ℕ ∪ {∞}

**Source definition.** Hgt(P) := max length of a chain.

**Source property — not certified.** Equals the minimum number of antichains covering P (Mirsky's theorem).

**Source use — context only.** Longest dependency-chain length in build systems.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for L45.** Which gates, oracle evaluations, uncomputations and output checks appear in the actual circuit DAG? Identify the exact role of this operator in that derivation.

<a id="op-l46"></a>

#### L46. `⨁_lat` — ordinal sum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Pos × Pos → Pos

**Source definition.** P ⨁_lat Q := disjoint union with all of P below all of Q.

**Source property — not certified.** Associative, not commutative; respects height additively.

**Source use — context only.** Phase-ordering composition in build pipelines.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L46.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l47"></a>

#### L47. `⊗_lat` — lattice tensor of posets

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Pos × Pos → Pos

**Source definition.** P ⊗_lat Q := P × Q with product order.

**Source property — not certified.** Bifunctorial; widths multiply.

**Source use — context only.** Joint state spaces in concurrent specifications.

**Amendment (FALSE_AS_STATED).** Widths do not multiply under general poset products: two two-element chains each have width one, whereas their product has width two. Use a direct width calculation or a proved bound.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for L47.** Does a dependency through a shared oracle prevent the proposed parallel schedule? Identify the exact role of this operator in that derivation.

<a id="op-l48"></a>

#### L48. `⨂_lin` — linear extension count

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Pos → ℕ

**Source definition.** ⨂_lin(P) := number of total orders extending ≤_P.

**Source property — not certified.** Equals dim(P)'s order polytope volume × n! (Stanley).

**Source use — context only.** Enumerating valid schedules consistent with constraints.

**Amendment (TYPE_GAP).** Use ambient dimension |P| for the usual order polytope volume formula, not the order dimension of the poset.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L48.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

<a id="op-l49"></a>

#### L49. `⩥_α` — α-strong Pareto

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** R^n × R^n → {0,1}

**Source definition.** (x ⩥_α y) ⇔ ∀i, x_i ≥ y_i + α(max_j x_j - min_j x_j).

**Source property — not certified.** Parameterized strict dominance; α = 0 recovers weak Pareto.

**Source use — context only.** ε-dominated archive pruning in evolutionary optimization.

**QPT-128 substitution.** Use only through [A03](#a03), with each contract and its four research questions.

**Eligibility question for L49.** Does the claimed extractor exist uniformly for all adversaries, or is a different uncomputable extractor selected after seeing each attack? Identify the exact role of this operator in that derivation.

<a id="op-l50"></a>

#### L50. `⨯_lat` — lattice quotient

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L × Cong(L) → L/θ

**Source definition.** L ⨯_lat θ := equivalence classes of θ with induced order.

**Source property — not certified.** Quotient preserves lattice operations iff θ is a congruence.

**Source use — context only.** Behavioral abstraction in equivalence-based model reduction.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for L50.** Can this order construction compare already proved probability/resource bounds without changing their event or reversing an inequality?

### Family T: Tropical and idempotent algebra

<a id="op-t1"></a>

#### T1. `⊕_min` — min-plus sum

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** R_min × R_min → R_min

**Source definition.** a ⊕_min b := min(a, b).

**Source property — not certified.** Idempotent: a ⊕_min a = a; identity +∞.

**Source use — context only.** Shortest-path edge-weight combination in graph algorithms.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for T1.** Which gates, oracle evaluations, uncomputations and output checks appear in the actual circuit DAG? Identify the exact role of this operator in that derivation.

<a id="op-t2"></a>

#### T2. `⊗_min` — min-plus product

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** R_min × R_min → R_min

**Source definition.** a ⊗_min b := a + b.

**Source property — not certified.** Commutative, associative, distributes over ⊕_min; identity 0.

**Source use — context only.** Concatenation cost in dynamic programming.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for T2.** When a branch is duplicated to reduce depth, how many processors and gates does that duplication add? Identify the exact role of this operator in that derivation.

<a id="op-t3"></a>

#### T3. `⊕_max` — max-plus sum

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** R_max × R_max → R_max

**Source definition.** a ⊕_max b := max(a, b).

**Source property — not certified.** Idempotent; identity -∞; dual to ⊕_min.

**Source use — context only.** Latest-completion-time computation in PERT scheduling.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for T3.** Does a dependency through a shared oracle prevent the proposed parallel schedule? Identify the exact role of this operator in that derivation.

<a id="op-t4"></a>

#### T4. `⊗_max` — max-plus product

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** R_max × R_max → R_max

**Source definition.** a ⊗_max b := a + b.

**Source property — not certified.** Same arithmetic as ⊗_min but used with ⊕_max.

**Source use — context only.** Earliest-firing-time recursion in timed event graphs.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for T4.** Are the depth cap and the total gate cap both satisfied after the extractor is included? Identify the exact role of this operator in that derivation.

<a id="op-t5"></a>

#### T5. `⊗̂_min` — min-plus matrix product

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** R_min^{n×k} × R_min^{k×m} → R_min^{n×m}

**Source definition.** (A ⊗̂_min B)_{ij} := min_k (A_{ik} + B_{kj}).

**Source property — not certified.** Associative; corresponds to path concatenation.

**Source use — context only.** All-pairs shortest paths via repeated squaring.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for T5.** Which gates, oracle evaluations, uncomputations and output checks appear in the actual circuit DAG? Identify the exact role of this operator in that derivation.

<a id="op-t6"></a>

#### T6. `⊕̂` — tropical determinant

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max^{n×n} → R_max

**Source definition.** tdet(A) := max_{σ ∈ S_n} Σ_i A_{i,σ(i)}.

**Source property — not certified.** Best assignment value; permanent and determinant coincide tropically.

**Source use — context only.** Optimal assignment in bipartite matching.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T6.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t7"></a>

#### T7. `λ_⊗` — tropical eigenvalue

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** R_max^{n×n} → R_max

**Source definition.** λ_⊗(A) := max over circuits C of (Σ_{(i,j)∈C} A_{ij}) / |C|.

**Source property — not certified.** Equals 1/n × max trace of A^⊗k for k = 1..n.

**Source use — context only.** Cycle-time analysis of timed Petri nets.

**Amendment (FALSE_AS_STATED).** For a finite max-plus matrix with cycles, maximum cycle mean equals max over 1<=k<=n of tr_max(A^k)/k. Division by n after taking the maximum is not equivalent; negative self-loop weights give a counterexample.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T7.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t8"></a>

#### T8. `v_⊗` — tropical eigenvector

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** R_max^{n×n} → R_max^n

**Source definition.** v_⊗(A) satisfies A ⊗̂ v = λ_⊗(A) ⊗ v.

**Source property — not certified.** Exists when A is irreducible; unique up to additive constant.

**Source use — context only.** Steady-state firing rates in max-plus linear systems.

**Amendment (FALSE_AS_STATED).** Irreducibility ensures a max-plus eigenvector exists, but does not by itself ensure uniqueness up to an additive constant. A=[[0,-1],[-1,0]] has eigenvalue zero and many such eigenvectors.

**QPT-128 substitution.** Use only through [A09](#a09), with each contract and its four research questions.

**Eligibility question for T8.** Is the purported spectral gap attached to a valid quantum channel or only to a classical diagnostic matrix? Identify the exact role of this operator in that derivation.

<a id="op-t9"></a>

#### T9. `⊘_min` — min-plus division

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_min × R_min → R_min

**Source definition.** a ⊘_min b := a - b.

**Source property — not certified.** Right inverse of ⊗_min; not defined when b = +∞.

**Source use — context only.** Relative-cost computation in shortest-path differences.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T9.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t10"></a>

#### T10. `⊗*` — tropical Kleene star

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_min^{n×n} → R_min^{n×n}

**Source definition.** A^⊗* := I ⊕ A ⊕ A^⊗2 ⊕ ... .

**Source property — not certified.** Converges iff A has no negative-weight cycles.

**Source use — context only.** Transitive shortest-path closure.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T10.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t11"></a>

#### T11. `◊_min` — min-plus convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_min^Z × R_min^Z → R_min^Z

**Source definition.** (f ◊_min g)(n) := inf_k (f(k) + g(n-k)).

**Source property — not certified.** Tropical analog of ordinary convolution; epi-graphical equivalent of Minkowski sum.

**Source use — context only.** Network calculus arrival-curve composition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T11.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t12"></a>

#### T12. `◊_max` — max-plus convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max^Z × R_max^Z → R_max^Z

**Source definition.** (f ◊_max g)(n) := sup_k (f(k) + g(n-k)).

**Source property — not certified.** Sup-convolution; dual to ◊_min.

**Source use — context only.** Bottleneck capacity in pipeline systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T12.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t13"></a>

#### T13. `⨁_seg` — tropical segment join

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** PL(R) × PL(R) → PL(R)

**Source definition.** (f ⨁_seg g)(x) := min(f(x), g(x)) for piecewise-linear f, g.

**Source property — not certified.** Preserves piecewise linearity; vertex count is at most |f| + |g|.

**Source use — context only.** Lower-envelope construction for parametric optimization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T13.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t14"></a>

#### T14. `Δ_⊗` — tropical Newton polytope

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_min[x_1,...,x_n] → 𝒞(R^n)

**Source definition.** Δ_⊗(p) := convex hull of exponent vectors of monomials appearing in p with finite coefficient.

**Source property — not certified.** Tropical hypersurface = boundary of subdivision dual to Δ_⊗.

**Source use — context only.** Combinatorial structure of polynomial systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T14.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t15"></a>

#### T15. `Trop` — tropicalization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** {C[t]-Laurent polys} → R_max-polys

**Source definition.** Trop(Σ c_α t^α x^α)(v) := max_α (deg c_α + ⟨α, v⟩).

**Source property — not certified.** Sends algebraic varieties to piecewise-linear tropical varieties.

**Source use — context only.** Limit-shape analysis of algebraic curves.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T15.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t16"></a>

#### T16. `Var_⊗` — tropical variety operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max-poly → 𝒫(R^n)

**Source definition.** Var_⊗(p) := { v : the max in p(v) is attained at least twice }.

**Source property — not certified.** Always a polyhedral complex of pure codimension 1.

**Source use — context only.** Phylogenetic-tree space coordinates.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T16.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t17"></a>

#### T17. `⊞_min` — min-plus tensor product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_min^m × R_min^n → R_min^{m×n}

**Source definition.** (u ⊞_min v)_{ij} := u_i + v_j.

**Source property — not certified.** Rank-1 tropical tensor; building block of low-rank tropical decomposition.

**Source use — context only.** Separable cost models in operations research.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T17.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t18"></a>

#### T18. `⌖_⊗` — tropical rank

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** R_min^{m×n} → ℕ

**Source definition.** trank(A) := min k such that A = ⊕̂_{i=1}^k u^{(i)} ⊞_min v^{(i)}.

**Source property — not certified.** NP-hard to compute; lower bound by tropical singular values.

**Source use — context only.** Complexity measure of scheduling tableaus.

**Amendment (DEFINITION_MISMATCH).** The minimum inner dimension in a tropical matrix factorization is a factor rank. Do not equate it with every notion called tropical rank, or import ordinary singular-value statements.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T18.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t19"></a>

#### T19. `σ_⊗` — tropical singular values

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_min^{m×n} → R_min^{min(m,n)}

**Source definition.** σ_k(A) := max over k×k submatrices B of tdet(B)/k.

**Source property — not certified.** Generalizes singular values; weakly decreasing in k.

**Source use — context only.** Robustness margin in optimization-based control.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T19.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t20"></a>

#### T20. `℘_⊗` — polytrope hull

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** R^n → 𝒫(R^n)

**Source definition.** ℘_⊗(v) := { u : u_i - u_j ≤ v_i - v_j ∀i,j }.

**Source property — not certified.** Tropically convex; intersection of half-spaces with slope ±1.

**Source use — context only.** Feasible-region geometry in min-plus linear systems.

**Amendment (DEFINITION_MISMATCH).** Constraints u_i-u_j=v_i-v_j for all ordered pairs force u-v to be constant. This is a translated diagonal line, not a general polytrope hull.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T20.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t21"></a>

#### T21. `Conv_⊗` — tropical convex hull

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 𝒫(R^n) → 𝒫(R^n)

**Source definition.** Conv_⊗(S) := { ⊕_i (λ_i ⊗ s_i) : s_i ∈ S, λ_i ∈ R_max }.

**Source property — not certified.** Idempotent; tropically convex sets are unions of polytropes.

**Source use — context only.** Phylogenetic consensus region.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T21.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t22"></a>

#### T22. `ρ_⊗` — tropical spectral radius

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max^{n×n} → R_max

**Source definition.** ρ_⊗(A) := lim_k (1/k) max_{ij} (A^⊗k)_{ij}.

**Source property — not certified.** Equals λ_⊗(A); Karp's mean-cycle formula.

**Source use — context only.** Throughput rate in cyclic schedules.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T22.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t23"></a>

#### T23. `⨯_perm` — tropical permanent

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max^{n×n} → R_max

**Source definition.** tperm(A) := max_σ Σ A_{i,σ(i)}.

**Source property — not certified.** Coincides with tropical determinant; both maximize over permutations.

**Source use — context only.** Optimal-permutation cost in linear assignment.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T23.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t24"></a>

#### T24. `⨃_subharm` — subharmonic envelope

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R^X → R^X

**Source definition.** ⨃_subharm(f)(x) := sup over tropical-affine functions ℓ ≤ f of ℓ(x).

**Source property — not certified.** Idempotent; coincides with tropical-concave hull.

**Source use — context only.** Lower-bound envelopes in piecewise-linear approximation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T24.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t25"></a>

#### T25. `⨃_superharm` — superharmonic envelope

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R^X → R^X

**Source definition.** ⨃_superharm(f)(x) := inf over tropical-affine ℓ ≥ f of ℓ(x).

**Source property — not certified.** Dual to ⨃_subharm; equals the concave-up hull.

**Source use — context only.** Upper-bound envelopes for branch-and-bound.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T25.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t26"></a>

#### T26. `⌐_⊗` — tropical negation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** R_max → R_min

**Source definition.** ⌐_⊗ a := -a, switching between max-plus and min-plus.

**Source property — not certified.** Anti-isomorphism of semirings.

**Source use — context only.** Primal-dual conversion in LP/min-plus duality.

**Amendment (DIRECTION_ERROR).** Negation maps max to min and preserves addition. It is a semiring isomorphism between those semirings and reverses the ordinary order; distinguish the two statements.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T26.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t27"></a>

#### T27. `⨉_⊗` — Legendre-Fenchel transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R^R^n → R^R^n

**Source definition.** f*(p) := sup_x (⟨p,x⟩ - f(x)).

**Source property — not certified.** Tropical Fourier transform; ⨉_⊗ ∘ ⨉_⊗ recovers lsc convex hull.

**Source use — context only.** Duality in convex optimization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T27.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t28"></a>

#### T28. `⊞_inf` — infimal convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R^R^n × R^R^n → R^R^n

**Source definition.** (f ⊞_inf g)(x) := inf_y (f(y) + g(x-y)).

**Source property — not certified.** Continuous analog of ◊_min.

**Source use — context only.** Risk pooling and proximal-operator composition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T28.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t29"></a>

#### T29. `Prox_f` — proximal operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** R^R^n × R_+ → R^n

**Source definition.** Prox_f(λ, x) := argmin_y (f(y) + (1/2λ) ‖y-x‖²).

**Source property — not certified.** Resolvent of subdifferential ∂f.

**Source use — context only.** Splitting methods in non-smooth optimization.

**Amendment (DOMAIN_GAP).** Specify the evaluation point x, lambda>0 and a proper lower-semicontinuous convex function before using the single-valued proximal map or differentiable Moreau envelope.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T29.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t30"></a>

#### T30. `Mor_f` — Moreau envelope

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** R^R^n × R_+ → R^R^n

**Source definition.** M_λ f(x) := inf_y (f(y) + (1/2λ) ‖y-x‖²).

**Source property — not certified.** Smooth lower approximant of f; recovers f as λ → 0.

**Source use — context only.** Smoothing non-smooth objectives for gradient methods.

**Amendment (DOMAIN_GAP).** Specify the evaluation point x, lambda>0 and a proper lower-semicontinuous convex function before using the single-valued proximal map or differentiable Moreau envelope.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T30.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t31"></a>

#### T31. `conv*` — biconjugate

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R^R^n → R^R^n

**Source definition.** f** := (f*)*.

**Source property — not certified.** Idempotent; gives the closed convex hull of f.

**Source use — context only.** Convex relaxation in non-convex optimization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T31.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t32"></a>

#### T32. `⨁_pw` — pointwise tropical sum

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** (X → R_min)² → (X → R_min)

**Source definition.** (f ⨁_pw g)(x) := min(f(x), g(x)).

**Source property — not certified.** Idempotent; makes R_min^X a tropical semimodule.

**Source use — context only.** Pessimistic-bound combination across scenarios.

**QPT-128 substitution.** Use only through [A02](#a02), with each contract and its four research questions.

**Eligibility question for T32.** Does the total conditional bound stay below the chosen constant-success threshold without assuming independent failures? Identify the exact role of this operator in that derivation.

<a id="op-t33"></a>

#### T33. `⊙_scal` — tropical scalar action

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max × (X → R_max) → (X → R_max)

**Source definition.** (λ ⊙ f)(x) := λ + f(x).

**Source property — not certified.** R_max acts on R_max^X by translation.

**Source use — context only.** Cost shifting in parametric LP.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T33.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t34"></a>

#### T34. `⨅_trop` — tropical infimum operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (X → R_min) → R_min

**Source definition.** ⨅_trop f := inf_{x ∈ X} f(x).

**Source property — not certified.** Semiring trace of the identity tropical kernel.

**Source use — context only.** Global optimum extraction.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T34.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t35"></a>

#### T35. `⊗̃` — tropical Hadamard product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_min^n × R_min^n → R_min^n

**Source definition.** (u ⊗̃ v)_i := u_i + v_i.

**Source property — not certified.** Entry-wise tropical product.

**Source use — context only.** Independent-cost combination across resources.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T35.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t36"></a>

#### T36. `⊖_inv` — tropical inverse

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (R_max \ {-∞}) → R_max

**Source definition.** ⊖_inv a := -a.

**Source property — not certified.** Group inverse in (R, +) lifted to (R_max, ⊗_max).

**Source use — context only.** Backwards-pass weights in min-plus dynamic programming.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T36.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t37"></a>

#### T37. `Schur_⊗` — tropical Schur complement

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** R_min^{(n+m)×(n+m)} → R_min^{n×n}

**Source definition.** Schur_⊗(A) := A_11 ⊕̂ A_12 ⊗̂ A_22^⊗* ⊗̂ A_21 (where defined).

**Source property — not certified.** Reduces dimension while preserving shortest-path distances.

**Source use — context only.** Hub-routing simplification in shortest-path networks.

**QPT-128 substitution.** Use only through [A04](#a04), with each contract and its four research questions.

**Eligibility question for T37.** Which gates, oracle evaluations, uncomputations and output checks appear in the actual circuit DAG? Identify the exact role of this operator in that derivation.

<a id="op-t38"></a>

#### T38. `res_⊗` — tropical resultant

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max-poly × R_max-poly → R_max

**Source definition.** tres(p, q) := min over common roots ξ of multiplicities-weighted sum.

**Source property — not certified.** Vanishes (= -∞) iff p, q share a tropical root.

**Source use — context only.** Elimination in tropical polynomial systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T38.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t39"></a>

#### T39. `⨹_⊗` — tropical Hahn-Banach extension

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sub-semimodule × R_max → R_max-linear

**Source definition.** ⨹_⊗(φ, S) := max-plus linear extension of φ from S to the ambient module.

**Source property — not certified.** Existence holds; uniqueness fails generically.

**Source use — context only.** Sub-additive cost extension across coalition structures.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T39.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t40"></a>

#### T40. `ν_⊗` — tropical valuation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C{{t}} → R ∪ {∞}

**Source definition.** ν_⊗(Σ c_α t^α) := min{ α : c_α ≠ 0 }.

**Source property — not certified.** Non-archimedean valuation on Puiseux series.

**Source use — context only.** Asymptotic analysis of perturbation expansions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T40.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t41"></a>

#### T41. `Ber_⊗` — tropical Bernoulli measure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R^N → Δ(R_max)

**Source definition.** Ber_⊗(x)({a}) := exp(-x_a) / Σ_b exp(-x_b), as inverse-temperature limit.

**Source property — not certified.** Recovers ⊕_min as the zero-temperature limit.

**Source use — context only.** Softmin smoothing in differentiable shortest paths.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T41.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t42"></a>

#### T42. `Logsumexp_β` — β-softmin

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** R^n × R_+ → R

**Source definition.** lse_β(x) := -(1/β) log Σ exp(-β x_i).

**Source property — not certified.** Converges to min_i x_i as β → ∞; convex and smooth for finite β.

**Source use — context only.** Differentiable approximation of tropical operations.

**Amendment (FALSE_AS_STATED).** For beta>0, -(1/beta) log(sum_i exp(-beta*x_i)) is concave, not convex. Log-sum-exp without the outer negative sign is convex.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T42.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t43"></a>

#### T43. `μ_circ` — max-mean cycle

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max^{n×n} → R_max

**Source definition.** μ_circ(A) := max over directed cycles C of (sum weights)/|C|.

**Source property — not certified.** Karp's algorithm computes in O(n |E|).

**Source use — context only.** Critical-cycle identification in dataflow graphs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T43.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t44"></a>

#### T44. `π_⊗` — tropical projection onto polytrope

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R^n × Polytrope → R^n

**Source definition.** π_⊗(v, P) := tropical nearest point to v in P.

**Source property — not certified.** Tropically linear in v on each cell.

**Source use — context only.** Constraint enforcement in tropical optimization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T44.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t45"></a>

#### T45. `Tdiv` — tropical division

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max × R_max → R_max

**Source definition.** Tdiv(a, b) := a - b (when b ≠ -∞).

**Source property — not certified.** Group inverse against ⊗.

**Source use — context only.** Normalization to canonical eigenvector representatives.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T45.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t46"></a>

#### T46. `⊗^∞` — infinite tropical power

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_min^{n×n} → R_min^{n×n}

**Source definition.** A^⊗∞ := lim_k A^⊗k / k = ρ_⊗(A) · J (after centering, J the all-ones matrix).

**Source property — not certified.** Reveals the cycle-time and limit behavior.

**Source use — context only.** Steady-state analysis of synchronous-clocked circuits.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T46.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t47"></a>

#### T47. `crit_⊗` — critical graph

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R_max^{n×n} → DiGraph

**Source definition.** crit_⊗(A) := nodes and arcs on cycles achieving λ_⊗(A).

**Source property — not certified.** Subgraph of A's adjacency graph; controls eigenspace structure.

**Source use — context only.** Bottleneck identification in throughput-limited systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T47.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t48"></a>

#### T48. `Asymp_⊗` — tropical asymptotic equivalence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** {seqs in R} → equivalence classes

**Source definition.** (x_k ~ y_k) ⇔ lim (x_k - y_k)/k = 0 tropically.

**Source property — not certified.** Coarser than ordinary asymptotic; captures linear-growth-rate equality.

**Source use — context only.** Long-run-average comparison of cost trajectories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T48.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t49"></a>

#### T49. `⨃_norm` — tropical normalization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** R^n → R^n / R·(1,...,1)

**Source definition.** ⨃_norm(v) := v - (min_i v_i) · (1,...,1) (for min-plus).

**Source property — not certified.** Projects to the tropical projective torus.

**Source use — context only.** Canonicalization of cost vectors up to global shift.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T49.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

<a id="op-t50"></a>

#### T50. `⊕_W` — Wasserstein tropical sum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R_max) × Δ(R_max) → Δ(R_max)

**Source definition.** (μ ⊕_W ν) := distribution of min(X, Y) for independent X ~ μ, Y ~ ν.

**Source property — not certified.** CDF satisfies F_{μ⊕_Wν}(t) = 1 - (1 - F_μ(t))(1 - F_ν(t)).

**Source use — context only.** Reliability of parallel-redundant systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for T50.** Can this tropical operation be interpreted on a finite, costed circuit or reduction graph, with work and depth kept distinct?

### Family F: Fractional calculus

<a id="op-f1"></a>

#### F1. `I^α_RL` — Riemann-Liouville integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L^1[a,b] × C → C[a,b], Re α > 0

**Source definition.** (I^α_a f)(x) := (1/Γ(α)) ∫_a^x (x-t)^{α-1} f(t) dt.

**Source property — not certified.** Semigroup: I^α I^β = I^{α+β}.

**Source use — context only.** Memory kernels in viscoelastic materials.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F1.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f2"></a>

#### F2. `D^α_RL` — Riemann-Liouville derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** AC^n[a,b] × C → distributions

**Source definition.** D^α_a f := (d/dx)^n I^{n-α}_a f, n = ⌈Re α⌉.

**Source property — not certified.** Reduces to ordinary derivative at integer α; non-zero on constants.

**Source use — context only.** Anomalous diffusion equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F2.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f3"></a>

#### F3. `D^α_C` — Caputo derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** AC^n[a,b] × C → C[a,b]

**Source definition.** D^α_C f := I^{n-α}_a (f^(n)).

**Source property — not certified.** Vanishes on constants; suits initial-value problems.

**Source use — context only.** Fractional-order control systems with physical initial conditions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F3.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f4"></a>

#### F4. `D^α_GL` — Grünwald-Letnikov derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C[a,b] × C → C

**Source definition.** D^α_GL f(x) := lim_{h→0} h^{-α} Σ_{k=0}^∞ (-1)^k C(α, k) f(x - kh).

**Source property — not certified.** Equivalent to D^α_RL for sufficiently regular f.

**Source use — context only.** Numerical schemes for fractional ODEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F4.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f5"></a>

#### F5. `D^α_M` — Marchaud derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^α(R) → C(R)

**Source definition.** D^α_M f(x) := (α/Γ(1-α)) ∫_0^∞ (f(x) - f(x-t)) / t^{1+α} dt.

**Source property — not certified.** Equals D^α_RL on the line; better suited to unbounded domains.

**Source use — context only.** Lévy-flight process generators.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F5.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f6"></a>

#### F6. `D^α_W` — Weyl derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Periodic L^1 × C → distributions

**Source definition.** D^α_W f := ((d/dx) Fourier-multiplier (in)^α) applied to f.

**Source property — not certified.** Acts diagonally in Fourier basis: e^{inx} ↦ (in)^α e^{inx}.

**Source use — context only.** Periodic-signal smoothness analysis.

**Amendment (FORMULA_ERROR).** For a periodic Fourier multiplier derivative, define D^alpha f=sum_n (i*n)^alpha*fhat(n)*exp(i*n*x), with a branch convention and a suitable Sobolev domain. Do not apply one extra ordinary derivative to this expression.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F6.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f7"></a>

#### F7. `D^α_F` — Fourier fractional derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** S(R^n) × C → S'(R^n)

**Source definition.** D^α_F f := F^{-1}((iξ)^α F(f)).

**Source property — not certified.** Diagonalized by Fourier transform; defines fractional Laplacians.

**Source use — context only.** Fractional Sobolev spaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F7.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f8"></a>

#### F8. `(-Δ)^{s}` — fractional Laplacian

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** S(R^n) × (0,1) → S'(R^n)

**Source definition.** (-Δ)^s f(x) := C_{n,s} P.V. ∫ (f(x) - f(y)) / |x-y|^{n+2s} dy.

**Source property — not certified.** Generator of 2s-stable symmetric Lévy process.

**Source use — context only.** Non-local PDEs in image processing.

**Amendment (SIGN_ERROR).** The symmetric stable Markov semigroup has generator -(-Delta)^(alpha/2), with a negative sign, for 0<alpha<=2.

**QPT-128 substitution.** Use only through [A27](#a27), with each contract and its four research questions.

**Eligibility question for F8.** Is any truncation of long memory accompanied by a rigorous tail bound and a counted computational cost? Identify the exact role of this operator in that derivation.

<a id="op-f9"></a>

#### F9. `Hp_s` — Hadamard fractional integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** {f : [a,b] → R, a > 0} × C → C

**Source definition.** Hp_s f(x) := (1/Γ(s)) ∫_a^x (log(x/t))^{s-1} f(t) dt/t.

**Source property — not certified.** Suited to functions with logarithmic growth.

**Source use — context only.** Models on (0, ∞) with scale-invariant phenomena.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F9.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f10"></a>

#### F10. `Hd_s` — Hadamard fractional derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** AC_δ^n × C → distributions

**Source definition.** Hd_s f := (x d/dx)^n Hp_{n-s} f.

**Source property — not certified.** Caputo-like Hadamard variant zeros constants.

**Source use — context only.** Time-warped processes in financial mathematics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F10.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f11"></a>

#### F11. `E_α` — Mittag-Leffler operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B(H) × C → B(H)

**Source definition.** E_α(A) := Σ_{k=0}^∞ A^k / Γ(αk + 1).

**Source property — not certified.** Solves D^α_C u = Au; reduces to exp when α = 1.

**Source use — context only.** Solution operators of fractional evolution equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F11.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f12"></a>

#### F12. `E_{α,β}` — two-parameter Mittag-Leffler

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B(H) × C × C → B(H)

**Source definition.** E_{α,β}(A) := Σ A^k / Γ(αk + β).

**Source property — not certified.** Generalizes resolvents and Bessel-type functions.

**Source use — context only.** Asymptotic relaxation in fractional Maxwell models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F12.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f13"></a>

#### F13. `I^α_K` — Erdélyi-Kober integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L^1(R_+) × C × C → C

**Source definition.** I^{α,η}_K f(x) := (x^{-α-η}/Γ(α)) ∫_0^x (x-t)^{α-1} t^η f(t) dt.

**Source property — not certified.** Includes Riemann-Liouville at η = 0.

**Source use — context only.** Singular integral equations in mathematical physics.

**Amendment (FALSE_AS_STATED).** At eta=0 the displayed prefactor still gives x^(-alpha) times the Riemann-Liouville integral, not that integral itself. Either retain the Erdelyi-Kober normalization or remove the claimed equality.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F13.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f14"></a>

#### F14. `I^α_log` — logarithmic fractional integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C(0,1) × C → C

**Source definition.** I^α_log f(x) := (1/Γ(α)) ∫_0^x (log(x/t))^{α-1} f(t) dt/t.

**Source property — not certified.** Same as Hadamard integral on (0,1).

**Source use — context only.** Multiplicative-calculus models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F14.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f15"></a>

#### F15. `D^{α,β}` — Hilfer derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → with parameters 0 ≤ β ≤ 1

**Source definition.** D^{α,β} f := I^{β(1-α)} D^1 I^{(1-β)(1-α)} f.

**Source property — not certified.** Interpolates between Riemann-Liouville (β=0) and Caputo (β=1).

**Source use — context only.** Unified initial-condition treatment.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F15.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f16"></a>

#### F16. `D^α_psi` — ψ-fractional derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × ψ ∈ C^1↑ → operator

**Source definition.** D^α_ψ f := (1/Γ(n-α)) (1/ψ'(x) d/dx)^n ∫_a^x ψ'(t)(ψ(x)-ψ(t))^{n-α-1} f(t) dt.

**Source property — not certified.** Unifies many fractional derivatives via choice of ψ.

**Source use — context only.** Models on warped time/space coordinates.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F16.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f17"></a>

#### F17. `D^α_var` — variable-order derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^n[a,b] × C^0(R_+) → C

**Source definition.** D^{α(x)} f := pointwise application of D^{α(x_0)} at each x_0.

**Source property — not certified.** Order itself depends on space/time.

**Source use — context only.** Materials with spatially varying memory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F17.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f18"></a>

#### F18. `D^α_dist` — distributed-order derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × measure → distributions

**Source definition.** D^μ f := ∫ D^α f dμ(α).

**Source property — not certified.** Superposition of fractional derivatives by a measure μ.

**Source use — context only.** Multi-scale relaxation in glassy materials.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F18.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f19"></a>

#### F19. `I^α_Lio` — Liouville integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L^1(R) → L^1(R)

**Source definition.** I^α_L f(x) := (1/Γ(α)) ∫_{-∞}^x (x-t)^{α-1} f(t) dt.

**Source property — not certified.** Riemann-Liouville with a = -∞; suited to bilateral processes.

**Source use — context only.** Causal-system response on the line.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F19.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f20"></a>

#### F20. `D^α_pde` — fractional PDE generator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Suitable function space → space

**Source definition.** L_α f := -(-Δ)^α f + V f for V a potential.

**Source property — not certified.** Generator of subordinated diffusion semigroups.

**Source use — context only.** Anomalous-diffusion modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F20.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f21"></a>

#### F21. `J^α_*` — Caputo-Fabrizio integral

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** L^1[a,b] × (0,1) → C

**Source definition.** J^α_{CF} f(x) := (1-α)/(M(α)) f(x) + α/(M(α)) ∫_a^x f(t) dt.

**Source property — not certified.** Non-singular exponential kernel; finite memory.

**Source use — context only.** Heat conduction with finite propagation speed.

**Amendment (FALSE_AS_STATED).** A formula containing a nonzero multiple of f does not generally map arbitrary L1 inputs into continuous functions. Exponential decay is not finite memory; specify a truncation and its error separately.

**QPT-128 substitution.** Use only through [A27](#a27), with each contract and its four research questions.

**Eligibility question for F21.** What finite-dimensional state and actual protocol step correspond to the proposed differential operator? Identify the exact role of this operator in that derivation.

<a id="op-f22"></a>

#### F22. `D^α_CF` — Caputo-Fabrizio derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** AC[a,b] × (0,1) → C

**Source definition.** D^α_{CF} f(x) := M(α)/(1-α) ∫_a^x exp(-α(x-t)/(1-α)) f'(t) dt.

**Source property — not certified.** Exponential, non-singular kernel.

**Source use — context only.** Memory effects without singular weights.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F22.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f23"></a>

#### F23. `D^α_AB` — Atangana-Baleanu derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** D^α_{AB} f := B(α)/(1-α) ∫_a^x E_α(-α(x-t)^α/(1-α)) f'(t) dt.

**Source property — not certified.** Mittag-Leffler non-singular kernel.

**Source use — context only.** Crossover dynamics in epidemiological models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F23.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f24"></a>

#### F24. `⊛_FC` — fractional convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L^1(R)² × C → L^1(R)

**Source definition.** (f ⊛_FC g)_α := I^α_RL(f * g).

**Source property — not certified.** Combines convolution with fractional smoothing.

**Source use — context only.** Long-memory filter design.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F24.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f25"></a>

#### F25. `(-Δ)^α_{spec}` — spectral fractional Laplacian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Eigenbasis of Δ on bounded Ω → space

**Source definition.** (-Δ)^α_{spec} (Σ c_n φ_n) := Σ λ_n^α c_n φ_n.

**Source property — not certified.** Differs from integral fractional Laplacian on bounded domains.

**Source use — context only.** Heat-kernel methods on graphs and manifolds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F25.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f26"></a>

#### F26. `D^α_loc` — local fractional derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** D^α_loc f(x_0) := lim_{x → x_0} (f(x) - f(x_0)) / (x - x_0)^α.

**Source property — not certified.** Probes Hölder regularity α; zero on smooth functions when α < 1.

**Source use — context only.** Local roughness measurement in fractal signals.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F26.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f27"></a>

#### F27. `Hd_K` — K-fractional derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** _K D^α f := (1/Γ_K(n-α)) (d/dx)^n ∫_a^x (x-t)^{n-α/K - 1} f(t) dt / K.

**Source property — not certified.** Reduces to RL when K = 1.

**Source use — context only.** k-parameter generalizations of fractional integrals.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F27.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f28"></a>

#### F28. `I^α_2D` — 2D Riesz potential

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sufficient L^p(R^n) × (0,n) → L^q(R^n)

**Source definition.** I^α f(x) := γ_{n,α} ∫ f(y) / |x-y|^{n-α} dy.

**Source property — not certified.** Inverts (-Δ)^{α/2}; Hardy-Littlewood-Sobolev bounds.

**Source use — context only.** Newtonian-potential generalization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F28.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f29"></a>

#### F29. `D^α_Marc` — Marchaud-type bilateral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → ×

**Source definition.** D^α_{Marc, ±} f := α/Γ(1-α) ∫_0^∞ (f(x) - f(x ∓ t))/t^{1+α} dt.

**Source property — not certified.** Captures one-sided long-range memory.

**Source use — context only.** Backward-vs-forward asymmetry in causality models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F29.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f30"></a>

#### F30. `D^α_seq` — sequential fractional

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → × given multi-index

**Source definition.** D^{α_1, ..., α_k} f := D^{α_k} ... D^{α_1} f.

**Source property — not certified.** Non-commutative in general: D^α D^β ≠ D^{α+β}.

**Source use — context only.** Multi-stage fractional-order control.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F30.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f31"></a>

#### F31. `L_α^FC` — fractional Laplace transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × s ∈ C → ×

**Source definition.** L_α[f](s) := ∫_0^∞ E_α(-s t^α) f(t) t^{α-1} dt.

**Source property — not certified.** Adapted to Mittag-Leffler kernels.

**Source use — context only.** Solving fractional differential equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F31.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f32"></a>

#### F32. `S_α` — Sonine-pair integration

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × given Sonine pair (k, ℓ) → ×

**Source definition.** S_α f(x) := ∫_0^x k(x-t) f(t) dt with ℓ ⋆ k = 1.

**Source property — not certified.** General fractional integral with arbitrary admissible kernel.

**Source use — context only.** Generalized memory models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F32.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f33"></a>

#### F33. `D_α_S` — Sonine-pair derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → ×

**Source definition.** D_α^S f := d/dx ∫_0^x ℓ(x-t) f(t) dt.

**Source property — not certified.** Inverse of S_α; defines general fractional calculus.

**Source use — context only.** Phenomenological non-local laws in mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F33.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f34"></a>

#### F34. `I^α_q` — q-Jackson fractional integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C(q^N) × (0,1) × C → C

**Source definition.** I^α_q f(x) := (x^α (1-q))/(Γ_q(α)) Σ_{k=0}^∞ q^k (1 - q^{k+1})_{α-1} f(q^k x).

**Source property — not certified.** Discrete sum over geometric grid; reduces to RL as q → 1.

**Source use — context only.** Discrete-scale fractional models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F34.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f35"></a>

#### F35. `D^α_q` — q-fractional derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → ×

**Source definition.** D^α_q := (D_q)^{[α]+1} I^{[α]+1-α}_q.

**Source property — not certified.** Pairs naturally with q-Jackson integral.

**Source use — context only.** Discrete fractional difference equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F35.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f36"></a>

#### F36. `D^α_disc` — discrete fractional difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℓ^∞(Z) × C → ℓ^∞(Z)

**Source definition.** Δ^α f(n) := Σ_{k=0}^n (-1)^k C(α, k) f(n - k).

**Source property — not certified.** Discrete analog of Grünwald-Letnikov.

**Source use — context only.** Long-memory time-series models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F36.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f37"></a>

#### F37. `∇^α` — fractional gradient

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** S(R^n) × (0,1) → vector field

**Source definition.** ∇^α f := C_{n,α} P.V. ∫ (f(x) - f(y))(x - y)/|x-y|^{n+α+1} dy.

**Source property — not certified.** Riesz gradient; satisfies ∇^α · = (-Δ)^{(α+1)/2}.

**Source use — context only.** Non-local diffusion gradients in image inpainting.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F37.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f38"></a>

#### F38. `div^α` — fractional divergence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Vector fields × (0,1) → scalars

**Source definition.** div^α u(x) := C_{n,α} P.V. ∫ (u(x) - u(y)) · (x-y)/|x-y|^{n+α+1} dy.

**Source property — not certified.** Adjoint of -∇^{α}; gives non-local conservation laws.

**Source use — context only.** Anomalous transport in heterogeneous media.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F38.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f39"></a>

#### F39. `curl^α` — fractional curl

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** R^3 vector fields × (0,1) → ×

**Source definition.** curl^α u defined via fractional analog of ∇ × u with Riesz kernel.

**Source property — not certified.** Non-local rotational sensitivity.

**Source use — context only.** Vorticity in non-Newtonian fluids.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F39.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f40"></a>

#### F40. `Bes_s` — Bessel potential

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** S × C → S

**Source definition.** Bes_s f := F^{-1}((1 + |ξ|²)^{-s/2} F f).

**Source property — not certified.** Defines Bessel potential spaces H^s.

**Source use — context only.** Sobolev embedding constants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F40.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f41"></a>

#### F41. `Sob_s` — Sobolev seminorm operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** H^s × C → R_+

**Source definition.** Sob_s(f) := ‖(-Δ)^{s/2} f‖_{L^2}.

**Source property — not certified.** Hilbert seminorm on the fractional Sobolev space.

**Source use — context only.** Regularity quantification in PDE analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F41.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f42"></a>

#### F42. `Carre_α` — fractional carré du champ

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Suitable space × generator L → bilinear form

**Source definition.** Γ_α(f, g) := (1/2)(L(fg) - f Lg - g Lf), with L = -(-Δ)^α.

**Source property — not certified.** Encodes diffusion-coefficient information of L.

**Source use — context only.** Functional-inequality estimates.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F42.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f43"></a>

#### F43. `D^α_RZ` — Riesz-Zygmund derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** D^α_{RZ} f := lim_{ε → 0} 1/ε^α (f(x+ε) - f(x))_avg over directions.

**Source property — not certified.** Symmetric fractional derivative; vanishes on odd-power perturbations.

**Source use — context only.** Isotropic fractional models in fluid mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F43.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f44"></a>

#### F44. `D^α_tem` — tempered fractional derivative

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × λ > 0 → ×

**Source definition.** D^{α,λ} f := exp(-λx) D^α (exp(λx) f) - λ^α f.

**Source property — not certified.** Truncates long memory exponentially.

**Source use — context only.** Tempered Lévy processes for finance with finite moments.

**Amendment (FALSE_AS_STATED).** Exponential tempering suppresses a nonlocal tail; it does not truncate it to finite support. Charge any numerical truncation error explicitly.

**QPT-128 substitution.** Use only through [A27](#a27), with each contract and its four research questions.

**Eligibility question for F44.** Is any truncation of long memory accompanied by a rigorous tail bound and a counted computational cost? Identify the exact role of this operator in that derivation.

<a id="op-f45"></a>

#### F45. `D^α_str` — strained fractional derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × deformation map → ×

**Source definition.** D^α_strain f := |J|^{-1/α} D^α (f ∘ φ^{-1}) along strained coordinates.

**Source property — not certified.** Adapts the fractional kernel to anisotropic media.

**Source use — context only.** Crack propagation in anisotropic materials.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F45.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f46"></a>

#### F46. `⨯_FC` — fractional convolution product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L^p × L^q × C → L^r

**Source definition.** (f ⨯_FC g)_α(x) := ∫ f(y) g(x-y) |x-y|^{α-1} dy / Γ(α).

**Source property — not certified.** Hardy-Littlewood-Sobolev-bounded for appropriate exponents.

**Source use — context only.** Non-local nonlinearities in fractional PDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F46.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f47"></a>

#### F47. `U_α(t)` — fractional evolution semigroup

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** B(X) × R_+ → B(X) given generator A

**Source definition.** U_α(t) := E_α(t^α A).

**Source property — not certified.** Solves D^α_C u = A u; not strongly continuous at 0 except for α = 1.

**Source use — context only.** Fractional-time heat and wave equations.

**Amendment (FALSE_AS_STATED).** For bounded A, E_alpha(t^alpha A) is norm-continuous at zero for 0<alpha<=1. For alpha!=1 it is generally not a semigroup. A=0 gives I at all times, refuting the source continuity claim.

**QPT-128 substitution.** Use only through [A27](#a27), with each contract and its four research questions.

**Eligibility question for F47.** Does a postselection normalization cancel the apparent amplitude shrinkage? Identify the exact role of this operator in that derivation.

<a id="op-f48"></a>

#### F48. `Subord_α` — subordinator operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Markov semigroup × (0,1) → subordinated semigroup

**Source definition.** Subord_α(P_t) := ∫_0^∞ P_s f_{α,t}(s) ds, where f_{α,t} is α-stable density.

**Source property — not certified.** Builds fractional generators from Markov semigroups.

**Source use — context only.** Connecting random-walk and fractional-diffusion limits.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F48.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f49"></a>

#### F49. `FBM_H` — fractional Brownian motion increment operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × (0,1) → centered Gaussian random variable

**Source definition.** FBM_H[f] := ∫ f(t) dB^H_t, the fractional Wiener integral.

**Source property — not certified.** Variance kernel: (1/2)(t^{2H} + s^{2H} - |t-s|^{2H}).

**Source use — context only.** Long-range-dependent noise modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for F49.** Can this analytic operator be replaced by a finite failure instrument with a uniform norm certificate and a charged discretization/tail error?

<a id="op-f50"></a>

#### F50. `MlrLink_α` — Mittag-Leffler link function

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** (0,1) × R → (0,1)

**Source definition.** MlrLink_α(x) := E_α(-x).

**Source property — not certified.** Generalizes the exponential survival function with heavy tails.

**Source use — context only.** Survival analysis with non-Markovian aging.

**Amendment (DOMAIN_GAP).** For 0<alpha<=1 and x>=0, E_alpha(-x) lies in (0,1], including value one at x=0. An unrestricted real argument does not have codomain (0,1).

**QPT-128 substitution.** Use only through [A27](#a27), with each contract and its four research questions.

**Eligibility question for F50.** Does smoothing lower the adversary success probability or merely erase information needed by honest verification? Identify the exact role of this operator in that derivation.

### Family Q: q-deformed operators

<a id="op-q1"></a>

#### Q1. `D_q` — q-derivative (Jackson)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** {f : C → C} × (C\{0,1}) → {f : C → C}

**Source definition.** (D_q f)(x) := (f(qx) - f(x)) / ((q-1) x), x ≠ 0.

**Source property — not certified.** lim_{q→1} D_q f = f'; product rule (D_q (fg))(x) = D_q f(x) g(x) + f(qx) D_q g(x).

**Source use — context only.** Hahn calculus on geometric lattices.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for Q1.** What state vector or failure event does a_n denote in the real proof protocol? Identify the exact role of this operator in that derivation.

<a id="op-q2"></a>

#### Q2. `∫_q` — Jackson q-integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** C(0,a) × (0,1) → C

**Source definition.** (∫_q f)(a) := a(1-q) Σ_{n=0}^∞ q^n f(q^n a).

**Source property — not certified.** Right inverse of D_q on continuous functions.

**Source use — context only.** Discrete analog of integration over geometric grids.

**Amendment (DOMAIN_GAP).** Continuity on the open interval (0,a) alone does not imply convergence of the Jackson sum: f(x)=1/x makes every summand equal. Require appropriate behavior near zero.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q2.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q3"></a>

#### Q3. `[·]_q` — q-bracket

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** ℕ × C → C

**Source definition.** [n]_q := (1 - q^n)/(1 - q) = 1 + q + ... + q^{n-1}.

**Source property — not certified.** Reduces to n at q = 1; q-deforms classical multiplicities.

**Source use — context only.** Counting via q-binomial coefficients.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for Q3.** Why are 128 halvings insufficient when the security reduction multiplies their probability by 20*Q^2? Identify the exact role of this operator in that derivation.

<a id="op-q4"></a>

#### Q4. `[·]_q!` — q-factorial

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℕ × C → C

**Source definition.** [n]_q! := Π_{k=1}^n [k]_q.

**Source property — not certified.** Recovers n! at q = 1.

**Source use — context only.** Normalization in q-deformed combinatorial identities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q4.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q5"></a>

#### Q5. `C_q(n,k)` — Gaussian binomial

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** ℕ² × C → C

**Source definition.** C_q(n,k) := [n]_q! / ([k]_q! [n-k]_q!).

**Source property — not certified.** Polynomial in q with non-negative integer coefficients.

**Source use — context only.** Counting subspaces of F_q^n over a finite field.

**Amendment (DOMAIN_GAP).** Require integers 0<=k<=n. Interpret the Gaussian binomial as its polynomial continuation at removable singularities; use prime-power q for counting finite-field subspaces.

**QPT-128 substitution.** Use only through [A15](#a15), with each contract and its four research questions.

**Eligibility question for Q5.** Which rank deficiency controls the signature entropy estimate, over which field or module? Identify the exact role of this operator in that derivation.

<a id="op-q6"></a>

#### Q6. `E_q` — q-exponential

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** C × (|q| < 1) → C

**Source definition.** E_q(z) := Σ_{n=0}^∞ z^n / [n]_q!.

**Source property — not certified.** Two distinct q-exponentials e_q, E_q with E_q(z) e_q(-z) = 1.

**Source use — context only.** Generating functions for q-counting.

**Amendment (DEFINITION_MISMATCH).** The written series is a normalized version of the small q-exponential and has a finite convergence disk for |q|<1; its reciprocal identity needs the distinct partner with q^(n(n-1)/2) factors and consistent argument scaling. Do not use it as an entire, automatically invertible transform.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q6.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q7"></a>

#### Q7. `(z;q)_∞` — q-Pochhammer infinite

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × (|q| < 1) → C

**Source definition.** (z;q)_∞ := Π_{n=0}^∞ (1 - z q^n).

**Source property — not certified.** Building block of theta functions and modular forms.

**Source use — context only.** Partition generating functions in number theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q7.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q8"></a>

#### Q8. `(z;q)_n` — q-Pochhammer finite

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × C × ℕ → C

**Source definition.** (z;q)_n := Π_{k=0}^{n-1} (1 - z q^k).

**Source property — not certified.** Relates to ordinary Pochhammer as q → 1.

**Source use — context only.** q-hypergeometric series.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q8.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q9"></a>

#### Q9. `φ` — q-hypergeometric

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** C^r × C^s × C × C → C

**Source definition.** _rφ_s(a_1,...; b_1,...; q, z) := Σ_n [Π (a_i;q)_n / Π (b_j;q)_n] z^n.

**Source property — not certified.** Encompasses many classical q-special functions.

**Source use — context only.** Counting plane partitions, lattice paths.

**Amendment (FORMULA_GAP).** The standard basic hypergeometric series also contains (q;q)_n in the denominator and a power of ((-1)^n*q^(n(n-1)/2)), determined by 1+s-r. Supply these conventions, parameter restrictions and convergence before using an identity.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q9.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q10"></a>

#### Q10. `Δ_q` — q-difference (forward)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** {f : C → C} × C → {f : C → C}

**Source definition.** Δ_q f(x) := f(qx) - f(x).

**Source property — not certified.** Related to D_q by D_q = Δ_q / ((q-1)x).

**Source use — context only.** q-difference equations in special-function theory.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for Q10.** Can each repetition be shown to halve its failure probability under the adversarial history? Identify the exact role of this operator in that derivation.

<a id="op-q11"></a>

#### Q11. `σ_q` — q-shift

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** {f : C → C} × C → {f : C → C}

**Source definition.** σ_q f(x) := f(qx).

**Source property — not certified.** Δ_q = σ_q - id; D_q = (σ_q - id)/((q-1)x).

**Source use — context only.** Symmetry of q-difference equations.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for Q11.** Why are 128 halvings insufficient when the security reduction multiplies their probability by 20*Q^2? Identify the exact role of this operator in that derivation.

<a id="op-q12"></a>

#### Q12. `Θ_q` — Jacobi theta operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Modular forms space → ×

**Source definition.** Θ_q(z) := Σ_{n ∈ Z} z^n q^{n(n-1)/2}.

**Source property — not certified.** Satisfies Jacobi triple product Θ_q(z) = (q;q)_∞ (z;q)_∞ (q/z;q)_∞.

**Source use — context only.** Modular forms and elliptic genera.

**Amendment (SIGN_ERROR).** For 0<|q|<1 and z!=0, the displayed bilateral series has triple product (q;q)_infinity*(-z;q)_infinity*(-q/z;q)_infinity. The product with positive z factors corresponds to alternating signs in the series.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q12.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q13"></a>

#### Q13. `R_q` — Yang-Baxter R-matrix

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** V ⊗ V × C → V ⊗ V

**Source definition.** R_q satisfies R_{12} R_{13} R_{23} = R_{23} R_{13} R_{12}.

**Source property — not certified.** Universal source of solvable lattice models.

**Source use — context only.** Quantum spin chains.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q13.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q14"></a>

#### Q14. `F_q` — Frobenius operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** X(F_q) × C → C

**Source definition.** F_q sends each point to its q-th power coordinate-wise.

**Source property — not certified.** Fixed-point set counts |X(F_q)|.

**Source use — context only.** Weil conjectures, zeta functions of varieties.

**Amendment (TYPE_GAP).** Use the q-power Frobenius endomorphism on an appropriate scheme over the algebraic closure of F_q; its fixed geometric points are the F_q-rational points. It is not a map from rational points times C into C.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q14.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q15"></a>

#### Q15. `D_q^α` — q-fractional derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × C → ×

**Source definition.** D_q^α := q-analog of Riemann-Liouville via q-Gamma function.

**Source property — not certified.** Reduces to D_q at α = 1.

**Source use — context only.** Discrete fractional calculus.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q15.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q16"></a>

#### Q16. `[X, Y]_q` — q-commutator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Algebra² × C → Algebra

**Source definition.** [X, Y]_q := X Y - q Y X.

**Source property — not certified.** Reduces to ordinary commutator at q = 1.

**Source use — context only.** Quantum-group relations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q16.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q17"></a>

#### Q17. `E_α^q` — q-Mittag-Leffler

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × C × C → C

**Source definition.** E_α^q(z) := Σ z^n / Γ_q(αn + 1).

**Source property — not certified.** Combines q-deformation and fractional order.

**Source use — context only.** q-fractional differential equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q17.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q18"></a>

#### Q18. `Γ_q` — q-Gamma function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C \ {0,-1,-2,...} × C → C

**Source definition.** Γ_q(z) := (q;q)_∞ / (q^z;q)_∞ (1-q)^{1-z}.

**Source property — not certified.** Reduces to Γ(z) as q → 1^-.

**Source use — context only.** Normalization in q-special-function identities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q18.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q19"></a>

#### Q19. `B_q` — q-Beta function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C² × C → C

**Source definition.** B_q(a,b) := Γ_q(a) Γ_q(b) / Γ_q(a+b).

**Source property — not certified.** Integral representation via Jackson integral.

**Source use — context only.** q-Selberg integrals.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q19.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q20"></a>

#### Q20. `⊗_q` — q-deformed tensor product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** V × W × C → V ⊗_q W

**Source definition.** Acts on bases with braiding factor q^{deg(v) deg(w)}.

**Source property — not certified.** Universal in symmetric tensor categories.

**Source use — context only.** Quantum-group representations.

**Amendment (DOMAIN_GAP).** A braided tensor category need not be symmetric: braiding twice need not be the identity. State the category and braiding explicitly.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q20.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q21"></a>

#### Q21. `S_q` — q-antipode

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Hopf algebra × C → ×

**Source definition.** S_q: H_q → H_q satisfying μ(S_q ⊗ id) Δ = ε.

**Source property — not certified.** Anti-coalgebra and anti-algebra map.

**Source use — context only.** Quantum-group symmetries.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q21.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q22"></a>

#### Q22. `Δ_H,q` — q-coproduct

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Hopf algebra × C → H ⊗ H

**Source definition.** Δ_{H,q}(X) for generators X is q-deformed standard coproduct.

**Source property — not certified.** Comultiplication in quantized enveloping algebras.

**Source use — context only.** Tensoring quantum-group representations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q22.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q23"></a>

#### Q23. `U_q(g)` — quantized enveloping algebra functor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lie algebras × C → algebras

**Source definition.** U_q(g) given by Drinfeld-Jimbo relations; ψ-Serre relations among E_i, F_i, K_i^±.

**Source property — not certified.** Hopf algebra with universal R-matrix at generic q.

**Source use — context only.** Knot invariants and 3-manifold invariants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q23.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q24"></a>

#### Q24. `J_q` — Jones polynomial operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Knots × C → Z[q^{±1}]

**Source definition.** J_q(K) := Markov trace of braid representation in U_q(sl_2).

**Source property — not certified.** Topological invariant up to ambient isotopy.

**Source use — context only.** Knot classification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q24.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q25"></a>

#### Q25. `V_q` — Vassiliev finite-type operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Knots × C → coeffs in q-expansion

**Source definition.** Coefficients of J_q at q = 1 give finite-type knot invariants.

**Source property — not certified.** Encodes singularities of the universal R-matrix.

**Source use — context only.** Combinatorial knot invariants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q25.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q26"></a>

#### Q26. `Ω_q` — Chevalley involution (q)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** U_q(g) × C → ×

**Source definition.** Ω_q exchanges E_i ↔ F_i, K_i ↔ K_i^{-1}, q ↔ q^{-1}.

**Source property — not certified.** Anti-algebra isomorphism preserving duality.

**Source use — context only.** Dual modules in category O_q.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q26.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q27"></a>

#### Q27. `B_q^n` — q-Bernstein basis polynomial

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × ℕ × ℕ × C → C

**Source definition.** B_q^n_k(x) := C_q(n,k) x^k Π_{j=0}^{n-k-1}(1 - q^j x).

**Source property — not certified.** Reduces to Bernstein basis at q = 1.

**Source use — context only.** q-Bezier curves in geometric modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q27.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q28"></a>

#### Q28. `Toy_q` — Toeplitz q-deformation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** B(ℓ²) × C → ×

**Source definition.** Generated by S with S* S - q S S* = (1-q) P_0, P_0 the rank-1 projection.

**Source property — not certified.** C*-algebra deformation; nuclear when |q| < 1.

**Source use — context only.** Free-probability with q-Gaussian variables.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q28.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q29"></a>

#### Q29. `Φ_q` — q-Fourier transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** L^2(q^Z, μ_q) × C → ×

**Source definition.** Φ_q f(ξ) := Σ_{n ∈ Z} f(q^n) e_q(i ξ q^n) μ_q({q^n}).

**Source property — not certified.** Diagonalizes the q-derivative.

**Source use — context only.** Signal processing on logarithmic grids.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q29.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q30"></a>

#### Q30. `Carleson_q` — q-Carleson kernel

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** K_q(x, y) := Σ_{n ≥ 0} q^n / (1 - q^n xy).

**Source property — not certified.** q-deformed Cauchy kernel.

**Source use — context only.** q-orthogonal polynomial theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q30.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q31"></a>

#### Q31. `Aₚ_q` — q-Askey-Wilson polynomials

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Functions on [-1,1] × C^4 × C → ×

**Source definition.** p_n(x; a,b,c,d | q) satisfying a 4-parameter q-orthogonality relation.

**Source property — not certified.** Top of the q-Askey scheme; all classical OPs are limits.

**Source use — context only.** Solvable models in mathematical physics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q31.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q32"></a>

#### Q32. `Mac_q` — Macdonald operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Symmetric functions × t, q → ×

**Source definition.** Diagonalized by Macdonald polynomials P_λ(x; q, t).

**Source property — not certified.** Two-parameter generalization of Schur and Hall-Littlewood.

**Source use — context only.** Symmetric function theory and AGT correspondences.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q32.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q33"></a>

#### Q33. `Ch_q` — q-Chebyshev operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Polynomials × C → ×

**Source definition.** T_n^q(cos θ) := cos(n θ) deformed via q-recursion.

**Source property — not certified.** Recovers classical Chebyshev at q = 1.

**Source use — context only.** q-orthogonal approximation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q33.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q34"></a>

#### Q34. `Hcr_q` — q-Hermite

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Polynomials × C → ×

**Source definition.** H_n^q satisfy a q-version of the three-term recursion of Hermite.

**Source property — not certified.** Generating function involves q-exponential.

**Source use — context only.** Continuous q-Gaussian distributions in free probability.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q34.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q35"></a>

#### Q35. `Lag_q` — q-Laguerre

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Polynomials × C × R → ×

**Source definition.** L_n^{α,q} satisfy q-deformed Laguerre orthogonality.

**Source property — not certified.** Special function in the q-Askey scheme.

**Source use — context only.** q-deformed harmonic oscillator.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q35.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q36"></a>

#### Q36. `Lege_q` — little/big q-Legendre

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** [−1,1] × C → ×

**Source definition.** Specializations of Askey-Wilson with a, b, c, d set to ±√q.

**Source property — not certified.** Orthogonal w.r.t. uniform q-measure.

**Source use — context only.** Lattice-path enumeration.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q36.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q37"></a>

#### Q37. `Sa_q` — q-Saalschütz operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Hypergeometric coefficients × C → ×

**Source definition.** Sa_q applies the q-Saalschütz summation identity to a Saalschützian _3φ_2 series.

**Source property — not certified.** Closed form: product of q-Pochhammers.

**Source use — context only.** Special-value identities in number theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q37.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q38"></a>

#### Q38. `Jct_q` — q-Heine sum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Hypergeometric coefficients × C → ×

**Source definition.** Heine's q-analog of Gauss's _2F_1 summation theorem.

**Source property — not certified.** Sums a Saalschütz-like _2φ_1 in closed form.

**Source use — context only.** Reduction of q-series to closed form.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q38.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q39"></a>

#### Q39. `HW_q` — Hayman-Wynn product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Power series × C → ×

**Source definition.** HW_q(f) := f(qx) f(q²x) ... (formal infinite product).

**Source property — not certified.** Closed-form solutions to first-order q-difference equations.

**Source use — context only.** q-Heun equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q39.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q40"></a>

#### Q40. `[D_q, σ_q]` — shift-difference commutator

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × C → ×

**Source definition.** D_q σ_q - σ_q D_q = (q - 1) σ_q D_q / ((q-1)x · ?).

**Source property — not certified.** Captures non-commutativity of q-derivative and shift.

**Source use — context only.** Algebraic foundation of q-difference equations.

**Amendment (FORMULA_ERROR).** For q!=0,1 and x!=0, D_q sigma_q=q*sigma_q D_q, hence [D_q,sigma_q]=(q-1)*sigma_q D_q. Remove the unresolved denominator and question mark.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for Q40.** Do exact boundary tests give 73, 137, 193 and 265 rounds for the four chosen query caps? Identify the exact role of this operator in that derivation.

<a id="op-q41"></a>

#### Q41. `Pos_q` — positivity operator (q-Schur)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Symmetric functions × C → ×

**Source definition.** Pos_q checks positivity of expansion coefficients in q-Schur basis.

**Source property — not certified.** Conjecturally polynomial-time for Macdonald cases (Haglund-Haiman-Loehr).

**Source use — context only.** Combinatorial models for q-Macdonald polynomials.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q41.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q42"></a>

#### Q42. `Vert_q` — vertex operator (q-deformed)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Fock space × q → ×

**Source definition.** Vert_q(z) := exp(Σ a_n^* z^n) exp(Σ a_n z^{-n}) with q-modified bracket.

**Source property — not certified.** Generates quantum-affine algebra representations.

**Source use — context only.** Integrable hierarchies (KP, Toda).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q42.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q43"></a>

#### Q43. `Whit_q` — q-Whittaker function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** B-orbit functions on G(q) × params → ×

**Source definition.** Whit_q := matrix coefficient of principal series w.r.t. Whittaker vector.

**Source property — not certified.** Eigenfunction of Macdonald operators in the q → 0 limit.

**Source use — context only.** Geometric Langlands at finite places.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q43.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q44"></a>

#### Q44. `Eisen_q` — Eisenstein series (q-expansion)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Upper half-plane × ℕ → C

**Source definition.** E_k(q) := 1 - (2k/B_k) Σ_{n≥1} σ_{k-1}(n) q^n.

**Source property — not certified.** Generates ring of modular forms (k even ≥ 4).

**Source use — context only.** Number-theoretic identities, partition congruences.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q44.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q45"></a>

#### Q45. `Hecke_q` — Hecke operator (Hecke algebra at q)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Modular forms × C → ×

**Source definition.** T_p applied to f = Σ a_n q^n gives Σ (a_{np} + p^{k-1} a_{n/p}) q^n.

**Source property — not certified.** Multiplicative; eigenforms have multiplicative Fourier coefficients.

**Source use — context only.** Galois representations attached to modular forms.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q45.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q46"></a>

#### Q46. `Bra_q` — q-braid generator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** B_n × C → ×

**Source definition.** σ_i represented by R_q-matrix acting on tensor positions i, i+1.

**Source property — not certified.** Yang-Baxter equation gives braid relations.

**Source use — context only.** Topological-quantum-computation primitives.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q46.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q47"></a>

#### Q47. `Crys_q→0` — crystallization functor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** U_q(g)-modules × q → 0 → crystal bases

**Source definition.** Sends generators to combinatorial crystal operators ẽ_i, f̃_i.

**Source property — not certified.** Kashiwara crystals: combinatorial shadows of representations.

**Source use — context only.** Combinatorial models for branching rules.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q47.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q48"></a>

#### Q48. `[E_i, F_j]` — Drinfeld-Jimbo bracket

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** U_q(g) generators × q → algebra

**Source definition.** [E_i, F_j] = δ_{ij} (K_i - K_i^{-1}) / (q_i - q_i^{-1}).

**Source property — not certified.** Defining relation; reduces to [e_i, f_j] = δ_{ij} h_i at q → 1.

**Source use — context only.** Quantum-group commutation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q48.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q49"></a>

#### Q49. `⟨·,·⟩_q` — q-Shapovalov form

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** U_q(g)-modules × C → C

**Source definition.** ⟨·,·⟩_q is the unique contravariant Hermitian form normalized at highest weight.

**Source property — not certified.** Determinant formula generalizes Kac's.

**Source use — context only.** Irreducibility criteria for Verma modules.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q49.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

<a id="op-q50"></a>

#### Q50. `Tarasov` — Tarasov-Varchenko qKZ operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Tensor product of evaluation modules × q → ×

**Source definition.** Difference equation generalizing KZ to the q-setting.

**Source property — not certified.** Connection matrices given by R-matrices.

**Source use — context only.** Form factors in integrable lattice models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Q50.** Which concrete finite counting identity or recurrence does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?

### Family D: Discrete difference calculus

<a id="op-d1"></a>

#### D1. `Δ` — forward difference

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C^Z → C^Z

**Source definition.** (Δ f)(n) := f(n+1) - f(n).

**Source property — not certified.** Commutes with shifts; Δ = E - I where E is the shift.

**Source use — context only.** Finite-difference approximations to derivatives.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for D1.** What state vector or failure event does a_n denote in the real proof protocol? Identify the exact role of this operator in that derivation.

<a id="op-d2"></a>

#### D2. `∇` — backward difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^Z → C^Z

**Source definition.** (∇ f)(n) := f(n) - f(n-1).

**Source property — not certified.** ∇ = I - E^{-1}.

**Source use — context only.** Newton-Cotes backward interpolation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D2.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d3"></a>

#### D3. `δ_c` — central difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** C^Z → C^Z

**Source definition.** (δ_c f)(n) := f(n + 1/2) - f(n - 1/2).

**Source property — not certified.** Symmetric; preserves time-reversal symmetry.

**Source use — context only.** Symmetric numerical schemes.

**Amendment (TYPE_GAP).** Half-integer evaluations require functions on (1/2)Z or on R, not merely functions on Z. Retype the lattice before composing shifts.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D3.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d4"></a>

#### D4. `μ_c` — central average

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** C^Z → C^Z

**Source definition.** (μ_c f)(n) := (f(n + 1/2) + f(n - 1/2)) / 2.

**Source property — not certified.** Forms a calculus pair with δ_c: μ_c δ_c = (E - E^{-1})/2.

**Source use — context only.** Smoothed-derivative schemes.

**Amendment (TYPE_GAP).** Half-integer evaluations require functions on (1/2)Z or on R, not merely functions on Z. Retype the lattice before composing shifts.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D4.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d5"></a>

#### D5. `E^h` — h-shift operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C(R) × R → C(R)

**Source definition.** (E^h f)(x) := f(x + h).

**Source property — not certified.** E^h = exp(h D) formally on analytic functions.

**Source use — context only.** Translation symmetry in time-step analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D5.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d6"></a>

#### D6. `Δ_h` — h-forward difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C(R) × R → C(R)

**Source definition.** (Δ_h f)(x) := f(x+h) - f(x).

**Source property — not certified.** Δ_h / h → D as h → 0.

**Source use — context only.** Variable-step finite-difference methods.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D6.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d7"></a>

#### D7. `Δ^{(n)}` — iterated forward difference

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C^Z × ℕ → C^Z

**Source definition.** Δ^{(n)} f(k) := Σ_{j=0}^n (-1)^{n-j} C(n,j) f(k+j).

**Source property — not certified.** Vanishes on polynomials of degree < n.

**Source use — context only.** Polynomial-fit detection in numerical signals.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for D7.** Why are 128 halvings insufficient when the security reduction multiplies their probability by 20*Q^2? Identify the exact role of this operator in that derivation.

<a id="op-d8"></a>

#### D8. `∇_q^{(n)}` — iterated backward difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → ×

**Source definition.** ∇^{(n)} f(k) := Σ_{j=0}^n (-1)^j C(n,j) f(k - j).

**Source property — not certified.** Conjugate to Δ^{(n)} under reflection.

**Source use — context only.** Backward interpolation polynomials.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D8.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d9"></a>

#### D9. `Δ^α` — fractional forward difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** C^Z × C → C^Z

**Source definition.** Δ^α f(n) := Σ_{k=0}^∞ (-1)^k C(α,k) f(n+k) (truncate at finite range).

**Source property — not certified.** Reduces to Δ^{(n)} at α = n; corresponds to Grünwald-Letnikov.

**Source use — context only.** Long-memory discrete-time models.

**Amendment (SIGN_ERROR).** The displayed binomial series is (I-E)^alpha. At integer n it equals (-1)^n*(E-I)^n, not always the displayed forward difference. Choose a convention and convergence domain; an arbitrary truncation changes the operator.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D9.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d10"></a>

#### D10. `S^N` — Newton series operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Polynomials → Polynomials

**Source definition.** S^N f := Σ_{k=0}^N (Δ^k f)(0) · C(x, k).

**Source property — not certified.** Inverts the polynomial basis change x^n ↔ x^{(n)}.

**Source use — context only.** Sampling-based polynomial reconstruction.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D10.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d11"></a>

#### D11. `x^{(n)}` — falling factorial

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × ℕ → C

**Source definition.** x^{(n)} := x(x-1)...(x-n+1).

**Source property — not certified.** Δ x^{(n)} = n x^{(n-1)} — discrete analog of derivative.

**Source use — context only.** Umbral calculus identities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D11.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d12"></a>

#### D12. `x^[n]` — rising factorial

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × ℕ → C

**Source definition.** x^[n] := x(x+1)...(x+n-1).

**Source property — not certified.** Related to Pochhammer; integration partner of falling factorial.

**Source use — context only.** Hypergeometric coefficient simplification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D12.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d13"></a>

#### D13. `S(n,k)` — Stirling 2nd-kind operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℕ² → ℕ

**Source definition.** S(n,k) := (1/k!) Σ_{j=0}^k (-1)^{k-j} C(k,j) j^n.

**Source property — not certified.** Connection coefficients: x^n = Σ_k S(n,k) x^{(k)}.

**Source use — context only.** Partitioning sets into k blocks.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D13.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d14"></a>

#### D14. `s(n,k)` — Stirling 1st-kind operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℕ² → ℤ

**Source definition.** x^{(n)} = Σ_k s(n,k) x^k.

**Source property — not certified.** Signed; |s(n,k)| counts permutations of n with k cycles.

**Source use — context only.** Cycle structure of permutations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D14.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d15"></a>

#### D15. `B_n` — Bell number operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℕ → ℕ

**Source definition.** B_n := Σ_{k=0}^n S(n,k).

**Source property — not certified.** Number of partitions of an n-element set.

**Source use — context only.** Combinatorial counting in set partitions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D15.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d16"></a>

#### D16. `Σ_h` — h-summation (indefinite)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^Z → C^Z

**Source definition.** Σ_h f satisfies Δ_h(Σ_h f) = f.

**Source property — not certified.** Discrete antiderivative; unique up to h-periodic constants.

**Source use — context only.** Discrete antidifference in summation by parts.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D16.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d17"></a>

#### D17. `⊕_summ` — summation by parts

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^Z² → C^Z

**Source definition.** Σ f Δg = fg|_a^b - Σ Eg · Δf.

**Source property — not certified.** Discrete analog of integration by parts.

**Source use — context only.** Discrete-integral manipulations in number theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D17.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d18"></a>

#### D18. `Ind_disc` — discrete indicator derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 𝒫(Z) → C^Z

**Source definition.** I_S(n) := 1 if n ∈ S, else 0; Δ I_S = I_{S-1} - I_S.

**Source property — not certified.** Detects boundary transitions.

**Source use — context only.** Event-onset detection in time-series.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D18.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d19"></a>

#### D19. `Conv_disc` — discrete convolution

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** C^Z × C^Z → C^Z

**Source definition.** (f * g)(n) := Σ_k f(k) g(n - k).

**Source property — not certified.** Diagonalized by discrete Fourier transform.

**Source use — context only.** FIR filters in DSP.

**Amendment (DOMAIN_GAP).** For infinite convolution, require summability or work with finite-support sequences/formal series. Arbitrary bilateral sequences need not have a defined convolution.

**QPT-128 substitution.** Use only through [A11](#a11), with each contract and its four research questions.

**Eligibility question for D19.** What is the maximal mass of that family under the implemented bit-to-challenge map? Identify the exact role of this operator in that derivation.

<a id="op-d20"></a>

#### D20. `Z_op` — Z-transform operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℓ¹(ℕ) × C → C

**Source definition.** Z[f](z) := Σ_{n ≥ 0} f(n) z^{-n}.

**Source property — not certified.** Difference operators become rational functions in z.

**Source use — context only.** Stability analysis of discrete-time systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D20.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d21"></a>

#### D21. `Umb` — umbral evaluation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Polynomials in shadow variable × linear functional → ×

**Source definition.** Umb_L(p(α)) := L(p) interpreting powers α^n via L(α^n).

**Source property — not certified.** Bridges polynomial identities and combinatorial sequences.

**Source use — context only.** Generating-function identities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D21.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d22"></a>

#### D22. `D_α^umb` — umbral derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Polynomials × umbral variable → polynomials

**Source definition.** D_α := lowering operator with [D_α, M_α] = id in umbral algebra.

**Source property — not certified.** Adjoint of shift in the umbral Hopf algebra.

**Source use — context only.** Sheffer-sequence identities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D22.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d23"></a>

#### D23. `Δ^{Mac}` — MacMahon Ω operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Laurent series in z → Laurent series without z

**Source definition.** Ω_{≥} (Σ a_{j,k} λ^j) := Σ_{j ≥ 0} a_{j,k}.

**Source property — not certified.** Extracts non-negative coefficients; key in partition analysis.

**Source use — context only.** Solving partition counting with linear constraints.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D23.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d24"></a>

#### D24. `Sh_T` — Sheffer sequence operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Linear functionals × polynomials → polynomials

**Source definition.** Sh_T(p_n) := A(T) (B(T))^n / n! · x^n in Riordan-array sense.

**Source property — not certified.** Generalizes binomial-, Appell-, and associated sequences.

**Source use — context only.** Unified treatment of classical polynomial families.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D24.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d25"></a>

#### D25. `Bell_∂` — Bell polynomial operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^∞ × ℕ → polynomial

**Source definition.** B_{n,k}(f_1,...,f_{n-k+1}) := ν-sums over partitions of n into k parts.

**Source property — not certified.** Faà di Bruno: D^n (g ∘ f) = Σ g^{(k)} B_{n,k}.

**Source use — context only.** Higher-order chain rule.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D25.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d26"></a>

#### D26. `D^FdB` — Faà di Bruno operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^∞ × C^∞ × ℕ → C

**Source definition.** D^{FdB}_n(g, f) := Σ_k g^{(k)}(f(x)) B_{n,k}.

**Source property — not certified.** Closed-form n-th derivative of composition.

**Source use — context only.** Hochschild homology and Taylor expansion.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D26.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d27"></a>

#### D27. `Sym_n` — symmetrization operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^n → C^n

**Source definition.** Sym_n f(x_1,...,x_n) := (1/n!) Σ_{σ ∈ S_n} f(x_{σ(1)},...,x_{σ(n)}).

**Source property — not certified.** Idempotent projection onto symmetric functions.

**Source use — context only.** Bosonic states in statistical mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D27.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d28"></a>

#### D28. `Asym_n` — antisymmetrization operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^n → C^n

**Source definition.** Asym_n f := (1/n!) Σ_σ sgn(σ) f(σ · x).

**Source property — not certified.** Idempotent; image is the antisymmetric subspace.

**Source use — context only.** Fermionic Slater determinants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D28.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d29"></a>

#### D29. `Lah` — Lah operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Polynomials × ℕ → polynomials

**Source definition.** x^{[n]} = Σ_k L(n,k) x^{(k)}, L(n,k) := (n-1 choose k-1) n!/k!.

**Source property — not certified.** Connection coefficients between rising and falling factorials.

**Source use — context only.** Combinatorial bijections.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D29.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d30"></a>

#### D30. `Δ_log` — logarithmic difference

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C^Z → C^Z

**Source definition.** Δ_log f(n) := log f(n+1) - log f(n).

**Source property — not certified.** Gives ratios: exp(Δ_log f) = f(n+1)/f(n).

**Source use — context only.** Growth-rate normalization in time series.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for D30.** Can each repetition be shown to halve its failure probability under the adversarial history? Identify the exact role of this operator in that derivation.

<a id="op-d31"></a>

#### D31. `Geom_op` — geometric-mean shift

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (R_+)^Z → R_+

**Source definition.** G f(n) := √(f(n+1) f(n-1)).

**Source property — not certified.** Discrete analog of midpoint exponential.

**Source use — context only.** Smoothing log-normally distributed data.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D31.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d32"></a>

#### D32. `Δ_α^P` — Patera-type fractional difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^Z × C → C^Z

**Source definition.** Δ_α^P f := infinite-sum binomial difference along α.

**Source property — not certified.** Tempered version of Δ^α.

**Source use — context only.** Discrete tempered Lévy walks.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D32.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d33"></a>

#### D33. `Δ_circ` — circular difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^{Z_n} → C^{Z_n}

**Source definition.** (Δ_circ f)(k) := f(k+1 mod n) - f(k).

**Source property — not certified.** Eigenvalues e^{2πij/n} - 1 in DFT basis.

**Source use — context only.** Periodic-signal differentiation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D33.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d34"></a>

#### D34. `Var_disc` — discrete total variation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^Z → R_+

**Source definition.** TV(f) := Σ_n |f(n+1) - f(n)|.

**Source property — not certified.** Functional; finite TV characterizes BV sequences.

**Source use — context only.** Discrete-image regularization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D34.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d35"></a>

#### D35. `Lap_g` — discrete graph Laplacian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^V × Graph → C^V

**Source definition.** L f(v) := Σ_{w ~ v} (f(v) - f(w)).

**Source property — not certified.** Positive semidefinite; kernel is constant functions on connected components.

**Source use — context only.** Spectral graph theory; community detection.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D35.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d36"></a>

#### D36. `L_p_graph` — p-Laplacian on graphs

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^V × Graph × p → C^V

**Source definition.** L_p f(v) := Σ_{w~v} |f(v) - f(w)|^{p-2} (f(v) - f(w)).

**Source property — not certified.** Non-linear for p ≠ 2; minimizes ℓ^p energy.

**Source use — context only.** Image-graph segmentation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D36.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d37"></a>

#### D37. `Norm_disc` — discrete normalized Laplacian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^V × Graph → C^V

**Source definition.** L_norm := D^{-1/2} (D - A) D^{-1/2}, D diagonal degree.

**Source property — not certified.** Eigenvalues in [0, 2]; ties to random walks.

**Source use — context only.** Cheeger inequality bounds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D37.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d38"></a>

#### D38. `PageR_op` — PageRank operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(V) × Graph × α → Δ(V)

**Source definition.** PR(π) := α P^T π + (1-α) u, u uniform.

**Source property — not certified.** Contraction in TV distance; unique fixed point.

**Source use — context only.** Web-page ranking.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D38.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d39"></a>

#### D39. `DTW_op` — dynamic time warping

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Sequences × cost → R_+

**Source definition.** DTW(x, y) := min over warps π of Σ d(x_i, y_{π(i)}).

**Source property — not certified.** Pseudo-metric on time-series.

**Source use — context only.** Speech recognition alignment.

**Amendment (FALSE_AS_STATED).** Standard dynamic time warping is not generally a metric or pseudometric: triangle inequalities can fail. Use it as a cost unless a modified definition has a proved triangle inequality.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D39.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d40"></a>

#### D40. `Edit_op` — edit-distance operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Strings × cost → R_+

**Source definition.** Levenshtein, dual of substitution / insertion / deletion cost.

**Source property — not certified.** Metric on free monoid.

**Source use — context only.** Spell checking, DNA sequence comparison.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D40.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d41"></a>

#### D41. `Conv_dt` — discrete distance transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** {0,1}^Z^n → R_+^Z^n

**Source definition.** DT(f)(x) := min_{y : f(y)=1} d(x,y).

**Source property — not certified.** Computed via infimal convolution with a quadratic.

**Source use — context only.** Object skeletonization in computer vision.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D41.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d42"></a>

#### D42. `Wave_disc` — discrete wave operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** C^{Z × Z} → C^{Z × Z}

**Source definition.** (□ u)(n, t) := u(n, t+1) + u(n, t-1) - u(n+1, t) - u(n-1, t).

**Source property — not certified.** Discrete d'Alembertian; preserves Lorentzian symmetry on lattice.

**Source use — context only.** Numerical wave propagation.

**Amendment (FALSE_AS_STATED).** A fixed square lattice does not preserve the full continuous Lorentz group. State the discrete symmetries actually preserved.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D42.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d43"></a>

#### D43. `Heat_disc` — discrete heat equation operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^Z → C^Z

**Source definition.** H f(n) := f(n+1) - 2 f(n) + f(n-1).

**Source property — not certified.** Second difference; eigenvalues -4 sin²(k/2).

**Source use — context only.** Random walks on Z.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D43.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d44"></a>

#### D44. `Lap_dir` — directional discrete Laplacian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^Z^d × direction v → C^Z^d

**Source definition.** L_v f := f(x + v) - 2 f(x) + f(x - v).

**Source property — not certified.** Anisotropic discretization.

**Source use — context only.** Lattice models with preferred axes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D44.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d45"></a>

#### D45. `Shf_per` — periodic-shift Sheffer

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** Polynomials p_n(x) := σ_q-shift Sheffer generated by exp((x - a) f(t)).

**Source property — not certified.** Reduces to Hermite, Laguerre for specific (a, f).

**Source use — context only.** Combinatorial identities with periodic structure.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D45.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d46"></a>

#### D46. `Tdiff` — telescoping operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C^Z × Z² → C

**Source definition.** T_{a,b} f := f(b) - f(a) = Σ_{n=a}^{b-1} Δf(n).

**Source property — not certified.** Fundamental theorem of summation calculus.

**Source use — context only.** Reducing sums to boundary evaluations.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for D46.** Can each repetition be shown to halve its failure probability under the adversarial history? Identify the exact role of this operator in that derivation.

<a id="op-d47"></a>

#### D47. `WZ` — Wilf-Zeilberger pair

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Hypergeometric pairs (F, G) → boolean

**Source definition.** Δ_n F(n,k) = ∇_k G(n,k) certifies Σ F is constant in n.

**Source property — not certified.** Algorithmic proof of hypergeometric identities.

**Source use — context only.** Automated combinatorial identity verification.

**Amendment (DOMAIN_GAP).** The WZ telescoping identity implies a constant sum only after boundary terms vanish and infinite sums/limits are justified, or on a finite range with its boundary terms included.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D47.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d48"></a>

#### D48. `Hyper` — hypergeometric ratio operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Sequences → rational functions

**Source definition.** Hyper(f)(n) := f(n+1)/f(n).

**Source property — not certified.** Detects hypergeometric sequences (those with rational ratio).

**Source use — context only.** Closed-form solutions to recurrences.

**QPT-128 substitution.** Use only through [A05](#a05), with each contract and its four research questions.

**Eligibility question for D48.** Do exact boundary tests give 73, 137, 193 and 265 rounds for the four chosen query caps? Identify the exact role of this operator in that derivation.

<a id="op-d49"></a>

#### D49. `Petkovšek` — Petkovšek's algorithm operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Linear recurrences → hypergeometric solutions

**Source definition.** Returns hypergeometric solutions to P(n, E) f = 0 if any exist.

**Source property — not certified.** Decides existence in polynomial time.

**Source use — context only.** Closed-form solutions to combinatorial recurrences.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D49.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

<a id="op-d50"></a>

#### D50. `Gosper` — Gosper's algorithm operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Hypergeometric t_k → antidifference

**Source definition.** Returns S_k with Δ_k S = t if t is indefinite-hypergeometric-summable.

**Source property — not certified.** Decision procedure for hypergeometric antidifferences.

**Source use — context only.** Closed-form indefinite sums.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for D50.** Can this discrete identity certify a recurrence, exact count or stopping boundary used by a named security inequality?

### Family I: Information theory

<a id="op-i1"></a>

#### I1. `H` — Shannon entropy

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Δ(X) → R_+ ∪ {∞}

**Source definition.** H(P) := -∫ p log p dμ.

**Source property — not certified.** Concave; maximized by uniform distribution on finite X.

**Source use — context only.** Channel capacity and source coding.

**Amendment (DOMAIN_GAP).** For the nonnegative entropy signature, restrict to discrete probability masses. Differential entropy and its Renyi analog depend on the reference measure and can be negative. Set log base two for bit calculations.

**QPT-128 substitution.** Use only through [A14](#a14), with each contract and its four research questions.

**Eligibility question for I1.** Which variable is secret, and what classical/quantum side information does E contain at the time of use? Identify the exact role of this operator in that derivation.

<a id="op-i2"></a>

#### I2. `H_α` — Rényi α-entropy

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Δ(X) × (0,∞)\{1} → R_+

**Source definition.** H_α(P) := (1/(1-α)) log ∫ p^α dμ.

**Source property — not certified.** Limit α → 1 gives Shannon; α = 2 gives collision entropy.

**Source use — context only.** Security analysis in randomness extraction.

**Amendment (DOMAIN_GAP).** For the nonnegative entropy signature, restrict to discrete probability masses. Differential entropy and its Renyi analog depend on the reference measure and can be negative. Set log base two for bit calculations.

**QPT-128 substitution.** Use only through [A14](#a14), [A25](#a25), with each contract and its four research questions.

**Eligibility question for I2.** Does the operator improve conditional guessing probability or only a Shannon-entropy/visual statistic? Identify the exact role of this operator in that derivation.

<a id="op-i3"></a>

#### I3. `H_T` — Tsallis q-entropy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X) × R → R

**Source definition.** H_q(P) := (1 - ∫ p^q dμ) / (q - 1).

**Source property — not certified.** Non-extensive; recovers H as q → 1.

**Source use — context only.** Non-equilibrium statistical mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I3.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i4"></a>

#### I4. `D_KL` — Kullback-Leibler divergence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X)² → R_+ ∪ {∞}

**Source definition.** D_KL(P‖Q) := ∫ p log(p/q) dμ.

**Source property — not certified.** Non-negative; zero iff P = Q; not symmetric.

**Source use — context only.** Variational inference; likelihood ratios.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I4.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i5"></a>

#### I5. `D_f` — f-divergence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ(X)² × convex f → R_+ ∪ {∞}

**Source definition.** D_f(P‖Q) := ∫ q f(p/q) dμ.

**Source property — not certified.** Encompasses KL (f(t) = t log t), χ² (f(t) = (t-1)²), TV (f(t) = |t-1|/2).

**Source use — context only.** Unified framework for divergence-based estimation.

**Amendment (DOMAIN_GAP).** Require a convex f normalized by f(1)=0 and appropriate extended-value conventions to conclude nonnegativity for probability distributions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I5.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i6"></a>

#### I6. `D_α^R` — Rényi α-divergence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X)² × (0,∞)\{1} → R_+ ∪ {∞}

**Source definition.** D_α(P‖Q) := (1/(α-1)) log ∫ p^α q^{1-α} dμ.

**Source property — not certified.** Monotone in α; data-processing inequality holds.

**Source use — context only.** Hypothesis-testing error exponents.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I6.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i7"></a>

#### I7. `D_TV` — total variation distance

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(X)² → [0,1]

**Source definition.** D_TV(P,Q) := (1/2) ∫ |p - q| dμ = sup_A |P(A) - Q(A)|.

**Source property — not certified.** Metric; bounded by √((1/2) D_KL) (Pinsker).

**Source use — context only.** Coupling-based mixing-time bounds for Markov chains.

**QPT-128 substitution.** Use only through [A12](#a12), [A20](#a20), [A25](#a25), with each contract and its four research questions.

**Eligibility question for I7.** For a binary replacement, which two distinct accepted responses reconstruct the actual quorum witness? Identify the exact role of this operator in that derivation.

<a id="op-i8"></a>

#### I8. `D_H` — Hellinger distance

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X)² → [0,1]

**Source definition.** D_H(P,Q)² := (1/2) ∫ (√p - √q)² dμ.

**Source property — not certified.** Metric; relates to fidelity F = 1 - D_H².

**Source use — context only.** Asymptotic statistics; Le Cam's inequalities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I8.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i9"></a>

#### I9. `D_BC` — Bhattacharyya coefficient

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X)² → [0,1]

**Source definition.** BC(P,Q) := ∫ √(p q) dμ.

**Source property — not certified.** Multiplicative under product measures.

**Source use — context only.** Pattern-recognition class-separability measure.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I9.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i10"></a>

#### I10. `D_W_p` — Wasserstein-p distance

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X)² × p ≥ 1 → R_+

**Source definition.** W_p(P,Q) := (inf_π ∫ d(x,y)^p dπ(x,y))^{1/p}, π coupling.

**Source property — not certified.** Metric; metrizes weak convergence on compact spaces.

**Source use — context only.** Optimal transport; generative-model evaluation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I10.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i11"></a>

#### I11. `D_KR` — Kantorovich-Rubinstein dual

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X)² → R_+

**Source definition.** D_KR(P,Q) := sup_{‖f‖_Lip ≤ 1} ∫ f d(P - Q).

**Source property — not certified.** Equals W_1; expresses Lipschitz-test optimization.

**Source use — context only.** 1-Wasserstein GANs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I11.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i12"></a>

#### I12. `I(X;Y)` — mutual information

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X × Y) → R_+

**Source definition.** I(X;Y) := D_KL(P_{XY} ‖ P_X ⊗ P_Y) = H(X) + H(Y) - H(X,Y).

**Source property — not certified.** Symmetric in X, Y; non-negative; zero iff independent.

**Source use — context only.** Channel capacity; feature selection.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I12.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i13"></a>

#### I13. `I_α` — Rényi mutual information

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X × Y) × α → R

**Source definition.** I_α(X;Y) := D_α(P_{XY} ‖ P_X ⊗ P_Y).

**Source property — not certified.** Multiple non-equivalent definitions; data-processing varies by definition.

**Source use — context only.** Side-channel leakage quantification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I13.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i14"></a>

#### I14. `C(X;Y)` — Sibson information radius

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Set of channels × prior → R_+

**Source definition.** C(P_Y|X) := sup_{P_X} I(X;Y).

**Source property — not certified.** Equals channel capacity.

**Source use — context only.** Shannon-coding theorem.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I14.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i15"></a>

#### I15. `E_KL` — KL projection

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ(X) × E ⊆ Δ → arg inf

**Source definition.** E_KL(Q) := arg min_{P ∈ E} D_KL(P ‖ Q).

**Source property — not certified.** Unique on convex sets E; Pythagorean theorem holds.

**Source use — context only.** Information-geometric mean and maximum-entropy fitting.

**Amendment (DOMAIN_GAP).** Convexity alone does not imply existence of an attained KL projection. Add closedness/compactness or another existence hypothesis and suitable finiteness/support assumptions for uniqueness.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I15.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i16"></a>

#### I16. `M_KL` — KL projection (reverse)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X) × E → arg inf

**Source definition.** M_KL(Q) := arg min_{P ∈ E} D_KL(Q ‖ P).

**Source property — not certified.** Differs from E_KL except on flat families.

**Source use — context only.** Variational inference (M-step in EM).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I16.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i17"></a>

#### I17. `⊗_I` — joint information construction

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(X) × Markov kernel → Δ(X × Y)

**Source definition.** (P ⊗_I K)(A × B) := ∫_A K(x, B) dP(x).

**Source property — not certified.** Lifts marginal P and conditional K to a joint.

**Source use — context only.** Bayesian-network construction.

**QPT-128 substitution.** Use only through [A02](#a02), [A16](#a16), with each contract and its four research questions.

**Eligibility question for I17.** Can extractor failure, binding failure, signature forgery and truncation failure be defined on one coupled execution? Identify the exact role of this operator in that derivation.

<a id="op-i18"></a>

#### I18. `Marg_X` — marginalization operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ(X × Y) → Δ(X)

**Source definition.** Marg_X(P)(A) := P(A × Y).

**Source property — not certified.** Right inverse to ⊗_I given a fixed conditional.

**Source use — context only.** Marginal likelihood computation.

**Amendment (DIRECTION_ERROR).** Marginalization is a left inverse of the map P -> P tensor K for a fixed stochastic kernel K: Marg(P tensor K)=P. The reverse composition is not the identity on arbitrary joints.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I18.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i19"></a>

#### I19. `Cond` — conditioning operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(X × Y) × Y → Δ(X)

**Source definition.** Cond(P, y)(A) := P(X ∈ A | Y = y) (Radon-Nikodym definition).

**Source property — not certified.** Defined almost surely; gives regular conditional distributions.

**Source use — context only.** Bayesian inference posterior.

**QPT-128 substitution.** Use only through [A08](#a08), [A16](#a16), with each contract and its four research questions.

**Eligibility question for I19.** Which information is visible when the next challenge is sampled? Identify the exact role of this operator in that derivation.

<a id="op-i20"></a>

#### I20. `H(X|Y)` — conditional entropy

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(X × Y) → R_+

**Source definition.** H(X|Y) := H(X,Y) - H(Y) = E_Y H(X|Y=y).

**Source property — not certified.** Non-negative for discrete; equals 0 iff X is Y-measurable.

**Source use — context only.** Predictive uncertainty quantification.

**QPT-128 substitution.** Use only through [A14](#a14), with each contract and its four research questions.

**Eligibility question for I20.** If compression discards information, is that information necessary to verify authorization or extract a conflict witness? Identify the exact role of this operator in that derivation.

<a id="op-i21"></a>

#### I21. `Ent_diff` — differential entropy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ(R^n) → R ∪ {-∞}

**Source definition.** h(X) := -∫ f(x) log f(x) dx.

**Source property — not certified.** Not translation-invariant in absolute scale; can be negative.

**Source use — context only.** Gaussian channel capacity.

**Amendment (FALSE_AS_STATED).** Differential entropy is translation invariant when defined: h(X+c)=h(X). Under nonsingular linear scaling h(AX)=h(X)+log|det A|. Both positive and negative infinite cases need domain conventions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I21.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i22"></a>

#### I22. `CMI` — conditional mutual information

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X × Y × Z) → R_+

**Source definition.** I(X;Y|Z) := E_Z [I(X;Y | Z=z)].

**Source property — not certified.** Chain rule: I(X;Y,Z) = I(X;Z) + I(X;Y|Z).

**Source use — context only.** Causal feature selection.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I22.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i23"></a>

#### I23. `Tot_corr` — total correlation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X_1 × ... × X_n) → R_+

**Source definition.** TC := H(X_1) + ... + H(X_n) - H(X_1,...,X_n).

**Source property — not certified.** Generalizes mutual information to multi-variable.

**Source use — context only.** Disentanglement in representation learning.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I23.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i24"></a>

#### I24. `Dual_tot` — dual total correlation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X_1×...×X_n) → R_+

**Source definition.** D_tot := H(joint) - Σ H(X_i | rest).

**Source property — not certified.** Vanishes iff factorization is conditionally independent.

**Source use — context only.** Multi-information decomposition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I24.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i25"></a>

#### I25. `Sync` — synergistic information

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (X_1, X_2; Y) → R_+

**Source definition.** Syn(X_1,X_2; Y) := I(X_1, X_2; Y) - max over redundancies.

**Source property — not certified.** Williams-Beer PID decomposition (one of several definitions).

**Source use — context only.** Partial-information decomposition in neuroscience.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I25.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i26"></a>

#### I26. `Red` — redundant information

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (X_1, X_2; Y) → R_+

**Source definition.** Red := common information across sources, formally I_min or related.

**Source property — not certified.** Lower bound on individual mutual informations.

**Source use — context only.** Shared-signal measurement.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I26.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i27"></a>

#### I27. `Channel_cap` — Shannon channel capacity

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Markov kernel K: X → Y → R_+

**Source definition.** C(K) := sup_{P_X} I(X; Y).

**Source property — not certified.** Achieved by some input distribution (compactness).

**Source use — context only.** Maximum reliable transmission rate.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I27.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i28"></a>

#### I28. `Rate-Dist` — rate-distortion function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X) × distortion d × D → R_+

**Source definition.** R(D) := inf_{P_{Ŷ|X} : E d ≤ D} I(X; Ŷ).

**Source property — not certified.** Convex, non-increasing in D; zero at D ≥ D_max.

**Source use — context only.** Lossy compression bounds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I28.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i29"></a>

#### I29. `F_I` — Fisher information

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X; θ) → SymPSD(d × d)

**Source definition.** I_F(θ)_{ij} := E [∂_i log p_θ · ∂_j log p_θ].

**Source property — not certified.** Local Riemannian metric on the statistical manifold.

**Source use — context only.** Cramér-Rao lower bound on estimator variance.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I29.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i30"></a>

#### I30. `ℋ` — von Neumann entropy

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** States on H → R_+

**Source definition.** S(ρ) := -tr(ρ log ρ).

**Source property — not certified.** Concave; equal to Shannon for diagonal ρ.

**Source use — context only.** Quantum information theory.

**QPT-128 substitution.** Use only through [A14](#a14), with each contract and its four research questions.

**Eligibility question for I30.** Does the operator improve conditional guessing probability or only a Shannon-entropy/visual statistic? Identify the exact role of this operator in that derivation.

<a id="op-i31"></a>

#### I31. `D_Umegaki` — Umegaki relative entropy

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** States × states → R_+

**Source definition.** D(ρ‖σ) := tr ρ(log ρ - log σ).

**Source property — not certified.** Quantum analog of KL; data-processing under CPTP maps.

**Source use — context only.** Quantum hypothesis testing.

**QPT-128 substitution.** Use only through [A20](#a20), with each contract and its four research questions.

**Eligibility question for I31.** Can a property-specific assumption and reduction cover the complete deployed hash interface and all its uses? Identify the exact role of this operator in that derivation.

<a id="op-i32"></a>

#### I32. `D_max` — max-divergence

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(X)² → R_+

**Source definition.** D_max(P‖Q) := log ess sup p/q.

**Source property — not certified.** Operationally tight in differential privacy.

**Source use — context only.** Privacy budget composition.

**QPT-128 substitution.** Use only through [A12](#a12), with each contract and its four research questions.

**Eligibility question for I32.** Does a proposed distribution-distance bound remain meaningful after adaptive quantum queries to its generating oracle? Identify the exact role of this operator in that derivation.

<a id="op-i33"></a>

#### I33. `D_min` — min-divergence

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Δ(X)² → R_+

**Source definition.** D_min(P‖Q) := -log P(supp Q).

**Source property — not certified.** Used in hypothesis-testing with type-II constraint.

**Source use — context only.** Hypothesis testing under prior mismatch.

**Amendment (FORMULA_ERROR).** For the classical order-zero divergence use D_0(P||Q)=-log Q(supp P). The source expression -log P(supp Q) reverses the arguments.

**QPT-128 substitution.** Use only through [A14](#a14), with each contract and its four research questions.

**Eligibility question for I33.** Which variable is secret, and what classical/quantum side information does E contain at the time of use? Identify the exact role of this operator in that derivation.

<a id="op-i34"></a>

#### I34. `D_smooth` — smooth divergence

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ × Δ × ε → R_+

**Source definition.** D^ε(P‖Q) := inf_{P' : D_TV(P,P') ≤ ε} D(P'‖Q).

**Source property — not certified.** Robustifies divergences to approximate measures.

**Source use — context only.** Cryptographic security against imperfect adversaries.

**QPT-128 substitution.** Use only through [A14](#a14), [A25](#a25), with each contract and its four research questions.

**Eligibility question for I34.** Does the operator improve conditional guessing probability or only a Shannon-entropy/visual statistic? Identify the exact role of this operator in that derivation.

<a id="op-i35"></a>

#### I35. `Conv_I` — information bottleneck operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X × Y) × β → Δ(T)

**Source definition.** IB(β) := arg min I(X;T) - β I(T;Y).

**Source property — not certified.** Lagrangian trade-off; β = 0 gives constant T, β → ∞ retains Y info.

**Source use — context only.** Representation learning.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I35.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i36"></a>

#### I36. `D_χ², ` — chi-squared divergence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X)² → R_+

**Source definition.** χ²(P‖Q) := ∫ (p - q)²/q dμ.

**Source property — not certified.** Upper bound on KL when both are bounded; quadratic approximation.

**Source use — context only.** Goodness-of-fit tests.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I36.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i37"></a>

#### I37. `D_JS` — Jensen-Shannon divergence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(X)² → [0, log 2]

**Source definition.** JS(P,Q) := (1/2) D_KL(P‖M) + (1/2) D_KL(Q‖M), M = (P+Q)/2.

**Source property — not certified.** Symmetric; square root is a metric.

**Source use — context only.** Distribution comparison in NLP.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I37.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i38"></a>

#### I38. `D_Renyi^∞` — max-entropy divergence

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ × Δ → R_+

**Source definition.** D_∞(P‖Q) := log ess sup p/q.

**Source property — not certified.** Limit of D_α as α → ∞.

**Source use — context only.** Worst-case privacy leakage.

**QPT-128 substitution.** Use only through [A12](#a12), with each contract and its four research questions.

**Eligibility question for I38.** Are reductions using the identical challenge map and domain separation as the verifier? Identify the exact role of this operator in that derivation.

<a id="op-i39"></a>

#### I39. `MMD` — maximum mean discrepancy

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(X)² × RKHS → R_+

**Source definition.** MMD(P,Q) := sup_{‖f‖_H ≤ 1} |E_P f - E_Q f|.

**Source property — not certified.** Metric if kernel is characteristic.

**Source use — context only.** Two-sample testing in kernel methods.

**QPT-128 substitution.** Use only through [A20](#a20), with each contract and its four research questions.

**Eligibility question for I39.** Can a property-specific assumption and reduction cover the complete deployed hash interface and all its uses? Identify the exact role of this operator in that derivation.

<a id="op-i40"></a>

#### I40. `EnergyDist` — energy distance

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(R^d)² → R_+

**Source definition.** ED(P,Q)² := 2 E ‖X - Y‖ - E ‖X - X'‖ - E ‖Y - Y'‖.

**Source property — not certified.** Special MMD with negative-distance kernel.

**Source use — context only.** Independence testing.

**QPT-128 substitution.** Use only through [A20](#a20), with each contract and its four research questions.

**Eligibility question for I40.** Do empirical output tests or a larger digest merely leave that computational premise untouched? Identify the exact role of this operator in that derivation.

<a id="op-i41"></a>

#### I41. `Var_KL` — variational lower bound (ELBO)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Posterior approx Q × evidence p(x) → R

**Source definition.** ELBO(Q) := E_Q log p(x, z) - E_Q log Q(z).

**Source property — not certified.** Bounds log p(x) from below; tight iff Q = posterior.

**Source use — context only.** Variational autoencoders.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I41.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i42"></a>

#### I42. `HSIC` — Hilbert-Schmidt independence criterion

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(X × Y) × kernels → R_+

**Source definition.** HSIC := ‖C_{XY}‖_HS², C_{XY} cross-covariance operator.

**Source property — not certified.** Zero iff X ⊥ Y for characteristic kernels.

**Source use — context only.** Kernel-based independence testing.

**QPT-128 substitution.** Use only through [A20](#a20), with each contract and its four research questions.

**Eligibility question for I42.** Is a random ideal permutation being silently replaced with the known Keccak permutation? Identify the exact role of this operator in that derivation.

<a id="op-i43"></a>

#### I43. `Fan_info` — Fano information bound

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Decoder mapping × channel → R_+

**Source definition.** P_e ≥ (H(X|Y) - 1) / log(|X| - 1).

**Source property — not certified.** Lower bound on error probability via conditional entropy.

**Source use — context only.** Coding lower bounds; minimax theory in statistics.

**Amendment (DOMAIN_GAP).** State Fano with binary logs, a finite alphabet of size at least three for this rearranged denominator, and a specified estimator. The binary case needs the usual binary-entropy form, not division by log(1).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I43.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i44"></a>

#### I44. `Cap_α` — α-capacity

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Channel × α → R_+

**Source definition.** C_α := sup_{P_X} I_α(X; Y).

**Source property — not certified.** Generalized channel capacity for Rényi info.

**Source use — context only.** Robust coding bounds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I44.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i45"></a>

#### I45. `BlockEnt` — block entropy rate

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Stationary process × n → R_+

**Source definition.** H_n := H(X_1,...,X_n)/n; H_∞ := lim H_n.

**Source property — not certified.** Decreasing in n; limit exists for stationary sources.

**Source use — context only.** Source coding for stationary processes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I45.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i46"></a>

#### I46. `Exch_perm` — permutation entropy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Time series × order n → R_+

**Source definition.** PE := -Σ_π p_π log p_π over ordinal patterns of length n.

**Source property — not certified.** Translation- and ordinal-monotone-invariant.

**Source use — context only.** Complexity quantification in physiological signals.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I46.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

<a id="op-i47"></a>

#### I47. `Lemp_compl` — Lempel-Ziv complexity

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Finite string → ℕ

**Source definition.** LZ(s) := number of distinct phrases in the LZ77 parsing.

**Source property — not certified.** Estimates the entropy rate.

**Source use — context only.** Universal data compression.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for I47.** Is the attack class being tested narrower than the QPT adversaries in the theorem? Identify the exact role of this operator in that derivation.

<a id="op-i48"></a>

#### I48. `Apx_ent` — approximate entropy

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Sequence × (m, r) → R

**Source definition.** ApEn := Φ^m(r) - Φ^{m+1}(r), Φ^m a sum-log over tolerance r matches.

**Source property — not certified.** Robust to noise; quantifies regularity.

**Source use — context only.** EEG and ECG signal analysis.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for I48.** What symbolic invariant learned from a failed test can subsequently be proved for all parameters? Identify the exact role of this operator in that derivation.

<a id="op-i49"></a>

#### I49. `Sample_ent` — sample entropy

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Sequence × (m, r) → R

**Source definition.** SampEn := -log(A/B), A and B m+1- and m-length match counts excluding self.

**Source property — not certified.** Bias-corrected variant of ApEn.

**Source use — context only.** Heart-rate variability.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for I49.** What failure modes can this experiment actually detect at its sample size? Identify the exact role of this operator in that derivation.

<a id="op-i50"></a>

#### I50. `Trans_ent` — transfer entropy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Pair of stochastic processes × lag → R_+

**Source definition.** TE_{X→Y} := H(Y_{t+1} | Y^t) - H(Y_{t+1} | Y^t, X^t).

**Source property — not certified.** Directional information flow; equals conditional MI.

**Source use — context only.** Causal-direction inference in neuroscience and finance.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for I50.** Does this information quantity control the required guessing or distinguishing game with quantum side information, rather than an unrelated average statistic?

### Family P: Paths and loops

<a id="op-p1"></a>

#### P1. `∫_γ` — line integral (scalar)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C(M) × Path(M) → R

**Source definition.** ∫_γ f := ∫_a^b f(γ(t)) |γ'(t)| dt.

**Source property — not certified.** Reparameterization-invariant.

**Source use — context only.** Arc-length functionals in geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P1.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p2"></a>

#### P2. `∫_γ ω` — differential-form integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Ω^1(M) × Path(M) → R

**Source definition.** ∫_γ ω := ∫_a^b γ*ω.

**Source property — not certified.** Stokes: ∫_∂Σ ω = ∫_Σ dω.

**Source use — context only.** Work integrals; circulation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P2.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p3"></a>

#### P3. `∮` — loop integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Ω^1(M) × Loop(M) → R

**Source definition.** ∮_γ ω := ∫_γ ω for closed γ.

**Source property — not certified.** Vanishes if ω is exact (Poincaré lemma).

**Source use — context only.** Residue calculus; magnetic flux.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P3.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p4"></a>

#### P4. `Hol_∇` — holonomy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Conn(E) × Loop_x(M) → GL(E_x)

**Source definition.** Hol_∇(γ) := P-exp(-∮_γ A), A the connection 1-form.

**Source property — not certified.** Group homomorphism from loop monoid to gauge group; trivial iff ∇ is flat and M is simply connected.

**Source use — context only.** Gauge fields; Berry phase.

**Amendment (FALSE_AS_STATED).** Trivial holonomy does not require a simply connected base: a trivial connection on a trivial bundle over a circle is a counterexample. Flatness plus simple connectivity is a sufficient condition, not the asserted equivalence.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P4.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p5"></a>

#### P5. `P-exp` — path-ordered exponential

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Path × Lie-algebra valued 1-form → group element

**Source definition.** P-exp(∫_γ A) := lim Π_i exp(A(γ(t_i)) Δt_i).

**Source property — not certified.** Solves dU/dt = A(t) U(t) along the path.

**Source use — context only.** Wilson lines in gauge theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P5.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p6"></a>

#### P6. `PT_∇` — parallel transport

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Conn × Path → linear iso

**Source definition.** PT_∇(γ): E_{γ(a)} → E_{γ(b)} solves ∇_{γ'} σ = 0.

**Source property — not certified.** Group cocycle in γ; coincides with holonomy for loops.

**Source use — context only.** Geometric phases.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P6.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p7"></a>

#### P7. `⟲_x_0` — loop concatenation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Loop_x(M)² → Loop_x(M)

**Source definition.** (γ ⟲ δ)(t) := γ(2t) if t ≤ 1/2, else δ(2t-1).

**Source property — not certified.** Endows Loop_x(M) with topological-monoid structure; π_1 modulo homotopy.

**Source use — context only.** Fundamental group construction.

**Amendment (DOMAIN_GAP).** Fixed-interval concatenation is associative only up to reparameterization. Use Moore paths for strict associativity. Paths with varying endpoints give a groupoid after homotopy, not a single group.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P7.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p8"></a>

#### P8. `⟲̄` — loop inversion

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Loop_x(M) → Loop_x(M)

**Source definition.** γ̄(t) := γ(1 - t).

**Source property — not certified.** Group inverse modulo homotopy.

**Source use — context only.** Loop-space dualities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P8.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p9"></a>

#### P9. `Σ` — path concatenation

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Path × Path (endpoints match) → Path

**Source definition.** (γ ∘ δ)(t) := γ(2t) if t ≤ 1/2, else δ(2t-1).

**Source property — not certified.** Associative up to reparameterization; group structure after homotopy.

**Source use — context only.** Path algebras.

**Amendment (DOMAIN_GAP).** Fixed-interval concatenation is associative only up to reparameterization. Use Moore paths for strict associativity. Paths with varying endpoints give a groupoid after homotopy, not a single group.

**QPT-128 substitution.** Use only through [A18](#a18), with each contract and its four research questions.

**Eligibility question for P9.** Which committed values does D contain and which deterministic algorithm reconstructs each complete witness? Identify the exact role of this operator in that derivation.

<a id="op-p10"></a>

#### P10. `⨏_path` — average over paths

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Path-space × measure → R

**Source definition.** ⟨F⟩ := ∫ F[γ] dμ(γ).

**Source property — not certified.** Functional integral; for Brownian motion gives heat-equation evaluation.

**Source use — context only.** Feynman path integral.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P10.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p11"></a>

#### P11. `Wils_γ` — Wilson loop

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Conn × Loop × rep ρ → C

**Source definition.** W_ρ(γ) := tr_ρ Hol_∇(γ).

**Source property — not certified.** Gauge invariant; basis for observables in lattice gauge theory.

**Source use — context only.** Confinement criteria in QCD.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P11.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p12"></a>

#### P12. `Polyakov` — Polyakov loop

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Conn on S^1 × X × rep → C

**Source definition.** Polyakov := tr ρ(Hol around the time circle).

**Source property — not certified.** Order parameter for confinement-deconfinement.

**Source use — context only.** Finite-temperature gauge theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P12.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p13"></a>

#### P13. `dev_γ` — Cartan development

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Path in M × Cartan-geometry → path in model space

**Source definition.** dev_γ unrolls a path in M to one in the model G/H.

**Source property — not certified.** Inverse to monodromy in flat Cartan geometry.

**Source use — context only.** Rolling-ball kinematics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P13.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p14"></a>

#### P14. `End_path` — endpoint evaluation

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Path(M) × {0, 1} → M

**Source definition.** End_t γ := γ(t).

**Source property — not certified.** Fiber bundle Path(M) → M × M.

**Source use — context only.** Two-point boundary problems.

**QPT-128 substitution.** Use only through [A18](#a18), with each contract and its four research questions.

**Eligibility question for P14.** Are the two roots, public statements and witness encodings uniquely tied to the same roster and epoch? Identify the exact role of this operator in that derivation.

<a id="op-p15"></a>

#### P15. `Loop_op` — loop space construction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Pointed top space → topological space

**Source definition.** Ω M := { γ ∈ Path(M) : γ(0) = γ(1) = x_0 }.

**Source property — not certified.** ΩΣX is weakly equivalent to ⨁ Σ^k X^k (James splitting).

**Source use — context only.** Homotopy theory; π_n(M) = π_{n-1}(ΩM).

**Amendment (FORMULA_ERROR).** The James splitting is a suspension splitting under its hypotheses; do not identify Omega Sigma X directly with the unsuspended direct sum written here.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P15.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p16"></a>

#### P16. `Chen` — Chen iterated integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ω_1,...,ω_k × γ → R

**Source definition.** ∫_γ ω_1 ω_2 ... ω_k := ∫_{0 ≤ t_1 ≤ ... ≤ t_k ≤ 1} γ*ω_1(t_1) ... γ*ω_k(t_k).

**Source property — not certified.** Generates cohomology of loop space via shuffle algebra.

**Source use — context only.** Rational-homotopy theory; rough-path signatures.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P16.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p17"></a>

#### P17. `Sig` — path signature

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Bounded-variation path × → tensor series

**Source definition.** S(γ) := (1, ∫dγ, ∫∫dγ⊗dγ, ...) ∈ ⨁ V^{⊗n}.

**Source property — not certified.** Determines γ up to tree-like equivalence (Hambly-Lyons).

**Source use — context only.** Rough paths and machine learning for time series.

**Amendment (TYPE_GAP).** An infinite path signature belongs to a completed tensor algebra/product with a convergence convention, not a finite direct sum. A rough-path signature is not an authentication signature.

**QPT-128 substitution.** Use only through [A19](#a19), with each contract and its four research questions.

**Eligibility question for P17.** Does the requested conflict extractor have public certificates only, or is it allowed a trapdoor? Identify the exact role of this operator in that derivation.

<a id="op-p18"></a>

#### P18. `Log_sig` — log-signature

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Path × → Lie series

**Source definition.** logSig(γ) := log of signature in tensor algebra.

**Source property — not certified.** Lives in free Lie algebra (Chen-Strichartz).

**Source use — context only.** Efficient path features.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P18.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p19"></a>

#### P19. `Mon_g` — monodromy of flat connection

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Flat conn × π_1 → group

**Source definition.** Mon_g: π_1(M, x_0) → G/H given by Hol_∇.

**Source property — not certified.** Representation of π_1; equivalent to ∇ up to gauge.

**Source use — context only.** Riemann-Hilbert correspondence.

**Amendment (TYPE_GAP).** Holonomy of a flat principal G-connection yields a representation of pi_1 into G (up to conjugation), not generally into the coset space G/H.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P19.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p20"></a>

#### P20. `Per_g` — period mapping

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Polarized Hodge structure × loop → matrix

**Source definition.** Per(γ) := matrix of integrals ∫_{γ_i} ω_j.

**Source property — not certified.** Differentiates with respect to moduli (Griffiths transversality).

**Source use — context only.** Hodge theory of families.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P20.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p21"></a>

#### P21. `ζ_path` — path zeta function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Graph × paths → power series

**Source definition.** ζ(s) := Π_p (1 - N(p)^{-s})^{-1}, p closed geodesics.

**Source property — not certified.** Ihara-zeta on graphs; analog of Selberg zeta.

**Source use — context only.** Graph isospectral problems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P21.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p22"></a>

#### P22. `Tr_pt` — trace as path-sum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Square matrix → C

**Source definition.** tr(M^k) = Σ_{closed walks of length k} weight.

**Source property — not certified.** Combinatorial cycle interpretation.

**Source use — context only.** Random matrix theory limits.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P22.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p23"></a>

#### P23. `Mor_op` — Morse path operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Critical points × → ×

**Source definition.** Mor counts (modulo signs) gradient flow lines between critical points.

**Source property — not certified.** Squares to zero ⇒ chain complex.

**Source use — context only.** Morse homology of M.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P23.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p24"></a>

#### P24. `⨯_braid` — braid composition

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B_n × B_n → B_n

**Source definition.** (σ_i)(σ_j) by stacking; σ_i σ_j = σ_j σ_i for |i-j| ≥ 2; σ_i σ_{i+1} σ_i = σ_{i+1} σ_i σ_{i+1}.

**Source property — not certified.** Defines the braid group on n strands.

**Source use — context only.** Topological quantum computation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P24.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p25"></a>

#### P25. `Linkno` — linking number

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (γ_1, γ_2) disjoint loops in R^3 → Z

**Source definition.** lk(γ_1, γ_2) := (1/4π) ∮∮ (γ_1 - γ_2) · (dγ_1 × dγ_2) / |γ_1 - γ_2|^3.

**Source property — not certified.** Topological invariant.

**Source use — context only.** DNA supercoiling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P25.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p26"></a>

#### P26. `Jones_q` — Jones polynomial as braid trace

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B_n × q → polynomial

**Source definition.** J(γ) := Markov trace of Burau-like representation.

**Source property — not certified.** Knot invariant up to Markov moves.

**Source use — context only.** Knot classification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P26.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p27"></a>

#### P27. `HOMFLY` — HOMFLY polynomial operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Oriented links × → Z[ℓ^{±1}, m^{±1}]

**Source definition.** Skein relation: ℓ P(L_+) + ℓ^{-1} P(L_-) + m P(L_0) = 0.

**Source property — not certified.** Specializes to Jones, Alexander.

**Source use — context only.** Link invariants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P27.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p28"></a>

#### P28. `Path_α` — α-Hölder path operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** C^α-path → ×

**Source definition.** Maps γ to the smallest Hölder constant in [a,b].

**Source property — not certified.** Detects rough paths; α = 1/2 for Brownian motion.

**Source use — context only.** Rough-path theory.

**Amendment (FALSE_AS_STATED).** Brownian sample paths are locally alpha-Holder for every alpha<1/2, but not generally at alpha=1/2. Do not use the endpoint as a deterministic Holder bound.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P28.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p29"></a>

#### P29. `StoIto_γ` — Itô line integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Adapted process × Brownian path → random variable

**Source definition.** ∫_0^t φ_s dB_s := L²-limit of forward Riemann sums.

**Source property — not certified.** Itô isometry; martingale property.

**Source use — context only.** Stochastic calculus.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P29.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p30"></a>

#### P30. `Strat_γ` — Stratonovich line integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** ∫_0^t φ_s ∘ dB_s := lim of midpoint Riemann sums.

**Source property — not certified.** Satisfies ordinary chain rule; differs from Itô by a quadratic-variation term.

**Source use — context only.** Geometric stochastic differential equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P30.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p31"></a>

#### P31. `MAG_γ` — magnetic Laplacian path-amplitude

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Path × magnetic 1-form A → C

**Source definition.** M_γ := exp(i ∫_γ A).

**Source property — not certified.** Aharonov-Bohm phase; gauge-dependent.

**Source use — context only.** Quantum mechanics in magnetic fields.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P31.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p32"></a>

#### P32. `∮_∂` — boundary loop operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Σ ⊂ M → ∂Σ ⊂ M

**Source definition.** ∮_∂(Σ) := boundary loop of an oriented surface.

**Source property — not certified.** Adjoint to ∂̄ in surface chains.

**Source use — context only.** Stokes' theorem decomposition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P32.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p33"></a>

#### P33. `FundGrpd` — fundamental groupoid

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Top space → category

**Source definition.** Π_1(M) := paths up to homotopy rel endpoints.

**Source property — not certified.** Equivalent to π_1 in connected case as a one-object groupoid.

**Source use — context only.** Categorical foundations of homotopy.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P33.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p34"></a>

#### P34. `WLN_q` — Wilson lattice operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lattice × link → group element

**Source definition.** U_l := e^{i a A · ê_l} on each link l.

**Source property — not certified.** Building block of lattice gauge action.

**Source use — context only.** Numerical lattice QCD.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P34.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p35"></a>

#### P35. `Plaq` — plaquette operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lattice × face → group element

**Source definition.** P_□ := U_1 U_2 U_3^{-1} U_4^{-1} (around a face).

**Source property — not certified.** Discrete curvature; tr P_□ in Wilson action.

**Source use — context only.** Lattice gauge field strength.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P35.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p36"></a>

#### P36. `Path_decomp` — Hodge path decomposition

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Path-form pairs × → harmonic + exact + co-exact

**Source definition.** Decomposes ω restricted to γ via Hodge along γ.

**Source property — not certified.** Unique on closed manifolds (Hodge theorem).

**Source use — context only.** Topological invariants of holographies.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P36.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p37"></a>

#### P37. `Stokes_op` — Stokes operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Ω^k(M) × Σ → R

**Source definition.** Stokes(ω, Σ) := ∫_{∂Σ} ω - ∫_Σ dω = 0.

**Source property — not certified.** Equality is Stokes' theorem.

**Source use — context only.** Conservation laws.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P37.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p38"></a>

#### P38. `dR_γ` — de Rham path-restriction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Ω^*(M) × γ → Ω^*([0,1])

**Source definition.** dR_γ(ω) := γ*ω.

**Source property — not certified.** Chain map respecting d.

**Source use — context only.** Induced cohomology on path subspaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P38.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p39"></a>

#### P39. `⨯_Tor` — Toric flux

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** T^n × form → R

**Source definition.** Tor(ω) := ∫_{T^n} ω.

**Source property — not certified.** Period over toric cycle.

**Source use — context only.** Quantization of flux in compact gauge directions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P39.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p40"></a>

#### P40. `Path_curv` — geodesic curvature

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Curve in Riemannian manifold → function

**Source definition.** κ_g(γ)(t) := |∇_{γ'} γ'|.

**Source property — not certified.** Vanishes iff γ is a geodesic.

**Source use — context only.** Geodesic-flow analysis.

**Amendment (DOMAIN_GAP).** For the given curvature magnitude use unit-speed curves. Vanishing covariant acceleration characterizes affinely parameterized geodesics; arbitrary reparameterizations need speed corrections.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P40.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p41"></a>

#### P41. `Tor_γ` — torsion of curve

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^3 curve in R^3 → function

**Source definition.** τ := (γ' × γ'') · γ''' / |γ' × γ''|².

**Source property — not certified.** Vanishes iff γ is planar.

**Source use — context only.** Frenet-Serret formulas.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P41.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p42"></a>

#### P42. `StRing` — string operator (Chas-Sullivan)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Free loop space × → string product

**Source definition.** ★: H_*(LM) × H_*(LM) → H_*(LM) using intersection at coincident points.

**Source property — not certified.** Makes H_*(LM) into Batalin-Vilkovisky algebra.

**Source use — context only.** Topological string theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P42.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p43"></a>

#### P43. `⨯_open` — open-string concatenation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Paths with boundary conditions × → ×

**Source definition.** γ_1 ★ γ_2 by joining endpoints in D-brane.

**Source property — not certified.** Associative A_∞-structure with higher operations.

**Source use — context only.** String field theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P43.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p44"></a>

#### P44. `PathInt_∂` — path-integral boundary state

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Boundary state × evolution → ×

**Source definition.** |ψ_∂⟩ := exp(-i H T) |ψ_0⟩ evaluated as path integral.

**Source property — not certified.** Connects field theory to quantum mechanics.

**Source use — context only.** Holographic correspondence.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P44.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p45"></a>

#### P45. `⨴_BrSph` — Brownian sphere area

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Brownian path of duration t → random variable

**Source definition.** ∫_0^t |dB_s|^2 = t (a.s.).

**Source property — not certified.** Quadratic variation of B is deterministic.

**Source use — context only.** Itô calculus core identity.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P45.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p46"></a>

#### P46. `Walsh_path` — Walsh-spider operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Half-line × angles → diffusion

**Source definition.** Walsh process at 0 sends path to a random ray with prescribed weights.

**Source property — not certified.** Generator is a Walsh's spider operator.

**Source use — context only.** Limits of multi-skewed Brownian motion.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P46.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p47"></a>

#### P47. `Loop_grp` — loop group element

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Smooth maps S^1 → G

**Source definition.** Composition pointwise.

**Source property — not certified.** Central extensions classified by H^3(G).

**Source use — context only.** Affine Lie algebras.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P47.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p48"></a>

#### P48. `⨯_LG` — loop-group product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** LG² → LG

**Source definition.** (g, h)(θ) := g(θ) h(θ).

**Source property — not certified.** Coboundary structure for level-k extensions.

**Source use — context only.** Conformal field theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P48.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p49"></a>

#### P49. `⨴_period` — period homomorphism

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** H_1(M) × H^1(M) → R

**Source definition.** (γ, ω) ↦ ∫_γ ω.

**Source property — not certified.** Perfect pairing in de Rham cohomology.

**Source use — context only.** Integration on cycles.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P49.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

<a id="op-p50"></a>

#### P50. `Pol_K` — polynomial-loop operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Polynomial path × form → R^d-valued integral

**Source definition.** Pol_K(γ, ω) := ∫_γ K(t) ω(γ(t)) dt for some kernel K.

**Source property — not certified.** Used in regularity-structure theory.

**Source use — context only.** Renormalization of singular SPDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for P50.** Is there an explicit finite transcript/state evolution represented by this path operator, and what map preserves the required security event?

### Family S: Spectral operators

<a id="op-s1"></a>

#### S1. `σ` — spectrum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B(H) → closed subset of C

**Source definition.** σ(T) := { λ ∈ C : T - λI not invertible }.

**Source property — not certified.** Compact and non-empty for bounded T.

**Source use — context only.** Stability of linear systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S1.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s2"></a>

#### S2. `σ_p` — point spectrum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B(H) → subset of C

**Source definition.** σ_p(T) := { λ : ker(T - λ) ≠ 0 }.

**Source property — not certified.** Subset of σ(T); eigenvalues.

**Source use — context only.** Modal analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S2.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s3"></a>

#### S3. `σ_c` — continuous spectrum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** B(H) → ×

**Source definition.** σ_c(T) := { λ : ran(T - λ) dense, T - λ injective but not surjective }.

**Source property — not certified.** Disjoint from σ_p and σ_r.

**Source use — context only.** Scattering in quantum mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S3.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s4"></a>

#### S4. `σ_r` — residual spectrum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** B(H) → ×

**Source definition.** σ_r(T) := { λ : T - λ injective, ran(T - λ) not dense }.

**Source property — not certified.** Empty for self-adjoint and normal operators.

**Source use — context only.** Operator-theoretic classification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S4.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s5"></a>

#### S5. `σ_ess` — essential spectrum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B(H) → C

**Source definition.** σ_ess(T) := { λ : T - λ not Fredholm }.

**Source property — not certified.** Invariant under compact perturbation (Weyl).

**Source use — context only.** Asymptotic analysis of differential operators.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S5.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s6"></a>

#### S6. `R_λ` — resolvent

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B(H) × ρ(T) → B(H)

**Source definition.** R_λ(T) := (T - λI)^{-1}.

**Source property — not certified.** Analytic in λ on the resolvent set; first resolvent identity holds.

**Source use — context only.** Functional calculus.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S6.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s7"></a>

#### S7. `ρ` — spectral radius

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** B(H) → R_+

**Source definition.** ρ(T) := sup{ |λ| : λ ∈ σ(T) }.

**Source property — not certified.** Equals lim ‖T^n‖^{1/n} (Gelfand).

**Source use — context only.** Convergence of Neumann series.

**QPT-128 substitution.** Use only through [A09](#a09), with each contract and its four research questions.

**Eligibility question for S7.** If a weighted norm contracts, what factor converts its bound back to physical trace/probability? Identify the exact role of this operator in that derivation.

<a id="op-s8"></a>

#### S8. `f(T)` — Borel functional calculus

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Self-adjoint T × Borel function → B(H)

**Source definition.** f(T) := ∫ f(λ) dE(λ).

**Source property — not certified.** *-homomorphism on bounded Borel functions.

**Source use — context only.** Construction of evolution semigroups.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S8.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s9"></a>

#### S9. `E(λ)` — spectral measure

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Self-adjoint T × Borel(R) → projections

**Source definition.** T = ∫ λ dE(λ); E(A) is the projection onto a spectral subspace.

**Source property — not certified.** Resolution of the identity.

**Source use — context only.** Quantum measurement postulate.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for S9.** Can both verifiers run before the one terminal database measurement in the intended security game? Identify the exact role of this operator in that derivation.

<a id="op-s10"></a>

#### S10. `⨃_⊕` — spectral decomposition (compact normal)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Compact normal T → ⨁ eigenspaces

**Source definition.** T = Σ λ_n P_n with Σ P_n = I.

**Source property — not certified.** Eigenvalues accumulate only at 0.

**Source use — context only.** PCA on covariance operators.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S10.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s11"></a>

#### S11. `μ_n(T)` — n-th singular value

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Compact T × ℕ → R_+

**Source definition.** μ_n(T) := n-th eigenvalue of √(T*T) in decreasing order.

**Source property — not certified.** ‖T‖_p = (Σ μ_n^p)^{1/p}; Schatten norms.

**Source use — context only.** Low-rank approximation.

**QPT-128 substitution.** Use only through [A06](#a06), with each contract and its four research questions.

**Eligibility question for S11.** Does the certificate remain valid with an arbitrary entangled reference system? Identify the exact role of this operator in that derivation.

<a id="op-s12"></a>

#### S12. `Tr` — trace operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Trace-class operators → C

**Source definition.** Tr T := Σ ⟨e_n, T e_n⟩ for any ONB.

**Source property — not certified.** Basis-independent; cyclic.

**Source use — context only.** Quantum statistical mechanics.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for S12.** Does the application require continuing with the same quantum oracle after extraction, which needs a stronger theorem? Identify the exact role of this operator in that derivation.

<a id="op-s13"></a>

#### S13. `Det` — Fredholm determinant

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** I + trace-class → C

**Source definition.** det(I + A) := Π (1 + λ_n(A)).

**Source property — not certified.** Multiplicative: det(I+A)(I+B) = det((I+A)(I+B)).

**Source use — context only.** Random-matrix gap probabilities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S13.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s14"></a>

#### S14. `Index` — Fredholm index

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Fredholm operators → Z

**Source definition.** ind(T) := dim ker T - dim coker T.

**Source property — not certified.** Homotopy invariant; stable under compact perturbation.

**Source use — context only.** Atiyah-Singer index theorem.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S14.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s15"></a>

#### S15. `‖·‖_p` — Schatten p-norm

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Compact operators × [1, ∞] → R_+ ∪ {∞}

**Source definition.** ‖T‖_p := (Σ μ_n^p)^{1/p}.

**Source property — not certified.** Forms a Banach space S_p; trace class = S_1, Hilbert-Schmidt = S_2.

**Source use — context only.** Operator approximation in machine learning.

**QPT-128 substitution.** Use only through [A06](#a06), [A07](#a07), with each contract and its four research questions.

**Eligibility question for S15.** Does the certificate remain valid with an arbitrary entangled reference system? Identify the exact role of this operator in that derivation.

<a id="op-s16"></a>

#### S16. `Sp_pol` — polar decomposition

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** B(H) → unitary × positive

**Source definition.** T = U |T|, U partial isometry, |T| = √(T*T).

**Source property — not certified.** Unique on ran|T|.

**Source use — context only.** Singular value decomposition.

**Amendment (TYPE_GAP).** The polar factor U is a partial isometry; it need not be unitary. Match the signature to the definition.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for S16.** Does the application require continuing with the same quantum oracle after extraction, which needs a stronger theorem? Identify the exact role of this operator in that derivation.

<a id="op-s17"></a>

#### S17. `Schur_T` — Schur decomposition (matrix)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^{n×n} → unitary × upper triangular

**Source definition.** A = UTU* with T upper triangular, U unitary.

**Source property — not certified.** Always exists; diagonal of T is σ(A).

**Source use — context only.** Eigenvalue computation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S17.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s18"></a>

#### S18. `Jordan` — Jordan canonical form

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C^{n×n} → block diagonal

**Source definition.** A = P J P^{-1} with J Jordan blocks.

**Source property — not certified.** Unique up to block ordering; basis-dependent.

**Source use — context only.** Solving linear ODEs.

**QPT-128 substitution.** Use only through [A09](#a09), with each contract and its four research questions.

**Eligibility question for S18.** Do truncation or Krylov residuals hide a larger singular value? Identify the exact role of this operator in that derivation.

<a id="op-s19"></a>

#### S19. `RayQuot` — Rayleigh quotient

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Hermitian A × C^n \ {0} → R

**Source definition.** R(x) := ⟨Ax, x⟩ / ⟨x, x⟩.

**Source property — not certified.** min-max over k-dim subspaces gives k-th eigenvalue (Courant-Fischer).

**Source use — context only.** Eigenvalue estimation by iteration.

**QPT-128 substitution.** Use only through [A06](#a06), [A07](#a07), with each contract and its four research questions.

**Eligibility question for S19.** Does the certificate remain valid with an arbitrary entangled reference system? Identify the exact role of this operator in that derivation.

<a id="op-s20"></a>

#### S20. `Min_max` — min-max characterization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Self-adjoint A × ℕ → R

**Source definition.** λ_k(A) := min over k-dim subspaces V of max_{x ∈ V} R(x).

**Source property — not certified.** Equivalent dual: max over (n-k+1)-codim of min.

**Source use — context only.** Variational principles in mechanics.

**Amendment (DIMENSION_ERROR).** For an n-dimensional Hermitian matrix and ascending eigenvalues, lambda_k=min_dim(V)=k max R and also max_dim(W)=n-k+1 min R. The latter is a dimension, not the codimension written in the source.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S20.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s21"></a>

#### S21. `Lan_op` — Lanczos tridiagonalization

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Hermitian A × starting vector → T (tridiagonal)

**Source definition.** Builds Krylov basis with three-term recurrence.

**Source property — not certified.** Preserves eigenvalues; numerically valuable.

**Source use — context only.** Iterative eigensolvers.

**Amendment (DOMAIN_GAP).** A truncated Krylov process gives Ritz values, not all original eigenvalues. Arnoldi has a residual term A Q_m=Q_m H_m+h_(m+1,m) q_(m+1) e_m^T unless the Krylov subspace is invariant.

**QPT-128 substitution.** Use only through [A09](#a09), with each contract and its four research questions.

**Eligibility question for S21.** Was an eigenvalue bound mistakenly used as a one-step failure-amplitude bound for a nonnormal matrix? Identify the exact role of this operator in that derivation.

<a id="op-s22"></a>

#### S22. `Arn_op` — Arnoldi reduction

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** General A × v → H (upper Hessenberg)

**Source definition.** Builds Krylov basis Q with AQ = QH.

**Source property — not certified.** Lanczos = Arnoldi for Hermitian A.

**Source use — context only.** Large-scale eigenproblems.

**Amendment (DOMAIN_GAP).** A truncated Krylov process gives Ritz values, not all original eigenvalues. Arnoldi has a residual term A Q_m=Q_m H_m+h_(m+1,m) q_(m+1) e_m^T unless the Krylov subspace is invariant.

**QPT-128 substitution.** Use only through [A09](#a09), with each contract and its four research questions.

**Eligibility question for S22.** Do truncation or Krylov residuals hide a larger singular value? Identify the exact role of this operator in that derivation.

<a id="op-s23"></a>

#### S23. `Krylov_n` — Krylov subspace

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (A, b, n) → subspace

**Source definition.** K_n(A, b) := span{b, Ab, ..., A^{n-1} b}.

**Source property — not certified.** Building block of iterative methods.

**Source use — context only.** GMRES, conjugate gradient.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S23.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s24"></a>

#### S24. `LU` — LU decomposition (with pivoting)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Square invertible matrix → (P, L, U)

**Source definition.** PA = LU, L unit lower triangular, U upper triangular.

**Source property — not certified.** Exists under generic conditions; pivoting for stability.

**Source use — context only.** Solving linear systems.

**QPT-128 substitution.** Use only through [A15](#a15), with each contract and its four research questions.

**Eligibility question for S24.** Can the entropy and rejection good-key events be intersected without invalidating either estimate? Identify the exact role of this operator in that derivation.

<a id="op-s25"></a>

#### S25. `Chol` — Cholesky decomposition

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Positive-definite → lower triangular

**Source definition.** A = L L*.

**Source property — not certified.** Faster and more stable than LU for SPD matrices.

**Source use — context only.** Gaussian random sampling.

**QPT-128 substitution.** Use only through [A15](#a15), with each contract and its four research questions.

**Eligibility question for S25.** Which rank deficiency controls the signature entropy estimate, over which field or module? Identify the exact role of this operator in that derivation.

<a id="op-s26"></a>

#### S26. `QR` — QR decomposition

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^{m×n} → Q × R

**Source definition.** A = QR, Q orthogonal, R upper triangular.

**Source property — not certified.** Existence; uniqueness with positive diagonal of R.

**Source use — context only.** Linear least squares.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S26.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s27"></a>

#### S27. `SVD` — singular value decomposition

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C^{m×n} → (U, Σ, V*)

**Source definition.** A = U Σ V*, Σ diagonal of σ_i ≥ 0.

**Source property — not certified.** Best low-rank approximation in ‖·‖_2 and ‖·‖_F (Eckart-Young).

**Source use — context only.** PCA, recommender systems.

**QPT-128 substitution.** Use only through [A06](#a06), [A07](#a07), with each contract and its four research questions.

**Eligibility question for S27.** Does the certificate remain valid with an arbitrary entangled reference system? Identify the exact role of this operator in that derivation.

<a id="op-s28"></a>

#### S28. `Trunc_k` — rank-k truncation

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** SVD × ℕ → low-rank matrix

**Source definition.** T_k(A) := Σ_{i=1}^k σ_i u_i v_i^*.

**Source property — not certified.** Minimizes ‖A - B‖_F over rank ≤ k.

**Source use — context only.** Image compression.

**QPT-128 substitution.** Use only through [A21](#a21), with each contract and its four research questions.

**Eligibility question for S28.** Would changing the sponge parameters change the protocol and its implementation compatibility obligations? Identify the exact role of this operator in that derivation.

<a id="op-s29"></a>

#### S29. `NNMF` — non-negative matrix factorization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Non-negative A × k → (W, H) ≥ 0

**Source definition.** A ≈ WH with W ∈ R_+^{m×k}, H ∈ R_+^{k×n}.

**Source property — not certified.** Solutions non-unique; multiplicative-update or ALS algorithms.

**Source use — context only.** Topic modeling, parts-based decomposition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S29.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s30"></a>

#### S30. `Pinv` — Moore-Penrose pseudoinverse

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C^{m×n} → C^{n×m}

**Source definition.** A^+ = V Σ^+ U*.

**Source property — not certified.** Unique solution to four Moore-Penrose conditions.

**Source use — context only.** Minimum-norm least squares.

**QPT-128 substitution.** Use only through [A15](#a15), with each contract and its four research questions.

**Eligibility question for S30.** Can the exact rank-count identity replace a loose union bound in that SAME distribution? Identify the exact role of this operator in that derivation.

<a id="op-s31"></a>

#### S31. `Speh` — specht-type norm

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Operators × Schur function → R_+

**Source definition.** Defines a unitary-invariant norm via symmetric gauge function.

**Source property — not certified.** Equivalent under permutation invariance to Schatten/Ky Fan norms.

**Source use — context only.** Matrix concentration inequalities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S31.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s32"></a>

#### S32. `KyFan_k` — Ky Fan k-norm

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Operators × ℕ → R_+

**Source definition.** ‖A‖_{(k)} := σ_1 + ... + σ_k.

**Source property — not certified.** Convex hull of partial-sums; subadditive.

**Source use — context only.** Sparse low-rank optimization.

**QPT-128 substitution.** Use only through [A06](#a06), with each contract and its four research questions.

**Eligibility question for S32.** Can an adversarial interleaving move amplitude into an unbounded subspace or reintroduce already removed failure paths? Identify the exact role of this operator in that derivation.

<a id="op-s33"></a>

#### S33. `Nucl` — nuclear (trace) norm

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Trace-class → R_+

**Source definition.** ‖A‖_* := Σ σ_n.

**Source property — not certified.** Convex relaxation of rank.

**Source use — context only.** Compressed sensing for matrices.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S33.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s34"></a>

#### S34. `Spect_gap` — spectral gap

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Self-adjoint compact operator → R_+

**Source definition.** γ(T) := λ_2 - λ_1 (or 1 - |λ_2|/|λ_1| for Markov operators).

**Source property — not certified.** Controls mixing time of associated random walk.

**Source use — context only.** Markov-chain convergence.

**QPT-128 substitution.** Use only through [A09](#a09), with each contract and its four research questions.

**Eligibility question for S34.** Do truncation or Krylov residuals hide a larger singular value? Identify the exact role of this operator in that derivation.

<a id="op-s35"></a>

#### S35. `RND_F` — free-probability spectral density

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Spectrum × support × → ×

**Source definition.** ν(t) := density of σ(A_n)/n as n → ∞.

**Source property — not certified.** Closed under free additive convolution.

**Source use — context only.** Asymptotic random matrix theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S35.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s36"></a>

#### S36. `Stiel` — Stieltjes transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ(R) × upper half-plane → upper half-plane

**Source definition.** G_μ(z) := ∫ dμ(λ)/(z - λ).

**Source property — not certified.** Inversion: μ has density (1/π) Im G_μ(t + i0).

**Source use — context only.** Random matrices, semicircle law.

**Amendment (SIGN_ERROR).** With G(z)=integral (z-lambda)^(-1)dmu(lambda), the upper half-plane maps to the lower half-plane; a density is -(1/pi)*Im G(t+i0) where the inversion limit is valid.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S36.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s37"></a>

#### S37. `R_transform` — R-transform (free probability)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ → analytic at 0

**Source definition.** R_μ(z) := G_μ^{-1}(z) - 1/z.

**Source property — not certified.** Additive under free convolution: R_{μ⊞ν} = R_μ + R_ν.

**Source use — context only.** Spectra of sums of asymptotically free matrices.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S37.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s38"></a>

#### S38. `S_transform` — S-transform (free probability)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Δ → ×

**Source definition.** S_μ(z) := (z+1)/z · ψ_μ^{-1}(z) where ψ_μ(z) := ∫ tz/(1-tz) dμ(t).

**Source property — not certified.** Multiplicative under free convolution.

**Source use — context only.** Wishart matrices.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S38.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s39"></a>

#### S39. `Mehler_op` — Mehler heat kernel

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × t → ×

**Source definition.** Reproduces (e^{-tH} ψ)(x) for harmonic oscillator H.

**Source property — not certified.** Closed-form Gaussian kernel.

**Source use — context only.** Coherent-state representations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S39.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s40"></a>

#### S40. `Bog_op` — Bogoliubov transformation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Symplectic × CCR-Fock → CCR-Fock

**Source definition.** Unitary implementing canonical (u, v) on creation/annihilation operators.

**Source property — not certified.** Implementable iff v ∈ Hilbert-Schmidt (Shale).

**Source use — context only.** Squeezed states in quantum optics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S40.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s41"></a>

#### S41. `BLA` — block Lanczos

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Hermitian A × block of vectors → block tridiagonal

**Source definition.** Block version of Lanczos.

**Source property — not certified.** Captures multiple eigenpairs per iteration.

**Source use — context only.** Multimodal eigenvalue search.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S41.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s42"></a>

#### S42. `Davidson` — Davidson preconditioner

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → expanded Krylov

**Source definition.** Includes diagonal preconditioning for clustered spectra.

**Source property — not certified.** Improved convergence for chemistry Hamiltonians.

**Source use — context only.** Quantum-chemistry eigensolvers.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S42.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s43"></a>

#### S43. `Inv_iter` — inverse iteration

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Approximate eigenvalue μ × → eigenvector

**Source definition.** v_{k+1} := (A - μI)^{-1} v_k / ‖...‖.

**Source property — not certified.** Cubic convergence near simple eigenvalues with Rayleigh-quotient shift.

**Source use — context only.** Eigenvector refinement.

**Amendment (DOMAIN_GAP).** Fixed-shift inverse iteration is generally linear; cubic local convergence of Rayleigh-quotient iteration needs suitable Hermitian/simple-eigenvalue assumptions. Do not import that rate for arbitrary matrices.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S43.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s44"></a>

#### S44. `Lanc_QR` — implicit-shift QR

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Upper Hessenberg matrix → Schur form

**Source definition.** QR iteration with multiple shifts and bulge chasing.

**Source property — not certified.** Workhorse for dense eigenproblems.

**Source use — context only.** LAPACK eigenvalue routines.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S44.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s45"></a>

#### S45. `Riccati` — Riccati operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Pair (A, B, C, Q, R) → P solving X A + A* X - X B R^{-1} B* X + Q = 0

**Source definition.** P is a self-adjoint solution; minimal positive solution under detectability.

**Source property — not certified.** Existence theory via stable invariant subspace of Hamiltonian.

**Source use — context only.** LQR/LQG optimal control.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S45.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s46"></a>

#### S46. `LyapEq` — Lyapunov equation operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** (A, Q) → P solving A* P + P A + Q = 0

**Source definition.** Unique solution when A stable (all σ(A) in left half-plane).

**Source property — not certified.** Vec-form gives Kronecker linear system.

**Source use — context only.** Stability certificates.

**QPT-128 substitution.** Use only through [A06](#a06), with each contract and its four research questions.

**Eligibility question for S46.** Can an exact positive-semidefinite certificate establish sum K* K<=beta I, rather than sampling a few vectors? Identify the exact role of this operator in that derivation.

<a id="op-s47"></a>

#### S47. `LRC` — Loewner reachability operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sampled transfer-function data → minimal model

**Source definition.** Builds Loewner / shifted-Loewner matrices and projects.

**Source property — not certified.** Data-driven realization.

**Source use — context only.** Reduced-order modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S47.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s48"></a>

#### S48. `Bal_red` — balanced truncation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Stable LTI system → reduced system

**Source definition.** Diagonalize controllability and observability Gramians simultaneously, truncate.

**Source property — not certified.** Error bound by twice the sum of neglected Hankel singular values.

**Source use — context only.** Model reduction in control.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S48.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s49"></a>

#### S49. `Hankel` — Hankel operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L^∞ × Hardy space → Hardy

**Source definition.** H_f(g) := P_- (f g).

**Source property — not certified.** Compact iff f ∈ H^∞ + C; ‖H_f‖ = dist(f, H^∞) (Nehari).

**Source use — context only.** Approximation theory and system identification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S49.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

<a id="op-s50"></a>

#### S50. `Toeplitz` — Toeplitz operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L^∞ × Hardy → Hardy

**Source definition.** T_f(g) := P_+ (f g).

**Source property — not certified.** Fredholm iff f bounded away from zero on T; index = -winding number of f.

**Source use — context only.** Wiener-Hopf factorization.

**Amendment (DOMAIN_GAP).** The usual nonvanishing-symbol/winding-number Fredholm criterion applies to continuous symbols. General L-infinity symbols need a more careful Toeplitz Fredholm criterion.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for S50.** Can this operator provide a certified bound for the full finite failure map, including residuals and the conversion to physical probability?

### Family M: Probability and measure

<a id="op-m1"></a>

#### M1. `E` — expectation

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** L^1(Ω, F, P) → R

**Source definition.** E[X] := ∫_Ω X dP.

**Source property — not certified.** Linear; positivity-preserving; ‖E‖ = 1.

**Source use — context only.** Statistical moments.

**QPT-128 substitution.** Use only through [A02](#a02), with each contract and its four research questions.

**Eligibility question for M1.** Can extractor failure, binding failure, signature forgery and truncation failure be defined on one coupled execution? Identify the exact role of this operator in that derivation.

<a id="op-m2"></a>

#### M2. `E[·|G]` — conditional expectation

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** L^1 × sub-σ-algebra → L^1

**Source definition.** E[X|G] := unique G-measurable Y with E[Y 1_A] = E[X 1_A] for A ∈ G.

**Source property — not certified.** L²-projection onto G-measurable functions; tower property.

**Source use — context only.** Filtering, martingale theory.

**QPT-128 substitution.** Use only through [A08](#a08), [A16](#a16), with each contract and its four research questions.

**Eligibility question for M2.** Can two individually half-probability failures be perfectly correlated in this protocol? Identify the exact role of this operator in that derivation.

<a id="op-m3"></a>

#### M3. `Var` — variance

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L² → R_+

**Source definition.** Var(X) := E[(X - E X)²].

**Source property — not certified.** Sub-additive in independence; affine: Var(aX+b) = a² Var(X).

**Source use — context only.** Risk quantification.

**Amendment (PRECISION).** For independent square-integrable real variables, Var(X+Y)=Var X+Var Y exactly. Without independence add twice the covariance.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M3.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m4"></a>

#### M4. `Cov` — covariance

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (L²)² → R

**Source definition.** Cov(X, Y) := E[XY] - E[X] E[Y].

**Source property — not certified.** Symmetric bilinear; |Cov| ≤ √(Var X · Var Y) (Cauchy-Schwarz).

**Source use — context only.** Linear-dependence measure.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M4.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m5"></a>

#### M5. `Q_α` — α-quantile

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ(R) × (0,1) → R

**Source definition.** Q_α(P) := inf{ x : F(x) ≥ α }.

**Source property — not certified.** Co-monotone; right-continuous in α.

**Source use — context only.** VaR in finance; robust statistics.

**Amendment (DIRECTION_ERROR).** The generalized inverse inf{x:F(x)>=alpha} is generally left-continuous in alpha, not right-continuous. A two-point distribution shows the jump direction.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M5.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m6"></a>

#### M6. `CVaR_α` — conditional value at risk

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R) × (0,1) → R

**Source definition.** CVaR_α(X) := (1/(1-α)) ∫_α^1 Q_u(X) du.

**Source property — not certified.** Coherent risk measure; tail-mean above Q_α.

**Source use — context only.** Expected-shortfall regulation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M6.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m7"></a>

#### M7. `M_p` — p-th moment

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L^p × ℕ → R

**Source definition.** M_p(X) := E[X^p].

**Source property — not certified.** M_p exists iff X ∈ L^p.

**Source use — context only.** Higher-order statistics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M7.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m8"></a>

#### M8. `Cum_n` — n-th cumulant

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L^∞ (mgf exists) × ℕ → R

**Source definition.** Cum_n := n-th coefficient of log E[e^{tX}].

**Source property — not certified.** Additive over independent sums.

**Source use — context only.** Free vs classical probability comparison.

**Amendment (NORMALIZATION).** The nth cumulant is the nth derivative of log M_X(t) at zero: its ordinary Taylor coefficient is kappa_n/n!, not kappa_n.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M8.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m9"></a>

#### M9. `Ψ` — characteristic function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R) × R → C

**Source definition.** ψ_X(t) := E[e^{itX}].

**Source property — not certified.** Continuous, ψ_X(0) = 1, positive-definite; injective into Δ(R).

**Source use — context only.** Convergence in distribution (Lévy).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M9.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m10"></a>

#### M10. `MGF` — moment generating function

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(R) × R → R ∪ {∞}

**Source definition.** M_X(t) := E[e^{tX}], when finite.

**Source property — not certified.** Determines distribution when finite on an interval around 0.

**Source use — context only.** Concentration inequalities.

**QPT-128 substitution.** Use only through [A13](#a13), with each contract and its four research questions.

**Eligibility question for M10.** At q_S<=2^64 and p<=759/1024, does R=519 suffice for a 2^-160 truncation budget and R=518 fail it? Identify the exact role of this operator in that derivation.

<a id="op-m11"></a>

#### M11. `CGF` — cumulant generating function

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ(R) → R ∪ {∞}

**Source definition.** K_X(t) := log M_X(t).

**Source property — not certified.** Convex; K(0) = 0; additive under independent sum.

**Source use — context only.** Large-deviation Cramér transform.

**QPT-128 substitution.** Use only through [A13](#a13), with each contract and its four research questions.

**Eligibility question for M11.** How does aborting after R attempts change signing correctness and the security experiment? Identify the exact role of this operator in that derivation.

<a id="op-m12"></a>

#### M12. `L*` — Cramér transform

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** CGF → rate function on R

**Source definition.** L*(x) := sup_t (tx - K(t)).

**Source property — not certified.** Legendre transform of K; convex, non-negative.

**Source use — context only.** Large-deviation principles.

**QPT-128 substitution.** Use only through [A13](#a13), with each contract and its four research questions.

**Eligibility question for M12.** For rejection sampling of challenges, are all additional oracle calls and possible adversarial retry choices counted? Identify the exact role of this operator in that derivation.

<a id="op-m13"></a>

#### M13. `Bayes` — Bayes operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Prior × likelihood → posterior

**Source definition.** π(θ | x) ∝ π(θ) L(x | θ).

**Source property — not certified.** Normalization via marginal m(x) = ∫ L π dθ.

**Source use — context only.** Bayesian inference.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M13.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m14"></a>

#### M14. `Mart` — martingale projection

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Adapted process × filtration → martingale

**Source definition.** M_t := E[X | F_t].

**Source property — not certified.** Closed if X ∈ L^1.

**Source use — context only.** Martingale representation in finance.

**QPT-128 substitution.** Use only through [A08](#a08), with each contract and its four research questions.

**Eligibility question for M14.** Can two individually half-probability failures be perfectly correlated in this protocol? Identify the exact role of this operator in that derivation.

<a id="op-m15"></a>

#### M15. `Doob_dec` — Doob decomposition

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Adapted L^1 process → (M, A)

**Source definition.** X_n = M_n + A_n, M martingale, A predictable.

**Source property — not certified.** Unique up to constant.

**Source use — context only.** Submartingale analysis.

**QPT-128 substitution.** Use only through [A08](#a08), with each contract and its four research questions.

**Eligibility question for M15.** Which information is visible when the next challenge is sampled? Identify the exact role of this operator in that derivation.

<a id="op-m16"></a>

#### M16. `Meyer_dec` — Doob-Meyer decomposition

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Cadlag submartingale → (M, A)

**Source definition.** Continuous-time version with predictable increasing A.

**Source property — not certified.** Existence and uniqueness under class (D).

**Source use — context only.** Foundations of stochastic calculus.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M16.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m17"></a>

#### M17. `It_int` — Itô integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Adapted L²-process × Brownian motion → continuous L²-martingale

**Source definition.** ∫_0^t H_s dB_s := L²-limit of simple processes.

**Source property — not certified.** Itô isometry: E (∫ H dB)² = E ∫ H² ds.

**Source use — context only.** Stochastic calculus foundation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M17.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m18"></a>

#### M18. `Strat_int` — Stratonovich integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Adapted × × → ×

**Source definition.** ∫_0^t H_s ∘ dB_s := ∫_0^t H_s dB_s + (1/2) [H, B]_t.

**Source property — not certified.** Satisfies ordinary chain rule.

**Source use — context only.** Geometric SDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M18.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m19"></a>

#### M19. `Cop` — copula operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Joint distribution on R^n → copula on [0,1]^n

**Source definition.** C(u_1, ..., u_n) := F(F_1^{-1}(u_1), ..., F_n^{-1}(u_n)) (Sklar).

**Source property — not certified.** Encapsulates all dependence; marginal-free.

**Source use — context only.** Multivariate risk modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M19.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m20"></a>

#### M20. `Surv` — survival function

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ([0,∞)) × t → [0,1]

**Source definition.** S(t) := 1 - F(t) = P(X > t).

**Source property — not certified.** Monotone, right-continuous, decreasing.

**Source use — context only.** Reliability and survival analysis.

**QPT-128 substitution.** Use only through [A13](#a13), with each contract and its four research questions.

**Eligibility question for M20.** For rejection sampling of challenges, are all additional oracle calls and possible adversarial retry choices counted? Identify the exact role of this operator in that derivation.

<a id="op-m21"></a>

#### M21. `Hazard` — hazard rate

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Δ([0,∞)) (abs continuous) × t → R_+

**Source definition.** h(t) := f(t)/S(t).

**Source property — not certified.** Cumulative hazard ∫_0^t h(s) ds = -log S(t).

**Source use — context only.** Proportional-hazards modeling.

**QPT-128 substitution.** Use only through [A13](#a13), with each contract and its four research questions.

**Eligibility question for M21.** Is the rejection probability bounded for every key in the SAME good-key event used by the signature reduction? Identify the exact role of this operator in that derivation.

<a id="op-m22"></a>

#### M22. `Mart_M` — Martingale measure (Lévy)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lévy process → adapted martingale

**Source definition.** M_t := X_t - E X_t.

**Source property — not certified.** Compensated process; fundamental in jump processes.

**Source use — context only.** Insurance reserves.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M22.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m23"></a>

#### M23. `Markov_semi` — Markov semigroup

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Markov kernel × t ≥ 0 → operator on bounded measurable functions

**Source definition.** P_t f(x) := E[f(X_t) | X_0 = x].

**Source property — not certified.** Strongly continuous in t under regularity; generator L = d/dt|_{t=0}.

**Source use — context only.** Continuous-time Markov-chain analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M23.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m24"></a>

#### M24. `Adj_K` — adjoint Markov kernel

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Markov kernel × measure → measure

**Source definition.** (K* μ)(A) := ∫ K(x, A) dμ(x).

**Source property — not certified.** Pushforward under K; preserves total mass.

**Source use — context only.** Invariant-measure equations: K* π = π.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M24.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m25"></a>

#### M25. `Cou_op` — coupling operator

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Δ(X) × Δ(Y) → Δ(X × Y)

**Source definition.** Cou(P, Q) := { π : Marg_X π = P, Marg_Y π = Q }.

**Source property — not certified.** Non-empty; coupling sets are convex.

**Source use — context only.** Total-variation comparisons.

**Amendment (TYPE_GAP).** The output is a set of joint distributions with specified marginals, not one distinguished distribution. A selection rule is additional data.

**QPT-128 substitution.** Use only through [A02](#a02), with each contract and its four research questions.

**Eligibility question for M25.** Can extractor failure, binding failure, signature forgery and truncation failure be defined on one coupled execution? Identify the exact role of this operator in that derivation.

<a id="op-m26"></a>

#### M26. `Rearr` — decreasing rearrangement

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R_+) → non-increasing function on R_+

**Source definition.** f*(t) := inf{ s : λ_f(s) ≤ t }, λ_f(s) := μ({|f| > s}).

**Source property — not certified.** Preserves L^p norms; building block of Lorentz spaces.

**Source use — context only.** Sharp inequalities (Hardy-Littlewood).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M26.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m27"></a>

#### M27. `Sym_rearr` — Schwarz symmetrization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L^1(R^n) → radial decreasing function

**Source definition.** f^* := unique radial decreasing function equimeasurable with |f|.

**Source property — not certified.** Decreases certain energies (Pólya-Szegő).

**Source use — context only.** Isoperimetric inequalities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M27.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m28"></a>

#### M28. `Choq` — Choquet integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Non-additive measure × non-neg function → R

**Source definition.** ∫_C f dν := ∫_0^∞ ν({f > t}) dt.

**Source property — not certified.** Co-monotone additivity; equals Lebesgue when ν is additive.

**Source use — context only.** Decision theory under ambiguity.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M28.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m29"></a>

#### M29. `Subm_cap` — submodular capacity

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 𝒫(X) → R_+

**Source definition.** ν(A ∪ B) + ν(A ∩ B) ≤ ν(A) + ν(B).

**Source property — not certified.** Concave-like; ⇒ diminishing returns.

**Source use — context only.** Cooperative-game theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M29.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m30"></a>

#### M30. `Shap` — Shapley value

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Cooperative game (N, v) → R^N

**Source definition.** φ_i(v) := Σ_{S ∋ i} weight · (v(S) - v(S \ {i})).

**Source property — not certified.** Unique efficient symmetric value satisfying additivity and dummy axiom.

**Source use — context only.** Fair attribution of model predictions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M30.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m31"></a>

#### M31. `Wass_cost` — Wasserstein cost operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (P, Q, c) → R_+

**Source definition.** W_c(P, Q) := inf_{π ∈ Cou(P,Q)} ∫ c(x,y) dπ.

**Source property — not certified.** Convex in (P, Q); duality with c-concave functions.

**Source use — context only.** Optimal transport.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M31.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m32"></a>

#### M32. `Sink` — Sinkhorn operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Joint × marginals → bi-stochastic

**Source definition.** Iterates row/column rescaling of e^{-c/ε}.

**Source property — not certified.** Converges to entropic-regularized OT plan; geometric rate.

**Source use — context only.** Differentiable optimal transport.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M32.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m33"></a>

#### M33. `Disint` — disintegration operator

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** P on X × Y → conditional kernel on X parameterized by Y

**Source definition.** Provides P_x ∈ Δ(Y) with P = ∫ P_x d(Marg_X P)(x).

**Source property — not certified.** Exists under regularity (Polish spaces).

**Source use — context only.** Sufficient-statistic decomposition.

**Amendment (TYPE_GAP).** Match conditioning direction: a kernel x -> P(Y in . | X=x) disintegrates against Marg_X(P), whereas a kernel y -> P(X in . | Y=y) uses Marg_Y(P).

**QPT-128 substitution.** Use only through [A08](#a08), [A16](#a16), with each contract and its four research questions.

**Eligibility question for M33.** Is the bound uniform over all reachable histories, including previous rejection outcomes? Identify the exact role of this operator in that derivation.

<a id="op-m34"></a>

#### M34. `Erg_mean` — ergodic average

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Bounded measurable × measure-preserving T × n → ×

**Source definition.** A_n f(x) := (1/n) Σ_{k=0}^{n-1} f(T^k x).

**Source property — not certified.** Converges a.s. and in L^1 (Birkhoff).

**Source use — context only.** Time-averages equal space-averages for ergodic T.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M34.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m35"></a>

#### M35. `Mix_op` — mixing operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Measure-preserving T × n → ×

**Source definition.** α(n) := sup |P(A ∩ T^{-n} B) - P(A) P(B)|.

**Source property — not certified.** Strong mixing iff α(n) → 0.

**Source use — context only.** CLT for dependent sequences.

**Amendment (DOMAIN_GAP).** Strong-mixing coefficients use specified separated past/future sigma-algebras. Taking the supremum over all measurable A and B is a different, generally much stronger condition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M35.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m36"></a>

#### M36. `PIT` — probability integral transform

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** X with CDF F → Uniform(0,1)

**Source definition.** U := F(X).

**Source property — not certified.** F continuous ⇒ U is Uniform(0,1).

**Source use — context only.** Quantile-based simulation.

**QPT-128 substitution.** Use only through [A12](#a12), with each contract and its four research questions.

**Eligibility question for M36.** Does a proposed distribution-distance bound remain meaningful after adaptive quantum queries to its generating oracle? Identify the exact role of this operator in that derivation.

<a id="op-m37"></a>

#### M37. `Inv_CDF` — inverse-CDF sampling

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Uniform U → X with CDF F

**Source definition.** X := F^{-1}(U).

**Source property — not certified.** U → F^{-1}(U) realizes F.

**Source use — context only.** Pseudo-random generation.

**QPT-128 substitution.** Use only through [A12](#a12), with each contract and its four research questions.

**Eligibility question for M37.** Is the hash input unambiguously bound to protocol version, roster, epoch, message and commitment? Identify the exact role of this operator in that derivation.

<a id="op-m38"></a>

#### M38. `MCMC_K` — Metropolis-Hastings kernel

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Target π × proposal Q → Markov kernel

**Source definition.** K(x, dy) := Q(x, dy) α(x, y) + δ_x · (rejection).

**Source property — not certified.** Stationary distribution π.

**Source use — context only.** Bayesian computation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M38.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m39"></a>

#### M39. `Lang_op` — Langevin operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Diff. potential U × T > 0 → SDE generator

**Source definition.** L f := -⟨∇U, ∇f⟩ + T Δf.

**Source property — not certified.** Generator of overdamped Langevin diffusion; e^{-U/T} invariant.

**Source use — context only.** MCMC, molecular dynamics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M39.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m40"></a>

#### M40. `HamMonte` — Hamiltonian Monte Carlo step

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (x, p) × leapfrog steps → (x', p')

**Source definition.** Integrates dx = ∂H/∂p, dp = -∂H/∂x with H = U(x) + (1/2)|p|².

**Source property — not certified.** Volume-preserving symplectic integrator.

**Source use — context only.** Sampling high-dim distributions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M40.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m41"></a>

#### M41. `Cad_emp` — empirical measure

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Samples × n → Δ(R^d)

**Source definition.** P̂_n := (1/n) Σ δ_{X_i}.

**Source property — not certified.** Glivenko-Cantelli: ‖P̂_n - P‖_∞ → 0 a.s.

**Source use — context only.** Non-parametric estimation.

**Amendment (TYPE_GAP).** Glivenko-Cantelli concerns empirical CDFs or specified Glivenko-Cantelli classes, not total variation of empirical and continuous probability measures. Their total variation is one at every finite sample size.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for M41.** What failure modes can this experiment actually detect at its sample size? Identify the exact role of this operator in that derivation.

<a id="op-m42"></a>

#### M42. `Bayes_pred` — Bayesian predictive

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Posterior × likelihood → predictive distribution

**Source definition.** p(x_new | data) = ∫ p(x_new | θ) π(θ | data) dθ.

**Source property — not certified.** Risk-optimal under squared error.

**Source use — context only.** Probabilistic forecasting.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M42.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m43"></a>

#### M43. `Filt_Kalman` — Kalman filter update

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Prior N(μ, Σ) × observation → posterior

**Source definition.** Updated mean and covariance via gain K = Σ H^T (H Σ H^T + R)^{-1}.

**Source property — not certified.** Optimal for linear Gaussian state-space models.

**Source use — context only.** Tracking and navigation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M43.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m44"></a>

#### M44. `Smooth_op` — Rauch-Tung-Striebel smoother

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Filtered means × → smoothed means

**Source definition.** Backward recursion using transition and filter.

**Source property — not certified.** Optimal smoother for linear Gaussian models.

**Source use — context only.** Trajectory reconstruction.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M44.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m45"></a>

#### M45. `Pred_op` — transition prediction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Filtered state × dynamics → forecast distribution

**Source definition.** Apply Markov kernel one step.

**Source property — not certified.** Gaussian remains Gaussian for linear systems.

**Source use — context only.** Operational forecasting.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M45.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

<a id="op-m46"></a>

#### M46. `U_stat_k` — U-statistic

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Kernel h × samples → R

**Source definition.** U_n := (1/C(n,k)) Σ_{i_1<...<i_k} h(X_{i_1},...,X_{i_k}).

**Source property — not certified.** Unbiased; minimum variance under symmetric kernels.

**Source use — context only.** Non-parametric tests, MMD estimators.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for M46.** Can a constructed rare event fool all empirical tests while violating the target bound? Identify the exact role of this operator in that derivation.

<a id="op-m47"></a>

#### M47. `Plugin` — plug-in estimator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Empirical measure × functional T → estimate

**Source definition.** T̂_n := T(P̂_n).

**Source property — not certified.** Consistent for Hadamard-differentiable T.

**Source use — context only.** Sample mean and variance.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for M47.** Is the attack class being tested narrower than the QPT adversaries in the theorem? Identify the exact role of this operator in that derivation.

<a id="op-m48"></a>

#### M48. `Boot_op` — bootstrap operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** P̂_n × B → empirical Δ(R^B)

**Source definition.** Draw B resamples X^*_b iid from P̂_n and compute T̂*_b.

**Source property — not certified.** Approximates the sampling distribution of T̂_n.

**Source use — context only.** Confidence intervals.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for M48.** What symbolic invariant learned from a failed test can subsequently be proved for all parameters? Identify the exact role of this operator in that derivation.

<a id="op-m49"></a>

#### M49. `Jknife` — jackknife operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Sample × estimator → bias-corrected estimator

**Source definition.** J(T) := n T̂_n - (n-1) (1/n) Σ T̂_{n,-i}.

**Source property — not certified.** Reduces O(1/n) bias.

**Source use — context only.** Bias correction in estimation.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for M49.** What failure modes can this experiment actually detect at its sample size? Identify the exact role of this operator in that derivation.

<a id="op-m50"></a>

#### M50. `SCV` — stochastic optimization gradient (REINFORCE)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sample × loss × parameter → unbiased gradient

**Source definition.** ∇ E_{p_θ}[f] = E_{p_θ}[f ∇ log p_θ].

**Source property — not certified.** Unbiased but high variance; control variates lower variance.

**Source use — context only.** Reinforcement learning, variational inference.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for M50.** Are the conditioning, dependence, support and tail assumptions needed by this probabilistic operator true in the exact cryptographic experiment?

### Family C: Combinatorics and generating functions

<a id="op-c1"></a>

#### C1. `OGF` — ordinary generating function

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Sequence → formal power series

**Source definition.** OGF(a)(x) := Σ_{n ≥ 0} a_n x^n.

**Source property — not certified.** Multiplication of OGFs corresponds to convolution.

**Source use — context only.** Counting combinatorial structures.

**QPT-128 substitution.** Use only through [A11](#a11), with each contract and its four research questions.

**Eligibility question for C1.** What exact family of accepted challenge sets fails to reveal the required witness? Identify the exact role of this operator in that derivation.

<a id="op-c2"></a>

#### C2. `EGF` — exponential generating function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Sequence → ×

**Source definition.** EGF(a)(x) := Σ_n a_n x^n / n!.

**Source property — not certified.** Product corresponds to labeled-structure combination.

**Source use — context only.** Counting labeled species.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C2.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c3"></a>

#### C3. `DGF` — Dirichlet generating function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Arithmetic sequence × s → C

**Source definition.** DGF(a)(s) := Σ_{n ≥ 1} a_n / n^s.

**Source property — not certified.** Multiplication = Dirichlet convolution.

**Source use — context only.** Number-theoretic identities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C3.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c4"></a>

#### C4. `ψ` — shift on power series

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C[[x]] → C[[x]]

**Source definition.** (ψ f)(x) := (f(x) - f(0))/x.

**Source property — not certified.** Lowers index by one in a_n x^n.

**Source use — context only.** Recursion-equation manipulation.

**QPT-128 substitution.** Use only through [A11](#a11), with each contract and its four research questions.

**Eligibility question for C4.** Does adding leading digits after b^r>=2^h leave the worst bad-box mass unchanged? Identify the exact role of this operator in that derivation.

<a id="op-c5"></a>

#### C5. `Hada` — Hadamard product

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C[[x]]² → C[[x]]

**Source definition.** (Σ a_n x^n) ⊙ (Σ b_n x^n) := Σ a_n b_n x^n.

**Source property — not certified.** Closed under ring operations on rational functions.

**Source use — context only.** Diagonal-sum extraction.

**QPT-128 substitution.** Use only through [A11](#a11), with each contract and its four research questions.

**Eligibility question for C5.** What exact family of accepted challenge sets fails to reveal the required witness? Identify the exact role of this operator in that derivation.

<a id="op-c6"></a>

#### C6. `Borel_op` — Borel sum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Formal series × → analytic function

**Source definition.** B(Σ a_n x^n) := Σ a_n x^n / n! followed by Laplace transform.

**Source property — not certified.** Sums certain divergent series to genuine analytic functions.

**Source use — context only.** Resurgence theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C6.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c7"></a>

#### C7. `Plet` — plethysm

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Symmetric functions × → ×

**Source definition.** (p_n ∘ p_m)(x_1, x_2, ...) := p_{nm}(x_1, x_2, ...) extended multiplicatively.

**Source property — not certified.** Associative; corresponds to substitution of variables.

**Source use — context only.** Wreath products of symmetric groups.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C7.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c8"></a>

#### C8. `L_inv` — Lagrange inversion

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Formal series with f(0) = 0, f'(0) ≠ 0 → inverse series

**Source definition.** [x^n] f^{-1}(x) = (1/n) [u^{n-1}] (u/f(u))^n.

**Source property — not certified.** Closed-form expansion of compositional inverse.

**Source use — context only.** Tree enumeration.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C8.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c9"></a>

#### C9. `⊎` — species sum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Species × species → species

**Source definition.** (F + G)[A] := F[A] ⊔ G[A].

**Source property — not certified.** OGFs add, EGFs add.

**Source use — context only.** Disjoint-choice combinatorics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C9.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c10"></a>

#### C10. `⊗_sp` — species product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Species × species → species

**Source definition.** (F · G)[A] := Σ_{A = B ⊔ C} F[B] × G[C].

**Source property — not certified.** EGFs multiply.

**Source use — context only.** Labeled-structure factorization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C10.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c11"></a>

#### C11. `∘_sp` — species composition

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Species × (F[∅] = ∅) → species

**Source definition.** (F ∘ G)[A] := Σ_{partitions π of A} F[π] × Π_{B ∈ π} G[B].

**Source property — not certified.** EGFs satisfy (F ∘ G)(x) = F(G(x)).

**Source use — context only.** Substitution of species.

**Amendment (DOMAIN_GAP).** Require the inner species G[empty]=empty for ordinary species substitution F composed with G; the source attaches the restriction to the wrong symbol.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C11.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c12"></a>

#### C12. `s_λ` — Schur function operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Partition × symmetric polynomials → ×

**Source definition.** s_λ(x_1, ..., x_n) := det(x_i^{λ_j + n - j}) / det(x_i^{n-j}).

**Source property — not certified.** Form a Z-basis of Λ; Schur positive products encoded by Littlewood-Richardson.

**Source use — context only.** Representations of GL(n).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C12.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c13"></a>

#### C13. `m_λ` — monomial symmetric function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Partition × → symmetric polynomial

**Source definition.** m_λ := Σ over distinct permutations of x^λ.

**Source property — not certified.** Free Z-basis of Λ.

**Source use — context only.** Combinatorial identities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C13.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c14"></a>

#### C14. `p_n` — power-sum symmetric function

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** ℕ → polynomial

**Source definition.** p_n(x_1,...) := Σ x_i^n.

**Source property — not certified.** Multiplicatively generate Λ ⊗ Q.

**Source use — context only.** Character theory of S_n.

**QPT-128 substitution.** Use only through [A15](#a15), with each contract and its four research questions.

**Eligibility question for C14.** Can the exact rank-count identity replace a loose union bound in that SAME distribution? Identify the exact role of this operator in that derivation.

<a id="op-c15"></a>

#### C15. `e_n` — elementary symmetric function

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** ℕ → polynomial

**Source definition.** e_n := Σ_{i_1 < ... < i_n} x_{i_1} ... x_{i_n}.

**Source property — not certified.** Newton's identities relate e_n and p_n.

**Source use — context only.** Coefficients of characteristic polynomials.

**QPT-128 substitution.** Use only through [A15](#a15), with each contract and its four research questions.

**Eligibility question for C15.** Does the standardized XOF-expanded matrix have the independence used by the rank calculation? Identify the exact role of this operator in that derivation.

<a id="op-c16"></a>

#### C16. `h_n` — complete homogeneous symmetric function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** ℕ → polynomial

**Source definition.** h_n := Σ_{i_1 ≤ ... ≤ i_n} x_{i_1} ... x_{i_n}.

**Source property — not certified.** Free basis; dual to elementary under standard scalar product.

**Source use — context only.** Symmetric-function bases for combinatorial identities.

**Amendment (DEFINITION_MISMATCH).** Under the usual Hall scalar product, the complete homogeneous basis is dual to the monomial basis; the elementary and complete bases are exchanged by omega, not dual as stated.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C16.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c17"></a>

#### C17. `P_λ` — Macdonald polynomial

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Partition × (q, t) → ×

**Source definition.** Unique basis of Λ with triangularity and (q,t)-orthogonality.

**Source property — not certified.** Specializes to Schur (q = t), Hall-Littlewood (q = 0), Jack (q → 1).

**Source use — context only.** AGT correspondence.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C17.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c18"></a>

#### C18. `ω` — involution on Λ

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Symmetric functions → ×

**Source definition.** ω(e_n) := h_n, extended multiplicatively.

**Source property — not certified.** Involution exchanging e ↔ h, s_λ ↔ s_{λ'}.

**Source use — context only.** Conjugate partitions in character theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C18.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c19"></a>

#### C19. `Sh` — shuffle product

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** T(V)² → T(V)

**Source definition.** (u_1...u_p) ⧢ (v_1...v_q) := Σ over interleavings.

**Source property — not certified.** Commutative; makes T(V) a Hopf algebra.

**Source use — context only.** Iterated-integral identities.

**QPT-128 substitution.** Use only through [A12](#a12), with each contract and its four research questions.

**Eligibility question for C19.** For a binary replacement, which two distinct accepted responses reconstruct the actual quorum witness? Identify the exact role of this operator in that derivation.

<a id="op-c20"></a>

#### C20. `Conc` — concatenation

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** T(V)² → T(V)

**Source definition.** Tensor product of words.

**Source property — not certified.** Non-commutative associative.

**Source use — context only.** Free-monoid algebra.

**QPT-128 substitution.** Use only through [A12](#a12), [A19](#a19), with each contract and its four research questions.

**Eligibility question for C20.** Does a proposed distribution-distance bound remain meaningful after adaptive quantum queries to its generating oracle? Identify the exact role of this operator in that derivation.

<a id="op-c21"></a>

#### C21. `⨯_RSK` — RSK correspondence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Generalized matrices ↔ pairs of SSYT

**Source definition.** Robinson-Schensted-Knuth bijection.

**Source property — not certified.** Bijection between non-neg integer matrices and pairs (P, Q) of SSYT of same shape.

**Source use — context only.** Cauchy identity Σ s_λ ⊗ s_λ = Π 1/(1 - x_i y_j).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C21.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c22"></a>

#### C22. `Riff` — riffle shuffle operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Permutations of [n] → permutations

**Source definition.** Riff(σ) := interleave two halves preserving order within each.

**Source property — not certified.** Random riffle shuffles mix in (3/2) log_2 n shuffles.

**Source use — context only.** Card-shuffling theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C22.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c23"></a>

#### C23. `Schub` — Schubert calculus operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Λ × → cohomology of Gr(k,n)

**Source definition.** Maps Schur polynomial s_λ to Schubert class σ_λ.

**Source property — not certified.** Ring isomorphism modulo (h_{n-k+1},...,h_n).

**Source use — context only.** Enumerative geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C23.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c24"></a>

#### C24. `∂_w` — BGG / divided-difference

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Polynomials × simple reflection s_i → polynomials

**Source definition.** ∂_i f := (f - s_i f)/(x_i - x_{i+1}).

**Source property — not certified.** Squares to zero; satisfies braid relations.

**Source use — context only.** Schubert polynomials.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C24.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c25"></a>

#### C25. `S_w` — Schubert polynomial

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** S_n × → polynomial

**Source definition.** S_w := ∂_{w^{-1} w_0} (x_1^{n-1} x_2^{n-2} ... x_{n-1}).

**Source property — not certified.** Stable under embedding S_n → S_{n+1}.

**Source use — context only.** Equivariant cohomology of flag varieties.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C25.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c26"></a>

#### C26. `Lin` — linear-extension operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Finite poset → set of linear extensions

**Source definition.** Lin(P) := { permutations of P respecting ≤_P }.

**Source property — not certified.** Counted by formula involving the Stanley-MacMahon transfer.

**Source use — context only.** Algorithmic counting (#P-complete).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C26.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c27"></a>

#### C27. `PromTr` — promotion operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Linear extensions × → ×

**Source definition.** Schützenberger promotion: replace 1, slide, fill.

**Source property — not certified.** Order equal to a divisor of |P|; preserves shape.

**Source use — context only.** Cyclic-sieving phenomena.

**Amendment (FALSE_AS_STATED).** Promotion order does not generally divide the number of elements for arbitrary posets or shapes. Special cyclic-sieving families require their own hypotheses.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C27.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c28"></a>

#### C28. `Evac` — evacuation operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** SSYT → SSYT (same shape)

**Source definition.** Iterated jeu de taquin from a 'jeu de taquin' definition.

**Source property — not certified.** Involution; corresponds to longest-permutation conjugation.

**Source use — context only.** Symmetry in tableau combinatorics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C28.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c29"></a>

#### C29. `JdT` — jeu de taquin

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Skew tableaux → straight-shape tableaux

**Source definition.** Slides cells through inner corners.

**Source property — not certified.** Resulting shape and entries are invariant under choice of slides.

**Source use — context only.** Littlewood-Richardson rule.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C29.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c30"></a>

#### C30. `LR` — Littlewood-Richardson coefficient

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (λ, μ, ν) → ℕ

**Source definition.** c^ν_{λμ} := number of LR-tableaux of shape ν/λ and content μ.

**Source property — not certified.** Schur product: s_λ s_μ = Σ c^ν_{λμ} s_ν.

**Source use — context only.** Tensor-product decomposition for GL representations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C30.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c31"></a>

#### C31. `Kost` — Kostka number

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (λ, μ) → ℕ

**Source definition.** K_{λμ} := |SSYT of shape λ and content μ|.

**Source property — not certified.** Transition between Schur and monomial bases.

**Source use — context only.** Counting tableaux.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C31.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c32"></a>

#### C32. `Cha` — characteristic map

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Class functions of S_n → Λ^n

**Source definition.** ch(χ) := (1/n!) Σ χ(σ) p_{type(σ)}.

**Source property — not certified.** Isomorphism of graded rings.

**Source use — context only.** Frobenius reciprocity for S_n.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C32.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c33"></a>

#### C33. `Hk_λ` — hook-length formula

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Standard Young tableau shape λ → ℕ

**Source definition.** f^λ = n! / Π_{c ∈ λ} h(c).

**Source property — not certified.** Counts SYT of shape λ.

**Source use — context only.** Dimension of irreducible S_n-modules.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C33.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c34"></a>

#### C34. `Dye_op` — Dyck-path enumeration

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℕ → ℕ

**Source definition.** C_n := (1/(n+1)) C(2n, n) (Catalan).

**Source property — not certified.** Counts Dyck paths from (0,0) to (2n,0).

**Source use — context only.** Triangulations, binary trees.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C34.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c35"></a>

#### C35. `Cat_n` — Catalan-number functional

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Algebraic structures → ℕ

**Source definition.** Counts: Dyck paths, triangulations, non-crossing partitions, binary trees, etc.

**Source property — not certified.** Many bijective interpretations.

**Source use — context only.** Universal in non-crossing combinatorics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C35.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c36"></a>

#### C36. `⊗_part` — partition product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Partitions × partitions → multiset of partitions

**Source definition.** λ ⋅ μ via Hall coefficients.

**Source property — not certified.** Encodes Hall algebra; equivalent to L-R for Schurs.

**Source use — context only.** Hall algebra of an abelian category.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C36.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c37"></a>

#### C37. `MacM` — MacMahon master theorem operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Coefficient operator on determinant identities

**Source definition.** [x^k] det(I - X A)^{-1} = sum over permutations weighted by A.

**Source property — not certified.** Generalizes Cauchy and binomial identities.

**Source use — context only.** Enumerative-generating-function identities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C37.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c38"></a>

#### C38. `BIDe` — BEST/Birkhoff-van der Waerden

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Bistochastic matrix → convex combination of permutation matrices

**Source definition.** Birkhoff-von Neumann decomposition.

**Source property — not certified.** Bistochastic = convex hull of permutation matrices.

**Source use — context only.** Combinatorial optimization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C38.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c39"></a>

#### C39. `Bell_n` — Bell number recurrence operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℕ → ℕ

**Source definition.** B_{n+1} = Σ_{k=0}^n C(n,k) B_k.

**Source property — not certified.** EGF: e^{e^x - 1}.

**Source use — context only.** Set-partition counts.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C39.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c40"></a>

#### C40. `⊕_lab` — labeled-structure sum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Combinatorial classes × → ×

**Source definition.** A ⊕ B has size-n elements = A_n + B_n.

**Source property — not certified.** EGFs add.

**Source use — context only.** Symbolic-method enumeration.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C40.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c41"></a>

#### C41. `Seq` — sequence construction

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Class with C[0] = ∅ → labeled sequences

**Source definition.** SEQ(C) := Σ_{k ≥ 0} C^k.

**Source property — not certified.** OGF/EGF: 1/(1 - C(x)).

**Source use — context only.** Strings, ordered tuples.

**QPT-128 substitution.** Use only through [A13](#a13), with each contract and its four research questions.

**Eligibility question for C41.** Is the rejection probability bounded for every key in the SAME good-key event used by the signature reduction? Identify the exact role of this operator in that derivation.

<a id="op-c42"></a>

#### C42. `Cyc` — cycle construction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Class × → cycles

**Source definition.** CYC(C) builds cyclic arrangements.

**Source property — not certified.** OGF: Σ φ(k)/k log(1/(1 - C(x^k))); EGF: log(1/(1 - C(x))).

**Source use — context only.** Permutation cycle counting.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C42.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c43"></a>

#### C43. `Set_op` — set construction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Class × → sets

**Source definition.** SET(C) := unordered multiset; subsets of C.

**Source property — not certified.** EGF: exp(C(x)).

**Source use — context only.** Combinatorial set decompositions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C43.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c44"></a>

#### C44. `CharSp` — characteristic series of species

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Species → power series

**Source definition.** F(x) := Σ |F[n]| x^n / n!.

**Source property — not certified.** EGF; bijection between F and its series under labeled equivalence.

**Source use — context only.** Combinatorial bijections.

**Amendment (FALSE_AS_STATED).** An exponential generating series records counts, not all species structure. Equal counts do not establish a natural isomorphism of species.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C44.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c45"></a>

#### C45. `Smith` — Smith normal form

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** C^{m×n} (over PID) → diagonal canonical form

**Source definition.** A = U D V with D diagonal, divisors d_1 | d_2 | ...

**Source property — not certified.** Unique up to unit; encodes integer kernel and image.

**Source use — context only.** Computing homology of chain complexes.

**Amendment (TYPE_GAP).** Specify matrices over a PID and unimodular factors. Over Z this encodes integer divisibility. Real/complex SVD does not replace this or finite-field elimination.

**QPT-128 substitution.** Use only through [A15](#a15), with each contract and its four research questions.

**Eligibility question for C45.** Which rank deficiency controls the signature entropy estimate, over which field or module? Identify the exact role of this operator in that derivation.

<a id="op-c46"></a>

#### C46. `HilbS` — Hilbert series

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Graded module M → power series

**Source definition.** HS(M)(t) := Σ_n dim M_n · t^n.

**Source property — not certified.** Rational if M finitely generated over polynomial ring.

**Source use — context only.** Combinatorial geometry, invariant theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C46.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c47"></a>

#### C47. `Euler_op` — Euler polynomial operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Generating-function → Euler-summed form

**Source definition.** E[Σ a_n x^n] := Σ Δ^k a_0 / (1 - x)^{k+1}.

**Source property — not certified.** Rearranges power series; useful for asymptotic acceleration.

**Source use — context only.** Series acceleration.

**Amendment (FORMULA_ERROR).** For the Newton-series generating-function identity use sum_(k>=0) Delta^k a_0*x^k/(1-x)^(k+1), with formal/analytic justification. The x^k factors are missing.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C47.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

<a id="op-c48"></a>

#### C48. `Bin_inv` — binomial inversion

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Sequence pair → equivalence

**Source definition.** b_n = Σ C(n,k) a_k ⇔ a_n = Σ (-1)^{n-k} C(n,k) b_k.

**Source property — not certified.** Möbius inversion on the Boolean lattice.

**Source use — context only.** Counting by complement.

**QPT-128 substitution.** Use only through [A11](#a11), with each contract and its four research questions.

**Eligibility question for C48.** Does adding leading digits after b^r>=2^h leave the worst bad-box mass unchanged? Identify the exact role of this operator in that derivation.

<a id="op-c49"></a>

#### C49. `Stir_inv` — Stirling inversion

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Sequence pair → equivalence

**Source definition.** b_n = Σ S(n,k) a_k ⇔ a_n = Σ s(n,k) b_k.

**Source property — not certified.** Stirling matrices are mutually inverse.

**Source use — context only.** Basis-change between rising/falling factorial bases.

**QPT-128 substitution.** Use only through [A11](#a11), with each contract and its four research questions.

**Eligibility question for C49.** What exact family of accepted challenge sets fails to reveal the required witness? Identify the exact role of this operator in that derivation.

<a id="op-c50"></a>

#### C50. `Aper` — Apéry-like operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Recurrence → closed form for special values

**Source definition.** Detects whether a given linear recurrence is hypergeometric-soluble.

**Source property — not certified.** Foundational in proofs of irrationality (e.g. of ζ(3)).

**Source use — context only.** Number-theoretic constants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for C50.** Can this counting operator enumerate the actual finite bad-set or key-distribution object, with an independent coefficient/count check?

### Family H: Topology and homology

<a id="op-h1"></a>

#### H1. `H_n` — singular homology

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Top × ℕ × abelian group A → abelian group

**Source definition.** H_n(X; A) := H_n(C_*(X; A)) of the singular chain complex.

**Source property — not certified.** Homotopy invariant; functorial.

**Source use — context only.** Topological classification of spaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H1.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h2"></a>

#### H2. `H^n` — singular cohomology

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Top × ℕ × A → abelian group

**Source definition.** H^n(X; A) := H^n(Hom(C_*(X), A)).

**Source property — not certified.** Ring structure under cup product.

**Source use — context only.** Obstructions to global sections.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H2.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h3"></a>

#### H3. `∂` — boundary operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C_n → C_{n-1}

**Source definition.** ∂[v_0,...,v_n] := Σ_i (-1)^i [v_0,...,v̂_i,...,v_n].

**Source property — not certified.** Squares to zero: ∂² = 0.

**Source use — context only.** Definition of chain complexes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H3.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h4"></a>

#### H4. `d` — coboundary operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^n → C^{n+1}

**Source definition.** (d φ)(σ) := φ(∂ σ).

**Source property — not certified.** Squares to zero; adjoint to ∂.

**Source use — context only.** Cohomological obstruction theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H4.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h5"></a>

#### H5. `Hˇ^n` — Čech cohomology

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Top × open cover × ℕ → abelian group

**Source definition.** Hˇ^n(X; F) := lim_U H^n(C_*(U; F)).

**Source property — not certified.** Agrees with sheaf cohomology on paracompact Hausdorff spaces.

**Source use — context only.** Computing cohomology via good covers.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H5.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h6"></a>

#### H6. `H^*(X; F)` — sheaf cohomology

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Space × sheaf × ℕ → abelian group

**Source definition.** H^n(X; F) := R^n Γ(F).

**Source property — not certified.** Vanishes for fine sheaves in positive degree.

**Source use — context only.** Riemann-Roch on complex manifolds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H6.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h7"></a>

#### H7. `PH_t` — persistent homology

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Filtration × t ∈ R → abelian group

**Source definition.** PH_n(t) := H_n(X_t) with maps induced by inclusion.

**Source property — not certified.** Decomposes into intervals (Crawley-Boevey).

**Source use — context only.** Topological data analysis.

**Amendment (DOMAIN_GAP).** Require a suitable pointwise finite-dimensional one-parameter persistence module over a field for interval decomposition. General abelian-group-valued persistence modules do not have that barcode classification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H7.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h8"></a>

#### H8. `BC` — barcode operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Persistence module → multiset of intervals

**Source definition.** BC(M) := decomposition of M as ⊕ k[a_i, b_i).

**Source property — not certified.** Unique decomposition up to permutation.

**Source use — context only.** Stable summary of point-cloud topology.

**Amendment (DOMAIN_GAP).** Require a suitable pointwise finite-dimensional one-parameter persistence module over a field for interval decomposition. General abelian-group-valued persistence modules do not have that barcode classification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H8.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h9"></a>

#### H9. `MV_seq` — Mayer-Vietoris connecting map

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Open cover X = U ∪ V × ℕ → long exact sequence

**Source definition.** δ: H_n(X) → H_{n-1}(U ∩ V).

**Source property — not certified.** Connects local and global homology.

**Source use — context only.** Computing homology by decomposition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H9.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h10"></a>

#### H10. `⌣` — cup product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** H^p × H^q → H^{p+q}

**Source definition.** (α ⌣ β)(σ) := α(σ|_{[0,...,p]}) β(σ|_{[p,...,p+q]}).

**Source property — not certified.** Graded-commutative: α ⌣ β = (-1)^{pq} β ⌣ α.

**Source use — context only.** Cohomology ring structure.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H10.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h11"></a>

#### H11. `⌢` — cap product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** H_p × H^q → H_{p-q}

**Source definition.** Pairing of chain and cochain via evaluation.

**Source property — not certified.** Adjoint to cup; Poincaré duality interpretation.

**Source use — context only.** Intersection products.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H11.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h12"></a>

#### H12. `κ_K` — Künneth operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** H_*(X) × H_*(Y) → H_*(X × Y)

**Source definition.** Cross product × induces isomorphism over fields or for torsion-free groups.

**Source property — not certified.** Generally Tor terms appear (Künneth formula).

**Source use — context only.** Cohomology of product spaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H12.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h13"></a>

#### H13. `PD` — Poincaré dual

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Closed oriented n-manifold × → ×

**Source definition.** PD: H^k(M) ≅ H_{n-k}(M).

**Source property — not certified.** Isomorphism via cap with fundamental class [M].

**Source use — context only.** Duality between cycles and cocycles.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H13.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h14"></a>

#### H14. `χ` — Euler characteristic

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Finite CW-complex → Z

**Source definition.** χ(X) := Σ (-1)^k dim H_k(X; Q) = Σ (-1)^k c_k(X).

**Source property — not certified.** Multiplicative for products and additive under inclusion-exclusion.

**Source use — context only.** Genus of surfaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H14.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h15"></a>

#### H15. `τ_R` — Reidemeister torsion

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Triangulated manifold × representation → group element

**Source definition.** τ(M; ρ) := alternating product of determinants of boundary maps in twisted chain complex.

**Source property — not certified.** Simple-homotopy invariant; not homotopy invariant in general.

**Source use — context only.** Distinguishing lens spaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H15.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h16"></a>

#### H16. `β` — Bockstein operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Coefficient short exact sequence × → connecting map

**Source definition.** β: H^n(X; Z/p) → H^{n+1}(X; Z/p) from 0 → Z/p → Z/p² → Z/p → 0.

**Source property — not certified.** Anti-commutes with itself: β² = 0.

**Source use — context only.** Detecting non-split torsion.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H16.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h17"></a>

#### H17. `Sq^i` — Steenrod square

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** H^n(X; Z/2) × ℕ → H^{n+i}(X; Z/2)

**Source definition.** Stable cohomology operations satisfying Cartan formula.

**Source property — not certified.** Generate the Steenrod algebra.

**Source use — context only.** Obstruction theory mod 2.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H17.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h18"></a>

#### H18. `P^i` — Steenrod power

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** H^n(X; Z/p) × ℕ → H^{n + 2i(p-1)}(X; Z/p)

**Source definition.** Analog of Sq for odd primes.

**Source property — not certified.** Cartan and Adem relations.

**Source use — context only.** Cohomology operations at odd primes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H18.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h19"></a>

#### H19. `PD_diag` — persistence diagram

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Persistence module → multiset of points in R²

**Source definition.** PD(M) := { (a_i, b_i) : interval [a_i, b_i) in BC }.

**Source property — not certified.** Stable under Hausdorff-Wasserstein metric on diagrams.

**Source use — context only.** Statistical TDA.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H19.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h20"></a>

#### H20. `Wass_PD` — Wasserstein on diagrams

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** PD² × p → R_+

**Source definition.** W_p(D_1, D_2) := inf over matchings of L^p cost.

**Source property — not certified.** Stability: W_p(PD(f), PD(g)) ≤ ‖f - g‖_∞.

**Source use — context only.** Robust topological summaries.

**Amendment (FALSE_AS_STATED).** The unit Lipschitz bound is for bottleneck distance under stability hypotheses. Finite-p Wasserstein bounds additionally depend on feature count or total persistence; moving N features by epsilon can cost N^(1/p)*epsilon.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H20.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h21"></a>

#### H21. `BD` — bottleneck distance

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** PD² → R_+

**Source definition.** BD(D_1, D_2) := inf over matchings of sup-cost.

**Source property — not certified.** Stability theorem against perturbations.

**Source use — context only.** Comparing point-cloud topologies.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H21.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h22"></a>

#### H22. `Image_persist` — persistent image

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** PD × kernel → R^{n×n}

**Source definition.** Convolves diagram with Gaussian on the wedge.

**Source property — not certified.** Stable, finite-dimensional vector representation.

**Source use — context only.** ML on topological features.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H22.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h23"></a>

#### H23. `π_n` — homotopy group

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Pointed top space × ℕ → group

**Source definition.** π_n(X, x_0) := [S^n, X]_*.

**Source property — not certified.** Abelian for n ≥ 2; π_1 may be non-abelian.

**Source use — context only.** Classification up to homotopy.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H23.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h24"></a>

#### H24. `Hur` — Hurewicz homomorphism

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** π_n(X) → H_n(X; Z)

**Source definition.** Hur([f]) := f_*[S^n].

**Source property — not certified.** Isomorphism for first non-trivial degree (in simply connected X).

**Source use — context only.** Algebraic topology computations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H24.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h25"></a>

#### H25. `Whit` — Whitehead product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** π_p × π_q → π_{p+q-1}

**Source definition.** [α, β] from commutator of attaching maps.

**Source property — not certified.** Graded-Lie-algebra structure on π_*(X) (mod Hurewicz).

**Source use — context only.** Higher-order homotopy structure.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H25.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h26"></a>

#### H26. `CW_attach` — CW-attaching operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Skeleton × map S^{n-1} → X^{(n-1)} → CW with cell

**Source definition.** Attach via pushout of S^{n-1} → D^n and S^{n-1} → X^{(n-1)}.

**Source property — not certified.** Provides building blocks of CW complexes.

**Source use — context only.** Cellular cohomology.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H26.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h27"></a>

#### H27. `Diff_pers` — differential of persistence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Time-varying filtration → R^N

**Source definition.** Tracks birth/death derivative under perturbation.

**Source property — not certified.** Lipschitz under controlled distortions.

**Source use — context only.** Gradient-based optimization of topological features.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H27.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h28"></a>

#### H28. `Vie_R` — Vietoris-Rips complex operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Metric space × ε → simplicial complex

**Source definition.** VR_ε(X) := { σ : diam(σ) ≤ ε }.

**Source property — not certified.** Monotone in ε; defines a filtration.

**Source use — context only.** Building persistence diagrams from point clouds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H28.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h29"></a>

#### H29. `Cech_X` — Čech complex operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Cover × → simplicial complex

**Source definition.** Č_ε(X) := nerve of {B(x, ε)}_{x ∈ X}.

**Source property — not certified.** Homotopy-equivalent to union of balls (nerve theorem).

**Source use — context only.** Approximating topology of unions of convex sets.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H29.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h30"></a>

#### H30. `Reeb` — Reeb-graph operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Manifold × Morse f → graph

**Source definition.** Reeb(M, f) := M / (x ∼ y if f(x) = f(y) and same component of f^{-1}(c)).

**Source property — not certified.** 1-d topological abstraction of f.

**Source use — context only.** Shape skeletonization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H30.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h31"></a>

#### H31. `Mapper` — Mapper operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Point cloud × cover × clusterer → graph

**Source definition.** Mapper(X, f, U) := nerve of cluster-refined pullback of U.

**Source property — not certified.** Multi-scale visualization of high-dimensional data.

**Source use — context only.** Exploratory data analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H31.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h32"></a>

#### H32. `∇_DG` — discrete gradient

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Function on simplicial complex → discrete vector field

**Source definition.** Morse-pairing on cells with f(σ) ≤ f(τ) and σ ⊂ τ.

**Source property — not certified.** Acyclic matching ⇒ discrete Morse theory.

**Source use — context only.** Combinatorial simplification of complexes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H32.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h33"></a>

#### H33. `LST` — Lefschetz fixed-point operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Continuous self-map of compact CW × → Z

**Source definition.** L(f) := Σ_k (-1)^k tr(f_* | H_k(X; Q)).

**Source property — not certified.** L(f) ≠ 0 ⇒ f has a fixed point.

**Source use — context only.** Brouwer's theorem and generalizations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H33.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h34"></a>

#### H34. `Tho` — Thom isomorphism

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Oriented rank-r vector bundle → H^*(E, E_0) ≅ H^{*-r}(B)

**Source definition.** Multiplication by Thom class u.

**Source property — not certified.** Generalizes integration over the fiber.

**Source use — context only.** Cobordism and characteristic classes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H34.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h35"></a>

#### H35. `w_i` — Stiefel-Whitney class

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Real vector bundle × ℕ → H^i(B; Z/2)

**Source definition.** Defined by axioms (naturality, Whitney sum, S^∞).

**Source property — not certified.** Detect orientability (w_1) and spin (w_1, w_2).

**Source use — context only.** Obstructions to manifold structures.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H35.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h36"></a>

#### H36. `c_i` — Chern class

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Complex vector bundle × ℕ → H^{2i}(B; Z)

**Source definition.** Defined via projectivization or splitting principle.

**Source property — not certified.** Whitney sum formula: c(E ⊕ F) = c(E) c(F).

**Source use — context only.** Complex algebraic geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H36.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h37"></a>

#### H37. `p_i` — Pontryagin class

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Real vector bundle × ℕ → H^{4i}(B; Z)

**Source definition.** p_i := (-1)^i c_{2i}(E ⊗ C).

**Source property — not certified.** Invariant under bundle complexification.

**Source use — context only.** Signature theorem (Hirzebruch).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H37.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h38"></a>

#### H38. `Sig` — signature

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** 4k-manifold → Z

**Source definition.** Sig(M) := signature of intersection form on H^{2k}(M; Q).

**Source property — not certified.** Hirzebruch: Sig(M) = ⟨L(p_1,...), [M]⟩.

**Source use — context only.** Topological invariants of 4-manifolds.

**QPT-128 substitution.** Use only through [A19](#a19), with each contract and its four research questions.

**Eligibility question for H38.** Where in its actual input does it obtain the information that the compressed-oracle reduction reads from D? Identify the exact role of this operator in that derivation.

<a id="op-h39"></a>

#### H39. `Â` — Â-genus

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Spin manifold → Q

**Source definition.** Â(M) := ⟨Â-class, [M]⟩.

**Source property — not certified.** Atiyah-Singer: equals index of Dirac operator.

**Source use — context only.** Witten genera, string-theoretic invariants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H39.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h40"></a>

#### H40. `RR_op` — Riemann-Roch operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Coherent sheaf F on smooth projective X → integer

**Source definition.** χ(F) := Σ (-1)^i dim H^i(X, F) = ∫_X ch(F) · td(X).

**Source property — not certified.** Combines cohomology and characteristic classes.

**Source use — context only.** Enumerative algebraic geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H40.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h41"></a>

#### H41. `π^!` — shriek pullback

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Smooth morphism × bounded derived category → derived category

**Source definition.** π^! F := π^* F ⊗ ω_{X/Y}[d] for smooth π of relative dimension d.

**Source property — not certified.** Right adjoint to push-forward (Grothendieck duality).

**Source use — context only.** Six-functor formalism.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H41.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h42"></a>

#### H42. `π_!` — shriek pushforward

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Proper morphism × → ×

**Source definition.** π_! := proper pushforward in derived category.

**Source property — not certified.** Left adjoint to π^! in proper case.

**Source use — context only.** Base-change theorems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H42.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h43"></a>

#### H43. `⊗^L` — derived tensor product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Bounded derived category² × → ×

**Source definition.** F ⊗^L G := total tensor with flat resolution.

**Source property — not certified.** Computes Tor: H^{-i}(F ⊗^L G) = Tor_i(F, G).

**Source use — context only.** Intersection theory with non-transverse pieces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H43.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h44"></a>

#### H44. `RHom` — derived Hom

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Bounded derived category² × → ×

**Source definition.** RHom(F, G) := total Hom with injective resolution.

**Source property — not certified.** Computes Ext.

**Source use — context only.** Categorified deformation theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H44.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h45"></a>

#### H45. `E_*∞` — spectral-sequence operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Filtered chain complex → bi-graded family E_r^{p,q}

**Source definition.** E_{r+1} = H(E_r, d_r); converges to graded gr H_*(C).

**Source property — not certified.** Differentials decrease in r.

**Source use — context only.** Computing homology of filtered spaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H45.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h46"></a>

#### H46. `LSS` — Leray spectral sequence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Fibration F → E → B × coefficients → ×

**Source definition.** E_2^{p,q} = H^p(B; H^q(F)) ⇒ H^{p+q}(E).

**Source property — not certified.** Tool of choice for bundle cohomology.

**Source use — context only.** Cohomology of total spaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H46.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h47"></a>

#### H47. `Adams_SS` — Adams spectral sequence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Spectra × → ×

**Source definition.** E_2^{s,t} = Ext_A^{s,t}(H^*X, H^*Y) ⇒ [X, Y]_{t-s}.

**Source property — not certified.** Powerful computer of stable homotopy.

**Source use — context only.** Stable homotopy groups of spheres.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H47.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h48"></a>

#### H48. `Stab` — stable homotopy functor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Spaces → spectra

**Source definition.** Σ^∞ X := suspension spectrum.

**Source property — not certified.** Adjoint to Ω^∞.

**Source use — context only.** Stable homotopy category.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H48.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h49"></a>

#### H49. `Hh` — Hochschild homology

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Algebra → graded module

**Source definition.** HH_n(A) := H_n(Cyclic resolution of A as A-bimodule).

**Source property — not certified.** HH_0(A) = A/[A,A]; HKR isomorphism gives differential forms.

**Source use — context only.** Deformation theory, noncommutative geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H49.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

<a id="op-h50"></a>

#### H50. `Cy` — cyclic homology

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Algebra → graded module

**Source definition.** HC_n(A) := H_n of Connes complex.

**Source property — not certified.** Connected to Hochschild via Connes long exact sequence.

**Source use — context only.** Noncommutative de Rham theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for H50.** What explicit finite reduction connects this topological invariant to the quorum relation or a quantified hardness game? Without one, why would it affect QPT-128?

### Family K: Category theory

<a id="op-k1"></a>

#### K1. `lim` — limit

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Cat × functor F: J → C → object of C

**Source definition.** lim F := terminal cone over F.

**Source property — not certified.** Preserves products and equalizers; unique up to unique iso.

**Source use — context only.** Universal solutions to commutative diagrams.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K1.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k2"></a>

#### K2. `colim` — colimit

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Cat × F: J → C → object

**Source definition.** colim F := initial cocone under F.

**Source property — not certified.** Dual to lim; preserves coproducts and coequalizers.

**Source use — context only.** Gluing constructions in geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K2.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k3"></a>

#### K3. `∫_c` — end

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Functor F: C^op × C → D → object

**Source definition.** ∫_c F(c,c) := equalizer of (F → ∏_c F(c,c)).

**Source property — not certified.** Generalizes natural-transformations: Nat(F, G) = ∫_c Hom(Fc, Gc).

**Source use — context only.** Dinatural transformations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K3.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k4"></a>

#### K4. `∫^c` — coend

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** F: C^op × C → D → object

**Source definition.** ∫^c F(c,c) := coequalizer dual to end.

**Source property — not certified.** Yoneda lemma: F ≅ ∫^c Hom(-, c) × F(c).

**Source use — context only.** Tensor products of functors.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K4.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k5"></a>

#### K5. `Yon` — Yoneda embedding

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C → Fun(C^op, Set)

**Source definition.** Yon(c) := Hom_C(-, c).

**Source property — not certified.** Fully faithful; preserves limits.

**Source use — context only.** Foundation of representable functors.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K5.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k6"></a>

#### K6. `⨯_Day` — Day convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Functors on monoidal C × → functor

**Source definition.** (F ⊛ G)(c) := ∫^{a,b} Hom(a ⊗ b, c) × F(a) × G(b).

**Source property — not certified.** Monoidal structure on presheaves.

**Source use — context only.** Operads, species.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K6.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k7"></a>

#### K7. `Lan_F` — left Kan extension

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** F: A → B × G: A → C → functor B → C

**Source definition.** Lan_F G(b) := colim_{a, F(a) → b} G(a).

**Source property — not certified.** Left adjoint to restriction along F.

**Source use — context only.** Free constructions, induced representations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K7.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k8"></a>

#### K8. `Ran_F` — right Kan extension

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** Ran_F G(b) := lim_{a, b → F(a)} G(a).

**Source property — not certified.** Right adjoint to restriction.

**Source use — context only.** Codensity monads.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K8.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k9"></a>

#### K9. `⊣` — adjunction

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Functor pair (F, G) → natural isomorphism Hom(F-, -) ≅ Hom(-, G-)

**Source definition.** F ⊣ G iff there exist unit η and counit ε with triangle identities.

**Source property — not certified.** Adjoints are unique up to unique iso when they exist.

**Source use — context only.** Universal constructions; free/forgetful pairs.

**QPT-128 substitution.** Use only through [A17](#a17), with each contract and its four research questions.

**Eligibility question for K9.** What exact hardness assumption bounds the remaining NMA adversary for the fixed ML-DSA parameter set? Identify the exact role of this operator in that derivation.

<a id="op-k10"></a>

#### K10. `T_monad` — monad

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Endofunctor T × η × μ → monad

**Source definition.** (T, η: id → T, μ: T² → T) with associativity and unitality.

**Source property — not certified.** Equivalent to adjunction with T = GF.

**Source use — context only.** Effects and computation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K10.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k11"></a>

#### K11. `Eilenberg-Moore` — Eilenberg-Moore category

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Monad → category of algebras

**Source definition.** EM(T) := { (X, h: TX → X) : h ∘ μ = h ∘ Th, h ∘ η = id }.

**Source property — not certified.** Forgetful EM(T) → C has T as monad; right adjoint produces T-free algebras.

**Source use — context only.** Universal model theory.

**Amendment (DIRECTION_ERROR).** The free Eilenberg-Moore algebra functor is left adjoint to the forgetful functor, not right adjoint as written.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K11.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k12"></a>

#### K12. `Kleisli` — Kleisli category

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Monad → category

**Source definition.** Kl(T) has same objects as C and morphisms Hom(X, TY).

**Source property — not certified.** Composition uses μ; gives free algebras directly.

**Source use — context only.** Programming with effects.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K12.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k13"></a>

#### K13. `T_comonad` — comonad

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Endofunctor T × ε × δ → comonad

**Source definition.** (T, ε: T → id, δ: T → T²) with co-associativity.

**Source property — not certified.** Dual to monad; arises from adjunctions in the opposite direction.

**Source use — context only.** Stateful and contextual computation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K13.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k14"></a>

#### K14. `⊗_C` — tensor in monoidal category

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C² → C

**Source definition.** Bifunctor with associator α and unitors λ, ρ satisfying coherence (pentagon, triangle).

**Source property — not certified.** Coherence theorem: all bracketings equivalent.

**Source use — context only.** Quantum group representations.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for K14.** Is a classical copy operation being applied only after the data have become classical? Identify the exact role of this operator in that derivation.

<a id="op-k15"></a>

#### K15. `⊗^*` — symmetric monoidal braid

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** σ_{A,B}: A ⊗ B → B ⊗ A with σ² = id.

**Source property — not certified.** Symmetric vs braided distinction.

**Source use — context only.** Hexagon coherence.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K15.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k16"></a>

#### K16. `σ_brd` — braiding

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Braided category × → natural iso

**Source definition.** σ_{A,B}: A ⊗ B → B ⊗ A satisfying hexagon (no σ² = id required).

**Source property — not certified.** Yang-Baxter equation derived from coherence.

**Source use — context only.** Braided fusion categories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K16.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k17"></a>

#### K17. `Star` — duality

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Compact closed C → contravariant equivalence

**Source definition.** Maps A ↦ A^* with evaluation ε_A: A ⊗ A* → I and coev η_A: I → A* ⊗ A.

**Source property — not certified.** Triangle equations enforce 'trace'.

**Source use — context only.** Categorical quantum mechanics.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for K17.** Can both verifiers run before the one terminal database measurement in the intended security game? Identify the exact role of this operator in that derivation.

<a id="op-k18"></a>

#### K18. `Tr_C` — categorical trace

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Endomorphism in traced monoidal category → endomorphism

**Source definition.** Tr^U(f) for f: X ⊗ U → Y ⊗ U.

**Source property — not certified.** Sliding, vanishing, naturality axioms.

**Source use — context only.** Fixed points, feedback in dataflow.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K18.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k19"></a>

#### K19. `Diag` — dinatural transformation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^op × C → D

**Source definition.** Family θ_c: F(c,c) → G(c,c) compatible with morphisms in both variables.

**Source property — not certified.** Naturalize across mixed variance.

**Source use — context only.** Trace-like constructions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K19.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k20"></a>

#### K20. `⨯_pro` — profunctor composition

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** C^op × D → Set and D^op × E → Set → C^op × E → Set

**Source definition.** (P ⊙ Q)(c, e) := ∫^d P(c, d) × Q(d, e).

**Source property — not certified.** Identity profunctor is Hom; composes with Yoneda extension.

**Source use — context only.** Categorified relations.

**QPT-128 substitution.** Use only through [A22](#a22), with each contract and its four research questions.

**Eligibility question for K20.** Can a tighter simulation reduce a concrete bottleneck without changing the admissible attack model? Identify the exact role of this operator in that derivation.

<a id="op-k21"></a>

#### K21. `Cat(F)` — fundamental category

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Top space → small category

**Source definition.** Π_1(X) := paths up to homotopy.

**Source property — not certified.** Π_1 of a CW-complex computed from the 2-skeleton.

**Source use — context only.** Algebraic topology.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K21.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k22"></a>

#### K22. `Nerve` — nerve functor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Small cat → simplicial set

**Source definition.** N(C)_n := sequences of n composable arrows.

**Source property — not certified.** Restricts to a fully faithful embedding Cat → sSet.

**Source use — context only.** Higher categories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K22.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k23"></a>

#### K23. `∞-Cat` — ∞-category truncation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Quasi-category × n → n-truncated

**Source definition.** τ_n : ∞-Cat → n-Cat by collapsing higher cells.

**Source property — not certified.** Left adjoint to inclusion.

**Source use — context only.** Truncation in derived contexts.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K23.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k24"></a>

#### K24. `Hocolim` — homotopy colimit

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Functor F: J → Top × → space

**Source definition.** hocolim F := colim of cofibrant replacement.

**Source property — not certified.** Homotopy-invariant version of colim.

**Source use — context only.** Moduli spaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K24.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k25"></a>

#### K25. `Holim` — homotopy limit

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** holim := lim of fibrant replacement.

**Source property — not certified.** Detects derived information.

**Source use — context only.** Spectra and obstruction theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K25.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k26"></a>

#### K26. `⊗^L_cat` — derived tensor of dg-categories

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Bounded dg-cats × → dg-cat

**Source definition.** Take cofibrant replacement before tensoring.

**Source property — not certified.** Symmetric monoidal model structure.

**Source use — context only.** Derived algebraic geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K26.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k27"></a>

#### K27. `Grothendieck` — Grothendieck construction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Functor C → Cat × → fibration

**Source definition.** ∫_C F has objects (c, x ∈ F(c)) and arrows compatibly.

**Source property — not certified.** Equivalent to category of fibrations over C.

**Source use — context only.** Indexed families of categories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K27.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k28"></a>

#### K28. `Quillen` — Quillen adjunction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Model cat pair × adjunction → Quillen adjunction

**Source definition.** F ⊣ G with F preserving cofibrations and acyclic cofibrations.

**Source property — not certified.** Induces total derived functors LF ⊣ RG.

**Source use — context only.** Homotopical algebra.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K28.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k29"></a>

#### K29. `Yan` — categorical pullback (fiber product)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Spans X → Z ← Y → object

**Source definition.** X ×_Z Y := limit of the cospan.

**Source property — not certified.** Universal property: maps to X ×_Z Y are pairs that agree in Z.

**Source use — context only.** Gluing constructions, base change.

**QPT-128 substitution.** Use only through [A16](#a16), [A18](#a18), [A28](#a28), with each contract and its four research questions.

**Eligibility question for K29.** Are both good-key events defined on exactly the same key-generation probability space? Identify the exact role of this operator in that derivation.

<a id="op-k30"></a>

#### K30. `Pul` — pushout

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Spans X ← Z → Y → object

**Source definition.** X ⊔_Z Y := colimit of the span.

**Source property — not certified.** Dual to pullback.

**Source use — context only.** Cell attachments in CW complexes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K30.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k31"></a>

#### K31. `Coeq` — coequalizer

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Parallel arrows f, g: A → B → object

**Source definition.** coeq(f,g) := B / (f(a) ∼ g(a)).

**Source property — not certified.** Universal quotient.

**Source use — context only.** Quotients in groups, modules, manifolds.

**QPT-128 substitution.** Use only through [A12](#a12), with each contract and its four research questions.

**Eligibility question for K31.** For a binary replacement, which two distinct accepted responses reconstruct the actual quorum witness? Identify the exact role of this operator in that derivation.

<a id="op-k32"></a>

#### K32. `Eq` — equalizer

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Parallel arrows × → object

**Source definition.** eq(f,g) := { a : f(a) = g(a) }.

**Source property — not certified.** Dual of coeq.

**Source use — context only.** Kernels and zero loci.

**QPT-128 substitution.** Use only through [A18](#a18), [A28](#a28), with each contract and its four research questions.

**Eligibility question for K32.** Does the proof apply to the current verifier, or only to a proposed commit-and-open replacement? Identify the exact role of this operator in that derivation.

<a id="op-k33"></a>

#### K33. `⨂_horiz` — horizontal composition of natural transformations

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Nat(F, G) × Nat(H, K) → Nat(HF, KG)

**Source definition.** (β ∗ α)_X := β_{GX} ∘ H(α_X) = K(α_X) ∘ β_{FX}.

**Source property — not certified.** Middle-four interchange with vertical composition.

**Source use — context only.** 2-category structure of Cat.

**QPT-128 substitution.** Use only through [A18](#a18), with each contract and its four research questions.

**Eligibility question for K33.** Which committed values does D contain and which deterministic algorithm reconstructs each complete witness? Identify the exact role of this operator in that derivation.

<a id="op-k34"></a>

#### K34. `⨂_vert` — vertical composition of natural transformations

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Nat(F, G) × Nat(G, H) → Nat(F, H)

**Source definition.** (β ∘ α)_X := β_X ∘ α_X.

**Source property — not certified.** Associative; identities are id_F.

**Source use — context only.** Categories of functors.

**QPT-128 substitution.** Use only through [A18](#a18), with each contract and its four research questions.

**Eligibility question for K34.** Are the two roots, public statements and witness encodings uniquely tied to the same roster and epoch? Identify the exact role of this operator in that derivation.

<a id="op-k35"></a>

#### K35. `Cosk` — coskeleton

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** sSet × n → sSet

**Source definition.** cosk_n X := right Kan extension along truncation.

**Source property — not certified.** Right adjoint to truncation.

**Source use — context only.** Higher coherence data.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K35.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k36"></a>

#### K36. `Sk_n` — skeleton

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** sSet × n → sSet

**Source definition.** sk_n X := subset generated by simplices of dim ≤ n.

**Source property — not certified.** Left adjoint to truncation.

**Source use — context only.** Cellular filtrations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K36.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k37"></a>

#### K37. `Sing` — singular simplicial functor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Top → sSet

**Source definition.** Sing(X)_n := Hom(Δ^n, X).

**Source property — not certified.** Right adjoint to geometric realization.

**Source use — context only.** Comparison of topological and combinatorial homotopy.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K37.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k38"></a>

#### K38. `|−|` — geometric realization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** sSet → Top

**Source definition.** |X| := ⊔ Δ^n × X_n / equivalence.

**Source property — not certified.** Left adjoint to Sing.

**Source use — context only.** Connecting categorical and topological data.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K38.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k39"></a>

#### K39. `Indo` — ind-completion

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Small cat → cocomplete cat

**Source definition.** Ind(C) := filtered colimits of C-objects.

**Source property — not certified.** Free cocompletion under filtered colimits.

**Source use — context only.** Locally finitely presentable categories.

**Amendment (DOMAIN_GAP).** Ind(C) freely adds filtered colimits. It is not automatically cocomplete for an arbitrary small category without further hypotheses.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K39.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k40"></a>

#### K40. `Pro` — pro-completion

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Small cat → complete cat

**Source definition.** Pro(C) := cofiltered limits of C-objects.

**Source property — not certified.** Dual to Ind.

**Source use — context only.** Profinite groups, pro-objects.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K40.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k41"></a>

#### K41. `Fr_C` — free monad

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Endofunctor → monad

**Source definition.** Fr(F) := free monad generated by F.

**Source property — not certified.** Initial in monads under F.

**Source use — context only.** Algebraic effects.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K41.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k42"></a>

#### K42. `Cof` — cofibrant replacement

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Model cat × object → cofibrant object

**Source definition.** QX → X with Q cofibrant.

**Source property — not certified.** Functorial in many model structures.

**Source use — context only.** Derived functor construction.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K42.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k43"></a>

#### K43. `Fib` — fibrant replacement

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Model cat × → ×

**Source definition.** X → RX with RX fibrant.

**Source property — not certified.** Functorial.

**Source use — context only.** Computing homotopy limits.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K43.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k44"></a>

#### K44. `⊥_op` — orthogonality operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Class of maps → class

**Source definition.** S^⊥ := { f : f ⊥ s for all s ∈ S }.

**Source property — not certified.** Galois connection between classes of maps; basis of factorization systems.

**Source use — context only.** Weak factorization systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K44.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k45"></a>

#### K45. `Fact` — factorization-system operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Cat × (L, R) → factorization of every map

**Source definition.** Each f factors as r ∘ ℓ, ℓ ∈ L, r ∈ R, functorially.

**Source property — not certified.** Defines orthogonal pair (L, R).

**Source use — context only.** Model categories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K45.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k46"></a>

#### K46. `Ext_op` — extension operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Object X × → maps from X

**Source definition.** Defines maps out of X; covariant by composition.

**Source property — not certified.** Functorial in X.

**Source use — context only.** Universal properties.

**Amendment (VARIANCE_ERROR).** Hom(X,-) is covariant in its target and contravariant in X. Specify which argument varies.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K46.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k47"></a>

#### K47. `Restr` — restriction along a functor

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** F: A → B × functor B → C → functor A → C

**Source definition.** (F^* G)(a) := G(F(a)).

**Source property — not certified.** Has both Kan-extension adjoints.

**Source use — context only.** Pullback of functors.

**QPT-128 substitution.** Use only through [A22](#a22), with each contract and its four research questions.

**Eligibility question for K47.** Are setup costs, cached advice or precomputation inside the target adversary budget? Identify the exact role of this operator in that derivation.

<a id="op-k48"></a>

#### K48. `LIM_w` — weighted limit

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C × J × weighting W: J → V → V-enriched limit

**Source definition.** lim^W F := equalizer reflecting weighted cones.

**Source property — not certified.** Reduces to ordinary limit when W = 1.

**Source use — context only.** Enriched-category constructions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K48.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k49"></a>

#### K49. `COLIM_w` — weighted colimit

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** colim^W F := dual of weighted limit.

**Source property — not certified.** Bicompletion of V-cat.

**Source use — context only.** Tensor of functor with weighting.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for K49.** Can this categorical construction be instantiated as typed algorithms between the exact games, with a proved adapter and a concrete resource map?

<a id="op-k50"></a>

#### K50. `Loc_op` — localization functor

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Cat × class of arrows W → cat

**Source definition.** C[W^{-1}] := universal cat with arrows of W inverted.

**Source property — not certified.** Triangulated/derived categories arise this way.

**Source use — context only.** Inverting weak equivalences.

**QPT-128 substitution.** Use only through [A20](#a20), with each contract and its four research questions.

**Eligibility question for K50.** Is a random ideal permutation being silently replaced with the known Keccak permutation? Identify the exact role of this operator in that derivation.

### Family N: Noncommutative algebra

<a id="op-n1"></a>

#### N1. `*_free` — free product (groups)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Groups × → group

**Source definition.** G * H := free group generated by G ⊔ H modulo G- and H-relations.

**Source property — not certified.** Universal property under homomorphisms agreeing on identity.

**Source use — context only.** Bass-Serre theory; group actions on trees.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N1.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n2"></a>

#### N2. `*_alg` — free product of algebras

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Algebras × → algebra

**Source definition.** A * B := tensor algebra modulo defining relations of A and B.

**Source property — not certified.** Coproduct in the category of unital algebras.

**Source use — context only.** Combining quantum-system algebras of observables.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N2.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n3"></a>

#### N3. `⊠_free` — free convolution (additive)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R)² → Δ(R)

**Source definition.** μ ⊠_+ ν := distribution of X + Y for free X, Y.

**Source property — not certified.** R-transform additive: R_{μ⊞ν} = R_μ + R_ν.

**Source use — context only.** Spectra of free sums of random matrices.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N3.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n4"></a>

#### N4. `⊠_mult` — free multiplicative convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R_+)² → Δ(R_+)

**Source definition.** S-transform multiplicative under free product of positive variables.

**Source property — not certified.** S_{μ⊠ν} = S_μ S_ν.

**Source use — context only.** Products of unitary-conjugated matrices.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N4.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n5"></a>

#### N5. `R_free` — R-transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R) → analytic at 0

**Source definition.** R_μ(z) := G_μ^{-1}(z) - 1/z; analog of log of moment generating function.

**Source property — not certified.** Additive under free convolution.

**Source use — context only.** Free cumulants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N5.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n6"></a>

#### N6. `S_free` — S-transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R_+) → analytic

**Source definition.** S_μ(z) := (z+1)/z · ψ_μ^{-1}(z).

**Source property — not certified.** Multiplicative under free multiplicative convolution.

**Source use — context only.** Multiplicative spectra in free probability.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N6.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n7"></a>

#### N7. `κ_n_free` — free cumulant

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ × ℕ → R

**Source definition.** κ_n := coefficient of z^{n-1} in R_μ.

**Source property — not certified.** All mixed free cumulants κ_n(a, b, ..., a, b, ...) vanish iff free.

**Source use — context only.** Diagrammatic free-probability calculations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N7.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n8"></a>

#### N8. `m_n_free` — free moment

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ × ℕ → R

**Source definition.** m_n := E[X^n] for non-commutative X.

**Source property — not certified.** Combinatorial expansion m_n = Σ_{π ∈ NC(n)} Π κ_{|B|}.

**Source use — context only.** Computing spectra of random matrices.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N8.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n9"></a>

#### N9. `⊥_free` — freeness predicate

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sub-algebras × → boolean

**Source definition.** A_1, A_2 free if E[a_1 a_2 ... a_k] = 0 for any alternating sequence with E[a_i] = 0.

**Source property — not certified.** Non-commutative analog of independence.

**Source use — context only.** Voiculescu's free probability theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N9.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n10"></a>

#### N10. `kQ` — path algebra of a quiver

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Quiver Q × field k → algebra

**Source definition.** kQ := free k-module on paths, multiplication by concatenation.

**Source property — not certified.** Path concatenation forms an associative algebra.

**Source use — context only.** Representations of quivers (Gabriel).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N10.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n11"></a>

#### N11. `Aus` — Auslander-Reiten translation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** kQ-mod × → kQ-mod

**Source definition.** τ M := DExt^1(M, kQ) where D is k-duality.

**Source property — not certified.** Auslander-Reiten formula relates Hom and Ext.

**Source use — context only.** Representation type classification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N11.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n12"></a>

#### N12. `⊗_q_brd` — braided tensor product (Hopf algebra)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Hopf-algebra modules × → ×

**Source definition.** (V ⊗ W) with braiding from R-matrix.

**Source property — not certified.** Compatibility with braided coalgebra structure.

**Source use — context only.** Quantum-group representations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N12.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n13"></a>

#### N13. `Planar_op` — planar-algebra operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Planar tangles × → ×

**Source definition.** Tangles compose by gluing internal discs.

**Source property — not certified.** Generates Jones planar algebras.

**Source use — context only.** Subfactor theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N13.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n14"></a>

#### N14. `Sub_idx` — subfactor index

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Inclusion N ⊂ M of II_1 factors → R_+ ∪ {∞}

**Source definition.** [M : N] := dim_N M.

**Source property — not certified.** Jones: [M:N] ∈ {4 cos²(π/n)} ∪ [4, ∞].

**Source use — context only.** Classification of subfactors.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N14.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n15"></a>

#### N15. `⊠_C` — Connes bimodule tensor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** M-N-bimodule × N-P-bimodule → M-P-bimodule

**Source definition.** Tensor over N with both module structures.

**Source property — not certified.** Defines correspondences and a 2-category of factors.

**Source use — context only.** Connes' correspondence theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N15.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n16"></a>

#### N16. `Conn_temp` — Connes-Takesaki temperature

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** II_∞ factor × → R-action

**Source definition.** Modular automorphism group σ^φ_t for a faithful weight φ.

**Source property — not certified.** Tomita-Takesaki theory: σ^φ_t intrinsic up to inner.

**Source use — context only.** KMS states in physics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N16.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n17"></a>

#### N17. `τ_trace` — trace on II_1 factor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** II_1 factor → C

**Source definition.** Unique normal faithful tracial state.

**Source property — not certified.** tr(xy) = tr(yx); central in factor classification.

**Source use — context only.** Murray-von Neumann dimension theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N17.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n18"></a>

#### N18. `Murr_dim` — Murray-von Neumann dimension

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Projection in II_1 factor → [0, 1]

**Source definition.** dim(P) := τ(P).

**Source property — not certified.** Continuous; takes all values in [0,1].

**Source use — context only.** Continuous-dimension geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N18.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n19"></a>

#### N19. `FCom` — free commutator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Non-comm algebra² → algebra

**Source definition.** [a, b] := ab - ba.

**Source property — not certified.** Standard commutator; bilinear and antisymmetric.

**Source use — context only.** Heisenberg uncertainty.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for N19.** Where would an earlier measurement change the probability of the second verification? Identify the exact role of this operator in that derivation.

<a id="op-n20"></a>

#### N20. `FAnti` — free anticommutator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** {a, b} := ab + ba.

**Source property — not certified.** Bilinear; symmetric; defining Clifford algebra.

**Source use — context only.** Pauli, Dirac matrices.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N20.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n21"></a>

#### N21. `OPL` — operator-valued log

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** B(H) (with spectrum away from R_{<0}) → B(H)

**Source definition.** log(T) := ∫ (1/(λ-T) - 1/(λ-I)) dλ on a suitable contour.

**Source property — not certified.** Inverse to operator exponential.

**Source use — context only.** Heat semigroup analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N21.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n22"></a>

#### N22. `⊗_CCR` — CCR tensor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Symplectic space × symplectic space → CCR algebra

**Source definition.** [a(f), a*(g)] = ⟨f, g⟩.

**Source property — not certified.** Generates the Weyl algebra.

**Source use — context only.** Quantum field theory of bosons.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N22.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n23"></a>

#### N23. `⊗_CAR` — CAR tensor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Hilbert space × → CAR algebra

**Source definition.** {a(f), a*(g)} = ⟨f, g⟩.

**Source property — not certified.** Generates anticommutative algebra.

**Source use — context only.** Fermionic quantum field theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N23.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n24"></a>

#### N24. `Fock_op` — Fock-space construction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Hilbert space × (bosonic / fermionic) → Fock space

**Source definition.** ℱ_±(H) := ⊕ Sym^n H (or Λ^n).

**Source property — not certified.** Carries CCR or CAR algebra.

**Source use — context only.** Many-body quantum systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N24.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n25"></a>

#### N25. `Wick` — Wick ordering

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Polynomial in CCR/CAR → normal-ordered polynomial

**Source definition.** :a(f) a*(g): := a*(g) a(f) plus correction terms.

**Source property — not certified.** Removes vacuum divergences.

**Source use — context only.** Quantum field theory renormalization.

**Amendment (FORMULA_ERROR).** Normal ordering moves creation operators left, with fermionic signs where applicable. Contraction correction terms belong to the expansion of an unordered product into normally ordered terms, not to the normally ordered monomial itself.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N25.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n26"></a>

#### N26. `Φ_HS` — Haagerup-Speicher operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Probabilistic data → non-commutative dist.

**Source definition.** Constructs *-distribution from moment data.

**Source property — not certified.** Universal in random-matrix limit theorems.

**Source use — context only.** Random matrix asymptotic spectral analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N26.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n27"></a>

#### N27. `Vor` — Voronoi pairing

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Quantum group dual pair → bilinear pairing

**Source definition.** ⟨φ, x⟩ for φ ∈ A°, x ∈ A.

**Source property — not certified.** Compatible with co-product.

**Source use — context only.** Tannaka-Krein-like dualities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N27.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n28"></a>

#### N28. `OPE` — operator product expansion

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Pair of local operators × → local-operator expansion

**Source definition.** O_1(x) O_2(y) ~ Σ_k C^k(x-y) O_k((x+y)/2).

**Source property — not certified.** Defines local algebra in CFT.

**Source use — context only.** Conformal field theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N28.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n29"></a>

#### N29. `L_n_Vir` — Virasoro generators

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** CFT → Lie algebra

**Source definition.** [L_n, L_m] = (n - m) L_{n+m} + (c/12)(n³ - n) δ_{n+m,0}.

**Source property — not certified.** Central extension of Witt algebra by central charge c.

**Source use — context only.** Conformal symmetry in 2D field theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N29.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n30"></a>

#### N30. `Kac_Moody` — affine Kac-Moody generator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Loop algebra → central extension

**Source definition.** [J^a_m, J^b_n] = f^{abc} J^c_{m+n} + k m δ^{ab} δ_{m+n,0}.

**Source property — not certified.** Central extension labeled by level k.

**Source use — context only.** WZW models, current algebras.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N30.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n31"></a>

#### N31. `⊗_red` — reduced group C*-algebra

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Discrete group → C*-algebra

**Source definition.** C*_r(G) := closure of λ(C[G]) in B(ℓ²(G)).

**Source property — not certified.** Equals full C*(G) iff G amenable.

**Source use — context only.** Operator-algebraic group representations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N31.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n32"></a>

#### N32. `⊗_full` — full group C*-algebra

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Discrete group → C*-algebra

**Source definition.** C*(G) := completion in maximal C*-norm.

**Source property — not certified.** Universal: representations of G ↔ representations of C*(G).

**Source use — context only.** Baum-Connes assembly map.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N32.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n33"></a>

#### N33. `vN_alg` — von Neumann algebra closure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Subset of B(H) → vN algebra

**Source definition.** M'' := double commutant.

**Source property — not certified.** Double-commutant theorem: M'' = strong closure for unital *-subalgebras.

**Source use — context only.** Mathematical foundations of QM.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N33.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n34"></a>

#### N34. `Mod_op_T` — modular operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** vN algebra × cyclic separating vector → ×

**Source definition.** Δ := S* S for S(xΩ) := x*Ω.

**Source property — not certified.** Defines the modular automorphism group of Tomita-Takesaki.

**Source use — context only.** KMS states; QFT thermal states.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N34.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n35"></a>

#### N35. `Jor` — Jordan algebra product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Algebra → Jordan algebra

**Source definition.** a ∘ b := (ab + ba)/2.

**Source property — not certified.** Commutative, satisfies Jordan identity.

**Source use — context only.** Quantum logic, Jordan formulations of QM.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N35.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n36"></a>

#### N36. `Lie_alg_op` — Lie algebraization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Associative algebra A → Lie algebra A_L

**Source definition.** [a, b] := ab - ba.

**Source property — not certified.** Forgetful functor with left adjoint U(g) (universal enveloping).

**Source use — context only.** Representation theory of Lie groups.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N36.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n37"></a>

#### N37. `Univ_env` — universal enveloping algebra

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lie algebra → associative algebra

**Source definition.** U(g) := T(g) / ⟨xy - yx - [x,y]⟩.

**Source property — not certified.** Hopf algebra with primitive g.

**Source use — context only.** Lifting Lie representations to associative algebras.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N37.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n38"></a>

#### N38. `PBW` — Poincaré-Birkhoff-Witt basis

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Universal enveloping × ordered basis → basis

**Source definition.** Monomials x_{i_1}^{a_1} ... x_{i_k}^{a_k} with i_1 < ... < i_k.

**Source property — not certified.** Free associative basis ordered by chosen ordering.

**Source use — context only.** Explicit computations in U(g).

**Amendment (TYPE_GAP).** PBW monomials form a vector-space basis of U(g); U(g) is not a free associative algebra on those generators in general.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N38.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n39"></a>

#### N39. `ad_g` — adjoint action

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lie alg × → endomorphism

**Source definition.** ad_x(y) := [x, y].

**Source property — not certified.** Lie-algebra homomorphism g → End(g).

**Source use — context only.** Roots and weights of g.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N39.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n40"></a>

#### N40. `Killing` — Killing form

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lie algebra² → R

**Source definition.** B(x, y) := tr(ad_x ad_y).

**Source property — not certified.** Bilinear invariant; non-degenerate iff g semisimple (Cartan).

**Source use — context only.** Cartan classification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N40.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n41"></a>

#### N41. `Casimir` — Casimir element

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lie algebra → U(g)

**Source definition.** C := Σ x^i x_i (Killing-dual basis).

**Source property — not certified.** Central in U(g); acts by scalar on irreducibles.

**Source use — context only.** Lie-algebra Laplacian.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N41.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n42"></a>

#### N42. `Verma` — Verma module functor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lie algebra × highest weight λ → module

**Source definition.** M(λ) := U(g) ⊗_{U(b)} C_λ.

**Source property — not certified.** Free U(n^-)-module on highest weight vector.

**Source use — context only.** Weyl character formula.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N42.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n43"></a>

#### N43. `BGG` — BGG resolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lie algebra × λ → resolution

**Source definition.** Resolves finite-dim L(λ) by Verma modules indexed by Weyl group.

**Source property — not certified.** Differentials given by divided differences.

**Source use — context only.** Computing Lie cohomology and characters.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N43.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n44"></a>

#### N44. `HC` — Harish-Chandra homomorphism

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Z(U(g)) → S(h)^W

**Source definition.** Sends z to its image in symmetric algebra of h modulo Weyl-group invariants.

**Source property — not certified.** Isomorphism (HC theorem).

**Source use — context only.** Central characters.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N44.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n45"></a>

#### N45. `Whit_rep` — Whittaker representation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lie group × generic character of N → induced representation

**Source definition.** Ind_N^G ψ; gives generic representations.

**Source property — not certified.** Multiplicity-one and uniqueness theorems.

**Source use — context only.** Automorphic forms.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N45.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n46"></a>

#### N46. `Sat_op` — Satake transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Spherical Hecke algebra → Weyl-invariant Laurent polynomials

**Source definition.** Satake: H(G, K) ≅ R[X^*(T)]^W.

**Source property — not certified.** Geometric Satake equivalence categorifies it.

**Source use — context only.** Langlands program.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N46.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n47"></a>

#### N47. `⊗_2cat` — tensor product in 2-categories

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** 2-cat objects × → ×

**Source definition.** Bi-functorial extension.

**Source property — not certified.** Coherence pseudo-natural transformations and modifications.

**Source use — context only.** Higher representation theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N47.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n48"></a>

#### N48. `Cat_irr` — category of irreducibles

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Algebra → category of finite-dim irreps

**Source definition.** Irr(A) := skeleton of finite-dim simple modules.

**Source property — not certified.** For semisimple algebras: ⊕ End(V_i).

**Source use — context only.** Fusion categories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N48.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n49"></a>

#### N49. `Hopf_dual` — Hopf-dual operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Hopf algebra → Hopf algebra

**Source definition.** A^° := elements of A* of finite rank under coproduct.

**Source property — not certified.** Hopf-algebra duality.

**Source use — context only.** Affine quantum-group constructions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N49.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

<a id="op-n50"></a>

#### N50. `BV_op` — Batalin-Vilkovisky operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Graded-commutative algebra → degree -1 operator

**Source definition.** Δ satisfying Δ² = 0 and the BV master equation.

**Source property — not certified.** Encodes gauge symmetry homologically.

**Source use — context only.** Quantization of gauge theories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for N50.** Can this noncommutative construction be realized on finite quantum registers with explicit positive maps and a proved operational probability bound?

### Family X: Stochastic calculus

<a id="op-x1"></a>

#### X1. `D_Mal` — Malliavin derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Smooth Wiener functional → L²(Ω; H)

**Source definition.** D F := Σ ∂_k F(B(h_1), ..., B(h_n)) h_k for F = f(B(h_1), ..., B(h_n)).

**Source property — not certified.** Closable on D^{1,2}; chain rule holds.

**Source use — context only.** Sensitivity analysis of Wiener-functionals.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X1.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x2"></a>

#### X2. `δ_Sk` — Skorokhod divergence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Adapted/anticipating processes → L²(Ω)

**Source definition.** δ(u) := ∫_0^T u_s dB_s (Skorokhod integral, extending Itô).

**Source property — not certified.** Adjoint of D in L²; reduces to Itô for adapted u.

**Source use — context only.** Anticipating stochastic calculus.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X2.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x3"></a>

#### X3. `I_n` — Wiener chaos projection

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L²(Ω) × ℕ → n-th Wiener chaos

**Source definition.** L²(Ω) = ⊕ H_n; I_n is the projection.

**Source property — not certified.** Hilbert-direct sum (Wiener-Itô).

**Source use — context only.** Spectral decomposition of Wiener functionals.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X3.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x4"></a>

#### X4. `OU` — Ornstein-Uhlenbeck semigroup

**Disposition.** ACTIVE INVESTIGATION; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** L²(Ω) × t → ×

**Source definition.** P_t F := E[F(e^{-t} W + √(1-e^{-2t}) W')].

**Source property — not certified.** Generator -L = sum n I_n; symmetric on L².

**Source use — context only.** Spectral analysis of Wiener functionals.

**QPT-128 substitution.** Use only through [A27](#a27), with each contract and its four research questions.

**Eligibility question for X4.** Is any truncation of long memory accompanied by a rigorous tail bound and a counted computational cost? Identify the exact role of this operator in that derivation.

<a id="op-x5"></a>

#### X5. `ClOc` — Clark-Ocone formula

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Smooth Wiener functional F → predictable integrand

**Source definition.** F = E F + ∫_0^T E[D_s F | F_s] dB_s.

**Source property — not certified.** Explicit hedging strategy.

**Source use — context only.** Mathematical finance, optimal portfolios.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X5.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x6"></a>

#### X6. `⊗_RP` — rough-path integration

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** α-Hölder path (α > 1/3) + Lévy area → integral

**Source definition.** ∫ f(X) dX in the rough-path sense.

**Source property — not certified.** Continuous in X under suitable Hölder + Lévy-area topology.

**Source use — context only.** Robust SDE solutions under irregular driving signals.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X6.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x7"></a>

#### X7. `RS_op` — regularity-structure operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Singular SPDE × model → modeled distribution

**Source definition.** Reconstruction theorem associates a distribution to a coherent local expansion.

**Source property — not certified.** Hairer; provides solution theory for KPZ, Φ^4_3.

**Source use — context only.** Renormalization of singular SPDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X7.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x8"></a>

#### X8. `Renorm_BPHZ` — BPHZ renormalization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Trees / Feynman graphs × → renormalized integrands

**Source definition.** Recursively subtracts subdivergences via forest formula.

**Source property — not certified.** Yields finite integrals from divergent perturbative expansions.

**Source use — context only.** Quantum-field theory renormalization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X8.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x9"></a>

#### X9. `BSDE` — BSDE solution operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Generator f × terminal condition ξ → (Y, Z)

**Source definition.** Y_t = ξ + ∫_t^T f(s, Y_s, Z_s) ds - ∫_t^T Z_s dB_s.

**Source property — not certified.** Existence/uniqueness for Lipschitz f (Pardoux-Peng).

**Source use — context only.** Stochastic control, finance pricing.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X9.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x10"></a>

#### X10. `MKV` — McKean-Vlasov SDE operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Drift b, diffusion σ depending on (X, P_X) → process

**Source definition.** dX_t = b(t, X_t, P_{X_t}) dt + σ(t, X_t, P_{X_t}) dB_t.

**Source property — not certified.** Well-posedness under W_p-Lipschitz coefficients.

**Source use — context only.** Mean-field interacting particle limits.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X10.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x11"></a>

#### X11. `FW` — Freidlin-Wentzell action

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Diffusion × path → R_+

**Source definition.** I(γ) := (1/2) ∫_0^T |γ̇ - b(γ)|²_{a^{-1}} dt for small-noise limit.

**Source property — not certified.** Rate function for LDP.

**Source use — context only.** Metastability and exit-problem analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X11.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x12"></a>

#### X12. `IS_qv` — quadratic-variation operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Semimartingale → continuous adapted

**Source definition.** [X]_t := lim Σ (X_{t_{i+1}} - X_{t_i})².

**Source property — not certified.** [B]_t = t for Brownian motion.

**Source use — context only.** Itô formula correction term.

**Amendment (DOMAIN_GAP).** The displayed continuous quadratic-variation/Itô formulas apply to continuous semimartingales. General jump processes need jump terms, and their quadratic variation need not be continuous.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X12.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x13"></a>

#### X13. `It_form` — Itô's formula

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Semimartingale × C² function → semimartingale

**Source definition.** df(X) = f'(X) dX + (1/2) f''(X) d[X].

**Source property — not certified.** Master tool of stochastic calculus.

**Source use — context only.** PDE-SDE correspondence.

**Amendment (DOMAIN_GAP).** The displayed continuous quadratic-variation/Itô formulas apply to continuous semimartingales. General jump processes need jump terms, and their quadratic variation need not be continuous.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X13.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x14"></a>

#### X14. `FK` — Feynman-Kac operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** PDE × → SDE expectation

**Source definition.** u(t, x) := E[g(X_T) exp(-∫_t^T V(X_s) ds) | X_t = x] solves parabolic PDE.

**Source property — not certified.** Probabilistic representation of solutions.

**Source use — context only.** Option pricing.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X14.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x15"></a>

#### X15. `DK` — Dynkin operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** C² × diffusion → ×

**Source definition.** L f(x) := lim_{t↓0} (E[f(X_t) | X_0 = x] - f(x))/t.

**Source property — not certified.** Generates Markov semigroup.

**Source use — context only.** Infinitesimal-generator analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X15.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x16"></a>

#### X16. `PG` — Pólya generating operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Distribution × → Poisson-mixture

**Source definition.** Builds compound Poisson distribution with given jump distribution.

**Source property — not certified.** Probability generating function multiplicative under independence.

**Source use — context only.** Insurance claim modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X16.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x17"></a>

#### X17. `Levy_⊗` — Lévy-process composition

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Lévy triple (b, A, ν) × → ×

**Source definition.** Independent increments with characteristic exponent ψ(ξ) = ibξ - (1/2) Aξ² + ∫ (e^{iξx} - 1 - iξx 1_{|x|≤1}) ν(dx).

**Source property — not certified.** Lévy-Khintchine representation.

**Source use — context only.** Heavy-tailed financial models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X17.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x18"></a>

#### X18. `Levy_pm` — Lévy-process partial maximum

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Lévy path × time → ×

**Source definition.** M_t := sup_{s ≤ t} X_s.

**Source property — not certified.** Wiener-Hopf factorization for distribution.

**Source use — context only.** Ruin theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X18.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x19"></a>

#### X19. `Skor` — Skorokhod embedding operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Δ(R) → stopping time on Brownian motion

**Source definition.** τ : E[B_τ] = E_μ X, distribution of B_τ = μ.

**Source property — not certified.** Existence (Skorokhod, Dubins, Azéma-Yor): many constructions.

**Source use — context only.** Embedding measures into Brownian motion.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X19.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x20"></a>

#### X20. `Doob_op` — Doob h-transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Markov process × harmonic h > 0 → conditioned process

**Source definition.** Generator L^h f := L(hf)/h - (Lh)/h · f.

**Source property — not certified.** Conditions process to behave according to h.

**Source use — context only.** Conditioned Brownian motion.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X20.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x21"></a>

#### X21. `Tan` — Tanaka's formula

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Brownian motion × → ×

**Source definition.** |B_t - a| = |B_0 - a| + ∫_0^t sgn(B_s - a) dB_s + L^a_t.

**Source property — not certified.** Defines local time L^a.

**Source use — context only.** Local-time analysis at a level.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X21.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x22"></a>

#### X22. `LT_op` — local-time operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Continuous semimartingale × level a → continuous increasing process

**Source definition.** L^a_t := lim_{ε↓0} (1/2ε) ∫_0^t 1_{|X_s - a| ≤ ε} d[X]_s.

**Source property — not certified.** Occupation density at a; L^a is jointly measurable.

**Source use — context only.** Ray-Knight theorems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X22.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x23"></a>

#### X23. `RK` — Ray-Knight theorem operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Brownian motion × → distribution of local-time process

**Source definition.** {L^a_τ : a ∈ R} is a specific Markov process (BES(3)² etc.).

**Source property — not certified.** Foundational identification in BM-local-time theory.

**Source use — context only.** Brownian motion structure theorems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X23.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x24"></a>

#### X24. `SDE_strong` — strong SDE solution operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (b, σ, B, x_0) → adapted process

**Source definition.** X_t = x_0 + ∫_0^t b ds + ∫_0^t σ dB.

**Source property — not certified.** Uniqueness via Lipschitz coefficients (Itô).

**Source use — context only.** Diffusion modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X24.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x25"></a>

#### X25. `SDE_weak` — weak SDE solution operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (b, σ, μ_0) → probability law

**Source definition.** (Ω, F, P, X, B) with X solving SDE.

**Source property — not certified.** Martingale-problem formulation (Stroock-Varadhan).

**Source use — context only.** Diffusion limits.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X25.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x26"></a>

#### X26. `Mart_rep` — martingale representation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L²(F_T, P) × Brownian → predictable integrand

**Source definition.** Every F-martingale has unique stochastic-integral representation w.r.t. B.

**Source property — not certified.** Completeness theorem for Brownian filtration.

**Source use — context only.** Hedging in complete markets.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X26.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x27"></a>

#### X27. `Gir` — Girsanov transformation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Process M × measure P → measure Q with M_t a P-martingale

**Source definition.** dQ/dP = ε(M)_T (stochastic exponential).

**Source property — not certified.** Drift change for Brownian motion.

**Source use — context only.** Risk-neutral pricing.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X27.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x28"></a>

#### X28. `ε(M)` — stochastic exponential

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Continuous semimartingale → semimartingale

**Source definition.** ε(M)_t := exp(M_t - (1/2)[M]_t).

**Source property — not certified.** Multiplicative martingale when M is a continuous local martingale.

**Source use — context only.** Solution of dY = Y dM.

**Amendment (DOMAIN_GAP).** For a continuous local martingale M starting at zero, the stochastic exponential is a local martingale; it need not be a true martingale without an integrability condition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X28.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x29"></a>

#### X29. `Mart_prob` — martingale problem operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Operator L on C^2 × initial distribution → ×

**Source definition.** Find P such that f(X_t) - f(X_0) - ∫_0^t Lf(X_s) ds is a P-martingale for all f ∈ D(L).

**Source property — not certified.** Equivalent to SDE under regularity.

**Source use — context only.** Construction of diffusions from generators.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X29.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x30"></a>

#### X30. `LDP_op` — large-deviation principle operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Family of laws → rate function I

**Source definition.** P_ε(A) ≈ exp(-I(A)/ε); I(x) := -lim ε log P_ε(N_x).

**Source property — not certified.** Lower semi-continuous, often convex.

**Source use — context only.** Statistical mechanics, rare events.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X30.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x31"></a>

#### X31. `Diff_O` — Donsker invariance principle

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Random-walk family → Brownian motion

**Source definition.** S_{[nt]}/√n ⇒ B_t in C[0,1].

**Source property — not certified.** Donsker's theorem; FCLT for sums.

**Source use — context only.** Functional CLT.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X31.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x32"></a>

#### X32. `Diff_O_inv` — Donsker inverse

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Brownian motion → random walks approximating it

**Source definition.** Embedded via Skorokhod.

**Source property — not certified.** Construction of random walks with given asymptotic distribution.

**Source use — context only.** Discretization of SDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X32.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x33"></a>

#### X33. `Euler_M` — Euler-Maruyama scheme operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** SDE × discretization → discrete approximation

**Source definition.** X̂_{k+1} := X̂_k + b(X̂_k) Δt + σ(X̂_k) ΔB_k.

**Source property — not certified.** Strong order 1/2; weak order 1 under regularity.

**Source use — context only.** Numerical SDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X33.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x34"></a>

#### X34. `Milstein` — Milstein scheme operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** SDE × → ×

**Source definition.** Adds (1/2) σ σ' (ΔB² - Δt).

**Source property — not certified.** Strong order 1.

**Source use — context only.** Higher-order SDE integration.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X34.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x35"></a>

#### X35. `MLMC` — multilevel Monte Carlo

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** SDE × cost-target × → estimator

**Source definition.** E f(X_T) ≈ Σ_ℓ (E_ℓ - E_{ℓ-1}) at varying step sizes.

**Source property — not certified.** Computes expectations at optimal cost (Giles).

**Source use — context only.** Reduced-variance SDE Monte Carlo.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for X35.** Is the attack class being tested narrower than the QPT adversaries in the theorem? Identify the exact role of this operator in that derivation.

<a id="op-x36"></a>

#### X36. `Backward_PDE` — backward Kolmogorov operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Generator L × terminal condition → solution

**Source definition.** ∂_t u + L u = 0, u(T, x) = g(x).

**Source property — not certified.** u(t, x) = E[g(X_T) | X_t = x] (Feynman-Kac).

**Source use — context only.** PDE-Markov correspondence.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X36.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x37"></a>

#### X37. `Fwd_PDE` — forward Kolmogorov / Fokker-Planck

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Generator L × initial density → ×

**Source definition.** ∂_t p = L* p.

**Source property — not certified.** Adjoint of backward Kolmogorov.

**Source use — context only.** Density evolution of stochastic systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X37.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x38"></a>

#### X38. `Stratonov` — Stratonovich-Itô conversion operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Stratonovich SDE → Itô SDE

**Source definition.** σ ∘ dB = σ dB + (1/2) σ σ' dt (in 1D).

**Source property — not certified.** Connects geometric and Itô formulations.

**Source use — context only.** Geometric SDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X38.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x39"></a>

#### X39. `Lie_brk_SDE` — Lie-bracket operator for SDEs

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Vector fields × → vector field

**Source definition.** Stratonovich SDEs let one use ordinary Lie-bracket calculus.

**Source property — not certified.** Hörmander's bracket-condition implies hypoellipticity.

**Source use — context only.** Sub-Riemannian diffusions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X39.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x40"></a>

#### X40. `Hor` — Hörmander bracket condition

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Vector fields V_0, ..., V_d × → boolean

**Source definition.** {V_1,...,V_d, [V_i, V_j], ...} spans tangent space at every point.

**Source property — not certified.** Implies hypoellipticity of SDE generator.

**Source use — context only.** Smoothness of transition densities.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X40.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x41"></a>

#### X41. `Bismut` — Bismut formula operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Semigroup × test function → ×

**Source definition.** ∇_x E_x f(X_t) = (1/t) E[f(X_t) ∫_0^t U^* dB].

**Source property — not certified.** Derivative-free representation of gradient of expectation.

**Source use — context only.** Path-wise differentiation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X41.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x42"></a>

#### X42. `Mall_DK` — Malliavin Greeks operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Option price × parameter → sensitivity

**Source definition.** Delta = E[Payoff · Mall-weight].

**Source property — not certified.** Bypasses pathwise differentiation when payoffs are non-smooth.

**Source use — context only.** Computational finance.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X42.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x43"></a>

#### X43. `Pois_pp` — Poisson point process

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Intensity measure → random set

**Source definition.** N(A) ~ Poisson(λ(A)); independent on disjoint A.

**Source property — not certified.** Mecke-Slivnyak formula for Palm distributions.

**Source use — context only.** Stochastic geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X43.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x44"></a>

#### X44. `Camp` — Campbell's formula

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Poisson point × measurable f → ×

**Source definition.** E[Σ_x f(x)] = ∫ f(x) dλ(x).

**Source property — not certified.** Linearity of Poisson integration.

**Source use — context only.** Spatial-statistics expectations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X44.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x45"></a>

#### X45. `FB` — filtering operator (Kushner-Stratonovich)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Observation × signal → conditional law

**Source definition.** π_t f := E[f(X_t) | F^Y_t]; evolves by SPDE.

**Source property — not certified.** Innovation process drives non-linear filter.

**Source use — context only.** Optimal nonlinear filtering.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X45.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x46"></a>

#### X46. `Zakai` — Zakai equation operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Filtering × → unnormalized density

**Source definition.** dρ_t = L* ρ_t dt + ρ_t H dY_t.

**Source property — not certified.** Linear unnormalized version of Kushner-Stratonovich.

**Source use — context only.** Stochastic PDE filtering.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X46.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x47"></a>

#### X47. `Pard` — Pardoux-Peng BSDE operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lipschitz coefficient × → Markov process pair

**Source definition.** Adapted (Y, Z) solving BSDE.

**Source property — not certified.** Comparison theorem under monotonicity.

**Source use — context only.** Semi-linear PDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X47.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x48"></a>

#### X48. `EDS_jmp` — SDE with jumps operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Drift × diffusion × jump measure ν → ×

**Source definition.** dX = b dt + σ dB + ∫ z Ñ(dt, dz).

**Source property — not certified.** Itô formula extended via jump-correction terms.

**Source use — context only.** Modeling discontinuous dynamics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X48.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x49"></a>

#### X49. `Mtg_BMO` — BMO-martingale operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Continuous local-martingale × → boolean

**Source definition.** ‖M‖_{BMO} := sup_τ ‖E[[M]_∞ - [M]_τ | F_τ]‖_∞^{1/2}.

**Source property — not certified.** Equivalent change of measure under Girsanov.

**Source use — context only.** Quadratic-growth BSDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X49.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

<a id="op-x50"></a>

#### X50. `Aron` — Aronson Gaussian heat-kernel bounds

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Uniformly elliptic operator × → ×

**Source definition.** c_1 t^{-d/2} exp(-C|x-y|²/t) ≤ p_t(x, y) ≤ C_2 t^{-d/2} exp(-c|x-y|²/t).

**Source property — not certified.** Diagonal and off-diagonal Gaussian estimates.

**Source use — context only.** Regularity of parabolic equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for X50.** Can this continuous stochastic result be given a finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail costs?

### Family G: Geometry and Lie/Clifford operators

<a id="op-g1"></a>

#### G1. `[·,·]` — Lie bracket

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** g² → g

**Source definition.** [X, Y] := XY - YX (matrix case); axiomatic via skew-symmetry + Jacobi.

**Source property — not certified.** Bilinear, antisymmetric, Jacobi identity.

**Source use — context only.** Infinitesimal symmetry algebra.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for G1.** Can both verifiers run before the one terminal database measurement in the intended security game? Identify the exact role of this operator in that derivation.

<a id="op-g2"></a>

#### G2. `L_X` — Lie derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Vect(M) × T(M) → T(M)

**Source definition.** L_X T := lim_{t→0} (φ_t^* T - T)/t with φ_t flow of X.

**Source property — not certified.** Commutes with d; satisfies Cartan magic formula on forms.

**Source use — context only.** Symmetries of differential equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G2.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g3"></a>

#### G3. `∧` — wedge product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Ω^p × Ω^q → Ω^{p+q}

**Source definition.** α ∧ β := antisymmetrization of α ⊗ β.

**Source property — not certified.** Graded commutative: α ∧ β = (-1)^{pq} β ∧ α.

**Source use — context only.** Differential forms on manifolds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G3.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g4"></a>

#### G4. `ι_X` — interior product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Vect(M) × Ω^p → Ω^{p-1}

**Source definition.** (ι_X α)(Y_1, ..., Y_{p-1}) := α(X, Y_1, ..., Y_{p-1}).

**Source property — not certified.** Graded derivation of degree -1; ι_X² = 0.

**Source use — context only.** Cartan's formula L_X = d ι_X + ι_X d.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G4.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g5"></a>

#### G5. `d` — exterior derivative

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Ω^p(M) → Ω^{p+1}(M)

**Source definition.** df(X) := X(f); extended uniquely to graded derivation with d² = 0.

**Source property — not certified.** d² = 0; defines de Rham complex.

**Source use — context only.** Stokes' theorem foundation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G5.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g6"></a>

#### G6. `*` — Hodge star

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Ω^p(M) × (oriented Riem g) → Ω^{n-p}(M)

**Source definition.** α ∧ *β := ⟨α, β⟩_g vol.

**Source property — not certified.** *² = (-1)^{p(n-p)} (Euclidean); switches sign on Lorentzian.

**Source use — context only.** Maxwell equations in form language.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G6.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g7"></a>

#### G7. `Δ_H` — Hodge Laplacian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Ω^p(M) → Ω^p(M)

**Source definition.** Δ_H := dd* + d*d.

**Source property — not certified.** Self-adjoint, non-negative; kernel = harmonic forms (Hodge theorem).

**Source use — context only.** Eigenforms of geometric Laplacians.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G7.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g8"></a>

#### G8. `·_C` — Clifford geometric product

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Cl(V, Q)² → Cl(V, Q)

**Source definition.** v · w := v ∧ w + Q(v, w).

**Source property — not certified.** Associative; recovers Q on the generating vectors.

**Source use — context only.** Spinors and Dirac equation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G8.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g9"></a>

#### G9. `⌒` — Clifford conjugation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Cl(V, Q) → Cl(V, Q)

**Source definition.** x̄: reverses order of generators and flips signs of all generators.

**Source property — not certified.** Anti-automorphism.

**Source use — context only.** Norms and inverses in Clifford algebras.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G9.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g10"></a>

#### G10. `Pin` — Pin group projection

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** O(V) → ×

**Source definition.** Pin(V) sits as a double cover of O(V) in Cl(V).

**Source property — not certified.** Lifts to Spin on connected component.

**Source use — context only.** Half-integer-spin representations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G10.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g11"></a>

#### G11. `Spin` — Spin group projection

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** SO(V) → ×

**Source definition.** Spin(V) is the connected double cover of SO(V).

**Source property — not certified.** π_1(SO(n)) = Z/2 for n ≥ 3.

**Source use — context only.** Fermions, Dirac fields.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G11.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g12"></a>

#### G12. `D_Dir` — Dirac operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Spinors on Spin manifold → spinors

**Source definition.** D := Σ e_i · ∇_{e_i}.

**Source property — not certified.** First-order elliptic; D² = ∇*∇ + (1/4) scal (Lichnerowicz).

**Source use — context only.** Atiyah-Singer; mass-energy in QFT.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G12.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g13"></a>

#### G13. `Ω` — curvature 2-form

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Principal bundle × connection → Lie-alg-valued 2-form

**Source definition.** Ω := dω + (1/2)[ω, ω].

**Source property — not certified.** Bianchi identity: dΩ + [ω, Ω] = 0.

**Source use — context only.** Yang-Mills field strength.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G13.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g14"></a>

#### G14. `T` — torsion form

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Principal bundle × ω → vector-valued 2-form

**Source definition.** T := dθ + ω ∧ θ for tautological 1-form θ.

**Source property — not certified.** Vanishes for Levi-Civita connection.

**Source use — context only.** Cartan geometries.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G14.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g15"></a>

#### G15. `Bia` — Bianchi identities

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Connection × → identity on Ω

**Source definition.** dΩ + [ω, Ω] = 0.

**Source property — not certified.** Constraint on curvature; automatically satisfied.

**Source use — context only.** Einstein equations consistency.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G15.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g16"></a>

#### G16. `Mom` — moment map

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** G-symplectic manifold (M, ω) → g*

**Source definition.** ι_{X_M} ω = d⟨μ, X⟩ for each X ∈ g.

**Source property — not certified.** Defines symplectic quotient M//G.

**Source use — context only.** Geometric quantization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G16.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g17"></a>

#### G17. `{·,·}_P` — Poisson bracket

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** C^∞(M) × C^∞(M) → C^∞(M)

**Source definition.** {f, g} := ω(X_f, X_g) for symplectic ω.

**Source property — not certified.** Bilinear, antisymmetric, Jacobi + Leibniz.

**Source use — context only.** Hamiltonian mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G17.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g18"></a>

#### G18. `Symp` — symplectic form

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** T*M × T*M → R

**Source definition.** ω = Σ dp_i ∧ dq_i (canonical).

**Source property — not certified.** Closed, non-degenerate.

**Source use — context only.** Canonical phase space.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G18.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g19"></a>

#### G19. `Kah` — Kähler form

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Complex manifold × Hermitian metric → 2-form

**Source definition.** ω = (i/2) g_{a b̄} dz^a ∧ dz̄^b.

**Source property — not certified.** Closed Hermitian; Kähler condition unifies Riemannian, complex, symplectic.

**Source use — context only.** String theory, complex geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G19.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g20"></a>

#### G20. `Ric` — Ricci curvature

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riemannian g → symmetric 2-tensor

**Source definition.** Ric(X, Y) := tr(Z ↦ R(Z, X) Y).

**Source property — not certified.** Reveals volume comparison via Bishop-Gromov.

**Source use — context only.** Einstein equations: Ric - (R/2) g + Λ g = 8π G T.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G20.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g21"></a>

#### G21. `R_Riem` — Riemann curvature tensor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riemannian g → (3,1)-tensor

**Source definition.** R(X, Y) Z := ∇_X ∇_Y Z - ∇_Y ∇_X Z - ∇_{[X,Y]} Z.

**Source property — not certified.** Algebraic symmetries; Bianchi identity.

**Source use — context only.** Tidal forces in general relativity.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G21.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g22"></a>

#### G22. `Sec` — sectional curvature

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 2-plane in T_p M → R

**Source definition.** K(σ) := R(X, Y, Y, X)/(|X|² |Y|² - ⟨X,Y⟩²).

**Source property — not certified.** Determines curvature tensor for any dimension via polarization.

**Source use — context only.** Comparison geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G22.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g23"></a>

#### G23. `scal` — scalar curvature

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riem g → C^∞(M)

**Source definition.** scal := tr_g Ric.

**Source property — not certified.** Variation = Einstein-Hilbert action.

**Source use — context only.** Einstein equations; positive mass theorems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G23.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g24"></a>

#### G24. `J` — almost-complex structure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** TM → TM

**Source definition.** J²= -id.

**Source property — not certified.** Integrable iff Nijenhuis vanishes; then M is a complex manifold.

**Source use — context only.** Complex geometry foundations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G24.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g25"></a>

#### G25. `N_J` — Nijenhuis tensor

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Almost-complex J → (1,2)-tensor

**Source definition.** N_J(X, Y) := [JX, JY] - J[JX, Y] - J[X, JY] - [X, Y].

**Source property — not certified.** Vanishes iff J integrable (Newlander-Nirenberg).

**Source use — context only.** Integrability of complex structures.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G25.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g26"></a>

#### G26. `Pf` — Pfaffian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Antisymmetric matrix → R

**Source definition.** Pf(A)² = det(A) for 2n × 2n antisymmetric.

**Source property — not certified.** Polynomial in entries; sign sensitive to orientation.

**Source use — context only.** Euler characteristic via Gauss-Bonnet.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G26.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g27"></a>

#### G27. `CS_op` — Chern-Simons operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Principal G-bundle on 3-mfd × connection → R/Z

**Source definition.** CS(A) := (1/8π²) ∫ tr(A ∧ dA + (2/3) A ∧ A ∧ A).

**Source property — not certified.** Gauge-invariant mod integers; flows to gauge-invariant action.

**Source use — context only.** Topological field theory, knot invariants.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G27.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g28"></a>

#### G28. `WZW` — Wess-Zumino-Witten term

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Map S² → G × extension to D³ → R/2π

**Source definition.** WZW(g) := (1/12π) ∫_{D³} tr((g^{-1} dg)³).

**Source property — not certified.** Topological action; level k ∈ Z.

**Source use — context only.** Conformal field theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G28.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g29"></a>

#### G29. `⨯_Lie` — exponential map

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** g → G

**Source definition.** exp(X) := γ_X(1), γ_X(t) = one-parameter subgroup.

**Source property — not certified.** Local diffeo near 0; geodesic flow for left-invariant metric.

**Source use — context only.** Lie-group integration.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G29.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g30"></a>

#### G30. `Ad` — adjoint action (group)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** G × g → g

**Source definition.** Ad_g(X) := g X g^{-1}.

**Source property — not certified.** Lie-algebra automorphism for each g.

**Source use — context only.** Group representations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G30.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g31"></a>

#### G31. `ad` — adjoint action (Lie algebra)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** g × g → g

**Source definition.** ad_X(Y) := [X, Y].

**Source property — not certified.** Derivation of g; image lies in Inner derivations.

**Source use — context only.** Linearization of Ad.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G31.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g32"></a>

#### G32. `CBH` — Campbell-Baker-Hausdorff

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** g² × → g

**Source definition.** log(exp X exp Y) = X + Y + (1/2)[X,Y] + ....

**Source property — not certified.** Lie series; converges for small X, Y.

**Source use — context only.** Computing Lie-group products.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G32.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g33"></a>

#### G33. `Inv_X` — invariance under flow

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Tensor field × vector field → tensor field

**Source definition.** T invariant under X iff L_X T = 0.

**Source property — not certified.** Defines symmetric tensor fields.

**Source use — context only.** Killing vector fields.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G33.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g34"></a>

#### G34. `Killing_X` — Killing vector field

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riemannian manifold → vector fields

**Source definition.** X such that L_X g = 0.

**Source property — not certified.** Form a Lie algebra of dimension ≤ n(n+1)/2.

**Source use — context only.** Symmetries of curved spacetimes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G34.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g35"></a>

#### G35. `∇_LC` — Levi-Civita connection

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riemannian metric → unique torsion-free metric connection

**Source definition.** ∇_X Y - ∇_Y X = [X, Y]; ∇g = 0.

**Source property — not certified.** Fundamental theorem of Riemannian geometry.

**Source use — context only.** Geodesic equations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G35.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g36"></a>

#### G36. `Geo` — geodesic equation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riem × initial (x, v) → curve

**Source definition.** ∇_{γ'} γ' = 0.

**Source property — not certified.** Locally length-minimizing in Riemannian case.

**Source use — context only.** GR free fall.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G36.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g37"></a>

#### G37. `Hol_G` — geometric holonomy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riem g × x_0 → subgroup of O(T_{x_0} M)

**Source definition.** Group generated by parallel transport around loops.

**Source property — not certified.** Berger classification of irreducible holonomies.

**Source use — context only.** Special holonomy: Calabi-Yau, G_2, Spin(7).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G37.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g38"></a>

#### G38. `Ωᵏ` — k-forms

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Manifold × ℕ → vector bundle

**Source definition.** Section of Λ^k T*M.

**Source property — not certified.** Forms a graded algebra under ∧.

**Source use — context only.** Differential geometry foundations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G38.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g39"></a>

#### G39. `HodSt` — Hodge theorem

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Compact Riem mfd × → cohomology

**Source definition.** H^k_dR(M) ≅ Harm^k(M).

**Source property — not certified.** Each cohomology class has a unique harmonic representative.

**Source use — context only.** Topology meets analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G39.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g40"></a>

#### G40. `BCO` — Bochner technique

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riem mfd × tensor → integral identity

**Source definition.** Compares Laplacian and Bochner-Lichnerowicz Laplacian via curvature term.

**Source property — not certified.** Vanishing theorems under positive curvature.

**Source use — context only.** Rigidity in Riemannian geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G40.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g41"></a>

#### G41. `Wzn` — Witten Laplacian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Riem mfd × Morse f × β → operator

**Source definition.** Δ_β := d_β d_β* + d_β* d_β with d_β := e^{-βf} d e^{βf}.

**Source property — not certified.** Concentrates on critical points as β → ∞.

**Source use — context only.** Morse-theoretic proofs of Hodge isomorphisms.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G41.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g42"></a>

#### G42. `Atia` — Atiyah-Singer index operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Elliptic operator on compact manifold → Z

**Source definition.** ind(D) := dim ker D - dim coker D = ∫_M ch(σ(D)) td(M).

**Source property — not certified.** Topological formula for an analytic index.

**Source use — context only.** Index theory; Dirac operator on spin manifolds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G42.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g43"></a>

#### G43. `Frob_Riem` — Frobenius theorem operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Distribution D ⊂ TM → integrability

**Source definition.** D integrable iff [Γ(D), Γ(D)] ⊂ Γ(D).

**Source property — not certified.** Locally given by foliation charts.

**Source use — context only.** Integrability of PDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G43.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g44"></a>

#### G44. `⨯_Stiefel` — Stiefel manifold operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (n, k) → manifold V_k(R^n)

**Source definition.** V_k(R^n) := { orthonormal k-frames in R^n }.

**Source property — not certified.** Fibers SO(n)/SO(n-k); π_{k-1}(V_k(R^n)) = 0 (Bott).

**Source use — context only.** Frame fields in physics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G44.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g45"></a>

#### G45. `Gr_op` — Grassmannian operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (n, k) → Gr(k, n)

**Source definition.** Gr(k, n) := { k-dim subspaces of R^n }.

**Source property — not certified.** Smooth projective variety of dimension k(n-k).

**Source use — context only.** Schubert calculus.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G45.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g46"></a>

#### G46. `Tot_chr` — total Chern character

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Complex vector bundle → H^*(B; Q)

**Source definition.** ch(E) := Σ e^{x_i} via splitting principle.

**Source property — not certified.** Ring homomorphism K(B) → H^*(B; Q).

**Source use — context only.** Atiyah-Singer ingredient.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G46.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g47"></a>

#### G47. `J_op` — complex-structure deformation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Almost-complex J × → deformation parameters

**Source definition.** Kuranishi space H^1(M, T_M) parameterizes infinitesimal deformations.

**Source property — not certified.** Obstructed by [α, α] ∈ H^2(M, T_M).

**Source use — context only.** Moduli of complex structures.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G47.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g48"></a>

#### G48. `Spec_op` — spectral flow

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Path of self-adjoint Fredholm operators × → Z

**Source definition.** Net number of eigenvalues crossing 0 from below.

**Source property — not certified.** Atiyah-Patodi-Singer invariant.

**Source use — context only.** Family-version index theorem.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G48.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g49"></a>

#### G49. `η_op` — eta invariant

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Self-adjoint elliptic operator → R

**Source definition.** η(D) := s = 0 value of η(s) := Σ sign(λ_k) |λ_k|^{-s}.

**Source property — not certified.** Local + global signature defect on a manifold with boundary.

**Source use — context only.** APS index theorem.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G49.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

<a id="op-g50"></a>

#### G50. `Sec_Lie` — section of associated bundle

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Principal G-bundle P × G-space F → fiber bundle P ×_G F

**Source definition.** Maps to F transforming under G-action.

**Source property — not certified.** Equivalent to G-equivariant maps P → F.

**Source use — context only.** Gauge theories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for G50.** Which finite-dimensional cryptographic object does this geometric operator act on, and what event-preserving reduction connects its invariant to security?

### Family R: Quantum resource theory

<a id="op-r1"></a>

#### R1. `≺` — majorization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ_n × Δ_n → boolean

**Source definition.** p ≺ q iff Σ_{i=1}^k p^↓_i ≤ Σ_{i=1}^k q^↓_i for all k, with equality at k=n.

**Source property — not certified.** Partial order; q most disordered when uniform.

**Source use — context only.** Resource theory of purity.

**Amendment (PRECISION).** Majorization is a preorder on unsorted vectors, becoming a partial order after quotienting permutations or sorting. The uniform vector is majorized by every probability vector in this convention.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R1.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r2"></a>

#### R2. `Lor` — Lorenz curve

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ_n → C[0,1]

**Source definition.** Lor_p(t) := Σ_{i≤⌈nt⌉} p^↓_i, piecewise linear.

**Source property — not certified.** p ≺ q iff Lor_p lies below Lor_q.

**Source use — context only.** Inequality measurement (economics).

**Amendment (FORMULA_ERROR).** Use a genuinely linearly interpolated curve. The conventional nonnegative Gini formula 1-2*integral Lor uses an ascending cumulative Lorenz curve. For a descending curve the sign is reversed (with the chosen finite-population normalization).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R2.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r3"></a>

#### R3. `Gini` — Gini coefficient

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Δ → [0,1]

**Source definition.** Gini := 1 - 2 ∫_0^1 Lor(t) dt.

**Source property — not certified.** 0 = equal, 1 = maximum inequality.

**Source use — context only.** Income inequality.

**Amendment (FORMULA_ERROR).** Use a genuinely linearly interpolated curve. The conventional nonnegative Gini formula 1-2*integral Lor uses an ascending cumulative Lorenz curve. For a descending curve the sign is reversed (with the chosen finite-population normalization).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R3.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r4"></a>

#### R4. `E_F` — entanglement of formation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States on H_A ⊗ H_B → R_+

**Source definition.** E_F(ρ) := inf Σ p_i S(tr_B |ψ_i⟩⟨ψ_i|) over decompositions.

**Source property — not certified.** LOCC monotone; equals concurrence-based formula for two qubits.

**Source use — context only.** Entanglement quantification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R4.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r5"></a>

#### R5. `R_E` — relative entropy of resource

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ρ × free states F → R_+

**Source definition.** R_E(ρ) := inf_{σ ∈ F} D(ρ ‖ σ).

**Source property — not certified.** Resource monotone; vanishes iff ρ free.

**Source use — context only.** Faithful resource quantifier.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R5.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r6"></a>

#### R6. `Rob` — robustness measure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ρ × free states → R_+

**Source definition.** R(ρ) := inf{ s ≥ 0 : (ρ + sσ)/(1+s) ∈ F for some state σ }.

**Source property — not certified.** Convex; faithful; operational meaning via discrimination.

**Source use — context only.** Resource discrimination.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R6.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r7"></a>

#### R7. `D_max_R` — max-relative entropy of resource

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** ρ × F → R_+

**Source definition.** D_max(ρ ‖ F) := inf_{σ ∈ F} D_max(ρ ‖ σ).

**Source property — not certified.** Operationally tight for one-shot conversion.

**Source use — context only.** Single-shot resource manipulation.

**QPT-128 substitution.** Use only through [A25](#a25), with each contract and its four research questions.

**Eligibility question for R7.** Can the precise theorem yield the allocated trace-distance error including smoothing and seed exposure? Identify the exact role of this operator in that derivation.

<a id="op-r8"></a>

#### R8. `LOCC` — local operations + classical communication

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States on H_A ⊗ H_B → states (set of)

**Source definition.** Composition of local CPTP maps interspersed with classical signaling.

**Source property — not certified.** Cannot increase entanglement; closed under composition.

**Source use — context only.** Free operations of entanglement theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R8.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r9"></a>

#### R9. `Therm` — thermal operations

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States × thermal bath at β → states

**Source definition.** Free Gibbs state at β; energy-conserving unitaries on system + bath.

**Source property — not certified.** Cannot decrease F_β-entropy.

**Source use — context only.** Resource theory of thermodynamics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R9.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r10"></a>

#### R10. `Cov_op` — covariant operations

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Symmetry group G × G-representations → CPTP maps

**Source definition.** Λ satisfying Λ(U_g ρ U_g*) = V_g Λ(ρ) V_g*.

**Source property — not certified.** Free operations under asymmetry resource theory.

**Source use — context only.** Quantum reference frames.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R10.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r11"></a>

#### R11. `Cat_op` — catalytic operations

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ρ × → ρ → σ if ρ ⊗ c → σ ⊗ c

**Source definition.** Catalyst c assists; returned unchanged.

**Source property — not certified.** Strictly enlarges the set of reachable states.

**Source use — context only.** Catalytic resource manipulation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R11.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r12"></a>

#### R12. `Dist_op` — distillation rate

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** State × → R_+

**Source definition.** D(ρ) := sup_{maps} log_2 m / n where ρ^{⊗n} ↦ Φ^{⊗m} approximately.

**Source property — not certified.** Asymptotic conversion rate.

**Source use — context only.** Asymptotic resource extraction.

**Amendment (NORMALIZATION).** If the output is m Bell pairs Phi^(tensor m), the rate is m/n. Use log2(m)/n only when m denotes the dimension of a maximally entangled state.

**QPT-128 substitution.** Use only through [A21](#a21), with each contract and its four research questions.

**Eligibility question for R12.** Would changing the sponge parameters change the protocol and its implementation compatibility obligations? Identify the exact role of this operator in that derivation.

<a id="op-r13"></a>

#### R13. `Cost_op` — formation cost

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** State × → R_+

**Source definition.** C(ρ) := inf log_2 m / n where Φ^{⊗m} ↦ ρ^{⊗n} approximately.

**Source property — not certified.** Dual to distillation rate.

**Source use — context only.** Lower bound on creation resources.

**Amendment (NORMALIZATION).** If the output is m Bell pairs Phi^(tensor m), the rate is m/n. Use log2(m)/n only when m denotes the dimension of a maximally entangled state.

**QPT-128 substitution.** Use only through [A21](#a21), with each contract and its four research questions.

**Eligibility question for R13.** Does the chosen 720- or 832-bit challenge source actually have the ideal distribution required by the sampler lemma? Identify the exact role of this operator in that derivation.

<a id="op-r14"></a>

#### R14. `Concur` — concurrence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States on C² ⊗ C² → [0,1]

**Source definition.** C(ρ) := max(0, λ_1 - λ_2 - λ_3 - λ_4).

**Source property — not certified.** Wootters formula for two-qubit entanglement.

**Source use — context only.** Closed form for 2-qubit entanglement.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R14.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r15"></a>

#### R15. `Neg` — negativity

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Bipartite state → R_+

**Source definition.** N(ρ) := (‖ρ^{T_B}‖_1 - 1)/2.

**Source property — not certified.** Detects NPT entanglement; computable.

**Source use — context only.** Computable entanglement monotone.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R15.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r16"></a>

#### R16. `LogN` — logarithmic negativity

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Bipartite state → R_+

**Source definition.** E_N(ρ) := log_2 ‖ρ^{T_B}‖_1.

**Source property — not certified.** Additive; upper bound on distillable entanglement.

**Source use — context only.** Easy-to-compute entanglement bound.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R16.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r17"></a>

#### R17. `F_β_op` — free energy at β

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** State × Hamiltonian × β → R

**Source definition.** F_β(ρ) := E(ρ) - β^{-1} S(ρ).

**Source property — not certified.** Monotone under thermal operations.

**Source use — context only.** Equilibrium thermodynamics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R17.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r18"></a>

#### R18. `D_F_β` — free-energy drop

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** State pair × Hamiltonian × β → R_+

**Source definition.** ΔF := F_β(ρ) - F_β(σ).

**Source property — not certified.** Non-positive for monotone evolution under thermal ops.

**Source use — context only.** Thermodynamic work-extraction bound.

**Amendment (SIGN_ERROR).** With Delta F=F(initial)-F(final), nonincreasing free energy gives Delta F>=0, not <=0.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R18.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r19"></a>

#### R19. `Athermal` — athermality measure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** State × Hamiltonian × β → R_+

**Source definition.** A := D(ρ ‖ γ_β).

**Source property — not certified.** Free-state set = {γ_β}; relative entropy gives the canonical monotone.

**Source use — context only.** Out-of-equilibrium resource.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R19.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r20"></a>

#### R20. `Asym_op` — asymmetry monotone

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** State × G-action → R_+

**Source definition.** f(ρ) := D(ρ ‖ ⟨ρ⟩_G), ⟨·⟩_G group-twirl.

**Source property — not certified.** Captures non-invariance under G.

**Source use — context only.** Quantum reference frames.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R20.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r21"></a>

#### R21. `Twirl` — twirling operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** State × group G → state

**Source definition.** ⟨ρ⟩_G := ∫_G U_g ρ U_g* dμ(g).

**Source property — not certified.** Projection onto G-invariant states.

**Source use — context only.** Symmetrization in resource theories.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for R21.** Can both verifiers run before the one terminal database measurement in the intended security game? Identify the exact role of this operator in that derivation.

<a id="op-r22"></a>

#### R22. `Sup_act` — superactivation indicator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Resource × channel × → boolean

**Source definition.** Detects whether ρ ⊗ σ has resource even though neither does.

**Source property — not certified.** Implies non-convexity of free states.

**Source use — context only.** Quantum-channel zero-error coding.

**Amendment (UNSUPPORTED_INFERENCE).** Superactivation of channel capacities does not by itself imply nonconvexity of a chosen free-state set. Specify the resource, tensor closure and free operations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R22.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r23"></a>

#### R23. `Quan_op` — quantum capacity

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Channel N → R_+

**Source definition.** Q(N) := lim (1/n) max I_c(A; B)_{N^{⊗n}}.

**Source property — not certified.** Coherent information regularized.

**Source use — context only.** Quantum communication rate.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R23.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r24"></a>

#### R24. `I_c` — coherent information

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ρ × channel N → R

**Source definition.** I_c := S(N(ρ)) - S(N_c(ρ)) for complementary channel.

**Source property — not certified.** Lower bound on Q(N).

**Source use — context only.** Quantum channel capacity.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R24.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r25"></a>

#### R25. `Priv` — private capacity

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Channel × → R_+

**Source definition.** Largest rate of secure private communication.

**Source property — not certified.** Generally Q ≤ P; can be strict.

**Source use — context only.** Cryptographic information theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R25.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r26"></a>

#### R26. `HK_ent` — Hartley-Kolmogorov entropy

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Set → R_+

**Source definition.** H_0(X) := log |supp(X)|.

**Source property — not certified.** Rényi entropy at α = 0.

**Source use — context only.** Combinatorial counting bounds.

**QPT-128 substitution.** Use only through [A14](#a14), with each contract and its four research questions.

**Eligibility question for R26.** Does the operator improve conditional guessing probability or only a Shannon-entropy/visual statistic? Identify the exact role of this operator in that derivation.

<a id="op-r27"></a>

#### R27. `D_α^q` — quantum Rényi divergence (sandwiched)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** States² × α > 1/2 → R_+

**Source definition.** D̃_α(ρ ‖ σ) := (1/(α-1)) log tr(σ^{(1-α)/(2α)} ρ σ^{(1-α)/(2α)})^α.

**Source property — not certified.** Data-processing under CPTP for α ≥ 1/2.

**Source use — context only.** Quantum hypothesis testing.

**QPT-128 substitution.** Use only through [A20](#a20), [A25](#a25), with each contract and its four research questions.

**Eligibility question for R27.** Can a property-specific assumption and reduction cover the complete deployed hash interface and all its uses? Identify the exact role of this operator in that derivation.

<a id="op-r28"></a>

#### R28. `D_α^Petz` — Petz Rényi divergence

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** States² × α ∈ (0,1) ∪ (1, ∞) → R_+

**Source definition.** D_α^P(ρ ‖ σ) := (1/(α-1)) log tr(ρ^α σ^{1-α}).

**Source property — not certified.** Data-processing for α ∈ [0, 2].

**Source use — context only.** Different operational meanings vs sandwiched.

**QPT-128 substitution.** Use only through [A20](#a20), with each contract and its four research questions.

**Eligibility question for R28.** Do empirical output tests or a larger digest merely leave that computational premise untouched? Identify the exact role of this operator in that derivation.

<a id="op-r29"></a>

#### R29. `Q-Steer` — quantum steering operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Assemblage → R_+

**Source definition.** Quantifies LHS-violation; e.g. relative entropy of steering.

**Source property — not certified.** Resource monotone under one-way LOCC.

**Source use — context only.** Asymmetric nonlocality.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R29.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r30"></a>

#### R30. `Bell-Op` — Bell nonlocality operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Behavior → R_+

**Source definition.** Max violation over Bell inequalities (e.g. CHSH).

**Source property — not certified.** Local-deterministic models cannot reach quantum bound.

**Source use — context only.** Device-independent cryptography.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R30.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r31"></a>

#### R31. `Coh_l1` — ℓ_1 coherence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** State × basis → R_+

**Source definition.** C_{ℓ_1}(ρ) := Σ_{i ≠ j} |ρ_{ij}|.

**Source property — not certified.** Monotone under incoherent operations.

**Source use — context only.** Coherence as a resource.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R31.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r32"></a>

#### R32. `Coh_rel` — relative entropy of coherence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ρ × basis → R_+

**Source definition.** C_{rel}(ρ) := S(ρ_diag) - S(ρ).

**Source property — not certified.** Faithful; equal to distillable coherence.

**Source use — context only.** Quantification of superposition.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R32.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r33"></a>

#### R33. `Magic` — magic monotone

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** State × stabilizer set → R_+

**Source definition.** M(ρ) := min over stabilizer mixtures of distance to ρ; or stabilizer Rényi entropies.

**Source property — not certified.** Quantifies fault-tolerant universality.

**Source use — context only.** Quantum computational resource.

**QPT-128 substitution.** Use only through [A22](#a22), with each contract and its four research questions.

**Eligibility question for R33.** Is a polynomial-time extractor being called concretely efficient without evaluating its polynomial at the target budget? Identify the exact role of this operator in that derivation.

<a id="op-r34"></a>

#### R34. `Mana` — mana (magic-state mana)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Wigner function W_ρ → R_+

**Source definition.** M(ρ) := log Σ |W_ρ(x)|.

**Source property — not certified.** Sub-additive under stabilizer ops.

**Source use — context only.** Magic-state distillation cost lower bounds.

**QPT-128 substitution.** Use only through [A22](#a22), with each contract and its four research questions.

**Eligibility question for R34.** Do the downstream signature or hash hardness assumptions cover the inflated resource vector? Identify the exact role of this operator in that derivation.

<a id="op-r35"></a>

#### R35. `Robust_mag` — robustness of magic

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** State → R_+

**Source definition.** Inf s with (ρ + sσ)/(1+s) ∈ stab.

**Source property — not certified.** Convex; faithful magic monotone.

**Source use — context only.** Lower bounds on magic-state cost.

**QPT-128 substitution.** Use only through [A22](#a22), with each contract and its four research questions.

**Eligibility question for R35.** Are setup costs, cached advice or precomputation inside the target adversary budget? Identify the exact role of this operator in that derivation.

<a id="op-r36"></a>

#### R36. `Schmidt` — Schmidt rank

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Pure bipartite state → ℕ

**Source definition.** Schmidt rank: number of non-zero Schmidt coefficients.

**Source property — not certified.** LOCC-invariant; rank-r convertibility characterized via majorization.

**Source use — context only.** Pure-state entanglement classification.

**Amendment (FALSE_AS_STATED).** Schmidt rank is invariant under local unitaries but can decrease under LOCC. Resetting both parties locally converts a Bell state to a product state.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R36.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r37"></a>

#### R37. `Schmidt_n` — Schmidt number

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Mixed state × → ℕ

**Source definition.** Min over decompositions of max Schmidt rank.

**Source property — not certified.** Generalizes Schmidt rank to mixed states.

**Source use — context only.** Mixed-state entanglement dimension.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R37.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r38"></a>

#### R38. `OP_op` — open-system entropy production

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Trajectory under dynamics → R_+

**Source definition.** σ := ∫ J · X dt, with J fluxes, X thermodynamic forces.

**Source property — not certified.** Non-negative by second law; vanishes at equilibrium.

**Source use — context only.** Stochastic thermodynamics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R38.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r39"></a>

#### R39. `Jar` — Jarzynski identity

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Non-equilibrium work W × β → identity

**Source definition.** ⟨exp(-βW)⟩ = exp(-βΔF).

**Source property — not certified.** Exact identity even far from equilibrium.

**Source use — context only.** Free-energy estimation from non-equilibrium experiments.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R39.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r40"></a>

#### R40. `Cro` — Crooks fluctuation theorem

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Forward/reverse processes × → ratio

**Source definition.** P_F(W) / P_R(-W) = exp(β(W - ΔF)).

**Source property — not certified.** Detailed-balance origin of Jarzynski.

**Source use — context only.** Inferring ΔF from fluctuating work measurements.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R40.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r41"></a>

#### R41. `Conv_op` — convertibility operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** States × free ops F → boolean

**Source definition.** ρ ⟶_F σ iff ∃ Λ ∈ F with Λ(ρ) = σ.

**Source property — not certified.** Pre-order; equivalence ⇔ inter-convertibility.

**Source use — context only.** Resource ordering.

**QPT-128 substitution.** Use only through [A22](#a22), with each contract and its four research questions.

**Eligibility question for R41.** Is a polynomial-time extractor being called concretely efficient without evaluating its polynomial at the target budget? Identify the exact role of this operator in that derivation.

<a id="op-r42"></a>

#### R42. `Mono_op` — resource monotone

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Quantity f: states → R → → boolean

**Source definition.** Monotone: ρ ⟶ σ ⇒ f(ρ) ≥ f(σ).

**Source property — not certified.** Necessary conditions for conversion.

**Source use — context only.** Selecting valid monotones.

**QPT-128 substitution.** Use only through [A22](#a22), with each contract and its four research questions.

**Eligibility question for R42.** Do the downstream signature or hash hardness assumptions cover the inflated resource vector? Identify the exact role of this operator in that derivation.

<a id="op-r43"></a>

#### R43. `Conv_asym` — asymptotic conversion rate

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States × F → R_+

**Source definition.** Sup_R lim approximate convertibility of ρ^{⊗n} to σ^{⊗⌊Rn⌋}.

**Source property — not certified.** Often distillation/formation difference.

**Source use — context only.** Asymptotic resource theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R43.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r44"></a>

#### R44. `Reverse_op` — reversibility indicator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States × F → boolean

**Source definition.** Resource theory reversible iff D_∞ = C_∞ for all states.

**Source property — not certified.** Holds for bipartite pure-state entanglement, not in general.

**Source use — context only.** Foundational resource-theory question.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R44.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r45"></a>

#### R45. `Single_shot` — single-shot conversion

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States × ε → boolean

**Source definition.** Existence of Λ ∈ F with Λ(ρ) ε-close to σ.

**Source property — not certified.** Characterized by smooth max-divergence.

**Source use — context only.** Practical resource manipulation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R45.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r46"></a>

#### R46. `LOCC_PPT` — PPT-LOCC closure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Bipartite states → set

**Source definition.** Free states extended to PPT (positive partial transpose).

**Source property — not certified.** Strictly larger than LOCC; tractable bounds.

**Source use — context only.** Tractable bounds on entanglement measures.

**Amendment (TYPE_GAP).** PPT states and LOCC channels are different types. PPT-preserving channels are a relaxation of LOCC; the set of PPT states is not a set of operations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R46.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r47"></a>

#### R47. `Distill_PPT` — distillation under PPT

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Bipartite states → R_+

**Source definition.** Distillation rate under PPT-preserving operations.

**Source property — not certified.** Bounded by log-negativity.

**Source use — context only.** Computable upper bounds.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R47.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r48"></a>

#### R48. `Q_Ham` — quantum Hamming bound

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Code parameters → R_+

**Source definition.** Quantum sphere-packing bound for entanglement-assisted codes.

**Source property — not certified.** Necessary condition on code existence.

**Source use — context only.** Quantum error correction.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R48.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r49"></a>

#### R49. `Multipart_E` — multipartite entanglement

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States on H_1 ⊗ ... ⊗ H_n → R_+

**Source definition.** GME measures: e.g., genuine multipartite negativity.

**Source property — not certified.** Hierarchy of n-way entanglements.

**Source use — context only.** Network quantum resources.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R49.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

<a id="op-r50"></a>

#### R50. `Coh_LOCC` — coherence-LOCC bridge

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Coherent states ↔ entangled states

**Source definition.** Operator-level isomorphism between coherence theory and resource theory of speakable asymmetry.

**Source property — not certified.** Maps incoherent ops to (one-way) LOCC.

**Source use — context only.** Resource interconvertibility.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for R50.** Is the free-operation class used by this resource operator the actual adversary class, and does the monotone bound the stated success or cost quantity?

### Family O: Logic and verification

<a id="op-o1"></a>

#### O1. `□` — necessity (modal)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Formulas × Kripke model → boolean

**Source definition.** M, w ⊨ □φ iff M, v ⊨ φ for all v with wRv.

**Source property — not certified.** Normal modal logic K: □(φ → ψ) → (□φ → □ψ).

**Source use — context only.** Knowledge, obligation, time.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O1.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o2"></a>

#### O2. `◇` — possibility (modal)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Formulas × Kripke → boolean

**Source definition.** M, w ⊨ ◇φ iff ∃v with wRv and M, v ⊨ φ.

**Source property — not certified.** Dual of □: ◇φ ↔ ¬□¬φ.

**Source use — context only.** Future possibilities, alternatives.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O2.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o3"></a>

#### O3. `μX.φ` — least fixed-point (modal μ-calculus)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Formula in X positive × → formula

**Source definition.** μX.φ(X) := smallest set satisfying X ↔ φ(X).

**Source property — not certified.** Defines inductive predicates.

**Source use — context only.** Reachability in temporal logic.

**QPT-128 substitution.** Use only through [A01](#a01), with each contract and its four research questions.

**Eligibility question for O3.** Does a proposed improvement reduce an actual summand, or merely rename the threshold? Identify the exact role of this operator in that derivation.

<a id="op-o4"></a>

#### O4. `νX.φ` — greatest fixed-point (modal μ-calculus)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → ×

**Source definition.** νX.φ(X) := largest set with X ↔ φ(X).

**Source property — not certified.** Coinductive definitions; safety properties.

**Source use — context only.** Bisimulation, invariance.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O4.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o5"></a>

#### O5. `⊃_int` — intuitionistic implication

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Heyting algebra² → ×

**Source definition.** a ⊃ b := sup{ x : a ∧ x ≤ b }.

**Source property — not certified.** Right adjoint to ∧; differs from classical → in intuitionistic settings.

**Source use — context only.** Constructive proofs in Coq/Agda.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O5.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o6"></a>

#### O6. `BSim` — bisimulation relation

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Two LTS → relation

**Source definition.** R is a bisimulation iff (s, t) ∈ R, s →^a s' ⇒ ∃t' (t →^a t', (s', t') ∈ R), and vice versa.

**Source property — not certified.** Largest such R is bisimilarity (greatest fixed point).

**Source use — context only.** Process equivalence in concurrency.

**QPT-128 substitution.** Use only through [A18](#a18), with each contract and its four research questions.

**Eligibility question for O6.** Are the two roots, public statements and witness encodings uniquely tied to the same roster and epoch? Identify the exact role of this operator in that derivation.

<a id="op-o7"></a>

#### O7. `MC` — model checking operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Kripke structure × formula → boolean

**Source definition.** MC(M, φ) := M ⊨ φ.

**Source property — not certified.** Decidable for LTL, CTL, μ-calculus on finite models.

**Source use — context only.** Verification of finite-state systems.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O7.** Does a negative mutation such as swapping a sign, deleting a domain tag or replacing missing data by zero get rejected? Identify the exact role of this operator in that derivation.

<a id="op-o8"></a>

#### O8. `K_a_trans` — Kripke transition

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Worlds × accessibility → set of worlds

**Source definition.** K_a(w) := { v : wR_av }.

**Source property — not certified.** Encodes agent a's epistemic possibilities.

**Source use — context only.** Multi-agent epistemic logic.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O8.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o9"></a>

#### O9. `⊗_lin` — linear-logic 'times' (multiplicative conjunction)

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Formulas × → formula

**Source definition.** Γ ⊢ A, Δ ⊗ Σ ⊢ B, Θ ⇒ Γ, Σ ⊢ A ⊗ B, Δ, Θ.

**Source property — not certified.** Resource-sensitive; no contraction or weakening.

**Source use — context only.** Resource management in proofs.

**Amendment (FORMULA_GAP).** Use a fixed single-sided or two-sided sequent convention. For intuitionistic tensor, Gamma|-A and Delta|-B imply Gamma,Delta|-A tensor B; a context is not itself a tensor connective as in the source.

**QPT-128 substitution.** Use only through [A10](#a10), [A22](#a22), with each contract and its four research questions.

**Eligibility question for O9.** Can both verifiers run before the one terminal database measurement in the intended security game? Identify the exact role of this operator in that derivation.

<a id="op-o10"></a>

#### O10. `⅋` — linear-logic 'par' (multiplicative disjunction)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Formulas × → formula

**Source definition.** Dual of ⊗ under negation.

**Source property — not certified.** Sequent: Γ, A, B ⊢ Δ ⇒ Γ, A ⅋ B ⊢ Δ.

**Source use — context only.** Parallel composition in proof nets.

**Amendment (FORMULA_GAP).** Use a fixed single-sided or two-sided sequent convention. For intuitionistic tensor, Gamma|-A and Delta|-B imply Gamma,Delta|-A tensor B; a context is not itself a tensor connective as in the source.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O10.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o11"></a>

#### O11. `!` — linear-logic exponential (of course)

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Formula → formula

**Source definition.** Allows contraction and weakening on !A.

**Source property — not certified.** Comonad: !!A → !A, !A → A.

**Source use — context only.** Reusable resources.

**Amendment (DIRECTION_ERROR).** For the comonad structure use dereliction !A->A and comultiplication !A->!!A. A possible !!A->!A map is not the comultiplication.

**QPT-128 substitution.** Use only through [A10](#a10), with each contract and its four research questions.

**Eligibility question for O11.** Where would an earlier measurement change the probability of the second verification? Identify the exact role of this operator in that derivation.

<a id="op-o12"></a>

#### O12. `?` — linear-logic exponential (why not)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Formula → formula

**Source definition.** Dual of ! under linear negation.

**Source property — not certified.** Allows dual structural rules.

**Source use — context only.** Co-reusable resources.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O12.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o13"></a>

#### O13. `Quot` — quotient operator (logic)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Formulas × equivalence → formulas

**Source definition.** Q(φ; ~) := φ where ~ identifies syntactic equivalence.

**Source property — not certified.** Normal forms; canonical representatives.

**Source use — context only.** Theorem proving.

**QPT-128 substitution.** Use only through [A12](#a12), [A19](#a19), [A28](#a28), with each contract and its four research questions.

**Eligibility question for O13.** Is the hash input unambiguously bound to protocol version, roster, epoch, message and commitment? Identify the exact role of this operator in that derivation.

<a id="op-o14"></a>

#### O14. `Sk` — Skolemization

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** FO formula → ∃-free formula in expanded signature

**Source definition.** ∀x ∃y P(x, y) ↝ ∀x P(x, f(x)) with new Skolem function f.

**Source property — not certified.** Preserves satisfiability, not validity.

**Source use — context only.** First-order theorem proving.

**QPT-128 substitution.** Use only through [A17](#a17), with each contract and its four research questions.

**Eligibility question for O14.** Is that hardness bound valid at the transformed time, query and memory costs of B? Identify the exact role of this operator in that derivation.

<a id="op-o15"></a>

#### O15. `Her` — Herbrandization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** FO formula → ground theory

**Source definition.** Dual to Skolemization: ∃x ∀y P(x, y) ↝ ∃x P(x, f(x)).

**Source property — not certified.** Preserves validity.

**Source use — context only.** Herbrand's theorem.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O15.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o16"></a>

#### O16. `Res` — resolution operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Pair of clauses → resolvent clause

**Source definition.** {A, C}, {¬A, D} ⇒ {C, D}.

**Source property — not certified.** Sound and refutation-complete for propositional logic.

**Source use — context only.** SAT solvers.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O16.** Can each claimed closure be traced to a written lemma or an external theorem whose hypotheses are satisfied? Identify the exact role of this operator in that derivation.

<a id="op-o17"></a>

#### O17. `CDCL` — conflict-driven clause learning

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** SAT instance × → assignment or UNSAT proof

**Source definition.** Backjumps and learns clauses from analyzed conflicts.

**Source property — not certified.** Industrial-strength SAT.

**Source use — context only.** Hardware/software verification.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O17.** Which quantified domain was exhausted, and which parameters remain symbolic? Identify the exact role of this operator in that derivation.

<a id="op-o18"></a>

#### O18. `DPLL` — Davis-Putnam-Logemann-Loveland

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** SAT instance → assignment or UNSAT

**Source definition.** Recursive DFS with unit propagation and pure literal elimination.

**Source property — not certified.** Complete decision procedure.

**Source use — context only.** Classical SAT solving.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O18.** Can independent brute force check a closed-form counter without reusing its recurrence? Identify the exact role of this operator in that derivation.

<a id="op-o19"></a>

#### O19. `SMT` — satisfiability modulo theories

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** QF formula in theory T → SAT/UNSAT

**Source definition.** Combines SAT with theory solvers (LRA, EUF, BV, etc.).

**Source property — not certified.** DPLL(T) framework.

**Source use — context only.** Software verification.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O19.** Does a negative mutation such as swapping a sign, deleting a domain tag or replacing missing data by zero get rejected? Identify the exact role of this operator in that derivation.

<a id="op-o20"></a>

#### O20. `Cont_op` — continuation-passing operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** λ-term → CPS form

**Source definition.** M ↝ λk. ...; transformation makes control explicit.

**Source property — not certified.** Preserves operational semantics.

**Source use — context only.** Compiler intermediate languages.

**QPT-128 substitution.** Use only through [A18](#a18), with each contract and its four research questions.

**Eligibility question for O20.** Does the proof apply to the current verifier, or only to a proposed commit-and-open replacement? Identify the exact role of this operator in that derivation.

<a id="op-o21"></a>

#### O21. `γ` — Gödel-Gentzen translation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Classical formulas → intuitionistic formulas

**Source definition.** Inserts double negations to make classical theorems intuitionistically valid.

**Source property — not certified.** Embeds classical logic into intuitionistic.

**Source use — context only.** Constructive interpretations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O21.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o22"></a>

#### O22. `Forc` — forcing relation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Poset × condition × formula → boolean

**Source definition.** p ⊩ φ for forcing condition p.

**Source property — not certified.** Cohen's technique for independence proofs.

**Source use — context only.** Independence of CH from ZFC.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O22.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o23"></a>

#### O23. `Ult` — ultrapower construction

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Structure × ultrafilter → elementary extension

**Source definition.** M^I / U is an elementary extension if U non-principal.

**Source property — not certified.** Łoś's theorem on first-order satisfaction.

**Source use — context only.** Non-standard analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O23.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o24"></a>

#### O24. `Comp_op` — compactness operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** FO theory → boolean

**Source definition.** T satisfiable iff every finite subtheory is.

**Source property — not certified.** Equivalent to Łoś's theorem for ultrafilter limits.

**Source use — context only.** Model-theoretic constructions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O24.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o25"></a>

#### O25. `Down_LS` — downward Löwenheim-Skolem

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Infinite structure × cardinal → elementary substructure

**Source definition.** M has elementary substructure of any infinite cardinality |M| ≥ κ ≥ |L|.

**Source property — not certified.** Skolem paradox.

**Source use — context only.** Foundations of set theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O25.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o26"></a>

#### O26. `Up_LS` — upward Löwenheim-Skolem

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Infinite structure × cardinal → elementary extension

**Source definition.** M has elementary extension of any cardinality κ ≥ |M|.

**Source property — not certified.** Infinite structures aren't categorical.

**Source use — context only.** Limits of first-order definability.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O26.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o27"></a>

#### O27. `Elim_Quant` — quantifier elimination

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Theory × formula → quantifier-free formula

**Source definition.** Theory admits QE iff every formula equivalent to a quantifier-free one.

**Source property — not certified.** Decidability of theory (with effective QE).

**Source use — context only.** Algebraic decision procedures.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O27.** Does a negative mutation such as swapping a sign, deleting a domain tag or replacing missing data by zero get rejected? Identify the exact role of this operator in that derivation.

<a id="op-o28"></a>

#### O28. `Pres` — Presburger decision procedure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Formula in (Z, +, <, 0, 1) → boolean

**Source definition.** Theory of Z with + and <; admits QE in extended language.

**Source property — not certified.** Decidable; super-exponential complexity (Fischer-Rabin).

**Source use — context only.** Integer linear arithmetic.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O28.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o29"></a>

#### O29. `Tar` — Tarski quantifier elimination

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Formula in (R, +, ·, <) → boolean

**Source definition.** Real closed fields admit QE.

**Source property — not certified.** Decidable; doubly-exponential lower bound.

**Source use — context only.** Real algebraic geometry.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O29.** Which quantified domain was exhausted, and which parameters remain symbolic? Identify the exact role of this operator in that derivation.

<a id="op-o30"></a>

#### O30. `AC_op` — axiom-of-choice equivalents

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Statement × ZF → equivalent to AC?

**Source definition.** AC ↔ Zorn's lemma ↔ well-ordering principle.

**Source property — not certified.** Each independent of ZF; equivalent in ZF.

**Source use — context only.** Set-theoretic foundations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O30.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o31"></a>

#### O31. `⊨_lin` — linear-temporal-logic satisfaction

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Trace × LTL formula → boolean

**Source definition.** π ⊨ X φ iff π[1..] ⊨ φ; π ⊨ φ U ψ iff ∃i with π[i..] ⊨ ψ and π[j..] ⊨ φ for j < i.

**Source property — not certified.** PSPACE-complete model checking.

**Source use — context only.** Reactive-system specification.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for O31.** Which public evidence proves that a common signer actually signed both statements? Identify the exact role of this operator in that derivation.

<a id="op-o32"></a>

#### O32. `⊨_CTL` — computation-tree-logic satisfaction

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Kripke × CTL formula → boolean

**Source definition.** Branching-time temporal logic with path quantifiers A, E and temporal X, F, G, U.

**Source property — not certified.** Polynomial-time model checking.

**Source use — context only.** Verification of finite-state systems.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for O32.** Does a quorum intersection proof get incorrectly treated as proof that shares were collected through a secure distributed protocol? Identify the exact role of this operator in that derivation.

<a id="op-o33"></a>

#### O33. `AF` — always-eventually operator (CTL)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States × → boolean

**Source definition.** AF φ := on every path eventually φ.

**Source property — not certified.** Liveness property.

**Source use — context only.** Termination, response specifications.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O33.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o34"></a>

#### O34. `EG` — exists-globally operator (CTL)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** States × → boolean

**Source definition.** EG φ := exists a path where φ holds globally.

**Source property — not certified.** Safety along some computation.

**Source use — context only.** Possible deadlock free path.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O34.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o35"></a>

#### O35. `Φ_BV` — Belief revision operator (Bayesian/AGM)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Belief state × evidence → updated belief

**Source definition.** AGM postulates determine consistent revision up to choice.

**Source property — not certified.** Includes contraction, expansion, revision.

**Source use — context only.** Logical theory of belief change.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O35.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o36"></a>

#### O36. `De_Lop` — Default-logic operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Default rules × → extension

**Source definition.** Reiter extensions = fixed points of operator on Th(W ∪ defaults).

**Source property — not certified.** Non-monotonic; may have 0, 1, or multiple extensions.

**Source use — context only.** Non-monotonic reasoning.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O36.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o37"></a>

#### O37. `Circ` — circumscription operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** FO theory × minimization → extended theory

**Source definition.** McCarthy's: minimizes extension of predicate P.

**Source property — not certified.** Captures the closed-world assumption.

**Source use — context only.** Common-sense reasoning.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O37.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o38"></a>

#### O38. `Prop_op` — propositional Horn-SAT

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Horn formula → satisfying assignment

**Source definition.** Solvable in linear time via forward chaining.

**Source property — not certified.** Polynomial-time.

**Source use — context only.** Datalog and rule-based systems.

**QPT-128 substitution.** Use only through [A23](#a23), [A28](#a28), with each contract and its four research questions.

**Eligibility question for O38.** Can independent brute force check a closed-form counter without reusing its recurrence? Identify the exact role of this operator in that derivation.

<a id="op-o39"></a>

#### O39. `Datalog` — Datalog evaluation

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Rules × facts → derived facts

**Source definition.** Bottom-up: fixed point of T_P.

**Source property — not certified.** Polynomial-time evaluation; PSPACE expressive power for first-order.

**Source use — context only.** Database query languages.

**Amendment (COMPLEXITY_GAP).** Separate data complexity (polynomial for fixed ordinary Datalog programs) from combined complexity (EXPTIME-complete in general). Do not infer the source PSPACE claim.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O39.** Does a negative mutation such as swapping a sign, deleting a domain tag or replacing missing data by zero get rejected? Identify the exact role of this operator in that derivation.

<a id="op-o40"></a>

#### O40. `Ind_op` — induction operator (PA)

**Disposition.** ACTIVE INVESTIGATION; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Formula φ(x) × → ∀x φ(x)?

**Source definition.** From φ(0) and ∀x (φ(x) → φ(x+1)).

**Source property — not certified.** Equivalent to well-ordering of ω.

**Source use — context only.** Mathematical induction.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O40.** Can each claimed closure be traced to a written lemma or an external theorem whose hypotheses are satisfied? Identify the exact role of this operator in that derivation.

<a id="op-o41"></a>

#### O41. `Cur_How` — Curry-Howard isomorphism

**Disposition.** ACTIVE INVESTIGATION; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Type × proof → ×

**Source definition.** Type ↔ proposition; term ↔ proof; reduction ↔ proof normalization.

**Source property — not certified.** Bijection between intuitionistic logic and typed λ-calculus.

**Source use — context only.** Proofs-as-programs paradigm.

**QPT-128 substitution.** Use only through [A17](#a17), [A23](#a23), [A28](#a28), with each contract and its four research questions.

**Eligibility question for O41.** What exact hardness assumption bounds the remaining NMA adversary for the fixed ML-DSA parameter set? Identify the exact role of this operator in that derivation.

<a id="op-o42"></a>

#### O42. `Norm_op` — proof-normalization operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Proof term × β/η-rules → normal form

**Source definition.** Strong normalization for typed λ-calculus.

**Source property — not certified.** Cut elimination at the proof level.

**Source use — context only.** Decidability of type checking.

**QPT-128 substitution.** Use only through [A23](#a23), with each contract and its four research questions.

**Eligibility question for O42.** Can independent brute force check a closed-form counter without reusing its recurrence? Identify the exact role of this operator in that derivation.

<a id="op-o43"></a>

#### O43. `Cut` — cut elimination

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sequent calculus proof → cut-free proof

**Source definition.** Eliminates the cut rule via Gentzen's procedure.

**Source property — not certified.** Implies consistency.

**Source use — context only.** Foundational completeness results.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O43.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o44"></a>

#### O44. `MA` — Modal algebra operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Boolean algebra with operator □ → ×

**Source definition.** Modal algebra is a BAO satisfying K-axioms.

**Source property — not certified.** Dual to descriptive frames (Jónsson-Tarski).

**Source use — context only.** Algebraic semantics of modal logic.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O44.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o45"></a>

#### O45. `Top_op` — Topological semantics of modal logic

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Topological space × → S4-model

**Source definition.** □φ := interior of φ.

**Source property — not certified.** S4-completeness (McKinsey-Tarski).

**Source use — context only.** Spatial interpretation of necessity.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O45.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o46"></a>

#### O46. `DRT` — dynamic-predicate-logic operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Discourse representation structure × update → ×

**Source definition.** DRT updates introduce discourse referents and conditions.

**Source property — not certified.** Capable of donkey-anaphora resolution.

**Source use — context only.** Natural-language semantics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O46.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o47"></a>

#### O47. `LP_op` — linear-programming relaxation in logic

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** MaxSAT instance × → LP

**Source definition.** Relaxes Boolean variables to [0,1].

**Source property — not certified.** Provides upper bounds; rounding gives approximations.

**Source use — context only.** Approximate logic optimization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O47.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o48"></a>

#### O48. `Co_alg` — coalgebra operator (modal logic)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Endofunctor F × → category of F-coalgebras

**Source definition.** Each coalgebra X → F(X) gives a transition structure.

**Source property — not certified.** Final coalgebra: behavioural equivalence quotient.

**Source use — context only.** Categorical semantics for processes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O48.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o49"></a>

#### O49. `Sub_log` — substructural-logic operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Sequent calculus × removed structural rule → logic

**Source definition.** Drop contraction → linear, drop weakening → relevance, drop both → strict.

**Source property — not certified.** Lattice of substructural logics.

**Source use — context only.** Resource and relevance reasoning.

**Amendment (DEFINITION_MISMATCH).** Linear logic removes unrestricted weakening and contraction; affine logic restores weakening and relevant variants restore contraction. Dropping contraction alone is not the complete definition of linear logic.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O49.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

<a id="op-o50"></a>

#### O50. `HoTT_id` — homotopy-type-theory identity type

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Two terms × → type

**Source definition.** Id_A(a, b) carrying paths between a and b.

**Source property — not certified.** Univalence: identity types model homotopy paths.

**Source use — context only.** Foundations via homotopy theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for O50.** Can this logical operator produce a checkable statement about the exact typed relation and quantifiers, rather than merely label a missing premise?

### Family W: Multiscale transforms

<a id="op-w1"></a>

#### W1. `CWT` — continuous wavelet transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L²(R) × wavelet ψ → L²(R_+* × R)

**Source definition.** (W f)(a, b) := (1/√a) ∫ f(t) ψ̄((t-b)/a) dt.

**Source property — not certified.** Isometry under admissibility condition C_ψ < ∞.

**Source use — context only.** Time-frequency analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W1.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w2"></a>

#### W2. `DWT` — discrete wavelet transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L²(R) × MRA → ℓ²(Z²)

**Source definition.** c_{j,k} := ⟨f, ψ_{j,k}⟩ with ψ_{j,k}(x) := 2^{j/2} ψ(2^j x - k).

**Source property — not certified.** Orthogonal basis when ψ generates an MRA.

**Source use — context only.** Image compression (JPEG2000).

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W2.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w3"></a>

#### W3. `φ_scale` — scaling function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** MRA → φ ∈ L²(R)

**Source definition.** Satisfies refinement: φ(x) = √2 Σ h_k φ(2x - k).

**Source property — not certified.** Generates V_0 = closure of span{φ(· - k)}.

**Source use — context only.** Building blocks of multiresolution analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W3.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w4"></a>

#### W4. `ψ_mother` — mother wavelet

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** MRA → ψ

**Source definition.** ψ(x) := √2 Σ g_k φ(2x - k) with g_k := (-1)^k h_{1-k}.

**Source property — not certified.** Together with shifts and dilates forms orthonormal basis of L²(R).

**Source use — context only.** Basis for orthogonal wavelet decompositions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W4.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w5"></a>

#### W5. `MRA` — multiresolution analysis

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** L²(R) → nested closed subspaces {V_j}

**Source definition.** V_j ⊂ V_{j+1}, ⋂V_j = 0, ⋃V_j = L²(R), f(x) ∈ V_j ⇔ f(2x) ∈ V_{j+1}.

**Source property — not certified.** Equivalent to a scaling function φ.

**Source use — context only.** Architecture of wavelet bases.

**Amendment (TOPOLOGY_GAP).** The union of the MRA subspaces is dense in L2; it need not literally equal L2. State closure of the union.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W5.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w6"></a>

#### W6. `FWT` — fast wavelet transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L²(R) × O(n) → coefficients

**Source definition.** Mallat pyramid algorithm using h, g filters.

**Source property — not certified.** O(n) time complexity.

**Source use — context only.** Computational signal processing.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W6.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w7"></a>

#### W7. `Daub_N` — Daubechies wavelet

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** ℕ → orthonormal wavelet

**Source definition.** Compactly supported orthogonal wavelets with N vanishing moments.

**Source property — not certified.** Support of width 2N - 1; smoothness grows with N.

**Source use — context only.** Smoothness-vs-compactness trade-off.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W7.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w8"></a>

#### W8. `Ridge` — ridge transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** L²(R^d) × line → ×

**Source definition.** R f(θ, t) := ∫ f(x) δ(t - x · θ) dx.

**Source property — not certified.** Inversion via Radon-derivative.

**Source use — context only.** Wavelet-based image features.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W8.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w9"></a>

#### W9. `ScaleSp` — scale-space operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** L²(R^d) × t > 0 → L²(R^d)

**Source definition.** f_t := f * G_t (Gaussian convolution).

**Source property — not certified.** Satisfies heat equation ∂_t f = (1/2) Δ f.

**Source use — context only.** Computer-vision feature detection.

**QPT-128 substitution.** Use only through [A27](#a27), with each contract and its four research questions.

**Eligibility question for W9.** What finite-dimensional state and actual protocol step correspond to the proposed differential operator? Identify the exact role of this operator in that derivation.

<a id="op-w10"></a>

#### W10. `RG_flow` — renormalization-group flow

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Couplings × scale → couplings

**Source definition.** g(μ) evolves via Callan-Symanzik / Wilson equations: μ dg/dμ = β(g).

**Source property — not certified.** Fixed points classify universality classes.

**Source use — context only.** Phase transitions, asymptotic freedom.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W10.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w11"></a>

#### W11. `β` — RG beta function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Coupling → derivative

**Source definition.** β(g) := μ dg/dμ.

**Source property — not certified.** Zero at fixed points; sign determines (a)symptotic freedom.

**Source use — context only.** Running couplings.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W11.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w12"></a>

#### W12. `Kad` — Kadanoff block-spin

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Lattice spin × block size → coarser lattice

**Source definition.** S'_I := f({S_i}_{i ∈ I}); rescale.

**Source property — not certified.** Iteration generates the RG flow.

**Source use — context only.** Block-spin RG.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W12.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w13"></a>

#### W13. `Wil-Kog` — Wilson-Kogut RG

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Effective action × scale Λ → effective action at lower Λ

**Source definition.** Integrate out high-momentum modes; rescale fields and couplings.

**Source property — not certified.** Defines Wilson effective theory.

**Source use — context only.** Field-theoretic RG.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W13.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w14"></a>

#### W14. `LSM` — level-set method operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Φ: R^n × R_+ → R × velocity v → evolution

**Source definition.** Φ_t + v |∇Φ| = 0.

**Source property — not certified.** Front {Φ = 0} captures interface; topology changes naturally.

**Source use — context only.** Multi-phase flow simulation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W14.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w15"></a>

#### W15. `Wave_sym` — symmetric wavelet

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → biorthogonal wavelet pair

**Source definition.** Two functions ψ, ψ̃ with biorthogonality.

**Source property — not certified.** Sacrifices orthogonality for symmetry.

**Source use — context only.** Image processing with linear-phase filters.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W15.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w16"></a>

#### W16. `CDF` — Cohen-Daubechies-Feauveau wavelet

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → biorthogonal pair

**Source definition.** Built from cardinal B-splines.

**Source property — not certified.** Used in JPEG2000.

**Source use — context only.** Image compression standards.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W16.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w17"></a>

#### W17. `Coif` — Coiflet

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × → orthonormal wavelet

**Source definition.** Daubechies-type wavelet with both scaling and wavelet function having vanishing moments.

**Source property — not certified.** Useful for numerical-analysis problems requiring vanishing moments.

**Source use — context only.** Numerical PDE methods.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W17.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w18"></a>

#### W18. `Lift_sch` — lifting scheme

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Discrete signal × filter steps → wavelet coefficients

**Source definition.** Alternates prediction (P) and update (U) steps.

**Source property — not certified.** Reversible in integer arithmetic.

**Source use — context only.** Wavelet-based lossless compression.

**QPT-128 substitution.** Use only through [A14](#a14), with each contract and its four research questions.

**Eligibility question for W18.** Does the operator improve conditional guessing probability or only a Shannon-entropy/visual statistic? Identify the exact role of this operator in that derivation.

<a id="op-w19"></a>

#### W19. `Frame_op` — wavelet frame operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** L² × family {ψ_λ} → L²

**Source definition.** T_F f := Σ ⟨f, ψ_λ⟩ ψ_λ.

**Source property — not certified.** Bounded with bounded inverse iff frame bounds 0 < A ≤ B.

**Source use — context only.** Redundant signal representations.

**QPT-128 substitution.** Use only through [A07](#a07), with each contract and its four research questions.

**Eligibility question for W19.** What is the minimum repetition count at 32, 64, 92 and 128 under this weaker contraction? Identify the exact role of this operator in that derivation.

<a id="op-w20"></a>

#### W20. `Curve` — curvelet transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** L²(R²) × → ×

**Source definition.** Anisotropic scaling: scale 2^{-j} × 2^{-j/2}, plus orientation.

**Source property — not certified.** Optimal nonlinear approximation rate for C² functions with C² edges.

**Source use — context only.** Image processing with edges.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W20.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w21"></a>

#### W21. `Shear` — shearlet transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** L²(R²) × → ×

**Source definition.** Shear matrix in place of rotation; admits filter-bank algorithms.

**Source property — not certified.** Same optimality as curvelets; more easily implementable.

**Source use — context only.** Edge detection.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W21.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w22"></a>

#### W22. `Gabor` — Gabor frame

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** L²(R) × (a, b) → ×

**Source definition.** g_{m,n}(x) := e^{2πi mb x} g(x - na).

**Source property — not certified.** Frame iff (a, b) in admissibility region (Heisenberg uncertainty).

**Source use — context only.** Time-frequency analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W22.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w23"></a>

#### W23. `STFT` — short-time Fourier transform

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** L²(R) × window g → ×

**Source definition.** STFT f(t, ξ) := ∫ f(s) g(s - t) e^{-2πi ξ s} ds.

**Source property — not certified.** Continuous version of Gabor.

**Source use — context only.** Spectrograms.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W23.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w24"></a>

#### W24. `Heis` — Heisenberg uncertainty operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L²(R) × → R_+

**Source definition.** Δx · Δp ≥ 1/2.

**Source property — not certified.** Equality iff f is a Gaussian.

**Source use — context only.** Lower bound on time-frequency localization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W24.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w25"></a>

#### W25. `Wigner` — Wigner distribution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L²(R)² → R

**Source definition.** W_f(x, ξ) := ∫ f(x + s/2) f̄(x - s/2) e^{-2πi sξ} ds.

**Source property — not certified.** Real-valued; marginals give |f|² and |f̂|²; can be negative.

**Source use — context only.** Time-frequency analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W25.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w26"></a>

#### W26. `Wignerρ` — Wigner function of density operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Density operator → R

**Source definition.** W_ρ(x, p) := (1/π) ∫ ⟨x - y| ρ |x + y⟩ e^{2ipy} dy.

**Source property — not certified.** Quasi-probability; integrates to 1.

**Source use — context only.** Phase-space quantum mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W26.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w27"></a>

#### W27. `Bezier_sub` — Bézier subdivision

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Control polygon × t ∈ [0,1] → refined polygon

**Source definition.** De Casteljau algorithm.

**Source property — not certified.** Converges to Bézier curve at rate O(2^{-n}).

**Source use — context only.** Computer-aided design.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W27.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w28"></a>

#### W28. `Loop_sub` — Loop subdivision

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Triangle mesh × → refined mesh

**Source definition.** Adds vertices on edges via weighted averages.

**Source property — not certified.** Limit surface is C² except at extraordinary vertices.

**Source use — context only.** Computer graphics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W28.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w29"></a>

#### W29. `Catm` — Catmull-Clark subdivision

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Quad mesh × → refined mesh

**Source definition.** Generalizes B-spline subdivision to arbitrary topology.

**Source property — not certified.** Limit C² almost everywhere.

**Source use — context only.** Animated movie geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W29.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w30"></a>

#### W30. `Box-Spl` — box spline

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Direction set X ⊂ Z^n → function

**Source definition.** B_X(x) := convolution of indicators of unit segments in directions of X.

**Source property — not certified.** Reproduces polynomials of certain degree.

**Source use — context only.** Multivariate approximation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W30.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w31"></a>

#### W31. `Wave_pkt` — wavelet packet

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** L² × subband tree → orthonormal basis

**Source definition.** Recursive subband decomposition explored on tree.

**Source property — not certified.** Best-basis selection via entropy minimization.

**Source use — context only.** Adaptive signal compression.

**QPT-128 substitution.** Use only through [A21](#a21), with each contract and its four research questions.

**Eligibility question for W31.** If a published bound becomes uninformative, is that being reported as a proof gap rather than an attack? Identify the exact role of this operator in that derivation.

<a id="op-w32"></a>

#### W32. `Best-Basis` — best-basis algorithm

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Wavelet-packet tree × cost → optimal basis

**Source definition.** Dynamic programming on tree.

**Source property — not certified.** Polynomial time.

**Source use — context only.** Adaptive transform coding.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W32.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w33"></a>

#### W33. `MULT-VS` — multivariate scale-space

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** L²(R^d) × t → ×

**Source definition.** Vector heat equation; tensor scale-spaces for matrix-valued data.

**Source property — not certified.** Anisotropic-diffusion variants.

**Source use — context only.** Geometric image analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W33.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w34"></a>

#### W34. `AOS` — additive-operator splitting

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Diffusion × time step → numerical scheme

**Source definition.** AOS averages 1D implicit diffusions.

**Source property — not certified.** Unconditionally stable.

**Source use — context only.** Efficient scale-space algorithm.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W34.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w35"></a>

#### W35. `Wav-Pde` — wavelet PDE solver

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** PDE × → fast iterative solver

**Source definition.** Galerkin discretization in wavelet basis.

**Source property — not certified.** Sparsity in wavelet basis ⇒ near-linear cost.

**Source use — context only.** Adaptive PDE solution.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W35.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w36"></a>

#### W36. `MG` — multigrid operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Linear system × hierarchy of grids → solution

**Source definition.** V-cycle: restriction → coarse-grid solve → prolongation.

**Source property — not certified.** Optimal O(n) complexity for elliptic PDEs.

**Source use — context only.** Scientific computing.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W36.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w37"></a>

#### W37. `AMG` — algebraic multigrid

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sparse matrix × → solver

**Source definition.** Coarsens by matrix structure, not geometry.

**Source property — not certified.** Black-box solver for elliptic systems.

**Source use — context only.** Unstructured-mesh PDEs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W37.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w38"></a>

#### W38. `Lift` — wavelet lifting

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Signal × → wavelet coefficients

**Source definition.** Split → predict → update.

**Source property — not certified.** In-place computation; integer-to-integer.

**Source use — context only.** Hardware-friendly wavelet.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W38.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w39"></a>

#### W39. `Sub_λ` — subdivision rule

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Coarse data × scheme → refined data

**Source definition.** Convergent iff mask m̂(ξ) = 1 + O(ξ) and contractivity.

**Source property — not certified.** Stationary if rule does not change with level.

**Source use — context only.** Surface modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W39.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w40"></a>

#### W40. `Stat_op` — stationary subdivision operator

**Disposition.** ACTIVE INVESTIGATION; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → ×

**Source definition.** Same rule at every level.

**Source property — not certified.** Smoothness controlled by joint spectral radius of subdivision matrices.

**Source use — context only.** Stability analysis.

**QPT-128 substitution.** Use only through [A06](#a06), [A27](#a27), with each contract and its four research questions.

**Eligibility question for W40.** Can an adversarial interleaving move amplitude into an unbounded subspace or reintroduce already removed failure paths? Identify the exact role of this operator in that derivation.

<a id="op-w41"></a>

#### W41. `Pyramid` — Gaussian pyramid operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Image × levels → multiresolution stack

**Source definition.** L_{k+1} := downsample(L_k * gauss).

**Source property — not certified.** Approximates scale-space at dyadic scales.

**Source use — context only.** Computer-vision feature pyramids.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W41.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w42"></a>

#### W42. `Lapl_Pyr` — Laplacian pyramid

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Image × → pyramid

**Source definition.** L_k := G_k - upsample(G_{k+1} * gauss).

**Source property — not certified.** Multiresolution band-pass representation.

**Source use — context only.** Image fusion.

**QPT-128 substitution.** Use only through [A21](#a21), with each contract and its four research questions.

**Eligibility question for W42.** What theorem charges every absorb/squeeze call and grants the same adversarial access as the implementation? Identify the exact role of this operator in that derivation.

<a id="op-w43"></a>

#### W43. `RGFlow_PDE` — Polchinski exact renormalization equation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Effective action × scale → ×

**Source definition.** ∂_Λ Γ_Λ = (1/2) tr [(∂_Λ R_Λ)(Γ^{(2)}_Λ + R_Λ)^{-1}].

**Source property — not certified.** Exact one-loop-like flow equation.

**Source use — context only.** Non-perturbative QFT.

**Amendment (DEFINITION_MISMATCH).** The displayed effective-average-action flow with an inverse Hessian plus regulator is the Wetterich form, not the Polchinski equation. Specify which action and regulator are being used.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W43.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w44"></a>

#### W44. `MERA` — multiscale entanglement renormalization ansatz

**Disposition.** ACTIVE INVESTIGATION; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Quantum state × → ×

**Source definition.** Tensor network with disentanglers and isometries on log levels.

**Source property — not certified.** Captures critical 1D ground states efficiently.

**Source use — context only.** Holographic interpretations of quantum states.

**QPT-128 substitution.** Use only through [A21](#a21), with each contract and its four research questions.

**Eligibility question for W44.** Would changing the sponge parameters change the protocol and its implementation compatibility obligations? Identify the exact role of this operator in that derivation.

<a id="op-w45"></a>

#### W45. `DMRG` — density-matrix RG

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 1D quantum lattice × → ground state approximation

**Source definition.** Iteratively keeps largest-weight Schmidt eigenvectors.

**Source property — not certified.** Polynomial cost for gapped 1D systems.

**Source use — context only.** Quantum spin-chain ground states.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W45.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w46"></a>

#### W46. `TRG` — tensor renormalization group

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Tensor network × → coarse-grained network

**Source definition.** Levin-Nave block decomposition with SVD truncation.

**Source property — not certified.** Computes partition functions of 2D classical models.

**Source use — context only.** Statistical mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W46.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w47"></a>

#### W47. `Bal_Wav` — balanced multiwavelets

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** L² × → multiwavelet system

**Source definition.** Polynomial-preserving multi-wavelets without prefiltering.

**Source property — not certified.** Vanishing moments + balancing.

**Source use — context only.** Multivariate signal processing.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for W47.** Does this transform preserve the information and event needed by verification/extraction, with all discarded coefficients, seeds and costs accounted for?

<a id="op-w48"></a>

#### W48. `Spar_op` — sparse approximation operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Signal × dictionary → sparse code

**Source definition.** x* := argmin ‖α‖_0 s.t. Φ α = x (NP-hard; replace with ℓ_1).

**Source property — not certified.** BPDN, OMP, lasso provide computable approximations.

**Source use — context only.** Compressed sensing.

**QPT-128 substitution.** Use only through [A14](#a14), with each contract and its four research questions.

**Eligibility question for W48.** If compression discards information, is that information necessary to verify authorization or extract a conflict witness? Identify the exact role of this operator in that derivation.

<a id="op-w49"></a>

#### W49. `FrameTh` — frame-theoretic atomic decomposition

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** L² × frame → reconstruction

**Source definition.** f = Σ ⟨f, ψ̃_λ⟩ ψ_λ.

**Source property — not certified.** Robust to coefficient loss.

**Source use — context only.** Quantization and error correction.

**QPT-128 substitution.** Use only through [A07](#a07), with each contract and its four research questions.

**Eligibility question for W49.** Can a total per-round amplitude norm of at most 3/4 be proved for the actual transition? Identify the exact role of this operator in that derivation.

<a id="op-w50"></a>

#### W50. `Lift_ZZ` — integer-to-integer wavelet

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Z^Z signal × → Z^Z transform

**Source definition.** Lifting steps with rounding.

**Source property — not certified.** Lossless reversibility.

**Source use — context only.** Lossless image coding.

**QPT-128 substitution.** Use only through [A14](#a14), with each contract and its four research questions.

**Eligibility question for W50.** Does the operator improve conditional guessing probability or only a Shannon-entropy/visual statistic? Identify the exact role of this operator in that derivation.

### Family Y: Games and decisions

<a id="op-y1"></a>

#### Y1. `MinMax` — minimax operator

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT.

**Source signature.** Two-player zero-sum game × strategy spaces → R

**Source definition.** v := min_{x ∈ X} max_{y ∈ Y} u(x, y).

**Source property — not certified.** v ≤ max-min in general; equality under convex/compact assumptions (von Neumann).

**Source use — context only.** Worst-case decision theory.

**Amendment (DIRECTION_ERROR).** Use sup_y inf_x u(x,y)<=inf_x sup_y u(x,y). Equality requires an appropriate minimax theorem, including mixed strategies for finite zero-sum games. Preserve the same minimizing and maximizing players across both expressions.

**QPT-128 substitution.** Use only through [A03](#a03), with each contract and its four research questions.

**Eligibility question for Y1.** Does the claimed extractor exist uniformly for all adversaries, or is a different uncomputable extractor selected after seeing each attack? Identify the exact role of this operator in that derivation.

<a id="op-y2"></a>

#### Y2. `MaxMin` — maximin operator

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** × × → R

**Source definition.** v := max_x min_y u(x, y).

**Source property — not certified.** Equals minimax in finite zero-sum games.

**Source use — context only.** Security strategies.

**Amendment (DIRECTION_ERROR).** Use sup_y inf_x u(x,y)<=inf_x sup_y u(x,y). Equality requires an appropriate minimax theorem, including mixed strategies for finite zero-sum games. Preserve the same minimizing and maximizing players across both expressions.

**QPT-128 substitution.** Use only through [A03](#a03), with each contract and its four research questions.

**Eligibility question for Y2.** Was an average over generated keys replaced by a bound for every key without a bad-key event? Identify the exact role of this operator in that derivation.

<a id="op-y3"></a>

#### Y3. `NE` — Nash equilibrium

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** n-player game → strategy profile

**Source definition.** x* with u_i(x*) ≥ u_i(y_i, x*_{-i}) for all i, y_i.

**Source property — not certified.** Existence in mixed strategies for finite games (Nash).

**Source use — context only.** Strategic decision making.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y3.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y4"></a>

#### Y4. `BR` — best response

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Player × opponent profile → set of best strategies

**Source definition.** BR_i(x_{-i}) := argmax_{y_i} u_i(y_i, x_{-i}).

**Source property — not certified.** NE iff x_i ∈ BR_i(x_{-i}) for all i.

**Source use — context only.** Iterative algorithms for equilibrium.

**QPT-128 substitution.** Use only through [A03](#a03), with each contract and its four research questions.

**Eligibility question for Y4.** Which candidate parameters minimize the worst proved error with all required resources charged? Identify the exact role of this operator in that derivation.

<a id="op-y5"></a>

#### Y5. `CE` — correlated equilibrium

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Game × → distribution over action profiles

**Source definition.** Distribution π such that for each i and a, a' ∈ A_i: E_π[u_i(a, ·)] ≥ E_π[u_i(a', ·)].

**Source property — not certified.** Set of CE is convex polytope; contains NE.

**Source use — context only.** Mediated coordination.

**Amendment (FORMULA_ERROR).** For each recommended action a and deviation a_prime, require sum_(a_minus_i) pi(a,a_minus_i)*(u_i(a,a_minus_i)-u_i(a_prime,a_minus_i))>=0. The recommendation-conditioned weights cannot be dropped.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y5.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y6"></a>

#### Y6. `ESS` — evolutionarily stable strategy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game (symmetric) → strategy

**Source definition.** x* is ESS if it is a strict NE against itself or has invasion barrier ε against any mutant.

**Source property — not certified.** ESS ⇒ NE; converse fails in general.

**Source use — context only.** Behavioral evolution.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y6.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y7"></a>

#### Y7. `RD` — replicator dynamics

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Population × time → trajectory

**Source definition.** ẋ_i = x_i (f_i(x) - ⟨f, x⟩).

**Source property — not certified.** ESS attracts; folk theorem links interior equilibria to NE.

**Source use — context only.** Evolutionary game theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y7.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y8"></a>

#### Y8. `Fic_play` — fictitious play

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × → strategy sequence

**Source definition.** Each player best-responds to empirical history of opponents.

**Source property — not certified.** Converges in 2-player zero-sum and potential games.

**Source use — context only.** Learning equilibria.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y8.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y9"></a>

#### Y9. `No_reg` — no-regret learning operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sequence × algorithm → cumulative regret

**Source definition.** R_T := Σ (u(a*, ·) - u(a_t, ·)).

**Source property — not certified.** Algorithms (Hedge, FTRL) achieve R_T = O(√(T log K)).

**Source use — context only.** Online learning, ad auctions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y9.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y10"></a>

#### Y10. `Lemke-Howson` — Lemke-Howson algorithm

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Bimatrix game × → NE

**Source definition.** Pivots through best-response polytopes.

**Source property — not certified.** Finds at least one NE; PPAD-complete in general.

**Source use — context only.** Computing 2-player NE.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y10.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y11"></a>

#### Y11. `Auction_op` — auction allocation

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Bids × auction rule → allocation, payment

**Source definition.** First-price: highest bidder pays bid; second-price (Vickrey): pays second-highest.

**Source property — not certified.** Vickrey is dominant-strategy truthful.

**Source use — context only.** Mechanism design.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y11.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y12"></a>

#### Y12. `VCG` — Vickrey-Clarke-Groves mechanism

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Bids × allocation → payments

**Source definition.** Pays each agent the externality their presence imposes on others.

**Source property — not certified.** Truth-telling is dominant; efficient allocation.

**Source use — context only.** Combinatorial auctions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y12.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y13"></a>

#### Y13. `MD` — mechanism-design operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Social choice rule × → implementation

**Source definition.** Gibbard-Satterthwaite: only dictatorship is strategy-proof onto.

**Source property — not certified.** Strategy-proof, efficient, anonymous: impossible in general.

**Source use — context only.** Voting and auctions.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y13.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y14"></a>

#### Y14. `Sha-Folk` — Shapley-Folkman lemma

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Sum of n compact sets in R^d → distance

**Source definition.** Distance of x ∈ co(Σ A_i) from Σ A_i bounded by max d radii.

**Source property — not certified.** Approximate convexification for large games.

**Source use — context only.** Non-convex aggregate analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y14.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y15"></a>

#### Y15. `Core_op` — core of cooperative game

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** (N, v) → set of allocations

**Source definition.** Core := { x ∈ R^N : x(N) = v(N), x(S) ≥ v(S) ∀S }.

**Source property — not certified.** Non-empty iff game is balanced (Bondareva-Shapley).

**Source use — context only.** Stable cost-sharing.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for Y15.** Which public evidence proves that a common signer actually signed both statements? Identify the exact role of this operator in that derivation.

<a id="op-y16"></a>

#### Y16. `Shap_alt` — Shapley value (alternate)

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** (N, v) → R^N

**Source definition.** φ_i := Σ_{S ⊂ N \ {i}} (|S|! (n - |S| - 1)!)/n! · (v(S ∪ {i}) - v(S)).

**Source property — not certified.** Unique value satisfying efficiency, symmetry, additivity, dummy.

**Source use — context only.** Fair cost attribution.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for Y16.** Does a quorum intersection proof get incorrectly treated as proof that shares were collected through a secure distributed protocol? Identify the exact role of this operator in that derivation.

<a id="op-y17"></a>

#### Y17. `Nucl_op` — nucleolus operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** (N, v) → allocation

**Source definition.** Lexicographically minimizes vector of complaints (descending).

**Source property — not certified.** Always exists, unique; in core if core non-empty.

**Source use — context only.** Disagreement-minimizing distribution.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y17.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y18"></a>

#### Y18. `Kakutani` — Kakutani fixed point

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Compact convex × USC convex-valued correspondence → fixed point

**Source definition.** Φ: K ⇒ K with non-empty convex values has fixed point.

**Source property — not certified.** Generalizes Brouwer; basis of NE existence proofs.

**Source use — context only.** Equilibrium existence.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y18.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y19"></a>

#### Y19. `Brouw` — Brouwer fixed point

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Compact convex × continuous self-map → fixed point

**Source definition.** f: K → K continuous has fixed point.

**Source property — not certified.** Topological theorem; constructive only in special cases.

**Source use — context only.** Foundational existence theorem.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y19.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y20"></a>

#### Y20. `EvolDyn` — evolutionary dynamics class

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × dynamic → trajectory

**Source definition.** Includes replicator, BNN, Smith dynamics.

**Source property — not certified.** Different dynamics may select different equilibria.

**Source use — context only.** Modeling competing populations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y20.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y21"></a>

#### Y21. `BNN` — BNN dynamic

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Population × → flow

**Source definition.** ẋ_i = max(0, payoff_i - avg) - x_i max(0, total).

**Source property — not certified.** Selects NE; equilibrium stationary points coincide with NE.

**Source use — context only.** Continuous-time learning.

**Amendment (FORMULA_GAP).** For BNN dynamics the second term is x_i times the SUM of all positive payoff excesses, not the positive part of their algebraic sum.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y21.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y22"></a>

#### Y22. `Risk_dom` — risk dominance

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** 2x2 coordination game → equilibrium

**Source definition.** Equilibrium (A, A) risk-dominates (B, B) iff product of deviation losses larger.

**Source property — not certified.** Selection criterion in coordination games.

**Source use — context only.** Equilibrium refinement.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y22.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y23"></a>

#### Y23. `Tremb` — trembling-hand perfect

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × → NE

**Source definition.** Limit as ε → 0 of equilibria of ε-perturbed games.

**Source property — not certified.** Refines NE: rules out dominated strategies in trembling games.

**Source use — context only.** Robust equilibrium concept.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y23.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y24"></a>

#### Y24. `Seq-Eq` — sequential equilibrium

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Extensive-form game × → (strategy, beliefs)

**Source definition.** Beliefs consistent with limits of fully mixed; strategy sequentially rational.

**Source property — not certified.** Refines subgame perfection in imperfect info.

**Source use — context only.** Dynamic games with private information.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y24.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y25"></a>

#### Y25. `Bayes-NE` — Bayesian Nash equilibrium

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game with types × → strategy as type-map

**Source definition.** x_i(t_i) ∈ argmax E_{t_{-i}} u_i(x_i, x_{-i}(t_{-i}), t).

**Source property — not certified.** Existence via Kakutani in continuous types.

**Source use — context only.** Auctions, principal-agent.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y25.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y26"></a>

#### Y26. `Stack` — Stackelberg leadership

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Leader-follower game → equilibrium

**Source definition.** Leader x* := argmax_x u_L(x, BR_F(x)).

**Source property — not certified.** Sequential vs simultaneous: leader may benefit from commitment.

**Source use — context only.** Industrial-organization economics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y26.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y27"></a>

#### Y27. `Bargain` — Nash bargaining solution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Bargaining problem (S, d) → ×

**Source definition.** Maximizes (u_1 - d_1)(u_2 - d_2) over S.

**Source property — not certified.** Axiomatic: Pareto, symmetric, scale-invariant, IIA.

**Source use — context only.** Cooperative-game arbitration.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y27.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y28"></a>

#### Y28. `Kalai` — Kalai-Smorodinsky bargaining

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Bargaining problem × → ×

**Source definition.** Maximal point on line from d to ideal.

**Source property — not certified.** Axiomatic: replaces IIA with monotonicity.

**Source use — context only.** Alternative bargaining solution.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y28.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y29"></a>

#### Y29. `Egal` — egalitarian solution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Bargaining × → ×

**Source definition.** Equalizes gains over d.

**Source property — not certified.** Maximin-fair.

**Source use — context only.** Equity-driven bargaining.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y29.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y30"></a>

#### Y30. `Pot_game` — potential game operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SPECIFIC AMENDMENT.

**Source signature.** Game × → potential function (if exists)

**Source definition.** Φ: A → R with u_i(a_i', a_{-i}) - u_i(a_i, a_{-i}) = Φ(a_i', a_{-i}) - Φ(a_i, a_{-i}).

**Source property — not certified.** Best-response dynamics converge to NE.

**Source use — context only.** Congestion games, routing.

**Amendment (DOMAIN_GAP).** Finite exact potential games terminate under strict unilateral improvement. Arbitrary tie moves or simultaneous best responses need not converge.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y30.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y31"></a>

#### Y31. `Cong_game` — congestion game operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Resources × users × cost on each resource → game

**Source definition.** Always has potential ⇒ NE exists in pure strategies.

**Source property — not certified.** Rosenthal's potential.

**Source use — context only.** Network routing.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y31.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y32"></a>

#### Y32. `Pri-Anar` — price of anarchy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × social welfare → ratio

**Source definition.** PoA := worst NE cost / optimal cost.

**Source property — not certified.** Bounded for selfish routing (Roughgarden-Tardos).

**Source use — context only.** Inefficiency of selfish behavior.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y32.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y33"></a>

#### Y33. `Pri-Stab` — price of stability

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × → ratio

**Source definition.** PoS := best NE cost / optimal cost.

**Source property — not certified.** Lower than PoA; bounded for fair-cost-sharing games.

**Source use — context only.** Inefficiency under best-case decentralization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y33.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y34"></a>

#### Y34. `Smith` — Smith dynamics

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Population × → flow

**Source definition.** Adjustment proportional to better-response gains; smooth.

**Source property — not certified.** Local stability conditions established.

**Source use — context only.** Smooth evolutionary game.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y34.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y35"></a>

#### Y35. `LQ_game` — linear-quadratic dynamic game

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION.

**Source signature.** Quadratic costs × linear dynamics × → ×

**Source definition.** Riccati-like equations characterize equilibrium feedback strategies.

**Source property — not certified.** Solvable via coupled Riccati equations.

**Source use — context only.** Engineering control.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y35.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y36"></a>

#### Y36. `Folk_thm` — folk theorem operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Infinite repeated game × → equilibrium payoff set

**Source definition.** Any feasible IR payoff is sustainable with sufficient patience.

**Source property — not certified.** Triggers with grim or finite-stage punishment.

**Source use — context only.** Cooperation via reputation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y36.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y37"></a>

#### Y37. `Tit-Tat` — tit-for-tat

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Repeated PD × → strategy

**Source definition.** Cooperate, then copy opponent's last action.

**Source property — not certified.** Robust strategy in Axelrod's tournaments.

**Source use — context only.** Iterated prisoner's dilemma.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y37.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y38"></a>

#### Y38. `UCB` — upper confidence bound

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Multi-armed bandit × → action choice

**Source definition.** Pull arm a maximizing μ̂_a + √(2 log t / n_a).

**Source property — not certified.** Achieves logarithmic regret.

**Source use — context only.** Exploration-exploitation.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for Y38.** Can a constructed rare event fool all empirical tests while violating the target bound? Identify the exact role of this operator in that derivation.

<a id="op-y39"></a>

#### Y39. `Thompson` — Thompson sampling

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Bandit × Bayes prior → arm choice

**Source definition.** Sample θ ~ posterior, play argmax μ(θ).

**Source property — not certified.** Optimal regret in Bayesian sense.

**Source use — context only.** Online optimization.

**QPT-128 substitution.** Use only through [A26](#a26), with each contract and its four research questions.

**Eligibility question for Y39.** Is the attack class being tested narrower than the QPT adversaries in the theorem? Identify the exact role of this operator in that derivation.

<a id="op-y40"></a>

#### Y40. `Reg-Mat` — regret matching

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × → mixed strategy update

**Source definition.** Probability ∝ positive part of cumulative regret.

**Source property — not certified.** Converges to CE in average play.

**Source use — context only.** Computing correlated equilibria.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y40.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y41"></a>

#### Y41. `CFR` — counterfactual regret minimization

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Extensive game × → strategy

**Source definition.** Updates strategies based on counterfactual regret at each information set.

**Source property — not certified.** Converges to NE in zero-sum games.

**Source use — context only.** Solving poker.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y41.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y42"></a>

#### Y42. `Mech_Aut` — AGV mechanism

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × → balanced budget mechanism

**Source definition.** Modifies VCG to enforce budget balance.

**Source property — not certified.** Budget-balanced + interim individually rational.

**Source use — context only.** Public-good provision.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y42.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y43"></a>

#### Y43. `Sup-Mod` — supermodular game

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × → boolean

**Source definition.** u_i has increasing differences in (own action, opponent action).

**Source property — not certified.** Best-response monotone; smallest and largest NE exist.

**Source use — context only.** Strategic complements.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y43.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y44"></a>

#### Y44. `Sub-Mod` — submodular game

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Game × → boolean

**Source definition.** u_i has decreasing differences.

**Source property — not certified.** Strategic substitutes; existence and uniqueness conditions.

**Source use — context only.** Strategic substitutability.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y44.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y45"></a>

#### Y45. `Inv_op` — invariance under affine transformations

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Solution concept × → boolean

**Source definition.** Whether the solution is preserved under positive affine rescaling of utilities.

**Source property — not certified.** NE is invariant; non-utilitarian welfare concepts may not be.

**Source use — context only.** Foundational equivalences.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y45.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y46"></a>

#### Y46. `Cap_Glob` — global game operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Coordination game × private signals → equilibrium

**Source definition.** Carlsson-van Damme: noise selection picks unique equilibrium.

**Source property — not certified.** Pins down equilibrium when multiple exist.

**Source use — context only.** Currency attacks, bank runs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y46.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y47"></a>

#### Y47. `Mat_Th` — matching theory operator (Gale-Shapley)

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Preferences × → stable matching

**Source definition.** Deferred-acceptance algorithm always terminates with a stable match.

**Source property — not certified.** Proposer-optimal; respondent-pessimal stable matching.

**Source use — context only.** School choice, medical residencies.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y47.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y48"></a>

#### Y48. `Top-Trad` — top-trading cycles

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Object endowment × preferences → allocation

**Source definition.** Removes cycles of mutually-most-preferred trades.

**Source property — not certified.** Strategy-proof, individually rational, Pareto.

**Source use — context only.** Kidney exchange.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y48.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

<a id="op-y49"></a>

#### Y49. `Vot-Th` — voting theorem operator

**Disposition.** ACTIVE INVESTIGATION.

**Source signature.** Voting rule × → property

**Source definition.** Arrow: no rule satisfies Pareto + IIA + non-dictator on ≥ 3 alternatives.

**Source property — not certified.** Foundational impossibility.

**Source use — context only.** Social choice.

**QPT-128 substitution.** Use only through [A24](#a24), with each contract and its four research questions.

**Eligibility question for Y49.** Does the extracted witness contain distinct roster-bound keys rather than a threshold-sized list with duplicates? Identify the exact role of this operator in that derivation.

<a id="op-y50"></a>

#### Y50. `Sub-NE` — subgame-perfect equilibrium

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED.

**Source signature.** Extensive-form game × → strategy

**Source definition.** NE in every subgame.

**Source property — not certified.** Backward induction in finite games.

**Source use — context only.** Bargaining; dynamic games.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Y50.** Does this game result bound every admissible adversary or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?

### Family Z: Hybrid constructions

<a id="op-z1"></a>

#### Z1. `PH_KL` — persistent KL divergence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Pair of filtrations × → R-valued function

**Source definition.** PH_KL(t) := D_KL(PH-distribution at scale t).

**Source property — not certified.** Combines persistent homology [F11.7] with KL [F6.4]; stable under interleaving.

**Source use — context only.** Topological-statistical comparison of data.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z1.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z2"></a>

#### Z2. `Trop_Free` — tropical free convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Free probability + tropical limit → ×

**Source definition.** lim β→∞ free R-transform replacing log with -β·.

**Source property — not certified.** Composition of [F2.42] and [F13.3]; gives min-plus analog of free additive convolution.

**Source use — context only.** Zero-temperature random-matrix limits.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z2.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z3"></a>

#### Z3. `L_q^Δ` — q-deformed graph Laplacian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Graph × q ∈ C → operator on functions on vertices

**Source definition.** L_q f(v) := Σ_{w ~ v} (f(v) - q^{d(v,w)} f(w)).

**Source property — not certified.** Combines [F4.1] and [F5.35]; reduces to graph Laplacian at q = 1.

**Source use — context only.** Quantum walks on graphs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z3.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z4"></a>

#### Z4. `Hol_SDE` — stochastic holonomy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Connection × Brownian path → random group element

**Source definition.** Hol_SDE := P-exp(∫ A_i ∘ dB^i_t), Stratonovich.

**Source property — not certified.** Combines [F7.4] and [F14.18]; satisfies SDE on the gauge group.

**Source use — context only.** Random gauge transformations.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z4.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z5"></a>

#### Z5. `RT_IB` — information bottleneck on resource theory

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** (ρ, free states F, β) → optimal compressed state

**Source definition.** Minimizes D_F(σ) - β · I(σ; ρ) over CPTP maps.

**Source property — not certified.** Composes [F6.35] and [F16.5].

**Source use — context only.** Resource-efficient quantum coding.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z5.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z6"></a>

#### Z6. `SpecWav` — spectral wavelets

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Graph × scale → operator basis

**Source definition.** ψ_{s,k}(L) := s^k L^k φ(sL) for spectral filter φ.

**Source property — not certified.** Combines [F8.8] and [F18.1].

**Source use — context only.** Signal processing on graphs.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z6.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z7"></a>

#### Z7. `Top_Game` — topological game value

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Game graph × topology → ×

**Source definition.** Combines game-theoretic backward induction with persistent-homology summary of strategy space.

**Source property — not certified.** Distinguishes games with different equilibrium-set topologies.

**Source use — context only.** Robust equilibrium analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z7.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z8"></a>

#### Z8. `Frac_FreeProb` — fractional free convolution

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Free distributions × α → ×

**Source definition.** R_{μ ⊠_α ν} := R_μ^α + R_ν^α (formal α-interpolation).

**Source property — not certified.** Combines [F3.1] and [F13.3].

**Source use — context only.** Anomalous random-matrix universality.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z8.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z9"></a>

#### Z9. `Cat_RG` — categorified renormalization group

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** ∞-category of effective theories × scale → ×

**Source definition.** RG flow as functor on a category of QFTs.

**Source property — not certified.** Combines [F12.13] and [F18.11].

**Source use — context only.** Foundational QFT structures.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z9.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z10"></a>

#### Z10. `LMM` — Lévy-Macdonald measure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Lévy process × Macdonald parameters → operator-valued process

**Source definition.** Builds processes with q-symmetric jump-measure structure.

**Source property — not certified.** Combines [F4.32] and [F14.16].

**Source use — context only.** Integrable random processes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z10.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z11"></a>

#### Z11. `Trop_PathInt` — tropical path integral

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** (min,+) action × → minimum-cost path

**Source definition.** Z_⊗ := ⊕_paths ⊗_edges weight, equals min-cost path.

**Source property — not certified.** Combines [F2.5] and [F7.10]; classical limit of quantum path integral.

**Source use — context only.** WKB approximation.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z11.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z12"></a>

#### Z12. `Wass_Game` — Wasserstein game

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Player strategies as distributions × cost in W_p → equilibrium

**Source definition.** Mean-field game where state distribution is the strategy.

**Source property — not certified.** Combines [F9.31] and [F19.3].

**Source use — context only.** Crowd dynamics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z12.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z13"></a>

#### Z13. `FRG_q` — q-deformed functional RG

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** q-deformed effective action × scale → ×

**Source definition.** ∂_Λ Γ_Λ^q := q-trace of one-loop kernel.

**Source property — not certified.** Combines [F4.23] and [F18.43].

**Source use — context only.** Quantum-group QFT.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z13.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z14"></a>

#### Z14. `Hom_Game` — homotopical game theory

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** n-player game × strategy space topology → set of equilibrium classes mod homotopy

**Source definition.** Classifies equilibria up to deformation.

**Source property — not certified.** Combines [F11.23] and [F19.3].

**Source use — context only.** Topological refinements of NE.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z14.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z15"></a>

#### Z15. `Trop_Wav` — tropical wavelets

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** (min,+) signal × scale → ×

**Source definition.** Idempotent multi-scale decomposition using min-plus convolution.

**Source property — not certified.** Combines [F2.11] and [F18.1].

**Source use — context only.** Multi-scale decomposition of cost surfaces.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z15.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z16"></a>

#### Z16. `Q-Mart` — q-deformed martingale

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Discrete process × q → ×

**Source definition.** q-shift in conditional-expectation update.

**Source property — not certified.** Combines [F4.10] and [F9.14].

**Source use — context only.** Discrete-time quantum-stochastic models.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z16.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z17"></a>

#### Z17. `Lap_pers` — persistent Laplacian

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Filtered simplicial complex × → operator family

**Source definition.** L_{q,a,b} := Hodge Laplacian restricted to {chains born by a, dying after b}.

**Source property — not certified.** Combines [F15.7] and [F11.7]; eigenvalues encode persistence.

**Source use — context only.** Topological spectral analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z17.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z18"></a>

#### Z18. `Coh_Game` — coherence games

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Multi-agent quantum game × → equilibrium with coherence resource

**Source definition.** Players' utilities defined on coherent states.

**Source property — not certified.** Combines [F16.32] and [F19.3].

**Source use — context only.** Quantum strategic interaction.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z18.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z19"></a>

#### Z19. `Trop_Cat` — tropical category

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Category enriched over (R_max, max, +) → ×

**Source definition.** Hom-sets are tropical numbers; composition is +.

**Source property — not certified.** Combines [F2.1] and [F12.10].

**Source use — context only.** Categorical optimization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z19.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z20"></a>

#### Z20. `Stoc_RG` — stochastic RG flow

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Coupling × scale × noise → SDE on coupling

**Source definition.** dg = β(g) d(log Λ) + σ dW.

**Source property — not certified.** Combines [F14.24] and [F18.11].

**Source use — context only.** Noisy RG in disordered systems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z20.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z21"></a>

#### Z21. `Mart_Spec` — martingale spectral measure

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Square-integrable martingale → spectral measure

**Source definition.** Karhunen-Loève spectral decomposition of the martingale.

**Source property — not certified.** Combines [F8.9] and [F9.14].

**Source use — context only.** Spectral methods in stochastic analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z21.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z22"></a>

#### Z22. `Frac_Pois` — fractional Poisson process

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Time × α ∈ (0,1] → counting process

**Source definition.** Increments E_α(-λ t^α)-distributed; reduces to Poisson at α = 1.

**Source property — not certified.** Combines [F3.11] and [F14.43].

**Source use — context only.** Heavy-tailed event modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z22.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z23"></a>

#### Z23. `Sk_Game` — Skorokhod-game embedding

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Game value process × → optimal stopping

**Source definition.** Stops Brownian motion to match a target value distribution.

**Source property — not certified.** Combines [F14.19] and [F19.1].

**Source use — context only.** Optimal-stopping games.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z23.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z24"></a>

#### Z24. `Coh_PH` — coherent persistence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Family of filtrations with consistent maps → persistence module

**Source definition.** PH but with structural maps respecting external symmetry.

**Source property — not certified.** Combines [F11.7] and [F12.18].

**Source use — context only.** Equivariant TDA.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z24.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z25"></a>

#### Z25. `Q-LDP` — q-deformed large deviations

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Sequence × q → rate function I_q

**Source definition.** I_q := Legendre transform of q-CGF.

**Source property — not certified.** Combines [F4.18] and [F14.30].

**Source use — context only.** Non-extensive statistical mechanics.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z25.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z26"></a>

#### Z26. `Sob_q` — q-fractional Sobolev space

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** × × → Banach space

**Source definition.** H_q^{α,p} := { f : D_q^α f ∈ L^p }.

**Source property — not certified.** Combines [F3.7] and [F4.15].

**Source use — context only.** Discrete fractional regularity.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z26.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z27"></a>

#### Z27. `KS_Net` — Kolmogorov-Sinai network

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Markov chain on metric graph × → entropy rate

**Source definition.** h_KS := lim n^{-1} H(X_1,...,X_n).

**Source property — not certified.** Combines [F6.46] and [F9.35].

**Source use — context only.** Information rate of stochastic processes on networks.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z27.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z28"></a>

#### Z28. `Cohom_Game` — cohomological game value

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Game × cohomology theory → invariant

**Source definition.** H^*(strategy space, value) detects obstructions to equilibrium selection.

**Source property — not certified.** Combines [F11.2] and [F19.3].

**Source use — context only.** Topological obstructions in mechanism design.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z28.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z29"></a>

#### Z29. `BV_HoTT` — BV-quantization in HoTT

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Type-theoretic action × → quantization

**Source definition.** BV operator [F13.50] formulated in homotopy-type theory [F17.50].

**Source property — not certified.** Combines [F13.50] and [F17.50].

**Source use — context only.** Foundational quantization.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z29.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z30"></a>

#### Z30. `OT_Game` — optimal-transport game

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Source × target measures × cost × player choice → equilibrium

**Source definition.** Players choose plans; cost is W_p; NE = optimal coupling.

**Source property — not certified.** Combines [F9.31] and [F19.3].

**Source use — context only.** Matching markets.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z30.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z31"></a>

#### Z31. `Ric_Game` — Ricci-flow game

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Manifold × players choosing metric perturbations → trajectory

**Source definition.** Players minimize curvature functionals along Ricci flow.

**Source property — not certified.** Combines [F15.19] and [F19.3].

**Source use — context only.** Geometric design problems.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z31.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z32"></a>

#### Z32. `Tr_Schw` — tropical Schwarz function

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Curve in tropical projective space → ×

**Source definition.** Tropical analog of Schwarzian derivative.

**Source property — not certified.** Combines [F2.40] and [F15.21].

**Source use — context only.** Curvature in tropical geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z32.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z33"></a>

#### Z33. `Free_Game` — free-probability game

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Free random variables × strategy → expected payoff

**Source definition.** Payoff E[u(X_1,...,X_n)] under freeness rather than independence.

**Source property — not certified.** Combines [F13.9] and [F19.3].

**Source use — context only.** Non-commutative strategic settings.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z33.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z34"></a>

#### Z34. `Wav_Quantum` — wavelet quantum state

**Disposition.** ACTIVE INVESTIGATION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Quantum state × wavelet basis → multi-scale coefficients

**Source definition.** ψ_{j,k} := wavelet basis of L²(R) used to expand quantum states.

**Source property — not certified.** Combines [F18.4] and [F8.10].

**Source use — context only.** Multi-scale quantum simulation.

**QPT-128 substitution.** Use only through [A21](#a21), with each contract and its four research questions.

**Eligibility question for Z34.** What theorem charges every absorb/squeeze call and grants the same adversarial access as the implementation? Identify the exact role of this operator in that derivation.

<a id="op-z35"></a>

#### Z35. `Top_Crypt` — topological cryptography

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Topological invariant × secret → protocol

**Source definition.** Uses computational hardness of topological invariants (e.g. knot equivalence).

**Source property — not certified.** Combines [F11.26] and [F17.18].

**Source use — context only.** Post-quantum cryptography.

**Amendment (UNSUPPORTED_SECURITY).** A topological invariant is not a post-quantum signature construction or hardness reduction. Replace the security claim with a protocol contract: explicit algorithms, average-case instance distribution, QPT game, reduction and concrete resources.

**QPT-128 substitution.** Use only through [A17](#a17), [A19](#a19), with each contract and its four research questions.

**Eligibility question for Z35.** Does an idealized Dilithium theorem cover the standardized algorithms, encodings and rejection behavior being deployed? Identify the exact role of this operator in that derivation.

<a id="op-z36"></a>

#### Z36. `Lyap_Info` — Lyapunov-information operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Dynamical system × → joint Lyapunov + entropy spectrum

**Source definition.** (λ, h_KS) pair captures chaos + information rate.

**Source property — not certified.** Combines [F8.34] and [F6.1].

**Source use — context only.** Chaos quantification.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z36.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z37"></a>

#### Z37. `Mod_Game` — modal game theory

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Game with epistemic types × modal logic → equilibrium under knowledge

**Source definition.** Solution concept refined by common knowledge.

**Source property — not certified.** Combines [F17.1] and [F19.25].

**Source use — context only.** Epistemic game theory.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z37.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z38"></a>

#### Z38. `Cat_Info` — categorical information theory

**Disposition.** ACTIVE INVESTIGATION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Symmetric monoidal category × → entropy functor

**Source definition.** Functor H: Cat → R satisfying chain rule and gluing.

**Source property — not certified.** Combines [F12.14] and [F6.1].

**Source use — context only.** Foundations of information.

**QPT-128 substitution.** Use only through [A20](#a20), with each contract and its four research questions.

**Eligibility question for Z38.** Is a random ideal permutation being silently replaced with the known Keccak permutation? Identify the exact role of this operator in that derivation.

<a id="op-z39"></a>

#### Z39. `Hopf_Per` — Hopf-algebraic persistence

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Persistence module × Hopf-algebra action → ×

**Source definition.** Compatibility with multiplication and comultiplication.

**Source property — not certified.** Combines [F4.21] and [F11.7].

**Source use — context only.** Algebraic persistent homology.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z39.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z40"></a>

#### Z40. `RG_TDA` — RG-filtered topology

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Statistical-mechanics model × RG step → PH at each scale

**Source definition.** Tracks topological features through RG iterations.

**Source property — not certified.** Combines [F11.7] and [F18.46].

**Source use — context only.** Phase-transition detection.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z40.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z41"></a>

#### Z41. `Free_Hodge` — free Hodge theory

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Free-probability differential algebra × → decomposition

**Source definition.** Hodge-like decomposition for non-commutative chain complexes.

**Source property — not certified.** Combines [F13.5] and [F15.39].

**Source use — context only.** Non-commutative differential geometry.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z41.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z42"></a>

#### Z42. `Multi_Mart` — multi-scale martingale

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Process × wavelet basis → ×

**Source definition.** Wavelet coefficients of a martingale are themselves martingales at each scale.

**Source property — not certified.** Combines [F14.14] and [F18.1].

**Source use — context only.** Multi-scale stochastic analysis.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z42.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z43"></a>

#### Z43. `Cat_RT` — categorified resource theory

**Disposition.** ACTIVE INVESTIGATION; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Category of resources × ⊗ → ×

**Source definition.** Free operations as a sub-2-category.

**Source property — not certified.** Combines [F12.14] and [F16.10].

**Source use — context only.** Universal resource theories.

**QPT-128 substitution.** Use only through [A22](#a22), with each contract and its four research questions.

**Eligibility question for Z43.** Are setup costs, cached advice or precomputation inside the target adversary budget? Identify the exact role of this operator in that derivation.

<a id="op-z44"></a>

#### Z44. `Q-Modal` — q-deformed modal logic

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; SOURCE SIGNATURE NEEDS COMPLETION; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Modal logic × q-weight → ×

**Source definition.** Weighted accessibility with q-arithmetic.

**Source property — not certified.** Combines [F4.10] and [F17.1].

**Source use — context only.** Quantitative modal reasoning.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z44.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z45"></a>

#### Z45. `Frac_Game` — fractional dynamic game

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Game × α-fractional dynamics → equilibrium

**Source definition.** D^α u = ... with strategic interactions.

**Source property — not certified.** Combines [F3.3] and [F19.35].

**Source use — context only.** Memory effects in dynamic games.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z45.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z46"></a>

#### Z46. `PerEnt` — persistent entropy

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Persistence diagram → R

**Source definition.** PE := -Σ_i (ℓ_i / L) log(ℓ_i / L), L = total length.

**Source property — not certified.** Combines [F6.1] and [F11.19].

**Source use — context only.** Information content of barcodes.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z46.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z47"></a>

#### Z47. `OT_NN` — optimal-transport neural network operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Neural net × OT regularizer → trained network

**Source definition.** Loss includes W_p distance to target distribution.

**Source property — not certified.** Combines [F9.31] and [F8.29].

**Source use — context only.** Generative modeling.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z47.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z48"></a>

#### Z48. `Spec_Game` — spectral game theory

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Matrix game with spectral structure → equilibrium

**Source definition.** Equilibrium depends on eigenstructure of payoff matrix.

**Source property — not certified.** Combines [F8.1] and [F19.3].

**Source use — context only.** Structured games.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z48.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z49"></a>

#### Z49. `Cat_Inv` — categorical invariance operator

**Disposition.** PARKED — NO DIRECT ROUTE ESTABLISHED; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** Functor F × symmetry G → equivariant subfunctor

**Source definition.** F^G := largest sub-functor on which G acts trivially.

**Source property — not certified.** Combines [F12.46] and [F16.10].

**Source use — context only.** Equivariant categorical resource theories.

**QPT-128 substitution.** None established in this pass. Supply a finite typed adapter and an event/resource inequality before promoting this entry.

**Eligibility question for Z49.** Can the proposed fusion supply typed input/output algorithms, a proved invariant and a composable resource bound, rather than just names from two fields?

<a id="op-z50"></a>

#### Z50. `Master` — master operator (cross-family)

**Disposition.** ACTIVE INVESTIGATION; SPECIFIC AMENDMENT; HYBRID NAME IS NOT A COMPOSITION PROOF.

**Source signature.** All families → coherent multi-structure

**Source definition.** Master(ξ) := tuple (algebraic, geometric, probabilistic, logical, ...) lift of ξ.

**Source property — not certified.** Functorial across all 19 prior families; identity on the canonical projection.

**Source use — context only.** Universal organizing principle for mathematical modeling.

**Amendment (UNDEFINED_COMPOSITION).** A tuple of structures does not automatically define a functor or a security theorem. Replace Master by an explicit typed proof-obligation record whose composition is refused on incompatible games, distributions, oracle access or resource bounds.

**QPT-128 substitution.** Use only through [A28](#a28), with each contract and its four research questions.

**Eligibility question for Z50.** Which exact adapters justify every change of model between consecutive components? Identify the exact role of this operator in that derivation.

## Executed adversarial checks

**23 groups passed.** These tests cover selected counterexamples, exact finite identities, component inequalities and negative contract mutations. They do not test all 116 editorial amendments, instantiate an actual joint extractor, or establish a deployed cryptographic security claim.

| Check | Scope | Result |
|---|---|---|
| L1 threshold meet | Finite complete-chain counterexample. | PASS |
| L9/L10 majorization | Both normalized envelopes fail at k=1. | PASS |
| L35/L47 order | Lexicographic second projection fails; product width is two. | PASS |
| T7 cycle mean | Maximum of normalized traces differs from normalization after maximum. | PASS |
| T8 eigenvector uniqueness | Two non-translation-equivalent max-plus eigenvectors. | PASS |
| T42 softmin | Exact Hessian refutes convexity. | PASS |
| Q40/D9 signs | 54 commutator cases and an odd-order difference counterexample. | PASS |
| I21/I33 entropy corrections | Uniform interval translation preserves density; swapped support masses differ. | PASS |
| Contraction instruments | Exact K^T K=(1/2)I and robust K^T K=(9/16)I certificates. | PASS |
| Spectral-radius substitution rejected | Nilpotent norm-two map is not a valid failure instrument. | PASS |
| Measurement order | Two projection orders yield probabilities 1/4 and 1/2. | PASS |
| Marginals do not multiply | Perfectly correlated half-probability failures remain probability 1/2. | PASS |
| QPT staged component bounds | Exact minimum-round boundary checks at 32,64,92,128; wrong event substitution remains forbidden. | PASS |
| Generalized prefix-box lemma | 490 prefix counts and 156 maximum-box instances checked exhaustively. | PASS |
| Deterministic entropy | 32 small maps checked; the quantum-side-information extension is proved in the text. | PASS |
| Good events and retry tail | Tight four-outcome conditioning example; 519/518 exact truncation boundary. | PASS |
| Finite-field rank | 673 matrices enumerated; no seeded-module distribution claim follows. | PASS |
| Work/depth and reduction composition | Parallel work 37 vs depth 7; affine resource maps composed explicitly. | PASS |
| Fixed-hash versus independent oracle | Equality test gap is 1-2^-h; no claim about simulator-based indifferentiability. | PASS |
| Y1 minimax direction | Pure-strategy matching-pennies values give -1<1. | PASS |
| H20/R36 counterexamples | Two-feature Wasserstein squared cost two; local-reset Schmidt rank decreases. | PASS |
| Quorum set intersection | 441 pairs checked; no signature/authorization premise supplied. | PASS |
| Contract negative mutations | 10 mismatches/missing fields rejected; compatible records never self-certify a theorem. | PASS |

### Complete machine-readable results

```json
{
  "version": "1.33",
  "test_groups_passed": 23,
  "checks": [
    {
      "test": "L1 threshold meet",
      "status": "PASS",
      "scope": "Finite complete-chain counterexample."
    },
    {
      "test": "L9/L10 majorization",
      "status": "PASS",
      "scope": "Both normalized envelopes fail at k=1."
    },
    {
      "test": "L35/L47 order",
      "status": "PASS",
      "scope": "Lexicographic second projection fails; product width is two."
    },
    {
      "test": "T7 cycle mean",
      "status": "PASS",
      "scope": "Maximum of normalized traces differs from normalization after maximum."
    },
    {
      "test": "T8 eigenvector uniqueness",
      "status": "PASS",
      "scope": "Two non-translation-equivalent max-plus eigenvectors."
    },
    {
      "test": "T42 softmin",
      "status": "PASS",
      "scope": "Exact Hessian refutes convexity."
    },
    {
      "test": "Q40/D9 signs",
      "status": "PASS",
      "scope": "54 commutator cases and an odd-order difference counterexample."
    },
    {
      "test": "I21/I33 entropy corrections",
      "status": "PASS",
      "scope": "Uniform interval translation preserves density; swapped support masses differ."
    },
    {
      "test": "Contraction instruments",
      "status": "PASS",
      "scope": "Exact K^T K=(1/2)I and robust K^T K=(9/16)I certificates."
    },
    {
      "test": "Spectral-radius substitution rejected",
      "status": "PASS",
      "scope": "Nilpotent norm-two map is not a valid failure instrument."
    },
    {
      "test": "Measurement order",
      "status": "PASS",
      "scope": "Two projection orders yield probabilities 1/4 and 1/2."
    },
    {
      "test": "Marginals do not multiply",
      "status": "PASS",
      "scope": "Perfectly correlated half-probability failures remain probability 1/2."
    },
    {
      "test": "QPT staged component bounds",
      "status": "PASS",
      "scope": "Exact minimum-round boundary checks at 32,64,92,128; wrong event substitution remains forbidden."
    },
    {
      "test": "Generalized prefix-box lemma",
      "status": "PASS",
      "scope": "490 prefix counts and 156 maximum-box instances checked exhaustively."
    },
    {
      "test": "Deterministic entropy",
      "status": "PASS",
      "scope": "32 small maps checked; the quantum-side-information extension is proved in the text."
    },
    {
      "test": "Good events and retry tail",
      "status": "PASS",
      "scope": "Tight four-outcome conditioning example; 519/518 exact truncation boundary."
    },
    {
      "test": "Finite-field rank",
      "status": "PASS",
      "scope": "673 matrices enumerated; no seeded-module distribution claim follows."
    },
    {
      "test": "Work/depth and reduction composition",
      "status": "PASS",
      "scope": "Parallel work 37 vs depth 7; affine resource maps composed explicitly."
    },
    {
      "test": "Fixed-hash versus independent oracle",
      "status": "PASS",
      "scope": "Equality test gap is 1-2^-h; no claim about simulator-based indifferentiability."
    },
    {
      "test": "Y1 minimax direction",
      "status": "PASS",
      "scope": "Pure-strategy matching-pennies values give -1<1."
    },
    {
      "test": "H20/R36 counterexamples",
      "status": "PASS",
      "scope": "Two-feature Wasserstein squared cost two; local-reset Schmidt rank decreases."
    },
    {
      "test": "Quorum set intersection",
      "status": "PASS",
      "scope": "441 pairs checked; no signature/authorization premise supplied."
    },
    {
      "test": "Contract negative mutations",
      "status": "PASS",
      "scope": "10 mismatches/missing fields rejected; compatible records never self-certify a theorem."
    }
  ],
  "stages": [
    {
      "query_exponent": 32,
      "ideal_half_rounds": 73,
      "robust_9_16_rounds": 88,
      "robust_bound_log2_display": -4.724671778189133
    },
    {
      "query_exponent": 64,
      "ideal_half_rounds": 137,
      "robust_9_16_rounds": 165,
      "robust_bound_log2_display": -4.640446667131073
    },
    {
      "query_exponent": 92,
      "ideal_half_rounds": 193,
      "robust_9_16_rounds": 233,
      "robust_bound_log2_display": -5.085546569053804
    },
    {
      "query_exponent": 128,
      "ideal_half_rounds": 265,
      "robust_9_16_rounds": 320,
      "robust_bound_log2_display": -5.302071443572686
    }
  ],
  "robust_128_raw_bound_log2_display": -5.302071443572686,
  "full_QPT128_established": false,
  "open_premises": [
    "actual joint relation decoder",
    "public conflict extractor without sidecar",
    "p_star bridge for actual protocol and sampler",
    "concrete signature hardness at reduction resources",
    "compatible signature good-key event and standardized algorithm adapter",
    "deployed-hash game properties",
    "concrete gate/depth/memory accounting"
  ],
  "scope": "Exact arithmetic, finite counterexamples and component-bound checks; no quantum cryptanalysis executed."
}
```

### Standalone reproduction code

Save the following block as `check_operators.py` and run `python3 check_operators.py`. It uses only the Python standard library, writes no external systems, and prints JSON. All threshold decisions are exact; logarithms are display only.

```python
#!/usr/bin/env python3
"""Exact local mathematical checks, not a quantum attack or security proof.

Standalone, Python 3 standard library. Prints its complete summary as JSON.
Probability pass/fail decisions use integers and Fraction, not floating logs.
"""
from fractions import Fraction as F
from itertools import product, combinations
from math import log2
import json

ELL=1<<20
V=2*(ELL*21+1)
TAU=F(1,24)

def joint_raw(s,h,p):
    q=1<<s
    return F((72+40*ELL)*q**3+2*V,1<<h)+20*q*q*p

def log_display(x):
    x=F(x)
    if x<=0: return None
    def logint(n):
        shift=max(0,n.bit_length()-53)
        return log2(n>>shift)+shift
    return logint(x.numerator)-logint(x.denominator)

def minimum_rounds(s,beta,h=512):
    beta=F(beta)
    if not 0<beta<1: raise ValueError('require 0<beta<1')
    if joint_raw(s,h,F(0))>=TAU: return None
    p=F(1); n=0
    while joint_raw(s,h,p)>TAU:
        p*=beta; n+=1
    return n

def digits(x,b,r):
    out=[]
    for _ in range(r):
        x,d=divmod(x,b); out.append(d)
    return tuple(reversed(out))

def prefix_count(R,b,t,r):
    """Count x<R with r base-b digits each in [0,t)."""
    if not (2<=b and 1<=t<b and r>=0 and 0<=R<=b**r):
        raise ValueError('invalid digit parameters')
    if R==b**r: return t**r
    total=0
    for j,d in enumerate(digits(R,b,r)):
        remaining=r-j-1
        total+=min(d,t)*t**remaining
        if d>=t: return total
    return total

def box_mass(h,b,t,r):
    if h<0: raise ValueError('h must be nonnegative')
    a,R=divmod(1<<h,b**r)
    return F(a*t**r+prefix_count(R,b,t,r),1<<h)

def brute_box_mass(h,b,t,r):
    # Independent enumeration of every permitted t-subset in every coordinate.
    subsets=list(combinations(range(b),t))
    residue_counts=[0]*(b**r)
    for u in range(1<<h): residue_counts[u%(b**r)]+=1
    best=0
    for box in product(subsets,repeat=r):
        total=0
        for ds in product(*box):
            x=0
            for d in ds: x=b*x+d
            total+=residue_counts[x]
        best=max(best,total)
    return F(best,1<<h)

def mm(a,b):
    return [[sum((a[i][k]*b[k][j] for k in range(len(b))),F(0))
             for j in range(len(b[0]))] for i in range(len(a))]

def tr(a): return sum((a[i][i] for i in range(len(a))),F(0))
def transpose(a): return [list(x) for x in zip(*a)]
def normsq(v): return sum((x*x for x in v),F(0))
def mv(a,v): return [sum((x*y for x,y in zip(row,v)),F(0)) for row in a]
def eye(a=F(1)): return [[a,F(0)],[F(0),a]]
def sub(a,b): return [[x-y for x,y in zip(u,v)] for u,v in zip(a,b)]
def psd2(a):
    return a==transpose(a) and a[0][0]>=0 and a[1][1]>=0 and a[0][0]*a[1][1]>=a[0][1]**2

def rank_mod(a,q):
    a=[list(row) for row in a]; m=len(a); n=len(a[0]); r=0
    for col in range(n):
        pivot=next((i for i in range(r,m) if a[i][col]%q),None)
        if pivot is None: continue
        a[r],a[pivot]=a[pivot],a[r]
        inv=pow(a[r][col]%q,-1,q)
        a[r]=[(v*inv)%q for v in a[r]]
        for i in range(m):
            if i!=r:
                coef=a[i][col]
                a[i]=[(x-coef*y)%q for x,y in zip(a[i],a[r])]
        r+=1
        if r==m: break
    return r

def rank_count(m,n,r,q):
    if not 0<=r<=min(m,n): return 0
    v=F(1)
    for i in range(r): v*=F((q**m-q**i)*(q**n-q**i),q**r-q**i)
    assert v.denominator==1
    return v.numerator

def dag_cost(nodes):
    """Nodes are already topologically ordered: (name,gates,depth,preds)."""
    depth={}; work=0
    for name,g,d,preds in nodes:
        if min(g,d)<0 or name in depth: raise ValueError('invalid DAG cost')
        depth[name]=d+max((depth[p] for p in preds),default=0)
        work+=g
    return work,max(depth.values(),default=0)

FIELDS=('event','relation','key_distribution','oracle_interface','resources')
def compatible(a,b):
    missing=[f for f in FIELDS if f not in a or f not in b]
    mismatch=[f for f in FIELDS if f in a and f in b and a[f]!=b[f]]
    return {'structurally_compatible':not missing and not mismatch,
            'missing':missing,'mismatch':mismatch,'cryptographic_theorem_verified':False}

def main():
    checks=[]
    def passed(name,detail): checks.append({'test':name,'status':'PASS','scope':detail})

    # 1: exact counterexample to threshold-meet idempotence.
    chain=[F(0),F(1,4),F(1,2),F(1)]
    admissible=[z for z in chain if z<=F(1,4) and z>=F(1,2)]
    result=max(admissible,default=F(0))
    assert result!=F(1,4)
    passed('L1 threshold meet','Finite complete-chain counterexample.')

    p=[F(4,5),F(1,10),F(1,10)]; q=[F(3,5),F(2,5),F(0)]
    upper=[max(a,b) for a,b in zip(p,q)]; lower=[min(a,b) for a,b in zip(p,q)]
    upper=[x/sum(upper) for x in upper]; lower=[x/sum(lower) for x in lower]
    assert upper==[F(8,13),F(4,13),F(1,13)] and upper[0]<p[0]
    assert lower==[F(6,7),F(1,7),F(0)] and lower[0]>p[0]
    passed('L9/L10 majorization','Both normalized envelopes fail at k=1.')

    # Cover/product/order issues are witnessed on finite structures.
    points=list(product(range(2),repeat=2))
    def le(x,y): return all(a<=b for a,b in zip(x,y))
    width=max(len(c) for k in range(5) for c in combinations(points,k)
              if all(not le(x,y) and not le(y,x) for x,y in combinations(c,2)))
    assert width==2 and (0,1)<(1,0) and not 1<=0
    passed('L35/L47 order','Lexicographic second projection fails; product width is two.')

    # Negative diagonal self-loops: trace(A)=-1, trace(A^2)=-2.
    correct=max(F(-1,1),F(-2,2)); source=F(max(-1,-2),2)
    assert correct==F(-1) and source==F(-1,2)
    passed('T7 cycle mean','Maximum of normalized traces differs from normalization after maximum.')

    a=[[0,-1],[-1,0]]
    for x in ([F(0),F(0)],[F(0),F(1,2)]):
        assert [max(F(a[i][j])+x[j] for j in range(2)) for i in range(2)]==x
    passed('T8 eigenvector uniqueness','Two non-translation-equivalent max-plus eigenvectors.')

    # Softmin Hessian at (0,0), beta=1 is negative semidefinite, not positive.
    soft_hessian=[[F(-1,4),F(1,4)],[F(1,4),F(-1,4)]]
    assert not psd2(soft_hessian) and psd2([[-x for x in row] for row in soft_hessian])
    passed('T42 softmin','Exact Hessian refutes convexity.')

    # Jackson commutator on monomials for several rational q,x values.
    qcases=0
    for qv in (F(1,2),F(2),F(3)):
        for x in (F(1,3),F(1),F(2)):
            for n in range(6):
                f=lambda z:z**n
                dq=lambda z:(f(qv*z)-f(z))/((qv-1)*z)
                lhs=(f(qv*qv*x)-f(qv*x))/((qv-1)*x)-dq(qv*x)
                assert lhs==(qv-1)*dq(qv*x)
                qcases+=1
    assert (1-2)==-1  # (I-E)x=-1, while (E-I)x=1.
    passed('Q40/D9 signs',f'{qcases} commutator cases and an odd-order difference counterexample.')

    # Uniform interval has unchanged density after translation; min divergence orientation.
    width_before=F(2)-F(0); width_after=F(9)-F(7)
    assert width_before==width_after and F(1)/width_before==F(1)/width_after
    source_mass=F(1); correct_mass=F(1,2)
    assert source_mass!=correct_mass
    passed('I21/I33 entropy corrections','Uniform interval translation preserves density; swapped support masses differ.')

    # K^T K exactly certifies subnormalized contraction; no state sampling needed.
    k=[[F(1,2),F(1,2)],[F(1,2),F(-1,2)]]
    kt_k=mm(transpose(k),k)
    assert kt_k==eye(F(1,2))
    robust=eye(F(3,4))
    assert mm(transpose(robust),robust)==eye(F(9,16))
    assert psd2(sub(eye(),kt_k))
    passed('Contraction instruments','Exact K^T K=(1/2)I and robust K^T K=(9/16)I certificates.')

    nonnormal=[[F(0),F(2)],[F(0),F(0)]]
    assert mm(nonnormal,nonnormal)==eye(F(0))
    assert normsq(mv(nonnormal,[F(0),F(1)]))==4
    assert not psd2(sub(eye(),mm(transpose(nonnormal),nonnormal)))
    passed('Spectral-radius substitution rejected','Nilpotent norm-two map is not a valid failure instrument.')

    z=[[F(1),F(0)],[F(0),F(0)]]
    plus=[[F(1,2),F(1,2)],[F(1,2),F(1,2)]]
    v0=[F(1),F(0)]
    assert normsq(mv(mm(z,plus),v0))==F(1,4)
    assert normsq(mv(mm(plus,z),v0))==F(1,2)
    passed('Measurement order','Two projection orders yield probabilities 1/4 and 1/2.')

    # Correlated Bernoulli rounds demonstrate the need for conditional bounds.
    joint_bad=F(1,2); marginal_product=F(1,4)
    assert joint_bad>marginal_product
    passed('Marginals do not multiply','Perfectly correlated half-probability failures remain probability 1/2.')

    stages=[]
    for s in (32,64,92,128):
        exact=minimum_rounds(s,F(1,2)); robust_n=minimum_rounds(s,F(9,16))
        for beta,n in ((F(1,2),exact),(F(9,16),robust_n)):
            assert joint_raw(s,512,beta**n)<=TAU
            assert n>0 and joint_raw(s,512,beta**(n-1))>TAU
        stages.append({'query_exponent':s,'ideal_half_rounds':exact,'robust_9_16_rounds':robust_n,
                       'robust_bound_log2_display':log_display(joint_raw(s,512,F(9,16)**robust_n))})
    assert [x['ideal_half_rounds'] for x in stages]==[73,137,193,265]
    assert stages[-1]['robust_9_16_rounds']==320
    assert joint_raw(128,512,F(1,1<<128))>1
    assert joint_raw(128,512,F(9,16)**320)<TAU
    assert minimum_rounds(128,F(1,2),h=256) is None
    passed('QPT staged component bounds','Exact minimum-round boundary checks at 32,64,92,128; wrong event substitution remains forbidden.')

    # Exact source sampler vs independent enumeration, including non-ternary cases.
    boxcases=0; prefixcases=0
    for b in range(2,6):
        for t in range(1,b):
            for r in range(1,4 if b<=4 else 3):
                for R in range(b**r+1):
                    brute=sum(all(d<t for d in digits(x,b,r)) for x in range(R))
                    assert prefix_count(R,b,t,r)==brute
                    prefixcases+=1
                for h in range(1,7):
                    assert box_mass(h,b,t,r)==brute_box_mass(h,b,t,r)
                    boxcases+=1
    assert box_mass(2,3,2,2)==F(3,4)
    assert box_mass(512,3,2,324)==box_mass(512,3,2,512)
    assert joint_raw(128,720,box_mass(720,3,2,454))<=TAU
    passed('Generalized prefix-box lemma',f'{prefixcases} prefix counts and {boxcases} maximum-box instances checked exhaustively.')

    # Unconditional entropy cannot increase through a deterministic classical map.
    maps=0
    for weights in ((1,1,1),(1,2,3),(0,1,5),(5,0,1)):
        for f in product(range(2),repeat=3):
            out=[sum(weights[i] for i in range(3) if f[i]==j) for j in range(2)]
            assert max(out)>=max(weights)
            maps+=1
    passed('Deterministic entropy',f'{maps} small maps checked; the quantum-side-information extension is proved in the text.')

    d1=d2=F(1,4); epsilon=F(1,3)
    conditional=F(1,2)
    assert conditional==epsilon*(1-d1)/(1-d1-d2)
    assert (1-d1-d2)>0
    assert (1<<64)*F(759,1024)**519<=F(1,1<<160)
    assert (1<<64)*F(759,1024)**518>F(1,1<<160)
    passed('Good events and retry tail','Tight four-outcome conditioning example; 519/518 exact truncation boundary.')

    rankcases=0
    for qv,m,n in ((2,2,2),(2,2,3),(2,3,3),(3,2,2)):
        counts=[0]*(min(m,n)+1)
        for flat in product(range(qv),repeat=m*n):
            matrix=[flat[i*n:(i+1)*n] for i in range(m)]
            counts[rank_mod(matrix,qv)]+=1
        assert counts==[rank_count(m,n,r,qv) for r in range(min(m,n)+1)]
        assert sum(counts)==qv**(m*n)
        rankcases+=qv**(m*n)
    passed('Finite-field rank',f'{rankcases} matrices enumerated; no seeded-module distribution claim follows.')

    nodes=[('a',10,3,()),('b',20,5,()),('join',7,2,('a','b'))]
    assert dag_cost(nodes)==(37,7)
    assert 2*128==256 and (lambda t:3*(2*t+1)+4)(10)==67
    passed('Work/depth and reduction composition','Parallel work 37 vs depth 7; affine resource maps composed explicitly.')

    # A fixed publicly computable function is distinguishable from an independent RO.
    # Finite oracle table enumeration on two inputs with four possible outputs.
    matches=sum(table[0]==2 for table in product(range(4),repeat=2))
    assert F(matches,16)==F(1,4)
    assert F(1)-F(matches,16)==F(3,4)
    passed('Fixed-hash versus independent oracle','Equality test gap is 1-2^-h; no claim about simulator-based indifferentiability.')

    game=[[1,-1],[-1,1]]
    minmax=min(max(row) for row in game)
    maxmin=max(min(game[i][j] for i in range(2)) for j in range(2))
    assert maxmin==-1 and minmax==1 and maxmin<minmax
    passed('Y1 minimax direction','Pure-strategy matching-pennies values give -1<1.')

    # Other false source properties use simple exact witnesses.
    pd0=[(0,6),(20,26)]; pd1=[(1,7),(21,27)]
    def diagcost(pt): return F(pt[1]-pt[0],2)**2
    costs=[]
    for assignment in product((-1,0,1),repeat=2):
        used=[j for j in assignment if j!=-1]
        if len(used)!=len(set(used)): continue
        cost=sum((diagcost(pd0[i]) if j==-1 else
                  F(max(abs(x-y) for x,y in zip(pd0[i],pd1[j])))**2)
                 for i,j in enumerate(assignment))
        cost+=sum(diagcost(pd1[j]) for j in range(2) if j not in used)
        costs.append(cost)
    assert min(costs)==2  # W_2=sqrt(2), while bottleneck distance is one.
    # Explicit CPTP local reset on a two-qubit Bell density operator.
    bell=[[F(0) for _ in range(4)] for _ in range(4)]
    for i,j in product((0,3),repeat=2): bell[i][j]=F(1,2)
    output=[[F(0) for _ in range(4)] for _ in range(4)]
    completeness=[[F(0) for _ in range(4)] for _ in range(4)]
    for k0 in range(4):
        e=[[F(0) for _ in range(4)] for _ in range(4)]; e[0][k0]=F(1)
        term=mm(mm(e,bell),transpose(e)); ce=mm(transpose(e),e)
        for i,j in product(range(4),repeat=2):
            output[i][j]+=term[i][j]; completeness[i][j]+=ce[i][j]
    assert output[0][0]==1 and sum(map(sum,output))==1
    assert completeness==[[F(i==j) for j in range(4)] for i in range(4)]
    passed('H20/R36 counterexamples','Two-feature Wasserstein squared cost two; local-reset Schmidt rank decreases.')

    intersectioncases=0
    sets=[set(c) for c in combinations(range(7),5)]
    for a,b in product(sets,repeat=2):
        assert len(a&b)>=5+5-7
        intersectioncases+=1
    passed('Quorum set intersection',f'{intersectioncases} pairs checked; no signature/authorization premise supplied.')

    good=dict(event='bad-box-mass',relation='quorum-v1',key_distribution='uniform-model',
              oracle_interface='QROM-shared',resources='queries<=2^128')
    assert compatible(good,good)['structurally_compatible']
    rejected=0
    for field in FIELDS:
        other=dict(good); other[field]='incompatible'
        assert not compatible(good,other)['structurally_compatible']; rejected+=1
        other=dict(good); del other[field]
        assert not compatible(good,other)['structurally_compatible']; rejected+=1
    assert not compatible(good,good)['cryptographic_theorem_verified']
    passed('Contract negative mutations',f'{rejected} mismatches/missing fields rejected; compatible records never self-certify a theorem.')

    return {'version':'1.33','test_groups_passed':len(checks),'checks':checks,'stages':stages,
            'robust_128_raw_bound_log2_display':log_display(joint_raw(128,512,F(9,16)**320)),
            'full_QPT128_established':False,
            'open_premises':['actual joint relation decoder','public conflict extractor without sidecar',
                'p_star bridge for actual protocol and sampler','concrete signature hardness at reduction resources',
                'compatible signature good-key event and standardized algorithm adapter',
                'deployed-hash game properties','concrete gate/depth/memory accounting'],
            'scope':'Exact arithmetic, finite counterexamples and component-bound checks; no quantum cryptanalysis executed.'}

if __name__=='__main__':
    print(json.dumps(main(),indent=2))
```
