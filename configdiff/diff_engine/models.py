"""Data models for the diff engine."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class ChangeType(enum.Enum):
    """Classification of a single configuration change."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    TYPE_CHANGED = "type_changed"


@dataclass(frozen=True, slots=True)
class DiffEntry:
    """One atomic change between two configs."""

    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict for JSON / YAML output."""
        result: dict[str, Any] = {
            "path": self.path,
            "type": self.change_type.value,
        }
        if self.change_type in (
            ChangeType.REMOVED,
            ChangeType.MODIFIED,
            ChangeType.TYPE_CHANGED,
        ):
            result["old"] = self.old_value
        if self.change_type in (
            ChangeType.ADDED,
            ChangeType.MODIFIED,
            ChangeType.TYPE_CHANGED,
        ):
            result["new"] = self.new_value
        return result


@dataclass(slots=True)
class DiffResult:
    """Aggregated diff output returned by the engine."""

    entries: list[DiffEntry] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return len(self.entries) > 0

    @property
    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.entries:
            key = entry.change_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts
