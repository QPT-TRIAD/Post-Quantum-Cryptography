# The independent B0 implementation, and its specification gaps

`independent-b0/b0_indep.py` is an implementation of CE-QS profile B0 (the v1.44 frame format)
written **from `B0_wire_spec_v1.44.md` alone**, with no reference source consulted; Python 3.12
standard library only. Its own header states the rule it was built under: "Section numbers in
comments refer to the spec. Every place where I had to choose an interpretation is marked
'GAP:' and listed in SPEC_GAPS.md."

This is the strongest independence claim in the domain, and it is a claim about *method*: the
implementer held the specification and the vectors, not the reference code — but the same programme
wrote the specification, the reference and the audit. See `README.md`.

## 1. How the vectors were produced, and why that is not circular

`independent-b0/gen_b0_vectors.py` runs the **reference** module
(`sidecar_free_certificate_v1.44.py`, imported read-only from the research tree) to emit
`b0_vectors.json`: 900 cases covering conflicts, non-conflicts, malformed frames and cross-domain
cases, each with the reference's own `encode` output, `extract` result, `verify` verdicts and blame
verdicts. `independent-b0/check_vectors.py` then runs the spec-only implementation against that file
and never modifies it. The circularity is exactly this: the vectors are the reference's answers.
What is being tested is therefore **agreement of an independent reading of the specification with
the reference**, not agreement of two independent implementations of a cryptographic scheme.

## 2. Recorded result

`independent-b0/independent_results.json` and `INDEPENDENT_RESULTS.md`:

| category | agree | disagree |
|---|---:|---:|
| cfg | 1 | 0 |
| conflict.blame | 3,200 | 0 |
| conflict.encode | 800 | 0 |
| conflict.extract | 400 | 0 |
| conflict.verify | 800 | 0 |
| conflict.verify_fields | 800 | 0 |
| mutated.verify | 100 | 0 |
| other-domain.blame_all_false (spec-derived) | 100 | 0 |
| other-domain.extract | 100 | 0 |
| same-message.blame_all_false (spec-derived) | 100 | 0 |
| same-message.extract | 100 | 0 |
| trailing.verify | 100 | 0 |
| truncated.verify | 100 | 0 |
| **total** | **6,701** | **0** |

Every frame re-encoded byte-for-byte; every `verify` / `extract` / `blame` verdict matched.
Rejection clauses hit: `mutated` → {§7.7: 93, §7.4: 7}; `truncated` → {§7.3: 100}; `trailing` →
{§7.3: 100}. Recorded runtime: 9.6 s.

Re-run for this repository, in a sandbox: the produced `independent_results.json` is **equal** to
the recorded file (deep comparison of every category and count), exit 0.

## 3. The eighteen specification gaps

Recorded in `independent-b0/SPEC_GAPS.md` while implementing from the text. Four are marked
**[observable]** — they can change wire bytes or verdicts:

1. **§6 bitmap bit numbering.** "bit i" — value bit `2^i` (LSB = seat 0) or the i-th bit of the
   big-endian byte string (MSB-first)? The chosen reading is the value bit, serialised as u64 BE;
   the other reading would produce different bytes for every frame.
2. **§6 `encode` has no secret-key input.** §5 defines `sk_i` by index (`b"SK" ‖ u16be(i)`) while
   the toy `verify` derives `sk` from the registry pk — these coincide only for `pk_i = b"PK" ‖
   u16be(i)`. For a permuted or non-canonical registry the spec gives no rule.
3. **§5 toy `verify` prefix check.** The text says to recompute with `sk = b"SK" ‖ pk[2:]` but never
   says to check `pk[:2] == b"PK"`, so a pk such as `b"ZZ\x00\x05"` verifies seat-5 signatures. The
   implementer followed the text literally (no check).
4. **§10 vector-file format.** §10 describes per-case `registry` and a single `frame`; the actual
   file has one top-level `registry`/`cfg` and cases with `frame0/frame1`, `message0/message1`,
   `seats0/seats1`, `kind`, `expected_extract`, `expected_verify`. Public keys are hex but
   `scheme_id` is a plain string whose encoding is unspecified.

The remaining fourteen affect API shape or unreachable branches: the form of a rejection (raise vs
return `None`/`False`); whether a "byte string" includes `bytearray`/`memoryview`; the type of
`expected_cfg`; whether `seat` accepts `bool` (an `int` subclass) or `3.0`; the error type for
non-bytes parts; where registry validation happens; two redundant clauses (§7.5 vs §7.3, §8.2/§8.3
unreachable for two valid frames); check ordering; plain concatenation in §4/§5 vs length-prefixed
`H` in §2/§3; the implicit bound `W ≤ 757` and who must reject oversize frames; `MAX_FRAME_BYTES`
being inert for the toy provider; and "constant width 32" meaning a constant-time compare.

All four observable gaps were resolved normatively in the specification's §11 after the exercise;
gap 3 is recorded as a deliberate literal reading, not a defect the implementation fixed.

## 4. What this establishes, and what it does not

- **Establishes:** the extraction rule, the blame rule, the encoding and the rejection clauses of B0
  are determined by the specification closely enough that an implementer who never saw the
  reference reproduces them — including every rejection clause hit by malformed input.
- **Does not establish:** anything about the reference's *cryptography* (both sides use the same
  symbolic signature double), and nothing about the parts of the construction that B0 does not
  contain. It is not a second implementation of QPT-128; it is a second implementation of one wire
  format. The full second implementation of the construction remains open.
- **A specification that lets two implementations agree by luck is a defect even when they agree** —
  which is why the four observable gaps are recorded as findings (S1–S4) of this domain rather than
  as implementation trivia.
