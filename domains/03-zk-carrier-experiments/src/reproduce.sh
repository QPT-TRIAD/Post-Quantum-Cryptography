#!/bin/sh
# Reproduction entry point for the retained CEQS29 component evidence.
# Run from anywhere: the script re-roots itself on src/ first.
set -eu
cd -- "$(dirname -- "$0")"
python3 install_dependency.py
python3 verify_audit.py
python3 test_authorization.py --out ../results/replay-evidence
