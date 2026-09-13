"""
check_vectors.py -- cross-validate b0_indep.py (spec-only implementation)
against b0_vectors.json (reference vectors).  Never modifies the vectors.

Writes independent_results.json and INDEPENDENT_RESULTS.md next to itself.
"""

from __future__ import annotations

import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import b0_indep as B  # noqa: E402

VEC = os.path.join(HERE, "b0_vectors.json")
OUT_JSON = os.path.join(HERE, "independent_results.json")
OUT_MD = os.path.join(HERE, "INDEPENDENT_RESULTS.md")


class Tally:
    def __init__(self):
        self.agree = collections.Counter()
        self.disagree = collections.Counter()
        self.disagreements = []     # dicts: category, case, mine, reference
        self.info = collections.defaultdict(collections.Counter)

    def check(self, category, case_id, mine, reference, ok=None):
        same = (mine == reference) if ok is None else ok
        if same:
            self.agree[category] += 1
        else:
            self.disagree[category] += 1
            self.disagreements.append({
                "category": category, "case": case_id,
                "mine": mine if isinstance(mine, (str, bool, int, type(None))) else repr(mine)[:300],
                "reference": reference if isinstance(reference, (str, bool, int, type(None))) else repr(reference)[:300],
            })
        return same


def unhex(s):
    return bytes.fromhex(s)


def load_registry(reg):
    pks = [unhex(h) for h in reg["public_keys"]]
    sid = reg["scheme_id"]
    # GAP (§10): scheme_id is a plain string in the file, keys are hex.  A
    # hex-looking scheme_id would be ambiguous; 'toy-shake-32' is not hex.
    try:
        sid_b = unhex(sid)
        note = "scheme_id decoded as hex"
    except ValueError:
        sid_b = sid.encode("utf-8")
        note = "scheme_id used as UTF-8 text"
    return (pks, sid_b), note


