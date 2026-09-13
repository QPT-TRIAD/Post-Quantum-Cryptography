#!/usr/bin/env python3
"""Record the exit codes of the two harnesses' modes, and show the failure path works.

Why this probe exists. A run whose failure mode is not stated cannot be told apart from a
run that cannot fail. The two harnesses in `src/` are shipped unmodified from the revisions
that produced the recorded results, so this probe does not edit them: it reads them, and
demonstrates the failure path on a *copy* in a temporary directory outside this repository.

What it does, in order, printing everything it observes:

  1. sha256 of both shipped files, before and after -- to show the probe changed nothing.
  2. `--self-test` on each shipped file, from `src/`, recording exit code and the test count.
     This is the mode with assertions in it, and it must exit 0 when the checks pass.
  3. A copy of each file with one test method appended that fails unconditionally, laid out
     in a temporary tree with `domains/08-hidden-signers` symlinked so the relative module
     load resolves. Running it must exit 1. If it exited 0, the exit code would carry no
     information and every "exit 0" in VERIFICATION.md would be worthless.
  4. The source line that defines the failure path, quoted for each harness.

`--all` is *not* exercised here: it is a report mode that returns 0 by construction (see the
last section of the output), it takes minutes, and its verdict is in the report body, not in
an exit code. Its counts are checked separately (VERIFICATION.md).

Usage:  python3 probe_exit_codes.py          (from this directory)
Writes nothing except a temporary directory under $TMPDIR, which it removes.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAIN = HERE.parent
SRC = DOMAIN / "src"
REPO = DOMAIN.parent.parent
HARNESSES = ("ceqs_attack_lab.py", "ceqs_games.py")
INJECTION = '''
    def test_probe_injected_failure(self):
        """Injected by results/probe_exit_codes.py: must make this mode exit non-zero."""
        self.assertTrue(False, 'injected failure -- the exit code must be 1')
'''

failures = 0


def say(*parts):
    print(*parts)
    sys.stdout.flush()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cwd, argv):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable] + argv, cwd=str(cwd), env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def rel(path):
    """Path relative to the repository root, so a captured run names no machine."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return path.name


def main():
    global failures
    say("probe: harness exit codes                     (%s)" % sys.platform)
    say("interpreter: %s" % sys.version.split()[0])
    say("source directory: %s   (relative to the repository root)" % rel(SRC))
    say("")

    before = {name: sha256(SRC / name) for name in HARNESSES}

    # --- 1. the shipped files must not change -------------------------------------------
    say("1. shipped files, read-only input to this probe")
    for name in HARNESSES:
        say("   %-22s %s  %d bytes" % (name, before[name][:16] + "...", (SRC / name).stat().st_size))
    say("")

    # --- 2. the check mode on the shipped files -----------------------------------------
    say("2. --self-test on the shipped files (the mode that carries assertions)")
    for name in HARNESSES:
        rc, out = run(SRC, [name, "--self-test"])
        line = next((l for l in out.splitlines() if l.startswith("Ran ")), "(no summary line)")
        ok = "OK" if re.search(r"^OK$", out, re.M) else "NOT OK"
        say("   %-22s exit=%d  %s  %s" % (name, rc, line.strip(), ok))
        if rc != 0:
            failures += 1
            say("      FAIL: the shipped self-test exited non-zero")
    say("")

    # --- 3. the same mode on a copy carrying one injected failing test -------------------
    say("3. --self-test on a copy with one injected failing test (in a temporary directory)")
    tmp = Path(tempfile.mkdtemp(prefix="d9probe-"))
    try:
        (tmp / "domains/09-security-games-and-attack-lab/src").mkdir(parents=True)
        (tmp / "domains/08-hidden-signers").symlink_to(REPO / "domains/08-hidden-signers")
        for name in HARNESSES:
            text = (SRC / name).read_text(encoding="utf-8")
            anchor = "def main(argv=None):"
            n = text.count(anchor)
            if n != 1:
                say("   %-22s FAIL: anchor matched %d times, not 1" % (name, n))
                failures += 1
                continue
            mutant = text.replace(anchor, INJECTION.lstrip("\n") + "\n" + anchor)
            (tmp / "domains/09-security-games-and-attack-lab/src" / name).write_text(
                mutant, encoding="utf-8")
            rc, out = run(tmp / "domains/09-security-games-and-attack-lab/src",
                          [name, "--self-test"])
            line = next((l for l in out.splitlines() if l.startswith("Ran ")), "(no summary)")
            say("   %-22s exit=%d  %s  (expect exit=1)" % (name, rc, line.strip()))
            if rc != 1:
                failures += 1
                say("      FAIL: a failing test did not produce a non-zero exit code")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    say("")

    # --- 4. what the failure path actually is -------------------------------------------
    say("4. the failure path, quoted from the shipped sources")
    for name in HARNESSES:
        for line in (SRC / name).read_text(encoding="utf-8").splitlines():
            if "wasSuccessful()" in line:
                say("   %-22s %s" % (name, line.strip()))
    say("   report modes, by construction (no verdict in the exit code):")
    for name in HARNESSES:
        lines = (SRC / name).read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "return 0":
                say("   %-22s line %d: %s" % (name, i + 1, line.strip()))
    say("")

    # --- 5. nothing was written ----------------------------------------------------------
    after = {name: sha256(SRC / name) for name in HARNESSES}
    say("5. shipped files after the probe")
    for name in HARNESSES:
        same = "unchanged" if after[name] == before[name] else "CHANGED (!!)"
        say("   %-22s %s  %s" % (name, after[name][:16] + "...", same))
        if after[name] != before[name]:
            failures += 1
    say("")
    say("RESULT: %s" % ("PASS -- exit codes carry the verdict, and the failure path exits 1"
                        if not failures else "FAIL -- %d observation(s) above" % failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
