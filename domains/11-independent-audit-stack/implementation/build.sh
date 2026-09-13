#!/bin/bash
# Build matrix for modeB_prover_v1.50.c (pristine copy in src/). Every compiler
# invocation and its full stdout/stderr is appended verbatim to build_log.txt.
W="$(cd "$(dirname "$0")" && pwd)"
SRC="$W/src/modeB_prover_v1.50.c"
# This repository carries the frozen prover once, in the hidden-signers domain, and has the
# audit stack reference it instead of duplicating it (see docs/inputs-and-provenance.md).
# Fall back to that copy when the stack-local one is absent; the two are byte-identical
# (sha256 ff8e5cd9…6adb92, the hash IMPLEMENTATION_RESULTS.md quotes for the pristine copy).
if [ ! -f "$SRC" ]; then
    SRC="$W/../../08-hidden-signers/history/mode-b-prover-v1.50.c"
fi
if [ ! -f "$SRC" ]; then
    echo "target not found: place modeB_prover_v1.50.c in $W/src/ (see docs/inputs-and-provenance.md)" >&2
    exit 2
fi
LOG="$W/build_log.txt"
# clang 18 sanitizer runtimes: libclang-rt-18-dev is NOT installed system-wide; the exact matching
# .deb (1:18.1.8~++20240731025043+3b5b5c1ec4a3) was fetched with apt-get download and extracted (no root)
# into a private resource dir (system headers symlinked + lib/linux/libclang_rt.*.a). See rt_deb/, rt/18/.
RD="$W/rt/18"
: > "$LOG"
build() {  # name, compiler, flags...
    local name="$1"; shift
    local cc="$1"; shift
    echo "=== [$name] $cc $* -o bin/$name src/modeB_prover_v1.50.c" | tee -a "$LOG"
    if "$cc" "$@" -o "$W/bin/$name" "$SRC" >> "$LOG" 2>&1; then
        echo "    OK  (exit 0)" | tee -a "$LOG"
    else
        echo "    FAILED (exit $?) -- see build_log.txt" | tee -a "$LOG"
    fi
}
# reference, exactly the build line from the source header comment (gcc 14)
build ref_gcc_O3      gcc   -O3 -march=native -fopenmp
# (a) ASan+UBSan
build asan_ubsan      clang -resource-dir=$RD -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -march=native -fopenmp
# (b) UBSan only, strict groups, no recovery (as specified)
build ubsan_strict    clang -resource-dir=$RD -O1 -g -fsanitize=undefined,integer,implicit-conversion -fno-sanitize-recover=all -fno-omit-frame-pointer -march=native -fopenmp
# (b') same checks but recoverable, to enumerate every distinct diagnostic site
build ubsan_recover   clang -resource-dir=$RD -O1 -g -fsanitize=undefined,integer,implicit-conversion -fsanitize-recover=all -fno-omit-frame-pointer -march=native -fopenmp
# (c) MSan: built WITHOUT -fopenmp (libomp is not MSan-instrumented -> guaranteed false positives)
build msan            clang -resource-dir=$RD -O1 -g -fsanitize=memory -fno-omit-frame-pointer -march=native
echo; echo "=== binaries:"; ls -l "$W/bin"
