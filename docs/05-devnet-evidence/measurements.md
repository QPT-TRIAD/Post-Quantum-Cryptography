# Measurements

Every number in this document was read out of a run record produced by the devnet campaign. For each
one, the run that produced it is named, and the document says whether the figure is a **single run**
or a **repeated** measurement. Nothing here is a benchmark, a throughput claim, or a distribution over
many trials; the records themselves label their timings `LOCAL-CONTROL OBSERVATION; NOT A NETWORK
BENCHMARK OR CONSENSUS TIMING`, and that label stays attached.

Two qualifiers are used throughout:

- **single run** — one execution produced the number. It is not a distribution.
- **repeated** — the number is a summary over more than one execution or more than one sample, and the
  count is given. Where a record says "medians of 3", the figure is the median of three executions.

Timings are wall-clock from the driving side. A figure below 1 ms is at the resolution floor of the
measurement and is reported as the record reports it, with that caveat.

## 1. Certificate and frame sizes as released by a live node

These are sizes of objects a running node actually produced and released, not design arithmetic.

| Object | Released size | Run | Nature |
|---|---:|---|---|
| Relation QC for a phase, 43 signers, profile ML-DSA-87 | **199,357 B** | every pair of `20260911T154517Z` and `20260913T064402Z` (447 pairs in the second pass) | single run per pass, identical across all pairs within a pass |
| Side-B certificate in the multi-target pairs | **203,990 B** | `20260911T154517Z` and `20260913T064402Z` | single run per pass; the same value in all multi-target pairs of both passes |
| Side-B control certificate in the second pass (`xset-qc_b`) | **199,357 B** | `20260913T064402Z` | single run; the control form, identical to the relation QC |
| Empty frame (`vacuous:empty-hex`) | **0 B** | `20260913T070954Z` | single run |
| Zero-signer frame (`vacuous:zero-signer`), well-formed header with an all-zero bitmap | **199,357 B** | `20260913T070954Z` | single run |
| Design-ledger expectation for the same QC | **199,099 B** — refuted | testbed design ledger, corrected by the C-22 record | model figure, not a measurement |

**The release-measurement reconciliation.** The design ledger's figure of 199,099 bytes for the
quorum certificate was **refuted by observation**: the live node released 199,357 bytes. The
difference is 258 bytes, which is **43 × 6 bytes** of per-entry framing the ledger had omitted. The
ledger figure is retained in the record as an expectation that did not hold, and the correct value is
carried as a reconciliation field in every record since. This is the only arithmetic in this document
that is not read directly from a record: it is stated with its inputs so a reader can check it.

**What the sizes mean.** The zero-signer case is the one worth reading carefully: a frame with a
well-formed header and an all-zero signer bitmap is still 199,357 bytes, and it is rejected for not
being a quorum (`NotAQuorum{got:0,need:43}`), not for its size. The empty case is rejected earlier, at
decode time (`decode.a:TooShort`). A frame's size therefore carries no information about whether it is
a quorum.

## 2. Timings

### Round finalization — the calibration run

Run `20260913T143920Z`, one attempt, exclusive host lock, node profile `mainnet`, node
`22026ca8…`, one round. Single run; not repeated.

| Quantity | Value |
|---|---:|
| Quiet-host precheck (rolling 60 s window) | `quiet`, iowait ≤ 0.13 % |
| First finalization | **20.17 s** |
| All 64 seats on one new finalized height with one state root | **37.46 s** |
| Finalized view | 0 |
| Relation QC signers in the finalized frame | 43 |

### Local-control latency — the same run

`/v1/status` sampled through the pending window: 512 probes, ok fraction 0.6.

| Percentile | Value |
|---|---:|
| p50 | **3.381 s** |
| p95 | **5.011 s** |

### Round finalization — the liveness arms

Runs `20260913T125634Z` (arms A/B/B2/C) and `20260913T132924Z` (arms D/E/E2). Each arm is a **single
run**; B2 and E2 are replicates of B and E respectively.

