"""Parser for TOML configuration files."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from configdiff.parsers.base import BaseParser


class TomlParser(BaseParser):
    format_name = "toml"
    extensions = [".toml"]

    def parse(self, path: Path) -> dict[str, Any]:
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise ValueError(f"Cannot read {path}: {exc}") from exc

        try:
            data = tomllib.loads(raw.decode("utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Invalid TOML in {path}: {exc}") from exc

        return data
