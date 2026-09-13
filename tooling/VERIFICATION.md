# VERIFICATION — `tooling/`

What was observed on the machine that recorded this repository's results, with the command that
observed it and the value it reported. This file is the evidence base for every version string and
every runtime elsewhere in `tooling/`: nothing in those documents is quoted from a ledger, and
anything that could not be observed here is listed as not run or not reproducible with its reason.

**Verdict values:** `reproduced`, `reproduced-with-difference`, `not-reproducible`, `not-run`.

**The rule this file follows.** A number a re-run does not reproduce is written down as a difference
with the reason, in public, and is never smoothed over. The differences a re-run will actually meet
are in §4.1 and §4.2; §4.3 and §4.4 add what the repository's own four gates reported when they were
last run against this tree, including the states they replaced. No recorded claim in this package
rests on any of them.

## 0. Where and how these were observed

| Item | Value |
|---|---|
| Host | Linux, x86-64, 12 cores (`nproc=12`), 13th Gen Intel Core i7-1355U |
| Date | 2026-09-13; the version captures carry timestamps 16:35–16:47Z |
| Python | CPython 3.12.3, the interpreter the environment provides |
| Environment | two virtual environments and a tool tree, laid out as `environment.md` §3–§7 describes; nothing below was observed outside them |
| How commands were run | in a shell with the environment's activation script sourced, from the repository root unless a row says otherwise |
| What "expected (recorded)" cites | the environment's own recorded `pip freeze` output (one per profile) for distribution versions; the recorded run logs and result files inside the repository for outputs; the domain's own `results/` files for runtimes |
| Two profiles | the **pinned profile** is the host environment the domains document (sympy 1.13.1, numpy 2.4.6, numba 0.65.1); the **container profile** reproduces the pins of the mathematics container (sympy 1.14.0, numpy 2.2.6, numba 0.61.2). They are separate environments and are reported separately |
| Data outside the repository | the read-only research tree, reached through `PQT_SRC`, and the NIST ACVP vector files. Neither is redistributed here; both are described in `README.md` |

## 1. The pinned Python environment, observed live

The observations in this table come from the import check the environment build ran on
2026-09-13T16:35Z. It imported every installed distribution, then every third-party symbol the
sources in this repository import, and finished with `IMPORT FAILURES: 0`. `python3 -m pip list`
reports the same version strings on the same interpreter. The check script itself belongs to the
environment build and is not shipped; `environment.md` §9 gives the shipped equivalents.

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| Python interpreter | `python3 -V` | pinned profile | 3.12.3 | `Python 3.12.3` | reproduced | the same interpreter for both profiles |
| sympy | `python3 -m pip list` | pinned profile | 1.13.1 (recorded lock) | 1.13.1, imports both as `sympy` and as `isympy` | reproduced | exact-arithmetic engine of the mathematics layer |
| galois | `python3 -m pip list` | pinned profile | 0.4.11 (recorded lock) | 0.4.11 | reproduced | independent field engine; see §3 |
| numpy | `python3 -m pip list` | pinned profile | 2.4.6 (recorded lock) | 2.4.6 | reproduced | used by the mathematics layer and the S1 Grover chain |
| numba | `python3 -m pip list` | pinned profile | 0.65.1 (recorded lock) | 0.65.1 | reproduced | pulled in by galois at run time |
| llvmlite | `python3 -m pip list` | pinned profile | 0.47.0 (recorded lock) | 0.47.0 | reproduced | numba's code generator |
| hypothesis | `python3 -m pip list` | pinned profile | 6.151.9 (recorded lock) | 6.151.9, and every symbol the property files import resolves | reproduced | the property layer's falsification engine |
| pytest | `python3 -m pip list` | pinned profile | 9.0.2 (recorded lock) | 9.0.2 | reproduced | invoked as a command by the property runner |
| pluggy, iniconfig, packaging | `python3 -m pip list` | pinned profile | 1.6.0, 2.3.0, 26.3 (recorded lock) | 1.6.0, 2.3.0, 26.3 | reproduced | pytest's dependencies |
| dilithium-py | `python3 -m pip list` | pinned profile | 1.4.0 (recorded lock) | 1.4.0; `dilithium_py.ml_dsa.ML_DSA_87` imports | reproduced | pure-Python ML-DSA, one of the three cross-checked implementations |
| kyber-py | `python3 -m pip list` | pinned profile | 1.2.0 (recorded lock) | 1.2.0; `kyber_py.ml_kem.ML_KEM_1024` imports | reproduced | pure-Python ML-KEM |
| cryptography | `python3 -m pip list` | pinned profile | 46.0.0 (recorded lock) | 46.0.0; HKDF, AESGCM, `hashes` and `InvalidTag` all import | reproduced | the proof-carrier experiment's data channel |
| cffi | `python3 -m pip list` | pinned profile | 2.0.0 (recorded lock) | 2.0.0 | reproduced | required by the pinned `pqcrypto` wheel |
| pycparser | `python3 -m pip list` | pinned profile | 3.0 (recorded lock) | 3.0 | reproduced | cffi's parser |
| pqcrypto | `python3 -m pip list` | pinned profile | 0.3.4 (recorded lock; wheel digest and byte size recorded in the domain) | 0.3.4; `pqcrypto.kem.ml_kem_1024`, `pqcrypto.sign.ml_dsa_87`, `falcon_padded_512`, `sphincs_shake_256s_simple` all import | reproduced | the wheel is not redistributed; `packages.md` records its digest |
| hsslms | `python3 -m pip list` | pinned profile | 0.1.3 (recorded lock) | 0.1.3, imports | reproduced | **differs from the recorded audit-host runs — see §4.1** |
| dnspython | `python3 -m pip list` | pinned profile | 2.8.0 (recorded lock) | 2.8.0; all eight `dns.*` symbols the S2 script imports resolve | reproduced | **differs from the recorded audit-host runs — see §4.1** |
| liboqs-python | `python3 -c "import oqs; print(oqs.oqs_version(), oqs.oqs_python_version())"` | pinned profile, environment sourced | 0.16.0 (recorded lock) | `0.16.0 0.16.0` | reproduced | prints `liboqs-python faulthandler is disabled` on stderr first; needs `OQS_INSTALL_PATH`, otherwise it tries to fetch and build its own copy |
| mpmath | `python3 -m pip list` | pinned profile | 1.3.0 (recorded lock) | 1.3.0 | reproduced | sympy's dependency; imported by no source file here |
| sortedcontainers, Pygments, typing_extensions | `python3 -m pip list` | pinned profile | 2.4.0, 2.21.0, 4.16.0 (recorded lock) | 2.4.0, 2.21.0, 4.16.0 | reproduced | transitive dependencies |
| pip | `python3 -m pip list` | pinned profile | 24.0 | 24.0 | reproduced | reported for completeness; not used by any run |

