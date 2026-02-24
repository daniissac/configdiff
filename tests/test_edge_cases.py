"""Edge-case and boundary-condition tests.

Covers: empty files, null values, type changes, special characters,
malformed input, encoding, large files, and mixed data types.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from configdiff.cli.app import EXIT_CHANGES, EXIT_ERROR, EXIT_NO_CHANGES, run
from configdiff.diff_engine import ChangeType, compare

DATASETS = Path(__file__).parent / "datasets"


class TestEmptyConfigs:
    def test_both_empty_dicts(self) -> None:
        result = compare({}, {})
        assert not result.has_changes
        assert result.summary == {}

    def test_empty_before(self) -> None:
        result = compare({}, {"a": 1, "b": "two"})
        assert result.has_changes
        assert all(e.change_type is ChangeType.ADDED for e in result.entries)
        assert len(result.entries) == 2

    def test_empty_after(self) -> None:
        result = compare({"a": 1, "b": "two"}, {})
        assert result.has_changes
        assert all(e.change_type is ChangeType.REMOVED for e in result.entries)

    def test_empty_json_files(self) -> None:
        empty = DATASETS / "edge_cases" / "empty.json"
        code = run([str(empty), str(empty)])
        assert code == EXIT_NO_CHANGES

    def test_empty_yaml_files(self) -> None:
        empty = DATASETS / "edge_cases" / "empty.yaml"
        code = run([str(empty), str(empty)])
        assert code == EXIT_NO_CHANGES

    def test_empty_nested_dicts(self) -> None:
        result = compare({"a": {}}, {"a": {}})
        assert not result.has_changes

    def test_empty_lists(self) -> None:
        result = compare({"a": []}, {"a": []})
        assert not result.has_changes

    def test_empty_to_populated(self) -> None:
        result = compare({"a": {}}, {"a": {"b": 1}})
        assert result.has_changes
        assert result.entries[0].change_type is ChangeType.ADDED


class TestNullValues:
    def test_null_to_value(self) -> None:
        result = compare({"x": None}, {"x": "set"})
        assert result.has_changes
        entry = result.entries[0]
        assert entry.old_value is None
        assert entry.new_value == "set"

    def test_value_to_null(self) -> None:
        result = compare({"x": "set"}, {"x": None})
        assert result.has_changes
        entry = result.entries[0]
        assert entry.old_value == "set"
        assert entry.new_value is None

    def test_null_to_null(self) -> None:
        result = compare({"x": None}, {"x": None})
        assert not result.has_changes

    def test_null_in_list(self) -> None:
        result = compare(
            {"a": [None, 1, None]},
            {"a": [None, 1, "replaced"]},
        )
        assert result.has_changes
        assert len(result.entries) == 1
        assert result.entries[0].path == "a[2]"

    def test_null_files_diff(self) -> None:
        before = DATASETS / "edge_cases" / "nulls.json"
        after = DATASETS / "edge_cases" / "nulls_modified.json"
        code = run([str(before), str(after)])
        assert code == EXIT_CHANGES


class TestTypeChanges:
    @pytest.mark.parametrize(
        "before_val,after_val,expected_type",
        [
            ("42", 42, ChangeType.TYPE_CHANGED),
            (42, "42", ChangeType.TYPE_CHANGED),
            (True, "true", ChangeType.TYPE_CHANGED),
            ("true", True, ChangeType.TYPE_CHANGED),
            (None, "set", ChangeType.TYPE_CHANGED),
            ([1, 2], "flat", ChangeType.TYPE_CHANGED),
            ({"a": 1}, "flat", ChangeType.TYPE_CHANGED),
            ({"a": 1}, [1, 2], ChangeType.TYPE_CHANGED),
        ],
        ids=[
            "str->int", "int->str", "bool->str", "str->bool",
            "null->str", "list->str", "dict->str", "dict->list",
        ],
    )
    def test_type_change_detected(
        self, before_val, after_val, expected_type
    ) -> None:
        result = compare({"x": before_val}, {"x": after_val})
        assert result.has_changes
        assert result.entries[0].change_type is expected_type

    def test_int_float_equivalence(self) -> None:
        """Python considers 10 == 10.0 but type() differs."""
        result = compare({"x": 10}, {"x": 10.0})
        assert result.has_changes
        assert result.entries[0].change_type is ChangeType.TYPE_CHANGED

    def test_type_changes_file(self) -> None:
        before = DATASETS / "edge_cases" / "mixed_types.json"
        after = DATASETS / "edge_cases" / "mixed_types_changed.json"
        code = run([str(before), str(after)])
        assert code == EXIT_CHANGES


class TestMalformedInput:
    def test_malformed_json_returns_error(self) -> None:
        bad = DATASETS / "edge_cases" / "malformed.json"
        good = DATASETS / "edge_cases" / "empty.json"
        code = run([str(bad), str(good)])
        assert code == EXIT_ERROR

    def test_malformed_yaml_returns_error(self) -> None:
        bad = DATASETS / "edge_cases" / "malformed.yaml"
        good = DATASETS / "edge_cases" / "empty.yaml"
        code = run([str(bad), str(good)])
        assert code == EXIT_ERROR

    def test_nonexistent_file_returns_error(self, tmp_path: Path) -> None:
        fake = tmp_path / "does_not_exist.json"
        real = tmp_path / "real.json"
        real.write_text("{}", encoding="utf-8")
        code = run([str(fake), str(real)])
        assert code == EXIT_ERROR

    def test_format_mismatch_returns_error(self, tmp_path: Path) -> None:
        j = tmp_path / "a.json"
        y = tmp_path / "b.yaml"
        j.write_text("{}", encoding="utf-8")
        y.write_text("{}\n", encoding="utf-8")
        code = run([str(j), str(y)])
        assert code == EXIT_ERROR

    def test_unknown_extension_returns_error(self, tmp_path: Path) -> None:
        a = tmp_path / "a.xyz"
        b = tmp_path / "b.xyz"
        a.write_text("{}", encoding="utf-8")
        b.write_text("{}", encoding="utf-8")
        code = run([str(a), str(b)])
        assert code == EXIT_ERROR


class TestSpecialCharacters:
    def test_unicode_values(self) -> None:
        result = compare(
            {"name": "café résumé"},
            {"name": "café résumé updated"},
        )
        assert result.has_changes
        assert result.entries[0].new_value == "café résumé updated"

    def test_emoji_values(self) -> None:
        result = compare(
            {"status": "✅ deployed"},
            {"status": "❌ failed"},
        )
        assert result.has_changes

    def test_keys_with_dots(self) -> None:
        result = compare(
            {"a.b.c": "old"},
            {"a.b.c": "new"},
        )
        assert result.has_changes

    def test_special_chars_file(self) -> None:
        before = DATASETS / "edge_cases" / "special_chars.yaml"
        after = DATASETS / "edge_cases" / "special_chars_modified.yaml"
        code = run([str(before), str(after)])
        assert code == EXIT_CHANGES


class TestLargeFiles:
    def test_large_config_runs(self) -> None:
        before = DATASETS / "large" / "before.json"
        after = DATASETS / "large" / "after.json"
        code = run([str(before), str(after)])
        assert code == EXIT_CHANGES

    def test_large_config_detects_changes(self) -> None:
        before = json.loads(
            (DATASETS / "large" / "before.json").read_text(encoding="utf-8")
        )
        after = json.loads(
            (DATASETS / "large" / "after.json").read_text(encoding="utf-8")
        )
        result = compare(before, after)
        assert result.has_changes
        assert len(result.entries) > 50


class TestListEdgeCases:
    def test_empty_list_to_populated(self) -> None:
        result = compare({"a": []}, {"a": [1, 2, 3]})
        assert result.has_changes
        assert len(result.entries) == 3

    def test_populated_to_empty(self) -> None:
        result = compare({"a": [1, 2, 3]}, {"a": []})
        assert result.has_changes
        assert len(result.entries) == 3
        assert all(e.change_type is ChangeType.REMOVED for e in result.entries)

    def test_nested_list_of_dicts(self) -> None:
        result = compare(
            {"items": [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]},
            {"items": [{"id": 1, "val": "a"}, {"id": 2, "val": "changed"}]},
        )
        assert result.has_changes
        assert len(result.entries) == 1
        assert "items[1].val" == result.entries[0].path

    def test_deeply_nested_list(self) -> None:
        before = {"a": {"b": {"c": [1, [2, [3, [4]]]]}}}
        after = {"a": {"b": {"c": [1, [2, [3, [999]]]]}}}
        result = compare(before, after)
        assert result.has_changes
        assert len(result.entries) == 1
