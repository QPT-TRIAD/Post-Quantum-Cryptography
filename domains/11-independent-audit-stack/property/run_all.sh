#!/usr/bin/env bash
# Runs the property / differential / malformed-input layer. At most 4 processes at once.
# Targets in the research tree (PQT_SRC) are loaded read-only (no bytecode is written there).
set -u
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
# The pinned verification environment provides the audit's Python packages; source its
# activation script first (see tooling/).
mkdir -p logs
: > logs/summary.txt
PYTEST="python3 -m pytest -q -p no:cacheprovider -rxXf -s"

run() {
  local name=$1; shift
  ( "$@" > "logs/$name.log" 2>&1; echo "$name exit=$? :: $(tail -n 1 "logs/$name.log")" >> logs/summary.txt )
}

run b0       $PYTEST test_props_b0.py &
run modeB    $PYTEST test_props_modeB.py &
run hashsig  $PYTEST test_props_hashsig.py &
run tesla    $PYTEST test_props_tesla.py &
wait
run differential python3 differential_b0.py
echo "==== summary (logs/*.log) ===="
cat logs/summary.txt
grep -h -E "ACCEPT|DISAGREE|<-- FINDING" logs/*.log | sort -u | sed 's/^/  /' || true