### The container profile

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| sympy | `python3 -m pip list` | container profile | 1.14.0 (recorded lock) | 1.14.0 | reproduced | the mathematics layer's container pins |
| galois | `python3 -m pip list` | container profile | 0.4.11 (recorded lock) | 0.4.11 | reproduced | same version as the pinned profile |
| numpy | `python3 -m pip list` | container profile | 2.2.6 (recorded lock) | 2.2.6 | reproduced | deliberately older than the pinned profile |
| numba | `python3 -m pip list` | container profile | 0.61.2 (recorded lock) | 0.61.2 | reproduced | container pin |
| llvmlite | `python3 -m pip list` | container profile | 0.44.0 (recorded lock) | 0.44.0 | reproduced | container pin |
| mpmath, typing_extensions, pip | `python3 -m pip list` | container profile | 1.3.0, 4.16.0, 24.0 (recorded lock) | 1.3.0, 4.16.0, 24.0 | reproduced | transitive |
| every other distribution | the same import check, run against this interpreter | container profile | not expected here | correctly reported `NOT INSTALLED in this interpreter` for cryptography, dilithium-py, dnspython, hsslms, hypothesis, kyber-py, liboqs-python, pqcrypto and the rest | reproduced | the two profiles are separate; the container profile is for the mathematics layer only, and the check's final line is still `IMPORT FAILURES: 0` over the packages both profiles share |

## 2. The tools and the C library, observed live

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| Tamarin | `tamarin-prover --version` | environment sourced (also needs Maude) | 1.12.0 | `tamarin-prover 1.12.0`, with `maude tool: 'maude'` and `checking version: 3.5.1. OK.` printed by the same invocation | reproduced | the version line is emitted together with the Maude check, so one command observes both |
| Maude | `maude --version < /dev/null` | environment sourced | 3.5.1 | `3.5.1` | reproduced | without the stdin redirect Maude opens a session and waits — do not run it bare while scripting |
| ProVerif | `proverif -h \| head -2` | environment sourced | 2.05 | `Proverif 2.05. Cryptographic protocol verifier, by Bruno Blanchet, Vincent Cheval, and Marc Sylvestre` | reproduced | no distribution package exists; built from source per `environment.md` §7 |
| GraphViz `dot` | `dot -V` | environment sourced (launcher supplies `LD_LIBRARY_PATH`) | 2.43.0 | `dot - graphviz version 2.43.0 (0)` | reproduced | needed only for Tamarin's tool-availability check |
| liboqs shared library | `sha256sum tooling/liboqs/lib/liboqs.so.0.16.0` | build product of `environment.md` §6 | `710d951bd840b02b8a35cd671185c269432eec0fdc2605ddeed3e565871d0311` | `710d951bd840b02b8a35cd671185c269432eec0fdc2605ddeed3e565871d0311`, version `0.16.0` | reproduced | digest identifies the exact build the recorded measurements came from; a different compiler or CPU target changes it legitimately |
| liboqs algorithm census | the ctypes wrapper, in-process | pinned profile, library loaded from the built tree | 221 signature and 41 KEM identifiers enabled, none disabled | `SIG: 221/221 enabled`, `SIG disabled: (none)`, `KEM: 41/41 enabled`, `KEM disabled: (none)` | reproduced | includes ML-DSA-44/65/87, ML-KEM-512/768/1024, OV, SNOVA, MAYO, Falcon, SLH-DSA |
| the wrapper's default library path | same run | pinned profile | `tools/liboqs-0.16.0/build/lib/liboqs.so` two directories above the stack | resolved to that path, `exists True`; the library reports itself as `liboqs 0.16.0` | reproduced | this is the path `environment.md` §6 tells a reader to create in this repository's layout |

## 3. Checks re-run during this pass

