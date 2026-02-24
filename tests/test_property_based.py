"""Property-based and fuzz tests using Hypothesis.

Validates structural invariants that must hold for any input, not just
hand-crafted examples. Key properties:

1. Comparing X to X always yields zero changes.
2. Changes are always one of the four known types.
3. Every change entry has a non-empty path.
4. Comparing X to Y then Y to X yields symmetric change counts.
5. Output is always valid JSON.
6. Mutation always produces at least one change.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

try:
    from hypothesis import given, settings, assume, HealthCheck
    from hypothesis import strategies as st

    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False

from configdiff.diff_engine import ChangeType, compare
from configdiff.output.json_output import JsonFormatter

pytestmark = pytest.mark.skipif(
    not HAS_HYPOTHESIS, reason="hypothesis not installed"
)

json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10000, max_value=10000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=50),
)

json_values = st.recursive(
    json_primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            children,
            max_size=10,
        ),
    ),
    max_leaves=50,
)

config_dicts = st.dictionaries(
    st.text(min_size=1, max_size=20),
    json_values,
    max_size=15,
)


class TestIdentityProperty:
    """Comparing any config to itself must yield no changes."""

    @given(data=config_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_self_comparison_is_empty(self, data: dict[str, Any]) -> None:
        result = compare(data, data)
        assert not result.has_changes
        assert len(result.entries) == 0


class TestChangeTypeInvariant:
    """Every entry must have a valid ChangeType."""

    @given(before=config_dicts, after=config_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_all_entries_have_valid_type(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> None:
        result = compare(before, after)
        valid_types = set(ChangeType)
        for entry in result.entries:
            assert entry.change_type in valid_types


class TestPathInvariant:
    """Every entry must have a non-empty path (except root-level)."""

    @given(before=config_dicts, after=config_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_all_entries_have_path(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> None:
        result = compare(before, after)
        for entry in result.entries:
            assert isinstance(entry.path, str)
            assert len(entry.path) > 0


class TestSymmetryProperty:
    """Comparing A->B and B->A should yield the same total change count
    (added ↔ removed are symmetric)."""

    @given(before=config_dicts, after=config_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_symmetric_change_count(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> None:
        forward = compare(before, after)
        reverse = compare(after, before)
        assert len(forward.entries) == len(reverse.entries)


class TestOutputValidity:
    """JSON formatter must always produce valid JSON."""

    @given(before=config_dicts, after=config_dicts)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_json_output_always_valid(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> None:
        result = compare(before, after)
        formatter = JsonFormatter()
        output = formatter.format(result)
        data = json.loads(output)
        assert isinstance(data, dict)
        assert "changes" in data
        assert "total_changes" in data
        assert data["total_changes"] == len(data["changes"])


class TestMutationDetection:
    """Mutating a single key must always be detected."""

    @given(data=config_dicts)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_single_key_mutation_detected(
        self, data: dict[str, Any]
    ) -> None:
        assume(len(data) > 0)
        import copy
        modified = copy.deepcopy(data)
        key = next(iter(modified))
        modified[key] = "__MUTATED_SENTINEL__"
        result = compare(data, modified)
        assert result.has_changes

    @given(data=config_dicts)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_key_addition_detected(self, data: dict[str, Any]) -> None:
        import copy
        modified = copy.deepcopy(data)
        modified["__NEW_KEY_SENTINEL__"] = "added"
        result = compare(data, modified)
        assert result.has_changes
        added = [
            e for e in result.entries if e.change_type is ChangeType.ADDED
        ]
        assert len(added) >= 1

    @given(data=config_dicts)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_key_removal_detected(self, data: dict[str, Any]) -> None:
        assume(len(data) > 0)
        import copy
        modified = copy.deepcopy(data)
        key = next(iter(modified))
        del modified[key]
        result = compare(data, modified)
        assert result.has_changes
        removed = [
            e for e in result.entries if e.change_type is ChangeType.REMOVED
        ]
        assert len(removed) >= 1


class TestSummaryConsistency:
    """Summary counts must match actual entry counts by type."""

    @given(before=config_dicts, after=config_dicts)
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_summary_matches_entries(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> None:
        result = compare(before, after)
        summary = result.summary
        for ct in ChangeType:
            expected = len([
                e for e in result.entries if e.change_type is ct
            ])
            actual = summary.get(ct.value, 0)
            assert actual == expected, (
                f"Summary mismatch for {ct.value}: {actual} != {expected}"
            )
