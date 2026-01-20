# Adapted from Dockerfile at
# blog.trailofbits.com/2024/02/23/continuously-fuzzing-python-c-extensions

# Debian 12 (Bookworm) has Python 3.11, while 13 (Trixie) has Python 3.13,
# unsupported by Atheris as of January 2026.
FROM debian:13-slim

SHELL ["/bin/bash", "-eu", "-o", "pipefail", "-c"]

# Install system packages needed to build Atheris (and Clang) from source
RUN apt-get update \
    && apt-get upgrade --assume-yes --no-install-recommends \
    binutils \
    build-essential \
    cmake \
    git=1:2.39.* \
    python3-dev=3.11.* \
    python3-full=3.11.* \
    python3-pip=23.* \
    wget=1.21.* \
    xz-utils=5.4.* \
    && rm -rf /var/lib/apt/lists/*

RUN python3 --version

ENV APP_DIR="/app"
ENV CLANG_DIR="$APP_DIR/clang"
RUN mkdir -p $CLANG_DIR
WORKDIR $APP_DIR

ENV VIRTUAL_ENV="/opt/venv"
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ARG CLANG_URL=https://github.com/llvm/llvm-project/releases/download/llvmorg-17.0.6/clang+llvm-17.0.6-aarch64-linux-gnu.tar.xz
ARG CLANG_CHECKSUM=6dd62762285326f223f40b8e4f2864b5c372de3f7de0731cb7cd55ca5287b75a
ENV CLANG_FILE=clang.tar.xz

# Note that **two** spaces between checksum and file are significant:
# "a line with: checksum, a space, a character indicating input mode
# ('*' for binary, ' ' for text or where binary is insignificant),
# and name for each FILE".
RUN wget -q -O "$CLANG_FILE" "$CLANG_URL" && \
    echo "$CLANG_CHECKSUM  $CLANG_FILE" | sha256sum --check - && \
    tar xf "$CLANG_FILE" -C "$CLANG_DIR" --strip-components 1 && \
    rm $CLANG_FILE

# https://github.com/google/atheris#building-from-source
RUN LIBFUZZER_LIB=$($CLANG_DIR/bin/clang -print-file-name=libclang_rt.fuzzer_no_main.a) \
    python3 -m pip install --no-cache-dir --no-binary atheris atheris==3.0.0

# https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#step-1-compiling-your-extension
ENV CC="$CLANG_DIR/bin/clang"
ENV CFLAGS="-fsanitize=address,undefined,fuzzer-no-link"
ENV CXX="$CLANG_DIR/bin/clang++"
ENV CXXFLAGS="-fsanitize=address,undefined,fuzzer-no-link"
ENV LDSHARED="$CLANG_DIR/bin/clang -shared"

# Install poetry for further operations
RUN python3 -m pip install --no-cache-dir poetry==2.3.0

ARG OWNER=github.com/dupuy
ARG REPO=reliabot
ARG PKG=reliabot
ARG BRANCH=main

RUN git clone \
    --depth 1 \
    --branch "$BRANCH" \
    https://${OWNER}/${REPO}.git

WORKDIR ${APP_DIR}/${REPO}
RUN poetry install --with fuzz

# Allow Atheris to find fuzzer sanitizer shared libs
# https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#option-a-sanitizerlibfuzzer-preloads
#ENV LD_PRELOAD="$VIRTUAL_ENV/lib/python3.11/site-packages/asan_with_fuzzer.so"

# 1. Skip allocation failures and memory leaks for now, they are common, and low impact (DoS)
# 2. https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#leak-detection
# 3. Provide the symbolizer to turn virtual addresses to file/line locations
ENV ASAN_OPTIONS="allocator_may_return_null=1,detect_leaks=0,external_symbolizer_path=$CLANG_DIR/bin/llvm-symbolizer"

COPY reliabot_fuzzer.py reliabot_fuzzer.py

ENTRYPOINT ["python3", "reliabot_fuzzer.py"]
