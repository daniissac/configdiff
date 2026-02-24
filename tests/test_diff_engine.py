"""Tests for the diff engine."""

from __future__ import annotations

from configdiff.diff_engine import ChangeType, DiffResult, compare


class TestScalarChanges:
    def test_no_changes(self) -> None:
        result = compare({"a": 1}, {"a": 1})
        assert not result.has_changes

    def test_modified_value(self) -> None:
        result = compare({"a": 1}, {"a": 2})
        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.path == "a"
        assert entry.change_type is ChangeType.MODIFIED
        assert entry.old_value == 1
        assert entry.new_value == 2

    def test_added_key(self) -> None:
        result = compare({"a": 1}, {"a": 1, "b": 2})
        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.path == "b"
        assert entry.change_type is ChangeType.ADDED
        assert entry.new_value == 2

    def test_removed_key(self) -> None:
        result = compare({"a": 1, "b": 2}, {"a": 1})
        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.path == "b"
        assert entry.change_type is ChangeType.REMOVED
        assert entry.old_value == 2

    def test_type_changed(self) -> None:
        result = compare({"a": "1"}, {"a": 1})
        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry.path == "a"
        assert entry.change_type is ChangeType.TYPE_CHANGED
        assert entry.old_value == "1"
        assert entry.new_value == 1


class TestNestedChanges:
    def test_nested_modified(self) -> None:
        before = {"top": {"mid": {"deep": "old"}}}
        after = {"top": {"mid": {"deep": "new"}}}
        result = compare(before, after)
        assert result.entries[0].path == "top.mid.deep"
        assert result.entries[0].change_type is ChangeType.MODIFIED

    def test_nested_added(self) -> None:
        before = {"top": {"a": 1}}
        after = {"top": {"a": 1, "b": 2}}
        result = compare(before, after)
        assert result.entries[0].path == "top.b"
        assert result.entries[0].change_type is ChangeType.ADDED

    def test_nested_removed(self) -> None:
        before = {"top": {"a": 1, "b": 2}}
        after = {"top": {"a": 1}}
        result = compare(before, after)
        assert result.entries[0].path == "top.b"
        assert result.entries[0].change_type is ChangeType.REMOVED


class TestListChanges:
    def test_list_element_modified(self) -> None:
        result = compare({"a": [1, 2, 3]}, {"a": [1, 99, 3]})
        assert len(result.entries) == 1
        assert result.entries[0].path == "a[1]"
        assert result.entries[0].change_type is ChangeType.MODIFIED

    def test_list_element_added(self) -> None:
        result = compare({"a": [1, 2]}, {"a": [1, 2, 3]})
        assert len(result.entries) == 1
        assert result.entries[0].path == "a[2]"
        assert result.entries[0].change_type is ChangeType.ADDED

    def test_list_element_removed(self) -> None:
        result = compare({"a": [1, 2, 3]}, {"a": [1, 2]})
        assert len(result.entries) == 1
        assert result.entries[0].path == "a[2]"
        assert result.entries[0].change_type is ChangeType.REMOVED

    def test_ignore_order(self) -> None:
        result = compare(
            {"a": [3, 1, 2]},
            {"a": [2, 3, 1]},
            ignore_order=True,
        )
        assert not result.has_changes

    def test_ignore_order_detects_real_diff(self) -> None:
        result = compare(
            {"a": [1, 2, 3]},
            {"a": [1, 2, 4]},
            ignore_order=True,
        )
        assert result.has_changes


class TestEdgeCases:
    def test_both_empty(self) -> None:
        assert not compare({}, {}).has_changes

    def test_before_empty(self) -> None:
        result = compare({}, {"a": 1})
        assert len(result.entries) == 1
        assert result.entries[0].change_type is ChangeType.ADDED

    def test_after_empty(self) -> None:
        result = compare({"a": 1}, {})
        assert len(result.entries) == 1
        assert result.entries[0].change_type is ChangeType.REMOVED

    def test_dict_to_scalar_type_change(self) -> None:
        result = compare({"a": {"nested": 1}}, {"a": "flat"})
        assert result.entries[0].change_type is ChangeType.TYPE_CHANGED


class TestDiffResult:
    def test_summary(self) -> None:
        result = compare(
            {"a": 1, "b": 2, "c": 3},
            {"a": 99, "c": 3, "d": 4},
        )
        summary = result.summary
        assert summary["modified"] == 1
        assert summary["removed"] == 1
        assert summary["added"] == 1

    def test_metadata(self) -> None:
        result = compare({"a": 1}, {"a": 2}, metadata={"file": "test"})
        assert result.metadata["file"] == "test"

    def test_to_dict(self) -> None:
        result = compare({"a": 1}, {"a": 2})
        d = result.entries[0].to_dict()
        assert d["path"] == "a"
        assert d["type"] == "modified"
        assert d["old"] == 1
        assert d["new"] == 2
