"""Tests for the config parser system."""

from __future__ import annotations

from pathlib import Path

import pytest

from configdiff.parsers import ParserRegistry
from configdiff.parsers.ini_parser import IniParser
from configdiff.parsers.json_parser import JsonParser
from configdiff.parsers.toml_parser import TomlParser
from configdiff.parsers.yaml_parser import YamlParser


class TestJsonParser:
    parser = JsonParser()

    def test_parse_valid(self, fixtures_dir: Path) -> None:
        data = self.parser.parse(fixtures_dir / "sample.json")
        assert data["hostname"] == "router-01"
        assert data["interfaces"]["eth0"]["ip"] == "10.0.0.1"

    def test_parse_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            self.parser.parse(tmp_path / "nope.json")

    def test_parse_invalid_json(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json}", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            self.parser.parse(bad)

    def test_parse_non_object(self, tmp_path: Path) -> None:
        arr = tmp_path / "arr.json"
        arr.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(ValueError, match="Expected a JSON object"):
            self.parser.parse(arr)


class TestYamlParser:
    parser = YamlParser()

    def test_parse_valid(self, fixtures_dir: Path) -> None:
        data = self.parser.parse(fixtures_dir / "sample.yaml")
        assert data["hostname"] == "router-01"
        assert data["dns"] == ["8.8.8.8", "8.8.4.4"]

    def test_parse_empty(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.yaml"
        empty.write_text("", encoding="utf-8")
        assert self.parser.parse(empty) == {}

    def test_parse_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            self.parser.parse(tmp_path / "nope.yaml")

    def test_parse_non_mapping(self, tmp_path: Path) -> None:
        lst = tmp_path / "list.yaml"
        lst.write_text("- a\n- b\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Expected a YAML mapping"):
            self.parser.parse(lst)


class TestTomlParser:
    parser = TomlParser()

    def test_parse_valid(self, fixtures_dir: Path) -> None:
        data = self.parser.parse(fixtures_dir / "sample.toml")
        assert data["server"]["hostname"] == "router-01"
        assert data["database"]["port"] == 5432

    def test_parse_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            self.parser.parse(tmp_path / "nope.toml")

    def test_parse_invalid_toml(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.toml"
        bad.write_text("[unterminated", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid TOML"):
            self.parser.parse(bad)


class TestIniParser:
    parser = IniParser()

    def test_parse_valid(self, fixtures_dir: Path) -> None:
        data = self.parser.parse(fixtures_dir / "sample.ini")
        assert data["server"]["hostname"] == "router-01"
        assert data["database"]["name"] == "appdb"

    def test_parse_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            self.parser.parse(tmp_path / "nope.ini")


class TestParserRegistry:
    def test_lookup_by_format_name(self) -> None:
        parser = ParserRegistry.get_parser("json")
        assert isinstance(parser, JsonParser)

    def test_lookup_by_extension(self) -> None:
        parser = ParserRegistry.get_parser(".yaml")
        assert isinstance(parser, YamlParser)

    def test_lookup_yml_extension(self) -> None:
        parser = ParserRegistry.get_parser(".yml")
        assert isinstance(parser, YamlParser)

    def test_lookup_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported format"):
            ParserRegistry.get_parser(".xyz")

    def test_supported_extensions(self) -> None:
        exts = ParserRegistry.supported_extensions()
        assert ".json" in exts
        assert ".yaml" in exts
        assert ".toml" in exts
        assert ".ini" in exts

    def test_supported_formats(self) -> None:
        fmts = ParserRegistry.supported_formats()
        assert fmts == {"json", "yaml", "toml", "ini"}
