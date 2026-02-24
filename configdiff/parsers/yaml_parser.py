"""Parser for YAML configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from configdiff.parsers.base import BaseParser


class YamlParser(BaseParser):
    format_name = "yaml"
    extensions = [".yaml", ".yml"]

    def parse(self, path: Path) -> dict[str, Any]:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise ValueError(f"Cannot read {path}: {exc}") from exc

        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

        if data is None:
            return {}

        if not isinstance(data, dict):
            raise ValueError(
                f"Expected a YAML mapping at top level in {path}, "
                f"got {type(data).__name__}"
            )
        return data