| item | command | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| every distribution imports, and every imported symbol resolves | the environment build's import check (equivalent shipped command in `environment.md` §9) | both profiles, each interpreter separately | 0 failures | `IMPORT FAILURES: 0` in both profiles; no symbol the sources import failed to resolve in the profile that is meant to provide it | reproduced | the container profile reports the pinned-profile-only packages as not installed in that interpreter, which is correct and is why the two profiles are reported separately |
| ML-DSA-87 through the project's own ctypes wrapper | `python3 domains/11-independent-audit-stack/primitives/oqs_ctypes.py` | pinned profile, library from the built tree | public key 2592 B, secret key 4896 B, signature 4627 B; sign/verify with context true, with the wrong context false | `ML-DSA-87 FIPS204 ctx True 2592 4896 4627`; `sign/verify ctx: True wrong ctx: False`; `liboqs 0.16.0` and the library path printed on the first line | reproduced | this is the shipped script, so the row is repeatable as written once the compatibility directory of `environment.md` §6 exists |
| ML-DSA-87 seeded signature and tamper rejection | the same wrapper, driven with the recorded parameters | pinned profile | signature width 4627; verify true; wrong message false; tampered signature false; seeded key generation deterministic | `ML-DSA-87 ctx=None: siglen=4627 verify=True wrong_msg=False tampered=False`; the same for a context string; seeded key generation deterministic with the recorded public-key prefix | reproduced | the recorded 4627-byte width is the input to the 32 KiB certificate budget |
| ML-KEM-1024 round trip | the same wrapper | pinned profile | encapsulation key 1568, decapsulation key 3168, ciphertext 1568, shared secret 32; round trip true; both seeded entry points available | `ML-KEM-1024 FIPS203 1568 3168 1568 32 seeds 64 32 derand True True`; `kem roundtrip: True` | reproduced | the derandomised entry points are what make the recorded vectors reproducible |
| liboqs against the recorded per-scheme signature widths | the same wrapper over the schemes the certificate layer uses | pinned profile | OV-V-pkc 260, SNOVA_29_6_5 454, SNOVA_60_10_4 576, MAYO-5 964, ML-DSA-87 4627, each verifying and each rejecting a wrong message | every one matched its recorded width, verified, and rejected the wrong message; final line `RESULT: PASS` | reproduced | this is the evidence behind the scheme table in the certificate layer |
| the field library, exhaustively | a one-off GF(2^8) sweep against an independent shift-and-add reference | pinned profile: galois 0.4.11, numpy 2.4.6, numba 0.65.1, Python 3.12.3 | all 65,536 products correct | `field GF(2^8) irreducible_poly x^8 + x^4 + x^3 + x^2 + 1 0x11d primitive_element 2`; `pairs 65536 mismatches 0`; `spot: GF(0x57)*GF(0x83) = 0x31 ref 0x31`; `inverses x*x^-1==1 for all nonzero x: True`; `seconds 1.56`; `RESULT: PASS` | reproduced | the script belongs to the environment build and is not shipped — hence the column wording; the mathematics layer (`math_layer.py`) exercises the same library in the shipped tree and is the repeatable substitute |
| Tamarin's own self-test | `tamarin-prover test` | environment sourced, `dot` available | 55 cases, 0 errors, 0 failures | `Cases: 55 Tried: 55 Errors: 0 Failures: 0`; `*** TEST SUMMARY *** All tests successful.` | reproduced | exit 0; the unification infrastructure and the Maude interaction are both exercised |
| ProVerif on a distribution example | `proverif tooling/tools/proverif-2.05/examples/pitype/secr-auth/NeedhamSchroederPK-corr.pv` | environment sourced | the example's own published result block, exit 0 | exit 0, with the example's expected correspondence block emitted | reproduced | this checks the tool, not this repository's model; the model is a `not-run` row below |
| the D2 checkers reproduce their recorded output | `diff <(python3 src/ce_qs_quorum_family_checker.py) results/ce_qs_quorum_family_checker.txt` (and the trace-tag simulator the same way) | pinned profile, working directory `domains/02-ceqs-construction-evolution` | empty diff — byte-identical output | empty diff for both checkers; `IDENTICAL` | reproduced | run from this package because the tooling documents quote those runtimes; the domain's own `VERIFICATION.md` is the authority for the full set |
| forbidden-content scan of the tree, and of `tooling/` on its own | `python3 tooling/checks/scan-forbidden.py .` and `python3 tooling/checks/scan-forbidden.py tooling` | Python 3.12.3, from the repository root | 0 hits in all six categories | exit 0 both times: whole tree `files scanned: 644, findings: 0`; `tooling/` alone `files scanned: 12, findings: 0`; all six categories 0, and each run prints the note naming the one file it skipped | reproduced | the exemption — the scanner's own source, skipped by identity — and the findings an outside copy of the scanner reports instead are both in §4.3, which also records the minutes in which the rule table did not compile |
| every markdown link in the tree resolves | `python3 tooling/checks/check-links.py` | Python 3.12.3, from the repository root | not recorded before this pass — the checker was written for this repository | exit 0, `RESULT: PASS`: `markdown files: 214`, `link targets that do not resolve: 0 (0 distinct)`; the non-fatal code-span counts are in §4.3 | reproduced | the code-span half is deliberately not a pass/fail condition; §4.3 says why and what the two counts mean |

**Check counts of the layers whose runtimes this package quotes** — observed in the recorded logs
beside the scripts, not re-run here: the independent B0 vector check reports 6701 agreements and 0
disagreements across thirteen categories and a byte-identical diff against its archived results
(`elapsed_s: 19.36`); the fault-injection layer reports 300 schedules, 1717 checks, 3700 corruption
attempts, 0 accepted invalid certificates, 33 conflicts extracted, and `"verdict": "REPRODUCED"`;
the property summary records `tesla exit=0 :: 8 passed, 2 xfailed in 2.61s`,
`b0 exit=0 :: 12 passed in 6.56s`, `hashsig exit=1 :: 5 failed, 11 passed in 22.47s`,
`modeB exit=1 :: 2 failed, 14 passed in 110.09s (0:01:50)`; the mathematics result file records
eight groups `"verdict": "REPRODUCED"`; the primitives layer records `runtime 24.7 s` and its
Tamarin sibling records `processing time: 111.31s` with `TAMARIN_EXIT=0 ELAPSED=111` over twelve
lemmas.

