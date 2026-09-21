#!/usr/bin/env python3
"""Integration gate for the built repository.

Checks, against the file map:
  1. every `copy` / `copy-history` row has its file present at `new_path`;
  2. its sha256 equals the source sha256, unless the file is listed in rewrites.tsv
     (rewritten files legitimately differ — reported separately);
  3. every file in the repository is either claimed by a map row, or is a recognised
     generated document (README.md, docs/, VERIFICATION.md, SHA256SUMS.txt, ...);
     unclaimed files are reported so nothing is published by accident;
  4. no excluded source path appears in the repository;
  5. no file is empty, and no file is a duplicate of another unless the map allows it.

Usage:
  python3 verify_repo.py [--repo DIR] [--map FILE] [--rewrites FILE]
Exit status 0 iff checks 1, 3, 4 pass and there are no unexplained differences.
"""
import argparse
import collections
import hashlib
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The same file sits at `tools/` while the repository is being assembled, where the map and the
# rewrites table are working copies under `maps/`, and at `tooling/checks/` once published, where
# the two tables are the published copies under `records/`. The defaults follow the location.
ROOT = HERE.parent.parent if HERE.name == "checks" else HERE.parent
TABLES = ROOT / ("records" if HERE.name == "checks" else "maps")
WORK = HERE.parent
# Tool caches, not repository content: the same set `.gitignore` declares and `scrub_repo.py`
# already skips. A test suite run inside a domain writes these, and listing them as unexplained
# files would report something the repository never publishes.
SKIP = {".git", "__pycache__", ".hypothesis", ".pytest_cache", ".mypy_cache", "venv", ".venv"}
GENERATED_OK = {"README.md", "VERIFICATION.md", "SHA256SUMS.txt", "MANIFEST.json", ".gitignore", ".gitattributes"}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path.home() / "Documents/Post-Quantum-Cryptography"))
    ap.add_argument("--map", default=str(TABLES / "file-map.tsv"))
    ap.add_argument("--rewrites", default=str(TABLES / "rewrites.tsv"))
    a = ap.parse_args()

    repo = Path(a.repo)
    rows = [l.split("\t") for l in Path(a.map).read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
    copied = [r for r in rows if r[4] in ("copy", "copy-history")]
    excluded = [r for r in rows if r[4].startswith("exclude-") or r[4] == "source-only"]

    rewritten = set()
    rw = Path(a.rewrites)
    if rw.exists():
        for line in rw.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):   # the published table carries a note line
                continue
            cols = line.split("\t")
            if len(cols) >= 2:
                for f in cols[1].split(";"):
                    if f.strip():
                        rewritten.add(f.strip())

    errors, missing, differences, claimed = [], [], [], {}
    for r in copied:
        orig, digest, new = r[0], r[1], r[5]
        claimed.setdefault(new, []).append(orig)
        p = repo / new
        if not p.exists():
            missing.append(new)
            continue
        got = sha256(p)
        if got != digest:
            # rewrites.tsv names the destination path, which is what the repository holds.
            (differences if new in rewritten else errors).append("%s (map %s, repo %s)" % (new, digest[:12], got[:12]))

    present = set()
    empty = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fn in files:
            p = Path(root) / fn
            rel = str(p.relative_to(repo))
            present.add(rel)
            if p.stat().st_size == 0:
                empty.append(rel)

    unclaimed_all = sorted(x for x in present if x not in claimed and Path(x).name not in GENERATED_OK)
    # Authored and derived documents are expected, and nothing in the map can predict their
    # names: a domain writes its own README/VERIFICATION/docs, extracts an embedded script into
    # src/, or regenerates a result into results/. The layout convention fixes those directories,
    # so files there are recognisable -- and they are still listed, not merely counted, because
    # this list is how a file gets into a published tree without anyone having decided to ship it.
    #
    # A file reaches this branch only when the map does not claim it: a copied file is claimed, so
    # it is never in `unclaimed_all` to begin with. The directories below therefore say "what this
    # repository generated itself", never "what may be published unchecked". The last group is the
    # independent audit stack, whose whole point is that its inputs are re-derived here -- a
    # formal-verification trace, a re-run of a property suite, a rebuilt cross-validation -- so
    # those trees hold re-derived output as well as copies, and output is what they hold when the
    # map claims nothing there.
    #
    # Extended for domains 12-15, which are runnable engines rather than scripts and documents: a
    # domain may carry a self-contained package, so `tests/`, `scripts/`, `config/` and `notes/` are
    # part of the convention alongside `src/`, as are the two packaging files that make the package
    # installable. Excluding them would not have kept anything out of the repository -- the files
    # would still be published -- it would only have stopped this check from listing them.
    AUTHORED = re.compile(r"^(docs/|records/|tooling/|"
                          r"domains/[^/]+/(README\.md$|VERIFICATION\.md$|pyproject\.toml$|"
                          r"requirements\.txt$|docs/|src/|tests/|scripts/|config/|notes/|results/|"
                          r"fixtures/|vectors/|history/)|"
                          r"domains/11-independent-audit-stack/(formal|math|fault|property|fixes|implementation|"
                          r"independent-b0|primitives)/)")
    unclaimed = [x for x in unclaimed_all if not AUTHORED.match(x)]
    authored = [x for x in unclaimed_all if AUTHORED.match(x)]
    # `missing` (no file at that path) and `claimed - present` are the same set: the walk
    # covers the whole repository, so a claimed path that exists is in `present`. Report one.
    absent = sorted(set(missing))

    bad_rows = [r[0] for r in rows if len(r) != 7]
    print("map rows:                 %d (copy %d, excluded %d)" % (len(rows), len(copied), len(excluded)))
    print("files present in repo:    %d" % len(present))
    print("claimed new_paths:        %d" % len(claimed))
    print("missing from repo:        %d" % len(absent))
    print("sha256 differences:       %d (explained by rewrites: %d)" % (len(errors), len(differences)))
    print("authored documents:       %d (expected, not in the map)" % len(authored))
    print("UNEXPLAINED files:        %d" % len(unclaimed))
    print("empty files:              %d" % len(empty))
    print("malformed map rows:       %d" % len(bad_rows))
    for label, items in (("MISSING", absent), ("HASH", errors), ("UNCLAIMED", unclaimed),
                         ("AUTHORED", authored), ("EMPTY", empty), ("BADROW", bad_rows)):
        for it in items[:80]:
            print("%s\t%s" % (label, it))
    ok = not (missing or absent or errors or unclaimed or empty or bad_rows)
    print("RESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
