"""Determinism validation tests.

Ensures ConfigDiff produces identical output across multiple runs for the
same input. Non-determinism would be a critical bug for CI/CD usage.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from configdiff.cli.app import run
from configdiff.diff_engine import compare
from configdiff.output.json_output import JsonFormatter

DATASETS = Path(__file__).parent / "datasets"


class TestEngineDeterminism:
    """Run compare() multiple times and assert identical results."""

    @pytest.mark.parametrize("iteration", range(10))
    def test_scalar_diff_is_stable(self, iteration: int) -> None:
        result = compare(
            {"a": 1, "b": "old", "c": True},
            {"a": 2, "b": "new", "d": False},
        )
        entries = [(e.path, e.change_type.value, e.old_value, e.new_value)
                   for e in result.entries]
        expected = [
            ("a", "modified", 1, 2),
            ("b", "modified", "old", "new"),
            ("c", "removed", True, None),
            ("d", "added", None, False),
        ]
        assert entries == expected

    @pytest.mark.parametrize("iteration", range(10))
    def test_nested_diff_is_stable(self, iteration: int) -> None:
        before = {
            "level1": {
                "level2": {"a": 1, "b": 2},
                "items": [1, 2, 3],
            }
        }
        after = {
            "level1": {
                "level2": {"a": 1, "b": 99, "c": "new"},
                "items": [1, 2],
            }
        }
        result = compare(before, after)
        paths = [e.path for e in result.entries]
        assert paths == sorted(paths) or paths == [
            "level1.items[2]",
            "level1.level2.b",
            "level1.level2.c",
        ]

    @pytest.mark.parametrize("iteration", range(5))
    def test_large_diff_is_stable(self, iteration: int) -> None:
        before_data = json.loads(
            (DATASETS / "large" / "before.json").read_text(encoding="utf-8")
        )
        after_data = json.loads(
            (DATASETS / "large" / "after.json").read_text(encoding="utf-8")
        )
        result = compare(before_data, after_data)
        output = JsonFormatter().format(result)
        data = json.loads(output)
        change_count = data["total_changes"]
        assert change_count > 50
        if iteration == 0:
            TestEngineDeterminism._large_baseline = output
        else:
            assert output == TestEngineDeterminism._large_baseline

    _large_baseline: str = ""


class TestCLIDeterminism:
    """Run CLI multiple times and verify identical stdout."""

    @pytest.mark.parametrize("iteration", range(5))
    def test_cli_json_output_stable(
        self,
        iteration: int,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        before = DATASETS / "kubernetes" / "before.yaml"
        after = DATASETS / "kubernetes" / "after.yaml"
        run([str(before), str(after), "--format", "json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        if iteration == 0:
            TestCLIDeterminism._k8s_baseline = data
        else:
            assert data == TestCLIDeterminism._k8s_baseline

    _k8s_baseline: dict = {}


class TestOutputDeterminism:
    """Verify that all three formatters are deterministic."""

    def test_all_formatters_deterministic(self) -> None:
        from configdiff.output import get_formatter

        before = {"a": 1, "b": [1, 2], "c": {"d": "x"}}
        after = {"a": 2, "b": [1, 3], "c": {"d": "y"}, "e": True}
        result = compare(before, after)

        for fmt_name in ("text", "json", "yaml"):
            formatter = get_formatter(fmt_name)
            outputs = [formatter.format(result) for _ in range(10)]
            assert len(set(outputs)) == 1, (
                f"Non-deterministic output for {fmt_name} formatter"
            )
