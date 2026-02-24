"""Parser for JSON configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from configdiff.parsers.base import BaseParser


class JsonParser(BaseParser):
    format_name = "json"
    extensions = [".json"]

    def parse(self, path: Path) -> dict[str, Any]:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise ValueError(f"Cannot read {path}: {exc}") from exc

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a JSON object at top level in {path}, "
                f"got {type(data).__name__}"
            )
        return data
