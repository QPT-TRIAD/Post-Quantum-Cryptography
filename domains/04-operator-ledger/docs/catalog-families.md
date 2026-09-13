# What each family of catalogue entries does

The catalogue holds 1,000 named mathematical operators in 20 families of 50. Each family is a
mathematical area. An entry is an operator, functional, transform or construction from that area,
carried with its original signature, definition, claimed property and application context — all
labelled uncertified.

The ledger's second half is almost entirely a negative result: it records why these areas do not by
themselves supply cryptographic theorems, and it names the exact typed adapter each would need. The
adapter is expressed in the family's **parked-entry eligibility question**, which is repeated
verbatim by every parked entry of that family and was extracted here from those entries. That
question is the most useful single line per family: it states, in the ledger's own words, what would
have to be supplied before any entry in the family could count.

An entry that is not parked is *active*: it is a member of one or more of the 28 typed contracts
`A01`–`A28`, and its own `QPT-128 substitution` field names those contracts. Membership is a
proposed use, not an established one (line 331).

Line ranges are for `operator-ledger.md` in the parent directory. "Amended" counts entries carrying
an `Amendment (LABEL)` paragraph; amended and active overlap (35 entries are both). Parked is always
`50 − active`.

## Summary

| Family | Lines | Area | Active | Amended | Parked |
|---|---|---|---:|---:|---:|
| L | 788–1721 | Lattice and order | 17 | 16 | 33 |
| T | 1722–2639 | Tropical and idempotent algebra | 8 | 8 | 42 |
| F | 2640–3555 | Fractional calculus | 5 | 7 | 45 |
| Q | 3556–4473 | q-deformed operators | 6 | 8 | 44 |
| D | 4474–5389 | Discrete difference calculus | 6 | 7 | 44 |
| I | 5390–6307 | Information theory | 18 | 8 | 32 |
| P | 6308–7225 | Paths and loops | 3 | 8 | 47 |
| S | 7226–8141 | Spectral operators | 18 | 7 | 32 |
| M | 8142–9057 | Probability and measure | 18 | 7 | 32 |
| C | 9058–9971 | Combinatorics and generating functions | 11 | 6 | 39 |
| H | 9972–10879 | Topology and homology | 1 | 3 | 49 |
| K | 10880–11787 | Category theory | 11 | 3 | 39 |
| N | 11788–12693 | Noncommutative algebra | 1 | 2 | 49 |
| X | 12694–13601 | Stochastic calculus | 2 | 3 | 48 |
| G | 13602–14503 | Geometry and Lie/Clifford operators | 1 | 0 | 49 |
| R | 14504–15423 | Quantum resource theory | 12 | 9 | 38 |
| O | 15424–16335 | Logic and verification | 21 | 5 | 29 |
| W | 16336–17241 | Multiscale transforms | 10 | 2 | 40 |
| Y | 17242–18153 | Games and decisions | 8 | 5 | 42 |
| Z | 18154–19059 | Hybrid constructions | 5 | 2 | 45 |

Active entries concentrate where the ledger found something to say. O (logic and verification) is
the most active family at 21, but mostly through `A23`, the validation-discipline contract, which
is a methodological rule and carries no claim. I (information theory), M (probability and measure)
and S (spectral operators) follow at 18 each, feeding the entropy, composition and contraction
contracts respectively. H, N and G have one active entry each, and none of the three is a proof
obligation the family itself supplies.

## The families

### L — Lattice and order (17 active, 16 amended)

Parked template (33 entries, first at 884): *Can this order construction compare already proved
probability/resource bounds without changing their event or reversing an inequality?*

The most worked family, because the contracts are built out of order-theoretic notions. L1 (a
θ-threshold meet) is the first entry in the file and the ledger's first correction: the source
claimed idempotence, and the counterexample `x = 1/4`, `ν(z) = z`, `θ = 1/2` gives bottom, not `x`.
L9 and L10 carry the majorization counterexample that forced contract `A02` away from normalized
envelopes and back to unnormalized event-wise union bounds. L47 (widths do not multiply) feeds the
work/depth accounting of `A04`. L25, L32–L34 and the `O` and `Y` entries routed with them form
`A24`, the quorum-intersection contract.

