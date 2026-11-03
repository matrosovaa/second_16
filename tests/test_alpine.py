"""Tests for reading and parsing Alpine package indexes."""

import io
import tarfile
import unittest
from unittest.mock import patch

from src.alpine import direct_dependencies, index_url, parse_index, read_apkindex


SAMPLE_INDEX = (
    "P:app\nV:1.0-r0\nD:lib>=1.0 busybox so:libc.musl-x86_64.so.1\n\n"
    "P:lib\nV:1.0-r0\nD:busybox\n\n"
    "P:busybox\nV:1.0-r0\n\n"
)


class AlpineIndexTests(unittest.TestCase):
    """Check parsing, direct dependencies and archive loading."""

    def test_parse_index(self):
        self.assertEqual(parse_index(SAMPLE_INDEX)["app"], ["busybox", "lib"])

    def test_empty_dependencies(self):
        self.assertEqual(parse_index(SAMPLE_INDEX)["busybox"], [])

    def test_missing_package(self):
        with self.assertRaisesRegex(ValueError, "not found"):
            direct_dependencies(parse_index(SAMPLE_INDEX), "missing")

    def test_index_url(self):
        self.assertEqual(index_url("https://example.org/main/"),
                         "https://example.org/main/APKINDEX.tar.gz")

    def test_read_archive(self):
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w:gz") as tar:
            payload = SAMPLE_INDEX.encode()
            info = tarfile.TarInfo("APKINDEX")
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))

        class Response:
            """Simple context-managed fake HTTP response."""

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return raw.getvalue()

        with patch("src.alpine.urlopen", return_value=Response()):
            index = read_apkindex("https://example.org/main/")
        self.assertIn("lib", index)


if __name__ == "__main__":
    unittest.main()
