"""Tests for the comparison with the output of apk dot."""

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from src.apk_dot import (
    build_dot_command,
    graph_edges,
    normalize_name,
    parse_dot_edges,
    print_dot_comparison,
    split_virtual,
)


DOT_TEXT = (
    'digraph "apkindex" {\n'
    '  "app-1.0-r0" -> "lib"\n'
    '  "app-1.0-r0" -> "so:libc.musl-x86_64.so.1"\n'
    '  "lib" -> "musl-1.2.5-r0" [color=red]\n'
    '  "lib" -> "lib"\n'
    "}\n"
)


class ParsingTests(unittest.TestCase):
    """Check Graphviz parsing and name normalization."""

    def test_normalize_name(self):
        self.assertEqual(normalize_name("musl-1.2.5-r0"), "musl")
        self.assertEqual(normalize_name("lib"), "lib")

    def test_parse_edges(self):
        edges = parse_dot_edges(DOT_TEXT)
        self.assertEqual(
            edges,
            {
                ("app", "lib"),
                ("app", "so:libc.musl-x86_64.so.1"),
                ("lib", "musl"),
            },
        )

    def test_split_virtual(self):
        real, virtual = split_virtual(parse_dot_edges(DOT_TEXT))
        self.assertEqual(real, {("app", "lib"), ("lib", "musl")})
        self.assertEqual(virtual, {("app", "so:libc.musl-x86_64.so.1")})

    def test_graph_edges(self):
        graph = {"A": ["B", "C"], "B": [], "C": []}
        self.assertEqual(graph_edges(graph), {("A", "B"), ("A", "C")})


class ReportTests(unittest.TestCase):
    """Check the printed comparison report."""

    @staticmethod
    def report(graph):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            print_dot_comparison(graph, DOT_TEXT)
        return buffer.getvalue()

    def test_difference_is_explained(self):
        report = self.report({"app": ["lib"], "lib": []})
        self.assertIn("Only in apk dot: 1", report)
        self.assertIn("lib -> musl", report)
        self.assertIn("Possible reasons", report)

    def test_equal_graphs(self):
        graph = {"app": ["lib"], "lib": ["musl"], "musl": []}
        self.assertIn("same package-to-package edges", self.report(graph))


class CommandTests(unittest.TestCase):
    """Check how the apk dot command is assembled."""

    def test_docker_command(self):
        def fake_which(name):
            return "/usr/bin/docker" if name == "docker" else None

        with mock.patch("src.apk_dot.shutil.which", fake_which):
            command = build_dot_command(
                "curl", "https://example.org/main/x86_64/", "alpine:3.20"
            )
        self.assertEqual(command[:3], ["/usr/bin/docker", "run", "--rm"])
        self.assertIn("linux/amd64", command)
        self.assertEqual(command[-1], "curl")

    def test_nothing_available(self):
        with mock.patch("src.apk_dot.shutil.which", lambda name: None):
            with self.assertRaisesRegex(RuntimeError, "Docker"):
                build_dot_command("curl", "https://x/y", "alpine:3.20")


if __name__ == "__main__":
    unittest.main()
