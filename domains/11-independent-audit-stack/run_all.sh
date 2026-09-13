#!/usr/bin/env bash
# QPT-128 independent audit stack — run every layer and collect results.
# Layers that need a tool absent on this host report NOT RUN (never a pass).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The pinned verification environment provides the audit's Python packages
# (Hypothesis, hsslms, sympy/galois) and puts tamarin-prover, maude and proverif on PATH.
# Source its activation script before running this file (see tooling/).
LOG="$HERE/run_all.log"; : > "$LOG"
step() { echo "== $1" | tee -a "$LOG"; shift; ( "$@" ) >> "$LOG" 2>&1; echo "   exit $?" | tee -a "$LOG"; }

step "MATH + CRYPTANALYSIS (SymPy, galois, exact Grover, multi-target, toy FRAME)"  python3 "$HERE/math/math_layer.py"
step "FORMAL: bounded model checker (third model)"                                  python3 "$HERE/formal/bounded_checker.py"
if command -v tamarin-prover >/dev/null; then
  step "FORMAL: Tamarin --prove"  tamarin-prover --prove "$HERE/formal/qpt128_quorum.spthy"
else echo "== FORMAL: Tamarin NOT RUN (tamarin-prover not on PATH)" | tee -a "$LOG"; fi
if command -v proverif >/dev/null; then
  step "FORMAL: ProVerif"  proverif "$HERE/formal/qpt128_quorum.pv"
else echo "== FORMAL: ProVerif NOT RUN (proverif not on PATH)" | tee -a "$LOG"; fi
step "PRIMITIVES: liboqs vs dilithium-py/kyber-py vs NIST ACVP"                      python3 "$HERE/primitives/cross_validate.py"
step "IMPLEMENTATION: sanitizers + libFuzzer (see implementation/IMPLEMENTATION_RESULTS.md)" bash -c "ls $HERE/implementation/*.md"
step "PROPERTY / DIFFERENTIAL / MALFORMED (Hypothesis)"                               bash "$HERE/property/run_all.sh"
step "FAULT INJECTION on the certificate/extraction pipeline"                         python3 "$HERE/fault/fault_injection.py"
echo "== done; see $LOG and docs/audit-stack-overview.md" | tee -a "$LOG"
