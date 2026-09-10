"""Diff engine — structure-aware recursive comparison."""

from configdiff.diff_engine.engine import compare
from configdiff.diff_engine.models import ChangeType, DiffEntry, DiffResult

__all__ = ["ChangeType", "DiffEntry", "DiffResult", "compare"]
