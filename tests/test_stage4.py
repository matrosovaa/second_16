"""Tests for dependency installation order and APK output parsing."""

import unittest

from src.stage4 import (
    build_install_order,
    parse_apk_installation_order,
    repository_for_apk,
)


class InstallationOrderTests(unittest.TestCase):
    """Check topological order, cycles and deterministic results."""

    def test_chain(self):
        graph = {"A": ["B"], "B": ["C"], "C": []}
        self.assertEqual(build_install_order(graph), ["C", "B", "A"])

    def test_diamond(self):
        graph = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        }
        self.assertEqual(
            build_install_order(graph), ["D", "B", "C", "A"]
        )

    def test_single_package(self):
        self.assertEqual(build_install_order({"A": []}), ["A"])

    def test_cycle(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        with self.assertRaisesRegex(ValueError, "cycle"):
            build_install_order(graph)


class ApkOutputTests(unittest.TestCase):
    """Check parsing of simulated APK output and repository URLs."""

    def test_parse_installation_order(self):
        output = (
            "(1/3) Installing libx (1.0-r0)\n"
            "(2/3) Installing liby (2.0-r0)\n"
            "(3/3) Installing app (3.0-r0)\n"
        )
        self.assertEqual(
            parse_apk_installation_order(output), ["libx", "liby", "app"]
        )

    def test_repository_directory(self):
        url = "https://example.org/main/x86_64/APKINDEX.tar.gz"
        self.assertEqual(
            repository_for_apk(url), "https://example.org/main/x86_64"
        )


if __name__ == "__main__":
    unittest.main()
