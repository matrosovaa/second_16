"""CLI prototype for dependency graph configuration (variant 16)."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from src.alpine import direct_dependencies, read_apkindex


PACKAGE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+_.-]*$")
MAX_ALLOWED_DEPTH = 100
DEFAULT_DEPTH = 3


def build_parser():
    """Create a command-line parser with all stage-one options."""
    parser = argparse.ArgumentParser(
        description="Alpine Linux dependency analyzer (variant 16)."
    )
    parser.add_argument(
        "--package", required=True,
        help="Name of the package to analyze."
    )
    parser.add_argument(
        "--repository", required=True,
        help="Repository URL or path to a test repository file."
    )
    parser.add_argument(
        "--test-mode", action="store_true",
        help="Use a local test repository instead of a real repository."
    )
    parser.add_argument(
        "--max-depth", type=int, default=DEFAULT_DEPTH,
        help="Maximum dependency analysis depth (default: 3)."
    )
    return parser


def validate_package(package):
    """Validate the package name."""
    if not package or not PACKAGE_PATTERN.fullmatch(package):
        raise ValueError(
            "Invalid package name: use letters, digits, '.', '_', '+', or '-'."
        )


def validate_depth(depth):
    """Validate the maximum dependency depth."""
    if depth < 0:
        raise ValueError("Maximum depth cannot be negative.")
    if depth > MAX_ALLOWED_DEPTH:
        raise ValueError(
            f"Maximum depth cannot exceed {MAX_ALLOWED_DEPTH}."
        )


def validate_repository(repository, test_mode):
    """Validate a local test path or a remote repository URL."""
    if not repository.strip():
        raise ValueError("Repository URL or test file path is required.")

    if test_mode:
        path = Path(repository).expanduser()
        if not path.exists():
            raise ValueError(f"Test repository file does not exist: {path}")
        if not path.is_file():
            raise ValueError("Test repository path must point to a file.")
        try:
            with path.open("r", encoding="utf-8"):
                pass
        except OSError as error:
            raise ValueError("Test repository file cannot be read.") from error
        return

    parsed = urlparse(repository)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            "In real mode, repository must be a valid HTTP or HTTPS URL."
        )


def validate_arguments(args):
    """Validate all user-configurable command-line parameters."""
    validate_package(args.package)
    validate_repository(args.repository, args.test_mode)
    validate_depth(args.max_depth)


def print_configuration(args):
    """Print all configuration values as key-value pairs."""
    print("Configuration:")
    print(f"package = {args.package}")
    print(f"repository = {args.repository}")
    print(f"test_mode = {args.test_mode}")
    print(f"max_depth = {args.max_depth}")


def main(argv=None):
    """Run the stage-one command-line application."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        validate_arguments(args)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    if args.test_mode:
        print_configuration(args)
        print("Test repository analysis is available in stage 3.")
        return 0

    try:
        index = read_apkindex(args.repository)
        dependencies = direct_dependencies(index, args.package)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(f"Direct dependencies of {args.package}:")
    for dependency in dependencies:
        print(f"- {dependency}")
    if not dependencies:
        print("(none)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
