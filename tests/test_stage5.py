"""Tests for D2 dependency diagram generation."""

import unittest

from src.stage5 import build_d2


class D2DiagramTests(unittest.TestCase):
    """Check labels, dependency arrows and root-node highlighting."""

    def test_nodes_and_edges(self):
        graph = {"A": ["B", "C"], "B": ["D"], "C": [], "D": []}
        diagram = build_d2(graph, "A")
        self.assertIn('package_0: "A" {', diagram)
        self.assertIn("package_0 -> package_1", diagram)
        self.assertIn("package_0 -> package_2", diagram)
        self.assertIn("package_1 -> package_3", diagram)

    def test_root_is_highlighted(self):
        diagram = build_d2({"A": [], "B": []}, "B")
        self.assertIn('style.fill: "#e8f1ff"', diagram)
        self.assertIn('style.stroke: "#356a9a"', diagram)

    def test_missing_root(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            build_d2({"A": []}, "Z")


if __name__ == "__main__":
    unittest.main()
