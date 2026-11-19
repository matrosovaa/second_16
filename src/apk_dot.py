"""Compare the analyzer's graph with the output of the `apk dot` command."""

import re
import shutil
import subprocess

from src.stage4 import docker_platform, repository_for_apk


SUCCESS_EXIT_CODE = 0
MAX_LISTED_EDGES = 20
DOT_EDGE = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')
VERSION_SUFFIX = re.compile(r"-\d[^-]*-r\d+$")
VIRTUAL_PREFIXES = ("so:", "cmd:", "pc:")
DOCKER_SCRIPT = (
    "printf '%s\\n' \"$1\" > /etc/apk/repositories && "
    "apk update > /dev/null && apk dot \"$2\""
)
DOT_REASONS = (
    "Possible reasons: the analyzer does not follow so:, cmd: and pc: "
    "dependencies, apk dot resolves virtual providers and prints the whole "
    "graph without a depth limit, node names in apk dot may carry versions, "
    "and the analyzer stops at --max-depth."
)


def build_dot_command(package, repository, apk_image):
    """Build a command that runs `apk dot` locally or in a Docker image."""
    directory = repository_for_apk(repository)
    apk_path = shutil.which("apk")
    if apk_path:
        return [apk_path, "dot", "--repository", directory, package]
    docker_path = shutil.which("docker")
    if not docker_path:
        raise RuntimeError(
            "APK and Docker were not found. Install apk or Docker to compare."
        )
    arguments = ["run", "--rm"]
    platform = docker_platform(directory)
    if platform:
        arguments.extend(["--platform", platform])
    arguments.extend([apk_image, "sh", "-c", DOCKER_SCRIPT])
    return [docker_path, *arguments, "apk-dot", directory, package]


def run_apk_dot(package, repository, apk_image):
    """Run `apk dot` and return its Graphviz output."""
    command = build_dot_command(package, repository, apk_image)
    result = subprocess.run(
        command, capture_output=True, text=True, check=False
    )
    if result.returncode != SUCCESS_EXIT_CODE:
        message = (result.stderr or result.stdout).strip()
        raise RuntimeError(message or "apk dot failed.")
    return result.stdout


def normalize_name(name):
    """Drop the version suffix from a package name printed by apk."""
    return VERSION_SUFFIX.sub("", name)


def parse_dot_edges(text):
    """Extract dependency edges from Graphviz text produced by apk dot."""
    edges = set()
    for source, target in DOT_EDGE.findall(text):
        edge = (normalize_name(source), normalize_name(target))
        if edge[0] != edge[1]:
            edges.add(edge)
    return edges


def split_virtual(edges):
    """Separate package-to-package edges from so:, cmd: and pc: edges."""
    virtual = {edge for edge in edges if edge[1].startswith(VIRTUAL_PREFIXES)}
    return edges - virtual, virtual


def graph_edges(graph):
    """Convert the analyzer's adjacency list to a set of edges."""
    return {
        (package, dependency)
        for package, dependencies in graph.items()
        for dependency in dependencies
    }


def format_edges(edges):
    """Format a limited, sorted list of edges for the terminal."""
    ordered = sorted(edges)
    lines = [
        f"  {source} -> {target}"
        for source, target in ordered[:MAX_LISTED_EDGES]
    ]
    if len(ordered) > MAX_LISTED_EDGES:
        hidden = len(ordered) - MAX_LISTED_EDGES
        lines.append(f"  ... and {hidden} more")
    return "\n".join(lines)


def print_edge_difference(title, edges):
    """Print one group of edges that exist in only one of the graphs."""
    print(f"{title}: {len(edges)}")
    if edges:
        print(format_edges(edges))


def print_dot_comparison(graph, dot_output):
    """Compare the analyzer's graph with the edges reported by apk dot."""
    ours = graph_edges(graph)
    real, virtual = split_virtual(parse_dot_edges(dot_output))
    print("\nComparison with apk dot:")
    print(f"Edges in the analyzer graph: {len(ours)}")
    print(f"Package-to-package edges in apk dot: {len(real)}")
    print(f"so:/cmd:/pc: edges in apk dot: {len(virtual)}")
    print_edge_difference("Only in the analyzer graph", ours - real)
    print_edge_difference("Only in apk dot", real - ours)
    if ours != real:
        print(DOT_REASONS)
    else:
        print("The graphs contain the same package-to-package edges.")
