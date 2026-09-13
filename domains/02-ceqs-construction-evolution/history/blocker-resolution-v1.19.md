# PQ CE-QS v1.19 — corrected binding, pool sizing and security-budget decisions

Date: **9 September 2026**. Reviewed input: *Pasted markdown(20260909-110038).md*, the adversarial alternative-strategy companion to v1.18.

## Result

The new document was read in full and checked against the existing source, recorded circuit measurements and relevant primary papers. This revision resolves several of its design questions, supplies an exact relation inventory, and derives a conditional retry bound. **It does not complete compact PQ CE-QS: no new full QCs were generated, no new proof backend was implemented, and no distributed prover was executed.**

The most consequential result is that **a 46–50-person candidate pool does not tolerate 21 arbitrary withholding validators while guaranteeing 43 contributions**. The safe unfiltered eligibility pool is all 64. Smaller pools require additional justified information or a different, proved recovery protocol.

The binding review also narrows the next implementation task. The existing v1.10 private relation already couples authorization and tracing through one seat index and signs the individual handle. The native trace proof omits authorization. A new registration commitment does not substitute for adding that missing in-proof check.

| Item reviewed | Disposition |
|---|---|
| Registration commitment as a replacement for authorization/trace computation | Reject that cost-saving inference; retain as optional registration architecture only. |
| A 46–50-person unfiltered pool guaranteeing 43 usable inputs | Rejected by exact worst-case arithmetic. |
| A retry bound | At most **22 attempts**, conditional on fresh sound fault identification for every failed attempt and stable delivery/timeouts. |
| An oversized conservative upper estimate proving impossibility | Incorrect; only an applicable lower bound or an actual oversized measurement establishes the corresponding failure. |
| Treating quantum collision resistance as Grover preimage resistance | Incorrect; the events have different query exponents. |
| Treating statistical quantum lifting as automatic adaptive-corruption security | Not supported by the examined theorem/model. |
| Complete compactness, QPT security and collaborative production | Remain open. |

## 1. Authorization binding: retain the existing shared seat

In `ce_qs_relation_v1_10.py`, `check_private_contribution` uses the same `witness.index` to select both `trace_public_keys` and `vote_public_keys`. It derives the handle from that index and the trace secret, then verifies the vote signature on the actual handle. The signed message includes configuration, domain, message and individual handle. Configuration fingerprinting covers the ordered trace registry and ordered vote registry.

Thus the private relation specification already enforces:

\[
\operatorname{TraceKeyRel}(tk_i,s_i)\land
\operatorname{HandleRel}(i,s_i,d,m,h_i)\land
\operatorname{VerifyVote}(pk_i,\operatorname{VoteBytes}(cfg,d,m,h_i),\sigma_i).
\]

The quorum wrapper additionally enforces exactly 43 distinct indices and agreement with the canonical public handle list. These are private-witness computations. They do not constitute a public zero-knowledge proof. The v1.17 native circuit is explicitly trace-only and contains zero ML-DSA verification constraints.

The next authorization task is therefore **porting this existing complete condition into the selected proof backend**, preserving the shared index, rather than designing a new relationship between the two registries from scratch.

### What a registration commitment establishes

Let the registered tuple be \(R_i=(pk_i,tk_i)\). Publishing \(C_i=\operatorname{Commit}(R_i;r_i)\) can bind a subsequently opened tuple to a registration, under the commitment's applicable binding property. It does not establish that the holder authorized a future message or that a future handle was computed correctly.

The document's own proposed per-QC relation still includes all three checks:

\[
\operatorname{Open}(C_i,pk_i,tk_i;r_i)\land
\operatorname{VerifyVote}(pk_i,\operatorname{VoteBytes}(cfg,d,m,h_i),\sigma_i)
\land\operatorname{HandleRel}(tk_i,s_i,d,m,h_i).
\]

Both subrelations must consume the same opened values in the current proof. The commitment cannot enforce this equality once at registration and then dispense with consistent witness use in later proofs. Opening public key material is not a fresh vote authorization.

A commitment or authenticated data structure may reduce a particular implementation's static membership or registration-validation costs. That would require a comparison with the actual existing lookup, using the exact backend. Here there are only 64 fixed rows, their ordering is already configuration-bound, and the expensive message-specific relations remain. No saving is credited until such a comparison is available.

