"""ConfigDiff CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import configdiff
from configdiff.diff_engine import compare
from configdiff.output import get_formatter
from configdiff.parsers import ParserRegistry  # noqa: F401 (triggers auto-registration)
from configdiff.utils.format_detection import detect_format
from configdiff.utils.logging import setup_logging

EXIT_NO_CHANGES = 0
EXIT_CHANGES = 1
EXIT_ERROR = 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="configdiff",
        description=(
            "Structure-aware configuration diff tool. "
            "Compares two config files semantically and reports "
            "added, removed, modified, and type-changed values."
        ),
        epilog="Example: configdiff before.yaml after.yaml --format json",
    )
    parser.add_argument(
        "before",
        type=Path,
        metavar="BEFORE",
        help="Path to the original (before) config file.",
    )
    parser.add_argument(
        "after",
        type=Path,
        metavar="AFTER",
        help="Path to the updated (after) config file.",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "yaml"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--ignore-order",
        action="store_true",
        default=False,
        help="Ignore list ordering when comparing arrays.",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=Path,
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose/debug logging to stderr.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {configdiff.__version__}",
    )
    return parser


def _error(message: str) -> int:
    print(f"Error: {message}", file=sys.stderr)
    return EXIT_ERROR


def run(argv: list[str] | None = None) -> int:
    """Execute the CLI and return an exit code (for testability)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    setup_logging(verbose=args.verbose)

    before_path: Path = args.before
    after_path: Path = args.after

    if not before_path.is_file():
        return _error(f"File not found: {before_path}")
    if not after_path.is_file():
        return _error(f"File not found: {after_path}")

    try:
        before_format = detect_format(before_path)
        after_format = detect_format(after_path)
    except ValueError as exc:
        return _error(str(exc))

    if before_format != after_format:
        return _error(
            f"Format mismatch: {before_path} is {before_format}, "
            f"but {after_path} is {after_format}. "
            "Both files must use the same configuration format."
        )

    fmt_parser = ParserRegistry.get_parser(before_format)

    try:
        before_data = fmt_parser.parse(before_path)
        after_data = fmt_parser.parse(after_path)
    except (ValueError, FileNotFoundError) as exc:
        return _error(str(exc))

    result = compare(
        before_data,
        after_data,
        ignore_order=args.ignore_order,
        metadata={
            "before": str(before_path),
            "after": str(after_path),
            "format": before_format,
        },
    )

    try:
        formatter = get_formatter(args.output_format)
    except ValueError as exc:
        return _error(str(exc))

    output = formatter.format(result)

    if args.output_file:
        try:
            args.output_file.write_text(output + "\n", encoding="utf-8")
        except OSError as exc:
            return _error(f"Cannot write to {args.output_file}: {exc}")
    else:
        print(output)

    return EXIT_CHANGES if result.has_changes else EXIT_NO_CHANGES


def main() -> None:
    """Entry point registered in pyproject.toml."""
    sys.exit(run())


if __name__ == "__main__":
    main()
