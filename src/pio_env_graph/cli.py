import argparse
import sys
from pathlib import Path

from pio_env_graph.parser import parse
from pio_env_graph.renderers.dot import render


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pio-env-graph",
        description="Visualize PlatformIO environment dependency graph as Graphviz DOT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  pio-env-graph                              auto-discover ./platformio.ini
  pio-env-graph /path/to/platformio.ini      explicit path
  pio-env-graph -o graph.dot                 write to file
  pio-env-graph | dot -Tpng -o graph.png     render to PNG
  pio-env-graph | dot -Tsvg -o graph.svg     render to SVG
  pio-env-graph -d BT                        bottom-to-top layout
  pio-env-graph | dot -Tpng | display -      render and display immediately
  pio-env-graph --refs                       include ${section.key} references
""",
    )
    parser.add_argument(
        "ini_file",
        nargs="?",
        default=None,
        help="Path to platformio.ini (default: ./platformio.ini)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "-d",
        "--direction",
        default="RL",
        choices=["TB", "BT", "LR", "RL"],
        help="Graph direction (default: RL)",
    )
    parser.add_argument(
        "--refs",
        action="store_true",
        default=False,
        help="Show ${section.key} value references as dashed edges",
    )
    args = parser.parse_args()

    # Resolve INI path
    if args.ini_file:
        ini_path = Path(args.ini_file)
    else:
        ini_path = Path("platformio.ini")

    if not ini_path.exists():
        print(f"Error: {ini_path} not found", file=sys.stderr)
        sys.exit(1)

    graph = parse(ini_path)
    dot_output = render(graph, rankdir=args.direction, show_refs=args.refs)

    if args.output:
        Path(args.output).write_text(dot_output, encoding="utf-8")
    else:
        sys.stdout.write(dot_output)
