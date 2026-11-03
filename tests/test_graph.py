"""Tests for BFS recursion, depth limits and cyclic repositories."""

import tempfile
import unittest
from pathlib import Path

from src.graph import build_graph, read_test_repository


class GraphTests(unittest.TestCase):
    """Exercise several repository shapes and validation errors."""

    def test_transitive(self):
        source = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        result = build_graph(source, "A", 3)
        self.assertEqual(result["B"], ["D"])
        self.assertIn("D", result)

    def test_depth_zero(self):
        self.assertEqual(build_graph({"A": ["B"]}, "A", 0), {"A": []})

    def test_depth_one(self):
        source = {"A": ["B"], "B": ["C"], "C": []}
        self.assertEqual(build_graph(source, "A", 1),
                         {"A": ["B"], "B": []})

    def test_cycle(self):
        source = {"A": ["B"], "B": ["C"], "C": ["A"]}
        result = build_graph(source, "A", 5)
        self.assertEqual(result["C"], ["A"])
        self.assertEqual(set(result), {"A", "B", "C"})

    def test_diamond(self):
        source = {"A": ["B", "C"], "B": ["D"],
                  "C": ["D"], "D": []}
        self.assertEqual(build_graph(source, "A", 3)["C"], ["D"])

    def test_missing_package(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            build_graph({"A": []}, "Z", 2)

    def test_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.txt"
            path.write_text("# example\nA: B, C\nB: A\nC:\n")
            self.assertEqual(read_test_repository(path)["A"], ["B", "C"])

    def test_invalid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.txt"
            path.write_text("A: wrong\n")
            with self.assertRaisesRegex(ValueError, "uppercase"):
                read_test_repository(path)


if __name__ == "__main__":
    unittest.main()