## 4. Differences, and things a re-run will meet differently

### 4.1 `hsslms` and `dnspython` are installed here, and were not on the host that ran the audit

The recorded D10 runs were made where neither package was available: the S1 audit reports
`OK (skipped=2)` with `skipped 'hsslms not installed'` and `"independent_implementation": null`, and
every invocation of the DNSSEC script reports `ModuleNotFoundError: No module named 'dns'` and exits
1 after about a fifth of a second. The package index that describes the programme records those two
packages as "not installed on the host".

In the environment this repository instructs a reader to build, both are installed and importable
(§1). A re-run therefore produces **more** than the recorded run: the two skipped S1 tests execute,
and the DNSSEC layer produces a result for the first time. This is an availability difference and
nothing else — no cryptographic result in the repository changes — but it does mean that a re-run of
`domains/10-digital-infrastructure/src/audit_ledger.py` will not show the recorded `61/64` line, and a re-run of `domains/10-digital-infrastructure/src/s1_lms.py --self-test`
will not show `OK (skipped=2)`. Verdict: **reproduced-with-difference**. Recorded in `packages.md`
and in `imports.md` as well, because it is the difference most likely to be mistaken for a defect.

### 4.2 The superseded v0.1 simulator is not bit-reproducible

`domains/02-…/history/…_v0_1.py` draws quorums from an unseeded generator, so its recorded
`minimum observed quorum intersection=26` yields 24, 25 or 26 across runs. The bound on the same line
(`f + 1 = 22`) holds in every observed run and no later version depends on the line. The current
v0.2 simulator seeds everything and does reproduce byte-for-byte. Verdict:
**reproduced-with-difference** for the v0.1 line, **reproduced** for v0.2. Not a finding of this
package; recorded here so that the runtime tables in `run-everything.md` are not read as promising
a clean diff for a file that cannot give one.

### 4.3 The repository's own gates, run here against this repository

The four gate scripts were run from the repository root with the shipped copies, and the output below
is what they printed. The exact commands, so that a reader re-runs instead of quoting this file:

```sh
python3 tooling/checks/scan-forbidden.py .        # the whole repository
python3 tooling/checks/scan-forbidden.py tooling  # this package alone
python3 tooling/checks/verify-repository.py
python3 tooling/checks/check-links.py
```

**The scanner — clean, with one file exempt by construction.** Exit 0 in both runs; the figures here
are from the last run recorded in this pass (2026-09-13T17:22Z). Over the whole repository: `files
scanned: 644, findings: 0`. Over `tooling/` alone: `files scanned: 12, findings: 0` — the twelve
being this package's six markdown documents, `activate.sh`, the two files under `audit-stack/` and
the three other scripts under `checks/`; the scanner's own source is skipped, and it is the only file
in the package the run does not read. Every category is zero in both runs — `ai-name 0, ai-meta 0, abs-path 0, tracking 0,
contact 0, secret 0` — and each run prints the note naming the one file it did not read:

```
note: this scanner's own source was skipped by identity (/…/tooling/checks/scan-forbidden.py)
```

That file is the exemption, and it is the only one: the scanner's rule table necessarily contains the
literals it searches for — the alternation of assistant and vendor names, the machine-path rule, the
attribution and model-vocabulary phrases — so its own source cannot pass its own scan. It skips
itself **by identity** (`SELF = Path(__file__).resolve()`, set once ahead of the walk — line 94 at
the revision this pass measured), not by name and not by directory,
and it prints the note on every run so the exemption is visible rather than silent. A reader who
edits a copy of this repository can therefore move it, rename it, or point the scanner at a
directory of their own and the exemption still behaves the same way. The note is also the one line of
an otherwise clean run that carries a string the scanner's own `abs-path` rule forbids: it prints the
scanner's absolute path, so a transcript of a run — captured to a log, pasted into a file, committed —
is itself something a later scan of that file would flag. This document elides it (`/…/`), and a
reader archiving a run's output should do the same.

One consequence is worth stating because a re-run meets it, and because it is the shape of command a
reader may reach for first. The skip fires on the copy that is *executing*, so scanning this tree
with a copy of the scanner that lives somewhere else — which is what the recorded pass did, running
the build's own copy from outside the tree — does not skip
`tooling/checks/scan-forbidden.py`, because from that copy's position the shipped file is just
another file with a suspicious rule table in it. That run reports **10 findings, every one of them a
line of that one file**: 2 `ai-name` (the vendor-name alternation, and the temporary-directory
literal the path rule carries), 5 `ai-meta` (the rule-table comment lines and the
attribution/vocabulary alternation) and 3 `abs-path` (two rule-table comment lines and the path regex
itself — the third arrived with the widened tilde rule). This file names none of those literals,
deliberately: writing one here would put it back in the tree and the next scan would find it. The two
copies were byte-identical when that run was made — `diff` of the build's copy against the shipped
one exited 0 with no output — so what the outside copy reported was entirely a property of where the
scanner was standing, not of any content under `tooling/`. Pointed at this package by an outside
copy, the scan can never be clean; run as documented, from the repository root, it is, and it has
been since the shipped copy acquired the self-skip. Verdict: **reproduced** for the documented run,
clean at the moment it was taken. (The count of that block is not a constant: it tracks the rule
table's revision, because what the outside copy is reading is a file whose lines the rules match. A
scan of a later revision of the same file reported one `ai-name` line fewer, and the shipped copy has
since been edited again — see the paragraph after the next.)

