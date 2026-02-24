"""Tests for output formatters."""

from __future__ import annotations

import json
import os

import yaml

from configdiff.diff_engine import ChangeType, DiffEntry, DiffResult, compare
from configdiff.output import get_formatter
from configdiff.output.json_output import JsonFormatter
from configdiff.output.text import TextFormatter
from configdiff.output.yaml_output import YamlFormatter


def _sample_result() -> DiffResult:
    return compare(
        {"a": 1, "b": {"c": 2}, "removed": True},
        {"a": 99, "b": {"c": 2}, "added": "new"},
    )


class TestTextFormatter:
    def test_no_changes(self) -> None:
        os.environ["NO_COLOR"] = "1"
        try:
            result = compare({"a": 1}, {"a": 1})
            output = TextFormatter().format(result)
            assert "No differences" in output
        finally:
            del os.environ["NO_COLOR"]

    def test_has_changes(self) -> None:
        os.environ["NO_COLOR"] = "1"
        try:
            output = TextFormatter().format(_sample_result())
            assert "change(s)" in output
            assert "a" in output
        finally:
            del os.environ["NO_COLOR"]

    def test_type_changed(self) -> None:
        os.environ["NO_COLOR"] = "1"
        try:
            result = compare({"a": "1"}, {"a": 1})
            output = TextFormatter().format(result)
            assert "type:" in output
        finally:
            del os.environ["NO_COLOR"]


class TestJsonFormatter:
    def test_valid_json(self) -> None:
        output = JsonFormatter().format(_sample_result())
        data = json.loads(output)
        assert "changes" in data
        assert "summary" in data
        assert "total_changes" in data
        assert data["total_changes"] == len(data["changes"])

    def test_no_changes_json(self) -> None:
        result = compare({"x": 1}, {"x": 1})
        data = json.loads(JsonFormatter().format(result))
        assert data["total_changes"] == 0
        assert data["changes"] == []

    def test_metadata_included(self) -> None:
        result = compare({"a": 1}, {"a": 2}, metadata={"file": "test"})
        data = json.loads(JsonFormatter().format(result))
        assert data["metadata"]["file"] == "test"


class TestYamlFormatter:
    def test_valid_yaml(self) -> None:
        output = YamlFormatter().format(_sample_result())
        data = yaml.safe_load(output)
        assert "changes" in data
        assert "summary" in data

    def test_no_changes_yaml(self) -> None:
        result = compare({"x": 1}, {"x": 1})
        data = yaml.safe_load(YamlFormatter().format(result))
        assert data["total_changes"] == 0


class TestGetFormatter:
    def test_text(self) -> None:
        assert isinstance(get_formatter("text"), TextFormatter)

    def test_json(self) -> None:
        assert isinstance(get_formatter("json"), JsonFormatter)

    def test_yaml(self) -> None:
        assert isinstance(get_formatter("yaml"), YamlFormatter)

    def test_unknown_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="Unknown output format"):
            get_formatter("xml")
