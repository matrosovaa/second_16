"""Stage 5: create and display D2 dependency diagrams."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from src.alpine import read_apkindex
from src.apk_dot import print_dot_comparison, run_apk_dot
from src.graph import build_graph, read_test_repository
from src.main import validate_depth, validate_package, validate_repository
from src.stage4 import DEFAULT_APK_IMAGE


DEFAULT_DEPTH = 3
SUCCESS_EXIT_CODE = 0
ROOT_FILL = "#e8f1ff"
ROOT_STROKE = "#356a9a"


def build_parser():
    """Create command-line options for dependency visualization."""
    parser = argparse.ArgumentParser(
        description="Visualize dependencies with D2 (variant 16, stage 5)."
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
        "--output", help="Optional path for the generated SVG image."
    )
    parser.add_argument(
        "--no-open", action="store_true",
        help="Create the SVG without opening the image viewer."
    )
    parser.add_argument(
        "--compare-apk", action="store_true",
        help="Compare the graph with the output of apk dot."
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


def escape_label(value):
    """Quote a package name safely for a D2 string label."""
    return json.dumps(value, ensure_ascii=False)


def build_d2(graph, root):
    """Convert the dependency adjacency list to a D2 diagram description."""
    if root not in graph:
        raise ValueError(f"Package not found in graph: {root}")

    packages = sorted(graph)
    node_ids = {
        package: f"package_{index}"
        for index, package in enumerate(packages)
    }
    lines = ["direction: right", ""]
    for package in packages:
        node_id = node_ids[package]
        label = escape_label(package)
        if package == root:
            lines.extend([
                f"{node_id}: {label} {{",
                f'  style.fill: "{ROOT_FILL}"',
                f'  style.stroke: "{ROOT_STROKE}"',
                "}"
            ])
        else:
            lines.append(f"{node_id}: {label}")

    for package in packages:
        for dependency in sorted(graph[package]):
            if dependency in node_ids:
                lines.append(
                    f"{node_ids[package]} -> {node_ids[dependency]}"
                )
    return "\n".join(lines) + "\n"


def render_d2(source, output_path=None):
    """Render D2 text to SVG with the installed D2 command-line tool."""
    d2_path = shutil.which("d2")
    if not d2_path:
        raise RuntimeError(
            "D2 was not found. Install it using the official D2 instructions."
        )

    result = subprocess.run(
        [d2_path, "--stdout-format=svg", "-", "-"],
        input=source, capture_output=True, text=True, check=False
    )
    if result.returncode != SUCCESS_EXIT_CODE:
        raise RuntimeError(result.stderr.strip() or "D2 rendering failed.")

    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        handle = tempfile.NamedTemporaryFile(
            prefix="variant16-", suffix=".svg", delete=False
        )
        path = Path(handle.name)
        handle.close()
    path.write_text(result.stdout, encoding="utf-8")
    return path


def open_diagram(path):
    """Open the generated SVG in the operating system's default viewer."""
    if sys.platform == "darwin":
        command = ["open", str(path)]
    elif os.name == "nt":
        os.startfile(str(path))
        return
    else:
        command = ["xdg-open", str(path)]
    subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def validate_stage_arguments(args):
    """Validate the shared configuration before reading repository data."""
    validate_package(args.package)
    validate_repository(args.repository, args.test_mode)
    validate_depth(args.max_depth)
    if args.compare_apk and args.test_mode:
        raise ValueError("APK comparison requires a real repository URL.")


def compare_with_apk(args, graph):
    """Run apk dot and print how its graph differs from the analyzer's."""
    output = run_apk_dot(args.package, args.repository, args.apk_image)
    print_dot_comparison(graph, output)


def show_image(diagram, args):
    """Render the diagram to SVG and open it unless opening is disabled."""
    image_path = render_d2(diagram, args.output)
    print(f"SVG image: {image_path}")
    if args.no_open:
        return
    try:
        open_diagram(image_path)
    except OSError as error:
        print(f"Could not open the image automatically: {error}")


def run_visualization(args):
    """Build the graph, print its D2 text, show the image, compare with apk."""
    validate_stage_arguments(args)
    source = load_source(args.repository, args.test_mode)
    graph = build_graph(source, args.package, args.max_depth)
    diagram = build_d2(graph, args.package)
    print(f"D2 description for {args.package}:")
    print(diagram, end="")
    show_image(diagram, args)
    if args.compare_apk:
        compare_with_apk(args, graph)


def main(argv=None):
    """Run stage 5 and report any failure as a short error message."""
    args = build_parser().parse_args(argv)
    try:
        run_visualization(args)
    except (OSError, RuntimeError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
