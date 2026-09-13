#!/bin/bash
# Runs the self-test/demo of modeB_prover_v1.50.c under the instrumented builds.
# Reduced parameters (see TARGET_NOTES.md): --b 10 --tau 4 --wg 8 --rho 256, 4 threads,
# pinned to cores 0-3, 20-minute timeout per run. Output (stdout+stderr) is appended
# verbatim to the result files together with the command, env, exit code and wall time.
W="$(cd "$(dirname "$0")" && pwd)"
cd "$W" || exit 1
P="--b 10 --tau 4 --wg 8 --rho 256"
export OMP_NUM_THREADS=4
run() {  # binary outfile args...
    local bin="$1" out="$2"; shift 2
    {
        echo "################################################################"
        echo "### $(date -Is)  cmd: taskset -c 0-3 timeout 1200 bin/$bin $*"
        echo "### env: OMP_NUM_THREADS=$OMP_NUM_THREADS ASAN_OPTIONS=$ASAN_OPTIONS UBSAN_OPTIONS=$UBSAN_OPTIONS MSAN_OPTIONS=$MSAN_OPTIONS"
        local s e rc; s=$(date +%s.%N)
        taskset -c 0-3 timeout 1200 "$W/bin/$bin" "$@" 2>&1; rc=$?
        e=$(date +%s.%N)
        echo "### exit code: $rc   (124 = killed by the 20-minute timeout)   wall time: $(echo "$e - $s" | bc) s"
        echo
    } >> "$out"
}

export ASAN_OPTIONS=detect_leaks=1:abort_on_error=0
export UBSAN_OPTIONS=print_stacktrace=1
: > asan_ubsan_output.txt
run asan_ubsan asan_ubsan_output.txt --vectors
run asan_ubsan asan_ubsan_output.txt --run $P --threads 4

: > ubsan_output.txt
echo "=== (b) ubsan_strict: -fsanitize=undefined,integer,implicit-conversion -fno-sanitize-recover=all (aborts at the first diagnostic)" >> ubsan_output.txt
run ubsan_strict ubsan_output.txt --vectors
run ubsan_strict ubsan_output.txt --run $P --threads 4
echo "=== (b') ubsan_recover: same checks with -fsanitize-recover=all (UBSan reports each source location once; enumerates all distinct sites)" >> ubsan_output.txt
run ubsan_recover ubsan_output.txt --vectors
run ubsan_recover ubsan_output.txt --run $P --threads 4

: > msan_output.txt
export MSAN_OPTIONS=print_stats=0
echo "=== (c) msan: -fsanitize=memory, built WITHOUT -fopenmp (libomp is uninstrumented); single-threaded" >> msan_output.txt
run msan msan_output.txt --vectors
run msan msan_output.txt --run $P
echo "ALL SANITIZER RUNS DONE $(date -Is)" > logs/sanitizers.done