**The two copies then stopped being identical, and the outside count did not move.** Re-run at
2026-09-13T17:31Z, the instructed command reports the same block — `files scanned: 13`, the same 2
`ai-name` / 5 `ai-meta` / 3 `abs-path`, exit 1 — but `diff` of the build's copy against the shipped
one now exits 1. The build copy (mtime 19:29:57 host-local, 17:29:57Z) has been rewritten so that its
rule table no longer
spells its names out: it carries two fragment lists and zips them into the alternation, and assembles
the scratch-directory prefix the same way, each with a comment saying why. The shipped copy still
spells them out. That the count is the same is the point worth keeping: the two rule tables match the
same strings, so what the outside copy reports was and remains a property of the *shipped* file's
text, not of the copy doing the reading. The byte-identity sentence above therefore describes the run
it was written for (2026-09-13T17:22Z), not the pair on disk now; a reader who repeats the `diff`
will get a difference and should read it as this paragraph, not as a fault.

**The shipped copy then caught up: the two are identical again, and the outside count is now 8.** The
build copy's fragment form was placed at `tooling/checks/scan-forbidden.py` at 2026-09-13T17:33Z, so
the pair is byte-identical again (`diff` exits 0; 8,973 bytes, sha256 `fdd11dc44d47138a…`) and the
window the paragraph above describes is closed. Re-run at that revision, the outside-copy scan
reports **8 findings — 5 `ai-meta` and 3 `abs-path`, and no `ai-name` line at all** — where the run
recorded above reported 2 / 5 / 3. Both `ai-name` findings are gone because the alternation the
shipped copy now carries is the fragment form: read across, the two rows are the twelve names, and
the scratch-directory prefix is assembled from the same first pair, so the file matches the same text
while its published bytes carry none of the names. That is why the change was made — a repository
whose rule is that a name must not appear in it should not carry the name in the one file that keeps
it out of everything else — and the rules themselves are unchanged: the assembled alternation and the
assembled prefix were compared against the literals they replaced, and match exactly the same strings
on a probe set that includes both the names and the near-misses the rule must not fire on. The
remaining 8 are structural and stay. A rule that matches a phrase has to contain the phrase, and both
remaining categories are matched against ordinary text — an attribution wording, a path prefix — that
a comment explaining the rule has reason to quote. So an outside copy still cannot report this
package clean, and now the whole of what it reports is the rule table and nothing else. The run to
quote remains the documented one from the repository root; and this repository's own integration gate
invokes the shipped copy rather than a copy held outside it, for exactly the reason these paragraphs
record.

**As this pass closed, the rule table was mid-edit and did not run at all.** A scan at
2026-09-13T17:25Z, a few minutes after the clean run above, stopped before reading anything:

```
  File "/…/tooling/checks/scan-forbidden.py", line 51, in <module>
    ("abs-path", re.compile(...
re.error: unbalanced parenthesis at position 113
```

Exit 1, raised while compiling the `abs-path` rule: an unfinished edit to its alternation, in a copy
whose modification time is minutes before the scan. It is recorded because it is the same class of
observable as everything else in this section, and because it is the state a reader may meet: the
scanner either prints counts or it does not, and a traceback means the rule table is being changed,
not that the tree is clean or dirty. So run the command before quoting any figure here — if it prints
counts, the figures above are what to compare against; if it prints this traceback, no scan evidence
exists from that moment, and the last clean run recorded here is the 17:22Z one. Verdict:
**not-reproducible** for the scan as the tree stood at 17:25Z, with the reason; the run recorded in
§3 and above is the one that stands until the next one.

The edit was finished about a minute later: scans at 17:26Z, with the rule table repaired, print
counts again — `tooling/` twelve files, 0 findings; the whole tree 644 files, 0 findings — so the
window is recorded as the transient it was, and a reader who sees counts can read this paragraph as a
state the tree has left.

Two bookkeeping notes for a reader comparing this file against the domain documents. Times here are
UTC, and at least one sibling document dates the same events in local time, which is UTC+02:00 in
this corpus: the 17:25Z break above is its 19:25 and the 17:26Z repair its 19:26 — one window, two
spellings, no disagreement. And the outside-copy case has a second, independent measurement, taken
in that same window and recorded in the domain-09 package: a scan of this tree run from outside it
with a locally repaired copy, reporting 646 files and 12 findings — ten of them lines of the shipped
scanner's own source (3 `ai-name`, 5 `ai-meta`, 4 `abs-path`, one line matching two categories at
once) and two in a transient `records/scrub-report.tsv` that had been removed again by the time it
was looked for. Nothing else in the tree fired. That is the same shape as the run above at a
different rule-table revision, measured by a different reader.

The repaired rule was then probed in both directions, because a rule edited in a hurry can come back
either broken or neutered. A throwaway file outside the tree carrying the tilde form of a project
directory on one line and a home-directory path on another produced **2 findings, both `abs-path`**,
while two control lines — an ordinary tilde path that names no directory under the home directory,
and a system path outside the two prefixes the rule carries — produced none. The widening therefore
catches the class it was widened for and still does not fire on ordinary prose.

The scanner's second boundary is what its rules match, and it earns one sentence because a reader
auditing a tree of their own will meet it: the rules match **names, phrases and shapes**, so a
sentence that describes a category without naming anything in it — a note that says a file "names AI
coding tools", say — passes by design. That is not a hole a wider rule should close: a rule matching
the description would match the description of the rules here too. It is the reason the fixed point
of scrubbing is to name nothing at all rather than to rely on a rule.

