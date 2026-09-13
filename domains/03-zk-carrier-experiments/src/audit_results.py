#!/usr/bin/env python3
"""Check retained evidence, the exact field, and the proof-component accounting.

This is an evidence audit, not a cryptographic security theorem. Public proof
verification is performed separately by verify_public.py.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAIN = HERE.parent
FIXTURES = DOMAIN / "fixtures"
RESULTS = DOMAIN / "results"
HISTORY = DOMAIN / "history"

# Version 1.27b's own run directory was split by the file map: its frames are the
# frames are the shared fixture (the .pt27 and .pf27 suffixes keep them apart),
# its check_case*.json outputs are the domain's retained results,
# and the rest stayed with the version.  Later generations have their own frame
# suffix and their own negative-control count.
FRAMES = {"1.27": FIXTURES, "1.27b": FIXTURES}
CHECKS = {"1.27": HISTORY / "v1.27", "1.27b": RESULTS}
CHECK_NAME = {"1.27": "check_case{}.json", "1.27b": "check-case{}.json"}


def poly_rem(a, b):
    while a.bit_length() >= b.bit_length():
        a ^= b << (a.bit_length() - b.bit_length())
    return a


def field_certificate():
    modulus = (1 << 512) | 0x125
    x, middle = 2, None
    for degree in range(1, 513):
        x = poly_rem(sum(1 << (2*j) for j in range(x.bit_length()) if x >> j & 1), modulus)
        if degree == 256:
            middle = x
    a, b = middle ^ 2, modulus
    while b:
        a, b = b, poly_rem(a, b)
    assert x == 2 and a == 1
    return {"polynomial_tail": 293, "frobenius_512_equals_x": True,
            "gcd_x_2pow256_minus_x": a, "degree_prime_divisors": [2], "irreducible": True}


def main():
    rows = []
    for version in ("1.25", "1.27", "1.27b"):
        root = HISTORY / ("v" + version)
        for case in ("case0", "case1"):
            d = json.loads((root / f"encode_{case}.json").read_text())
            c = d["codec"]
            boundary = sum(s.get("boundary_hashes", 0) for s in c["sections"]) * 32
            scalars = sum(s.get("transmitted_scalars", 0) for s in c["sections"]) * 16
            terminal = sum(s.get("terminal_encoded_bytes", 0) for s in c["sections"])
            fixed = c["header_bytes"] + c["native_prefix_bytes"] + terminal
            assert fixed + boundary + scalars == c["encoded_bytes"]
            assert c["encoded_bytes"] + 5712 == d["frame_bytes"]
            rows.append(dict(version=version, case=case, gates=d["stats"]["n_gates"],
                             committed_allocated=d["stats"]["committed_allocated"],
                             native_proof_bytes=d["native_proof_bytes"],
                             encoded_proof_bytes=c["encoded_bytes"], frame_bytes=d["frame_bytes"],
                             boundary_hash_bytes=boundary, transmitted_scalar_bytes=scalars,
                             fixed_and_terminal_bytes=fixed,
                             hypothetical_proof_bytes_if_boundary_hashes_cost_zero=fixed+scalars))
    for version, suffix, binary in (("1.27", "pt27", "ceqs-paired-trace-v127"),
                                     ("1.27b", "pf27", "ceqs-fixed-pair-v127b")):
        root = HISTORY / ("v" + version)
        public = json.loads((root / "public_verification.json").read_text())
        assert public["recovered_indices"] == list(range(22))
        assert public["qpt_128_qualified"] is False
        assert public["complete_32KiB_QCs_accepted"] == 0
        built = root / "bin" / binary
        if built.is_file():
            assert public["binary_sha256"] == hashlib.sha256(built.read_bytes()).hexdigest()
        else:
            print("note: compiled binary is excluded from this repository, so the recorded "
                  "binary_sha256 was not re-derived:", built, file=sys.stderr)
        for j, frame in enumerate(public["frames"]):
            path = FRAMES[version] / f"case{j}" / f"trace43_rate3.{suffix}"
            raw = path.read_bytes()
            assert len(raw) == frame["frame_bytes"]
            assert hashlib.sha256(raw).hexdigest() == frame["sha256"]
            assert frame["native_verified"] and frame["all_proof_bytes_inline"]
            assert not frame["private_input_opened"] and not frame["complete_QC_accepted"]
            assert not (path.parent / "PRIVATE_TRACE_WITNESS.bin").exists()
            check = json.loads((CHECKS[version] / CHECK_NAME[version].format(j)).read_text())
            assert len(check["constraint_checks"]) == 11
    negative = json.loads((HISTORY / "v1.27b" / "public_negative_checks.json").read_text())
    assert negative["checks_passed"] == 18
    assert "domain_rebound_in_frame_and_config" in negative["rejected"]
    assert "registry_rebound_in_frame_and_config" in negative["rejected"]
    result = dict(scope="RETAINED_EVIDENCE_AND_ALGEBRA_AUDIT_NOT_SECURITY_PROOF",
                  field_certificate=field_certificate(), comparisons=rows,
                  complete_original_goal_QCs=0,
                  cost_diagnosis_scope="Only these retained transcripts under the unchanged QVT1 representation; not a protocol lower bound.")
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "evidence-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
