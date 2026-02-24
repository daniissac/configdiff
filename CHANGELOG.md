# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-02-24

### Added

- Structure-aware deep comparison for JSON, YAML, TOML, and INI config files
- Change classification: added, removed, modified, type_changed
- Dot-notation paths for precise change identification (`bgp.neighbors[0].remote_as`)
- Human-readable text output with colour for terminal review
- Machine-readable JSON and YAML output for CI/CD pipelines
- `--ignore-order` flag to treat lists as unordered sets
- `--output-file` flag to write results to a file
- CI/CD exit codes: `0` (no changes), `1` (changes detected), `2` (error)
- Plugin architecture for extensible parsers and formatters
- Auto-detection of config format from file extension
- Docker image with multi-stage build and non-root user
- Comprehensive test suite: unit, integration, golden, property-based, performance
- GitHub Actions CI with Python 3.11, 3.12, 3.13 matrix

[0.1.0]: https://github.com/daniissac/configdiff/releases/tag/v0.1.0
