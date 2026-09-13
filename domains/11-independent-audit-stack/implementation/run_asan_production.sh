#!/bin/bash
# Bonus: ASan+UBSan at PRODUCTION parameters (b=20, tau=11, wg=16, rho=4096), 2 threads on cores 2-3,
# same 20-minute timeout. Recorded whatever the outcome (exit 124 = timeout).
W="$(cd "$(dirname "$0")" && pwd)"; cd "$W" || exit 1
{
  echo "################################################################"
  echo "### (a2) PRODUCTION parameters under ASan+UBSan, 2 threads (cores 2-3), detect_leaks=0, 20-minute timeout"
  echo "### $(date -Is)  cmd: taskset -c 2,3 timeout 1200 bin/asan_ubsan --run --threads 2"
  echo "### env: ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1 OMP_NUM_THREADS=2"
  s=$(date +%s.%N); ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1 OMP_NUM_THREADS=2 taskset -c 2,3 timeout 1200 ./bin/asan_ubsan --run --threads 2 2>&1; rc=$?
  echo "### exit code: $rc   (124 = killed by the 20-minute timeout)   wall time: $(echo "$(date +%s.%N) - $s" | bc) s"; echo
} >> asan_ubsan_output.txt
echo done > logs/asan_production.done
