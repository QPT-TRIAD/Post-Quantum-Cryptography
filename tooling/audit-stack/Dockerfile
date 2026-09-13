# QPT-128 independent audit environment (item 19 of the audit-stack design).
# One image: sources, SageMath (via passagemath), SymPy, galois, Hypothesis, liboqs,
# independent ML-DSA/ML-KEM implementations, Tamarin + Maude, ProVerif (opam),
# clang sanitizers + libFuzzer, AFL++, valgrind, the attack lab and the devnet tooling.
#
#   docker build -t qpt128-audit:2.1 -f Dockerfile ..
#   docker run --rm -it -v "$PWD/artifacts:/audit/artifacts" qpt128-audit:2.1 ./run_all.sh
#
# NOT built or tested on the authoring host (a 64-container devnet sweep was running there);
# the layer scripts under this directory were executed natively with the same tool versions
# where available (see AUDIT_STACK.md, column "executed here"). Pin every version before
# citing a result from this image.

FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
ARG LIBOQS_TAG=0.16.0
ARG TAMARIN_VERSION=1.10.0
ARG MAUDE_VERSION=3.5

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential clang-18 lld-18 llvm-18 cmake ninja-build git curl ca-certificates unzip \
    python3 python3-pip python3-venv valgrind afl++ opam m4 pkg-config libgmp-dev \
    graphviz && rm -rf /var/lib/apt/lists/* \
 && ln -sf /usr/bin/clang-18 /usr/local/bin/clang && ln -sf /usr/bin/clang++-18 /usr/local/bin/clang++

WORKDIR /audit
COPY . /audit/qpt_audit_stack
# The project sources are mounted or copied by the caller into /audit/src (read-only):
#   docker run -v /path/to/PQT:/audit/src:ro ...
ENV PQT_SRC=/audit/src

# --- Python engines: SymPy, galois (GF(2^m)), Hypothesis, numpy, dnspython, hsslms, passagemath (SageMath modules)
RUN python3 -m venv /audit/venv && . /audit/venv/bin/activate \
 && pip install --no-cache-dir sympy==1.14.0 galois==0.4.11 numba hypothesis==6.168.0 numpy scipy dnspython==2.8.0 hsslms==0.1.3 \
    dilithium-py kyber-py \
 && (pip install --no-cache-dir passagemath-standard || echo "passagemath (SageMath) install failed; SymPy/galois remain the math engines")
ENV PATH="/audit/venv/bin:${PATH}"

# --- liboqs (independent PQ primitives), minimal build
RUN git clone --branch ${LIBOQS_TAG} --depth 1 https://github.com/open-quantum-safe/liboqs /audit/liboqs \
 && cmake -S /audit/liboqs -B /audit/liboqs/build -GNinja -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON \
    -DOQS_MINIMAL_BUILD="OQS_ENABLE_SIG_ml_dsa_87;OQS_ENABLE_SIG_ml_dsa_44;OQS_ENABLE_KEM_ml_kem_1024;OQS_ENABLE_KEM_ml_kem_768" \
 && cmake --build /audit/liboqs/build && cmake --install /audit/liboqs/build --prefix /usr/local && ldconfig

# --- Tamarin prover + Maude
RUN curl -fsSL -o /tmp/tamarin.tar.gz \
      https://github.com/tamarin-prover/tamarin-prover/releases/download/${TAMARIN_VERSION}/tamarin-prover-${TAMARIN_VERSION}-linux64-ubuntu.tar.gz \
 && tar -xzf /tmp/tamarin.tar.gz -C /usr/local/bin && chmod +x /usr/local/bin/tamarin-prover \
 && curl -fsSL -o /tmp/maude.zip https://github.com/maude-lang/Maude/releases/download/Maude${MAUDE_VERSION}/Maude-${MAUDE_VERSION}-linux-x86_64.zip \
 && unzip -q /tmp/maude.zip -d /tmp/maude && cp /tmp/maude/*/maude* /usr/local/bin/ 2>/dev/null || cp /tmp/maude/maude* /usr/local/bin/ \
 && chmod +x /usr/local/bin/maude* && tamarin-prover test || echo "tamarin self-test failed; record in the ledger"

# --- ProVerif via opam
RUN opam init --disable-sandboxing -y -a && eval $(opam env) && opam install -y proverif \
 && ln -sf "$(opam var bin)/proverif" /usr/local/bin/proverif || echo "proverif install failed; models remain unexecuted"

# --- NIST ACVP vectors (ML-DSA, ML-KEM) fetched at build time for the primitives layer
RUN mkdir -p /audit/acvp && cd /audit/acvp \
 && for f in ML-DSA-keyGen-FIPS204 ML-DSA-sigVer-FIPS204 ML-KEM-keyGen-FIPS203 ML-KEM-encapDecap-FIPS203; do \
      curl -fsSL -o "$f.json" "https://raw.githubusercontent.com/usnistgov/ACVP-Server/master/gen-val/json-files/$f/internalProjection.json" || true; done

ENTRYPOINT ["/bin/bash", "-c"]
CMD ["cd /audit/qpt_audit_stack && ./run_all.sh"]