The document's discussion of a mix-and-match construction identifies a logical insufficiency in two unbound existential statements. Public key material alone does not generate accepting proofs or 43 valid authorizations. We neither demonstrated a forgery against the existing implementation nor inferred one from that sketch.

**Decision:** keep the shared-index relation as the reference. A future commitment-based variant must prove the same message-specific conditions and demonstrate an actual advantage. Proof-of-possession and rogue-registration defenses must match the chosen registration and aggregation model; their necessity is not established merely by adding the word commitment.

## 2. Relation inventory: what the proposed changes leave to prove

The inventory below combines direct source inspection with the previously recorded v1.17 circuit statistics. It is **not an estimate of lattice R1CS size**.

| Quantity | Exact value / status |
|---|---:|
| Hidden selected seats | 43 |
| Trace secret coordinates per seat | 256 |
| Registration / link / mask rows per seat | 608 / 608 / 48 |
| Mathematical scalar products across those matrices | 13,914,112 |
| Packed native integer multiplications | 6,957,056 |
| Private 64-bit input words | 11,051 |
| Public 64-bit handle words | 516 |
| Explicit pairwise distinctness checks | 903 |
| Secret-dependent Keccak permutations in the native trace circuit | 215 |
| Recorded native internal wires | 22,176,863 |
| ML-DSA verifications required for the current authorization mode | 43 |
| ML-DSA verifications present in the native trace proof | **0** |
| ML-DSA signature witness bytes before proof encoding | 142,287 |
| Additional commitment-opening checks in the proposed per-seat variant | 43 |
| Complete lattice relation size and proof bytes | **Unknown** |

The multiplication count follows directly from

\[
43(608+608+48)256=13,914,112.
\]

The native implementation packs two matrix rows per multiplication, giving exactly half that count. The trace hash code performs five secret-dependent Keccak permutations per seat; an initial public prefix permutation is precomputed. The inventory is tied to the supplied implementation, not a lower bound for every equivalent arithmetic circuit.

Signature witness bytes are not transmitted QC bytes and do not imply a proof-size lower bound. Similarly, 11,051 input words are not the full arithmetic witness length after all intermediate computations. Neither figure can be substituted into an unrelated proof-size graph.

The existing trace circuit already proves all 43 contributions in one native proof. A proposed batch optimization must identify which equations, openings or commitments it actually removes or amortizes. It cannot start by assuming that the current system sends 43 separate full proofs.

**Decision:** the document's “a few thousand constraints per seat” possibility remains unestablished for the exact relation. The recorded workload provides a concrete reference, while a lattice port needs its own field, range, hash, membership, authorization and norm inventory.

## 3. Candidate pools: exact worst-case and random-selection calculations

Let \(n=64\), \(f=21\), and let a QC require \(q=43\) usable authorized contributions. A candidate pool of size \(k\) may contain all 21 Byzantine validators. If they withhold, the guaranteed honest count is only

\[
H_{\min}(k)=k-21.
\]

Consequently, guaranteeing 43 honest candidates without further information requires \(k\ge64\). A declaration of willingness in phase 1 does not prevent a Byzantine validator from withholding in phase 2.

For an illustrative probability calculation, assume exactly 21 **fixed** Byzantine identities, a uniformly random pool without replacement, all honest validators willing to authorize the same vote, and every Byzantine validator withholding. Success requires the pool to contain all 43 honest identities:

\[
\Pr[H\ge43]=\frac{\binom{21}{k-43}}{\binom{64}{k}}.
\]

| Pool size | Worst-case honest candidates | Withholding faults tolerable while retaining 43 | Uniform-pool probability of containing all 43 honest |
|---|---:|---:|---:|
| 46 | 25 | 3 | 3.692712161 × 10⁻¹³ |
| 48 | 27 | 5 | 4.165379318 × 10⁻¹¹ |
| 50 | 29 | 7 | 2.429804602 × 10⁻⁹ |
| 60 | 39 | 17 | 0.009419619249 |
| 63 | 42 | 20 | 0.328125 |
| 64 | 43 | 21 | 1 |