### T — Tropical and idempotent algebra (8 active, 8 amended)

Parked template (42 entries, first at 1830): *Can this tropical operation be interpreted on a finite,
costed circuit or reduction graph, with work and depth kept distinct?*

The tropical family is the ledger's source of resource-composition language: `A04` (work versus
depth) is built on T1–T5 and T37, and the mutation replaces tropical path operators with an explicit
finite circuit DAG with nonnegative gate costs. T8's max-plus eigenvector claim is corrected by
`A=[[0,−1],[−1,0]]`, which has two non-translation-equivalent eigenvectors; that counterexample is
reused by `A09` against spectral shortcuts. T42 (a softmin whose exact Hessian is negative
semidefinite, not positive) is a convexity claim that fails at the second derivative.

### F — Fractional calculus (5 active, 7 amended)

Parked template (45 entries, first at 2658): *Can this analytic operator be replaced by a finite
failure instrument with a uniform norm certificate and a charged discretization/tail error?*

The smallest active set relative to its size, and deliberately so: every member is routed to `A27`
("Do not turn smoothing into a security assumption"). Four amendments carry the reason. F8 fixes a
generator sign to `−(−Δ)^{α/2}`. F21 and F44 record that exponential decay or tempering is not
finite memory, and that any truncation must be charged. F47 shows that `E_α(t^α A)` is not a
semigroup for `α ≠ 1`, with `A = 0` as the counterexample. The family is the clearest case in the
catalogue of an appealing analogy that the ledger refuses.

### Q — q-deformed operators (6 active, 8 amended)

Parked template (44 entries, first at 3594): *Which concrete finite counting identity or recurrence
does this q-operator prove for the actual sampler or key distribution, with q and its domain fixed?*

`A05` ("give the shrink recurrence a measurable meaning") is built on Q1, Q3, Q10, Q11 and Q40. The
family's most useful contribution is Q40, whose commutator identity `[D_q, σ_q] = (q−1) σ_q D_q`
resolves a question mark in the source definition, and whose Jackson-derivative identity is the one
piece of this family the checker computes — 54 rational `(q, x, n)` cases. This is also the family
where the ledger's target is stated most bluntly: Q3's eligibility question asks why 128 halvings
are insufficient when the reduction multiplies their probability by `20Q²`.

### D — Discrete difference calculus (6 active, 7 amended)

Parked template (44 entries, first at 4510): *Can this discrete identity certify a recurrence, exact
count or stopping boundary used by a named security inequality?*

Routed to `A05` (D1, D7, D30, D46, D48) and `A11` (D19). D9's amendment corrects the binomial
series sign: at integer `n`, `(I − E)^α` gives `(−1)^n (E − I)^n`. The checker's assertion for D9 is
`assert (1-2)==-1`, which restates the correction rather than computing it — see
`checker-and-what-it-verifies.md`.

### I — Information theory (18 active, 8 amended)

Parked template (32 entries, first at 5448): *Does this information quantity control the required
guessing or distinguishing game with quantum side information, rather than an unrelated average
statistic?*

The second-largest active family, routed to `A14` (entropy), `A12` (encoding), `A20` (deployed hash),
`A25` (extraction), `A02` and `A16`. The amendments are the family's real content: I1 and I2 restrict
nonnegative entropy to discrete masses and to log base 2; I21 records that differential entropy is
translation invariant; I33 reverses a Kullback–Leibler argument to `D_0(P‖Q) = −log Q(supp P)`. The
distinction the family exists to enforce is between a quantity that bounds a cryptographic guessing
game and a quantity that merely looks like one.

### P — Paths and loops (3 active, 8 amended)