**Then the rule table was widened, and the tree stopped being clean for a while.** While this file
was being written, the scanner's owner extended the `abs-path` rule to catch the tilde form of a
machine path — a home directory followed by the two tree names this programme used — which names the
host that recorded the results just as `/home/<user>/` does. The first scan after the widening, run
from the repository root, reported:

```
files scanned: 613, findings: 8
  ai-name   0
  ai-meta   0
  abs-path  8
  tracking  0
  contact   0
  secret    0
```

Eight findings, all `abs-path`, in four files: `docs/01-research-journey/VERIFICATION.md` lines 14,
15, 22 and 23 (the prose sentence naming the host's repository root and its work directory, a `cmp`
command that spelled out where the source tree lives, and the command line of the scan itself);
`domains/02-ceqs-construction-evolution/VERIFICATION.md` lines 15 and 25 (the shell-setup row and
the entry-point fence); `domains/10-digital-infrastructure/VERIFICATION.md` line 28 (an activation
line); and `tooling/checks/verify-repository.py` line 15 — the one of the eight in this directory,
its `Usage:` block, whose example invocation carried the path. This file does not reproduce the
class of string here, deliberately: writing one would put it back in the tree and the next scan would
find it, which is exactly what happened once while this paragraph was being drafted.

All eight were corrected by the packages that own them, and the corrections are the kind a reader can
check: the activation lines became `. tooling/activate.sh`, which is the script that ships here and
the form a reader can run; the `docs/01` sentence now names the two directories by their role rather
than by the host's path; the `cmp` row states what was compared and points at the map row for the
digest, because a reader has the map and not the source tree; and the checker's `Usage:` line now
reads `[--repo DIR]`, which is what it always meant. The re-run after those corrections, the last one
recorded here:

```
files scanned: 613, findings: 0
  ai-name   0
  ai-meta   0
  abs-path  0
  tracking  0
  contact   0
  secret    0
  note: this scanner's own source was skipped by identity (…/tooling/checks/scan-forbidden.py)
```

Exit 0. That was the figure at the time; the tree grew while the rest of this package was written,
and a re-run over it reports `files scanned: 644, findings: 0`. The command is the thing to trust
over this paragraph — run it — but the numbers above are the figures to compare against if it does
not agree.

**The map gate — passes.** Exit 0, at the last run recorded here (2026-09-13T17:20Z, from the
repository root, shipped checker, default paths). The summary block, verbatim:

```
map rows:                 1369 (copy 439, excluded 930)
files present in repo:    668
claimed new_paths:        439
missing from repo:        0
sha256 differences:       0 (explained by rewrites: 132)
authored documents:       184 (expected, not in the map)
UNEXPLAINED files:        0
empty files:              0
malformed map rows:       0
RESULT: PASS
```

Read it as the four questions it exists to answer. Every copy row is present at its destination at
the digest the map records (`missing from repo: 0`). Nothing is here that neither the map nor the
repository's own documents account for (`UNEXPLAINED files: 0`). No file is empty. No map row is
malformed. And every digest difference it found is one the rewrites table already documents. The
`sha256 differences` line prints the count it could **not** explain first and the count it could in
brackets, so the number to read is the `0`, and `explained by rewrites: 132` is the size of the
explained set. `authored documents` counts the files the map does not list because this repository
wrote them — this package's documents among them — and it moves as documents are written; it is not a
failure. **No line in the output names anything under `tooling/`.**

**It did not pass when this section was first drafted, and the reason is kept here.** The earlier
run, on a tree a few files smaller, reported:

```
files present in repo:    654
sha256 differences:       131 (explained by rewrites: 1)
authored documents:       171 (expected, not in the map)
RESULT: FAIL
```

Exit 1, and the one line it objected to was the digest line. Behind that line: the gate separates
digest mismatches into those it can match against a rewrites row (printed as `explained by rewrites`)
and those it cannot (printed first, as the number before the bracket, and listed as `HASH` lines).
Its own source says what it expects — it builds a set from column 2 of `records/rewrites.tsv`, and
the comment on the line that does the comparison reads "rewrites.tsv names the destination path,
which is what the repository holds". In the table as it stood then, column 2 held **source-tree
names** instead: 169 names, of which our own check found exactly one that is a map destination (the
`tooling/audit-stack/Dockerfile.math` row, whose source and destination happen to be spelled
identically). So 130 recorded rewrites — every one of them a legitimate, intended difference the
table documents in full, with a reason and a file — could not match anything the gate compared them
to, and were counted as unexplained digest drift. That is how a gate can FAIL while `UNEXPLAINED
files` and `empty files` are both 0 and `missing from repo` is 0: a tree with no unexplained file can
still report 131 unexplained hashes if the table and the gate disagree about what column 2 means.

It was a disagreement between two packages that have to move together — the gate and the table are
owned separately — and it was reported to both owners with this evidence rather than fixed from
here, because a gate that FAILs on a clean tree is how a real failure gets ignored later. It has
since been resolved on the **table side**, with no change to the gate program: `records/rewrites.tsv`
now keys column 2 by the destination path, which is what the checker's own comment says it expects,
so a reader following a name lands on a file this repository holds. The exception is stated by the
table and is five names long — the files the map does not carry over, three marked `exclude-triad`
(the two devnet tarballs and `TRIAD_System_Explained.docx`) and two marked `source-only` (the
`prior-setup` transcripts) — which keep their original spelling because they have no destination to
name, and a name that resolves to nothing can never match a repository path. Between them, the 267
data rows carry 511 names: 506 repository paths and those five. `records/README.md` describes the
table from its own side — 267 rows, 163 `[mechanical]` / 72 `[judgement]` / 32 `[no-rewrite]` — and
its figures and the ones here agree at the revision both were measured against. One detail is worth
knowing before anyone counts rows again: five of the 267 *begin* with `#`, because the text they
quote was a shell comment, so a count that skips `#`-leading lines gives 262. That is what this file
first recorded, and it was wrong; the table's only non-row line is the banner above the header.