For 50 candidates, the exact probability is \(5/2,057,778,636\). These probabilities are a model calculation, not a measured network result or an estimate against adaptive selection/corruption. Adversarially biased candidate selection has no such uniform-sampling guarantee.

The chance can improve if corrupt validators cooperate, fewer than 21 are faulty, or the system has useful prior information. None of those is a worst-case liveness guarantee under the stated contract. Independently resampling small pools also does not yield a deterministic bounded retry count.

### When smaller pools become justified

After \(b\) distinct Byzantine identities have been **soundly identified and excluded**, the remaining fault budget is at most \(21-b\). A sufficient worst-case candidate count becomes

\[
k\ge43+(21-b)=64-b.
\]

Thus a 50-person pool is justified by this argument only after at least 14 certified faulty exclusions; a 46-person pool needs at least 18. This does not apply to exclusions based merely on silence or suspicion. It also assumes a total corruption budget, not a mobile adversary able to corrupt fresh identities indefinitely.

**Decision:** keep all non-excluded eligible validators available for recovery. A smaller active proving set is an optimization requiring a real fault-handling mechanism; it is not the fault-tolerance basis.

## 4. A precise conditional retry theorem

Assume all of the following hold during a stable delivery and timeout regime:

1. At least 43 never-corrupted validators have valid private inputs and authorize the same required vote; consensus agreement on that vote is supplied separately.
2. Each attempt completes within a stated bound and returns either a valid complete QC or a **sound certificate identifying at least one previously unexcluded Byzantine identity** responsible for failure.
3. Honest validators are never permanently excluded, and every exclusion reduces the remaining total fault budget by at least one.
4. A replacement attempt can use the remaining eligible inputs without invalid reuse of session-bound shares, nonces or proof randomness. Necessary restart, resharing or recovery is included in its cost.
5. At most 21 identities are corrupted in total for this analysis; successful proof generation has the declared completeness behavior.

Then there are at most **21 blame-producing failures and 22 total attempts** before success, apart from any separately bounded completeness or subprotocol-failure events.

**Proof.** Use the potential \(\Phi=21-b\), where \(b\) is the number of distinct soundly excluded faulty identities. Each failed attempt decreases \(\Phi\) by at least one. All 43 never-corrupted approving validators remain. After at most 21 such failures, no additional blame-producing failure is possible; by assumption the next bounded attempt succeeds. No independence between attempts is used.

This is an application-level theorem conditional on a concrete subprotocol interface. The included model checks that potential argument and its longest deterministic path for every fault count from 0 through 21. The model's fault certificates are ideal assumptions, **not implemented cryptographic evidence**.

If every stable attempt, including agreement, private input handling, proving, delivery and fault identification, costs at most \(T\), the conditional bound is \(22T\). That is not a claim about the time to reach synchrony, and it does not force the adversary to abort cheaply. Every malicious failure can still occur near the end of an expensive proving attempt.

A timeout does not establish culpability before message-delay bounds apply. A lack of output also does not by itself identify which participant is at fault. Timeouts may trigger a retry or a view change under a proved protocol; they must not silently become permanent fault certificates. The document's phase split alone proves neither cheap recovery nor the second assumption above.

Unmasking TRaccoon demonstrates identifiable-abort machinery for its particular threshold signature. Transferring that guarantee to a different collaborative proof protocol requires a new protocol and proof; it cannot be inferred from its interface name.[^5]

### Separate computing parties from selected signers

An alternative architectural reference is to use all 64 validators as computing parties, privately validate their inputs and select 43 authorized contributions inside a robust computation. The numerical inequality \(64>3\cdot21\) matches the classical honest-majority threshold for Byzantine-resilient general MPC in BGW. A 43-party computing committee containing 21 faulty members does not satisfy that threshold.[^1]

This is an existence-oriented reference, not an implemented PQ collaborative prover. The secure channels, broadcast or agreement layer, input-selection functionality, output delivery, corruption model and actual proof-generation computation still need qualification. The earlier private 64-input filter is a functional oracle, not a distributed execution.

