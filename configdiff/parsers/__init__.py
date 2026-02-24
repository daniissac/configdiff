"""Config parsers — auto-registers all built-in parsers on import."""

from configdiff.parsers.ini_parser import IniParser
from configdiff.parsers.json_parser import JsonParser
from configdiff.parsers.registry import ParserRegistry
from configdiff.parsers.toml_parser import TomlParser
from configdiff.parsers.yaml_parser import YamlParser

ParserRegistry.register(JsonParser())
ParserRegistry.register(YamlParser())
ParserRegistry.register(TomlParser())
ParserRegistry.register(IniParser())

__all__ = [
    "JsonParser",
    "YamlParser",
    "TomlParser",
    "IniParser",
    "ParserRegistry",
]