Nothing under `tooling/` is in a `HASH` list at either run, so this package's own record is
unaffected — but its reading of the gate would be wrong without this paragraph, which is why the
paragraph is here.

Verdict: **reproduced** — the shipped checker, run as documented from the repository root, exits 0 and
PASSes on this tree, and the `Dockerfile.math` change §4.4 describes is among the 132 differences it
explains. The FAIL above is kept as the state it replaced, together with the mechanism, because the
next reader of that digest line is the one who needs to know what it counts.

**The redactor — starts and passes, and did not start at first.** Run with both paths given, as the
table requires:

```
$ python3 tooling/checks/redact-for-publication.py --in records/rewrites.tsv --out /tmp/rewrites.public.tsv
rows: 268, rows with redaction: 0, spans redacted: 0
wrote /tmp/rewrites.public.tsv
RESULT: PASS -- no rule matches anything the table publishes
```

Exit 0. `rows with redaction: 0` is the right answer for *this* table rather than a sign the script
did nothing: `records/rewrites.tsv` as published **is** the redacted artifact, so a second pass over
it has nothing left to replace, and what the line reports is that no span of it matches the
forbidden-content rules — the property the table is supposed to have. (`rows: 268` is a line count, not
a finding count, and it is one line off the table's own makeup: the table's 269 lines are a banner
line, the four-column header, and 267 data rows, while the script treats line 1 as its header and
subtracts exactly one, so its 268 is the 267 data rows plus the header it counted. Run the script
over an unredacted copy and `rows with redaction` is the figure that moves, not this one.)

**What it did at first**, kept because the correction is the evidence that the report was acted on:
exit 1, before reading anything, with

```
  File "/…/tooling/checks/redact-for-publication.py", line 30, in <module>
    from scan_forbidden import RULES  # noqa: E402  (same directory, same rules, one definition)
ModuleNotFoundError: No module named 'scan_forbidden'
```

The file beside it is named `tooling/checks/scan-forbidden.py`, and a hyphenated name is not
importable, so the import could not resolve in this tree; the same failure occurred with the default
paths, so it was the import and not the arguments. Nothing was redacted and no output file was
written. The script belongs to the package that owns `checks/`, and this was reported to it with the
traceback rather than repaired here, because a silent edit to a file that package placed would change
what that package believes it shipped. One default still does not fit this tree: `--in`/`--out`
resolve under `tooling/maps/`, which does not exist here, and invoked with no arguments the script
stops on `FileNotFoundError` naming `tooling/maps/rewrites.tsv` — so pass both paths explicitly, as
above. Verdict: **reproduced** for the script as it now stands; the traceback is the state it
replaced.

**The link checker — clean on the part that decides the exit status.** Exit 0, `RESULT: PASS`:

```
markdown files: 214
link targets that do not resolve:       0 (0 distinct)
code-span names resolved from a directory named in the same paragraph: 168
code-span names not in this repository: 841 (390 distinct)
  ... of which the file map lists the source: 574 (246 distinct)
  ... and which the map does not list either: 266 (144 distinct)
```

These are the last run of this pass (2026-09-13T17:33Z). The two that decide whether this file is
telling the truth are the first two lines, which are zero and passed; the code-span numbers below them
are a running count over a tree that was still being written, and this document is inside the count —
its own code spans are scanned like anyone else's, so the pair here (166 and 835 (385) in the run
before this one) can grow between runs with nothing else in the package changing at all.

Every markdown link in the repository resolves. The code-span counts are not a pass/fail condition
and this tool says so itself. Of its three lines, the first counts names the checker did resolve, by
reading a directory named in the same paragraph; the second counts names the map records as
*sources*, absent because they are what a copy was made from; and the third includes names that are
relative to a domain rather than to the tree — this package's own recipe runs
`python3 src/s1_lms.py --self-test` from `domains/10-digital-infrastructure` and names the script
bare in the prose beside it, which is how the recorded run invoked it and is left as it was recorded.
Verdict: **reproduced**.

All four output blocks are snapshots, taken while other packages were still landing files, and every
one of their numbers moved while this file was being written. The map gate's `files present in repo`
went 646 → 654 → 668 and its `authored documents` 171 → 184 as documents landed; `empty files` went
1 → 0 as the hidden-signers domain filled its empty result; `UNEXPLAINED files` 2 → 0; and its
`sha256 differences` went 131 → 132 → 131 → 0, with `RESULT: FAIL` becoming `RESULT: PASS` once the
rewrites table was re-keyed by destination. The scanner's whole-tree count went 613 → 644 and its
`tooling/` count 11 → 12, and its rule table spent part of the pass not compiling at all. The link
checker was extended mid-pass (it now prints a bucket for names resolved from a directory named in
the same paragraph, and its code-span counts move with every document anyone writes, this one
included). A reader should run the four commands rather than compare against these numbers, and
should read a non-zero exit by the rule in `README.md` — the gate names what it objects to, and the
question is only whether any of those names is in the package being checked.

### 4.4 The one file under `tooling/` no gate used to read — and how that was closed