Parked template (47 entries, first at 6326): *Is there an explicit finite transcript/state evolution
represented by this path operator, and what map preserves the required security event?*

Only P9 and P14 (to `A18`, the decoder interface) and P17 (to `A19`) are active. P17's amendment is
the family's most quotable line and the catalogue's sharpest rejection of name-based analogy: **"A
rough-path signature is not an authentication signature."** The amendment still routes P17 to `A19`,
which is a public-conflict-extraction obligation, so the entry is active despite the rejection — a
good example of why membership must not be read as a use.

### S — Spectral operators (18 active, 8 amended)

Parked template (32 entries, first at 7244): *Can this operator provide a certified bound for the
full finite failure map, including residuals and the conversion to physical probability?*

Routed to `A06` and `A07` (contraction certificates), `A09` (spectral shortcuts), `A10`
(measurement), `A15` (rank) and `A21` (hash parameters). The amendments all point the same way: a
spectral quantity is not a norm bound. S16 corrects the polar factor to a partial isometry rather
than a unitary; S20 gives a dimension `n−k+1` where the source said codimension; S21 and S22 record
that a truncated Krylov method returns Ritz values and that the Arnoldi residual must be retained;
S36 fixes a Stieltjes sign. `A09`'s counterexample `K = [[0,2],[0,0]]` — spectral radius 0, norm 2 —
is the summary.

### M — Probability and measure (18 active, 8 amended)

Parked template (32 entries, first at 8198): *Are the conditioning, dependence, support and tail
assumptions needed by this probabilistic operator true in the exact cryptographic experiment?*

The most directly load-bearing family for the ledger's composition contracts: `A02`, `A08`, `A13`,
`A16` and `A26` all draw on it. The amendments are mostly about which of several plausible identities
is the true one: M3 gives `Var(X+Y) = Var X + Var Y` exactly under independence and with a
covariance term otherwise; M8 fixes a cumulant Taylor coefficient to `κ_n/n!`; M25 records that a
coupling output is a set; M33 corrects a disintegration direction; M41 records that
Glivenko–Cantelli is about CDFs and that the empirical-to-continuous total-variation distance is 1.
`A26`'s rule follows: observing zero failures is not evidence of a `2^-128` bound without a
justified statistical model and sample size.

### C — Combinatorics and generating functions (11 active, 6 amended)

Parked template (39 entries, first at 9094): *Can this counting operator enumerate the actual finite
bad-set or key-distribution object, with an independent coefficient/count check?*

Routed to `A11` (challenge mass), `A12`, `A13`, `A15` and `A19`. C45 and C47 matter for `A15`: the
Smith normal form over a PID is neither a real SVD nor finite-field elimination, and the Euler
transform was missing its `x^k` factors. C16, C27 and C44 complete the amended set. The family's
checker evidence is the prefix-box group, which enumerates 490 exact prefix counts and 156 box
masses; that evidence is attached to C48 and C49.

### H — Topology and homology (1 active, 3 amended)

Parked template (49 entries, first at 9990): *What explicit finite reduction connects this
topological invariant to the quorum relation or a quantified hardness game? Without one, why would
it affect QPT-128?*

H7 and H8 amend the same gap: the interval decomposition of a persistence module requires
pointwise finite-dimensional one-parameter modules over a field, and general abelian-group-valued
persistence modules have no such barcode classification. H20 corrects a stability claim — the
unit-Lipschitz bound is for bottleneck distance, and finite-`p` Wasserstein distance carries a
feature-count factor `N^{1/p}ε` — and is one of the three amendments in the whole second half with a
genuine executable witness. Only H38 is active, routed to `A19` because a reduction reads a
compressed-oracle database that a public trace cannot.

### K — Category theory (11 active, 3 amended)

Parked template (39 entries, first at 10898): *Can this categorical construction be instantiated as
typed algorithms between the exact games, with a proved adapter and a concrete resource map?*

