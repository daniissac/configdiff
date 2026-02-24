"""Human-readable text formatter with optional colour."""

from __future__ import annotations

import os
import sys

from configdiff.diff_engine.models import ChangeType, DiffResult
from configdiff.output.base import BaseFormatter

_COLOURS = {
    "green": "\033[32m",
    "red": "\033[31m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "reset": "\033[0m",
    "bold": "\033[1m",
}


def _use_colour() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def _c(name: str) -> str:
    return _COLOURS[name] if _use_colour() else ""


def _repr_value(value: object) -> str:
    if isinstance(value, str):
        return repr(value)
    return str(value)


class TextFormatter(BaseFormatter):
    format_name = "text"

    def format(self, result: DiffResult) -> str:
        if not result.has_changes:
            return f"{_c('green')}No differences found.{_c('reset')}"

        lines: list[str] = []
        summary = result.summary
        header_parts = []
        for change_type, count in sorted(summary.items()):
            header_parts.append(f"{count} {change_type}")
        lines.append(
            f"{_c('bold')}Found {len(result.entries)} change(s): "
            f"{', '.join(header_parts)}{_c('reset')}"
        )
        lines.append("")

        for entry in result.entries:
            path_str = f"{_c('bold')}{entry.path}{_c('reset')}"

            if entry.change_type is ChangeType.ADDED:
                lines.append(
                    f"  {_c('green')}+ {path_str}: "
                    f"{_repr_value(entry.new_value)}{_c('reset')}"
                )
            elif entry.change_type is ChangeType.REMOVED:
                lines.append(
                    f"  {_c('red')}- {path_str}: "
                    f"{_repr_value(entry.old_value)}{_c('reset')}"
                )
            elif entry.change_type is ChangeType.MODIFIED:
                lines.append(
                    f"  {_c('yellow')}~ {path_str}:{_c('reset')}"
                )
                lines.append(
                    f"      {_c('red')}{_repr_value(entry.old_value)}{_c('reset')}"
                    f" {_c('cyan')}\u2192{_c('reset')} "
                    f"{_c('green')}{_repr_value(entry.new_value)}{_c('reset')}"
                )
            elif entry.change_type is ChangeType.TYPE_CHANGED:
                old_type = type(entry.old_value).__name__
                new_type = type(entry.new_value).__name__
                lines.append(
                    f"  {_c('yellow')}! {path_str} "
                    f"(type: {old_type} \u2192 {new_type}):{_c('reset')}"
                )
                lines.append(
                    f"      {_c('red')}{_repr_value(entry.old_value)}{_c('reset')}"
                    f" {_c('cyan')}\u2192{_c('reset')} "
                    f"{_c('green')}{_repr_value(entry.new_value)}{_c('reset')}"
                )

        return "\n".join(lines)