If an external observer learns an exact 43-member active set and the protocol requires every one of them to authorize, that metadata reveals the signer set regardless of the QC's zero knowledge. A full-pool computation can separate computing membership from hidden signer selection, but the exact leakage policy must still cover traffic, candidate lists, blame and retries.

## 5. Correct the size gate before applying it to another backend

The attachment correctly retains the measured native-prefix obstacle, but then generalizes it too far. The floor of 50,496 bytes applies to the measured format with the 46,192-byte prefix retained, its 16-byte codec header and its 4,288-byte envelope. It is not a lower bound on every hash-based IOP or on the complete hash-proof family. SmallWood's different small-instance regime is one reason not to infer such a universal claim; it does not itself establish that our relation fits.[^4]

There is a second logical distinction in the proposed falsification gate. If a conservative estimate is an **upper bound** \(U\) and \(U>28,480\), that does not prove the actual proof exceeds 28,480. An upper bound may be loose. One can choose to stop that engineering branch for cost reasons, but should label that choice accordingly.

| Evidence about a complete serialized frame | Permitted conclusion |
|---|---|
| Certified mandatory lower bound exceeds 32,768 bytes | That parameterization/format is ruled out. |
| Actual complete frame exceeds 32,768 bytes | That measured frame fails the size target. |
| Conservative upper estimate exceeds the cap | Size remains unresolved; engineering may defer the branch. |
| Favorable upper estimate lies within the cap | Proceed to exact implementation/measurement and validate the estimate's assumptions. |
| A component fits but the complete relation is missing | Full-QC compactness remains unresolved. |
| Complete measured frame fits | The size gate passes for that measurement; the independent security gates remain. |

The new executable gate enforces those distinctions, including the case where a loose 60,000-byte upper estimate must not be reported as a proved impossibility. The original 28,480-byte proof allowance still applies only when the current 4,288-byte envelope is retained. New commitments, finalizers, tags or openings must be counted exactly once, in the field where they are actually serialized.

No scaling curve was supplied for the proposed lattice relation. Extrapolating from a 58 KB unrelated R1CS benchmark using an assumed square-root or logarithmic law cannot fill that gap. The choice of a lattice backend remains a candidate experiment, with no credited byte saving from registration commitments or batching yet.

## 6. Security-loss ledger: numbers where justified, unknowns where necessary

`PQ_CE_QS_security_loss_ledger_v1_19.json` records eight required obligation groups, available statistical arithmetic and an explicitly illustrative budget calculation. **No required group is fully qualified.** Unknown reductions and resource bounds are represented as unknown; the administrative gate rejects an unpinned or incomplete ledger.

### Distinguish work factor, advantage and quantum hash events

“128-bit security” is insufficient to fix a numerical failure-probability ledger. The experiment needs a resource profile: quantum queries and computation, signing queries, users, sessions, epochs, corruption and exposure. A constant-success work factor near \(2^{128}\) is not a promise of success probability below \(2^{-128}\) for every adversary making up to \(2^{128}\) queries.

For a generic random function with \(h\)-bit output, quantum preimage and collision events have different query behavior: the usual generic scales are \(Q^2/2^h\) and \(Q^3/2^h\), respectively, with theorem-specific constants and ranges. Constant-success collision query complexity has exponent \(h/3\), rather than the preimage exponent \(h/2\). The collision literature establishes this distinction; the exact reduction for our use must identify which event is required.[^3]

Consequently, a generic 256-bit collision-resistance assumption does not provide a 128-bit quantum collision work factor. This observation does **not** demonstrate an attack on Binius or prove that every Binius soundness reduction needs that exact unrestricted collision game. The actual vector-commitment/extraction analysis determines the required notion. The extended BCS QROM work supplies relevant theory, but its hypotheses and losses must be matched to the implemented protocol.[^6]

### A conditional numerical example, not chosen parameters

Suppose a future reduction genuinely supplies eight additive error terms in the same experiment. Giving each term a bound of \(2^{-131}\) yields

\[
\sum_{j=1}^{8}\epsilon_j\le8\cdot2^{-131}=2^{-128}.
\]

Eight terms each bounded only by \(2^{-128}\) give \(2^{-125}\). Add probabilities, not bit exponents. The existence of eight obligation labels alone does not establish the necessary composition inequality.