The active set is large relative to the family's content because categorical language maps neatly
onto the ledger's own composition obligation: K29 (good-event glue and the final compatibility
record), K31 and K32 (encoding and the joint decoder), K33/K34 (interfaces), K50 (the fixed hash),
K20/K47 (resource inflation), and K9/K14/K17 (the signature contract and the measurement order).
The three amendments are ADJACENT errors rather than deep ones: K11 reverses an adjunction (the free
Eilenberg–Moore algebra functor is left adjoint, not right), K39 overstates `Ind(C)` as automatically
cocomplete, and K46 leaves unspecified which argument of `Hom` varies. K40 carries the parallel
defect that K39's amendment did not reach.

### N — Noncommutative algebra (1 active, 2 amended)

Parked template (49 entries, first at 11806): *Can this noncommutative construction be realized on
finite quantum registers with explicit positive maps and a proved operational probability bound?*

N25 corrects normal ordering (contraction terms belong to the expansion, not to the normally ordered
monomial) and N38 corrects the Poincaré–Birkhoff–Witt claim: the PBW monomials are a vector-space
basis, not a free associative algebra on the generators. Only N19 is active, routed to `A10`.

### X — Stochastic calculus (2 active, 3 amended)

Parked template (48 entries, first at 12712): *Can this continuous stochastic result be given a
finite algorithmic realization with uniform adversarial conditioning and explicit approximation/tail
costs?*

X12, X13 and X28 all record the same restriction from different angles: the displayed
quadratic-variation and Itô formulas hold for continuous semimartingales, general jump processes
need jump terms, and a stochastic exponential of a continuous local martingale is a local martingale
unless an integrability condition is added. X4 and X35 are active, and both go to methodological
contracts (`A27`, `A26`) rather than to a proof obligation — the one shared with F.

### G — Geometry and Lie/Clifford operators (1 active, 0 amended)

Parked template (49 entries, first at 13638): *Which finite-dimensional cryptographic object does
this geometric operator act on, and what event-preserving reduction connects its invariant to
security?*

The only family with no amendment at all. None of its 50 entries was found to state something
false; none was found to state something usable either. The single active entry, G1, is routed to
`A10` for the measurement-order question. This is the family that most cleanly shows the ledger's
negative mode: 49 entries parked without a single claim to correct. G44's Bott property is flagged
in the reading record as apparently false at `k = n = 2` and is left unamended.

### R — Quantum resource theory (12 active, 9 amended)

Parked template (38 entries, first at 14524): *Is the free-operation class used by this resource
operator the actual adversary class, and does the monotone bound the stated success or cost
quantity?*

The most amended family after L (9 amendments), and fourth by active count. `A22` (resource
inflation) is built largely here, with R33–R35, R41 and R42; R7 and R27 go to extraction; R12 and
R13 to hash parameters; R26 to entropy. The nine amendments are mostly normalization and
sign errors with real consequences for cost claims: R1 (majorization is a preorder on unsorted
vectors, and the uniform vector is majorized *by* every other), R2 and R3 (Lorenz curve
interpolation and the Gini sign convention), R12 and R13 (a distillation rate of `m/n` for `m` Bell
pairs, and `log₂(m)/n` only when `m` is a dimension), R18 (a free-energy sign), R22, R36 and R46.
R36's correction — Schmidt rank is invariant under local unitaries but **can decrease** under LOCC,
by resetting both parties locally — is the second of the second half's three genuinely witnessed
amendments, and uses exactly the LOCC-reset construction that the source had ruled out.

### O — Logic and verification (21 active, 5 amended)

Parked template (29 entries, first at 15442): *Can this logical operator produce a checkable
statement about the exact typed relation and quantifiers, rather than merely label a missing
premise?*

