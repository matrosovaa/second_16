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

## Stage 4 — installation order

Stage 4 calculates a safe installation order from the dependency graph.
Dependencies are listed before the package that requires them. The order is
calculated deterministically; a cycle is reported because it prevents a valid
topological installation order. If `--max-depth` cuts off the graph, the
program warns which packages were not fully explored.

Run with a local test repository:

```bash
./run_stage4.sh --package A \
  --repository tests/diamond-repository.txt \
  --test-mode --max-depth 10 --install-order
```

Check cycle handling:

```bash
./run_stage4.sh --package A \
  --repository tests/cycle-repository.txt \
  --test-mode --max-depth 10 --install-order
```

Compare with the real Alpine package manager using an Alpine repository:

```bash
./run_stage4.sh --package curl \
  --repository https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64/ \
  --max-depth 100 --install-order --compare-apk
```

The comparison uses `apk add --simulate`, so it does not install packages.
It uses the local `apk` command when available or a disposable Docker Alpine
container otherwise. Differences can occur because APK resolves package
versions, virtual dependencies, architecture and already installed packages;
the analyzer builds a name-based graph from one repository index.

## Stage 5 — D2 visualization

Stage 5 converts the graph into the D2 diagram language, prints the D2 source,
renders an SVG image and opens it in the default image viewer. By default the
SVG is written to a temporary file outside the repository. Use `--output` to
save it to a chosen path, or `--no-open` to skip opening the image.

Install the D2 command-line tool using the
[official installation instructions](https://d2lang.com/tour/install/):

```bash
curl -fsSL https://d2lang.com/install.sh | sh -s --
d2 version
```

Visualize one package:

```bash
./run_stage5.sh --package A \
  --repository tests/test-repository.txt \
  --test-mode --max-depth 10
```

The three-package demonstration uses packages `A`, `B` and `C` from the test
repository and opens each generated diagram:

```bash
./scripts/demo_stage5.sh
```

To save an image instead of using a temporary file:

```bash
./run_stage5.sh --package A \
  --repository tests/test-repository.txt \
  --test-mode --output graph-A.svg
```