| Arm | Binary | Finalized | First / all-64 | View |
|---|---|---|---|---|
| A (control) | debug, pre-fix | **no** — 0 in 300 s | — | — |
| B | release, pre-fix | yes, one root | 145 s / 152 s | 1 |
| B2 | release, pre-fix, replicate | yes, one root | 137 s / 167 s | 1 |
| C (scale probe, n = 32) | release, pre-fix | yes, one root | ≤ 5 s / ≤ 5 s | — |
| D | debug, post-fix | **no** — 0 in 300 s | — | — |
| E | release, post-fix | yes, one root | 67 s / 67 s | 0 |
| E2 | release, post-fix, replicate | yes, one root | 10 s / 10 s | 0 |

E and E2 are the **same binary** and differ by **57 s**. Both pre-fix release runs finalized only in
view 1; both post-fix release runs finalized in view 0. The record's reading is that host state
weighs at least as much as the binary: E ran with host iowait median 77.5 % and max 98 %, E2 after a
quiet-host wait with iowait median 0.3 % and max 77 %.

### `status` latency per arm

Probe success and `/v1/status` p95 over the pending window, single run per arm.

| Arm | ok % | p95 |
|---|---:|---:|
| A (debug, pre-fix) | 4.9 | 5.0 s |
| B (release, pre-fix) | 92.4 | 5.0 s |
| B2 (release, pre-fix) | 71.6 | 5.0 s |
| C (release, n = 32) | 100 | 0.05 s |
| D (debug, post-fix) | 22.2 | 5.0 s |
| E (release, post-fix) | 65.8 | 5.0 s |
| E2 (release, post-fix) | 100 | **0.75 s** |

The p95 of 5.0 s is the probe timeout in most arms: the value means the probe timed out, not that the
latency measured 5.0 s. Only arm C (0.05 s) and arm E2 (0.75 s) measured a real latency below the
timeout. This distinction matters and is kept.

### Seat-level timings

Run `20260913T072300Z` (key rollback) and `20260913T072646Z` (stale state). Each **single run**.

| Quantity | Value | Run |
|---|---:|---|
| Restarted seat comes up ready | **8.2 s** | `20260913T072300Z` |
| Restart of the seat whose journal was rolled back | **7.1 s** | `20260913T072300Z` |
| Restart of the lagging seat | **7.1 s** (recorded `not_ready` at that point) | `20260913T072646Z` |
| Catch-up of the lagging seat | **4.4 s** | `20260913T072646Z` |
| Administrative calls driving the stale-state checks | 3 | `20260913T072646Z` |

### Verification and extraction timings — one certificate pair

Run `20260911T154517Z`, 378 pairs. **Single run per pair**; the table gives the range and median over
the 378 pairs for the wall-clock and the values recorded for the first pair for the phase breakdown.

| Quantity | Value |
|---|---:|
| Wall clock per pair | 1,336.3 ms – 2,870.7 ms (median 1,898.7 ms) |
| Decode | 43.051 ms |
| Extract | 61 µs |
| Offer | 942.937 ms |
| Verify both QCs | 158.246 ms |

### Replayed-evidence administrative round

Run `20260913T063631Z`, **single run**. Three phases, each carrying 43 votes: 1,854.452 ms,
1,872.453 ms, 1,856.085 ms.

## 3. Message, attempt and verification counts

| Count | Value | Run | Nature |
|---|---:|---|---|
| Votes per replayed-evidence phase | **43** | `20260913T063631Z` | single run, three phases |
| Relation QC signers in the finalized calibration frame | **43** | `20260913T143920Z` | single run |
| `/v1/status` probes in the calibration pending window | **512** | `20260913T143920Z` | single run, sampled every 5 s |
| Multi-target transplant attempts | **378** | `20260911T154517Z` and `20260913T064402Z` | single run per pass; the same attempt count in both |
| Multi-target pairs in the second pass | **447** | `20260913T064402Z` | single run |
| Multi-target checks passed | **380** (first pass), **899** (second pass) | `20260911T154517Z`, `20260913T064402Z` | single run per pass |
| Multi-target side-A quorums that verified (first pass) | **378 of 378** | `20260911T154517Z` | single run |
| Successful transplants | **0** | both passes | single run per pass |
| Rejection-stream calls answered with a typed 4xx | **240 / 240** | `20260913T070954Z` | single run |
| Rejection-stream attempts (stream plus 3 vacuous cases) | 243 | `20260913T070954Z` | single run, 4 administrative calls |
| Malformed-certificate checks | 30, all passed | `20260911T153826Z` | single run, 17 administrative calls |
| Signatures verified by the independent verifier | **258 of 258 (6 × 43)** | `20260913T071235Z` | single run; `disagreements: []` |
| Extraction-taxonomy cases | 24 of 24, with `index_out_of_range` `not_applicable` | `20260913T071235Z` | single run |
| Honest seats named in any run above | **0** | all runs above | single run per run; false positives 0 |

