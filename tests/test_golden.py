"""Golden file comparison tests.

Compares ConfigDiff output against pre-recorded expected outputs. If golden
files need updating after intentional changes, run:

    pytest tests/test_golden.py --update-golden
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from configdiff.diff_engine import compare
from configdiff.output.json_output import JsonFormatter
from configdiff.parsers.json_parser import JsonParser
from configdiff.parsers.yaml_parser import YamlParser

GOLDEN_DIR = Path(__file__).parent / "golden"
DATASETS = Path(__file__).parent / "datasets"


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regenerate golden files instead of comparing.",
    )


def _compare_or_update(
    golden_path: Path,
    actual_output: str,
    request: pytest.FixtureRequest,
) -> None:
    """Compare against golden file, or update if --update-golden is set."""
    if request.config.getoption("--update-golden", default=False):
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(actual_output + "\n", encoding="utf-8")
        pytest.skip(f"Updated golden file: {golden_path.name}")
        return

    assert golden_path.exists(), (
        f"Golden file missing: {golden_path}. "
        f"Run with --update-golden to create it."
    )
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    actual = json.loads(actual_output)
    assert actual == expected, (
        f"Output does not match golden file {golden_path.name}"
    )


class TestGoldenSmallDiff:
    def test_small_json_diff(self, request: pytest.FixtureRequest) -> None:
        result = compare(
            {"app_name": "myservice", "version": "1.2.3", "debug": False,
             "port": 8080, "log_level": "info"},
            {"app_name": "myservice", "version": "1.3.0", "debug": True,
             "port": 9090, "log_level": "debug", "new_feature": True},
        )
        output = JsonFormatter().format(result)
        _compare_or_update(GOLDEN_DIR / "small_json_diff.json", output, request)


class TestGoldenEmpty:
    def test_empty_no_changes(self, request: pytest.FixtureRequest) -> None:
        result = compare({}, {})
        output = JsonFormatter().format(result)
        _compare_or_update(
            GOLDEN_DIR / "empty_no_changes.json", output, request
        )


class TestGoldenNulls:
    def test_null_handling(self, request: pytest.FixtureRequest) -> None:
        result = compare(
            {"value": None, "nested": {"a": None, "b": "present"},
             "list_with_nulls": [None, 1, None, "text"]},
            {"value": "now_set", "nested": {"a": 42, "b": None},
             "list_with_nulls": [None, 1, "replaced", "text"]},
        )
        output = JsonFormatter().format(result)
        _compare_or_update(
            GOLDEN_DIR / "null_handling.json", output, request
        )


class TestGoldenTypeChanges:
    def test_type_changes(self, request: pytest.FixtureRequest) -> None:
        result = compare(
            {"string_to_int": "42", "int_to_string": 42,
             "bool_to_string": True, "string_to_bool": "true",
             "int_to_float": 10, "null_to_string": None,
             "list_to_string": [1, 2, 3],
             "dict_to_string": {"nested": "value"}},
            {"string_to_int": 42, "int_to_string": "42",
             "bool_to_string": "true", "string_to_bool": True,
             "int_to_float": 10.0, "null_to_string": "now_set",
             "list_to_string": "serialized",
             "dict_to_string": "flattened"},
        )
        output = JsonFormatter().format(result)
        _compare_or_update(
            GOLDEN_DIR / "type_changes.json", output, request
        )


class TestGoldenKubernetes:
    def test_kubernetes_deployment(
        self, request: pytest.FixtureRequest
    ) -> None:
        before = YamlParser().parse(DATASETS / "kubernetes" / "before.yaml")
        after = YamlParser().parse(DATASETS / "kubernetes" / "after.yaml")
        result = compare(before, after)
        output = JsonFormatter().format(result)
        _compare_or_update(
            GOLDEN_DIR / "kubernetes_deployment.json", output, request
        )
