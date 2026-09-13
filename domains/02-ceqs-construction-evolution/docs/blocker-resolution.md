# PQ CE-QS v1.20 — Frozen-registry experiment and corrected conflict theorem

9 September 2026. Research prototype; **the complete target remains unachieved**.

This revision reconciles the three latest reviews with the attached frontier, v1.3–v1.6 documents, and the accumulated v1.7–v1.19 implementation evidence. It makes one construction change concrete: **176 link rows instead of 608, conditional on fixing the registry before sampling fresh domain matrices**. It also corrects the latest addendum's claim that public conflict extraction requires a secret opener.

The new circuit has **9,800,861 gates**, down from **14,988,983**. It uses **4,579,328 packed integer multiplications**, down from **6,957,056**. This is an executed trace circuit, not a cost extrapolation from an unrelated paper. It still contains **zero ML-DSA verification constraints**. Its first verified encoded diagnostic frame is **722,528 bytes**, well above the **32,768-byte** complete-certificate limit.

## 1. Preserve the acceptance contract

The retained v1.18/v1.19 target is 43 distinct authorized seats from an ordered registry of 64. Given two accepted conflicting complete QCs in one configuration and domain, public extraction must identify at least 22 actual double-authorizers. Verification and extraction use the two certificate byte strings and fixed public configuration only. Ordinary signer privacy, independent authorization and tracing secrets, QPT security with an explicit resource model, and distributed production under the stated corruption and network assumptions remain required.

The 28,480-byte proof allowance follows from the **current** 160-byte envelope and 43 96-byte handles. The invariant target is the complete 32,768-byte frame; a new encoding may reallocate its bytes. No secret opener, post-conflict committee response, or separately retrieved witness is introduced here.

The new files use a distinct experimental **TR20** frame. A TR20 proof certifies the trace relation only. It is not a CQ10 quorum certificate and is not accepted by the complete-QC API. Full accepted-QC count remains **zero**.

## 2. Corrections to the three new documents

| Claim or proposal | Resolution |
|---|---|
| Conflict extraction was never specified before the new addendum | Incorrect. The attached frontier §14.5–14.7, v1.3 extraction sections, and later acceptance obligations already address it. Their conditional theorems are not a completed implementation. |
| ZK simulation makes public extraction from two QCs impossible | Incorrect for this construction. The handles are public inputs, and those public inputs contain the extraction equation. See §3. |
| A 22-of-64 secret opener committee meets the original interface | It changes that interface: extraction needs secret shares or a post-conflict service. Public verifiability of an opening does not make its generation publicly computable. |
| TRaccoon identifiable abort gives extraction from two successful aggregate signatures | Not established. The cited paper identifies misbehavior when its signing protocol fails. Its abstract describes interactive abort handling, not the required offline two-signature extraction.[1] |
| Conflict extraction discharges the retry theorem's per-failure blame premise | False. A failed attempt may produce no accepted QC. There is then no conflicting accepted pair for that extractor to process. |
| One identified equivocator satisfies this continuation's target | It weakens the retained requirement of at least 22. |
| The only binding work left is a witness-wiring audit | Incomplete: the native circuit has no ML-DSA verifier to wire. Implementing all message-authorization checks is still necessary in the existing authorization mode. |
| Each ML-DSA verification exceeds the whole 13.9-million-product trace relation | Unsupported by the supplied evidence. Signature witness bytes and field-operation counts do not establish native circuit costs or proof bytes. No such measurement is credited. |
| ML-DSA-65 is inconsistent with the system's 128-bit aspiration | No inherent inconsistency follows. A stronger component may serve a weaker overall target. FIPS 204 gives category 3 and 3,309-byte signatures for ML-DSA-65; category labels do not replace the system's concrete loss analysis.[2] |
| Static commitments are structurally incompatible with CE | Too strong. A commitment alone does not authorize a message; it can still be a useful component of a correctly bound relation. |
| “Online extractable” accountable ring signatures automatically offer public conflict opening | Incorrect inference. The matched Beullens–Katsumata–Pintore paper uses an opener public/secret key. Its knowledge extractor is a security-proof mechanism, not the desired public two-QC algorithm.[3] |

