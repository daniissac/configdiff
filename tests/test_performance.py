"""Performance and scalability tests.

Measures runtime and validates that ConfigDiff scales reasonably with
input size. Uses wall-clock timing — not micro-benchmarks — to detect
regressions and establish baseline expectations.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

from configdiff.diff_engine import compare
from configdiff.output.json_output import JsonFormatter

DATASETS = Path(__file__).parent / "datasets"


def _generate_config(n_keys: int, depth: int = 0) -> dict:
    """Generate a config dict of given breadth and depth."""
    d: dict = {}
    for i in range(n_keys):
        if depth > 0:
            d[f"key_{i}"] = _generate_config(max(1, n_keys // 5), depth - 1)
        else:
            d[f"key_{i}"] = f"value_{i}"
    return d


class TestSmallConfigPerformance:
    def test_small_diff_under_10ms(self) -> None:
        before = {"a": 1, "b": "old", "c": [1, 2, 3]}
        after = {"a": 2, "b": "new", "c": [1, 2, 4], "d": True}
        start = time.perf_counter()
        for _ in range(100):
            compare(before, after)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 10, f"Small diff averaged {avg_ms:.2f}ms (limit: 10ms)"

    def test_small_format_under_10ms(self) -> None:
        result = compare({"a": 1}, {"a": 2, "b": "new"})
        formatter = JsonFormatter()
        start = time.perf_counter()
        for _ in range(100):
            formatter.format(result)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 100) * 1000
        assert avg_ms < 10, f"Small format averaged {avg_ms:.2f}ms (limit: 10ms)"


class TestLargeConfigPerformance:
    def test_large_diff_under_500ms(self) -> None:
        before = json.loads(
            (DATASETS / "large" / "before.json").read_text(encoding="utf-8")
        )
        after = json.loads(
            (DATASETS / "large" / "after.json").read_text(encoding="utf-8")
        )
        start = time.perf_counter()
        result = compare(before, after)
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 500, f"Large diff took {elapsed:.1f}ms (limit: 500ms)"
        assert result.has_changes

    def test_large_format_under_200ms(self) -> None:
        before = json.loads(
            (DATASETS / "large" / "before.json").read_text(encoding="utf-8")
        )
        after = json.loads(
            (DATASETS / "large" / "after.json").read_text(encoding="utf-8")
        )
        result = compare(before, after)
        formatter = JsonFormatter()
        start = time.perf_counter()
        formatter.format(result)
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 200, f"Large format took {elapsed:.1f}ms (limit: 200ms)"


class TestScalability:
    """Verify roughly linear scaling as config size increases."""

    @pytest.mark.parametrize(
        "n_keys", [10, 50, 100, 500, 1000],
        ids=["10k", "50k", "100k", "500k", "1000k"],
    )
    def test_flat_scaling(self, n_keys: int) -> None:
        before = {f"k{i}": f"v{i}" for i in range(n_keys)}
        after = {f"k{i}": f"v{i}" if i % 2 == 0 else f"changed{i}"
                 for i in range(n_keys)}
        start = time.perf_counter()
        result = compare(before, after)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert result.has_changes
        assert elapsed_ms < max(100, n_keys * 0.5), (
            f"{n_keys} keys took {elapsed_ms:.1f}ms"
        )

    @pytest.mark.parametrize(
        "depth", [2, 4, 6, 8],
        ids=["depth2", "depth4", "depth6", "depth8"],
    )
    def test_nested_scaling(self, depth: int) -> None:
        before = _generate_config(5, depth)
        after = _generate_config(5, depth)
        after["key_0"] = "mutated"
        start = time.perf_counter()
        result = compare(before, after)
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert result.has_changes
        assert elapsed_ms < 500, f"Depth {depth} took {elapsed_ms:.1f}ms"


class TestMemoryBounds:
    """Rough check that output size is proportional to change count."""

    def test_output_size_proportional(self) -> None:
        sizes = []
        for n in [10, 50, 200]:
            before = {f"k{i}": f"v{i}" for i in range(n)}
            after = {f"k{i}": f"changed{i}" for i in range(n)}
            result = compare(before, after)
            output = JsonFormatter().format(result)
            sizes.append((n, len(output)))

        for i in range(1, len(sizes)):
            ratio = sizes[i][1] / sizes[i - 1][1]
            key_ratio = sizes[i][0] / sizes[i - 1][0]
            assert ratio < key_ratio * 2, (
                f"Output size grew disproportionately: "
                f"{sizes[i - 1]} -> {sizes[i]}"
            )
