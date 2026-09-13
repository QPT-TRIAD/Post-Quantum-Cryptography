#!/bin/bash
# 10-minute libFuzzer campaign for fuzz_verify (2 jobs / 2 workers, pinned to cores 0-1).
# Leak detection is OFF here because the known verify() leak (line 803/815) would stop
# every job within seconds; that leak is documented separately (artifacts/leak-*, logs/leak_probe.txt).
W="$(cd "$(dirname "$0")" && pwd)"; cd "$W/logs/fuzz" || exit 1
LEN=$(stat -c %s "$W/corpus_genuine.bin")
echo "### $(date -Is) cmd: taskset -c 0,1 $W/bin/fuzz_verify $W/corpus/ -max_len=$((2*LEN)) -jobs=2 -workers=2 -timeout=30 -max_total_time=600 -detect_leaks=0 -print_final_stats=1 -artifact_prefix=$W/artifacts/"
ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1 taskset -c 0,1 "$W/bin/fuzz_verify" "$W/corpus/" -max_len=$((2*LEN)) -jobs=2 -workers=2 -timeout=30 -max_total_time=600 -detect_leaks=0 -print_final_stats=1 -artifact_prefix="$W/artifacts/" 2>&1
echo "### exit code: $?  $(date -Is)"
echo done > "$W/logs/fuzz.done"
