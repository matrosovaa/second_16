"""Stage 4: calculate package installation order and compare it with APK."""

import argparse
import heapq
import re
import shutil
import subprocess
import sys

from src.alpine import read_apkindex
from src.graph import build_graph, read_test_repository
from src.main import validate_depth, validate_package, validate_repository


DEFAULT_DEPTH = 3
DEFAULT_APK_IMAGE = "alpine:3.20"
NO_DEPENDENCIES = 0
APK_INDEX_SUFFIX = "/APKINDEX.tar.gz"
DOCKER_PLATFORMS = {
    "x86_64": "linux/amd64",
    "aarch64": "linux/arm64",
    "armhf": "linux/arm/v6",
    "armv7": "linux/arm/v7",
}
INSTALL_LINE = re.compile(
    r"\bInstalling\s+([A-Za-z0-9][A-Za-z0-9+_.-]*)\s+\("
)


def build_parser():
    """Create command-line options for the installation-order stage."""
    parser = argparse.ArgumentParser(
        description="Show dependency installation order (variant 16, stage 4)."
    )
    parser.add_argument("--package", required=True, help="Package to analyze.")
    parser.add_argument(
        "--repository", required=True,
        help="Alpine repository URL or test file."
    )
    parser.add_argument(
        "--test-mode", action="store_true", help="Read a local test graph."
    )
    parser.add_argument(
        "--max-depth", type=int, default=DEFAULT_DEPTH,
        help="Maximum dependency depth (default: 3)."
    )
    parser.add_argument(
        "--install-order", action="store_true", required=True,
        help="Print dependencies in installation order."
    )
    parser.add_argument(
        "--compare-apk", action="store_true",
        help="Compare the order with a simulated APK installation."
    )
    parser.add_argument(
        "--apk-image", default=DEFAULT_APK_IMAGE,
        help="Docker image used when the apk command is unavailable."
    )
    return parser


def load_source(repository, test_mode):
    """Load dependency records from a test file or Alpine index."""
    if test_mode:
        return read_test_repository(repository)
    return read_apkindex(repository)


def build_install_order(graph):
    """Return a deterministic order with every dependency before its parent."""
    pending = {
        package: sum(item in graph for item in dependencies)
        for package, dependencies in graph.items()
    }
    dependents = {package: [] for package in graph}
    for package, dependencies in graph.items():
        for dependency in dependencies:
            if dependency in dependents:
                dependents[dependency].append(package)

    ready = [
        package for package, count in pending.items()
        if count == NO_DEPENDENCIES
    ]
    heapq.heapify(ready)
    order = []
    while ready:
        dependency = heapq.heappop(ready)
        order.append(dependency)
        for package in dependents[dependency]:
            pending[package] -= 1
            if pending[package] == NO_DEPENDENCIES:
                heapq.heappush(ready, package)

    if len(order) != len(graph):
        unresolved = sorted(set(graph) - set(order))
        names = ", ".join(unresolved)
        raise ValueError(f"Dependency cycle blocks installation order: {names}")
    return order


def format_install_order(order):
    """Format an installation order as a numbered terminal list."""
    return "\n".join(
        f"{number}. {package}"
        for number, package in enumerate(order, start=1)
    )


def find_depth_limited_packages(source, graph):
    """Find nodes whose dependencies were not explored because of the limit."""
    return sorted(
        package for package, dependencies in graph.items()
        if not dependencies and source.get(package)
    )


def repository_for_apk(repository):
    """Convert an APKINDEX archive URL to the repository directory URL."""
    if repository.endswith(APK_INDEX_SUFFIX):
        return repository[:-len(APK_INDEX_SUFFIX)]
    return repository.rstrip("/")


def docker_platform(repository):
    """Match a known Alpine repository architecture to a Docker platform."""
    architecture = repository_for_apk(repository).rsplit("/", 1)[-1]
    return DOCKER_PLATFORMS.get(architecture)


def build_apk_command(package, repository, apk_image):
    """Build a safe simulation command using apk or a Docker Alpine image."""
    apk_args = [
        "add", "--simulate", "--no-progress", "--repository",
        repository_for_apk(repository), package
    ]
    apk_path = shutil.which("apk")
    if apk_path:
        return [apk_path, *apk_args]
    docker_path = shutil.which("docker")
    if docker_path:
        repository = repository_for_apk(repository)
        script = (
            "printf '%s\\n' \"$1\" > /etc/apk/repositories && "
            "apk update && apk add --simulate --no-progress \"$2\""
        )
        docker_args = ["run", "--rm"]
        platform = docker_platform(repository)
        if platform:
            docker_args.extend(["--platform", platform])
        docker_args.extend([apk_image, "sh", "-c", script])
        return [docker_path, *docker_args, "stage4", repository, package]
    raise RuntimeError(
        "APK and Docker were not found. Install apk or Docker to compare."
    )


def run_apk_simulation(package, repository, apk_image):
    """Run APK in simulation mode without changing the local system."""
    command = build_apk_command(package, repository, apk_image)
    result = subprocess.run(
        command, capture_output=True, text=True, check=False
    )
    output = "\n".join(
        part.strip() for part in (result.stdout, result.stderr) if part.strip()
    )
    if result.returncode != 0:
        raise RuntimeError(output or "APK simulation failed.")
    return output


def parse_apk_installation_order(output):
    """Extract package names from APK's simulated installation messages."""
    return INSTALL_LINE.findall(output)


def print_comparison(expected, output):
    """Display APK's order and compare packages shared by both results."""
    actual = parse_apk_installation_order(output)
    print("\nAPK simulation output:")
    print(output or "No output from APK.")
    if not actual:
        print("Could not extract package names from APK output.")
        return
    print("APK installation order: " + " -> ".join(actual))

    expected_common = [name for name in expected if name in actual]
    actual_common = [name for name in actual if name in expected]
    if expected_common == actual_common:
        print("\nComparison: the shared packages have the same order.")
    else:
        print("\nComparison: package order differs from the analyzer.")
        print(
            "Possible reasons: installed packages, virtual providers, "
            "versions, architecture or repository priority."
        )
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing:
        print("Not listed by APK: " + ", ".join(missing))
    if extra:
        print("Only listed by APK: " + ", ".join(extra))
    if missing or extra:
        print(
            "Possible reasons: preinstalled packages, virtual providers, "
            "versions, architecture or repository priority."
        )


def validate_stage_arguments(args):
    """Validate the shared configuration before reading repository data."""
    validate_package(args.package)
    validate_repository(args.repository, args.test_mode)
    validate_depth(args.max_depth)
    if args.compare_apk and args.test_mode:
        raise ValueError("APK comparison requires a real repository URL.")


def main(argv=None):
    """Run stage 4 and optionally compare its result with the APK manager."""
    args = build_parser().parse_args(argv)
    try:
        validate_stage_arguments(args)
        source = load_source(args.repository, args.test_mode)
        graph = build_graph(source, args.package, args.max_depth)
        order = build_install_order(graph)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    print(f"Installation order for {args.package}:")
    print(format_install_order(order))
    limited = find_depth_limited_packages(source, graph)
    if limited:
        print("Depth limit reached for: " + ", ".join(limited))

    if args.compare_apk:
        try:
            output = run_apk_simulation(
                args.package, args.repository, args.apk_image
            )
        except (OSError, RuntimeError) as error:
            print(f"APK comparison error: {error}", file=sys.stderr)
            return 2
        print_comparison(order, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
