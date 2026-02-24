"""Central registry that maps format names / file extensions to parsers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from configdiff.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """Singleton-style registry for config parsers.

    Parsers are looked up by format name (``"json"``) or file extension
    (``".json"``).  The built-in parsers are registered automatically when
    the ``configdiff.parsers`` package is first imported.
    """

    _parsers: dict[str, BaseParser] = {}

    @classmethod
    def register(cls, parser: BaseParser) -> None:
        """Register *parser* for its declared format name and extensions."""
        cls._parsers[parser.format_name] = parser
        for ext in parser.extensions:
            cls._parsers[ext] = parser
        logger.debug("Registered parser: %s", parser)

    @classmethod
    def get_parser(cls, key: str) -> BaseParser:
        """Return the parser matching *key* (format name or extension).

        Raises
        ------
        ValueError
            If no parser is registered for *key*.
        """
        try:
            return cls._parsers[key]
        except KeyError:
            supported = sorted(
                {p.format_name for p in cls._parsers.values()}
            )
            raise ValueError(
                f"Unsupported format or extension: {key!r}. "
                f"Supported formats: {', '.join(supported)}"
            ) from None

    @classmethod
    def supported_extensions(cls) -> set[str]:
        """Return the set of all registered file extensions."""
        return {k for k in cls._parsers if k.startswith(".")}

    @classmethod
    def supported_formats(cls) -> set[str]:
        """Return the set of all registered format names."""
        return {p.format_name for p in cls._parsers.values()}

    @classmethod
    def clear(cls) -> None:
        """Remove all registered parsers (useful in tests)."""
        cls._parsers.clear()
