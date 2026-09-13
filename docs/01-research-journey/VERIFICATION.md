# VERIFICATION — docs/01-research-journey

What was checked while assembling this package, with the commands run and what they returned.

Verdicts are one of `reproduced`, `reproduced-with-difference`, `not-reproducible`, `not-run`.

**Scope note carried from the work-package specification: there is no executable in this domain.**
The research-journey package has no test suite, no script and no result artefact of its own — the
trail's own line is "Tests to re-run: none". Every recorded count and byte figure in
`chronology.md`, `decisions.md`, `dead-ends.md` and `theories-used.md` is therefore reported as the
trail records it, and the entries below mark which of those numbers were independently checked by
arithmetic and which could not be checked at all because the artefact does not exist.

Environment for every command: the repository root, and the work directory beside it that holds the
assembly tooling and the pinned interpreter, activated with `tooling/activate.sh` where a command
needs more than the standard library (none below does).

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| `pqt.md` placed at its mapped path | `sha256sum docs/01-research-journey/pqt.md` | CPython 3.12 host, `sha256sum` from coreutils | `40fce0843d9b4b8316d8994908aaa4002aa76eb0fef0937520a930e18d23bda7` (map row `pqt.md`, domain D0) | `40fce0843d9b4b8316d8994908aaa4002aa76eb0fef0937520a930e18d23bda7` | reproduced | exact match against the map's digest |
| `pqt.md` size | `wc -c docs/01-research-journey/pqt.md` | as above | 65,258 bytes (map row) | 65,258 | reproduced | — |
| `pqt.md` byte-identical to the source file | `cmp` of this file against the copy in the source tree (outside this repository) | as above | no output, exit 0 | no output, exit 0 | reproduced | the file was copied, not rewritten; the map row carries its digest, so the copy can be checked here without the source tree |
| forbidden-string scan over this package | `python3 tooling/checks/scan-forbidden.py docs/01-research-journey/` (run from the repository root; re-run with `--quiet` after `VERIFICATION.md` was added, and once more after this file's line 25 was rewritten) | pinned Python, scanner with 6 rule categories | no findings | `files scanned: 7, findings: 0` — ai-name 0, ai-meta 0, abs-path 0, tracking 0, contact 0, secret 0; exit 0 on the first and the final run | reproduced-with-difference | seven files scanned (`README.md`, `chronology.md`, `decisions.md`, `dead-ends.md`, `theories-used.md`, `pqt.md`, `VERIFICATION.md`). One intermediate pass reported `findings: 2` — `ai-name` 1, `abs-path` 1 — **both on line 25 of this file**, in the illustrative path shapes this very table used. That line was rewritten (see the two rows below) and the final run is clean. See the note below on why the scan is otherwise clean |
| scrub line changes | — | — | any finding judged a real leak to be recorded as `new_path<TAB>line<TAB>rule<TAB>before<TAB>after` | **2 data rows**, both on `docs/01-research-journey/VERIFICATION.md` line 25, rules `ai-name` and `abs-path`; recorded in `staging/scrub-docs01.tsv` | reproduced | both findings are in text newly written for this package, not in the trail's own material, and both were judged to be real (a tool name and a literal machine-path shape must not stand, even as examples of what is being removed). The minimum edit replaced each example with the rule's own name; no fact, number, date or decision was touched. Every other line of the package scanned clean |
| machine-path scrubbing pass (`scrub_repo.py`'s own rules, applied to this directory only) | `python3` importing the assembly's `scrub_repo.py` — a work-directory tool, not part of this repository — and applying its six rules (`scratch-uuid`, `scratch-any`, `scratch-tail`, `source-tree`, `home-linux`, `home-mac`) to every file under this directory | pinned Python | no line rewritten | `files checked: 7  scrub_repo rule hits: 0` on the final run | reproduced-with-difference | the integration scrub rewrites scratch-directory paths (its three `scratch-*` rules) and home-directory paths (`source-tree`, `home-linux`, `home-mac`). An earlier run of this same check reported one hit, rule `scratch-tail`, on line 25 of this file; the line was rewritten and the final run is clean. This check and the forbidden-string scan overlap on those shapes, so it was run anyway rather than inferred from the other |
| chain arithmetic: quorum intersection | `python3 -c "print(2*43-64, 21+1)"` | CPython 3 | 22 = F+1 | 22, 22 | reproduced | the accountability claim's central constant |
| chain arithmetic: ML-DSA and sidecar sizes | `python3 -c "print(667*2420, 43*3309, 32768-43*96-160, 208+5504+27056, 5504/43)"` | CPython 3 | 1,614,140 B ≈ 1.539 MiB; 142,287 B ≈ 139.0 KiB; 28,480 B; 32,768 B; 128 B | 1,614,140 / 1.5394 MiB; 142,287 / 139.0 KiB; 28,480; 32,768; 128.0 | reproduced | the two proof allowances and the handle width all follow |
| chain arithmetic: signer-set counting bound | `python3` with `lgamma`, `log2 C(1000,667)` | CPython 3 | ≈ 912.74 bits (≈ 114.1 B) | 912.74 bits | reproduced | the bound that reframed the target |
| chain arithmetic: the counting bound's unit slip | `python3 -c "print(918285/8, 918285/8/1024)"` | CPython 3 | source says "≈ 918,285 bits ≈ 114.8 KiB" | 114,785.6 B = 114.8 **kB** = 112.1 KiB | reproduced-with-difference | **source error, recorded not repaired.** The bit count is right and the byte count is right in decimal units; the KiB label is wrong. The trail's own presentation of the instance is what carries the slip, not the bound |
| chain arithmetic: 384-bit width | `python3 -c "print(384//3)"` | CPython 3 | 2^(384/3) = 2^128 and 256/3 ≈ 85.3 | 128; 85.3 | reproduced | — |
| chain arithmetic: multi-user lifetime budget | `python3` with `log2(64*3653)` | CPython 3 | E = 3,653, N_u = 233,792, loss 17.835 bits, single-user target 157.835 at 2^-140 | 3,653; 233,792; 17.835; 157.835 | reproduced | review input #6 reproduced the same values independently |
| chain arithmetic: extraction-bound illustration | `python3 -c "print(12*2**384/2**512, 20*2**256/2**265)"` | CPython 3 | 2^-124.415; 5/128 = 0.0390625 | 2^-124.415; 5/128 = 0.0390625 | reproduced | — |
| chain arithmetic: repetition counts | `python3` with `ceil(log2(20·2^(2n)/(1/24)))` at n = 32, 64, 92, 128 | CPython 3 | 73, 137, 193, 265 | 73, 137, 193, 265 | reproduced | — |
| chain arithmetic: the wider repetition margin | `python3 -c "print(log2(20)-64)"` | CPython 3 | 320 repetitions give ε_J < 2^-59 | −59.68 | reproduced | the claim holds; the value is slightly better than stated |
| chain arithmetic: Hoeffding application | `python3 -c "print(-2*128*0.25/log(2), sqrt(log(2)/2))"` | CPython 3 | 2^-92.33248 at N = 128, Δ = 1/2; Δ ≥ 0.588705 for 2^-128 | −92.33248; 0.588705 | reproduced | checked against the source's own formula form, which uses `e^{-2NΔ²}` with no leading factor — so the value is self-consistent and the *premise* is what fails, not the arithmetic |
| chain arithmetic: sample-disclosure length | `python3` with `ceil((128+log2 Q_d)/(−log2(1−22/64)))` | CPython 3 | L = 211 single-domain; L = 264 for 2^32 domains = 33 bytes | 211; 264 | reproduced | — |
| chain arithmetic: the conditional ledger | `python3 -c "from fractions import Fraction; print(Fraction(6,2**131)==Fraction(3,4*2**128))"` | CPython 3 | 6·2^-131 = (3/4)·2^-128 < 2^-128 | `True` | reproduced | exact rational comparison |
| chain arithmetic: runtime cap | `python3 -c "print(64+519*log2(759/1024))"` | CPython 3 | R = 519 suffices for δ_run ≤ 2^-160 at q_S = 2^64 | −160.23 | reproduced | the stated bound is satisfied |
| chain arithmetic: JMW parameter check | `python3 -c "print(8380417//32)"` | CPython 3 | 2γη′n(m+k) < ⌊q/32⌋ fails for ML-DSA-87: 6,304,047,104 < 261,888 is false | ⌊8380417/32⌋ = 261,888; ratio ≈ 24,071 | reproduced | the inequality is false by a factor of about 24,000 |
| chain arithmetic: conflict-domain request count | `python3 -c "print(3*43 > 64+2*32)"` | CPython 3 | 3q > n + 2c holds at c = 32, giving K ≤ 2 | `True` | reproduced | — |
| chain arithmetic: size-campaign floors and reductions | `python3 -c "print(79632/28480, 31744-28480, 328672/28480, (328672-267472)/328672*100, 50496/32768)"` | CPython 3 | 2.8×; 3,264 B over; 11.54×; 18.6% reduction; 1.54× | 2.796; 3,264; 11.54; 18.62%; 1.54 | reproduced | all five |
| chain arithmetic: toy test counts | `python3 -c "print(17**3*16)"` | CPython 3 | 78,608 interpolation cases over F₁₇ | 78,608 | reproduced | 17³·16 |
| chain arithmetic: collision and category-5 screen | `python3 -c "print(3*64-256)"` | CPython 3 | (2^64)³/2^256 = 2^-64; and the pasted table's n = 128 entry | 2^-64 confirmed; the pasted n = 128 entry is wrong (see the next row) | reproduced-with-difference | **source error, recorded not repaired.** The pasted cubic table writes "n=128: 2^-64"; with q = 2^64 the term is 2^(+64), a vacuous bound above 1. The n = 192, 256 and 320 entries are consistent |
| chain arithmetic: the report's sizing template | `python3 -c "print(3*64+16+0+131)"` | CPython 3 | h ≥ 3·log₂Q + log₂M + log₂C + 131 = 339 for Q = 2^64, M = 2^16 | 339 | reproduced | 384 clears it |
| the malformed final-statement box | `awk 'NR>=1506 && NR<=1520' docs/01-research-journey/pqt.md` | coreutils | a defect at lines 1508–1518 | confirmed: `\[` at line 1511 is closed by `$$` at 1513, and line 1518 carries a stray `]` | reproduced | **left unrepaired by design.** The file is the artefact; the defect is described in `README.md` and the statement is quoted in `chronology.md` §VIII |
| the undefined `\Adv` macro in the report | `grep -c '\\Adv' pqt.md`; `grep -n 'newcommand' pqt.md` | coreutils | not previously recorded | 8 uses of `\Adv`, 0 macro definitions in the file, and the file has no LaTeX preamble | reproduced | a source defect that renders as an error in any standard renderer; recorded here rather than silently corrected |
| the phase VI size campaign's counts and byte sizes | — | — | v1.7–v1.29 pass counts and frame sizes | not run | not-run | **no artefact exists.** The v1.7–v1.16 and v1.22 review packages, and the v1.30 and v1.32 documents, are absent from the source tree; the counts exist only as transcript prose. Re-running them would require the experiment folders, which is the work of `domains/03-zk-carrier-experiments/` |
| the Target-B construction's test counts | — | — | 78,608 interpolation cases; 289 masking tables; 4,096 and 151,263 sampling combinations; four negative controls | not run | not-run | the report and its test bundle are absent from the source tree; only the headline number survives, in prose |
| the bounded model checks (v0.6, v0.7) | — | — | v0.6: 15,633/44,388, 2,401/10,976, 90/233. v0.7: 729/2,916, 140/400, 23,474/127,006, 28/55, 1,440/8,592, 13 invariants | not run | not-run | the v0.7 `.tla` and `.cfg` are absent from the source tree, so the checks cannot be re-run; **the v0.8 release is absent entirely**, including its `.tla`, `.cfg`, auditor and SHA-256 manifest. Review input #7 also reports that the checker script contains no consistency check |
| native TLC/TLAPS on the model | — | — | never run in the research environment | not run | not-run | the trail records that TLC/TLAPS and `tla2tools.jar` were unavailable and that external binary acquisition was blocked. This is the reason no model-check result on this trail is machine-checked by the standard tool |
| the downstream reversal measurements (property-layer count, amendment figures) | — | — | withdrawn "16/16"; "113 of 116" | not re-run here | not-run | these are other domains' measurements, recorded in `records/` and in `domains/04-operator-ledger/` and `domains/08-hidden-signers/`. They are reported in `chronology.md` §IX with their owners and were **not** re-derived for this package |
| the property-layer withdrawal's own evidence | — | — | hash-signature suite collects zero tests | not run | not-run | the re-run logs belong to `records/`; this package cites the finding, it does not own it |

## Note: why the forbidden-string scan is clean here, and what that does and does not mean

The final scan over this directory returns zero findings. One line was changed — line 25 of this
file, which had named two of the scrub's path shapes by their literal examples — and that change is
recorded as two rows in `staging/scrub-docs01.tsv`. No line of the trail's own material was edited.
The zero should not be read as a claim that the trail was clean.

The trail's two finding-heavy texts — the first and second working transcripts — are **not migrated
into this repository**. The file map marks both `source-only` and the work-package specification
instructs that the journey documents be newly written from the reading dossier rather than copied
from them. So the findings those two files carry (179 of the tree's 252) are not in this directory
and cannot be, because the files they live in are not here.

`pqt.md` was checked separately: it is placed byte-identical to the source, and the scan finds nothing
in it either. A reader who wants the findings that were removed from the source tree should read the
scrub report that the integration pass produces, not this package's directory.

What the zero means, precisely: **nothing in this package leaks a machine-specific path, a tracking
parameter, an address, a token shape or an assistant-adjacent phrase.** It does not mean the trail was
free of them, and it does not mean no reasoning was lost: the only line edited is the one recorded
above, and it carried no fact, number, date or decision.

## What could not be checked, and why

- **No test in this domain can be run.** There is no executable here, and the trail's phase VI and
  phase VII numbers rest on artefacts of which most are absent from the source tree (see
  `chronology.md` §XII–XIII).
- **No claim on this trail is machine-checked or externally refereed.** Native TLC and TLAPS were
  never run; the mechanisation recommendations were never carried out; and the trail's recorded
  reviews are external review input, several of which corrected each other as well as the work.
- **The arithmetic checks above verify consistency, not provenance.** Where a floor or a bound is
  reproduced, that shows the trail's arithmetic is internally sound. It does not show that the
  underlying measurement was correct, and for the absent artefacts it cannot.
- **Two source errors are recorded and not repaired**, per this package's rule: the unit slip at
  PS:99, and the vacuous n = 128 entry in the pasted cubic table. Both are stated in
  `chronology.md` §X. Neither changes a conclusion the trail draws; the second is the more serious,
  because the entry is used to argue about Category 5 parameters and had it been noticed at the time
  it would have strengthened the refutation rather than weakened it.
