# Variant 16 — Stage 1

## Overview

A minimal command-line prototype for a dependency graph visualizer.
This stage implements configuration through command-line options and
validates every user-configurable parameter.

The project uses Python standard-library modules only. Dependency
retrieval and graph construction are not part of stage 1.

## Parameters

| Option | Required | Description |
|---|---:|---|
| `--package` | Yes | Package name to analyze |
| `--repository` | Yes | Repository URL or test repository file path |
| `--test-mode` | No | Enables local test repository mode |
| `--max-depth` | No | Maximum dependency depth, from 0 to 100; default is 3 |

In real mode, `--repository` must be an HTTP or HTTPS URL.
In test mode, it must point to an existing file.

## Requirements

- Python 3.10 or newer
- No third-party libraries

## Run

Linux/macOS:

```bash
./run.sh --package curl --repository https://dl-cdn.alpinelinux.org/alpine/
```

Windows:

```bat
run.bat --package curl --repository https://dl-cdn.alpinelinux.org/alpine/
```

Test mode:

```bash
./run.sh --package demo --repository ./tests/test-repository.txt --test-mode
```

Set maximum depth:

```bash
./run.sh --package curl --repository https://example.org/alpine/ --max-depth 5
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Error handling

The application reports errors for:
- missing required command-line options;
- invalid package names;
- an empty repository parameter;
- an invalid URL in real mode;
- a missing test repository file;
- a test repository path that is not a file;
- a negative maximum depth;
- a maximum depth greater than 100.

Invalid values produce an error message and exit code `2`.
A successful run prints all configuration parameters as key-value pairs.

## Stage boundary

This implementation covers only stage 1. It does not download package
metadata, resolve dependencies, or build a dependency graph.
