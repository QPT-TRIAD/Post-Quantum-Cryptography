#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
# tamarin-prover and maude come from the sourced verification environment (see tooling/).
for L in A_acceptance_authorized B_conflict_needs_2qN_corrupt C1_intersection_nonempty C2_intersection_at_least_2qN E2_at_threshold_conflict_exists D1_non_frameability E1_below_threshold_no_conflict; do
  { echo "### $L  $(date -Is)  -M8000m  timeout 1500 s"; s=$(date +%s)
    timeout 1500 tamarin-prover --prove="$L" qpt128_quorum_n7.spthy +RTS -M8000m -N4 -RTS 2>&1 | grep -v "^\[" | tail -40
    echo "### exit ${PIPESTATUS[0]} wall $(( $(date +%s) - s )) s"; } > "perlemma_n7_8g/$L.txt" 2>&1
done
echo done > perlemma_n7_8g/done
