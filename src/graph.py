"""Recursive breadth-first dependency traversal with a depth limit."""

import re
from pathlib import Path


TEST_NAME = re.compile(r"^[A-Z]+$")


def read_test_repository(filename):
    """Read a text graph containing lines such as `A: B, C`."""
    graph = {}
    for number, raw in enumerate(Path(filename).read_text(
            encoding="utf-8").splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Line {number}: expected 'A: B, C'.")
        name, values = line.split(":", 1)
        name = name.strip()
        children = values.replace(",", " ").split()
        if not TEST_NAME.fullmatch(name):
            raise ValueError(f"Line {number}: invalid package '{name}'.")
        if not all(TEST_NAME.fullmatch(child) for child in children):
            raise ValueError(f"Line {number}: use uppercase Latin names.")
        if name in graph:
            raise ValueError(f"Line {number}: duplicate package '{name}'.")
        graph[name] = sorted(set(children))
    return graph


def _bfs_level(source, frontier, depth, limit, visited, graph):
    """Visit one breadth-first layer and recursively process the next."""
    if not frontier or depth >= limit:
        return
    next_frontier = []
    for package in frontier:
        children = source.get(package, [])
        graph[package] = list(children)
        for child in children:
            graph.setdefault(child, [])
            if child not in visited:
                visited.add(child)
                next_frontier.append(child)
    _bfs_level(source, next_frontier, depth + 1, limit, visited, graph)


def build_graph(source, root, max_depth):
    """Collect reachable dependencies via recursive level-by-level BFS."""
    if root not in source:
        raise ValueError(f"Package not found in repository: {root}")
    graph = {root: []}
    _bfs_level(source, [root], 0, max_depth, {root}, graph)
    return graph


def format_graph(graph):
    """Render a deterministic adjacency list, including cycle edges."""
    return "\n".join(
        f"{node}: {', '.join(children) if children else '(none)'}"
        for node, children in sorted(graph.items())
    )
