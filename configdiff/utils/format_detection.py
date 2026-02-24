"""Detect config format from file extension."""

from __future__ import annotations

from pathlib import Path

from configdiff.parsers.registry import ParserRegistry


def detect_format(path: Path) -> str:
    """Return the format name for *path* based on its file extension.

    Raises
    ------
    ValueError
        If the extension is not recognised.
    """
    suffix = path.suffix.lower()
    if not suffix:
        raise ValueError(
            f"Cannot detect format for {path}: no file extension. "
            f"Supported extensions: {sorted(ParserRegistry.supported_extensions())}"
        )
    parser = ParserRegistry.get_parser(suffix)
    return parser.format_name
