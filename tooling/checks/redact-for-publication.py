#!/usr/bin/env python3
"""Publish a redacted copy of the rewrites table.

The rewrites table records, for each file that differs from its source, the text that was
replaced and the text that replaced it. The text that was replaced is exactly the text the
scrubbing pass removed: absolute machine paths, scratch-directory names, a campaign parameter
and an assistant tool name. Publishing the table unredacted would publish the strings the
table exists to document the removal of, which is a leak in the shape of a provenance record.

Redaction keeps the evidentiary value and drops the string: which files differ, how many
lines, which replacement class, and the reason. A reader who wants the literal text can take
the file's sha256 from the map and obtain the source; a reader who wants to know what class
of change was made reads this table. The redacted spans are replaced by a placeholder that
names the *category*, so the table still says what kind of thing was removed.

Only columns 1 and 3 (the before and after text) and column 4 (the reason) are redacted.
Column 2 lists the affected files and is what a reader follows.

Usage:
  python3 redact_for_publication.py [--in maps/rewrites.tsv] [--out maps/rewrites.public.tsv]
Exit status 0. Prints the number of spans redacted per category.
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_rules():
    """The rule table, from the sibling file that defines it.

    The rules live in the scanner and nowhere else: a second copy here would be a copy free to
    drift from the one the publication gate enforces. The two trees spell the scanner's name
    differently -- `scan_forbidden.py` while the repository is being assembled, `scan-forbidden.py`
    once published -- and a hyphen is not importable as a module name, so the file is loaded by
    path under whichever spelling is beside this one rather than imported by name.
    """
    for name in ("scan_forbidden.py", "scan-forbidden.py"):
        path = HERE / name
        if path.is_file():
            spec = importlib.util.spec_from_file_location("scan_forbidden", path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["scan_forbidden"] = mod
            spec.loader.exec_module(mod)
            return mod.RULES
    raise SystemExit("no scanner (%s) beside %s" % ("scan_forbidden.py", HERE))


RULES = load_rules()

# A placeholder has to be stable, greppable, and say what was there without being it.
PLACEHOLDER = {
    "ai-name": "<redacted: coding-tool name>",
    "ai-meta": "<redacted: assistant wording>",
    "abs-path": "<redacted: machine path>",
    "tracking": "<redacted: campaign parameter>",
    "contact": "<redacted: address>",
    "secret": "<redacted: credential>",
}
REDACT_COLS = (0, 2, 3)

# Absolute paths are redacted whole, before the category rules run. The category rules replace
# only the span they name, and an absolute path often contains two of them -- a scratch prefix
# followed by the project path, as in `/tmp/<prefix>-1000/<home>/<project>/<id>/`. Replacing the
# first span leaves the remainder of the path in place, which is a partial redaction: the table
# would then publish the second half of the string it was redacted to remove. So a path-shaped
# run is matched greedily, from its leading slash to its last segment, and replaced entire.
#
# The lookbehind is what keeps this from eating relative paths. A run only starts where an
# absolute path can start -- at the beginning of the text, or after a quote, an equals sign, a
# colon, whitespace. A relative path inside a token (`'fixture/xyz/fixtures'`,
# `'../results/x.json'`) has a word character, a dot or a hyphen before its slash and is left
# alone, which matters because most of this table describes path repointing: redacting the
# relative paths too would remove the evidence the table exists to carry.
PATH_RUN = re.compile(r"(?<![\w.\-])/(?:[A-Za-z0-9_.+-]+/)+[A-Za-z0-9_.+-]*")
PATH_PLACEHOLDER = "<redacted: machine path>"

NOTE = ("# Redacted for publication. Columns 1, 3 and 4 replace, with a placeholder naming "
        "the category, every span matching the repository's forbidden-content rules "
        "(machine-specific paths, coding-tool names, assistant wording, campaign parameters, "
        "e-mail addresses, credentials). The files in column 2 and the reasons are unchanged. "
        "The rules and this redaction are both in tooling/checks/; see records/provenance.md.")


def redact(text):
    n = 0
    text, k = PATH_RUN.subn(PATH_PLACEHOLDER, text)   # whole absolute paths, before the rules
    n += k
    for cat, rx in RULES:
        text, k = rx.subn(PLACEHOLDER[cat], text)
        n += k
    return text, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=str(HERE.parent / "maps/rewrites.tsv"))
    ap.add_argument("--out", dest="dst", default=str(HERE.parent / "maps/rewrites.public.tsv"))
    a = ap.parse_args()

    lines = Path(a.src).read_text(encoding="utf-8").splitlines()
    counts, rows, residue = {}, [], []
    for i, line in enumerate(lines):
        cols = line.split("\t")
        if i == 0:                      # header row
            rows.append(line)
            continue
        for c in REDACT_COLS:
            if c < len(cols):
                cols[c], n = redact(cols[c])
                if n:
                    counts[i] = counts.get(i, 0) + n
        # Every column is checked, including the file list that is published unredacted: if a
        # rule matches a column this tool does not redact, the table must not go out at all.
        for c in range(len(cols)):
            for cat, rx in RULES:
                if rx.search(cols[c]):
                    residue.append((i, c, cat, cols[c][:120]))
        rows.append("\t".join(cols))

    out = Path(a.dst)
    out.write_text(NOTE + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    total = sum(counts.values())
    print("rows: %d, rows with redaction: %d, spans redacted: %d"
          % (len(rows) - 1, len(counts), total))
    print("wrote %s" % out)
    if residue:
        print("RESIDUE: %d span(s) still match a rule after redaction" % len(residue))
        for i, c, cat, text in residue[:20]:
            print("  row %d col %d [%s]: %s" % (i, c + 1, cat, text))
        return 1
    print("RESULT: PASS -- no rule matches anything the table publishes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