For illustration only, suppose a valid theorem gives

\[
\epsilon_{\rm coll}\le C M Q^3/2^h,
\]

with a proved constant \(C\), multiplicity \(M\), and query bound \(Q\). Meeting a per-term \(2^{-131}\) target requires

\[
h\ge3\log_2 Q+\log_2 M+\log_2 C+131.
\]

If one **hypothetically** sets \(Q=2^{64}, M=2^{16}, C=1\), the requirement is 339 bits. Using the preimage exponent instead would give 275 bits. These numbers demonstrate the effect of choosing the wrong event. They are not recommended parameters: \(C=1\), the multiplicity and the resource profile have not been proved or selected for this construction. The ledger preserves that distinction explicitly.

### What is numerically available now

The prior exact arithmetic routine was rerun for the all-secret random-matrix uniqueness bound with exponent 16, dimension 256, 608 rows and 1,024 additional domains. It reproduces

\[
\log_2\epsilon_{\rm uniqueness}\approx-148.2870623165,
\]

and the exact rational is below \(2^{-131}\). This is one conditional statistical collision bound under the existing matrix-sampling assumptions. It is not a computational LWR hardness estimate, a framing theorem, or the total error of the QC system.

The row-exposure accounting remains 672,352. Matching that distribution, rounding convention, secret distribution and number of observations to an applicable LWR reduction and concrete hardness analysis is still required. The small-modulus LWR paper provides conditional reductions, not automatic validation of these parameters.[^7]

### Quantum lifting does not silently add adaptive corruption

The examined Unruh full version states quantum lifting in Theorem 15: suitable statistical classical-UC emulation between classical protocols implies statistical quantum-UC emulation. Its Definition 3 quantifies over a fixed corruption set \(C\), and its network model replaces those parties accordingly. This does not establish adaptive mid-execution corruption for our proposed producer. It also does not turn an arbitrary classical stand-alone MPC proof into a UC proof.[^2]

We therefore retain explicit adaptive corruption/exposure obligations in the ledger. A fixed-corruption analysis may be useful intermediate evidence; it does not qualify the stronger target. For a total corruption bound of 21, the retry arithmetic still holds when fresh faults are charged to that bound. Privacy under such corruptions requires its own applicable protocol theorem.

## 7. Corrected next construction attempt

The attachment's four proposals can be retained only after these revisions:

1. **Registration and binding:** use the existing configuration-bound ordered registry and shared seat variable as the reference. Add a commitment layer only if it provides a measured static-cost or registration benefit. Preserve every message-specific authorization and trace condition.
2. **Relation and bytes:** port that exact joint relation into a selected lattice proof system, with explicit field/norm/hash costs. Use the corrected size gate; keep unknown complete size unknown. The existing trace format is already ruled out under the retained-prefix restriction.
3. **Security:** develop the resource profile and loss mapping alongside the relation inventory, before claiming a parameter set qualified. Preserve distinct collision, preimage, extraction, privacy and adaptive-corruption obligations.
4. **Production:** retain the full eligible registry for recovery. Choose a concrete robust MPC or a concrete collaborative prover with sound identifiable abort. Treat a smaller active set and phase separation as performance choices whose privacy and recovery properties must be proved.

This is a corrected conditional specification. This revision deliberately does not alter `verify_qc`, the native verifier, the tracing function, the authorization suite or the fault-exclusion policy in a deployed system.

## 8. Blocker disposition and reproducibility

| Blocker | Progress in v1.19 | What remains |
|---|---|---|
| Authorization-to-trace binding | Existing private shared-index relation audited; commitment shortcut rejected; exact missing native authorization identified. | In-proof authorization and complete backend integration. |
| 32 KiB serialization | Native workload inventoried; restricted floor preserved; incorrect upper-bound rejection rule corrected. | Exact eligible complete lattice relation and serialized proof. |
| 128-bit QPT qualification | Structured loss ledger created; statistical term recomputed; hash-event and corruption-model errors corrected. | Concrete applicable reductions, resource profile, parameter costs and composition. |
| Distributed production | Pool guarantee settled; exact sampling probabilities calculated; conditional 22-attempt theorem and ideal-model checks supplied. | A malicious-secure collaborative prover, actual blame/recovery implementation and privacy/liveness proof. |