The 378 attempt count is a **count of what was tried**, never a bound on what exists. The zero in the
transplant column is a count of successful transplants observed, not a statement that none exists.

## 4. Resource measurements

### Calibration round (`20260913T143920Z`, single run, 8 samples over the pending window)

| Quantity | Median | Max |
|---|---:|---:|
| Container CPU sum | **7.05 %** | **1,160.3 %** |
| Host iowait | — | 92.12 % |

The CPU sum is over 64 containers on a 12-core host: 1,160.3 % means roughly twelve cores saturated at
one sample. The host iowait maximum of 92.12 % is in-round, on a host whose precheck had shown iowait
≤ 0.13 % over the preceding 60 s — the storage pressure arose *within* the round.

### Liveness arms (single run per arm)

| Arm | CPU sum median / max | RSS sum max | Load max | MemAvail min | Host iowait median / max |
|---|---|---|---|---|---|
| A (debug, pre-fix) | 1,163 % / 1,234 % | 3.6 GiB | 73.7 | 8.3 GiB | n/a |
| B (release, pre-fix) | 347 % / 1,161 % | 6.3 GiB | 47.5 | 5.6 GiB | n/a |
| B2 (release, pre-fix) | 372 % / 1,050 % | 6.2 GiB | 51.0 | 5.7 GiB | n/a |
| C (release, n = 32) | 379 % (1 sample) | 1.0 GiB | 9.2 | 11.3 GiB | n/a |
| D (debug, post-fix) | 1,087 % / 1,222 % | 4.1 GiB | 76.0 | 5.8 GiB | 0 % / 70 % |
| E (release, post-fix) | 38 % / 413 % | 5.6 GiB | 54.1 | 4.4 GiB | 77.5 % / 98 % |
| E2 (release, post-fix) | 587 % / 1,075 % (2 samples) | 3.4 GiB | 19.9 | 6.5 GiB | 0.3 % / 77 % |

The record adds two observations from the stall windows: in arm E, all 7 stall sweeps fell inside the
high-iowait interval, 26–64 seats timed out per sweep spread across seats, every responding seat was at
view 0, and the round finalized about 12 s after the I/O pressure cleared; in arm E2, after a 3 s
spike the device absorbed 67–250 MiB/s at under 10 ms latency and nothing stalled. Arm D was a CPU
stall (user 98–99 %), not an I/O stall.

### Rejection stream (`20260913T070954Z`, single run)

| Quantity | Value |
|---|---:|
| RSS delta over the run | 6,039,798 B |
| Fitted slope over 7 points | **18,827.56 B/call** (intercept 21,507,416.8) |
| Peak RSS | 27,577,548 B |
| Process count delta | 0 |
| Bytes submitted | 1,212,103 |

### Per-run totals of local-control traffic

| Run | Administrative calls | Bytes | Local-control seconds |
|---|---:|---:|---:|
| `20260911T153826Z` (malformed certificate) | 17 | 11,840,217 | 2.589 |
| `20260911T154517Z` (multi-target, first pass) | 379 | 469,656,610 | 728.93 |
| `20260913T064402Z` (multi-target, second pass) | 449 | 552,717,548 | 526.186 |
| `20260913T070954Z` (rejection stream) | 4 | 1,212,103 | 2.028 |
| `20260913T072300Z` (key rollback) | 3 | 1,252,614 | 1.155 |

