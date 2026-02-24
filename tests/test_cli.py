"""Integration tests for the CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from configdiff.cli.app import EXIT_CHANGES, EXIT_ERROR, EXIT_NO_CHANGES, run


class TestCLIBasic:
    def test_no_changes(self, tmp_path: Path) -> None:
        f = tmp_path / "same.json"
        f.write_text('{"a": 1}', encoding="utf-8")
        code = run([str(f), str(f)])
        assert code == EXIT_NO_CHANGES

    def test_changes_detected(self, tmp_json: tuple[Path, Path]) -> None:
        before, after = tmp_json
        code = run([str(before), str(after)])
        assert code == EXIT_CHANGES

    def test_missing_file(self, tmp_path: Path) -> None:
        existing = tmp_path / "a.json"
        existing.write_text('{"x": 1}', encoding="utf-8")
        code = run([str(existing), str(tmp_path / "missing.json")])
        assert code == EXIT_ERROR

    def test_format_mismatch(self, tmp_path: Path) -> None:
        a = tmp_path / "a.json"
        b = tmp_path / "b.yaml"
        a.write_text('{"x": 1}', encoding="utf-8")
        b.write_text("x: 1\n", encoding="utf-8")
        code = run([str(a), str(b)])
        assert code == EXIT_ERROR


class TestCLIFormats:
    def test_json_output(
        self, tmp_json: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        before, after = tmp_json
        code = run([str(before), str(after), "--format", "json"])
        assert code == EXIT_CHANGES
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "changes" in data

    def test_yaml_output(
        self, tmp_yaml: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        before, after = tmp_yaml
        code = run([str(before), str(after), "--format", "yaml"])
        assert code == EXIT_CHANGES


class TestCLIFlags:
    def test_output_file(self, tmp_json: tuple[Path, Path], tmp_path: Path) -> None:
        before, after = tmp_json
        out = tmp_path / "result.json"
        code = run(
            [str(before), str(after), "--format", "json", "-o", str(out)]
        )
        assert code == EXIT_CHANGES
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["total_changes"] > 0

    def test_ignore_order(self, tmp_path: Path) -> None:
        before = tmp_path / "b.json"
        after = tmp_path / "a.json"
        before.write_text('{"list": [3, 1, 2]}', encoding="utf-8")
        after.write_text('{"list": [1, 2, 3]}', encoding="utf-8")
        code = run([str(before), str(after), "--ignore-order"])
        assert code == EXIT_NO_CHANGES

    def test_verbose(
        self, tmp_json: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        before, after = tmp_json
        code = run([str(before), str(after), "--verbose"])
        assert code in (EXIT_NO_CHANGES, EXIT_CHANGES)


class TestCLITomlIni:
    def test_toml_diff(self, tmp_toml: tuple[Path, Path]) -> None:
        before, after = tmp_toml
        code = run([str(before), str(after)])
        assert code == EXIT_CHANGES

    def test_ini_diff(self, tmp_ini: tuple[Path, Path]) -> None:
        before, after = tmp_ini
        code = run([str(before), str(after)])
        assert code == EXIT_CHANGES
