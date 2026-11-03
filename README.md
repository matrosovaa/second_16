# Variant 16 — Stage 3

## Overview

A command-line Alpine Linux (`apk`) dependency analyzer implemented with
Python's standard library. It downloads package records directly from an
Alpine `APKINDEX.tar.gz` or loads a local text test repository.

Stage 2 retrieved direct dependencies; **stage 3** traverses transitive
dependencies with **recursive BFS**. Each recursive call processes the next
breadth-first layer. A visited set handles cycles, and `--max-depth` limits
how many edges are explored. Cyclic edges remain in the reported graph.

## CLI parameters

| Option | Description |
|---|---|
| `--package NAME` | Package to analyze, required |
| `--repository PATH_OR_URL` | Remote Alpine repository directory or local graph file |
| `--test-mode` | Interpret repository as a local graph file |
| `--max-depth N` | BFS limit in edges, integer 0–100; default 3 |

The remote URL must point to a specific repository, e.g. a `main/x86_64/`
folder containing `APKINDEX.tar.gz`, not simply the Alpine website root.
Special virtual dependencies (`so:`, `cmd:`, `pc:`) are not resolved. Named
package constraints are normalized to names for this graph demonstration.

## Run (macOS / Linux)

```bash
./run.sh --package A --repository tests/test-repository.txt --test-mode
./run.sh --package A --repository tests/cycle-repository.txt --test-mode
./run.sh --package A --repository tests/diamond-repository.txt \
  --test-mode --max-depth 1
./run.sh --package busybox --repository \
  https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/ \
  --max-depth 2
```

For Windows, use `run.bat` instead of `./run.sh`.

## Test repository format

Packages use **uppercase Latin letters**. Each line is `NAME: DEP1, DEP2`;
blank dependency lists are permitted. Blank lines and `#` comments are
ignored. Examples are in `tests/`.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Limitations and errors

Invalid options, missing files or packages, malformed graph files,
unavailable repositories and damaged archive data produce error messages.
This educational tool does not implement Alpine virtual package providers,
architecture selection, pinning or cross-repository version resolution.
The output is a sorted adjacency list, not an image (visualization is stage 5).
