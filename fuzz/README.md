# Fuzzing reliabot

This directory has resources for fuzzing `reliabot` using
[Atheris](https://github.com/google/atheris), a coverage-guided fuzzer for
Python.

## Prerequisites

- **Linux** (recommended) or **macOS** (using Docker).
- **Poetry 2.3+** for dependency management.
- **Python 3.11—3.12** (`atheris` does not yet support Python 3.13+).
- `libFuzzer` support (not present in macOS pre-installed Clang/LLVM).

## Running Locally

1. **Install Atheris**:

   > Note: On macOS, the default Apple Clang does NOT include libFuzzer.
   > Installing a newer LLVM with Homebrew won't work unless you rebuild Python
   > using the newer LLVM as well. Instead, you should follow the instructions
   > for running Atheris in Docker. However, these instructions should work on
   > Linux systems with all the packages specified in the Dockerfile installed.

   ```sh
   poetry env use 3.11
   poetry install --with fuzz
   ```

   > Note: You can also use Python 3.12. For consistency with Docker builds
   > using Debian 12 (with Python 3.11) these instructions also use 3.11.

2. **Run the fuzzer**:

   ```sh
   # Run for 10 seconds (check for immediate crashes)
   poetry run python3.11 fuzz/reliabot_fuzzer.py -max_total_time=10

   # Run indefinitely
   poetry run python3.11 fuzz/reliabot_fuzzer.py
   ```

## Running with Docker (recommended for macOS)

Since Atheris requires a specific Clang setup, using Docker may be easier.

1. **Build the Docker image**:

   ```sh
   docker buildx build \
       --tag reliabot-fuzz \
       --attest type=provenance,mode=max,version=v1 \
       fuzz
   ```

2. **Run the fuzzer**:

   ```sh
   docker run --rm reliabot-fuzz
   ```
