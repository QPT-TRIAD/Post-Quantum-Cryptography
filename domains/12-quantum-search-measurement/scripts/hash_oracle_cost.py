#!/usr/bin/env python3
"""What one SHA-256 oracle query costs, read off a verified circuit, beside the assumed 2^18.

The infrastructure record prices every hash-based component with ``n/2 - log2(T)/2 + 18``: the last
term is an assumed ``2^18`` gates per hash-oracle query, used as a *floor* — an adversary with a
``2^128`` gate budget is allowed ``2^128 / 2^18`` queries and no more. ``scripts/infra_campaign.py``
measures the other two terms and says it cannot reach this one. This script reaches it: it builds
the reversible SHA-256 of :mod:`grover_emulator.circuits.sha256_circuit`, re-verifies it against
``hashlib`` in this very run, and reports exact counts for one hash and for one Grover oracle query
(hash, compare, un-hash) on the record's own LM-OTS chain step.

**The direction of the inference, which is easy to get backwards.** A circuit that has been built
is an *upper* bound on the cost of hashing: it shows the job can be done for this much. The record
needs a *lower* bound: that it cannot be done for less than ``2^18``. No construction proves a lower
bound. What a construction can show is whether the assumed floor is consistent with the cheapest
circuits anyone has exhibited, and by what margin — and that margin is the finding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grover_emulator.circuits.sha256_circuit import (  # noqa: E402
    PUBLISHED_AMY_2016,
    build_sha256_compression,
    build_sha256_preimage_predicate,
    pad_single_block,
)
from grover_emulator.reporting.report_generator import SCOPE_BOUNDARY  # noqa: E402
from grover_emulator.utils.wide_simulation import (  # noqa: E402
    pack_columns,
    simulate_bitsliced,
    unpack_register,
)

ASSUMED_LOG2_GATES_PER_QUERY = 18
RECORD_WHERE = ("pq_infra_s4_embedded_broadcast_v2.0.py:102; pq_audit_s1_lms_v2.2.py:286; "
                "pq_audit_s2_dns_worstcase_v2.1.py:455; QPT128_finalization_v1.43.md:72")

#: Seven T, six CNOT and two H: the standard ancilla-free Clifford+T Toffoli. Named because every
#: "total gates" figure below depends on it, and a reader with a different Toffoli can redo the sum.
TOFFOLI_AS_CLIFFORD_T = {"t": 7, "cx": 6, "h": 2}
LMOTS_PREFIX = b"I" * 16 + (3).to_bytes(4, "big") + (5).to_bytes(2, "big") + (0).to_bytes(1, "big")


def verify(gl, layout, samples: int = 64) -> int:
    """Digests matching hashlib out of ``samples`` random one-block messages, checked in this run."""
    rng = random.Random(20260921)
    messages = [rng.randbytes(rng.randrange(56)) for _ in range(samples)]
    blocks = [pad_single_block(m) for m in messages]
    registers = [(layout.message[j], [int.from_bytes(b[4 * j: 4 * j + 4], "big") for b in blocks])
                 for j in range(16)]
    out = simulate_bitsliced(gl, pack_columns(gl.num_qubits, registers), samples)
    words = [unpack_register(out, layout.digest[w], samples) for w in range(8)]
    got = [b"".join(words[w][j].to_bytes(4, "big") for w in range(8)) for j in range(samples)]
    return sum(g == hashlib.sha256(m).digest() for g, m in zip(got, messages))


def costs(gl, *, mcx_controls: int = 0) -> dict:
    counts = gl.counts()
    toffolis = gl.toffoli_equivalent()              # an MCX with c controls taken as c - 1 Toffolis
    clifford_t_total = (toffolis * sum(TOFFOLI_AS_CLIFFORD_T.values())
                        + counts.get("cx", 0) + counts.get("x", 0))
    t_count = 7 * toffolis
    out = {
        "qubits": gl.num_qubits,
        "as_built": {k: v for k, v in counts.items()},
        "toffoli_equivalent": toffolis,
        "t_count_at_7_per_toffoli": t_count,
        "clifford_t_total_gates": clifford_t_total,
        "log2": {
            "as_built_total_gates": math.log2(counts["total"]),
            "t_count": math.log2(t_count),
            "clifford_t_total_gates": math.log2(clifford_t_total),
        },
        "provenance": "counted on a gate list verified against hashlib in this run",
    }
    if mcx_controls:
        # Amy et al.'s own figure for the k-fold controlled NOT, 32k - 84 T, in place of 7(k - 1).
        alt = t_count - 7 * (mcx_controls - 1) + (32 * mcx_controls - 84)
        out["t_count_with_published_mcx_cost"] = alt
        out["log2"]["t_count_with_published_mcx_cost"] = math.log2(alt)
    return out


def margin(log2_value: float) -> float:
    return round(log2_value - ASSUMED_LOG2_GATES_PER_QUERY, 2)


def build_results() -> dict:
    hash_gl, layout = build_sha256_compression()
    verified = verify(hash_gl, layout)
    if verified != 64:
        raise SystemExit(f"the circuit matched hashlib on {verified}/64 messages; refusing to count it")

    target = hashlib.sha256(LMOTS_PREFIX + bytes(32)).digest()
    oracle_256, *_ = build_sha256_preimage_predicate(LMOTS_PREFIX, 32, target, image_bits=256)
    oracle_192, *_ = build_sha256_preimage_predicate(LMOTS_PREFIX[:23], 24, target, image_bits=192)

    published = PUBLISHED_AMY_2016
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "assumed_log2_gates_per_query": ASSUMED_LOG2_GATES_PER_QUERY,
        "record_where": RECORD_WHERE,
        "verified_digests": f"{verified}/64",
        "toffoli_as_clifford_t": TOFFOLI_AS_CLIFFORD_T,
        "one_hash": costs(hash_gl),
        "oracle_query_n32_image256": costs(oracle_256, mcx_controls=256),
        "oracle_query_n24_image192": costs(oracle_192, mcx_controls=192),
        "published": published | {
            "log2_sha256_t_count_optimised": math.log2(published["sha256_t_count_optimised"]),
            "log2_sha256_oracle_t_count": math.log2(published["sha256_oracle_t_count"]),
            "log2_sha3_256_t_count_optimised": math.log2(published["sha3_256_t_count_optimised"]),
            "provenance": "published (read from the paper's tables; not derived here)",
        },
    }


def render(r: dict) -> str:
    h, q, q192, p = (r["one_hash"], r["oracle_query_n32_image256"],
                     r["oracle_query_n24_image192"], r["published"])
    cheapest_query = min(q["log2"]["as_built_total_gates"], p["log2_sha256_oracle_t_count"])

    def row(label, c, key, basis):
        return (f"| {label} | {basis} | {c[key] if key in c else '—':,} | "
                f"{c['log2'][LOG2_KEY[key]]:.2f} | {margin(c['log2'][LOG2_KEY[key]]):+.2f} |")

    out = [
        "# What one SHA-256 oracle query costs — counted on a verified circuit",
        "", SCOPE_BOUNDARY, "",
        "**What this adds to that boundary.** Nothing here is a fault-tolerant cost: there is no "
        "error correction, no magic-state distillation, no depth limit. These are logical gate "
        "counts of one explicit circuit. And a built circuit is an **upper** bound on the cost of "
        "hashing, while the record uses 2^18 as a **lower** bound on it — so this report can show "
        "whether the floor is consistent with the cheapest known circuits, and cannot prove it.",
        "",
        f"The record's assumption: 2^{r['assumed_log2_gates_per_query']} gates per hash-oracle "
        f"query ({r['record_where']}).",
        "",
        f"**The circuit was verified before it was counted:** {r['verified_digests']} random "
        f"one-block messages hashed to the `hashlib` digest in this run. {h['qubits']} qubits; "
        f"as built, {h['as_built'].get('ccx', 0):,} Toffoli, {h['as_built'].get('cx', 0):,} CNOT, "
        f"{h['as_built'].get('x', 0):,} X.",
        "",
        "## Counted — this circuit",
        "",
        "| object | metric | count | log2 | margin over 2^18 (bits) |", "|---|---|---|---|---|",
        row("one hash", h, "as_built_total", "gates as built (X/CNOT/Toffoli)"),
        row("one hash", h, "t_count_at_7_per_toffoli", "T-count, 7 T per Toffoli"),
        row("one hash", h, "clifford_t_total_gates", "all Clifford+T gates"),
        row("one oracle query, n = 32", q, "as_built_total", "gates as built"),
        row("one oracle query, n = 32", q, "t_count_at_7_per_toffoli", "T-count, 7 T per Toffoli"),
        row("one oracle query, n = 32", q, "clifford_t_total_gates", "all Clifford+T gates"),
        row("one oracle query, n = 24", q192, "t_count_at_7_per_toffoli", "T-count, 7 T per Toffoli"),
        "",
        "An oracle query is hash, compare, **un-hash**: a Grover iteration cannot leave the digest "
        "behind, so it pays for the hash twice. One hash is half a query.",
        "",
        "## Published — Amy et al., SAC 2016 (not derived here)",
        "",
        "| object | metric | count | log2 | margin over 2^18 (bits) |", "|---|---|---|---|---|",
        f"| one SHA-256 hash | T-count after T-par | {p['sha256_t_count_optimised']:,} | "
        f"{p['log2_sha256_t_count_optimised']:.2f} | {margin(p['log2_sha256_t_count_optimised']):+.2f} |",
        f"| one SHA-256 oracle query | T-count, eq. (9) | {p['sha256_oracle_t_count']:,} | "
        f"{p['log2_sha256_oracle_t_count']:.2f} | {margin(p['log2_sha256_oracle_t_count']):+.2f} |",
        f"| one SHA3-256 hash | T-count after T-par | {p['sha3_256_t_count_optimised']:,} | "
        f"{p['log2_sha3_256_t_count_optimised']:.2f} | "
        f"{margin(p['log2_sha3_256_t_count_optimised']):+.2f} |",
        "",
        "## What follows, and what does not",
        "",
        f"- **Per oracle query the floor holds against every figure here**, counted or published. "
        f"The cheapest is 2^{cheapest_query:.2f}, a margin of {margin(cheapest_query):+.2f} bits. "
        "That is under one bit: the floor is consistent with the cheapest circuits exhibited, not "
        "comfortably below them.",
        "- **Per single hash evaluation the floor does not hold.** The published optimised SHA-256 "
        f"T-count is 2^{p['log2_sha256_t_count_optimised']:.2f}, and this circuit as built is "
        f"2^{h['log2']['as_built_total_gates']:.2f} gates — both below 2^18. The record is safe on "
        "this point only because what Grover calls is the query, not the hash; any ledger line that "
        "charges 2^18 to a *single classical-style hash evaluation* inside a quantum attack would "
        "be charging too much.",
        "- **The floor cites a SHA3-256 figure (499,200 T) but is applied to SHA-256 components.** "
        "For SHA3-256 one hash alone clears 2^18 by "
        f"{margin(p['log2_sha3_256_t_count_optimised']):+.2f} bits; for SHA-256 it takes the whole "
        "query to clear it.",
        "- **Not shown:** that no cheaper circuit exists. A future construction more than "
        f"{margin(cheapest_query):.2f} bits cheaper per query would put the floor above the truth, "
        "and every ledger row that uses it would lose that many bits.",
        "- **Not counted:** error correction. Amy et al. put the full fault-tolerant SHA-256 "
        "preimage attack at about 2^166 logical-qubit-cycles against 2^128 queries — overhead that "
        "is entirely in the defender's favour and that the record, conservatively, does not claim.",
        "",
    ]
    return "\n".join(out)


LOG2_KEY = {"as_built_total": "as_built_total_gates",
            "t_count_at_7_per_toffoli": "t_count",
            "clifford_t_total_gates": "clifford_t_total_gates"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="directory for the json and report")
    args = parser.parse_args()
    results = build_results()
    for section in ("one_hash", "oracle_query_n32_image256", "oracle_query_n24_image192"):
        results[section]["as_built_total"] = results[section]["as_built"]["total"]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "hash_oracle_cost.json").write_text(json.dumps(results, indent=2))
    (args.out / "report.md").write_text(render(results))
    print(render(results))


if __name__ == "__main__":
    main()