def main():
    data = json.load(open(VEC))
    t = Tally()
    registry, sid_note = load_registry(data["registry"])
    t.info["registry"][sid_note] += 1

    # ---- cfg -------------------------------------------------------------
    my_cfg = B.cfg(registry)
    t.check("cfg", "top-level", my_cfg.hex(), data["cfg"])
    expected_cfg = my_cfg          # what a verifier would be configured with
    ref_cfg = unhex(data["cfg"])

    # canonical toy registry?  (informs GAP about encode's secret keys)
    canonical = registry[0] == [B.toy_pk(i) for i in range(B.N)] and registry[1] == B.TOY_SCHEME_ID
    t.info["registry"]["canonical toy registry" if canonical else "NON-canonical registry"] += 1

    for case in data["cases"]:
        kind = case["kind"]
        cid = str(case["id"])

        if kind == "conflict":
            domain = unhex(case["domain"])
            for k in ("0", "1"):
                msg = unhex(case["message" + k])
                seats = case["seats" + k]
                ref_frame = unhex(case["frame" + k])
                try:
                    my_frame = B.encode(registry, domain, msg, seats)
                except Exception as e:
                    my_frame = None
                    t.check("conflict.encode", cid + "/frame" + k, "ENCODE RAISED: %r" % e, "frame bytes")
                if my_frame is not None:
                    if not t.check("conflict.encode", cid + "/frame" + k, my_frame.hex(), ref_frame.hex()):
                        # locate first differing byte for the report
                        n = min(len(my_frame), len(ref_frame))
                        first = next((i for i in range(n) if my_frame[i] != ref_frame[i]), n)
                        t.disagreements[-1]["mine"] = "len=%d first_diff_at=%d" % (len(my_frame), first)
                        t.disagreements[-1]["reference"] = "len=%d" % len(ref_frame)
                # verify the *reference* frame (must accept)
                res, why = B.verify_reason(ref_frame, registry, expected_cfg)
                t.check("conflict.verify", cid + "/frame" + k,
                        "accept" if res else "reject: " + why, "accept")
                if res:
                    # cross-check the decoded fields against the case inputs
                    ok = (res["domain"] == domain and res["message"] == msg
                          and res["seats"] == sorted(seats) and res["cfg"] == ref_cfg
                          and res["width"] == B.TOY_WIDTH)
                    t.check("conflict.verify_fields", cid + "/frame" + k, ok, True)

            f0, f1 = unhex(case["frame0"]), unhex(case["frame1"])
            mine, why = B.extract_reason(f0, f1, registry, expected_cfg)
            ref = [tuple(x) for x in case["extract"]]
            t.check("conflict.extract", cid,
                    mine if mine is not None else "reject: " + why, ref)
            if mine is not None:
                t.info["conflict.extract"]["overlap=%d" % len(mine)] += 1

            for seat_s, ref_verdict in case["blame"].items():
                seat = int(seat_s)
                mine_v = B.blame(f0, f1, registry, expected_cfg, seat)
                t.check("conflict.blame", "%s/seat%d" % (cid, seat), mine_v, bool(ref_verdict))
                t.info["conflict.blame"]["ref=%s" % ref_verdict] += 1

        elif kind in ("same-message", "other-domain"):
            f0, f1 = unhex(case["frame0"]), unhex(case["frame1"])
            assert case["expected_extract"] == "reject"
            mine, why = B.extract_reason(f0, f1, registry, expected_cfg)
            t.check(kind + ".extract", cid, "reject" if mine is None else "ACCEPTED %d triples" % len(mine), "reject")
            if mine is None:
                t.info[kind + ".extract_reason"][why.split(":")[0]] += 1
            # informational: each frame alone should still be a valid frame
            for k, f in (("0", f0), ("1", f1)):
                r, w = B.verify_reason(f, registry, expected_cfg)
                t.info[kind + ".verify_each"]["accept" if r else "reject " + w] += 1
            # spec-derived (not in vectors): blame must be False for every seat
            bad = [s for s in range(B.N) if B.blame(f0, f1, registry, expected_cfg, s)]
            t.check(kind + ".blame_all_false(spec-derived)", cid, bad, [])

        elif kind in ("mutated", "truncated", "trailing"):
            f = unhex(case["frame"])
            assert case["expected_verify"] is False
            res, why = B.verify_reason(f, registry, expected_cfg)
            t.check(kind + ".verify", cid, "reject" if res is None else "ACCEPTED", "reject")
            if res is None:
                t.info[kind + ".reject_reason"][why.split(" ")[0]] += 1
            t.info[kind + ".frame_len"][str(len(f))] += 1

        else:
            t.check("unknown-kind", cid, kind, "known kind")

    # ---- summary -------------------------------------------------------------
    cats = sorted(set(t.agree) | set(t.disagree))
    summary = {
        "vectors": os.path.basename(VEC),
        "spec": data.get("spec"),
        "cases": len(data["cases"]),
        "categories": {c: {"agree": t.agree[c], "disagree": t.disagree[c]} for c in cats},
        "total_agree": sum(t.agree.values()),
        "total_disagree": sum(t.disagree.values()),
        "disagreements": t.disagreements,
        "info": {k: dict(v) for k, v in t.info.items()},
    }
    json.dump(summary, open(OUT_JSON, "w"), indent=1)

    lines = ["# Independent B0 implementation vs reference vectors", ""]
    lines.append("Spec-only implementation `b0_indep.py`; vectors `%s` (%d cases)." % (os.path.basename(VEC), len(data["cases"])))
    lines.append("")
    lines.append("| category | agree | disagree |")
    lines.append("|---|---:|---:|")
    for c in cats:
        lines.append("| %s | %d | %d |" % (c, t.agree[c], t.disagree[c]))
    lines.append("| **total** | **%d** | **%d** |" % (summary["total_agree"], summary["total_disagree"]))
    lines.append("")
    if t.disagreements:
        lines.append("## Disagreements (case id: mine vs reference)")
        for d in t.disagreements:
            lines.append("- `%s` %s: mine=`%s` ref=`%s`" % (d["category"], d["case"], d["mine"], d["reference"]))
    else:
        lines.append("## Disagreements")
        lines.append("None. Every frame re-encoded byte-for-byte; every verify / extract / blame verdict matched.")
    lines.append("")
    lines.append("Rejection clauses hit: " + "; ".join(
        "%s -> %s" % (k.replace(".reject_reason", ""), dict(v))
        for k, v in t.info.items() if k.endswith("reject_reason")))
    text = "\n".join(lines) + "\n"
    assert text.count("\n") <= 40, "INDEPENDENT_RESULTS.md exceeds 40 lines"
    open(OUT_MD, "w").write(text)
    print(text)
    print(json.dumps({k: v for k, v in summary.items() if k != "disagreements"}, indent=1))
    return 1 if t.disagreements else 0


if __name__ == "__main__":
    sys.exit(main())
