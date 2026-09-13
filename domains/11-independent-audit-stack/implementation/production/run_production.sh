#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
{ echo "### ASan+UBSan PRODUCTION (b=20 tau=11 wg=16 rho=4096), 8 threads, 60-min timeout, $(date -Is)"
  s=$(date +%s); ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1 OMP_NUM_THREADS=8 timeout 3600 ./bin/asan_ubsan --run --threads 8 2>&1; rc=$?
  echo "### exit $rc wall $(( $(date +%s) - s )) s"; } > production/asan_ubsan_production.txt 2>&1
{ echo "### MSan PRODUCTION, 1 thread (no OpenMP), 60-min timeout, $(date -Is)"
  s=$(date +%s); MSAN_OPTIONS=print_stats=1 timeout 3600 ./bin/msan --run --threads 1 2>&1; rc=$?
  echo "### exit $rc wall $(( $(date +%s) - s )) s"; } > production/msan_production.txt 2>&1
echo done > production/done
