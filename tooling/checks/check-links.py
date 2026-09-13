#!/usr/bin/env python3
"""Report references in this repository that point at a file that is not here.

A repository assembled from another tree by renaming and re-placing files is exactly the kind
of tree where a document keeps naming a file by its old name, or by a path relative to a
directory it no longer sits in. Both read fine and send the reader nowhere.

Two kinds of reference are checked:

  * markdown link targets -- `[text](path)`, resolved relative to the file that carries them
    and then against the repository root.
  * inline code spans that name a file -- a backticked token containing a `/` and ending in a
    known extension, which is how this repository cites its own artifacts (`records/file-map.tsv`,
    `src/sidecar_free_certificate.py`). Resolved the same two ways, plus relative to the file's
    own directory's parent, because a domain document cites a sibling package by its directory
    name from the domain root.

Not every unresolved name is a fault, and this tool does not pretend otherwise: a `history/`
entry keeps a superseded file's original name on purpose, and a `not-run` record legitimately
names an artifact that is absent -- that absence is what makes it not-run. The largest legitimate
class is a document that names the file it was assembled from; `--map` supplies the file map, and
names it lists as source files are counted separately from names nothing accounts for. The output
is a list for a human to read, and the exit status is non-zero only for markdown link targets,
which are always meant to resolve.

Usage:
  python3 check_links.py [--repo DIR] [--map records/file-map.tsv] [--quiet]
"""
import argparse
import collections
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".hypothesis", ".mypy_cache"}
TEXT_EXT = {".md"}
EXT = r"(?:md|py|json|tsv|txt|sh|c|h|spthy|p?v|proof|cfg|toml|lock|rs|bin)"   # file-shaped tails
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CODE = re.compile(r"`([^`\n]+)`")
PATHISH = re.compile(r"(?<![\w/.-])([A-Za-z0-9_][A-Za-z0-9_./-]*\.%s)\b" % EXT)
DIRMENTION = re.compile(r"(?<![\w/-])((?:domains|docs|tooling|records|staging)"
                        r"(?:/[A-Za-z0-9_.-]+)+)")

HERE = Path(__file__).resolve().parent
# The same file sits at `tools/` while the repository is being assembled and at `tooling/checks/`
# once published, so the default root is found from where the file itself is rather than assumed.
ROOT = HERE.parent.parent if HERE.name == "checks" else HERE.parent


def looks_like_a_path(target):
    """Mathematical function application is written like a link and is not one.

    The source documents carry definitions such as `L_α[f](s) := …` and `Z[f](z) := …`. A
    markdown link target has to look like a path to be read as one: it either contains a
    directory separator or ends in a file extension.
    """
    t = target.strip()
    if t.startswith(("http://", "https://", "mailto:", "#")):
        return True                      # handled (and skipped) in resolve()
    return "/" in t or bool(re.search(r"\.[A-Za-z0-9]{1,6}$", t))


def resolve(repo, base, raw):
    """Try the path the way a reader would: as written, relative to the file, relative to root."""
    raw = raw.strip().lstrip("./")
    if not raw or raw.startswith(("http://", "https://", "mailto:", "#")):
        return True
    raw = raw.split("#", 1)[0]
    if not raw:
        return True
    for cand in (base / raw, repo / raw, base.parent / raw, base.parent.parent / raw):
        if cand.exists():
            return True
    return False


def context_dirs(repo, paragraph):
    """Directories a paragraph names, nearest mention first.

    Half the citations in a repository like this one are written relative to a directory the
    surrounding prose has just named -- "`domains/09-security-games-and-attack-lab`, whose
    `src/ceqs_games.py` ...", or a section headed `**Directory:** domains/08-hidden-signers`
    followed by a list of that directory's files. A reader follows those with no trouble, because
    the directory is the sentence they are in. So the directory is collected here, and a citation
    that fails on its own is tried against these before it is reported.
    """
    out = []
    for m in DIRMENTION.finditer(paragraph):
        parts = m.group(1).split("/")
        for k in range(len(parts), 0, -1):          # the longest existing prefix of the mention
            cand = repo / "/".join(parts[:k])
            if cand.is_dir():
                out.append(cand)
                break
    out.reverse()                                   # the mention nearest the citation wins
    return out


def paragraphs(text):
    """(first-line-number, text) for each blank-line-separated block; headings end a block."""
    block, start = [], 1
    for i, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            if block:
                yield start, "\n".join(block)
            block, start = [], i + 1
        else:
            if not block:
                start = i
            block.append(line)
    if block:
        yield start, "\n".join(block)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(ROOT))
    ap.add_argument("--map", default=str(ROOT / "records/file-map.tsv"),
                    help="file map; names it lists as source files are expected to be absent "
                         "here and are counted separately")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()

    # A document that names a file the repository does not hold is usually naming it on purpose:
    # it is describing the source the file came from, and the source names are what the map
    # records. So the map is read first, and its source basenames are the set of names that are
    # allowed to be absent. What is left over is the part worth a reader's attention.
    source_names = set()
    if a.map and Path(a.map).exists():
        for line in Path(a.map).read_text(encoding="utf-8").splitlines()[1:]:
            cols = line.split("\t")
            if len(cols) >= 6 and cols[0].strip():
                source_names.add(os.path.basename(cols[0].replace("\\", "/")))

    hard, soft, contextual = [], [], []
    nfiles = 0
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() not in TEXT_EXT:
                continue
            nfiles += 1
            rel = str(p.relative_to(repo))
            base = p.parent
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for start, para in paragraphs(text):
                ctx = None
                for i, line in enumerate(para.splitlines(), start=start):
                    for m in LINK.finditer(line):
                        if not looks_like_a_path(m.group(1)):
                            continue
                        if not resolve(repo, base, m.group(1)):
                            hard.append((rel, i, m.group(1)))
                    for span in CODE.findall(line):
                        for m in PATHISH.finditer(span):
                            t = m.group(1)
                            if resolve(repo, base, t):
                                continue
                            if ctx is None:
                                ctx = context_dirs(repo, para)
                            if any((d / t).exists() for d in ctx):
                                contextual.append((rel, i, t))
                            else:
                                soft.append((rel, i, t))

    hard_by_target = collections.Counter(t for _, _, t in hard)
    from_source = collections.Counter(t for _, _, t in soft
                                      if os.path.basename(t) in source_names)
    unknown = collections.Counter(t for _, _, t in soft
                                 if os.path.basename(t) not in source_names)
    print("markdown files: %d" % nfiles)
    print("link targets that do not resolve:       %d (%d distinct)"
          % (len(hard), len(hard_by_target)))
    print("code-span names resolved from a directory named in the same paragraph: %d"
          % len(contextual))
    print("code-span names not in this repository: %d (%d distinct)"
          % (len(soft), len({t for _, _, t in soft})))
    print("  ... of which the file map lists the source: %d (%d distinct)"
          % (sum(from_source.values()), len(from_source)))
    print("  ... and which the map does not list either: %d (%d distinct)"
          % (sum(unknown.values()), len(unknown)))
    if not a.quiet:
        for rel, i, t in hard:
            print("LINK\t%s:%d\t%s" % (rel, i, t))
        for t, c in unknown.most_common(120):
            where = next(rel for rel, _, x in soft if x == t)
            print("CODE\t%d refs\t%-52s first in %s" % (c, t[:52], where))
    print("RESULT: %s" % ("PASS" if not hard else "FAIL (link targets)"))
    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