The largest active family, and the least claim-bearing: most of its 21 active entries route to
`A23`, which is the ledger's own validation rule — keep arithmetic tests, finite-model proofs,
literature theorems and unproved protocol assumptions as separate statuses, and do not read a green
eligibility flag as a cryptographic proof. The five amendments are ordinary errors: O9 and O10 (a
linear-logic sequent rule conflating a context with a tensor connective; O10 reuses O9's text
verbatim and states no par-specific rule), O11 (a comonad direction), O39 (data complexity versus
combined complexity in Datalog), O49 (linear logic removes weakening *and* contraction, not
contraction alone). `A23` is what makes the rest of this domain readable: it is the rule that says a
finite check is a proof aid with an explicit scope.

### W — Multiscale transforms (10 active, 2 amended)

Parked template (40 entries, first at 16354): *Does this transform preserve the information and
event needed by verification/extraction, with all discarded coefficients, seeds and costs
accounted for?*

Active entries route to `A07` (robust contraction, via W19 and W49), `A14`, `A21`, `A06` and `A27`.
Only W5 and W43 are amended: W5 corrects a multiresolution analysis (the union of the subspaces is
dense in `L²`, not literally equal to it) and W43 corrects a name (the displayed flow with an
inverse Hessian and a regulator is the Wetterich equation, not Polchinski's). The family's main
contribution is a question asked repeatedly — whether an operator improves the conditional guessing
probability or only a Shannon-entropy or visual statistic.

### Y — Games and decisions (8 active, 5 amended)

Parked template (42 entries, first at 17300): *Does this game result bound every admissible adversary
or only rational/equilibrium behavior, and is there a valid bridge to the cryptographic quantifiers?*

Y1 and Y2 correct the minimax direction: `sup_y inf_x u ≤ inf_x sup_y u`, with equality requiring a
minimax theorem and mixed strategies. Y1's correction is the third and last of the second half's
genuinely witnessed amendments — the checker computes the matching-pennies values `−1` and `1`.
Y5 restores the recommendation-conditioned weights in the correlated-equilibrium constraint; Y21
corrects a best-response dynamic to use the sum of positive excesses rather than the positive part
of the sum; Y30 restricts a termination claim to finite exact potential games under strict
unilateral improvement. The family exists in the ledger mainly to be disqualified: `A24`'s contract
states flatly that "Economic equilibria do not supply authorization" (717).

### Z — Hybrid constructions (5 active, 2 amended, 50 hybrid-flagged)

Parked template (45 entries, first at 18172): *Can the proposed fusion supply typed input/output
algorithms, a proved invariant and a composable resource bound, rather than just names from two
fields?*

Every Z entry carries the hybrid flag, because every Z entry is a combination of two earlier
families — and the flag's meaning is exactly that a hybrid name is not a composition proof. Z35
("topological cryptography") is the family's headline rejection: a topological invariant is not a
post-quantum signature construction or a hardness reduction, and the entry is replaced by a
protocol contract (`UNSUPPORTED_SECURITY`). Z50, the "master operator", is rejected as
`UNDEFINED_COMPOSITION` — a tuple of structures does not define a functor or a security theorem —
and replaced by `A28`'s typed proof-obligation record whose composition is refused on incompatible
games, distributions, oracle access or resource bounds.

The Z family also carries 98 historical cross-references of the form `[F<family>.<entry>]`, all
resolved by document order (1 = L … 20 = Z). Z29 confirms the mapping by naming its targets. The
ledger itself warns that these "may point to the wrong mathematical operation" (22), and several do;
the reading record's resolution table is the authority for which.

## Reading a family block

To read one family in `operator-ledger.md`, use the line range from the summary table above. Within
a family the entries are consecutive, each beginning `#### <ID>. \`symbol\` — name` and ending with
its eligibility question. The parked entries of a family are near-identical apart from their source
fields, so the efficient read is: the family heading, one parked entry, then every entry whose
disposition carries `ACTIVE`, `SPECIFIC AMENDMENT` or `HYBRID NAME IS NOT A COMPOSITION PROOF`. A
`grep -n '^#### ' | grep -E '^\S+:#### (L|T|...)N\.'` over the file locates them.
