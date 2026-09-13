#!/usr/bin/env python3
"""Create a fresh centralized experiment in a new directory; remove private files.

This is the version 1.27b regeneration harness. It builds a self-contained copy
of the paired-trace experiment in a *new* directory and runs the whole pipeline
there: fresh fixture, check, prove, encode, public verification, negative
controls. Host private inputs are then removed and their removal is recorded.
The point of the harness is that nothing in it reuses the retained evidence.

The adapter source for this experiment is `history/v1.27b/adapter`; the compiled
binary it needs is a build product and is not retained in this repository. Point
`CEQS_BINARY` at a build of that adapter, or place it at `src/bin/` under the
name below, before running.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOMAIN = HERE.parent
BINARY_NAME = "ceqs-fixed-pair-v127b"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="a new directory; it must not exist yet")
    args = parser.parse_args()
    binary = Path(os.environ.get("CEQS_BINARY", HERE / "bin" / BINARY_NAME))
    if not binary.is_file():
        raise SystemExit(
            "native paired-trace binary not present: " + str(binary) + "\n"
            "the compiled adapter is not part of this repository (see docs/provenance.md);\n"
            "build history/v1.27b/adapter against the pinned upstream tree and set CEQS_BINARY")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "bin").mkdir()
    (output / "adapter").mkdir()
    (output / "fixture").mkdir()
    # The version 1.27b scripts are retained unmodified under history/; they expect
    # to be run from a directory that holds bin/, fixture/ and adapter/.
    for name in ("run_native.py", "verify_public.py", "check_public_mutations.py"):
        shutil.copy2(DOMAIN / "history/v1.27b" / name, output / name)
    # paired_reference.py and make_fixture.py are byte-identical to the retained
    # current copies; make_fixture.py takes its fixture directory from the
    # environment, which the runner below sets.
    shutil.copy2(HERE / "paired_reference.py", output / "paired_reference.py")
    shutil.copy2(HERE / "make_fixture.py", output / "make_fixture.py")
    shutil.copy2(HERE / "adapter/field_vectors.json", output / "adapter/field_vectors.json")
    shutil.copy2(binary, output / "bin" / BINARY_NAME)
    (output / "bin" / BINARY_NAME).chmod(0o700)

    environment = dict(os.environ, CEQS_FIXTURES=str(output / "fixture"),
                       CEQS_RESULTS=str(output))

    def run(label, *argv):
        with (output / (label + ".stdout.log")).open("w") as out, \
             (output / (label + ".stderr.log")).open("w") as err:
            subprocess.run([sys.executable, *map(str, argv)], cwd=output, env=environment,
                           stdout=out, stderr=err, check=True, timeout=1500)

    deleted = []
    private_paths = [output / "fixture" / case / "PRIVATE_TRACE_WITNESS.bin"
                     for case in ("case0", "case1")]
    try:
        run("fresh_fixture", output / "make_fixture.py")
        for case in ("case0", "case1"):
            run("check_" + case, output / "run_native.py", "check_" + case, "check", case)
            run("prove_" + case, output / "run_native.py", "prove_" + case, "prove_native", case)
    finally:
        for path in private_paths:
            if path.exists():
                deleted.append({"path": str(path.relative_to(output)), "bytes": path.stat().st_size})
                path.unlink()
            if path.exists():
                raise RuntimeError("private input still present after removal")
        (output / "private_input_deletion.json").write_text(json.dumps({
            "deleted_before_public_verification": True, "files": deleted,
            "bytes_deleted": sum(row["bytes"] for row in deleted),
            "secure_erasure_claim": False}, indent=2) + "\n")
    for case in ("case0", "case1"):
        run("encode_" + case, output / "run_native.py", "encode_" + case, "encode", case)
    run("public_verification", output / "verify_public.py", "--config", output / "fixture/config.json",
        "--frame", output / "fixture/case0/trace43_rate3.pf27",
        "--frame", output / "fixture/case1/trace43_rate3.pf27",
        "--output", output / "public_verification.json")
    run("public_negative", output / "check_public_mutations.py")
    if any(path.exists() for path in private_paths):
        raise RuntimeError("private input unexpectedly present at final check")
    print(json.dumps({"output": str(output), "fresh_pair_verified": True,
                      "centralized_experiment": True, "complete_original_goal_QCs": 0}))


if __name__ == "__main__":
    main()