`tooling/audit-stack/Dockerfile.math` carried, in a comment on its third line, an example invocation
with an absolute host path for the read-only research tree. A file the scanner never opens is the one
place a forbidden string can sit while a scan still reports clean, and at that time this file was
exactly that: the scanner reads files by suffix, `.math` was not in its text set, so the file was
never examined — not when the scan above reported clean, and not in any run before it.

The path itself is gone. It was found by reading the file, since no gate looked at it; it was reported
to the file's owner rather than edited here, because a silent edit would put the file's digest out of
step with the map without a row explaining why; and the owner has since redacted it — the example
`docker run` line now mounts the tree at `/src` and passes `PQT_SRC=/src`, which is what
`environment.md` §8 documents. It was the only occurrence of its kind recorded under `tooling/`.

The gap is closed, by the package that owns the scanner: `.math` is in the scanner's suffix set (the
set's own comment names `Dockerfile.math` as the case it was added for), so this file is now read by
every scan. Observed here three ways at once — the suffix appears in the set in
`tooling/checks/scan-forbidden.py`; the scanner pointed at that single file reports `files scanned: 1,
findings: 0`; and the whole-package scan counts it among the twelve files it reads. Nothing in it
matches any of the six categories, so the file is clean under the wider set as well as by eye.

What survives the correction is the shape of the boundary, which is worth a reader's attention
because it applies to whatever they add: a file is read *because its suffix is in the set*, so a file
whose suffix is not — a format nobody thought of, or one you introduce — is published unexamined.
`environment.md` §8 says the same for this directory. Verdict: **reproduced** — the file is read by
the scanner and the scan of it is clean; the earlier state, in which no gate result could be read as
evidence about this file, is kept above as the state it replaced.

What a reader needs to know: the mount in that comment is an example, and nothing in the build
depends on where the tree sits. Mount the read-only tree wherever you keep it, and pass the location
in the documented environment variable;
the mathematics layer raises `SystemExit` with a one-line message if it is unset, so a wrong or
absent value fails loudly rather than guessing. Keeping the working directory stable also keeps the
mathematics results comparable, since the layer records paths inside its own output.

## 5. Not run, and why

| item | command that would run it | environment | expected (recorded) | observed | verdict | notes |
|---|---|---|---|---|---|---|
| TLA+ model checking of the epoch-barrier invariants | `tlc … epoch-barrier.tla` | any with a JVM and `tla2tools.jar` | the invariants hold; the recorded alternative is an independent enumeration script | not run | not-run | no TLA+ tools and no pinned Java here; the claim is carried by the enumeration checker in the domain instead, and the domain says so |
| EasyCrypt refinement check | `easycrypt frame_b0.ec` | EasyCrypt | the recorded file is an `admit`ted skeleton and was never checked | not run | not-run | EasyCrypt is not installed; the file's status is recorded by its own domain and must not be read as a completed proof |
| NIST ACVP conformance vectors | `python3 domains/11-independent-audit-stack/primitives/cross_validate.py` | pinned profile, with the five vector files present | 6701 comparisons from the vector tables, no disagreements | not run | not-run | the five `internalProjection.json` files are not redistributed; `vectors/SOURCE.txt` records the upstream commit and each file's digest |
| This repository's ProVerif model | `proverif domains/11-independent-audit-stack/formal/qpt128_quorum.pv` | ProVerif 2.05 | none recorded — the recorded full-stack run shows `ProVerif NOT RUN (proverif not on PATH)` | not run for this repository's model | not-run | ProVerif itself was verified here on a distribution example (§3); the model was not re-proved, and no result is claimed for it |
| Tamarin on the larger instantiation | `tamarin-prover --prove formal/qpt128_quorum_n7.spthy` | Tamarin 1.12.0, Maude 3.5.1 | does not terminate in the recorded budget: the batch run was stopped at 1,200 s, and the per-lemma run leaves four lemmas with no result after timeouts of 266–420 s | not run to completion | not-run | recorded as a gap by the domain, not as a proof of the missing lemmas |
| Sanitizer and fuzz layers | the scripts under `implementation/` | clang with sanitizer and libFuzzer runtimes | as recorded in the domain's implementation results | not run | not-run | one recorded production-parameter run timed out; the layer's results are recorded evidence, not a promise that the recipe completes in a stated time |
| Docker full-stack image | `docker build -f tooling/audit-stack/Dockerfile .` | Docker | never built by the recorded pass | not run | not-run | the mathematics container was built and run and records all eight groups reproduced; the full-stack image is untested; `Dockerfile.math` is read by the scanner like any other text file, and the boundary that remains is a suffix the scanner's set does not list (`environment.md` §8, `VERIFICATION.md` §4.4) |
| SageMath, KLEE, AFL++, valgrind, opam, CryptoMiniSat | — | — | planned or depended on, never run | not run | not-run | listed with reasons in `environment.md` §8; CryptoMiniSat in particular has no recorded version, and the conclusion resting on it is recorded as inconclusive by the domain that made it |
| the Binius64 adapter binaries | — | AVX-512 capable CPU | recorded sizes and transcripts, produced by binaries that never ran on the audit host | not run | not-run | the binaries contain AVX-512 instructions; rebuilding them changes their digests, and re-running them here is impossible |

## 6. What this file does not claim

It does not claim that the cryptography is sound, that the recorded numbers are the right numbers to
have measured, or that any layer is free of the defects its own domain records. It records the
versions this environment provides, the checks that were re-run against them, and the exact
differences between a fresh run and the recorded one — which is what a reader needs in order to
decide whether a re-run reproduced the work.
