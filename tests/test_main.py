"""Unit tests for stage-one parameter validation."""

import tempfile
import unittest
from pathlib import Path

from src.main import (
    validate_depth,
    validate_package,
    validate_repository,
)


class PackageValidationTests(unittest.TestCase):
    """Check package name validation."""

    def test_valid_package(self):
        validate_package("python3-dev")

    def test_empty_package(self):
        with self.assertRaises(ValueError):
            validate_package("")

    def test_invalid_package(self):
        with self.assertRaises(ValueError):
            validate_package("bad package")


class DepthValidationTests(unittest.TestCase):
    """Check maximum dependency depth validation."""

    def test_valid_depth(self):
        validate_depth(3)

    def test_negative_depth(self):
        with self.assertRaises(ValueError):
            validate_depth(-1)

    def test_too_large_depth(self):
        with self.assertRaises(ValueError):
            validate_depth(101)


class RepositoryValidationTests(unittest.TestCase):
    """Check real and test repository parameter validation."""

    def test_valid_url(self):
        validate_repository("https://dl-cdn.alpinelinux.org/alpine/", False)

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            validate_repository("ftp://example.com/repo", False)

    def test_empty_repository(self):
        with self.assertRaises(ValueError):
            validate_repository(" ", False)

    def test_existing_test_file(self):
        with tempfile.TemporaryDirectory() as folder:
            test_file = Path(folder) / "repository.txt"
            test_file.write_text("A: B", encoding="utf-8")
            validate_repository(str(test_file), True)

    def test_missing_test_file(self):
        with self.assertRaises(ValueError):
            validate_repository("missing-repository.txt", True)


if __name__ == "__main__":
    unittest.main()
