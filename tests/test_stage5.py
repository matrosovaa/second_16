"""Tests for D2 dependency diagram generation."""

import unittest

from src.stage5 import build_d2, main


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


class CommandLineTests(unittest.TestCase):
    """Check the argument validation of the stage-5 command."""

    def test_compare_requires_real_repository(self):
        code = main([
            "--package", "A", "--repository", "tests/test-repository.txt",
            "--test-mode", "--compare-apk", "--no-open",
        ])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