Boneh–Komlo TAPS likewise expressly uses a secret tracing key; its efficient constructions are Schnorr based. It is an accountability reference, not a qualifying PQ public-conflict backend.[4] The proposed C1/C2/C3 choices therefore do not exhaust the viable design space. The earlier independent-authorization signature-of-knowledge direction remains conditional; adopting it would require a new authorization suite and proof, not simply deleting ML-DSA checks.[5]

## 3. The public conflict theorem, stated with its actual premises

Write the rounded linear map as \(F_M(s)\). For seat \(i\), let the certified public handle be

\[
L_i=H_{\rm link}(cfg,d,F_{B_d}(s_i)),\qquad
Z_i=F_{C_d}(s_i)+c_m(i+1),\qquad
c_m=H_{\rm challenge}(cfg,d,m),
\]

where the second equation is in \(\mathbb F_{2^{384}}\); field addition is XOR. The trace registry binds \(F_A(s_i)\) to index \(i\). The **same** index must select the authorization key whose signature verifies on the exact configuration, domain, message and handle. Both handle lists have 43 distinct seats and strictly increasing distinct link values.

**Conditional theorem.** Suppose both complete QCs have valid witnesses for that full relation; each registered trace key has at most one secret opening; different registered openings have different domain link values; and \(c_m\ne c_{m'}\). Publicly matching equal links and computing

\[
i+1=(Z_i+Z_i')/(c_m+c_{m'})
\]

recovers exactly the intersection of the two witness signer sets. Hence it recovers at least \(43+43-64=22\) distinct seats.

**Proof.** Every common seat uses the same registered secret by uniqueness, so its link and mask repeat within the domain. Subtraction cancels the mask and yields the displayed identity. Distinct-seat link uniqueness prevents a false match. Conversely, every matched pair must belong to the same seat. The set-size bound gives 22. The public computation uses neither signature witnesses nor a tracing trapdoor. ∎

**Actual authorization requires more than NP soundness.** To conclude that a recovered honest seat really authorized both messages, require the appropriate joint QPT knowledge-extraction property for the complete relation, plus multi-user chosen-message security of the vote signatures. Existence of a valid signature is not evidence that an adversary obtained it: mathematically, valid signatures exist on messages that an honest signer never approved. The extraction reduction must recover signatures on precisely the signed tuples. Simulation extractability and signing-oracle simulation must be matched to the chosen backend and game; they are not asserted for the native experiment.

A useful whole-game failure decomposition is

\[
\epsilon_{CE}\le\epsilon_{cfg}+\epsilon_{A\text{-uniq}}
+\epsilon_{B\text{-pair}}+\epsilon_{H\text{-link}}
+\epsilon_{H\text{-challenge}}+\epsilon_{joint\text{-extract}}
+\epsilon_{vote\text{-forge}}.
\]

Each symbol denotes the event across the complete experiment, not a single invocation with its repetition factors omitted. This revision supplies exact conditional statistical values for the two matrix terms. It supplies no numeric completion of the computational terms, privacy theorem, or distributed-prover theorem.

**Why the proposed ZK contradiction fails.** A ZK simulator preserves the public statement, including \((L_i,Z_i)\). These inputs can already disclose identities when paired with conflicting inputs. Simulation hides the private witness; it does not erase public-input information. Access to a simulation trapdoor or programmed oracle is also not an ordinary signing capability. No extra opener follows from this argument.

**Transferable evidence.** A completed system can use the two accepted QCs themselves, together with the matched positions, as blame evidence. A public judge verifies both QCs, their common configuration/domain and conflicting messages, then checks the match and field equation. The positions are derivable from the two QCs; they are not a retrieved sidecar. The current trace-only frames cannot serve as that evidence of authorization.

**Avoid a vacuous forensic game.** If at most 21 seats are corrupt and honest seats approve at most one message per domain, two valid 43-seat conflicting certificates already require a security failure. Forensic completeness should therefore quantify over any two accepted conflicting certificates, including executions in which at least 22 seats actually equivocate. Non-framing is a separate game protecting a designated honest non-double-authorizing seat. The ≤21 operational threshold governs consensus safety and liveness; it should not make the accountability test vacuous.

## 4. New result: a fixed-registry bound permits 176 link rows

The earlier 608-row argument made each domain map injective over **every possible trace secret**. That is a sufficient condition. If the registry is already fixed, it suffices to separate the at most 64 secrets to which it is bound. This weaker quantifier permits the following conditional optimization without changing the public handle width.

### 4.1 Required setup order

1. Sample the 608-row registration matrix \(A\) uniformly; register all 64 ordered trace and vote public keys.
2. Freeze exactly one registry. Charge the bad event that \(F_A\) has two secret openings to the existing all-secret uniqueness bound.
3. **After that freeze**, sample fresh independent uniform 176-row \(B_d\) and 48-row \(C_d\) matrices for each configured domain. Publish them as fixed public configuration.
4. Changing registrations requires a new configuration and fresh subsequent matrix sampling. Repeated, selectively retained setup attempts must be accounted for.

The fixture implements this order in one process using OS randomness. It **does not implement a distributed unbiased setup ceremony**. Hashing a registry into a seed is not a proof of the required independence, and a fingerprint alone cannot establish chronology. A production design needs an authenticated immutable freeze and an appropriate randomness/setup model, including QPT adversaries and setup restarts. These are new obligations, not silently inherited properties of the old configuration.

### 4.2 Pairwise rounding bound

Set \(q=2^{16}\), output modulus \(p=256\), and rounding-bin width \(b=q/p=256\). For fixed distinct secrets \(s,t\), classify \(\delta=s-t\) by additive order \(2^k\). For a uniform row \(a\), \(\langle a,\delta\rangle\) is uniform on the subgroup with spacing \(2^{16-k}\). Equality of the two rounded outputs requires this residue to lie within cyclic distance at most \(b\) of zero. Therefore

\[
\Pr[F_a(s)=F_a(t)]\le
\beta_k=\frac{\min(2^k,\,2\lfloor256/2^{16-k}\rfloor+1)}{2^k}
\le\tfrac12,\qquad 1\le k\le16.
\]

The distance condition is deliberately loose and includes boundary residues. It is a necessary condition, so it remains an upper bound despite correlations between the two inner products. Independence across rows gives at most \(2^{-r}\) for a fixed pair and an \(r\)-row matrix.

Conditional on good registration uniqueness and an immutable registry preceding the matrices, the secret openings are fixed independently of the fresh \(B_d\)'s. Union-bound over 2,016 unordered pairs and 1,024 domains:

\[
\epsilon_{B\text{-pair}}\le1024\binom{64}{2}2^{-176}
=63\cdot2^{-161}\approx2^{-155.0227200765}.
\]

This covers maliciously chosen registered secrets as well as honest ones, **provided they are bound before the matrix sampling**. It is not a claim that a 176-row map is injective on the entire secret space. The short-link result must not be applied to registrations chosen after seeing those matrices.

### 4.3 Original exact bound, now explicitly shipped

For one 608-row matrix, the number of nonzero differences of additive order \(2^k\) in \(\mathbb Z_{2^{16}}^{256}\) is

\[
N_k=2^{256k}-2^{256(k-1)}.
\]

Existence of any colliding secret pair implies that its difference satisfies the necessary small-residue condition in every row. Union-bound over differences, not an additional independent enumeration of base secrets:

\[
\epsilon_A\le\sum_{k=1}^{16}N_k\beta_k^{608}.
\]

The old epoch expression was \(1025\epsilon_A\), with log₂ approximately **−148.28706231651813**. The new setup needs that all-secret bound for \(A\) only, then the fixed-pair bound for the domain link matrices:

\[
\epsilon_{\rm new}\le\epsilon_A+1024\binom{64}{2}2^{-176}
\approx2^{-154.88001813344454}.
\]

`PQ_CE_QS_exact_bounds_v1_20.json` contains the complete integer numerator and denominator of each term and total. `bound_audit.py` independently reconstructs the old expression, compares exact fractions, checks all 16 order cases, and checks the rounding argument on an exhaustively enumerated small modulus. **154 named checks pass**, including a check summarizing **992 distinct secret-pair cases**. These are arithmetic checks, not 154 cryptographic security proofs.

Hash collisions, LWR pseudorandomness/hardness, configuration binding, and the randomness ceremony are outside these statistical numbers. A smaller row-exposure count is useful input for a future LWR analysis; it does not establish that analysis.

## 5. Executed circuit and serialization results

The adapter preserves the existing 16-bit secrets, 608-row registration relation, independent ML-DSA public registry, hidden seat range/distinctness checks, 48-byte links and masks, field identity equation, and byte-exact query codec. It changes the link-row count, corresponding SHAKE padding, and configuration/frame domain separation. The native proof protocol is unchanged.

| Trace-only quantity | v1.17 baseline | v1.20 frozen-registry experiment |
|---|---:|---:|
| Registration / link / mask rows per seat | 608 / 608 / 48 | 608 / 176 / 48 |
| Scalar products | 13,914,112 | 9,158,656 |
| Packed integer multiplications | 6,957,056 | 4,579,328 |
| Secret-dependent Keccak permutations | 215 | 86 |
| Native gates | 14,988,983 | 9,800,861 |
| Native internal wires | 22,176,863 | 14,638,877 |
| Allocated committed slots | 33,554,432 | 16,777,216 |
| Private 64-bit input words | 11,051 | 11,051 |
| Public 64-bit handle words | 516 | 516 |
| ML-DSA verifications inside proof | 0 | 0 |
| Full 1,024-domain matrix bytes, derived | 344,244,224 | 117,751,808 |

The private-input accounting requested by the addendum is exactly **43 × (1 seat-index word + 256 secret-coordinate words) = 11,051 words**. It does not count internal circuit wires, private signature witnesses, or prove that the complete relation is implemented. The 43 signature witnesses would add 142,287 raw bytes in the existing authorization mode; raw witness size is not a lower bound on a succinct proof.

The scalar-product saving is exactly \(27/79\), or about **34.18%**. Public link hashing uses two secret-dependent Keccak permutations per seat instead of five. The full-domain matrix totals are arithmetic; the executed fixture contains **one domain**, not 1,024 generated domains.

| New diagnostic sample | Native proof bytes | Encoded TR20 frame bytes | Fresh public verification |
|---|---:|---:|---|
| Case 0 | 863,744 | 722,528 | Accepted trace proof |
| Case 1 | 863,744 | 729,728 | Accepted trace proof |

Both native proofs were generated, encoded, and verified in separate processes. All three temporary private trace-witness files were deleted before the fresh public verification runs. Both verifiers rejected a changed public mask. The expanded native proofs match the original native byte strings exactly.

The evidence checker passes **27 consistency checks** and recovers the **22 expected synthetic trace indices** from the two public handle lists. The fixture separately checks **86 real ML-DSA signatures** on the corresponding messages and handles, and rejects 86 wrong-seat public-key substitutions. These private checks do not put authorization inside either public proof.

The native proof suite retains its earlier 96-bit security label; this experiment makes no QPT-128 qualification. The two producer runs used approximately 13.0 GiB peak RSS under the 20 GiB address-space limit. Timing and path-compression differences between randomized fixtures are observations, not a general performance theorem.

The new first frame retains a 46,080-byte native prefix. With the unchanged codec header and handle envelope, even deleting all query, Merkle-path and terminal material would leave

\[
46,080+16+4,288=50,384>32,768.
\]

This is a hard obstruction for **this retained-prefix layout**. It is not a lower bound for all hash-based proofs or all PQ quorum signatures. It demonstrates why reducing witness work does not automatically solve succinctness. Further query-only compression of this layout cannot reach the target.

The lower-level encoder uses a larger diagnostic limit. That is not a relaxation of the QC cap. A mathematically certified upper bound below the cap could establish a size theorem, but a usable deliverable still requires an implemented accepted frame. A heuristic estimate above the cap does not establish impossibility.

## 6. Keep conflict evidence and abort evidence separate

The interfaces have different inputs and guarantees:

| Interface | Inputs | Needed guarantee |
|---|---|---|
| `ExtractConflict` | Two accepted conflicting complete QCs and fixed public configuration | Return ≥22 actual double-authorizers; no secret opening service |
| `AbortBlame` | Evidence produced by a particular distributed execution | Identify a culpable participant when that execution fails, under its protocol and timing model |

A timeout or aborted attempt may yield zero complete QCs. Consequently, `ExtractConflict` cannot discharge the second interface. The conditional ≤22-attempt result from v1.19 remains conditional on bounded per-failure sound fresh blame, progress of the honest parties, safe retries and ≤21 total corruptions. TRaccoon-IA's protocol-specific result does not automatically transfer to this prover.[1]

Replacing 43 vote verifications with one threshold signature also needs a proof that **the same seats** authorized the message and supplied the trace handles. Validity under a shared group key alone does not establish that equality of signer sets. Identifiable abort supplies no missing same-seat equation.

## 7. What is closed, and what still blocks completion

| Obligation | Status after this revision |
|---|---|
| Public two-challenge identity extraction algebra | Conditional theorem restated correctly; secret opener unnecessary |
| Correct nonvacuous forensic test and separate abort-blame interface | Specified |
| Missing private-word accounting and exact rational uniqueness evidence | Supplied and checked |
| Cheaper link relation under fixed-registration sampling | Derived, implemented and measured; new setup premise remains conditional |
| Full 43-seat message authorization inside the proof | **Open**; native ML-DSA check count remains zero |
| Complete frame ≤32,768 bytes | **Open overall; current experimental layout fails** |
| Concrete QPT loss ledger, LWR exposure analysis and privacy | **Open**; arithmetic bounds do not qualify the whole system |
| Robust collaborative prover with qualified corruption/leakage model | **Open**; all new production is centralized diagnostic work |
| New unbiased post-freeze setup ceremony | **Open** for the optimized branch; not needed by the unchanged older all-secret bound |

The actionable backend task remains a **complete joint authorization-and-trace relation in a proof protocol with a different size profile**, carrying the conditional short-link optimization only if its setup premise is met. In the compatibility mode it must include all 43 ML-DSA verifications. A co-designed signature-of-knowledge authorization mode is a separate suite requiring its own registered independent authorization keys, chosen-message security and collaborative signing protocol. Neither a threshold signature plus unrelated trace proof nor an opener committee is accepted as a shortcut.

No complete compact PQ CE-QS has been produced. The result to carry forward is a checked, cheaper trace construction and a corrected account of what can and cannot be inferred from the proposed literature.

## Sources and reproducibility

Primary sources checked for the new proposals; these are targeted scope checks, not claims to have audited every theorem of every paper:

1. Rafael del Pino et al., *Unmasking TRaccoon*, ePrint 2025/849, revision 2 July 2025. [Primary paper record](https://eprint.iacr.org/2025/849). Identifiable abort upon signing failure.
2. NIST, *FIPS 204*, §4 Tables 1–2. [Standard](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.204.pdf). [Publication page and current errata notice](https://csrc.nist.gov/pubs/fips/204/final). Signature sizes and category framing; no inference of circuit cost.
3. Ward Beullens, Shuichi Katsumata, Federico Pintore, *Group signatures and more from isogenies and lattices: generic, simple, and efficient*, DCC 2023. [Article](https://link.springer.com/article/10.1007/s10623-023-01192-x), [ePrint 2021/1366](https://eprint.iacr.org/2021/1366). Designated opener versus knowledge extraction.
4. Dan Boneh and Chelsea Komlo, *Threshold Signatures with Private Accountability*, ePrint 2022/1636. [Primary record](https://eprint.iacr.org/2022/1636). Secret tracing key and Schnorr-based efficient constructions.
5. Jens Groth and Mary Maller, *Snarky Signatures: Minimal Signatures of Knowledge from Simulation-Extractable SNARKs*, CRYPTO 2017. [Author manuscript](https://discovery.ucl.ac.uk/10039783/1/SESNARKCryptoFinal.pdf). Conceptual extraction requirements; its concrete pairing construction is not a PQ backend.

The review archive preserves every v1.19 member byte for byte, adds the three new input documents, complete exact fractions, the adapter sources, public configurations and trace proofs, execution records, and reproduction scripts. Temporary private trace witnesses are deleted and excluded. The native circuit derives from the already pinned Binius source and the previously reviewed prover-memory changes. The new row bound and its setup-conditioned use are this revision's mathematical derivation, not a theorem attributed to one of the papers above.
