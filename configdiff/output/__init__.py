"""Output formatters — text, JSON, and YAML."""

from configdiff.output.base import BaseFormatter
from configdiff.output.json_output import JsonFormatter
from configdiff.output.text import TextFormatter
from configdiff.output.yaml_output import YamlFormatter

FORMATTERS: dict[str, BaseFormatter] = {
    "text": TextFormatter(),
    "json": JsonFormatter(),
    "yaml": YamlFormatter(),
}


def get_formatter(name: str) -> BaseFormatter:
    """Return the formatter for *name*, or raise :class:`ValueError`."""
    try:
        return FORMATTERS[name]
    except KeyError:
        raise ValueError(
            f"Unknown output format: {name!r}. "
            f"Choose from: {', '.join(sorted(FORMATTERS))}"
        ) from None


__all__ = [
    "BaseFormatter",
    "TextFormatter",
    "JsonFormatter",
    "YamlFormatter",
    "get_formatter",
]
