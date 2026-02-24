"""Recursive structure-aware diff engine."""

from __future__ import annotations

import logging
from typing import Any

from configdiff.diff_engine.models import ChangeType, DiffEntry, DiffResult

logger = logging.getLogger(__name__)


def _sort_key(item: Any) -> Any:
    """Produce a sortable key for heterogeneous lists."""
    try:
        return (0, str(item))
    except Exception:
        return (1, id(item))


def _deep_diff(
    before: Any,
    after: Any,
    path: str,
    *,
    ignore_order: bool,
) -> list[DiffEntry]:
    """Recursively compare *before* and *after*, returning diff entries."""

    if type(before) is not type(after):
        return [
            DiffEntry(
                path=path,
                change_type=ChangeType.TYPE_CHANGED,
                old_value=before,
                new_value=after,
            )
        ]

    if isinstance(before, dict):
        return _diff_dicts(before, after, path, ignore_order=ignore_order)

    if isinstance(before, list):
        return _diff_lists(before, after, path, ignore_order=ignore_order)

    if before != after:
        return [
            DiffEntry(
                path=path,
                change_type=ChangeType.MODIFIED,
                old_value=before,
                new_value=after,
            )
        ]

    return []


def _diff_dicts(
    before: dict[str, Any],
    after: dict[str, Any],
    path: str,
    *,
    ignore_order: bool,
) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    all_keys = set(before) | set(after)

    for key in sorted(all_keys):
        child_path = f"{path}.{key}" if path else key

        if key not in before:
            entries.append(
                DiffEntry(
                    path=child_path,
                    change_type=ChangeType.ADDED,
                    new_value=after[key],
                )
            )
        elif key not in after:
            entries.append(
                DiffEntry(
                    path=child_path,
                    change_type=ChangeType.REMOVED,
                    old_value=before[key],
                )
            )
        else:
            entries.extend(
                _deep_diff(
                    before[key],
                    after[key],
                    child_path,
                    ignore_order=ignore_order,
                )
            )

    return entries


def _diff_lists(
    before: list[Any],
    after: list[Any],
    path: str,
    *,
    ignore_order: bool,
) -> list[DiffEntry]:
    if ignore_order:
        before = sorted(before, key=_sort_key)
        after = sorted(after, key=_sort_key)

    entries: list[DiffEntry] = []
    max_len = max(len(before), len(after))

    for i in range(max_len):
        child_path = f"{path}[{i}]"

        if i >= len(before):
            entries.append(
                DiffEntry(
                    path=child_path,
                    change_type=ChangeType.ADDED,
                    new_value=after[i],
                )
            )
        elif i >= len(after):
            entries.append(
                DiffEntry(
                    path=child_path,
                    change_type=ChangeType.REMOVED,
                    old_value=before[i],
                )
            )
        else:
            entries.extend(
                _deep_diff(
                    before[i],
                    after[i],
                    child_path,
                    ignore_order=ignore_order,
                )
            )

    return entries


def compare(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    ignore_order: bool = False,
    metadata: dict[str, Any] | None = None,
) -> DiffResult:
    """Public API: compare two parsed config dicts and return a :class:`DiffResult`."""
    logger.debug("Starting diff (ignore_order=%s)", ignore_order)
    entries = _deep_diff(before, after, path="", ignore_order=ignore_order)
    return DiffResult(entries=entries, metadata=metadata or {})
