"""Abstract base class for output formatters."""

from __future__ import annotations

import abc

from configdiff.diff_engine.models import DiffResult


class BaseFormatter(abc.ABC):
    """Every output formatter must implement :meth:`format`."""

    format_name: str

    @abc.abstractmethod
    def format(self, result: DiffResult) -> str:
        """Render *result* as a string ready for display or file output."""