These are local-control figures — bytes and calls issued by the driver over its administrative channel
on one host. They are not network traffic, throughput, or consensus timing.

## 5. Debug against release — the ratio measurements

Run `20260913T125634Z`. **Repeated: medians of 3** where labelled, otherwise single run.

| Quantity | Debug | Release | Ratio |
|---|---:|---:|---:|
| ML-DSA-87 sign + verify, medians of 3, no cluster | **10.6 ms** (10.63 ms) | **0.78 ms** | **≈ 13.6× (13.57×)** |
| One validation-equivalent: transfer | ≈ 0.26 s | ≈ 6–9 ms | — |
| One validation-equivalent: evidence intent (construct + sign) | ≈ 0.32 s | ≈ 6–9 ms | — |
| Capacity, validations per second (estimated from the above) | ≈ 40/s | ≈ 1,300/s | — |

The release validation figure is **at the resolution floor** of the measurement — the exec baseline
was subtracted and the remainder is jitter. The capacity row is an estimate derived from those two
rows, against an estimated relay demand of about 2,000/s at n = 64; it is a model figure, not a
measurement, and is marked as such in the record.

The sign+verify measurement was taken with no cluster running. It is reported with its sample size (3)
so that it is not mistaken for a distribution.

## 6. Release-measurement observations

Three observations about measurements themselves, each recorded with the run that produced it:

1. **A model figure yielded to a release measurement.** The ledger's 199,099 B was replaced by the
   observed 199,357 B, and the 258-byte difference (43 × 6 B of per-entry framing) was identified as
   the omitted term. The correction is carried in the record field, not in the prose.
2. **A release measurement is not stable across host states.** The same release binary finalized at
   67 s and at 10 s in two runs 57 s apart, and the two post-fix runs carry opposite verdicts
   (`mixed_inconclusive` against `debug_build_artefact`) on pre-committed rules.
3. **A release result does not transfer to the debug build.** The debug arms failed to finalize both
   before and after the relay change, with the recorded verdict `design_limit_on_this_host`. A
   `mainnet`-profile pass does not close the debug finding.

## 7. Deduplication observations

- **The relay-path duplicate check.** On the peer relay route only, a receipt **byte-identical** to an
  entry already queued skips re-validation. The client submission route still validates first. This
  asymmetry was deliberate: it preserves the recorded 4xx expectations of the `REPLAY` scenario, whose
  240-call rejection stream and typed rejections depend on the client path validating every time.
- **What the dedup did and did not change.** It raised the debug arm's probe success from 4.9 % to
  22.2 % and lowered CPU median by about 7 %, and both post-fix release runs finalized in view 0
  against view 1 pre-fix. It did **not** clear the debug stall: the post-fix debug arm still recorded
  0 finalized in 300 s. The record's reading is that the residual debug cost is pacemaker
  re-validation every 250 ms, the submit loop, and construct-and-sign at about 0.27 s.
- **Deduplication at the offence level is per offence key.** The construction for the typed-duplicate
  re-extraction turns on the fact that the offence key is computed once and holds no candidate
  identifier, so any finalized key makes that seat's claim a duplicate whichever record carried the
  evidence. This is a property of the construction recorded before the scenario text changed; the
  observation that would confirm it live is pending (see `open-items.md`).
- **An unverified precondition.** The offer step rejects with `SlashEvidenceInvalid` before the
  duplicate check when the snapshot epoch differs from the vote epoch, so the duplicate route needs
  the epoch unchanged from height 1 to height 2. This has not been verified live.

## 8. What these numbers are not

- Not benchmarks, and not evidence about the construction. They describe one implementation on one
  shared 12-core host under one operator.
- Not distributions. Where a number is a median it is a median of three; where it is a maximum it is
  a single sample; where it is a percentile over a timeout-bounded probe, the timeout is named.
- Not transferable between profiles. Debug figures and release figures are never combined, and no
  ratio here is a claim about a deployed build.
- Not additive. The theoretical and measured columns carried by the records are reported separately
  and are never summed, and the campaign's regimes are never merged into a total.
