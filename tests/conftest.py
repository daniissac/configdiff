"""Shared pytest fixtures for ConfigDiff validation suite."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
DATASETS_DIR = Path(__file__).parent / "datasets"
GOLDEN_DIR = Path(__file__).parent / "golden"


@pytest.fixture()
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture()
def datasets_dir() -> Path:
    return DATASETS_DIR


@pytest.fixture()
def golden_dir() -> Path:
    return GOLDEN_DIR


@pytest.fixture()
def tmp_json(tmp_path: Path) -> tuple[Path, Path]:
    """Create a before/after JSON pair and return their paths."""
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(
        '{"a": 1, "b": {"c": 2}, "d": [1, 2, 3]}', encoding="utf-8"
    )
    after.write_text(
        '{"a": 1, "b": {"c": 99}, "d": [1, 2, 3], "e": "new"}',
        encoding="utf-8",
    )
    return before, after


@pytest.fixture()
def tmp_yaml(tmp_path: Path) -> tuple[Path, Path]:
    """Create a before/after YAML pair."""
    before = tmp_path / "before.yaml"
    after = tmp_path / "after.yaml"
    before.write_text("a: 1\nb:\n  c: 2\n", encoding="utf-8")
    after.write_text("a: 1\nb:\n  c: 99\ne: new\n", encoding="utf-8")
    return before, after


@pytest.fixture()
def tmp_toml(tmp_path: Path) -> tuple[Path, Path]:
    """Create a before/after TOML pair."""
    before = tmp_path / "before.toml"
    after = tmp_path / "after.toml"
    before.write_text('[section]\nkey = "old"\n', encoding="utf-8")
    after.write_text('[section]\nkey = "new"\nextra = true\n', encoding="utf-8")
    return before, after


@pytest.fixture()
def tmp_ini(tmp_path: Path) -> tuple[Path, Path]:
    """Create a before/after INI pair."""
    before = tmp_path / "before.ini"
    after = tmp_path / "after.ini"
    before.write_text(
        "[section]\nkey = old\nremoved = yes\n", encoding="utf-8"
    )
    after.write_text("[section]\nkey = new\nadded = yes\n", encoding="utf-8")
    return before, after


def write_json_pair(
    tmp_path: Path,
    before_data: dict[str, Any],
    after_data: dict[str, Any],
) -> tuple[Path, Path]:
    """Helper to write before/after JSON files from dicts."""
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps(before_data), encoding="utf-8")
    after.write_text(json.dumps(after_data), encoding="utf-8")
    return before, after


class PerfTimer:
    """Context manager to measure execution time."""

    def __init__(self) -> None:
        self.elapsed: float = 0.0

    def __enter__(self) -> PerfTimer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self.elapsed = time.perf_counter() - self._start
