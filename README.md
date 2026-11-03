# Variant 16 — Stage 2

## Overview

A CLI for retrieving **direct** dependencies of Alpine Linux (`apk`)
packages. Uses Python's standard library, not apk or dependency libraries.
The program reads `APKINDEX.tar.gz` from an Alpine repository directory,
extracts the `APKINDEX` text file, and parses its `P:` and `D:` records.

## Options

- `--package NAME`: the package to analyze (required).
- `--repository URL`: URL of a specific Alpine repository directory
  containing `APKINDEX.tar.gz` (required), for example
  `https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/`.
- `--test-mode`: reserved for local test repositories in stage 3.
- `--max-depth N`: depth 0–100, default 3 (used in stage 3).

Alpine dependency constraints such as `lib>=1` are normalized to `lib`.
Special `so:`, `cmd:` and `pc:` dependencies are excluded because they
are virtual capabilities, not direct package names. This stage reads the
specific repository index supplied by the user; it does not combine indexes
from separate repositories or resolve provider aliases.

## Run

Python 3.10+ is required. On Linux/macOS:

```bash
./run.sh --package busybox --repository \
  https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/
```

On Windows use `run.bat` with the same options.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Error handling

Invalid CLI options, missing packages, network failures and malformed
repository archives cause clear error messages and a nonzero exit code.
No external Python dependencies are required.
