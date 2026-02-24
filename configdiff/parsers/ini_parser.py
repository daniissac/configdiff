"""Parser for INI configuration files."""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any

from configdiff.parsers.base import BaseParser


class IniParser(BaseParser):
    format_name = "ini"
    extensions = [".ini", ".cfg", ".conf"]

    def parse(self, path: Path) -> dict[str, Any]:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise ValueError(f"Cannot read {path}: {exc}") from exc

        cp = configparser.ConfigParser()
        try:
            cp.read_string(text, source=str(path))
        except configparser.Error as exc:
            raise ValueError(f"Invalid INI in {path}: {exc}") from exc

        result: dict[str, Any] = {}
        for section in cp.sections():
            result[section] = dict(cp[section])
        if cp.defaults():
            result["DEFAULT"] = dict(cp.defaults())
        return result
