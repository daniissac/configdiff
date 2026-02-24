"""Abstract base class for configuration file parsers."""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Any


class BaseParser(abc.ABC):
    """Base class that every config format parser must implement.

    Subclasses declare ``format_name`` (e.g. ``"json"``) and
    ``extensions`` (e.g. ``[".json"]``), then implement :meth:`parse`.
    """

    format_name: str
    extensions: list[str]

    @abc.abstractmethod
    def parse(self, path: Path) -> dict[str, Any]:
        """Read *path* and return a normalised Python dict.

        Raises
        ------
        FileNotFoundError
            If *path* does not exist.
        ValueError
            If the file cannot be parsed.
        """

    def __repr__(self) -> str:
        return f"<{type(self).__name__} format={self.format_name!r}>"