The executable artifact reports **116 passing checks** covering all 22 pool sizes from 43 through 64, independent small-population enumeration of the sampling formula, ideal retry paths for every fault count 0–21, size-evidence classification, relation-count agreement, statistical arithmetic and rejection of the incomplete security ledger. These are arithmetic and ideal-model checks; they do not validate a cryptographic MPC implementation or a full QC.

Historical evidence is preserved separately. The v1.17 source ledger records two accepted native trace components and 27 public-pair diagnostic checks. Its files establish neither full vote authorization nor a complete 32 KiB QC. The source hashes and new inventory are included in the v1.19 model output. **Valid full-QC count remains zero.**

The package contains the new input document, this report, the security-loss ledger, the executable model and results, assembly sources, and every v1.18 archive member unchanged. Run the model after unpacking with:

```bash
python3 ce_qs_blocker_model_v1_19.py --root . --output audit_rerun.json
```

Local evidence references: `ce_qs_relation_v1_10.py`; `ce_qs_relation_checker_v1_10_results.json`; `ce_qs_parameter_audit_v1_10.py`; `continuation_v1.17/adapter/src/trace.rs`; `continuation_v1.17/patched_trace43_lazy_keys.json`; and `PQ_CE_QS_source_ledger_v1_17.json`.

## Sources

The attachment supplies the proposals being evaluated, not evidence of their security or performance. The following primary sources were checked for the relevant technical distinctions. Selected definitions and results were examined; no independent full-paper audit is claimed.

[^1]: M. Ben-Or, S. Goldwasser and A. Wigderson. *Completeness Theorems for Non-Cryptographic Fault-Tolerant Distributed Computation*, STOC 1988. [Author-hosted proceedings paper](https://www.math.ias.edu/~avi/PUBLICATIONS/MYPAPERS/GBW88/GBW88.pdf), first-page theorem and model discussion examined from page images. Supports the classical Byzantine-MPC threshold; not an adaptive-QPT implementation theorem for this system.

[^2]: D. Unruh. *Universally Composable Quantum Multi-Party Computation*, full version arXiv:0910.2912v1, 15 October 2009; EUROCRYPT 2010 work. [Primary full text](https://arxiv.org/pdf/0910.2912). Definition 3, corruption model, and Theorem 15 examined. The theorem numbering here follows this full version.

[^3]: Q. Liu and M. Zhandry. *On Finding Quantum Multi-collisions*, arXiv:1811.05385v2, 27 February 2019. [Primary full text](https://arxiv.org/pdf/1811.05385), abstract and §§1.4–2.2 examined for query exponents. Asymptotic statements do not provide concrete constants for our construction.

[^4]: T. Feneuil and M. Rivain. *SmallWood: Hash-Based Polynomial Commitments and Zero-Knowledge Arguments for Relatively Small Instances*, ePrint 2025/1085, revised 13 February 2026. [Primary record](https://eprint.iacr.org/2025/1085). Previously screened in v1.18; cited only to delimit the unsupported family-wide size claim.

[^5]: R. del Pino, S. Katsumata, G. Niot, M. Reichle and K. Takemure. *Unmasking TRaccoon: A Lattice-Based Threshold Signature with An Efficient Identifiable Abort Protocol*, CRYPTO 2025, ePrint revision 2 July 2025. [Primary record](https://eprint.iacr.org/2025/849). Abstract and protocol scope checked.

[^6]: A. Chiesa, Z. Di, Z. Hu and Y. Zheng. *How to Prove Post-Quantum Security for Succinct Non-Interactive Reductions*, EUROCRYPT 2026, ePrint revision 2 March 2026. [Primary record](https://eprint.iacr.org/2025/2166). Abstract and scope checked; full theorem-to-code mapping remains open.

[^7]: A. Bogdanov, S. Guo, D. Masny, S. Richelson and A. Rosen. *On the Hardness of Learning with Rounding over Small Modulus*, TCC 2016a, revised 5 February 2016. [Primary record](https://eprint.iacr.org/2015/769). Previously screened in v1.18; no concrete hardness estimate for this trace parameter set is inferred.
